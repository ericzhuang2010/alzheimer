#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = "multiple_testing")
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/11_apply_multiple_testing.R --config FILE ",
        "[--execution-config FILE] [--task-mode multiple_testing]\n",
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
  if (!identical(out$task_mode, "multiple_testing")) {
    stop("--task-mode must be 'multiple_testing'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_tsv <- function(x, path, gzip = FALSE) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid(), if (gzip) ".gz" else "")
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA",
    compress = if (gzip) "gzip" else "none"
  )
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
  path <- tempfile("phase11_inputs_", fileext = ".txt")
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

read_validated_statuses <- function(paths, expected_schema) {
  if (!length(paths) || any(!file.exists(paths))) {
    stop("Required status file is missing for schema ", expected_schema, call. = FALSE)
  }
  values <- lapply(paths, function(path) {
    value <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
    if (nrow(value) != 1L || !identical(value$schema_version[[1L]], expected_schema) ||
        !identical(value$validation_status[[1L]], "validated_complete")) {
      stop("Required status is not validated_complete: ", path, call. = FALSE)
    }
    value
  })
  do.call(rbind, values)
}

read_many <- function(paths) {
  if (!length(paths)) stop("No required result files were found", call. = FALSE)
  data.table::rbindlist(lapply(paths, data.table::fread), fill = TRUE, use.names = TRUE)
}

adjust_subset <- function(p_value, index) {
  adjusted <- rep(NA_real_, length(p_value))
  eligible <- index & is.finite(p_value)
  adjusted[eligible] <- stats::p.adjust(p_value[eligible], method = "BH")
  adjusted
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table")
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
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)

pilot <- isTRUE(config$scope$pilot)
execution <- list(
  execution_stage = if (pilot) "local_pilot" else "minerva_production",
  execution_phase = if (pilot) 1L else 2L,
  backend = "direct", run_id = if (pilot) "manual_local_multiple_testing" else "manual_multiple_testing"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

alpha <- as.numeric(analysis$multiple_testing$alpha %||% 0.05)
yu_fold_change <- as.numeric(
  analysis$multiple_testing$yu_absolute_fold_change_threshold %||% 1.3
)
output_status <- as.character(
  if (pilot) analysis$pilot$output_status else analysis$production$output_status
)
required_families <- c(
  "genomewide_gene_within_method_cell_type_contrast",
  "genomewide_gene_global_across_cell_types_and_contrasts_sensitivity",
  "mtdna_gene_global_across_cell_types_and_contrasts",
  "mitocarta_gene_global_across_cell_types_and_contrasts",
  "pathway_rank_global_across_cell_types_and_contrasts",
  "pathway_ora_global_across_cell_types_and_contrasts",
  "similarity_within_method_comparison",
  "similarity_global_across_comparisons_sensitivity"
)
configured_families <- unlist(analysis$multiple_testing$families, use.names = FALSE)
if (!all(required_families %in% configured_families)) {
  stop(
    "Scientific configuration lacks Phase 11 families: ",
    paste(setdiff(required_families, configured_families), collapse = ", "),
    call. = FALSE
  )
}

pb_dir <- file.path(output_root, "07_pseudobulk_de")
mast_dir <- file.path(output_root, "08_mast")
downstream09_dir <- file.path(output_root, "09_downstream")
downstream10_dir <- file.path(output_root, "10_downstream")
annotation_path <- file.path(output_root, "03_annotations", "tested_gene_universe.tsv")
annotation_status_path <- file.path(output_root, "03_annotations", "annotation_status.tsv")

pb_paths <- list.files(pb_dir, pattern = "[.]pseudobulk_de[.]tsv[.]gz$", full.names = TRUE)
pb_status_paths <- list.files(pb_dir, pattern = "[.]pseudobulk_de_status[.]tsv$", full.names = TRUE)
mast_paths <- list.files(mast_dir, pattern = "[.]mast_de[.]tsv[.]gz$", full.names = TRUE)
mast_status_paths <- list.files(mast_dir, pattern = "[.]mast_de_status[.]tsv$", full.names = TRUE)
pathway_paths <- list.files(downstream09_dir, pattern = "[.]pathway_results[.]tsv$", full.names = TRUE)
pathway_status_paths <- list.files(downstream09_dir, pattern = "[.]pathway_status[.]tsv$", full.names = TRUE)
similarity_path <- file.path(
  downstream10_dir, if (pilot) "similarity_smoke.tsv" else "similarity_results.tsv"
)
similarity_status_path <- file.path(downstream10_dir, "similarity_status.tsv")

pb_status <- read_validated_statuses(pb_status_paths, "pseudobulk_de_status_v1")
mast_status <- read_validated_statuses(mast_status_paths, "mast_de_status_v1")
pathway_status <- read_validated_statuses(pathway_status_paths, "mito_pathway_status_v1")
similarity_status <- read_validated_statuses(similarity_status_path, "similarity_status_v1")
annotation_status <- read_validated_statuses(annotation_status_path, "mito_annotations_status_v1")
if (length(pb_paths) != nrow(pb_status) || length(mast_paths) != nrow(mast_status) ||
    length(pathway_paths) != nrow(pathway_status)) {
  stop("Validated upstream status and result-file counts do not match", call. = FALSE)
}
if (!file.exists(similarity_path) || !file.exists(annotation_path)) {
  stop("Required similarity or annotation result is missing", call. = FALSE)
}

upstream_paths <- c(
  pb_paths, pb_status_paths, mast_paths, mast_status_paths,
  pathway_paths, pathway_status_paths, similarity_path,
  similarity_status_path, annotation_path, annotation_status_path
)
upstream_sha_before <- vapply(upstream_paths, sha256_file, character(1))

annotations <- data.table::fread(annotation_path)
annotation_map <- annotations[, .(
  is_mtdna_protein_gene = any(as_logical(is_mtdna_protein_gene)),
  is_mitocarta = any(as_logical(is_mitocarta))
), by = .(gene = feature)]

make_gene_results <- function(table, branch) {
  required <- c(
    "rds_id", "cell_type_high_resolution", "contrast_id", "contrast_family",
    "contrast_name", "gene", "logFC", "p_value", "fdr_bh_within_contrast"
  )
  missing <- setdiff(required, names(table))
  if (length(missing)) stop(branch, " lacks: ", paste(missing, collapse = ", "), call. = FALSE)
  contrast_kind <- if ("contrast_kind" %in% names(table)) {
    as.character(table$contrast_kind)
  } else {
    rep("single_df", nrow(table))
  }
  data.table::data.table(
    schema_version = "multiple_testing_gene_results_v1",
    execution_stage = execution$execution_stage,
    output_status = output_status,
    method_branch = branch,
    rds_id = as.character(table$rds_id),
    cell_type_high_resolution = as.character(table$cell_type_high_resolution),
    contrast_id = as.character(table$contrast_id),
    contrast_family = as.character(table$contrast_family),
    contrast_name = as.character(table$contrast_name),
    hypothesis_context = ifelse(
      contrast_kind == "interaction_df", "tested_interaction", "within_group_ad_vs_nci"
    ),
    gene = as.character(table$gene),
    logFC = as.numeric(table$logFC),
    p_value = as.numeric(table$p_value),
    fdr_bh_within_contrast = as.numeric(table$fdr_bh_within_contrast),
    within_contrast_family_id = paste0(
      "genomewide_gene_within_method_cell_type_contrast::", branch, "::",
      as.character(table$contrast_id)
    )
  )
}

gene_results <- data.table::rbindlist(list(
  make_gene_results(read_many(pb_paths), "pseudobulk"),
  make_gene_results(read_many(mast_paths), "mast")
), use.names = TRUE)
gene_results <- merge(gene_results, annotation_map, by = "gene", all.x = TRUE, sort = FALSE)
gene_results[is.na(is_mtdna_protein_gene), is_mtdna_protein_gene := FALSE]
gene_results[is.na(is_mitocarta), is_mitocarta := FALSE]
gene_results[, `:=`(
  global_genome_family_id = paste0(
    "genomewide_gene_global_across_cell_types_and_contrasts_sensitivity::",
    method_branch
  ),
  mtdna_family_id = data.table::fifelse(
    is_mtdna_protein_gene,
    paste0("mtdna_gene_global_across_cell_types_and_contrasts::", method_branch),
    NA_character_
  ),
  mitocarta_family_id = data.table::fifelse(
    is_mitocarta,
    paste0("mitocarta_gene_global_across_cell_types_and_contrasts::", method_branch),
    NA_character_
  ),
  fdr_bh_global_genome_sensitivity = NA_real_,
  fdr_bh_mtdna_global = NA_real_,
  fdr_bh_mitocarta_global = NA_real_
)]
for (branch in unique(gene_results$method_branch)) {
  index <- gene_results$method_branch == branch
  gene_results$fdr_bh_global_genome_sensitivity[index] <- stats::p.adjust(
    gene_results$p_value[index], method = "BH"
  )
  gene_results$fdr_bh_mtdna_global <- ifelse(
    index & gene_results$is_mtdna_protein_gene,
    adjust_subset(gene_results$p_value, index & gene_results$is_mtdna_protein_gene),
    gene_results$fdr_bh_mtdna_global
  )
  gene_results$fdr_bh_mitocarta_global <- ifelse(
    index & gene_results$is_mitocarta,
    adjust_subset(gene_results$p_value, index & gene_results$is_mitocarta),
    gene_results$fdr_bh_mitocarta_global
  )
}
gene_results[, `:=`(
  yu_comparable_deg = fdr_bh_within_contrast < alpha & abs(logFC) > log2(yu_fold_change),
  global_genome_significant = fdr_bh_global_genome_sensitivity < alpha,
  mtdna_global_significant = is_mtdna_protein_gene & fdr_bh_mtdna_global < alpha,
  mitocarta_global_significant = is_mitocarta & fdr_bh_mitocarta_global < alpha,
  interpretation_guardrail = "unequal_power_possible;absence_of_evidence_is_not_evidence_of_no_effect"
)]

pathway_results <- read_many(pathway_paths)
pathway_results[, `:=`(
  schema_version = "multiple_testing_pathway_results_v1",
  execution_stage = execution$execution_stage,
  output_status = output_status,
  rank_global_family_id = paste0(
    "pathway_rank_global_across_cell_types_and_contrasts::", method_branch
  ),
  ora_global_family_id = paste0(
    "pathway_ora_global_across_cell_types_and_contrasts::", method_branch
  ),
  rank_fdr_bh_global_branch = NA_real_,
  ora_fdr_bh_global_branch = NA_real_
)]
for (branch in unique(pathway_results$method_branch)) {
  eligible <- pathway_results$method_branch == branch &
    pathway_results$terminal_status == "validated_complete"
  pathway_results$rank_fdr_bh_global_branch <- ifelse(
    eligible,
    adjust_subset(pathway_results$rank_p_value, eligible),
    pathway_results$rank_fdr_bh_global_branch
  )
  pathway_results$ora_fdr_bh_global_branch <- ifelse(
    eligible,
    adjust_subset(pathway_results$ora_p_value, eligible),
    pathway_results$ora_fdr_bh_global_branch
  )
}

similarity_results <- data.table::fread(similarity_path)
similarity_results[, `:=`(
  schema_version = "multiple_testing_similarity_results_v1",
  global_similarity_family_id = paste0(
    "similarity_global_across_comparisons_sensitivity::", method_branch
  ),
  empirical_fdr_bh_global_method_branch = NA_real_
)]
for (branch in unique(similarity_results$method_branch)) {
  index <- similarity_results$method_branch == branch
  similarity_results$empirical_fdr_bh_global_method_branch[index] <- stats::p.adjust(
    similarity_results$empirical_p_value_directional[index], method = "BH"
  )
}

family_rows <- list()
add_family <- function(branch, family_id, entity_type, scope, tests, subfamilies, significant) {
  family_rows[[length(family_rows) + 1L]] <<- data.frame(
    schema_version = "multiple_testing_family_manifest_v1",
    method_branch = branch, family_id = family_id,
    entity_type = entity_type, correction_method = "BH",
    alpha = alpha, scope = scope, tests = tests,
    subfamilies = subfamilies, significant = significant,
    execution_stage = execution$execution_stage,
    output_status = output_status, stringsAsFactors = FALSE
  )
}
for (branch in unique(gene_results$method_branch)) {
  table <- gene_results[method_branch == branch]
  add_family(branch, "genomewide_gene_within_method_cell_type_contrast", "gene",
    "one family per method branch and contrast", nrow(table),
    data.table::uniqueN(table$contrast_id), sum(table$fdr_bh_within_contrast < alpha))
  add_family(branch, "genomewide_gene_global_across_cell_types_and_contrasts_sensitivity", "gene",
    "one global sensitivity family per method branch", nrow(table), 1L,
    sum(table$fdr_bh_global_genome_sensitivity < alpha))
  add_family(branch, "mtdna_gene_global_across_cell_types_and_contrasts", "mtDNA_gene",
    "all mtDNA gene tests across cell types and contrasts per method branch",
    sum(table$is_mtdna_protein_gene), 1L, sum(table$mtdna_global_significant))
  add_family(branch, "mitocarta_gene_global_across_cell_types_and_contrasts", "MitoCarta_gene",
    "all MitoCarta gene tests across cell types and contrasts per method branch",
    sum(table$is_mitocarta), 1L, sum(table$mitocarta_global_significant))
}
for (branch in unique(pathway_results$method_branch)) {
  table <- pathway_results[
    method_branch == branch & terminal_status == "validated_complete"
  ]
  add_family(branch, "pathway_rank_global_across_cell_types_and_contrasts", "pathway_rank",
    "all eligible ranked pathway tests per method branch", nrow(table), 1L,
    sum(table$rank_fdr_bh_global_branch < alpha))
  add_family(branch, "pathway_ora_global_across_cell_types_and_contrasts", "pathway_ora",
    "all eligible over-representation tests per method branch", nrow(table), 1L,
    sum(table$ora_fdr_bh_global_branch < alpha))
}
for (branch in unique(similarity_results$method_branch)) {
  table <- similarity_results[method_branch == branch]
  add_family(branch, "similarity_within_method_comparison", "similarity_gene",
    "one empirical family per method branch and comparison", nrow(table),
    data.table::uniqueN(table$comparison_id),
    sum(table$empirical_fdr_bh_within_branch_comparison < alpha))
  add_family(branch, "similarity_global_across_comparisons_sensitivity", "similarity_gene",
    "one global sensitivity family per method branch", nrow(table), 1L,
    sum(table$empirical_fdr_bh_global_method_branch < alpha))
}
family_manifest <- data.table::rbindlist(family_rows)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "multiple_testing_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
gene_key <- paste(gene_results$method_branch, gene_results$contrast_id, gene_results$gene, sep = "\r")
pathway_key <- paste(pathway_results$method_branch, pathway_results$contrast_id, pathway_results$hierarchy, sep = "\r")
similarity_key <- paste(similarity_results$method_branch, similarity_results$comparison_id, similarity_results$gene, sep = "\r")
eligible_pathway <- pathway_results$terminal_status == "validated_complete"
add_check("gene_result_keys_unique", !anyDuplicated(gene_key), anyDuplicated(gene_key), 0L)
add_check("pathway_result_keys_unique", !anyDuplicated(pathway_key), anyDuplicated(pathway_key), 0L)
add_check("similarity_result_keys_unique", !anyDuplicated(similarity_key), anyDuplicated(similarity_key), 0L)
add_check("gene_raw_p_values_have_explicit_families", all(is.finite(gene_results$p_value) & nzchar(gene_results$within_contrast_family_id) & nzchar(gene_results$global_genome_family_id)), nrow(gene_results), nrow(gene_results))
add_check("gene_fdr_values_in_range", all(gene_results$fdr_bh_within_contrast >= 0 & gene_results$fdr_bh_within_contrast <= 1 & gene_results$fdr_bh_global_genome_sensitivity >= 0 & gene_results$fdr_bh_global_genome_sensitivity <= 1), nrow(gene_results), nrow(gene_results))
add_check("mtdna_family_complete", all(is.finite(gene_results$fdr_bh_mtdna_global[gene_results$is_mtdna_protein_gene])) && all(is.na(gene_results$fdr_bh_mtdna_global[!gene_results$is_mtdna_protein_gene])), sum(gene_results$is_mtdna_protein_gene), ">0")
add_check("mitocarta_family_complete", all(is.finite(gene_results$fdr_bh_mitocarta_global[gene_results$is_mitocarta])) && all(is.na(gene_results$fdr_bh_mitocarta_global[!gene_results$is_mitocarta])), sum(gene_results$is_mitocarta), ">0")
add_check("pathway_global_fdr_complete", all(is.finite(pathway_results$rank_fdr_bh_global_branch[eligible_pathway])) && all(is.finite(pathway_results$ora_fdr_bh_global_branch[eligible_pathway])), sum(eligible_pathway), sum(eligible_pathway))
add_check("similarity_global_fdr_complete", all(is.finite(similarity_results$empirical_fdr_bh_global_method_branch)), nrow(similarity_results), nrow(similarity_results))
add_check("configured_families_represented", all(required_families %in% family_manifest$family_id), paste(sort(unique(family_manifest$family_id)), collapse = ";"), paste(sort(required_families), collapse = ";"))
add_check("execution_labels_match", all(gene_results$execution_stage == execution$execution_stage) && all(gene_results$output_status == output_status), paste(execution$execution_stage, output_status, sep = ";"), paste(execution$execution_stage, output_status, sep = ";"))
add_check("upstream_statuses_validated", all(pb_status$validation_status == "validated_complete") && all(mast_status$validation_status == "validated_complete") && all(pathway_status$validation_status == "validated_complete") && all(similarity_status$validation_status == "validated_complete") && all(annotation_status$validation_status == "validated_complete"), "validated_complete", "validated_complete")
checks <- data.table::rbindlist(checks)

output_dir <- file.path(output_root, "11_multiple_testing")
paths <- list(
  gene = file.path(output_dir, "gene_multiple_testing.tsv.gz"),
  pathway = file.path(output_dir, "pathway_multiple_testing.tsv.gz"),
  similarity = file.path(output_dir, "similarity_multiple_testing.tsv.gz"),
  families = file.path(output_dir, "multiple_testing_family_manifest.tsv"),
  checks = file.path(output_dir, "multiple_testing_checks.tsv"),
  artifacts = file.path(output_dir, "multiple_testing_artifacts.tsv"),
  status = file.path(output_dir, "multiple_testing_status.tsv")
)
atomic_write_tsv(gene_results, paths$gene, gzip = TRUE)
atomic_write_tsv(pathway_results, paths$pathway, gzip = TRUE)
atomic_write_tsv(similarity_results, paths$similarity, gzip = TRUE)
atomic_write_tsv(family_manifest, paths$families)
atomic_write_tsv(checks, paths$checks)

upstream_sha_after <- vapply(upstream_paths, sha256_file, character(1))
upstream_unchanged <- identical(unname(upstream_sha_before), unname(upstream_sha_after))
checks <- data.table::fread(paths$checks)
checks <- data.table::rbindlist(list(checks, data.frame(
  schema_version = "multiple_testing_checks_v1",
  check = "upstream_artifacts_unchanged", passed = upstream_unchanged,
  observed = if (upstream_unchanged) "unchanged" else "changed",
  expected = "unchanged", stringsAsFactors = FALSE
)))
atomic_write_tsv(checks, paths$checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

artifact_paths <- unlist(paths[c("gene", "pathway", "similarity", "families", "checks")])
artifacts <- data.frame(
  schema_version = "multiple_testing_artifacts_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(gene_results), nrow(pathway_results), nrow(similarity_results), nrow(family_manifest), nrow(checks)),
  validation_status = validation_status, stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "multiple_testing_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = "global:multiple_testing",
  source_rds = paste(sort(unique(gene_results$rds_id)), collapse = ";"),
  scientific_script = "scripts/11_apply_multiple_testing.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/11_apply_multiple_testing.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  upstream_input_bundle_sha256 = sha256_lines(paste(names(upstream_sha_before), upstream_sha_before, sep = "=")),
  correction_method = "BH", alpha = alpha,
  yu_absolute_fold_change_threshold = yu_fold_change,
  output_status = output_status,
  correction_family_rows = nrow(family_manifest),
  gene_result_rows = nrow(gene_results),
  pathway_result_rows = nrow(pathway_results),
  similarity_result_rows = nrow(similarity_results),
  mtdna_test_rows = sum(gene_results$is_mtdna_protein_gene),
  mitocarta_test_rows = sum(gene_results$is_mitocarta),
  significant_within_contrast_test_rows = sum(gene_results$fdr_bh_within_contrast < alpha),
  significant_global_genome_test_rows = sum(gene_results$fdr_bh_global_genome_sensitivity < alpha),
  significant_global_mtdna_test_rows = sum(gene_results$mtdna_global_significant),
  significant_global_mitocarta_test_rows = sum(gene_results$mitocarta_global_significant),
  significant_global_rank_pathway_tests = sum(pathway_results$rank_fdr_bh_global_branch < alpha, na.rm = TRUE),
  significant_global_ora_pathway_tests = sum(pathway_results$ora_fdr_bh_global_branch < alpha, na.rm = TRUE),
  significant_global_similarity_tests = sum(similarity_results$empirical_fdr_bh_global_method_branch < alpha),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Multiple-testing output: ", output_dir, "\n", sep = "")
cat("Gene test rows: ", nrow(gene_results), "\n", sep = "")
cat("Pathway test rows: ", nrow(pathway_results), "\n", sep = "")
cat("Similarity test rows: ", nrow(similarity_results), "\n", sep = "")
cat("Global mtDNA significant test rows: ", status$significant_global_mtdna_test_rows, "\n", sep = "")
cat("Phase 11 status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
