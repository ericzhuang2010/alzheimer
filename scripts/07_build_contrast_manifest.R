#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, samples = NULL,
    task_mode = "contrasts"
  )
  value_options <- c("--config", "--execution-config", "--samples", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/07_build_contrast_manifest.R --config FILE ",
        "[--execution-config FILE] [--samples TSV[,TSV...]] ",
        "[--task-mode contrasts]\n",
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
  if (!identical(out$task_mode, "contrasts")) {
    stop("--task-mode must be 'contrasts'", call. = FALSE)
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

group_label <- function(diagnosis, sex, apoe) {
  paste(diagnosis, sex, apoe, sep = "__")
}

encode_terms <- function(groups, weights) {
  paste(paste(groups, weights, sep = "="), collapse = ";")
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
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)

execution <- list(
  execution_stage = if (isTRUE(config$scope$pilot)) "local_pilot" else "minerva_production",
  execution_phase = if (isTRUE(config$scope$pilot)) 1L else 2L,
  backend = "direct", run_id = "manual_contrasts"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}

pseudobulk_dir <- file.path(output_root, "07_pseudobulk")
if (!is.null(args$samples)) {
  sample_paths <- strsplit(args$samples, ",", fixed = TRUE)[[1L]]
  sample_paths <- vapply(trimws(sample_paths), absolute_path, character(1), root = project_root)
} else {
  sample_paths <- list.files(
    pseudobulk_dir, pattern = "[.]pseudobulk_samples[.]tsv$",
    full.names = TRUE
  )
}
sample_paths <- sort(unique(sample_paths))
if (!length(sample_paths) || any(!file.exists(sample_paths))) {
  stop("No complete pseudobulk sample tables were found", call. = FALSE)
}
samples <- data.table::rbindlist(lapply(sample_paths, function(path) {
  data.table::fread(
    path, colClasses = c(projid = "character", pseudobulk_id = "character")
  )
}), fill = TRUE, use.names = TRUE)
samples <- as.data.frame(samples)
required_columns <- c(
  "rds_id", "pseudobulk_id", "projid", "cell_type_high_resolution",
  "diagnosis", "sex", "apoe_group", "nuclei", "primary_eligible"
)
missing_columns <- setdiff(required_columns, names(samples))
if (length(missing_columns)) {
  stop("Pseudobulk sample columns missing: ", paste(missing_columns, collapse = ", "), call. = FALSE)
}
if (anyDuplicated(samples$pseudobulk_id)) stop("Pseudobulk IDs must be globally unique", call. = FALSE)
samples$primary_eligible <- as_logical(samples$primary_eligible)
samples$diagnosis <- as.character(samples$diagnosis)
samples$sex <- as.character(samples$sex)
samples$apoe_group <- as.character(samples$apoe_group)
samples$group_label <- group_label(samples$diagnosis, samples$sex, samples$apoe_group)

diagnoses <- c("NCI", "AD")
sexes <- unlist(analysis$contrasts$sex_levels %||% c("Female", "Male"), use.names = FALSE)
apoe_levels <- unlist(analysis$contrasts$apoe_levels %||% c("e2", "e33", "e4"), use.names = FALSE)
minimum_donors <- as.integer(
  analysis$pseudobulk$minimum_donors_per_contrast_side %||% 5L
)
analysis_units <- unique(samples[, c("rds_id", "cell_type_high_resolution")])
analysis_units <- analysis_units[order(
  analysis_units$rds_id, analysis_units$cell_type_high_resolution
), , drop = FALSE]

definitions <- list()
add_definition <- function(family, name, kind, groups, weights = NULL, paper = FALSE) {
  definitions[[length(definitions) + 1L]] <<- list(
    family = family, name = name, kind = kind, groups = groups,
    weights = weights, paper = paper
  )
}

for (sex in sexes) {
  for (apoe in apoe_levels) {
    groups <- c(group_label("AD", sex, apoe), group_label("NCI", sex, apoe))
    add_definition(
      "AD_vs_NCI", paste("AD_vs_NCI", sex, apoe, sep = "__"),
      "single_df", groups, c(1, -1), TRUE
    )
  }
}
for (apoe in apoe_levels) {
  groups <- c(
    group_label("AD", "Female", apoe), group_label("NCI", "Female", apoe),
    group_label("AD", "Male", apoe), group_label("NCI", "Male", apoe)
  )
  add_definition(
    "sex_interaction", paste0("AD_effect_Female_minus_Male__", apoe),
    "single_df", groups, c(1, -1, -1, 1), FALSE
  )
}
for (sex in sexes) {
  for (apoe in c("e2", "e4")) {
    groups <- c(
      group_label("AD", sex, apoe), group_label("NCI", sex, apoe),
      group_label("AD", sex, "e33"), group_label("NCI", sex, "e33")
    )
    add_definition(
      "apoe_interaction", paste0("AD_effect_", apoe, "_minus_e33__", sex),
      "single_df", groups, c(1, -1, -1, 1), FALSE
    )
  }
}
all_groups <- as.vector(outer(
  as.vector(outer(diagnoses, sexes, paste, sep = "__")),
  apoe_levels, paste, sep = "__"
))
add_definition(
  "global_heterogeneity", "AD_effect_heterogeneity_across_sex_APOE",
  "multi_df", all_groups, NULL, FALSE
)

rows <- list()
for (unit_index in seq_len(nrow(analysis_units))) {
  unit <- analysis_units[unit_index, , drop = FALSE]
  unit_samples <- samples[
    samples$rds_id == unit$rds_id &
      samples$cell_type_high_resolution == unit$cell_type_high_resolution &
      samples$primary_eligible,
    , drop = FALSE
  ]
  for (definition_index in seq_along(definitions)) {
    definition <- definitions[[definition_index]]
    donor_counts <- vapply(definition$groups, function(group) {
      length(unique(unit_samples$projid[unit_samples$group_label == group]))
    }, integer(1))
    nuclei_counts <- vapply(definition$groups, function(group) {
      sum(as.numeric(unit_samples$nuclei[unit_samples$group_label == group]))
    }, numeric(1))
    eligible <- all(donor_counts >= minimum_donors)
    reason <- if (eligible) "" else paste0(
      "fewer_than_", minimum_donors, "_eligible_donors_in_required_group:",
      paste(definition$groups[donor_counts < minimum_donors], collapse = ",")
    )
    contrast_id <- paste(
      unit$rds_id, make.names(unit$cell_type_high_resolution), definition$name,
      sep = "::"
    )
    rows[[length(rows) + 1L]] <- data.frame(
      schema_version = "contrast_manifest_v1",
      manifest_row = NA_integer_, contrast_id = contrast_id,
      rds_id = unit$rds_id,
      cell_type_high_resolution = unit$cell_type_high_resolution,
      contrast_family = definition$family,
      contrast_name = definition$name,
      contrast_kind = definition$kind,
      paper_matched = definition$paper,
      contrast_terms = if (is.null(definition$weights)) "" else encode_terms(
        definition$groups, definition$weights
      ),
      required_groups = paste(definition$groups, collapse = ";"),
      group_donor_counts = paste(
        paste(definition$groups, donor_counts, sep = "="), collapse = ";"
      ),
      group_nuclei_counts = paste(
        paste(definition$groups, nuclei_counts, sep = "="), collapse = ";"
      ),
      numerator_donors = if (definition$paper) donor_counts[[1L]] else NA_integer_,
      denominator_donors = if (definition$paper) donor_counts[[2L]] else NA_integer_,
      numerator_nuclei = if (definition$paper) nuclei_counts[[1L]] else NA_real_,
      denominator_nuclei = if (definition$paper) nuclei_counts[[2L]] else NA_real_,
      minimum_donors_per_required_group = minimum_donors,
      eligibility_status = if (eligible) "eligible" else "ineligible",
      ineligibility_reason = reason,
      source_sample_files = paste(
        sub(paste0("^", project_root, "/?"), "", sample_paths), collapse = ";"
      ),
      stringsAsFactors = FALSE
    )
  }
}
contrast_manifest <- do.call(rbind, rows)
contrast_manifest$manifest_row <- seq_len(nrow(contrast_manifest))

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "contrast_manifest_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
add_check("sample_ids_unique", !anyDuplicated(samples$pseudobulk_id), anyDuplicated(samples$pseudobulk_id), 0L)
add_check("analysis_units_present", nrow(analysis_units) > 0L, nrow(analysis_units), ">0")
add_check("paper_rows_per_cell_type", sum(contrast_manifest$paper_matched) == nrow(analysis_units) * 6L, sum(contrast_manifest$paper_matched), nrow(analysis_units) * 6L)
add_check("all_rows_per_cell_type", nrow(contrast_manifest) == nrow(analysis_units) * 14L, nrow(contrast_manifest), nrow(analysis_units) * 14L)
add_check("contrast_ids_unique", !anyDuplicated(contrast_manifest$contrast_id), anyDuplicated(contrast_manifest$contrast_id), 0L)
add_check("eligibility_status_complete", all(contrast_manifest$eligibility_status %in% c("eligible", "ineligible")), paste(unique(contrast_manifest$eligibility_status), collapse = ","), "eligible;ineligible")
checks <- do.call(rbind, checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

output_dir <- file.path(output_root, "07_contrasts")
stage <- execution$execution_stage
paths <- list(
  manifest = file.path(output_dir, paste0(stage, "_contrast_manifest.tsv")),
  checks = file.path(output_dir, paste0(stage, "_contrast_manifest_checks.tsv")),
  artifacts = file.path(output_dir, paste0(stage, "_contrast_manifest_artifacts.tsv")),
  status = file.path(output_dir, paste0(stage, "_contrast_manifest_status.tsv"))
)
atomic_write_tsv(contrast_manifest, paths$manifest)
atomic_write_tsv(checks, paths$checks)
artifact_paths <- c(paths$manifest, paths$checks)
artifacts <- data.frame(
  schema_version = "contrast_manifest_artifacts_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(nrow(contrast_manifest), nrow(checks)),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "contrast_manifest_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend, run_id = execution$run_id,
  stable_task_id = "global:contrasts",
  scientific_script = "scripts/07_build_contrast_manifest.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/07_build_contrast_manifest.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  sample_table_count = length(sample_paths),
  sample_table_sha256 = paste(vapply(sample_paths, sha256_file, character(1)), collapse = ";"),
  analysis_units = nrow(analysis_units),
  paper_matched_rows = sum(contrast_manifest$paper_matched),
  interaction_rows = sum(!contrast_manifest$paper_matched),
  eligible_rows = sum(contrast_manifest$eligibility_status == "eligible"),
  ineligible_rows = sum(contrast_manifest$eligibility_status == "ineligible"),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Contrast manifest: ", paths$manifest, "\n", sep = "")
cat("Analysis units: ", nrow(analysis_units), "\n", sep = "")
cat("Paper-matched rows: ", sum(contrast_manifest$paper_matched), "\n", sep = "")
cat("Interaction rows: ", sum(!contrast_manifest$paper_matched), "\n", sep = "")
cat("Eligible rows: ", sum(contrast_manifest$eligibility_status == "eligible"), "\n", sep = "")
cat("Manifest status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
