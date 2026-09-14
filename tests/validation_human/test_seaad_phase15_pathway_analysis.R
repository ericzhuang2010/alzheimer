#!/usr/bin/env Rscript

source(
  file.path(getwd(), "scripts/validation_human/15_seaad_pathway_common.R"),
  local = globalenv()
)

library(data.table)

assert_true <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

flags_match <- function(x, threshold) {
  expected_local <- ifelse(
    is.finite(x$local_fdr_bh), x$local_fdr_bh < threshold, FALSE
  )
  expected_global <- ifelse(
    is.finite(x$global_fdr_bh), x$global_fdr_bh < threshold, FALSE
  )
  identical(
    as.vector(as.logical(expected_local)),
    as.vector(as.logical(x$local_fdr_significant))
  ) && identical(
    as.vector(as.logical(expected_global)),
    as.vector(as.logical(x$global_fdr_significant))
  )
}

validate_output_bundle <- function(root, prefix, config, project_root) {
  status <- fread(file.path(root, paste0(prefix, "_status.tsv")))
  artifacts <- fread(file.path(root, paste0(prefix, "_artifacts.tsv")))
  assert_true(nrow(status) == 1L, paste(prefix, "status must have one row"))
  assert_true(
    status$validation_status[[1L]] == "validated_complete",
    paste(prefix, "is not validated_complete")
  )
  assert_true(
    status$artifacts_manifest_sha256[[1L]] ==
      phase11_sha256_file(
        file.path(root, paste0(prefix, "_artifacts.tsv"))
      ),
    paste(prefix, "artifact-manifest hash differs")
  )
  assert_true(
    phase11_schema_ok(artifacts, config$schemas$artifacts),
    paste(prefix, "artifact schema differs")
  )
  assert_true(
    !anyDuplicated(artifacts$artifact) && !anyDuplicated(artifacts$path),
    paste(prefix, "artifact keys are duplicated")
  )
  assert_true(
    all(vapply(seq_len(nrow(artifacts)), function(i) {
      phase11_artifact_valid(artifacts[i], project_root)
    }, logical(1))),
    paste(prefix, "artifact validation failed")
  )
  list(status = status, artifacts = artifacts)
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
fine_config <- yaml::read_yaml(
  "config/seaad_phase15_pathway_deg_fine.yml"
)
broad_config <- yaml::read_yaml(
  "config/seaad_phase15_pathway_deg_broad.yml"
)
fine_root <- file.path(
  project_root, "results/validation_human/15_pathway_deg_fine"
)
broad_root <- file.path(
  project_root, "results/validation_human/15_pathway_deg_broad"
)

fine_bundle <- validate_output_bundle(
  fine_root, "seaad_fine_deg_pathway", fine_config, project_root
)
fine_manifest <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_contrast_manifest.tsv")
)
fine_background <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_background_genes.tsv.gz")
)
fine_queries <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_query_manifest.tsv")
)
fine_query_genes <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_query_genes.tsv.gz")
)
fine_ora <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_ora.tsv.gz")
)
fine_programs <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_program_manifest.tsv")
)
fine_membership <- fread(
  file.path(fine_root, "seaad_fine_deg_pathway_program_membership.tsv.gz")
)
kda_ora <- fread(
  file.path(fine_root, "seaad_kda_effective_query_program_ora.tsv.gz")
)

assert_true(
  nrow(fine_manifest) == fine_config$expected$structural_contrasts,
  "Fine contrast count differs"
)
assert_true(
  sum(fine_manifest$structurally_available) ==
    fine_config$expected$completed_contrasts,
  "Fine completed contrast count differs"
)
assert_true(
  nrow(fine_background) == fine_config$expected$background_gene_rows,
  "Fine background row count differs"
)
assert_true(
  nrow(fine_queries) == fine_config$expected$query_definitions,
  "Fine query count differs"
)
assert_true(
  nrow(fine_ora) == fine_config$expected$primary_ora_rows,
  "Fine ORA row count differs"
)
assert_true(
  !anyDuplicated(
    fine_ora[, .(query_id, pathway_collection, pathway_id)]
  ),
  "Fine ORA keys are duplicated"
)
assert_true(
  seaad15_pvalues_reproduce(fine_ora),
  "Fine ORA p-values do not reproduce"
)
assert_true(
  flags_match(fine_ora, fine_config$fdr$threshold),
  "Fine ORA FDR flags differ"
)
assert_true(
  data.table::uniqueN(kda_ora$kda_run_id) ==
    fine_config$expected$kda_effective_queries &&
    nrow(kda_ora) == fine_config$expected$kda_ora_rows,
  "Fine KDA companion dimensions differ"
)
assert_true(
  seaad15_pvalues_reproduce(kda_ora),
  "KDA companion ORA p-values do not reproduce"
)
assert_true(
  nrow(fine_programs) == fine_config$expected$pathway_definitions,
  "Fine program count differs"
)
assert_true(
  all(unique(fine_membership[, .(
    pathway_collection, pathway_id
  )])[
    unique(fine_programs[, .(pathway_collection, pathway_id)]),
    on = .(pathway_collection, pathway_id),
    nomatch = 0L
  ][, .N] == uniqueN(fine_membership[, .(
    pathway_collection, pathway_id
  )])),
  "Fine membership contains a program not in the manifest"
)
fine_query_keys <- unique(
  fine_query_genes[, .(background_id, symbol_hgnc_current)]
)
fine_background_keys <- unique(
  fine_background[, .(background_id, symbol_hgnc_current)]
)
assert_true(
  nrow(fine_query_keys[
    !fine_background_keys,
    on = .(background_id, symbol_hgnc_current)
  ]) == 0L,
  "A fine query gene is outside its background"
)

broad_bundle <- validate_output_bundle(
  broad_root, "seaad_broad_deg_pathway", broad_config, project_root
)
broad_manifest <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_contrast_manifest.tsv")
)
ranks <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_ranked_genes.tsv.gz")
)
rank_manifest <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_rank_manifest.tsv")
)
gsea <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_gsea.tsv.gz")
)
broad_ora <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_ora.tsv.gz")
)
broad_vs_fine <- fread(
  file.path(
    broad_root,
    "seaad_broad_deg_pathway_broad_vs_fine_concordance.tsv.gz"
  )
)
broad_programs <- fread(
  file.path(broad_root, "seaad_broad_deg_pathway_program_manifest.tsv")
)

assert_true(
  nrow(broad_manifest) == broad_config$expected$structural_contrasts,
  "Broad contrast count differs"
)
assert_true(
  sum(broad_manifest$analysis_status == "validated_complete") ==
    broad_config$expected$completed_contrasts,
  "Broad completed contrast count differs"
)
assert_true(
  nrow(ranks) == broad_config$expected$primary_rank_rows,
  "Broad rank row count differs"
)
assert_true(
  all(abs(
    ranks$rank_score -
      sign(ranks$logFC) * sqrt(pmax(ranks$F, 0))
  ) < 1e-14),
  "Broad rank statistic differs"
)
assert_true(
  !anyDuplicated(ranks[, .(rank_id, symbol_hgnc_current)]),
  "Broad rank symbols are duplicated"
)
assert_true(
  sum(rank_manifest$structurally_available) ==
    broad_config$expected$completed_contrasts,
  "Broad rank-manifest availability differs"
)
assert_true(
  nrow(gsea) == broad_config$expected$primary_gsea_rows,
  "Broad GSEA row count differs"
)
assert_true(
  !anyDuplicated(gsea[, .(
    rank_id, pathway_collection, pathway_id
  )]),
  "Broad GSEA keys are duplicated"
)
assert_true(
  seaad15_gsea_fdr_reproduces(gsea),
  "Broad GSEA FDR values do not reproduce"
)
assert_true(
  flags_match(gsea, broad_config$fdr$threshold),
  "Broad GSEA FDR flags differ"
)
assert_true(
  nrow(broad_ora) == broad_config$expected$primary_ora_rows,
  "Broad ORA row count differs"
)
assert_true(
  seaad15_pvalues_reproduce(broad_ora),
  "Broad ORA p-values do not reproduce"
)
assert_true(
  flags_match(broad_ora, broad_config$fdr$threshold),
  "Broad ORA FDR flags differ"
)
assert_true(
  nrow(broad_vs_fine) == broad_config$expected$broad_vs_fine_rows,
  "Broad-versus-fine row count differs"
)
assert_true(
  all(broad_vs_fine$resolution_concordance %chin% c(
    "not_comparable", "concordant_support", "broad_only",
    "fine_only", "neither"
  )),
  "Broad-versus-fine categories differ"
)
comparison_columns <- setdiff(names(broad_programs), "schema_version")
assert_true(
  isTRUE(all.equal(
    broad_programs[, ..comparison_columns],
    fine_programs[, ..comparison_columns],
    check.attributes = FALSE,
    tolerance = 0
  )),
  "Fine and broad program catalogs differ"
)

cat("SEA-AD VH15 pathway production tests passed\n")
