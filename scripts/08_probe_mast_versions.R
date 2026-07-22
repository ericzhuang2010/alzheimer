#!/usr/bin/env Rscript

# Probe plausible MAST releases on a small, fixed Vasculature panel while
# holding the normalized object, Seurat invocation, covariates, filters, and
# multiple-testing rule constant.

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    label = NULL, output_dir = NULL, age90_value = NULL,
    age_mode = "continuous", zlm_method = NULL, ebayes = NULL
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (!key %in% c(
      "--label", "--output-dir", "--age90-value", "--age-mode",
      "--zlm-method", "--ebayes"
    ) ||
        i == length(args)) {
      stop("Usage: Rscript scripts/08_probe_mast_versions.R ",
           "--label LABEL --output-dir DIR [--age90-value NUMBER] ",
           "[--age-mode continuous|yu_numeric|yu_raw] ",
           "[--zlm-method NAME] [--ebayes TRUE|FALSE]",
           call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$label) || is.null(out$output_dir)) {
    stop("--label and --output-dir are required", call. = FALSE)
  }
  out
}

safe_cor <- function(x, y, method = "pearson") {
  keep <- is.finite(x) & is.finite(y)
  x <- x[keep]
  y <- y[keep]
  if (length(x) < 2L || stats::sd(x) == 0 || stats::sd(y) == 0) {
    return(NA_real_)
  }
  suppressWarnings(stats::cor(x, y, method = method))
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c(
  "data.table", "RcppAnnoy", "Seurat", "SeuratObject", "MAST", "readxl"
)
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop("Missing packages: ", paste(missing, collapse = ", "), call. = FALSE)
}

suppressPackageStartupMessages({
  library(RcppAnnoy)
  library(Seurat)
  library(MAST)
})

root <- normalizePath(getwd(), mustWork = TRUE)
normalized_path <- file.path(
  root, "results/local_pilot/05_normalized/Vasculature_cells.normalized.rds"
)
yu_path <- file.path(root, "docs/yu_paper/ALZ-22-e71463-s002.xlsx")
baseline_path <- file.path(
  root, "results/local_pilot/08_mast/vasculature.yu_mast_de.tsv.gz"
)
stopifnot(
  file.exists(normalized_path),
  file.exists(yu_path),
  file.exists(baseline_path)
)

panel <- data.frame(
  cell_type = c("End", "Per", "End"),
  sex = c("Female", "Male", "Female"),
  apoe_group = c("e33", "e2", "e4"),
  yu_contrast = c(
    "F_e33_AD_vs_F_e33_NCI",
    "M_e2x_AD_vs_M_e2x_NCI",
    "F_e4x_AD_vs_F_e4x_NCI"
  ),
  stringsAsFactors = FALSE
)

message("Reading normalized object")
object <- readRDS(normalized_path)
stopifnot(inherits(object, "Seurat"), methods::validObject(object))
SeuratObject::DefaultAssay(object) <- "RNA"
metadata <- object[[]]
if (!is.null(args$age90_value)) {
  age90_value <- as.numeric(args$age90_value)
  if (!is.finite(age90_value)) {
    stop("--age90-value must be finite", call. = FALSE)
  }
  required_age_fields <- c(
    "projid", "cohort_included", "age_death_numeric", "age_90plus"
  )
  stopifnot(all(required_age_fields %in% names(metadata)))
  analytic <- metadata[metadata$cohort_included, required_age_fields, drop = FALSE]
  donor_key <- !duplicated(analytic$projid)
  donors <- analytic[donor_key, , drop = FALSE]
  stopifnot(!anyDuplicated(donors$projid))
  donor_age <- as.numeric(donors$age_death_numeric)
  donor_age[as.logical(donors$age_90plus)] <- age90_value
  donor_age_scaled <- as.numeric(scale(donor_age))
  object$age_death_scaled <- donor_age_scaled[
    match(metadata$projid, donors$projid)
  ]
  metadata <- object[[]]
  message("Re-encoded age 90+ as ", age90_value)
}
if (!args$age_mode %in% c("continuous", "yu_numeric", "yu_raw")) {
  stop(
    "--age-mode must be continuous, yu_numeric, or yu_raw",
    call. = FALSE
  )
}
if (identical(args$age_mode, "yu_raw")) {
  object$age_death_yu_raw <- ifelse(
    as.logical(metadata$age_90plus),
    "90+",
    as.character(metadata$age_death_numeric)
  )
  metadata <- object[[]]
  message("Using Yu-style raw age_death character covariate")
}

message("Reading Yu Table S1 and baseline")
yu_raw <- suppressWarnings(as.data.frame(readxl::read_excel(
  yu_path, sheet = "Table S1. DEGs"
)))
yu <- data.frame(
  cell_type = trimws(as.character(yu_raw$Celltype)),
  yu_contrast = trimws(as.character(yu_raw$Contrast)),
  gene = trimws(as.character(yu_raw$Symbol)),
  yu_p_value = as.numeric(yu_raw$p_val),
  yu_fdr = as.numeric(yu_raw$p_val_adj),
  yu_logFC = as.numeric(yu_raw$avg_log2FC),
  stringsAsFactors = FALSE
)
baseline <- as.data.frame(data.table::fread(baseline_path))

pair_rows <- list()
call_rows <- list()
summary_rows <- list()
latent_vars <- if (identical(args$age_mode, "yu_raw")) {
  c("nCount_RNA", "pmi_scaled", "age_death_yu_raw")
} else if (identical(args$age_mode, "yu_numeric")) {
  c("nCount_RNA", "pmi_numeric", "age_death_numeric")
} else {
  c("nCount_RNA", "age_death_scaled", "pmi_scaled")
}
effect_threshold <- log2(1.3)

for (i in seq_len(nrow(panel))) {
  probe <- panel[i, , drop = FALSE]
  mask <- metadata$cohort_included &
    metadata$cell_type_high_resolution == probe$cell_type &
    metadata$sex == probe$sex &
    metadata$apoe_group == probe$apoe_group &
    metadata$diagnosis %in% c("AD", "NCI")
  mask[is.na(mask)] <- FALSE
  selected_cells <- rownames(metadata)[mask]
  message(
    "Running ", probe$cell_type, " / ", probe$yu_contrast,
    " with ", length(selected_cells), " cells"
  )

  subobject <- object[, selected_cells, drop = FALSE]
  SeuratObject::DefaultAssay(subobject) <- "RNA"
  find_args <- list(
    object = subobject,
    ident.1 = "AD",
    ident.2 = "NCI",
    group.by = "diagnosis",
    assay = "RNA",
    slot = "data",
    test.use = "MAST",
    min.pct = 0.10,
    min.cells.group = 3,
    logfc.threshold = 0,
    latent.vars = latent_vars,
    densify = FALSE,
    verbose = FALSE
  )
  if (!is.null(args$zlm_method)) {
    find_args$method <- args$zlm_method
  }
  if (!is.null(args$ebayes)) {
    ebayes <- toupper(args$ebayes)
    if (!ebayes %in% c("TRUE", "FALSE")) {
      stop("--ebayes must be TRUE or FALSE", call. = FALSE)
    }
    find_args$ebayes <- identical(ebayes, "TRUE")
  }
  markers <- do.call(Seurat::FindMarkers, find_args)
  rm(subobject)
  invisible(gc())

  logfc_column <- intersect(c("avg_log2FC", "avg_logFC"), names(markers))
  stopifnot(length(logfc_column) == 1L)
  current <- data.frame(
    cell_type = probe$cell_type,
    yu_contrast = probe$yu_contrast,
    gene = rownames(markers),
    current_p_value = as.numeric(markers$p_val),
    current_fdr = stats::p.adjust(as.numeric(markers$p_val), method = "BH"),
    current_logFC = as.numeric(markers[[logfc_column]]),
    pct_ad = as.numeric(markers$pct.1),
    pct_nci = as.numeric(markers$pct.2),
    stringsAsFactors = FALSE
  )
  current$current_call <- current$current_fdr < 0.05 &
    abs(current$current_logFC) > effect_threshold &
    (current$pct_ad >= 0.10 | current$pct_nci >= 0.10)

  yu_subset <- yu[
    yu$cell_type == probe$cell_type &
      yu$yu_contrast == probe$yu_contrast,
    , drop = FALSE
  ]
  pair_index <- match(yu_subset$gene, current$gene)
  stopifnot(!anyNA(pair_index))
  pairs <- cbind(
    yu_subset,
    current[pair_index, c(
      "current_p_value", "current_fdr", "current_logFC", "current_call"
    ), drop = FALSE]
  )
  pairs$label <- args$label
  pairs$abs_p_difference <- abs(pairs$current_p_value - pairs$yu_p_value)
  pairs$abs_fdr_difference <- abs(pairs$current_fdr - pairs$yu_fdr)
  pairs$p_ratio <- ifelse(
    pairs$yu_p_value > 0,
    pairs$current_p_value / pairs$yu_p_value,
    NA_real_
  )
  pair_rows[[length(pair_rows) + 1L]] <- pairs

  baseline_subset <- baseline[
    baseline$cell_type_high_resolution == probe$cell_type &
      baseline$yu_contrast == probe$yu_contrast,
    , drop = FALSE
  ]
  baseline_index <- match(current$gene, baseline_subset$gene)
  comparable <- !is.na(baseline_index)
  baseline_p <- rep(NA_real_, nrow(current))
  baseline_p[comparable] <- baseline_subset$p_value[baseline_index[comparable]]
  current$baseline_p_value <- baseline_p
  current$abs_p_difference_from_baseline <- abs(
    current$current_p_value - current$baseline_p_value
  )
  current$label <- args$label
  call_rows[[length(call_rows) + 1L]] <- current

  yu_calls <- yu_subset$gene
  current_calls <- current$gene[current$current_call]
  shared_calls <- intersect(yu_calls, current_calls)
  finite_ratio <- is.finite(pairs$p_ratio)
  finite_log <- pairs$yu_p_value > 0 & pairs$current_p_value > 0
  summary_rows[[length(summary_rows) + 1L]] <- data.frame(
    label = args$label,
    cell_type = probe$cell_type,
    yu_contrast = probe$yu_contrast,
    cells = length(selected_cells),
    tested_genes = nrow(current),
    yu_degs = length(yu_calls),
    current_degs = length(current_calls),
    shared_degs = length(shared_calls),
    recall = length(shared_calls) / length(yu_calls),
    precision = if (length(current_calls)) {
      length(shared_calls) / length(current_calls)
    } else {
      NA_real_
    },
    median_abs_p_difference = stats::median(pairs$abs_p_difference),
    median_abs_fdr_difference = stats::median(pairs$abs_fdr_difference),
    median_current_to_yu_p_ratio = stats::median(
      pairs$p_ratio[finite_ratio], na.rm = TRUE
    ),
    fraction_current_p_larger = mean(
      pairs$current_p_value > pairs$yu_p_value
    ),
    spearman_p = safe_cor(
      pairs$current_p_value, pairs$yu_p_value, "spearman"
    ),
    pearson_neg_log10_p = safe_cor(
      -log10(pairs$current_p_value[finite_log]),
      -log10(pairs$yu_p_value[finite_log]),
      "pearson"
    ),
    genes_compared_to_baseline = sum(comparable),
    median_abs_p_difference_from_baseline = stats::median(
      current$abs_p_difference_from_baseline[comparable], na.rm = TRUE
    ),
    max_abs_p_difference_from_baseline = max(
      current$abs_p_difference_from_baseline[comparable], na.rm = TRUE
    ),
    stringsAsFactors = FALSE
  )
}

pairs <- do.call(rbind, pair_rows)
calls <- do.call(rbind, call_rows)
summary <- do.call(rbind, summary_rows)

yu_key <- paste(pairs$cell_type, pairs$yu_contrast, pairs$gene, sep = "\034")
current_called <- calls[calls$current_call, , drop = FALSE]
current_key <- paste(
  current_called$cell_type, current_called$yu_contrast, current_called$gene,
  sep = "\034"
)
finite_ratio <- is.finite(pairs$p_ratio)
finite_log <- pairs$yu_p_value > 0 & pairs$current_p_value > 0
overall <- data.frame(
  label = args$label,
  r_version = R.version.string,
  seurat_version = as.character(utils::packageVersion("Seurat")),
  seuratobject_version = as.character(utils::packageVersion("SeuratObject")),
  mast_version = as.character(utils::packageVersion("MAST")),
  matrix_version = as.character(utils::packageVersion("Matrix")),
  age90_value = if (is.null(args$age90_value)) {
    "stored_phase05"
  } else {
    as.character(args$age90_value)
  },
  age_mode = args$age_mode,
  zlm_method = args$zlm_method %||% "bayesglm_default",
  ebayes = args$ebayes %||% "TRUE_default",
  panel_comparisons = nrow(panel),
  tested_genes = nrow(calls),
  yu_degs = length(yu_key),
  current_degs = length(current_key),
  shared_degs = length(intersect(yu_key, current_key)),
  recall = length(intersect(yu_key, current_key)) / length(yu_key),
  precision = length(intersect(yu_key, current_key)) / length(current_key),
  median_abs_p_difference = stats::median(pairs$abs_p_difference),
  median_abs_fdr_difference = stats::median(pairs$abs_fdr_difference),
  median_current_to_yu_p_ratio = stats::median(
    pairs$p_ratio[finite_ratio], na.rm = TRUE
  ),
  fraction_current_p_larger = mean(pairs$current_p_value > pairs$yu_p_value),
  spearman_p = safe_cor(pairs$current_p_value, pairs$yu_p_value, "spearman"),
  pearson_neg_log10_p = safe_cor(
    -log10(pairs$current_p_value[finite_log]),
    -log10(pairs$yu_p_value[finite_log]),
    "pearson"
  ),
  median_abs_p_difference_from_baseline = stats::median(
    calls$abs_p_difference_from_baseline, na.rm = TRUE
  ),
  max_abs_p_difference_from_baseline = max(
    calls$abs_p_difference_from_baseline, na.rm = TRUE
  ),
  stringsAsFactors = FALSE
)

output_dir <- if (grepl("^/", args$output_dir)) {
  args$output_dir
} else {
  file.path(root, args$output_dir)
}
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
data.table::fwrite(
  pairs, file.path(output_dir, paste0(args$label, "_yu_pairs.tsv")),
  sep = "\t", quote = FALSE, na = "NA"
)
data.table::fwrite(
  calls, file.path(output_dir, paste0(args$label, "_all_tested.tsv")),
  sep = "\t", quote = FALSE, na = "NA"
)
data.table::fwrite(
  summary, file.path(output_dir, paste0(args$label, "_by_comparison.tsv")),
  sep = "\t", quote = FALSE, na = "NA"
)
data.table::fwrite(
  overall, file.path(output_dir, paste0(args$label, "_overall.tsv")),
  sep = "\t", quote = FALSE, na = "NA"
)

print(overall)
