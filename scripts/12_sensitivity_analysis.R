#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL, mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode", "--mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/12_sensitivity_analysis.R --config FILE ",
        "[--execution-config FILE] [--task-mode sensitivity | --mode sensitivity]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  selected_mode <- out$task_mode %||% out$mode %||% "sensitivity"
  if (!identical(selected_mode, "sensitivity")) {
    stop("Phase 12 mode must be 'sensitivity'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_tsv <- function(x, path, gzip = FALSE) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid(), if (gzip) ".gz" else "")
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA",
    compress = if (gzip) "gzip" else "none"
  )
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

sha256_lines <- function(values) {
  path <- tempfile("phase12_inputs_", fileext = ".txt")
  on.exit(unlink(path), add = TRUE)
  writeLines(sort(unique(as.character(values))), path, useBytes = TRUE)
  sha256_file(path)
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(gsub("[^0-9.]", "", line[[1L]])) / (1024^2)
}

git_revision <- function(root) {
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

as_logical <- function(x) {
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

normalize_projid <- function(x) {
  sprintf("%08d", as.integer(gsub("[^0-9]", "", as.character(x))))
}

read_validated_statuses <- function(paths, expected_schema) {
  if (!length(paths) || any(!file.exists(paths))) {
    stop("Required status file is missing for schema ", expected_schema, call. = FALSE)
  }
  values <- lapply(paths, function(path) {
    value <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
    if (nrow(value) != 1L || !identical(value$schema_version[[1L]], expected_schema) ||
        !identical(value$validation_status[[1L]], "validated_complete")) {
      stop("Required status is not validated_complete: ", path, call. = FALSE)
    }
    value
  })
  invisible(do.call(rbind, values))
}

read_many <- function(paths) {
  if (!length(paths)) stop("No required result files were found", call. = FALSE)
  data.table::rbindlist(lapply(paths, data.table::fread), fill = TRUE, use.names = TRUE)
}

parse_terms <- function(value) {
  pieces <- strsplit(value, ";", fixed = TRUE)[[1L]]
  pairs <- strsplit(pieces, "=", fixed = TRUE)
  groups <- vapply(pairs, `[[`, character(1), 1L)
  weights <- as.numeric(vapply(pairs, `[[`, character(1), 2L))
  setNames(weights, groups)
}

split_groups <- function(value) {
  if (is.na(value) || !nzchar(value)) character() else strsplit(value, ";", fixed = TRUE)[[1L]]
}

make_single_contrast <- function(terms, design_columns) {
  if (!all(names(terms) %in% design_columns)) {
    stop("Required design groups are absent: ", paste(setdiff(names(terms), design_columns), collapse = ", "))
  }
  contrast <- setNames(numeric(length(design_columns)), design_columns)
  contrast[names(terms)] <- terms
  contrast
}

make_global_contrasts <- function(design_columns) {
  strata <- as.vector(outer(c("Female", "Male"), c("e2", "e33", "e4"), paste, sep = "__"))
  reference <- "Female__e33"
  comparisons <- setdiff(strata, reference)
  matrix <- matrix(0, nrow = length(design_columns), ncol = length(comparisons))
  effect_vector <- function(stratum) {
    pieces <- strsplit(stratum, "__", fixed = TRUE)[[1L]]
    terms <- c(1, -1)
    names(terms) <- c(
      paste("AD", pieces[[1L]], pieces[[2L]], sep = "__"),
      paste("NCI", pieces[[1L]], pieces[[2L]], sep = "__")
    )
    make_single_contrast(terms, design_columns)
  }
  reference_vector <- effect_vector(reference)
  for (i in seq_along(comparisons)) {
    matrix[, i] <- effect_vector(comparisons[[i]]) - reference_vector
  }
  matrix
}

fit_fraction_design <- function(metadata, covariates) {
  metadata$group <- factor(metadata$group_label)
  formula <- stats::as.formula(
    paste("~ 0 + group", paste(covariates, collapse = " + "), sep = " + ")
  )
  design <- stats::model.matrix(formula, data = metadata)
  colnames(design)[seq_len(nlevels(metadata$group))] <- levels(metadata$group)
  if (qr(design)$rank < ncol(design)) return(list(error = "rank-deficient design"))
  response <- cbind(
    mitochondrial = metadata$total_mt_count,
    non_mitochondrial = metadata$total_umi_count - metadata$total_mt_count
  )
  error <- NULL
  fit <- tryCatch(
    stats::glm.fit(x = design, y = response, family = stats::quasibinomial()),
    error = function(e) {
      error <<- conditionMessage(e)
      NULL
    }
  )
  if (is.null(fit)) return(list(error = error))
  class(fit) <- c("glm", "lm")
  list(fit = fit, design = design, covariance = stats::vcov(fit), error = "")
}

test_fraction_contrast <- function(model, row) {
  fit <- model$fit
  if (identical(as.character(row$contrast_kind), "single_df")) {
    contrast <- make_single_contrast(parse_terms(row$contrast_terms), colnames(model$design))
    estimate <- sum(contrast * stats::coef(fit))
    standard_error <- sqrt(as.numeric(t(contrast) %*% model$covariance %*% contrast))
    statistic <- estimate / standard_error
    p_value <- 2 * stats::pt(abs(statistic), df = fit$df.residual, lower.tail = FALSE)
    critical <- stats::qt(0.975, df = fit$df.residual)
    list(
      effect_size = estimate, ci95_low = estimate - critical * standard_error,
      ci95_high = estimate + critical * standard_error, p_value = p_value
    )
  } else {
    contrast <- make_global_contrasts(colnames(model$design))
    estimates <- as.numeric(t(contrast) %*% stats::coef(fit))
    covariance <- t(contrast) %*% model$covariance %*% contrast
    numerator_df <- qr(covariance)$rank
    statistic <- as.numeric(t(estimates) %*% qr.solve(covariance, estimates) / numerator_df)
    list(
      effect_size = max(abs(estimates)), ci95_low = NA_real_, ci95_high = NA_real_,
      p_value = stats::pf(statistic, df1 = numerator_df, df2 = fit$df.residual, lower.tail = FALSE)
    )
  }
}

fit_fraction_variant <- function(samples, manifest, eligibility_field, covariates, variant_id, minimum_donors) {
  result_list <- list()
  diagnostic_list <- list()
  for (rds_id in sort(unique(manifest$rds_id))) {
    rds_manifest <- manifest[manifest$rds_id == rds_id, , drop = FALSE]
    for (cell_type in sort(unique(rds_manifest$cell_type_high_resolution))) {
      rows <- rds_manifest[rds_manifest$cell_type_high_resolution == cell_type, , drop = FALSE]
      metadata <- samples[
        samples$rds_id == rds_id & samples$cell_type_high_resolution == cell_type &
          as_logical(samples[[eligibility_field]]), , drop = FALSE
      ]
      group_counts <- table(metadata$group_label)
      dynamically_eligible <- vapply(seq_len(nrow(rows)), function(i) {
        required <- split_groups(rows$required_groups[[i]])
        counts <- as.numeric(group_counts[required])
        length(required) > 0L && all(is.finite(counts) & counts >= minimum_donors)
      }, logical(1))
      rows <- rows[dynamically_eligible, , drop = FALSE]
      if (!nrow(rows)) {
        diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
          schema_version = "sensitivity_model_diagnostics_v1",
          sensitivity_id = variant_id, rds_id = rds_id,
          cell_type_high_resolution = cell_type, samples = nrow(metadata),
          eligible_contrasts = 0L, completed_contrasts = 0L,
          terminal_status = "not_estimable",
          message = "no contrast retained at sensitivity eligibility threshold",
          stringsAsFactors = FALSE
        )
        next
      }
      model <- fit_fraction_design(metadata, covariates)
      if (nzchar(model$error)) {
        diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
          schema_version = "sensitivity_model_diagnostics_v1",
          sensitivity_id = variant_id, rds_id = rds_id,
          cell_type_high_resolution = cell_type, samples = nrow(metadata),
          eligible_contrasts = nrow(rows), completed_contrasts = 0L,
          terminal_status = "failed", message = model$error,
          stringsAsFactors = FALSE
        )
        next
      }
      completed <- 0L
      for (i in seq_len(nrow(rows))) {
        row <- rows[i, , drop = FALSE]
        test <- tryCatch(test_fraction_contrast(model, row), error = function(e) NULL)
        if (is.null(test)) next
        completed <- completed + 1L
        result_list[[length(result_list) + 1L]] <- data.frame(
          sensitivity_id = variant_id, rds_id = rds_id,
          cell_type_high_resolution = cell_type,
          contrast_id = row$contrast_id, contrast_name = row$contrast_name,
          effect_size = test$effect_size, ci95_low = test$ci95_low,
          ci95_high = test$ci95_high, p_value = test$p_value, fdr = NA_real_,
          model_samples = nrow(metadata), covariates = paste(covariates, collapse = ";"),
          stringsAsFactors = FALSE
        )
      }
      diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
        schema_version = "sensitivity_model_diagnostics_v1",
        sensitivity_id = variant_id, rds_id = rds_id,
        cell_type_high_resolution = cell_type, samples = nrow(metadata),
        eligible_contrasts = nrow(rows), completed_contrasts = completed,
        terminal_status = if (completed == nrow(rows)) "validated_complete" else "failed",
        message = if (completed == nrow(rows)) "" else "one or more contrasts failed",
        stringsAsFactors = FALSE
      )
    }
  }
  results <- if (length(result_list)) data.table::rbindlist(result_list, fill = TRUE) else data.table::data.table()
  if (nrow(results)) results[, fdr := stats::p.adjust(p_value, method = "BH")]
  diagnostics <- if (length(diagnostic_list)) data.table::rbindlist(diagnostic_list, fill = TRUE) else data.table::data.table()
  list(results = results, diagnostics = diagnostics)
}

make_standard_result <- function(
    sensitivity_id, method_branch, rds_id, cell_type, contrast_id,
    contrast_name, entity_type, entity, primary_effect, sensitivity_effect,
    primary_ci_low, primary_ci_high, sensitivity_ci_low, sensitivity_ci_high,
    primary_fdr, sensitivity_fdr, repetitions_planned = 0L,
    repetitions_completed = 0L, terminal_status = "validated_complete", message = "") {
  data.table::data.table(
    schema_version = "sensitivity_results_v1",
    sensitivity_id = sensitivity_id, method_branch = method_branch,
    rds_id = rds_id, cell_type_high_resolution = cell_type,
    contrast_id = contrast_id, contrast_name = contrast_name,
    entity_type = entity_type, entity = entity,
    primary_effect = primary_effect, sensitivity_effect = sensitivity_effect,
    effect_difference = sensitivity_effect - primary_effect,
    primary_ci95_low = primary_ci_low, primary_ci95_high = primary_ci_high,
    sensitivity_ci95_low = sensitivity_ci_low,
    sensitivity_ci95_high = sensitivity_ci_high,
    primary_fdr = primary_fdr, sensitivity_fdr = sensitivity_fdr,
    direction_concordant = ifelse(
      is.finite(primary_effect) & is.finite(sensitivity_effect),
      sign(primary_effect) == sign(sensitivity_effect), NA
    ),
    conclusion_changed = ifelse(
      is.finite(primary_fdr) & is.finite(sensitivity_fdr),
      (primary_fdr < 0.05) != (sensitivity_fdr < 0.05), NA
    ),
    repetitions_planned = repetitions_planned,
    repetitions_completed = repetitions_completed,
    terminal_status = terminal_status, message = message
  )
}

compare_fraction_variant <- function(primary, alternative, sensitivity_id) {
  if (!nrow(alternative)) return(data.table::data.table())
  baseline <- primary[, .(
    rds_id, cell_type_high_resolution, contrast_id, contrast_name,
    primary_effect = effect_size, primary_ci_low = ci95_low,
    primary_ci_high = ci95_high,
    primary_fdr = fdr_bh_mito_fraction_family
  )]
  merged <- merge(
    baseline, alternative,
    by = c("rds_id", "cell_type_high_resolution", "contrast_id", "contrast_name"),
    all = FALSE
  )
  if (!nrow(merged)) return(data.table::data.table())
  make_standard_result(
    sensitivity_id, "mitochondrial_fraction", merged$rds_id,
    merged$cell_type_high_resolution, merged$contrast_id, merged$contrast_name,
    "mitochondrial_fraction", "total_mt_count_over_total_umi_count",
    merged$primary_effect, merged$effect_size,
    merged$primary_ci_low, merged$primary_ci_high,
    merged$ci95_low, merged$ci95_high,
    merged$primary_fdr, merged$fdr
  )
}

run_replicate_sensitivity <- function(
    samples, manifest, primary_fraction, covariates, mode,
    repetitions, seed) {
  replicate_rows <- list()
  diagnostic_rows <- list()
  set.seed(seed)
  eligible_manifest <- manifest[manifest$eligibility_status == "eligible", , drop = FALSE]
  for (rds_id in sort(unique(eligible_manifest$rds_id))) {
    rds_manifest <- eligible_manifest[eligible_manifest$rds_id == rds_id, , drop = FALSE]
    for (cell_type in sort(unique(rds_manifest$cell_type_high_resolution))) {
      rows <- rds_manifest[rds_manifest$cell_type_high_resolution == cell_type, , drop = FALSE]
      metadata <- samples[
        samples$rds_id == rds_id & samples$cell_type_high_resolution == cell_type &
          as_logical(samples$primary_eligible), , drop = FALSE
      ]
      donors <- unique(metadata$projid)
      iterations <- if (mode == "bootstrap") seq_len(repetitions) else seq_along(donors)
      completed_iterations <- 0L
      for (iteration in iterations) {
        sampled <- if (mode == "bootstrap") {
          indices <- unlist(lapply(split(seq_len(nrow(metadata)), metadata$group_label), function(index) {
            sample(index, length(index), replace = TRUE)
          }), use.names = FALSE)
          metadata[indices, , drop = FALSE]
        } else {
          metadata[metadata$projid != donors[[iteration]], , drop = FALSE]
        }
        model <- fit_fraction_design(sampled, covariates)
        if (nzchar(model$error)) next
        any_result <- FALSE
        for (i in seq_len(nrow(rows))) {
          test <- tryCatch(test_fraction_contrast(model, rows[i, , drop = FALSE]), error = function(e) NULL)
          if (is.null(test)) next
          any_result <- TRUE
          replicate_rows[[length(replicate_rows) + 1L]] <- data.frame(
            rds_id = rds_id, cell_type_high_resolution = cell_type,
            contrast_id = rows$contrast_id[[i]], contrast_name = rows$contrast_name[[i]],
            iteration = iteration, effect_size = test$effect_size,
            p_value = test$p_value, stringsAsFactors = FALSE
          )
        }
        if (any_result) completed_iterations <- completed_iterations + 1L
      }
      diagnostic_rows[[length(diagnostic_rows) + 1L]] <- data.frame(
        schema_version = "sensitivity_replicate_diagnostics_v1",
        sensitivity_id = if (mode == "bootstrap") "donor_bootstrap" else "leave_one_donor_out",
        rds_id = rds_id, cell_type_high_resolution = cell_type,
        repetitions_planned = length(iterations),
        repetitions_with_any_result = completed_iterations,
        terminal_status = if (completed_iterations == length(iterations)) "validated_complete" else "failed",
        message = "", stringsAsFactors = FALSE
      )
    }
  }
  replicates <- if (length(replicate_rows)) data.table::rbindlist(replicate_rows) else data.table::data.table()
  diagnostics <- if (length(diagnostic_rows)) data.table::rbindlist(diagnostic_rows) else data.table::data.table()
  if (!nrow(replicates)) return(list(results = data.table::data.table(), diagnostics = diagnostics))
  summary <- replicates[, {
    values <- effect_size[is.finite(effect_size)]
    p_values <- p_value[is.finite(p_value)]
    sensitivity_p <- if (mode == "bootstrap") {
      min(1, 2 * min(
        (1 + sum(values <= 0)) / (length(values) + 1),
        (1 + sum(values >= 0)) / (length(values) + 1)
      ))
    } else max(p_values)
    list(
      sensitivity_effect = stats::median(values),
      sensitivity_ci_low = stats::quantile(values, 0.025, names = FALSE),
      sensitivity_ci_high = stats::quantile(values, 0.975, names = FALSE),
      sensitivity_p = sensitivity_p,
      repetitions_completed = length(values)
    )
  }, by = .(rds_id, cell_type_high_resolution, contrast_id, contrast_name)]
  summary[, sensitivity_fdr := stats::p.adjust(sensitivity_p, method = "BH")]
  baseline <- primary_fraction[, .(
    rds_id, cell_type_high_resolution, contrast_id, contrast_name,
    primary_effect = effect_size, primary_ci_low = ci95_low,
    primary_ci_high = ci95_high,
    primary_fdr = fdr_bh_mito_fraction_family
  )]
  summary <- merge(summary, baseline, by = c(
    "rds_id", "cell_type_high_resolution", "contrast_id", "contrast_name"
  ), all = FALSE)
  sensitivity_id <- if (mode == "bootstrap") "donor_bootstrap" else "leave_one_donor_out"
  results <- make_standard_result(
    sensitivity_id, "mitochondrial_fraction", summary$rds_id,
    summary$cell_type_high_resolution, summary$contrast_id, summary$contrast_name,
    "mitochondrial_fraction", "total_mt_count_over_total_umi_count",
    summary$primary_effect, summary$sensitivity_effect,
    summary$primary_ci_low, summary$primary_ci_high,
    summary$sensitivity_ci_low, summary$sensitivity_ci_high,
    summary$primary_fdr, summary$sensitivity_fdr,
    if (mode == "bootstrap") repetitions else summary$repetitions_completed,
    summary$repetitions_completed
  )
  list(results = results, diagnostics = diagnostics)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(absolute_path(config$project$root %||% ".", invocation_root), mustWork = TRUE)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)

pilot <- isTRUE(config$scope$pilot)
execution <- list(
  execution_stage = if (pilot) "local_pilot" else "minerva_production",
  execution_phase = if (pilot) 1L else 2L,
  backend = "direct", run_id = if (pilot) "manual_local_sensitivity" else "manual_sensitivity"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}
settings <- if (pilot) analysis$pilot else analysis$production
bootstrap_repetitions <- as.integer(settings$sensitivity_bootstrap_repetitions)
output_status <- as.character(settings$output_status)
minimum_primary <- as.integer(analysis$pseudobulk$minimum_nuclei_primary)
minimum_sensitivity <- as.integer(analysis$pseudobulk$minimum_nuclei_sensitivity)
minimum_donors <- as.integer(analysis$pseudobulk$minimum_donors_per_contrast_side)
base_seed <- as.integer(analysis$analysis$seed)
alpha <- as.numeric(analysis$multiple_testing$alpha)

phase11_dir <- file.path(output_root, "11_multiple_testing")
gene_mt_path <- file.path(phase11_dir, "gene_multiple_testing.tsv.gz")
pathway_mt_path <- file.path(phase11_dir, "pathway_multiple_testing.tsv.gz")
similarity_mt_path <- file.path(phase11_dir, "similarity_multiple_testing.tsv.gz")
phase11_status_path <- file.path(phase11_dir, "multiple_testing_status.tsv")
read_validated_statuses(phase11_status_path, "multiple_testing_status_v1")

fraction_paths <- list.files(file.path(output_root, "09_downstream"), pattern = "[.]mito_fraction_models[.]tsv$", full.names = TRUE)
fraction_status_paths <- list.files(file.path(output_root, "09_downstream"), pattern = "[.]mito_fraction_status[.]tsv$", full.names = TRUE)
read_validated_statuses(fraction_status_paths, "mito_fraction_status_v1")
pb_bundle_paths <- list.files(file.path(output_root, "07_pseudobulk"), pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE)
pb_status_paths <- list.files(file.path(output_root, "07_pseudobulk"), pattern = "[.]pseudobulk_status[.]tsv$", full.names = TRUE)
read_validated_statuses(pb_status_paths, "pseudobulk_status_v1")
qc_paths <- list.files(file.path(output_root, "04_qc"), pattern = "_cell_qc[.]tsv[.]gz$", full.names = TRUE)
qc_status_paths <- list.files(file.path(output_root, "04_qc"), pattern = "_qc_status[.]tsv$", full.names = TRUE)
read_validated_statuses(qc_status_paths, "mito_qc_status_v1")

contrast_candidates <- list.files(file.path(output_root, "07_contrasts"), pattern = "contrast_manifest[.]tsv$", full.names = TRUE)
contrast_candidates <- contrast_candidates[!grepl("checks|artifacts|status", basename(contrast_candidates))]
preferred <- contrast_candidates[basename(contrast_candidates) == paste0(execution$execution_stage, "_contrast_manifest.tsv")]
contrast_path <- if (length(preferred) == 1L) preferred else contrast_candidates
if (length(contrast_path) != 1L) stop("Contrast manifest selection must identify one file", call. = FALSE)

required_inputs <- c(
  gene_mt_path, pathway_mt_path, similarity_mt_path, phase11_status_path,
  fraction_paths, fraction_status_paths, pb_bundle_paths, pb_status_paths,
  qc_paths, qc_status_paths, contrast_path, analysis_path, manifest_path
)
if (any(!file.exists(required_inputs))) stop("One or more Phase 12 inputs are missing", call. = FALSE)
upstream_sha_before <- vapply(required_inputs, sha256_file, character(1))

gene_mt <- data.table::fread(gene_mt_path)
pathway_mt <- data.table::fread(pathway_mt_path)
similarity_mt <- data.table::fread(similarity_mt_path)
primary_fraction <- read_many(fraction_paths)
manifest <- data.table::fread(contrast_path, data.table = FALSE)

bundle_list <- lapply(pb_bundle_paths, readRDS)
samples <- data.table::rbindlist(lapply(bundle_list, function(bundle) data.table::as.data.table(bundle$samples)), fill = TRUE)
samples[, projid := normalize_projid(projid)]
samples[, group_label := paste(diagnosis, sex, apoe_group, sep = "__")]
donor_pmi <- unique(samples[, .(projid, pmi_log1p)])
pmi_center <- mean(donor_pmi$pmi_log1p, na.rm = TRUE)
pmi_scale <- stats::sd(donor_pmi$pmi_log1p, na.rm = TRUE)
samples[, pmi_log1p_scaled := (pmi_log1p - pmi_center) / pmi_scale]

qc <- read_many(qc_paths)
qc[, projid := normalize_projid(projid)]
unflagged <- qc[as_logical(cohort_included) & !as_logical(robust_any_flag), .(
  nuclei = .N,
  total_umi_count = sum(as.numeric(nCount_RNA)),
  total_mt_count = sum(as.numeric(nCount_MT)),
  diagnosis = diagnosis[[1L]], sex = sex[[1L]], apoe_group = apoe_group[[1L]]
), by = .(rds_id, projid, cell_type_high_resolution)]
donor_covariates <- unique(samples[, .(
  rds_id, projid, age_death_numeric, age_90plus, pmi_numeric,
  pmi_log1p, pmi_log1p_scaled, age_death_scaled, pmi_scaled
)])
unflagged <- merge(unflagged, donor_covariates, by = c("rds_id", "projid"), all.x = TRUE)
unflagged[, `:=`(
  primary_eligible = nuclei >= minimum_primary,
  sensitivity_eligible = nuclei >= minimum_sensitivity,
  group_label = paste(diagnosis, sex, apoe_group, sep = "__")
)]

primary_refit <- fit_fraction_variant(
  samples, manifest, "primary_eligible", c("age_death_scaled", "pmi_scaled"),
  "primary_fraction_refit_parity", minimum_donors
)
flagged_fit <- fit_fraction_variant(
  unflagged, manifest, "primary_eligible", c("age_death_scaled", "pmi_scaled"),
  "flagged_nuclei_exclusion", minimum_donors
)
threshold50_fit <- fit_fraction_variant(
  samples, manifest, "sensitivity_eligible", c("age_death_scaled", "pmi_scaled"),
  "nuclei_minimum_50", minimum_donors
)
age_pmi_fit <- fit_fraction_variant(
  samples, manifest, "primary_eligible",
  c("age_death_scaled", "age_90plus", "pmi_log1p_scaled"),
  "alternative_age_pmi_encoding", minimum_donors
)

result_list <- list()
diagnostic_list <- list(
  primary_refit$diagnostics, flagged_fit$diagnostics,
  threshold50_fit$diagnostics, age_pmi_fit$diagnostics
)
status_list <- list()
add_status <- function(sensitivity_id, category, terminal_status, rows, message, repetitions = 0L) {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "sensitivity_robustness_v1",
    sensitivity_id = sensitivity_id, category = category,
    terminal_status = terminal_status, result_rows = as.integer(rows),
    repetitions_completed = as.integer(repetitions), message = message,
    stringsAsFactors = FALSE
  )
}

method_keys <- c("rds_id", "cell_type_high_resolution", "contrast_id", "contrast_name", "gene")
pb <- gene_mt[method_branch == "pseudobulk"]
mast <- gene_mt[method_branch == "mast"]
method_compare <- merge(pb, mast, by = method_keys, suffixes = c("_pb", "_mast"), all = FALSE)
method_compare <- method_compare[
  is_mtdna_protein_gene_pb | is_mitocarta_pb |
    fdr_bh_within_contrast_pb < alpha | fdr_bh_within_contrast_mast < alpha |
    fdr_bh_global_genome_sensitivity_pb < alpha |
    fdr_bh_global_genome_sensitivity_mast < alpha
]
if (nrow(method_compare)) {
  result_list[[length(result_list) + 1L]] <- make_standard_result(
    "pseudobulk_vs_mast", "pseudobulk_primary__mast_sensitivity",
    method_compare$rds_id, method_compare$cell_type_high_resolution,
    method_compare$contrast_id, method_compare$contrast_name,
    "gene", method_compare$gene, method_compare$logFC_pb, method_compare$logFC_mast,
    NA_real_, NA_real_, NA_real_, NA_real_,
    method_compare$fdr_bh_within_contrast_pb,
    method_compare$fdr_bh_within_contrast_mast
  )
}
add_status(
  "pseudobulk_vs_mast", "method_branch",
  if (nrow(method_compare)) "validated_complete" else "not_estimable",
  nrow(method_compare), "common mitochondrial/headline gene tests compared"
)

global_gene <- gene_mt[
  is_mtdna_protein_gene | is_mitocarta |
    fdr_bh_within_contrast < alpha | fdr_bh_global_genome_sensitivity < alpha
]
global_results <- make_standard_result(
  "global_vs_within_contrast_fdr", global_gene$method_branch,
  global_gene$rds_id, global_gene$cell_type_high_resolution,
  global_gene$contrast_id, global_gene$contrast_name,
  "gene", global_gene$gene, global_gene$logFC, global_gene$logFC,
  NA_real_, NA_real_, NA_real_, NA_real_,
  global_gene$fdr_bh_within_contrast, global_gene$fdr_bh_global_genome_sensitivity
)
eligible_pathway <- pathway_mt[
  terminal_status == "validated_complete" &
    (rank_fdr_bh_within_branch_contrast < alpha | rank_fdr_bh_global_branch < alpha)
]
if (nrow(eligible_pathway)) {
  global_results <- data.table::rbindlist(list(global_results, make_standard_result(
    "global_vs_within_contrast_fdr", eligible_pathway$method_branch,
    eligible_pathway$rds_id, eligible_pathway$cell_type_high_resolution,
    eligible_pathway$contrast_id, eligible_pathway$contrast_name,
    "pathway_rank", eligible_pathway$hierarchy,
    eligible_pathway$rank_mean_difference, eligible_pathway$rank_mean_difference,
    NA_real_, NA_real_, NA_real_, NA_real_,
    eligible_pathway$rank_fdr_bh_within_branch_contrast,
    eligible_pathway$rank_fdr_bh_global_branch
  )), fill = TRUE)
}
similarity_headline <- similarity_mt[
  is_mtdna_protein_gene | is_mitocarta |
    empirical_fdr_bh_within_branch_comparison < alpha |
    empirical_fdr_bh_global_method_branch < alpha
]
if (nrow(similarity_headline)) {
  global_results <- data.table::rbindlist(list(global_results, make_standard_result(
    "global_vs_within_contrast_fdr", similarity_headline$method_branch,
    NA_character_, NA_character_, similarity_headline$comparison_id,
    similarity_headline$comparison_id, "similarity_gene", similarity_headline$gene,
    similarity_headline$similarity_score, similarity_headline$similarity_score,
    NA_real_, NA_real_, NA_real_, NA_real_,
    similarity_headline$empirical_fdr_bh_within_branch_comparison,
    similarity_headline$empirical_fdr_bh_global_method_branch
  )), fill = TRUE)
}
result_list[[length(result_list) + 1L]] <- global_results
add_status("global_vs_within_contrast_fdr", "multiple_testing", "validated_complete", nrow(global_results), "within-result and global sensitivity FDR compared")

flagged_result <- compare_fraction_variant(primary_fraction, flagged_fit$results, "flagged_nuclei_exclusion")
if (nrow(flagged_result)) result_list[[length(result_list) + 1L]] <- flagged_result
add_status(
  "flagged_nuclei_exclusion", "qc_refit",
  if (nrow(flagged_result)) "validated_complete" else "not_estimable",
  nrow(flagged_result), "mitochondrial-fraction model refit after excluding robustly flagged nuclei"
)
threshold50_result <- compare_fraction_variant(primary_fraction, threshold50_fit$results, "nuclei_minimum_50")
if (nrow(threshold50_result)) result_list[[length(result_list) + 1L]] <- threshold50_result
add_status(
  "nuclei_minimum_50", "eligibility_refit",
  if (nrow(threshold50_result)) "validated_complete" else "not_estimable",
  nrow(threshold50_result),
  if (nrow(threshold50_result)) "50-nucleus models refit" else "no contrast retained at 50 nuclei and five donors per side"
)
age_result <- compare_fraction_variant(primary_fraction, age_pmi_fit$results, "alternative_age_pmi_encoding")
if (nrow(age_result)) result_list[[length(result_list) + 1L]] <- age_result
add_status(
  "alternative_age_pmi_encoding", "covariate_refit",
  if (nrow(age_result)) "validated_complete" else "not_estimable",
  nrow(age_result), "age-90-plus indicator and scaled log1p PMI used"
)

lodo <- run_replicate_sensitivity(
  samples, manifest, primary_fraction, c("age_death_scaled", "pmi_scaled"),
  "leave_one_out", 0L, base_seed + 1200L
)
if (nrow(lodo$results)) result_list[[length(result_list) + 1L]] <- lodo$results
diagnostic_list[[length(diagnostic_list) + 1L]] <- lodo$diagnostics
add_status(
  "leave_one_donor_out", "donor_influence",
  if (nrow(lodo$results)) "validated_complete" else "not_estimable",
  nrow(lodo$results), "conservative maximum leave-one-out p-value recorded",
  if (nrow(lodo$results)) min(lodo$results$repetitions_completed) else 0L
)

bootstrap <- run_replicate_sensitivity(
  samples, manifest, primary_fraction, c("age_death_scaled", "pmi_scaled"),
  "bootstrap", bootstrap_repetitions, base_seed + 1250L
)
if (nrow(bootstrap$results)) result_list[[length(result_list) + 1L]] <- bootstrap$results
diagnostic_list[[length(diagnostic_list) + 1L]] <- bootstrap$diagnostics
bootstrap_complete <- nrow(bootstrap$results) &&
  all(bootstrap$results$repetitions_completed == bootstrap_repetitions)
add_status(
  "donor_bootstrap", "donor_resampling",
  if (bootstrap_complete) "validated_complete" else "failed",
  nrow(bootstrap$results), paste0("stratified donor bootstrap; configured repetitions=", bootstrap_repetitions),
  if (nrow(bootstrap$results)) min(bootstrap$results$repetitions_completed) else 0L
)

batch_fields <- grep("batch|lane|library_id|sequencing", names(samples), ignore.case = TRUE, value = TRUE)
add_status(
  "validated_batch_covariate", "covariate_refit", "blocked_missing_input", 0L,
  if (length(batch_fields)) {
    "candidate batch fields exist but require validation before modeling"
  } else {
    "no validated sequencing-batch field is available"
  }
)
sct_files <- list.files(
  output_root, pattern = "sct|sctransform", recursive = TRUE,
  full.names = TRUE, ignore.case = TRUE
)
add_status(
  "normalization_sctransform", "normalization", "blocked_missing_input", 0L,
  if (length(sct_files)) {
    "SCTransform artifacts exist but no frozen sensitivity assay mapping is declared"
  } else {
    "no separately stored SCTransform sensitivity artifact exists"
  }
)
add_status(
  "per_object_vs_results_only_harmonization", "harmonization",
  "blocked_missing_input", 0L,
  "results-only pseudobulk/MAST harmonization is available; no prespecified per-object harmonized result bundle exists"
)
alternative_set <- analysis$references$alternative_mitochondrial_gene_set %||% NULL
add_status(
  "alternative_external_mitochondrial_sets", "gene_set",
  "blocked_missing_input", 0L,
  if (is.null(alternative_set)) {
    "no alternative external mitochondrial set is frozen in the scientific configuration"
  } else {
    "alternative set is declared but its comparison is not yet validated"
  }
)

if (!pilot && any(vapply(
  status_list,
  function(row) row$terminal_status[[1L]] %in% c("blocked_missing_input", "failed"),
  logical(1)
))) {
  output_status <- "partial_with_blocked_sensitivities"
}

results <- data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE)
results[, `:=`(execution_stage = execution$execution_stage, output_status = output_status)]
robustness <- data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE)
robustness[, `:=`(execution_stage = execution$execution_stage, output_status = output_status)]
diagnostics <- data.table::rbindlist(diagnostic_list, fill = TRUE, use.names = TRUE)
diagnostics[, `:=`(execution_stage = execution$execution_stage, output_status = output_status)]

prespecified_ids <- c(
  "pseudobulk_vs_mast", "flagged_nuclei_exclusion", "nuclei_minimum_50",
  "normalization_sctransform", "alternative_age_pmi_encoding",
  "validated_batch_covariate", "leave_one_donor_out", "donor_bootstrap",
  "per_object_vs_results_only_harmonization",
  "alternative_external_mitochondrial_sets", "global_vs_within_contrast_fdr"
)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "sensitivity_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
primary_compare <- merge(
  primary_fraction[, .(contrast_id, primary_effect = effect_size)],
  primary_refit$results[, .(contrast_id, refit_effect = effect_size)],
  by = "contrast_id", all = FALSE
)
parity_difference <- if (nrow(primary_compare)) {
  max(abs(primary_compare$primary_effect - primary_compare$refit_effect))
} else Inf
add_check(
  "primary_fraction_refit_parity",
  nrow(primary_compare) == nrow(primary_fraction) && parity_difference < 1e-8,
  parity_difference, "<1e-8"
)
add_check(
  "all_prespecified_sensitivities_have_terminal_status",
  setequal(robustness$sensitivity_id, prespecified_ids) && !anyDuplicated(robustness$sensitivity_id),
  paste(sort(robustness$sensitivity_id), collapse = ";"),
  paste(sort(prespecified_ids), collapse = ";")
)
add_check(
  "terminal_status_vocabulary",
  all(robustness$terminal_status %in% c(
    "validated_complete", "not_estimable", "blocked_missing_input", "failed"
  )), paste(sort(unique(robustness$terminal_status)), collapse = ";"),
  "declared_terminal_status"
)
add_check(
  "no_failed_sensitivity", !any(robustness$terminal_status == "failed"),
  sum(robustness$terminal_status == "failed"), 0L
)
completed <- results$terminal_status == "validated_complete"
add_check(
  "completed_results_have_effect_and_fdr",
  all(is.finite(results$primary_effect[completed]) &
    is.finite(results$sensitivity_effect[completed]) &
    is.finite(results$primary_fdr[completed]) &
    is.finite(results$sensitivity_fdr[completed])),
  sum(completed), sum(completed)
)
add_check(
  "bootstrap_repetitions_complete",
  robustness$repetitions_completed[robustness$sensitivity_id == "donor_bootstrap"] >= bootstrap_repetitions,
  robustness$repetitions_completed[robustness$sensitivity_id == "donor_bootstrap"],
  bootstrap_repetitions
)
add_check(
  "blocked_sensitivities_have_reason",
  all(nzchar(robustness$message[robustness$terminal_status == "blocked_missing_input"])),
  sum(robustness$terminal_status == "blocked_missing_input"), "all_have_message"
)
add_check(
  "nonfinal_pilot_label",
  !pilot || (all(results$output_status == "nonfinal_smoke_test") &&
    all(robustness$output_status == "nonfinal_smoke_test")),
  output_status, if (pilot) "nonfinal_smoke_test" else output_status
)
result_key <- paste(
  results$sensitivity_id, results$method_branch, results$rds_id,
  results$contrast_id, results$entity_type, results$entity, sep = "\r"
)
add_check("result_keys_unique", !anyDuplicated(result_key), anyDuplicated(result_key), 0L)
checks <- data.table::rbindlist(checks)

output_dir <- file.path(output_root, "12_sensitivity")
result_path <- file.path(
  output_dir, if (pilot) "sensitivity_smoke.tsv" else "sensitivity_results.tsv.gz"
)
paths <- list(
  results = result_path,
  robustness = file.path(output_dir, "sensitivity_robustness.tsv"),
  diagnostics = file.path(output_dir, "sensitivity_diagnostics.tsv"),
  checks = file.path(output_dir, "sensitivity_checks.tsv"),
  artifacts = file.path(output_dir, "sensitivity_artifacts.tsv"),
  status = file.path(output_dir, "sensitivity_status.tsv")
)
atomic_write_tsv(results, paths$results, gzip = !pilot)
atomic_write_tsv(robustness, paths$robustness)
atomic_write_tsv(diagnostics, paths$diagnostics)
atomic_write_tsv(checks, paths$checks)

upstream_sha_after <- vapply(required_inputs, sha256_file, character(1))
upstream_unchanged <- identical(unname(upstream_sha_before), unname(upstream_sha_after))
checks <- data.table::fread(paths$checks)
checks <- data.table::rbindlist(list(checks, data.frame(
  schema_version = "sensitivity_checks_v1",
  check = "upstream_artifacts_unchanged", passed = upstream_unchanged,
  observed = if (upstream_unchanged) "unchanged" else "changed",
  expected = "unchanged", stringsAsFactors = FALSE
)))
atomic_write_tsv(checks, paths$checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

artifact_paths <- unlist(paths[c("results", "robustness", "diagnostics", "checks")])
artifacts <- data.frame(
  schema_version = "sensitivity_artifacts_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(results), nrow(robustness), nrow(diagnostics), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "sensitivity_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = "global:sensitivity",
  source_rds = paste(sort(unique(samples$rds_id)), collapse = ";"),
  scientific_script = "scripts/12_sensitivity_analysis.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/12_sensitivity_analysis.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  upstream_input_bundle_sha256 = sha256_lines(paste(names(upstream_sha_before), upstream_sha_before, sep = "=")),
  bootstrap_repetitions = bootstrap_repetitions,
  output_status = output_status,
  prespecified_sensitivities = length(prespecified_ids),
  completed_sensitivities = sum(robustness$terminal_status == "validated_complete"),
  not_estimable_sensitivities = sum(robustness$terminal_status == "not_estimable"),
  blocked_sensitivities = sum(robustness$terminal_status == "blocked_missing_input"),
  result_rows = nrow(results),
  conclusion_changes = sum(results$conclusion_changed, na.rm = TRUE),
  direction_discordant_rows = sum(!results$direction_concordant, na.rm = TRUE),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Sensitivity output: ", output_dir, "\n", sep = "")
cat("Sensitivity result rows: ", nrow(results), "\n", sep = "")
cat("Completed sensitivities: ", status$completed_sensitivities, "\n", sep = "")
cat("Not estimable sensitivities: ", status$not_estimable_sensitivities, "\n", sep = "")
cat("Blocked sensitivities: ", status$blocked_sensitivities, "\n", sep = "")
cat("Conclusion changes: ", status$conclusion_changes, "\n", sep = "")
cat("Phase 12 status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
