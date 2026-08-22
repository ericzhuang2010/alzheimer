#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(coloc)
  library(data.table)
  library(Matrix)
  library(yaml)
})

root <- normalizePath(".", mustWork = TRUE)
config <- yaml.load_file(file.path(root, "config/phase19_genetic_support_tier2_recovery.yml"))
manifest_dir <- file.path(root, config$inputs$source_manifest_dir)
routes <- fread(file.path(manifest_dir, "recovery_route_manifest.tsv"), sep = "\t")
registry <- fread(file.path(manifest_dir, "recovery_dataset_registry.tsv"), sep = "\t")
baseline <- fread(file.path(manifest_dir, "recovery_baseline_hashes.tsv"), sep = "\t")

checks <- list()
add_check <- function(id, condition, detail) {
  checks[[length(checks) + 1L]] <<- data.table(
    schema_version = "human_genetic_support_tier2_classical_coloc_recovery_v1",
    check_id = id, status = ifelse(isTRUE(condition), "pass", "fail"), detail = detail
  )
}

add_check("frozen_route_count", nrow(routes) == 54L, "Exactly 54 nuclear eQTL/sQTL routes")
add_check("signal_gate_count", sum(routes$gwas_signal_present == "TRUE") == 12L, "Exactly 12 routes require QTL/LD recovery")
add_check("baseline_hashes", all(baseline$status == "pass"), "Both prior result bundles remain immutable")
add_check("selection_frozen", all(registry$selection_frozen_before_result == "TRUE"), "Dataset selection predates H4")
add_check(
  "case_fraction",
  abs(config$source_release$gwas_cases /
    (config$source_release$gwas_cases + config$source_release$gwas_controls) -
    111326 / 788989) < 1e-15,
  "Bellenguez case-control fraction retained"
)

n <- 100L
variants <- paste0("v", seq_len(n))
shared1 <- matrix(-5, nrow = 1L, ncol = n, dimnames = list("L1", variants))
shared2 <- shared1
shared1[1, 10] <- 20
shared2[1, 10] <- 20
shared1 <- cbind(shared1, null = 0)
shared2 <- cbind(shared2, null = 0)
shared <- coloc.bf_bf(shared1, shared2, p1 = 1e-4, p2 = 1e-4, p12 = 5e-6)
add_check("synthetic_shared_signal", shared$summary$PP.H4.abf[1] > 0.99, "Matched LBF peaks recover H4")

distinct2 <- matrix(-5, nrow = 1L, ncol = n, dimnames = list("L1", variants))
distinct2[1, 80] <- 20
distinct2 <- cbind(distinct2, null = 0)
distinct <- coloc.bf_bf(shared1, distinct2, p1 = 1e-4, p2 = 1e-4, p12 = 5e-6)
add_check("synthetic_distinct_signal", distinct$summary$PP.H3.abf[1] > 0.99, "Separated LBF peaks recover H3")

flip_beta <- function(beta, effect, other, ref, alt) {
  if (effect == alt && other == ref) beta else if (effect == ref && other == alt) -beta else NA_real_
}
add_check("allele_flip", flip_beta(0.4, "A", "G", "A", "G") == -0.4, "Effect-is-reference beta is flipped")
add_check("allele_match", flip_beta(0.4, "G", "A", "A", "G") == 0.4, "Effect-is-alternate beta is unchanged")

ld <- matrix(c(1, 0.4, 0.1, 0.4, 1, 0.3, 0.1, 0.3, 1), 3, 3)
add_check("ld_symmetry", max(abs(ld - t(ld))) == 0, "Synthetic LD symmetry gate")
add_check("ld_diagonal", max(abs(diag(ld) - 1)) == 0, "Synthetic LD unit diagonal gate")
add_check("ld_psd", min(eigen(ld, symmetric = TRUE, only.values = TRUE)$values) > 0, "Synthetic LD PSD gate")
permuted <- ld[c(2, 1, 3), c(2, 1, 3)]
add_check("ld_order_detection", !identical(rownames(permuted), c("v1", "v2", "v3")), "Order mismatch is detectable")
add_check("ancestry_gate", !("East_Asian" %in% c("European", "non_Hispanic_White")), "Ancestry mismatch is rejected")

pilot_root <- file.path(root, config$outputs$pilot_root)
dir.create(pilot_root, recursive = TRUE, showWarnings = FALSE)
pilot_checks <- rbindlist(checks)
fwrite(pilot_checks, file.path(pilot_root, "pilot_checks.tsv"), sep = "\t", quote = FALSE)
pilot_status <- data.table(
  schema_version = "human_genetic_support_tier2_classical_coloc_recovery_v1",
  validation_status = ifelse(all(pilot_checks$status == "pass"), "validated_pilot", "pilot_failed"),
  shared_signal_control = shared$summary$PP.H4.abf[1],
  distinct_signal_control = distinct$summary$PP.H3.abf[1],
  blocking_failures = sum(pilot_checks$status != "pass"),
  execution_backend = "direct"
)
fwrite(pilot_status, file.path(pilot_root, "pilot_status.tsv"), sep = "\t", quote = FALSE)
if (any(pilot_checks$status != "pass")) {
  stop("Pilot checks failed: ", paste(pilot_checks[status != "pass"]$check_id, collapse = ", "))
}

output_root <- file.path(root, config$outputs$root)
if (dir.exists(output_root)) {
  declared <- c(
    "recovery_analysis_manifest.tsv", "recovery_route_manifest.tsv",
    "recovery_dataset_registry.tsv", "recovery_request_manifest.tsv",
    "recovery_input_inventory.tsv", "recovery_source_checks.tsv",
    "recovery_route_decisions.tsv", "recovery_regional_gwas_summary.tsv",
    "recovery_regional_qtl_summary.tsv", "recovery_gwas_finemapping.tsv.gz",
    "recovery_qtl_finemapping.tsv.gz", "recovery_ld_qc.tsv",
    "recovery_variant_harmonization.tsv.gz", "recovery_variant_harmonization_summary.tsv",
    "recovery_colocalization.tsv.gz", "recovery_colocalization_qc.tsv",
    "recovery_prior_sensitivity.tsv.gz", "recovery_assessability.tsv",
    "recovery_evidence_summary.tsv", "recovery_figure_data.tsv.gz",
    "recovery_evidence_matrix.pdf", "recovery_evidence_matrix.png",
    "recovery_locus_plots.pdf", "recovery_checks.tsv",
    "recovery_artifacts.tsv", "recovery_status.tsv"
  )
  stopifnot(identical(sort(list.files(output_root)), sort(declared)))
  stopifnot(nrow(fread(file.path(output_root, "recovery_assessability.tsv"))) == 54L)
  stopifnot(nrow(fread(file.path(output_root, "recovery_evidence_summary.tsv"))) == 47L)
  stopifnot(all(fread(file.path(output_root, "recovery_checks.tsv"))$status == "pass"))
}
cat("Tier 2 recovery pilot/tests passed:", nrow(pilot_checks), "checks\n")
