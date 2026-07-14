#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = "mito_fraction"
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--task-mode"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/09_run_mito_fraction_models.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--task-mode mito_fraction]\n",
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
  if (!identical(out$task_mode, "mito_fraction")) {
    stop("--task-mode must be 'mito_fraction'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
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

parse_terms <- function(value) {
  if (is.na(value) || !nzchar(value)) return(setNames(numeric(), character()))
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
    stop(
      "Required design groups are absent: ",
      paste(setdiff(names(terms), design_columns), collapse = ", ")
    )
  }
  contrast <- setNames(numeric(length(design_columns)), design_columns)
  contrast[names(terms)] <- terms
  contrast
}

make_global_contrasts <- function(design_columns) {
  sexes <- c("Female", "Male")
  apoe_levels <- c("e2", "e33", "e4")
  strata <- as.vector(outer(sexes, apoe_levels, paste, sep = "__"))
  reference <- "Female__e33"
  comparisons <- setdiff(strata, reference)
  matrix <- matrix(
    0, nrow = length(design_columns), ncol = length(comparisons),
    dimnames = list(design_columns, paste0("effect_", comparisons, "_minus_", reference))
  )
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

serialize_group_counts <- function(metadata, groups, field) {
  values <- vapply(groups, function(group) {
    sum(metadata[[field]][metadata$group_label == group], na.rm = TRUE)
  }, numeric(1))
  paste(paste(groups, format(values, scientific = FALSE, trim = TRUE), sep = "="), collapse = ";")
}

read_status <- function(path, expected_schema) {
  if (!file.exists(path)) stop("Required status file is missing: ", path, call. = FALSE)
  value <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
  if (nrow(value) != 1L || !identical(value$schema_version[[1L]], expected_schema) ||
      !identical(value$validation_status[[1L]], "validated_complete")) {
    stop("Required status is not validated_complete: ", path, call. = FALSE)
  }
  value
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table")
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root), mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
rds_manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)
rds_manifest <- read.delim(rds_manifest_path, check.names = FALSE, stringsAsFactors = FALSE)

if (!is.null(args$manifest_row)) {
  selected <- rds_manifest[rds_manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
} else if (!is.null(args$rds_id)) {
  selected <- rds_manifest[rds_manifest$rds_id == args$rds_id, , drop = FALSE]
} else {
  enabled <- if ("enabled" %in% names(rds_manifest)) as_logical(rds_manifest$enabled) else rep(TRUE, nrow(rds_manifest))
  selected <- rds_manifest[enabled, , drop = FALSE]
}
if (nrow(selected) != 1L) {
  stop("RDS manifest selection must identify exactly one row", call. = FALSE)
}

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct", run_id = "manual_mito_fraction"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
prefix <- tolower(rds_id)

bundle_candidates <- list.files(
  file.path(output_root, "07_pseudobulk"),
  pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE
)
bundle_match <- vapply(bundle_candidates, function(path) {
  value <- readRDS(path)
  identical(as.character(value$rds_id), rds_id)
}, logical(1))
bundle_path <- bundle_candidates[bundle_match]
if (length(bundle_path) != 1L) stop("Pseudobulk bundle selection must identify one file", call. = FALSE)
bundle <- readRDS(bundle_path)
if (!identical(bundle$schema_version, "pseudobulk_counts_v1")) {
  stop("Unsupported pseudobulk bundle schema", call. = FALSE)
}

sample_candidates <- list.files(
  file.path(output_root, "07_pseudobulk"),
  pattern = "[.]pseudobulk_samples[.]tsv$", full.names = TRUE
)
sample_match <- vapply(sample_candidates, function(path) {
  value <- read.delim(path, nrows = 1L, check.names = FALSE, stringsAsFactors = FALSE)
  "rds_id" %in% names(value) && identical(as.character(value$rds_id[[1L]]), rds_id)
}, logical(1))
sample_path <- sample_candidates[sample_match]
if (length(sample_path) != 1L) stop("Pseudobulk sample selection must identify one file", call. = FALSE)

qc_candidates <- list.files(
  file.path(output_root, "04_qc"), pattern = "_donor_celltype_qc[.]tsv$", full.names = TRUE
)
qc_match <- vapply(qc_candidates, function(path) {
  value <- read.delim(path, nrows = 1L, check.names = FALSE, stringsAsFactors = FALSE)
  "rds_id" %in% names(value) && identical(as.character(value$rds_id[[1L]]), rds_id)
}, logical(1))
qc_path <- qc_candidates[qc_match]
if (length(qc_path) != 1L) stop("Donor-cell-type QC selection must identify one file", call. = FALSE)

contrast_candidates <- list.files(
  file.path(output_root, "07_contrasts"),
  pattern = "contrast_manifest[.]tsv$", full.names = TRUE
)
contrast_candidates <- contrast_candidates[!grepl("checks|artifacts|status", basename(contrast_candidates))]
preferred <- contrast_candidates[
  basename(contrast_candidates) == paste0(execution$execution_stage, "_contrast_manifest.tsv")
]
contrast_path <- if (length(preferred) == 1L) preferred else contrast_candidates
if (length(contrast_path) != 1L) stop("Contrast manifest selection must identify one file", call. = FALSE)

base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_rel))
pseudobulk_status_path <- file.path(
  output_root, "07_pseudobulk", paste0(base_name, ".pseudobulk_status.tsv")
)
read_status(pseudobulk_status_path, "pseudobulk_status_v1")

samples <- as.data.frame(bundle$samples)
samples$primary_eligible <- as_logical(samples$primary_eligible)
samples$group_label <- paste(samples$diagnosis, samples$sex, samples$apoe_group, sep = "__")
required_sample_columns <- c(
  "projid", "cell_type_high_resolution", "diagnosis", "sex", "apoe_group",
  "age_death_scaled", "pmi_scaled", "nuclei", "total_umi_count",
  "total_mt_count", "primary_eligible", "group_label"
)
if (!all(required_sample_columns %in% names(samples))) {
  stop("Pseudobulk samples are missing required mitochondrial-fraction fields", call. = FALSE)
}
if (any(samples$total_mt_count < 0 | samples$total_umi_count <= 0 |
        samples$total_mt_count > samples$total_umi_count, na.rm = TRUE)) {
  stop("Invalid mitochondrial/total UMI count pairs", call. = FALSE)
}

contrast_manifest <- data.table::fread(contrast_path, data.table = FALSE)
contrast_manifest <- contrast_manifest[contrast_manifest$rds_id == rds_id, , drop = FALSE]
if (!nrow(contrast_manifest)) stop("No contrast rows apply to ", rds_id, call. = FALSE)

result_list <- list()
diagnostic_list <- list()
status_list <- list()

add_contrast_status <- function(row, terminal_status, message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "mito_fraction_contrast_status_v1",
    rds_id = rds_id, manifest_row = row$manifest_row,
    contrast_id = row$contrast_id,
    cell_type_high_resolution = row$cell_type_high_resolution,
    contrast_family = row$contrast_family, contrast_name = row$contrast_name,
    eligibility_status = row$eligibility_status,
    terminal_status = terminal_status, message = message,
    stringsAsFactors = FALSE
  )
}

for (cell_type in sort(unique(contrast_manifest$cell_type_high_resolution))) {
  manifest_rows <- contrast_manifest[
    contrast_manifest$cell_type_high_resolution == cell_type, , drop = FALSE
  ]
  ineligible <- manifest_rows$eligibility_status != "eligible"
  if (any(ineligible)) {
    for (i in which(ineligible)) {
      add_contrast_status(
        manifest_rows[i, , drop = FALSE], "ineligible",
        manifest_rows$ineligibility_reason[[i]]
      )
    }
  }
  eligible_rows <- manifest_rows[!ineligible, , drop = FALSE]
  if (!nrow(eligible_rows)) {
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "mito_fraction_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, donors = 0L, groups = 0L,
      design_columns = "", design_rank = 0L, residual_df = NA_real_,
      dispersion = NA_real_, converged = NA, model_status = "not_fit_no_eligible_contrasts",
      message = "", stringsAsFactors = FALSE
    )
    next
  }

  metadata <- samples[
    samples$cell_type_high_resolution == cell_type & samples$primary_eligible,
    , drop = FALSE
  ]
  metadata$group <- factor(metadata$group_label)
  design <- stats::model.matrix(
    ~ 0 + group + age_death_scaled + pmi_scaled, data = metadata
  )
  group_columns <- seq_len(nlevels(metadata$group))
  colnames(design)[group_columns] <- levels(metadata$group)
  design_rank <- qr(design)$rank
  if (design_rank < ncol(design)) {
    message_text <- paste0("Design is rank deficient: ", design_rank, " of ", ncol(design))
    for (i in seq_len(nrow(eligible_rows))) {
      add_contrast_status(eligible_rows[i, , drop = FALSE], "failed", message_text)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "mito_fraction_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, donors = nrow(metadata),
      groups = nlevels(metadata$group), design_columns = paste(colnames(design), collapse = ";"),
      design_rank = design_rank, residual_df = NA_real_, dispersion = NA_real_,
      converged = FALSE, model_status = "failed", message = message_text,
      stringsAsFactors = FALSE
    )
    next
  }

  response <- cbind(
    mitochondrial = metadata$total_mt_count,
    non_mitochondrial = metadata$total_umi_count - metadata$total_mt_count
  )
  fit_error <- NULL
  fit <- tryCatch(
    stats::glm.fit(x = design, y = response, family = stats::quasibinomial()),
    error = function(e) {
      fit_error <<- conditionMessage(e)
      NULL
    }
  )
  if (is.null(fit)) {
    for (i in seq_len(nrow(eligible_rows))) {
      add_contrast_status(eligible_rows[i, , drop = FALSE], "failed", fit_error)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "mito_fraction_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, donors = nrow(metadata),
      groups = nlevels(metadata$group), design_columns = paste(colnames(design), collapse = ";"),
      design_rank = design_rank, residual_df = NA_real_, dispersion = NA_real_,
      converged = FALSE, model_status = "failed", message = fit_error,
      stringsAsFactors = FALSE
    )
    next
  }
  class(fit) <- c("glm", "lm")
  fit_summary <- summary(fit)
  covariance <- stats::vcov(fit)
  dispersion <- as.numeric(fit_summary$dispersion)
  diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
    schema_version = "mito_fraction_diagnostics_v1", rds_id = rds_id,
    cell_type_high_resolution = cell_type, donors = nrow(metadata),
    groups = nlevels(metadata$group), design_columns = paste(colnames(design), collapse = ";"),
    design_rank = fit$rank, residual_df = fit$df.residual, dispersion = dispersion,
    converged = isTRUE(fit$converged),
    model_status = if (isTRUE(fit$converged)) "fitted" else "failed_not_converged",
    message = "", stringsAsFactors = FALSE
  )

  for (i in seq_len(nrow(eligible_rows))) {
    row <- eligible_rows[i, , drop = FALSE]
    required_groups <- split_groups(row$required_groups)
    terms <- parse_terms(row$contrast_terms)
    test_error <- NULL
    test <- tryCatch({
      if (identical(row$contrast_kind, "single_df")) {
        contrast <- make_single_contrast(terms, colnames(design))
        estimate <- sum(contrast * stats::coef(fit))
        variance <- as.numeric(t(contrast) %*% covariance %*% contrast)
        standard_error <- sqrt(variance)
        statistic <- estimate / standard_error
        p_value <- 2 * stats::pt(abs(statistic), df = fit$df.residual, lower.tail = FALSE)
        critical <- stats::qt(0.975, df = fit$df.residual)
        list(
          effect_type = "log_odds_ratio", estimate = estimate,
          odds_ratio = exp(estimate), standard_error = standard_error,
          ci95_low = estimate - critical * standard_error,
          ci95_high = estimate + critical * standard_error,
          statistic = statistic, statistic_type = "t", numerator_df = 1L,
          p_value = p_value
        )
      } else if (identical(row$contrast_kind, "multi_df")) {
        contrast <- make_global_contrasts(colnames(design))
        estimates <- as.numeric(t(contrast) %*% stats::coef(fit))
        contrast_covariance <- t(contrast) %*% covariance %*% contrast
        numerator_df <- qr(contrast_covariance)$rank
        statistic <- as.numeric(
          t(estimates) %*% qr.solve(contrast_covariance, estimates) / numerator_df
        )
        p_value <- stats::pf(
          statistic, df1 = numerator_df, df2 = fit$df.residual, lower.tail = FALSE
        )
        list(
          effect_type = "maximum_absolute_log_odds_heterogeneity",
          estimate = max(abs(estimates)), odds_ratio = NA_real_,
          standard_error = NA_real_, ci95_low = NA_real_, ci95_high = NA_real_,
          statistic = statistic, statistic_type = "F", numerator_df = numerator_df,
          p_value = p_value
        )
      } else {
        stop("Unsupported contrast kind: ", row$contrast_kind)
      }
    }, error = function(e) {
      test_error <<- conditionMessage(e)
      NULL
    })
    if (is.null(test)) {
      add_contrast_status(row, "failed", test_error)
      next
    }

    positive_groups <- names(terms)[terms > 0]
    negative_groups <- names(terms)[terms < 0]
    positive_index <- metadata$group_label %in% positive_groups
    negative_index <- metadata$group_label %in% negative_groups
    result_list[[length(result_list) + 1L]] <- data.frame(
      schema_version = "mito_fraction_results_v1", rds_id = rds_id,
      source_rds = source_rel, cell_type_high_resolution = cell_type,
      manifest_row = row$manifest_row, contrast_id = row$contrast_id,
      contrast_family = row$contrast_family, contrast_name = row$contrast_name,
      contrast_kind = row$contrast_kind,
      model_method = "donor_level_quasibinomial_logit",
      numerator_field = "total_mt_count", denominator_field = "total_umi_count",
      effect_type = test$effect_type, effect_size = test$estimate,
      odds_ratio = test$odds_ratio, standard_error = test$standard_error,
      ci95_low = test$ci95_low, ci95_high = test$ci95_high,
      statistic = test$statistic, statistic_type = test$statistic_type,
      numerator_df = test$numerator_df, denominator_df = fit$df.residual,
      p_value = test$p_value, fdr_bh_mito_fraction_family = NA_real_,
      required_group_mt_counts = serialize_group_counts(metadata, required_groups, "total_mt_count"),
      required_group_total_counts = serialize_group_counts(metadata, required_groups, "total_umi_count"),
      positive_groups_mt_counts = sum(metadata$total_mt_count[positive_index]),
      positive_groups_total_counts = sum(metadata$total_umi_count[positive_index]),
      negative_groups_mt_counts = sum(metadata$total_mt_count[negative_index]),
      negative_groups_total_counts = sum(metadata$total_umi_count[negative_index]),
      model_donors = nrow(metadata), model_nuclei = sum(metadata$nuclei),
      dispersion = dispersion, covariates = "age_death_scaled;pmi_scaled",
      stringsAsFactors = FALSE
    )
    add_contrast_status(row, "validated_complete", "")
  }
}

contrast_status <- as.data.frame(data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE))
contrast_status <- contrast_status[order(contrast_status$manifest_row), , drop = FALSE]
diagnostics <- as.data.frame(data.table::rbindlist(diagnostic_list, fill = TRUE, use.names = TRUE))
if (length(result_list)) {
  results <- as.data.frame(data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE))
  results$fdr_bh_mito_fraction_family <- stats::p.adjust(results$p_value, method = "BH")
} else {
  results <- data.frame(
    schema_version = character(), rds_id = character(), source_rds = character(),
    cell_type_high_resolution = character(), manifest_row = integer(),
    contrast_id = character(), contrast_family = character(), contrast_name = character(),
    contrast_kind = character(), model_method = character(), numerator_field = character(),
    denominator_field = character(), effect_type = character(), effect_size = numeric(),
    odds_ratio = numeric(), standard_error = numeric(), ci95_low = numeric(),
    ci95_high = numeric(), statistic = numeric(), statistic_type = character(),
    numerator_df = numeric(), denominator_df = numeric(), p_value = numeric(),
    fdr_bh_mito_fraction_family = numeric(), required_group_mt_counts = character(),
    required_group_total_counts = character(), positive_groups_mt_counts = numeric(),
    positive_groups_total_counts = numeric(), negative_groups_mt_counts = numeric(),
    negative_groups_total_counts = numeric(), model_donors = integer(),
    model_nuclei = numeric(), dispersion = numeric(), covariates = character(),
    stringsAsFactors = FALSE
  )
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "mito_fraction_checks_v1", rds_id = rds_id,
    check = check, passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
eligible <- contrast_manifest$eligibility_status == "eligible"
status_index <- match(contrast_manifest$manifest_row, contrast_status$manifest_row)
add_check("one_terminal_status_per_manifest_row", nrow(contrast_status) == nrow(contrast_manifest) && !anyDuplicated(contrast_status$manifest_row), nrow(contrast_status), nrow(contrast_manifest))
add_check("eligible_contrasts_completed", all(contrast_status$terminal_status[status_index[eligible]] == "validated_complete"), sum(contrast_status$terminal_status == "validated_complete"), sum(eligible))
add_check("ineligible_contrasts_explicit", all(contrast_status$terminal_status[status_index[!eligible]] == "ineligible"), sum(contrast_status$terminal_status == "ineligible"), sum(!eligible))
add_check("result_keys_unique", !anyDuplicated(results$contrast_id), anyDuplicated(results$contrast_id), 0L)
add_check("numerator_denominator_valid", !nrow(results) || all(results$positive_groups_mt_counts <= results$positive_groups_total_counts & results$negative_groups_mt_counts <= results$negative_groups_total_counts), if (nrow(results)) sum(results$positive_groups_mt_counts > results$positive_groups_total_counts | results$negative_groups_mt_counts > results$negative_groups_total_counts) else 0L, 0L)
add_check("p_values_in_range", !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1), if (nrow(results)) sum(!is.finite(results$p_value) | results$p_value < 0 | results$p_value > 1) else 0L, 0L)
add_check("fdr_in_range", !nrow(results) || all(is.finite(results$fdr_bh_mito_fraction_family) & results$fdr_bh_mito_fraction_family >= 0 & results$fdr_bh_mito_fraction_family <= 1), if (nrow(results)) sum(!is.finite(results$fdr_bh_mito_fraction_family) | results$fdr_bh_mito_fraction_family < 0 | results$fdr_bh_mito_fraction_family > 1) else 0L, 0L)
add_check("all_models_donor_level", !nrow(results) || all(results$model_donors > 0 & results$model_nuclei >= results$model_donors), if (nrow(results)) min(results$model_donors) else 0L, ">0")
add_check("execution_stage_recorded", nzchar(execution$execution_stage), execution$execution_stage, "nonempty")
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "09_downstream")
paths <- list(
  results = file.path(output_dir, paste0(prefix, ".mito_fraction_models.tsv")),
  diagnostics = file.path(output_dir, paste0(prefix, ".mito_fraction_diagnostics.tsv")),
  contrast_status = file.path(output_dir, paste0(prefix, ".mito_fraction_contrast_status.tsv")),
  checks = file.path(output_dir, paste0(prefix, ".mito_fraction_checks.tsv")),
  artifacts = file.path(output_dir, paste0(prefix, ".mito_fraction_artifacts.tsv")),
  status = file.path(output_dir, paste0(prefix, ".mito_fraction_status.tsv"))
)
atomic_write_tsv(results, paths$results)
atomic_write_tsv(diagnostics, paths$diagnostics)
atomic_write_tsv(contrast_status, paths$contrast_status)
atomic_write_tsv(checks, paths$checks)
artifact_paths <- c(paths$results, paths$diagnostics, paths$contrast_status, paths$checks)
artifacts <- data.frame(
  schema_version = "mito_fraction_artifacts_v1", rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(results), nrow(diagnostics), nrow(contrast_status), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "mito_fraction_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = paste("mito_fraction", rds_id, sep = ":"),
  source_rds = source_rel,
  scientific_script = "scripts/09_run_mito_fraction_models.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/09_run_mito_fraction_models.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(rds_manifest_path),
  donor_celltype_qc_sha256 = sha256_file(qc_path),
  pseudobulk_bundle_sha256 = sha256_file(bundle_path),
  pseudobulk_samples_sha256 = sha256_file(sample_path),
  contrast_manifest_sha256 = sha256_file(contrast_path),
  model_method = "donor_level_quasibinomial_logit",
  manifest_rows = nrow(contrast_manifest), eligible_contrasts = sum(eligible),
  completed_contrasts = sum(contrast_status$terminal_status == "validated_complete"),
  ineligible_contrasts = sum(contrast_status$terminal_status == "ineligible"),
  failed_contrasts = sum(contrast_status$terminal_status == "failed"),
  significant_fdr_005 = if (nrow(results)) sum(results$fdr_bh_mito_fraction_family < 0.05) else 0L,
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Mitochondrial fraction results: ", paths$results, "\n", sep = "")
cat("Eligible contrasts: ", sum(eligible), "\n", sep = "")
cat("Completed contrasts: ", sum(contrast_status$terminal_status == "validated_complete"), "\n", sep = "")
cat("Significant fraction tests (BH FDR < 0.05): ", status$significant_fdr_005, "\n", sep = "")
cat("Mitochondrial fraction status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
