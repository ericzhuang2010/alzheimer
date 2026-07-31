#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    input_dir = "results/minerva_production/12_kda",
    netweaver_dir = "untracked/NetWeaver",
    output_dir = "results/figures/analysis/phase12_kda",
    basename = "phase12_kda_circular",
    top_per_network = 5L
  )
  value_options <- c(
    "--input-dir", "--netweaver-dir", "--output-dir", "--basename",
    "--top-per-network"
  )

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/analysis/phease12_kda/",
        "visualize_phase12_kda_netweaver.R ",
        "[--input-dir DIR] [--netweaver-dir DIR] [--output-dir DIR] ",
        "[--basename NAME] [--top-per-network N]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }

    value <- args[[i + 1L]]
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- value
    i <- i + 2L
  }

  out$top_per_network <- suppressWarnings(as.integer(out$top_per_network))
  if (
    length(out$top_per_network) != 1L ||
      is.na(out$top_per_network) ||
      out$top_per_network < 1L ||
      out$top_per_network > 20L
  ) {
    stop("--top-per-network must be an integer from 1 to 20", call. = FALSE)
  }
  for (name in c("input_dir", "netweaver_dir", "output_dir")) {
    if (!nzchar(out[[name]])) {
      stop("--", gsub("_", "-", name), " must not be empty", call. = FALSE)
    }
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

require_columns <- function(x, columns, label) {
  missing <- setdiff(columns, names(x))
  if (length(missing)) {
    stop(
      label, " is missing columns: ", paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
}

read_phase12_table <- function(input_dir, filename) {
  path <- file.path(input_dir, filename)
  if (!file.exists(path)) {
    stop("Required Phase 12 file does not exist: ", path, call. = FALSE)
  }
  utils::read.delim(
    path,
    header = TRUE,
    sep = "\t",
    quote = "",
    comment.char = "",
    check.names = FALSE
  )
}

validate_phase12 <- function(status, checks, manifest, summary) {
  require_columns(
    status,
    c("schema_version", "validation_status"),
    "kda_status.tsv"
  )
  require_columns(
    checks,
    c("schema_version", "check_id", "passed"),
    "kda_checks.tsv"
  )
  require_columns(
    manifest,
    c(
      "schema_version", "kda_run_id", "analysis_tier", "fine_cell_type",
      "broad_network", "eligibility_status"
    ),
    "kda_run_manifest.tsv"
  )
  require_columns(
    summary,
    c(
      "schema_version", "broad_network", "key_driver",
      "significant_runs", "fine_cell_types", "primary_runs",
      "secondary_runs", "global_calls", "minimum_adjusted_p_value",
      "maximum_fold_enrichment"
    ),
    "kda_key_driver_summary.tsv"
  )

  if (
    nrow(status) != 1L ||
      status$schema_version[[1L]] != "mitochondrial_kda_status_v1" ||
      status$validation_status[[1L]] != "validated_complete"
  ) {
    stop(
      "This figure requires a Phase 12 bundle with validated_complete status",
      call. = FALSE
    )
  }
  if (
    !all(checks$schema_version == "mitochondrial_kda_checks_v1") ||
      any(is.na(checks$passed)) ||
      !all(checks$passed)
  ) {
    stop("At least one Phase 12 validation check did not pass", call. = FALSE)
  }
  if (
    !all(manifest$schema_version == "mitochondrial_kda_run_manifest_v1") ||
      anyDuplicated(manifest$kda_run_id)
  ) {
    stop("Unexpected or duplicated Phase 12 run manifest rows", call. = FALSE)
  }
  if (
    !nrow(summary) ||
      !all(
        summary$schema_version ==
          "mitochondrial_kda_key_driver_summary_v1"
      ) ||
      anyDuplicated(summary[, c("broad_network", "key_driver")])
  ) {
    stop("Unexpected or duplicated Phase 12 key-driver summary rows",
         call. = FALSE)
  }

  numeric_columns <- c(
    "significant_runs", "fine_cell_types", "primary_runs",
    "secondary_runs", "global_calls", "minimum_adjusted_p_value",
    "maximum_fold_enrichment"
  )
  if (
    anyNA(summary[, numeric_columns]) ||
      any(!is.finite(as.matrix(summary[, numeric_columns]))) ||
      any(summary$significant_runs <= 0) ||
      any(summary$minimum_adjusted_p_value <= 0) ||
      any(summary$minimum_adjusted_p_value > 0.05) ||
      any(summary$maximum_fold_enrichment <= 0) ||
      any(
        summary$primary_runs + summary$secondary_runs !=
          summary$significant_runs
      ) ||
      any(summary$global_calls > summary$significant_runs)
  ) {
    stop("Phase 12 key-driver summary values are inconsistent", call. = FALSE)
  }
}

load_netweaver_plotting <- function(netweaver_dir) {
  r_dir <- file.path(netweaver_dir, "R")
  required_files <- c(
    "rcEnvir.R",
    "rc.check.cytoband.R",
    "rc.set.cytoband.R",
    "rc.get.params.R",
    "rc.get.chrom.R",
    "rc.get.baseUnits.R",
    "rc.track.pos.R",
    "rc.get.coordinates.R",
    "rc.initialize.R",
    "rc.reset.params.R",
    "rc.plot.area.R",
    "rc.plot.track.R",
    "rc.plot.histogram.R",
    "rc.plot.barchart.R",
    "rc.plot.heatmap.R",
    "rc.plot.ideogram.R",
    "rc.plot.link.R",
    "rc.plot.track.id.R"
  )
  paths <- file.path(r_dir, required_files)
  missing <- paths[!file.exists(paths)]
  if (length(missing)) {
    stop(
      "NetWeaver plotting source is incomplete: ",
      paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
  for (path in paths) {
    sys.source(path, envir = .GlobalEnv)
  }

  expected_functions <- c(
    "rc.initialize", "rc.plot.area", "rc.plot.ideogram",
    "rc.plot.histogram", "rc.plot.barchart", "rc.plot.heatmap",
    "rc.plot.link", "rc.plot.track.id"
  )
  absent <- expected_functions[
    !vapply(expected_functions, exists, logical(1), mode = "function")
  ]
  if (length(absent)) {
    stop(
      "NetWeaver plotting functions failed to load: ",
      paste(absent, collapse = ", "),
      call. = FALSE
    )
  }
}

network_colors <- c(
  Astrocytes = "#009E73",
  Excitatory_neurons = "#E69F00",
  Inhibitory_neurons = "#0072B2",
  Microglia = "#CC79A7",
  OPCs = "#56B4E9",
  Oligodendrocytes = "#F0E442",
  Vasculature_cells = "#D55E00"
)

tier_composition_colors <- c(
  "Primary calls" = "#0072B2",
  "Pooled calls" = "#D55E00"
)

heat_strength_colors <- rev(grDevices::hcl.colors(100, "YlOrRd"))

network_labels <- c(
  Astrocytes = "Astrocytes",
  Excitatory_neurons = "Excitatory neurons",
  Inhibitory_neurons = "Inhibitory neurons",
  Microglia = "Microglia",
  OPCs = "OPCs",
  Oligodendrocytes = "Oligodendrocytes",
  Vasculature_cells = "Vasculature"
)

prepare_plot_data <- function(manifest, summary, top_per_network) {
  eligible <- manifest[
    manifest$eligibility_status == "eligible",
    ,
    drop = FALSE
  ]
  if (!nrow(eligible)) {
    stop("Phase 12 manifest has no eligible KDA runs", call. = FALSE)
  }

  tier_denominators <- stats::aggregate(
    kda_run_id ~ broad_network + analysis_tier,
    eligible,
    length
  )
  names(tier_denominators)[[3L]] <- "eligible_runs"
  primary_denominator <- setNames(
    tier_denominators$eligible_runs[
      tier_denominators$analysis_tier == "primary"
    ],
    tier_denominators$broad_network[
      tier_denominators$analysis_tier == "primary"
    ]
  )
  secondary_denominator <- setNames(
    tier_denominators$eligible_runs[
      tier_denominators$analysis_tier == "secondary"
    ],
    tier_denominators$broad_network[
      tier_denominators$analysis_tier == "secondary"
    ]
  )

  eligible_fine <- unique(
    eligible[, c("broad_network", "fine_cell_type"), drop = FALSE]
  )
  fine_denominator <- table(eligible_fine$broad_network)

  network_order <- unique(manifest$broad_network)
  network_order <- network_order[network_order %in% summary$broad_network]
  unsupported <- setdiff(network_order, names(network_colors))
  if (length(unsupported)) {
    stop(
      "No display color is configured for networks: ",
      paste(unsupported, collapse = ", "),
      call. = FALSE
    )
  }

  selected_list <- lapply(network_order, function(network) {
    x <- summary[summary$broad_network == network, , drop = FALSE]
    x <- x[
      order(
        -x$significant_runs,
        x$minimum_adjusted_p_value,
        -x$maximum_fold_enrichment,
        x$key_driver
      ),
      ,
      drop = FALSE
    ]
    utils::head(x, top_per_network)
  })
  selected <- do.call(rbind, selected_list)
  rownames(selected) <- NULL

  selected$eligible_primary_runs <- unname(
    primary_denominator[selected$broad_network]
  )
  selected$eligible_secondary_runs <- unname(
    secondary_denominator[selected$broad_network]
  )
  selected$eligible_runs <- (
    selected$eligible_primary_runs + selected$eligible_secondary_runs
  )
  selected$eligible_fine_cell_types <- unname(
    fine_denominator[selected$broad_network]
  )
  if (
    anyNA(
      selected[, c(
        "eligible_primary_runs", "eligible_secondary_runs",
        "eligible_runs", "eligible_fine_cell_types"
      )]
    ) ||
      any(selected$eligible_runs <= 0) ||
      any(selected$eligible_fine_cell_types <= 0)
  ) {
    stop("Could not derive Phase 12 plotting denominators", call. = FALSE)
  }

  selected$recurrence_fraction <- (
    selected$significant_runs / selected$eligible_runs
  )
  selected$primary_recurrence_fraction <- (
    selected$primary_runs / selected$eligible_primary_runs
  )
  selected$secondary_recurrence_fraction <- (
    selected$secondary_runs / selected$eligible_secondary_runs
  )
  selected$fine_cell_coverage_fraction <- (
    selected$fine_cell_types / selected$eligible_fine_cell_types
  )
  selected$global_call_fraction <- (
    selected$global_calls / selected$significant_runs
  )
  selected$minus_log10_minimum_adjusted_p <- (
    -log10(selected$minimum_adjusted_p_value)
  )
  selected$log2_maximum_fold_enrichment <- log2(
    selected$maximum_fold_enrichment
  )

  fraction_columns <- c(
    "recurrence_fraction", "primary_recurrence_fraction",
    "secondary_recurrence_fraction", "fine_cell_coverage_fraction",
    "global_call_fraction"
  )
  if (
    any(
      as.matrix(selected[, fraction_columns, drop = FALSE]) <
        -sqrt(.Machine$double.eps)
    ) ||
      any(
        as.matrix(selected[, fraction_columns, drop = FALSE]) >
          1 + sqrt(.Machine$double.eps)
      )
  ) {
    stop("At least one normalized plotting fraction is outside [0, 1]",
         call. = FALSE)
  }

  selected$minimum_adjusted_p_strength <- pmin(
    selected$minus_log10_minimum_adjusted_p,
    25
  ) / 25
  selected$maximum_fold_enrichment_strength <- pmin(
    selected$log2_maximum_fold_enrichment,
    12
  ) / 12
  selected$sector_id <- sprintf("driver_%03d", seq_len(nrow(selected)))
  selected$network_color <- unname(network_colors[selected$broad_network])
  selected$display_network <- unname(network_labels[selected$broad_network])
  selected$selection_rank <- ave(
    seq_len(nrow(selected)),
    selected$broad_network,
    FUN = seq_along
  )
  selected
}

make_recurrence_links <- function(selected) {
  occurrences <- table(selected$key_driver)
  recurring <- names(occurrences)[occurrences > 1L]
  if (!length(recurring)) {
    return(data.frame(
      Chr1 = character(), Pos1 = numeric(), Chr2 = character(),
      Pos2 = numeric(), Weight = numeric(), Color = character()
    ))
  }

  links <- lapply(recurring, function(gene) {
    x <- selected[selected$key_driver == gene, , drop = FALSE]
    if (nrow(x) < 2L) return(NULL)
    data.frame(
      Chr1 = x$sector_id[[1L]],
      Pos1 = 50,
      Chr2 = x$sector_id[-1L],
      Pos2 = 50,
      Weight = nrow(x),
      Color = "#4D4D4D45",
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, links)
}

draw_phase12_circle <- function(selected, manifest) {
  cyto <- data.frame(
    Chr = selected$sector_id,
    Start = 1,
    End = 100,
    BandColor = selected$network_color,
    stringsAsFactors = FALSE
  )

  rc.initialize(
    cyto,
    num.tracks = 14,
    chr.order = selected$sector_id,
    params = list(
      chr.padding = 0.08,
      track.padding = 0.08,
      track.height = 0.15
    )
  )
  params <- rc.get.params()
  rc.plot.area(size = 0.72, mar = c(2, 2, 5, 2))

  aliases <- setNames(selected$key_driver, selected$sector_id)
  label_colors <- setNames(selected$network_color, selected$sector_id)
  rc.plot.ideogram(
    track.ids = c(1, 2),
    plot.band = TRUE,
    plot.chromosome.id = TRUE,
    chrom.alias = aliases,
    color.chromosome.id = label_colors,
    cex.text = 0.49,
    track.border = NA,
    polygon.border = "white"
  )

  recurrence <- data.frame(
    Chr = selected$sector_id,
    Start = 1,
    End = 100,
    Data = selected$recurrence_fraction,
    Color = selected$network_color,
    stringsAsFactors = FALSE
  )
  rc.plot.histogram(
    recurrence,
    track.id = 4,
    data.col = "Data",
    color.col = "Color",
    fixed.height = FALSE,
    track.color = "#F2F2F2",
    track.border = "white",
    polygon.border = NA,
    custom.track.height = params$track.height * 2,
    max.value = 1
  )

  tier_composition <- data.frame(
    Chr = selected$sector_id,
    Start = 1,
    End = 100,
    Primary = selected$primary_runs,
    Pooled = selected$secondary_runs,
    stringsAsFactors = FALSE
  )
  rc.plot.barchart(
    tier_composition,
    track.id = 5,
    data.col = c("Primary", "Pooled"),
    bar.color = unname(tier_composition_colors),
    track.color = "#F2F2F2",
    track.border = "white",
    polygon.border = NA,
    ratio = TRUE
  )

  heatmap_data <- rbind(
    primary_recurrence = selected$primary_recurrence_fraction,
    pooled_recurrence = selected$secondary_recurrence_fraction,
    cell_type_coverage = selected$fine_cell_coverage_fraction,
    global_call_share = selected$global_call_fraction,
    minimum_fdr_strength = selected$minimum_adjusted_p_strength,
    maximum_fe_strength = selected$maximum_fold_enrichment_strength
  )
  colnames(heatmap_data) <- selected$sector_id
  rc.plot.heatmap(
    heatmap_data,
    track.id = 6,
    color.gradient = heat_strength_colors,
    track.color = "#F2F2F2",
    track.border = "white",
    polygon.border = "white"
  )

  links <- make_recurrence_links(selected)
  if (nrow(links)) {
    rc.plot.link(
      links,
      track.id = 12,
      data.col = "Weight",
      color.col = "Color",
      max.lwd = 2.1,
      sort.links = FALSE
    )
  }

  rc.plot.track.id(
    c(4, 5, 6, 7, 8, 9, 10, 11),
    labels = c("R", "T", "P", "S", "C", "G", "Q", "FE"),
    degree = 90,
    col = "#222222",
    cex = 0.52,
    font = 2
  )

  graphics::symbols(
    0, 0,
    circles = 0.42,
    inches = FALSE,
    add = TRUE,
    fg = "#BDBDBD",
    bg = "white"
  )
  graphics::text(
    0, 0.16,
    labels = "Phase 12 KDA",
    cex = 0.9,
    font = 2,
    col = "#222222"
  )
  graphics::text(
    0, -0.03,
    labels = paste0(
      nrow(selected), " top drivers\n",
      length(unique(selected$broad_network)), " networks"
    ),
    cex = 0.62,
    col = "#4D4D4D"
  )
  graphics::text(
    0, -0.27,
    labels = "links = same driver\nacross networks",
    cex = 0.46,
    col = "#6B6B6B"
  )

  legend_networks <- unique(
    selected[, c("broad_network", "display_network", "network_color")]
  )
  legend_x_left <- -params$radius / 0.72
  legend_y_top <- params$radius / 0.72
  network_legend <- graphics::legend(
    x = legend_x_left,
    y = legend_y_top,
    legend = legend_networks$display_network,
    fill = legend_networks$network_color,
    border = "#666666",
    title = "Network color\n(outer sectors and R bars)",
    bty = "n",
    cex = 0.58,
    xjust = 0,
    yjust = 1,
    xpd = NA
  )
  tier_legend_y <- legend_y_top - network_legend$rect$h - 0.12
  tier_legend <- graphics::legend(
    x = legend_x_left,
    y = tier_legend_y,
    legend = names(tier_composition_colors),
    fill = unname(tier_composition_colors),
    border = "#666666",
    title = "T composition color",
    bty = "n",
    cex = 0.58,
    xjust = 0,
    yjust = 1,
    xpd = NA
  )
  heat_legend_indices <- c(1L, 50L, length(heat_strength_colors))
  graphics::legend(
    x = legend_x_left,
    y = tier_legend_y - tier_legend$rect$h - 0.12,
    legend = c("Low (0)", "Middle (0.5)", "High (1)"),
    fill = heat_strength_colors[heat_legend_indices],
    border = "#A0A0A0",
    title = "Heat-ring color\n(P, S, C, G, Q, FE)",
    bty = "n",
    cex = 0.58,
    xjust = 0,
    yjust = 1,
    xpd = NA
  )
  graphics::legend(
    x = params$radius / 0.72,
    y = legend_y_top,
    legend = c(
      "R  all-run recurrence",
      "T  primary / pooled share",
      "P  primary recurrence",
      "S  pooled recurrence",
      "C  eligible cell-type coverage",
      "G  global-driver call share",
      "Q  min BH FDR strength (cap 25)",
      "FE max fold-enrichment strength (cap 12)"
    ),
    title = "Tracks, outer to inner",
    bty = "n",
    cex = 0.54,
    text.col = "#333333",
    xjust = 1,
    yjust = 1,
    xpd = NA
  )

  no_eligible_networks <- setdiff(
    unique(manifest$broad_network),
    unique(
      manifest$broad_network[
        manifest$eligibility_status == "eligible"
      ]
    )
  )
  no_result_text <- if (length(no_eligible_networks)) {
    paste0(
      "No eligible KDA runs: ",
      paste(gsub("_", " ", no_eligible_networks), collapse = ", ")
    )
  } else {
    "All configured networks had at least one eligible KDA run"
  }
  graphics::text(
    0,
    -params$radius / 0.72 + 0.15,
    labels = no_result_text,
    cex = 0.56,
    col = "#5A5A5A",
    xpd = NA
  )
  graphics::mtext(
    "Phase 12 mitochondrial key-driver overview",
    side = 3,
    line = 2.1,
    cex = 1.15,
    font = 2,
    col = "#222222"
  )
  graphics::mtext(
    paste0(
      "Top ", max(selected$selection_rank),
      " significant drivers per result-producing broad network; ",
      "fractions use eligible-run denominators"
    ),
    side = 3,
    line = 0.8,
    cex = 0.66,
    col = "#555555"
  )
}

atomic_write_table <- function(x, path) {
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
    na = "NA"
  )
  if (!file.rename(tmp, path)) {
    stop("Could not publish table: ", path, call. = FALSE)
  }
}

render_atomic <- function(path, open_device, draw) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  extension <- tools::file_ext(path)
  tmp <- file.path(
    dirname(path),
    paste0(".", tools::file_path_sans_ext(basename(path)),
           ".tmp.", Sys.getpid(), ".", extension)
  )
  device_open <- FALSE
  on.exit({
    if (device_open && grDevices::dev.cur() > 1L) {
      grDevices::dev.off()
    }
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
  if (!file.rename(tmp, path)) {
    stop("Could not publish figure: ", path, call. = FALSE)
  }
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
project_root <- normalizePath(getwd(), mustWork = TRUE)
input_dir <- absolute_path(args$input_dir, project_root)
netweaver_dir <- absolute_path(args$netweaver_dir, project_root)
output_dir <- absolute_path(args$output_dir, project_root)

if (!dir.exists(input_dir)) {
  stop("Phase 12 input directory does not exist: ", input_dir, call. = FALSE)
}
if (!dir.exists(netweaver_dir)) {
  stop("NetWeaver directory does not exist: ", netweaver_dir, call. = FALSE)
}
if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo graphics support", call. = FALSE)
}

message("Reading validated Phase 12 data from ", input_dir)
status <- read_phase12_table(input_dir, "kda_status.tsv")
checks <- read_phase12_table(input_dir, "kda_checks.tsv")
manifest <- read_phase12_table(input_dir, "kda_run_manifest.tsv")
summary <- read_phase12_table(input_dir, "kda_key_driver_summary.tsv")
validate_phase12(status, checks, manifest, summary)

message("Loading NetWeaver circular plotting functions from ", netweaver_dir)
load_netweaver_plotting(netweaver_dir)
selected <- prepare_plot_data(manifest, summary, args$top_per_network)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

table_path <- file.path(
  output_dir,
  paste0(args$basename, "_plotted_data.tsv")
)
svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))

atomic_write_table(selected, table_path)
message("Writing ", svg_path)
render_atomic(
  svg_path,
  function(path) {
    grDevices::svg(
      filename = path,
      width = 12,
      height = 12,
      pointsize = 12,
      family = "sans",
      bg = "white",
      antialias = "subpixel"
    )
  },
  function() draw_phase12_circle(selected, manifest)
)
message("Writing ", png_path)
render_atomic(
  png_path,
  function(path) {
    grDevices::png(
      filename = path,
      width = 3600,
      height = 3600,
      units = "px",
      pointsize = 12,
      res = 300,
      type = "cairo",
      bg = "white"
    )
  },
  function() draw_phase12_circle(selected, manifest)
)

message(
  "Phase 12 NetWeaver figure complete: ",
  nrow(selected), " drivers from ",
  length(unique(selected$broad_network)), " result-producing networks"
)
