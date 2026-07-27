#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

kda_dir <- dirname(normalizePath(
  sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1L]),
  winslash = "/", mustWork = TRUE
))
source(file.path(kda_dir, "lib", "cli.R"))
source_kda_libraries(kda_dir)

usage <- paste(
  "Usage:",
  "  Rscript scripts/analysis/kda/prepare_kda_inputs.R [options]",
  "",
  "Options:",
  "  --phase08-dir DIR          Default: results/minerva_production/08_mast",
  "  --annotation-dir DIR       Default: results/minerva_production/09_annotate_genes",
  "  --network-root DIR         Default: data/bayesian_network",
  "  --output-dir DIR           Default: results/minerva_production/12_kda/inputs",
  "  --query-universe NAME      core_mito (primary) or all_mito_related",
  "  --force                    Replace incompatible/partial known outputs",
  "  --help, -h                 Show this help",
  sep = "\n"
)

network_id_for <- function(rds_id, fine_cell_type) {
  if (identical(rds_id, "astrocytes") && startsWith(fine_cell_type, "Ast")) {
    return("Astrocytes")
  }
  if (startsWith(rds_id, "excitatory_set") && startsWith(fine_cell_type, "Exc")) {
    return("Excitatory_neurons")
  }
  if (identical(rds_id, "inhibitory") && startsWith(fine_cell_type, "Inh")) {
    return("Inhibitory_neurons")
  }
  if (identical(rds_id, "opcs") && identical(fine_cell_type, "OPC")) {
    return("OPCs")
  }
  if (identical(rds_id, "oligodendrocytes") && identical(fine_cell_type, "Oli")) {
    return("Oligodendrocytes")
  }
  if (identical(rds_id, "vasculature") &&
      fine_cell_type %in% c("End", "Fib FLRT2", "Fib SLC4A4", "Per", "SMC")) {
    return("Vasculature_cells")
  }
  if (identical(rds_id, "immune") && identical(fine_cell_type, "CAMs")) {
    return("CAMs")
  }
  if (identical(rds_id, "immune") && startsWith(fine_cell_type, "Mic ")) {
    return("Microglia")
  }
  if (identical(rds_id, "immune") && identical(fine_cell_type, "T cells")) {
    return("T_cells")
  }
  kda_abort(
    "No audited broad-network mapping exists for rds_id='%s', fine_cell_type='%s'.",
    rds_id,
    fine_cell_type
  )
}

query_directions <- list(
  all_mito = function(table) rep(TRUE, nrow(table)),
  AD_up_mito = function(table) table$logFC > 0,
  AD_down_mito = function(table) table$logFC < 0
)

arguments <- commandArgs(trailingOnly = TRUE)
if ("-h" %in% arguments) {
  cat(usage, "\n")
  quit(save = "no", status = 0L)
}
cli <- parse_kda_cli(
  arguments,
  value_options = c(
    "phase08-dir", "annotation-dir", "network-root",
    "output-dir", "query-universe"
  ),
  flag_options = "force",
  defaults = list(
    "phase08-dir" = "results/minerva_production/08_mast",
    "annotation-dir" = "results/minerva_production/09_annotate_genes",
    "network-root" = "data/bayesian_network",
    "output-dir" = "results/minerva_production/12_kda/inputs",
    "query-universe" = "core_mito",
    force = FALSE
  ),
  usage = usage
)
project_root <- find_project_root(kda_dir)
phase08_dir <- resolve_project_path(cli[["phase08-dir"]], project_root)
annotation_dir <- resolve_project_path(cli[["annotation-dir"]], project_root)
network_root <- resolve_project_path(cli[["network-root"]], project_root)
output_dir <- resolve_project_path(cli[["output-dir"]], project_root)
query_universe <- cli[["query-universe"]]
mito_tiers <- switch(
  query_universe,
  core_mito = "core_mito_protein",
  all_mito_related = c("core_mito_protein", "mito_extended", "mtdna_noncoding"),
  kda_abort("--query-universe must be 'core_mito' or 'all_mito_related'.")
)
require_kda_packages()

phase08_files <- sort(
  Sys.glob(file.path(phase08_dir, "*.yu_mast_de.tsv.gz")),
  method = "radix"
)
if (length(phase08_files) != 9L) {
  kda_abort("Expected nine Phase 08 MAST result files; found %d in %s.",
            length(phase08_files), phase08_dir)
}
status_files <- sort(
  Sys.glob(file.path(phase08_dir, "*.yu_mast_contrast_status.tsv")),
  method = "radix"
)
if (length(status_files) != 9L) {
  kda_abort("Expected nine Phase 08 contrast-status files; found %d.", length(status_files))
}
for (status_path in status_files) {
  status <- read_tsv(status_path)
  if (!"terminal_status" %in% names(status) ||
      any(!status$terminal_status %in% c("validated_complete", "not_estimable"))) {
    kda_abort("Phase 08 status is not fully validated/explicitly non-estimable: %s", status_path)
  }
}

annotation_master_path <- file.path(annotation_dir, "gene_annotation_master.tsv.gz")
annotation_status_path <- file.path(annotation_dir, "annotation_status.tsv")
annotation_artifacts_path <- file.path(annotation_dir, "annotation_artifacts.tsv")
annotation_status <- read_tsv(annotation_status_path)
if (!"validation_status" %in% names(annotation_status) ||
    nrow(annotation_status) != 1L ||
    !identical(annotation_status$validation_status[[1L]], "validated_complete")) {
  kda_abort("Phase 09 annotation status is not validated_complete.")
}
annotation_artifacts <- read_tsv(annotation_artifacts_path)
artifact_row <- annotation_artifacts[artifact == "gene_annotation_master.tsv.gz"]
if (nrow(artifact_row) != 1L ||
    !identical(artifact_row$validation_status[[1L]], "validated_complete")) {
  kda_abort("Phase 09 artifact manifest lacks one validated annotation-master row.")
}
if (!identical(sha256_file(annotation_master_path), artifact_row$sha256[[1L]])) {
  kda_abort("Phase 09 gene_annotation_master.tsv.gz checksum does not match its artifact manifest.")
}

network_paths <- file.path(
  network_root,
  c(
    "Astrocytes", "CAMs", "Excitatory_neurons", "Inhibitory_neurons",
    "Microglia", "OPCs", "Oligodendrocytes", "T_cells", "Vasculature_cells"
  ),
  "result.links3.links.txt"
)
names(network_paths) <- basename(dirname(network_paths))
missing_networks <- network_paths[!file.exists(network_paths)]
if (length(missing_networks)) {
  kda_abort("Missing Bayesian network file(s): %s", paste(missing_networks, collapse = ", "))
}
network_node_sets <- lapply(network_paths, function(path) network_nodes(read_network_file(path)))

expected <- list(
  analysis_type = "prepare_kda_inputs",
  query_universe = query_universe,
  annotation_master_sha256 = sha256_file(annotation_master_path),
  phase08_sha256 = paste(vapply(phase08_files, sha256_file, character(1L)), collapse = ";"),
  networks_sha256 = paste(vapply(network_paths, sha256_file, character(1L)), collapse = ";")
)
preparation_manifest_path <- file.path(output_dir, "run_manifest.json")
expected_output_paths <- c(
  file.path(output_dir, "kda_run_manifest.tsv"),
  file.path(output_dir, "signature_members.tsv.gz"),
  file.path(output_dir, "background_members.tsv.gz"),
  file.path(output_dir, "query_gene_diagnostics.tsv.gz"),
  file.path(output_dir, "kda_query_qc.tsv")
)
if (assert_compatible_completed_run(
  preparation_manifest_path, expected, isTRUE(cli$force), "KDA input preparation"
)) {
  missing_outputs <- expected_output_paths[!file.exists(expected_output_paths)]
  if (length(missing_outputs)) {
    kda_abort("Completed preparation manifest is missing output(s): %s",
              paste(missing_outputs, collapse = ", "))
  }
  cat("Reused compatible prepared KDA inputs in", output_dir, "\n")
  quit(save = "no", status = 0L)
}
if (!isTRUE(cli$force) &&
    (dir.exists(output_dir) && length(list.files(output_dir, all.files = TRUE,
                                                no.. = TRUE)))) {
  kda_abort("Output directory is nonempty without a compatible manifest; use --force or a new directory: %s",
            output_dir)
}

annotation <- read_tsv(
  annotation_master_path,
  select = c(
    "rds_id", "feature_id_original", "reference_only", "mito_tier",
    "symbol_hgnc_current", "mapping_status"
  )
)
annotation <- annotation[reference_only == FALSE]
if (anyDuplicated(annotation[, .(rds_id, feature_id_original)])) {
  kda_abort("Phase 09 annotation master has duplicate assay-feature keys.")
}
data.table::setnames(annotation, "feature_id_original", "gene")
data.table::setkey(annotation, rds_id, gene)

manifest_rows <- list()
signature_rows <- list()
background_rows <- list()
diagnostic_rows <- list()
qc_rows <- list()
row_index <- 0L
started <- Sys.time()

for (phase08_path in phase08_files) {
  kda_message("Preparing KDA queries from %s", basename(phase08_path))
  mast <- read_tsv(
    phase08_path,
    select = c(
      "rds_id", "contrast_id", "cell_type_high_resolution", "sex",
      "apoe_group", "contrast_family", "contrast_name", "gene", "logFC",
      "pct_ad", "pct_nci", "fdr_bh_within_contrast",
      "paper_effect_threshold_log2", "paper_deg"
    )
  )
  mast <- mast[contrast_family == "AD_vs_NCI"]
  if (!nrow(mast)) next
  if (any(is.na(mast$gene) | !nzchar(trimws(mast$gene)))) {
    kda_abort("Phase 08 file contains missing/blank gene identifiers: %s", phase08_path)
  }
  mast[, gene := trimws(gene)]
  mast <- annotation[mast, on = .(rds_id, gene)]
  if (any(is.na(mast$mito_tier))) {
    kda_abort("Phase 08 genes failed to map uniquely into the Phase 09 annotation master.")
  }

  contrast_ids <- unique(mast$contrast_id)
  for (contrast_id in contrast_ids) {
    current_contrast_id <- contrast_id
    contrast <- mast[contrast_id == current_contrast_id]
    metadata_columns <- c(
      "rds_id", "cell_type_high_resolution", "sex", "apoe_group",
      "contrast_family", "contrast_name"
    )
    metadata <- unique(contrast[, ..metadata_columns])
    if (nrow(metadata) != 1L) {
      kda_abort("Contrast has inconsistent metadata: %s", contrast_id)
    }
    network_id <- network_id_for(
      metadata$rds_id[[1L]], metadata$cell_type_high_resolution[[1L]]
    )
    nodes <- network_node_sets[[network_id]]
    background <- intersect(unique(contrast$gene), nodes)
    mitochondrial_degs <- contrast[
      paper_deg == TRUE & mito_tier %in% mito_tiers
    ]

    for (direction in names(query_directions)) {
      row_index <- row_index + 1L
      direction_rows <- mitochondrial_degs[
        query_directions[[direction]](mitochondrial_degs)
      ]
      original_query <- sort(unique(direction_rows$gene), method = "radix")
      effective_query <- intersect(original_query, background)
      eligible <- length(effective_query) >= 3L
      skip_reason <- if (eligible) "" else "effective_query_lt_3"
      run_id <- safe_path_component(paste(
        metadata$rds_id[[1L]],
        metadata$cell_type_high_resolution[[1L]],
        metadata$sex[[1L]],
        metadata$apoe_group[[1L]],
        query_universe,
        direction,
        sep = "__"
      ))
      network_path <- network_paths[[network_id]]
      signature_output <- file.path(output_dir, "signature_members.tsv.gz")
      background_output <- file.path(output_dir, "background_members.tsv.gz")
      manifest_rows[[row_index]] <- data.table::data.table(
        schema_version = "kda_run_manifest_v1",
        run_id = run_id,
        contrast_id = contrast_id,
        network_id = network_id,
        network_path = project_relative_path(network_path, project_root),
        fine_cell_type = metadata$cell_type_high_resolution[[1L]],
        sex = metadata$sex[[1L]],
        apoe_group = metadata$apoe_group[[1L]],
        comparison = metadata$contrast_family[[1L]],
        query_direction = direction,
        query_universe = query_universe,
        mitochondrial_tiers = paste(mito_tiers, collapse = ";"),
        signature_path = project_relative_path(signature_output, project_root),
        background_path = project_relative_path(background_output, project_root),
        query_definition_version = "phase08_paper_deg_original_gene_v1",
        background_definition_version = "phase08_returned_gene_intersect_network_v1",
        identifier_policy = "phase08_gene_original",
        deg_fdr_rule = "fdr_bh_within_contrast < 0.05",
        deg_effect_rule = "abs(logFC) > log2(1.3)",
        deg_detection_rule = "pct_ad >= 0.10 OR pct_nci >= 0.10",
        query_size_original = length(original_query),
        query_size_effective = length(effective_query),
        query_genes_unmapped = paste(setdiff(original_query, background), collapse = ";"),
        background_size = length(background),
        eligible = eligible,
        skip_reason = skip_reason
      )
      if (length(effective_query)) {
        signature_rows[[row_index]] <- data.table::data.table(
          run_id = run_id,
          gene = effective_query
        )
      }
      background_rows[[row_index]] <- data.table::data.table(
        run_id = run_id,
        gene = background
      )
      if (nrow(direction_rows)) {
        diagnostic_rows[[row_index]] <- unique(direction_rows[, .(
          run_id = run_id,
          gene,
          symbol_hgnc_current,
          mapping_status,
          mito_tier,
          logFC,
          fdr_bh_within_contrast,
          paper_deg,
          in_network_background = gene %in% background
        )])
      }
      qc_rows[[row_index]] <- data.table::data.table(
        run_id = run_id,
        contrast_id = contrast_id,
        network_id = network_id,
        query_size_original = length(original_query),
        query_size_effective = length(effective_query),
        query_genes_unmapped = paste(setdiff(original_query, background), collapse = ";"),
        background_size_before_network = length(unique(contrast$gene)),
        background_size = length(background),
        eligible = eligible,
        skip_reason = skip_reason
      )
    }
  }
}

run_manifest <- data.table::rbindlist(manifest_rows, use.names = TRUE)
if (anyDuplicated(run_manifest$run_id)) {
  kda_abort("Generated run IDs are not unique; revise the ID construction.")
}
signature_members <- data.table::rbindlist(signature_rows, use.names = TRUE, fill = TRUE)
background_members <- data.table::rbindlist(background_rows, use.names = TRUE)
query_diagnostics <- data.table::rbindlist(diagnostic_rows, use.names = TRUE, fill = TRUE)
query_qc <- data.table::rbindlist(qc_rows, use.names = TRUE)
data.table::setorder(run_manifest, network_id, fine_cell_type, sex, apoe_group, query_direction)
if (nrow(signature_members)) data.table::setorder(signature_members, run_id, gene)
data.table::setorder(background_members, run_id, gene)
if (nrow(query_diagnostics)) data.table::setorder(query_diagnostics, run_id, gene)
data.table::setorder(query_qc, run_id)

atomic_write_tsv(run_manifest, expected_output_paths[[1L]])
atomic_write_tsv(signature_members, expected_output_paths[[2L]])
atomic_write_tsv(background_members, expected_output_paths[[3L]])
atomic_write_tsv(query_diagnostics, expected_output_paths[[4L]])
atomic_write_tsv(query_qc, expected_output_paths[[5L]])
finished <- Sys.time()
run_provenance <- c(
  common_run_provenance(project_root),
  expected,
  list(
    status = "complete",
    phase08_directory = project_relative_path(phase08_dir, project_root),
    annotation_directory = project_relative_path(annotation_dir, project_root),
    network_root = project_relative_path(network_root, project_root),
    run_rows = nrow(run_manifest),
    eligible_rows = sum(run_manifest$eligible),
    ineligible_rows = sum(!run_manifest$eligible),
    started_at = utc_timestamp(started),
    completed_at = utc_timestamp(finished),
    elapsed_seconds = unname(as.numeric(difftime(finished, started, units = "secs")))
  )
)
atomic_write_json(run_provenance, preparation_manifest_path)
cat(
  "Prepared", nrow(run_manifest), "KDA run rows:",
  sum(run_manifest$eligible), "eligible and",
  sum(!run_manifest$eligible), "ineligible.\n"
)
