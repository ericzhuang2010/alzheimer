#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)

args <- phase08_parse_cli(commandArgs(trailingOnly = TRUE), allow = c("--resume"))
if (isTRUE(args$help)) {
  cat(
    "Usage: Rscript scripts/08_run_broad_deg_composition_sensitivity.R ",
    "[--config FILE] [--profile local_pilot|minerva_production] [--resume]\n",
    sep = ""
  )
  quit(status = 0L)
}

context <- phase08_load_context(args$config, args$profile, include_model = TRUE)
sensitivity_config <- context$config$composition_sensitivity
phase08_assert(isTRUE(sensitivity_config$enabled), "Composition sensitivity is disabled")
input_dir <- file.path(context$output_root, "00_inputs")
broad_dir <- file.path(context$output_root, "02_broad_pseudobulk")
deg_dir <- file.path(context$output_root, "03_deg")
sensitivity_dir <- file.path(context$output_root, "04_sensitivity")
dir.create(sensitivity_dir, recursive = TRUE, showWarnings = FALSE)

manifest_path <- file.path(input_dir, "broad_deg_contrast_manifest.tsv")
composition_path <- file.path(broad_dir, "broad_fine_type_composition.tsv.gz")
primary_path <- file.path(deg_dir, "broad_deg_unannotated.tsv.gz")
model_status_path <- file.path(deg_dir, "broad_deg_model_stage_status.tsv")
for (path in c(manifest_path, composition_path, primary_path, model_status_path)) {
  if (!file.exists(path)) phase08_abort(paste("Sensitivity prerequisite is missing:", path))
}
model_status <- data.table::fread(model_status_path, data.table = FALSE)
phase08_assert(
  nrow(model_status) == 1L && identical(model_status$validation_status[[1L]], "validated_complete"),
  "Primary broad DEG model must be validated_complete"
)

stage_status_path <- file.path(sensitivity_dir, "broad_deg_sensitivity_stage_status.tsv")
result_path <- file.path(sensitivity_dir, "broad_deg_composition_adjusted.tsv.gz")
if (isTRUE(args$resume) && file.exists(stage_status_path) && file.exists(result_path)) {
  old <- data.table::fread(stage_status_path, data.table = FALSE)
  current <- nrow(old) == 1L &&
    identical(old$validation_status[[1L]], "validated_complete") &&
    identical(old$config_sha256[[1L]], phase08_sha256_file(context$config_path)) &&
    identical(old$model_status_sha256[[1L]], phase08_sha256_file(model_status_path)) &&
    identical(old$composition_sha256[[1L]], phase08_sha256_file(composition_path)) &&
    identical(old$scientific_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/08_run_broad_deg_composition_sensitivity.R")
    )) &&
    identical(old$helper_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
    ))
  if (isTRUE(current)) {
    cat("Composition sensitivity stage is current; resume skipped refit\n")
    quit(status = 0L)
  }
}

manifest <- data.table::fread(manifest_path, data.table = FALSE)
composition <- data.table::fread(
  composition_path, colClasses = c(projid = "character"), data.table = FALSE
)
primary <- data.table::fread(primary_path, data.table = FALSE)
max_pcs <- as.integer(sensitivity_config$maximum_pcs)
pseudocount <- as.numeric(sensitivity_config$zero_pseudocount_nuclei)
phase08_assert(is.finite(pseudocount) && pseudocount > 0,
               "Composition zero pseudocount must be positive")

result_list <- list()
status_list <- list()
diagnostic_list <- list()

add_status <- function(row, terminal_status, genes_returned = 0L, pcs = 0L, message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "broad_deg_sensitivity_contrast_status_v1",
    manifest_row = as.integer(row$manifest_row), contrast_id = as.character(row$contrast_id),
    broad_cell_type = as.character(row$broad_cell_type), group_id = as.character(row$group_id),
    primary_modeling_status = as.character(row$modeling_status),
    terminal_status = terminal_status, composition_pcs = as.integer(pcs),
    genes_returned = as.integer(genes_returned), message = as.character(message),
    stringsAsFactors = FALSE
  )
}

for (broad in context$broad_types) {
  bundle_path <- file.path(broad_dir, paste0(broad, ".broad_pseudobulk_counts.rds"))
  bundle <- readRDS(bundle_path)
  metadata <- as.data.frame(bundle$samples)
  sample_index <- which(phase08_as_logical(metadata$primary_eligible))
  metadata <- metadata[sample_index, , drop = FALSE]
  counts <- bundle$counts[, sample_index, drop = FALSE]
  broad_manifest <- manifest[manifest$broad_cell_type == broad, , drop = FALSE]
  broad_composition <- composition[
    composition$broad_cell_type == broad & composition$projid %in% metadata$projid,
    , drop = FALSE
  ]
  fine_types <- sort(unique(broad_composition$fine_cell_type), method = "radix")
  if (length(fine_types) < 2L) {
    message_text <- "not_applicable_single_fine_cell_type"
    for (i in seq_len(nrow(broad_manifest))) {
      add_status(broad_manifest[i, , drop = FALSE], "not_applicable", message = message_text)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_sensitivity_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), fine_cell_types = length(fine_types),
      composition_pcs = 0L, design_rank = NA_integer_, design_columns = "",
      tested_genes = 0L, model_status = "not_applicable", message = message_text,
      stringsAsFactors = FALSE
    )
    next
  }

  composition_dt <- data.table::as.data.table(broad_composition)
  wide <- data.table::dcast(
    composition_dt, projid ~ fine_cell_type,
    value.var = "fine_type_nuclei", fill = 0, fun.aggregate = sum
  )
  wide_index <- match(metadata$projid, wide$projid)
  phase08_assert(!anyNA(wide_index), paste("Composition matrix misses donors for", broad))
  composition_counts <- as.matrix(wide[wide_index, fine_types, with = FALSE])
  storage.mode(composition_counts) <- "double"
  adjusted <- composition_counts + pseudocount
  proportions <- adjusted / rowSums(adjusted)
  log_proportions <- log(proportions)
  clr <- log_proportions - rowMeans(log_proportions)
  variable_columns <- apply(clr, 2L, stats::sd) > sqrt(.Machine$double.eps)
  clr <- clr[, variable_columns, drop = FALSE]
  if (ncol(clr) < 2L) {
    message_text <- "not_applicable_insufficient_composition_variation"
    for (i in seq_len(nrow(broad_manifest))) {
      add_status(broad_manifest[i, , drop = FALSE], "not_applicable", message = message_text)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_sensitivity_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), fine_cell_types = length(fine_types),
      composition_pcs = 0L, design_rank = NA_integer_, design_columns = "",
      tested_genes = 0L, model_status = "not_applicable", message = message_text,
      stringsAsFactors = FALSE
    )
    next
  }
  pca <- stats::prcomp(clr, center = TRUE, scale. = FALSE)
  nonzero_pcs <- sum(pca$sdev > sqrt(.Machine$double.eps))
  npc <- min(max_pcs, nonzero_pcs, ncol(clr) - 1L)
  if (npc < 1L) phase08_abort(paste("No estimable composition PC for", broad))
  pc_names <- paste0("composition_PC", seq_len(npc))
  for (i in seq_len(npc)) metadata[[pc_names[[i]]]] <- pca$x[, i]

  metadata$group_label <- paste(metadata$diagnosis, metadata$sex, metadata$apoe_group, sep = "__")
  metadata$group <- factor(metadata$group_label)
  formula <- stats::as.formula(paste(
    "~ 0 + group +",
    paste(c(unlist(context$config$analysis$covariates, use.names = FALSE), pc_names), collapse = " + ")
  ))
  design <- stats::model.matrix(formula, data = metadata)
  group_columns <- seq_len(nlevels(metadata$group))
  colnames(design)[group_columns] <- levels(metadata$group)
  design_rank <- qr(design)$rank
  if (design_rank < ncol(design)) {
    message_text <- paste0("composition_design_rank_deficient:", design_rank, "_of_", ncol(design))
    for (i in seq_len(nrow(broad_manifest))) {
      add_status(broad_manifest[i, , drop = FALSE], "failed", pcs = npc, message = message_text)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_sensitivity_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), fine_cell_types = length(fine_types),
      composition_pcs = npc, design_rank = design_rank,
      design_columns = paste(colnames(design), collapse = ";"), tested_genes = 0L,
      model_status = "failed", message = message_text, stringsAsFactors = FALSE
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
    for (i in seq_len(nrow(broad_manifest))) {
      add_status(broad_manifest[i, , drop = FALSE], "failed", pcs = npc, message = fit_error)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "broad_deg_sensitivity_model_diagnostics_v1",
      broad_cell_type = broad, samples = nrow(metadata), fine_cell_types = length(fine_types),
      composition_pcs = npc, design_rank = design_rank,
      design_columns = paste(colnames(design), collapse = ";"), tested_genes = 0L,
      model_status = "failed", message = fit_error, stringsAsFactors = FALSE
    )
    next
  }
  y <- fit_objects$y
  fit <- fit_objects$fit
  diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
    schema_version = "broad_deg_sensitivity_model_diagnostics_v1",
    broad_cell_type = broad, samples = nrow(metadata), fine_cell_types = length(fine_types),
    composition_pcs = npc, design_rank = design_rank,
    design_columns = paste(colnames(design), collapse = ";"), tested_genes = nrow(y$counts),
    model_status = "fitted", message = "", stringsAsFactors = FALSE
  )

  for (i in seq_len(nrow(broad_manifest))) {
    row <- broad_manifest[i, , drop = FALSE]
    if (row$modeling_status != "estimable") {
      add_status(row, "not_estimable", pcs = npc, message = row$modeling_reason)
      next
    }
    test_error <- NULL
    test <- tryCatch(
      edgeR::glmQLFTest(fit, contrast = phase08_contrast_vector(row, colnames(design))),
      error = function(e) {
        test_error <<- conditionMessage(e)
        NULL
      }
    )
    if (is.null(test)) {
      add_status(row, "failed", pcs = npc, message = test_error)
      next
    }
    table <- edgeR::topTags(test, n = Inf, sort.by = "none")$table
    p_value <- as.numeric(table$PValue)
    result <- data.frame(
      schema_version = "broad_deg_composition_sensitivity_results_v1",
      manifest_row = as.integer(row$manifest_row), contrast_id = as.character(row$contrast_id),
      broad_cell_type = broad, group_id = as.character(row$group_id),
      gene = rownames(table), logFC = as.numeric(table$logFC),
      logCPM = as.numeric(table$logCPM), F = as.numeric(table$F),
      p_value = p_value,
      fdr_bh_within_contrast = stats::p.adjust(p_value, method = "BH"),
      composition_transform = "centered_log_ratio",
      composition_zero_pseudocount_nuclei = pseudocount,
      composition_pcs = npc, composition_pc_names = paste(pc_names, collapse = ";"),
      stringsAsFactors = FALSE
    )
    result <- phase08_threshold_flags(result, context$config)
    result_list[[length(result_list) + 1L]] <- result
    add_status(row, "validated_complete", nrow(result), npc)
  }
  rm(y, fit, counts)
  invisible(gc())
}

results <- as.data.frame(data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE))
if (nrow(results)) results <- results[order(results$manifest_row, results$gene), , drop = FALSE]
status <- as.data.frame(data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE))
status <- status[order(status$manifest_row), , drop = FALSE]
diagnostics <- as.data.frame(data.table::rbindlist(diagnostic_list, fill = TRUE, use.names = TRUE))

phase08_atomic_write_tsv_gz(results, result_path)
status_path <- file.path(sensitivity_dir, "broad_deg_sensitivity_contrast_status.tsv")
diagnostics_path <- file.path(sensitivity_dir, "broad_deg_sensitivity_model_diagnostics.tsv")
phase08_atomic_write_tsv(status, status_path)
phase08_atomic_write_tsv(diagnostics, diagnostics_path)

summary_rows <- lapply(seq_len(nrow(manifest)), function(i) {
  row <- manifest[i, , drop = FALSE]
  primary_chunk <- primary[primary$contrast_id == row$contrast_id, , drop = FALSE]
  sensitivity_chunk <- results[results$contrast_id == row$contrast_id, , drop = FALSE]
  joined <- merge(
    primary_chunk[, c("gene", "logFC"), drop = FALSE],
    sensitivity_chunk[, c("gene", "logFC"), drop = FALSE],
    by = "gene", suffixes = c("_primary", "_sensitivity")
  )
  data.frame(
    schema_version = "broad_deg_sensitivity_summary_v1",
    manifest_row = as.integer(row$manifest_row), contrast_id = row$contrast_id,
    broad_cell_type = row$broad_cell_type, group_id = row$group_id,
    sensitivity_terminal_status = status$terminal_status[
      match(row$manifest_row, status$manifest_row)
    ],
    shared_tested_genes = nrow(joined),
    logFC_pearson = if (nrow(joined) >= 3L) stats::cor(joined$logFC_primary, joined$logFC_sensitivity) else NA_real_,
    sign_concordance = if (nrow(joined)) mean(sign(joined$logFC_primary) == sign(joined$logFC_sensitivity)) else NA_real_,
    primary_strict_degs = if (nrow(primary_chunk)) sum(phase08_threshold_flags(primary_chunk, context$config)$strict_deg) else 0L,
    sensitivity_strict_degs = if (nrow(sensitivity_chunk)) sum(sensitivity_chunk$strict_deg) else 0L,
    primary_relaxed_degs = if (nrow(primary_chunk)) sum(phase08_threshold_flags(primary_chunk, context$config)$relaxed_deg) else 0L,
    sensitivity_relaxed_degs = if (nrow(sensitivity_chunk)) sum(sensitivity_chunk$relaxed_deg) else 0L,
    stringsAsFactors = FALSE
  )
})
summary <- do.call(rbind, summary_rows)
summary_path <- file.path(sensitivity_dir, "broad_deg_sensitivity_summary.tsv")
phase08_atomic_write_tsv(summary, summary_path)

result_keys <- paste(results$contrast_id, results$gene, sep = "\r")
checks <- data.frame(
  schema_version = "broad_deg_sensitivity_checks_v1",
  check = c(
    "one_status_per_manifest", "no_failed_sensitivity_contrasts",
    "result_keys_unique", "p_values_in_range", "diagnosis_blind_pcs",
    "summary_covers_manifest"
  ),
  passed = c(
    nrow(status) == nrow(manifest) && !anyDuplicated(status$manifest_row),
    !any(status$terminal_status == "failed"),
    !anyDuplicated(result_keys),
    !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1),
    isTRUE(sensitivity_config$diagnosis_blind),
    nrow(summary) == nrow(manifest) && !anyDuplicated(summary$manifest_row)
  ),
  stringsAsFactors = FALSE
)
checks_path <- file.path(sensitivity_dir, "broad_deg_sensitivity_checks.tsv")
phase08_atomic_write_tsv(checks, checks_path)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

stage_status <- data.frame(
  schema_version = "broad_deg_sensitivity_stage_status_v1",
  profile = context$profile_name, execution_stage = context$profile$execution_stage,
  run_id = context$profile$run_id,
  structural_contrasts = nrow(manifest),
  completed_contrasts = sum(status$terminal_status == "validated_complete"),
  not_estimable_contrasts = sum(status$terminal_status == "not_estimable"),
  not_applicable_contrasts = sum(status$terminal_status == "not_applicable"),
  failed_contrasts = sum(status$terminal_status == "failed"),
  result_rows = nrow(results),
  transform = sensitivity_config$transform,
  zero_pseudocount_nuclei = pseudocount, maximum_pcs = max_pcs,
  diagnosis_blind = isTRUE(sensitivity_config$diagnosis_blind),
  config_sha256 = phase08_sha256_file(context$config_path),
  model_status_sha256 = phase08_sha256_file(model_status_path),
  composition_sha256 = phase08_sha256_file(composition_path),
  scientific_script = "scripts/08_run_broad_deg_composition_sensitivity.R",
  scientific_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/08_run_broad_deg_composition_sensitivity.R")
  ),
  helper_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
  ),
  peak_ram_gib = phase08_peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status, failed_checks = paste(failed_checks, collapse = ";"),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
phase08_atomic_write_tsv(stage_status, stage_status_path)

cat("Composition-adjusted sensitivity results: ", result_path, "\n", sep = "")
cat("Completed sensitivity contrasts: ", sum(status$terminal_status == "validated_complete"), "\n", sep = "")
cat("Not estimable/applicable: ",
    sum(status$terminal_status %in% c("not_estimable", "not_applicable")), "\n", sep = "")
cat("Sensitivity result rows: ", nrow(results), "\n", sep = "")
cat("Validation status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) quit(status = 2L)
