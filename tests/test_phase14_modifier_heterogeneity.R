#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_test_cli <- function(args) {
  out <- list(
    validate_output = NULL, expected_contexts = NULL, expected_pairs = NULL,
    expected_omnibus_rows = NULL, expected_pairwise_rows = NULL,
    expected_context_modifier_rows = NULL, expected_stratum_rows = NULL,
    expected_status = NULL
  )
  keys <- c(
    "--validate-output", "--expected-contexts", "--expected-pairs",
    "--expected-omnibus-rows", "--expected-pairwise-rows",
    "--expected-context-modifier-rows", "--expected-stratum-rows",
    "--expected-status"
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
source(file.path(root, "scripts/14_run_modifier_heterogeneity.R"), local = FALSE)
args <- parse_test_cli(commandArgs(trailingOnly = TRUE))

required <- c("yaml", "data.table", "nlme", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing required packages: ", paste(missing, collapse = ", "),
                          call. = FALSE)

phase_cfg <- yaml::read_yaml(file.path(root, "config/phase14_modifier_heterogeneity.yml"))
phase13 <- yaml::read_yaml(file.path(root, "config/phase13_respiratory_modifier.yml"))
members <- data.table::fread(file.path(root, "config/phase13_respiratory_modules.tsv"),
                             data.table = FALSE)

contexts <- context_manifest_from_phase13(phase13, unlist(phase_cfg$pilot$contexts))
pairs <- pair_manifest(contexts)
contrasts <- contrast_manifest_from_phase13(phase13)
modules <- module_manifest_from_phase13(phase13)

assert(nrow(contexts) == 3L, "Pilot must use exactly three contexts")
assert(identical(contexts$context_id,
                 c("astrocytes", "excitatory_neurons", "vasculature")),
       "Pilot context order changed")
assert(nrow(pairs) == 3L && !anyDuplicated(pairs$pair_id),
       "Three contexts must yield three unique unordered pairs")
assert(nrow(contrasts) == 7L, "Expected seven inherited modifiers")
assert(nrow(modules) == 4L, "Expected four inherited modules")
assert(nrow(members) == 273L, "Expected all 273 frozen module memberships")
assert(identical(as.integer(table(factor(
  members$module_id, levels = modules$module_id
))), c(13L, 86L, 155L, 19L)), "Frozen module sizes changed")
assert(length(unlist(phase_cfg$outputs$declared_files)) == 31L,
       "Phase 14 must declare exactly 31 output files")
assert(!isTRUE(phase_cfg$analysis$production_approved),
       "Local-pilot approval must not authorize production")

coefficient_names <- c(
  as.vector(outer(contexts$context_id, unlist(phase13$groups),
                  function(context, group) paste0("context_group", context, "::", group))),
  "age_death_scaled", "pmi_scaled", "studyROS"
)
for (contrast in phase13$contrasts) {
  vector <- context_contrast_vector(contrast, "astrocytes", coefficient_names)
  inherited <- unlist(contrast$coefficients)
  observed <- vector[paste0("context_groupastrocytes::", names(inherited))]
  assert(identical(as.numeric(observed), as.numeric(inherited)),
         paste("Incorrect inherited contrast vector:", contrast$contrast_id))
}

beta <- setNames(seq_along(coefficient_names) / 10, coefficient_names)
covariance <- diag(length(beta))
dimnames(covariance) <- list(names(beta), names(beta))
known <- context_contrast_vector(phase13$contrasts[[2L]], "astrocytes", names(beta))
known_test <- linear_test(beta, covariance, known)
assert(known_test$success && is.finite(known_test$estimate),
       "Known linear contrast did not evaluate")
singular <- wald_test(beta, covariance,
                      rbind(known, known))
assert(!singular$success && singular$failure_reason == "singular_omnibus_covariance",
       "Singular omnibus covariance was not rejected")

bh_fixture <- data.frame(p_value = c(0.01, 0.04, NA, 0.03))
bh_observed <- apply_bh(bh_fixture)$q_value
bh_expected <- c(stats::p.adjust(c(0.01, 0.04, 0.03), method = "BH")[c(1, 2)],
                 NA_real_, stats::p.adjust(c(0.01, 0.04, 0.03), method = "BH")[[3L]])
assert(isTRUE(all.equal(bh_observed, bh_expected)),
       "BH correction did not preserve the structural NA row")

profiles <- build_pilot_profiles(phase_cfg, phase13, contexts, modules)
assert(nrow(profiles) < length(unique(profiles$projid)) * 3L * 4L,
       "Synthetic fixture does not contain missing contexts")
score_bundle <- build_common_scores(profiles, members, phase_cfg, modules, contexts)
assert(nrow(score_bundle$scores) == nrow(profiles),
       "Common score construction changed the profile grid")
assert(all(is.finite(score_bundle$scores$common_score)),
       "Common score fixture contains nonfinite values")
assert(all(score_bundle$scores$pc1_mean_z_correlation >= 0),
       "PC1 scores were not deterministically oriented")
coverage <- setNames(score_bundle$modules$common_coverage_pass,
                     score_bundle$modules$module_id)
assert(all(coverage[c("mtdna_oxphos_13", "nuclear_oxphos_structural_86",
                      "mitochondrial_translation_155")]),
       "Three intended pilot modules must pass common coverage")
assert(!coverage[["mib_micos_inner_membrane_19"]],
       "MIB/MICOS fixture must fail all-context common coverage")

low_contrast <- phase13$contrasts[[1L]]
low_counts <- paired_group_counts(score_bundle$scores, low_contrast,
                                  "astrocytes", "excitatory_neurons")
assert(any(low_counts < 5L), "Low paired-donor fixture was not created")

small_groups <- unlist(phase13$groups)
model_fixture <- score_bundle$scores[
  score_bundle$scores$module_id == "mtdna_oxphos_13", ]
model_fit <- fit_joint_model(model_fixture, contexts$context_id, small_groups)
assert(model_fit$success, paste("Known-positive mixed-model fixture failed:",
                                model_fit$failure_reason))
v_astro <- context_contrast_vector(phase13$contrasts[[2L]], "astrocytes",
                                   names(model_fit$beta))
v_excitatory <- context_contrast_vector(phase13$contrasts[[2L]],
                                        "excitatory_neurons", names(model_fit$beta))
positive <- linear_test(model_fit$beta, model_fit$covariance,
                        v_astro - v_excitatory)
assert(positive$success && positive$estimate > 0.5,
       "Known positive heterogeneity was not recovered")

worker_fixture <- phase14_worker_plan(list(
  max_total_cores = 8L, phase14_stability_workers = 6L
))
assert(worker_fixture$effective >= 1L && worker_fixture$effective <= 6L,
       "Phase 14 worker resolution exceeded its limits")

if (!is.null(args$validate_output)) {
  numeric_value <- function(name) as.integer(args[[name]])
  validate_phase14_output(
    absolute_path(args$validate_output, root),
    numeric_value("expected_contexts"), numeric_value("expected_pairs"),
    numeric_value("expected_omnibus_rows"), numeric_value("expected_pairwise_rows"),
    numeric_value("expected_context_modifier_rows"), numeric_value("expected_stratum_rows"),
    args$expected_status
  )
  cat("Phase 14 output validation passed: ", args$validate_output, "\n", sep = "")
} else {
  cat("Phase 14 synthetic and unit tests passed\n")
}
