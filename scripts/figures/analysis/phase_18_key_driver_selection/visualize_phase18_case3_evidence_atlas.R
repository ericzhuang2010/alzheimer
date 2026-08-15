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
    "phase_18_key_driver_selection/visualize_phase18_case3_evidence_atlas.R ",
    "[--data-dir DIR] [--output-dir DIR] [--evidence-cap VALUE] ",
    "[--png-dpi DPI] [--width-inches VALUE] [--height-inches VALUE]\n",
    sep = ""
  )
}

cli_args <- commandArgs(trailingOnly = TRUE)
args <- parse_value_args(
  cli_args,
  defaults = list(
    data_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "case3_evidence_atlas"
    ),
    output_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "case3_evidence_atlas"
    ),
    evidence_cap = "12",
    png_dpi = "450",
    width_inches = "12",
    height_inches = "8"
  ),
  allowed = c(
    "--data-dir", "--output-dir", "--evidence-cap", "--png-dpi",
    "--width-inches", "--height-inches"
  )
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

evidence_cap <- suppressWarnings(as.numeric(args$evidence_cap))
png_dpi <- suppressWarnings(as.integer(args$png_dpi))
figure_width_inches <- suppressWarnings(as.numeric(args$width_inches))
figure_height_inches <- suppressWarnings(as.numeric(args$height_inches))
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
assert_true(capabilities("cairo"), "This R installation lacks Cairo support")

project_root <- normalizePath(getwd(), mustWork = TRUE)
data_dir <- normalizePath(absolute_path(args$data_dir, project_root), mustWork = TRUE)
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

summary_path <- file.path(data_dir, "phase18_case3_gene_summary.tsv")
detail_path <- file.path(data_dir, "phase18_case3_gene_network_details.tsv")
plot_path <- file.path(data_dir, "phase18_case3_evidence_atlas_plot_data.tsv")
summary_data <- read_tsv(summary_path)
detail_data <- read_tsv(detail_path)
plot_data <- read_tsv(plot_path)

require_columns(
  summary_data,
  c(
    "case_id", "current_symbol", "atlas_display_order",
    "extended_reference_member", "passing_broad_network_count",
    "unique_supporting_fine_cell_type_count", "eligible_query_count",
    "usable_query_count", "query_coverage_fraction",
    "conservative_supporting_query_count", "query_recurrence_fraction",
    "supporting_group_count", "supporting_direction_count"
  ),
  basename(summary_path)
)
require_columns(
  detail_data,
  c(
    "case_id", "current_symbol", "atlas_display_order", "broad_network",
    "network_order", "network_color", "circle_displayed",
    "stability_candidate_fraction", "stability_assessable",
    "degree_matched_empirical_tail_p",
    "degree_diagnostic_complete", "degree_sensitivity_blocking_gate"
  ),
  basename(detail_path)
)
require_columns(
  plot_data,
  c(
    "case_id", "current_symbol", "atlas_display_order", "broad_network",
    "network_order", "network_label", "network_color", "tile_status",
    "passing_context", "circle_displayed", "within_case_rank",
    "aggregate_acat_q", "capped_negative_log10_aggregate_acat_q"
  ),
  basename(plot_path)
)

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
  "Phase 18 network order differs from the established figure order"
)
assert_true(nrow(summary_data) == 15L, "Gene summary must contain 15 rows")
assert_true(nrow(detail_data) == 22L, "Gene-network details must contain 22 rows")
assert_true(nrow(plot_data) == 105L, "Panel A plot data must contain 105 rows")
assert_true(
  all(summary_data$case_id == "case3_not_core_mito") &&
    all(detail_data$case_id == "case3_not_core_mito") &&
    all(plot_data$case_id == "case3_not_core_mito"),
  "Unexpected case ID in atlas data"
)
assert_true(
  identical(sort(unique(summary_data$atlas_display_order)), seq_len(15L)),
  "Atlas display order must be the integers 1 through 15"
)
assert_true(
  all(plot_data$tile_status %in% c(
    "circle_displayed", "passing_not_circle_displayed", "no_passing_context"
  )),
  "Unsupported tile state"
)
assert_true(
  sum(detail_data$circle_displayed) == 21L &&
    sum(plot_data$circle_displayed) == 21L,
  "Circle-display flags do not reconcile to 21 contexts"
)
assert_true(
  all(
    is.na(plot_data$capped_negative_log10_aggregate_acat_q[!plot_data$passing_context])
  ),
  "Nonpassing tiles contain evidence values"
)
assert_true(
  all(
    plot_data$capped_negative_log10_aggregate_acat_q[plot_data$passing_context] <=
      evidence_cap + 1e-12
  ),
  "A capped evidence value exceeds the declared cap"
)

summary_data <- summary_data[order(summary_data$atlas_display_order), , drop = FALSE]
detail_data <- detail_data[
  order(detail_data$atlas_display_order, detail_data$network_order),
  ,
  drop = FALSE
]
plot_data <- plot_data[
  order(plot_data$atlas_display_order, plot_data$network_order),
  ,
  drop = FALSE
]

cividis_palette <- grDevices::hcl.colors(256L, palette = "cividis")
evidence_color <- function(value) {
  if (is.na(value)) return("#F2F2F2")
  position <- 1L + round(255 * max(0, min(1, value / evidence_cap)))
  cividis_palette[[position]]
}

contrast_text_color <- function(background) {
  rgb <- grDevices::col2rgb(background) / 255
  luminance <- 0.2126 * rgb[[1L]] + 0.7152 * rgb[[2L]] + 0.0722 * rgb[[3L]]
  if (luminance < 0.48) "white" else text_dark
}

network_shapes <- c(
  Astrocytes = 0,
  Excitatory_neurons = 1,
  Inhibitory_neurons = 2,
  Microglia = 5,
  OPCs = 6,
  Oligodendrocytes = 3,
  Vasculature_cells = 4
)

row_y <- function(order_value) 16 - order_value
text_dark <- "#252525"
text_mid <- "#666666"
grid_color <- "#E3E3E3"
empty_color <- "#F3F3F3"

draw_panel_a <- function() {
  graphics::par(mar = c(4.1, 6.7, 4.7, 0.4), xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0.2, 7.5), ylim = c(0.35, 15.65), xaxs = "i", yaxs = "i")

  for (row in seq_len(nrow(plot_data))) {
    record <- plot_data[row, , drop = FALSE]
    x <- record$network_order[[1L]]
    y <- row_y(record$atlas_display_order[[1L]])
    passing <- isTRUE(record$passing_context[[1L]])
    displayed <- isTRUE(record$circle_displayed[[1L]])
    fill <- if (passing) evidence_color(
      record$capped_negative_log10_aggregate_acat_q[[1L]]
    ) else empty_color
    border <- if (displayed) "#202020" else if (passing) "#666666" else "#D8D8D8"
    line_type <- if (passing && !displayed) 2L else 1L
    line_width <- if (displayed) 1.25 else 0.75
    graphics::rect(
      x - 0.43, y - 0.34, x + 0.43, y + 0.34,
      col = fill, border = border, lty = line_type, lwd = line_width
    )
    if (passing) {
      rank_color <- contrast_text_color(fill)
      graphics::text(
        x, y, labels = record$within_case_rank[[1L]],
        cex = 0.70, font = 2, col = rank_color
      )
    }
  }

  gene_y <- row_y(summary_data$atlas_display_order)
  graphics::axis(
    2, at = gene_y, labels = summary_data$current_symbol,
    las = 1, tick = FALSE, line = -0.15, cex.axis = 0.80, font = 2,
    col.axis = text_dark
  )
  extended <- summary_data$extended_reference_member
  if (any(extended)) {
    graphics::points(
      rep(0.31, sum(extended)), gene_y[extended],
      pch = 23, bg = "#111111", col = "#111111", cex = 0.72
    )
  }

  graphics::par(xpd = NA)
  for (network_index in seq_along(phase18_network_order)) {
    network <- phase18_network_order[[network_index]]
    graphics::segments(
      network_index - 0.43, 15.50, network_index + 0.43, 15.50,
      col = phase12_network_colors[[network]], lwd = 4.0
    )
    graphics::text(
      network_index - 0.03, 15.68,
      labels = phase12_network_labels[[network]],
      srt = 47, adj = c(0, 0.5), cex = 0.68, font = 2,
      col = text_dark
    )
  }

  graphics::mtext("A", side = 3, line = 3.15, adj = 0, cex = 1.10, font = 2)
  graphics::mtext(
    "Network evidence matrix",
    side = 3, line = 3.15, adj = 0.10, cex = 1.02, font = 2
  )
  graphics::mtext(
    "Tile number = within-network Case 3 rank",
    side = 3, line = 2.15, adj = 0.10, cex = 0.74, col = text_mid
  )

  legend_y <- -0.32
  legend_x <- seq(0.72, 3.12, length.out = 65L)
  for (i in seq_len(length(legend_x) - 1L)) {
    value <- (i - 1) / (length(legend_x) - 2) * evidence_cap
    graphics::rect(
      legend_x[[i]], legend_y - 0.13, legend_x[[i + 1L]], legend_y + 0.13,
      col = evidence_color(value), border = NA
    )
  }
  graphics::rect(legend_x[[1L]], legend_y - 0.13, tail(legend_x, 1L), legend_y + 0.13, border = "#555555")
  graphics::text(legend_x[[1L]], legend_y - 0.24, "0", cex = 0.70, adj = c(0, 1))
  graphics::text(tail(legend_x, 1L), legend_y - 0.24, format(evidence_cap, trim = TRUE), cex = 0.70, adj = c(1, 1))
  graphics::text(mean(range(legend_x)), legend_y + 0.28, "capped −log10(ACAT q)", cex = 0.72, font = 2)

  graphics::rect(3.52, legend_y - 0.18, 3.82, legend_y + 0.18, col = "white", border = "#202020", lwd = 1.25)
  graphics::text(3.90, legend_y, "circle top five", adj = c(0, 0.5), cex = 0.70)
  graphics::rect(5.25, legend_y - 0.18, 5.55, legend_y + 0.18, col = "white", border = "#666666", lty = 2)
  graphics::text(5.63, legend_y, "passing, below cap", adj = c(0, 0.5), cex = 0.70)
  graphics::points(3.52, legend_y - 0.62, pch = 23, bg = "#111111", cex = 0.72)
  graphics::text(3.72, legend_y - 0.62, "broader mitochondrial reference", adj = c(0, 0.5), cex = 0.70)
}

draw_measure <- function(y, start, end, value, maximum, label, color = "#252525") {
  mark_end <- start + 0.68 * (end - start)
  graphics::segments(start, y, mark_end, y, col = "#D6D6D6", lwd = 1.0)
  point_x <- start + 0.68 * (end - start) * max(0, min(1, value / maximum))
  graphics::segments(start, y, point_x, y, col = color, lwd = 2.2)
  graphics::points(point_x, y, pch = 21, bg = "white", col = color, cex = 0.64, lwd = 0.9)
  graphics::text(end, y, label, adj = c(1, 0.5), cex = 0.70, font = 2, col = text_dark)
}

draw_panel_b <- function() {
  graphics::par(mar = c(4.1, 0.55, 4.7, 0.25), xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(-0.05, 8.65), ylim = c(0.35, 15.65), xaxs = "i", yaxs = "i")
  for (y in seq_len(15L)) {
    graphics::segments(-0.05, y, 8.65, y, col = grid_color, lwd = 0.45)
  }

  tracks <- list(
    networks = c(0.00, 0.95),
    fine = c(1.12, 2.25),
    recurrence = c(2.43, 4.05),
    coverage = c(4.23, 5.85),
    groups = c(6.03, 7.15),
    directions = c(7.33, 8.55)
  )
  fine_max <- max(summary_data$unique_supporting_fine_cell_type_count)
  for (index in seq_len(nrow(summary_data))) {
    row <- summary_data[index, , drop = FALSE]
    y <- row_y(row$atlas_display_order[[1L]])
    draw_measure(y, tracks$networks[[1L]], tracks$networks[[2L]], row$passing_broad_network_count[[1L]], 7, as.character(row$passing_broad_network_count[[1L]]))
    draw_measure(y, tracks$fine[[1L]], tracks$fine[[2L]], row$unique_supporting_fine_cell_type_count[[1L]], fine_max, as.character(row$unique_supporting_fine_cell_type_count[[1L]]))
    draw_measure(
      y, tracks$recurrence[[1L]], tracks$recurrence[[2L]],
      row$query_recurrence_fraction[[1L]], 1,
      paste0(row$conservative_supporting_query_count[[1L]], "/", row$usable_query_count[[1L]])
    )
    draw_measure(
      y, tracks$coverage[[1L]], tracks$coverage[[2L]],
      row$query_coverage_fraction[[1L]], 1,
      paste0(row$usable_query_count[[1L]], "/", row$eligible_query_count[[1L]])
    )
    draw_measure(y, tracks$groups[[1L]], tracks$groups[[2L]], row$supporting_group_count[[1L]], 6, as.character(row$supporting_group_count[[1L]]))
    draw_measure(y, tracks$directions[[1L]], tracks$directions[[2L]], row$supporting_direction_count[[1L]], 2, as.character(row$supporting_direction_count[[1L]]))
  }

  headers <- c(
    "Broad\nnetworks\n(max 7)",
    paste0("Fine cell\ntypes\n(max ", fine_max, ")"),
    "Supporting /\nusable queries\n(fraction)",
    "Usable /\neligible queries\n(fraction)",
    "Sex/APOE\ngroups\n(max 6)",
    "AD\ndirections\n(max 2)"
  )
  centers <- vapply(tracks, mean, numeric(1L))
  graphics::par(xpd = NA)
  graphics::text(centers, rep(15.77, length(centers)), headers, cex = 0.70, font = 2, adj = c(0.5, 0))
  graphics::mtext("B", side = 3, line = 3.15, adj = 0, cex = 1.10, font = 2)
  graphics::mtext(
    "Breadth, recurrence and coverage",
    side = 3, line = 3.15, adj = 0.10, cex = 1.02, font = 2
  )
  graphics::mtext(
    "Counts are restricted to each gene's passing Case 3 contexts",
    side = 3, line = 2.15, adj = 0.10, cex = 0.74, col = text_mid
  )
  graphics::mtext(
    "Points/bars show the fraction or count; bold labels preserve raw numerators and denominators.",
    side = 1, line = 2.45, adj = 0, cex = 0.70, col = text_mid
  )
}

draw_panel_c <- function() {
  graphics::par(mar = c(4.1, 0.55, 4.7, 0.8), xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(-0.03, 3.45), ylim = c(0.35, 15.65), xaxs = "i", yaxs = "i")
  for (y in seq_len(15L)) {
    graphics::segments(-0.03, y, 3.45, y, col = grid_color, lwd = 0.45)
  }

  retention_start <- 0.04
  retention_end <- 1.22
  degree_start <- 1.75
  degree_end <- 3.30
  degree_cap <- 2.1
  graphics::segments(retention_start, 0.42, retention_start, 15.48, col = "#BDBDBD")
  graphics::segments(retention_end, 0.42, retention_end, 15.48, col = "#BDBDBD")
  graphics::segments(degree_start, 0.42, degree_start, 15.48, col = "#BDBDBD")
  graphics::segments(degree_end, 0.42, degree_end, 15.48, col = "#BDBDBD")
  retention_reference <- retention_start + 0.8 * (retention_end - retention_start)
  degree_reference <- degree_start + (-log10(0.05) / degree_cap) * (degree_end - degree_start)
  graphics::segments(retention_reference, 0.42, retention_reference, 15.48, col = "#969696", lty = 3, lwd = 0.8)
  graphics::segments(degree_reference, 0.42, degree_reference, 15.48, col = "#969696", lty = 3, lwd = 0.8)

  for (index in seq_len(nrow(detail_data))) {
    row <- detail_data[index, , drop = FALSE]
    network <- row$broad_network[[1L]]
    jitter <- (row$network_order[[1L]] - 4) * 0.045
    y <- row_y(row$atlas_display_order[[1L]]) + jitter
    stability_assessable <- isTRUE(row$stability_assessable[[1L]])
    retention_x <- if (stability_assessable) {
      retention_start + row$stability_candidate_fraction[[1L]] *
        (retention_end - retention_start)
    } else {
      retention_start
    }
    degree_score <- min(-log10(row$degree_matched_empirical_tail_p[[1L]]), degree_cap)
    degree_x <- degree_start + degree_score / degree_cap * (degree_end - degree_start)
    complete <- isTRUE(row$degree_diagnostic_complete[[1L]])
    fill <- if (complete) phase12_network_colors[[network]] else "white"
    if (stability_assessable) {
      graphics::points(retention_x, y, pch = 21, bg = fill, col = "#303030", cex = 0.76, lwd = 0.65)
      graphics::points(retention_x, y, pch = network_shapes[[network]], col = "#202020", cex = 0.34, lwd = 0.70)
    } else {
      graphics::points(retention_x, y, pch = 21, bg = "white", col = phase12_network_colors[[network]], cex = 0.76, lwd = 0.9)
      graphics::points(retention_x, y, pch = 4, col = "#202020", cex = 0.42, lwd = 0.8)
    }
    graphics::points(degree_x, y, pch = 21, bg = fill, col = "#303030", cex = 0.76, lwd = 0.65)
    graphics::points(degree_x, y, pch = network_shapes[[network]], col = "#202020", cex = 0.34, lwd = 0.70)
  }

  tick_cex <- 0.70
  for (value in c(0, 0.5, 1)) {
    x <- retention_start + value * (retention_end - retention_start)
    graphics::segments(x, 0.35, x, 0.20, col = text_mid)
    graphics::text(x, 0.02, format(value, trim = TRUE), cex = tick_cex)
  }
  for (value in c(0, 1, 2)) {
    x <- degree_start + value / degree_cap * (degree_end - degree_start)
    graphics::segments(x, 0.35, x, 0.20, col = text_mid)
    graphics::text(x, 0.02, format(value, trim = TRUE), cex = tick_cex)
  }
  graphics::par(xpd = NA)
  graphics::text(mean(c(retention_start, retention_end)), 15.77, "Candidate\nretention\n(0–1)", cex = 0.70, font = 2, adj = c(0.5, 0))
  graphics::text(mean(c(degree_start, degree_end)), 15.77, "Degree-matched\n−log10(empirical P)\n(cap 2.1)", cex = 0.70, font = 2, adj = c(0.5, 0))
  graphics::mtext("C", side = 3, line = 3.15, adj = 0, cex = 1.10, font = 2)
  graphics::mtext(
    "Network robustness",
    side = 3, line = 3.15, adj = 0.20, cex = 0.96, font = 2
  )
  graphics::mtext("Network-specific sensitivity diagnostics", side = 3, line = 2.15, adj = 0.20, cex = 0.70, col = text_mid)
  graphics::points(2.16, -1.53, pch = 21, bg = "white", col = "#555555", cex = 0.74)
  graphics::points(2.16, -1.53, pch = 4, col = "#202020", cex = 0.42)
  graphics::text(2.28, -1.53, "stability not assessable", adj = c(0, 0.5), cex = 0.70)

  legend_y <- -0.58
  legend_x <- c(0.08, 1.18, 2.28, 0.08, 1.18, 2.28, 0.08)
  legend_row <- c(0, 0, 0, -0.48, -0.48, -0.48, -0.96)
  for (index in seq_along(phase18_network_order)) {
    network <- phase18_network_order[[index]]
    x <- legend_x[[index]]
    y <- legend_y + legend_row[[index]]
    graphics::points(x, y, pch = 21, bg = phase12_network_colors[[network]], col = "#303030", cex = 0.74)
    graphics::points(x, y, pch = network_shapes[[network]], col = "#202020", cex = 0.32)
    graphics::text(x + 0.12, y, phase12_network_labels[[network]], adj = c(0, 0.5), cex = 0.70)
  }
}

draw_atlas <- function() {
  graphics::layout(matrix(c(1L, 2L, 3L), nrow = 1L), widths = c(4.25, 4.75, 3.00))
  graphics::par(
    oma = c(3.0, 0.4, 4.2, 0.2),
    family = "sans", fg = text_dark, col.axis = text_dark,
    col.lab = text_dark, col.main = text_dark, lend = "round"
  )
  draw_panel_a()
  draw_panel_b()
  draw_panel_c()
  graphics::mtext(
    "Breadth and reproducibility of Case 3 key-driver candidates",
    side = 3, outer = TRUE, line = 2.45, adj = 0.02,
    cex = 1.35, font = 2, col = text_dark
  )
  graphics::mtext(
    "Drivers outside the 1,136-gene core MitoCarta inventory",
    side = 3, outer = TRUE, line = 1.25, adj = 0.02,
    cex = 0.95, col = text_mid
  )
  graphics::mtext(
    "15 circle genes • 21 circle-displayed contexts • 22 total passing contexts",
    side = 3, outer = TRUE, line = 0.15, adj = 0.02,
    cex = 0.74, col = text_mid
  )
}

basename_value <- "phase18_case3_evidence_atlas"
svg_path <- file.path(output_dir, paste0(basename_value, ".svg"))
pdf_path <- file.path(output_dir, paste0(basename_value, ".pdf"))
png_path <- file.path(output_dir, paste0(basename_value, ".png"))

message("Writing ", svg_path)
render_atomic(
  svg_path,
  function(path) open_svg_device(path, figure_width_inches, figure_height_inches),
  draw_atlas
)
message("Writing ", pdf_path)
render_atomic(
  pdf_path,
  function(path) open_pdf_device(path, figure_width_inches, figure_height_inches),
  draw_atlas
)
message("Writing ", png_path)
render_atomic(
  png_path,
  function(path) open_png_device(
    path, figure_width_inches, figure_height_inches, dpi = png_dpi
  ),
  draw_atlas
)

message(
  "Rendered Case 3 evidence atlas: ", nrow(summary_data), " genes; ",
  nrow(detail_data), " passing contexts; ", nrow(plot_data), " matrix cells"
)
