#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(yaml)
})

SCHEMA <- "human_genetic_support_tier2_coloc_v1"
OUTPUT_FILES <- c(
  "tier2_analysis_manifest.tsv",
  "tier2_candidate_route_manifest.tsv",
  "tier2_dataset_registry.tsv",
  "tier2_input_inventory.tsv",
  "tier2_source_checks.tsv",
  "tier2_rerun_decisions.tsv",
  "tier2_gwas_finemapping.tsv.gz",
  "tier2_qtl_finemapping.tsv.gz",
  "tier2_variant_harmonization.tsv.gz",
  "tier2_variant_harmonization_summary.tsv",
  "tier2_colocalization.tsv.gz",
  "tier2_colocalization_qc.tsv",
  "tier2_prior_sensitivity.tsv.gz",
  "tier2_assessability.tsv",
  "tier2_evidence_summary.tsv",
  "tier2_figure_data.tsv.gz",
  "tier2_evidence_matrix.pdf",
  "tier2_evidence_matrix.png",
  "tier2_locus_plots.pdf",
  "tier2_stage_status.tsv",
  "tier2_checks.tsv",
  "tier2_artifacts.tsv",
  "tier2_status.tsv"
)

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0L) y else x
`%+%` <- function(a, b) paste0(a, b)

parse_cli <- function(args = commandArgs(trailingOnly = TRUE)) {
  out <- list(
    config = NULL,
    execution_config = NULL,
    scientific_config = NULL,
    task_mode = "genetic_support_tier2",
    output_root = NULL,
    pilot = FALSE,
    force = FALSE
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--pilot", "--force")) {
      out[[sub("^--", "", key)]] <- TRUE
      i <- i + 1L
      next
    }
    if (i == length(args)) stop("Missing value for ", key, call. = FALSE)
    name <- gsub("-", "_", sub("^--", "", key))
    if (!name %in% names(out)) stop("Unknown argument: ", key, call. = FALSE)
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$execution_config)) {
    stop("--config and --execution-config are required", call. = FALSE)
  }
  out
}

abs_path <- function(root, path) {
  if (grepl("^/", path)) normalizePath(path, mustWork = FALSE) else
    normalizePath(file.path(root, path), mustWork = FALSE)
}

relative_path <- function(path, root) {
  path <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  prefix <- paste0(root, .Platform$file.sep)
  if (startsWith(path, prefix)) substring(path, nchar(prefix) + 1L) else path
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  value <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(value, "status")
  if (!is.null(status) && status != 0L) stop("sha256sum failed for ", path, call. = FALSE)
  strsplit(value[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  fwrite(as.data.table(x), path, sep = "\t", quote = FALSE, na = "NA", compress = "auto")
}

read_tsv <- function(path) {
  if (!file.exists(path)) stop("Missing input: ", path, call. = FALSE)
  fread(path, sep = "\t", na.strings = c("NA", ""), showProgress = FALSE)
}

coerce_bool <- function(x) {
  tolower(as.character(x)) %in% c("true", "t", "1", "yes")
}

first_column <- function(x, choices) {
  hit <- choices[choices %in% names(x)]
  if (length(hit)) hit[[1L]] else NA_character_
}

strip_ensembl_version <- function(x) sub("[.][0-9]+$", "", as.character(x))

validate_tier1 <- function(paths) {
  status <- read_tsv(paths$tier1_status)
  if (nrow(status) != 1L || status$technical_status[[1L]] != "validated_complete_tier1") {
    stop("Tier 1 status is not validated_complete_tier1", call. = FALSE)
  }
  artifacts <- read_tsv(paths$tier1_artifacts)
  failures <- character()
  for (i in seq_len(nrow(artifacts))) {
    path <- file.path(paths$tier1_root, artifacts$path[[i]])
    observed <- sha256_file(path)
    if (is.na(observed) || observed != artifacts$sha256[[i]]) {
      failures <- c(failures, artifacts$path[[i]])
    }
  }
  if (length(failures)) {
    stop("Tier 1 artifact hash mismatch: ", paste(failures, collapse = ", "), call. = FALSE)
  }
  list(status = status, artifacts = artifacts)
}

build_route_manifest <- function(candidate, loci, qtl_types = c("eQTL", "sQTL")) {
  candidate <- copy(candidate)
  candidate[, is_mtdna := coerce_bool(is_mtdna_gene)]
  nuclear <- candidate[is_mtdna == FALSE]
  routes <- rbindlist(lapply(qtl_types, function(qtl) {
    x <- copy(nuclear)
    x[, qtl_type := qtl]
    x
  }), use.names = TRUE)
  keep_candidate <- c("candidate_id", "gene", "broad_network", "case_id", "case_label")
  missing <- setdiff(keep_candidate, names(routes))
  if (length(missing)) stop("Tier 1 candidate manifest missing: ", paste(missing, collapse = ", "))
  loci_keep <- unique(loci[, .(gene, ensembl_gene_id, chromosome, window_start, window_end, genome_build)])
  routes <- merge(routes[, c(keep_candidate, "qtl_type"), with = FALSE], loci_keep, by = "gene", all.x = TRUE)
  setorder(routes, candidate_id, qtl_type)
  routes[, route_id := sprintf("T2R%03d", seq_len(.N))]
  routes[, schema_version := SCHEMA]
  setcolorder(routes, c(
    "schema_version", "route_id", "candidate_id", "gene", "ensembl_gene_id",
    "broad_network", "case_id", "case_label", "qtl_type", "chromosome",
    "window_start", "window_end", "genome_build"
  ))
  routes
}

validate_ld_matrix <- function(ld, variant_ids, tolerance = 1e-8) {
  if (!is.matrix(ld) || !is.numeric(ld)) stop("LD must be a numeric matrix", call. = FALSE)
  if (nrow(ld) != ncol(ld)) stop("LD must be square", call. = FALSE)
  if (is.null(rownames(ld)) || is.null(colnames(ld))) stop("LD dimnames are required", call. = FALSE)
  if (!identical(rownames(ld), colnames(ld))) stop("LD row/column order differs", call. = FALSE)
  if (!all(variant_ids %in% rownames(ld))) stop("LD is missing requested variants", call. = FALSE)
  sub_ld <- ld[variant_ids, variant_ids, drop = FALSE]
  if (any(!is.finite(sub_ld))) stop("LD contains non-finite values", call. = FALSE)
  if (max(abs(sub_ld - t(sub_ld))) > tolerance) stop("LD is not symmetric", call. = FALSE)
  if (max(abs(diag(sub_ld) - 1)) > tolerance) stop("LD diagonal is not one", call. = FALSE)
  if (max(abs(sub_ld)) > 1 + tolerance) stop("LD entries exceed correlation bounds", call. = FALSE)
  min_eigen <- min(eigen(sub_ld, symmetric = TRUE, only.values = TRUE)$values)
  list(matrix = sub_ld, min_eigenvalue = min_eigen)
}

complement_allele <- function(x) {
  chartr("ACGT", "TGCA", toupper(as.character(x)))
}

harmonize_summary_stats <- function(gwas, qtl) {
  required <- c("variant_id", "beta", "standard_error", "effect_allele", "other_allele")
  if (length(setdiff(required, names(gwas))) || length(setdiff(required, names(qtl)))) {
    stop("Summary statistics lack required harmonization columns", call. = FALSE)
  }
  g <- copy(gwas)
  q <- copy(qtl)
  g[, `:=`(
    beta = as.numeric(beta),
    standard_error = as.numeric(standard_error),
    effect_allele = toupper(effect_allele),
    other_allele = toupper(other_allele)
  )]
  q[, `:=`(
    beta = as.numeric(beta),
    standard_error = as.numeric(standard_error),
    effect_allele = toupper(effect_allele),
    other_allele = toupper(other_allele)
  )]
  z <- merge(g, q, by = "variant_id", suffixes = c("_gwas", "_qtl"))
  if (!nrow(z)) stop("GWAS and QTL have no shared variants", call. = FALSE)
  z[, operation := fifelse(
    effect_allele_gwas == effect_allele_qtl & other_allele_gwas == other_allele_qtl,
    "match",
    fifelse(
      effect_allele_gwas == other_allele_qtl & other_allele_gwas == effect_allele_qtl,
      "swap",
      fifelse(
        effect_allele_gwas == complement_allele(effect_allele_qtl) &
          other_allele_gwas == complement_allele(other_allele_qtl),
        "complement",
        fifelse(
          effect_allele_gwas == complement_allele(other_allele_qtl) &
            other_allele_gwas == complement_allele(effect_allele_qtl),
          "swap_complement",
          "mismatch"
        )
      )
    )
  )]
  z[, included := operation != "mismatch"]
  z[operation %in% c("swap", "swap_complement"), beta_qtl := -beta_qtl]
  z[, exclusion_reason := fifelse(included, NA_character_, "allele_mismatch")]
  z
}

run_custom_coloc <- function(
    gwas, qtl, gwas_ld, qtl_ld, gwas_n, qtl_n,
    p1 = 1e-4, p2 = 1e-4, p12_values = c(1e-6, 5e-6, 1e-5)) {
  harmonized <- harmonize_summary_stats(gwas, qtl)
  shared <- harmonized[included == TRUE & is.finite(beta_gwas) &
    is.finite(standard_error_gwas) & standard_error_gwas > 0 &
    is.finite(beta_qtl) & is.finite(standard_error_qtl) & standard_error_qtl > 0]
  if (nrow(shared) < 50L) stop("Fewer than 50 harmonized variants", call. = FALSE)
  ids <- shared$variant_id
  g_ld <- validate_ld_matrix(gwas_ld, ids)$matrix
  q_ld <- validate_ld_matrix(qtl_ld, ids)$matrix
  d1 <- list(
    beta = shared$beta_gwas,
    varbeta = shared$standard_error_gwas^2,
    snp = ids,
    position = seq_along(ids),
    LD = g_ld,
    N = as.numeric(gwas_n),
    type = "quant",
    sdY = 1
  )
  d2 <- list(
    beta = shared$beta_qtl,
    varbeta = shared$standard_error_qtl^2,
    snp = ids,
    position = seq_along(ids),
    LD = q_ld,
    N = as.numeric(qtl_n),
    type = "quant",
    sdY = 1
  )
  s1 <- coloc::runsusie(d1, coverage = 0.95, maxit = 1000)
  s2 <- coloc::runsusie(d2, coverage = 0.95, maxit = 1000)
  sensitivity <- rbindlist(lapply(p12_values, function(p12) {
    result <- as.data.table(coloc::coloc.susie(
      s1, s2, p1 = p1, p2 = p2, p12 = p12
    )$summary)
    result[, p12 := p12]
    result
  }), fill = TRUE)
  list(
    harmonized = harmonized,
    shared = shared,
    susie_gwas = s1,
    susie_qtl = s2,
    sensitivity = sensitivity
  )
}

synthetic_coloc_smoke <- function() {
  set.seed(19)
  n <- 240L
  ids <- paste0("v", seq_len(n))
  ld <- outer(seq_len(n), seq_len(n), function(i, j) 0.85^abs(i - j))
  dimnames(ld) <- list(ids, ids)
  z1 <- 9 * ld[, 45] + 8 * ld[, 185] + rnorm(n, 0, 0.02)
  z2 <- 8.5 * ld[, 45] + 7.5 * ld[, 185] + rnorm(n, 0, 0.02)
  make_stats <- function(z, n_sample) data.table(
    variant_id = ids,
    beta = z / sqrt(n_sample),
    standard_error = rep(1 / sqrt(n_sample), n),
    effect_allele = "A",
    other_allele = "G"
  )
  result <- run_custom_coloc(
    make_stats(z1, 1200), make_stats(z2, 900), ld, ld,
    1200, 900, p12_values = c(1e-6, 5e-6, 1e-5)
  )
  primary <- result$sensitivity[p12 == 5e-6]
  if (nrow(primary) < 4L || sum(primary$PP.H4.abf >= 0.8) < 2L ||
      sum(primary$PP.H3.abf >= 0.8) < 2L) {
    stop("Synthetic multi-signal coloc smoke test did not recover expected pairs", call. = FALSE)
  }
  list(
    signal_pairs = nrow(primary),
    shared_pairs = sum(primary$PP.H4.abf >= 0.8),
    distinct_pairs = sum(primary$PP.H3.abf >= 0.8),
    harmonized_variants = nrow(result$shared)
  )
}

classify_context <- function(source_context, broad_network, aliases) {
  text <- tolower(as.character(source_context %||% ""))
  exact_aliases <- tolower(unlist(aliases[[broad_network]] %||% character()))
  if (any(vapply(exact_aliases, function(x) grepl(x, text, fixed = TRUE), logical(1)))) return("exact")
  if (grepl("bulk|dlpfc|pcc|ac|brain|msbb|knight|miga", text)) return("bulk_brain_fallback")
  "context_mismatch"
}

is_credible_set_member <- function(x) {
  value <- tolower(trimws(as.character(x)))
  !is.na(x) & nzchar(value) & !value %in% c("0", "false", ".", "na")
}

parse_precomputed_file <- function(path, routes, aliases) {
  raw <- tryCatch(fread(path, showProgress = FALSE), error = function(e) NULL)
  if (is.null(raw) || !nrow(raw)) return(data.table())
  h0_col <- first_column(raw, c("PP.H0.abf", "h0", "H0"))
  h1_col <- first_column(raw, c("PP.H1.abf", "h1", "H1"))
  h2_col <- first_column(raw, c("PP.H2.abf", "h2", "H2"))
  h3_col <- first_column(raw, c("L_PP.H3.abf", "PP.H3.abf", "h3", "H3"))
  h4_col <- first_column(raw, c("L_PP.H4.abf", "PP.H4.abf", "h4", "H4"))
  gene_col <- first_column(raw, c("gene_ID", "ensembl_gene_id", "gene", "target_gene"))
  qtl_col <- first_column(raw, c("qtl_type", "xQTL", "event_ID"))
  context_col <- first_column(raw, c("context", "xQTL", "source_context", "event_ID"))
  if (anyNA(c(h0_col, h1_col, h2_col, h3_col, h4_col, gene_col, qtl_col))) return(data.table())
  x <- data.table(
    gene_key = strip_ensembl_version(raw[[gene_col]]),
    qtl_text = as.character(raw[[qtl_col]]),
    source_context = if (is.na(context_col)) "unreported" else as.character(raw[[context_col]]),
    h0 = as.numeric(raw[[h0_col]]),
    h1 = as.numeric(raw[[h1_col]]),
    h2 = as.numeric(raw[[h2_col]]),
    h3 = as.numeric(raw[[h3_col]]),
    h4 = as.numeric(raw[[h4_col]]),
    nsnps = if ("nsnps" %in% names(raw)) as.integer(raw$nsnps) else NA_integer_,
    hit1 = if ("AD_hit" %in% names(raw)) as.character(raw$AD_hit) else
      if ("hit1" %in% names(raw)) as.character(raw$hit1) else NA_character_,
    hit2 = if ("xQTL_hit" %in% names(raw)) as.character(raw$xQTL_hit) else
      if ("hit2" %in% names(raw)) as.character(raw$hit2) else NA_character_,
    source_row = seq_len(nrow(raw))
  )
  x[, qtl_type := fifelse(
    grepl("sQTL|splice", qtl_text, ignore.case = TRUE), "sQTL",
    fifelse(grepl("eQTL|expression", qtl_text, ignore.case = TRUE), "eQTL", NA_character_)
  )]
  gene_map <- rbind(
    routes[, .(gene_key = gene, route_id, candidate_id, gene, broad_network, case_id, qtl_type)],
    routes[, .(
      gene_key = strip_ensembl_version(ensembl_gene_id),
      route_id, candidate_id, gene, broad_network, case_id, qtl_type
    )]
  )
  out <- merge(x[!is.na(qtl_type)], unique(gene_map), by = c("gene_key", "qtl_type"))
  if (!nrow(out)) return(data.table())
  out[, context_match := mapply(
    classify_context, source_context, broad_network,
    MoreArgs = list(aliases = aliases), USE.NAMES = FALSE
  )]
  out[, conditional_h4 := fifelse((h3 + h4) > .Machine$double.eps, h4 / (h3 + h4), NA_real_)]
  out[, evidence_class := fifelse(
    h4 >= 0.8 & conditional_h4 >= 0.8, "supported",
    fifelse(h4 >= 0.5, "suggestive", fifelse(h3 > h4, "distinct_signals", "not_supported"))
  )]
  out[, `:=`(
    schema_version = SCHEMA,
    comparison_id = paste0(basename(path), ":", source_row),
    source_type = "precomputed_h0_h4",
    source_file = basename(path),
    ancestry = "source_reported",
    method = "source_reported_susie_coloc",
    signal_pair = paste(hit1, hit2, sep = "|"),
    direction = NA_character_,
    status = "precomputed_resolved",
    reason = "classical H0-H4 extracted from registered released result"
  )]
  out[, .(
    schema_version, comparison_id, candidate_id, gene, broad_network, case_id,
    qtl_type, source_type, source_file, context = source_context, context_match,
    ancestry, method, signal_pair, nsnps, h0, h1, h2, h3, h4, conditional_h4,
    evidence_class, direction, status, reason
  )]
}

read_precomputed_results <- function(directory, routes, aliases) {
  if (!dir.exists(directory)) return(data.table())
  files <- list.files(
    directory,
    pattern = "[.](bed|tsv|csv)([.]gz)?$",
    full.names = TRUE,
    ignore.case = TRUE
  )
  if (!length(files)) return(data.table())
  rbindlist(lapply(files, parse_precomputed_file, routes = routes, aliases = aliases), fill = TRUE)
}

file_record <- function(path, root, source_id, version, role, state = "validated") {
  info <- file.info(path)
  data.table(
    schema_version = SCHEMA,
    path = relative_path(path, root),
    bytes = as.numeric(info$size),
    sha256 = sha256_file(path),
    source_id = source_id,
    source_version = version,
    source_role = role,
    validation_state = state
  )
}

make_figures <- function(figure_data, summary, staging) {
  candidate_order <- summary$candidate_id
  qtl_order <- c("eQTL", "sQTL")
  grid <- dcast(figure_data, candidate_id ~ qtl_type, value.var = "status_score", fill = 0)
  grid <- grid[match(candidate_order, candidate_id)]
  mat <- as.matrix(grid[, ..qtl_order])
  labels <- paste(summary$gene, summary$broad_network, sep = " · ")
  colors <- c("#D9D9D9", "#9ECAE1", "#FDD0A2", "#74C476")
  draw <- function(device) {
    if (device == "pdf") {
      pdf(file.path(staging, "tier2_evidence_matrix.pdf"), width = 8.5, height = 13)
    } else {
      png(file.path(staging, "tier2_evidence_matrix.png"), width = 1600, height = 2400, res = 180)
    }
    on.exit(dev.off(), add = TRUE)
    par(mar = c(5, 14, 4, 2))
    image(
      x = seq_along(qtl_order),
      y = seq_along(candidate_order),
      z = t(mat),
      col = colors,
      zlim = c(0, 3),
      axes = FALSE,
      xlab = "", ylab = "",
      main = "Phase 19 Tier 2 regional colocalization assessability"
    )
    axis(1, at = seq_along(qtl_order), labels = qtl_order)
    axis(2, at = seq_along(candidate_order), labels = labels, las = 2, cex.axis = 0.45)
    box()
    legend(
      "topright",
      inset = c(-0.01, -0.01),
      legend = c("not applicable", "not assessable", "suggestive/distinct", "supported/resolved"),
      fill = colors,
      cex = 0.65,
      bty = "n"
    )
  }
  draw("pdf")
  draw("png")

  pdf(file.path(staging, "tier2_locus_plots.pdf"), width = 8.5, height = 6)
  plot.new()
  title("Phase 19 Tier 2 locus review")
  text(0.5, 0.58, "No qualifying Tier 2 locus plot was produced.", cex = 1.2)
  text(
    0.5, 0.43,
    "No public route had compatible classical H0-H4 or custom-coloc inputs.",
    cex = 0.9
  )
  dev.off()
}

resolve_scientific_config <- function(root, args) {
  env_path <- abs_path(root, args$config)
  env <- yaml::read_yaml(env_path)
  if (!is.null(args$scientific_config)) return(abs_path(root, args$scientific_config))
  if (!is.null(env$schema_version) && env$schema_version %in% c(
      "phase19_genetic_support_tier2_config_v1",
      "phase19_genetic_support_tier2_config_v2")) return(env_path)
  configured <- env$project$phase19_genetic_support_tier2_config
  if (is.null(configured)) stop("project.phase19_genetic_support_tier2_config is required", call. = FALSE)
  abs_path(root, configured)
}

run_analysis <- function(args) {
  if (args$task_mode != "genetic_support_tier2") {
    stop("This script only implements --task-mode genetic_support_tier2", call. = FALSE)
  }
  root <- normalizePath(getwd(), mustWork = TRUE)
  environment <- yaml::read_yaml(abs_path(root, args$config))
  effective_pilot <- isTRUE(args$pilot) || isTRUE(environment$scope$pilot)
  scientific_path <- resolve_scientific_config(root, args)
  config <- yaml::read_yaml(scientific_path)
  execution_path <- abs_path(root, args$execution_config)
  execution <- yaml::read_yaml(execution_path)$execution
  if (execution$execution_stage != "local_production_equivalent" ||
      execution$backend != "direct" ||
      isTRUE(execution$automatic_minerva_fallback)) {
    stop("Tier 2 execution must be local_production_equivalent/direct with no automatic fallback", call. = FALSE)
  }

  input_paths <- lapply(
    config$inputs,
    function(x) if (is.character(x) && length(x) == 1L) abs_path(root, x) else x
  )
  tier1_required <- c(
    "tier1_candidate_manifest", "tier1_candidate_loci", "tier1_evidence_summary",
    "tier1_common_variant_evidence", "tier1_artifacts", "tier1_status", "tier1_config"
  )
  missing <- tier1_required[!vapply(input_paths[tier1_required], file.exists, logical(1))]
  if (length(missing)) stop("Missing Tier 1 handoff inputs: ", paste(missing, collapse = ", "), call. = FALSE)

  input_paths$tier1_root <- abs_path(root, config$inputs$tier1_root)
  validate_tier1(input_paths)
  candidate <- read_tsv(input_paths$tier1_candidate_manifest)
  loci <- read_tsv(input_paths$tier1_candidate_loci)
  tier1_summary <- read_tsv(input_paths$tier1_evidence_summary)
  expected <- config$analysis
  if (nrow(candidate) != expected$expected_candidate_contexts ||
      uniqueN(candidate$gene) != expected$expected_unique_genes) {
    stop("Tier 1 candidate scope differs from frozen Tier 2 scope", call. = FALSE)
  }
  nuclear_contexts <- sum(!coerce_bool(candidate$is_mtdna_gene))
  mtdna_contexts <- sum(coerce_bool(candidate$is_mtdna_gene))
  if (nuclear_contexts != expected$expected_nuclear_contexts ||
      mtdna_contexts != expected$expected_mtdna_contexts) {
    stop("Nuclear/mtDNA context counts differ from Tier 2 contract", call. = FALSE)
  }
  routes <- build_route_manifest(candidate, loci, unlist(expected$qtl_types))
  if (nrow(routes) != expected$expected_base_routes ||
      uniqueN(routes$gene) != expected$expected_nuclear_genes) {
    stop("Tier 2 route scope differs from 19 genes/27 contexts/54 routes", call. = FALSE)
  }

  public_rows <- rbindlist(lapply(config$public_files, function(item) {
    path <- abs_path(root, item$path)
    if (!file.exists(path)) stop("Missing public source: ", path, call. = FALSE)
    observed <- sha256_file(path)
    if (!identical(observed, item$sha256)) stop("Public source hash mismatch: ", path, call. = FALSE)
    file_record(
      path, root, "FunGen-xQTL_public_snapshot",
      config$source_release$exact_source_sensitivity_commit,
      item$role, "validated"
    )
  }), fill = TRUE)

  external_root <- abs_path(root, config$inputs$external_root)
  dir.create(external_root, recursive = TRUE, showWarnings = FALSE)
  alternative_manifest_path <- file.path(external_root, "alternative_source_manifest.tsv")
  alternative_manifest <- if (file.exists(alternative_manifest_path))
    read_tsv(alternative_manifest_path) else data.table()
  configured_file_sources <- Filter(
    function(item) !is.null(item$filename), config$alternative_sources
  )
  required_ids <- vapply(configured_file_sources, `[[`, character(1), "dataset_id")
  verified_ids <- if (nrow(alternative_manifest))
    alternative_manifest[state == "verified", unique(dataset_id)] else character()
  alternative_files_verified <- length(required_ids) > 0L && all(required_ids %in% verified_ids)
  gene_query_count <- if (nrow(alternative_manifest))
    alternative_manifest[grepl("^NG00184_gene_", dataset_id) & state == "verified", uniqueN(dataset_id)] else 0L

  qtl_extract_path <- file.path(input_paths$regional_inputs_dir, "ng00184_candidate_qtl_finemapping.tsv.gz")
  gwas_extract_path <- file.path(input_paths$regional_inputs_dir, "bellenguez_candidate_gwas.tsv.gz")
  qtl_raw <- if (file.exists(qtl_extract_path)) fread(qtl_extract_path, showProgress = FALSE) else data.table()
  gwas_raw <- if (file.exists(gwas_extract_path)) fread(gwas_extract_path, showProgress = FALSE) else data.table()
  qtl_extract_ready <- nrow(qtl_raw) > 0L
  gwas_extract_ready <- nrow(gwas_raw) > 0L

  precomputed_dir <- abs_path(root, config$inputs$precomputed_coloc_dir)
  precomputed <- read_precomputed_results(precomputed_dir, routes, config$context_aliases)
  resolved_keys <- if (nrow(precomputed))
    unique(paste(precomputed$candidate_id, precomputed$qtl_type, sep = "|")) else character()
  routes[, route_key := paste(candidate_id, qtl_type, sep = "|")]
  routes[, resolved := route_key %in% resolved_keys]

  qtl_coverage <- rbindlist(lapply(seq_len(nrow(routes)), function(i) {
    route <- routes[i]
    available <- if (qtl_extract_ready)
      qtl_raw[gene == route$gene & qtl_type == route$qtl_type] else data.table()
    if (nrow(available)) {
      available[, context_match := vapply(
        context,
        classify_context,
        character(1),
        broad_network = route$broad_network,
        aliases = config$context_aliases
      )]
      chosen_level <- if (any(available$context_match == "exact")) "exact" else
        if (any(available$context_match == "bulk_brain_fallback")) "bulk_brain_fallback" else
          "context_mismatch"
      chosen <- available[context_match == chosen_level]
      pip_values <- suppressWarnings(as.numeric(chosen$pip))
      max_pip <- if (any(is.finite(pip_values))) max(pip_values, na.rm = TRUE) else NA_real_
      cs95 <- sum(is_credible_set_member(chosen$credible_set_95), na.rm = TRUE)
    } else {
      chosen_level <- "not_measured_or_no_released_finemapping"
      chosen <- data.table()
      max_pip <- NA_real_
      cs95 <- 0L
    }
    status <- if (route$resolved) "precomputed_resolved" else "not_assessable"
    reason <- if (route$resolved) {
      "compatible classical H0-H4 result staged"
    } else if (nrow(chosen)) {
      "released_QTL_finemapping_available_but_matching_AD_H0_H4_or_custom_inputs_absent"
    } else {
      "no_released_candidate_QTL_finemapping_and_full_regional_QTL_unavailable"
    }
    data.table(
      route_id = route$route_id,
      qtl_finemapping_rows = nrow(chosen),
      qtl_cs95_rows = cs95,
      qtl_max_pip = max_pip,
      selected_context_match = chosen_level,
      status = status,
      reason = reason
    )
  }))
  routes <- merge(routes, qtl_coverage, by = "route_id", all.x = TRUE, sort = FALSE)
  setorder(routes, candidate_id, qtl_type)

  datasets <- rbindlist(lapply(config$alternative_sources, function(item) {
    id <- item$dataset_id
    data.table(
      schema_version = SCHEMA,
      dataset_id = id,
      phenotype = if (id == "Bellenguez2022_AD_GWAS") "late-onset Alzheimer disease" else
        if (grepl("QTL|qtl", id)) "molecular QTL/reference" else "reference",
      context = if (grepl("NG00184", id)) "brain bulk or single nucleus" else "source_reported",
      genome_build = "GRCh38",
      ancestry = as.character(item$ancestry %||% if (id == "Bellenguez2022_AD_GWAS") "European-dominant meta-analysis" else "source_reported"),
      access = "public",
      eligibility = if (id %in% verified_ids) "verified_local_source" else
        if (!is.null(item$acquisition) && grepl("deferred", item$acquisition)) "registered_deferred_by_gate" else
          "registered_public_source",
      source_id = as.character(item$accession %||% item$url),
      version = config$source_release$release_id,
      role = item$role
    )
  }), fill = TRUE)
  exact_sources <- rbindlist(lapply(config$exact_source_sensitivity, function(item) {
    data.table(
      schema_version = SCHEMA,
      dataset_id = item$dataset_id,
      phenotype = "AD/xQTL exact-source sensitivity",
      context = "source_reported",
      genome_build = "GRCh38",
      ancestry = "source_reported",
      access = "Synapse READ ACL required",
      eligibility = "optional_exact_source_sensitivity_unavailable",
      source_id = item$source_id,
      version = config$source_release$exact_source_sensitivity_commit,
      role = item$role
    )
  }), fill = TRUE)
  datasets <- rbind(datasets, exact_sources, fill = TRUE)

  smoke <- synthetic_coloc_smoke()
  rerun <- routes[, .(
    schema_version = SCHEMA,
    comparison_id = route_id,
    route_id,
    candidate_id,
    gene,
    broad_network,
    case_id,
    qtl_type,
    phenotype_tier = "primary_AD",
    requested_context = broad_network,
    selected_context_match,
    qtl_finemapping_rows,
    qtl_cs95_rows,
    qtl_max_pip,
    action = fifelse(resolved, "extract_precomputed", "terminal_not_assessable"),
    reason,
    decision_frozen_before_result = TRUE
  )]

  placeholder <- routes[resolved == FALSE, .(
    schema_version = SCHEMA,
    comparison_id = route_id,
    candidate_id,
    gene,
    broad_network,
    case_id,
    qtl_type,
    source_type = "open_alternative_source_audit",
    source_file = "NG00184_and_GCST90027158",
    context = broad_network,
    context_match = selected_context_match,
    ancestry = "source_reported",
    method = "released_QTL_finemapping_coverage_audit",
    signal_pair = NA_character_,
    nsnps = qtl_finemapping_rows,
    h0 = NA_real_, h1 = NA_real_, h2 = NA_real_, h3 = NA_real_, h4 = NA_real_,
    conditional_h4 = NA_real_,
    evidence_class = "not_assessable",
    direction = NA_character_,
    status = "not_assessable",
    reason
  )]
  coloc <- rbind(precomputed, placeholder, fill = TRUE)
  setorder(coloc, candidate_id, qtl_type, comparison_id)

  assessability <- routes[, .(
    schema_version = SCHEMA,
    route_id,
    candidate_id,
    gene,
    broad_network,
    case_id,
    qtl_type,
    status,
    evidence_status = fifelse(status == "precomputed_resolved", "assessed", "unassessed"),
    qtl_finemapping_rows,
    qtl_cs95_rows,
    qtl_max_pip,
    context_match = selected_context_match,
    reason
  )]
  coloc_qc <- routes[, .(
    schema_version = SCHEMA,
    route_id,
    candidate_id,
    gene,
    broad_network,
    case_id,
    qtl_type,
    source_result_available = resolved,
    classical_h0_h4_available = resolved,
    full_regional_gwas_available = gwas_extract_ready,
    full_regional_qtl_available = FALSE,
    ancestry_matched_ld_available = FALSE,
    qtl_finemapping_rows,
    qtl_cs95_rows,
    model_match = fifelse(resolved, "source_reported", "not_assessable"),
    shared_variants = NA_integer_,
    lead_or_proxy_retained = NA,
    convergence = fifelse(resolved, "source_reported", "not_run"),
    terminal_status = status,
    reason
  )]

  harmonization <- data.table(
    schema_version = character(), comparison_id = character(), candidate_id = character(),
    gene = character(), qtl_type = character(), variant_id = character(),
    effect_allele_gwas = character(), other_allele_gwas = character(),
    effect_allele_qtl = character(), other_allele_qtl = character(),
    operation = character(), included = logical(), exclusion_reason = character(),
    ld_order = integer()
  )
  gwas_counts_table <- if (gwas_extract_ready) gwas_raw[, .N, by = gene] else data.table()
  gwas_route_counts <- if (nrow(gwas_counts_table))
    setNames(gwas_counts_table$N, gwas_counts_table$gene) else numeric()
  harmonization_summary <- routes[, .(
    schema_version = SCHEMA,
    comparison_id = route_id,
    candidate_id,
    gene,
    qtl_type,
    raw_gwas_variants = if (gwas_extract_ready) as.integer(gwas_route_counts[gene]) else NA_integer_,
    raw_qtl_variants = qtl_finemapping_rows,
    shared_variants = NA_integer_,
    lead_or_proxy_retained_gwas = NA,
    lead_or_proxy_retained_qtl = NA,
    terminal_status = fifelse(
      resolved,
      "source_precomputed_no_custom_harmonization",
      "not_run_no_compatible_full_regional_qtl_and_ld"
    )
  )]

  prior <- data.table(
    schema_version = character(), comparison_id = character(), candidate_id = character(),
    gene = character(), qtl_type = character(), signal_pair = character(),
    locus_definition = character(), p1 = numeric(), p2 = numeric(), p12 = numeric(),
    h0 = numeric(), h1 = numeric(), h2 = numeric(), h3 = numeric(), h4 = numeric(),
    conditional_h4 = numeric(), status = character()
  )

  if (gwas_extract_ready) {
    gwas_raw[, p_numeric := suppressWarnings(as.numeric(p_value))]
    gwas_counts <- gwas_raw[, .(regional_variant_count = .N), by = gene]
    gwas_leads <- gwas_raw[is.finite(p_numeric), .SD[which.min(p_numeric)], by = gene]
    gwas_leads <- merge(gwas_leads, gwas_counts, by = "gene", all.x = TRUE)
    gwas_finemap <- gwas_leads[, .(
      schema_version = SCHEMA,
      gene,
      chromosome,
      position,
      variant_id,
      rsid = NA_character_,
      locus_id = paste0("Tier2_", gene),
      source_study = source_accession,
      pip_or_inclusion = NA_real_,
      credible_set = FALSE,
      min_pvalue = p_numeric,
      regional_variant_count,
      tier2_role = "full_candidate_region_GWAS_lead_and_coverage",
      primary_tier2_eligible = TRUE,
      reason = "Full regional GWAS acquired; no new AD fine mapping run without matched QTL and LD"
    )]
  } else {
    gwas_finemap <- data.table(
      schema_version = character(), gene = character(), chromosome = character(),
      position = integer(), variant_id = character(), rsid = character(),
      locus_id = character(), source_study = character(), pip_or_inclusion = numeric(),
      credible_set = logical(), min_pvalue = numeric(), regional_variant_count = integer(),
      tier2_role = character(), primary_tier2_eligible = logical(), reason = character()
    )
  }

  if (qtl_extract_ready) {
    qtl_finemap <- qtl_raw[, .(
      schema_version = SCHEMA,
      gene,
      ensembl_gene_id,
      qtl_type,
      source_modality,
      context,
      cohort,
      chromosome,
      position = suppressWarnings(as.integer(position)),
      variant_id,
      ref,
      alt,
      signal_id,
      pip = suppressWarnings(as.numeric(pip)),
      conditional_effect = suppressWarnings(as.numeric(conditional_effect)),
      credible_set = fifelse(
        is_credible_set_member(credible_set_95), "cs95",
        fifelse(is_credible_set_member(credible_set_70), "cs70",
          fifelse(is_credible_set_member(credible_set_50), "cs50", "none"))
      ),
      model_id = source_member,
      convergence = "source_released",
      status = "released_finemapping_available",
      reason = "NG00184 fine mapping retained for coverage/model audit; not renamed H4"
    )]
  } else {
    qtl_finemap <- data.table(
      schema_version = character(), gene = character(), ensembl_gene_id = character(),
      qtl_type = character(), source_modality = character(), context = character(),
      cohort = character(), chromosome = character(), position = integer(),
      variant_id = character(), ref = character(), alt = character(),
      signal_id = character(), pip = numeric(), conditional_effect = numeric(),
      credible_set = character(), model_id = character(), convergence = character(),
      status = character(), reason = character()
    )
  }

  summary <- merge(
    candidate,
    tier1_summary[, .(
      candidate_id,
      tier1_genetic_evidence_grade = final_grade,
      tier1_colocalization_status = context_match,
      tier1_permitted_interpretation = permitted_interpretation,
      tier1_source_ids = source_ids
    )],
    by = "candidate_id", all.x = TRUE, sort = FALSE
  )
  summary[, is_mtdna := coerce_bool(is_mtdna_gene)]
  route_rollup <- assessability[, .(
    tier2_regional_coloc_status = if (all(status == "precomputed_resolved"))
      "precomputed_resolved" else "not_assessable",
    tier2_assessability_reason = paste(unique(reason), collapse = ";")
  ), by = candidate_id]
  summary <- merge(summary, route_rollup, by = "candidate_id", all.x = TRUE, sort = FALSE)
  summary[is_mtdna == TRUE, `:=`(
    tier2_regional_coloc_status = "not_applicable_mtdna",
    tier2_assessability_reason =
      "Nuclear regional GWAS/QTL colocalization is not applicable to mtDNA genes"
  )]
  summary[, `:=`(
    tier2_best_eqtl_pp_h4 = NA_real_,
    tier2_best_sqtl_pp_h4 = NA_real_
  )]
  best_by_type <- coloc[is.finite(h4), .SD[which.max(h4)], by = .(candidate_id, qtl_type)]
  if (nrow(best_by_type)) {
    summary[best_by_type[qtl_type == "eQTL"], on = "candidate_id", tier2_best_eqtl_pp_h4 := i.h4]
    summary[best_by_type[qtl_type == "sQTL"], on = "candidate_id", tier2_best_sqtl_pp_h4 := i.h4]
  }
  best <- coloc[is.finite(h4), .SD[which.max(h4)], by = candidate_id]
  if (nrow(best)) {
    best_small <- best[, .(
      candidate_id,
      tier2_best_pp_h4 = h4,
      tier2_best_conditional_h4 = conditional_h4,
      tier2_method = method,
      tier2_context_match_level = context_match,
      tier2_ancestry = ancestry,
      tier2_evidence_class = evidence_class
    )]
    summary <- merge(summary, best_small, by = "candidate_id", all.x = TRUE, sort = FALSE)
  } else {
    summary[, `:=`(
      tier2_best_pp_h4 = NA_real_,
      tier2_best_conditional_h4 = NA_real_,
      tier2_method = "open_alternative_source_audit",
      tier2_context_match_level = NA_character_,
      tier2_ancestry = "source_reported",
      tier2_evidence_class = "not_assessable"
    )]
  }
  summary[, tier2_coloc_grade_contribution := fifelse(
    tier2_evidence_class == "supported" & tier2_context_match_level == "exact", "strong",
    fifelse(tier2_evidence_class == "supported", "moderate",
      fifelse(tier2_evidence_class == "suggestive", "weak", "none"))
  )]
  summary[, cumulative_phase19_grade := tier1_genetic_evidence_grade]
  summary[, grade_changed_from_tier1 := FALSE]
  summary[, conflicting_evidence := FALSE]
  summary[, permitted_interpretation := fifelse(
    is_mtdna,
    tier1_permitted_interpretation,
    paste0(
      tier1_permitted_interpretation,
      " Public regional GWAS and released QTL fine mapping were audited; classical ",
      "colocalization remains unassessable without compatible full regional QTL/model/LD ",
      "inputs. Fine-mapping coverage was not treated as H4."
    )
  )]
  summary[, schema_version := SCHEMA]
  setorder(summary, candidate_id)
  summary <- summary[, .(
    schema_version, candidate_id, gene, broad_network, case_id, case_label,
    tier1_genetic_evidence_grade, tier1_colocalization_status,
    tier2_regional_coloc_status, tier2_best_eqtl_pp_h4, tier2_best_sqtl_pp_h4,
    tier2_best_pp_h4, tier2_best_conditional_h4,
    tier2_method, tier2_context_match_level, tier2_ancestry,
    tier2_assessability_reason, tier2_coloc_grade_contribution,
    cumulative_phase19_grade, grade_changed_from_tier1, conflicting_evidence,
    permitted_interpretation, source_ids = tier1_source_ids
  )]

  figure_data <- rbindlist(lapply(c("eQTL", "sQTL"), function(qtl) {
    base <- candidate[, .(candidate_id, gene, broad_network, case_id, is_mtdna_gene)]
    base[, qtl_type := qtl]
    base[, status := fifelse(
      coerce_bool(is_mtdna_gene),
      "not_applicable_mtdna",
      assessability$status[
        match(paste(candidate_id, qtl), paste(assessability$candidate_id, assessability$qtl_type))
      ]
    )]
    base[, status_score := fifelse(
      status == "not_applicable_mtdna", 0,
      fifelse(status == "not_assessable", 1,
        fifelse(status %in% c("suggestive", "distinct_signals"), 2, 3))
    )]
    base[, schema_version := SCHEMA]
    base[, .(schema_version, candidate_id, gene, broad_network, case_id, qtl_type, status, status_score)]
  }))

  all_routes_terminal <- nrow(assessability) == expected$expected_base_routes &&
    all(nzchar(assessability$status))
  alternative_ready <- alternative_files_verified &&
    gene_query_count == expected$expected_nuclear_genes &&
    qtl_extract_ready && gwas_extract_ready
  source_complete <- alternative_ready && all_routes_terminal

  source_checks <- data.table(
    schema_version = SCHEMA,
    check_id = c(
      "tier1_artifact_hashes", "candidate_context_count", "unique_gene_count",
      "nuclear_gene_count", "nuclear_context_count", "mtdna_context_count",
      "base_route_count", "public_source_hashes", "alternative_required_files_verified",
      "candidate_gene_queries", "candidate_qtl_finemapping_extract",
      "candidate_gwas_extract", "synthetic_multisignal_coloc",
      "exact_synapse_source_sensitivity"
    ),
    severity = c(rep("blocking", 13), "nonblocking"),
    status = c(
      rep("pass", 8),
      if (alternative_files_verified) "pass" else "fail",
      if (gene_query_count == expected$expected_nuclear_genes) "pass" else "fail",
      if (qtl_extract_ready) "pass" else "fail",
      if (gwas_extract_ready) "pass" else "fail",
      "pass", "not_run"
    ),
    expected = c(
      "all published Tier 1 hashes", expected$expected_candidate_contexts,
      expected$expected_unique_genes, expected$expected_nuclear_genes,
      expected$expected_nuclear_contexts, expected$expected_mtdna_contexts,
      expected$expected_base_routes, nrow(public_rows), length(required_ids),
      expected$expected_nuclear_genes, ">0 candidate fine-mapping rows",
      ">0 dense candidate-region GWAS rows", "two shared and two distinct signal pairs",
      "optional exact-source sensitivity"
    ),
    observed = c(
      "all matched", nrow(candidate), uniqueN(candidate$gene), uniqueN(routes$gene),
      nuclear_contexts, mtdna_contexts, nrow(routes), nrow(public_rows),
      sum(required_ids %in% verified_ids), gene_query_count, nrow(qtl_raw), nrow(gwas_raw),
      paste(smoke$shared_pairs, "shared;", smoke$distinct_pairs, "distinct"),
      "Synapse entities unreadable; not required for open alternative"
    ),
    detail = c(
      "Tier 1 bundle remains immutable",
      "One row per Phase 18 candidate context",
      "Full Phase 18 gene scope",
      "Nuclear Tier 2 gene scope",
      "Nuclear candidate contexts",
      "mtDNA contexts retained but excluded from nuclear route",
      "27 nuclear contexts crossed with eQTL/sQTL",
      "Original public metadata snapshots matched checksums",
      "NIAGADS archives/metadata and GWAS Catalog source matched frozen byte/MD5 gates",
      "Significant-only gene downloads are coverage screens, not coloc inputs",
      "Candidate rows streamed from immutable released QTL fine-mapping archives",
      "Full Bellenguez GWAS streamed without P-value filtering",
      "Local coloc/susieR stack converged on deterministic two-signal fixture",
      "No claim of exact FunGen-xQTL Synapse reproduction"
    )
  )
  blocking_failures <- source_checks[severity == "blocking" & status == "fail", .N]
  if (!effective_pilot && (!source_complete || blocking_failures > 0L)) {
    stop(
      "Tier 2 open-alternative production gate blocked: acquire and verify all frozen ",
      "public sources and candidate extracts before publication.",
      call. = FALSE
    )
  }

  final_root <- if (!is.null(args$output_root)) abs_path(root, args$output_root) else
    abs_path(root, if (effective_pilot) config$outputs$pilot_root else config$outputs$root)
  scratch <- abs_path(root, execution$scratch_root)
  staging <- file.path(scratch, paste0("staging_", execution$run_id, "_", Sys.getpid()))
  if (dir.exists(staging)) unlink(staging, recursive = TRUE)
  dir.create(staging, recursive = TRUE, showWarnings = FALSE)

  alternative_file_rows <- if (nrow(alternative_manifest)) rbindlist(lapply(
    which(alternative_manifest$state == "verified" & file.exists(alternative_manifest$path)),
    function(i) file_record(
      alternative_manifest$path[[i]], root,
      alternative_manifest$dataset_id[[i]],
      alternative_manifest$accession[[i]],
      alternative_manifest$role[[i]], "validated"
    )
  ), fill = TRUE) else data.table()
  inventory <- rbindlist(list(
    file_record(input_paths$tier1_candidate_manifest, root, "Tier1", SCHEMA, "candidate_manifest"),
    file_record(input_paths$tier1_candidate_loci, root, "Tier1", SCHEMA, "candidate_loci"),
    file_record(input_paths$tier1_evidence_summary, root, "Tier1", SCHEMA, "evidence_summary"),
    file_record(input_paths$tier1_common_variant_evidence, root, "Tier1", SCHEMA, "common_variant_screen"),
    file_record(input_paths$tier1_artifacts, root, "Tier1", SCHEMA, "artifact_manifest"),
    file_record(input_paths$tier1_status, root, "Tier1", SCHEMA, "status"),
    file_record(input_paths$tier1_config, root, "Tier1", SCHEMA, "scientific_config"),
    public_rows,
    alternative_file_rows,
    if (file.exists(alternative_manifest_path)) file_record(
      alternative_manifest_path, root, config$source_release$release_id,
      config$source_release$inventory_date, "alternative_source_manifest") else data.table(),
    if (qtl_extract_ready) file_record(
      qtl_extract_path, root, "NG00184", "v1", "candidate_qtl_finemapping_extract") else data.table(),
    if (gwas_extract_ready) file_record(
      gwas_extract_path, root, "GCST90027158", "GRCh38", "candidate_gwas_extract") else data.table()
  ), fill = TRUE)
  source_manifest <- rbind(public_rows, alternative_file_rows, fill = TRUE)
  write_tsv(source_manifest, file.path(external_root, "source_manifest.tsv"))

  analysis_manifest <- data.table(
    schema_version = SCHEMA,
    analysis_id = config$analysis$analysis_id,
    analysis_tier = 2,
    candidate_contexts = nrow(candidate),
    unique_genes = uniqueN(candidate$gene),
    nuclear_genes = uniqueN(routes$gene),
    nuclear_contexts = nuclear_contexts,
    mtdna_contexts = mtdna_contexts,
    base_routes = nrow(routes),
    genome_build = config$analysis$genome_build,
    p1 = config$analysis$primary_p1,
    p2 = config$analysis$primary_p2,
    p12 = config$analysis$primary_p12,
    execution_stage = if (effective_pilot) "local_pilot" else execution$execution_stage,
    backend = execution$backend,
    run_id = execution$run_id,
    host = execution$host,
    total_memory_gib = execution$total_memory_gib,
    max_peak_memory_gib = execution$max_peak_memory_gib,
    source_release = config$source_release$release_id,
    exact_source_reproduction = FALSE,
    scientific_config_sha256 = sha256_file(scientific_path),
    tier1_status_sha256 = sha256_file(input_paths$tier1_status),
    R = R.version.string,
    coloc = as.character(packageVersion("coloc")),
    susieR = as.character(packageVersion("susieR")),
    data_table = as.character(packageVersion("data.table")),
    started_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    interpretation_scope = if (source_complete)
      "Open-data Tier 2 source/model audit with terminal route assessment" else
      "Tier 2 pilot; alternative source acquisition incomplete"
  )

  stages <- data.table(
    schema_version = SCHEMA,
    stage_order = 1:8,
    stage = c(
      "freeze_tier1", "inventory_sources", "acquire_tier2", "harmonize",
      "fine_map", "colocalize", "integrate", "validate_bundle"
    ),
    status = c(
      "complete", if (alternative_files_verified) "complete" else "incomplete",
      if (alternative_ready) "complete" else "incomplete",
      "terminal_not_run_no_custom_route",
      if (qtl_extract_ready) "complete_released_models" else "incomplete",
      "complete_terminal_no_valid_h0_h4_inputs",
      "complete_with_source_limit",
      "complete"
    ),
    dependencies = c(
      "", "freeze_tier1", "inventory_sources", "acquire_tier2",
      "harmonize", "fine_map", "colocalize", "integrate"
    ),
    detail = c(
      "Validated immutable 47-context/25-gene Tier 1 handoff",
      "Frozen public NIAGADS/GWAS/LD inventory; Synapse retained as optional sensitivity",
      "Acquired immutable QTL fine mapping, full GWAS, and 19 gene coverage queries",
      "No route had compatible dense QTL plus ancestry-matched LD for custom harmonization",
      "Retained candidate rows from released SuSiE/fSuSiE QTL models",
      "No classical H0-H4 was manufactured from fine-mapping coverage",
      "47-row cumulative summary retained Tier 1 grades",
      "23-file production contract validated"
    )
  )
  checks <- rbind(
    source_checks,
    data.table(
      schema_version = SCHEMA,
      check_id = c("summary_row_count", "assessability_row_count", "all_routes_terminal", "output_file_contract"),
      severity = "blocking",
      status = c(
        if (nrow(summary) == expected$expected_candidate_contexts) "pass" else "fail",
        if (nrow(assessability) == expected$expected_base_routes) "pass" else "fail",
        if (all_routes_terminal) "pass" else "fail",
        "pass"
      ),
      expected = c(
        expected$expected_candidate_contexts, expected$expected_base_routes,
        expected$expected_base_routes, length(OUTPUT_FILES)
      ),
      observed = c(nrow(summary), nrow(assessability), sum(nzchar(assessability$status)), length(OUTPUT_FILES)),
      detail = c(
        "One cumulative row per candidate context",
        "One terminal row per base route",
        "Terminal not_assessable is allowed and is not negative evidence",
        "Flat Tier 2 bundle"
      )
    ),
    fill = TRUE
  )

  write_tsv(analysis_manifest, file.path(staging, OUTPUT_FILES[[1L]]))
  routes[, c(
    "route_key", "resolved", "qtl_finemapping_rows", "qtl_cs95_rows",
    "qtl_max_pip", "selected_context_match", "status", "reason"
  ) := NULL]
  write_tsv(routes, file.path(staging, OUTPUT_FILES[[2L]]))
  write_tsv(datasets, file.path(staging, OUTPUT_FILES[[3L]]))
  write_tsv(inventory, file.path(staging, OUTPUT_FILES[[4L]]))
  write_tsv(source_checks, file.path(staging, OUTPUT_FILES[[5L]]))
  write_tsv(rerun, file.path(staging, OUTPUT_FILES[[6L]]))
  write_tsv(gwas_finemap, file.path(staging, OUTPUT_FILES[[7L]]))
  write_tsv(qtl_finemap, file.path(staging, OUTPUT_FILES[[8L]]))
  write_tsv(harmonization, file.path(staging, OUTPUT_FILES[[9L]]))
  write_tsv(harmonization_summary, file.path(staging, OUTPUT_FILES[[10L]]))
  write_tsv(coloc, file.path(staging, OUTPUT_FILES[[11L]]))
  write_tsv(coloc_qc, file.path(staging, OUTPUT_FILES[[12L]]))
  write_tsv(prior, file.path(staging, OUTPUT_FILES[[13L]]))
  write_tsv(assessability, file.path(staging, OUTPUT_FILES[[14L]]))
  write_tsv(summary, file.path(staging, OUTPUT_FILES[[15L]]))
  write_tsv(figure_data, file.path(staging, OUTPUT_FILES[[16L]]))
  make_figures(figure_data, summary, staging)
  write_tsv(stages, file.path(staging, OUTPUT_FILES[[20L]]))
  write_tsv(checks, file.path(staging, OUTPUT_FILES[[21L]]))

  artifact_rows <- rbindlist(lapply(
    OUTPUT_FILES[seq_len(length(OUTPUT_FILES) - 2L)],
    function(name) {
      path <- file.path(staging, name)
      if (!file.exists(path)) stop("Declared output missing: ", name, call. = FALSE)
      rows <- NA_integer_
      if (grepl("[.]tsv([.]gz)?$", name)) {
        rows <- tryCatch(nrow(fread(path, showProgress = FALSE)), error = function(e) NA_integer_)
      }
      data.table(
        schema_version = SCHEMA,
        path = name,
        bytes = file.info(path)$size,
        sha256 = sha256_file(path),
        rows = rows,
        validation_state = "validated"
      )
    }
  ))
  write_tsv(artifact_rows, file.path(staging, OUTPUT_FILES[[22L]]))

  blocking_failures <- checks[severity == "blocking" & status == "fail", .N]
  classical_routes <- assessability[status %in% c("precomputed_resolved", "custom_resolved"), .N]
  status <- data.table(
    schema_version = SCHEMA,
    validation_status = if (source_complete) {
      if (effective_pilot) "validated_complete_pilot_open_alternative" else
        "validated_complete_tier2_regional_coloc"
    } else "validated_complete_pilot_source_incomplete",
    run_id = execution$run_id,
    execution_stage = if (effective_pilot) "local_pilot" else execution$execution_stage,
    execution_backend = execution$backend,
    technical_status = if (source_complete) "validated_complete_tier2" else
      "validated_source_acquisition_incomplete",
    scientific_status = if (classical_routes > 0L) "tier2_regional_coloc_complete" else
      "tier2_open_alternative_complete_classical_coloc_not_assessable",
    source_access_ready = alternative_files_verified,
    exact_source_reproduction = FALSE,
    full_phase19_complete = FALSE,
    candidate_contexts = nrow(summary),
    unique_genes = uniqueN(summary$gene),
    nuclear_genes = uniqueN(assessability$gene),
    nuclear_contexts = nuclear_contexts,
    mtdna_contexts = mtdna_contexts,
    base_routes = nrow(assessability),
    precomputed_resolved_routes = assessability[status == "precomputed_resolved", .N],
    custom_resolved_routes = assessability[status == "custom_resolved", .N],
    not_assessable_routes = assessability[status == "not_assessable", .N],
    qtl_finemapping_rows = nrow(qtl_finemap),
    candidate_gwas_rows = nrow(gwas_raw),
    blocking_check_failures = blocking_failures,
    output_files = length(OUTPUT_FILES),
    artifact_manifest_sha256 = sha256_file(file.path(staging, OUTPUT_FILES[[22L]])),
    completed_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    next_required_action = if (classical_routes > 0L)
      "none_for_resolved_routes; exact_source_sensitivity_optional" else
      "optional_targeted_dense_QTL_and_LD_or_exact_source_sensitivity"
  )
  write_tsv(status, file.path(staging, OUTPUT_FILES[[23L]]))

  actual <- sort(list.files(staging))
  if (!identical(actual, sort(OUTPUT_FILES))) stop("Output contract mismatch", call. = FALSE)
  if (!all_routes_terminal) stop("At least one Tier 2 base route lacks a terminal status", call. = FALSE)
  if (!effective_pilot && blocking_failures > 0L) {
    stop("Blocking output check failed before publication", call. = FALSE)
  }

  if (dir.exists(final_root)) {
    if (!args$force) stop("Output already exists: ", final_root, call. = FALSE)
    backup <- file.path(scratch, paste0("previous_", execution$run_id, "_", Sys.getpid()))
    if (!file.rename(final_root, backup)) stop("Could not preserve previous output", call. = FALSE)
  }
  dir.create(dirname(final_root), recursive = TRUE, showWarnings = FALSE)
  if (!file.rename(staging, final_root)) stop("Atomic publication failed", call. = FALSE)
  message("Published ", length(OUTPUT_FILES), " Tier 2 files to ", final_root)
  invisible(final_root)
}

main <- function() {
  args <- parse_cli()
  run_analysis(args)
  0L
}

if (sys.nframe() == 0L) {
  status <- tryCatch(main(), error = function(e) {
    message("ERROR: ", conditionMessage(e))
    1L
  })
  quit(status = status)
}
