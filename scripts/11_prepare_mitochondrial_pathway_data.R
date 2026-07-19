#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/11_prepare_mitochondrial_pathway_data.R ",
        "--config FILE --execution-config FILE --task-mode pathway\n",
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
  required <- c("config", "execution_config", "task_mode")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) {
    stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  if (!identical(out$task_mode, "pathway")) {
    stop("--task-mode must be pathway", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  path <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  prefix <- paste0(root, .Platform$file.sep)
  if (startsWith(path, prefix)) substring(path, nchar(prefix) + 1L) else path
}

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2(
    "sha256sum", path, stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "HEAD"),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  result[[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  lines <- readLines(path, warn = FALSE)
  value <- sub(
    "^VmHWM:[[:space:]]+([0-9]+)[[:space:]]+kB.*$", "\\1",
    grep("^VmHWM:", lines, value = TRUE)
  )
  if (!length(value)) return(NA_real_)
  as.numeric(value[[1L]]) / 1024^2
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid()))
  compress <- if (grepl("\\.gz$", path)) "gzip" else "none"
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA",
    logical01 = FALSE, compress = compress
  )
  if (!file.rename(tmp, path)) {
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

nonempty <- function(x) {
  !is.na(x) & nzchar(trimws(as.character(x)))
}

collapse_values <- function(x) {
  x <- unique(as.character(x[nonempty(x)]))
  if (length(x)) paste(x, collapse = ",") else ""
}

schema_ok <- function(x, expected) {
  "schema_version" %in% names(x) &&
    nrow(x) > 0L &&
    all(x$schema_version == expected)
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
for (package in c("data.table", "yaml", "digest", "readxl")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}
library(data.table)

start_time <- Sys.time()
project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, project_root)
execution_path <- absolute_path(args$execution_config, project_root)
must(file.exists(config_path), paste("Project config does not exist:", config_path))
must(file.exists(execution_path), paste("Execution config does not exist:", execution_path))

config <- yaml::read_yaml(config_path)
execution_config <- yaml::read_yaml(execution_path)
phase11_path <- absolute_path(
  config$project$phase11_pathway_config %||% "", project_root
)
must(file.exists(phase11_path), paste("Phase 11 config does not exist:", phase11_path))
phase11 <- yaml::read_yaml(phase11_path)
must(
  identical(phase11$schema_version, "phase11_pathway_config_v1"),
  "Unexpected Phase 11 config schema"
)

execution <- execution_config$execution
execution_stage <- as.character(execution$execution_stage)
must(
  execution_stage %in% c("local_pilot", "minerva_production", "lsf_fallback"),
  "Unsupported execution stage"
)
expected_validation_status <- if (identical(execution_stage, "local_pilot")) {
  as.character(phase11$expected_phase10$local_validation_status)
} else {
  as.character(phase11$expected_phase10$production_validation_status)
}
output_root <- absolute_path(config$outputs$root, project_root)
phase10_root <- file.path(output_root, "10_similarity")
final_root <- file.path(output_root, "11_pathway")
staging_root <- file.path(
  output_root, paste0(".11_pathway.staging.", Sys.getpid())
)

required_phase10 <- c(
  "similarity_status.tsv",
  "similarity_checks.tsv",
  "similarity_artifacts.tsv",
  "similarity_comparison_manifest.tsv",
  "mitochondrial_similarity_feature_manifest.tsv",
  "mitochondrial_similarity_results.tsv.gz",
  "mitochondrial_similarity_rank_sets.tsv",
  "mitochondrial_similarity_state_pairs.tsv.gz"
)
phase10_paths <- setNames(
  file.path(phase10_root, required_phase10), required_phase10
)
must(
  all(file.exists(phase10_paths)),
  paste(
    "Missing required Phase 10 inputs:",
    paste(names(phase10_paths)[!file.exists(phase10_paths)], collapse = ", ")
  )
)

msig_cfg <- phase11$references$msigdb_c2_cp
mito_cfg <- phase11$references$mitocarta_mitopathways
msig_path <- absolute_path(msig_cfg$path, project_root)
mito_path <- absolute_path(mito_cfg$path, project_root)
must(file.exists(msig_path), paste("MSigDB reference does not exist:", msig_path))
must(file.exists(mito_path), paste("MitoCarta reference does not exist:", mito_path))

script_path <- file.path(
  project_root, "scripts/11_prepare_mitochondrial_pathway_data.R"
)
manifest_path <- absolute_path(config$project$manifest, project_root)
current_hashes <- list(
  scientific_script_sha256 = sha256_file(script_path),
  scientific_config_sha256 = sha256_file(phase11_path),
  pipeline_config_sha256 = sha256_file(config_path),
  execution_config_sha256 = sha256_file(execution_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  phase10_status_sha256 = sha256_file(phase10_paths[["similarity_status.tsv"]]),
  phase10_checks_sha256 = sha256_file(phase10_paths[["similarity_checks.tsv"]]),
  phase10_artifacts_sha256 = sha256_file(phase10_paths[["similarity_artifacts.tsv"]]),
  phase10_comparison_manifest_sha256 = sha256_file(
    phase10_paths[["similarity_comparison_manifest.tsv"]]
  ),
  phase10_feature_manifest_sha256 = sha256_file(
    phase10_paths[["mitochondrial_similarity_feature_manifest.tsv"]]
  ),
  phase10_results_sha256 = sha256_file(
    phase10_paths[["mitochondrial_similarity_results.tsv.gz"]]
  ),
  phase10_rank_sets_sha256 = sha256_file(
    phase10_paths[["mitochondrial_similarity_rank_sets.tsv"]]
  ),
  phase10_state_pairs_sha256 = sha256_file(
    phase10_paths[["mitochondrial_similarity_state_pairs.tsv.gz"]]
  ),
  msigdb_sha256 = sha256_file(msig_path),
  mitocarta_sha256 = sha256_file(mito_path)
)
must(all(nonempty(unlist(current_hashes))), "Could not hash all required inputs")
must(
  identical(current_hashes$msigdb_sha256, as.character(msig_cfg$sha256)),
  "MSigDB checksum differs from the frozen Phase 11 config"
)
must(
  identical(current_hashes$mitocarta_sha256, as.character(mito_cfg$sha256)),
  "MitoCarta checksum differs from the frozen Phase 11 config"
)

if (dir.exists(final_root)) {
  status_path <- file.path(final_root, "pathway_status.tsv")
  artifacts_path <- file.path(final_root, "pathway_artifacts.tsv")
  resumable <- file.exists(status_path) && file.exists(artifacts_path)
  if (resumable) {
    existing_status <- fread(status_path)
    existing_artifacts <- fread(artifacts_path)
    resumable <- nrow(existing_status) == 1L &&
      existing_status$schema_version[[1L]] == phase11$schemas$status &&
      existing_status$validation_status[[1L]] == expected_validation_status &&
      existing_status$scientific_script_sha256[[1L]] ==
        current_hashes$scientific_script_sha256 &&
      existing_status$scientific_config_sha256[[1L]] ==
        current_hashes$scientific_config_sha256 &&
      existing_status$phase10_results_sha256[[1L]] ==
        current_hashes$phase10_results_sha256 &&
      existing_status$phase10_rank_sets_sha256[[1L]] ==
        current_hashes$phase10_rank_sets_sha256 &&
      existing_status$msigdb_sha256[[1L]] == current_hashes$msigdb_sha256 &&
      existing_status$mitocarta_sha256[[1L]] == current_hashes$mitocarta_sha256
    if (resumable) {
      for (i in seq_len(nrow(existing_artifacts))) {
        path <- absolute_path(existing_artifacts$path[[i]], project_root)
        resumable <- resumable &&
          file.exists(path) &&
          identical(sha256_file(path), existing_artifacts$sha256[[i]]) &&
          as.numeric(file.info(path)$size) ==
            as.numeric(existing_artifacts$bytes[[i]]) &&
          existing_artifacts$validation_status[[i]] == "validated_complete"
      }
    }
  }
  if (isTRUE(resumable)) {
    cat("Phase 11 output is already complete and hash-valid: ", final_root, "\n", sep = "")
    quit(status = 0L)
  }
  stop(
    "Phase 11 output directory already exists but is not resumable: ",
    final_root, call. = FALSE
  )
}

phase10_status <- fread(phase10_paths[["similarity_status.tsv"]])
phase10_checks <- fread(phase10_paths[["similarity_checks.tsv"]])
phase10_artifacts <- fread(phase10_paths[["similarity_artifacts.tsv"]])
comparisons <- fread(phase10_paths[["similarity_comparison_manifest.tsv"]])
feature_manifest <- fread(
  phase10_paths[["mitochondrial_similarity_feature_manifest.tsv"]]
)
results <- fread(phase10_paths[["mitochondrial_similarity_results.tsv.gz"]])
rank_sets <- fread(phase10_paths[["mitochondrial_similarity_rank_sets.tsv"]])
state_pairs <- fread(
  phase10_paths[["mitochondrial_similarity_state_pairs.tsv.gz"]]
)

must(nrow(phase10_status) == 1L, "Phase 10 status must have exactly one row")
must(
  schema_ok(phase10_status, phase11$expected_phase10$status_schema),
  "Unexpected Phase 10 status schema"
)
must(
  identical(phase10_status$validation_status[[1L]], expected_validation_status),
  paste("Phase 10 validation status must be", expected_validation_status)
)
must(
  schema_ok(phase10_checks, phase11$expected_phase10$checks_schema),
  "Unexpected Phase 10 checks schema"
)
must(all(phase10_checks$passed %in% TRUE), "A Phase 10 blocking check failed")
must(
  schema_ok(phase10_artifacts, phase11$expected_phase10$artifacts_schema),
  "Unexpected Phase 10 artifacts schema"
)
must(
  all(phase10_artifacts$validation_status == "validated_complete"),
  "A Phase 10 artifact is not validated_complete"
)
must(
  schema_ok(comparisons, phase11$expected_phase10$comparison_manifest_schema),
  "Unexpected Phase 10 comparison manifest schema"
)
must(
  schema_ok(feature_manifest, phase11$expected_phase10$feature_manifest_schema),
  "Unexpected Phase 10 feature manifest schema"
)
must(
  schema_ok(results, phase11$expected_phase10$results_schema),
  "Unexpected Phase 10 results schema"
)
must(
  schema_ok(rank_sets, phase11$expected_phase10$rank_sets_schema),
  "Unexpected Phase 10 rank-set schema"
)
must(
  schema_ok(state_pairs, phase11$expected_phase10$state_pairs_schema),
  "Unexpected Phase 10 state-pair schema"
)

phase10_artifact_hash_ok <- logical(nrow(phase10_artifacts))
phase10_artifact_bytes_ok <- logical(nrow(phase10_artifacts))
phase10_artifact_rows_ok <- logical(nrow(phase10_artifacts))
phase10_artifact_schema_ok <- logical(nrow(phase10_artifacts))
for (i in seq_len(nrow(phase10_artifacts))) {
  artifact_path <- absolute_path(phase10_artifacts$path[[i]], project_root)
  phase10_artifact_hash_ok[[i]] <- file.exists(artifact_path) &&
    identical(sha256_file(artifact_path), phase10_artifacts$sha256[[i]])
  phase10_artifact_bytes_ok[[i]] <- file.exists(artifact_path) &&
    as.numeric(file.info(artifact_path)$size) ==
      as.numeric(phase10_artifacts$bytes[[i]])
  if (file.exists(artifact_path)) {
    artifact_schema <- fread(
      artifact_path, select = "schema_version", showProgress = FALSE
    )
    phase10_artifact_rows_ok[[i]] <-
      nrow(artifact_schema) == as.integer(phase10_artifacts$records[[i]])
    phase10_artifact_schema_ok[[i]] <-
      nrow(artifact_schema) > 0L &&
      all(artifact_schema$schema_version == phase10_artifacts$output_schema[[i]])
  }
}
must(all(phase10_artifact_hash_ok), "A Phase 10 artifact checksum does not match")
must(all(phase10_artifact_bytes_ok), "A Phase 10 artifact byte count does not match")
must(all(phase10_artifact_rows_ok), "A Phase 10 artifact row count does not match")
must(all(phase10_artifact_schema_ok), "A Phase 10 artifact schema does not match")

comparison_config <- rbindlist(lapply(
  seq_along(phase11$comparisons),
  function(i) {
    x <- phase11$comparisons[[i]]
    data.table(
      comparison_order = as.integer(i),
      comparison_id = as.character(x$comparison_id),
      figure_analogue = as.character(x$figure_analogue),
      panel_a_requested_k = as.integer(x$panel_a_requested_k),
      panel_b_tails = paste(unlist(x$panel_b_tails), collapse = ",")
    )
  }
))
must(nrow(comparisons) == 6L, "Phase 10 must define exactly six comparisons")
must(
  setequal(comparisons$comparison_id, comparison_config$comparison_id),
  "Phase 10 comparison IDs differ from the frozen Phase 11 config"
)
must(
  !anyDuplicated(results[, .(comparison_id, similarity_feature_id)]),
  "Phase 10 result keys are not unique"
)
must(
  !anyDuplicated(rank_sets[, .(rank_set_id, selection_order)]),
  "Phase 10 rank-set keys are not unique"
)
must(
  !anyDuplicated(state_pairs[, .(
    comparison_id, similarity_feature_id, dimension_id
  )]),
  "Phase 10 state-pair keys are not unique"
)
rank_join <- merge(
  rank_sets[, .(comparison_id, similarity_feature_id)],
  results[, .(comparison_id, similarity_feature_id)],
  by = c("comparison_id", "similarity_feature_id"),
  all.x = TRUE
)
must(nrow(rank_join) == nrow(rank_sets), "A Phase 10 rank-set row does not join once")

parse_gmt <- function(path, cfg, schema) {
  lines <- readLines(path, warn = FALSE)
  must(length(lines) > 0L, "MSigDB GMT is empty")
  fields <- strsplit(lines, "\t", fixed = TRUE)
  must(all(lengths(fields) >= 3L), "MSigDB GMT contains a malformed record")
  pathway_names <- trimws(vapply(fields, function(x) x[[1L]], character(1)))
  descriptions <- vapply(fields, function(x) x[[2L]], character(1))
  must(all(nonempty(pathway_names)), "MSigDB GMT contains an empty pathway name")
  must(!anyDuplicated(pathway_names), "MSigDB GMT contains duplicate pathway names")
  metadata <- vector("list", length(fields))
  memberships <- vector("list", length(fields))
  raw_memberships <- integer(length(fields))
  duplicate_memberships <- integer(length(fields))
  for (i in seq_along(fields)) {
    genes_raw <- trimws(fields[[i]][-(1:2)])
    genes_raw <- genes_raw[nonempty(genes_raw)]
    must(length(genes_raw) > 0L, paste("Empty MSigDB pathway:", pathway_names[[i]]))
    genes <- genes_raw[!duplicated(genes_raw)]
    raw_memberships[[i]] <- length(genes_raw)
    duplicate_memberships[[i]] <- length(genes_raw) - length(genes)
    metadata[[i]] <- data.table(
      pathway_collection = as.character(cfg$collection_id),
      collection_order = 1L,
      collection_release = as.character(cfg$release),
      pathway_id = pathway_names[[i]],
      pathway_name = pathway_names[[i]],
      description = descriptions[[i]],
      source_pathway_order = as.integer(i),
      source_pathway_size = length(genes),
      hierarchy = NA_character_,
      hierarchy_depth = NA_integer_,
      level_1 = NA_character_,
      level_2 = NA_character_,
      level_3_or_deeper = NA_character_,
      parent_pathway = NA_character_,
      pathway_scope = "canonical_pathway"
    )
    memberships[[i]] <- data.table(
      schema_version = schema,
      pathway_collection = as.character(cfg$collection_id),
      collection_release = as.character(cfg$release),
      pathway_id = pathway_names[[i]],
      pathway_name = pathway_names[[i]],
      description = descriptions[[i]],
      source_pathway_order = as.integer(i),
      source_gene_order = seq_along(genes),
      symbol_hgnc_current = genes,
      hierarchy = NA_character_,
      hierarchy_depth = NA_integer_,
      level_1 = NA_character_,
      level_2 = NA_character_,
      level_3_or_deeper = NA_character_,
      parent_pathway = NA_character_,
      pathway_scope = "canonical_pathway"
    )
  }
  list(
    metadata = rbindlist(metadata),
    memberships = rbindlist(memberships),
    raw_memberships = sum(raw_memberships),
    duplicates_removed = sum(duplicate_memberships)
  )
}

parse_mitocarta <- function(path, cfg, schema) {
  raw <- as.data.table(readxl::read_excel(
    path, sheet = as.character(cfg$sheet), col_types = "text"
  ))
  required <- c("MitoPathway", "MitoPathways Hierarchy", "Genes")
  must(all(required %in% names(raw)), "MitoCarta pathway sheet columns changed")
  blank <- !nonempty(raw$MitoPathway)
  x <- raw[!blank]
  must(nrow(x) > 0L, "MitoCarta pathway sheet has no pathways")
  must(all(nonempty(x$Genes)), "A MitoCarta pathway has no genes")
  must(!anyDuplicated(x$MitoPathway), "MitoCarta pathway names are duplicated")
  metadata <- vector("list", nrow(x))
  memberships <- vector("list", nrow(x))
  raw_memberships <- integer(nrow(x))
  duplicate_memberships <- integer(nrow(x))
  for (i in seq_len(nrow(x))) {
    pathway_name <- trimws(x$MitoPathway[[i]])
    hierarchy <- trimws(x[["MitoPathways Hierarchy"]][[i]])
    parts <- trimws(strsplit(hierarchy, ">", fixed = TRUE)[[1L]])
    parts <- parts[nonempty(parts)]
    genes_raw <- trimws(strsplit(x$Genes[[i]], ",", fixed = TRUE)[[1L]])
    genes_raw <- genes_raw[nonempty(genes_raw)]
    genes <- genes_raw[!duplicated(genes_raw)]
    must(length(genes) > 0L, paste("Empty MitoCarta pathway:", pathway_name))
    depth <- length(parts)
    raw_memberships[[i]] <- length(genes_raw)
    duplicate_memberships[[i]] <- length(genes_raw) - length(genes)
    level_3 <- if (depth >= 3L) paste(parts[3:depth], collapse = " > ") else NA_character_
    parent <- if (depth >= 2L) parts[[depth - 1L]] else NA_character_
    metadata[[i]] <- data.table(
      pathway_collection = as.character(cfg$collection_id),
      collection_order = 2L,
      collection_release = as.character(cfg$release),
      pathway_id = pathway_name,
      pathway_name = pathway_name,
      description = hierarchy,
      source_pathway_order = as.integer(i),
      source_pathway_size = length(genes),
      hierarchy = hierarchy,
      hierarchy_depth = as.integer(depth),
      level_1 = if (depth >= 1L) parts[[1L]] else NA_character_,
      level_2 = if (depth >= 2L) parts[[2L]] else NA_character_,
      level_3_or_deeper = level_3,
      parent_pathway = parent,
      pathway_scope = if (depth == 1L) "broad_pathway" else "detailed_pathway"
    )
    memberships[[i]] <- data.table(
      schema_version = schema,
      pathway_collection = as.character(cfg$collection_id),
      collection_release = as.character(cfg$release),
      pathway_id = pathway_name,
      pathway_name = pathway_name,
      description = hierarchy,
      source_pathway_order = as.integer(i),
      source_gene_order = seq_along(genes),
      symbol_hgnc_current = genes,
      hierarchy = hierarchy,
      hierarchy_depth = as.integer(depth),
      level_1 = if (depth >= 1L) parts[[1L]] else NA_character_,
      level_2 = if (depth >= 2L) parts[[2L]] else NA_character_,
      level_3_or_deeper = level_3,
      parent_pathway = parent,
      pathway_scope = if (depth == 1L) "broad_pathway" else "detailed_pathway"
    )
  }
  list(
    metadata = rbindlist(metadata),
    memberships = rbindlist(memberships),
    raw_memberships = sum(raw_memberships),
    duplicates_removed = sum(duplicate_memberships),
    blank_rows = sum(blank)
  )
}

msig <- parse_gmt(msig_path, msig_cfg, phase11$schemas$membership_long)
mitocarta <- parse_mitocarta(mito_path, mito_cfg, phase11$schemas$membership_long)
pathway_metadata <- rbindlist(list(msig$metadata, mitocarta$metadata), fill = TRUE)
pathway_membership <- rbindlist(
  list(msig$memberships, mitocarta$memberships), fill = TRUE
)
setorder(pathway_membership, pathway_collection, source_pathway_order, source_gene_order)
must(
  !anyDuplicated(pathway_metadata[, .(pathway_collection, pathway_id)]),
  "Normalized pathway keys are not unique"
)
must(
  !anyDuplicated(pathway_membership[, .(
    pathway_collection, pathway_id, symbol_hgnc_current
  )]),
  "Normalized pathway memberships are not unique"
)
must(all(nonempty(pathway_membership$symbol_hgnc_current)), "Empty reference symbol")
must(
  nrow(msig$metadata) == as.integer(msig_cfg$expected_pathways),
  "Unexpected MSigDB pathway count"
)
must(
  nrow(mitocarta$metadata) == as.integer(mito_cfg$expected_pathways),
  "Unexpected MitoCarta pathway count"
)
must(
  nrow(mitocarta$memberships) == as.integer(mito_cfg$expected_memberships),
  "Unexpected MitoCarta membership count"
)
must(
  uniqueN(mitocarta$memberships$symbol_hgnc_current) ==
    as.integer(mito_cfg$expected_unique_symbols),
  "Unexpected MitoCarta unique-symbol count"
)
must(
  mitocarta$blank_rows == as.integer(mito_cfg$expected_blank_rows),
  "Unexpected MitoCarta blank-row count"
)

reference_manifest <- rbindlist(list(
  data.table(
    schema_version = phase11$schemas$reference_manifest,
    pathway_collection = as.character(msig_cfg$collection_id),
    collection_order = 1L,
    release = as.character(msig_cfg$release),
    species = as.character(msig_cfg$species),
    identifier_namespace = as.character(msig_cfg$identifier_namespace),
    source_path = relative_path(msig_path, project_root),
    source_url = as.character(msig_cfg$source_url),
    source_sha256 = current_hashes$msigdb_sha256,
    source_bytes = as.numeric(file.info(msig_path)$size),
    source_pathways = nrow(msig$metadata),
    normalized_pathways = nrow(msig$metadata),
    source_memberships = msig$raw_memberships,
    normalized_memberships = nrow(msig$memberships),
    within_pathway_duplicates_removed = msig$duplicates_removed,
    unique_symbols = uniqueN(msig$memberships$symbol_hgnc_current),
    blank_rows_discarded = 0L,
    validation_status = "validated_complete"
  ),
  data.table(
    schema_version = phase11$schemas$reference_manifest,
    pathway_collection = as.character(mito_cfg$collection_id),
    collection_order = 2L,
    release = as.character(mito_cfg$release),
    species = as.character(mito_cfg$species),
    identifier_namespace = as.character(mito_cfg$identifier_namespace),
    source_path = relative_path(mito_path, project_root),
    source_url = NA_character_,
    source_sha256 = current_hashes$mitocarta_sha256,
    source_bytes = as.numeric(file.info(mito_path)$size),
    source_pathways = nrow(mitocarta$metadata),
    normalized_pathways = nrow(mitocarta$metadata),
    source_memberships = mitocarta$raw_memberships,
    normalized_memberships = nrow(mitocarta$memberships),
    within_pathway_duplicates_removed = mitocarta$duplicates_removed,
    unique_symbols = uniqueN(mitocarta$memberships$symbol_hgnc_current),
    blank_rows_discarded = mitocarta$blank_rows,
    validation_status = "validated_complete"
  )
))
universe_names <- names(phase11$analysis_universes)
must(
  identical(sort(universe_names), sort(c("core_mito", "all_mito_related"))),
  "Phase 11 must define core_mito and all_mito_related universes"
)
background_rows <- list()
background_gene_rows <- list()
for (comparison_value in comparison_config$comparison_id) {
  comp_order <- comparison_config[
    comparison_id == comparison_value, comparison_order
  ]
  for (universe in universe_names) {
    member_col <- as.character(
      phase11$analysis_universes[[universe]]$membership_column
    )
    must(member_col %in% names(results), paste("Missing universe column:", member_col))
    eligible <- results[
      comparison_id == comparison_value &
        ranking_eligible == TRUE &
        get(member_col) == TRUE
    ]
    background_id <- paste(comparison_value, universe, sep = "::")
    mapped <- eligible[nonempty(symbol_hgnc_current)]
    duplicate_count <- nrow(mapped) - uniqueN(mapped$symbol_hgnc_current)
    mapped <- mapped[!duplicated(symbol_hgnc_current)]
    unmapped <- eligible[!nonempty(symbol_hgnc_current)]
    genes <- mapped[, .(
      schema_version = phase11$schemas$background_genes,
      background_id = background_id,
      comparison_order = as.integer(comp_order),
      comparison_id,
      analysis_universe = universe,
      similarity_feature_id,
      feature_id_original,
      symbol_hgnc_current,
      hgnc_id,
      ensembl_id_stable,
      mapping_status,
      mito_tier,
      genome_origin,
      ranking_eligible,
      admission_status = "admitted_unique_symbol"
    )]
    setorder(genes, symbol_hgnc_current, similarity_feature_id)
    background_gene_rows[[length(background_gene_rows) + 1L]] <- genes
    background_rows[[length(background_rows) + 1L]] <- data.table(
      schema_version = phase11$schemas$background_manifest,
      background_id = background_id,
      comparison_order = as.integer(comp_order),
      comparison_id = comparison_value,
      analysis_universe = universe,
      universe_role = as.character(phase11$analysis_universes[[universe]]$role),
      ranking_eligible_feature_rows = nrow(eligible),
      mapped_feature_rows = nrow(eligible) - nrow(unmapped),
      mapped_unique_background_genes = nrow(genes),
      background_size = nrow(genes),
      unmapped_feature_count = nrow(unmapped),
      unmapped_feature_ids = collapse_values(unmapped$similarity_feature_id),
      duplicate_symbol_collapses = duplicate_count,
      phase10_results_sha256 = current_hashes$phase10_results_sha256,
      validation_status = "validated_complete"
    )
  }
}
background_manifest <- rbindlist(background_rows)
background_genes <- rbindlist(background_gene_rows)
must(nrow(background_manifest) == 12L, "Expected exactly 12 ORA backgrounds")
must(
  !anyDuplicated(background_manifest$background_id),
  "Background IDs are not unique"
)
must(
  !anyDuplicated(background_genes[, .(
    background_id, symbol_hgnc_current
  )]),
  "Background symbols are not unique"
)

ora_requested_k <- as.integer(phase11$rank_sets$ora_requested_k)
ora_tails <- unlist(phase11$rank_sets$tails, use.names = FALSE)
rank200 <- rank_sets[
  requested_k == ora_requested_k &
    tail %in% ora_tails &
    analysis_universe %in% universe_names
]
rank200_groups <- unique(rank200[, .(
  rank_set_id, comparison_id, analysis_universe, tail, selected_k
)])
must(nrow(rank200_groups) == 24L, "Expected exactly 24 Phase 10 200-tail rank sets")

query_rows <- list()
query_gene_rows <- list()
for (i in seq_len(nrow(rank200_groups))) {
  group <- rank200_groups[i]
  d <- rank200[rank_set_id == group$rank_set_id]
  setorder(d, selection_order)
  must(
    nrow(d) == as.integer(group$selected_k),
    paste("Rank-set row count differs from selected_k:", group$rank_set_id)
  )
  mapped <- d[nonempty(symbol_hgnc_current)]
  duplicate_count <- nrow(mapped) - uniqueN(mapped$symbol_hgnc_current)
  mapped <- mapped[!duplicated(symbol_hgnc_current)]
  unmapped <- d[!nonempty(symbol_hgnc_current)]
  background_id <- paste(
    group$comparison_id, group$analysis_universe, sep = "::"
  )
  background_value <- background_id
  bg_symbols <- background_genes[
    background_id == background_value, symbol_hgnc_current
  ]
  must(
    all(mapped$symbol_hgnc_current %chin% bg_symbols),
    paste("Query is not a subset of background:", group$rank_set_id)
  )
  comp <- comparison_config[comparison_id == group$comparison_id]
  panel_b_tails <- strsplit(comp$panel_b_tails[[1L]], ",", fixed = TRUE)[[1L]]
  figure_required <- group$tail %in% panel_b_tails
  genes <- mapped[, .(
    schema_version = phase11$schemas$query_genes,
    query_id = as.character(group$rank_set_id),
    background_id = background_id,
    comparison_order,
    comparison_id,
    figure_analogue = comp$figure_analogue[[1L]],
    analysis_universe,
    tail,
    requested_k,
    selected_k,
    selection_order,
    deterministic_rank,
    similarity_feature_id,
    feature_id_original,
    symbol_hgnc_current,
    hgnc_id,
    ensembl_id_stable,
    mito_tier,
    score_scope,
    similarity_score,
    score_sign,
    directional_fdr_bh,
    paired_tests,
    nominal_dimensions,
    nominal_coverage_fraction,
    coverage_fraction,
    mapping_admission = "admitted_unique_symbol"
  )]
  query_gene_rows[[length(query_gene_rows) + 1L]] <- genes
  query_rows[[length(query_rows) + 1L]] <- data.table(
    schema_version = phase11$schemas$query_manifest,
    query_order = as.integer(i),
    query_id = as.character(group$rank_set_id),
    background_id = background_id,
    comparison_order = as.integer(comp$comparison_order[[1L]]),
    comparison_id = as.character(group$comparison_id),
    figure_analogue = as.character(comp$figure_analogue[[1L]]),
    panel_id = if (grepl("^Figure_6_", comp$figure_analogue[[1L]])) {
      paste0("Figure_6B_", sub("^Figure_6_", "", comp$figure_analogue[[1L]]))
    } else {
      paste0(comp$figure_analogue[[1L]], "B")
    },
    analysis_universe = as.character(group$analysis_universe),
    tail = as.character(group$tail),
    requested_k = ora_requested_k,
    selected_k = as.integer(group$selected_k),
    rank_set_feature_rows = nrow(d),
    mapped_feature_rows = nrow(d) - nrow(unmapped),
    mapped_unique_query_genes = nrow(genes),
    query_size = nrow(genes),
    background_size = length(bg_symbols),
    unmapped_feature_count = nrow(unmapped),
    unmapped_feature_ids = collapse_values(unmapped$similarity_feature_id),
    duplicate_symbol_collapses = duplicate_count,
    figure_panel_b_required = figure_required,
    required_primary_panel_b =
      figure_required && group$analysis_universe == "core_mito",
    phase10_rank_sets_sha256 = current_hashes$phase10_rank_sets_sha256,
    validation_status = "validated_complete"
  )
}
query_manifest <- rbindlist(query_rows)
query_genes <- rbindlist(query_gene_rows)
setorder(query_manifest, query_order)
setorder(query_genes, query_id, selection_order)
must(nrow(query_manifest) == 24L, "Expected 24 query definitions")
must(!anyDuplicated(query_manifest$query_id), "Query IDs are not unique")
must(
  !anyDuplicated(query_genes[, .(query_id, symbol_hgnc_current)]),
  "Query genes are not unique by current symbol"
)
must(
  all(query_manifest$query_size <= query_manifest$background_size),
  "A query is larger than its background"
)
ambiguous_tail_symbols <- query_genes[, {
  high <- symbol_hgnc_current[tail == "high_score"]
  low <- symbol_hgnc_current[tail == "low_score"]
  .(ambiguous_symbols = length(intersect(high, low)))
}, by = .(comparison_id, analysis_universe)]
must(
  all(ambiguous_tail_symbols$ambiguous_symbols == 0L),
  "A current symbol appears in both high and low tails"
)

panel_rank_rows <- list()
for (i in seq_len(nrow(comparison_config))) {
  comp <- comparison_config[i]
  for (universe in universe_names) {
    universe_value <- universe
    d <- rank_sets[
      comparison_id == comp$comparison_id &
        analysis_universe == universe_value &
        requested_k == as.integer(comp$panel_a_requested_k) &
        tail %in% ora_tails
    ]
    must(
      uniqueN(d$rank_set_id) == 2L,
      paste("Missing Phase 10 panel-A rank sets:", comp$comparison_id, universe)
    )
    d[, `:=`(
      figure_analogue = as.character(comp$figure_analogue),
      panel_id = if (grepl("^Figure_6_", comp$figure_analogue)) {
        paste0("Figure_6A_", sub("^Figure_6_", "", comp$figure_analogue))
      } else {
        paste0(comp$figure_analogue, "A")
      }
    )]
    panel_rank_rows[[length(panel_rank_rows) + 1L]] <- d
  }
}
panel_rank <- rbindlist(panel_rank_rows, fill = TRUE)
count_columns <- c(
  "S_pos1_pos1", "S_neg1_neg1", "S_pos1_0", "S_neg1_0",
  "S_0_pos1", "S_0_neg1", "S_pos1_neg1", "S_neg1_pos1", "S_0_0"
)
panel_result_columns <- c(
  "comparison_id", "similarity_feature_id", count_columns,
  "genome_origin"
)
panel_wide <- merge(
  panel_rank,
  results[, ..panel_result_columns],
  by = c("comparison_id", "similarity_feature_id"),
  all.x = TRUE
)
must(nrow(panel_wide) == nrow(panel_rank), "Panel-A rank rows do not join once")
must(
  !anyNA(panel_wide[, ..count_columns]),
  "Panel-A state-pair counts are missing after the result join"
)
panel_wide[, symbol_duplicated := duplicated(
  symbol_hgnc_current
) | duplicated(symbol_hgnc_current, fromLast = TRUE),
by = rank_set_id]
panel_wide[, display_label := fifelse(
  symbol_duplicated,
  paste0(symbol_hgnc_current, " [", similarity_feature_id, "]"),
  symbol_hgnc_current
)]
pair_spec <- data.table(
  pair_column = count_columns,
  pair_label = c(
    "(+1,+1)", "(-1,-1)", "(+1,0)", "(-1,0)", "(0,+1)",
    "(0,-1)", "(+1,-1)", "(-1,+1)", "(0,0)"
  ),
  source_state_pair = c(
    "(1,1)", "(-1,-1)", "(1,0)", "(-1,0)", "(0,1)",
    "(0,-1)", "(1,-1)", "(-1,1)", "(0,0)"
  ),
  pair_order = seq_along(count_columns)
)
similarity_panel_data <- melt(
  panel_wide,
  id.vars = setdiff(names(panel_wide), count_columns),
  measure.vars = count_columns,
  variable.name = "pair_column",
  value.name = "occurrence_count"
)
similarity_panel_data <- merge(
  similarity_panel_data, pair_spec,
  by = "pair_column", all.x = TRUE
)
similarity_panel_data[, occurrence_fraction := fifelse(
  paired_tests > 0L, occurrence_count / paired_tests, NA_real_
)]
similarity_panel_data[, panel_feature_id := similarity_feature_id]
similarity_panel_data[, execution_label := expected_validation_status]
similarity_panel_data[, schema_version := phase11$schemas$similarity_panel]
similarity_panel_data[, tail_order := match(
  tail, c("high_score", "low_score")
)]
setorder(
  similarity_panel_data, comparison_order, analysis_universe,
  tail_order, selection_order, pair_order
)

state_count_audit <- state_pairs[
  paired_for_score == TRUE,
  .(audit_count = .N),
  by = .(comparison_id, similarity_feature_id, source_state_pair = state_pair)
]
panel_audit <- merge(
  similarity_panel_data[, .(
    comparison_id, similarity_feature_id, source_state_pair,
    occurrence_count
  )],
  state_count_audit,
  by = c("comparison_id", "similarity_feature_id", "source_state_pair"),
  all.x = TRUE
)
panel_audit[is.na(audit_count), audit_count := 0L]
panel_state_counts_reconcile <- all(
  panel_audit$occurrence_count == panel_audit$audit_count
)
membership_keys <- paste(
  pathway_membership$pathway_collection,
  pathway_membership$pathway_id,
  sep = "\r"
)
membership_lists <- split(
  pathway_membership$symbol_hgnc_current, membership_keys
)
ora_rows <- list()
for (i in seq_len(nrow(query_manifest))) {
  query <- query_manifest[i]
  query_id <- as.character(query$query_id)
  background_id <- as.character(query$background_id)
  query_value <- query_id
  background_value <- background_id
  query_symbols <- query_genes[
    query_id == query_value, symbol_hgnc_current
  ]
  query_feature_map <- query_genes[
    query_id == query_value,
    .(symbol_hgnc_current, similarity_feature_id)
  ]
  background_symbols <- background_genes[
    background_id == background_value, symbol_hgnc_current
  ]
  N <- length(background_symbols)
  n <- length(query_symbols)
  must(n > 0L, paste("Mapped query is empty:", query_id))
  must(n <= N, paste("Mapped query exceeds background:", query_id))
  for (collection_value in reference_manifest$pathway_collection) {
    meta <- pathway_metadata[pathway_collection == collection_value]
    keys <- paste(collection_value, meta$pathway_id, sep = "\r")
    members <- membership_lists[keys]
    background_members <- lapply(
      members, function(x) x[x %chin% background_symbols]
    )
    overlaps <- lapply(
      members, function(x) x[x %chin% query_symbols]
    )
    M <- lengths(background_members)
    k <- lengths(overlaps)
    coverage <- M / meta$source_pathway_size
    cfg <- if (collection_value == as.character(msig_cfg$collection_id)) {
      msig_cfg
    } else {
      mito_cfg
    }
    minimum_members <- as.integer(cfg$minimum_background_members)
    reason <- rep("tested", nrow(meta))
    reason[M < minimum_members] <- "below_minimum_background_members"
    reason[M >= N] <- "pathway_spans_entire_background"
    if (collection_value == as.character(mito_cfg$collection_id)) {
      reason[
        reason == "tested" &
          coverage < as.numeric(cfg$minimum_reference_coverage)
      ] <- "below_minimum_reference_coverage"
    }
    tested_here <- reason == "tested"
    p_value <- rep(NA_real_, nrow(meta))
    p_value[tested_here] <- phyper(
      q = k[tested_here] - 1L,
      m = M[tested_here],
      n = N - M[tested_here],
      k = n,
      lower.tail = FALSE
    )
    overlap_genes <- vapply(
      overlaps,
      function(x) if (length(x)) paste(x, collapse = ",") else "",
      character(1)
    )
    overlap_features <- vapply(
      overlaps,
      function(x) {
        if (!length(x)) return("")
        paste(
          query_feature_map$similarity_feature_id[
            match(x, query_feature_map$symbol_hgnc_current)
          ],
          collapse = ","
        )
      },
      character(1)
    )
    ora_rows[[length(ora_rows) + 1L]] <- data.table(
      schema_version = phase11$schemas$ora,
      query_order = as.integer(query$query_order),
      query_id = query_id,
      background_id = background_id,
      comparison_order = as.integer(query$comparison_order),
      comparison_id = as.character(query$comparison_id),
      figure_analogue = as.character(query$figure_analogue),
      panel_id = as.character(query$panel_id),
      analysis_universe = as.character(query$analysis_universe),
      tail = as.character(query$tail),
      requested_k = as.integer(query$requested_k),
      selected_k = as.integer(query$selected_k),
      pathway_collection = collection_value,
      collection_order = meta$collection_order,
      collection_release = meta$collection_release,
      pathway_id = meta$pathway_id,
      pathway_name = meta$pathway_name,
      pathway_label = meta$pathway_name,
      description = meta$description,
      source_pathway_order = meta$source_pathway_order,
      hierarchy = meta$hierarchy,
      hierarchy_depth = meta$hierarchy_depth,
      level_1 = meta$level_1,
      level_2 = meta$level_2,
      level_3_or_deeper = meta$level_3_or_deeper,
      parent_pathway = meta$parent_pathway,
      pathway_scope = meta$pathway_scope,
      source_pathway_size = as.integer(meta$source_pathway_size),
      background_pathway_size = as.integer(M),
      background_size = as.integer(N),
      query_size = as.integer(n),
      overlap_count = as.integer(k),
      query_in_pathway = as.integer(k),
      query_not_in_pathway = as.integer(n - k),
      background_outside_query_in_pathway = as.integer(M - k),
      background_outside_query_not_in_pathway =
        as.integer(N - M - n + k),
      reference_coverage = coverage,
      gene_ratio = k / n,
      background_ratio = M / N,
      fold_enrichment = ifelse(M > 0L, (k / n) / (M / N), 0),
      pathway_hit_rate = ifelse(M > 0L, k / M, 0),
      test_status = ifelse(tested_here, "tested", "not_testable"),
      testability_reason = reason,
      small_pathway_status = ifelse(
        tested_here & M <= as.integer(phase11$ora$small_pathway_upper_bound),
        "small_pathway_lower_confidence",
        ifelse(tested_here, "standard_pathway_size", "not_testable")
      ),
      p_value = p_value,
      overlap_genes = overlap_genes,
      overlap_source_features = overlap_features,
      figure_panel_b_required = as.logical(query$figure_panel_b_required),
      required_primary_panel_b = as.logical(query$required_primary_panel_b),
      execution_label = expected_validation_status
    )
  }
}
ora <- rbindlist(ora_rows, fill = TRUE)
ora[, `:=`(
  tail_fdr_bh = NA_real_,
  tail_fdr_family_size = NA_integer_,
  tail_fdr_significant = FALSE,
  global_fdr_bh = NA_real_,
  global_fdr_family_size = NA_integer_
)]
ora[test_status == "tested", `:=`(
  tail_fdr_bh = p.adjust(p_value, method = as.character(phase11$fdr$method)),
  tail_fdr_family_size = .N
), by = .(query_id, pathway_collection)]
ora[test_status == "tested", `:=`(
  global_fdr_bh = p.adjust(p_value, method = as.character(phase11$fdr$method)),
  global_fdr_family_size = .N
), by = .(analysis_universe, pathway_collection)]
ora[
  test_status == "tested",
  tail_fdr_significant :=
    tail_fdr_bh < as.numeric(phase11$fdr$threshold)
]
ora[, query_significant_pathways := sum(tail_fdr_significant), by = .(
  query_id, pathway_collection
)]
ora[, status_order := ifelse(test_status == "tested", 0L, 1L)]
setorderv(
  ora,
  c(
    "query_order", "collection_order", "status_order",
    "tail_fdr_bh", "p_value", "overlap_count", "source_pathway_order"
  ),
  c(1L, 1L, 1L, 1L, 1L, -1L, 1L),
  na.last = TRUE
)
ora[, statistical_order := seq_len(.N), by = .(query_id, pathway_collection)]
ora[, status_order := NULL]

profile_rows <- list()
panel_manifest_rows <- list()
for (profile_id in names(phase11$downstream_profiles)) {
  profile <- phase11$downstream_profiles[[profile_id]]
  profile_value <- profile_id
  universe_value <- as.character(profile$analysis_universe)
  collection_value <- as.character(profile$pathway_collection)
  profile_queries <- query_manifest[
    analysis_universe == universe_value &
      figure_panel_b_required == TRUE
  ]
  must(nrow(profile_queries) == 9L, paste("Expected nine panel-B queries:", profile_id))
  d <- ora[
    query_id %in% profile_queries$query_id &
      pathway_collection == collection_value
  ]
  d[, `:=`(
    profile_id = profile_value,
    profile_role = as.character(profile$role),
    explicit_query_status = fifelse(
      query_significant_pathways == 0L,
      "no_significant_pathways", "significant_pathways_present"
    )
  )]
  profile_rows[[length(profile_rows) + 1L]] <- d
  set_count <- reference_manifest[
    pathway_collection == collection_value, normalized_pathways
  ]
  panel_manifest_rows[[length(panel_manifest_rows) + 1L]] <-
    profile_queries[, .(
      schema_version = phase11$schemas$downstream_panel_manifest,
      profile_id = profile_value,
      profile_role = as.character(profile$role),
      figure_analogue,
      panel_id,
      comparison_order,
      comparison_id,
      analysis_universe,
      pathway_collection = collection_value,
      collection_release = reference_manifest[
        pathway_collection == collection_value, release
      ],
      required_tail = tail,
      query_id,
      requested_k,
      selected_k,
      query_size,
      background_size,
      expected_pathway_rows = as.integer(set_count),
      data_source = "pathway_panel_data.tsv.gz",
      execution_label = expected_validation_status
    )]
}
pathway_panel_data <- rbindlist(profile_rows, fill = TRUE)
pathway_panel_data[, schema_version := phase11$schemas$pathway_panel]
setcolorder(
  pathway_panel_data,
  c(
    "schema_version", "profile_id", "profile_role",
    setdiff(names(pathway_panel_data), c(
      "schema_version", "profile_id", "profile_role"
    ))
  )
)
downstream_panel_manifest <- rbindlist(panel_manifest_rows)
setorder(
  downstream_panel_manifest, profile_id,
  comparison_order, required_tail
)

toy_cases <- data.table(
  case_id = c(
    "moderate_overlap", "zero_overlap", "single_overlap", "complete_overlap"
  ),
  background_size = c(20L, 10L, 10L, 10L),
  query_size = c(5L, 2L, 2L, 2L),
  background_pathway_size = c(4L, 3L, 3L, 3L),
  overlap_count = c(2L, 0L, 1L, 2L),
  expected_p_value = c(3856 / 15504, 1, 24 / 45, 3 / 45)
)
toy_cases[, observed_p_value := phyper(
  overlap_count - 1L,
  background_pathway_size,
  background_size - background_pathway_size,
  query_size,
  lower.tail = FALSE
)]
toy_cases[, absolute_error := abs(observed_p_value - expected_p_value)]
toy_cases[, passed := absolute_error < 1e-12]
toy_cases[, `:=`(
  schema_version = phase11$schemas$toy_checks,
  formula = "phyper(k-1,M,N-M,n,lower.tail=FALSE)"
)]
setcolorder(toy_cases, c(
  "schema_version", "case_id", "background_size", "query_size",
  "background_pathway_size", "overlap_count", "formula",
  "expected_p_value", "observed_p_value", "absolute_error", "passed"
))

fisher_audit <- head(ora[
  test_status == "tested" & overlap_count > 0L
], 20L)
fisher_p <- vapply(seq_len(nrow(fisher_audit)), function(i) {
  x <- fisher_audit[i]
  table <- matrix(c(
    x$overlap_count,
    x$query_not_in_pathway,
    x$background_outside_query_in_pathway,
    x$background_outside_query_not_in_pathway
  ), nrow = 2L, byrow = TRUE)
  fisher.test(table, alternative = "greater")$p.value
}, numeric(1))
fisher_audit_ok <- nrow(fisher_audit) > 0L &&
  max(abs(fisher_audit$p_value - fisher_p)) < 1e-12

tail_fdr_audit <- ora[test_status == "tested", .(
  max_error = max(abs(
    tail_fdr_bh -
      p.adjust(p_value, method = as.character(phase11$fdr$method))
  ))
), by = .(query_id, pathway_collection)]
global_fdr_audit <- ora[test_status == "tested", .(
  max_error = max(abs(
    global_fdr_bh -
      p.adjust(p_value, method = as.character(phase11$fdr$method))
  ))
), by = .(analysis_universe, pathway_collection)]

qc_rows <- list(
  reference_manifest[, .(
    section = "reference",
    metric = "normalized_pathways",
    category = pathway_collection,
    value = as.character(normalized_pathways)
  )],
  background_manifest[, .(
    section = "background",
    metric = "background_size",
    category = background_id,
    value = as.character(background_size)
  )],
  query_manifest[, .(
    section = "query",
    metric = "query_size",
    category = query_id,
    value = as.character(query_size)
  )],
  ora[, .N, by = .(pathway_collection, test_status)][, .(
    section = "ora",
    metric = "test_status_rows",
    category = paste(pathway_collection, test_status, sep = "::"),
    value = as.character(N)
  )],
  ora[, .(
    significant_pathways = sum(tail_fdr_significant)
  ), by = .(query_id, pathway_collection)][, .(
    section = "ora",
    metric = "tail_fdr_significant_pathways",
    category = paste(query_id, pathway_collection, sep = "::"),
    value = as.character(significant_pathways)
  )],
  pathway_panel_data[, .N, by = profile_id][, .(
    section = "downstream",
    metric = "pathway_panel_rows",
    category = profile_id,
    value = as.character(N)
  )]
)
pathway_qc_summary <- rbindlist(qc_rows, fill = TRUE)
pathway_qc_summary[, schema_version := phase11$schemas$qc_summary]
setcolorder(
  pathway_qc_summary,
  c("schema_version", "section", "metric", "category", "value")
)
setorder(pathway_qc_summary, section, metric, category)

checks_list <- list()
add_check <- function(name, blocking, passed, observed, expected, details = "") {
  checks_list[[length(checks_list) + 1L]] <<- data.table(
    schema_version = phase11$schemas$checks,
    check_name = as.character(name),
    blocking = isTRUE(blocking),
    passed = isTRUE(passed),
    observed = as.character(observed),
    expected = as.character(expected),
    details = as.character(details)
  )
}
add_check(
  "phase10_status", TRUE,
  nrow(phase10_status) == 1L &&
    phase10_status$validation_status[[1L]] == expected_validation_status,
  phase10_status$validation_status[[1L]], expected_validation_status
)
add_check(
  "phase10_blocking_checks", TRUE, all(phase10_checks$passed %in% TRUE),
  sum(phase10_checks$passed %in% TRUE), nrow(phase10_checks)
)
add_check(
  "phase10_artifact_hashes", TRUE, all(phase10_artifact_hash_ok),
  sum(phase10_artifact_hash_ok), nrow(phase10_artifacts)
)
add_check(
  "phase10_artifact_bytes", TRUE, all(phase10_artifact_bytes_ok),
  sum(phase10_artifact_bytes_ok), nrow(phase10_artifacts)
)
add_check(
  "phase10_artifact_rows_and_schemas", TRUE,
  all(phase10_artifact_rows_ok) && all(phase10_artifact_schema_ok),
  paste(sum(phase10_artifact_rows_ok), sum(phase10_artifact_schema_ok), sep = "/"),
  paste(nrow(phase10_artifacts), nrow(phase10_artifacts), sep = "/")
)
add_check(
  "six_frozen_comparisons", TRUE,
  nrow(comparisons) == 6L &&
    setequal(comparisons$comparison_id, comparison_config$comparison_id),
  nrow(comparisons), 6L
)
add_check(
  "phase10_keys_unique", TRUE,
  !anyDuplicated(results[, .(comparison_id, similarity_feature_id)]) &&
    !anyDuplicated(rank_sets[, .(rank_set_id, selection_order)]) &&
    !anyDuplicated(state_pairs[, .(
      comparison_id, similarity_feature_id, dimension_id
    )]),
  "result/rank/state-pair", "all unique"
)
add_check(
  "msigdb_checksum", TRUE,
  current_hashes$msigdb_sha256 == as.character(msig_cfg$sha256),
  current_hashes$msigdb_sha256, as.character(msig_cfg$sha256)
)
add_check(
  "msigdb_pathways", TRUE,
  nrow(msig$metadata) == as.integer(msig_cfg$expected_pathways),
  nrow(msig$metadata), as.integer(msig_cfg$expected_pathways)
)
add_check(
  "mitocarta_checksum", TRUE,
  current_hashes$mitocarta_sha256 == as.character(mito_cfg$sha256),
  current_hashes$mitocarta_sha256, as.character(mito_cfg$sha256)
)
add_check(
  "mitocarta_invariants", TRUE,
  nrow(mitocarta$metadata) == as.integer(mito_cfg$expected_pathways) &&
    nrow(mitocarta$memberships) == as.integer(mito_cfg$expected_memberships) &&
    uniqueN(mitocarta$memberships$symbol_hgnc_current) ==
      as.integer(mito_cfg$expected_unique_symbols) &&
    mitocarta$blank_rows == as.integer(mito_cfg$expected_blank_rows),
  paste(
    nrow(mitocarta$metadata), nrow(mitocarta$memberships),
    uniqueN(mitocarta$memberships$symbol_hgnc_current),
    mitocarta$blank_rows, sep = "/"
  ),
  paste(
    mito_cfg$expected_pathways, mito_cfg$expected_memberships,
    mito_cfg$expected_unique_symbols, mito_cfg$expected_blank_rows, sep = "/"
  )
)
add_check(
  "reference_keys_and_memberships", TRUE,
  !anyDuplicated(pathway_metadata[, .(pathway_collection, pathway_id)]) &&
    !anyDuplicated(pathway_membership[, .(
      pathway_collection, pathway_id, symbol_hgnc_current
    )]) &&
    all(nonempty(pathway_membership$symbol_hgnc_current)),
  nrow(pathway_membership), "unique nonempty memberships"
)
add_check(
  "background_count_and_keys", TRUE,
  nrow(background_manifest) == 12L &&
    !anyDuplicated(background_manifest$background_id) &&
    !anyDuplicated(background_genes[, .(
      background_id, symbol_hgnc_current
    )]),
  nrow(background_manifest), 12L
)
add_check(
  "query_count_and_keys", TRUE,
  nrow(query_manifest) == 24L &&
    !anyDuplicated(query_manifest$query_id) &&
    !anyDuplicated(query_genes[, .(query_id, symbol_hgnc_current)]),
  nrow(query_manifest), 24L
)
add_check(
  "query_sizes_and_subsets", TRUE,
  all(query_manifest$rank_set_feature_rows == query_manifest$selected_k) &&
    all(query_manifest$query_size <= query_manifest$background_size),
  paste(range(query_manifest$query_size), collapse = "-"),
  "stored selected_k and subset of background"
)
add_check(
  "cross_tail_symbol_ambiguity", TRUE,
  all(ambiguous_tail_symbols$ambiguous_symbols == 0L),
  sum(ambiguous_tail_symbols$ambiguous_symbols), 0L
)
expected_ora_rows <- nrow(query_manifest) * nrow(pathway_metadata)
add_check(
  "complete_ora_grid", TRUE,
  nrow(ora) == expected_ora_rows &&
    !anyDuplicated(ora[, .(query_id, pathway_collection, pathway_id)]),
  nrow(ora), expected_ora_rows
)
tested <- ora$test_status == "tested"
contingency_ok <- with(ora,
  query_in_pathway >= 0L &
    query_not_in_pathway >= 0L &
    background_outside_query_in_pathway >= 0L &
    background_outside_query_not_in_pathway >= 0L &
    query_in_pathway + query_not_in_pathway +
      background_outside_query_in_pathway +
      background_outside_query_not_in_pathway == background_size
)
add_check(
  "ora_contingency_cells", TRUE, all(contingency_ok),
  sum(contingency_ok), nrow(ora)
)
recalculated_p <- phyper(
  ora$overlap_count[tested] - 1L,
  ora$background_pathway_size[tested],
  ora$background_size[tested] - ora$background_pathway_size[tested],
  ora$query_size[tested],
  lower.tail = FALSE
)
add_check(
  "ora_p_values", TRUE,
  all(abs(ora$p_value[tested] - recalculated_p) < 1e-14) &&
    all(is.na(ora$p_value[!tested])) &&
    all(ora$p_value[tested] >= 0 & ora$p_value[tested] <= 1),
  length(recalculated_p), "all tested rows reproduce phyper"
)
zero_overlap <- tested & ora$overlap_count == 0L
add_check(
  "zero_overlap_p_value", TRUE,
  all(ora$p_value[zero_overlap] == 1),
  sum(zero_overlap), "p_value=1"
)
add_check(
  "fisher_exact_audit", TRUE, fisher_audit_ok,
  nrow(fisher_audit), "up to 20 tested nonzero-overlap rows"
)
add_check(
  "tail_fdr_recalculation", TRUE,
  all(tail_fdr_audit$max_error < 1e-14),
  max(tail_fdr_audit$max_error), 0
)
add_check(
  "global_fdr_recalculation", TRUE,
  all(global_fdr_audit$max_error < 1e-14),
  max(global_fdr_audit$max_error), 0
)
add_check(
  "not_testable_inference_missing", TRUE,
  all(is.na(ora$p_value[!tested])) &&
    all(is.na(ora$tail_fdr_bh[!tested])) &&
    all(is.na(ora$global_fdr_bh[!tested])),
  sum(!tested), "all inferential values NA"
)
add_check(
  "similarity_panel_counts", TRUE,
  panel_state_counts_reconcile &&
    all(similarity_panel_data$occurrence_count >= 0L) &&
    all(
      similarity_panel_data$occurrence_fraction >= 0 &
        similarity_panel_data$occurrence_fraction <= 1
    ),
  nrow(similarity_panel_data), "all counts reconcile to Phase 10 state pairs"
)
add_check(
  "downstream_profiles", TRUE,
  setequal(
    unique(downstream_panel_manifest$profile_id),
    names(phase11$downstream_profiles)
  ) &&
    nrow(downstream_panel_manifest) == 27L &&
    nrow(pathway_panel_data) > 0L,
  paste(
    uniqueN(downstream_panel_manifest$profile_id),
    nrow(downstream_panel_manifest), sep = "/"
  ),
  "3 profiles/27 query-profile rows"
)
add_check(
  "figure6_low_tail", TRUE,
  all(
    downstream_panel_manifest[
      grepl("^Figure_6", figure_analogue), required_tail
    ] == as.character(phase11$rank_sets$figure6_primary_tail)
  ),
  as.character(phase11$rank_sets$figure6_primary_tail), "low_score"
)
add_check(
  "toy_hypergeometric_cases", TRUE, all(toy_cases$passed),
  sum(toy_cases$passed), nrow(toy_cases)
)
add_check(
  "no_figure_outputs", TRUE, TRUE,
  "tabular Phase 11 bundle", "no PDF/PNG/SVG"
)

pathway_checks <- rbindlist(checks_list)
must(
  all(pathway_checks$passed[pathway_checks$blocking]),
  paste(
    "Blocking Phase 11 checks failed:",
    paste(
      pathway_checks$check_name[
        pathway_checks$blocking & !pathway_checks$passed
      ],
      collapse = ", "
    )
  )
)

setorder(reference_manifest, collection_order)
setorder(pathway_metadata, collection_order, source_pathway_order)
setorder(background_manifest, comparison_order, analysis_universe)
setorder(background_genes, comparison_order, analysis_universe, symbol_hgnc_current)
setorder(query_manifest, query_order)
setorder(query_genes, query_id, selection_order)
setorder(
  pathway_panel_data, profile_id, query_order,
  collection_order, statistical_order
)

dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
must(dir.exists(staging_root), "Could not create Phase 11 staging directory")
cleanup_staging <- TRUE
on.exit({
  if (cleanup_staging && dir.exists(staging_root)) {
    unlink(staging_root, recursive = TRUE, force = TRUE)
  }
}, add = TRUE)

output_tables <- list(
  "pathway_reference_manifest.tsv" = reference_manifest,
  "pathway_membership_long.tsv.gz" = pathway_membership,
  "pathway_background_manifest.tsv" = background_manifest,
  "pathway_background_genes.tsv.gz" = background_genes,
  "pathway_query_manifest.tsv" = query_manifest,
  "pathway_query_genes.tsv.gz" = query_genes,
  "similarity_tail_pathway_ora.tsv.gz" = ora,
  "similarity_panel_data.tsv.gz" = similarity_panel_data,
  "pathway_panel_data.tsv.gz" = pathway_panel_data,
  "downstream_panel_manifest.tsv" = downstream_panel_manifest,
  "pathway_toy_checks.tsv" = toy_cases,
  "pathway_qc_summary.tsv" = pathway_qc_summary,
  "pathway_checks.tsv" = pathway_checks
)
for (name in names(output_tables)) {
  atomic_fwrite(output_tables[[name]], file.path(staging_root, name))
}

artifact_rows <- lapply(names(output_tables), function(name) {
  stage_path <- file.path(staging_root, name)
  final_path <- file.path(final_root, name)
  table <- output_tables[[name]]
  data.table(
    schema_version = phase11$schemas$artifacts,
    artifact = name,
    path = relative_path(final_path, project_root),
    bytes = as.numeric(file.info(stage_path)$size),
    sha256 = sha256_file(stage_path),
    records = nrow(table),
    output_schema = if (nrow(table)) {
      as.character(table$schema_version[[1L]])
    } else {
      NA_character_
    },
    validation_status = "validated_complete"
  )
})
pathway_artifacts <- rbindlist(artifact_rows)
must(
  all(nonempty(pathway_artifacts$sha256)),
  "Could not hash all Phase 11 artifacts"
)
atomic_fwrite(
  pathway_artifacts, file.path(staging_root, "pathway_artifacts.tsv")
)

status <- data.table(
  schema_version = phase11$schemas$status,
  execution_stage = execution_stage,
  execution_phase = as.integer(execution$execution_phase),
  backend = as.character(execution$backend),
  run_id = as.character(execution$run_id),
  stable_task_id = "global:pathway",
  task_mode = "pathway",
  scientific_script = "scripts/11_prepare_mitochondrial_pathway_data.R",
  scientific_script_sha256 = current_hashes$scientific_script_sha256,
  scientific_config_sha256 = current_hashes$scientific_config_sha256,
  pipeline_config_sha256 = current_hashes$pipeline_config_sha256,
  execution_config_sha256 = current_hashes$execution_config_sha256,
  rds_manifest_sha256 = current_hashes$rds_manifest_sha256,
  phase10_status_sha256 = current_hashes$phase10_status_sha256,
  phase10_checks_sha256 = current_hashes$phase10_checks_sha256,
  phase10_artifacts_sha256 = current_hashes$phase10_artifacts_sha256,
  phase10_comparison_manifest_sha256 =
    current_hashes$phase10_comparison_manifest_sha256,
  phase10_feature_manifest_sha256 =
    current_hashes$phase10_feature_manifest_sha256,
  phase10_results_sha256 = current_hashes$phase10_results_sha256,
  phase10_rank_sets_sha256 = current_hashes$phase10_rank_sets_sha256,
  phase10_state_pairs_sha256 = current_hashes$phase10_state_pairs_sha256,
  msigdb_sha256 = current_hashes$msigdb_sha256,
  mitocarta_sha256 = current_hashes$mitocarta_sha256,
  rds_sets = as.integer(phase10_status$rds_sets[[1L]]),
  fine_cell_types = as.integer(phase10_status$fine_cell_types[[1L]]),
  comparison_families = nrow(comparisons),
  pathway_collections = nrow(reference_manifest),
  source_pathways = sum(reference_manifest$source_pathways),
  normalized_memberships = sum(reference_manifest$normalized_memberships),
  background_families = nrow(background_manifest),
  query_families = nrow(query_manifest),
  ora_rows = nrow(ora),
  tested_ora_rows = sum(tested),
  primary_significant_ora_rows = sum(ora$tail_fdr_significant),
  similarity_panel_rows = nrow(similarity_panel_data),
  pathway_panel_rows = nrow(pathway_panel_data),
  downstream_panel_definitions = nrow(downstream_panel_manifest),
  fdr_method = as.character(phase11$fdr$method),
  primary_fdr_family = as.character(phase11$fdr$primary_family),
  global_fdr_family = as.character(phase11$fdr$global_family),
  fdr_threshold = as.numeric(phase11$fdr$threshold),
  failed_checks = sum(pathway_checks$blocking & !pathway_checks$passed),
  r_version = as.character(getRversion()),
  data_table_version = as.character(packageVersion("data.table")),
  yaml_version = as.character(packageVersion("yaml")),
  digest_version = as.character(packageVersion("digest")),
  readxl_version = as.character(packageVersion("readxl")),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(
    Sys.time(), start_time, units = "secs"
  )),
  validation_status = expected_validation_status,
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
)
atomic_fwrite(status, file.path(staging_root, "pathway_status.tsv"))

must(!dir.exists(final_root), "Final Phase 11 directory appeared during execution")
if (!file.rename(staging_root, final_root)) {
  stop("Could not atomically publish Phase 11 output directory", call. = FALSE)
}
cleanup_staging <- FALSE

cat("Phase 11 completed successfully\n")
cat("  output: ", final_root, "\n", sep = "")
cat("  status: ", expected_validation_status, "\n", sep = "")
cat("  references: ", nrow(reference_manifest), "\n", sep = "")
cat("  backgrounds: ", nrow(background_manifest), "\n", sep = "")
cat("  queries: ", nrow(query_manifest), "\n", sep = "")
cat("  ORA rows: ", nrow(ora), "\n", sep = "")
cat("  tested ORA rows: ", sum(tested), "\n", sep = "")
