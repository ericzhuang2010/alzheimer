#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_cli <- function(args) {
  out <- list(config = NULL, network = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript 11_prepare_rimbanet_expression.R --config FILE --network NAME\n")
      quit(status = 0L)
    }
    if (i == length(args)) stop("Incomplete argument: ", key)
    value <- args[[i + 1L]]
    if (key == "--config") out$config <- value
    else if (key == "--network") out$network <- value
    else stop("Unknown argument: ", key)
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$network)) {
    stop("--config and --network are required")
  }
  out
}

gzip_executable <- function() {
  executable <- unname(Sys.which("gzip"))
  if (!nzchar(executable)) {
    stop("gzip executable is required for compressed TSV input/output")
  }
  executable
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  compressed <- grepl("[.]gz$", path)
  temporary_plain <- file.path(
    dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  temporary_gzip <- paste0(temporary_plain, ".gz")
  on.exit(unlink(c(temporary_plain, temporary_gzip)), add = TRUE)
  data.table::fwrite(
    x, temporary_plain, sep = "\t", na = "NA", quote = FALSE
  )
  published <- temporary_plain
  if (compressed) {
    status <- system2(
      gzip_executable(), c("-n", "-f", "--", shQuote(temporary_plain))
    )
    if (status != 0L || !file.exists(temporary_gzip)) {
      stop("gzip compression failed: ", path)
    }
    published <- temporary_gzip
  }
  if (!file.rename(published, path)) stop("Atomic rename failed: ", path)
}

sha256_file <- function(path) {
  digest::digest(file = path, algo = "sha256", serialize = FALSE)
}

resolve_config_path <- function(value, project_root) {
  if (grepl("^/", value)) value else file.path(project_root, value)
}

provenance_paths <- function(paths, project_root) {
  resolved <- normalizePath(paths, mustWork = TRUE)
  prefix <- paste0(project_root, "/")
  ifelse(startsWith(resolved, prefix), substring(resolved, nchar(prefix) + 1L), resolved)
}
fread_tsv <- function(path) {
  if (grepl("[.]gz$", path)) {
    return(data.table::fread(
      cmd = paste(shQuote(gzip_executable()), "-dc --", shQuote(path)),
      sep = "\t",
      data.table = FALSE
    ))
  }
  data.table::fread(path, sep = "\t", data.table = FALSE)
}


args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "edgeR")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
if (!identical(config$schema_version, "seaad_rimbanet_config_v1")) {
  stop("Unsupported config schema")
}
networks <- unlist(config$networks)
if (!args$network %in% networks) stop("Unknown network: ", args$network)
generated_root <- config$storage$generated_output_root
if (is.null(generated_root)) generated_root <- config$output_root
generated_root <- resolve_config_path(generated_root, project_root)
dir.create(generated_root, recursive = TRUE, showWarnings = FALSE)
output_root <- normalizePath(generated_root, mustWork = TRUE)

input_dir <- resolve_config_path(config$inputs$pseudobulk_directory, project_root)
counts_path <- file.path(
  input_dir, paste0(args$network, config$expression$counts_suffix)
)
samples_path <- file.path(
  input_dir, paste0(args$network, config$expression$samples_suffix)
)
if (!file.exists(counts_path) || !file.exists(samples_path)) {
  stop("Missing VH05 broad pseudobulk inputs for ", args$network)
}

counts_table <- fread_tsv(counts_path)
samples <- fread_tsv(samples_path)
required_sample_cols <- c(
  "pseudobulk_id", "donor_id", "broad_network", "nuclei", "diagnosis",
  "sex", "apoe_group", "age_death_scaled", "pmi_scaled", "study"
)
if (!all(required_sample_cols %in% names(samples))) {
  stop("Sample manifest lacks required columns")
}
if (!all(c("feature_index", "source_symbol") %in% names(counts_table))) {
  stop("Count matrix lacks feature_index/source_symbol")
}
if (anyDuplicated(counts_table$source_symbol)) {
  stop("Duplicate source symbols must be resolved before network preparation")
}
if (anyDuplicated(samples$donor_id) || anyDuplicated(samples$pseudobulk_id)) {
  stop("Sample/donor identifiers must be unique")
}

minimum_nuclei <- as.integer(config$cohort$primary_min_nuclei)
samples <- samples[samples$nuclei >= minimum_nuclei, , drop = FALSE]
if (nrow(samples) < 10L) stop("Fewer than 10 eligible donors")
sample_ids <- as.character(samples$pseudobulk_id)
if (!all(sample_ids %in% names(counts_table))) {
  stop("Count matrix/sample manifest identifiers differ")
}
raw_counts <- as.matrix(counts_table[, sample_ids, drop = FALSE])
storage.mode(raw_counts) <- "double"
if (any(!is.finite(raw_counts)) || any(raw_counts < 0)) stop("Invalid counts")

dge_all <- edgeR::DGEList(counts = raw_counts)
cpm_values <- edgeR::cpm(dge_all, log = FALSE)
detected <- rowSums(cpm_values >= as.numeric(config$expression$cpm_minimum))
minimum_donors <- ceiling(
  as.numeric(config$expression$minimum_donor_fraction) * ncol(raw_counts)
)
unique_values <- apply(raw_counts, 1L, function(x) length(unique(x)))
symbols <- as.character(counts_table$source_symbol)
base_pass <- detected >= minimum_donors &
  unique_values >= as.integer(config$expression$minimum_unique_values) &
  nzchar(symbols) & symbols != "NA"

if (sum(base_pass) < 3L) stop("Expression filters retained fewer than three genes")
filtered_counts <- raw_counts[base_pass, , drop = FALSE]
dge <- edgeR::DGEList(counts = filtered_counts)
dge <- edgeR::calcNormFactors(dge, method = "TMM")
normalized <- edgeR::cpm(
  dge, log = TRUE, prior.count = as.numeric(config$expression$prior_count)
)

samples$log10_nuclei <- log10(pmax(as.numeric(samples$nuclei), 1))
design <- stats::model.matrix(
  stats::as.formula(config$expression$residual_formula), data = samples
)
if (qr(design)$rank != ncol(design)) {
  stop("Residualization design matrix is rank deficient")
}
fit <- stats::lm.fit(x = design, y = t(normalized))
adjusted <- t(fit$residuals)
rownames(adjusted) <- rownames(normalized)
colnames(adjusted) <- colnames(normalized)
residual_variance <- apply(adjusted, 1L, stats::var)

cap <- if (identical(args$network, config$cohort$pilot_network)) {
  as.integer(config$expression$pilot_max_genes)
} else {
  as.integer(config$expression$production_max_genes)
}
filtered_symbols <- symbols[base_pass]
source_indices <- as.integer(counts_table$feature_index[base_pass])
ordering <- order(-residual_variance, source_indices, na.last = NA)
selected_indices <- ordering[seq_len(min(length(ordering), cap))]
force_include <- unlist(config$expression$force_include_symbols)
if (length(force_include)) {
  selected_indices <- unique(c(
    selected_indices, which(filtered_symbols %in% force_include)
  ))
}
selected_indices <- selected_indices[
  order(source_indices[selected_indices], method = "radix")
]
selected_symbols <- filtered_symbols[selected_indices]

gene_manifest <- data.frame(
  feature_index = as.integer(counts_table$feature_index),
  source_symbol = symbols,
  eligible_donors_detected = detected,
  unique_count_values = unique_values,
  expression_filter_pass = base_pass,
  residual_variance = NA_real_,
  selected_network_gene = FALSE,
  exclusion_reason = ifelse(
    detected < minimum_donors, "low_expression",
    ifelse(unique_values < as.integer(config$expression$minimum_unique_values),
           "insufficient_unique_values",
           ifelse(!nzchar(symbols) | symbols == "NA", "invalid_symbol", "variance_cap"))
  ),
  stringsAsFactors = FALSE
)
manifest_match <- match(filtered_symbols, gene_manifest$source_symbol)
gene_manifest$residual_variance[manifest_match] <- residual_variance
selected_match <- match(selected_symbols, gene_manifest$source_symbol)
gene_manifest$selected_network_gene[selected_match] <- TRUE
gene_manifest$exclusion_reason[selected_match] <- ""

output_dir <- file.path(
  output_root, config$phase_directory, "11b_expression", args$network
)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
sample_manifest_path <- file.path(output_dir, "sample_manifest.tsv")
gene_manifest_path <- file.path(output_dir, "gene_manifest.tsv")
counts_output <- file.path(output_dir, "filtered_counts.tsv.gz")
normalized_output <- file.path(output_dir, "normalized_expression.tsv.gz")
adjusted_output <- file.path(output_dir, "adjusted_expression.tsv.gz")
unadjusted_output <- file.path(output_dir, "unadjusted_sensitivity.tsv.gz")
qc_path <- file.path(output_dir, "expression_qc.tsv")

samples$sample_order <- seq.int(0L, nrow(samples) - 1L)
sample_cols <- c(
  "sample_order", "pseudobulk_id", "donor_id", "broad_network", "nuclei",
  "diagnosis", "sex", "apoe_group", "age_death_scaled", "pmi_scaled",
  "study", "log10_nuclei"
)
atomic_fwrite(samples[, sample_cols, drop = FALSE], sample_manifest_path)
atomic_fwrite(gene_manifest, gene_manifest_path)

to_frame <- function(matrix_value, genes) {
  frame <- data.frame(source_symbol = genes, matrix_value, check.names = FALSE)
  names(frame)[-1L] <- sample_ids
  frame
}
atomic_fwrite(
  to_frame(filtered_counts[selected_indices, , drop = FALSE], selected_symbols),
  counts_output
)
atomic_fwrite(
  to_frame(normalized[selected_indices, , drop = FALSE], selected_symbols),
  normalized_output
)
atomic_fwrite(
  to_frame(adjusted[selected_indices, , drop = FALSE], selected_symbols),
  adjusted_output
)
if (isTRUE(config$expression$write_unadjusted_sensitivity)) {
  atomic_fwrite(
    to_frame(normalized[selected_indices, , drop = FALSE], selected_symbols),
    unadjusted_output
  )
}

qc <- data.frame(
  metric = c(
    "eligible_donors", "input_genes", "expression_filter_genes",
    "selected_genes", "minimum_donors_detected", "design_columns",
    "design_rank"
  ),
  value = c(
    nrow(samples), nrow(raw_counts), sum(base_pass), length(selected_indices),
    minimum_donors, ncol(design), qr(design)$rank
  )
)
atomic_fwrite(qc, qc_path)
checks <- data.frame(
  check = c(
    "sample_order_matches_matrix", "selected_symbols_unique",
    "adjusted_finite", "design_full_rank", "selected_within_cap"
  ),
  passed = c(
    identical(colnames(adjusted), sample_ids),
    !anyDuplicated(selected_symbols),
    all(is.finite(adjusted[selected_indices, , drop = FALSE])),
    qr(design)$rank == ncol(design),
    length(selected_indices) <= cap + length(force_include)
  )
)
atomic_fwrite(checks, file.path(output_dir, "checks.tsv"))
artifact_paths <- c(
  sample_manifest_path, gene_manifest_path, counts_output, normalized_output,
  adjusted_output, qc_path, file.path(output_dir, "checks.tsv")
)
if (file.exists(unadjusted_output)) artifact_paths <- c(artifact_paths, unadjusted_output)
artifacts <- data.frame(
  path = provenance_paths(artifact_paths, project_root),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  stringsAsFactors = FALSE
)
atomic_fwrite(artifacts, file.path(output_dir, "artifacts.tsv"))
status <- data.frame(
  schema_version = "seaad_rimbanet_expression_status_v1",
  stage = "VH11B",
  state = if (all(checks$passed)) "validated_complete" else "failed",
  network = args$network,
  donors = nrow(samples),
  genes = length(selected_indices),
  config_sha256 = sha256_file(config_path)
)
atomic_fwrite(status, file.path(output_dir, "status.tsv"))
if (!all(checks$passed)) quit(status = 2L)
cat("VH11B validated:", args$network, "donors=", nrow(samples),
    "genes=", length(selected_indices), "\n")
