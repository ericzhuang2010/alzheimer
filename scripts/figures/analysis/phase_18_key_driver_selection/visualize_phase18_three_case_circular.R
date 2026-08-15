#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

common_path <- file.path(
  "scripts", "figures", "analysis", "phease12_kda",
  "phase12_kda_figure_common.R"
)
if (!file.exists(common_path)) {
  stop("Missing shared figure helper: ", common_path, call. = FALSE)
}
source(common_path)

usage <- function() {
  cat(
    "Usage: Rscript --vanilla scripts/figures/analysis/",
    "phase_18_key_driver_selection/visualize_phase18_three_case_circular.R ",
    "[--input-dir DIR] [--output-dir DIR] [--top-per-network N] ",
    "[--evidence-cap VALUE] [--png-dpi DPI] [--width-inches VALUE] ",
    "[--height-inches VALUE]\n",
    sep = ""
  )
}

cli_args <- commandArgs(trailingOnly = TRUE)
args <- parse_value_args(
  cli_args,
  defaults = list(
    input_dir = "results/minerva_production/18_key_driver_selection",
    output_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "three_case_circular"
    ),
    top_per_network = "5",
    evidence_cap = "15",
    png_dpi = "450",
    width_inches = "12",
    height_inches = "7.2"
  ),
  allowed = c(
    "--input-dir", "--output-dir", "--top-per-network", "--evidence-cap",
    "--png-dpi", "--width-inches", "--height-inches"
  )
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

top_per_network <- suppressWarnings(as.integer(args$top_per_network))
evidence_cap <- suppressWarnings(as.numeric(args$evidence_cap))
png_dpi <- suppressWarnings(as.integer(args$png_dpi))
figure_width_inches <- suppressWarnings(as.numeric(args$width_inches))
figure_height_inches <- suppressWarnings(as.numeric(args$height_inches))

assert_true(
  length(top_per_network) == 1L && is.finite(top_per_network) &&
    top_per_network == 5L,
  "The frozen Phase 18 display limit is exactly five"
)
assert_true(
  length(evidence_cap) == 1L && is.finite(evidence_cap) && evidence_cap > 0,
  "--evidence-cap must be a positive number"
)
assert_true(
  length(png_dpi) == 1L && is.finite(png_dpi) && png_dpi >= 300L,
  "--png-dpi must be at least 300"
)
assert_true(
  length(figure_width_inches) == 1L && is.finite(figure_width_inches) &&
    figure_width_inches > 0 &&
    length(figure_height_inches) == 1L && is.finite(figure_height_inches) &&
    figure_height_inches > 0,
  "Figure dimensions must be positive"
)
legend_panel_width_inches <- figure_width_inches - figure_height_inches
assert_true(
  legend_panel_width_inches >= 4,
  paste0(
    "The double-size right-side legend requires a canvas at least 4 inches ",
    "wider than it is tall"
  )
)
circle_panel_fraction <- figure_height_inches / figure_width_inches
legend_text_multiplier <- 2
assert_true(capabilities("cairo"), "This R installation lacks Cairo support")
assert_true(
  file.exists("/usr/bin/shasum"),
  "The renderer requires /usr/bin/shasum for SHA-256 validation"
)

project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
input_dir <- normalizePath(input_dir, mustWork = TRUE)

phase18_network_order <- c(
  "Astrocytes",
  "Excitatory_neurons",
  "Inhibitory_neurons",
  "Microglia",
  "OPCs",
  "Oligodendrocytes",
  "Vasculature_cells"
)
assert_true(
  identical(phase18_network_order, phase12_network_order),
  "Phase 18 network order no longer matches the reduced Phase 12 reference"
)

case_order <- c(
  "case1_core_mito_in_query",
  "case2_core_mito_not_in_query",
  "case3_not_core_mito"
)
case_titles <- c(
  case1_core_mito_in_query =
    "Case 1 — core MitoCarta driver in the run query",
  case2_core_mito_not_in_query =
    "Case 2 — core MitoCarta driver outside the run query",
  case3_not_core_mito =
    "Case 3 — driver outside the 1,136-gene core MitoCarta inventory"
)
case_basenames <- c(
  case1_core_mito_in_query = "phase18_case1_core_mito_in_query_circular",
  case2_core_mito_not_in_query =
    "phase18_case2_core_mito_not_in_query_circular",
  case3_not_core_mito = "phase18_case3_not_core_mito_circular"
)

required_source_files <- c(
  "key_driver_status.tsv",
  "key_driver_checks.tsv",
  "key_driver_artifacts.tsv",
  "key_driver_analysis_manifest.tsv",
  "key_driver_case_manifest.tsv",
  "key_driver_top5.tsv",
  "key_driver_figure_data.tsv",
  "key_driver_candidates.tsv"
)

source_paths <- setNames(
  file.path(input_dir, required_source_files),
  required_source_files
)
missing_source_files <- required_source_files[!file.exists(source_paths)]
assert_true(
  !length(missing_source_files),
  paste("Missing Phase 18 source files:", paste(missing_source_files, collapse = ", "))
)

status <- read_tsv(source_paths[["key_driver_status.tsv"]])
phase18_checks <- read_tsv(source_paths[["key_driver_checks.tsv"]])
artifacts <- read_tsv(source_paths[["key_driver_artifacts.tsv"]])
analysis_manifest <- read_tsv(source_paths[["key_driver_analysis_manifest.tsv"]])
case_manifest <- read_tsv(source_paths[["key_driver_case_manifest.tsv"]])
top5 <- read_tsv(source_paths[["key_driver_top5.tsv"]])
figure_data <- read_tsv(source_paths[["key_driver_figure_data.tsv"]])
candidates <- read_tsv(source_paths[["key_driver_candidates.tsv"]])

require_columns(
  status,
  c(
    "validation_status", "included_broad_networks", "phase18_cases",
    "driver_candidates", "top5_network_case_lists", "failed_checks"
  ),
  "key_driver_status.tsv"
)
require_columns(
  phase18_checks,
  c("check_id", "severity", "observed", "expected", "passed"),
  "key_driver_checks.tsv"
)
require_columns(
  artifacts,
  c("path", "declared", "rows", "bytes", "sha256", "hash_status"),
  "key_driver_artifacts.tsv"
)
require_columns(
  analysis_manifest,
  c(
    "minimum_coverage", "aggregate_q_threshold", "ranking_order",
    "display_limit", "validation_class"
  ),
  "key_driver_analysis_manifest.tsv"
)
require_columns(
  case_manifest,
  c("case_order", "case_id", "case_label", "exact_rule"),
  "key_driver_case_manifest.tsv"
)
top5_columns <- c(
  "broad_network", "case_order", "case_id", "list_status",
  "total_passing_candidate_count", "displayed_candidate_count",
  "display_rank", "current_symbol", "aggregate_acat_p", "aggregate_acat_q",
  "coverage_numerator", "coverage_denominator", "coverage_fraction",
  "conservative_support_count", "evidence_tier", "empty_result_reason"
)
require_columns(top5, top5_columns, "key_driver_top5.tsv")
require_columns(
  figure_data,
  c(
    top5_columns, "supporting_groups", "supporting_directions",
    "supporting_fine_cell_types"
  ),
  "key_driver_figure_data.tsv"
)
require_columns(
  candidates,
  c(
    "broad_network", "current_symbol", "case_order", "case_id",
    "is_core_mito", "mitocarta_canonical_symbol", "mito_tier",
    "genome_origin", "is_mtdna_gene", "extended_reference_member",
    "mapping_status", "aggregate_acat_p", "aggregate_acat_q",
    "terminal_candidate_status", "within_case_rank", "top5_display",
    "evidence_tier"
  ),
  "key_driver_candidates.tsv"
)

assert_true(
  nrow(status) == 1L && status$validation_status[[1L]] == "validated_complete",
  "Phase 18 must be validated_complete before figure generation"
)
assert_true(
  status$included_broad_networks[[1L]] == 7L &&
    status$phase18_cases[[1L]] == 3L &&
    status$driver_candidates[[1L]] == 109L &&
    status$top5_network_case_lists[[1L]] == 27L &&
    status$failed_checks[[1L]] == 0L,
  "Phase 18 status does not match the frozen validated bundle"
)
assert_true(
  nrow(phase18_checks) > 0L && !anyNA(phase18_checks$passed) &&
    all(phase18_checks$passed),
  "At least one Phase 18 validation check is missing or failed"
)
assert_true(
  nrow(analysis_manifest) == 1L &&
    analysis_manifest$validation_class[[1L]] == "validated_complete" &&
    analysis_manifest$display_limit[[1L]] == 5L &&
    analysis_manifest$ranking_order[[1L]] ==
      "aggregate_acat_q|aggregate_acat_p|current_symbol" &&
    abs(analysis_manifest$minimum_coverage[[1L]] - 0.8) < 1e-12 &&
    abs(analysis_manifest$aggregate_q_threshold[[1L]] - 0.05) < 1e-12,
  "Phase 18 analysis manifest does not match the frozen figure contract"
)
assert_true(
  nrow(case_manifest) == 3L &&
    identical(case_manifest$case_id[order(case_manifest$case_order)], case_order),
  "The Phase 18 case manifest does not contain the expected ordered cases"
)

sha256_file <- function(path) {
  output <- system2(
    "/usr/bin/shasum",
    c("-a", "256", shQuote(path)),
    stdout = TRUE,
    stderr = TRUE
  )
  status_code <- attr(output, "status") %||% 0L
  assert_true(status_code == 0L && length(output) >= 1L, paste("Could not hash", path))
  strsplit(trimws(output[[1L]]), "[[:space:]]+")[[1L]][[1L]]
}

source_hashes <- data.frame(
  file = required_source_files,
  declared_sha256 = NA_character_,
  observed_sha256 = vapply(source_paths, sha256_file, character(1L)),
  hash_match = NA,
  stringsAsFactors = FALSE
)
for (index in seq_len(nrow(source_hashes))) {
  artifact_row <- artifacts[artifacts$path == source_hashes$file[[index]], , drop = FALSE]
  if (nrow(artifact_row) == 1L && !is.na(artifact_row$sha256[[1L]])) {
    source_hashes$declared_sha256[[index]] <- artifact_row$sha256[[1L]]
    source_hashes$hash_match[[index]] <-
      identical(
        source_hashes$observed_sha256[[index]],
        source_hashes$declared_sha256[[index]]
      )
  }
}
assert_true(
  all(source_hashes$hash_match[!is.na(source_hashes$hash_match)]),
  "At least one Phase 18 source hash differs from key_driver_artifacts.tsv"
)

normalize_compare <- function(x) {
  if (is.factor(x)) as.character(x) else x
}

for (column in top5_columns) {
  left <- normalize_compare(top5[[column]])
  right <- normalize_compare(figure_data[[column]])
  assert_true(
    isTRUE(all.equal(left, right, check.attributes = FALSE)),
    paste("key_driver_top5.tsv and key_driver_figure_data.tsv differ in", column)
  )
}
assert_true(
  nrow(top5) == nrow(figure_data),
  "The top-five and figure-data tables have different row counts"
)

allowed_list_statuses <- c(
  "ranked_candidates",
  "no_passing_candidate",
  "not_testable_no_included_runs",
  "not_testable_no_eligible_case_runs"
)
assert_true(
  all(top5$list_status %in% allowed_list_statuses),
  "The top-five table contains an unsupported list status"
)

list_keys <- unique(top5[c("broad_network", "case_id")])
assert_true(
  nrow(list_keys) == 27L,
  "The top-five table must contain 9 broad networks x 3 cases"
)
assert_true(
  all(c("CAMs", "T_cells", phase18_network_order) %in% list_keys$broad_network),
  "The top-five table is missing a declared broad network"
)
assert_true(
  all(
    top5$list_status[top5$broad_network %in% c("CAMs", "T_cells")] ==
      "not_testable_no_included_runs"
  ),
  "CAMs and T cells must be recorded as having no included Phase 18 runs"
)

ranked_top5 <- top5[top5$list_status == "ranked_candidates", , drop = FALSE]
assert_true(
  nrow(ranked_top5) == 63L && !anyNA(ranked_top5$current_symbol) &&
    !anyNA(ranked_top5$display_rank),
  "The validated top-five table should contain 63 displayed candidate rows"
)
assert_true(
  all(ranked_top5$display_rank >= 1L & ranked_top5$display_rank <= 5L),
  "A displayed rank falls outside 1-5"
)
assert_true(
  !anyDuplicated(
    paste(
      ranked_top5$broad_network, ranked_top5$case_id,
      ranked_top5$display_rank, sep = "\r"
    )
  ),
  "A displayed rank is duplicated within a network and case"
)
assert_true(
  !anyDuplicated(
    paste(
      ranked_top5$broad_network, ranked_top5$case_id,
      ranked_top5$current_symbol, sep = "\r"
    )
  ),
  "A displayed symbol is duplicated within a network and case"
)

candidate_key <- paste(
  candidates$broad_network, candidates$case_id, candidates$current_symbol,
  sep = "\r"
)
ranked_key <- paste(
  ranked_top5$broad_network, ranked_top5$case_id, ranked_top5$current_symbol,
  sep = "\r"
)
candidate_match <- match(ranked_key, candidate_key)
assert_true(
  !anyNA(candidate_match) && !anyDuplicated(candidate_key),
  "Displayed rows do not join one-to-one to key_driver_candidates.tsv"
)
displayed_candidates <- candidates[candidate_match, , drop = FALSE]
assert_true(
  all(displayed_candidates$terminal_candidate_status == "driver_candidate") &&
    all(displayed_candidates$top5_display %in% TRUE),
  "A displayed row is not a frozen Phase 18 top-five driver candidate"
)
assert_true(
  isTRUE(all.equal(
    ranked_top5$display_rank,
    displayed_candidates$within_case_rank,
    check.attributes = FALSE
  )),
  "Top-five display ranks differ from candidate within-case ranks"
)
for (column in c("aggregate_acat_p", "aggregate_acat_q", "evidence_tier")) {
  assert_true(
    isTRUE(all.equal(
      normalize_compare(ranked_top5[[column]]),
      normalize_compare(displayed_candidates[[column]]),
      check.attributes = FALSE
    )),
    paste("Top-five values differ from candidate values in", column)
  )
}

expected_case_counts <- c(
  case1_core_mito_in_query = 27L,
  case2_core_mito_not_in_query = 15L,
  case3_not_core_mito = 21L
)
observed_case_counts <- table(factor(ranked_top5$case_id, levels = case_order))
assert_true(
  identical(as.integer(observed_case_counts), as.integer(expected_case_counts)),
  "Displayed case counts do not reconcile to 27, 15, and 21"
)

geometry_rows <- vector("list", length(phase18_network_order) * top_per_network)
network_gap <- 6
slot_gap <- 1
total_slots <- length(phase18_network_order) * top_per_network
total_gap <- length(phase18_network_order) * network_gap +
  (total_slots - length(phase18_network_order)) * slot_gap
slot_width <- (360 - total_gap) / total_slots
cursor <- 90
geometry_index <- 1L
for (network_index in seq_along(phase18_network_order)) {
  network <- phase18_network_order[[network_index]]
  for (slot_rank in seq_len(top_per_network)) {
    start_degrees <- cursor
    end_degrees <- start_degrees - slot_width
    geometry_rows[[geometry_index]] <- data.frame(
      broad_network = network,
      network_display_order = network_index,
      slot_rank = slot_rank,
      sector_start_degrees = start_degrees,
      sector_end_degrees = end_degrees,
      sector_mid_degrees = (start_degrees + end_degrees) / 2,
      stringsAsFactors = FALSE
    )
    cursor <- end_degrees - if (slot_rank < top_per_network) slot_gap else network_gap
    geometry_index <- geometry_index + 1L
  }
}
geometry <- do.call(rbind, geometry_rows)
rownames(geometry) <- NULL

safe_value <- function(x, default = NA) {
  if (!length(x)) default else x[[1L]]
}

build_slot_row <- function(case_id, geometry_row, top_row, figure_row, candidate_row,
                           slot_status) {
  candidate_present <- identical(slot_status, "ranked_candidate")
  data.frame(
    schema_version = "phase18_three_case_circular_plot_data_v1",
    case_order = match(case_id, case_order),
    case_id = case_id,
    case_label = case_manifest$case_label[match(case_id, case_manifest$case_id)],
    broad_network = geometry_row$broad_network,
    network_display_order = geometry_row$network_display_order,
    display_network = unname(phase12_network_labels[geometry_row$broad_network]),
    network_color = unname(phase12_network_colors[geometry_row$broad_network]),
    slot_rank = geometry_row$slot_rank,
    slot_status = slot_status,
    list_status = safe_value(top_row$list_status),
    empty_result_reason = safe_value(top_row$empty_result_reason),
    total_passing_candidate_count = safe_value(top_row$total_passing_candidate_count),
    displayed_candidate_count = safe_value(top_row$displayed_candidate_count),
    display_rank = if (candidate_present) safe_value(top_row$display_rank) else NA_integer_,
    current_symbol = if (candidate_present) safe_value(top_row$current_symbol) else NA_character_,
    is_core_mito = if (candidate_present) safe_value(candidate_row$is_core_mito) else NA,
    mitocarta_canonical_symbol = if (candidate_present) {
      safe_value(candidate_row$mitocarta_canonical_symbol)
    } else {
      NA_character_
    },
    mapping_status = if (candidate_present) safe_value(candidate_row$mapping_status) else NA_character_,
    mito_tier = if (candidate_present) safe_value(candidate_row$mito_tier) else NA_character_,
    genome_origin = if (candidate_present) safe_value(candidate_row$genome_origin) else NA_character_,
    is_mtdna_gene = if (candidate_present) safe_value(candidate_row$is_mtdna_gene) else NA,
    extended_reference_member = if (candidate_present) {
      safe_value(candidate_row$extended_reference_member)
    } else {
      NA
    },
    aggregate_acat_p = if (candidate_present) safe_value(top_row$aggregate_acat_p) else NA_real_,
    aggregate_acat_q = if (candidate_present) safe_value(top_row$aggregate_acat_q) else NA_real_,
    negative_log10_acat_q = if (candidate_present) {
      -log10(max(safe_value(top_row$aggregate_acat_q), .Machine$double.xmin))
    } else {
      NA_real_
    },
    capped_negative_log10_acat_q = NA_real_,
    display_score = NA_real_,
    coverage_numerator = if (candidate_present) safe_value(top_row$coverage_numerator) else NA_integer_,
    coverage_denominator = if (candidate_present) safe_value(top_row$coverage_denominator) else NA_integer_,
    coverage_fraction = if (candidate_present) safe_value(top_row$coverage_fraction) else NA_real_,
    conservative_support_count = if (candidate_present) {
      safe_value(top_row$conservative_support_count)
    } else {
      NA_integer_
    },
    evidence_tier = if (candidate_present) safe_value(top_row$evidence_tier) else NA_character_,
    supporting_groups = if (candidate_present) safe_value(figure_row$supporting_groups) else NA_character_,
    supporting_directions = if (candidate_present) {
      safe_value(figure_row$supporting_directions)
    } else {
      NA_character_
    },
    supporting_fine_cell_types = if (candidate_present) {
      safe_value(figure_row$supporting_fine_cell_types)
    } else {
      NA_character_
    },
    selected_network_count_within_case = NA_integer_,
    sector_start_degrees = geometry_row$sector_start_degrees,
    sector_end_degrees = geometry_row$sector_end_degrees,
    sector_mid_degrees = geometry_row$sector_mid_degrees,
    source_top5_sha256 = source_hashes$observed_sha256[
      source_hashes$file == "key_driver_top5.tsv"
    ],
    source_candidates_sha256 = source_hashes$observed_sha256[
      source_hashes$file == "key_driver_candidates.tsv"
    ],
    source_figure_data_sha256 = source_hashes$observed_sha256[
      source_hashes$file == "key_driver_figure_data.tsv"
    ],
    stringsAsFactors = FALSE
  )
}

plot_rows <- vector("list", length(case_order) * nrow(geometry))
plot_index <- 1L
for (case_id in case_order) {
  for (geometry_index in seq_len(nrow(geometry))) {
    geometry_row <- geometry[geometry_index, , drop = FALSE]
    network_rows <- top5[
      top5$case_id == case_id &
        top5$broad_network == geometry_row$broad_network,
      ,
      drop = FALSE
    ]
    assert_true(nrow(network_rows) >= 1L, "Missing included network-case list")
    list_status <- unique(network_rows$list_status)
    assert_true(length(list_status) == 1L, "Mixed list statuses within a network and case")

    if (list_status == "ranked_candidates") {
      ranked_row <- network_rows[
        network_rows$display_rank == geometry_row$slot_rank,
        ,
        drop = FALSE
      ]
      if (nrow(ranked_row) == 1L) {
        row_number <- which(
          figure_data$case_id == case_id &
            figure_data$broad_network == geometry_row$broad_network &
            figure_data$current_symbol == ranked_row$current_symbol
        )
        candidate_number <- which(
          candidates$case_id == case_id &
            candidates$broad_network == geometry_row$broad_network &
            candidates$current_symbol == ranked_row$current_symbol
        )
        assert_true(
          length(row_number) == 1L && length(candidate_number) == 1L,
          "Displayed candidate annotation join is not one-to-one"
        )
        plot_rows[[plot_index]] <- build_slot_row(
          case_id,
          geometry_row,
          ranked_row,
          figure_data[row_number, , drop = FALSE],
          candidates[candidate_number, , drop = FALSE],
          "ranked_candidate"
        )
      } else {
        assert_true(
          nrow(ranked_row) == 0L &&
            geometry_row$slot_rank > unique(network_rows$displayed_candidate_count),
          "Ranked list contains a nonconsecutive or missing displayed rank"
        )
        plot_rows[[plot_index]] <- build_slot_row(
          case_id,
          geometry_row,
          network_rows[1L, , drop = FALSE],
          data.frame(),
          data.frame(),
          "unused_display_slot"
        )
      }
    } else if (list_status == "no_passing_candidate") {
      assert_true(
        nrow(network_rows) == 1L &&
          network_rows$total_passing_candidate_count[[1L]] == 0L &&
          network_rows$displayed_candidate_count[[1L]] == 0L &&
          is.na(network_rows$current_symbol[[1L]]),
        "A no-passing-candidate list contains unexpected candidate data"
      )
      plot_rows[[plot_index]] <- build_slot_row(
        case_id,
        geometry_row,
        network_rows,
        data.frame(),
        data.frame(),
        "no_passing_candidate_slot"
      )
    } else {
      stop(
        "Included network has unsupported list status: ", list_status,
        call. = FALSE
      )
    }
    plot_index <- plot_index + 1L
  }
}

plot_data <- do.call(rbind, plot_rows)
rownames(plot_data) <- NULL
occupied <- plot_data$slot_status == "ranked_candidate"
plot_data$capped_negative_log10_acat_q[occupied] <- pmin(
  plot_data$negative_log10_acat_q[occupied], evidence_cap
)
plot_data$display_score[occupied] <-
  plot_data$capped_negative_log10_acat_q[occupied] / evidence_cap

selection_counts <- table(
  paste(
    plot_data$case_id[occupied], plot_data$current_symbol[occupied],
    sep = "\r"
  )
)
plot_data$selected_network_count_within_case[occupied] <- as.integer(
  selection_counts[
    paste(
      plot_data$case_id[occupied], plot_data$current_symbol[occupied],
      sep = "\r"
    )
  ]
)

assert_true(
  nrow(plot_data) == 105L &&
    all(table(plot_data$case_id) == 35L) &&
    all(table(plot_data$case_id[occupied]) == expected_case_counts),
  "The fixed-slot plotted data do not reconcile to 35 rows per case"
)
assert_true(
  all(plot_data$display_score[occupied] > 0 &
    plot_data$display_score[occupied] <= 1),
  "A displayed evidence score falls outside (0, 1]"
)
assert_true(
  all(plot_data$is_core_mito[
    occupied & plot_data$case_id == "case1_core_mito_in_query"
  ] %in% TRUE) &&
    all(!plot_data$is_core_mito[
      occupied & plot_data$case_id == "case3_not_core_mito"
    ]),
  "Case 1 or Case 3 core MitoCarta membership is inconsistent"
)

expected_empty_keys <- c(
  "case2_core_mito_not_in_query\rOligodendrocytes",
  "case2_core_mito_not_in_query\rVasculature_cells",
  "case3_not_core_mito\rVasculature_cells"
)
observed_empty_keys <- unique(paste(
  plot_data$case_id[plot_data$slot_status == "no_passing_candidate_slot"],
  plot_data$broad_network[
    plot_data$slot_status == "no_passing_candidate_slot"
  ],
  sep = "\r"
))
assert_true(
  setequal(expected_empty_keys, observed_empty_keys),
  "Explicit empty-result networks do not match the validated Phase 18 bundle"
)

link_rows <- list()
link_index <- 1L
for (case_id in case_order) {
  case_candidates <- plot_data[
    plot_data$case_id == case_id & occupied,
    ,
    drop = FALSE
  ]
  repeated_genes <- names(which(table(case_candidates$current_symbol) > 1L))
  for (gene in sort(repeated_genes)) {
    gene_rows <- case_candidates[
      case_candidates$current_symbol == gene,
      ,
      drop = FALSE
    ]
    anchor_index <- which.max(gene_rows$negative_log10_acat_q)
    target_indices <- setdiff(seq_len(nrow(gene_rows)), anchor_index)
    for (target_index in target_indices) {
      link_rows[[link_index]] <- data.frame(
        schema_version = "phase18_three_case_circular_links_v1",
        case_id = case_id,
        current_symbol = gene,
        selected_network_count_within_case = nrow(gene_rows),
        anchor_broad_network = gene_rows$broad_network[[anchor_index]],
        target_broad_network = gene_rows$broad_network[[target_index]],
        anchor_sector_mid_degrees = gene_rows$sector_mid_degrees[[anchor_index]],
        target_sector_mid_degrees = gene_rows$sector_mid_degrees[[target_index]],
        anchor_negative_log10_acat_q =
          gene_rows$negative_log10_acat_q[[anchor_index]],
        target_negative_log10_acat_q =
          gene_rows$negative_log10_acat_q[[target_index]],
        link_rule = "highest_uncapped_evidence_to_each_other_occurrence",
        stringsAsFactors = FALSE
      )
      link_index <- link_index + 1L
    }
  }
}
links <- if (length(link_rows)) {
  do.call(rbind, link_rows)
} else {
  data.frame(
    schema_version = character(), case_id = character(),
    current_symbol = character(), selected_network_count_within_case = integer(),
    anchor_broad_network = character(), target_broad_network = character(),
    anchor_sector_mid_degrees = numeric(), target_sector_mid_degrees = numeric(),
    anchor_negative_log10_acat_q = numeric(),
    target_negative_log10_acat_q = numeric(), link_rule = character(),
    stringsAsFactors = FALSE
  )
}
rownames(links) <- NULL

for (case_id in case_order) {
  counts <- table(
    plot_data$current_symbol[
      plot_data$case_id == case_id & occupied
    ]
  )
  expected_links <- sum(pmax(as.integer(counts) - 1L, 0L))
  observed_links <- sum(links$case_id == case_id)
  assert_true(
    observed_links == expected_links,
    paste("Link count does not follow m - 1 for", case_id)
  )
}

if (dir.exists(output_dir) || file.exists(output_dir)) {
  stop(
    "Output path already exists; refusing to overwrite: ", output_dir,
    call. = FALSE
  )
}
output_parent <- dirname(output_dir)
dir.create(output_parent, recursive = TRUE, showWarnings = FALSE)
staging_dir <- file.path(
  output_parent,
  paste0(".", basename(output_dir), ".staging.", Sys.getpid())
)
assert_true(
  !dir.exists(staging_dir) && !file.exists(staging_dir),
  paste("Staging path already exists:", staging_dir)
)
dir.create(staging_dir, recursive = FALSE, showWarnings = FALSE)
published <- FALSE
on.exit({
  if (!published && dir.exists(staging_dir)) {
    unlink(staging_dir, recursive = TRUE, force = TRUE)
  }
}, add = TRUE)

atomic_write_lines <- function(lines, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- file.path(
    dirname(path),
    paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  on.exit(if (file.exists(temporary)) unlink(temporary), add = TRUE)
  writeLines(lines, temporary, useBytes = TRUE)
  if (!file.rename(temporary, path)) {
    stop("Could not publish text artifact: ", path, call. = FALSE)
  }
  invisible(path)
}

plot_data_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_plot_data.tsv"
)
links_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_links.tsv"
)
atomic_write_table(plot_data, plot_data_path)
atomic_write_table(links, links_path)

annular_sector <- function(start_degrees, end_degrees, inner_radius, outer_radius,
                           fill, border = NA, line_width = 0.5) {
  theta <- seq(start_degrees, end_degrees, length.out = 80) * pi / 180
  x <- c(outer_radius * cos(theta), inner_radius * cos(rev(theta)))
  y <- c(outer_radius * sin(theta), inner_radius * sin(rev(theta)))
  graphics::polygon(x, y, col = fill, border = border, lwd = line_width)
}

circle_line <- function(radius, color, line_width = 0.5, line_type = 1) {
  theta <- seq(0, 2 * pi, length.out = 720)
  graphics::lines(
    radius * cos(theta), radius * sin(theta),
    col = color, lwd = line_width, lty = line_type
  )
}

bezier_link <- function(angle1, angle2, radius = 0.61, color = "#66666633") {
  start <- radius * c(cos(angle1 * pi / 180), sin(angle1 * pi / 180))
  end <- radius * c(cos(angle2 * pi / 180), sin(angle2 * pi / 180))
  control <- c(0, 0)
  t <- seq(0, 1, length.out = 160)
  points <- outer((1 - t)^2, start) +
    outer(2 * (1 - t) * t, control) +
    outer(t^2, end)
  graphics::lines(points[, 1L], points[, 2L], col = color, lwd = 0.65)
}

upright_rotation <- function(angle) {
  rotation <- (angle - 90) %% 360
  if (rotation > 90 && rotation < 270) rotation <- rotation + 180
  if (rotation > 180) rotation <- rotation - 360
  rotation
}

draw_case_legend <- function(case_id) {
  graphics::par(
    fig = c(circle_panel_fraction, 1, 0, 1),
    mar = c(0, 0, 0, 0),
    xaxs = "i", yaxs = "i", family = "sans", xpd = NA,
    new = TRUE
  )
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1))

  key_x <- 0.005
  key_width <- 0.052
  text_x <- 0.075
  graphics::text(
    key_x, 0.63, "Legend",
    adj = c(0, 0.5), cex = 0.82 * legend_text_multiplier,
    font = 2, col = "#222222"
  )
  graphics::rect(
    key_x, 0.521, key_x + key_width, 0.559,
    col = phase12_network_colors[[1L]], border = NA
  )
  graphics::text(
    text_x, 0.54, "broad network",
    adj = c(0, 0.5), cex = 0.56 * legend_text_multiplier,
    col = "#333333"
  )
  graphics::rect(
    key_x, 0.451, key_x + key_width, 0.489,
    col = "#344E73", border = NA
  )
  graphics::text(
    text_x, 0.47, "capped -log10(ACAT q)",
    adj = c(0, 0.5), cex = 0.52 * legend_text_multiplier,
    col = "#333333"
  )
  graphics::segments(
    key_x, 0.40, key_x + key_width, 0.40,
    col = rgba("#666666", 0.55), lwd = 1
  )
  graphics::text(
    text_x, 0.40, "same gene across networks",
    adj = c(0, 0.5), cex = 0.50 * legend_text_multiplier,
    col = "#333333"
  )
  if (case_id %in% case_order[1:2]) {
    graphics::points(
      key_x + key_width / 2, 0.33,
      pch = 16, col = "#777777", cex = 0.55
    )
    marker_text <- "mtDNA-encoded candidate"
  } else {
    graphics::points(
      key_x + key_width / 2, 0.33,
      pch = 5, col = "#555555", cex = 0.72, lwd = 0.8
    )
    marker_text <- "mito_extended; outside core"
  }
  graphics::text(
    text_x, 0.33, marker_text,
    adj = c(0, 0.5), cex = 0.49 * legend_text_multiplier,
    col = "#333333"
  )
  graphics::text(
    key_x, 0.25,
    paste0("Common scale 0–", format(evidence_cap, trim = TRUE)),
    adj = c(0, 0.5), cex = 0.54 * legend_text_multiplier,
    col = "#555555"
  )
  graphics::text(
    key_x, 0.195,
    paste0("Outer cap: q ≤ 10^-", format(evidence_cap, trim = TRUE)),
    adj = c(0, 0.5), cex = 0.48 * legend_text_multiplier,
    col = "#666666"
  )
}

draw_case_circle <- function(case_id) {
  case_slots <- plot_data[plot_data$case_id == case_id, , drop = FALSE]
  case_slots <- case_slots[
    order(case_slots$network_display_order, case_slots$slot_rank),
    ,
    drop = FALSE
  ]
  case_links <- links[links$case_id == case_id, , drop = FALSE]
  case_occupied <- case_slots$slot_status == "ranked_candidate"

  graphics::par(
    fig = c(0, circle_panel_fraction, 0, 1),
    mar = c(2.4, 0.8, 5.4, 0.8),
    xaxs = "i", yaxs = "i", family = "sans", xpd = NA
  )
  graphics::plot.new()
  graphics::plot.window(xlim = c(-1.65, 1.65), ylim = c(-1.65, 1.65), asp = 1)

  score_inner <- 0.62
  score_height <- 0.32
  for (index in seq_len(nrow(case_slots))) {
    annular_sector(
      case_slots$sector_start_degrees[[index]],
      case_slots$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height,
      fill = if (
        case_slots$slot_status[[index]] == "no_passing_candidate_slot"
      ) {
        "#E4E7EA"
      } else {
        "#F1F3F5"
      },
      border = "white",
      line_width = 0.55
    )
  }
  for (reference_value in c(5, 10, evidence_cap)) {
    reference_fraction <- min(reference_value / evidence_cap, 1)
    circle_line(
      score_inner + score_height * reference_fraction,
      color = if (reference_fraction == 1) "#AEB6BF" else "#CBD0D5",
      line_width = if (reference_fraction == 1) 0.65 else 0.4,
      line_type = if (reference_fraction == 1) 1 else 3
    )
  }

  if (nrow(case_links)) {
    for (index in seq_len(nrow(case_links))) {
      bezier_link(
        case_links$anchor_sector_mid_degrees[[index]],
        case_links$target_sector_mid_degrees[[index]],
        color = rgba("#666666", 0.20)
      )
    }
  }

  for (index in which(case_occupied)) {
    annular_sector(
      case_slots$sector_start_degrees[[index]],
      case_slots$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height * case_slots$display_score[[index]],
      fill = "#344E73",
      border = "white",
      line_width = 0.55
    )
  }

  for (index in seq_len(nrow(case_slots))) {
    network_border <- if (
      case_slots$broad_network[[index]] == "Oligodendrocytes"
    ) {
      "#9E8B00"
    } else {
      "white"
    }
    annular_sector(
      case_slots$sector_start_degrees[[index]],
      case_slots$sector_end_degrees[[index]],
      0.98,
      1.07,
      fill = case_slots$network_color[[index]],
      border = network_border,
      line_width = if (network_border == "white") 0.75 else 0.55
    )
  }

  for (index in which(case_occupied)) {
    angle <- case_slots$sector_mid_degrees[[index]]
    label_radius <- c(1.12, 1.23, 1.34, 1.23, 1.12)[
      case_slots$slot_rank[[index]]
    ]
    label_color <- if (isTRUE(case_slots$is_mtdna_gene[[index]])) {
      "#777777"
    } else {
      "#202020"
    }
    graphics::text(
      label_radius * cos(angle * pi / 180),
      label_radius * sin(angle * pi / 180),
      labels = case_slots$current_symbol[[index]],
      srt = upright_rotation(angle),
      cex = 0.70,
      col = label_color,
      font = 1
    )
    if (
      case_id %in% case_order[1:2] &&
      isTRUE(case_slots$is_mtdna_gene[[index]])
    ) {
      marker_radius <- 1.095
      graphics::points(
        marker_radius * cos(angle * pi / 180),
        marker_radius * sin(angle * pi / 180),
        pch = 16, col = "#777777", cex = 0.42
      )
    }
    if (
      case_id == "case3_not_core_mito" &&
      isTRUE(case_slots$extended_reference_member[[index]])
    ) {
      marker_radius <- 1.095
      graphics::points(
        marker_radius * cos(angle * pi / 180),
        marker_radius * sin(angle * pi / 180),
        pch = 5, col = "#555555", cex = 0.60, lwd = 0.8
      )
    }
  }

  for (network in phase18_network_order) {
    indices <- which(case_slots$broad_network == network)
    block_mid <- mean(c(
      case_slots$sector_start_degrees[[min(indices)]],
      case_slots$sector_end_degrees[[max(indices)]]
    ))
    network_radius <- 1.50
    graphics::text(
      network_radius * cos(block_mid * pi / 180),
      network_radius * sin(block_mid * pi / 180),
      labels = phase12_network_labels[[network]],
      srt = upright_rotation(block_mid),
      cex = 0.90,
      col = "#222222",
      font = 2
    )
    if (all(
      case_slots$slot_status[indices] == "no_passing_candidate_slot"
    )) {
      empty_radius <- 1.21
      graphics::text(
        empty_radius * cos(block_mid * pi / 180),
        empty_radius * sin(block_mid * pi / 180),
        labels = "No passing\ncandidate",
        srt = upright_rotation(block_mid),
        cex = 0.47,
        col = "#666666",
        font = 3
      )
    }
  }

  graphics::title(
    main = "Phase 18 key-driver candidates across broad cell networks",
    cex.main = 1.08,
    font.main = 2,
    col.main = "#202020",
    line = 3.4
  )
  graphics::mtext(
    case_titles[[case_id]],
    side = 3, line = 2.15, cex = 0.74, font = 2, col = "#333333"
  )
  graphics::mtext(
    "Up to five passing candidates per network, ranked by aggregate ACAT q value",
    side = 3, line = 1.35, cex = 0.58, col = "#555555"
  )
  if (case_id == "case1_core_mito_in_query") {
    graphics::mtext(
      "Self-overlap was removed before run-level evidence was combined",
      side = 3, line = 0.65, cex = 0.52, col = "#606060"
    )
  }
  graphics::mtext(
    "Primary AD-up and AD-down runs only; CAMs and T cells had no included Phase 18 runs",
    side = 1,
    line = 0.7,
    cex = 0.54,
    col = "#606060"
  )
  draw_case_legend(case_id)
}

figure_paths <- list()
for (case_id in case_order) {
  basename_value <- case_basenames[[case_id]]
  svg_path <- file.path(staging_dir, paste0(basename_value, ".svg"))
  pdf_path <- file.path(staging_dir, paste0(basename_value, ".pdf"))
  png_path <- file.path(staging_dir, paste0(basename_value, ".png"))

  message("Writing ", svg_path)
  render_atomic(
    svg_path,
    function(path) {
      open_svg_device(path, figure_width_inches, figure_height_inches)
    },
    function() draw_case_circle(case_id)
  )
  message("Writing ", pdf_path)
  render_atomic(
    pdf_path,
    function(path) {
      open_pdf_device(path, figure_width_inches, figure_height_inches)
    },
    function() draw_case_circle(case_id)
  )
  message("Writing ", png_path)
  render_atomic(
    png_path,
    function(path) {
      open_png_device(
        path, figure_width_inches, figure_height_inches, dpi = png_dpi
      )
    },
    function() draw_case_circle(case_id)
  )
  figure_paths[[case_id]] <- c(svg = svg_path, pdf = pdf_path, png = png_path)
}

caption_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_caption.md"
)
caption_lines <- c(
  "# Phase 18 three-case circular figures: caption",
  "",
  paste0(
    "**Case-specific Phase 18 key-driver candidates across broad brain-cell ",
    "networks.** Each circular graph shows one prespecified relationship ",
    "between a candidate driver and the run-specific mitochondrial query: ",
    "Case 1 contains core MitoCarta genes in the query, Case 2 contains core ",
    "MitoCarta genes not in the query, and Case 3 contains genes outside the ",
    "1,136-gene core MitoCarta inventory. Within each broad network, up to ",
    "five genes that passed the 80% coverage, conservative-support, and ",
    "aggregate ACAT q ≤ 0.05 gates are shown in frozen q-value rank order; ",
    "unfilled positions were not backfilled. For Case 1, the driver's ",
    "guaranteed self-overlap was removed before enrichment statistics were ",
    "recomputed. Navy bar height is the common-scale negative log10 aggregate ",
    "ACAT q value capped at ", format(evidence_cap, trim = TRUE),
    ", and outer colors identify broad networks. Gray center links connect ",
    "repeated displayed genes across networks within the same case and are ",
    "not network edges. Explicit empty blocks mean that no gene passed all ",
    "candidate gates for that network and case. Gray dots in Cases 1 and 2 ",
    "mark mtDNA-encoded candidates. Outlined diamonds in Case 3 mark ",
    "mito_extended annotations that remain outside the core MitoCarta case ",
    "definition. CAMs and T cells are absent because they had no included ",
    "Phase 18 runs, not because a negative driver result was observed. These ",
    "are statistically supported network associations and do not establish ",
    "causal regulation."
  )
)
atomic_write_lines(caption_lines, caption_path)

methods_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_methods.md"
)
methods_lines <- c(
  "# Phase 18 three-case circular figures: methods",
  "",
  "## Inputs and selection",
  "",
  paste0(
    "The renderer required the validated Phase 18 production bundle at `",
    "results/minerva_production/18_key_driver_selection/`. Display membership ",
    "and rank were read from `key_driver_top5.tsv`; the renderer did not ",
    "recalculate ACAT, multiple-testing correction, candidate status, or rank."
  ),
  "",
  paste0(
    "Within each broad network and case, the frozen Phase 18 rank is ascending ",
    "aggregate ACAT q value, ascending aggregate ACAT P value for q-value ties, ",
    "and current gene symbol as the deterministic final tie-breaker. Up to five ",
    "passing candidates were displayed without backfilling."
  ),
  "",
  "## Geometry and encoding",
  "",
  paste0(
    "All three circles used the same seven-network order and 35-slot geometry ",
    "(five display slots per network). Candidate bar height was `min(-log10(q), ",
    format(evidence_cap, trim = TRUE), ") / ",
    format(evidence_cap, trim = TRUE), "`, with one common scale across cases. ",
    "Network identity was encoded by the colorblind-aware outer band and by ",
    "text labels. Repeated displayed symbols within one case were connected ",
    "from their strongest uncapped evidence sector to each other occurrence. ",
    "The legend occupied a dedicated panel to the right of the circular plot; ",
    "the plot center contained neither legend content nor an opaque mask, ",
    "leaving cross-network link curves visible end to end. All legend text ",
    "was rendered at twice its original size and arranged in a compact key. ",
    "Broad-network labels were enlarged and positioned close to the outer band."
  ),
  "",
  "## Export",
  "",
  paste0(
    "Figures were rendered with base R and Cairo on a ",
    format(figure_width_inches, trim = TRUE), " × ",
    format(figure_height_inches, trim = TRUE),
    " inch canvas. SVG and PDF are the authoritative vector files; PNG review ",
    "copies were exported at ", png_dpi, " dpi."
  ),
  "",
  "## Reproduction command",
  "",
  "```bash",
  paste(
    "Rscript --vanilla",
    "scripts/figures/analysis/phase_18_key_driver_selection/",
    "visualize_phase18_three_case_circular.R",
    "--input-dir results/minerva_production/18_key_driver_selection",
    paste0(
      "--output-dir results/figures/analysis/phase_18_key_driver_selection/",
      "three_case_circular"
    ),
    "--top-per-network 5",
    paste("--evidence-cap", format(evidence_cap, trim = TRUE)),
    paste("--png-dpi", png_dpi),
    sep = paste0(" ", intToUtf8(92), "\n  ")
  ),
  "```"
)
atomic_write_lines(methods_lines, methods_path)

uint32_from_raw <- function(x) {
  sum(as.numeric(x) * 256^(3:0))
}

read_png_metadata <- function(path) {
  connection <- file(path, "rb")
  on.exit(close(connection), add = TRUE)
  bytes <- readBin(connection, what = "raw", n = file.info(path)$size)
  signature <- as.raw(c(137, 80, 78, 71, 13, 10, 26, 10))
  assert_true(
    length(bytes) >= 24L && identical(bytes[1:8], signature),
    paste("Invalid PNG signature:", path)
  )
  width <- uint32_from_raw(bytes[17:20])
  height <- uint32_from_raw(bytes[21:24])
  pattern <- charToRaw("pHYs")
  match_index <- NA_integer_
  for (index in seq_len(length(bytes) - length(pattern) + 1L)) {
    if (identical(bytes[index:(index + length(pattern) - 1L)], pattern)) {
      match_index <- index
      break
    }
  }
  dpi_x <- NA_real_
  dpi_y <- NA_real_
  if (!is.na(match_index) && match_index + 12L <= length(bytes)) {
    x_pixels_per_meter <- uint32_from_raw(bytes[(match_index + 4L):(match_index + 7L)])
    y_pixels_per_meter <- uint32_from_raw(bytes[(match_index + 8L):(match_index + 11L)])
    unit_specifier <- as.integer(bytes[[match_index + 12L]])
    if (unit_specifier == 1L) {
      dpi_x <- x_pixels_per_meter * 0.0254
      dpi_y <- y_pixels_per_meter * 0.0254
    }
  }
  list(width = width, height = height, dpi_x = dpi_x, dpi_y = dpi_y)
}

expected_png_width <- round(figure_width_inches * png_dpi)
expected_png_height <- round(figure_height_inches * png_dpi)
png_metadata <- lapply(
  figure_paths,
  function(paths) read_png_metadata(paths[["png"]])
)
png_dimensions_pass <- all(vapply(
  png_metadata,
  function(metadata) {
    metadata$width == expected_png_width &&
      metadata$height == expected_png_height
  },
  logical(1L)
))
png_dpi_pass <- all(vapply(
  png_metadata,
  function(metadata) {
    is.finite(metadata$dpi_x) && is.finite(metadata$dpi_y) &&
      abs(metadata$dpi_x - png_dpi) <= 0.2 &&
      abs(metadata$dpi_y - png_dpi) <= 0.2
  },
  logical(1L)
))

svg_paths <- vapply(figure_paths, `[[`, character(1L), "svg")
pdf_paths <- vapply(figure_paths, `[[`, character(1L), "pdf")
png_paths <- vapply(figure_paths, `[[`, character(1L), "png")
all_figure_paths <- c(svg_paths, pdf_paths, png_paths)
files_nonempty <- all(file.exists(all_figure_paths)) &&
  all(file.info(all_figure_paths)$size > 0)
svg_vector_pass <- all(vapply(
  svg_paths,
  function(path) {
    lines <- readLines(path, warn = FALSE)
    any(grepl("<(path|polygon|use|text)", lines)) &&
      !any(grepl("data:image/(png|jpeg)", lines, ignore.case = TRUE))
  },
  logical(1L)
))
pdf_header_pass <- all(vapply(
  pdf_paths,
  function(path) {
    connection <- file(path, "rb")
    on.exit(close(connection), add = TRUE)
    identical(rawToChar(readBin(connection, "raw", n = 5L)), "%PDF-")
  },
  logical(1L)
))

input_source_rows <- lapply(seq_len(nrow(source_hashes)), function(index) {
  path <- source_paths[[source_hashes$file[[index]]]]
  data.frame(
    schema_version = "phase18_three_case_circular_sources_v1",
    artifact_role = "input",
    path = file.path(
      "results", "minerva_production", "18_key_driver_selection",
      source_hashes$file[[index]]
    ),
    rows = switch(
      source_hashes$file[[index]],
      "key_driver_status.tsv" = nrow(status),
      "key_driver_checks.tsv" = nrow(phase18_checks),
      "key_driver_artifacts.tsv" = nrow(artifacts),
      "key_driver_analysis_manifest.tsv" = nrow(analysis_manifest),
      "key_driver_case_manifest.tsv" = nrow(case_manifest),
      "key_driver_top5.tsv" = nrow(top5),
      "key_driver_figure_data.tsv" = nrow(figure_data),
      "key_driver_candidates.tsv" = nrow(candidates)
    ),
    bytes = file.info(path)$size,
    declared_sha256 = source_hashes$declared_sha256[[index]],
    observed_sha256 = source_hashes$observed_sha256[[index]],
    hash_match = source_hashes$hash_match[[index]],
    stringsAsFactors = FALSE
  )
})

hash_output_paths <- c(
  all_figure_paths,
  plot_data_path,
  links_path,
  caption_path,
  methods_path
)
output_source_rows <- lapply(hash_output_paths, function(path) {
  final_relative_path <- file.path(
    "results", "figures", "analysis", "phase_18_key_driver_selection",
    "three_case_circular", basename(path)
  )
  data.frame(
    schema_version = "phase18_three_case_circular_sources_v1",
    artifact_role = "output",
    path = final_relative_path,
    rows = if (path == plot_data_path) {
      nrow(plot_data)
    } else if (path == links_path) {
      nrow(links)
    } else {
      NA_integer_
    },
    bytes = file.info(path)$size,
    declared_sha256 = NA_character_,
    observed_sha256 = sha256_file(path),
    hash_match = NA,
    stringsAsFactors = FALSE
  )
})
sources_table <- do.call(rbind, c(input_source_rows, output_source_rows))
rownames(sources_table) <- NULL
sources_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_sources.tsv"
)
atomic_write_table(sources_table, sources_path)

check_rows <- list()
add_check <- function(check_id, observed, expected, passed, severity = "error") {
  check_rows[[length(check_rows) + 1L]] <<- data.frame(
    schema_version = "phase18_three_case_circular_checks_v1",
    check_id = check_id,
    severity = severity,
    observed = as.character(observed),
    expected = as.character(expected),
    passed = isTRUE(passed),
    stringsAsFactors = FALSE
  )
}
add_check(
  "phase18_validation_status", status$validation_status[[1L]],
  "validated_complete", status$validation_status[[1L]] == "validated_complete"
)
add_check(
  "phase18_source_checks", sum(phase18_checks$passed), nrow(phase18_checks),
  all(phase18_checks$passed)
)
add_check(
  "phase18_source_hashes",
  sum(source_hashes$hash_match %in% TRUE),
  sum(!is.na(source_hashes$hash_match)),
  all(source_hashes$hash_match[!is.na(source_hashes$hash_match)])
)
add_check("case_count", length(case_order), 3L, length(case_order) == 3L)
add_check(
  "plot_rows_per_case",
  paste(as.integer(table(plot_data$case_id)), collapse = "|"),
  "35|35|35",
  all(table(plot_data$case_id) == 35L)
)
add_check(
  "occupied_slots_by_case",
  paste(as.integer(table(plot_data$case_id[occupied])), collapse = "|"),
  "27|15|21",
  identical(
    as.integer(table(factor(plot_data$case_id[occupied], levels = case_order))),
    c(27L, 15L, 21L)
  )
)
add_check(
  "occupied_top5_reconciliation", sum(occupied), nrow(ranked_top5),
  sum(occupied) == nrow(ranked_top5)
)
add_check(
  "occupied_annotation_join", nrow(displayed_candidates), sum(occupied),
  nrow(displayed_candidates) == sum(occupied)
)
add_check(
  "maximum_display_rank", max(plot_data$display_rank, na.rm = TRUE), 5L,
  max(plot_data$display_rank, na.rm = TRUE) <= 5L
)
add_check(
  "explicit_empty_network_cases",
  length(observed_empty_keys), length(expected_empty_keys),
  setequal(observed_empty_keys, expected_empty_keys)
)
add_check(
  "excluded_no_run_networks", "CAMs|T_cells", "CAMs|T_cells",
  !any(plot_data$broad_network %in% c("CAMs", "T_cells"))
)
add_check(
  "case1_core_mito_membership",
  sum(plot_data$is_core_mito[
    occupied & plot_data$case_id == case_order[[1L]]
  ] %in% TRUE),
  expected_case_counts[[case_order[[1L]]]],
  all(plot_data$is_core_mito[
    occupied & plot_data$case_id == case_order[[1L]]
  ] %in% TRUE)
)
add_check(
  "case3_noncore_mito_membership",
  sum(!plot_data$is_core_mito[
    occupied & plot_data$case_id == case_order[[3L]]
  ]),
  expected_case_counts[[case_order[[3L]]]],
  all(!plot_data$is_core_mito[
    occupied & plot_data$case_id == case_order[[3L]]
  ])
)
add_check(
  "display_score_range",
  paste0(
    format(min(plot_data$display_score[occupied]), digits = 6), "..",
    format(max(plot_data$display_score[occupied]), digits = 6)
  ),
  "(0,1]",
  all(plot_data$display_score[occupied] > 0 &
    plot_data$display_score[occupied] <= 1)
)
expected_total_links <- sum(
  unlist(lapply(case_order, function(case_id) {
    counts <- table(
      plot_data$current_symbol[plot_data$case_id == case_id & occupied]
    )
    sum(pmax(as.integer(counts) - 1L, 0L))
  }))
)
add_check(
  "m_minus_one_link_rule", nrow(links), expected_total_links,
  nrow(links) == expected_total_links
)
add_check(
  "empty_slots_have_no_candidate_values",
  sum(!occupied & is.na(plot_data$current_symbol) &
    is.na(plot_data$aggregate_acat_q) & is.na(plot_data$display_score)),
  sum(!occupied),
  all(is.na(plot_data$current_symbol[!occupied])) &&
    all(is.na(plot_data$aggregate_acat_q[!occupied])) &&
    all(is.na(plot_data$display_score[!occupied]))
)
add_check(
  "figure_files_nonempty", sum(file.info(all_figure_paths)$size > 0),
  length(all_figure_paths), files_nonempty
)
add_check(
  "svg_vector_content", sum(vapply(
    svg_paths,
    function(path) {
      lines <- readLines(path, warn = FALSE)
      any(grepl("<(path|polygon|use|text)", lines)) &&
        !any(grepl("data:image/(png|jpeg)", lines, ignore.case = TRUE))
    },
    logical(1L)
  )),
  length(svg_paths), svg_vector_pass
)
add_check(
  "pdf_headers", sum(vapply(
    pdf_paths,
    function(path) {
      connection <- file(path, "rb")
      on.exit(close(connection), add = TRUE)
      identical(rawToChar(readBin(connection, "raw", n = 5L)), "%PDF-")
    },
    logical(1L)
  )),
  length(pdf_paths), pdf_header_pass
)
add_check(
  "png_dimensions",
  paste0(expected_png_width, "x", expected_png_height, " each"),
  paste0(expected_png_width, "x", expected_png_height, " each"),
  png_dimensions_pass
)
add_check(
  "png_dpi_metadata", png_dpi, png_dpi, png_dpi_pass
)
add_check(
  "source_and_output_hashes_recorded",
  sum(!is.na(sources_table$observed_sha256)), nrow(sources_table),
  all(!is.na(sources_table$observed_sha256))
)

checks_table <- do.call(rbind, check_rows)
rownames(checks_table) <- NULL
assert_true(all(checks_table$passed), "At least one figure-package check failed")
checks_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_checks.tsv"
)
atomic_write_table(checks_table, checks_path)

generation_log_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_generation_log.tsv"
)
generation_log <- data.frame(
  schema_version = "phase18_three_case_circular_generation_log_v1",
  generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  figure_script = paste0(
    "scripts/figures/analysis/phase_18_key_driver_selection/",
    "visualize_phase18_three_case_circular.R"
  ),
  input_directory = "results/minerva_production/18_key_driver_selection",
  output_directory = paste0(
    "results/figures/analysis/phase_18_key_driver_selection/",
    "three_case_circular"
  ),
  cases = length(case_order),
  included_broad_networks = length(phase18_network_order),
  slots_per_case = nrow(geometry),
  case1_displayed_candidates = expected_case_counts[[case_order[[1L]]]],
  case2_displayed_candidates = expected_case_counts[[case_order[[2L]]]],
  case3_displayed_candidates = expected_case_counts[[case_order[[3L]]]],
  cross_network_links = nrow(links),
  evidence_measure = "negative_log10_aggregate_acat_q",
  evidence_cap = evidence_cap,
  width_inches = figure_width_inches,
  height_inches = figure_height_inches,
  png_dpi = png_dpi,
  automated_checks = nrow(checks_table),
  automated_checks_passed = sum(checks_table$passed),
  stringsAsFactors = FALSE
)
atomic_write_table(generation_log, generation_log_path)

status_path <- file.path(
  staging_dir,
  "phase18_three_case_circular_status.tsv"
)
figure_status <- data.frame(
  schema_version = "phase18_three_case_circular_status_v1",
  validation_status = "validated_complete",
  case_figures = length(case_order),
  included_broad_networks = length(phase18_network_order),
  plotted_slot_rows = nrow(plot_data),
  displayed_candidate_rows = sum(occupied),
  cross_network_links = nrow(links),
  failed_checks = sum(!checks_table$passed),
  timestamp_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  stringsAsFactors = FALSE
)
atomic_write_table(figure_status, status_path)

assert_true(
  file.rename(staging_dir, output_dir),
  paste("Could not atomically publish output directory:", output_dir)
)
published <- TRUE

message(
  "Phase 18 three-case circular package complete: ",
  sum(occupied), " displayed candidate sectors; ", nrow(links),
  " cross-network links; ", nrow(checks_table), " checks passed"
)
