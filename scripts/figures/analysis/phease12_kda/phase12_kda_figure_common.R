options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

phase12_network_order <- c(
  "Astrocytes",
  "Excitatory_neurons",
  "Inhibitory_neurons",
  "Microglia",
  "OPCs",
  "Oligodendrocytes",
  "Vasculature_cells"
)

phase12_network_labels <- c(
  Astrocytes = "Astrocytes",
  Excitatory_neurons = "Excitatory neurons",
  Inhibitory_neurons = "Inhibitory neurons",
  Microglia = "Microglia",
  OPCs = "OPCs",
  Oligodendrocytes = "Oligodendrocytes",
  Vasculature_cells = "Vasculature"
)

phase12_network_colors <- c(
  Astrocytes = "#009E73",
  Excitatory_neurons = "#E69F00",
  Inhibitory_neurons = "#0072B2",
  Microglia = "#CC79A7",
  OPCs = "#56B4E9",
  Oligodendrocytes = "#F0E442",
  Vasculature_cells = "#D55E00"
)

phase12_candidate_pool <- c(
  "RPL11", "RPS15", "WDR82", "LAMTOR5", "SELENOW", "GABARAPL2",
  "TMEM147", "BEX3", "APOE", "FTL", "ANKRD11", "SLC11A1",
  "HSPA1A", "PARK7"
)

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

assert_true <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
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

read_tsv <- function(path) {
  if (!file.exists(path)) stop("Required file does not exist: ", path, call. = FALSE)
  connection <- if (grepl("[.]gz$", path)) gzfile(path, "rt") else path
  on.exit(if (inherits(connection, "connection")) close(connection), add = TRUE)
  utils::read.delim(
    connection,
    header = TRUE,
    sep = "\t",
    quote = "",
    comment.char = "",
    check.names = FALSE,
    na.strings = c("NA")
  )
}

validate_phase12_bundle <- function(input_dir) {
  status <- read_tsv(file.path(input_dir, "kda_status.tsv"))
  checks <- read_tsv(file.path(input_dir, "kda_checks.tsv"))
  require_columns(status, c("schema_version", "validation_status"), "kda_status.tsv")
  require_columns(checks, c("schema_version", "check_id", "passed"), "kda_checks.tsv")
  assert_true(
    nrow(status) == 1L &&
      identical(status$schema_version[[1L]], "mitochondrial_kda_status_v1") &&
      identical(status$validation_status[[1L]], "validated_complete"),
    "The figures require the validated_complete Phase 12 production bundle"
  )
  assert_true(
    nrow(checks) > 0L && !anyNA(checks$passed) && all(checks$passed),
    "At least one Phase 12 validation check is missing or failed"
  )
  invisible(TRUE)
}

atomic_write_table <- function(x, path, na = "NA") {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(
    dirname(path),
    paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  on.exit(if (file.exists(tmp)) unlink(tmp), add = TRUE)
  utils::write.table(
    x,
    file = tmp,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    col.names = TRUE,
    na = na
  )
  if (!file.rename(tmp, path)) stop("Could not publish table: ", path, call. = FALSE)
  invisible(path)
}

render_atomic <- function(path, open_device, draw) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  extension <- tools::file_ext(path)
  tmp <- file.path(
    dirname(path),
    paste0(
      ".", tools::file_path_sans_ext(basename(path)),
      ".tmp.", Sys.getpid(), ".", extension
    )
  )
  device_open <- FALSE
  on.exit({
    if (device_open && grDevices::dev.cur() > 1L) grDevices::dev.off()
    if (file.exists(tmp)) unlink(tmp)
  }, add = TRUE)
  open_device(tmp)
  device_open <- TRUE
  draw()
  grDevices::dev.off()
  device_open <- FALSE
  if (!file.exists(tmp) || file.info(tmp)$size <= 0) {
    stop("Renderer produced an empty output: ", path, call. = FALSE)
  }
  if (!file.rename(tmp, path)) stop("Could not publish figure: ", path, call. = FALSE)
  invisible(path)
}

open_svg_device <- function(path, width, height) {
  grDevices::svg(
    filename = path,
    width = width,
    height = height,
    pointsize = 10,
    family = "sans",
    bg = "white",
    antialias = "subpixel"
  )
}

open_pdf_device <- function(path, width, height) {
  grDevices::cairo_pdf(
    filename = path,
    width = width,
    height = height,
    pointsize = 10,
    family = "sans",
    bg = "white"
  )
}

open_png_device <- function(path, width, height, dpi = 450) {
  grDevices::png(
    filename = path,
    width = width,
    height = height,
    units = "in",
    pointsize = 10,
    res = dpi,
    type = "cairo",
    bg = "white"
  )
}

rgba <- function(color, alpha) grDevices::adjustcolor(color, alpha.f = alpha)

parse_value_args <- function(args, defaults, allowed) {
  out <- defaults
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) return(structure(out, help = TRUE))
    if (!key %in% allowed || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  out
}
