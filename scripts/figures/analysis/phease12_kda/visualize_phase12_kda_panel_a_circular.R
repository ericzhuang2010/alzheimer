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
    "visualize_phase12_kda_panel_a_circular.R ",
    "[--input-dir DIR] [--output-dir DIR] [--basename NAME] ",
    "[--top-per-network N] [--minimum-ranking-coverage FRACTION]\n",
    sep = ""
  )
}

args <- parse_value_args(
  commandArgs(trailingOnly = TRUE),
  defaults = list(
    input_dir = "results/figures/analysis/phase12_kda",
    output_dir = "results/figures/analysis/phase12_kda",
    basename = "phase12_kda_panel_a_circular",
    top_per_network = "3",
    minimum_ranking_coverage = "0.80"
  ),
  allowed = c(
    "--input-dir", "--output-dir", "--basename", "--top-per-network",
    "--minimum-ranking-coverage"
  )
)
if (isTRUE(attr(args, "help"))) {
  usage()
  quit(status = 0L)
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
top_per_network <- suppressWarnings(as.integer(args$top_per_network))
minimum_ranking_coverage <- suppressWarnings(as.numeric(args$minimum_ranking_coverage))
assert_true(
  length(top_per_network) == 1L && is.finite(top_per_network) &&
    top_per_network >= 1L && top_per_network <= 5L,
  "--top-per-network must be an integer from 1 to 5"
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

summary_path <- file.path(input_dir, "phase12_kda_mean_of_log_summary.tsv")
checks_path <- file.path(input_dir, "phase12_kda_figure_data_checks.tsv")
summary <- read_tsv(summary_path)
checks <- read_tsv(checks_path)
require_columns(
  summary,
  c(
    "broad_network", "key_driver", "mean_of_log_score", "ranking_runs",
    "eligible_directional_runs", "ranking_coverage_fraction",
    "primary_directional_significant_runs",
    "primary_directional_recurrence_fraction", "mtDNA_encoded"
  ),
  basename(summary_path)
)
assert_true(nrow(checks) > 0L && all(checks$passed), "Prepared figure-data checks did not all pass")

selected_parts <- lapply(phase12_network_order, function(network) {
  x <- summary[
    summary$broad_network == network &
      summary$ranking_coverage_fraction >= minimum_ranking_coverage,
    ,
    drop = FALSE
  ]
  assert_true(
    nrow(x) >= top_per_network,
    paste("Fewer than", top_per_network, "coverage-qualified candidates in", network)
  )
  maximum <- max(x$mean_of_log_score, na.rm = TRUE)
  x$mean_of_log_score_standardized <- if (maximum > 0) x$mean_of_log_score / maximum else 0
  x <- x[
    order(
      -x$mean_of_log_score_standardized,
      -x$ranking_runs,
      -x$primary_directional_recurrence_fraction,
      x$key_driver
    ),
    ,
    drop = FALSE
  ]
  x <- utils::head(x, top_per_network)
  x$driver_display_order_within_network <- seq_len(nrow(x))
  x
})
selected <- do.call(rbind, selected_parts)
rownames(selected) <- NULL
selected$network_display_order <- match(selected$broad_network, phase12_network_order)
selected$network_color <- unname(phase12_network_colors[selected$broad_network])
selected$display_network <- unname(phase12_network_labels[selected$broad_network])
selected$selection_rule <- paste0(
  "Top ", top_per_network,
  " MeanOfLog candidates per network with ranking coverage >= ",
  format(minimum_ranking_coverage, trim = TRUE)
)
selected_count <- table(selected$key_driver)
selected$selected_network_count <- as.integer(selected_count[selected$key_driver])
selected <- selected[
  order(selected$network_display_order, selected$driver_display_order_within_network),
  ,
  drop = FALSE
]

network_gap <- 6
driver_gap <- 1
number_networks <- length(phase12_network_order)
number_drivers <- nrow(selected)
total_gap <- number_networks * network_gap +
  (number_drivers - number_networks) * driver_gap
sector_width <- (360 - total_gap) / number_drivers
cursor <- 90
angle_rows <- vector("list", number_drivers)
for (index in seq_len(number_drivers)) {
  start <- cursor
  end <- start - sector_width
  angle_rows[[index]] <- data.frame(
    sector_start_degrees = start,
    sector_end_degrees = end,
    sector_mid_degrees = (start + end) / 2,
    stringsAsFactors = FALSE
  )
  same_network_next <-
    index < number_drivers &&
    selected$broad_network[[index + 1L]] == selected$broad_network[[index]]
  cursor <- end - if (same_network_next) driver_gap else network_gap
}
angles <- do.call(rbind, angle_rows)
selected <- cbind(selected, angles)

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

draw_panel_a <- function() {
  graphics::par(
    mar = c(1.8, 1.0, 4.6, 1.0),
    xaxs = "i", yaxs = "i", family = "sans", xpd = NA
  )
  graphics::plot.new()
  graphics::plot.window(xlim = c(-1.48, 1.48), ylim = c(-1.48, 1.48), asp = 1)

  score_inner <- 0.62
  score_height <- 0.32
  for (index in seq_len(nrow(selected))) {
    annular_sector(
      selected$sector_start_degrees[[index]],
      selected$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height,
      fill = "#F1F3F5",
      border = "white",
      line_width = 0.6
    )
  }
  for (reference in c(0.25, 0.50, 0.75, 1.00)) {
    circle_line(
      score_inner + score_height * reference,
      color = if (reference == 1) "#AEB6BF" else "#CBD0D5",
      line_width = if (reference == 1) 0.65 else 0.4,
      line_type = if (reference == 1) 1 else 3
    )
  }

  recurring <- names(selected_count)[selected_count > 1L]
  for (gene in recurring) {
    indices <- which(selected$key_driver == gene)
    anchor <- indices[[which.max(selected$mean_of_log_score_standardized[indices])]]
    for (other in setdiff(indices, anchor)) {
      bezier_link(
        selected$sector_mid_degrees[[anchor]],
        selected$sector_mid_degrees[[other]],
        color = rgba("#666666", 0.22)
      )
    }
  }

  for (index in seq_len(nrow(selected))) {
    annular_sector(
      selected$sector_start_degrees[[index]],
      selected$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height * selected$mean_of_log_score_standardized[[index]],
      fill = "#344E73",
      border = "white",
      line_width = 0.55
    )
    annular_sector(
      selected$sector_start_degrees[[index]],
      selected$sector_end_degrees[[index]],
      0.98,
      1.07,
      fill = selected$network_color[[index]],
      border = "white",
      line_width = 0.8
    )
  }

  for (index in seq_len(nrow(selected))) {
    angle <- selected$sector_mid_degrees[[index]]
    label_radius <- 1.145
    color <- if (selected$mtDNA_encoded[[index]]) "#777777" else "#202020"
    graphics::text(
      label_radius * cos(angle * pi / 180),
      label_radius * sin(angle * pi / 180),
      labels = selected$key_driver[[index]],
      srt = upright_rotation(angle),
      cex = 0.72,
      col = color,
      font = if (selected$mtDNA_encoded[[index]]) 1 else 2
    )
  }

  for (network in phase12_network_order) {
    indices <- which(selected$broad_network == network)
    mid <- mean(c(
      selected$sector_start_degrees[[min(indices)]],
      selected$sector_end_degrees[[max(indices)]]
    ))
    radius <- 1.34
    graphics::text(
      radius * cos(mid * pi / 180),
      radius * sin(mid * pi / 180),
      labels = phase12_network_labels[[network]],
      srt = upright_rotation(mid),
      cex = 0.70,
      col = "#222222",
      font = 2
    )
  }

  graphics::symbols(
    0, 0, circles = 0.405, inches = FALSE, add = TRUE,
    fg = "#B9C0C8", bg = "white"
  )
  graphics::text(0, 0.245, "Legend", cex = 0.72, font = 2, col = "#222222")
  graphics::rect(-0.31, 0.135, -0.23, 0.175, col = phase12_network_colors[[1L]], border = NA)
  graphics::text(-0.19, 0.155, "broad network", adj = c(0, 0.5), cex = 0.52, col = "#333333")
  graphics::rect(-0.31, 0.045, -0.23, 0.085, col = "#344E73", border = NA)
  graphics::text(-0.19, 0.065, "standardized MeanOfLog", adj = c(0, 0.5), cex = 0.52, col = "#333333")
  graphics::segments(-0.31, -0.025, -0.23, -0.025, col = rgba("#666666", 0.55), lwd = 1)
  graphics::text(-0.19, -0.025, "same driver across networks", adj = c(0, 0.5), cex = 0.52, col = "#333333")
  graphics::points(-0.27, -0.115, pch = 16, col = "#777777", cex = 0.55)
  graphics::text(-0.19, -0.115, "mtDNA-encoded sentinel candidate", adj = c(0, 0.5), cex = 0.48, col = "#333333")
  graphics::text(0, -0.245, "Score range 0-1", cex = 0.52, col = "#666666")

  graphics::title(
    main = "Recurrent mitochondrial KDA evidence across brain cell networks",
    cex.main = 1.12,
    font.main = 2,
    col.main = "#202020",
    line = 2.4
  )
  graphics::mtext(
    paste0(
      "Top ", top_per_network,
      " coverage-qualified drivers per network, ranked by mean -log10(KDA P)"
    ),
    side = 3, line = 0.9, cex = 0.76, col = "#555555"
  )
  graphics::text(
    0, -1.43,
    "Primary AD-up and AD-down runs only; CAMs and T cells had no eligible KDA runs",
    cex = 0.61,
    col = "#606060"
  )
}

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
table_path <- file.path(output_dir, paste0(args$basename, "_plotted_data.tsv"))
svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
pdf_path <- file.path(output_dir, paste0(args$basename, ".pdf"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))
log_path <- file.path(output_dir, paste0(args$basename, "_generation_log.tsv"))

atomic_write_table(selected, table_path)
message("Writing ", svg_path)
render_atomic(svg_path, function(path) open_svg_device(path, 7.1, 7.1), draw_panel_a)
message("Writing ", pdf_path)
render_atomic(pdf_path, function(path) open_pdf_device(path, 7.1, 7.1), draw_panel_a)
message("Writing ", png_path)
render_atomic(png_path, function(path) open_png_device(path, 7.1, 7.1, 450), draw_panel_a)
atomic_write_table(
  data.frame(
    schema_version = "phase12_kda_figure_generation_log_v1",
    generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    figure_script = "scripts/figures/analysis/phease12_kda/visualize_phase12_kda_panel_a_circular.R",
    input_summary = summary_path,
    input_checks = checks_path,
    figure_basename = args$basename,
    selection_rule = unique(selected$selection_rule),
    plotted_rows = nrow(selected),
    unique_drivers = length(unique(selected$key_driver)),
    width_inches = 7.1,
    height_inches = 7.1,
    png_dpi = 450,
    data_checks_passed = all(checks$passed),
    stringsAsFactors = FALSE
  ),
  log_path
)

message(
  "Figure A complete: ", nrow(selected), " network-driver sectors; ",
  length(unique(selected$key_driver)), " unique drivers"
)
