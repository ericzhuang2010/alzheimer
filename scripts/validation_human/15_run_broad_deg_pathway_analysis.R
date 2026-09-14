#!/usr/bin/env Rscript

source(
  file.path(getwd(), "scripts/validation_human/15_seaad_pathway_common.R"),
  local = globalenv()
)

rosmap_broad_helpers <- new.env(parent = globalenv())
sys.source(
  file.path(getwd(), "scripts/11_run_broad_deg_pathway_analysis.R"),
  envir = rosmap_broad_helpers
)

seaad15_validate_fine_pathway_bundle <- function(root, project_root) {
  status_path <- file.path(root, "seaad_fine_deg_pathway_status.tsv")
  artifacts_path <- file.path(root, "seaad_fine_deg_pathway_artifacts.tsv")
  required <- c(
    status_path,
    artifacts_path,
    file.path(root, "seaad_fine_deg_pathway_program_manifest.tsv"),
    file.path(root, "seaad_fine_deg_pathway_program_membership.tsv.gz"),
    file.path(root, "seaad_fine_deg_pathway_ora.tsv.gz")
  )
  phase11_must(
    all(file.exists(required)),
    "SEA-AD fine pathway authority is incomplete"
  )
  status <- seaad15_read(status_path)
  artifacts <- seaad15_read(artifacts_path)
  phase11_must(
    nrow(status) == 1L &&
      phase11_schema_ok(status, "seaad_fine_deg_pathway_status_v1") &&
      status$phase[[1L]] == "VH15F" &&
      status$validation_status[[1L]] == "validated_complete" &&
      status$artifacts_manifest_sha256[[1L]] ==
        phase11_sha256_file(artifacts_path),
    "SEA-AD fine pathway authority is not validated_complete"
  )
  seaad15_validate_artifact_rows(artifacts, project_root)
  list(
    status = status,
    artifacts = artifacts,
    paths = c(
      status = status_path,
      artifacts = artifacts_path,
      program_manifest = required[[3L]],
      program_membership = required[[4L]],
      ora = required[[5L]]
    )
  )
}

seaad15_load_broad_core <- function(
    completed_status, project_root, config) {
  rows <- lapply(seq_len(nrow(completed_status)), function(i) {
    authority <- completed_status[i]
    path <- phase11_absolute_path(authority$result_path, project_root)
    seaad15_assert_file_hash(
      path, authority$result_sha256, "Broad DEG result"
    )
    x <- seaad15_read(
      path,
      select = c(
        "feature_index", "source_symbol", "current_symbol_for_kda",
        "is_core_mito_phase18", "mapping_status", "logFC", "F",
        "PValue", "FDR", "test_status", "effect_direction"
      )
    )
    x <- x[
      phase11_is_true(is_core_mito_phase18) &
        test_status == "tested" &
        phase11_nonempty(current_symbol_for_kda)
    ]
    phase11_must(
      all(is.finite(x$logFC)) &&
        all(is.finite(x$F)) &&
        all(x$F >= -as.numeric(config$analysis$negative_f_tolerance)) &&
        all(is.finite(x$PValue)) &&
        all(is.finite(x$FDR)),
      paste("Broad mitochondrial rank contains invalid statistics:",
            authority$contrast_id)
    )
    phase11_must(
      !anyDuplicated(x$current_symbol_for_kda),
      paste("Broad mitochondrial symbols are duplicated:",
            authority$contrast_id)
    )
    expected_direction <- data.table::fifelse(
      x$logFC > 0, "Dementia_up",
      data.table::fifelse(x$logFC < 0, "Dementia_down", "zero")
    )
    phase11_must(
      identical(x$effect_direction, expected_direction),
      paste("Broad effect-direction labels differ:", authority$contrast_id)
    )
    x[, .(
      contrast_id = as.character(authority$contrast_id),
      broad_cell_type = as.character(authority$broad_network),
      group_id = as.character(authority$signature_group),
      sex = as.character(authority$sex),
      apoe_group = as.character(authority$apoe_group),
      gene = source_symbol,
      symbol_hgnc_current = current_symbol_for_kda,
      mapping_status,
      feature_index,
      logFC,
      F,
      p_value = PValue,
      fdr_bh_within_contrast = FDR,
      strict_deg =
        FDR < 0.05 & abs(logFC) > log2(1.3),
      relaxed_deg =
        FDR <= 0.10 & abs(logFC) >= log2(1.2),
      exploratory_deg = FDR <= 0.20,
      direction = data.table::fifelse(logFC > 0, "AD_up", "AD_down")
    )]
  })
  result <- data.table::rbindlist(rows, fill = TRUE)
  data.table::setorder(result, contrast_id, symbol_hgnc_current)
  result
}

seaad15_validate_broad_filter_universes <- function(
    status, core, project_root) {
  authorities <- unique(status[, .(
    broad_cell_type = broad_network, filter_path, filter_sha256
  )], by = "broad_cell_type")
  comparisons <- lapply(seq_len(nrow(authorities)), function(i) {
    authority <- authorities[i]
    path <- phase11_absolute_path(authority$filter_path, project_root)
    seaad15_assert_file_hash(
      path, authority$filter_sha256, "Broad DEG filter"
    )
    x <- seaad15_read(
      path,
      select = c(
        "current_symbol_for_kda", "is_core_mito_phase18", "test_status"
      )
    )
    expected <- sort(unique(x[
      phase11_is_true(is_core_mito_phase18) &
        test_status == "tested" &
        phase11_nonempty(current_symbol_for_kda),
      current_symbol_for_kda
    ]))
    observed <- sort(unique(core[
      broad_cell_type == authority$broad_cell_type,
      symbol_hgnc_current
    ]))
    data.table::data.table(
      broad_cell_type = authority$broad_cell_type,
      filter_symbols = length(expected),
      result_symbols = length(observed),
      exact_match = setequal(expected, observed)
    )
  })
  data.table::rbindlist(comparisons)
}

seaad15_relabel_queries <- function(queries) {
  mode_map <- c(
    AD_any_mito = "Dementia_any_mito",
    AD_up_mito = "Dementia_up_mito",
    AD_down_mito = "Dementia_down_mito"
  )
  queries$manifest[, query_mode := unname(mode_map[query_mode])]
  queries$manifest[, query_id := sub(
    "::AD_", "::Dementia_", query_id, fixed = TRUE
  )]
  queries$genes[, query_mode := unname(mode_map[query_mode])]
  queries$genes[, query_id := sub(
    "::AD_", "::Dementia_", query_id, fixed = TRUE
  )]
  queries$genes[, direction := data.table::fifelse(
    direction == "AD_up", "Dementia_up", "Dementia_down"
  )]
  queries
}

seaad15_broad_fdr_flags_match <- function(x, threshold) {
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

seaad15_mark_missing_fgsea_results <- function(x) {
  missing <- x$test_status == "tested" & !is.finite(x$p_value)
  x[missing, `:=`(
    test_status = "not_testable",
    testability_reason = "fgsea_no_finite_result",
    gsea_direction = "not_testable",
    leading_edge_confidence = "not_testable"
  )]
  x
}

run_seaad_broad_pathway <- function(
    cli = seaad15_parse_cli(commandArgs(trailingOnly = TRUE))) {
  library(data.table)
  started <- Sys.time()
  loaded <- seaad15_load_config(
    cli$config,
    "seaad_phase15_pathway_deg_broad_config_v1",
    "broad"
  )
  config <- loaded$config
  project_root <- loaded$project_root
  config_path <- loaded$config_path
  script_path <- file.path(
    project_root,
    "scripts/validation_human/15_run_broad_deg_pathway_analysis.R"
  )
  common_path <- file.path(
    project_root, "scripts/validation_human/15_seaad_pathway_common.R"
  )
  shared_path <- file.path(
    project_root, "scripts/lib/phase11_deg_pathway_common.R"
  )
  rosmap_helper_path <- file.path(
    project_root, "scripts/11_run_broad_deg_pathway_analysis.R"
  )
  code_paths <- c(
    script_path, common_path, shared_path, rosmap_helper_path
  )
  final_root <- phase11_absolute_path(
    config$output$directory, project_root
  )
  prefix <- "seaad_broad_deg_pathway"
  if (dir.exists(final_root)) {
    if (seaad15_valid_existing(
      final_root, prefix, config, config_path, code_paths, project_root
    )) {
      cat("SEA-AD broad pathway bundle is complete and hash-valid: ",
          final_root, "\n", sep = "")
      return(invisible(final_root))
    }
    stop(
      "Existing SEA-AD broad pathway output is not a valid resumable bundle",
      call. = FALSE
    )
  }

  input <- function(name) {
    phase11_absolute_path(config$inputs[[name]], project_root)
  }
  deg_root <- input("deg_root")
  deg_release <- seaad15_validate_release(
    deg_root, project_root, "seaad_deg_broad_status_v1", "VH08B", "broad"
  )
  fine_release <- seaad15_validate_fine_pathway_bundle(
    input("fine_pathway_root"), project_root
  )
  paths <- c(
    deg_status = deg_release$status_path,
    deg_artifacts = deg_release$artifacts_path,
    contrast_status = input("contrast_status"),
    result_index = input("result_index"),
    fine_status = fine_release$paths[["status"]],
    fine_artifacts = fine_release$paths[["artifacts"]],
    fine_program_manifest = fine_release$paths[["program_manifest"]],
    fine_program_membership = fine_release$paths[["program_membership"]],
    fine_ora = fine_release$paths[["ora"]],
    legacy_module_membership = input("legacy_module_membership"),
    mitocarta_source = input("mitocarta_source"),
    scientific_script = script_path,
    seaad_pathway_common = common_path,
    shared_pathway_library = shared_path,
    rosmap_broad_helper = rosmap_helper_path,
    scientific_config = config_path
  )
  phase11_must(all(file.exists(paths)), "A required broad VH15 input is missing")
  references <- seaad15_make_reference_manifest(
    paths, config$schemas$reference_manifest, project_root
  )

  status <- seaad15_read(paths[["contrast_status"]])
  result_index <- seaad15_read(paths[["result_index"]])
  programs <- seaad15_build_programs(config, project_root)
  programs$membership[, schema_version :=
    config$schemas$program_membership]
  data.table::setcolorder(
    programs$membership,
    c("schema_version", setdiff(
      names(programs$membership), "schema_version"
    ))
  )
  fine_program <- seaad15_read(paths[["fine_program_manifest"]])
  fine_membership <- seaad15_read(paths[["fine_program_membership"]])
  program_columns <- setdiff(names(programs$metadata), "schema_version")
  membership_columns <- setdiff(
    names(programs$membership), "schema_version"
  )
  program_catalogs_match <- isTRUE(all.equal(
    programs$metadata[, ..program_columns],
    fine_program[, ..program_columns],
    check.attributes = FALSE,
    tolerance = 0
  )) && isTRUE(all.equal(
    programs$membership[, ..membership_columns],
    fine_membership[, ..membership_columns],
    check.attributes = FALSE,
    tolerance = 0
  ))
  phase11_must(
    program_catalogs_match,
    "Fine and broad SEA-AD pathway catalogs differ"
  )

  contrast_manifest <- status[, .(
    manifest_row = as.integer(contrast_slot),
    contrast_id,
    broad_cell_type = broad_network,
    group_id = signature_group,
    signature_group,
    sex,
    apoe_group,
    n_dementia_donors = as.integer(n_case_donors),
    n_no_dementia_donors = as.integer(n_reference_donors),
    source_support_status = support_status,
    source_eligibility_status = eligibility_status,
    source_terminal_status = terminal_status,
    source_terminal_reason = terminal_reason,
    result_path,
    result_sha256,
    filter_path,
    filter_sha256,
    analysis_status = data.table::fifelse(
      terminal_status == "completed",
      "validated_complete",
      "contrast_not_estimable"
    )
  )]
  contrast_manifest[, schema_version := config$schemas$contrast_manifest]
  data.table::setcolorder(
    contrast_manifest,
    c("schema_version", "manifest_row", setdiff(
      names(contrast_manifest), c("schema_version", "manifest_row")
    ))
  )
  data.table::setorder(contrast_manifest, manifest_row)

  core <- seaad15_load_broad_core(
    status[terminal_status == "completed"], project_root, config
  )
  filter_comparison <- seaad15_validate_broad_filter_universes(
    status, core, project_root
  )
  ranks <- rosmap_broad_helpers$build_rank_bundle(
    core,
    contrast_manifest,
    "primary",
    config$schemas$rank_manifest,
    config$schemas$ranked_genes,
    as.numeric(config$analysis$negative_f_tolerance),
    available_status = "validated_complete"
  )
  backgrounds <- rosmap_broad_helpers$build_background_bundle(
    core,
    contrast_manifest,
    config$schemas$background_manifest,
    config$schemas$background_genes
  )

  helper_config <- config
  names(helper_config$analysis$query_modes) <- c(
    "AD_any_mito", "AD_up_mito", "AD_down_mito"
  )
  queries <- rosmap_broad_helpers$build_ora_queries(
    core,
    contrast_manifest,
    helper_config,
    config$schemas$ora_query_manifest,
    config$schemas$ora_query_genes
  )
  queries <- seaad15_relabel_queries(queries)

  complete_gsea <- phase11_run_gsea_collection(
    ranks$manifest,
    ranks$genes,
    programs$metadata,
    programs$membership,
    "mitocarta_complete_149",
    config,
    config$schemas$gsea,
    "primary"
  )
  legacy_gsea <- phase11_run_gsea_collection(
    ranks$manifest,
    ranks$genes,
    programs$metadata,
    programs$membership,
    "legacy_four",
    config,
    config$schemas$gsea,
    "primary"
  )
  complete_gsea <- seaad15_mark_missing_fgsea_results(complete_gsea)
  legacy_gsea <- seaad15_mark_missing_fgsea_results(legacy_gsea)
  broad_gsea <- phase11_derive_broad_gsea(
    complete_gsea, programs$metadata, config$schemas$gsea
  )
  gsea <- phase11_finalize_gsea(
    data.table::rbindlist(
      list(legacy_gsea, broad_gsea, complete_gsea),
      use.names = TRUE,
      fill = TRUE
    ),
    config
  )
  gsea[, `:=`(
    cohort = "SEA-AD",
    analysis_profile = "primary_sex_apoe_broad_deg",
    gsea_direction = data.table::fcase(
      gsea_direction == "AD_up", "Dementia_up",
      gsea_direction == "AD_down", "Dementia_down",
      default = gsea_direction
    )
  )]
  data.table::setcolorder(
    gsea, c("schema_version", "cohort", "analysis_profile",
      setdiff(
        names(gsea), c("schema_version", "cohort", "analysis_profile")
      ))
  )
  significant_gsea <- data.table::copy(
    gsea[local_fdr_significant %in% TRUE]
  )
  significant_gsea[, schema_version := config$schemas$significant_gsea]

  ora <- phase11_run_ora(
    queries$manifest,
    queries$genes,
    backgrounds$genes,
    programs$metadata,
    programs$membership,
    config,
    config$schemas$ora
  )
  ora[, `:=`(
    cohort = "SEA-AD",
    analysis_profile = "thresholded_sex_apoe_broad_deg"
  )]
  data.table::setcolorder(
    ora, c("schema_version", "cohort", "analysis_profile",
      setdiff(
        names(ora), c("schema_version", "cohort", "analysis_profile")
      ))
  )
  significant_ora <- data.table::copy(
    ora[local_fdr_significant %in% TRUE]
  )
  significant_ora[, schema_version := config$schemas$significant_ora]

  fine_ora <- seaad15_read(paths[["fine_ora"]])
  phase11_must(
    phase11_schema_ok(fine_ora, "seaad_fine_deg_pathway_ora_v1"),
    "Unexpected SEA-AD fine ORA schema"
  )
  broad_vs_fine <- seaad15_broad_vs_fine(
    ora, fine_ora, config$schemas$broad_vs_fine
  )
  broad_summary <- seaad15_broad_summary(
    gsea,
    ora,
    c("broad_cell_type", "sex", "apoe_group"),
    config$schemas$broad_cell_summary
  )
  sex_summary <- seaad15_broad_summary(
    gsea,
    ora,
    c("sex", "apoe_group"),
    config$schemas$sex_apoe_summary
  )
  redundancy <- phase11_compute_redundancy_map(
    programs$metadata,
    programs$membership,
    config$schemas$redundancy_map,
    as.numeric(config$redundancy$representative_jaccard_threshold)
  )

  query_background_keys <- unique(backgrounds$genes[, .(
    background_id, symbol_hgnc_current
  )])
  query_keys <- unique(queries$genes[, .(
    background_id = contrast_id, symbol_hgnc_current
  )])
  query_outside_background <- query_keys[
    !query_background_keys,
    on = .(background_id, symbol_hgnc_current)
  ]
  threshold <- as.numeric(config$fdr$threshold)
  check_rows <- list(
    list(
      "broad_release_validated", TRUE, "validated_complete",
      "validated_complete", "All declared VH08B artifacts were hash-checked"
    ),
    list(
      "fine_pathway_release_validated", TRUE, "validated_complete",
      "validated_complete", "VH15F is the fine-resolution authority"
    ),
    list(
      "structural_contrast_count",
      nrow(contrast_manifest) ==
        as.integer(config$expected$structural_contrasts),
      nrow(contrast_manifest), config$expected$structural_contrasts, ""
    ),
    list(
      "completed_contrast_count",
      sum(contrast_manifest$analysis_status == "validated_complete") ==
        as.integer(config$expected$completed_contrasts),
      sum(contrast_manifest$analysis_status == "validated_complete"),
      config$expected$completed_contrasts, ""
    ),
    list(
      "nonestimable_contrast_count",
      sum(contrast_manifest$analysis_status == "contrast_not_estimable") ==
        as.integer(config$expected$nonestimable_contrasts),
      sum(contrast_manifest$analysis_status == "contrast_not_estimable"),
      config$expected$nonestimable_contrasts, ""
    ),
    list(
      "completed_result_index_count",
      nrow(result_index) == as.integer(config$expected$completed_contrasts),
      nrow(result_index), config$expected$completed_contrasts, ""
    ),
    list(
      "broad_filter_universes_match_results",
      all(filter_comparison$exact_match),
      sum(filter_comparison$exact_match),
      nrow(filter_comparison), ""
    ),
    list(
      "primary_rank_rows",
      nrow(ranks$genes) == as.integer(config$expected$primary_rank_rows),
      nrow(ranks$genes), config$expected$primary_rank_rows, ""
    ),
    list(
      "rank_statistic_exact",
      all(abs(
        ranks$genes$rank_score -
          sign(ranks$genes$logFC) *
            sqrt(pmax(ranks$genes$F, 0))
      ) < 1e-15),
      TRUE, TRUE, ""
    ),
    list(
      "background_gene_rows",
      nrow(backgrounds$genes) ==
        as.integer(config$expected$background_gene_rows),
      nrow(backgrounds$genes), config$expected$background_gene_rows, ""
    ),
    list(
      "query_definition_count",
      nrow(queries$manifest) ==
        as.integer(config$expected$query_definitions),
      nrow(queries$manifest), config$expected$query_definitions, ""
    ),
    list(
      "query_genes_within_background",
      nrow(query_outside_background) == 0L,
      nrow(query_outside_background), 0L, ""
    ),
    list(
      "program_catalogs_match_fine",
      program_catalogs_match, TRUE, TRUE, ""
    ),
    list(
      "primary_gsea_rows",
      nrow(gsea) == as.integer(config$expected$primary_gsea_rows),
      nrow(gsea), config$expected$primary_gsea_rows, ""
    ),
    list(
      "primary_gsea_keys_unique",
      !anyDuplicated(gsea[, .(
        rank_id, pathway_collection, pathway_id
      )]),
      anyDuplicated(gsea[, .(
        rank_id, pathway_collection, pathway_id
      )]),
      0L, ""
    ),
    list(
      "primary_gsea_fdr_reproduces",
      seaad15_gsea_fdr_reproduces(gsea), TRUE, TRUE, ""
    ),
    list(
      "primary_gsea_fdr_flags_match",
      seaad15_broad_fdr_flags_match(gsea, threshold), TRUE, TRUE, ""
    ),
    list(
      "primary_ora_rows",
      nrow(ora) == as.integer(config$expected$primary_ora_rows),
      nrow(ora), config$expected$primary_ora_rows, ""
    ),
    list(
      "primary_ora_keys_unique",
      !anyDuplicated(ora[, .(
        query_id, pathway_collection, pathway_id
      )]),
      anyDuplicated(ora[, .(
        query_id, pathway_collection, pathway_id
      )]),
      0L, ""
    ),
    list(
      "primary_ora_pvalues_reproduce",
      seaad15_pvalues_reproduce(ora), TRUE, TRUE, ""
    ),
    list(
      "primary_ora_fdr_flags_match",
      seaad15_broad_fdr_flags_match(ora, threshold), TRUE, TRUE, ""
    ),
    list(
      "broad_vs_fine_rows",
      nrow(broad_vs_fine) ==
        as.integer(config$expected$broad_vs_fine_rows),
      nrow(broad_vs_fine), config$expected$broad_vs_fine_rows, ""
    ),
    list(
      "broad_vs_fine_categories_valid",
      all(broad_vs_fine$resolution_concordance %chin% c(
        "not_comparable", "concordant_support", "broad_only",
        "fine_only", "neither"
      )),
      TRUE, TRUE, ""
    ),
    list(
      "upstream_references_hash_bound",
      seaad15_reference_files_match(references, project_root),
      TRUE, TRUE, ""
    ),
    list(
      "pooled_anchor_excluded",
      !any(grepl("__pooled__", contrast_manifest$contrast_id, fixed = TRUE)),
      TRUE, TRUE,
      "Primary broad analysis mirrors ROSMAP's 42 sex/APOE contrasts"
    )
  )
  checks <- seaad15_checks(check_rows, config$schemas$checks)
  failed <- checks[passed == FALSE, check]
  phase11_must(
    !length(failed),
    paste(
      "SEA-AD broad pathway checks failed:",
      paste(failed, collapse = ", ")
    )
  )

  readme <- c(
    "# SEA-AD broad-cell DEG pathway analysis",
    "",
    "This VH15B release mirrors the ROSMAP broad-cell pathway contract for",
    "the 42 sex/APOE-stratified broad-cell contrasts.",
    "",
    "Preranked GSEA is primary and uses every tested core mitochondrial gene",
    "ranked by sign(logFC) * sqrt(F). ORA is a thresholded companion using",
    "strict, relaxed, and exploratory DEG tiers. Each method uses the tested",
    "core mitochondrial universe for that broad cell type.",
    "",
    "The program catalog contains the frozen legacy four modules, 46 broad",
    "MitoCarta3.0 programs, and all 149 MitoCarta3.0 pathways. BH FDR is",
    "reported within contrast/collection and across the declared global",
    "families.",
    "",
    "The seven pooled disease anchors are intentionally excluded because this",
    "release is designed for direct ROSMAP sex/APOE comparison. SEA-AD has no",
    "ROSMAP-equivalent composition-adjusted broad DEG release, so no",
    "composition-sensitivity GSEA is fabricated.",
    "",
    "Non-estimable SEA-AD strata remain explicit and are not negative evidence."
  )
  tables <- list(
    seaad_broad_deg_pathway_checks.tsv = checks,
    seaad_broad_deg_pathway_reference_manifest.tsv = references,
    seaad_broad_deg_pathway_program_manifest.tsv = programs$metadata,
    seaad_broad_deg_pathway_program_membership.tsv.gz =
      programs$membership,
    seaad_broad_deg_pathway_contrast_manifest.tsv = contrast_manifest,
    seaad_broad_deg_pathway_rank_manifest.tsv = ranks$manifest,
    seaad_broad_deg_pathway_ranked_genes.tsv.gz = ranks$genes,
    seaad_broad_deg_pathway_gsea.tsv.gz = gsea,
    seaad_broad_deg_pathway_significant_gsea.tsv.gz = significant_gsea,
    seaad_broad_deg_pathway_background_manifest.tsv =
      backgrounds$manifest,
    seaad_broad_deg_pathway_background_genes.tsv.gz = backgrounds$genes,
    seaad_broad_deg_pathway_ora_query_manifest.tsv = queries$manifest,
    seaad_broad_deg_pathway_ora_query_genes.tsv.gz = queries$genes,
    seaad_broad_deg_pathway_ora.tsv.gz = ora,
    seaad_broad_deg_pathway_significant_ora.tsv.gz = significant_ora,
    seaad_broad_deg_pathway_broad_cell_summary.tsv = broad_summary,
    seaad_broad_deg_pathway_sex_apoe_summary.tsv = sex_summary,
    seaad_broad_deg_pathway_broad_vs_fine_concordance.tsv.gz =
      broad_vs_fine,
    seaad_broad_deg_pathway_redundancy_map.tsv.gz = redundancy
  )
  schemas <- c(
    seaad_broad_deg_pathway_checks.tsv = config$schemas$checks,
    seaad_broad_deg_pathway_reference_manifest.tsv =
      config$schemas$reference_manifest,
    seaad_broad_deg_pathway_program_manifest.tsv =
      config$schemas$program_manifest,
    seaad_broad_deg_pathway_program_membership.tsv.gz =
      config$schemas$program_membership,
    seaad_broad_deg_pathway_contrast_manifest.tsv =
      config$schemas$contrast_manifest,
    seaad_broad_deg_pathway_rank_manifest.tsv =
      config$schemas$rank_manifest,
    seaad_broad_deg_pathway_ranked_genes.tsv.gz =
      config$schemas$ranked_genes,
    seaad_broad_deg_pathway_gsea.tsv.gz = config$schemas$gsea,
    seaad_broad_deg_pathway_significant_gsea.tsv.gz =
      config$schemas$significant_gsea,
    seaad_broad_deg_pathway_background_manifest.tsv =
      config$schemas$background_manifest,
    seaad_broad_deg_pathway_background_genes.tsv.gz =
      config$schemas$background_genes,
    seaad_broad_deg_pathway_ora_query_manifest.tsv =
      config$schemas$ora_query_manifest,
    seaad_broad_deg_pathway_ora_query_genes.tsv.gz =
      config$schemas$ora_query_genes,
    seaad_broad_deg_pathway_ora.tsv.gz = config$schemas$ora,
    seaad_broad_deg_pathway_significant_ora.tsv.gz =
      config$schemas$significant_ora,
    seaad_broad_deg_pathway_broad_cell_summary.tsv =
      config$schemas$broad_cell_summary,
    seaad_broad_deg_pathway_sex_apoe_summary.tsv =
      config$schemas$sex_apoe_summary,
    seaad_broad_deg_pathway_broad_vs_fine_concordance.tsv.gz =
      config$schemas$broad_vs_fine,
    seaad_broad_deg_pathway_redundancy_map.tsv.gz =
      config$schemas$redundancy_map
  )
  status_fields <- data.table::data.table(
    analysis_resolution = "broad",
    analysis_scope = as.character(config$analysis$scope),
    pooled_anchor_policy = as.character(config$analysis$pooled_anchor_policy),
    composition_sensitivity = "not_available_in_seaad_deg_release",
    structural_contrasts = nrow(contrast_manifest),
    completed_contrasts =
      sum(contrast_manifest$analysis_status == "validated_complete"),
    nonestimable_contrasts =
      sum(contrast_manifest$analysis_status == "contrast_not_estimable"),
    broad_cell_types =
      data.table::uniqueN(contrast_manifest$broad_cell_type),
    primary_rank_rows = nrow(ranks$genes),
    query_definitions = nrow(queries$manifest),
    pathway_definitions = nrow(programs$metadata),
    primary_gsea_rows = nrow(gsea),
    tested_primary_gsea_rows = sum(gsea$test_status == "tested"),
    significant_primary_gsea_rows =
      sum(gsea$local_fdr_significant %in% TRUE),
    primary_ora_rows = nrow(ora),
    tested_primary_ora_rows = sum(ora$test_status == "tested"),
    significant_primary_ora_rows =
      sum(ora$local_fdr_significant %in% TRUE),
    broad_vs_fine_rows = nrow(broad_vs_fine),
    blocking_checks = nrow(checks),
    R_version = as.character(getRversion()),
    data_table_version = as.character(packageVersion("data.table")),
    fgsea_version = as.character(packageVersion("fgsea")),
    elapsed_seconds = as.numeric(difftime(
      Sys.time(), started, units = "secs"
    ))
  )
  seaad15_publish(
    final_root, prefix, config, config_path, code_paths, project_root,
    tables, schemas, readme, status_fields
  )
  cat(
    "SEA-AD broad-cell DEG pathway analysis validated and published: ",
    final_root, "\n", sep = ""
  )
  invisible(final_root)
}

if (sys.nframe() == 0L) {
  run_seaad_broad_pathway()
}
