#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_cli <- function(args) {
  out <- list(
    config = NULL,
    execution_config = NULL,
    task_mode = NULL,
    force = FALSE
  )
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/11_run_broad_deg_pathway_analysis.R ",
        "--config FILE --execution-config FILE ",
        "--task-mode pathway_deg_broad [--force]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (key == "--force") {
      out$force <- TRUE
      i <- i + 1L
      next
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  required <- c("config", "execution_config", "task_mode")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) {
    stop(
      "Missing required options: ", paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
  if (!identical(out$task_mode, "pathway_deg_broad")) {
    stop("--task-mode must be pathway_deg_broad", call. = FALSE)
  }
  out
}

broad_output_schema_map <- function(config) {
  c(
    broad_deg_pathway_checks.tsv = config$schemas$checks,
    broad_deg_pathway_reference_manifest.tsv =
      config$schemas$reference_manifest,
    broad_deg_pathway_program_manifest.tsv = config$schemas$program_manifest,
    broad_deg_pathway_contrast_manifest.tsv =
      config$schemas$contrast_manifest,
    broad_deg_pathway_rank_manifest.tsv = config$schemas$rank_manifest,
    broad_deg_pathway_ranked_genes.tsv.gz = config$schemas$ranked_genes,
    broad_deg_pathway_gsea.tsv.gz = config$schemas$gsea,
    broad_deg_pathway_significant_gsea.tsv.gz =
      config$schemas$significant_gsea,
    broad_deg_pathway_background_manifest.tsv =
      config$schemas$background_manifest,
    broad_deg_pathway_background_genes.tsv.gz =
      config$schemas$background_genes,
    broad_deg_pathway_ora_query_manifest.tsv =
      config$schemas$ora_query_manifest,
    broad_deg_pathway_ora_query_genes.tsv.gz =
      config$schemas$ora_query_genes,
    broad_deg_pathway_ora.tsv.gz = config$schemas$ora,
    broad_deg_pathway_significant_ora.tsv.gz =
      config$schemas$significant_ora,
    broad_deg_pathway_composition_rank_manifest.tsv =
      config$schemas$composition_rank_manifest,
    broad_deg_pathway_composition_ranked_genes.tsv.gz =
      config$schemas$composition_ranked_genes,
    broad_deg_pathway_composition_gsea.tsv.gz =
      config$schemas$composition_gsea,
    broad_deg_pathway_composition_concordance.tsv =
      config$schemas$composition_concordance,
    broad_deg_pathway_broad_cell_summary.tsv =
      config$schemas$broad_cell_summary,
    broad_deg_pathway_sex_apoe_summary.tsv =
      config$schemas$sex_apoe_summary,
    broad_deg_pathway_broad_vs_fine_concordance.tsv.gz =
      config$schemas$broad_vs_fine,
    broad_deg_pathway_redundancy_map.tsv.gz =
      config$schemas$redundancy_map,
    README.md = "markdown_v1"
  )
}

broad_expected_artifact_records <- function(config, status) {
  c(
    broad_deg_pathway_checks.tsv = as.integer(status$blocking_checks[[1L]]),
    broad_deg_pathway_reference_manifest.tsv =
      as.integer(config$expected$reference_inputs),
    broad_deg_pathway_program_manifest.tsv =
      as.integer(config$expected$program_definitions),
    broad_deg_pathway_contrast_manifest.tsv =
      as.integer(config$expected$planned_contrasts),
    broad_deg_pathway_rank_manifest.tsv =
      as.integer(config$expected$primary_rank_definitions),
    broad_deg_pathway_ranked_genes.tsv.gz =
      as.integer(config$expected$primary_core_mito_rows),
    broad_deg_pathway_gsea.tsv.gz =
      as.integer(config$expected$primary_gsea_rows),
    broad_deg_pathway_significant_gsea.tsv.gz =
      as.integer(status$significant_primary_gsea_rows[[1L]]),
    broad_deg_pathway_background_manifest.tsv =
      as.integer(config$expected$planned_contrasts),
    broad_deg_pathway_background_genes.tsv.gz =
      as.integer(config$expected$background_gene_rows),
    broad_deg_pathway_ora_query_manifest.tsv =
      as.integer(config$expected$ora_query_definitions),
    broad_deg_pathway_ora_query_genes.tsv.gz =
      as.integer(config$expected$ora_query_gene_rows),
    broad_deg_pathway_ora.tsv.gz =
      as.integer(config$expected$primary_ora_rows),
    broad_deg_pathway_significant_ora.tsv.gz =
      as.integer(status$significant_ora_rows[[1L]]),
    broad_deg_pathway_composition_rank_manifest.tsv =
      as.integer(config$expected$composition_rank_definitions),
    broad_deg_pathway_composition_ranked_genes.tsv.gz =
      as.integer(config$expected$composition_core_mito_rows),
    broad_deg_pathway_composition_gsea.tsv.gz =
      as.integer(config$expected$composition_gsea_rows),
    broad_deg_pathway_composition_concordance.tsv =
      as.integer(config$expected$composition_gsea_rows),
    broad_deg_pathway_broad_cell_summary.tsv =
      as.integer(config$expected$broad_cell_summary_rows),
    broad_deg_pathway_sex_apoe_summary.tsv =
      as.integer(config$expected$sex_apoe_summary_rows),
    broad_deg_pathway_broad_vs_fine_concordance.tsv.gz =
      as.integer(config$expected$broad_vs_fine_rows),
    broad_deg_pathway_redundancy_map.tsv.gz =
      as.integer(config$expected$redundancy_pairs),
    README.md = as.integer(status$readme_lines[[1L]])
  )
}

broad_reference_files_match <- function(references, project_root) {
  if (!all(c("path", "sha256", "bytes") %in% names(references))) {
    return(FALSE)
  }
  all(vapply(seq_len(nrow(references)), function(i) {
    input_path <- phase11_absolute_path(references$path[[i]], project_root)
    file.exists(input_path) &&
      identical(
        phase11_sha256_file(input_path), references$sha256[[i]]
      ) &&
      as.numeric(file.info(input_path)$size) ==
        as.numeric(references$bytes[[i]])
  }, logical(1)))
}

valid_existing_bundle <- function(
    final_root, project_root, config,
    script_hash, common_hash, config_hash) {
  status_path <- file.path(final_root, "broad_deg_pathway_status.tsv")
  artifacts_path <- file.path(final_root, "broad_deg_pathway_artifacts.tsv")
  if (!file.exists(status_path) || !file.exists(artifacts_path)) return(FALSE)
  status <- tryCatch(data.table::fread(status_path), error = function(e) NULL)
  artifacts <- tryCatch(
    data.table::fread(artifacts_path), error = function(e) NULL
  )
  if (is.null(status) || is.null(artifacts) || nrow(status) != 1L) {
    return(FALSE)
  }
  if (!phase11_schema_ok(status, config$schemas$status) ||
      !phase11_schema_ok(artifacts, config$schemas$artifacts)) {
    return(FALSE)
  }
  if (!identical(status$validation_status[[1L]], "validated_complete") ||
      !identical(status$scientific_script_sha256[[1L]], script_hash) ||
      !identical(status$common_library_sha256[[1L]], common_hash) ||
      !identical(status$scientific_config_sha256[[1L]], config_hash)) {
    return(FALSE)
  }
  if (!"artifacts_manifest_sha256" %in% names(status) ||
      !identical(
        status$artifacts_manifest_sha256[[1L]],
        phase11_sha256_file(artifacts_path)
      )) {
    return(FALSE)
  }
  expected_schemas <- broad_output_schema_map(config)
  expected_artifacts <- names(expected_schemas)
  if (nrow(artifacts) != as.integer(config$expected$output_artifacts) ||
      anyDuplicated(artifacts$artifact) ||
      anyDuplicated(artifacts$path) ||
      !setequal(artifacts$artifact, expected_artifacts)) {
    return(FALSE)
  }
  artifacts <- artifacts[match(expected_artifacts, artifact)]
  expected_paths <- phase11_relative_path(
    file.path(final_root, expected_artifacts), project_root
  )
  expected_records <- broad_expected_artifact_records(config, status)
  if (!identical(artifacts$path, expected_paths) ||
      !identical(artifacts$output_schema, unname(expected_schemas)) ||
      !identical(as.integer(artifacts$records), unname(expected_records)) ||
      !all(artifacts$validation_status == "validated_complete")) {
    return(FALSE)
  }
  if (!all(vapply(
    seq_len(nrow(artifacts)),
    function(i) phase11_artifact_valid(artifacts[i], project_root),
    logical(1)
  ))) {
    return(FALSE)
  }
  reference_path <- file.path(
    final_root, "broad_deg_pathway_reference_manifest.tsv"
  )
  references <- tryCatch(
    data.table::fread(reference_path), error = function(e) NULL
  )
  if (is.null(references) ||
      !phase11_schema_ok(references, config$schemas$reference_manifest) ||
      nrow(references) != as.integer(config$expected$reference_inputs) ||
      anyDuplicated(references$input_id) ||
      anyDuplicated(references$path) ||
      !all(references$validation_status == "validated_input")) {
    return(FALSE)
  }
  broad_reference_files_match(references, project_root)
}

require_bound_artifact <- function(
    manifest, artifact_name, expected_path, project_root,
    manifest_label = "artifact manifest") {
  row <- manifest[artifact == artifact_name]
  phase11_must(
    nrow(row) == 1L,
    paste(manifest_label, "must contain exactly one", artifact_name)
  )
  declared <- normalizePath(
    phase11_absolute_path(row$path[[1L]], project_root),
    mustWork = FALSE
  )
  expected <- normalizePath(expected_path, mustWork = FALSE)
  phase11_must(
    identical(declared, expected),
    paste(manifest_label, "path is not bound to", artifact_name)
  )
  phase11_must(
    phase11_artifact_valid(row, project_root),
    paste(artifact_name, "failed checksum or byte validation")
  )
  row
}

build_rank_bundle <- function(
    source, contrast_manifest, profile, manifest_schema, genes_schema,
    negative_f_tolerance, available_status = "validated_complete") {
  rank_rows <- vector("list", nrow(contrast_manifest))
  manifest_rows <- vector("list", nrow(contrast_manifest))
  source_split <- split(source, source$contrast_id)

  for (i in seq_len(nrow(contrast_manifest))) {
    contrast <- contrast_manifest[i]
    contrast_id <- as.character(contrast$contrast_id)
    rank_id <- if (identical(profile, "primary")) {
      contrast_id
    } else {
      paste0(contrast_id, "::", profile)
    }
    available <- identical(
      as.character(contrast$analysis_status), available_status
    )
    x <- source_split[[contrast_id]]
    if (is.null(x)) x <- source[0]
    source_rows <- nrow(x)
    duplicate_symbols <- if (source_rows) {
      sum(duplicated(x$symbol_hgnc_current))
    } else {
      0L
    }
    finite <- if (source_rows) {
      is.finite(x$logFC) & is.finite(x$F) &
        x$F >= -negative_f_tolerance &
        phase11_nonempty(x$symbol_hgnc_current)
    } else {
      logical()
    }
    valid <- x[finite]
    valid[, F_for_rank := pmax(F, 0)]
    valid[, rank_score := sign(logFC) * sqrt(F_for_rank)]
    valid <- valid[is.finite(rank_score)]
    data.table::setorder(
      valid, -rank_score, -logFC, symbol_hgnc_current, gene
    )
    valid[, rank_position := seq_len(.N)]

    if (available) {
      phase11_must(source_rows > 0L, paste(
        "No rank source rows for completed contrast", contrast_id
      ))
      phase11_must(
        duplicate_symbols == 0L,
        paste("Duplicate rank symbols for", contrast_id)
      )
      phase11_must(
        nrow(valid) == source_rows,
        paste("Invalid rank inputs for", contrast_id)
      )
    } else {
      phase11_must(
        source_rows == 0L,
        paste("Unavailable contrast unexpectedly has rank rows", contrast_id)
      )
    }

    manifest_rows[[i]] <- data.table::data.table(
      schema_version = manifest_schema,
      analysis_profile = profile,
      rank_order = as.integer(contrast$manifest_row),
      rank_id = rank_id,
      contrast_id = contrast_id,
      broad_cell_type = as.character(contrast$broad_cell_type),
      group_id = as.character(contrast$group_id),
      sex = as.character(contrast$sex),
      apoe_group = as.character(contrast$apoe_group),
      structural_status = as.character(contrast$analysis_status),
      structurally_available = available,
      source_rows = as.integer(source_rows),
      finite_rank_rows = as.integer(nrow(valid)),
      duplicate_symbols = as.integer(duplicate_symbols),
      tiny_negative_f_clamped = as.integer(sum(
        is.finite(x$F) & x$F < 0 & x$F >= -negative_f_tolerance
      )),
      materially_negative_f = as.integer(sum(
        is.finite(x$F) & x$F < -negative_f_tolerance
      )),
      rank_size = as.integer(nrow(valid)),
      rank_status = if (available) "available" else {
        as.character(contrast$analysis_status)
      },
      rank_statistic = "sign(logFC)*sqrt(max(F,0))",
      negative_f_tolerance = as.numeric(negative_f_tolerance),
      deterministic_tie_break = "rank_score_desc;logFC_desc;symbol_asc"
    )
    if (nrow(valid)) {
      rank_rows[[i]] <- valid[, .(
        schema_version = genes_schema,
        analysis_profile = profile,
        rank_id = rank_id,
        contrast_id = contrast_id,
        broad_cell_type = as.character(contrast$broad_cell_type),
        group_id = as.character(contrast$group_id),
        sex = as.character(contrast$sex),
        apoe_group = as.character(contrast$apoe_group),
        rank_position = as.integer(rank_position),
        gene,
        symbol_hgnc_current,
        logFC,
        F,
        F_for_rank,
        p_value,
        fdr_bh_within_contrast,
        rank_score
      )]
    }
  }

  manifest <- data.table::rbindlist(manifest_rows, fill = TRUE)
  genes <- data.table::rbindlist(rank_rows, fill = TRUE)
  data.table::setorder(manifest, rank_order)
  data.table::setorder(genes, rank_id, rank_position)
  list(manifest = manifest, genes = genes)
}

build_background_bundle <- function(
    core, contrast_manifest, manifest_schema, genes_schema) {
  universes <- unique(core[, .(
    broad_cell_type, symbol_hgnc_current
  )])
  data.table::setorder(universes, broad_cell_type, symbol_hgnc_current)

  for (cell_type in unique(contrast_manifest$broad_cell_type)) {
    expected <- universes[
      broad_cell_type == cell_type, symbol_hgnc_current
    ]
    observed <- split(
      core[broad_cell_type == cell_type, symbol_hgnc_current],
      core[broad_cell_type == cell_type, contrast_id]
    )
    phase11_must(
      all(vapply(observed, setequal, logical(1), y = expected)),
      paste("Core-mito tested universe differs by contrast for", cell_type)
    )
  }

  rows <- lapply(seq_len(nrow(contrast_manifest)), function(i) {
    contrast <- contrast_manifest[i]
    symbols <- universes[
      broad_cell_type == contrast$broad_cell_type,
      symbol_hgnc_current
    ]
    data.table::data.table(
      schema_version = genes_schema,
      background_id = as.character(contrast$contrast_id),
      contrast_id = as.character(contrast$contrast_id),
      broad_cell_type = as.character(contrast$broad_cell_type),
      symbol_hgnc_current = sort(symbols),
      background_origin = if (
        contrast$analysis_status == "validated_complete"
      ) {
        "tested_genes_for_contrast"
      } else {
        "inferred_from_completed_broad_cell_siblings"
      }
    )
  })
  genes <- data.table::rbindlist(rows)
  manifest <- contrast_manifest[, .(
    schema_version = manifest_schema,
    background_order = as.integer(manifest_row),
    background_id = contrast_id,
    contrast_id,
    broad_cell_type,
    group_id,
    sex,
    apoe_group,
    structural_status = analysis_status,
    structurally_available = analysis_status == "validated_complete"
  )]
  sizes <- genes[, .(
    background_size = data.table::uniqueN(symbol_hgnc_current)
  ), by = background_id]
  manifest <- merge(
    manifest, sizes, by = "background_id", all.x = TRUE, sort = FALSE
  )
  manifest[, background_status := data.table::fifelse(
    structurally_available, "available", structural_status
  )]
  data.table::setorder(manifest, background_order)
  data.table::setorder(genes, background_id, symbol_hgnc_current)
  list(manifest = manifest, genes = genes)
}

build_ora_queries <- function(
    core, contrast_manifest, config, manifest_schema, genes_schema) {
  tier_names <- names(config$analysis$deg_tiers)
  mode_names <- names(config$analysis$query_modes)
  source_split <- split(core, core$contrast_id)
  manifest_rows <- list()
  gene_rows <- list()
  row_index <- 0L

  for (i in seq_len(nrow(contrast_manifest))) {
    contrast <- contrast_manifest[i]
    x <- source_split[[as.character(contrast$contrast_id)]]
    if (is.null(x)) x <- core[0]
    available <- identical(
      as.character(contrast$analysis_status), "validated_complete"
    )
    for (tier in tier_names) {
      tier_flag <- paste0(tier, "_deg")
      for (mode in mode_names) {
        row_index <- row_index + 1L
        selected <- if (available && nrow(x)) {
          phase11_is_true(x[[tier_flag]]) & switch(
            mode,
            AD_any_mito = TRUE,
            AD_up_mito = x$direction == "AD_up",
            AD_down_mito = x$direction == "AD_down"
          )
        } else {
          rep(FALSE, nrow(x))
        }
        genes <- x[selected]
        query_id <- paste(
          contrast$contrast_id, tier, mode, sep = "::"
        )
        up_count <- sum(genes$direction == "AD_up")
        down_count <- sum(genes$direction == "AD_down")
        manifest_rows[[row_index]] <- data.table::data.table(
          schema_version = manifest_schema,
          query_order = as.integer(row_index),
          query_id = query_id,
          background_id = as.character(contrast$contrast_id),
          contrast_id = as.character(contrast$contrast_id),
          broad_cell_type = as.character(contrast$broad_cell_type),
          group_id = as.character(contrast$group_id),
          sex = as.character(contrast$sex),
          apoe_group = as.character(contrast$apoe_group),
          deg_tier = tier,
          tier_order = as.integer(config$analysis$deg_tiers[[tier]]$order),
          tier_role = as.character(config$analysis$deg_tiers[[tier]]$role),
          query_mode = mode,
          query_mode_order = as.integer(
            config$analysis$query_modes[[mode]]$order
          ),
          structural_status = as.character(contrast$analysis_status),
          structurally_available = available,
          query_size = as.integer(nrow(genes)),
          upregulated_query_genes = as.integer(up_count),
          downregulated_query_genes = as.integer(down_count),
          query_status = if (!available) {
            as.character(contrast$analysis_status)
          } else if (!nrow(genes)) {
            "empty_query"
          } else if (
            nrow(genes) < as.integer(config$analysis$minimum_query_size)
          ) {
            "query_below_minimum"
          } else {
            "eligible_for_pathway_testing"
          }
        )
        if (nrow(genes)) {
          gene_rows[[row_index]] <- genes[, .(
            schema_version = genes_schema,
            query_id = query_id,
            contrast_id = as.character(contrast$contrast_id),
            broad_cell_type = as.character(contrast$broad_cell_type),
            sex = as.character(contrast$sex),
            apoe_group = as.character(contrast$apoe_group),
            deg_tier = tier,
            query_mode = mode,
            gene,
            symbol_hgnc_current,
            logFC,
            F,
            p_value,
            fdr_bh_within_contrast,
            direction,
            in_upregulated_query = direction == "AD_up",
            in_downregulated_query = direction == "AD_down"
          )]
        }
      }
    }
  }
  manifest <- data.table::rbindlist(manifest_rows, fill = TRUE)
  genes <- data.table::rbindlist(gene_rows, fill = TRUE)
  data.table::setorder(manifest, query_order)
  data.table::setorder(genes, query_id, symbol_hgnc_current)
  list(manifest = manifest, genes = genes)
}

safe_min <- function(x) {
  x <- x[is.finite(x)]
  if (length(x)) min(x) else NA_real_
}

safe_max <- function(x) {
  x <- x[is.finite(x)]
  if (length(x)) max(x) else NA_real_
}

safe_median <- function(x) {
  x <- x[is.finite(x)]
  if (length(x)) stats::median(x) else NA_real_
}

summarize_gsea <- function(gsea, group_type, schema) {
  x <- data.table::copy(gsea)
  if (group_type == "broad_cell_type") {
    x[, `:=`(
      summary_group = broad_cell_type,
      secondary_group = paste(sex, apoe_group, sep = "::"),
      summary_broad_cell_type = broad_cell_type,
      summary_sex = NA_character_,
      summary_apoe_group = NA_character_
    )]
  } else {
    x[, `:=`(
      summary_group = paste(sex, apoe_group, sep = "::"),
      secondary_group = broad_cell_type,
      summary_broad_cell_type = NA_character_,
      summary_sex = sex,
      summary_apoe_group = apoe_group
    )]
  }
  x[, {
    tested <- test_status == "tested"
    significant <- local_fdr_significant %in% TRUE
    recurrence <- phase11_recurrence_fields(
      leading_edge_genes, significant
    )
    c(list(
      schema_version = schema,
      summary_group_type = group_type,
      broad_cell_type = summary_broad_cell_type[[1L]],
      sex = summary_sex[[1L]],
      apoe_group = summary_apoe_group[[1L]],
      analysis_method = "GSEA",
      deg_tier = NA_character_,
      query_mode = NA_character_,
      structural_contrasts = data.table::uniqueN(contrast_id),
      available_contrasts = data.table::uniqueN(
        contrast_id[structurally_available %in% TRUE]
      ),
      testable_records = sum(tested),
      positive_records = sum(tested & normalized_enrichment_score > 0),
      negative_records = sum(tested & normalized_enrichment_score < 0),
      locally_significant_records = sum(significant),
      globally_significant_records = sum(global_fdr_significant %in% TRUE),
      median_effect = safe_median(normalized_enrichment_score[tested]),
      minimum_effect = safe_min(normalized_enrichment_score[tested]),
      maximum_effect = safe_max(normalized_enrichment_score[tested]),
      significant_secondary_groups =
        data.table::uniqueN(secondary_group[significant]),
      signal_confined_to_one_secondary_group =
        data.table::uniqueN(secondary_group[significant]) == 1L &&
        any(significant)
    ), recurrence)
  }, by = .(
    summary_group, analysis_profile, pathway_collection,
    collection_order, collection_role, pathway_id, pathway_name,
    hierarchy, hierarchy_depth, level_1, level_2, pathway_scope
  )]
}

summarize_ora <- function(ora, group_type, schema) {
  x <- data.table::copy(ora)
  if (group_type == "broad_cell_type") {
    x[, `:=`(
      summary_group = broad_cell_type,
      secondary_group = paste(sex, apoe_group, sep = "::"),
      summary_broad_cell_type = broad_cell_type,
      summary_sex = NA_character_,
      summary_apoe_group = NA_character_
    )]
  } else {
    x[, `:=`(
      summary_group = paste(sex, apoe_group, sep = "::"),
      secondary_group = broad_cell_type,
      summary_broad_cell_type = NA_character_,
      summary_sex = sex,
      summary_apoe_group = apoe_group
    )]
  }
  x[, {
    tested <- test_status == "tested"
    significant <- local_fdr_significant %in% TRUE
    recurrence <- phase11_recurrence_fields(overlap_genes, significant)
    c(list(
      schema_version = schema,
      summary_group_type = group_type,
      broad_cell_type = summary_broad_cell_type[[1L]],
      sex = summary_sex[[1L]],
      apoe_group = summary_apoe_group[[1L]],
      analysis_method = "ORA",
      analysis_profile = "thresholded_ora",
      structural_contrasts = data.table::uniqueN(contrast_id),
      available_contrasts = data.table::uniqueN(
        contrast_id[structurally_available %in% TRUE]
      ),
      testable_records = sum(tested),
      positive_records = if (query_mode[[1L]] == "AD_up_mito") {
        sum(significant)
      } else {
        NA_integer_
      },
      negative_records = if (query_mode[[1L]] == "AD_down_mito") {
        sum(significant)
      } else {
        NA_integer_
      },
      locally_significant_records = sum(significant),
      globally_significant_records = sum(global_fdr_significant %in% TRUE),
      median_effect = safe_median(fold_enrichment[significant]),
      minimum_effect = safe_min(fold_enrichment[significant]),
      maximum_effect = safe_max(fold_enrichment[significant]),
      significant_secondary_groups =
        data.table::uniqueN(secondary_group[significant]),
      signal_confined_to_one_secondary_group =
        data.table::uniqueN(secondary_group[significant]) == 1L &&
        any(significant)
    ), recurrence)
  }, by = .(
    summary_group, deg_tier, query_mode, pathway_collection,
    collection_order, collection_role, pathway_id, pathway_name,
    hierarchy, hierarchy_depth, level_1, level_2, pathway_scope
  )]
}

build_summary <- function(gsea, composition_gsea, ora, group_type, schema) {
  gsea_rows <- summarize_gsea(
    data.table::rbindlist(list(gsea, composition_gsea), fill = TRUE),
    group_type, schema
  )
  ora_rows <- summarize_ora(ora, group_type, schema)
  result <- data.table::rbindlist(
    list(gsea_rows, ora_rows), use.names = TRUE, fill = TRUE
  )
  data.table::setorderv(
    result,
    c(
      "summary_group", "analysis_method", "analysis_profile",
      "deg_tier", "query_mode", "collection_order", "pathway_id"
    ),
    na.last = TRUE
  )
  result
}

build_composition_concordance <- function(
    primary, composition, sensitivity_summary, schema) {
  key <- c("contrast_id", "pathway_collection", "pathway_id")
  p <- primary[, .(
    contrast_id, broad_cell_type, sex, apoe_group,
    pathway_collection, collection_order, collection_role,
    pathway_id, pathway_name, hierarchy, hierarchy_depth,
    level_1, level_2, pathway_scope,
    primary_test_status = test_status,
    primary_nes = normalized_enrichment_score,
    primary_p_value = p_value,
    primary_local_fdr_bh = local_fdr_bh,
    primary_local_significant = local_fdr_significant,
    primary_global_fdr_bh = global_fdr_bh,
    primary_leading_edge_genes = leading_edge_genes
  )]
  c <- composition[, .(
    contrast_id, pathway_collection, pathway_id,
    composition_test_status = test_status,
    composition_testability_reason = testability_reason,
    composition_nes = normalized_enrichment_score,
    composition_p_value = p_value,
    composition_local_fdr_bh = local_fdr_bh,
    composition_local_significant = local_fdr_significant,
    composition_global_fdr_bh = global_fdr_bh,
    composition_leading_edge_genes = leading_edge_genes
  )]
  result <- merge(p, c, by = key, all.x = TRUE, sort = FALSE)
  result <- merge(
    result,
    sensitivity_summary[, .(
      contrast_id,
      whole_transcriptome_logFC_pearson = logFC_pearson,
      whole_transcriptome_sign_concordance = sign_concordance,
      upstream_sensitivity_status = sensitivity_terminal_status
    )],
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  overlap <- mapply(function(a, b) {
    length(intersect(phase11_split_genes(a), phase11_split_genes(b)))
  }, result$primary_leading_edge_genes, result$composition_leading_edge_genes)
  union_size <- mapply(function(a, b) {
    length(union(phase11_split_genes(a), phase11_split_genes(b)))
  }, result$primary_leading_edge_genes, result$composition_leading_edge_genes)
  result[, `:=`(
    schema_version = schema,
    both_profiles_tested =
      primary_test_status == "tested" & composition_test_status == "tested",
    nes_sign_concordant = data.table::fifelse(
      primary_test_status == "tested" & composition_test_status == "tested",
      sign(primary_nes) == sign(composition_nes), NA
    ),
    nes_difference = composition_nes - primary_nes,
    absolute_nes_difference = abs(composition_nes - primary_nes),
    leading_edge_overlap_count = as.integer(overlap),
    leading_edge_union_count = as.integer(union_size),
    leading_edge_jaccard = data.table::fifelse(
      union_size > 0L, overlap / union_size, NA_real_
    ),
    primary_signal_survives_composition =
      primary_local_significant %in% TRUE &
      composition_local_significant %in% TRUE &
      sign(primary_nes) == sign(composition_nes)
  )]
  data.table::setcolorder(result, c("schema_version", setdiff(
    names(result), "schema_version"
  )))
  data.table::setorder(result, contrast_id, collection_order, pathway_id)
  result
}

build_broad_vs_fine <- function(broad_ora, fine_ora, schema) {
  fine <- fine_ora[
    analysis_profile == "primary_pre_network_fine_deg"
  ]
  keys <- c(
    "broad_cell_type", "sex", "apoe_group", "query_mode",
    "pathway_collection", "pathway_id"
  )
  fine_summary <- fine[, {
    significant <- local_fdr_significant %in% TRUE
    overlap_union <- sort(unique(unlist(
      lapply(overlap_genes[significant], phase11_split_genes),
      use.names = FALSE
    )))
    list(
      fine_query_records = .N,
      fine_testable_queries = sum(test_status == "tested"),
      fine_locally_significant_queries = sum(significant),
      any_fine_local_significant = any(significant),
      fine_best_local_fdr_bh = safe_min(local_fdr_bh),
      fine_maximum_fold_enrichment = safe_max(fold_enrichment[significant]),
      significant_fine_cell_types = paste(
        sort(unique(fine_cell_type[significant])), collapse = ","
      ),
      significant_fine_cell_type_count =
        data.table::uniqueN(fine_cell_type[significant]),
      fine_significant_overlap_gene_union = paste(
        overlap_union, collapse = ","
      ),
      fine_significant_overlap_gene_union_count = length(overlap_union)
    )
  }, by = keys]
  broad <- broad_ora[deg_tier == "strict"]
  result <- merge(
    broad, fine_summary, by = keys, all.x = TRUE, sort = FALSE
  )
  result[, `:=`(
    broad_resolution_testable = test_status == "tested",
    fine_resolution_testable =
      !is.na(fine_testable_queries) & fine_testable_queries > 0L
  )]
  result[, resolution_concordance := data.table::fcase(
    !broad_resolution_testable | !fine_resolution_testable,
    "not_comparable",
    local_fdr_significant %in% TRUE &
      any_fine_local_significant %in% TRUE,
    "concordant_support",
    local_fdr_significant %in% TRUE,
    "broad_only",
    any_fine_local_significant %in% TRUE,
    "fine_only",
    default = "neither"
  )]
  result[, schema_version := schema]
  data.table::setcolorder(result, c("schema_version", setdiff(
    names(result), "schema_version"
  )))
  data.table::setorder(
    result, query_order, collection_order, source_pathway_order
  )
  result
}

run_analysis <- function(cli = parse_cli(commandArgs(trailingOnly = TRUE))) {
  required_packages <- c(
    "data.table", "yaml", "digest", "readxl", "fgsea"
  )
  missing_packages <- required_packages[!vapply(
    required_packages, requireNamespace, logical(1), quietly = TRUE
  )]
  if (length(missing_packages)) {
    stop(
      "Required package(s) not installed: ",
      paste(missing_packages, collapse = ", "),
      ". Restore the project environment before running production.",
      call. = FALSE
    )
  }
  library(data.table)

  start_time <- Sys.time()
  project_root <- normalizePath(getwd(), mustWork = TRUE)
  common_path <- file.path(
    project_root, "scripts/lib/phase11_deg_pathway_common.R"
  )
  if (!file.exists(common_path)) {
    stop("Shared Phase 11 library is missing", call. = FALSE)
  }
  source(common_path, local = globalenv())

  pipeline_config_path <- phase11_absolute_path(cli$config, project_root)
  execution_config_path <- phase11_absolute_path(
    cli$execution_config, project_root
  )
  phase11_must(file.exists(pipeline_config_path), "Pipeline config is missing")
  phase11_must(
    file.exists(execution_config_path), "Execution config is missing"
  )
  pipeline_config <- yaml::read_yaml(pipeline_config_path)
  execution_config <- yaml::read_yaml(execution_config_path)
  phase_config_path <- phase11_absolute_path(
    pipeline_config$project$phase11_pathway_deg_broad_config %||% "",
    project_root
  )
  phase11_must(
    file.exists(phase_config_path),
    "Broad-DEG pathway config is missing from the pipeline config"
  )
  config <- yaml::read_yaml(phase_config_path)
  phase11_must(
    identical(
      config$schema_version, "phase11_pathway_deg_broad_config_v1"
    ),
    "Unexpected broad-DEG pathway config schema"
  )
  phase11_must(
    identical(
      as.character(utils::packageVersion("fgsea")),
      as.character(config$gsea$required_fgsea_version)
    ),
    paste0(
      "fgsea version must be ", config$gsea$required_fgsea_version,
      "; installed version is ", utils::packageVersion("fgsea")
    )
  )

  execution <- execution_config$execution
  execution_stage <- as.character(execution$execution_stage)
  phase11_must(
    execution_stage %in% c(
      "local_pilot", "local_production_equivalent",
      "minerva_production", "lsf_fallback"
    ),
    "Unsupported execution stage"
  )
  output_root <- phase11_absolute_path(
    pipeline_config$outputs$root, project_root
  )
  final_root <- file.path(output_root, as.character(config$output$directory))
  staging_root <- file.path(
    output_root,
    paste0(".", config$output$directory, ".staging.", Sys.getpid())
  )
  script_path <- file.path(
    project_root, "scripts/11_run_broad_deg_pathway_analysis.R"
  )
  script_hash <- phase11_sha256_file(script_path)
  common_hash <- phase11_sha256_file(common_path)
  config_hash <- phase11_sha256_file(phase_config_path)

  if (dir.exists(final_root)) {
    if (valid_existing_bundle(
      final_root, project_root,
      config,
      script_hash, common_hash, config_hash
    )) {
      cat(
        "Broad-DEG pathway output is complete and hash-valid: ",
        final_root, "\n", sep = ""
      )
      return(invisible(final_root))
    }
    stop(
      "Output directory exists but is not a complete hash-valid bundle: ",
      final_root,
      if (isTRUE(cli$force)) {
        " (--force never deletes or overwrites an invalid production bundle)"
      } else {
        ""
      },
      call. = FALSE
    )
  }
  phase11_must(
    !dir.exists(staging_root), "Process-specific staging directory exists"
  )
  dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
  on.exit({
    if (dir.exists(staging_root)) unlink(staging_root, recursive = TRUE)
  }, add = TRUE)

  input_path <- function(key) {
    phase11_absolute_path(config$inputs[[key]], project_root)
  }
  broad_root <- input_path("broad_deg_root")
  phase09_root <- input_path("phase09_root")
  phase11_root <- input_path("phase11_similarity_root")
  fine_root <- input_path("phase11_fine_root")
  paths <- list(
    broad_status = file.path(broad_root, "broad_deg_status.tsv"),
    broad_checks = file.path(broad_root, "broad_deg_checks.tsv"),
    broad_artifacts = file.path(broad_root, "broad_deg_artifacts.tsv"),
    broad_config_snapshot = file.path(
      broad_root, "00_inputs/phase08_broad_deg_config_snapshot.yml"
    ),
    broad_manifest = file.path(
      broad_root, "00_inputs/broad_deg_contrast_manifest.tsv"
    ),
    broad_contrast_status = file.path(
      broad_root, "broad_deg_contrast_status.tsv"
    ),
    broad_results = file.path(broad_root, "broad_deg_results.tsv.gz"),
    broad_model_diagnostics = file.path(
      broad_root, "broad_deg_model_diagnostics.tsv"
    ),
    broad_filter_funnel = file.path(
      broad_root, "broad_deg_filter_funnel.tsv"
    ),
    composition_results = file.path(
      broad_root,
      "04_sensitivity/broad_deg_composition_adjusted.tsv.gz"
    ),
    composition_status = file.path(
      broad_root,
      "04_sensitivity/broad_deg_sensitivity_contrast_status.tsv"
    ),
    composition_summary = file.path(
      broad_root, "04_sensitivity/broad_deg_sensitivity_summary.tsv"
    ),
    composition_checks = file.path(
      broad_root, "04_sensitivity/broad_deg_sensitivity_checks.tsv"
    ),
    phase09_status = file.path(phase09_root, "annotation_status.tsv"),
    phase09_checks = file.path(phase09_root, "annotation_checks.tsv"),
    phase09_artifacts = file.path(phase09_root, "annotation_artifacts.tsv"),
    phase09_master = file.path(
      phase09_root, "gene_annotation_master.tsv.gz"
    ),
    phase11_status = file.path(phase11_root, "pathway_status.tsv"),
    phase11_artifacts = file.path(phase11_root, "pathway_artifacts.tsv"),
    phase11_reference = file.path(
      phase11_root, "pathway_reference_manifest.tsv"
    ),
    phase11_membership = file.path(
      phase11_root, "pathway_membership_long.tsv.gz"
    ),
    fine_status = file.path(fine_root, "fine_deg_pathway_status.tsv"),
    fine_artifacts = file.path(fine_root, "fine_deg_pathway_artifacts.tsv"),
    fine_reference = file.path(
      fine_root, "fine_deg_pathway_reference_manifest.tsv"
    ),
    fine_program = file.path(
      fine_root, "fine_deg_pathway_program_manifest.tsv"
    ),
    fine_ora = file.path(fine_root, "fine_deg_pathway_ora.tsv.gz"),
    legacy = input_path("legacy_module_membership"),
    mitocarta = input_path("mitocarta_source")
  )
  missing_paths <- names(paths)[!vapply(paths, file.exists, logical(1))]
  phase11_must(
    !length(missing_paths),
    paste("Required inputs are missing:", paste(missing_paths, collapse = ", "))
  )

  broad_status <- fread(paths$broad_status)
  broad_checks <- fread(paths$broad_checks)
  broad_artifacts <- fread(paths$broad_artifacts)
  contrast_source <- fread(paths$broad_manifest)
  contrast_status <- fread(paths$broad_contrast_status)
  model_diagnostics <- fread(paths$broad_model_diagnostics)
  filter_funnel <- fread(paths$broad_filter_funnel)
  sensitivity_status <- fread(paths$composition_status)
  sensitivity_summary <- fread(paths$composition_summary)
  sensitivity_checks <- fread(paths$composition_checks)

  phase11_must(
    phase11_schema_ok(broad_status, config$expected_schemas$broad_status) &&
      broad_status$validation_status[[1L]] == "validated_complete",
    "Broad DEG status is not validated_complete"
  )
  phase11_must(
    phase11_schema_ok(broad_checks, config$expected_schemas$broad_checks) &&
      all(phase11_is_true(broad_checks$passed)),
    "Broad DEG checks did not all pass"
  )
  phase11_must(
    phase11_schema_ok(
      broad_artifacts, config$expected_schemas$broad_artifacts
    ),
    "Unexpected broad DEG artifact schema"
  )
  phase11_must(
    phase11_schema_ok(
      contrast_source, config$expected_schemas$broad_contrast_manifest
    ) &&
      phase11_schema_ok(
        contrast_status, config$expected_schemas$broad_contrast_status
      ) &&
      phase11_schema_ok(
        model_diagnostics, config$expected_schemas$broad_model_diagnostics
      ) &&
      phase11_schema_ok(
        filter_funnel, config$expected_schemas$broad_filter_funnel
      ),
    "Unexpected broad DEG contract schema"
  )
  phase11_must(
    phase11_schema_ok(
      sensitivity_status, config$expected_schemas$composition_status
    ) &&
      phase11_schema_ok(
        sensitivity_summary, config$expected_schemas$composition_summary
      ) &&
      phase11_schema_ok(
        sensitivity_checks, config$expected_schemas$composition_checks
      ) &&
      all(phase11_is_true(sensitivity_checks$passed)),
    "Composition-sensitivity contract is invalid"
  )
  phase11_must(
    !anyDuplicated(contrast_source$contrast_id) &&
      !anyDuplicated(contrast_status$contrast_id) &&
      setequal(contrast_source$contrast_id, contrast_status$contrast_id) &&
      all(contrast_source$modeling_status %in% c(
        "estimable", "not_estimable"
      )) &&
      all(contrast_status$terminal_status %in% c(
        "validated_complete", "not_estimable"
      )),
    "Primary contrast statuses contain missing, failed, or unknown states"
  )
  primary_status_contract <- merge(
    contrast_source[, .(contrast_id, modeling_status)],
    contrast_status[, .(contrast_id, terminal_status)],
    by = "contrast_id", sort = FALSE
  )
  phase11_must(
    all(
      (primary_status_contract$modeling_status == "estimable" &
        primary_status_contract$terminal_status == "validated_complete") |
        (primary_status_contract$modeling_status == "not_estimable" &
          primary_status_contract$terminal_status == "not_estimable")
    ),
    "Primary manifest and terminal statuses are inconsistent"
  )
  phase11_must(
    !anyDuplicated(sensitivity_status$contrast_id) &&
      setequal(contrast_source$contrast_id, sensitivity_status$contrast_id) &&
      all(sensitivity_status$terminal_status %in% c(
        "validated_complete", "not_applicable", "not_estimable"
      )),
    "Composition statuses contain missing, failed, or unknown states"
  )

  phase11_must(
    !anyDuplicated(broad_artifacts$artifact) &&
      !anyDuplicated(broad_artifacts$path),
    "Broad DEG artifact manifest contains duplicate keys"
  )
  direct_broad_artifacts <- c(
    phase08_broad_deg_config_snapshot.yml = paths$broad_config_snapshot,
    broad_deg_contrast_manifest.tsv = paths$broad_manifest,
    broad_deg_contrast_status.tsv = paths$broad_contrast_status,
    broad_deg_model_diagnostics.tsv = paths$broad_model_diagnostics,
    broad_deg_filter_funnel.tsv = paths$broad_filter_funnel,
    broad_deg_results.tsv.gz = paths$broad_results,
    broad_deg_composition_adjusted.tsv.gz = paths$composition_results,
    broad_deg_sensitivity_contrast_status.tsv = paths$composition_status,
    broad_deg_sensitivity_summary.tsv = paths$composition_summary,
    broad_deg_sensitivity_checks.tsv = paths$composition_checks
  )
  direct_rows <- rbindlist(lapply(
    names(direct_broad_artifacts),
    function(artifact_name) require_bound_artifact(
      broad_artifacts, artifact_name,
      direct_broad_artifacts[[artifact_name]], project_root,
      "Broad DEG artifact manifest"
    )
  ))
  physical_expected <- contrast_source[, .(
    artifact = paste0(
      broad_cell_type, "__", group_id, ".broad_deg.tsv.gz"
    ),
    expected_path = file.path(
      broad_root, "05_by_contrast",
      paste0(broad_cell_type, "__", group_id, ".broad_deg.tsv.gz")
    )
  )]
  physical_rows <- broad_artifacts[
    grepl("[.]broad_deg[.]tsv[.]gz$", artifact)
  ]
  phase11_must(
    nrow(physical_expected) == as.integer(config$expected$planned_contrasts) &&
      nrow(physical_rows) == nrow(physical_expected) &&
      setequal(physical_rows$artifact, physical_expected$artifact),
    "Physical broad-DEG artifact set does not match the contrast manifest"
  )
  physical_rows <- rbindlist(lapply(seq_len(nrow(physical_expected)), function(i) {
    require_bound_artifact(
      broad_artifacts, physical_expected$artifact[[i]],
      physical_expected$expected_path[[i]], project_root,
      "Broad DEG artifact manifest"
    )
  }))
  required_rows <- rbindlist(list(direct_rows, physical_rows), fill = TRUE)
  broad_provenance_hashes_exact <- identical(
      broad_status$config_sha256[[1L]],
      phase11_sha256_file(paths$broad_config_snapshot)
    ) &&
      identical(
        broad_status$annotation_master_sha256[[1L]],
        phase11_sha256_file(paths$phase09_master)
      )
  phase11_must(
    broad_provenance_hashes_exact,
    "Broad DEG status provenance hashes do not match consumed authorities"
  )

  phase09_status <- fread(paths$phase09_status)
  phase09_checks <- fread(paths$phase09_checks)
  phase09_artifacts <- fread(paths$phase09_artifacts)
  phase11_status <- fread(paths$phase11_status)
  phase11_artifacts <- fread(paths$phase11_artifacts)
  phase11_reference <- fread(paths$phase11_reference)
  phase11_membership <- fread(paths$phase11_membership)
  fine_status <- fread(paths$fine_status)
  fine_artifacts <- fread(paths$fine_artifacts)
  fine_reference <- fread(paths$fine_reference)
  fine_program <- fread(paths$fine_program)

  phase11_must(
    phase11_schema_ok(
      phase09_status, config$expected_schemas$phase09_status
    ) &&
      phase09_status$validation_status[[1L]] == "validated_complete" &&
      phase11_schema_ok(
        phase09_checks, config$expected_schemas$phase09_checks
      ) &&
      all(phase11_is_true(phase09_checks$passed)) &&
      phase11_schema_ok(
        phase09_artifacts, config$expected_schemas$phase09_artifacts
      ),
    "Phase 09 annotation bundle is invalid"
  )
  phase11_must(
    !anyDuplicated(phase09_artifacts$artifact) &&
      !anyDuplicated(phase09_artifacts$path),
    "Phase 09 artifact manifest contains duplicate keys"
  )
  phase09_master_artifact <- require_bound_artifact(
    phase09_artifacts, "gene_annotation_master.tsv.gz",
    paths$phase09_master, project_root, "Phase 09 artifact manifest"
  )
  phase11_must(
    phase11_schema_ok(
      phase11_status, config$expected_schemas$phase11_status
    ) &&
      phase11_status$validation_status[[1L]] == "validated_complete" &&
      phase11_schema_ok(
        phase11_artifacts, config$expected_schemas$phase11_artifacts
      ) &&
      phase11_schema_ok(
        phase11_reference,
        config$expected_schemas$phase11_reference_manifest
      ) &&
      phase11_schema_ok(
        phase11_membership, config$expected_schemas$phase11_membership
      ),
    "Phase 11 pathway reference bundle is invalid"
  )
  phase11_must(
    !anyDuplicated(phase11_artifacts$artifact) &&
      !anyDuplicated(phase11_artifacts$path),
    "Phase 11 artifact manifest contains duplicate keys"
  )
  phase11_required <- rbindlist(list(
    require_bound_artifact(
      phase11_artifacts, "pathway_reference_manifest.tsv",
      paths$phase11_reference, project_root, "Phase 11 artifact manifest"
    ),
    require_bound_artifact(
      phase11_artifacts, "pathway_membership_long.tsv.gz",
      paths$phase11_membership, project_root, "Phase 11 artifact manifest"
    )
  ))
  phase11_must(
    phase11_schema_ok(fine_status, config$expected_schemas$fine_status) &&
      fine_status$validation_status[[1L]] == "validated_complete" &&
      phase11_schema_ok(
        fine_artifacts, config$expected_schemas$fine_artifacts
      ) &&
      phase11_schema_ok(
        fine_reference, config$expected_schemas$fine_reference_manifest
      ) &&
      phase11_schema_ok(
        fine_program, config$expected_schemas$fine_program_manifest
      ),
    "Fine-DEG pathway bundle is invalid"
  )
  phase11_must(
    !anyDuplicated(fine_artifacts$artifact) &&
      !anyDuplicated(fine_artifacts$path),
    "Fine-DEG artifact manifest contains duplicate keys"
  )
  fine_required <- rbindlist(list(
    require_bound_artifact(
      fine_artifacts, "fine_deg_pathway_reference_manifest.tsv",
      paths$fine_reference, project_root, "Fine-DEG artifact manifest"
    ),
    require_bound_artifact(
      fine_artifacts, "fine_deg_pathway_program_manifest.tsv",
      paths$fine_program, project_root, "Fine-DEG artifact manifest"
    ),
    require_bound_artifact(
      fine_artifacts, "fine_deg_pathway_ora.tsv.gz",
      paths$fine_ora, project_root, "Fine-DEG artifact manifest"
    )
  ))
  fine_authorities <- c(
    phase11_reference = paths$phase11_reference,
    phase11_membership = paths$phase11_membership,
    legacy_module_membership = paths$legacy,
    mitocarta_source = paths$mitocarta
  )
  phase11_must(
    !anyDuplicated(fine_reference$input_role) &&
      all(names(fine_authorities) %in% fine_reference$input_role),
    "Fine-DEG reference manifest lacks a required pathway authority"
  )
  for (input_role in names(fine_authorities)) {
    current_role <- input_role
    row <- fine_reference[
      fine_reference$input_role == current_role
    ]
    current_path <- fine_authorities[[input_role]]
    phase11_must(
      nrow(row) == 1L &&
        identical(
          normalizePath(
            phase11_absolute_path(row$path[[1L]], project_root),
            mustWork = FALSE
          ),
          normalizePath(current_path, mustWork = FALSE)
        ) &&
        identical(
          row$sha256[[1L]], phase11_sha256_file(current_path)
        ) &&
        as.numeric(row$bytes[[1L]]) ==
          as.numeric(file.info(current_path)$size),
      paste("Fine-DEG pathway authority differs for", input_role)
    )
  }
  phase11_must(
    identical(
      phase11_sha256_file(paths$mitocarta),
      as.character(config$references$mitocarta$source_sha256)
    ),
    "MitoCarta source checksum differs from the frozen config"
  )

  results <- fread(paths$broad_results, showProgress = FALSE)
  composition <- fread(paths$composition_results, showProgress = FALSE)
  fine_ora <- fread(paths$fine_ora, showProgress = FALSE)
  phase09_master <- fread(
    paths$phase09_master,
    select = c(
      "symbol_hgnc_current", "mito_tier", "reference_only"
    ),
    showProgress = FALSE
  )
  legacy <- fread(paths$legacy)
  phase11_must(
    phase11_schema_ok(results, config$expected_schemas$broad_results) &&
      phase11_schema_ok(
        composition, config$expected_schemas$composition_results
      ) &&
      phase11_schema_ok(fine_ora, config$expected_schemas$fine_ora),
    "Unexpected result-table schema"
  )

  physical_artifacts <- broad_artifacts[
    grepl("[.]broad_deg[.]tsv[.]gz$", artifact)
  ]
  reconciliation_columns <- c(
    "contrast_id", "broad_cell_type", "group_id", "sex", "apoe_group",
    "gene", "logFC", "F", "p_value", "fdr_bh_within_contrast",
    "symbol_hgnc_current", "mapping_status", "is_mitocarta3",
    "is_mtDNA_gene", "mito_tier", "genome_origin",
    "strict_deg", "relaxed_deg", "exploratory_deg", "direction"
  )
  physical <- rbindlist(lapply(
    phase11_absolute_path(physical_artifacts$path, project_root),
    fread,
    select = reconciliation_columns,
    showProgress = FALSE
  ), use.names = TRUE)
  combined_reconciliation <- results[, ..reconciliation_columns]
  setorder(physical, contrast_id, gene)
  setorder(combined_reconciliation, contrast_id, gene)
  physical_reconstruction_exact <- isTRUE(all.equal(
    physical, combined_reconciliation,
    check.attributes = FALSE, tolerance = 0
  ))
  direction_labels_exact <- identical(
    results$direction,
    ifelse(results$logFC > 0, "AD_up", "AD_down")
  )
  phase11_must(
    direction_labels_exact,
    "Stored DEG direction labels do not match logFC signs"
  )

  strict_reproduced <- with(
    results,
    fdr_bh_within_contrast < 0.05 &
      abs(logFC) > log2(1.3)
  )
  relaxed_reproduced <- with(
    results,
    fdr_bh_within_contrast <= 0.10 &
      abs(logFC) >= log2(1.2)
  )
  exploratory_reproduced <- with(
    results, fdr_bh_within_contrast <= 0.20
  )
  strict_exact <- identical(
    as.logical(results$strict_deg), as.logical(strict_reproduced)
  )
  relaxed_exact <- identical(
    as.logical(results$relaxed_deg), as.logical(relaxed_reproduced)
  )
  exploratory_exact <- identical(
    as.logical(results$exploratory_deg),
    as.logical(exploratory_reproduced)
  )

  contrast_manifest <- merge(
    contrast_source,
    contrast_status[, .(
      contrast_id,
      terminal_status,
      genes_returned,
      terminal_message = message
    )],
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  contrast_manifest[, `:=`(
    schema_version = config$schemas$contrast_manifest,
    analysis_status = data.table::fcase(
      terminal_status == "validated_complete", "validated_complete",
      terminal_status == "not_estimable", "contrast_not_estimable",
      default = NA_character_
    )
  )]
  phase11_must(
    all(phase11_nonempty(contrast_manifest$analysis_status)),
    "Primary analysis status mapping is incomplete"
  )
  setorder(contrast_manifest, manifest_row)
  setcolorder(contrast_manifest, c(
    "schema_version", setdiff(names(contrast_manifest), "schema_version")
  ))

  core <- results[mito_tier == config$analysis$primary_mito_tier]
  phase11_must(
    nrow(core) == as.integer(config$expected$primary_core_mito_rows),
    "Unexpected number of primary core-mito result rows"
  )
  phase11_must(
    all(phase11_nonempty(core$symbol_hgnc_current)) &&
      !anyDuplicated(core[, .(contrast_id, symbol_hgnc_current)]),
    "Core-mito symbol identities are incomplete or duplicated"
  )
  annotation_core_symbols <- unique(phase09_master[
    mito_tier == config$analysis$primary_mito_tier &
      !phase11_is_true(reference_only),
    symbol_hgnc_current
  ])
  broad_symbols_in_phase09 <- all(
    unique(core$symbol_hgnc_current) %in% annotation_core_symbols
  )

  parsed_mitocarta <- phase11_parse_mitocarta_source(paths$mitocarta)
  normalized_mitocarta <- phase11_membership[
    pathway_collection ==
      config$references$mitocarta$normalized_collection,
    .(pathway_id, symbol_hgnc_current)
  ]
  mitocarta_reconciles <- setequal(
    parsed_mitocarta$membership[
      , paste(pathway_id, symbol_hgnc_current, sep = "\r")
    ],
    normalized_mitocarta[
      , paste(pathway_id, symbol_hgnc_current, sep = "\r")
    ]
  )
  programs <- phase11_build_program_collections(
    legacy, parsed_mitocarta, config
  )
  program_manifest <- programs$metadata
  program_membership <- programs$membership
  program_compare_columns <- setdiff(
    intersect(names(program_manifest), names(fine_program)),
    "schema_version"
  )
  broad_program_authority <- copy(
    program_manifest[, ..program_compare_columns]
  )
  fine_program_authority <- copy(
    fine_program[, ..program_compare_columns]
  )
  setorderv(
    broad_program_authority,
    c("collection_order", "source_pathway_order", "pathway_id")
  )
  setorderv(
    fine_program_authority,
    c("collection_order", "source_pathway_order", "pathway_id")
  )
  fine_program_manifest_reconciles <- isTRUE(all.equal(
    broad_program_authority, fine_program_authority,
    check.attributes = FALSE, tolerance = 0
  ))
  phase11_must(
    fine_program_manifest_reconciles,
    "Broad and fine pathway program manifests do not reconcile"
  )

  primary_ranks <- build_rank_bundle(
    core, contrast_manifest, "primary",
    config$schemas$rank_manifest, config$schemas$ranked_genes,
    negative_f_tolerance = as.numeric(
      config$analysis$negative_f_tolerance
    )
  )
  backgrounds <- build_background_bundle(
    core, contrast_manifest,
    config$schemas$background_manifest,
    config$schemas$background_genes
  )
  queries <- build_ora_queries(
    core, contrast_manifest, config,
    config$schemas$ora_query_manifest,
    config$schemas$ora_query_genes
  )

  primary_complete <- phase11_run_gsea_collection(
    primary_ranks$manifest, primary_ranks$genes,
    program_manifest, program_membership,
    "mitocarta_complete_149", config, config$schemas$gsea, "primary"
  )
  primary_legacy <- phase11_run_gsea_collection(
    primary_ranks$manifest, primary_ranks$genes,
    program_manifest, program_membership,
    "legacy_four", config, config$schemas$gsea, "primary"
  )
  primary_broad <- phase11_derive_broad_gsea(
    primary_complete, program_manifest, config$schemas$gsea
  )
  primary_gsea <- phase11_finalize_gsea(
    rbindlist(
      list(primary_legacy, primary_broad, primary_complete),
      use.names = TRUE, fill = TRUE
    ),
    config
  )

  ora <- phase11_run_ora(
    queries$manifest, queries$genes,
    backgrounds$genes, program_manifest, program_membership,
    config, config$schemas$ora
  )

  annotation_authority <- unique(results[, .(
    broad_cell_type, gene, symbol_hgnc_current, mito_tier,
    mapping_status, is_mitocarta3, is_mtDNA_gene, genome_origin
  )])
  phase11_must(
    !anyDuplicated(annotation_authority[, .(broad_cell_type, gene)]),
    "Broad-cell gene annotation authority is not unique"
  )
  phase11_must(
    !anyDuplicated(composition[, .(contrast_id, gene)]),
    "Composition result keys are duplicated"
  )
  composition_pairs <- unique(composition[, .(
    contrast_id, broad_cell_type
  )])
  expected_pairs <- contrast_manifest[, .(
    contrast_id, expected_broad_cell_type = broad_cell_type
  )]
  composition_pairs <- merge(
    composition_pairs, expected_pairs,
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  phase11_must(
    nrow(composition_pairs) ==
      uniqueN(composition[, .(contrast_id, broad_cell_type)]) &&
      all(
        composition_pairs$broad_cell_type ==
          composition_pairs$expected_broad_cell_type
      ),
    "Composition contrast-to-broad-cell identities are inconsistent"
  )
  annotation_authority[, annotation_joined := TRUE]
  composition_annotated <- merge(
    composition, annotation_authority,
    by = c("broad_cell_type", "gene"),
    all.x = TRUE, sort = FALSE
  )
  composition_annotation_exact <-
    nrow(composition_annotated) == nrow(composition) &&
    nrow(composition) == as.integer(
      broad_status$sensitivity_result_rows[[1L]]
    ) &&
    all(composition_annotated$annotation_joined %in% TRUE) &&
    all(phase11_nonempty(composition_annotated$mapping_status)) &&
    all(phase11_nonempty(composition_annotated$mito_tier))
  phase11_must(
    composition_annotation_exact,
    "Composition results did not join exactly to the broad-cell annotation authority"
  )
  composition_annotated[, annotation_joined := NULL]
  composition_core <- composition_annotated[
    mito_tier == config$analysis$primary_mito_tier
  ]
  phase11_must(
    nrow(composition_core) ==
      as.integer(config$expected$composition_core_mito_rows) &&
      all(phase11_nonempty(composition_core$symbol_hgnc_current)),
    "Composition core-mito annotation or row count changed"
  )
  composition_manifest <- merge(
    contrast_manifest,
    sensitivity_status[, .(
      contrast_id,
      sensitivity_terminal_status = terminal_status,
      composition_pcs,
      sensitivity_genes_returned = genes_returned,
      sensitivity_message = message
    )],
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  composition_manifest[, analysis_status := data.table::fcase(
    sensitivity_terminal_status == "validated_complete",
    "validated_complete",
    sensitivity_terminal_status == "not_applicable",
    "not_applicable_single_fine_type",
    sensitivity_terminal_status == "not_estimable",
    "contrast_not_estimable",
    default = NA_character_
  )]
  phase11_must(
    all(phase11_nonempty(composition_manifest$analysis_status)),
    "Composition analysis status mapping is incomplete"
  )
  setorder(composition_manifest, manifest_row)
  composition_ranks <- build_rank_bundle(
    composition_core, composition_manifest, "composition_adjusted",
    config$schemas$composition_rank_manifest,
    config$schemas$composition_ranked_genes,
    negative_f_tolerance = as.numeric(
      config$analysis$negative_f_tolerance
    )
  )
  composition_complete <- phase11_run_gsea_collection(
    composition_ranks$manifest, composition_ranks$genes,
    program_manifest, program_membership,
    "mitocarta_complete_149", config,
    config$schemas$composition_gsea, "composition_adjusted"
  )
  composition_legacy <- phase11_run_gsea_collection(
    composition_ranks$manifest, composition_ranks$genes,
    program_manifest, program_membership,
    "legacy_four", config,
    config$schemas$composition_gsea, "composition_adjusted"
  )
  composition_broad <- phase11_derive_broad_gsea(
    composition_complete, program_manifest,
    config$schemas$composition_gsea
  )
  composition_gsea <- phase11_finalize_gsea(
    rbindlist(
      list(composition_legacy, composition_broad, composition_complete),
      use.names = TRUE, fill = TRUE
    ),
    config
  )

  composition_concordance <- build_composition_concordance(
    primary_gsea, composition_gsea, sensitivity_summary,
    config$schemas$composition_concordance
  )
  broad_cell_summary <- build_summary(
    primary_gsea, composition_gsea, ora,
    "broad_cell_type", config$schemas$broad_cell_summary
  )
  sex_apoe_summary <- build_summary(
    primary_gsea, composition_gsea, ora,
    "sex_apoe", config$schemas$sex_apoe_summary
  )
  broad_vs_fine <- build_broad_vs_fine(
    ora, fine_ora, config$schemas$broad_vs_fine
  )
  redundancy_map <- phase11_compute_redundancy_map(
    program_manifest, program_membership,
    config$schemas$redundancy_map,
    threshold = as.numeric(
      config$redundancy$representative_jaccard_threshold
    )
  )

  fixed_reference_paths <- c(
    phase08_broad_status = paths$broad_status,
    phase08_broad_checks = paths$broad_checks,
    phase08_broad_artifacts = paths$broad_artifacts,
    phase08_broad_config_snapshot = paths$broad_config_snapshot,
    phase08_broad_contrast_manifest = paths$broad_manifest,
    phase08_broad_contrast_status = paths$broad_contrast_status,
    phase08_broad_model_diagnostics = paths$broad_model_diagnostics,
    phase08_broad_filter_funnel = paths$broad_filter_funnel,
    phase08_broad_results = paths$broad_results,
    phase08_composition_results = paths$composition_results,
    phase08_composition_status = paths$composition_status,
    phase08_composition_summary = paths$composition_summary,
    phase08_composition_checks = paths$composition_checks,
    phase09_status = paths$phase09_status,
    phase09_checks = paths$phase09_checks,
    phase09_artifacts = paths$phase09_artifacts,
    phase09_annotation_master = paths$phase09_master,
    phase11_similarity_status = paths$phase11_status,
    phase11_similarity_artifacts = paths$phase11_artifacts,
    phase11_reference_manifest = paths$phase11_reference,
    phase11_pathway_membership = paths$phase11_membership,
    phase11_fine_status = paths$fine_status,
    phase11_fine_artifacts = paths$fine_artifacts,
    phase11_fine_reference_manifest = paths$fine_reference,
    phase11_fine_program_manifest = paths$fine_program,
    phase11_fine_ora = paths$fine_ora,
    legacy_four_modules = paths$legacy,
    mitocarta_source = paths$mitocarta
  )
  fixed_reference_roles <- c(
    rep("broad_deg_release_contract", 9L),
    rep("composition_sensitivity_contract", 4L),
    rep("gene_identity_authority", 4L),
    rep("normalized_pathway_reference", 4L),
    rep("fine_resolution_comparison_contract", 5L),
    "legacy_compatibility_programs",
    "mitocarta_reference_authority"
  )
  reference_sources <- rbindlist(list(
    data.table::data.table(
      input_id = names(fixed_reference_paths),
      role = unname(fixed_reference_roles),
      path = unname(fixed_reference_paths)
    ),
    data.table::data.table(
      input_id = paste0(
        "phase08_physical_slice__", physical_expected$artifact
      ),
      role = "physical_broad_deg_slice",
      path = physical_expected$expected_path
    )
  ))
  phase11_must(
    nrow(reference_sources) ==
      as.integer(config$expected$reference_inputs) &&
      !anyDuplicated(reference_sources$input_id) &&
      !anyDuplicated(reference_sources$path),
    "Reference source set is incomplete or duplicated"
  )
  reference_manifest <- reference_sources[, .(
    schema_version = config$schemas$reference_manifest,
    input_id,
    role,
    path = phase11_relative_path(path, project_root),
    bytes = as.numeric(file.info(path)$size),
    sha256 = vapply(path, phase11_sha256_file, character(1)),
    validation_status = "validated_input"
  )]

  check_rows <- list()
  add_check <- function(check, passed, observed, expected, detail = "") {
    check_rows[[length(check_rows) + 1L]] <<- data.table::data.table(
      schema_version = config$schemas$checks,
      check = check,
      passed = isTRUE(passed),
      observed = as.character(observed),
      expected = as.character(expected),
      detail = as.character(detail)
    )
  }
  add_check(
    "broad_release_validated",
    broad_status$validation_status[[1L]] == "validated_complete",
    broad_status$validation_status[[1L]], "validated_complete"
  )
  add_check(
    "broad_release_provenance_hashes",
    broad_provenance_hashes_exact,
    broad_provenance_hashes_exact, TRUE
  )
  add_check(
    "reference_input_count",
    nrow(reference_manifest) ==
      as.integer(config$expected$reference_inputs),
    nrow(reference_manifest), config$expected$reference_inputs
  )
  add_check(
    "planned_contrast_count",
    nrow(contrast_manifest) == as.integer(config$expected$planned_contrasts),
    nrow(contrast_manifest), config$expected$planned_contrasts
  )
  add_check(
    "completed_contrast_count",
    sum(contrast_manifest$analysis_status == "validated_complete") ==
      as.integer(config$expected$completed_contrasts),
    sum(contrast_manifest$analysis_status == "validated_complete"),
    config$expected$completed_contrasts
  )
  add_check(
    "nonestimable_contrast_count",
    sum(contrast_manifest$analysis_status == "contrast_not_estimable") ==
      as.integer(config$expected$nonestimable_contrasts),
    sum(contrast_manifest$analysis_status == "contrast_not_estimable"),
    config$expected$nonestimable_contrasts
  )
  add_check(
    "broad_result_row_count",
    nrow(results) == as.integer(config$expected$broad_result_rows),
    nrow(results), config$expected$broad_result_rows
  )
  add_check(
    "physical_slices_reconstruct_combined_results",
    physical_reconstruction_exact,
    physical_reconstruction_exact, TRUE,
    "Every downstream-consumed DEG column compared at tolerance zero"
  )
  add_check(
    "deg_direction_labels_match_logfc",
    direction_labels_exact, direction_labels_exact, TRUE
  )
  add_check(
    "strict_deg_flags_reproduced", strict_exact, strict_exact, TRUE
  )
  add_check(
    "relaxed_deg_flags_reproduced", relaxed_exact, relaxed_exact, TRUE
  )
  add_check(
    "exploratory_deg_flags_reproduced",
    exploratory_exact, exploratory_exact, TRUE
  )
  add_check(
    "core_mito_rows",
    nrow(core) == as.integer(config$expected$primary_core_mito_rows),
    nrow(core), config$expected$primary_core_mito_rows
  )
  add_check(
    "core_mito_unique_symbols",
    uniqueN(core$symbol_hgnc_current) ==
      as.integer(config$expected$primary_core_mito_symbols),
    uniqueN(core$symbol_hgnc_current),
    config$expected$primary_core_mito_symbols
  )
  add_check(
    "core_mito_symbols_in_phase09_authority",
    broad_symbols_in_phase09, broad_symbols_in_phase09, TRUE
  )
  add_check(
    "mitocarta_exact_reconciliation",
    mitocarta_reconciles, mitocarta_reconciles, TRUE
  )
  add_check(
    "fine_program_manifest_reconciles",
    fine_program_manifest_reconciles,
    fine_program_manifest_reconciles, TRUE
  )
  collection_counts <- program_manifest[, .N, by = pathway_collection]
  for (collection in names(config$collections)) {
    expected_count <- as.integer(
      config$collections[[collection]]$expected_programs
    )
    observed_count <- collection_counts[
      pathway_collection == collection, N
    ]
    add_check(
      paste0("program_count_", collection),
      length(observed_count) == 1L && observed_count == expected_count,
      if (length(observed_count)) observed_count else 0L,
      expected_count
    )
  }
  background_sizes <- unique(backgrounds$manifest[, .(
    broad_cell_type, background_size
  )])
  background_expected <- unlist(
    config$expected$primary_background_sizes, use.names = TRUE
  )
  background_observed <- background_sizes$background_size[
    match(names(background_expected), background_sizes$broad_cell_type)
  ]
  add_check(
    "background_sizes_exact",
    identical(
      as.integer(background_observed), as.integer(background_expected)
    ),
    paste(background_observed, collapse = ","),
    paste(background_expected, collapse = ",")
  )
  add_check(
    "primary_rank_manifest_rows",
    nrow(primary_ranks$manifest) ==
      as.integer(config$expected$primary_rank_definitions),
    nrow(primary_ranks$manifest), config$expected$primary_rank_definitions
  )
  add_check(
    "primary_rank_gene_rows",
    nrow(primary_ranks$genes) ==
      as.integer(config$expected$primary_core_mito_rows),
    nrow(primary_ranks$genes), config$expected$primary_core_mito_rows
  )
  add_check(
    "primary_tiny_negative_f_clamped",
    sum(primary_ranks$manifest$tiny_negative_f_clamped) ==
      as.integer(config$expected$primary_tiny_negative_f_clamped) &&
      sum(primary_ranks$manifest$materially_negative_f) == 0L,
    sum(primary_ranks$manifest$tiny_negative_f_clamped),
    config$expected$primary_tiny_negative_f_clamped,
    paste0(
      "Tolerance=", config$analysis$negative_f_tolerance,
      "; materially_negative=0"
    )
  )
  add_check(
    "ora_query_definition_rows",
    nrow(queries$manifest) ==
      as.integer(config$expected$ora_query_definitions),
    nrow(queries$manifest), config$expected$ora_query_definitions
  )
  for (tier in names(config$expected$testable_query_slots)) {
    for (mode in names(config$expected$testable_query_slots[[tier]])) {
      observed <- queries$manifest[
        deg_tier == tier & query_mode == mode &
          structurally_available & query_size >=
            as.integer(config$analysis$minimum_query_size),
        .N
      ]
      expected <- as.integer(
        config$expected$testable_query_slots[[tier]][[mode]]
      )
      add_check(
        paste("eligible_query_slots", tier, mode, sep = "_"),
        observed == expected, observed, expected
      )
    }
  }
  add_check(
    "primary_gsea_grid_rows",
    nrow(primary_gsea) == as.integer(config$expected$primary_gsea_rows),
    nrow(primary_gsea), config$expected$primary_gsea_rows
  )
  add_check(
    "primary_gsea_probabilities_valid",
    all(primary_gsea[
      test_status == "tested",
      is.finite(p_value) & p_value >= 0 & p_value <= 1 &
        is.finite(normalized_enrichment_score)
    ]),
    sum(primary_gsea$test_status == "tested"), "all tested rows valid"
  )
  primary_reuse <- merge(
    primary_gsea[pathway_collection == "mitocarta_broad_46", .(
      contrast_id, pathway_id, broad_es = enrichment_score,
      broad_nes = normalized_enrichment_score, broad_p = p_value,
      broad_le = leading_edge_genes
    )],
    primary_gsea[pathway_collection == "mitocarta_complete_149", .(
      contrast_id, pathway_id, complete_es = enrichment_score,
      complete_nes = normalized_enrichment_score, complete_p = p_value,
      complete_le = leading_edge_genes
    )],
    by = c("contrast_id", "pathway_id")
  )
  raw_gsea_reused <- isTRUE(all.equal(
    primary_reuse[, .(broad_es, broad_nes, broad_p, broad_le)],
    primary_reuse[, .(
      broad_es = complete_es, broad_nes = complete_nes,
      broad_p = complete_p, broad_le = complete_le
    )],
    check.attributes = FALSE, tolerance = 0
  ))
  add_check(
    "broad46_raw_gsea_reused_from_complete149",
    raw_gsea_reused, raw_gsea_reused, TRUE
  )
  add_check(
    "ora_grid_rows",
    nrow(ora) == as.integer(config$expected$primary_ora_rows),
    nrow(ora), config$expected$primary_ora_rows
  )
  add_check(
    "ora_probabilities_valid",
    all(ora[
      test_status == "tested",
      is.finite(p_value) & p_value >= 0 & p_value <= 1
    ]),
    sum(ora$test_status == "tested"), "all tested rows valid"
  )
  add_check(
    "hypergeometric_toy_case",
    isTRUE(all.equal(
      phase11_ora_probability(3L, 10L, 100L, 5L),
      phyper(2L, 10L, 90L, 5L, lower.tail = FALSE),
      tolerance = 0
    )),
    phase11_ora_probability(3L, 10L, 100L, 5L),
    phyper(2L, 10L, 90L, 5L, lower.tail = FALSE)
  )
  add_check(
    "composition_rank_manifest_rows",
    nrow(composition_ranks$manifest) ==
      as.integer(config$expected$composition_rank_definitions),
    nrow(composition_ranks$manifest),
    config$expected$composition_rank_definitions
  )
  add_check(
    "composition_annotation_join_exact",
    composition_annotation_exact, composition_annotation_exact, TRUE
  )
  composition_status_counts <- composition_ranks$manifest[, .N, by = rank_status]
  count_status <- function(status) {
    value <- composition_status_counts[rank_status == status, N]
    if (length(value)) value else 0L
  }
  add_check(
    "composition_completed_contrasts",
    count_status("available") ==
      as.integer(config$expected$composition_completed_contrasts),
    count_status("available"),
    config$expected$composition_completed_contrasts
  )
  add_check(
    "composition_not_applicable_contrasts",
    count_status("not_applicable_single_fine_type") ==
      as.integer(config$expected$composition_not_applicable_contrasts),
    count_status("not_applicable_single_fine_type"),
    config$expected$composition_not_applicable_contrasts
  )
  add_check(
    "composition_nonestimable_contrasts",
    count_status("contrast_not_estimable") ==
      as.integer(config$expected$composition_nonestimable_contrasts),
    count_status("contrast_not_estimable"),
    config$expected$composition_nonestimable_contrasts
  )
  add_check(
    "composition_rank_gene_rows",
    nrow(composition_ranks$genes) ==
      as.integer(config$expected$composition_core_mito_rows),
    nrow(composition_ranks$genes),
    config$expected$composition_core_mito_rows
  )
  add_check(
    "composition_tiny_negative_f_clamped",
    sum(composition_ranks$manifest$tiny_negative_f_clamped) ==
      as.integer(config$expected$composition_tiny_negative_f_clamped) &&
      sum(composition_ranks$manifest$materially_negative_f) == 0L,
    sum(composition_ranks$manifest$tiny_negative_f_clamped),
    config$expected$composition_tiny_negative_f_clamped,
    paste0(
      "Tolerance=", config$analysis$negative_f_tolerance,
      "; materially_negative=0"
    )
  )
  add_check(
    "composition_gsea_grid_rows",
    nrow(composition_gsea) ==
      as.integer(config$expected$composition_gsea_rows),
    nrow(composition_gsea), config$expected$composition_gsea_rows
  )
  add_check(
    "composition_concordance_rows",
    nrow(composition_concordance) ==
      as.integer(config$expected$composition_gsea_rows),
    nrow(composition_concordance), config$expected$composition_gsea_rows
  )
  add_check(
    "broad_vs_fine_rows",
    nrow(broad_vs_fine) == as.integer(config$expected$broad_vs_fine_rows),
    nrow(broad_vs_fine), config$expected$broad_vs_fine_rows
  )
  allowed_resolution_categories <- c(
    "concordant_support", "broad_only", "fine_only", "neither",
    "not_comparable"
  )
  resolution_categories_valid <-
    all(broad_vs_fine$resolution_concordance %in%
      allowed_resolution_categories) &&
    all(
      (broad_vs_fine$resolution_concordance == "not_comparable") ==
        (!broad_vs_fine$broad_resolution_testable |
          !broad_vs_fine$fine_resolution_testable)
    )
  add_check(
    "broad_vs_fine_categories_valid",
    resolution_categories_valid,
    paste(
      sort(unique(broad_vs_fine$resolution_concordance)),
      collapse = ","
    ),
    paste(allowed_resolution_categories, collapse = ",")
  )
  add_check(
    "redundancy_pair_rows",
    nrow(redundancy_map) == as.integer(config$expected$redundancy_pairs),
    nrow(redundancy_map), config$expected$redundancy_pairs
  )
  add_check(
    "structural_unavailable_records_preserved",
    all(primary_gsea[
      structurally_available == FALSE,
      test_status == "not_testable" &
        testability_reason == "contrast_not_estimable"
    ]) &&
      all(ora[
        structurally_available == FALSE,
        test_status == "not_testable" &
          testability_reason == "contrast_not_estimable"
      ]),
    sum(!primary_gsea$structurally_available), "all explicit and not tested"
  )
  checks <- rbindlist(check_rows)
  phase11_must(
    all(checks$passed),
    paste(
      "Broad-DEG pathway validation failed:",
      paste(checks[passed == FALSE, check], collapse = ", ")
    )
  )

  significant_gsea <- primary_gsea[local_fdr_significant %in% TRUE]
  significant_ora <- ora[local_fdr_significant %in% TRUE]
  significant_gsea[, schema_version := config$schemas$significant_gsea]
  significant_ora[, schema_version := config$schemas$significant_ora]
  tier_roles <- vapply(
    config$analysis$deg_tiers,
    function(x) as.character(x$role),
    character(1)
  )
  significant_ora[, evidence_role := unname(tier_roles[deg_tier])]

  readme_lines <- c(
    "# Broad-cell DEG mitochondrial pathway analysis",
    "",
    "Validated Phase 11 release using ROSMAP donor-level broad-cell DEGs.",
    "",
    paste0(
      "- Primary analysis: preranked GSEA over ", nrow(primary_ranks$manifest),
      " structural contrasts (", sum(primary_ranks$manifest$structurally_available),
      " estimable)."
    ),
    paste0(
      "- GSEA rank: `sign(logFC) * sqrt(F)` over tested core-mito genes."
    ),
    paste0(
      "- Threshold companion: ORA over strict, relaxed, and exploratory tiers."
    ),
    paste0(
      "- Program collections: legacy 4, broad MitoCarta 46, complete MitoCarta 149."
    ),
    paste0(
      "- Composition sensitivity: ", sum(
        composition_ranks$manifest$structurally_available
      ), " estimable ranks."
    ),
    paste0(
      "- Local significance: BH FDR < ", config$fdr$threshold,
      " within the frozen local family."
    ),
    "",
    "Positive GSEA NES means genes tend toward the AD-up end; negative NES",
    "means genes tend toward the AD-down end. NES is coordinated expression,",
    "not direct evidence of pathway activity. Relaxed and exploratory ORA are",
    "sensitivity and hypothesis-generating evidence, not confirmatory results.",
    "",
    "The complete GSEA and ORA grids are authoritative. Significant-only files",
    "are convenience subsets. Broad-versus-fine recurrence is descriptive",
    "because strata and cell classes can share donors."
  )

  output_objects <- list(
    broad_deg_pathway_reference_manifest.tsv = reference_manifest,
    broad_deg_pathway_program_manifest.tsv = program_manifest,
    broad_deg_pathway_contrast_manifest.tsv = contrast_manifest,
    broad_deg_pathway_rank_manifest.tsv = primary_ranks$manifest,
    broad_deg_pathway_ranked_genes.tsv.gz = primary_ranks$genes,
    broad_deg_pathway_gsea.tsv.gz = primary_gsea,
    broad_deg_pathway_significant_gsea.tsv.gz = significant_gsea,
    broad_deg_pathway_background_manifest.tsv = backgrounds$manifest,
    broad_deg_pathway_background_genes.tsv.gz = backgrounds$genes,
    broad_deg_pathway_ora_query_manifest.tsv = queries$manifest,
    broad_deg_pathway_ora_query_genes.tsv.gz = queries$genes,
    broad_deg_pathway_ora.tsv.gz = ora,
    broad_deg_pathway_significant_ora.tsv.gz = significant_ora,
    broad_deg_pathway_composition_rank_manifest.tsv =
      composition_ranks$manifest,
    broad_deg_pathway_composition_ranked_genes.tsv.gz =
      composition_ranks$genes,
    broad_deg_pathway_composition_gsea.tsv.gz = composition_gsea,
    broad_deg_pathway_composition_concordance.tsv =
      composition_concordance,
    broad_deg_pathway_broad_cell_summary.tsv = broad_cell_summary,
    broad_deg_pathway_sex_apoe_summary.tsv = sex_apoe_summary,
    broad_deg_pathway_broad_vs_fine_concordance.tsv.gz = broad_vs_fine,
    broad_deg_pathway_redundancy_map.tsv.gz = redundancy_map
  )
  for (name in names(output_objects)) {
    phase11_atomic_fwrite(
      output_objects[[name]], file.path(staging_root, name)
    )
  }
  phase11_atomic_fwrite(
    checks, file.path(staging_root, "broad_deg_pathway_checks.tsv")
  )
  phase11_atomic_write_lines(readme_lines, file.path(staging_root, "README.md"))

  output_schemas <- broad_output_schema_map(config)
  record_counts <- c(
    broad_deg_pathway_checks.tsv = nrow(checks),
    vapply(output_objects, nrow, integer(1)),
    README.md = length(readme_lines)
  )
  artifact_names <- names(output_schemas)
  artifacts <- rbindlist(lapply(artifact_names, function(name) {
    staged_path <- file.path(staging_root, name)
    data.table(
      schema_version = config$schemas$artifacts,
      artifact = name,
      path = phase11_relative_path(file.path(final_root, name), project_root),
      bytes = as.numeric(file.info(staged_path)$size),
      sha256 = phase11_sha256_file(staged_path),
      records = as.integer(record_counts[[name]]),
      output_schema = unname(output_schemas[[name]]),
      validation_status = "validated_complete"
    )
  }))
  phase11_must(
    nrow(artifacts) == as.integer(config$expected$output_artifacts) &&
      !anyDuplicated(artifacts$artifact) &&
      !anyDuplicated(artifacts$path) &&
      identical(artifacts$artifact, artifact_names) &&
      identical(
        artifacts$path,
        unname(phase11_relative_path(
          file.path(final_root, artifact_names), project_root
        ))
      ) &&
      identical(artifacts$output_schema, unname(output_schemas)) &&
      identical(
        as.integer(artifacts$records),
        as.integer(record_counts[artifact_names])
      ),
    "Output artifact manifest is incomplete or not path-bound"
  )
  phase11_atomic_fwrite(
    artifacts, file.path(staging_root, "broad_deg_pathway_artifacts.tsv")
  )
  artifacts_manifest_hash <- phase11_sha256_file(
    file.path(staging_root, "broad_deg_pathway_artifacts.tsv")
  )

  elapsed <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
  status <- data.table(
    schema_version = config$schemas$status,
    execution_stage = execution_stage,
    execution_phase = as.integer(execution$execution_phase %||% NA_integer_),
    backend = as.character(execution$backend %||% "direct"),
    run_id = as.character(execution$run_id %||% NA_character_),
    stable_task_id = "global:pathway_deg_broad",
    task_mode = "pathway_deg_broad",
    scientific_script = phase11_relative_path(script_path, project_root),
    scientific_script_sha256 = script_hash,
    common_library_sha256 = common_hash,
    scientific_config_sha256 = config_hash,
    artifacts_manifest_sha256 = artifacts_manifest_hash,
    pipeline_config_sha256 = phase11_sha256_file(pipeline_config_path),
    execution_config_sha256 = phase11_sha256_file(execution_config_path),
    broad_results_sha256 = phase11_sha256_file(paths$broad_results),
    composition_results_sha256 =
      phase11_sha256_file(paths$composition_results),
    phase09_master_sha256 = phase11_sha256_file(paths$phase09_master),
    phase11_membership_sha256 =
      phase11_sha256_file(paths$phase11_membership),
    fine_ora_sha256 = phase11_sha256_file(paths$fine_ora),
    mitocarta_source_sha256 = phase11_sha256_file(paths$mitocarta),
    planned_contrasts = nrow(contrast_manifest),
    estimable_contrasts = sum(
      contrast_manifest$analysis_status == "validated_complete"
    ),
    nonestimable_contrasts = sum(
      contrast_manifest$analysis_status == "contrast_not_estimable"
    ),
    primary_rank_rows = nrow(primary_ranks$genes),
    query_definitions = nrow(queries$manifest),
    pathway_definitions = nrow(program_manifest),
    primary_gsea_rows = nrow(primary_gsea),
    tested_primary_gsea_rows = sum(primary_gsea$test_status == "tested"),
    significant_primary_gsea_rows = nrow(significant_gsea),
    ora_rows = nrow(ora),
    tested_ora_rows = sum(ora$test_status == "tested"),
    significant_ora_rows = nrow(significant_ora),
    composition_gsea_rows = nrow(composition_gsea),
    composition_tested_gsea_rows =
      sum(composition_gsea$test_status == "tested"),
    broad_vs_fine_rows = nrow(broad_vs_fine),
    reference_inputs = nrow(reference_manifest),
    output_artifacts = nrow(artifacts),
    blocking_checks = nrow(checks),
    readme_lines = length(readme_lines),
    failed_checks = sum(!checks$passed),
    R_version = as.character(getRversion()),
    data_table_version = as.character(packageVersion("data.table")),
    fgsea_version = as.character(packageVersion("fgsea")),
    yaml_version = as.character(packageVersion("yaml")),
    digest_version = as.character(packageVersion("digest")),
    readxl_version = as.character(packageVersion("readxl")),
    elapsed_seconds = elapsed,
    validation_status = "validated_complete",
    git_revision = phase11_git_revision(project_root),
    timestamp_utc = format(
      Sys.time(), tz = "UTC", format = "%Y-%m-%d %H:%M:%S UTC"
    )
  )
  phase11_atomic_fwrite(
    status, file.path(staging_root, "broad_deg_pathway_status.tsv")
  )

  staged_artifacts <- fread(
    file.path(staging_root, "broad_deg_pathway_artifacts.tsv")
  )
  staged_valid <- all(vapply(seq_len(nrow(staged_artifacts)), function(i) {
    staged_path <- file.path(
      staging_root, basename(staged_artifacts$path[[i]])
    )
    file.exists(staged_path) &&
      identical(
        phase11_sha256_file(staged_path),
        staged_artifacts$sha256[[i]]
      ) &&
      as.numeric(file.info(staged_path)$size) ==
        as.numeric(staged_artifacts$bytes[[i]])
  }, logical(1)))
  phase11_must(
    staged_valid, "A staged output artifact failed final hash validation"
  )
  phase11_must(!dir.exists(final_root), "Final output appeared during staging")
  if (!file.rename(staging_root, final_root)) {
    stop("Could not atomically publish output bundle", call. = FALSE)
  }
  on.exit(NULL, add = FALSE)
  cat(
    "Broad-DEG pathway analysis validated and published: ",
    final_root, "\n", sep = ""
  )
  invisible(final_root)
}

if (sys.nframe() == 0L) {
  run_analysis()
}
