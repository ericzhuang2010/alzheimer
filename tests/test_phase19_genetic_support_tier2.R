#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

assert <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/19_run_genetic_support_tier2.R"), local = FALSE)

required <- c("coloc", "data.table", "susieR", "yaml")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop("Missing required packages: ", paste(missing, collapse = ", "), call. = FALSE)
}

cfg <- yaml::read_yaml(file.path(root, "config/phase19_genetic_support_tier2.yml"))
paths <- lapply(
  cfg$inputs,
  function(x) if (is.character(x) && length(x) == 1L) abs_path(root, x) else x
)
paths$tier1_root <- abs_path(root, cfg$inputs$tier1_root)

invisible(validate_tier1(paths))
candidate <- read_tsv(paths$tier1_candidate_manifest)
loci <- read_tsv(paths$tier1_candidate_loci)
routes <- build_route_manifest(candidate, loci, unlist(cfg$analysis$qtl_types))

assert(nrow(candidate) == 47L, "Tier 1 handoff no longer has 47 candidate contexts")
assert(data.table::uniqueN(candidate$gene) == 25L, "Tier 1 handoff no longer has 25 genes")
assert(nrow(routes) == 54L, "Tier 2 route manifest must have 54 eQTL/sQTL routes")
assert(data.table::uniqueN(routes$gene) == 19L, "Tier 2 route manifest must have 19 nuclear genes")
assert(sum(coerce_bool(candidate$is_mtdna_gene)) == 20L, "Expected 20 mtDNA contexts")
assert(!anyDuplicated(routes[, .(candidate_id, qtl_type)]), "Tier 2 route keys are duplicated")

gwas <- data.table::data.table(
  variant_id = paste0("v", 1:5),
  beta = rep(0.1, 5),
  standard_error = rep(0.05, 5),
  effect_allele = c("A", "A", "A", "A", "A"),
  other_allele = c("G", "G", "C", "C", "C")
)
qtl <- data.table::data.table(
  variant_id = paste0("v", 1:5),
  beta = 1:5,
  standard_error = rep(0.1, 5),
  effect_allele = c("A", "G", "T", "G", "A"),
  other_allele = c("G", "A", "G", "T", "G")
)
harmonized <- harmonize_summary_stats(gwas, qtl)
expected_operations <- c(
  v1 = "match", v2 = "swap", v3 = "complement",
  v4 = "swap_complement", v5 = "mismatch"
)
observed_operations <- setNames(harmonized$operation, harmonized$variant_id)
assert(
  identical(observed_operations[names(expected_operations)], expected_operations),
  "Allele harmonization operations changed"
)
observed_beta <- setNames(harmonized$beta_qtl, harmonized$variant_id)
assert(observed_beta[["v2"]] == -2 && observed_beta[["v4"]] == -4,
       "Swapped QTL effect sizes were not flipped")
assert(!harmonized[variant_id == "v5", included], "Allele mismatch was not excluded")

ld <- matrix(c(1, 0.2, 0.2, 1), nrow = 2)
dimnames(ld) <- list(c("v1", "v2"), c("v1", "v2"))
ld_check <- validate_ld_matrix(ld, c("v2", "v1"))
assert(identical(rownames(ld_check$matrix), c("v2", "v1")), "LD variant order changed")
bad_ld <- ld
bad_ld[1, 2] <- 0.3
assert(inherits(try(validate_ld_matrix(bad_ld, c("v1", "v2")), silent = TRUE), "try-error"),
       "Asymmetric LD fixture was not rejected")

smoke <- synthetic_coloc_smoke()
assert(
  smoke$signal_pairs >= 4L && smoke$shared_pairs >= 2L && smoke$distinct_pairs >= 2L,
  "Multi-signal coloc fixture did not recover shared and distinct signals"
)

fixture <- file.path(root, "tests/fixtures/phase19_tier2/precomputed_apoe_h0_h4.tsv")
parsed <- parse_precomputed_file(fixture, routes, cfg$context_aliases)
assert(nrow(parsed) == 1L, "Known APOE H0-H4 fixture did not map to one route")
assert(parsed$candidate_id[[1L]] == "GS002" && parsed$context_match[[1L]] == "exact",
       "Known APOE fixture mapped to the wrong candidate or context")
assert(parsed$evidence_class[[1L]] == "supported", "Known H4 fixture was not supported")

output <- tempfile("phase19_tier2_test_")
args <- list(
  config = "config/phase19_genetic_support_tier2.yml",
  execution_config = "config/phase19_tier2_local_execution.yml",
  scientific_config = NULL,
  task_mode = "genetic_support_tier2",
  output_root = output,
  pilot = TRUE,
  force = FALSE
)
invisible(run_analysis(args))
assert(
  identical(sort(list.files(output)), sort(OUTPUT_FILES)),
  "Pilot output does not match the exact 23-file contract"
)

summary <- read_tsv(file.path(output, "tier2_evidence_summary.tsv"))
assessability <- read_tsv(file.path(output, "tier2_assessability.tsv"))
status <- read_tsv(file.path(output, "tier2_status.tsv"))
checks <- read_tsv(file.path(output, "tier2_checks.tsv"))
artifacts <- read_tsv(file.path(output, "tier2_artifacts.tsv"))

assert(nrow(summary) == 47L && data.table::uniqueN(summary$gene) == 25L,
       "Pilot cumulative summary scope changed")
assert(nrow(assessability) == 54L && all(nzchar(assessability$status)),
       "Every Tier 2 base route must have a terminal status")
assert(sum(summary$tier2_regional_coloc_status == "not_applicable_mtdna") == 20L,
       "mtDNA contexts were not retained as not applicable")
assert(status$technical_status[[1L]] %in% c(
         "validated_complete_tier2", "validated_source_acquisition_incomplete"),
       "Pilot returned an unknown open-alternative technical status")
assert(!coerce_bool(status$full_phase19_complete[[1L]]),
       "Tier 2 regional work incorrectly claimed full Phase 19 completion")
if (status$technical_status[[1L]] == "validated_complete_tier2") {
  assert(sum(checks$status == "fail" & checks$severity == "blocking") == 0L,
         "Verified open-alternative pilot has a blocking failure")
  assert(checks[check_id == "alternative_required_files_verified", status] == "pass",
         "Frozen public source files did not pass verification")
  assert(checks[check_id == "candidate_qtl_finemapping_extract", status] == "pass",
         "Candidate QTL fine-mapping extract did not pass")
  assert(checks[check_id == "candidate_gwas_extract", status] == "pass",
         "Candidate-region GWAS extract did not pass")
  assert(status$scientific_status[[1L]] %in% c(
           "tier2_regional_coloc_complete",
           "tier2_open_alternative_complete_classical_coloc_not_assessable"),
         "Scientific status does not describe the open-data execution")
} else {
  assert(sum(checks$status == "fail" & checks$severity == "blocking") >= 1L,
         "Incomplete alternative acquisition was not exposed by a blocking check")
}
assert(nrow(artifacts) == length(OUTPUT_FILES) - 2L,
       "Artifact manifest row count changed")
for (i in seq_len(nrow(artifacts))) {
  assert(
    sha256_file(file.path(output, artifacts$path[[i]])) == artifacts$sha256[[i]],
    paste("Artifact hash mismatch:", artifacts$path[[i]])
  )
}

invisible(validate_tier1(paths))
cat("Phase 19 Tier 2 open-source route, harmonization, LD, coloc, parser, and pilot tests passed\n")
