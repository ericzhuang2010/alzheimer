#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

"%||%" <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = "respiratory_modifier")
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/13_run_respiratory_modifier.R ",
          "--config FILE --execution-config FILE ",
          "[--task-mode respiratory_modifier]\n", sep = "")
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$execution_config)) {
    stop("--config and --execution-config are required", call. = FALSE)
  }
  if (!identical(out$task_mode, "respiratory_modifier")) {
    stop("--task-mode must be respiratory_modifier", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  x <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(x, "status")
  if (!length(x) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(x[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

git_revision <- function(root) {
  x <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(x, "status")
  if (!length(x) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else x[[1L]]
}

atomic_write_tsv <- function(x, path, schema_version = NULL) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  if (!is.null(schema_version)) {
    x$schema_version <- schema_version
    x <- x[, c("schema_version", setdiff(names(x), "schema_version")), drop = FALSE]
  }
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  con <- if (grepl("[.]gz$", path)) gzfile(tmp, "wt") else file(tmp, "wt")
  write.table(x, con, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  close(con)
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

atomic_save_rds <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  saveRDS(x, tmp, compress = "gzip")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

bind_rows <- function(xs) {
  xs <- Filter(function(x) !is.null(x) && nrow(x), xs)
  if (!length(xs)) return(data.frame())
  data.table::rbindlist(xs, fill = TRUE, use.names = TRUE)
}

read_status <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  x <- data.table::fread(path, nrows = 1L, data.table = FALSE)
  if (!"validation_status" %in% names(x)) return(NA_character_)
  as.character(x$validation_status[[1L]])
}

normalize_study <- function(cohort) {
  if (!"study" %in% names(cohort) && "Study" %in% names(cohort)) {
    cohort$study <- cohort$Study
  }
  cohort$study <- toupper(trimws(as.character(cohort$study)))
  cohort
}

contrast_manifest_from_config <- function(cfg) {
  out <- lapply(cfg$contrasts, function(x) {
    co <- unlist(x$coefficients)
    data.frame(
      contrast_order = as.integer(x$contrast_order),
      contrast_id = as.character(x$contrast_id),
      modifier = as.character(x$modifier),
      group_1 = as.character(x$required_groups[[1L]]),
      group_2 = as.character(x$required_groups[[2L]]),
      group_3 = as.character(x$required_groups[[3L]]),
      group_4 = as.character(x$required_groups[[4L]]),
      coefficients = paste(paste(names(co), co, sep = "="), collapse = ";"),
      positive_estimate_meaning = if (x$modifier == "sex") {
        "AD effect is more positive, or less negative, in females"
      } else "AD effect is more positive, or less negative, in the first APOE group",
      stringsAsFactors = FALSE
    )
  })
  as.data.frame(bind_rows(out))
}

context_manifest_from_config <- function(cfg, pilot) {
  entries <- cfg$contexts
  if (pilot) entries <- Filter(function(x) identical(x$context_id, "vasculature"), entries)
  out <- lapply(entries, function(x) data.frame(
    context_order = as.integer(x$context_order),
    context_id = as.character(x$context_id),
    context_label = as.character(x$label),
    source_rds_ids = paste(unlist(x$source_rds_ids), collapse = "|"),
    source_stems = paste(unlist(x$source_stems), collapse = "|"),
    pilot_context = pilot,
    stringsAsFactors = FALSE
  ))
  as.data.frame(bind_rows(out))
}

module_manifest_from_config <- function(cfg) {
  out <- lapply(cfg$modules, function(x) data.frame(
    module_order = as.integer(x$module_order),
    module_id = as.character(x$module_id),
    module_label = as.character(x$label),
    module_role = as.character(x$role),
    reference_genes = as.integer(x$reference_genes),
    minimum_fraction = as.numeric(x$minimum_fraction),
    minimum_genes = as.integer(x$minimum_genes),
    mtdna_specific_minimum = if (x$module_id == "mtdna_oxphos_13") 10L else NA_integer_,
    source = "MitoCarta3.0 frozen Phase 13 manifest",
    overlap_policy = "report overlap; do not treat modules as independent confirmations",
    stringsAsFactors = FALSE
  ))
  as.data.frame(bind_rows(out))
}

strata_from_config <- function(cfg) {
  lapply(cfg$strata, function(x) list(
    stratum_order = as.integer(x$stratum_order),
    stratum_id = as.character(x$stratum_id),
    nci_group = as.character(x$nci_group),
    ad_group = as.character(x$ad_group)
  ))
}

make_group <- function(diagnosis, sex, apoe) paste(diagnosis, sex, apoe, sep = "__")

build_design <- function(samples, group_levels, extra_qc = FALSE) {
  d <- samples
  d$diagnosis_sex_APOE_group <- factor(d$group_id, levels = group_levels)
  d$study <- factor(d$study, levels = sort(unique(d$study)))
  formula <- if (extra_qc) {
    ~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled +
      study + aggregate_percent_mt + robust_qc_fraction
  } else {
    ~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled + study
  }
  design <- model.matrix(formula, data = d)
  prefix <- "diagnosis_sex_APOE_group"
  nms <- colnames(design)
  hit <- startsWith(nms, prefix)
  nms[hit] <- sub(paste0("^", prefix), "", nms[hit])
  colnames(design) <- nms
  design
}

contrast_vector <- function(contrast, coefficient_names) {
  out <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  co <- unlist(contrast$coefficients)
  missing <- setdiff(names(co), coefficient_names)
  if (length(missing)) {
    stop("Contrast groups missing from design: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  out[names(co)] <- as.numeric(co)
  out
}

stratum_vector <- function(stratum, coefficient_names) {
  out <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  missing <- setdiff(c(stratum$ad_group, stratum$nci_group), coefficient_names)
  if (length(missing)) return(out * NA_real_)
  out[stratum$ad_group] <- 1
  out[stratum$nci_group] <- -1
  out
}

required_group_counts <- function(samples, contrast, threshold) {
  s <- samples[samples$nuclei >= threshold, , drop = FALSE]
  n <- table(factor(s$group_id, levels = unlist(contrast$required_groups)))
  setNames(as.integer(n), names(n))
}

seed_for <- function(cfg, id) {
  base <- as.numeric(cfg$randomization$base_seed)
  offset <- abs(as.numeric(digest::digest2int(as.character(id))))
  as.integer((base + offset) %% (.Machine$integer.max - 1)) + 1L
}

positive_core_count <- function(x) {
  value <- suppressWarnings(as.integer(x))
  if (length(value) != 1L || is.na(value) || value < 1L) NA_integer_ else value
}

scheduler_core_limit <- function(environment = Sys.getenv()) {
  keys <- c("LSB_DJOB_NUMPROC", "SLURM_CPUS_PER_TASK", "NSLOTS")
  values <- vapply(keys, function(key) {
    positive_core_count(unname(environment[key]))
  }, integer(1))
  values <- values[!is.na(values)]
  if (length(values)) min(values) else NA_integer_
}

resolve_stability_workers <- function(execution, available_cores = NULL,
                                      scheduler_cores = NULL,
                                      os_type = .Platform$OS.type) {
  maximum <- positive_core_count(execution$max_total_cores)
  if (is.na(maximum)) {
    stop("execution.max_total_cores must be a positive integer", call. = FALSE)
  }
  requested_value <- execution$phase13_stability_workers %||% maximum
  requested <- positive_core_count(requested_value)
  if (is.na(requested)) {
    stop("execution.phase13_stability_workers must be a positive integer", call. = FALSE)
  }
  if (is.null(available_cores)) {
    available_cores <- positive_core_count(parallel::detectCores(logical = TRUE))
  } else {
    available_cores <- positive_core_count(available_cores)
  }
  if (is.null(scheduler_cores)) scheduler_cores <- scheduler_core_limit()
  scheduler_cores <- positive_core_count(scheduler_cores)
  limits <- c(requested, maximum, available_cores, scheduler_cores)
  limits <- limits[!is.na(limits)]
  workers <- if (length(limits)) min(limits) else 1L
  if (!identical(os_type, "unix")) workers <- 1L
  list(
    requested = requested,
    effective = max(1L, as.integer(workers)),
    max_total = maximum,
    available = available_cores,
    scheduler = scheduler_cores,
    backend = if (identical(os_type, "unix") && workers > 1L) "fork" else "sequential"
  )
}

parallel_lapply_ordered <- function(tasks, fun, workers = 1L, label = "tasks") {
  if (!length(tasks)) return(list())
  workers <- positive_core_count(workers)
  if (is.na(workers)) workers <- 1L
  workers <- min(workers, length(tasks))
  if (workers <= 1L || !identical(.Platform$OS.type, "unix")) {
    return(lapply(tasks, fun))
  }
  started <- proc.time()[["elapsed"]]
  cat("  ", label, ": ", length(tasks), " tasks on ", workers,
      " fork workers\n", sep = "")
  wrapped <- function(task) {
    tryCatch(
      list(success = TRUE, value = fun(task), message = ""),
      error = function(e) list(
        success = FALSE, value = NULL,
        message = paste0(class(e)[[1L]], ": ", conditionMessage(e))
      )
    )
  }
  results <- parallel::mclapply(
    tasks, wrapped, mc.cores = workers, mc.preschedule = TRUE,
    mc.set.seed = FALSE, mc.silent = FALSE
  )
  process_failures <- vapply(results, inherits, logical(1), what = "try-error")
  task_failures <- !process_failures & !vapply(
    results, function(x) is.list(x) && isTRUE(x$success), logical(1)
  )
  if (any(process_failures | task_failures)) {
    failed <- which(process_failures | task_failures)
    messages <- vapply(failed, function(i) {
      if (process_failures[[i]]) as.character(results[[i]]) else results[[i]]$message
    }, character(1))
    stop(
      "Parallel ", label, " failed for task(s) ", paste(failed, collapse = ", "),
      ": ", paste(unique(messages), collapse = " | "), call. = FALSE
    )
  }
  elapsed <- proc.time()[["elapsed"]] - started
  cat("  ", label, " completed in ", round(elapsed, 1), " seconds\n", sep = "")
  lapply(results, `[[`, "value")
}

add_check_factory <- function() {
  rows <- list()
  add <- function(check_id, stage_id, scope_type, scope_id,
                  blocking, passed, observed, expected, details = "") {
    rows[[length(rows) + 1L]] <<- data.frame(
      check_id = as.character(check_id), stage_id = as.character(stage_id),
      scope_type = as.character(scope_type), scope_id = as.character(scope_id),
      blocking = as.logical(blocking), passed = isTRUE(passed),
      observed = paste(observed, collapse = ";"),
      expected = paste(expected, collapse = ";"),
      details = as.character(details), stringsAsFactors = FALSE
    )
    invisible(isTRUE(passed))
  }
  list(add = add, value = function() as.data.frame(bind_rows(rows)))
}

input_paths_for_source <- function(stage_root, phase_cfg, rds_id, stem) {
  pb_root <- file.path(stage_root, phase_cfg$paths$pseudobulk_relative)
  list(
    counts = file.path(pb_root, paste0(stem, ".pseudobulk_counts.rds")),
    samples = file.path(pb_root, paste0(stem, ".pseudobulk_samples.tsv")),
    conservation = file.path(pb_root, paste0(stem, ".pseudobulk_count_conservation.tsv")),
    manifest = file.path(pb_root, paste0(stem, ".pseudobulk_manifest.tsv")),
    status = file.path(pb_root, paste0(stem, ".pseudobulk_status.tsv")),
    qc = file.path(stage_root, "04_qc", paste0(rds_id, "_cell_qc.tsv.gz")),
    qc_status = file.path(stage_root, "04_qc", paste0(rds_id, "_qc_status.tsv"))
  )
}

validate_and_load_inputs <- function(project_root, stage_root, phase_cfg,
                                     context_manifest, check) {
  cohort_path <- file.path(stage_root, phase_cfg$paths$cohort_relative)
  cohort_status_path <- file.path(stage_root, phase_cfg$paths$cohort_status_relative)
  annotation_status_path <- file.path(stage_root, phase_cfg$paths$annotation_status_relative)
  required_global <- c(cohort_path, cohort_status_path, annotation_status_path)
  missing_global <- required_global[!file.exists(required_global)]
  check("required_global_inputs_exist", "input_validation", "global", "phase13",
        TRUE, !length(missing_global), length(required_global) - length(missing_global),
        length(required_global), paste(missing_global, collapse = "|"))
  if (length(missing_global)) {
    stop("Missing required Phase 13 global inputs: ", paste(missing_global, collapse = ", "),
         call. = FALSE)
  }
  check("phase02_status_validated", "input_validation", "global", "phase02",
        TRUE, identical(read_status(cohort_status_path), "validated_complete"),
        read_status(cohort_status_path), "validated_complete")
  check("phase03_status_validated", "input_validation", "global", "phase03",
        TRUE, identical(read_status(annotation_status_path), "validated_complete"),
        read_status(annotation_status_path), "validated_complete")
  cohort <- normalize_study(data.table::fread(
    cohort_path, colClasses = list(character = "projid"), data.table = FALSE
  ))
  cohort$projid <- as.character(cohort$projid)
  needed <- c("projid", "diagnosis", "sex", "apoe_group",
              "age_death_scaled", "pmi_scaled", "study")
  check("cohort_fields_complete", "input_validation", "global", "phase02",
        TRUE, all(needed %in% names(cohort)),
        paste(intersect(needed, names(cohort)), collapse = "|"), paste(needed, collapse = "|"))
  if (!all(needed %in% names(cohort))) stop("Phase 02 cohort fields are incomplete", call. = FALSE)
  check("cohort_key_unique", "input_validation", "global", "phase02",
        TRUE, !anyDuplicated(cohort$projid), anyDuplicated(cohort$projid), 0)
  inventory <- list(data.frame(
    input_id = c("phase02_cohort", "phase02_status", "phase03_status"),
    source_phase = c("02", "02", "03"), rds_id = NA_character_,
    path = required_global, bytes = file.info(required_global)$size,
    sha256 = vapply(required_global, sha256_file, character(1)),
    validation_status = c("validated_complete", read_status(cohort_status_path),
                          read_status(annotation_status_path)),
    stringsAsFactors = FALSE
  ))
  source_objects <- list()
  identity <- list()
  feature_reference <- NULL
  all_barcodes <- list()
  for (i in seq_len(nrow(context_manifest))) {
    context_id <- context_manifest$context_id[[i]]
    ids <- strsplit(context_manifest$source_rds_ids[[i]], "|", fixed = TRUE)[[1L]]
    stems <- strsplit(context_manifest$source_stems[[i]], "|", fixed = TRUE)[[1L]]
    source_objects[[context_id]] <- list()
    for (j in seq_along(ids)) {
      paths <- input_paths_for_source(stage_root, phase_cfg, ids[[j]], stems[[j]])
      required <- unlist(paths[c("counts", "samples", "conservation", "manifest",
                                 "status", "qc", "qc_status")])
      missing <- required[!file.exists(required)]
      check(paste0("source_files_exist__", ids[[j]]), "input_validation", "rds", ids[[j]],
            TRUE, !length(missing), length(required) - length(missing), length(required),
            paste(missing, collapse = "|"))
      if (length(missing)) {
        stop("Missing required Phase 07/04 bundle for ", ids[[j]], ": ",
             paste(missing, collapse = ", "),
             ". Run the Phase 07 prerequisite before Phase 13.", call. = FALSE)
      }
      pb_status <- read_status(paths$status)
      qc_status <- read_status(paths$qc_status)
      check(paste0("phase07_status_validated__", ids[[j]]), "input_validation", "rds",
            ids[[j]], TRUE, identical(pb_status, "validated_complete"), pb_status,
            "validated_complete")
      check(paste0("phase04_status_validated__", ids[[j]]), "input_validation", "rds",
            ids[[j]], TRUE, identical(qc_status, "validated_complete"), qc_status,
            "validated_complete")
      obj <- readRDS(paths$counts)
      samples_file <- data.table::fread(
        paths$samples, colClasses = list(character = "projid"), data.table = FALSE
      )
      if (!identical(as.character(obj$samples$projid), as.character(samples_file$projid))) {
        stop("Phase 07 embedded and external samples disagree for ", ids[[j]], call. = FALSE)
      }
      counts <- obj$counts
      features <- rownames(counts)
      sample_match <- identical(colnames(counts), as.character(samples_file$pseudobulk_id))
      check(paste0("sample_columns_match__", ids[[j]]), "input_validation", "rds",
            ids[[j]], TRUE, sample_match, sample_match, TRUE)
      if (is.null(feature_reference)) feature_reference <- features
      feature_match <- identical(features, feature_reference)
      check(paste0("feature_order_match__", ids[[j]]), "input_validation", "rds",
            ids[[j]], TRUE, feature_match, length(features), length(feature_reference))
      cons <- data.table::fread(paths$conservation, data.table = FALSE)
      cons_ok <- all(as.logical(cons$passed))
      check(paste0("phase07_conservation__", ids[[j]]), "input_validation", "rds",
            ids[[j]], TRUE, cons_ok, sum(as.logical(cons$passed)), nrow(cons))
      qc <- data.table::fread(paths$qc, select = c("barcode", "cohort_included"),
                             colClasses = list(character = "barcode"), data.table = FALSE)
      qc <- qc[as.logical(qc$cohort_included), , drop = FALSE]
      all_barcodes[[ids[[j]]]] <- as.character(qc$barcode)
      source_objects[[context_id]][[ids[[j]]]] <- list(
        rds_id = ids[[j]], stem = stems[[j]], counts = counts,
        samples = samples_file, object = obj, paths = paths
      )
      inventory[[length(inventory) + 1L]] <- data.frame(
        input_id = paste0(ids[[j]], "__", names(required)),
        source_phase = c("07", "07", "07", "07", "07", "04", "04"),
        rds_id = ids[[j]], path = as.character(required),
        bytes = file.info(required)$size,
        sha256 = vapply(required, sha256_file, character(1)),
        validation_status = c(rep(pb_status, 5L), rep(qc_status, 2L)),
        stringsAsFactors = FALSE
      )
      identity[[length(identity) + 1L]] <- data.frame(
        context_id = context_id, rds_id = ids[[j]], features = nrow(counts),
        samples = ncol(counts), feature_order_identical = feature_match,
        count_columns_match_samples = sample_match, conservation_passed = cons_ok,
        cohort_barcodes = length(all_barcodes[[ids[[j]]]]), stringsAsFactors = FALSE
      )
    }
  }
  ex_ids <- intersect(c("excitatory_set1", "excitatory_set2", "excitatory_set3"),
                      names(all_barcodes))
  overlap_count <- 0L
  if (length(ex_ids) > 1L) {
    pairs <- combn(ex_ids, 2L, simplify = FALSE)
    overlap_count <- sum(vapply(pairs, function(p) {
      length(intersect(all_barcodes[[p[[1L]]]], all_barcodes[[p[[2L]]]]))
    }, integer(1)))
  }
  check("excitatory_barcodes_pairwise_disjoint", "input_validation", "context",
        "excitatory_neurons", TRUE, overlap_count == 0L, overlap_count, 0L)
  list(cohort = cohort, source_objects = source_objects,
       inventory = as.data.frame(bind_rows(inventory)),
       identity = as.data.frame(bind_rows(identity)))
}

aggregate_context <- function(context_id, sources, cohort, phase_cfg, check) {
  source_counts <- lapply(sources, function(x) x$counts)
  source_samples <- lapply(sources, function(x) x$samples)
  features <- rownames(source_counts[[1L]])
  if (!all(vapply(source_counts, function(x) identical(rownames(x), features), logical(1)))) {
    stop("Feature order differs within context ", context_id, call. = FALSE)
  }
  counts <- if (length(source_counts) == 1L) {
    source_counts[[1L]]
  } else do.call(Matrix::cbind2, source_counts)
  samples <- as.data.frame(bind_rows(source_samples))
  if (!identical(colnames(counts), as.character(samples$pseudobulk_id))) {
    stop("Combined count/sample order differs in context ", context_id, call. = FALSE)
  }
  donors <- sort(unique(as.character(samples$projid)))
  donor_factor <- factor(as.character(samples$projid), levels = donors)
  aggregate_map <- Matrix::sparse.model.matrix(~ 0 + donor_factor)
  broad_counts <- counts %*% aggregate_map
  colnames(broad_counts) <- donors
  rownames(broad_counts) <- features
  numeric_sum <- c("nuclei", "total_umi_count", "total_mt_count",
                   "total_mitocarta_count", "robust_flagged_nuclei")
  ag <- aggregate(samples[, numeric_sum, drop = FALSE],
                  by = list(projid = as.character(samples$projid)), FUN = sum)
  ag <- ag[match(donors, ag$projid), , drop = FALSE]
  fine <- aggregate(samples$cell_type_high_resolution,
                    by = list(projid = as.character(samples$projid)),
                    FUN = function(x) paste(sort(unique(x)), collapse = "|"))
  names(fine)[[2L]] <- "fine_cell_types"
  nprofiles <- as.data.frame(table(as.character(samples$projid)), stringsAsFactors = FALSE)
  names(nprofiles) <- c("projid", "source_fine_profiles")
  ag <- merge(ag, fine, by = "projid", all.x = TRUE, sort = FALSE)
  ag <- merge(ag, nprofiles, by = "projid", all.x = TRUE, sort = FALSE)
  ag <- ag[match(donors, ag$projid), , drop = FALSE]
  keep_cohort <- c("projid", "diagnosis", "sex", "apoe_group",
                   "age_death_scaled", "pmi_scaled", "study")
  ag <- merge(ag, cohort[, keep_cohort, drop = FALSE], by = "projid",
              all.x = TRUE, sort = FALSE)
  ag <- ag[match(donors, ag$projid), , drop = FALSE]
  if (anyNA(ag[, keep_cohort[-1L], drop = FALSE])) {
    stop("Missing donor metadata after aggregation in context ", context_id, call. = FALSE)
  }
  ag$context_id <- context_id
  ag$donor_context_id <- paste(context_id, ag$projid, sep = "::")
  ag$group_id <- make_group(ag$diagnosis, ag$sex, ag$apoe_group)
  ag$aggregate_percent_mt <- ifelse(
    ag$total_umi_count > 0, 100 * ag$total_mt_count / ag$total_umi_count, NA_real_
  )
  ag$robust_qc_fraction <- ifelse(
    ag$nuclei > 0, ag$robust_flagged_nuclei / ag$nuclei, NA_real_
  )
  ag$severe_qc_profile <- ag$robust_qc_fraction >=
    as.numeric(phase_cfg$eligibility$severe_qc_flag_fraction)
  ag$primary_eligible <- ag$nuclei >= as.integer(phase_cfg$eligibility$primary_min_nuclei)
  ag$sensitivity_eligible <- ag$nuclei >= as.integer(phase_cfg$eligibility$sensitivity_min_nuclei)
  ag$primary_ineligibility_reason <- ifelse(ag$primary_eligible, "", "nuclei_below_20")
  ag$sensitivity_ineligibility_reason <- ifelse(ag$sensitivity_eligible, "", "nuclei_below_50")
  ag$schema_version <- "phase13_donor_samples_v1"
  ag <- ag[, c("schema_version", "context_id", "donor_context_id", "projid",
               "diagnosis", "sex", "apoe_group", "group_id", "study",
               "age_death_scaled", "pmi_scaled", "nuclei", "total_umi_count",
               "total_mt_count", "aggregate_percent_mt", "total_mitocarta_count",
               "robust_flagged_nuclei", "robust_qc_fraction", "severe_qc_profile",
               "source_fine_profiles", "fine_cell_types", "primary_eligible",
               "sensitivity_eligible", "primary_ineligibility_reason",
               "sensitivity_ineligibility_reason"), drop = FALSE]
  rownames(ag) <- ag$projid
  source_total <- sum(vapply(source_counts, function(x) sum(x), numeric(1)))
  broad_total <- sum(broad_counts)
  gene_source <- Reduce(function(a, b) a + b, lapply(source_counts, Matrix::rowSums))
  gene_broad <- Matrix::rowSums(broad_counts)
  conservation <- data.frame(
    context_id = context_id,
    check_id = c("gene_wise_counts_conserved", "total_umi_conserved",
                 "nuclei_conserved", "donor_columns_match"),
    passed = c(identical(as.numeric(gene_source), as.numeric(gene_broad)),
               identical(as.numeric(source_total), as.numeric(broad_total)),
               sum(samples$nuclei) == sum(ag$nuclei),
               identical(colnames(broad_counts), ag$projid)),
    observed = c(max(abs(as.numeric(gene_source) - as.numeric(gene_broad))),
                 broad_total, sum(ag$nuclei), ncol(broad_counts)),
    expected = c(0, source_total, sum(samples$nuclei), nrow(ag)),
    stringsAsFactors = FALSE
  )
  for (i in seq_len(nrow(conservation))) {
    check(paste0(conservation$check_id[[i]], "__", context_id),
          "broad_aggregation", "context", context_id, TRUE,
          conservation$passed[[i]], conservation$observed[[i]],
          conservation$expected[[i]])
  }
  list(counts = broad_counts, samples = ag, conservation = conservation)
}

normalize_context <- function(counts, samples, phase_cfg) {
  eligible <- which(samples$primary_eligible)
  s <- samples[eligible, , drop = FALSE]
  x <- counts[, eligible, drop = FALSE]
  design <- build_design(s, unlist(phase_cfg$groups))
  rank <- qr(design)$rank
  if (rank != ncol(design)) {
    return(list(success = FALSE, reason = "not_testable_design_rank",
                samples = s, design = design, design_rank = rank))
  }
  y <- edgeR::DGEList(x)
  keep <- edgeR::filterByExpr(y, design)
  y <- y[keep, , keep.lib.sizes = FALSE]
  y <- edgeR::calcNormFactors(y, method = "TMM")
  y <- edgeR::estimateDisp(y, design, robust = TRUE)
  fit <- edgeR::glmQLFit(y, design, robust = TRUE)
  logcpm <- edgeR::cpm(y, log = TRUE,
                       prior.count = as.numeric(phase_cfg$analysis$prior_count))
  list(success = TRUE, reason = "", samples = s, design = design,
       design_rank = rank, residual_df = nrow(design) - rank,
       y = y, fit = fit, logcpm = logcpm, tested_genes = rownames(y),
       all_genes = rownames(counts))
}
gene_contrast_standard_errors <- function(norm, vectors) {
  contrast_matrix <- do.call(cbind, vectors)
  design <- norm$design
  fitted <- norm$fit$fitted.values
  dispersion <- rep_len(norm$fit$dispersion, nrow(fitted))
  ql_scale <- rep_len(norm$fit$var.post, nrow(fitted))
  out <- matrix(
    NA_real_, nrow = nrow(fitted), ncol = ncol(contrast_matrix),
    dimnames = list(rownames(fitted), colnames(contrast_matrix))
  )
  for (g in seq_len(nrow(fitted))) {
    working_weight <- fitted[g, ] / (1 + dispersion[[g]] * fitted[g, ])
    if (!is.null(norm$fit$weights)) {
      working_weight <- working_weight * norm$fit$weights[g, ]
    }
    information <- crossprod(design, design * working_weight)
    covariance <- tryCatch(solve(information), error = function(e) NULL)
    if (is.null(covariance)) next
    contrast_variance <- colSums(contrast_matrix * (covariance %*% contrast_matrix))
    out[g, ] <- sqrt(pmax(contrast_variance * ql_scale[[g]], 0)) / log(2)
  }
  out
}

gene_contrast_result <- function(norm, vector, standard_error,
                                 context_id, contrast_id, kind) {
  qlf <- edgeR::glmQLFTest(norm$fit, contrast = vector)
  tab <- qlf$table
  se <- as.numeric(standard_error[rownames(tab)])
  df_total <- as.numeric(qlf$df.total)
  critical <- stats::qt(0.975, df = df_total)
  out <- data.frame(
    context_id = context_id,
    effect_type = kind,
    effect_id = contrast_id,
    assay_feature_identifier = rownames(tab),
    log2_fold_change = as.numeric(tab$logFC),
    standard_error = se,
    ci_low = as.numeric(tab$logFC) - critical * se,
    ci_high = as.numeric(tab$logFC) + critical * se,
    ql_f_statistic = as.numeric(tab$F),
    p_value = as.numeric(tab$PValue),
    residual_df = as.numeric(df_total),
    model_status = "estimated",
    failure_reason = "",
    stringsAsFactors = FALSE
  )
  out$q_value <- stats::p.adjust(out$p_value, method = "BH")
  out
}

fit_gene_models <- function(norm, context_id, phase_cfg) {
  if (!isTRUE(norm$success)) {
    return(list(interactions = data.frame(), strata = data.frame()))
  }
  contrast_vectors <- lapply(
    phase_cfg$contrasts, contrast_vector, coefficient_names = colnames(norm$design)
  )
  names(contrast_vectors) <- vapply(
    phase_cfg$contrasts, function(x) x$contrast_id, character(1)
  )
  strata <- strata_from_config(phase_cfg)
  stratum_vectors <- lapply(
    strata, stratum_vector, coefficient_names = colnames(norm$design)
  )
  names(stratum_vectors) <- vapply(strata, function(x) x$stratum_id, character(1))
  all_vectors <- c(contrast_vectors, stratum_vectors)
  standard_errors <- gene_contrast_standard_errors(norm, all_vectors)
  interaction_rows <- lapply(seq_along(phase_cfg$contrasts), function(i) {
    x <- phase_cfg$contrasts[[i]]
    gene_contrast_result(
      norm, contrast_vectors[[i]], standard_errors[, x$contrast_id],
      context_id, x$contrast_id, "modifier"
    )
  })
  stratum_rows <- lapply(seq_along(strata), function(i) {
    x <- strata[[i]]
    gene_contrast_result(
      norm, stratum_vectors[[i]], standard_errors[, x$stratum_id],
      context_id, x$stratum_id, "AD_minus_NCI"
    )
  })
  list(
    interactions = as.data.frame(bind_rows(interaction_rows)),
    strata = as.data.frame(bind_rows(stratum_rows))
  )
}

lm_contrast_vector <- function(fit, coefficients) {
  out <- setNames(rep(0, length(stats::coef(fit))), names(stats::coef(fit)))
  prefix <- "diagnosis_sex_APOE_group"
  for (nm in names(coefficients)) {
    fit_name <- paste0(prefix, nm)
    if (!fit_name %in% names(out)) return(out * NA_real_)
    out[[fit_name]] <- as.numeric(coefficients[[nm]])
  }
  out
}

hc3_contrast <- function(fit, coefficients) {
  beta <- stats::coef(fit)
  if (anyNA(beta)) {
    return(list(success = FALSE, reason = "rank_deficient_score_model"))
  }
  vector <- lm_contrast_vector(fit, coefficients)
  if (anyNA(vector)) {
    return(list(success = FALSE, reason = "contrast_columns_missing"))
  }
  covariance <- sandwich::vcovHC(fit, type = "HC3")
  estimate <- drop(sum(vector * beta))
  variance <- drop(t(vector) %*% covariance %*% vector)
  if (!is.finite(variance) || variance < 0) {
    return(list(success = FALSE, reason = "invalid_hc3_variance"))
  }
  se <- sqrt(variance)
  df <- stats::df.residual(fit)
  if (!is.finite(se) || se <= 0 || df <= 0) {
    return(list(success = FALSE, reason = "invalid_score_standard_error"))
  }
  statistic <- estimate / se
  p <- 2 * stats::pt(abs(statistic), df = df, lower.tail = FALSE)
  critical <- stats::qt(0.975, df = df)
  list(
    success = TRUE, reason = "", estimate = estimate, se = se,
    statistic = statistic, df = df, p = p,
    ci_low = estimate - critical * se, ci_high = estimate + critical * se
  )
}

fit_score_outcome <- function(outcome, samples, phase_cfg, contrast = NULL,
                              stratum = NULL, extra_qc = FALSE) {
  d <- samples
  d$outcome <- as.numeric(outcome)
  d$diagnosis_sex_APOE_group <- factor(d$group_id, levels = unlist(phase_cfg$groups))
  d$study <- factor(d$study, levels = sort(unique(d$study)))
  formula <- if (extra_qc) {
    outcome ~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled +
      study + aggregate_percent_mt + robust_qc_fraction
  } else {
    outcome ~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled + study
  }
  fit <- tryCatch(stats::lm(formula, data = d), error = function(e) e)
  if (inherits(fit, "error")) {
    return(list(success = FALSE, reason = paste0("score_model_error:", conditionMessage(fit))))
  }
  coefficients <- if (!is.null(contrast)) {
    unlist(contrast$coefficients)
  } else {
    setNames(c(1, -1), c(stratum$ad_group, stratum$nci_group))
  }
  ans <- hc3_contrast(fit, coefficients)
  ans$fit <- fit
  ans
}

pc1_scores <- function(z, nci_index, raw_score) {
  if (length(nci_index) < 3L || nrow(z) < 2L) {
    return(list(success = FALSE, reason = "insufficient_pc1_dimensions"))
  }
  pc <- tryCatch(
    stats::prcomp(t(z[, nci_index, drop = FALSE]), center = TRUE, scale. = FALSE),
    error = function(e) e
  )
  if (inherits(pc, "error") || !ncol(pc$rotation)) {
    return(list(success = FALSE, reason = "pc1_training_failed"))
  }
  loading <- pc$rotation[, 1L]
  projected <- drop(sweep(t(z), 2L, pc$center, "-") %*% loading)
  nci_mean <- mean(projected[nci_index])
  nci_sd <- stats::sd(projected[nci_index])
  if (!is.finite(nci_sd) || nci_sd <= 0) {
    return(list(success = FALSE, reason = "pc1_nci_sd_invalid"))
  }
  standardized <- (projected - nci_mean) / nci_sd
  correlation <- suppressWarnings(stats::cor(
    standardized[nci_index], raw_score[nci_index],
    use = "complete.obs"
  ))
  orientation <- 1
  if (is.finite(correlation) && correlation < 0) {
    orientation <- -1
  } else if (is.finite(correlation) && correlation == 0) {
    first_nonzero <- which(abs(loading) > .Machine$double.eps)[1L]
    if (length(first_nonzero) && loading[[first_nonzero]] < 0) orientation <- -1
  }
  loading <- loading * orientation
  standardized <- standardized * orientation
  projected <- projected * orientation
  correlation <- suppressWarnings(stats::cor(
    standardized[nci_index], raw_score[nci_index], use = "complete.obs"
  ))
  variance_explained <- pc$sdev[[1L]]^2 / sum(pc$sdev^2)
  list(
    success = TRUE, reason = "", loading = loading, score = standardized,
    projected = projected, nci_mean = nci_mean * orientation, nci_sd = nci_sd,
    correlation = correlation, variance_explained = variance_explained,
    orientation = orientation, center = pc$center
  )
}

score_one_module <- function(norm, members, module_cfg, context_id) {
  assay <- as.character(members$assay_feature_identifier)
  measured <- assay %in% norm$all_genes
  filtered <- assay %in% norm$tested_genes
  nci_index <- which(norm$samples$diagnosis == "NCI")
  candidate <- which(filtered)
  nci_mean <- nci_sd <- rep(NA_real_, nrow(members))
  if (length(candidate)) {
    m <- norm$logcpm[assay[candidate], nci_index, drop = FALSE]
    nci_mean[candidate] <- Matrix::rowMeans(m)
    nci_sd[candidate] <- apply(m, 1L, stats::sd)
  }
  nonzero <- is.finite(nci_sd) & nci_sd > 0
  admitted <- filtered & nonzero
  admitted_count <- sum(admitted)
  reference_count <- nrow(members)
  fraction <- admitted_count / reference_count
  coverage_pass <- fraction >= as.numeric(module_cfg$minimum_fraction) &&
    admitted_count >= as.integer(module_cfg$minimum_genes)
  if (module_cfg$module_id == "mtdna_oxphos_13") {
    coverage_pass <- coverage_pass && admitted_count >= 10L
  }
  coverage <- data.frame(
    context_id = context_id, module_id = module_cfg$module_id,
    reference_genes = reference_count, measured_genes = sum(measured),
    genes_passing_expression_filter = sum(filtered),
    genes_with_nonzero_nci_sd = sum(nonzero & filtered),
    genes_used_in_score = admitted_count, coverage_fraction = fraction,
    coverage_pass = coverage_pass,
    missing_assay_genes = paste(members$frozen_gene_symbol[!measured], collapse = "|"),
    filtered_genes = paste(members$frozen_gene_symbol[measured & !filtered], collapse = "|"),
    zero_variance_genes = paste(members$frozen_gene_symbol[filtered & !nonzero], collapse = "|"),
    admitted_genes = paste(members$frozen_gene_symbol[admitted], collapse = "|"),
    admitted_assay_features = paste(assay[admitted], collapse = "|"),
    coverage_status = if (coverage_pass) "testable" else "not_testable_module_coverage",
    stringsAsFactors = FALSE
  )
  parameters <- data.frame(
    context_id = context_id, module_id = module_cfg$module_id,
    frozen_gene_symbol = members$frozen_gene_symbol,
    assay_feature_identifier = assay, measured = measured,
    passed_expression_filter = filtered, nci_mean_logcpm = nci_mean,
    nci_sd_logcpm = nci_sd, admitted = admitted,
    exclusion_reason = ifelse(
      !measured, "no_assay_match",
      ifelse(!filtered, "expression_filter", ifelse(!nonzero, "zero_nci_variance", ""))
    ),
    stringsAsFactors = FALSE
  )
  if (!coverage_pass) {
    return(list(success = FALSE, reason = "not_testable_module_coverage",
                coverage = coverage, parameters = parameters))
  }
  used_assay <- assay[admitted]
  values <- norm$logcpm[used_assay, , drop = FALSE]
  z <- sweep(values, 1L, nci_mean[admitted], "-")
  z <- sweep(z, 1L, nci_sd[admitted], "/")
  raw <- Matrix::colMeans(z)
  module_mean <- mean(raw[nci_index])
  module_sd <- stats::sd(raw[nci_index])
  if (!is.finite(module_sd) || module_sd <= 0) {
    coverage$coverage_pass <- FALSE
    coverage$coverage_status <- "not_testable_module_nci_sd"
    return(list(success = FALSE, reason = "not_testable_module_nci_sd",
                coverage = coverage, parameters = parameters))
  }
  standardized <- (raw - module_mean) / module_sd
  pc1 <- pc1_scores(z, nci_index, raw)
  pc1_value <- if (isTRUE(pc1$success)) pc1$score else rep(NA_real_, length(raw))
  scores <- data.frame(
    context_id = context_id, module_id = module_cfg$module_id,
    donor_context_id = norm$samples$donor_context_id,
    projid = norm$samples$projid, group_id = norm$samples$group_id,
    diagnosis = norm$samples$diagnosis, sex = norm$samples$sex,
    apoe_group = norm$samples$apoe_group, raw_mean_z = as.numeric(raw),
    standardized_score = as.numeric(standardized), pc1_score = as.numeric(pc1_value),
    module_mean_nci = module_mean, module_sd_nci = module_sd,
    admitted_gene_count = admitted_count, stringsAsFactors = FALSE
  )
  loadings <- if (isTRUE(pc1$success)) data.frame(
    context_id = context_id, module_id = module_cfg$module_id,
    frozen_gene_symbol = members$frozen_gene_symbol[admitted],
    assay_feature_identifier = used_assay, pc1_loading = as.numeric(pc1$loading),
    pc1_center = as.numeric(pc1$center), nci_training_donors = length(nci_index),
    pc1_nci_mean = pc1$nci_mean, pc1_nci_sd = pc1$nci_sd,
    orientation = pc1$orientation, nci_mean_z_pc1_correlation = pc1$correlation,
    variance_explained_pc1 = pc1$variance_explained, stringsAsFactors = FALSE
  ) else data.frame()
  reliability <- data.frame(
    context_id = context_id, module_id = module_cfg$module_id,
    pc1_success = isTRUE(pc1$success),
    pc1_failure_reason = pc1$reason %||% "",
    nci_mean_z_pc1_correlation = if (isTRUE(pc1$success)) pc1$correlation else NA_real_,
    variance_explained_pc1 = if (isTRUE(pc1$success)) pc1$variance_explained else NA_real_,
    pc1_reliable = isTRUE(pc1$success) && abs(pc1$correlation) >= 0.70,
    omission_units = NA_integer_, omission_sign_reversals = NA_integer_,
    omission_fraction_retain_half_magnitude = NA_real_,
    most_influential_omission = NA_character_, stringsAsFactors = FALSE
  )
  list(
    success = TRUE, reason = "", coverage = coverage, parameters = parameters,
    admitted = members[admitted, , drop = FALSE], z = z,
    raw = raw, standardized = standardized, scores = scores,
    pc1 = pc1, loadings = loadings, reliability = reliability
  )
}

model_result_row <- function(test_id, context_id, contrast, module_cfg,
                             counts20, counts50, coverage, primary, pc1,
                             norm, eligibility_status) {
  base <- data.frame(
    test_id = test_id, context_id = context_id,
    contrast_order = as.integer(contrast$contrast_order),
    contrast_id = contrast$contrast_id, modifier = contrast$modifier,
    module_order = as.integer(module_cfg$module_order),
    module_id = module_cfg$module_id, module_role = module_cfg$role,
    group_1 = contrast$required_groups[[1L]],
    group_2 = contrast$required_groups[[2L]],
    group_3 = contrast$required_groups[[3L]],
    group_4 = contrast$required_groups[[4L]],
    group_1_donors = counts20[[1L]], group_2_donors = counts20[[2L]],
    group_3_donors = counts20[[3L]], group_4_donors = counts20[[4L]],
    group_1_donors_threshold50 = counts50[[1L]],
    group_2_donors_threshold50 = counts50[[2L]],
    group_3_donors_threshold50 = counts50[[3L]],
    group_4_donors_threshold50 = counts50[[4L]],
    minimum_group_donors = min(counts20),
    coverage_fraction = coverage$coverage_fraction,
    admitted_genes = coverage$genes_used_in_score,
    coverage_pass = coverage$coverage_pass,
    design_rank = norm$design_rank, residual_df = norm$residual_df %||% NA_integer_,
    eligibility_status = eligibility_status,
    model_status = if (isTRUE(primary$success)) "estimated" else eligibility_status,
    failure_reason = if (isTRUE(primary$success)) "" else primary$reason %||% eligibility_status,
    estimate = if (isTRUE(primary$success)) primary$estimate else NA_real_,
    robust_se = if (isTRUE(primary$success)) primary$se else NA_real_,
    ci_low = if (isTRUE(primary$success)) primary$ci_low else NA_real_,
    ci_high = if (isTRUE(primary$success)) primary$ci_high else NA_real_,
    t_statistic = if (isTRUE(primary$success)) primary$statistic else NA_real_,
    p_value = if (isTRUE(primary$success)) primary$p else NA_real_,
    pc1_estimate = if (isTRUE(pc1$success)) pc1$estimate else NA_real_,
    pc1_robust_se = if (isTRUE(pc1$success)) pc1$se else NA_real_,
    pc1_ci_low = if (isTRUE(pc1$success)) pc1$ci_low else NA_real_,
    pc1_ci_high = if (isTRUE(pc1$success)) pc1$ci_high else NA_real_,
    pc1_p_value = if (isTRUE(pc1$success)) pc1$p else NA_real_,
    stringsAsFactors = FALSE
  )
  base$q_value <- NA_real_
  base
}

analyze_context <- function(context_id, broad, module_members, phase_cfg, check) {
  norm <- normalize_context(broad$counts, broad$samples, phase_cfg)
  check(paste0("design_full_rank__", context_id), "primary_models", "context", context_id,
        TRUE, isTRUE(norm$success), norm$design_rank,
        if (!is.null(norm$design)) ncol(norm$design) else NA_integer_,
        norm$reason %||% "")
  if (!isTRUE(norm$success)) stop("Primary design failed in ", context_id, call. = FALSE)
  check(paste0("full_transcriptome_normalization__", context_id), "primary_models",
        "context", context_id, TRUE, nrow(broad$counts) > nrow(module_members),
        nrow(broad$counts), paste0(">", nrow(module_members)))
  genes <- fit_gene_models(norm, context_id, phase_cfg)
  coverage_rows <- list()
  parameter_rows <- list()
  score_rows <- list()
  loading_rows <- list()
  reliability_rows <- list()
  result_rows <- list()
  stratum_rows <- list()
  test_manifest_rows <- list()
  module_objects <- list()
  for (module_cfg in phase_cfg$modules) {
    module_id <- module_cfg$module_id
    members <- module_members[module_members$module_id == module_id, , drop = FALSE]
    scored <- score_one_module(norm, members, module_cfg, context_id)
    module_objects[[module_id]] <- scored
    coverage_rows[[length(coverage_rows) + 1L]] <- scored$coverage
    parameter_rows[[length(parameter_rows) + 1L]] <- scored$parameters
    if (isTRUE(scored$success)) {
      score_rows[[length(score_rows) + 1L]] <- scored$scores
      loading_rows[[length(loading_rows) + 1L]] <- scored$loadings
      reliability_rows[[length(reliability_rows) + 1L]] <- scored$reliability
      for (stratum in strata_from_config(phase_cfg)) {
        sr <- fit_score_outcome(scored$standardized, norm$samples, phase_cfg,
                                stratum = stratum)
        stratum_rows[[length(stratum_rows) + 1L]] <- data.frame(
          context_id = context_id, module_id = module_id,
          stratum_order = stratum$stratum_order, stratum_id = stratum$stratum_id,
          estimate = if (isTRUE(sr$success)) sr$estimate else NA_real_,
          robust_se = if (isTRUE(sr$success)) sr$se else NA_real_,
          ci_low = if (isTRUE(sr$success)) sr$ci_low else NA_real_,
          ci_high = if (isTRUE(sr$success)) sr$ci_high else NA_real_,
          p_value = if (isTRUE(sr$success)) sr$p else NA_real_,
          model_status = if (isTRUE(sr$success)) "estimated" else "failed",
          failure_reason = sr$reason %||% "", stringsAsFactors = FALSE
        )
      }
    } else {
      reliability_rows[[length(reliability_rows) + 1L]] <- data.frame(
        context_id = context_id, module_id = module_id, pc1_success = FALSE,
        pc1_failure_reason = scored$reason,
        nci_mean_z_pc1_correlation = NA_real_, variance_explained_pc1 = NA_real_,
        pc1_reliable = FALSE, omission_units = NA_integer_,
        omission_sign_reversals = NA_integer_,
        omission_fraction_retain_half_magnitude = NA_real_,
        most_influential_omission = NA_character_, stringsAsFactors = FALSE
      )
      for (stratum in strata_from_config(phase_cfg)) {
        stratum_rows[[length(stratum_rows) + 1L]] <- data.frame(
          context_id = context_id, module_id = module_id,
          stratum_order = stratum$stratum_order, stratum_id = stratum$stratum_id,
          estimate = NA_real_, robust_se = NA_real_, ci_low = NA_real_,
          ci_high = NA_real_, p_value = NA_real_, model_status = "not_testable",
          failure_reason = scored$reason, stringsAsFactors = FALSE
        )
      }
    }
    for (contrast in phase_cfg$contrasts) {
      counts20 <- required_group_counts(
        broad$samples, contrast, as.integer(phase_cfg$eligibility$primary_min_nuclei)
      )
      counts50 <- required_group_counts(
        broad$samples, contrast, as.integer(phase_cfg$eligibility$sensitivity_min_nuclei)
      )
      eligibility <- if (min(counts20) < as.integer(
        phase_cfg$eligibility$minimum_estimable_donors_per_group
      )) {
        "not_testable_low_donor_count"
      } else if (!isTRUE(scored$success)) scored$reason else "eligible"
      test_id <- paste(context_id, contrast$contrast_id, module_id, sep = "::")
      primary <- list(success = FALSE, reason = eligibility)
      pc1_result <- list(success = FALSE, reason = eligibility)
      if (eligibility == "eligible") {
        primary <- fit_score_outcome(
          scored$standardized, norm$samples, phase_cfg, contrast = contrast
        )
        if (isTRUE(scored$pc1$success)) {
          pc1_result <- fit_score_outcome(
            scored$pc1$score, norm$samples, phase_cfg, contrast = contrast
          )
        } else pc1_result$reason <- scored$pc1$reason
      }
      result_rows[[length(result_rows) + 1L]] <- model_result_row(
        test_id, context_id, contrast, module_cfg, counts20, counts50,
        scored$coverage, primary, pc1_result, norm, eligibility
      )
      test_manifest_rows[[length(test_manifest_rows) + 1L]] <- data.frame(
        test_id = test_id, context_id = context_id,
        contrast_order = as.integer(contrast$contrast_order),
        contrast_id = contrast$contrast_id, modifier = contrast$modifier,
        module_order = as.integer(module_cfg$module_order), module_id = module_id,
        group_1 = contrast$required_groups[[1L]],
        group_2 = contrast$required_groups[[2L]],
        group_3 = contrast$required_groups[[3L]],
        group_4 = contrast$required_groups[[4L]],
        group_1_donors = counts20[[1L]], group_2_donors = counts20[[2L]],
        group_3_donors = counts20[[3L]], group_4_donors = counts20[[4L]],
        group_1_nuclei = sum(broad$samples$nuclei[
          broad$samples$nuclei >= 20 & broad$samples$group_id == contrast$required_groups[[1L]]
        ]),
        group_2_nuclei = sum(broad$samples$nuclei[
          broad$samples$nuclei >= 20 & broad$samples$group_id == contrast$required_groups[[2L]]
        ]),
        group_3_nuclei = sum(broad$samples$nuclei[
          broad$samples$nuclei >= 20 & broad$samples$group_id == contrast$required_groups[[3L]]
        ]),
        group_4_nuclei = sum(broad$samples$nuclei[
          broad$samples$nuclei >= 20 & broad$samples$group_id == contrast$required_groups[[4L]]
        ]),
        threshold50_minimum_group_donors = min(counts50),
        coverage_fraction = scored$coverage$coverage_fraction,
        coverage_pass = scored$coverage$coverage_pass,
        eligibility_status = eligibility, stringsAsFactors = FALSE
      )
    }
  }
  results <- as.data.frame(bind_rows(result_rows))
  testable <- is.finite(results$p_value)
  results$q_value[testable] <- stats::p.adjust(results$p_value[testable], method = "BH")
  diagnostics <- data.frame(
    context_id = context_id, donor_profiles = nrow(norm$samples),
    genes_before_filter = nrow(broad$counts), genes_after_filter = nrow(norm$y),
    design_columns = ncol(norm$design), design_rank = norm$design_rank,
    residual_df = norm$residual_df,
    study_levels = paste(levels(factor(norm$samples$study)), collapse = "|"),
    tmm_factors = paste(
      paste(norm$samples$projid, signif(norm$y$samples$norm.factors, 8), sep = "="),
      collapse = "|"
    ),
    common_dispersion = norm$y$common.dispersion,
    trended_dispersion_median = stats::median(norm$y$trended.dispersion, na.rm = TRUE),
    model_status = "estimated", failure_reason = "", stringsAsFactors = FALSE
  )
  list(
    norm = norm, genes = genes,
    coverage = as.data.frame(bind_rows(coverage_rows)),
    parameters = as.data.frame(bind_rows(parameter_rows)),
    scores = as.data.frame(bind_rows(score_rows)),
    loadings = as.data.frame(bind_rows(loading_rows)),
    reliability = as.data.frame(bind_rows(reliability_rows)),
    results = results, strata = as.data.frame(bind_rows(stratum_rows)),
    test_manifest = as.data.frame(bind_rows(test_manifest_rows)),
    diagnostics = diagnostics, modules = module_objects
  )
}

run_camera_context <- function(context_id, analysis, phase_cfg) {
  norm <- analysis$norm
  v <- limma::voom(norm$y, norm$design, plot = FALSE)
  rows <- list()
  for (i in seq_len(nrow(analysis$results))) {
    primary <- analysis$results[i, , drop = FALSE]
    module <- analysis$modules[[primary$module_id]]
    contrast <- phase_cfg$contrasts[[which(vapply(
      phase_cfg$contrasts, function(x) identical(x$contrast_id, primary$contrast_id),
      logical(1)
    ))]]
    base <- data.frame(
      test_id = primary$test_id, context_id = context_id,
      contrast_order = primary$contrast_order, contrast_id = primary$contrast_id,
      modifier = primary$modifier, module_order = primary$module_order,
      module_id = primary$module_id, module_role = primary$module_role,
      module_genes = primary$admitted_genes,
      background_genes = nrow(v$E), inter_gene_correlation = NA_real_,
      direction = NA_character_, p_value = NA_real_, q_value = NA_real_,
      camera_status = primary$eligibility_status, failure_reason = "",
      stringsAsFactors = FALSE
    )
    if (primary$eligibility_status != "eligible" || !isTRUE(module$success)) {
      base$failure_reason <- primary$failure_reason
      rows[[length(rows) + 1L]] <- base
      next
    }
    idx <- match(module$admitted$assay_feature_identifier, rownames(v$E))
    idx <- idx[!is.na(idx)]
    cor_info <- tryCatch(
      limma::interGeneCorrelation(v$E[idx, , drop = FALSE], norm$design),
      error = function(e) e
    )
    if (inherits(cor_info, "error")) {
      base$camera_status <- "failed"
      base$failure_reason <- paste0("inter_gene_correlation:", conditionMessage(cor_info))
      rows[[length(rows) + 1L]] <- base
      next
    }
    cvec <- contrast_vector(contrast, colnames(norm$design))
    cam <- tryCatch(limma::camera(
      v$E, index = idx, design = norm$design, contrast = cvec,
      weights = v$weights, allow.neg.cor = FALSE,
      inter.gene.cor = as.numeric(cor_info$correlation), sort = FALSE
    ), error = function(e) e)
    if (inherits(cam, "error")) {
      base$camera_status <- "failed"
      base$failure_reason <- paste0("camera:", conditionMessage(cam))
    } else {
      base$inter_gene_correlation <- as.numeric(cor_info$correlation)
      base$direction <- as.character(cam$Direction[[1L]])
      base$p_value <- as.numeric(cam$PValue[[1L]])
      base$camera_status <- "estimated"
    }
    rows[[length(rows) + 1L]] <- base
  }
  as.data.frame(bind_rows(rows))
}
fixed_module_scores <- function(counts, samples, analysis, phase_cfg) {
  tested <- analysis$norm$tested_genes
  y <- edgeR::DGEList(counts[tested, , drop = FALSE])
  y <- edgeR::calcNormFactors(y, method = "TMM")
  logcpm <- edgeR::cpm(
    y, log = TRUE, prior.count = as.numeric(phase_cfg$analysis$prior_count)
  )
  nci <- which(samples$diagnosis == "NCI")
  out <- list()
  for (module_id in names(analysis$modules)) {
    module <- analysis$modules[[module_id]]
    if (!isTRUE(module$success)) {
      out[[module_id]] <- list(success = FALSE, reason = module$reason)
      next
    }
    assay <- module$admitted$assay_feature_identifier
    values <- logcpm[assay, , drop = FALSE]
    means <- Matrix::rowMeans(values[, nci, drop = FALSE])
    sds <- apply(values[, nci, drop = FALSE], 1L, stats::sd)
    if (any(!is.finite(sds) | sds <= 0)) {
      out[[module_id]] <- list(success = FALSE, reason = "resample_zero_nci_variance")
      next
    }
    z <- sweep(values, 1L, means, "-")
    z <- sweep(z, 1L, sds, "/")
    raw <- Matrix::colMeans(z)
    module_sd <- stats::sd(raw[nci])
    if (!is.finite(module_sd) || module_sd <= 0) {
      out[[module_id]] <- list(success = FALSE, reason = "resample_module_nci_sd")
      next
    }
    out[[module_id]] <- list(
      success = TRUE, score = (raw - mean(raw[nci])) / module_sd, z = z
    )
  }
  out
}

stability_record <- function(primary, analysis_type, repetition, fit,
                             seed = NA_integer_, omitted_donor = "",
                             omitted_unit = "", sampled_donors = "") {
  data.frame(
    test_id = primary$test_id, context_id = primary$context_id,
    contrast_id = primary$contrast_id, module_id = primary$module_id,
    analysis_type = analysis_type, repetition = as.integer(repetition),
    seed = as.integer(seed), omitted_donor = as.character(omitted_donor),
    omitted_unit = as.character(omitted_unit),
    sampled_donors = as.character(sampled_donors),
    estimate = if (isTRUE(fit$success)) fit$estimate else NA_real_,
    standard_error = if (isTRUE(fit$success)) fit$se else NA_real_,
    fit_success = isTRUE(fit$success),
    failure_reason = fit$reason %||% "", stringsAsFactors = FALSE
  )
}

fit_resampled_rows <- function(scores, samples, analysis, phase_cfg,
                               analysis_type, repetition, seed = NA_integer_,
                               omitted_donor = "", sampled_donors = "") {
  rows <- list()
  eligible <- analysis$results$eligibility_status == "eligible"
  primary_rows <- analysis$results[eligible, , drop = FALSE]
  for (i in seq_len(nrow(primary_rows))) {
    primary <- primary_rows[i, , drop = FALSE]
    module_score <- scores[[primary$module_id]]
    contrast <- phase_cfg$contrasts[[which(vapply(
      phase_cfg$contrasts, function(x) identical(x$contrast_id, primary$contrast_id),
      logical(1)
    ))]]
    fit <- if (isTRUE(module_score$success)) {
      fit_score_outcome(module_score$score, samples, phase_cfg, contrast = contrast)
    } else list(success = FALSE, reason = module_score$reason)
    rows[[length(rows) + 1L]] <- stability_record(
      primary, analysis_type, repetition, fit, seed,
      omitted_donor = omitted_donor, sampled_donors = sampled_donors
    )
  }
  as.data.frame(bind_rows(rows))
}

omission_units_for_module <- function(module) {
  admitted <- module$admitted
  module_id <- unique(admitted$module_id)
  if (module_id %in% c("mtdna_oxphos_13", "mib_micos_inner_membrane_19")) {
    return(setNames(
      lapply(seq_len(nrow(admitted)), function(i) i),
      paste0("gene:", admitted$frozen_gene_symbol)
    ))
  }
  if (module_id == "nuclear_oxphos_structural_86") {
    units <- sort(unique(admitted$respiratory_complex))
    return(setNames(lapply(units, function(x) which(admitted$respiratory_complex == x)),
                    paste0("complex_", units)))
  }
  categories <- c(
    "mitochondrial_ribosome", "ribosome_assembly", "translation_factors",
    "mt_trna_synthetases", "fmet_processing", "parent_only_genes"
  )
  setNames(lapply(categories, function(category) {
    which(vapply(strsplit(admitted$omission_category, "|", fixed = TRUE),
                 function(x) category %in% x, logical(1)))
  }), categories)
}

run_omission_sensitivity <- function(analysis, phase_cfg) {
  rows <- list()
  eligible <- analysis$results$eligibility_status == "eligible"
  primary_rows <- analysis$results[eligible, , drop = FALSE]
  nci <- which(analysis$norm$samples$diagnosis == "NCI")
  for (module_id in names(analysis$modules)) {
    module <- analysis$modules[[module_id]]
    if (!isTRUE(module$success)) next
    units <- omission_units_for_module(module)
    module_primary <- primary_rows[primary_rows$module_id == module_id, , drop = FALSE]
    for (unit_name in names(units)) {
      keep <- setdiff(seq_len(nrow(module$z)), units[[unit_name]])
      if (length(keep) < 2L) {
        omitted_scores <- list(success = FALSE, reason = "too_few_genes_after_omission")
      } else {
        raw <- Matrix::colMeans(module$z[keep, , drop = FALSE])
        scale <- stats::sd(raw[nci])
        omitted_scores <- if (!is.finite(scale) || scale <= 0) {
          list(success = FALSE, reason = "omission_nci_sd_invalid")
        } else list(success = TRUE, score = (raw - mean(raw[nci])) / scale)
      }
      for (i in seq_len(nrow(module_primary))) {
        primary <- module_primary[i, , drop = FALSE]
        contrast <- phase_cfg$contrasts[[which(vapply(
          phase_cfg$contrasts,
          function(x) identical(x$contrast_id, primary$contrast_id), logical(1)
        ))]]
        fit <- if (isTRUE(omitted_scores$success)) {
          fit_score_outcome(omitted_scores$score, analysis$norm$samples,
                            phase_cfg, contrast = contrast)
        } else list(success = FALSE, reason = omitted_scores$reason)
        rows[[length(rows) + 1L]] <- stability_record(
          primary, "gene_concentration_omission", match(unit_name, names(units)),
          fit, omitted_unit = unit_name
        )
      }
    }
  }
  as.data.frame(bind_rows(rows))
}

run_stability_context <- function(context_id, broad, analysis, phase_cfg, pilot,
                                  workers = 1L) {
  rows <- list()
  samples <- analysis$norm$samples
  counts <- broad$counts[, samples$projid, drop = FALSE]
  repetitions_boot <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_bootstrap_repetitions)
  } else as.integer(phase_cfg$stability$production_bootstrap_repetitions)
  repetitions_balance <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_balance_repetitions)
  } else as.integer(phase_cfg$stability$production_balance_repetitions)

  cat("Phase 13 stability ", context_id, ": ", repetitions_boot,
      " stratified bootstrap repetitions\n", sep = "")
  bootstrap_one <- function(rep) {
    seed <- seed_for(phase_cfg, paste(context_id, "bootstrap", rep, sep = "::"))
    set.seed(seed)
    selected <- unlist(lapply(unlist(phase_cfg$groups), function(group) {
      idx <- which(samples$group_id == group)
      sample(idx, length(idx), replace = TRUE)
    }), use.names = FALSE)
    boot_samples <- samples[selected, , drop = FALSE]
    boot_samples$projid <- paste0(boot_samples$projid, "__boot", seq_along(selected))
    boot_counts <- counts[, selected, drop = FALSE]
    colnames(boot_counts) <- boot_samples$projid
    scores <- tryCatch(
      fixed_module_scores(boot_counts, boot_samples, analysis, phase_cfg),
      error = function(e) e
    )
    if (inherits(scores, "error")) {
      fail <- lapply(names(analysis$modules), function(x) {
        list(success = FALSE, reason = paste0("bootstrap:", conditionMessage(scores)))
      })
      names(fail) <- names(analysis$modules)
      scores <- fail
    }
    fit_resampled_rows(
      scores, boot_samples, analysis, phase_cfg, "donor_bootstrap", rep, seed,
      sampled_donors = paste(samples$projid[selected], collapse = "|")
    )
  }
  rows[[length(rows) + 1L]] <- as.data.frame(bind_rows(parallel_lapply_ordered(
    as.list(seq_len(repetitions_boot)), bootstrap_one, workers, "donor bootstrap"
  )))

  cat("Phase 13 stability ", context_id, ": leave-one-donor-out\n", sep = "")
  loo_one <- function(j) {
    keep <- setdiff(seq_len(nrow(samples)), j)
    loo_samples <- samples[keep, , drop = FALSE]
    loo_counts <- counts[, keep, drop = FALSE]
    scores <- tryCatch(
      fixed_module_scores(loo_counts, loo_samples, analysis, phase_cfg),
      error = function(e) e
    )
    if (inherits(scores, "error")) {
      fail <- lapply(names(analysis$modules), function(x) {
        list(success = FALSE, reason = paste0("loo:", conditionMessage(scores)))
      })
      names(fail) <- names(analysis$modules)
      scores <- fail
    }
    fit_resampled_rows(
      scores, loo_samples, analysis, phase_cfg, "leave_one_donor_out", j,
      omitted_donor = samples$projid[[j]]
    )
  }
  rows[[length(rows) + 1L]] <- as.data.frame(bind_rows(parallel_lapply_ordered(
    as.list(seq_len(nrow(samples))), loo_one, workers, "leave-one-donor-out"
  )))

  cat("Phase 13 stability ", context_id, ": ", repetitions_balance,
      " balanced repetitions per eligible contrast\n", sep = "")
  balance_tasks <- list()
  for (contrast_index in seq_along(phase_cfg$contrasts)) {
    contrast <- phase_cfg$contrasts[[contrast_index]]
    counts_by_group <- table(factor(samples$group_id,
                                    levels = unlist(contrast$required_groups)))
    if (min(counts_by_group) < as.integer(
      phase_cfg$eligibility$minimum_estimable_donors_per_group
    )) next
    for (rep in seq_len(repetitions_balance)) {
      balance_tasks[[length(balance_tasks) + 1L]] <- list(
        contrast_index = contrast_index, repetition = rep,
        smallest = as.integer(min(counts_by_group))
      )
    }
  }
  balance_one <- function(task) {
    contrast <- phase_cfg$contrasts[[task$contrast_index]]
    rep <- task$repetition
    smallest <- task$smallest
    seed <- seed_for(
      phase_cfg, paste(context_id, contrast$contrast_id, "balance", rep, sep = "::")
    )
    set.seed(seed)
    required <- unlist(contrast$required_groups)
    selected_required <- unlist(lapply(required, function(group) {
      sample(which(samples$group_id == group), smallest, replace = FALSE)
    }), use.names = FALSE)
    selected_other <- which(!samples$group_id %in% required)
    selected <- sort(c(selected_required, selected_other))
    bal_samples <- samples[selected, , drop = FALSE]
    bal_counts <- counts[, selected, drop = FALSE]
    scores <- tryCatch(
      fixed_module_scores(bal_counts, bal_samples, analysis, phase_cfg),
      error = function(e) e
    )
    if (inherits(scores, "error")) {
      fail <- lapply(names(analysis$modules), function(x) {
        list(success = FALSE, reason = paste0("balance:", conditionMessage(scores)))
      })
      names(fail) <- names(analysis$modules)
      scores <- fail
    }
    module_rows <- analysis$results[
      analysis$results$eligibility_status == "eligible" &
        analysis$results$contrast_id == contrast$contrast_id, , drop = FALSE
    ]
    local_rows <- list()
    for (i in seq_len(nrow(module_rows))) {
      primary <- module_rows[i, , drop = FALSE]
      score <- scores[[primary$module_id]]
      fit <- if (isTRUE(score$success)) {
        fit_score_outcome(score$score, bal_samples, phase_cfg, contrast = contrast)
      } else list(success = FALSE, reason = score$reason)
      local_rows[[length(local_rows) + 1L]] <- stability_record(
        primary, "group_size_balanced", rep, fit, seed,
        sampled_donors = paste(samples$projid[selected], collapse = "|")
      )
    }
    as.data.frame(bind_rows(local_rows))
  }
  rows[[length(rows) + 1L]] <- as.data.frame(bind_rows(parallel_lapply_ordered(
    balance_tasks, balance_one, workers, "group-size-balanced resampling"
  )))

  threshold <- as.integer(phase_cfg$eligibility$sensitivity_min_nuclei)
  threshold_idx <- which(broad$samples$nuclei >= threshold)
  threshold_samples <- broad$samples[threshold_idx, , drop = FALSE]
  threshold_counts <- broad$counts[, threshold_idx, drop = FALSE]
  threshold_scores <- tryCatch(
    fixed_module_scores(threshold_counts, threshold_samples, analysis, phase_cfg),
    error = function(e) e
  )
  eligible_rows <- analysis$results[analysis$results$eligibility_status == "eligible", ,
                                    drop = FALSE]
  for (i in seq_len(nrow(eligible_rows))) {
    primary <- eligible_rows[i, , drop = FALSE]
    contrast <- phase_cfg$contrasts[[which(vapply(
      phase_cfg$contrasts, function(x) identical(x$contrast_id, primary$contrast_id),
      logical(1)
    ))]]
    n50 <- required_group_counts(broad$samples, contrast, threshold)
    fit <- if (min(n50) < as.integer(
      phase_cfg$eligibility$minimum_estimable_donors_per_group
    )) {
      list(success = FALSE, reason = "not_testable_threshold50")
    } else if (inherits(threshold_scores, "error")) {
      list(success = FALSE, reason = paste0("threshold50:", conditionMessage(threshold_scores)))
    } else if (!isTRUE(threshold_scores[[primary$module_id]]$success)) {
      list(success = FALSE, reason = threshold_scores[[primary$module_id]]$reason)
    } else {
      fit_score_outcome(threshold_scores[[primary$module_id]]$score,
                        threshold_samples, phase_cfg, contrast = contrast)
    }
    rows[[length(rows) + 1L]] <- stability_record(
      primary, "threshold50", 1L, fit
    )
  }

  for (i in seq_len(nrow(eligible_rows))) {
    primary <- eligible_rows[i, , drop = FALSE]
    contrast <- phase_cfg$contrasts[[which(vapply(
      phase_cfg$contrasts, function(x) identical(x$contrast_id, primary$contrast_id),
      logical(1)
    ))]]
    module <- analysis$modules[[primary$module_id]]
    pc_fit <- if (isTRUE(module$pc1$success)) {
      fit_score_outcome(module$pc1$score, samples, phase_cfg, contrast = contrast)
    } else list(success = FALSE, reason = module$pc1$reason)
    rows[[length(rows) + 1L]] <- stability_record(primary, "pc1", 1L, pc_fit)
    qc_fit <- fit_score_outcome(module$standardized, samples, phase_cfg,
                                contrast = contrast, extra_qc = TRUE)
    rows[[length(rows) + 1L]] <- stability_record(
      primary, "mitochondrial_qc_covariates", 1L, qc_fit
    )
  }

  severe_keep <- which(
    broad$samples$primary_eligible & !broad$samples$severe_qc_profile
  )
  severe_samples <- broad$samples[severe_keep, , drop = FALSE]
  severe_counts <- broad$counts[, severe_keep, drop = FALSE]
  severe_scores <- tryCatch(
    fixed_module_scores(severe_counts, severe_samples, analysis, phase_cfg),
    error = function(e) e
  )
  for (i in seq_len(nrow(eligible_rows))) {
    primary <- eligible_rows[i, , drop = FALSE]
    contrast <- phase_cfg$contrasts[[which(vapply(
      phase_cfg$contrasts, function(x) identical(x$contrast_id, primary$contrast_id),
      logical(1)
    ))]]
    n_severe <- table(factor(severe_samples$group_id,
                             levels = unlist(contrast$required_groups)))
    fit <- if (min(n_severe) < as.integer(
      phase_cfg$eligibility$minimum_estimable_donors_per_group
    )) {
      list(success = FALSE, reason = "not_testable_severe_qc_exclusion")
    } else if (inherits(severe_scores, "error")) {
      list(success = FALSE, reason = paste0("severe_qc:", conditionMessage(severe_scores)))
    } else if (!isTRUE(severe_scores[[primary$module_id]]$success)) {
      list(success = FALSE, reason = severe_scores[[primary$module_id]]$reason)
    } else {
      fit_score_outcome(severe_scores[[primary$module_id]]$score,
                        severe_samples, phase_cfg, contrast = contrast)
    }
    rows[[length(rows) + 1L]] <- stability_record(
      primary, "severe_qc_exclusion", 1L, fit
    )
  }

  rows[[length(rows) + 1L]] <- run_omission_sensitivity(analysis, phase_cfg)
  as.data.frame(bind_rows(rows))
}
summarize_stability <- function(primary_results, replicates, phase_cfg, pilot,
                                donor_counts_by_context) {
  boot_expected <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_bootstrap_repetitions)
  } else as.integer(phase_cfg$stability$production_bootstrap_repetitions)
  balance_expected <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_balance_repetitions)
  } else as.integer(phase_cfg$stability$production_balance_repetitions)
  rows <- list()
  get_type <- function(x, type) x[x$analysis_type == type, , drop = FALSE]
  direction_fraction <- function(x, estimate) {
    ok <- x$fit_success & is.finite(x$estimate)
    if (!any(ok) || !is.finite(estimate) || estimate == 0) return(NA_real_)
    mean(x$estimate[ok] * estimate > 0)
  }
  single_estimate <- function(x) {
    if (!nrow(x) || !isTRUE(x$fit_success[[1L]])) NA_real_ else x$estimate[[1L]]
  }
  for (i in seq_len(nrow(primary_results))) {
    primary <- primary_results[i, , drop = FALSE]
    x <- replicates[replicates$test_id == primary$test_id, , drop = FALSE]
    boot <- get_type(x, "donor_bootstrap")
    loo <- get_type(x, "leave_one_donor_out")
    balance <- get_type(x, "group_size_balanced")
    threshold <- get_type(x, "threshold50")
    pc1 <- get_type(x, "pc1")
    qc <- get_type(x, "mitochondrial_qc_covariates")
    severe <- get_type(x, "severe_qc_exclusion")
    omission <- get_type(x, "gene_concentration_omission")
    boot_ok <- boot$fit_success & is.finite(boot$estimate)
    loo_ok <- loo$fit_success & is.finite(loo$estimate)
    balance_ok <- balance$fit_success & is.finite(balance$estimate)
    omission_ok <- omission$fit_success & is.finite(omission$estimate)
    loo_change <- if (any(loo_ok) && is.finite(primary$estimate)) {
      abs(loo$estimate[loo_ok] - primary$estimate)
    } else numeric()
    loo_donors <- loo$omitted_donor[loo_ok]
    omission_change <- if (any(omission_ok) && is.finite(primary$estimate)) {
      abs(omission$estimate[omission_ok] - primary$estimate)
    } else numeric()
    omission_units <- omission$omitted_unit[omission_ok]
    rows[[length(rows) + 1L]] <- data.frame(
      test_id = primary$test_id, context_id = primary$context_id,
      contrast_id = primary$contrast_id, module_id = primary$module_id,
      primary_estimate = primary$estimate,
      bootstrap_planned = if (primary$eligibility_status == "eligible") boot_expected else 0L,
      bootstrap_successful = sum(boot_ok),
      bootstrap_median = if (any(boot_ok)) stats::median(boot$estimate[boot_ok]) else NA_real_,
      bootstrap_ci_low = if (any(boot_ok)) {
        stats::quantile(boot$estimate[boot_ok], 0.025, names = FALSE)
      } else NA_real_,
      bootstrap_ci_high = if (any(boot_ok)) {
        stats::quantile(boot$estimate[boot_ok], 0.975, names = FALSE)
      } else NA_real_,
      bootstrap_same_direction_fraction = direction_fraction(boot, primary$estimate),
      bootstrap_valid = sum(boot_ok) >= ceiling(
        boot_expected * as.numeric(phase_cfg$stability$minimum_success_fraction)
      ),
      loo_planned = if (primary$eligibility_status == "eligible") {
        donor_counts_by_context[[primary$context_id]]
      } else 0L,
      loo_successful = sum(loo_ok),
      loo_sign_reversals = if (any(loo_ok) && is.finite(primary$estimate)) {
        sum(loo$estimate[loo_ok] * primary$estimate < 0)
      } else NA_integer_,
      loo_largest_change_donor = if (length(loo_change)) {
        loo_donors[[which.max(loo_change)]]
      } else NA_character_,
      loo_largest_absolute_change = if (length(loo_change)) max(loo_change) else NA_real_,
      loo_minimum_estimate = if (any(loo_ok)) min(loo$estimate[loo_ok]) else NA_real_,
      loo_maximum_estimate = if (any(loo_ok)) max(loo$estimate[loo_ok]) else NA_real_,
      balance_planned = if (primary$eligibility_status == "eligible") balance_expected else 0L,
      balance_successful = sum(balance_ok),
      balance_same_direction_fraction = direction_fraction(balance, primary$estimate),
      balance_valid = sum(balance_ok) >= ceiling(
        balance_expected * as.numeric(phase_cfg$stability$minimum_success_fraction)
      ),
      threshold50_estimate = single_estimate(threshold),
      threshold50_status = if (!nrow(threshold)) "not_run" else if (
        isTRUE(threshold$fit_success[[1L]])
      ) "estimated" else threshold$failure_reason[[1L]],
      threshold50_agrees = if (is.finite(single_estimate(threshold)) &&
                               is.finite(primary$estimate)) {
        single_estimate(threshold) * primary$estimate > 0 &&
          abs(single_estimate(threshold)) >= 0.5 * abs(primary$estimate)
      } else FALSE,
      pc1_estimate = single_estimate(pc1),
      pc1_status = if (!nrow(pc1)) "not_run" else if (
        isTRUE(pc1$fit_success[[1L]])
      ) "estimated" else pc1$failure_reason[[1L]],
      pc1_agrees = if (is.finite(single_estimate(pc1)) && is.finite(primary$estimate)) {
        single_estimate(pc1) * primary$estimate > 0 &&
          abs(single_estimate(pc1)) >= 0.5 * abs(primary$estimate)
      } else FALSE,
      qc_adjusted_estimate = single_estimate(qc),
      qc_adjusted_same_direction = if (is.finite(single_estimate(qc)) &&
                                        is.finite(primary$estimate)) {
        single_estimate(qc) * primary$estimate > 0
      } else FALSE,
      severe_qc_exclusion_estimate = single_estimate(severe),
      severe_qc_exclusion_status = if (!nrow(severe)) "not_run" else if (
        isTRUE(severe$fit_success[[1L]])
      ) "estimated" else severe$failure_reason[[1L]],
      severe_qc_same_direction = if (is.finite(single_estimate(severe)) &&
                                       is.finite(primary$estimate)) {
        single_estimate(severe) * primary$estimate > 0
      } else FALSE,
      omission_units = nrow(omission),
      omission_successful = sum(omission_ok),
      omission_sign_reversals = if (any(omission_ok) && is.finite(primary$estimate)) {
        sum(omission$estimate[omission_ok] * primary$estimate < 0)
      } else NA_integer_,
      omission_fraction_retain_half_magnitude = if (
        any(omission_ok) && is.finite(primary$estimate)
      ) {
        mean(abs(omission$estimate[omission_ok]) >= 0.5 * abs(primary$estimate))
      } else NA_real_,
      most_influential_omission = if (length(omission_change)) {
        omission_units[[which.max(omission_change)]]
      } else NA_character_,
      stability_status = if (primary$eligibility_status == "eligible") {
        "evaluated"
      } else "not_applicable_not_testable",
      stringsAsFactors = FALSE
    )
  }
  as.data.frame(bind_rows(rows))
}

direction_compatible <- function(estimate, camera_direction) {
  if (!is.finite(estimate) || is.na(camera_direction)) return(FALSE)
  (estimate > 0 && camera_direction == "Up") ||
    (estimate < 0 && camera_direction == "Down")
}

apply_gate <- function(results, camera, stability, reliability, phase_cfg) {
  x <- merge(results, camera[, c(
    "test_id", "direction", "p_value", "q_value", "camera_status"
  )], by = "test_id", all.x = TRUE, suffixes = c("_score", "_camera"), sort = FALSE)
  x <- merge(x, stability, by = c("test_id", "context_id", "contrast_id", "module_id"),
             all.x = TRUE, sort = FALSE)
  rel <- reliability[, c(
    "context_id", "module_id", "nci_mean_z_pc1_correlation", "pc1_reliable"
  ), drop = FALSE]
  x <- merge(x, rel, by = c("context_id", "module_id"), all.x = TRUE, sort = FALSE)
  x <- x[match(results$test_id, x$test_id), , drop = FALSE]
  sesoi <- as.numeric(phase_cfg$analysis$sesoi_nci_sd)
  x$donor_count_confirmatory <- x$minimum_group_donors >=
    as.integer(phase_cfg$eligibility$minimum_confirmatory_donors_per_group)
  x$module_coverage_pass <- as.logical(x$coverage_pass)
  x$score_q_pass <- is.finite(x$q_value_score) &
    x$q_value_score <= as.numeric(phase_cfg$multiple_testing$q_threshold)
  x$effect_meets_sesoi <- is.finite(x$estimate) & abs(x$estimate) >= sesoi
  x$interval_excludes_zero <- is.finite(x$ci_low) & is.finite(x$ci_high) &
    (x$ci_low > 0 | x$ci_high < 0)
  x$interval_inside_sesoi <- is.finite(x$ci_low) & is.finite(x$ci_high) &
    x$ci_low >= -sesoi & x$ci_high <= sesoi
  x$camera_testable <- x$camera_status == "estimated" & is.finite(x$p_value_camera)
  x$camera_direction_compatible <- mapply(
    direction_compatible, x$estimate, x$direction
  )
  x$camera_competitive_q_support <- is.finite(x$q_value_camera) &
    x$q_value_camera <= as.numeric(phase_cfg$multiple_testing$q_threshold)
  x$bootstrap_direction_pass <- as.logical(x$bootstrap_valid) &
    is.finite(x$bootstrap_same_direction_fraction) &
    x$bootstrap_same_direction_fraction >=
      as.numeric(phase_cfg$stability$minimum_direction_fraction)
  x$loo_pass <- is.finite(x$loo_sign_reversals) & x$loo_sign_reversals == 0 &
    x$loo_successful == x$loo_planned
  x$pc1_correlation_pass <- as.logical(x$pc1_reliable) &
    is.finite(x$nci_mean_z_pc1_correlation) &
    abs(x$nci_mean_z_pc1_correlation) >=
      as.numeric(phase_cfg$stability$pc1_minimum_correlation)
  x$pc1_sensitivity_pass <- as.logical(x$pc1_agrees)
  x$threshold50_sensitivity_pass <- as.logical(x$threshold50_agrees)
  x$balance_direction_pass <- as.logical(x$balance_valid) &
    is.finite(x$balance_same_direction_fraction) &
    x$balance_same_direction_fraction >=
      as.numeric(phase_cfg$stability$minimum_direction_fraction)
  x$omission_pass <- is.finite(x$omission_sign_reversals) &
    x$omission_sign_reversals == 0 &
    is.finite(x$omission_fraction_retain_half_magnitude) &
    x$omission_fraction_retain_half_magnitude >=
      as.numeric(phase_cfg$stability$minimum_direction_fraction)
  x$severe_qc_exclusion_pass <- as.logical(x$severe_qc_same_direction)
  rule_columns <- c(
    "module_coverage_pass", "score_q_pass", "effect_meets_sesoi",
    "interval_excludes_zero", "camera_testable", "camera_direction_compatible",
    "bootstrap_direction_pass", "loo_pass", "pc1_correlation_pass",
    "pc1_sensitivity_pass", "threshold50_sensitivity_pass",
    "balance_direction_pass", "omission_pass", "severe_qc_exclusion_pass"
  )
  x$all_non_donor_support_rules_pass <- apply(
    x[, rule_columns, drop = FALSE], 1L, function(z) all(as.logical(z), na.rm = FALSE)
  )
  x$scientific_status <- vapply(seq_len(nrow(x)), function(i) {
    row <- x[i, , drop = FALSE]
    if (row$model_status != "estimated") return("not_testable")
    if (row$minimum_group_donors < 10L &&
        row$minimum_group_donors >= 5L &&
        isTRUE(row$all_non_donor_support_rules_pass)) {
      return("provisional_low_power")
    }
    if (isTRUE(row$donor_count_confirmatory) &&
        isTRUE(row$all_non_donor_support_rules_pass)) return("supported")
    if (isTRUE(row$score_q_pass) && isTRUE(row$interval_excludes_zero) &&
        !isTRUE(row$effect_meets_sesoi)) {
      return("statistically_detectable_but_small")
    }
    if (isTRUE(row$interval_inside_sesoi)) return("not_supported_precise_null")
    "inconclusive"
  }, character(1))
  x$permitted_sentence <- vapply(seq_len(nrow(x)), function(i) {
    row <- x[i, , drop = FALSE]
    if (!row$scientific_status %in% c("supported", "provisional_low_power")) return("")
    qualifier <- if (row$scientific_status == "provisional_low_power") {
      "Provisionally, "
    } else ""
    paste0(
      qualifier, "in ROSMAP broad ", gsub("_", " ", row$context_id),
      " profiles, ", toupper(row$modifier), " modified the AD-associated ",
      gsub("_", " ", row$module_id), " expression difference (",
      row$contrast_id, "; estimate ", signif(row$estimate, 3), ")."
    )
  }, character(1))
  x
}

claim_summary_from_gate <- function(gate, pilot) {
  direct <- gate$module_role == "direct_respiratory"
  supported <- gate$scientific_status == "supported" & direct
  sex <- supported & gate$modifier == "sex"
  apoe <- supported & gate$modifier == "apoe"
  overall <- if (pilot) {
    "not_applicable_pilot"
  } else if (any(sex) && any(apoe)) {
    "supported_both"
  } else if (any(sex)) {
    "supported_sex_only"
  } else if (any(apoe)) {
    "supported_apoe_only"
  } else if (!any(direct & gate$scientific_status != "not_testable")) {
    "not_testable"
  } else if (all(gate$scientific_status[direct &
      gate$minimum_group_donors >= 10L] == "not_supported_precise_null")) {
    "not_supported"
  } else "inconclusive"
  data.frame(
    conclusion_type = c("sex", "apoe", "overall", "supporting_modules", "provisional"),
    scientific_decision = c(
      if (any(sex)) "supported" else if (pilot) "not_applicable_pilot" else "not_supported",
      if (any(apoe)) "supported" else if (pilot) "not_applicable_pilot" else "not_supported",
      overall,
      if (any(gate$scientific_status == "supported" & !direct)) "supported_narrow" else
        if (pilot) "not_applicable_pilot" else "not_supported",
      if (any(gate$scientific_status == "provisional_low_power")) "present" else "absent"
    ),
    passing_test_ids = c(
      paste(gate$test_id[sex], collapse = "|"),
      paste(gate$test_id[apoe], collapse = "|"),
      paste(gate$test_id[supported], collapse = "|"),
      paste(gate$test_id[gate$scientific_status == "supported" & !direct], collapse = "|"),
      paste(gate$test_id[gate$scientific_status == "provisional_low_power"], collapse = "|")
    ),
    allowed_wording = c(
      paste(gate$permitted_sentence[sex], collapse = " "),
      paste(gate$permitted_sentence[apoe], collapse = " "),
      if (pilot) "Pilot effects are nonfinal and cannot support Claim 1." else
        paste(gate$permitted_sentence[supported], collapse = " "),
      paste(gate$permitted_sentence[gate$scientific_status == "supported" & !direct],
            collapse = " "),
      paste(gate$permitted_sentence[gate$scientific_status == "provisional_low_power"],
            collapse = " ")
    ),
    stringsAsFactors = FALSE
  )
}

count_records <- function(path) {
  if (grepl("[.]rds$", path)) return(NA_real_)
  con <- if (grepl("[.]gz$", path)) gzfile(path, "rt") else file(path, "rt")
  on.exit(close(con))
  n <- -1L
  repeat {
    lines <- readLines(con, n = 10000L, warn = FALSE)
    if (!length(lines)) break
    n <- n + length(lines)
  }
  max(n, 0L)
}

validate_phase13_output <- function(path, expected_contexts, expected_tests,
                                    expected_stratum_rows, expected_status,
                                    declared_files = NULL) {
  if (!dir.exists(path)) stop("Output directory does not exist: ", path, call. = FALSE)
  actual <- sort(list.files(path, all.files = FALSE, recursive = FALSE))
  if (is.null(declared_files)) {
    status <- data.table::fread(file.path(path, "respiratory_status.tsv"),
                               data.table = FALSE)
    declared_files <- actual
  }
  if (!identical(actual, sort(declared_files))) {
    stop("Output filename contract mismatch", call. = FALSE)
  }
  if (length(list.dirs(path, recursive = FALSE, full.names = FALSE))) {
    stop("Output directory contains subdirectories", call. = FALSE)
  }
  read_one <- function(name) data.table::fread(file.path(path, name), data.table = FALSE)
  contexts <- read_one("respiratory_cell_context_manifest.tsv")
  contrasts <- read_one("respiratory_contrast_manifest.tsv")
  modules <- read_one("respiratory_module_manifest.tsv")
  members <- read_one("respiratory_module_members.tsv")
  tests <- read_one("respiratory_test_manifest.tsv")
  results <- read_one("respiratory_module_results.tsv")
  camera <- read_one("respiratory_camera_results.tsv")
  stability <- read_one("respiratory_stability_summary.tsv")
  gate <- read_one("respiratory_gate_decisions.tsv")
  strata <- read_one("respiratory_module_stratum_effects.tsv")
  checks <- read_one("respiratory_checks.tsv")
  artifacts <- read_one("respiratory_artifacts.tsv")
  status <- read_one("respiratory_status.tsv")
  stopifnot(
    nrow(contexts) == expected_contexts, nrow(contrasts) == 7L,
    nrow(modules) == 4L, nrow(members) == 273L,
    nrow(tests) == expected_tests, nrow(results) == expected_tests,
    nrow(camera) == expected_tests, nrow(stability) == expected_tests,
    nrow(gate) == expected_tests, nrow(strata) == expected_stratum_rows,
    length(unique(tests$test_id)) == expected_tests,
    all(checks$passed[as.logical(checks$blocking)]),
    identical(status$validation_status[[1L]], expected_status),
    all(gate$scientific_status %in% c(
      "supported", "provisional_low_power", "statistically_detectable_but_small",
      "not_supported_precise_null", "inconclusive", "not_testable"
    )),
    "MRPL13" %in% members$frozen_gene_symbol,
    !"RPL13" %in% members$frozen_gene_symbol,
    !any(members$frozen_gene_symbol %in% c("ATP5IF1", "CYCS", "HCCS") &
           members$module_id == "nuclear_oxphos_structural_86")
  )
  for (i in seq_len(nrow(artifacts))) {
    artifact_path <- file.path(path, basename(artifacts$path[[i]]))
    if (!file.exists(artifact_path) ||
        !identical(sha256_file(artifact_path), artifacts$sha256[[i]])) {
      stop("Artifact hash mismatch: ", artifacts$artifact_id[[i]], call. = FALSE)
    }
  }
  invisible(TRUE)
}

qc_summary_table <- function(broad_profiles, phase_cfg) {
  rows <- list()
  for (context_id in names(broad_profiles)) {
    s <- broad_profiles[[context_id]]$samples
    for (threshold in c(
      as.integer(phase_cfg$eligibility$primary_min_nuclei),
      as.integer(phase_cfg$eligibility$sensitivity_min_nuclei)
    )) {
      for (group in unlist(phase_cfg$groups)) {
        x <- s[s$group_id == group & s$nuclei >= threshold, , drop = FALSE]
        rows[[length(rows) + 1L]] <- data.frame(
          context_id = context_id, group_id = group, nucleus_threshold = threshold,
          donors = nrow(x), nuclei = sum(x$nuclei), total_umi_count = sum(x$total_umi_count),
          median_nuclei = if (nrow(x)) stats::median(x$nuclei) else NA_real_,
          median_percent_mt = if (nrow(x)) stats::median(x$aggregate_percent_mt) else NA_real_,
          severe_qc_profiles = sum(x$severe_qc_profile), stringsAsFactors = FALSE
        )
      }
    }
  }
  as.data.frame(bind_rows(rows))
}

main <- function() {
  args <- parse_cli(commandArgs(trailingOnly = TRUE))
  required_packages <- c(
    "yaml", "data.table", "Matrix", "edgeR", "limma", "sandwich", "digest"
  )
  missing <- required_packages[!vapply(
    required_packages, requireNamespace, logical(1), quietly = TRUE
  )]
  if (length(missing)) {
    stop("Missing required packages: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- absolute_path(args$config, root)
  execution_path <- absolute_path(args$execution_config, root)
  config <- yaml::read_yaml(config_path)
  execution_cfg <- yaml::read_yaml(execution_path)
  worker_plan <- resolve_stability_workers(execution_cfg$execution)
  cat(
    "Phase 13 stability backend: ", worker_plan$backend,
    "; effective workers: ", worker_plan$effective,
    "; requested workers: ", worker_plan$requested,
    "; max_total_cores: ", worker_plan$max_total,
    if (!is.na(worker_plan$scheduler)) {
      paste0("; scheduler allocation: ", worker_plan$scheduler)
    } else "",
    "\n", sep = ""
  )
  phase_path <- absolute_path(config$project$phase13_respiratory_modifier_config, root)
  phase_cfg <- yaml::read_yaml(phase_path)
  module_path <- absolute_path(phase_cfg$paths$module_members, root)
  module_members <- data.table::fread(module_path, data.table = FALSE)
  pilot <- isTRUE(config$scope$pilot)
  stage_root <- absolute_path(config$outputs$root, root)
  final_dir <- file.path(stage_root, phase_cfg$paths$output_relative)
  declared <- unlist(phase_cfg$outputs$declared_files)
  expected_contexts <- if (pilot) 1L else 7L
  expected_tests <- expected_contexts * 7L * 4L
  expected_strata <- expected_contexts * 4L * 6L
  expected_status <- if (pilot) "nonfinal_smoke_test" else "validated_complete"
  if (dir.exists(final_dir)) {
    validate_phase13_output(final_dir, expected_contexts, expected_tests,
                            expected_strata, expected_status, declared)
    cat("Validated Phase 13 output already exists: ", final_dir, "\n", sep = "")
    return(invisible(TRUE))
  }
  do.call(RNGkind, list(as.character(phase_cfg$randomization$rng_kind)))
  context_manifest <- context_manifest_from_config(phase_cfg, pilot)
  contrast_manifest <- contrast_manifest_from_config(phase_cfg)
  module_manifest <- module_manifest_from_config(phase_cfg)
  check_store <- add_check_factory()
  check <- check_store$add
  check("definitions_frozen", "definitions", "global", "phase13", TRUE,
        isTRUE(phase_cfg$analysis$definitions_frozen),
        phase_cfg$analysis$definitions_frozen, TRUE)
  check("module_membership_count", "definitions", "global", "phase13", TRUE,
        nrow(module_members) == 273L, nrow(module_members), 273L)
  check("module_sizes", "definitions", "global", "phase13", TRUE,
        identical(as.integer(table(factor(
          module_members$module_id, levels = module_manifest$module_id
        ))), c(13L, 86L, 155L, 19L)),
        paste(as.integer(table(module_members$module_id)), collapse = "|"),
        "13|86|155|19")
  check("mrpl13_not_rpl13", "definitions", "gene", "MRPL13", TRUE,
        "MRPL13" %in% module_members$frozen_gene_symbol &&
          !"RPL13" %in% module_members$frozen_gene_symbol,
        paste(module_members$frozen_gene_symbol[
          module_members$frozen_gene_symbol %in% c("MRPL13", "RPL13")
        ], collapse = "|"), "MRPL13")
  strict <- module_members[
    module_members$module_id == "nuclear_oxphos_structural_86", , drop = FALSE
  ]
  check("strict_nuclear_oxphos_exclusions", "definitions", "module",
        "nuclear_oxphos_structural_86", TRUE,
        !any(strict$frozen_gene_symbol %in% c(
          paste0("MT-", c("ATP6", "ATP8", "CO1", "CO2", "CO3", "CYB",
                          "ND1", "ND2", "ND3", "ND4", "ND4L", "ND5", "ND6")),
          "ATP5IF1", "CYCS", "HCCS"
        )), paste(intersect(strict$frozen_gene_symbol,
                           c("ATP5IF1", "CYCS", "HCCS")), collapse = "|"), "none")
  hand_ok <- all(vapply(phase_cfg$contrasts, function(x) {
    identical(as.numeric(unlist(x$coefficients)), c(1, -1, -1, 1))
  }, logical(1)))
  check("contrast_vectors_hand_verified", "definitions", "global", "contrasts",
        TRUE, hand_ok, hand_ok, TRUE)

  input <- validate_and_load_inputs(root, stage_root, phase_cfg, context_manifest, check)
  input_hashes <- paste(input$inventory$sha256, collapse = "|")
  fingerprint <- digest::digest(paste(
    sha256_file(phase_path), sha256_file(module_path),
    sha256_file(file.path(root, "scripts/13_run_respiratory_modifier.R")),
    sha256_file(config_path), sha256_file(execution_path), input_hashes,
    sep = "|"
  ), algo = "sha256", serialize = FALSE)
  scratch_root <- absolute_path(execution_cfg$execution$temp_dir, root)
  scratch <- file.path(scratch_root, phase_cfg$paths$scratch_relative, fingerprint)
  dir.create(scratch, recursive = TRUE, showWarnings = FALSE)
  broad_checkpoint <- file.path(scratch, "broad_profiles.rds")
  if (file.exists(broad_checkpoint)) {
    broad_profiles <- readRDS(broad_checkpoint)
  } else {
    broad_profiles <- list()
    for (context_id in context_manifest$context_id) {
      broad_profiles[[context_id]] <- aggregate_context(
        context_id, input$source_objects[[context_id]], input$cohort, phase_cfg, check
      )
    }
    atomic_save_rds(broad_profiles, broad_checkpoint)
  }
  donor_samples <- as.data.frame(bind_rows(lapply(broad_profiles, function(x) x$samples)))
  count_conservation <- as.data.frame(bind_rows(lapply(
    broad_profiles, function(x) x$conservation
  )))
  check("donor_context_keys_unique", "broad_aggregation", "global", "phase13",
        TRUE, !anyDuplicated(donor_samples$donor_context_id),
        anyDuplicated(donor_samples$donor_context_id), 0)
  check("study_has_two_levels", "broad_aggregation", "global", "study", TRUE,
        length(unique(donor_samples$study)) == 2L,
        paste(sort(unique(donor_samples$study)), collapse = "|"), "MAP|ROS")

  primary_checkpoint <- file.path(scratch, "primary_analysis.rds")
  if (file.exists(primary_checkpoint)) {
    analyses <- readRDS(primary_checkpoint)
  } else {
    analyses <- list()
    for (context_id in names(broad_profiles)) {
      cat("Phase 13 primary analysis: ", context_id, "\n", sep = "")
      analyses[[context_id]] <- analyze_context(
        context_id, broad_profiles[[context_id]], module_members, phase_cfg, check
      )
    }
    atomic_save_rds(analyses, primary_checkpoint)
  }
  module_results <- as.data.frame(bind_rows(lapply(analyses, function(x) x$results)))
  score_testable <- is.finite(module_results$p_value)
  module_results$q_value[score_testable] <- stats::p.adjust(
    module_results$p_value[score_testable], method = "BH"
  )
  test_manifest <- as.data.frame(bind_rows(lapply(analyses, function(x) x$test_manifest)))
  coverage <- as.data.frame(bind_rows(lapply(analyses, function(x) x$coverage)))
  nci_parameters <- as.data.frame(bind_rows(lapply(analyses, function(x) x$parameters)))
  donor_scores <- as.data.frame(bind_rows(lapply(analyses, function(x) x$scores)))
  pc1_loadings <- as.data.frame(bind_rows(lapply(analyses, function(x) x$loadings)))
  module_strata <- as.data.frame(bind_rows(lapply(analyses, function(x) x$strata)))
  reliability <- as.data.frame(bind_rows(lapply(analyses, function(x) x$reliability)))
  gene_interactions <- as.data.frame(bind_rows(lapply(
    analyses, function(x) x$genes$interactions
  )))
  gene_strata <- as.data.frame(bind_rows(lapply(analyses, function(x) x$genes$strata)))
  diagnostics <- as.data.frame(bind_rows(lapply(analyses, function(x) x$diagnostics)))
  camera <- as.data.frame(bind_rows(lapply(names(analyses), function(context_id) {
    run_camera_context(context_id, analyses[[context_id]], phase_cfg)
  })))
  camera_testable <- is.finite(camera$p_value)
  camera$q_value[camera_testable] <- stats::p.adjust(
    camera$p_value[camera_testable], method = "BH"
  )
  check("primary_test_rows", "primary_models", "global", "phase13", TRUE,
        nrow(module_results) == expected_tests, nrow(module_results), expected_tests)
  check("camera_test_rows", "camera", "global", "phase13", TRUE,
        nrow(camera) == expected_tests, nrow(camera), expected_tests)
  check("module_stratum_rows", "primary_models", "global", "phase13", TRUE,
        nrow(module_strata) == expected_strata, nrow(module_strata), expected_strata)

  stability_checkpoint <- file.path(scratch, "stability.rds")
  if (file.exists(stability_checkpoint)) {
    stability_replicates <- readRDS(stability_checkpoint)
  } else {
    stability_contexts <- lapply(names(analyses), function(context_id) {
      context_checkpoint <- file.path(
        scratch, paste0("stability_", context_id, ".rds")
      )
      if (file.exists(context_checkpoint)) {
        cat("Reusing Phase 13 stability checkpoint: ", context_id, "\n", sep = "")
        return(readRDS(context_checkpoint))
      }
      result <- run_stability_context(
        context_id, broad_profiles[[context_id]], analyses[[context_id]], phase_cfg,
        pilot, workers = worker_plan$effective
      )
      atomic_save_rds(result, context_checkpoint)
      result
    })
    stability_replicates <- as.data.frame(bind_rows(stability_contexts))
    atomic_save_rds(stability_replicates, stability_checkpoint)
  }
  donor_counts_context <- setNames(vapply(
    analyses, function(x) nrow(x$norm$samples), integer(1)
  ), names(analyses))
  stability_summary <- summarize_stability(
    module_results, stability_replicates, phase_cfg, pilot, donor_counts_context
  )
  for (i in seq_len(nrow(reliability))) {
    evaluated <- stability_summary[
      stability_summary$context_id == reliability$context_id[[i]] &
        stability_summary$module_id == reliability$module_id[[i]] &
        stability_summary$omission_units > 0, , drop = FALSE
    ]
    if (!nrow(evaluated)) next
    reliability$omission_units[[i]] <- max(evaluated$omission_units, na.rm = TRUE)
    reliability$omission_sign_reversals[[i]] <- max(
      evaluated$omission_sign_reversals, na.rm = TRUE
    )
    reliability$omission_fraction_retain_half_magnitude[[i]] <- min(
      evaluated$omission_fraction_retain_half_magnitude, na.rm = TRUE
    )
    influential_index <- which.min(
      evaluated$omission_fraction_retain_half_magnitude
    )[[1L]]
    reliability$most_influential_omission[[i]] <-
      evaluated$most_influential_omission[[influential_index]]
  }
  gate <- apply_gate(module_results, camera, stability_summary, reliability, phase_cfg)
  claim_summary <- claim_summary_from_gate(gate, pilot)
  overall_decision <- claim_summary$scientific_decision[
    claim_summary$conclusion_type == "overall"
  ][[1L]]

  boot_expected <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_bootstrap_repetitions)
  } else as.integer(phase_cfg$stability$production_bootstrap_repetitions)
  bal_expected <- if (pilot) {
    as.integer(phase_cfg$stability$pilot_balance_repetitions)
  } else as.integer(phase_cfg$stability$production_balance_repetitions)
  eligible_summary <- stability_summary[
    module_results$eligibility_status == "eligible", , drop = FALSE
  ]
  check("stability_summary_rows", "stability", "global", "phase13", TRUE,
        nrow(stability_summary) == expected_tests, nrow(stability_summary), expected_tests)
  check("bootstrap_repetition_success", "stability", "global", "phase13", TRUE,
        !nrow(eligible_summary) || all(eligible_summary$bootstrap_successful >=
          ceiling(boot_expected * as.numeric(phase_cfg$stability$minimum_success_fraction))),
        if (nrow(eligible_summary)) min(eligible_summary$bootstrap_successful) else 0,
        ceiling(boot_expected * as.numeric(phase_cfg$stability$minimum_success_fraction)))
  check("balance_repetition_success", "stability", "global", "phase13", TRUE,
        !nrow(eligible_summary) || all(eligible_summary$balance_successful >=
          ceiling(bal_expected * as.numeric(phase_cfg$stability$minimum_success_fraction))),
        if (nrow(eligible_summary)) min(eligible_summary$balance_successful) else 0,
        ceiling(bal_expected * as.numeric(phase_cfg$stability$minimum_success_fraction)))
  check("gate_rows_terminal", "gate", "global", "phase13", TRUE,
        nrow(gate) == expected_tests &&
          all(gate$scientific_status %in% c(
            "supported", "provisional_low_power", "statistically_detectable_but_small",
            "not_supported_precise_null", "inconclusive", "not_testable"
          )), nrow(gate), expected_tests)

  checks <- check_store$value()
  failed_blocking <- checks$blocking & !checks$passed
  if (any(failed_blocking)) {
    stop("Blocking Phase 13 checks failed: ",
         paste(checks$check_id[failed_blocking], collapse = ", "), call. = FALSE)
  }

  staging <- file.path(scratch, paste0("staging_", Sys.getpid()))
  if (dir.exists(staging)) stop("Staging directory already exists: ", staging, call. = FALSE)
  dir.create(staging, recursive = TRUE)
  analysis_manifest <- data.frame(
    analysis_id = phase_cfg$analysis$analysis_id,
    title = phase_cfg$analysis$title,
    definitions_approved = phase_cfg$analysis$definitions_approved,
    definitions_frozen = phase_cfg$analysis$definitions_frozen,
    approval_basis = phase_cfg$analysis$approval_basis,
    execution_stage = execution_cfg$execution$execution_stage,
    pilot = pilot, contexts = expected_contexts, groups = 12L,
    contrasts = 7L, modules = 4L, module_memberships = 273L,
    planned_primary_tests = expected_tests,
    sesoi_nci_sd = phase_cfg$analysis$sesoi_nci_sd,
    prior_count = phase_cfg$analysis$prior_count,
    model_formula = phase_cfg$analysis$model_formula,
    score_family = phase_cfg$multiple_testing$score_family,
    camera_family = phase_cfg$multiple_testing$camera_family,
    base_seed = phase_cfg$randomization$base_seed,
    stability_parallel_backend = worker_plan$backend,
    stability_workers_requested = worker_plan$requested,
    stability_workers_effective = worker_plan$effective,
    analysis_fingerprint = fingerprint,
    scientific_config_sha256 = sha256_file(phase_path),
    module_manifest_sha256 = sha256_file(module_path),
    stringsAsFactors = FALSE
  )
  broad_counts_output <- list(
    schema_version = "phase13_pseudobulk_counts_v1",
    contexts = lapply(broad_profiles, function(x) x$counts),
    samples = lapply(broad_profiles, function(x) x$samples),
    analysis_fingerprint = fingerprint
  )
  expression_bundle <- list(
    schema_version = "phase13_expression_bundle_v1",
    contexts = lapply(analyses, function(x) list(
      tested_genes = x$norm$tested_genes,
      tmm_factors = x$norm$y$samples$norm.factors,
      library_sizes = x$norm$y$samples$lib.size,
      logcpm = x$norm$logcpm, design = x$norm$design,
      samples = x$norm$samples,
      background_genes = x$norm$tested_genes
    )),
    prior_count = phase_cfg$analysis$prior_count,
    analysis_fingerprint = fingerprint
  )
  stage_ids <- c(
    "definitions", "input_validation", "broad_aggregation", "test_manifest",
    "primary_models", "camera", "stability", "gate", "publication"
  )
  stage_status <- data.frame(
    stage_order = seq_along(stage_ids), stage_id = stage_ids,
    dependencies = c("", "definitions", "input_validation",
                     "broad_aggregation", "test_manifest", "primary_models",
                     "primary_models|camera", "stability", "gate"),
    analysis_fingerprint = fingerprint, planned_shards = 1L,
    completed_shards = 1L, reused_shards = 0L, skipped_shards = 0L,
    failed_shards = 0L, started_utc = format(started_at, tz = "UTC"),
    finished_utc = format(Sys.time(), tz = "UTC"), terminal_status = "completed",
    stringsAsFactors = FALSE
  )
  tables <- list(
    respiratory_analysis_manifest.tsv = list(analysis_manifest, "phase13_analysis_manifest_v1"),
    respiratory_cell_context_manifest.tsv = list(context_manifest, "phase13_context_manifest_v1"),
    respiratory_contrast_manifest.tsv = list(contrast_manifest, "phase13_contrast_manifest_v1"),
    respiratory_module_manifest.tsv = list(module_manifest, "phase13_module_manifest_v1"),
    respiratory_module_members.tsv = list(module_members, "phase13_module_members_v1"),
    respiratory_input_inventory.tsv = list(input$inventory, "phase13_input_inventory_v1"),
    respiratory_source_identity_checks.tsv = list(input$identity, "phase13_source_identity_v1"),
    respiratory_test_manifest.tsv = list(test_manifest, "phase13_test_manifest_v1"),
    respiratory_donor_samples.tsv.gz = list(donor_samples, "phase13_donor_samples_v1"),
    respiratory_count_conservation.tsv = list(count_conservation, "phase13_count_conservation_v1"),
    respiratory_qc_summary.tsv = list(qc_summary_table(broad_profiles, phase_cfg),
                                      "phase13_qc_summary_v1"),
    respiratory_gene_stratum_effects.tsv.gz = list(gene_strata, "phase13_gene_stratum_v1"),
    respiratory_gene_interaction_results.tsv.gz = list(gene_interactions,
                                                        "phase13_gene_interaction_v1"),
    respiratory_gene_model_diagnostics.tsv = list(diagnostics,
                                                   "phase13_gene_diagnostics_v1"),
    respiratory_module_coverage.tsv = list(coverage, "phase13_module_coverage_v1"),
    respiratory_nci_reference_parameters.tsv.gz = list(nci_parameters,
                                                        "phase13_nci_reference_v1"),
    respiratory_donor_module_scores.tsv.gz = list(donor_scores,
                                                   "phase13_donor_scores_v1"),
    respiratory_pc1_loadings.tsv.gz = list(pc1_loadings, "phase13_pc1_loadings_v1"),
    respiratory_module_stratum_effects.tsv = list(module_strata,
                                                   "phase13_module_stratum_v1"),
    respiratory_module_results.tsv = list(module_results, "phase13_module_results_v1"),
    respiratory_camera_results.tsv = list(camera, "phase13_camera_results_v1"),
    respiratory_module_reliability.tsv = list(reliability,
                                               "phase13_module_reliability_v1"),
    respiratory_stability_replicates.tsv.gz = list(stability_replicates,
                                                    "phase13_stability_replicates_v1"),
    respiratory_stability_summary.tsv = list(stability_summary,
                                              "phase13_stability_summary_v1"),
    respiratory_gate_decisions.tsv = list(gate, "phase13_gate_decisions_v1"),
    respiratory_claim_summary.tsv = list(claim_summary, "phase13_claim_summary_v1"),
    respiratory_stage_status.tsv = list(stage_status, "phase13_stage_status_v1"),
    respiratory_checks.tsv = list(checks, "phase13_checks_v1")
  )
  for (name in names(tables)) {
    atomic_write_tsv(tables[[name]][[1L]], file.path(staging, name),
                     tables[[name]][[2L]])
  }
  atomic_save_rds(broad_counts_output,
                  file.path(staging, "respiratory_pseudobulk_counts.rds"))
  atomic_save_rds(expression_bundle,
                  file.path(staging, "respiratory_expression_bundle.rds"))

  artifact_names <- setdiff(declared, c(
    "respiratory_artifacts.tsv", "respiratory_status.tsv"
  ))
  artifacts <- as.data.frame(bind_rows(lapply(seq_along(artifact_names), function(i) {
    name <- artifact_names[[i]]
    path <- file.path(staging, name)
    data.frame(
      artifact_role = if (grepl("manifest|checks|status", name)) "control" else "scientific",
      artifact_id = sub("[.](tsv([.]gz)?|rds)$", "", name),
      path = file.path(stage_root, phase_cfg$paths$output_relative, name),
      bytes = file.info(path)$size, records = count_records(path),
      sha256 = sha256_file(path), canonical_content_sha256 = sha256_file(path),
      output_schema = if (grepl("[.]rds$", name)) "rds_v1" else "tsv_v1",
      validation_status = expected_status, stringsAsFactors = FALSE
    )
  })))
  atomic_write_tsv(artifacts, file.path(staging, "respiratory_artifacts.tsv"),
                   "phase13_artifacts_v1")
  status <- data.frame(
    execution_stage = execution_cfg$execution$execution_stage,
    execution_phase = execution_cfg$execution$execution_phase,
    backend = execution_cfg$execution$backend, run_id = execution_cfg$execution$run_id,
    stable_task_id = "global:respiratory_modifier",
    task_mode = "respiratory_modifier",
    scientific_script = "scripts/13_run_respiratory_modifier.R",
    scientific_script_sha256 = sha256_file(file.path(root, "scripts/13_run_respiratory_modifier.R")),
    scientific_config_sha256 = sha256_file(phase_path),
    module_manifest_sha256 = sha256_file(module_path),
    pipeline_config_sha256 = sha256_file(config_path),
    execution_config_sha256 = sha256_file(execution_path),
    rds_manifest_sha256 = sha256_file(absolute_path(config$project$manifest, root)),
    contexts = expected_contexts, modules = 4L, module_memberships = 273L,
    modifier_contrasts = 7L, planned_primary_tests = expected_tests,
    eligible_tests = sum(module_results$eligibility_status == "eligible"),
    not_testable_tests = sum(module_results$eligibility_status != "eligible"),
    score_result_rows = nrow(module_results), camera_result_rows = nrow(camera),
    bootstrap_repetitions = boot_expected, balance_repetitions = bal_expected,
    stability_parallel_backend = worker_plan$backend,
    stability_workers_requested = worker_plan$requested,
    stability_workers_effective = worker_plan$effective,
    supported_rows = sum(gate$scientific_status == "supported"),
    scientific_decision = overall_decision,
    failed_checks = "", artifact_manifest_sha256 = sha256_file(
      file.path(staging, "respiratory_artifacts.tsv")
    ),
    validation_status = expected_status, git_revision = git_revision(root),
    timestamp_utc = format(Sys.time(), tz = "UTC"), stringsAsFactors = FALSE
  )
  atomic_write_tsv(status, file.path(staging, "respiratory_status.tsv"),
                   "phase13_status_v1")
  validate_phase13_output(staging, expected_contexts, expected_tests,
                          expected_strata, expected_status, declared)
  dir.create(dirname(final_dir), recursive = TRUE, showWarnings = FALSE)
  if (!file.rename(staging, final_dir)) {
    stop("Could not atomically publish Phase 13 output", call. = FALSE)
  }
  cat("Phase 13 published: ", final_dir, "\n", sep = "")
  cat("Technical status: ", expected_status, "\n", sep = "")
  cat("Scientific decision: ", overall_decision, "\n", sep = "")
  invisible(TRUE)
}

if (sys.nframe() == 0L) main()
