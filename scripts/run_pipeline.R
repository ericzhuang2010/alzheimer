#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, phase = NULL,
    manifest = NULL, task_graph_output = NULL, rds_id = NULL,
    dry_run = FALSE, force = FALSE
  )
  value_options <- c(
    "--config", "--execution-config", "--phase", "--manifest",
    "--task-graph-output", "--rds-id"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/run_pipeline.R --config FILE ",
        "--execution-config FILE --phase MODE [--manifest FILE] ",
        "[--rds-id ID] [--dry-run] [--force] ",
        "[--task-graph-output FILE]\n",
        sep = ""
      )
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
  required <- c("config", "execution_config", "phase")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
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

registry <- data.frame(
  task_mode = c(
    "environment", "parity", "audit", "cohort", "annotations", "qc",
    "normalize", "descriptive", "pseudobulk", "contrasts", "pseudobulk_de",
    "mast", "annotate_genes", "similarity"
  ),
  scope = c(
    "global", "global", "rds", "global", "global", "rds", "rds", "rds",
    "rds", "global", "rds", "rds", "global", "global"
  ),
  script = c(
    "scripts/00_check_environment.R",
    "scripts/14_validate_execution_parity.R",
    "scripts/01_audit_seurat_inputs.R",
    "scripts/02_build_cohort.R",
    "scripts/03_build_mito_annotations.R",
    "scripts/04_mito_qc.R",
    "scripts/05_normalize_and_attach_metadata.R",
    "scripts/06_summarize_celltypes.R",
    "scripts/07_make_pseudobulk.R",
    "scripts/07_build_contrast_manifest.R",
    "scripts/07_run_pseudobulk_de.R",
    "scripts/08_run_mast.R",
    "scripts/09_annotate_mitochondrial_genes.R",
    "scripts/10_calculate_mitochondrial_similarity.R"
  ),
  argument_names = c(
    "config,execution-config,report,status",
    rep("config,execution-config,manifest-row,task-mode", 13L)
  ),
  output_schema = c(
    "environment_checks_v1", "parity_v1", "rds_audit_v1", "cohort_v1",
    "mito_annotations_v1", "mito_qc_v1", "normalized_rds_v1",
    "descriptive_v1", "pseudobulk_v1", "contrast_manifest_v1",
    "pseudobulk_de_v1", "yu_mast_de_v2",
    "mitochondrial_annotation_status_v1", "mitochondrial_similarity_v1"
  ),
  stringsAsFactors = FALSE
)
registry$argument_names[registry$task_mode == "cohort"] <- paste(
  c("config", "execution-config", "audit", "task-mode"), collapse = ","
)
registry$argument_names[registry$task_mode == "annotations"] <- paste(
  c("config", "execution-config", "features", "task-mode"), collapse = ","
)
registry$argument_names[registry$task_mode == "annotate_genes"] <- paste(
  c("config", "execution-config", "task-mode"), collapse = ","
)
registry$argument_names[registry$task_mode == "similarity"] <- paste(
  c("config", "execution-config", "task-mode"), collapse = ","
)

args <- parse_cli(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("yaml", quietly = TRUE)) stop("Package 'yaml' is required", call. = FALSE)

root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, root)
execution_path <- absolute_path(args$execution_config, root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
if (!file.exists(execution_path)) stop("Execution config does not exist: ", execution_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
execution_config <- yaml::read_yaml(execution_path)
manifest_path <- absolute_path(args$manifest %||% config$project$manifest, root)
analysis_path <- absolute_path(config$project$analysis_config, root)
if (!file.exists(manifest_path)) stop("Manifest does not exist: ", manifest_path, call. = FALSE)
if (!file.exists(analysis_path)) stop("Analysis config does not exist: ", analysis_path, call. = FALSE)
manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
enabled <- toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES")
manifest <- manifest[enabled, , drop = FALSE]

allowed_modes <- unlist(config$scope$allowed_task_modes, use.names = FALSE)
valid_modes <- unique(c(allowed_modes, "all"))
if (!args$phase %in% valid_modes) {
  stop("Unsupported --phase '", args$phase, "'. Allowed: ", paste(valid_modes, collapse = ", "), call. = FALSE)
}

execution <- execution_config$execution
execution_stage <- as.character(execution$execution_stage %||% if (
  isTRUE(config$scope$pilot)
) "local_pilot" else "minerva_production")
allowed_execution_stages <- c("local_pilot", "minerva_production", "lsf_fallback")
if (length(execution_stage) != 1L || !execution_stage %in% allowed_execution_stages) {
  stop(
    "execution.execution_stage must be one of: ",
    paste(allowed_execution_stages, collapse = ", "),
    call. = FALSE
  )
}
total_memory <- as.numeric(execution$total_memory_gib)
reserve_memory <- as.numeric(execution$reserve_memory_gib)
if (!is.finite(total_memory) || !is.finite(reserve_memory) || total_memory <= reserve_memory) {
  stop("Invalid memory budget: total_memory_gib must exceed reserve_memory_gib", call. = FALSE)
}
if (as.integer(execution$max_total_cores) < 1L) stop("max_total_cores must be at least 1", call. = FALSE)

selected_modes <- if (args$phase == "all") allowed_modes else args$phase
selected_registry <- registry[registry$task_mode %in% selected_modes, , drop = FALSE]
selected_registry$order <- match(selected_registry$task_mode, registry$task_mode)
selected_registry <- selected_registry[order(selected_registry$order), , drop = FALSE]

if (!is.null(args$rds_id)) {
  if (!nrow(selected_registry) || any(selected_registry$scope != "rds")) {
    stop("--rds-id can only be used when every selected task mode has RDS scope", call. = FALSE)
  }
  selected_manifest <- manifest[manifest$rds_id == args$rds_id, , drop = FALSE]
  if (nrow(selected_manifest) != 1L) {
    stop("--rds-id must identify exactly one enabled manifest row: ", args$rds_id, call. = FALSE)
  }
  manifest <- selected_manifest
}

graph_rows <- list()
for (i in seq_len(nrow(selected_registry))) {
  task <- selected_registry[i, , drop = FALSE]
  targets <- if (task$scope == "rds") seq_len(nrow(manifest)) else NA_integer_
  for (target in targets) {
    is_rds <- !is.na(target)
    rds_id <- if (is_rds) manifest$rds_id[[target]] else NA_character_
    manifest_row <- if (is_rds) manifest$manifest_row[[target]] else NA_integer_
    stable_task_id <- if (is_rds) paste(task$task_mode, rds_id, sep = ":") else paste0("global:", task$task_mode)
    script_path <- absolute_path(task$script, root)
    task_config_path <- if (task$task_mode == "annotate_genes") {
      phase09_config <- config$project$phase09_annotation_config
      if (is.null(phase09_config)) {
        stop("project.phase09_annotation_config is required for annotate_genes", call. = FALSE)
      }
      absolute_path(phase09_config, root)
    } else if (task$task_mode == "similarity") {
      phase10_config <- config$project$phase10_similarity_config
      if (is.null(phase10_config)) {
        stop("project.phase10_similarity_config is required for similarity", call. = FALSE)
      }
      absolute_path(phase10_config, root)
    } else {
      analysis_path
    }
    if (!file.exists(task_config_path)) {
      stop("Scientific config does not exist: ", task_config_path, call. = FALSE)
    }
    graph_rows[[length(graph_rows) + 1L]] <- data.frame(
      execution_stage = execution_stage,
      execution_phase = execution$execution_phase,
      backend = execution$backend,
      run_id = execution$run_id,
      stable_task_id = stable_task_id,
      task_mode = task$task_mode,
      manifest_row = manifest_row,
      rds_id = rds_id,
      scientific_script = task$script,
      script_exists = file.exists(script_path),
      scientific_script_sha256 = sha256_file(script_path),
      scientific_config_sha256 = sha256_file(task_config_path),
      manifest_sha256 = sha256_file(manifest_path),
      argument_names = task$argument_names,
      output_schema = task$output_schema,
      pilot = isTRUE(config$scope$pilot),
      stringsAsFactors = FALSE
    )
  }
}
task_graph <- do.call(rbind, graph_rows)

default_graph <- file.path(
  config$outputs$root, "00_environment",
  paste0(
    execution_stage, "_", args$phase,
    if (is.null(args$rds_id)) "" else paste0(
      "_", gsub("[^A-Za-z0-9_.-]", "_", args$rds_id)
    ),
    "_task_graph.tsv"
  )
)
graph_path <- absolute_path(args$task_graph_output %||% default_graph, root)
atomic_write_tsv(task_graph, graph_path)
cat("Task graph: ", graph_path, "\n", sep = "")

if (args$dry_run) {
  print(task_graph[, c("stable_task_id", "task_mode", "rds_id", "scientific_script", "script_exists")],
    row.names = FALSE
  )
  if (any(!task_graph$script_exists)) {
    cat("Dry run is incomplete: scientific scripts marked FALSE have not been implemented.\n")
    quit(status = 3L)
  }
  quit(status = 0L)
}

missing_scripts <- unique(task_graph$scientific_script[!task_graph$script_exists])
if (length(missing_scripts)) {
  stop(
    "Cannot execute phase '", args$phase, "'; required scripts are missing: ",
    paste(missing_scripts, collapse = ", "),
    ". Implement the owning scientific phases before using --phase all.",
    call. = FALSE
  )
}

if (args$phase == "environment") {
  env_args <- c(
    absolute_path("scripts/00_check_environment.R", root),
    "--config", config_path,
    "--execution-config", execution_path
  )
  exit_code <- system2("Rscript", env_args)
  quit(status = exit_code)
}

# Scientific tasks use either the shared per-RDS runner or the same global
# scientific entry point in every execution stage.
implemented_global_modes <- c(
  "cohort", "annotations", "contrasts", "annotate_genes", "similarity"
)
unsupported_global <- task_graph$task_mode[
  is.na(task_graph$manifest_row) &
    !task_graph$task_mode %in% implemented_global_modes
]
if (length(unsupported_global)) {
  stop(
    "Global scientific task execution is not implemented for: ",
    paste(unique(unsupported_global), collapse = ", "),
    call. = FALSE
  )
}

failed_tasks <- character()
for (i in seq_len(nrow(task_graph))) {
  row <- task_graph[i, , drop = FALSE]
  if (is.na(row$manifest_row)) {
    runner_args <- c(
      absolute_path(row$scientific_script, root),
      "--config", config_path,
      "--execution-config", execution_path,
      "--task-mode", row$task_mode
    )
  } else {
    runner_args <- c(
      absolute_path("scripts/run_one_rds.R", root),
      "--config", config_path,
      "--execution-config", execution_path,
      "--manifest-row", as.character(row$manifest_row),
      "--task-mode", row$task_mode,
      "--script", absolute_path(row$scientific_script, root)
    )
    if (isTRUE(args$force)) runner_args <- c(runner_args, "--force")
  }
  exit_code <- system2("Rscript", runner_args)
  if (exit_code != 0L) {
    failed_tasks <- c(failed_tasks, row$stable_task_id)
    if (isTRUE(execution$fail_fast)) quit(status = exit_code)
  }
}
if (length(failed_tasks)) {
  cat("Failed tasks: ", paste(failed_tasks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
