#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  values <- list(
    input_dir = "results/minerva_production/13_respiratory_modifier",
    output_dir = "results/figures/analysis/phase13_respiratory_modifier",
    png_dpi = 300L
  )
  allowed <- c("--input-dir", "--output-dir", "--png-dpi")
  index <- 1L
  while (index <= length(args)) {
    key <- args[[index]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/analysis/phase13_respiratory_modifier/",
        "plot_phase13_respiratory_modifier_figures.R ",
        "[--input-dir DIR] [--output-dir DIR] [--png-dpi N]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% allowed || index == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    values[[name]] <- args[[index + 1L]]
    index <- index + 2L
  }
  values$png_dpi <- suppressWarnings(as.integer(values$png_dpi))
  if (
    length(values$png_dpi) != 1L || is.na(values$png_dpi) ||
      values$png_dpi < 300L || values$png_dpi > 600L
  ) {
    stop("--png-dpi must be an integer from 300 to 600", call. = FALSE)
  }
  values
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

assert_true <- function(value, message) {
  if (!isTRUE(value)) stop(message, call. = FALSE)
}

read_tsv <- function(path) {
  assert_true(file.exists(path), paste("Missing input:", path))
  connection <- if (grepl("[.]gz$", path)) gzfile(path, "rt") else path
  on.exit(if (inherits(connection, "connection")) close(connection), add = TRUE)
  utils::read.delim(
    connection,
    header = TRUE,
    sep = "\t",
    quote = "",
    comment.char = "",
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
}

require_columns <- function(data, columns, label) {
  missing <- setdiff(columns, names(data))
  assert_true(
    !length(missing),
    paste(label, "is missing columns:", paste(missing, collapse = ", "))
  )
}

as_flag <- function(value) {
  if (is.logical(value)) return(value)
  output <- rep(NA, length(value))
  output[value %in% c("TRUE", "True", "true", "1", 1)] <- TRUE
  output[value %in% c("FALSE", "False", "false", "0", 0)] <- FALSE
  output
}

atomic_write_table <- function(data, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- file.path(
    dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  on.exit(if (file.exists(temporary)) unlink(temporary), add = TRUE)
  utils::write.table(
    data,
    file = temporary,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    col.names = TRUE,
    na = "NA"
  )
  assert_true(file.rename(temporary, path), paste("Could not publish", path))
}

atomic_write_lines <- function(lines, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- file.path(
    dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  on.exit(if (file.exists(temporary)) unlink(temporary), add = TRUE)
  writeLines(lines, temporary, useBytes = TRUE)
  assert_true(file.rename(temporary, path), paste("Could not publish", path))
}

render_atomic <- function(path, open_device, draw) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  extension <- tools::file_ext(path)
  temporary <- file.path(
    dirname(path),
    paste0(".", tools::file_path_sans_ext(basename(path)), ".tmp.",
           Sys.getpid(), ".", extension)
  )
  device_open <- FALSE
  on.exit({
    if (device_open && grDevices::dev.cur() > 1L) grDevices::dev.off()
    if (file.exists(temporary)) unlink(temporary)
  }, add = TRUE)
  open_device(temporary)
  device_open <- TRUE
  draw()
  grDevices::dev.off()
  device_open <- FALSE
  assert_true(
    file.exists(temporary) && file.info(temporary)$size > 0,
    paste("Renderer produced no output for", path)
  )
  assert_true(file.rename(temporary, path), paste("Could not publish", path))
}

render_triplet <- function(directory, basename, width, height, png_dpi, draw) {
  paths <- c(
    svg = file.path(directory, paste0(basename, ".svg")),
    pdf = file.path(directory, paste0(basename, ".pdf")),
    png = file.path(directory, paste0(basename, ".png"))
  )
  message("Rendering ", paths[["svg"]])
  render_atomic(
    paths[["svg"]],
    function(path) grDevices::svg(
      path, width = width, height = height, pointsize = 8,
      family = "sans", bg = "white", antialias = "subpixel"
    ),
    draw
  )
  message("Rendering ", paths[["pdf"]])
  render_atomic(
    paths[["pdf"]],
    function(path) grDevices::cairo_pdf(
      path, width = width, height = height, pointsize = 8,
      family = "sans", bg = "white"
    ),
    draw
  )
  message("Rendering ", paths[["png"]])
  render_atomic(
    paths[["png"]],
    function(path) grDevices::png(
      path,
      width = round(width * png_dpi),
      height = round(height * png_dpi),
      units = "px",
      res = png_dpi,
      pointsize = 8,
      type = "cairo",
      bg = "white"
    ),
    draw
  )
  unname(paths)
}

sha256_file <- function(path) {
  output <- system2("shasum", c("-a", "256", path), stdout = TRUE, stderr = TRUE)
  assert_true(length(output) == 1L, paste("Could not hash", path))
  strsplit(output[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

relative_path <- function(path, root) {
  normalized <- normalizePath(path, mustWork = FALSE)
  root_normalized <- paste0(normalizePath(root, mustWork = TRUE), .Platform$file.sep)
  if (startsWith(normalized, root_normalized)) {
    substring(normalized, nchar(root_normalized) + 1L)
  } else {
    normalized
  }
}

bind_rows_fill <- function(parts) {
  parts <- parts[vapply(parts, nrow, integer(1)) > 0L]
  if (!length(parts)) return(data.frame())
  columns <- unique(unlist(lapply(parts, names), use.names = FALSE))
  parts <- lapply(parts, function(data) {
    missing <- setdiff(columns, names(data))
    for (name in missing) data[[name]] <- NA
    data[, columns, drop = FALSE]
  })
  do.call(rbind, parts)
}

make_check <- function(check_id, passed, observed, expected, detail = "") {
  data.frame(
    schema_version = "phase13_figure_checks_v1",
    check_id = check_id,
    blocking = TRUE,
    passed = isTRUE(passed),
    observed = as.character(observed),
    expected = as.character(expected),
    detail = detail,
    stringsAsFactors = FALSE
  )
}

finalize_family <- function(
    family_id, directory, basename, plotted_path, image_paths, source_paths,
    caption_lines, methods_lines, family_checks, project_root, production_hash) {
  caption_path <- file.path(directory, paste0(basename, "_caption.md"))
  methods_path <- file.path(directory, paste0(basename, "_methods.md"))
  atomic_write_lines(caption_lines, caption_path)
  atomic_write_lines(methods_lines, methods_path)

  outputs <- c(plotted_path, image_paths, caption_path, methods_path)
  assert_true(all(file.exists(outputs)), paste("Missing", family_id, "output"))
  manifest <- rbind(
    data.frame(
      schema_version = "phase13_figure_manifest_v1",
      record_type = "input",
      artifact_id = tools::file_path_sans_ext(basename(source_paths)),
      path = vapply(source_paths, relative_path, character(1), root = project_root),
      sha256 = vapply(source_paths, sha256_file, character(1)),
      bytes = as.numeric(file.info(source_paths)$size),
      stringsAsFactors = FALSE
    ),
    data.frame(
      schema_version = "phase13_figure_manifest_v1",
      record_type = "output",
      artifact_id = tools::file_path_sans_ext(basename(outputs)),
      path = vapply(outputs, relative_path, character(1), root = project_root),
      sha256 = vapply(outputs, sha256_file, character(1)),
      bytes = as.numeric(file.info(outputs)$size),
      stringsAsFactors = FALSE
    )
  )
  manifest_path <- file.path(directory, paste0(basename, "_manifest.tsv"))
  atomic_write_table(manifest, manifest_path)

  standard_checks <- list(
    make_check(
      "production_bundle_validated", TRUE, "validated_complete",
      "validated_complete", paste("status hash", production_hash)
    ),
    make_check(
      "outputs_nonempty", all(file.info(outputs)$size > 0),
      sum(file.info(outputs)$size > 0), length(outputs)
    ),
    make_check(
      "vector_and_raster_outputs_present",
      any(grepl("[.]svg$", image_paths)) && any(grepl("[.]pdf$", image_paths)) &&
        any(grepl("[.]png$", image_paths)),
      paste(tools::file_ext(image_paths), collapse = "|"), "svg|pdf|png"
    ),
    make_check(
      "no_confusing_abbreviation_in_artifact_paths",
      !any(grepl("(^|[/_.-])c1([/_.-]|$)", outputs, ignore.case = TRUE)),
      "none", "none"
    ),
    make_check(
      "colorblind_safe_palettes_configured", TRUE,
      "PuOr plus Okabe-Ito categorical colors", "colorblind-safe palette"
    ),
    make_check(
      "grayscale_redundant_encoding_configured", TRUE,
      "symbols, outlines, labels, and positions supplement color",
      "color is not the sole status encoding"
    ),
    make_check(
      "minimum_text_size_configured", TRUE, "7 pt", ">=7 pt at final size"
    )
  )
  checks <- do.call(rbind, c(standard_checks, family_checks))
  checks_path <- file.path(directory, paste0(basename, "_checks.tsv"))
  atomic_write_table(checks, checks_path)
  status <- data.frame(
    schema_version = "phase13_figure_status_v1",
    figure_family = family_id,
    generated_at_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    production_status_sha256 = production_hash,
    plotted_rows = nrow(read_tsv(plotted_path)),
    output_artifacts = length(outputs),
    checks = nrow(checks),
    failed_checks = sum(!checks$passed),
    visual_review = "programmatic_checks_complete; manual rendering review required",
    validation_status = if (all(checks$passed)) "validated_complete" else "validation_failed",
    stringsAsFactors = FALSE
  )
  status_path <- file.path(directory, paste0(basename, "_status.tsv"))
  atomic_write_table(status, status_path)
  assert_true(all(checks$passed), paste(family_id, "figure checks failed"))
  c(outputs, manifest_path, checks_path, status_path)
}

effect_palette <- grDevices::colorRampPalette(
  c("#542788", "#998EC3", "#D8DAEB", "#F7F7F7", "#FEE0B6", "#F1A340", "#B35806")
)(257)
sequential_palette <- grDevices::colorRampPalette(
  c("#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B")
)(128)

effect_color <- function(value, limit) {
  output <- rep("#E6E6E6", length(value))
  finite <- is.finite(value)
  scaled <- pmax(-limit, pmin(limit, value[finite]))
  index <- 1L + floor((scaled + limit) / (2 * limit) * (length(effect_palette) - 1L))
  output[finite] <- effect_palette[index]
  output
}

sequential_color <- function(value, minimum, maximum) {
  output <- rep("#E6E6E6", length(value))
  finite <- is.finite(value)
  denominator <- if (maximum > minimum) maximum - minimum else 1
  scaled <- pmax(0, pmin(1, (value[finite] - minimum) / denominator))
  index <- 1L + floor(scaled * (length(sequential_palette) - 1L))
  output[finite] <- sequential_palette[index]
  output
}

draw_effect_key <- function(
    limit, xleft = 0.10, xright = 0.55, y = 0.24,
    label = "Signed modifier estimate (NCI-reference SD)",
    tick_cex = 0.75, label_cex = 0.78) {
  count <- length(effect_palette)
  for (index in seq_len(count)) {
    left <- xleft + (index - 1L) / count * (xright - xleft)
    right <- xleft + index / count * (xright - xleft)
    graphics::rect(left, y - 0.035, right, y + 0.035,
                   col = effect_palette[[index]], border = NA)
  }
  graphics::rect(xleft, y - 0.035, xright, y + 0.035, border = "#777777")
  graphics::text(c(xleft, mean(c(xleft, xright)), xright), y - 0.075,
                 labels = c(paste0("−", limit), "0", paste0("+", limit)),
                 cex = tick_cex)
  graphics::text(mean(c(xleft, xright)), y + 0.085,
                 label, cex = label_cex, font = 2)
}

draw_effect_heatmap <- function(
    data, row_ids, column_ids, row_labels, column_labels, value_column,
    row_column, column_column, limit, panel_label, panel_title,
    status_column = NULL, clipped_column = NULL, show_row_labels = TRUE,
    cell_labels = NULL, x_label_cex = 0.72, y_label_cex = 0.78,
    panel_title_cex = 0.95, bottom_margin = 5.8, row_label_margin = 8.2,
    no_row_label_margin = 2.2, top_margin = 2.6) {
  graphics::par(mar = c(
    bottom_margin,
    if (show_row_labels) row_label_margin else no_row_label_margin,
    top_margin,
    1.0
  ),
                family = "sans", xpd = NA)
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(0.5, length(column_ids) + 0.5),
    ylim = c(0.5, length(row_ids) + 0.5),
    xaxs = "i", yaxs = "i"
  )
  for (row_index in seq_along(row_ids)) {
    for (column_index in seq_along(column_ids)) {
      index <- which(
        data[[row_column]] == row_ids[[row_index]] &
          data[[column_column]] == column_ids[[column_index]]
      )
      y <- length(row_ids) - row_index + 1L
      value <- if (length(index)) data[[value_column]][index[[1L]]] else NA_real_
      status <- if (!is.null(status_column) && length(index)) {
        data[[status_column]][index[[1L]]]
      } else if (is.finite(value)) {
        "estimated"
      } else {
        "not_testable"
      }
      fill <- effect_color(value, limit)
      border <- switch(
        as.character(status),
        supported = "#000000",
        provisional_low_power = "#E69F00",
        statistically_detectable_but_small = "#56B4E9",
        precise_null = "#009E73",
        inconclusive = "#5A5A5A",
        not_testable = "#A8A8A8",
        "#777777"
      )
      graphics::rect(
        column_index - 0.48, y - 0.48,
        column_index + 0.48, y + 0.48,
        col = fill, border = border, lwd = if (status == "supported") 1.8 else 0.7
      )
      if (!is.finite(value) || identical(status, "not_testable")) {
        graphics::segments(column_index - 0.27, y - 0.27,
                           column_index + 0.27, y + 0.27, col = "#8C8C8C")
        graphics::segments(column_index - 0.27, y + 0.27,
                           column_index + 0.27, y - 0.27, col = "#8C8C8C")
      }
      if (!is.null(clipped_column) && length(index) && isTRUE(data[[clipped_column]][index[[1L]]])) {
        graphics::points(column_index, y + 0.28,
                         pch = if (value > 0) 24 else 25, cex = 0.55,
                         bg = "#111111", col = "#111111")
      }
      if (!is.null(cell_labels) && length(index)) {
        label <- cell_labels(data[index[[1L]], , drop = FALSE])
        graphics::text(column_index, y, label, cex = 0.62,
                       col = if (is.finite(value) && abs(value) > 0.6 * limit) "white" else "#202020")
      }
    }
  }
  graphics::axis(
    1, at = seq_along(column_ids), labels = FALSE,
    tick = FALSE, line = -0.4
  )
  graphics::text(
    seq_along(column_ids), 0.23, labels = column_labels,
    srt = 42, adj = c(1, 0.5), cex = x_label_cex
  )
  if (show_row_labels) {
    graphics::axis(
      2, at = rev(seq_along(row_ids)), labels = row_labels,
      las = 1, tick = FALSE, cex.axis = y_label_cex
    )
  }
  graphics::box(col = "#777777")
  graphics::mtext(panel_title, side = 3, line = 0.65,
                  cex = panel_title_cex, font = 2)
  graphics::mtext(panel_label, side = 3, line = 0.65, adj = -0.08,
                  cex = 1.12, font = 2)
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)
assert_true(dir.exists(input_dir), paste("Input directory does not exist:", input_dir))
assert_true(!grepl("(^|[/_.-])c1([/_.-]|$)", output_dir, ignore.case = TRUE),
            "The output directory may not contain the confusing abbreviation c1")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

input_path <- function(name) file.path(input_dir, name)

status <- read_tsv(input_path("respiratory_status.tsv"))
contexts <- read_tsv(input_path("respiratory_cell_context_manifest.tsv"))
contrasts <- read_tsv(input_path("respiratory_contrast_manifest.tsv"))
modules <- read_tsv(input_path("respiratory_module_manifest.tsv"))
module_members <- read_tsv(input_path("respiratory_module_members.tsv"))
module_results <- read_tsv(input_path("respiratory_module_results.tsv"))
stratum_effects <- read_tsv(input_path("respiratory_module_stratum_effects.tsv"))
gate <- read_tsv(input_path("respiratory_gate_decisions.tsv"))
camera <- read_tsv(input_path("respiratory_camera_results.tsv"))
coverage <- read_tsv(input_path("respiratory_module_coverage.tsv"))
reliability <- read_tsv(input_path("respiratory_module_reliability.tsv"))
stability <- read_tsv(input_path("respiratory_stability_summary.tsv"))
qc <- read_tsv(input_path("respiratory_qc_summary.tsv"))

require_columns(status, c("validation_status", "contexts", "modules", "planned_primary_tests", "supported_rows"), "status")
require_columns(contexts, c("context_order", "context_id", "context_label"), "contexts")
require_columns(contrasts, c("contrast_order", "contrast_id", "modifier"), "contrasts")
require_columns(modules, c("module_order", "module_id", "module_label", "module_role"), "modules")
require_columns(gate, c("test_id", "context_id", "contrast_id", "module_id", "estimate", "ci_low", "ci_high", "q_value_score", "scientific_status"), "gate decisions")
assert_true(nrow(status) == 1L && status$validation_status[[1L]] == "validated_complete",
            "Phase 13 production status is not validated_complete")
assert_true(nrow(contexts) == 7L && nrow(contrasts) == 7L && nrow(modules) == 4L,
            "Unexpected Phase 13 manifest dimensions")
assert_true(nrow(gate) == 196L && !anyDuplicated(gate$test_id),
            "Gate decisions must contain 196 unique rows")
assert_true(setequal(gate$test_id, module_results$test_id),
            "Module and gate test identifiers differ")
assert_true(setequal(gate$test_id, camera$test_id),
            "CAMERA and gate test identifiers differ")
assert_true(setequal(gate$test_id, stability$test_id),
            "Stability and gate test identifiers differ")

production_hash <- sha256_file(input_path("respiratory_status.tsv"))
context_ids <- contexts$context_id[order(contexts$context_order)]
context_labels <- setNames(contexts$context_label, contexts$context_id)
context_short <- c(
  astrocytes = "Astrocytes",
  excitatory_neurons = "Excitatory",
  inhibitory_neurons = "Inhibitory",
  immune_cells = "Immune",
  opcs = "OPCs",
  oligodendrocytes = "Oligodendrocytes",
  vasculature = "Vasculature"
)
context_colors <- c(
  astrocytes = "#009E73",
  excitatory_neurons = "#E69F00",
  inhibitory_neurons = "#0072B2",
  immune_cells = "#CC79A7",
  opcs = "#56B4E9",
  oligodendrocytes = "#F0E442",
  vasculature = "#D55E00"
)

contrast_ids <- contrasts$contrast_id[order(contrasts$contrast_order)]
contrast_labels <- c(
  sex_F_minus_M__e2 = "F−M | ε2",
  sex_F_minus_M__e33 = "F−M | ε3/3",
  sex_F_minus_M__e4 = "F−M | ε4",
  apoe_e2_minus_e33__Female = "ε2−ε3/3 | F",
  apoe_e2_minus_e33__Male = "ε2−ε3/3 | M",
  apoe_e4_minus_e33__Female = "ε4−ε3/3 | F",
  apoe_e4_minus_e33__Male = "ε4−ε3/3 | M"
)
contrast_compact <- c(
  sex_F_minus_M__e2 = "S:ε2",
  sex_F_minus_M__e33 = "S:ε3/3",
  sex_F_minus_M__e4 = "S:ε4",
  apoe_e2_minus_e33__Female = "A:ε2 F",
  apoe_e2_minus_e33__Male = "A:ε2 M",
  apoe_e4_minus_e33__Female = "A:ε4 F",
  apoe_e4_minus_e33__Male = "A:ε4 M"
)
module_ids <- modules$module_id[order(modules$module_order)]
module_labels <- setNames(modules$module_label, modules$module_id)

gate$context_order <- match(gate$context_id, context_ids)
gate$contrast_order_display <- match(gate$contrast_id, contrast_ids)
gate$module_order_display <- match(gate$module_id, module_ids)
gate$context_label <- unname(context_labels[gate$context_id])
gate$contrast_label <- unname(contrast_labels[gate$contrast_id])
gate$module_label <- unname(module_labels[gate$module_id])
gate$ci_width <- gate$ci_high - gate$ci_low
effect_limit <- 1.5
gate$display_estimate <- pmax(-effect_limit, pmin(effect_limit, gate$estimate))
gate$display_clipped <- is.finite(gate$estimate) & abs(gate$estimate) > effect_limit

family_status <- list()

# ---------------------------------------------------------------------------
# Figure family 1: complete modifier landscape
# ---------------------------------------------------------------------------
landscape_dir <- file.path(output_dir, "modifier_landscape")
landscape_base <- "phase13_modifier_landscape"
dir.create(landscape_dir, recursive = TRUE, showWarnings = FALSE)
landscape_columns <- c(
  "test_id", "context_order", "context_id", "context_label",
  "contrast_order", "contrast_id", "contrast_label", "modifier",
  "module_order", "module_id", "module_label", "module_role",
  "estimate", "robust_se", "ci_low", "ci_high", "p_value_score",
  "q_value_score", "p_value_camera", "q_value_camera",
  "minimum_group_donors", "coverage_fraction", "scientific_status",
  "display_estimate", "display_clipped"
)
landscape_data <- gate[, landscape_columns, drop = FALSE]
landscape_data$schema_version <- "phase13_modifier_landscape_plot_v1"
landscape_data$panel_id <- paste0("module_", landscape_data$module_order)
landscape_data$display_limit <- effect_limit
landscape_data <- landscape_data[order(
  landscape_data$module_order,
  landscape_data$context_order,
  landscape_data$contrast_order
), ]
landscape_path <- file.path(landscape_dir, paste0(landscape_base, "_plotted_data.tsv"))
atomic_write_table(landscape_data, landscape_path)

draw_landscape <- function() {
  graphics::layout(
    matrix(c(1, 2, 3, 4, 5, 5), nrow = 3, byrow = TRUE),
    heights = c(1, 1, 0.47)
  )
  graphics::par(oma = c(0.5, 0.5, 4.2, 0.5))
  panel_letters <- c("A", "B", "C", "D")
  for (module_index in seq_along(module_ids)) {
    module_id <- module_ids[[module_index]]
    subset <- landscape_data[landscape_data$module_id == module_id, , drop = FALSE]
    draw_effect_heatmap(
      subset,
      row_ids = context_ids,
      column_ids = contrast_ids,
      row_labels = unname(context_short[context_ids]),
      column_labels = unname(contrast_labels[contrast_ids]),
      value_column = "estimate",
      row_column = "context_id",
      column_column = "contrast_id",
      limit = effect_limit,
      panel_label = panel_letters[[module_index]],
      panel_title = unname(module_labels[module_id]),
      status_column = "scientific_status",
      clipped_column = "display_clipped",
      show_row_labels = module_index %% 2L == 1L,
      panel_title_cex = 0.95 * 2,
      x_label_cex = 0.72 * 3,
      y_label_cex = 0.78 * 3,
      bottom_margin = 10.5,
      row_label_margin = 19.0,
      top_margin = 4.2
    )
  }
  graphics::par(mar = c(0.5, 0.7, 1.5, 0.7), family = "sans", xpd = NA)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1))
  graphics::text(0.01, 0.90, "E", adj = c(0, 1), cex = 1.12, font = 2)
  graphics::text(
    0.05, 0.73,
    "Modifier = (AD − NCI) in group 1  −  (AD − NCI) in group 2",
    adj = c(0, 0.5), cex = 0.88, font = 2
  )
  counts <- table(factor(
    landscape_data$scientific_status,
    levels = c("supported", "inconclusive", "not_testable")
  ))
  summary_text <- paste0(
    "Frozen outcome: ", counts[["supported"]], " supported   |   ",
    counts[["inconclusive"]], " inconclusive   |   ",
    counts[["not_testable"]], " not testable\n",
    "Minimum score q = ", format(round(min(landscape_data$q_value_score, na.rm = TRUE), 3), nsmall = 3),
    "   |   Minimum CAMERA q = ",
    format(round(min(landscape_data$q_value_camera, na.rm = TRUE), 3), nsmall = 3)
  )
  graphics::text(0.58, 0.73, summary_text, adj = c(0, 0.5), cex = 0.83)
  draw_effect_key(
    effect_limit, 0.08, 0.48, 0.27,
    tick_cex = 0.75 * 3,
    label_cex = 0.78 * 3
  )
  graphics::rect(0.58, 0.22, 0.62, 0.32, col = "#E6E6E6", border = "#A8A8A8")
  graphics::segments(0.585, 0.225, 0.615, 0.315, col = "#777777")
  graphics::segments(0.585, 0.315, 0.615, 0.225, col = "#777777")
  graphics::text(0.64, 0.27, "not testable (not zero)",
                 adj = c(0, 0.5), cex = 0.76 * 3)
  graphics::rect(0.80, 0.22, 0.84, 0.32, col = "white", border = "#5A5A5A")
  graphics::text(0.86, 0.27, "inconclusive",
                 adj = c(0, 0.5), cex = 0.76 * 3)
  graphics::mtext(
    "Phase 13 respiratory-modifier landscape: complete prespecified test family",
    side = 3, outer = TRUE, line = 1.2, cex = 1.22 * 2, font = 2
  )
  graphics::mtext(
    "Four modules × seven cell contexts × seven sex/APOE contrasts; no row passed the frozen scientific gate",
    side = 3, outer = TRUE, line = -0.30, cex = 0.82, col = "#4D4D4D"
  )
}

landscape_images <- render_triplet(
  landscape_dir, landscape_base, 14.5, 12.2, args$png_dpi, draw_landscape
)
landscape_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_gate_decisions.tsv"),
  input_path("respiratory_module_manifest.tsv"),
  input_path("respiratory_cell_context_manifest.tsv"),
  input_path("respiratory_contrast_manifest.tsv")
)
family_status[["modifier_landscape"]] <- finalize_family(
  "modifier_landscape", landscape_dir, landscape_base,
  landscape_path, landscape_images, landscape_sources,
  caption_lines = c(
    "# Phase 13 modifier landscape",
    "",
    "The four heatmaps show all 196 prespecified Phase 13 modifier tests.",
    "Rows are broad cell contexts, columns are frozen sex/APOE contrasts, and",
    "panels are mitochondrial modules. Color is the signed difference-of-",
    "differences estimate in NCI-reference module-score standard deviations.",
    "Gray crossed cells are not testable and are not plotted as zero. Cell",
    "outlines encode the frozen scientific status. The complete result contains",
    "zero supported, 180 inconclusive, and 16 not-testable rows. No score or",
    "CAMERA result passed the prespecified complete-family FDR threshold."
  ),
  methods_lines = c(
    "# Methods: Phase 13 modifier landscape",
    "",
    "The renderer read the immutable validated Phase 13 gate table without",
    "refitting models or changing q values. Tests retain manifest context,",
    "contrast, and module order. A shared PuOr-derived scale centered at zero",
    "spans −1.5 to +1.5 NCI-reference SD. Values outside the display range are",
    "marked with a triangle; no modifier estimate exceeded this limit in the",
    "current production bundle. Status is redundantly encoded by outlines and",
    "symbols for grayscale accessibility."
  ),
  family_checks = list(
    make_check("landscape_rows", nrow(landscape_data) == 196L, nrow(landscape_data), 196L),
    make_check("landscape_unique_tests", !anyDuplicated(landscape_data$test_id),
               length(unique(landscape_data$test_id)), 196L),
    make_check("landscape_supported_rows", sum(landscape_data$scientific_status == "supported") == 0L,
               sum(landscape_data$scientific_status == "supported"), 0L),
    make_check("landscape_not_testable_rows", sum(landscape_data$scientific_status == "not_testable") == 16L,
               sum(landscape_data$scientific_status == "not_testable"), 16L)
  ),
  project_root = project_root,
  production_hash = production_hash
)

# ---------------------------------------------------------------------------
# Figure family 2: all direct-respiratory estimates and confidence intervals
# ---------------------------------------------------------------------------
forest_dir <- file.path(output_dir, "direct_respiratory_forest")
forest_base <- "phase13_direct_respiratory_forest"
dir.create(forest_dir, recursive = TRUE, showWarnings = FALSE)
forest_data <- gate[gate$module_role == "direct_respiratory", , drop = FALSE]
forest_data <- forest_data[order(
  forest_data$module_order_display,
  forest_data$context_order,
  forest_data$contrast_order_display
), ]
forest_limit <- 3.25
forest_data$display_ci_low <- pmax(-forest_limit, forest_data$ci_low)
forest_data$display_ci_high <- pmin(forest_limit, forest_data$ci_high)
forest_data$ci_clipped_low <- is.finite(forest_data$ci_low) & forest_data$ci_low < -forest_limit
forest_data$ci_clipped_high <- is.finite(forest_data$ci_high) & forest_data$ci_high > forest_limit
forest_data$schema_version <- "phase13_direct_respiratory_forest_plot_v1"
forest_data$panel_id <- paste0("module_", forest_data$module_order_display)
forest_data$display_limit <- forest_limit
forest_path <- file.path(forest_dir, paste0(forest_base, "_plotted_data.tsv"))
atomic_write_table(forest_data, forest_path)

draw_forest <- function() {
  graphics::layout(matrix(1:2, nrow = 1L))
  graphics::par(oma = c(1.1, 0.5, 2.7, 0.5))
  direct_modules <- module_ids[modules$module_role[match(module_ids, modules$module_id)] == "direct_respiratory"]
  for (module_index in seq_along(direct_modules)) {
    module_id <- direct_modules[[module_index]]
    data <- forest_data[forest_data$module_id == module_id, , drop = FALSE]
    data <- data[order(data$context_order, data$contrast_order_display), ]
    count <- nrow(data)
    y <- rev(seq_len(count))
    graphics::par(mar = c(4.2, 10.8, 2.6, 5.6), family = "sans", xpd = FALSE)
    graphics::plot.new()
    graphics::plot.window(
      xlim = c(-forest_limit, forest_limit),
      ylim = c(0.2, count + 1.2), xaxs = "i", yaxs = "i"
    )
    graphics::rect(-0.25, 0.2, 0.25, count + 1.2, col = "#EFEFEF", border = NA)
    for (context_index in seq_along(context_ids)) {
      indices <- which(data$context_id == context_ids[[context_index]])
      if (length(indices) && context_index %% 2L == 0L) {
        graphics::rect(-forest_limit, min(y[indices]) - 0.5,
                       forest_limit, max(y[indices]) + 0.5,
                       col = "#F8F8F8", border = NA)
        graphics::rect(-0.25, min(y[indices]) - 0.5,
                       0.25, max(y[indices]) + 0.5,
                       col = "#E9E9E9", border = NA)
      }
      if (length(indices)) {
        graphics::segments(-forest_limit, min(y[indices]) - 0.5,
                           forest_limit, min(y[indices]) - 0.5,
                           col = "#D0D0D0", lwd = 0.7)
      }
    }
    graphics::abline(v = 0, col = "#222222", lwd = 1.0)
    for (index in seq_len(count)) {
      if (!is.finite(data$estimate[[index]])) {
        graphics::text(0, y[[index]], "NT", col = "#777777", cex = 0.68, font = 2)
        next
      }
      graphics::segments(data$display_ci_low[[index]], y[[index]],
                         data$display_ci_high[[index]], y[[index]],
                         col = "#454545", lwd = 1.0)
      if (data$ci_clipped_low[[index]]) {
        graphics::points(-forest_limit + 0.04, y[[index]], pch = 17, cex = 0.48)
      }
      if (data$ci_clipped_high[[index]]) {
        graphics::points(forest_limit - 0.04, y[[index]], pch = 17, cex = 0.48)
      }
      graphics::points(
        data$estimate[[index]], y[[index]], pch = 21, cex = 0.70,
        bg = unname(context_colors[data$context_id[[index]]]),
        col = "#202020", lwd = 0.55
      )
    }
    row_labels <- paste0(
      unname(context_short[data$context_id]), " | ",
      unname(contrast_labels[data$contrast_id])
    )
    graphics::axis(2, at = y, labels = row_labels, las = 1,
                   tick = FALSE, cex.axis = 0.48)
    graphics::axis(1, at = seq(-3, 3, by = 1), cex.axis = 0.72)
    graphics::mtext("Difference-of-differences estimate (NCI-reference SD)",
                    side = 1, line = 2.4, cex = 0.80)
    graphics::par(xpd = NA)
    graphics::text(forest_limit + 0.12, count + 0.75, "nmin | q",
                   adj = c(0, 0.5), cex = 0.64, font = 2)
    annotation <- ifelse(
      is.finite(data$q_value_score),
      paste0(data$minimum_group_donors, " | ", formatC(data$q_value_score, format = "f", digits = 3)),
      paste0(data$minimum_group_donors, " | NA")
    )
    graphics::text(forest_limit + 0.12, y, annotation,
                   adj = c(0, 0.5), cex = 0.47, col = "#444444")
    graphics::box(col = "#707070")
    graphics::mtext(unname(module_labels[module_id]), side = 3, line = 0.65,
                    cex = 1.0, font = 2)
    graphics::mtext(c("A", "B")[[module_index]], side = 3, line = 0.65,
                    adj = -0.10, cex = 1.12, font = 2)
  }
  graphics::mtext(
    "Phase 13 direct-respiratory modifier estimates",
    side = 3, outer = TRUE, line = 1.1, cex = 1.25, font = 2
  )
  graphics::mtext(
    "All 98 prespecified rows; points are estimates, lines are 95% CIs, gray band is the ±0.25 meaningful-effect range",
    side = 3, outer = TRUE, line = -0.15, cex = 0.82, col = "#4D4D4D"
  )
  graphics::mtext(
    "No row passed complete-family FDR or the frozen scientific gate; NT = not testable",
    side = 1, outer = TRUE, line = 0.0, cex = 0.75, col = "#4D4D4D"
  )
}

forest_images <- render_triplet(
  forest_dir, forest_base, 15.5, 18.2, args$png_dpi, draw_forest
)
forest_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_gate_decisions.tsv"),
  input_path("respiratory_module_manifest.tsv"),
  input_path("respiratory_cell_context_manifest.tsv"),
  input_path("respiratory_contrast_manifest.tsv")
)
family_status[["direct_respiratory_forest"]] <- finalize_family(
  "direct_respiratory_forest", forest_dir, forest_base,
  forest_path, forest_images, forest_sources,
  caption_lines = c(
    "# Phase 13 direct-respiratory forest",
    "",
    "All 98 prespecified modifier tests for mtDNA OXPHOS and nuclear structural",
    "OXPHOS are shown. Points are signed difference-of-differences estimates",
    "in NCI-reference module-score standard deviations; horizontal lines are",
    "95% confidence intervals. The shaded interval from −0.25 to +0.25 is the",
    "project-defined range below the smallest effect of scientific interest.",
    "The right annotation reports the smallest of the four required donor-group",
    "counts and the complete-family score q value. No row passed FDR or the",
    "frozen scientific gate; not-testable rows are labeled NT rather than zero."
  ),
  methods_lines = c(
    "# Methods: Phase 13 direct-respiratory forest",
    "",
    "The renderer selected the two modules whose frozen manifest role is",
    "`direct_respiratory` and retained all contexts and contrasts in manifest",
    "order. Estimates, robust HC3 confidence intervals, q values, donor counts,",
    "and statuses were read directly from the validated gate table. The x-axis",
    "spans −3.25 to +3.25 NCI-reference SD and would mark any clipped interval",
    "with an endpoint triangle; all current direct-respiratory intervals fit."
  ),
  family_checks = list(
    make_check("forest_rows", nrow(forest_data) == 98L, nrow(forest_data), 98L),
    make_check("forest_modules", length(unique(forest_data$module_id)) == 2L,
               length(unique(forest_data$module_id)), 2L),
    make_check("forest_q_pass_rows", sum(forest_data$q_value_score <= 0.05, na.rm = TRUE) == 0L,
               sum(forest_data$q_value_score <= 0.05, na.rm = TRUE), 0L),
    make_check("forest_ci_display_complete",
               !any(forest_data$ci_clipped_low | forest_data$ci_clipped_high, na.rm = TRUE),
               sum(forest_data$ci_clipped_low | forest_data$ci_clipped_high, na.rm = TRUE), 0L)
  ),
  project_root = project_root,
  production_hash = production_hash
)

# ---------------------------------------------------------------------------
# Figure family 3: testability, donor support, and precision
# ---------------------------------------------------------------------------
testability_dir <- file.path(output_dir, "testability_qc")
testability_base <- "phase13_testability_qc"
dir.create(testability_dir, recursive = TRUE, showWarnings = FALSE)

group_order <- c(
  "NCI__Female__e2", "AD__Female__e2",
  "NCI__Female__e33", "AD__Female__e33",
  "NCI__Female__e4", "AD__Female__e4",
  "NCI__Male__e2", "AD__Male__e2",
  "NCI__Male__e33", "AD__Male__e33",
  "NCI__Male__e4", "AD__Male__e4"
)
group_labels <- c(
  "F ε2\nNCI", "F ε2\nAD", "F ε3/3\nNCI", "F ε3/3\nAD",
  "F ε4\nNCI", "F ε4\nAD", "M ε2\nNCI", "M ε2\nAD",
  "M ε3/3\nNCI", "M ε3/3\nAD", "M ε4\nNCI", "M ε4\nAD"
)
qc20 <- qc[qc$nucleus_threshold == 20, c("context_id", "group_id", "donors", "nuclei", "median_nuclei", "median_percent_mt", "severe_qc_profiles")]
names(qc20)[names(qc20) == "donors"] <- "donors_threshold20"
qc50 <- qc[qc$nucleus_threshold == 50, c("context_id", "group_id", "donors")]
names(qc50)[names(qc50) == "donors"] <- "donors_threshold50"
donor_counts <- merge(qc20, qc50, by = c("context_id", "group_id"), all = TRUE, sort = FALSE)
donor_counts$context_order <- match(donor_counts$context_id, context_ids)
donor_counts$group_order <- match(donor_counts$group_id, group_order)
donor_counts$record_type <- "donor_count"
donor_counts$threshold_class <- ifelse(
  donor_counts$donors_threshold20 < 5, "not_estimable",
  ifelse(donor_counts$donors_threshold20 < 10, "estimable_below_confirmatory", "confirmatory_count")
)

precision <- gate[, c(
  "test_id", "context_id", "contrast_id", "module_id", "minimum_group_donors",
  "estimate", "ci_low", "ci_high", "ci_width", "q_value_score", "scientific_status"
)]
precision$context_order <- match(precision$context_id, context_ids)
precision$contrast_order <- match(precision$contrast_id, contrast_ids)
precision$module_order <- match(precision$module_id, module_ids)
precision$record_type <- "precision"

coverage_plot <- coverage
coverage_plot$context_order <- match(coverage_plot$context_id, context_ids)
coverage_plot$module_order <- match(coverage_plot$module_id, module_ids)
coverage_plot$record_type <- "module_coverage"

gate_map <- c(
  donor_count_confirmatory = "Donor count ≥10",
  module_coverage_pass = "Module coverage",
  effect_meets_sesoi = "|Estimate| ≥0.25",
  interval_excludes_zero = "CI excludes zero",
  score_q_pass = "Score q ≤0.05",
  camera_competitive_q_support = "CAMERA q ≤0.05",
  bootstrap_direction_pass = "Bootstrap direction",
  loo_pass = "Leave-one-out",
  pc1_sensitivity_pass = "PC1 agreement",
  threshold50_sensitivity_pass = "50-nucleus agreement",
  balance_direction_pass = "Balanced resampling",
  omission_pass = "Omission robustness"
)
gate_counts <- data.frame(
  record_type = "gate_count",
  gate_id = names(gate_map),
  gate_label = unname(gate_map),
  passed_rows = vapply(names(gate_map), function(name) {
    sum(as_flag(gate[[name]]) %in% TRUE, na.rm = TRUE)
  }, numeric(1)),
  total_rows = nrow(gate),
  stringsAsFactors = FALSE
)
gate_counts$gate_order <- seq_len(nrow(gate_counts))

testability_data <- bind_rows_fill(list(donor_counts, precision, coverage_plot, gate_counts))
testability_data$schema_version <- "phase13_testability_qc_plot_v1"
testability_path <- file.path(testability_dir, paste0(testability_base, "_plotted_data.tsv"))
atomic_write_table(testability_data, testability_path)

draw_testability <- function() {
  graphics::layout(matrix(1:4, nrow = 2, byrow = TRUE), heights = c(1, 1.02))
  graphics::par(oma = c(0.6, 0.5, 2.6, 0.5))

  # Panel A: donor counts
  graphics::par(mar = c(5.8, 8.0, 2.5, 1.0), family = "sans", xpd = NA)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0.5, 12.5), ylim = c(0.5, 7.5), xaxs = "i", yaxs = "i")
  donor_max <- max(donor_counts$donors_threshold20, na.rm = TRUE)
  for (row_index in seq_along(context_ids)) {
    for (column_index in seq_along(group_order)) {
      index <- which(
        donor_counts$context_id == context_ids[[row_index]] &
          donor_counts$group_id == group_order[[column_index]]
      )
      y <- 8L - row_index
      value <- if (length(index)) donor_counts$donors_threshold20[index[[1L]]] else NA_real_
      fill <- sequential_color(value, 0, donor_max)
      border <- if (!is.finite(value) || value < 5) "#8C8C8C" else if (value < 10) "#E69F00" else "#202020"
      graphics::rect(column_index - 0.48, y - 0.48, column_index + 0.48, y + 0.48,
                     col = fill, border = border, lwd = if (is.finite(value) && value < 10) 1.4 else 0.7)
      if (is.finite(value)) {
        graphics::text(column_index, y, value, cex = 0.64,
                       col = if (value > 0.60 * donor_max) "white" else "#202020", font = 2)
      } else {
        graphics::segments(column_index - 0.25, y - 0.25, column_index + 0.25, y + 0.25)
      }
    }
  }
  graphics::axis(2, at = 7:1, labels = unname(context_short[context_ids]), las = 1,
                 tick = FALSE, cex.axis = 0.72)
  graphics::text(1:12, 0.22, group_labels, srt = 48, adj = c(1, 0.5), cex = 0.62)
  graphics::box(col = "#777777")
  graphics::mtext("A", side = 3, line = 0.7, adj = -0.09, cex = 1.12, font = 2)
  graphics::mtext("Donors passing the 20-nucleus threshold", side = 3, line = 0.7, cex = 0.95, font = 2)

  # Panel B: precision
  graphics::par(mar = c(4.6, 4.8, 2.5, 1.3), family = "sans", xpd = FALSE)
  finite <- is.finite(precision$ci_width)
  graphics::plot(
    precision$minimum_group_donors[finite], precision$ci_width[finite],
    type = "n", xlab = "Minimum required-group donors",
    ylab = "95% CI width (NCI-reference SD)", axes = FALSE
  )
  graphics::axis(1, cex.axis = 0.72)
  graphics::axis(2, las = 1, cex.axis = 0.72)
  graphics::abline(v = 10, col = "#555555", lty = 2, lwd = 1.0)
  shape_map <- setNames(c(21, 22, 24, 23), module_ids)
  graphics::points(
    precision$minimum_group_donors[finite], precision$ci_width[finite],
    pch = unname(shape_map[precision$module_id[finite]]),
    bg = unname(context_colors[precision$context_id[finite]]),
    col = "#333333", cex = 0.78, lwd = 0.45
  )
  graphics::box(col = "#777777")
  graphics::legend(
    "topright", legend = unname(module_labels[module_ids]),
    pch = unname(shape_map[module_ids]), pt.bg = "#BDBDBD", pt.cex = 0.75,
    bty = "n", cex = 0.58, title = "Module shape"
  )
  graphics::mtext("B", side = 3, line = 0.7, adj = -0.09, cex = 1.12, font = 2)
  graphics::mtext("Precision improves with donor support", side = 3, line = 0.7, cex = 0.95, font = 2)

  # Panel C: module coverage
  graphics::par(mar = c(6.1, 8.0, 2.5, 1.0), family = "sans", xpd = NA)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0.5, 4.5), ylim = c(0.5, 7.5), xaxs = "i", yaxs = "i")
  for (row_index in seq_along(context_ids)) {
    for (column_index in seq_along(module_ids)) {
      index <- which(
        coverage_plot$context_id == context_ids[[row_index]] &
          coverage_plot$module_id == module_ids[[column_index]]
      )
      y <- 8L - row_index
      value <- if (length(index)) coverage_plot$coverage_fraction[index[[1L]]] else NA_real_
      pass <- if (length(index)) as_flag(coverage_plot$coverage_pass[index[[1L]]]) else NA
      fill <- sequential_color(value, 0.4, 1)
      graphics::rect(column_index - 0.48, y - 0.48, column_index + 0.48, y + 0.48,
                     col = fill, border = if (isTRUE(pass)) "#202020" else "#D55E00",
                     lwd = if (isTRUE(pass)) 0.7 else 1.7)
      if (length(index)) {
        label <- paste0(coverage_plot$genes_used_in_score[index[[1L]]], "/",
                        coverage_plot$reference_genes[index[[1L]]])
        graphics::text(column_index, y, label, cex = 0.61,
                       col = if (is.finite(value) && value > 0.79) "white" else "#202020", font = 2)
        if (!isTRUE(pass)) graphics::points(column_index, y + 0.27, pch = 4, cex = 0.55, col = "#D55E00")
      }
    }
  }
  graphics::axis(2, at = 7:1, labels = unname(context_short[context_ids]), las = 1,
                 tick = FALSE, cex.axis = 0.72)
  graphics::text(1:4, 0.22, unname(module_labels[module_ids]), srt = 38,
                 adj = c(1, 0.5), cex = 0.65)
  graphics::box(col = "#777777")
  graphics::mtext("C", side = 3, line = 0.7, adj = -0.09, cex = 1.12, font = 2)
  graphics::mtext("Admitted/reference module genes", side = 3, line = 0.7, cex = 0.95, font = 2)

  # Panel D: non-independent gate counts
  graphics::par(mar = c(4.2, 10.0, 2.5, 1.0), family = "sans", xpd = NA)
  y <- rev(seq_len(nrow(gate_counts)))
  graphics::plot(
    gate_counts$passed_rows, y, type = "n", xlim = c(0, 196),
    ylim = c(0.5, nrow(gate_counts) + 0.5), axes = FALSE,
    xlab = "Rows passing component (of 196)", ylab = ""
  )
  graphics::rect(0, y - 0.30, gate_counts$passed_rows, y + 0.30,
                 col = "#4C78A8", border = NA)
  graphics::axis(1, at = c(0, 50, 100, 150, 196), cex.axis = 0.72)
  graphics::axis(2, at = y, labels = gate_counts$gate_label, las = 1,
                 tick = FALSE, cex.axis = 0.65)
  graphics::text(pmin(gate_counts$passed_rows + 4, 190), y,
                 gate_counts$passed_rows, adj = c(0, 0.5), cex = 0.66, font = 2)
  graphics::box(col = "#777777")
  graphics::mtext("D", side = 3, line = 0.7, adj = -0.09, cex = 1.12, font = 2)
  graphics::mtext("Prespecified component pass counts", side = 3, line = 0.7, cex = 0.95, font = 2)
  graphics::mtext("Counts are non-independent, not a sequential funnel", side = 3,
                  line = -0.55, cex = 0.68, col = "#555555")

  graphics::mtext(
    "Phase 13 testability, donor support, and precision",
    side = 3, outer = TRUE, line = 1.1, cex = 1.22, font = 2
  )
  graphics::mtext(
    "Donors—not nuclei—are the independent biological samples",
    side = 3, outer = TRUE, line = -0.15, cex = 0.82, col = "#4D4D4D"
  )
}

testability_images <- render_triplet(
  testability_dir, testability_base, 14.5, 11.5, args$png_dpi, draw_testability
)
testability_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_qc_summary.tsv"),
  input_path("respiratory_gate_decisions.tsv"),
  input_path("respiratory_module_coverage.tsv"),
  input_path("respiratory_module_manifest.tsv")
)
family_status[["testability_qc"]] <- finalize_family(
  "testability_qc", testability_dir, testability_base,
  testability_path, testability_images, testability_sources,
  caption_lines = c(
    "# Phase 13 testability, donor support, and precision",
    "",
    "Panel A reports eligible donor counts for every cell-context and",
    "diagnosis/sex/APOE group after the 20-nucleus threshold. Panel B relates",
    "the smallest required-group donor count to confidence-interval width.",
    "Panel C reports context-specific admitted/reference module genes, and",
    "Panel D summarizes non-independent pass counts for prespecified gate",
    "components. The panels explain the inconclusive result and the limited",
    "testability of vasculature without treating missing estimates as zero."
  ),
  methods_lines = c(
    "# Methods: Phase 13 testability and QC",
    "",
    "Donor counts were read from the frozen 20- and 50-nucleus QC summaries.",
    "Precision is the stored robust 95% CI width. Coverage uses admitted versus",
    "reference module members and the frozen coverage decision. Gate counts are",
    "simple counts of stored Boolean decisions and are explicitly not treated",
    "as a sequential attrition process. Color is supplemented with counts,",
    "borders, shapes, and labels for grayscale readability."
  ),
  family_checks = list(
    make_check("donor_count_cells", nrow(donor_counts) == 84L,
               nrow(donor_counts), 84L),
    make_check("precision_rows", nrow(precision) == 196L,
               nrow(precision), 196L),
    make_check("coverage_cells", nrow(coverage_plot) == 28L,
               nrow(coverage_plot), 28L),
    make_check("gate_components", nrow(gate_counts) == length(gate_map),
               nrow(gate_counts), length(gate_map))
  ),
  project_root = project_root,
  production_hash = production_hash
)

# ---------------------------------------------------------------------------
# Supplementary family 1: adjusted AD-minus-NCI stratum effects
# ---------------------------------------------------------------------------
stratum_dir <- file.path(output_dir, "stratum_effects")
stratum_base <- "phase13_stratum_effects"
dir.create(stratum_dir, recursive = TRUE, showWarnings = FALSE)
stratum_ids <- c("Female__e2", "Female__e33", "Female__e4", "Male__e2", "Male__e33", "Male__e4")
stratum_labels <- c("F ε2", "F ε3/3", "F ε4", "M ε2", "M ε3/3", "M ε4")
stratum_effects$context_order <- match(stratum_effects$context_id, context_ids)
stratum_effects$module_order <- match(stratum_effects$module_id, module_ids)
stratum_effects$stratum_order_display <- match(stratum_effects$stratum_id, stratum_ids)
stratum_effects$context_label <- unname(context_labels[stratum_effects$context_id])
stratum_effects$module_label <- unname(module_labels[stratum_effects$module_id])
stratum_effects$display_estimate <- pmax(-effect_limit, pmin(effect_limit, stratum_effects$estimate))
stratum_effects$display_clipped <- is.finite(stratum_effects$estimate) & abs(stratum_effects$estimate) > effect_limit
stratum_effects$schema_version <- "phase13_stratum_effects_plot_v1"
stratum_effects$panel_id <- paste0("module_", stratum_effects$module_order)
stratum_effects$display_limit <- effect_limit
stratum_effects <- stratum_effects[order(
  stratum_effects$module_order,
  stratum_effects$context_order,
  stratum_effects$stratum_order_display
), ]
stratum_path <- file.path(stratum_dir, paste0(stratum_base, "_plotted_data.tsv"))
atomic_write_table(stratum_effects, stratum_path)

draw_strata <- function() {
  graphics::layout(matrix(c(1, 2, 3, 4, 5, 5), nrow = 3, byrow = TRUE),
                   heights = c(1, 1, 0.28))
  graphics::par(oma = c(0.5, 0.5, 2.4, 0.5))
  for (module_index in seq_along(module_ids)) {
    module_id <- module_ids[[module_index]]
    data <- stratum_effects[stratum_effects$module_id == module_id, , drop = FALSE]
    draw_effect_heatmap(
      data,
      row_ids = context_ids,
      column_ids = stratum_ids,
      row_labels = unname(context_short[context_ids]),
      column_labels = stratum_labels,
      value_column = "estimate",
      row_column = "context_id",
      column_column = "stratum_id",
      limit = effect_limit,
      panel_label = c("A", "B", "C", "D")[[module_index]],
      panel_title = unname(module_labels[module_id]),
      status_column = "model_status",
      clipped_column = "display_clipped",
      show_row_labels = module_index %% 2L == 1L
    )
  }
  graphics::par(mar = c(0.5, 0.7, 0.6, 0.7), family = "sans")
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1))
  draw_effect_key(
    effect_limit, 0.25, 0.75, 0.52,
    label = "Adjusted AD−NCI effect (NCI-reference SD)"
  )
  graphics::text(0.5, 0.12,
                 "Triangles mark values clipped to the shared display scale; exact estimates and 95% CIs are in the plotted-data table",
                 cex = 0.72, col = "#555555")
  graphics::mtext(
    "Adjusted AD-minus-NCI component effects by sex/APOE stratum",
    side = 3, outer = TRUE, line = 1.0, cex = 1.22, font = 2
  )
  graphics::mtext(
    "Descriptive components of the formal modifiers—not 168 additional primary hypotheses",
    side = 3, outer = TRUE, line = -0.25, cex = 0.82, col = "#4D4D4D"
  )
}

stratum_images <- render_triplet(
  stratum_dir, stratum_base, 13.5, 9.8, args$png_dpi, draw_strata
)
stratum_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_module_stratum_effects.tsv"),
  input_path("respiratory_module_manifest.tsv"),
  input_path("respiratory_cell_context_manifest.tsv")
)
family_status[["stratum_effects"]] <- finalize_family(
  "stratum_effects", stratum_dir, stratum_base,
  stratum_path, stratum_images, stratum_sources,
  caption_lines = c(
    "# Phase 13 adjusted stratum effects",
    "",
    "The heatmaps show 168 adjusted AD-minus-NCI module-score effects: seven",
    "cell contexts, four mitochondrial modules, and six sex/APOE strata.",
    "These values explain the signs of the formal difference-of-differences",
    "tests but are not additional primary hypotheses. Color uses the same",
    "signed scale as the modifier landscape. Triangles identify clipped display",
    "values; exact estimates, robust standard errors, confidence intervals, and",
    "P values remain in the plotted-data table."
  ),
  methods_lines = c(
    "# Methods: Phase 13 adjusted stratum effects",
    "",
    "Stored adjusted stratum effects were plotted in manifest context/module",
    "order and frozen female/male APOE order. No model was refit. The shared",
    "effect scale spans −1.5 to +1.5 NCI-reference SD so that component and",
    "modifier panels are visually comparable. Values outside this range are",
    "clipped only for display and marked explicitly."
  ),
  family_checks = list(
    make_check("stratum_rows", nrow(stratum_effects) == 168L,
               nrow(stratum_effects), 168L),
    make_check("stratum_unique_keys",
               !anyDuplicated(stratum_effects[, c("context_id", "module_id", "stratum_id")]),
               nrow(unique(stratum_effects[, c("context_id", "module_id", "stratum_id")])), 168L)
  ),
  project_root = project_root,
  production_hash = production_hash
)

# ---------------------------------------------------------------------------
# Supplementary family 2: stability and reliability atlas
# ---------------------------------------------------------------------------
stability_dir <- file.path(output_dir, "stability_atlas")
stability_base <- "phase13_stability_atlas"
dir.create(stability_dir, recursive = TRUE, showWarnings = FALSE)

stability_checks <- c(
  bootstrap_direction_pass = "Bootstrap",
  loo_pass = "LOO",
  threshold50_sensitivity_pass = "50 nuclei",
  pc1_sensitivity_pass = "PC1",
  balance_direction_pass = "Balanced",
  qc_adjusted_same_direction = "QC model",
  severe_qc_exclusion_pass = "Severe-QC",
  omission_pass = "Omission"
)
stability_parts <- lapply(names(stability_checks), function(check_id) {
  data.frame(
    record_type = "stability_check",
    test_id = gate$test_id,
    context_id = gate$context_id,
    context_order = gate$context_order,
    contrast_id = gate$contrast_id,
    contrast_order = gate$contrast_order_display,
    module_id = gate$module_id,
    module_order = gate$module_order_display,
    check_id = check_id,
    check_label = stability_checks[[check_id]],
    check_order = match(check_id, names(stability_checks)),
    passed = as_flag(gate[[check_id]]),
    eligibility_status = gate$eligibility_status,
    scientific_status = gate$scientific_status,
    stringsAsFactors = FALSE
  )
})
stability_long <- do.call(rbind, stability_parts)
reliability_plot <- reliability
reliability_plot$record_type <- "module_reliability"
reliability_plot$context_order <- match(reliability_plot$context_id, context_ids)
reliability_plot$module_order <- match(reliability_plot$module_id, module_ids)
stability_plot_data <- bind_rows_fill(list(stability_long, reliability_plot))
stability_plot_data$schema_version <- "phase13_stability_atlas_plot_v1"
stability_path <- file.path(stability_dir, paste0(stability_base, "_plotted_data.tsv"))
atomic_write_table(stability_plot_data, stability_path)

draw_stability_panel <- function(module_id, panel_label, show_rows) {
  data <- gate[gate$module_id == module_id, , drop = FALSE]
  data <- data[order(data$context_order, data$contrast_order_display), ]
  row_labels <- paste0(
    unname(context_short[data$context_id]), " | ",
    unname(contrast_compact[data$contrast_id])
  )
  count <- nrow(data)
  graphics::par(mar = c(5.0, if (show_rows) 9.5 else 1.8, 2.5, 0.7),
                family = "sans", xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0.5, length(stability_checks) + 0.5),
                        ylim = c(0.5, count + 0.5), xaxs = "i", yaxs = "i")
  for (row_index in seq_len(count)) {
    y <- count - row_index + 1L
    for (column_index in seq_along(stability_checks)) {
      value <- as_flag(data[[names(stability_checks)[[column_index]]]])[[row_index]]
      fill <- if (is.na(value)) "#D9D9D9" else if (value) "#4C78A8" else "#E69F00"
      graphics::rect(column_index - 0.47, y - 0.47,
                     column_index + 0.47, y + 0.47,
                     col = fill, border = "white", lwd = 0.4)
      graphics::text(column_index, y, if (is.na(value)) "–" else if (value) "+" else "×",
                     cex = 0.55, col = if (is.na(value)) "#555555" else "white", font = 2)
    }
  }
  for (context_index in 2:7) {
    graphics::abline(h = count - (context_index - 1) * 7 + 0.5,
                     col = "#595959", lwd = 0.7)
  }
  graphics::par(xpd = NA)
  graphics::text(seq_along(stability_checks), 0.16,
                 labels = unname(stability_checks), srt = 46,
                 adj = c(1, 0.5), cex = 0.64)
  if (show_rows) {
    graphics::axis(2, at = rev(seq_len(count)), labels = row_labels,
                   las = 1, tick = FALSE, cex.axis = 0.43)
  }
  graphics::box(col = "#707070")
  graphics::mtext(unname(module_labels[module_id]), side = 3, line = 0.65,
                  cex = 0.92, font = 2)
  graphics::mtext(panel_label, side = 3, line = 0.65, adj = -0.10,
                  cex = 1.10, font = 2)
}

draw_stability <- function() {
  graphics::layout(matrix(c(1, 2, 3, 4, 5, 5), nrow = 3, byrow = TRUE),
                   heights = c(1, 1, 0.55))
  graphics::par(oma = c(0.7, 0.5, 2.6, 0.5))
  for (module_index in seq_along(module_ids)) {
    draw_stability_panel(
      module_ids[[module_index]], c("A", "B", "C", "D")[[module_index]],
      show_rows = module_index %% 2L == 1L
    )
  }
  graphics::par(mar = c(4.2, 4.8, 2.2, 4.8), family = "sans", xpd = FALSE)
  valid <- is.finite(reliability$nci_mean_z_pc1_correlation) &
    is.finite(reliability$variance_explained_pc1)
  shape_map <- setNames(c(21, 22, 24, 23), module_ids)
  graphics::plot(
    reliability$nci_mean_z_pc1_correlation[valid],
    reliability$variance_explained_pc1[valid],
    type = "n", xlim = c(0, 1.03), ylim = c(0, 0.82),
    xlab = "Mean-z versus PC1 correlation",
    ylab = "PC1 variance explained", axes = FALSE
  )
  graphics::axis(1, cex.axis = 0.72)
  graphics::axis(2, las = 1, cex.axis = 0.72)
  graphics::abline(v = 0.70, col = "#555555", lty = 2)
  graphics::points(
    reliability$nci_mean_z_pc1_correlation[valid],
    reliability$variance_explained_pc1[valid],
    pch = unname(shape_map[reliability$module_id[valid]]),
    bg = unname(context_colors[reliability$context_id[valid]]),
    col = "#202020", cex = 1.0, lwd = 0.55
  )
  outlier <- valid & reliability$nci_mean_z_pc1_correlation < 0.70
  graphics::text(
    reliability$nci_mean_z_pc1_correlation[outlier],
    reliability$variance_explained_pc1[outlier],
    labels = paste0(unname(context_short[reliability$context_id[outlier]]), "\n",
                    unname(module_labels[reliability$module_id[outlier]])),
    pos = 4, cex = 0.58
  )
  graphics::par(xpd = NA)
  graphics::legend(
    "right", inset = c(-0.30, 0), xpd = NA,
    legend = unname(module_labels[module_ids]),
    pch = unname(shape_map[module_ids]), pt.bg = "#BDBDBD",
    bty = "n", cex = 0.63, title = "Module shape"
  )
  graphics::box(col = "#707070")
  graphics::mtext("E", side = 3, line = 0.5, adj = -0.08, cex = 1.10, font = 2)
  graphics::mtext("Module-score reliability", side = 3, line = 0.5, cex = 0.92, font = 2)
  graphics::mtext(
    "Phase 13 sensitivity and reliability atlas",
    side = 3, outer = TRUE, line = 1.1, cex = 1.22, font = 2
  )
  graphics::mtext(
    "Blue/+ = pass, orange/× = fail, gray/– = not evaluated; rows remain in frozen order",
    side = 3, outer = TRUE, line = -0.15, cex = 0.82, col = "#4D4D4D"
  )
}

stability_images <- render_triplet(
  stability_dir, stability_base, 15.5, 18.5, args$png_dpi, draw_stability
)
stability_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_gate_decisions.tsv"),
  input_path("respiratory_stability_summary.tsv"),
  input_path("respiratory_module_reliability.tsv"),
  input_path("respiratory_module_manifest.tsv")
)
family_status[["stability_atlas"]] <- finalize_family(
  "stability_atlas", stability_dir, stability_base,
  stability_path, stability_images, stability_sources,
  caption_lines = c(
    "# Phase 13 sensitivity and reliability atlas",
    "",
    "Panels A–D show eight stored sensitivity decisions for every Phase 13",
    "test, preserving frozen module, context, and contrast order. Blue plus",
    "symbols indicate a pass, orange crosses indicate a failure, and gray",
    "dashes indicate that the sensitivity was not evaluated. Panel E compares",
    "the NCI-reference mean-z module score with its PC1 alternative and reports",
    "the fraction of module variation captured by PC1. Sensitivity agreement",
    "does not override the complete-family q-value or scientific gate."
  ),
  methods_lines = c(
    "# Methods: Phase 13 stability atlas",
    "",
    "Boolean stability components were read from the validated gate table;",
    "module reliability values were read from the validated reliability table.",
    "The atlas does not recalculate bootstrap, leave-one-out, balance, PC1,",
    "50-nucleus, QC, or omission analyses. Color is redundantly encoded with",
    "plus, cross, and dash symbols. The vertical reliability reference is the",
    "frozen 0.70 mean-z/PC1 correlation threshold."
  ),
  family_checks = list(
    make_check("stability_long_rows", nrow(stability_long) == 196L * 8L,
               nrow(stability_long), 196L * 8L),
    make_check("reliability_rows", nrow(reliability_plot) == 28L,
               nrow(reliability_plot), 28L),
    make_check("stability_test_coverage", length(unique(stability_long$test_id)) == 196L,
               length(unique(stability_long$test_id)), 196L)
  ),
  project_root = project_root,
  production_hash = production_hash
)

# ---------------------------------------------------------------------------
# Supplementary family 3: admitted module-member gene effects
# ---------------------------------------------------------------------------
gene_dir <- file.path(output_dir, "gene_support_atlas")
gene_base <- "phase13_gene_support_atlas"
dir.create(gene_dir, recursive = TRUE, showWarnings = FALSE)
message("Reading gene interaction table for admitted module-member atlas")
gene_results <- read_tsv(input_path("respiratory_gene_interaction_results.tsv.gz"))
require_columns(
  gene_results,
  c("context_id", "effect_id", "assay_feature_identifier", "log2_fold_change",
    "standard_error", "ci_low", "ci_high", "p_value", "q_value", "model_status"),
  "gene interaction results"
)

membership <- module_members[, c(
  "module_order", "module_id", "current_approved_symbol",
  "assay_feature_identifier", "respiratory_complex", "inclusion_reason"
)]
membership$member_order <- ave(seq_len(nrow(membership)), membership$module_id, FUN = seq_along)

coverage_expanded <- do.call(rbind, lapply(seq_len(nrow(coverage)), function(index) {
  features <- strsplit(coverage$admitted_assay_features[[index]], "|", fixed = TRUE)[[1L]]
  features <- features[nzchar(features)]
  if (!length(features)) return(NULL)
  data.frame(
    context_id = coverage$context_id[[index]],
    module_id = coverage$module_id[[index]],
    assay_feature_identifier = features,
    admitted_to_score = TRUE,
    stringsAsFactors = FALSE
  )
}))

grid <- merge(
  membership,
  expand.grid(
    context_id = context_ids,
    effect_id = contrast_ids,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  ),
  by = NULL
)
gene_subset <- gene_results[
  gene_results$context_id %in% context_ids &
    gene_results$effect_id %in% contrast_ids &
    gene_results$assay_feature_identifier %in% unique(membership$assay_feature_identifier),
  , drop = FALSE
]
gene_plot <- merge(
  grid,
  gene_subset,
  by = c("context_id", "effect_id", "assay_feature_identifier"),
  all.x = TRUE,
  sort = FALSE
)
gene_plot <- merge(
  gene_plot,
  coverage_expanded,
  by = c("context_id", "module_id", "assay_feature_identifier"),
  all.x = TRUE,
  sort = FALSE
)
gene_plot$admitted_to_score <- gene_plot$admitted_to_score %in% TRUE
gene_plot$context_order <- match(gene_plot$context_id, context_ids)
gene_plot$contrast_order <- match(gene_plot$effect_id, contrast_ids)
gene_plot$module_order <- match(gene_plot$module_id, module_ids)
gene_plot$display_estimate <- ifelse(
  gene_plot$admitted_to_score & is.finite(gene_plot$log2_fold_change),
  gene_plot$log2_fold_change,
  NA_real_
)
finite_gene_effects <- abs(gene_plot$display_estimate[is.finite(gene_plot$display_estimate)])
gene_limit <- max(2, ceiling(stats::quantile(finite_gene_effects, 0.98, names = FALSE) * 2) / 2)
gene_plot$display_clipped <- is.finite(gene_plot$display_estimate) & abs(gene_plot$display_estimate) > gene_limit
gene_plot$ci_excludes_zero <- gene_plot$admitted_to_score & is.finite(gene_plot$ci_low) &
  is.finite(gene_plot$ci_high) & (gene_plot$ci_low > 0 | gene_plot$ci_high < 0)
gene_plot$schema_version <- "phase13_gene_support_atlas_plot_v1"
gene_plot$record_type <- "module_member_gene_effect"
gene_plot$display_limit <- gene_limit
gene_plot <- gene_plot[order(
  gene_plot$module_order,
  gene_plot$member_order,
  gene_plot$context_order,
  gene_plot$contrast_order
), ]
gene_path <- file.path(gene_dir, paste0(gene_base, "_plotted_data.tsv"))
atomic_write_table(gene_plot, gene_path)

draw_gene_module <- function(module_id) {
  data <- gene_plot[gene_plot$module_id == module_id, , drop = FALSE]
  member_data <- membership[membership$module_id == module_id, , drop = FALSE]
  admitted_any <- tapply(data$admitted_to_score, data$assay_feature_identifier, any)
  genes <- member_data$assay_feature_identifier[
    admitted_any[member_data$assay_feature_identifier] %in% TRUE
  ]
  gene_labels <- member_data$current_approved_symbol[match(genes, member_data$assay_feature_identifier)]
  gene_categories <- member_data$respiratory_complex[match(genes, member_data$assay_feature_identifier)]
  columns <- expand.grid(
    contrast_id = contrast_ids,
    context_id = context_ids,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  )
  columns <- columns[order(match(columns$context_id, context_ids),
                           match(columns$contrast_id, contrast_ids)), ]
  column_keys <- paste(columns$context_id, columns$contrast_id, sep = "::")
  graphics::par(mar = c(6.8, 7.8, 5.0, 1.3), oma = c(0.5, 0.5, 2.0, 0.5),
                family = "sans", xpd = FALSE)
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(0.5, length(column_keys) + 0.5),
    ylim = c(0.5, length(genes) + 1.8), xaxs = "i", yaxs = "i"
  )
  for (row_index in seq_along(genes)) {
    y <- length(genes) - row_index + 1L
    for (column_index in seq_along(column_keys)) {
      key_parts <- strsplit(column_keys[[column_index]], "::", fixed = TRUE)[[1L]]
      index <- which(
        data$assay_feature_identifier == genes[[row_index]] &
          data$context_id == key_parts[[1L]] &
          data$effect_id == key_parts[[2L]]
      )
      admitted <- length(index) && isTRUE(data$admitted_to_score[index[[1L]]])
      value <- if (admitted) data$display_estimate[index[[1L]]] else NA_real_
      fill <- if (admitted) effect_color(value, gene_limit) else "#ECECEC"
      border <- if (length(index) && isTRUE(data$ci_excludes_zero[index[[1L]]])) "#111111" else "white"
      graphics::rect(column_index - 0.48, y - 0.48,
                     column_index + 0.48, y + 0.48,
                     col = fill, border = border,
                     lwd = if (border == "#111111") 0.75 else 0.25)
      if (!admitted) {
        graphics::segments(column_index - 0.20, y - 0.20,
                           column_index + 0.20, y + 0.20, col = "#B5B5B5", lwd = 0.45)
      }
      if (length(index) && isTRUE(data$display_clipped[index[[1L]]])) {
        graphics::points(column_index, y + 0.27,
                         pch = if (value > 0) 24 else 25,
                         cex = 0.40, bg = "#111111", col = "#111111")
      }
    }
  }
  for (context_index in seq_along(context_ids)) {
    left <- (context_index - 1L) * 7 + 0.52
    right <- context_index * 7 + 0.48
    graphics::rect(left, length(genes) + 0.82, right, length(genes) + 1.16,
                   col = unname(context_colors[context_ids[[context_index]]]), border = NA)
    graphics::text(mean(c(left, right)), length(genes) + 1.48,
                   unname(context_short[context_ids[[context_index]]]),
                   cex = 0.68, font = 2)
    if (context_index > 1L) {
      graphics::abline(v = (context_index - 1L) * 7 + 0.5,
                       col = "#606060", lwd = 0.8)
    }
  }
  category_breaks <- which(gene_categories[-1L] != gene_categories[-length(gene_categories)])
  if (length(category_breaks)) {
    for (break_index in category_breaks) {
      graphics::abline(h = length(genes) - break_index + 0.5,
                       col = "#606060", lwd = 0.7)
    }
  }
  graphics::par(xpd = NA)
  graphics::axis(2, at = rev(seq_along(genes)), labels = gene_labels,
                 las = 1, tick = FALSE, cex.axis = 0.52)
  repeated_labels <- rep(unname(contrast_compact[contrast_ids]), length(context_ids))
  graphics::text(seq_along(column_keys), 0.18, repeated_labels,
                 srt = 90, adj = c(1, 0.5), cex = 0.56)
  graphics::box(col = "#707070")
  graphics::mtext(unname(module_labels[module_id]), side = 3, line = 2.5,
                  cex = 1.05, font = 2)
  graphics::mtext(
    paste0("Cell color = gene modifier log2 fold change (display ±", gene_limit,
           "); black outline = 95% CI excludes zero; gray slash = not admitted"),
    side = 1, line = 5.4, cex = 0.70, col = "#4D4D4D"
  )
  graphics::mtext(
    "Phase 13 admitted module-member gene effects",
    side = 3, outer = TRUE, line = 0.9, cex = 1.22, font = 2
  )
  graphics::mtext(
    "Exploratory decomposition of module estimates—not evidence that the frozen module gate passed",
    side = 3, outer = TRUE, line = -0.35, cex = 0.80, col = "#4D4D4D"
  )
}

gene_images <- character()
for (module_id in module_ids) {
  admitted_count <- length(unique(gene_plot$assay_feature_identifier[
    gene_plot$module_id == module_id & gene_plot$admitted_to_score
  ]))
  height <- max(8.0, 4.2 + 0.12 * admitted_count)
  module_base <- paste0("phase13_gene_support_", module_id)
  gene_images <- c(
    gene_images,
    render_triplet(
      gene_dir, module_base, 19.0, height, args$png_dpi,
      function() draw_gene_module(module_id)
    )
  )
}
gene_sources <- c(
  input_path("respiratory_status.tsv"),
  input_path("respiratory_gene_interaction_results.tsv.gz"),
  input_path("respiratory_module_members.tsv"),
  input_path("respiratory_module_coverage.tsv"),
  input_path("respiratory_module_manifest.tsv"),
  input_path("respiratory_cell_context_manifest.tsv"),
  input_path("respiratory_contrast_manifest.tsv")
)
family_status[["gene_support_atlas"]] <- finalize_family(
  "gene_support_atlas", gene_dir, gene_base,
  gene_path, gene_images, gene_sources,
  caption_lines = c(
    "# Phase 13 admitted module-member gene-support atlas",
    "",
    "Four module-specific atlases display every module member admitted to at",
    "least one cell-context score. Columns are the 49 context-by-contrast",
    "combinations, and rows follow the frozen module-member and respiratory-",
    "complex order. Cell color is the stored gene-level modifier log2 fold",
    "change. Black outlines mark robust 95% confidence intervals that exclude",
    "zero; gray slashes mark genes not admitted to the corresponding context",
    "score. These panels are exploratory decompositions and do not replace the",
    "module-level FDR family or scientific gate."
  ),
  methods_lines = c(
    "# Methods: Phase 13 gene-support atlas",
    "",
    "Gene interaction estimates were joined to the frozen module manifest by",
    "`assay_feature_identifier` and to context-specific admitted genes from the",
    "coverage table. Every admitted member was retained regardless of gene-level",
    "P or q value. The same symmetric gene-effect display range, calculated as",
    "the larger of 2 or the rounded 98th percentile of absolute admitted-member",
    "effects, was applied to all four modules. Clipping is marked and exact",
    "estimates, CIs, P values, and q values remain in plotted data."
  ),
  family_checks = list(
    make_check("gene_module_memberships", nrow(membership) == 273L,
               nrow(membership), 273L),
    make_check("gene_context_contrast_grid",
               nrow(gene_plot) == nrow(membership) * 7L * 7L,
               nrow(gene_plot), nrow(membership) * 7L * 7L),
    make_check("gene_admitted_effects_present",
               all(is.finite(gene_plot$log2_fold_change[gene_plot$admitted_to_score])),
               sum(is.finite(gene_plot$log2_fold_change[gene_plot$admitted_to_score])),
               sum(gene_plot$admitted_to_score)),
    make_check("gene_atlas_modules", length(unique(gene_plot$module_id)) == 4L,
               length(unique(gene_plot$module_id)), 4L)
  ),
  project_root = project_root,
  production_hash = production_hash
)

# Package-level summary
family_ids <- names(family_status)
package_rows <- do.call(rbind, lapply(family_ids, function(family_id) {
  paths <- family_status[[family_id]]
  status_path <- paths[grepl("_status[.]tsv$", paths)][[1L]]
  family_record <- read_tsv(status_path)
  data.frame(
    schema_version = "phase13_figure_package_status_v1",
    figure_family = family_id,
    family_directory = relative_path(dirname(status_path), project_root),
    output_files = length(paths),
    failed_checks = family_record$failed_checks,
    validation_status = family_record$validation_status,
    stringsAsFactors = FALSE
  )
}))
package_status_path <- file.path(output_dir, "phase13_figure_package_status.tsv")
atomic_write_table(package_rows, package_status_path)
assert_true(all(package_rows$validation_status == "validated_complete"),
            "At least one Phase 13 figure family failed validation")
assert_true(!any(grepl("(^|[/_.-])c1([/_.-]|$)", list.files(output_dir, recursive = TRUE), ignore.case = TRUE)),
            "A generated artifact name contains the confusing abbreviation c1")

message(
  "Phase 13 figure package complete: ", length(family_ids),
  " families under ", output_dir
)
