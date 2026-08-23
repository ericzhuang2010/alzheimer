#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/07_build_contrast_manifests.R --config FILE
")
      quit(status = 0L)
    }
    if (args[[i]] != "--config" || i == length(args)) stop("Unknown or incomplete argument: ", args[[i]])
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, temporary, sep = "	", na = "NA", quote = FALSE,
                     compress = if (grepl("[.]gz$", path)) "gzip" else "none")
  if (!file.rename(temporary, path)) stop("Atomic rename failed: ", path)
}
sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)
relative_path <- function(path, root) {
  normalized <- normalizePath(path, mustWork = TRUE)
  prefix <- paste0(normalizePath(root, mustWork = TRUE), "/")
  if (!startsWith(normalized, prefix)) stop("Artifact escapes project root: ", normalized)
  substring(normalized, nchar(prefix) + 1L)
}
require_phase <- function(output_root, phase, project_root) {
  directory <- file.path(output_root, phase)
  status <- data.table::fread(file.path(directory, "status.tsv"), data.table = FALSE)
  if (nrow(status) != 1L || status$validation_status[[1L]] != "validated_complete") stop("Invalid predecessor: ", phase)
  artifacts <- data.table::fread(file.path(directory, "artifacts.tsv"), data.table = FALSE)
  for (i in seq_len(nrow(artifacts))) {
    path <- file.path(project_root, artifacts$path[[i]])
    if (!file.exists(path) || file.info(path)$size != artifacts$bytes[[i]] ||
        sha256_file(path) != artifacts$digest_value[[i]]) stop("Predecessor artifact mismatch: ", path)
  }
  status
}
write_artifacts <- function(paths, destination, project_root) {
  rows <- lapply(paths, function(path) data.frame(
    artifact = basename(path), path = relative_path(path, project_root),
    artifact_role = "result", bytes = file.info(path)$size,
    digest_algorithm = "sha256", digest_scope = "full_file",
    digest_value = sha256_file(path), stringsAsFactors = FALSE
  ))
  atomic_fwrite(data.table::rbindlist(rows), destination)
}

group_specs <- function(config) {
  data.frame(
    signature_group = vapply(config$cohort$signature_groups, function(x) x$group_id, character(1)),
    sex = vapply(config$cohort$signature_groups, function(x) x$sex, character(1)),
    apoe_group = vapply(config$cohort$signature_groups, function(x) x$apoe_group, character(1)),
    stringsAsFactors = FALSE
  )
}

build_grouped_design <- function(metadata, group_levels) {
  metadata$diagnosis_id <- ifelse(metadata$diagnosis == "No dementia", "No_dementia", "Dementia")
  observed <- paste(metadata$diagnosis_id, metadata$signature_group, sep = "__")
  levels_used <- group_levels[group_levels %in% observed]

  # Construct the no-intercept group indicators explicitly so sparse contexts
  # with a single observed group remain auditable instead of failing factor coding.
  group_matrix <- outer(observed, levels_used, FUN = "==") * 1
  colnames(group_matrix) <- paste0("diagnosis_sex_apoe_group", levels_used)
  numeric_matrix <- as.matrix(metadata[, c("age_death_scaled", "pmi_scaled"), drop = FALSE])
  storage.mode(numeric_matrix) <- "double"

  study_levels <- sort(unique(metadata$study))
  if (length(study_levels) > 1L) {
    study_matrix <- outer(metadata$study, study_levels[-1L], FUN = "==") * 1
    colnames(study_matrix) <- paste0("study", study_levels[-1L])
  } else {
    study_matrix <- matrix(numeric(0), nrow = nrow(metadata), ncol = 0L)
  }
  design <- cbind(group_matrix, numeric_matrix, study_matrix)
  storage.mode(design) <- "double"
  list(metadata = metadata, design = design)
}

build_pooled_design <- function(metadata) {
  metadata$diagnosis <- factor(metadata$diagnosis, levels = c("No dementia", "Dementia"))
  metadata$sex <- factor(metadata$sex, levels = c("Female", "Male"))
  metadata$apoe_group <- factor(metadata$apoe_group, levels = c("e33", "e2", "e4"))
  metadata$study <- factor(metadata$study, levels = sort(unique(metadata$study)))
  model.matrix(
    ~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
}

design_record <- function(design, design_id, tier, context_id, formula_id) {
  rank <- if (nrow(design) && ncol(design)) qr(design)$rank else 0L
  data.frame(
    design_id = design_id, deg_tier = tier, context_id = context_id,
    formula_id = formula_id, samples = nrow(design), design_columns = ncol(design),
    design_rank = rank, full_rank = rank == ncol(design),
    residual_df = nrow(design) - rank,
    column_names = paste(colnames(design), collapse = "|"),
    stringsAsFactors = FALSE
  )
}

direction_manifest <- function(contrast_manifest) {
  result <- do.call(rbind, lapply(seq_len(nrow(contrast_manifest)), function(i) {
    row <- contrast_manifest[i, , drop = FALSE]
    rbind(
      data.frame(
        contrast_id = row$contrast_id, deg_tier = row$deg_tier,
        supertype_id = row$supertype_id, supertype_label = row$supertype_label,
        broad_network = row$broad_network, signature_group = row$signature_group,
        deg_direction = "Dementia_up", phase18_signature_direction = "AD_up_mito",
        source_eligibility_status = row$eligibility_status,
        stringsAsFactors = FALSE
      ),
      data.frame(
        contrast_id = row$contrast_id, deg_tier = row$deg_tier,
        supertype_id = row$supertype_id, supertype_label = row$supertype_label,
        broad_network = row$broad_network, signature_group = row$signature_group,
        deg_direction = "Dementia_down", phase18_signature_direction = "AD_down_mito",
        source_eligibility_status = row$eligibility_status,
        stringsAsFactors = FALSE
      )
    )
  }))
  result$direction_slot <- seq_len(nrow(result))
  result$direction_slot_id <- paste(result$contrast_id, result$deg_direction, sep = "__")
  result[, c("direction_slot", "direction_slot_id", setdiff(names(result), c("direction_slot", "direction_slot_id")))]
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path, handlers = list(int = function(x) as.numeric(x)))
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
if (output_root != normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)) stop("Unsafe output root")
require_phase(output_root, "02_cohort", project_root)
vh06_status <- require_phase(output_root, "06_pseudobulk_qc", project_root)

output_dir <- file.path(output_root, "07_contrasts")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
profiles <- data.table::fread(file.path(output_root, "06_pseudobulk_qc/profile_manifest.tsv.gz"), data.table = FALSE)
mapping <- data.table::fread(file.path(output_root, "04_supertype_manifest/supertype_to_broad_network.tsv"), data.table = FALSE)
mapping <- mapping[order(mapping$supertype_index), ]
groups <- group_specs(config)
group_levels <- as.vector(rbind(
  paste("No_dementia", groups$signature_group, sep = "__"),
  paste("Dementia", groups$signature_group, sep = "__")
))
minimum <- as.integer(config$thresholds$min_donors_per_disease_arm)
broad_order <- unlist(config$taxonomy$broad_network_order)

fine_rows <- list()
pooled_rows <- list()
broad_grouped_rows <- list()
design_rows <- list()
column_rows <- list()
vector_rows <- list()
donor_count_rows <- list()

for (map_index in seq_len(nrow(mapping))) {
  map <- mapping[map_index, , drop = FALSE]
  all_context <- profiles[profiles$resolution == "fine_supertype" & profiles$context_id == map$supertype_id, , drop = FALSE]
  metadata <- all_context[all_context$primary_profile_eligible, , drop = FALSE]
  built <- if (nrow(metadata)) build_grouped_design(metadata, group_levels) else list(metadata = metadata, design = matrix(numeric(0), 0, 0))
  design <- built$design
  design_id <- paste("fine", map$supertype_id, "grouped", sep = "::")
  record <- design_record(design, design_id, "fine_supertype_phase18_parity", map$supertype_id, "fine_grouped_v1")
  design_rows[[length(design_rows) + 1L]] <- record
  if (ncol(design)) {
    column_rows[[length(column_rows) + 1L]] <- data.frame(
      design_id = design_id, column_order = seq_len(ncol(design)),
      design_column = colnames(design), stringsAsFactors = FALSE
    )
  }
  for (g in seq_len(nrow(groups))) {
    spec <- groups[g, ]
    counts <- table(factor(
      all_context$diagnosis[
        all_context$primary_profile_eligible & all_context$signature_group == spec$signature_group
      ],
      levels = c("Dementia", "No dementia")
    ))
    n_case <- as.integer(counts[["Dementia"]])
    n_reference <- as.integer(counts[["No dementia"]])
    support_pass <- n_case >= minimum && n_reference >= minimum
    case_column <- paste0("diagnosis_sex_apoe_groupDementia__", spec$signature_group)
    reference_column <- paste0("diagnosis_sex_apoe_groupNo_dementia__", spec$signature_group)
    coefficients_present <- all(c(case_column, reference_column) %in% colnames(design))
    full_rank <- isTRUE(record$full_rank[[1L]])
    residual_ok <- record$residual_df[[1L]] > 0
    eligible <- support_pass && coefficients_present && full_rank && residual_ok
    reason <- if (eligible) "" else if (!support_pass) "disease_arm_below_minimum" else if (!coefficients_present) "missing_required_coefficient" else if (!full_rank) "design_rank_deficient" else "nonpositive_residual_df"
    contrast_id <- paste(map$supertype_id, spec$signature_group, "Dementia_vs_No_dementia", sep = "__")
    fine_rows[[length(fine_rows) + 1L]] <- data.frame(
      contrast_id = contrast_id,
      deg_tier = "fine_supertype_phase18_parity",
      supertype_id = map$supertype_id,
      supertype_label = map$supertype_label,
      broad_network = map$broad_network,
      signature_group = spec$signature_group,
      sex = spec$sex,
      apoe_group = spec$apoe_group,
      case_phenotype = "Dementia",
      reference_phenotype = "No dementia",
      coefficient_direction = "Dementia_minus_No_dementia",
      n_case_donors = n_case,
      n_reference_donors = n_reference,
      formula_id = "fine_grouped_v1",
      design_id = design_id,
      contrast_vector_id = paste0(contrast_id, "::vector"),
      support_status = if (support_pass) "support_pass" else "support_fail",
      eligibility_status = if (eligible) "eligible" else "not_estimable",
      ineligibility_reason = reason,
      stringsAsFactors = FALSE
    )
    vector_rows[[length(vector_rows) + 1L]] <- data.frame(
      contrast_vector_id = paste0(contrast_id, "::vector"), contrast_id = contrast_id,
      design_id = design_id, coefficient = c(case_column, reference_column),
      value = c(1, -1), design_column_present = c(case_column, reference_column) %in% colnames(design),
      stringsAsFactors = FALSE
    )
    donor_count_rows[[length(donor_count_rows) + 1L]] <- data.frame(
      deg_tier = "fine_supertype_phase18_parity", context_id = map$supertype_id,
      broad_network = map$broad_network, signature_group = spec$signature_group,
      dementia_donors = n_case, no_dementia_donors = n_reference,
      stringsAsFactors = FALSE
    )
  }
}

for (network in broad_order) {
  all_context <- profiles[profiles$resolution == "direct_broad" & profiles$context_id == network, , drop = FALSE]
  metadata <- all_context[all_context$primary_profile_eligible, , drop = FALSE]

  pooled_design <- build_pooled_design(metadata)
  pooled_design_id <- paste("broad", network, "pooled", sep = "::")
  pooled_record <- design_record(pooled_design, pooled_design_id, "broad_pooled_anchor", network, "broad_pooled_v1")
  design_rows[[length(design_rows) + 1L]] <- pooled_record
  column_rows[[length(column_rows) + 1L]] <- data.frame(
    design_id = pooled_design_id, column_order = seq_len(ncol(pooled_design)),
    design_column = colnames(pooled_design), stringsAsFactors = FALSE
  )
  disease_counts <- table(factor(metadata$diagnosis, levels = c("Dementia", "No dementia")))
  n_case <- as.integer(disease_counts[["Dementia"]])
  n_reference <- as.integer(disease_counts[["No dementia"]])
  support_pass <- n_case >= minimum && n_reference >= minimum
  coefficient <- "diagnosisDementia"
  coefficient_present <- coefficient %in% colnames(pooled_design)
  eligible <- support_pass && coefficient_present && pooled_record$full_rank[[1L]] && pooled_record$residual_df[[1L]] > 0
  reason <- if (eligible) "" else if (!support_pass) "disease_arm_below_minimum" else if (!coefficient_present) "missing_required_coefficient" else if (!pooled_record$full_rank[[1L]]) "design_rank_deficient" else "nonpositive_residual_df"
  contrast_id <- paste(network, "pooled", "Dementia_vs_No_dementia", sep = "__")
  pooled_rows[[length(pooled_rows) + 1L]] <- data.frame(
    contrast_id = contrast_id, deg_tier = "broad_pooled_anchor",
    supertype_id = NA_character_, supertype_label = NA_character_, broad_network = network,
    signature_group = NA_character_, sex = NA_character_, apoe_group = NA_character_,
    case_phenotype = "Dementia", reference_phenotype = "No dementia",
    coefficient_direction = "Dementia_minus_No_dementia",
    n_case_donors = n_case, n_reference_donors = n_reference,
    formula_id = "broad_pooled_v1", design_id = pooled_design_id,
    contrast_vector_id = paste0(contrast_id, "::vector"),
    support_status = if (support_pass) "support_pass" else "support_fail",
    eligibility_status = if (eligible) "eligible" else "not_estimable",
    ineligibility_reason = reason, stringsAsFactors = FALSE
  )
  vector_rows[[length(vector_rows) + 1L]] <- data.frame(
    contrast_vector_id = paste0(contrast_id, "::vector"), contrast_id = contrast_id,
    design_id = pooled_design_id, coefficient = coefficient, value = 1,
    design_column_present = coefficient_present, stringsAsFactors = FALSE
  )
  donor_count_rows[[length(donor_count_rows) + 1L]] <- data.frame(
    deg_tier = "broad_pooled_anchor", context_id = network, broad_network = network,
    signature_group = NA_character_, dementia_donors = n_case,
    no_dementia_donors = n_reference, stringsAsFactors = FALSE
  )

  grouped <- build_grouped_design(metadata, group_levels)
  grouped_design <- grouped$design
  grouped_design_id <- paste("broad", network, "grouped", sep = "::")
  grouped_record <- design_record(grouped_design, grouped_design_id, "broad_stratified_support", network, "broad_grouped_v1")
  design_rows[[length(design_rows) + 1L]] <- grouped_record
  column_rows[[length(column_rows) + 1L]] <- data.frame(
    design_id = grouped_design_id, column_order = seq_len(ncol(grouped_design)),
    design_column = colnames(grouped_design), stringsAsFactors = FALSE
  )
  for (g in seq_len(nrow(groups))) {
    spec <- groups[g, ]
    counts <- table(factor(
      metadata$diagnosis[metadata$signature_group == spec$signature_group],
      levels = c("Dementia", "No dementia")
    ))
    n_case <- as.integer(counts[["Dementia"]])
    n_reference <- as.integer(counts[["No dementia"]])
    support_pass <- n_case >= minimum && n_reference >= minimum
    case_column <- paste0("diagnosis_sex_apoe_groupDementia__", spec$signature_group)
    reference_column <- paste0("diagnosis_sex_apoe_groupNo_dementia__", spec$signature_group)
    coefficients_present <- all(c(case_column, reference_column) %in% colnames(grouped_design))
    eligible <- support_pass && coefficients_present && grouped_record$full_rank[[1L]] && grouped_record$residual_df[[1L]] > 0
    reason <- if (eligible) "" else if (!support_pass) "disease_arm_below_minimum" else if (!coefficients_present) "missing_required_coefficient" else if (!grouped_record$full_rank[[1L]]) "design_rank_deficient" else "nonpositive_residual_df"
    contrast_id <- paste(network, spec$signature_group, "Dementia_vs_No_dementia", sep = "__")
    broad_grouped_rows[[length(broad_grouped_rows) + 1L]] <- data.frame(
      contrast_id = contrast_id, deg_tier = "broad_stratified_support",
      supertype_id = NA_character_, supertype_label = NA_character_, broad_network = network,
      signature_group = spec$signature_group, sex = spec$sex, apoe_group = spec$apoe_group,
      case_phenotype = "Dementia", reference_phenotype = "No dementia",
      coefficient_direction = "Dementia_minus_No_dementia",
      n_case_donors = n_case, n_reference_donors = n_reference,
      formula_id = "broad_grouped_v1", design_id = grouped_design_id,
      contrast_vector_id = paste0(contrast_id, "::vector"),
      support_status = if (support_pass) "support_pass" else "support_fail",
      eligibility_status = if (eligible) "eligible" else "not_estimable",
      ineligibility_reason = reason, stringsAsFactors = FALSE
    )
    vector_rows[[length(vector_rows) + 1L]] <- data.frame(
      contrast_vector_id = paste0(contrast_id, "::vector"), contrast_id = contrast_id,
      design_id = grouped_design_id, coefficient = c(case_column, reference_column),
      value = c(1, -1), design_column_present = c(case_column, reference_column) %in% colnames(grouped_design),
      stringsAsFactors = FALSE
    )
    donor_count_rows[[length(donor_count_rows) + 1L]] <- data.frame(
      deg_tier = "broad_stratified_support", context_id = network,
      broad_network = network, signature_group = spec$signature_group,
      dementia_donors = n_case, no_dementia_donors = n_reference,
      stringsAsFactors = FALSE
    )
  }
}

fine_manifest <- data.table::rbindlist(fine_rows)
fine_manifest$contrast_slot <- seq_len(nrow(fine_manifest))
fine_manifest <- fine_manifest[, c("contrast_slot", setdiff(names(fine_manifest), "contrast_slot")), with = FALSE]
pooled_manifest <- data.table::rbindlist(pooled_rows)
pooled_manifest$contrast_slot <- seq_len(nrow(pooled_manifest))
pooled_manifest <- pooled_manifest[, c("contrast_slot", setdiff(names(pooled_manifest), "contrast_slot")), with = FALSE]
broad_manifest <- data.table::rbindlist(broad_grouped_rows)
broad_manifest$contrast_slot <- seq_len(nrow(broad_manifest))
broad_manifest <- broad_manifest[, c("contrast_slot", setdiff(names(broad_manifest), "contrast_slot")), with = FALSE]
fine_directions <- direction_manifest(fine_manifest)
pooled_directions <- direction_manifest(pooled_manifest)
broad_directions <- direction_manifest(broad_manifest)
designs <- data.table::rbindlist(design_rows, use.names = TRUE)
columns <- data.table::rbindlist(column_rows, use.names = TRUE)
vectors <- data.table::rbindlist(vector_rows, use.names = TRUE)
donor_counts <- data.table::rbindlist(donor_count_rows, use.names = TRUE)

fine_support <- sum(fine_manifest$support_status == "support_pass")
fine_eligible <- sum(fine_manifest$eligibility_status == "eligible")
pooled_eligible <- sum(pooled_manifest$eligibility_status == "eligible")
broad_eligible <- sum(broad_manifest$eligibility_status == "eligible")
checks <- data.frame(
  check = c(
    "fine_contrast_rows", "fine_direction_rows", "fine_contrast_ids_unique",
    "fine_direction_ids_unique", "fine_support_reproduced",
    "all_rows_have_eligibility", "eligible_designs_full_rank_positive_df",
    "broad_pooled_rows", "broad_pooled_eligible", "broad_stratified_rows",
    "broad_stratified_eligible", "broad_stratified_not_estimable",
    "direction_mapping_exact"
  ),
  passed = c(
    nrow(fine_manifest) == as.integer(config$expected_identity$fine_contrasts),
    nrow(fine_directions) == as.integer(config$expected_identity$fine_directions),
    !anyDuplicated(fine_manifest$contrast_id), !anyDuplicated(fine_directions$direction_slot_id),
    fine_support == as.integer(config$expected_identity$fine_support_passing),
    all(fine_manifest$eligibility_status %in% c("eligible", "not_estimable")) &&
      all(pooled_manifest$eligibility_status %in% c("eligible", "not_estimable")) &&
      all(broad_manifest$eligibility_status %in% c("eligible", "not_estimable")),
    all(designs$full_rank[designs$design_id %in% c(fine_manifest$design_id[fine_manifest$eligibility_status == "eligible"], pooled_manifest$design_id[pooled_manifest$eligibility_status == "eligible"], broad_manifest$design_id[broad_manifest$eligibility_status == "eligible"])]) &&
      all(designs$residual_df[designs$design_id %in% c(fine_manifest$design_id[fine_manifest$eligibility_status == "eligible"], pooled_manifest$design_id[pooled_manifest$eligibility_status == "eligible"], broad_manifest$design_id[broad_manifest$eligibility_status == "eligible"])] > 0),
    nrow(pooled_manifest) == 7L, pooled_eligible == 7L,
    nrow(broad_manifest) == 42L,
    broad_eligible == as.integer(config$expected_identity$broad_stratified_eligible),
    sum(broad_manifest$eligibility_status == "not_estimable") == as.integer(config$expected_identity$broad_stratified_not_estimable),
    all(fine_directions$phase18_signature_direction == ifelse(fine_directions$deg_direction == "Dementia_up", "AD_up_mito", "AD_down_mito"))
  ),
  observed = c(
    nrow(fine_manifest), nrow(fine_directions), !anyDuplicated(fine_manifest$contrast_id),
    !anyDuplicated(fine_directions$direction_slot_id), fine_support, TRUE, TRUE,
    nrow(pooled_manifest), pooled_eligible, nrow(broad_manifest), broad_eligible,
    sum(broad_manifest$eligibility_status == "not_estimable"), TRUE
  ),
  expected = c(
    config$expected_identity$fine_contrasts, config$expected_identity$fine_directions,
    TRUE, TRUE, config$expected_identity$fine_support_passing, TRUE, TRUE,
    7, 7, 42, config$expected_identity$broad_stratified_eligible,
    config$expected_identity$broad_stratified_not_estimable, TRUE
  ),
  details = "",
  stringsAsFactors = FALSE
)

paths <- list(
  fine = file.path(output_dir, "fine_contrast_manifest.tsv"),
  fine_direction = file.path(output_dir, "fine_direction_manifest.tsv"),
  pooled = file.path(output_dir, "broad_pooled_contrast_manifest.tsv"),
  pooled_direction = file.path(output_dir, "broad_pooled_direction_manifest.tsv"),
  broad = file.path(output_dir, "broad_stratified_contrast_manifest.tsv"),
  broad_direction = file.path(output_dir, "broad_stratified_direction_manifest.tsv"),
  columns = file.path(output_dir, "design_columns.tsv.gz"),
  ranks = file.path(output_dir, "design_rank_checks.tsv"),
  vectors = file.path(output_dir, "contrast_vectors.tsv.gz"),
  donor_counts = file.path(output_dir, "donor_counts_by_required_group.tsv"),
  checks = file.path(output_dir, "contrast_checks.tsv"),
  artifacts = file.path(output_dir, "artifacts.tsv"),
  status = file.path(output_dir, "status.tsv")
)
atomic_fwrite(fine_manifest, paths$fine)
atomic_fwrite(fine_directions, paths$fine_direction)
atomic_fwrite(pooled_manifest, paths$pooled)
atomic_fwrite(pooled_directions, paths$pooled_direction)
atomic_fwrite(broad_manifest, paths$broad)
atomic_fwrite(broad_directions, paths$broad_direction)
atomic_fwrite(columns, paths$columns)
atomic_fwrite(designs, paths$ranks)
atomic_fwrite(vectors, paths$vectors)
atomic_fwrite(donor_counts, paths$donor_counts)
atomic_fwrite(checks, paths$checks)
write_artifacts(unlist(paths[c("fine", "fine_direction", "pooled", "pooled_direction", "broad", "broad_direction", "columns", "ranks", "vectors", "donor_counts", "checks")]), paths$artifacts, project_root)

failed <- checks$check[!checks$passed]
state <- if (length(failed)) "failed" else "validated_complete"
status <- data.frame(
  schema_version = "seaad_fine_phase_status_v2", phase = "VH07",
  validation_status = state, failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  fine_contrasts = nrow(fine_manifest), fine_directions = nrow(fine_directions),
  fine_support_passing = fine_support, fine_eligible = fine_eligible,
  broad_pooled_eligible = pooled_eligible,
  broad_stratified_eligible = broad_eligible,
  broad_stratified_not_estimable = sum(broad_manifest$eligibility_status == "not_estimable"),
  config_sha256 = sha256_file(config_path),
  vh06_status_sha256 = sha256_file(file.path(output_root, "06_pseudobulk_qc/status.tsv")),
  stringsAsFactors = FALSE
)
atomic_fwrite(status, paths$status)
cat("VH07 status: ", state, "; fine support=", fine_support, "; fine eligible=", fine_eligible, "
", sep = "")
if (length(failed)) quit(status = 2L)
