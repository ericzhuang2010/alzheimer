#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

started_at <- Sys.time()
`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL,
    execution_config = NULL,
    audit = NULL,
    task_mode = "cohort"
  )
  value_options <- c("--config", "--execution-config", "--audit", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/02_build_cohort.R --config FILE ",
        "[--execution-config FILE] [--audit FILE] [--task-mode cohort]\n",
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
  if (!identical(out$task_mode, "cohort")) {
    stop("--task-mode must be 'cohort'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

normalize_projid <- function(x, width) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "NaN")] <- NA_character_
  valid <- !is.na(x)
  x[valid] <- vapply(x[valid], function(value) {
    if (grepl("^[0-9]+$", value) && nchar(value) < width) {
      paste0(strrep("0", width - nchar(value)), value)
    } else {
      value
    }
  }, character(1))
  x
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(
    x, tmp, sep = "\t", quote = FALSE, row.names = FALSE,
    col.names = TRUE, na = "NA"
  )
  if (!file.rename(tmp, path)) {
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2(
    "sha256sum", path, stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    return(NA_character_)
  }
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
    return("unborn_or_non_git_repository")
  }
  result[[1L]]
}

as_numeric_clean <- function(x) {
  suppressWarnings(as.numeric(trimws(as.character(x))))
}

scale_checked <- function(x, name) {
  value <- stats::sd(x)
  if (!is.finite(value) || value == 0) {
    stop("Cannot scale constant or invalid covariate: ", name, call. = FALSE)
  }
  (x - mean(x)) / value
}

make_group_counts <- function(cohort, scope, rds_id = NA_character_) {
  sex_levels <- c("Female", "Male")
  apoe_levels <- c("e2", "e33", "e4")
  diagnosis_levels <- c("NCI", "AD")
  grid <- expand.grid(
    diagnosis = diagnosis_levels,
    apoe_group = apoe_levels,
    sex = sex_levels,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  )
  keys <- paste(cohort$diagnosis, cohort$apoe_group, cohort$sex, sep = "\r")
  grid_keys <- paste(grid$diagnosis, grid$apoe_group, grid$sex, sep = "\r")
  counts <- table(factor(keys, levels = grid_keys))
  data.frame(
    schema_version = "cohort_group_counts_v1",
    scope = scope,
    rds_id = rds_id,
    sex = grid$sex,
    apoe_group = grid$apoe_group,
    diagnosis = grid$diagnosis,
    donors = as.integer(counts),
    stringsAsFactors = FALSE
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table")
missing_packages <- required_packages[!vapply(
  required_packages, requireNamespace, logical(1), quietly = TRUE
)]
if (length(missing_packages)) {
  stop(
    "Missing required packages: ", paste(missing_packages, collapse = ", "),
    call. = FALSE
  )
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, invocation_root)
if (!file.exists(config_path)) {
  stop("Config does not exist: ", config_path, call. = FALSE)
}
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", invocation_root),
  mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
clinical_path <- absolute_path(config$inputs$clinical_csv, project_root)
metadata_path <- absolute_path(config$inputs$cell_metadata_tsv, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
for (path in c(analysis_path, manifest_path, clinical_path, metadata_path)) {
  if (!file.exists(path)) stop("Required input does not exist: ", path, call. = FALSE)
}
analysis <- yaml::read_yaml(analysis_path)
cohort_parameters <- analysis$cohort
join_key <- cohort_parameters$join_key %||% "projid"
projid_width <- as.integer(cohort_parameters$projid_width %||% 8L)

cohort_dir <- file.path(output_root, "02_cohort")
dir.create(cohort_dir, recursive = TRUE, showWarnings = FALSE)
global_path <- file.path(cohort_dir, "global_cohort_276.tsv")
flow_path <- file.path(cohort_dir, "cohort_exclusion_flow.tsv")
groups_path <- file.path(cohort_dir, "cohort_group_counts.tsv")
intersections_path <- file.path(cohort_dir, "cohort_rds_intersections.tsv")
sex_check_path <- file.path(cohort_dir, "sex_linked_expression_check.tsv")
checks_path <- file.path(cohort_dir, "cohort_checks.tsv")
status_path <- file.path(cohort_dir, "cohort_status.tsv")

audit_paths <- if (!is.null(args$audit)) {
  absolute_path(args$audit, project_root)
} else {
  list.files(
    file.path(output_root, "01_audit"),
    pattern = "[.]audit[.]tsv$",
    full.names = TRUE
  )
}
audit_paths <- sort(unique(audit_paths))
if (!length(audit_paths) || any(!file.exists(audit_paths))) {
  stop(
    "No readable audit summaries were found. Run Scientific Phase A first.",
    call. = FALSE
  )
}
audits <- lapply(audit_paths, function(path) {
  x <- data.table::fread(path, data.table = FALSE)
  if (nrow(x) != 1L) stop("Audit summary must contain one row: ", path, call. = FALSE)
  if (!identical(x$validation_status[[1L]], "validated_complete")) {
    stop("Audit is not validated_complete: ", path, call. = FALSE)
  }
  x$audit_path <- path
  x$donors_path <- sub("[.]audit[.]tsv$", ".donors.tsv", path)
  if (!file.exists(x$donors_path[[1L]])) {
    stop(
      "Required donor inventory is missing: ", x$donors_path[[1L]],
      ". Rerun Scientific Phase A with the promoted audit script.",
      call. = FALSE
    )
  }
  x
})
audit_table <- data.table::rbindlist(audits, fill = TRUE)
if (anyDuplicated(audit_table$rds_id)) {
  stop("Audit inputs contain duplicate rds_id values", call. = FALSE)
}

clinical <- data.table::fread(
  clinical_path,
  colClasses = setNames("character", join_key),
  na.strings = c("", "NA"),
  data.table = FALSE
)
metadata <- data.table::fread(
  metadata_path,
  select = join_key,
  colClasses = setNames("character", join_key),
  na.strings = c("", "NA"),
  data.table = FALSE
)
if (!join_key %in% names(clinical) || !join_key %in% names(metadata)) {
  stop("Join key is missing from a required input: ", join_key, call. = FALSE)
}
clinical[[join_key]] <- normalize_projid(clinical[[join_key]], projid_width)
metadata[[join_key]] <- normalize_projid(metadata[[join_key]], projid_width)
if (anyNA(metadata[[join_key]])) {
  stop("Master cell metadata contains missing projid values", call. = FALSE)
}
if (anyDuplicated(clinical[[join_key]])) {
  duplicate_ids <- unique(clinical[[join_key]][duplicated(clinical[[join_key]])])
  stop(
    "Clinical data contain duplicate normalized projid values: ",
    paste(duplicate_ids, collapse = ", "),
    call. = FALSE
  )
}

metadata_donors <- sort(unique(metadata[[join_key]]))
matched_index <- match(metadata_donors, clinical[[join_key]])
if (anyNA(matched_index)) {
  stop(
    "Clinical rows are missing for metadata donors: ",
    paste(metadata_donors[is.na(matched_index)], collapse = ", "),
    call. = FALSE
  )
}
joined <- clinical[matched_index, , drop = FALSE]
stopifnot(identical(joined[[join_key]], metadata_donors))

diagnosis_field <- cohort_parameters$diagnosis_field
sex_field <- cohort_parameters$sex_field
apoe_field <- cohort_parameters$apoe_field
pmi_field <- cohort_parameters$pmi_field
required_fields <- c(
  join_key, diagnosis_field, sex_field, apoe_field, pmi_field, "age_death"
)
missing_fields <- setdiff(required_fields, names(joined))
if (length(missing_fields)) {
  stop(
    "Clinical input lacks required fields: ",
    paste(missing_fields, collapse = ", "),
    call. = FALSE
  )
}

diagnosis_value <- as_numeric_clean(joined[[diagnosis_field]])
sex_value <- as_numeric_clean(joined[[sex_field]])
apoe_value <- as_numeric_clean(joined[[apoe_field]])
pmi_value <- as_numeric_clean(joined[[pmi_field]])
age_raw <- trimws(as.character(joined$age_death))
age_numeric <- suppressWarnings(as.numeric(sub("[+]$", "", age_raw)))
age_90plus <- grepl("[+]$", age_raw)

active <- rep(TRUE, nrow(joined))
flow_rows <- list()
record_flow <- function(step, rule, keep) {
  before <- sum(active)
  excluded <- sum(active & !keep)
  active <<- active & keep
  flow_rows[[length(flow_rows) + 1L]] <<- data.frame(
    schema_version = "cohort_exclusion_flow_v1",
    step = step,
    rule = rule,
    donors_before = before,
    donors_excluded = excluded,
    donors_remaining = sum(active),
    stringsAsFactors = FALSE
  )
}
record_flow(1L, "represented_in_master_cell_metadata", rep(TRUE, nrow(joined)))
record_flow(
  2L, "retain_NCI_or_AD",
  diagnosis_value %in% c(
    as.numeric(unlist(cohort_parameters$nci_values)),
    as.numeric(unlist(cohort_parameters$ad_values))
  )
)
record_flow(
  3L, "exclude_prespecified_sex_discordant",
  !joined[[join_key]] %in% unlist(
    cohort_parameters$excluded_sex_discordant_projids,
    use.names = FALSE
  )
)
record_flow(
  4L, "exclude_APOE_e2_e4",
  is.na(apoe_value) | !apoe_value %in% as.numeric(unlist(
    cohort_parameters$excluded_apoe_values
  ))
)
record_flow(5L, "require_APOE_genotype", !is.na(apoe_value))
record_flow(6L, "require_PMI", !is.na(pmi_value))
record_flow(
  7L, "require_age_at_death_and_valid_sex",
  !is.na(age_numeric) &
    sex_value %in% c(
      as.numeric(cohort_parameters$female_value),
      as.numeric(cohort_parameters$male_value)
    )
)
exclusion_flow <- do.call(rbind, flow_rows)

cohort <- joined[active, , drop = FALSE]
cohort$diagnosis <- ifelse(
  diagnosis_value[active] %in% as.numeric(unlist(cohort_parameters$nci_values)),
  "NCI", "AD"
)
cohort$sex <- ifelse(
  sex_value[active] == as.numeric(cohort_parameters$female_value),
  "Female", "Male"
)
eligible_apoe <- apoe_value[active]
cohort$apoe_group <- ifelse(
  eligible_apoe %in% as.numeric(unlist(cohort_parameters$apoe_e2_values)),
  "e2",
  ifelse(
    eligible_apoe %in% as.numeric(unlist(cohort_parameters$apoe_e33_values)),
    "e33",
    ifelse(
      eligible_apoe %in% as.numeric(unlist(cohort_parameters$apoe_e4_values)),
      "e4", NA_character_
    )
  )
)
cohort$age_death_numeric <- age_numeric[active]
cohort$age_90plus <- age_90plus[active]
cohort$pmi_numeric <- pmi_value[active]
cohort$pmi_log1p <- log1p(cohort$pmi_numeric)
cohort$age_death_scaled <- scale_checked(
  cohort$age_death_numeric, "age_death_numeric"
)
cohort$pmi_scaled <- scale_checked(cohort$pmi_numeric, "pmi_numeric")
cohort$schema_version <- "analytic_cohort_v1"
derived_first <- c(
  "schema_version", join_key, "diagnosis", "sex", "apoe_group",
  "age_death_numeric", "age_90plus", "pmi_numeric", "pmi_log1p",
  "age_death_scaled", "pmi_scaled"
)
cohort <- cohort[, c(
  derived_first,
  setdiff(names(cohort), derived_first)
), drop = FALSE]
cohort <- cohort[order(cohort[[join_key]]), , drop = FALSE]

donor_inventories <- lapply(seq_len(nrow(audit_table)), function(i) {
  inventory <- data.table::fread(
    audit_table$donors_path[[i]],
    colClasses = c(projid = "character"),
    data.table = FALSE
  )
  required <- c(
    "projid", "nuclei", "raw_counts", "xist_counts", "uty_counts"
  )
  missing <- setdiff(required, names(inventory))
  if (length(missing)) {
    stop(
      "Donor inventory lacks required columns in ",
      audit_table$donors_path[[i]], ": ", paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
  inventory$projid <- normalize_projid(inventory$projid, projid_width)
  if (anyNA(inventory$projid) || anyDuplicated(inventory$projid)) {
    stop(
      "Donor inventory contains missing or duplicate projid values: ",
      audit_table$donors_path[[i]], call. = FALSE
    )
  }
  inventory$rds_id <- audit_table$rds_id[[i]]
  inventory$source_rds <- audit_table$source_rds[[i]]
  inventory
})

combined_expression <- data.table::rbindlist(lapply(
  donor_inventories,
  function(x) x[, c(
    "projid", "nuclei", "raw_counts", "xist_counts", "uty_counts"
  )]
))
sex_check <- combined_expression[, .(
  nuclei = sum(nuclei),
  raw_counts = sum(raw_counts),
  xist_counts = sum(xist_counts),
  uty_counts = sum(uty_counts)
), by = projid]
sex_check <- as.data.frame(sex_check)
sex_check$reported_sex <- ifelse(
  sex_value[match(sex_check$projid, joined[[join_key]])] ==
    as.numeric(cohort_parameters$female_value),
  "Female", "Male"
)
sex_check$expression_sex <- ifelse(
  sex_check$xist_counts > sex_check$uty_counts & sex_check$xist_counts > 0,
  "Female",
  ifelse(
    sex_check$uty_counts > sex_check$xist_counts & sex_check$uty_counts > 0,
    "Male", "Undetermined"
  )
)
sex_check$expression_concordant <- ifelse(
  sex_check$expression_sex == "Undetermined",
  NA,
  sex_check$expression_sex == sex_check$reported_sex
)
prespecified_discordant <- normalize_projid(
  unlist(cohort_parameters$excluded_sex_discordant_projids, use.names = FALSE),
  projid_width
)
sex_check$prespecified_discordant <- sex_check$projid %in% prespecified_discordant
sex_check$xist_cpm <- ifelse(
  sex_check$raw_counts > 0,
  1e6 * sex_check$xist_counts / sex_check$raw_counts,
  NA_real_
)
sex_check$uty_cpm <- ifelse(
  sex_check$raw_counts > 0,
  1e6 * sex_check$uty_counts / sex_check$raw_counts,
  NA_real_
)
sex_check$schema_version <- "sex_linked_expression_check_v1"
sex_check <- sex_check[, c(
  "schema_version", "projid", "reported_sex", "expression_sex",
  "expression_concordant", "prespecified_discordant", "nuclei",
  "raw_counts", "xist_counts", "uty_counts", "xist_cpm", "uty_cpm"
)]
sex_check <- sex_check[order(sex_check$projid), , drop = FALSE]

group_tables <- list(make_group_counts(cohort, "global"))
intersection_rows <- list()
intersection_cohorts <- list()
for (i in seq_along(donor_inventories)) {
  inventory <- donor_inventories[[i]]
  rds_id <- audit_table$rds_id[[i]]
  source_rds <- audit_table$source_rds[[i]]
  intersection <- cohort[cohort[[join_key]] %in% inventory$projid, , drop = FALSE]
  absent <- sort(setdiff(cohort[[join_key]], inventory$projid))
  output_name <- if (identical(rds_id, "vasculature")) {
    "vasculature_cohort_274.tsv"
  } else {
    paste0(rds_id, "_cohort_", nrow(intersection), ".tsv")
  }
  output_path <- file.path(cohort_dir, output_name)
  intersection_cohorts[[rds_id]] <- list(data = intersection, path = output_path)
  intersection_rows[[length(intersection_rows) + 1L]] <- data.frame(
    schema_version = "cohort_rds_intersection_v1",
    rds_id = rds_id,
    source_rds = source_rds,
    represented_donors = nrow(inventory),
    eligible_donors = nrow(intersection),
    globally_eligible_absent_donors = length(absent),
    absent_projids = paste(absent, collapse = ";"),
    output_file = sub(paste0("^", project_root, "/?"), "", output_path),
    stringsAsFactors = FALSE
  )
  group_tables[[length(group_tables) + 1L]] <- make_group_counts(
    intersection, "rds", rds_id
  )
}
intersections <- do.call(rbind, intersection_rows)
group_counts <- do.call(rbind, group_tables)

expected_global_group_counts <- c(
  17L, 8L, 45L, 37L, 11L, 26L,
  6L, 7L, 53L, 29L, 10L, 27L
)
expected_vasculature_group_counts <- c(
  17L, 8L, 45L, 36L, 11L, 26L,
  6L, 7L, 52L, 29L, 10L, 27L
)
checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "cohort_checks_v1",
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}
add_check(
  "metadata_donor_count",
  length(metadata_donors) == 427L,
  length(metadata_donors),
  427L
)
add_check(
  "global_cohort_count",
  nrow(cohort) == as.integer(cohort_parameters$expected_global_donors),
  nrow(cohort),
  cohort_parameters$expected_global_donors
)
add_check(
  "global_group_counts",
  identical(group_counts$donors[group_counts$scope == "global"], expected_global_group_counts),
  group_counts$donors[group_counts$scope == "global"],
  expected_global_group_counts
)
add_check(
  "unique_global_projids",
  !anyDuplicated(cohort[[join_key]]),
  anyDuplicated(cohort[[join_key]]),
  0L
)
add_check(
  "required_derived_fields_complete",
  !anyNA(cohort[, c(
    "diagnosis", "sex", "apoe_group", "age_death_numeric", "pmi_numeric"
  )]),
  sum(is.na(cohort[, c(
    "diagnosis", "sex", "apoe_group", "age_death_numeric", "pmi_numeric"
  )])),
  0L
)
if (isTRUE(config$scope$pilot)) {
  pilot_row <- intersections[intersections$rds_id == "vasculature", , drop = FALSE]
  add_check(
    "phase1_vasculature_intersection_present",
    nrow(pilot_row) == 1L,
    nrow(pilot_row),
    1L
  )
  if (nrow(pilot_row) == 1L) {
    add_check(
      "phase1_vasculature_donor_count",
      pilot_row$eligible_donors[[1L]] ==
        as.integer(cohort_parameters$expected_phase1_donors),
      pilot_row$eligible_donors[[1L]],
      cohort_parameters$expected_phase1_donors
    )
    observed_absent <- sort(strsplit(
      pilot_row$absent_projids[[1L]], ";", fixed = TRUE
    )[[1L]])
    expected_absent <- sort(normalize_projid(
      unlist(cohort_parameters$expected_phase1_absent_projids, use.names = FALSE),
      projid_width
    ))
    add_check(
      "phase1_expected_absent_projids",
      identical(observed_absent, expected_absent),
      observed_absent,
      expected_absent
    )
    vascular_counts <- group_counts$donors[
      group_counts$scope == "rds" & group_counts$rds_id == "vasculature"
    ]
    add_check(
      "phase1_vasculature_group_counts",
      identical(vascular_counts, expected_vasculature_group_counts),
      vascular_counts,
      expected_vasculature_group_counts
    )
  }
  expression_discordant <- sort(sex_check$projid[
    !is.na(sex_check$expression_concordant) &
      !sex_check$expression_concordant
  ])
  add_check(
    "phase1_sex_linked_expression_discordance",
    identical(expression_discordant, sort(prespecified_discordant)),
    expression_discordant,
    sort(prespecified_discordant)
  )
}

check_table <- do.call(rbind, checks)
failed_checks <- check_table$check[!check_table$passed]
validation_status <- if (length(failed_checks)) {
  "failed"
} else {
  "validated_complete"
}

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) {
  "local_pilot_manual"
} else {
  "manual_cohort"
}
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) {
    stop("Execution config does not exist: ", execution_path, call. = FALSE)
  }
  execution_config <- yaml::read_yaml(execution_path)
  execution_phase <- execution_config$execution$execution_phase %||% execution_phase
  backend <- execution_config$execution$backend %||% backend
  run_id <- execution_config$execution$run_id %||% run_id
}

status <- data.frame(
  schema_version = "cohort_status_v1",
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = "global:cohort",
  source_rds = paste(audit_table$source_rds, collapse = ";"),
  scientific_script = "scripts/02_build_cohort.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(
    project_root, "scripts/02_build_cohort.R"
  )),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(
    Sys.time(), started_at, units = "secs"
  )),
  global_donors = nrow(cohort),
  audited_rds = nrow(audit_table),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)

atomic_write_tsv(cohort, global_path)
for (item in intersection_cohorts) {
  atomic_write_tsv(item$data, item$path)
}
atomic_write_tsv(exclusion_flow, flow_path)
atomic_write_tsv(group_counts, groups_path)
atomic_write_tsv(intersections, intersections_path)
atomic_write_tsv(sex_check, sex_check_path)
atomic_write_tsv(check_table, checks_path)
atomic_write_tsv(status, status_path)

cat("Global cohort: ", global_path, " (", nrow(cohort), " donors)\n", sep = "")
for (i in seq_len(nrow(intersections))) {
  cat(
    "RDS cohort: ", intersections$output_file[[i]], " (",
    intersections$eligible_donors[[i]], " donors)\n",
    sep = ""
  )
}
cat("Exclusion flow: ", flow_path, "\n", sep = "")
cat("Group counts: ", groups_path, "\n", sep = "")
cat("Sex-linked expression check: ", sex_check_path, "\n", sep = "")
cat("Cohort status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
