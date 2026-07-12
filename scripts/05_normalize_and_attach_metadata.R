#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = "normalize"
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--task-mode"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/05_normalize_and_attach_metadata.R ",
        "--config FILE [--execution-config FILE] ",
        "[--manifest-row N | --rds-id ID] [--task-mode normalize]\n",
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
  if (is.null(out$manifest_row) == is.null(out$rds_id)) {
    stop("Specify exactly one of --manifest-row or --rds-id", call. = FALSE)
  }
  if (!identical(out$task_mode, "normalize")) {
    stop("--task-mode must be 'normalize'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
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
  status_path <- "/proc/self/status"
  if (!file.exists(status_path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(status_path, warn = FALSE), value = TRUE)
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

normalize_id <- function(x, width) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "NaN")] <- NA_character_
  valid <- !is.na(x)
  x[valid] <- vapply(
    x[valid],
    function(value) {
      if (grepl("^[0-9]+$", value) && nchar(value) < width) {
        paste0(strrep("0", width - nchar(value)), value)
      } else {
        value
      }
    },
    character(1)
  )
  x
}

get_assay_layer <- function(object, assay, layer) {
  tryCatch(
    SeuratObject::LayerData(object, assay = assay, layer = layer),
    error = function(e) {
      tryCatch(
        SeuratObject::GetAssayData(object, assay = assay, slot = layer),
        error = function(e2) NULL
      )
    }
  )
}

matrix_sha256 <- function(matrix) {
  digest::digest(matrix, algo = "sha256", serialize = TRUE)
}

make_formula_samples <- function(counts, scale_factor, seed, sample_size = 500L) {
  if (!inherits(counts, "dgCMatrix")) {
    counts <- methods::as(counts, "dgCMatrix")
  }
  set.seed(seed)
  nonzero_n <- min(as.integer(sample_size), length(counts@x))
  nonzero_index <- if (nonzero_n) {
    sort(sample.int(length(counts@x), nonzero_n))
  } else {
    integer()
  }
  nonzero_rows <- if (length(nonzero_index)) counts@i[nonzero_index] + 1L else integer()
  nonzero_columns <- if (length(nonzero_index)) {
    findInterval(nonzero_index - 1L, counts@p)
  } else {
    integer()
  }
  # Coerce dimensions before multiplication: large Minerva matrices exceed
  # R's 32-bit integer range even though only a small sample is requested.
  matrix_entries <- as.double(nrow(counts)) * as.double(ncol(counts))
  random_n <- as.integer(min(as.double(sample_size), matrix_entries))
  random_rows <- sample.int(nrow(counts), random_n, replace = TRUE)
  random_columns <- sample.int(ncol(counts), random_n, replace = TRUE)
  pairs <- unique(data.frame(
    row_index = c(nonzero_rows, random_rows),
    column_index = c(nonzero_columns, random_columns),
    stringsAsFactors = FALSE
  ))
  raw_count <- as.numeric(counts[cbind(pairs$row_index, pairs$column_index)])
  cell_total <- as.numeric(Matrix::colSums(counts))[pairs$column_index]
  pairs$feature <- rownames(counts)[pairs$row_index]
  pairs$barcode <- colnames(counts)[pairs$column_index]
  pairs$raw_count <- raw_count
  pairs$cell_total <- cell_total
  pairs$expected_normalized <- log1p(raw_count / cell_total * scale_factor)
  pairs
}

observe_formula_samples <- function(data_layer, samples, field) {
  values <- as.numeric(data_layer[cbind(samples$row_index, samples$column_index)])
  samples[[field]] <- values
  samples[[paste0(field, "_absolute_error")]] <- abs(
    values - samples$expected_normalized
  )
  samples
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c(
  "yaml", "Matrix", "RcppAnnoy", "Seurat", "SeuratObject",
  "data.table", "digest"
)
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

# This load order prevents the Minerva RcppAnnoy lazy-module failure.
suppressPackageStartupMessages({
  library(RcppAnnoy)
  library(Seurat)
})

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
if (!file.exists(analysis_path)) stop("Analysis config does not exist", call. = FALSE)
if (!file.exists(manifest_path)) stop("Manifest does not exist", call. = FALSE)
analysis <- yaml::read_yaml(analysis_path)

manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
if (!is.null(args$manifest_row)) {
  selected <- manifest[manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
} else {
  selected <- manifest[manifest$rds_id == args$rds_id, , drop = FALSE]
}
if (nrow(selected) != 1L) stop("Manifest selection must identify exactly one row", call. = FALSE)
if (!toupper(as.character(selected$enabled[[1L]])) %in% c("TRUE", "T", "1", "YES")) {
  stop("Selected manifest row is disabled", call. = FALSE)
}

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
source_path <- absolute_path(source_rel, project_root)
if (!file.exists(source_path)) stop("Input RDS does not exist: ", source_path, call. = FALSE)
source_sha_before <- sha256_file(source_path)
base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_path))

audit_path <- file.path(output_root, "01_audit", paste0(base_name, ".audit.tsv"))
if (!file.exists(audit_path)) stop("Required Phase 01 audit is missing: ", audit_path, call. = FALSE)
audit <- data.table::fread(audit_path, integer64 = "double", data.table = FALSE)
if (nrow(audit) != 1L || !identical(audit$validation_status[[1L]], "validated_complete")) {
  stop("Phase 01 audit must contain one validated_complete row", call. = FALSE)
}

intersections_path <- file.path(output_root, "02_cohort", "cohort_rds_intersections.tsv")
if (!file.exists(intersections_path)) stop("Cohort intersection manifest is missing", call. = FALSE)
intersections <- data.table::fread(
  intersections_path, integer64 = "double", data.table = FALSE
)
intersection <- intersections[intersections$rds_id == rds_id, , drop = FALSE]
if (nrow(intersection) != 1L) stop("Cohort intersection must identify one row", call. = FALSE)
cohort_path <- absolute_path(as.character(intersection$output_file[[1L]]), project_root)
if (!file.exists(cohort_path)) stop("RDS cohort is missing: ", cohort_path, call. = FALSE)
cohort <- data.table::fread(
  cohort_path, colClasses = c(projid = "character"),
  integer64 = "double", data.table = FALSE
)
projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
cohort$projid <- normalize_id(cohort$projid, projid_width)
if (anyNA(cohort$projid) || anyDuplicated(cohort$projid)) {
  stop("Cohort projid values must be complete and unique", call. = FALSE)
}

qc_dir <- file.path(output_root, "04_qc")
qc_path <- file.path(qc_dir, paste0(tolower(rds_id), "_cell_qc.tsv.gz"))
qc_status_path <- file.path(qc_dir, paste0(tolower(rds_id), "_qc_status.tsv"))
if (!file.exists(qc_path)) stop("Phase 04 cell QC is missing: ", qc_path, call. = FALSE)
if (!file.exists(qc_status_path)) stop("Phase 04 QC status is missing", call. = FALSE)
qc_status <- data.table::fread(
  qc_status_path, integer64 = "double", data.table = FALSE
)
if (nrow(qc_status) != 1L || !identical(qc_status$validation_status[[1L]], "validated_complete")) {
  stop("Phase 04 must be validated_complete before normalization", call. = FALSE)
}
qc <- data.table::fread(
  qc_path,
  colClasses = c(barcode = "character", projid = "character"),
  integer64 = "double", data.table = FALSE
)

message("Reading source Seurat object: ", source_path)
object <- readRDS(source_path)
if (!inherits(object, "Seurat")) stop("Input is not a Seurat object", call. = FALSE)
assay <- analysis$normalization$assay %||% "RNA"
method <- analysis$normalization$method %||% "LogNormalize"
scale_factor <- as.numeric(analysis$normalization$scale_factor %||% 10000)
if (!assay %in% SeuratObject::Assays(object)) stop("Required assay is absent", call. = FALSE)
if (!identical(method, "LogNormalize")) stop("Phase 05 requires LogNormalize", call. = FALSE)
if (!is.finite(scale_factor) || scale_factor <= 0) stop("Scale factor must be positive", call. = FALSE)
SeuratObject::DefaultAssay(object) <- assay
counts <- get_assay_layer(object, assay, "counts")
if (is.null(counts)) stop("Raw counts layer is absent", call. = FALSE)
cells <- colnames(counts)
features <- rownames(counts)
source_dimensions <- dim(object)
source_counts_sha256 <- matrix_sha256(counts)
cell_totals <- as.numeric(Matrix::colSums(counts))
if (any(!is.finite(cell_totals)) || any(cell_totals <= 0)) {
  stop("Every nucleus must have a positive finite raw RNA total", call. = FALSE)
}

source_metadata <- object[[]]
if (!identical(rownames(source_metadata), cells)) {
  source_metadata <- source_metadata[match(cells, rownames(source_metadata)), , drop = FALSE]
}
if (!all(c("projid", "cell_type_high_resolution") %in% names(source_metadata))) {
  stop("Source metadata lacks projid or cell_type_high_resolution", call. = FALSE)
}
source_projid <- normalize_id(source_metadata$projid, projid_width)
source_cell_type <- trimws(as.character(source_metadata$cell_type_high_resolution))

qc_index <- match(cells, qc$barcode)
if (anyNA(qc_index) || anyDuplicated(qc$barcode) || nrow(qc) != length(cells)) {
  stop("Phase 04 QC must match source barcodes one-to-one", call. = FALSE)
}
qc <- qc[qc_index, , drop = FALSE]
if (!identical(cells, qc$barcode)) stop("QC barcode order could not be aligned", call. = FALSE)
if (!identical(source_projid, normalize_id(qc$projid, projid_width))) {
  stop("QC projid values disagree with the source object", call. = FALSE)
}
if (!identical(source_cell_type, trimws(as.character(qc$cell_type_high_resolution)))) {
  stop("QC cell types disagree with the source object", call. = FALSE)
}

cohort_index <- match(source_projid, cohort$projid)
cohort_included <- !is.na(cohort_index)
if (!identical(cohort_included, as.logical(qc$cohort_included))) {
  stop("Cohort membership disagrees between Phase 02 and Phase 04", call. = FALSE)
}

cohort_fields <- c(
  "diagnosis", "sex", "apoe_group", "age_death_numeric", "age_90plus",
  "pmi_numeric", "pmi_log1p", "age_death_scaled", "pmi_scaled"
)
missing_cohort_fields <- setdiff(cohort_fields, names(cohort))
if (length(missing_cohort_fields)) {
  stop("Cohort fields missing: ", paste(missing_cohort_fields, collapse = ", "), call. = FALSE)
}
qc_fields <- c(
  "nCount_RNA", "nFeature_RNA", "nCount_MT", "percent_mt", "nFeature_MT",
  "nCount_MitoCarta", "percent_mitocarta", "flag_low_nCount_RNA",
  "flag_high_nCount_RNA", "flag_low_nFeature_RNA", "flag_high_nFeature_RNA",
  "flag_high_percent_mt", "flag_high_percent_mitocarta", "flag_zero_mt",
  "robust_any_flag", "flag_reasons"
)
missing_qc_fields <- setdiff(qc_fields, names(qc))
if (length(missing_qc_fields)) {
  stop("QC fields missing: ", paste(missing_qc_fields, collapse = ", "), call. = FALSE)
}

attached <- data.frame(
  projid = source_projid,
  cell_type_high_resolution = source_cell_type,
  cohort_included = cohort_included,
  stringsAsFactors = FALSE,
  row.names = cells
)
for (field in cohort_fields) attached[[field]] <- cohort[[field]][cohort_index]
for (field in qc_fields) attached[[field]] <- qc[[field]]
object <- SeuratObject::AddMetaData(object, metadata = attached)
metadata_after_join <- object[[]]

formula_samples <- make_formula_samples(
  counts, scale_factor = scale_factor,
  seed = as.integer(analysis$analysis$seed %||% 20260711L)
)

message(
  "Running Seurat NormalizeData: method=", method,
  ", scale.factor=", format(scale_factor, scientific = FALSE)
)
object <- Seurat::NormalizeData(
  object = object,
  assay = assay,
  normalization.method = method,
  scale.factor = scale_factor,
  verbose = TRUE
)
data_after <- get_assay_layer(object, assay, "data")
counts_after <- get_assay_layer(object, assay, "counts")
if (is.null(data_after) || is.null(counts_after)) {
  stop("Normalized data or preserved counts layer is absent", call. = FALSE)
}
counts_after_sha256 <- matrix_sha256(counts_after)
formula_samples <- observe_formula_samples(
  data_after, formula_samples, "observed_in_memory"
)

normalized_dir <- file.path(output_root, "05_normalized")
dir.create(normalized_dir, recursive = TRUE, showWarnings = FALSE)
paths <- list(
  object = file.path(normalized_dir, paste0(base_name, ".normalized.rds")),
  samples = file.path(normalized_dir, paste0(base_name, ".normalization_formula_samples.tsv")),
  validation = file.path(normalized_dir, paste0(base_name, ".normalization_validation.tsv")),
  manifest = file.path(normalized_dir, paste0(base_name, ".normalization_manifest.tsv")),
  status = file.path(normalized_dir, paste0(base_name, ".normalization_status.tsv"))
)

object_tmp <- paste0(paths$object, ".tmp.", Sys.getpid())
saveRDS(object, object_tmp, compress = TRUE)
source_sha_after <- sha256_file(source_path)

in_memory_dimensions <- dim(object)
in_memory_metadata <- object[[]]
rm(object, counts, counts_after, data_after)
invisible(gc())

message("Reloading normalized object for validation: ", object_tmp)
reloaded <- readRDS(object_tmp)
reload_is_seurat <- inherits(reloaded, "Seurat")
reload_counts <- get_assay_layer(reloaded, assay, "counts")
reload_data <- get_assay_layer(reloaded, assay, "data")
if (is.null(reload_counts) || is.null(reload_data)) {
  stop("Reloaded object lacks counts or normalized data", call. = FALSE)
}
reload_counts_sha256 <- matrix_sha256(reload_counts)
formula_samples <- observe_formula_samples(
  reload_data, formula_samples, "observed_after_reload"
)
reload_metadata <- reloaded[[]]
reload_dimensions <- dim(reloaded)

if (!file.rename(object_tmp, paths$object)) {
  stop("Could not atomically publish normalized object", call. = FALSE)
}
output_sha256 <- sha256_file(paths$object)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "normalization_validation_v1",
    rds_id = rds_id,
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}

tolerance <- 1e-8
in_memory_error <- max(formula_samples$observed_in_memory_absolute_error)
reload_error <- max(formula_samples$observed_after_reload_absolute_error)
attached_fields <- names(attached)
analytic_metadata <- metadata_after_join[metadata_after_join$cohort_included, , drop = FALSE]

add_check("source_feature_count_matches_audit", source_dimensions[[1L]] == audit$features[[1L]], source_dimensions[[1L]], audit$features[[1L]])
add_check("source_nucleus_count_matches_audit", source_dimensions[[2L]] == audit$nuclei[[1L]], source_dimensions[[2L]], audit$nuclei[[1L]])
add_check("phase04_status_validated", identical(qc_status$validation_status[[1L]], "validated_complete"), qc_status$validation_status[[1L]], "validated_complete")
add_check("qc_barcode_join_complete", identical(cells, qc$barcode), sum(cells == qc$barcode), length(cells))
add_check("cohort_membership_matches", identical(cohort_included, as.logical(qc$cohort_included)), sum(cohort_included), sum(qc$cohort_included))
add_check("analytic_donor_count", data.table::uniqueN(analytic_metadata$projid) == nrow(cohort), data.table::uniqueN(analytic_metadata$projid), nrow(cohort))
add_check("analytic_cohort_fields_complete", !anyNA(analytic_metadata[, cohort_fields, drop = FALSE]), sum(is.na(analytic_metadata[, cohort_fields, drop = FALSE])), 0L)
add_check("qc_numeric_fields_complete", !anyNA(metadata_after_join[, setdiff(qc_fields, "flag_reasons"), drop = FALSE]), sum(is.na(metadata_after_join[, setdiff(qc_fields, "flag_reasons"), drop = FALSE])), 0L)
add_check("in_memory_dimensions_unchanged", identical(in_memory_dimensions, source_dimensions), in_memory_dimensions, source_dimensions)
add_check("in_memory_counts_unchanged", identical(counts_after_sha256, source_counts_sha256), counts_after_sha256, source_counts_sha256)
add_check("normalized_data_dimensions", identical(dim(reload_data), source_dimensions), dim(reload_data), source_dimensions)
add_check("in_memory_formula_error", is.finite(in_memory_error) && in_memory_error <= tolerance, format(in_memory_error, scientific = TRUE), paste0("<=", tolerance))
add_check("reload_is_seurat", reload_is_seurat, reload_is_seurat, TRUE)
add_check("reload_dimensions_unchanged", identical(reload_dimensions, source_dimensions), reload_dimensions, source_dimensions)
add_check("reload_counts_unchanged", identical(reload_counts_sha256, source_counts_sha256), reload_counts_sha256, source_counts_sha256)
add_check("reload_formula_error", is.finite(reload_error) && reload_error <= tolerance, format(reload_error, scientific = TRUE), paste0("<=", tolerance))
add_check("metadata_fields_persisted", all(attached_fields %in% names(reload_metadata)), setdiff(attached_fields, names(reload_metadata)), "none_missing")
add_check("metadata_values_persisted", identical(reload_metadata[, attached_fields, drop = FALSE], in_memory_metadata[, attached_fields, drop = FALSE]), nrow(reload_metadata), nrow(in_memory_metadata))
add_check("source_rds_unchanged", identical(source_sha_after, source_sha_before), source_sha_after, source_sha_before)
add_check("published_output_readable", file.exists(paths$object) && is.finite(file.info(paths$object)$size) && file.info(paths$object)$size > 0, file.info(paths$object)$size, ">0")

validation <- do.call(rbind, checks)
failed_checks <- validation$check[!validation$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

formula_output <- data.frame(
  schema_version = "normalization_formula_samples_v1",
  rds_id = rds_id,
  formula_samples,
  stringsAsFactors = FALSE
)
atomic_write_tsv(formula_output, paths$samples)
atomic_write_tsv(validation, paths$validation)

artifact_paths <- c(paths$object, paths$samples, paths$validation)
artifact_records <- c(ncol(reloaded), nrow(formula_output), nrow(validation))
normalization_manifest <- data.frame(
  schema_version = "normalization_manifest_v1",
  rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = artifact_records,
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(normalization_manifest, paths$manifest)

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) "local_pilot_manual" else "manual_normalize"
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) stop("Execution config does not exist", call. = FALSE)
  execution <- yaml::read_yaml(execution_path)$execution
  execution_phase <- execution$execution_phase %||% execution_phase
  backend <- execution$backend %||% backend
  run_id <- execution$run_id %||% run_id
}

status <- data.frame(
  schema_version = "normalization_status_v1",
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = paste("normalize", rds_id, sep = ":"),
  source_rds = source_rel,
  source_rds_sha256 = source_sha_before,
  normalized_rds = sub(paste0("^", project_root, "/?"), "", paths$object),
  normalized_rds_sha256 = output_sha256,
  scientific_script = "scripts/05_normalize_and_attach_metadata.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/05_normalize_and_attach_metadata.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  phase01_audit_sha256 = sha256_file(audit_path),
  phase02_cohort_sha256 = sha256_file(cohort_path),
  phase04_qc_sha256 = sha256_file(qc_path),
  phase04_status_sha256 = sha256_file(qc_status_path),
  assay = assay,
  normalization_method = method,
  scale_factor = scale_factor,
  features = source_dimensions[[1L]],
  nuclei = source_dimensions[[2L]],
  analytic_nuclei = sum(cohort_included),
  analytic_donors = data.table::uniqueN(source_projid[cohort_included]),
  raw_counts_sha256 = source_counts_sha256,
  formula_samples = nrow(formula_samples),
  max_formula_error = max(in_memory_error, reload_error),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Normalized object: ", paths$object, "\n", sep = "")
cat("Dimensions: ", paste(source_dimensions, collapse = " x "), "\n", sep = "")
cat("Analytic nuclei: ", sum(cohort_included), "\n", sep = "")
cat("Analytic donors: ", data.table::uniqueN(source_projid[cohort_included]), "\n", sep = "")
cat("Formula samples: ", nrow(formula_samples), "\n", sep = "")
cat("Maximum formula error: ", format(max(in_memory_error, reload_error), scientific = TRUE), "\n", sep = "")
cat("Normalization status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
