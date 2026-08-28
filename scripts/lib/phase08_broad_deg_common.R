options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

phase08_abort <- function(message) stop(message, call. = FALSE)

phase08_assert <- function(value, message) {
  if (!isTRUE(value)) phase08_abort(message)
  invisible(TRUE)
}

phase08_as_logical <- function(x) {
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

phase08_absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

phase08_relative_path <- function(path, root) {
  path <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  sub(paste0("^", gsub("([][{}()+*^$|\\?.])", "\\\\\\1", root), "/?"), "", path)
}

phase08_atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) phase08_abort(paste("Could not atomically write", path))
  invisible(path)
}

phase08_atomic_write_tsv_gz <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  stem <- sub("[.]gz$", "", path)
  tmp <- paste0(stem, ".tmp.", Sys.getpid(), ".gz")
  connection <- gzfile(tmp, open = "wt", compression = 6)
  write.table(x, connection, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  close(connection)
  if (!file.rename(tmp, path)) phase08_abort(paste("Could not atomically write", path))
  invisible(path)
}

phase08_atomic_save_rds <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  saveRDS(x, tmp, compress = "gzip")
  if (!file.rename(tmp, path)) phase08_abort(paste("Could not atomically write", path))
  invisible(path)
}

phase08_atomic_copy <- function(from, to) {
  dir.create(dirname(to), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(to, ".tmp.", Sys.getpid())
  if (!file.copy(from, tmp, overwrite = TRUE, copy.mode = TRUE)) {
    phase08_abort(paste("Could not stage", from))
  }
  if (!file.rename(tmp, to)) phase08_abort(paste("Could not atomically write", to))
  invisible(to)
}

phase08_sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

phase08_matrix_sha256 <- function(x) {
  digest::digest(x, algo = "sha256", serialize = TRUE)
}

phase08_peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(gsub("[^0-9.]", "", line[[1L]])) / (1024^2)
}

phase08_git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else {
    result[[1L]]
  }
}

phase08_slug <- function(x) gsub("[^A-Za-z0-9_.-]+", "_", as.character(x))

phase08_required_packages <- function(include_model = FALSE) {
  packages <- c("yaml", "Matrix", "data.table", "digest")
  if (isTRUE(include_model)) packages <- c(packages, "edgeR", "limma")
  packages
}

phase08_require_packages <- function(include_model = FALSE) {
  packages <- phase08_required_packages(include_model)
  missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing)) phase08_abort(paste("Missing required packages:", paste(missing, collapse = ", ")))
  invisible(packages)
}

phase08_load_context <- function(config_path, profile, include_model = FALSE) {
  phase08_require_packages(include_model)
  invocation_root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- phase08_absolute_path(config_path, invocation_root)
  if (!file.exists(config_path)) phase08_abort(paste("Config is missing:", config_path))
  config <- yaml::read_yaml(config_path)
  phase08_assert(
    identical(config$schema_version, "phase08_broad_deg_config_v1"),
    "Unsupported Phase 08 broad config schema"
  )
  project_root <- invocation_root
  selected_profile <- config$profiles[[profile]]
  if (is.null(selected_profile)) phase08_abort(paste("Unknown profile:", profile))
  mapping_path <- phase08_absolute_path(config$inputs$mapping, project_root)
  if (!file.exists(mapping_path)) phase08_abort(paste("Mapping is missing:", mapping_path))
  mapping <- data.table::fread(mapping_path, data.table = FALSE)
  required_mapping <- c(
    "schema_version", "expected_rds_id", "fine_cell_type",
    "broad_cell_type", "include", "exclusion_reason"
  )
  missing_mapping <- setdiff(required_mapping, names(mapping))
  if (length(missing_mapping)) {
    phase08_abort(paste("Mapping fields missing:", paste(missing_mapping, collapse = ", ")))
  }
  phase08_assert(
    all(mapping$schema_version == "phase08_broad_cell_mapping_v1"),
    "Unsupported broad-cell mapping schema"
  )
  phase08_assert(!anyDuplicated(mapping$fine_cell_type), "Fine-cell mapping keys must be unique")
  mapping$include <- phase08_as_logical(mapping$include)
  source_ids <- unlist(selected_profile$source_rds_ids, use.names = FALSE)
  broad_types <- unlist(selected_profile$broad_cell_types, use.names = FALSE)
  phase08_assert(length(source_ids) == as.integer(selected_profile$expected_source_bundles),
                 "Profile source-bundle count disagrees with its expectation")
  phase08_assert(length(broad_types) == as.integer(selected_profile$expected_broad_types),
                 "Profile broad-cell count disagrees with its expectation")
  list(
    config = config,
    profile_name = profile,
    profile = selected_profile,
    project_root = project_root,
    config_path = config_path,
    mapping_path = mapping_path,
    mapping = mapping,
    source_ids = source_ids,
    broad_types = broad_types,
    source_root = phase08_absolute_path(
      selected_profile$source_pseudobulk_directory, project_root
    ),
    annotation_master = phase08_absolute_path(selected_profile$annotation_master, project_root),
    annotation_status = phase08_absolute_path(selected_profile$annotation_status, project_root),
    output_root = phase08_absolute_path(selected_profile$output_directory, project_root)
  )
}

phase08_source_bundle_path <- function(context, rds_id) {
  filename <- context$config$inputs$source_bundle_filenames[[rds_id]]
  if (is.null(filename)) phase08_abort(paste("No source filename configured for", rds_id))
  file.path(context$source_root, filename)
}

phase08_source_status_path <- function(bundle_path) {
  sub("[.]pseudobulk_counts[.]rds$", ".pseudobulk_status.tsv", bundle_path)
}

phase08_validate_source_bundle <- function(context, rds_id, read_bundle = TRUE) {
  bundle_path <- phase08_source_bundle_path(context, rds_id)
  status_path <- phase08_source_status_path(bundle_path)
  if (!file.exists(bundle_path)) phase08_abort(paste("Source bundle is missing:", bundle_path))
  if (!file.exists(status_path)) phase08_abort(paste("Source status is missing:", status_path))
  status <- data.table::fread(status_path, data.table = FALSE)
  phase08_assert(
    nrow(status) == 1L && identical(status$validation_status[[1L]], "validated_complete"),
    paste("Phase 07 source is not validated_complete:", rds_id)
  )
  answer <- list(
    rds_id = rds_id,
    bundle_path = bundle_path,
    status_path = status_path,
    bundle_sha256 = phase08_sha256_file(bundle_path),
    status_sha256 = phase08_sha256_file(status_path)
  )
  if (isTRUE(read_bundle)) {
    bundle <- readRDS(bundle_path)
    phase08_assert(identical(bundle$schema_version, "pseudobulk_counts_v1"),
                   paste("Unsupported source bundle schema:", rds_id))
    phase08_assert(identical(as.character(bundle$rds_id), rds_id),
                   paste("Source RDS identity mismatch:", rds_id))
    phase08_assert(inherits(bundle$counts, "sparseMatrix"),
                   paste("Source counts are not sparse:", rds_id))
    phase08_assert(identical(colnames(bundle$counts), bundle$samples$pseudobulk_id),
                   paste("Source count/sample order mismatch:", rds_id))
    answer$bundle <- bundle
  }
  answer
}

phase08_single_value <- function(x, label) {
  values <- unique(x)
  values <- values[!(is.na(values) & is.character(values))]
  if (length(values) != 1L) phase08_abort(paste("Conflicting values for", label))
  values[[1L]]
}

phase08_aggregate_source_bundle <- function(bundle, mapping, broad_types, analysis) {
  samples <- as.data.frame(bundle$samples)
  required <- c(
    "pseudobulk_id", "projid", "cell_type_high_resolution", "diagnosis",
    "sex", "apoe_group", "age_death_scaled", "pmi_scaled", "nuclei",
    "total_umi_count", "total_mt_count", "total_mitocarta_count",
    "robust_flagged_nuclei"
  )
  missing <- setdiff(required, names(samples))
  if (length(missing)) phase08_abort(paste("Source sample fields missing:", paste(missing, collapse = ", ")))
  source_map <- mapping[mapping$expected_rds_id == bundle$rds_id, , drop = FALSE]
  observed <- sort(unique(trimws(as.character(samples$cell_type_high_resolution))))
  expected <- sort(unique(source_map$fine_cell_type))
  phase08_assert(identical(observed, expected), paste(
    "Observed fine types disagree with frozen mapping for", bundle$rds_id,
    "observed=", paste(observed, collapse = ";"),
    "expected=", paste(expected, collapse = ";")
  ))
  map_index <- match(samples$cell_type_high_resolution, source_map$fine_cell_type)
  phase08_assert(!anyNA(map_index), paste("Unmapped fine types in", bundle$rds_id))
  samples$broad_cell_type <- source_map$broad_cell_type[map_index]
  samples$mapping_include <- source_map$include[map_index]
  selected <- samples$mapping_include & samples$broad_cell_type %in% broad_types
  selected[is.na(selected)] <- FALSE
  phase08_assert(any(selected), paste("No requested broad-cell samples in", bundle$rds_id))
  selected_samples <- samples[selected, , drop = FALSE]
  selected_counts <- bundle$counts[, selected, drop = FALSE]
  key <- paste(selected_samples$projid, selected_samples$broad_cell_type, sep = "\r")
  unique_key <- sort(unique(key), method = "radix")
  group_index <- match(key, unique_key)
  aggregation <- Matrix::sparseMatrix(
    i = seq_along(group_index), j = group_index, x = 1,
    dims = c(length(group_index), length(unique_key))
  )
  counts <- selected_counts %*% aggregation
  counts <- methods::as(counts, "dgCMatrix")
  rownames(counts) <- rownames(selected_counts)
  metadata_rows <- lapply(seq_along(unique_key), function(i) {
    idx <- which(group_index == i)
    chunk <- selected_samples[idx, , drop = FALSE]
    total_umi <- sum(as.numeric(chunk$total_umi_count))
    total_mt <- sum(as.numeric(chunk$total_mt_count))
    total_mito <- sum(as.numeric(chunk$total_mitocarta_count))
    data.frame(
      projid = as.character(phase08_single_value(chunk$projid, "projid")),
      broad_cell_type = as.character(phase08_single_value(chunk$broad_cell_type, "broad_cell_type")),
      diagnosis = as.character(phase08_single_value(chunk$diagnosis, "diagnosis")),
      sex = as.character(phase08_single_value(chunk$sex, "sex")),
      apoe_group = as.character(phase08_single_value(chunk$apoe_group, "apoe_group")),
      age_death_scaled = as.numeric(phase08_single_value(chunk$age_death_scaled, "age_death_scaled")),
      pmi_scaled = as.numeric(phase08_single_value(chunk$pmi_scaled, "pmi_scaled")),
      nuclei = as.integer(sum(as.numeric(chunk$nuclei))),
      total_umi_count = as.numeric(total_umi),
      total_mt_count = as.numeric(total_mt),
      aggregate_percent_mt = if (total_umi > 0) 100 * total_mt / total_umi else NA_real_,
      total_mitocarta_count = as.numeric(total_mito),
      aggregate_percent_mitocarta = if (total_umi > 0) 100 * total_mito / total_umi else NA_real_,
      robust_flagged_nuclei = as.integer(sum(as.numeric(chunk$robust_flagged_nuclei))),
      contributing_fine_cell_types = paste(sort(unique(chunk$cell_type_high_resolution)), collapse = ";"),
      source_rds_ids = as.character(bundle$rds_id),
      stringsAsFactors = FALSE
    )
  })
  metadata <- do.call(rbind, metadata_rows)
  metadata <- metadata[order(metadata$broad_cell_type, metadata$projid), , drop = FALSE]
  reorder_index <- match(
    paste(metadata$projid, metadata$broad_cell_type, sep = "\r"), unique_key
  )
  counts <- counts[, reorder_index, drop = FALSE]
  metadata$broad_pseudobulk_id <- paste(
    phase08_slug(metadata$broad_cell_type), metadata$projid, sep = "__"
  )
  colnames(counts) <- metadata$broad_pseudobulk_id
  minimum_primary <- as.integer(analysis$minimum_nuclei_primary)
  minimum_sensitivity <- as.integer(analysis$minimum_nuclei_sensitivity)
  metadata$primary_eligible <- metadata$nuclei >= minimum_primary
  metadata$sensitivity_eligible <- metadata$nuclei >= minimum_sensitivity
  metadata$primary_ineligibility_reason <- ifelse(
    metadata$primary_eligible, "", paste0("nuclei_below_", minimum_primary)
  )
  metadata$sensitivity_ineligibility_reason <- ifelse(
    metadata$sensitivity_eligible, "", paste0("nuclei_below_", minimum_sensitivity)
  )
  phase08_assert(
    identical(as.numeric(Matrix::colSums(counts)), as.numeric(metadata$total_umi_count)),
    paste("Library-size conservation failed for", bundle$rds_id)
  )
  source_gene_sums <- Matrix::rowSums(selected_counts)
  aggregate_gene_sums <- Matrix::rowSums(counts)
  phase08_assert(
    identical(as.numeric(source_gene_sums), as.numeric(aggregate_gene_sums)),
    paste("Gene-wise count conservation failed for", bundle$rds_id)
  )
  list(
    schema_version = "broad_pseudobulk_shard_v1",
    rds_id = as.character(bundle$rds_id),
    counts = counts,
    samples = metadata,
    source_selected_columns = ncol(selected_counts),
    source_selected_total_counts = sum(as.numeric(source_gene_sums)),
    aggregate_total_counts = sum(as.numeric(aggregate_gene_sums)),
    included_fine_types = sort(unique(selected_samples$cell_type_high_resolution)),
    excluded_fine_types = sort(unique(samples$cell_type_high_resolution[!selected]))
  )
}

phase08_combine_shards <- function(shards, broad_types, analysis) {
  answer <- list()
  for (broad in broad_types) {
    selected_shards <- shards[vapply(
      shards,
      function(shard) broad %in% shard$samples$broad_cell_type,
      logical(1)
    )]
    phase08_assert(length(selected_shards) >= 1L, paste("No shard supplies", broad))
    reference_genes <- rownames(selected_shards[[1L]]$counts)
    for (shard in selected_shards) {
      phase08_assert(identical(rownames(shard$counts), reference_genes),
                     paste("Feature identity/order mismatch while combining", broad))
    }
    count_parts <- lapply(selected_shards, function(shard) {
      idx <- shard$samples$broad_cell_type == broad
      shard$counts[, idx, drop = FALSE]
    })
    sample_parts <- lapply(selected_shards, function(shard) {
      shard$samples[shard$samples$broad_cell_type == broad, , drop = FALSE]
    })
    combined_counts <- do.call(cbind, count_parts)
    combined_samples <- do.call(rbind, sample_parts)
    key <- as.character(combined_samples$projid)
    donor_ids <- sort(unique(key), method = "radix")
    group_index <- match(key, donor_ids)
    aggregation <- Matrix::sparseMatrix(
      i = seq_along(group_index), j = group_index, x = 1,
      dims = c(length(group_index), length(donor_ids))
    )
    counts <- combined_counts %*% aggregation
    counts <- methods::as(counts, "dgCMatrix")
    rownames(counts) <- reference_genes
    metadata_rows <- lapply(seq_along(donor_ids), function(i) {
      chunk <- combined_samples[group_index == i, , drop = FALSE]
      total_umi <- sum(as.numeric(chunk$total_umi_count))
      total_mt <- sum(as.numeric(chunk$total_mt_count))
      total_mito <- sum(as.numeric(chunk$total_mitocarta_count))
      data.frame(
        schema_version = "broad_pseudobulk_samples_v1",
        projid = donor_ids[[i]], broad_cell_type = broad,
        diagnosis = as.character(phase08_single_value(chunk$diagnosis, "diagnosis")),
        sex = as.character(phase08_single_value(chunk$sex, "sex")),
        apoe_group = as.character(phase08_single_value(chunk$apoe_group, "apoe_group")),
        age_death_scaled = as.numeric(phase08_single_value(chunk$age_death_scaled, "age_death_scaled")),
        pmi_scaled = as.numeric(phase08_single_value(chunk$pmi_scaled, "pmi_scaled")),
        nuclei = as.integer(sum(as.numeric(chunk$nuclei))),
        total_umi_count = as.numeric(total_umi), total_mt_count = as.numeric(total_mt),
        aggregate_percent_mt = if (total_umi > 0) 100 * total_mt / total_umi else NA_real_,
        total_mitocarta_count = as.numeric(total_mito),
        aggregate_percent_mitocarta = if (total_umi > 0) 100 * total_mito / total_umi else NA_real_,
        robust_flagged_nuclei = as.integer(sum(as.numeric(chunk$robust_flagged_nuclei))),
        contributing_fine_cell_types = paste(
          sort(unique(unlist(strsplit(chunk$contributing_fine_cell_types, ";", fixed = TRUE)))),
          collapse = ";"
        ),
        source_rds_ids = paste(sort(unique(chunk$source_rds_ids)), collapse = ";"),
        stringsAsFactors = FALSE
      )
    })
    metadata <- do.call(rbind, metadata_rows)
    metadata$broad_pseudobulk_id <- paste(phase08_slug(broad), metadata$projid, sep = "__")
    colnames(counts) <- metadata$broad_pseudobulk_id
    metadata$primary_eligible <- metadata$nuclei >= as.integer(analysis$minimum_nuclei_primary)
    metadata$sensitivity_eligible <- metadata$nuclei >= as.integer(analysis$minimum_nuclei_sensitivity)
    metadata$primary_ineligibility_reason <- ifelse(
      metadata$primary_eligible, "",
      paste0("nuclei_below_", as.integer(analysis$minimum_nuclei_primary))
    )
    metadata$sensitivity_ineligibility_reason <- ifelse(
      metadata$sensitivity_eligible, "",
      paste0("nuclei_below_", as.integer(analysis$minimum_nuclei_sensitivity))
    )
    phase08_assert(identical(colnames(counts), metadata$broad_pseudobulk_id),
                   paste("Final count/sample order mismatch for", broad))
    phase08_assert(
      identical(as.numeric(Matrix::colSums(counts)), as.numeric(metadata$total_umi_count)),
      paste("Final library-size conservation failed for", broad)
    )
    phase08_assert(
      identical(as.numeric(Matrix::rowSums(counts)), as.numeric(Matrix::rowSums(combined_counts))),
      paste("Final gene-wise conservation failed for", broad)
    )
    answer[[broad]] <- list(
      schema_version = "broad_pseudobulk_counts_v1",
      broad_cell_type = broad,
      assay = "RNA", count_source = "RNA_counts",
      counts = counts, samples = metadata,
      source_rds_ids = sort(unique(unlist(lapply(selected_shards, `[[`, "rds_id")))),
      counts_sha256 = phase08_matrix_sha256(counts)
    )
  }
  answer
}

phase08_group_rows <- function(config) {
  groups <- config$analysis$groups
  do.call(rbind, lapply(groups, function(group) data.frame(
    group_id = as.character(group$group_id),
    sex = as.character(group$sex),
    apoe_group = as.character(group$apoe_group),
    stringsAsFactors = FALSE
  )))
}

phase08_build_contrast_manifest <- function(samples, context) {
  groups <- phase08_group_rows(context$config)
  numerator <- as.character(context$config$analysis$numerator)
  denominator <- as.character(context$config$analysis$denominator)
  minimum_donors <- as.integer(context$config$analysis$minimum_donors_per_arm)
  confirmatory_donors <- as.integer(context$config$analysis$confirmatory_donors_per_arm)
  rows <- list()
  for (broad in context$broad_types) {
    broad_samples <- samples[
      samples$broad_cell_type == broad & phase08_as_logical(samples$primary_eligible),
      , drop = FALSE
    ]
    for (i in seq_len(nrow(groups))) {
      group <- groups[i, , drop = FALSE]
      stratum <- broad_samples[
        broad_samples$sex == group$sex &
          broad_samples$apoe_group == group$apoe_group,
        , drop = FALSE
      ]
      ad <- stratum[stratum$diagnosis == numerator, , drop = FALSE]
      nci <- stratum[stratum$diagnosis == denominator, , drop = FALSE]
      donors_ad <- length(unique(ad$projid))
      donors_nci <- length(unique(nci$projid))
      estimable <- donors_ad >= minimum_donors && donors_nci >= minimum_donors
      reason <- if (estimable) "" else paste0(
        "fewer_than_", minimum_donors, "_eligible_donors_per_arm:AD=",
        donors_ad, ",NCI=", donors_nci
      )
      rows[[length(rows) + 1L]] <- data.frame(
        schema_version = "broad_deg_contrast_manifest_v1",
        contrast_id = paste(broad, paste("AD_vs_NCI", group$sex, group$apoe_group, sep = "__"), sep = "::"),
        broad_cell_type = broad, group_id = group$group_id,
        sex = group$sex, apoe_group = group$apoe_group,
        numerator = numerator, denominator = denominator,
        donors_ad = as.integer(donors_ad), donors_nci = as.integer(donors_nci),
        nuclei_ad = as.integer(sum(ad$nuclei)), nuclei_nci = as.integer(sum(nci$nuclei)),
        minimum_donors_per_arm = minimum_donors,
        confirmatory_donors_per_arm = confirmatory_donors,
        confirmatory_support = donors_ad >= confirmatory_donors && donors_nci >= confirmatory_donors,
        modeling_status = if (estimable) "estimable" else "not_estimable",
        modeling_reason = reason, stringsAsFactors = FALSE
      )
    }
  }
  manifest <- do.call(rbind, rows)
  manifest$manifest_row <- seq_len(nrow(manifest))
  manifest <- manifest[, c("schema_version", "manifest_row", setdiff(names(manifest), c("schema_version", "manifest_row")))]
  manifest
}

phase08_contrast_vector <- function(row, design_columns) {
  ad <- paste(row$numerator, row$sex, row$apoe_group, sep = "__")
  nci <- paste(row$denominator, row$sex, row$apoe_group, sep = "__")
  if (!all(c(ad, nci) %in% design_columns)) {
    phase08_abort(paste("Required design groups absent for", row$contrast_id))
  }
  answer <- setNames(numeric(length(design_columns)), design_columns)
  answer[ad] <- 1
  answer[nci] <- -1
  answer
}

phase08_threshold_flags <- function(results, config) {
  strict_q <- as.numeric(config$thresholds$strict$q)
  strict_lfc <- log2(as.numeric(config$thresholds$strict$absolute_fold_change))
  relaxed_q <- as.numeric(config$thresholds$relaxed$q)
  relaxed_lfc <- log2(as.numeric(config$thresholds$relaxed$absolute_fold_change))
  exploratory_q <- as.numeric(config$thresholds$exploratory$q)
  results$strict_deg <- results$fdr_bh_within_contrast < strict_q & abs(results$logFC) > strict_lfc
  results$relaxed_deg <- results$fdr_bh_within_contrast <= relaxed_q & abs(results$logFC) >= relaxed_lfc
  results$exploratory_deg <- results$fdr_bh_within_contrast <= exploratory_q
  results$direction <- ifelse(results$logFC > 0, "AD_up", ifelse(results$logFC < 0, "AD_down", "zero"))
  results$strict_q_threshold <- strict_q
  results$strict_abs_log2fc_threshold <- strict_lfc
  results$relaxed_q_threshold <- relaxed_q
  results$relaxed_abs_log2fc_threshold <- relaxed_lfc
  results$exploratory_q_threshold <- exploratory_q
  results
}

phase08_read_annotation <- function(context) {
  if (!file.exists(context$annotation_master)) {
    phase08_abort(paste("Annotation master is missing:", context$annotation_master))
  }
  if (!file.exists(context$annotation_status)) {
    phase08_abort(paste("Annotation status is missing:", context$annotation_status))
  }
  status <- data.table::fread(context$annotation_status, data.table = FALSE)
  phase08_assert(nrow(status) == 1L && identical(status$validation_status[[1L]], "validated_complete"),
                 "Phase 09 annotation is not validated_complete")
  annotation <- data.table::fread(context$annotation_master, data.table = FALSE)
  annotation <- annotation[!phase08_as_logical(annotation$reference_only), , drop = FALSE]
  required <- c(
    "feature_id_original", "symbol_hgnc_current", "mapping_status", "chromosome",
    "is_mitocarta3", "is_mtDNA_gene", "mito_tier", "genome_origin"
  )
  missing <- setdiff(required, names(annotation))
  if (length(missing)) phase08_abort(paste("Annotation fields missing:", paste(missing, collapse = ", ")))
  selected <- annotation[, required, drop = FALSE]
  selected <- selected[order(selected$feature_id_original), , drop = FALSE]
  groups <- split(seq_len(nrow(selected)), selected$feature_id_original)
  for (field in setdiff(required, "feature_id_original")) {
    conflicting <- vapply(groups, function(index) {
      values <- unique(as.character(selected[[field]][index]))
      values <- values[!is.na(values)]
      length(values) > 1L
    }, logical(1))
    if (any(conflicting)) {
      phase08_abort(paste(
        "Annotation conflict for", names(conflicting)[which(conflicting)[[1L]]], field
      ))
    }
  }
  first_index <- vapply(groups, `[[`, integer(1), 1L)
  consensus <- selected[first_index, , drop = FALSE]
  row.names(consensus) <- NULL
  phase08_assert(!anyDuplicated(consensus$feature_id_original), "Annotation consensus keys are not unique")
  consensus
}

phase08_artifact_rows <- function(paths, context, schema = "broad_deg_artifacts_v1") {
  paths <- sort(unique(paths[file.exists(paths)]), method = "radix")
  data.frame(
    schema_version = schema,
    artifact = basename(paths),
    path = vapply(paths, phase08_relative_path, character(1), root = context$project_root),
    bytes = as.numeric(file.info(paths)$size),
    sha256 = vapply(paths, phase08_sha256_file, character(1)),
    stringsAsFactors = FALSE
  )
}

phase08_parse_cli <- function(args, allow = character()) {
  out <- list(config = "config/phase08_broad_deg.yml", profile = "local_pilot")
  boolean_options <- intersect(c("--preflight", "--resume"), allow)
  value_options <- c("--config", "--profile", setdiff(allow, boolean_options))
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      out$help <- TRUE
      i <- i + 1L
    } else if (key %in% boolean_options) {
      out[[gsub("-", "_", sub("^--", "", key))]] <- TRUE
      i <- i + 1L
    } else if (key %in% value_options && i < length(args)) {
      out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
      i <- i + 2L
    } else {
      phase08_abort(paste("Unknown option or missing value:", key))
    }
  }
  out$preflight <- isTRUE(out$preflight)
  out$resume <- isTRUE(out$resume)
  out
}
