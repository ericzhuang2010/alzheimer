#!/usr/bin/env Rscript

# Compare Phase 08 v2 Yu-compatible MAST calls with frozen Supplemental Table S1.

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, yu_supplement = NULL, rds_id = NULL)
  value_options <- c("--config", "--yu-supplement", "--rds-id")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/08_compare_yu_table_s1.R --config FILE ",
        "--yu-supplement XLSX [--rds-id ID]\n",
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
  if (is.null(out$yu_supplement)) {
    stop("--yu-supplement is required", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  sub(paste0("^", root, "/?"), "", path)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2(
    "sha256sum", path, stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    return(NA_character_)
  }
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
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

as_logical <- function(x) {
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

key_for <- function(cell_type, contrast, gene) {
  paste(cell_type, contrast, gene, sep = "\034")
}

safe_correlation <- function(x, y, method) {
  keep <- is.finite(x) & is.finite(y)
  x <- x[keep]
  y <- y[keep]
  if (length(x) < 2L || stats::sd(x) == 0 || stats::sd(y) == 0) {
    return(NA_real_)
  }
  suppressWarnings(stats::cor(x, y, method = method))
}

comparison_metrics <- function(yu, current, scope, group_name, group_value) {
  yu_keys <- yu$key
  current_keys <- current$key
  shared_keys <- intersect(yu_keys, current_keys)
  yi <- match(shared_keys, yu$key)
  ci <- match(shared_keys, current$key)
  yu_logfc <- yu$yu_logFC[yi]
  current_logfc <- current$current_logFC[ci]
  direction <- if (length(shared_keys)) {
    mean(sign(yu_logfc) == sign(current_logfc))
  } else {
    NA_real_
  }
  data.frame(
    schema_version = "yu_table_s1_comparison_metrics_v2",
    scope = scope,
    group = group_name,
    value = group_value,
    yu_degs = length(yu_keys),
    phase08_degs = length(current_keys),
    shared_degs = length(shared_keys),
    yu_only_degs = length(setdiff(yu_keys, current_keys)),
    phase08_only_degs = length(setdiff(current_keys, yu_keys)),
    recall = if (length(yu_keys)) length(shared_keys) / length(yu_keys) else NA_real_,
    precision = if (length(current_keys)) {
      length(shared_keys) / length(current_keys)
    } else {
      NA_real_
    },
    jaccard = if (length(union(yu_keys, current_keys))) {
      length(shared_keys) / length(union(yu_keys, current_keys))
    } else {
      NA_real_
    },
    direction_agreement = direction,
    pearson_logFC = safe_correlation(yu_logfc, current_logfc, "pearson"),
    spearman_logFC = safe_correlation(yu_logfc, current_logfc, "spearman"),
    median_abs_logFC_difference = if (length(shared_keys)) {
      stats::median(abs(yu_logfc - current_logfc), na.rm = TRUE)
    } else {
      NA_real_
    },
    max_abs_logFC_difference = if (length(shared_keys)) {
      max(abs(yu_logfc - current_logfc), na.rm = TRUE)
    } else {
      NA_real_
    },
    stringsAsFactors = FALSE
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table", "readxl")
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
analysis <- yaml::read_yaml(analysis_path)
output_root <- absolute_path(config$outputs$root, project_root)
phase08_dir <- file.path(output_root, "08_mast")
yu_path <- absolute_path(args$yu_supplement, project_root)
if (!file.exists(yu_path)) stop("Yu supplement does not exist: ", yu_path, call. = FALSE)
if (!dir.exists(phase08_dir)) stop("Phase 08 output directory is missing", call. = FALSE)

expected_yu_sha256 <- "333898a4c1b89a484b56f51164bdc2fd553a43f7938fc1db2e19b1b8a7dc1ff0"
yu_sha256 <- sha256_file(yu_path)
sheet_name <- "Table S1. DEGs"
sheets <- readxl::excel_sheets(yu_path)
if (!sheet_name %in% sheets) {
  stop("Yu workbook is missing sheet: ", sheet_name, call. = FALSE)
}
yu_raw <- suppressWarnings(as.data.frame(readxl::read_excel(
  yu_path, sheet = sheet_name
)))
required_yu <- c(
  "Symbol", "Geneid", "Celltype", "Contrast", "p_val", "avg_log2FC",
  "pct.1", "pct.2", "p_val_adj_bonferroni", "p_val_adj"
)
missing_yu <- setdiff(required_yu, names(yu_raw))
if (length(missing_yu)) {
  stop("Yu Table S1 fields missing: ", paste(missing_yu, collapse = ", "), call. = FALSE)
}

prefix <- if (is.null(args$rds_id)) NULL else tolower(args$rds_id)
select_files <- function(suffix) {
  if (!is.null(prefix)) {
    path <- file.path(phase08_dir, paste0(prefix, suffix))
    if (!file.exists(path)) stop("Required Phase 08 artifact missing: ", path, call. = FALSE)
    return(path)
  }
  files <- list.files(
    phase08_dir, pattern = paste0(gsub("[.]", "[.]", suffix), "$"),
    full.names = TRUE
  )
  if (!length(files)) stop("No Phase 08 artifacts found for ", suffix, call. = FALSE)
  sort(files)
}

result_files <- select_files(".yu_mast_de.tsv.gz")
manifest_files <- select_files(".yu_mast_contrast_manifest.tsv")
contrast_status_files <- select_files(".yu_mast_contrast_status.tsv")
scientific_status_files <- select_files(".yu_mast_de_status.tsv")

read_many <- function(paths) {
  as.data.frame(data.table::rbindlist(
    lapply(paths, data.table::fread), fill = TRUE, use.names = TRUE
  ))
}

results <- read_many(result_files)
manifests <- read_many(manifest_files)
contrast_status <- read_many(contrast_status_files)
scientific_status <- read_many(scientific_status_files)
cell_types <- sort(unique(as.character(manifests$cell_type_high_resolution)))
scope <- if (is.null(prefix)) "all_phase08_cell_types" else paste0("rds_id:", prefix)

yu <- data.frame(
  cell_type = trimws(as.character(yu_raw$Celltype)),
  contrast = trimws(as.character(yu_raw$Contrast)),
  gene = trimws(as.character(yu_raw$Symbol)),
  gene_id = as.character(yu_raw$Geneid),
  yu_p_value = as.numeric(yu_raw$p_val),
  yu_logFC = as.numeric(yu_raw$avg_log2FC),
  yu_pct_ad = as.numeric(yu_raw$pct.1),
  yu_pct_nci = as.numeric(yu_raw$pct.2),
  yu_bonferroni = as.numeric(yu_raw$p_val_adj_bonferroni),
  yu_fdr = as.numeric(yu_raw$p_val_adj),
  stringsAsFactors = FALSE
)
yu$key <- key_for(yu$cell_type, yu$contrast, yu$gene)
yu_full_unique_keys <- length(unique(yu$key))
yu <- yu[yu$cell_type %in% cell_types, , drop = FALSE]

results$paper_deg <- as_logical(results$paper_deg)
current_all <- data.frame(
  rds_id = as.character(results$rds_id),
  cell_type = as.character(results$cell_type_high_resolution),
  contrast = as.character(results$yu_contrast),
  gene = as.character(results$gene),
  current_p_value = as.numeric(results$p_value),
  current_logFC = as.numeric(results$logFC),
  current_pct_ad = as.numeric(results$pct_ad),
  current_pct_nci = as.numeric(results$pct_nci),
  current_bonferroni = as.numeric(results$p_val_adj_bonferroni),
  current_fdr = as.numeric(results$fdr_bh_within_contrast),
  current_paper_deg = results$paper_deg,
  stringsAsFactors = FALSE
)
current_all$key <- key_for(
  current_all$cell_type, current_all$contrast, current_all$gene
)
current_calls <- current_all[current_all$current_paper_deg, , drop = FALSE]

overall <- comparison_metrics(yu, current_calls, scope, "overall", "all")
by_contrast <- do.call(rbind, lapply(
  sort(unique(c(yu$contrast, manifests$yu_contrast))),
  function(value) comparison_metrics(
    yu[yu$contrast == value, , drop = FALSE],
    current_calls[current_calls$contrast == value, , drop = FALSE],
    scope, "yu_contrast", value
  )
))
by_cell_type <- do.call(rbind, lapply(cell_types, function(value) {
  comparison_metrics(
    yu[yu$cell_type == value, , drop = FALSE],
    current_calls[current_calls$cell_type == value, , drop = FALSE],
    scope, "cell_type_high_resolution", value
  )
}))

status_key <- paste(
  contrast_status$cell_type_high_resolution, contrast_status$yu_contrast,
  sep = "\034"
)
yu_only <- yu[!yu$key %in% current_calls$key, , drop = FALSE]
yu_result_index <- match(yu_only$key, current_all$key)
yu_status_index <- match(
  paste(yu_only$cell_type, yu_only$contrast, sep = "\034"), status_key
)
yu_terminal_status <- contrast_status$terminal_status[yu_status_index]
yu_current <- current_all[yu_result_index, , drop = FALSE]
alpha <- as.numeric(analysis$multiple_testing$alpha %||% 0.05)
fold_threshold <- log2(as.numeric(
  analysis$multiple_testing$yu_absolute_fold_change_threshold %||% 1.3
))
yu_reason <- rep("yu_only_call", nrow(yu_only))
not_estimable <- is.na(yu_terminal_status) |
  yu_terminal_status != "validated_complete"
yu_reason[not_estimable] <- "comparison_not_estimable"
not_returned <- !not_estimable & is.na(yu_result_index)
yu_reason[not_returned] <- "gene_not_returned"
returned <- !not_estimable & !not_returned
direction_difference <- returned &
  sign(yu_only$yu_logFC) != sign(yu_current$current_logFC)
yu_reason[direction_difference] <- "direction_difference"
same_direction <- returned & !direction_difference
fdr_pass <- yu_current$current_fdr < alpha
fold_pass <- abs(yu_current$current_logFC) > fold_threshold
yu_reason[same_direction & !fdr_pass & !fold_pass] <-
  "fails_current_fdr_and_fold_change"
yu_reason[same_direction & !fdr_pass & fold_pass] <- "fails_current_fdr"
yu_reason[same_direction & fdr_pass & !fold_pass] <- "fails_current_fold_change"

mismatch_columns <- c(
  "schema_version", "scope", "mismatch_source", "mismatch_reason",
  "rds_id", "cell_type", "contrast", "gene", "gene_id",
  "yu_p_value", "yu_logFC", "yu_pct_ad", "yu_pct_nci",
  "yu_bonferroni", "yu_fdr", "current_p_value", "current_logFC",
  "current_pct_ad", "current_pct_nci", "current_bonferroni", "current_fdr",
  "contrast_terminal_status"
)
yu_mismatches <- data.frame(
  schema_version = rep("yu_table_s1_mismatches_v2", nrow(yu_only)),
  scope = rep(scope, nrow(yu_only)),
  mismatch_source = rep("yu_only", nrow(yu_only)),
  mismatch_reason = yu_reason,
  rds_id = yu_current$rds_id,
  cell_type = yu_only$cell_type,
  contrast = yu_only$contrast,
  gene = yu_only$gene,
  gene_id = yu_only$gene_id,
  yu_p_value = yu_only$yu_p_value,
  yu_logFC = yu_only$yu_logFC,
  yu_pct_ad = yu_only$yu_pct_ad,
  yu_pct_nci = yu_only$yu_pct_nci,
  yu_bonferroni = yu_only$yu_bonferroni,
  yu_fdr = yu_only$yu_fdr,
  current_p_value = yu_current$current_p_value,
  current_logFC = yu_current$current_logFC,
  current_pct_ad = yu_current$current_pct_ad,
  current_pct_nci = yu_current$current_pct_nci,
  current_bonferroni = yu_current$current_bonferroni,
  current_fdr = yu_current$current_fdr,
  contrast_terminal_status = yu_terminal_status,
  stringsAsFactors = FALSE
)

current_only <- current_calls[!current_calls$key %in% yu$key, , drop = FALSE]
current_status_index <- match(
  paste(current_only$cell_type, current_only$contrast, sep = "\034"), status_key
)
current_mismatches <- data.frame(
  schema_version = rep("yu_table_s1_mismatches_v2", nrow(current_only)),
  scope = rep(scope, nrow(current_only)),
  mismatch_source = rep("phase08_only", nrow(current_only)),
  mismatch_reason = rep("phase08_only_call", nrow(current_only)),
  rds_id = current_only$rds_id,
  cell_type = current_only$cell_type,
  contrast = current_only$contrast,
  gene = current_only$gene,
  gene_id = rep(NA_character_, nrow(current_only)),
  yu_p_value = rep(NA_real_, nrow(current_only)),
  yu_logFC = rep(NA_real_, nrow(current_only)),
  yu_pct_ad = rep(NA_real_, nrow(current_only)),
  yu_pct_nci = rep(NA_real_, nrow(current_only)),
  yu_bonferroni = rep(NA_real_, nrow(current_only)),
  yu_fdr = rep(NA_real_, nrow(current_only)),
  current_p_value = current_only$current_p_value,
  current_logFC = current_only$current_logFC,
  current_pct_ad = current_only$current_pct_ad,
  current_pct_nci = current_only$current_pct_nci,
  current_bonferroni = current_only$current_bonferroni,
  current_fdr = current_only$current_fdr,
  contrast_terminal_status = contrast_status$terminal_status[current_status_index],
  stringsAsFactors = FALSE
)
mismatches <- rbind(
  yu_mismatches[, mismatch_columns, drop = FALSE],
  current_mismatches[, mismatch_columns, drop = FALSE]
)
mismatches <- mismatches[order(
  mismatches$cell_type, mismatches$contrast, mismatches$gene,
  mismatches$mismatch_source
), , drop = FALSE]

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "yu_table_s1_comparison_checks_v2",
    check = check,
    passed = isTRUE(passed),
    observed = as.character(observed),
    expected = as.character(expected),
    stringsAsFactors = FALSE
  )
}
add_check("yu_xlsx_sha256", identical(yu_sha256, expected_yu_sha256), yu_sha256, expected_yu_sha256)
add_check("yu_sheet_present", sheet_name %in% sheets, sheet_name, sheet_name)
add_check("yu_full_unique_deg_keys", yu_full_unique_keys == 118297L, yu_full_unique_keys, 118297L)
add_check("comparison_scope_nonempty", nrow(yu) > 0L, nrow(yu), ">0")
add_check("yu_scope_keys_unique", !anyDuplicated(yu$key), anyDuplicated(yu$key), 0L)
add_check("phase08_result_keys_unique", !anyDuplicated(current_all$key), anyDuplicated(current_all$key), 0L)
add_check(
  "manifest_six_rows_per_cell_type",
  all(table(manifests$cell_type_high_resolution) == 6L),
  paste(as.integer(table(manifests$cell_type_high_resolution)), collapse = ","),
  "6 per cell type"
)
add_check("status_rows_match_manifest", nrow(contrast_status) == nrow(manifests), nrow(contrast_status), nrow(manifests))
add_check("no_failed_contrasts", !any(contrast_status$terminal_status == "failed"), sum(contrast_status$terminal_status == "failed"), 0L)
add_check(
  "terminal_statuses_complete",
  all(contrast_status$terminal_status %in% c("validated_complete", "not_estimable")),
  paste(sort(unique(contrast_status$terminal_status)), collapse = ","),
  "validated_complete,not_estimable"
)
add_check(
  "scientific_status_validated",
  all(scientific_status$schema_version == "yu_mast_de_status_v2") &&
    all(scientific_status$validation_status == "validated_complete"),
  paste(unique(scientific_status$validation_status), collapse = ","),
  "validated_complete"
)
add_check(
  "current_probabilities_valid",
  all(is.finite(current_all$current_p_value)) &&
    all(current_all$current_p_value >= 0 & current_all$current_p_value <= 1) &&
    all(is.finite(current_all$current_fdr)) &&
    all(current_all$current_fdr >= 0 & current_all$current_fdr <= 1),
  nrow(current_all), "all p-values and FDR values finite in [0,1]"
)
recomputed_deg <- current_all$current_fdr < alpha &
  abs(current_all$current_logFC) > fold_threshold &
  (current_all$current_pct_ad >= as.numeric(analysis$models$mast$min_pct) |
     current_all$current_pct_nci >= as.numeric(analysis$models$mast$min_pct))
add_check(
  "paper_deg_rule_reproduced",
  identical(as.logical(current_all$current_paper_deg), as.logical(recomputed_deg)),
  sum(current_all$current_paper_deg != recomputed_deg), 0L
)
checks <- do.call(rbind, checks)

exact <- overall$yu_only_degs == 0L && overall$phase08_only_degs == 0L &&
  (is.na(overall$direction_agreement) || overall$direction_agreement == 1) &&
  (is.na(overall$max_abs_logFC_difference) ||
     overall$max_abs_logFC_difference <= 1e-10)
method_equivalent <- is.finite(overall$recall) && overall$recall >= 0.95 &&
  is.finite(overall$precision) && overall$precision >= 0.95 &&
  is.finite(overall$jaccard) && overall$jaccard >= 0.90 &&
  is.finite(overall$direction_agreement) && overall$direction_agreement >= 0.999 &&
  is.finite(overall$pearson_logFC) && overall$pearson_logFC >= 0.995 &&
  is.finite(overall$median_abs_logFC_difference) &&
  overall$median_abs_logFC_difference <= 0.01
alignment_tier <- if (exact) {
  "exact"
} else if (method_equivalent) {
  "method_equivalent"
} else {
  "below_target"
}
validation_status <- if (all(checks$passed)) "validated_complete" else "failed"

comparison_status <- data.frame(
  schema_version = "yu_table_s1_comparison_status_v2",
  validation_status = validation_status,
  alignment_tier = alignment_tier,
  scope = scope,
  rds_id = args$rds_id %||% "all",
  yu_supplement = relative_path(yu_path, project_root),
  yu_supplement_sha256 = yu_sha256,
  yu_sheet = sheet_name,
  fine_cell_types = length(cell_types),
  planned_comparisons = nrow(manifests),
  estimable_comparisons = sum(manifests$modeling_status == "estimable"),
  completed_comparisons = sum(contrast_status$terminal_status == "validated_complete"),
  not_estimable_comparisons = sum(contrast_status$terminal_status == "not_estimable"),
  yu_degs_in_scope = overall$yu_degs,
  phase08_degs_in_scope = overall$phase08_degs,
  shared_degs = overall$shared_degs,
  failed_checks = paste(checks$check[!checks$passed], collapse = ";"),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)

validation_dir <- file.path(phase08_dir, "yu_table_s1_validation")
paths <- list(
  summary = file.path(validation_dir, "yu_table_s1_comparison_summary.tsv"),
  contrast = file.path(validation_dir, "yu_table_s1_comparison_by_contrast.tsv"),
  cell_type = file.path(validation_dir, "yu_table_s1_comparison_by_cell_type.tsv"),
  mismatches = file.path(validation_dir, "yu_table_s1_mismatches.tsv.gz"),
  checks = file.path(validation_dir, "yu_table_s1_comparison_checks.tsv"),
  status = file.path(validation_dir, "yu_table_s1_comparison_status.tsv")
)
atomic_write_tsv(overall, paths$summary)
atomic_write_tsv(by_contrast, paths$contrast)
atomic_write_tsv(by_cell_type, paths$cell_type)
atomic_write_tsv_gz(mismatches, paths$mismatches)
atomic_write_tsv(checks, paths$checks)
atomic_write_tsv(comparison_status, paths$status)

cat("Yu comparison scope: ", scope, "\n", sep = "")
cat("Yu DEGs: ", overall$yu_degs, "\n", sep = "")
cat("Phase 08 DEGs: ", overall$phase08_degs, "\n", sep = "")
cat("Shared DEGs: ", overall$shared_degs, "\n", sep = "")
cat("Alignment tier: ", alignment_tier, "\n", sep = "")
cat("Validation status: ", validation_status, "\n", sep = "")

if (!identical(validation_status, "validated_complete")) {
  stop("Yu comparison structural validation failed", call. = FALSE)
}
