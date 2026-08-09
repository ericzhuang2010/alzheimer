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
    "visualize_phase12_kda_panel_b_sex_apoe.R ",
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
    output_dir = "results/figures/analysis/phase12_kda",
    basename = "phase12_kda_panel_b_sex_apoe",
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

mean_path <- file.path(input_dir, "phase12_kda_mean_of_log_summary.tsv")
conservative_path <- file.path(input_dir, "phase12_kda_conservative_candidate_summary.tsv")
group_path <- file.path(input_dir, "phase12_kda_candidate_group_summary.tsv")
checks_path <- file.path(input_dir, "phase12_kda_figure_data_checks.tsv")
mean_summary <- read_tsv(mean_path)
conservative <- read_tsv(conservative_path)
group_summary <- read_tsv(group_path)
checks <- read_tsv(checks_path)
assert_true(nrow(checks) > 0L && all(checks$passed), "Prepared figure-data checks did not all pass")

require_columns(
  mean_summary,
  c(
    "broad_network", "key_driver", "mean_of_log_score", "ranking_runs",
    "eligible_directional_runs", "ranking_coverage_fraction"
  ),
  basename(mean_path)
)
require_columns(
  conservative,
  c(
    "broad_network", "key_driver", "conservative_significant_runs",
    "conservative_fine_cell_types", "highlighted_candidate_pool"
  ),
  basename(conservative_path)
)
require_columns(
  group_summary,
  c(
    "broad_network", "key_driver", "signature_group", "signature_direction",
    "candidate_runs_tested", "eligible_runs", "significant_runs",
    "significant_run_fraction", "mean_minus_log10_p"
  ),
  basename(group_path)
)

coverage_qualified <- mean_summary[
  mean_summary$ranking_coverage_fraction >= minimum_ranking_coverage,
  ,
  drop = FALSE
]
coverage_qualified$overall_mean_of_log_score_standardized <- NA_real_
for (network in phase12_network_order) {
  index <- coverage_qualified$broad_network == network
  if (!any(index)) next
  maximum <- max(coverage_qualified$mean_of_log_score[index], na.rm = TRUE)
  coverage_qualified$overall_mean_of_log_score_standardized[index] <-
    if (maximum > 0) coverage_qualified$mean_of_log_score[index] / maximum else 0
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
    "broad_network", "key_driver", "mean_of_log_score",
    "overall_mean_of_log_score_standardized", "ranking_runs",
    "eligible_directional_runs", "ranking_coverage_fraction"
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
    -candidates$overall_mean_of_log_score_standardized,
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
  "Highlighted non-mtDNA conservative candidates; ranking coverage >= ",
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
grid <- merge(
  grid,
  group_summary,
  by = c("broad_network", "key_driver", "signature_group", "signature_direction"),
  all.x = TRUE,
  sort = FALSE,
  suffixes = c("", "_group")
)
grid$sex <- ifelse(grepl("^F_", grid$signature_group), "Female", "Male")
grid$apoe_group <- sub("^[FM]_", "", grid$signature_group)
grid$display_status <- ifelse(
  is.na(grid$candidate_runs_tested) | grid$candidate_runs_tested == 0,
  "no_eligible_or_tested_run",
  ifelse(grid$significant_runs == 0, "tested_no_significant_run", "tested_significant")
)

finite_evidence <- grid$mean_minus_log10_p[
  is.finite(grid$mean_minus_log10_p) & grid$display_status != "no_eligible_or_tested_run"
]
assert_true(length(finite_evidence) > 0L, "No finite Figure B evidence values were found")
evidence_cap <- unname(stats::quantile(finite_evidence, 0.95, type = 8, na.rm = TRUE))
if (!is.finite(evidence_cap) || evidence_cap <= 0) evidence_cap <- max(finite_evidence, na.rm = TRUE)
grid$mean_minus_log10_p_display <- pmin(grid$mean_minus_log10_p, evidence_cap)
grid$evidence_color_cap <- evidence_cap
grid$schema_version <- "phase12_kda_figure_b_plotted_data_v1"
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
  "significant_run_fraction", "mean_minus_log10_p",
  "mean_minus_log10_p_display", "evidence_color_cap",
  "mean_of_log_score", "overall_mean_of_log_score_standardized",
  "ranking_runs", "eligible_directional_runs", "ranking_coverage_fraction",
  "conservative_significant_runs", "conservative_fine_cell_types",
  "display_status", "selection_rule", "network_color", "display_network"
)
if (!"ranking_coverage_fraction_group" %in% names(grid)) {
  names(grid)[names(grid) == "ranking_coverage_fraction_group"] <-
    "ranking_coverage_fraction_group"
}
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
        bg = evidence_color(grid$mean_minus_log10_p_display[[index]]),
        col = "#4D535A",
        lwd = 0.55
      )
    }
  }

  for (index in seq_len(nrow(candidates))) {
    y <- candidates$row_y[[index]]
    score <- candidates$overall_mean_of_log_score_standardized[[index]]
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
  graphics::text(15, maximum_y + 1.95, "standardized\nMeanOfLog", cex = 0.58, col = "#505050")
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
    "Mean -log10(KDA P)", cex = 0.63, font = 2, col = "#333333"
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
    "Primary directional KDA evidence; descriptive strata, not formal interaction tests",
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
    figure_script = "scripts/figures/analysis/phease12_kda/visualize_phase12_kda_panel_b_sex_apoe.R",
    input_mean_summary = mean_path,
    input_conservative_summary = conservative_path,
    input_group_summary = group_path,
    input_checks = checks_path,
    figure_basename = args$basename,
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
