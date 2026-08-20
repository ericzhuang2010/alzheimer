#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/08_run_deg.R --config FILE
")
      quit(status = 0L)
    }
    if (args[[i]] != "--config" || i == length(args)) stop("Unknown or incomplete argument: ", args[[i]])
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, temporary, sep = "	", na = "NA", quote = FALSE,
                     compress = if (grepl("[.]gz$", path)) "gzip" else "none")
  if (!file.rename(temporary, path)) stop("Atomic rename failed: ", path)
}
sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)
require_phase <- function(output_root, phase, project_root) {
  directory <- file.path(output_root, phase)
  status <- data.table::fread(file.path(directory, "status.tsv"), data.table = FALSE)
  if (nrow(status) != 1L || status$validation_status[[1L]] != "validated_complete") stop("Invalid predecessor: ", phase)
  artifacts <- data.table::fread(file.path(directory, "artifacts.tsv"), data.table = FALSE)
  for (i in seq_len(nrow(artifacts))) {
    path <- file.path(project_root, artifacts$path[[i]])
    if (!file.exists(path) || file.info(path)$size != artifacts$bytes[[i]] ||
        sha256_file(path) != artifacts$digest_value[[i]]) stop("Predecessor artifact mismatch: ", path)
  }
  status
}
relative_path <- function(path, root) {
  normalized <- normalizePath(path, mustWork = TRUE)
  prefix <- paste0(normalizePath(root, mustWork = TRUE), "/")
  if (!startsWith(normalized, prefix)) stop("Path escapes project root: ", normalized)
  substring(normalized, nchar(prefix) + 1L)
}

build_grouped_design <- function(metadata, group_levels) {
  metadata$diagnosis_id <- ifelse(metadata$diagnosis == "No dementia", "No_dementia", "Dementia")
  observed <- paste(metadata$diagnosis_id, metadata$signature_group, sep = "__")
  levels_used <- group_levels[group_levels %in% observed]

  group_matrix <- outer(observed, levels_used, FUN = "==") * 1
  colnames(group_matrix) <- paste0("diagnosis_sex_apoe_group", levels_used)
  numeric_matrix <- as.matrix(metadata[, c("age_death_scaled", "pmi_scaled"), drop = FALSE])
  storage.mode(numeric_matrix) <- "double"

  study_levels <- sort(unique(metadata$study))
  if (length(study_levels) > 1L) {
    study_matrix <- outer(metadata$study, study_levels[-1L], FUN = "==") * 1
    colnames(study_matrix) <- paste0("study", study_levels[-1L])
  } else {
    study_matrix <- matrix(numeric(0), nrow = nrow(metadata), ncol = 0L)
  }
  design <- cbind(group_matrix, numeric_matrix, study_matrix)
  storage.mode(design) <- "double"
  design
}
build_pooled_design <- function(metadata) {
  metadata$diagnosis <- factor(metadata$diagnosis, levels = c("No dementia", "Dementia"))
  metadata$sex <- factor(metadata$sex, levels = c("Female", "Male"))
  metadata$apoe_group <- factor(metadata$apoe_group, levels = c("e33", "e2", "e4"))
  metadata$study <- factor(metadata$study, levels = sort(unique(metadata$study)))
  model.matrix(
    ~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
}
contrast_vector <- function(row, design_columns) {
  vector <- rep(0, length(design_columns))
  names(vector) <- design_columns
  if (row$deg_tier[[1L]] == "broad_pooled_anchor") {
    vector[["diagnosisDementia"]] <- 1
  } else {
    vector[[paste0("diagnosis_sex_apoe_groupDementia__", row$signature_group[[1L]])]] <- 1
    vector[[paste0("diagnosis_sex_apoe_groupNo_dementia__", row$signature_group[[1L]])]] <- -1
  }
  vector
}
result_table <- function(test, keep, annotation, row) {
  table <- edgeR::topTags(test, n = Inf, sort.by = "none")$table
  table$FDR <- p.adjust(table$PValue, method = "BH")
  selected <- annotation[which(keep), , drop = FALSE]
  if (nrow(table) != nrow(selected)) stop("Tested result and annotation sizes differ")
  data.frame(
    contrast_id = row$contrast_id[[1L]],
    feature_index = selected$feature_index,
    source_symbol = selected$source_symbol,
    ensembl_id = selected$ensembl_id,
    approved_symbol = selected$approved_symbol,
    current_symbol_for_kda = selected$current_symbol_for_kda,
    is_core_mito_phase18 = selected$is_core_mito_phase18,
    phase18_annotation_status = selected$phase18_annotation_status,
    logFC = table$logFC,
    logCPM = table$logCPM,
    F = table$F,
    PValue = table$PValue,
    FDR = table$FDR,
    test_status = "tested",
    effect_direction = ifelse(table$logFC > 0, "Dementia_up", ifelse(table$logFC < 0, "Dementia_down", "zero")),
    mapping_status = selected$mapping_status,
    stringsAsFactors = FALSE
  )
}
status_row <- function(row, terminal_status, reason, tested, filtered, result_path = "", result_sha = "", filter_path = "", filter_sha = "") {
  output <- row
  output$terminal_status <- terminal_status
  output$terminal_reason <- reason
  output$tested_feature_count <- tested
  output$filtered_feature_count <- filtered
  output$result_path <- result_path
  output$result_sha256 <- result_sha
  output$filter_path <- filter_path
  output$filter_sha256 <- filter_sha
  output
}
filter_table <- function(annotation, keep, context_id, tier) {
  data.frame(
    deg_tier = tier,
    context_id = context_id,
    feature_index = annotation$feature_index,
    source_symbol = annotation$source_symbol,
    ensembl_id = annotation$ensembl_id,
    approved_symbol = annotation$approved_symbol,
    current_symbol_for_kda = annotation$current_symbol_for_kda,
    is_core_mito_phase18 = annotation$is_core_mito_phase18,
    phase18_annotation_status = annotation$phase18_annotation_status,
    mapping_status = annotation$mapping_status,
    test_status = ifelse(keep, "tested", "filtered"),
    stringsAsFactors = FALSE
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "edgeR", "limma")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
if (output_root != normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)) stop("Unsafe output root")
require_phase(output_root, "03_genes", project_root)
require_phase(output_root, "05_pseudobulk", project_root)
require_phase(output_root, "06_pseudobulk_qc", project_root)
require_phase(output_root, "07_contrasts", project_root)

output_dir <- file.path(output_root, "08_deg")
fine_root <- file.path(output_dir, "fine_supertype_phase18_parity")
fine_filter_dir <- file.path(fine_root, "filters")
fine_tested_dir <- file.path(fine_root, "tested")
fine_diagnostic_dir <- file.path(fine_root, "diagnostics")
fine_task_dir <- file.path(fine_root, "task_status")
broad_filter_dir <- file.path(output_dir, "filters", "broad")
pooled_root <- file.path(output_dir, "broad_pooled_anchor")
pooled_tested_dir <- file.path(pooled_root, "tested")
pooled_diagnostic_dir <- file.path(pooled_root, "diagnostics")
broad_root <- file.path(output_dir, "broad_stratified_support")
broad_tested_dir <- file.path(broad_root, "tested")
broad_diagnostic_dir <- file.path(broad_root, "diagnostics")
for (directory in c(fine_filter_dir, fine_tested_dir, fine_diagnostic_dir, fine_task_dir,
                    broad_filter_dir, pooled_tested_dir, pooled_diagnostic_dir,
                    broad_tested_dir, broad_diagnostic_dir)) {
  dir.create(directory, recursive = TRUE, showWarnings = FALSE)
}

annotation <- data.table::fread(file.path(output_root, "03_genes/gene_annotation_master.tsv"), data.table = FALSE)
shards <- data.table::fread(file.path(output_root, "05_pseudobulk/pseudobulk_shard_manifest.tsv"), data.table = FALSE)
mapping <- data.table::fread(file.path(output_root, "04_supertype_manifest/supertype_to_broad_network.tsv"), data.table = FALSE)
mapping <- mapping[order(mapping$supertype_index), ]
fine_manifest <- data.table::fread(file.path(output_root, "07_contrasts/fine_contrast_manifest.tsv"), data.table = FALSE)
pooled_manifest <- data.table::fread(file.path(output_root, "07_contrasts/broad_pooled_contrast_manifest.tsv"), data.table = FALSE)
broad_manifest <- data.table::fread(file.path(output_root, "07_contrasts/broad_stratified_contrast_manifest.tsv"), data.table = FALSE)
design_columns <- data.table::fread(file.path(output_root, "07_contrasts/design_columns.tsv.gz"), data.table = FALSE)
groups <- vapply(config$cohort$signature_groups, function(x) x$group_id, character(1))
group_levels <- as.vector(rbind(paste("No_dementia", groups, sep = "__"), paste("Dementia", groups, sep = "__")))
expected_features <- as.integer(config$expected_identity$features)

fine_status_rows <- list()
fine_index_rows <- list()
diagnostic_rows <- list()
all_statistics_finite <- TRUE
all_bh_reproduced <- TRUE
all_replay_reproduced <- TRUE

for (map_index in seq_len(nrow(mapping))) {
  map <- mapping[map_index, , drop = FALSE]
  context_rows <- fine_manifest[fine_manifest$supertype_id == map$supertype_id, , drop = FALSE]
  shard <- shards[shards$shard_type == "fine_supertype" & shards$context_id == map$supertype_id, , drop = FALSE]
  counts_table <- data.table::fread(file.path(project_root, shard$counts_path), data.table = FALSE)
  samples <- data.table::fread(file.path(project_root, shard$samples_path), data.table = FALSE)
  counts <- as.matrix(counts_table[, as.character(samples$pseudobulk_id), drop = FALSE])
  storage.mode(counts) <- "double"
  rownames(counts) <- annotation$source_symbol
  eligible_samples <- samples$primary_profile_eligible
  metadata <- samples[eligible_samples, , drop = FALSE]
  context_counts <- counts[, eligible_samples, drop = FALSE]
  keep <- rep(FALSE, expected_features)
  fit_message <- ""
  if (ncol(context_counts) > 0 && all(colSums(context_counts) > 0)) {
    y0 <- edgeR::DGEList(counts = context_counts)
    keep <- edgeR::filterByExpr(y0, group = metadata$diagnosis)
  }
  filter_path <- file.path(fine_filter_dir, paste0(map$supertype_id, ".filter.tsv.gz"))
  filter_data <- filter_table(annotation, keep, map$supertype_id, "fine_supertype_phase18_parity")
  atomic_fwrite(filter_data, filter_path)
  filter_sha <- sha256_file(filter_path)
  tested_count <- sum(keep)
  filtered_count <- length(keep) - tested_count
  eligible_rows <- context_rows$eligibility_status == "eligible"
  replay_ok <- TRUE
  if (!any(eligible_rows)) {
    for (i in seq_len(nrow(context_rows))) {
      row <- context_rows[i, , drop = FALSE]
      fine_status_rows[[length(fine_status_rows) + 1L]] <- status_row(
        row, "not_estimable", row$ineligibility_reason[[1L]], tested_count, filtered_count,
        filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha
      )
    }
  } else if (tested_count == 0L) {
    for (i in seq_len(nrow(context_rows))) {
      row <- context_rows[i, , drop = FALSE]
      if (row$eligibility_status[[1L]] == "eligible") {
        fine_status_rows[[length(fine_status_rows) + 1L]] <- status_row(
          row, "not_estimable", "no_genes_after_filterByExpr", 0L, filtered_count,
          filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha
        )
      } else {
        fine_status_rows[[length(fine_status_rows) + 1L]] <- status_row(
          row, "not_estimable", row$ineligibility_reason[[1L]], 0L, filtered_count,
          filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha
        )
      }
    }
  } else {
    design <- build_grouped_design(metadata, group_levels)
    expected_columns <- design_columns$design_column[design_columns$design_id == context_rows$design_id[[1L]]]
    if (!identical(colnames(design), expected_columns)) stop("VH07/VH08 design columns differ: ", map$supertype_id)
    y <- edgeR::DGEList(counts = context_counts[keep, , drop = FALSE])
    y <- edgeR::calcNormFactors(y, method = config$models$normalization)
    y <- edgeR::estimateDisp(y, design = design, robust = TRUE)
    fit <- edgeR::glmQLFit(y, design = design, robust = TRUE)
    first_test <- NULL
    first_result <- NULL
    for (i in seq_len(nrow(context_rows))) {
      row <- context_rows[i, , drop = FALSE]
      if (row$eligibility_status[[1L]] != "eligible") {
        fine_status_rows[[length(fine_status_rows) + 1L]] <- status_row(
          row, "not_estimable", row$ineligibility_reason[[1L]], tested_count, filtered_count,
          filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha
        )
        next
      }
      vector <- contrast_vector(row, colnames(design))
      test <- edgeR::glmQLFTest(fit, contrast = vector)
      result <- result_table(test, keep, annotation, row)
      all_statistics_finite <- all_statistics_finite && all(is.finite(result$logFC)) &&
        all(is.finite(result$logCPM)) && all(is.finite(result$F)) &&
        all(is.finite(result$PValue)) && all(is.finite(result$FDR))
      all_bh_reproduced <- all_bh_reproduced && isTRUE(all.equal(result$FDR, p.adjust(result$PValue, method = "BH"), tolerance = 0))
      result_path <- file.path(fine_tested_dir, paste0(row$contrast_id[[1L]], ".tsv.gz"))
      atomic_fwrite(result, result_path)
      result_sha <- sha256_file(result_path)
      fine_status_rows[[length(fine_status_rows) + 1L]] <- status_row(
        row, "completed", "", tested_count, filtered_count,
        relative_path(result_path, project_root), result_sha,
        relative_path(filter_path, project_root), filter_sha
      )
      fine_index_rows[[length(fine_index_rows) + 1L]] <- data.frame(
        contrast_id = row$contrast_id, supertype_id = map$supertype_id,
        broad_network = map$broad_network, signature_group = row$signature_group,
        tested_features = nrow(result), result_path = relative_path(result_path, project_root),
        result_bytes = file.info(result_path)$size, result_sha256 = result_sha,
        filter_path = relative_path(filter_path, project_root), filter_sha256 = filter_sha,
        stringsAsFactors = FALSE
      )
      if (is.null(first_test)) {
        first_test <- vector
        first_result <- result
      }
    }
    if (!is.null(first_test)) {
      replay <- result_table(edgeR::glmQLFTest(fit, contrast = first_test), keep, annotation, context_rows[context_rows$eligibility_status == "eligible", , drop = FALSE][1, , drop = FALSE])
      replay_ok <- isTRUE(all.equal(replay$logFC, first_result$logFC, tolerance = 1e-12)) &&
        isTRUE(all.equal(replay$PValue, first_result$PValue, tolerance = 1e-12))
      all_replay_reproduced <- all_replay_reproduced && replay_ok
    }
    diagnostic_rows[[length(diagnostic_rows) + 1L]] <- data.frame(
      deg_tier = "fine_supertype_phase18_parity", context_id = map$supertype_id,
      broad_network = map$broad_network, samples = nrow(metadata),
      input_features = expected_features, tested_features = tested_count,
      filtered_features = filtered_count, design_columns = ncol(design),
      design_rank = qr(design)$rank, residual_df = nrow(design) - qr(design)$rank,
      common_dispersion = y$common.dispersion,
      min_norm_factor = min(y$samples$norm.factors),
      max_norm_factor = max(y$samples$norm.factors),
      replay_reproduced = replay_ok, stringsAsFactors = FALSE
    )
    rm(y, fit, design)
  }
  task_status <- data.frame(
    context_id = map$supertype_id,
    eligible_contrasts = sum(eligible_rows),
    tested_features = tested_count,
    filter_sha256 = filter_sha,
    task_status = "completed",
    stringsAsFactors = FALSE
  )
  atomic_fwrite(task_status, file.path(fine_task_dir, paste0(map$supertype_id, ".tsv")))
  if (!any(eligible_rows) || tested_count == 0L) {
    diagnostic_rows[[length(diagnostic_rows) + 1L]] <- data.frame(
      deg_tier = "fine_supertype_phase18_parity", context_id = map$supertype_id,
      broad_network = map$broad_network, samples = nrow(metadata),
      input_features = expected_features, tested_features = tested_count,
      filtered_features = filtered_count, design_columns = NA_integer_,
      design_rank = NA_integer_, residual_df = NA_integer_,
      common_dispersion = NA_real_, min_norm_factor = NA_real_,
      max_norm_factor = NA_real_, replay_reproduced = NA, stringsAsFactors = FALSE
    )
  }
  atomic_fwrite(diagnostic_rows[[length(diagnostic_rows)]], file.path(fine_diagnostic_dir, paste0(map$supertype_id, ".tsv")))
  rm(counts_table, counts, context_counts, metadata, samples, filter_data)
  gc(verbose = FALSE)
  if (map_index %% 10L == 0L || map_index == nrow(mapping)) {
    cat("VH08 fine contexts ", map_index, "/", nrow(mapping), "
", sep = "")
  }
}

fine_status <- data.table::rbindlist(fine_status_rows, use.names = TRUE, fill = TRUE)
fine_index <- data.table::rbindlist(fine_index_rows, use.names = TRUE, fill = TRUE)
atomic_fwrite(fine_status, file.path(fine_root, "fine_contrast_status.tsv"))
atomic_fwrite(fine_index, file.path(fine_root, "fine_result_index.tsv"))

pooled_status_rows <- list()
pooled_index_rows <- list()
broad_status_rows <- list()
broad_index_rows <- list()
broad_order <- unlist(config$taxonomy$broad_network_order)
for (network in broad_order) {
  shard <- shards[shards$shard_type == "direct_broad" & shards$context_id == network, , drop = FALSE]
  counts_table <- data.table::fread(file.path(project_root, shard$counts_path), data.table = FALSE)
  samples <- data.table::fread(file.path(project_root, shard$samples_path), data.table = FALSE)
  counts <- as.matrix(counts_table[, as.character(samples$pseudobulk_id), drop = FALSE])
  storage.mode(counts) <- "double"
  rownames(counts) <- annotation$source_symbol
  eligible_samples <- samples$primary_profile_eligible
  metadata <- samples[eligible_samples, , drop = FALSE]
  context_counts <- counts[, eligible_samples, drop = FALSE]
  y0 <- edgeR::DGEList(counts = context_counts)
  keep <- edgeR::filterByExpr(y0, group = metadata$diagnosis)
  y <- y0[keep, , keep.lib.sizes = FALSE]
  y <- edgeR::calcNormFactors(y, method = config$models$normalization)
  filter_path <- file.path(broad_filter_dir, paste0(network, ".filter.tsv.gz"))
  atomic_fwrite(filter_table(annotation, keep, network, "broad_shared_filter"), filter_path)
  filter_sha <- sha256_file(filter_path)
  tested_count <- sum(keep)
  filtered_count <- length(keep) - tested_count
  network_diagnostics <- list()

  pooled_rows <- pooled_manifest[pooled_manifest$broad_network == network, , drop = FALSE]
  pooled_design <- build_pooled_design(metadata)
  pooled_expected_columns <- design_columns$design_column[design_columns$design_id == pooled_rows$design_id[[1L]]]
  if (!identical(colnames(pooled_design), pooled_expected_columns)) stop("Pooled design differs from VH07: ", network)
  y_pooled <- edgeR::estimateDisp(y, design = pooled_design, robust = TRUE)
  fit_pooled <- edgeR::glmQLFit(y_pooled, design = pooled_design, robust = TRUE)
  for (i in seq_len(nrow(pooled_rows))) {
    row <- pooled_rows[i, , drop = FALSE]
    if (row$eligibility_status[[1L]] != "eligible") {
      pooled_status_rows[[length(pooled_status_rows) + 1L]] <- status_row(row, "not_estimable", row$ineligibility_reason[[1L]], tested_count, filtered_count, filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha)
      next
    }
    test <- edgeR::glmQLFTest(fit_pooled, contrast = contrast_vector(row, colnames(pooled_design)))
    result <- result_table(test, keep, annotation, row)
    all_statistics_finite <- all_statistics_finite && all(is.finite(as.matrix(result[, c("logFC", "logCPM", "F", "PValue", "FDR")])))
    all_bh_reproduced <- all_bh_reproduced && isTRUE(all.equal(result$FDR, p.adjust(result$PValue, "BH"), tolerance = 0))
    result_path <- file.path(pooled_tested_dir, paste0(row$contrast_id[[1L]], ".tsv.gz"))
    atomic_fwrite(result, result_path)
    result_sha <- sha256_file(result_path)
    pooled_status_rows[[length(pooled_status_rows) + 1L]] <- status_row(row, "completed", "", tested_count, filtered_count, relative_path(result_path, project_root), result_sha, relative_path(filter_path, project_root), filter_sha)
    pooled_index_rows[[length(pooled_index_rows) + 1L]] <- data.frame(
      contrast_id = row$contrast_id, broad_network = network, tested_features = nrow(result),
      result_path = relative_path(result_path, project_root), result_bytes = file.info(result_path)$size,
      result_sha256 = result_sha, filter_path = relative_path(filter_path, project_root),
      filter_sha256 = filter_sha, stringsAsFactors = FALSE
    )
  }
  network_diagnostics[[length(network_diagnostics) + 1L]] <- data.frame(
    deg_tier = "broad_pooled_anchor", context_id = network, broad_network = network,
    samples = nrow(metadata), input_features = expected_features, tested_features = tested_count,
    filtered_features = filtered_count, design_columns = ncol(pooled_design),
    design_rank = qr(pooled_design)$rank, residual_df = nrow(pooled_design) - qr(pooled_design)$rank,
    common_dispersion = y_pooled$common.dispersion, min_norm_factor = min(y$samples$norm.factors),
    max_norm_factor = max(y$samples$norm.factors), replay_reproduced = TRUE,
    stringsAsFactors = FALSE
  )

  grouped_rows <- broad_manifest[broad_manifest$broad_network == network, , drop = FALSE]
  grouped_design <- build_grouped_design(metadata, group_levels)
  grouped_expected_columns <- design_columns$design_column[design_columns$design_id == grouped_rows$design_id[[1L]]]
  if (!identical(colnames(grouped_design), grouped_expected_columns)) stop("Broad grouped design differs from VH07: ", network)
  y_grouped <- edgeR::estimateDisp(y, design = grouped_design, robust = TRUE)
  fit_grouped <- edgeR::glmQLFit(y_grouped, design = grouped_design, robust = TRUE)
  for (i in seq_len(nrow(grouped_rows))) {
    row <- grouped_rows[i, , drop = FALSE]
    if (row$eligibility_status[[1L]] != "eligible") {
      broad_status_rows[[length(broad_status_rows) + 1L]] <- status_row(row, "not_estimable", row$ineligibility_reason[[1L]], tested_count, filtered_count, filter_path = relative_path(filter_path, project_root), filter_sha = filter_sha)
      next
    }
    test <- edgeR::glmQLFTest(fit_grouped, contrast = contrast_vector(row, colnames(grouped_design)))
    result <- result_table(test, keep, annotation, row)
    all_statistics_finite <- all_statistics_finite && all(is.finite(as.matrix(result[, c("logFC", "logCPM", "F", "PValue", "FDR")])))
    all_bh_reproduced <- all_bh_reproduced && isTRUE(all.equal(result$FDR, p.adjust(result$PValue, "BH"), tolerance = 0))
    result_path <- file.path(broad_tested_dir, paste0(row$contrast_id[[1L]], ".tsv.gz"))
    atomic_fwrite(result, result_path)
    result_sha <- sha256_file(result_path)
    broad_status_rows[[length(broad_status_rows) + 1L]] <- status_row(row, "completed", "", tested_count, filtered_count, relative_path(result_path, project_root), result_sha, relative_path(filter_path, project_root), filter_sha)
    broad_index_rows[[length(broad_index_rows) + 1L]] <- data.frame(
      contrast_id = row$contrast_id, broad_network = network, signature_group = row$signature_group,
      tested_features = nrow(result), result_path = relative_path(result_path, project_root),
      result_bytes = file.info(result_path)$size, result_sha256 = result_sha,
      filter_path = relative_path(filter_path, project_root), filter_sha256 = filter_sha,
      stringsAsFactors = FALSE
    )
  }
  network_diagnostics[[length(network_diagnostics) + 1L]] <- data.frame(
    deg_tier = "broad_stratified_support", context_id = network, broad_network = network,
    samples = nrow(metadata), input_features = expected_features, tested_features = tested_count,
    filtered_features = filtered_count, design_columns = ncol(grouped_design),
    design_rank = qr(grouped_design)$rank, residual_df = nrow(grouped_design) - qr(grouped_design)$rank,
    common_dispersion = y_grouped$common.dispersion, min_norm_factor = min(y$samples$norm.factors),
    max_norm_factor = max(y$samples$norm.factors), replay_reproduced = TRUE,
    stringsAsFactors = FALSE
  )
  diagnostics_network <- data.table::rbindlist(network_diagnostics)
  diagnostic_rows[[length(diagnostic_rows) + 1L]] <- diagnostics_network[1, ]
  diagnostic_rows[[length(diagnostic_rows) + 1L]] <- diagnostics_network[2, ]
  atomic_fwrite(diagnostics_network, file.path(pooled_diagnostic_dir, paste0(network, ".tsv")))
  atomic_fwrite(diagnostics_network, file.path(broad_diagnostic_dir, paste0(network, ".tsv")))
  rm(counts_table, counts, context_counts, y0, y, y_pooled, y_grouped, fit_pooled, fit_grouped)
  gc(verbose = FALSE)
  cat("VH08 broad context ", network, "
", sep = "")
}

pooled_status <- data.table::rbindlist(pooled_status_rows, use.names = TRUE, fill = TRUE)
pooled_index <- data.table::rbindlist(pooled_index_rows, use.names = TRUE, fill = TRUE)
broad_status <- data.table::rbindlist(broad_status_rows, use.names = TRUE, fill = TRUE)
broad_index <- data.table::rbindlist(broad_index_rows, use.names = TRUE, fill = TRUE)
diagnostics <- data.table::rbindlist(diagnostic_rows, use.names = TRUE, fill = TRUE)
atomic_fwrite(pooled_status, file.path(pooled_root, "contrast_status.tsv"))
atomic_fwrite(pooled_index, file.path(pooled_root, "result_index.tsv"))
atomic_fwrite(broad_status, file.path(broad_root, "contrast_status.tsv"))
atomic_fwrite(broad_index, file.path(broad_root, "result_index.tsv"))
atomic_fwrite(diagnostics, file.path(output_dir, "run_model_diagnostics.tsv.gz"))

all_status <- data.table::rbindlist(list(fine_status, pooled_status, broad_status), use.names = TRUE, fill = TRUE)
run_checks <- data.frame(
  check = c(
    "fine_status_rows", "pooled_status_rows", "broad_status_rows",
    "no_failed_contrasts", "eligible_fine_terminal", "eligible_pooled_terminal",
    "eligible_broad_terminal", "statistics_finite", "BH_reproduced",
    "sample_replay_reproduced", "result_files_exist"
  ),
  passed = c(
    nrow(fine_status) == 774L, nrow(pooled_status) == 7L, nrow(broad_status) == 42L,
    !any(all_status$terminal_status == "failed"),
    all(fine_status$terminal_status[fine_status$eligibility_status == "eligible"] %in% c("completed", "not_estimable")),
    all(pooled_status$terminal_status[pooled_status$eligibility_status == "eligible"] %in% c("completed", "not_estimable")),
    all(broad_status$terminal_status[broad_status$eligibility_status == "eligible"] %in% c("completed", "not_estimable")),
    all_statistics_finite, all_bh_reproduced, all_replay_reproduced,
    all(file.exists(file.path(project_root, all_status$result_path[all_status$terminal_status == "completed"])))
  ),
  observed = c(
    nrow(fine_status), nrow(pooled_status), nrow(broad_status), sum(all_status$terminal_status == "failed"),
    TRUE, TRUE, TRUE, all_statistics_finite, all_bh_reproduced, all_replay_reproduced,
    sum(file.exists(file.path(project_root, all_status$result_path[all_status$terminal_status == "completed"])))
  ),
  expected = c(774, 7, 42, 0, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, sum(all_status$terminal_status == "completed")),
  details = "",
  stringsAsFactors = FALSE
)
atomic_fwrite(run_checks, file.path(output_dir, "run_checks.tsv"))
failed <- run_checks$check[!run_checks$passed]
run_state <- if (length(failed)) "failed" else "worker_complete"
run_status <- data.frame(
  schema_version = "seaad_deg_run_status_v2", task = "VH08_edgeR_runner",
  task_status = run_state, failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  fine_completed = sum(fine_status$terminal_status == "completed"),
  fine_no_genes_after_filter = sum(fine_status$terminal_reason == "no_genes_after_filterByExpr"),
  pooled_completed = sum(pooled_status$terminal_status == "completed"),
  broad_stratified_completed = sum(broad_status$terminal_status == "completed"),
  config_sha256 = sha256_file(config_path),
  stringsAsFactors = FALSE
)
atomic_fwrite(run_status, file.path(output_dir, "run_status.tsv"))
cat("VH08 runner: ", run_state, "; fine completed=", run_status$fine_completed, "
", sep = "")
if (length(failed)) quit(status = 2L)
