#!/usr/bin/env Rscript

# Reproducible examples rendered directly from the R files in this checkout.
# Usage: Rscript examples/generate_local_figures.R [output-directory]

options(stringsAsFactors = FALSE)
set.seed(20260801)

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) {
  stop("Run this file with Rscript")
}
script_path <- normalizePath(sub("^--file=", "", script_arg))
package_dir <- normalizePath(file.path(dirname(script_path), ".."))
args <- commandArgs(trailingOnly = TRUE)
output_dir <- if (length(args)) args[[1L]] else file.path(dirname(script_path), "generated")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
output_dir <- normalizePath(output_dir)

# Source the checkout itself rather than an installed copy of NetWeaver.
r_dir <- file.path(package_dir, "R")
r_files <- list.files(r_dir, pattern = "[.]R$", full.names = TRUE)
env_file <- file.path(r_dir, "rcEnvir.R")
for (r_file in c(env_file, setdiff(r_files, env_file))) {
  sys.source(r_file, envir = globalenv())
}

save_png <- function(filename, draw, width = 2200L, height = width, res = 220L) {
  path <- file.path(output_dir, filename)
  png(path, width = width, height = height, res = res, bg = "white")
  on.exit(dev.off(), add = TRUE)
  draw()
  dev.off()
  on.exit(NULL, add = FALSE)
  message("Wrote ", path)
  invisible(path)
}

plot_primitives <- function() {
  cyto <- data.frame(
    Chr = paste0("C", 1:20),
    Start = 1,
    End = 100,
    BandColor = grDevices::hcl.colors(20, "Set 3")
  )

  rc.initialize(
    cyto,
    num.tracks = 9,
    params = list(chr.padding = 0.1, slice.size = 300, slice.rotate = 30)
  )
  params <- rc.get.params()
  rc.plot.area(size = 0.93)
  rc.plot.ideogram(1:2, plot.band = TRUE, plot.chromosome.id = TRUE,
                   track.border = NA, polygon.border = "white", cex.text = 0.65)

  cross_data <- data.frame(
    Chr1 = paste0("C", seq(1, 16, by = 3)),
    Start1 = 35,
    Chr2 = paste0("C", seq(3, 18, by = 3)),
    End2 = 65,
    Value = seq(0.25, 1, length.out = 6),
    Color = grDevices::hcl.colors(6, "Plasma")
  )
  rc.plot.mHistogram(cross_data, track.id = 3, data.col = "Value",
                     color.col = "Color", track.border = NA, polygon.border = NA)

  hist_data <- data.frame(
    Chr = cyto$Chr,
    Start = 1,
    End = 48,
    Value = runif(20, 0.12, 1)
  )
  rc.plot.histogram(hist_data, track.id = 5, data.col = "Value",
                    color.gradient = hcl.colors(50, "Blues 3"),
                    custom.track.height = params$track.height * 2,
                    track.border = NA, polygon.border = NA)

  heat_data <- data.frame(
    Chr = cyto$Chr,
    Start = 52,
    End = 100,
    Value = seq_len(20)
  )
  rc.plot.histogram(heat_data, track.id = 6, data.col = "Value",
                    color.gradient = rev(heat.colors(50)), fixed.height = TRUE,
                    track.border = NA, polygon.border = NA)

  bar_data <- data.frame(
    Chr = cyto$Chr,
    Start = 1,
    End = 100,
    A = runif(20), B = runif(20), C = runif(20), D = runif(20)
  )
  rc.plot.barchart(bar_data, track.id = 7, data.col = c("A", "B", "C", "D"),
                   bar.color = hcl.colors(4, "YlGnBu"), ratio = TRUE,
                   track.border = NA, polygon.border = NA)

  links <- data.frame(
    Chr1 = sample(cyto$Chr, 28, replace = TRUE),
    Pos1 = sample(15:85, 28, replace = TRUE),
    Chr2 = sample(cyto$Chr, 28, replace = TRUE),
    Pos2 = sample(15:85, 28, replace = TRUE),
    Weight = runif(28, 0.2, 1),
    Color = grDevices::adjustcolor(
      sample(c("#2C7BB6", "#D7191C", "#FDAE61", "#1A9641"), 28, replace = TRUE),
      alpha.f = 0.65
    )
  )
  links <- links[links$Chr1 != links$Chr2, ]
  rc.plot.link(links, track.id = 8, data.col = "Weight", color.col = "Color",
               max.lwd = 2.5)

  ribbons <- data.frame(
    Chr1 = c("C1", "C4"), Start1 = c(10, 15), End1 = c(38, 42),
    Chr2 = c("C15", "C11"), Start2 = c(10, 15), End2 = c(55, 60),
    Color = grDevices::adjustcolor(c("#9E0142", "#5E4FA2"), alpha.f = 0.55)
  )
  rc.plot.ribbon(ribbons, track.id = 8, color.col = "Color", twist = TRUE)

  rc.plot.point(
    data.frame(Chr = c("C2", "C7", "C12"), Pos = c(50, 60, 45),
               Height = c(0.5, 1, 0.75), Color = c("black", "red", "navy")),
    track.id = 3, color.col = "Color", pch = 19, cex = 1.1
  )
  rc.plot.line(
    data.frame(Chr = "C19", Pos = seq(15, 85, by = 14), Color = "#333333"),
    track.id = 3, color.col = "Color", arrow.length = 0.08, lwd = 1.2
  )
  rc.plot.text(data.frame(Chr = "C4", Pos = 50, Label = "feature"),
               track.id = 3.5, col = "#111111", cex = 0.6)
  rc.plot.track.id(2:7, labels = c("bands", "span", "bars", "heat", "stack"),
                   col = "#444444", cex = 0.55)
  title("NetWeaver plotting primitives", line = -1.5, cex.main = 1.15)
}

plot_modules <- function() {
  data_env <- new.env(parent = emptyenv())
  load(file.path(package_dir, "data", "Modules.RData"), envir = data_env)
  modules <- data_env$Modules

  blue <- colorRampPalette(c("white", "#2166AC"))
  brown <- colorRampPalette(c("white", "#8C510A"))
  heat <- function(n) rev(heat.colors(n))
  n_col <- 50L
  cyto <- data.frame(Chr = modules$id, Start = 1, End = 100,
                     BandColor = "black")

  rc.initialize(cyto, num.tracks = 36, params = list(chr.padding = 0.1))
  params <- rc.get.params()
  rc.plot.area(size = 0.9)
  aliases <- seq_len(nrow(cyto))
  names(aliases) <- cyto$Chr
  rc.plot.ideogram(1:2, plot.band = FALSE, plot.chromosome.id = TRUE,
                   cex.text = 0.72, chrom.alias = aliases,
                   track.border = NA, polygon.border = NA)

  rank_data <- data.frame(cyto[, c("Chr", "Start", "End")], Score = modules$Score)
  rc.plot.histogram(rank_data, track.id = 4, data.col = "Score",
                    custom.track.height = params$track.height * 3,
                    track.border = NA, polygon.border = NA)

  track_border <- "#B8B8B8"
  track_color <- "white"
  track_num <- 4L
  for (cor_col in grep("Rho", names(modules), value = TRUE)) {
    track_num <- track_num + 1L
    hist_data <- data.frame(Chr = modules$id, Start = 1, End = 100,
                            Data = modules[[cor_col]])
    positive <- hist_data[hist_data$Data > 0, ]
    positive$Color <- brown(n_col)[pmax(1, floor(positive$Data * n_col))]
    rc.plot.histogram(positive, track_num, data.col = "Data", color.col = "Color",
                      fixed.height = TRUE, track.color = track_color,
                      track.border = track_border, polygon.border = NA)
    negative <- hist_data[hist_data$Data <= 0, ]
    negative$Data <- abs(negative$Data)
    negative$Color <- blue(n_col)[pmax(1, floor(negative$Data * n_col))]
    rc.plot.histogram(negative, track_num, data.col = "Data", color.col = "Color",
                      fixed.height = TRUE, track.border = track_border,
                      polygon.border = NA)
  }

  track_num <- track_num + 1L
  enrichment <- t(modules[, grep("Enrichment.*Pvalue", names(modules))])
  colnames(enrichment) <- modules$id
  enrichment[,] <- as.integer(-log10(enrichment + 1e-320))
  enrichment[enrichment > 25] <- 25
  rc.plot.heatmap(enrichment, track_num, color.gradient = heat(n_col),
                  track.color = track_color, track.border = track_border,
                  polygon.border = NA)
  track_num <- track_num + nrow(enrichment)

  y <- rc.get.coordinates(1, 1, 1)$y[1] - 1
  x <- params$radius * 0.8
  rc.plot.grColLegend(x, y, brown(n_col), at = c(1, 25, 50),
                      legend = c(0, 0.5, 1), title = expression(italic(r)),
                      width = 0.18, height = 0.52, cex.text = 0.62)
  rc.plot.grColLegend(x, y - 0.52, rev(blue(n_col)), at = c(1, 25),
                      legend = c(-1, -0.5), title = "",
                      width = 0.18, height = 0.52, cex.text = 0.62)
  rc.plot.grColLegend(x + 0.75, y - 0.52, heat(n_col), at = c(1, 25, 50),
                      legend = c(0, 12.5, 25), title = expression(-log[10](P)),
                      width = 0.18, height = 1.04, cex.text = 0.62)
  rc.plot.track.id(4, labels = 1, col = "black",
                   custom.track.height = params$track.height * 2, cex = 0.65)
  rc.plot.track.id(seq(7, track_num - 1, by = 3),
                   labels = seq(7, track_num - 1, by = 3) - 3,
                   col = "black", cex = 0.58)
  title("Coexpression module features", line = -1.5, cex.main = 1.15)
}

plot_donut <- function() {
  values <- c(Perl = 0.20, Bash = 0.30, Python = 0.10,
              Mathematica = 0.10, MySQL = 0.15, LaTeX = 0.15) * 100
  colors <- hcl.colors(length(values) + 1L, "Dark 3")
  cyto <- data.frame(Chr = names(values), Start = 1, End = values,
                     BandColor = colors[seq_along(values)])

  rc.initialize(cyto, num.tracks = 3,
                params = list(chr.padding = 0.1, track.padding = 0,
                              track.height = 0.29))
  rc.plot.area()
  rc.plot.histogram(cyto, track.id = 2, color.col = "BandColor",
                    track.border = NA, polygon.border = NA)
  labels <- data.frame(Chr = cyto$Chr, Pos = cyto$End / 2, Label = names(values))
  rc.plot.text(labels, track.id = 2.5, col = "white", cex = 0.72)
  symbols(0, 0, circles = 0.4, inches = FALSE, add = TRUE,
          bg = colors[length(colors)], fg = NA)
  text(0, 0, labels = "R", cex = 2.5, col = "white", font = 2)
  title("NetWeaver donut chart", line = -1.5, cex.main = 1.15)
}

save_png("netweaver_plotting_primitives.png", plot_primitives)
save_png("netweaver_module_features.png", plot_modules, width = 2600L, res = 240L)
save_png("netweaver_donut.png", plot_donut, width = 1800L, res = 220L)

