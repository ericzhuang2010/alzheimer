#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, counts = NULL, manifest = NULL,
    task_mode = "pseudobulk_de"
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--counts", "--manifest", "--task-mode"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/07_run_pseudobulk_de.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--counts RDS --manifest TSV] [--task-mode pseudobulk_de]\n",
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
  if (!identical(out$task_mode, "pseudobulk_de")) {
    stop("--task-mode must be 'pseudobulk_de'", call. = FALSE)
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

atomic_write_tsv_gz <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  stem <- sub("[.]gz$", "", path)
  tmp <- paste0(stem, ".tmp.", Sys.getpid(), ".gz")
  connection <- gzfile(tmp, open = "wt", compression = 6)
  on.exit(try(close(connection), silent = TRUE), add = TRUE)
  write.table(x, connection, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  close(connection)
  on.exit(NULL, add = FALSE)
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
    stop("Required design groups are absent: ", paste(setdiff(names(terms), design_columns), collapse = ", "))
  }
  vector <- setNames(numeric(length(design_columns)), design_columns)
  vector[names(terms)] <- terms
  vector
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
    sex <- pieces[[1L]]
    apoe <- pieces[[2L]]
    terms <- c(1, -1)
    names(terms) <- c(
      paste("AD", sex, apoe, sep = "__"),
      paste("NCI", sex, apoe, sep = "__")
    )
    make_single_contrast(terms, design_columns)
  }
  reference_vector <- effect_vector(reference)
  for (i in seq_along(comparisons)) {
    matrix[, i] <- effect_vector(comparisons[[i]]) - reference_vector
  }
  matrix
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "Matrix", "data.table", "edgeR", "limma")
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
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
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
} else if (!is.null(args$counts)) {
  selected <- NULL
} else {
  stop("Select an RDS with --manifest-row, --rds-id, or --counts", call. = FALSE)
}
if (!is.null(selected) && nrow(selected) != 1L) {
  stop("RDS manifest selection must identify exactly one row", call. = FALSE)
}

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct", run_id = "manual_pseudobulk_de"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

if (!is.null(args$counts)) {
  counts_path <- absolute_path(args$counts, project_root)
  bundle <- readRDS(counts_path)
  rds_id <- as.character(bundle$rds_id)
  source_rel <- as.character(bundle$source_rds)
} else {
  rds_id <- as.character(selected$rds_id[[1L]])
  source_rel <- as.character(selected$input_rds[[1L]])
  candidate_paths <- list.files(
    file.path(output_root, "07_pseudobulk"),
    pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE
  )
  if (!length(candidate_paths)) stop("No pseudobulk count bundles were found", call. = FALSE)
  matched <- vapply(candidate_paths, function(path) {
    metadata <- readRDS(path)
    identical(as.character(metadata$rds_id), rds_id)
  }, logical(1))
  counts_path <- candidate_paths[matched]
  if (length(counts_path) != 1L) stop("Pseudobulk bundle selection must identify one file", call. = FALSE)
  bundle <- readRDS(counts_path)
}
if (!identical(bundle$schema_version, "pseudobulk_counts_v1")) {
  stop("Unsupported pseudobulk bundle schema", call. = FALSE)
}

if (!is.null(args$manifest)) {
  contrast_manifest_path <- absolute_path(args$manifest, project_root)
} else {
  candidates <- list.files(
    file.path(output_root, "07_contrasts"),
    pattern = "contrast_manifest[.]tsv$", full.names = TRUE
  )
  candidates <- candidates[!grepl("checks|artifacts|status", basename(candidates))]
  preferred <- candidates[basename(candidates) == paste0(execution$execution_stage, "_contrast_manifest.tsv")]
  contrast_manifest_path <- if (length(preferred) == 1L) preferred else candidates
}
if (length(contrast_manifest_path) != 1L || !file.exists(contrast_manifest_path)) {
  stop("Contrast manifest selection must identify one file", call. = FALSE)
}
contrast_manifest <- data.table::fread(contrast_manifest_path, data.table = FALSE)
contrast_manifest <- contrast_manifest[contrast_manifest$rds_id == rds_id, , drop = FALSE]
if (!nrow(contrast_manifest)) stop("No contrast rows apply to ", rds_id, call. = FALSE)

counts <- bundle$counts
samples <- as.data.frame(bundle$samples)
if (!identical(colnames(counts), samples$pseudobulk_id)) {
  stop("Pseudobulk count columns and sample metadata disagree", call. = FALSE)
}
samples$primary_eligible <- as_logical(samples$primary_eligible)
samples$group_label <- paste(samples$diagnosis, samples$sex, samples$apoe_group, sep = "__")
cell_types <- unique(contrast_manifest$cell_type_high_resolution)
cell_types <- sort(cell_types)

result_list <- list()
diagnostic_list <- list()
status_list <- list()

add_contrast_status <- function(row, terminal_status, genes_returned = 0L, message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "pseudobulk_de_contrast_status_v1",
    rds_id = rds_id, manifest_row = row$manifest_row,
    contrast_id = row$contrast_id,
    cell_type_high_resolution = row$cell_type_high_resolution,
    contrast_family = row$contrast_family,
    contrast_name = row$contrast_name,
    eligibility_status = row$eligibility_status,
    terminal_status = terminal_status,
    genes_returned = as.integer(genes_returned),
    message = message,
    stringsAsFactors = FALSE
  )
}

for (cell_type in cell_types) {
  manifest_rows <- contrast_manifest[
    contrast_manifest$cell_type_high_resolution == cell_type, , drop = FALSE
  ]
  eligible_rows <- manifest_rows[manifest_rows$eligibility_status == "eligible", , drop = FALSE]
  ineligible_rows <- manifest_rows[manifest_rows$eligibility_status != "eligible", , drop = FALSE]
  if (nrow(ineligible_rows)) {
    for (i in seq_len(nrow(ineligible_rows))) {
      add_contrast_status(
        ineligible_rows[i, , drop = FALSE], "ineligible", 0L,
        ineligible_rows$ineligibility_reason[[i]]
      )
    }
  }
  if (!nrow(eligible_rows)) {
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "pseudobulk_model_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, samples = 0L, donors = 0L,
      input_genes = nrow(counts), tested_genes = 0L, design_columns = "",
      design_rank = 0L, residual_df_min = NA_real_,
      model_status = "not_fit_no_eligible_contrasts", message = "",
      stringsAsFactors = FALSE
    )
    next
  }

  sample_index <- which(
    samples$cell_type_high_resolution == cell_type & samples$primary_eligible
  )
  metadata <- samples[sample_index, , drop = FALSE]
  cell_counts <- counts[, sample_index, drop = FALSE]
  metadata$group <- factor(metadata$group_label)
  design <- stats::model.matrix(
    ~ 0 + group + age_death_scaled + pmi_scaled,
    data = metadata
  )
  group_columns <- seq_len(nlevels(metadata$group))
  colnames(design)[group_columns] <- levels(metadata$group)
  rank <- qr(design)$rank
  if (rank < ncol(design)) {
    message_text <- paste0("Design is rank deficient: ", rank, " of ", ncol(design))
    for (i in seq_len(nrow(eligible_rows))) {
      add_contrast_status(eligible_rows[i, , drop = FALSE], "failed", 0L, message_text)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "pseudobulk_model_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, samples = nrow(metadata),
      donors = length(unique(metadata$projid)), input_genes = nrow(cell_counts),
      tested_genes = 0L, design_columns = paste(colnames(design), collapse = ";"),
      design_rank = rank, residual_df_min = NA_real_, model_status = "failed",
      message = message_text, stringsAsFactors = FALSE
    )
    next
  }

  fit_error <- NULL
  fit_objects <- tryCatch({
    y <- edgeR::DGEList(counts = as.matrix(cell_counts))
    keep <- edgeR::filterByExpr(y, design = design)
    if (!any(keep)) stop("filterByExpr retained no genes")
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
    for (i in seq_len(nrow(eligible_rows))) {
      add_contrast_status(eligible_rows[i, , drop = FALSE], "failed", 0L, fit_error)
    }
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "pseudobulk_model_diagnostics_v1", rds_id = rds_id,
      cell_type_high_resolution = cell_type, samples = nrow(metadata),
      donors = length(unique(metadata$projid)), input_genes = nrow(cell_counts),
      tested_genes = 0L, design_columns = paste(colnames(design), collapse = ";"),
      design_rank = rank, residual_df_min = NA_real_, model_status = "failed",
      message = fit_error, stringsAsFactors = FALSE
    )
    next
  }

  y <- fit_objects$y
  fit <- fit_objects$fit
  keep <- fit_objects$keep
  residual_df_min <- min(fit$df.residual.zeros %||% fit$df.residual)
  diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
    schema_version = "pseudobulk_model_diagnostics_v1", rds_id = rds_id,
    cell_type_high_resolution = cell_type, samples = nrow(metadata),
    donors = length(unique(metadata$projid)), input_genes = nrow(cell_counts),
    tested_genes = sum(keep), design_columns = paste(colnames(design), collapse = ";"),
    design_rank = rank, residual_df_min = residual_df_min,
    model_status = "fitted", message = "", stringsAsFactors = FALSE
  )

  for (i in seq_len(nrow(eligible_rows))) {
    row <- eligible_rows[i, , drop = FALSE]
    test_error <- NULL
    test_result <- tryCatch({
      if (row$contrast_kind == "single_df") {
        contrast <- make_single_contrast(
          parse_terms(row$contrast_terms), colnames(design)
        )
        test <- edgeR::glmQLFTest(fit, contrast = contrast)
      } else if (row$contrast_kind == "multi_df") {
        contrast <- make_global_contrasts(colnames(design))
        test <- edgeR::glmQLFTest(fit, contrast = contrast)
      } else {
        stop("Unsupported contrast kind: ", row$contrast_kind)
      }
      table <- edgeR::topTags(test, n = Inf, sort.by = "none")$table
      list(test = test, table = table)
    }, error = function(e) {
      test_error <<- conditionMessage(e)
      NULL
    })
    if (is.null(test_result)) {
      add_contrast_status(row, "failed", 0L, test_error)
      next
    }

    table <- test_result$table
    test <- test_result$test
    required_groups <- split_groups(row$required_groups)
    relevant <- metadata$group_label %in% required_groups
    tested_counts <- y$counts[, relevant, drop = FALSE]
    detection_rate <- rowMeans(tested_counts > 0)
    if (row$contrast_kind == "single_df") {
      log_fc <- as.numeric(table$logFC)
      f_statistic <- as.numeric(table$F)
      standard_error <- rep(NA_real_, length(log_fc))
      positive_f <- is.finite(f_statistic) & f_statistic > 0
      standard_error[positive_f] <- abs(log_fc[positive_f]) / sqrt(f_statistic[positive_f])
      df_total <- as.numeric(test$df.total)
      if (length(df_total) == 1L) df_total <- rep(df_total, length(log_fc))
      critical <- stats::qt(0.975, df = df_total)
      ci_low <- log_fc - critical * standard_error
      ci_high <- log_fc + critical * standard_error
      effect_size <- log_fc
      effect_type <- "log2_fold_change"
    } else {
      log_fc_columns <- grep("^logFC", names(table), value = TRUE)
      if (length(log_fc_columns)) {
        effect_size <- apply(abs(as.matrix(table[, log_fc_columns, drop = FALSE])), 1L, max)
      } else {
        effect_size <- rep(NA_real_, nrow(table))
      }
      log_fc <- rep(NA_real_, nrow(table))
      standard_error <- rep(NA_real_, nrow(table))
      ci_low <- rep(NA_real_, nrow(table))
      ci_high <- rep(NA_real_, nrow(table))
      effect_type <- "maximum_absolute_heterogeneity_log2FC"
    }
    p_value <- as.numeric(table$PValue)
    result <- data.frame(
      schema_version = "pseudobulk_de_results_v1",
      rds_id = rds_id, source_rds = source_rel,
      cell_type_high_resolution = cell_type,
      manifest_row = row$manifest_row, contrast_id = row$contrast_id,
      contrast_family = row$contrast_family, contrast_name = row$contrast_name,
      contrast_kind = row$contrast_kind, paper_matched = row$paper_matched,
      gene = rownames(table), effect_type = effect_type,
      effect_size = effect_size, logFC = log_fc,
      standard_error = standard_error, ci95_low = ci_low, ci95_high = ci_high,
      logCPM = as.numeric(table$logCPM), F = as.numeric(table$F),
      p_value = p_value, fdr_bh_within_contrast = stats::p.adjust(p_value, method = "BH"),
      detection_rate_required_groups = as.numeric(detection_rate[rownames(table)]),
      numerator_donors = row$numerator_donors,
      denominator_donors = row$denominator_donors,
      numerator_nuclei = row$numerator_nuclei,
      denominator_nuclei = row$denominator_nuclei,
      model_samples = nrow(metadata), model_donors = length(unique(metadata$projid)),
      stringsAsFactors = FALSE
    )
    result_list[[length(result_list) + 1L]] <- result
    add_contrast_status(row, "validated_complete", nrow(result), "")
  }
  rm(cell_counts, y, fit)
  invisible(gc())
}

contrast_status <- data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE)
contrast_status <- as.data.frame(contrast_status)
contrast_status <- contrast_status[order(contrast_status$manifest_row), , drop = FALSE]
diagnostics <- data.table::rbindlist(diagnostic_list, fill = TRUE, use.names = TRUE)
diagnostics <- as.data.frame(diagnostics)
if (length(result_list)) {
  results <- data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE)
  results <- as.data.frame(results)
} else {
  results <- data.frame(
    schema_version = character(), rds_id = character(), source_rds = character(),
    cell_type_high_resolution = character(), manifest_row = integer(),
    contrast_id = character(), contrast_family = character(), contrast_name = character(),
    contrast_kind = character(), paper_matched = logical(), gene = character(),
    effect_type = character(), effect_size = numeric(), logFC = numeric(),
    standard_error = numeric(), ci95_low = numeric(), ci95_high = numeric(),
    logCPM = numeric(), F = numeric(), p_value = numeric(),
    fdr_bh_within_contrast = numeric(), detection_rate_required_groups = numeric(),
    numerator_donors = integer(), denominator_donors = integer(),
    numerator_nuclei = numeric(), denominator_nuclei = numeric(),
    model_samples = integer(), model_donors = integer(), stringsAsFactors = FALSE
  )
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "pseudobulk_de_checks_v1", rds_id = rds_id,
    check = check, passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
eligible_manifest <- contrast_manifest$eligibility_status == "eligible"
add_check("one_terminal_status_per_manifest_row", nrow(contrast_status) == nrow(contrast_manifest) && !anyDuplicated(contrast_status$manifest_row), nrow(contrast_status), nrow(contrast_manifest))
add_check("eligible_contrasts_completed", all(contrast_status$terminal_status[match(contrast_manifest$manifest_row[eligible_manifest], contrast_status$manifest_row)] == "validated_complete"), sum(contrast_status$terminal_status == "validated_complete"), sum(eligible_manifest))
add_check("ineligible_contrasts_explicit", all(contrast_status$terminal_status[match(contrast_manifest$manifest_row[!eligible_manifest], contrast_status$manifest_row)] == "ineligible"), sum(contrast_status$terminal_status == "ineligible"), sum(!eligible_manifest))
result_keys <- if (nrow(results)) paste(results$cell_type_high_resolution, results$contrast_id, results$gene, sep = "\r") else character()
add_check("result_keys_unique", !anyDuplicated(result_keys), anyDuplicated(result_keys), 0L)
add_check("p_values_in_range", !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1), if (nrow(results)) sum(!is.finite(results$p_value) | results$p_value < 0 | results$p_value > 1) else 0L, 0L)
add_check("fdr_in_range", !nrow(results) || all(is.finite(results$fdr_bh_within_contrast) & results$fdr_bh_within_contrast >= 0 & results$fdr_bh_within_contrast <= 1), if (nrow(results)) sum(!is.finite(results$fdr_bh_within_contrast) | results$fdr_bh_within_contrast < 0 | results$fdr_bh_within_contrast > 1) else 0L, 0L)
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "07_pseudobulk_de")
prefix <- tolower(rds_id)
paths <- list(
  results = file.path(output_dir, paste0(prefix, ".pseudobulk_de.tsv.gz")),
  diagnostics = file.path(output_dir, paste0(prefix, ".pseudobulk_model_diagnostics.tsv")),
  contrast_status = file.path(output_dir, paste0(prefix, ".pseudobulk_contrast_status.tsv")),
  checks = file.path(output_dir, paste0(prefix, ".pseudobulk_de_checks.tsv")),
  artifacts = file.path(output_dir, paste0(prefix, ".pseudobulk_de_artifacts.tsv")),
  status = file.path(output_dir, paste0(prefix, ".pseudobulk_de_status.tsv"))
)
atomic_write_tsv_gz(results, paths$results)
atomic_write_tsv(diagnostics, paths$diagnostics)
atomic_write_tsv(contrast_status, paths$contrast_status)
atomic_write_tsv(checks, paths$checks)
artifact_paths <- c(paths$results, paths$diagnostics, paths$contrast_status, paths$checks)
artifacts <- data.frame(
  schema_version = "pseudobulk_de_artifacts_v1", rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(results), nrow(diagnostics), nrow(contrast_status), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "pseudobulk_de_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = paste("pseudobulk_de", rds_id, sep = ":"),
  source_rds = source_rel,
  scientific_script = "scripts/07_run_pseudobulk_de.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/07_run_pseudobulk_de.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(rds_manifest_path),
  pseudobulk_bundle_sha256 = sha256_file(counts_path),
  contrast_manifest_sha256 = sha256_file(contrast_manifest_path),
  fine_cell_types = length(cell_types),
  manifest_rows = nrow(contrast_manifest),
  eligible_contrasts = sum(eligible_manifest),
  completed_contrasts = sum(contrast_status$terminal_status == "validated_complete"),
  ineligible_contrasts = sum(contrast_status$terminal_status == "ineligible"),
  failed_contrasts = sum(contrast_status$terminal_status == "failed"),
  result_rows = nrow(results),
  significant_fdr_005 = if (nrow(results)) sum(results$fdr_bh_within_contrast < 0.05) else 0L,
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Pseudobulk DE results: ", paths$results, "\n", sep = "")
cat("Manifest rows: ", nrow(contrast_manifest), "\n", sep = "")
cat("Eligible contrasts: ", sum(eligible_manifest), "\n", sep = "")
cat("Completed contrasts: ", sum(contrast_status$terminal_status == "validated_complete"), "\n", sep = "")
cat("Result rows: ", nrow(results), "\n", sep = "")
cat("DE status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
