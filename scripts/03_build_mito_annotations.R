#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, features = character(),
    task_mode = "annotations"
  )
  value_options <- c("--config", "--execution-config", "--features", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/03_build_mito_annotations.R --config FILE ",
        "[--execution-config FILE] [--features FILE ...] ",
        "[--task-mode annotations]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    value <- args[[i + 1L]]
    if (key == "--features") {
      out$features <- c(out$features, value)
    } else {
      name <- gsub("-", "_", sub("^--", "", key))
      out[[name]] <- value
    }
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  if (!identical(out$task_mode, "annotations")) {
    stop("--task-mode must be 'annotations'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  write.table(x, tmp, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

atomic_write_lines <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  writeLines(x, tmp, useBytes = TRUE)
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

peak_ram_gib <- function() {
  status_path <- "/proc/self/status"
  if (!file.exists(status_path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(status_path, warn = FALSE), value = TRUE)
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

extract_gtf_attribute <- function(attributes, key) {
  pattern <- paste0("(?:^|;[[:space:]]*)", key, "[[:space:]]+\"([^\"]+)\"")
  matches <- regexec(pattern, attributes, perl = TRUE)
  values <- regmatches(attributes, matches)
  vapply(values, function(value) {
    if (length(value) >= 2L) value[[2L]] else NA_character_
  }, character(1))
}

read_gtf_genes <- function(path, chunk_size = 100000L) {
  connection <- gzfile(path, open = "rt")
  on.exit(close(connection), add = TRUE)
  chunks <- list()
  repeat {
    lines <- readLines(connection, n = chunk_size, warn = FALSE)
    if (!length(lines)) break
    gene_lines <- lines[grepl("\tgene\t", lines, fixed = TRUE)]
    if (!length(gene_lines)) next
    fields <- strsplit(gene_lines, "\t", fixed = TRUE)
    valid <- lengths(fields) >= 9L
    fields <- fields[valid]
    if (!length(fields)) next
    attributes <- vapply(fields, `[[`, character(1), 9L)
    chunks[[length(chunks) + 1L]] <- data.frame(
      chromosome = vapply(fields, `[[`, character(1), 1L),
      gene_id = sub("[.][0-9]+$", "", extract_gtf_attribute(attributes, "gene_id")),
      gene_name = extract_gtf_attribute(attributes, "gene_name"),
      gene_type = extract_gtf_attribute(attributes, "gene_type"),
      stringsAsFactors = FALSE
    )
  }
  if (!length(chunks)) stop("No gene records were parsed from GENCODE", call. = FALSE)
  genes <- unique(do.call(rbind, chunks))
  genes <- genes[!is.na(genes$gene_id) & !is.na(genes$gene_name), , drop = FALSE]
  genes[order(genes$chromosome, genes$gene_name, genes$gene_id), , drop = FALSE]
}

split_pipe <- function(x) {
  if (is.na(x) || !nzchar(trimws(x)) || trimws(x) == "-") return(character())
  values <- trimws(strsplit(x, "|", fixed = TRUE)[[1L]])
  unique(values[nzchar(values) & values != "-"])
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c("yaml", "data.table", "readxl")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages)) {
  stop("Missing required packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, root)
if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
config <- yaml::read_yaml(config_path)
project_root <- normalizePath(
  absolute_path(config$project$root %||% ".", root), mustWork = TRUE
)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
output_root <- absolute_path(config$outputs$root, project_root)
if (!file.exists(analysis_path)) stop("Analysis config does not exist", call. = FALSE)
if (!file.exists(manifest_path)) stop("RDS manifest does not exist", call. = FALSE)
analysis <- yaml::read_yaml(analysis_path)
references <- analysis$references

gencode_path <- absolute_path(references$gencode_gtf, project_root)
mitocarta_path <- absolute_path(references$mitocarta_source, project_root)
if (!file.exists(gencode_path)) stop("GENCODE GTF does not exist: ", gencode_path, call. = FALSE)
if (!file.exists(mitocarta_path)) {
  stop("MitoCarta spreadsheet does not exist: ", mitocarta_path, call. = FALSE)
}

gencode_sha <- sha256_file(gencode_path)
mitocarta_sha <- sha256_file(mitocarta_path)
gzip_status <- system2("gzip", c("-t", gencode_path), stdout = FALSE, stderr = FALSE)
if (!identical(gzip_status, 0L)) stop("GENCODE gzip integrity check failed", call. = FALSE)
if (!identical(gencode_sha, references$gencode_gtf_sha256)) {
  stop("GENCODE checksum mismatch: ", gencode_sha, call. = FALSE)
}
if (!identical(mitocarta_sha, references$mitocarta_sha256)) {
  stop("MitoCarta checksum mismatch: ", mitocarta_sha, call. = FALSE)
}

message("Parsing GENCODE gene records: ", gencode_path)
gencode <- read_gtf_genes(gencode_path)
gencode_symbol_duplicates <- duplicated(gencode$gene_name) |
  duplicated(gencode$gene_name, fromLast = TRUE)
gencode$duplicate_gene_name <- gencode_symbol_duplicates

message("Reading MitoCarta inventory: ", mitocarta_path)
inventory_sheet <- references$mitocarta_inventory_sheet %||% "A Human MitoCarta3.0"
pathway_sheet <- references$mitocarta_pathways_sheet %||% "C MitoPathways"
mitocarta <- suppressWarnings(as.data.frame(readxl::read_excel(
  mitocarta_path, sheet = inventory_sheet
)))
pathways <- suppressWarnings(as.data.frame(readxl::read_excel(
  mitocarta_path, sheet = pathway_sheet
)))
required_inventory <- c(
  "HumanGeneID", "Symbol", "Synonyms", "Description",
  "MitoCarta3.0_SubMitoLocalization", "MitoCarta3.0_MitoPathways"
)
missing_inventory <- setdiff(required_inventory, names(mitocarta))
if (length(missing_inventory)) {
  stop("MitoCarta inventory columns missing: ", paste(missing_inventory, collapse = ", "), call. = FALSE)
}
required_pathways <- c("MitoPathway", "MitoPathways Hierarchy", "Genes")
missing_pathways <- setdiff(required_pathways, names(pathways))
if (length(missing_pathways)) {
  stop("MitoCarta pathway columns missing: ", paste(missing_pathways, collapse = ", "), call. = FALSE)
}

mitocarta$Symbol <- trimws(as.character(mitocarta$Symbol))
mitocarta <- mitocarta[nzchar(mitocarta$Symbol), , drop = FALSE]
mitocarta$duplicate_canonical_symbol <- duplicated(mitocarta$Symbol) |
  duplicated(mitocarta$Symbol, fromLast = TRUE)

alias_rows <- list()
for (i in seq_len(nrow(mitocarta))) {
  aliases <- unique(c(mitocarta$Symbol[[i]], split_pipe(mitocarta$Synonyms[[i]])))
  alias_rows[[i]] <- data.frame(
    canonical_symbol = mitocarta$Symbol[[i]],
    alias = aliases,
    alias_type = ifelse(aliases == mitocarta$Symbol[[i]], "canonical", "synonym"),
    stringsAsFactors = FALSE
  )
}
aliases <- data.table::rbindlist(alias_rows, use.names = TRUE)
alias_counts <- aliases[, .(canonical_targets = data.table::uniqueN(canonical_symbol)), by = alias]
aliases <- merge(aliases, alias_counts, by = "alias", all.x = TRUE, sort = FALSE)
aliases[, duplicate_alias := canonical_targets > 1L]

pathway_records <- lapply(seq_len(nrow(pathways)), function(i) {
  genes <- split_pipe(pathways$Genes[[i]])
  data.frame(
    pathway = trimws(as.character(pathways$MitoPathway[[i]])),
    hierarchy = trimws(as.character(pathways$`MitoPathways Hierarchy`[[i]])),
    genes = paste(genes, collapse = "|"),
    gene_count = length(genes),
    stringsAsFactors = FALSE
  )
})
pathway_table <- do.call(rbind, pathway_records)
pathway_table <- pathway_table[nzchar(pathway_table$pathway), , drop = FALSE]
gmt_lines <- vapply(seq_len(nrow(pathway_table)), function(i) {
  genes <- split_pipe(pathway_table$genes[[i]])
  paste(c(pathway_table$pathway[[i]], pathway_table$hierarchy[[i]], genes), collapse = "\t")
}, character(1))

manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
enabled <- toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES")
manifest <- manifest[enabled, , drop = FALSE]
manifest$feature_file <- file.path(
  config$outputs$root, "01_audit",
  paste0(sub("[.][Rr][Dd][Ss]$", "", basename(manifest$input_rds)), ".features.tsv.gz")
)

feature_paths <- args$features
if (!length(feature_paths)) feature_paths <- manifest$feature_file
feature_paths <- vapply(feature_paths, absolute_path, character(1), root = project_root)
missing_feature_files <- feature_paths[!file.exists(feature_paths)]
if (length(missing_feature_files)) {
  stop("Feature inventories missing: ", paste(missing_feature_files, collapse = ", "), call. = FALSE)
}

features_by_rds <- list()
for (path in feature_paths) {
  base_name <- sub("[.]features[.]tsv[.]gz$", "", basename(path))
  row <- manifest[
    sub("[.][Rr][Dd][Ss]$", "", basename(manifest$input_rds)) == base_name,
    , drop = FALSE
  ]
  if (nrow(row) != 1L) stop("Could not map feature inventory to one RDS: ", path, call. = FALSE)
  feature_table <- data.table::fread(path, data.table = FALSE)
  required_features <- c("feature", "total_raw_counts", "nuclei_detected")
  missing_features <- setdiff(required_features, names(feature_table))
  if (length(missing_features)) {
    stop("Feature columns missing in ", path, ": ", paste(missing_features, collapse = ", "), call. = FALSE)
  }
  feature_table$rds_id <- row$rds_id[[1L]]
  feature_table$source_feature_file <- sub(paste0("^", project_root, "/?"), "", path)
  features_by_rds[[length(features_by_rds) + 1L]] <- feature_table
}
universe <- data.table::rbindlist(features_by_rds, fill = TRUE)
universe[, feature := trimws(as.character(feature))]

gencode_by_symbol <- gencode[!duplicated(gencode$gene_name), , drop = FALSE]
symbol_index <- match(universe$feature, gencode_by_symbol$gene_name)
ensembl_index <- match(sub("[.][0-9]+$", "", universe$feature), gencode$gene_id)
use_ensembl <- is.na(symbol_index) & !is.na(ensembl_index)
universe[, `:=`(
  gencode_gene_id = gencode_by_symbol$gene_id[symbol_index],
  gencode_gene_name = gencode_by_symbol$gene_name[symbol_index],
  chromosome = gencode_by_symbol$chromosome[symbol_index],
  gene_type = gencode_by_symbol$gene_type[symbol_index],
  gencode_match_type = ifelse(!is.na(symbol_index), "symbol", "unmatched")
)]
universe$gencode_gene_id[use_ensembl] <- gencode$gene_id[ensembl_index[use_ensembl]]
universe$gencode_gene_name[use_ensembl] <- gencode$gene_name[ensembl_index[use_ensembl]]
universe$chromosome[use_ensembl] <- gencode$chromosome[ensembl_index[use_ensembl]]
universe$gene_type[use_ensembl] <- gencode$gene_type[ensembl_index[use_ensembl]]
universe$gencode_match_type[use_ensembl] <- "ensembl_gene_id"

direct_index <- match(universe$feature, mitocarta$Symbol)
unique_aliases <- unique(aliases[canonical_targets == 1L, .(alias, canonical_symbol)])
alias_index <- match(universe$feature, unique_aliases$alias)
use_alias <- is.na(direct_index) & !is.na(alias_index)
universe[, `:=`(
  mitocarta_symbol = mitocarta$Symbol[direct_index],
  mitocarta_match_type = ifelse(!is.na(direct_index), "canonical", "unmatched")
)]
universe$mitocarta_symbol[use_alias] <- unique_aliases$canonical_symbol[alias_index[use_alias]]
universe$mitocarta_match_type[use_alias] <- "unique_synonym"
universe[, `:=`(
  is_mitocarta = !is.na(mitocarta_symbol),
  is_mtdna_protein_gene = feature %in% unlist(
    analysis$mitochondrial_features$mtdna_protein_genes, use.names = FALSE
  ),
  test_eligible = is.finite(total_raw_counts) & total_raw_counts > 0,
  test_exclusion_reason = ifelse(
    is.finite(total_raw_counts) & total_raw_counts > 0, "", "zero_or_nonfinite_raw_counts"
  )
)]

mapped <- universe[is_mitocarta == TRUE, .(
  mapped_feature = paste(sort(unique(feature)), collapse = ";"),
  match_type = paste(sort(unique(mitocarta_match_type)), collapse = ";"),
  tested = any(test_eligible)
), by = .(rds_id, canonical_symbol = mitocarta_symbol)]
mc_grid <- data.table::CJ(
  rds_id = sort(unique(universe$rds_id)),
  canonical_symbol = mitocarta$Symbol,
  unique = TRUE
)
mc_columns <- data.table::data.table(
  canonical_symbol = mitocarta$Symbol,
  human_gene_id = as.character(mitocarta$HumanGeneID),
  description = as.character(mitocarta$Description),
  synonyms = as.character(mitocarta$Synonyms),
  sub_mito_localization = as.character(mitocarta$`MitoCarta3.0_SubMitoLocalization`),
  mito_pathways = as.character(mitocarta$`MitoCarta3.0_MitoPathways`),
  duplicate_canonical_symbol = mitocarta$duplicate_canonical_symbol
)
mc_by_rds <- merge(mc_grid, mc_columns, by = "canonical_symbol", all.x = TRUE)
mc_by_rds <- merge(mc_by_rds, mapped, by = c("rds_id", "canonical_symbol"), all.x = TRUE)
mc_by_rds[, `:=`(
  measured = !is.na(mapped_feature),
  tested = !is.na(tested) & tested
)]
mc_by_rds$match_type[is.na(mc_by_rds$match_type)] <- "unmatched"

alias_feature_counts <- universe[, .(feature_present_rds = data.table::uniqueN(rds_id)), by = feature]
aliases <- merge(aliases, alias_feature_counts, by.x = "alias", by.y = "feature", all.x = TRUE)
aliases$feature_present_rds[is.na(aliases$feature_present_rds)] <- 0L
selected_alias_counts <- universe[mitocarta_match_type == "unique_synonym", .(
  selected_mapping_rds = data.table::uniqueN(rds_id)
), by = .(alias = feature, canonical_symbol = mitocarta_symbol)]
aliases <- merge(aliases, selected_alias_counts, by = c("alias", "canonical_symbol"), all.x = TRUE)
aliases$selected_mapping_rds[is.na(aliases$selected_mapping_rds)] <- 0L

expected_mt <- unlist(analysis$mitochondrial_features$mtdna_protein_genes, use.names = FALSE)
mt_grid <- data.table::CJ(
  rds_id = sort(unique(universe$rds_id)), feature = expected_mt, unique = TRUE
)
mt_observed <- universe[feature %in% expected_mt, .(
  measured = TRUE,
  tested = any(test_eligible),
  total_raw_counts = sum(total_raw_counts),
  nuclei_detected = sum(nuclei_detected),
  chromosome = paste(sort(unique(stats::na.omit(chromosome))), collapse = ";"),
  gencode_gene_id = paste(sort(unique(stats::na.omit(gencode_gene_id))), collapse = ";")
), by = .(rds_id, feature)]
mt_table <- merge(mt_grid, mt_observed, by = c("rds_id", "feature"), all.x = TRUE)
mt_table$measured[is.na(mt_table$measured)] <- FALSE
mt_table$tested[is.na(mt_table$tested)] <- FALSE
mt_table$chromosome[is.na(mt_table$chromosome)] <- ""
mt_table$gencode_gene_id[is.na(mt_table$gencode_gene_id)] <- ""

annotation_dir <- file.path(output_root, "03_annotations")
dir.create(annotation_dir, recursive = TRUE, showWarnings = FALSE)
paths <- list(
  mt = file.path(annotation_dir, "mtDNA_protein_genes.tsv"),
  mc = file.path(annotation_dir, "mitocarta_measured_genes.tsv"),
  gmt = file.path(annotation_dir, "mitocarta_pathways.gmt"),
  pathway_table = file.path(annotation_dir, "mitocarta_pathways.tsv"),
  aliases = file.path(annotation_dir, "gene_alias_mapping.tsv"),
  universe = file.path(annotation_dir, "tested_gene_universe.tsv"),
  gencode = file.path(annotation_dir, "gencode_gene_annotation.tsv"),
  checks = file.path(annotation_dir, "annotation_checks.tsv"),
  manifest = file.path(annotation_dir, "annotation_manifest.tsv"),
  status = file.path(annotation_dir, "annotation_status.tsv")
)

atomic_write_tsv(as.data.frame(mt_table), paths$mt)
atomic_write_tsv(as.data.frame(mc_by_rds), paths$mc)
atomic_write_lines(gmt_lines, paths$gmt)
atomic_write_tsv(pathway_table, paths$pathway_table)
atomic_write_tsv(as.data.frame(aliases), paths$aliases)
atomic_write_tsv(as.data.frame(universe), paths$universe)
atomic_write_tsv(gencode, paths$gencode)

checks <- list()
add_check <- function(check, passed, observed, expected) {
  checks[[length(checks) + 1L]] <<- data.frame(
    schema_version = "mito_annotations_checks_v1",
    check = check,
    passed = isTRUE(passed),
    observed = paste(observed, collapse = ";"),
    expected = paste(expected, collapse = ";"),
    stringsAsFactors = FALSE
  )
}
add_check("gencode_gzip_integrity", identical(gzip_status, 0L), gzip_status, 0L)
add_check("gencode_sha256", identical(gencode_sha, references$gencode_gtf_sha256), gencode_sha, references$gencode_gtf_sha256)
add_check("gencode_gene_records", nrow(gencode) > 0L, nrow(gencode), ">0")
add_check("mitocarta_sha256", identical(mitocarta_sha, references$mitocarta_sha256), mitocarta_sha, references$mitocarta_sha256)
add_check("mitocarta_inventory_rows", nrow(mitocarta) == 1136L, nrow(mitocarta), 1136L)
add_check("mitocarta_unique_symbols", !anyDuplicated(mitocarta$Symbol), anyDuplicated(mitocarta$Symbol), 0L)
add_check("mitocarta_pathways", nrow(pathway_table) == 154L, nrow(pathway_table), 154L)
add_check("feature_inventories", length(feature_paths) == nrow(manifest), length(feature_paths), nrow(manifest))
mt_counts <- mt_table[, .(measured = sum(measured), chromosomes = sum(nzchar(chromosome))), by = rds_id]
add_check("all_mtdna_genes_measured", all(mt_counts$measured == length(expected_mt)), paste(mt_counts$measured, collapse = ";"), length(expected_mt))
add_check("mtdna_chromosomes_present", all(mt_counts$chromosomes == length(expected_mt)), paste(mt_counts$chromosomes, collapse = ";"), length(expected_mt))
add_check("tested_gene_universe", nrow(universe) > 0L && all(nzchar(universe$feature)), nrow(universe), ">0")
check_table <- do.call(rbind, checks)
failed_checks <- check_table$check[!check_table$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"
atomic_write_tsv(check_table, paths$checks)

artifact_paths <- c(
  gencode_path, mitocarta_path, paths$mt, paths$mc, paths$gmt,
  paths$pathway_table, paths$aliases, paths$universe, paths$gencode, paths$checks
)
artifact_records <- c(
  nrow(gencode), nrow(mitocarta), nrow(mt_table), nrow(mc_by_rds),
  length(gmt_lines), nrow(pathway_table), nrow(aliases), nrow(universe),
  nrow(gencode), nrow(check_table)
)
annotation_manifest <- data.frame(
  schema_version = "annotation_manifest_v1",
  artifact = basename(artifact_paths),
  path = sub(paste0("^", project_root, "/?"), "", artifact_paths),
  bytes = file.info(artifact_paths)$size,
  sha256 = vapply(artifact_paths, sha256_file, character(1)),
  records = artifact_records,
  source_version = c(
    paste0("GENCODE_", references$gencode_release),
    paste0("MitoCarta_", references$mitocarta_version),
    rep(as.character(analysis$analysis$version), length(artifact_paths) - 2L)
  ),
  source_url = c("https://www.gencodegenes.org/human/release_44.html", references$mitocarta_url, rep("", length(artifact_paths) - 2L)),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(annotation_manifest, paths$manifest)

execution_phase <- if (isTRUE(config$scope$pilot)) 1L else 2L
backend <- "direct"
run_id <- if (isTRUE(config$scope$pilot)) "local_pilot_manual" else "manual_annotations"
if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  if (!file.exists(execution_path)) stop("Execution config does not exist: ", execution_path, call. = FALSE)
  execution <- yaml::read_yaml(execution_path)$execution
  execution_phase <- execution$execution_phase %||% execution_phase
  backend <- execution$backend %||% backend
  run_id <- execution$run_id %||% run_id
}
status <- data.frame(
  schema_version = "mito_annotations_status_v1",
  execution_phase = execution_phase,
  backend = backend,
  run_id = run_id,
  stable_task_id = "global:annotations",
  task_mode = "annotations",
  scientific_script = "scripts/03_build_mito_annotations.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/03_build_mito_annotations.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  manifest_sha256 = sha256_file(manifest_path),
  gencode_sha256 = gencode_sha,
  mitocarta_sha256 = mitocarta_sha,
  rds_feature_sets = length(feature_paths),
  tested_gene_rows = nrow(universe),
  mitocarta_rows = nrow(mitocarta),
  pathway_rows = nrow(pathway_table),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, paths$status)

cat("Annotation directory: ", annotation_dir, "\n", sep = "")
cat("MitoCarta genes: ", nrow(mitocarta), "\n", sep = "")
cat("MitoCarta pathways: ", nrow(pathway_table), "\n", sep = "")
cat("Feature sets: ", length(feature_paths), "\n", sep = "")
cat("Annotation status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
