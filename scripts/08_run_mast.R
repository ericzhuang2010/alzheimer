#!/usr/bin/env Rscript

# Phase 08 v2: Yu et al. cell-level MAST replication.
#
# This implementation intentionally depends on Phase 05 only. It selects all
# cohort-included nuclei in each fine-cell-type/sex/APOE AD-versus-NCI stratum
# and never reads Phase 07 eligibility, pseudobulk samples, or pseudobulk DE.

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, input = NULL, manifest = NULL, task_mode = "mast"
  )
  value_options <- c(
    "--config", "--execution-config", "--manifest-row", "--rds-id",
    "--input", "--manifest", "--task-mode"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/08_run_mast.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--input NORMALIZED_RDS] [--manifest YU_MANIFEST_TSV] ",
        "[--task-mode mast]\n",
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
  if (!identical(out$task_mode, "mast")) {
    stop("--task-mode must be 'mast'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  sub(paste0("^", root, "/?"), "", path)
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

normalize_id <- function(x, width) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "NaN")] <- NA_character_
  valid <- !is.na(x)
  x[valid] <- vapply(x[valid], function(value) {
    if (grepl("^[0-9]+$", value) && nchar(value) < width) {
      paste0(strrep("0", width - nchar(value)), value)
    } else {
      value
    }
  }, character(1))
  x
}

yu_stratum <- function(sex, apoe) {
  sex_token <- switch(
    as.character(sex), Female = "F", Male = "M",
    stop("Unsupported sex: ", sex, call. = FALSE)
  )
  apoe_token <- switch(
    as.character(apoe), e2 = "e2x", e33 = "e33", e4 = "e4x",
    stop("Unsupported APOE group: ", apoe, call. = FALSE)
  )
  paste0(sex_token, "_", apoe_token)
}

yu_contrast_label <- function(sex, apoe) {
  label <- yu_stratum(sex, apoe)
  paste0(label, "_AD_vs_", label, "_NCI")
}

small_group_reason <- function(cells_ad, cells_nci, min_cells_group) {
  counts <- c(AD = as.integer(cells_ad), NCI = as.integer(cells_nci))
  zero_arms <- names(counts)[counts < 1L]
  if (length(zero_arms)) {
    return(paste0("zero_cells_in_arm:", paste(zero_arms, collapse = ",")))
  }
  small_arms <- names(counts)[counts < min_cells_group]
  paste0(
    "seurat_min_cells_group_not_met:min_cells_group=", min_cells_group,
    ",arms=", paste0(small_arms, "(", counts[small_arms], ")", collapse = ",")
  )
}

build_yu_manifest <- function(
    metadata, rds_id, analysis, expected_cell_types, min_cells_group) {
  numerator <- as.character(analysis$contrasts$numerator %||% "AD")
  denominator <- as.character(analysis$contrasts$denominator %||% "NCI")
  sexes <- as.character(unlist(
    analysis$contrasts$sex_levels %||% c("Female", "Male"),
    use.names = FALSE
  ))
  apoe_levels <- as.character(unlist(
    analysis$contrasts$apoe_levels %||% c("e2", "e33", "e4"),
    use.names = FALSE
  ))
  if (!setequal(sexes, c("Female", "Male"))) {
    stop("Phase 08 requires Female and Male sex levels", call. = FALSE)
  }
  if (!setequal(apoe_levels, c("e2", "e33", "e4"))) {
    stop("Phase 08 requires e2, e33, and e4 APOE levels", call. = FALSE)
  }

  analytic <- metadata[
    metadata$cohort_included &
      metadata$diagnosis %in% c(numerator, denominator),
    , drop = FALSE
  ]
  cell_types <- sort(unique(analytic$cell_type_high_resolution))
  cell_types <- cell_types[!is.na(cell_types) & nzchar(cell_types)]
  if (!length(cell_types)) stop("No cohort-included fine cell types", call. = FALSE)
  if (is.finite(expected_cell_types) && length(cell_types) != expected_cell_types) {
    stop(
      "Phase 05 metadata contains ", length(cell_types),
      " fine cell types; manifest expected ", expected_cell_types,
      call. = FALSE
    )
  }

  rows <- list()
  for (cell_type in cell_types) {
    for (sex in sexes) {
      for (apoe in apoe_levels) {
        selected <- analytic[
          analytic$cell_type_high_resolution == cell_type &
            analytic$sex == sex &
            analytic$apoe_group == apoe,
          , drop = FALSE
        ]
        cells_ad <- sum(selected$diagnosis == numerator)
        cells_nci <- sum(selected$diagnosis == denominator)
        donors_ad <- length(unique(
          selected$projid[selected$diagnosis == numerator]
        ))
        donors_nci <- length(unique(
          selected$projid[selected$diagnosis == denominator]
        ))
        group_too_small <- cells_ad < min_cells_group ||
          cells_nci < min_cells_group
        contrast_name <- paste("AD_vs_NCI", sex, apoe, sep = "__")
        rows[[length(rows) + 1L]] <- data.frame(
          schema_version = "yu_mast_contrast_manifest_v2",
          manifest_row = NA_integer_,
          contrast_id = paste(rds_id, cell_type, contrast_name, sep = "::"),
          rds_id = rds_id,
          cell_type_high_resolution = cell_type,
          sex = sex,
          apoe_group = apoe,
          yu_stratum = yu_stratum(sex, apoe),
          yu_contrast = yu_contrast_label(sex, apoe),
          contrast_family = "AD_vs_NCI",
          contrast_name = contrast_name,
          contrast_kind = "single_df",
          numerator = numerator,
          denominator = denominator,
          cells_ad_expected = as.integer(cells_ad),
          cells_nci_expected = as.integer(cells_nci),
          donors_ad_expected = as.integer(donors_ad),
          donors_nci_expected = as.integer(donors_nci),
          analysis_population = "yu_all_cohort_included_nuclei",
          modeling_status = if (group_too_small) "not_estimable" else "estimable",
          modeling_reason = if (group_too_small) {
            small_group_reason(cells_ad, cells_nci, min_cells_group)
          } else {
            ""
          },
          stringsAsFactors = FALSE
        )
      }
    }
  }
  manifest <- do.call(rbind, rows)
  manifest$manifest_row <- seq_len(nrow(manifest))
  manifest
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c(
  "yaml", "data.table", "RcppAnnoy", "Seurat", "SeuratObject", "MAST"
)
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

# This order avoids the Minerva RcppAnnoy lazy-module failure.
suppressPackageStartupMessages({
  library(RcppAnnoy)
  library(Seurat)
  library(MAST)
})

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
rds_manifest <- read.delim(
  rds_manifest_path, check.names = FALSE, stringsAsFactors = FALSE
)

if (!is.null(args$manifest_row)) {
  selected <- rds_manifest[
    rds_manifest$manifest_row == as.integer(args$manifest_row),
    , drop = FALSE
  ]
} else if (!is.null(args$rds_id)) {
  selected <- rds_manifest[rds_manifest$rds_id == args$rds_id, , drop = FALSE]
} else if (!is.null(args$input)) {
  selected <- NULL
} else {
  stop("Select an RDS with --manifest-row, --rds-id, or --input", call. = FALSE)
}
if (!is.null(selected) && nrow(selected) != 1L) {
  stop("RDS manifest selection must identify exactly one row", call. = FALSE)
}

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct",
  run_id = "manual_yu_mast"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

if (!is.null(args$input)) {
  normalized_path <- absolute_path(args$input, project_root)
  base_name <- sub("[.]normalized[.][Rr][Dd][Ss]$", "", basename(normalized_path))
  source_candidates <- rds_manifest[
    sub("[.][Rr][Dd][Ss]$", "", basename(rds_manifest$input_rds)) == base_name,
    , drop = FALSE
  ]
  if (nrow(source_candidates) != 1L) {
    stop("Could not map normalized input to one RDS manifest row", call. = FALSE)
  }
  selected <- source_candidates
} else {
  source_rel <- as.character(selected$input_rds[[1L]])
  base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_rel))
  normalized_path <- file.path(
    output_root, "05_normalized", paste0(base_name, ".normalized.rds")
  )
}

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
prefix <- tolower(rds_id)
expected_cell_types <- suppressWarnings(as.numeric(selected$expected_cell_types[[1L]]))
if (!file.exists(normalized_path)) {
  stop("Normalized RDS is missing: ", normalized_path, call. = FALSE)
}
normalized_sha_before <- sha256_file(normalized_path)

normalization_status_path <- file.path(
  output_root, "05_normalized", paste0(base_name, ".normalization_status.tsv")
)
if (!file.exists(normalization_status_path)) {
  stop("Normalization status is missing", call. = FALSE)
}
normalization_status <- data.table::fread(
  normalization_status_path, data.table = FALSE
)
if (nrow(normalization_status) != 1L ||
    normalization_status$validation_status[[1L]] != "validated_complete") {
  stop("Phase 05 normalization must be validated_complete", call. = FALSE)
}

message("Reading normalized Seurat object: ", normalized_path)
object <- readRDS(normalized_path)
if (!inherits(object, "Seurat") || !isTRUE(methods::validObject(object))) {
  stop("Normalized input is not a valid Seurat object", call. = FALSE)
}

mast_config <- analysis$models$mast %||% list()
assay <- as.character(mast_config$assay %||% analysis$normalization$assay %||% "RNA")
data_slot <- as.character(mast_config$slot %||% "data")
if (!assay %in% SeuratObject::Assays(object)) {
  stop("Required RNA assay is absent", call. = FALSE)
}
if (!data_slot %in% SeuratObject::Layers(object[[assay]])) {
  stop("Normalized RNA data layer is absent", call. = FALSE)
}
SeuratObject::DefaultAssay(object) <- assay

metadata <- object[[]]
latent_vars <- as.character(unlist(
  mast_config$latent_vars %||% c("nCount_RNA", "age_death_scaled", "pmi_scaled"),
  use.names = FALSE
))
required_metadata <- c(
  "projid", "cell_type_high_resolution", "cohort_included",
  "diagnosis", "sex", "apoe_group", latent_vars
)
missing_metadata <- setdiff(required_metadata, names(metadata))
if (length(missing_metadata)) {
  stop(
    "Normalized metadata fields missing: ",
    paste(missing_metadata, collapse = ", "),
    call. = FALSE
  )
}

projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
metadata$projid <- normalize_id(metadata$projid, projid_width)
metadata$cell_type_high_resolution <- trimws(
  as.character(metadata$cell_type_high_resolution)
)
metadata$diagnosis <- as.character(metadata$diagnosis)
metadata$sex <- as.character(metadata$sex)
metadata$apoe_group <- as.character(metadata$apoe_group)
metadata$cohort_included <- as_logical(metadata$cohort_included)

analysis_population <- as.character(
  mast_config$analysis_population %||% "yu_all_cohort_included_nuclei"
)
if (!identical(analysis_population, "yu_all_cohort_included_nuclei")) {
  stop("Unsupported Phase 08 analysis population", call. = FALSE)
}
min_pct <- as.numeric(mast_config$min_pct %||% 0.10)
logfc_threshold <- as.numeric(mast_config$logfc_threshold %||% 0)
# FindMarkers.default enforces this threshold before dispatching to MAST. Keep
# it explicit so manifest estimability and model execution cannot disagree.
seurat_min_cells_group <- 3L
alpha <- as.numeric(analysis$multiple_testing$alpha %||% 0.05)
paper_fold_change <- as.numeric(
  analysis$multiple_testing$yu_absolute_fold_change_threshold %||% 1.3
)
paper_log2fc_threshold <- log2(paper_fold_change)
if (!is.finite(min_pct) || min_pct < 0 || min_pct > 1) {
  stop("models.mast.min_pct must be in [0,1]", call. = FALSE)
}
if (!identical(logfc_threshold, 0)) {
  stop("Yu-compatible MAST requires logfc_threshold = 0", call. = FALSE)
}
if (!is.finite(alpha) || alpha <= 0 || alpha >= 1) {
  stop("multiple_testing.alpha must be in (0,1)", call. = FALSE)
}

if (!is.null(args$manifest)) {
  input_manifest_path <- absolute_path(args$manifest, project_root)
  if (!file.exists(input_manifest_path)) {
    stop("Yu manifest is missing: ", input_manifest_path, call. = FALSE)
  }
  yu_manifest <- data.table::fread(input_manifest_path, data.table = FALSE)
  yu_manifest <- yu_manifest[yu_manifest$rds_id == rds_id, , drop = FALSE]
} else {
  yu_manifest <- build_yu_manifest(
    metadata, rds_id, analysis, expected_cell_types,
    seurat_min_cells_group
  )
}

required_manifest <- c(
  "schema_version", "manifest_row", "contrast_id", "rds_id",
  "cell_type_high_resolution", "sex", "apoe_group", "yu_stratum",
  "yu_contrast", "contrast_family", "contrast_name", "contrast_kind",
  "numerator", "denominator", "cells_ad_expected", "cells_nci_expected",
  "donors_ad_expected", "donors_nci_expected", "analysis_population",
  "modeling_status", "modeling_reason"
)
missing_manifest <- setdiff(required_manifest, names(yu_manifest))
if (length(missing_manifest)) {
  stop(
    "Yu manifest fields missing: ", paste(missing_manifest, collapse = ", "),
    call. = FALSE
  )
}
if (!nrow(yu_manifest)) stop("No Yu MAST contrasts apply to ", rds_id, call. = FALSE)
if (anyDuplicated(yu_manifest$contrast_id) ||
    anyDuplicated(yu_manifest$manifest_row)) {
  stop("Yu manifest rows and contrast IDs must be unique", call. = FALSE)
}
if (!all(yu_manifest$schema_version == "yu_mast_contrast_manifest_v2") ||
    !all(yu_manifest$analysis_population == analysis_population)) {
  stop("Unsupported Yu manifest schema or population", call. = FALSE)
}

# Normalize older/external v2 manifests to the minimum that the exact Seurat
# method can fit. The observed counts are checked against these expected counts
# before any contrast is assigned a terminal outcome below.
small_manifest_groups <-
  as.integer(yu_manifest$cells_ad_expected) < seurat_min_cells_group |
  as.integer(yu_manifest$cells_nci_expected) < seurat_min_cells_group
if (any(small_manifest_groups)) {
  yu_manifest$modeling_status[small_manifest_groups] <- "not_estimable"
  yu_manifest$modeling_reason[small_manifest_groups] <- vapply(
    which(small_manifest_groups),
    function(i) small_group_reason(
      yu_manifest$cells_ad_expected[[i]],
      yu_manifest$cells_nci_expected[[i]],
      seurat_min_cells_group
    ),
    character(1)
  )
}

result_list <- list()
diagnostic_list <- list()
status_list <- list()

add_status <- function(
    row, terminal_status, genes_returned = 0L, paper_degs = 0L,
    cells_ad = 0L, cells_nci = 0L, donors_ad = 0L, donors_nci = 0L,
    message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "yu_mast_contrast_status_v2",
    rds_id = rds_id,
    manifest_row = as.integer(row$manifest_row),
    contrast_id = as.character(row$contrast_id),
    cell_type_high_resolution = as.character(row$cell_type_high_resolution),
    sex = as.character(row$sex),
    apoe_group = as.character(row$apoe_group),
    yu_stratum = as.character(row$yu_stratum),
    yu_contrast = as.character(row$yu_contrast),
    contrast_family = as.character(row$contrast_family),
    contrast_name = as.character(row$contrast_name),
    analysis_population = analysis_population,
    manifest_modeling_status = as.character(row$modeling_status),
    terminal_status = terminal_status,
    genes_returned = as.integer(genes_returned),
    paper_degs = as.integer(paper_degs),
    cells_ad = as.integer(cells_ad),
    cells_nci = as.integer(cells_nci),
    donors_ad = as.integer(donors_ad),
    donors_nci = as.integer(donors_nci),
    message = as.character(message),
    stringsAsFactors = FALSE
  )
}

add_diagnostic <- function(
    row, model_status, cells_ad, cells_nci, donors_ad, donors_nci,
    tested_genes = 0L, paper_degs = 0L, design_rank = NA_integer_,
    design_columns = NA_integer_, message = "") {
  diagnostic_list[[length(diagnostic_list) + 1L]] <<- data.frame(
    schema_version = "yu_mast_model_diagnostics_v2",
    rds_id = rds_id,
    manifest_row = as.integer(row$manifest_row),
    contrast_id = as.character(row$contrast_id),
    cell_type_high_resolution = as.character(row$cell_type_high_resolution),
    sex = as.character(row$sex),
    apoe_group = as.character(row$apoe_group),
    yu_stratum = as.character(row$yu_stratum),
    yu_contrast = as.character(row$yu_contrast),
    contrast_name = as.character(row$contrast_name),
    analysis_population = analysis_population,
    cells_ad = as.integer(cells_ad),
    cells_nci = as.integer(cells_nci),
    donors_ad = as.integer(donors_ad),
    donors_nci = as.integer(donors_nci),
    tested_genes = as.integer(tested_genes),
    paper_degs = as.integer(paper_degs),
    latent_vars = paste(latent_vars, collapse = ";"),
    min_pct = min_pct,
    logfc_threshold = logfc_threshold,
    design_rank = as.integer(design_rank),
    design_columns = as.integer(design_columns),
    model_status = model_status,
    message = as.character(message),
    stringsAsFactors = FALSE
  )
}

for (row_index in seq_len(nrow(yu_manifest))) {
  row <- yu_manifest[row_index, , drop = FALSE]
  cell_type <- as.character(row$cell_type_high_resolution)
  numerator <- as.character(row$numerator)
  denominator <- as.character(row$denominator)

  cell_mask <- metadata$cohort_included &
    metadata$cell_type_high_resolution == cell_type &
    metadata$sex == as.character(row$sex) &
    metadata$apoe_group == as.character(row$apoe_group) &
    metadata$diagnosis %in% c(numerator, denominator)
  cell_mask[is.na(cell_mask)] <- FALSE
  selected_cells <- rownames(metadata)[cell_mask]
  selected_metadata <- metadata[cell_mask, , drop = FALSE]

  cells_ad <- sum(selected_metadata$diagnosis == numerator)
  cells_nci <- sum(selected_metadata$diagnosis == denominator)
  donors_ad <- length(unique(
    selected_metadata$projid[selected_metadata$diagnosis == numerator]
  ))
  donors_nci <- length(unique(
    selected_metadata$projid[selected_metadata$diagnosis == denominator]
  ))

  counts_match <- cells_ad == as.integer(row$cells_ad_expected) &&
    cells_nci == as.integer(row$cells_nci_expected) &&
    donors_ad == as.integer(row$donors_ad_expected) &&
    donors_nci == as.integer(row$donors_nci_expected)
  if (!counts_match) {
    message_text <- paste0(
      "manifest_count_mismatch:observed_cells=", cells_ad, "/", cells_nci,
      ",observed_donors=", donors_ad, "/", donors_nci,
      ",expected_cells=", row$cells_ad_expected, "/", row$cells_nci_expected,
      ",expected_donors=", row$donors_ad_expected, "/", row$donors_nci_expected
    )
    add_status(
      row, "failed", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    add_diagnostic(
      row, "failed", cells_ad, cells_nci, donors_ad, donors_nci,
      message = message_text
    )
    next
  }

  if (as.character(row$modeling_status) != "estimable") {
    message_text <- as.character(row$modeling_reason)
    add_status(
      row, "not_estimable", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    add_diagnostic(
      row, "not_estimable", cells_ad, cells_nci, donors_ad, donors_nci,
      message = message_text
    )
    next
  }

  covariate_frame <- selected_metadata[, latent_vars, drop = FALSE]
  covariates_complete <- !anyNA(covariate_frame) && all(vapply(
    covariate_frame,
    function(x) all(is.finite(as.numeric(x))),
    logical(1)
  ))
  if (!covariates_complete) {
    message_text <- "latent_covariates_incomplete_or_nonfinite"
    add_status(
      row, "not_estimable", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    add_diagnostic(
      row, "not_estimable", cells_ad, cells_nci, donors_ad, donors_nci,
      message = message_text
    )
    next
  }

  design_data <- data.frame(
    diagnosis = factor(
      selected_metadata$diagnosis,
      levels = c(denominator, numerator)
    ),
    lapply(covariate_frame, as.numeric),
    check.names = FALSE
  )
  design <- stats::model.matrix(~ ., data = design_data)
  design_rank <- qr(design)$rank
  design_columns <- ncol(design)
  if (design_rank != design_columns) {
    message_text <- paste0(
      "latent_covariate_design_rank_deficient:",
      design_rank, "_of_", design_columns
    )
    add_status(
      row, "not_estimable", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    add_diagnostic(
      row, "not_estimable", cells_ad, cells_nci, donors_ad, donors_nci,
      design_rank = design_rank, design_columns = design_columns,
      message = message_text
    )
    next
  }

  message(
    "Running Yu MAST: ", cell_type, " / ", row$contrast_name,
    " (AD cells=", cells_ad, ", NCI cells=", cells_nci,
    "; AD donors=", donors_ad, ", NCI donors=", donors_nci, ")"
  )
  subobject <- object[, selected_cells, drop = FALSE]
  SeuratObject::DefaultAssay(subobject) <- assay
  marker_error <- NULL
  markers <- tryCatch(
    Seurat::FindMarkers(
      object = subobject,
      ident.1 = numerator,
      ident.2 = denominator,
      group.by = "diagnosis",
      assay = assay,
      slot = data_slot,
      test.use = "MAST",
      min.pct = min_pct,
      min.cells.group = seurat_min_cells_group,
      logfc.threshold = logfc_threshold,
      latent.vars = latent_vars,
      densify = FALSE,
      verbose = FALSE
    ),
    error = function(e) {
      marker_error <<- conditionMessage(e)
      NULL
    }
  )
  rm(subobject)
  invisible(gc())

  if (is.null(markers)) {
    add_status(
      row, "failed", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = marker_error
    )
    add_diagnostic(
      row, "failed", cells_ad, cells_nci, donors_ad, donors_nci,
      design_rank = design_rank, design_columns = design_columns,
      message = marker_error
    )
    next
  }

  logfc_column <- intersect(c("avg_log2FC", "avg_logFC"), names(markers))
  if (nrow(markers) &&
      (length(logfc_column) != 1L ||
       !all(c("p_val", "pct.1", "pct.2") %in% names(markers)))) {
    message_text <- "FindMarkers returned an unsupported result schema"
    add_status(
      row, "failed", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    add_diagnostic(
      row, "failed", cells_ad, cells_nci, donors_ad, donors_nci,
      design_rank = design_rank, design_columns = design_columns,
      message = message_text
    )
    next
  }

  paper_deg_count <- 0L
  if (nrow(markers)) {
    gene <- rownames(markers)
    p_value <- as.numeric(markers$p_val)
    fdr <- stats::p.adjust(p_value, method = "BH")
    bonferroni <- if ("p_val_adj" %in% names(markers)) {
      as.numeric(markers$p_val_adj)
    } else {
      stats::p.adjust(p_value, method = "bonferroni")
    }
    logfc <- as.numeric(markers[[logfc_column]])
    pct_ad <- as.numeric(markers$pct.1)
    pct_nci <- as.numeric(markers$pct.2)
    paper_deg <- fdr < alpha &
      abs(logfc) > paper_log2fc_threshold &
      (pct_ad >= min_pct | pct_nci >= min_pct)

    result <- data.frame(
      schema_version = "yu_mast_de_results_v2",
      rds_id = rds_id,
      source_rds = source_rel,
      normalized_rds = relative_path(normalized_path, project_root),
      analysis_population = analysis_population,
      cell_type_high_resolution = cell_type,
      sex = as.character(row$sex),
      apoe_group = as.character(row$apoe_group),
      yu_stratum = as.character(row$yu_stratum),
      yu_contrast = as.character(row$yu_contrast),
      manifest_row = as.integer(row$manifest_row),
      contrast_id = as.character(row$contrast_id),
      contrast_family = as.character(row$contrast_family),
      contrast_name = as.character(row$contrast_name),
      contrast_kind = as.character(row$contrast_kind),
      gene = gene,
      logFC = logfc,
      pct_ad = pct_ad,
      pct_nci = pct_nci,
      p_value = p_value,
      p_val_adj_bonferroni = bonferroni,
      fdr_bh_within_contrast = fdr,
      paper_effect_threshold_log2 = paper_log2fc_threshold,
      paper_deg = paper_deg,
      cells_ad = cells_ad,
      cells_nci = cells_nci,
      donors_ad = donors_ad,
      donors_nci = donors_nci,
      latent_vars = paste(latent_vars, collapse = ";"),
      stringsAsFactors = FALSE
    )
    result_list[[length(result_list) + 1L]] <- result
    paper_deg_count <- sum(paper_deg)
  }

  add_diagnostic(
    row, "fitted", cells_ad, cells_nci, donors_ad, donors_nci,
    tested_genes = nrow(markers), paper_degs = paper_deg_count,
    design_rank = design_rank, design_columns = design_columns
  )
  add_status(
    row, "validated_complete", genes_returned = nrow(markers),
    paper_degs = paper_deg_count, cells_ad = cells_ad,
    cells_nci = cells_nci, donors_ad = donors_ad, donors_nci = donors_nci
  )
}

statuses <- as.data.frame(data.table::rbindlist(
  status_list, fill = TRUE, use.names = TRUE
))
statuses <- statuses[order(statuses$manifest_row), , drop = FALSE]
diagnostics <- as.data.frame(data.table::rbindlist(
  diagnostic_list, fill = TRUE, use.names = TRUE
))
diagnostics <- diagnostics[order(diagnostics$manifest_row), , drop = FALSE]

if (length(result_list)) {
  results <- as.data.frame(data.table::rbindlist(
    result_list, fill = TRUE, use.names = TRUE
  ))
} else {
  results <- data.frame(
    schema_version = character(),
    rds_id = character(),
    source_rds = character(),
    normalized_rds = character(),
    analysis_population = character(),
    cell_type_high_resolution = character(),
    sex = character(),
    apoe_group = character(),
    yu_stratum = character(),
    yu_contrast = character(),
    manifest_row = integer(),
    contrast_id = character(),
    contrast_family = character(),
    contrast_name = character(),
    contrast_kind = character(),
    gene = character(),
    logFC = numeric(),
    pct_ad = numeric(),
    pct_nci = numeric(),
    p_value = numeric(),
    p_val_adj_bonferroni = numeric(),
    fdr_bh_within_contrast = numeric(),
    paper_effect_threshold_log2 = numeric(),
    paper_deg = logical(),
    cells_ad = integer(),
    cells_nci = integer(),
    donors_ad = integer(),
    donors_nci = integer(),
    latent_vars = character(),
    stringsAsFactors = FALSE
  )
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "yu_mast_de_checks_v2",
    rds_id = rds_id,
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}

manifest_cell_types <- unique(yu_manifest$cell_type_high_resolution)
expected_count <- if (is.finite(expected_cell_types)) {
  as.integer(expected_cell_types)
} else {
  length(manifest_cell_types)
}
add_check(
  "expected_fine_cell_types",
  length(manifest_cell_types) == expected_count,
  length(manifest_cell_types),
  expected_count
)
add_check(
  "six_yu_contrasts_per_cell_type",
  nrow(yu_manifest) == length(manifest_cell_types) * 6L &&
    all(table(yu_manifest$cell_type_high_resolution) == 6L),
  nrow(yu_manifest),
  length(manifest_cell_types) * 6L
)
add_check(
  "six_yu_contrast_labels",
  length(unique(yu_manifest$yu_contrast)) == 6L,
  length(unique(yu_manifest$yu_contrast)),
  6L
)
add_check(
  "one_status_per_manifest_row",
  nrow(statuses) == nrow(yu_manifest) &&
    !anyDuplicated(statuses$manifest_row),
  nrow(statuses),
  nrow(yu_manifest)
)
add_check(
  "all_rows_have_terminal_outcome",
  all(statuses$terminal_status %in%
      c("validated_complete", "not_estimable", "failed")),
  paste(sort(unique(statuses$terminal_status)), collapse = ","),
  "validated_complete;not_estimable;failed"
)
add_check(
  "all_estimable_rows_completed",
  all(statuses$terminal_status[yu_manifest$modeling_status == "estimable"] ==
      "validated_complete"),
  sum(statuses$terminal_status == "validated_complete"),
  sum(yu_manifest$modeling_status == "estimable")
)
add_check(
  "no_failed_contrasts",
  !any(statuses$terminal_status == "failed"),
  sum(statuses$terminal_status == "failed"),
  0L
)

result_keys <- if (nrow(results)) {
  paste(
    results$cell_type_high_resolution,
    results$yu_contrast,
    results$gene,
    sep = "\r"
  )
} else {
  character()
}
add_check("result_keys_unique", !anyDuplicated(result_keys), anyDuplicated(result_keys), 0L)
add_check(
  "result_population_is_all_cohort_nuclei",
  !nrow(results) || all(results$analysis_population == analysis_population),
  paste(unique(results$analysis_population), collapse = ","),
  analysis_population
)
add_check(
  "p_values_in_range",
  !nrow(results) || all(
    is.finite(results$p_value) &
      results$p_value >= 0 & results$p_value <= 1
  ),
  if (nrow(results)) sum(
    !is.finite(results$p_value) |
      results$p_value < 0 | results$p_value > 1
  ) else 0L,
  0L
)
add_check(
  "fdr_in_range",
  !nrow(results) || all(
    is.finite(results$fdr_bh_within_contrast) &
      results$fdr_bh_within_contrast >= 0 &
      results$fdr_bh_within_contrast <= 1
  ),
  if (nrow(results)) sum(
    !is.finite(results$fdr_bh_within_contrast) |
      results$fdr_bh_within_contrast < 0 |
      results$fdr_bh_within_contrast > 1
  ) else 0L,
  0L
)
add_check(
  "detection_threshold_respected",
  !nrow(results) ||
    all(results$pct_ad >= min_pct | results$pct_nci >= min_pct),
  if (nrow(results)) {
    sum(results$pct_ad < min_pct & results$pct_nci < min_pct)
  } else {
    0L
  },
  0L
)
expected_paper_deg <- if (nrow(results)) {
  results$fdr_bh_within_contrast < alpha &
    abs(results$logFC) > paper_log2fc_threshold &
    (results$pct_ad >= min_pct | results$pct_nci >= min_pct)
} else {
  logical()
}
add_check(
  "paper_deg_rule_reproduced",
  !nrow(results) ||
    identical(as.logical(results$paper_deg), as.logical(expected_paper_deg)),
  if (nrow(results)) sum(results$paper_deg != expected_paper_deg) else 0L,
  0L
)

normalized_sha_after <- sha256_file(normalized_path)
add_check(
  "normalized_rds_unchanged",
  identical(normalized_sha_after, normalized_sha_before),
  normalized_sha_after,
  normalized_sha_before
)

checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "08_mast")
paths <- list(
  manifest = file.path(
    output_dir, paste0(prefix, ".yu_mast_contrast_manifest.tsv")
  ),
  results = file.path(output_dir, paste0(prefix, ".yu_mast_de.tsv.gz")),
  diagnostics = file.path(
    output_dir, paste0(prefix, ".yu_mast_model_diagnostics.tsv")
  ),
  contrast_status = file.path(
    output_dir, paste0(prefix, ".yu_mast_contrast_status.tsv")
  ),
  checks = file.path(output_dir, paste0(prefix, ".yu_mast_de_checks.tsv")),
  artifacts = file.path(
    output_dir, paste0(prefix, ".yu_mast_de_artifacts.tsv")
  ),
  status = file.path(output_dir, paste0(prefix, ".yu_mast_de_status.tsv"))
)

atomic_write_tsv(yu_manifest, paths$manifest)
atomic_write_tsv_gz(results, paths$results)
atomic_write_tsv(diagnostics, paths$diagnostics)
atomic_write_tsv(statuses, paths$contrast_status)
atomic_write_tsv(checks, paths$checks)

artifact_paths <- c(
  paths$manifest, paths$results, paths$diagnostics,
  paths$contrast_status, paths$checks
)
artifacts <- data.frame(
  schema_version = "yu_mast_de_artifacts_v2",
  rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = relative_path(artifact_paths, project_root),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(
    nrow(yu_manifest), nrow(results), nrow(diagnostics),
    nrow(statuses), nrow(checks)
  ),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "yu_mast_de_status_v2",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend,
  run_id = execution$run_id,
  stable_task_id = paste("mast", rds_id, sep = ":"),
  source_rds = source_rel,
  normalized_rds = relative_path(normalized_path, project_root),
  normalized_rds_sha256 = normalized_sha_before,
  normalization_status_sha256 = sha256_file(normalization_status_path),
  analysis_population = analysis_population,
  scientific_script = "scripts/08_run_mast.R",
  scientific_code_bundle_sha256 = sha256_file(
    file.path(project_root, "scripts/08_run_mast.R")
  ),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(rds_manifest_path),
  yu_manifest_sha256 = sha256_file(paths$manifest),
  seurat_version = as.character(utils::packageVersion("Seurat")),
  seuratobject_version = as.character(utils::packageVersion("SeuratObject")),
  mast_version = as.character(utils::packageVersion("MAST")),
  manifest_rows = nrow(yu_manifest),
  estimable_contrasts = sum(yu_manifest$modeling_status == "estimable"),
  completed_contrasts = sum(statuses$terminal_status == "validated_complete"),
  not_estimable_contrasts = sum(statuses$terminal_status == "not_estimable"),
  failed_contrasts = sum(statuses$terminal_status == "failed"),
  result_rows = nrow(results),
  paper_degs = if (nrow(results)) sum(results$paper_deg) else 0L,
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Yu MAST results: ", paths$results, "\n", sep = "")
cat("Yu manifest rows: ", nrow(yu_manifest), "\n", sep = "")
cat(
  "Completed contrasts: ",
  sum(statuses$terminal_status == "validated_complete"), "\n",
  sep = ""
)
cat(
  "Not-estimable contrasts: ",
  sum(statuses$terminal_status == "not_estimable"), "\n",
  sep = ""
)
cat(
  "Failed contrasts: ",
  sum(statuses$terminal_status == "failed"), "\n",
  sep = ""
)
cat("Result rows: ", nrow(results), "\n", sep = "")
cat(
  "Yu-rule DEGs: ",
  if (nrow(results)) sum(results$paper_deg) else 0L,
  "\n",
  sep = ""
)
cat("Yu MAST status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
