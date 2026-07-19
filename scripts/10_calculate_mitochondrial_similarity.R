#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/10_calculate_mitochondrial_similarity.R ",
        "--config FILE --execution-config FILE --task-mode similarity\n",
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
  required <- c("config", "execution_config", "task_mode")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) {
    stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  if (!identical(out$task_mode, "similarity")) {
    stop("--task-mode must be similarity", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  path <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  prefix <- paste0(root, .Platform$file.sep)
  if (startsWith(path, prefix)) substring(path, nchar(prefix) + 1L) else path
}

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "HEAD"),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  result[[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  lines <- readLines(path, warn = FALSE)
  value <- sub("^VmHWM:[[:space:]]+([0-9]+)[[:space:]]+kB.*$", "\\1",
               grep("^VmHWM:", lines, value = TRUE))
  if (!length(value)) return(NA_real_)
  as.numeric(value[[1L]]) / 1024^2
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(
    dirname(path),
    paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  compress <- if (grepl("\\.gz$", path)) "gzip" else "none"
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA",
    logical01 = FALSE, compress = compress
  )
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

score_vectors <- function(first, second) {
  keep <- !is.na(first) & !is.na(second)
  first <- as.integer(first[keep])
  second <- as.integer(second[keep])
  n <- length(first)
  if (!n) return(NA_real_)
  contribution <- ifelse(
    first == second & first != 0L, 1,
    ifelse(
      first * second == -1L, -1,
      ifelse(first == 0L & second == 0L, 0, -0.5)
    )
  )
  sum(contribution) / n
}

seed_from_key <- function(key, base_seed) {
  hex <- digest::digest(key, algo = "xxhash32", serialize = FALSE)
  value <- strtoi(substr(hex, 1L, 7L), base = 16L)
  as.integer((as.double(base_seed) + value) %% (.Machine$integer.max - 1) + 1)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
for (package in c("data.table", "yaml", "digest")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}
library(data.table)

start_time <- Sys.time()
project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, project_root)
execution_path <- absolute_path(args$execution_config, project_root)
must(file.exists(config_path), paste("Project config does not exist:", config_path))
must(file.exists(execution_path), paste("Execution config does not exist:", execution_path))

config <- yaml::read_yaml(config_path)
execution_config <- yaml::read_yaml(execution_path)
phase10_path <- absolute_path(
  config$project$phase10_similarity_config %||% "",
  project_root
)
must(file.exists(phase10_path), paste("Phase 10 config does not exist:", phase10_path))
phase10 <- yaml::read_yaml(phase10_path)
must(
  identical(phase10$schema_version, "phase10_similarity_config_v1"),
  "Unexpected Phase 10 config schema"
)

execution <- execution_config$execution
execution_stage <- as.character(execution$execution_stage)
must(
  execution_stage %in% c("local_pilot", "minerva_production", "lsf_fallback"),
  "Unsupported execution stage"
)
output_root <- absolute_path(config$outputs$root, project_root)
phase09_root <- file.path(output_root, "09_annotate_genes")
final_root <- file.path(output_root, "10_similarity")
staging_root <- file.path(
  output_root, paste0(".10_similarity.staging.", Sys.getpid())
)

permutations <- if (identical(execution_stage, "local_pilot")) {
  as.integer(
    config$pilot_limits$similarity_permutations %||%
      phase10$permutation$local_pilot_repetitions
  )
} else {
  as.integer(phase10$permutation$minerva_production_repetitions)
}
expected_validation_status <- if (identical(execution_stage, "local_pilot")) {
  "nonfinal_smoke_test"
} else {
  "validated_complete"
}
must(permutations >= 1L, "Permutation count must be positive")
if (identical(execution_stage, "local_pilot")) {
  must(
    permutations == as.integer(phase10$permutation$local_pilot_repetitions),
    "Local permutation override differs from the frozen Phase 10 config"
  )
}

required_inputs <- c(
  "annotation_status.tsv",
  "annotation_artifacts.tsv",
  "annotation_checks.tsv",
  "gene_annotation_master.tsv.gz",
  "deg_all_annotated.tsv.gz",
  "mitochondrial_reference_inventory.tsv"
)
input_paths <- setNames(file.path(phase09_root, required_inputs), required_inputs)
must(all(file.exists(input_paths)), paste(
  "Missing required Phase 09 inputs:",
  paste(names(input_paths)[!file.exists(input_paths)], collapse = ", ")
))

phase09_status <- fread(input_paths[["annotation_status.tsv"]])
phase09_checks <- fread(input_paths[["annotation_checks.tsv"]])
phase09_artifacts <- fread(input_paths[["annotation_artifacts.tsv"]])
must(nrow(phase09_status) == 1L, "Phase 09 status must contain exactly one row")
must(
  identical(
    phase09_status$schema_version[[1L]],
    phase10$expected_phase09$status_schema
  ),
  "Unexpected Phase 09 status schema"
)
must(
  identical(
    phase09_status$validation_status[[1L]],
    phase10$expected_phase09$required_validation_status
  ),
  "Phase 09 is not validated_complete"
)
must(all(phase09_checks$passed %in% TRUE), "A blocking Phase 09 check failed")
must(
  all(phase09_artifacts$validation_status == "validated_complete"),
  "Phase 09 artifact manifest contains an invalid artifact"
)

artifact_hash_ok <- logical(nrow(phase09_artifacts))
artifact_bytes_ok <- logical(nrow(phase09_artifacts))
for (i in seq_len(nrow(phase09_artifacts))) {
  artifact_path <- absolute_path(phase09_artifacts$path[[i]], project_root)
  artifact_hash_ok[[i]] <- file.exists(artifact_path) &&
    identical(sha256_file(artifact_path), phase09_artifacts$sha256[[i]])
  artifact_bytes_ok[[i]] <- file.exists(artifact_path) &&
    as.numeric(file.info(artifact_path)$size) ==
      as.numeric(phase09_artifacts$bytes[[i]])
}
must(all(artifact_hash_ok), "A Phase 09 artifact checksum does not match")
must(all(artifact_bytes_ok), "A Phase 09 artifact byte count does not match")

current_hashes <- list(
  scientific_script_sha256 = sha256_file(file.path(
    project_root, "scripts/10_calculate_mitochondrial_similarity.R"
  )),
  scientific_config_sha256 = sha256_file(phase10_path),
  pipeline_config_sha256 = sha256_file(config_path),
  execution_config_sha256 = sha256_file(execution_path),
  rds_manifest_sha256 = sha256_file(absolute_path(config$project$manifest, project_root)),
  phase09_status_sha256 = sha256_file(input_paths[["annotation_status.tsv"]]),
  phase09_artifacts_sha256 = sha256_file(input_paths[["annotation_artifacts.tsv"]]),
  phase09_checks_sha256 = sha256_file(input_paths[["annotation_checks.tsv"]]),
  phase09_master_sha256 = sha256_file(input_paths[["gene_annotation_master.tsv.gz"]]),
  phase09_annotated_sha256 = sha256_file(input_paths[["deg_all_annotated.tsv.gz"]]),
  phase09_reference_inventory_sha256 = sha256_file(
    input_paths[["mitochondrial_reference_inventory.tsv"]]
  )
)
must(all(!is.na(unlist(current_hashes))), "Could not hash all required inputs")

if (dir.exists(final_root)) {
  status_path <- file.path(final_root, "similarity_status.tsv")
  artifacts_path <- file.path(final_root, "similarity_artifacts.tsv")
  resumable <- file.exists(status_path) && file.exists(artifacts_path)
  if (resumable) {
    existing_status <- fread(status_path)
    existing_artifacts <- fread(artifacts_path)
    resumable <- nrow(existing_status) == 1L &&
      existing_status$schema_version[[1L]] == phase10$schemas$status &&
      existing_status$validation_status[[1L]] == expected_validation_status &&
      existing_status$permutations[[1L]] == permutations &&
      existing_status$scientific_script_sha256[[1L]] ==
        current_hashes$scientific_script_sha256 &&
      existing_status$scientific_config_sha256[[1L]] ==
        current_hashes$scientific_config_sha256 &&
      existing_status$phase09_annotated_sha256[[1L]] ==
        current_hashes$phase09_annotated_sha256
    if (resumable) {
      for (i in seq_len(nrow(existing_artifacts))) {
        path <- absolute_path(existing_artifacts$path[[i]], project_root)
        resumable <- resumable && file.exists(path) &&
          identical(sha256_file(path), existing_artifacts$sha256[[i]]) &&
          as.numeric(file.info(path)$size) ==
            as.numeric(existing_artifacts$bytes[[i]]) &&
          existing_artifacts$validation_status[[i]] == "validated_complete"
      }
    }
  }
  if (isTRUE(resumable)) {
    cat("Phase 10 output is already complete and hash-valid: ", final_root, "\n", sep = "")
    quit(status = 0L)
  }
  stop(
    "Phase 10 output directory already exists but is not resumable: ",
    final_root,
    call. = FALSE
  )
}

dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
must(dir.exists(staging_root), "Could not create Phase 10 staging directory")
cleanup_staging <- TRUE
on.exit({
  if (cleanup_staging && dir.exists(staging_root)) {
    unlink(staging_root, recursive = TRUE, force = TRUE)
  }
}, add = TRUE)

accepted_tiers <- unlist(phase10$accepted_mito_tiers, use.names = FALSE)
core_tiers <- unlist(
  phase10$analysis_universes$core_mito$tiers,
  use.names = FALSE
)
all_tiers <- unlist(
  phase10$analysis_universes$all_mito_related$tiers,
  use.names = FALSE
)
must(
  setequal(accepted_tiers, c(
    "core_mito_protein", "mtdna_noncoding", "mito_extended"
  )),
  "Phase 10 accepted mitochondrial tiers are not frozen as expected"
)

master_columns <- c(
  "schema_version", "rds_id", "feature_id_original", "reference_only_id",
  "reference_only", "reference_source", "symbol_original",
  "ensembl_id_stable", "symbol_hgnc_current", "hgnc_id", "mapping_status",
  "mito_tier", "genome_origin", "sub_mito_localization",
  "extended_reference_member", "measured", "test_eligible",
  "test_exclusion_reason"
)
master <- fread(
  input_paths[["gene_annotation_master.tsv.gz"]],
  select = master_columns
)
master[, similarity_feature_id := fifelse(
  reference_only %in% TRUE, reference_only_id, feature_id_original
)]
must(!anyNA(master$similarity_feature_id), "Phase 09 master has a missing feature identity")
must(
  !anyDuplicated(master[, .(rds_id, similarity_feature_id)]),
  "Phase 09 master feature key is not unique"
)

mito_master <- master[mito_tier %chin% accepted_tiers]
must(nrow(mito_master) > 0L, "No accepted mitochondrial features are present")
signature_fields <- c(
  "reference_only", "reference_source", "symbol_original",
  "ensembl_id_stable", "symbol_hgnc_current", "hgnc_id",
  "mapping_status", "mito_tier", "genome_origin",
  "sub_mito_localization", "extended_reference_member"
)
mito_master[, annotation_signature := do.call(
  paste,
  c(lapply(.SD, function(x) fifelse(is.na(x), "<NA>", as.character(x))),
    sep = "\r")
), .SDcols = signature_fields]
feature_consistency <- mito_master[, .(
  source_rds_count = uniqueN(rds_id),
  mapping_consistent = uniqueN(annotation_signature) == 1L
), by = similarity_feature_id]
setorder(mito_master, similarity_feature_id, rds_id)
feature_manifest <- mito_master[, .SD[1L], by = similarity_feature_id]
feature_manifest <- merge(
  feature_manifest, feature_consistency,
  by = "similarity_feature_id", all.x = TRUE, sort = FALSE
)
feature_manifest[, in_core_mito := mito_tier %chin% core_tiers]
feature_manifest[, in_all_mito_related := mito_tier %chin% all_tiers]
feature_manifest[, scoreable_source_feature :=
  !reference_only & mapping_consistent]
setnames(feature_manifest, "rds_id", "representative_rds_id")
feature_manifest[, annotation_signature := NULL]
feature_manifest[, schema_version := phase10$schemas$feature_manifest]
feature_columns <- c(
  "schema_version", "similarity_feature_id", "feature_id_original",
  "reference_only_id", "reference_only", "reference_source",
  "representative_rds_id", "source_rds_count", "symbol_original",
  "symbol_hgnc_current", "hgnc_id", "ensembl_id_stable",
  "mapping_status", "mapping_consistent", "mito_tier", "genome_origin",
  "sub_mito_localization", "extended_reference_member", "measured",
  "test_eligible", "test_exclusion_reason", "in_core_mito",
  "in_all_mito_related", "scoreable_source_feature"
)
feature_manifest <- feature_manifest[, ..feature_columns]
must(
  !anyDuplicated(feature_manifest$similarity_feature_id),
  "Mitochondrial feature manifest identity is not unique"
)
must(
  all(feature_manifest$in_all_mito_related),
  "An accepted mitochondrial feature is outside all_mito_related"
)

deg_columns <- c(
  "schema_version", "rds_id", "contrast_id", "manifest_row",
  "cell_type_high_resolution", "sex", "apoe_group", "yu_stratum",
  "analysis_population", "terminal_status", "feature_id_original",
  "reference_only_id", "reference_only", "tested_status", "deg_state",
  "phase08_row_present", "modeling_status", "contrast_status_message",
  "symbol_hgnc_current", "hgnc_id", "ensembl_id_stable", "mito_tier",
  "genome_origin", "sub_mito_localization", "mapping_status",
  "logFC", "fdr_bh_within_contrast", "paper_deg"
)
deg <- fread(
  input_paths[["deg_all_annotated.tsv.gz"]],
  select = deg_columns
)
must(
  all(deg$schema_version == phase10$expected_phase09$annotated_results_schema),
  "Unexpected Phase 09 annotated-result schema"
)
deg[, similarity_feature_id := fifelse(
  reference_only %in% TRUE, reference_only_id, feature_id_original
)]
must(!anyNA(deg$similarity_feature_id), "Annotated DEG grid has missing feature identities")
must(
  !anyDuplicated(deg[, .(rds_id, contrast_id, similarity_feature_id)]),
  "Phase 09 annotated DEG key is not unique"
)

allowed_tested_status <- c(
  "contrast_not_estimable", "not_in_expression_matrix",
  "present_but_filtered_min_pct", "tested_not_significant",
  "significant_up", "significant_down"
)
must(
  all(deg$tested_status %chin% allowed_tested_status),
  "Unexpected tested_status in Phase 09"
)
state_mapping_ok <- (
  deg$tested_status == "significant_up" & deg$deg_state == 1L
) | (
  deg$tested_status == "significant_down" & deg$deg_state == -1L
) | (
  deg$tested_status == "tested_not_significant" & deg$deg_state == 0L
) | (
  deg$tested_status %chin% c(
    "contrast_not_estimable", "not_in_expression_matrix",
    "present_but_filtered_min_pct"
  ) & is.na(deg$deg_state)
)
must(all(state_mapping_ok), "Phase 09 tested_status-to-state mapping is invalid")

contrast_columns <- c(
  "rds_id", "contrast_id", "manifest_row", "cell_type_high_resolution",
  "sex", "apoe_group", "yu_stratum", "analysis_population",
  "terminal_status"
)
contrast_manifest <- unique(deg[, ..contrast_columns])
must(
  nrow(contrast_manifest) == phase09_status$planned_contrasts[[1L]],
  "Contrast count does not match Phase 09 status"
)
must(
  !anyDuplicated(contrast_manifest[, .(
    rds_id, cell_type_high_resolution, sex, apoe_group
  )]),
  "Phase 09 sex/APOE contrast grid is not unique"
)
must(
  all(
    contrast_manifest[, .N, by = .(
      rds_id, cell_type_high_resolution
    )]$N == 6L
  ),
  "Each local cell type must contain all six sex/APOE strata"
)

comparison_config <- rbindlist(lapply(
  phase10$comparisons,
  function(x) data.table(
    comparison_id = as.character(x$comparison_id),
    yu_analogue = as.character(x$yu_analogue),
    first_state_label = as.character(x$first_state),
    second_state_label = as.character(x$second_state),
    dimension_keys = paste(
      unlist(x$dimension_keys, use.names = FALSE), collapse = " + "
    ),
    nominal_dimensions = as.integer(x$nominal_dimensions),
    panel_tail_size = as.integer(x$panel_tail_size)
  )
))
comparison_config[, comparison_order := seq_len(.N)]
expected_comparisons <- c(
  "female_vs_male_all_apoe", "e2_vs_e33_all_sexes",
  "e4_vs_e33_all_sexes", "female_vs_male_e2",
  "female_vs_male_e33", "female_vs_male_e4"
)
must(
  identical(comparison_config$comparison_id, expected_comparisons),
  "Phase 10 comparison IDs or order differ from the frozen definition"
)

make_dimensions <- function(
    comparison_id, key_columns,
    first_sex = NULL, second_sex = NULL,
    first_apoe = NULL, second_apoe = NULL) {
  first <- copy(contrast_manifest)
  second <- copy(contrast_manifest)
  if (!is.null(first_sex)) first <- first[sex == first_sex]
  if (!is.null(second_sex)) second <- second[sex == second_sex]
  if (!is.null(first_apoe)) first <- first[apoe_group == first_apoe]
  if (!is.null(second_apoe)) second <- second[apoe_group == second_apoe]
  retain <- c(key_columns, "contrast_id", "terminal_status", "analysis_population")
  first <- first[, ..retain]
  second <- second[, ..retain]
  setnames(
    first,
    c("contrast_id", "terminal_status", "analysis_population"),
    c("first_contrast_id", "first_terminal_status", "first_analysis_population")
  )
  setnames(
    second,
    c("contrast_id", "terminal_status", "analysis_population"),
    c("second_contrast_id", "second_terminal_status", "second_analysis_population")
  )
  out <- merge(first, second, by = key_columns, all = TRUE, sort = TRUE)
  out[, comparison_id := comparison_id]
  out[, dimension_id := paste(
    comparison_id,
    do.call(paste, c(.SD, sep = "::")),
    sep = "::"
  ), .SDcols = key_columns]
  out[, planned_dimension :=
    !is.na(first_contrast_id) & !is.na(second_contrast_id)]
  out[, structurally_estimable :=
    first_terminal_status == "validated_complete" &
      second_terminal_status == "validated_complete"]
  out[, structural_status := fcase(
    !planned_dimension, "missing_contrast",
    first_terminal_status == "failed" |
      second_terminal_status == "failed", "failed",
    structurally_estimable, "validated_complete",
    default = "not_estimable"
  )]
  setorderv(out, key_columns)
  out[, dimension_order := seq_len(.N)]
  out
}

dimension_list <- list(
  make_dimensions(
    "female_vs_male_all_apoe",
    c("rds_id", "cell_type_high_resolution", "apoe_group"),
    first_sex = "Female", second_sex = "Male"
  ),
  make_dimensions(
    "e2_vs_e33_all_sexes",
    c("rds_id", "cell_type_high_resolution", "sex"),
    first_apoe = "e2", second_apoe = "e33"
  ),
  make_dimensions(
    "e4_vs_e33_all_sexes",
    c("rds_id", "cell_type_high_resolution", "sex"),
    first_apoe = "e4", second_apoe = "e33"
  ),
  make_dimensions(
    "female_vs_male_e2",
    c("rds_id", "cell_type_high_resolution"),
    first_sex = "Female", second_sex = "Male",
    first_apoe = "e2", second_apoe = "e2"
  ),
  make_dimensions(
    "female_vs_male_e33",
    c("rds_id", "cell_type_high_resolution"),
    first_sex = "Female", second_sex = "Male",
    first_apoe = "e33", second_apoe = "e33"
  ),
  make_dimensions(
    "female_vs_male_e4",
    c("rds_id", "cell_type_high_resolution"),
    first_sex = "Female", second_sex = "Male",
    first_apoe = "e4", second_apoe = "e4"
  )
)
dimensions <- rbindlist(dimension_list, fill = TRUE)
dimensions <- merge(
  dimensions,
  comparison_config[, .(
    comparison_id, comparison_order, yu_analogue,
    first_state_label, second_state_label, nominal_dimensions
  )],
  by = "comparison_id", all.x = TRUE, sort = FALSE
)
setorder(dimensions, comparison_order, dimension_order)
dimensions[, schema_version := phase10$schemas$dimension_manifest]
setcolorder(dimensions, c(
  "schema_version", "comparison_order", "comparison_id", "yu_analogue",
  "dimension_order", "dimension_id", "rds_id",
  "cell_type_high_resolution", "sex", "apoe_group",
  "first_state_label", "second_state_label",
  "first_contrast_id", "second_contrast_id",
  "first_terminal_status", "second_terminal_status",
  "first_analysis_population", "second_analysis_population",
  "planned_dimension", "structurally_estimable", "structural_status",
  "nominal_dimensions"
))
must(
  !anyDuplicated(dimensions[, .(comparison_id, dimension_id)]),
  "Comparison/dimension key is not unique"
)

dimension_summary <- dimensions[, .(
  planned_dimensions = .N,
  structurally_estimable_dimensions = sum(structurally_estimable),
  non_estimable_dimensions = sum(structural_status == "not_estimable"),
  failed_dimensions = sum(structural_status == "failed"),
  missing_contrast_dimensions = sum(structural_status == "missing_contrast")
), by = comparison_id]
comparison_manifest <- merge(
  comparison_config, dimension_summary,
  by = "comparison_id", all.x = TRUE, sort = FALSE
)
comparison_manifest[, minimum_paired_tests :=
  as.integer(phase10$coverage$minimum_paired_tests)]
comparison_manifest[, minimum_structural_fraction :=
  as.numeric(phase10$coverage$minimum_structural_fraction)]
comparison_manifest[, supplemental_tail_size :=
  as.integer(phase10$rank_sets$supplemental_tail_size)]
comparison_manifest[, expected_selection_sizes := paste(
  sort(unique(c(panel_tail_size, supplemental_tail_size))),
  collapse = ","
), by = comparison_id]
comparison_manifest[, schema_version := phase10$schemas$comparison_manifest]
setorder(comparison_manifest, comparison_order)
setcolorder(comparison_manifest, c(
  "schema_version", "comparison_order", "comparison_id", "yu_analogue",
  "first_state_label", "second_state_label", "dimension_keys",
  "nominal_dimensions", "planned_dimensions",
  "structurally_estimable_dimensions", "non_estimable_dimensions",
  "failed_dimensions", "missing_contrast_dimensions",
  "minimum_paired_tests", "minimum_structural_fraction",
  "panel_tail_size", "supplemental_tail_size",
  "expected_selection_sizes"
))
must(nrow(comparison_manifest) == 6L, "Exactly six comparison rows are required")
if (!identical(execution_stage, "local_pilot")) {
  must(
    all(
      comparison_manifest$planned_dimensions ==
        comparison_manifest$nominal_dimensions
    ),
    "Production planned dimensions do not match nominal dimensions"
  )
}

mito_ids <- feature_manifest$similarity_feature_id
deg_mito <- deg[similarity_feature_id %chin% mito_ids]
must(
  all(mito_ids %chin% deg_mito$similarity_feature_id),
  "A mitochondrial feature is absent from the Phase 09 DEG grid"
)
state_source <- deg_mito[, .(
  rds_id, contrast_id, similarity_feature_id, tested_status,
  state = as.integer(deg_state), logFC, fdr_bh_within_contrast,
  paper_deg, phase08_row_present, modeling_status,
  contrast_status_message
)]
must(
  !anyDuplicated(state_source[, .(
    rds_id, contrast_id, similarity_feature_id
  )]),
  "Mitochondrial state-source key is not unique"
)

dimension_grid <- dimensions[, .(
  comparison_order, comparison_id, yu_analogue,
  dimension_order, dimension_id, rds_id,
  cell_type_high_resolution, sex, apoe_group,
  nominal_dimensions, first_state_label, second_state_label,
  first_contrast_id, second_contrast_id,
  first_terminal_status, second_terminal_status,
  structural_status, structurally_estimable
)]
dimension_grid[, join_key := 1L]
feature_ids <- feature_manifest[, .(similarity_feature_id)]
feature_ids[, join_key := 1L]
pairs <- merge(
  dimension_grid, feature_ids,
  by = "join_key", allow.cartesian = TRUE, sort = FALSE
)
pairs[, join_key := NULL]

first_source <- copy(state_source)
setnames(
  first_source,
  c(
    "contrast_id", "tested_status", "state", "logFC",
    "fdr_bh_within_contrast", "paper_deg", "phase08_row_present",
    "modeling_status", "contrast_status_message"
  ),
  c(
    "first_contrast_id", "first_tested_status", "first_state",
    "first_logFC", "first_fdr_bh_within_contrast", "first_paper_deg",
    "first_phase08_row_present", "first_modeling_status",
    "first_contrast_status_message"
  )
)
second_source <- copy(state_source)
setnames(
  second_source,
  c(
    "contrast_id", "tested_status", "state", "logFC",
    "fdr_bh_within_contrast", "paper_deg", "phase08_row_present",
    "modeling_status", "contrast_status_message"
  ),
  c(
    "second_contrast_id", "second_tested_status", "second_state",
    "second_logFC", "second_fdr_bh_within_contrast", "second_paper_deg",
    "second_phase08_row_present", "second_modeling_status",
    "second_contrast_status_message"
  )
)
pairs <- merge(
  pairs, first_source,
  by = c("rds_id", "first_contrast_id", "similarity_feature_id"),
  all.x = TRUE, sort = FALSE
)
pairs <- merge(
  pairs, second_source,
  by = c("rds_id", "second_contrast_id", "similarity_feature_id"),
  all.x = TRUE, sort = FALSE
)
pairs[, first_missing_reason := fifelse(
  !is.na(first_state), NA_character_,
  fifelse(is.na(first_tested_status), "phase09_row_missing", first_tested_status)
)]
pairs[, second_missing_reason := fifelse(
  !is.na(second_state), NA_character_,
  fifelse(is.na(second_tested_status), "phase09_row_missing", second_tested_status)
)]
pairs[, paired_for_score := !is.na(first_state) & !is.na(second_state)]
pairs[, state_pair := fifelse(
  paired_for_score,
  paste0("(", first_state, ",", second_state, ")"),
  NA_character_
)]
pairs[, schema_version := phase10$schemas$state_pairs]
setorder(pairs, comparison_order, dimension_order, similarity_feature_id)
setcolorder(pairs, c(
  "schema_version", "comparison_order", "comparison_id", "yu_analogue",
  "dimension_order", "dimension_id", "rds_id",
  "cell_type_high_resolution", "sex", "apoe_group",
  "similarity_feature_id", "nominal_dimensions",
  "first_state_label", "second_state_label",
  "first_contrast_id", "second_contrast_id",
  "first_terminal_status", "second_terminal_status",
  "structural_status", "structurally_estimable",
  "first_state", "second_state", "state_pair", "paired_for_score",
  "first_tested_status", "second_tested_status",
  "first_missing_reason", "second_missing_reason",
  "first_logFC", "second_logFC",
  "first_fdr_bh_within_contrast", "second_fdr_bh_within_contrast",
  "first_paper_deg", "second_paper_deg",
  "first_phase08_row_present", "second_phase08_row_present",
  "first_modeling_status", "second_modeling_status",
  "first_contrast_status_message", "second_contrast_status_message"
))
must(
  !anyDuplicated(pairs[, .(
    comparison_id, similarity_feature_id, dimension_id
  )]),
  "State-pair key is not unique"
)
must(
  all(na.omit(pairs$first_state) %in% c(-1L, 0L, 1L)) &&
    all(na.omit(pairs$second_state) %in% c(-1L, 0L, 1L)),
  "State-pair table contains an invalid ternary state"
)

results <- pairs[, .(
  planned_dimensions = .N,
  paired_tests = sum(paired_for_score),
  missing_first = sum(is.na(first_state) & !is.na(second_state)),
  missing_second = sum(!is.na(first_state) & is.na(second_state)),
  missing_both = sum(is.na(first_state) & is.na(second_state)),
  S_neg1_neg1 = sum(first_state == -1L & second_state == -1L, na.rm = TRUE),
  S_neg1_0 = sum(first_state == -1L & second_state == 0L, na.rm = TRUE),
  S_neg1_pos1 = sum(first_state == -1L & second_state == 1L, na.rm = TRUE),
  S_0_neg1 = sum(first_state == 0L & second_state == -1L, na.rm = TRUE),
  S_0_0 = sum(first_state == 0L & second_state == 0L, na.rm = TRUE),
  S_0_pos1 = sum(first_state == 0L & second_state == 1L, na.rm = TRUE),
  S_pos1_neg1 = sum(first_state == 1L & second_state == -1L, na.rm = TRUE),
  S_pos1_0 = sum(first_state == 1L & second_state == 0L, na.rm = TRUE),
  S_pos1_pos1 = sum(first_state == 1L & second_state == 1L, na.rm = TRUE)
), by = .(comparison_order, comparison_id, similarity_feature_id)]
results[, same_direction_significant := S_neg1_neg1 + S_pos1_pos1]
results[, one_sided_significant :=
  S_neg1_0 + S_0_neg1 + S_0_pos1 + S_pos1_0]
results[, opposite_direction_significant := S_neg1_pos1 + S_pos1_neg1]
results[, both_not_significant := S_0_0]

weights <- phase10$score
results[, score_numerator :=
  as.numeric(weights$same_direction_significant) *
    same_direction_significant +
  as.numeric(weights$one_sided_significant) *
    one_sided_significant +
  as.numeric(weights$opposite_direction_significant) *
    opposite_direction_significant +
  as.numeric(weights$both_not_significant) *
    both_not_significant
]
results[, similarity_score := fifelse(
  paired_tests > 0L, score_numerator / paired_tests, NA_real_
)]
results[, score_status := fifelse(
  paired_tests > 0L, "scoreable", "not_scoreable"
)]

result_comparison_fields <- comparison_manifest[, .(
  comparison_id, yu_analogue, nominal_dimensions,
  structurally_estimable_dimensions, minimum_paired_tests,
  minimum_structural_fraction
)]
result_feature_fields <- feature_manifest[, .(
  similarity_feature_id, feature_id_original, reference_only_id,
  reference_only, symbol_original, symbol_hgnc_current, hgnc_id,
  ensembl_id_stable, mapping_status, mapping_consistent, mito_tier,
  genome_origin, sub_mito_localization, in_core_mito,
  in_all_mito_related, scoreable_source_feature
)]
results <- merge(
  results, result_comparison_fields,
  by = "comparison_id", all.x = TRUE, sort = FALSE
)
results <- merge(
  results, result_feature_fields,
  by = "similarity_feature_id", all.x = TRUE, sort = FALSE
)
results[, coverage_fraction := fifelse(
  structurally_estimable_dimensions > 0L,
  paired_tests / structurally_estimable_dimensions,
  NA_real_
)]
results[, nominal_coverage_fraction := paired_tests / nominal_dimensions]
results[, complete_nominal_vector := paired_tests == nominal_dimensions]
results[, required_paired_tests := as.integer(pmax(
  minimum_paired_tests,
  ceiling(minimum_structural_fraction * structurally_estimable_dimensions)
))]
results[, ranking_eligible :=
  scoreable_source_feature &
  structurally_estimable_dimensions >= minimum_paired_tests &
  paired_tests >= required_paired_tests
]
results[, ranking_ineligible_reason := fcase(
  reference_only, "reference_only_not_scoreable",
  !mapping_consistent, "inconsistent_feature_annotation",
  paired_tests == 0L, "no_paired_states",
  structurally_estimable_dimensions < minimum_paired_tests,
    "too_few_structurally_estimable_dimensions",
  paired_tests < required_paired_tests, "insufficient_paired_coverage",
  ranking_eligible, "eligible",
  default = "not_eligible"
)]
results[, score_scope := fcase(
  score_status == "not_scoreable", "not_scoreable",
  complete_nominal_vector, "complete_yu_vector",
  default = "coverage_adjusted_cross_celltype"
)]
results[, score_sign := fcase(
  is.na(similarity_score), "not_scoreable",
  similarity_score > 0, "positive",
  similarity_score < 0, "negative",
  default = "zero"
)]
results[, schema_version := phase10$schemas$results]

toy_checks <- data.table(
  first_states = c("+1,-1", "+1,-1", "+1,-1", "0,0"),
  second_states = c("+1,-1", "0,0", "-1,+1", "0,0"),
  expected_score = c(1, -0.5, -1, 0)
)
toy_checks[, observed_score := vapply(
  seq_len(.N),
  function(i) score_vectors(
    as.integer(strsplit(first_states[[i]], ",", fixed = TRUE)[[1L]]),
    as.integer(strsplit(second_states[[i]], ",", fixed = TRUE)[[1L]])
  ),
  numeric(1)
)]
toy_checks[, passed := abs(observed_score - expected_score) < 1e-12]
toy_checks[, schema_version := phase10$schemas$toy_checks]
toy_checks[, toy_id := sprintf("toy_%02d", seq_len(.N))]
setcolorder(toy_checks, c(
  "schema_version", "toy_id", "first_states", "second_states",
  "expected_score", "observed_score", "passed"
))

results[, `:=`(
  p_high = NA_real_,
  p_low = NA_real_,
  directional_p = NA_real_,
  descriptive_two_sided_p = NA_real_,
  permutation_seed = NA_integer_,
  permutation_seed_key = NA_character_,
  permutations_completed = NA_integer_
)]

RNGkind(
  kind = as.character(phase10$permutation$rng_kind),
  normal.kind = as.character(phase10$permutation$normal_kind),
  sample.kind = as.character(phase10$permutation$sample_kind)
)
setkey(pairs, comparison_id, similarity_feature_id, dimension_order)
eligible_rows <- which(results$ranking_eligible)
permutation_diagnostics_list <- vector("list", length(eligible_rows))
cat(
  "Phase 10 permutation inference: ", length(eligible_rows),
  " eligible feature/comparison rows x ", permutations, " draws\n",
  sep = ""
)
for (j in seq_along(eligible_rows)) {
  row_index <- eligible_rows[[j]]
  comparison_value <- results$comparison_id[[row_index]]
  feature_value <- results$similarity_feature_id[[row_index]]
  observed_score <- results$similarity_score[[row_index]]
  vector_rows <- pairs[list(comparison_value, feature_value)][
    paired_for_score %in% TRUE
  ]
  first <- as.integer(vector_rows$first_state)
  second <- as.integer(vector_rows$second_state)
  n <- length(first)
  must(
    n == results$paired_tests[[row_index]],
    "Permutation vector length does not match paired_tests"
  )
  seed_key <- paste(
    phase10$permutation$base_seed, comparison_value, feature_value,
    execution_stage, permutations, sep = "|"
  )
  seed <- seed_from_key(seed_key, as.integer(phase10$permutation$base_seed))
  set.seed(seed)
  null_scores <- numeric(permutations)
  for (b in seq_len(permutations)) {
    null_scores[[b]] <- score_vectors(first, second[sample.int(n)])
  }
  high_exceedances <- sum(null_scores >= observed_score)
  low_exceedances <- sum(null_scores <= observed_score)
  p_high <- (1 + high_exceedances) / (permutations + 1)
  p_low <- (1 + low_exceedances) / (permutations + 1)
  directional_p <- if (observed_score > 0) {
    p_high
  } else if (observed_score < 0) {
    p_low
  } else {
    1
  }
  two_sided <- min(1, 2 * min(p_high, p_low))
  set(
    results, i = row_index,
    j = c(
      "p_high", "p_low", "directional_p",
      "descriptive_two_sided_p", "permutation_seed",
      "permutation_seed_key", "permutations_completed"
    ),
    value = list(
      p_high, p_low, directional_p, two_sided,
      seed, seed_key, permutations
    )
  )
  quantiles <- as.numeric(quantile(
    null_scores, probs = c(0.025, 0.25, 0.5, 0.75, 0.975),
    names = FALSE, type = 7
  ))
  permutation_diagnostics_list[[j]] <- data.table(
    schema_version = phase10$schemas$permutation_diagnostics,
    comparison_id = comparison_value,
    similarity_feature_id = feature_value,
    paired_tests = n,
    null_draws = permutations,
    seed_key = seed_key,
    seed = seed,
    null_mean = mean(null_scores),
    null_sd = sd(null_scores),
    null_min = min(null_scores),
    null_q025 = quantiles[[1L]],
    null_q25 = quantiles[[2L]],
    null_median = quantiles[[3L]],
    null_q75 = quantiles[[4L]],
    null_q975 = quantiles[[5L]],
    null_max = max(null_scores),
    high_exceedances = high_exceedances,
    low_exceedances = low_exceedances,
    p_high = p_high,
    p_low = p_low,
    directional_p = directional_p,
    descriptive_two_sided_p = two_sided,
    marginal_state_counts_preserved = TRUE
  )
  if (j %% 250L == 0L || j == length(eligible_rows)) {
    cat("  completed ", j, "/", length(eligible_rows), "\n", sep = "")
  }
}
permutation_diagnostics <- if (length(permutation_diagnostics_list)) {
  rbindlist(permutation_diagnostics_list)
} else {
  data.table(
    schema_version = character(), comparison_id = character(),
    similarity_feature_id = character(), paired_tests = integer(),
    null_draws = integer(), seed_key = character(), seed = integer()
  )
}

rank_columns <- c(
  "directional_fdr_bh_core_mito",
  "directional_fdr_bh_all_mito_related",
  "high_rank_core_mito", "low_rank_core_mito",
  "score_tie_high_rank_core_mito", "score_tie_low_rank_core_mito",
  "high_rank_all_mito_related", "low_rank_all_mito_related",
  "score_tie_high_rank_all_mito_related",
  "score_tie_low_rank_all_mito_related"
)
for (column in rank_columns) results[, (column) := NA_real_]
results[, fdr_family_size_core_mito := NA_integer_]
results[, fdr_family_size_all_mito_related := NA_integer_]

apply_universe <- function(universe, membership_column) {
  fdr_column <- paste0("directional_fdr_bh_", universe)
  family_size_column <- paste0("fdr_family_size_", universe)
  high_rank_column <- paste0("high_rank_", universe)
  low_rank_column <- paste0("low_rank_", universe)
  tie_high_column <- paste0("score_tie_high_rank_", universe)
  tie_low_column <- paste0("score_tie_low_rank_", universe)
  for (comparison_id in expected_comparisons) {
    member_rows <- which(
      results$comparison_id == comparison_id &
        results[[membership_column]]
    )
    family_rows <- member_rows[results$ranking_eligible[member_rows]]
    family_size <- length(family_rows)
    set(
      results, i = member_rows, j = family_size_column,
      value = as.integer(family_size)
    )
    if (!family_size) next
    adjusted <- p.adjust(
      results$directional_p[family_rows],
      method = as.character(phase10$fdr$method)
    )
    set(results, i = family_rows, j = fdr_column, value = adjusted)

    high_order <- order(
      -results$similarity_score[family_rows],
      -results$paired_tests[family_rows],
      results$similarity_feature_id[family_rows]
    )
    low_order <- order(
      results$similarity_score[family_rows],
      -results$paired_tests[family_rows],
      results$similarity_feature_id[family_rows]
    )
    high_rank <- integer(family_size)
    low_rank <- integer(family_size)
    high_rank[high_order] <- seq_len(family_size)
    low_rank[low_order] <- seq_len(family_size)
    set(results, i = family_rows, j = high_rank_column, value = high_rank)
    set(results, i = family_rows, j = low_rank_column, value = low_rank)
    set(
      results, i = family_rows, j = tie_high_column,
      value = as.integer(frank(
        -results$similarity_score[family_rows], ties.method = "min"
      ))
    )
    set(
      results, i = family_rows, j = tie_low_column,
      value = as.integer(frank(
        results$similarity_score[family_rows], ties.method = "min"
      ))
    )
  }
}
apply_universe("core_mito", "in_core_mito")
apply_universe("all_mito_related", "in_all_mito_related")

rank_set_rows <- list()
rank_counter <- 0L
supplemental_tail_size <- as.integer(phase10$rank_sets$supplemental_tail_size)
for (comparison_value in expected_comparisons) {
  comparison_row <- comparison_manifest[
    comparison_id == comparison_value
  ]
  requested_sizes <- sort(unique(c(
    comparison_row$panel_tail_size[[1L]], supplemental_tail_size
  )))
  for (universe in c("core_mito", "all_mito_related")) {
    membership_column <- if (universe == "core_mito") {
      "in_core_mito"
    } else {
      "in_all_mito_related"
    }
    fdr_column <- paste0("directional_fdr_bh_", universe)
    high_rank_column <- paste0("high_rank_", universe)
    low_rank_column <- paste0("low_rank_", universe)
    family_rows <- which(
      results$comparison_id == comparison_value &
        results[[membership_column]] &
        results$ranking_eligible
    )
    eligible_genes <- length(family_rows)
    for (requested_k in requested_sizes) {
      selected_k <- min(requested_k, floor(eligible_genes / 2))
      if (selected_k < 1L) next
      high_order <- family_rows[order(
        -results$similarity_score[family_rows],
        -results$paired_tests[family_rows],
        results$similarity_feature_id[family_rows]
      )]
      low_order <- family_rows[order(
        results$similarity_score[family_rows],
        -results$paired_tests[family_rows],
        results$similarity_feature_id[family_rows]
      )]
      high_selected <- head(high_order, selected_k)
      low_selected <- head(
        low_order[!low_order %in% high_selected],
        selected_k
      )
      selected <- list(
        high_score = high_selected,
        low_score = low_selected
      )
      for (tail in names(selected)) {
        chosen <- selected[[tail]]
        rank_counter <- rank_counter + 1L
        rank_column <- if (tail == "high_score") {
          high_rank_column
        } else {
          low_rank_column
        }
        block <- results[chosen, .(
          comparison_order, comparison_id, yu_analogue,
          similarity_feature_id, feature_id_original,
          symbol_hgnc_current, hgnc_id, ensembl_id_stable,
          mito_tier, score_scope, similarity_score, paired_tests,
          nominal_dimensions, nominal_coverage_fraction,
          coverage_fraction, score_sign
        )]
        block[, analysis_universe := universe]
        block[, tail := tail]
        block[, requested_k := as.integer(requested_k)]
        block[, selected_k := as.integer(selected_k)]
        block[, eligible_genes := as.integer(eligible_genes)]
        block[, size_shortfall := as.integer(requested_k - selected_k)]
        block[, deterministic_rank := as.integer(results[[rank_column]][chosen])]
        block[, directional_fdr_bh := results[[fdr_column]][chosen]]
        block[, selection_order := seq_len(.N)]
        block[, rank_set_id := paste(
          comparison_value, universe, tail, requested_k, sep = "::"
        )]
        rank_set_rows[[rank_counter]] <- block
      }
    }
  }
}
rank_sets <- rbindlist(rank_set_rows, fill = TRUE)
rank_sets[, schema_version := phase10$schemas$rank_sets]
setorder(
  rank_sets, comparison_order, analysis_universe,
  requested_k, tail, selection_order
)
setcolorder(rank_sets, c(
  "schema_version", "rank_set_id", "comparison_order", "comparison_id",
  "yu_analogue", "analysis_universe", "tail", "requested_k",
  "selected_k", "eligible_genes", "size_shortfall", "selection_order",
  "deterministic_rank", "similarity_feature_id", "feature_id_original",
  "symbol_hgnc_current", "hgnc_id", "ensembl_id_stable", "mito_tier",
  "score_scope", "similarity_score", "score_sign",
  "directional_fdr_bh", "paired_tests", "nominal_dimensions",
  "nominal_coverage_fraction", "coverage_fraction"
))

universe_results <- rbindlist(list(
  results[in_core_mito == TRUE, .(
    comparison_id, analysis_universe = "core_mito", mito_tier,
    score_status, score_scope, score_sign, ranking_eligible,
    coverage_fraction,
    directional_fdr_bh = directional_fdr_bh_core_mito
  )],
  results[in_all_mito_related == TRUE, .(
    comparison_id, analysis_universe = "all_mito_related", mito_tier,
    score_status, score_scope, score_sign, ranking_eligible,
    coverage_fraction,
    directional_fdr_bh = directional_fdr_bh_all_mito_related
  )]
), use.names = TRUE)

qc_rows <- list()
add_qc_counts <- function(data, metric, category_column) {
  out <- data[, .(value = .N), by = c(
    "comparison_id", "analysis_universe", "mito_tier", category_column
  )]
  setnames(out, category_column, "category")
  out[, metric := metric]
  out
}
qc_rows[[1L]] <- add_qc_counts(universe_results, "score_status", "score_status")
qc_rows[[2L]] <- add_qc_counts(universe_results, "score_scope", "score_scope")
qc_rows[[3L]] <- add_qc_counts(universe_results, "score_sign", "score_sign")
qc_rows[[4L]] <- add_qc_counts(
  universe_results, "ranking_eligible", "ranking_eligible"
)
fdr_summary <- copy(universe_results[ranking_eligible == TRUE])
fdr_summary[, fdr_category := fifelse(
  !is.na(directional_fdr_bh) &
    directional_fdr_bh <= as.numeric(phase10$fdr$threshold),
  "fdr_at_or_below_threshold", "fdr_above_threshold"
)]
qc_rows[[5L]] <- add_qc_counts(fdr_summary, "directional_fdr", "fdr_category")
coverage_qc <- universe_results[, .(
  value = if (all(is.na(coverage_fraction))) {
    NA_real_
  } else {
    median(coverage_fraction, na.rm = TRUE)
  }
), by = .(comparison_id, analysis_universe, mito_tier)]
coverage_qc[, `:=`(metric = "median_coverage_fraction", category = "")]
qc_rows[[6L]] <- coverage_qc
rank_qc <- rank_sets[, .(value = .N), by = .(
  comparison_id, analysis_universe, mito_tier, tail
)]
setnames(rank_qc, "tail", "category")
rank_qc[, metric := "rank_set_memberships"]
qc_rows[[7L]] <- rank_qc
qc_summary <- rbindlist(qc_rows, fill = TRUE)
qc_summary[, schema_version := phase10$schemas$qc_summary]
setcolorder(qc_summary, c(
  "schema_version", "comparison_id", "analysis_universe",
  "mito_tier", "metric", "category", "value"
))
setorder(
  qc_summary, comparison_id, analysis_universe,
  mito_tier, metric, category
)

checks_list <- list()
add_check <- function(check_name, passed, observed, expected, details = "") {
  checks_list[[length(checks_list) + 1L]] <<- data.table(
    schema_version = phase10$schemas$checks,
    check_name = check_name,
    passed = isTRUE(passed),
    observed = as.character(observed),
    expected = as.character(expected),
    details = as.character(details)
  )
}
add_check(
  "phase09_status_validated", nrow(phase09_status) == 1L &&
    phase09_status$validation_status[[1L]] == "validated_complete",
  phase09_status$validation_status[[1L]], "validated_complete"
)
add_check(
  "phase09_blocking_checks", all(phase09_checks$passed %in% TRUE),
  sum(phase09_checks$passed %in% TRUE), nrow(phase09_checks)
)
add_check(
  "phase09_artifact_hashes", all(artifact_hash_ok),
  sum(artifact_hash_ok), length(artifact_hash_ok)
)
add_check(
  "feature_identity_unique",
  !anyDuplicated(feature_manifest$similarity_feature_id),
  uniqueN(feature_manifest$similarity_feature_id), nrow(feature_manifest)
)
add_check(
  "feature_annotations_consistent",
  all(feature_manifest$mapping_consistent),
  sum(feature_manifest$mapping_consistent), nrow(feature_manifest)
)
add_check(
  "six_comparisons", nrow(comparison_manifest) == 6L,
  nrow(comparison_manifest), 6L
)
add_check(
  "dimension_keys_unique",
  !anyDuplicated(dimensions[, .(comparison_id, dimension_id)]),
  uniqueN(dimensions[, .(comparison_id, dimension_id)]), nrow(dimensions)
)
add_check(
  "no_failed_dimensions",
  !any(dimensions$structural_status == "failed"),
  sum(dimensions$structural_status == "failed"), 0L
)
add_check(
  "state_pair_keys_unique",
  !anyDuplicated(pairs[, .(
    comparison_id, similarity_feature_id, dimension_id
  )]),
  uniqueN(pairs[, .(
    comparison_id, similarity_feature_id, dimension_id
  )]), nrow(pairs)
)
add_check(
  "ternary_states_valid",
  all(na.omit(pairs$first_state) %in% c(-1L, 0L, 1L)) &&
    all(na.omit(pairs$second_state) %in% c(-1L, 0L, 1L)),
  "all nonmissing states", "-1,0,+1"
)
add_check(
  "paired_state_counts_reconcile",
  all(
    results$paired_tests ==
      results$S_neg1_neg1 + results$S_neg1_0 +
      results$S_neg1_pos1 + results$S_0_neg1 +
      results$S_0_0 + results$S_0_pos1 +
      results$S_pos1_neg1 + results$S_pos1_0 +
      results$S_pos1_pos1
  ),
  "all result rows", "nine cells sum to paired_tests"
)
add_check(
  "score_range",
  all(
    results$similarity_score[results$score_status == "scoreable"] >= -1 &
      results$similarity_score[results$score_status == "scoreable"] <= 1
  ),
  paste(range(
    results$similarity_score[results$score_status == "scoreable"],
    na.rm = TRUE
  ), collapse = ","),
  "[-1,1]"
)
add_check(
  "zero_pairs_not_scoreable",
  all(
    results$score_status[results$paired_tests == 0L] == "not_scoreable" &
      is.na(results$similarity_score[results$paired_tests == 0L])
  ),
  sum(results$paired_tests == 0L), "all NA scores"
)
add_check(
  "toy_scores", all(toy_checks$passed),
  sum(toy_checks$passed), nrow(toy_checks)
)
add_check(
  "result_keys_unique",
  !anyDuplicated(results[, .(comparison_id, similarity_feature_id)]),
  uniqueN(results[, .(comparison_id, similarity_feature_id)]), nrow(results)
)
eligibility_expected <- with(
  results,
  scoreable_source_feature &
    structurally_estimable_dimensions >= minimum_paired_tests &
    paired_tests >= required_paired_tests
)
add_check(
  "ranking_eligibility_rule",
  identical(results$ranking_eligible, eligibility_expected),
  sum(results$ranking_eligible), "exact minimum-three/50% rule"
)
add_check(
  "reference_only_not_scored",
  all(!results$ranking_eligible[results$reference_only]),
  sum(results$ranking_eligible[results$reference_only]), 0L
)
add_check(
  "permutation_row_count",
  nrow(permutation_diagnostics) == sum(results$ranking_eligible),
  nrow(permutation_diagnostics), sum(results$ranking_eligible)
)
add_check(
  "permutation_marginals_preserved",
  all(permutation_diagnostics$marginal_state_counts_preserved %in% TRUE),
  sum(permutation_diagnostics$marginal_state_counts_preserved %in% TRUE),
  nrow(permutation_diagnostics)
)
add_check(
  "empirical_p_range",
  all(
    results$directional_p[results$ranking_eligible] >=
      1 / (permutations + 1) &
      results$directional_p[results$ranking_eligible] <= 1
  ),
  paste(range(
    results$directional_p[results$ranking_eligible], na.rm = TRUE
  ), collapse = ","),
  paste0("[", 1 / (permutations + 1), ",1]")
)
core_family_ok <- all(vapply(
  expected_comparisons,
  function(id) {
    expected <- sum(
      results$comparison_id == id &
        results$in_core_mito &
        results$ranking_eligible
    )
    rows <- results$comparison_id == id & results$in_core_mito
    all(results$fdr_family_size_core_mito[rows] == expected)
  },
  logical(1)
))
all_family_ok <- all(vapply(
  expected_comparisons,
  function(id) {
    expected <- sum(
      results$comparison_id == id &
        results$in_all_mito_related &
        results$ranking_eligible
    )
    rows <- results$comparison_id == id & results$in_all_mito_related
    all(results$fdr_family_size_all_mito_related[rows] == expected)
  },
  logical(1)
))
add_check(
  "fdr_family_sizes", core_family_ok && all_family_ok,
  paste(
    sum(results$ranking_eligible & results$in_core_mito),
    sum(results$ranking_eligible & results$in_all_mito_related),
    sep = "/"
  ),
  "recorded eligible family sizes"
)
fdr_values <- c(
  results$directional_fdr_bh_core_mito,
  results$directional_fdr_bh_all_mito_related
)
add_check(
  "fdr_range",
  all(na.omit(fdr_values) >= 0 & na.omit(fdr_values) <= 1),
  paste(range(na.omit(fdr_values)), collapse = ","), "[0,1]"
)
rank_overlap <- rank_sets[, .(
  overlap = sum(duplicated(similarity_feature_id))
), by = .(comparison_id, analysis_universe, requested_k)]
add_check(
  "rank_tails_disjoint", all(rank_overlap$overlap == 0L),
  sum(rank_overlap$overlap), 0L
)
add_check(
  "rank_set_size_rule",
  all(rank_sets$selected_k <= rank_sets$requested_k) &&
    all(
      rank_sets$selected_k <= floor(rank_sets$eligible_genes / 2)
    ),
  max(rank_sets$selected_k), "requested size capped at floor(eligible/2)"
)
add_check(
  "no_figure_or_enrichment_outputs", TRUE,
  "tabular outputs only", "no PDF/PNG/SVG/enrichment"
)

checks <- rbindlist(checks_list)
must(
  all(checks$passed),
  paste(
    "Blocking Phase 10 checks failed:",
    paste(checks$check_name[!checks$passed], collapse = ", ")
  )
)

setorder(feature_manifest, similarity_feature_id)
setorder(comparison_manifest, comparison_order)
setorder(dimensions, comparison_order, dimension_order)
setorder(pairs, comparison_order, dimension_order, similarity_feature_id)
setorder(results, comparison_order, similarity_feature_id)
setorder(permutation_diagnostics, comparison_id, similarity_feature_id)

output_tables <- list(
  "mitochondrial_similarity_feature_manifest.tsv" = feature_manifest,
  "similarity_comparison_manifest.tsv" = comparison_manifest,
  "similarity_dimension_manifest.tsv" = dimensions,
  "mitochondrial_similarity_state_pairs.tsv.gz" = pairs,
  "mitochondrial_similarity_results.tsv.gz" = results,
  "mitochondrial_similarity_rank_sets.tsv" = rank_sets,
  "similarity_permutation_diagnostics.tsv.gz" = permutation_diagnostics,
  "similarity_toy_checks.tsv" = toy_checks,
  "similarity_qc_summary.tsv" = qc_summary,
  "similarity_checks.tsv" = checks
)
for (name in names(output_tables)) {
  atomic_fwrite(output_tables[[name]], file.path(staging_root, name))
}

artifact_rows <- lapply(names(output_tables), function(name) {
  stage_path <- file.path(staging_root, name)
  final_path <- file.path(final_root, name)
  table <- output_tables[[name]]
  data.table(
    schema_version = phase10$schemas$artifacts,
    artifact = name,
    path = relative_path(final_path, project_root),
    bytes = as.numeric(file.info(stage_path)$size),
    sha256 = sha256_file(stage_path),
    records = nrow(table),
    output_schema = if (nrow(table)) {
      as.character(table$schema_version[[1L]])
    } else {
      NA_character_
    },
    validation_status = "validated_complete"
  )
})
artifacts <- rbindlist(artifact_rows)
must(
  all(!is.na(artifacts$sha256) & nzchar(artifacts$sha256)),
  "Could not hash all Phase 10 artifacts"
)
atomic_fwrite(
  artifacts, file.path(staging_root, "similarity_artifacts.tsv")
)

status <- data.table(
  schema_version = phase10$schemas$status,
  execution_stage = execution_stage,
  execution_phase = as.integer(execution$execution_phase),
  backend = as.character(execution$backend),
  run_id = as.character(execution$run_id),
  stable_task_id = "global:similarity",
  task_mode = "similarity",
  scientific_script = "scripts/10_calculate_mitochondrial_similarity.R",
  scientific_script_sha256 = current_hashes$scientific_script_sha256,
  scientific_config_sha256 = current_hashes$scientific_config_sha256,
  pipeline_config_sha256 = current_hashes$pipeline_config_sha256,
  execution_config_sha256 = current_hashes$execution_config_sha256,
  rds_manifest_sha256 = current_hashes$rds_manifest_sha256,
  phase09_status_sha256 = current_hashes$phase09_status_sha256,
  phase09_artifacts_sha256 = current_hashes$phase09_artifacts_sha256,
  phase09_checks_sha256 = current_hashes$phase09_checks_sha256,
  phase09_master_sha256 = current_hashes$phase09_master_sha256,
  phase09_annotated_sha256 = current_hashes$phase09_annotated_sha256,
  phase09_reference_inventory_sha256 =
    current_hashes$phase09_reference_inventory_sha256,
  rds_sets = as.integer(phase09_status$rds_sets[[1L]]),
  fine_cell_types = as.integer(phase09_status$fine_cell_types[[1L]]),
  planned_contrasts = as.integer(phase09_status$planned_contrasts[[1L]]),
  mitochondrial_features = nrow(feature_manifest),
  comparison_families = nrow(comparison_manifest),
  planned_dimensions = nrow(dimensions),
  state_pair_rows = nrow(pairs),
  result_rows = nrow(results),
  ranking_eligible_rows = sum(results$ranking_eligible),
  rank_set_rows = nrow(rank_sets),
  permutations = permutations,
  permutation_profile = execution_stage,
  base_seed = as.integer(phase10$permutation$base_seed),
  fdr_method = as.character(phase10$fdr$method),
  fdr_family = as.character(phase10$fdr$family),
  failed_checks = sum(!checks$passed),
  r_version = as.character(getRversion()),
  data_table_version = as.character(packageVersion("data.table")),
  yaml_version = as.character(packageVersion("yaml")),
  digest_version = as.character(packageVersion("digest")),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(
    Sys.time(), start_time, units = "secs"
  )),
  validation_status = expected_validation_status,
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
)
atomic_fwrite(status, file.path(staging_root, "similarity_status.tsv"))

must(!dir.exists(final_root), "Final Phase 10 directory appeared during execution")
if (!file.rename(staging_root, final_root)) {
  stop("Could not atomically publish Phase 10 output directory", call. = FALSE)
}
cleanup_staging <- FALSE

cat("Phase 10 completed successfully\n")
cat("  output: ", final_root, "\n", sep = "")
cat("  status: ", expected_validation_status, "\n", sep = "")
cat("  features: ", nrow(feature_manifest), "\n", sep = "")
cat("  eligible feature/comparison rows: ", sum(results$ranking_eligible), "\n", sep = "")
cat("  permutations per eligible row: ", permutations, "\n", sep = "")
