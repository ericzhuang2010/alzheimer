#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/06_validate_pseudobulk.R --config FILE
")
      quit(status = 0L)
    }
    if (args[[i]] != "--config" || i == length(args)) stop("Unknown or incomplete argument: ", args[[i]])
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, temporary, sep = "	", na = "NA", quote = FALSE,
                     compress = if (grepl("[.]gz$", path)) "gzip" else "none")
  if (!file.rename(temporary, path)) stop("Atomic rename failed: ", path)
}

sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)

relative_path <- function(path, root) {
  normalized <- normalizePath(path, mustWork = TRUE)
  prefix <- paste0(normalizePath(root, mustWork = TRUE), "/")
  if (!startsWith(normalized, prefix)) stop("Artifact escapes project root: ", normalized)
  substring(normalized, nchar(prefix) + 1L)
}

require_phase <- function(output_root, phase, project_root) {
  directory <- file.path(output_root, phase)
  status_path <- file.path(directory, "status.tsv")
  artifact_path <- file.path(directory, "artifacts.tsv")
  if (!file.exists(status_path) || !file.exists(artifact_path)) stop("Missing predecessor records: ", phase)
  status <- data.table::fread(status_path, data.table = FALSE)
  if (nrow(status) != 1L || status$validation_status[[1L]] != "validated_complete") stop("Predecessor is not validated: ", phase)
  artifacts <- data.table::fread(artifact_path, data.table = FALSE)
  for (i in seq_len(nrow(artifacts))) {
    path <- file.path(project_root, artifacts$path[[i]])
    if (!file.exists(path) || file.info(path)$size != artifacts$bytes[[i]] ||
        sha256_file(path) != artifacts$digest_value[[i]]) stop("Predecessor artifact mismatch: ", path)
  }
  status
}

write_artifacts <- function(paths, destination, project_root) {
  rows <- lapply(paths, function(path) data.frame(
    artifact = basename(path),
    path = relative_path(path, project_root),
    artifact_role = "result",
    bytes = file.info(path)$size,
    digest_algorithm = "sha256",
    digest_scope = "full_file",
    digest_value = sha256_file(path),
    stringsAsFactors = FALSE
  ))
  atomic_fwrite(data.table::rbindlist(rows), destination)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "Matrix")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
if (output_root != normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)) stop("Unsafe output root")
require_phase(output_root, "02_cohort", project_root)
require_phase(output_root, "03_genes", project_root)
require_phase(output_root, "04_supertype_manifest", project_root)
vh05_status <- require_phase(output_root, "05_pseudobulk", project_root)

output_dir <- file.path(output_root, "06_pseudobulk_qc")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
manifest <- data.table::fread(file.path(output_root, "05_pseudobulk/pseudobulk_shard_manifest.tsv"), data.table = FALSE)
annotation <- data.table::fread(file.path(output_root, "03_genes/gene_annotation_master.tsv"), data.table = FALSE)
cohort <- data.table::fread(file.path(output_root, "02_cohort/donor_cohort_primary.tsv"), data.table = FALSE)
cohort$donor_id <- as.character(cohort$donor_id)
mapping <- data.table::fread(file.path(output_root, "04_supertype_manifest/supertype_to_broad_network.tsv"), data.table = FALSE)
broad_order <- unlist(config$taxonomy$broad_network_order)
expected_features <- as.integer(config$expected_identity$features)
expected_donors <- as.integer(config$expected_identity$analysis_donors)
mito_index <- which(as.logical(annotation$is_mtdna_gene))

profile_rows <- list()
fine_summary_rows <- list()
broad_summary_rows <- list()
reconciliation_rows <- list()
rollups <- setNames(lapply(broad_order, function(x) matrix(0, nrow = expected_features, ncol = expected_donors)), broad_order)
all_shards_valid <- TRUE
all_clinical_joins_valid <- TRUE
fine_total <- 0
broad_total <- 0

fine_manifest <- manifest[manifest$shard_type == "fine_supertype", , drop = FALSE]
fine_manifest <- fine_manifest[match(mapping$supertype_id, fine_manifest$context_id), , drop = FALSE]
for (i in seq_len(nrow(fine_manifest))) {
  shard <- fine_manifest[i, , drop = FALSE]
  counts_table <- data.table::fread(file.path(project_root, shard$counts_path), data.table = FALSE)
  samples <- data.table::fread(file.path(project_root, shard$samples_path), data.table = FALSE)
  valid <- nrow(counts_table) == expected_features &&
    nrow(samples) == expected_donors &&
    identical(as.integer(counts_table$feature_index), seq.int(0L, expected_features - 1L)) &&
    identical(as.character(counts_table$source_symbol), as.character(annotation$source_symbol)) &&
    identical(as.integer(samples$sample_order), seq.int(0L, expected_donors - 1L))
  all_shards_valid <- all_shards_valid && valid
  samples$donor_id <- as.character(samples$donor_id)
  joined <- merge(samples, cohort, by = "donor_id", suffixes = c("", ".cohort"), sort = FALSE)
  joined <- joined[match(samples$donor_id, joined$donor_id), , drop = FALSE]
  join_valid <- nrow(joined) == expected_donors &&
    all(joined$diagnosis == joined$diagnosis.cohort) &&
    all(joined$signature_group == joined$signature_group.cohort)
  all_clinical_joins_valid <- all_clinical_joins_valid && join_valid
  count_columns <- as.character(samples$pseudobulk_id)
  counts <- as.matrix(counts_table[, count_columns, drop = FALSE])
  storage.mode(counts) <- "double"
  if (any(!is.finite(counts)) || any(counts < 0) || any(counts != floor(counts))) stop("Invalid fine count shard: ", shard$context_id)
  libraries <- colSums(counts)
  detected <- colSums(counts > 0)
  mito_counts <- if (length(mito_index)) colSums(counts[mito_index, , drop = FALSE]) else rep(0, ncol(counts))
  mito_fraction <- ifelse(libraries > 0, mito_counts / libraries, NA_real_)
  primary_eligible <- samples$nuclei >= as.integer(config$thresholds$primary_min_nuclei)
  sensitivity_eligible <- samples$nuclei >= as.integer(config$thresholds$sensitivity_min_nuclei)
  profile_rows[[length(profile_rows) + 1L]] <- data.frame(
    resolution = "fine_supertype",
    context_id = shard$context_id,
    scientific_label = shard$scientific_label,
    broad_network = shard$broad_network,
    sample_order = samples$sample_order,
    pseudobulk_id = samples$pseudobulk_id,
    donor_id = samples$donor_id,
    nuclei = samples$nuclei,
    library_size = libraries,
    detected_features = detected,
    mtdna_umi_fraction = mito_fraction,
    primary_profile_eligible = primary_eligible,
    sensitivity_profile_eligible = sensitivity_eligible,
    diagnosis = samples$diagnosis,
    sex = samples$sex,
    apoe_group = samples$apoe_group,
    signature_group = samples$signature_group,
    age_death_scaled = samples$age_death_scaled,
    pmi_scaled = samples$pmi_scaled,
    study = samples$study,
    counts_path = shard$counts_path,
    samples_path = shard$samples_path,
    stringsAsFactors = FALSE
  )
  fine_summary_rows[[length(fine_summary_rows) + 1L]] <- data.frame(
    supertype_id = shard$context_id,
    supertype_label = shard$scientific_label,
    broad_network = shard$broad_network,
    structural_profiles = nrow(samples),
    primary_eligible_profiles = sum(primary_eligible),
    sensitivity_eligible_profiles = sum(sensitivity_eligible),
    total_nuclei = sum(samples$nuclei),
    total_umis = sum(libraries),
    median_library_size_eligible = if (any(primary_eligible)) median(libraries[primary_eligible]) else NA_real_,
    stringsAsFactors = FALSE
  )
  fine_total <- fine_total + sum(libraries)
  rollups[[shard$broad_network]] <- rollups[[shard$broad_network]] + counts
  rm(counts_table, counts, samples, joined)
  gc(verbose = FALSE)
}

broad_manifest <- manifest[manifest$shard_type == "direct_broad", , drop = FALSE]
broad_manifest <- broad_manifest[match(broad_order, broad_manifest$context_id), , drop = FALSE]
for (i in seq_len(nrow(broad_manifest))) {
  shard <- broad_manifest[i, , drop = FALSE]
  counts_table <- data.table::fread(file.path(project_root, shard$counts_path), data.table = FALSE)
  samples <- data.table::fread(file.path(project_root, shard$samples_path), data.table = FALSE)
  count_columns <- as.character(samples$pseudobulk_id)
  counts <- as.matrix(counts_table[, count_columns, drop = FALSE])
  storage.mode(counts) <- "double"
  valid <- nrow(counts_table) == expected_features && nrow(samples) == expected_donors &&
    identical(as.integer(counts_table$feature_index), seq.int(0L, expected_features - 1L)) &&
    identical(as.character(counts_table$source_symbol), as.character(annotation$source_symbol))
  all_shards_valid <- all_shards_valid && valid
  equal <- identical(unname(rollups[[shard$context_id]]), unname(counts))
  mismatches <- sum(rollups[[shard$context_id]] != counts)
  reconciliation_rows[[length(reconciliation_rows) + 1L]] <- data.frame(
    broad_network = shard$context_id,
    fine_rollup_umi_total = sum(rollups[[shard$context_id]]),
    direct_broad_umi_total = sum(counts),
    mismatched_gene_donor_cells = mismatches,
    exact_equal = equal,
    stringsAsFactors = FALSE
  )
  libraries <- colSums(counts)
  detected <- colSums(counts > 0)
  mito_counts <- if (length(mito_index)) colSums(counts[mito_index, , drop = FALSE]) else rep(0, ncol(counts))
  mito_fraction <- ifelse(libraries > 0, mito_counts / libraries, NA_real_)
  primary_eligible <- samples$nuclei >= as.integer(config$thresholds$primary_min_nuclei)
  sensitivity_eligible <- samples$nuclei >= as.integer(config$thresholds$sensitivity_min_nuclei)
  profile_rows[[length(profile_rows) + 1L]] <- data.frame(
    resolution = "direct_broad",
    context_id = shard$context_id,
    scientific_label = shard$scientific_label,
    broad_network = shard$broad_network,
    sample_order = samples$sample_order,
    pseudobulk_id = samples$pseudobulk_id,
    donor_id = samples$donor_id,
    nuclei = samples$nuclei,
    library_size = libraries,
    detected_features = detected,
    mtdna_umi_fraction = mito_fraction,
    primary_profile_eligible = primary_eligible,
    sensitivity_profile_eligible = sensitivity_eligible,
    diagnosis = samples$diagnosis,
    sex = samples$sex,
    apoe_group = samples$apoe_group,
    signature_group = samples$signature_group,
    age_death_scaled = samples$age_death_scaled,
    pmi_scaled = samples$pmi_scaled,
    study = samples$study,
    counts_path = shard$counts_path,
    samples_path = shard$samples_path,
    stringsAsFactors = FALSE
  )
  broad_summary_rows[[length(broad_summary_rows) + 1L]] <- data.frame(
    broad_network = shard$context_id,
    structural_profiles = nrow(samples),
    primary_eligible_profiles = sum(primary_eligible),
    sensitivity_eligible_profiles = sum(sensitivity_eligible),
    total_nuclei = sum(samples$nuclei),
    total_umis = sum(libraries),
    median_library_size_eligible = median(libraries[primary_eligible]),
    stringsAsFactors = FALSE
  )
  broad_total <- broad_total + sum(libraries)
  rm(counts_table, counts, samples)
  gc(verbose = FALSE)
}

profiles <- data.table::rbindlist(profile_rows, use.names = TRUE)
fine_summary <- data.table::rbindlist(fine_summary_rows)
broad_summary <- data.table::rbindlist(broad_summary_rows)
reconciliation <- data.table::rbindlist(reconciliation_rows)
eligibility <- profiles[, .(
  structural_profiles = .N,
  primary_eligible_profiles = sum(primary_profile_eligible),
  sensitivity_eligible_profiles = sum(sensitivity_profile_eligible)
), by = .(resolution, context_id, scientific_label, broad_network)]
library_qc <- profiles[, .(
  resolution, context_id, scientific_label, broad_network, pseudobulk_id,
  donor_id, nuclei, library_size, detected_features, mtdna_umi_fraction,
  primary_profile_eligible, sensitivity_profile_eligible
)]
model_profiles <- profiles[profiles$primary_profile_eligible, ]
model_covariates_complete <- all(is.finite(model_profiles$age_death_scaled)) &&
  all(is.finite(model_profiles$pmi_scaled)) &&
  all(nzchar(model_profiles$study)) &&
  all(model_profiles$library_size > 0)
expected_selected <- as.numeric(config$expected_identity$selected_umis)
checks <- data.frame(
  check = c(
    "fine_shards_reloaded", "broad_shards_reloaded", "feature_sample_order",
    "stable_donor_clinical_joins", "fine_total_recheck", "broad_total_recheck",
    "fine_direct_broad_reconciliation", "model_profiles_valid",
    "all_structural_fine_profiles_retained", "all_structural_broad_profiles_retained"
  ),
  passed = c(
    nrow(fine_manifest) == 129L, nrow(broad_manifest) == 7L, all_shards_valid,
    all_clinical_joins_valid, fine_total == expected_selected,
    broad_total == expected_selected, all(reconciliation$exact_equal),
    model_covariates_complete,
    sum(profiles$resolution == "fine_supertype") == 78L * 129L,
    sum(profiles$resolution == "direct_broad") == 78L * 7L
  ),
  observed = c(
    nrow(fine_manifest), nrow(broad_manifest), all_shards_valid,
    all_clinical_joins_valid, fine_total, broad_total,
    sum(reconciliation$mismatched_gene_donor_cells), model_covariates_complete,
    sum(profiles$resolution == "fine_supertype"),
    sum(profiles$resolution == "direct_broad")
  ),
  expected = c(129, 7, TRUE, TRUE, expected_selected, expected_selected, 0, TRUE, 78 * 129, 78 * 7),
  details = "",
  stringsAsFactors = FALSE
)

paths <- list(
  profiles = file.path(output_dir, "profile_manifest.tsv.gz"),
  eligibility = file.path(output_dir, "profile_eligibility.tsv"),
  library = file.path(output_dir, "library_qc.tsv.gz"),
  fine_summary = file.path(output_dir, "supertype_qc_summary.tsv"),
  broad_summary = file.path(output_dir, "broad_qc_summary.tsv"),
  conservation = file.path(output_dir, "count_conservation_recheck.tsv"),
  reconciliation = file.path(output_dir, "fine_broad_reconciliation_recheck.tsv"),
  checks = file.path(output_dir, "pseudobulk_qc_checks.tsv"),
  artifacts = file.path(output_dir, "artifacts.tsv"),
  status = file.path(output_dir, "status.tsv")
)
atomic_fwrite(profiles, paths$profiles)
atomic_fwrite(eligibility, paths$eligibility)
atomic_fwrite(library_qc, paths$library)
atomic_fwrite(fine_summary, paths$fine_summary)
atomic_fwrite(broad_summary, paths$broad_summary)
atomic_fwrite(data.frame(
  quantity = c("fine_pseudobulk_umi_total", "direct_broad_pseudobulk_umi_total"),
  value = c(fine_total, broad_total),
  expected = c(expected_selected, expected_selected)
), paths$conservation)
atomic_fwrite(reconciliation, paths$reconciliation)
atomic_fwrite(checks, paths$checks)
write_artifacts(unlist(paths[c("profiles", "eligibility", "library", "fine_summary", "broad_summary", "conservation", "reconciliation", "checks")]), paths$artifacts, project_root)

failed <- checks$check[!checks$passed]
state <- if (length(failed)) "failed" else "validated_complete"
status <- data.frame(
  schema_version = "seaad_fine_phase_status_v2",
  phase = "VH06",
  validation_status = state,
  failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  fine_shards = nrow(fine_manifest),
  broad_shards = nrow(broad_manifest),
  structural_fine_profiles = sum(profiles$resolution == "fine_supertype"),
  primary_eligible_fine_profiles = sum(profiles$resolution == "fine_supertype" & profiles$primary_profile_eligible),
  fine_pseudobulk_umi_total = fine_total,
  direct_broad_umi_total = broad_total,
  config_sha256 = sha256_file(config_path),
  vh05_status_sha256 = sha256_file(file.path(output_root, "05_pseudobulk/status.tsv")),
  stringsAsFactors = FALSE
)
atomic_fwrite(status, paths$status)
cat("VH06 status: ", state, "; fine profiles=", status$structural_fine_profiles, "
", sep = "")
if (length(failed)) quit(status = 2L)
