#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)

args <- phase08_parse_cli(commandArgs(trailingOnly = TRUE), allow = c("--resume"))
if (isTRUE(args$help)) {
  cat(
    "Usage: Rscript scripts/08_run_broad_pseudobulk_de.R ",
    "[--config FILE] [--profile local_pilot|minerva_production] [--resume]\n",
    sep = ""
  )
  quit(status = 0L)
}

context <- phase08_load_context(args$config, args$profile, include_model = TRUE)
input_dir <- file.path(context$output_root, "00_inputs")
broad_dir <- file.path(context$output_root, "02_broad_pseudobulk")
deg_dir <- file.path(context$output_root, "03_deg")
dir.create(input_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(deg_dir, recursive = TRUE, showWarnings = FALSE)

build_status_path <- file.path(broad_dir, "broad_pseudobulk_stage_status.tsv")
if (!file.exists(build_status_path)) phase08_abort("Broad pseudobulk stage status is missing")
build_status <- data.table::fread(build_status_path, data.table = FALSE)
phase08_assert(
  nrow(build_status) == 1L && identical(build_status$validation_status[[1L]], "validated_complete"),
  "Broad pseudobulk stage must be validated_complete"
)

stage_status_path <- file.path(deg_dir, "broad_deg_model_stage_status.tsv")
unannotated_path <- file.path(deg_dir, "broad_deg_unannotated.tsv.gz")
if (isTRUE(args$resume) && file.exists(stage_status_path) && file.exists(unannotated_path)) {
  old_status <- data.table::fread(stage_status_path, data.table = FALSE)
  current <- nrow(old_status) == 1L &&
    identical(old_status$validation_status[[1L]], "validated_complete") &&
    identical(old_status$config_sha256[[1L]], phase08_sha256_file(context$config_path)) &&
    identical(old_status$build_status_sha256[[1L]], phase08_sha256_file(build_status_path)) &&
    identical(old_status$scientific_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/08_run_broad_pseudobulk_de.R")
    )) &&
    identical(old_status$helper_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
    ))
  if (isTRUE(current)) {
    cat("Broad DEG model stage is current; resume skipped refit\n")
    quit(status = 0L)
  }
}

broad_bundles <- list()
sample_list <- list()
for (broad in context$broad_types) {
  path <- file.path(broad_dir, paste0(broad, ".broad_pseudobulk_counts.rds"))
  if (!file.exists(path)) phase08_abort(paste("Broad count bundle is missing:", path))
  bundle <- readRDS(path)
  phase08_assert(identical(bundle$schema_version, "broad_pseudobulk_counts_v1"),
                 paste("Unsupported broad bundle schema:", broad))
  phase08_assert(identical(bundle$broad_cell_type, broad),
                 paste("Broad bundle identity mismatch:", broad))
  phase08_assert(inherits(bundle$counts, "sparseMatrix"),
                 paste("Broad counts are not sparse:", broad))
  phase08_assert(identical(colnames(bundle$counts), bundle$samples$broad_pseudobulk_id),
                 paste("Broad count/sample order mismatch:", broad))
  broad_bundles[[broad]] <- bundle
  sample_list[[broad]] <- bundle$samples
}
all_samples <- do.call(rbind, sample_list)
manifest <- phase08_build_contrast_manifest(all_samples, context)
phase08_assert(nrow(manifest) == as.integer(context$profile$expected_contrasts),
               "Contrast manifest does not have the expected profile size")
manifest_path <- file.path(input_dir, "broad_deg_contrast_manifest.tsv")
phase08_atomic_write_tsv(manifest, manifest_path)

result_list <- list()
status_list <- list()
diagnostic_list <- list()

add_status <- function(row, terminal_status, genes_returned = 0L, message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "broad_deg_contrast_status_v1",
    manifest_row = as.integer(row$manifest_row),
    contrast_id = as.character(row$contrast_id),
    broad_cell_type = as.character(row$broad_cell_type),
    group_id = as.character(row$group_id),
    sex = as.character(row$sex), apoe_group = as.character(row$apoe_group),
    manifest_modeling_status = as.character(row$modeling_status),
    terminal_status = terminal_status,
    donors_ad = as.integer(row$donors_ad), donors_nci = as.integer(row$donors_nci),
    nuclei_ad = as.integer(row$nuclei_ad), nuclei_nci = as.integer(row$nuclei_nci),
    genes_returned = as.integer(genes_returned), message = as.character(message),
    stringsAsFactors = FALSE
  )
}

for (broad in context$broad_types) {
  message("Fitting broad-cell edgeR QL model: ", broad)
  bundle <- broad_bundles[[broad]]
  metadata <- as.data.frame(bundle$samples)
  sample_index <- which(phase08_as_logical(metadata$primary_eligible))
  metadata <- metadata[sample_index, , drop = FALSE]
  counts <- bundle$counts[, sample_index, drop = FALSE]
  covariates <- unlist(context$config$analysis$covariates, use.names = FALSE)
  finite_covariates <- !anyNA(metadata[, covariates, drop = FALSE]) && all(vapply(
    metadata[, covariates, drop = FALSE],
    function(x) all(is.finite(as.numeric(x))), logical(1)
  ))
  broad_manifest <- manifest[manifest$broad_cell_type == broad, , drop = FALSE]
  if (!finite_covariates) {
    message_text <- "required_covariates_incomplete_or_nonfinite"
    for (i in seq_len(nrow(broad_manifest))) add_status(broad_manifest[i, , drop = FALSE], "failed", message = message_text)
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), donors = length(unique(metadata$projid)),
      input_genes = nrow(counts), tested_genes = 0L, design_columns = "",
      design_rank = 0L, residual_df_min = NA_real_, model_status = "failed",
      message = message_text, stringsAsFactors = FALSE
    )
    next
  }
  metadata$group_label <- paste(metadata$diagnosis, metadata$sex, metadata$apoe_group, sep = "__")
  metadata$group <- factor(metadata$group_label)
  design <- stats::model.matrix(
    ~ 0 + group + age_death_scaled + pmi_scaled,
    data = metadata
  )
  group_columns <- seq_len(nlevels(metadata$group))
  colnames(design)[group_columns] <- levels(metadata$group)
  design_rank <- qr(design)$rank
  if (design_rank < ncol(design)) {
    message_text <- paste0("design_rank_deficient:", design_rank, "_of_", ncol(design))
    for (i in seq_len(nrow(broad_manifest))) add_status(broad_manifest[i, , drop = FALSE], "failed", message = message_text)
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), donors = length(unique(metadata$projid)),
      input_genes = nrow(counts), tested_genes = 0L,
      design_columns = paste(colnames(design), collapse = ";"),
      design_rank = design_rank, residual_df_min = NA_real_, model_status = "failed",
      message = message_text, stringsAsFactors = FALSE
    )
    next
  }

  fit_error <- NULL
  fit_objects <- tryCatch({
    y <- edgeR::DGEList(counts = as.matrix(counts))
    keep <- edgeR::filterByExpr(y, design = design)
    if (!any(keep)) phase08_abort("filterByExpr retained no genes")
    y <- y[keep, , keep.lib.sizes = FALSE]
    y <- edgeR::calcNormFactors(y, method = "TMM")
    y <- edgeR::estimateDisp(y, design, robust = TRUE)
    fit <- edgeR::glmQLFit(y, design, robust = TRUE)
    list(y = y, fit = fit, keep = keep)
  }, error = function(e) {
    fit_error <<- conditionMessage(e)
    NULL
  })
  if (is.null(fit_objects)) {
    for (i in seq_len(nrow(broad_manifest))) add_status(broad_manifest[i, , drop = FALSE], "failed", message = fit_error)
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), donors = length(unique(metadata$projid)),
      input_genes = nrow(counts), tested_genes = 0L,
      design_columns = paste(colnames(design), collapse = ";"),
      design_rank = design_rank, residual_df_min = NA_real_, model_status = "failed",
      message = fit_error, stringsAsFactors = FALSE
    )
    next
  }
  y <- fit_objects$y
  fit <- fit_objects$fit
  keep <- fit_objects$keep
  residual_df_min <- min(fit$df.residual.zeros %||% fit$df.residual)
  diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
    schema_version = "broad_deg_model_diagnostics_v1",
    broad_cell_type = broad, samples = nrow(metadata), donors = length(unique(metadata$projid)),
    input_genes = nrow(counts), tested_genes = sum(keep),
    design_columns = paste(colnames(design), collapse = ";"),
    design_rank = design_rank, residual_df_min = residual_df_min,
    model_status = "fitted", message = "", stringsAsFactors = FALSE
  )

  broad_results <- list()
  for (i in seq_len(nrow(broad_manifest))) {
    row <- broad_manifest[i, , drop = FALSE]
    if (row$modeling_status != "estimable") {
      add_status(row, "not_estimable", message = row$modeling_reason)
      next
    }
    test_error <- NULL
    test_result <- tryCatch({
      contrast <- phase08_contrast_vector(row, colnames(design))
      test <- edgeR::glmQLFTest(fit, contrast = contrast)
      table <- edgeR::topTags(test, n = Inf, sort.by = "none")$table
      list(test = test, table = table)
    }, error = function(e) {
      test_error <<- conditionMessage(e)
      NULL
    })
    if (is.null(test_result)) {
      add_status(row, "failed", message = test_error)
      next
    }
    table <- test_result$table
    test <- test_result$test
    relevant <- metadata$sex == row$sex &
      metadata$apoe_group == row$apoe_group &
      metadata$diagnosis %in% c(row$numerator, row$denominator)
    detection_rate <- rowMeans(y$counts[, relevant, drop = FALSE] > 0)
    log_fc <- as.numeric(table$logFC)
    f_statistic <- as.numeric(table$F)
    standard_error <- rep(NA_real_, length(log_fc))
    positive_f <- is.finite(f_statistic) & f_statistic > 0
    standard_error[positive_f] <- abs(log_fc[positive_f]) / sqrt(f_statistic[positive_f])
    df_total <- as.numeric(test$df.total)
    if (length(df_total) == 1L) df_total <- rep(df_total, length(log_fc))
    critical <- stats::qt(0.975, df = df_total)
    p_value <- as.numeric(table$PValue)
    result <- data.frame(
      schema_version = "broad_deg_results_v1",
      manifest_row = as.integer(row$manifest_row),
      contrast_id = as.character(row$contrast_id),
      broad_cell_type = broad, group_id = as.character(row$group_id),
      sex = as.character(row$sex), apoe_group = as.character(row$apoe_group),
      numerator = as.character(row$numerator), denominator = as.character(row$denominator),
      gene = rownames(table), logFC = log_fc,
      standard_error = standard_error,
      ci95_low = log_fc - critical * standard_error,
      ci95_high = log_fc + critical * standard_error,
      logCPM = as.numeric(table$logCPM), F = f_statistic,
      p_value = p_value,
      fdr_bh_within_contrast = stats::p.adjust(p_value, method = "BH"),
      detection_rate_required_groups = as.numeric(detection_rate[rownames(table)]),
      donors_ad = as.integer(row$donors_ad), donors_nci = as.integer(row$donors_nci),
      nuclei_ad = as.integer(row$nuclei_ad), nuclei_nci = as.integer(row$nuclei_nci),
      model_samples = nrow(metadata), model_donors = length(unique(metadata$projid)),
      stringsAsFactors = FALSE
    )
    broad_results[[length(broad_results) + 1L]] <- result
    result_list[[length(result_list) + 1L]] <- result
    add_status(row, "validated_complete", genes_returned = nrow(result))
  }
  per_broad <- if (length(broad_results)) {
    as.data.frame(data.table::rbindlist(broad_results, fill = TRUE, use.names = TRUE))
  } else {
    data.frame()
  }
  phase08_atomic_write_tsv_gz(
    per_broad, file.path(deg_dir, paste0(broad, ".broad_deg_unannotated.tsv.gz"))
  )
  rm(y, fit, counts)
  invisible(gc())
}

results <- if (length(result_list)) {
  as.data.frame(data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE))
} else {
  data.frame(
    schema_version = character(), manifest_row = integer(), contrast_id = character(),
    broad_cell_type = character(), group_id = character(), sex = character(),
    apoe_group = character(), numerator = character(), denominator = character(),
    gene = character(), logFC = numeric(), standard_error = numeric(), ci95_low = numeric(),
    ci95_high = numeric(), logCPM = numeric(), F = numeric(), p_value = numeric(),
    fdr_bh_within_contrast = numeric(), detection_rate_required_groups = numeric(),
    donors_ad = integer(), donors_nci = integer(), nuclei_ad = integer(), nuclei_nci = integer(),
    model_samples = integer(), model_donors = integer(), stringsAsFactors = FALSE
  )
}
if (nrow(results)) {
  results$fdr_bh_global_all_contrast_genes <- stats::p.adjust(results$p_value, method = "BH")
  results <- results[order(results$manifest_row, results$gene), , drop = FALSE]
  row.names(results) <- NULL
} else {
  results$fdr_bh_global_all_contrast_genes <- numeric()
}
contrast_status <- as.data.frame(data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE))
contrast_status <- contrast_status[order(contrast_status$manifest_row), , drop = FALSE]
diagnostics <- as.data.frame(data.table::rbindlist(diagnostic_list, fill = TRUE, use.names = TRUE))

status_path <- file.path(context$output_root, "broad_deg_contrast_status.tsv")
diagnostics_path <- file.path(context$output_root, "broad_deg_model_diagnostics.tsv")
phase08_atomic_write_tsv_gz(results, unannotated_path)
phase08_atomic_write_tsv(contrast_status, status_path)
phase08_atomic_write_tsv(diagnostics, diagnostics_path)

completed_manifest <- manifest$modeling_status == "estimable"
status_match <- match(manifest$manifest_row, contrast_status$manifest_row)
result_keys <- paste(results$contrast_id, results$gene, sep = "\r")
checks <- data.frame(
  schema_version = "broad_deg_model_stage_checks_v1",
  check = c(
    "manifest_size", "one_terminal_status_per_manifest", "estimable_completed",
    "not_estimable_explicit", "no_failed_contrasts", "result_keys_unique",
    "p_values_in_range", "within_fdr_in_range", "global_fdr_in_range"
  ),
  passed = c(
    nrow(manifest) == as.integer(context$profile$expected_contrasts),
    nrow(contrast_status) == nrow(manifest) && !anyDuplicated(contrast_status$manifest_row),
    all(contrast_status$terminal_status[status_match[completed_manifest]] == "validated_complete"),
    all(contrast_status$terminal_status[status_match[!completed_manifest]] == "not_estimable"),
    !any(contrast_status$terminal_status == "failed"),
    !anyDuplicated(result_keys),
    !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1),
    !nrow(results) || all(is.finite(results$fdr_bh_within_contrast) & results$fdr_bh_within_contrast >= 0 & results$fdr_bh_within_contrast <= 1),
    !nrow(results) || all(is.finite(results$fdr_bh_global_all_contrast_genes) & results$fdr_bh_global_all_contrast_genes >= 0 & results$fdr_bh_global_all_contrast_genes <= 1)
  ),
  stringsAsFactors = FALSE
)
checks_path <- file.path(deg_dir, "broad_deg_model_stage_checks.tsv")
phase08_atomic_write_tsv(checks, checks_path)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

stage_status <- data.frame(
  schema_version = "broad_deg_model_stage_status_v1",
  profile = context$profile_name,
  execution_stage = context$profile$execution_stage,
  run_id = context$profile$run_id,
  broad_cell_types = length(context$broad_types),
  manifest_rows = nrow(manifest),
  completed_contrasts = sum(contrast_status$terminal_status == "validated_complete"),
  not_estimable_contrasts = sum(contrast_status$terminal_status == "not_estimable"),
  failed_contrasts = sum(contrast_status$terminal_status == "failed"),
  result_rows = nrow(results),
  config_sha256 = phase08_sha256_file(context$config_path),
  build_status_sha256 = phase08_sha256_file(build_status_path),
  manifest_sha256 = phase08_sha256_file(manifest_path),
  scientific_script = "scripts/08_run_broad_pseudobulk_de.R",
  scientific_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/08_run_broad_pseudobulk_de.R")
  ),
  helper_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
  ),
  edgeR_version = as.character(packageVersion("edgeR")),
  limma_version = as.character(packageVersion("limma")),
  peak_ram_gib = phase08_peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
phase08_atomic_write_tsv(stage_status, stage_status_path)

cat("Broad DEG unannotated results: ", unannotated_path, "\n", sep = "")
cat("Contrasts completed: ", sum(contrast_status$terminal_status == "validated_complete"), "\n", sep = "")
cat("Contrasts not estimable: ", sum(contrast_status$terminal_status == "not_estimable"), "\n", sep = "")
cat("Result rows: ", nrow(results), "\n", sep = "")
cat("Validation status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) quit(status = 2L)
