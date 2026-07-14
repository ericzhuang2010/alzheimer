#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL, mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode", "--mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/14_validate_outputs.R --config FILE ",
        "[--execution-config FILE] [--task-mode validate | --mode validate]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  selected_mode <- out$task_mode %||% out$mode %||% "validate"
  if (!identical(selected_mode, "validate")) {
    stop("Phase 14 mode must be 'validate'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

as_logical <- function(x) {
  !is.na(x) & toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(gsub("[^0-9.]", "", line[[1L]])) / (1024^2)
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else {
    result[[1L]]
  }
}

safe_read_tsv <- function(path) {
  tryCatch(
    read.delim(path, check.names = FALSE, stringsAsFactors = FALSE),
    error = function(e) structure(list(error = conditionMessage(e)), class = "read_error")
  )
}

make_expected_tasks <- function(manifest, output_root, execution_stage, allowed_modes) {
  scripts <- c(
    environment = "scripts/00_check_environment.R",
    audit = "scripts/01_audit_seurat_inputs.R",
    cohort = "scripts/02_build_cohort.R",
    annotations = "scripts/03_build_mito_annotations.R",
    qc = "scripts/04_mito_qc.R",
    normalize = "scripts/05_normalize_and_attach_metadata.R",
    descriptive = "scripts/06_summarize_celltypes.R",
    pseudobulk = "scripts/07_make_pseudobulk.R",
    contrasts = "scripts/07_build_contrast_manifest.R",
    pseudobulk_de = "scripts/07_run_pseudobulk_de.R",
    mast = "scripts/08_run_mast.R",
    mito_fraction = "scripts/09_run_mito_fraction_models.R",
    pathways = "scripts/09_run_mito_pathways.R",
    similarity = "scripts/10_similarity_analysis.R",
    multiple_testing = "scripts/11_apply_multiple_testing.R",
    sensitivity = "scripts/12_sensitivity_analysis.R",
    power = "scripts/13_power_analysis.R"
  )
  modes <- names(scripts)[names(scripts) %in% allowed_modes]
  global_modes <- c(
    "environment", "cohort", "annotations", "contrasts", "similarity",
    "multiple_testing", "sensitivity", "power"
  )
  status_path <- function(mode, rds_id = NA_character_, stem = NA_character_) {
    switch(
      mode,
      environment = file.path(output_root, "00_environment", "environment_status.tsv"),
      audit = file.path(output_root, "01_audit", paste0(stem, ".audit_status.tsv")),
      cohort = file.path(output_root, "02_cohort", "cohort_status.tsv"),
      annotations = file.path(output_root, "03_annotations", "annotation_status.tsv"),
      qc = file.path(output_root, "04_qc", paste0(rds_id, "_qc_status.tsv")),
      normalize = file.path(output_root, "05_normalized", paste0(stem, ".normalization_status.tsv")),
      descriptive = file.path(output_root, "06_descriptive", paste0(rds_id, "_descriptive_status.tsv")),
      pseudobulk = file.path(output_root, "07_pseudobulk", paste0(stem, ".pseudobulk_status.tsv")),
      contrasts = file.path(
        output_root, "07_contrasts", paste0(execution_stage, "_contrast_manifest_status.tsv")
      ),
      pseudobulk_de = file.path(output_root, "07_pseudobulk_de", paste0(rds_id, ".pseudobulk_de_status.tsv")),
      mast = file.path(output_root, "08_mast", paste0(rds_id, ".mast_de_status.tsv")),
      mito_fraction = file.path(output_root, "09_downstream", paste0(rds_id, ".mito_fraction_status.tsv")),
      pathways = file.path(output_root, "09_downstream", paste0(rds_id, ".pathway_status.tsv")),
      similarity = file.path(output_root, "10_downstream", "similarity_status.tsv"),
      multiple_testing = file.path(output_root, "11_multiple_testing", "multiple_testing_status.tsv"),
      sensitivity = file.path(output_root, "12_sensitivity", "sensitivity_status.tsv"),
      power = file.path(output_root, "13_power", "power_status.tsv")
    )
  }
  rows <- list()
  for (mode in modes) {
    if (mode %in% global_modes) {
      rows[[length(rows) + 1L]] <- data.frame(
        task_mode = mode,
        stable_task_id = paste0("global:", mode),
        rds_id = NA_character_,
        scientific_script = unname(scripts[[mode]]),
        status_path = status_path(mode),
        stringsAsFactors = FALSE
      )
    } else {
      for (i in seq_len(nrow(manifest))) {
        stem <- sub("[.]rds$", "", basename(manifest$input_rds[[i]]), ignore.case = TRUE)
        rows[[length(rows) + 1L]] <- data.frame(
          task_mode = mode,
          stable_task_id = paste(mode, manifest$rds_id[[i]], sep = ":"),
          rds_id = manifest$rds_id[[i]],
          scientific_script = unname(scripts[[mode]]),
          status_path = status_path(mode, manifest$rds_id[[i]], stem),
          stringsAsFactors = FALSE
        )
      }
    }
  }
  do.call(rbind, rows)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("yaml", quietly = TRUE)) stop("Package 'yaml' is required", call. = FALSE)

root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
execution_config <- if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, root)
  if (!file.exists(execution_path)) stop("Execution config does not exist: ", execution_path, call. = FALSE)
  yaml::read_yaml(execution_path)
} else {
  list(execution = list())
}

manifest_path <- absolute_path(config$project$manifest, root)
analysis_path <- absolute_path(config$project$analysis_config, root)
output_root <- absolute_path(config$outputs$root, root)
if (!file.exists(manifest_path)) stop("Manifest does not exist: ", manifest_path, call. = FALSE)
if (!file.exists(analysis_path)) stop("Analysis config does not exist: ", analysis_path, call. = FALSE)
manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
manifest <- manifest[as_logical(manifest$enabled), , drop = FALSE]
if (!nrow(manifest)) stop("No enabled manifest rows", call. = FALSE)

execution <- execution_config$execution %||% list()
execution_stage <- as.character(execution$execution_stage %||% if (isTRUE(config$scope$pilot)) {
  "local_pilot"
} else {
  "minerva_production"
})
validation_dir <- file.path(output_root, "14_validation")
dir.create(validation_dir, recursive = TRUE, showWarnings = FALSE)

expected <- make_expected_tasks(
  manifest, output_root, execution_stage,
  unlist(config$scope$allowed_task_modes, use.names = FALSE)
)
current_config_sha256 <- sha256_file(analysis_path)
current_manifest_sha256 <- sha256_file(manifest_path)

completion_rows <- lapply(seq_len(nrow(expected)), function(i) {
  task <- expected[i, , drop = FALSE]
  status_exists <- file.exists(task$status_path)
  status <- if (status_exists) safe_read_tsv(task$status_path) else NULL
  readable <- status_exists && !inherits(status, "read_error") && nrow(status) == 1L
  get_value <- function(name, default = NA_character_) {
    if (!readable || !name %in% names(status)) return(default)
    as.character(status[[name]][[1L]])
  }
  observed_task_id <- get_value("stable_task_id")
  observed_validation <- get_value("validation_status", "not_started")
  recorded_script <- get_value("scientific_script")
  recorded_script_sha256 <- get_value("scientific_code_bundle_sha256")
  current_script_path <- absolute_path(task$scientific_script, root)
  current_script_sha256 <- sha256_file(current_script_path)
  recorded_config_sha256 <- get_value("scientific_config_sha256")
  recorded_manifest_sha256 <- get_value(
    "manifest_sha256", get_value("rds_manifest_sha256")
  )
  terminal_classification <- if (!status_exists) {
    "not_started"
  } else if (!readable) {
    "failed"
  } else if (identical(observed_validation, "validated_complete")) {
    "validated"
  } else if (grepl("fail", observed_validation, ignore.case = TRUE)) {
    "failed"
  } else {
    "pending"
  }
  data.frame(
    schema_version = "completion_manifest_v1",
    execution_stage = execution_stage,
    task_mode = task$task_mode,
    stable_task_id = task$stable_task_id,
    rds_id = task$rds_id,
    expected_status_path = sub(paste0("^", root, "/?"), "", task$status_path),
    status_exists = status_exists,
    status_readable_single_row = readable,
    observed_stable_task_id = observed_task_id,
    stable_task_id_matches = readable && identical(observed_task_id, task$stable_task_id),
    observed_schema_version = get_value("schema_version", "legacy_status_without_schema"),
    observed_validation_status = observed_validation,
    terminal_classification = terminal_classification,
    recorded_scientific_script = recorded_script,
    expected_scientific_script = task$scientific_script,
    scientific_script_path_matches = readable && identical(recorded_script, task$scientific_script),
    recorded_script_sha256 = recorded_script_sha256,
    current_script_sha256 = current_script_sha256,
    scientific_script_sha256_matches = readable && !is.na(recorded_script_sha256) &&
      identical(recorded_script_sha256, current_script_sha256),
    recorded_scientific_config_sha256 = recorded_config_sha256,
    current_scientific_config_sha256 = current_config_sha256,
    scientific_config_sha256_matches = readable && !is.na(recorded_config_sha256) &&
      identical(recorded_config_sha256, current_config_sha256),
    recorded_manifest_sha256 = recorded_manifest_sha256,
    current_manifest_sha256 = current_manifest_sha256,
    manifest_sha256_matches = readable && !is.na(recorded_manifest_sha256) &&
      identical(recorded_manifest_sha256, current_manifest_sha256),
    peak_ram_gib = suppressWarnings(as.numeric(get_value("peak_ram_gib"))),
    elapsed_seconds = suppressWarnings(as.numeric(get_value("elapsed_seconds"))),
    status_message = if (inherits(status, "read_error")) status$error else "",
    stringsAsFactors = FALSE
  )
})
completion <- do.call(rbind, completion_rows)

check_paths <- list.files(
  output_root, pattern = "_checks[.]tsv$", recursive = TRUE, full.names = TRUE
)
check_paths <- check_paths[!grepl("/14_validation/", check_paths, fixed = TRUE)]
check_audit <- do.call(rbind, lapply(check_paths, function(path) {
  table <- safe_read_tsv(path)
  if (inherits(table, "read_error") || !"passed" %in% names(table)) {
    return(data.frame(
      path = sub(paste0("^", root, "/?"), "", path), checks = NA_integer_,
      required_checks = NA_integer_, failed_required_checks = 1L,
      message = if (inherits(table, "read_error")) table$error else "missing passed column",
      stringsAsFactors = FALSE
    ))
  }
  required <- if ("required" %in% names(table)) as_logical(table$required) else rep(TRUE, nrow(table))
  passed <- as_logical(table$passed)
  data.frame(
    path = sub(paste0("^", root, "/?"), "", path), checks = nrow(table),
    required_checks = sum(required), failed_required_checks = sum(required & !passed),
    message = "", stringsAsFactors = FALSE
  )
}))

artifact_manifest_paths <- list.files(
  output_root, pattern = "_artifacts[.]tsv$", recursive = TRUE, full.names = TRUE
)
artifact_manifest_paths <- artifact_manifest_paths[
  !grepl("/14_validation/", artifact_manifest_paths, fixed = TRUE)
]
artifact_rows <- list()
for (manifest_file in artifact_manifest_paths) {
  table <- safe_read_tsv(manifest_file)
  if (inherits(table, "read_error") || !all(c("path", "sha256") %in% names(table))) {
    artifact_rows[[length(artifact_rows) + 1L]] <- data.frame(
      artifact_manifest = sub(paste0("^", root, "/?"), "", manifest_file),
      artifact_path = NA_character_, artifact_exists = FALSE, bytes_match = FALSE,
      sha256_match = FALSE, declared_validation_complete = FALSE,
      message = if (inherits(table, "read_error")) table$error else "missing path or sha256 column",
      stringsAsFactors = FALSE
    )
    next
  }
  for (i in seq_len(nrow(table))) {
    artifact_path <- absolute_path(as.character(table$path[[i]]), root)
    exists <- file.exists(artifact_path)
    observed_bytes <- if (exists) as.numeric(file.info(artifact_path)$size) else NA_real_
    expected_bytes <- if ("bytes" %in% names(table)) as.numeric(table$bytes[[i]]) else observed_bytes
    declared_status <- if ("validation_status" %in% names(table)) {
      as.character(table$validation_status[[i]])
    } else {
      "validated_complete"
    }
    artifact_rows[[length(artifact_rows) + 1L]] <- data.frame(
      artifact_manifest = sub(paste0("^", root, "/?"), "", manifest_file),
      artifact_path = sub(paste0("^", root, "/?"), "", artifact_path),
      artifact_exists = exists,
      bytes_match = exists && isTRUE(all.equal(observed_bytes, expected_bytes)),
      sha256_match = exists && identical(sha256_file(artifact_path), as.character(table$sha256[[i]])),
      declared_validation_complete = identical(declared_status, "validated_complete"),
      message = "", stringsAsFactors = FALSE
    )
  }
}
artifact_audit <- if (length(artifact_rows)) do.call(rbind, artifact_rows) else data.frame(
  artifact_manifest = character(), artifact_path = character(), artifact_exists = logical(),
  bytes_match = logical(), sha256_match = logical(),
  declared_validation_complete = logical(), message = character()
)

core_checks <- data.frame(
  check = c(
    "expected_statuses_present", "status_files_readable_single_row",
    "stable_task_ids_match", "all_tasks_validated_complete",
    "scientific_script_paths_match", "scientific_script_checksums_match",
    "manifest_checksums_match", "required_scientific_checks_pass",
    "declared_artifacts_exist", "declared_artifact_sizes_match",
    "declared_artifact_checksums_match", "declared_artifacts_validated"
  ),
  passed = c(
    all(completion$status_exists), all(completion$status_readable_single_row),
    all(completion$stable_task_id_matches),
    all(completion$observed_validation_status == "validated_complete"),
    all(completion$scientific_script_path_matches),
    all(completion$scientific_script_sha256_matches),
    all(completion$manifest_sha256_matches),
    nrow(check_audit) > 0L && all(check_audit$failed_required_checks == 0L),
    nrow(artifact_audit) > 0L && all(artifact_audit$artifact_exists),
    nrow(artifact_audit) > 0L && all(artifact_audit$bytes_match),
    nrow(artifact_audit) > 0L && all(artifact_audit$sha256_match),
    nrow(artifact_audit) > 0L && all(artifact_audit$declared_validation_complete)
  ),
  gate = "validation",
  stringsAsFactors = FALSE
)

rerun_root <- file.path(dirname(output_root), paste0(basename(output_root), "_rerun"))
parity_files <- list.files(
  validation_dir, pattern = "parity|task_graph_diff", full.names = TRUE,
  ignore.case = TRUE
)
output_statuses <- unique(unlist(lapply(completion$expected_status_path, function(path) {
  absolute <- absolute_path(path, root)
  table <- if (file.exists(absolute)) safe_read_tsv(absolute) else NULL
  if (is.null(table) || inherits(table, "read_error") || !"output_status" %in% names(table)) {
    return(character())
  }
  as.character(table$output_status)
})))
expected_output_status <- if (isTRUE(config$scope$pilot)) {
  as.character(config$pilot_limits$required_status %||% "nonfinal_smoke_test")
} else {
  "final"
}

promotion_checks <- data.frame(
  check = c(
    "scientific_config_checksums_match_current_config",
    "clean_rerun_output_exists", "execution_task_graph_parity_available",
    "output_labels_match_execution_scope"
  ),
  passed = c(
    all(completion$scientific_config_sha256_matches),
    dir.exists(rerun_root) && length(list.files(rerun_root, recursive = TRUE)) > 0L,
    length(parity_files) > 0L,
    length(output_statuses) > 0L && all(output_statuses == expected_output_status)
  ),
  gate = "promotion",
  stringsAsFactors = FALSE
)
validation_checks <- rbind(core_checks, promotion_checks)
validation_checks$observed <- c(
  sum(completion$status_exists), sum(completion$status_readable_single_row),
  sum(completion$stable_task_id_matches),
  sum(completion$observed_validation_status == "validated_complete"),
  sum(completion$scientific_script_path_matches),
  sum(completion$scientific_script_sha256_matches),
  sum(completion$manifest_sha256_matches),
  sum(check_audit$failed_required_checks),
  sum(artifact_audit$artifact_exists), sum(artifact_audit$bytes_match),
  sum(artifact_audit$sha256_match), sum(artifact_audit$declared_validation_complete),
  sum(completion$scientific_config_sha256_matches),
  dir.exists(rerun_root), length(parity_files), paste(output_statuses, collapse = ";")
)
validation_checks$expected <- c(
  rep(nrow(completion), 7L), 0L,
  rep(nrow(artifact_audit), 4L), nrow(completion), TRUE, ">0",
  expected_output_status
)

resource_report <- completion[, c(
  "schema_version", "execution_stage", "task_mode", "stable_task_id", "rds_id",
  "peak_ram_gib", "elapsed_seconds", "terminal_classification"
)]
resource_report$schema_version <- "validation_resource_report_v1"

core_failures <- validation_checks$check[
  validation_checks$gate == "validation" & !validation_checks$passed
]
promotion_blockers <- validation_checks$check[
  validation_checks$gate == "promotion" & !validation_checks$passed
]
validation_status <- if (length(core_failures)) "failed" else "validated_complete"
promotion_status <- if (length(core_failures) || length(promotion_blockers)) "blocked" else "ready"

report <- data.frame(
  schema_version = "validation_report_v1",
  execution_stage = execution_stage,
  expected_tasks = nrow(completion),
  validated_tasks = sum(completion$terminal_classification == "validated"),
  pending_tasks = sum(completion$terminal_classification == "pending"),
  failed_tasks = sum(completion$terminal_classification == "failed"),
  not_started_tasks = sum(completion$terminal_classification == "not_started"),
  scientific_check_tables = nrow(check_audit),
  failed_required_scientific_checks = sum(check_audit$failed_required_checks),
  declared_artifacts = nrow(artifact_audit),
  invalid_declared_artifacts = sum(
    !artifact_audit$artifact_exists | !artifact_audit$bytes_match |
      !artifact_audit$sha256_match | !artifact_audit$declared_validation_complete
  ),
  config_drift_tasks = sum(!completion$scientific_config_sha256_matches),
  validation_status = validation_status,
  promotion_status = promotion_status,
  validation_failures = paste(core_failures, collapse = ";"),
  promotion_blockers = paste(promotion_blockers, collapse = ";"),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)

completion_path <- file.path(validation_dir, paste0(execution_stage, "_completion_manifest.tsv"))
checks_path <- file.path(validation_dir, paste0(execution_stage, "_validation_checks.tsv"))
resource_path <- file.path(validation_dir, paste0(execution_stage, "_resource_report.tsv"))
artifact_audit_path <- file.path(validation_dir, paste0(execution_stage, "_artifact_audit.tsv"))
report_path <- file.path(validation_dir, paste0(execution_stage, "_validation_report.tsv"))
artifacts_path <- file.path(validation_dir, "validation_artifacts.tsv")
status_path <- file.path(validation_dir, "validation_status.tsv")

atomic_write_tsv(completion, completion_path)
atomic_write_tsv(validation_checks, checks_path)
atomic_write_tsv(resource_report, resource_path)
atomic_write_tsv(artifact_audit, artifact_audit_path)
atomic_write_tsv(report, report_path)

output_files <- c(completion_path, checks_path, resource_path, artifact_audit_path, report_path)
validation_artifacts <- data.frame(
  schema_version = "validation_artifacts_v1",
  artifact = basename(output_files),
  path = sub(paste0("^", root, "/?"), "", output_files),
  bytes = as.numeric(file.info(output_files)$size),
  sha256 = vapply(output_files, sha256_file, character(1)),
  records = vapply(output_files, function(path) nrow(read.delim(path, check.names = FALSE)), integer(1)),
  validation_status = "validated_complete",
  stringsAsFactors = FALSE
)
atomic_write_tsv(validation_artifacts, artifacts_path)

status <- data.frame(
  schema_version = "validation_status_v1",
  execution_stage = execution_stage,
  execution_phase = execution$execution_phase %||% NA_integer_,
  backend = execution$backend %||% NA_character_,
  run_id = execution$run_id %||% NA_character_,
  stable_task_id = "global:validate",
  source_rds = paste(manifest$rds_id, collapse = ";"),
  scientific_script = "scripts/14_validate_outputs.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(root, "scripts/14_validate_outputs.R")),
  scientific_config_sha256 = current_config_sha256,
  rds_manifest_sha256 = current_manifest_sha256,
  expected_tasks = nrow(completion),
  validated_tasks = sum(completion$terminal_classification == "validated"),
  promotion_status = promotion_status,
  promotion_blockers = paste(promotion_blockers, collapse = ";"),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(core_failures, collapse = ";"),
  git_revision = git_revision(root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, status_path)

cat("Phase 14 validation output: ", validation_dir, "\n", sep = "")
cat("Expected tasks: ", nrow(completion), "\n", sep = "")
cat("Validated tasks: ", sum(completion$terminal_classification == "validated"), "\n", sep = "")
cat("Required scientific check failures: ", sum(check_audit$failed_required_checks), "\n", sep = "")
cat("Invalid declared artifacts: ", report$invalid_declared_artifacts[[1L]], "\n", sep = "")
cat("Phase 14 validation status: ", validation_status, "\n", sep = "")
cat("Promotion status: ", promotion_status, "\n", sep = "")
if (length(promotion_blockers)) {
  cat("Promotion blockers: ", paste(promotion_blockers, collapse = ", "), "\n", sep = "")
}
if (length(core_failures)) {
  cat("Failed validation checks: ", paste(core_failures, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
