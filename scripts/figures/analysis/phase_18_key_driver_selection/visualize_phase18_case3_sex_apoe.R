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
    "phase_18_key_driver_selection/visualize_phase18_case3_sex_apoe.R ",
    "[--data-dir DIR] [--output-dir DIR] [--evidence-cap VALUE] ",
    "[--network-q-axis-max VALUE] [--png-dpi DPI] ",
    "[--width-inches VALUE] [--height-inches VALUE]\n",
    sep = ""
  )
}

cli_args <- commandArgs(trailingOnly = TRUE)
args <- parse_value_args(
  cli_args,
  defaults = list(
    data_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "case3_sex_apoe"
    ),
    output_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "case3_sex_apoe"
    ),
    evidence_cap = "8",
    network_q_axis_max = "12",
    png_dpi = "450",
    width_inches = "15",
    height_inches = "11"
  ),
  allowed = c(
    "--data-dir", "--output-dir", "--evidence-cap",
    "--network-q-axis-max", "--png-dpi", "--width-inches",
    "--height-inches"
  )
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

evidence_cap <- suppressWarnings(as.numeric(args$evidence_cap))
network_q_axis_max <- suppressWarnings(as.numeric(args$network_q_axis_max))
png_dpi <- suppressWarnings(as.integer(args$png_dpi))
figure_width_inches <- suppressWarnings(as.numeric(args$width_inches))
figure_height_inches <- suppressWarnings(as.numeric(args$height_inches))
assert_true(
  length(evidence_cap) == 1L && is.finite(evidence_cap) && evidence_cap > 0,
  "--evidence-cap must be positive"
)
assert_true(
  length(network_q_axis_max) == 1L && is.finite(network_q_axis_max) &&
    network_q_axis_max > 0,
  "--network-q-axis-max must be positive"
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
assert_true(capabilities("cairo"), "This R installation lacks Cairo support")

project_root <- normalizePath(getwd(), mustWork = TRUE)
data_dir <- normalizePath(absolute_path(args$data_dir, project_root), mustWork = TRUE)
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

plot_path <- file.path(data_dir, "phase18_case3_sex_apoe_plot_data.tsv")
row_path <- file.path(data_dir, "phase18_case3_sex_apoe_row_annotations.tsv")
plot_data <- read_tsv(plot_path)
row_data <- read_tsv(row_path)

require_columns(
  plot_data,
  c(
    "case_id", "current_symbol", "broad_network", "network_label",
    "network_color", "atlas_display_order", "network_order",
    "context_display_order", "circle_displayed", "within_case_rank",
    "signature_direction", "direction_order", "signature_group",
    "group_order", "column_order", "eligible_query_count",
    "usable_query_count", "conservative_support_count", "support_fraction",
    "stratum_acat_p", "capped_negative_log10_stratum_acat_p", "cell_state"
  ),
  basename(plot_path)
)
require_columns(
  row_data,
  c(
    "case_id", "current_symbol", "broad_network", "network_label",
    "network_color", "atlas_display_order", "network_order",
    "context_display_order", "circle_displayed", "within_case_rank",
    "evidence_tier", "extended_reference_member", "eligible_run_count",
    "usable_run_count", "conservative_support_count", "coverage_fraction",
    "recurrence_fraction", "negative_log10_aggregate_acat_q"
  ),
  basename(row_path)
)

direction_order <- c("AD_up_mito", "AD_down_mito")
group_order <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
allowed_states <- c(
  "supporting_tested", "tested_zero_support",
  "eligible_no_usable_test", "no_eligible_query"
)

assert_true(nrow(row_data) == 22L, "Row annotations must contain 22 contexts")
assert_true(nrow(plot_data) == 264L, "Plotted data must contain 264 cells")
assert_true(
  all(row_data$case_id == "case3_not_core_mito") &&
    all(plot_data$case_id == "case3_not_core_mito"),
  "Unexpected case ID"
)
assert_true(
  identical(sort(unique(row_data$context_display_order)), seq_len(22L)),
  "Context display order must be 1 through 22"
)
assert_true(
  identical(sort(unique(plot_data$column_order)), seq_len(12L)),
  "Column order must be 1 through 12"
)
assert_true(
  identical(
    unique(plot_data$signature_direction[order(plot_data$direction_order)]),
    direction_order
  ),
  "Direction order drifted"
)
assert_true(
  identical(
    unique(plot_data$signature_group[order(plot_data$group_order)]),
    group_order
  ),
  "Group order drifted"
)
assert_true(all(plot_data$cell_state %in% allowed_states), "Unsupported cell state")
assert_true(sum(row_data$circle_displayed) == 21L, "Circle-display flags do not sum to 21")
assert_true(
  all(
    is.na(plot_data$capped_negative_log10_stratum_acat_p) |
      plot_data$capped_negative_log10_stratum_acat_p <= evidence_cap + 1e-12
  ),
  "A plotted evidence value exceeds the cap"
)
assert_true(
  all(row_data$negative_log10_aggregate_acat_q <= network_q_axis_max + 1e-12),
  "Network q track exceeds its axis"
)

row_data <- row_data[order(row_data$context_display_order), , drop = FALSE]
plot_data <- plot_data[
  order(plot_data$context_display_order, plot_data$column_order),
  ,
  drop = FALSE
]

text_dark <- "#242424"
text_mid <- "#646464"
grid_color <- "#E2E2E2"
empty_color <- "#F2F2F2"
neutral_track <- "#3F3F3F"
cividis_palette <- grDevices::hcl.colors(256L, palette = "cividis")
tier_colors <- c(
  tier1_recurrent_stable = "#0072B2",
  tier2_localized_or_unstable = "#E69F00",
  tier_not_assessable = "#8A8A8A"
)
tier_labels <- c(
  tier1_recurrent_stable = "Tier 1: recurrent/stable",
  tier2_localized_or_unstable = "Tier 2: localized/unstable",
  tier_not_assessable = "Tier not assessable"
)

evidence_color <- function(value) {
  if (is.na(value)) return(empty_color)
  position <- 1L + round(255 * max(0, min(1, value / evidence_cap)))
  cividis_palette[[position]]
}

row_y <- function(context_order) 23 - context_order

draw_main_panel <- function() {
  graphics::par(mar = c(4.1, 0.4, 0.5, 0.2), xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(-6.75, 22.25), ylim = c(-0.70, 25.60),
    xaxs = "i", yaxs = "i"
  )

  q_start <- 13.15
  q_end <- 15.70
  support_x <- 16.55
  coverage_start <- 17.25
  coverage_end <- 18.35
  coverage_label_x <- 19.05
  tier_x1 <- 19.62
  tier_x2 <- 19.86
  rank_x <- 20.78

  for (index in seq_len(nrow(row_data))) {
    record <- row_data[index, , drop = FALSE]
    y <- row_y(record$context_display_order[[1L]])

    graphics::rect(
      -6.66, y - 0.37, -6.43, y + 0.37,
      col = record$network_color[[1L]], border = NA
    )
    graphics::points(
      -6.13, y, pch = if (isTRUE(record$circle_displayed[[1L]])) 16 else 1,
      cex = 0.63, lwd = 0.9, col = text_dark
    )
    if (isTRUE(record$extended_reference_member[[1L]])) {
      graphics::points(
        -5.78, y, pch = 23, bg = "white", col = text_dark,
        cex = 0.66, lwd = 0.8
      )
    }
    graphics::text(
      -5.50, y, record$current_symbol[[1L]], adj = c(0, 0.5),
      cex = 0.74, font = 2, col = text_dark
    )
    graphics::text(
      -3.12, y, record$network_label[[1L]], adj = c(0, 0.5),
      cex = 0.70, col = text_dark
    )

    graphics::segments(q_start, y, q_end, y, col = "#D3D3D3", lwd = 0.85)
    q_x <- q_start + min(
      record$negative_log10_aggregate_acat_q[[1L]], network_q_axis_max
    ) / network_q_axis_max * (q_end - q_start)
    graphics::segments(q_start, y, q_x, y, col = neutral_track, lwd = 1.7)
    graphics::points(q_x, y, pch = 21, bg = "white", col = neutral_track, cex = 0.57, lwd = 0.8)

    graphics::text(
      support_x, y,
      paste0(
        record$conservative_support_count[[1L]], "/",
        record$usable_run_count[[1L]]
      ),
      cex = 0.70, font = 2, col = text_dark
    )
    graphics::segments(
      coverage_start, y, coverage_end, y,
      col = "#D3D3D3", lwd = 0.9
    )
    coverage_x <- coverage_start + record$coverage_fraction[[1L]] *
      (coverage_end - coverage_start)
    graphics::segments(
      coverage_start, y, coverage_x, y,
      col = neutral_track, lwd = 1.7
    )
    graphics::points(
      coverage_x, y, pch = 21, bg = "white", col = neutral_track,
      cex = 0.52, lwd = 0.75
    )
    graphics::text(
      coverage_label_x, y,
      paste0(record$usable_run_count[[1L]], "/", record$eligible_run_count[[1L]]),
      cex = 0.67, font = 2, col = text_dark
    )
    graphics::rect(
      tier_x1, y - 0.28, tier_x2, y + 0.28,
      col = tier_colors[[record$evidence_tier[[1L]]]], border = NA
    )
    graphics::text(
      rank_x, y, record$within_case_rank[[1L]],
      cex = 0.70, font = 2, col = text_dark
    )
  }

  for (index in seq_len(nrow(plot_data))) {
    record <- plot_data[index, , drop = FALSE]
    x <- record$column_order[[1L]]
    y <- row_y(record$context_display_order[[1L]])
    state <- record$cell_state[[1L]]
    cell_fill <- if (state == "no_eligible_query") "#F0F0F0" else "#FBFBFB"
    graphics::rect(
      x - 0.44, y - 0.37, x + 0.44, y + 0.37,
      col = cell_fill, border = grid_color, lwd = 0.45
    )
    if (state == "supporting_tested") {
      graphics::points(
        x, y, pch = 21,
        bg = evidence_color(record$capped_negative_log10_stratum_acat_p[[1L]]),
        col = "#282828",
        cex = 1.25 * sqrt(record$support_fraction[[1L]]),
        lwd = 0.75
      )
    } else if (state == "tested_zero_support") {
      graphics::points(x, y, pch = 1, col = "#555555", cex = 0.46, lwd = 0.75)
    } else if (state == "eligible_no_usable_test") {
      graphics::points(x, y, pch = 4, col = "#858585", cex = 0.58, lwd = 1.0)
    } else {
      graphics::segments(x - 0.12, y, x + 0.12, y, col = "#A7A7A7", lwd = 0.85)
    }
  }

  gene_change <- which(row_data$current_symbol[-1L] != row_data$current_symbol[-nrow(row_data)])
  if (length(gene_change)) {
    for (index in gene_change) {
      boundary_y <- row_y(index) - 0.50
      graphics::segments(-6.66, boundary_y, 20.98, boundary_y, col = "#BDBDBD", lwd = 0.62)
    }
  }
  graphics::segments(6.50, 0.45, 6.50, 22.45, col = "#909090", lty = 2, lwd = 0.9)

  graphics::par(xpd = NA)
  apoe_labels <- rep(c("APOE ε2", "APOE ε3/ε3", "APOE ε4"), 4L)
  graphics::text(
    seq_len(12L), rep(23.10, 12L), apoe_labels,
    srt = 38, adj = c(0, 0.5), cex = 0.66, col = text_dark
  )
  sex_centers <- c(2, 5, 8, 11)
  graphics::text(
    sex_centers, rep(24.05, 4L),
    c("Female", "Male", "Female", "Male"),
    cex = 0.76, font = 2, col = text_dark
  )
  graphics::segments(c(0.60, 3.60, 6.60, 9.60), 23.72, c(3.40, 6.40, 9.40, 12.40), 23.72, col = "#777777", lwd = 0.65)
  graphics::text(
    c(3.50, 9.50), rep(25.05, 2L),
    c("AD-up mitochondrial query", "AD-down mitochondrial query"),
    cex = 0.88, font = 2, col = text_dark
  )
  graphics::segments(c(0.55, 6.55), 24.67, c(6.45, 12.45), 24.67, col = "#555555", lwd = 0.8)

  graphics::text(-6.55, 23.15, "Net.", cex = 0.67, font = 2, srt = 38, adj = c(0, 0.5))
  graphics::text(-6.10, 23.15, "Circle", cex = 0.67, font = 2, srt = 38, adj = c(0, 0.5))
  graphics::text(-5.72, 23.15, "Extended", cex = 0.67, font = 2, srt = 38, adj = c(0, 0.5))
  graphics::text(-5.50, 24.05, "Gene", cex = 0.72, font = 2, adj = c(0, 0.5))
  graphics::text(-3.12, 24.05, "Broad network", cex = 0.72, font = 2, adj = c(0, 0.5))
  graphics::text(mean(c(q_start, q_end)), 24.45, "Network aggregate q", cex = 0.72, font = 2)
  graphics::text(mean(c(q_start, q_end)), 23.85, "−log10(q), separate scale", cex = 0.67, col = text_mid)
  graphics::text(support_x, 24.20, "Support /", cex = 0.69, font = 2)
  graphics::text(support_x, 23.65, "usable", cex = 0.69, font = 2)
  graphics::text(mean(c(coverage_start, coverage_end)), 24.20, "Coverage", cex = 0.69, font = 2)
  graphics::text(coverage_label_x, 23.65, "usable / eligible", cex = 0.65, font = 2)
  graphics::text(mean(c(tier_x1, tier_x2)), 24.05, "Tier", cex = 0.68, font = 2, srt = 38)
  graphics::text(rank_x, 24.05, "Rank", cex = 0.68, font = 2, srt = 38)

  q_ticks <- c(0, network_q_axis_max / 2, network_q_axis_max)
  q_tick_x <- q_start + q_ticks / network_q_axis_max * (q_end - q_start)
  graphics::segments(q_tick_x, 0.25, q_tick_x, 0.42, col = text_mid, lwd = 0.65)
  graphics::text(q_tick_x, -0.06, format(q_ticks, trim = TRUE), cex = 0.66, col = text_mid)
  graphics::mtext(
    "Each cell aggregates eligible fine-cell-type queries within one fixed broad Bayesian network.",
    side = 1, line = 2.35, adj = 0.02, cex = 0.70, col = text_mid
  )
}

draw_legend_panel <- function() {
  graphics::par(mar = c(1.2, 0.6, 0.5, 0.6), xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1), xaxs = "i", yaxs = "i")
  graphics::par(xpd = NA)

  graphics::text(0.02, 0.975, "Figure keys", adj = c(0, 1), cex = 0.90, font = 2, col = text_dark)
  graphics::text(0.02, 0.925, "Stratum ACAT evidence", adj = c(0, 1), cex = 0.74, font = 2, col = text_dark)
  gradient_x <- seq(0.03, 0.72, length.out = 81L)
  for (index in seq_len(length(gradient_x) - 1L)) {
    value <- (index - 1) / (length(gradient_x) - 2) * evidence_cap
    graphics::rect(
      gradient_x[[index]], 0.858, gradient_x[[index + 1L]], 0.882,
      col = evidence_color(value), border = NA
    )
  }
  graphics::rect(gradient_x[[1L]], 0.858, tail(gradient_x, 1L), 0.882, border = "#555555", lwd = 0.6)
  graphics::text(c(gradient_x[[1L]], mean(range(gradient_x)), tail(gradient_x, 1L)), 0.842, c("0", format(evidence_cap / 2, trim = TRUE), format(evidence_cap, trim = TRUE)), cex = 0.66, adj = c(0.5, 1))
  graphics::text(0.03, 0.805, "capped −log10(stratum ACAT P)", adj = c(0, 1), cex = 0.69, col = text_mid)

  graphics::text(0.02, 0.755, "Supporting-dot area", adj = c(0, 1), cex = 0.74, font = 2)
  size_values <- c(0.25, 0.50, 0.75, 1.00)
  size_x <- c(0.10, 0.31, 0.54, 0.79)
  for (index in seq_along(size_values)) {
    graphics::points(
      size_x[[index]], 0.700, pch = 21, bg = evidence_color(0.65 * evidence_cap),
      col = "#282828", cex = 1.25 * sqrt(size_values[[index]]), lwd = 0.7
    )
    graphics::text(size_x[[index]], 0.660, format(size_values[[index]], nsmall = 2), cex = 0.66)
  }
  graphics::text(0.02, 0.625, "fraction of usable queries supporting", adj = c(0, 1), cex = 0.67, col = text_mid)

  graphics::text(0.02, 0.580, "Cell states", adj = c(0, 1), cex = 0.74, font = 2)
  state_y <- c(0.535, 0.497, 0.459, 0.421)
  graphics::points(0.07, state_y[[1L]], pch = 21, bg = evidence_color(0.65 * evidence_cap), col = text_dark, cex = 0.80)
  graphics::points(0.07, state_y[[2L]], pch = 1, col = "#555555", cex = 0.50)
  graphics::points(0.07, state_y[[3L]], pch = 4, col = "#858585", cex = 0.58, lwd = 1)
  graphics::segments(0.045, state_y[[4L]], 0.095, state_y[[4L]], col = "#A7A7A7", lwd = 0.9)
  graphics::text(
    0.13, state_y,
    c("supporting tested", "tested, zero support", "eligible, no usable test", "no eligible query"),
    adj = c(0, 0.5), cex = 0.67
  )

  graphics::text(0.02, 0.375, "Row annotations", adj = c(0, 1), cex = 0.74, font = 2)
  graphics::points(0.07, 0.335, pch = 16, cex = 0.62)
  graphics::text(0.13, 0.335, "circle-displayed context", adj = c(0, 0.5), cex = 0.67)
  graphics::points(0.07, 0.300, pch = 1, cex = 0.62)
  graphics::text(0.13, 0.300, "passing context below display cap", adj = c(0, 0.5), cex = 0.67)
  graphics::points(0.07, 0.265, pch = 23, bg = "white", cex = 0.65)
  graphics::text(0.13, 0.265, "broader mitochondrial reference", adj = c(0, 0.5), cex = 0.67)

  graphics::text(0.02, 0.225, "Evidence tier", adj = c(0, 1), cex = 0.74, font = 2)
  tier_y <- c(0.188, 0.157, 0.126)
  for (index in seq_along(tier_y)) {
    key <- names(tier_colors)[[index]]
    graphics::rect(0.045, tier_y[[index]] - 0.010, 0.095, tier_y[[index]] + 0.010, col = tier_colors[[key]], border = NA)
    graphics::text(0.13, tier_y[[index]], tier_labels[[key]], adj = c(0, 0.5), cex = 0.64)
  }

  graphics::text(0.52, 0.375, "Network strip", adj = c(0, 1), cex = 0.74, font = 2)
  network_y <- seq(0.335, 0.095, length.out = length(phase12_network_order))
  for (index in seq_along(phase12_network_order)) {
    network <- phase12_network_order[[index]]
    graphics::rect(0.535, network_y[[index]] - 0.010, 0.585, network_y[[index]] + 0.010, col = phase12_network_colors[[network]], border = NA)
    graphics::text(0.61, network_y[[index]], phase12_network_labels[[network]], adj = c(0, 0.5), cex = 0.62)
  }

  graphics::text(
    0.02, 0.055,
    "Neutral right-side points show network q, not stratum P.",
    adj = c(0, 1), cex = 0.64, col = text_mid
  )
  graphics::text(
    0.02, 0.020,
    "Shapes and direct labels preserve meaning without color.",
    adj = c(0, 1), cex = 0.64, col = text_mid
  )
}

draw_figure <- function() {
  graphics::layout(matrix(c(1L, 2L), nrow = 1L), widths = c(12.0, 3.0))
  graphics::par(
    oma = c(2.2, 0.3, 4.6, 0.3), family = "sans",
    fg = text_dark, col.axis = text_dark, col.lab = text_dark,
    col.main = text_dark, lend = "round"
  )
  draw_main_panel()
  draw_legend_panel()
  graphics::mtext(
    "Sex- and APOE-stratified support for Case 3 key-driver candidates",
    side = 3, outer = TRUE, line = 2.85, adj = 0.015,
    cex = 1.38, font = 2, col = text_dark
  )
  graphics::mtext(
    "Primary AD-up and AD-down mitochondrial queries • descriptive strata, not interaction tests",
    side = 3, outer = TRUE, line = 1.62, adj = 0.015,
    cex = 0.98, col = text_mid
  )
  graphics::mtext(
    "15 circle genes • 21 circle-displayed contexts • 22 total passing contexts • 264 cells",
    side = 3, outer = TRUE, line = 0.52, adj = 0.015,
    cex = 0.76, col = text_mid
  )
  graphics::mtext(
    "Case 3 denotes genes outside core MitoCarta; network key-driver evidence prioritizes candidates but does not prove causality.",
    side = 1, outer = TRUE, line = 0.58, adj = 0.015,
    cex = 0.70, col = text_mid
  )
}

basename_value <- "phase18_case3_sex_apoe"
svg_path <- file.path(output_dir, paste0(basename_value, ".svg"))
pdf_path <- file.path(output_dir, paste0(basename_value, ".pdf"))
png_path <- file.path(output_dir, paste0(basename_value, ".png"))

message("Writing ", svg_path)
render_atomic(
  svg_path,
  function(path) open_svg_device(path, figure_width_inches, figure_height_inches),
  draw_figure
)
message("Writing ", pdf_path)
render_atomic(
  pdf_path,
  function(path) open_pdf_device(path, figure_width_inches, figure_height_inches),
  draw_figure
)
message("Writing ", png_path)
render_atomic(
  png_path,
  function(path) open_png_device(path, figure_width_inches, figure_height_inches, dpi = png_dpi),
  draw_figure
)

message(
  "Rendered Case 3 sex/APOE dot heatmap: ", nrow(row_data),
  " rows; ", nrow(plot_data), " cells"
)
