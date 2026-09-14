# Shared release, pathway-reference, and summary helpers for SEA-AD VH15.

options(stringsAsFactors = FALSE, warn = 1)

source(
  file.path(getwd(), "scripts/lib/phase11_deg_pathway_common.R"),
  local = globalenv()
)

seaad15_parse_cli <- function(args = commandArgs(trailingOnly = TRUE)) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript SCRIPT --config FILE\n")
      quit(status = 0L)
    }
    if (key != "--config" || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  phase11_must(phase11_nonempty(out$config), "--config is required")
  out
}

seaad15_load_config <- function(path, expected_schema, resolution) {
  for (package in c("data.table", "yaml", "digest", "readxl")) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Package '", package, "' is required", call. = FALSE)
    }
  }
  project_root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- phase11_absolute_path(path, project_root)
  phase11_must(file.exists(config_path), "VH15 config does not exist")
  config <- yaml::read_yaml(config_path)
  phase11_must(
    identical(config$schema_version, expected_schema),
    "Unexpected VH15 config schema"
  )
  phase11_must(
    identical(config$analysis_resolution, resolution),
    "VH15 config resolution does not match the runner"
  )
  list(
    config = config,
    config_path = config_path,
    project_root = project_root
  )
}

seaad15_read <- function(path, ...) {
  data.table::fread(path, showProgress = FALSE, ...)
}

seaad15_validate_artifact_rows <- function(artifacts, project_root) {
  required <- c("path", "bytes")
  phase11_must(
    all(required %in% names(artifacts)),
    "Artifact manifest lacks required columns"
  )
  digest_column <- if ("digest_value" %in% names(artifacts)) {
    "digest_value"
  } else if ("sha256" %in% names(artifacts)) {
    "sha256"
  } else {
    stop("Artifact manifest has no SHA-256 column", call. = FALSE)
  }
  valid <- vapply(seq_len(nrow(artifacts)), function(i) {
    path <- phase11_absolute_path(artifacts$path[[i]], project_root)
    file.exists(path) &&
      as.numeric(file.info(path)$size) == as.numeric(artifacts$bytes[[i]]) &&
      identical(
        phase11_sha256_file(path),
        as.character(artifacts[[digest_column]][[i]])
      )
  }, logical(1))
  phase11_must(all(valid), "An upstream artifact failed SHA-256 validation")
  invisible(TRUE)
}

seaad15_validate_release <- function(
    root, project_root, status_schema, phase, release_scope = NULL) {
  status_path <- file.path(root, "status.tsv")
  artifacts_path <- file.path(root, "artifacts.tsv")
  phase11_must(
    file.exists(status_path) && file.exists(artifacts_path),
    paste("Validated release records are missing under", root)
  )
  status <- seaad15_read(status_path)
  artifacts <- seaad15_read(artifacts_path)
  phase11_must(
    nrow(status) == 1L &&
      identical(status$schema_version[[1L]], status_schema) &&
      identical(status$phase[[1L]], phase) &&
      identical(status$validation_status[[1L]], "validated_complete"),
    paste("Upstream release is not validated_complete:", root)
  )
  if (!is.null(release_scope)) {
    phase11_must(
      identical(status$release_scope[[1L]], release_scope),
      paste("Unexpected upstream release scope:", root)
    )
  }
  if ("artifact_manifest_sha256" %in% names(status)) {
    phase11_must(
      identical(
        status$artifact_manifest_sha256[[1L]],
        phase11_sha256_file(artifacts_path)
      ),
      paste("Upstream artifact-manifest hash differs:", root)
    )
  }
  phase11_must(
    !anyDuplicated(artifacts$path),
    paste("Upstream artifact paths are duplicated:", root)
  )
  seaad15_validate_artifact_rows(artifacts, project_root)
  list(
    status = status,
    artifacts = artifacts,
    status_path = status_path,
    artifacts_path = artifacts_path
  )
}

seaad15_validate_simple_bundle <- function(
    root, project_root, status_schema, phase) {
  seaad15_validate_release(
    root, project_root, status_schema, phase, release_scope = NULL
  )
}

seaad15_assert_file_hash <- function(path, expected_sha256, label) {
  phase11_must(file.exists(path), paste(label, "does not exist:", path))
  phase11_must(
    identical(phase11_sha256_file(path), as.character(expected_sha256)),
    paste(label, "failed SHA-256 validation:", path)
  )
  invisible(TRUE)
}

seaad15_code_bundle_sha <- function(paths, project_root) {
  normalized <- sort(unique(normalizePath(paths, mustWork = TRUE)))
  payload <- paste(
    paste0(
      phase11_relative_path(normalized, project_root), "=",
      vapply(normalized, phase11_sha256_file, character(1))
    ),
    collapse = "\n"
  )
  digest::digest(payload, algo = "sha256", serialize = FALSE)
}

seaad15_make_reference_manifest <- function(paths, schema, project_root) {
  phase11_must(
    length(paths) == length(unique(names(paths))) &&
      all(phase11_nonempty(names(paths))),
    "Reference roles must be uniquely named"
  )
  normalized <- normalizePath(unname(paths), mustWork = TRUE)
  phase11_must(
    !anyDuplicated(normalized),
    "Reference manifest contains duplicate physical files"
  )
  result <- data.table::data.table(
    schema_version = schema,
    input_order = seq_along(paths),
    input_role = names(paths),
    path = phase11_relative_path(normalized, project_root),
    bytes = as.numeric(file.info(normalized)$size),
    sha256 = vapply(normalized, phase11_sha256_file, character(1)),
    validation_status = "validated_input"
  )
  result
}

seaad15_reference_files_match <- function(references, project_root) {
  if (!all(c("path", "bytes", "sha256") %in% names(references))) return(FALSE)
  all(vapply(seq_len(nrow(references)), function(i) {
    path <- phase11_absolute_path(references$path[[i]], project_root)
    file.exists(path) &&
      as.numeric(file.info(path)$size) == as.numeric(references$bytes[[i]]) &&
      identical(phase11_sha256_file(path), references$sha256[[i]])
  }, logical(1)))
}

seaad15_valid_existing <- function(
    final_root, prefix, config, config_path, code_paths, project_root) {
  status_path <- file.path(final_root, paste0(prefix, "_status.tsv"))
  artifacts_path <- file.path(final_root, paste0(prefix, "_artifacts.tsv"))
  reference_path <- file.path(
    final_root, paste0(prefix, "_reference_manifest.tsv")
  )
  if (!all(file.exists(c(status_path, artifacts_path, reference_path)))) {
    return(FALSE)
  }
  status <- tryCatch(seaad15_read(status_path), error = function(e) NULL)
  artifacts <- tryCatch(seaad15_read(artifacts_path), error = function(e) NULL)
  references <- tryCatch(seaad15_read(reference_path), error = function(e) NULL)
  if (is.null(status) || is.null(artifacts) || is.null(references) ||
      nrow(status) != 1L) {
    return(FALSE)
  }
  if (!phase11_schema_ok(status, config$schemas$status) ||
      !phase11_schema_ok(artifacts, config$schemas$artifacts) ||
      !phase11_schema_ok(references, config$schemas$reference_manifest)) {
    return(FALSE)
  }
  expected_bundle <- seaad15_code_bundle_sha(code_paths, project_root)
  if (!identical(status$validation_status[[1L]], "validated_complete") ||
      !identical(
        status$scientific_config_sha256[[1L]],
        phase11_sha256_file(config_path)
      ) ||
      !identical(status$code_bundle_sha256[[1L]], expected_bundle) ||
      !identical(
        status$artifacts_manifest_sha256[[1L]],
        phase11_sha256_file(artifacts_path)
      )) {
    return(FALSE)
  }
  output_valid <- all(vapply(seq_len(nrow(artifacts)), function(i) {
    phase11_artifact_valid(artifacts[i], project_root)
  }, logical(1)))
  output_valid && seaad15_reference_files_match(references, project_root)
}

seaad15_build_programs <- function(config, project_root) {
  legacy_path <- phase11_absolute_path(
    config$inputs$legacy_module_membership, project_root
  )
  mitocarta_path <- phase11_absolute_path(
    config$inputs$mitocarta_source, project_root
  )
  phase11_must(
    identical(
      phase11_sha256_file(mitocarta_path),
      as.character(config$references$mitocarta$source_sha256)
    ),
    "MitoCarta source differs from the frozen SHA-256"
  )
  legacy <- seaad15_read(legacy_path)
  parsed <- phase11_parse_mitocarta_source(mitocarta_path)
  programs <- phase11_build_program_collections(
    legacy, parsed, config
  )
  counts <- programs$metadata[, .N, by = pathway_collection]
  expected <- c(
    legacy_four = as.integer(config$expected$legacy_modules),
    mitocarta_broad_46 =
      as.integer(config$expected$broad_mitocarta_pathways),
    mitocarta_complete_149 =
      as.integer(config$expected$complete_mitocarta_pathways)
  )
  observed <- counts$N[match(names(expected), counts$pathway_collection)]
  phase11_must(
    identical(as.integer(observed), unname(expected)) &&
      nrow(programs$metadata) ==
        as.integer(config$expected$pathway_definitions),
    "Pathway-program counts differ from the frozen contract"
  )
  programs
}

seaad15_checks <- function(rows, schema) {
  result <- data.table::rbindlist(lapply(rows, function(row) {
    data.table::data.table(
      check = as.character(row[[1L]]),
      passed = isTRUE(row[[2L]]),
      observed = as.character(row[[3L]]),
      expected = as.character(row[[4L]]),
      detail = as.character(row[[5L]])
    )
  }))
  result[, `:=`(
    schema_version = schema,
    blocking = TRUE,
    check_order = seq_len(.N)
  )]
  data.table::setcolorder(
    result,
    c(
      "schema_version", "check_order", "check", "blocking", "passed",
      "observed", "expected", "detail"
    )
  )
  result
}

seaad15_pvalues_reproduce <- function(ora, tolerance = 1e-14) {
  tested <- ora[test_status == "tested"]
  if (!nrow(tested)) return(TRUE)
  reproduced <- phase11_ora_probability(
    tested$overlap_count,
    tested$background_pathway_size,
    tested$background_size,
    tested$query_size
  )
  max(abs(reproduced - tested$p_value), na.rm = TRUE) <= tolerance
}

seaad15_fdr_flags_match <- function(x, threshold) {
  local <- ifelse(
    is.finite(x$local_fdr_bh), x$local_fdr_bh < threshold, FALSE
  )
  global <- ifelse(
    is.finite(x$global_fdr_bh), x$global_fdr_bh < threshold, FALSE
  )
  identical(as.logical(local), as.logical(x$local_fdr_significant)) &&
    identical(as.logical(global), as.logical(x$global_fdr_significant))
}

seaad15_gsea_fdr_reproduces <- function(gsea, tolerance = 1e-14) {
  tested <- data.table::copy(gsea[test_status == "tested"])
  if (!nrow(tested)) return(TRUE)
  tested[, expected_local := stats::p.adjust(p_value, method = "BH"),
    by = .(contrast_id, pathway_collection)]
  tested[, expected_global := stats::p.adjust(p_value, method = "BH"),
    by = .(pathway_collection)]
  max(abs(tested$expected_local - tested$local_fdr_bh), na.rm = TRUE) <=
      tolerance &&
    max(abs(tested$expected_global - tested$global_fdr_bh), na.rm = TRUE) <=
      tolerance
}

seaad15_recurrence_summary <- function(ora, by_columns, schema) {
  result <- ora[, {
    significant <- local_fdr_significant %in% TRUE
    fold <- fold_enrichment[significant & is.finite(fold_enrichment)]
    recurrence <- phase11_recurrence_fields(overlap_genes, significant)
    c(list(
      structurally_available_contrasts =
        data.table::uniqueN(contrast_id[structurally_available %in% TRUE]),
      total_contrasts = data.table::uniqueN(contrast_id),
      testable_queries = sum(test_status == "tested"),
      locally_significant_queries = sum(significant),
      globally_significant_queries =
        sum(global_fdr_significant %in% TRUE),
      significant_dementia_any_queries =
        sum(significant & query_mode == "Dementia_any_mito"),
      significant_dementia_up_queries =
        sum(significant & query_mode == "Dementia_up_mito"),
      significant_dementia_down_queries =
        sum(significant & query_mode == "Dementia_down_mito"),
      significant_fine_cell_types =
        data.table::uniqueN(fine_cell_type[significant]),
      median_significant_fold_enrichment =
        if (length(fold)) stats::median(fold) else NA_real_,
      minimum_significant_fold_enrichment =
        if (length(fold)) min(fold) else NA_real_,
      maximum_significant_fold_enrichment =
        if (length(fold)) max(fold) else NA_real_
    ), recurrence)
  }, by = by_columns]
  result[, schema_version := schema]
  data.table::setcolorder(
    result, c("schema_version", setdiff(names(result), "schema_version"))
  )
  result
}

seaad15_safe_min <- function(x) {
  x <- x[is.finite(x)]
  if (length(x)) min(x) else NA_real_
}

seaad15_safe_median <- function(x) {
  x <- x[is.finite(x)]
  if (length(x)) stats::median(x) else NA_real_
}

seaad15_broad_summary <- function(gsea, ora, group_columns, schema) {
  pathway_columns <- c(
    "pathway_collection", "collection_role", "pathway_id", "pathway_name",
    "hierarchy_depth", "level_1", "level_2"
  )
  gsea_summary <- gsea[, .(
    analysis_method = "GSEA",
    deg_tier = NA_character_,
    query_mode = NA_character_,
    total_records = .N,
    testable_records = sum(test_status == "tested"),
    locally_significant_records = sum(local_fdr_significant %in% TRUE),
    globally_significant_records = sum(global_fdr_significant %in% TRUE),
    minimum_local_fdr_bh = seaad15_safe_min(local_fdr_bh),
    median_normalized_enrichment_score =
      seaad15_safe_median(normalized_enrichment_score),
    dementia_up_records = sum(gsea_direction == "Dementia_up"),
    dementia_down_records = sum(gsea_direction == "Dementia_down"),
    maximum_fold_enrichment = NA_real_
  ), by = c(group_columns, pathway_columns)]
  ora_summary <- ora[, .(
    analysis_method = "ORA",
    total_records = .N,
    testable_records = sum(test_status == "tested"),
    locally_significant_records = sum(local_fdr_significant %in% TRUE),
    globally_significant_records = sum(global_fdr_significant %in% TRUE),
    minimum_local_fdr_bh = seaad15_safe_min(local_fdr_bh),
    median_normalized_enrichment_score = NA_real_,
    dementia_up_records = sum(
      local_fdr_significant %in% TRUE &
        query_mode == "Dementia_up_mito"
    ),
    dementia_down_records = sum(
      local_fdr_significant %in% TRUE &
        query_mode == "Dementia_down_mito"
    ),
    maximum_fold_enrichment = {
      x <- fold_enrichment[
        local_fdr_significant %in% TRUE & is.finite(fold_enrichment)
      ]
      if (length(x)) max(x) else NA_real_
    }
  ), by = c(group_columns, "deg_tier", "query_mode", pathway_columns)]
  result <- data.table::rbindlist(
    list(gsea_summary, ora_summary), use.names = TRUE, fill = TRUE
  )
  result[, schema_version := schema]
  data.table::setcolorder(
    result, c("schema_version", setdiff(names(result), "schema_version"))
  )
  result
}

seaad15_broad_vs_fine <- function(broad_ora, fine_ora, schema) {
  keys <- c(
    "broad_cell_type", "sex", "apoe_group", "query_mode",
    "pathway_collection", "pathway_id"
  )
  fine_summary <- fine_ora[, {
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
      fine_best_local_fdr_bh = seaad15_safe_min(local_fdr_bh),
      fine_maximum_fold_enrichment = {
        x <- fold_enrichment[significant & is.finite(fold_enrichment)]
        if (length(x)) max(x) else NA_real_
      },
      significant_fine_cell_types = paste(
        sort(unique(fine_cell_type[significant])), collapse = ","
      ),
      significant_fine_cell_type_count =
        data.table::uniqueN(fine_cell_type[significant]),
      fine_significant_overlap_gene_union =
        paste(overlap_union, collapse = ","),
      fine_significant_overlap_gene_union_count = length(overlap_union)
    )
  }, by = keys]
  result <- merge(
    broad_ora[deg_tier == "strict"],
    fine_summary,
    by = keys,
    all.x = TRUE,
    sort = FALSE
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
  data.table::setcolorder(
    result, c("schema_version", setdiff(names(result), "schema_version"))
  )
  data.table::setorder(
    result, query_order, collection_order, source_pathway_order
  )
  result
}

seaad15_publish <- function(
    final_root, prefix, config, config_path, code_paths, project_root,
    tables, schemas, readme_lines, status_fields) {
  phase11_must(!dir.exists(final_root), paste(
    "Output directory already exists but is not a valid resumable bundle:",
    final_root
  ))
  staging_root <- paste0(final_root, ".staging.", Sys.getpid())
  phase11_must(!dir.exists(staging_root), "VH15 staging directory exists")
  dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
  on.exit(unlink(staging_root, recursive = TRUE), add = TRUE)

  phase11_must(
    identical(sort(names(tables)), sort(names(schemas))),
    "Output table/schema maps differ"
  )
  for (name in names(tables)) {
    phase11_atomic_fwrite(tables[[name]], file.path(staging_root, name))
  }
  phase11_atomic_write_lines(
    readme_lines, file.path(staging_root, "README.md")
  )

  artifact_names <- c(names(tables), "README.md")
  artifact_schemas <- c(unlist(schemas[names(tables)]), "markdown_v1")
  artifact_records <- c(
    vapply(tables, nrow, integer(1)),
    length(readme_lines)
  )
  staged_paths <- file.path(staging_root, artifact_names)
  final_paths <- file.path(final_root, artifact_names)
  artifacts <- data.table::data.table(
    schema_version = config$schemas$artifacts,
    artifact = artifact_names,
    path = phase11_relative_path(final_paths, project_root),
    bytes = as.numeric(file.info(staged_paths)$size),
    sha256 = vapply(staged_paths, phase11_sha256_file, character(1)),
    records = as.integer(artifact_records),
    output_schema = unname(artifact_schemas),
    validation_status = "validated_complete"
  )
  artifacts_name <- paste0(prefix, "_artifacts.tsv")
  artifacts_path <- file.path(staging_root, artifacts_name)
  phase11_atomic_fwrite(artifacts, artifacts_path)

  status <- data.table::copy(status_fields)
  status[, `:=`(
    schema_version = config$schemas$status,
    phase = if (config$analysis_resolution == "fine") "VH15F" else "VH15B",
    validation_status = "validated_complete",
    failed_checks = "",
    scientific_config_sha256 = phase11_sha256_file(config_path),
    code_bundle_sha256 = seaad15_code_bundle_sha(code_paths, project_root),
    artifacts_manifest_sha256 = phase11_sha256_file(artifacts_path),
    output_artifacts = nrow(artifacts),
    git_revision = phase11_git_revision(project_root),
    completed_at_utc = format(
      Sys.time(), tz = "UTC", format = "%Y-%m-%dT%H:%M:%SZ"
    )
  )]
  data.table::setcolorder(
    status,
    c(
      "schema_version", "phase", "validation_status", "failed_checks",
      setdiff(
        names(status),
        c("schema_version", "phase", "validation_status", "failed_checks")
      )
    )
  )
  phase11_atomic_fwrite(
    status, file.path(staging_root, paste0(prefix, "_status.tsv"))
  )

  staged_valid <- all(vapply(seq_len(nrow(artifacts)), function(i) {
    path <- file.path(staging_root, artifacts$artifact[[i]])
    file.exists(path) &&
      as.numeric(file.info(path)$size) == artifacts$bytes[[i]] &&
      identical(phase11_sha256_file(path), artifacts$sha256[[i]])
  }, logical(1)))
  phase11_must(staged_valid, "A staged VH15 artifact failed validation")
  dir.create(dirname(final_root), recursive = TRUE, showWarnings = FALSE)
  phase11_must(
    file.rename(staging_root, final_root),
    "Could not atomically publish the VH15 pathway bundle"
  )
  on.exit(NULL, add = FALSE)
  invisible(final_root)
}
