#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_test_cli <- function(args) {
  out <- list(
    validate_output = NULL, expected_contexts = NULL,
    expected_tests = NULL, expected_stratum_rows = NULL,
    expected_status = NULL
  )
  if (!length(args)) return(out)
  keys <- c(
    "--validate-output", "--expected-contexts", "--expected-tests",
    "--expected-stratum-rows", "--expected-status"
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

root <- normalizePath(getwd(), mustWork = TRUE)
source(file.path(root, "scripts/13_run_respiratory_modifier.R"), local = FALSE)
args <- parse_test_cli(commandArgs(trailingOnly = TRUE))
phase_cfg <- yaml::read_yaml(file.path(root, "config/phase13_respiratory_modifier.yml"))
members <- data.table::fread(
  file.path(root, "config/phase13_respiratory_modules.tsv"), data.table = FALSE
)

assert <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

assert(nrow(members) == 273L, "Module manifest must have 273 rows")
sizes <- table(factor(
  members$module_id,
  levels = vapply(phase_cfg$modules, function(x) x$module_id, character(1))
))
assert(identical(as.integer(sizes), c(13L, 86L, 155L, 19L)),
       "Module sizes are not 13/86/155/19")
assert("MRPL13" %in% members$frozen_gene_symbol,
       "MRPL13 is missing from translation")
assert(!"RPL13" %in% members$frozen_gene_symbol,
       "RPL13 must not be substituted for MRPL13")
assert(!anyDuplicated(members[c("module_id", "frozen_gene_symbol")]),
       "Module membership keys must be unique")
assert(all(members$mapping_status == "unique_assay_match"),
       "Every frozen membership must have a unique assay mapping")
legacy_assay_map <- c(
  DMAC2L = "ATP5S", GARS1 = "GARS", KARS1 = "KARS", MTRES1 = "C6orf203"
)
for (symbol in names(legacy_assay_map)) {
  observed <- unique(members$assay_feature_identifier[
    members$frozen_gene_symbol == symbol
  ])
  assert(identical(observed, unname(legacy_assay_map[[symbol]])),
         paste("Incorrect legacy assay mapping for", symbol))
}
assert(length(phase_cfg$contexts) == 7L, "Expected seven contexts")
assert(length(phase_cfg$contrasts) == 7L, "Expected seven contrasts")
assert(length(phase_cfg$groups) == 12L, "Expected twelve groups")

explicit_pseudobulk_root <- phase13_pseudobulk_root(
  list(
    inputs = list(phase13_pseudobulk_root = "results/07_pseudobulk"),
    outputs = list(root = "results/minerva_production")
  ),
  phase_cfg, "/project"
)
assert(identical(explicit_pseudobulk_root, "/project/results/07_pseudobulk"),
       "Explicit Phase 13 pseudobulk root was not respected")
fallback_pseudobulk_root <- phase13_pseudobulk_root(
  list(inputs = list(), outputs = list(root = "results/local_pilot")),
  phase_cfg, "/project"
)
assert(identical(
  fallback_pseudobulk_root, "/project/results/local_pilot/07_pseudobulk"
), "Default Phase 13 pseudobulk root did not follow the output stage")

separated_input_paths <- input_paths_for_source(
  "/project/results/minerva_production",
  "/project/results/07_pseudobulk",
  "astrocytes", "Astrocytes"
)
assert(identical(
  separated_input_paths$counts,
  "/project/results/07_pseudobulk/Astrocytes.pseudobulk_counts.rds"
), "Phase 07 counts did not use the explicit pseudobulk root")
assert(identical(
  separated_input_paths$qc,
  "/project/results/minerva_production/04_qc/astrocytes_cell_qc.tsv.gz"
), "Phase 04 QC did not remain under the production stage root")



assert(is.na(scheduler_core_limit(c(PATH = "/usr/bin"))),
       "Missing scheduler variables must not fail core detection")
assert(scheduler_core_limit(c(LSB_DJOB_NUMPROC = "8")) == 8L,
       "LSF core allocation was not detected")

worker_fixture <- resolve_stability_workers(
  list(max_total_cores = 48L, phase13_stability_workers = 32L),
  available_cores = 24L, scheduler_cores = 16L, os_type = "unix"
)
assert(worker_fixture$effective == 16L,
       "Stability workers must respect the scheduler allocation")
assert(worker_fixture$backend == "fork", "Unix multicore backend must use fork")
sequential_worker_fixture <- resolve_stability_workers(
  list(max_total_cores = 48L, phase13_stability_workers = 32L),
  available_cores = 24L, scheduler_cores = 16L, os_type = "windows"
)
assert(sequential_worker_fixture$effective == 1L,
       "Non-Unix stability execution must fall back to one worker")

parallel_fixture_fun <- function(repetition) {
  seed <- seed_for(phase_cfg, paste0("parallel-fixture::", repetition))
  set.seed(seed)
  data.frame(repetition = repetition, seed = seed, value = stats::runif(1))
}
parallel_fixture_tasks <- as.list(seq_len(8L))
parallel_fixture_serial <- parallel_lapply_ordered(
  parallel_fixture_tasks, parallel_fixture_fun, workers = 1L, label = "test serial"
)
parallel_fixture_multicore <- parallel_lapply_ordered(
  parallel_fixture_tasks, parallel_fixture_fun, workers = 2L, label = "test multicore"
)
assert(identical(parallel_fixture_serial, parallel_fixture_multicore),
       "Parallel scheduling changed seeded results or task order")

design_names <- c(unlist(phase_cfg$groups), "age_death_scaled", "pmi_scaled", "studyROS")
for (contrast in phase_cfg$contrasts) {
  vector <- contrast_vector(contrast, design_names)
  assert(identical(
    as.numeric(vector[unlist(contrast$required_groups)]), c(1, -1, -1, 1)
  ), paste("Incorrect coefficient vector:", contrast$contrast_id))
}

groups <- unlist(phase_cfg$groups)
fixture <- do.call(rbind, lapply(seq_along(groups), function(i) {
  n <- 6L
  centered_age <- c(-0.15, -0.09, -0.03, 0.03, 0.09, 0.15)
  centered_pmi <- c(-0.20, 0.10, 0.05, 0.15, -0.05, -0.05)
  centered_noise <- c(-0.12, 0.03, 0.07, 0.08, -0.10, 0.04)
  data.frame(
    projid = sprintf("fixture_%02d_%02d", i, seq_len(n)),
    donor_context_id = sprintf("fixture::%02d_%02d", i, seq_len(n)),
    group_id = groups[[i]],
    diagnosis = strsplit(groups[[i]], "__", fixed = TRUE)[[1L]][[1L]],
    sex = strsplit(groups[[i]], "__", fixed = TRUE)[[1L]][[2L]],
    apoe_group = strsplit(groups[[i]], "__", fixed = TRUE)[[1L]][[3L]],
    age_death_scaled = centered_age,
    pmi_scaled = centered_pmi,
    study = rep(c("MAP", "ROS"), 3L),
    aggregate_percent_mt = 1 + seq_len(n) / 100,
    robust_qc_fraction = seq_len(n) / 100,
    nuclei = 100L,
    noise = centered_noise + rep(c(-0.01, 0.01), 3L),
    stringsAsFactors = FALSE
  )
}))
positive <- fixture$noise
positive[fixture$group_id == "AD__Female__e33"] <-
  positive[fixture$group_id == "AD__Female__e33"] + 1
positive_fit <- fit_score_outcome(
  positive, fixture, phase_cfg, contrast = phase_cfg$contrasts[[2L]]
)
assert(isTRUE(positive_fit$success), "Known-positive HC3 fixture did not fit")
assert(abs(positive_fit$estimate - 1) < 1e-10,
       "Known-positive interaction was not recovered")

null_fit <- fit_score_outcome(
  fixture$noise, fixture, phase_cfg, contrast = phase_cfg$contrasts[[6L]]
)
assert(isTRUE(null_fit$success), "Known-null HC3 fixture did not fit")
assert(abs(null_fit$estimate) < 1e-10, "Known-null interaction was not recovered")

rank_fixture <- fixture
rank_fixture$pmi_scaled <- rank_fixture$age_death_scaled
rank_design <- build_design(rank_fixture, groups)
assert(qr(rank_design)$rank < ncol(rank_design),
       "Synthetic rank-failure fixture did not fail rank")

z <- rbind(
  gene_a = c(-2, -1, 1, 2, -1.8, -0.8, 1.2, 2.2),
  gene_b = c(-1.9, -0.9, 0.9, 1.9, -1.7, -0.7, 1.1, 2.1),
  gene_c = c(-2.1, -1.1, 1.1, 2.1, -1.9, -0.9, 1.3, 2.3)
)
pc <- pc1_scores(z, 1:4, Matrix::colMeans(z))
assert(isTRUE(pc$success), "PC1 fixture failed")
assert(pc$correlation >= 0, "PC1 orientation must be nonnegative")

coverage_norm <- list(
  all_genes = paste0("g", 1:6),
  tested_genes = paste0("g", 1:3),
  y = list(counts = matrix(1, nrow = 3, ncol = 8,
                           dimnames = list(paste0("g", 1:3), NULL))),
  logcpm = rbind(
    g1 = c(1, 1, 1, 1, 2, 2, 2, 2),
    g2 = c(1, 2, 1, 2, 2, 3, 2, 3),
    g3 = c(2, 3, 2, 3, 3, 4, 3, 4)
  ),
  samples = data.frame(
    diagnosis = c(rep("NCI", 4), rep("AD", 4)),
    donor_context_id = paste0("c::", 1:8), projid = as.character(1:8),
    group_id = rep(c("NCI__Female__e33", "AD__Female__e33"), each = 4),
    sex = "Female", apoe_group = "e33", stringsAsFactors = FALSE
  )
)
coverage_members <- data.frame(
  module_id = "synthetic", frozen_gene_symbol = paste0("G", 1:6),
  assay_feature_identifier = paste0("g", 1:6), stringsAsFactors = FALSE
)
coverage_cfg <- list(
  module_id = "synthetic", minimum_fraction = 0.70, minimum_genes = 5L
)
coverage_result <- score_one_module(
  coverage_norm, coverage_members, coverage_cfg, "synthetic_context"
)
assert(!isTRUE(coverage_result$success),
       "Synthetic module coverage failure was not detected")
assert("G1" %in% strsplit(
  coverage_result$coverage$zero_variance_genes, "|", fixed = TRUE
)[[1L]], "Synthetic zero-variance gene was not reported")

p <- c(0.001, 0.02, 0.7, NA)
q <- rep(NA_real_, length(p))
q[is.finite(p)] <- p.adjust(p[is.finite(p)], method = "BH")
assert(isTRUE(all.equal(q[1:3], c(0.003, 0.03, 0.7))),
       "BH fixture failed")

primary_fixture <- data.frame(
  test_id = "c::x::m", context_id = "c", contrast_id = "x", module_id = "m",
  estimate = 1, eligibility_status = "eligible", stringsAsFactors = FALSE
)
replicate_fixture <- data.frame(
  test_id = rep("c::x::m", 3), context_id = "c", contrast_id = "x",
  module_id = "m", analysis_type = "leave_one_donor_out",
  repetition = 1:3, seed = NA_integer_,
  omitted_donor = c("ordinary1", "influential", "ordinary2"),
  omitted_unit = "", sampled_donors = "",
  estimate = c(0.9, -0.2, 0.8), standard_error = 0.1,
  fit_success = TRUE, failure_reason = "", stringsAsFactors = FALSE
)
summary_fixture <- summarize_stability(
  primary_fixture, replicate_fixture, phase_cfg, TRUE, c(c = 3L)
)
assert(summary_fixture$loo_largest_change_donor == "influential",
       "Influential-donor fixture failed")
assert(summary_fixture$loo_sign_reversals == 1L,
       "Leave-one-donor sign reversal fixture failed")

if (!is.null(args$validate_output)) {
  required <- c(
    "expected_contexts", "expected_tests", "expected_stratum_rows", "expected_status"
  )
  missing <- required[vapply(args[required], is.null, logical(1))]
  if (length(missing)) {
    stop("Output validation is missing: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  validate_phase13_output(
    args$validate_output,
    as.integer(args$expected_contexts),
    as.integer(args$expected_tests),
    as.integer(args$expected_stratum_rows),
    args$expected_status,
    unlist(phase_cfg$outputs$declared_files)
  )
  cat("Phase 13 output validation passed: ", args$validate_output, "\n", sep = "")
} else {
  cat("Phase 13 synthetic/unit tests passed\n")
}
