#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL,
    execution_config = NULL,
    manifest_row = NULL,
    rds_id = NULL,
    task_mode = "audit"
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
        "Usage: Rscript scripts/01_audit_seurat_inputs.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--task-mode audit]\n",
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
  if (!identical(out$task_mode, "audit")) {
    stop("--task-mode must be 'audit'", call. = FALSE)
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
  kib <- suppressWarnings(as.numeric(gsub("[^0-9.]", "", line[[1L]])))
  kib / (1024^2)
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

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "Matrix", "SeuratObject", "data.table")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

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
metadata_path <- absolute_path(config$inputs$cell_metadata_tsv, project_root)
output_root <- absolute_path(config$outputs$root, project_root)

if (!file.exists(analysis_path)) stop("Analysis config does not exist: ", analysis_path, call. = FALSE)
if (!file.exists(manifest_path)) stop("Manifest does not exist: ", manifest_path, call. = FALSE)
if (!file.exists(metadata_path)) stop("Cell metadata does not exist: ", metadata_path, call. = FALSE)

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
input_rel <- as.character(selected$input_rds[[1L]])
input_path <- absolute_path(input_rel, project_root)
if (!file.exists(input_path)) stop("Input RDS does not exist: ", input_path, call. = FALSE)
base_name <- sub("\\.[Rr][Dd][Ss]$", "", basename(input_path))
audit_dir <- file.path(output_root, "01_audit")
audit_path <- file.path(audit_dir, paste0(base_name, ".audit.tsv"))
features_path <- file.path(audit_dir, paste0(base_name, ".features.tsv.gz"))
cell_types_path <- file.path(audit_dir, paste0(base_name, ".cell_types.tsv"))
status_path <- file.path(audit_dir, paste0(base_name, ".audit_status.tsv"))

message("Reading Seurat object: ", input_path)
object <- readRDS(input_path)
object_is_seurat <- inherits(object, "Seurat")
if (!object_is_seurat) stop("Input is not a Seurat object: ", input_path, call. = FALSE)

assay <- analysis$normalization$assay %||% "RNA"
assays <- SeuratObject::Assays(object)
if (!assay %in% assays) stop("Required assay is absent: ", assay, call. = FALSE)
counts <- get_assay_layer(object, assay, "counts")
if (is.null(counts)) stop("Raw counts layer is absent from assay ", assay, call. = FALSE)
data_layer <- get_assay_layer(object, assay, "data")

cells <- colnames(counts)
features <- rownames(counts)
object_metadata <- object[[]]
required_object_metadata <- c("projid", "cell_type_high_resolution")
object_metadata_present <- required_object_metadata %in% colnames(object_metadata)

projid_width <- as.integer(analysis$cohort$projid_width %||% 8L)
object_projids <- if (object_metadata_present[[1L]]) {
  normalize_id(object_metadata$projid, projid_width)
} else {
  rep(NA_character_, length(cells))
}
object_cell_types <- if (object_metadata_present[[2L]]) {
  trimws(as.character(object_metadata$cell_type_high_resolution))
} else {
  rep(NA_character_, length(cells))
}
object_cell_types[object_cell_types == ""] <- NA_character_

is_sparse <- inherits(counts, "sparseMatrix")
count_values <- if (is_sparse && "x" %in% slotNames(counts)) counts@x else counts[]
counts_finite <- all(is.finite(count_values))
counts_nonnegative <- counts_finite && all(count_values >= 0)
counts_integer <- counts_finite && all(abs(count_values - round(count_values)) < 1e-8)
counts_nnz <- if (is_sparse && "x" %in% slotNames(counts)) length(counts@x) else sum(counts != 0)
counts_total <- sum(count_values)

if (is_sparse && "i" %in% slotNames(counts)) {
  nuclei_detected <- tabulate(counts@i + 1L, nbins = nrow(counts))
} else {
  nuclei_detected <- rowSums(counts != 0)
}
feature_totals <- if (is_sparse) Matrix::rowSums(counts) else rowSums(counts)

expected_mt <- unlist(analysis$mitochondrial_features$mtdna_protein_genes, use.names = FALSE)
observed_mt <- intersect(expected_mt, features)
missing_mt <- setdiff(expected_mt, features)

master_required <- c(
  "projid", "cell_type_high_resolution", "barcode", "cell_type_broad"
)
message("Reading master metadata columns: ", paste(master_required, collapse = ", "))
master <- data.table::fread(
  metadata_path,
  select = master_required,
  colClasses = "character",
  showProgress = FALSE
)
master <- master[barcode %chin% cells]
master_duplicate_barcodes <- sum(duplicated(master$barcode))
master_index <- match(cells, master$barcode)
master_missing_barcodes <- sum(is.na(master_index))
matched_master <- master[master_index]
master_projids <- normalize_id(matched_master$projid, projid_width)
master_cell_types <- trimws(as.character(matched_master$cell_type_high_resolution))
projid_mismatches <- sum(
  is.na(object_projids) | is.na(master_projids) | object_projids != master_projids,
  na.rm = TRUE
)
cell_type_mismatches <- sum(
  is.na(object_cell_types) | is.na(master_cell_types) | object_cell_types != master_cell_types,
  na.rm = TRUE
)
master_broad_types <- sort(unique(stats::na.omit(matched_master$cell_type_broad)))

expected_features <- as.integer(selected$expected_features[[1L]])
expected_cells <- as.integer(selected$expected_cells[[1L]])
expected_donors <- as.integer(selected$expected_donors[[1L]])
expected_cell_types <- as.integer(selected$expected_cell_types[[1L]])
observed_donors <- data.table::uniqueN(object_projids[!is.na(object_projids)])
observed_cell_types <- data.table::uniqueN(object_cell_types[!is.na(object_cell_types)])

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    check = check,
    passed = isTRUE(passed),
    observed = as.character(observed),
    expected = as.character(expected),
    stringsAsFactors = FALSE
  )
}
add_check("seurat_object", object_is_seurat, paste(class(object), collapse = ";"), "Seurat")
add_check("feature_count", nrow(counts) == expected_features, nrow(counts), expected_features)
add_check("nucleus_count", ncol(counts) == expected_cells, ncol(counts), expected_cells)
add_check("counts_sparse", is_sparse, paste(class(counts), collapse = ";"), "sparseMatrix")
add_check("counts_finite", counts_finite, counts_finite, TRUE)
add_check("counts_nonnegative", counts_nonnegative, counts_nonnegative, TRUE)
add_check("counts_integer_valued", counts_integer, counts_integer, TRUE)
add_check("feature_names_nonempty", !anyNA(features) && all(nzchar(features)), sum(!nzchar(features)), 0)
add_check("feature_names_unique", !anyDuplicated(features), anyDuplicated(features), 0)
add_check("barcodes_unique", !anyDuplicated(cells), anyDuplicated(cells), 0)
add_check("metadata_rownames_match", identical(rownames(object_metadata), cells),
  identical(rownames(object_metadata), cells), TRUE
)
add_check("required_object_metadata", all(object_metadata_present),
  paste(required_object_metadata[object_metadata_present], collapse = ";"),
  paste(required_object_metadata, collapse = ";")
)
add_check("donor_ids_complete", !anyNA(object_projids), sum(is.na(object_projids)), 0)
add_check("donor_count", observed_donors == expected_donors, observed_donors, expected_donors)
add_check("cell_types_complete", !anyNA(object_cell_types), sum(is.na(object_cell_types)), 0)
add_check("cell_type_count", observed_cell_types == expected_cell_types,
  observed_cell_types, expected_cell_types
)
add_check("mtdna_protein_genes", !length(missing_mt),
  paste(observed_mt, collapse = ";"), paste(expected_mt, collapse = ";")
)
add_check("master_barcode_coverage", master_missing_barcodes == 0L,
  length(cells) - master_missing_barcodes, length(cells)
)
add_check("master_barcodes_unique", master_duplicate_barcodes == 0L,
  master_duplicate_barcodes, 0
)
add_check("master_projid_agreement", projid_mismatches == 0L, projid_mismatches, 0)
add_check("master_cell_type_agreement", cell_type_mismatches == 0L, cell_type_mismatches, 0)
check_table <- do.call(rbind, checks)
failed_checks <- check_table$check[!check_table$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

layer_names <- tryCatch(
  SeuratObject::Layers(object[[assay]]),
  error = function(e) character()
)
command_names <- tryCatch(names(object@commands), error = function(e) character())
reduction_names <- tryCatch(SeuratObject::Reductions(object), error = function(e) character())
graph_names <- tryCatch(SeuratObject::Graphs(object), error = function(e) character())

audit <- data.frame(
  schema_version = "rds_audit_v1",
  rds_id = rds_id,
  stable_task_id = paste0("audit:", rds_id),
  source_rds = input_rel,
  source_rds_bytes = file.info(input_path)$size,
  source_rds_sha256 = sha256_file(input_path),
  object_class = paste(class(object), collapse = ";"),
  object_version = as.character(object@version),
  seurat_version = as.character(utils::packageVersion("Seurat")),
  seurat_object_version = as.character(utils::packageVersion("SeuratObject")),
  assays = paste(assays, collapse = ";"),
  default_assay = SeuratObject::DefaultAssay(object),
  audited_assay = assay,
  assay_class = paste(class(object[[assay]]), collapse = ";"),
  layers = paste(layer_names, collapse = ";"),
  raw_counts_class = paste(class(counts), collapse = ";"),
  raw_counts_sparse = is_sparse,
  raw_counts_integer_valued = counts_integer,
  raw_counts_nonnegative = counts_nonnegative,
  raw_counts_nnz = counts_nnz,
  raw_counts_total = counts_total,
  normalized_data_present = !is.null(data_layer),
  normalized_data_dimensions = if (is.null(data_layer)) NA_character_ else paste(dim(data_layer), collapse = "x"),
  features = nrow(counts),
  nuclei = ncol(counts),
  donors = observed_donors,
  fine_cell_types = observed_cell_types,
  metadata_fields = paste(colnames(object_metadata), collapse = ";"),
  master_metadata_rows_matched = length(cells) - master_missing_barcodes,
  master_metadata_missing_barcodes = master_missing_barcodes,
  master_metadata_duplicate_barcodes = master_duplicate_barcodes,
  master_projid_mismatches = projid_mismatches,
  master_cell_type_mismatches = cell_type_mismatches,
  master_broad_cell_types = paste(master_broad_types, collapse = ";"),
  mtdna_protein_genes_observed = length(observed_mt),
  mtdna_protein_genes_missing = paste(missing_mt, collapse = ";"),
  reductions = paste(reduction_names, collapse = ";"),
  graphs = paste(graph_names, collapse = ";"),
  commands = paste(command_names, collapse = ";"),
  normalize_command_present = any(grepl("NormalizeData", command_names, fixed = TRUE)),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  stringsAsFactors = FALSE
)

feature_table <- data.frame(
  feature_index = seq_along(features),
  feature = features,
  total_raw_counts = as.numeric(feature_totals),
  nuclei_detected = as.integer(nuclei_detected),
  is_mtdna_protein_gene = features %in% expected_mt,
  stringsAsFactors = FALSE
)

cell_type_dt <- data.table::data.table(
  fine_cell_type = object_cell_types,
  projid = object_projids
)
cell_type_table <- cell_type_dt[, .(
  nuclei = .N,
  donors = data.table::uniqueN(projid[!is.na(projid)]),
  missing_donor_ids = sum(is.na(projid))
), by = fine_cell_type]
data.table::setorder(cell_type_table, fine_cell_type)

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) "phase1_local_manual" else "manual_audit"
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) stop("Execution config does not exist: ", execution_path, call. = FALSE)
  execution_config <- yaml::read_yaml(execution_path)
  execution_phase <- execution_config$execution$execution_phase %||% execution_phase
  backend <- execution_config$execution$backend %||% backend
  run_id <- execution_config$execution$run_id %||% run_id
}

status <- data.frame(
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = paste0("audit:", rds_id),
  source_rds = input_rel,
  scientific_script = "scripts/01_audit_seurat_inputs.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/01_audit_seurat_inputs.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)

atomic_write_tsv(audit, audit_path)
atomic_write_tsv_gz(feature_table, features_path)
atomic_write_tsv(cell_type_table, cell_types_path)
atomic_write_tsv(status, status_path)

cat("Audit summary: ", audit_path, "\n", sep = "")
cat("Feature inventory: ", features_path, "\n", sep = "")
cat("Cell-type summary: ", cell_types_path, "\n", sep = "")
cat("Audit status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
