#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = "annotate_genes")
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/09_annotate_mitochondrial_genes.R ",
        "--config FILE --execution-config FILE [--task-mode annotate_genes]\n",
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
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  if (is.null(out$execution_config)) stop("--execution-config is required", call. = FALSE)
  if (!identical(out$task_mode, "annotate_genes")) {
    stop("--task-mode must be 'annotate_genes'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  sub(paste0("^", root, "/?"), "", path)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2(
    "sha256sum", path, stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    return(NA_character_)
  }
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(gsub("[^0-9.]", "", line[[1L]])) / (1024^2)
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else {
    result[[1L]]
  }
}

as_bool <- function(x) {
  !is.na(x) & toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

write_tsv <- function(x, path) {
  data.table::fwrite(x, path, sep = "\t", quote = FALSE, na = "NA")
}

write_tsv_gz <- function(x, path) {
  plain <- paste0(path, ".plain.", Sys.getpid())
  data.table::fwrite(x, plain, sep = "\t", quote = FALSE, na = "NA")
  status <- system2("gzip", c("-n", "-f", plain))
  compressed <- paste0(plain, ".gz")
  if (status != 0L || !file.exists(compressed) ||
      !file.rename(compressed, path)) {
    unlink(c(plain, compressed))
    stop("Could not write gzip-compressed TSV: ", path, call. = FALSE)
  }
}

build_lookup <- function(pairs) {
  pairs <- unique(pairs[!is.na(key) & nzchar(trimws(key))])
  pairs[, key := trimws(key)]
  counts <- pairs[, .(targets = data.table::uniqueN(hgnc_row)), by = key]
  unique_keys <- counts[targets == 1L, key]
  unique_pairs <- unique(pairs[key %chin% unique_keys, .(key, hgnc_row)])
  list(
    unique = stats::setNames(unique_pairs$hgnc_row, unique_pairs$key),
    ambiguous = counts[targets > 1L, key]
  )
}

explode_hgnc_field <- function(values, rows) {
  pieces <- strsplit(ifelse(is.na(values), "", values), "|", fixed = TRUE)
  result <- data.table::data.table(
    lookup_key = trimws(unlist(pieces, use.names = FALSE)),
    hgnc_row = rep(rows, lengths(pieces))
  )
  data.table::setnames(result, "lookup_key", "key")
  result[nzchar(key)]
}

lookup_rows <- function(keys, lookup) {
  result <- rep(NA_integer_, length(keys))
  valid <- !is.na(keys) & nzchar(keys) & keys %chin% names(lookup)
  result[valid] <- as.integer(unname(lookup[keys[valid]]))
  result
}

apply_hgnc_mapping <- function(x, hgnc, lookups) {
  x <- data.table::copy(x)
  x[, mapping_symbol := data.table::fifelse(
    !is.na(symbol_original) & nzchar(symbol_original),
    symbol_original,
    gencode_gene_name
  )]
  x[, hgnc_row := NA_integer_]
  x[, mapping_status := "unmapped"]
  x[, mapping_evidence := ""]

  mapped <- lookup_rows(x$ensembl_id_stable, lookups$ensembl$unique)
  hit <- !is.na(mapped)
  x$hgnc_row[hit] <- mapped[hit]
  x$mapping_status[hit] <- "mapped_ensembl"
  x$mapping_evidence[hit] <- paste0(
    "stable_ensembl:", x$ensembl_id_stable[hit]
  )

  for (candidate_name in c("mapping_symbol", "gencode_gene_name")) {
    candidate <- x[[candidate_name]]
    available <- is.na(x$hgnc_row)
    mapped <- lookup_rows(candidate, lookups$current$unique)
    hit <- available & !is.na(mapped)
    x$hgnc_row[hit] <- mapped[hit]
    x$mapping_status[hit] <- "mapped_current_symbol"
    x$mapping_evidence[hit] <- paste0("current_symbol:", candidate[hit])
  }

  for (candidate_name in c("mapping_symbol", "gencode_gene_name")) {
    candidate <- x[[candidate_name]]
    available <- is.na(x$hgnc_row)
    mapped <- lookup_rows(candidate, lookups$previous$unique)
    hit <- available & !is.na(mapped)
    x$hgnc_row[hit] <- mapped[hit]
    x$mapping_status[hit] <- "mapped_previous_symbol"
    x$mapping_evidence[hit] <- paste0("previous_symbol:", candidate[hit])
  }
  previous_ambiguous <- is.na(x$hgnc_row) & (
    x$mapping_symbol %chin% lookups$previous$ambiguous |
      x$gencode_gene_name %chin% lookups$previous$ambiguous
  )
  x$mapping_status[previous_ambiguous] <- "ambiguous_previous_symbol"
  x$mapping_evidence[previous_ambiguous] <- "multiple_HGNC_previous_symbol_targets"

  for (candidate_name in c("mapping_symbol", "gencode_gene_name")) {
    candidate <- x[[candidate_name]]
    available <- is.na(x$hgnc_row) &
      x$mapping_status != "ambiguous_previous_symbol"
    mapped <- lookup_rows(candidate, lookups$alias$unique)
    hit <- available & !is.na(mapped)
    x$hgnc_row[hit] <- mapped[hit]
    x$mapping_status[hit] <- "mapped_alias"
    x$mapping_evidence[hit] <- paste0("alias_symbol:", candidate[hit])
  }
  alias_ambiguous <- is.na(x$hgnc_row) &
    x$mapping_status != "ambiguous_previous_symbol" & (
      x$mapping_symbol %chin% lookups$alias$ambiguous |
        x$gencode_gene_name %chin% lookups$alias$ambiguous
    )
  x$mapping_status[alias_ambiguous] <- "ambiguous_alias"
  x$mapping_evidence[alias_ambiguous] <- "multiple_HGNC_alias_targets"

  idx <- x$hgnc_row
  x[, symbol_hgnc_current := hgnc$symbol[idx]]
  x[, hgnc_id := hgnc$hgnc_id[idx]]
  x[, hgnc_name := hgnc$name[idx]]
  x[, hgnc_status := hgnc$status[idx]]
  x[, hgnc_locus_type := hgnc$locus_type[idx]]
  x[, hgnc_prev_symbols := hgnc$prev_symbol[idx]]
  x[, hgnc_alias_symbols := hgnc$alias_symbol[idx]]
  x[, hgnc_ensembl_gene_id := sub("[.][0-9]+$", "", hgnc$ensembl_gene_id[idx])]
  x[, c("mapping_symbol", "hgnc_row") := NULL]
  x
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("data.table", "yaml")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

suppressPackageStartupMessages(library(data.table))

root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, root)
execution_path <- absolute_path(args$execution_config, root)
must(file.exists(config_path), paste("Config does not exist:", config_path))
must(file.exists(execution_path), paste("Execution config does not exist:", execution_path))

config <- yaml::read_yaml(config_path)
execution_config <- yaml::read_yaml(execution_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", root), mustWork = TRUE
)
phase09_config_path <- absolute_path(
  config$project$phase09_annotation_config %||% "config/phase09_annotation.yml",
  project_root
)
must(file.exists(phase09_config_path), paste(
  "Phase 09 config does not exist:", phase09_config_path
))
phase09 <- yaml::read_yaml(phase09_config_path)
must(
  identical(phase09$schema_version, "phase09_annotation_config_v1"),
  "Unsupported Phase 09 config schema"
)

manifest_path <- absolute_path(config$project$manifest, project_root)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
must(file.exists(manifest_path), "RDS manifest does not exist")
must(file.exists(analysis_path), "Analysis config does not exist")
dir.create(output_root, recursive = TRUE, showWarnings = FALSE)

manifest <- fread(manifest_path)
must(all(c("rds_id", "enabled") %chin% names(manifest)), "Invalid RDS manifest")
manifest <- manifest[as_bool(enabled)]
must(nrow(manifest) > 0L, "No enabled RDS IDs")
rds_ids <- as.character(manifest$rds_id)

execution <- execution_config$execution
execution_stage <- as.character(execution$execution_stage %||% if (
  isTRUE(config$scope$pilot)
) "local_pilot" else "minerva_production")

final_root <- file.path(output_root, "09_annotate_genes")
staging_root <- file.path(
  output_root, paste0(".09_annotate_genes.staging.", Sys.getpid())
)
if (dir.exists(staging_root)) {
  stop("Staging directory already exists: ", staging_root, call. = FALSE)
}

references <- phase09$references
reference_specs <- list(
  gencode = c(path = references$gencode$path, sha256 = references$gencode$sha256),
  mitocarta = c(path = references$mitocarta$path, sha256 = references$mitocarta$sha256),
  hgnc = c(path = references$hgnc$path, sha256 = references$hgnc$sha256),
  extended_source_zip = c(
    path = references$extended_tier$source_zip_path,
    sha256 = references$extended_tier$source_zip_sha256
  ),
  extended_source_gmt = c(
    path = references$extended_tier$source_gmt_path,
    sha256 = references$extended_tier$source_gmt_sha256
  ),
  extended_derived_gmt = c(
    path = references$extended_tier$derived_gmt_path,
    sha256 = references$extended_tier$derived_gmt_sha256
  ),
  extended_manifest = c(
    path = references$extended_tier$manifest_path,
    sha256 = references$extended_tier$manifest_sha256
  )
)
reference_paths <- lapply(reference_specs, function(spec) {
  absolute_path(unname(spec[["path"]]), project_root)
})
reference_hashes <- vapply(names(reference_specs), function(name) {
  path <- reference_paths[[name]]
  expected <- unname(reference_specs[[name]][["sha256"]])
  must(file.exists(path), paste("Required reference does not exist:", path))
  observed <- sha256_file(path)
  must(identical(observed, expected), paste("Reference checksum mismatch:", path))
  observed
}, character(1))

phase03_root <- file.path(output_root, "03_annotations")
phase08_root <- file.path(output_root, "08_mast")
phase03_status_path <- file.path(phase03_root, "annotation_status.tsv")
phase03_manifest_path <- file.path(phase03_root, "annotation_manifest.tsv")
must(file.exists(phase03_status_path), "Phase 03 annotation status is missing")
must(file.exists(phase03_manifest_path), "Phase 03 annotation manifest is missing")
phase03_status <- fread(phase03_status_path)
must(
  nrow(phase03_status) == 1L &&
    identical(phase03_status$validation_status[[1L]], "validated_complete"),
  "Phase 03 is not validated_complete"
)
phase03_artifacts <- fread(phase03_manifest_path)
must(all(phase03_artifacts$validation_status == "validated_complete"),
     "Phase 03 artifact manifest contains invalid rows")
for (i in seq_len(nrow(phase03_artifacts))) {
  artifact_path <- absolute_path(phase03_artifacts$path[[i]], project_root)
  must(file.exists(artifact_path), paste("Missing Phase 03 artifact:", artifact_path))
  must(
    identical(sha256_file(artifact_path), phase03_artifacts$sha256[[i]]),
    paste("Phase 03 artifact checksum mismatch:", artifact_path)
  )
}

phase08_status_paths <- file.path(
  phase08_root, paste0(rds_ids, ".yu_mast_de_status.tsv")
)
phase08_artifact_paths <- file.path(
  phase08_root, paste0(rds_ids, ".yu_mast_de_artifacts.tsv")
)
phase08_de_paths <- file.path(
  phase08_root, paste0(rds_ids, ".yu_mast_de.tsv.gz")
)
phase08_manifest_paths <- file.path(
  phase08_root, paste0(rds_ids, ".yu_mast_contrast_manifest.tsv")
)
phase08_contrast_status_paths <- file.path(
  phase08_root, paste0(rds_ids, ".yu_mast_contrast_status.tsv")
)
all_phase08_paths <- c(
  phase08_status_paths, phase08_artifact_paths, phase08_de_paths,
  phase08_manifest_paths, phase08_contrast_status_paths
)
must(all(file.exists(all_phase08_paths)), "One or more required Phase 08 files are missing")

phase08_status <- rbindlist(lapply(phase08_status_paths, fread), fill = TRUE)
must(all(phase08_status$schema_version == "yu_mast_de_status_v2"),
     "Unexpected Phase 08 status schema")
must(all(phase08_status$validation_status == "validated_complete"),
     "One or more Phase 08 tasks are not validated_complete")
must(all(phase08_status$failed_contrasts == 0L), "Phase 08 has failed contrasts")

phase08_artifacts <- rbindlist(lapply(phase08_artifact_paths, fread), fill = TRUE)
must(all(phase08_artifacts$validation_status == "validated_complete"),
     "Phase 08 artifact manifest contains invalid rows")
for (i in seq_len(nrow(phase08_artifacts))) {
  artifact_path <- absolute_path(phase08_artifacts$path[[i]], project_root)
  must(file.exists(artifact_path), paste("Missing Phase 08 artifact:", artifact_path))
  must(
    identical(sha256_file(artifact_path), phase08_artifacts$sha256[[i]]),
    paste("Phase 08 artifact checksum mismatch:", artifact_path)
  )
}

controller_paths <- file.path(
  output_root, "status", paste0("mast__", rds_ids, ".tsv")
)
must(all(file.exists(controller_paths)), "A Phase 08 controller status is missing")
controller_status <- rbindlist(lapply(controller_paths, fread), fill = TRUE)
must(all(controller_status$validation_status == "validated_complete"),
     "A Phase 08 controller is not validated_complete")
must(all(controller_status$exit_code == 0L), "A Phase 08 controller has nonzero exit code")

phase03_status_sha <- sha256_file(phase03_status_path)
phase03_manifest_sha <- sha256_file(phase03_manifest_path)
phase08_status_sha <- paste(
  paste(rds_ids, vapply(phase08_status_paths, sha256_file, character(1)), sep = "="),
  collapse = ";"
)
phase08_artifacts_sha <- paste(
  paste(rds_ids, vapply(phase08_artifact_paths, sha256_file, character(1)), sep = "="),
  collapse = ";"
)

current_hashes <- list(
  scientific_script_sha256 = sha256_file(file.path(project_root, "scripts/09_annotate_mitochondrial_genes.R")),
  scientific_config_sha256 = sha256_file(phase09_config_path),
  pipeline_config_sha256 = sha256_file(config_path),
  analysis_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  phase03_status_sha256 = phase03_status_sha,
  phase03_manifest_sha256 = phase03_manifest_sha,
  phase08_status_sha256 = phase08_status_sha,
  phase08_artifacts_sha256 = phase08_artifacts_sha
)

if (dir.exists(final_root)) {
  existing_status_path <- file.path(final_root, "annotation_status.tsv")
  existing_artifacts_path <- file.path(final_root, "annotation_artifacts.tsv")
  can_resume <- file.exists(existing_status_path) && file.exists(existing_artifacts_path)
  if (can_resume) {
    existing_status <- fread(existing_status_path)
    can_resume <- nrow(existing_status) == 1L &&
      existing_status$validation_status[[1L]] == "validated_complete"
    for (field in names(current_hashes)) {
      can_resume <- can_resume && field %chin% names(existing_status) &&
        identical(as.character(existing_status[[field]][[1L]]), current_hashes[[field]])
    }
    if (can_resume) {
      existing_artifacts <- fread(existing_artifacts_path)
      for (i in seq_len(nrow(existing_artifacts))) {
        path <- absolute_path(existing_artifacts$path[[i]], project_root)
        can_resume <- can_resume && file.exists(path) &&
          identical(sha256_file(path), existing_artifacts$sha256[[i]]) &&
          file.info(path)$size == existing_artifacts$bytes[[i]] &&
          existing_artifacts$validation_status[[i]] == "validated_complete"
      }
    }
  }
  if (can_resume) {
    cat("Resume: validated Phase 09 output is current; skipping rebuild\n")
    quit(status = 0L)
  }
  stop(
    "Phase 09 output exists but is not a current validated bundle: ", final_root,
    call. = FALSE
  )
}

dir.create(staging_root, recursive = FALSE, showWarnings = FALSE)
published <- FALSE
on.exit({
  if (!published && dir.exists(staging_root)) {
    unlink(staging_root, recursive = TRUE, force = TRUE)
  }
}, add = TRUE)

universe_path <- file.path(phase03_root, "tested_gene_universe.tsv")
gencode_table_path <- file.path(phase03_root, "gencode_gene_annotation.tsv")
mitocarta_table_path <- file.path(phase03_root, "mitocarta_measured_genes.tsv")
must(all(file.exists(c(universe_path, gencode_table_path, mitocarta_table_path))),
     "Required Phase 03 annotation tables are missing")
universe <- fread(universe_path)
gencode <- fread(gencode_table_path)
mitocarta <- fread(mitocarta_table_path)
must(!anyDuplicated(universe[, .(rds_id, feature)]),
     "Phase 03 universe contains duplicate RDS-feature keys")
must(setequal(unique(universe$rds_id), rds_ids),
     "Phase 03 universe RDS IDs differ from the enabled manifest")
must(all(mitocarta$rds_id %chin% rds_ids), "Unexpected RDS ID in MitoCarta table")

hgnc <- fread(reference_paths$hgnc)
required_hgnc_columns <- unlist(references$hgnc$required_columns, use.names = FALSE)
must(all(required_hgnc_columns %chin% names(hgnc)), "HGNC required columns are missing")
must(nrow(hgnc) == as.integer(references$hgnc$expected_rows),
     "HGNC row count differs from the frozen expectation")
must(!anyDuplicated(hgnc$hgnc_id), "HGNC IDs are not unique")
hgnc[, hgnc_row := .I]
hgnc[, ensembl_gene_id := sub("[.][0-9]+$", "", ensembl_gene_id)]
hgnc_approved <- hgnc[status == "Approved"]

lookups <- list(
  ensembl = build_lookup(hgnc_approved[, .(key = ensembl_gene_id, hgnc_row)]),
  current = build_lookup(hgnc_approved[, .(key = symbol, hgnc_row)]),
  previous = build_lookup(explode_hgnc_field(
    hgnc_approved$prev_symbol, hgnc_approved$hgnc_row
  )),
  alias = build_lookup(explode_hgnc_field(
    hgnc_approved$alias_symbol, hgnc_approved$hgnc_row
  ))
)

mitocarta[, canonical_symbol_source := canonical_symbol]
mitocarta_current_rows <- lookup_rows(
  mitocarta$canonical_symbol_source, lookups$current$unique
)
mitocarta_previous_rows <- lookup_rows(
  mitocarta$canonical_symbol_source, lookups$previous$unique
)
mitocarta_alias_rows <- lookup_rows(
  mitocarta$canonical_symbol_source, lookups$alias$unique
)
mitocarta_hgnc_rows <- mitocarta_current_rows
use_previous <- is.na(mitocarta_hgnc_rows) & !is.na(mitocarta_previous_rows)
mitocarta_hgnc_rows[use_previous] <- mitocarta_previous_rows[use_previous]
use_alias <- is.na(mitocarta_hgnc_rows) & !is.na(mitocarta_alias_rows)
mitocarta_hgnc_rows[use_alias] <- mitocarta_alias_rows[use_alias]
mitocarta[, canonical_symbol_hgnc := hgnc$symbol[mitocarta_hgnc_rows]]

extended_manifest <- fread(reference_paths$extended_manifest)
must(nrow(extended_manifest) == 4L, "Extended manifest must contain four rows")
must(all(extended_manifest$validation_status == "validated_complete"),
     "Extended manifest is not validated_complete")
gmt_lines <- readLines(reference_paths$extended_derived_gmt, warn = FALSE)
gmt_fields <- strsplit(gmt_lines, "\t", fixed = TRUE)
must(length(gmt_fields) == 4L && all(lengths(gmt_fields) >= 3L),
     "Derived extended-tier GMT is malformed")
extended_ids <- vapply(gmt_fields, `[[`, character(1), 2L)
expected_extended_ids <- unlist(references$extended_tier$stable_ids, use.names = FALSE)
must(setequal(extended_ids, expected_extended_ids),
     "Extended-tier stable IDs differ from configuration")
extended_genes <- sort(unique(unlist(lapply(gmt_fields, function(fields) {
  fields[-c(1L, 2L)]
}), use.names = FALSE)))
must(length(extended_genes) == as.integer(references$extended_tier$expected_union_genes),
     "Extended-tier union gene count differs from configuration")
must(all(extended_genes %chin% hgnc_approved$symbol),
     "An extended-tier symbol is not an approved current HGNC symbol")

mitocarta_source_symbols <- sort(unique(mitocarta$canonical_symbol_source))
mitocarta_hgnc_symbols <- sort(unique(na.omit(mitocarta$canonical_symbol_hgnc)))
must(length(mitocarta_source_symbols) == as.integer(phase09$expected$mitocarta_genes),
     "MitoCarta canonical gene count differs from configuration")
extended_core <- intersect(extended_genes, mitocarta_hgnc_symbols)
extended_only <- setdiff(extended_genes, mitocarta_hgnc_symbols)
must(length(extended_core) == as.integer(references$extended_tier$expected_mitocarta_core_genes),
     "Extended-tier MitoCarta overlap differs from configuration")
must(length(extended_only) == as.integer(references$extended_tier$expected_extended_only_genes),
     "Extended-only gene count differs from configuration")

mt_chromosome <- phase09$annotation[["mtDNA_chromosome"]]
mt_noncoding_types <- unlist(
  phase09$annotation[["mtDNA_noncoding_gene_types"]], use.names = FALSE
)
mtdna_genes <- unique(gencode[chromosome == mt_chromosome])
must(nrow(mtdna_genes) == as.integer(phase09$expected$conventional_mtDNA_genes),
     "Conventional mtDNA gene count differs from configuration")
must(nrow(mtdna_genes[gene_type == "protein_coding"]) ==
       as.integer(phase09$expected$mtDNA_protein_coding_genes),
     "mtDNA protein-coding count differs from configuration")
must(nrow(mtdna_genes[gene_type == "Mt_tRNA"]) ==
       as.integer(phase09$expected$mtDNA_tRNA_genes),
     "mtDNA tRNA count differs from configuration")
must(nrow(mtdna_genes[gene_type == "Mt_rRNA"]) ==
       as.integer(phase09$expected$mtDNA_rRNA_genes),
     "mtDNA rRNA count differs from configuration")

gencode_symbol_counts <- gencode[, .N, by = gene_name]
gencode_unique_symbols <- gencode[
  gene_name %chin% gencode_symbol_counts[N == 1L, gene_name]
]
symbol_to_ensembl <- setNames(gencode_unique_symbols$gene_id, gencode_unique_symbols$gene_name)
symbol_to_chromosome <- setNames(gencode_unique_symbols$chromosome, gencode_unique_symbols$gene_name)
symbol_to_gene_type <- setNames(gencode_unique_symbols$gene_type, gencode_unique_symbols$gene_name)
gencode_id_counts <- gencode[, .N, by = gene_id]
gencode_unique_ids <- gencode[gene_id %chin% gencode_id_counts[N == 1L, gene_id]]
ensembl_to_chromosome <- setNames(gencode_unique_ids$chromosome, gencode_unique_ids$gene_id)
ensembl_to_gene_type <- setNames(gencode_unique_ids$gene_type, gencode_unique_ids$gene_id)
mitocarta_symbol_map <- unique(mitocarta[, .(
  mitocarta_canonical_symbol = canonical_symbol_source,
  mitocarta_hgnc_symbol = canonical_symbol_hgnc
)])

master_list <- list()
for (current_rds_id in rds_ids) {
  u <- universe[rds_id == current_rds_id]
  m <- mitocarta[rds_id == current_rds_id]
  assay <- u[, .(
    rds_id,
    feature_index = as.integer(feature_index),
    feature_id_original = as.character(feature),
    reference_only_id = NA_character_,
    reference_only = FALSE,
    reference_source = "assay_feature",
    symbol_original = as.character(feature),
    ensembl_id_versioned = data.table::fifelse(
      grepl("^ENSG[0-9]+[.][0-9]+$", feature), feature, NA_character_
    ),
    ensembl_id_stable = sub("[.][0-9]+$", "", as.character(gencode_gene_id)),
    gencode_gene_name = as.character(gencode_gene_name),
    chromosome = as.character(chromosome),
    gene_type = as.character(gene_type),
    phase03_gencode_match_type = as.character(gencode_match_type),
    mitocarta_symbol_input = as.character(mitocarta_symbol),
    phase03_mitocarta_match_type = as.character(mitocarta_match_type),
    total_raw_counts = as.numeric(total_raw_counts),
    nuclei_detected = as.integer(nuclei_detected),
    measured = TRUE,
    test_eligible = as_bool(test_eligible),
    test_exclusion_reason = as.character(test_exclusion_reason)
  )]

  represented_mito <- unique(na.omit(u$mitocarta_symbol))
  represented_mtdna <- unique(na.omit(u[chromosome == mt_chromosome, gencode_gene_name]))
  represented_mito_hgnc <- mitocarta_symbol_map[
    mitocarta_canonical_symbol %chin% represented_mito,
    mitocarta_hgnc_symbol
  ]
  represented_symbols <- unique(c(
    u$feature, u$gencode_gene_name, represented_mito_hgnc
  ))
  missing_mito <- setdiff(m$canonical_symbol, represented_mito)
  missing_mtdna <- setdiff(mtdna_genes$gene_name, represented_mtdna)
  missing_extended <- setdiff(extended_genes, represented_symbols)
  reference_symbols <- sort(unique(c(missing_mito, missing_mtdna, missing_extended)))

  if (length(reference_symbols)) {
    refs <- data.table(
      rds_id = current_rds_id,
      feature_index = NA_integer_,
      feature_id_original = NA_character_,
      reference_only_id = paste0("reference:", reference_symbols),
      reference_only = TRUE,
      reference_source = fcase(
        reference_symbols %chin% missing_mito, "MitoCarta3.0",
        reference_symbols %chin% missing_mtdna, "GENCODE_chrM",
        default = "Reactome_V97_extended"
      ),
      symbol_original = reference_symbols,
      ensembl_id_versioned = NA_character_,
      ensembl_id_stable = unname(symbol_to_ensembl[reference_symbols]),
      gencode_gene_name = reference_symbols,
      chromosome = unname(symbol_to_chromosome[reference_symbols]),
      gene_type = unname(symbol_to_gene_type[reference_symbols]),
      phase03_gencode_match_type = "reference_only",
      mitocarta_symbol_input = data.table::fifelse(
        reference_symbols %chin% mitocarta_source_symbols, reference_symbols, NA_character_
      ),
      phase03_mitocarta_match_type = data.table::fifelse(
        reference_symbols %chin% mitocarta_source_symbols, "reference_only", "unmatched"
      ),
      total_raw_counts = NA_real_,
      nuclei_detected = NA_integer_,
      measured = FALSE,
      test_eligible = FALSE,
      test_exclusion_reason = "reference_only_not_in_expression_matrix"
    )
    assay <- rbindlist(list(assay, refs), use.names = TRUE, fill = TRUE)
  }
  master_list[[current_rds_id]] <- assay
}
master <- rbindlist(master_list, use.names = TRUE, fill = TRUE)
master <- apply_hgnc_mapping(master, hgnc, lookups)

fill_ensembl <- is.na(master$ensembl_id_stable) &
  !is.na(master$hgnc_ensembl_gene_id)
master$ensembl_id_stable[fill_ensembl] <- master$hgnc_ensembl_gene_id[fill_ensembl]
fill_chromosome <- is.na(master$chromosome) & !is.na(master$ensembl_id_stable)
master$chromosome[fill_chromosome] <- unname(
  ensembl_to_chromosome[master$ensembl_id_stable[fill_chromosome]]
)
fill_gene_type <- is.na(master$gene_type) & !is.na(master$ensembl_id_stable)
master$gene_type[fill_gene_type] <- unname(
  ensembl_to_gene_type[master$ensembl_id_stable[fill_gene_type]]
)

normalized_to_source <- mitocarta_symbol_map[
  !is.na(mitocarta_hgnc_symbol),
  .(mitocarta_canonical_symbol = first(mitocarta_canonical_symbol)),
  by = mitocarta_hgnc_symbol
]
master[, mitocarta_canonical_symbol := fcase(
  !is.na(mitocarta_symbol_input) & nzchar(mitocarta_symbol_input),
  mitocarta_symbol_input,
  symbol_hgnc_current %chin% normalized_to_source$mitocarta_hgnc_symbol,
  normalized_to_source$mitocarta_canonical_symbol[
    match(symbol_hgnc_current, normalized_to_source$mitocarta_hgnc_symbol)
  ],
  symbol_original %chin% mitocarta_source_symbols,
  symbol_original,
  default = NA_character_
)]
master[, mitocarta_hgnc_symbol := mitocarta_symbol_map$mitocarta_hgnc_symbol[
  match(mitocarta_canonical_symbol, mitocarta_symbol_map$mitocarta_canonical_symbol)
]]
master[, is_mitocarta3 := !is.na(mitocarta_canonical_symbol)]

localization_lookup <- unique(mitocarta[, .(
  rds_id, mitocarta_canonical_symbol = canonical_symbol,
  sub_mito_localization = as.character(sub_mito_localization)
)])
master <- localization_lookup[master, on = .(rds_id, mitocarta_canonical_symbol)]
master[, is_mtDNA_gene := !is.na(chromosome) & chromosome == mt_chromosome]
master[, extended_reference_member := (
  symbol_hgnc_current %chin% extended_genes |
    symbol_original %chin% extended_genes
)]
master[, mito_tier := fcase(
  is_mitocarta3, "core_mito_protein",
  is_mtDNA_gene & gene_type %chin% mt_noncoding_types, "mtdna_noncoding",
  extended_reference_member, "mito_extended",
  default = "non_mito"
)]
master[, genome_origin := fcase(
  is_mtDNA_gene, "mtDNA",
  !is.na(chromosome) | is_mitocarta3 | extended_reference_member, "nuclear",
  default = "unknown"
)]
master[, extended_annotation_status := "evaluated_reactome_v97"]
master[, schema_version := phase09$schemas$master]
setcolorder(master, c(
  "schema_version", "rds_id", "feature_index", "feature_id_original",
  "reference_only_id", "reference_only", "reference_source",
  "symbol_original", "ensembl_id_versioned", "ensembl_id_stable",
  "symbol_hgnc_current", "hgnc_id", "hgnc_name", "hgnc_status",
  "hgnc_locus_type", "hgnc_prev_symbols", "hgnc_alias_symbols",
  "hgnc_ensembl_gene_id", "mapping_status", "mapping_evidence",
  "gencode_gene_name", "chromosome", "gene_type",
  "phase03_gencode_match_type", "mitocarta_canonical_symbol",
  "mitocarta_hgnc_symbol",
  "phase03_mitocarta_match_type", "is_mitocarta3", "is_mtDNA_gene",
  "mito_tier", "genome_origin", "sub_mito_localization",
  "extended_reference_member", "extended_annotation_status", "measured",
  "test_eligible", "test_exclusion_reason", "total_raw_counts",
  "nuclei_detected", "mitocarta_symbol_input"
))
setorder(master, rds_id, reference_only, feature_index, reference_only_id)

hgnc_meta <- hgnc_approved[, .(
  canonical_symbol = symbol,
  hgnc_id,
  ensembl_id_stable = ensembl_gene_id
)]
reference_inventory_list <- list()
for (current_rds_id in rds_ids) {
  m <- copy(mitocarta[rds_id == current_rds_id])
  core <- m[, .(
    schema_version = phase09$schemas$reference_inventory,
    rds_id,
    canonical_symbol = canonical_symbol_source,
    symbol_hgnc_current = canonical_symbol_hgnc,
    reference_class = "core_mito_protein",
    sub_mito_localization = as.character(sub_mito_localization),
    mapped_feature = as.character(mapped_feature),
    measured = as_bool(measured),
    test_eligible = as_bool(tested)
  )]
  core[, hgnc_id := hgnc_approved$hgnc_id[
    match(symbol_hgnc_current, hgnc_approved$symbol)
  ]]
  core[, ensembl_id_stable := hgnc_approved$ensembl_gene_id[
    match(symbol_hgnc_current, hgnc_approved$symbol)
  ]]
  core[, chromosome := unname(ensembl_to_chromosome[ensembl_id_stable])]
  core[, gene_type := unname(ensembl_to_gene_type[ensembl_id_stable])]

  u <- universe[rds_id == current_rds_id]
  noncoding_ref <- mtdna_genes[gene_type %chin% mt_noncoding_types]
  mapped_by_symbol <- u[
    gencode_gene_name %chin% noncoding_ref$gene_name,
    .SD[1L], by = gencode_gene_name
  ]
  noncoding <- noncoding_ref[, .(
    schema_version = phase09$schemas$reference_inventory,
    rds_id = current_rds_id,
    canonical_symbol = gene_name,
    symbol_hgnc_current = gene_name,
    reference_class = "mtdna_noncoding",
    hgnc_id = hgnc_approved$hgnc_id[match(gene_name, hgnc_approved$symbol)],
    ensembl_id_stable = gene_id,
    chromosome,
    gene_type,
    sub_mito_localization = NA_character_,
    mapped_feature = mapped_by_symbol$feature[match(gene_name, mapped_by_symbol$gencode_gene_name)],
    measured = gene_name %chin% mapped_by_symbol$gencode_gene_name,
    test_eligible = as_bool(mapped_by_symbol$test_eligible[
      match(gene_name, mapped_by_symbol$gencode_gene_name)
    ])
  )]
  setcolorder(core, names(noncoding))
  reference_inventory_list[[current_rds_id]] <- rbindlist(
    list(core, noncoding), use.names = TRUE, fill = TRUE
  )
}
reference_inventory <- rbindlist(reference_inventory_list, use.names = TRUE)
setorder(reference_inventory, rds_id, reference_class, canonical_symbol)

de <- rbindlist(lapply(phase08_de_paths, fread), use.names = TRUE, fill = TRUE)
contrast_manifest <- rbindlist(
  lapply(phase08_manifest_paths, fread), use.names = TRUE, fill = TRUE
)
contrast_status <- rbindlist(
  lapply(phase08_contrast_status_paths, fread), use.names = TRUE, fill = TRUE
)
must(all(de$schema_version == "yu_mast_de_results_v2"),
     "Unexpected Phase 08 result schema")
must(!anyDuplicated(de[, .(rds_id, contrast_id, gene)]),
     "Phase 08 returned rows have duplicate keys")
must(!any(contrast_status$terminal_status == "failed"),
     "Phase 08 contrast status contains a failure")
must(all(contrast_status$terminal_status %chin% c(
  "validated_complete", "not_estimable"
)), "Unexpected Phase 08 contrast terminal status")

contrast_status_keep <- contrast_status[, .(
  rds_id, contrast_id, terminal_status,
  contrast_genes_returned = genes_returned,
  contrast_paper_degs = paper_degs,
  contrast_cells_ad = cells_ad,
  contrast_cells_nci = cells_nci,
  contrast_donors_ad = donors_ad,
  contrast_donors_nci = donors_nci,
  contrast_status_message = message
)]
contrast_meta <- merge(
  contrast_manifest, contrast_status_keep,
  by = c("rds_id", "contrast_id"), all.x = TRUE, sort = FALSE
)
must(nrow(contrast_meta) == nrow(contrast_manifest),
     "Contrast status did not join one-to-one to the manifest")

grid_master <- copy(master)
grid_master[, schema_version := NULL]
contrast_meta[, schema_version := NULL]
grid <- merge(
  contrast_meta, grid_master, by = "rds_id", allow.cartesian = TRUE,
  sort = FALSE
)

de_stats <- de[, .(
  rds_id, contrast_id, feature_id_original = gene,
  phase08_result_schema_version = schema_version,
  source_rds, normalized_rds, logFC, pct_ad, pct_nci, p_value,
  p_val_adj_bonferroni, fdr_bh_within_contrast,
  paper_effect_threshold_log2, paper_deg,
  cells_ad, cells_nci, donors_ad, donors_nci, latent_vars,
  phase08_row_present = TRUE
)]
annotated <- merge(
  grid, de_stats,
  by = c("rds_id", "contrast_id", "feature_id_original"),
  all.x = TRUE, sort = FALSE
)
annotated[is.na(phase08_row_present), phase08_row_present := FALSE]
annotated[, tested_status := "present_but_filtered_min_pct"]
annotated[reference_only == TRUE, tested_status := "not_in_expression_matrix"]
annotated[phase08_row_present & !paper_deg,
          tested_status := "tested_not_significant"]
annotated[phase08_row_present & paper_deg & logFC > 0,
          tested_status := "significant_up"]
annotated[phase08_row_present & paper_deg & logFC < 0,
          tested_status := "significant_down"]
annotated[terminal_status == "not_estimable",
          tested_status := "contrast_not_estimable"]
annotated[, deg_state := NA_integer_]
annotated[phase08_row_present & !paper_deg, deg_state := 0L]
annotated[phase08_row_present & paper_deg & logFC > 0, deg_state := 1L]
annotated[phase08_row_present & paper_deg & logFC < 0, deg_state := -1L]
annotated[, schema_version := phase09$schemas$annotated_results]
setcolorder(annotated, c(
  "schema_version", "rds_id", "contrast_id", "manifest_row",
  "cell_type_high_resolution", "sex", "apoe_group", "yu_stratum",
  "yu_contrast", "contrast_family", "contrast_name", "contrast_kind",
  "numerator", "denominator", "analysis_population", "terminal_status",
  "feature_id_original", "reference_only_id", "reference_only",
  "symbol_hgnc_current", "hgnc_id", "ensembl_id_stable", "mito_tier",
  "genome_origin", "sub_mito_localization", "mapping_status",
  "measured", "test_eligible", "tested_status", "deg_state",
  "phase08_row_present"
))
setorder(annotated, rds_id, manifest_row, reference_only, feature_index, reference_only_id)

deg_mito_core <- annotated[mito_tier == "core_mito_protein"]
mtdna_noncoding_results <- annotated[mito_tier == "mtdna_noncoding"]
unresolved <- master[mapping_status %chin% c(
  "ambiguous_previous_symbol", "ambiguous_alias", "unmapped"
)]

qc_summary_rows <- list()
add_qc_metric <- function(scope, rds_id, metric, value) {
  qc_summary_rows[[length(qc_summary_rows) + 1L]] <<- data.table(
    schema_version = phase09$schemas$qc,
    scope = scope,
    rds_id = rds_id,
    metric = metric,
    value = as.numeric(value),
    validation_status = "validated_complete"
  )
}
for (current_rds_id in rds_ids) {
  m <- master[rds_id == current_rds_id]
  a <- annotated[rds_id == current_rds_id]
  add_qc_metric("rds", current_rds_id, "assay_features", nrow(m[reference_only == FALSE]))
  add_qc_metric("rds", current_rds_id, "reference_only_records", nrow(m[reference_only == TRUE]))
  add_qc_metric("rds", current_rds_id, "mitocarta_core_records", nrow(m[mito_tier == "core_mito_protein"]))
  add_qc_metric("rds", current_rds_id, "mtdna_noncoding_records", nrow(m[mito_tier == "mtdna_noncoding"]))
  add_qc_metric("rds", current_rds_id, "extended_tier_records", nrow(m[mito_tier == "mito_extended"]))
  add_qc_metric("rds", current_rds_id, "contrast_rows", uniqueN(a$contrast_id))
  add_qc_metric("rds", current_rds_id, "annotated_grid_rows", nrow(a))
  add_qc_metric("rds", current_rds_id, "phase08_returned_rows", sum(a$phase08_row_present))
  add_qc_metric("rds", current_rds_id, "significant_up", sum(a$tested_status == "significant_up"))
  add_qc_metric("rds", current_rds_id, "significant_down", sum(a$tested_status == "significant_down"))
  add_qc_metric("rds", current_rds_id, "filtered_rows", sum(a$tested_status == "present_but_filtered_min_pct"))
}
qc_summary <- rbindlist(qc_summary_rows)
qc_by_contrast <- annotated[, .(
  schema_version = phase09$schemas$qc,
  total_rows = .N,
  assay_feature_rows = sum(!reference_only),
  reference_only_rows = sum(reference_only),
  phase08_returned_rows = sum(phase08_row_present),
  filtered_rows = sum(tested_status == "present_but_filtered_min_pct"),
  tested_not_significant = sum(tested_status == "tested_not_significant"),
  significant_up = sum(tested_status == "significant_up"),
  significant_down = sum(tested_status == "significant_down"),
  not_in_expression_matrix = sum(tested_status == "not_in_expression_matrix"),
  contrast_not_estimable = sum(tested_status == "contrast_not_estimable"),
  mitocarta_core_rows = sum(mito_tier == "core_mito_protein"),
  mtdna_noncoding_rows = sum(mito_tier == "mtdna_noncoding"),
  extended_tier_rows = sum(mito_tier == "mito_extended")
), by = .(
  rds_id, manifest_row, contrast_id, cell_type_high_resolution,
  sex, apoe_group, yu_stratum, terminal_status
)]
setcolorder(qc_by_contrast, c("schema_version", setdiff(
  names(qc_by_contrast), "schema_version"
)))

checks_list <- list()
add_check <- function(check_name, passed, observed, expected, details = "") {
  checks_list[[length(checks_list) + 1L]] <<- data.table(
    schema_version = phase09$schemas$checks,
    check_name = check_name,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    details = details
  )
}

for (name in names(reference_specs)) {
  add_check(
    paste0("reference_checksum_", name),
    identical(reference_hashes[[name]], unname(reference_specs[[name]][["sha256"]])),
    reference_hashes[[name]], unname(reference_specs[[name]][["sha256"]])
  )
}
add_check("phase03_validated", all(phase03_status$validation_status == "validated_complete"),
          phase03_status$validation_status, "validated_complete")
add_check("phase08_validated", all(phase08_status$validation_status == "validated_complete"),
          paste(unique(phase08_status$validation_status), collapse = ","), "validated_complete")
add_check("hgnc_rows", nrow(hgnc) == as.integer(references$hgnc$expected_rows),
          nrow(hgnc), references$hgnc$expected_rows)
add_check("mitocarta_genes", length(mitocarta_source_symbols) == as.integer(phase09$expected$mitocarta_genes),
          length(mitocarta_source_symbols), phase09$expected$mitocarta_genes)
add_check("conventional_mtdna_genes", nrow(mtdna_genes) == as.integer(phase09$expected$conventional_mtDNA_genes),
          nrow(mtdna_genes), phase09$expected$conventional_mtDNA_genes)
add_check("extended_union_genes", length(extended_genes) == as.integer(references$extended_tier$expected_union_genes),
          length(extended_genes), references$extended_tier$expected_union_genes)
add_check("extended_core_genes", length(extended_core) == as.integer(references$extended_tier$expected_mitocarta_core_genes),
          length(extended_core), references$extended_tier$expected_mitocarta_core_genes)
add_check("extended_only_genes", length(extended_only) == as.integer(references$extended_tier$expected_extended_only_genes),
          length(extended_only), references$extended_tier$expected_extended_only_genes)
add_check(
  "no_redundant_reactome_core_reference_records",
  nrow(master[
    reference_source == "Reactome_V97_extended" &
      mito_tier == "core_mito_protein"
  ]) == 0L,
  nrow(master[
    reference_source == "Reactome_V97_extended" &
      mito_tier == "core_mito_protein"
  ]),
  0
)
add_check("master_assay_feature_keys_unique",
          !anyDuplicated(master[reference_only == FALSE, .(rds_id, feature_id_original)]),
          anyDuplicated(master[reference_only == FALSE, .(rds_id, feature_id_original)]), 0)
add_check("master_reference_keys_unique",
          !anyDuplicated(master[reference_only == TRUE, .(rds_id, reference_only_id)]),
          anyDuplicated(master[reference_only == TRUE, .(rds_id, reference_only_id)]), 0)
add_check("mapping_status_allowed",
          all(master$mapping_status %chin% unlist(phase09$annotation$allowed_mapping_status)),
          paste(sort(unique(master$mapping_status)), collapse = ","),
          paste(unlist(phase09$annotation$allowed_mapping_status), collapse = ","))
add_check("annotated_keys_unique",
          !anyDuplicated(annotated[, .(rds_id, contrast_id, feature_id_original, reference_only_id)]),
          anyDuplicated(annotated[, .(rds_id, contrast_id, feature_id_original, reference_only_id)]), 0)
add_check("tested_status_allowed",
          all(annotated$tested_status %chin% unlist(phase09$annotation$allowed_tested_status)),
          paste(sort(unique(annotated$tested_status)), collapse = ","),
          paste(unlist(phase09$annotation$allowed_tested_status), collapse = ","))
add_check("phase08_rows_preserved_once", sum(annotated$phase08_row_present) == nrow(de),
          sum(annotated$phase08_row_present), nrow(de))
add_check("phase08_genes_in_master", all(de$gene %chin% master[reference_only == FALSE, feature_id_original]),
          length(setdiff(unique(de$gene), master[reference_only == FALSE, feature_id_original])), 0)

preservation_columns <- c(
  "logFC", "pct_ad", "pct_nci", "p_value", "p_val_adj_bonferroni",
  "fdr_bh_within_contrast", "paper_effect_threshold_log2", "paper_deg",
  "cells_ad", "cells_nci", "donors_ad", "donors_nci"
)
preserved <- annotated[phase08_row_present == TRUE]
setorder(preserved, rds_id, contrast_id, feature_id_original)
original <- copy(de)
setorder(original, rds_id, contrast_id, gene)
preservation_ok <- nrow(preserved) == nrow(original) && all(vapply(
  preservation_columns,
  function(column) isTRUE(all.equal(
    preserved[[column]], original[[column]], check.attributes = FALSE
  )),
  logical(1)
))
add_check("phase08_statistics_preserved", preservation_ok,
          preservation_ok, TRUE)
add_check("mito_core_subset_exact",
          nrow(deg_mito_core) == nrow(annotated[mito_tier == "core_mito_protein"]),
          nrow(deg_mito_core), nrow(annotated[mito_tier == "core_mito_protein"]))
add_check("mtdna_noncoding_subset_exact",
          nrow(mtdna_noncoding_results) == nrow(annotated[mito_tier == "mtdna_noncoding"]),
          nrow(mtdna_noncoding_results), nrow(annotated[mito_tier == "mtdna_noncoding"]))
add_check("reference_inventory_per_rds",
          all(reference_inventory[, .N, by = rds_id]$N ==
                as.integer(phase09$expected$mitocarta_genes) +
                as.integer(phase09$expected$mtDNA_tRNA_genes) +
                as.integer(phase09$expected$mtDNA_rRNA_genes)),
          paste(reference_inventory[, .N, by = rds_id]$N, collapse = ","),
          as.integer(phase09$expected$mitocarta_genes) + 24L)

if (isTRUE(config$scope$pilot)) {
  add_check("local_pilot_assay_features",
            nrow(master[reference_only == FALSE]) == as.integer(phase09$expected$local_pilot_features),
            nrow(master[reference_only == FALSE]), phase09$expected$local_pilot_features)
  add_check("local_pilot_contrasts",
            uniqueN(annotated$contrast_id) == as.integer(phase09$expected$local_pilot_contrasts),
            uniqueN(annotated$contrast_id), phase09$expected$local_pilot_contrasts)
}

control_expectations <- list(
  `MT-ND2` = list(origin = "mtDNA", tier = "core_mito_protein"),
  NDUFS1 = list(origin = "nuclear", tier = "core_mito_protein"),
  SDHA = list(origin = "nuclear", tier = "core_mito_protein"),
  COX5A = list(origin = "nuclear", tier = "core_mito_protein"),
  ATP5F1A = list(origin = "nuclear", tier = "core_mito_protein"),
  TFAM = list(origin = "nuclear", tier = "core_mito_protein"),
  TOMM20 = list(origin = "nuclear", tier = "core_mito_protein"),
  PINK1 = list(origin = "nuclear", tier = "core_mito_protein")
)
for (gene in names(control_expectations)) {
  rows <- master[symbol_hgnc_current == gene | symbol_original == gene]
  expectation <- control_expectations[[gene]]
  passed <- nrow(rows) > 0L && all(rows$genome_origin == expectation$origin) &&
    all(rows$mito_tier == expectation$tier)
  add_check(
    paste0("positive_control_", gene), passed,
    if (nrow(rows)) paste(unique(paste(rows$genome_origin, rows$mito_tier, sep = ":")), collapse = ",") else "absent",
    paste(expectation$origin, expectation$tier, sep = ":")
  )
}
tomm20 <- master[symbol_hgnc_current == "TOMM20" | symbol_original == "TOMM20"]
add_check("positive_control_TOMM20_localization",
          nrow(tomm20) > 0L && any(
            tomm20$sub_mito_localization == "MOM" |
              grepl("Outer", tomm20$sub_mito_localization, ignore.case = TRUE),
            na.rm = TRUE
          ),
          paste(unique(tomm20$sub_mito_localization), collapse = ","),
          "MOM_or_contains_Outer")
mtrnr2l8 <- master[symbol_hgnc_current == "MTRNR2L8" | symbol_original == "MTRNR2L8"]
add_check("negative_control_MTRNR2L8_not_mtdna",
          nrow(mtrnr2l8) > 0L && all(!mtrnr2l8$is_mtDNA_gene) && all(mtrnr2l8$genome_origin != "mtDNA"),
          if (nrow(mtrnr2l8)) paste(unique(mtrnr2l8$genome_origin), collapse = ",") else "absent",
          "nuclear_or_unknown")

checks <- rbindlist(checks_list, use.names = TRUE, fill = TRUE)
failed_checks <- checks[passed == FALSE, check_name]
if (length(failed_checks)) {
  stop("Phase 09 validation failed: ", paste(failed_checks, collapse = ", "), call. = FALSE)
}

report_lines <- c(
  "# Phase 09 mitochondrial annotation QC report",
  "",
  paste0("- Validation status: `validated_complete`"),
  paste0("- Execution stage: `", execution_stage, "`"),
  paste0("- Enabled RDS IDs: ", paste(rds_ids, collapse = ", ")),
  paste0("- Assay feature records: ", format(nrow(master[reference_only == FALSE]), big.mark = ",")),
  paste0("- Reference-only records: ", format(nrow(master[reference_only == TRUE]), big.mark = ",")),
  paste0("- Contrast rows: ", format(uniqueN(annotated$contrast_id), big.mark = ",")),
  paste0("- Annotated grid rows: ", format(nrow(annotated), big.mark = ",")),
  paste0("- Phase 08 returned rows preserved: ", format(sum(annotated$phase08_row_present), big.mark = ",")),
  paste0("- MitoCarta core master records: ", format(nrow(master[mito_tier == "core_mito_protein"]), big.mark = ",")),
  paste0("- mtDNA noncoding master records: ", format(nrow(master[mito_tier == "mtdna_noncoding"]), big.mark = ",")),
  paste0("- Extended-tier master records: ", format(nrow(master[mito_tier == "mito_extended"]), big.mark = ",")),
  "",
  "This report summarizes structural and provenance checks only. Phase 09 does not perform pathway analysis or recalculate differential-expression statistics."
)

output_objects <- list(
  "gene_annotation_master.tsv.gz" = list(data = master, schema = phase09$schemas$master, gzip = TRUE),
  "mitochondrial_reference_inventory.tsv" = list(data = reference_inventory, schema = phase09$schemas$reference_inventory, gzip = FALSE),
  "deg_all_annotated.tsv.gz" = list(data = annotated, schema = phase09$schemas$annotated_results, gzip = TRUE),
  "deg_mito_core.tsv.gz" = list(data = deg_mito_core, schema = phase09$schemas$annotated_results, gzip = TRUE),
  "mtdna_noncoding_results.tsv.gz" = list(data = mtdna_noncoding_results, schema = phase09$schemas$annotated_results, gzip = TRUE),
  "unresolved_gene_mappings.tsv" = list(data = unresolved, schema = phase09$schemas$master, gzip = FALSE),
  "annotation_qc_summary.tsv" = list(data = qc_summary, schema = phase09$schemas$qc, gzip = FALSE),
  "annotation_qc_by_contrast.tsv" = list(data = qc_by_contrast, schema = phase09$schemas$qc, gzip = FALSE)
)
for (name in names(output_objects)) {
  spec <- output_objects[[name]]
  path <- file.path(staging_root, name)
  if (isTRUE(spec$gzip)) write_tsv_gz(spec$data, path) else write_tsv(spec$data, path)
}
writeLines(report_lines, file.path(staging_root, "mitochondrial_annotation_qc_report.md"), useBytes = TRUE)

written_paths <- c(
  file.path(staging_root, names(output_objects)),
  file.path(staging_root, "mitochondrial_annotation_qc_report.md")
)
written_count <- sum(
  file.exists(written_paths) & file.info(written_paths)$size > 0
)
written_ok <- written_count == length(written_paths)
add_check("written_outputs_nonempty", written_ok,
          written_count,
          length(written_paths))
checks <- rbindlist(checks_list, use.names = TRUE, fill = TRUE)
must(
  all(checks$passed),
  paste(
    "Final output checks failed:",
    paste(checks[passed == FALSE, check_name], collapse = ", ")
  )
)
checks_path <- file.path(staging_root, "annotation_checks.tsv")
write_tsv(checks, checks_path)

artifact_rows <- list()
for (name in names(output_objects)) {
  spec <- output_objects[[name]]
  stage_path <- file.path(staging_root, name)
  artifact_rows[[length(artifact_rows) + 1L]] <- data.table(
    schema_version = phase09$schemas$artifacts,
    artifact = name,
    path = file.path(config$outputs$root, "09_annotate_genes", name),
    bytes = as.numeric(file.info(stage_path)$size),
    sha256 = sha256_file(stage_path),
    records = nrow(spec$data),
    output_schema = spec$schema,
    validation_status = "validated_complete"
  )
}
for (name in c("annotation_checks.tsv", "mitochondrial_annotation_qc_report.md")) {
  stage_path <- file.path(staging_root, name)
  artifact_rows[[length(artifact_rows) + 1L]] <- data.table(
    schema_version = phase09$schemas$artifacts,
    artifact = name,
    path = file.path(config$outputs$root, "09_annotate_genes", name),
    bytes = as.numeric(file.info(stage_path)$size),
    sha256 = sha256_file(stage_path),
    records = if (name == "annotation_checks.tsv") nrow(checks) else length(report_lines),
    output_schema = if (name == "annotation_checks.tsv") phase09$schemas$checks else "markdown_v1",
    validation_status = "validated_complete"
  )
}
artifacts <- rbindlist(artifact_rows)
must(all(!is.na(artifacts$sha256) & nzchar(artifacts$sha256)),
     "Could not hash every Phase 09 output")
write_tsv(artifacts, file.path(staging_root, "annotation_artifacts.tsv"))

status <- data.table(
  schema_version = phase09$schemas$status,
  execution_stage = execution_stage,
  execution_phase = as.integer(execution$execution_phase),
  backend = as.character(execution$backend),
  run_id = as.character(execution$run_id),
  stable_task_id = "global:annotate_genes",
  task_mode = "annotate_genes",
  scientific_script = "scripts/09_annotate_mitochondrial_genes.R",
  scientific_script_sha256 = current_hashes$scientific_script_sha256,
  scientific_config_sha256 = current_hashes$scientific_config_sha256,
  pipeline_config_sha256 = current_hashes$pipeline_config_sha256,
  analysis_config_sha256 = current_hashes$analysis_config_sha256,
  rds_manifest_sha256 = current_hashes$rds_manifest_sha256,
  phase03_status_sha256 = current_hashes$phase03_status_sha256,
  phase03_manifest_sha256 = current_hashes$phase03_manifest_sha256,
  phase08_status_sha256 = current_hashes$phase08_status_sha256,
  phase08_artifacts_sha256 = current_hashes$phase08_artifacts_sha256,
  gencode_sha256 = reference_hashes[["gencode"]],
  mitocarta_sha256 = reference_hashes[["mitocarta"]],
  hgnc_sha256 = reference_hashes[["hgnc"]],
  extended_manifest_sha256 = reference_hashes[["extended_manifest"]],
  rds_sets = length(rds_ids),
  fine_cell_types = uniqueN(contrast_manifest[, .(rds_id, cell_type_high_resolution)]),
  planned_contrasts = nrow(contrast_manifest),
  master_rows = nrow(master),
  assay_feature_rows = nrow(master[reference_only == FALSE]),
  reference_only_rows = nrow(master[reference_only == TRUE]),
  annotated_grid_rows = nrow(annotated),
  phase08_result_rows = nrow(de),
  paper_degs = sum(de$paper_deg),
  failed_checks = "",
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = "validated_complete",
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
)
write_tsv(status, file.path(staging_root, "annotation_status.tsv"))

must(!dir.exists(final_root), "Final output appeared during Phase 09 execution")
must(file.rename(staging_root, final_root), "Could not publish Phase 09 output directory")
published <- TRUE

cat("Phase 09 annotation completed and validated\n")
cat("Output: ", final_root, "\n", sep = "")
cat("Master rows: ", nrow(master), "\n", sep = "")
cat("Annotated grid rows: ", nrow(annotated), "\n", sep = "")
cat("Phase 08 rows preserved: ", sum(annotated$phase08_row_present), "\n", sep = "")
