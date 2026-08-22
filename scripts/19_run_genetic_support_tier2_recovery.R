#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(coloc)
  library(data.table)
  library(digest)
  library(Matrix)
  library(RSpectra)
  library(susieR)
  library(yaml)
})

SCHEMA <- "human_genetic_support_tier2_classical_coloc_recovery_v1"
script_arg <- grep("^--file=", commandArgs(), value = TRUE)
ROOT <- normalizePath(file.path(dirname(sub("^--file=", "", script_arg)), ".."), mustWork = TRUE)
resolve_path <- function(path) ifelse(grepl("^/", path), path, file.path(ROOT, path))

args <- commandArgs(trailingOnly = TRUE)
arg_value <- function(flag, default = NULL) {
  index <- match(flag, args)
  if (is.na(index) || index == length(args)) default else args[[index + 1L]]
}
config_path <- resolve_path(arg_value("--config", "config/phase19_genetic_support_tier2_recovery.yml"))
config <- yaml.load_file(config_path)
if (!is.null(config$project)) {
  registered <- config$project$phase19_genetic_support_tier2_recovery_config
  if (is.null(registered)) stop("Shared config lacks the Tier 2 recovery registration")
  config_path <- resolve_path(registered)
  config <- yaml.load_file(config_path)
}
inputs <- config$inputs
analysis <- config$analysis
release <- config$source_release
output_override <- arg_value("--output-root", NULL)
output_root <- resolve_path(if (is.null(output_override)) config$outputs$root else output_override)
staging <- paste0(output_root, ".staging")
force <- "--force" %in% args

if (dir.exists(output_root) && !force) stop("Output exists; pass --force: ", output_root)
if (dir.exists(staging)) unlink(staging, recursive = TRUE)
dir.create(staging, recursive = TRUE, showWarnings = FALSE)

read_tsv <- function(path) fread(path, sep = "\t", na.strings = character(), showProgress = FALSE)
read_gz <- function(path) fread(cmd = paste("gzip -dc", shQuote(path)), sep = "\t", na.strings = character(), showProgress = FALSE)
write_tsv <- function(x, name) fwrite(x, file.path(staging, name), sep = "\t", quote = FALSE, na = "NA")
write_gz <- function(x, name) {
  connection <- gzfile(file.path(staging, name), "wb", compression = 6)
  write.table(x, connection, sep = "\t", quote = FALSE, row.names = FALSE, col.names = TRUE, na = "NA", eol = "\n")
  close(connection)
}
sha256 <- function(path) digest(file = path, algo = "sha256", serialize = FALSE)
truth <- function(x) ifelse(x, "TRUE", "FALSE")
locus_id <- function(row) paste0(row$gene, "_chr", sub("^chr", "", row$chromosome), "_", row$window_start, "_", row$window_end)

manifest_dir <- resolve_path(inputs$source_manifest_dir)
routes <- read_tsv(file.path(manifest_dir, "recovery_route_manifest.tsv"))
requests <- read_tsv(file.path(manifest_dir, "recovery_request_manifest.tsv"))
registry <- read_tsv(file.path(manifest_dir, "recovery_dataset_registry.tsv"))
baseline <- read_tsv(file.path(manifest_dir, "recovery_baseline_hashes.tsv"))
sources <- read_tsv(file.path(manifest_dir, "recovery_source_manifest.tsv"))
qtl_audit <- read_tsv(file.path(manifest_dir, "recovery_qtl_model_extraction_summary.tsv"))
qtl_artifacts <- read_tsv(file.path(manifest_dir, "recovery_qtl_model_artifacts.tsv"))
dense_qtl_audit <- read_tsv(file.path(manifest_dir, "recovery_dense_qtl_extraction_summary.tsv"))
dense_qtl_artifacts <- read_tsv(file.path(manifest_dir, "recovery_dense_qtl_artifacts.tsv"))
ld_extract <- read_tsv(file.path(manifest_dir, "recovery_ld_extraction_summary.tsv"))
ld_artifacts <- read_tsv(file.path(manifest_dir, "recovery_ld_block_artifacts.tsv"))
tier2_summary <- read_tsv(resolve_path(inputs$tier2_evidence_summary))
gwas <- read_gz(resolve_path(inputs$candidate_gwas))
gwas_numeric_columns <- c(
  "chromosome", "window_start", "window_end", "position", "effect_allele_frequency",
  "beta", "standard_error", "p_value", "odds_ratio", "n_cases", "n_controls"
)
for (column in gwas_numeric_columns) {
  set(gwas, j = column, value = suppressWarnings(as.numeric(gwas[[column]])))
}

stopifnot(nrow(routes) == 54L, nrow(tier2_summary) == 47L, all(baseline$status == "pass"))
write_tsv(routes, "recovery_route_manifest.tsv")
write_tsv(registry, "recovery_dataset_registry.tsv")
write_tsv(requests, "recovery_request_manifest.tsv")

analysis_manifest <- data.table(
  schema_version = SCHEMA,
  analysis_id = analysis$analysis_id,
  source_release_id = release$release_id,
  genome_build = analysis$genome_build,
  execution_stage = "local_production_equivalent",
  execution_backend = "direct",
  publication_namespace = "minerva_production",
  primary_method = "coloc_bf_bf_susie_models",
  single_signal_sensitivity = "coloc.abf_not_promoted_to_primary",
  p1 = analysis$primary_p1, p2 = analysis$primary_p2, p12 = analysis$primary_p12,
  strong_h4 = analysis$strong_h4,
  strong_conditional_h4 = analysis$strong_conditional_h4,
  gwas_trait_type = "case_control",
  gwas_cases = release$gwas_cases, gwas_controls = release$gwas_controls,
  gwas_case_fraction = release$gwas_cases / (release$gwas_cases + release$gwas_controls),
  qtl_model_class = "released_complete_susie_log_bayes_factors",
  ld_panel = release$niagads_panel,
  ld_panel_ancestry = "non_Hispanic_White",
  ld_panel_sample_size = release$niagads_panel_sample_size,
  ld_sparse_retention_rule = "within_5Mb_and_abs_R_gt_0.2",
  selection_frozen_before_result = "TRUE",
  full_phase19_complete = "FALSE"
)
write_tsv(analysis_manifest, "recovery_analysis_manifest.tsv")

inventory <- sources[, .(
  schema_version = SCHEMA, source_id, role, source_version, path, url,
  bytes = observed_bytes, sha256, validation_state
)]
for (artifact_table in list(qtl_artifacts, dense_qtl_artifacts, ld_artifacts)) {
  if (!nrow(artifact_table)) next
  id_field <- if ("dataset_id" %in% names(artifact_table)) "dataset_id" else "locus_id"
  addition <- artifact_table[, .(
    schema_version = SCHEMA,
    source_id = get(id_field), role, source_version = "local_deterministic_extraction",
    path, url = "local_deterministic_extraction",
    bytes = file.info(resolve_path(path))$size, sha256,
    validation_state = "validated"
  )]
  inventory <- rbind(inventory, addition, fill = TRUE)
}
setorder(inventory, source_id, role, path)
write_tsv(inventory, "recovery_input_inventory.tsv")

source_checks <- rbind(
  sources[, .(
    schema_version = SCHEMA, check_id = paste0("source_", .I), source_id, role, path,
    expected = ifelse(expected_bytes == "NA", "exists", expected_bytes),
    observed = observed_bytes,
    status = ifelse(validation_state == "validated", "pass", "fail"),
    detail = "registered_size_and_checksum_validation"
  )],
  baseline[, .(
    schema_version = SCHEMA, check_id = paste0("baseline_", tier, "_", .I),
    source_id = tier, role = "immutable_baseline_artifact", path,
    expected = expected_sha256, observed = observed_sha256, status,
    detail = "baseline_hash_reproduced"
  )],
  fill = TRUE
)
write_tsv(source_checks, "recovery_source_checks.tsv")

gwas_summary <- gwas[, .(
  chromosome = chromosome[1], window_start = min(window_start), window_end = max(window_end),
  regional_gwas_rows = .N, regional_min_p = min(p_value, na.rm = TRUE),
  regional_lead_variant = variant_id[which.min(p_value)],
  cases = max(n_cases), controls = max(n_controls)
), by = .(gene, ensembl_gene_id)]
gwas_summary[, schema_version := SCHEMA]
gwas_summary[, regional_gwas_signal := truth(regional_min_p < as.numeric(analysis$gwas_signal_p))]
gwas_summary[, trait_type := "case_control"]
gwas_summary[, effect_scale := "log_odds_beta"]
gwas_summary[, source_accession := release$gwas_accession]
setcolorder(gwas_summary, c(
  "schema_version", "gene", "ensembl_gene_id", "chromosome", "window_start", "window_end",
  "regional_gwas_rows", "regional_min_p", "regional_lead_variant", "regional_gwas_signal",
  "trait_type", "effect_scale", "cases", "controls", "source_accession"
))
write_tsv(gwas_summary, "recovery_regional_gwas_summary.tsv")

qtl_summary <- copy(qtl_audit)
dense_for_merge <- dense_qtl_audit[, .(
  dataset_id, gene, ensembl_gene_id, qtl_type,
  dense_statistics_rows, dense_minimum_p_value = minimum_p_value,
  dense_bonferroni_tests = bonferroni_tests,
  dense_bonferroni_threshold = bonferroni_threshold,
  dense_regional_qtl_signal = regional_qtl_signal,
  dense_coverage_state = coverage_state,
  dense_source_url = source_url
)]
qtl_summary <- merge(
  qtl_summary, dense_for_merge,
  by = c("dataset_id", "gene", "ensembl_gene_id", "qtl_type"), all.x = TRUE, sort = FALSE
)
qtl_summary[, context_match_level := registry$context_match_level[match(dataset_id, registry$dataset_id)]]
qtl_summary[, source_context := registry$tissue_label[match(dataset_id, registry$dataset_id)]]
qtl_summary[, source_sample_size := registry$sample_size[match(dataset_id, registry$dataset_id)]]
qtl_summary[, source_model_class := "released_complete_susie_log_bayes_factors"]
write_tsv(qtl_summary, "recovery_regional_qtl_summary.tsv")

signal_routes <- routes[gwas_signal_present == "TRUE"]
loci <- unique(signal_routes[, .(
  gene, ensembl_gene_id, chromosome, window_start, window_end
)])
loci[, locus_id := locus_id(.SD)]
setcolorder(loci, c("locus_id", "gene", "ensembl_gene_id", "chromosome", "window_start", "window_end"))

model_locus <- function(locus) {
  id <- locus$locus_id
  block_dir <- resolve_path(inputs$ld_candidate_blocks_dir)
  variants <- read_gz(file.path(block_dir, paste0(id, ".variant_map.tsv.gz")))
  edges <- read_gz(file.path(block_dir, paste0(id, ".ld_edges.tsv.gz")))
  result <- list(
    state = "model_or_ld_incompatible", reason = "uninitialized", fit = NULL, bf = NULL,
    variants = variants, raw_min_eigenvalue = NA_real_, corrected_min_eigenvalue = NA_real_,
    shrinkage_factor = 1, symmetry_max_error = NA_real_, diagonal_max_error = NA_real_,
    order_valid = FALSE, finite_valid = FALSE
  )
  if (nrow(variants) < as.integer(analysis$minimum_harmonized_variants) || !nrow(edges)) {
    result$reason <- "insufficient_ld_observed_variants_or_edges"
    return(result)
  }
  order <- variants$variant
  i <- match(edges$variant1, order)
  j <- match(edges$variant2, order)
  result$order_valid <- all(!is.na(i)) && all(!is.na(j))
  result$finite_valid <- all(is.finite(edges$r))
  if (!result$order_valid || !result$finite_valid) {
    result$reason <- "ld_variant_order_or_finiteness_failed"
    return(result)
  }
  sparse <- sparseMatrix(
    i = c(i, j, seq_along(order)), j = c(j, i, seq_along(order)),
    x = c(edges$r, edges$r, rep(1, length(order))),
    dims = c(length(order), length(order)), dimnames = list(order, order)
  )
  sparse <- forceSymmetric(sparse, uplo = "L")
  result$symmetry_max_error <- max(abs(sparse - t(sparse)))
  result$diagonal_max_error <- max(abs(diag(sparse) - 1))
  result$raw_min_eigenvalue <- tryCatch(
    as.numeric(eigs_sym(sparse, 1, which = "SA", opts = list(retvec = FALSE))$values),
    error = function(e) NA_real_
  )
  if (!is.finite(result$raw_min_eigenvalue)) {
    result$reason <- "ld_smallest_eigenvalue_not_computable"
    return(result)
  }
  if (result$raw_min_eigenvalue < 1e-6) {
    result$shrinkage_factor <- min(1, (1 - 1e-6) / (1 - result$raw_min_eigenvalue))
    sparse <- result$shrinkage_factor * sparse
    diag(sparse) <- 1
  }
  result$corrected_min_eigenvalue <- tryCatch(
    as.numeric(eigs_sym(sparse, 1, which = "SA", opts = list(retvec = FALSE))$values),
    error = function(e) NA_real_
  )
  if (result$shrinkage_factor < 0.8) {
    result$reason <- "published_sparse_ld_requires_excessive_uniform_shrinkage"
    return(result)
  }
  if (!is.finite(result$corrected_min_eigenvalue) || result$corrected_min_eigenvalue < -1e-5) {
    result$reason <- "ld_positive_semidefinite_check_failed"
    return(result)
  }
  if (length(order) > 15000L) {
    result$reason <- "dense_ld_model_memory_gate_exceeded_15000_variants"
    return(result)
  }
  dense <- as.matrix(sparse)
  z <- variants$gwas_beta_ld_alt / variants$gwas_standard_error
  names(z) <- order
  fit <- tryCatch(
    susie_rss(
      z = z, R = dense, n = as.integer(release$gwas_cases + release$gwas_controls),
      L = as.integer(analysis$custom_susie_L),
      max_iter = as.integer(analysis$custom_susie_maxit),
      estimate_residual_variance = FALSE, check_prior = TRUE,
      coverage = as.numeric(analysis$credible_set_coverage)
    ),
    error = function(e) structure(list(message = conditionMessage(e)), class = "recovery_model_error")
  )
  rm(dense)
  gc(FALSE)
  if (inherits(fit, "recovery_model_error")) {
    result$reason <- paste0("susie_rss_error:", fit$message)
    return(result)
  }
  if (!isTRUE(fit$converged)) {
    result$reason <- "susie_rss_did_not_converge"
    return(result)
  }
  if (is.null(fit$sets$cs_index) || !length(fit$sets$cs_index)) {
    result$reason <- "gwas_signal_not_recovered_by_ld_model"
    return(result)
  }
  indices <- as.integer(fit$sets$cs_index)
  bf <- fit$lbf_variable[indices, , drop = FALSE]
  colnames(bf) <- order
  result$state <- "modeled"
  result$reason <- "custom_gwas_susie_rss_converged"
  result$fit <- fit
  result$bf <- cbind(bf, null = 0)
  result
}

locus_models <- list()
gwas_fm <- list()
ld_qc <- list()
qtl_signal_genes <- unique(qtl_audit[credible_set_rows > 0]$gene)
for (index in seq_len(nrow(loci))) {
  locus <- loci[index]
  model <- if (locus$gene %in% qtl_signal_genes) model_locus(locus) else list(
    state = "not_required_no_qtl_signal",
    reason = "gwas_finemapping_skipped_after_complete_qtl_no_signal_gate",
    fit = NULL, bf = NULL, variants = data.table(),
    raw_min_eigenvalue = NA_real_, corrected_min_eigenvalue = NA_real_,
    shrinkage_factor = 1, symmetry_max_error = NA_real_, diagonal_max_error = NA_real_,
    order_valid = NA, finite_valid = NA
  )
  locus_models[[locus$locus_id]] <- model
  ld_qc[[length(ld_qc) + 1L]] <- data.table(
    schema_version = SCHEMA, locus_id = locus$locus_id, gene = locus$gene,
    chromosome = locus$chromosome,
    variants = ld_extract$ld_observed_variants[match(locus$locus_id, ld_extract$locus_id)],
    edges = ld_extract$ld_observed_edges[match(locus$locus_id, ld_extract$locus_id)],
    source_panel = release$niagads_panel, source_ancestry = "non_Hispanic_White",
    source_sample_size = release$niagads_panel_sample_size,
    source_retention_rule = "within_5Mb_and_abs_R_gt_0.2",
    missing_pair_policy = "zero_before_documented_uniform_psd_shrinkage",
    order_valid = truth(model$order_valid), finite_valid = truth(model$finite_valid),
    symmetry_max_error = model$symmetry_max_error, diagonal_max_error = model$diagonal_max_error,
    raw_min_eigenvalue = model$raw_min_eigenvalue,
    shrinkage_factor = model$shrinkage_factor,
    corrected_min_eigenvalue = model$corrected_min_eigenvalue,
    model_state = model$state, reason = model$reason
  )
  if (model$state == "modeled") {
    fit <- model$fit
    for (variant_index in seq_len(nrow(model$variants))) {
      memberships <- which(vapply(fit$sets$cs, function(x) variant_index %in% x, logical(1)))
      gwas_fm[[length(gwas_fm) + 1L]] <- data.table(
        schema_version = SCHEMA, locus_id = locus$locus_id, gene = locus$gene,
        variant = model$variants$variant[variant_index],
        gwas_variant_id = model$variants$gwas_variant_id[variant_index],
        position = model$variants$position[variant_index],
        beta_ld_alt = model$variants$gwas_beta_ld_alt[variant_index],
        standard_error = model$variants$gwas_standard_error[variant_index],
        z = model$variants$gwas_beta_ld_alt[variant_index] / model$variants$gwas_standard_error[variant_index],
        p_value = model$variants$gwas_p_value[variant_index],
        pip = fit$pip[variant_index],
        credible_signal_indices = if (length(memberships)) paste(memberships, collapse = ";") else "NA",
        model_state = "modeled"
      )
    }
  }
}
ld_qc_dt <- rbindlist(ld_qc, fill = TRUE)
write_tsv(ld_qc_dt, "recovery_ld_qc.tsv")
gwas_fm_dt <- rbindlist(gwas_fm, fill = TRUE)
if (!nrow(gwas_fm_dt)) {
  gwas_fm_dt <- data.table(
    schema_version = character(), locus_id = character(), gene = character(),
    variant = character(), gwas_variant_id = character(), position = integer(),
    beta_ld_alt = numeric(), standard_error = numeric(), z = numeric(),
    p_value = numeric(), pip = numeric(), credible_signal_indices = character(),
    model_state = character()
  )
}
write_gz(gwas_fm_dt, "recovery_gwas_finemapping.tsv.gz")
selected_datasets <- unique(signal_routes$source_dataset_id)
qtl_lbf <- list()
qtl_cs <- list()
qtl_fm <- list()
for (dataset_id in selected_datasets) {
  qtl_lbf[[dataset_id]] <- read_gz(file.path(resolve_path(inputs$regional_qtl_dir), paste0(dataset_id, ".candidate_lbf.tsv.gz")))
  qtl_cs[[dataset_id]] <- read_gz(file.path(resolve_path(inputs$regional_qtl_dir), paste0(dataset_id, ".candidate_credible_sets.tsv.gz")))
  if (nrow(qtl_cs[[dataset_id]])) {
    part <- copy(qtl_cs[[dataset_id]])
    part[, schema_version := SCHEMA]
    part[, dataset_id := dataset_id]
    part[, study_id := registry$study_id[match(dataset_id, registry$dataset_id)]]
    part[, qtl_type := registry$qtl_type[match(dataset_id, registry$dataset_id)]]
    part[, source_context := registry$tissue_label[match(dataset_id, registry$dataset_id)]]
    part[, context_match_level := registry$context_match_level[match(dataset_id, registry$dataset_id)]]
    qtl_fm[[length(qtl_fm) + 1L]] <- part
  }
}
qtl_fm_dt <- rbindlist(qtl_fm, fill = TRUE)
if (!nrow(qtl_fm_dt)) {
  qtl_fm_dt <- data.table(
    schema_version = character(), dataset_id = character(), study_id = character(),
    qtl_type = character(), molecular_trait_id = character(), gene_id = character(),
    cs_id = character(), variant = character(), pip = numeric()
  )
}
write_gz(qtl_fm_dt, "recovery_qtl_finemapping.tsv.gz")

decisions <- list()
harmonized <- list()
harmonization_summary <- list()
coloc_primary <- list()
coloc_sensitivity <- list()
coloc_qc <- list()
assessability <- list()
route_best <- list()
terminal_vocabulary <- c(
  "precomputed_resolved", "custom_resolved", "no_regional_gwas_signal",
  "no_regional_qtl_signal", "distinct_signals", "qtl_context_not_measured",
  "model_or_ld_incompatible", "not_assessable"
)

for (route_index in seq_len(nrow(routes))) {
  route <- routes[route_index]
  comparison_id <- route$comparison_id
  id <- locus_id(route)
  terminal_state <- "not_assessable"
  reason <- "recovery_not_attempted"
  mapped_traits <- 0L
  signal_traits_count <- 0L
  maximum_overlap <- 0L
  primary_for_route <- list()
  sensitivity_for_route <- list()
  audit <- qtl_audit[0]
  dense_audit <- dense_qtl_audit[0]

  if (route$gwas_signal_present != "TRUE") {
    terminal_state <- "no_regional_gwas_signal"
    reason <- "complete_dense_bellenguez_region_has_no_variant_below_5e-8"
  } else {
    audit <- qtl_audit[
      dataset_id == route$source_dataset_id &
        gene == route$gene &
        qtl_type == route$qtl_type
    ]
    dense_audit <- dense_qtl_audit[
      dataset_id == route$source_dataset_id & gene == route$gene & qtl_type == route$qtl_type
    ]
    model <- locus_models[[id]]
    if (!nrow(audit)) {
      terminal_state <- "not_assessable"
      reason <- "registered_qtl_dataset_gene_audit_missing"
    } else if (audit$mapped_molecular_traits[1] == 0L) {
      terminal_state <- "not_assessable"
      reason <- ifelse(
        route$qtl_type == "sQTL",
        "target_gene_splicing_event_absent_from_conditionally_detected_cc_and_lbf_releases;measurement_status_unresolved",
        "no_molecular_trait_mapping_in_released_source_model"
      )
    } else if (audit$model_lbf_rows[1] == 0L) {
      if (route$qtl_type == "eQTL" && nrow(dense_audit) && dense_audit$dense_statistics_rows[1] > 0L) {
        if (dense_audit$regional_qtl_signal[1] == "FALSE") {
          terminal_state <- "no_regional_qtl_signal"
          reason <- "complete_indexed_dense_eqtl_region_fails_frozen_per_gene_bonferroni_signal_gate"
        } else {
          terminal_state <- "model_or_ld_incompatible"
          reason <- "dense_regional_eqtl_signal_present_but_released_susie_model_absent_and_qtl_ancestry_matched_ld_unavailable"
        }
      } else {
        terminal_state <- "not_assessable"
        reason <- "mapped_trait_absent_from_released_complete_lbf_archive_and_no_complete_dense_fallback"
      }
    } else if (audit$credible_set_rows[1] == 0L) {
      terminal_state <- "no_regional_qtl_signal"
      reason <- "released_complete_susie_model_has_no_95pct_credible_signal"
    } else if (is.null(model) || model$state != "modeled") {
      terminal_state <- "model_or_ld_incompatible"
      reason <- if (is.null(model)) "gwas_locus_model_missing" else model$reason
    } else {
      trait_ids <- strsplit(audit$molecular_trait_ids[1], ";", fixed = TRUE)[[1]]
      trait_ids <- trait_ids[nzchar(trait_ids)]
      mapped_traits <- length(trait_ids)
      dataset_lbf <- qtl_lbf[[route$source_dataset_id]]
      dataset_cs <- qtl_cs[[route$source_dataset_id]]
      signal_traits <- intersect(trait_ids, unique(dataset_cs$molecular_trait_id))
      signal_traits_count <- length(signal_traits)
      errors <- character()

      for (trait_id in signal_traits) {
        trait_lbf <- dataset_lbf[molecular_trait_id == trait_id]
        trait_cs <- dataset_cs[molecular_trait_id == trait_id]
        signal_numbers <- sort(unique(as.integer(sub(".*_L", "", trait_cs$cs_id))))
        signal_numbers <- signal_numbers[
          is.finite(signal_numbers) & signal_numbers >= 1L &
            signal_numbers <= as.integer(analysis$custom_susie_L)
        ]
        common <- intersect(model$variants$variant, trait_lbf$variant)
        maximum_overlap <- max(maximum_overlap, length(common))
        if (length(common) < as.integer(analysis$minimum_harmonized_variants)) {
          errors <- c(errors, paste0(trait_id, ":insufficient_common_variants_", length(common)))
          next
        }
        lbf_columns <- paste0("lbf_variable", seq_len(as.integer(analysis$custom_susie_L)))
        qbf <- t(as.matrix(trait_lbf[, ..lbf_columns]))
        storage.mode(qbf) <- "double"
        colnames(qbf) <- trait_lbf$variant
        qbf <- qbf[signal_numbers, , drop = FALSE]
        qbf <- cbind(qbf, null = 0)

        harmonized[[length(harmonized) + 1L]] <- data.table(
          schema_version = SCHEMA, comparison_id, route_id = route$route_id,
          locus_id = id, dataset_id = route$source_dataset_id,
          molecular_trait_id = trait_id, variant = common,
          gwas_present = "TRUE", qtl_model_present = "TRUE",
          allele_identity = "canonical_GRCh38_ref_alt_match",
          harmonization_state = "included"
        )

        for (p12 in as.numeric(analysis$sensitivity_p12)) {
          result <- tryCatch(
            coloc.bf_bf(
              model$bf, qbf,
              p1 = as.numeric(analysis$primary_p1),
              p2 = as.numeric(analysis$primary_p2), p12 = p12,
              overlap.min = as.numeric(analysis$minimum_model_overlap_fraction),
              trim_by_posterior = TRUE
            ),
            error = function(e) structure(list(message = conditionMessage(e)), class = "recovery_coloc_error")
          )
          if (inherits(result, "recovery_coloc_error") || is.null(result$summary)) {
            errors <- c(errors, paste0(trait_id, ":coloc_error"))
            next
          }
          summary <- as.data.table(result$summary)
          if (!nrow(summary)) next
          summary[, schema_version := SCHEMA]
          summary[, comparison_id := comparison_id]
          summary[, route_id := route$route_id]
          summary[, candidate_id := route$candidate_id]
          summary[, gene := route$gene]
          summary[, broad_network := route$broad_network]
          summary[, qtl_type := route$qtl_type]
          summary[, dataset_id := route$source_dataset_id]
          summary[, molecular_trait_id := trait_id]
          summary[, context_match_level := route$context_match_level]
          summary[, p1 := as.numeric(analysis$primary_p1)]
          summary[, p2 := as.numeric(analysis$primary_p2)]
          summary[, p12 := p12]
          summary[, conditional_h4 := PP.H4.abf / (PP.H3.abf + PP.H4.abf)]
          summary[, method := "coloc_bf_bf_custom_gwas_susie_released_qtl_susie"]
          sensitivity_for_route[[length(sensitivity_for_route) + 1L]] <- summary
          if (isTRUE(all.equal(p12, as.numeric(analysis$primary_p12)))) {
            primary_for_route[[length(primary_for_route) + 1L]] <- summary
          }
        }
      }

      if (length(primary_for_route)) {
        primary <- rbindlist(primary_for_route, fill = TRUE)
        primary <- primary[is.finite(PP.H4.abf)]
        if (nrow(primary)) {
          best <- primary[which.max(PP.H4.abf)]
          route_best[[comparison_id]] <- best
          coloc_primary[[length(coloc_primary) + 1L]] <- primary
          if (
            best$PP.H4.abf >= as.numeric(analysis$strong_h4) &&
              best$conditional_h4 >= as.numeric(analysis$strong_conditional_h4)
          ) {
            terminal_state <- "custom_resolved"
            reason <- "strong_shared_signal_under_frozen_h4_thresholds"
          } else if (best$PP.H3.abf > best$PP.H4.abf && best$PP.H3.abf >= 0.5) {
            terminal_state <- "distinct_signals"
            reason <- "posterior_support_favors_h3_distinct_signals"
          } else {
            terminal_state <- "custom_resolved"
            reason <- "classical_h0_h4_calculated_without_strong_shared_or_distinct_call"
          }
        } else {
          terminal_state <- "model_or_ld_incompatible"
          reason <- "coloc_returned_no_finite_primary_posteriors"
        }
      } else {
        terminal_state <- "model_or_ld_incompatible"
        reason <- if (length(errors)) paste(unique(errors), collapse = ";") else "no_compatible_signal_pair"
      }
      if (length(sensitivity_for_route)) {
        coloc_sensitivity[[length(coloc_sensitivity) + 1L]] <- rbindlist(sensitivity_for_route, fill = TRUE)
      }
    }
  }

  best <- route_best[[comparison_id]]
  decisions[[length(decisions) + 1L]] <- data.table(
    schema_version = SCHEMA, comparison_id, route_id = route$route_id,
    candidate_id = route$candidate_id, gene = route$gene,
    broad_network = route$broad_network, case_id = route$case_id,
    qtl_type = route$qtl_type, dataset_id = route$source_dataset_id,
    context_match_level = route$context_match_level, gwas_min_p = route$gwas_min_p,
    terminal_state, reason,
    decision_rule = "frozen_gwas_gate_then_complete_qtl_model_then_ld_model_then_h0_h4"
  )
  harmonization_summary[[length(harmonization_summary) + 1L]] <- data.table(
    schema_version = SCHEMA, comparison_id, route_id = route$route_id,
    candidate_id = route$candidate_id, gene = route$gene,
    broad_network = route$broad_network, qtl_type = route$qtl_type,
    dataset_id = route$source_dataset_id, locus_id = id,
    gwas_signal_present = route$gwas_signal_present,
    mapped_qtl_traits = mapped_traits, qtl_signal_traits = signal_traits_count,
    maximum_harmonized_variants = maximum_overlap,
    minimum_required_variants = as.integer(analysis$minimum_harmonized_variants),
    terminal_state, reason
  )
  assessability[[length(assessability) + 1L]] <- data.table(
    schema_version = SCHEMA, comparison_id, route_id = route$route_id,
    candidate_id = route$candidate_id, gene = route$gene,
    broad_network = route$broad_network, qtl_type = route$qtl_type,
    dataset_id = route$source_dataset_id, context_match_level = route$context_match_level,
    terminal_state,
    assessable = truth(terminal_state %in% c("custom_resolved", "precomputed_resolved", "distinct_signals")),
    best_pp_h3 = if (is.null(best)) NA_real_ else best$PP.H3.abf,
    best_pp_h4 = if (is.null(best)) NA_real_ else best$PP.H4.abf,
    best_conditional_h4 = if (is.null(best)) NA_real_ else best$conditional_h4,
    reason
  )
  coloc_qc[[length(coloc_qc) + 1L]] <- data.table(
    schema_version = SCHEMA, comparison_id, route_id = route$route_id,
    locus_id = id, dataset_id = route$source_dataset_id,
    gwas_signal_gate = route$gwas_signal_present,
    gwas_model_state = if (route$gwas_signal_present == "TRUE") locus_models[[id]]$state else "not_required",
    qtl_model_rows = if (nrow(audit)) audit$model_lbf_rows[1] else 0L,
    qtl_credible_rows = if (nrow(audit)) audit$credible_set_rows[1] else 0L,
    dense_qtl_rows = if (nrow(dense_audit)) dense_audit$dense_statistics_rows[1] else 0L,
    dense_qtl_signal = if (nrow(dense_audit)) dense_audit$regional_qtl_signal[1] else "NA",
    maximum_harmonized_variants = maximum_overlap,
    posterior_rows = if (length(primary_for_route)) nrow(rbindlist(primary_for_route, fill = TRUE)) else 0L,
    qc_state = ifelse(terminal_state == "model_or_ld_incompatible", "failed_with_terminal_reason", "complete"),
    terminal_state, reason
  )
}

decisions_dt <- rbindlist(decisions, fill = TRUE)
harmonized_dt <- rbindlist(harmonized, fill = TRUE)
if (!nrow(harmonized_dt)) {
  harmonized_dt <- data.table(
    schema_version = character(), comparison_id = character(), route_id = character(),
    locus_id = character(), dataset_id = character(), molecular_trait_id = character(),
    variant = character(), gwas_present = character(), qtl_model_present = character(),
    allele_identity = character(), harmonization_state = character()
  )
}
harmonization_summary_dt <- rbindlist(harmonization_summary, fill = TRUE)
coloc_dt <- rbindlist(coloc_primary, fill = TRUE)
if (!nrow(coloc_dt)) {
  coloc_dt <- data.table(
    schema_version = character(), comparison_id = character(), route_id = character(),
    candidate_id = character(), gene = character(), broad_network = character(),
    qtl_type = character(), dataset_id = character(), molecular_trait_id = character(),
    context_match_level = character(), nsnps = integer(), hit1 = character(), hit2 = character(),
    PP.H0.abf = numeric(), PP.H1.abf = numeric(), PP.H2.abf = numeric(),
    PP.H3.abf = numeric(), PP.H4.abf = numeric(), idx1 = integer(), idx2 = integer(),
    p1 = numeric(), p2 = numeric(), p12 = numeric(), conditional_h4 = numeric(),
    method = character()
  )
}
sensitivity_dt <- rbindlist(coloc_sensitivity, fill = TRUE)
if (!nrow(sensitivity_dt)) sensitivity_dt <- copy(coloc_dt)[0]
assessability_dt <- rbindlist(assessability, fill = TRUE)
coloc_qc_dt <- rbindlist(coloc_qc, fill = TRUE)

write_tsv(decisions_dt, "recovery_route_decisions.tsv")
write_gz(harmonized_dt, "recovery_variant_harmonization.tsv.gz")
write_tsv(harmonization_summary_dt, "recovery_variant_harmonization_summary.tsv")
write_gz(coloc_dt, "recovery_colocalization.tsv.gz")
write_tsv(coloc_qc_dt, "recovery_colocalization_qc.tsv")
write_gz(sensitivity_dt, "recovery_prior_sensitivity.tsv.gz")
write_tsv(assessability_dt, "recovery_assessability.tsv")
evidence_summary <- copy(tier2_summary)
setnames(evidence_summary, "schema_version", "previous_schema_version")
evidence_summary[, schema_version := SCHEMA]
candidate_recovery <- assessability_dt[, {
  finite_h4 <- best_pp_h4[is.finite(best_pp_h4)]
  finite_conditional <- best_conditional_h4[is.finite(best_conditional_h4)]
  list(
    recovery_route_count = .N,
    recovery_terminal_states = paste(sort(unique(terminal_state)), collapse = ";"),
    recovery_best_pp_h4 = if (length(finite_h4)) max(finite_h4) else NA_real_,
    recovery_best_conditional_h4 = if (length(finite_conditional)) max(finite_conditional) else NA_real_,
    recovery_strong_shared_signal = truth(any(
      best_pp_h4 >= as.numeric(analysis$strong_h4) &
        best_conditional_h4 >= as.numeric(analysis$strong_conditional_h4),
      na.rm = TRUE
    ))
  )
}, by = candidate_id]
evidence_summary <- merge(evidence_summary, candidate_recovery, by = "candidate_id", all.x = TRUE, sort = FALSE)
evidence_summary[is.na(recovery_route_count), recovery_route_count := 0L]
evidence_summary[is.na(recovery_terminal_states), recovery_terminal_states := "mtDNA_not_in_nuclear_recovery_scope"]
evidence_summary[is.na(recovery_strong_shared_signal), recovery_strong_shared_signal := "FALSE"]
evidence_summary[, recovery_method := ifelse(
  recovery_route_count > 0L,
  "custom_GWAS_SuSiE_RSS_plus_released_QTL_SuSiE_LBF",
  "not_applicable_mtDNA"
)]
evidence_summary[, recovery_grade_contribution := ifelse(
  recovery_strong_shared_signal == "TRUE", "classical_colocalization_support", "none"
)]
evidence_summary[, full_phase19_complete := "FALSE"]
setcolorder(evidence_summary, c(
  "schema_version", "previous_schema_version",
  setdiff(names(evidence_summary), c("schema_version", "previous_schema_version"))
))
setorder(evidence_summary, candidate_id)
write_tsv(evidence_summary, "recovery_evidence_summary.tsv")

figure_data <- assessability_dt[, .(
  schema_version = SCHEMA, candidate_id, gene, broad_network, qtl_type,
  terminal_state, best_pp_h3, best_pp_h4, best_conditional_h4,
  display_value = fifelse(
    terminal_state == "no_regional_gwas_signal", 0,
    fifelse(
      terminal_state == "no_regional_qtl_signal", 1,
      fifelse(
        terminal_state %in% c("not_assessable", "model_or_ld_incompatible"), 2,
        fifelse(terminal_state == "distinct_signals", 3, 4 + fifelse(is.finite(best_pp_h4), best_pp_h4, 0))
      )
    )
  )
)]
write_gz(figure_data, "recovery_figure_data.tsv.gz")

draw_matrix <- function(device) {
  device()
  labels <- unique(paste(assessability_dt$gene, assessability_dt$broad_network, sep = " / "))
  values <- matrix(NA_real_, nrow = length(labels), ncol = 2L, dimnames = list(labels, c("eQTL", "sQTL")))
  for (row_index in seq_len(nrow(figure_data))) {
    label <- paste(figure_data$gene[row_index], figure_data$broad_network[row_index], sep = " / ")
    values[match(label, labels), match(figure_data$qtl_type[row_index], colnames(values))] <- figure_data$display_value[row_index]
  }
  par(mar = c(5, 15, 4, 2))
  image(
    seq_len(ncol(values)), seq_len(nrow(values)), t(values),
    axes = FALSE, xlab = "", ylab = "",
    main = "Phase 19 Tier 2 classical colocalization recovery",
    col = c("#f0f0f0", "#fee8c8", "#fdbb84", "#e34a33", "#2b8cbe", "#08589e"),
    breaks = c(-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.01)
  )
  axis(1, at = seq_len(ncol(values)), labels = colnames(values))
  axis(2, at = seq_len(nrow(values)), labels = rownames(values), las = 2, cex.axis = 0.55)
  box()
  legend(
    "topright",
    legend = c("No GWAS signal", "No QTL signal", "Input/model limitation", "Distinct signals", "H0-H4 resolved"),
    fill = c("#f0f0f0", "#fee8c8", "#fdbb84", "#e34a33", "#2b8cbe"),
    cex = 0.65
  )
  dev.off()
}
draw_matrix(function() pdf(file.path(staging, "recovery_evidence_matrix.pdf"), width = 11, height = 14, useDingbats = FALSE))
draw_matrix(function() png(file.path(staging, "recovery_evidence_matrix.png"), width = 1800, height = 2200, res = 170, type = "cairo"))

pdf(file.path(staging, "recovery_locus_plots.pdf"), width = 10, height = 8, useDingbats = FALSE)
par(mfrow = c(2, 2), mar = c(4, 4, 3, 1))
for (index in seq_len(nrow(loci))) {
  locus <- loci[index]
  locus_gwas <- gwas[
    gene == locus$gene & as.character(chromosome) == as.character(locus$chromosome) &
      position >= locus$window_start & position <= locus$window_end
  ]
  plot(
    locus_gwas$position / 1e6,
    -log10(pmax(locus_gwas$p_value, .Machine$double.xmin)),
    pch = 16, cex = 0.35, col = "#4d4d4d",
    xlab = paste0("chr", locus$chromosome, " position (Mb)"),
    ylab = expression(-log[10](p)), main = locus$gene
  )
  abline(h = -log10(as.numeric(analysis$gwas_signal_p)), col = "#b2182b", lty = 2)
  mtext(paste(unique(decisions_dt[gene == locus$gene]$terminal_state), collapse = ";"), side = 3, cex = 0.65)
}
dev.off()

declared <- c(
  "recovery_analysis_manifest.tsv",
  "recovery_route_manifest.tsv",
  "recovery_dataset_registry.tsv",
  "recovery_request_manifest.tsv",
  "recovery_input_inventory.tsv",
  "recovery_source_checks.tsv",
  "recovery_route_decisions.tsv",
  "recovery_regional_gwas_summary.tsv",
  "recovery_regional_qtl_summary.tsv",
  "recovery_gwas_finemapping.tsv.gz",
  "recovery_qtl_finemapping.tsv.gz",
  "recovery_ld_qc.tsv",
  "recovery_variant_harmonization.tsv.gz",
  "recovery_variant_harmonization_summary.tsv",
  "recovery_colocalization.tsv.gz",
  "recovery_colocalization_qc.tsv",
  "recovery_prior_sensitivity.tsv.gz",
  "recovery_assessability.tsv",
  "recovery_evidence_summary.tsv",
  "recovery_figure_data.tsv.gz",
  "recovery_evidence_matrix.pdf",
  "recovery_evidence_matrix.png",
  "recovery_locus_plots.pdf",
  "recovery_checks.tsv",
  "recovery_artifacts.tsv",
  "recovery_status.tsv"
)

checks <- data.table(
  schema_version = SCHEMA,
  check_id = c(
    "baseline_tier1_hashes_unchanged", "baseline_tier2_hashes_unchanged",
    "route_count_54", "terminal_route_count_54", "evidence_summary_count_47",
    "dataset_selection_frozen", "gwas_case_fraction", "source_checks_pass",
    "all_routes_permitted_terminal_state", "execution_backend_direct",
    "full_phase19_complete_false", "declared_file_count_26"
  ),
  blocking = "TRUE",
  observed = c(
    truth(all(baseline[tier == "tier1"]$status == "pass")),
    truth(all(baseline[tier == "tier2"]$status == "pass")),
    as.character(nrow(routes)), as.character(nrow(decisions_dt)),
    as.character(nrow(evidence_summary)),
    truth(all(registry$selection_frozen_before_result == "TRUE")),
    format(release$gwas_cases / (release$gwas_cases + release$gwas_controls), digits = 17),
    truth(all(source_checks$status == "pass")),
    truth(all(decisions_dt$terminal_state %in% terminal_vocabulary)),
    "direct", "FALSE", as.character(length(declared))
  ),
  expected = c(
    "TRUE", "TRUE", "54", "54", "47", "TRUE",
    format(111326 / 788989, digits = 17), "TRUE", "TRUE",
    "direct", "FALSE", "26"
  ),
  detail = c(
    "Tier 1 artifact hashes reproduced", "Tier 2 artifact hashes reproduced",
    "Frozen nuclear eQTL/sQTL routes", "Every route has one terminal decision",
    "Cumulative candidate-context matrix", "Source choices frozen before result",
    "Bellenguez case-control fraction retained", "All acquired sources validated",
    "Terminal vocabulary enforced", "Actually ran on local direct backend",
    "Remaining Phase 19 scopes stay separate", "Output contract is frozen"
  )
)
checks[, status := ifelse(observed == expected, "pass", "fail")]
write_tsv(checks, "recovery_checks.tsv")
if (any(checks$blocking == "TRUE" & checks$status != "pass")) {
  stop("Blocking recovery checks failed: ", paste(checks[status != "pass"]$check_id, collapse = ", "))
}

count_rows <- function(path) {
  connection <- if (grepl("\\.gz$", path)) gzfile(path, "rt") else file(path, "rt")
  on.exit(close(connection))
  count <- -1L
  while (length(lines <- readLines(connection, n = 100000L, warn = FALSE))) count <- count + length(lines)
  max(0L, count)
}
artifact_targets <- setdiff(declared, c("recovery_artifacts.tsv", "recovery_status.tsv"))
missing <- artifact_targets[!file.exists(file.path(staging, artifact_targets))]
if (length(missing)) stop("Missing declared artifacts: ", paste(missing, collapse = ", "))
artifacts <- rbindlist(lapply(artifact_targets, function(filename) {
  path <- file.path(staging, filename)
  data.table(
    schema_version = SCHEMA, path = filename, bytes = file.info(path)$size,
    sha256 = sha256(path),
    rows = if (grepl("\\.(tsv|tsv\\.gz)$", filename)) count_rows(path) else NA_integer_,
    validation_state = "validated"
  )
}))
write_tsv(artifacts, "recovery_artifacts.tsv")

status <- data.table(
  schema_version = SCHEMA,
  validation_status = "validated_complete_tier2_classical_coloc_recovery",
  run_id = paste0("phase19_tier2_recovery_local_", format(Sys.Date(), "%Y%m%d")),
  execution_stage = "local_production_equivalent",
  execution_backend = "direct",
  publication_namespace = "minerva_production",
  technical_status = "validated_complete_tier2_recovery",
  scientific_status = "terminal_route_specific_recovery_complete",
  baseline_tier1_hashes_unchanged = "TRUE",
  baseline_tier2_hashes_unchanged = "TRUE",
  full_phase19_complete = "FALSE",
  candidate_contexts = nrow(evidence_summary),
  nuclear_recovery_routes = nrow(routes),
  terminal_recovery_routes = nrow(decisions_dt),
  precomputed_resolved_routes = sum(decisions_dt$terminal_state == "precomputed_resolved"),
  custom_resolved_routes = sum(decisions_dt$terminal_state == "custom_resolved"),
  distinct_signal_routes = sum(decisions_dt$terminal_state == "distinct_signals"),
  no_regional_gwas_signal_routes = sum(decisions_dt$terminal_state == "no_regional_gwas_signal"),
  no_regional_qtl_signal_routes = sum(decisions_dt$terminal_state == "no_regional_qtl_signal"),
  model_or_ld_incompatible_routes = sum(decisions_dt$terminal_state == "model_or_ld_incompatible"),
  not_assessable_routes = sum(decisions_dt$terminal_state == "not_assessable"),
  blocking_check_failures = sum(checks$blocking == "TRUE" & checks$status != "pass"),
  output_files = length(declared),
  artifact_manifest_sha256 = sha256(file.path(staging, "recovery_artifacts.tsv")),
  completed_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  next_required_action = ifelse(
    any(decisions_dt$terminal_state %in% c("model_or_ld_incompatible", "not_assessable")),
    "review_route_specific_remaining_source_or_LD_limitations", "none"
  )
)
write_tsv(status, "recovery_status.tsv")

actual <- sort(list.files(staging, all.files = FALSE, no.. = TRUE))
if (!identical(actual, sort(declared))) {
  stop(
    "Output contract mismatch; missing=", paste(setdiff(declared, actual), collapse = ","),
    "; undeclared=", paste(setdiff(actual, declared), collapse = ",")
  )
}
if (dir.exists(output_root)) {
  if (!force) stop("Output appeared during run: ", output_root)
  unlink(output_root, recursive = TRUE)
}
if (!file.rename(staging, output_root)) stop("Atomic publication rename failed")
cat("Published", length(declared), "validated files to", output_root, "\n")
print(decisions_dt[, .N, by = terminal_state][order(terminal_state)])
