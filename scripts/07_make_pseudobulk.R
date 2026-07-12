#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, input = NULL, cohort = NULL, task_mode = "pseudobulk"
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--input", "--cohort", "--task-mode"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/07_make_pseudobulk.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--input RDS --cohort TSV] [--task-mode pseudobulk]\n",
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
  if (!identical(out$task_mode, "pseudobulk")) {
    stop("--task-mode must be 'pseudobulk'", call. = FALSE)
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

atomic_save_rds <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  saveRDS(x, tmp, compress = "gzip")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

matrix_sha256 <- function(x) {
  digest::digest(x, algo = "sha256", serialize = TRUE)
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

normalize_id <- function(x, width) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "NaN")] <- NA_character_
  valid <- !is.na(x)
  x[valid] <- vapply(x[valid], function(value) {
    if (grepl("^[0-9]+$", value) && nchar(value) < width) {
      paste0(strrep("0", width - nchar(value)), value)
    } else {
      value
    }
  }, character(1))
  x
}

as_logical <- function(x) {
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

get_assay_layer <- function(object, assay, layer) {
  tryCatch(
    SeuratObject::LayerData(object, assay = assay, layer = layer),
    error = function(e) SeuratObject::GetAssayData(
      object, assay = assay, slot = layer
    )
  )
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

suppressPackageStartupMessages({
  library(RcppAnnoy)
  library(Seurat)
})

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)
manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)

if (!is.null(args$manifest_row)) {
  selected <- manifest[manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
} else if (!is.null(args$rds_id)) {
  selected <- manifest[manifest$rds_id == args$rds_id, , drop = FALSE]
} else if (!is.null(args$input)) {
  input_rel <- sub(paste0("^", project_root, "/?"), "", absolute_path(args$input, project_root))
  selected <- manifest[manifest$input_rds == input_rel, , drop = FALSE]
} else {
  stop("Select one input with --manifest-row, --rds-id, or --input", call. = FALSE)
}
if (nrow(selected) != 1L) stop("Manifest selection must identify exactly one row", call. = FALSE)
if (!as_logical(selected$enabled[[1L]])) stop("Selected manifest row is disabled", call. = FALSE)

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
source_path <- absolute_path(args$input %||% source_rel, project_root)
if (!file.exists(source_path)) stop("Input RDS does not exist: ", source_path, call. = FALSE)
source_sha256 <- sha256_file(source_path)
base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_path))

intersections_path <- file.path(output_root, "02_cohort", "cohort_rds_intersections.tsv")
if (!is.null(args$cohort)) {
  cohort_path <- absolute_path(args$cohort, project_root)
} else {
  if (!file.exists(intersections_path)) stop("Cohort intersection manifest is missing", call. = FALSE)
  intersections <- data.table::fread(intersections_path, data.table = FALSE)
  intersection <- intersections[intersections$rds_id == rds_id, , drop = FALSE]
  if (nrow(intersection) != 1L) stop("Cohort intersection must identify one row", call. = FALSE)
  cohort_path <- absolute_path(as.character(intersection$output_file[[1L]]), project_root)
}
if (!file.exists(cohort_path)) stop("Cohort file is missing: ", cohort_path, call. = FALSE)

qc_dir <- file.path(output_root, "04_qc")
qc_path <- file.path(qc_dir, paste0(tolower(rds_id), "_cell_qc.tsv.gz"))
qc_status_path <- file.path(qc_dir, paste0(tolower(rds_id), "_qc_status.tsv"))
if (!file.exists(qc_path) || !file.exists(qc_status_path)) {
  stop("Validated Phase 04 QC inputs are missing for ", rds_id, call. = FALSE)
}
qc_status <- data.table::fread(qc_status_path, data.table = FALSE)
if (nrow(qc_status) != 1L || qc_status$validation_status[[1L]] != "validated_complete") {
  stop("Phase 04 QC must be validated_complete", call. = FALSE)
}

projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
cohort <- data.table::fread(
  cohort_path, colClasses = c(projid = "character"), data.table = FALSE
)
cohort$projid <- normalize_id(cohort$projid, projid_width)
if (anyNA(cohort$projid) || anyDuplicated(cohort$projid)) {
  stop("Cohort projid values must be complete and unique", call. = FALSE)
}

qc <- data.table::fread(
  qc_path,
  colClasses = c(barcode = "character", projid = "character"),
  data.table = FALSE
)
qc$projid <- normalize_id(qc$projid, projid_width)

message("Reading source Seurat object: ", source_path)
object <- readRDS(source_path)
if (!inherits(object, "Seurat")) stop("Input is not a Seurat object", call. = FALSE)
object <- SeuratObject::UpdateSeuratObject(object)
if (!isTRUE(methods::validObject(object))) stop("Updated Seurat object is invalid", call. = FALSE)
assay <- analysis$normalization$assay %||% "RNA"
counts <- get_assay_layer(object, assay, "counts")
if (is.null(counts) || !inherits(counts, "sparseMatrix")) {
  stop("A sparse raw counts layer is required", call. = FALSE)
}
if (is.null(rownames(counts)) || is.null(colnames(counts))) {
  stop("Raw counts require feature and barcode names", call. = FALSE)
}

qc_index <- match(colnames(counts), qc$barcode)
if (anyNA(qc_index) || anyDuplicated(qc$barcode) || nrow(qc) != ncol(counts)) {
  stop("Phase 04 QC must match source barcodes one-to-one", call. = FALSE)
}
qc <- qc[qc_index, , drop = FALSE]
include <- as_logical(qc$cohort_included)
if (!any(include)) stop("No nuclei belong to the analytic cohort", call. = FALSE)
if (anyNA(qc$projid[include]) || any(!qc$projid[include] %in% cohort$projid)) {
  stop("Included nuclei contain donors outside the analytic cohort", call. = FALSE)
}
cell_type <- trimws(as.character(qc$cell_type_high_resolution))
if (any(!nzchar(cell_type[include])) || anyNA(cell_type[include])) {
  stop("Included nuclei require fine cell types", call. = FALSE)
}

included_index <- which(include)
cell_groups <- data.frame(
  projid = qc$projid[included_index],
  cell_type_high_resolution = cell_type[included_index],
  stringsAsFactors = FALSE
)
sample_keys <- unique(cell_groups)
sample_keys <- sample_keys[order(
  sample_keys$cell_type_high_resolution, sample_keys$projid
), , drop = FALSE]
sample_keys$sample_index <- seq_len(nrow(sample_keys))
sample_keys$pseudobulk_id <- sprintf("%s__pb%05d", rds_id, sample_keys$sample_index)
group_index <- match(
  paste(cell_groups$projid, cell_groups$cell_type_high_resolution, sep = "\r"),
  paste(sample_keys$projid, sample_keys$cell_type_high_resolution, sep = "\r")
)
if (anyNA(group_index)) stop("Could not map included nuclei to pseudobulk samples", call. = FALSE)

aggregation_matrix <- Matrix::sparseMatrix(
  i = seq_along(group_index), j = group_index, x = 1,
  dims = c(length(group_index), nrow(sample_keys))
)
message(
  "Aggregating ", length(included_index), " analytic-cohort nuclei into ",
  nrow(sample_keys), " donor-cell-type pseudobulk samples"
)
pseudobulk_counts <- counts[, included_index, drop = FALSE] %*% aggregation_matrix
pseudobulk_counts <- methods::as(pseudobulk_counts, "dgCMatrix")
rownames(pseudobulk_counts) <- rownames(counts)
colnames(pseudobulk_counts) <- sample_keys$pseudobulk_id

qc_included <- data.table::as.data.table(qc[included_index, , drop = FALSE])
qc_included[, cell_type_high_resolution := trimws(as.character(cell_type_high_resolution))]
qc_summary <- qc_included[, .(
  nuclei = .N,
  total_umi_count = sum(as.numeric(nCount_RNA)),
  total_mt_count = sum(as.numeric(nCount_MT)),
  aggregate_percent_mt = 100 * sum(as.numeric(nCount_MT)) / sum(as.numeric(nCount_RNA)),
  median_percent_mt = stats::median(as.numeric(percent_mt)),
  total_mitocarta_count = sum(as.numeric(nCount_MitoCarta)),
  aggregate_percent_mitocarta = 100 * sum(as.numeric(nCount_MitoCarta)) / sum(as.numeric(nCount_RNA)),
  median_percent_mitocarta = stats::median(as.numeric(percent_mitocarta)),
  robust_flagged_nuclei = sum(as_logical(robust_any_flag))
), by = .(projid, cell_type_high_resolution)]
qc_summary <- as.data.frame(qc_summary)

sample_match <- match(
  paste(sample_keys$projid, sample_keys$cell_type_high_resolution, sep = "\r"),
  paste(qc_summary$projid, qc_summary$cell_type_high_resolution, sep = "\r")
)
if (anyNA(sample_match)) stop("QC aggregation did not cover every pseudobulk sample", call. = FALSE)
samples <- cbind(sample_keys, qc_summary[sample_match, setdiff(names(qc_summary), c("projid", "cell_type_high_resolution")), drop = FALSE])
cohort_match <- match(samples$projid, cohort$projid)
if (anyNA(cohort_match)) stop("Pseudobulk donors are missing from the cohort", call. = FALSE)
cohort_fields <- c(
  "diagnosis", "sex", "apoe_group", "age_death_numeric", "age_90plus",
  "pmi_numeric", "pmi_log1p", "age_death_scaled", "pmi_scaled"
)
missing_fields <- setdiff(cohort_fields, names(cohort))
if (length(missing_fields)) {
  stop("Cohort fields missing: ", paste(missing_fields, collapse = ", "), call. = FALSE)
}
for (field in cohort_fields) samples[[field]] <- cohort[[field]][cohort_match]
minimum_primary <- as.integer(analysis$pseudobulk$minimum_nuclei_primary %||% 20L)
minimum_sensitivity <- as.integer(analysis$pseudobulk$minimum_nuclei_sensitivity %||% 50L)
samples$primary_eligible <- samples$nuclei >= minimum_primary
samples$sensitivity_eligible <- samples$nuclei >= minimum_sensitivity
samples$primary_ineligibility_reason <- ifelse(
  samples$primary_eligible, "", paste0("nuclei_below_", minimum_primary)
)
samples$sensitivity_ineligibility_reason <- ifelse(
  samples$sensitivity_eligible, "", paste0("nuclei_below_", minimum_sensitivity)
)
samples <- samples[, c(
  "pseudobulk_id", "sample_index", "projid", "cell_type_high_resolution",
  "diagnosis", "sex", "apoe_group", "age_death_numeric", "age_90plus",
  "pmi_numeric", "pmi_log1p", "age_death_scaled", "pmi_scaled",
  "nuclei", "total_umi_count", "total_mt_count", "aggregate_percent_mt",
  "median_percent_mt", "total_mitocarta_count", "aggregate_percent_mitocarta",
  "median_percent_mitocarta", "robust_flagged_nuclei", "primary_eligible",
  "sensitivity_eligible", "primary_ineligibility_reason",
  "sensitivity_ineligibility_reason"
)]
samples <- data.frame(
  schema_version = "pseudobulk_samples_v1", rds_id = rds_id,
  source_rds = source_rel, samples, stringsAsFactors = FALSE
)

source_gene_sums <- as.numeric(Matrix::rowSums(counts[, included_index, drop = FALSE]))
aggregate_gene_sums <- as.numeric(Matrix::rowSums(pseudobulk_counts))
gene_differences <- aggregate_gene_sums - source_gene_sums
sample_column_sums <- as.numeric(Matrix::colSums(pseudobulk_counts))
gene_wise_exact <- all(gene_differences == 0)
total_source <- sum(source_gene_sums)
total_aggregate <- sum(aggregate_gene_sums)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "pseudobulk_conservation_v1", rds_id = rds_id,
    check = check, passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}
add_check("phase04_status_validated", qc_status$validation_status[[1L]] == "validated_complete", qc_status$validation_status[[1L]], "validated_complete")
add_check("barcode_join_complete", identical(colnames(counts), qc$barcode), sum(colnames(counts) == qc$barcode), ncol(counts))
add_check("pseudobulk_dimensions", identical(dim(pseudobulk_counts), c(nrow(counts), nrow(samples))), dim(pseudobulk_counts), c(nrow(counts), nrow(samples)))
add_check("one_metadata_row_per_column", identical(colnames(pseudobulk_counts), samples$pseudobulk_id), nrow(samples), ncol(pseudobulk_counts))
add_check("nuclei_conserved", sum(samples$nuclei) == length(included_index), sum(samples$nuclei), length(included_index))
add_check("sample_umi_totals_match", identical(sample_column_sums, as.numeric(samples$total_umi_count)), sum(sample_column_sums != as.numeric(samples$total_umi_count)), 0L)
add_check("gene_wise_counts_conserved", gene_wise_exact, sum(gene_differences != 0), 0L)
add_check("maximum_gene_count_difference", max(abs(gene_differences)) == 0, max(abs(gene_differences)), 0)
add_check("total_umi_conserved", identical(total_source, total_aggregate), total_aggregate, total_source)
add_check("cohort_metadata_complete", !anyNA(samples[, cohort_fields, drop = FALSE]), sum(is.na(samples[, cohort_fields, drop = FALSE])), 0L)
add_check("primary_eligibility_consistent", identical(samples$primary_eligible, samples$nuclei >= minimum_primary), sum(samples$primary_eligible), sum(samples$nuclei >= minimum_primary))
conservation <- do.call(rbind, checks)
failed_checks <- conservation$check[!conservation$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "07_pseudobulk")
paths <- list(
  counts = file.path(output_dir, paste0(base_name, ".pseudobulk_counts.rds")),
  samples = file.path(output_dir, paste0(base_name, ".pseudobulk_samples.tsv")),
  conservation = file.path(output_dir, paste0(base_name, ".pseudobulk_count_conservation.tsv")),
  manifest = file.path(output_dir, paste0(base_name, ".pseudobulk_manifest.tsv")),
  status = file.path(output_dir, paste0(base_name, ".pseudobulk_status.tsv"))
)
bundle <- list(
  schema_version = "pseudobulk_counts_v1", rds_id = rds_id,
  source_rds = source_rel, source_rds_sha256 = source_sha256,
  assay = assay, count_source = "RNA_counts", counts = pseudobulk_counts,
  samples = samples, source_features = nrow(counts),
  source_nuclei = ncol(counts), included_nuclei = length(included_index),
  source_counts_sha256 = matrix_sha256(counts),
  pseudobulk_counts_sha256 = matrix_sha256(pseudobulk_counts)
)
atomic_save_rds(bundle, paths$counts)
atomic_write_tsv(samples, paths$samples)
atomic_write_tsv(conservation, paths$conservation)

artifact_paths <- c(paths$counts, paths$samples, paths$conservation)
artifact_manifest <- data.frame(
  schema_version = "pseudobulk_manifest_v1", rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(ncol(pseudobulk_counts), nrow(samples), nrow(conservation)),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifact_manifest, paths$manifest)

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct", run_id = "manual_pseudobulk"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}
status <- data.frame(
  schema_version = "pseudobulk_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = paste("pseudobulk", rds_id, sep = ":"),
  source_rds = source_rel, source_rds_sha256 = source_sha256,
  scientific_script = "scripts/07_make_pseudobulk.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/07_make_pseudobulk.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  cohort_sha256 = sha256_file(cohort_path), qc_sha256 = sha256_file(qc_path),
  features = nrow(pseudobulk_counts), pseudobulk_samples = ncol(pseudobulk_counts),
  included_nuclei = length(included_index), analytic_donors = length(unique(samples$projid)),
  fine_cell_types = length(unique(samples$cell_type_high_resolution)),
  primary_eligible_samples = sum(samples$primary_eligible),
  source_counts_sha256 = bundle$source_counts_sha256,
  pseudobulk_counts_sha256 = bundle$pseudobulk_counts_sha256,
  total_umi_count = total_aggregate,
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Pseudobulk counts: ", paths$counts, "\n", sep = "")
cat("Dimensions: ", paste(dim(pseudobulk_counts), collapse = " x "), "\n", sep = "")
cat("Pseudobulk samples: ", nrow(samples), "\n", sep = "")
cat("Primary-eligible samples: ", sum(samples$primary_eligible), "\n", sep = "")
cat("Included nuclei: ", length(included_index), "\n", sep = "")
cat("Count conservation: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
