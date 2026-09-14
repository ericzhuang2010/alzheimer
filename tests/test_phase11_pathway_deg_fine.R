#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_test_cli <- function(args) {
  out <- list(validate_output = NULL)
  if (!length(args)) return(out)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] != "--validate-output" || i == length(args)) {
      stop("Unknown test option or missing value: ", args[[i]], call. = FALSE)
    }
    out$validate_output <- args[[i + 1L]]
    i <- i + 2L
  }
  out
}

assert <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

root <- normalizePath(getwd(), mustWork = TRUE)
source(
  file.path(root, "scripts/11_run_fine_deg_pathway_analysis.R"),
  local = FALSE
)
for (package in c("data.table", "yaml", "digest")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}
library(data.table)
args <- parse_test_cli(commandArgs(trailingOnly = TRUE))
config <- yaml::read_yaml(
  file.path(root, "config/phase11_pathway_deg_fine.yml")
)

toy <- data.table(
  N = c(20L, 10L, 10L, 10L),
  n = c(5L, 2L, 2L, 2L),
  M = c(4L, 3L, 3L, 3L),
  k = c(2L, 0L, 1L, 2L),
  expected = c(3856 / 15504, 1, 24 / 45, 3 / 45)
)
toy[, observed := ora_probability(k, M, N, n)]
assert(
  max(abs(toy$observed - toy$expected)) < 1e-12,
  "Frozen hypergeometric toy cases failed"
)

assert(
  program_testability(
    "mitocarta_broad_46", FALSE, 0L, 0L, 0L, 0
  ) == "contrast_not_estimable",
  "Non-estimable query status was not retained"
)
assert(
  program_testability(
    "mitocarta_broad_46", TRUE, 0L, 100L, 10L, 1
  ) == "empty_query",
  "Empty query status was not retained"
)
assert(
  program_testability(
    "mitocarta_broad_46", TRUE, 2L, 100L, 10L, 1
  ) == "query_below_minimum",
  "Small query status was not retained"
)
assert(
  program_testability(
    "mitocarta_broad_46", TRUE, 3L, 100L, 4L, 1
  ) == "below_minimum_background_members",
  "Small pathway status was not retained"
)
assert(
  program_testability(
    "mitocarta_broad_46", TRUE, 3L, 100L, 10L, 0.29
  ) == "below_minimum_reference_coverage",
  "Low-reference-coverage status was not retained"
)
assert(
  program_testability(
    "legacy_four", TRUE, 3L, 100L, 0L, 0
  ) == "tested",
  "Legacy compatibility profile applied an extra pathway-size filter"
)

bh_fixture <- data.table(
  query_id = rep(c("q1", "q2"), each = 3L),
  pathway_collection = "c",
  query_mode = "AD_any_mito",
  test_status = "tested",
  p_value = c(0.001, 0.02, 0.7, 0.03, 0.2, 0.8)
)
bh_fixture <- apply_bh_families(
  bh_fixture, global_columns = c("pathway_collection", "query_mode")
)
assert(
  isTRUE(all.equal(
    bh_fixture[query_id == "q1", local_fdr_bh],
    c(0.003, 0.03, 0.7)
  )),
  "Local BH family calculation failed"
)
assert(
  bh_fixture[, unique(global_fdr_family_size)] == 6L,
  "Global BH family size is incorrect"
)

summary_fixture <- data.table(
  contrast_id = c("c1", "c2"),
  fine_cell_type = c("f1", "f2"),
  signature_group = "F_e33",
  sex = "Female",
  apoe_group = "e33",
  query_mode = "AD_up_mito",
  pathway_collection = "mitocarta_broad_46",
  collection_role = "primary_expanded",
  pathway_id = "Complex I",
  pathway_name = "Complex I",
  hierarchy_depth = 2L,
  level_1 = "OXPHOS",
  level_2 = "Complex I",
  structurally_available = TRUE,
  test_status = "tested",
  local_fdr_significant = c(TRUE, TRUE),
  global_fdr_significant = c(FALSE, FALSE),
  fold_enrichment = c(2, 3),
  overlap_genes = c("A,B", "B,C")
)
summary <- build_recurrence_summary(
  summary_fixture,
  c(
    "signature_group", "sex", "apoe_group", "query_mode",
    "pathway_collection", "collection_role", "pathway_id",
    "pathway_name", "hierarchy_depth", "level_1", "level_2"
  ),
  "test_schema"
)
assert(
  summary$overlap_gene_union_count[[1L]] == 3L &&
    summary$recurrent_overlap_gene_count[[1L]] == 1L &&
    summary$recurrent_overlap_genes[[1L]] == "B",
  "Recurrence-gene summary failed"
)

if (!is.null(args$validate_output)) {
  output_root <- absolute_path(args$validate_output, root)
  required <- c(
    "fine_deg_pathway_status.tsv",
    "fine_deg_pathway_checks.tsv",
    "fine_deg_pathway_artifacts.tsv",
    "fine_deg_pathway_reference_manifest.tsv",
    "fine_deg_pathway_program_manifest.tsv",
    "fine_deg_pathway_contrast_manifest.tsv",
    "fine_deg_pathway_background_manifest.tsv",
    "fine_deg_pathway_background_genes.tsv.gz",
    "fine_deg_pathway_query_manifest.tsv",
    "fine_deg_pathway_query_genes.tsv.gz",
    "fine_deg_pathway_ora.tsv.gz",
    "fine_deg_pathway_significant_results.tsv.gz",
    "fine_deg_pathway_fine_cell_summary.tsv",
    "fine_deg_pathway_broad_cell_summary.tsv",
    "fine_deg_pathway_sex_apoe_summary.tsv",
    "fine_deg_pathway_redundancy_map.tsv.gz",
    "kda_effective_query_program_ora.tsv.gz",
    "legacy_four_module_reconciliation.tsv",
    "README.md"
  )
  assert(
    all(file.exists(file.path(output_root, required))),
    "Validated output bundle is incomplete"
  )
  status <- fread(file.path(output_root, "fine_deg_pathway_status.tsv"))
  checks <- fread(file.path(output_root, "fine_deg_pathway_checks.tsv"))
  artifacts <- fread(file.path(output_root, "fine_deg_pathway_artifacts.tsv"))
  programs <- fread(file.path(output_root, "fine_deg_pathway_program_manifest.tsv"))
  contrasts <- fread(file.path(output_root, "fine_deg_pathway_contrast_manifest.tsv"))
  queries <- fread(file.path(output_root, "fine_deg_pathway_query_manifest.tsv"))
  reconciliation <- fread(
    file.path(output_root, "legacy_four_module_reconciliation.tsv")
  )
  kda_ora <- fread(
    file.path(output_root, "kda_effective_query_program_ora.tsv.gz"),
    select = "query_mode", showProgress = FALSE
  )

  assert(
    schema_ok(status, config$schemas$status) &&
      status$validation_status[[1L]] == "validated_complete",
    "Output status is not validated_complete"
  )
  assert(all(checks$passed %in% TRUE), "A production output check failed")
  assert(all(reconciliation$passed %in% TRUE), "Legacy reconciliation failed")
  assert(
    identical(unique(kda_ora$query_mode), "AD_both_mito"),
    "KDA companion did not preserve its Phase 20 source query-mode label"
  )
  assert(
    nrow(contrasts) == as.integer(config$expected$planned_contrasts) &&
      sum(contrasts$structurally_available) ==
        as.integer(config$expected$estimable_contrasts),
    "Production contrast counts are incorrect"
  )
  assert(
    nrow(queries) == as.integer(config$expected$planned_contrasts) * 3L,
    "Production query count is incorrect"
  )
  expected_program_counts <- c(
    legacy_four = 4L,
    mitocarta_broad_46 = 46L,
    mitocarta_complete_149 = 149L
  )
  observed_program_counts <- programs[, .N, by = pathway_collection]
  assert(
    identical(
      observed_program_counts[
        match(names(expected_program_counts), pathway_collection), N
      ],
      unname(expected_program_counts)
    ),
    "Production program counts are incorrect"
  )
  hashes_valid <- all(vapply(seq_len(nrow(artifacts)), function(i) {
    artifact_valid(artifacts[i], root)
  }, logical(1)))
  assert(hashes_valid, "A production artifact hash or byte count failed")
}

cat("Phase 11 fine-DEG pathway tests passed\n")
