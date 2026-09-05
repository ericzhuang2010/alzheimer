#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_cli <- function(args) {
  out <- list(config = NULL, network = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (i == length(args)) stop("Incomplete argument: ", args[[i]])
    if (args[[i]] == "--config") out$config <- args[[i + 1L]]
    else if (args[[i]] == "--network") out$network <- args[[i + 1L]]
    else stop("Unknown argument: ", args[[i]])
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$network)) {
    stop("--config and --network are required")
  }
  out
}

atomic_fwrite <- function(x, path, col_names = TRUE) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(
    x, temporary, sep = "\t", col.names = col_names, quote = FALSE, na = "NA"
  )
  if (!file.rename(temporary, path)) stop("Atomic rename failed: ", path)
}
gzip_executable <- function() {
  executable <- unname(Sys.which("gzip"))
  if (!nzchar(executable)) {
    stop("gzip executable is required for compressed TSV input")
  }
  executable
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


resolve_config_path <- function(value, project_root) {
  if (grepl("^/", value)) value else file.path(project_root, value)
}

provenance_paths <- function(paths, project_root) {
  resolved <- normalizePath(paths, mustWork = TRUE)
  prefix <- paste0(project_root, "/")
  ifelse(startsWith(resolved, prefix), substring(resolved, nchar(prefix) + 1L), resolved)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
if (!identical(config$schema_version, "seaad_rimbanet_config_v1")) {
  stop("Unsupported config schema")
}
if (!args$network %in% unlist(config$networks)) stop("Unknown network")
generated_root <- config$storage$generated_output_root
if (is.null(generated_root)) generated_root <- config$output_root
generated_root <- resolve_config_path(generated_root, project_root)
dir.create(generated_root, recursive = TRUE, showWarnings = FALSE)
output_root <- normalizePath(generated_root, mustWork = TRUE)
expression_dir <- file.path(
  output_root, config$phase_directory, "11b_expression", args$network
)
expression_path <- file.path(expression_dir, "adjusted_expression.tsv.gz")
sample_path <- file.path(expression_dir, "sample_manifest.tsv")
gene_path <- file.path(expression_dir, "gene_manifest.tsv")
if (!all(file.exists(c(expression_path, sample_path, gene_path)))) {
  stop("Expression stage is incomplete for ", args$network)
}

expression <- fread_tsv(expression_path)
samples <- fread_tsv(sample_path)
gene_manifest <- fread_tsv(gene_path)
if (names(expression)[[1L]] != "source_symbol") {
  stop("Adjusted expression first column must be source_symbol")
}
sample_ids <- as.character(samples$pseudobulk_id)
if (!identical(names(expression)[-1L], sample_ids)) {
  stop("Adjusted expression columns do not match sample manifest")
}
if (anyDuplicated(expression$source_symbol)) stop("Duplicate genes")

values <- as.matrix(expression[, -1L, drop = FALSE])
storage.mode(values) <- "double"
if (any(!is.finite(values))) stop("Expression contains non-finite values")
states <- as.integer(config$discretization$states)
if (states != 3L) stop("This contract requires exactly three states")
base_seed <- as.integer(config$discretization$random_seed)
nstart <- as.integer(config$discretization$nstart)
iter_max <- as.integer(config$discretization$iter_max)

discrete <- matrix(
  NA_integer_, nrow = nrow(values), ncol = ncol(values),
  dimnames = list(as.character(expression$source_symbol), sample_ids)
)
centers <- matrix(NA_real_, nrow = nrow(values), ncol = states)
accepted <- rep(FALSE, nrow(values))
reasons <- rep("", nrow(values))

for (i in seq_len(nrow(values))) {
  x <- values[i, ]
  if (length(unique(x)) < states) {
    reasons[[i]] <- "fewer_than_three_distinct_values"
    next
  }
  set.seed(base_seed + i)
  fit <- tryCatch(
    stats::kmeans(x, centers = states, nstart = nstart, iter.max = iter_max),
    error = function(e) e
  )
  if (inherits(fit, "error")) {
    reasons[[i]] <- paste0("kmeans_error:", conditionMessage(fit))
    next
  }
  if (length(unique(fit$cluster)) != states) {
    reasons[[i]] <- "empty_cluster"
    next
  }
  ordered <- order(as.numeric(fit$centers))
  relabel <- integer(states)
  relabel[ordered] <- seq.int(0L, states - 1L)
  discrete[i, ] <- relabel[fit$cluster]
  centers[i, ] <- sort(as.numeric(fit$centers))
  accepted[[i]] <- TRUE
}

if (sum(accepted) < 3L) stop("Discretization retained fewer than three genes")
final_discrete <- discrete[accepted, , drop = FALSE]
final_genes <- rownames(final_discrete)
if (any(!final_discrete %in% 0:2)) stop("Invalid discretized state")

input_dir <- file.path(
  output_root, config$phase_directory, "11e_inputs", args$network
)
dir.create(input_dir, recursive = TRUE, showWarnings = FALSE)
data_path <- file.path(input_dir, "data.discretized.txt")
manifest_path <- file.path(input_dir, "gene_manifest.tsv")
qc_path <- file.path(input_dir, "discretization_qc.tsv")

output_frame <- data.frame(
  source_symbol = final_genes, final_discrete,
  check.names = FALSE, stringsAsFactors = FALSE
)
names(output_frame)[-1L] <- sample_ids
atomic_fwrite(output_frame, data_path, col_names = FALSE)

source_rows <- match(expression$source_symbol, gene_manifest$source_symbol)
if (anyNA(source_rows)) stop("Expression genes missing from gene manifest")
manifest <- gene_manifest[source_rows, , drop = FALSE]
manifest$discretization_pass <- accepted
manifest$discretization_exclusion_reason <- reasons
manifest$center_low <- centers[, 1L]
manifest$center_middle <- centers[, 2L]
manifest$center_high <- centers[, 3L]
manifest$final_node_order <- NA_integer_
manifest$final_node_order[accepted] <- seq.int(0L, sum(accepted) - 1L)
atomic_fwrite(manifest, manifest_path)

qc <- data.frame(
  metric = c(
    "input_genes", "accepted_genes", "rejected_genes", "samples",
    "state_0_count", "state_1_count", "state_2_count"
  ),
  value = c(
    nrow(values), sum(accepted), sum(!accepted), ncol(values),
    sum(final_discrete == 0L), sum(final_discrete == 1L),
    sum(final_discrete == 2L)
  )
)
atomic_fwrite(qc, qc_path)
checks <- data.frame(
  check = c(
    "sample_order_matches", "unique_genes", "only_three_states",
    "all_genes_have_three_states"
  ),
  passed = c(
    identical(colnames(final_discrete), sample_ids),
    !anyDuplicated(final_genes),
    all(final_discrete %in% 0:2),
    all(apply(final_discrete, 1L, function(x) length(unique(x)) == 3L))
  )
)
atomic_fwrite(checks, file.path(input_dir, "discretization_checks.tsv"))
artifact_paths <- c(
  data_path, manifest_path, qc_path,
  file.path(input_dir, "discretization_checks.tsv")
)
artifacts <- data.frame(
  path = provenance_paths(artifact_paths, project_root),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(
    artifact_paths,
    function(path) digest::digest(
      file = path, algo = "sha256", serialize = FALSE
    ),
    character(1)
  ),
  stringsAsFactors = FALSE
)
atomic_fwrite(artifacts, file.path(input_dir, "discretization_artifacts.tsv"))
status <- data.frame(
  schema_version = "seaad_rimbanet_discretization_status_v1",
  stage = "VH11E_DISCRETIZE",
  state = if (all(checks$passed)) "validated_complete" else "failed",
  network = args$network,
  samples = ncol(final_discrete),
  nodes = nrow(final_discrete),
  config_sha256 = digest::digest(
    file = config_path, algo = "sha256", serialize = FALSE
  ),
  data_sha256 = digest::digest(
    file = data_path, algo = "sha256", serialize = FALSE
  )
)
atomic_fwrite(status, file.path(input_dir, "discretization_status.tsv"))
if (!all(checks$passed)) quit(status = 2L)
cat("VH11E discretized:", args$network, "nodes=", nrow(final_discrete),
    "samples=", ncol(final_discrete), "\n")
