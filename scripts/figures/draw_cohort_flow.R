#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    input = "results/minerva_production/02_cohort/cohort_exclusion_flow.tsv",
    output_dir = "results/figures/cohort_flow",
    basename = "cohort_flow"
  )
  value_options <- c("--input", "--output-dir", "--basename")

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/draw_cohort_flow.R ",
        "[--input FILE] [--output-dir DIR] [--basename NAME]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }

    value <- args[[i + 1L]]
    if (identical(key, "--input")) {
      out$input <- value
    } else if (identical(key, "--output-dir")) {
      out$output_dir <- value
    } else {
      out$basename <- value
    }
    i <- i + 2L
  }

  if (!nzchar(out$input)) stop("--input must not be empty", call. = FALSE)
  if (!nzchar(out$output_dir)) {
    stop("--output-dir must not be empty", call. = FALSE)
  }
  if (!grepl("^[A-Za-z0-9._-]+$", out$basename)) {
    stop(
      "--basename may contain only letters, numbers, dots, underscores, ",
      "and hyphens",
      call. = FALSE
    )
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

require_columns <- function(x, columns) {
  missing <- setdiff(columns, names(x))
  if (length(missing)) {
    stop(
      "Cohort flow input is missing columns: ",
      paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
}

validate_cohort_flow <- function(x) {
  required <- c(
    "schema_version", "step", "rule", "donors_before",
    "donors_excluded", "donors_remaining"
  )
  require_columns(x, required)

  if (!nrow(x)) stop("Cohort flow input has no rows", call. = FALSE)
  if (anyNA(x[, required])) {
    stop("Cohort flow input contains missing required values", call. = FALSE)
  }
  if (!all(x$schema_version == "cohort_exclusion_flow_v1")) {
    stop("Unexpected cohort flow schema version", call. = FALSE)
  }

  numeric_columns <- c(
    "step", "donors_before", "donors_excluded", "donors_remaining"
  )
  for (column in numeric_columns) {
    values <- x[[column]]
    if (
      !is.numeric(values) ||
        any(!is.finite(values)) ||
        any(values < 0) ||
        any(values != floor(values))
    ) {
      stop(column, " must contain non-negative integers", call. = FALSE)
    }
  }

  x <- x[order(x$step), , drop = FALSE]
  if (!identical(as.integer(x$step), seq_len(nrow(x)))) {
    stop("Cohort flow steps must be unique and contiguous from 1", call. = FALSE)
  }
  if (anyDuplicated(x$rule)) {
    stop("Cohort flow rules must be unique", call. = FALSE)
  }
  if (any(x$donors_before - x$donors_excluded != x$donors_remaining)) {
    stop(
      "At least one cohort stage fails before - excluded = remaining",
      call. = FALSE
    )
  }
  if (
    nrow(x) > 1L &&
      any(x$donors_before[-1L] != x$donors_remaining[-nrow(x)])
  ) {
    stop("Donor counts are discontinuous between cohort stages", call. = FALSE)
  }
  x
}

format_rule <- function(rule) {
  labels <- c(
    represented_in_master_cell_metadata =
      "represented in\nmaster cell\nmetadata",
    retain_NCI_or_AD =
      "retain NCI or AD",
    exclude_prespecified_sex_discordant =
      "exclude\nprespecified sex\ndiscordant",
    exclude_APOE_e2_e4 =
      "exclude APOE e2\ne4",
    require_APOE_genotype =
      "require APOE\ngenotype",
    require_PMI =
      "require PMI",
    require_age_at_death_and_valid_sex =
      "require age at\ndeath and valid\nsex"
  )

  known <- unname(labels[rule])
  fallback <- vapply(
    gsub("_", " ", rule, fixed = TRUE),
    function(value) paste(strwrap(value, width = 18L), collapse = "\n"),
    character(1)
  )
  ifelse(is.na(known), fallback, known)
}

draw_cohort_flow <- function(cohort) {
  labels <- paste0(
    "Step ", cohort$step, ":\n",
    format_rule(cohort$rule)
  )
  y_max <- max(cohort$donors_remaining)

  old <- graphics::par(
    mar = c(8, 5, 5, 2),
    family = "sans",
    fg = "#222222",
    col.axis = "#222222",
    col.lab = "#222222",
    col.main = "#222222"
  )
  on.exit(graphics::par(old), add = TRUE)

  bars <- graphics::barplot(
    cohort$donors_remaining,
    names.arg = labels,
    las = 1,
    col = "#4C78A8",
    border = NA,
    cex.names = 0.75,
    cex.axis = 0.9,
    ylim = c(0, max(1, y_max * 1.12)),
    ylab = "Donors remaining",
    main = "Cohort flow"
  )
  graphics::text(
    bars,
    cohort$donors_remaining,
    labels = cohort$donors_remaining,
    pos = 3,
    cex = 0.9,
    col = "#222222"
  )
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
project_root <- normalizePath(getwd(), mustWork = TRUE)
input_path <- absolute_path(args$input, project_root)
output_dir <- absolute_path(args$output_dir, project_root)

if (!file.exists(input_path)) {
  stop("Cohort flow input does not exist: ", input_path, call. = FALSE)
}
if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo support required for SVG output",
       call. = FALSE)
}

cohort <- utils::read.delim(
  input_path,
  header = TRUE,
  sep = "\t",
  quote = "",
  comment.char = "",
  check.names = FALSE
)
cohort <- validate_cohort_flow(cohort)

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
tmp_svg <- file.path(
  output_dir,
  paste0(".", args$basename, ".tmp.", Sys.getpid(), ".svg")
)

device_open <- FALSE
on.exit({
  if (device_open && grDevices::dev.cur() > 1L) {
    grDevices::dev.off()
  }
  if (file.exists(tmp_svg)) unlink(tmp_svg)
}, add = TRUE)

message("Reading ", input_path)
message("Writing ", svg_path)
grDevices::svg(
  filename = tmp_svg,
  width = 14,
  height = 8.5,
  pointsize = 12,
  onefile = TRUE,
  family = "sans",
  bg = "white",
  antialias = "subpixel"
)
device_open <- TRUE
draw_cohort_flow(cohort)
grDevices::dev.off()
device_open <- FALSE

if (!file.exists(tmp_svg) || file.info(tmp_svg)$size <= 0) {
  stop("SVG renderer produced an empty output", call. = FALSE)
}
if (!file.rename(tmp_svg, svg_path)) {
  stop("Could not publish SVG output: ", svg_path, call. = FALSE)
}

message(
  "Cohort flow complete: ",
  nrow(cohort),
  " stages; ",
  cohort$donors_before[[1L]],
  " initial donors; ",
  cohort$donors_remaining[[nrow(cohort)]],
  " eligible donors"
)
