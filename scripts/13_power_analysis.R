#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL, mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode", "--mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/13_power_analysis.R --config FILE ",
        "[--execution-config FILE] [--task-mode power | --mode power]\n",
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
  selected_mode <- out$task_mode %||% out$mode %||% "power"
  if (!identical(selected_mode, "power")) {
    stop("Phase 13 mode must be 'power'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

as_logical <- function(x) {
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

clamp <- function(x, lower, upper) {
  pmax(lower, pmin(upper, x))
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
  path <- tempfile("phase13_inputs_", fileext = ".txt")
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

read_validated_statuses <- function(paths, expected_schema) {
  if (!length(paths) || any(!file.exists(paths))) {
    stop("Required status file is missing for schema ", expected_schema, call. = FALSE)
  }
  values <- lapply(paths, function(path) {
    value <- data.table::fread(path, data.table = FALSE)
    if (nrow(value) != 1L ||
        !identical(value$schema_version[[1L]], expected_schema) ||
        !identical(value$validation_status[[1L]], "validated_complete")) {
      stop("Required status is not validated_complete: ", path, call. = FALSE)
    }
    value
  })
  invisible(do.call(rbind, values))
}

select_contrast_manifest <- function(output_root, execution_stage) {
  candidates <- list.files(
    file.path(output_root, "07_contrasts"),
    pattern = "contrast_manifest[.]tsv$", full.names = TRUE
  )
  candidates <- candidates[!grepl("checks|artifacts|status", basename(candidates))]
  preferred <- candidates[
    basename(candidates) == paste0(execution_stage, "_contrast_manifest.tsv")
  ]
  selected <- if (length(preferred) == 1L) preferred else candidates
  if (length(selected) != 1L) {
    stop("Contrast manifest selection must identify exactly one file", call. = FALSE)
  }
  selected
}

select_representative_cell_types <- function(samples, eligible_manifest) {
  eligible_types <- unique(eligible_manifest$cell_type_high_resolution)
  summary <- samples[
    primary_eligible & cell_type_high_resolution %in% eligible_types,
    .(
      analytic_nuclei = sum(as.numeric(nuclei)),
      analytic_donors = data.table::uniqueN(projid)
    ),
    by = .(cell_type_high_resolution)
  ]
  if (!nrow(summary)) {
    stop("No primary-eligible cell type has an eligible paper-matched contrast", call. = FALSE)
  }
  data.table::setorder(summary, analytic_nuclei, cell_type_high_resolution)
  rare <- summary[1L]
  abundant <- summary[.N]
  selected <- data.table::rbindlist(list(
    data.table::copy(rare)[, representative_role := "rare"],
    data.table::copy(abundant)[, representative_role := "abundant"]
  ))
  selected <- selected[, .(
    analytic_nuclei = max(analytic_nuclei),
    analytic_donors = max(analytic_donors),
    representative_role = paste(sort(unique(representative_role)), collapse = "_and_")
  ), by = .(cell_type_high_resolution)]
  selected
}

select_representative_contrasts <- function(eligible_manifest, selected_types, maximum) {
  selected <- eligible_manifest[
    cell_type_high_resolution %in% selected_types$cell_type_high_resolution
  ]
  selected[, `:=`(
    limiting_donors = pmin(numerator_donors, denominator_donors),
    total_donors = numerator_donors + denominator_donors
  )]
  rows <- list()
  for (cell_type in selected_types$cell_type_high_resolution) {
    table <- selected[cell_type_high_resolution == cell_type]
    data.table::setorder(table, limiting_donors, total_donors, contrast_id)
    limiting <- table[1L]
    limiting[, contrast_role := "limiting"]
    rows[[length(rows) + 1L]] <- limiting
    if (maximum > 1L && nrow(table) > 1L) {
      data.table::setorder(table, -limiting_donors, -total_donors, contrast_id)
      better <- table[1L]
      if (!identical(better$contrast_id[[1L]], limiting$contrast_id[[1L]])) {
        better[, contrast_role := "better_powered"]
        rows[[length(rows) + 1L]] <- better
      }
    }
  }
  data.table::rbindlist(rows, fill = TRUE)
}

select_representative_genes <- function(
    detection, bundles, selected_types, genes_per_cell_type) {
  rows <- list()
  for (cell_type in selected_types$cell_type_high_resolution) {
    rds_ids <- unique(
      bundles$samples$rds_id[
        bundles$samples$cell_type_high_resolution == cell_type
      ]
    )
    available <- unique(unlist(lapply(
      bundles$objects[rds_ids],
      function(bundle) rownames(bundle$counts)
    )))
    table <- detection[
      cell_type_high_resolution == cell_type &
        measured & feature %in% available &
        is.finite(nucleus_detection_fraction)
    ]
    if (!nrow(table)) {
      stop("No measured mtDNA gene is available for cell type ", cell_type, call. = FALSE)
    }
    data.table::setorder(table, nucleus_detection_fraction, feature)
    indices <- unique(round(seq(1L, nrow(table), length.out = min(
      genes_per_cell_type, nrow(table)
    ))))
    chosen <- table[indices]
    chosen[, gene_role := if (.N == 1L) {
      "representative_detection"
    } else ifelse(seq_len(.N) == 1L, "low_detection", "high_detection")]
    rows[[length(rows) + 1L]] <- chosen
  }
  data.table::rbindlist(rows, fill = TRUE)
}

estimate_scenario_parameters <- function(
    contrast, gene_row, bundle, settings) {
  samples <- data.table::as.data.table(bundle$samples)
  samples[, group_label := paste(diagnosis, sex, apoe_group, sep = "__")]
  required_groups <- strsplit(contrast$required_groups[[1L]], ";", fixed = TRUE)[[1L]]
  selected <- which(
    samples$cell_type_high_resolution == contrast$cell_type_high_resolution[[1L]] &
      as_logical(samples$primary_eligible) &
      samples$group_label %in% required_groups
  )
  if (!length(selected)) stop("No samples selected for ", contrast$contrast_id[[1L]])
  gene_index <- match(gene_row$feature[[1L]], rownames(bundle$counts))
  if (is.na(gene_index)) stop("Selected gene is absent from pseudobulk counts")
  sample_indices <- as.integer(samples$sample_index[selected])
  counts <- as.numeric(bundle$counts[gene_index, sample_indices, drop = TRUE])
  nuclei <- as.numeric(samples$nuclei[selected])
  diagnosis <- as.character(samples$diagnosis[selected])
  if (!all(diagnosis %in% c("AD", "NCI")) || !all(nuclei > 0)) {
    stop("Selected scenario has invalid diagnosis or nuclei values")
  }
  mean_per_nucleus <- sum(counts) / sum(nuclei)
  expected <- pmax(mean_per_nucleus * nuclei, 1e-8)
  raw_phi <- sum(pmax((counts - expected)^2 - expected, 0)) / sum(expected^2)
  donor_dispersion <- clamp(
    raw_phi,
    as.numeric(settings$minimum_donor_dispersion),
    as.numeric(settings$maximum_donor_dispersion)
  )
  detection_probability <- clamp(
    as.numeric(gene_row$nucleus_detection_fraction[[1L]]),
    as.numeric(settings$minimum_detection_probability),
    as.numeric(settings$maximum_detection_probability)
  )
  positive_mean <- max(
    mean_per_nucleus / detection_probability,
    as.numeric(settings$minimum_positive_mean)
  )
  list(
    counts = counts, nuclei = nuclei, diagnosis = diagnosis,
    mean_per_nucleus = mean_per_nucleus,
    donor_dispersion = donor_dispersion,
    detection_probability = detection_probability,
    positive_mean = positive_mean
  )
}

simulate_dataset <- function(parameter, effect_log2, settings) {
  diagnosis <- parameter$diagnosis
  observed_nuclei <- parameter$nuclei
  nuclei <- numeric(length(observed_nuclei))
  for (group in c("AD", "NCI")) {
    index <- which(diagnosis == group)
    nuclei[index] <- sample(observed_nuclei[index], length(index), replace = TRUE)
  }
  donor_sigma <- sqrt(log1p(parameter$donor_dispersion))
  donor_multiplier <- exp(
    stats::rnorm(length(nuclei), sd = donor_sigma) - 0.5 * donor_sigma^2
  )
  diagnosis_multiplier <- ifelse(diagnosis == "AD", 2^effect_log2, 1)
  target_mean <- pmax(
    parameter$mean_per_nucleus * donor_multiplier * diagnosis_multiplier,
    1e-8
  )
  detection_shift <- 0.5 * log(target_mean / pmax(parameter$mean_per_nucleus, 1e-8))
  probability <- stats::plogis(
    stats::qlogis(parameter$detection_probability) + detection_shift
  )
  probability <- clamp(
    probability,
    as.numeric(settings$minimum_detection_probability),
    as.numeric(settings$maximum_detection_probability)
  )
  positive_mean <- pmax(
    target_mean / probability,
    as.numeric(settings$minimum_positive_mean)
  )
  cell_size <- 1 / as.numeric(settings$cell_count_dispersion)
  detected <- stats::rbinom(length(nuclei), size = nuclei, prob = probability)
  pseudobulk_counts <- numeric(length(nuclei))
  positive_values <- vector("list", length(nuclei))
  cap <- as.integer(settings$mast_positive_cells_per_donor_cap)
  for (i in seq_along(nuclei)) {
    detections <- as.integer(detected[[i]])
    if (detections > 0L) {
      residual_mean <- max(positive_mean[[i]] - 1, 1e-8)
      pseudobulk_counts[[i]] <- detections + stats::rnbinom(
        1L, size = detections * cell_size, mu = detections * residual_mean
      )
      retained <- min(detections, cap)
      positive_values[[i]] <- 1 + stats::rnbinom(
        retained, size = cell_size, mu = residual_mean
      )
    } else {
      pseudobulk_counts[[i]] <- 0
      positive_values[[i]] <- numeric()
    }
  }
  list(
    diagnosis = diagnosis, nuclei = nuclei, detected = detected,
    counts = pseudobulk_counts, positive_values = positive_values
  )
}

fit_pseudobulk <- function(simulated, dispersion) {
  group <- factor(simulated$diagnosis, levels = c("NCI", "AD"))
  design <- stats::model.matrix(~ group)
  offset <- matrix(log(pmax(simulated$nuclei, 1)), nrow = 1L)
  fit <- edgeR::glmFit(
    matrix(simulated$counts, nrow = 1L),
    design = design, dispersion = dispersion, offset = offset
  )
  test <- edgeR::glmLRT(fit, coef = "groupAD")
  table <- edgeR::topTags(test, n = 1L, sort.by = "none")$table
  list(
    p_value = as.numeric(table$PValue[[1L]]),
    estimated_log2fc = as.numeric(table$logFC[[1L]])
  )
}

fit_mast_like <- function(simulated) {
  ad <- simulated$diagnosis == "AD"
  detected_ad <- sum(simulated$detected[ad])
  detected_nci <- sum(simulated$detected[!ad])
  nuclei_ad <- sum(simulated$nuclei[ad])
  nuclei_nci <- sum(simulated$nuclei[!ad])
  detection_p <- tryCatch(
    suppressWarnings(stats::prop.test(
      c(detected_ad, detected_nci),
      c(nuclei_ad, nuclei_nci),
      correct = FALSE
    )$p.value),
    error = function(e) NA_real_
  )
  positive <- unlist(simulated$positive_values, use.names = FALSE)
  positive_group <- unlist(Map(
    function(values, group) rep(group, length(values)),
    simulated$positive_values, simulated$diagnosis
  ), use.names = FALSE)
  continuous_p <- if (
    length(positive) >= 4L &&
      length(unique(positive_group)) == 2L &&
      all(table(positive_group) >= 2L)
  ) {
    tryCatch(
      suppressWarnings(summary(stats::lm(log1p(positive) ~ factor(
        positive_group, levels = c("NCI", "AD")
      )))$coefficients[2L, 4L]),
      error = function(e) NA_real_
    )
  } else {
    NA_real_
  }
  component_p <- c(detection_p, continuous_p)
  component_p <- component_p[is.finite(component_p)]
  combined_p <- if (!length(component_p)) {
    NA_real_
  } else if (length(component_p) == 1L) {
    component_p[[1L]]
  } else {
    statistic <- -2 * sum(log(pmax(component_p, .Machine$double.xmin)))
    stats::pchisq(statistic, df = 2L * length(component_p), lower.tail = FALSE)
  }
  rate_ad <- (sum(simulated$counts[ad]) + 0.5) / (nuclei_ad + 0.5)
  rate_nci <- (sum(simulated$counts[!ad]) + 0.5) / (nuclei_nci + 0.5)
  list(
    p_value = combined_p,
    estimated_log2fc = log2(rate_ad / rate_nci),
    detection_p_value = detection_p,
    continuous_p_value = continuous_p
  )
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table", "Matrix", "edgeR")
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
power_settings <- list(
  target_power = 0.80,
  nominal_alpha = 0.05,
  effect_log2_grid = c(0.0, 0.25, 0.3785116, 0.5, 0.75, 1.0),
  representative_cell_types = c("rare", "abundant"),
  representative_genes_per_cell_type = 2L,
  representative_contrasts_per_cell_type = 2L,
  minimum_detection_probability = 0.001,
  maximum_detection_probability = 0.999,
  minimum_positive_mean = 1.0,
  cell_count_dispersion = 0.50,
  minimum_donor_dispersion = 0.01,
  maximum_donor_dispersion = 2.00,
  mast_positive_cells_per_donor_cap = 100L
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
analysis <- yaml::read_yaml(analysis_path)

pilot <- isTRUE(config$scope$pilot)
execution <- list(
  execution_stage = if (pilot) "local_pilot" else "minerva_production",
  execution_phase = if (pilot) 1L else 2L,
  backend = "direct", run_id = if (pilot) "manual_local_power" else "manual_power"
)
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  execution <- modifyList(execution, yaml::read_yaml(execution_path)$execution)
}
settings <- if (pilot) analysis$pilot else analysis$production
repetitions <- as.integer(settings$power_repetitions)
output_status <- as.character(settings$output_status)
base_seed <- as.integer(analysis$analysis$seed)
alpha <- as.numeric(power_settings$nominal_alpha)
target_power <- as.numeric(power_settings$target_power)
effects <- sort(unique(as.numeric(unlist(power_settings$effect_log2_grid))))
if (
  !is.finite(repetitions) || repetitions < 1L ||
    any(!is.finite(effects)) || !0 %in% effects ||
    any(effects < 0) || !is.finite(alpha) || alpha <= 0 || alpha >= 1
) {
  stop("Power simulation settings are invalid", call. = FALSE)
}

pb_dir <- file.path(output_root, "07_pseudobulk")
descriptive_dir <- file.path(output_root, "06_descriptive")
contrast_dir <- file.path(output_root, "07_contrasts")
pb_paths <- list.files(
  pb_dir, pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE
)
pb_status_paths <- list.files(
  pb_dir, pattern = "[.]pseudobulk_status[.]tsv$", full.names = TRUE
)
detection_paths <- list.files(
  descriptive_dir, pattern = "_mito_detection[.]tsv$", full.names = TRUE
)
descriptive_status_paths <- list.files(
  descriptive_dir, pattern = "_descriptive_status[.]tsv$", full.names = TRUE
)
contrast_status_paths <- list.files(
  contrast_dir, pattern = "contrast_manifest_status[.]tsv$", full.names = TRUE
)
contrast_path <- select_contrast_manifest(output_root, execution$execution_stage)

read_validated_statuses(pb_status_paths, "pseudobulk_status_v1")
read_validated_statuses(descriptive_status_paths, "descriptive_status_v1")
read_validated_statuses(contrast_status_paths, "contrast_manifest_status_v1")
if (
  !length(pb_paths) || length(pb_paths) != length(pb_status_paths) ||
    !length(detection_paths) ||
    length(detection_paths) != length(descriptive_status_paths)
) {
  stop("Validated Phase 06/07 inputs do not reconcile", call. = FALSE)
}

required_inputs <- c(
  pb_paths, pb_status_paths, detection_paths, descriptive_status_paths,
  contrast_path, contrast_status_paths, analysis_path, manifest_path
)
if (any(!file.exists(required_inputs))) {
  stop("One or more required Phase 13 inputs are missing", call. = FALSE)
}
upstream_sha_before <- vapply(required_inputs, sha256_file, character(1))

bundle_objects <- lapply(pb_paths, readRDS)
bundle_ids <- vapply(bundle_objects, function(bundle) as.character(bundle$rds_id), character(1))
if (anyDuplicated(bundle_ids)) stop("Pseudobulk bundle RDS IDs are not unique", call. = FALSE)
names(bundle_objects) <- bundle_ids
sample_list <- lapply(bundle_objects, function(bundle) {
  value <- data.table::as.data.table(bundle$samples)
  if (
    nrow(value) != ncol(bundle$counts) ||
      !identical(as.integer(value$sample_index), seq_len(nrow(value)))
  ) {
    stop("Pseudobulk sample order does not match count columns for ", bundle$rds_id)
  }
  value
})
samples <- data.table::rbindlist(sample_list, fill = TRUE)
samples[, primary_eligible := as_logical(primary_eligible)]
detection <- data.table::rbindlist(
  lapply(detection_paths, data.table::fread), fill = TRUE
)
detection[, measured := as_logical(measured)]
manifest <- data.table::fread(contrast_path)
eligible_manifest <- manifest[
  as_logical(paper_matched) & eligibility_status == "eligible"
]
if (!nrow(eligible_manifest)) stop("No eligible paper-matched contrasts exist", call. = FALSE)

bundle_container <- list(objects = bundle_objects, samples = samples)
selected_types <- select_representative_cell_types(samples, eligible_manifest)
selected_contrasts <- select_representative_contrasts(
  eligible_manifest, selected_types,
  as.integer(power_settings$representative_contrasts_per_cell_type)
)
selected_genes <- select_representative_genes(
  detection, bundle_container, selected_types,
  as.integer(power_settings$representative_genes_per_cell_type)
)

scenario_rows <- list()
for (i in seq_len(nrow(selected_contrasts))) {
  contrast <- selected_contrasts[i]
  genes <- selected_genes[
    cell_type_high_resolution == contrast$cell_type_high_resolution
  ]
  for (j in seq_len(nrow(genes))) {
    gene <- genes[j]
    bundle <- bundle_objects[[contrast$rds_id[[1L]]]]
    parameter <- estimate_scenario_parameters(
      contrast, gene, bundle, power_settings
    )
    role <- selected_types[
      cell_type_high_resolution == contrast$cell_type_high_resolution,
      representative_role
    ][[1L]]
    scenario_rows[[length(scenario_rows) + 1L]] <- data.table::data.table(
      rds_id = contrast$rds_id,
      cell_type_high_resolution = contrast$cell_type_high_resolution,
      representative_role = role,
      contrast_id = contrast$contrast_id,
      contrast_name = contrast$contrast_name,
      contrast_role = contrast$contrast_role,
      gene = gene$feature,
      gene_role = gene$gene_role,
      observed_detection_probability = parameter$detection_probability,
      observed_mean_count_per_nucleus = parameter$mean_per_nucleus,
      observed_positive_mean = parameter$positive_mean,
      observed_donor_dispersion = parameter$donor_dispersion,
      donors_ad = sum(parameter$diagnosis == "AD"),
      donors_nci = sum(parameter$diagnosis == "NCI"),
      observed_nuclei_ad = sum(parameter$nuclei[parameter$diagnosis == "AD"]),
      observed_nuclei_nci = sum(parameter$nuclei[parameter$diagnosis == "NCI"]),
      parameter = list(parameter)
    )
  }
}
scenarios <- data.table::rbindlist(scenario_rows, fill = TRUE)
scenarios[, scenario_id := sprintf("power_scenario_%03d", seq_len(.N))]

grid <- scenarios[, .(
  effect_log2 = effects,
  effect_fold_change = 2^effects
), by = .(
  scenario_id, rds_id, cell_type_high_resolution, representative_role,
  contrast_id, contrast_name, contrast_role, gene, gene_role,
  observed_detection_probability, observed_mean_count_per_nucleus,
  observed_positive_mean, observed_donor_dispersion,
  donors_ad, donors_nci, observed_nuclei_ad, observed_nuclei_nci
)]
grid <- grid[, .(method_branch = c(
  "pseudobulk_edgeR_known_dispersion",
  "paper_like_mast_hurdle"
)), by = names(grid)]
grid[, grid_id := sprintf("power_grid_%04d", seq_len(.N))]

diagnostic_rows <- vector("list", nrow(grid) * repetitions)
position <- 0L
for (i in seq_len(nrow(grid))) {
  row <- grid[i]
  scenario_index <- match(row$scenario_id, scenarios$scenario_id)
  parameter <- scenarios$parameter[[scenario_index]]
  scenario_number <- as.integer(sub(".*_", "", row$scenario_id))
  effect_number <- match(row$effect_log2, effects)
  for (iteration in seq_len(repetitions)) {
    seed <- as.integer(base_seed + scenario_number * 100000L + effect_number * 1000L + iteration)
    set.seed(seed)
    simulated <- simulate_dataset(parameter, row$effect_log2, power_settings)
    fit_error <- ""
    fit <- tryCatch(
      if (row$method_branch == "pseudobulk_edgeR_known_dispersion") {
        fit_pseudobulk(simulated, parameter$donor_dispersion)
      } else {
        fit_mast_like(simulated)
      },
      error = function(e) {
        fit_error <<- conditionMessage(e)
        NULL
      }
    )
    position <- position + 1L
    diagnostic_rows[[position]] <- data.table::data.table(
      schema_version = "power_simulation_diagnostics_v1",
      grid_id = row$grid_id, scenario_id = row$scenario_id,
      method_branch = row$method_branch,
      rds_id = row$rds_id,
      cell_type_high_resolution = row$cell_type_high_resolution,
      contrast_id = row$contrast_id, gene = row$gene,
      effect_log2 = row$effect_log2,
      repetition = iteration, seed = seed,
      p_value = if (is.null(fit)) NA_real_ else fit$p_value,
      estimated_log2fc = if (is.null(fit)) NA_real_ else fit$estimated_log2fc,
      detection_p_value = if (
        is.null(fit) || is.null(fit$detection_p_value)
      ) NA_real_ else fit$detection_p_value,
      continuous_p_value = if (
        is.null(fit) || is.null(fit$continuous_p_value)
      ) NA_real_ else fit$continuous_p_value,
      detected_at_nominal_alpha = if (
        is.null(fit) || !is.finite(fit$p_value)
      ) NA else fit$p_value < alpha,
      terminal_status = if (
        is.null(fit) || !is.finite(fit$p_value) ||
          !is.finite(fit$estimated_log2fc)
      ) "failed" else "validated_complete",
      message = fit_error
    )
  }
}
diagnostics <- data.table::rbindlist(diagnostic_rows[seq_len(position)], fill = TRUE)

results <- diagnostics[, {
  completed <- terminal_status == "validated_complete"
  valid_p <- p_value[completed]
  valid_effect <- estimated_log2fc[completed]
  rejection <- valid_p < alpha
  list(
    repetitions_planned = repetitions,
    repetitions_completed = sum(completed),
    rejected = sum(rejection),
    rejection_rate = mean(rejection),
    power = if (effect_log2[[1L]] > 0) mean(rejection) else NA_real_,
    directional_power = if (effect_log2[[1L]] > 0) {
      mean(rejection & valid_effect > 0)
    } else {
      NA_real_
    },
    false_positive_rate = if (effect_log2[[1L]] == 0) {
      mean(rejection)
    } else {
      NA_real_
    },
    mean_estimated_log2fc = mean(valid_effect),
    median_estimated_log2fc = stats::median(valid_effect),
    effect_bias = mean(valid_effect) - effect_log2[[1L]],
    monte_carlo_standard_error = sqrt(
      mean(rejection) * (1 - mean(rejection)) / length(rejection)
    ),
    terminal_status = if (sum(completed) == repetitions) {
      "validated_complete"
    } else {
      "failed"
    }
  )
}, by = .(
  grid_id, scenario_id, method_branch, rds_id,
  cell_type_high_resolution, contrast_id, gene, effect_log2
)]
results <- merge(
  results,
  grid[, .(
    grid_id, representative_role, contrast_name, contrast_role, gene_role,
    effect_fold_change, observed_detection_probability,
    observed_mean_count_per_nucleus, observed_positive_mean,
    observed_donor_dispersion, donors_ad, donors_nci,
    observed_nuclei_ad, observed_nuclei_nci
  )],
  by = "grid_id", all.x = TRUE, sort = FALSE
)
results[, `:=`(
  schema_version = "power_results_v1",
  execution_stage = execution$execution_stage,
  output_status = output_status,
  nominal_alpha = alpha,
  target_power = target_power
)]
data.table::setcolorder(results, c(
  "schema_version", "execution_stage", "output_status", "grid_id",
  "scenario_id", "method_branch", "rds_id",
  "cell_type_high_resolution", "representative_role", "contrast_id",
  "contrast_name", "contrast_role", "gene", "gene_role", "effect_log2",
  "effect_fold_change", "nominal_alpha", "target_power",
  setdiff(names(results), c(
    "schema_version", "execution_stage", "output_status", "grid_id",
    "scenario_id", "method_branch", "rds_id",
    "cell_type_high_resolution", "representative_role", "contrast_id",
    "contrast_name", "contrast_role", "gene", "gene_role", "effect_log2",
    "effect_fold_change", "nominal_alpha", "target_power"
  ))
))

mde <- results[effect_log2 > 0, {
  eligible <- which(
    terminal_status == "validated_complete" &
      is.finite(power) & power >= target_power
  )
  if (length(eligible)) {
    selected <- eligible[which.min(effect_log2[eligible])]
    list(
      minimum_detectable_log2_effect = effect_log2[selected],
      minimum_detectable_fold_change = effect_fold_change[selected],
      achieved_power = power[selected],
      mde_status = "target_reached"
    )
  } else {
    list(
      minimum_detectable_log2_effect = NA_real_,
      minimum_detectable_fold_change = NA_real_,
      achieved_power = max(power, na.rm = TRUE),
      mde_status = "target_not_reached_in_grid"
    )
  }
}, by = .(
  scenario_id, method_branch, rds_id, cell_type_high_resolution,
  representative_role, contrast_id, contrast_name, contrast_role,
  gene, gene_role, donors_ad, donors_nci
)]
mde[, `:=`(
  schema_version = "power_mde_v1",
  execution_stage = execution$execution_stage,
  output_status = output_status,
  target_power = target_power,
  interpretation = if (pilot) {
    "pilot_mde_is_coarse_and_nonfinal"
  } else {
    "production_mde_from_prespecified_grid"
  }
)]

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "power_checks_v1", check = check,
    passed = isTRUE(passed), observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"), stringsAsFactors = FALSE
  )
}
add_check(
  "both_analysis_branches_present",
  setequal(unique(results$method_branch), c(
    "pseudobulk_edgeR_known_dispersion", "paper_like_mast_hurdle"
  )),
  paste(sort(unique(results$method_branch)), collapse = ";"),
  "paper_like_mast_hurdle;pseudobulk_edgeR_known_dispersion"
)
add_check(
  "representative_rare_and_abundant_cell_types_present",
  all(c("rare", "abundant") %in% unlist(strsplit(
    paste(selected_types$representative_role, collapse = "_and_"),
    "_and_", fixed = TRUE
  ))),
  paste(selected_types$representative_role, collapse = ";"),
  "rare;abundant"
)
add_check(
  "zero_and_positive_effects_present",
  0 %in% results$effect_log2 && any(results$effect_log2 > 0),
  paste(sort(unique(results$effect_log2)), collapse = ";"),
  "zero_and_positive"
)
add_check(
  "all_grid_rows_reach_repetition_target",
  all(results$repetitions_completed == repetitions),
  paste(range(results$repetitions_completed), collapse = ";"),
  repetitions
)
add_check(
  "all_simulations_validate",
  all(diagnostics$terminal_status == "validated_complete"),
  sum(diagnostics$terminal_status == "failed"), 0L
)
add_check(
  "p_values_and_effects_finite",
  all(is.finite(diagnostics$p_value)) &&
    all(diagnostics$p_value >= 0 & diagnostics$p_value <= 1) &&
    all(is.finite(diagnostics$estimated_log2fc)),
  nrow(diagnostics), nrow(diagnostics)
)
add_check(
  "seeds_unique_within_method",
  !anyDuplicated(paste(
    diagnostics$method_branch, diagnostics$seed, sep = "\r"
  )),
  anyDuplicated(paste(diagnostics$method_branch, diagnostics$seed, sep = "\r")),
  0L
)
add_check(
  "output_label_matches_execution_scope",
  (!pilot && identical(output_status, "final")) ||
    (pilot && identical(output_status, "nonfinal_smoke_test")),
  output_status, if (pilot) "nonfinal_smoke_test" else "final"
)
add_check(
  "mde_rows_cover_scenarios_and_methods",
  nrow(mde) == data.table::uniqueN(
    paste(results$scenario_id, results$method_branch, sep = "\r")
  ),
  nrow(mde),
  data.table::uniqueN(paste(results$scenario_id, results$method_branch, sep = "\r"))
)
checks <- data.table::rbindlist(checks)

output_dir <- file.path(output_root, "13_power")
paths <- list(
  results = file.path(
    output_dir, if (pilot) "power_smoke.tsv" else "power_results.tsv.gz"
  ),
  grid = file.path(output_dir, "power_grid.tsv"),
  mde = file.path(output_dir, "power_mde.tsv"),
  diagnostics = file.path(
    output_dir,
    if (pilot) "power_simulation_diagnostics.tsv" else "power_simulation_diagnostics.tsv.gz"
  ),
  checks = file.path(output_dir, "power_checks.tsv"),
  artifacts = file.path(output_dir, "power_artifacts.tsv"),
  status = file.path(output_dir, "power_status.tsv")
)
grid_output <- data.table::copy(grid)
grid_output[, `:=`(
  schema_version = "power_grid_v1",
  execution_stage = execution$execution_stage,
  output_status = output_status,
  repetitions = repetitions
)]
atomic_write_tsv(results, paths$results, gzip = !pilot)
atomic_write_tsv(grid_output, paths$grid)
atomic_write_tsv(mde, paths$mde)
atomic_write_tsv(diagnostics, paths$diagnostics, gzip = !pilot)
atomic_write_tsv(checks, paths$checks)

upstream_sha_after <- vapply(required_inputs, sha256_file, character(1))
upstream_unchanged <- identical(
  unname(upstream_sha_before), unname(upstream_sha_after)
)
checks <- data.table::fread(paths$checks)
checks <- data.table::rbindlist(list(checks, data.frame(
  schema_version = "power_checks_v1",
  check = "upstream_artifacts_unchanged",
  passed = upstream_unchanged,
  observed = if (upstream_unchanged) "unchanged" else "changed",
  expected = "unchanged", stringsAsFactors = FALSE
)))
atomic_write_tsv(checks, paths$checks)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

artifact_paths <- unlist(paths[c("results", "grid", "mde", "diagnostics", "checks")])
artifacts <- data.frame(
  schema_version = "power_artifacts_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = c(
    nrow(results), nrow(grid_output), nrow(mde), nrow(diagnostics), nrow(checks)
  ),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, paths$artifacts)

status <- data.frame(
  schema_version = "power_status_v1",
  execution_stage = execution$execution_stage,
  execution_phase = execution$execution_phase,
  backend = execution$backend,
  run_id = execution$run_id,
  stable_task_id = "global:power",
  source_rds = paste(sort(unique(scenarios$rds_id)), collapse = ";"),
  scientific_script = "scripts/13_power_analysis.R",
  scientific_code_bundle_sha256 = sha256_file(
    file.path(project_root, "scripts/13_power_analysis.R")
  ),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  upstream_input_bundle_sha256 = sha256_lines(
    paste(names(upstream_sha_before), upstream_sha_before, sep = "=")
  ),
  output_status = output_status,
  representative_cell_types = data.table::uniqueN(
    scenarios$cell_type_high_resolution
  ),
  representative_scenarios = nrow(scenarios),
  grid_rows = nrow(results),
  simulation_rows = nrow(diagnostics),
  repetitions_per_condition = repetitions,
  target_power = target_power,
  mde_target_reached_rows = sum(mde$mde_status == "target_reached"),
  mde_target_not_reached_rows = sum(
    mde$mde_status == "target_not_reached_in_grid"
  ),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Power output: ", output_dir, "\n", sep = "")
cat("Representative cell types: ", status$representative_cell_types, "\n", sep = "")
cat("Representative scenarios: ", status$representative_scenarios, "\n", sep = "")
cat("Power grid rows: ", status$grid_rows, "\n", sep = "")
cat("Simulation rows: ", status$simulation_rows, "\n", sep = "")
cat("MDE targets reached: ", status$mde_target_reached_rows, "\n", sep = "")
cat("Phase 13 status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
