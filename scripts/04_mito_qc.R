#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = "qc"
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
        "Usage: Rscript scripts/04_mito_qc.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--task-mode qc]\n",
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
  if (is.null(out$manifest_row) == is.null(out$rds_id)) {
    stop("Specify exactly one of --manifest-row or --rds-id", call. = FALSE)
  }
  if (!identical(out$task_mode, "qc")) {
    stop("--task-mode must be 'qc'", call. = FALSE)
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
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  connection <- gzfile(tmp, open = "wt")
  on.exit(close(connection), add = TRUE)
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
  status_path <- "/proc/self/status"
  if (!file.exists(status_path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(status_path, warn = FALSE), value = TRUE)
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

normalize_id <- function(x, width) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "NaN")] <- NA_character_
  valid <- !is.na(x)
  x[valid] <- vapply(
    x[valid],
    function(value) {
      if (grepl("^[0-9]+$", value) && nchar(value) < width) {
        paste0(strrep("0", width - nchar(value)), value)
      } else {
        value
      }
    },
    character(1)
  )
  x
}

get_assay_layer <- function(object, assay, layer) {
  tryCatch(
    SeuratObject::LayerData(object, assay = assay, layer = layer),
    error = function(e) {
      tryCatch(
        SeuratObject::GetAssayData(object, assay = assay, slot = layer),
        error = function(e2) NULL
      )
    }
  )
}

finite_quantile <- function(x, probability) {
  x <- x[is.finite(x)]
  if (!length(x)) return(NA_real_)
  as.numeric(stats::quantile(x, probability, names = FALSE, type = 7))
}

robust_limits <- function(x, threshold, two_sided = TRUE) {
  values <- x[is.finite(x)]
  if (!length(values)) return(c(low = -Inf, high = Inf, median = NA_real_, mad = NA_real_))
  center <- stats::median(values)
  spread <- stats::mad(values, center = center, constant = 1.4826)
  if (!is.finite(spread) || spread <= 0) {
    return(c(low = -Inf, high = Inf, median = center, mad = spread))
  }
  c(
    low = if (two_sided) center - threshold * spread else -Inf,
    high = center + threshold * spread,
    median = center,
    mad = spread
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c(
  "yaml", "Matrix", "RcppAnnoy", "Seurat", "SeuratObject", "data.table"
)
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

# This load order is required on Minerva and is shared by both execution stages.
suppressPackageStartupMessages({
  library(RcppAnnoy)
  library(Seurat)
})

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
if (!file.exists(analysis_path)) stop("Analysis config does not exist", call. = FALSE)
if (!file.exists(manifest_path)) stop("Manifest does not exist", call. = FALSE)

analysis <- yaml::read_yaml(analysis_path)
manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
if (!is.null(args$manifest_row)) {
  selected <- manifest[manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
} else {
  selected <- manifest[manifest$rds_id == args$rds_id, , drop = FALSE]
}
if (nrow(selected) != 1L) stop("Manifest selection must identify exactly one row", call. = FALSE)
if (!toupper(as.character(selected$enabled[[1L]])) %in% c("TRUE", "T", "1", "YES")) {
  stop("Selected manifest row is disabled", call. = FALSE)
}

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
source_path <- absolute_path(source_rel, project_root)
if (!file.exists(source_path)) stop("Input RDS does not exist: ", source_path, call. = FALSE)
source_sha_before <- sha256_file(source_path)

intersections_path <- file.path(output_root, "02_cohort", "cohort_rds_intersections.tsv")
if (!file.exists(intersections_path)) {
  stop("Required cohort intersection manifest is missing: ", intersections_path, call. = FALSE)
}
intersections <- data.table::fread(intersections_path, data.table = FALSE)
intersection <- intersections[intersections$rds_id == rds_id, , drop = FALSE]
if (nrow(intersection) != 1L) {
  stop("Cohort intersection selection must identify exactly one row for ", rds_id, call. = FALSE)
}
cohort_path <- absolute_path(as.character(intersection$output_file[[1L]]), project_root)
if (!file.exists(cohort_path)) stop("Required RDS cohort is missing: ", cohort_path, call. = FALSE)
cohort <- data.table::fread(cohort_path, colClasses = c(projid = "character"), data.table = FALSE)
required_cohort <- c("projid", "diagnosis", "sex", "apoe_group")
missing_cohort <- setdiff(required_cohort, names(cohort))
if (length(missing_cohort)) {
  stop("Cohort fields missing: ", paste(missing_cohort, collapse = ", "), call. = FALSE)
}
projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
cohort$projid <- normalize_id(cohort$projid, projid_width)
if (anyNA(cohort$projid) || anyDuplicated(cohort$projid)) {
  stop("Cohort projid values must be complete and unique", call. = FALSE)
}

annotation_dir <- file.path(output_root, "03_annotations")
mt_path <- file.path(annotation_dir, "mtDNA_protein_genes.tsv")
mitocarta_path <- file.path(annotation_dir, "mitocarta_measured_genes.tsv")
for (path in c(mt_path, mitocarta_path)) {
  if (!file.exists(path)) stop("Required annotation is missing: ", path, call. = FALSE)
}
mt_annotation <- data.table::fread(mt_path, data.table = FALSE)
mitocarta_annotation <- data.table::fread(mitocarta_path, data.table = FALSE)
mt_annotation <- mt_annotation[mt_annotation$rds_id == rds_id, , drop = FALSE]
mitocarta_annotation <- mitocarta_annotation[
  mitocarta_annotation$rds_id == rds_id & mitocarta_annotation$measured,
  , drop = FALSE
]
if (!nrow(mt_annotation)) stop("No mtDNA annotations found for ", rds_id, call. = FALSE)
if (!nrow(mitocarta_annotation)) stop("No measured MitoCarta annotations found for ", rds_id, call. = FALSE)

message("Reading Seurat object: ", source_path)
object <- readRDS(source_path)
if (!inherits(object, "Seurat")) stop("Input is not a Seurat object", call. = FALSE)
assay <- analysis$normalization$assay %||% "RNA"
if (!assay %in% SeuratObject::Assays(object)) {
  stop("Required assay is absent: ", assay, call. = FALSE)
}
counts <- get_assay_layer(object, assay, "counts")
if (is.null(counts)) stop("Raw counts layer is absent from assay ", assay, call. = FALSE)

cells <- colnames(counts)
features <- rownames(counts)
metadata <- object[[]]
if (!identical(rownames(metadata), cells)) {
  metadata <- metadata[match(cells, rownames(metadata)), , drop = FALSE]
}
if (!all(c("projid", "cell_type_high_resolution") %in% names(metadata))) {
  stop("Object metadata lacks projid or cell_type_high_resolution", call. = FALSE)
}
projid <- normalize_id(metadata$projid, projid_width)
cell_type <- trimws(as.character(metadata$cell_type_high_resolution))
cell_type[cell_type == ""] <- NA_character_
if (anyNA(projid) || anyNA(cell_type)) {
  stop("Object projid and cell type metadata must be complete", call. = FALSE)
}

is_sparse <- inherits(counts, "sparseMatrix")
count_values <- if (is_sparse && "x" %in% slotNames(counts)) counts@x else counts[]
counts_finite <- all(is.finite(count_values))
counts_nonnegative <- counts_finite && all(count_values >= 0)
counts_integer <- counts_finite && all(abs(count_values - round(count_values)) < 1e-8)
n_count_rna <- if (is_sparse) Matrix::colSums(counts) else colSums(counts)
n_feature_rna <- if (inherits(counts, "dgCMatrix")) {
  diff(counts@p)
} else if (is_sparse) {
  Matrix::colSums(counts != 0)
} else {
  colSums(counts != 0)
}

expected_mt <- unlist(analysis$mitochondrial_features$mtdna_protein_genes, use.names = FALSE)
mt_features <- intersect(expected_mt, features)
mt_index <- match(mt_features, features)
n_count_mt <- as.numeric(Matrix::colSums(counts[mt_index, , drop = FALSE]))
n_feature_mt <- as.numeric(Matrix::colSums(counts[mt_index, , drop = FALSE] != 0))

mapped_fields <- as.character(mitocarta_annotation$mapped_feature)
mitocarta_features <- unique(unlist(strsplit(mapped_fields, ";", fixed = TRUE), use.names = FALSE))
mitocarta_features <- intersect(mitocarta_features[nzchar(mitocarta_features)], features)
mitocarta_index <- match(mitocarta_features, features)
n_count_mitocarta <- as.numeric(Matrix::colSums(counts[mitocarta_index, , drop = FALSE]))

percent_mt <- ifelse(n_count_rna > 0, 100 * n_count_mt / n_count_rna, NA_real_)
percent_mitocarta <- ifelse(n_count_rna > 0, 100 * n_count_mitocarta / n_count_rna, NA_real_)
cohort_index <- match(projid, cohort$projid)
cohort_included <- !is.na(cohort_index)

cell_qc <- data.table::data.table(
  schema_version = "mito_cell_qc_v1",
  rds_id = rds_id,
  source_rds = source_rel,
  barcode = cells,
  projid = projid,
  cell_type_high_resolution = cell_type,
  cohort_included = cohort_included,
  diagnosis = cohort$diagnosis[cohort_index],
  sex = cohort$sex[cohort_index],
  apoe_group = cohort$apoe_group[cohort_index],
  nCount_RNA = as.numeric(n_count_rna),
  nFeature_RNA = as.numeric(n_feature_rna),
  nCount_MT = n_count_mt,
  percent_mt = percent_mt,
  nFeature_MT = n_feature_mt,
  nCount_MitoCarta = n_count_mitocarta,
  percent_mitocarta = percent_mitocarta
)

mad_threshold <- as.numeric(analysis$quality_control$robust_mad_threshold %||% 5)
if (!is.finite(mad_threshold) || mad_threshold <= 0) {
  stop("quality_control.robust_mad_threshold must be positive", call. = FALSE)
}
cell_qc[, `:=`(
  flag_low_nCount_RNA = FALSE,
  flag_high_nCount_RNA = FALSE,
  flag_low_nFeature_RNA = FALSE,
  flag_high_nFeature_RNA = FALSE,
  flag_high_percent_mt = FALSE,
  flag_high_percent_mitocarta = FALSE
)]

threshold_rows <- list()
for (current_cell_type in sort(unique(cell_qc$cell_type_high_resolution))) {
  index <- which(cell_qc$cell_type_high_resolution == current_cell_type)
  count_limits <- robust_limits(log1p(cell_qc$nCount_RNA[index]), mad_threshold, TRUE)
  feature_limits <- robust_limits(log1p(cell_qc$nFeature_RNA[index]), mad_threshold, TRUE)
  mt_limits <- robust_limits(cell_qc$percent_mt[index], mad_threshold, FALSE)
  mc_limits <- robust_limits(cell_qc$percent_mitocarta[index], mad_threshold, FALSE)
  cell_qc$flag_low_nCount_RNA[index] <- log1p(cell_qc$nCount_RNA[index]) < count_limits[["low"]]
  cell_qc$flag_high_nCount_RNA[index] <- log1p(cell_qc$nCount_RNA[index]) > count_limits[["high"]]
  cell_qc$flag_low_nFeature_RNA[index] <- log1p(cell_qc$nFeature_RNA[index]) < feature_limits[["low"]]
  cell_qc$flag_high_nFeature_RNA[index] <- log1p(cell_qc$nFeature_RNA[index]) > feature_limits[["high"]]
  cell_qc$flag_high_percent_mt[index] <- cell_qc$percent_mt[index] > mt_limits[["high"]]
  cell_qc$flag_high_percent_mitocarta[index] <- cell_qc$percent_mitocarta[index] > mc_limits[["high"]]
  threshold_rows[[length(threshold_rows) + 1L]] <- data.frame(
    schema_version = "mito_qc_thresholds_v1",
    rds_id = rds_id,
    cell_type_high_resolution = current_cell_type,
    nuclei = length(index),
    mad_threshold = mad_threshold,
    log1p_nCount_RNA_median = count_limits[["median"]],
    log1p_nCount_RNA_mad = count_limits[["mad"]],
    log1p_nFeature_RNA_median = feature_limits[["median"]],
    log1p_nFeature_RNA_mad = feature_limits[["mad"]],
    percent_mt_median = mt_limits[["median"]],
    percent_mt_mad = mt_limits[["mad"]],
    percent_mitocarta_median = mc_limits[["median"]],
    percent_mitocarta_mad = mc_limits[["mad"]],
    stringsAsFactors = FALSE
  )
}
threshold_table <- do.call(rbind, threshold_rows)
flag_columns <- c(
  "flag_low_nCount_RNA", "flag_high_nCount_RNA",
  "flag_low_nFeature_RNA", "flag_high_nFeature_RNA",
  "flag_high_percent_mt", "flag_high_percent_mitocarta"
)
cell_qc[, flag_zero_mt := nCount_MT == 0]
cell_qc[, robust_any_flag := Reduce(`|`, .SD), .SDcols = flag_columns]
cell_qc[, flag_reasons := apply(.SD, 1L, function(values) {
  reasons <- c(flag_columns, "flag_zero_mt")[as.logical(values)]
  paste(reasons, collapse = ";")
}), .SDcols = c(flag_columns, "flag_zero_mt")]

analytic <- cell_qc[cohort_included == TRUE]
if (!nrow(analytic)) stop("No nuclei intersect the analytic cohort", call. = FALSE)

donor_summary <- analytic[, .(
  nuclei = .N,
  total_rna_counts = sum(nCount_RNA),
  total_mt_counts = sum(nCount_MT),
  aggregate_percent_mt = 100 * sum(nCount_MT) / sum(nCount_RNA),
  median_percent_mt = stats::median(percent_mt),
  q25_percent_mt = finite_quantile(percent_mt, 0.25),
  q75_percent_mt = finite_quantile(percent_mt, 0.75),
  median_detected_mt_genes = stats::median(nFeature_MT),
  total_mitocarta_counts = sum(nCount_MitoCarta),
  aggregate_percent_mitocarta = 100 * sum(nCount_MitoCarta) / sum(nCount_RNA),
  median_percent_mitocarta = stats::median(percent_mitocarta),
  zero_mt_nuclei = sum(nCount_MT == 0),
  zero_mt_fraction = mean(nCount_MT == 0),
  robust_flagged_nuclei = sum(robust_any_flag),
  robust_flagged_fraction = mean(robust_any_flag)
), by = .(rds_id, projid, cell_type_high_resolution, diagnosis, sex, apoe_group)]
donor_summary[, schema_version := "mito_donor_celltype_qc_v1"]
data.table::setcolorder(donor_summary, c(
  "schema_version", "rds_id", "projid", "cell_type_high_resolution",
  "diagnosis", "sex", "apoe_group", setdiff(names(donor_summary), c(
    "schema_version", "rds_id", "projid", "cell_type_high_resolution",
    "diagnosis", "sex", "apoe_group"
  ))
))

sex_levels <- unlist(analysis$contrasts$sex_levels, use.names = FALSE)
apoe_levels <- unlist(analysis$contrasts$apoe_levels, use.names = FALSE)
diagnosis_levels <- c(analysis$contrasts$denominator, analysis$contrasts$numerator)
group_grid <- data.table::CJ(
  cell_type_high_resolution = sort(unique(cell_qc$cell_type_high_resolution)),
  sex = sex_levels,
  apoe_group = apoe_levels,
  diagnosis = diagnosis_levels,
  unique = TRUE
)
observed_groups <- analytic[, .(
  nuclei = .N,
  donors = data.table::uniqueN(projid),
  zero_mt_nuclei = sum(nCount_MT == 0),
  zero_mt_fraction = mean(nCount_MT == 0),
  median_percent_mt = stats::median(percent_mt),
  q25_percent_mt = finite_quantile(percent_mt, 0.25),
  q75_percent_mt = finite_quantile(percent_mt, 0.75),
  median_percent_mitocarta = stats::median(percent_mitocarta),
  robust_flagged_nuclei = sum(robust_any_flag),
  robust_flagged_fraction = mean(robust_any_flag)
), by = .(cell_type_high_resolution, sex, apoe_group, diagnosis)]
group_summary <- merge(
  group_grid, observed_groups,
  by = c("cell_type_high_resolution", "sex", "apoe_group", "diagnosis"),
  all.x = TRUE, sort = TRUE
)
zero_columns <- c("nuclei", "donors", "zero_mt_nuclei", "robust_flagged_nuclei")
for (column in zero_columns) group_summary[[column]][is.na(group_summary[[column]])] <- 0L
group_summary$group_has_nuclei <- group_summary$nuclei > 0L
group_summary$schema_version <- "mito_group_missingness_v1"
group_summary$rds_id <- rds_id
data.table::setcolorder(group_summary, c(
  "schema_version", "rds_id", "cell_type_high_resolution", "sex",
  "apoe_group", "diagnosis", setdiff(names(group_summary), c(
    "schema_version", "rds_id", "cell_type_high_resolution", "sex",
    "apoe_group", "diagnosis"
  ))
))

donor_contributions <- donor_summary[, .(
  projid, cell_type_high_resolution, nuclei, total_mt_counts
)]
concentration_rows <- lapply(
  split(donor_contributions, donor_contributions$cell_type_high_resolution),
  function(table) {
    table <- table[order(table$total_mt_counts, decreasing = TRUE), , drop = FALSE]
    total_mt <- sum(table$total_mt_counts)
    total_nuclei <- sum(table$nuclei)
    data.frame(
      schema_version = "mito_donor_concentration_v1",
      rds_id = rds_id,
      cell_type_high_resolution = table$cell_type_high_resolution[[1L]],
      donors = nrow(table),
      nuclei = total_nuclei,
      total_mt_counts = total_mt,
      top_mt_donor = table$projid[[1L]],
      top1_mt_count_fraction = if (total_mt > 0) table$total_mt_counts[[1L]] / total_mt else NA_real_,
      top3_mt_count_fraction = if (total_mt > 0) sum(utils::head(table$total_mt_counts, 3L)) / total_mt else NA_real_,
      top1_nuclei_fraction = if (total_nuclei > 0) max(table$nuclei) / total_nuclei else NA_real_,
      stringsAsFactors = FALSE
    )
  }
)
donor_concentration <- do.call(rbind, concentration_rows)
top1_warning <- as.numeric(
  analysis$quality_control$donor_dominance_top1_fraction_warning %||% 0.25
)
top3_warning <- as.numeric(
  analysis$quality_control$donor_dominance_top3_fraction_warning %||% 0.50
)
donor_concentration$top1_warning <- donor_concentration$top1_mt_count_fraction > top1_warning
donor_concentration$top3_warning <- donor_concentration$top3_mt_count_fraction > top3_warning

qc_dir <- file.path(output_root, "04_qc")
dir.create(qc_dir, recursive = TRUE, showWarnings = FALSE)
prefix <- tolower(rds_id)
paths <- list(
  cell = file.path(qc_dir, paste0(prefix, "_cell_qc.tsv.gz")),
  donor = file.path(qc_dir, paste0(prefix, "_donor_celltype_qc.tsv")),
  flags = file.path(qc_dir, paste0(prefix, "_qc_flags.tsv.gz")),
  groups = file.path(qc_dir, paste0(prefix, "_group_missingness.tsv")),
  concentration = file.path(qc_dir, paste0(prefix, "_donor_concentration.tsv")),
  thresholds = file.path(qc_dir, paste0(prefix, "_qc_thresholds.tsv")),
  figure = file.path(qc_dir, paste0(prefix, "_qc_distributions.pdf")),
  checks = file.path(qc_dir, paste0(prefix, "_qc_checks.tsv")),
  manifest = file.path(qc_dir, paste0(prefix, "_qc_manifest.tsv")),
  status = file.path(qc_dir, paste0(prefix, "_qc_status.tsv"))
)

atomic_write_tsv_gz(as.data.frame(cell_qc), paths$cell)
flag_output <- cell_qc[, c(
  "schema_version", "rds_id", "barcode", "projid", "cell_type_high_resolution",
  "cohort_included", flag_columns, "flag_zero_mt", "robust_any_flag", "flag_reasons"
), with = FALSE]
flag_output$schema_version <- "mito_qc_flags_v1"
atomic_write_tsv_gz(as.data.frame(flag_output), paths$flags)
atomic_write_tsv(as.data.frame(donor_summary), paths$donor)
atomic_write_tsv(as.data.frame(group_summary), paths$groups)
atomic_write_tsv(donor_concentration, paths$concentration)
atomic_write_tsv(threshold_table, paths$thresholds)

figure_tmp <- paste0(paths$figure, ".tmp.", Sys.getpid())
grDevices::pdf(figure_tmp, width = 10, height = 7)
graphics::hist(
  analytic$percent_mt, breaks = 50, col = "grey70", border = "white",
  main = paste(rds_id, "analytic-cohort percent.mt"), xlab = "percent.mt"
)
graphics::boxplot(
  percent_mt ~ cell_type_high_resolution, data = analytic,
  las = 2, col = "grey85", main = "percent.mt by fine cell type", ylab = "percent.mt"
)
graphics::hist(
  analytic$percent_mitocarta, breaks = 50, col = "steelblue2", border = "white",
  main = paste(rds_id, "analytic-cohort MitoCarta fraction"),
  xlab = "MitoCarta UMI fraction (%)"
)
flag_rate <- analytic[, .(flagged_fraction = mean(robust_any_flag)),
  by = cell_type_high_resolution
]
graphics::barplot(
  flag_rate$flagged_fraction,
  names.arg = flag_rate$cell_type_high_resolution,
  las = 2, col = "tomato2", ylim = c(0, max(0.01, flag_rate$flagged_fraction)),
  main = "Robust QC flag fraction", ylab = "Fraction"
)
grDevices::dev.off()
if (!file.rename(figure_tmp, paths$figure)) {
  stop("Could not atomically write ", paths$figure, call. = FALSE)
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "mito_qc_checks_v1",
    rds_id = rds_id,
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}
add_check("source_feature_count", nrow(counts) == selected$expected_features[[1L]], nrow(counts), selected$expected_features[[1L]])
add_check("source_nucleus_count", ncol(counts) == selected$expected_cells[[1L]], ncol(counts), selected$expected_cells[[1L]])
add_check("counts_finite", counts_finite, counts_finite, TRUE)
add_check("counts_nonnegative", counts_nonnegative, counts_nonnegative, TRUE)
add_check("counts_integer", counts_integer, counts_integer, TRUE)
add_check("all_expected_mtdna_features", identical(sort(mt_features), sort(expected_mt)), mt_features, expected_mt)
add_check("all_mtdna_annotations_measured", all(mt_annotation$measured), sum(mt_annotation$measured), nrow(mt_annotation))
add_check("cell_output_complete", nrow(cell_qc) == ncol(counts) && !anyDuplicated(cell_qc$barcode), nrow(cell_qc), ncol(counts))
add_check("analytic_cohort_donor_count", data.table::uniqueN(analytic$projid) == nrow(cohort), data.table::uniqueN(analytic$projid), nrow(cohort))
add_check("analytic_cells_present", nrow(analytic) > 0L, nrow(analytic), ">0")
add_check("mt_counts_nonnegative", all(analytic$nCount_MT >= 0), min(analytic$nCount_MT), ">=0")
add_check("percent_mt_finite", all(is.finite(analytic$percent_mt)), sum(is.finite(analytic$percent_mt)), nrow(analytic))
add_check("percent_mt_range", all(analytic$percent_mt >= 0 & analytic$percent_mt <= 100), range(analytic$percent_mt), "0..100")
add_check("percent_mitocarta_finite", all(is.finite(analytic$percent_mitocarta)), sum(is.finite(analytic$percent_mitocarta)), nrow(analytic))
add_check("percent_mitocarta_range", all(analytic$percent_mitocarta >= 0 & analytic$percent_mitocarta <= 100), range(analytic$percent_mitocarta), "0..100")
add_check("mtdna_signal_not_all_zero", any(analytic$nCount_MT > 0), sum(analytic$nCount_MT), ">0")
add_check("donor_summary_cell_conservation", sum(donor_summary$nuclei) == nrow(analytic), sum(donor_summary$nuclei), nrow(analytic))
add_check("all_study_groups_reported", nrow(group_summary) == length(unique(cell_type)) * length(sex_levels) * length(apoe_levels) * length(diagnosis_levels), nrow(group_summary), length(unique(cell_type)) * 12L)
add_check("donor_concentration_reported", nrow(donor_concentration) == length(unique(cell_type)), nrow(donor_concentration), length(unique(cell_type)))
source_sha_after <- sha256_file(source_path)
add_check("source_rds_unchanged", identical(source_sha_before, source_sha_after), source_sha_after, source_sha_before)
check_table <- do.call(rbind, checks)
failed_checks <- check_table$check[!check_table$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"
atomic_write_tsv(check_table, paths$checks)

artifact_paths <- c(
  paths$cell, paths$donor, paths$flags, paths$groups,
  paths$concentration, paths$thresholds, paths$figure, paths$checks
)
artifact_records <- c(
  nrow(cell_qc), nrow(donor_summary), nrow(flag_output), nrow(group_summary),
  nrow(donor_concentration), nrow(threshold_table), NA_integer_, nrow(check_table)
)
qc_manifest <- data.frame(
  schema_version = "mito_qc_manifest_v1",
  rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = artifact_records,
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(qc_manifest, paths$manifest)

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) "local_pilot_manual" else "manual_qc"
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) stop("Execution config does not exist", call. = FALSE)
  execution <- yaml::read_yaml(execution_path)$execution
  execution_phase <- execution$execution_phase %||% execution_phase
  backend <- execution$backend %||% backend
  run_id <- execution$run_id %||% run_id
}
status <- data.frame(
  schema_version = "mito_qc_status_v1",
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = paste("qc", rds_id, sep = ":"),
  source_rds = source_rel,
  source_rds_sha256 = source_sha_before,
  scientific_script = "scripts/04_mito_qc.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/04_mito_qc.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  cohort_sha256 = sha256_file(cohort_path),
  mt_annotation_sha256 = sha256_file(mt_path),
  mitocarta_annotation_sha256 = sha256_file(mitocarta_path),
  source_nuclei = ncol(counts),
  analytic_nuclei = nrow(analytic),
  analytic_donors = data.table::uniqueN(analytic$projid),
  fine_cell_types = data.table::uniqueN(analytic$cell_type_high_resolution),
  robust_flagged_nuclei = sum(analytic$robust_any_flag),
  zero_mt_nuclei = sum(analytic$nCount_MT == 0),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("QC directory: ", qc_dir, "\n", sep = "")
cat("Source nuclei: ", ncol(counts), "\n", sep = "")
cat("Analytic nuclei: ", nrow(analytic), "\n", sep = "")
cat("Analytic donors: ", data.table::uniqueN(analytic$projid), "\n", sep = "")
cat("Fine cell types: ", data.table::uniqueN(analytic$cell_type_high_resolution), "\n", sep = "")
cat("Robust flagged nuclei: ", sum(analytic$robust_any_flag), "\n", sep = "")
cat("Zero-mt nuclei: ", sum(analytic$nCount_MT == 0), "\n", sep = "")
cat("QC status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
