#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

common_path <- file.path(
  "scripts", "figures", "analysis", "phease12_kda",
  "phase12_kda_figure_common.R"
)
if (!file.exists(common_path)) stop("Missing shared figure helper: ", common_path, call. = FALSE)
source(common_path)

usage <- function() {
  cat(
    "Usage: Rscript scripts/figures/analysis/phease12_kda/",
    "prepare_phase12_kda_figure_data.R ",
    "[--input-dir DIR] [--output-dir DIR] [--kda-source FILE]\n",
    sep = ""
  )
}

args <- parse_value_args(
  commandArgs(trailingOnly = TRUE),
  defaults = list(
    input_dir = "results/minerva_production/12_kda",
    output_dir = "results/figures/analysis/phase12_kda",
    kda_source = "scripts/NetWeaver/fKDA.R"
  ),
  allowed = c("--input-dir", "--output-dir", "--kda-source")
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
kda_source <- absolute_path(args$kda_source, project_root)

validate_phase12_bundle(input_dir)
assert_true(file.exists(kda_source), paste("KDA source does not exist:", kda_source))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

sha256_file <- function(path) {
  output <- system2("shasum", c("-a", "256", path), stdout = TRUE, stderr = TRUE)
  assert_true(length(output) == 1L, paste("Could not hash", path))
  strsplit(output[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

message("Reading validated Phase 12 manifests and compact inputs")
manifest <- read_tsv(file.path(input_dir, "kda_run_manifest.tsv"))
signatures <- read_tsv(file.path(input_dir, "kda_signature_members.tsv.gz"))
significant_results <- read_tsv(file.path(input_dir, "kda_results.tsv.gz"))
artifacts <- read_tsv(file.path(input_dir, "kda_artifacts.tsv"))

require_columns(
  manifest,
  c(
    "kda_run_id", "analysis_tier", "fine_cell_type", "broad_network",
    "signature_group", "signature_direction", "effective_query_genes",
    "induced_network_edges", "effective_background_genes",
    "eligibility_status"
  ),
  "kda_run_manifest.tsv"
)
require_columns(
  signatures,
  c("kda_run_id", "gene", "effective_member"),
  "kda_signature_members.tsv.gz"
)
require_columns(
  significant_results,
  c(
    "kda_run_id", "analysis_tier", "fine_cell_type", "broad_network",
    "signature_group", "signature_direction", "key_driver", "best_layer",
    "overlap_count", "neighborhood_size", "non_neighborhood_size",
    "signature_size", "fold_enrichment", "log_p_value",
    "adjusted_p_value", "overlap_items"
  ),
  "kda_results.tsv.gz"
)
require_columns(artifacts, c("artifact_role", "path", "sha256"), "kda_artifacts.tsv")

directional <- manifest[
  manifest$analysis_tier == "primary" &
    manifest$signature_direction %in% c("AD_up_mito", "AD_down_mito") &
    manifest$eligibility_status == "eligible",
  ,
  drop = FALSE
]
assert_true(nrow(directional) > 0L, "No eligible primary directional KDA runs were found")
assert_true(!anyDuplicated(directional$kda_run_id), "Directional KDA run IDs are duplicated")
assert_true(
  setequal(unique(directional$broad_network), phase12_network_order),
  "Unexpected result-producing broad-network set"
)

kda_artifact <- artifacts[artifacts$artifact_role == "fKDA_source", , drop = FALSE]
assert_true(nrow(kda_artifact) == 1L, "The artifact table must contain one fKDA_source row")
assert_true(
  identical(sha256_file(kda_source), kda_artifact$sha256[[1L]]),
  "The reviewed fKDA source checksum does not match the validated artifact table"
)

network_rows <- artifacts[grepl("^network_", artifacts$artifact_role), , drop = FALSE]
network_paths <- setNames(
  vapply(network_rows$path, absolute_path, character(1), root = project_root),
  sub("^network_", "", network_rows$artifact_role)
)
for (network in phase12_network_order) {
  path <- network_paths[[network]]
  assert_true(!is.null(path) && file.exists(path), paste("Missing network for", network))
  expected_hash <- network_rows$sha256[network_rows$artifact_role == paste0("network_", network)]
  assert_true(length(expected_hash) == 1L, paste("Missing network hash for", network))
  assert_true(identical(sha256_file(path), expected_hash), paste("Network hash mismatch for", network))
}

message("Loading reviewed KDA neighborhood functions")
source(kda_source, local = .GlobalEnv)

network_cache <- new.env(parent = emptyenv())
read_network <- function(network) {
  if (exists(network, envir = network_cache, inherits = FALSE)) {
    return(get(network, envir = network_cache, inherits = FALSE))
  }
  tab <- utils::read.delim(
    network_paths[[network]], header = FALSE, sep = "\t", quote = "",
    comment.char = "", col.names = c("from", "to"), check.names = FALSE
  )
  tab <- unique(tab[
    !is.na(tab$from) & !is.na(tab$to) & nzchar(tab$from) & nzchar(tab$to) &
      tab$from != tab$to,
    ,
    drop = FALSE
  ])
  assign(network, tab, envir = network_cache)
  tab
}

empty_explicit_tests <- function() {
  data.frame(
    key_driver = character(), best_layer = integer(), overlap_count = integer(),
    neighborhood_size = integer(), non_neighborhood_size = integer(),
    signature_size = integer(), fold_enrichment = numeric(),
    raw_log_p_value = numeric(), raw_p_value = numeric(),
    adjusted_p_value = numeric(), candidate_test_status = character(),
    stringsAsFactors = FALSE
  )
}

compute_explicit_tests <- function(net, signature, background_size) {
  target_layers <- expandToNeighbors(
    seed = signature,
    net = net,
    nLayersToExpand = 3L,
    return.individual.layer = TRUE,
    directed = FALSE
  )
  if (is.null(target_layers) || !length(target_layers)) return(empty_explicit_tests())
  targets <- target_layers[[length(target_layers)]]
  rows <- lapply(targets, function(candidate) {
    neighbors <- getNeigobhors(
      node = candidate,
      net = net,
      nLayer = 3L,
      collapse = FALSE,
      directed = TRUE
    )
    if (is.null(neighbors) || !length(neighbors)) return(NULL)
    layer_rows <- lapply(seq_along(neighbors), function(layer) {
      neighborhood <- neighbors[[layer]]
      overlap_count <- sum(neighborhood %in% signature)
      neighborhood_size <- length(neighborhood)
      raw_log_p <- stats::phyper(
        overlap_count - 1,
        neighborhood_size,
        background_size - neighborhood_size,
        length(signature),
        lower.tail = FALSE,
        log.p = TRUE
      )
      data.frame(
        key_driver = candidate,
        best_layer = as.integer(layer),
        overlap_count = as.integer(overlap_count),
        neighborhood_size = as.integer(neighborhood_size),
        non_neighborhood_size = as.integer(background_size - neighborhood_size),
        signature_size = as.integer(length(signature)),
        fold_enrichment = round(
          overlap_count * background_size / neighborhood_size / length(signature),
          2
        ),
        raw_log_p_value = raw_log_p,
        stringsAsFactors = FALSE
      )
    })
    do.call(rbind, layer_rows)
  })
  rows <- rows[!vapply(rows, is.null, logical(1))]
  if (!length(rows)) return(empty_explicit_tests())
  result <- do.call(rbind, rows)
  result <- result[order(result$raw_log_p_value), , drop = FALSE]
  result <- result[!duplicated(result$key_driver), , drop = FALSE]
  result$raw_p_value <- exp(result$raw_log_p_value)
  result$adjusted_p_value <- stats::p.adjust(result$raw_p_value, method = "BH")
  result$candidate_test_status <- ifelse(
    result$overlap_count == 0L,
    "explicit_zero_overlap",
    "explicit_test"
  )
  rownames(result) <- NULL
  result
}

compare_significant_results <- function(run_id, explicit) {
  expected <- significant_results[
    significant_results$kda_run_id == run_id,
    ,
    drop = FALSE
  ]
  observed <- explicit[explicit$adjusted_p_value <= 0.05, , drop = FALSE]
  if (!nrow(expected) && !nrow(observed)) return(TRUE)
  if (nrow(expected) != nrow(observed)) return(FALSE)
  if (!setequal(expected$key_driver, observed$key_driver)) return(FALSE)
  observed <- observed[match(expected$key_driver, observed$key_driver), , drop = FALSE]
  integer_ok <-
    expected$best_layer == observed$best_layer &
    expected$overlap_count == observed$overlap_count &
    expected$neighborhood_size == observed$neighborhood_size &
    expected$non_neighborhood_size == observed$non_neighborhood_size &
    expected$signature_size == observed$signature_size
  numeric_ok <-
    abs(expected$fold_enrichment - observed$fold_enrichment) <= 1e-12 &
    abs(expected$log_p_value - observed$raw_log_p_value) <= 1e-12 &
    abs(expected$adjusted_p_value - observed$adjusted_p_value) <= 1e-12
  all(integer_ok) && all(numeric_ok)
}

update_named <- function(current, keys, increments) {
  old <- current[keys]
  old[is.na(old)] <- 0
  current[keys] <- old + increments
  current
}

state <- new.env(parent = emptyenv())
state$score_sum <- setNames(vector("list", length(phase12_network_order)), phase12_network_order)
state$ranking_runs <- setNames(vector("list", length(phase12_network_order)), phase12_network_order)
state$significant_runs <- setNames(vector("list", length(phase12_network_order)), phase12_network_order)
for (network in phase12_network_order) {
  state$score_sum[[network]] <- numeric()
  state$ranking_runs[[network]] <- numeric()
  state$significant_runs[[network]] <- numeric()
}
state$group_parts <- list()
state$check_parts <- list()
state$processed_run_ids <- character()

candidate_columns <- c(
  "schema_version", "kda_run_id", "analysis_tier", "fine_cell_type",
  "broad_network", "signature_group", "signature_direction", "key_driver",
  "best_layer", "overlap_count", "neighborhood_size",
  "non_neighborhood_size", "signature_size", "fold_enrichment",
  "raw_log_p_value", "raw_p_value", "adjusted_p_value",
  "candidate_test_status", "ranking_candidate"
)
candidate_path <- file.path(
  output_dir,
  "phase12_kda_primary_directional_candidate_tests.tsv.gz"
)
candidate_tmp <- file.path(
  output_dir,
  paste0(".", basename(candidate_path), ".tmp.", Sys.getpid())
)
candidate_connection <- gzfile(candidate_tmp, "wt", compression = 6)
candidate_connection_open <- TRUE
candidate_published <- FALSE
on.exit({
  if (candidate_connection_open) close(candidate_connection)
  if (!candidate_published && file.exists(candidate_tmp)) unlink(candidate_tmp)
}, add = TRUE)
writeLines(paste(candidate_columns, collapse = "\t"), candidate_connection)

process_run <- function(run_id, background) {
  meta <- directional[directional$kda_run_id == run_id, , drop = FALSE]
  assert_true(nrow(meta) == 1L, paste("Unexpected background run:", run_id))
  background <- sort(unique(background))
  assert_true(
    length(background) == meta$effective_background_genes[[1L]],
    paste("Background size mismatch for", run_id)
  )
  signature <- signatures$gene[
    signatures$kda_run_id == run_id & signatures$effective_member %in% TRUE
  ]
  signature <- sort(unique(signature))
  assert_true(
    length(signature) == meta$effective_query_genes[[1L]],
    paste("Effective signature size mismatch for", run_id)
  )
  network <- meta$broad_network[[1L]]
  full_network <- read_network(network)
  induced <- full_network[
    full_network$from %in% background & full_network$to %in% background,
    ,
    drop = FALSE
  ]
  assert_true(
    nrow(induced) == meta$induced_network_edges[[1L]],
    paste("Induced edge count mismatch for", run_id)
  )
  explicit <- compute_explicit_tests(induced, signature, length(background))
  assert_true(
    compare_significant_results(run_id, explicit),
    paste("Recomputed candidate tests do not match published results for", run_id)
  )

  implicit_genes <- setdiff(background, explicit$key_driver)
  implicit <- data.frame(
    key_driver = implicit_genes,
    best_layer = NA_integer_,
    overlap_count = 0L,
    neighborhood_size = 0L,
    non_neighborhood_size = as.integer(length(background)),
    signature_size = as.integer(length(signature)),
    fold_enrichment = NA_real_,
    raw_log_p_value = 0,
    raw_p_value = 1,
    adjusted_p_value = 1,
    candidate_test_status = "implicit_zero_overlap",
    stringsAsFactors = FALSE
  )
  tests <- if (nrow(explicit)) rbind(explicit, implicit) else implicit
  tests <- tests[order(tests$key_driver), , drop = FALSE]
  assert_true(
    nrow(tests) == length(background) && !anyDuplicated(tests$key_driver),
    paste("Candidate matrix is incomplete for", run_id)
  )

  output <- data.frame(
    schema_version = "phase12_kda_candidate_tests_figure_v1",
    kda_run_id = run_id,
    analysis_tier = meta$analysis_tier[[1L]],
    fine_cell_type = meta$fine_cell_type[[1L]],
    broad_network = network,
    signature_group = meta$signature_group[[1L]],
    signature_direction = meta$signature_direction[[1L]],
    tests,
    ranking_candidate = TRUE,
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
  output <- output[, candidate_columns, drop = FALSE]
  utils::write.table(
    output,
    file = candidate_connection,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    col.names = FALSE,
    na = "NA",
    append = TRUE
  )

  negative_log10 <- -tests$raw_log_p_value / log(10)
  significant <- as.numeric(tests$adjusted_p_value <= 0.05)
  state$score_sum[[network]] <- update_named(
    state$score_sum[[network]], tests$key_driver, negative_log10
  )
  state$ranking_runs[[network]] <- update_named(
    state$ranking_runs[[network]], tests$key_driver, rep(1, nrow(tests))
  )
  state$significant_runs[[network]] <- update_named(
    state$significant_runs[[network]], tests$key_driver, significant
  )

  pool_index <- tests$key_driver %in% phase12_candidate_pool
  if (any(pool_index)) {
    pool <- tests[pool_index, , drop = FALSE]
    state$group_parts[[length(state$group_parts) + 1L]] <- data.frame(
      broad_network = network,
      key_driver = pool$key_driver,
      signature_group = meta$signature_group[[1L]],
      signature_direction = meta$signature_direction[[1L]],
      negative_log10_p_sum = -pool$raw_log_p_value / log(10),
      significant_runs = as.numeric(pool$adjusted_p_value <= 0.05),
      candidate_runs_tested = 1,
      stringsAsFactors = FALSE
    )
  }

  state$check_parts[[length(state$check_parts) + 1L]] <- data.frame(
    kda_run_id = run_id,
    broad_network = network,
    background_genes = length(background),
    explicit_candidates = nrow(explicit),
    implicit_zero_overlap_candidates = length(implicit_genes),
    published_significant_candidates = sum(explicit$adjusted_p_value <= 0.05),
    published_result_reconciliation = TRUE,
    stringsAsFactors = FALSE
  )
  state$processed_run_ids <- c(state$processed_run_ids, run_id)
  message(
    sprintf(
      "[%d/%d] %s: %d background, %d explicit candidates",
      length(state$processed_run_ids), nrow(directional), run_id,
      length(background), nrow(explicit)
    )
  )
  invisible(TRUE)
}

background_path <- file.path(input_dir, "kda_background_members.tsv.gz")
assert_true(file.exists(background_path), "Missing compressed Phase 12 background-members table")
pattern_file <- tempfile("phase12_directional_run_patterns_", fileext = ".txt")
on.exit(if (file.exists(pattern_file)) unlink(pattern_file), add = TRUE)
writeLines(paste0("\t", directional$kda_run_id, "\t"), pattern_file, useBytes = TRUE)
stream_command <- paste(
  "gzip -dc", shQuote(background_path),
  "| grep -F -f", shQuote(pattern_file)
)
message("Streaming relevant backgrounds from the 1.1 GB uncompressed membership table")
background_connection <- pipe(stream_command, open = "r")
background_connection_open <- TRUE
on.exit(if (background_connection_open) close(background_connection), add = TRUE)

current_run <- NULL
current_genes <- character()
repeat {
  lines <- readLines(background_connection, n = 50000L, warn = FALSE)
  if (!length(lines)) break
  first_tab <- regexpr("\t", lines, fixed = TRUE)
  rest <- substring(lines, first_tab + 1L)
  second_tab <- regexpr("\t", rest, fixed = TRUE)
  run_ids <- substr(rest, 1L, second_tab - 1L)
  genes <- substring(rest, second_tab + 1L)
  starts <- c(1L, which(run_ids[-1L] != run_ids[-length(run_ids)]) + 1L)
  ends <- c(starts[-1L] - 1L, length(run_ids))
  for (index in seq_along(starts)) {
    run_id <- run_ids[[starts[[index]]]]
    segment_genes <- genes[starts[[index]]:ends[[index]]]
    if (is.null(current_run)) current_run <- run_id
    if (!identical(run_id, current_run)) {
      process_run(current_run, current_genes)
      current_run <- run_id
      current_genes <- character()
    }
    current_genes <- c(current_genes, segment_genes)
  }
}
if (!is.null(current_run)) process_run(current_run, current_genes)
close(background_connection)
background_connection_open <- FALSE

assert_true(
  identical(state$processed_run_ids, directional$kda_run_id),
  "The streamed background order or run set did not match the directional manifest"
)
close(candidate_connection)
candidate_connection_open <- FALSE
assert_true(file.exists(candidate_tmp) && file.info(candidate_tmp)$size > 0, "Candidate export is empty")
if (!file.rename(candidate_tmp, candidate_path)) {
  stop("Could not publish candidate-test table: ", candidate_path, call. = FALSE)
}
candidate_published <- TRUE

eligible_by_network <- table(factor(directional$broad_network, levels = phase12_network_order))
summary_parts <- lapply(phase12_network_order, function(network) {
  genes <- names(state$ranking_runs[[network]])
  count <- unname(state$ranking_runs[[network]][genes])
  score_sum <- unname(state$score_sum[[network]][genes])
  significant <- unname(state$significant_runs[[network]][genes])
  mean_score <- score_sum / count
  maximum <- max(mean_score, na.rm = TRUE)
  data.frame(
    schema_version = "phase12_kda_mean_of_log_summary_v1",
    broad_network = network,
    key_driver = genes,
    mean_of_log_score = mean_score,
    mean_of_log_score_standardized = if (maximum > 0) mean_score / maximum else 0,
    ranking_runs = as.integer(count),
    eligible_directional_runs = as.integer(eligible_by_network[[network]]),
    ranking_coverage_fraction = count / as.integer(eligible_by_network[[network]]),
    primary_directional_significant_runs = as.integer(significant),
    primary_directional_recurrence_fraction = significant / count,
    mtDNA_encoded = grepl("^MT-", genes),
    stringsAsFactors = FALSE
  )
})
mean_summary <- do.call(rbind, summary_parts)
mean_summary$network_display_order <- match(mean_summary$broad_network, phase12_network_order)
mean_summary <- mean_summary[
  order(
    mean_summary$network_display_order,
    -mean_summary$mean_of_log_score_standardized,
    -mean_summary$ranking_runs,
    -mean_summary$primary_directional_recurrence_fraction,
    mean_summary$key_driver
  ),
  ,
  drop = FALSE
]
rownames(mean_summary) <- NULL

self_member <- mapply(
  function(driver, items) {
    if (is.na(items) || !nzchar(items)) return(FALSE)
    driver %in% strsplit(items, ";", fixed = TRUE)[[1L]]
  },
  significant_results$key_driver,
  significant_results$overlap_items,
  USE.NAMES = FALSE
)
strict_index <-
  significant_results$analysis_tier == "primary" &
  significant_results$signature_direction %in% c("AD_up_mito", "AD_down_mito") &
  !grepl("^MT-", significant_results$key_driver) &
  !self_member &
  significant_results$overlap_count >= 2L &
  significant_results$signature_size >= 10L
strict <- significant_results[strict_index, , drop = FALSE]
strict_keys <- unique(strict[, c("broad_network", "key_driver"), drop = FALSE])
strict_parts <- lapply(seq_len(nrow(strict_keys)), function(index) {
  network <- strict_keys$broad_network[[index]]
  driver <- strict_keys$key_driver[[index]]
  x <- strict[strict$broad_network == network & strict$key_driver == driver, , drop = FALSE]
  data.frame(
    schema_version = "phase12_kda_conservative_candidate_summary_v1",
    broad_network = network,
    key_driver = driver,
    conservative_significant_runs = length(unique(x$kda_run_id)),
    conservative_fine_cell_types = length(unique(x$fine_cell_type)),
    highlighted_candidate_pool = driver %in% phase12_candidate_pool,
    stringsAsFactors = FALSE
  )
})
conservative_summary <- do.call(rbind, strict_parts)
conservative_summary$network_display_order <- match(
  conservative_summary$broad_network, phase12_network_order
)
conservative_summary <- conservative_summary[
  order(
    conservative_summary$network_display_order,
    -conservative_summary$conservative_significant_runs,
    -conservative_summary$conservative_fine_cell_types,
    conservative_summary$key_driver
  ),
  ,
  drop = FALSE
]
rownames(conservative_summary) <- NULL

group_rows <- do.call(rbind, state$group_parts)
group_summary <- stats::aggregate(
  cbind(negative_log10_p_sum, significant_runs, candidate_runs_tested) ~
    broad_network + key_driver + signature_group + signature_direction,
  data = group_rows,
  FUN = sum
)
group_summary$mean_minus_log10_p <-
  group_summary$negative_log10_p_sum / group_summary$candidate_runs_tested
eligible_group <- stats::aggregate(
  kda_run_id ~ broad_network + signature_group + signature_direction,
  data = directional,
  FUN = length
)
names(eligible_group)[[4L]] <- "eligible_runs"
group_summary <- merge(
  group_summary,
  eligible_group,
  by = c("broad_network", "signature_group", "signature_direction"),
  all.x = TRUE,
  sort = FALSE
)
group_summary$ranking_coverage_fraction <-
  group_summary$candidate_runs_tested / group_summary$eligible_runs
group_summary$significant_run_fraction <-
  group_summary$significant_runs / group_summary$candidate_runs_tested
group_summary$sex <- ifelse(grepl("^F_", group_summary$signature_group), "Female", "Male")
group_summary$apoe_group <- sub("^[FM]_", "", group_summary$signature_group)
group_summary$schema_version <- "phase12_kda_candidate_group_summary_v1"
group_summary$network_display_order <- match(group_summary$broad_network, phase12_network_order)
group_order <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
direction_order <- c("AD_up_mito", "AD_down_mito")
group_summary <- group_summary[
  order(
    group_summary$network_display_order,
    group_summary$key_driver,
    match(group_summary$signature_direction, direction_order),
    match(group_summary$signature_group, group_order)
  ),
  c(
    "schema_version", "broad_network", "network_display_order", "key_driver",
    "signature_group", "sex", "apoe_group", "signature_direction",
    "candidate_runs_tested", "eligible_runs", "ranking_coverage_fraction",
    "significant_runs", "significant_run_fraction", "mean_minus_log10_p",
    "negative_log10_p_sum"
  ),
  drop = FALSE
]
rownames(group_summary) <- NULL

run_checks <- do.call(rbind, state$check_parts)
checks <- data.frame(
  schema_version = "phase12_kda_figure_data_checks_v1",
  check_id = c(
    "eligible_primary_directional_runs",
    "all_runs_processed_once",
    "published_significant_results_reconciled",
    "candidate_matrix_complete_within_background",
    "mean_scores_finite_nonnegative",
    "ranking_coverage_in_unit_interval",
    "group_recurrence_in_unit_interval"
  ),
  passed = c(
    nrow(directional) == 295L,
    length(state$processed_run_ids) == nrow(directional) &&
      !anyDuplicated(state$processed_run_ids),
    all(run_checks$published_result_reconciliation),
    all(
      run_checks$background_genes ==
        run_checks$explicit_candidates + run_checks$implicit_zero_overlap_candidates
    ),
    all(is.finite(mean_summary$mean_of_log_score)) &&
      all(mean_summary$mean_of_log_score >= 0),
    all(mean_summary$ranking_coverage_fraction > 0 &
      mean_summary$ranking_coverage_fraction <= 1),
    all(group_summary$significant_run_fraction >= 0 &
      group_summary$significant_run_fraction <= 1)
  ),
  observed = c(
    nrow(directional),
    length(state$processed_run_ids),
    sum(run_checks$published_result_reconciliation),
    sum(
      run_checks$background_genes ==
        run_checks$explicit_candidates + run_checks$implicit_zero_overlap_candidates
    ),
    sum(is.finite(mean_summary$mean_of_log_score) & mean_summary$mean_of_log_score >= 0),
    sum(mean_summary$ranking_coverage_fraction > 0 &
      mean_summary$ranking_coverage_fraction <= 1),
    sum(group_summary$significant_run_fraction >= 0 &
      group_summary$significant_run_fraction <= 1)
  ),
  expected = c(
    295L,
    nrow(directional),
    nrow(run_checks),
    nrow(run_checks),
    nrow(mean_summary),
    nrow(mean_summary),
    nrow(group_summary)
  ),
  stringsAsFactors = FALSE
)
assert_true(all(checks$passed), "At least one prepared figure-data validation check failed")

atomic_write_table(
  mean_summary,
  file.path(output_dir, "phase12_kda_mean_of_log_summary.tsv")
)
atomic_write_table(
  conservative_summary,
  file.path(output_dir, "phase12_kda_conservative_candidate_summary.tsv")
)
atomic_write_table(
  group_summary,
  file.path(output_dir, "phase12_kda_candidate_group_summary.tsv")
)
atomic_write_table(
  run_checks,
  file.path(output_dir, "phase12_kda_candidate_run_reconciliation.tsv")
)
atomic_write_table(
  checks,
  file.path(output_dir, "phase12_kda_figure_data_checks.tsv")
)

message(
  "Prepared complete Figure A/B data: ", nrow(directional),
  " primary directional runs; ", nrow(mean_summary),
  " network-driver summaries"
)
