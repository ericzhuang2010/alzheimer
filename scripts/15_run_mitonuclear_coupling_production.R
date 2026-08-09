options(stringsAsFactors = FALSE, warn = 1)

phase15_drop_schema <- function(x) {
  if ("schema_version" %in% names(x)) x$schema_version <- NULL
  x
}

phase15_read_table <- function(path) {
  data.table::fread(path, data.table = FALSE, showProgress = FALSE)
}

phase15_require_columns <- function(x, required, label) {
  missing <- setdiff(required, names(x))
  if (length(missing)) {
    stop(label, " is missing required columns: ", paste(missing, collapse = ", "),
         call. = FALSE)
  }
  invisible(TRUE)
}

phase15_production_authorized <- function(cfg) {
  if (!isTRUE(cfg$analysis$definitions_approved) ||
      !isTRUE(cfg$analysis$definitions_frozen)) {
    stop("Phase 15 production requires approved, frozen definitions", call. = FALSE)
  }
  if (!isTRUE(cfg$analysis$production_approved)) {
    stop("Phase 15 production is implemented but not approved; set ",
         "analysis.production_approved only after local validation", call. = FALSE)
  }
  invisible(TRUE)
}

phase15_required_phase13_files <- function() c(
  "respiratory_analysis_manifest.tsv",
  "respiratory_cell_context_manifest.tsv",
  "respiratory_contrast_manifest.tsv",
  "respiratory_module_manifest.tsv",
  "respiratory_module_members.tsv",
  "respiratory_donor_samples.tsv.gz",
  "respiratory_pseudobulk_counts.rds",
  "respiratory_expression_bundle.rds",
  "respiratory_module_coverage.tsv",
  "respiratory_nci_reference_parameters.tsv.gz",
  "respiratory_donor_module_scores.tsv.gz",
  "respiratory_pc1_loadings.tsv.gz",
  "respiratory_module_reliability.tsv",
  "respiratory_module_results.tsv",
  "respiratory_gate_decisions.tsv",
  "respiratory_checks.tsv",
  "respiratory_artifacts.tsv",
  "respiratory_status.tsv"
)

validate_phase13_production_bundle <- function(path, cfg) {
  required <- phase15_required_phase13_files()
  missing <- required[!file.exists(file.path(path, required))]
  if (length(missing)) {
    stop("Phase 13 production bundle is incomplete: ",
         paste(missing, collapse = ", "), call. = FALSE)
  }
  status <- phase15_read_table(file.path(path, "respiratory_status.tsv"))
  checks <- phase15_read_table(file.path(path, "respiratory_checks.tsv"))
  artifacts <- phase15_read_table(file.path(path, "respiratory_artifacts.tsv"))
  phase15_require_columns(
    status, c("execution_stage", "contexts", "modules", "module_memberships",
              "modifier_contrasts", "planned_primary_tests", "validation_status",
              "artifact_manifest_sha256"), "Phase 13 status"
  )
  expected <- cfg$production$phase13_required_dimensions
  observed <- c(
    contexts = status$contexts[[1L]], modules = status$modules[[1L]],
    module_memberships = status$module_memberships[[1L]],
    modifier_contrasts = status$modifier_contrasts[[1L]],
    planned_primary_tests = status$planned_primary_tests[[1L]]
  )
  wanted <- vapply(names(observed), function(x) as.integer(expected[[x]]), integer(1))
  if (nrow(status) != 1L || status$execution_stage[[1L]] != "minerva_production" ||
      status$validation_status[[1L]] !=
        cfg$production$required_phase13_validation_status ||
      !identical(as.integer(observed), as.integer(wanted))) {
    stop("Phase 13 production status does not satisfy the frozen Phase 15 dependency",
         call. = FALSE)
  }
  phase15_require_columns(checks, c("blocking", "passed"), "Phase 13 checks")
  if (any(as.logical(checks$blocking) & !as.logical(checks$passed))) {
    stop("Phase 13 contains failed blocking checks", call. = FALSE)
  }
  phase15_require_columns(artifacts, c("artifact_id", "path", "sha256"),
                          "Phase 13 artifact manifest")
  for (i in seq_len(nrow(artifacts))) {
    local_path <- file.path(path, basename(artifacts$path[[i]]))
    if (!file.exists(local_path) ||
        !identical(sha256_file(local_path), artifacts$sha256[[i]])) {
      stop("Phase 13 artifact hash mismatch: ", artifacts$artifact_id[[i]],
           call. = FALSE)
    }
  }
  if (!identical(sha256_file(file.path(path, "respiratory_artifacts.tsv")),
                 status$artifact_manifest_sha256[[1L]])) {
    stop("Phase 13 terminal artifact-manifest hash does not reproduce", call. = FALSE)
  }
  list(status = status, checks = checks, artifacts = artifacts,
       required_files = required)
}

production_context_manifest <- function(phase13, cfg) {
  primary <- unlist(cfg$production$primary_contexts, use.names = FALSE)
  secondary <- unlist(cfg$production$secondary_contexts, use.names = FALSE)
  ids <- c(primary, secondary)
  configured <- vapply(phase13$contexts, function(x) x$context_id, character(1))
  if (!identical(ids, configured)) {
    stop("Phase 15 production context order does not match frozen Phase 13 order",
         call. = FALSE)
  }
  context_manifest_from_phase13(phase13, ids, primary_ids = primary, pilot = FALSE)
}

load_phase13_production_scores <- function(path, contexts) {
  samples <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_donor_samples.tsv.gz")
  ))
  stored <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_donor_module_scores.tsv.gz")
  ))
  phase15_require_columns(
    samples, c("context_id", "donor_context_id", "projid", "diagnosis", "sex",
               "apoe_group", "group_id", "study", "age_death_scaled", "pmi_scaled",
               "nuclei", "aggregate_percent_mt", "robust_qc_fraction",
               "severe_qc_profile", "primary_eligible", "sensitivity_eligible"),
    "Phase 13 donor samples"
  )
  phase15_require_columns(
    stored, c("context_id", "module_id", "donor_context_id", "projid", "group_id",
              "diagnosis", "sex", "apoe_group", "raw_mean_z", "standardized_score",
              "pc1_score", "module_mean_nci", "module_sd_nci",
              "admitted_gene_count"), "Phase 13 module scores"
  )
  # fread may infer all-digit donor IDs as integers. Recover the exact character
  # key, including leading zeroes, from the authoritative donor/context key.
  samples$projid <- sub("^[^:]+::", "", as.character(samples$donor_context_id))
  stored$projid <- sub("^[^:]+::", "", as.character(stored$donor_context_id))
  samples$donor_context_id <- as.character(samples$donor_context_id)
  stored$donor_context_id <- as.character(stored$donor_context_id)
  samples <- samples[as.logical(samples$primary_eligible) &
                       samples$context_id %in% contexts$context_id, , drop = FALSE]
  keep <- c("mtdna_oxphos_13", "nuclear_oxphos_structural_86")
  stored <- stored[stored$module_id %in% keep &
                     stored$context_id %in% contexts$context_id, , drop = FALSE]
  if (anyDuplicated(stored[c("donor_context_id", "module_id")]) ||
      anyDuplicated(samples$donor_context_id)) {
    stop("Phase 13 donor/module keys are not unique", call. = FALSE)
  }
  module_part <- function(module_id, prefix) {
    x <- stored[stored$module_id == module_id, c(
      "context_id", "donor_context_id", "projid", "group_id", "diagnosis", "sex",
      "apoe_group", "raw_mean_z", "standardized_score", "pc1_score",
      "module_mean_nci", "module_sd_nci", "admitted_gene_count"
    ), drop = FALSE]
    names(x)[8:ncol(x)] <- paste0(prefix, names(x)[8:ncol(x)])
    x
  }
  mt <- module_part("mtdna_oxphos_13", "mtdna_")
  nu <- module_part("nuclear_oxphos_structural_86", "nuclear_")
  identity_keys <- c("context_id", "donor_context_id", "projid", "group_id",
                     "diagnosis", "sex", "apoe_group")
  pairs <- merge(mt, nu, by = identity_keys, all = TRUE, sort = FALSE)
  if (nrow(pairs) != nrow(samples) || anyNA(pairs$donor_context_id)) {
    stop("Both Phase 13 direct-respiratory scores are required for every eligible profile",
         call. = FALSE)
  }
  score_columns <- setdiff(names(pairs), identity_keys)
  pairs <- merge(samples, pairs[c("donor_context_id", score_columns)],
                 by = "donor_context_id", all.x = TRUE, sort = FALSE)
  if (any(!is.finite(as.matrix(pairs[c(
      "mtdna_standardized_score", "nuclear_standardized_score",
      "mtdna_pc1_score", "nuclear_pc1_score"
    )])))) {
    stop("Phase 13 contains nonfinite direct-respiratory scores", call. = FALSE)
  }
  pairs$original_projid <- as.character(pairs$projid)
  pairs$sex_APOE_stratum <- paste(pairs$sex, pairs$apoe_group, sep = "__")
  pairs$M <- pairs$mtdna_standardized_score
  pairs$N <- pairs$nuclear_standardized_score
  pairs$M_pc1 <- pairs$mtdna_pc1_score
  pairs$N_pc1 <- pairs$nuclear_pc1_score
  pairs$profile_eligible_20 <- as.logical(pairs$primary_eligible)
  pairs$profile_eligible_50 <- as.logical(pairs$sensitivity_eligible)
  pairs$donor_context_id <- as.character(pairs$donor_context_id)
  order_key <- match(pairs$context_id, contexts$context_id)
  pairs <- pairs[order(order_key, pairs$projid), , drop = FALSE]
  rownames(pairs) <- NULL
  for (context_id in contexts$context_id) {
    x <- pairs[pairs$context_id == context_id & pairs$diagnosis == "NCI", ]
    for (column in c("M", "N")) {
      if (abs(mean(x[[column]])) > 1e-8 || abs(stats::sd(x[[column]]) - 1) > 1e-8) {
        stop("Stored Phase 13 score scaling does not reproduce in ", context_id,
             " for ", column, call. = FALSE)
      }
    }
  }
  pairs
}

reconstruct_phase13_score_error <- function(path, scores) {
  bundle <- readRDS(file.path(path, "respiratory_expression_bundle.rds"))
  parameters <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_nci_reference_parameters.tsv.gz")
  ))
  errors <- numeric()
  for (context_id in unique(scores$context_id)) {
    expression <- bundle$contexts[[context_id]]
    for (module_id in c("mtdna_oxphos_13", "nuclear_oxphos_structural_86")) {
      p <- parameters[parameters$context_id == context_id &
                        parameters$module_id == module_id &
                        as.logical(parameters$admitted), , drop = FALSE]
      assay <- p$assay_feature_identifier
      values <- expression$logcpm[assay, , drop = FALSE]
      z <- sweep(values, 1L, p$nci_mean_logcpm, "-")
      z <- sweep(z, 1L, p$nci_sd_logcpm, "/")
      raw <- colMeans(z)
      prefix <- if (module_id == "mtdna_oxphos_13") "mtdna_" else "nuclear_"
      d <- scores[scores$context_id == context_id, , drop = FALSE]
      idx <- match(d$projid, colnames(values))
      reconstructed <- (raw[idx] - d[[paste0(prefix, "module_mean_nci")]]) /
        d[[paste0(prefix, "module_sd_nci")]]
      errors <- c(errors, abs(reconstructed - d[[paste0(prefix, "standardized_score")]]))
    }
  }
  max(errors, na.rm = TRUE)
}

load_phase15_resampling_inputs <- function(path, contexts, phase13) {
  if (!"package:Matrix" %in% search()) {
    suppressPackageStartupMessages(
      library("Matrix", character.only = TRUE)
    )
  }
  counts_bundle <- readRDS(file.path(path, "respiratory_pseudobulk_counts.rds"))
  expression_bundle <- readRDS(file.path(path, "respiratory_expression_bundle.rds"))
  coverage <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_module_coverage.tsv")
  ))
  parameters <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_nci_reference_parameters.tsv.gz")
  ))
  members <- phase15_drop_schema(phase15_read_table(
    file.path(path, "respiratory_module_members.tsv")
  ))
  module_ids <- c("mtdna_oxphos_13", "nuclear_oxphos_structural_86")
  out <- list()
  for (context_id in contexts$context_id) {
    samples <- counts_bundle$samples[[context_id]]
    samples <- samples[as.logical(samples$primary_eligible), , drop = FALSE]
    samples$sex_APOE_stratum <- paste(samples$sex, samples$apoe_group, sep = "__")
    counts <- counts_bundle$contexts[[context_id]][, samples$projid, drop = FALSE]
    cov <- coverage[coverage$context_id == context_id &
                      coverage$module_id %in% module_ids, , drop = FALSE]
    if (nrow(cov) != 2L || !all(as.logical(cov$coverage_pass))) {
      stop("Phase 13 direct-respiratory coverage is not valid in ", context_id,
           call. = FALSE)
    }
    admitted <- setNames(lapply(module_ids, function(module_id) {
      value <- cov$admitted_assay_features[cov$module_id == module_id]
      strsplit(value, "|", fixed = TRUE)[[1L]]
    }), module_ids)
    tested <- expression_bundle$contexts[[context_id]]$tested_genes
    if (!all(unlist(admitted) %in% tested) || !all(tested %in% rownames(counts))) {
      stop("Phase 13 resampling genes do not match the expression bundle in ",
           context_id, call. = FALSE)
    }
    gene_z <- setNames(lapply(module_ids, function(module_id) {
      p <- parameters[parameters$context_id == context_id &
                        parameters$module_id == module_id &
                        as.logical(parameters$admitted), , drop = FALSE]
      values <- expression_bundle$contexts[[context_id]]$logcpm[
        p$assay_feature_identifier, samples$projid, drop = FALSE
      ]
      z <- sweep(sweep(values, 1L, p$nci_mean_logcpm, "-"),
                 1L, p$nci_sd_logcpm, "/")
      rownames(z) <- p$frozen_gene_symbol
      z
    }), module_ids)
    member_metadata <- members[members$module_id %in% module_ids,
                               c("module_id", "frozen_gene_symbol",
                                 "assay_feature_identifier", "respiratory_complex"),
                               drop = FALSE]
    out[[context_id]] <- list(
      context_id = context_id, counts = counts, samples = samples,
      tested_genes = tested, admitted = admitted,
      prior_count = as.numeric(phase13$analysis$prior_count),
      gene_z = gene_z, member_metadata = member_metadata
    )
  }
  out
}

rebuild_phase15_context_scores <- function(input, original_ids, draw_ids = original_ids,
                                           normalization = "full") {
  idx <- match(as.character(original_ids), as.character(input$samples$projid))
  keep <- !is.na(idx)
  idx <- idx[keep]
  draw_ids <- as.character(draw_ids)[keep]
  original_ids <- as.character(original_ids)[keep]
  if (!length(idx) || anyDuplicated(draw_ids)) {
    stop("Invalid donor draw for context ", input$context_id, call. = FALSE)
  }
  samples <- input$samples[idx, , drop = FALSE]
  samples$original_projid <- original_ids
  samples$projid <- draw_ids
  samples$donor_context_id <- paste(input$context_id, draw_ids, sep = "::")
  counts <- input$counts[input$tested_genes, idx, drop = FALSE]
  colnames(counts) <- draw_ids
  y <- edgeR::DGEList(counts)
  if (normalization == "full") {
    y <- edgeR::calcNormFactors(y, method = "TMM")
  } else if (normalization == "nuclear_only") {
    nuclear <- !grepl("^MT-", rownames(counts), ignore.case = TRUE)
    y_nuclear <- edgeR::calcNormFactors(edgeR::DGEList(counts[nuclear, , drop = FALSE]),
                                        method = "TMM")
    y$samples$norm.factors <- y_nuclear$samples$norm.factors
  } else stop("Unknown normalization variant: ", normalization, call. = FALSE)
  logcpm <- edgeR::cpm(y, log = TRUE, prior.count = input$prior_count)
  nci <- samples$diagnosis == "NCI"
  if (sum(nci) < 3L) stop("Too few NCI donors in resample", call. = FALSE)
  module_score <- function(module_id) {
    values <- logcpm[input$admitted[[module_id]], , drop = FALSE]
    means <- rowMeans(values[, nci, drop = FALSE])
    sds <- apply(values[, nci, drop = FALSE], 1L, stats::sd)
    if (any(!is.finite(sds) | sds <= 0)) stop("Nonpositive resampled gene SD")
    z <- sweep(sweep(values, 1L, means, "-"), 1L, sds, "/")
    raw <- colMeans(z)
    scale <- stats::sd(raw[nci])
    if (!is.finite(scale) || scale <= 0) stop("Nonpositive resampled module SD")
    (raw - mean(raw[nci])) / scale
  }
  samples$M <- module_score("mtdna_oxphos_13")
  samples$N <- module_score("nuclear_oxphos_structural_86")
  samples$M_pc1 <- NA_real_
  samples$N_pc1 <- NA_real_
  samples$sex_APOE_stratum <- paste(samples$sex, samples$apoe_group, sep = "__")
  samples$profile_eligible_20 <- samples$nuclei >= 20L
  samples$profile_eligible_50 <- samples$nuclei >= 50L
  samples
}

rebuild_phase15_scores <- function(inputs, draw, context_ids = names(inputs),
                                   normalization = "full") {
  bind_rows(lapply(context_ids, function(context_id) {
    rebuild_phase15_context_scores(
      inputs[[context_id]], draw$original_projid, draw$projid, normalization
    )
  }))
}

phase15_result_rows <- function(analysis) {
  general <- analysis$results$general
  modifier <- analysis$results$modifier
  general$scope_id <- "general"
  modifier$scope_id <- "modifier"
  bind_rows(list(general, modifier))
}

phase15_sensitivity_rows <- function(analysis, sensitivity_type) {
  x <- phase15_result_rows(analysis)
  x$sensitivity_type <- sensitivity_type
  x[c("sensitivity_type", "scope_id", "context_id", "context_role", "endpoint_id",
      "contrast_id", "estimate", "standard_error", "ci_low", "ci_high", "p_value",
      "model_status", "failure_reason")]
}

phase15_stability_rows <- function(analysis, analysis_type, repetition_id,
                                   omitted = NA_character_, seed = NA_integer_) {
  x <- phase15_result_rows(analysis)
  out <- x[c("scope_id", "context_id", "endpoint_id", "contrast_id", "estimate",
             "p_value", "model_status", "failure_reason")]
  out$analysis_type <- analysis_type
  out$repetition_id <- as.integer(repetition_id)
  out$seed <- as.integer(seed)
  out$omitted_original_projid <- as.character(omitted)
  out$donor_resampling_unit <- "whole_donor"
  out
}

phase15_failed_stability_rows <- function(primary_rows, analysis_type, repetition_id,
                                          reason, omitted = NA_character_,
                                          seed = NA_integer_) {
  out <- primary_rows[c("scope_id", "context_id", "endpoint_id", "contrast_id")]
  out$estimate <- NA_real_
  out$p_value <- NA_real_
  out$model_status <- "not_estimated"
  out$failure_reason <- paste0(analysis_type, ":", reason)
  out$analysis_type <- analysis_type
  out$repetition_id <- as.integer(repetition_id)
  out$seed <- as.integer(seed)
  out$omitted_original_projid <- as.character(omitted)
  out$donor_resampling_unit <- "whole_donor"
  out
}

run_phase15_production_stability <- function(scores, inputs, cfg, phase13, contexts,
                                             endpoints, fingerprint, workers) {
  primary_analysis <- analyze_scores(scores, cfg, phase13, contexts, endpoints,
                                     fingerprint, production = TRUE)
  primary_rows <- phase15_result_rows(primary_analysis)
  donor_meta <- unique(scores[c("original_projid", "group_id")])
  consistency <- aggregate(group_id ~ original_projid, donor_meta,
                           function(x) length(unique(x)))
  if (any(consistency$group_id != 1L)) {
    stop("Donor group metadata are inconsistent across contexts", call. = FALSE)
  }
  donor_meta <- donor_meta[!duplicated(donor_meta$original_projid), , drop = FALSE]
  groups <- unlist(phase13$groups, use.names = FALSE)
  boot_repetitions <- as.integer(cfg$production$bootstrap_repetitions)
  balance_repetitions <- as.integer(cfg$production$balance_repetitions)
  cat("Phase 15 production stability: ", boot_repetitions,
      " paired-context donor bootstraps\n", sep = "")
  bootstrap_one <- function(rep) {
    seed <- seed_for(cfg, paste("production", "bootstrap", rep, sep = "::"))
    set.seed(seed)
    selected <- unlist(lapply(groups, function(group) {
      ids <- donor_meta$original_projid[donor_meta$group_id == group]
      sample(ids, length(ids), replace = TRUE)
    }), use.names = FALSE)
    draw <- data.frame(
      original_projid = selected,
      projid = paste0(selected, "::bootstrap_", seq_along(selected)),
      stringsAsFactors = FALSE
    )
    tryCatch({
      rebuilt <- rebuild_phase15_scores(inputs, draw)
      analysis <- analyze_scores(rebuilt, cfg, phase13, contexts, endpoints,
                                 fingerprint, production = TRUE)
      phase15_stability_rows(analysis, "donor_bootstrap", rep, seed = seed)
    }, error = function(e) phase15_failed_stability_rows(
      primary_rows, "donor_bootstrap", rep, conditionMessage(e), seed = seed
    ))
  }
  bootstrap <- bind_rows(ordered_lapply(
    as.list(seq_len(boot_repetitions)), bootstrap_one, workers
  ))

  donors <- sort(donor_meta$original_projid)
  loo_limit <- cfg$production$loo_donor_limit %||% length(donors)
  loo_limit <- suppressWarnings(as.integer(loo_limit))
  if (!is.finite(loo_limit) || loo_limit < 1L) {
    stop("production.loo_donor_limit must be a positive integer", call. = FALSE)
  }
  donors <- head(donors, loo_limit)
  cat("Phase 15 production stability: ", length(donors),
      " paired-context leave-one-donor-out fits\n", sep = "")
  loo_one <- function(i) {
    omitted <- donors[[i]]
    kept <- donors[donors != omitted]
    draw <- data.frame(original_projid = kept, projid = kept,
                       stringsAsFactors = FALSE)
    tryCatch({
      rebuilt <- rebuild_phase15_scores(inputs, draw)
      analysis <- analyze_scores(rebuilt, cfg, phase13, contexts, endpoints,
                                 fingerprint, production = TRUE)
      phase15_stability_rows(analysis, "leave_one_donor_out", i, omitted)
    }, error = function(e) phase15_failed_stability_rows(
      primary_rows, "leave_one_donor_out", i, conditionMessage(e), omitted
    ))
  }
  loo <- bind_rows(ordered_lapply(as.list(seq_along(donors)), loo_one, workers))

  general_tasks <- list()
  modifier_tasks <- list()
  for (context_id in contexts$context_id) {
    for (rep in seq_len(balance_repetitions)) {
      general_tasks[[length(general_tasks) + 1L]] <- list(
        context_id = context_id, repetition = rep
      )
      for (contrast_index in seq_along(phase13$contrasts)) {
        modifier_tasks[[length(modifier_tasks) + 1L]] <- list(
          context_id = context_id, repetition = rep,
          contrast_index = contrast_index
        )
      }
    }
  }
  cat("Phase 15 production stability: ", length(general_tasks),
      " general and ", length(modifier_tasks), " modifier balance fits\n", sep = "")
  general_balance_one <- function(task) {
    context_id <- task$context_id
    rep <- task$repetition
    samples <- inputs[[context_id]]$samples
    seed <- seed_for(cfg, paste("production", context_id, "general_balance", rep,
                                sep = "::"))
    set.seed(seed)
    selected <- unlist(lapply(unique(samples$sex_APOE_stratum), function(stratum) {
      x <- samples[samples$sex_APOE_stratum == stratum, , drop = FALSE]
      minimum <- min(table(factor(x$diagnosis, levels = c("NCI", "AD"))))
      unlist(lapply(c("NCI", "AD"), function(diagnosis) {
        sample(x$projid[x$diagnosis == diagnosis], minimum, replace = FALSE)
      }), use.names = FALSE)
    }), use.names = FALSE)
    draw <- data.frame(original_projid = selected, projid = selected,
                       stringsAsFactors = FALSE)
    target <- primary_rows[primary_rows$scope_id == "general" &
                             primary_rows$context_id == context_id, , drop = FALSE]
    tryCatch({
      rebuilt <- rebuild_phase15_scores(inputs, draw, context_id)
      one_context <- contexts[contexts$context_id == context_id, , drop = FALSE]
      analysis <- analyze_scores(rebuilt, cfg, phase13, one_context, endpoints,
                                 fingerprint, production = TRUE)
      rows <- phase15_stability_rows(
        analysis, "group_size_balanced", rep, seed = seed
      )
      rows[rows$scope_id == "general", , drop = FALSE]
    }, error = function(e) phase15_failed_stability_rows(
      target, "group_size_balanced", rep, conditionMessage(e), seed = seed
    ))
  }
  general_balance <- bind_rows(ordered_lapply(general_tasks, general_balance_one, workers))

  modifier_balance_one <- function(task) {
    context_id <- task$context_id
    rep <- task$repetition
    contrast <- phase13$contrasts[[task$contrast_index]]
    samples <- inputs[[context_id]]$samples
    required <- unlist(contrast$required_groups, use.names = FALSE)
    smallest <- min(table(factor(samples$group_id, levels = required)))
    seed <- seed_for(cfg, paste("production", context_id, contrast$contrast_id,
                                "modifier_balance", rep, sep = "::"))
    set.seed(seed)
    selected_required <- unlist(lapply(required, function(group) {
      sample(samples$projid[samples$group_id == group], smallest, replace = FALSE)
    }), use.names = FALSE)
    selected <- c(selected_required, samples$projid[!samples$group_id %in% required])
    draw <- data.frame(original_projid = selected, projid = selected,
                       stringsAsFactors = FALSE)
    target <- primary_rows[primary_rows$scope_id == "modifier" &
                             primary_rows$context_id == context_id &
                             primary_rows$contrast_id == contrast$contrast_id, , drop = FALSE]
    tryCatch({
      rebuilt <- rebuild_phase15_scores(inputs, draw, context_id)
      one_context <- contexts[contexts$context_id == context_id, , drop = FALSE]
      analysis <- analyze_scores(rebuilt, cfg, phase13, one_context, endpoints,
                                 fingerprint, production = TRUE)
      rows <- phase15_stability_rows(
        analysis, "group_size_balanced", rep, seed = seed
      )
      rows[rows$scope_id == "modifier" &
             rows$contrast_id == contrast$contrast_id, , drop = FALSE]
    }, error = function(e) phase15_failed_stability_rows(
      target, "group_size_balanced", rep, conditionMessage(e), seed = seed
    ))
  }
  modifier_balance <- bind_rows(ordered_lapply(
    modifier_tasks, modifier_balance_one, workers
  ))
  out <- bind_rows(list(bootstrap, loo, general_balance, modifier_balance))
  attr(out, "loo_planned") <- length(donors)
  out
}

summarize_phase15_production_stability <- function(primary, replicates, cfg,
                                                   loo_planned) {
  boot_planned <- as.integer(cfg$production$bootstrap_repetitions)
  balance_planned <- as.integer(cfg$production$balance_repetitions)
  success_threshold <- as.numeric(cfg$stability$minimum_success_fraction)
  direction_threshold <- as.numeric(cfg$stability$minimum_direction_fraction)
  bind_rows(lapply(seq_len(nrow(primary)), function(i) {
    row <- primary[i, , drop = FALSE]
    x <- replicates[
      replicates$scope_id == row$scope_id &
        replicates$context_id == row$context_id &
        replicates$endpoint_id == row$endpoint_id &
        replicates$contrast_id == row$contrast_id, , drop = FALSE
    ]
    one <- function(type) x[x$analysis_type == type, , drop = FALSE]
    boot <- one("donor_bootstrap")
    balance <- one("group_size_balanced")
    loo <- one("leave_one_donor_out")
    ok <- function(z) z$model_status == "estimated" & is.finite(z$estimate)
    boot_ok <- ok(boot)
    balance_ok <- ok(balance)
    loo_ok <- ok(loo)
    direction <- function(z, good) {
      if (!any(good) || !is.finite(row$estimate) || row$estimate == 0) NA_real_ else
        mean(sign(z$estimate[good]) == sign(row$estimate))
    }
    boot_direction <- direction(boot, boot_ok)
    balance_direction <- direction(balance, balance_ok)
    loo_reversals <- if (any(loo_ok) && is.finite(row$estimate) && row$estimate != 0) {
      sum(sign(loo$estimate[loo_ok]) != sign(row$estimate))
    } else NA_integer_
    loo_change <- if (any(loo_ok) && is.finite(row$estimate))
      abs(loo$estimate[loo_ok] - row$estimate) else numeric()
    stable <- !startsWith(row$eligibility_status, "not_testable")
    data.frame(
      scope_id = row$scope_id, context_id = row$context_id,
      endpoint_id = row$endpoint_id, contrast_id = row$contrast_id,
      primary_estimate = row$estimate,
      bootstrap_planned = if (stable) boot_planned else 0L,
      bootstrap_successful = sum(boot_ok),
      bootstrap_median = if (any(boot_ok)) stats::median(boot$estimate[boot_ok]) else NA_real_,
      bootstrap_ci_low = if (any(boot_ok)) stats::quantile(
        boot$estimate[boot_ok], 0.025, names = FALSE) else NA_real_,
      bootstrap_ci_high = if (any(boot_ok)) stats::quantile(
        boot$estimate[boot_ok], 0.975, names = FALSE) else NA_real_,
      bootstrap_same_direction_fraction = boot_direction,
      bootstrap_pass = stable && sum(boot_ok) >= ceiling(boot_planned * success_threshold) &&
        is.finite(boot_direction) && boot_direction >= direction_threshold,
      balance_planned = if (stable) balance_planned else 0L,
      balance_successful = sum(balance_ok),
      balance_same_direction_fraction = balance_direction,
      balance_pass = stable && sum(balance_ok) >= ceiling(balance_planned * success_threshold) &&
        is.finite(balance_direction) && balance_direction >= direction_threshold,
      loo_planned = if (stable) as.integer(loo_planned) else 0L,
      loo_successful = sum(loo_ok), loo_sign_reversals = loo_reversals,
      loo_largest_absolute_change = if (length(loo_change)) max(loo_change) else NA_real_,
      loo_largest_change_donor = if (length(loo_change))
        loo$omitted_original_projid[loo_ok][[which.max(loo_change)]] else NA_character_,
      loo_pass = stable && sum(loo_ok) == loo_planned &&
        is.finite(loo_reversals) && loo_reversals == 0L,
      stability_pass = stable &&
        sum(boot_ok) >= ceiling(boot_planned * success_threshold) &&
        sum(balance_ok) >= ceiling(balance_planned * success_threshold) &&
        is.finite(boot_direction) && boot_direction >= direction_threshold &&
        is.finite(balance_direction) && balance_direction >= direction_threshold &&
        sum(loo_ok) == loo_planned && is.finite(loo_reversals) && loo_reversals == 0L,
      stringsAsFactors = FALSE
    )
  }))
}

rebuild_phase15_static_variant <- function(inputs, predicate,
                                           normalization = "full") {
  bind_rows(lapply(names(inputs), function(context_id) {
    input <- inputs[[context_id]]
    keep <- predicate(input$samples)
    ids <- input$samples$projid[keep]
    rebuild_phase15_context_scores(input, ids, ids, normalization)
  }))
}

phase15_evaluate_existing_endpoints <- function(endpoint_bundle, cfg, phase13, contexts,
                                                endpoints, fingerprint,
                                                extra_covariates) {
  list(
    endpoint_bundle = endpoint_bundle,
    results = evaluate_models(
      endpoint_bundle, phase13, contexts, endpoints, cfg, fingerprint,
      extra_covariates = extra_covariates, production = TRUE
    )
  )
}

phase15_reference_variant <- function(scores, primary_bundle, cfg, phase13, contexts,
                                      endpoints, fingerprint, variant) {
  bundle <- primary_bundle
  data <- bundle$data
  status_rows <- list()
  for (context_id in contexts$context_id) {
    idx <- which(data$context_id == context_id)
    d <- data[idx, , drop = FALSE]
    d$sex_APOE_stratum <- factor(
      d$sex_APOE_stratum,
      levels = c("Female__e2", "Female__e33", "Female__e4",
                 "Male__e2", "Male__e33", "Male__e4")
    )
    d$sex <- factor(d$sex, levels = c("Female", "Male"))
    d$apoe_group <- factor(d$apoe_group, levels = c("e2", "e33", "e4"))
    d$study <- factor(d$study, levels = c("MAP", "ROS"))
    nci <- d[d$diagnosis == "NCI", , drop = FALSE]
    formula <- if (variant == "full_nci_reference") {
      M ~ N + sex_APOE_stratum + age_death_scaled + pmi_scaled + study
    } else if (variant == "additive_nci_reference") {
      M ~ N + sex + apoe_group + age_death_scaled + pmi_scaled + study
    } else stop("Unknown NCI reference variant", call. = FALSE)
    fit <- tryCatch(stats::lm(formula, data = nci), error = function(e) e)
    success <- !inherits(fit, "error") && fit$rank == length(stats::coef(fit)) &&
      !anyNA(stats::coef(fit))
    failure <- if (success) "" else if (inherits(fit, "error")) conditionMessage(fit) else
      "rank_deficient_reference_sensitivity"
    residual <- rep(NA_real_, nrow(d))
    if (success) {
      predicted <- tryCatch(stats::predict(fit, newdata = d),
                            error = function(e) rep(NA_real_, nrow(d)))
      raw <- d$M - predicted
      scale <- stats::sd(raw[d$diagnosis == "NCI"])
      success <- all(is.finite(predicted)) && is.finite(scale) && scale > 0
      if (success) {
        residual <- (raw - mean(raw[d$diagnosis == "NCI"])) / scale
      } else failure <- "invalid_reference_sensitivity_predictions"
    }
    data$nci_reference_residual[idx] <- residual
    data$reference_status[idx] <- if (success) "eligible" else failure
    status_rows[[context_id]] <- data.frame(
      context_id = context_id, reference_success = success,
      reference_failure_reason = failure,
      nci_donors = nrow(nci), ad_donors = sum(d$diagnosis == "AD")
    )
  }
  bundle$data <- data
  bundle$context_status <- bind_rows(status_rows)
  list(
    endpoint_bundle = bundle,
    results = evaluate_models(bundle, phase13, contexts, endpoints, cfg, fingerprint,
                              production = TRUE)
  )
}

phase15_add_sensitivity_agreement <- function(rows, primary_rows) {
  key <- c("scope_id", "context_id", "endpoint_id", "contrast_id")
  reference <- primary_rows[c(key, "estimate")]
  names(reference)[names(reference) == "estimate"] <- "primary_estimate"
  out <- merge(rows, reference, by = key, all.x = TRUE, sort = FALSE)
  out$direction_retained <- is.finite(out$estimate) & is.finite(out$primary_estimate) &
    out$estimate * out$primary_estimate > 0
  out$relative_magnitude <- abs(out$estimate) / pmax(abs(out$primary_estimate), 1e-12)
  out$sensitivity_status <- ifelse(
    out$model_status == "estimated" & is.finite(out$estimate), "estimated",
    paste0("not_testable:", out$failure_reason)
  )
  out
}

run_phase15_production_sensitivities <- function(scores, inputs, primary, cfg, phase13,
                                                 contexts, endpoints, fingerprint) {
  rows <- list()
  threshold <- rebuild_phase15_static_variant(
    inputs, function(samples) samples$nuclei >= 50L
  )
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    analyze_scores(threshold, cfg, phase13, contexts, endpoints, fingerprint,
                   production = TRUE), "fifty_nucleus"
  )
  pc1 <- scores
  pc1$M <- pc1$M_pc1
  pc1$N <- pc1$N_pc1
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    analyze_scores(pc1, cfg, phase13, contexts, endpoints, fingerprint,
                   production = TRUE), "paired_PC1"
  )
  nuclear_only <- rebuild_phase15_static_variant(
    inputs, function(samples) rep(TRUE, nrow(samples)), "nuclear_only"
  )
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    analyze_scores(nuclear_only, cfg, phase13, contexts, endpoints, fingerprint,
                   production = TRUE), "nuclear_only_TMM"
  )
  severe <- rebuild_phase15_static_variant(
    inputs, function(samples) !as.logical(samples$severe_qc_profile)
  )
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    analyze_scores(severe, cfg, phase13, contexts, endpoints, fingerprint,
                   production = TRUE), "severe_QC_exclusion"
  )
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    phase15_evaluate_existing_endpoints(
      primary$endpoint_bundle, cfg, phase13, contexts, endpoints, fingerprint,
      "robust_qc_fraction"
    ), "robust_QC_covariate"
  )
  rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
    phase15_evaluate_existing_endpoints(
      primary$endpoint_bundle, cfg, phase13, contexts, endpoints, fingerprint,
      "aggregate_percent_mt"
    ), "percent_mt_diagnostic"
  )
  for (variant in c("full_nci_reference", "additive_nci_reference")) {
    rows[[length(rows) + 1L]] <- phase15_sensitivity_rows(
      phase15_reference_variant(
        scores, primary$endpoint_bundle, cfg, phase13, contexts, endpoints,
        fingerprint, variant
      ), variant
    )
  }
  assignment_rows <- list()
  assignment_count <- as.integer(cfg$production$reference_fold_assignments)
  for (assignment_id in seq_len(assignment_count)) {
    analysis <- analyze_scores(
      scores, cfg, phase13, contexts, endpoints, fingerprint,
      assignment_id = assignment_id, production = TRUE
    )
    x <- phase15_sensitivity_rows(analysis, "reference_fold_assignment")
    x <- x[x$endpoint_id == "nci_reference_residual", , drop = FALSE]
    x$repetition_id <- assignment_id
    assignment_rows[[assignment_id]] <- x
  }
  static <- bind_rows(rows)
  static$repetition_id <- NA_integer_
  out <- bind_rows(list(static, bind_rows(assignment_rows)))
  phase15_add_sensitivity_agreement(out, phase15_result_rows(primary))
}

phase15_score_from_gene_z <- function(z, samples, keep) {
  keep <- intersect(keep, rownames(z))
  if (!length(keep)) return(rep(NA_real_, ncol(z)))
  raw <- colMeans(z[keep, , drop = FALSE])
  nci <- samples$diagnosis == "NCI"
  scale <- stats::sd(raw[nci])
  if (!is.finite(scale) || scale <= 0) return(rep(NA_real_, length(raw)))
  (raw - mean(raw[nci])) / scale
}

phase15_influence_definitions <- function(inputs) {
  first <- inputs[[1L]]
  mt_genes <- rownames(first$gene_z$mtdna_oxphos_13)
  c(
    setNames(lapply(mt_genes, function(x) list(kind = "omit_mt_gene", id = x)),
             paste0("omit_mt_gene_", mt_genes)),
    setNames(lapply(c("I", "II", "III", "IV", "V"), function(x)
      list(kind = "omit_nuclear_complex", id = x)),
      paste0("omit_nuclear_complex_", c("I", "II", "III", "IV", "V"))),
    list(nuclear_82_gene = list(kind = "nuclear_82_gene", id = "II")),
    setNames(lapply(c("I", "III", "IV", "V"), function(x)
      list(kind = "matched_complex", id = x)),
      paste0("matched_complex_", c("I", "III", "IV", "V")))
  )
}

phase15_influence_scores <- function(scores, inputs, definition) {
  out <- scores
  for (context_id in names(inputs)) {
    input <- inputs[[context_id]]
    idx <- which(out$context_id == context_id)
    score_order <- match(out$projid[idx], input$samples$projid)
    meta <- input$member_metadata
    mt_meta <- meta[meta$module_id == "mtdna_oxphos_13", , drop = FALSE]
    nu_meta <- meta[meta$module_id == "nuclear_oxphos_structural_86", , drop = FALSE]
    mt_keep <- rownames(input$gene_z$mtdna_oxphos_13)
    nu_keep <- rownames(input$gene_z$nuclear_oxphos_structural_86)
    if (definition$kind == "omit_mt_gene") {
      mt_keep <- setdiff(mt_keep, definition$id)
    } else if (definition$kind == "omit_nuclear_complex") {
      omit <- nu_meta$frozen_gene_symbol[nu_meta$respiratory_complex == definition$id]
      nu_keep <- setdiff(nu_keep, omit)
    } else if (definition$kind == "nuclear_82_gene") {
      omit <- nu_meta$frozen_gene_symbol[nu_meta$respiratory_complex == "II"]
      nu_keep <- setdiff(nu_keep, omit)
    } else if (definition$kind == "matched_complex") {
      mt_keep <- intersect(mt_keep, mt_meta$frozen_gene_symbol[
        mt_meta$respiratory_complex == definition$id
      ])
      nu_keep <- intersect(nu_keep, nu_meta$frozen_gene_symbol[
        nu_meta$respiratory_complex == definition$id
      ])
    }
    M <- phase15_score_from_gene_z(input$gene_z$mtdna_oxphos_13,
                                   input$samples, mt_keep)
    N <- phase15_score_from_gene_z(input$gene_z$nuclear_oxphos_structural_86,
                                   input$samples, nu_keep)
    out$M[idx] <- M[score_order]
    out$N[idx] <- N[score_order]
  }
  out
}

run_phase15_gene_complex_influence <- function(scores, inputs, cfg, phase13,
                                               contexts, endpoints, fingerprint) {
  definitions <- phase15_influence_definitions(inputs)
  rows <- bind_rows(lapply(names(definitions), function(name) {
    definition <- definitions[[name]]
    variant <- phase15_influence_scores(scores, inputs, definition)
    analysis <- analyze_scores(variant, cfg, phase13, contexts, endpoints,
                               fingerprint, production = TRUE)
    x <- phase15_result_rows(analysis)
    data.frame(
      influence_type = definition$kind, influence_id = definition$id,
      scope_id = x$scope_id, context_id = x$context_id,
      endpoint_id = x$endpoint_id, contrast_id = x$contrast_id,
      sensitivity_estimate = x$estimate, model_status = x$model_status,
      failure_reason = x$failure_reason, stringsAsFactors = FALSE
    )
  }))
  primary_rows <- phase15_result_rows(analyze_scores(
    scores, cfg, phase13, contexts, endpoints, fingerprint, production = TRUE
  ))
  reference <- primary_rows[c("scope_id", "context_id", "endpoint_id", "contrast_id",
                              "estimate", "sesoi")]
  names(reference)[names(reference) == "estimate"] <- "primary_estimate"
  out <- merge(rows, reference,
               by = c("scope_id", "context_id", "endpoint_id", "contrast_id"),
               all.x = TRUE, sort = FALSE)
  out$direction_retained <- is.finite(out$sensitivity_estimate) &
    out$sensitivity_estimate * out$primary_estimate > 0
  out$relative_magnitude <- abs(out$sensitivity_estimate) /
    pmax(abs(out$primary_estimate), 1e-12)
  out$opposite_sesoi_effect <- is.finite(out$sensitivity_estimate) &
    out$sensitivity_estimate * out$primary_estimate < 0 &
    abs(out$sensitivity_estimate) >= out$sesoi
  out
}

summarize_phase15_influence_pass <- function(primary, influence) {
  bind_rows(lapply(seq_len(nrow(primary)), function(i) {
    row <- primary[i, , drop = FALSE]
    x <- influence[
      influence$scope_id == row$scope_id & influence$context_id == row$context_id &
        influence$endpoint_id == row$endpoint_id &
        influence$contrast_id == row$contrast_id, , drop = FALSE
    ]
    mt <- x[x$influence_type == "omit_mt_gene", , drop = FALSE]
    nu <- x[x$influence_type == "omit_nuclear_complex", , drop = FALSE]
    n82 <- x[x$influence_type == "nuclear_82_gene", , drop = FALSE]
    data.frame(
      scope_id = row$scope_id, context_id = row$context_id,
      endpoint_id = row$endpoint_id, contrast_id = row$contrast_id,
      mt_omissions = nrow(mt), mt_same_direction = sum(mt$direction_retained),
      nuclear_omissions = nrow(nu), nuclear_same_direction = sum(nu$direction_retained),
      opposite_sesoi_effects = sum(x$opposite_sesoi_effect, na.rm = TRUE),
      nuclear_82_direction_retained = nrow(n82) == 1L && isTRUE(n82$direction_retained),
      influence_pass = nrow(mt) == 13L && sum(mt$direction_retained) >= 12L &&
        nrow(nu) == 5L && sum(nu$direction_retained) >= 4L &&
        !any(x$opposite_sesoi_effect, na.rm = TRUE) &&
        nrow(n82) == 1L && isTRUE(n82$direction_retained),
      stringsAsFactors = FALSE
    )
  }))
}

phase15_common_interval <- function(d, required_groups) {
  intervals <- lapply(required_groups, function(group) {
    central_interval(d$N[d$group_id == group])
  })
  low <- max(vapply(intervals, `[[`, numeric(1), 1L))
  high <- min(vapply(intervals, `[[`, numeric(1), 2L))
  if (!is.finite(low) || !is.finite(high) || high <= low) c(NA_real_, NA_real_) else
    c(low, high)
}

build_phase15_production_prediction_grid <- function(endpoint_data, phase13) {
  groups <- unlist(phase13$groups, use.names = FALSE)
  rows <- list()
  for (context_id in unique(endpoint_data$context_id)) {
    d <- endpoint_data[endpoint_data$context_id == context_id, , drop = FALSE]
    model <- fit_hc3(d$M, build_slope_design(d, groups))
    if (!model$success) next
    beta <- model$beta
    intercept <- setNames(beta[paste0("XI__", groups)], groups)
    slopes <- setNames(beta[paste0("XS__", groups)], groups)
    definitions <- c(
      list(list(scope_id = "general",
                contrast_id = "general_equal_stratum_AD_minus_NCI",
                required_groups = groups, coefficients = NULL)),
      lapply(phase13$contrasts, function(contrast) list(
        scope_id = "modifier", contrast_id = contrast$contrast_id,
        required_groups = unlist(contrast$required_groups),
        coefficients = unlist(contrast$coefficients)
      ))
    )
    for (definition in definitions) {
      interval <- phase15_common_interval(d, definition$required_groups)
      if (any(!is.finite(interval))) next
      grid <- seq(interval[[1L]], interval[[2L]], length.out = 41L)
      if (definition$scope_id == "general") {
        strata <- unique(sub("^(NCI|AD)__", "", groups))
        departure <- vapply(grid, function(value) mean(vapply(strata, function(s) {
          (intercept[[paste0("AD__", s)]] + slopes[[paste0("AD__", s)]] * value) -
            (intercept[[paste0("NCI__", s)]] + slopes[[paste0("NCI__", s)]] * value)
        }, numeric(1))), numeric(1))
      } else {
        co <- definition$coefficients
        departure <- vapply(grid, function(value) sum(as.numeric(co) *
          (intercept[names(co)] + slopes[names(co)] * value)), numeric(1))
      }
      target <- c(-1, 0, 1)
      inside <- target[target >= interval[[1L]] & target <= interval[[2L]]]
      substitution <- length(inside) < 2L
      checkpoints <- if (substitution) {
        stats::quantile(interval, c(0.25, 0.5, 0.75), names = FALSE, type = 7)
      } else inside
      checkpoint_index <- unique(vapply(checkpoints, function(value)
        which.min(abs(grid - value)), integer(1)))
      rows[[length(rows) + 1L]] <- data.frame(
        context_id = context_id, scope_id = definition$scope_id,
        contrast_id = definition$contrast_id, nuclear_score = grid,
        departure = departure, common_range_low = interval[[1L]],
        common_range_high = interval[[2L]],
        checkpoint = seq_along(grid) %in% checkpoint_index,
        checkpoint_substitution = substitution,
        slope_rewiring_observed = crossing_slope_flag(departure),
        stringsAsFactors = FALSE
      )
    }
  }
  bind_rows(rows)
}

build_quadratic_slope_design <- function(d, groups) {
  group <- factor(d$group_id, levels = groups)
  G <- stats::model.matrix(~ 0 + group)
  colnames(G) <- paste0("I__", groups)
  S <- G * d$N
  colnames(S) <- paste0("S__", groups)
  Q <- G * (d$N^2)
  colnames(Q) <- paste0("Q__", groups)
  cbind(G, S, Q, age_death_scaled = d$age_death_scaled,
        pmi_scaled = d$pmi_scaled, studyROS = as.numeric(d$study == "ROS"))
}

phase15_quadratic_vector <- function(row, phase13, coefficient_names) {
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  if (row$scope_id == "general") {
    groups <- unlist(phase13$groups, use.names = FALSE)
    strata <- unique(sub("^(NCI|AD)__", "", groups))
    for (stratum in strata) {
      vector[paste0("XQ__AD__", stratum)] <- 1 / length(strata)
      vector[paste0("XQ__NCI__", stratum)] <- -1 / length(strata)
    }
  } else {
    contrast <- phase13$contrasts[[which(vapply(
      phase13$contrasts, function(x) x$contrast_id == row$contrast_id,
      logical(1)
    ))]]
    co <- unlist(contrast$coefficients)
    vector[paste0("XQ__", names(co))] <- as.numeric(co)
  }
  vector
}

run_phase15_slope_sensitivities <- function(primary, phase13, prediction_grid) {
  groups <- unlist(phase13$groups, use.names = FALSE)
  primary_rows <- phase15_result_rows(primary)
  primary_rows <- primary_rows[primary_rows$endpoint_id == "coupling_slope_change", ]
  data <- primary$endpoint_bundle$data
  bind_rows(lapply(seq_len(nrow(primary_rows)), function(i) {
    row <- primary_rows[i, , drop = FALSE]
    d <- data[data$context_id == row$context_id, , drop = FALSE]
    required <- if (row$scope_id == "general") groups else {
      contrast <- phase13$contrasts[[which(vapply(
        phase13$contrasts, function(x) x$contrast_id == row$contrast_id,
        logical(1)
      ))]]
      unlist(contrast$required_groups)
    }
    interval <- phase15_common_interval(d, required)
    keep <- !d$group_id %in% required |
      (d$N >= interval[[1L]] & d$N <= interval[[2L]])
    trimmed <- d[keep, , drop = FALSE]
    trim_model <- if (all(is.finite(interval)))
      fit_hc3(trimmed$M, build_slope_design(trimmed, groups)) else
        list(success = FALSE, failure_reason = "no_common_predictor_range")
    trim_vector <- if (row$scope_id == "general") {
      general_vector(groups, names(trim_model$beta %||% numeric()), TRUE)
    } else {
      contrast <- phase13$contrasts[[which(vapply(
        phase13$contrasts, function(x) x$contrast_id == row$contrast_id,
        logical(1)
      ))]]
      modifier_vector(contrast, names(trim_model$beta %||% numeric()), TRUE)
    }
    trim_test <- linear_test(trim_model, trim_vector)
    quadratic_model <- fit_hc3(d$M, build_quadratic_slope_design(d, groups))
    quadratic_test <- linear_test(
      quadratic_model,
      phase15_quadratic_vector(row, phase13,
                               names(quadratic_model$beta %||% numeric()))
    )
    grid <- prediction_grid[
      prediction_grid$scope_id == row$scope_id &
        prediction_grid$context_id == row$context_id &
        prediction_grid$contrast_id == row$contrast_id, , drop = FALSE
    ]
    relative <- abs(trim_test$estimate) / pmax(abs(row$estimate), 1e-12)
    data.frame(
      scope_id = row$scope_id, context_id = row$context_id,
      endpoint_id = row$endpoint_id, contrast_id = row$contrast_id,
      primary_estimate = row$estimate, common_range_low = interval[[1L]],
      common_range_high = interval[[2L]], trimmed_donors = nrow(trimmed),
      common_range_estimate = trim_test$estimate,
      common_range_status = if (trim_test$success) "estimated" else trim_test$failure_reason,
      common_range_direction_retained = trim_test$success &&
        trim_test$estimate * row$estimate > 0,
      common_range_relative_magnitude = relative,
      quadratic_contrast_estimate = quadratic_test$estimate,
      quadratic_contrast_p_value = quadratic_test$p,
      quadratic_shape_flag = quadratic_test$success && quadratic_test$p <= 0.05 &&
        abs(quadratic_test$estimate) >= row$sesoi,
      slope_rewiring_observed = nrow(grid) && any(grid$slope_rewiring_observed),
      slope_sensitivity_pass = trim_test$success &&
        trim_test$estimate * row$estimate > 0 && is.finite(relative) && relative >= 0.5 &&
        !(quadratic_test$success && quadratic_test$p <= 0.05 &&
            abs(quadratic_test$estimate) >= row$sesoi) &&
        !(nrow(grid) && any(grid$slope_rewiring_observed)),
      stringsAsFactors = FALSE
    )
  }))
}

summarize_phase15_sensitivities <- function(primary, sensitivities, reliability,
                                            influence_summary, slope_summary, cfg) {
  rows <- phase15_result_rows(primary)
  required_static <- c("fifty_nucleus", "paired_PC1", "nuclear_only_TMM",
                       "severe_QC_exclusion", "robust_QC_covariate")
  bind_rows(lapply(seq_len(nrow(rows)), function(i) {
    row <- rows[i, , drop = FALSE]
    x <- sensitivities[
      sensitivities$scope_id == row$scope_id &
        sensitivities$context_id == row$context_id &
        sensitivities$endpoint_id == row$endpoint_id &
        sensitivities$contrast_id == row$contrast_id, , drop = FALSE
    ]
    static_pass <- vapply(required_static, function(type) {
      z <- x[x$sensitivity_type == type, , drop = FALSE]
      nrow(z) == 1L && z$model_status == "estimated" &&
        isTRUE(z$direction_retained) && is.finite(z$relative_magnitude) &&
        z$relative_magnitude >= if (type %in% c("fifty_nucleus", "paired_PC1")) 0.5 else 0
    }, logical(1))
    rel <- reliability[reliability$context_id == row$context_id &
                         reliability$module_id %in%
                           c("mtdna_oxphos_13", "nuclear_oxphos_structural_86"), ]
    pc1_reliability_pass <- nrow(rel) == 2L && all(as.logical(rel$pc1_reliable)) &&
      all(abs(rel$nci_mean_z_pc1_correlation) >= cfg$stability$pc1_minimum_correlation)
    reference_pass <- TRUE
    reference_direction_fraction <- NA_real_
    if (row$endpoint_id == "nci_reference_residual") {
      assignment <- x[x$sensitivity_type == "reference_fold_assignment", , drop = FALSE]
      assignment_ok <- assignment$model_status == "estimated" &
        is.finite(assignment$estimate)
      reference_direction_fraction <- if (any(assignment_ok))
        mean(assignment$direction_retained[assignment_ok]) else NA_real_
      full <- x[x$sensitivity_type == "full_nci_reference", , drop = FALSE]
      additive <- x[x$sensitivity_type == "additive_nci_reference", , drop = FALSE]
      reference_pass <- sum(assignment_ok) == cfg$production$reference_fold_assignments &&
        is.finite(reference_direction_fraction) &&
        reference_direction_fraction >= cfg$stability$minimum_direction_fraction &&
        nrow(full) == 1L && isTRUE(full$direction_retained) &&
        nrow(additive) == 1L && isTRUE(additive$direction_retained)
    }
    influence <- influence_summary[
      influence_summary$scope_id == row$scope_id &
        influence_summary$context_id == row$context_id &
        influence_summary$endpoint_id == row$endpoint_id &
        influence_summary$contrast_id == row$contrast_id, , drop = FALSE
    ]
    influence_pass <- nrow(influence) == 1L && isTRUE(influence$influence_pass)
    slope_pass <- TRUE
    if (row$endpoint_id == "coupling_slope_change") {
      slope <- slope_summary[
        slope_summary$scope_id == row$scope_id &
          slope_summary$context_id == row$context_id &
          slope_summary$contrast_id == row$contrast_id, , drop = FALSE
      ]
      slope_pass <- nrow(slope) == 1L && isTRUE(slope$slope_sensitivity_pass)
    }
    data.frame(
      scope_id = row$scope_id, context_id = row$context_id,
      endpoint_id = row$endpoint_id, contrast_id = row$contrast_id,
      fifty_nucleus_pass = static_pass[["fifty_nucleus"]],
      pc1_pass = static_pass[["paired_PC1"]] && pc1_reliability_pass,
      nuclear_only_normalization_pass = static_pass[["nuclear_only_TMM"]],
      severe_qc_pass = static_pass[["severe_QC_exclusion"]],
      robust_qc_covariate_pass = static_pass[["robust_QC_covariate"]],
      reference_direction_fraction = reference_direction_fraction,
      reference_sensitivity_pass = reference_pass,
      influence_pass = influence_pass, slope_sensitivity_pass = slope_pass,
      mandatory_sensitivity_pass = all(static_pass) && pc1_reliability_pass &&
        reference_pass && influence_pass && slope_pass,
      stringsAsFactors = FALSE
    )
  }))
}

finalize_phase15_endpoint_status <- function(results, stability_summary,
                                             sensitivity_summary) {
  key <- c("scope_id", "context_id", "endpoint_id", "contrast_id")
  out <- merge(results, stability_summary, by = key, all.x = TRUE, sort = FALSE)
  out <- merge(out, sensitivity_summary, by = key, all.x = TRUE, sort = FALSE)
  out$stability_status <- ifelse(
    as.logical(out$stability_pass), "passed",
    ifelse(startsWith(out$eligibility_status, "not_testable"), "not_applicable", "failed")
  )
  out$endpoint_status <- vapply(seq_len(nrow(out)), function(i) {
    numeric <- out$endpoint_status_numeric[[i]]
    if (numeric %in% c("supported", "provisional_low_power")) {
      if (isTRUE(out$stability_pass[[i]]) &&
          isTRUE(out$mandatory_sensitivity_pass[[i]])) numeric else "inconclusive"
    } else numeric
  }, character(1))
  out
}

phase15_gate_compatibility <- function(rows, prediction_grid) {
  carrier <- rows$endpoint_id[rows$endpoint_status %in%
                                c("supported", "provisional_low_power")]
  if (length(carrier) < 2L) return(FALSE)
  level <- intersect(carrier, c("standardized_difference", "nci_reference_residual"))
  if (length(level) == 2L) {
    estimates <- rows$estimate[match(level, rows$endpoint_id)]
    if (any(!is.finite(estimates)) || prod(estimates) <= 0) return(FALSE)
  }
  if ("coupling_slope_change" %in% carrier) {
    grid <- prediction_grid[
      prediction_grid$scope_id == rows$scope_id[[1L]] &
        prediction_grid$context_id == rows$context_id[[1L]] &
        prediction_grid$contrast_id == rows$contrast_id[[1L]], , drop = FALSE
    ]
    if (!nrow(grid) || any(grid$slope_rewiring_observed)) return(FALSE)
    checkpoints <- grid$departure[grid$checkpoint]
    compatible <- vapply(level, function(endpoint_id) {
      estimate <- rows$estimate[rows$endpoint_id == endpoint_id][[1L]]
      compatibility_pass(estimate, checkpoints)
    }, logical(1))
    if (!length(compatible) || !any(compatible)) return(FALSE)
  }
  TRUE
}

phase15_gate_row <- function(rows, prediction_grid) {
  statuses <- rows$endpoint_status
  carriers <- rows$endpoint_id[statuses %in% c("supported", "provisional_low_power")]
  supported <- rows$endpoint_id[statuses == "supported"]
  compatibility <- phase15_gate_compatibility(rows, prediction_grid)
  has_bridge_endpoint <- any(carriers %in%
    c("nci_reference_residual", "coupling_slope_change"))
  supported_rule <- length(supported) >= 2L &&
    any(supported %in% c("nci_reference_residual", "coupling_slope_change")) &&
    compatibility
  provisional_rule <- !supported_rule && length(carriers) >= 2L &&
    any(statuses == "provisional_low_power") && has_bridge_endpoint && compatibility
  gate_status <- if (all(statuses == "not_testable")) "not_testable" else
    if (supported_rule) "supported" else
      if (provisional_rule) "provisional_low_power" else
        if (any(statuses %in% c("supported", "provisional_low_power")))
          "partial_evidence" else
            if (all(statuses == "not_supported_precise_null"))
              "not_supported_precise_null" else "inconclusive"
  classification <- if (!gate_status %in% c("supported", "provisional_low_power"))
    "none" else if (all(c("standardized_difference", "nci_reference_residual",
                           "coupling_slope_change") %in% carriers))
      "imbalance_and_slope_change" else if ("coupling_slope_change" %in% carriers)
        "slope_change" else "relative_imbalance"
  residual <- rows[rows$endpoint_id == "nci_reference_residual", , drop = FALSE]
  bridge <- gate_status == "supported" && nrow(residual) == 1L &&
    residual$endpoint_status == "supported" &&
    isTRUE(residual$reference_sensitivity_pass)
  data.frame(
    context_id = rows$context_id[[1L]], context_role = rows$context_role[[1L]],
    scope_id = rows$scope_id[[1L]], contrast_id = rows$contrast_id[[1L]],
    supported_endpoints = paste(supported, collapse = "|"),
    carrier_endpoints = paste(carriers, collapse = "|"),
    compatibility_pass = compatibility,
    compatibility_classification = classification,
    slope_rewiring_observed = {
      grid <- prediction_grid[
        prediction_grid$scope_id == rows$scope_id[[1L]] &
          prediction_grid$context_id == rows$context_id[[1L]] &
          prediction_grid$contrast_id == rows$contrast_id[[1L]], , drop = FALSE]
      nrow(grid) > 0L && any(grid$slope_rewiring_observed)
    },
    bridge_authorized = bridge, gate_status = gate_status,
    permitted_wording = if (gate_status != "supported") "" else if (
      rows$scope_id[[1L]] == "general" && classification == "relative_imbalance"
    ) paste0("In ROSMAP donor-level ", rows$context_id[[1L]],
             " profiles, AD was associated with an altered relative balance between ",
             "mtDNA-encoded respiratory and nuclear-encoded OXPHOS structural-gene expression.")
    else if (rows$scope_id[[1L]] == "general") paste0(
      "In ROSMAP donor-level ", rows$context_id[[1L]],
      " profiles, AD was associated with an altered mtDNA-versus-nuclear OXPHOS expression slope."
    ) else paste0("In ROSMAP donor-level ", rows$context_id[[1L]],
                  " profiles, the AD-related mitonuclear expression relationship differed for ",
                  rows$contrast_id[[1L]], "."),
    stringsAsFactors = FALSE
  )
}

build_phase15_gates <- function(results, prediction_grid) {
  keys <- unique(results[c("scope_id", "context_id", "contrast_id")])
  gates <- bind_rows(lapply(seq_len(nrow(keys)), function(i) {
    key <- keys[i, , drop = FALSE]
    rows <- results[results$scope_id == key$scope_id &
                      results$context_id == key$context_id &
                      results$contrast_id == key$contrast_id, , drop = FALSE]
    phase15_gate_row(rows, prediction_grid)
  }))
  list(
    general = gates[gates$scope_id == "general", , drop = FALSE],
    modifier = gates[gates$scope_id == "modifier", , drop = FALSE]
  )
}

phase15_overall_decision <- function(gates) {
  general <- gates$general[gates$general$context_role == "primary_confirmatory", ]
  modifier <- gates$modifier[gates$modifier$context_role == "primary_confirmatory", ]
  all_primary <- bind_rows(list(general, modifier))
  if (any(general$gate_status == "supported") &&
      any(modifier$gate_status == "supported")) return("supported_general_and_modifier")
  if (any(general$gate_status == "supported")) return("supported_general_only")
  if (any(modifier$gate_status == "supported")) return("supported_modifier_only")
  if (any(all_primary$gate_status == "provisional_low_power")) return("provisional")
  if (all(all_primary$gate_status == "not_testable")) return("not_testable")
  eligible <- all_primary$gate_status != "not_testable"
  if (any(eligible) && all(all_primary$gate_status[eligible] ==
                           "not_supported_precise_null")) return("not_supported")
  "inconclusive"
}

run_phase15_production <- function(root, config, execution_cfg, cfg, phase13,
                                   phase_path, phase13_path, member_path) {
  started <- Sys.time()
  phase15_production_authorized(cfg)
  required_packages <- c("edgeR", "Matrix")
  missing_packages <- required_packages[!vapply(
    required_packages, requireNamespace, logical(1), quietly = TRUE
  )]
  if (length(missing_packages)) {
    stop("Missing Phase 15 production packages: ",
         paste(missing_packages, collapse = ", "), call. = FALSE)
  }
  stage_root <- absolute_path(config$outputs$root, root)
  phase13_dir <- file.path(stage_root, cfg$paths$phase13_relative)
  final_dir <- file.path(stage_root, cfg$paths$output_relative)
  if (dir.exists(final_dir)) {
    stop("Phase 15 output already exists and will not be overwritten: ", final_dir,
         call. = FALSE)
  }
  upstream <- validate_phase13_production_bundle(phase13_dir, cfg)
  contexts <- production_context_manifest(phase13, cfg)
  endpoints <- endpoint_manifest_from_config(cfg)
  contrasts <- contrast_manifest_from_phase13(phase13)
  modules <- module_manifest_from_phase13(phase13)
  upstream_members <- phase15_drop_schema(phase15_read_table(
    file.path(phase13_dir, "respiratory_module_members.tsv")
  ))
  members <- upstream_members[upstream_members$module_id %in% modules$module_id, ,
                              drop = FALSE]
  if (nrow(members) != 99L || anyDuplicated(members[c("module_id", "frozen_gene_symbol")])) {
    stop("Frozen Phase 15 direct-respiratory membership is not exactly 13+86 genes",
         call. = FALSE)
  }
  local_members <- phase15_drop_schema(phase15_read_table(member_path))
  local_members <- local_members[local_members$module_id %in% modules$module_id, ,
                                 drop = FALSE]
  member_key <- c("module_id", "frozen_gene_symbol", "assay_feature_identifier")
  if (!identical(
      members[order(members$module_id, members$frozen_gene_symbol), member_key],
      local_members[order(local_members$module_id, local_members$frozen_gene_symbol), member_key]
  )) {
    stop("Local and validated Phase 13 direct-respiratory memberships differ",
         call. = FALSE)
  }
  members$c3_admitted <- TRUE
  members$c3_role <- ifelse(members$module_id == "mtdna_oxphos_13",
                            "mtDNA", "nuclear")
  scores <- load_phase13_production_scores(phase13_dir, contexts)
  reconstruction_error <- reconstruct_phase13_score_error(phase13_dir, scores)
  if (!is.finite(reconstruction_error) || reconstruction_error > 1e-8) {
    stop("Phase 13 stored-score reconstruction exceeded tolerance: ",
         signif(reconstruction_error, 6), call. = FALSE)
  }
  inputs <- load_phase15_resampling_inputs(phase13_dir, contexts, phase13)
  helper_path <- file.path(root, "scripts/15_run_mitonuclear_coupling_production.R")
  fingerprint <- digest::digest(paste(
    sha256_file(phase_path), sha256_file(phase13_path), sha256_file(member_path),
    sha256_file(file.path(root, "scripts/15_run_mitonuclear_coupling.R")),
    sha256_file(helper_path), upstream$status$artifact_manifest_sha256[[1L]], sep = "|"
  ), algo = "sha256", serialize = FALSE)

  cat("Phase 15 production: fitting seven-context primary endpoint models\n")
  primary <- analyze_scores(scores, cfg, phase13, contexts, endpoints, fingerprint,
                            production = TRUE)
  prediction_grid <- build_phase15_production_prediction_grid(
    primary$endpoint_bundle$data, phase13
  )
  primary_rows <- phase15_result_rows(primary)
  if (nrow(primary$results$general) != cfg$production$output_dimensions$general_rows ||
      nrow(primary$results$modifier) != cfg$production$output_dimensions$modifier_rows ||
      nrow(primary$results$strata) != cfg$production$output_dimensions$stratum_rows) {
    stop("Primary Phase 15 dimensions do not match the frozen production contract",
         call. = FALSE)
  }
  worker_plan <- phase15_worker_plan(execution_cfg$execution)
  stability <- run_phase15_production_stability(
    scores, inputs, cfg, phase13, contexts, endpoints, fingerprint,
    worker_plan$effective
  )
  loo_planned <- attr(stability, "loo_planned") %||%
    length(unique(scores$original_projid))
  stability_summary <- summarize_phase15_production_stability(
    primary_rows, stability, cfg, loo_planned
  )
  general_stability <- stability_summary[stability_summary$scope_id == "general", ,
                                         drop = FALSE]
  modifier_stability <- stability_summary[stability_summary$scope_id == "modifier", ,
                                          drop = FALSE]

  cat("Phase 15 production: running fixed score, reference, QC, and influence sensitivities\n")
  sensitivities <- run_phase15_production_sensitivities(
    scores, inputs, primary, cfg, phase13, contexts, endpoints, fingerprint
  )
  influence <- run_phase15_gene_complex_influence(
    scores, inputs, cfg, phase13, contexts, endpoints, fingerprint
  )
  influence_summary <- summarize_phase15_influence_pass(primary_rows, influence)
  slope_summary <- run_phase15_slope_sensitivities(primary, phase13, prediction_grid)
  sensitivity_summary <- summarize_phase15_sensitivities(
    primary, sensitivities, phase15_drop_schema(phase15_read_table(
      file.path(phase13_dir, "respiratory_module_reliability.tsv")
    )), influence_summary, slope_summary, cfg
  )
  finalized <- finalize_phase15_endpoint_status(
    primary_rows, stability_summary, sensitivity_summary
  )
  general <- finalized[finalized$scope_id == "general", , drop = FALSE]
  modifier <- finalized[finalized$scope_id == "modifier", , drop = FALSE]
  gates <- build_phase15_gates(finalized, prediction_grid)
  if (nrow(gates$general) != cfg$production$output_dimensions$general_gates ||
      nrow(gates$modifier) != cfg$production$output_dimensions$modifier_gates) {
    stop("Phase 15 gate dimensions do not match the frozen production contract",
         call. = FALSE)
  }
  scientific_decision <- phase15_overall_decision(gates)

  donor_eligibility <- bind_rows(lapply(contexts$context_id, function(context_id) {
    d <- scores[scores$context_id == context_id, , drop = FALSE]
    bind_rows(lapply(unlist(phase13$groups), function(group) {
      x <- d[d$group_id == group, , drop = FALSE]
      data.frame(
        context_id = context_id, group_id = group, donors = nrow(x),
        minimum_nuclei = if (nrow(x)) min(x$nuclei) else NA_integer_,
        eligible_20 = sum(x$nuclei >= 20L), eligible_50 = sum(x$nuclei >= 50L),
        mtdna_coverage_pass = all(is.finite(x$M)),
        nuclear_coverage_pass = all(is.finite(x$N)),
        nuclear_variance = if (nrow(x) > 1L) stats::var(x$N) else NA_real_,
        nuclear_distinct_values = length(unique(x$N)), stringsAsFactors = FALSE
      )
    }))
  }))
  reliability <- phase15_drop_schema(phase15_read_table(
    file.path(phase13_dir, "respiratory_module_reliability.tsv")
  ))
  reliability <- reliability[reliability$module_id %in% modules$module_id, , drop = FALSE]
  reliability$stored_score_reconstruction_max_abs_error <- reconstruction_error
  reliability$mtdna_genes <- 13L
  reliability$nuclear_genes <- 86L

  required_inputs <- c(
    phase_path, phase13_path, member_path, helper_path,
    file.path(phase13_dir, upstream$required_files)
  )
  input_inventory <- data.frame(
    input_id = c("phase15_config", "phase13_config", "local_module_members",
                 "phase15_production_implementation",
                 paste0("phase13_", sub("[.](tsv([.]gz)?|rds)$", "",
                                       upstream$required_files))),
    path = required_inputs, exists = file.exists(required_inputs),
    bytes = file.info(required_inputs)$size,
    sha256 = vapply(required_inputs, sha256_file, character(1)),
    usage = c("frozen_phase15_design", "inherited_definitions",
              "local_membership_identity", "production_implementation",
              rep("validated_phase13_input", length(upstream$required_files))),
    stringsAsFactors = FALSE
  )
  source_checks <- data.frame(
    check_id = c(
      "phase13_validated_complete", "phase13_artifact_hashes", "seven_contexts",
      "selected_module_count", "selected_membership_count", "score_keys_unique",
      "score_pairs_same_donor_context", "stored_scores_reconstruct",
      "primary_secondary_roles", "no_pilot_fixture", "production_approval"
    ),
    passed = c(
      upstream$status$validation_status[[1L]] == "validated_complete", TRUE,
      nrow(contexts) == 7L, nrow(modules) == 2L, nrow(members) == 99L,
      !anyDuplicated(scores$donor_context_id),
      all(is.finite(scores$M) & is.finite(scores$N)),
      reconstruction_error <= 1e-8,
      sum(contexts$context_role == "primary_confirmatory") == 3L &&
        sum(contexts$context_role == "secondary_extension") == 4L,
      !any(contexts$pilot_fixture_context), isTRUE(cfg$analysis$production_approved)
    ),
    blocking = TRUE,
    observed = c(
      upstream$status$validation_status[[1L]], "validated", nrow(contexts),
      nrow(modules), nrow(members), anyDuplicated(scores$donor_context_id),
      "paired", signif(reconstruction_error, 8),
      paste(table(contexts$context_role), collapse = "|"), "absent",
      cfg$analysis$production_approved
    ),
    expected = c("validated_complete", "validated", 7, 2, 99, 0, "paired",
                 "<=1e-8", "3 primary|4 secondary", "absent", TRUE),
    detail = "", stringsAsFactors = FALSE
  )
  expected_stability_rows <-
    cfg$production$bootstrap_repetitions * nrow(primary_rows) +
    loo_planned * nrow(primary_rows) +
    cfg$production$balance_repetitions * nrow(primary_rows)
  checks <- bind_rows(list(source_checks, data.frame(
    check_id = c(
      "endpoint_dimensions", "gate_dimensions", "stability_rows_complete",
      "stability_units_whole_donor", "crossfit_no_leakage",
      "reference_assignments_complete", "influence_rows_complete",
      "all_endpoint_statuses_terminal", "all_gate_statuses_terminal",
      "declared_output_count"
    ),
    passed = c(
      nrow(general) == 21L && nrow(modifier) == 147L &&
        nrow(primary$results$strata) == 126L,
      nrow(gates$general) == 7L && nrow(gates$modifier) == 49L,
      nrow(stability) == expected_stability_rows,
      all(stability$donor_resampling_unit == "whole_donor"),
      validate_crossfit_leakage(primary$endpoint_bundle$folds),
      sum(sensitivities$sensitivity_type == "reference_fold_assignment") ==
        cfg$production$reference_fold_assignments * 56L,
      nrow(influence_summary) == nrow(primary_rows),
      all(finalized$endpoint_status %in% c(
        "supported", "provisional_low_power", "statistically_detectable_but_small",
        "not_supported_precise_null", "inconclusive", "not_testable"
      )),
      all(c(gates$general$gate_status, gates$modifier$gate_status) %in% c(
        "supported", "provisional_low_power", "partial_evidence",
        "not_supported_precise_null", "inconclusive", "not_testable"
      )),
      length(unlist(cfg$outputs$declared_files)) == 36L
    ),
    blocking = TRUE, observed = "production_observed", expected = "pass",
    detail = "", stringsAsFactors = FALSE
  )))
  if (any(checks$blocking & !checks$passed)) {
    stop("Blocking Phase 15 production checks failed: ",
         paste(checks$check_id[checks$blocking & !checks$passed], collapse = ", "),
         call. = FALSE)
  }

  analysis_manifest <- data.frame(
    analysis_id = cfg$analysis$analysis_id, title = cfg$analysis$title,
    definitions_approved = cfg$analysis$definitions_approved,
    definitions_frozen = cfg$analysis$definitions_frozen,
    approval_basis = cfg$analysis$approval_basis,
    production_approved = cfg$analysis$production_approved,
    execution_scope = "minerva_production", fixture_id = "",
    contexts = nrow(contexts), primary_contexts = 3L, secondary_contexts = 4L,
    endpoints = nrow(endpoints), modules = nrow(modules), memberships = nrow(members),
    modifier_contrasts = length(phase13$contrasts),
    bootstrap_repetitions = cfg$production$bootstrap_repetitions,
    balance_repetitions = cfg$production$balance_repetitions,
    reference_fold_assignments = cfg$production$reference_fold_assignments,
    analysis_fingerprint = fingerprint,
    phase15_config_sha256 = sha256_file(phase_path),
    phase13_artifact_manifest_sha256 = upstream$status$artifact_manifest_sha256[[1L]],
    production_implementation_sha256 = sha256_file(helper_path),
    stringsAsFactors = FALSE
  )
  general_manifest <- general[c("context_id", "context_role", "endpoint_id",
                                 "contrast_id", "family_id", "eligibility_status")]
  general_manifest$test_order <- seq_len(nrow(general_manifest))
  modifier_manifest <- modifier[c("context_id", "context_role", "endpoint_id",
                                   "contrast_id", "family_id", "donor_counts",
                                   "eligibility_status")]
  modifier_manifest$test_order <- seq_len(nrow(modifier_manifest))
  claim_summary <- data.frame(
    claim_scope = c("primary_overall", "general_C3", "modifier_C3",
                    "secondary_extension", "residual_bridge", "phase13_C1_context"),
    scientific_decision = c(
      scientific_decision,
      if (any(gates$general$gate_status == "supported" &
              gates$general$context_role == "primary_confirmatory")) "supported" else
        "not_supported_or_inconclusive",
      if (any(gates$modifier$gate_status == "supported" &
              gates$modifier$context_role == "primary_confirmatory")) "supported" else
        "not_supported_or_inconclusive",
      if (any(c(gates$general$gate_status[gates$general$context_role == "secondary_extension"],
                gates$modifier$gate_status[gates$modifier$context_role ==
                                             "secondary_extension"]) == "supported"))
        "secondary_context_support_only" else "no_secondary_support",
      if (any(c(gates$general$bridge_authorized, gates$modifier$bridge_authorized)))
        "authorized" else "not_authorized",
      upstream$status$scientific_decision[[1L]] %||% "inconclusive"
    ),
    bridge_authorized = c(FALSE, FALSE, FALSE, FALSE,
                          any(c(gates$general$bridge_authorized,
                                gates$modifier$bridge_authorized)), FALSE),
    conclusion = c(
      scientific_decision,
      paste(gates$general$permitted_wording[nzchar(gates$general$permitted_wording)],
            collapse = " "),
      paste(gates$modifier$permitted_wording[nzchar(gates$modifier$permitted_wording)],
            collapse = " "),
      "Secondary contexts are reported separately and do not alter the primary decision.",
      "Residual bridge authorization follows exact supported gates only.",
      "Phase 13 C1 is contextual provenance and does not gate Phase 15 C3."
    ), stringsAsFactors = FALSE
  )
  figure_data <- bind_rows(list(
    data.frame(
      figure_record_type = "donor_point",
      context_id = primary$endpoint_bundle$data$context_id,
      scope_id = "donor", endpoint_id = "score_pair", contrast_id = NA_character_,
      projid = primary$endpoint_bundle$data$projid,
      nuclear_score = primary$endpoint_bundle$data$N,
      value = primary$endpoint_bundle$data$M,
      diagnosis = primary$endpoint_bundle$data$diagnosis,
      group_id = primary$endpoint_bundle$data$group_id
    ),
    data.frame(
      figure_record_type = "prediction_grid", context_id = prediction_grid$context_id,
      scope_id = prediction_grid$scope_id, endpoint_id = "coupling_slope_change",
      contrast_id = prediction_grid$contrast_id, projid = NA_character_,
      nuclear_score = prediction_grid$nuclear_score, value = prediction_grid$departure,
      diagnosis = NA_character_, group_id = NA_character_
    )
  ))
  stage_status <- data.frame(
    stage_order = 1:7,
    stage_id = c("definitions", "phase13_inputs", "score_pairs", "crossfit_models",
                 "stability_sensitivities", "gates", "publication"),
    dependency = c("none", "definitions", "phase13_inputs", "score_pairs",
                   "crossfit_models", "stability_sensitivities", "checks"),
    terminal_status = c(rep("complete", 6L), "ready"),
    records = c(1L, length(upstream$required_files), nrow(scores),
                nrow(primary$results$diagnostics), nrow(stability) + nrow(sensitivities),
                nrow(gates$general) + nrow(gates$modifier), 36L),
    started_utc = format(started, tz = "UTC"),
    completed_utc = format(Sys.time(), tz = "UTC"), stringsAsFactors = FALSE
  )
  donor_endpoints <- primary$endpoint_bundle$data[c(
    "projid", "original_projid", "context_id", "group_id", "diagnosis", "sex",
    "apoe_group", "sex_APOE_stratum", "M", "N", "standardized_difference",
    "residual_raw", "nci_reference_residual", "reference_status"
  )]
  sensitivity_output <- bind_rows(list(sensitivities, transform(
    slope_summary, sensitivity_type = "slope_common_range_and_quadratic"
  )))
  tables <- list(
    mitonuclear_analysis_manifest.tsv = list(analysis_manifest, "phase15_analysis_manifest_v1"),
    mitonuclear_context_manifest.tsv = list(contexts, "phase15_context_manifest_v1"),
    mitonuclear_endpoint_manifest.tsv = list(endpoints, "phase15_endpoint_manifest_v1"),
    mitonuclear_contrast_manifest.tsv = list(contrasts, "phase15_contrast_manifest_v1"),
    mitonuclear_module_manifest.tsv = list(modules, "phase15_module_manifest_v1"),
    mitonuclear_module_members.tsv = list(members, "phase15_module_members_v1"),
    mitonuclear_input_inventory.tsv = list(input_inventory, "phase15_input_inventory_v1"),
    mitonuclear_source_checks.tsv = list(source_checks, "phase15_source_checks_v1"),
    mitonuclear_donor_eligibility.tsv = list(donor_eligibility, "phase15_donor_eligibility_v1"),
    mitonuclear_score_pairs.tsv.gz = list(scores, "phase15_score_pairs_v1"),
    mitonuclear_crossfit_folds.tsv = list(primary$endpoint_bundle$folds, "phase15_crossfit_folds_v1"),
    mitonuclear_nci_reference_models.tsv = list(primary$endpoint_bundle$models, "phase15_reference_models_v1"),
    mitonuclear_reference_predictions.tsv.gz = list(primary$endpoint_bundle$predictions, "phase15_reference_predictions_v1"),
    mitonuclear_donor_endpoints.tsv.gz = list(donor_endpoints, "phase15_donor_endpoints_v1"),
    mitonuclear_general_test_manifest.tsv = list(general_manifest, "phase15_general_manifest_v1"),
    mitonuclear_modifier_test_manifest.tsv = list(modifier_manifest, "phase15_modifier_manifest_v1"),
    mitonuclear_general_results.tsv = list(general, "phase15_general_results_v1"),
    mitonuclear_modifier_results.tsv = list(modifier, "phase15_modifier_results_v1"),
    mitonuclear_stratum_effects.tsv = list(primary$results$strata, "phase15_stratum_effects_v1"),
    mitonuclear_group_slopes.tsv = list(primary$results$group_slopes, "phase15_group_slopes_v1"),
    mitonuclear_prediction_grid.tsv.gz = list(prediction_grid, "phase15_prediction_grid_v1"),
    mitonuclear_model_diagnostics.tsv = list(primary$results$diagnostics, "phase15_model_diagnostics_v1"),
    mitonuclear_score_reliability.tsv = list(reliability, "phase15_score_reliability_v1"),
    mitonuclear_stability_replicates.tsv.gz = list(stability, "phase15_stability_replicates_v1"),
    mitonuclear_general_stability_summary.tsv = list(general_stability, "phase15_general_stability_v1"),
    mitonuclear_modifier_stability_summary.tsv = list(modifier_stability, "phase15_modifier_stability_v1"),
    mitonuclear_gene_complex_influence.tsv = list(influence, "phase15_gene_complex_influence_v1"),
    mitonuclear_qc_normalization_sensitivity.tsv = list(sensitivity_output, "phase15_qc_normalization_v1"),
    mitonuclear_general_gate_decisions.tsv = list(gates$general, "phase15_general_gates_v1"),
    mitonuclear_modifier_gate_decisions.tsv = list(gates$modifier, "phase15_modifier_gates_v1"),
    mitonuclear_claim_summary.tsv = list(claim_summary, "phase15_claim_summary_v1"),
    mitonuclear_figure_data.tsv.gz = list(figure_data, "phase15_figure_data_v1"),
    mitonuclear_stage_status.tsv = list(stage_status, "phase15_stage_status_v1"),
    mitonuclear_checks.tsv = list(checks, "phase15_checks_v1")
  )

  staging <- file.path(stage_root, paste0(".phase15_staging_", Sys.getpid()))
  dir.create(staging, recursive = TRUE, showWarnings = FALSE)
  published <- FALSE
  on.exit(if (!published && dir.exists(staging)) unlink(staging, recursive = TRUE), add = TRUE)
  for (name in names(tables)) atomic_write_tsv(
    phase15_drop_schema(tables[[name]][[1L]]), file.path(staging, name),
    tables[[name]][[2L]]
  )
  declared <- unlist(cfg$outputs$declared_files)
  artifact_files <- setdiff(declared, c("mitonuclear_artifacts.tsv", "mitonuclear_status.tsv"))
  artifacts <- bind_rows(lapply(artifact_files, function(name) {
    path <- file.path(staging, name)
    data.frame(
      artifact_file = name,
      artifact_role = if (grepl("manifest|checks|status", name)) "control" else "scientific",
      path = file.path(config$outputs$root, cfg$paths$output_relative, name),
      records = count_records(path), bytes = file.info(path)$size,
      sha256 = sha256_file(path), validation_status = "validated_complete",
      stringsAsFactors = FALSE
    )
  }))
  atomic_write_tsv(artifacts, file.path(staging, "mitonuclear_artifacts.tsv"),
                   "phase15_artifacts_v1")
  status <- data.frame(
    execution_stage = execution_cfg$execution$execution_stage,
    execution_phase = execution_cfg$execution$execution_phase,
    backend = execution_cfg$execution$backend, run_id = execution_cfg$execution$run_id,
    stable_task_id = "global:mitonuclear_coupling", task_mode = "mitonuclear_coupling",
    output_schema = cfg$analysis$output_schema, fixture_id = "", contexts = 7L,
    primary_contexts = 3L, secondary_contexts = 4L, modules = 2L,
    module_memberships = 99L, endpoints = 3L, modifier_contrasts = 7L,
    general_result_rows = nrow(general), modifier_result_rows = nrow(modifier),
    stratum_rows = nrow(primary$results$strata), general_gate_rows = nrow(gates$general),
    modifier_gate_rows = nrow(gates$modifier), crossfit_leakage_detected = FALSE,
    stability_workers_requested = worker_plan$requested,
    stability_workers_effective = worker_plan$effective,
    stability_backend = worker_plan$backend, analysis_fingerprint = fingerprint,
    failed_checks = "",
    artifact_manifest_sha256 = sha256_file(file.path(staging, "mitonuclear_artifacts.tsv")),
    scientific_decision = scientific_decision,
    validation_status = cfg$production$terminal_validation_status,
    pilot_results_are_scientific_evidence = FALSE,
    production_analysis = TRUE, git_revision = git_revision(root),
    timestamp_utc = format(Sys.time(), tz = "UTC"), stringsAsFactors = FALSE
  )
  atomic_write_tsv(status, file.path(staging, "mitonuclear_status.tsv"),
                   "phase15_status_v1")
  validate_phase15_output(
    staging, 7L, 21L, 147L, 126L, 7L, 49L,
    cfg$production$terminal_validation_status, declared
  )
  dir.create(dirname(final_dir), recursive = TRUE, showWarnings = FALSE)
  if (!file.rename(staging, final_dir)) {
    stop("Could not atomically publish Phase 15 production output", call. = FALSE)
  }
  published <- TRUE
  cat("Phase 15 production published: ", final_dir, "\n", sep = "")
  cat("Technical status: ", cfg$production$terminal_validation_status, "\n", sep = "")
  cat("Scientific decision: ", scientific_decision, "\n", sep = "")
  invisible(TRUE)
}
