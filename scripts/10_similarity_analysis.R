#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = "similarity")
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/10_similarity_analysis.R --config FILE ",
        "[--execution-config FILE] [--task-mode similarity]\n",
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
  if (!identical(out$task_mode, "similarity")) {
    stop("--task-mode must be 'similarity'", call. = FALSE)
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
  path <- tempfile("phase10_inputs_", fileext = ".txt")
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
  if (!length(paths)) stop("No required status files were found", call. = FALSE)
  values <- lapply(paths, function(path) {
    value <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
    if (nrow(value) != 1L || !identical(value$schema_version[[1L]], expected_schema) ||
        !identical(value$validation_status[[1L]], "validated_complete")) {
      stop("Required status is not validated_complete: ", path, call. = FALSE)
    }
    value$status_path <- path
    value
  })
  do.call(rbind, values)
}

similarity_score <- function(first, second) {
  if (length(first) != length(second) || !length(first)) return(NA_real_)
  if (any(!first %in% -1:1) || any(!second %in% -1:1)) {
    stop("Similarity states must be -1, 0, or +1", call. = FALSE)
  }
  concordant <- sum((first == 1L & second == 1L) |
    (first == -1L & second == -1L))
  one_sided <- sum((first == 0L & second != 0L) |
    (first != 0L & second == 0L))
  opposite <- sum((first == 1L & second == -1L) |
    (first == -1L & second == 1L))
  (concordant - 0.5 * one_sided - opposite) / length(first)
}

score_components <- function(first, second) {
  data.frame(
    paired_tests = length(first),
    concordant_same_direction = sum((first == 1L & second == 1L) |
      (first == -1L & second == -1L)),
    one_sided_change = sum((first == 0L & second != 0L) |
      (first != 0L & second == 0L)),
    opposite_direction = sum((first == 1L & second == -1L) |
      (first == -1L & second == 1L)),
    both_unchanged = sum(first == 0L & second == 0L),
    similarity_score = similarity_score(first, second),
    stringsAsFactors = FALSE
  )
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
  backend = "direct", run_id = if (pilot) "manual_local_similarity" else "manual_similarity"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

settings <- if (pilot) analysis$pilot else analysis$production
permutations <- as.integer(settings$similarity_permutations)
output_status <- as.character(settings$output_status)
if (!is.finite(permutations) || permutations < 1L) {
  stop("Configured similarity_permutations must be a positive integer", call. = FALSE)
}
alpha <- as.numeric(analysis$multiple_testing$alpha %||% 0.05)
effect_threshold <- log2(1.3)
base_seed <- as.integer(analysis$analysis$seed)

pseudobulk_dir <- file.path(output_root, "07_pseudobulk_de")
mast_dir <- file.path(output_root, "08_mast")
annotation_path <- file.path(output_root, "03_annotations", "tested_gene_universe.tsv")
annotation_status_path <- file.path(output_root, "03_annotations", "annotation_status.tsv")

pseudobulk_status_paths <- list.files(
  pseudobulk_dir, pattern = "[.]pseudobulk_de_status[.]tsv$", full.names = TRUE
)
mast_status_paths <- list.files(
  mast_dir, pattern = "[.]mast_de_status[.]tsv$", full.names = TRUE
)
pseudobulk_status <- read_validated_statuses(
  pseudobulk_status_paths, "pseudobulk_de_status_v1"
)
mast_status <- read_validated_statuses(mast_status_paths, "mast_de_status_v1")
annotation_status <- read_validated_statuses(
  annotation_status_path, "mito_annotations_status_v1"
)

pseudobulk_paths <- list.files(
  pseudobulk_dir, pattern = "[.]pseudobulk_de[.]tsv[.]gz$", full.names = TRUE
)
mast_paths <- list.files(mast_dir, pattern = "[.]mast_de[.]tsv[.]gz$", full.names = TRUE)
if (length(pseudobulk_paths) != nrow(pseudobulk_status) ||
    length(mast_paths) != nrow(mast_status)) {
  stop("Validated Phase 07/08 status and result-file counts do not match", call. = FALSE)
}
if (!file.exists(annotation_path)) {
  stop("Required Phase 03 tested-gene universe is missing: ", annotation_path, call. = FALSE)
}

read_results <- function(paths) {
  do.call(rbind, lapply(paths, function(path) {
    data.table::fread(path, data.table = FALSE, showProgress = FALSE)
  }))
}
pseudobulk <- read_results(pseudobulk_paths)
mast <- read_results(mast_paths)
if (!nrow(pseudobulk) || !nrow(mast)) {
  stop("Phase 07 or Phase 08 contains no gene-level results", call. = FALSE)
}

make_states <- function(table, branch) {
  required <- c(
    "rds_id", "cell_type_high_resolution", "contrast_family",
    "contrast_name", "gene", "logFC", "fdr_bh_within_contrast"
  )
  missing <- setdiff(required, names(table))
  if (length(missing)) {
    stop(branch, " results lack columns: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  keep <- table$contrast_family == "AD_vs_NCI" &
    grepl("^AD_vs_NCI__(Female|Male)__(e2|e33|e4)$", table$contrast_name)
  if (identical(branch, "pseudobulk") && "paper_matched" %in% names(table)) {
    keep <- keep & as_logical(table$paper_matched)
  }
  table <- table[keep, , drop = FALSE]
  if (!nrow(table)) stop("No paper-matched AD-versus-NCI rows for ", branch, call. = FALSE)
  significant <- if (identical(branch, "mast")) {
    if (!"paper_deg" %in% names(table)) stop("MAST results lack paper_deg", call. = FALSE)
    as_logical(table$paper_deg)
  } else {
    as.numeric(table$fdr_bh_within_contrast) < alpha &
      abs(as.numeric(table$logFC)) > effect_threshold
  }
  state <- integer(nrow(table))
  state[significant & as.numeric(table$logFC) > 0] <- 1L
  state[significant & as.numeric(table$logFC) < 0] <- -1L
  out <- data.frame(
    method_branch = branch,
    rds_id = as.character(table$rds_id),
    cell_type_high_resolution = as.character(table$cell_type_high_resolution),
    sex = sub("^AD_vs_NCI__([^_]+)__.*$", "\\1", table$contrast_name),
    apoe_group = sub("^AD_vs_NCI__[^_]+__(.*)$", "\\1", table$contrast_name),
    gene = as.character(table$gene),
    ternary_state = state,
    stringsAsFactors = FALSE
  )
  out <- out[!is.na(out$gene) & nzchar(out$gene), , drop = FALSE]
  key <- paste(
    out$rds_id, out$cell_type_high_resolution, out$sex,
    out$apoe_group, out$gene, sep = "\r"
  )
  if (anyDuplicated(key)) stop("Duplicate gene/stratum rows in ", branch, call. = FALSE)
  out
}

states <- rbind(make_states(pseudobulk, "pseudobulk"), make_states(mast, "mast"))

comparisons <- data.frame(
  comparison_id = c(
    "female_vs_male_all_apoe", "e2_vs_e33_all_sexes", "e4_vs_e33_all_sexes",
    "female_vs_male_e2", "female_vs_male_e33", "female_vs_male_e4",
    "e2_vs_e33_Female", "e2_vs_e33_Male",
    "e4_vs_e33_Female", "e4_vs_e33_Male"
  ),
  comparison_family = c(rep("primary_paper", 3L), rep("stratified_extension", 7L)),
  axis = c(rep("sex", 1L), rep("apoe", 2L), rep("sex", 3L), rep("apoe", 4L)),
  first_level = c(
    "Female", "e2", "e4", "Female", "Female", "Female",
    "e2", "e2", "e4", "e4"
  ),
  second_level = c(
    "Male", "e33", "e33", "Male", "Male", "Male",
    "e33", "e33", "e33", "e33"
  ),
  fixed_level = c(NA, NA, NA, "e2", "e33", "e4", "Female", "Male", "Female", "Male"),
  stringsAsFactors = FALSE
)

build_pairs <- function(branch_states, definition) {
  axis <- definition$axis[[1L]]
  fixed <- definition$fixed_level[[1L]]
  table <- branch_states
  if (!is.na(fixed)) {
    table <- if (axis == "sex") {
      table[table$apoe_group == fixed, , drop = FALSE]
    } else {
      table[table$sex == fixed, , drop = FALSE]
    }
  }
  if (axis == "sex") {
    first <- table[table$sex == definition$first_level[[1L]], , drop = FALSE]
    second <- table[table$sex == definition$second_level[[1L]], , drop = FALSE]
    first$dimension_id <- paste(first$rds_id, first$cell_type_high_resolution, first$apoe_group, sep = "::")
    second$dimension_id <- paste(second$rds_id, second$cell_type_high_resolution, second$apoe_group, sep = "::")
  } else {
    first <- table[table$apoe_group == definition$first_level[[1L]], , drop = FALSE]
    second <- table[table$apoe_group == definition$second_level[[1L]], , drop = FALSE]
    first$dimension_id <- paste(first$rds_id, first$cell_type_high_resolution, first$sex, sep = "::")
    second$dimension_id <- paste(second$rds_id, second$cell_type_high_resolution, second$sex, sep = "::")
  }
  first <- first[, c("gene", "dimension_id", "ternary_state"), drop = FALSE]
  second <- second[, c("gene", "dimension_id", "ternary_state"), drop = FALSE]
  names(first)[[3L]] <- "first_state"
  names(second)[[3L]] <- "second_state"
  merge(first, second, by = c("gene", "dimension_id"), all = FALSE, sort = TRUE)
}

annotations <- data.table::fread(annotation_path, data.table = FALSE, showProgress = FALSE)
required_annotation <- c("feature", "is_mtdna_protein_gene", "is_mitocarta")
if (!all(required_annotation %in% names(annotations))) {
  stop("Tested-gene universe lacks mitochondrial flags", call. = FALSE)
}
annotation_map <- aggregate(
  cbind(
    is_mtdna_protein_gene = as.integer(as_logical(annotations$is_mtdna_protein_gene)),
    is_mitocarta = as.integer(as_logical(annotations$is_mitocarta))
  ),
  by = list(gene = annotations$feature), FUN = max, na.rm = TRUE
)
annotation_map$is_mtdna_protein_gene <- annotation_map$is_mtdna_protein_gene > 0L
annotation_map$is_mitocarta <- annotation_map$is_mitocarta > 0L

toy_specs <- list(
  identical = list(first = c(1L, -1L), second = c(1L, -1L), expected = 1),
  one_sided = list(first = c(1L), second = c(0L), expected = -0.5),
  opposite = list(first = c(1L, -1L), second = c(-1L, 1L), expected = -1),
  both_unchanged = list(first = c(0L), second = c(0L), expected = 0)
)
toy_checks <- do.call(rbind, lapply(names(toy_specs), function(name) {
  spec <- toy_specs[[name]]
  observed <- similarity_score(spec$first, spec$second)
  data.frame(
    schema_version = "similarity_toy_checks_v1", example = name,
    first_states = paste(spec$first, collapse = ","),
    second_states = paste(spec$second, collapse = ","),
    expected_score = spec$expected, observed_score = observed,
    passed = isTRUE(all.equal(observed, spec$expected, tolerance = 1e-12)),
    stringsAsFactors = FALSE
  )
}))

result_list <- list()
comparison_status_list <- list()
diagnostic_list <- list()
branches <- c("pseudobulk", "mast")

for (branch_index in seq_along(branches)) {
  branch <- branches[[branch_index]]
  branch_states <- states[states$method_branch == branch, , drop = FALSE]
  for (comparison_index in seq_len(nrow(comparisons))) {
    definition <- comparisons[comparison_index, , drop = FALSE]
    pairs <- build_pairs(branch_states, definition)
    status_value <- if (nrow(pairs)) {
      "validated_complete"
    } else {
      "not_estimable_missing_paired_strata"
    }
    comparison_seed <- base_seed + branch_index * 10000L + comparison_index * 100L
    result_rows <- 0L
    pattern_count <- 0L
    null_min <- NA_real_
    null_median <- NA_real_
    null_max <- NA_real_
    paired_dimension_count <- length(unique(pairs$dimension_id))

    if (nrow(pairs)) {
      gene_rows <- split(seq_len(nrow(pairs)), pairs$gene)
      genes <- sort(names(gene_rows))
      gene_info <- lapply(genes, function(gene) {
        table <- pairs[gene_rows[[gene]], , drop = FALSE]
        table <- table[order(table$dimension_id), , drop = FALSE]
        first <- as.integer(table$first_state)
        second <- as.integer(table$second_state)
        list(
          gene = gene, first = first, second = second,
          pattern = paste(
            paste(table$dimension_id, first, second, sep = ":"),
            collapse = "|"
          ),
          components = score_components(first, second)
        )
      })
      patterns <- vapply(gene_info, `[[`, character(1), "pattern")
      pattern_groups <- split(seq_along(gene_info), patterns)
      pattern_names <- sort(names(pattern_groups))
      pattern_count <- length(pattern_names)
      p_values <- numeric(length(gene_info))
      null_summaries <- matrix(NA_real_, nrow = pattern_count, ncol = 3L)

      for (pattern_index in seq_along(pattern_names)) {
        members <- pattern_groups[[pattern_names[[pattern_index]]]]
        representative <- gene_info[[members[[1L]]]]
        set.seed(comparison_seed + pattern_index)
        null_scores <- replicate(
          permutations,
          similarity_score(representative$first, sample(representative$second))
        )
        observed <- representative$components$similarity_score[[1L]]
        empirical_p <- if (observed >= 0) {
          (1 + sum(null_scores >= observed)) / (permutations + 1)
        } else {
          (1 + sum(null_scores <= observed)) / (permutations + 1)
        }
        p_values[members] <- empirical_p
        null_summaries[pattern_index, ] <- c(
          min(null_scores), stats::median(null_scores), max(null_scores)
        )
      }

      fdr <- stats::p.adjust(p_values, method = "BH")
      branch_results <- do.call(rbind, lapply(seq_along(gene_info), function(i) {
        info <- gene_info[[i]]
        data.frame(
          schema_version = "similarity_results_v1",
          execution_stage = execution$execution_stage,
          output_status = output_status,
          method_branch = branch,
          comparison_family = definition$comparison_family[[1L]],
          comparison_id = definition$comparison_id[[1L]],
          comparison_axis = definition$axis[[1L]],
          first_level = definition$first_level[[1L]],
          second_level = definition$second_level[[1L]],
          fixed_level = definition$fixed_level[[1L]],
          gene = info$gene,
          info$components,
          similarity_direction = if (
            info$components$similarity_score[[1L]] > 0
          ) "concordant" else if (
            info$components$similarity_score[[1L]] < 0
          ) "divergent" else "neutral",
          empirical_p_value_directional = p_values[[i]],
          empirical_fdr_bh_within_branch_comparison = fdr[[i]],
          permutations = permutations,
          seed = comparison_seed,
          formula_version = "zhang_yu_similarity_v1",
          stringsAsFactors = FALSE
        )
      }))
      branch_results <- merge(branch_results, annotation_map, by = "gene", all.x = TRUE, sort = FALSE)
      branch_results$is_mtdna_protein_gene[is.na(branch_results$is_mtdna_protein_gene)] <- FALSE
      branch_results$is_mitocarta[is.na(branch_results$is_mitocarta)] <- FALSE
      branch_results$mitochondrial_subset <- ifelse(
        branch_results$is_mtdna_protein_gene, "mtDNA_protein_coding",
        ifelse(branch_results$is_mitocarta, "MitoCarta", "non_mitochondrial")
      )
      result_list[[length(result_list) + 1L]] <- branch_results
      result_rows <- nrow(branch_results)
      null_min <- min(null_summaries[, 1L])
      null_median <- stats::median(null_summaries[, 2L])
      null_max <- max(null_summaries[, 3L])
    }

    comparison_status_list[[length(comparison_status_list) + 1L]] <- data.frame(
      schema_version = "similarity_comparison_status_v1",
      method_branch = branch,
      comparison_family = definition$comparison_family[[1L]],
      comparison_id = definition$comparison_id[[1L]],
      first_level = definition$first_level[[1L]],
      second_level = definition$second_level[[1L]],
      fixed_level = definition$fixed_level[[1L]],
      paired_dimensions = paired_dimension_count,
      paired_genes = if (nrow(pairs)) length(unique(pairs$gene)) else 0L,
      result_rows = result_rows,
      terminal_status = status_value,
      stringsAsFactors = FALSE
    )
    diagnostic_list[[length(diagnostic_list) + 1L]] <- data.frame(
      schema_version = "similarity_permutation_diagnostics_v1",
      method_branch = branch,
      comparison_id = definition$comparison_id[[1L]],
      terminal_status = status_value,
      genes = result_rows,
      unique_state_patterns = pattern_count,
      permutations_configured = permutations,
      permutations_completed_per_pattern = if (nrow(pairs)) permutations else 0L,
      seed = comparison_seed,
      null_score_min = null_min,
      null_score_median_of_pattern_medians = null_median,
      null_score_max = null_max,
      empirical_p_definition = "one_sided_in_observed_direction_plus_one_correction",
      fdr_method = "BH_within_method_branch_and_comparison",
      stringsAsFactors = FALSE
    )
  }
}

similarity_results <- if (length(result_list)) {
  do.call(rbind, result_list)
} else {
  stop("No similarity comparison was estimable", call. = FALSE)
}
comparison_status <- do.call(rbind, comparison_status_list)
permutation_diagnostics <- do.call(rbind, diagnostic_list)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "similarity_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
result_key <- paste(
  similarity_results$method_branch, similarity_results$comparison_id,
  similarity_results$gene, sep = "\r"
)
add_check("toy_examples_match_hand_calculations", all(toy_checks$passed), sum(toy_checks$passed), nrow(toy_checks))
add_check("method_branches_separate_and_present", setequal(unique(similarity_results$method_branch), branches), paste(sort(unique(similarity_results$method_branch)), collapse = ";"), "mast;pseudobulk")
add_check("result_keys_unique", !anyDuplicated(result_key), anyDuplicated(result_key), 0L)
add_check("scores_within_minus_one_plus_one", all(is.finite(similarity_results$similarity_score) & abs(similarity_results$similarity_score) <= 1), range(similarity_results$similarity_score), "[-1,1]")
add_check("empirical_p_values_in_range", all(similarity_results$empirical_p_value_directional > 0 & similarity_results$empirical_p_value_directional <= 1), range(similarity_results$empirical_p_value_directional), "(0,1]")
add_check("empirical_fdr_in_range", all(similarity_results$empirical_fdr_bh_within_branch_comparison >= 0 & similarity_results$empirical_fdr_bh_within_branch_comparison <= 1), range(similarity_results$empirical_fdr_bh_within_branch_comparison), "[0,1]")
add_check("mitochondrial_annotations_recorded", all(!is.na(similarity_results$is_mtdna_protein_gene) & !is.na(similarity_results$is_mitocarta)), sum(similarity_results$is_mitocarta), "no_missing_flags")
add_check("configured_permutations_recorded", all(similarity_results$permutations == permutations), unique(similarity_results$permutations), permutations)
add_check("execution_stage_recorded", all(similarity_results$execution_stage == execution$execution_stage), unique(similarity_results$execution_stage), execution$execution_stage)
add_check("output_status_recorded", all(similarity_results$output_status == output_status), unique(similarity_results$output_status), output_status)
add_check("all_comparisons_have_terminal_status", nrow(comparison_status) == length(branches) * nrow(comparisons) && all(nzchar(comparison_status$terminal_status)), nrow(comparison_status), length(branches) * nrow(comparisons))
add_check("validated_upstream_statuses", all(pseudobulk_status$validation_status == "validated_complete") && all(mast_status$validation_status == "validated_complete") && all(annotation_status$validation_status == "validated_complete"), "validated_complete", "validated_complete")
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "10_downstream")
result_filename <- if (pilot) "similarity_smoke.tsv" else "similarity_results.tsv"
paths <- list(
  results = file.path(output_dir, result_filename),
  comparisons = file.path(output_dir, "similarity_comparison_status.tsv"),
  toys = file.path(output_dir, "similarity_toy_checks.tsv"),
  diagnostics = file.path(output_dir, "similarity_permutation_diagnostics.tsv"),
  checks = file.path(output_dir, "similarity_checks.tsv"),
  artifacts = file.path(output_dir, "similarity_artifacts.tsv"),
  status = file.path(output_dir, "similarity_status.tsv")
)
atomic_write_tsv(similarity_results, paths$results)
atomic_write_tsv(comparison_status, paths$comparisons)
atomic_write_tsv(toy_checks, paths$toys)
atomic_write_tsv(permutation_diagnostics, paths$diagnostics)
atomic_write_tsv(checks, paths$checks)

artifact_paths <- unlist(paths[c("results", "comparisons", "toys", "diagnostics", "checks")])
artifact_records <- c(
  nrow(similarity_results), nrow(comparison_status), nrow(toy_checks),
  nrow(permutation_diagnostics), nrow(checks)
)
artifacts <- data.frame(
  schema_version = "similarity_artifacts_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = artifact_records,
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

input_checksums <- vapply(
  c(pseudobulk_paths, mast_paths, annotation_path), sha256_file, character(1)
)
status <- data.frame(
  schema_version = "similarity_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend,
  run_id = execution$run_id,
  stable_task_id = "global:similarity",
  source_rds = paste(sort(unique(states$rds_id)), collapse = ";"),
  scientific_script = "scripts/10_similarity_analysis.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/10_similarity_analysis.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  upstream_input_bundle_sha256 = sha256_lines(paste(names(input_checksums), input_checksums, sep = "=")),
  formula_version = "zhang_yu_similarity_v1",
  significance_rule = paste0("BH_FDR<", alpha, "_and_abs_FC>1.3"),
  permutations = permutations,
  seed = base_seed,
  output_status = output_status,
  method_branches = length(unique(similarity_results$method_branch)),
  comparison_templates = nrow(comparisons),
  estimable_branch_comparisons = sum(comparison_status$terminal_status == "validated_complete"),
  not_estimable_branch_comparisons = sum(comparison_status$terminal_status != "validated_complete"),
  result_rows = nrow(similarity_results),
  unique_genes = length(unique(similarity_results$gene)),
  mtdna_result_rows = sum(similarity_results$is_mtdna_protein_gene),
  mitocarta_result_rows = sum(similarity_results$is_mitocarta),
  significant_empirical_fdr_005 = sum(similarity_results$empirical_fdr_bh_within_branch_comparison < 0.05),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Similarity results: ", paths$results, "\n", sep = "")
cat("Similarity rows: ", nrow(similarity_results), "\n", sep = "")
cat("Estimable branch/comparisons: ", status$estimable_branch_comparisons, "\n", sep = "")
cat("MitoCarta result rows: ", status$mitocarta_result_rows, "\n", sep = "")
cat("Empirical FDR < 0.05: ", status$significant_empirical_fdr_005, "\n", sep = "")
cat("Similarity status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
