#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/08_run_broad_deg.R --config FILE\n")
      quit(status = 0L)
    }
    if (key != "--config" || i == length(args)) stop("Unknown option or missing value: ", key)
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(
    x, tmp, sep = "\t", na = "NA", quote = FALSE,
    compress = if (grepl("[.]gz$", path)) "gzip" else "none"
  )
  if (!file.rename(tmp, path)) stop("Atomic rename failed: ", path)
}

atomic_save_rds <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  saveRDS(x, tmp, compress = "gzip")
  if (!file.rename(tmp, path)) stop("Atomic rename failed: ", path)
}

sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)

require_status <- function(path) {
  if (!file.exists(path)) stop("Missing upstream status: ", path)
  value <- data.table::fread(path, integer64 = "double")
  if (nrow(value) != 1L || value$validation_status[[1L]] != "validated_complete") {
    stop("Upstream phase is not validated: ", path)
  }
  value
}

prepare_metadata <- function(samples) {
  samples$diagnosis <- factor(samples$diagnosis,
                              levels = c("No dementia", "Dementia"))
  samples$sex <- factor(samples$sex, levels = c("Female", "Male"))
  samples$apoe_group <- factor(samples$apoe_group, levels = c("e33", "e2", "e4"))
  samples$study <- factor(samples$study)
  samples$diagnosis_key <- ifelse(samples$diagnosis == "Dementia",
                                  "Dementia", "No_dementia")
  samples$diagnosis_sex_apoe_group <- factor(
    paste(samples$diagnosis_key, samples$sex, samples$apoe_group, sep = "__")
  )
  samples
}

make_designs <- function(metadata) {
  primary <- model.matrix(
    ~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
  secondary <- model.matrix(
    ~ 0 + diagnosis_sex_apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
  list(primary = primary, secondary = secondary)
}

parse_contrast <- function(serialized, design_columns) {
  vector <- setNames(numeric(length(design_columns)), design_columns)
  if (is.na(serialized) || !nzchar(serialized)) return(vector)
  pieces <- strsplit(serialized, ";", fixed = TRUE)[[1L]]
  for (piece in pieces) {
    pair <- strsplit(piece, "=", fixed = TRUE)[[1L]]
    if (length(pair) != 2L || !pair[[1L]] %in% design_columns) {
      stop("Invalid serialized contrast term: ", piece)
    }
    vector[pair[[1L]]] <- as.numeric(pair[[2L]])
  }
  vector
}

result_from_test <- function(test, keep, annotation, manifest_row) {
  table <- edgeR::topTags(test, n = Inf, sort.by = "none")$table
  feature_indices <- which(keep) - 1L
  if (nrow(table) != length(feature_indices)) stop("edgeR result length mismatch")
  selected_annotation <- annotation[feature_indices + 1L, , drop = FALSE]
  fdr <- p.adjust(table$PValue, method = "BH")
  direction <- ifelse(table$logFC > 0, "AD_up",
                      ifelse(table$logFC < 0, "AD_down", "zero"))
  data.frame(
    contrast_id = manifest_row$contrast_id[[1L]],
    context = manifest_row$context[[1L]],
    contrast_family = manifest_row$contrast_family[[1L]],
    sex = manifest_row$sex[[1L]],
    apoe_group = manifest_row$apoe_group[[1L]],
    dementia_donors = manifest_row$dementia_donors[[1L]],
    no_dementia_donors = manifest_row$no_dementia_donors[[1L]],
    feature_index = feature_indices,
    source_symbol = selected_annotation$source_symbol,
    approved_symbol = selected_annotation$approved_symbol,
    hgnc_id = selected_annotation$hgnc_id,
    gencode_gene_id = selected_annotation$gencode_gene_id,
    chromosome = selected_annotation$chromosome,
    gene_type = selected_annotation$gene_type,
    is_mitocarta = selected_annotation$is_mitocarta,
    is_mtdna_protein_coding = selected_annotation$is_mtdna_protein_coding,
    logFC = table$logFC,
    logCPM = table$logCPM,
    F = table$F,
    PValue = table$PValue,
    FDR = fdr,
    direction = direction,
    test_status = "tested",
    stringsAsFactors = FALSE
  )
}

complete_result <- function(result, annotation, manifest_row) {
  index <- match(annotation$feature_index, result$feature_index)
  tested <- !is.na(index)
  stats <- result[index, c("logFC", "logCPM", "F", "PValue", "FDR", "direction"),
                  drop = FALSE]
  data.frame(
    contrast_id = manifest_row$contrast_id[[1L]],
    context = manifest_row$context[[1L]],
    contrast_family = manifest_row$contrast_family[[1L]],
    sex = manifest_row$sex[[1L]],
    apoe_group = manifest_row$apoe_group[[1L]],
    dementia_donors = manifest_row$dementia_donors[[1L]],
    no_dementia_donors = manifest_row$no_dementia_donors[[1L]],
    feature_index = annotation$feature_index,
    source_symbol = annotation$source_symbol,
    approved_symbol = annotation$approved_symbol,
    hgnc_id = annotation$hgnc_id,
    gencode_gene_id = annotation$gencode_gene_id,
    chromosome = annotation$chromosome,
    gene_type = annotation$gene_type,
    is_mitocarta = annotation$is_mitocarta,
    is_mtdna_protein_coding = annotation$is_mtdna_protein_coding,
    test_status = ifelse(tested, "tested", "filtered"),
    logFC = stats$logFC,
    logCPM = stats$logCPM,
    F = stats$F,
    PValue = stats$PValue,
    FDR = stats$FDR,
    direction = stats$direction,
    stringsAsFactors = FALSE
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "edgeR", "limma", "statmod")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
required_root <- normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)
if (!identical(output_root, required_root)) stop("Output root is not isolated validation_human")
require_status(file.path(output_root, "06_pseudobulk_qc/status.tsv"))
vh07_status <- require_status(file.path(output_root, "07_contrasts/status.tsv"))

bundle <- readRDS(file.path(output_root, "06_pseudobulk_qc/seaad_broad_pseudobulk.rds"))
if (!identical(bundle$schema_version, "seaad_broad_pseudobulk_v1")) stop("Unsupported VH06 bundle")
counts <- bundle$counts
samples <- as.data.frame(bundle$samples)
annotation <- as.data.frame(bundle$genes)
annotation$feature_index <- as.integer(annotation$feature_index)
manifest <- data.table::fread(
  file.path(output_root, "07_contrasts/contrast_manifest.tsv"),
  data.table = FALSE
)
contexts <- unlist(config$broad_context_order)

output_dir <- file.path(output_root, "08_deg")
primary_dir <- file.path(output_dir, "primary")
secondary_dir <- file.path(output_dir, "secondary")
model_dir <- file.path(output_dir, "model_objects")
dir.create(primary_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(secondary_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(model_dir, recursive = TRUE, showWarnings = FALSE)

primary_results <- list()
secondary_results <- list()
primary_complete <- list()
secondary_complete <- list()
filter_rows <- list()
diagnostic_rows <- list()
status_rows <- list()
summary_rows <- list()
per_contrast_paths <- character()
model_paths <- character()

for (context in contexts) {
  context_manifest <- manifest[manifest$context == context, , drop = FALSE]
  sample_index <- which(samples$context == context & samples$primary_eligible)
  metadata <- prepare_metadata(samples[sample_index, , drop = FALSE])
  context_counts <- counts[, sample_index, drop = FALSE]
  if (!identical(colnames(context_counts), metadata$pseudobulk_id)) {
    stop("Count/sample misalignment in context ", context)
  }
  designs <- make_designs(metadata)
  if (qr(designs$primary)$rank != ncol(designs$primary)) {
    stop("Primary design is rank deficient in ", context)
  }
  if (qr(designs$secondary)$rank != ncol(designs$secondary)) {
    stop("Secondary design is rank deficient in ", context)
  }

  y0 <- edgeR::DGEList(counts = context_counts)
  keep <- edgeR::filterByExpr(y0, group = metadata$diagnosis)
  if (!any(keep)) stop("filterByExpr retained no genes in ", context)
  y <- y0[keep, , keep.lib.sizes = FALSE]
  y <- edgeR::calcNormFactors(y, method = "TMM")

  y_primary <- edgeR::estimateDisp(y, designs$primary, robust = TRUE)
  primary_fit <- edgeR::glmQLFit(y_primary, designs$primary, robust = TRUE)
  y_secondary <- edgeR::estimateDisp(y, designs$secondary, robust = TRUE)
  secondary_fit <- edgeR::glmQLFit(y_secondary, designs$secondary, robust = TRUE)

  filter_rows[[length(filter_rows) + 1L]] <- data.frame(
    context = context,
    feature_index = annotation$feature_index,
    source_symbol = annotation$source_symbol,
    filter_by_expr = keep,
    test_status = ifelse(keep, "tested", "filtered"),
    stringsAsFactors = FALSE
  )

  primary_row <- context_manifest[
    context_manifest$contrast_family == "primary", , drop = FALSE
  ]
  if (nrow(primary_row) != 1L || primary_row$eligibility_status[[1L]] != "eligible") {
    stop("Expected exactly one eligible primary contrast in ", context)
  }
  primary_contrast <- parse_contrast(
    primary_row$coefficient_vector[[1L]], colnames(designs$primary)
  )
  primary_test <- edgeR::glmQLFTest(primary_fit, contrast = primary_contrast)
  primary_result <- result_from_test(primary_test, keep, annotation, primary_row)
  primary_path <- file.path(primary_dir, primary_row$output_basename[[1L]])
  atomic_fwrite(primary_result, primary_path)
  per_contrast_paths <- c(per_contrast_paths, primary_path)
  primary_results[[length(primary_results) + 1L]] <- primary_result
  primary_complete[[length(primary_complete) + 1L]] <- complete_result(
    primary_result, annotation, primary_row
  )
  status_rows[[length(status_rows) + 1L]] <- data.frame(
    contrast_id = primary_row$contrast_id,
    context = context,
    contrast_family = "primary",
    sex = NA_character_,
    apoe_group = NA_character_,
    eligibility_status = "eligible",
    terminal_status = "completed",
    genes_returned = nrow(primary_result),
    output_path = sub(paste0("^", project_root, "/?"), "", primary_path),
    message = "",
    stringsAsFactors = FALSE
  )
  summary_rows[[length(summary_rows) + 1L]] <- data.frame(
    contrast_id = primary_row$contrast_id,
    context = context,
    contrast_family = "primary",
    tested_genes = nrow(primary_result),
    filtered_genes = nrow(annotation) - nrow(primary_result),
    fdr_lt_0_05 = sum(primary_result$FDR < 0.05),
    ad_up_tested = sum(primary_result$logFC > 0),
    ad_down_tested = sum(primary_result$logFC < 0),
    stringsAsFactors = FALSE
  )

  secondary_vectors <- list()
  secondary_rows <- context_manifest[
    context_manifest$contrast_family == "secondary", , drop = FALSE
  ]
  for (row_number in seq_len(nrow(secondary_rows))) {
    row <- secondary_rows[row_number, , drop = FALSE]
    if (row$eligibility_status[[1L]] != "eligible") {
      status_rows[[length(status_rows) + 1L]] <- data.frame(
        contrast_id = row$contrast_id,
        context = context,
        contrast_family = "secondary",
        sex = row$sex,
        apoe_group = row$apoe_group,
        eligibility_status = "not_estimable",
        terminal_status = "not_estimable",
        genes_returned = 0L,
        output_path = "",
        message = row$ineligibility_reason,
        stringsAsFactors = FALSE
      )
      next
    }
    vector <- parse_contrast(
      row$coefficient_vector[[1L]], colnames(designs$secondary)
    )
    secondary_vectors[[row$contrast_id[[1L]]]] <- vector
    test <- edgeR::glmQLFTest(secondary_fit, contrast = vector)
    result <- result_from_test(test, keep, annotation, row)
    result_path <- file.path(secondary_dir, row$output_basename[[1L]])
    atomic_fwrite(result, result_path)
    per_contrast_paths <- c(per_contrast_paths, result_path)
    secondary_results[[length(secondary_results) + 1L]] <- result
    secondary_complete[[length(secondary_complete) + 1L]] <- complete_result(
      result, annotation, row
    )
    status_rows[[length(status_rows) + 1L]] <- data.frame(
      contrast_id = row$contrast_id,
      context = context,
      contrast_family = "secondary",
      sex = row$sex,
      apoe_group = row$apoe_group,
      eligibility_status = "eligible",
      terminal_status = "completed",
      genes_returned = nrow(result),
      output_path = sub(paste0("^", project_root, "/?"), "", result_path),
      message = "",
      stringsAsFactors = FALSE
    )
    summary_rows[[length(summary_rows) + 1L]] <- data.frame(
      contrast_id = row$contrast_id,
      context = context,
      contrast_family = "secondary",
      tested_genes = nrow(result),
      filtered_genes = nrow(annotation) - nrow(result),
      fdr_lt_0_05 = sum(result$FDR < 0.05),
      ad_up_tested = sum(result$logFC > 0),
      ad_down_tested = sum(result$logFC < 0),
      stringsAsFactors = FALSE
    )
  }

  model_object <- list(
    schema_version = "seaad_edger_model_object_v1",
    context = context,
    keep = keep,
    source_symbols = annotation$source_symbol,
    metadata = metadata,
    primary_design = designs$primary,
    secondary_design = designs$secondary,
    primary_fit = primary_fit,
    secondary_fit = secondary_fit,
    primary_contrast = primary_contrast,
    secondary_contrasts = secondary_vectors,
    feature_order_sha256 = bundle$feature_order_sha256,
    config_sha256 = sha256_file(config_path)
  )
  model_path <- file.path(model_dir, paste0(context, ".edgeR.rds"))
  atomic_save_rds(model_object, model_path)
  model_paths <- c(model_paths, model_path)
  reloaded <- readRDS(model_path)
  replay <- edgeR::glmQLFTest(
    reloaded$primary_fit, contrast = reloaded$primary_contrast
  )
  replay_table <- edgeR::topTags(replay, n = Inf, sort.by = "none")$table
  sample_rows <- seq_len(min(20L, nrow(primary_result)))
  replay_ok <- isTRUE(all.equal(
    as.numeric(replay_table$logFC[sample_rows]),
    as.numeric(primary_result$logFC[sample_rows]),
    tolerance = 1e-12
  )) && isTRUE(all.equal(
    as.numeric(replay_table$PValue[sample_rows]),
    as.numeric(primary_result$PValue[sample_rows]),
    tolerance = 1e-12
  ))
  primary_residual_df <- primary_fit$df.residual.zeros
  if (is.null(primary_residual_df)) primary_residual_df <- primary_fit$df.residual
  secondary_residual_df <- secondary_fit$df.residual.zeros
  if (is.null(secondary_residual_df)) secondary_residual_df <- secondary_fit$df.residual
  diagnostic_rows[[length(diagnostic_rows) + 1L]] <- data.frame(
    context = context,
    samples = nrow(metadata),
    input_genes = nrow(annotation),
    tested_genes = sum(keep),
    filtered_genes = sum(!keep),
    primary_design_columns = ncol(designs$primary),
    primary_design_rank = qr(designs$primary)$rank,
    secondary_design_columns = ncol(designs$secondary),
    secondary_design_rank = qr(designs$secondary)$rank,
    primary_common_dispersion = y_primary$common.dispersion,
    secondary_common_dispersion = y_secondary$common.dispersion,
    min_primary_residual_df = min(primary_residual_df),
    min_secondary_residual_df = min(secondary_residual_df),
    model_reload_reproduced = replay_ok,
    stringsAsFactors = FALSE
  )
  rm(context_counts, y0, y, y_primary, y_secondary, primary_fit, secondary_fit,
     model_object, reloaded)
  gc(verbose = FALSE)
}

primary_all <- data.table::rbindlist(primary_results, use.names = TRUE, fill = TRUE)
secondary_all <- data.table::rbindlist(secondary_results, use.names = TRUE, fill = TRUE)
primary_complete_all <- data.table::rbindlist(primary_complete, use.names = TRUE, fill = TRUE)
secondary_complete_all <- data.table::rbindlist(secondary_complete, use.names = TRUE, fill = TRUE)
gene_filter <- data.table::rbindlist(filter_rows, use.names = TRUE)
diagnostics <- data.table::rbindlist(diagnostic_rows, use.names = TRUE)
contrast_status <- data.table::rbindlist(status_rows, use.names = TRUE, fill = TRUE)
summary <- data.table::rbindlist(summary_rows, use.names = TRUE)

paths <- list(
  primary_all = file.path(output_dir, "primary_deg_all.tsv.gz"),
  secondary_all = file.path(output_dir, "secondary_deg_all.tsv.gz"),
  primary_complete = file.path(output_dir, "seaad_primary_deg_complete.tsv.gz"),
  secondary_complete = file.path(output_dir, "seaad_secondary_deg_complete.tsv.gz"),
  release_manifest = file.path(output_dir, "seaad_deg_contrast_manifest.tsv"),
  contrast_status = file.path(output_dir, "seaad_deg_contrast_status.tsv"),
  summary = file.path(output_dir, "seaad_deg_summary.tsv"),
  testability = file.path(output_dir, "seaad_gene_testability.tsv.gz"),
  filter = file.path(output_dir, "gene_filter_status.tsv.gz"),
  diagnostics = file.path(output_dir, "model_diagnostics.tsv"),
  checks = file.path(output_dir, "deg_checks.tsv"),
  artifacts = file.path(output_dir, "artifacts.tsv"),
  status = file.path(output_dir, "status.tsv")
)
atomic_fwrite(primary_all, paths$primary_all)
atomic_fwrite(secondary_all, paths$secondary_all)
atomic_fwrite(primary_complete_all, paths$primary_complete)
atomic_fwrite(secondary_complete_all, paths$secondary_complete)
atomic_fwrite(manifest, paths$release_manifest)
atomic_fwrite(contrast_status, paths$contrast_status)
atomic_fwrite(summary, paths$summary)
atomic_fwrite(gene_filter, paths$testability)
atomic_fwrite(gene_filter, paths$filter)
atomic_fwrite(diagnostics, paths$diagnostics)

completed_primary <- sum(
  contrast_status$contrast_family == "primary" &
    contrast_status$terminal_status == "completed"
)
completed_secondary <- sum(
  contrast_status$contrast_family == "secondary" &
    contrast_status$terminal_status == "completed"
)
not_estimable_secondary <- sum(
  contrast_status$contrast_family == "secondary" &
    contrast_status$terminal_status == "not_estimable"
)
tested_stats_finite <- all(
  is.finite(c(primary_all$logFC, secondary_all$logFC)) &
    is.finite(c(primary_all$logCPM, secondary_all$logCPM)) &
    is.finite(c(primary_all$F, secondary_all$F)) &
    is.finite(c(primary_all$PValue, secondary_all$PValue)) &
    is.finite(c(primary_all$FDR, secondary_all$FDR))
)
fdr_valid <- all(c(primary_all$FDR, secondary_all$FDR) >= 0 &
                   c(primary_all$FDR, secondary_all$FDR) <= 1)
unique_within_contrast <- !anyDuplicated(
  paste(primary_all$contrast_id, primary_all$feature_index)
) && !anyDuplicated(
  paste(secondary_all$contrast_id, secondary_all$feature_index)
)
no_gene_rows_for_ineligible <- all(
  !manifest$contrast_id[manifest$eligibility_status == "not_estimable"] %in%
    c(primary_all$contrast_id, secondary_all$contrast_id)
)
checks <- data.frame(
  check = c(
    "completed_primary_contrasts", "completed_secondary_contrasts",
    "secondary_not_estimable_explicit", "contrast_status_rows",
    "tested_statistics_finite", "FDR_range", "unique_genes_within_contrast",
    "primary_complete_grid", "secondary_complete_grid",
    "complete_test_status_values", "no_gene_rows_for_ineligible",
    "model_objects_reload_reproduce", "all_per_contrast_files_exist",
    "effect_direction_frozen"
  ),
  passed = c(
    completed_primary == config$expected$primary_contrasts,
    completed_secondary == vh07_status$secondary_eligible[[1L]],
    not_estimable_secondary == vh07_status$secondary_not_estimable[[1L]],
    nrow(contrast_status) == 49L,
    tested_stats_finite, fdr_valid, unique_within_contrast,
    nrow(primary_complete_all) == nrow(annotation) * completed_primary,
    nrow(secondary_complete_all) == nrow(annotation) * completed_secondary,
    all(c(primary_complete_all$test_status,
          secondary_complete_all$test_status) %in% c("tested", "filtered")),
    no_gene_rows_for_ineligible,
    all(diagnostics$model_reload_reproduced),
    all(file.exists(per_contrast_paths)),
    all(primary_all$direction == ifelse(primary_all$logFC > 0, "AD_up",
      ifelse(primary_all$logFC < 0, "AD_down", "zero"))) &&
      all(secondary_all$direction == ifelse(secondary_all$logFC > 0, "AD_up",
        ifelse(secondary_all$logFC < 0, "AD_down", "zero")))
  ),
  observed = c(
    completed_primary, completed_secondary, not_estimable_secondary,
    nrow(contrast_status), tested_stats_finite, fdr_valid,
    unique_within_contrast, nrow(primary_complete_all),
    nrow(secondary_complete_all),
    paste(unique(c(primary_complete_all$test_status,
                   secondary_complete_all$test_status)), collapse = ";"),
    no_gene_rows_for_ineligible, sum(diagnostics$model_reload_reproduced),
    sum(file.exists(per_contrast_paths)), TRUE
  ),
  expected = c(
    config$expected$primary_contrasts, vh07_status$secondary_eligible[[1L]],
    vh07_status$secondary_not_estimable[[1L]], 49, TRUE, TRUE, TRUE,
    nrow(annotation) * completed_primary,
    nrow(annotation) * completed_secondary,
    "tested;filtered", TRUE, length(contexts), length(per_contrast_paths), TRUE
  ),
  details = "",
  stringsAsFactors = FALSE
)
atomic_fwrite(checks, paths$checks)

result_artifact_paths <- c(
  unlist(paths[c("primary_all", "secondary_all", "primary_complete",
                 "secondary_complete", "release_manifest", "contrast_status",
                 "summary", "testability", "filter", "diagnostics", "checks")]),
  per_contrast_paths,
  model_paths
)
code_paths <- sort(list.files(
  file.path(project_root, "scripts/validation_human"),
  recursive = TRUE, full.names = TRUE
))
code_paths <- code_paths[file.info(code_paths)$isdir %in% FALSE]
code_paths <- code_paths[!grepl("/__pycache__/|[.]pyc$", code_paths)]
code_sha256 <- vapply(code_paths, sha256_file, character(1))
code_bundle_sha256 <- digest::digest(
  paste(paste(sub(paste0("^", project_root, "/?"), "", code_paths),
              code_sha256, sep = "="), collapse = "\n"),
  algo = "sha256", serialize = FALSE
)
artifact_paths <- c(result_artifact_paths, code_paths)
artifacts <- data.frame(
  artifact_role = c(rep("result", length(result_artifact_paths)),
                    rep("code", length(code_paths))),
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = c(vapply(result_artifact_paths, sha256_file, character(1)), code_sha256),
  stringsAsFactors = FALSE
)
atomic_fwrite(artifacts, paths$artifacts)

failed <- checks$check[!checks$passed]
validation_status <- if (length(failed)) "failed" else "validated_complete"
status <- data.frame(
  schema_version = "seaad_phase_status_v1",
  phase = "VH08",
  validation_status = validation_status,
  failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  primary_completed = completed_primary,
  secondary_completed = completed_secondary,
  secondary_not_estimable = not_estimable_secondary,
  source_features = nrow(annotation),
  primary_complete_rows = nrow(primary_complete_all),
  secondary_complete_rows = nrow(secondary_complete_all),
  manifest_sha256 = sha256_file(paths$release_manifest),
  primary_complete_sha256 = sha256_file(paths$primary_complete),
  secondary_complete_sha256 = sha256_file(paths$secondary_complete),
  config_sha256 = sha256_file(config_path),
  code_bundle_sha256 = code_bundle_sha256,
  vh00_code_manifest_sha256 = sha256_file(file.path(output_root, "00_environment/code_manifest.tsv")),
  vh01_artifacts_sha256 = sha256_file(file.path(output_root, "01_audit/artifacts.tsv")),
  vh05_status_sha256 = sha256_file(file.path(output_root, "05_pseudobulk/status.tsv")),
  vh06_status_sha256 = sha256_file(file.path(output_root, "06_pseudobulk_qc/status.tsv")),
  vh07_status_sha256 = sha256_file(file.path(output_root, "07_contrasts/status.tsv")),
  stringsAsFactors = FALSE
)
atomic_fwrite(status, paths$status)
cat("VH08 status: ", validation_status, "; primary=", completed_primary,
    "; secondary=", completed_secondary, "; not_estimable=",
    not_estimable_secondary, "\n", sep = "")
if (length(failed)) quit(status = 2L)
