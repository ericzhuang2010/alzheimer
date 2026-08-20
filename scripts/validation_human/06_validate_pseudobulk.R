#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/06_validate_pseudobulk.R --config FILE\n")
      quit(status = 0L)
    }
    if (key != "--config" || i == length(args)) stop("Unknown option or missing value: ", key)
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, tmp, sep = "\t", na = "NA", quote = FALSE,
                     compress = if (grepl("[.]gz$", path)) "gzip" else "none")
  if (!file.rename(tmp, path)) stop("Atomic rename failed: ", path)
}

atomic_save_rds <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  saveRDS(x, tmp, compress = "gzip")
  if (!file.rename(tmp, path)) stop("Atomic rename failed: ", path)
}

sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)

require_status <- function(path, allowed = "validated_complete") {
  if (!file.exists(path)) stop("Missing upstream status: ", path)
  value <- data.table::fread(path, integer64 = "double")
  if (nrow(value) != 1L || !"validation_status" %in% names(value)) {
    stop("Malformed upstream status: ", path)
  }
  if (!value$validation_status[[1L]] %in% allowed) {
    stop("Upstream phase is not validated: ", path)
  }
  value
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "Matrix")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
required_root <- normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)
if (!identical(output_root, required_root)) stop("Output root is not isolated validation_human")

require_status(file.path(output_root, "02_cohort/status.tsv"))
require_status(file.path(output_root, "03_genes/status.tsv"))
require_status(file.path(output_root, "04_cell_manifest/status.tsv"))
vh05_status <- require_status(file.path(output_root, "05_pseudobulk/status.tsv"))
if (!isTRUE(as.logical(vh05_status$production_run[[1L]]))) stop("VH05 status is not a production run")

input_dir <- file.path(output_root, "05_pseudobulk")
output_dir <- file.path(output_root, "06_pseudobulk_qc")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

counts_table <- data.table::fread(file.path(input_dir, "seaad_broad_pseudobulk_counts.tsv.gz"), integer64 = "double")
if (names(counts_table)[[1L]] != "gene") stop("First pseudobulk column must be gene")
genes <- as.character(counts_table$gene)
count_columns <- setdiff(names(counts_table), "gene")
counts <- as.matrix(counts_table[, count_columns, with = FALSE])
storage.mode(counts) <- "double"
rownames(counts) <- genes
rm(counts_table)
samples <- data.table::fread(file.path(input_dir, "seaad_broad_pseudobulk_samples.tsv"),
                            data.table = FALSE)
cohort <- data.table::fread(file.path(output_root, "02_cohort/donor_cohort_primary.tsv"),
                           data.table = FALSE)
feature_order <- data.table::fread(file.path(output_root, "03_genes/feature_order.tsv"),
                                  data.table = FALSE)
annotation <- data.table::fread(file.path(output_root, "03_genes/gene_annotation_master.tsv"),
                               data.table = FALSE)
nucleus_counts <- data.table::fread(
  file.path(output_root, "04_cell_manifest/donor_context_nucleus_counts.tsv"),
  data.table = FALSE
)
conservation <- data.table::fread(file.path(input_dir, "count_conservation.tsv"),
                                 data.table = FALSE, integer64 = "double")

sample_match <- match(samples$donor_id, cohort$donor_id)
cohort_join_complete <- !anyNA(sample_match)
sample_ids_align <- identical(colnames(counts), as.character(samples$pseudobulk_id))
gene_order_align <- identical(genes, as.character(feature_order$source_symbol))
annotation_align <- identical(genes, as.character(annotation$source_symbol))
counts_integer <- all(is.finite(counts)) && all(counts >= 0) &&
  all(counts == floor(counts))
library_size <- colSums(counts)
samples$library_size_recalculated <- as.numeric(library_size)
samples$primary_eligible <- samples$nuclei >= config$thresholds$primary_min_nuclei
samples$sensitivity_eligible <- samples$nuclei >= config$thresholds$sensitivity_min_nuclei
samples$ineligibility_reason <- ifelse(
  samples$primary_eligible, "",
  paste0("nuclei_below_", config$thresholds$primary_min_nuclei)
)

if (cohort_join_complete) {
  compare_fields <- c("diagnosis", "sex", "apoe_group", "age_death", "pmi",
                      "study", "age_death_scaled", "pmi_scaled")
  join_consistent <- all(vapply(compare_fields, function(field) {
    source <- cohort[[field]][sample_match]
    target <- samples[[field]]
    if (is.numeric(source)) isTRUE(all.equal(source, target, tolerance = 1e-12))
    else identical(as.character(source), as.character(target))
  }, logical(1)))
} else {
  join_consistent <- FALSE
}

mtdna <- as.logical(annotation$is_mtdna_protein_coding)
mito_umi <- if (any(mtdna)) colSums(counts[mtdna, , drop = FALSE]) else rep(0, ncol(counts))
library_qc <- data.frame(
  pseudobulk_id = samples$pseudobulk_id,
  donor_id = samples$donor_id,
  context = samples$context,
  nuclei = samples$nuclei,
  library_size = as.numeric(library_size),
  detected_genes = colSums(counts > 0),
  mtdna_protein_umi = as.numeric(mito_umi),
  mtdna_protein_fraction = ifelse(library_size > 0, mito_umi / library_size, NA_real_)
)

eligibility <- samples[, c(
  "pseudobulk_id", "donor_id", "context", "nuclei",
  "primary_eligible", "sensitivity_eligible", "ineligibility_reason"
)]
coverage <- aggregate(
  primary_eligible ~ context,
  data = samples,
  FUN = sum
)
names(coverage)[[2L]] <- "eligible_profiles"
expected_coverage <- unlist(config$expected$primary_eligible_profiles)
coverage$expected_profiles <- as.integer(expected_coverage[coverage$context])
coverage$matches_expected <- coverage$eligible_profiles == coverage$expected_profiles

source_selected <- conservation$value[conservation$quantity == "source_umi_selected_nuclei"]
pseudobulk_source <- conservation$value[conservation$quantity == "pseudobulk_umi_total"]
recheck <- data.frame(
  quantity = c("VH05_selected_source", "VH05_pseudobulk", "R_matrix_total",
               "VH05_selected_minus_R_matrix"),
  value = c(source_selected, pseudobulk_source, sum(counts),
            source_selected - sum(counts))
)

checks <- data.frame(
  check = c(
    "sample_columns_align", "feature_order_align", "annotation_align",
    "counts_nonnegative_integer", "nonzero_library_sizes",
    "donor_join_complete", "donor_metadata_join_consistent",
    "count_conservation_recheck", "expected_context_coverage",
    "all_seven_contexts", "rds_reload"
  ),
  passed = c(
    sample_ids_align, gene_order_align, annotation_align, counts_integer,
    all(library_size > 0), cohort_join_complete, join_consistent,
    length(source_selected) == 1L && source_selected == sum(counts),
    all(coverage$matches_expected), length(unique(samples$context)) == 7L,
    TRUE
  ),
  observed = c(
    ncol(counts), length(genes), nrow(annotation), counts_integer,
    min(library_size), sum(!is.na(sample_match)), join_consistent,
    source_selected - sum(counts),
    paste(paste0(coverage$context, "=", coverage$eligible_profiles), collapse = ";"),
    length(unique(samples$context)), "pending"
  ),
  expected = c(
    nrow(samples), nrow(feature_order), nrow(annotation), TRUE, ">0",
    nrow(samples), TRUE, 0,
    paste(paste0(names(expected_coverage), "=", expected_coverage), collapse = ";"),
    7, "reloadable"
  ),
  details = "",
  stringsAsFactors = FALSE
)

bundle <- list(
  schema_version = "seaad_broad_pseudobulk_v1",
  counts = counts,
  samples = samples,
  genes = annotation,
  feature_order_sha256 = feature_order$feature_order_sha256[[1L]],
  source_vh05_status_sha256 = sha256_file(file.path(input_dir, "status.tsv")),
  config_sha256 = sha256_file(config_path)
)
paths <- list(
  rds = file.path(output_dir, "seaad_broad_pseudobulk.rds"),
  samples = file.path(output_dir, "pseudobulk_samples.tsv"),
  eligibility = file.path(output_dir, "donor_context_eligibility.tsv"),
  library_qc = file.path(output_dir, "library_qc.tsv"),
  conservation = file.path(output_dir, "count_conservation_recheck.tsv"),
  checks = file.path(output_dir, "pseudobulk_qc_checks.tsv"),
  status = file.path(output_dir, "status.tsv")
)
atomic_save_rds(bundle, paths$rds)
reloaded <- tryCatch(readRDS(paths$rds), error = function(e) NULL)
reload_ok <- !is.null(reloaded) &&
  identical(dim(reloaded$counts), dim(counts)) &&
  identical(colnames(reloaded$counts), colnames(counts)) &&
  identical(reloaded$samples$pseudobulk_id, samples$pseudobulk_id)
checks$passed[checks$check == "rds_reload"] <- reload_ok
checks$observed[checks$check == "rds_reload"] <- reload_ok
rm(reloaded)

atomic_fwrite(samples, paths$samples)
atomic_fwrite(eligibility, paths$eligibility)
atomic_fwrite(library_qc, paths$library_qc)
atomic_fwrite(recheck, paths$conservation)
atomic_fwrite(checks, paths$checks)

failed <- checks$check[!checks$passed]
validation_status <- if (length(failed)) "failed" else "validated_complete"
status <- data.frame(
  schema_version = "seaad_phase_status_v1",
  phase = "VH06",
  validation_status = validation_status,
  failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  pseudobulk_groups = ncol(counts),
  features = nrow(counts),
  primary_eligible_profiles = sum(samples$primary_eligible),
  sensitivity_eligible_profiles = sum(samples$sensitivity_eligible),
  total_umi = sum(counts),
  feature_order_sha256 = feature_order$feature_order_sha256[[1L]],
  config_sha256 = sha256_file(config_path),
  stringsAsFactors = FALSE
)
atomic_fwrite(status, paths$status)
cat("VH06 status: ", validation_status, "; groups: ", ncol(counts), "\n", sep = "")
if (length(failed)) quit(status = 2L)
