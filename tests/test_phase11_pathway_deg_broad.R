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

for (package in c("data.table", "yaml", "digest", "readxl", "fgsea")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}
library(data.table)

root <- normalizePath(getwd(), mustWork = TRUE)
source(
  file.path(root, "scripts/lib/phase11_deg_pathway_common.R"),
  local = FALSE
)
source(
  file.path(root, "scripts/11_run_broad_deg_pathway_analysis.R"),
  local = FALSE
)
args <- parse_test_cli(commandArgs(trailingOnly = TRUE))
config <- yaml::read_yaml(
  file.path(root, "config/phase11_pathway_deg_broad.yml")
)

toy <- data.table(
  N = c(20L, 10L, 10L, 10L),
  n = c(5L, 2L, 2L, 2L),
  M = c(4L, 3L, 3L, 3L),
  k = c(2L, 0L, 1L, 2L),
  expected = c(3856 / 15504, 1, 24 / 45, 3 / 45)
)
toy[, observed := phase11_ora_probability(k, M, N, n)]
assert(
  max(abs(toy$observed - toy$expected)) < 1e-12,
  "Frozen hypergeometric toy cases failed"
)

assert(
  phase11_program_testability(
    "mitocarta_broad_46", FALSE, 0L, 0L, 0L, 0
  ) == "contrast_not_estimable",
  "Non-estimable ORA query status was not retained"
)
assert(
  phase11_program_testability(
    "mitocarta_broad_46", TRUE, 2L, 100L, 10L, 1
  ) == "query_below_minimum",
  "Small ORA query status was not retained"
)
assert(
  phase11_program_testability(
    "mitocarta_broad_46", TRUE, 3L, 100L, 4L, 1
  ) == "below_minimum_background_members",
  "Small ORA pathway status was not retained"
)
assert(
  phase11_program_testability(
    "legacy_four", TRUE, 3L, 100L, 0L, 0
  ) == "tested",
  "Legacy ORA compatibility rule changed"
)

bh_fixture <- data.table(
  contrast_id = rep(c("c1", "c2"), each = 3L),
  deg_tier = "strict",
  query_mode = "AD_any_mito",
  pathway_collection = "c",
  test_status = "tested",
  p_value = c(0.001, 0.02, 0.7, 0.03, 0.2, 0.8)
)
bh_fixture <- phase11_apply_fdr(
  bh_fixture,
  local_columns = c(
    "contrast_id", "deg_tier", "query_mode", "pathway_collection"
  ),
  global_columns = c("deg_tier", "query_mode", "pathway_collection")
)
assert(
  isTRUE(all.equal(
    bh_fixture[contrast_id == "c1", local_fdr_bh],
    c(0.003, 0.03, 0.7)
  )),
  "Local BH family calculation failed"
)
assert(
  bh_fixture[, unique(global_fdr_family_size)] == 6L,
  "Global BH family size is incorrect"
)

mitocarta_path <- file.path(root, config$inputs$mitocarta_source)
parsed <- phase11_parse_mitocarta_source(mitocarta_path)
normalized <- fread(
  file.path(
    root, config$inputs$phase11_similarity_root,
    "pathway_membership_long.tsv.gz"
  )
)[
  pathway_collection == config$references$mitocarta$normalized_collection
]
assert(
  nrow(parsed$metadata) ==
    as.integer(config$expected$complete_mitocarta_pathways),
  "MitoCarta pathway count changed"
)
assert(
  nrow(parsed$membership) ==
    as.integer(config$expected$mitocarta_memberships),
  "MitoCarta membership count changed"
)
assert(
  setequal(
    parsed$membership[
      , paste(pathway_id, symbol_hgnc_current, sep = "\r")
    ],
    normalized[
      , paste(pathway_id, symbol_hgnc_current, sep = "\r")
    ]
  ),
  "Shared MitoCarta parser differs from the validated Phase 11 normalization"
)

legacy <- fread(file.path(root, config$inputs$legacy_module_membership))
programs <- phase11_build_program_collections(legacy, parsed, config)
collection_counts <- programs$metadata[, .N, by = pathway_collection]
assert(
  collection_counts[
    pathway_collection == "legacy_four", N
  ] == as.integer(config$expected$legacy_modules),
  "Legacy program count changed"
)
assert(
  collection_counts[
    pathway_collection == "mitocarta_broad_46", N
  ] == as.integer(config$expected$broad_mitocarta_pathways),
  "Broad MitoCarta program count changed"
)
assert(
  collection_counts[
    pathway_collection == "mitocarta_complete_149", N
  ] == as.integer(config$expected$complete_mitocarta_pathways),
  "Complete MitoCarta program count changed"
)

toy_symbols <- sprintf("G%03d", seq_len(80L))
toy_stats <- seq(4, -4, length.out = length(toy_symbols))
toy_rank_manifest <- data.table(
  rank_order = 1L,
  rank_id = "toy_rank",
  contrast_id = "toy_contrast",
  broad_cell_type = "Toy",
  sex = "Female",
  apoe_group = "e33",
  structural_status = "validated_complete",
  structurally_available = TRUE
)
toy_ranked_genes <- data.table(
  rank_id = "toy_rank",
  symbol_hgnc_current = toy_symbols,
  rank_score = toy_stats
)
toy_program_manifest <- data.table(
  pathway_collection = "mitocarta_complete_149",
  collection_order = 3L,
  collection_role = "supplemental_complete",
  pathway_id = c("P_POS", "P_NEG"),
  pathway_name = c("Positive toy pathway", "Negative toy pathway"),
  description = "toy",
  source_pathway_order = 1:2,
  hierarchy = c("Toy > Positive", "Toy > Negative"),
  hierarchy_depth = 2L,
  level_1 = "Toy",
  level_2 = c("Positive", "Negative"),
  level_3_or_deeper = NA_character_,
  parent_pathway = "Toy",
  pathway_scope = "broad_program",
  source_pathway_size = 10L
)
toy_program_membership <- rbindlist(list(
  data.table(
    pathway_collection = "mitocarta_complete_149",
    pathway_id = "P_POS",
    symbol_hgnc_current = toy_symbols[1:10]
  ),
  data.table(
    pathway_collection = "mitocarta_complete_149",
    pathway_id = "P_NEG",
    symbol_hgnc_current = toy_symbols[71:80]
  )
))
toy_run <- function() {
  phase11_run_gsea_collection(
    toy_rank_manifest, toy_ranked_genes,
    toy_program_manifest, toy_program_membership,
    "mitocarta_complete_149", config,
    "toy_gsea_v1", "primary"
  )
}
toy_gsea_1 <- toy_run()
toy_gsea_2 <- toy_run()
comparison_columns <- c(
  "pathway_id", "enrichment_score", "normalized_enrichment_score",
  "p_value", "log2_error", "leading_edge_genes"
)
assert(
  identical(
    toy_gsea_1[, ..comparison_columns],
    toy_gsea_2[, ..comparison_columns]
  ),
  "Seeded one-worker fgsea result is not deterministic"
)
assert(
  toy_gsea_1[pathway_id == "P_POS", normalized_enrichment_score] > 0 &&
    toy_gsea_1[pathway_id == "P_NEG", normalized_enrichment_score] < 0,
  "Toy GSEA direction is incorrect"
)

comparison_ids <- paste0("P", seq_len(6L))
toy_broad_ora <- data.table(
  query_order = seq_len(6L),
  source_pathway_order = seq_len(6L),
  query_id = paste0("broad_", comparison_ids),
  broad_cell_type = "Astrocytes",
  sex = "Female",
  apoe_group = "e33",
  query_mode = "AD_any_mito",
  pathway_collection = "legacy_four",
  collection_order = 1L,
  pathway_id = comparison_ids,
  deg_tier = "strict",
  test_status = c(rep("tested", 4L), "not_testable", "tested"),
  local_fdr_significant = c(TRUE, TRUE, FALSE, FALSE, FALSE, FALSE)
)
toy_fine_ora <- data.table(
  analysis_profile = "primary_pre_network_fine_deg",
  broad_cell_type = "Astrocytes",
  sex = "Female",
  apoe_group = "e33",
  query_mode = "AD_any_mito",
  pathway_collection = "legacy_four",
  pathway_id = comparison_ids,
  fine_cell_type = paste0("Astro_", seq_len(6L)),
  test_status = c(rep("tested", 5L), "not_testable"),
  local_fdr_significant = c(TRUE, FALSE, TRUE, FALSE, TRUE, FALSE),
  local_fdr_bh = c(0.01, 0.5, 0.01, 0.5, 0.01, NA_real_),
  fold_enrichment = c(2, 1, 2, 1, 2, NA_real_),
  overlap_genes = c("A", "", "B", "", "C", "")
)
toy_resolution <- build_broad_vs_fine(
  toy_broad_ora, toy_fine_ora, "toy_resolution_v1"
)
assert(
  identical(
    toy_resolution$resolution_concordance,
    c(
      "concordant_support", "broad_only", "fine_only", "neither",
      "not_comparable", "not_comparable"
    )
  ),
  "Broad-versus-fine comparability classification failed"
)

resume_input_fixture <- tempfile("phase11_resume_input_")
writeLines("frozen input", resume_input_fixture)
resume_reference_fixture <- data.table(
  path = resume_input_fixture,
  sha256 = phase11_sha256_file(resume_input_fixture),
  bytes = as.numeric(file.info(resume_input_fixture)$size)
)
assert(
  broad_reference_files_match(resume_reference_fixture, root),
  "Frozen resume-input fixture should initially validate"
)
writeLines("changed input", resume_input_fixture)
assert(
  !broad_reference_files_match(resume_reference_fixture, root),
  "Changed upstream input was not rejected by resume validation"
)
unlink(resume_input_fixture)

if (!is.null(args$validate_output)) {
  output_root <- phase11_absolute_path(args$validate_output, root)
  required <- c(
    "broad_deg_pathway_status.tsv",
    "broad_deg_pathway_checks.tsv",
    "broad_deg_pathway_artifacts.tsv",
    "broad_deg_pathway_reference_manifest.tsv",
    "broad_deg_pathway_program_manifest.tsv",
    "broad_deg_pathway_contrast_manifest.tsv",
    "broad_deg_pathway_rank_manifest.tsv",
    "broad_deg_pathway_ranked_genes.tsv.gz",
    "broad_deg_pathway_gsea.tsv.gz",
    "broad_deg_pathway_significant_gsea.tsv.gz",
    "broad_deg_pathway_background_manifest.tsv",
    "broad_deg_pathway_background_genes.tsv.gz",
    "broad_deg_pathway_ora_query_manifest.tsv",
    "broad_deg_pathway_ora_query_genes.tsv.gz",
    "broad_deg_pathway_ora.tsv.gz",
    "broad_deg_pathway_significant_ora.tsv.gz",
    "broad_deg_pathway_composition_rank_manifest.tsv",
    "broad_deg_pathway_composition_ranked_genes.tsv.gz",
    "broad_deg_pathway_composition_gsea.tsv.gz",
    "broad_deg_pathway_composition_concordance.tsv",
    "broad_deg_pathway_broad_cell_summary.tsv",
    "broad_deg_pathway_sex_apoe_summary.tsv",
    "broad_deg_pathway_broad_vs_fine_concordance.tsv.gz",
    "broad_deg_pathway_redundancy_map.tsv.gz",
    "README.md"
  )
  assert(
    all(file.exists(file.path(output_root, required))),
    "Validated broad pathway output bundle is incomplete"
  )
  status <- fread(file.path(output_root, "broad_deg_pathway_status.tsv"))
  checks <- fread(file.path(output_root, "broad_deg_pathway_checks.tsv"))
  artifacts <- fread(file.path(output_root, "broad_deg_pathway_artifacts.tsv"))
  references <- fread(
    file.path(output_root, "broad_deg_pathway_reference_manifest.tsv")
  )
  production_programs <- fread(
    file.path(output_root, "broad_deg_pathway_program_manifest.tsv")
  )
  contrasts <- fread(
    file.path(output_root, "broad_deg_pathway_contrast_manifest.tsv")
  )
  ranks <- fread(file.path(output_root, "broad_deg_pathway_rank_manifest.tsv"))
  ranked_genes <- fread(
    file.path(output_root, "broad_deg_pathway_ranked_genes.tsv.gz"),
    showProgress = FALSE
  )
  backgrounds <- fread(
    file.path(output_root, "broad_deg_pathway_background_manifest.tsv")
  )
  background_genes <- fread(
    file.path(output_root, "broad_deg_pathway_background_genes.tsv.gz"),
    showProgress = FALSE
  )
  queries <- fread(
    file.path(output_root, "broad_deg_pathway_ora_query_manifest.tsv")
  )
  query_genes <- fread(
    file.path(output_root, "broad_deg_pathway_ora_query_genes.tsv.gz"),
    showProgress = FALSE
  )
  gsea <- fread(
    file.path(output_root, "broad_deg_pathway_gsea.tsv.gz"),
    showProgress = FALSE
  )
  significant_gsea <- fread(
    file.path(output_root, "broad_deg_pathway_significant_gsea.tsv.gz"),
    showProgress = FALSE
  )
  ora <- fread(
    file.path(output_root, "broad_deg_pathway_ora.tsv.gz"),
    showProgress = FALSE
  )
  significant_ora <- fread(
    file.path(output_root, "broad_deg_pathway_significant_ora.tsv.gz"),
    showProgress = FALSE
  )
  composition_ranks <- fread(
    file.path(
      output_root, "broad_deg_pathway_composition_rank_manifest.tsv"
    )
  )
  composition_gsea <- fread(
    file.path(output_root, "broad_deg_pathway_composition_gsea.tsv.gz"),
    showProgress = FALSE
  )
  composition_ranked_genes <- fread(
    file.path(
      output_root, "broad_deg_pathway_composition_ranked_genes.tsv.gz"
    ),
    showProgress = FALSE
  )
  composition_concordance <- fread(
    file.path(output_root, "broad_deg_pathway_composition_concordance.tsv")
  )
  broad_vs_fine <- fread(
    file.path(
      output_root, "broad_deg_pathway_broad_vs_fine_concordance.tsv.gz"
    ),
    showProgress = FALSE
  )
  broad_cell_summary <- fread(
    file.path(output_root, "broad_deg_pathway_broad_cell_summary.tsv")
  )
  sex_apoe_summary <- fread(
    file.path(output_root, "broad_deg_pathway_sex_apoe_summary.tsv")
  )
  redundancy <- fread(
    file.path(output_root, "broad_deg_pathway_redundancy_map.tsv.gz"),
    showProgress = FALSE
  )

  assert(
    phase11_schema_ok(status, config$schemas$status) &&
      status$validation_status[[1L]] == "validated_complete",
    "Production status is not validated_complete"
  )
  assert(
    phase11_schema_ok(checks, config$schemas$checks) && all(checks$passed),
    "Production validation checks did not all pass"
  )
  assert(
    phase11_schema_ok(artifacts, config$schemas$artifacts),
    "Production artifact schema is invalid"
  )
  expected_schemas <- broad_output_schema_map(config)
  expected_artifacts <- names(expected_schemas)
  ordered_artifacts <- artifacts[match(expected_artifacts, artifact)]
  expected_paths <- phase11_relative_path(
    file.path(output_root, expected_artifacts), root
  )
  expected_records <- broad_expected_artifact_records(config, status)
  assert(
    nrow(artifacts) == as.integer(config$expected$output_artifacts) &&
      !anyDuplicated(artifacts$artifact) &&
      !anyDuplicated(artifacts$path) &&
      setequal(artifacts$artifact, expected_artifacts) &&
      identical(ordered_artifacts$path, unname(expected_paths)) &&
      identical(
        ordered_artifacts$output_schema, unname(expected_schemas)
      ) &&
      identical(
        as.integer(ordered_artifacts$records),
        unname(expected_records)
      ) &&
      all(ordered_artifacts$validation_status == "validated_complete"),
    "Production artifact manifest is incomplete or not path-bound"
  )
  assert(
    identical(
      status$artifacts_manifest_sha256[[1L]],
      phase11_sha256_file(
        file.path(output_root, "broad_deg_pathway_artifacts.tsv")
      )
    ),
    "Status does not bind the output artifact manifest"
  )
  assert(
    all(vapply(
      seq_len(nrow(artifacts)),
      function(i) phase11_artifact_valid(artifacts[i], root),
      logical(1)
    )),
    "A production artifact failed hash or byte validation"
  )
  assert(
    phase11_schema_ok(references, config$schemas$reference_manifest) &&
      nrow(references) == as.integer(config$expected$reference_inputs) &&
      !anyDuplicated(references$input_id) &&
      !anyDuplicated(references$path) &&
      all(references$validation_status == "validated_input"),
    "Production reference manifest is incomplete or duplicated"
  )
  current_input_hashes <- vapply(
    phase11_absolute_path(references$path, root),
    phase11_sha256_file,
    character(1)
  )
  assert(
    identical(unname(current_input_hashes), references$sha256) &&
      identical(
        as.numeric(file.info(
          phase11_absolute_path(references$path, root)
        )$size),
        as.numeric(references$bytes)
      ),
    "A production input differs from the frozen reference manifest"
  )
  assert(
    uniqueN(contrasts$broad_cell_type) ==
      as.integer(config$expected$broad_cell_types) &&
      uniqueN(contrasts[, .(sex, apoe_group)]) ==
        as.integer(config$expected$sex_apoe_strata),
    "Broad-cell or sex/APOE structural count is incorrect"
  )
  assert(
    nrow(production_programs) ==
      as.integer(config$expected$program_definitions),
    "Program-definition count is incorrect"
  )
  assert(
    nrow(ranks) == as.integer(config$expected$primary_rank_definitions) &&
      sum(ranks$structurally_available) ==
        as.integer(config$expected$completed_contrasts),
    "Primary rank manifest counts are incorrect"
  )
  assert(
    !anyDuplicated(contrasts$contrast_id) &&
      !anyDuplicated(ranks$rank_id) &&
      !anyDuplicated(ranked_genes[, .(rank_id, symbol_hgnc_current)]) &&
      !anyDuplicated(backgrounds$background_id) &&
      !anyDuplicated(
        background_genes[, .(background_id, symbol_hgnc_current)]
      ),
    "A primary contrast, rank, or background key is duplicated"
  )
  assert(
    max(abs(
      ranked_genes$rank_score -
        sign(ranked_genes$logFC) * sqrt(pmax(ranked_genes$F, 0))
    )) < 1e-14 &&
      all(is.finite(ranked_genes$rank_score)) &&
      sum(ranked_genes$F < 0) ==
        as.integer(config$expected$primary_tiny_negative_f_clamped) &&
      all(ranked_genes$F >= -as.numeric(
        config$analysis$negative_f_tolerance
      )),
    "Primary GSEA rank calculation is invalid"
  )
  assert(
    nrow(queries) == as.integer(config$expected$ora_query_definitions),
    "ORA query manifest count is incorrect"
  )
  assert(
    !anyDuplicated(queries$query_id) &&
      !anyDuplicated(query_genes[, .(query_id, symbol_hgnc_current)]),
    "An ORA query key is duplicated"
  )
  assert(
    identical(
      query_genes$direction,
      ifelse(query_genes$logFC > 0, "AD_up", "AD_down")
    ) &&
      identical(
        as.logical(query_genes$in_upregulated_query),
        query_genes$direction == "AD_up"
      ) &&
      identical(
        as.logical(query_genes$in_downregulated_query),
        query_genes$direction == "AD_down"
      ) &&
      all(query_genes[
        query_mode == "AD_up_mito", direction == "AD_up"
      ]) &&
      all(query_genes[
        query_mode == "AD_down_mito", direction == "AD_down"
      ]),
    "ORA query directions do not reconcile with logFC"
  )
  query_background_keys <- paste(
    query_genes$contrast_id, query_genes$symbol_hgnc_current, sep = "\r"
  )
  background_keys <- paste(
    background_genes$background_id,
    background_genes$symbol_hgnc_current,
    sep = "\r"
  )
  assert(
    all(query_background_keys %chin% background_keys),
    "An ORA query gene is absent from its exact background"
  )
  tier_counts <- query_genes[
    query_mode == "AD_any_mito", .N, by = deg_tier
  ]
  assert(
    tier_counts[deg_tier == "strict", N] ==
      as.integer(config$expected$strict_core_mito_degs) &&
      tier_counts[deg_tier == "relaxed", N] ==
        as.integer(config$expected$relaxed_core_mito_degs) &&
      tier_counts[deg_tier == "exploratory", N] ==
        as.integer(config$expected$exploratory_core_mito_degs),
    "Core-mito DEG tier totals are incorrect"
  )
  assert(
    nrow(gsea) == as.integer(config$expected$primary_gsea_rows) &&
      all(gsea[
        test_status == "tested",
        is.finite(p_value) & p_value >= 0 & p_value <= 1
      ]),
    "Primary GSEA grid is invalid"
  )
  assert(
    !anyDuplicated(gsea[, .(
      rank_id, pathway_collection, pathway_id
    )]) &&
      all(gsea[
        test_status == "tested" & normalized_enrichment_score > 0,
        gsea_direction == "AD_up"
      ]) &&
      all(gsea[
        test_status == "tested" & normalized_enrichment_score < 0,
        gsea_direction == "AD_down"
      ]),
    "GSEA keys or direction labels are invalid"
  )
  verify_fdr <- function(
      x, local_columns, global_columns, tolerance = 1e-14) {
    tested <- copy(x[test_status == "tested"])
    tested[, expected_local := p.adjust(p_value, method = "BH"),
      by = local_columns
    ]
    tested[, expected_global := p.adjust(p_value, method = "BH"),
      by = global_columns
    ]
    max(abs(tested$expected_local - tested$local_fdr_bh)) <= tolerance &&
      max(abs(tested$expected_global - tested$global_fdr_bh)) <= tolerance
  }
  flags_match_fdr <- function(x) {
    threshold <- as.numeric(config$fdr$threshold)
    identical(
      as.logical(x$local_fdr_significant),
      x$test_status == "tested" &
        !is.na(x$local_fdr_bh) & x$local_fdr_bh < threshold
    ) &&
      identical(
        as.logical(x$global_fdr_significant),
        x$test_status == "tested" &
          !is.na(x$global_fdr_bh) & x$global_fdr_bh < threshold
      )
  }
  tables_equal <- function(x, y, tolerance = 1e-13) {
    identical(names(x), names(y)) &&
      nrow(x) == nrow(y) &&
      all(vapply(names(x), function(column) {
        left <- x[[column]]
        right <- y[[column]]
        if (all(is.na(left)) && all(is.na(right))) return(TRUE)
        isTRUE(all.equal(
          left, right, check.attributes = FALSE, tolerance = tolerance
        ))
      }, logical(1)))
  }
  assert(
    verify_fdr(
      gsea,
      c("contrast_id", "pathway_collection"),
      c("pathway_collection")
    ),
    "Primary GSEA FDR values do not reproduce"
  )
  assert(
    flags_match_fdr(gsea),
    "Primary GSEA FDR significance flags are inconsistent"
  )
  expected_significant_gsea <- copy(
    gsea[local_fdr_significant %in% TRUE]
  )
  expected_significant_gsea[
    , schema_version := config$schemas$significant_gsea
  ]
  assert(
    tables_equal(significant_gsea, expected_significant_gsea),
    "Significant-only GSEA file is not the exact authoritative subset"
  )
  leading_edges <- gsea[
    test_status == "tested" & nzchar(leading_edge_genes),
    .(
      symbol_hgnc_current = unlist(
        strsplit(leading_edge_genes, ",", fixed = TRUE)
      )
    ),
    by = .(rank_id, pathway_collection, pathway_id)
  ]
  leading_rank_keys <- paste(
    leading_edges$rank_id,
    leading_edges$symbol_hgnc_current,
    sep = "\r"
  )
  ranked_gene_keys <- paste(
    ranked_genes$rank_id, ranked_genes$symbol_hgnc_current, sep = "\r"
  )
  leading_pathway_keys <- paste(
    leading_edges$pathway_collection,
    leading_edges$pathway_id,
    leading_edges$symbol_hgnc_current,
    sep = "\r"
  )
  membership_keys <- paste(
    programs$membership$pathway_collection,
    programs$membership$pathway_id,
    programs$membership$symbol_hgnc_current,
    sep = "\r"
  )
  assert(
    all(leading_rank_keys %chin% ranked_gene_keys) &&
      all(leading_pathway_keys %chin% membership_keys),
    "A GSEA leading-edge gene is absent from its rank or pathway"
  )
  assert(
    nrow(ora) == as.integer(config$expected$primary_ora_rows) &&
      all(ora[
        test_status == "tested",
        is.finite(p_value) & p_value >= 0 & p_value <= 1
      ]),
    "ORA grid is invalid"
  )
  assert(
    !anyDuplicated(ora[, .(
      query_id, pathway_collection, pathway_id
    )]) &&
      all(ora[
        test_status == "tested",
        query_in_pathway >= 0L &
          query_not_in_pathway >= 0L &
          background_outside_query_in_pathway >= 0L &
          background_outside_query_not_in_pathway >= 0L &
          query_in_pathway + query_not_in_pathway +
            background_outside_query_in_pathway +
            background_outside_query_not_in_pathway == background_size &
          overlap_count <= query_size &
          overlap_count <= background_pathway_size &
          query_size <= background_size
      ]),
    "ORA keys or contingency tables are invalid"
  )
  tested_sample <- ora[test_status == "tested"][seq_len(min(.N, 1000L))]
  recomputed <- with(
    tested_sample,
    phase11_ora_probability(
      overlap_count, background_pathway_size, background_size, query_size
    )
  )
  assert(
    max(abs(recomputed - tested_sample$p_value)) < 1e-15,
    "Production ORA P values do not reproduce"
  )
  tested_all <- ora[test_status == "tested"]
  recomputed_all <- with(
    tested_all,
    phase11_ora_probability(
      overlap_count, background_pathway_size, background_size, query_size
    )
  )
  assert(
    max(abs(recomputed_all - tested_all$p_value)) < 1e-15 &&
      all(tested_all[overlap_count == 0L, p_value == 1]),
    "Complete production ORA P values or zero-overlap results are invalid"
  )
  assert(
    verify_fdr(
      ora,
      c(
        "contrast_id", "deg_tier", "query_mode", "pathway_collection"
      ),
      c("deg_tier", "query_mode", "pathway_collection")
    ),
    "ORA FDR values do not reproduce"
  )
  assert(
    flags_match_fdr(ora),
    "ORA FDR significance flags are inconsistent"
  )
  expected_significant_ora <- copy(
    ora[local_fdr_significant %in% TRUE]
  )
  expected_significant_ora[
    , schema_version := config$schemas$significant_ora
  ]
  tier_roles <- vapply(
    config$analysis$deg_tiers,
    function(x) as.character(x$role),
    character(1)
  )
  expected_significant_ora[
    , evidence_role := unname(tier_roles[deg_tier])
  ]
  assert(
    tables_equal(significant_ora, expected_significant_ora),
    "Significant-only ORA file is not the exact authoritative subset"
  )
  fisher_sample <- tested_all[
    overlap_count > 0L
  ][seq_len(min(.N, 50L))]
  fisher_p <- vapply(seq_len(nrow(fisher_sample)), function(i) {
    row <- fisher_sample[i]
    stats::fisher.test(
      matrix(c(
        row$overlap_count,
        row$query_size - row$overlap_count,
        row$background_pathway_size - row$overlap_count,
        row$background_size - row$background_pathway_size -
          row$query_size + row$overlap_count
      ), nrow = 2L),
      alternative = "greater"
    )$p.value
  }, numeric(1))
  assert(
    max(abs(fisher_p - fisher_sample$p_value)) < 1e-12,
    "Audited ORA rows do not match one-sided Fisher tests"
  )
  assert(
    nrow(composition_ranks) ==
      as.integer(config$expected$composition_rank_definitions) &&
      sum(composition_ranks$structurally_available) ==
        as.integer(config$expected$composition_completed_contrasts),
    "Composition rank manifest counts are incorrect"
  )
  assert(
    !anyDuplicated(composition_ranks$rank_id) &&
      !anyDuplicated(
        composition_ranked_genes[, .(rank_id, symbol_hgnc_current)]
      ) &&
      !anyDuplicated(composition_gsea[, .(
        rank_id, pathway_collection, pathway_id
      )]) &&
      !anyDuplicated(composition_concordance[, .(
        contrast_id, pathway_collection, pathway_id
      )]),
    "A composition-sensitivity key is duplicated"
  )
  assert(
    nrow(composition_gsea) ==
      as.integer(config$expected$composition_gsea_rows),
    "Composition GSEA grid count is incorrect"
  )
  assert(
    verify_fdr(
      composition_gsea,
      c("contrast_id", "pathway_collection"),
      c("pathway_collection")
    ),
    "Composition GSEA FDR values do not reproduce"
  )
  assert(
    flags_match_fdr(composition_gsea),
    "Composition GSEA FDR significance flags are inconsistent"
  )
  assert(
    all(composition_gsea[
      structural_status == "not_applicable_single_fine_type",
      testability_reason == "not_applicable_single_fine_type"
    ]),
    "Composition not-applicable records were not preserved"
  )
  expected_broad_cell_summary <- build_summary(
    gsea, composition_gsea, ora,
    "broad_cell_type", config$schemas$broad_cell_summary
  )
  expected_sex_apoe_summary <- build_summary(
    gsea, composition_gsea, ora,
    "sex_apoe", config$schemas$sex_apoe_summary
  )
  assert(
    nrow(broad_cell_summary) ==
      as.integer(config$expected$broad_cell_summary_rows) &&
      tables_equal(broad_cell_summary, expected_broad_cell_summary),
    "Broad-cell summary does not reproduce from authoritative grids"
  )
  assert(
    nrow(sex_apoe_summary) ==
      as.integer(config$expected$sex_apoe_summary_rows) &&
      tables_equal(sex_apoe_summary, expected_sex_apoe_summary),
    "Sex/APOE summary does not reproduce from authoritative grids"
  )
  sensitivity_summary <- fread(file.path(
    root, config$inputs$broad_deg_root,
    "04_sensitivity/broad_deg_sensitivity_summary.tsv"
  ))
  expected_composition_concordance <- build_composition_concordance(
    gsea, composition_gsea, sensitivity_summary,
    config$schemas$composition_concordance
  )
  assert(
    tables_equal(
      composition_concordance, expected_composition_concordance
    ),
    "Composition concordance does not reproduce from authoritative inputs"
  )
  fine_ora <- fread(
    file.path(
      root, config$inputs$phase11_fine_root,
      "fine_deg_pathway_ora.tsv.gz"
    ),
    showProgress = FALSE
  )
  expected_broad_vs_fine <- build_broad_vs_fine(
    ora, fine_ora, config$schemas$broad_vs_fine
  )
  assert(
    tables_equal(broad_vs_fine, expected_broad_vs_fine),
    "Broad-versus-fine output does not reproduce from authoritative inputs"
  )
  assert(
    nrow(broad_vs_fine) == as.integer(config$expected$broad_vs_fine_rows),
    "Broad-versus-fine comparison count is incorrect"
  )
  assert(
    setequal(
      unique(broad_vs_fine$broad_cell_type),
      unlist(config$fine_comparison$shared_broad_cell_types, use.names = FALSE)
    ) &&
      !anyDuplicated(broad_vs_fine[, .(
        query_id, pathway_collection, pathway_id
      )]),
    "Broad-versus-fine comparison scope or keys are invalid"
  )
  allowed_resolution_categories <- c(
    "concordant_support", "broad_only", "fine_only", "neither",
    "not_comparable"
  )
  assert(
    all(broad_vs_fine$resolution_concordance %in%
      allowed_resolution_categories) &&
      all(
        (broad_vs_fine$resolution_concordance == "not_comparable") ==
          (!broad_vs_fine$broad_resolution_testable |
            !broad_vs_fine$fine_resolution_testable)
      ),
    "Broad-versus-fine comparability categories are invalid"
  )
  assert(
    nrow(redundancy) == as.integer(config$expected$redundancy_pairs),
    "Redundancy-map count is incorrect"
  )
}

cat("Phase 11 broad-DEG pathway tests passed.\n")
