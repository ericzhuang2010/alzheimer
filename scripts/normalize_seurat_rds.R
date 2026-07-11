#!/usr/bin/env Rscript


args <- commandArgs(trailingOnly = TRUE)

input_dir <- "data/processed"
output_dir <- file.path(input_dir, "normalized")
assay_arg <- "RNA"
scale_factor <- 10000
force <- FALSE
input_files <- character()

usage <- function() {
  cat(
    "Usage:\n",
    "  Rscript scripts/normalize_seurat_rds.R [options] [file1.rds file2.rds ...]\n\n",
    "Options:\n",
    "  --input-dir DIR      Directory to scan when no files are given. Default: data/processed\n",
    "  --output-dir DIR     Directory for normalized RDS files. Default: data/processed/normalized\n",
    "  --assay ASSAY        Assay to normalize. Default: RNA, falling back to DefaultAssay(object)\n",
    "  --scale-factor N     Seurat LogNormalize scale factor. Default: 10000\n",
    "  --force              Overwrite existing normalized files\n",
    "  --help               Show this help\n\n",
    "This script keeps raw counts in the counts slot/layer and writes log-normalized\n",
    "values to the Seurat data slot/layer using NormalizeData().\n",
    sep = ""
  )
}

i <- 1
while (i <= length(args)) {
  arg <- args[[i]]
  if (arg == "--help" || arg == "-h") {
    usage()
    quit(status = 0)
  } else if (arg == "--input-dir") {
    i <- i + 1
    input_dir <- args[[i]]
  } else if (arg == "--output-dir") {
    i <- i + 1
    output_dir <- args[[i]]
  } else if (arg == "--assay") {
    i <- i + 1
    assay_arg <- args[[i]]
  } else if (arg == "--scale-factor") {
    i <- i + 1
    scale_factor <- as.numeric(args[[i]])
  } else if (arg == "--force") {
    force <- TRUE
  } else {
    input_files <- c(input_files, arg)
  }
  i <- i + 1
}

if (length(input_files) == 0) {
  input_files <- list.files(input_dir, pattern = "\\.rds$", full.names = TRUE, ignore.case = TRUE)
  input_files <- input_files[!grepl("_normalized\\.rds$", input_files, ignore.case = TRUE)]
}

if (length(input_files) == 0) {
  stop("No .rds files found to normalize.")
}

if (!requireNamespace("Seurat", quietly = TRUE)) {
  stop(
    "The R package 'Seurat' is required for NormalizeData().\n",
    "Install it in R with: install.packages('Seurat')"
  )
}

suppressPackageStartupMessages({
  library(Seurat)
})

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

matrix_summary <- function(obj, assay, slot_name) {
  mat <- tryCatch(
    GetAssayData(obj, assay = assay, slot = slot_name),
    error = function(e) NULL
  )
  if (is.null(mat)) {
    return("unavailable")
  }
  dims <- paste(dim(mat), collapse = " x ")
  nnz <- if (inherits(mat, "sparseMatrix")) length(mat@x) else sum(mat != 0)
  paste0(dims, ", nonzero=", format(nnz, big.mark = ","))
}

normalize_one <- function(input_file) {
  input_file <- normalizePath(input_file, mustWork = TRUE)
  output_file <- file.path(
    output_dir,
    sub("\\.rds$", "_normalized.rds", basename(input_file), ignore.case = TRUE)
  )

  if (file.exists(output_file) && !force) {
    message("Skipping existing output: ", output_file)
    return(invisible(output_file))
  }

  message("\nReading: ", input_file)
  obj <- readRDS(input_file)

  if (!inherits(obj, "Seurat")) {
    stop("Input is not a Seurat object: ", input_file)
  }

  assay <- assay_arg
  if (!assay %in% Assays(obj)) {
    assay <- DefaultAssay(obj)
    message("Requested assay not found; using DefaultAssay(object): ", assay)
  }
  DefaultAssay(obj) <- assay

  message("Object: ", ncol(obj), " cells x ", nrow(obj), " features")
  message("Assay: ", assay)
  message("Before counts: ", matrix_summary(obj, assay, "counts"))
  message("Before data:   ", matrix_summary(obj, assay, "data"))

  obj <- NormalizeData(
    object = obj,
    assay = assay,
    normalization.method = "LogNormalize",
    scale.factor = scale_factor,
    verbose = TRUE
  )

  message("After data:    ", matrix_summary(obj, assay, "data"))
  saveRDS(obj, output_file)
  message("Wrote: ", output_file)

  invisible(output_file)
}

for (input_file in input_files) {
  normalize_one(input_file)
}
