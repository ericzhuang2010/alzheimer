#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

\`%||%\` <- function(x, y) if (is.null(x)) y else x

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
