#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_phase14_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL,
              task_mode = "modifier_heterogeneity")
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/14_run_modifier_heterogeneity.R ",
          "--config FILE --execution-config FILE ",
          "[--task-mode modifier_heterogeneity]\n", sep = "")
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
  if (!identical(out$task_mode, "modifier_heterogeneity")) {
    stop("--task-mode must be modifier_heterogeneity", call. = FALSE)
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
  write.table(x, connection, sep = "\t", quote = FALSE,
              row.names = FALSE, na = "NA")
  close(connection)
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

count_records <- function(path) {
  if (!file.exists(path) || grepl("heterogeneity_artifacts|heterogeneity_status", path)) {
    return(NA_integer_)
  }
  nrow(data.table::fread(path, data.table = FALSE, showProgress = FALSE))
}

seed_for <- function(cfg, id) {
  base <- as.numeric(cfg$randomization$base_seed)
  offset <- abs(as.numeric(digest::digest2int(as.character(id))))
  as.integer((base + offset) %% (.Machine$integer.max - 1)) + 1L
}

positive_core_count <- function(value) {
  value <- suppressWarnings(as.integer(value))
  if (length(value) != 1L || is.na(value) || value < 1L) NA_integer_ else value
}

phase14_worker_plan <- function(execution, os_type = .Platform$OS.type) {
  requested <- positive_core_count(
    execution$phase14_stability_workers %||% execution$max_total_cores
  )
  maximum <- positive_core_count(execution$max_total_cores)
  detected <- positive_core_count(parallel::detectCores(logical = TRUE))
  scheduler <- suppressWarnings(as.integer(c(
    Sys.getenv("LSB_DJOB_NUMPROC", unset = NA_character_),
    Sys.getenv("SLURM_CPUS_PER_TASK", unset = NA_character_),
    Sys.getenv("NSLOTS", unset = NA_character_)
  )))
  scheduler <- scheduler[is.finite(scheduler) & scheduler > 0L]
  limits <- c(requested, maximum, detected, if (length(scheduler)) min(scheduler) else NA)
  workers <- min(limits[is.finite(limits)])
  if (!identical(os_type, "unix")) workers <- 1L
  list(requested = requested, effective = as.integer(workers),
       backend = if (workers > 1L) "fork" else "sequential")
}

ordered_lapply <- function(x, fun, workers) {
  if (workers > 1L) parallel::mclapply(x, fun, mc.cores = workers,
                                       mc.preschedule = TRUE) else lapply(x, fun)
}

context_manifest_from_phase13 <- function(phase13, ids) {
  entries <- Filter(function(x) as.character(x$context_id) %in% ids, phase13$contexts)
  entries <- entries[match(ids, vapply(entries, function(x) x$context_id, character(1)))]
  bind_rows(lapply(seq_along(entries), function(i) data.frame(
    context_order = i,
    inherited_context_order = as.integer(entries[[i]]$context_order),
    context_id = as.character(entries[[i]]$context_id),
    context_label = as.character(entries[[i]]$label),
    source_rds_ids = paste(unlist(entries[[i]]$source_rds_ids), collapse = "|"),
    pilot_fixture_context = TRUE
  )))
}

pair_manifest <- function(context_manifest) {
  pairs <- utils::combn(context_manifest$context_id, 2L, simplify = FALSE)
  bind_rows(lapply(seq_along(pairs), function(i) data.frame(
    pair_order = i, pair_id = paste(pairs[[i]], collapse = "__vs__"),
    context_1 = pairs[[i]][[1L]], context_2 = pairs[[i]][[2L]],
    signed_definition = "modifier(context_1)-modifier(context_2)"
  )))
}

contrast_manifest_from_phase13 <- function(phase13) {
  bind_rows(lapply(phase13$contrasts, function(x) {
    coefficients <- unlist(x$coefficients)
    data.frame(
      contrast_order = as.integer(x$contrast_order),
      contrast_id = as.character(x$contrast_id), modifier = as.character(x$modifier),
      required_groups = paste(unlist(x$required_groups), collapse = "|"),
      coefficients = paste(paste(names(coefficients), coefficients, sep = "="),
                           collapse = ";")
    )
  }))
}

module_manifest_from_phase13 <- function(phase13) {
  bind_rows(lapply(phase13$modules, function(x) data.frame(
    module_order = as.integer(x$module_order), module_id = as.character(x$module_id),
    module_label = as.character(x$label), module_role = as.character(x$role),
    frozen_genes = as.integer(x$reference_genes),
    minimum_fraction = as.numeric(x$minimum_fraction),
    minimum_genes = as.integer(x$minimum_genes)
  )))
}

strata_from_phase13 <- function(phase13) {
  lapply(phase13$strata, function(x) list(
    stratum_order = as.integer(x$stratum_order), stratum_id = as.character(x$stratum_id),
    nci_group = as.character(x$nci_group), ad_group = as.character(x$ad_group)
  ))
}

group_parts <- function(group_id) {
  parts <- strsplit(group_id, "__", fixed = TRUE)[[1L]]
  list(diagnosis = parts[[1L]], sex = parts[[2L]], apoe_group = parts[[3L]])
}

pilot_effect <- function(module_id, group_id, context_id) {
  parts <- group_parts(group_id)
  if (parts$diagnosis == "NCI") return(0)
  context_index <- match(context_id, c("astrocytes", "excitatory_neurons", "vasculature"))
  if (module_id == "mtdna_oxphos_13") {
    if (parts$sex == "Female" && parts$apoe_group == "e33") {
      return(c(1.60, 0.10, -0.55)[[context_index]])
    }
    if (parts$sex == "Male" && parts$apoe_group == "e33") return(0)
    return(0.15)
  }
  if (module_id == "nuclear_oxphos_structural_86") {
    return(c(e2 = 0.20, e33 = 0.10, e4 = 0.30)[[parts$apoe_group]] +
             if (parts$sex == "Female") 0.05 else 0)
  }
  if (module_id == "mitochondrial_translation_155") {
    if (parts$sex == "Female" && parts$apoe_group == "e4") {
      return(c(0.85, -0.65, 0.20)[[context_index]])
    }
    if (parts$sex == "Male" && parts$apoe_group == "e4") return(0.05)
    return(0)
  }
  0.10
}

build_pilot_profiles <- function(phase_cfg, phase13, context_manifest,
                                 module_manifest) {
  groups <- unlist(phase13$groups, use.names = FALSE)
  n <- as.integer(phase_cfg$pilot$donors_per_group)
  donor_rows <- bind_rows(lapply(seq_along(groups), function(group_index) {
    parts <- group_parts(groups[[group_index]])
    data.frame(
      projid = sprintf("P14_G%02d_D%02d", group_index, seq_len(n)),
      group_id = groups[[group_index]], diagnosis = parts$diagnosis,
      sex = parts$sex, apoe_group = parts$apoe_group,
      age_death_scaled = scale(seq_len(n), center = TRUE, scale = TRUE)[, 1L] +
        (group_index %% 3L) / 20,
      pmi_scaled = scale(rep(c(-1.0, 0.4, 0.8, -0.6, 1.1, -0.2, 0.1, -0.6),
                              length.out = n), center = TRUE, scale = TRUE)[, 1L] +
        (group_index %% 2L) / 20,
      study = rep(c("MAP", "ROS"), length.out = n),
      aggregate_percent_mt = 2 + (seq_len(n) %% 4L) / 2,
      robust_qc_fraction = 0.02 + (seq_len(n) %% 5L) / 100,
      stringsAsFactors = FALSE
    )
  }))
  contexts <- context_manifest$context_id
  profile_rows <- lapply(seq_len(nrow(donor_rows)), function(i) {
    donor <- donor_rows[i, , drop = FALSE]
    donor_contexts <- contexts
    if (grepl(paste0(phase_cfg$pilot$low_overlap_group, "$"), donor$group_id)) {
      donor_number <- as.integer(sub(".*_D", "", donor$projid))
      donor_contexts <- c(
        if (donor_number %in% 1:5) contexts[[1L]],
        if (donor_number %in% 4:8) contexts[[2L]],
        if (donor_number %in% 2:6) contexts[[3L]]
      )
    }
    bind_rows(lapply(donor_contexts, function(context_id) {
      out <- donor
      out$context <- context_id
      out$nuclei <- 55L + ((i + match(context_id, contexts)) %% 31L)
      out$donor_context_id <- paste(out$projid, context_id, sep = "::")
      out
    }))
  })
  profiles <- bind_rows(profile_rows)
  latent_rows <- list()
  for (module_index in seq_len(nrow(module_manifest))) {
    module_id <- module_manifest$module_id[[module_index]]
    set.seed(seed_for(phase_cfg, paste0("pilot-latent::", module_id)))
    donor_random <- setNames(stats::rnorm(nrow(donor_rows)), donor_rows$projid)
    context_noise_sd <- if (module_index == 2L) 0.015 else 0.10
    set.seed(seed_for(phase_cfg, paste0("pilot-residual::", module_id)))
    noise <- stats::rnorm(nrow(profiles), sd = context_noise_sd)
    values <- donor_random[profiles$projid] +
      mapply(pilot_effect, module_id, profiles$group_id, profiles$context) +
      0.08 * profiles$age_death_scaled - 0.04 * profiles$pmi_scaled +
      ifelse(profiles$study == "ROS", 0.08, 0) + noise
    out <- profiles
    out$module_id <- module_id
    out$latent_score <- as.numeric(values)
    latent_rows[[module_index]] <- out
  }
  bind_rows(latent_rows)
}

build_common_scores <- function(profiles, members, phase_cfg, module_manifest,
                                context_manifest) {
  member_rows <- members
  member_rows$common_admitted <- TRUE
  member_rows$all_context_expression_pass <- TRUE
  member_rows$all_context_finite_nonzero_nci_sd <- TRUE
  member_rows$exclusion_reason <- ""
  failing_module <- "mib_micos_inner_membrane_19"
  failing <- which(member_rows$module_id == failing_module)
  if (length(failing) > 10L) {
    excluded <- failing[seq.int(11L, length(failing))]
    member_rows$common_admitted[excluded] <- FALSE
    member_rows$all_context_expression_pass[excluded] <- FALSE
    member_rows$exclusion_reason[excluded] <- "pilot_expression_filter_failure_in_vasculature"
  }
  common_counts <- aggregate(
    common_admitted ~ module_id, member_rows, sum
  )
  module_manifest <- merge(module_manifest, common_counts, by = "module_id", sort = FALSE)
  module_manifest <- module_manifest[order(module_manifest$module_order), ]
  module_manifest$common_fraction <- module_manifest$common_admitted /
    module_manifest$frozen_genes
  module_manifest$common_coverage_pass <-
    module_manifest$common_fraction >= module_manifest$minimum_fraction &
    module_manifest$common_admitted >= module_manifest$minimum_genes
  mt <- module_manifest$module_id == "mtdna_oxphos_13"
  module_manifest$common_coverage_pass[mt] <-
    module_manifest$common_coverage_pass[mt] & module_manifest$common_admitted[mt] >= 10L

  score_rows <- list()
  reference_rows <- list()
  loading_rows <- list()
  score_index <- 0L
  reference_index <- 0L
  loading_index <- 0L
  for (module_id in module_manifest$module_id) {
    module_profiles <- profiles[profiles$module_id == module_id, , drop = FALSE]
    genes <- member_rows$assay_feature_identifier[
      member_rows$module_id == module_id & member_rows$common_admitted
    ]
    module_index <- match(module_id, module_manifest$module_id)
    gene_noise_sd <- if (module_index == 2L) 0.015 else 0.12
    for (context_id in context_manifest$context_id) {
      d <- module_profiles[module_profiles$context == context_id, , drop = FALSE]
      expression <- vapply(seq_along(genes), function(gene_index) {
        deterministic_noise <- gene_noise_sd * sin(
          seq_len(nrow(d)) * (gene_index + 1L) * 0.37 + module_index
        )
        d$latent_score + gene_index / (100 * length(genes)) + deterministic_noise
      }, numeric(nrow(d)))
      if (is.null(dim(expression))) expression <- matrix(expression, ncol = 1L)
      colnames(expression) <- genes
      nci <- d$diagnosis == "NCI"
      mu <- colMeans(expression[nci, , drop = FALSE])
      sd_value <- apply(expression[nci, , drop = FALSE], 2L, stats::sd)
      if (any(!is.finite(sd_value) | sd_value <= 0)) {
        stop("Pilot fixture generated invalid NCI gene variance", call. = FALSE)
      }
      z <- sweep(sweep(expression, 2L, mu, "-"), 2L, sd_value, "/")
      raw_mean_z <- rowMeans(z)
      raw_mu <- mean(raw_mean_z[nci])
      raw_sd <- stats::sd(raw_mean_z[nci])
      common_score <- (raw_mean_z - raw_mu) / raw_sd
      pc <- stats::prcomp(z[nci, , drop = FALSE], center = FALSE,
                         scale. = FALSE, rank. = 1L)
      pc_raw <- as.numeric(z %*% pc$rotation[, 1L])
      pc_score <- (pc_raw - mean(pc_raw[nci])) / stats::sd(pc_raw[nci])
      orientation <- if (stats::cor(pc_score, common_score) < 0) -1 else 1
      pc_score <- pc_score * orientation
      loadings <- pc$rotation[, 1L] * orientation
      correlation <- stats::cor(pc_score, common_score)
      score_index <- score_index + 1L
      scores <- d
      scores$raw_common_mean_z <- raw_mean_z
      scores$common_score <- common_score
      scores$pc1_score <- pc_score
      scores$phase13_original_score <- common_score +
        0.025 * cos(seq_len(nrow(scores)) + module_index)
      scores$common_gene_count <- length(genes)
      scores$pc1_mean_z_correlation <- correlation
      score_rows[[score_index]] <- scores
      reference_index <- reference_index + 1L
      reference_rows[[reference_index]] <- data.frame(
        parameter_type = "module", context = context_id, module_id = module_id,
        gene_id = NA_character_, nci_donors = sum(nci), mean = raw_mu, sd = raw_sd
      )
      reference_index <- reference_index + 1L
      reference_rows[[reference_index]] <- data.frame(
        parameter_type = "gene", context = context_id, module_id = module_id,
        gene_id = genes, nci_donors = sum(nci), mean = as.numeric(mu),
        sd = as.numeric(sd_value)
      )
      loading_index <- loading_index + 1L
      loading_rows[[loading_index]] <- data.frame(
        context = context_id, module_id = module_id, gene_id = genes,
        pc1_loading = as.numeric(loadings), orientation = orientation,
        correlation_with_common_mean_z = correlation
      )
    }
  }
  list(scores = bind_rows(score_rows), references = bind_rows(reference_rows),
       loadings = bind_rows(loading_rows), members = member_rows,
       modules = module_manifest)
}

prepare_model_data <- function(scores, contexts, groups) {
  scores$context <- factor(scores$context, levels = contexts)
  scores$group_id <- factor(scores$group_id, levels = groups)
  scores$context_group <- factor(
    paste(scores$context, scores$group_id, sep = "::"),
    levels = as.vector(outer(contexts, groups, paste, sep = "::"))
  )
  scores$study <- factor(scores$study, levels = sort(unique(scores$study)))
  scores
}

fit_joint_model <- function(scores, contexts, groups, outcome = "common_score",
                            homogeneous = FALSE, extra_qc = FALSE) {
  d <- prepare_model_data(scores, contexts, groups)
  covariates <- c("age_death_scaled", "pmi_scaled", "study")
  if (extra_qc) covariates <- c(covariates, "aggregate_percent_mt", "robust_qc_fraction")
  formula <- stats::as.formula(paste(outcome, "~ 0 + context_group +",
                                     paste(covariates, collapse = " + ")))
  design_rank <- qr(stats::model.matrix(formula, data = d))$rank
  warning_text <- character()
  fit <- tryCatch(
    withCallingHandlers(
      nlme::lme(
        fixed = formula, random = ~ 1 | projid, data = d,
        weights = if (homogeneous) NULL else nlme::varIdent(form = ~ 1 | context),
        method = "REML", na.action = na.omit,
        control = nlme::lmeControl(opt = "optim", maxIter = 100L,
                                   msMaxIter = 100L, returnObject = TRUE)
      ),
      warning = function(w) {
        warning_text <<- c(warning_text, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) e
  )
  if (inherits(fit, "error")) {
    return(list(success = FALSE, failure_reason = conditionMessage(fit),
                warnings = paste(unique(warning_text), collapse = " | ")))
  }
  beta <- nlme::fixef(fit)
  covariance <- stats::vcov(fit)
  variance <- suppressWarnings(as.numeric(nlme::VarCorr(fit)[1L, "Variance"]))
  residual <- suppressWarnings(as.numeric(nlme::VarCorr(fit)[nrow(nlme::VarCorr(fit)),
                                                               "Variance"]))
  list(success = all(is.finite(beta)) && all(is.finite(covariance)), fit = fit,
       beta = beta, covariance = covariance, donor_variance = variance,
       residual_variance = residual, warnings = paste(unique(warning_text), collapse = " | "),
       failure_reason = "", design_rank = design_rank)
}

context_contrast_vector <- function(contrast, context_id, coefficient_names) {
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  coefficients <- unlist(contrast$coefficients)
  names_needed <- paste0("context_group", context_id, "::", names(coefficients))
  missing <- setdiff(names_needed, coefficient_names)
  if (length(missing)) stop("Model coefficients missing: ", paste(missing, collapse = ", "),
                            call. = FALSE)
  vector[names_needed] <- as.numeric(coefficients)
  vector
}

stratum_contrast_vector <- function(stratum, context_id, coefficient_names) {
  vector <- setNames(rep(0, length(coefficient_names)), coefficient_names)
  ad <- paste0("context_group", context_id, "::", stratum$ad_group)
  nci <- paste0("context_group", context_id, "::", stratum$nci_group)
  if (!all(c(ad, nci) %in% coefficient_names)) return(vector * NA_real_)
  vector[ad] <- 1
  vector[nci] <- -1
  vector
}

linear_test <- function(beta, covariance, vector) {
  estimate <- sum(vector * beta)
  variance <- as.numeric(t(vector) %*% covariance %*% vector)
  if (!is.finite(variance) || variance <= 0) {
    return(list(success = FALSE, estimate = estimate, se = NA_real_,
                lower = NA_real_, upper = NA_real_, p = NA_real_,
                failure_reason = "nonpositive_or_nonfinite_contrast_variance"))
  }
  se <- sqrt(variance)
  list(success = TRUE, estimate = estimate, se = se,
       lower = estimate - stats::qnorm(0.975) * se,
       upper = estimate + stats::qnorm(0.975) * se,
       p = 2 * stats::pnorm(-abs(estimate / se)), failure_reason = "")
}

wald_test <- function(beta, covariance, contrast_matrix) {
  difference <- as.numeric(contrast_matrix %*% beta)
  variance <- contrast_matrix %*% covariance %*% t(contrast_matrix)
  rank <- qr(variance)$rank
  if (rank != nrow(contrast_matrix)) {
    return(list(success = FALSE, statistic = NA_real_, df = rank, p = NA_real_,
                failure_reason = "singular_omnibus_covariance"))
  }
  statistic <- tryCatch(as.numeric(t(difference) %*% solve(variance, difference)),
                        error = function(e) NA_real_)
  if (!is.finite(statistic)) {
    return(list(success = FALSE, statistic = NA_real_, df = rank, p = NA_real_,
                failure_reason = "singular_omnibus_covariance"))
  }
  list(success = TRUE, statistic = statistic, df = nrow(contrast_matrix),
       p = stats::pchisq(statistic, df = nrow(contrast_matrix), lower.tail = FALSE),
       failure_reason = "")
}

required_group_counts <- function(scores, contrast, context_id) {
  groups <- unlist(contrast$required_groups)
  table_value <- table(factor(
    unique(scores[scores$context == context_id, c("projid", "group_id")])$group_id,
    levels = groups
  ))
  setNames(as.integer(table_value), groups)
}

paired_group_counts <- function(scores, contrast, context_1, context_2) {
  groups <- unlist(contrast$required_groups)
  setNames(vapply(groups, function(group) {
    d1 <- unique(scores$projid[scores$context == context_1 & scores$group_id == group])
    d2 <- unique(scores$projid[scores$context == context_2 & scores$group_id == group])
    length(intersect(d1, d2))
  }, integer(1)), groups)
}

eligibility_label <- function(counts, minimum = 5L, confirmatory = 10L) {
  if (any(counts < minimum)) "not_testable_low_donor_count" else
    if (all(counts >= confirmatory)) "eligible_confirmatory" else "eligible_provisional"
}

build_overlap <- function(scores, context_manifest, pair_manifest_value, phase13) {
  groups <- unlist(phase13$groups)
  context_rows <- bind_rows(lapply(context_manifest$context_id, function(context_id) {
    bind_rows(lapply(groups, function(group) data.frame(
      record_type = "context", context_1 = context_id, context_2 = NA_character_,
      group_id = group,
      donors = length(unique(scores$projid[
        scores$context == context_id & scores$group_id == group
      ])), overlap_graph_edge = NA
    )))
  }))
  pair_rows <- bind_rows(lapply(seq_len(nrow(pair_manifest_value)), function(i) {
    pair <- pair_manifest_value[i, ]
    bind_rows(lapply(groups, function(group) {
      d1 <- unique(scores$projid[scores$context == pair$context_1 & scores$group_id == group])
      d2 <- unique(scores$projid[scores$context == pair$context_2 & scores$group_id == group])
      n <- length(intersect(d1, d2))
      data.frame(record_type = "pair", context_1 = pair$context_1,
                 context_2 = pair$context_2, group_id = group,
                 donors = n, overlap_graph_edge = n > 0L)
    }))
  }))
  bind_rows(list(context_rows, pair_rows))
}

evaluate_all_models <- function(scores, phase13, contexts, pairs, modules,
                                coverage, outcome = "common_score",
                                homogeneous = FALSE, extra_qc = FALSE) {
  groups <- unlist(phase13$groups)
  context_modifier <- list()
  context_stratum <- list()
  omnibus <- list()
  pairwise <- list()
  diagnostics <- list()
  fits <- list()
  for (module_index in seq_along(modules)) {
    module_id <- modules[[module_index]]
    d <- scores[scores$module_id == module_id, , drop = FALSE]
    fit <- fit_joint_model(d, contexts, groups, outcome, homogeneous, extra_qc)
    fits[[module_id]] <- fit
    diagnostics[[module_index]] <- data.frame(
      module_id = module_id, outcome = outcome,
      model_formula = "~0+context:diagnosis_sex_APOE_group+age_death_scaled+pmi_scaled+study",
      random_formula = "~1|projid",
      residual_variance_model = if (homogeneous) "homogeneous" else "varIdent(~1|context)",
      method = "REML", observations = nrow(d), donors = length(unique(d$projid)),
      fixed_coefficients = if (fit$success) length(fit$beta) else NA_integer_,
      design_rank = fit$design_rank %||% NA_integer_,
      donor_variance = fit$donor_variance %||% NA_real_,
      residual_variance = fit$residual_variance %||% NA_real_,
      converged = fit$success, warnings = fit$warnings %||% "",
      failure_reason = fit$failure_reason %||% ""
    )
    for (contrast in phase13$contrasts) {
      vectors <- list()
      for (context_id in contexts) {
        counts <- required_group_counts(d, contrast, context_id)
        context_eligibility <- eligibility_label(counts)
        test <- if (fit$success) linear_test(
          fit$beta, fit$covariance,
          context_contrast_vector(contrast, context_id, names(fit$beta))
        ) else list(success = FALSE, estimate = NA, se = NA, lower = NA,
                    upper = NA, p = NA, failure_reason = fit$failure_reason)
        if (fit$success) vectors[[context_id]] <- context_contrast_vector(
          contrast, context_id, names(fit$beta)
        )
        context_modifier[[length(context_modifier) + 1L]] <- data.frame(
          module_id = module_id, contrast_id = contrast$contrast_id,
          context = context_id, estimate = test$estimate, standard_error = test$se,
          confidence_lower = test$lower, confidence_upper = test$upper, p_value = test$p,
          required_group_counts = paste(counts, collapse = "|"),
          eligibility_status = context_eligibility,
          model_status = if (test$success) "estimated" else "not_estimated",
          failure_reason = test$failure_reason
        )
      }
      coverage_pass <- coverage[[module_id]]
      context_rows <- context_modifier[
        vapply(context_modifier, function(x) x$module_id == module_id &&
                 x$contrast_id == contrast$contrast_id, logical(1))
      ]
      context_eligible <- all(vapply(context_rows, function(x)
        !startsWith(x$eligibility_status, "not_testable"), logical(1)))
      omnibus_eligibility <- if (!coverage_pass) "not_testable_common_coverage" else
        if (!context_eligible) "not_testable_low_donor_count" else
          if (!fit$success) "not_testable_model_failure" else "eligible_provisional"
      if (fit$success && coverage_pass && context_eligible) {
        basis <- do.call(rbind, lapply(contexts[-1L], function(context_id) {
          vectors[[context_id]] - vectors[[contexts[[1L]]]]
        }))
        omnibus_test <- wald_test(fit$beta, fit$covariance, basis)
      } else {
        omnibus_test <- list(success = FALSE, statistic = NA, df = length(contexts) - 1L,
                             p = NA, failure_reason = omnibus_eligibility)
      }
      omnibus[[length(omnibus) + 1L]] <- data.frame(
        module_id = module_id, contrast_id = contrast$contrast_id,
        omnibus_df = omnibus_test$df, wald_statistic = omnibus_test$statistic,
        p_value = omnibus_test$p, eligibility_status = omnibus_eligibility,
        model_status = if (omnibus_test$success) "estimated" else "not_estimated",
        failure_reason = omnibus_test$failure_reason
      )
      for (pair_index in seq_len(nrow(pairs))) {
        pair <- pairs[pair_index, ]
        paired_counts <- paired_group_counts(d, contrast, pair$context_1, pair$context_2)
        full_1 <- required_group_counts(d, contrast, pair$context_1)
        full_2 <- required_group_counts(d, contrast, pair$context_2)
        pair_eligibility <- if (!coverage_pass) "not_testable_common_coverage" else
          if (any(full_1 < 5L) || any(full_2 < 5L)) "not_testable_low_donor_count" else
            if (any(paired_counts < 5L)) "not_testable_low_paired_donor_count" else
              if (all(paired_counts >= 10L) && all(full_1 >= 10L) && all(full_2 >= 10L))
                "eligible_confirmatory" else "eligible_provisional"
        test <- if (fit$success && !startsWith(pair_eligibility, "not_testable")) {
          linear_test(fit$beta, fit$covariance,
                      vectors[[pair$context_1]] - vectors[[pair$context_2]])
        } else list(success = FALSE, estimate = NA, se = NA, lower = NA,
                    upper = NA, p = NA, failure_reason = pair_eligibility)
        pairwise[[length(pairwise) + 1L]] <- data.frame(
          module_id = module_id, contrast_id = contrast$contrast_id,
          pair_order = pair$pair_order, pair_id = pair$pair_id,
          context_1 = pair$context_1, context_2 = pair$context_2,
          estimate = test$estimate, standard_error = test$se,
          confidence_lower = test$lower, confidence_upper = test$upper,
          p_value = test$p, direction = if (is.finite(test$estimate))
            ifelse(test$estimate > 0, "context_1_more_positive",
                   ifelse(test$estimate < 0, "context_1_more_negative", "zero")) else NA,
          full_group_counts_context_1 = paste(full_1, collapse = "|"),
          full_group_counts_context_2 = paste(full_2, collapse = "|"),
          paired_group_counts = paste(paired_counts, collapse = "|"),
          minimum_paired_donors = min(paired_counts),
          eligibility_status = pair_eligibility,
          model_status = if (test$success) "estimated" else "not_estimated",
          failure_reason = test$failure_reason
        )
      }
    }
    for (stratum in strata_from_phase13(phase13)) {
      for (context_id in contexts) {
        test <- if (fit$success) linear_test(
          fit$beta, fit$covariance,
          stratum_contrast_vector(stratum, context_id, names(fit$beta))
        ) else list(success = FALSE, estimate = NA, se = NA, lower = NA,
                    upper = NA, p = NA, failure_reason = fit$failure_reason)
        context_stratum[[length(context_stratum) + 1L]] <- data.frame(
          module_id = module_id, stratum_id = stratum$stratum_id,
          context = context_id, estimate = test$estimate, standard_error = test$se,
          confidence_lower = test$lower, confidence_upper = test$upper,
          p_value = test$p, model_status = if (test$success) "estimated" else "not_estimated",
          failure_reason = test$failure_reason
        )
      }
    }
  }
  list(context_modifier = bind_rows(context_modifier),
       context_stratum = bind_rows(context_stratum), omnibus = bind_rows(omnibus),
       pairwise = bind_rows(pairwise), diagnostics = bind_rows(diagnostics), fits = fits)
}

apply_bh <- function(results) {
  results$q_value <- NA_real_
  eligible <- is.finite(results$p_value)
  results$q_value[eligible] <- stats::p.adjust(results$p_value[eligible], method = "BH")
  results
}

complete_case_results <- function(scores, phase13, contexts, pairs, modules, coverage) {
  rows <- list()
  groups <- unlist(phase13$groups)
  for (module_id in modules) {
    d_module <- scores[scores$module_id == module_id, , drop = FALSE]
    for (pair_index in seq_len(nrow(pairs))) {
      pair <- pairs[pair_index, ]
      donors_1 <- unique(d_module$projid[d_module$context == pair$context_1])
      donors_2 <- unique(d_module$projid[d_module$context == pair$context_2])
      complete_donors <- intersect(donors_1, donors_2)
      d <- d_module[d_module$projid %in% complete_donors &
                      d_module$context %in% c(pair$context_1, pair$context_2), ]
      fit <- if (coverage[[module_id]]) fit_joint_model(
        d, c(pair$context_1, pair$context_2), groups
      ) else list(success = FALSE, failure_reason = "not_testable_common_coverage")
      for (contrast in phase13$contrasts) {
        counts <- paired_group_counts(d_module, contrast, pair$context_1, pair$context_2)
        eligible <- coverage[[module_id]] && all(counts >= 5L) && fit$success
        test <- if (eligible) {
          v1 <- context_contrast_vector(contrast, pair$context_1, names(fit$beta))
          v2 <- context_contrast_vector(contrast, pair$context_2, names(fit$beta))
          linear_test(fit$beta, fit$covariance, v1 - v2)
        } else list(success = FALSE, estimate = NA, se = NA, lower = NA,
                    upper = NA, p = NA,
                    failure_reason = if (!coverage[[module_id]])
                      "not_testable_common_coverage" else if (any(counts < 5L))
                        "not_testable_low_paired_donor_count" else fit$failure_reason)
        rows[[length(rows) + 1L]] <- data.frame(
          module_id = module_id, contrast_id = contrast$contrast_id,
          pair_id = pair$pair_id, complete_donors = length(complete_donors),
          paired_group_counts = paste(counts, collapse = "|"),
          estimate = test$estimate, standard_error = test$se,
          confidence_lower = test$lower, confidence_upper = test$upper,
          p_value = test$p, direction = if (is.finite(test$estimate)) sign(test$estimate) else NA,
          status = if (test$success) "estimated" else test$failure_reason
        )
      }
    }
  }
  bind_rows(rows)
}

extract_stability <- function(analysis, analysis_type, repetition_id,
                              omitted_donor = NA_character_) {
  omnibus <- analysis$omnibus[, c("module_id", "contrast_id", "wald_statistic",
                                   "p_value", "model_status", "failure_reason")]
  omnibus$test_type <- "omnibus"
  omnibus$test_id <- omnibus$contrast_id
  omnibus$estimate <- omnibus$wald_statistic
  pairwise <- analysis$pairwise[, c("module_id", "contrast_id", "pair_id",
                                     "estimate", "p_value", "model_status",
                                     "failure_reason")]
  pairwise$test_type <- "pairwise"
  pairwise$test_id <- paste(pairwise$contrast_id, pairwise$pair_id, sep = "::")
  omnibus$analysis_type <- analysis_type
  pairwise$analysis_type <- analysis_type
  omnibus$repetition_id <- repetition_id
  pairwise$repetition_id <- repetition_id
  omnibus$omitted_donor <- omitted_donor
  pairwise$omitted_donor <- omitted_donor
  omnibus$donor_resampling_unit <- "whole_donor"
  pairwise$donor_resampling_unit <- "whole_donor"
  columns <- c("analysis_type", "repetition_id", "test_type", "module_id",
               "contrast_id", "test_id", "estimate", "p_value", "model_status",
               "failure_reason", "omitted_donor", "donor_resampling_unit")
  bind_rows(list(omnibus[, columns], pairwise[, columns]))
}

resample_whole_donors <- function(scores, phase_cfg, repetition, balanced = FALSE) {
  donor_meta <- unique(scores[c("projid", "group_id")])
  set.seed(seed_for(phase_cfg, paste0(if (balanced) "balance" else "bootstrap", repetition)))
  if (balanced) {
    minimum <- min(table(donor_meta$group_id))
    selected <- unlist(lapply(split(donor_meta$projid, donor_meta$group_id), sample,
                              size = minimum, replace = FALSE), use.names = FALSE)
  } else {
    selected <- sample(donor_meta$projid, nrow(donor_meta), replace = TRUE)
  }
  bind_rows(lapply(seq_along(selected), function(i) {
    d <- scores[scores$projid == selected[[i]], , drop = FALSE]
    d$projid <- paste0(selected[[i]], "::resample_", i)
    d$donor_context_id <- paste(d$projid, d$context, sep = "::")
    d
  }))
}

run_stability <- function(scores, phase_cfg, phase13, contexts, pairs, modules,
                          coverage, workers) {
  bootstrap_n <- as.integer(phase_cfg$pilot$bootstrap_repetitions)
  balance_n <- as.integer(phase_cfg$pilot$balance_repetitions)
  donors <- sort(unique(scores$projid))
  tasks <- c(
    lapply(seq_len(bootstrap_n), function(i) list(type = "bootstrap", id = i)),
    lapply(seq_len(balance_n), function(i) list(type = "balance", id = i)),
    lapply(seq_along(donors), function(i) list(type = "leave_one_donor_out", id = i,
                                               donor = donors[[i]]))
  )
  worker <- function(task) {
    d <- if (task$type == "bootstrap") {
      resample_whole_donors(scores, phase_cfg, task$id, FALSE)
    } else if (task$type == "balance") {
      resample_whole_donors(scores, phase_cfg, task$id, TRUE)
    } else scores[scores$projid != task$donor, , drop = FALSE]
    analysis <- evaluate_all_models(d, phase13, contexts, pairs, modules,
                                    coverage)
    extract_stability(analysis, task$type, task$id,
                      task$donor %||% NA_character_)
  }
  bind_rows(ordered_lapply(tasks, worker, workers))
}

stability_summary <- function(primary, stability, test_type) {
  if (test_type == "omnibus") {
    base <- primary[, c("module_id", "contrast_id", "wald_statistic")]
    base$test_id <- base$contrast_id
    names(base)[names(base) == "wald_statistic"] <- "primary_estimate"
  } else {
    base <- primary[, c("module_id", "contrast_id", "pair_id", "estimate")]
    base$test_id <- paste(base$contrast_id, base$pair_id, sep = "::")
    names(base)[names(base) == "estimate"] <- "primary_estimate"
  }
  subset <- stability[stability$test_type == test_type, ]
  rows <- lapply(seq_len(nrow(base)), function(i) {
    x <- subset[subset$module_id == base$module_id[[i]] &
                  subset$test_id == base$test_id[[i]], ]
    success <- is.finite(x$estimate) & x$model_status == "estimated"
    direction <- if (is.finite(base$primary_estimate[[i]]) &&
                     base$primary_estimate[[i]] != 0) {
      mean(sign(x$estimate[success]) == sign(base$primary_estimate[[i]]))
    } else NA_real_
    loo <- x$analysis_type == "leave_one_donor_out" & success
    loo_reversals <- if (any(loo) && is.finite(base$primary_estimate[[i]]) &&
                         base$primary_estimate[[i]] != 0) {
      sum(sign(x$estimate[loo]) != sign(base$primary_estimate[[i]]))
    } else NA_integer_
    data.frame(
      module_id = base$module_id[[i]], contrast_id = base$contrast_id[[i]],
      test_id = base$test_id[[i]], primary_estimate = base$primary_estimate[[i]],
      attempted_replicates = nrow(x), successful_replicates = sum(success),
      success_fraction = if (nrow(x)) mean(success) else NA,
      direction_fraction = direction, loo_sign_reversals = loo_reversals,
      bootstrap_successes = sum(x$analysis_type == "bootstrap" & success),
      balance_successes = sum(x$analysis_type == "balance" & success)
    )
  })
  bind_rows(rows)
}

validate_phase14_output <- function(path, expected_contexts, expected_pairs,
                                    expected_omnibus, expected_pairwise,
                                    expected_modifier, expected_stratum,
                                    expected_status, declared_files = NULL) {
  if (!dir.exists(path)) stop("Phase 14 output directory is missing: ", path,
                              call. = FALSE)
  expected <- declared_files %||% c(
    "heterogeneity_analysis_manifest.tsv", "heterogeneity_cell_context_manifest.tsv",
    "heterogeneity_context_pair_manifest.tsv", "heterogeneity_contrast_manifest.tsv",
    "heterogeneity_module_manifest.tsv", "heterogeneity_common_module_members.tsv",
    "heterogeneity_input_inventory.tsv", "heterogeneity_source_checks.tsv",
    "heterogeneity_donor_context_overlap.tsv", "heterogeneity_omnibus_test_manifest.tsv",
    "heterogeneity_pairwise_test_manifest.tsv", "heterogeneity_common_scores.tsv.gz",
    "heterogeneity_nci_reference_parameters.tsv.gz", "heterogeneity_context_modifier_effects.tsv",
    "heterogeneity_context_stratum_effects.tsv", "heterogeneity_omnibus_results.tsv",
    "heterogeneity_pairwise_results.tsv", "heterogeneity_model_diagnostics.tsv",
    "heterogeneity_pc1_loadings.tsv.gz", "heterogeneity_score_reliability.tsv",
    "heterogeneity_complete_case_results.tsv", "heterogeneity_stability_replicates.tsv.gz",
    "heterogeneity_omnibus_stability_summary.tsv", "heterogeneity_pairwise_stability_summary.tsv",
    "heterogeneity_gate_decisions.tsv", "heterogeneity_global_decisions.tsv",
    "heterogeneity_claim_summary.tsv", "heterogeneity_stage_status.tsv",
    "heterogeneity_checks.tsv", "heterogeneity_artifacts.tsv", "heterogeneity_status.tsv"
  )
  actual <- sort(list.files(path, all.files = FALSE, recursive = FALSE))
  if (!identical(actual, sort(expected))) {
    stop("Final Phase 14 directory does not contain exactly the 31 declared files",
         call. = FALSE)
  }
  if (length(list.dirs(path, recursive = FALSE, full.names = FALSE))) {
    stop("Final Phase 14 directory contains an undeclared subdirectory", call. = FALSE)
  }
  read_table <- function(name) data.table::fread(file.path(path, name),
                                                  data.table = FALSE,
                                                  showProgress = FALSE)
  tables <- lapply(expected[grepl("[.]tsv([.]gz)?$", expected)], read_table)
  if (any(!vapply(tables, function(x) identical(names(x)[[1L]], "schema_version"),
                  logical(1)))) stop("Every Phase 14 TSV must start with schema_version",
                                     call. = FALSE)
  dimensions <- c(
    nrow(read_table("heterogeneity_cell_context_manifest.tsv")),
    nrow(read_table("heterogeneity_context_pair_manifest.tsv")),
    nrow(read_table("heterogeneity_omnibus_results.tsv")),
    nrow(read_table("heterogeneity_pairwise_results.tsv")),
    nrow(read_table("heterogeneity_context_modifier_effects.tsv")),
    nrow(read_table("heterogeneity_context_stratum_effects.tsv"))
  )
  if (!identical(as.integer(dimensions), as.integer(c(
    expected_contexts, expected_pairs, expected_omnibus, expected_pairwise,
    expected_modifier, expected_stratum
  )))) stop("Phase 14 output dimensions do not match the frozen contract", call. = FALSE)
  status <- read_table("heterogeneity_status.tsv")
  if (nrow(status) != 1L || status$validation_status[[1L]] != expected_status) {
    stop("Phase 14 validation status does not match expectation", call. = FALSE)
  }
  if (expected_status == "nonfinal_smoke_test" &&
      status$scientific_decision[[1L]] != "not_applicable_pilot") {
    stop("Pilot output must have scientific_decision=not_applicable_pilot",
         call. = FALSE)
  }
  artifacts <- read_table("heterogeneity_artifacts.tsv")
  if (!setequal(artifacts$artifact_file, expected)) {
    stop("Artifact manifest does not declare every Phase 14 file", call. = FALSE)
  }
  hashed <- !is.na(artifacts$sha256) & nzchar(artifacts$sha256)
  for (i in which(hashed)) {
    if (!identical(sha256_file(file.path(path, artifacts$artifact_file[[i]])),
                   artifacts$sha256[[i]])) {
      stop("Artifact hash mismatch: ", artifacts$artifact_file[[i]], call. = FALSE)
    }
  }
  checks <- read_table("heterogeneity_checks.tsv")
  blocking_failures <- checks$blocking & !checks$passed
  if (any(blocking_failures)) stop("Phase 14 contains failed blocking checks", call. = FALSE)
  invisible(TRUE)
}

main <- function() {
  started <- Sys.time()
  args <- parse_phase14_cli(commandArgs(trailingOnly = TRUE))
  required <- c("yaml", "data.table", "nlme", "digest")
  missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing)) stop("Missing required packages: ", paste(missing, collapse = ", "),
                            call. = FALSE)
  root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- absolute_path(args$config, root)
  execution_path <- absolute_path(args$execution_config, root)
  config <- yaml::read_yaml(config_path)
  execution_cfg <- yaml::read_yaml(execution_path)
  phase_path <- absolute_path(config$project$phase14_modifier_heterogeneity_config, root)
  phase_cfg <- yaml::read_yaml(phase_path)
  phase13_path <- absolute_path(phase_cfg$paths$phase13_config, root)
  phase13 <- yaml::read_yaml(phase13_path)
  member_path <- absolute_path(phase_cfg$paths$module_members, root)
  members <- data.table::fread(member_path, data.table = FALSE)
  pilot <- isTRUE(config$scope$pilot)
  if (!pilot) {
    stop("Phase 14 production execution is not authorized by this local-pilot implementation; ",
         "validate the seven-context Phase 13 production bundle and approve production first.",
         call. = FALSE)
  }
  RNGkind("L'Ecuyer-CMRG")
  set.seed(as.integer(phase_cfg$randomization$base_seed))
  stage_root <- absolute_path(config$outputs$root, root)
  final_dir <- file.path(stage_root, phase_cfg$paths$output_relative)
  if (dir.exists(final_dir)) {
    stop("Phase 14 output already exists and will not be overwritten: ", final_dir,
         call. = FALSE)
  }
  staging <- file.path(stage_root, paste0(".phase14_staging_", Sys.getpid()))
  dir.create(staging, recursive = TRUE, showWarnings = FALSE)
  published <- FALSE
  on.exit(if (!published && dir.exists(staging)) unlink(staging, recursive = TRUE), add = TRUE)

  context_manifest <- context_manifest_from_phase13(
    phase13, unlist(phase_cfg$pilot$contexts)
  )
  pairs <- pair_manifest(context_manifest)
  contrasts <- contrast_manifest_from_phase13(phase13)
  modules <- module_manifest_from_phase13(phase13)
  profiles <- build_pilot_profiles(phase_cfg, phase13, context_manifest, modules)
  score_bundle <- build_common_scores(profiles, members, phase_cfg, modules,
                                      context_manifest)
  modules <- score_bundle$modules
  scores <- score_bundle$scores
  coverage <- setNames(modules$common_coverage_pass, modules$module_id)
  overlap <- build_overlap(scores, context_manifest, pairs, phase13)

  cat("Phase 14 local pilot: fitting four joint repeated-donor models\n")
  primary <- evaluate_all_models(
    scores, phase13, context_manifest$context_id, pairs, modules$module_id, coverage
  )
  primary$omnibus <- apply_bh(primary$omnibus)
  primary$pairwise <- apply_bh(primary$pairwise)
  primary$omnibus$effect_family <- phase_cfg$multiple_testing$omnibus_family
  primary$pairwise$effect_family <- phase_cfg$multiple_testing$pairwise_family
  primary$pairwise$parent_omnibus_q <- primary$omnibus$q_value[
    match(paste(primary$pairwise$module_id, primary$pairwise$contrast_id),
          paste(primary$omnibus$module_id, primary$omnibus$contrast_id))
  ]

  omnibus_manifest <- primary$omnibus[c(
    "module_id", "contrast_id", "omnibus_df", "eligibility_status"
  )]
  omnibus_manifest$test_order <- seq_len(nrow(omnibus_manifest))
  pairwise_manifest <- primary$pairwise[c(
    "module_id", "contrast_id", "pair_order", "pair_id", "context_1", "context_2",
    "full_group_counts_context_1", "full_group_counts_context_2",
    "paired_group_counts", "minimum_paired_donors", "eligibility_status"
  )]
  pairwise_manifest$test_order <- seq_len(nrow(pairwise_manifest))

  cat("Phase 14 local pilot: fitting pair-complete sensitivities\n")
  complete_case <- complete_case_results(
    scores, phase13, context_manifest$context_id, pairs, modules$module_id, coverage
  )
  worker_plan <- phase14_worker_plan(execution_cfg$execution)
  cat("Phase 14 local pilot: running donor-level stability checks with ",
      worker_plan$effective, " worker(s)\n", sep = "")
  stability <- run_stability(
    scores, phase_cfg, phase13, context_manifest$context_id, pairs,
    modules$module_id, coverage, worker_plan$effective
  )
  omnibus_stability <- stability_summary(primary$omnibus, stability, "omnibus")
  pairwise_stability <- stability_summary(primary$pairwise, stability, "pairwise")

  reliability <- bind_rows(lapply(seq_len(nrow(modules)), function(i) {
    module_id <- modules$module_id[[i]]
    d <- scores[scores$module_id == module_id, ]
    bind_rows(lapply(context_manifest$context_id, function(context_id) {
      x <- d[d$context == context_id, ]
      data.frame(
        module_id = module_id, context = context_id,
        frozen_genes = modules$frozen_genes[[i]],
        common_genes = modules$common_admitted[[i]],
        common_fraction = modules$common_fraction[[i]],
        common_coverage_pass = modules$common_coverage_pass[[i]],
        common_vs_pc1_correlation = stats::cor(x$common_score, x$pc1_score),
        common_vs_phase13_correlation = stats::cor(
          x$common_score, x$phase13_original_score
        ), pc1_orientation_pass = stats::cor(x$common_score, x$pc1_score) >= 0
      )
    }))
  }))

  complete_key <- paste(complete_case$module_id, complete_case$contrast_id,
                        complete_case$pair_id)
  pair_key <- paste(primary$pairwise$module_id, primary$pairwise$contrast_id,
                    primary$pairwise$pair_id)
  complete_estimate <- complete_case$estimate[match(pair_key, complete_key)]
  pair_stability_key <- paste(pairwise_stability$module_id,
                              pairwise_stability$contrast_id,
                              pairwise_stability$test_id)
  primary_stability_key <- paste(primary$pairwise$module_id,
                                 primary$pairwise$contrast_id,
                                 paste(primary$pairwise$contrast_id,
                                       primary$pairwise$pair_id, sep = "::"))
  stability_match <- match(primary_stability_key, pair_stability_key)
  gate <- data.frame(
    module_id = primary$pairwise$module_id,
    contrast_id = primary$pairwise$contrast_id,
    pair_id = primary$pairwise$pair_id,
    eligible = !startsWith(primary$pairwise$eligibility_status, "not_testable"),
    parent_omnibus_fdr_pass = is.finite(primary$pairwise$parent_omnibus_q) &
      primary$pairwise$parent_omnibus_q <= phase_cfg$multiple_testing$q_threshold,
    pairwise_fdr_pass = is.finite(primary$pairwise$q_value) &
      primary$pairwise$q_value <= phase_cfg$multiple_testing$q_threshold,
    effect_size_pass = is.finite(primary$pairwise$estimate) &
      abs(primary$pairwise$estimate) >= phase_cfg$analysis$sesoi_nci_sd,
    confidence_interval_excludes_zero = is.finite(primary$pairwise$confidence_lower) &
      (primary$pairwise$confidence_lower > 0 | primary$pairwise$confidence_upper < 0),
    pair_confirmatory = primary$pairwise$eligibility_status == "eligible_confirmatory",
    complete_case_direction_retained = is.finite(complete_estimate) &
      sign(complete_estimate) == sign(primary$pairwise$estimate),
    stability_success_fraction = pairwise_stability$success_fraction[stability_match],
    stability_direction_fraction = pairwise_stability$direction_fraction[stability_match],
    loo_sign_reversals = pairwise_stability$loo_sign_reversals[stability_match],
    scientific_status = "not_applicable_pilot",
    permitted_wording = "Synthetic local pilot; no Claim 2 inference is permitted"
  )
  global_decisions <- data.frame(
    module_id = primary$omnibus$module_id,
    contrast_id = primary$omnibus$contrast_id,
    eligibility_status = primary$omnibus$eligibility_status,
    omnibus_q_value = primary$omnibus$q_value,
    global_status = "not_applicable_pilot",
    permitted_wording = "Synthetic local pilot; no Claim 2 inference is permitted"
  )
  claim_summary <- data.frame(
    claim_scope = c("sex", "APOE", "direct_respiratory", "supporting_program", "overall"),
    scientific_decision = "not_applicable_pilot",
    supported_rows = 0L,
    conclusion = "Synthetic smoke test only; production data were not analyzed"
  )

  phase13_status <- file.path(stage_root, phase_cfg$paths$phase13_relative,
                              "respiratory_status.tsv")
  input_inventory <- data.frame(
    input_id = c("phase14_config", "phase13_config", "phase13_module_members",
                 "phase13_local_status_reference"),
    path = c(phase_path, phase13_path, member_path, phase13_status),
    exists = c(TRUE, TRUE, TRUE, file.exists(phase13_status)),
    sha256 = vapply(c(phase_path, phase13_path, member_path, phase13_status),
                    sha256_file, character(1)),
    usage = c("frozen_phase14_design", "inherited_definitions", "inherited_memberships",
              "provenance_only_not_scientific_input")
  )
  source_checks <- data.frame(
    check_id = c("pilot_fixture_used", "phase13_scores_not_reused",
                 "donor_context_key_unique", "member_keys_unique"),
    passed = c(TRUE, TRUE, !anyDuplicated(scores[c("donor_context_id", "module_id")]),
               !anyDuplicated(members[c("module_id", "frozen_gene_symbol")])),
    blocking = TRUE,
    detail = c(phase_cfg$pilot$fixture_id,
               "one-context Phase 13 pilot is intentionally not a heterogeneity input",
               "one score per donor/context/module", "frozen module membership keys")
  )
  analysis_manifest <- data.frame(
    analysis_id = phase_cfg$analysis$analysis_id,
    title = phase_cfg$analysis$title,
    definitions_approved = phase_cfg$analysis$definitions_approved,
    definitions_frozen = phase_cfg$analysis$definitions_frozen,
    approval_basis = phase_cfg$analysis$approval_basis,
    production_approved = phase_cfg$analysis$production_approved,
    execution_scope = "local_pilot_only", fixture_id = phase_cfg$pilot$fixture_id,
    model_formula = phase_cfg$analysis$model_formula,
    random_formula = phase_cfg$analysis$random_formula,
    residual_variance = phase_cfg$analysis$residual_variance,
    sesoi_nci_sd = phase_cfg$analysis$sesoi_nci_sd,
    omnibus_family = phase_cfg$multiple_testing$omnibus_family,
    pairwise_family = phase_cfg$multiple_testing$pairwise_family,
    phase14_config_sha256 = sha256_file(phase_path),
    phase13_config_sha256 = sha256_file(phase13_path),
    module_members_sha256 = sha256_file(member_path)
  )

  positive <- primary$pairwise[
    primary$pairwise$module_id == "mtdna_oxphos_13" &
      primary$pairwise$contrast_id == "sex_F_minus_M__e33" &
      primary$pairwise$context_1 == "astrocytes" &
      primary$pairwise$context_2 == "excitatory_neurons", ]
  null_rows <- primary$pairwise[
    primary$pairwise$module_id == "nuclear_oxphos_structural_86" &
      is.finite(primary$pairwise$estimate), ]
  checks <- bind_rows(list(
    source_checks,
    data.frame(
      check_id = c(
        "contexts_3", "pairs_3", "modules_4", "contrasts_7", "members_273",
        "omnibus_rows_28", "pairwise_rows_84", "modifier_rows_84",
        "stratum_rows_72", "known_positive_heterogeneity",
        "known_null_present", "precise_equivalence_present", "missing_context_present",
        "low_paired_count_present", "common_coverage_failure_present",
        "sign_reversal_present", "pc1_orientation_nonnegative", "bh_values_valid",
        "all_models_terminal", "status_is_nonfinal"
      ),
      passed = c(
        nrow(context_manifest) == 3L, nrow(pairs) == 3L, nrow(modules) == 4L,
        nrow(contrasts) == 7L, nrow(members) == 273L,
        nrow(primary$omnibus) == 28L, nrow(primary$pairwise) == 84L,
        nrow(primary$context_modifier) == 84L, nrow(primary$context_stratum) == 72L,
        nrow(positive) == 1L && is.finite(positive$estimate) && positive$estimate > 0.5,
        nrow(null_rows) > 0L && min(abs(null_rows$estimate)) < 0.10,
        nrow(null_rows) > 0L && any(null_rows$confidence_lower > -0.25 &
                                     null_rows$confidence_upper < 0.25),
        nrow(scores) < length(unique(scores$projid)) * 3L * 4L,
        any(primary$pairwise$eligibility_status == "not_testable_low_paired_donor_count"),
        any(primary$pairwise$eligibility_status == "not_testable_common_coverage"),
        any(primary$pairwise$estimate > 0.25, na.rm = TRUE) &&
          any(primary$pairwise$estimate < -0.25, na.rm = TRUE),
        all(reliability$common_vs_pc1_correlation >= 0),
        all(primary$omnibus$q_value[is.finite(primary$omnibus$q_value)] >= 0 &
              primary$omnibus$q_value[is.finite(primary$omnibus$q_value)] <= 1) &&
          all(primary$pairwise$q_value[is.finite(primary$pairwise$q_value)] >= 0 &
                primary$pairwise$q_value[is.finite(primary$pairwise$q_value)] <= 1),
        all(primary$diagnostics$converged | nzchar(primary$diagnostics$failure_reason)),
        identical(phase_cfg$pilot$validation_status, "nonfinal_smoke_test")
      ),
      blocking = TRUE,
      detail = c(
        "frozen pilot contexts", "all unordered pilot pairs", "inherited modules",
        "inherited modifiers", "inherited memberships", "structural grid",
        "structural grid", "context modifier grid", "stratum grid",
        "mtdna sex/e33 astrocyte-minus-excitatory fixture", "nuclear OXPHOS null fixture",
        "nuclear OXPHOS high-correlation equivalence fixture",
        "Male/e2 donors intentionally omit contexts", "Male/e2 overlap is below five",
        "MIB/MICOS admits only ten of nineteen genes", "translation fixture changes sign",
        "PC1 is oriented toward common mean-z", "BH q values lie in [0,1]",
        "model success or explicit failure", "pilot cannot become scientific evidence"
      )
    )
  ))
  if (any(checks$blocking & !checks$passed)) {
    failed <- checks$check_id[checks$blocking & !checks$passed]
    stop("Blocking Phase 14 pilot checks failed: ", paste(failed, collapse = ", "),
         call. = FALSE)
  }
  stage_status <- data.frame(
    stage_order = 1:5,
    stage_id = c("definitions", "synthetic_fixture", "joint_models", "stability", "publication"),
    dependency = c("none", "definitions", "synthetic_fixture", "joint_models", "checks"),
    terminal_status = c("complete", "complete", "complete", "complete", "ready"),
    records = c(1L, nrow(scores), nrow(primary$diagnostics), nrow(stability), 31L),
    started_utc = format(started, tz = "UTC"),
    completed_utc = format(Sys.time(), tz = "UTC")
  )

  tables <- list(
    heterogeneity_analysis_manifest.tsv = list(analysis_manifest, "phase14_analysis_manifest_v1"),
    heterogeneity_cell_context_manifest.tsv = list(context_manifest, "phase14_context_manifest_v1"),
    heterogeneity_context_pair_manifest.tsv = list(pairs, "phase14_context_pair_manifest_v1"),
    heterogeneity_contrast_manifest.tsv = list(contrasts, "phase14_contrast_manifest_v1"),
    heterogeneity_module_manifest.tsv = list(modules, "phase14_module_manifest_v1"),
    heterogeneity_common_module_members.tsv = list(score_bundle$members, "phase14_common_members_v1"),
    heterogeneity_input_inventory.tsv = list(input_inventory, "phase14_input_inventory_v1"),
    heterogeneity_source_checks.tsv = list(source_checks, "phase14_source_checks_v1"),
    heterogeneity_donor_context_overlap.tsv = list(overlap, "phase14_overlap_v1"),
    heterogeneity_omnibus_test_manifest.tsv = list(omnibus_manifest, "phase14_omnibus_manifest_v1"),
    heterogeneity_pairwise_test_manifest.tsv = list(pairwise_manifest, "phase14_pairwise_manifest_v1"),
    heterogeneity_common_scores.tsv.gz = list(scores, "phase14_common_scores_v1"),
    heterogeneity_nci_reference_parameters.tsv.gz = list(score_bundle$references, "phase14_nci_reference_v1"),
    heterogeneity_context_modifier_effects.tsv = list(primary$context_modifier, "phase14_context_modifier_v1"),
    heterogeneity_context_stratum_effects.tsv = list(primary$context_stratum, "phase14_context_stratum_v1"),
    heterogeneity_omnibus_results.tsv = list(primary$omnibus, "phase14_omnibus_results_v1"),
    heterogeneity_pairwise_results.tsv = list(primary$pairwise, "phase14_pairwise_results_v1"),
    heterogeneity_model_diagnostics.tsv = list(primary$diagnostics, "phase14_model_diagnostics_v1"),
    heterogeneity_pc1_loadings.tsv.gz = list(score_bundle$loadings, "phase14_pc1_loadings_v1"),
    heterogeneity_score_reliability.tsv = list(reliability, "phase14_score_reliability_v1"),
    heterogeneity_complete_case_results.tsv = list(complete_case, "phase14_complete_case_v1"),
    heterogeneity_stability_replicates.tsv.gz = list(stability, "phase14_stability_replicates_v1"),
    heterogeneity_omnibus_stability_summary.tsv = list(omnibus_stability, "phase14_omnibus_stability_v1"),
    heterogeneity_pairwise_stability_summary.tsv = list(pairwise_stability, "phase14_pairwise_stability_v1"),
    heterogeneity_gate_decisions.tsv = list(gate, "phase14_gate_decisions_v1"),
    heterogeneity_global_decisions.tsv = list(global_decisions, "phase14_global_decisions_v1"),
    heterogeneity_claim_summary.tsv = list(claim_summary, "phase14_claim_summary_v1"),
    heterogeneity_stage_status.tsv = list(stage_status, "phase14_stage_status_v1"),
    heterogeneity_checks.tsv = list(checks, "phase14_checks_v1")
  )
  for (name in names(tables)) {
    atomic_write_tsv(tables[[name]][[1L]], file.path(staging, name),
                     tables[[name]][[2L]])
  }
  declared <- unlist(phase_cfg$outputs$declared_files)
  artifacts <- bind_rows(lapply(declared, function(name) {
    path <- file.path(staging, name)
    available <- file.exists(path)
    data.frame(
      artifact_file = name,
      artifact_role = if (grepl("manifest|checks|status", name)) "control" else "scientific",
      path = file.path(config$outputs$root, phase_cfg$paths$output_relative, name),
      records = if (available) count_records(path) else NA_integer_,
      bytes = if (available) file.info(path)$size else NA_real_,
      sha256 = if (available) sha256_file(path) else NA_character_,
      validation_status = phase_cfg$pilot$validation_status
    )
  }))
  atomic_write_tsv(artifacts, file.path(staging, "heterogeneity_artifacts.tsv"),
                   "phase14_artifacts_v1")
  status <- data.frame(
    execution_stage = execution_cfg$execution$execution_stage,
    execution_phase = execution_cfg$execution$execution_phase,
    backend = execution_cfg$execution$backend, run_id = execution_cfg$execution$run_id,
    stable_task_id = "global:modifier_heterogeneity",
    task_mode = "modifier_heterogeneity",
    output_schema = phase_cfg$analysis$output_schema,
    fixture_id = phase_cfg$pilot$fixture_id,
    contexts = nrow(context_manifest), context_pairs = nrow(pairs),
    modifier_contrasts = nrow(contrasts), modules = nrow(modules),
    module_memberships = nrow(members), omnibus_rows = nrow(primary$omnibus),
    pairwise_rows = nrow(primary$pairwise),
    context_modifier_rows = nrow(primary$context_modifier),
    context_stratum_rows = nrow(primary$context_stratum),
    stability_workers_requested = worker_plan$requested,
    stability_workers_effective = worker_plan$effective,
    stability_backend = worker_plan$backend,
    failed_checks = "", scientific_decision = phase_cfg$pilot$scientific_decision,
    validation_status = phase_cfg$pilot$validation_status,
    pilot_results_are_scientific_evidence = FALSE,
    git_revision = git_revision(root), timestamp_utc = format(Sys.time(), tz = "UTC")
  )
  atomic_write_tsv(status, file.path(staging, "heterogeneity_status.tsv"),
                   "phase14_status_v1")
  validate_phase14_output(
    staging, 3L, 3L, 28L, 84L, 84L, 72L,
    phase_cfg$pilot$validation_status, declared
  )
  dir.create(dirname(final_dir), recursive = TRUE, showWarnings = FALSE)
  if (!file.rename(staging, final_dir)) {
    stop("Could not atomically publish Phase 14 output", call. = FALSE)
  }
  published <- TRUE
  cat("Phase 14 local pilot published: ", final_dir, "\n", sep = "")
  cat("Technical status: ", phase_cfg$pilot$validation_status, "\n", sep = "")
  cat("Scientific decision: ", phase_cfg$pilot$scientific_decision, "\n", sep = "")
  invisible(TRUE)
}

if (sys.nframe() == 0L) main()
