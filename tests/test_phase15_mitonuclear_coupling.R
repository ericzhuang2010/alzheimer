#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_test_cli <- function(args) {
  out <- list(
    validate_output = NULL, expected_contexts = NULL,
    expected_general_rows = NULL, expected_modifier_rows = NULL,
    expected_stratum_rows = NULL, expected_general_gates = NULL,
    expected_modifier_gates = NULL, expected_status = NULL
  )
  keys <- c(
    "--validate-output", "--expected-contexts", "--expected-general-rows",
    "--expected-modifier-rows", "--expected-stratum-rows",
    "--expected-general-gates", "--expected-modifier-gates", "--expected-status"
  )
  i <- 1L
  while (i <= length(args)) {
    if (!args[[i]] %in% keys || i == length(args)) {
      stop("Unknown test option or missing value: ", args[[i]], call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", args[[i]]))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  out
}

assert <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/15_run_mitonuclear_coupling.R"), local = FALSE)
source(file.path(root, "scripts/15_run_mitonuclear_coupling_production.R"), local = FALSE)
args <- parse_test_cli(commandArgs(trailingOnly = TRUE))

required <- c("yaml", "data.table", "sandwich", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing required packages: ", paste(missing, collapse = ", "),
                          call. = FALSE)

cfg <- yaml::read_yaml(file.path(root, "config/phase15_mitonuclear_coupling.yml"))
phase13 <- yaml::read_yaml(file.path(root, "config/phase13_respiratory_modifier.yml"))
all_members <- data.table::fread(file.path(root, "config/phase13_respiratory_modules.tsv"),
                                 data.table = FALSE)
contexts <- context_manifest_from_phase13(phase13, unlist(cfg$pilot$contexts))
endpoints <- endpoint_manifest_from_config(cfg)
contrasts <- contrast_manifest_from_phase13(phase13)
modules <- module_manifest_from_phase13(phase13)
members <- all_members[all_members$module_id %in% modules$module_id, ]

assert(nrow(contexts) == 3L, "Pilot must contain three primary contexts")
assert(identical(contexts$context_id,
                 c("astrocytes", "excitatory_neurons", "inhibitory_neurons")),
       "Phase 15 primary context order changed")
assert(nrow(endpoints) == 3L, "Expected three frozen endpoints")
assert(nrow(contrasts) == 8L && sum(contrasts$contrast_type == "modifier") == 7L,
       "Expected one general and seven modifier contrasts")
assert(nrow(modules) == 2L && nrow(members) == 99L,
       "Expected frozen 13+86 C3 module memberships")
assert(identical(as.integer(table(factor(members$module_id, levels = modules$module_id))),
                 c(13L, 86L)), "C3 module sizes changed")
assert(length(unlist(cfg$outputs$declared_files)) == 36L,
       "Phase 15 must declare exactly 36 outputs")
unauthorized_cfg <- cfg
unauthorized_cfg$analysis$production_approved <- FALSE
authorization_error <- tryCatch({
  phase15_production_authorized(unauthorized_cfg)
  NULL
}, error = function(e) e)
assert(inherits(authorization_error, "error"),
       "Production authorization gate did not reject an unapproved configuration")
authorized_cfg <- cfg
authorized_cfg$analysis$production_approved <- TRUE

scores <- build_pilot_score_pairs(cfg, phase13, contexts)
assert(!anyDuplicated(scores$donor_context_id), "Donor/context score keys are duplicated")
assert(is.character(scores$projid), "projid must remain character")
assert(all(scores$nuclei >= 50L), "Pilot fixture should exercise the 50-nucleus path")
assert(all(vapply(split(scores$M[scores$diagnosis == "NCI"],
                        scores$context_id[scores$diagnosis == "NCI"]),
                  function(x) abs(mean(x)) < 1e-12 && abs(stats::sd(x) - 1) < 1e-12,
                  logical(1))), "M scores are not NCI standardized")

folds <- bind_rows(lapply(contexts$context_id, function(context_id)
  assign_crossfit_folds(scores, context_id, cfg)))
assert(validate_crossfit_leakage(folds), "Valid fold fixture failed leakage check")
leaky <- folds
duplicate <- leaky[1L, ]
duplicate$fold <- if (duplicate$fold == 5L) 1L else duplicate$fold + 1L
leaky <- rbind(leaky, duplicate)
assert(!validate_crossfit_leakage(leaky), "Deliberate NCI leakage was not rejected")

reference <- fit_nci_references(scores, "astrocytes", cfg)
assert(reference$success, paste("Known-valid NCI reference failed:",
                                reference$failure_reason))
assert(all(reference$models$heldout_training_overlap[
  reference$models$model_status == "estimated"
] == 0L), "Held-out donors appeared in reference training")

rank_fixture <- scores[scores$context_id == "astrocytes", ]
rank_fixture$sex_APOE_stratum <- "Female__e33"
rank_reference <- fit_nci_references(rank_fixture, "astrocytes", cfg)
assert(!rank_reference$success,
       "Rank-deficient reference fixture was not rejected")

groups <- unlist(phase13$groups)
astro <- scores[scores$context_id == "astrocytes", ]
level_model <- fit_hc3(astro$M - astro$N, build_level_design(astro, groups))
assert(level_model$success, paste("HC3 fixture failed:", level_model$failure_reason))
for (contrast in phase13$contrasts) {
  vector <- modifier_vector(contrast, names(level_model$beta), FALSE)
  inherited <- unlist(contrast$coefficients)
  observed <- vector[paste0("XG__", names(inherited))]
  assert(identical(as.numeric(observed), as.numeric(inherited)),
         paste("Incorrect modifier coefficient vector:", contrast$contrast_id))
}

manual_model <- stats::lm((M - N) ~ build_level_design(astro, groups) - 1,
                          data = astro)
manual_hc3 <- sandwich::vcovHC(manual_model, type = "HC3")
assert(isTRUE(all.equal(unname(level_model$covariance), unname(manual_hc3),
                        tolerance = 1e-12)),
       "HC3 covariance does not reproduce sandwich::vcovHC")

range_fixture <- astro[astro$group_id %in% unlist(phase13$contrasts[[1L]]$required_groups), ]
first_group <- unlist(phase13$contrasts[[1L]]$required_groups)[[1L]]
range_fixture$N[range_fixture$group_id == first_group] <-
  range_fixture$N[range_fixture$group_id == first_group] + 20
assert(range_overlap_fraction(range_fixture,
                              unlist(phase13$contrasts[[1L]]$required_groups)) == 0,
       "Predictor-range mismatch fixture was not detected")

assert(crossing_slope_flag(c(-1, -0.5, 0.2, 1)),
       "Crossing-slope fixture was not detected")
assert(!compatibility_pass(1, c(-1, 0, 1)),
       "Crossing slope incorrectly passed compatibility")
assert(compatibility_pass(1, c(0.2, 0.4, 0.6)),
       "Compatible slope fixture did not pass")
assert(!compatibility_pass(1, c(-0.2, -0.4, -0.6)),
       "Opposite endpoint directions incorrectly passed compatibility")

bh_fixture <- data.frame(family_id = c("a", "a", "b", "b"),
                         p_value = c(0.01, 0.04, 0.02, NA))
bh_observed <- apply_bh_families(bh_fixture)$q_value
assert(isTRUE(all.equal(bh_observed, c(0.02, 0.04, 0.02, NA_real_))),
       "Family-specific BH correction is incorrect")
assert(endpoint_status(0.01, 0.5, 0.2, 0.8, 0.25,
                       "eligible_confirmatory") == "supported",
       "Known supported endpoint status failed")
assert(endpoint_status(0.01, 0.5, 0.2, 0.8, 0.25,
                       "provisional_low_power") == "provisional_low_power",
       "Known provisional endpoint status failed")
assert(endpoint_status(0.8, 0.01, -0.1, 0.1, 0.25,
                       "eligible_confirmatory") == "not_supported_precise_null",
       "Known precise-null status failed")

worker_fixture <- phase15_worker_plan(list(max_total_cores = 8L,
                                            phase15_stability_workers = 6L))
assert(worker_fixture$effective >= 1L && worker_fixture$effective <= 6L,
       "Phase 15 worker resolution exceeded its limits")

phase13_production_dir <- file.path(
  root, "results/minerva_production/13_respiratory_modifier"
)
if (dir.exists(phase13_production_dir)) {
  invisible(validate_phase13_production_bundle(phase13_production_dir, cfg))
  production_contexts <- production_context_manifest(phase13, cfg)
  assert(nrow(production_contexts) == 7L,
         "Production must contain seven Phase 13 contexts")
  assert(sum(production_contexts$context_role == "primary_confirmatory") == 3L &&
           sum(production_contexts$context_role == "secondary_extension") == 4L,
         "Production context roles must remain three primary plus four secondary")
  production_scores <- load_phase13_production_scores(
    phase13_production_dir, production_contexts
  )
  assert(is.character(production_scores$projid) &&
           any(startsWith(production_scores$projid, "0")),
         "Production projid lost character type or leading zeroes")
  reconstruction_error <- reconstruct_phase13_score_error(
    phase13_production_dir, production_scores
  )
  assert(is.finite(reconstruction_error) && reconstruction_error <= 1e-8,
         "Stored Phase 13 scores do not reconstruct from validated inputs")
  production_analysis <- analyze_scores(
    production_scores, cfg, phase13, production_contexts, endpoints,
    "phase15_local_integration_test", production = TRUE
  )
  assert(nrow(production_analysis$results$general) == 21L &&
           nrow(production_analysis$results$modifier) == 147L &&
           nrow(production_analysis$results$strata) == 126L,
         "Production primary result dimensions changed")
  assert(all(production_analysis$endpoint_bundle$context_status$reference_success),
         "A production NCI cross-fit reference failed")
  assert(setequal(unique(production_analysis$results$general$family_id),
                  c(cfg$multiple_testing$families$general_primary,
                    cfg$multiple_testing$families$general_secondary)),
         "Primary and secondary general FDR families were not separated")
  production_inputs <- load_phase15_resampling_inputs(
    phase13_production_dir, production_contexts, phase13
  )
  astro_input <- production_inputs$astrocytes
  rebuilt <- rebuild_phase15_context_scores(
    astro_input, astro_input$samples$projid, astro_input$samples$projid
  )
  rebuilt_nci <- rebuilt$diagnosis == "NCI"
  assert(abs(mean(rebuilt$M[rebuilt_nci])) < 1e-10 &&
           abs(stats::sd(rebuilt$M[rebuilt_nci]) - 1) < 1e-10 &&
           abs(mean(rebuilt$N[rebuilt_nci])) < 1e-10 &&
           abs(stats::sd(rebuilt$N[rebuilt_nci]) - 1) < 1e-10,
         "Count-level production score rebuilding is not NCI standardized")
  production_grid <- build_phase15_production_prediction_grid(
    production_analysis$endpoint_bundle$data, phase13
  )
  assert(nrow(production_grid) > 0L &&
           all(production_grid$nuclear_score >= production_grid$common_range_low) &&
           all(production_grid$nuclear_score <= production_grid$common_range_high),
         "Production slope grid escaped the frozen common predictor range")
  assert(length(phase15_influence_definitions(production_inputs)) == 23L,
         "The frozen 13+5+1+4 influence analysis set changed")
}

if (!is.null(args$validate_output)) {
  number <- function(name) as.integer(args[[name]])
  validate_phase15_output(
    absolute_path(args$validate_output, root),
    number("expected_contexts"), number("expected_general_rows"),
    number("expected_modifier_rows"), number("expected_stratum_rows"),
    number("expected_general_gates"), number("expected_modifier_gates"),
    args$expected_status
  )
  cat("Phase 15 output validation passed: ", args$validate_output, "\n", sep = "")
} else {
  cat("Phase 15 synthetic, leakage, and HC3 unit tests passed\n")
}
