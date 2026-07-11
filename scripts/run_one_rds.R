#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = NULL, script = NULL, dry_run = FALSE
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
        "[--manifest-row N | --rds-id ID] [--dry-run]\n"
      ))
      quit(status = 0L)
    }
    if (key == "--dry-run") {
      out$dry_run <- TRUE
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
