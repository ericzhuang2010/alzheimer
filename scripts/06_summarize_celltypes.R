#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = "descriptive"
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
        "Usage: Rscript scripts/06_summarize_celltypes.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--task-mode descriptive]\n",
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
  if (!identical(out$task_mode, "descriptive")) {
    stop("--task-mode must be 'descriptive'", call. = FALSE)
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

finite_quantile <- function(x, probability) {
  x <- x[is.finite(x)]
  if (!length(x)) return(NA_real_)
  as.numeric(stats::quantile(x, probability, names = FALSE, type = 7))
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

split_mapped_features <- function(x) {
  x <- x[!is.na(x) & nzchar(x)]
  unique(unlist(strsplit(x, ";", fixed = TRUE), use.names = FALSE))
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
if (!file.exists(source_path)) stop("Source RDS does not exist: ", source_path, call. = FALSE)
source_sha_before <- sha256_file(source_path)
base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_path))
prefix <- tolower(rds_id)

audit_path <- file.path(output_root, "01_audit", paste0(base_name, ".audit.tsv"))
audit_cell_types_path <- file.path(output_root, "01_audit", paste0(base_name, ".cell_types.tsv"))
intersections_path <- file.path(output_root, "02_cohort", "cohort_rds_intersections.tsv")
annotation_status_path <- file.path(output_root, "03_annotations", "annotation_status.tsv")
mt_annotation_path <- file.path(output_root, "03_annotations", "mtDNA_protein_genes.tsv")
mitocarta_annotation_path <- file.path(output_root, "03_annotations", "mitocarta_measured_genes.tsv")
qc_path <- file.path(output_root, "04_qc", paste0(prefix, "_cell_qc.tsv.gz"))
donor_qc_path <- file.path(output_root, "04_qc", paste0(prefix, "_donor_celltype_qc.tsv"))
qc_status_path <- file.path(output_root, "04_qc", paste0(prefix, "_qc_status.tsv"))
normalization_status_path <- file.path(
  output_root, "05_normalized", paste0(base_name, ".normalization_status.tsv")
)
required_paths <- c(
  audit_path, audit_cell_types_path, intersections_path, annotation_status_path,
  mt_annotation_path, mitocarta_annotation_path, qc_path, donor_qc_path,
  qc_status_path, normalization_status_path
)
missing_paths <- required_paths[!file.exists(required_paths)]
if (length(missing_paths)) {
  stop("Required Phase 01-05 inputs are missing: ", paste(missing_paths, collapse = ", "), call. = FALSE)
}

audit <- data.table::fread(audit_path, data.table = FALSE)
annotation_status <- data.table::fread(annotation_status_path, data.table = FALSE)
qc_status <- data.table::fread(qc_status_path, data.table = FALSE)
normalization_status <- data.table::fread(normalization_status_path, data.table = FALSE)
for (item in list(audit, annotation_status, qc_status, normalization_status)) {
  if (nrow(item) != 1L || !identical(item$validation_status[[1L]], "validated_complete")) {
    stop("All required Phase 01, 03, 04, and 05 statuses must be validated_complete", call. = FALSE)
  }
}

intersections <- data.table::fread(intersections_path, data.table = FALSE)
intersection <- intersections[intersections$rds_id == rds_id, , drop = FALSE]
if (nrow(intersection) != 1L) stop("Cohort intersection must identify one row", call. = FALSE)
cohort_path <- absolute_path(as.character(intersection$output_file[[1L]]), project_root)
if (!file.exists(cohort_path)) stop("RDS cohort is missing: ", cohort_path, call. = FALSE)
cohort <- data.table::fread(
  cohort_path, colClasses = c(projid = "character"), data.table = FALSE
)

cell_type_inventory <- data.table::fread(audit_cell_types_path, data.table = FALSE)
cell_types <- sort(unique(as.character(cell_type_inventory$fine_cell_type)))
qc <- data.table::fread(
  qc_path,
  colClasses = c(barcode = "character", projid = "character"),
  data.table = TRUE
)
donor_qc <- data.table::fread(
  donor_qc_path, colClasses = c(projid = "character"), data.table = TRUE
)
mt_annotation <- data.table::fread(mt_annotation_path, data.table = FALSE)
mt_annotation <- mt_annotation[mt_annotation$rds_id == rds_id, , drop = FALSE]
mitocarta <- data.table::fread(mitocarta_annotation_path, data.table = FALSE)
mitocarta <- mitocarta[mitocarta$rds_id == rds_id, , drop = FALSE]
if (!length(cell_types) || !nrow(qc) || !nrow(donor_qc)) {
  stop("Audit or QC inventories are empty", call. = FALSE)
}

primary_minimum <- as.integer(analysis$pseudobulk$minimum_nuclei_primary %||% 20L)
sensitivity_minimum <- as.integer(
  analysis$pseudobulk$minimum_nuclei_sensitivity %||% 50L
)
minimum_donors <- as.integer(
  analysis$pseudobulk$minimum_donors_per_contrast_side %||% 5L
)
if (primary_minimum < 1L || sensitivity_minimum < primary_minimum || minimum_donors < 1L) {
  stop("Invalid pseudobulk eligibility thresholds", call. = FALSE)
}

sample_eligibility <- data.table::copy(donor_qc)
sample_eligibility[, `:=`(
  minimum_nuclei_primary = primary_minimum,
  minimum_nuclei_sensitivity = sensitivity_minimum,
  primary_eligible = nuclei >= primary_minimum,
  sensitivity_eligible = nuclei >= sensitivity_minimum,
  primary_ineligibility_reason = ifelse(
    nuclei >= primary_minimum, "", paste0("nuclei_below_", primary_minimum)
  ),
  sensitivity_ineligibility_reason = ifelse(
    nuclei >= sensitivity_minimum, "", paste0("nuclei_below_", sensitivity_minimum)
  )
)]
sample_eligibility[, schema_version := "descriptive_sample_eligibility_v1"]
eligibility_first <- c(
  "schema_version", "rds_id", "projid", "cell_type_high_resolution",
  "diagnosis", "sex", "apoe_group", "nuclei", "minimum_nuclei_primary",
  "minimum_nuclei_sensitivity", "primary_eligible", "sensitivity_eligible",
  "primary_ineligibility_reason", "sensitivity_ineligibility_reason"
)
data.table::setcolorder(sample_eligibility, c(
  eligibility_first, setdiff(names(sample_eligibility), eligibility_first)
))

analytic_qc <- qc[cohort_included == TRUE]
sex_levels <- unlist(analysis$contrasts$sex_levels, use.names = FALSE)
apoe_levels <- unlist(analysis$contrasts$apoe_levels, use.names = FALSE)
diagnosis_levels <- c(analysis$contrasts$denominator, analysis$contrasts$numerator)
group_grid <- data.table::CJ(
  cell_type_high_resolution = cell_types,
  sex = sex_levels,
  apoe_group = apoe_levels,
  diagnosis = diagnosis_levels,
  unique = TRUE
)

cell_group_summary <- analytic_qc[, .(
  nuclei = .N,
  donors = data.table::uniqueN(projid),
  median_nCount_RNA = as.numeric(stats::median(nCount_RNA)),
  median_nFeature_RNA = as.numeric(stats::median(nFeature_RNA)),
  median_nCount_MT = as.numeric(stats::median(nCount_MT)),
  median_percent_mt = as.numeric(stats::median(percent_mt)),
  q25_percent_mt = finite_quantile(percent_mt, 0.25),
  q75_percent_mt = finite_quantile(percent_mt, 0.75),
  median_nFeature_MT = as.numeric(stats::median(nFeature_MT)),
  median_percent_mitocarta = as.numeric(stats::median(percent_mitocarta)),
  zero_mt_nuclei = sum(nCount_MT == 0),
  zero_mt_fraction = mean(nCount_MT == 0),
  robust_flagged_nuclei = sum(robust_any_flag),
  robust_flagged_fraction = mean(robust_any_flag)
), by = .(cell_type_high_resolution, sex, apoe_group, diagnosis)]

eligibility_group_summary <- sample_eligibility[, .(
  donor_celltype_samples = .N,
  median_nuclei_per_donor = as.numeric(stats::median(nuclei)),
  q25_nuclei_per_donor = finite_quantile(nuclei, 0.25),
  q75_nuclei_per_donor = finite_quantile(nuclei, 0.75),
  primary_eligible_donors = sum(primary_eligible),
  sensitivity_eligible_donors = sum(sensitivity_eligible),
  primary_ineligible_donors = sum(!primary_eligible),
  sensitivity_ineligible_donors = sum(!sensitivity_eligible)
), by = .(cell_type_high_resolution, sex, apoe_group, diagnosis)]

group_coverage <- merge(
  group_grid, cell_group_summary,
  by = c("cell_type_high_resolution", "sex", "apoe_group", "diagnosis"),
  all.x = TRUE, sort = TRUE
)
group_coverage <- merge(
  group_coverage, eligibility_group_summary,
  by = c("cell_type_high_resolution", "sex", "apoe_group", "diagnosis"),
  all.x = TRUE, sort = TRUE
)
zero_fields <- c(
  "nuclei", "donors", "zero_mt_nuclei", "robust_flagged_nuclei",
  "donor_celltype_samples", "primary_eligible_donors",
  "sensitivity_eligible_donors", "primary_ineligible_donors",
  "sensitivity_ineligible_donors"
)
for (field in zero_fields) group_coverage[[field]][is.na(group_coverage[[field]])] <- 0L
group_coverage$group_has_nuclei <- group_coverage$nuclei > 0L
group_coverage$primary_side_eligible <- group_coverage$primary_eligible_donors >= minimum_donors
group_coverage$sensitivity_side_eligible <- group_coverage$sensitivity_eligible_donors >= minimum_donors
group_coverage$minimum_donors_per_contrast_side <- minimum_donors
group_coverage$schema_version <- "descriptive_group_coverage_v1"
group_coverage$rds_id <- rds_id
group_first <- c(
  "schema_version", "rds_id", "cell_type_high_resolution", "sex",
  "apoe_group", "diagnosis"
)
data.table::setcolorder(group_coverage, c(
  group_first, setdiff(names(group_coverage), group_first)
))

contrast_rows <- lapply(
  split(
    group_coverage,
    interaction(
      group_coverage$cell_type_high_resolution,
      group_coverage$sex,
      group_coverage$apoe_group,
      drop = TRUE, lex.order = TRUE
    )
  ),
  function(table) {
    nci <- table[table$diagnosis == analysis$contrasts$denominator, , drop = FALSE]
    ad <- table[table$diagnosis == analysis$contrasts$numerator, , drop = FALSE]
    data.frame(
      schema_version = "descriptive_contrast_coverage_v1",
      rds_id = rds_id,
      cell_type_high_resolution = table$cell_type_high_resolution[[1L]],
      sex = table$sex[[1L]],
      apoe_group = table$apoe_group[[1L]],
      contrast = paste0(analysis$contrasts$numerator, "_vs_", analysis$contrasts$denominator),
      minimum_donors_per_side = minimum_donors,
      nci_nuclei = nci$nuclei[[1L]],
      ad_nuclei = ad$nuclei[[1L]],
      nci_primary_eligible_donors = nci$primary_eligible_donors[[1L]],
      ad_primary_eligible_donors = ad$primary_eligible_donors[[1L]],
      nci_sensitivity_eligible_donors = nci$sensitivity_eligible_donors[[1L]],
      ad_sensitivity_eligible_donors = ad$sensitivity_eligible_donors[[1L]],
      primary_contrast_eligible = nci$primary_side_eligible[[1L]] && ad$primary_side_eligible[[1L]],
      sensitivity_contrast_eligible = nci$sensitivity_side_eligible[[1L]] && ad$sensitivity_side_eligible[[1L]],
      primary_ineligibility_reason = if (
        nci$primary_side_eligible[[1L]] && ad$primary_side_eligible[[1L]]
      ) "" else paste0(
        "fewer_than_", minimum_donors,
        "_eligible_donors_on_one_or_both_sides"
      ),
      stringsAsFactors = FALSE
    )
  }
)
contrast_coverage <- do.call(rbind, contrast_rows)
rownames(contrast_coverage) <- NULL

message("Reading source object for mitochondrial detection summaries: ", source_path)
object <- readRDS(source_path)
if (!inherits(object, "Seurat")) stop("Source is not a Seurat object", call. = FALSE)
assay <- analysis$normalization$assay %||% "RNA"
counts <- get_assay_layer(object, assay, "counts")
if (is.null(counts)) stop("Raw counts layer is absent", call. = FALSE)
cells <- colnames(counts)
qc_index <- match(cells, qc$barcode)
if (anyNA(qc_index) || anyDuplicated(qc$barcode) || nrow(qc) != length(cells)) {
  stop("Phase 04 QC must align one-to-one with source barcodes", call. = FALSE)
}
aligned_qc <- qc[qc_index]
analytic_index <- which(aligned_qc$cohort_included)

expected_mt <- unlist(analysis$mitochondrial_features$mtdna_protein_genes, use.names = FALSE)
mt_features <- intersect(expected_mt, rownames(counts))
mt_rows <- list()
for (cell_type in cell_types) {
  cell_index <- analytic_index[
    aligned_qc$cell_type_high_resolution[analytic_index] == cell_type
  ]
  current_projids <- aligned_qc$projid[cell_index]
  matrix <- counts[mt_features, cell_index, drop = FALSE]
  for (gene in expected_mt) {
    if (gene %in% mt_features) {
      values <- as.numeric(matrix[gene, ])
      detected <- values > 0
      total_counts <- sum(values)
      detected_nuclei <- sum(detected)
      detected_donors <- data.table::uniqueN(current_projids[detected])
    } else {
      total_counts <- 0
      detected_nuclei <- 0L
      detected_donors <- 0L
    }
    mt_rows[[length(mt_rows) + 1L]] <- data.frame(
      schema_version = "descriptive_mtdna_detection_v1",
      rds_id = rds_id,
      cell_type_high_resolution = cell_type,
      feature = gene,
      measured = gene %in% mt_features,
      nuclei = length(cell_index),
      donors = data.table::uniqueN(current_projids),
      total_raw_counts = total_counts,
      nuclei_detected = detected_nuclei,
      nucleus_detection_fraction = if (length(cell_index)) detected_nuclei / length(cell_index) else NA_real_,
      donors_detected = detected_donors,
      donor_detection_fraction = if (data.table::uniqueN(current_projids)) {
        detected_donors / data.table::uniqueN(current_projids)
      } else NA_real_,
      stringsAsFactors = FALSE
    )
  }
}
mito_detection <- do.call(rbind, mt_rows)

measured_mitocarta <- mitocarta[mitocarta$measured, , drop = FALSE]
mapped_features <- split_mapped_features(measured_mitocarta$mapped_feature)
mapped_features <- intersect(mapped_features, rownames(counts))
mitocarta_rows <- list()
for (cell_type in cell_types) {
  cell_index <- analytic_index[
    aligned_qc$cell_type_high_resolution[analytic_index] == cell_type
  ]
  feature_totals <- if (length(mapped_features) && length(cell_index)) {
    Matrix::rowSums(counts[mapped_features, cell_index, drop = FALSE])
  } else {
    stats::setNames(numeric(length(mapped_features)), mapped_features)
  }
  canonical_detected <- vapply(
    measured_mitocarta$mapped_feature,
    function(value) {
      features_for_gene <- intersect(split_mapped_features(value), names(feature_totals))
      length(features_for_gene) && any(feature_totals[features_for_gene] > 0)
    },
    logical(1)
  )
  measured_count <- sum(mitocarta$measured)
  tested_count <- sum(mitocarta$tested)
  detected_count <- sum(canonical_detected)
  mitocarta_rows[[length(mitocarta_rows) + 1L]] <- data.frame(
    schema_version = "descriptive_mitocarta_coverage_v1",
    rds_id = rds_id,
    cell_type_high_resolution = cell_type,
    inventory_genes = nrow(mitocarta),
    measured_genes = measured_count,
    tested_genes = tested_count,
    unmatched_genes = nrow(mitocarta) - measured_count,
    genes_detected_in_analytic_nuclei = detected_count,
    fraction_of_inventory_measured = measured_count / nrow(mitocarta),
    fraction_of_measured_detected = if (measured_count) detected_count / measured_count else NA_real_,
    analytic_nuclei = length(cell_index),
    analytic_donors = data.table::uniqueN(aligned_qc$projid[cell_index]),
    stringsAsFactors = FALSE
  )
}
mitocarta_coverage <- do.call(rbind, mitocarta_rows)
source_sha_after <- sha256_file(source_path)

descriptive_dir <- file.path(output_root, "06_descriptive")
dir.create(descriptive_dir, recursive = TRUE, showWarnings = FALSE)
paths <- list(
  groups = file.path(descriptive_dir, paste0(prefix, "_group_coverage.tsv")),
  contrasts = file.path(descriptive_dir, paste0(prefix, "_contrast_coverage.tsv")),
  eligibility = file.path(descriptive_dir, paste0(prefix, "_sample_eligibility.tsv")),
  mt = file.path(descriptive_dir, paste0(prefix, "_mito_detection.tsv")),
  mitocarta = file.path(descriptive_dir, paste0(prefix, "_mitocarta_coverage.tsv")),
  figure = file.path(descriptive_dir, paste0(prefix, "_descriptive_figures.pdf")),
  checks = file.path(descriptive_dir, paste0(prefix, "_descriptive_checks.tsv")),
  manifest = file.path(descriptive_dir, paste0(prefix, "_descriptive_manifest.tsv")),
  status = file.path(descriptive_dir, paste0(prefix, "_descriptive_status.tsv"))
)

atomic_write_tsv(group_coverage, paths$groups)
atomic_write_tsv(contrast_coverage, paths$contrasts)
atomic_write_tsv(as.data.frame(sample_eligibility), paths$eligibility)
atomic_write_tsv(mito_detection, paths$mt)
atomic_write_tsv(mitocarta_coverage, paths$mitocarta)

figure_tmp <- paste0(paths$figure, ".tmp.", Sys.getpid())
grDevices::pdf(figure_tmp, width = 11, height = 8.5)
cell_totals <- analytic_qc[, .(nuclei = .N, donors = data.table::uniqueN(projid)),
  by = cell_type_high_resolution
]
graphics::barplot(
  cell_totals$nuclei, names.arg = cell_totals$cell_type_high_resolution,
  las = 2, col = "steelblue2", main = "Analytic nuclei by fine cell type",
  ylab = "Nuclei"
)
eligible_totals <- sample_eligibility[, .(
  primary = sum(primary_eligible), sensitivity = sum(sensitivity_eligible)
), by = cell_type_high_resolution]
graphics::barplot(
  t(as.matrix(eligible_totals[, .(primary, sensitivity)])),
  beside = TRUE, names.arg = eligible_totals$cell_type_high_resolution,
  las = 2, col = c("darkseagreen3", "goldenrod2"),
  legend.text = c(paste0(">=", primary_minimum), paste0(">=", sensitivity_minimum)),
  main = "Eligible donor-cell-type samples", ylab = "Donors"
)
graphics::boxplot(
  percent_mt ~ cell_type_high_resolution, data = analytic_qc,
  las = 2, col = "grey85", main = "percent.mt by fine cell type",
  ylab = "percent.mt"
)
contrast_plot <- stats::xtabs(
  as.integer(primary_contrast_eligible) ~ cell_type_high_resolution + sex + apoe_group,
  data = contrast_coverage
)
graphics::barplot(
  rowSums(contrast_plot), las = 2, col = "mediumpurple2",
  main = "Eligible primary AD-vs-NCI strata", ylab = "Eligible sex-APOE strata"
)
grDevices::dev.off()
if (!file.rename(figure_tmp, paths$figure)) {
  stop("Could not atomically publish descriptive figures", call. = FALSE)
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "descriptive_checks_v1",
    rds_id = rds_id,
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}

expected_group_rows <- length(cell_types) * length(sex_levels) *
  length(apoe_levels) * length(diagnosis_levels)
expected_contrast_rows <- length(cell_types) * length(sex_levels) * length(apoe_levels)
add_check("phase01_status_validated", identical(audit$validation_status[[1L]], "validated_complete"), audit$validation_status[[1L]], "validated_complete")
add_check("phase03_status_validated", identical(annotation_status$validation_status[[1L]], "validated_complete"), annotation_status$validation_status[[1L]], "validated_complete")
add_check("phase04_status_validated", identical(qc_status$validation_status[[1L]], "validated_complete"), qc_status$validation_status[[1L]], "validated_complete")
add_check("phase05_status_validated", identical(normalization_status$validation_status[[1L]], "validated_complete"), normalization_status$validation_status[[1L]], "validated_complete")
add_check("source_feature_count_matches_audit", nrow(counts) == audit$features[[1L]], nrow(counts), audit$features[[1L]])
add_check("source_nucleus_count_matches_audit", ncol(counts) == audit$nuclei[[1L]], ncol(counts), audit$nuclei[[1L]])
add_check("qc_barcode_join_complete", identical(cells, aligned_qc$barcode), sum(cells == aligned_qc$barcode), length(cells))
add_check("analytic_donor_count_matches_cohort", data.table::uniqueN(analytic_qc$projid) == nrow(cohort), data.table::uniqueN(analytic_qc$projid), nrow(cohort))
add_check("sample_cell_conservation", sum(sample_eligibility$nuclei) == nrow(analytic_qc), sum(sample_eligibility$nuclei), nrow(analytic_qc))
add_check("group_row_count", nrow(group_coverage) == expected_group_rows, nrow(group_coverage), expected_group_rows)
add_check("twelve_groups_per_cell_type", all(table(group_coverage$cell_type_high_resolution) == 12L), table(group_coverage$cell_type_high_resolution), 12L)
add_check("group_nucleus_conservation", sum(group_coverage$nuclei) == nrow(analytic_qc), sum(group_coverage$nuclei), nrow(analytic_qc))
add_check("contrast_row_count", nrow(contrast_coverage) == expected_contrast_rows, nrow(contrast_coverage), expected_contrast_rows)
add_check("eligibility_thresholds", all(sample_eligibility$minimum_nuclei_primary == primary_minimum) && all(sample_eligibility$minimum_nuclei_sensitivity == sensitivity_minimum), paste(primary_minimum, sensitivity_minimum), paste(primary_minimum, sensitivity_minimum))
add_check("all_expected_mtdna_features", identical(sort(mt_features), sort(expected_mt)), mt_features, expected_mt)
add_check("mtdna_rows_per_cell_type", nrow(mito_detection) == length(cell_types) * length(expected_mt), nrow(mito_detection), length(cell_types) * length(expected_mt))
add_check("mtdna_detection_ranges", all(mito_detection$nuclei_detected >= 0 & mito_detection$nuclei_detected <= mito_detection$nuclei) && all(mito_detection$donors_detected >= 0 & mito_detection$donors_detected <= mito_detection$donors), range(mito_detection$nucleus_detection_fraction, na.rm = TRUE), "0..1")
add_check("mitocarta_cell_type_rows", nrow(mitocarta_coverage) == length(cell_types), nrow(mitocarta_coverage), length(cell_types))
add_check("mitocarta_coverage_bounds", all(mitocarta_coverage$genes_detected_in_analytic_nuclei <= mitocarta_coverage$measured_genes), max(mitocarta_coverage$genes_detected_in_analytic_nuclei), max(mitocarta_coverage$measured_genes))
add_check("source_rds_unchanged", identical(source_sha_after, source_sha_before), source_sha_after, source_sha_before)

check_table <- do.call(rbind, checks)
failed_checks <- check_table$check[!check_table$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"
atomic_write_tsv(check_table, paths$checks)

artifact_paths <- c(
  paths$groups, paths$contrasts, paths$eligibility, paths$mt,
  paths$mitocarta, paths$figure, paths$checks
)
artifact_records <- c(
  nrow(group_coverage), nrow(contrast_coverage), nrow(sample_eligibility),
  nrow(mito_detection), nrow(mitocarta_coverage), NA_integer_, nrow(check_table)
)
descriptive_manifest <- data.frame(
  schema_version = "descriptive_manifest_v1",
  rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = artifact_records,
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(descriptive_manifest, paths$manifest)

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) "local_pilot_manual" else "manual_descriptive"
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) stop("Execution config does not exist", call. = FALSE)
  execution <- yaml::read_yaml(execution_path)$execution
  execution_phase <- execution$execution_phase %||% execution_phase
  backend <- execution$backend %||% backend
  run_id <- execution$run_id %||% run_id
}

status <- data.frame(
  schema_version = "descriptive_status_v1",
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = paste("descriptive", rds_id, sep = ":"),
  source_rds = source_rel,
  source_rds_sha256 = source_sha_before,
  scientific_script = "scripts/06_summarize_celltypes.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/06_summarize_celltypes.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  phase01_audit_sha256 = sha256_file(audit_path),
  phase02_cohort_sha256 = sha256_file(cohort_path),
  phase03_annotation_status_sha256 = sha256_file(annotation_status_path),
  phase04_qc_sha256 = sha256_file(qc_path),
  phase05_normalization_status_sha256 = sha256_file(normalization_status_path),
  fine_cell_types = length(cell_types),
  analytic_nuclei = nrow(analytic_qc),
  analytic_donors = data.table::uniqueN(analytic_qc$projid),
  donor_celltype_samples = nrow(sample_eligibility),
  primary_eligible_samples = sum(sample_eligibility$primary_eligible),
  sensitivity_eligible_samples = sum(sample_eligibility$sensitivity_eligible),
  primary_eligible_contrasts = sum(contrast_coverage$primary_contrast_eligible),
  sensitivity_eligible_contrasts = sum(contrast_coverage$sensitivity_contrast_eligible),
  zero_nucleus_groups = sum(!group_coverage$group_has_nuclei),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Descriptive directory: ", descriptive_dir, "\n", sep = "")
cat("Fine cell types: ", length(cell_types), "\n", sep = "")
cat("Analytic nuclei: ", nrow(analytic_qc), "\n", sep = "")
cat("Analytic donors: ", data.table::uniqueN(analytic_qc$projid), "\n", sep = "")
cat("Donor-cell-type samples: ", nrow(sample_eligibility), "\n", sep = "")
cat("Primary eligible samples: ", sum(sample_eligibility$primary_eligible), "\n", sep = "")
cat("Primary eligible AD-vs-NCI contrasts: ", sum(contrast_coverage$primary_contrast_eligible), "\n", sep = "")
cat("Zero-nucleus groups: ", sum(!group_coverage$group_has_nuclei), "\n", sep = "")
cat("Descriptive status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
