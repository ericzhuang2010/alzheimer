#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)

args <- phase08_parse_cli(
  commandArgs(trailingOnly = TRUE), allow = c("--require-status")
)
if (isTRUE(args$help)) {
  cat(
    "Usage: Rscript scripts/08_validate_broad_deg.R ",
    "[--config FILE] [--profile local_pilot|minerva_production] ",
    "[--require-status validated_complete]\n",
    sep = ""
  )
  quit(status = 0L)
}

context <- phase08_load_context(args$config, args$profile, include_model = FALSE)
input_dir <- file.path(context$output_root, "00_inputs")
broad_dir <- file.path(context$output_root, "02_broad_pseudobulk")
deg_dir <- file.path(context$output_root, "03_deg")
contrast_dir <- file.path(context$output_root, "05_by_contrast")

paths <- list(
  manifest = file.path(input_dir, "broad_deg_contrast_manifest.tsv"),
  samples = file.path(broad_dir, "broad_pseudobulk_samples.tsv.gz"),
  composition = file.path(broad_dir, "broad_fine_type_composition.tsv.gz"),
  conservation = file.path(broad_dir, "broad_pseudobulk_count_conservation.tsv.gz"),
  build_status = file.path(broad_dir, "broad_pseudobulk_stage_status.tsv"),
  model_status = file.path(deg_dir, "broad_deg_model_stage_status.tsv"),
  finalize_status = file.path(deg_dir, "broad_deg_finalize_stage_status.tsv"),
  results = file.path(context$output_root, "broad_deg_results.tsv.gz"),
  contrast_status = file.path(context$output_root, "broad_deg_contrast_status.tsv"),
  diagnostics = file.path(context$output_root, "broad_deg_model_diagnostics.tsv"),
  strict = file.path(context$output_root, "broad_deg_strict_signatures.tsv.gz"),
  relaxed = file.path(context$output_root, "broad_deg_relaxed_signatures.tsv.gz"),
  exploratory = file.path(context$output_root, "broad_deg_exploratory_signatures.tsv.gz"),
  handoff = file.path(context$output_root, "broad_core_mito_kda_query_handoff.tsv.gz"),
  funnel = file.path(context$output_root, "broad_deg_filter_funnel.tsv")
)
paths$sensitivity_results <- file.path(
  context$output_root, "04_sensitivity", "broad_deg_composition_adjusted.tsv.gz"
)
paths$sensitivity_summary <- file.path(
  context$output_root, "04_sensitivity", "broad_deg_sensitivity_summary.tsv"
)
paths$sensitivity_checks <- file.path(
  context$output_root, "04_sensitivity", "broad_deg_sensitivity_checks.tsv"
)
paths$sensitivity_status <- file.path(
  context$output_root, "04_sensitivity", "broad_deg_sensitivity_stage_status.tsv"
)
missing_paths <- names(paths)[!file.exists(unlist(paths))]
if (length(missing_paths)) {
  phase08_abort(paste("Required final outputs missing:", paste(missing_paths, collapse = ", ")))
}

manifest <- data.table::fread(paths$manifest, data.table = FALSE)
samples <- data.table::fread(
  paths$samples, colClasses = c(projid = "character"), data.table = FALSE
)
composition <- data.table::fread(
  paths$composition, colClasses = c(projid = "character"), data.table = FALSE
)
conservation <- data.table::fread(paths$conservation, data.table = FALSE)
results <- data.table::fread(paths$results, data.table = FALSE)
contrast_status <- data.table::fread(paths$contrast_status, data.table = FALSE)
diagnostics <- data.table::fread(paths$diagnostics, data.table = FALSE)
strict <- data.table::fread(paths$strict, data.table = FALSE)
relaxed <- data.table::fread(paths$relaxed, data.table = FALSE)
exploratory <- data.table::fread(paths$exploratory, data.table = FALSE)
handoff <- data.table::fread(paths$handoff, data.table = FALSE)
funnel <- data.table::fread(paths$funnel, data.table = FALSE)
build_status <- data.table::fread(paths$build_status, data.table = FALSE)
model_status <- data.table::fread(paths$model_status, data.table = FALSE)
finalize_status <- data.table::fread(paths$finalize_status, data.table = FALSE)
sensitivity_results <- data.table::fread(paths$sensitivity_results, data.table = FALSE)
sensitivity_summary <- data.table::fread(paths$sensitivity_summary, data.table = FALSE)
sensitivity_checks <- data.table::fread(paths$sensitivity_checks, data.table = FALSE)
sensitivity_status <- data.table::fread(paths$sensitivity_status, data.table = FALSE)

expected_contrasts <- as.integer(context$profile$expected_contrasts)
expected_broad <- as.integer(context$profile$expected_broad_types)
expected_groups <- nrow(phase08_group_rows(context$config))
status_index <- match(manifest$manifest_row, contrast_status$manifest_row)
completed <- contrast_status$terminal_status == "validated_complete"
result_keys <- paste(results$contrast_id, results$gene, sep = "\r")

recomputed_q <- unlist(lapply(split(results$p_value, results$contrast_id), function(p) {
  stats::p.adjust(p, method = "BH")
}), use.names = FALSE)
recomputed_order <- unlist(lapply(split(seq_len(nrow(results)), results$contrast_id), identity), use.names = FALSE)
q_reproduction <- if (nrow(results)) {
  isTRUE(all.equal(
    results$fdr_bh_within_contrast[recomputed_order], recomputed_q,
    tolerance = 1e-14, check.attributes = FALSE
  ))
} else TRUE
global_q_reproduction <- if (nrow(results)) {
  isTRUE(all.equal(
    results$fdr_bh_global_all_contrast_genes,
    stats::p.adjust(results$p_value, method = "BH"),
    tolerance = 1e-14, check.attributes = FALSE
  ))
} else TRUE

expected_flagged <- phase08_threshold_flags(
  results[, setdiff(names(results), c(
    "strict_deg", "relaxed_deg", "exploratory_deg", "direction",
    "strict_q_threshold", "strict_abs_log2fc_threshold",
    "relaxed_q_threshold", "relaxed_abs_log2fc_threshold",
    "exploratory_q_threshold"
  )), drop = FALSE],
  context$config
)
flag_reproduction <- identical(phase08_as_logical(results$strict_deg), expected_flagged$strict_deg) &&
  identical(phase08_as_logical(results$relaxed_deg), expected_flagged$relaxed_deg) &&
  identical(phase08_as_logical(results$exploratory_deg), expected_flagged$exploratory_deg) &&
  identical(as.character(results$direction), expected_flagged$direction)

file_count <- length(list.files(
  contrast_dir, pattern = "[.]broad_deg[.]tsv[.]gz$", full.names = TRUE
))
completed_ids <- contrast_status$contrast_id[completed]
direction_table <- table(
  factor(results$contrast_id, levels = completed_ids),
  factor(results$direction, levels = c("AD_up", "AD_down"))
)
both_directions <- !length(completed_ids) || all(direction_table[, "AD_up"] > 0 & direction_table[, "AD_down"] > 0)

signature_key <- function(x) paste(x$contrast_id, x$gene, sep = "\r")
strict_expected <- results[phase08_as_logical(results$strict_deg) & results$direction != "zero", , drop = FALSE]
relaxed_expected <- results[phase08_as_logical(results$relaxed_deg) & results$direction != "zero", , drop = FALSE]
exploratory_expected <- results[phase08_as_logical(results$exploratory_deg) & results$direction != "zero", , drop = FALSE]

checks <- list()
add_check <- function(check, passed, observed, expected, detail = "") {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "broad_deg_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), detail = detail,
    stringsAsFactors = FALSE
  )
}

add_check("manifest_has_expected_rows", nrow(manifest) == expected_contrasts, nrow(manifest), expected_contrasts)
add_check("manifest_keys_unique", !anyDuplicated(manifest$contrast_id), anyDuplicated(manifest$contrast_id), 0)
add_check("expected_broad_cells", length(unique(manifest$broad_cell_type)) == expected_broad,
          length(unique(manifest$broad_cell_type)), expected_broad)
add_check("six_groups_per_broad", all(table(manifest$broad_cell_type) == expected_groups),
          paste(table(manifest$broad_cell_type), collapse = ";"), expected_groups)
add_check("one_terminal_status_per_manifest", nrow(contrast_status) == nrow(manifest) &&
            !anyDuplicated(contrast_status$manifest_row) && !anyNA(status_index),
          nrow(contrast_status), nrow(manifest))
add_check("no_failed_contrasts", !any(contrast_status$terminal_status == "failed"),
          sum(contrast_status$terminal_status == "failed"), 0)
add_check("allowed_terminal_statuses", all(contrast_status$terminal_status %in% c("validated_complete", "not_estimable")),
          paste(sort(unique(contrast_status$terminal_status)), collapse = ";"),
          "validated_complete;not_estimable")
add_check("result_keys_unique", !anyDuplicated(result_keys), anyDuplicated(result_keys), 0)
add_check("completed_sets_have_results", all(completed_ids %in% unique(results$contrast_id)),
          length(intersect(completed_ids, unique(results$contrast_id))), length(completed_ids))
add_check("completed_sets_have_up_and_down_ranked_genes", both_directions,
          if (length(direction_table)) paste(apply(direction_table, 1, paste, collapse = "/"), collapse = ";") else "",
          "at_least_one_each_direction")
add_check("p_values_valid", !nrow(results) || all(is.finite(results$p_value) & results$p_value >= 0 & results$p_value <= 1),
          if (nrow(results)) sum(!is.finite(results$p_value) | results$p_value < 0 | results$p_value > 1) else 0, 0)
add_check("within_q_values_reproduce", q_reproduction, q_reproduction, TRUE)
add_check("global_q_values_reproduce", global_q_reproduction, global_q_reproduction, TRUE)
add_check("signature_flags_reproduce", flag_reproduction, flag_reproduction, TRUE)
add_check("strict_signature_members_reproduce", setequal(signature_key(strict), signature_key(strict_expected)),
          nrow(strict), nrow(strict_expected))
add_check("relaxed_signature_members_reproduce", setequal(signature_key(relaxed), signature_key(relaxed_expected)),
          nrow(relaxed), nrow(relaxed_expected))
add_check("exploratory_signature_members_reproduce", setequal(signature_key(exploratory), signature_key(exploratory_expected)),
          nrow(exploratory), nrow(exploratory_expected))
add_check("handoff_is_core_mito_only", !nrow(handoff) || all(handoff$mito_tier == "core_mito_protein"),
          if (nrow(handoff)) paste(sort(unique(handoff$mito_tier)), collapse = ";") else "empty", "core_mito_protein")
add_check("all_genes_retained_before_filtering", nrow(results) >= nrow(exploratory),
          paste(nrow(results), nrow(exploratory), sep = "/"), "full_at_least_filtered")
add_check("physical_result_set_count", file_count == expected_contrasts, file_count, expected_contrasts)
add_check("all_contrasts_in_filter_funnel", setequal(unique(funnel$contrast_id), manifest$contrast_id),
          length(unique(funnel$contrast_id)), expected_contrasts)
add_check("sample_keys_unique", !anyDuplicated(samples$broad_pseudobulk_id),
          anyDuplicated(samples$broad_pseudobulk_id), 0)
add_check("one_sample_per_donor_broad", !anyDuplicated(paste(samples$projid, samples$broad_cell_type, sep = "\r")),
          anyDuplicated(paste(samples$projid, samples$broad_cell_type, sep = "\r")), 0)
add_check("all_count_conservation_passed", all(phase08_as_logical(conservation$passed)),
          sum(!phase08_as_logical(conservation$passed)), 0)
composition_conservation <- data.table::as.data.table(composition)[, .(
  observed = sum(fine_type_nuclei), expected = unique(broad_nuclei)
), by = .(projid, broad_cell_type)]
add_check("fine_composition_conserves_broad_nuclei",
          all(composition_conservation$observed == composition_conservation$expected),
          sum(composition_conservation$observed != composition_conservation$expected), 0)
add_check("sensitivity_status_validated",
          nrow(sensitivity_status) == 1L &&
            identical(sensitivity_status$validation_status[[1L]], "validated_complete"),
          sensitivity_status$validation_status, "validated_complete")
add_check("sensitivity_checks_passed", all(phase08_as_logical(sensitivity_checks$passed)),
          sum(!phase08_as_logical(sensitivity_checks$passed)), 0)
add_check("sensitivity_summary_covers_manifest",
          nrow(sensitivity_summary) == nrow(manifest) &&
            setequal(sensitivity_summary$contrast_id, manifest$contrast_id),
          nrow(sensitivity_summary), nrow(manifest))
add_check("sensitivity_result_keys_unique",
          !anyDuplicated(paste(sensitivity_results$contrast_id, sensitivity_results$gene, sep = "\r")),
          anyDuplicated(paste(sensitivity_results$contrast_id, sensitivity_results$gene, sep = "\r")), 0)
add_check("all_stage_statuses_validated", all(c(
  build_status$validation_status, model_status$validation_status,
  sensitivity_status$validation_status, finalize_status$validation_status
) == "validated_complete"),
paste(c(build_status$validation_status, model_status$validation_status,
        sensitivity_status$validation_status, finalize_status$validation_status), collapse = ";"),
"validated_complete;validated_complete;validated_complete;validated_complete")

checks <- do.call(rbind, checks)
checks_path <- file.path(context$output_root, "broad_deg_checks.tsv")
phase08_atomic_write_tsv(checks, checks_path)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

artifact_candidates <- list.files(
  context$output_root, recursive = TRUE, full.names = TRUE, include.dirs = FALSE
)
artifact_candidates <- artifact_candidates[
  !grepl("/(logs|tmp)/", artifact_candidates) &
    !basename(artifact_candidates) %in% c("broad_deg_artifacts.tsv", "broad_deg_status.tsv")
]
artifacts <- phase08_artifact_rows(artifact_candidates, context)
artifacts_path <- file.path(context$output_root, "broad_deg_artifacts.tsv")
phase08_atomic_write_tsv(artifacts, artifacts_path)

status <- data.frame(
  schema_version = "broad_deg_status_v1",
  analysis_id = context$config$analysis$analysis_id,
  profile = context$profile_name,
  execution_stage = context$profile$execution_stage,
  execution_phase = as.integer(context$profile$execution_phase),
  run_id = context$profile$run_id,
  stable_task_id = paste("broad_deg", context$profile_name, sep = ":"),
  biological_replicate = "donor",
  count_source = context$config$analysis$count_source,
  method = context$config$analysis$method,
  broad_cell_types = length(unique(manifest$broad_cell_type)),
  structural_contrasts = nrow(manifest),
  completed_contrasts = sum(contrast_status$terminal_status == "validated_complete"),
  not_estimable_contrasts = sum(contrast_status$terminal_status == "not_estimable"),
  failed_contrasts = sum(contrast_status$terminal_status == "failed"),
  result_rows = nrow(results),
  strict_degs = sum(phase08_as_logical(results$strict_deg)),
  relaxed_degs = sum(phase08_as_logical(results$relaxed_deg)),
  exploratory_degs = sum(phase08_as_logical(results$exploratory_deg)),
  strict_core_mito_degs = sum(phase08_as_logical(results$strict_deg) & results$mito_tier == "core_mito_protein"),
  relaxed_core_mito_degs = sum(phase08_as_logical(results$relaxed_deg) & results$mito_tier == "core_mito_protein"),
  exploratory_core_mito_degs = sum(phase08_as_logical(results$exploratory_deg) & results$mito_tier == "core_mito_protein"),
  sensitivity_completed_contrasts = as.integer(sensitivity_status$completed_contrasts),
  sensitivity_result_rows = nrow(sensitivity_results),
  physical_result_sets = file_count,
  config_sha256 = phase08_sha256_file(context$config_path),
  mapping_sha256 = phase08_sha256_file(context$mapping_path),
  annotation_master_sha256 = phase08_sha256_file(context$annotation_master),
  scientific_scripts = paste(c(
    "scripts/08_build_broad_pseudobulk.R",
    "scripts/08_run_broad_pseudobulk_de.R",
    "scripts/08_run_broad_deg_composition_sensitivity.R",
    "scripts/08_finalize_broad_deg.R",
    "scripts/08_validate_broad_deg.R",
    "scripts/lib/phase08_broad_deg_common.R"
  ), collapse = ";"),
  R_version = as.character(getRversion()),
  edgeR_version = as.character(packageVersion("edgeR")),
  artifacts = nrow(artifacts),
  peak_ram_gib_validation = phase08_peak_ram_gib(),
  elapsed_seconds_validation = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = phase08_git_revision(context$project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
status_path <- file.path(context$output_root, "broad_deg_status.tsv")
phase08_atomic_write_tsv(status, status_path)

cat("Phase 08 broad validation status: ", validation_status, "\n", sep = "")
cat("Structural result sets: ", nrow(manifest), "\n", sep = "")
cat("Completed result sets: ", sum(completed), "\n", sep = "")
cat("Full tested-gene rows: ", nrow(results), "\n", sep = "")
cat("Strict/relaxed/exploratory DEGs: ",
    sum(results$strict_deg), "/", sum(results$relaxed_deg), "/",
    sum(results$exploratory_deg), "\n", sep = "")
if (!is.null(args$require_status) && !identical(validation_status, args$require_status)) {
  quit(status = 3L)
}
if (length(failed_checks)) quit(status = 2L)
