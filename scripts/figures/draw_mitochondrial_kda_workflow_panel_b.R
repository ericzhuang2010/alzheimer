#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    input_dir = Sys.getenv("KDA_INPUT_DIR", unset = ""),
    output_dir = "results/figures/kda_workflow",
    basename = "mitochondrial_kda_workflow_panel_b"
  )
  value_options <- c("--input-dir", "--output-dir", "--basename")

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/draw_mitochondrial_kda_workflow_panel_b.R ",
        "--input-dir DIR [--output-dir DIR] [--basename NAME]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    value <- args[[i + 1L]]
    if (identical(key, "--input-dir")) {
      out$input_dir <- value
    } else if (identical(key, "--output-dir")) {
      out$output_dir <- value
    } else {
      out$basename <- value
    }
    i <- i + 2L
  }

  if (!nzchar(out$input_dir)) {
    stop("--input-dir is required (or set KDA_INPUT_DIR)", call. = FALSE)
  }
  if (!nzchar(out$output_dir)) {
    stop("--output-dir must not be empty", call. = FALSE)
  }
  if (!grepl("^[A-Za-z0-9._-]+$", out$basename)) {
    stop(
      "--basename may contain only letters, numbers, dots, underscores, and hyphens",
      call. = FALSE
    )
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

read_tsv <- function(path) {
  utils::read.delim(
    path,
    header = TRUE,
    sep = "\t",
    quote = "",
    comment.char = "",
    check.names = FALSE
  )
}

require_columns <- function(x, columns, label) {
  missing <- setdiff(columns, names(x))
  if (length(missing)) {
    stop(
      label, " is missing columns: ", paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
}

format_count <- function(x) {
  format(as.integer(x), big.mark = ",", scientific = FALSE, trim = TRUE)
}

read_panel_values <- function(input_dir) {
  status_path <- file.path(input_dir, "kda_status.tsv")
  manifest_path <- file.path(input_dir, "kda_run_manifest.tsv")
  missing_files <- c(status_path, manifest_path)[
    !file.exists(c(status_path, manifest_path))
  ]
  if (length(missing_files)) {
    stop(
      "Missing KDA input files: ", paste(missing_files, collapse = ", "),
      call. = FALSE
    )
  }

  status <- read_tsv(status_path)
  manifest <- read_tsv(manifest_path)
  require_columns(
    status,
    c("validation_status", "planned_runs"),
    "KDA status"
  )
  require_columns(
    manifest,
    c("analysis_tier", "signature_group", "signature_direction"),
    "KDA run manifest"
  )
  if (nrow(status) != 1L) {
    stop("KDA status must contain exactly one row", call. = FALSE)
  }
  if (!identical(status$validation_status[[1L]], "validated_complete")) {
    stop("KDA status is not validated_complete", call. = FALSE)
  }

  primary_groups <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
  secondary_groups <- c(
    "female_pool", "male_pool", "e2_pool", "e33_pool", "e4_pool"
  )
  directions <- c("AD_up_mito", "AD_down_mito", "AD_both_mito")
  primary_count <- sum(manifest$analysis_tier == "primary")
  secondary_count <- sum(manifest$analysis_tier == "secondary")
  planned_count <- nrow(manifest)

  checks <- data.frame(
    check_id = c(
      "status_manifest_planned_agree",
      "primary_run_count",
      "secondary_run_count",
      "primary_groups_present",
      "secondary_groups_present",
      "directions_present_in_both_tiers"
    ),
    passed = c(
      status$planned_runs[[1L]] == planned_count,
      primary_count == 972L,
      secondary_count == 810L,
      setequal(
        unique(manifest$signature_group[manifest$analysis_tier == "primary"]),
        primary_groups
      ),
      setequal(
        unique(manifest$signature_group[manifest$analysis_tier == "secondary"]),
        secondary_groups
      ),
      all(vapply(
        c("primary", "secondary"),
        function(tier) {
          setequal(
            unique(manifest$signature_direction[
              manifest$analysis_tier == tier
            ]),
            directions
          )
        },
        logical(1)
      ))
    ),
    stringsAsFactors = FALSE
  )
  if (!all(checks$passed)) {
    stop(
      "Panel B input validation failed: ",
      paste(checks$check_id[!checks$passed], collapse = ", "),
      call. = FALSE
    )
  }

  list(
    values = c(
      planned_runs = planned_count,
      primary_planned_runs = primary_count,
      secondary_planned_runs = secondary_count
    ),
    checks = checks
  )
}

colours <- list(
  ink = "#183247",
  text = "#344B5E",
  muted = "#667985",
  primary = "#137C79",
  primary_fill = "#E2F2EF",
  secondary = "#7251A3",
  secondary_fill = "#EFE9F7",
  up = "#D55E42",
  up_fill = "#F9E4DD",
  down = "#2F6FAE",
  down_fill = "#E2EDF8",
  both = "#7E5A88",
  both_fill = "#EEE7F2"
)

figure_width <- 15.5
figure_height <- 5.6
figure_pointsize <- 18

rounded_box <- function(
    x0, y0, x1, y1, fill = "white", border = "#93A2AC",
    radius = 0.10, lwd = 1.2, lty = 1) {
  width <- x1 - x0
  height <- y1 - y0
  radius <- min(radius, width / 2, height / 2)
  arc <- function(cx, cy, from, to, n = 16L) {
    theta <- seq(from, to, length.out = n) * pi / 180
    cbind(cx + radius * cos(theta), cy + radius * sin(theta))
  }
  pts <- rbind(
    arc(x1 - radius, y0 + radius, -90, 0),
    arc(x1 - radius, y1 - radius, 0, 90),
    arc(x0 + radius, y1 - radius, 90, 180),
    arc(x0 + radius, y0 + radius, 180, 270)
  )
  graphics::polygon(
    pts[, 1L], pts[, 2L], col = fill, border = border,
    lwd = lwd, lty = lty
  )
}

draw_arrow <- function(
    x0, y0, x1, y1, col, lwd = 1.7, length = 0.09) {
  graphics::arrows(
    x0, y0, x1, y1, length = length, angle = 23, code = 2,
    col = col, lwd = lwd
  )
}

draw_pill <- function(
    x, y, width, height, label, fill, border, col = colours$ink,
    cex = 0.80, font = 2, lty = 1) {
  rounded_box(
    x - width / 2, y - height / 2, x + width / 2, y + height / 2,
    fill = fill, border = border, radius = height / 2,
    lwd = 1.35, lty = lty
  )
  graphics::text(x, y, label, cex = cex, font = font, col = col)
}

draw_signature_badge <- function(x, y, direction, label, width = 1.05) {
  style <- switch(
    direction,
    up = list(fill = colours$up_fill, border = colours$up, symbol = "▲"),
    down = list(fill = colours$down_fill, border = colours$down, symbol = "▼"),
    both = list(fill = colours$both_fill, border = colours$both, symbol = "◆")
  )
  rounded_box(
    x - width / 2, y - 0.30, x + width / 2, y + 0.30,
    fill = style$fill, border = style$border, radius = 0.10, lwd = 1.25
  )
  graphics::text(
    x - width * 0.31, y, style$symbol, cex = 0.78, col = style$border
  )
  graphics::text(
    x + width * 0.07, y, label, cex = 0.74, font = 2, col = colours$ink
  )
}

draw_panel_b <- function(values) {
  old <- graphics::par(
    mar = c(0.12, 0.12, 0.12, 0.12),
    xaxs = "i", yaxs = "i", family = "sans", bg = "white"
  )
  on.exit(graphics::par(old), add = TRUE)
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(0, figure_width), ylim = c(0, figure_height), asp = NA
  )

  rounded_box(
    0.35, 0.35, 15.15, 5.25,
    fill = "white", border = "#CBD3D8", radius = 0.16, lwd = 1.4
  )
  graphics::rect(0.35, 4.45, 15.15, 5.25, col = "#EAF0F3", border = NA)
  graphics::text(
    0.65, 4.85, "Primary and Secondary Runs",
    adj = c(0, 0.5), cex = 1.30, font = 2, col = colours$ink
  )
  draw_pill(
    13.50, 4.85, 2.65, 0.50,
    paste0(format_count(values[["planned_runs"]]), " planned runs"),
    fill = "#F8FAFB", border = colours$ink, cex = 0.80
  )

  rounded_box(
    0.72, 2.65, 14.78, 4.18,
    fill = colours$primary_fill, border = colours$primary,
    radius = 0.15, lwd = 1.8
  )
  graphics::text(
    1.00, 3.85, "PRIMARY", adj = c(0, 0.5), cex = 1.02,
    font = 2, col = colours$primary
  )
  graphics::text(
    1.00, 3.39, "six individual\nstrata", adj = c(0, 0.5),
    cex = 0.78, col = colours$text
  )

  groups <- c("F e2", "F e33", "F e4", "M e2", "M e33", "M e4")
  gx <- seq(2.75, 7.85, length.out = length(groups))
  for (i in seq_along(groups)) {
    draw_pill(
      gx[[i]], 3.55, 0.93, 0.56, groups[[i]],
      fill = "white", border = colours$primary, cex = 0.72
    )
  }
  graphics::text(
    5.30, 2.96, "each AD–NCI contrast remains separate",
    cex = 0.72, col = colours$text, font = 3
  )
  draw_arrow(8.36, 3.39, 8.83, 3.39, col = colours$primary)
  draw_signature_badge(9.43, 3.55, "up", "AD-up", width = 1.13)
  draw_signature_badge(10.63, 3.55, "down", "AD-down", width = 1.25)
  draw_signature_badge(11.83, 3.55, "both", "Both", width = 1.08)
  graphics::text(
    10.63, 2.96, "D_both = D_up ∪ D_down",
    cex = 0.72, col = colours$text
  )
  draw_pill(
    13.65, 3.39, 2.05, 0.76,
    paste0(
      "54 × 6 × 3\n= ", format_count(values[["primary_planned_runs"]])
    ),
    fill = "white", border = colours$primary, cex = 0.78
  )

  rounded_box(
    0.72, 0.65, 14.78, 2.34,
    fill = colours$secondary_fill, border = colours$secondary,
    radius = 0.15, lwd = 1.8, lty = 2
  )
  graphics::text(
    1.00, 2.02, "SECONDARY", adj = c(0, 0.5), cex = 1.02,
    font = 2, col = colours$secondary
  )
  graphics::text(
    1.00, 1.53, "five pooled\nsummaries", adj = c(0, 0.5),
    cex = 0.78, col = colours$text
  )

  pool_labels <- c(
    "Female\nF e2+e33+e4", "Male\nM e2+e33+e4",
    "e2\nF+M", "e33\nF+M", "e4\nF+M"
  )
  px <- seq(2.73, 7.77, length.out = length(pool_labels))
  for (i in seq_along(pool_labels)) {
    rounded_box(
      px[[i]] - 0.58, 1.03, px[[i]] + 0.58, 1.86,
      fill = "white", border = colours$secondary, radius = 0.10,
      lwd = 1.25, lty = 2
    )
    graphics::text(
      px[[i]], 1.45, pool_labels[[i]], cex = 0.66,
      font = 2, col = colours$ink
    )
  }
  draw_arrow(8.34, 1.45, 8.78, 1.45, col = colours$secondary)
  draw_signature_badge(9.34, 1.61, "up", "P-up", width = 1.04)
  draw_signature_badge(10.48, 1.61, "down", "P-down", width = 1.15)
  draw_signature_badge(11.62, 1.61, "both", "Both", width = 1.04)
  graphics::text(
    10.48, 0.89,
    "DEG set unions • no pooled model refit\ndirection discordance retained + flagged",
    cex = 0.66, col = colours$text
  )
  draw_pill(
    13.65, 1.45, 2.05, 0.76,
    paste0(
      "54 × 5 × 3\n= ", format_count(values[["secondary_planned_runs"]])
    ),
    fill = "white", border = colours$secondary, cex = 0.78, lty = 2
  )
}

write_graphic_atomic <- function(path, open_device, draw_fun) {
  extension <- tools::file_ext(path)
  tmp <- file.path(
    dirname(path),
    paste0(
      ".", tools::file_path_sans_ext(basename(path)), ".tmp.",
      Sys.getpid(), ".", extension
    )
  )
  device_open <- FALSE
  on.exit({
    if (device_open && grDevices::dev.cur() > 1L) grDevices::dev.off()
    if (file.exists(tmp)) unlink(tmp)
  }, add = TRUE)
  open_device(tmp)
  device_open <- TRUE
  draw_fun()
  grDevices::dev.off()
  device_open <- FALSE
  if (!file.exists(tmp) || file.info(tmp)$size <= 0) {
    stop("Renderer produced an empty output: ", path, call. = FALSE)
  }
  if (!file.rename(tmp, path)) {
    stop("Could not publish graphic: ", path, call. = FALSE)
  }
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- normalizePath(
  absolute_path(args$input_dir, project_root), mustWork = TRUE
)
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo graphics support", call. = FALSE)
}

message("Validating the KDA inputs used by standalone panel B")
panel_data <- read_panel_values(input_dir)
values <- panel_data$values

svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
pdf_path <- file.path(output_dir, paste0(args$basename, ".pdf"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))

message("Writing ", svg_path)
write_graphic_atomic(
  svg_path,
  function(path) grDevices::svg(
    path, width = figure_width, height = figure_height,
    pointsize = figure_pointsize, onefile = TRUE,
    family = "sans", bg = "white", antialias = "subpixel"
  ),
  function() draw_panel_b(values)
)

message("Writing ", pdf_path)
write_graphic_atomic(
  pdf_path,
  function(path) grDevices::cairo_pdf(
    path, width = figure_width, height = figure_height,
    pointsize = figure_pointsize,
    family = "sans", bg = "white", onefile = TRUE
  ),
  function() draw_panel_b(values)
)

message("Writing ", png_path)
write_graphic_atomic(
  png_path,
  function(path) grDevices::png(
    path, width = figure_width * 300, height = figure_height * 300,
    units = "px", res = 300, pointsize = figure_pointsize, bg = "white",
    type = "cairo", antialias = "subpixel"
  ),
  function() draw_panel_b(values)
)

message(
  "Standalone panel B complete: ",
  format_count(values[["planned_runs"]]), " planned runs"
)
