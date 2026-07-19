#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL,
    input_root = "results/minerva_production",
    output_root = "results/figures/figures03_to_06",
    dry_run = FALSE,
    force = FALSE
  )
  value_options <- c("--config", "--input-root", "--output-root")
  flag_options <- c("--dry-run", "--force")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/",
        "generate_yu_mitochondrial_figures_3_to_6.R ",
        "--config FILE [--input-root DIR] [--output-root DIR] ",
        "[--dry-run] [--force]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (key %in% flag_options) {
      out[[gsub("-", "_", sub("^--", "", key))]] <- TRUE
      i <- i + 1L
    } else if (key %in% value_options && i < length(args)) {
      out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
      i <- i + 2L
    } else {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
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
  if (grepl("[.]gz$", path)) {
    raw_tmp <- paste0(tmp, ".raw")
    data.table::fwrite(
      x, raw_tmp, sep = "\t", quote = FALSE, na = "NA",
      logical01 = FALSE, compress = "none"
    )
    input <- file(raw_tmp, open = "rb")
    output <- gzfile(tmp, open = "wb")
    repeat {
      chunk <- readBin(input, what = "raw", n = 1024L * 1024L)
      if (!length(chunk)) break
      writeBin(chunk, output)
    }
    close(input)
    close(output)
    unlink(raw_tmp)
  } else {
    data.table::fwrite(
      x, tmp, sep = "\t", quote = FALSE, na = "NA",
      logical01 = FALSE, compress = "none"
    )
  }
  if (!file.rename(tmp, path)) stop("Could not publish ", path, call. = FALSE)
}

atomic_write_lines <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid()))
  writeLines(x, tmp, useBytes = TRUE)
  if (!file.rename(tmp, path)) stop("Could not publish ", path, call. = FALSE)
}

list_to_dt <- function(x) {
  data.table::rbindlist(lapply(x, data.table::as.data.table), fill = TRUE)
}

schema_ok <- function(x, expected) {
  "schema_version" %in% names(x) && nrow(x) > 0L &&
    all(x$schema_version == expected)
}

scalar_text <- function(x) {
  if (!length(x) || all(is.na(x))) return("NA")
  paste(as.character(x), collapse = ",")
}

wrap_text <- function(x, width) {
  vapply(x, function(value) {
    paste(strwrap(value, width = width), collapse = "\n")
  }, character(1))
}

png_dimensions <- function(path) {
  con <- file(path, "rb")
  on.exit(close(con), add = TRUE)
  bytes <- readBin(con, what = "raw", n = 24L)
  if (length(bytes) < 24L) return(c(width = NA_integer_, height = NA_integer_))
  to_int <- function(z) sum(as.integer(z) * 256^(3:0))
  c(width = to_int(bytes[17:20]), height = to_int(bytes[21:24]))
}

pdf_pages <- function(path) {
  if (nzchar(Sys.which("pdfinfo"))) {
    info <- suppressWarnings(system2(
      "pdfinfo", shQuote(path), stdout = TRUE, stderr = TRUE
    ))
    line <- grep("^Pages:", info, value = TRUE)
    if (length(line)) {
      return(as.integer(trimws(sub("^Pages:", "", line[[1L]]))))
    }
  }
  if (nzchar(Sys.which("mdls"))) {
    if (nzchar(Sys.which("mdimport"))) {
      suppressWarnings(system2(
        "mdimport", shQuote(path), stdout = FALSE, stderr = FALSE
      ))
    }
    info <- suppressWarnings(system2(
      "mdls",
      c("-raw", "-name", "kMDItemNumberOfPages", shQuote(path)),
      stdout = TRUE, stderr = TRUE
    ))
    pages <- suppressWarnings(as.integer(info[[1L]]))
    if (!is.na(pages)) return(pages)
  }
  NA_integer_
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
required_packages <- c(
  "data.table", "ggplot2", "patchwork", "scales", "yaml", "digest"
)
for (package in required_packages) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}
library(data.table)
library(ggplot2)
library(patchwork)

start_time <- Sys.time()
project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, project_root)
input_root <- absolute_path(args$input_root, project_root)
output_root <- absolute_path(args$output_root, project_root)
script_path <- file.path(
  project_root, "scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R"
)
plan_path <- file.path(
  project_root, "docs/figures/similar_to_yu_figures_3_to_6_plan.md"
)

if (!file.exists(config_path)) stop("Config does not exist: ", config_path, call. = FALSE)
if (!dir.exists(input_root)) stop("Input root does not exist: ", input_root, call. = FALSE)
if (!file.exists(script_path)) stop("Figure script path is missing", call. = FALSE)
if (!file.exists(plan_path)) stop("Figure plan path is missing", call. = FALSE)
if (!capabilities("cairo") || !capabilities("png")) {
  stop("Local R lacks required Cairo or PNG graphics capability", call. = FALSE)
}

config <- yaml::read_yaml(config_path)
if (!identical(config$schema_version, "yu_mitochondrial_figures_config_v2")) {
  stop("Unexpected figure config schema", call. = FALSE)
}

figures <- list_to_dt(config$figures)
panel_a_cfg <- list_to_dt(config$panel_a_blocks)
panel_b_cfg <- list_to_dt(config$panel_b_queries)
pair_cfg <- list_to_dt(config$state_pairs)
group_cfg <- list_to_dt(config$state_pair_groups)
data.table::setorder(figures, figure_number)
data.table::setorder(panel_a_cfg, figure_id, block_order)
data.table::setorder(panel_b_cfg, figure_id, facet_order)
data.table::setorder(pair_cfg, pair_order)
data.table::setorder(group_cfg, group_order)

check_rows <- list()
assert_check <- function(name, passed, observed, expected, details = "", blocking = TRUE) {
  passed <- isTRUE(passed)
  check_rows[[length(check_rows) + 1L]] <<- data.table(
    schema_version = config$schemas$figure_checks,
    check_name = name,
    blocking = blocking,
    passed = passed,
    observed = scalar_text(observed),
    expected = scalar_text(expected),
    details = details
  )
  if (blocking && !passed) {
    stop("Blocking figure check failed: ", name, " (observed ",
         scalar_text(observed), "; expected ", scalar_text(expected), ")",
         call. = FALSE)
  }
  invisible(passed)
}

sim_root <- file.path(input_root, "10_similarity")
path_root <- file.path(input_root, "11_pathway")
required_paths <- c(
  sim_status = file.path(sim_root, "similarity_status.tsv"),
  sim_checks = file.path(sim_root, "similarity_checks.tsv"),
  sim_artifacts = file.path(sim_root, "similarity_artifacts.tsv"),
  path_status = file.path(path_root, "pathway_status.tsv"),
  path_checks = file.path(path_root, "pathway_checks.tsv"),
  path_artifacts = file.path(path_root, "pathway_artifacts.tsv"),
  references = file.path(path_root, "pathway_reference_manifest.tsv"),
  query_manifest = file.path(path_root, "pathway_query_manifest.tsv"),
  panel_manifest = file.path(path_root, "downstream_panel_manifest.tsv"),
  similarity_panel = file.path(path_root, "similarity_panel_data.tsv.gz"),
  pathway_panel = file.path(path_root, "pathway_panel_data.tsv.gz"),
  pathway_ora = file.path(path_root, "similarity_tail_pathway_ora.tsv.gz")
)
assert_check(
  "required_input_files", all(file.exists(required_paths)),
  sum(file.exists(required_paths)), length(required_paths),
  paste(names(required_paths)[!file.exists(required_paths)], collapse = ",")
)

sim_status <- fread(required_paths[["sim_status"]])
sim_checks <- fread(required_paths[["sim_checks"]])
sim_artifacts <- fread(required_paths[["sim_artifacts"]])
path_status <- fread(required_paths[["path_status"]])
path_checks <- fread(required_paths[["path_checks"]])
path_artifacts <- fread(required_paths[["path_artifacts"]])
references <- fread(required_paths[["references"]])
query_manifest <- fread(required_paths[["query_manifest"]])
panel_manifest <- fread(required_paths[["panel_manifest"]])

expected <- config$inputs
assert_check(
  "similarity_status", nrow(sim_status) == 1L &&
    schema_ok(sim_status, expected$expected_similarity_status_schema) &&
    sim_status$validation_status[[1L]] == expected$expected_validation_status &&
    sim_status$permutations[[1L]] == expected$expected_similarity_permutations &&
    sim_status$comparison_families[[1L]] == expected$expected_comparison_families &&
    sim_status$failed_checks[[1L]] == 0L,
  paste(sim_status$validation_status, sim_status$permutations, sep = "/"),
  paste(expected$expected_validation_status,
        expected$expected_similarity_permutations, sep = "/")
)
assert_check(
  "similarity_checks", schema_ok(sim_checks, expected$expected_similarity_checks_schema) &&
    all(sim_checks$passed), sum(sim_checks$passed), nrow(sim_checks)
)
assert_check(
  "similarity_artifact_manifest",
  schema_ok(sim_artifacts, expected$expected_similarity_artifacts_schema) &&
    all(sim_artifacts$validation_status == "validated_complete"),
  sum(sim_artifacts$validation_status == "validated_complete"), nrow(sim_artifacts)
)
assert_check(
  "pathway_status", nrow(path_status) == 1L &&
    schema_ok(path_status, expected$expected_pathway_status_schema) &&
    path_status$validation_status[[1L]] == expected$expected_validation_status &&
    path_status$comparison_families[[1L]] == expected$expected_comparison_families &&
    path_status$downstream_panel_definitions[[1L]] == expected$expected_downstream_definitions &&
    path_status$failed_checks[[1L]] == 0L,
  paste(path_status$validation_status, path_status$downstream_panel_definitions, sep = "/"),
  paste(expected$expected_validation_status,
        expected$expected_downstream_definitions, sep = "/")
)
assert_check(
  "pathway_checks", schema_ok(path_checks, expected$expected_pathway_checks_schema) &&
    all(path_checks$passed[path_checks$blocking]),
  sum(path_checks$passed[path_checks$blocking]), sum(path_checks$blocking)
)
assert_check(
  "pathway_artifact_manifest",
  schema_ok(path_artifacts, expected$expected_pathway_artifacts_schema) &&
    all(path_artifacts$validation_status == "validated_complete"),
  sum(path_artifacts$validation_status == "validated_complete"), nrow(path_artifacts)
)

validate_artifacts <- function(manifest, label) {
  paths <- vapply(manifest$path, absolute_path, character(1), root = project_root)
  exists <- file.exists(paths)
  bytes <- rep(FALSE, length(paths))
  hashes <- rep(FALSE, length(paths))
  bytes[exists] <- file.info(paths[exists])$size == as.numeric(manifest$bytes[exists])
  hashes[exists] <- vapply(paths[exists], sha256_file, character(1)) ==
    manifest$sha256[exists]
  assert_check(
    paste0(label, "_artifact_files"), all(exists), sum(exists), length(paths)
  )
  assert_check(
    paste0(label, "_artifact_bytes"), all(bytes), sum(bytes), length(paths)
  )
  assert_check(
    paste0(label, "_artifact_hashes"), all(hashes), sum(hashes), length(paths)
  )
}
validate_artifacts(sim_artifacts, "similarity")
validate_artifacts(path_artifacts, "pathway")

assert_check(
  "phase11_phase10_provenance",
  path_status$phase10_status_sha256[[1L]] == sha256_file(required_paths[["sim_status"]]) &&
    path_status$phase10_checks_sha256[[1L]] == sha256_file(required_paths[["sim_checks"]]) &&
    path_status$phase10_artifacts_sha256[[1L]] == sha256_file(required_paths[["sim_artifacts"]]),
  "matching hashes", "matching hashes"
)
assert_check(
  "reference_manifest",
  schema_ok(references, expected$expected_reference_manifest_schema) &&
    config$primary$pathway_collection %in% references$pathway_collection,
  paste(references$pathway_collection, collapse = ","),
  config$primary$pathway_collection
)
assert_check(
  "downstream_manifest",
  schema_ok(panel_manifest, expected$expected_downstream_manifest_schema) &&
    nrow(panel_manifest) == expected$expected_downstream_definitions,
  nrow(panel_manifest), expected$expected_downstream_definitions
)
assert_check(
  "query_manifest",
  schema_ok(query_manifest, expected$expected_query_manifest_schema) &&
    nrow(query_manifest) == expected$expected_query_manifest_rows,
  nrow(query_manifest), expected$expected_query_manifest_rows
)

message("Reading panel-ready Phase 11 data")
similarity_data <- fread(required_paths[["similarity_panel"]], showProgress = FALSE)
pathway_data <- fread(required_paths[["pathway_panel"]], showProgress = FALSE)
pathway_ora <- fread(required_paths[["pathway_ora"]], showProgress = FALSE)
assert_check(
  "similarity_panel_schema_rows",
  schema_ok(similarity_data, expected$expected_similarity_panel_schema) &&
    nrow(similarity_data) == expected$expected_similarity_panel_rows,
  paste(unique(similarity_data$schema_version), nrow(similarity_data), sep = "/"),
  paste(expected$expected_similarity_panel_schema,
        expected$expected_similarity_panel_rows, sep = "/")
)
assert_check(
  "pathway_panel_schema_rows",
  schema_ok(pathway_data, expected$expected_pathway_panel_schema) &&
    nrow(pathway_data) == expected$expected_pathway_panel_rows,
  paste(unique(pathway_data$schema_version), nrow(pathway_data), sep = "/"),
  paste(expected$expected_pathway_panel_schema,
        expected$expected_pathway_panel_rows, sep = "/")
)
assert_check(
  "pathway_ora_schema_rows",
  schema_ok(pathway_ora, expected$expected_pathway_ora_schema) &&
    nrow(pathway_ora) == expected$expected_pathway_ora_rows,
  paste(unique(pathway_ora$schema_version), nrow(pathway_ora), sep = "/"),
  paste(expected$expected_pathway_ora_schema,
        expected$expected_pathway_ora_rows, sep = "/")
)

primary <- config$primary
sim_primary <- similarity_data[analysis_universe == primary$analysis_universe]
sim_display <- merge(
  sim_primary,
  panel_a_cfg[, .(
    figure_id, block_order, comparison_id, requested_k,
    configured_nominal_dimensions = nominal_dimensions, block_label
  )],
  by = c("comparison_id", "requested_k"), all = FALSE, sort = FALSE
)
sim_display <- merge(
  sim_display,
  pair_cfg[, .(
    pair_column, configured_pair_label = pair_label,
    pair_group, configured_pair_order = pair_order,
    display_in_panel_a
  )],
  by = "pair_column", all.x = TRUE, sort = FALSE
)
expected_sim_rows <- sum(2L * panel_a_cfg$requested_k * nrow(pair_cfg))
assert_check(
  "primary_similarity_rows", nrow(sim_display) == expected_sim_rows,
  nrow(sim_display), expected_sim_rows
)
assert_check(
  "state_pair_contract",
  !anyNA(sim_display$configured_pair_order) &&
    all(sim_display$pair_order == sim_display$configured_pair_order) &&
    all(sim_display$pair_label == sim_display$configured_pair_label),
  paste(sort(unique(sim_display$pair_order)), collapse = ","), "1,2,3,4,5,6,7,8,9"
)
tail_counts <- unique(sim_display[, .(
  selected_k = unique(selected_k),
  feature_count = uniqueN(similarity_feature_id),
  state_rows = .N
), by = .(figure_id, comparison_id, requested_k, tail)])
assert_check(
  "similarity_tail_sizes",
  all(tail_counts$selected_k == tail_counts$requested_k) &&
    all(tail_counts$feature_count == tail_counts$requested_k) &&
    all(tail_counts$state_rows == tail_counts$requested_k * nrow(pair_cfg)),
  paste(tail_counts$feature_count, collapse = ","),
  paste(tail_counts$requested_k, collapse = ",")
)
count_reconciliation <- sim_display[, .(
  occurrence_sum = sum(occurrence_count),
  paired_tests_value = unique(paired_tests),
  paired_values = uniqueN(paired_tests)
), by = .(comparison_id, tail, similarity_feature_id)]
assert_check(
  "similarity_occurrence_reconciliation",
  all(count_reconciliation$paired_values == 1L) &&
    all(count_reconciliation$occurrence_sum == count_reconciliation$paired_tests_value),
  sum(count_reconciliation$occurrence_sum == count_reconciliation$paired_tests_value),
  nrow(count_reconciliation)
)
assert_check(
  "similarity_nominal_dimensions",
  all(sim_display$nominal_dimensions == sim_display$configured_nominal_dimensions),
  paste(sort(unique(sim_display$nominal_dimensions)), collapse = ","), "54,108,162"
)

score_digits <- as.integer(config$display$score_digits)
sim_display[, rendered_gene_label := paste0(
  display_label,
  ifelse(!is.na(directional_fdr_bh) & directional_fdr_bh <= 0.05, "*", ""),
  "  S=", formatC(similarity_score, format = "f", digits = score_digits),
  "  n=", paired_tests, "/", nominal_dimensions
)]
sim_display[, pair_axis_label := paste(pair_group, configured_pair_label, sep = "\n")]
sim_display[, tail_label := ifelse(
  tail == "high_score", "Highest similarity", "Lowest similarity"
)]
sim_display[, source_schema_version := schema_version]
sim_display[, schema_version := config$schemas$displayed_similarity]
setorder(sim_display, figure_id, block_order, tail_order, selection_order, pair_order)
sim_display <- sim_display[display_in_panel_a == TRUE]
expected_display_rows <- sum(
  2L * panel_a_cfg$requested_k * sum(pair_cfg$display_in_panel_a)
)
assert_check(
  "displayed_similarity_rows", nrow(sim_display) == expected_display_rows,
  nrow(sim_display), expected_display_rows
)

query_primary <- copy(query_manifest[
  analysis_universe == primary$analysis_universe & requested_k == 200L
])
assert_check(
  "primary_query_manifest_rows", nrow(query_primary) == 12L,
  nrow(query_primary), 12L
)
b_defs <- merge(
  panel_b_cfg,
  query_primary[, .(
    comparison_id, tail, query_id, panel_id, requested_k, selected_k,
    query_size, background_size, analysis_universe
  )],
  by = c("comparison_id", "tail"), all.x = TRUE, sort = FALSE
)
b_defs[, `:=`(
  pathway_collection = primary$pathway_collection,
  collection_release = primary$collection_release,
  expected_pathway_rows = references[
    pathway_collection == primary$pathway_collection, normalized_pathways
  ][[1L]]
)]
setorder(b_defs, figure_id, facet_order)
assert_check(
  "primary_query_definitions",
  nrow(b_defs) == 12L && !anyNA(b_defs$query_id) &&
    all(b_defs$analysis_universe == primary$analysis_universe) &&
    all(b_defs$pathway_collection == primary$pathway_collection),
  nrow(b_defs), 12L
)

summary_rows <- list()
display_rows <- list()
fdr_threshold <- as.numeric(config$display$pathway_fdr_threshold)
display_cap <- as.integer(config$display$max_pathways_per_query)
label_width <- as.integer(config$display$pathway_label_width)
for (i in seq_len(nrow(b_defs))) {
  def <- b_defs[i]
  query_value <- def$query_id[[1L]]
  d <- pathway_ora[
    query_id == query_value &
      pathway_collection == primary$pathway_collection
  ]
  assert_check(
    paste0("query_rows_", i), nrow(d) == def$expected_pathway_rows[[1L]],
    nrow(d), def$expected_pathway_rows[[1L]]
  )
  tested <- d[test_status == "tested" & !is.na(statistical_order)]
  significant <- tested[
    !is.na(tail_fdr_bh) & tail_fdr_bh < fdr_threshold
  ]
  setorder(significant, statistical_order, pathway_id)
  significant_count <- nrow(significant)
  assert_check(
    paste0("query_significance_", i),
    significant_count == def$expected_significant[[1L]] &&
      all(unique(d$query_significant_pathways) == significant_count),
    significant_count, def$expected_significant[[1L]]
  )
  matched <- tested[overlap_count > 0L]
  setorder(matched, statistical_order, pathway_id)
  matched_count <- nrow(matched)
  assert_check(
    paste0("query_matches_", i),
    matched_count == def$expected_matched[[1L]],
    matched_count, def$expected_matched[[1L]]
  )
  selected <- head(matched, display_cap)
  displayed_count <- nrow(selected)
  omitted_count <- matched_count - displayed_count
  expected_status <- if (matched_count == 0L) {
    "no_pathway_matches"
  } else {
    "pathway_matches_present"
  }
  summary_rows[[i]] <- data.table(
    schema_version = config$schemas$pathway_display_summary,
    figure_id = def$figure_id[[1L]],
    facet_order = def$facet_order[[1L]],
    facet_label = def$facet_label[[1L]],
    query_id = query_value,
    panel_id = def$panel_id[[1L]],
    comparison_id = def$comparison_id[[1L]],
    tail = def$tail[[1L]],
    profile_id = primary$profile_id,
    analysis_universe = primary$analysis_universe,
    pathway_collection = primary$pathway_collection,
    collection_release = def$collection_release[[1L]],
    query_size = def$query_size[[1L]],
    background_size = def$background_size[[1L]],
    significant_pathways = significant_count,
    matched_pathways = matched_count,
    displayed_pathways = displayed_count,
    omitted_by_cap = omitted_count,
    display_rule = "tested_overlap_positive_by_statistical_order",
    explicit_query_status = expected_status
  )
  if (displayed_count) {
    display_rows[[i]] <- selected[, .(
      schema_version = config$schemas$displayed_pathway,
      source_schema_version = schema_version,
      figure_id = def$figure_id[[1L]],
      facet_order = def$facet_order[[1L]],
      facet_label = def$facet_label[[1L]],
      record_type = "pathway",
      query_id, panel_id, comparison_id, tail,
      profile_id = primary$profile_id,
      analysis_universe, pathway_collection, collection_release,
      query_size, background_size,
      significant_pathways = significant_count,
      matched_pathways = matched_count,
      displayed_pathways = displayed_count,
      omitted_by_cap = omitted_count,
      display_rule = "tested_overlap_positive_by_statistical_order",
      display_rank = seq_len(.N),
      pathway_id, pathway_label,
      pathway_label_wrapped = wrap_text(pathway_label, label_width),
      statistical_order, gene_ratio, overlap_count, tail_fdr_bh,
      neg_log10_tail_fdr = -log10(pmax(tail_fdr_bh, .Machine$double.xmin)),
      tail_fdr_significant, p_value, test_status, overlap_genes
    )]
  } else {
    display_rows[[i]] <- data.table(
      schema_version = config$schemas$displayed_pathway,
      source_schema_version = expected$expected_pathway_ora_schema,
      figure_id = def$figure_id[[1L]],
      facet_order = def$facet_order[[1L]],
      facet_label = def$facet_label[[1L]],
      record_type = "empty_query",
      query_id = query_value,
      panel_id = def$panel_id[[1L]],
      comparison_id = def$comparison_id[[1L]],
      tail = def$tail[[1L]],
      profile_id = primary$profile_id,
      analysis_universe = primary$analysis_universe,
      pathway_collection = primary$pathway_collection,
      collection_release = def$collection_release[[1L]],
      query_size = def$query_size[[1L]],
      background_size = def$background_size[[1L]],
      significant_pathways = 0L,
      matched_pathways = 0L,
      displayed_pathways = 0L,
      omitted_by_cap = 0L,
      display_rule = "tested_overlap_positive_by_statistical_order",
      display_rank = NA_integer_,
      pathway_id = NA_character_, pathway_label = NA_character_,
      pathway_label_wrapped = NA_character_, statistical_order = NA_integer_,
      gene_ratio = NA_real_, overlap_count = NA_integer_, tail_fdr_bh = NA_real_,
      neg_log10_tail_fdr = NA_real_, tail_fdr_significant = NA,
      p_value = NA_real_, test_status = NA_character_,
      overlap_genes = NA_character_
    )
  }
}
path_summary <- rbindlist(summary_rows, use.names = TRUE)
path_display <- rbindlist(display_rows, use.names = TRUE, fill = TRUE)
setorder(path_summary, figure_id, facet_order)
setorder(path_display, figure_id, facet_order, display_rank)
assert_check(
  "pathway_summary_rows", nrow(path_summary) == 12L, nrow(path_summary), 12L
)
assert_check(
  "pathway_display_cap",
  all(path_summary$displayed_pathways <= display_cap) &&
    all(path_summary$matched_pathways ==
          path_summary$displayed_pathways + path_summary$omitted_by_cap),
  max(path_summary$displayed_pathways), display_cap
)

current_hashes <- list(
  script_sha256 = sha256_file(script_path),
  config_sha256 = sha256_file(config_path),
  plan_sha256 = sha256_file(plan_path),
  similarity_status_sha256 = sha256_file(required_paths[["sim_status"]]),
  similarity_panel_sha256 = sha256_file(required_paths[["similarity_panel"]]),
  pathway_status_sha256 = sha256_file(required_paths[["path_status"]]),
  pathway_panel_sha256 = sha256_file(required_paths[["pathway_panel"]]),
  pathway_ora_sha256 = sha256_file(required_paths[["pathway_ora"]]),
  query_manifest_sha256 = sha256_file(required_paths[["query_manifest"]]),
  panel_manifest_sha256 = sha256_file(required_paths[["panel_manifest"]])
)
assert_check(
  "required_hashes", all(!is.na(unlist(current_hashes))),
  sum(!is.na(unlist(current_hashes))), length(current_hashes)
)

planned_image_names <- c(figures$pdf_filename, figures$png_filename)
companion_names <- c(
  "displayed_similarity_data.tsv.gz", "displayed_pathway_data.tsv.gz",
  "pathway_display_summary.tsv", "figure_captions.md", "figure_manifest.tsv",
  "figure_checks.tsv", "figure_status.tsv"
)
planned_names <- c(planned_image_names, companion_names)
planned_paths <- file.path(output_root, planned_names)

if (!args$dry_run && !args$force && file.exists(file.path(output_root, "figure_status.tsv"))) {
  old_status <- fread(file.path(output_root, "figure_status.tsv"))
  old_manifest_path <- file.path(output_root, "figure_manifest.tsv")
  resumable <- nrow(old_status) == 1L &&
    old_status$schema_version[[1L]] == config$schemas$figure_status &&
    old_status$validation_status[[1L]] == "validated_complete" &&
    old_status$script_sha256[[1L]] == current_hashes$script_sha256 &&
    old_status$config_sha256[[1L]] == current_hashes$config_sha256 &&
    old_status$similarity_panel_sha256[[1L]] == current_hashes$similarity_panel_sha256 &&
    old_status$pathway_panel_sha256[[1L]] == current_hashes$pathway_panel_sha256 &&
    old_status$pathway_ora_sha256[[1L]] == current_hashes$pathway_ora_sha256 &&
    old_status$query_manifest_sha256[[1L]] == current_hashes$query_manifest_sha256 &&
    file.exists(old_manifest_path)
  if (resumable) {
    old_manifest <- fread(old_manifest_path)
    old_paths <- vapply(old_manifest$artifact_path, absolute_path, character(1),
                        root = project_root)
    resumable <- nrow(old_manifest) == 8L && all(file.exists(old_paths)) &&
      all(vapply(old_paths, sha256_file, character(1)) == old_manifest$sha256)
  }
  if (resumable) {
    cat("Validated figure bundle already exists with identical inputs; nothing to do.\n")
    quit(status = 0L)
  }
}
if (!args$dry_run && any(file.exists(planned_paths)) && !args$force) {
  stop(
    "One or more planned outputs already exist. Use --force only for intentional regeneration.",
    call. = FALSE
  )
}

cat("Validated local figure inputs\n")
cat("  similarity display rows: ", nrow(sim_display), "\n", sep = "")
cat("  panel-A tail blocks: ", nrow(tail_counts), "\n", sep = "")
cat("  panel-B queries: ", nrow(path_summary), "\n", sep = "")
print(path_summary[, .(
  figure_id, facet_label, query_size, background_size,
  significant_pathways, matched_pathways, displayed_pathways
)])
if (args$dry_run) {
  cat("Planned image outputs:\n")
  planned_relative_paths <- vapply(
    file.path(output_root, planned_image_names),
    relative_path, character(1), root = project_root
  )
  cat(paste0("  ", planned_relative_paths, "\n"), sep = "")
  cat("Dry run complete; no artifacts written.\n")
  quit(status = 0L)
}

base_font <- as.numeric(config$display$base_font_size)
make_heatmap_group <- function(
    d, group_value, occurrence_max, show_y_axis, show_legend) {
  group_spec <- group_cfg[pair_group == group_value]
  pair_levels <- pair_cfg[
    display_in_panel_a & pair_group == group_value
  ][order(pair_order), pair_label]
  gd <- copy(d[pair_group == group_value])
  gd[, pair_factor := factor(configured_pair_label, levels = pair_levels)]
  p <- ggplot(
    gd, aes(x = pair_factor, y = gene_factor, fill = occurrence_count)
  ) +
    geom_tile(color = "white", linewidth = 0.22) +
    facet_grid(
      rows = vars(tail_factor), scales = "free_y", space = "free_y",
      switch = "y"
    ) +
    scale_fill_gradient(
      low = group_spec$low_color[[1L]],
      high = group_spec$high_color[[1L]],
      limits = c(0, occurrence_max),
      oob = scales::squish,
      name = paste0(group_value, " occurrences"),
      guide = guide_colorbar(
        direction = "horizontal", title.position = "top",
        barwidth = grid::unit(1.5, "cm"),
        barheight = grid::unit(0.22, "cm")
      )
    ) +
    labs(title = group_value, x = NULL, y = NULL) +
    theme_bw(base_size = base_font) +
    theme(
      plot.title = element_text(
        face = "bold", hjust = 0.5, size = base_font + 0.5
      ),
      axis.text.x = element_text(angle = 45, hjust = 1, size = base_font - 1.2),
      axis.text.y = element_text(size = base_font - 2.0),
      strip.placement = "outside",
      strip.text.y.left = element_text(angle = 0, face = "bold"),
      panel.spacing.y = grid::unit(0.35, "lines"),
      legend.position = if (show_legend) "bottom" else "none",
      legend.title = element_text(size = base_font - 1),
      legend.text = element_text(size = base_font - 1.5),
      plot.margin = margin(2, 2, 2, 2)
    )
  if (!show_y_axis) {
    p <- p + theme(
      axis.text.y = element_blank(),
      axis.ticks.y = element_blank(),
      strip.text.y.left = element_blank(),
      strip.background.y = element_blank()
    )
  }
  p
}

make_heatmap <- function(
    comparison_value, title_value, occurrence_max, show_legends = TRUE) {
  d <- copy(sim_display[comparison_id == comparison_value])
  setorder(d, tail_order, selection_order, pair_order)
  gene_order <- unique(d$rendered_gene_label)
  d[, gene_factor := factor(rendered_gene_label, levels = rev(gene_order))]
  d[, tail_factor := factor(
    tail_label, levels = c("Highest similarity", "Lowest similarity")
  )]
  group_values <- group_cfg$pair_group
  group_plots <- lapply(seq_along(group_values), function(i) {
    make_heatmap_group(
      d, group_values[[i]], occurrence_max,
      show_y_axis = i == 1L, show_legend = show_legends
    )
  })
  group_widths <- vapply(group_values, function(group_value) {
    sum(pair_cfg$display_in_panel_a & pair_cfg$pair_group == group_value)
  }, numeric(1))
  wrap_plots(group_plots, nrow = 1L, widths = group_widths) +
    plot_annotation(
      title = title_value,
      theme = theme(plot.title = element_text(
        face = "bold", size = base_font + 1
      ))
    )
}

plot_limits_for_figure <- function(figure_value) {
  d <- path_display[figure_id == figure_value & record_type == "pathway"]
  x_max <- if (nrow(d)) max(d$gene_ratio, na.rm = TRUE) * 1.08 else 1
  color <- if (nrow(d)) range(d$neg_log10_tail_fdr, finite = TRUE) else c(0, 1)
  size <- if (nrow(d)) range(d$overlap_count, finite = TRUE) else c(1, 2)
  if (diff(color) == 0) color <- color + c(-0.1, 0.1)
  if (diff(size) == 0) size <- size + c(-0.5, 0.5)
  list(x = c(0, x_max), color = color, size = size)
}

make_pathway_plot <- function(query_value, limits, show_legend = TRUE) {
  summary <- path_summary[query_id == query_value]
  d <- copy(path_display[query_id == query_value & record_type == "pathway"])
  subtitle <- paste0(
    "n/N=", summary$query_size, "/", summary$background_size,
    "; sig=", summary$significant_pathways, "; shown=",
    summary$displayed_pathways, "/", summary$matched_pathways
  )
  if (!nrow(d)) {
    return(
      ggplot() +
        annotate(
          "text", x = 0.5, y = 0.53,
          label = config$display$empty_pathway_message,
          size = 3.2, fontface = "italic"
        ) +
        xlim(0, 1) + ylim(0, 1) +
        labs(title = summary$facet_label, subtitle = subtitle) +
        theme_void(base_size = base_font) +
        theme(
          plot.title = element_text(face = "bold", size = base_font + 1),
          plot.subtitle = element_text(size = base_font - 1),
          plot.margin = margin(5, 5, 5, 5),
          panel.border = element_rect(fill = NA, color = "grey70", linewidth = 0.5)
        )
    )
  }
  setorder(d, display_rank)
  d[, pathway_factor := factor(
    pathway_label_wrapped, levels = rev(unique(pathway_label_wrapped))
  )]
  ggplot(d, aes(
    x = gene_ratio, y = pathway_factor,
    size = overlap_count, color = neg_log10_tail_fdr,
    shape = tail_fdr_significant
  )) +
    geom_point(alpha = 1, stroke = 1.0) +
    scale_x_continuous(
      limits = limits$x,
      labels = scales::percent_format(accuracy = 1),
      expand = expansion(mult = c(0.01, 0.03))
    ) +
    scale_color_viridis_c(
      option = config$display$pathway_viridis_option,
      limits = limits$color,
      name = expression(-log[10]("BH FDR"))
    ) +
    scale_size_continuous(
      limits = limits$size, range = c(3.0, 6.0), name = "Overlap"
    ) +
    scale_shape_manual(
      values = c(`FALSE` = 1, `TRUE` = 16),
      limits = c("FALSE", "TRUE"),
      breaks = c("FALSE", "TRUE"),
      labels = c("No", "Yes"),
      drop = FALSE,
      name = "BH FDR < 0.05"
    ) +
    labs(
      title = summary$facet_label, subtitle = subtitle,
      x = "Gene ratio (overlap / query)", y = NULL
    ) +
    theme_bw(base_size = base_font) +
    theme(
      plot.title = element_text(face = "bold", size = base_font + 1),
      plot.subtitle = element_text(size = base_font - 1),
      axis.text.y = element_text(size = base_font - 2),
      panel.grid.major.y = element_blank(),
      legend.position = if (show_legend) "right" else "none",
      plot.margin = margin(5, 5, 5, 5)
    )
}

build_figure <- function(figure_value) {
  figure_def <- figures[figure_id == figure_value]
  a_defs <- panel_a_cfg[figure_id == figure_value][order(block_order)]
  occurrence_max <- max(
    sim_display[figure_id == figure_value, occurrence_count], na.rm = TRUE
  )
  a_plots <- lapply(seq_len(nrow(a_defs)), function(i) {
    make_heatmap(
      a_defs$comparison_id[[i]], a_defs$block_label[[i]], occurrence_max,
      show_legends = i == nrow(a_defs)
    )
  })
  a_panel <- wrap_plots(a_plots, ncol = 1L) +
    plot_annotation(
      title = "A. Highest- and lowest-similarity mitochondrial genes",
      subtitle = "Same (green), Different (orange), and Opposite (purple)"
    )

  b_defs_fig <- b_defs[figure_id == figure_value][order(facet_order)]
  limits <- plot_limits_for_figure(figure_value)
  b_plots <- lapply(seq_len(nrow(b_defs_fig)), function(i) {
    make_pathway_plot(
      b_defs_fig$query_id[[i]], limits,
      show_legend = i == nrow(b_defs_fig)
    )
  })
  b_ncol <- if (figure_value == "figure06") 2L else length(b_plots)
  b_panel <- wrap_plots(b_plots, ncol = b_ncol) +
    plot_annotation(title = "B. C2:CP pathway matches for 200-gene score tails")

  subtitle <- paste0(
    "core_mito; mitochondrial-restricted Yu analogue; ",
    "Human MSigDB C2:CP v", primary$collection_release
  )
  short_caption <- paste0(
    "Panel A: green = Same, orange = Different, purple = Opposite; (0,0) ",
    "remains in the score denominator but is not tiled. Missing states are ",
    "excluded; * denotes directional BH FDR <= 0.05. Panel B shows the ",
    "top stored pathway matches for both 200-gene tails regardless of FDR; ",
    "x = gene ratio, size = overlap, color = FDR, filled = FDR < 0.05."
  )
  short_caption <- wrap_text(
    short_caption, if (figure_value == "figure06") 220L else 175L
  )
  combined <- wrap_elements(full = a_panel) / wrap_elements(full = b_panel) +
    plot_layout(heights = c(
      figure_def$panel_a_fraction[[1L]], figure_def$panel_b_fraction[[1L]]
    )) +
    plot_annotation(
      title = figure_def$title[[1L]], subtitle = subtitle,
      caption = short_caption,
      theme = theme(
        plot.title = element_text(face = "bold", size = 14),
        plot.subtitle = element_text(size = 9),
        plot.caption = element_text(size = 7, hjust = 0)
      )
    )
  combined
}

save_plot <- function(plot, path, format, width, height, dpi) {
  tmp <- file.path(
    dirname(path),
    paste0(".", tools::file_path_sans_ext(basename(path)), ".tmp.",
           Sys.getpid(), ".", format)
  )
  render_error <- NULL
  tryCatch({
    if (format == "pdf") {
      grDevices::cairo_pdf(
        tmp, width = width, height = height, onefile = TRUE,
        family = "sans", bg = config$export$background
      )
    } else {
      grDevices::png(
        tmp, width = width, height = height, units = "in", res = dpi,
        type = config$export$png_type, antialias = "subpixel",
        bg = config$export$background
      )
    }
    print(plot)
  }, error = function(e) {
    render_error <<- conditionMessage(e)
  })
  if (grDevices::dev.cur() > 1L) grDevices::dev.off()
  if (!is.null(render_error)) {
    if (file.exists(tmp)) unlink(tmp)
    stop("Rendering failed for ", basename(path), ": ", render_error, call. = FALSE)
  }
  if (!file.exists(tmp) || file.info(tmp)$size <= 0) {
    stop("Renderer produced an empty artifact: ", basename(path), call. = FALSE)
  }
  if (!file.rename(tmp, path)) stop("Could not publish staged image: ", path, call. = FALSE)
}

caption_for <- function(figure_value) {
  f <- figures[figure_id == figure_value]
  a <- panel_a_cfg[figure_id == figure_value][order(block_order)]
  b <- path_summary[figure_id == figure_value][order(facet_order)]
  dimensions <- paste(unique(a$nominal_dimensions), collapse = ", ")
  queries <- paste0(
    b$facet_label, " (n=", b$query_size, ", N=", b$background_size,
    "; ", b$significant_pathways, " FDR-significant; ",
    b$matched_pathways, " pathway matches; ",
    b$displayed_pathways, " displayed)"
  )
  paste0(
    "**Figure ", f$figure_number, ". ", f$title, ".** ",
    "Mitochondrial-restricted Yu analogue using the Phase 10 `core_mito` ",
    "universe. Panel A displays stored highest- and lowest-similarity ",
    "Zhang–Yu rank sets over nominal paired dimensions ", dimensions,
    ". Heatmap cells are observed paired-state occurrence counts, grouped as ",
    "Same (green), Different (orange), and Opposite (purple). The `(0,0)` ",
    "count remains in each score denominator and companion validation but is ",
    "not a displayed tile; missing states are excluded rather than assigned ",
    "to `(0,0)`. Row labels give ",
    "the stored score and observed/nominal coverage; `*` marks stored ",
    "directional BH FDR <= 0.05. Panel B uses the stored top and bottom 200 ",
    "score-tail queries and Phase 11 one-sided ORA for Human MSigDB C2:CP v",
    primary$collection_release,
    ". GeneRatio = k/n, BackgroundRatio = M/N, and fold enrichment = ",
    "(k/n)/(M/N); point x, size, and color show GeneRatio, overlap k, and ",
    "within-query BH FDR. Filled points pass BH FDR < 0.05 and open points ",
    "do not. The first ", display_cap,
    " tested pathways with at least one matched query gene are displayed in ",
    "stored statistical order regardless of FDR, so a highest-similarity ",
    "tail remains visible even when none of its pathways passes FDR. Queries: ",
    paste(queries, collapse = "; "),
    ". `all_mito_related` and MitoPathways are sensitivity profiles and are ",
    "not used in this primary figure."
  )
}

staging_root <- file.path(output_root, paste0("yu_figures_3_to_6.staging.", Sys.getpid()))
dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
on.exit(if (dir.exists(staging_root)) unlink(staging_root, recursive = TRUE), add = TRUE)

message("Rendering four composite figures")
manifest_rows <- list()
dpi <- as.integer(config$export$dpi)
for (i in seq_len(nrow(figures))) {
  def <- figures[i]
  figure_value <- def$figure_id[[1L]]
  message("  ", figure_value)
  plot <- build_figure(figure_value)
  pdf_stage <- file.path(staging_root, def$pdf_filename[[1L]])
  png_stage <- file.path(staging_root, def$png_filename[[1L]])
  save_plot(
    plot, pdf_stage, "pdf", def$width_in[[1L]], def$height_in[[1L]], dpi
  )
  save_plot(
    plot, png_stage, "png", def$width_in[[1L]], def$height_in[[1L]], dpi
  )
  comparison_ids <- panel_a_cfg[figure_id == figure_value,
                                paste(comparison_id, collapse = ";")]
  query_ids <- b_defs[figure_id == figure_value, paste(query_id, collapse = ";")]
  for (format in c("pdf", "png")) {
    stage_path <- if (format == "pdf") pdf_stage else png_stage
    final_name <- if (format == "pdf") def$pdf_filename[[1L]] else def$png_filename[[1L]]
    manifest_rows[[length(manifest_rows) + 1L]] <- data.table(
      schema_version = config$schemas$figure_manifest,
      figure_id = figure_value,
      figure_number = def$figure_number[[1L]],
      format = format,
      artifact_path = relative_path(file.path(output_root, final_name), project_root),
      width_in = def$width_in[[1L]],
      height_in = def$height_in[[1L]],
      dpi = if (format == "png") dpi else NA_integer_,
      page_count = if (format == "pdf") pdf_pages(stage_path) else NA_integer_,
      pixel_width = if (format == "png") png_dimensions(stage_path)[["width"]] else NA_integer_,
      pixel_height = if (format == "png") png_dimensions(stage_path)[["height"]] else NA_integer_,
      bytes = file.info(stage_path)$size,
      sha256 = sha256_file(stage_path),
      profile_id = primary$profile_id,
      analysis_universe = primary$analysis_universe,
      pathway_collection = primary$pathway_collection,
      source_comparison_ids = comparison_ids,
      source_query_ids = query_ids,
      script_sha256 = current_hashes$script_sha256,
      config_sha256 = current_hashes$config_sha256,
      similarity_status_sha256 = current_hashes$similarity_status_sha256,
      similarity_panel_sha256 = current_hashes$similarity_panel_sha256,
      pathway_status_sha256 = current_hashes$pathway_status_sha256,
      pathway_panel_sha256 = current_hashes$pathway_panel_sha256,
      pathway_ora_sha256 = current_hashes$pathway_ora_sha256,
      query_manifest_sha256 = current_hashes$query_manifest_sha256,
      r_version = as.character(getRversion()),
      ggplot2_version = as.character(packageVersion("ggplot2")),
      patchwork_version = as.character(packageVersion("patchwork")),
      created_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      validation_status = "validated_complete"
    )
  }
  rm(plot)
  invisible(gc())
}
figure_manifest <- rbindlist(manifest_rows, use.names = TRUE)
figure_manifest[format == "pdf", page_count := vapply(
  basename(artifact_path),
  function(filename) pdf_pages(file.path(staging_root, filename)),
  integer(1)
)]

assert_check(
  "eight_primary_images", nrow(figure_manifest) == 8L &&
    all(figure_manifest$bytes > 0) && all(!is.na(figure_manifest$sha256)),
  nrow(figure_manifest), 8L
)
assert_check(
  "pdf_page_counts",
  all(figure_manifest[format == "pdf", page_count] == 1L),
  paste(figure_manifest[format == "pdf", page_count], collapse = ","), "1,1,1,1"
)
png_manifest <- figure_manifest[format == "png"]
expected_pixels <- figures[, .(
  figure_id,
  expected_width = as.integer(round(width_in * dpi)),
  expected_height = as.integer(round(height_in * dpi))
)]
png_check <- merge(png_manifest, expected_pixels, by = "figure_id")
assert_check(
  "png_dimensions",
  all(png_check$pixel_width == png_check$expected_width) &&
    all(png_check$pixel_height == png_check$expected_height),
  paste(png_check$pixel_width, png_check$pixel_height, sep = "x", collapse = ","),
  paste(png_check$expected_width, png_check$expected_height,
        sep = "x", collapse = ",")
)

caption_lines <- c("# Figure captions", "")
for (figure_value in figures$figure_id) {
  number <- figures[figure_id == figure_value, figure_number]
  caption_lines <- c(
    caption_lines, paste0("## Figure ", number), "",
    caption_for(figure_value), ""
  )
}
assert_check(
  "caption_count", sum(grepl("^## Figure ", caption_lines)) == 4L,
  sum(grepl("^## Figure ", caption_lines)), 4L
)

escape_newlines <- function(x) {
  out <- x
  present <- !is.na(x)
  out[present] <- vapply(
    strsplit(x[present], "\n", fixed = TRUE),
    paste, character(1), collapse = "\\n"
  )
  out
}
sim_output <- copy(sim_display)[, pair_axis_label := escape_newlines(pair_axis_label)]
path_output <- copy(path_display)[, pathway_label_wrapped := escape_newlines(pathway_label_wrapped)]
atomic_fwrite(sim_output, file.path(staging_root, "displayed_similarity_data.tsv.gz"))
atomic_fwrite(path_output, file.path(staging_root, "displayed_pathway_data.tsv.gz"))
atomic_fwrite(path_summary, file.path(staging_root, "pathway_display_summary.tsv"))
atomic_write_lines(caption_lines, file.path(staging_root, "figure_captions.md"))
atomic_fwrite(figure_manifest, file.path(staging_root, "figure_manifest.tsv"))

figure_checks <- rbindlist(check_rows, use.names = TRUE)
assert_check(
  "all_blocking_checks", all(figure_checks$passed[figure_checks$blocking]),
  sum(figure_checks$passed[figure_checks$blocking]), sum(figure_checks$blocking)
)
figure_checks <- rbindlist(check_rows, use.names = TRUE)
atomic_fwrite(figure_checks, file.path(staging_root, "figure_checks.tsv"))

status <- data.table(
  schema_version = config$schemas$figure_status,
  input_execution_label = primary$execution_label,
  input_root = relative_path(input_root, project_root),
  output_root = relative_path(output_root, project_root),
  script = relative_path(script_path, project_root),
  script_sha256 = current_hashes$script_sha256,
  config = relative_path(config_path, project_root),
  config_sha256 = current_hashes$config_sha256,
  plan_sha256 = current_hashes$plan_sha256,
  similarity_status_sha256 = current_hashes$similarity_status_sha256,
  similarity_panel_sha256 = current_hashes$similarity_panel_sha256,
  pathway_status_sha256 = current_hashes$pathway_status_sha256,
  pathway_panel_sha256 = current_hashes$pathway_panel_sha256,
  pathway_ora_sha256 = current_hashes$pathway_ora_sha256,
  query_manifest_sha256 = current_hashes$query_manifest_sha256,
  panel_manifest_sha256 = current_hashes$panel_manifest_sha256,
  displayed_similarity_sha256 = sha256_file(
    file.path(staging_root, "displayed_similarity_data.tsv.gz")
  ),
  displayed_pathway_sha256 = sha256_file(
    file.path(staging_root, "displayed_pathway_data.tsv.gz")
  ),
  pathway_display_summary_sha256 = sha256_file(
    file.path(staging_root, "pathway_display_summary.tsv")
  ),
  captions_sha256 = sha256_file(file.path(staging_root, "figure_captions.md")),
  figure_manifest_sha256 = sha256_file(file.path(staging_root, "figure_manifest.tsv")),
  figure_checks_sha256 = sha256_file(file.path(staging_root, "figure_checks.tsv")),
  figures = nrow(figures),
  image_artifacts = nrow(figure_manifest),
  similarity_display_rows = nrow(sim_display),
  pathway_display_rows = nrow(path_display),
  pathway_queries = nrow(path_summary),
  failed_checks = sum(!figure_checks$passed[figure_checks$blocking]),
  r_version = as.character(getRversion()),
  data_table_version = as.character(packageVersion("data.table")),
  ggplot2_version = as.character(packageVersion("ggplot2")),
  patchwork_version = as.character(packageVersion("patchwork")),
  scales_version = as.character(packageVersion("scales")),
  yaml_version = as.character(packageVersion("yaml")),
  digest_version = as.character(packageVersion("digest")),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), start_time, units = "secs")),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  validation_status = "validated_complete"
)
atomic_fwrite(status, file.path(staging_root, "figure_status.tsv"))

dir.create(output_root, recursive = TRUE, showWarnings = FALSE)
publish_order <- c(setdiff(planned_names, "figure_status.tsv"), "figure_status.tsv")
for (name in publish_order) {
  source <- file.path(staging_root, name)
  target <- file.path(output_root, name)
  if (!file.exists(source)) stop("Missing staged artifact: ", name, call. = FALSE)
  if (file.exists(target)) {
    if (!args$force) stop("Refusing to replace existing artifact: ", target, call. = FALSE)
    unlink(target)
  }
  if (!file.rename(source, target)) stop("Could not publish artifact: ", target, call. = FALSE)
}

cat("Figure workflow completed successfully\n")
if (dir.exists(staging_root)) unlink(staging_root, recursive = TRUE)
cat("  output: ", relative_path(output_root, project_root), "\n", sep = "")
cat("  figures: ", nrow(figures), "\n", sep = "")
cat("  image artifacts: ", nrow(figure_manifest), "\n", sep = "")
cat("  status: validated_complete\n")
