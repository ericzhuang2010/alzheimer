#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, manifest_row = NULL,
    rds_id = NULL, task_mode = "pathways"
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
        "Usage: Rscript scripts/09_run_mito_pathways.R --config FILE ",
        "[--execution-config FILE] [--manifest-row N | --rds-id ID] ",
        "[--task-mode pathways]\n",
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
  if (!identical(out$task_mode, "pathways")) {
    stop("--task-mode must be 'pathways'", call. = FALSE)
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

sha256_lines <- function(values) {
  path <- tempfile("phase09_background_", fileext = ".txt")
  on.exit(unlink(path), add = TRUE)
  writeLines(sort(unique(as.character(values))), path, useBytes = TRUE)
  sha256_file(path)
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

read_status <- function(path, expected_schema) {
  if (!file.exists(path)) stop("Required status file is missing: ", path, call. = FALSE)
  value <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
  if (nrow(value) != 1L || !identical(value$schema_version[[1L]], expected_schema) ||
      !identical(value$validation_status[[1L]], "validated_complete")) {
    stop("Required status is not validated_complete: ", path, call. = FALSE)
  }
  value
}

split_pathway_genes <- function(value) {
  genes <- trimws(strsplit(as.character(value), ",", fixed = TRUE)[[1L]])
  sort(unique(genes[nzchar(genes)]))
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table", "Matrix")
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root), mustWork = TRUE
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
} else {
  enabled <- if ("enabled" %in% names(rds_manifest)) as_logical(rds_manifest$enabled) else rep(TRUE, nrow(rds_manifest))
  selected <- rds_manifest[enabled, , drop = FALSE]
}
if (nrow(selected) != 1L) {
  stop("RDS manifest selection must identify exactly one row", call. = FALSE)
}

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct", run_id = "manual_pathways"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

rds_id <- as.character(selected$rds_id[[1L]])
source_rel <- as.character(selected$input_rds[[1L]])
prefix <- tolower(rds_id)
base_name <- sub("[.][Rr][Dd][Ss]$", "", basename(source_rel))

pseudobulk_de_path <- file.path(
  output_root, "07_pseudobulk_de", paste0(prefix, ".pseudobulk_de.tsv.gz")
)
pseudobulk_de_status_path <- file.path(
  output_root, "07_pseudobulk_de", paste0(prefix, ".pseudobulk_de_status.tsv")
)
mast_path <- file.path(output_root, "08_mast", paste0(prefix, ".mast_de.tsv.gz"))
mast_status_path <- file.path(output_root, "08_mast", paste0(prefix, ".mast_de_status.tsv"))
read_status(pseudobulk_de_status_path, "pseudobulk_de_status_v1")
read_status(mast_status_path, "mast_de_status_v1")

bundle_candidates <- list.files(
  file.path(output_root, "07_pseudobulk"),
  pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE
)
bundle_match <- vapply(bundle_candidates, function(path) {
  value <- readRDS(path)
  identical(as.character(value$rds_id), rds_id)
}, logical(1))
bundle_path <- bundle_candidates[bundle_match]
if (length(bundle_path) != 1L) stop("Pseudobulk bundle selection must identify one file", call. = FALSE)
bundle <- readRDS(bundle_path)
if (!identical(bundle$schema_version, "pseudobulk_counts_v1")) {
  stop("Unsupported pseudobulk bundle schema", call. = FALSE)
}

pathway_path <- file.path(output_root, "03_annotations", "mitocarta_pathways.tsv")
tested_universe_path <- file.path(output_root, "03_annotations", "tested_gene_universe.tsv")
annotation_status_path <- file.path(output_root, "03_annotations", "annotation_status.tsv")
read_status(annotation_status_path, "mito_annotations_status_v1")
if (!file.exists(pathway_path) || !file.exists(tested_universe_path)) {
  stop("Required frozen Phase 03 annotation artifacts are missing", call. = FALSE)
}
mitocarta_source_path <- absolute_path(analysis$references$mitocarta_source, project_root)
mitocarta_source_sha <- sha256_file(mitocarta_source_path)
if (!identical(mitocarta_source_sha, analysis$references$mitocarta_sha256)) {
  stop("MitoCarta source checksum does not match the frozen scientific configuration", call. = FALSE)
}

pathways <- read.delim(pathway_path, check.names = FALSE, stringsAsFactors = FALSE)
if (!all(c("pathway", "hierarchy", "genes") %in% names(pathways)) || !nrow(pathways)) {
  stop("Unsupported or empty MitoCarta pathway table", call. = FALSE)
}
pathway_source_rows <- nrow(pathways)
valid_pathway <- !is.na(pathways$pathway) & nzchar(trimws(pathways$pathway)) &
  !is.na(pathways$hierarchy) & nzchar(trimws(pathways$hierarchy)) &
  !is.na(pathways$genes) & nzchar(trimws(pathways$genes))
excluded_blank_pathway_rows <- sum(!valid_pathway)
pathways <- pathways[valid_pathway, , drop = FALSE]
if (!nrow(pathways) || anyDuplicated(pathways$hierarchy)) {
  stop("Named MitoCarta pathway hierarchies must be nonempty and unique", call. = FALSE)
}
pathway_gene_sets <- setNames(lapply(pathways$genes, split_pathway_genes), pathways$pathway)

pseudobulk <- data.table::fread(pseudobulk_de_path, data.table = FALSE)
mast <- data.table::fread(mast_path, data.table = FALSE)
if (!nrow(pseudobulk) || !nrow(mast)) stop("Phase 07 or Phase 08 contains no gene-level results", call. = FALSE)

make_branch <- function(table, branch) {
  if (identical(branch, "pseudobulk")) {
    statistic <- sign(table$logFC) * sqrt(pmax(as.numeric(table$F), 0))
    significant <- as.numeric(table$fdr_bh_within_contrast) < 0.05
    method <- "signed_sqrt_edgeR_QLF"
  } else {
    p_value <- pmax(as.numeric(table$p_value), .Machine$double.xmin)
    statistic <- sign(table$logFC) * stats::qnorm(p_value / 2, lower.tail = FALSE)
    significant <- as_logical(table$paper_deg)
    method <- "signed_MAST_normal_score"
  }
  data.frame(
    branch = branch, rds_id = table$rds_id,
    cell_type_high_resolution = table$cell_type_high_resolution,
    contrast_id = table$contrast_id, contrast_family = table$contrast_family,
    contrast_name = table$contrast_name, gene = table$gene,
    signed_statistic = statistic, significant_gene = significant,
    ranking_method = method, stringsAsFactors = FALSE
  )
}

ranked <- rbind(make_branch(pseudobulk, "pseudobulk"), make_branch(mast, "mast"))
ranked <- ranked[is.finite(ranked$signed_statistic) & !is.na(ranked$gene) & nzchar(ranked$gene), , drop = FALSE]
ranked$key <- paste(ranked$branch, ranked$contrast_id, sep = "\r")

minimum_pathway_genes <- 5L
pathway_result_list <- list()
for (key in unique(ranked$key)) {
  table <- ranked[ranked$key == key, , drop = FALSE]
  if (anyDuplicated(table$gene)) stop("Duplicate genes in ranked contrast: ", key, call. = FALSE)
  background <- sort(unique(table$gene))
  background_sha <- sha256_lines(background)
  statistic <- setNames(table$signed_statistic, table$gene)
  significant <- setNames(table$significant_gene, table$gene)
  for (i in seq_len(nrow(pathways))) {
    members <- intersect(pathway_gene_sets[[pathways$pathway[[i]]]], background)
    nonmembers <- setdiff(background, members)
    terminal_status <- "validated_complete"
    message <- ""
    rank_p <- NA_real_
    mean_member <- NA_real_
    mean_nonmember <- NA_real_
    mean_difference <- NA_real_
    direction <- NA_character_
    ora_odds <- NA_real_
    ora_p <- NA_real_
    significant_in_pathway <- sum(significant[members], na.rm = TRUE)
    significant_background <- sum(significant[background], na.rm = TRUE)
    if (length(members) < minimum_pathway_genes || length(nonmembers) < minimum_pathway_genes) {
      terminal_status <- "ineligible"
      message <- paste0("fewer_than_", minimum_pathway_genes, "_tested_genes_in_pathway_or_complement")
    } else {
      mean_member <- mean(statistic[members])
      mean_nonmember <- mean(statistic[nonmembers])
      mean_difference <- mean_member - mean_nonmember
      direction <- if (mean_difference > 0) "up_in_AD_or_positive_effect" else if (mean_difference < 0) "down_in_AD_or_negative_effect" else "no_direction"
      rank_p <- suppressWarnings(stats::wilcox.test(
        statistic[members], statistic[nonmembers], exact = FALSE
      )$p.value)
      rank_p <- min(max(rank_p, 0), 1)
      a <- significant_in_pathway
      b <- length(members) - a
      c <- significant_background - a
      d <- length(nonmembers) - c
      fisher <- suppressWarnings(stats::fisher.test(matrix(c(a, b, c, d), nrow = 2L, byrow = TRUE)))
      ora_odds <- unname(fisher$estimate)
      ora_p <- min(max(fisher$p.value, 0), 1)
    }
    pathway_result_list[[length(pathway_result_list) + 1L]] <- data.frame(
      schema_version = "mito_pathway_results_v1", execution_stage = execution$execution_stage,
      rds_id = rds_id, source_rds = source_rel, method_branch = table$branch[[1L]],
      cell_type_high_resolution = table$cell_type_high_resolution[[1L]],
      contrast_id = table$contrast_id[[1L]], contrast_family = table$contrast_family[[1L]],
      contrast_name = table$contrast_name[[1L]], ranking_method = table$ranking_method[[1L]],
      pathway = pathways$pathway[[i]], hierarchy = pathways$hierarchy[[i]],
      gene_set_source = "Human_MitoCarta3.0_MitoPathways",
      gene_set_source_sha256 = mitocarta_source_sha,
      pathway_table_sha256 = sha256_file(pathway_path),
      background_sha256 = background_sha, background_genes = length(background),
      pathway_genes_frozen = length(pathway_gene_sets[[pathways$pathway[[i]]]]),
      pathway_genes_tested = length(members),
      rank_mean_pathway = mean_member, rank_mean_complement = mean_nonmember,
      rank_mean_difference = mean_difference, direction = direction,
      rank_p_value = rank_p, rank_fdr_bh_within_branch_contrast = NA_real_,
      significant_background_genes = significant_background,
      significant_pathway_genes = significant_in_pathway,
      ora_odds_ratio = ora_odds, ora_p_value = ora_p,
      ora_fdr_bh_within_branch_contrast = NA_real_,
      terminal_status = terminal_status, message = message,
      stringsAsFactors = FALSE
    )
  }
}
pathway_results <- as.data.frame(data.table::rbindlist(
  pathway_result_list, fill = TRUE, use.names = TRUE
))
family_key <- paste(pathway_results$method_branch, pathway_results$contrast_id, sep = "\r")
for (key in unique(family_key)) {
  index <- which(family_key == key & pathway_results$terminal_status == "validated_complete")
  pathway_results$rank_fdr_bh_within_branch_contrast[index] <- stats::p.adjust(
    pathway_results$rank_p_value[index], method = "BH"
  )
  pathway_results$ora_fdr_bh_within_branch_contrast[index] <- stats::p.adjust(
    pathway_results$ora_p_value[index], method = "BH"
  )
}

samples <- as.data.frame(bundle$samples)
samples$primary_eligible <- as_logical(samples$primary_eligible)
sample_index <- which(samples$primary_eligible)
counts <- bundle$counts[, sample_index, drop = FALSE]
metadata <- samples[sample_index, , drop = FALSE]
if (!identical(colnames(counts), metadata$pseudobulk_id)) {
  stop("Pseudobulk counts and selected sample metadata disagree", call. = FALSE)
}

get_pathway <- function(name) {
  value <- pathway_gene_sets[[name]]
  if (is.null(value)) stop("Required frozen MitoCarta pathway is missing: ", name, call. = FALSE)
  value
}
mtdna_genes <- analysis$mitochondrial_features$mtdna_protein_genes
oxphos_subunits <- get_pathway("OXPHOS subunits")
summary_sets <- list(
  mtdna_oxphos = mtdna_genes,
  nuclear_oxphos = setdiff(oxphos_subunits, mtdna_genes),
  complex_i = get_pathway("CI subunits"),
  complex_ii = get_pathway("CII subunits"),
  complex_iii = get_pathway("CIII subunits"),
  complex_iv = get_pathway("CIV subunits"),
  complex_v = get_pathway("CV subunits"),
  mitochondrial_ribosome = get_pathway("Mitochondrial ribosome"),
  mitochondrial_translation = get_pathway("Translation")
)
measured_sets <- lapply(summary_sets, intersect, y = rownames(counts))
sum_gene_set <- function(genes) {
  if (!length(genes)) return(rep(0, ncol(counts)))
  as.numeric(Matrix::colSums(counts[genes, , drop = FALSE]))
}
set_counts <- lapply(measured_sets, sum_gene_set)
set_sizes <- vapply(measured_sets, length, integer(1))

mitonuclear_balance <- data.frame(
  schema_version = "mitonuclear_balance_v1", execution_stage = execution$execution_stage,
  rds_id = rds_id, source_rds = source_rel,
  pseudobulk_id = metadata$pseudobulk_id, projid = metadata$projid,
  cell_type_high_resolution = metadata$cell_type_high_resolution,
  diagnosis = metadata$diagnosis, sex = metadata$sex, apoe_group = metadata$apoe_group,
  nuclei = metadata$nuclei, total_umi_count = metadata$total_umi_count,
  mtdna_oxphos_umi = set_counts$mtdna_oxphos,
  nuclear_oxphos_umi = set_counts$nuclear_oxphos,
  mtdna_oxphos_measured_genes = set_sizes[["mtdna_oxphos"]],
  nuclear_oxphos_measured_genes = set_sizes[["nuclear_oxphos"]],
  mtdna_oxphos_fraction_total = set_counts$mtdna_oxphos / metadata$total_umi_count,
  nuclear_oxphos_fraction_total = set_counts$nuclear_oxphos / metadata$total_umi_count,
  mitonuclear_log2_per_gene_balance = log2(
    (set_counts$mtdna_oxphos / set_sizes[["mtdna_oxphos"]] + 0.5) /
      (set_counts$nuclear_oxphos / set_sizes[["nuclear_oxphos"]] + 0.5)
  ),
  complex_i_umi = set_counts$complex_i, complex_ii_umi = set_counts$complex_ii,
  complex_iii_umi = set_counts$complex_iii, complex_iv_umi = set_counts$complex_iv,
  complex_v_umi = set_counts$complex_v,
  mitochondrial_ribosome_umi = set_counts$mitochondrial_ribosome,
  mitochondrial_translation_umi = set_counts$mitochondrial_translation,
  complex_i_measured_genes = set_sizes[["complex_i"]],
  complex_ii_measured_genes = set_sizes[["complex_ii"]],
  complex_iii_measured_genes = set_sizes[["complex_iii"]],
  complex_iv_measured_genes = set_sizes[["complex_iv"]],
  complex_v_measured_genes = set_sizes[["complex_v"]],
  mitochondrial_ribosome_measured_genes = set_sizes[["mitochondrial_ribosome"]],
  mitochondrial_translation_measured_genes = set_sizes[["mitochondrial_translation"]],
  gene_set_source = "Human_MitoCarta3.0_MitoPathways",
  gene_set_source_sha256 = mitocarta_source_sha,
  stringsAsFactors = FALSE
)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "mito_pathway_checks_v1", rds_id = rds_id,
    check = check, passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
result_keys <- paste(
  pathway_results$method_branch, pathway_results$contrast_id,
  pathway_results$hierarchy, sep = "\r"
)
eligible_pathways <- pathway_results$terminal_status == "validated_complete"
background_counts <- tapply(pathway_results$background_genes, family_key, unique)
add_check("pathway_result_keys_unique", !anyDuplicated(result_keys), anyDuplicated(result_keys), 0L)
add_check("both_de_branches_present", setequal(unique(pathway_results$method_branch), c("pseudobulk", "mast")), paste(sort(unique(pathway_results$method_branch)), collapse = ";"), "mast;pseudobulk")
add_check("all_named_frozen_pathways_represented", all(table(family_key) == nrow(pathways)), paste(range(table(family_key)), collapse = ";"), nrow(pathways))
add_check("blank_pathway_rows_explicitly_excluded", excluded_blank_pathway_rows == pathway_source_rows - nrow(pathways), excluded_blank_pathway_rows, pathway_source_rows - nrow(pathways))
add_check("backgrounds_nonempty_and_constant", all(pathway_results$background_genes > 0) && all(vapply(background_counts, length, integer(1)) == 1L), min(pathway_results$background_genes), ">0")
add_check("external_gene_set_checksum_present", all(nzchar(pathway_results$gene_set_source_sha256)) && identical(mitocarta_source_sha, analysis$references$mitocarta_sha256), mitocarta_source_sha, analysis$references$mitocarta_sha256)
add_check("rank_p_values_in_range", all(is.finite(pathway_results$rank_p_value[eligible_pathways]) & pathway_results$rank_p_value[eligible_pathways] >= 0 & pathway_results$rank_p_value[eligible_pathways] <= 1), sum(!is.finite(pathway_results$rank_p_value[eligible_pathways])), 0L)
add_check("rank_fdr_in_range", all(is.finite(pathway_results$rank_fdr_bh_within_branch_contrast[eligible_pathways]) & pathway_results$rank_fdr_bh_within_branch_contrast[eligible_pathways] >= 0 & pathway_results$rank_fdr_bh_within_branch_contrast[eligible_pathways] <= 1), sum(!is.finite(pathway_results$rank_fdr_bh_within_branch_contrast[eligible_pathways])), 0L)
add_check("ora_p_values_in_range", all(is.finite(pathway_results$ora_p_value[eligible_pathways]) & pathway_results$ora_p_value[eligible_pathways] >= 0 & pathway_results$ora_p_value[eligible_pathways] <= 1), sum(!is.finite(pathway_results$ora_p_value[eligible_pathways])), 0L)
add_check("mitonuclear_rows_match_primary_samples", nrow(mitonuclear_balance) == sum(samples$primary_eligible), nrow(mitonuclear_balance), sum(samples$primary_eligible))
add_check("mitonuclear_numerator_denominator_present", all(is.finite(mitonuclear_balance$mtdna_oxphos_umi) & is.finite(mitonuclear_balance$nuclear_oxphos_umi) & mitonuclear_balance$total_umi_count > 0), sum(!is.finite(mitonuclear_balance$mitonuclear_log2_per_gene_balance)), 0L)
add_check("execution_stage_recorded", all(pathway_results$execution_stage == execution$execution_stage) && all(mitonuclear_balance$execution_stage == execution$execution_stage), execution$execution_stage, execution$execution_stage)
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "09_downstream")
paths <- list(
  pathways = file.path(output_dir, paste0(prefix, ".pathway_results.tsv")),
  balance = file.path(output_dir, paste0(prefix, ".mitonuclear_balance.tsv")),
  checks = file.path(output_dir, paste0(prefix, ".pathway_checks.tsv")),
  artifacts = file.path(output_dir, paste0(prefix, ".pathway_artifacts.tsv")),
  status = file.path(output_dir, paste0(prefix, ".pathway_status.tsv"))
)
atomic_write_tsv(pathway_results, paths$pathways)
atomic_write_tsv(mitonuclear_balance, paths$balance)
atomic_write_tsv(checks, paths$checks)
artifact_paths <- c(paths$pathways, paths$balance, paths$checks)
artifacts <- data.frame(
  schema_version = "mito_pathway_artifacts_v1", rds_id = rds_id,
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(pathway_results), nrow(mitonuclear_balance), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "mito_pathway_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = paste("pathways", rds_id, sep = ":"),
  source_rds = source_rel,
  scientific_script = "scripts/09_run_mito_pathways.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/09_run_mito_pathways.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(rds_manifest_path),
  pseudobulk_de_sha256 = sha256_file(pseudobulk_de_path),
  mast_de_sha256 = sha256_file(mast_path),
  pseudobulk_bundle_sha256 = sha256_file(bundle_path),
  tested_universe_sha256 = sha256_file(tested_universe_path),
  pathway_table_sha256 = sha256_file(pathway_path),
  gene_set_source_sha256 = mitocarta_source_sha,
  pathway_source_rows = pathway_source_rows,
  pathway_definitions = nrow(pathways),
  excluded_blank_pathway_rows = excluded_blank_pathway_rows,
  de_branches = length(unique(pathway_results$method_branch)),
  branch_contrasts = length(unique(family_key)),
  pathway_result_rows = nrow(pathway_results),
  eligible_pathway_tests = sum(eligible_pathways),
  significant_rank_fdr_005 = sum(pathway_results$rank_fdr_bh_within_branch_contrast < 0.05, na.rm = TRUE),
  significant_ora_fdr_005 = sum(pathway_results$ora_fdr_bh_within_branch_contrast < 0.05, na.rm = TRUE),
  mitonuclear_rows = nrow(mitonuclear_balance),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Pathway results: ", paths$pathways, "\n", sep = "")
cat("Mitonuclear balance: ", paths$balance, "\n", sep = "")
cat("Pathway rows: ", nrow(pathway_results), "\n", sep = "")
cat("Eligible pathway tests: ", sum(eligible_pathways), "\n", sep = "")
cat("Significant ranked pathways (BH FDR < 0.05): ", status$significant_rank_fdr_005, "\n", sep = "")
cat("Pathway status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
