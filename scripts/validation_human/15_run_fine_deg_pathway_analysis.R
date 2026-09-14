#!/usr/bin/env Rscript

source(
  file.path(getwd(), "scripts/validation_human/15_seaad_pathway_common.R"),
  local = globalenv()
)

seaad15_collapse <- function(x) {
  paste(sort(unique(as.character(x[phase11_nonempty(x)]))), collapse = ",")
}

seaad15_build_fine_backgrounds <- function(
    contrast_manifest, status, project_root, config) {
  filter_authority <- unique(status[, .(
    fine_cell_id = supertype_id,
    fine_cell_type = supertype_label,
    filter_path,
    filter_sha256
  )], by = "fine_cell_id")
  phase11_must(
    nrow(filter_authority) ==
      as.integer(config$expected$fine_cell_types),
    "Unexpected number of SEA-AD fine filter authorities"
  )
  rows <- lapply(seq_len(nrow(filter_authority)), function(i) {
    authority <- filter_authority[i]
    path <- phase11_absolute_path(authority$filter_path, project_root)
    seaad15_assert_file_hash(
      path, authority$filter_sha256, "Fine DEG filter"
    )
    x <- seaad15_read(
      path,
      select = c(
        "feature_index", "source_symbol", "current_symbol_for_kda",
        "is_core_mito_phase18", "mapping_status", "test_status"
      )
    )
    x <- x[
      phase11_is_true(is_core_mito_phase18) &
        test_status == "tested" &
        phase11_nonempty(current_symbol_for_kda)
    ]
    x[, fine_cell_id := as.character(authority$fine_cell_id)]
    x[, .(
      source_feature_indices = seaad15_collapse(feature_index),
      source_symbols = seaad15_collapse(source_symbol),
      source_feature_count = .N,
      mapping_statuses = seaad15_collapse(mapping_status)
    ), by = .(
      fine_cell_id,
      symbol_hgnc_current = current_symbol_for_kda
    )]
  })
  context_genes <- data.table::rbindlist(rows, fill = TRUE)
  background_genes <- merge(
    contrast_manifest[, .(
      background_id = contrast_id,
      contrast_id,
      fine_cell_id,
      fine_cell_type,
      broad_cell_type,
      signature_group,
      sex,
      apoe_group
    )],
    context_genes,
    by = "fine_cell_id",
    allow.cartesian = TRUE,
    sort = FALSE
  )
  background_genes[, schema_version := config$schemas$background_genes]
  data.table::setcolorder(
    background_genes,
    c(
      "schema_version", "background_id", "contrast_id", "fine_cell_id",
      "fine_cell_type", "broad_cell_type", "signature_group", "sex",
      "apoe_group", "symbol_hgnc_current", "source_feature_indices",
      "source_symbols", "source_feature_count", "mapping_statuses"
    )
  )
  data.table::setorder(
    background_genes, background_id, symbol_hgnc_current
  )
  sizes <- background_genes[, .(
    background_size = data.table::uniqueN(symbol_hgnc_current),
    source_feature_rows = sum(source_feature_count),
    duplicate_symbol_collapses =
      sum(source_feature_count) - data.table::uniqueN(symbol_hgnc_current)
  ), by = background_id]
  background_manifest <- merge(
    contrast_manifest[, .(
      background_order = contrast_order,
      background_id = contrast_id,
      contrast_id,
      fine_cell_id,
      fine_cell_type,
      broad_cell_type,
      signature_group,
      sex,
      apoe_group,
      structural_status,
      structurally_available
    )],
    sizes,
    by = "background_id",
    all.x = TRUE,
    sort = FALSE
  )
  for (column in c(
    "background_size", "source_feature_rows", "duplicate_symbol_collapses"
  )) {
    data.table::set(
      background_manifest,
      which(is.na(background_manifest[[column]])),
      column,
      0L
    )
  }
  background_manifest[, `:=`(
    schema_version = config$schemas$background_manifest,
    background_status = data.table::fifelse(
      !structurally_available,
      structural_status,
      data.table::fifelse(
        background_size > 0L, "available", "empty_background"
      )
    )
  )]
  data.table::setcolorder(
    background_manifest,
    c(
      "schema_version", "background_order",
      setdiff(
        names(background_manifest),
        c("schema_version", "background_order")
      )
    )
  )
  data.table::setorder(background_manifest, background_order)
  list(manifest = background_manifest, genes = background_genes)
}

seaad15_load_fine_degs <- function(
    completed_status, project_root, absolute_fold_change) {
  effect_threshold <- log2(as.numeric(absolute_fold_change))
  rows <- lapply(seq_len(nrow(completed_status)), function(i) {
    authority <- completed_status[i]
    path <- phase11_absolute_path(authority$result_path, project_root)
    seaad15_assert_file_hash(
      path, authority$result_sha256, "Fine DEG result"
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
        phase11_nonempty(current_symbol_for_kda) &
        is.finite(FDR) & FDR < 0.05 &
        is.finite(logFC) & abs(logFC) > effect_threshold
    ]
    if (!nrow(x)) return(NULL)
    x[, `:=`(
      contrast_id = as.character(authority$contrast_id),
      absolute_logFC = abs(logFC)
    )]
    data.table::setorder(
      x, current_symbol_for_kda, -absolute_logFC, FDR, feature_index
    )
    x[, .(
      source_feature_indices = seaad15_collapse(feature_index),
      source_symbols = seaad15_collapse(source_symbol),
      source_feature_count = .N,
      logFC_min = min(logFC),
      logFC_max = max(logFC),
      logFC_representative = logFC[[1L]],
      F_representative = F[[1L]],
      minimum_p_value = min(PValue),
      minimum_fdr_bh = min(FDR),
      mapping_statuses = seaad15_collapse(mapping_status),
      in_upregulated_query = any(logFC > 0),
      in_downregulated_query = any(logFC < 0)
    ), by = .(
      contrast_id,
      symbol_hgnc_current = current_symbol_for_kda
    )]
  })
  data.table::rbindlist(rows, fill = TRUE)
}

seaad15_build_fine_queries <- function(
    contrast_manifest, collapsed_degs, background_manifest, config) {
  query_modes <- names(config$analysis$query_modes)
  manifest_rows <- vector(
    "list", nrow(contrast_manifest) * length(query_modes)
  )
  gene_rows <- list()
  row_index <- 0L
  for (i in seq_len(nrow(contrast_manifest))) {
    contrast <- contrast_manifest[i]
    x <- collapsed_degs[contrast_id == contrast$contrast_id]
    for (mode in query_modes) {
      row_index <- row_index + 1L
      direction <- as.character(
        config$analysis$query_modes[[mode]]$direction
      )
      selected <- switch(
        direction,
        any = x,
        up = x[in_upregulated_query %in% TRUE],
        down = x[in_downregulated_query %in% TRUE],
        stop("Unsupported fine query direction", call. = FALSE)
      )
      query_id <- paste(contrast$contrast_id, mode, sep = "::")
      if (nrow(selected)) {
        genes <- data.table::copy(selected)
        genes[, `:=`(
          schema_version = config$schemas$query_genes,
          query_id = query_id,
          background_id = as.character(contrast$contrast_id),
          fine_cell_id = as.character(contrast$fine_cell_id),
          fine_cell_type = as.character(contrast$fine_cell_type),
          broad_cell_type = as.character(contrast$broad_cell_type),
          signature_group = as.character(contrast$signature_group),
          sex = as.character(contrast$sex),
          apoe_group = as.character(contrast$apoe_group),
          deg_tier = as.character(config$analysis$deg_tier),
          query_mode = mode
        )]
        gene_rows[[length(gene_rows) + 1L]] <- genes
      }
      size <- data.table::uniqueN(selected$symbol_hgnc_current)
      manifest_rows[[row_index]] <- data.table::data.table(
        schema_version = config$schemas$query_manifest,
        query_order = as.integer(row_index),
        query_id = query_id,
        background_id = as.character(contrast$contrast_id),
        contrast_id = as.character(contrast$contrast_id),
        fine_cell_id = as.character(contrast$fine_cell_id),
        fine_cell_type = as.character(contrast$fine_cell_type),
        broad_cell_type = as.character(contrast$broad_cell_type),
        signature_group = as.character(contrast$signature_group),
        sex = as.character(contrast$sex),
        apoe_group = as.character(contrast$apoe_group),
        deg_tier = as.character(config$analysis$deg_tier),
        query_mode = mode,
        query_direction = direction,
        structural_status = as.character(contrast$structural_status),
        structurally_available = isTRUE(contrast$structurally_available),
        source_significant_feature_rows =
          as.integer(sum(selected$source_feature_count)),
        mapped_unique_query_genes = as.integer(size),
        duplicate_symbol_collapses = as.integer(
          sum(selected$source_feature_count) - size
        ),
        query_size = as.integer(size),
        background_size = as.integer(
          background_manifest[
            background_id == contrast$contrast_id, background_size
          ][[1L]]
        ),
        query_status = if (!isTRUE(contrast$structurally_available)) {
          as.character(contrast$structural_status)
        } else if (size == 0L) {
          "empty_query"
        } else if (size < as.integer(config$analysis$minimum_query_size)) {
          "query_below_minimum"
        } else {
          "eligible_for_pathway_testing"
        }
      )
    }
  }
  manifest <- data.table::rbindlist(manifest_rows, fill = TRUE)
  genes <- data.table::rbindlist(gene_rows, fill = TRUE)
  data.table::setorder(manifest, query_order)
  data.table::setorder(genes, query_id, symbol_hgnc_current)
  list(manifest = manifest, genes = genes)
}

seaad15_build_kda_ora <- function(
    kda_manifest, signature_members, background_members, core_symbols,
    programs, config) {
  active <- kda_manifest[eligibility_status == "eligible"]
  phase11_must(
    nrow(active) == as.integer(config$expected$kda_effective_queries),
    "Unexpected number of eligible SEA-AD KDA queries"
  )
  signatures <- signature_members[
    phase11_is_true(effective_member) & gene %chin% core_symbols
  ]
  backgrounds <- background_members[gene %chin% core_symbols]
  signature_sets <- split(signatures$gene, signatures$kda_run_id)
  background_sets <- split(backgrounds$gene, backgrounds$kda_run_id)
  manifest_rows <- vector("list", nrow(active))
  query_rows <- vector("list", nrow(active))
  background_rows <- vector("list", nrow(active))
  for (i in seq_len(nrow(active))) {
    run <- active[i]
    run_id <- as.character(run$kda_run_id)
    query <- sort(unique(signature_sets[[run_id]] %||% character()))
    background <- sort(unique(background_sets[[run_id]] %||% character()))
    phase11_must(
      all(query %chin% background),
      paste("KDA query is not a subset of its background:", run_id)
    )
    sex <- if (startsWith(run$signature_group, "F_")) {
      "Female"
    } else {
      "Male"
    }
    apoe <- sub("^[FM]_", "", run$signature_group)
    manifest_rows[[i]] <- data.table::data.table(
      query_order = as.integer(i),
      query_id = run_id,
      background_id = run_id,
      contrast_id = as.character(run$contrast_id),
      kda_run_id = run_id,
      fine_cell_type = as.character(run$fine_cell_type),
      broad_cell_type = as.character(run$broad_network),
      sex = sex,
      apoe_group = apoe,
      deg_tier = "kda_effective_query",
      query_mode = "Dementia_both_mito",
      structural_status = as.character(run$terminal_status),
      structurally_available = TRUE,
      query_size = length(query),
      background_size = length(background)
    )
    query_rows[[i]] <- data.table::data.table(
      query_id = run_id,
      symbol_hgnc_current = query,
      in_upregulated_query = FALSE,
      in_downregulated_query = FALSE
    )
    background_rows[[i]] <- data.table::data.table(
      background_id = run_id,
      symbol_hgnc_current = background
    )
  }
  query_manifest <- data.table::rbindlist(manifest_rows)
  query_genes <- data.table::rbindlist(query_rows)
  background_genes <- data.table::rbindlist(background_rows)
  result <- phase11_run_ora(
    query_manifest,
    query_genes,
    background_genes,
    programs$metadata,
    programs$membership,
    config,
    config$schemas$kda_ora
  )
  fine_map <- active[, .(
    contrast_id,
    kda_run_id,
    fine_cell_id = supertype_id,
    fine_cell_type,
    signature_group
  )]
  result <- merge(
    result,
    fine_map,
    by.x = c("contrast_id", "query_id"),
    by.y = c("contrast_id", "kda_run_id"),
    all.x = TRUE,
    sort = FALSE
  )
  result[, `:=`(
    kda_run_id = query_id,
    analysis_profile = "seaad_kda_effective_query_companion"
  )]
  data.table::setcolorder(
    result, c("schema_version", "analysis_profile", "kda_run_id",
      setdiff(
        names(result),
        c("schema_version", "analysis_profile", "kda_run_id")
      ))
  )
  result
}

run_seaad_fine_pathway <- function(
    cli = seaad15_parse_cli(commandArgs(trailingOnly = TRUE))) {
  library(data.table)
  started <- Sys.time()
  loaded <- seaad15_load_config(
    cli$config,
    "seaad_phase15_pathway_deg_fine_config_v1",
    "fine"
  )
  config <- loaded$config
  project_root <- loaded$project_root
  config_path <- loaded$config_path
  script_path <- file.path(
    project_root,
    "scripts/validation_human/15_run_fine_deg_pathway_analysis.R"
  )
  common_path <- file.path(
    project_root, "scripts/validation_human/15_seaad_pathway_common.R"
  )
  shared_path <- file.path(
    project_root, "scripts/lib/phase11_deg_pathway_common.R"
  )
  code_paths <- c(script_path, common_path, shared_path)
  final_root <- phase11_absolute_path(
    config$output$directory, project_root
  )
  prefix <- "seaad_fine_deg_pathway"
  if (dir.exists(final_root)) {
    if (seaad15_valid_existing(
      final_root, prefix, config, config_path, code_paths, project_root
    )) {
      cat("SEA-AD fine pathway bundle is complete and hash-valid: ",
          final_root, "\n", sep = "")
      return(invisible(final_root))
    }
    stop(
      "Existing SEA-AD fine pathway output is not a valid resumable bundle",
      call. = FALSE
    )
  }

  input <- function(name) {
    phase11_absolute_path(config$inputs[[name]], project_root)
  }
  deg_root <- input("deg_root")
  deg_release <- seaad15_validate_release(
    deg_root, project_root, "seaad_deg_fine_status_v1", "VH08F", "fine"
  )
  kda_root <- input("kda_input_root")
  kda_release <- seaad15_validate_simple_bundle(
    kda_root, project_root, "seaad_fine_phase_status_v2", "VH10A"
  )
  paths <- c(
    deg_status = deg_release$status_path,
    deg_artifacts = deg_release$artifacts_path,
    contrast_status = input("contrast_status"),
    result_index = input("result_index"),
    gene_annotation = input("gene_annotation"),
    kda_status = kda_release$status_path,
    kda_artifacts = kda_release$artifacts_path,
    kda_manifest = file.path(kda_root, "seaad_kda_run_manifest.tsv"),
    kda_signatures =
      file.path(kda_root, "seaad_kda_signature_members.tsv.gz"),
    kda_backgrounds =
      file.path(kda_root, "seaad_kda_background_members.tsv.gz"),
    legacy_module_membership = input("legacy_module_membership"),
    mitocarta_source = input("mitocarta_source"),
    scientific_script = script_path,
    seaad_pathway_common = common_path,
    shared_pathway_library = shared_path,
    scientific_config = config_path
  )
  phase11_must(all(file.exists(paths)), "A required fine VH15 input is missing")
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

  contrast_manifest <- status[, .(
    contrast_order = as.integer(contrast_slot),
    contrast_id,
    fine_cell_id = supertype_id,
    fine_cell_type = supertype_label,
    broad_cell_type = broad_network,
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
    structural_status = data.table::fifelse(
      terminal_status == "completed",
      "estimable_validated",
      paste0("not_estimable:", terminal_reason)
    ),
    structurally_available = terminal_status == "completed"
  )]
  contrast_manifest[, schema_version := config$schemas$contrast_manifest]
  data.table::setcolorder(
    contrast_manifest,
    c("schema_version", "contrast_order", setdiff(
      names(contrast_manifest), c("schema_version", "contrast_order")
    ))
  )
  data.table::setorder(contrast_manifest, contrast_order)

  backgrounds <- seaad15_build_fine_backgrounds(
    contrast_manifest, status, project_root, config
  )
  collapsed_degs <- seaad15_load_fine_degs(
    status[terminal_status == "completed"],
    project_root,
    config$analysis$absolute_fold_change
  )
  queries <- seaad15_build_fine_queries(
    contrast_manifest, collapsed_degs, backgrounds$manifest, config
  )
  ora <- phase11_run_ora(
    queries$manifest,
    queries$genes,
    backgrounds$genes,
    programs$metadata,
    programs$membership,
    config,
    config$schemas$ora
  )
  fine_map <- contrast_manifest[, .(
    contrast_id, fine_cell_id, fine_cell_type, signature_group
  )]
  ora <- merge(ora, fine_map, by = "contrast_id", all.x = TRUE, sort = FALSE)
  ora[, `:=`(
    analysis_profile = "primary_pre_network_fine_deg",
    cohort = "SEA-AD"
  )]
  data.table::setcolorder(
    ora, c("schema_version", "cohort", "analysis_profile",
      setdiff(
        names(ora), c("schema_version", "cohort", "analysis_profile")
      ))
  )
  significant <- data.table::copy(
    ora[local_fdr_significant %in% TRUE]
  )
  significant[, schema_version := config$schemas$significant_results]

  fine_summary <- ora[, .(
    structural_status = data.table::first(structural_status),
    structurally_available = data.table::first(structurally_available),
    background_size = max(background_size),
    query_size = max(query_size),
    pathway_count = .N,
    testable_pathways = sum(test_status == "tested"),
    locally_significant_pathways =
      sum(local_fdr_significant %in% TRUE),
    globally_significant_pathways =
      sum(global_fdr_significant %in% TRUE),
    minimum_local_fdr_bh = seaad15_safe_min(local_fdr_bh),
    top_pathway = if (any(is.finite(local_fdr_bh))) {
      pathway_name[which.min(local_fdr_bh)]
    } else {
      NA_character_
    }
  ), by = .(
    contrast_id, fine_cell_id, fine_cell_type, broad_cell_type,
    signature_group, sex, apoe_group, query_mode,
    pathway_collection, collection_role
  )]
  fine_summary[, schema_version := config$schemas$fine_cell_summary]
  data.table::setcolorder(
    fine_summary,
    c("schema_version", setdiff(names(fine_summary), "schema_version"))
  )
  broad_summary <- seaad15_recurrence_summary(
    ora,
    c(
      "signature_group", "sex", "apoe_group", "broad_cell_type",
      "query_mode", "pathway_collection", "collection_role",
      "pathway_id", "pathway_name", "hierarchy_depth", "level_1", "level_2"
    ),
    config$schemas$broad_cell_summary
  )
  sex_summary <- seaad15_recurrence_summary(
    ora,
    c(
      "signature_group", "sex", "apoe_group", "query_mode",
      "pathway_collection", "collection_role", "pathway_id",
      "pathway_name", "hierarchy_depth", "level_1", "level_2"
    ),
    config$schemas$sex_apoe_summary
  )
  redundancy <- phase11_compute_redundancy_map(
    programs$metadata,
    programs$membership,
    config$schemas$redundancy_map,
    as.numeric(config$redundancy$representative_jaccard_threshold)
  )

  annotation <- seaad15_read(
    paths[["gene_annotation"]],
    select = c("current_symbol_for_kda", "is_core_mito_phase18")
  )
  core_symbols <- unique(annotation[
    phase11_is_true(is_core_mito_phase18) &
      phase11_nonempty(current_symbol_for_kda),
    current_symbol_for_kda
  ])
  kda_manifest <- seaad15_read(paths[["kda_manifest"]])
  kda_signatures <- seaad15_read(paths[["kda_signatures"]])
  kda_backgrounds <- seaad15_read(paths[["kda_backgrounds"]])
  kda_ora <- seaad15_build_kda_ora(
    kda_manifest, kda_signatures, kda_backgrounds, core_symbols,
    programs, config
  )

  query_background_keys <- unique(backgrounds$genes[, .(
    background_id, symbol_hgnc_current
  )])
  query_keys <- unique(queries$genes[, .(
    background_id, symbol_hgnc_current
  )])
  query_outside_background <- query_keys[
    !query_background_keys,
    on = .(background_id, symbol_hgnc_current)
  ]
  direction_conflicts <- collapsed_degs[
    in_upregulated_query & in_downregulated_query, .N
  ]
  threshold <- as.numeric(config$fdr$threshold)
  check_rows <- list(
    list(
      "fine_release_validated", TRUE, "validated_complete",
      "validated_complete", "All declared VH08F artifacts were hash-checked"
    ),
    list(
      "structural_contrast_count",
      nrow(contrast_manifest) ==
        as.integer(config$expected$structural_contrasts),
      nrow(contrast_manifest), config$expected$structural_contrasts, ""
    ),
    list(
      "completed_contrast_count",
      sum(contrast_manifest$structurally_available) ==
        as.integer(config$expected$completed_contrasts),
      sum(contrast_manifest$structurally_available),
      config$expected$completed_contrasts, ""
    ),
    list(
      "nonestimable_contrast_count",
      sum(!contrast_manifest$structurally_available) ==
        as.integer(config$expected$nonestimable_contrasts),
      sum(!contrast_manifest$structurally_available),
      config$expected$nonestimable_contrasts, ""
    ),
    list(
      "completed_result_index_count",
      nrow(result_index) == as.integer(config$expected$completed_contrasts),
      nrow(result_index), config$expected$completed_contrasts, ""
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
      "collapsed_direction_conflicts",
      direction_conflicts == 0L, direction_conflicts, 0L,
      "A mapped symbol must not enter both directional queries"
    ),
    list(
      "program_definition_count",
      nrow(programs$metadata) ==
        as.integer(config$expected$pathway_definitions),
      nrow(programs$metadata), config$expected$pathway_definitions, ""
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
      seaad15_fdr_flags_match(ora, threshold), TRUE, TRUE, ""
    ),
    list(
      "kda_effective_query_count",
      data.table::uniqueN(kda_ora$kda_run_id) ==
        as.integer(config$expected$kda_effective_queries),
      data.table::uniqueN(kda_ora$kda_run_id),
      config$expected$kda_effective_queries, ""
    ),
    list(
      "kda_ora_rows",
      nrow(kda_ora) == as.integer(config$expected$kda_ora_rows),
      nrow(kda_ora), config$expected$kda_ora_rows, ""
    ),
    list(
      "kda_ora_pvalues_reproduce",
      seaad15_pvalues_reproduce(kda_ora), TRUE, TRUE, ""
    ),
    list(
      "kda_ora_fdr_flags_match",
      seaad15_fdr_flags_match(kda_ora, threshold), TRUE, TRUE, ""
    ),
    list(
      "upstream_references_hash_bound",
      seaad15_reference_files_match(references, project_root),
      TRUE, TRUE, ""
    )
  )
  checks <- seaad15_checks(check_rows, config$schemas$checks)
  failed <- checks[passed == FALSE, check]
  phase11_must(
    !length(failed),
    paste("SEA-AD fine pathway checks failed:", paste(failed, collapse = ", "))
  )

  readme <- c(
    "# SEA-AD fine-cell DEG pathway analysis",
    "",
    "This VH15F release mirrors the ROSMAP fine-cell pathway contract.",
    "It applies ORA to strict mitochondrial DEG lists for each of 129 fine",
    "cell types by six sex/APOE strata. Strict means FDR < 0.05 and",
    "|log2 fold change| > log2(1.3).",
    "",
    "Each ORA uses the core mitochondrial genes tested in that fine-cell",
    "context as its background. The program catalog contains the frozen",
    "legacy four modules, 46 broad MitoCarta3.0 programs, and all 149",
    "MitoCarta3.0 pathways. BH FDR is reported locally and globally.",
    "",
    "The KDA companion tests the 22 eligible merged-direction SEA-AD KDA",
    "queries against the same programs. It is supplementary to the",
    "pre-network DEG analysis and must not be interpreted as an independent",
    "DEG test.",
    "",
    "SEA-AD's smaller strata create many structurally non-estimable contrasts;",
    "these remain explicit rows and are never treated as negative evidence."
  )
  tables <- list(
    seaad_fine_deg_pathway_checks.tsv = checks,
    seaad_fine_deg_pathway_reference_manifest.tsv = references,
    seaad_fine_deg_pathway_program_manifest.tsv = programs$metadata,
    seaad_fine_deg_pathway_program_membership.tsv.gz =
      programs$membership,
    seaad_fine_deg_pathway_contrast_manifest.tsv = contrast_manifest,
    seaad_fine_deg_pathway_background_manifest.tsv =
      backgrounds$manifest,
    seaad_fine_deg_pathway_background_genes.tsv.gz = backgrounds$genes,
    seaad_fine_deg_pathway_query_manifest.tsv = queries$manifest,
    seaad_fine_deg_pathway_query_genes.tsv.gz = queries$genes,
    seaad_fine_deg_pathway_ora.tsv.gz = ora,
    seaad_fine_deg_pathway_significant_results.tsv.gz = significant,
    seaad_fine_deg_pathway_fine_cell_summary.tsv = fine_summary,
    seaad_fine_deg_pathway_broad_cell_summary.tsv = broad_summary,
    seaad_fine_deg_pathway_sex_apoe_summary.tsv = sex_summary,
    seaad_fine_deg_pathway_redundancy_map.tsv.gz = redundancy,
    seaad_kda_effective_query_program_ora.tsv.gz = kda_ora
  )
  schemas <- c(
    seaad_fine_deg_pathway_checks.tsv = config$schemas$checks,
    seaad_fine_deg_pathway_reference_manifest.tsv =
      config$schemas$reference_manifest,
    seaad_fine_deg_pathway_program_manifest.tsv =
      config$schemas$program_manifest,
    seaad_fine_deg_pathway_program_membership.tsv.gz =
      config$schemas$program_membership,
    seaad_fine_deg_pathway_contrast_manifest.tsv =
      config$schemas$contrast_manifest,
    seaad_fine_deg_pathway_background_manifest.tsv =
      config$schemas$background_manifest,
    seaad_fine_deg_pathway_background_genes.tsv.gz =
      config$schemas$background_genes,
    seaad_fine_deg_pathway_query_manifest.tsv =
      config$schemas$query_manifest,
    seaad_fine_deg_pathway_query_genes.tsv.gz =
      config$schemas$query_genes,
    seaad_fine_deg_pathway_ora.tsv.gz = config$schemas$ora,
    seaad_fine_deg_pathway_significant_results.tsv.gz =
      config$schemas$significant_results,
    seaad_fine_deg_pathway_fine_cell_summary.tsv =
      config$schemas$fine_cell_summary,
    seaad_fine_deg_pathway_broad_cell_summary.tsv =
      config$schemas$broad_cell_summary,
    seaad_fine_deg_pathway_sex_apoe_summary.tsv =
      config$schemas$sex_apoe_summary,
    seaad_fine_deg_pathway_redundancy_map.tsv.gz =
      config$schemas$redundancy_map,
    seaad_kda_effective_query_program_ora.tsv.gz =
      config$schemas$kda_ora
  )
  status_fields <- data.table::data.table(
    analysis_resolution = "fine",
    analysis_scope = "sex_apoe_stratified",
    deg_rule = as.character(config$analysis$deg_rule),
    structural_contrasts = nrow(contrast_manifest),
    completed_contrasts = sum(contrast_manifest$structurally_available),
    nonestimable_contrasts = sum(!contrast_manifest$structurally_available),
    fine_cell_types = data.table::uniqueN(contrast_manifest$fine_cell_id),
    query_definitions = nrow(queries$manifest),
    pathway_definitions = nrow(programs$metadata),
    primary_ora_rows = nrow(ora),
    tested_primary_ora_rows = sum(ora$test_status == "tested"),
    significant_primary_ora_rows =
      sum(ora$local_fdr_significant %in% TRUE),
    kda_effective_queries = data.table::uniqueN(kda_ora$kda_run_id),
    kda_ora_rows = nrow(kda_ora),
    blocking_checks = nrow(checks),
    elapsed_seconds = as.numeric(difftime(
      Sys.time(), started, units = "secs"
    ))
  )
  seaad15_publish(
    final_root, prefix, config, config_path, code_paths, project_root,
    tables, schemas, readme, status_fields
  )
  cat(
    "SEA-AD fine-cell DEG pathway analysis validated and published: ",
    final_root, "\n", sep = ""
  )
  invisible(final_root)
}

if (sys.nframe() == 0L) {
  run_seaad_fine_pathway()
}
