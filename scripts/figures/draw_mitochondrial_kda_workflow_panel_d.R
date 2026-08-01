#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    output_dir = "results/figures/kda_workflow",
    basename = "mitochondrial_kda_workflow_panel_d"
  )
  value_options <- c("--output-dir", "--basename")

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/draw_mitochondrial_kda_workflow_panel_d.R ",
        "[--output-dir DIR] [--basename NAME]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    value <- args[[i + 1L]]
    if (identical(key, "--output-dir")) {
      out$output_dir <- value
    } else {
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

colours <- list(
  ink = "#183247",
  text = "#344B5E",
  muted = "#667985",
  primary = "#137C79",
  query = "#E6A51A",
  query_fill = "#FDE7A7",
  success = "#2B7A4B",
  success_fill = "#E4F2E8",
  skip = "#7A8790",
  network_dark = "#5B6A73"
)

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
    x0, y0, x1, y1, col = colours$muted, lwd = 1.7,
    length = 0.09) {
  graphics::arrows(
    x0, y0, x1, y1, length = length, angle = 23, code = 2,
    col = col, lwd = lwd
  )
}

draw_pill <- function(
    x, y, width, height, label, fill, border, col = colours$ink,
    cex = 0.88, font = 2) {
  rounded_box(
    x - width / 2, y - height / 2, x + width / 2, y + height / 2,
    fill = fill, border = border, radius = height / 2, lwd = 1.4
  )
  graphics::text(x, y, label, cex = cex, font = font, col = col)
}

draw_node <- function(
    x, y, fill, border = colours$network_dark, cex = 1.5,
    label = NULL, label_cex = 0.72, text_col = colours$ink) {
  graphics::points(
    x, y, pch = 21, bg = fill, col = border, cex = cex, lwd = 1.4
  )
  if (!is.null(label)) {
    graphics::text(
      x, y, label, cex = label_cex, font = 2, col = text_col
    )
  }
}

draw_kda_network <- function() {
  pts <- data.frame(
    x = c(1.30, 3.10, 3.10, 5.05, 5.05, 5.05, 6.95, 6.95, 6.95),
    y = c(4.25, 5.13, 3.37, 5.75, 4.25, 2.75, 5.55, 4.25, 2.95),
    query = c(FALSE, TRUE, FALSE, FALSE, TRUE, FALSE, TRUE, FALSE, TRUE)
  )
  edges <- rbind(
    c(1, 2), c(1, 3), c(2, 4), c(2, 5), c(3, 5), c(3, 6),
    c(4, 7), c(5, 7), c(5, 8), c(6, 8), c(6, 9)
  )

  graphics::text(
    c(3.10, 5.05, 6.95), rep(6.12, 3),
    c("layer 1", "layer 2", "layer 3"),
    cex = 0.78, font = 2, col = colours$muted
  )
  graphics::segments(
    c(2.28, 4.23, 6.13), 5.94,
    c(3.92, 5.87, 7.77), 5.94,
    col = "#D2D9DD", lwd = 1.3
  )

  for (i in seq_len(nrow(edges))) {
    a <- edges[i, 1L]
    b <- edges[i, 2L]
    draw_arrow(
      pts$x[[a]], pts$y[[a]], pts$x[[b]], pts$y[[b]],
      col = "#7E8E98", lwd = 1.45, length = 0.075
    )
  }

  draw_node(
    pts$x[[1L]], pts$y[[1L]], fill = colours$primary,
    border = "#0C5654", cex = 2.75, label = "KD", label_cex = 0.76,
    text_col = "white"
  )
  for (i in 2:nrow(pts)) {
    if (pts$query[[i]]) {
      draw_node(
        pts$x[[i]], pts$y[[i]], colours$query_fill,
        colours$query, cex = 1.75
      )
    } else {
      draw_node(
        pts$x[[i]], pts$y[[i]], "#E2E7EA",
        colours$network_dark, cex = 1.62
      )
    }
  }

  graphics::text(
    1.30, 3.48, "candidate\nupstream driver",
    cex = 0.72, col = colours$text
  )
  graphics::points(
    2.35, 2.02, pch = 21, bg = colours$query_fill,
    col = colours$query, cex = 1.45, lwd = 1.3
  )
  graphics::text(
    2.68, 2.02, "effective query gene", adj = c(0, 0.5),
    cex = 0.74, col = colours$text
  )
  graphics::points(
    5.15, 2.02, pch = 21, bg = "#E2E7EA",
    col = colours$network_dark, cex = 1.45, lwd = 1.3
  )
  graphics::text(
    5.48, 2.02, "background gene", adj = c(0, 0.5),
    cex = 0.74, col = colours$text
  )
}

draw_panel_d <- function() {
  old <- graphics::par(
    mar = c(0.12, 0.12, 0.12, 0.12),
    xaxs = "i", yaxs = "i", family = "sans", bg = "white"
  )
  on.exit(graphics::par(old), add = TRUE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 14), ylim = c(0, 7.5), asp = NA)

  rounded_box(
    0.35, 0.35, 13.65, 7.15,
    fill = "white", border = "#CBD3D8", radius = 0.17, lwd = 1.4
  )
  graphics::rect(0.35, 6.35, 13.65, 7.15, col = "#EAF0F3", border = NA)
  graphics::text(
    0.68, 6.75, "NetWeaver Key Driver Analysis",
    adj = c(0, 0.5), cex = 1.18, font = 2, col = colours$ink
  )

  draw_kda_network()

  rounded_box(
    7.90, 2.15, 13.20, 5.95,
    fill = "#FBFCFC", border = "#B5C0C7", radius = 0.15, lwd = 1.35
  )
  graphics::text(
    8.23, 5.52, "Is the query concentrated downstream?",
    adj = c(0, 0.5), cex = 0.98, font = 2, col = colours$ink
  )
  graphics::text(
    8.25, 4.85,
    "M  background genes        m  neighborhood genes\n",
    adj = c(0, 0.5), cex = 0.76, col = colours$text
  )
  graphics::text(
    8.25, 4.52,
    "k  query genes                  q  query genes in neighborhood",
    adj = c(0, 0.5), cex = 0.76, col = colours$text
  )
  draw_pill(
    10.55, 3.78, 4.25, 0.77,
    "fold enrichment = (q/m) / (k/M)",
    fill = colours$query_fill, border = colours$query, cex = 0.87
  )
  graphics::text(
    10.55, 3.02,
    "one-sided hypergeometric test\nBH correction across drivers within this run",
    cex = 0.78, col = colours$text
  )
  draw_pill(
    10.55, 2.48, 3.80, 0.58,
    "adjusted P ≤ 0.05",
    fill = colours$success_fill, border = colours$success,
    col = colours$success, cex = 0.88
  )

  graphics::text(
    10.55, 1.83,
    "directed • layers 1–3 • no signature expansion • overlap genes returned",
    cex = 0.69, col = colours$muted
  )
  rounded_box(
    0.82, 0.65, 13.18, 1.58,
    fill = "#F5F8F9", border = "#A9B6BE", radius = 0.11, lwd = 1.25
  )
  graphics::text(
    1.16, 1.25, "REPORT", adj = c(0, 0.5),
    cex = 0.78, font = 2, col = colours$muted
  )
  graphics::text(
    4.45, 1.11,
    "Putative key driver\nbest layer • overlap • enrichment • adjusted P",
    cex = 0.80, font = 2, col = colours$ink
  )
  graphics::segments(
    7.10, 0.80, 7.10, 1.43, col = "#C1C9CE", lwd = 1.2
  )
  graphics::text(
    10.15, 1.11,
    "No driver passes cutoff\n= completed, not failed",
    cex = 0.80, col = colours$skip
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
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo graphics support", call. = FALSE)
}

svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
pdf_path <- file.path(output_dir, paste0(args$basename, ".pdf"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))

message("Writing ", svg_path)
write_graphic_atomic(
  svg_path,
  function(path) grDevices::svg(
    path, width = 14, height = 7.5, pointsize = 18, onefile = TRUE,
    family = "sans", bg = "white", antialias = "subpixel"
  ),
  draw_panel_d
)

message("Writing ", pdf_path)
write_graphic_atomic(
  pdf_path,
  function(path) grDevices::cairo_pdf(
    path, width = 14, height = 7.5, pointsize = 18,
    family = "sans", bg = "white", onefile = TRUE
  ),
  draw_panel_d
)

message("Writing ", png_path)
write_graphic_atomic(
  png_path,
  function(path) grDevices::png(
    path, width = 4200, height = 2250, units = "px", res = 300,
    pointsize = 18, bg = "white", type = "cairo", antialias = "subpixel"
  ),
  draw_panel_d
)

message("Standalone panel D complete")
