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
    "visualize_phase12_kda_sex_apoe.R ",
    "[--input-dir DIR] [--output-dir DIR] [--basename NAME] ",
    "[--maximum-rows N] [--maximum-per-network N] ",
    "[--minimum-ranking-coverage FRACTION]\n",
    sep = ""
  )
}

args <- parse_value_args(
  commandArgs(trailingOnly = TRUE),
  defaults = list(
    input_dir = "results/figures/analysis/phase12_kda",
    output_dir = "results/figures/analysis/phase12_kda/sex_apoe_figure",
    basename = "phase12_kda_sex_apoe",
    maximum_rows = "20",
    maximum_per_network = "3",
    minimum_ranking_coverage = "0.50"
  ),
  allowed = c(
    "--input-dir", "--output-dir", "--basename", "--maximum-rows",
    "--maximum-per-network", "--minimum-ranking-coverage"
  )
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
maximum_rows <- suppressWarnings(as.integer(args$maximum_rows))
maximum_per_network <- suppressWarnings(as.integer(args$maximum_per_network))
minimum_ranking_coverage <- suppressWarnings(as.numeric(args$minimum_ranking_coverage))
assert_true(
  length(maximum_rows) == 1L && is.finite(maximum_rows) && maximum_rows >= 6L,
  "--maximum-rows must be an integer of at least 6"
)
assert_true(
  length(maximum_per_network) == 1L && is.finite(maximum_per_network) &&
    maximum_per_network >= 1L && maximum_per_network <= 6L,
  "--maximum-per-network must be an integer from 1 to 6"
)
assert_true(
  length(minimum_ranking_coverage) == 1L && is.finite(minimum_ranking_coverage) &&
    minimum_ranking_coverage > 0 && minimum_ranking_coverage <= 1,
  "--minimum-ranking-coverage must be in (0, 1]"
)
assert_true(
  grepl("^[A-Za-z0-9._-]+$", args$basename),
  "--basename contains unsupported characters"
)
if (!capabilities("cairo")) stop("This R installation lacks Cairo graphics support", call. = FALSE)

conservative_path <- file.path(input_dir, "phase12_kda_conservative_candidate_summary.tsv")
candidate_path <- file.path(input_dir, "phase12_kda_primary_directional_candidate_tests.tsv.gz")
checks_path <- file.path(input_dir, "phase12_kda_figure_data_checks.tsv")
conservative <- read_tsv(conservative_path)
checks <- read_tsv(checks_path)
assert_true(nrow(checks) > 0L && all(checks$passed), "Prepared figure-data checks did not all pass")

require_columns(
  conservative,
  c(
    "broad_network", "key_driver", "conservative_significant_runs",
    "conservative_fine_cell_types", "highlighted_candidate_pool"
  ),
  basename(conservative_path)
)

# NetWeaver-compatible ACAT behavior, including its treatment of NA, 0, and 1.
# Reference: https://github.com/mw201608/NetWeaver/blob/master/R/ACAT.R
acat_combine_netweaver <- function(p_values, na_action = c("na.omit", "na.to1"),
                                   tolerance = 1e-300) {
  na_action <- match.arg(na_action)
  x <- as.numeric(p_values)
  assert_true(!any(x < 0 | x > 1, na.rm = TRUE), "ACAT input p-values must be in [0, 1]")
  if (anyNA(x)) {
    if (na_action == "na.omit") {
      x <- x[!is.na(x)]
    } else {
      x[is.na(x)] <- 1
    }
  }
  if (!length(x)) return(NA_real_)
  if (all(x == 1)) return(1)
  if (any(x == 0)) {
    positive <- x[x > 0]
    replacement <- if (length(positive)) min(positive) else tolerance
    if (replacement > tolerance) replacement <- tolerance
    x[x == 0] <- replacement
  }
  if (any(x == 1)) {
    x[x == 1] <- max(x[x < 1]) / 2 + 0.5
  }
  small <- x < 1e-15
  statistics <- numeric(length(x))
  statistics[small] <- 1 / (x[small] * pi)
  statistics[!small] <- tan((0.5 - x[!small]) * pi)
  stats::pcauchy(mean(statistics), lower.tail = FALSE)
}

p_matrix_acat_netweaver <- function(p_matrix, na_action = c("na.omit", "na.to1")) {
  na_action <- match.arg(na_action)
  apply(as.matrix(p_matrix), 1L, acat_combine_netweaver, na_action = na_action)
}

validate_acat_example <- function() {
  example <- matrix(
    c(
      0.5746569, 0.7090122, 0.7965851, 0.1149619,
      0.6513363, 0.6671072, 0.5985140, 0.4991580,
      0.1632148, 0.9312446, 0.9105127, 0.2293418,
      0.8836971, 0.8424568, 0.2578088, 0.3955429,
      0.6770827, 0.7551785, 0.3221481, 0.5570227
    ),
    nrow = 5L,
    byrow = TRUE
  )
  expected <- c(
    0.4768092003, 0.6079561876, 0.7884404860, 0.7135191247, 0.5935618969
  )
  observed <- p_matrix_acat_netweaver(example, na_action = "na.to1")
  error <- max(abs(observed - expected))
  assert_true(error <= 5e-10, "Local ACAT implementation failed the professor example")
  error
}

prepare_overall_acat_summary <- function(candidate_tests) {
  parts <- lapply(phase12_network_order, function(network) {
    x <- candidate_tests[candidate_tests$broad_network == network, , drop = FALSE]
    assert_true(nrow(x) > 0L, paste("No ACAT candidate tests for", network))
    run_ids <- unique(x$kda_run_id)
    genes <- sort(unique(x$key_driver))
    p_matrix <- matrix(
      NA_real_, nrow = length(genes), ncol = length(run_ids),
      dimnames = list(genes, run_ids)
    )
    indices <- cbind(match(x$key_driver, genes), match(x$kda_run_id, run_ids))
    p_matrix[indices] <- x$raw_p_value
    combined_p <- p_matrix_acat_netweaver(p_matrix, na_action = "na.to1")
    tested_runs <- rowSums(!is.na(p_matrix))
    data.frame(
      broad_network = network,
      key_driver = genes,
      overall_acat_combined_p = as.numeric(combined_p),
      overall_acat_negative_log10_p = -log10(
        pmax(combined_p, .Machine$double.xmin)
      ),
      ranking_runs = as.integer(tested_runs),
      eligible_directional_runs = length(run_ids),
      ranking_coverage_fraction = tested_runs / length(run_ids),
      stringsAsFactors = FALSE
    )
  })
  result <- do.call(rbind, parts)
  rownames(result) <- NULL
  assert_true(
    all(is.finite(result$overall_acat_combined_p)) &
      all(result$overall_acat_combined_p >= 0 & result$overall_acat_combined_p <= 1),
    "ACAT produced an invalid overall combined p-value"
  )
  result
}

acat_example_max_abs_error <- validate_acat_example()
message("Reading complete primary-directional KDA candidate tests for ACAT ranking")
candidate_tests <- read_tsv(candidate_path)
require_columns(
  candidate_tests,
  c(
    "kda_run_id", "analysis_tier", "broad_network", "signature_group",
    "signature_direction", "key_driver", "raw_p_value", "adjusted_p_value",
    "ranking_candidate"
  ),
  basename(candidate_path)
)
candidate_tests <- candidate_tests[
  candidate_tests$analysis_tier == "primary" &
    candidate_tests$signature_direction %in% c("AD_up_mito", "AD_down_mito") &
    candidate_tests$ranking_candidate %in% TRUE,
  ,
  drop = FALSE
]
assert_true(nrow(candidate_tests) > 0L, "No primary-directional candidate tests for ACAT")
assert_true(
  all(is.na(candidate_tests$raw_p_value) |
    candidate_tests$raw_p_value >= 0 & candidate_tests$raw_p_value <= 1),
  "Candidate raw p-values are outside [0, 1]"
)
assert_true(
  !anyDuplicated(paste(candidate_tests$kda_run_id, candidate_tests$key_driver, sep = "\r")),
  "Candidate table contains duplicated run-driver tests"
)
overall_acat <- prepare_overall_acat_summary(candidate_tests)

coverage_qualified <- overall_acat[
  overall_acat$ranking_coverage_fraction >= minimum_ranking_coverage,
  ,
  drop = FALSE
]
coverage_qualified$overall_acat_evidence_standardized <- NA_real_
for (network in phase12_network_order) {
  index <- coverage_qualified$broad_network == network
  if (!any(index)) next
  maximum <- max(coverage_qualified$overall_acat_negative_log10_p[index], na.rm = TRUE)
  coverage_qualified$overall_acat_evidence_standardized[index] <-
    if (maximum > 0) {
      coverage_qualified$overall_acat_negative_log10_p[index] / maximum
    } else {
      0
    }
}

candidates <- conservative[
  conservative$highlighted_candidate_pool %in% TRUE &
    conservative$conservative_significant_runs >= 1L,
  ,
  drop = FALSE
]
candidates <- merge(
  candidates,
  coverage_qualified[, c(
    "broad_network", "key_driver", "overall_acat_combined_p",
    "overall_acat_negative_log10_p", "overall_acat_evidence_standardized",
    "ranking_runs", "eligible_directional_runs", "ranking_coverage_fraction"
  )],
  by = c("broad_network", "key_driver"),
  all = FALSE,
  sort = FALSE
)
assert_true(nrow(candidates) > 0L, "No highlighted conservative candidates passed ranking coverage")
candidates$network_display_order <- match(candidates$broad_network, phase12_network_order)
candidates <- candidates[
  order(
    candidates$network_display_order,
    candidates$overall_acat_combined_p,
    -candidates$conservative_fine_cell_types,
    candidates$key_driver
  ),
  ,
  drop = FALSE
]

if (nrow(candidates) > maximum_rows) {
  capped <- lapply(phase12_network_order, function(network) {
    x <- candidates[candidates$broad_network == network, , drop = FALSE]
    utils::head(x, maximum_per_network)
  })
  candidates <- do.call(rbind, capped)
  candidates <- candidates[!is.na(candidates$broad_network), , drop = FALSE]
}
if (nrow(candidates) > maximum_rows) candidates <- utils::head(candidates, maximum_rows)
assert_true(nrow(candidates) >= 6L, "Fewer than six candidate rows remain for Figure B")
rownames(candidates) <- NULL
candidates$driver_display_order <- seq_len(nrow(candidates))
candidates$display_network <- unname(phase12_network_labels[candidates$broad_network])
candidates$network_color <- unname(phase12_network_colors[candidates$broad_network])
candidates$selection_rule <- paste0(
  "Highlighted non-mtDNA conservative candidates ranked by overall ACAT P; ranking coverage >= ",
  format(minimum_ranking_coverage, trim = TRUE),
  if (nrow(conservative[conservative$highlighted_candidate_pool %in% TRUE, ]) > maximum_rows) {
    paste0("; capped at ", maximum_per_network, " per network")
  } else ""
)

group_order <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
direction_order <- c("AD_up_mito", "AD_down_mito")
grid <- expand.grid(
  driver_display_order = candidates$driver_display_order,
  signature_group = group_order,
  signature_direction = direction_order,
  KEEP.OUT.ATTRS = FALSE,
  stringsAsFactors = FALSE
)
grid <- merge(
  grid,
  candidates,
  by = "driver_display_order",
  all.x = TRUE,
  sort = FALSE
)

run_metadata <- unique(candidate_tests[, c(
  "kda_run_id", "broad_network", "signature_group", "signature_direction"
)])
assert_true(!anyDuplicated(run_metadata$kda_run_id), "KDA run metadata are inconsistent")
selected_tests <- candidate_tests[
  candidate_tests$key_driver %in% unique(candidates$key_driver),
  ,
  drop = FALSE
]
cell_statistics <- lapply(seq_len(nrow(grid)), function(index) {
  network <- grid$broad_network[[index]]
  driver <- grid$key_driver[[index]]
  signature_group <- grid$signature_group[[index]]
  direction <- grid$signature_direction[[index]]
  run_ids <- run_metadata$kda_run_id[
    run_metadata$broad_network == network &
      run_metadata$signature_group == signature_group &
      run_metadata$signature_direction == direction
  ]
  tested <- selected_tests[
    selected_tests$broad_network == network &
      selected_tests$key_driver == driver &
      selected_tests$signature_group == signature_group &
      selected_tests$signature_direction == direction,
    ,
    drop = FALSE
  ]
  assert_true(!anyDuplicated(tested$kda_run_id), "Duplicated candidate tests within a stratum")
  assert_true(all(tested$kda_run_id %in% run_ids), "Candidate test has no matching eligible run")
  p_values <- rep(NA_real_, length(run_ids))
  if (nrow(tested)) {
    p_values[match(tested$kda_run_id, run_ids)] <- tested$raw_p_value
  }
  candidate_runs_tested <- nrow(tested)
  eligible_runs <- length(run_ids)
  significant_runs <- sum(tested$adjusted_p_value <= 0.05)
  combined_p <- if (candidate_runs_tested > 0L) {
    acat_combine_netweaver(p_values, na_action = "na.to1")
  } else {
    NA_real_
  }
  data.frame(
    candidate_runs_tested = candidate_runs_tested,
    eligible_runs = eligible_runs,
    ranking_coverage_fraction_group = if (eligible_runs > 0L) {
      candidate_runs_tested / eligible_runs
    } else {
      NA_real_
    },
    significant_runs = significant_runs,
    significant_run_fraction = if (candidate_runs_tested > 0L) {
      significant_runs / candidate_runs_tested
    } else {
      NA_real_
    },
    acat_combined_p = combined_p,
    acat_negative_log10_p = if (is.finite(combined_p)) {
      -log10(max(combined_p, .Machine$double.xmin))
    } else {
      NA_real_
    },
    stringsAsFactors = FALSE
  )
})
grid <- cbind(grid, do.call(rbind, cell_statistics))
grid$sex <- ifelse(grepl("^F_", grid$signature_group), "Female", "Male")
grid$apoe_group <- sub("^[FM]_", "", grid$signature_group)
grid$display_status <- ifelse(
  is.na(grid$candidate_runs_tested) | grid$candidate_runs_tested == 0,
  "no_eligible_or_tested_run",
  ifelse(grid$significant_runs == 0, "tested_no_significant_run", "tested_significant")
)

finite_evidence <- grid$acat_negative_log10_p[
  is.finite(grid$acat_negative_log10_p) & grid$display_status != "no_eligible_or_tested_run"
]
assert_true(length(finite_evidence) > 0L, "No finite Figure B evidence values were found")
evidence_cap <- unname(stats::quantile(finite_evidence, 0.95, type = 8, na.rm = TRUE))
if (!is.finite(evidence_cap) || evidence_cap <= 0) evidence_cap <- max(finite_evidence, na.rm = TRUE)
grid$acat_negative_log10_p_display <- pmin(grid$acat_negative_log10_p, evidence_cap)
grid$evidence_color_cap <- evidence_cap
grid$acat_input_p_value <- "raw_p_value"
grid$acat_na_action <- "na.to1"
grid$schema_version <- "phase12_kda_figure_b_acat_plotted_data_v1"
grid <- grid[
  order(
    grid$driver_display_order,
    match(grid$signature_direction, direction_order),
    match(grid$signature_group, group_order)
  ),
  ,
  drop = FALSE
]
rownames(grid) <- NULL

required_output_columns <- c(
  "schema_version", "broad_network", "network_display_order", "key_driver",
  "driver_display_order", "signature_group", "sex", "apoe_group",
  "signature_direction", "candidate_runs_tested", "eligible_runs",
  "ranking_coverage_fraction_group", "significant_runs",
  "significant_run_fraction", "acat_combined_p", "acat_negative_log10_p",
  "acat_negative_log10_p_display", "evidence_color_cap",
  "overall_acat_combined_p", "overall_acat_negative_log10_p",
  "overall_acat_evidence_standardized", "acat_input_p_value", "acat_na_action",
  "ranking_runs", "eligible_directional_runs", "ranking_coverage_fraction",
  "conservative_significant_runs", "conservative_fine_cell_types",
  "display_status", "selection_rule", "network_color", "display_network"
)
missing_output <- setdiff(required_output_columns, names(grid))
assert_true(
  !length(missing_output),
  paste("Figure B plotted data are missing:", paste(missing_output, collapse = ", "))
)
plotted_data <- grid[, required_output_columns, drop = FALSE]

row_positions <- numeric(nrow(candidates))
current_y <- nrow(candidates) + 3
for (index in seq_len(nrow(candidates))) {
  row_positions[[index]] <- current_y
  network_changes <- index < nrow(candidates) &&
    candidates$broad_network[[index + 1L]] != candidates$broad_network[[index]]
  current_y <- current_y - if (network_changes) 1.55 else 1
}
candidates$row_y <- row_positions
y_lookup <- setNames(candidates$row_y, candidates$driver_display_order)
grid$row_y <- unname(y_lookup[as.character(grid$driver_display_order)])

facet_offsets <- c(AD_up_mito = 0, AD_down_mito = 7)
group_offsets <- setNames(0:5, group_order)
grid$x <- unname(facet_offsets[grid$signature_direction]) +
  unname(group_offsets[grid$signature_group])

palette <- rev(grDevices::hcl.colors(100, "Cividis"))
evidence_color <- function(value) {
  if (!is.finite(value)) return("white")
  scaled <- min(max(value / evidence_cap, 0), 1)
  palette[[1L + floor(scaled * (length(palette) - 1L))]]
}

draw_panel_b <- function() {
  maximum_y <- max(candidates$row_y)
  minimum_y <- min(candidates$row_y)
  graphics::par(
    mar = c(2.2, 1.0, 4.7, 0.8),
    xaxs = "i", yaxs = "i", family = "sans", xpd = NA
  )
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(-5.0, 18.5),
    ylim = c(minimum_y - 3.5, maximum_y + 3.6)
  )

  for (direction in direction_order) {
    offset <- facet_offsets[[direction]]
    for (column in 0:5) {
      for (row in candidates$row_y) {
        graphics::rect(
          offset + column - 0.43, row - 0.43,
          offset + column + 0.43, row + 0.43,
          col = "#F7F8FA", border = "#E4E7EB", lwd = 0.45
        )
      }
    }
    graphics::segments(
      offset + 2.5, minimum_y - 0.6,
      offset + 2.5, maximum_y + 1.9,
      col = "#AEB4BB", lwd = 0.75
    )
  }

  for (network in unique(candidates$broad_network)) {
    rows <- candidates$row_y[candidates$broad_network == network]
    graphics::rect(
      -3.05, min(rows) - 0.43, -2.83, max(rows) + 0.43,
      col = phase12_network_colors[[network]], border = NA
    )
    graphics::text(
      -3.48, mean(range(rows)),
      labels = phase12_network_labels[[network]],
      srt = 90, cex = 0.62, font = 2, col = "#333333"
    )
  }
  for (index in seq_len(nrow(candidates))) {
    graphics::text(
      -0.62, candidates$row_y[[index]], candidates$key_driver[[index]],
      adj = c(1, 0.5), cex = 0.72, font = 2, col = "#202020"
    )
  }

  for (index in seq_len(nrow(grid))) {
    status <- grid$display_status[[index]]
    if (status == "no_eligible_or_tested_run") {
      graphics::points(grid$x[[index]], grid$row_y[[index]], pch = 4, cex = 0.72, col = "#B8BDC4", lwd = 0.9)
    } else if (status == "tested_no_significant_run") {
      graphics::points(grid$x[[index]], grid$row_y[[index]], pch = 21, cex = 0.48, bg = "white", col = "#A8ADB4", lwd = 0.8)
    } else {
      fraction <- grid$significant_run_fraction[[index]]
      graphics::points(
        grid$x[[index]], grid$row_y[[index]],
        pch = 21,
        cex = max(0.5, 2.45 * sqrt(fraction)),
        bg = evidence_color(grid$acat_negative_log10_p_display[[index]]),
        col = "#4D535A",
        lwd = 0.55
      )
    }
  }

  for (index in seq_len(nrow(candidates))) {
    y <- candidates$row_y[[index]]
    score <- candidates$overall_acat_evidence_standardized[[index]]
    graphics::rect(14, y - 0.25, 16, y + 0.25, col = "#EEF1F4", border = NA)
    graphics::rect(14, y - 0.25, 14 + 2 * score, y + 0.25, col = "#344E73", border = NA)
    graphics::text(
      16.17, y,
      labels = paste0(
        candidates$ranking_runs[[index]], "/",
        candidates$eligible_directional_runs[[index]]
      ),
      adj = c(0, 0.5), cex = 0.52, col = "#555555"
    )
  }

  for (direction in direction_order) {
    offset <- facet_offsets[[direction]]
    label <- if (direction == "AD_up_mito") {
      "AD-up mitochondrial signature"
    } else {
      "AD-down mitochondrial signature"
    }
    graphics::text(offset + 2.5, maximum_y + 2.85, label, cex = 0.86, font = 2, col = "#202020")
    graphics::text(offset + 1, maximum_y + 1.95, "Female", cex = 0.70, font = 2, col = "#404040")
    graphics::text(offset + 4, maximum_y + 1.95, "Male", cex = 0.70, font = 2, col = "#404040")
    for (column in 0:5) {
      graphics::text(
        offset + column, maximum_y + 1.05,
        labels = c("e2", "e3/3", "e4", "e2", "e3/3", "e4")[[column + 1L]],
        cex = 0.66, col = "#404040"
      )
    }
  }
  graphics::text(15, maximum_y + 2.85, "Overall score", cex = 0.78, font = 2, col = "#202020")
  graphics::text(15, maximum_y + 1.95, "standardized\n-log10(ACAT P)", cex = 0.58, col = "#505050")
  graphics::text(16.15, maximum_y + 1.05, "runs", adj = c(0, 0.5), cex = 0.52, col = "#606060")

  legend_y <- minimum_y - 2.25
  color_left <- 0
  color_right <- 4.2
  color_steps <- length(palette)
  for (index in seq_len(color_steps)) {
    x1 <- color_left + (index - 1L) / color_steps * (color_right - color_left)
    x2 <- color_left + index / color_steps * (color_right - color_left)
    graphics::rect(x1, legend_y - 0.20, x2, legend_y + 0.20, col = palette[[index]], border = NA)
  }
  graphics::text(
    mean(c(color_left, color_right)), legend_y + 0.58,
    "-log10(ACAT P)", cex = 0.63, font = 2, col = "#333333"
  )
  graphics::text(color_left, legend_y - 0.50, "0", cex = 0.53, col = "#555555")
  graphics::text(
    color_right, legend_y - 0.50,
    paste0("≥", format(round(evidence_cap, 2), trim = TRUE)),
    cex = 0.53, col = "#555555"
  )

  size_x <- c(6.4, 7.8, 9.3)
  size_values <- c(0.25, 0.50, 1.00)
  for (index in seq_along(size_x)) {
    graphics::points(
      size_x[[index]], legend_y,
      pch = 21, cex = 2.45 * sqrt(size_values[[index]]),
      bg = "#617CA3", col = "#4D535A", lwd = 0.55
    )
    graphics::text(
      size_x[[index]], legend_y - 0.62,
      paste0(size_values[[index]] * 100, "%"),
      cex = 0.52, col = "#555555"
    )
  }
  graphics::text(
    mean(range(size_x)), legend_y + 0.78,
    "Significant tested runs", cex = 0.63, font = 2, col = "#333333"
  )
  graphics::points(11.2, legend_y, pch = 21, cex = 0.48, bg = "white", col = "#A8ADB4")
  graphics::text(11.55, legend_y, "tested; none significant", adj = c(0, 0.5), cex = 0.52, col = "#555555")
  graphics::points(14.8, legend_y, pch = 4, cex = 0.72, col = "#B8BDC4")
  graphics::text(15.15, legend_y, "not eligible/tested", adj = c(0, 0.5), cex = 0.52, col = "#555555")

  graphics::title(
    main = "Sex- and APOE-stratified support for prioritized mitochondrial key drivers",
    cex.main = 1.08,
    font.main = 2,
    col.main = "#202020",
    line = 2.5
  )
  graphics::mtext(
    "Primary directional KDA evidence combined by ACAT; descriptive strata, not formal interaction tests",
    side = 3, line = 0.9, cex = 0.74, col = "#555555"
  )
}

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
table_path <- file.path(output_dir, paste0(args$basename, "_plotted_data.tsv"))
svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
pdf_path <- file.path(output_dir, paste0(args$basename, ".pdf"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))
log_path <- file.path(output_dir, paste0(args$basename, "_generation_log.tsv"))

atomic_write_table(plotted_data, table_path)
figure_height <- max(5.8, min(7.2, 3.5 + 0.25 * nrow(candidates)))
message("Writing ", svg_path)
render_atomic(svg_path, function(path) open_svg_device(path, 7.1, figure_height), draw_panel_b)
message("Writing ", pdf_path)
render_atomic(pdf_path, function(path) open_pdf_device(path, 7.1, figure_height), draw_panel_b)
message("Writing ", png_path)
render_atomic(png_path, function(path) open_png_device(path, 7.1, figure_height, 450), draw_panel_b)
atomic_write_table(
  data.frame(
    schema_version = "phase12_kda_figure_generation_log_v1",
    generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    figure_script = "scripts/figures/analysis/phease12_kda/visualize_phase12_kda_sex_apoe.R",
    input_candidate_tests = candidate_path,
    input_conservative_summary = conservative_path,
    input_checks = checks_path,
    figure_basename = args$basename,
    ranking_method = "acat",
    acat_input_p_value = "raw_p_value",
    acat_na_action = "na.to1",
    acat_example_max_abs_error = acat_example_max_abs_error,
    acat_reference = "https://github.com/mw201608/NetWeaver/blob/master/R/ACAT.R",
    selection_rule = unique(candidates$selection_rule),
    plotted_network_driver_rows = nrow(candidates),
    plotted_stratum_direction_cells = nrow(plotted_data),
    evidence_color_cap = evidence_cap,
    width_inches = 7.1,
    height_inches = figure_height,
    png_dpi = 450,
    data_checks_passed = all(checks$passed),
    stringsAsFactors = FALSE
  ),
  log_path
)

message(
  "Figure B complete: ", nrow(candidates), " network-driver rows; evidence cap ",
  format(round(evidence_cap, 3), trim = TRUE)
)
