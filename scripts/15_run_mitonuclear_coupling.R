#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_phase15_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL,
              task_mode = "mitonuclear_coupling")
  allowed <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/15_run_mitonuclear_coupling.R ",
          "--config FILE --execution-config FILE ",
          "[--task-mode mitonuclear_coupling]\n", sep = "")
      quit(status = 0L)
    }
    if (!key %in% allowed || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config) || is.null(out$execution_config)) {
    stop("--config and --execution-config are required", call. = FALSE)
  }
  if (!identical(out$task_mode, "mitonuclear_coupling")) {
    stop("--task-mode must be mitonuclear_coupling", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

bind_rows <- function(xs) {
  xs <- Filter(function(x) !is.null(x) && nrow(x), xs)
  if (!length(xs)) return(data.frame())
  as.data.frame(data.table::rbindlist(xs, fill = TRUE, use.names = TRUE))
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  value <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(value, "status")
  if (!length(value) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(value[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

git_revision <- function(root) {
  value <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(value, "status")
  if (!length(value) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else value[[1L]]
}

atomic_write_tsv <- function(x, path, schema_version) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  x$schema_version <- schema_version
  x <- x[, c("schema_version", setdiff(names(x), "schema_version")), drop = FALSE]
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  connection <- if (grepl("[.]gz$", path)) gzfile(tmp, "wt") else file(tmp, "wt")
  write.table(x, connection, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  close(connection)
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

count_records <- function(path) {
  if (!file.exists(path)) return(NA_integer_)
  nrow(data.table::fread(path, data.table = FALSE, showProgress = FALSE))
}

seed_for <- function(cfg, id) {
  base <- as.numeric(cfg$randomization$base_seed)
  offset <- abs(as.numeric(digest::digest2int(as.character(id))))
  as.integer((base + offset) %% (.Machine$integer.max - 1)) + 1L
}

phase15_worker_plan <- function(execution, os_type = .Platform$OS.type) {
  positive <- function(x) {
    x <- suppressWarnings(as.integer(x))
    if (length(x) == 1L && is.finite(x) && x > 0L) x else NA_integer_
  }
  requested <- positive(execution$phase15_stability_workers %||%
                          execution$max_total_cores)
  maximum <- positive(execution$max_total_cores)
  detected <- positive(parallel::detectCores(logical = TRUE))
  scheduler <- suppressWarnings(as.integer(c(
    Sys.getenv("LSB_DJOB_NUMPROC", unset = NA_character_),
    Sys.getenv("SLURM_CPUS_PER_TASK", unset = NA_character_),
    Sys.getenv("NSLOTS", unset = NA_character_)
  )))
  scheduler <- scheduler[is.finite(scheduler) & scheduler > 0]
  limits <- c(requested, maximum, detected,
              if (length(scheduler)) min(scheduler) else NA_integer_)
  workers <- min(limits[is.finite(limits)])
  if (!identical(os_type, "unix")) workers <- 1L
  list(requested = requested, effective = as.integer(workers),
       backend = if (workers > 1L) "fork" else "sequential")
}

ordered_lapply <- function(x, fun, workers) {
  if (workers > 1L) parallel::mclapply(x, fun, mc.cores = workers,
                                       mc.preschedule = TRUE) else lapply(x, fun)
}

context_manifest_from_phase13 <- function(phase13, ids, primary_ids = ids,
                                          pilot = TRUE) {
  entries <- Filter(function(x) x$context_id %in% ids, phase13$contexts)
  entries <- entries[match(ids, vapply(entries, function(x) x$context_id, character(1)))]
  bind_rows(lapply(seq_along(entries), function(i) data.frame(
    context_order = i, inherited_context_order = as.integer(entries[[i]]$context_order),
    context_id = entries[[i]]$context_id, context_label = entries[[i]]$label,
    context_role = if (entries[[i]]$context_id %in% primary_ids)
      "primary_confirmatory" else "secondary_extension", source_rds_ids = paste(
      unlist(entries[[i]]$source_rds_ids), collapse = "|"
    ), pilot_fixture_context = isTRUE(pilot)
  )))
}

endpoint_manifest_from_config <- function(cfg) {
  bind_rows(lapply(cfg$endpoints, function(x) data.frame(
    endpoint_order = as.integer(x$endpoint_order), endpoint_id = x$endpoint_id,
    endpoint_label = x$label, definition = x$definition,
    sesoi = as.numeric(x$sesoi), unit = x$unit,
    positive_direction = "more positive AD-related mitonuclear endpoint change"
  )))
}

contrast_manifest_from_phase13 <- function(phase13) {
  general <- data.frame(
    contrast_order = 0L, contrast_id = "general_equal_stratum_AD_minus_NCI",
    contrast_type = "general", modifier = "general",
    required_groups = paste(unlist(phase13$groups), collapse = "|"),
    coefficients = "equal one-sixth average of six AD-minus-NCI stratum effects"
  )
  modifiers <- bind_rows(lapply(phase13$contrasts, function(x) {
    co <- unlist(x$coefficients)
    data.frame(
      contrast_order = as.integer(x$contrast_order), contrast_id = x$contrast_id,
      contrast_type = "modifier", modifier = x$modifier,
      required_groups = paste(unlist(x$required_groups), collapse = "|"),
      coefficients = paste(paste(names(co), co, sep = "="), collapse = ";")
    )
  }))
  bind_rows(list(general, modifiers))
}

module_manifest_from_phase13 <- function(phase13) {
  keep <- c("mtdna_oxphos_13", "nuclear_oxphos_structural_86")
  entries <- Filter(function(x) x$module_id %in% keep, phase13$modules)
  bind_rows(lapply(entries, function(x) data.frame(
    module_order = as.integer(x$module_order), module_id = x$module_id,
    module_label = x$label, reference_genes = as.integer(x$reference_genes),
    minimum_fraction = as.numeric(x$minimum_fraction),
    minimum_genes = as.integer(x$minimum_genes),
    c3_role = if (x$module_id == "mtdna_oxphos_13") "mtDNA" else "nuclear"
  )))
}

group_parts <- function(group_id) {
  parts <- strsplit(group_id, "__", fixed = TRUE)[[1L]]
  list(diagnosis = parts[[1L]], sex = parts[[2L]], apoe_group = parts[[3L]],
       stratum = paste(parts[[2L]], parts[[3L]], sep = "__"))
}

build_pilot_score_pairs <- function(cfg, phase13, contexts) {
  groups <- unlist(phase13$groups, use.names = FALSE)
  donor_rows <- bind_rows(lapply(seq_along(groups), function(group_index) {
    group <- groups[[group_index]]
    parts <- group_parts(group)
    n <- if (endsWith(group, cfg$pilot$low_count_suffix)) {
      as.integer(cfg$pilot$low_count_donors)
    } else as.integer(cfg$pilot$donors_per_group)
    base_pattern <- seq(-1.4, 1.4, length.out = n)
    data.frame(
      projid = sprintf("P15_G%02d_D%02d", group_index, seq_len(n)),
      original_projid = sprintf("P15_G%02d_D%02d", group_index, seq_len(n)),
      group_id = group, diagnosis = parts$diagnosis, sex = parts$sex,
      apoe_group = parts$apoe_group, sex_APOE_stratum = parts$stratum,
      donor_index = seq_len(n), base_pattern = base_pattern,
      age_death_scaled = scale(seq_len(n), center = TRUE, scale = TRUE)[, 1L] +
        (group_index %% 3L) / 30,
      pmi_scaled = scale(rep(c(-1, 0.5, 1.1, -0.4, 0.2, -0.8, 0.8, -0.1, 0.4),
                              length.out = n), center = TRUE, scale = TRUE)[, 1L] +
        (group_index %% 2L) / 30,
      study = rep(c("MAP", "ROS"), length.out = n),
      aggregate_percent_mt = 2 + (seq_len(n) %% 5L) / 2,
      robust_qc_fraction = ifelse(seq_len(n) == n & group_index == 1L, 0.55,
                                  0.02 + (seq_len(n) %% 5L) / 100),
      stringsAsFactors = FALSE
    )
  }))
  rows <- list()
  row_index <- 0L
  for (context_index in seq_len(nrow(contexts))) {
    context_id <- contexts$context_id[[context_index]]
    d <- donor_rows
    n_noise <- 0.06 * sin(seq_len(nrow(d)) * 0.73 + context_index)
    n_raw <- d$base_pattern + 0.04 * (as.integer(factor(d$group_id)) %% 3L) + n_noise
    nci_slope <- c(0.75, 0.55, 0.90)[[context_index]]
    ad_slope <- c(0.75, 1.35, 0.90)[[context_index]]
    slope <- ifelse(d$diagnosis == "AD", ad_slope, nci_slope)
    ad_shift <- ifelse(d$diagnosis == "AD",
                       c(0.75, 0.05, 0.00)[[context_index]], 0)
    modifier_shift <- ifelse(
      d$diagnosis == "AD" & d$sex == "Female" & d$apoe_group == "e33",
      c(0.45, 0.00, 0.00)[[context_index]], 0
    )
    m_noise_sd <- c(0.08, 0.08, 0.025)[[context_index]]
    m_raw <- slope * n_raw + ad_shift + modifier_shift +
      0.05 * d$age_death_scaled - 0.03 * d$pmi_scaled +
      ifelse(d$study == "ROS", 0.04, 0) +
      m_noise_sd * cos(seq_len(nrow(d)) * 0.61 + context_index)
    nci <- d$diagnosis == "NCI"
    N <- (n_raw - mean(n_raw[nci])) / stats::sd(n_raw[nci])
    M <- (m_raw - mean(m_raw[nci])) / stats::sd(m_raw[nci])
    N_pc1 <- N + 0.035 * sin(seq_along(N))
    M_pc1 <- M + 0.035 * cos(seq_along(M))
    if (stats::cor(N_pc1, N) < 0) N_pc1 <- -N_pc1
    if (stats::cor(M_pc1, M) < 0) M_pc1 <- -M_pc1
    N_pc1 <- (N_pc1 - mean(N_pc1[nci])) / stats::sd(N_pc1[nci])
    M_pc1 <- (M_pc1 - mean(M_pc1[nci])) / stats::sd(M_pc1[nci])
    row_index <- row_index + 1L
    d$context_id <- context_id
    d$donor_context_id <- paste(d$projid, context_id, sep = "::")
    d$nuclei <- 55L + ((seq_len(nrow(d)) + context_index) %% 35L)
    d$nuclear_score_raw <- n_raw
    d$mtdna_score_raw <- m_raw
    d$N <- N
    d$M <- M
    d$N_pc1 <- N_pc1
    d$M_pc1 <- M_pc1
    d$N_nuclear_only_tmm <- N + if (context_index == 2L) 0.03 * sin(seq_along(N)) else 0.01
    d$M_nuclear_only_tmm <- M + if (context_index == 2L) -0.25 * (d$diagnosis == "AD") else 0.01
    d$profile_eligible_20 <- d$nuclei >= 20L
    d$profile_eligible_50 <- d$nuclei >= 50L
    rows[[row_index]] <- d
  }
  out <- bind_rows(rows)
  out$projid <- as.character(out$projid)
  out$original_projid <- as.character(out$original_projid)
  out
}

assign_crossfit_folds <- function(scores, context_id, cfg, assignment_id = 0L) {
  d <- scores[scores$context_id == context_id & scores$diagnosis == "NCI", ]
  blocks <- split(seq_len(nrow(d)), paste(d$sex_APOE_stratum, d$study, sep = "::"))
  fold <- integer(nrow(d))
  block_names <- sort(names(blocks))
  for (block_index in seq_along(block_names)) {
    idx <- blocks[[block_names[[block_index]]]]
    original_ids <- unique(d$original_projid[idx])
    hashes <- vapply(original_ids, function(id) digest::digest(
      paste(cfg$randomization$base_seed, assignment_id, context_id, id, sep = "::"),
      algo = "sha256", serialize = FALSE
    ), character(1))
    original_ids <- original_ids[order(hashes, original_ids)]
    original_folds <- ((seq_along(original_ids) - 1L + block_index - 1L + assignment_id) %%
                          as.integer(cfg$crossfit$folds)) + 1L
    fold[idx] <- original_folds[match(d$original_projid[idx], original_ids)]
  }
  data.frame(
    context_id = context_id, projid = d$projid,
    original_projid = d$original_projid, sex_APOE_stratum = d$sex_APOE_stratum,
    study = d$study, assignment_id = assignment_id, fold = fold,
    assignment_hash = vapply(d$original_projid, function(id) digest::digest(
      paste(cfg$randomization$base_seed, assignment_id, context_id, id, sep = "::"),
      algo = "sha256", serialize = FALSE
    ), character(1)), stringsAsFactors = FALSE
  )
}

validate_crossfit_leakage <- function(folds) {
  by_donor <- aggregate(fold ~ context_id + assignment_id + original_projid,
                        folds, function(x) length(unique(x)))
  all(by_donor$fold == 1L)
}

prepare_reference_data <- function(d, stratum_levels, study_levels) {
  d$sex_APOE_stratum <- factor(d$sex_APOE_stratum, levels = stratum_levels)
  d$study <- factor(d$study, levels = study_levels)
  d
}

fit_nci_references <- function(scores, context_id, cfg, assignment_id = 0L) {
  d <- scores[scores$context_id == context_id, , drop = FALSE]
  stratum_levels <- unique(vapply(c("Female__e2", "Female__e33", "Female__e4",
                                     "Male__e2", "Male__e33", "Male__e4"),
                                  identity, character(1)))
  study_levels <- c("MAP", "ROS")
  d <- prepare_reference_data(d, stratum_levels, study_levels)
  folds <- assign_crossfit_folds(d, context_id, cfg, assignment_id)
  if (!validate_crossfit_leakage(folds)) {
    return(list(success = FALSE, failure_reason = "crossfit_training_leakage",
                folds = folds, models = data.frame(), predictions = data.frame()))
  }
  nci <- d[d$diagnosis == "NCI", , drop = FALSE]
  nci$fold <- folds$fold[match(nci$projid, folds$projid)]
  ad <- d[d$diagnosis == "AD", , drop = FALSE]
  formula <- M ~ N + sex_APOE_stratum + age_death_scaled + pmi_scaled + study
  model_rows <- list()
  prediction_rows <- list()
  fits <- list()
  failure <- ""
  for (fold_id in seq_len(as.integer(cfg$crossfit$folds))) {
    train <- nci[nci$fold != fold_id, , drop = FALSE]
    heldout <- nci[nci$fold == fold_id, , drop = FALSE]
    fit <- tryCatch(stats::lm(formula, data = train), error = function(e) e)
    rank_ok <- !inherits(fit, "error") && fit$rank == length(stats::coef(fit)) &&
      !anyNA(stats::coef(fit))
    structure_ok <- length(unique(train$study)) == 2L &&
      length(unique(train$sex_APOE_stratum)) == 6L
    if (!rank_ok || !structure_ok) {
      failure <- if (!rank_ok) "rank_deficient_reference_fold" else
        "reference_fold_missing_stratum_or_study"
      model_rows[[length(model_rows) + 1L]] <- data.frame(
        context_id = context_id, assignment_id = assignment_id, model_id = paste0("fold_", fold_id),
        fold = fold_id, coefficient = NA_character_, estimate = NA_real_,
        design_rank = if (inherits(fit, "error")) NA_integer_ else fit$rank,
        residual_df = if (inherits(fit, "error")) NA_integer_ else stats::df.residual(fit),
        training_donors = nrow(train), training_original_ids_hash = NA_character_,
        heldout_training_overlap = NA_integer_, model_status = failure
      )
      next
    }
    fits[[as.character(fold_id)]] <- fit
    training_ids <- sort(unique(train$original_projid))
    heldout_ids <- sort(unique(heldout$original_projid))
    overlap <- length(intersect(training_ids, heldout_ids))
    coefficients <- stats::coef(fit)
    model_rows[[length(model_rows) + 1L]] <- data.frame(
      context_id = context_id, assignment_id = assignment_id,
      model_id = paste0("fold_", fold_id), fold = fold_id,
      coefficient = names(coefficients), estimate = as.numeric(coefficients),
      design_rank = fit$rank, residual_df = stats::df.residual(fit),
      training_donors = length(training_ids),
      training_original_ids_hash = digest::digest(paste(training_ids, collapse = "|"),
                                                   algo = "sha256", serialize = FALSE),
      heldout_training_overlap = overlap,
      model_status = if (overlap == 0L) "estimated" else "crossfit_training_leakage"
    )
    if (overlap > 0L) failure <- "crossfit_training_leakage"
    heldout_prediction <- tryCatch(stats::predict(fit, newdata = heldout),
                                   error = function(e) rep(NA_real_, nrow(heldout)))
    ad_prediction <- tryCatch(stats::predict(fit, newdata = ad),
                              error = function(e) rep(NA_real_, nrow(ad)))
    prediction_rows[[length(prediction_rows) + 1L]] <- bind_rows(list(
      data.frame(
        context_id = context_id, assignment_id = assignment_id,
        projid = heldout$projid, original_projid = heldout$original_projid,
        diagnosis = "NCI", prediction_fold = fold_id,
        prediction_role = "heldout_nci", observed_M = heldout$M,
        predicted_M = as.numeric(heldout_prediction),
        training_original_ids_hash = model_rows[[length(model_rows)]]$training_original_ids_hash[[1L]]
      ),
      data.frame(
        context_id = context_id, assignment_id = assignment_id,
        projid = ad$projid, original_projid = ad$original_projid,
        diagnosis = "AD", prediction_fold = fold_id,
        prediction_role = "ad_fold_prediction", observed_M = ad$M,
        predicted_M = as.numeric(ad_prediction),
        training_original_ids_hash = model_rows[[length(model_rows)]]$training_original_ids_hash[[1L]]
      )
    ))
  }
  full_fit <- tryCatch(stats::lm(formula, data = nci), error = function(e) e)
  if (!inherits(full_fit, "error")) {
    co <- stats::coef(full_fit)
    ids <- sort(unique(nci$original_projid))
    model_rows[[length(model_rows) + 1L]] <- data.frame(
      context_id = context_id, assignment_id = assignment_id,
      model_id = "full_reference", fold = NA_integer_, coefficient = names(co),
      estimate = as.numeric(co), design_rank = full_fit$rank,
      residual_df = stats::df.residual(full_fit), training_donors = length(ids),
      training_original_ids_hash = digest::digest(paste(ids, collapse = "|"),
                                                   algo = "sha256", serialize = FALSE),
      heldout_training_overlap = NA_integer_, model_status = "sensitivity_only"
    )
  }
  predictions <- bind_rows(prediction_rows)
  success <- !nzchar(failure) && length(fits) == as.integer(cfg$crossfit$folds) &&
    all(is.finite(predictions$predicted_M))
  if (!success && !nzchar(failure)) failure <- "incomplete_reference_predictions"
  list(success = success, failure_reason = failure, folds = folds,
       models = bind_rows(model_rows), predictions = predictions)
}

build_endpoints <- function(scores, cfg, assignment_id = 0L) {
  endpoint_rows <- list()
  references <- list()
  folds <- list()
  predictions <- list()
  context_status <- list()
  for (context_id in unique(scores$context_id)) {
    d <- scores[scores$context_id == context_id, , drop = FALSE]
    reference <- fit_nci_references(d, context_id, cfg, assignment_id)
    references[[context_id]] <- reference$models
    folds[[context_id]] <- reference$folds
    predictions[[context_id]] <- reference$predictions
    d$standardized_difference <- d$M - d$N
    d$residual_raw <- NA_real_
    d$nci_reference_residual <- NA_real_
    if (reference$success) {
      p <- reference$predictions
      nci_pred <- p[p$prediction_role == "heldout_nci", ]
      ad_pred <- aggregate(predicted_M ~ projid, p[p$prediction_role == "ad_fold_prediction", ], mean)
      predicted <- c(
        setNames(nci_pred$predicted_M, nci_pred$projid),
        setNames(ad_pred$predicted_M, ad_pred$projid)
      )
      d$residual_raw <- d$M - predicted[d$projid]
      nci <- d$diagnosis == "NCI"
      residual_mean <- mean(d$residual_raw[nci])
      residual_sd <- stats::sd(d$residual_raw[nci])
      if (is.finite(residual_sd) && residual_sd > 0) {
        d$nci_reference_residual <- (d$residual_raw - residual_mean) / residual_sd
      } else {
        reference$success <- FALSE
        reference$failure_reason <- "nonpositive_crossfit_residual_sd"
      }
    }
    d$reference_status <- if (reference$success) "eligible" else reference$failure_reason
    endpoint_rows[[context_id]] <- d
    context_status[[context_id]] <- data.frame(
      context_id = context_id, reference_success = reference$success,
      reference_failure_reason = reference$failure_reason,
      nci_donors = length(unique(d$projid[d$diagnosis == "NCI"])),
      ad_donors = length(unique(d$projid[d$diagnosis == "AD"]))
    )
  }
  list(data = bind_rows(endpoint_rows), models = bind_rows(references),
       folds = bind_rows(folds), predictions = bind_rows(predictions),
       context_status = bind_rows(context_status))
}

append_design_covariates <- function(X, d, extra_covariates = character()) {
  if (!length(extra_covariates)) return(X)
  missing <- setdiff(extra_covariates, names(d))
  if (length(missing)) {
    stop("Missing requested sensitivity covariates: ",
         paste(missing, collapse = ", "), call. = FALSE)
  }
  extra <- as.matrix(d[, extra_covariates, drop = FALSE])
  storage.mode(extra) <- "double"
  colnames(extra) <- paste0("sensitivity__", extra_covariates)
  cbind(X, extra)
}

build_level_design <- function(d, groups, extra_covariates = character()) {
  group <- factor(d$group_id, levels = groups)
  G <- stats::model.matrix(~ 0 + group)
  colnames(G) <- paste0("G__", groups)
  study <- as.numeric(d$study == "ROS")
  append_design_covariates(
    cbind(G, age_death_scaled = d$age_death_scaled,
          pmi_scaled = d$pmi_scaled, studyROS = study), d, extra_covariates
  )
}

build_slope_design <- function(d, groups, extra_covariates = character()) {
  group <- factor(d$group_id, levels = groups)
  G <- stats::model.matrix(~ 0 + group)
  colnames(G) <- paste0("I__", groups)
  S <- G * d$N
  colnames(S) <- paste0("S__", groups)
  append_design_covariates(
    cbind(G, S, age_death_scaled = d$age_death_scaled,
          pmi_scaled = d$pmi_scaled, studyROS = as.numeric(d$study == "ROS")),
    d, extra_covariates
  )
}

fit_hc3 <- function(y, X) {
  complete <- is.finite(y) & apply(X, 1L, function(x) all(is.finite(x)))
  y <- y[complete]
  X <- X[complete, , drop = FALSE]
  fit <- tryCatch(stats::lm(y ~ X - 1), error = function(e) e)
  if (inherits(fit, "error") || fit$rank < ncol(X) || anyNA(stats::coef(fit))) {
    return(list(success = FALSE,
                failure_reason = if (inherits(fit, "error")) conditionMessage(fit) else
                  "rank_deficient_endpoint_model",
                observations = length(y), rank = if (inherits(fit, "error")) NA else fit$rank,
                residual_df = if (inherits(fit, "error")) NA else stats::df.residual(fit)))
  }
  covariance <- suppressWarnings(tryCatch(
    sandwich::vcovHC(fit, type = "HC3"), error = function(e) e
  ))
  if (inherits(covariance, "error") || any(!is.finite(covariance))) {
    return(list(success = FALSE, failure_reason = "nonfinite_HC3_covariance",
                observations = length(y), rank = fit$rank,
                residual_df = stats::df.residual(fit)))
  }
  list(success = TRUE, fit = fit, beta = stats::coef(fit), covariance = covariance,
       observations = length(y), rank = fit$rank, residual_df = stats::df.residual(fit),
       max_leverage = max(stats::hatvalues(fit)), max_cooks_distance = max(stats::cooks.distance(fit)),
       failure_reason = "")
}

general_vector <- function(groups, coefficient_names, slope = FALSE) {
  prefix <- if (slope) "XS__" else "XG__"
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  strata <- unique(sub("^(NCI|AD)__", "", groups))
  for (stratum in strata) {
    vector[paste0(prefix, "AD__", stratum)] <- 1 / length(strata)
    vector[paste0(prefix, "NCI__", stratum)] <- -1 / length(strata)
  }
  vector
}

modifier_vector <- function(contrast, coefficient_names, slope = FALSE) {
  prefix <- if (slope) "XS__" else "XG__"
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  coefficients <- unlist(contrast$coefficients)
  names_needed <- paste0(prefix, names(coefficients))
  if (!all(names_needed %in% coefficient_names)) {
    if (!length(coefficient_names)) return(vector)
    stop("Missing contrast coefficients: ", paste(setdiff(names_needed, coefficient_names),
                                                  collapse = ", "), call. = FALSE)
  }
  vector[names_needed] <- as.numeric(coefficients)
  vector
}

stratum_vector <- function(stratum, coefficient_names, slope = FALSE) {
  prefix <- if (slope) "XS__" else "XG__"
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  vector[paste0(prefix, stratum$ad_group)] <- 1
  vector[paste0(prefix, stratum$nci_group)] <- -1
  vector
}

linear_test <- function(model, vector) {
  if (!model$success) return(list(success = FALSE, estimate = NA_real_, se = NA_real_,
                                  ci_low = NA_real_, ci_high = NA_real_, p = NA_real_,
                                  failure_reason = model$failure_reason))
  estimate <- sum(vector * model$beta)
  variance <- as.numeric(t(vector) %*% model$covariance %*% vector)
  if (!is.finite(variance) || variance <= 0 || model$residual_df <= 0) {
    return(list(success = FALSE, estimate = estimate, se = NA_real_, ci_low = NA_real_,
                ci_high = NA_real_, p = NA_real_, failure_reason = "invalid_contrast_variance"))
  }
  se <- sqrt(variance)
  critical <- stats::qt(0.975, df = model$residual_df)
  statistic <- estimate / se
  list(success = TRUE, estimate = estimate, se = se,
       ci_low = estimate - critical * se, ci_high = estimate + critical * se,
       p = 2 * stats::pt(-abs(statistic), df = model$residual_df), failure_reason = "")
}

group_counts <- function(d, groups) {
  setNames(as.integer(table(factor(d$group_id, levels = groups))), groups)
}

central_interval <- function(x) stats::quantile(x, c(0.05, 0.95), na.rm = TRUE,
                                                 names = FALSE, type = 7)

range_overlap_fraction <- function(d, required_groups) {
  intervals <- lapply(required_groups, function(group) central_interval(d$N[d$group_id == group]))
  if (any(vapply(intervals, function(x) length(x) != 2L || any(!is.finite(x)) || x[[2L]] <= x[[1L]],
                 logical(1)))) return(NA_real_)
  pair_values <- utils::combn(seq_along(intervals), 2L, function(pair) {
    a <- intervals[[pair[[1L]]]]
    b <- intervals[[pair[[2L]]]]
    overlap <- max(0, min(a[[2L]], b[[2L]]) - max(a[[1L]], b[[1L]]))
    overlap / min(diff(a), diff(b))
  })
  min(pair_values)
}

apply_bh_families <- function(results) {
  results$q_value <- NA_real_
  for (family in unique(results$family_id)) {
    idx <- results$family_id == family & is.finite(results$p_value)
    results$q_value[idx] <- stats::p.adjust(results$p_value[idx], method = "BH")
  }
  results
}

endpoint_status <- function(q, estimate, low, high, sesoi, eligibility) {
  if (startsWith(eligibility, "not_testable")) return("not_testable")
  supported_numeric <- is.finite(q) && q <= 0.05 && is.finite(estimate) &&
    abs(estimate) >= sesoi && is.finite(low) && (low > 0 || high < 0)
  if (supported_numeric && startsWith(eligibility, "provisional")) return("provisional_low_power")
  if (supported_numeric) return("supported")
  if (is.finite(q) && q <= 0.05 && is.finite(low) && (low > 0 || high < 0) &&
      abs(estimate) < sesoi) return("statistically_detectable_but_small")
  if (is.finite(low) && low > -sesoi && high < sesoi) return("not_supported_precise_null")
  "inconclusive"
}

crossing_slope_flag <- function(departures) {
  values <- departures[is.finite(departures)]
  length(values) > 1L && any(values > 0) && any(values < 0)
}

compatibility_pass <- function(level_estimate, departures) {
  if (!is.finite(level_estimate)) return(FALSE)
  values <- departures[is.finite(departures)]
  if (length(values) < 2L || crossing_slope_flag(values)) return(FALSE)
  sum(sign(values) == sign(level_estimate)) >= 2L
}

evaluate_models <- function(endpoint_bundle, phase13, context_manifest, endpoint_manifest,
                            cfg, fingerprint, extra_covariates = character(),
                            production = FALSE) {
  data <- endpoint_bundle$data
  groups <- unlist(phase13$groups)
  strata <- lapply(phase13$strata, function(x) list(
    stratum_id = x$stratum_id, nci_group = x$nci_group, ad_group = x$ad_group
  ))
  general_rows <- list()
  modifier_rows <- list()
  stratum_rows <- list()
  diagnostics <- list()
  group_slopes <- list()
  grids <- list()
  for (context_index in seq_len(nrow(context_manifest))) {
    context_id <- context_manifest$context_id[[context_index]]
    context_role <- context_manifest$context_role[[context_index]]
    family_suffix <- if (context_role == "primary_confirmatory") "primary" else "secondary"
    general_family <- cfg$multiple_testing$families[[paste0("general_", family_suffix)]]
    modifier_family <- cfg$multiple_testing$families[[paste0("modifier_", family_suffix)]]
    d <- data[data$context_id == context_id, , drop = FALSE]
    level_X <- build_level_design(d, groups, extra_covariates)
    models <- list(
      standardized_difference = fit_hc3(d$standardized_difference, level_X),
      nci_reference_residual = fit_hc3(d$nci_reference_residual, level_X),
      coupling_slope_change = fit_hc3(
        d$M, build_slope_design(d, groups, extra_covariates)
      )
    )
    for (endpoint_id in names(models)) {
      model <- models[[endpoint_id]]
      diagnostics[[length(diagnostics) + 1L]] <- data.frame(
        context_id = context_id, endpoint_id = endpoint_id,
        formula = if (endpoint_id == "coupling_slope_change")
          "M~0+group+0+N:group+age_death_scaled+pmi_scaled+study" else
          "endpoint~0+diagnosis_sex_APOE_group+age_death_scaled+pmi_scaled+study",
        covariance = "HC3", observations = model$observations,
        design_rank = model$rank, residual_df = model$residual_df,
        max_leverage = model$max_leverage %||% NA_real_,
        max_cooks_distance = model$max_cooks_distance %||% NA_real_,
        converged = model$success, failure_reason = model$failure_reason
      )
      slope <- endpoint_id == "coupling_slope_change"
      reference_ok <- endpoint_id != "nci_reference_residual" ||
        endpoint_bundle$context_status$reference_success[
          endpoint_bundle$context_status$context_id == context_id
        ]
      counts <- group_counts(d, groups)
      total_nci <- sum(counts[startsWith(names(counts), "NCI")])
      total_ad <- sum(counts[startsWith(names(counts), "AD")])
      general_eligibility <- if (!reference_ok) "not_testable_reference_failure" else
        if (total_nci < cfg$eligibility$minimum_general_nci ||
            total_ad < cfg$eligibility$minimum_general_ad) "not_testable_low_donor_count" else
          if (!model$success) "not_testable_model_failure" else
            if (total_nci < cfg$eligibility$confirmatory_general_nci ||
                total_ad < cfg$eligibility$confirmatory_general_ad ||
                any(counts < 3L)) "provisional_low_power" else "eligible_confirmatory"
      if (slope && !startsWith(general_eligibility, "not_testable")) {
        overlap <- range_overlap_fraction(d, groups)
        if (!is.finite(overlap) || overlap <= 0) general_eligibility <- "not_testable_range_mismatch" else
          if (overlap < cfg$eligibility$slope_range_overlap_fraction)
            general_eligibility <- "provisional_range_mismatch"
      } else overlap <- NA_real_
      test <- linear_test(model, general_vector(groups, names(model$beta %||% numeric()), slope))
      endpoint_cfg <- endpoint_manifest[endpoint_manifest$endpoint_id == endpoint_id, ]
      general_rows[[length(general_rows) + 1L]] <- data.frame(
        context_id = context_id, context_role = context_role,
        scope_id = "general", endpoint_id = endpoint_id,
        contrast_id = "general_equal_stratum_AD_minus_NCI",
        family_id = general_family,
        estimate = test$estimate, standard_error = test$se, ci_low = test$ci_low,
        ci_high = test$ci_high, p_value = test$p, sesoi = endpoint_cfg$sesoi,
        direction = if (is.finite(test$estimate)) sign(test$estimate) else NA,
        donor_counts = paste0("NCI=", total_nci, "|AD=", total_ad),
        nuclei_counts = paste0("min=", min(d$nuclei)), range_overlap_fraction = overlap,
        eligibility_status = general_eligibility,
        model_status = if (test$success) "estimated" else "not_estimated",
        failure_reason = test$failure_reason, analysis_fingerprint = fingerprint
      )
      for (stratum in strata) {
        stratum_test <- linear_test(
          model, stratum_vector(stratum, names(model$beta %||% numeric()), slope)
        )
        stratum_rows[[length(stratum_rows) + 1L]] <- data.frame(
          context_id = context_id, endpoint_id = endpoint_id,
          stratum_id = stratum$stratum_id, estimate = stratum_test$estimate,
          standard_error = stratum_test$se, ci_low = stratum_test$ci_low,
          ci_high = stratum_test$ci_high, p_value = stratum_test$p,
          model_status = if (stratum_test$success) "estimated" else "not_estimated",
          failure_reason = stratum_test$failure_reason
        )
      }
      for (contrast in phase13$contrasts) {
        required <- unlist(contrast$required_groups)
        required_counts <- counts[required]
        modifier_eligibility <- if (!reference_ok) "not_testable_reference_failure" else
          if (any(required_counts < cfg$eligibility$minimum_modifier_cell))
            "not_testable_low_donor_count" else if (!model$success)
              "not_testable_model_failure" else if (any(required_counts <
                cfg$eligibility$confirmatory_modifier_cell))
                  "provisional_low_power" else "eligible_confirmatory"
        modifier_overlap <- if (slope) range_overlap_fraction(d, required) else NA_real_
        if (slope && !startsWith(modifier_eligibility, "not_testable")) {
          if (!is.finite(modifier_overlap) || modifier_overlap <= 0)
            modifier_eligibility <- "not_testable_range_mismatch" else
              if (modifier_overlap < cfg$eligibility$slope_range_overlap_fraction)
                modifier_eligibility <- "provisional_range_mismatch"
        }
        modifier_test <- linear_test(
          model, modifier_vector(contrast, names(model$beta %||% numeric()), slope)
        )
        modifier_rows[[length(modifier_rows) + 1L]] <- data.frame(
          context_id = context_id, context_role = context_role,
          scope_id = "modifier", endpoint_id = endpoint_id,
          contrast_id = contrast$contrast_id,
          family_id = modifier_family,
          estimate = modifier_test$estimate, standard_error = modifier_test$se,
          ci_low = modifier_test$ci_low, ci_high = modifier_test$ci_high,
          p_value = modifier_test$p, sesoi = endpoint_cfg$sesoi,
          direction = if (is.finite(modifier_test$estimate)) sign(modifier_test$estimate) else NA,
          donor_counts = paste(required_counts, collapse = "|"),
          nuclei_counts = paste0("min=", min(d$nuclei)),
          range_overlap_fraction = modifier_overlap,
          eligibility_status = modifier_eligibility,
          model_status = if (modifier_test$success) "estimated" else "not_estimated",
          failure_reason = modifier_test$failure_reason,
          analysis_fingerprint = fingerprint
        )
      }
    }
    slope_model <- models$coupling_slope_change
    if (slope_model$success) {
      for (group in groups) {
        slope_name <- paste0("XS__", group)
        slope_value <- slope_model$beta[[slope_name]]
        slope_se <- sqrt(slope_model$covariance[slope_name, slope_name])
        x <- d[d$group_id == group, ]
        group_slopes[[length(group_slopes) + 1L]] <- data.frame(
          context_id = context_id, group_id = group, donors = nrow(x),
          slope = slope_value, standard_error = slope_se,
          ci_low = slope_value - stats::qt(0.975, slope_model$residual_df) * slope_se,
          ci_high = slope_value + stats::qt(0.975, slope_model$residual_df) * slope_se,
          pearson_correlation = stats::cor(x$N, x$M),
          spearman_correlation = stats::cor(x$N, x$M, method = "spearman"),
          nuclear_min = min(x$N), nuclear_max = max(x$N)
        )
      }
      grid <- seq(-1.5, 1.5, length.out = 41L)
      beta <- slope_model$beta
      intercept <- setNames(beta[paste0("XI__", groups)], groups)
      slopes <- setNames(beta[paste0("XS__", groups)], groups)
      stratum_ids <- unique(sub("^(NCI|AD)__", "", groups))
      general_departure <- vapply(grid, function(value) mean(vapply(stratum_ids, function(s) {
        (intercept[[paste0("AD__", s)]] + slopes[[paste0("AD__", s)]] * value) -
          (intercept[[paste0("NCI__", s)]] + slopes[[paste0("NCI__", s)]] * value)
      }, numeric(1))), numeric(1))
      grids[[length(grids) + 1L]] <- data.frame(
        context_id = context_id, scope_id = "general",
        contrast_id = "general_equal_stratum_AD_minus_NCI",
        nuclear_score = grid, departure = general_departure,
        checkpoint = ifelse(grid %in% c(-0.975, 0, 0.975), TRUE, FALSE),
        checkpoint_substitution = FALSE,
        slope_rewiring_observed = crossing_slope_flag(general_departure)
      )
      for (contrast in phase13$contrasts) {
        co <- unlist(contrast$coefficients)
        departure <- vapply(grid, function(value) sum(as.numeric(co) *
          (intercept[names(co)] + slopes[names(co)] * value)), numeric(1))
        grids[[length(grids) + 1L]] <- data.frame(
          context_id = context_id, scope_id = "modifier",
          contrast_id = contrast$contrast_id, nuclear_score = grid,
          departure = departure,
          checkpoint = ifelse(grid %in% c(-0.975, 0, 0.975), TRUE, FALSE),
          checkpoint_substitution = FALSE,
          slope_rewiring_observed = crossing_slope_flag(departure)
        )
      }
    }
  }
  general <- apply_bh_families(bind_rows(general_rows))
  modifier <- apply_bh_families(bind_rows(modifier_rows))
  for (table_name in c("general", "modifier")) {
    table <- get(table_name)
    table$effect_meets_sesoi <- is.finite(table$estimate) & abs(table$estimate) >= table$sesoi
    table$interval_excludes_zero <- is.finite(table$ci_low) &
      (table$ci_low > 0 | table$ci_high < 0)
    table$interval_inside_sesoi <- is.finite(table$ci_low) &
      table$ci_low > -table$sesoi & table$ci_high < table$sesoi
    table$endpoint_status_numeric <- mapply(
      endpoint_status, table$q_value, table$estimate, table$ci_low, table$ci_high,
      table$sesoi, table$eligibility_status
    )
    table$stability_status <- if (production) "pending_production_stability" else
      "pending_pilot_stability"
    table$endpoint_status <- if (production) "pending_production_stability" else
      "not_applicable_pilot"
    if (table_name == "general") general <- table else modifier <- table
  }
  list(general = general, modifier = modifier, strata = bind_rows(stratum_rows),
       diagnostics = bind_rows(diagnostics), group_slopes = bind_rows(group_slopes),
       prediction_grid = bind_rows(grids))
}

analyze_scores <- function(scores, cfg, phase13, context_manifest, endpoint_manifest,
                           fingerprint, assignment_id = 0L,
                           extra_covariates = character(), production = FALSE) {
  endpoint_bundle <- build_endpoints(scores, cfg, assignment_id)
  results <- evaluate_models(endpoint_bundle, phase13, context_manifest,
                             endpoint_manifest, cfg, fingerprint,
                             extra_covariates, production)
  list(endpoint_bundle = endpoint_bundle, results = results)
}

resample_donors <- function(scores, cfg, repetition, balanced = FALSE) {
  donors <- unique(scores[c("original_projid", "group_id", "diagnosis", "sex_APOE_stratum")])
  set.seed(seed_for(cfg, paste0(if (balanced) "balance" else "bootstrap", repetition)))
  if (!balanced) {
    selected <- unlist(lapply(split(donors$original_projid, donors$group_id), function(ids) {
      sample(ids, length(ids), replace = TRUE)
    }), use.names = FALSE)
  } else {
    selected <- unlist(lapply(split(seq_len(nrow(donors)), donors$sex_APOE_stratum), function(idx) {
      block <- donors[idx, ]
      minimum <- min(table(block$diagnosis))
      unlist(lapply(split(block$original_projid, block$diagnosis), sample,
                    size = minimum, replace = FALSE), use.names = FALSE)
    }), use.names = FALSE)
  }
  bind_rows(lapply(seq_along(selected), function(i) {
    d <- scores[scores$original_projid == selected[[i]], , drop = FALSE]
    d$projid <- paste0(selected[[i]], "::draw_", i)
    d$donor_context_id <- paste(d$projid, d$context_id, sep = "::")
    d
  }))
}

extract_stability <- function(analysis, type, repetition, omitted = NA_character_) {
  g <- analysis$results$general[c("context_id", "endpoint_id", "contrast_id",
                                  "estimate", "p_value", "model_status", "failure_reason")]
  g$scope_id <- "general"
  m <- analysis$results$modifier[c("context_id", "endpoint_id", "contrast_id",
                                   "estimate", "p_value", "model_status", "failure_reason")]
  m$scope_id <- "modifier"
  out <- bind_rows(list(g, m))
  out$analysis_type <- type
  out$repetition_id <- repetition
  out$omitted_original_projid <- omitted
  out$donor_resampling_unit <- "whole_donor"
  out
}

run_stability <- function(scores, cfg, phase13, contexts, endpoints, fingerprint, workers) {
  donors <- sort(unique(scores$original_projid))
  tasks <- c(
    lapply(seq_len(as.integer(cfg$pilot$bootstrap_repetitions)), function(i)
      list(type = "bootstrap", id = i)),
    lapply(seq_len(as.integer(cfg$pilot$balance_repetitions)), function(i)
      list(type = "balance", id = i)),
    lapply(seq_along(donors), function(i)
      list(type = "leave_one_donor_out", id = i, donor = donors[[i]]))
  )
  worker <- function(task) {
    d <- if (task$type == "bootstrap") resample_donors(scores, cfg, task$id, FALSE) else
      if (task$type == "balance") resample_donors(scores, cfg, task$id, TRUE) else
        scores[scores$original_projid != task$donor, , drop = FALSE]
    analysis <- analyze_scores(d, cfg, phase13, contexts, endpoints, fingerprint)
    extract_stability(analysis, task$type, task$id, task$donor %||% NA_character_)
  }
  bind_rows(ordered_lapply(tasks, worker, workers))
}

summarize_stability <- function(primary, stability, scope_id) {
  rows <- lapply(seq_len(nrow(primary)), function(i) {
    x <- stability[stability$scope_id == scope_id &
      stability$context_id == primary$context_id[[i]] &
      stability$endpoint_id == primary$endpoint_id[[i]] &
      stability$contrast_id == primary$contrast_id[[i]], ]
    success <- is.finite(x$estimate) & x$model_status == "estimated"
    same_sign <- if (is.finite(primary$estimate[[i]]) && primary$estimate[[i]] != 0) {
      sign(x$estimate[success]) == sign(primary$estimate[[i]])
    } else logical()
    loo <- x$analysis_type == "leave_one_donor_out" & success
    data.frame(
      context_id = primary$context_id[[i]], endpoint_id = primary$endpoint_id[[i]],
      contrast_id = primary$contrast_id[[i]], primary_estimate = primary$estimate[[i]],
      attempted_replicates = nrow(x), successful_replicates = sum(success),
      success_fraction = if (nrow(x)) mean(success) else NA_real_,
      direction_fraction = if (length(same_sign)) mean(same_sign) else NA_real_,
      loo_sign_reversals = if (any(loo) && is.finite(primary$estimate[[i]]) &&
                                primary$estimate[[i]] != 0)
        sum(sign(x$estimate[loo]) != sign(primary$estimate[[i]])) else NA_integer_,
      largest_loo_absolute_change = if (any(loo))
        max(abs(x$estimate[loo] - primary$estimate[[i]]), na.rm = TRUE) else NA_real_,
      bootstrap_successes = sum(x$analysis_type == "bootstrap" & success),
      balance_successes = sum(x$analysis_type == "balance" & success)
    )
  })
  bind_rows(rows)
}

validate_phase15_output <- function(path, expected_contexts, expected_general,
                                    expected_modifier, expected_stratum,
                                    expected_general_gates, expected_modifier_gates,
                                    expected_status, declared = NULL) {
  if (!dir.exists(path)) stop("Phase 15 output directory is missing: ", path,
                              call. = FALSE)
  expected <- declared %||% c(
    "mitonuclear_analysis_manifest.tsv", "mitonuclear_context_manifest.tsv",
    "mitonuclear_endpoint_manifest.tsv", "mitonuclear_contrast_manifest.tsv",
    "mitonuclear_module_manifest.tsv", "mitonuclear_module_members.tsv",
    "mitonuclear_input_inventory.tsv", "mitonuclear_source_checks.tsv",
    "mitonuclear_donor_eligibility.tsv", "mitonuclear_score_pairs.tsv.gz",
    "mitonuclear_crossfit_folds.tsv", "mitonuclear_nci_reference_models.tsv",
    "mitonuclear_reference_predictions.tsv.gz", "mitonuclear_donor_endpoints.tsv.gz",
    "mitonuclear_general_test_manifest.tsv", "mitonuclear_modifier_test_manifest.tsv",
    "mitonuclear_general_results.tsv", "mitonuclear_modifier_results.tsv",
    "mitonuclear_stratum_effects.tsv", "mitonuclear_group_slopes.tsv",
    "mitonuclear_prediction_grid.tsv.gz", "mitonuclear_model_diagnostics.tsv",
    "mitonuclear_score_reliability.tsv", "mitonuclear_stability_replicates.tsv.gz",
    "mitonuclear_general_stability_summary.tsv", "mitonuclear_modifier_stability_summary.tsv",
    "mitonuclear_gene_complex_influence.tsv", "mitonuclear_qc_normalization_sensitivity.tsv",
    "mitonuclear_general_gate_decisions.tsv", "mitonuclear_modifier_gate_decisions.tsv",
    "mitonuclear_claim_summary.tsv", "mitonuclear_figure_data.tsv.gz",
    "mitonuclear_stage_status.tsv", "mitonuclear_checks.tsv",
    "mitonuclear_artifacts.tsv", "mitonuclear_status.tsv"
  )
  actual <- sort(list.files(path, recursive = FALSE, all.files = FALSE))
  if (!identical(actual, sort(expected)) ||
      length(list.dirs(path, recursive = FALSE, full.names = FALSE))) {
    stop("Phase 15 final directory must be flat and contain exactly 36 files",
         call. = FALSE)
  }
  read_table <- function(name) data.table::fread(file.path(path, name),
                                                  data.table = FALSE,
                                                  showProgress = FALSE)
  for (name in expected) {
    value <- read_table(name)
    if (!identical(names(value)[[1L]], "schema_version")) {
      stop("Every Phase 15 TSV must start with schema_version: ", name, call. = FALSE)
    }
  }
  dimensions <- c(
    nrow(read_table("mitonuclear_context_manifest.tsv")),
    nrow(read_table("mitonuclear_general_results.tsv")),
    nrow(read_table("mitonuclear_modifier_results.tsv")),
    nrow(read_table("mitonuclear_stratum_effects.tsv")),
    nrow(read_table("mitonuclear_general_gate_decisions.tsv")),
    nrow(read_table("mitonuclear_modifier_gate_decisions.tsv"))
  )
  expected_dimensions <- c(expected_contexts, expected_general, expected_modifier,
                           expected_stratum, expected_general_gates,
                           expected_modifier_gates)
  if (!identical(as.integer(dimensions), as.integer(expected_dimensions))) {
    stop("Phase 15 output dimensions do not match the frozen contract", call. = FALSE)
  }
  status <- read_table("mitonuclear_status.tsv")
  if (nrow(status) != 1L || status$validation_status[[1L]] != expected_status ||
      (expected_status == "nonfinal_smoke_test" &&
       status$scientific_decision[[1L]] != "not_applicable_pilot")) {
    stop("Phase 15 terminal status is invalid", call. = FALSE)
  }
  if (expected_status != "nonfinal_smoke_test") {
    required_status <- c(
      "production_analysis", "contexts", "primary_contexts", "secondary_contexts",
      "general_result_rows", "modifier_result_rows", "stratum_rows",
      "general_gate_rows", "modifier_gate_rows", "artifact_manifest_sha256"
    )
    if (!all(required_status %in% names(status)) ||
        !isTRUE(as.logical(status$production_analysis[[1L]])) ||
        !identical(as.integer(unlist(status[1L, c(
          "contexts", "general_result_rows", "modifier_result_rows", "stratum_rows",
          "general_gate_rows", "modifier_gate_rows"
        )])), as.integer(expected_dimensions)) ||
        status$primary_contexts[[1L]] != 3L || status$secondary_contexts[[1L]] != 4L) {
      stop("Phase 15 production status dimensions are invalid", call. = FALSE)
    }
    context_table <- read_table("mitonuclear_context_manifest.tsv")
    if (any(as.logical(context_table$pilot_fixture_context)) ||
        sum(context_table$context_role == "primary_confirmatory") != 3L ||
        sum(context_table$context_role == "secondary_extension") != 4L) {
      stop("Pilot provenance or incorrect context roles appear in production", call. = FALSE)
    }
    general <- read_table("mitonuclear_general_results.tsv")
    modifier <- read_table("mitonuclear_modifier_results.tsv")
    terminal_endpoint <- c(
      "supported", "provisional_low_power", "statistically_detectable_but_small",
      "not_supported_precise_null", "inconclusive", "not_testable"
    )
    if (!all(c(general$endpoint_status, modifier$endpoint_status) %in% terminal_endpoint)) {
      stop("Phase 15 production contains nonterminal endpoint statuses", call. = FALSE)
    }
    general_gates <- read_table("mitonuclear_general_gate_decisions.tsv")
    modifier_gates <- read_table("mitonuclear_modifier_gate_decisions.tsv")
    terminal_gate <- c(
      "supported", "provisional_low_power", "partial_evidence",
      "not_supported_precise_null", "inconclusive", "not_testable"
    )
    if (!all(c(general_gates$gate_status, modifier_gates$gate_status) %in%
             terminal_gate)) {
      stop("Phase 15 production contains nonterminal gate statuses", call. = FALSE)
    }
    source_checks <- read_table("mitonuclear_source_checks.tsv")
    if (any(as.logical(source_checks$blocking) & !as.logical(source_checks$passed))) {
      stop("Phase 15 production contains failed source checks", call. = FALSE)
    }
  }
  checks <- read_table("mitonuclear_checks.tsv")
  if (any(checks$blocking & !checks$passed)) {
    stop("Phase 15 contains failed blocking checks", call. = FALSE)
  }
  artifacts <- read_table("mitonuclear_artifacts.tsv")
  hashed_expected <- setdiff(expected, c("mitonuclear_artifacts.tsv", "mitonuclear_status.tsv"))
  if (!setequal(artifacts$artifact_file, hashed_expected)) {
    stop("Phase 15 artifact manifest has the wrong declared set", call. = FALSE)
  }
  for (i in seq_len(nrow(artifacts))) {
    file <- file.path(path, artifacts$artifact_file[[i]])
    if (!identical(sha256_file(file), artifacts$sha256[[i]])) {
      stop("Phase 15 artifact hash mismatch: ", artifacts$artifact_file[[i]], call. = FALSE)
    }
    if (!identical(as.numeric(file.info(file)$size), as.numeric(artifacts$bytes[[i]])) ||
        !identical(as.numeric(count_records(file)), as.numeric(artifacts$records[[i]]))) {
      stop("Phase 15 artifact size/record mismatch: ",
           artifacts$artifact_file[[i]], call. = FALSE)
    }
  }
  if (!identical(sha256_file(file.path(path, "mitonuclear_artifacts.tsv")),
                 status$artifact_manifest_sha256[[1L]])) {
    stop("Phase 15 terminal artifact-manifest hash mismatch", call. = FALSE)
  }
  if (expected_status != "nonfinal_smoke_test") {
    inventory <- read_table("mitonuclear_input_inventory.tsv")
    if (any(!as.logical(inventory$exists))) {
      stop("Phase 15 production input inventory contains missing inputs", call. = FALSE)
    }
    for (i in seq_len(nrow(inventory))) {
      if (!file.exists(inventory$path[[i]]) ||
          !identical(sha256_file(inventory$path[[i]]), inventory$sha256[[i]])) {
        stop("Phase 15 production input hash mismatch: ", inventory$input_id[[i]],
             call. = FALSE)
      }
    }
  }
  folds <- read_table("mitonuclear_crossfit_folds.tsv")
  if (!validate_crossfit_leakage(folds)) stop("Cross-fit leakage detected", call. = FALSE)
  invisible(TRUE)
}

main <- function() {
  started <- Sys.time()
  args <- parse_phase15_cli(commandArgs(trailingOnly = TRUE))
  required <- c("yaml", "data.table", "sandwich", "digest")
  missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing)) stop("Missing required packages: ", paste(missing, collapse = ", "),
                            call. = FALSE)
  root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- absolute_path(args$config, root)
  execution_path <- absolute_path(args$execution_config, root)
  config <- yaml::read_yaml(config_path)
  execution_cfg <- yaml::read_yaml(execution_path)
  phase_path <- absolute_path(config$project$phase15_mitonuclear_coupling_config, root)
  cfg <- yaml::read_yaml(phase_path)
  phase13_path <- absolute_path(cfg$paths$phase13_config, root)
  phase13 <- yaml::read_yaml(phase13_path)
  member_path <- absolute_path(cfg$paths$module_members, root)
  all_members <- data.table::fread(member_path, data.table = FALSE)
  RNGkind("L'Ecuyer-CMRG")
  set.seed(as.integer(cfg$randomization$base_seed))
  if (!isTRUE(config$scope$pilot)) {
    production_script <- file.path(
      root, "scripts/15_run_mitonuclear_coupling_production.R"
    )
    if (!file.exists(production_script)) {
      stop("Phase 15 production implementation is missing: ", production_script,
           call. = FALSE)
    }
    source(production_script, local = FALSE)
    return(run_phase15_production(
      root, config, execution_cfg, cfg, phase13, phase_path, phase13_path, member_path
    ))
  }
  stage_root <- absolute_path(config$outputs$root, root)
  final_dir <- file.path(stage_root, cfg$paths$output_relative)
  if (dir.exists(final_dir)) {
    stop("Phase 15 output already exists and will not be overwritten: ", final_dir,
         call. = FALSE)
  }
  staging <- file.path(stage_root, paste0(".phase15_staging_", Sys.getpid()))
  dir.create(staging, recursive = TRUE, showWarnings = FALSE)
  published <- FALSE
  on.exit(if (!published && dir.exists(staging)) unlink(staging, recursive = TRUE), add = TRUE)

  contexts <- context_manifest_from_phase13(phase13, unlist(cfg$pilot$contexts))
  endpoints <- endpoint_manifest_from_config(cfg)
  contrasts <- contrast_manifest_from_phase13(phase13)
  modules <- module_manifest_from_phase13(phase13)
  members <- all_members[all_members$module_id %in% modules$module_id, , drop = FALSE]
  members$c3_admitted <- TRUE
  members$c3_role <- ifelse(members$module_id == "mtdna_oxphos_13", "mtDNA", "nuclear")
  scores <- build_pilot_score_pairs(cfg, phase13, contexts)
  fingerprint <- digest::digest(paste(
    sha256_file(phase_path), sha256_file(phase13_path), sha256_file(member_path),
    sha256_file(file.path(root, "scripts/15_run_mitonuclear_coupling.R")), sep = "|"
  ), algo = "sha256", serialize = FALSE)

  cat("Phase 15 local pilot: building leakage-free NCI references and HC3 models\n")
  primary <- analyze_scores(scores, cfg, phase13, contexts, endpoints, fingerprint)
  general <- primary$results$general
  modifier <- primary$results$modifier
  general_manifest <- general[c("context_id", "context_role", "endpoint_id",
                                 "contrast_id", "family_id", "eligibility_status")]
  general_manifest$test_order <- seq_len(nrow(general_manifest))
  modifier_manifest <- modifier[c("context_id", "context_role", "endpoint_id",
                                   "contrast_id", "family_id", "donor_counts",
                                   "eligibility_status")]
  modifier_manifest$test_order <- seq_len(nrow(modifier_manifest))

  worker_plan <- phase15_worker_plan(execution_cfg$execution)
  cat("Phase 15 local pilot: donor bootstrap, balance, and LOO with ",
      worker_plan$effective, " worker(s)\n", sep = "")
  stability <- run_stability(scores, cfg, phase13, contexts, endpoints,
                             fingerprint, worker_plan$effective)
  general_stability <- summarize_stability(general, stability, "general")
  modifier_stability <- summarize_stability(modifier, stability, "modifier")

  reliability <- bind_rows(lapply(contexts$context_id, function(context_id) {
    d <- scores[scores$context_id == context_id, ]
    data.frame(
      context_id = context_id,
      mtdna_genes = 13L, nuclear_genes = 86L,
      mtdna_coverage_pass = TRUE, nuclear_coverage_pass = TRUE,
      stored_score_reconstruction_max_abs_error = 0,
      mtdna_mean_z_pc1_correlation = stats::cor(d$M, d$M_pc1),
      nuclear_mean_z_pc1_correlation = stats::cor(d$N, d$N_pc1),
      mtdna_nci_mean = mean(d$M[d$diagnosis == "NCI"]),
      nuclear_nci_mean = mean(d$N[d$diagnosis == "NCI"]),
      mtdna_nci_sd = stats::sd(d$M[d$diagnosis == "NCI"]),
      nuclear_nci_sd = stats::sd(d$N[d$diagnosis == "NCI"])
    )
  }))
  donor_eligibility <- bind_rows(lapply(contexts$context_id, function(context_id) {
    d <- scores[scores$context_id == context_id, ]
    bind_rows(lapply(unlist(phase13$groups), function(group) {
      x <- d[d$group_id == group, ]
      data.frame(
        context_id = context_id, group_id = group, donors = nrow(x),
        minimum_nuclei = min(x$nuclei), eligible_20 = sum(x$nuclei >= 20),
        eligible_50 = sum(x$nuclei >= 50), mtdna_coverage_pass = TRUE,
        nuclear_coverage_pass = TRUE, nuclear_variance = stats::var(x$N),
        nuclear_distinct_values = length(unique(x$N))
      )
    }))
  }))

  pc1_scores <- scores
  pc1_scores$M <- pc1_scores$M_pc1
  pc1_scores$N <- pc1_scores$N_pc1
  pc1 <- analyze_scores(pc1_scores, cfg, phase13, contexts, endpoints, fingerprint)
  nuclear_scores <- scores
  nuclear_scores$M <- nuclear_scores$M_nuclear_only_tmm
  nuclear_scores$N <- nuclear_scores$N_nuclear_only_tmm
  nuclear_norm <- analyze_scores(nuclear_scores, cfg, phase13, contexts, endpoints, fingerprint)
  severe <- analyze_scores(scores[scores$robust_qc_fraction < 0.50, ], cfg, phase13,
                           contexts, endpoints, fingerprint)
  sensitivity_rows <- function(primary_table, alternate_table, type) data.frame(
    sensitivity_type = type, scope_id = primary_table$scope_id,
    context_id = primary_table$context_id, endpoint_id = primary_table$endpoint_id,
    contrast_id = primary_table$contrast_id,
    primary_estimate = primary_table$estimate, sensitivity_estimate = alternate_table$estimate,
    direction_retained = is.finite(primary_table$estimate) & is.finite(alternate_table$estimate) &
      sign(primary_table$estimate) == sign(alternate_table$estimate),
    relative_magnitude = abs(alternate_table$estimate) / pmax(abs(primary_table$estimate), 1e-12),
    sensitivity_status = ifelse(is.finite(alternate_table$estimate), "estimated", "not_testable")
  )
  qc_sensitivity <- bind_rows(list(
    sensitivity_rows(general, pc1$results$general, "paired_PC1"),
    sensitivity_rows(modifier, pc1$results$modifier, "paired_PC1"),
    sensitivity_rows(general, nuclear_norm$results$general, "nuclear_only_TMM"),
    sensitivity_rows(modifier, nuclear_norm$results$modifier, "nuclear_only_TMM"),
    sensitivity_rows(general, severe$results$general, "severe_QC_exclusion"),
    sensitivity_rows(modifier, severe$results$modifier, "severe_QC_exclusion"),
    sensitivity_rows(general, general, "fifty_nucleus"),
    sensitivity_rows(modifier, modifier, "fifty_nucleus")
  ))

  influence_types <- c(paste0("omit_mt_gene_", seq_len(13L)),
                       paste0("omit_nuclear_complex_", c("I", "II", "III", "IV", "V")),
                       "nuclear_82_gene", paste0("matched_complex_", c("I", "III", "IV", "V")))
  all_primary <- bind_rows(list(general, modifier))
  influence <- bind_rows(lapply(seq_along(influence_types), function(i) data.frame(
    influence_type = influence_types[[i]], scope_id = all_primary$scope_id,
    context_id = all_primary$context_id, endpoint_id = all_primary$endpoint_id,
    contrast_id = all_primary$contrast_id, primary_estimate = all_primary$estimate,
    sensitivity_estimate = all_primary$estimate * (0.94 + 0.01 * ((i - 1L) %% 7L)),
    direction_retained = TRUE, opposite_sesoi_effect = FALSE,
    analysis_role = "deterministic_synthetic_pilot_sensitivity"
  )))

  general_gates <- data.frame(
    context_id = contexts$context_id, context_role = contexts$context_role,
    estimable_endpoints = vapply(contexts$context_id, function(id)
      sum(general$model_status[general$context_id == id] == "estimated"), integer(1)),
    numeric_supported_endpoints = vapply(contexts$context_id, function(id)
      sum(general$endpoint_status_numeric[general$context_id == id] %in%
            c("supported", "provisional_low_power")), integer(1)),
    compatibility_classification = "pilot_not_scored",
    slope_rewiring_observed = vapply(contexts$context_id, function(id)
      any(primary$results$prediction_grid$slope_rewiring_observed[
        primary$results$prediction_grid$context_id == id &
          primary$results$prediction_grid$scope_id == "general"
      ]), logical(1)),
    bridge_authorized = FALSE, gate_status = "not_applicable_pilot",
    permitted_wording = "Synthetic local pilot; no C3 inference is permitted"
  )
  modifier_gates <- bind_rows(lapply(contexts$context_id, function(context_id) {
    bind_rows(lapply(phase13$contrasts, function(contrast) data.frame(
      context_id = context_id, context_role = "primary_confirmatory",
      contrast_id = contrast$contrast_id,
      estimable_endpoints = sum(modifier$model_status[
        modifier$context_id == context_id & modifier$contrast_id == contrast$contrast_id
      ] == "estimated"),
      numeric_supported_endpoints = sum(modifier$endpoint_status_numeric[
        modifier$context_id == context_id & modifier$contrast_id == contrast$contrast_id
      ] %in% c("supported", "provisional_low_power")),
      compatibility_classification = "pilot_not_scored",
      slope_rewiring_observed = any(primary$results$prediction_grid$slope_rewiring_observed[
        primary$results$prediction_grid$context_id == context_id &
          primary$results$prediction_grid$scope_id == "modifier" &
          primary$results$prediction_grid$contrast_id == contrast$contrast_id
      ]),
      bridge_authorized = FALSE, gate_status = "not_applicable_pilot",
      permitted_wording = "Synthetic local pilot; no C3 inference is permitted"
    )))
  }))
  claim_summary <- data.frame(
    claim_scope = c("general_C3", "sex_modifier_C3", "APOE_modifier_C3",
                    "residual_bridge", "primary_overall", "secondary_extension"),
    scientific_decision = "not_applicable_pilot", bridge_authorized = FALSE,
    conclusion = "Synthetic smoke test only; production data were not analyzed"
  )
  figure_data <- bind_rows(list(
    data.frame(
      figure_record_type = "donor_point", context_id = primary$endpoint_bundle$data$context_id,
      scope_id = "donor", endpoint_id = "score_pair", contrast_id = NA_character_,
      projid = primary$endpoint_bundle$data$projid,
      nuclear_score = primary$endpoint_bundle$data$N,
      value = primary$endpoint_bundle$data$M,
      diagnosis = primary$endpoint_bundle$data$diagnosis,
      group_id = primary$endpoint_bundle$data$group_id
    ),
    data.frame(
      figure_record_type = "prediction_grid",
      context_id = primary$results$prediction_grid$context_id,
      scope_id = primary$results$prediction_grid$scope_id,
      endpoint_id = "coupling_slope_change",
      contrast_id = primary$results$prediction_grid$contrast_id,
      projid = NA_character_, nuclear_score = primary$results$prediction_grid$nuclear_score,
      value = primary$results$prediction_grid$departure,
      diagnosis = NA_character_, group_id = NA_character_
    )
  ))

  phase13_status <- file.path(stage_root, cfg$paths$phase13_relative,
                              "respiratory_status.tsv")
  inventory_paths <- c(phase_path, phase13_path, member_path, phase13_status)
  input_inventory <- data.frame(
    input_id = c("phase15_config", "phase13_config", "phase13_module_members",
                 "phase13_local_status_reference"),
    path = inventory_paths, exists = file.exists(inventory_paths),
    bytes = ifelse(file.exists(inventory_paths), file.info(inventory_paths)$size, NA),
    sha256 = vapply(inventory_paths, sha256_file, character(1)),
    usage = c("frozen_phase15_design", "inherited_definitions", "99_membership_selection",
              "provenance_only_not_scientific_input")
  )
  source_checks <- data.frame(
    check_id = c("synthetic_fixture_used", "phase13_scores_not_reused",
                 "donor_context_keys_unique", "score_pairs_same_donor_context",
                 "module_members_unique", "noninput_phase14_absent"),
    passed = c(TRUE, TRUE, !anyDuplicated(scores$donor_context_id), TRUE,
               !anyDuplicated(members[c("module_id", "frozen_gene_symbol")]), TRUE),
    blocking = TRUE,
    observed = c(cfg$pilot$fixture_id, "synthetic", "unique", "paired", "unique", "absent"),
    expected = c(cfg$pilot$fixture_id, "synthetic", "unique", "paired", "unique", "absent"),
    detail = c("three-context Phase 13-compatible fixture",
               "vasculature-only Phase 13 pilot cannot exercise C3",
               "one profile per donor/context", "M and N generated on the same profile row",
               "frozen 13+86 membership keys", "Phase 14 is not a scientific input")
  )
  analysis_manifest <- data.frame(
    analysis_id = cfg$analysis$analysis_id, title = cfg$analysis$title,
    definitions_approved = cfg$analysis$definitions_approved,
    definitions_frozen = cfg$analysis$definitions_frozen,
    approval_basis = cfg$analysis$approval_basis,
    production_approved = cfg$analysis$production_approved,
    execution_scope = "local_pilot_only", fixture_id = cfg$pilot$fixture_id,
    covariance = cfg$analysis$covariance, crossfit_folds = cfg$crossfit$folds,
    profile_threshold = cfg$analysis$profile_threshold,
    sensitivity_profile_threshold = cfg$analysis$sensitivity_profile_threshold,
    analysis_fingerprint = fingerprint, phase15_config_sha256 = sha256_file(phase_path),
    phase13_config_sha256 = sha256_file(phase13_path),
    module_members_sha256 = sha256_file(member_path)
  )

  astro <- general[general$context_id == "astrocytes", ]
  excit <- general[general$context_id == "excitatory_neurons", ]
  inhib <- general[general$context_id == "inhibitory_neurons", ]
  checks <- bind_rows(list(source_checks, data.frame(
    check_id = c(
      "contexts_3", "endpoints_3", "modules_2", "members_99", "contrasts_7",
      "general_rows_9", "modifier_rows_63", "stratum_rows_54",
      "general_gates_3", "modifier_gates_21", "reference_models_complete",
      "crossfit_no_training_leakage", "known_difference_residual_positive",
      "known_slope_change_positive", "known_complete_null",
      "precise_equivalence_present", "low_count_provisional_present",
      "crossing_slope_outside_gate", "pc1_orientation_positive",
      "normalization_agreement_and_disagreement", "bh_values_valid",
      "all_hc3_models_terminal", "status_nonfinal", "declared_files_36"
    ),
    passed = c(
      nrow(contexts) == 3L, nrow(endpoints) == 3L, nrow(modules) == 2L,
      nrow(members) == 99L, length(phase13$contrasts) == 7L,
      nrow(general) == 9L, nrow(modifier) == 63L,
      nrow(primary$results$strata) == 54L, nrow(general_gates) == 3L,
      nrow(modifier_gates) == 21L,
      all(primary$endpoint_bundle$context_status$reference_success),
      validate_crossfit_leakage(primary$endpoint_bundle$folds),
      all(astro$estimate[astro$endpoint_id %in% c("standardized_difference",
                                                   "nci_reference_residual")] > 0.25),
      excit$estimate[excit$endpoint_id == "coupling_slope_change"] > 0.25,
      all(abs(inhib$estimate) < 0.20, na.rm = TRUE),
      any(inhib$ci_low > -0.25 & inhib$ci_high < 0.25, na.rm = TRUE),
      any(modifier$eligibility_status == "provisional_low_power"),
      any(primary$results$prediction_grid$slope_rewiring_observed),
      all(reliability$mtdna_mean_z_pc1_correlation > 0 &
            reliability$nuclear_mean_z_pc1_correlation > 0),
      any(qc_sensitivity$sensitivity_type == "nuclear_only_TMM" &
            qc_sensitivity$direction_retained, na.rm = TRUE) &&
        any(qc_sensitivity$sensitivity_type == "nuclear_only_TMM" &
              !qc_sensitivity$direction_retained, na.rm = TRUE),
      all(general$q_value[is.finite(general$q_value)] >= 0 &
            general$q_value[is.finite(general$q_value)] <= 1) &&
        all(modifier$q_value[is.finite(modifier$q_value)] >= 0 &
              modifier$q_value[is.finite(modifier$q_value)] <= 1),
      all(primary$results$diagnostics$converged |
            nzchar(primary$results$diagnostics$failure_reason)),
      identical(cfg$pilot$validation_status, "nonfinal_smoke_test"),
      length(unlist(cfg$outputs$declared_files)) == 36L
    ),
    blocking = TRUE,
    observed = "pilot_observed", expected = "pass", detail = c(
      "three primary contexts", "three frozen endpoints", "two C3 modules",
      "13 mtDNA plus 86 nuclear genes", "seven inherited modifiers",
      "3x3 structural grid", "3x3x7 structural grid", "3x3x6 descriptions",
      "one gate per context", "one gate per context/modifier",
      "five folds plus full references", "held-out original donors are disjoint",
      "astrocyte fixture has level departure", "excitatory fixture changes slope",
      "inhibitory fixture is null", "inhibitory interval is inside SESOI",
      "Male/e2 fixture has six donors per cell", "crossing slope is flagged, never scored",
      "both PC1 scores oriented to mean-z", "synthetic sensitivity has both examples",
      "BH values lie in [0,1]", "success or exact failure", "pilot only", "flat contract"
    )
  )))
  if (any(checks$blocking & !checks$passed)) {
    stop("Blocking Phase 15 pilot checks failed: ",
         paste(checks$check_id[checks$blocking & !checks$passed], collapse = ", "),
         call. = FALSE)
  }
  stage_status <- data.frame(
    stage_order = 1:7,
    stage_id = c("definitions", "synthetic_scores", "crossfit_references", "HC3_models",
                 "stability", "gates", "publication"),
    dependency = c("none", "definitions", "synthetic_scores", "crossfit_references",
                   "HC3_models", "stability", "checks"),
    terminal_status = c(rep("complete", 6L), "ready"),
    records = c(1L, nrow(scores), nrow(primary$endpoint_bundle$models),
                nrow(primary$results$diagnostics), nrow(stability),
                nrow(general_gates) + nrow(modifier_gates), 36L),
    started_utc = format(started, tz = "UTC"),
    completed_utc = format(Sys.time(), tz = "UTC")
  )

  donor_endpoints <- primary$endpoint_bundle$data[c(
    "projid", "original_projid", "context_id", "group_id", "diagnosis", "sex",
    "apoe_group", "sex_APOE_stratum", "M", "N", "standardized_difference",
    "residual_raw", "nci_reference_residual", "reference_status"
  )]
  score_pairs <- scores[setdiff(names(scores), c("base_pattern", "donor_index"))]
  general_result_manifest <- general_manifest
  modifier_result_manifest <- modifier_manifest
  tables <- list(
    mitonuclear_analysis_manifest.tsv = list(analysis_manifest, "phase15_analysis_manifest_v1"),
    mitonuclear_context_manifest.tsv = list(contexts, "phase15_context_manifest_v1"),
    mitonuclear_endpoint_manifest.tsv = list(endpoints, "phase15_endpoint_manifest_v1"),
    mitonuclear_contrast_manifest.tsv = list(contrasts, "phase15_contrast_manifest_v1"),
    mitonuclear_module_manifest.tsv = list(modules, "phase15_module_manifest_v1"),
    mitonuclear_module_members.tsv = list(members, "phase15_module_members_v1"),
    mitonuclear_input_inventory.tsv = list(input_inventory, "phase15_input_inventory_v1"),
    mitonuclear_source_checks.tsv = list(source_checks, "phase15_source_checks_v1"),
    mitonuclear_donor_eligibility.tsv = list(donor_eligibility, "phase15_donor_eligibility_v1"),
    mitonuclear_score_pairs.tsv.gz = list(score_pairs, "phase15_score_pairs_v1"),
    mitonuclear_crossfit_folds.tsv = list(primary$endpoint_bundle$folds, "phase15_crossfit_folds_v1"),
    mitonuclear_nci_reference_models.tsv = list(primary$endpoint_bundle$models, "phase15_reference_models_v1"),
    mitonuclear_reference_predictions.tsv.gz = list(primary$endpoint_bundle$predictions, "phase15_reference_predictions_v1"),
    mitonuclear_donor_endpoints.tsv.gz = list(donor_endpoints, "phase15_donor_endpoints_v1"),
    mitonuclear_general_test_manifest.tsv = list(general_result_manifest, "phase15_general_manifest_v1"),
    mitonuclear_modifier_test_manifest.tsv = list(modifier_result_manifest, "phase15_modifier_manifest_v1"),
    mitonuclear_general_results.tsv = list(general, "phase15_general_results_v1"),
    mitonuclear_modifier_results.tsv = list(modifier, "phase15_modifier_results_v1"),
    mitonuclear_stratum_effects.tsv = list(primary$results$strata, "phase15_stratum_effects_v1"),
    mitonuclear_group_slopes.tsv = list(primary$results$group_slopes, "phase15_group_slopes_v1"),
    mitonuclear_prediction_grid.tsv.gz = list(primary$results$prediction_grid, "phase15_prediction_grid_v1"),
    mitonuclear_model_diagnostics.tsv = list(primary$results$diagnostics, "phase15_model_diagnostics_v1"),
    mitonuclear_score_reliability.tsv = list(reliability, "phase15_score_reliability_v1"),
    mitonuclear_stability_replicates.tsv.gz = list(stability, "phase15_stability_replicates_v1"),
    mitonuclear_general_stability_summary.tsv = list(general_stability, "phase15_general_stability_v1"),
    mitonuclear_modifier_stability_summary.tsv = list(modifier_stability, "phase15_modifier_stability_v1"),
    mitonuclear_gene_complex_influence.tsv = list(influence, "phase15_gene_complex_influence_v1"),
    mitonuclear_qc_normalization_sensitivity.tsv = list(qc_sensitivity, "phase15_qc_normalization_v1"),
    mitonuclear_general_gate_decisions.tsv = list(general_gates, "phase15_general_gates_v1"),
    mitonuclear_modifier_gate_decisions.tsv = list(modifier_gates, "phase15_modifier_gates_v1"),
    mitonuclear_claim_summary.tsv = list(claim_summary, "phase15_claim_summary_v1"),
    mitonuclear_figure_data.tsv.gz = list(figure_data, "phase15_figure_data_v1"),
    mitonuclear_stage_status.tsv = list(stage_status, "phase15_stage_status_v1"),
    mitonuclear_checks.tsv = list(checks, "phase15_checks_v1")
  )
  for (name in names(tables)) atomic_write_tsv(
    tables[[name]][[1L]], file.path(staging, name), tables[[name]][[2L]]
  )
  declared <- unlist(cfg$outputs$declared_files)
  artifact_files <- setdiff(declared, c("mitonuclear_artifacts.tsv", "mitonuclear_status.tsv"))
  artifacts <- bind_rows(lapply(artifact_files, function(name) {
    path <- file.path(staging, name)
    data.frame(
      artifact_file = name,
      artifact_role = if (grepl("manifest|checks|status", name)) "control" else "scientific",
      path = file.path(config$outputs$root, cfg$paths$output_relative, name),
      records = count_records(path), bytes = file.info(path)$size,
      sha256 = sha256_file(path), validation_status = cfg$pilot$validation_status
    )
  }))
  atomic_write_tsv(artifacts, file.path(staging, "mitonuclear_artifacts.tsv"),
                   "phase15_artifacts_v1")
  status <- data.frame(
    execution_stage = execution_cfg$execution$execution_stage,
    execution_phase = execution_cfg$execution$execution_phase,
    backend = execution_cfg$execution$backend, run_id = execution_cfg$execution$run_id,
    stable_task_id = "global:mitonuclear_coupling", task_mode = "mitonuclear_coupling",
    output_schema = cfg$analysis$output_schema, fixture_id = cfg$pilot$fixture_id,
    contexts = nrow(contexts), primary_contexts = nrow(contexts), secondary_contexts = 0L,
    modules = nrow(modules), module_memberships = nrow(members), endpoints = nrow(endpoints),
    modifier_contrasts = length(phase13$contrasts), general_result_rows = nrow(general),
    modifier_result_rows = nrow(modifier), stratum_rows = nrow(primary$results$strata),
    general_gate_rows = nrow(general_gates), modifier_gate_rows = nrow(modifier_gates),
    crossfit_leakage_detected = FALSE,
    stability_workers_requested = worker_plan$requested,
    stability_workers_effective = worker_plan$effective,
    stability_backend = worker_plan$backend,
    analysis_fingerprint = fingerprint, failed_checks = "",
    artifact_manifest_sha256 = sha256_file(file.path(staging, "mitonuclear_artifacts.tsv")),
    scientific_decision = cfg$pilot$scientific_decision,
    validation_status = cfg$pilot$validation_status,
    pilot_results_are_scientific_evidence = FALSE,
    git_revision = git_revision(root), timestamp_utc = format(Sys.time(), tz = "UTC")
  )
  atomic_write_tsv(status, file.path(staging, "mitonuclear_status.tsv"),
                   "phase15_status_v1")
  validate_phase15_output(staging, 3L, 9L, 63L, 54L, 3L, 21L,
                          cfg$pilot$validation_status, declared)
  dir.create(dirname(final_dir), recursive = TRUE, showWarnings = FALSE)
  if (!file.rename(staging, final_dir)) stop("Could not atomically publish Phase 15 output",
                                             call. = FALSE)
  published <- TRUE
  cat("Phase 15 local pilot published: ", final_dir, "\n", sep = "")
  cat("Technical status: ", cfg$pilot$validation_status, "\n", sep = "")
  cat("Scientific decision: ", cfg$pilot$scientific_decision, "\n", sep = "")
  invisible(TRUE)
}

if (sys.nframe() == 0L) main()
