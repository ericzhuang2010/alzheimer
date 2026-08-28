#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)

args <- phase08_parse_cli(commandArgs(trailingOnly = TRUE), allow = character())
if (isTRUE(args$help)) {
  cat(
    "Usage: Rscript scripts/08_finalize_broad_deg.R ",
    "[--config FILE] [--profile local_pilot|minerva_production]\n",
    sep = ""
  )
  quit(status = 0L)
}

context <- phase08_load_context(args$config, args$profile, include_model = FALSE)
input_dir <- file.path(context$output_root, "00_inputs")
deg_dir <- file.path(context$output_root, "03_deg")
contrast_dir <- file.path(context$output_root, "05_by_contrast")
dir.create(contrast_dir, recursive = TRUE, showWarnings = FALSE)

model_status_path <- file.path(deg_dir, "broad_deg_model_stage_status.tsv")
unannotated_path <- file.path(deg_dir, "broad_deg_unannotated.tsv.gz")
manifest_path <- file.path(input_dir, "broad_deg_contrast_manifest.tsv")
contrast_status_path <- file.path(context$output_root, "broad_deg_contrast_status.tsv")
for (path in c(model_status_path, unannotated_path, manifest_path, contrast_status_path)) {
  if (!file.exists(path)) phase08_abort(paste("Required model-stage file is missing:", path))
}
model_status <- data.table::fread(model_status_path, data.table = FALSE)
phase08_assert(
  nrow(model_status) == 1L && identical(model_status$validation_status[[1L]], "validated_complete"),
  "Broad DEG model stage must be validated_complete"
)
manifest <- data.table::fread(manifest_path, data.table = FALSE)
contrast_status <- data.table::fread(contrast_status_path, data.table = FALSE)
results <- data.table::fread(unannotated_path, data.table = FALSE)

annotation <- phase08_read_annotation(context)
annotation_index <- match(results$gene, annotation$feature_id_original)
phase08_assert(!anyNA(annotation_index), "One or more tested genes are absent from Phase 09 annotation")
annotation_fields <- setdiff(names(annotation), "feature_id_original")
for (field in annotation_fields) results[[field]] <- annotation[[field]][annotation_index]
results$mapped_gene <- as.character(results$symbol_hgnc_current)
missing_symbol <- is.na(results$mapped_gene) | !nzchar(results$mapped_gene)
results$mapped_gene[missing_symbol] <- results$gene[missing_symbol]
results <- phase08_threshold_flags(results, context$config)
results <- results[order(results$manifest_row, results$gene), , drop = FALSE]
row.names(results) <- NULL

results_path <- file.path(context$output_root, "broad_deg_results.tsv.gz")
phase08_atomic_write_tsv_gz(results, results_path)

signature_specs <- list(
  strict = results$strict_deg,
  relaxed = results$relaxed_deg,
  exploratory = results$exploratory_deg
)
signature_paths <- c(
  strict = file.path(context$output_root, "broad_deg_strict_signatures.tsv.gz"),
  relaxed = file.path(context$output_root, "broad_deg_relaxed_signatures.tsv.gz"),
  exploratory = file.path(context$output_root, "broad_deg_exploratory_signatures.tsv.gz")
)
signature_tables <- list()
for (tier in names(signature_specs)) {
  selected <- results[signature_specs[[tier]] & results$direction != "zero", , drop = FALSE]
  selected$signature_tier <- tier
  selected$signature_direction <- ifelse(
    selected$direction == "AD_up", "AD_up_mito", "AD_down_mito"
  )
  selected$schema_version <- "broad_deg_signature_members_v1"
  phase08_atomic_write_tsv_gz(selected, signature_paths[[tier]])
  signature_tables[[tier]] <- selected
}

handoff_parts <- lapply(names(signature_tables), function(tier) {
  table <- signature_tables[[tier]]
  table <- table[table$mito_tier == "core_mito_protein", , drop = FALSE]
  if (!nrow(table)) return(table)
  table$signature_tier <- tier
  table
})
handoff <- as.data.frame(data.table::rbindlist(handoff_parts, fill = TRUE, use.names = TRUE))
handoff_path <- file.path(context$output_root, "broad_core_mito_kda_query_handoff.tsv.gz")
phase08_atomic_write_tsv_gz(handoff, handoff_path)

for (i in seq_len(nrow(manifest))) {
  row <- manifest[i, , drop = FALSE]
  table <- results[results$contrast_id == row$contrast_id, , drop = FALSE]
  filename <- paste0(
    phase08_slug(row$broad_cell_type), "__", phase08_slug(row$group_id),
    ".broad_deg.tsv.gz"
  )
  phase08_atomic_write_tsv_gz(table, file.path(contrast_dir, filename))
}

funnel_rows <- list()
for (i in seq_len(nrow(manifest))) {
  row <- manifest[i, , drop = FALSE]
  table <- results[results$contrast_id == row$contrast_id, , drop = FALSE]
  for (tier in names(signature_specs)) {
    flag_name <- paste0(tier, "_deg")
    for (direction in c("AD_up", "AD_down")) {
      selected <- table[[flag_name]] & table$direction == direction
      funnel_rows[[length(funnel_rows) + 1L]] <- data.frame(
        schema_version = "broad_deg_filter_funnel_v1",
        manifest_row = as.integer(row$manifest_row), contrast_id = row$contrast_id,
        broad_cell_type = row$broad_cell_type, group_id = row$group_id,
        terminal_status = contrast_status$terminal_status[
          match(row$manifest_row, contrast_status$manifest_row)
        ],
        signature_tier = tier, direction = direction,
        tested_genes = nrow(table),
        deg_genes = sum(selected),
        core_mito_deg_genes = sum(selected & table$mito_tier == "core_mito_protein"),
        mtdna_deg_genes = sum(selected & phase08_as_logical(table$is_mtDNA_gene)),
        stringsAsFactors = FALSE
      )
    }
  }
}
filter_funnel <- do.call(rbind, funnel_rows)
funnel_path <- file.path(context$output_root, "broad_deg_filter_funnel.tsv")
phase08_atomic_write_tsv(filter_funnel, funnel_path)

stage_checks <- data.frame(
  schema_version = "broad_deg_finalize_stage_checks_v1",
  check = c(
    "all_results_annotated", "result_keys_unique", "strict_implies_exploratory",
    "relaxed_implies_exploratory", "handoff_core_mito_only",
    "physical_contrast_file_count", "all_structural_contrasts_in_funnel"
  ),
  passed = c(
    !anyNA(annotation_index),
    !anyDuplicated(paste(results$contrast_id, results$gene, sep = "\r")),
    all(!results$strict_deg | results$exploratory_deg),
    all(!results$relaxed_deg | results$exploratory_deg),
    !nrow(handoff) || all(handoff$mito_tier == "core_mito_protein"),
    length(list.files(contrast_dir, pattern = "[.]broad_deg[.]tsv[.]gz$")) == nrow(manifest),
    length(unique(filter_funnel$contrast_id)) == nrow(manifest)
  ),
  stringsAsFactors = FALSE
)
stage_checks_path <- file.path(deg_dir, "broad_deg_finalize_stage_checks.tsv")
phase08_atomic_write_tsv(stage_checks, stage_checks_path)
failed_checks <- stage_checks$check[!stage_checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

stage_status <- data.frame(
  schema_version = "broad_deg_finalize_stage_status_v1",
  profile = context$profile_name,
  execution_stage = context$profile$execution_stage,
  run_id = context$profile$run_id,
  result_rows = nrow(results),
  strict_degs = sum(results$strict_deg),
  relaxed_degs = sum(results$relaxed_deg),
  exploratory_degs = sum(results$exploratory_deg),
  strict_core_mito_degs = sum(results$strict_deg & results$mito_tier == "core_mito_protein"),
  relaxed_core_mito_degs = sum(results$relaxed_deg & results$mito_tier == "core_mito_protein"),
  exploratory_core_mito_degs = sum(results$exploratory_deg & results$mito_tier == "core_mito_protein"),
  physical_contrast_files = length(list.files(
    contrast_dir, pattern = "[.]broad_deg[.]tsv[.]gz$"
  )),
  annotation_master_sha256 = phase08_sha256_file(context$annotation_master),
  annotation_status_sha256 = phase08_sha256_file(context$annotation_status),
  model_status_sha256 = phase08_sha256_file(model_status_path),
  scientific_script = "scripts/08_finalize_broad_deg.R",
  scientific_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/08_finalize_broad_deg.R")
  ),
  peak_ram_gib = phase08_peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
phase08_atomic_write_tsv(
  stage_status, file.path(deg_dir, "broad_deg_finalize_stage_status.tsv")
)

cat("Final broad DEG results: ", results_path, "\n", sep = "")
cat("Physical contrast result sets: ", nrow(manifest), "\n", sep = "")
cat("Strict DEGs: ", sum(results$strict_deg), "\n", sep = "")
cat("Relaxed DEGs: ", sum(results$relaxed_deg), "\n", sep = "")
cat("Exploratory DEGs: ", sum(results$exploratory_deg), "\n", sep = "")
cat("Core-mito handoff rows: ", nrow(handoff), "\n", sep = "")
cat("Validation status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) quit(status = 2L)
