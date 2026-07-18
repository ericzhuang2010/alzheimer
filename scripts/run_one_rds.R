#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = NULL, script = NULL,
    dry_run = FALSE, force = FALSE
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--task-mode", "--script"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(paste(
        "Usage: Rscript scripts/run_one_rds.R --config FILE",
        "--execution-config FILE --task-mode MODE --script FILE",
        "[--manifest-row N | --rds-id ID] [--dry-run] [--force]\n"
      ))
      quit(status = 0L)
    }
    if (key %in% c("--dry-run", "--force")) {
      name <- gsub("-", "_", sub("^--", "", key))
      out[[name]] <- TRUE
      i <- i + 1L
      next
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  required <- c("config", "execution_config", "task_mode", "script")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
  if (is.null(out$manifest_row) && is.null(out$rds_id)) {
    stop("One of --manifest-row or --rds-id is required", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) if (grepl("^/", path)) path else file.path(root, path)

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("yaml", quietly = TRUE)) stop("Package 'yaml' is required", call. = FALSE)

root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, root)
execution_path <- absolute_path(args$execution_config, root)
script_path <- absolute_path(args$script, root)
config <- yaml::read_yaml(config_path)
execution_config <- yaml::read_yaml(execution_path)
manifest_path <- absolute_path(config$project$manifest, root)
manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)

if (!is.null(args$manifest_row)) {
  row <- manifest[manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
} else {
  row <- manifest[manifest$rds_id == args$rds_id, , drop = FALSE]
}
if (nrow(row) != 1L) stop("Manifest selection must identify exactly one row", call. = FALSE)
if (!file.exists(script_path)) stop("Scientific script does not exist: ", script_path, call. = FALSE)

task_id <- paste(args$task_mode, row$rds_id[[1L]], sep = ":")
output_root <- absolute_path(config$outputs$root, root)
status_path <- file.path(output_root, "status", paste0(gsub(":", "__", task_id), ".tsv"))
log_dir <- absolute_path(execution_config$execution$log_dir, root)
dir.create(log_dir, recursive = TRUE, showWarnings = FALSE)
log_path <- file.path(log_dir, paste0(gsub(":", "__", task_id), ".log"))

read_single_tsv <- function(path) {
  if (!file.exists(path)) return(NULL)
  value <- tryCatch(
    read.delim(path, check.names = FALSE, stringsAsFactors = FALSE),
    error = function(e) NULL
  )
  if (is.null(value) || nrow(value) != 1L) NULL else value
}

field_matches <- function(table, field, expected) {
  !is.null(table) &&
    field %in% names(table) &&
    length(table[[field]]) == 1L &&
    !is.na(table[[field]][[1L]]) &&
    identical(as.character(table[[field]][[1L]]), as.character(expected))
}

validate_mast_resume <- function() {
  reasons <- character()
  require_check <- function(value, label) {
    if (!isTRUE(value)) reasons <<- c(reasons, label)
  }

  script_sha <- sha256_file(script_path)
  analysis_path <- absolute_path(config$project$analysis_config, root)
  analysis_sha <- sha256_file(analysis_path)
  manifest_sha <- sha256_file(manifest_path)
  execution <- execution_config$execution
  rds_id <- as.character(row$rds_id[[1L]])
  source_rds <- as.character(row$input_rds[[1L]])
  prefix <- tolower(rds_id)
  base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_rds))

  controller <- read_single_tsv(status_path)
  require_check(field_matches(controller, "stable_task_id", task_id), "controller task ID")
  require_check(field_matches(controller, "source_rds", source_rds), "controller source RDS")
  require_check(field_matches(controller, "scientific_code_bundle_sha256", script_sha), "controller script checksum")
  require_check(field_matches(controller, "scientific_config_sha256", analysis_sha), "controller scientific-config checksum")
  require_check(field_matches(controller, "manifest_sha256", manifest_sha), "controller manifest checksum")
  require_check(field_matches(controller, "execution_phase", execution$execution_phase), "controller execution phase")
  require_check(field_matches(controller, "backend", execution$backend), "controller backend")
  require_check(field_matches(controller, "run_id", execution$run_id), "controller run ID")
  require_check(field_matches(controller, "validation_status", "validated_complete"), "controller validation status")
  require_check(field_matches(controller, "exit_code", 0L), "controller exit code")

  output_dir <- file.path(output_root, "08_mast")
  scientific_path <- file.path(output_dir, paste0(prefix, ".yu_mast_de_status.tsv"))
  artifact_manifest_path <- file.path(
    output_dir, paste0(prefix, ".yu_mast_de_artifacts.tsv")
  )
  scientific <- read_single_tsv(scientific_path)
  require_check(field_matches(scientific, "schema_version", "yu_mast_de_status_v2"), "scientific status schema")
  require_check(field_matches(scientific, "stable_task_id", task_id), "scientific task ID")
  require_check(field_matches(scientific, "source_rds", source_rds), "scientific source RDS")
  require_check(field_matches(scientific, "scientific_code_bundle_sha256", script_sha), "scientific script checksum")
  require_check(field_matches(scientific, "scientific_config_sha256", analysis_sha), "scientific-config checksum")
  require_check(field_matches(scientific, "rds_manifest_sha256", manifest_sha), "scientific manifest checksum")
  require_check(
    field_matches(
      scientific, "analysis_population", "yu_all_cohort_included_nuclei"
    ),
    "scientific analysis population"
  )
  require_check(field_matches(scientific, "validation_status", "validated_complete"), "scientific validation status")
  require_check(field_matches(scientific, "failed_contrasts", 0L), "scientific failed-contrast count")

  normalized_path <- file.path(
    output_root, "05_normalized", paste0(base_name, ".normalized.rds")
  )
  normalization_status_path <- file.path(
    output_root, "05_normalized", paste0(base_name, ".normalization_status.tsv")
  )
  yu_manifest_path <- file.path(
    output_dir, paste0(prefix, ".yu_mast_contrast_manifest.tsv")
  )
  require_check(
    field_matches(scientific, "normalized_rds_sha256", sha256_file(normalized_path)),
    "normalized-RDS checksum"
  )
  require_check(
    field_matches(
      scientific, "normalization_status_sha256",
      sha256_file(normalization_status_path)
    ),
    "normalization-status checksum"
  )
  require_check(
    field_matches(scientific, "yu_manifest_sha256", sha256_file(yu_manifest_path)),
    "Yu-manifest checksum"
  )

  artifacts <- tryCatch(
    read.delim(artifact_manifest_path, check.names = FALSE, stringsAsFactors = FALSE),
    error = function(e) NULL
  )
  artifact_columns <- c("path", "bytes", "sha256", "validation_status")
  artifacts_ready <- !is.null(artifacts) && nrow(artifacts) > 0L &&
    all(artifact_columns %in% names(artifacts))
  require_check(artifacts_ready, "artifact manifest")
  if (artifacts_ready) {
    artifact_paths <- vapply(
      artifacts$path, absolute_path, character(1), root = root
    )
    artifacts_exist <- all(file.exists(artifact_paths))
    require_check(artifacts_exist, "artifact existence")
    if (artifacts_exist) {
      require_check(
        identical(
          as.numeric(file.info(artifact_paths)$size),
          as.numeric(artifacts$bytes)
        ),
        "artifact byte counts"
      )
      require_check(
        identical(
          unname(vapply(artifact_paths, sha256_file, character(1))),
          as.character(artifacts$sha256)
        ),
        "artifact checksums"
      )
    }
    require_check(
      all(artifacts$validation_status == "validated_complete"),
      "artifact validation statuses"
    )
  }

  list(valid = !length(reasons), reasons = unique(reasons))
}

child_args <- c(
  script_path,
  "--config", config_path,
  "--execution-config", execution_path,
  "--manifest-row", as.character(row$manifest_row[[1L]]),
  "--task-mode", args$task_mode
)
command_text <- paste(c("Rscript", shQuote(child_args)), collapse = " ")
if (args$dry_run) {
  cat(command_text, "\n")
  quit(status = 0L)
}

resume_enabled <- isTRUE(execution_config$execution$resume) && !isTRUE(args$force)
if (resume_enabled && identical(args$task_mode, "mast")) {
  resume <- validate_mast_resume()
  if (isTRUE(resume$valid)) {
    cat(
      "Resume: skipping validated task ", task_id,
      " because code, inputs, statuses, and artifact checksums match.\n",
      sep = ""
    )
    quit(status = 0L)
  }
  if (file.exists(status_path)) {
    cat(
      "Resume: rerunning ", task_id, "; validation mismatch: ",
      paste(resume$reasons, collapse = "; "), "\n",
      sep = ""
    )
  }
}

start <- Sys.time()
exit_code <- system2("Rscript", child_args, stdout = log_path, stderr = log_path)
elapsed <- as.numeric(difftime(Sys.time(), start, units = "secs"))
validation_status <- if (identical(exit_code, 0L)) "validated_complete" else "failed"

status <- data.frame(
  execution_phase = execution_config$execution$execution_phase,
  backend = execution_config$execution$backend,
  run_id = execution_config$execution$run_id,
  stable_task_id = task_id,
  source_rds = row$input_rds[[1L]],
  scientific_script = args$script,
  scientific_code_bundle_sha256 = sha256_file(script_path),
  scientific_config_sha256 = sha256_file(absolute_path(config$project$analysis_config, root)),
  manifest_sha256 = sha256_file(manifest_path),
  peak_ram_gib = NA_real_,
  elapsed_seconds = elapsed,
  validation_status = validation_status,
  exit_code = exit_code,
  log_path = sub(paste0("^", root, "/?"), "", log_path),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, status_path)
quit(status = exit_code)
