#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/07_build_contrast_manifest.R --config FILE\n")
      quit(status = 0L)
    }
    if (key != "--config" || i == length(args)) stop("Unknown option or missing value: ", key)
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required")
  out
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, tmp, sep = "\t", na = "NA", quote = FALSE)
  if (!file.rename(tmp, path)) stop("Atomic rename failed: ", path)
}

sha256_file <- function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE)

require_status <- function(path) {
  if (!file.exists(path)) stop("Missing upstream status: ", path)
  value <- data.table::fread(path, integer64 = "double")
  if (nrow(value) != 1L || value$validation_status[[1L]] != "validated_complete") {
    stop("Upstream phase is not validated: ", path)
  }
}

serialize_contrast <- function(vector) {
  active <- vector[vector != 0]
  paste(paste0(names(active), "=", format(active, scientific = FALSE, trim = TRUE)),
        collapse = ";")
}

prepare_metadata <- function(samples) {
  samples$diagnosis <- factor(samples$diagnosis,
                              levels = c("No dementia", "Dementia"))
  samples$sex <- factor(samples$sex, levels = c("Female", "Male"))
  samples$apoe_group <- factor(samples$apoe_group, levels = c("e33", "e2", "e4"))
  samples$study <- factor(samples$study)
  samples$diagnosis_key <- ifelse(samples$diagnosis == "Dementia",
                                  "Dementia", "No_dementia")
  samples$diagnosis_sex_apoe_group <- factor(
    paste(samples$diagnosis_key, samples$sex, samples$apoe_group, sep = "__")
  )
  samples
}

make_designs <- function(metadata) {
  primary <- model.matrix(
    ~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
  secondary <- model.matrix(
    ~ 0 + diagnosis_sex_apoe_group + age_death_scaled + pmi_scaled + study,
    data = metadata
  )
  list(primary = primary, secondary = secondary)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required <- c("yaml", "data.table", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing packages: ", paste(missing, collapse = ","))

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- normalizePath(args$config, mustWork = TRUE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(file.path(invocation_root, config$project_root), mustWork = TRUE)
output_root <- normalizePath(file.path(project_root, config$output_root), mustWork = TRUE)
required_root <- normalizePath(file.path(project_root, "results/validation_human"), mustWork = TRUE)
if (!identical(output_root, required_root)) stop("Output root is not isolated validation_human")
require_status(file.path(output_root, "06_pseudobulk_qc/status.tsv"))

bundle_path <- file.path(output_root, "06_pseudobulk_qc/seaad_broad_pseudobulk.rds")
bundle <- readRDS(bundle_path)
if (!identical(bundle$schema_version, "seaad_broad_pseudobulk_v1")) stop("Unsupported VH06 bundle")
samples <- as.data.frame(bundle$samples)
contexts <- unlist(config$broad_context_order)
min_arm <- as.integer(config$thresholds$min_donors_per_disease_arm)
sexes <- c("Female", "Male")
apoes <- c("e2", "e33", "e4")

manifest_rows <- list()
design_column_rows <- list()
rank_rows <- list()
donor_count_rows <- list()
row_index <- 0L

for (context in contexts) {
  metadata <- samples[samples$context == context & samples$primary_eligible, , drop = FALSE]
  metadata <- prepare_metadata(metadata)
  designs <- make_designs(metadata)
  primary_rank <- qr(designs$primary)$rank
  secondary_rank <- qr(designs$secondary)$rank
  primary_full <- primary_rank == ncol(designs$primary)
  secondary_full <- secondary_rank == ncol(designs$secondary)

  for (model_name in names(designs)) {
    design <- designs[[model_name]]
    design_column_rows[[length(design_column_rows) + 1L]] <- data.frame(
      context = context,
      model = model_name,
      column_index = seq_len(ncol(design)),
      column_name = colnames(design)
    )
  }
  rank_rows[[length(rank_rows) + 1L]] <- data.frame(
    context = context,
    model = c("primary", "secondary"),
    samples = nrow(metadata),
    columns = c(ncol(designs$primary), ncol(designs$secondary)),
    rank = c(primary_rank, secondary_rank),
    full_rank = c(primary_full, secondary_full)
  )

  counts <- aggregate(
    donor_id ~ diagnosis + sex + apoe_group,
    data = metadata,
    FUN = function(x) length(unique(x)),
    drop = FALSE
  )
  names(counts)[names(counts) == "donor_id"] <- "donors"
  counts$context <- context
  donor_count_rows[[length(donor_count_rows) + 1L]] <- counts

  primary_arms <- table(metadata$diagnosis)
  n_no <- as.integer(primary_arms["No dementia"])
  n_dem <- as.integer(primary_arms["Dementia"])
  primary_reason <- if (!primary_full) "primary_design_rank_deficient" else if (
    min(n_no, n_dem) < min_arm
  ) paste0("disease_arm_below_", min_arm) else ""
  primary_status <- if (nzchar(primary_reason)) "not_estimable" else "eligible"
  primary_vector <- setNames(numeric(ncol(designs$primary)), colnames(designs$primary))
  if ("diagnosisDementia" %in% names(primary_vector)) {
    primary_vector["diagnosisDementia"] <- 1
  } else {
    primary_status <- "not_estimable"
    primary_reason <- "diagnosisDementia_coefficient_absent"
  }
  row_index <- row_index + 1L
  manifest_rows[[length(manifest_rows) + 1L]] <- data.frame(
    slot = row_index,
    contrast_id = paste0(context, "__primary__Dementia_vs_No_dementia"),
    context = context,
    contrast_family = "primary",
    sex = NA_character_,
    apoe_group = NA_character_,
    contrast_name = "Dementia_vs_No_dementia",
    output_basename = paste0(context, "__Dementia_vs_No_dementia.tsv.gz"),
    eligibility_status = primary_status,
    ineligibility_reason = primary_reason,
    dementia_donors = n_dem,
    no_dementia_donors = n_no,
    design_model = "primary",
    coefficient_vector = serialize_contrast(primary_vector),
    stringsAsFactors = FALSE
  )

  for (sex_value in sexes) {
    for (apoe_value in apoes) {
      arm <- metadata[
        as.character(metadata$sex) == sex_value &
          as.character(metadata$apoe_group) == apoe_value, , drop = FALSE
      ]
      arm_table <- table(arm$diagnosis)
      arm_no <- if ("No dementia" %in% names(arm_table)) as.integer(arm_table["No dementia"]) else 0L
      arm_dem <- if ("Dementia" %in% names(arm_table)) as.integer(arm_table["Dementia"]) else 0L
      positive <- paste0("diagnosis_sex_apoe_groupDementia__", sex_value, "__", apoe_value)
      negative <- paste0("diagnosis_sex_apoe_groupNo_dementia__", sex_value, "__", apoe_value)
      reason <- ""
      if (min(arm_no, arm_dem) < min_arm) {
        reason <- paste0("disease_arm_below_", min_arm)
      } else if (!secondary_full) {
        reason <- "secondary_design_rank_deficient"
      } else if (!all(c(positive, negative) %in% colnames(designs$secondary))) {
        reason <- "required_group_coefficient_absent"
      }
      status <- if (nzchar(reason)) "not_estimable" else "eligible"
      vector <- setNames(numeric(ncol(designs$secondary)), colnames(designs$secondary))
      if (all(c(positive, negative) %in% names(vector))) {
        vector[positive] <- 1
        vector[negative] <- -1
      }
      row_index <- row_index + 1L
      manifest_rows[[length(manifest_rows) + 1L]] <- data.frame(
        slot = row_index,
        contrast_id = paste0(context, "__secondary__", sex_value, "__", apoe_value,
                             "__Dementia_vs_No_dementia"),
        context = context,
        contrast_family = "secondary",
        sex = sex_value,
        apoe_group = apoe_value,
        contrast_name = "Dementia_vs_No_dementia",
        output_basename = paste0(context, "__", sex_value, "__", apoe_value,
                                 "__Dementia_vs_No_dementia.tsv.gz"),
        eligibility_status = status,
        ineligibility_reason = reason,
        dementia_donors = arm_dem,
        no_dementia_donors = arm_no,
        design_model = "secondary",
        coefficient_vector = serialize_contrast(vector),
        stringsAsFactors = FALSE
      )
    }
  }
}

manifest <- do.call(rbind, manifest_rows)
design_columns <- do.call(rbind, design_column_rows)
rank_checks <- do.call(rbind, rank_rows)
donor_counts <- do.call(rbind, donor_count_rows)
eligibility <- manifest[, c(
  "slot", "contrast_id", "context", "contrast_family", "sex", "apoe_group",
  "eligibility_status", "ineligibility_reason", "dementia_donors",
  "no_dementia_donors"
)]

primary_eligible <- sum(
  manifest$contrast_family == "primary" & manifest$eligibility_status == "eligible"
)
secondary_eligible <- sum(
  manifest$contrast_family == "secondary" & manifest$eligibility_status == "eligible"
)
secondary_not_estimable <- sum(
  manifest$contrast_family == "secondary" &
    manifest$eligibility_status == "not_estimable"
)
eligible_arm_ok <- all(
  manifest$dementia_donors[manifest$eligibility_status == "eligible"] >= min_arm &
    manifest$no_dementia_donors[manifest$eligibility_status == "eligible"] >= min_arm
)

checks <- data.frame(
  check = c(
    "manifest_slots", "unique_contrast_ids", "primary_slots",
    "secondary_slots", "primary_eligible", "secondary_eligible_expected",
    "secondary_not_estimable_expected", "all_primary_designs_full_rank",
    "eligible_arm_thresholds", "eligibility_status_complete"
  ),
  passed = c(
    nrow(manifest) == 49L, !anyDuplicated(manifest$contrast_id),
    sum(manifest$contrast_family == "primary") == config$expected$primary_contrasts,
    sum(manifest$contrast_family == "secondary") == config$expected$secondary_slots,
    primary_eligible == config$expected$primary_contrasts,
    secondary_eligible == config$expected$secondary_eligible,
    secondary_not_estimable == config$expected$secondary_not_estimable,
    all(rank_checks$full_rank[rank_checks$model == "primary"]),
    eligible_arm_ok,
    all(manifest$eligibility_status %in% c("eligible", "not_estimable"))
  ),
  observed = c(
    nrow(manifest), !anyDuplicated(manifest$contrast_id),
    sum(manifest$contrast_family == "primary"),
    sum(manifest$contrast_family == "secondary"), primary_eligible,
    secondary_eligible, secondary_not_estimable,
    sum(rank_checks$full_rank[rank_checks$model == "primary"]),
    eligible_arm_ok, paste(unique(manifest$eligibility_status), collapse = ";")
  ),
  expected = c(
    49, TRUE, config$expected$primary_contrasts, config$expected$secondary_slots,
    config$expected$primary_contrasts, config$expected$secondary_eligible,
    config$expected$secondary_not_estimable, length(contexts), TRUE,
    "eligible;not_estimable"
  ),
  details = "",
  stringsAsFactors = FALSE
)

output_dir <- file.path(output_root, "07_contrasts")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
paths <- list(
  manifest = file.path(output_dir, "contrast_manifest.tsv"),
  eligibility = file.path(output_dir, "contrast_eligibility.tsv"),
  columns = file.path(output_dir, "design_columns.tsv"),
  ranks = file.path(output_dir, "design_rank_checks.tsv"),
  counts = file.path(output_dir, "donor_counts_by_required_group.tsv"),
  checks = file.path(output_dir, "contrast_checks.tsv"),
  status = file.path(output_dir, "status.tsv")
)
atomic_fwrite(manifest, paths$manifest)
atomic_fwrite(eligibility, paths$eligibility)
atomic_fwrite(design_columns, paths$columns)
atomic_fwrite(rank_checks, paths$ranks)
atomic_fwrite(donor_counts, paths$counts)
atomic_fwrite(checks, paths$checks)

failed <- checks$check[!checks$passed]
validation_status <- if (length(failed)) "failed" else "validated_complete"
status <- data.frame(
  schema_version = "seaad_phase_status_v1",
  phase = "VH07",
  validation_status = validation_status,
  failed_checks = paste(failed, collapse = ";"),
  started_at_utc = format(started_at, tz = "UTC", usetz = TRUE),
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  total_slots = nrow(manifest),
  primary_eligible = primary_eligible,
  secondary_eligible = secondary_eligible,
  secondary_not_estimable = secondary_not_estimable,
  manifest_sha256 = sha256_file(paths$manifest),
  config_sha256 = sha256_file(config_path),
  stringsAsFactors = FALSE
)
atomic_fwrite(status, paths$status)
cat("VH07 status: ", validation_status, "; primary=", primary_eligible,
    "; secondary=", secondary_eligible, "\n", sep = "")
if (length(failed)) quit(status = 2L)
