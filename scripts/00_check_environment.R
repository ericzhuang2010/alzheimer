#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, report = NULL, status = NULL)
  value_options <- c("--config", "--execution-config", "--report", "--status")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/00_check_environment.R --config FILE ",
        "[--execution-config FILE] [--report FILE] [--status FILE]\n",
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
  out
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

`%||%` <- function(x, y) if (is.null(x)) y else x

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

peak_ram_gib <- function() {
  status_path <- "/proc/self/status"
  if (!file.exists(status_path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(status_path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  kib <- suppressWarnings(as.numeric(gsub("[^0-9.]", "", line[[1L]])))
  kib / (1024^2)
}

git_revision <- function(root) {
  inside <- suppressWarnings(system2("git", c("-C", root, "rev-parse", "--is-inside-work-tree"),
    stdout = TRUE, stderr = FALSE
  ))
  inside_status <- attr(inside, "status")
  if (!length(inside) || (!is.null(inside_status) && inside_status != 0L) ||
    !identical(inside[[1L]], "true")) return("not_a_git_checkout")

  result <- suppressWarnings(system2("git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) "unborn_git_repository" else result[[1L]]
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("yaml", quietly = TRUE)) {
  stop("The R package 'yaml' is required for the Section 7 preflight.", call. = FALSE)
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
project_root_value <- config$project$root %||% "."
project_root <- normalizePath(absolute_path(project_root_value, invocation_root), mustWork = TRUE)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)

report_path <- absolute_path(args$report %||%
  file.path(config$outputs$root, "00_environment", "environment_checks.tsv"), project_root)
status_path <- absolute_path(args$status %||%
  file.path(config$outputs$root, "00_environment", "environment_status.tsv"), project_root)

checks <- list()
add_check <- function(check, passed, detail, required = TRUE) {
  checks[[length(checks) + 1L]] <<- data.frame(
    check = check,
    required = required,
    passed = isTRUE(passed),
    detail = as.character(detail),
    stringsAsFactors = FALSE
  )
}

add_check("project_root", identical(project_root, invocation_root), project_root)
add_check("analysis_config_exists", file.exists(analysis_path), analysis_path)
add_check("manifest_exists", file.exists(manifest_path), manifest_path)
add_check("clinical_csv_exists", file.exists(absolute_path(config$inputs$clinical_csv, project_root)),
  absolute_path(config$inputs$clinical_csv, project_root)
)
add_check("cell_metadata_exists", file.exists(absolute_path(config$inputs$cell_metadata_tsv, project_root)),
  absolute_path(config$inputs$cell_metadata_tsv, project_root)
)

analysis <- if (file.exists(analysis_path)) yaml::read_yaml(analysis_path) else list()
minimum_r <- analysis$environment$minimum_r_version %||% "4.3.3"
add_check("r_version", getRversion() >= numeric_version(minimum_r),
  paste("observed", getRversion(), "required", minimum_r)
)

required_packages <- unlist(analysis$environment$required_packages %||% character(), use.names = FALSE)
for (package in required_packages) {
  installed <- requireNamespace(package, quietly = TRUE)
  version <- if (installed) as.character(utils::packageVersion(package)) else "MISSING"
  add_check(paste0("r_package_", package), installed, version)
}

gtf_rel <- analysis$references$gencode_gtf %||% ""
gtf_path <- absolute_path(gtf_rel, project_root)
gtf_exists <- nzchar(gtf_rel) && file.exists(gtf_path)
add_check("gencode_gtf_exists", gtf_exists, gtf_path)
if (gtf_exists) {
  gzip_status <- system2("gzip", c("-t", shQuote(gtf_path)), stdout = FALSE, stderr = FALSE)
  add_check("gencode_gtf_gzip_integrity", identical(gzip_status, 0L), paste("exit", gzip_status))
  expected_gtf_sha <- analysis$references$gencode_gtf_sha256 %||% ""
  observed_gtf_sha <- sha256_file(gtf_path)
  add_check("gencode_gtf_sha256", identical(observed_gtf_sha, expected_gtf_sha), observed_gtf_sha)
}

mitocarta_rel <- analysis$references$mitocarta_source %||% ""
mitocarta_path <- absolute_path(mitocarta_rel, project_root)
add_check(
  "mitocarta_source_exists",
  nzchar(mitocarta_rel) && file.exists(mitocarta_path),
  paste(mitocarta_path, "(required when annotations starts)"),
  required = FALSE
)

manifest <- NULL
if (file.exists(manifest_path)) {
  manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
  required_columns <- c(
    "manifest_row", "rds_id", "stable_rds_task_id", "input_rds",
    "estimated_peak_ram_gib", "enabled"
  )
  missing_columns <- setdiff(required_columns, names(manifest))
  add_check("manifest_schema", !length(missing_columns),
    if (length(missing_columns)) paste("missing", paste(missing_columns, collapse = ",")) else "ok"
  )
  if (!length(missing_columns)) {
    enabled <- toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES")
    selected <- manifest[enabled, , drop = FALSE]
    add_check("manifest_has_enabled_rows", nrow(selected) > 0L, paste(nrow(selected), "enabled rows"))
    add_check("manifest_unique_rows", !anyDuplicated(selected$manifest_row), "manifest_row")
    add_check("manifest_unique_rds_ids", !anyDuplicated(selected$rds_id), "rds_id")
    add_check("manifest_unique_task_ids", !anyDuplicated(selected$stable_rds_task_id), "stable_rds_task_id")
    for (i in seq_len(nrow(selected))) {
      input_path <- absolute_path(selected$input_rds[[i]], project_root)
      add_check(paste0("input_rds_", selected$rds_id[[i]]), file.exists(input_path), input_path)
    }

    # The local pilot is intentionally small enough for an environment-level
    # compatibility read. Production objects are audited later, one at a time.
    if (isTRUE(config$scope$pilot) && nrow(selected) == 1L &&
      file.exists(absolute_path(selected$input_rds[[1L]], project_root)) &&
      requireNamespace("Seurat", quietly = TRUE)) {
      smoke <- tryCatch(
        readRDS(absolute_path(selected$input_rds[[1L]], project_root)),
        error = function(e) e
      )
      read_ok <- !inherits(smoke, "error")
      add_check("phase1_rds_smoke_read", read_ok,
        if (read_ok) paste(class(smoke), collapse = ",") else conditionMessage(smoke)
      )
      if (read_ok) {
        observed_dim <- dim(smoke)
        expected_features <- suppressWarnings(as.integer(selected$expected_features[[1L]]))
        expected_cells <- suppressWarnings(as.integer(selected$expected_cells[[1L]]))
        add_check("phase1_rds_is_seurat", inherits(smoke, "Seurat"), paste(class(smoke), collapse = ","))
        add_check("phase1_rds_dimensions",
          identical(as.integer(observed_dim), c(expected_features, expected_cells)),
          paste(observed_dim, collapse = "x")
        )
        rm(smoke)
        invisible(gc())
      }
    }
  }
}

if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  add_check("execution_config_exists", file.exists(execution_path), execution_path)
  if (file.exists(execution_path)) {
    execution_config <- yaml::read_yaml(execution_path)
    allocation <- execution_config$execution
    total_memory <- as.numeric(allocation$total_memory_gib %||% NA)
    reserve_memory <- as.numeric(allocation$reserve_memory_gib %||% NA)
    add_check("memory_budget", is.finite(total_memory) && is.finite(reserve_memory) &&
      total_memory > reserve_memory && reserve_memory >= 0,
    paste("total", total_memory, "GiB reserve", reserve_memory, "GiB"))
    max_cores <- as.integer(allocation$max_total_cores %||% NA)
    add_check("core_budget", !is.na(max_cores) && max_cores >= 1L,
      paste("max_total_cores", max_cores)
    )
  }
}

dir.create(output_root, recursive = TRUE, showWarnings = FALSE)
probe <- tempfile("write_probe_", tmpdir = output_root)
write_ok <- tryCatch({
  writeLines("ok", probe)
  unlink(probe)
  TRUE
}, error = function(e) FALSE)
add_check("output_root_writable", write_ok, output_root)

check_table <- do.call(rbind, checks)
required_failures <- check_table$required & !check_table$passed
overall_status <- if (any(required_failures)) "failed" else "validated_complete"
atomic_write_tsv(check_table, report_path)

execution_phase <- NA_integer_
backend <- NA_character_
run_id <- NA_character_
if (!is.null(args$execution_config) && file.exists(absolute_path(args$execution_config, project_root))) {
  execution_config <- yaml::read_yaml(absolute_path(args$execution_config, project_root))
  execution_phase <- execution_config$execution$execution_phase %||% NA_integer_
  backend <- execution_config$execution$backend %||% NA_character_
  run_id <- execution_config$execution$run_id %||% NA_character_
}

status <- data.frame(
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = "global:environment",
  source_rds = NA_character_,
  scientific_script = "scripts/00_check_environment.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/00_check_environment.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = overall_status,
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, status_path)

cat("Environment report: ", report_path, "\n", sep = "")
cat("Environment status: ", overall_status, "\n", sep = "")
if (any(required_failures)) {
  failed <- check_table$check[required_failures]
  cat("Required checks failed: ", paste(failed, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
