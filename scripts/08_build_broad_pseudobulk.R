#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/lib/phase08_broad_deg_common.R"), local = FALSE)

args <- phase08_parse_cli(
  commandArgs(trailingOnly = TRUE), allow = c("--preflight", "--resume")
)
if (isTRUE(args$help)) {
  cat(
    "Usage: Rscript scripts/08_build_broad_pseudobulk.R ",
    "[--config FILE] [--profile local_pilot|minerva_production] ",
    "[--preflight] [--resume]\n",
    sep = ""
  )
  quit(status = 0L)
}

context <- phase08_load_context(args$config, args$profile, include_model = FALSE)
analysis <- context$config$analysis
profile_mapping <- context$mapping[
  context$mapping$expected_rds_id %in% context$source_ids, , drop = FALSE
]
phase08_assert(
  nrow(profile_mapping) == as.integer(context$profile$expected_fine_types_observed),
  "Profile mapping row count disagrees with its frozen expectation"
)
phase08_assert(
  setequal(unique(profile_mapping$expected_rds_id), context$source_ids),
  "Profile mapping does not cover every source RDS"
)
phase08_assert(
  setequal(unique(profile_mapping$broad_cell_type[profile_mapping$include]), context$broad_types),
  "Included mapping does not cover exactly the requested broad cells"
)

input_rows <- list()
for (rds_id in context$source_ids) {
  info <- phase08_validate_source_bundle(context, rds_id, read_bundle = FALSE)
  input_rows[[length(input_rows) + 1L]] <- data.frame(
    schema_version = "broad_deg_input_authority_v1",
    rds_id = rds_id,
    bundle_path = phase08_relative_path(info$bundle_path, context$project_root),
    bundle_bytes = as.numeric(file.info(info$bundle_path)$size),
    bundle_sha256 = info$bundle_sha256,
    status_path = phase08_relative_path(info$status_path, context$project_root),
    status_sha256 = info$status_sha256,
    stringsAsFactors = FALSE
  )
}
input_authority <- do.call(rbind, input_rows)
input_signature <- paste(input_authority$bundle_sha256, collapse = ";")

if (isTRUE(args$preflight)) {
  cat("Phase 08 broad preflight passed\n")
  cat("Profile: ", context$profile_name, "\n", sep = "")
  cat("Source bundles: ", nrow(input_authority), "\n", sep = "")
  cat("Observed/frozen fine types: ", nrow(profile_mapping), "\n", sep = "")
  cat("Included fine types: ", sum(profile_mapping$include), "\n", sep = "")
  cat("Explicit exclusions: ", sum(!profile_mapping$include), "\n", sep = "")
  cat("Broad cells: ", paste(context$broad_types, collapse = ", "), "\n", sep = "")
  cat(
    "Structural contrasts: ",
    length(context$broad_types) * nrow(phase08_group_rows(context$config)),
    "\n", sep = ""
  )
  quit(status = 0L)
}

input_dir <- file.path(context$output_root, "00_inputs")
shard_dir <- file.path(context$output_root, "01_pseudobulk_shards")
broad_dir <- file.path(context$output_root, "02_broad_pseudobulk")
dir.create(input_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(shard_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(broad_dir, recursive = TRUE, showWarnings = FALSE)

stage_status_path <- file.path(broad_dir, "broad_pseudobulk_stage_status.tsv")
if (isTRUE(args$resume) && file.exists(stage_status_path)) {
  old_status <- data.table::fread(stage_status_path, data.table = FALSE)
  expected_broad_paths <- file.path(
    broad_dir, paste0(context$broad_types, ".broad_pseudobulk_counts.rds")
  )
  current <- nrow(old_status) == 1L &&
    identical(old_status$validation_status[[1L]], "validated_complete") &&
    identical(old_status$config_sha256[[1L]], phase08_sha256_file(context$config_path)) &&
    identical(old_status$mapping_sha256[[1L]], phase08_sha256_file(context$mapping_path)) &&
    identical(old_status$source_bundle_signature[[1L]], input_signature) &&
    identical(old_status$scientific_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/08_build_broad_pseudobulk.R")
    )) &&
    identical(old_status$helper_script_sha256[[1L]], phase08_sha256_file(
      file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
    )) &&
    all(file.exists(expected_broad_paths))
  if (isTRUE(current)) {
    cat("Broad pseudobulk stage is current; resume skipped rebuild\n")
    quit(status = 0L)
  }
}

phase08_atomic_copy(
  context$config_path,
  file.path(input_dir, "phase08_broad_deg_config_snapshot.yml")
)
phase08_atomic_copy(
  context$mapping_path,
  file.path(input_dir, "broad_cell_mapping.tsv")
)
phase08_atomic_write_tsv(
  input_authority,
  file.path(input_dir, "phase07_pseudobulk_input_authority.tsv")
)

shards <- list()
conservation_rows <- list()
fine_composition_rows <- list()
for (rds_id in context$source_ids) {
  message("Reading and aggregating Phase 07 bundle: ", rds_id)
  info <- phase08_validate_source_bundle(context, rds_id, read_bundle = TRUE)
  source_samples <- as.data.frame(info$bundle$samples)
  source_map <- context$mapping[
    context$mapping$expected_rds_id == rds_id, , drop = FALSE
  ]
  source_map_index <- match(
    source_samples$cell_type_high_resolution, source_map$fine_cell_type
  )
  phase08_assert(!anyNA(source_map_index), paste("Unmapped source fine type in", rds_id))
  source_samples$broad_cell_type <- source_map$broad_cell_type[source_map_index]
  source_samples$mapping_include <- source_map$include[source_map_index]
  composition_selected <- source_samples$mapping_include &
    source_samples$broad_cell_type %in% context$broad_types
  composition_selected[is.na(composition_selected)] <- FALSE
  fine_composition_rows[[length(fine_composition_rows) + 1L]] <- source_samples[
    composition_selected,
    c(
      "projid", "diagnosis", "sex", "apoe_group", "broad_cell_type",
      "cell_type_high_resolution", "nuclei"
    ),
    drop = FALSE
  ]
  shard <- phase08_aggregate_source_bundle(
    info$bundle, context$mapping, context$broad_types, analysis
  )
  shard$source_bundle_path <- phase08_relative_path(info$bundle_path, context$project_root)
  shard$source_bundle_sha256 <- info$bundle_sha256
  shard_path <- file.path(shard_dir, paste0(rds_id, ".broad_pseudobulk_shard.rds"))
  phase08_atomic_save_rds(shard, shard_path)
  conservation_rows[[length(conservation_rows) + 1L]] <- data.frame(
    schema_version = "broad_pseudobulk_count_conservation_v1",
    level = "source_shard", source_id = rds_id,
    broad_cell_type = paste(sort(unique(shard$samples$broad_cell_type)), collapse = ";"),
    source_columns = as.integer(shard$source_selected_columns),
    output_columns = as.integer(ncol(shard$counts)),
    source_total_counts = as.numeric(shard$source_selected_total_counts),
    output_total_counts = as.numeric(shard$aggregate_total_counts),
    difference = as.numeric(shard$aggregate_total_counts - shard$source_selected_total_counts),
    passed = identical(
      as.numeric(shard$source_selected_total_counts),
      as.numeric(shard$aggregate_total_counts)
    ),
    stringsAsFactors = FALSE
  )
  shards[[rds_id]] <- shard
  rm(info)
  invisible(gc())
}

broad_bundles <- phase08_combine_shards(shards, context$broad_types, analysis)
all_samples <- list()
for (broad in context$broad_types) {
  bundle <- broad_bundles[[broad]]
  bundle$profile <- context$profile_name
  bundle$source_bundle_signature <- input_signature
  bundle$config_sha256 <- phase08_sha256_file(context$config_path)
  bundle$mapping_sha256 <- phase08_sha256_file(context$mapping_path)
  output_path <- file.path(broad_dir, paste0(broad, ".broad_pseudobulk_counts.rds"))
  phase08_atomic_save_rds(bundle, output_path)
  all_samples[[length(all_samples) + 1L]] <- bundle$samples
  source_total <- sum(vapply(
    shards,
    function(shard) {
      idx <- shard$samples$broad_cell_type == broad
      if (!any(idx)) return(0)
      sum(as.numeric(Matrix::colSums(shard$counts[, idx, drop = FALSE])))
    }, numeric(1)
  ))
  output_total <- sum(as.numeric(Matrix::colSums(bundle$counts)))
  conservation_rows[[length(conservation_rows) + 1L]] <- data.frame(
    schema_version = "broad_pseudobulk_count_conservation_v1",
    level = "final_broad", source_id = paste(bundle$source_rds_ids, collapse = ";"),
    broad_cell_type = broad,
    source_columns = as.integer(sum(vapply(
      shards, function(shard) sum(shard$samples$broad_cell_type == broad), integer(1)
    ))),
    output_columns = as.integer(ncol(bundle$counts)),
    source_total_counts = as.numeric(source_total),
    output_total_counts = as.numeric(output_total),
    difference = as.numeric(output_total - source_total),
    passed = identical(as.numeric(source_total), as.numeric(output_total)),
    stringsAsFactors = FALSE
  )
}
samples <- do.call(rbind, all_samples)
samples <- samples[order(
  match(samples$broad_cell_type, context$broad_types), samples$projid
), , drop = FALSE]
row.names(samples) <- NULL
conservation <- do.call(rbind, conservation_rows)

fine_composition <- do.call(rbind, fine_composition_rows)
fine_composition <- data.table::as.data.table(fine_composition)
fine_composition <- fine_composition[, .(
  diagnosis = phase08_single_value(diagnosis, "composition diagnosis"),
  sex = phase08_single_value(sex, "composition sex"),
  apoe_group = phase08_single_value(apoe_group, "composition apoe_group"),
  fine_type_nuclei = as.integer(sum(as.numeric(nuclei)))
), by = .(projid, broad_cell_type, fine_cell_type = cell_type_high_resolution)]
broad_nuclei <- data.table::as.data.table(samples)[, .(
  broad_nuclei = as.integer(phase08_single_value(nuclei, "broad nuclei"))
), by = .(projid, broad_cell_type)]
fine_composition <- merge(
  fine_composition, broad_nuclei,
  by = c("projid", "broad_cell_type"), all.x = TRUE, sort = FALSE
)
phase08_assert(!anyNA(fine_composition$broad_nuclei),
               "Fine composition rows do not map to broad samples")
fine_composition[, fine_type_proportion := fine_type_nuclei / broad_nuclei]
composition_sums <- fine_composition[, .(observed = sum(fine_type_nuclei)),
                                     by = .(projid, broad_cell_type)]
composition_sums <- merge(
  composition_sums, broad_nuclei,
  by = c("projid", "broad_cell_type"), all.x = TRUE, sort = FALSE
)
phase08_assert(all(composition_sums$observed == composition_sums$broad_nuclei),
               "Fine-type composition nuclei do not conserve broad nuclei")
data.table::setorder(fine_composition, broad_cell_type, projid, fine_cell_type)
fine_composition <- as.data.frame(fine_composition)

samples_path <- file.path(broad_dir, "broad_pseudobulk_samples.tsv.gz")
conservation_path <- file.path(broad_dir, "broad_pseudobulk_count_conservation.tsv.gz")
composition_path <- file.path(broad_dir, "broad_fine_type_composition.tsv.gz")
phase08_atomic_write_tsv_gz(samples, samples_path)
phase08_atomic_write_tsv_gz(conservation, conservation_path)
phase08_atomic_write_tsv_gz(fine_composition, composition_path)

checks <- data.frame(
  schema_version = "broad_pseudobulk_stage_checks_v1",
  check = c(
    "source_bundle_count", "frozen_fine_type_count", "included_broad_types",
    "sample_ids_unique", "one_sample_per_donor_broad", "all_conservation_passed",
    "primary_eligibility_recomputed", "fine_composition_conserves_broad_nuclei"
  ),
  passed = c(
    nrow(input_authority) == as.integer(context$profile$expected_source_bundles),
    nrow(profile_mapping) == as.integer(context$profile$expected_fine_types_observed),
    setequal(unique(samples$broad_cell_type), context$broad_types),
    !anyDuplicated(samples$broad_pseudobulk_id),
    !anyDuplicated(paste(samples$projid, samples$broad_cell_type, sep = "\r")),
    all(conservation$passed),
    identical(
      phase08_as_logical(samples$primary_eligible),
      samples$nuclei >= as.integer(analysis$minimum_nuclei_primary)
    ),
    all(composition_sums$observed == composition_sums$broad_nuclei)
  ),
  observed = c(
    nrow(input_authority), nrow(profile_mapping), length(unique(samples$broad_cell_type)),
    anyDuplicated(samples$broad_pseudobulk_id),
    anyDuplicated(paste(samples$projid, samples$broad_cell_type, sep = "\r")),
    sum(!conservation$passed),
    sum(phase08_as_logical(samples$primary_eligible)),
    sum(composition_sums$observed != composition_sums$broad_nuclei)
  ),
  expected = c(
    context$profile$expected_source_bundles,
    context$profile$expected_fine_types_observed,
    context$profile$expected_broad_types, 0, 0, 0,
    sum(samples$nuclei >= as.integer(analysis$minimum_nuclei_primary)), 0
  ),
  stringsAsFactors = FALSE
)
checks_path <- file.path(broad_dir, "broad_pseudobulk_stage_checks.tsv")
phase08_atomic_write_tsv(checks, checks_path)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

status <- data.frame(
  schema_version = "broad_pseudobulk_stage_status_v1",
  profile = context$profile_name,
  execution_stage = context$profile$execution_stage,
  execution_phase = as.integer(context$profile$execution_phase),
  run_id = context$profile$run_id,
  source_bundles = nrow(input_authority),
  frozen_fine_types = nrow(profile_mapping),
  included_fine_types = sum(profile_mapping$include),
  explicitly_excluded_fine_types = sum(!profile_mapping$include),
  broad_cell_types = length(context$broad_types),
  donor_broad_samples = nrow(samples),
  primary_eligible_samples = sum(phase08_as_logical(samples$primary_eligible)),
  config_sha256 = phase08_sha256_file(context$config_path),
  mapping_sha256 = phase08_sha256_file(context$mapping_path),
  source_bundle_signature = input_signature,
  scientific_script = "scripts/08_build_broad_pseudobulk.R",
  scientific_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/08_build_broad_pseudobulk.R")
  ),
  helper_script_sha256 = phase08_sha256_file(
    file.path(context$project_root, "scripts/lib/phase08_broad_deg_common.R")
  ),
  peak_ram_gib = phase08_peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = phase08_git_revision(context$project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
phase08_atomic_write_tsv(status, stage_status_path)

cat("Broad pseudobulk output: ", broad_dir, "\n", sep = "")
cat("Broad cells: ", length(context$broad_types), "\n", sep = "")
cat("Donor-broad samples: ", nrow(samples), "\n", sep = "")
cat("Validation status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) quit(status = 2L)
