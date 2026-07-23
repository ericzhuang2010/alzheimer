#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    output_dir = "results/figures/processing_pipeline",
    basename = "processing_pipeline"
  )

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/draw_processing_pipeline.R ",
        "[--output-dir PATH] [--basename NAME]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% c("--output-dir", "--basename") || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }

    value <- args[[i + 1L]]
    if (identical(key, "--output-dir")) {
      out$output_dir <- value
    } else if (identical(key, "--basename")) {
      out$basename <- value
    }
    i <- i + 2L
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

rounded_box <- function(
    x, y, width, height, fill, border, radius = 0.12, lwd = 1.5) {
  left <- x - width / 2
  right <- x + width / 2
  bottom <- y - height / 2
  top <- y + height / 2
  radius <- min(radius, width / 2, height / 2)

  arc <- function(cx, cy, from, to, n = 12L) {
    theta <- seq(from, to, length.out = n) * pi / 180
    cbind(cx + radius * cos(theta), cy + radius * sin(theta))
  }

  points <- rbind(
    arc(right - radius, bottom + radius, -90, 0),
    arc(right - radius, top - radius, 0, 90),
    arc(left + radius, top - radius, 90, 180),
    arc(left + radius, bottom + radius, 180, 270)
  )
  polygon(points[, 1L], points[, 2L], col = fill, border = border, lwd = lwd)
}

draw_phase <- function(stage) {
  rounded_box(
    stage$x, stage$y, stage$width, stage$height,
    fill = stage$fill, border = stage$border, radius = 0.13, lwd = 1.7
  )
  title_offset <- if (is.null(stage$title_offset)) 0.43 else stage$title_offset
  detail_offset <- if (is.null(stage$detail_offset)) -0.35 else stage$detail_offset

  text(
    stage$x, stage$y + title_offset, stage$title,
    cex = 2.04, font = 2, col = "#183247"
  )
  text(
    stage$x, stage$y + detail_offset, stage$detail,
    cex = 1.60, col = "#344B5E"
  )
}

draw_source <- function(x, y, width, label) {
  rounded_box(
    x, y, width, 0.90,
    fill = "#F4F6F8", border = "#8B98A5", radius = 0.16, lwd = 1.2
  )
  text(x, y, label, cex = 1.52, font = 2, col = "#3C4B59")
}


draw_arrow <- function(x0, y0, x1, y1, col = "#52697A", lwd = 1.8) {
  arrows(
    x0, y0, x1, y1,
    length = 0.075, angle = 22, code = 2, col = col, lwd = lwd
  )
}

draw_pipeline <- function() {
  par(
    mar = c(0.15, 0.15, 0.15, 0.15),
    xaxs = "i", yaxs = "i", family = "sans"
  )
  plot.new()
  plot.window(xlim = c(0, 18), ylim = c(1.65, 8.8), asp = NA)


  section_col <- "#607688"
  text(0.35, 8.62, "PRIMARY INPUTS", adj = c(0, 0.5), cex = 0.84, font = 2, col = section_col)
  text(0.35, 7.37, "DATA FOUNDATION", adj = c(0, 0.5), cex = 0.84, font = 2, col = section_col)
  text(
    0.35, 4.42, "DISEASE EFFECTS & MITOCHONDRIAL INTERPRETATION",
    adj = c(0, 0.5), cex = 0.84, font = 2, col = section_col
  )

  top_x <- c(2.2, 6.6, 11.0, 15.4)
  lower_x <- c(2.2, 6.6, 11.0, 15.4)
  top_y <- 6.22
  lower_y <- 3.20
  top_width <- 3.05
  lower_width <- 3.75
  top_height <- 2.05
  lower_height <- 2.20

  stages <- list(
    list(
      phase = "01", x = top_x[[1L]], y = top_y, width = top_width,
      height = top_height, title = "Audit Seurat\ninputs",
      detail = "Raw-count integrity\nfeatures, donors\n& cell types",
      fill = "#E3EFF8", border = "#3C78A6"
    ),
    list(
      phase = "02", x = top_x[[2L]], y = top_y, width = top_width,
      height = top_height, title = "Build clinical\ncohort",
      detail = "Keyed metadata join\n276 eligible donors",
      fill = "#E3EFF8", border = "#3C78A6"
    ),
    list(
      phase = "03", x = top_x[[3L]], y = top_y, width = top_width,
      height = 2.55, title_offset = 0.64, detail_offset = -0.64,
      title = "Freeze\nmitochondrial\nsets",
      detail = "GENCODE + MitoCarta\nmeasured/tested\nuniverses",
      fill = "#E3EFF8", border = "#3C78A6"
    ),
    list(
      phase = "05", x = top_x[[4L]], y = top_y, width = top_width,
      height = top_height, title = "Normalize & add\nmetadata",
      detail = "Seurat LogNormalize\npreserve raw RNA\ncounts",
      fill = "#E2F2ED", border = "#278477"
    ),
    list(
      phase = "08", x = lower_x[[1L]], y = lower_y, width = lower_width,
      height = lower_height, title = "Cell-level MAST DE",
      detail = "Six sex x APOE\nAD-vs-NCI contrasts\nper fine cell type\n(324 planned)",
      fill = "#FBE8DD", border = "#B96236"
    ),
    list(
      phase = "09", x = lower_x[[2L]], y = lower_y, width = lower_width,
      height = lower_height, title = "Annotate DEG genes",
      detail = "Identifier crosswalk\n+ mitochondrial tiers,\npathways & DEG states",
      fill = "#FBE8DD", border = "#B96236"
    ),
    list(
      phase = "10", x = lower_x[[3L]], y = lower_y, width = lower_width,
      height = lower_height, title = "Score similarity",
      detail = "Ternary DEG\nconcordance\npermutations +\nranked sets",
      fill = "#EEE7F5", border = "#79589A"
    ),
    list(
      phase = "11", x = lower_x[[4L]], y = lower_y, width = lower_width,
      height = lower_height, title = "Prepare pathway data",
      detail = "MSigDB CP +\nMitoCarta ORA\nfigure-ready\npanel tables",
      fill = "#EEE7F5", border = "#79589A"
    )
  )

  arrow_col <- "#597083"
  for (i in seq_len(length(top_x) - 1L)) {
    draw_arrow(
      top_x[[i]] + top_width / 2 + 0.05, top_y,
      top_x[[i + 1L]] - top_width / 2 - 0.05, top_y,
      col = arrow_col
    )
  }
  for (i in seq_len(length(lower_x) - 1L)) {
    draw_arrow(
      lower_x[[i]] + lower_width / 2 + 0.05, lower_y,
      lower_x[[i + 1L]] - lower_width / 2 - 0.05, lower_y,
      col = arrow_col
    )
  }

  top_bottom <- top_y - top_height / 2
  lower_top <- lower_y + lower_height / 2
  handoff_y <- 4.75
  segments(top_x[[4L]], top_bottom, top_x[[4L]], handoff_y, col = arrow_col, lwd = 1.8)
  segments(top_x[[4L]], handoff_y, lower_x[[1L]], handoff_y, col = arrow_col, lwd = 1.8)
  draw_arrow(lower_x[[1L]], handoff_y, lower_x[[1L]], lower_top + 0.04, col = arrow_col)
  rounded_box(
    8.0, handoff_y, 3.25, 0.42,
    fill = "white", border = NA, radius = 0.08, lwd = 1
  )
  text(
    8.0, handoff_y, "normalized RNA + cohort metadata",
    cex = 0.72, font = 3, col = "#5A6E7E"
  )

  source_y <- 8.10
  draw_arrow(top_x[[1L]], source_y - 0.47, top_x[[1L]], top_y + top_height / 2 + 0.04, col = "#8B98A5", lwd = 1.3)
  draw_arrow(top_x[[2L]], source_y - 0.47, top_x[[2L]], top_y + top_height / 2 + 0.04, col = "#8B98A5", lwd = 1.3)
  draw_arrow(top_x[[3L]], source_y - 0.47, top_x[[3L]], top_y + 2.55 / 2 + 0.04, col = "#8B98A5", lwd = 1.3)


  draw_source(top_x[[1L]], source_y, 2.9, "9 Seurat objects\n+ cell metadata")
  draw_source(top_x[[2L]], source_y, 2.9, "Clinical covariates\ndiagnosis, sex, APOE")
  draw_source(top_x[[3L]], source_y, 2.9, "GENCODE v44\n+ MitoCarta 3.0")

  invisible(lapply(stages, draw_phase))


  text(
    17.65, 1.78,
    "Arrows summarize the selected processing sequence; outputs retain validation and provenance bundles.",
    adj = c(1, 0.5), cex = 0.64, col = "#6F7E89"
  )
  box(col = NA)
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
project_root <- normalizePath(getwd(), mustWork = TRUE)
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo support required for SVG output", call. = FALSE)
}

svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
tmp_svg <- paste0(svg_path, ".tmp.", Sys.getpid(), ".svg")
device_open <- FALSE
on.exit({
  if (device_open && grDevices::dev.cur() > 1L) {
    grDevices::dev.off()
  }
  if (file.exists(tmp_svg)) {
    unlink(tmp_svg)
  }
}, add = TRUE)

message("Writing ", svg_path)
grDevices::svg(
  tmp_svg,
  width = 18,
  height = 7.15,
  bg = "white",
  family = "sans",
  antialias = "subpixel"
)
device_open <- TRUE
draw_pipeline()
grDevices::dev.off()
device_open <- FALSE

if (!file.rename(tmp_svg, svg_path)) {
  stop("Could not publish SVG output: ", svg_path, call. = FALSE)
}

message("Pipeline figure complete")
