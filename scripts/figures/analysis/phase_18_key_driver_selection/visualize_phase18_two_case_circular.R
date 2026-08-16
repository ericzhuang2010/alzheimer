#!/usr/bin/env Rscript

# Render the two Phase 18 driver-class circular figures directly from the
# canonical all-tested call_key_drivers table.

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
    "phase_18_key_driver_selection/visualize_phase18_two_case_circular.R ",
    "[--input FILE] [--output-dir DIR] [--top-per-network N] ",
    "[--evidence-cap VALUE] [--png-dpi DPI] [--width-inches VALUE] ",
    "[--height-inches VALUE]\n",
    sep = ""
  )
}

cli_args <- commandArgs(trailingOnly = TRUE)
args <- parse_value_args(
  cli_args,
  defaults = list(
    input = paste0(
      "results/minerva_production/18_key_driver_selection/",
      "call_key_driver_returns.tsv"
    ),
    output_dir = paste0(
      "results/figures/analysis/phase_18_key_driver_selection/",
      "two_case_circular"
    ),
    top_per_network = "5",
    evidence_cap = "15",
    png_dpi = "450",
    width_inches = "12",
    height_inches = "7.2"
  ),
  allowed = c(
    "--input", "--output-dir", "--top-per-network", "--evidence-cap",
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
  "The Phase 18 display limit is exactly five"
)
assert_true(
  length(evidence_cap) == 1L && is.finite(evidence_cap) && evidence_cap > 0,
  "--evidence-cap must be positive"
)
assert_true(
  length(png_dpi) == 1L && is.finite(png_dpi) && png_dpi >= 300L,
  "--png-dpi must be at least 300"
)
assert_true(
  length(figure_width_inches) == 1L && is.finite(figure_width_inches) &&
    figure_width_inches > figure_height_inches &&
    length(figure_height_inches) == 1L && is.finite(figure_height_inches) &&
    figure_height_inches > 0,
  "The figure must be wider than it is tall"
)
assert_true(capabilities("cairo"), "This R installation lacks Cairo support")

project_root <- normalizePath(getwd(), mustWork = TRUE)
input_path <- absolute_path(args$input, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
input_path <- normalizePath(input_path, mustWork = TRUE)

phase18_network_order <- phase12_network_order
class_order <- c("mt_driver", "non_mt_driver")
class_labels <- c(
  mt_driver = "MT driver",
  non_mt_driver = "non-MT driver"
)
class_titles <- c(
  mt_driver = "MT drivers",
  non_mt_driver = "Non-MT drivers"
)
class_basenames <- c(
  mt_driver = "phase18_mt_driver_circular",
  non_mt_driver = "phase18_non_mt_driver_circular"
)

message("Reading ", input_path)
returns <- read_tsv(input_path)
required_columns <- c(
  "schema_version", "kda_run_id", "broad_network", "key_driver",
  "case_order", "case_id", "case_label", "is_core_mito",
  "is_mtdna_gene", "extended_reference_member", "coverage_fraction",
  "conservative_support_count", "aggregate_acat_p", "aggregate_acat_q",
  "terminal_candidate_status", "within_case_rank", "top5_display",
  "evidence_tier"
)
require_columns(returns, required_columns, basename(input_path))

as_flag <- function(x) {
  if (is.logical(x)) return(x)
  toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

assert_true(
  nrow(returns) == 95557L,
  paste("Expected 95,557 tested gene-run rows, found", nrow(returns))
)
assert_true(
  ncol(returns) == 104L,
  paste("Expected 104 columns, found", ncol(returns))
)
assert_true(
  all(returns$schema_version == "phase18_call_key_driver_returns_v1"),
  "The input does not use phase18_call_key_driver_returns_v1"
)
assert_true(
  length(unique(returns$kda_run_id)) == 161L,
  "The input does not contain all 161 included KDA calls"
)
run_gene_key <- paste(returns$kda_run_id, returns$key_driver, sep = "\r")
assert_true(!anyDuplicated(run_gene_key), "Duplicate kda_run_id + key_driver rows")
assert_true(
  setequal(unique(returns$case_id), class_order),
  "The input does not contain exactly the two driver classes"
)
assert_true(
  all(unique(returns$broad_network) %in% phase18_network_order),
  "The input contains an unsupported broad network"
)

aggregate_columns <- c(
  "broad_network", "key_driver", "case_order", "case_id", "case_label",
  "is_core_mito", "is_mtdna_gene", "extended_reference_member",
  "coverage_fraction", "conservative_support_count", "aggregate_acat_p",
  "aggregate_acat_q", "terminal_candidate_status", "within_case_rank",
  "top5_display", "evidence_tier"
)
aggregate_key <- paste(
  returns$broad_network, returns$key_driver, returns$case_id,
  sep = "\r"
)
first_index <- !duplicated(aggregate_key)
aggregates <- returns[first_index, aggregate_columns, drop = FALSE]
aggregate_unique_key <- aggregate_key[first_index]
aggregate_match <- match(aggregate_key, aggregate_unique_key)
same_value <- function(observed, expected) {
  all(
    (is.na(observed) & is.na(expected)) |
      (!is.na(observed) & !is.na(expected) & observed == expected)
  )
}
for (column in setdiff(aggregate_columns, c("broad_network", "key_driver", "case_id"))) {
  assert_true(
    same_value(returns[[column]], aggregates[[column]][aggregate_match]),
    paste("Aggregate field varies within candidate unit:", column)
  )
}
aggregates$top5_display <- as_flag(aggregates$top5_display)
aggregates$is_core_mito <- as_flag(aggregates$is_core_mito)
aggregates$is_mtdna_gene <- as_flag(aggregates$is_mtdna_gene)
aggregates$extended_reference_member <- as_flag(
  aggregates$extended_reference_member
)

assert_true(nrow(aggregates) == 10433L, "Unexpected represented aggregate count")
candidates <- aggregates[
  aggregates$terminal_candidate_status == "driver_candidate",
  ,
  drop = FALSE
]
displayed <- aggregates[aggregates$top5_display, , drop = FALSE]
assert_true(nrow(candidates) == 78L, "Expected 78 driver-candidate records")
assert_true(nrow(displayed) == 47L, "Expected 47 top-five display records")
assert_true(
  identical(
    as.integer(table(factor(displayed$case_id, levels = class_order))),
    c(26L, 21L)
  ),
  "Displayed class counts do not reconcile to 26 MT and 21 non-MT records"
)
assert_true(
  all(
    displayed$terminal_candidate_status == "driver_candidate" &
      displayed$coverage_fraction >= 0.80 &
      displayed$conservative_support_count >= 1L &
      displayed$aggregate_acat_q <= 0.05 &
      displayed$within_case_rank >= 1L &
      displayed$within_case_rank <= 5L
  ),
  "A displayed gene does not pass the Phase 18 candidate and rank rules"
)
assert_true(
  all(aggregates$is_core_mito[aggregates$case_id == "mt_driver"]) &&
    all(!aggregates$is_core_mito[aggregates$case_id == "non_mt_driver"]),
  "Driver-class assignment does not match core mitochondrial annotation"
)

for (network in phase18_network_order) {
  for (class_id in class_order) {
    group <- candidates[
      candidates$broad_network == network & candidates$case_id == class_id,
      ,
      drop = FALSE
    ]
    if (!nrow(group)) next
    group <- group[
      order(group$aggregate_acat_q, group$aggregate_acat_p, group$key_driver),
      ,
      drop = FALSE
    ]
    assert_true(
      identical(as.integer(group$within_case_rank), seq_len(nrow(group))),
      paste("Stored rank differs from the Phase 18 ordering:", network, class_id)
    )
    assert_true(
      identical(group$top5_display, seq_len(nrow(group)) <= top_per_network),
      paste("Stored top-five flag differs from rank:", network, class_id)
    )
  }
}

sha256_file <- function(path) {
  output <- system2(
    "/usr/bin/shasum",
    c("-a", "256", shQuote(path)),
    stdout = TRUE,
    stderr = TRUE
  )
  status_code <- attr(output, "status") %||% 0L
  assert_true(status_code == 0L && length(output) >= 1L, "Could not hash input")
  strsplit(trimws(output[[1L]]), "[[:space:]]+")[[1L]][[1L]]
}
source_sha256 <- sha256_file(input_path)

network_gap <- 6
slot_gap <- 1
total_slots <- length(phase18_network_order) * top_per_network
total_gap <- length(phase18_network_order) * network_gap +
  (total_slots - length(phase18_network_order)) * slot_gap
slot_width <- (360 - total_gap) / total_slots
cursor <- 90
geometry_rows <- list()
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

plot_rows <- list()
plot_index <- 1L
for (class_id in class_order) {
  for (geometry_index in seq_len(nrow(geometry))) {
    geometry_row <- geometry[geometry_index, , drop = FALSE]
    selected_row <- displayed[
      displayed$case_id == class_id &
        displayed$broad_network == geometry_row$broad_network &
        displayed$within_case_rank == geometry_row$slot_rank,
      ,
      drop = FALSE
    ]
    passing_count <- sum(
      candidates$case_id == class_id &
        candidates$broad_network == geometry_row$broad_network
    )
    assert_true(nrow(selected_row) <= 1L, "Duplicate displayed rank in one list")
    occupied <- nrow(selected_row) == 1L
    plot_rows[[plot_index]] <- data.frame(
      schema_version = "phase18_two_case_circular_plot_data_v1",
      class_order = match(class_id, class_order),
      case_id = class_id,
      case_label = class_labels[[class_id]],
      broad_network = geometry_row$broad_network,
      network_display_order = geometry_row$network_display_order,
      display_network = unname(phase12_network_labels[geometry_row$broad_network]),
      network_color = unname(phase12_network_colors[geometry_row$broad_network]),
      slot_rank = geometry_row$slot_rank,
      slot_status = if (occupied) {
        "ranked_candidate"
      } else if (passing_count == 0L) {
        "no_passing_candidate_slot"
      } else {
        "unused_display_slot"
      },
      total_passing_candidate_count = passing_count,
      displayed_candidate_count = min(passing_count, top_per_network),
      current_symbol = if (occupied) selected_row$key_driver[[1L]] else NA_character_,
      display_rank = if (occupied) selected_row$within_case_rank[[1L]] else NA_integer_,
      is_core_mito = if (occupied) selected_row$is_core_mito[[1L]] else NA,
      is_mtdna_gene = if (occupied) selected_row$is_mtdna_gene[[1L]] else NA,
      extended_reference_member = if (occupied) {
        selected_row$extended_reference_member[[1L]]
      } else {
        NA
      },
      coverage_fraction = if (occupied) {
        selected_row$coverage_fraction[[1L]]
      } else {
        NA_real_
      },
      conservative_support_count = if (occupied) {
        selected_row$conservative_support_count[[1L]]
      } else {
        NA_integer_
      },
      aggregate_acat_p = if (occupied) {
        selected_row$aggregate_acat_p[[1L]]
      } else {
        NA_real_
      },
      aggregate_acat_q = if (occupied) {
        selected_row$aggregate_acat_q[[1L]]
      } else {
        NA_real_
      },
      negative_log10_acat_q = if (occupied) {
        -log10(max(selected_row$aggregate_acat_q[[1L]], .Machine$double.xmin))
      } else {
        NA_real_
      },
      capped_negative_log10_acat_q = NA_real_,
      display_score = NA_real_,
      evidence_tier = if (occupied) selected_row$evidence_tier[[1L]] else NA_character_,
      selected_network_count_within_class = NA_integer_,
      sector_start_degrees = geometry_row$sector_start_degrees,
      sector_end_degrees = geometry_row$sector_end_degrees,
      sector_mid_degrees = geometry_row$sector_mid_degrees,
      source_call_key_driver_returns_sha256 = source_sha256,
      stringsAsFactors = FALSE
    )
    plot_index <- plot_index + 1L
  }
}
plot_data <- do.call(rbind, plot_rows)
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
plot_data$selected_network_count_within_class[occupied] <- as.integer(
  selection_counts[
    paste(
      plot_data$case_id[occupied], plot_data$current_symbol[occupied],
      sep = "\r"
    )
  ]
)
assert_true(
  nrow(plot_data) == 70L && all(table(plot_data$case_id) == 35L),
  "Fixed-slot plot data must contain 35 rows for each driver class"
)

link_rows <- list()
link_index <- 1L
for (class_id in class_order) {
  class_rows <- plot_data[plot_data$case_id == class_id & occupied, , drop = FALSE]
  repeated_genes <- names(which(table(class_rows$current_symbol) > 1L))
  for (gene in sort(repeated_genes)) {
    gene_rows <- class_rows[class_rows$current_symbol == gene, , drop = FALSE]
    anchor_index <- which.max(gene_rows$negative_log10_acat_q)
    target_indices <- setdiff(seq_len(nrow(gene_rows)), anchor_index)
    for (target_index in target_indices) {
      link_rows[[link_index]] <- data.frame(
        schema_version = "phase18_two_case_circular_links_v1",
        case_id = class_id,
        current_symbol = gene,
        selected_network_count_within_class = nrow(gene_rows),
        anchor_broad_network = gene_rows$broad_network[[anchor_index]],
        target_broad_network = gene_rows$broad_network[[target_index]],
        anchor_sector_mid_degrees = gene_rows$sector_mid_degrees[[anchor_index]],
        target_sector_mid_degrees = gene_rows$sector_mid_degrees[[target_index]],
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
    current_symbol = character(), selected_network_count_within_class = integer(),
    anchor_broad_network = character(), target_broad_network = character(),
    anchor_sector_mid_degrees = numeric(), target_sector_mid_degrees = numeric(),
    link_rule = character(), stringsAsFactors = FALSE
  )
}

if (dir.exists(output_dir) || file.exists(output_dir)) {
  stop("Output path already exists; refusing to overwrite: ", output_dir, call. = FALSE)
}
output_parent <- dirname(output_dir)
dir.create(output_parent, recursive = TRUE, showWarnings = FALSE)
staging_dir <- file.path(
  output_parent,
  paste0(".", basename(output_dir), ".staging.", Sys.getpid())
)
assert_true(!file.exists(staging_dir), "Staging path already exists")
dir.create(staging_dir, recursive = FALSE, showWarnings = FALSE)
published <- FALSE
on.exit({
  if (!published && dir.exists(staging_dir)) {
    unlink(staging_dir, recursive = TRUE, force = TRUE)
  }
}, add = TRUE)

atomic_write_lines <- function(lines, path) {
  temporary <- file.path(
    dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  on.exit(if (file.exists(temporary)) unlink(temporary), add = TRUE)
  writeLines(lines, temporary, useBytes = TRUE)
  if (!file.rename(temporary, path)) {
    stop("Could not publish text artifact: ", path, call. = FALSE)
  }
  invisible(path)
}

atomic_write_table(
  plot_data,
  file.path(staging_dir, "phase18_two_case_circular_plot_data.tsv")
)
atomic_write_table(
  links,
  file.path(staging_dir, "phase18_two_case_circular_links.tsv")
)

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
  graphics::lines(points[, 1L], points[, 2L], col = color, lwd = 0.8)
}

upright_rotation <- function(angle) {
  rotation <- (angle - 90) %% 360
  if (rotation > 90 && rotation < 270) rotation <- rotation + 180
  if (rotation > 180) rotation <- rotation - 360
  rotation
}

circle_panel_fraction <- figure_height_inches / figure_width_inches

draw_legend <- function(class_id) {
  graphics::par(
    fig = c(circle_panel_fraction, 1, 0, 1),
    mar = c(0, 0, 0, 0), xaxs = "i", yaxs = "i", family = "sans",
    xpd = NA, new = TRUE
  )
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1))
  key_x <- 0.02
  key_width <- 0.055
  text_x <- 0.095
  graphics::text(
    key_x, 0.67, "Legend", adj = c(0, 0.5), cex = 1.35,
    font = 2, col = "#222222"
  )
  graphics::rect(
    key_x, 0.585, key_x + key_width, 0.62,
    col = phase12_network_colors[[1L]], border = NA
  )
  graphics::text(
    text_x, 0.602, "Broad-network band", adj = c(0, 0.5),
    cex = 1.02, col = "#333333"
  )
  graphics::rect(
    key_x, 0.515, key_x + key_width, 0.55,
    col = "#344E73", border = NA
  )
  graphics::text(
    text_x, 0.532, "Capped -log10(ACAT q)", adj = c(0, 0.5),
    cex = 1.02, col = "#333333"
  )
  graphics::segments(
    key_x, 0.465, key_x + key_width, 0.465,
    col = rgba("#666666", 0.55), lwd = 1.2
  )
  graphics::text(
    text_x, 0.465, "Same gene across networks", adj = c(0, 0.5),
    cex = 1.02, col = "#333333"
  )
  if (class_id == "mt_driver") {
    graphics::points(
      key_x + key_width / 2, 0.395, pch = 16, col = "#666666", cex = 0.8
    )
    marker_text <- "mtDNA-encoded gene"
  } else {
    graphics::points(
      key_x + key_width / 2, 0.395, pch = 5, col = "#555555",
      cex = 1.0, lwd = 1
    )
    marker_text <- "Extended mitochondrial reference"
  }
  graphics::text(
    text_x, 0.395, marker_text, adj = c(0, 0.5),
    cex = 1.02, col = "#333333"
  )
  graphics::text(
    key_x, 0.315,
    paste0("Common evidence scale: 0–", format(evidence_cap, trim = TRUE)),
    adj = c(0, 0.5), cex = 1.02, col = "#555555"
  )
  graphics::text(
    key_x, 0.255,
    "Gray slots: fewer than five passing genes",
    adj = c(0, 0.5), cex = 0.94, col = "#666666"
  )
}

draw_circle <- function(class_id) {
  class_slots <- plot_data[plot_data$case_id == class_id, , drop = FALSE]
  class_slots <- class_slots[
    order(class_slots$network_display_order, class_slots$slot_rank),
    ,
    drop = FALSE
  ]
  class_links <- links[links$case_id == class_id, , drop = FALSE]
  class_occupied <- class_slots$slot_status == "ranked_candidate"

  graphics::par(
    fig = c(0, circle_panel_fraction, 0, 1),
    mar = c(2.4, 0.8, 5.4, 0.8), xaxs = "i", yaxs = "i",
    family = "sans", xpd = NA
  )
  graphics::plot.new()
  graphics::plot.window(xlim = c(-1.68, 1.68), ylim = c(-1.68, 1.68), asp = 1)

  score_inner <- 0.62
  score_height <- 0.32
  for (index in seq_len(nrow(class_slots))) {
    annular_sector(
      class_slots$sector_start_degrees[[index]],
      class_slots$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height,
      fill = if (class_slots$slot_status[[index]] == "ranked_candidate") {
        "#F1F3F5"
      } else {
        "#E2E5E9"
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

  if (nrow(class_links)) {
    for (index in seq_len(nrow(class_links))) {
      bezier_link(
        class_links$anchor_sector_mid_degrees[[index]],
        class_links$target_sector_mid_degrees[[index]],
        color = rgba("#666666", 0.25)
      )
    }
  }

  for (index in which(class_occupied)) {
    annular_sector(
      class_slots$sector_start_degrees[[index]],
      class_slots$sector_end_degrees[[index]],
      score_inner,
      score_inner + score_height * class_slots$display_score[[index]],
      fill = "#344E73", border = "white", line_width = 0.55
    )
  }

  for (index in seq_len(nrow(class_slots))) {
    border_color <- if (class_slots$broad_network[[index]] == "Oligodendrocytes") {
      "#8E7D00"
    } else {
      "white"
    }
    annular_sector(
      class_slots$sector_start_degrees[[index]],
      class_slots$sector_end_degrees[[index]],
      0.98, 1.07,
      fill = class_slots$network_color[[index]],
      border = border_color,
      line_width = if (border_color == "white") 0.75 else 0.6
    )
  }

  for (index in which(class_occupied)) {
    angle <- class_slots$sector_mid_degrees[[index]]
    label_radius <- c(1.12, 1.23, 1.34, 1.23, 1.12)[
      class_slots$slot_rank[[index]]
    ]
    label_color <- if (isTRUE(class_slots$is_mtdna_gene[[index]])) {
      "#666666"
    } else {
      "#202020"
    }
    graphics::text(
      label_radius * cos(angle * pi / 180),
      label_radius * sin(angle * pi / 180),
      labels = class_slots$current_symbol[[index]],
      srt = upright_rotation(angle), cex = 0.72,
      col = label_color, font = 1
    )
    marker_radius <- 1.092
    if (class_id == "mt_driver" && isTRUE(class_slots$is_mtdna_gene[[index]])) {
      graphics::points(
        marker_radius * cos(angle * pi / 180),
        marker_radius * sin(angle * pi / 180),
        pch = 16, col = "#666666", cex = 0.44
      )
    }
    if (
      class_id == "non_mt_driver" &&
      isTRUE(class_slots$extended_reference_member[[index]])
    ) {
      graphics::points(
        marker_radius * cos(angle * pi / 180),
        marker_radius * sin(angle * pi / 180),
        pch = 5, col = "#555555", cex = 0.62, lwd = 0.9
      )
    }
  }

  for (network in phase18_network_order) {
    indices <- which(class_slots$broad_network == network)
    block_mid <- mean(c(
      class_slots$sector_start_degrees[[min(indices)]],
      class_slots$sector_end_degrees[[max(indices)]]
    ))
    network_radius <- 1.51
    graphics::text(
      network_radius * cos(block_mid * pi / 180),
      network_radius * sin(block_mid * pi / 180),
      labels = phase12_network_labels[[network]],
      srt = upright_rotation(block_mid), cex = 1.05,
      col = "#222222", font = 2
    )
    if (all(class_slots$slot_status[indices] == "no_passing_candidate_slot")) {
      empty_radius <- 1.21
      graphics::text(
        empty_radius * cos(block_mid * pi / 180),
        empty_radius * sin(block_mid * pi / 180),
        labels = "No passing\ncandidate",
        srt = upright_rotation(block_mid), cex = 0.48,
        col = "#666666", font = 3
      )
    }
  }

  graphics::title(
    main = "Phase 18 key-driver candidates across broad cell networks",
    cex.main = 1.18, font.main = 2, col.main = "#202020", line = 3.4
  )
  graphics::mtext(
    class_titles[[class_id]], side = 3, line = 2.15,
    cex = 0.86, font = 2, col = "#333333"
  )
  graphics::mtext(
    "Up to five passing candidates per network, ranked by aggregate ACAT q",
    side = 3, line = 1.35, cex = 0.62, col = "#555555"
  )
  if (class_id == "mt_driver") {
    graphics::mtext(
      "Self-overlap was removed only in runs where the MT driver was a query member",
      side = 3, line = 0.65, cex = 0.54, col = "#606060"
    )
  }
  graphics::mtext(
    "Center links mark repeated displayed genes across networks; they are not network edges",
    side = 1, line = 0.7, cex = 0.55, col = "#606060"
  )
  draw_legend(class_id)
}

figure_paths <- list()
for (class_id in class_order) {
  basename_value <- class_basenames[[class_id]]
  svg_path <- file.path(staging_dir, paste0(basename_value, ".svg"))
  pdf_path <- file.path(staging_dir, paste0(basename_value, ".pdf"))
  png_path <- file.path(staging_dir, paste0(basename_value, ".png"))
  message("Writing ", basename(svg_path))
  render_atomic(
    svg_path,
    function(path) open_svg_device(path, figure_width_inches, figure_height_inches),
    function() draw_circle(class_id)
  )
  message("Writing ", basename(pdf_path))
  render_atomic(
    pdf_path,
    function(path) open_pdf_device(path, figure_width_inches, figure_height_inches),
    function() draw_circle(class_id)
  )
  message("Writing ", basename(png_path))
  render_atomic(
    png_path,
    function(path) {
      open_png_device(path, figure_width_inches, figure_height_inches, dpi = png_dpi)
    },
    function() draw_circle(class_id)
  )
  figure_paths[[class_id]] <- c(svg = svg_path, pdf = pdf_path, png = png_path)
}

caption_lines <- c(
  "# Phase 18 two-class circular figures: caption",
  "",
  paste0(
    "**MT and non-MT key-driver candidates across broad brain-cell networks.** ",
    "Each circular graph shows one Phase 18 driver class. Within each broad ",
    "network, up to five genes passing the 80% coverage, conservative-support, ",
    "and aggregate ACAT q <= 0.05 gates are shown in ascending q-value rank. ",
    "Navy bar height is -log10(aggregate ACAT q) on a common scale capped at ",
    format(evidence_cap, trim = TRUE), ". Outer colors identify broad networks ",
    "using a colorblind-aware palette. Center curves connect repeated displayed ",
    "genes across networks within the same driver class and are not Bayesian-",
    "network edges. MT-driver self-overlap was removed only for runs where the ",
    "driver belonged to the mitochondrial query. Gray unused slots indicate ",
    "that fewer than five genes passed; failing genes were not used as backfills."
  )
)
atomic_write_lines(
  caption_lines,
  file.path(staging_dir, "phase18_two_case_circular_caption.md")
)

methods_lines <- c(
  "# Phase 18 two-class circular figures: methods",
  "",
  paste0(
    "The renderer read `call_key_driver_returns.tsv` (SHA-256 `", source_sha256,
    "`) and deduplicated run-level rows to one `broad_network + key_driver + ",
    "case_id` record. It retained records with `terminal_candidate_status = ",
    "driver_candidate`, ranked them within broad network and driver class by ",
    "ascending aggregate ACAT q, ascending aggregate ACAT P, and gene symbol, ",
    "and displayed ranks 1-5 without backfilling."
  ),
  "",
  paste0(
    "Both figures use identical seven-network, 35-slot geometry and a common ",
    "evidence cap of ", format(evidence_cap, trim = TRUE), ". Network identity is ",
    "encoded by the outer color band and text label. The right-side legend does ",
    "not obscure center links. SVG and PDF are authoritative vector exports; ",
    "PNG review copies were rendered at ", png_dpi, " dpi."
  ),
  "",
  "## Reproduction command",
  "",
  "```bash",
  paste(
    "Rscript --vanilla",
    "scripts/figures/analysis/phase_18_key_driver_selection/",
    "visualize_phase18_two_case_circular.R",
    "--input results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv",
    paste0(
      "--output-dir results/figures/analysis/phase_18_key_driver_selection/",
      "two_case_circular"
    ),
    "--top-per-network 5",
    paste("--evidence-cap", format(evidence_cap, trim = TRUE)),
    paste("--png-dpi", png_dpi),
    sep = paste0(" ", intToUtf8(92), "\n  ")
  ),
  "```"
)
atomic_write_lines(
  methods_lines,
  file.path(staging_dir, "phase18_two_case_circular_methods.md")
)

all_figure_paths <- unlist(figure_paths, use.names = FALSE)
checks <- data.frame(
  check_id = c(
    "input_rows", "input_columns", "included_runs", "aggregate_records",
    "driver_candidates", "displayed_records", "driver_classes",
    "fixed_slots", "figure_files", "figure_files_nonempty"
  ),
  observed = c(
    nrow(returns), ncol(returns), length(unique(returns$kda_run_id)),
    nrow(aggregates), nrow(candidates), nrow(displayed),
    length(unique(displayed$case_id)), nrow(plot_data),
    length(all_figure_paths), sum(file.info(all_figure_paths)$size > 0)
  ),
  expected = c(95557, 104, 161, 10433, 78, 47, 2, 70, 6, 6),
  passed = FALSE,
  stringsAsFactors = FALSE
)
checks$passed <- checks$observed == checks$expected
assert_true(all(checks$passed), "At least one output validation check failed")
atomic_write_table(
  checks,
  file.path(staging_dir, "phase18_two_case_circular_checks.tsv")
)

status <- data.frame(
  schema_version = "phase18_two_case_circular_status_v1",
  validation_status = "validated_complete",
  input_rows = nrow(returns),
  driver_candidates = nrow(candidates),
  displayed_records = nrow(displayed),
  figure_count = length(class_order),
  source_sha256 = source_sha256,
  stringsAsFactors = FALSE
)
atomic_write_table(
  status,
  file.path(staging_dir, "phase18_two_case_circular_status.tsv")
)

if (!file.rename(staging_dir, output_dir)) {
  stop("Could not publish output directory: ", output_dir, call. = FALSE)
}
published <- TRUE
message("Published ", output_dir)
message("figures=2 displayed_records=", nrow(displayed))
