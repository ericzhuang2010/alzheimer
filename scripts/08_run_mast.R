#!/usr/bin/env Rscript

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
        "[--input NORMALIZED_RDS --manifest TSV] [--task-mode mast]\n",
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
  if (!identical(out$task_mode, "mast")) stop("--task-mode must be 'mast'", call. = FALSE)
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

# This order avoids the Minerva RcppAnnoy lazy-module failure. MAST is loaded
# afterward; SeuratObject functions below always use explicit namespaces.
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
rds_manifest <- read.delim(rds_manifest_path, check.names = FALSE, stringsAsFactors = FALSE)

if (!is.null(args$manifest_row)) {
  selected <- rds_manifest[rds_manifest$manifest_row == as.integer(args$manifest_row), , drop = FALSE]
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
  backend = "direct", run_id = "manual_mast"
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
  if (nrow(source_candidates) != 1L) stop("Could not map normalized input to one RDS manifest row", call. = FALSE)
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
if (!file.exists(normalized_path)) stop("Normalized RDS is missing: ", normalized_path, call. = FALSE)
normalized_sha_before <- sha256_file(normalized_path)

normalization_status_path <- file.path(
  output_root, "05_normalized", paste0(base_name, ".normalization_status.tsv")
)
if (!file.exists(normalization_status_path)) stop("Normalization status is missing", call. = FALSE)
normalization_status <- data.table::fread(normalization_status_path, data.table = FALSE)
if (nrow(normalization_status) != 1L || normalization_status$validation_status[[1L]] != "validated_complete") {
  stop("Phase 05 normalization must be validated_complete", call. = FALSE)
}

if (!is.null(args$manifest)) {
  contrast_manifest_path <- absolute_path(args$manifest, project_root)
} else {
  candidates <- list.files(
    file.path(output_root, "07_contrasts"),
    pattern = "contrast_manifest[.]tsv$", full.names = TRUE
  )
  candidates <- candidates[!grepl("checks|artifacts|status", basename(candidates))]
  preferred <- candidates[
    basename(candidates) == paste0(execution$execution_stage, "_contrast_manifest.tsv")
  ]
  contrast_manifest_path <- if (length(preferred) == 1L) preferred else candidates
}
if (length(contrast_manifest_path) != 1L || !file.exists(contrast_manifest_path)) {
  stop("Contrast manifest selection must identify one file", call. = FALSE)
}
contrast_manifest <- data.table::fread(contrast_manifest_path, data.table = FALSE)
contrast_manifest <- contrast_manifest[contrast_manifest$rds_id == rds_id, , drop = FALSE]
if (!nrow(contrast_manifest)) stop("No contrast rows apply to ", rds_id, call. = FALSE)

contrast_status_path <- file.path(
  output_root, "07_contrasts",
  paste0(execution$execution_stage, "_contrast_manifest_status.tsv")
)
if (!file.exists(contrast_status_path)) stop("Contrast-manifest status is missing", call. = FALSE)
contrast_status <- data.table::fread(contrast_status_path, data.table = FALSE)
if (nrow(contrast_status) != 1L || contrast_status$validation_status[[1L]] != "validated_complete") {
  stop("Phase 07 contrast manifest must be validated_complete", call. = FALSE)
}

pseudobulk_samples_path <- file.path(
  output_root, "07_pseudobulk", paste0(base_name, ".pseudobulk_samples.tsv")
)
pseudobulk_de_path <- file.path(
  output_root, "07_pseudobulk_de", paste0(tolower(rds_id), ".pseudobulk_de.tsv.gz")
)
if (!file.exists(pseudobulk_samples_path) || !file.exists(pseudobulk_de_path)) {
  stop("Validated Phase 07 pseudobulk samples/results are required", call. = FALSE)
}
pseudobulk_samples <- data.table::fread(
  pseudobulk_samples_path,
  colClasses = c(projid = "character", pseudobulk_id = "character"),
  data.table = FALSE
)
pseudobulk_samples$primary_eligible <- as_logical(pseudobulk_samples$primary_eligible)
pseudobulk_results <- data.table::fread(pseudobulk_de_path, data.table = FALSE)

message("Reading normalized Seurat object: ", normalized_path)
object <- readRDS(normalized_path)
if (!inherits(object, "Seurat") || !isTRUE(methods::validObject(object))) {
  stop("Normalized input is not a valid Seurat object", call. = FALSE)
}
assay <- analysis$normalization$assay %||% "RNA"
if (!assay %in% SeuratObject::Assays(object)) stop("Required RNA assay is absent", call. = FALSE)
if (!"data" %in% SeuratObject::Layers(object[[assay]])) {
  stop("Normalized RNA data layer is absent", call. = FALSE)
}
SeuratObject::DefaultAssay(object) <- assay
metadata <- object[[]]
required_metadata <- c(
  "projid", "cell_type_high_resolution", "cohort_included", "diagnosis",
  "sex", "apoe_group", "nCount_RNA"
)
latent_vars <- unlist(
  analysis$models$mast$latent_vars %||%
    c("nCount_RNA", "age_death_scaled", "pmi_scaled"),
  use.names = FALSE
)
missing_metadata <- setdiff(c(required_metadata, latent_vars), names(metadata))
if (length(missing_metadata)) {
  stop("Normalized metadata fields missing: ", paste(missing_metadata, collapse = ", "), call. = FALSE)
}
projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
metadata$projid <- normalize_id(metadata$projid, projid_width)
metadata$cell_type_high_resolution <- trimws(as.character(metadata$cell_type_high_resolution))
metadata$diagnosis <- as.character(metadata$diagnosis)
metadata$sex <- as.character(metadata$sex)
metadata$apoe_group <- as.character(metadata$apoe_group)
metadata$cohort_included <- as_logical(metadata$cohort_included)

min_pct <- 0.10
logfc_threshold <- 0
paper_log2fc_threshold <- log2(1.3)
result_list <- list()
diagnostic_list <- list()
status_list <- list()

add_status <- function(row, terminal_status, genes_returned = 0L, cells_ad = 0L,
                       cells_nci = 0L, donors_ad = 0L, donors_nci = 0L,
                       message = "") {
  status_list[[length(status_list) + 1L]] <<- data.frame(
    schema_version = "mast_contrast_status_v1", rds_id = rds_id,
    manifest_row = row$manifest_row, contrast_id = row$contrast_id,
    cell_type_high_resolution = row$cell_type_high_resolution,
    contrast_family = row$contrast_family, contrast_name = row$contrast_name,
    paper_matched = as_logical(row$paper_matched),
    eligibility_status = row$eligibility_status,
    terminal_status = terminal_status, genes_returned = as.integer(genes_returned),
    cells_ad = as.integer(cells_ad), cells_nci = as.integer(cells_nci),
    donors_ad = as.integer(donors_ad), donors_nci = as.integer(donors_nci),
    message = message, stringsAsFactors = FALSE
  )
}

for (row_index in seq_len(nrow(contrast_manifest))) {
  row <- contrast_manifest[row_index, , drop = FALSE]
  if (!as_logical(row$paper_matched)) {
    add_status(
      row, "not_applicable", message =
        "Interaction/omnibus rows are primary pseudobulk tests, not paper-style MAST rows"
    )
    next
  }
  if (row$eligibility_status != "eligible") {
    add_status(row, "ineligible", message = row$ineligibility_reason)
    next
  }

  cell_type <- as.character(row$cell_type_high_resolution)
  unit_samples <- pseudobulk_samples[
    pseudobulk_samples$cell_type_high_resolution == cell_type &
      pseudobulk_samples$primary_eligible,
    , drop = FALSE
  ]
  contrast_groups <- strsplit(row$required_groups, ";", fixed = TRUE)[[1L]]
  group_labels <- paste(
    unit_samples$diagnosis, unit_samples$sex, unit_samples$apoe_group, sep = "__"
  )
  unit_samples <- unit_samples[group_labels %in% contrast_groups, , drop = FALSE]
  ad_donors <- unique(unit_samples$projid[unit_samples$diagnosis == "AD"])
  nci_donors <- unique(unit_samples$projid[unit_samples$diagnosis == "NCI"])
  cell_mask <- metadata$cohort_included &
    metadata$cell_type_high_resolution == cell_type &
    ((metadata$diagnosis == "AD" & metadata$projid %in% ad_donors) |
       (metadata$diagnosis == "NCI" & metadata$projid %in% nci_donors))
  cell_mask[is.na(cell_mask)] <- FALSE
  selected_cells <- rownames(metadata)[cell_mask]
  selected_metadata <- metadata[cell_mask, , drop = FALSE]
  cells_ad <- sum(selected_metadata$diagnosis == "AD")
  cells_nci <- sum(selected_metadata$diagnosis == "NCI")
  donors_ad <- length(unique(selected_metadata$projid[selected_metadata$diagnosis == "AD"]))
  donors_nci <- length(unique(selected_metadata$projid[selected_metadata$diagnosis == "NCI"]))

  expected_cells_ad <- sum(unit_samples$nuclei[unit_samples$diagnosis == "AD"])
  expected_cells_nci <- sum(unit_samples$nuclei[unit_samples$diagnosis == "NCI"])
  counts_match <- cells_ad == expected_cells_ad && cells_nci == expected_cells_nci
  donors_match <- donors_ad == row$numerator_donors && donors_nci == row$denominator_donors
  covariates_complete <- !anyNA(selected_metadata[, latent_vars, drop = FALSE]) &&
    all(vapply(selected_metadata[, latent_vars, drop = FALSE], function(x) {
      all(is.finite(as.numeric(x)))
    }, logical(1)))
  if (!counts_match || !donors_match || !covariates_complete) {
    message_text <- paste(
      c(
        if (!counts_match) "cell counts disagree with pseudobulk samples",
        if (!donors_match) "donor counts disagree with contrast manifest",
        if (!covariates_complete) "latent covariates are incomplete/nonfinite"
      ),
      collapse = "; "
    )
    add_status(
      row, "failed", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "mast_model_diagnostics_v1", rds_id = rds_id,
      manifest_row = row$manifest_row, contrast_id = row$contrast_id,
      cell_type_high_resolution = cell_type, contrast_name = row$contrast_name,
      cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci,
      tested_genes = 0L, latent_vars = paste(latent_vars, collapse = ";"),
      min_pct = min_pct, logfc_threshold = logfc_threshold,
      spearman_logfc_with_pseudobulk = NA_real_, overlap_genes = 0L,
      model_status = "failed", message = message_text,
      stringsAsFactors = FALSE
    )
    next
  }

  message(
    "Running MAST: ", cell_type, " / ", row$contrast_name,
    " (AD cells=", cells_ad, ", NCI cells=", cells_nci, ")"
  )
  subobject <- object[, selected_cells, drop = FALSE]
  SeuratObject::DefaultAssay(subobject) <- assay
  marker_error <- NULL
  markers <- tryCatch(
    Seurat::FindMarkers(
      object = subobject, ident.1 = "AD", ident.2 = "NCI",
      group.by = "diagnosis", assay = assay, slot = "data",
      test.use = "MAST", min.pct = min_pct,
      logfc.threshold = logfc_threshold, latent.vars = latent_vars,
      densify = FALSE, verbose = FALSE
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
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "mast_model_diagnostics_v1", rds_id = rds_id,
      manifest_row = row$manifest_row, contrast_id = row$contrast_id,
      cell_type_high_resolution = cell_type, contrast_name = row$contrast_name,
      cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci,
      tested_genes = 0L, latent_vars = paste(latent_vars, collapse = ";"),
      min_pct = min_pct, logfc_threshold = logfc_threshold,
      spearman_logfc_with_pseudobulk = NA_real_, overlap_genes = 0L,
      model_status = "failed", message = marker_error,
      stringsAsFactors = FALSE
    )
    next
  }

  logfc_column <- intersect(c("avg_log2FC", "avg_logFC"), names(markers))
  if (length(logfc_column) != 1L || !all(c("p_val", "pct.1", "pct.2") %in% names(markers))) {
    message_text <- "FindMarkers returned an unsupported result schema"
    add_status(
      row, "failed", cells_ad = cells_ad, cells_nci = cells_nci,
      donors_ad = donors_ad, donors_nci = donors_nci, message = message_text
    )
    next
  }
  gene <- rownames(markers)
  p_value <- as.numeric(markers$p_val)
  fdr <- stats::p.adjust(p_value, method = "BH")
  logfc <- as.numeric(markers[[logfc_column]])
  result <- data.frame(
    schema_version = "mast_de_results_v1", rds_id = rds_id,
    source_rds = source_rel, normalized_rds = sub(paste0("^", project_root, "/?"), "", normalized_path),
    cell_type_high_resolution = cell_type,
    manifest_row = row$manifest_row, contrast_id = row$contrast_id,
    contrast_family = row$contrast_family, contrast_name = row$contrast_name,
    gene = gene, logFC = logfc, pct_ad = as.numeric(markers$pct.1),
    pct_nci = as.numeric(markers$pct.2), p_value = p_value,
    fdr_bh_within_contrast = fdr,
    paper_effect_threshold_log2 = paper_log2fc_threshold,
    paper_deg = fdr < 0.05 & abs(logfc) > paper_log2fc_threshold &
      (as.numeric(markers$pct.1) >= min_pct | as.numeric(markers$pct.2) >= min_pct),
    cells_ad = cells_ad, cells_nci = cells_nci,
    donors_ad = donors_ad, donors_nci = donors_nci,
    latent_vars = paste(latent_vars, collapse = ";"),
    stringsAsFactors = FALSE
  )

  pb <- pseudobulk_results[
    pseudobulk_results$cell_type_high_resolution == cell_type &
      pseudobulk_results$contrast_name == row$contrast_name,
    c("gene", "logFC", "p_value", "fdr_bh_within_contrast"),
    drop = FALSE
  ]
  names(pb) <- c("gene", "pseudobulk_logFC", "pseudobulk_p_value", "pseudobulk_fdr")
  pb_index <- match(result$gene, pb$gene)
  overlap <- !is.na(pb_index)
  result$pseudobulk_logFC <- pb$pseudobulk_logFC[pb_index]
  result$pseudobulk_fdr <- pb$pseudobulk_fdr[pb_index]
  result$direction_concordant_with_pseudobulk <- ifelse(
    overlap, sign(result$logFC) == sign(result$pseudobulk_logFC), NA
  )
  correlation <- if (sum(overlap) >= 3L) {
    suppressWarnings(stats::cor(
      result$logFC[overlap], result$pseudobulk_logFC[overlap],
      method = "spearman", use = "complete.obs"
    ))
  } else {
    NA_real_
  }
  result_list[[length(result_list) + 1L]] <- result
  diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
    schema_version = "mast_model_diagnostics_v1", rds_id = rds_id,
    manifest_row = row$manifest_row, contrast_id = row$contrast_id,
    cell_type_high_resolution = cell_type, contrast_name = row$contrast_name,
    cells_ad = cells_ad, cells_nci = cells_nci,
    donors_ad = donors_ad, donors_nci = donors_nci,
    tested_genes = nrow(result), latent_vars = paste(latent_vars, collapse = ";"),
    min_pct = min_pct, logfc_threshold = logfc_threshold,
    spearman_logfc_with_pseudobulk = correlation, overlap_genes = sum(overlap),
    model_status = "fitted", message = "",
    stringsAsFactors = FALSE
  )
  add_status(
    row, "validated_complete", genes_returned = nrow(result),
    cells_ad = cells_ad, cells_nci = cells_nci,
    donors_ad = donors_ad, donors_nci = donors_nci
  )
}

statuses <- as.data.frame(data.table::rbindlist(status_list, fill = TRUE, use.names = TRUE))
statuses <- statuses[order(statuses$manifest_row), , drop = FALSE]
diagnostics <- as.data.frame(data.table::rbindlist(
  diagnostic_list, fill = TRUE, use.names = TRUE
))
if (length(result_list)) {
  results <- as.data.frame(data.table::rbindlist(result_list, fill = TRUE, use.names = TRUE))
} else {
  results <- data.frame(
    schema_version = character(), rds_id = character(), source_rds = character(),
    normalized_rds = character(), cell_type_high_resolution = character(),
    manifest_row = integer(), contrast_id = character(), contrast_family = character(),
    contrast_name = character(), gene = character(), logFC = numeric(),
    pct_ad = numeric(), pct_nci = numeric(), p_value = numeric(),
    fdr_bh_within_contrast = numeric(), paper_effect_threshold_log2 = numeric(),
    paper_deg = logical(), cells_ad = integer(), cells_nci = integer(),
    donors_ad = integer(), donors_nci = integer(), latent_vars = character(),
    pseudobulk_logFC = numeric(), pseudobulk_fdr = numeric(),
    direction_concordant_with_pseudobulk = logical(), stringsAsFactors = FALSE
  )
}

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "mast_de_checks_v1", rds_id = rds_id,
    check = check, passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
paper_rows <- as_logical(contrast_manifest$paper_matched)
eligible_paper <- paper_rows & contrast_manifest$eligibility_status == "eligible"
add_check("one_status_per_manifest_row", nrow(statuses) == nrow(contrast_manifest) && !anyDuplicated(statuses$manifest_row), nrow(statuses), nrow(contrast_manifest))
add_check("eligible_paper_rows_completed", sum(statuses$terminal_status == "validated_complete") == sum(eligible_paper), sum(statuses$terminal_status == "validated_complete"), sum(eligible_paper))
add_check("ineligible_paper_rows_explicit", sum(statuses$terminal_status == "ineligible") == sum(paper_rows & !eligible_paper), sum(statuses$terminal_status == "ineligible"), sum(paper_rows & !eligible_paper))
add_check("nonpaper_rows_not_applicable", sum(statuses$terminal_status == "not_applicable") == sum(!paper_rows), sum(statuses$terminal_status == "not_applicable"), sum(!paper_rows))
add_check("no_failed_contrasts", !any(statuses$terminal_status == "failed"), sum(statuses$terminal_status == "failed"), 0L)
result_keys <- if (nrow(results)) paste(results$cell_type_high_resolution, results$contrast_id, results$gene, sep = "\r") else character()
add_check("result_keys_unique", !anyDuplicated(result_keys), anyDuplicated(result_keys), 0L)
add_check("p_values_in_range", !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1), if (nrow(results)) sum(!is.finite(results$p_value) | results$p_value < 0 | results$p_value > 1) else 0L, 0L)
add_check("fdr_in_range", !nrow(results) || all(is.finite(results$fdr_bh_within_contrast) & results$fdr_bh_within_contrast >= 0 & results$fdr_bh_within_contrast <= 1), if (nrow(results)) sum(!is.finite(results$fdr_bh_within_contrast) | results$fdr_bh_within_contrast < 0 | results$fdr_bh_within_contrast > 1) else 0L, 0L)
add_check("detection_threshold_respected", !nrow(results) || all(results$pct_ad >= min_pct | results$pct_nci >= min_pct), if (nrow(results)) sum(results$pct_ad < min_pct & results$pct_nci < min_pct) else 0L, 0L)
normalized_sha_after <- sha256_file(normalized_path)
add_check("normalized_rds_unchanged", identical(normalized_sha_after, normalized_sha_before), normalized_sha_after, normalized_sha_before)
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "08_mast")
prefix <- tolower(rds_id)
paths <- list(
  results = file.path(output_dir, paste0(prefix, ".mast_de.tsv.gz")),
  diagnostics = file.path(output_dir, paste0(prefix, ".mast_model_diagnostics.tsv")),
  contrast_status = file.path(output_dir, paste0(prefix, ".mast_contrast_status.tsv")),
  checks = file.path(output_dir, paste0(prefix, ".mast_de_checks.tsv")),
  artifacts = file.path(output_dir, paste0(prefix, ".mast_de_artifacts.tsv")),
  status = file.path(output_dir, paste0(prefix, ".mast_de_status.tsv"))
)
atomic_write_tsv_gz(results, paths$results)
atomic_write_tsv(diagnostics, paths$diagnostics)
atomic_write_tsv(statuses, paths$contrast_status)
atomic_write_tsv(checks, paths$checks)
artifact_paths <- c(paths$results, paths$diagnostics, paths$contrast_status, paths$checks)
artifacts <- data.frame(
  schema_version = "mast_de_artifacts_v1", rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(results), nrow(diagnostics), nrow(statuses), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "mast_de_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = paste("mast", rds_id, sep = ":"),
  source_rds = source_rel,
  normalized_rds = sub(paste0("^", project_root, "/?"), "", normalized_path),
  normalized_rds_sha256 = normalized_sha_before,
  scientific_script = "scripts/08_run_mast.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/08_run_mast.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(rds_manifest_path),
  contrast_manifest_sha256 = sha256_file(contrast_manifest_path),
  pseudobulk_samples_sha256 = sha256_file(pseudobulk_samples_path),
  pseudobulk_de_sha256 = sha256_file(pseudobulk_de_path),
  seurat_version = as.character(utils::packageVersion("Seurat")),
  mast_version = as.character(utils::packageVersion("MAST")),
  manifest_rows = nrow(contrast_manifest),
  eligible_paper_contrasts = sum(eligible_paper),
  completed_contrasts = sum(statuses$terminal_status == "validated_complete"),
  ineligible_contrasts = sum(statuses$terminal_status == "ineligible"),
  not_applicable_contrasts = sum(statuses$terminal_status == "not_applicable"),
  failed_contrasts = sum(statuses$terminal_status == "failed"),
  result_rows = nrow(results), paper_degs = if (nrow(results)) sum(results$paper_deg) else 0L,
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("MAST results: ", paths$results, "\n", sep = "")
cat("Manifest rows: ", nrow(contrast_manifest), "\n", sep = "")
cat("Eligible paper contrasts: ", sum(eligible_paper), "\n", sep = "")
cat("Completed contrasts: ", sum(statuses$terminal_status == "validated_complete"), "\n", sep = "")
cat("Result rows: ", nrow(results), "\n", sep = "")
cat("Paper-rule DEGs: ", if (nrow(results)) sum(results$paper_deg) else 0L, "\n", sep = "")
cat("MAST status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
