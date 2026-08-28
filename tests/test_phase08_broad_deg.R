#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)
phase08_require_packages(include_model = TRUE)

assert <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

mapping <- data.frame(
  schema_version = "phase08_broad_cell_mapping_v1",
  expected_rds_id = "fixture",
  fine_cell_type = c("Fine A", "Fine B", "Excluded"),
  broad_cell_type = c("Broad", "Broad", "ExcludedBroad"),
  include = c(TRUE, TRUE, FALSE),
  exclusion_reason = c("", "", "fixture_exclusion"),
  stringsAsFactors = FALSE
)
counts <- Matrix::Matrix(
  matrix(c(
    10, 20, 30, 7, 11,
    1, 2, 3, 5, 13,
    0, 4, 6, 2, 17
  ), nrow = 3L, byrow = TRUE),
  sparse = TRUE,
  dimnames = list(
    c("gene_up", "gene_down", "gene_null"),
    c("d1_a", "d1_b", "d1_excluded", "d2_a", "d2_b")
  )
)
samples <- data.frame(
  pseudobulk_id = colnames(counts),
  projid = c("d1", "d1", "d1", "d2", "d2"),
  cell_type_high_resolution = c("Fine A", "Fine B", "Excluded", "Fine A", "Fine B"),
  diagnosis = c("AD", "AD", "AD", "NCI", "NCI"),
  sex = "Female", apoe_group = "e2",
  age_death_scaled = c(0.1, 0.1, 0.1, -0.1, -0.1),
  pmi_scaled = c(0.2, 0.2, 0.2, -0.2, -0.2),
  nuclei = c(2L, 3L, 100L, 4L, 5L),
  total_umi_count = as.numeric(Matrix::colSums(counts)),
  total_mt_count = c(1, 2, 20, 1, 2),
  total_mitocarta_count = c(2, 3, 25, 2, 4),
  robust_flagged_nuclei = c(0L, 1L, 10L, 0L, 0L),
  stringsAsFactors = FALSE
)
bundle <- list(
  schema_version = "pseudobulk_counts_v1", rds_id = "fixture",
  counts = counts, samples = samples
)
analysis <- list(minimum_nuclei_primary = 5L, minimum_nuclei_sensitivity = 10L)
shard <- phase08_aggregate_source_bundle(bundle, mapping, "Broad", analysis)
assert(identical(dim(shard$counts), c(3L, 2L)), "Fixture broad aggregation has wrong dimensions")
assert(identical(as.numeric(shard$counts[, 1L]), c(30, 3, 4)),
       "Fine A/B counts were not summed for donor d1")
assert(identical(as.numeric(shard$counts[, 2L]), c(18, 18, 19)),
       "Fine A/B counts were not summed for donor d2")
assert(!any(as.numeric(shard$counts) == 30 + 30), "Excluded fine type leaked into broad counts")
assert(all(shard$samples$primary_eligible), "Eligibility was not recomputed after broad aggregation")
assert(identical(shard$excluded_fine_types, "Excluded"), "Explicit exclusion was not recorded")

second <- shard
second$rds_id <- "fixture2"
second$samples$source_rds_ids <- "fixture2"
second$counts[] <- second$counts[] + 1
second$samples$total_umi_count <- as.numeric(Matrix::colSums(second$counts))
combined <- phase08_combine_shards(
  list(fixture = shard, fixture2 = second), "Broad", analysis
)$Broad
assert(ncol(combined$counts) == 2L, "Cross-RDS merge duplicated donors")
assert(identical(
  as.numeric(combined$counts[, 1L]),
  as.numeric(shard$counts[, 1L] + second$counts[, 1L])
), "Cross-RDS merge did not sum matching donors")

groups <- data.frame(
  group_id = c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"),
  sex = rep(c("Female", "Male"), each = 3L),
  apoe_group = rep(c("e2", "e33", "e4"), 2L),
  stringsAsFactors = FALSE
)
manifest_samples <- do.call(rbind, lapply(seq_len(nrow(groups)), function(i) {
  data.frame(
    projid = paste0("d", i, "_", c("ad", "nci")),
    broad_cell_type = "Broad",
    diagnosis = c("AD", "NCI"), sex = groups$sex[[i]],
    apoe_group = groups$apoe_group[[i]], nuclei = c(20L, 20L),
    primary_eligible = TRUE, stringsAsFactors = FALSE
  )
}))
mock_context <- list(
  broad_types = "Broad",
  config = list(analysis = list(
    numerator = "AD", denominator = "NCI",
    groups = lapply(seq_len(nrow(groups)), function(i) as.list(groups[i, ])),
    minimum_donors_per_arm = 1L, confirmatory_donors_per_arm = 2L
  ))
)
manifest <- phase08_build_contrast_manifest(manifest_samples, mock_context)
assert(nrow(manifest) == 6L, "One broad cell must yield six structural contrasts")
assert(!anyDuplicated(manifest$contrast_id), "Contrast fixture IDs are not unique")
assert(all(manifest$modeling_status == "estimable"), "Supported fixture contrasts were not estimable")

design_columns <- c(
  "AD__Female__e2", "NCI__Female__e2", "age_death_scaled", "pmi_scaled"
)
contrast <- phase08_contrast_vector(manifest[1L, , drop = FALSE], design_columns)
assert(contrast[["AD__Female__e2"]] == 1, "AD contrast coefficient is not +1")
assert(contrast[["NCI__Female__e2"]] == -1, "NCI contrast coefficient is not -1")
assert(sum(abs(contrast)) == 2, "Contrast has unexpected nonzero coefficients")

threshold_config <- yaml::read_yaml(file.path(root, "config/phase08_broad_deg.yml"))
threshold_fixture <- data.frame(
  fdr_bh_within_contrast = c(0.05, 0.049, 0.10, 0.20, 0.201),
  logFC = c(log2(1.3) + 0.01, log2(1.3), log2(1.2), -0.01, -1),
  stringsAsFactors = FALSE
)
flagged <- phase08_threshold_flags(threshold_fixture, threshold_config)
assert(!flagged$strict_deg[[1L]], "Strict q boundary must use < 0.05")
assert(!flagged$strict_deg[[2L]], "Strict fold-change boundary must use > 1.3-fold")
assert(flagged$relaxed_deg[[3L]], "Relaxed equality boundaries must be included")
assert(flagged$exploratory_deg[[4L]], "Exploratory q=0.20 boundary must be included")
assert(!flagged$exploratory_deg[[5L]], "Exploratory q>0.20 must be excluded")
assert(flagged$direction[[4L]] == "AD_down", "Negative logFC did not map to AD_down")

cli <- phase08_parse_cli(
  c("--config", "x.yml", "--profile", "minerva_production", "--resume"),
  allow = c("--resume")
)
assert(identical(cli$config, "x.yml"), "CLI config parsing failed")
assert(identical(cli$profile, "minerva_production"), "CLI profile parsing failed")
assert(isTRUE(cli$resume), "CLI resume parsing failed")

trailing <- commandArgs(trailingOnly = TRUE)
if (length(trailing)) {
  if (length(trailing) != 2L || trailing[[1L]] != "--validate-output") {
    stop("Usage: Rscript tests/test_phase08_broad_deg.R [--validate-output DIR]", call. = FALSE)
  }
  output <- trailing[[2L]]
  status <- read.delim(file.path(output, "broad_deg_status.tsv"))
  manifest_out <- read.delim(file.path(output, "00_inputs", "broad_deg_contrast_manifest.tsv"))
  checks <- read.delim(file.path(output, "broad_deg_checks.tsv"))
  sensitivity <- read.delim(file.path(
    output, "04_sensitivity", "broad_deg_sensitivity_stage_status.tsv"
  ))
  results <- data.table::fread(file.path(output, "broad_deg_results.tsv.gz"), data.table = FALSE)
  assert(identical(status$validation_status, "validated_complete"),
         "Validated output status is not validated_complete")
  assert(nrow(manifest_out) == 6L, "Local pilot output must have six result sets")
  assert(all(checks$passed), "Local pilot output has failed checks")
  assert(identical(sensitivity$validation_status, "validated_complete"),
         "Local composition sensitivity is not validated_complete")
  assert(sensitivity$completed_contrasts == 4L,
         "Local composition sensitivity should complete four supported contrasts")
  assert(setequal(unique(results$direction), c("AD_up", "AD_down")),
         "Local pilot full results do not contain both directions")
}

cat("Phase 08 broad DEG tests passed\n")
