#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_cli <- function(args) {
  out <- list(config = NULL, network = NULL, stage = "all")
  i <- 1L
  while (i <= length(args)) {
    if (i == length(args)) stop("Incomplete argument: ", args[[i]])
    key <- args[[i]]
    value <- args[[i + 1L]]
    if (key == "--config") out$config <- value
    else if (key == "--network") out$network <- value
    else if (key == "--stage") out$stage <- value
    else stop("Unknown argument: ", key)
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$network)) {
    stop("--config and --network are required")
  }
  if (!out$stage %in% c("eqtl", "cit", "all")) stop("Invalid --stage")
  out
}

gzip_executable <- function() {
  executable <- unname(Sys.which("gzip"))
  if (!nzchar(executable)) {
    stop("gzip executable is required for compressed TSV input/output")
  }
  executable
}

fread_tsv <- function(path, ...) {
  if (grepl("[.]gz$", path)) {
    return(data.table::fread(
      cmd = paste(shQuote(gzip_executable()), "-dc --", shQuote(path)),
      sep = "\t",
      ...
    ))
  }
  data.table::fread(path, sep = "\t", ...)
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
    x, temporary_plain, sep = "\t", quote = FALSE, na = "NA"
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

resolve_config_path <- function(value, project_root) {
  if (grepl("^/", value)) value else file.path(project_root, value)
}

provenance_paths <- function(paths, project_root) {
  resolved <- normalizePath(paths, mustWork = TRUE)
  prefix <- paste0(project_root, "/")
  ifelse(startsWith(resolved, prefix), substring(resolved, nchar(prefix) + 1L), resolved)
}

read_gene_positions <- function(gtf_path, genes) {
  gtf <- data.table::fread(
    cmd = paste(shQuote(gzip_executable()), "-cd --", shQuote(gtf_path)),
    sep = "\t", header = FALSE, quote = "", data.table = FALSE,
    select = c(1L, 3L, 4L, 5L, 9L),
    col.names = c("chr", "feature", "left", "right", "attributes")
  )
  gtf <- gtf[gtf$feature == "gene", , drop = FALSE]
  gtf$geneid <- sub('.*gene_name "([^"]+)".*', "\\1", gtf$attributes)
  gtf <- gtf[gtf$geneid %in% genes, c("geneid", "chr", "left", "right")]
  gtf <- gtf[!duplicated(gtf$geneid), , drop = FALSE]
  gtf
}

build_covariates <- function(expression, samples, ancestry_path, n_expression_pcs) {
  ancestry <- data.table::fread(ancestry_path, data.table = FALSE)
  if (!all(c("donor_id") %in% names(ancestry))) {
    stop("Ancestry covariates lack donor_id")
  }
  ancestry$donor_id <- as.character(ancestry$donor_id)
  sample_donors <- as.character(samples$donor_id)
  ancestry <- ancestry[match(sample_donors, ancestry$donor_id), , drop = FALSE]
  if (anyNA(ancestry$donor_id)) stop("Missing ancestry PCs for expression donors")
  pc_columns <- grep("^PC[0-9]+$", names(ancestry), value = TRUE)
  if (!length(pc_columns)) stop("No ancestry PC columns")
  ancestry_matrix <- t(as.matrix(ancestry[, pc_columns, drop = FALSE]))
  expression_rank <- min(
    as.integer(n_expression_pcs), ncol(expression) - 1L, nrow(expression)
  )
  expression_pcs <- stats::prcomp(
    t(expression), center = TRUE, scale. = FALSE, rank. = expression_rank
  )$x[, seq_len(expression_rank), drop = FALSE]
  expression_pc_matrix <- t(expression_pcs)
  rownames(expression_pc_matrix) <- paste0("expression_PC", seq_len(expression_rank))
  result <- rbind(ancestry_matrix, expression_pc_matrix)
  colnames(result) <- sample_donors
  storage.mode(result) <- "double"
  result
}

extract_cit <- function(value) {
  flat <- unlist(value)
  names_flat <- names(flat)
  pick <- function(pattern) {
    index <- grep(pattern, names_flat, ignore.case = TRUE)
    if (!length(index)) return(NA_real_)
    as.numeric(flat[[index[[1L]]]])
  }
  c(
    p_cit = pick("(^|[.])p_cit$|omnibus"),
    p_component_1 = pick("p1$|test1"),
    p_component_2 = pick("p2$|test2"),
    p_component_3 = pick("p3$|test3"),
    p_component_4 = pick("p4$|test4")
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest", "MatrixEQTL")
if (args$stage %in% c("cit", "all")) required <- c(required, "cit")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
if (!identical(config$schema_version, "seaad_rimbanet_config_v1")) stop("Bad config")
if (!args$network %in% unlist(config$networks)) stop("Unknown network")
generated_root <- config$storage$generated_output_root
if (is.null(generated_root)) generated_root <- config$output_root
generated_root <- resolve_config_path(generated_root, project_root)
dir.create(generated_root, recursive = TRUE, showWarnings = FALSE)
output_root <- normalizePath(generated_root, mustWork = TRUE)
expression_dir <- file.path(
  output_root, config$phase_directory, "11b_expression", args$network
)
genetics_dir <- file.path(
  output_root, config$phase_directory, "11c_genetics", args$network
)
prior_dir <- file.path(
  output_root, config$phase_directory, "11d_priors", args$network
)
dir.create(genetics_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(prior_dir, recursive = TRUE, showWarnings = FALSE)

expression_table <- fread_tsv(
  file.path(expression_dir, "adjusted_expression.tsv.gz"), data.table = FALSE
)
samples <- data.table::fread(
  file.path(expression_dir, "sample_manifest.tsv"), data.table = FALSE
)
sample_ids <- as.character(samples$pseudobulk_id)
if (!identical(names(expression_table)[-1L], sample_ids)) {
  stop("Expression/sample order mismatch")
}
expression <- as.matrix(expression_table[, -1L, drop = FALSE])
storage.mode(expression) <- "double"
rownames(expression) <- as.character(expression_table$source_symbol)
colnames(expression) <- as.character(samples$donor_id)

genotype_path <- resolve_config_path(config$genetics$genotype_matrix, project_root)
position_path <- resolve_config_path(config$genetics$variant_positions, project_root)
ancestry_path <- resolve_config_path(config$genetics$ancestry_covariates, project_root)
if (!all(file.exists(c(genotype_path, position_path, ancestry_path)))) {
  stop("Prepared genotype inputs are missing")
}
genotype_table <- fread_tsv(genotype_path, data.table = FALSE)
variant_positions <- fread_tsv(position_path, data.table = FALSE)
donors <- intersect(colnames(expression), names(genotype_table)[-1L])
minimum_matched <- as.integer(config$genetics$minimum_matched_donors)
if (length(donors) < minimum_matched) {
  stop("Fewer than ", minimum_matched, " matched expression/genotype donors")
}
expression <- expression[, donors, drop = FALSE]
samples <- samples[match(donors, samples$donor_id), , drop = FALSE]
genotype_table <- genotype_table[
  , c("variant_id", donors), drop = FALSE
]
genotype <- as.matrix(genotype_table[, -1L, drop = FALSE])
storage.mode(genotype) <- "double"
rownames(genotype) <- genotype_table$variant_id
colnames(genotype) <- donors
if (any(!is.finite(genotype))) stop("Genotype matrix contains missing/non-finite data")

covariates <- build_covariates(
  expression, samples, ancestry_path, config$genetics$expression_pcs
)
if (qr(t(covariates))$rank != nrow(covariates)) {
  stop("eQTL covariate matrix is rank deficient")
}

eqtl_all_path <- file.path(genetics_dir, "cis_eqtl_all.tsv.gz")
eqtl_sig_path <- file.path(genetics_dir, "cis_eqtl_significant.tsv.gz")
if (args$stage %in% c("eqtl", "all")) {
  genotype_sliced <- MatrixEQTL::SlicedData$new()
  genotype_sliced$CreateFromMatrix(genotype)
  expression_sliced <- MatrixEQTL::SlicedData$new()
  expression_sliced$CreateFromMatrix(expression)
  covariate_sliced <- MatrixEQTL::SlicedData$new()
  covariate_sliced$CreateFromMatrix(covariates)

  snpspos <- variant_positions[
    match(rownames(genotype), variant_positions$variant_id),
    c("variant_id", "chromosome", "position")
  ]
  if (anyNA(snpspos$variant_id)) stop("Missing variant positions")
  names(snpspos) <- c("snpid", "chr", "pos")
  snpspos$chr <- sub("^chr", "", as.character(snpspos$chr), ignore.case = TRUE)
  genepos <- read_gene_positions(
    resolve_config_path(config$inputs$gencode_gtf, project_root), rownames(expression)
  )
  if (!setequal(genepos$geneid, rownames(expression))) {
    missing_genes <- setdiff(rownames(expression), genepos$geneid)
    stop("Missing GENCODE positions for ", length(missing_genes), " genes")
  }
  genepos$chr <- sub("^chr", "", as.character(genepos$chr), ignore.case = TRUE)
  temporary_cis <- file.path(genetics_dir, "matrixeqtl_cis.tmp.tsv")
  result <- MatrixEQTL::Matrix_eQTL_main(
    snps = genotype_sliced,
    gene = expression_sliced,
    cvrt = covariate_sliced,
    output_file_name = "",
    pvOutputThreshold = 0,
    useModel = MatrixEQTL::modelLINEAR,
    errorCovariance = numeric(),
    verbose = TRUE,
    output_file_name.cis = temporary_cis,
    pvOutputThreshold.cis = 1,
    snpspos = snpspos,
    genepos = genepos,
    cisDist = as.numeric(config$genetics$cis_window_bp),
    pvalue.hist = FALSE,
    min.pv.by.genesnp = FALSE,
    noFDRsaveMemory = FALSE
  )
  eqtl <- result$cis$eqtls
  if (is.null(eqtl) || !nrow(eqtl)) {
    eqtl <- data.frame(
      variant_id = character(), source_symbol = character(),
      beta = numeric(), statistic = numeric(), pvalue = numeric(),
      FDR = numeric()
    )
  }
  if (nrow(eqtl)) {
    names(eqtl)[names(eqtl) == "snps"] <- "variant_id"
    names(eqtl)[names(eqtl) == "gene"] <- "source_symbol"
    if (!"FDR" %in% names(eqtl)) {
      eqtl$FDR <- stats::p.adjust(eqtl$pvalue, method = config$genetics$fdr_method)
    }
    eqtl <- eqtl[order(eqtl$FDR, eqtl$pvalue), , drop = FALSE]
  }
  significant <- eqtl[
    eqtl$FDR <= as.numeric(config$genetics$fdr_maximum), , drop = FALSE
  ]
  atomic_fwrite(eqtl, eqtl_all_path)
  atomic_fwrite(significant, eqtl_sig_path)
  if (file.exists(temporary_cis)) unlink(temporary_cis)
  eqtl_summary <- data.frame(
    network = args$network,
    matched_donors = length(donors),
    tested_cis_pairs = nrow(eqtl),
    significant_cis_pairs = nrow(significant),
    significant_eGenes = if (nrow(significant)) {
      length(unique(significant$source_symbol))
    } else 0L,
    significant_instruments = if (nrow(significant)) {
      length(unique(significant$variant_id))
    } else 0L
  )
  atomic_fwrite(eqtl_summary, file.path(genetics_dir, "eqtl_summary.tsv"))
}

if (args$stage %in% c("cit", "all")) {
  if (!file.exists(eqtl_sig_path)) stop("Run eQTL stage before CIT")
  significant <- fread_tsv(eqtl_sig_path, data.table = FALSE)
  cit_rows <- list()
  row_index <- 0L
  if (nrow(significant)) {
    by_variant <- split(significant$source_symbol, significant$variant_id)
    for (variant_id in names(by_variant)) {
      genes <- sort(unique(by_variant[[variant_id]]))
      genes <- intersect(genes, rownames(expression))
      if (length(genes) < 2L) next
      L <- as.numeric(genotype[variant_id, donors])
      pairs <- utils::combn(genes, 2L, simplify = FALSE)
      for (pair in pairs) {
        for (direction in list(pair, rev(pair))) {
          mediator <- direction[[1L]]
          outcome <- direction[[2L]]
          row_index <- row_index + 1L
          result <- tryCatch(
            cit::cit.cp(
              L = L,
              G = as.numeric(expression[mediator, donors]),
              T = as.numeric(expression[outcome, donors]),
              C = t(covariates),
              n.resampl = as.integer(config$cit$n_resamples),
              n.perm = as.integer(config$cit$n_permutations),
              rseed = as.integer(config$cit$random_seed) + row_index
            ),
            error = function(e) e
          )
          if (inherits(result, "error")) {
            pvalues <- rep(NA_real_, 5L)
            names(pvalues) <- c(
              "p_cit", "p_component_1", "p_component_2",
              "p_component_3", "p_component_4"
            )
            error <- conditionMessage(result)
          } else {
            pvalues <- extract_cit(result)
            error <- ""
          }
          cit_rows[[row_index]] <- data.frame(
            variant_id = variant_id,
            parent = mediator,
            child = outcome,
            p_cit = pvalues[["p_cit"]],
            p_component_1 = pvalues[["p_component_1"]],
            p_component_2 = pvalues[["p_component_2"]],
            p_component_3 = pvalues[["p_component_3"]],
            p_component_4 = pvalues[["p_component_4"]],
            error = error,
            stringsAsFactors = FALSE
          )
        }
      }
    }
  }
  cit_table <- if (length(cit_rows)) {
    data.table::rbindlist(cit_rows, fill = TRUE)
  } else {
    data.frame(
      variant_id = character(), parent = character(), child = character(),
      p_cit = numeric(), p_component_1 = numeric(), p_component_2 = numeric(),
      p_component_3 = numeric(), p_component_4 = numeric(), error = character()
    )
  }
  cit_table$FDR <- NA_real_
  valid <- is.finite(cit_table$p_cit)
  cit_table$FDR[valid] <- stats::p.adjust(
    cit_table$p_cit[valid], method = config$cit$fdr_method
  )
  cit_table$significant <- valid &
    cit_table$FDR <= as.numeric(config$cit$fdr_maximum)
  atomic_fwrite(cit_table, file.path(prior_dir, "cit_edges.tsv.gz"))
  atomic_fwrite(
    cit_table[cit_table$significant, , drop = FALSE],
    file.path(prior_dir, "cit_edges_significant.tsv.gz")
  )
  atomic_fwrite(
    data.frame(
      network = args$network,
      ordered_tests = nrow(cit_table),
      valid_tests = sum(valid),
      significant_directions = sum(cit_table$significant)
    ),
    file.path(prior_dir, "cit_summary.tsv")
  )
}

failed <- FALSE
if (args$stage %in% c("eqtl", "all")) {
  significant_check <- fread_tsv(eqtl_sig_path, data.table = FALSE)
  eqtl_checks <- data.frame(
    check = c(
      "minimum_matched_donors", "covariates_full_rank",
      "significant_cis_eqtl_present"
    ),
    passed = c(
      length(donors) >= minimum_matched,
      qr(t(covariates))$rank == nrow(covariates),
      nrow(significant_check) > 0L
    ),
    observed = c(
      length(donors), qr(t(covariates))$rank, nrow(significant_check)
    ),
    expected = c(paste0(">=", minimum_matched), nrow(covariates), ">0")
  )
  atomic_fwrite(eqtl_checks, file.path(genetics_dir, "checks.tsv"))
  eqtl_artifact_paths <- c(
    eqtl_all_path, eqtl_sig_path,
    file.path(genetics_dir, "eqtl_summary.tsv"),
    file.path(genetics_dir, "checks.tsv")
  )
  atomic_fwrite(
    data.frame(
      path = provenance_paths(eqtl_artifact_paths, project_root),
      bytes = file.info(eqtl_artifact_paths)$size,
      sha256 = vapply(
        eqtl_artifact_paths,
        function(path) digest::digest(
          file = path, algo = "sha256", serialize = FALSE
        ),
        character(1)
      )
    ),
    file.path(genetics_dir, "artifacts.tsv")
  )
  eqtl_state <- if (all(eqtl_checks$passed)) {
    "validated_complete"
  } else {
    "blocked_no_significant_eqtl"
  }
  atomic_fwrite(
    data.frame(
      schema_version = "seaad_rimbanet_eqtl_status_v1",
      stage = "VH11C_EQTL",
      state = eqtl_state,
      network = args$network,
      matched_donors = length(donors),
      significant_cis_pairs = nrow(significant_check),
      config_sha256 = digest::digest(
        file = config_path, algo = "sha256", serialize = FALSE
      )
    ),
    file.path(genetics_dir, "status.tsv")
  )
  failed <- failed || !all(eqtl_checks$passed)
}
if (args$stage %in% c("cit", "all")) {
  cit_check <- fread_tsv(
    file.path(prior_dir, "cit_edges_significant.tsv.gz"), data.table = FALSE
  )
  cit_checks <- data.frame(
    check = c("CIT_completed", "significant_CIT_direction_present"),
    passed = c(file.exists(file.path(prior_dir, "cit_edges.tsv.gz")),
               nrow(cit_check) > 0L),
    observed = c(TRUE, nrow(cit_check)),
    expected = c(TRUE, ">0")
  )
  atomic_fwrite(cit_checks, file.path(prior_dir, "cit_checks.tsv"))
  cit_artifact_paths <- c(
    file.path(prior_dir, "cit_edges.tsv.gz"),
    file.path(prior_dir, "cit_edges_significant.tsv.gz"),
    file.path(prior_dir, "cit_summary.tsv"),
    file.path(prior_dir, "cit_checks.tsv")
  )
  atomic_fwrite(
    data.frame(
      path = provenance_paths(cit_artifact_paths, project_root),
      bytes = file.info(cit_artifact_paths)$size,
      sha256 = vapply(
        cit_artifact_paths,
        function(path) digest::digest(
          file = path, algo = "sha256", serialize = FALSE
        ),
        character(1)
      )
    ),
    file.path(prior_dir, "cit_artifacts.tsv")
  )
  cit_state <- if (all(cit_checks$passed)) {
    "validated_complete"
  } else {
    "blocked_no_significant_cit"
  }
  atomic_fwrite(
    data.frame(
      schema_version = "seaad_rimbanet_cit_status_v1",
      stage = "VH11D_CIT",
      state = cit_state,
      network = args$network,
      significant_directions = nrow(cit_check),
      config_sha256 = digest::digest(
        file = config_path, algo = "sha256", serialize = FALSE
      )
    ),
    file.path(prior_dir, "cit_status.tsv")
  )
  failed <- failed || !all(cit_checks$passed)
}

cat("VH11C/D complete:", args$network, "stage=", args$stage,
    "state=", if (failed) "blocked" else "validated_complete", "\n")
if (failed) quit(status = 2L)
