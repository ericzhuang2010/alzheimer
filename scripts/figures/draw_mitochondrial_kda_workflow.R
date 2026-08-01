#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_args <- function(args) {
  out <- list(
    input_dir = Sys.getenv("KDA_INPUT_DIR", unset = ""),
    output_dir = "results/figures",
    basename = "mitochondrial_kda_workflow"
  )
  value_options <- c("--input-dir", "--output-dir", "--basename")

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/draw_mitochondrial_kda_workflow.R ",
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

require_columns <- function(x, columns, label) {
  missing <- setdiff(columns, names(x))
  if (length(missing)) {
    stop(label, " is missing columns: ", paste(missing, collapse = ", "),
         call. = FALSE)
  }
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

format_count <- function(x) {
  format(as.integer(x), big.mark = ",", scientific = FALSE, trim = TRUE)
}

check_row <- function(check_id, observed, expected, passed) {
  data.frame(
    check_id = check_id,
    observed = as.character(observed),
    expected = as.character(expected),
    passed = isTRUE(passed),
    stringsAsFactors = FALSE
  )
}

validate_inputs <- function(input_dir) {
  files <- c(
    status = "kda_status.tsv",
    manifest = "kda_run_manifest.tsv",
    checks = "kda_checks.tsv",
    artifacts = "kda_artifacts.tsv"
  )
  paths <- setNames(file.path(input_dir, unname(files)), names(files))
  missing_files <- paths[!file.exists(paths)]
  if (length(missing_files)) {
    stop("Missing KDA input files: ", paste(missing_files, collapse = ", "),
         call. = FALSE)
  }

  status <- read_tsv(paths[["status"]])
  manifest <- read_tsv(paths[["manifest"]])
  source_checks <- read_tsv(paths[["checks"]])
  artifacts <- read_tsv(paths[["artifacts"]])

  require_columns(
    status,
    c(
      "schema_version", "fine_cell_types", "broad_networks",
      "planned_runs", "eligible_runs", "skipped_runs", "failed_runs",
      "significant_runs", "significant_key_drivers", "failed_checks",
      "validation_status"
    ),
    "KDA status"
  )
  require_columns(
    manifest,
    c(
      "schema_version", "kda_run_id", "analysis_tier", "fine_cell_type",
      "broad_network", "signature_group", "signature_direction",
      "eligibility_status", "terminal_status"
    ),
    "KDA run manifest"
  )
  require_columns(source_checks, c("check_id", "passed"), "KDA checks")
  require_columns(
    artifacts,
    c("artifact_role", "path", "sha256", "bytes"),
    "KDA artifacts"
  )

  if (nrow(status) != 1L) {
    stop("KDA status must contain exactly one row", call. = FALSE)
  }

  primary_groups <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
  secondary_groups <- c(
    "female_pool", "male_pool", "e2_pool", "e33_pool", "e4_pool"
  )
  directions <- c("AD_up_mito", "AD_down_mito", "AD_both_mito")
  primary_count <- sum(manifest$analysis_tier == "primary")
  secondary_count <- sum(manifest$analysis_tier == "secondary")
  terminal_counts <- table(manifest$terminal_status)
  terminal_value <- function(name) {
    if (name %in% names(terminal_counts)) as.integer(terminal_counts[[name]]) else 0L
  }
  completed_significant <- terminal_value("completed_significant")
  completed_no_significant <- terminal_value("completed_no_significant")
  skipped_manifest <- sum(grepl("^skipped_", manifest$terminal_status))
  network_map <- unique(manifest[c("fine_cell_type", "broad_network")])

  figure_checks <- do.call(
    rbind,
    list(
      check_row(
        "validation_status",
        status$validation_status[[1L]],
        "validated_complete",
        identical(status$validation_status[[1L]], "validated_complete")
      ),
      check_row(
        "source_checks_passed",
        sum(source_checks$passed %in% TRUE),
        nrow(source_checks),
        nrow(source_checks) > 0L && all(source_checks$passed %in% TRUE)
      ),
      check_row("primary_run_count", primary_count, 972L, primary_count == 972L),
      check_row(
        "secondary_run_count", secondary_count, 810L,
        secondary_count == 810L
      ),
      check_row(
        "planned_run_count", nrow(manifest), 1782L, nrow(manifest) == 1782L
      ),
      check_row(
        "status_manifest_planned_agree",
        status$planned_runs[[1L]], nrow(manifest),
        status$planned_runs[[1L]] == nrow(manifest)
      ),
      check_row(
        "run_balance",
        status$eligible_runs[[1L]] + status$skipped_runs[[1L]] +
          status$failed_runs[[1L]],
        status$planned_runs[[1L]],
        status$eligible_runs[[1L]] + status$skipped_runs[[1L]] +
          status$failed_runs[[1L]] == status$planned_runs[[1L]]
      ),
      check_row(
        "terminal_significant_runs",
        completed_significant, status$significant_runs[[1L]],
        completed_significant == status$significant_runs[[1L]]
      ),
      check_row(
        "terminal_no_significant_runs",
        completed_no_significant,
        status$eligible_runs[[1L]] - status$significant_runs[[1L]],
        completed_no_significant ==
          status$eligible_runs[[1L]] - status$significant_runs[[1L]]
      ),
      check_row(
        "terminal_skipped_runs",
        skipped_manifest, status$skipped_runs[[1L]],
        skipped_manifest == status$skipped_runs[[1L]]
      ),
      check_row(
        "no_failed_runs", status$failed_runs[[1L]], 0L,
        status$failed_runs[[1L]] == 0L
      ),
      check_row(
        "fine_cell_network_mapping",
        nrow(network_map), status$fine_cell_types[[1L]],
        nrow(network_map) == status$fine_cell_types[[1L]] &&
          !anyDuplicated(network_map$fine_cell_type)
      ),
      check_row(
        "primary_groups_present",
        paste(sort(unique(manifest$signature_group[
          manifest$analysis_tier == "primary"
        ])), collapse = ";"),
        paste(sort(primary_groups), collapse = ";"),
        setequal(
          unique(manifest$signature_group[manifest$analysis_tier == "primary"]),
          primary_groups
        )
      ),
      check_row(
        "secondary_groups_present",
        paste(sort(unique(manifest$signature_group[
          manifest$analysis_tier == "secondary"
        ])), collapse = ";"),
        paste(sort(secondary_groups), collapse = ";"),
        setequal(
          unique(manifest$signature_group[manifest$analysis_tier == "secondary"]),
          secondary_groups
        )
      ),
      check_row(
        "directions_present_in_both_tiers",
        paste(sort(unique(manifest$signature_direction)), collapse = ";"),
        paste(sort(directions), collapse = ";"),
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
      )
    )
  )

  if (!all(figure_checks$passed)) {
    failed <- figure_checks$check_id[!figure_checks$passed]
    stop("Figure input validation failed: ", paste(failed, collapse = ", "),
         call. = FALSE)
  }

  metrics <- data.frame(
    metric = c(
      "fine_cell_types", "broad_networks", "primary_planned_runs",
      "secondary_planned_runs", "planned_runs", "eligible_runs",
      "skipped_runs", "failed_runs", "significant_runs",
      "no_significant_runs", "significant_driver_rows",
      "validation_checks_passed"
    ),
    value = c(
      status$fine_cell_types[[1L]],
      status$broad_networks[[1L]],
      primary_count,
      secondary_count,
      status$planned_runs[[1L]],
      status$eligible_runs[[1L]],
      status$skipped_runs[[1L]],
      status$failed_runs[[1L]],
      status$significant_runs[[1L]],
      completed_no_significant,
      status$significant_key_drivers[[1L]],
      sum(source_checks$passed %in% TRUE)
    ),
    source_file = c(
      rep("kda_status.tsv", 2L),
      rep("kda_run_manifest.tsv", 2L),
      rep("kda_status.tsv", 5L),
      "kda_run_manifest.tsv",
      "kda_status.tsv",
      "kda_checks.tsv"
    ),
    derivation = c(
      "stored", "stored", "count analysis_tier", "count analysis_tier",
      "stored", "stored", "stored", "stored", "stored",
      "count terminal_status", "stored", "count passed"
    ),
    stringsAsFactors = FALSE
  )
  values <- setNames(as.integer(metrics$value), metrics$metric)

  list(
    status = status,
    manifest = manifest,
    source_checks = source_checks,
    artifacts = artifacts,
    metrics = metrics,
    values = values,
    figure_checks = figure_checks,
    input_paths = paths
  )
}

colours <- list(
  ink = "#183247",
  text = "#344B5E",
  muted = "#667985",
  border = "#93A2AC",
  panel = "#FFFFFF",
  input_fill = "#F2F5F7",
  primary = "#137C79",
  primary_fill = "#E2F2EF",
  secondary = "#7251A3",
  secondary_fill = "#EFE9F7",
  up = "#D55E42",
  up_fill = "#F9E4DD",
  down = "#2F6FAE",
  down_fill = "#E2EDF8",
  both = "#7E5A88",
  both_fill = "#EEE7F2",
  query = "#E6A51A",
  query_fill = "#FDE7A7",
  success = "#2B7A4B",
  success_fill = "#E4F2E8",
  skip = "#7A8790",
  skip_fill = "#EEF1F3",
  network = "#B7C0C6",
  network_dark = "#5B6A73"
)

rounded_box <- function(
    x0, y0, x1, y1, fill = "white", border = colours$border,
    radius = 0.10, lwd = 1.2, lty = 1) {
  width <- x1 - x0
  height <- y1 - y0
  radius <- min(radius, width / 2, height / 2)
  arc <- function(cx, cy, from, to, n = 12L) {
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

draw_panel <- function(x0, y0, x1, y1, tag, title) {
  rounded_box(x0, y0, x1, y1, fill = colours$panel, border = "#CBD3D8",
              radius = 0.13, lwd = 1.1)
  graphics::rect(x0, y1 - 0.43, x1, y1, col = "#EAF0F3", border = NA)
  graphics::text(
    x0 + 0.17, y1 - 0.215, paste0(tag, "  |  ", title),
    adj = c(0, 0.5), cex = 0.79, font = 2, col = colours$ink
  )
}

draw_arrow <- function(
    x0, y0, x1, y1, col = colours$muted, lwd = 1.5,
    lty = 1, length = 0.075) {
  graphics::arrows(
    x0, y0, x1, y1, length = length, angle = 23, code = 2,
    col = col, lwd = lwd, lty = lty
  )
}

draw_pill <- function(
    x, y, width, height, label, fill, border, col = colours$ink,
    cex = 0.55, font = 2, lty = 1) {
  rounded_box(
    x - width / 2, y - height / 2, x + width / 2, y + height / 2,
    fill = fill, border = border, radius = height / 2, lwd = 1.1, lty = lty
  )
  graphics::text(x, y, label, cex = cex, font = font, col = col)
}

draw_signature_badge <- function(x, y, direction, label, width = 0.82) {
  style <- switch(
    direction,
    up = list(fill = colours$up_fill, border = colours$up, symbol = "▲"),
    down = list(fill = colours$down_fill, border = colours$down, symbol = "▼"),
    both = list(fill = colours$both_fill, border = colours$both, symbol = "◆")
  )
  rounded_box(
    x - width / 2, y - 0.20, x + width / 2, y + 0.20,
    fill = style$fill, border = style$border, radius = 0.08, lwd = 1.0
  )
  graphics::text(x - width * 0.31, y, style$symbol, cex = 0.52,
                 col = style$border)
  graphics::text(x + width * 0.06, y, label, cex = 0.49, font = 2,
                 col = colours$ink)
}

draw_node <- function(x, y, fill, border = colours$network_dark,
                      cex = 1.15, label = NULL, label_cex = 0.45,
                      text_col = colours$ink) {
  graphics::points(x, y, pch = 21, bg = fill, col = border, cex = cex, lwd = 1.1)
  if (!is.null(label)) {
    graphics::text(x, y, label, cex = label_cex, font = 2, col = text_col)
  }
}

draw_small_network <- function(cx, cy, scale = 1, query_nodes = c(3L, 5L)) {
  pts <- data.frame(
    x = cx + scale * c(-0.78, -0.34, -0.30, 0.20, 0.25, 0.76, 0.73),
    y = cy + scale * c(0.04, 0.40, -0.34, 0.16, -0.43, 0.36, -0.20)
  )
  edges <- rbind(
    c(1, 2), c(1, 3), c(2, 4), c(3, 4), c(3, 5),
    c(4, 6), c(4, 7), c(5, 7)
  )
  for (i in seq_len(nrow(edges))) {
    a <- edges[i, 1L]
    b <- edges[i, 2L]
    draw_arrow(
      pts$x[a], pts$y[a], pts$x[b], pts$y[b],
      col = "#86949D", lwd = 0.9, length = 0.045
    )
  }
  for (i in seq_len(nrow(pts))) {
    fill <- if (i %in% query_nodes) colours$query_fill else "#E1E6E9"
    border <- if (i %in% query_nodes) colours$query else colours$network_dark
    draw_node(pts$x[i], pts$y[i], fill = fill, border = border, cex = 0.85)
  }
}

draw_input_panel <- function() {
  draw_panel(0.35, 6.95, 4.15, 10.15, "A", "Validated inputs")

  boxes <- list(
    list(
      y = 9.30, title = "Stratified AD-versus-NCI DE",
      detail = "54 fine cell types • 6 sex/APOE contrasts",
      fill = "#F8EEE8", border = "#B66A43"
    ),
    list(
      y = 8.49, title = "Mitochondrial annotation",
      detail = "core_mito_protein • original assay IDs",
      fill = "#EEF4E7", border = "#6C8A4F"
    ),
    list(
      y = 7.68, title = "Final Bayesian networks",
      detail = "9 broad cell classes • directed acyclic graphs",
      fill = "#EAF0F5", border = "#587A94"
    )
  )
  for (item in boxes) {
    rounded_box(
      0.60, item$y - 0.31, 3.90, item$y + 0.31,
      fill = item$fill, border = item$border, radius = 0.11, lwd = 1.1
    )
    graphics::text(0.82, item$y + 0.10, item$title, adj = c(0, 0.5),
                   cex = 0.66, font = 2, col = colours$ink)
    graphics::text(0.82, item$y - 0.13, item$detail, adj = c(0, 0.5),
                   cex = 0.52, col = colours$text)
  }

  draw_pill(
    2.25, 7.17, 3.15, 0.32,
    "fine-cell signature  →  matched broad network",
    fill = "#F5F7F8", border = "#B8C2C8", cex = 0.48, font = 2
  )
}

draw_analysis_grid_panel <- function(v) {
  draw_panel(4.35, 6.95, 17.65, 10.15, "B", "Primary and secondary analysis grid")
  draw_pill(
    16.35, 9.92, 2.10, 0.31,
    paste0(format_count(v[["planned_runs"]]), " planned runs"),
    fill = "#F8FAFB", border = colours$ink, cex = 0.50
  )

  rounded_box(
    4.62, 8.50, 17.38, 9.58,
    fill = colours$primary_fill, border = colours$primary,
    radius = 0.12, lwd = 1.45
  )
  graphics::text(4.87, 9.30, "PRIMARY", adj = c(0, 0.5), cex = 0.66,
                 font = 2, col = colours$primary)
  graphics::text(4.87, 9.02, "six individual\nstrata", adj = c(0, 0.5),
                 cex = 0.52, col = colours$text)
  groups <- c("F e2", "F e33", "F e4", "M e2", "M e33", "M e4")
  gx <- seq(6.35, 10.75, length.out = length(groups))
  for (i in seq_along(groups)) {
    draw_pill(
      gx[[i]], 9.17, 0.68, 0.39, groups[[i]],
      fill = "white", border = colours$primary, cex = 0.48
    )
  }
  graphics::text(8.55, 8.72, "each AD–NCI contrast remains separate",
                 cex = 0.48, col = colours$text, font = 3)
  draw_arrow(11.22, 9.05, 11.74, 9.05, col = colours$primary, lwd = 1.3)
  draw_signature_badge(12.23, 9.18, "up", "AD-up", width = 0.88)
  draw_signature_badge(13.18, 9.18, "down", "AD-down", width = 0.94)
  draw_signature_badge(14.15, 9.18, "both", "Both", width = 0.82)
  graphics::text(13.18, 8.72, "D_both = D_up ∪ D_down",
                 cex = 0.48, col = colours$text)
  draw_pill(
    16.14, 9.05, 1.86, 0.55,
    paste0("54 × 6 × 3\n= ", format_count(v[["primary_planned_runs"]])),
    fill = "white", border = colours$primary, cex = 0.52
  )

  rounded_box(
    4.62, 7.14, 17.38, 8.30,
    fill = colours$secondary_fill, border = colours$secondary,
    radius = 0.12, lwd = 1.45, lty = 2
  )
  graphics::text(4.87, 8.02, "SECONDARY", adj = c(0, 0.5), cex = 0.66,
                 font = 2, col = colours$secondary)
  graphics::text(4.87, 7.70, "five pooled\nsummaries", adj = c(0, 0.5),
                 cex = 0.52, col = colours$text)
  pool_labels <- c(
    "Female\nF e2+e33+e4", "Male\nM e2+e33+e4",
    "e2\nF+M", "e33\nF+M", "e4\nF+M"
  )
  px <- seq(6.35, 10.85, length.out = length(pool_labels))
  for (i in seq_along(pool_labels)) {
    rounded_box(
      px[[i]] - 0.48, 7.50, px[[i]] + 0.48, 8.03,
      fill = "white", border = colours$secondary, radius = 0.08,
      lwd = 1.0, lty = 2
    )
    graphics::text(px[[i]], 7.765, pool_labels[[i]], cex = 0.43,
                   font = 2, col = colours$ink)
  }
  draw_arrow(11.42, 7.73, 11.80, 7.73, col = colours$secondary, lwd = 1.3)
  draw_signature_badge(12.27, 7.87, "up", "P-up", width = 0.78)
  draw_signature_badge(13.14, 7.87, "down", "P-down", width = 0.84)
  draw_signature_badge(14.02, 7.87, "both", "Both", width = 0.78)
  graphics::text(
    13.15, 7.40,
    "DEG set unions • no pooled model refit\ndirection discordance retained + flagged",
    cex = 0.45, col = colours$text
  )
  draw_pill(
    16.14, 7.73, 1.86, 0.55,
    paste0("54 × 5 × 3\n= ", format_count(v[["secondary_planned_runs"]])),
    fill = "white", border = colours$secondary, cex = 0.52, lty = 2
  )
}

draw_construction_panel <- function() {
  draw_panel(0.35, 2.15, 8.85, 6.67, "C", "Construct and qualify one run")

  rounded_box(0.62, 3.08, 2.62, 5.95, fill = "#FBFCFC", border = "#B5C0C7",
              radius = 0.12, lwd = 1.05)
  graphics::text(1.62, 5.68, "1  Candidate query Q₀", cex = 0.62,
                 font = 2, col = colours$ink)
  graphics::text(1.62, 5.38, "core-mito DEGs", cex = 0.50,
                 col = colours$text)
  draw_signature_badge(1.62, 4.92, "up", "AD-up", width = 1.05)
  draw_signature_badge(1.62, 4.40, "down", "AD-down", width = 1.10)
  draw_signature_badge(1.62, 3.88, "both", "Both", width = 0.95)
  graphics::text(1.62, 3.37, "choose exactly one\nsignature per run",
                 cex = 0.49, col = colours$muted)

  draw_arrow(2.70, 4.52, 3.08, 4.52, col = colours$ink, lwd = 1.35)

  rounded_box(3.15, 3.08, 5.62, 5.95, fill = "#FBFCFC", border = "#B5C0C7",
              radius = 0.12, lwd = 1.05)
  graphics::text(4.385, 5.68, "2  Exact tested genes", cex = 0.62,
                 font = 2, col = colours$ink)
  rounded_box(3.40, 4.70, 5.37, 5.30, fill = colours$primary_fill,
              border = colours$primary, radius = 0.09, lwd = 1.0)
  graphics::text(3.57, 5.13, "PRIMARY", adj = c(0, 0.5), cex = 0.49,
                 font = 2, col = colours$primary)
  graphics::text(4.385, 4.88, "exact stratum contrast", cex = 0.49,
                 col = colours$text)
  rounded_box(3.40, 3.80, 5.37, 4.50, fill = colours$secondary_fill,
              border = colours$secondary, radius = 0.09, lwd = 1.0, lty = 2)
  graphics::text(3.57, 4.32, "SECONDARY", adj = c(0, 0.5), cex = 0.49,
                 font = 2, col = colours$secondary)
  graphics::text(4.385, 4.03, "intersection across\nall pool members",
                 cex = 0.48, col = colours$text)
  graphics::text(4.385, 3.43, "Pool query = union\nPool tested set = intersection",
                 cex = 0.48, font = 2, col = colours$ink)

  draw_arrow(5.70, 4.52, 6.03, 4.52, col = colours$ink, lwd = 1.35)

  rounded_box(6.10, 3.08, 8.58, 5.95, fill = "#FBFCFC", border = "#B5C0C7",
              radius = 0.12, lwd = 1.05)
  graphics::text(7.34, 5.68, "3  Induce network", cex = 0.62,
                 font = 2, col = colours$ink)
  draw_small_network(7.34, 4.85, scale = 0.75, query_nodes = c(3L, 5L, 6L))
  graphics::text(7.34, 4.13, "B = nodes in the run-specific graph",
                 cex = 0.45, col = colours$text)
  draw_pill(
    7.34, 3.70, 1.72, 0.38, "Q = Q₀ ∩ B",
    fill = colours$query_fill, border = colours$query, cex = 0.49
  )
  draw_pill(
    7.34, 3.31, 2.05, 0.34, "eligible when |Q| ≥ 3",
    fill = colours$success_fill, border = colours$success,
    col = colours$success, cex = 0.48
  )

  rounded_box(0.62, 2.37, 8.58, 2.86, fill = colours$skip_fill,
              border = "#B8C1C7", radius = 0.08, lwd = 0.9, lty = 2)
  graphics::text(
    4.60, 2.615,
    "Explicit skip status: source incomplete  •  induced network empty  •  effective query < 3       (3–9 genes: small-query warning)",
    cex = 0.48, col = colours$skip
  )
}

draw_kda_network <- function() {
  pts <- data.frame(
    x = c(9.78, 10.78, 10.78, 11.82, 11.82, 11.82, 12.88, 12.88, 12.88),
    y = c(4.72, 5.20, 4.28, 5.52, 4.72, 3.98, 5.42, 4.70, 4.05),
    query = c(FALSE, TRUE, FALSE, FALSE, TRUE, FALSE, TRUE, FALSE, TRUE)
  )
  edges <- rbind(
    c(1, 2), c(1, 3), c(2, 4), c(2, 5), c(3, 5), c(3, 6),
    c(4, 7), c(5, 7), c(5, 8), c(6, 8), c(6, 9)
  )
  graphics::text(c(10.78, 11.82, 12.88), rep(5.83, 3),
                 c("layer 1", "layer 2", "layer 3"), cex = 0.45,
                 font = 2, col = colours$muted)
  graphics::segments(c(10.33, 11.35, 12.41), 5.68,
                     c(11.23, 12.29, 13.35), 5.68,
                     col = "#D2D9DD", lwd = 1.0)
  for (i in seq_len(nrow(edges))) {
    a <- edges[i, 1L]
    b <- edges[i, 2L]
    draw_arrow(pts$x[a], pts$y[a], pts$x[b], pts$y[b],
               col = "#7E8E98", lwd = 1.05, length = 0.05)
  }
  draw_node(
    pts$x[[1L]], pts$y[[1L]], fill = colours$primary,
    border = "#0C5654", cex = 2.05, label = "KD", label_cex = 0.49,
    text_col = "white"
  )
  for (i in 2:nrow(pts)) {
    if (pts$query[[i]]) {
      draw_node(pts$x[[i]], pts$y[[i]], colours$query_fill,
                colours$query, cex = 1.30)
    } else {
      draw_node(pts$x[[i]], pts$y[[i]], "#E2E7EA",
                colours$network_dark, cex = 1.18)
    }
  }
  graphics::text(9.78, 4.22, "candidate\nupstream driver", cex = 0.44,
                 col = colours$text)
  graphics::points(10.16, 3.52, pch = 21, bg = colours$query_fill,
                   col = colours$query, cex = 1.0)
  graphics::text(10.38, 3.52, "effective query gene", adj = c(0, 0.5),
                 cex = 0.45, col = colours$text)
  graphics::points(11.65, 3.52, pch = 21, bg = "#E2E7EA",
                   col = colours$network_dark, cex = 1.0)
  graphics::text(11.87, 3.52, "background gene", adj = c(0, 0.5),
                 cex = 0.45, col = colours$text)
}

draw_kda_panel <- function() {
  draw_panel(9.05, 2.15, 17.65, 6.67, "D", "Directed NetWeaver enrichment test")
  draw_kda_network()

  rounded_box(13.62, 3.24, 17.38, 5.98, fill = "#FBFCFC",
              border = "#B5C0C7", radius = 0.12, lwd = 1.05)
  graphics::text(13.88, 5.70, "Is the query concentrated downstream?",
                 adj = c(0, 0.5), cex = 0.60, font = 2, col = colours$ink)
  graphics::text(
    13.90, 5.25,
    "M  background genes        m  neighborhood genes\nk  query genes                  q  query genes in neighborhood",
    adj = c(0, 0.5), cex = 0.48, col = colours$text
  )
  draw_pill(
    15.50, 4.63, 2.84, 0.52,
    "fold enrichment = (q/m) / (k/M)",
    fill = colours$query_fill, border = colours$query, cex = 0.50
  )
  graphics::text(
    15.50, 4.12,
    "one-sided hypergeometric test\nBH correction across drivers within this run",
    cex = 0.50, col = colours$text
  )
  draw_pill(
    15.50, 3.62, 2.70, 0.40,
    "adjusted P ≤ 0.05",
    fill = colours$success_fill, border = colours$success,
    col = colours$success, cex = 0.52
  )

  rounded_box(9.38, 2.39, 17.38, 3.02, fill = "#F5F8F9",
              border = "#A9B6BE", radius = 0.09, lwd = 1.0)
  graphics::text(
    9.62, 2.82,
    "REPORT",
    adj = c(0, 0.5), cex = 0.48, font = 2, col = colours$muted
  )
  graphics::text(
    11.50, 2.70,
    "Putative key driver\nbest layer • overlap • enrichment • adjusted P",
    cex = 0.50, font = 2, col = colours$ink
  )
  graphics::segments(13.78, 2.48, 13.78, 2.92, col = "#C1C9CE", lwd = 1)
  graphics::text(
    15.52, 2.70,
    "No driver passes cutoff\n= completed, not failed",
    cex = 0.50, col = colours$skip
  )
  graphics::text(
    15.50, 3.15,
    "directed • layers 1–3 • no signature expansion • overlap genes returned",
    cex = 0.42, col = colours$muted
  )
}

draw_outcome_ribbon <- function(v) {
  rounded_box(0.35, 0.26, 17.65, 1.92, fill = "#F7F9FA",
              border = "#C3CDD3", radius = 0.12, lwd = 1.05)
  graphics::text(0.60, 1.72, "VALIDATED PRODUCTION OUTCOME",
                 adj = c(0, 0.5), cex = 0.59, font = 2,
                 col = colours$ink)

  draw_pill(
    1.40, 1.18, 1.82, 0.58,
    paste0(format_count(v[["planned_runs"]]), "\nplanned"),
    fill = "white", border = colours$ink, cex = 0.49
  )
  draw_arrow(2.35, 1.18, 3.03, 1.18, col = colours$ink, lwd = 1.35)
  draw_pill(
    4.00, 1.18, 1.82, 0.58,
    paste0(format_count(v[["eligible_runs"]]), "\neligible"),
    fill = colours$primary_fill, border = colours$primary, cex = 0.49
  )
  draw_arrow(4.95, 1.18, 5.62, 1.18, col = colours$primary, lwd = 1.35)
  draw_pill(
    6.72, 1.18, 2.02, 0.58,
    paste0(format_count(v[["significant_runs"]]), " runs with ≥1\nsignificant driver"),
    fill = colours$success_fill, border = colours$success,
    col = colours$success, cex = 0.48
  )
  draw_arrow(7.78, 1.18, 8.35, 1.18, col = colours$success, lwd = 1.35)
  draw_pill(
    9.55, 1.18, 2.25, 0.58,
    paste0(format_count(v[["significant_driver_rows"]]),
           " significant\ndriver-by-run rows"),
    fill = colours$query_fill, border = colours$query, cex = 0.48
  )

  draw_pill(
    12.05, 1.18, 1.76, 0.58,
    paste0(format_count(v[["skipped_runs"]]), " skipped\nexplicit reasons"),
    fill = colours$skip_fill, border = colours$skip, col = colours$skip,
    cex = 0.48, lty = 2
  )
  draw_pill(
    14.10, 1.18, 1.46, 0.58,
    paste0(format_count(v[["no_significant_runs"]]),
           " completed\nno significant"),
    fill = colours$skip_fill, border = "#A5B0B7", col = colours$skip,
    cex = 0.45
  )
  draw_pill(
    15.72, 1.18, 1.22, 0.58,
    paste0(format_count(v[["failed_runs"]]), " failed"),
    fill = "white", border = colours$success, col = colours$success,
    cex = 0.49
  )
  draw_pill(
    17.03, 1.18, 0.92, 0.58,
    paste0(v[["validation_checks_passed"]], "/",
           v[["validation_checks_passed"]], "\nchecks"),
    fill = colours$success_fill, border = colours$success,
    col = colours$success, cex = 0.46
  )
  graphics::text(
    9.00, 0.53,
    "Primary strata are the main analysis • pooled summaries reuse member information • BH correction is within each run • enrichment prioritizes candidates; it does not prove causality",
    cex = 0.48, col = colours$muted
  )
}

draw_workflow <- function(values) {
  old <- graphics::par(
    mar = c(0.10, 0.10, 0.10, 0.10),
    xaxs = "i", yaxs = "i", family = "sans", bg = "white"
  )
  on.exit(graphics::par(old), add = TRUE)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 18), ylim = c(0, 11), asp = NA)

  graphics::text(
    0.40, 10.70,
    "Cell-type-specific mitochondrial key-driver analysis",
    adj = c(0, 0.5), cex = 1.52, font = 2, col = colours$ink
  )
  graphics::text(
    0.42, 10.34,
    "From stratified mitochondrial AD signatures to directed network-neighborhood enrichment",
    adj = c(0, 0.5), cex = 0.68, col = colours$muted
  )
  draw_pill(
    16.55, 10.57, 2.18, 0.46,
    "core mitochondrial universe",
    fill = "#EEF4E7", border = "#6C8A4F", cex = 0.52,
    col = "#4F6B39"
  )

  draw_input_panel()
  draw_analysis_grid_panel(values)
  draw_construction_panel()
  draw_kda_panel()
  draw_outcome_ribbon(values)

  draw_arrow(4.16, 8.55, 4.34, 8.55, col = colours$ink, lwd = 1.55,
             length = 0.065)
  graphics::segments(11.00, 6.94, 11.00, 6.78, col = colours$ink, lwd = 1.4)
  graphics::segments(11.00, 6.78, 4.60, 6.78, col = colours$ink, lwd = 1.4)
  draw_arrow(4.60, 6.78, 4.60, 6.68, col = colours$ink, lwd = 1.4,
             length = 0.055)
  draw_arrow(8.86, 4.42, 9.04, 4.42, col = colours$ink, lwd = 1.55,
             length = 0.065)

  graphics::box(col = NA)
}

write_tsv_atomic <- function(x, path) {
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  on.exit(if (file.exists(tmp)) unlink(tmp), add = TRUE)
  utils::write.table(
    x, tmp, sep = "\t", quote = FALSE, row.names = FALSE,
    col.names = TRUE, na = "NA"
  )
  if (!file.rename(tmp, path)) {
    stop("Could not publish table: ", path, call. = FALSE)
  }
}

write_graphic_atomic <- function(path, open_device, draw_fun) {
  extension <- tools::file_ext(path)
  tmp <- file.path(
    dirname(path),
    paste0(".", tools::file_path_sans_ext(basename(path)), ".tmp.",
           Sys.getpid(), ".", extension)
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
input_dir <- normalizePath(absolute_path(args$input_dir, project_root),
                           mustWork = TRUE)
output_dir <- absolute_path(args$output_dir, project_root)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!capabilities("cairo")) {
  stop("This R installation lacks Cairo graphics support", call. = FALSE)
}
if (!requireNamespace("digest", quietly = TRUE)) {
  stop("The digest R package is required for SHA-256 manifests", call. = FALSE)
}

message("Validating KDA production bundle")
inputs <- validate_inputs(input_dir)
values <- inputs$values

svg_path <- file.path(output_dir, paste0(args$basename, ".svg"))
pdf_path <- file.path(output_dir, paste0(args$basename, ".pdf"))
png_path <- file.path(output_dir, paste0(args$basename, ".png"))
data_path <- file.path(output_dir, paste0(args$basename, "_plotted_data.tsv"))
checks_path <- file.path(output_dir, paste0(args$basename, "_checks.tsv"))
manifest_path <- file.path(output_dir, paste0(args$basename, "_manifest.tsv"))

write_tsv_atomic(inputs$metrics, data_path)
write_tsv_atomic(inputs$figure_checks, checks_path)

message("Writing ", svg_path)
write_graphic_atomic(
  svg_path,
  function(path) grDevices::svg(
    path, width = 18, height = 11, pointsize = 12, onefile = TRUE,
    family = "sans", bg = "white", antialias = "subpixel"
  ),
  function() draw_workflow(values)
)

message("Writing ", pdf_path)
write_graphic_atomic(
  pdf_path,
  function(path) grDevices::cairo_pdf(
    path, width = 18, height = 11, pointsize = 12,
    family = "sans", bg = "white", onefile = TRUE
  ),
  function() draw_workflow(values)
)

message("Writing ", png_path)
write_graphic_atomic(
  png_path,
  function(path) grDevices::png(
    path, width = 5400, height = 3300, units = "px", res = 300,
    pointsize = 12, bg = "white", type = "cairo", antialias = "subpixel"
  ),
  function() draw_workflow(values)
)

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE)
} else {
  NA_character_
}

artifact_paths <- c(
  inputs$input_paths,
  script = script_path,
  figure_svg = svg_path,
  figure_pdf = pdf_path,
  figure_png = png_path,
  plotted_data = data_path,
  figure_checks = checks_path
)
artifact_roles <- c(
  "input_status", "input_run_manifest", "input_checks", "input_artifacts",
  "figure_script", "figure_svg", "figure_pdf", "figure_png",
  "plotted_data", "figure_checks"
)
manifest <- data.frame(
  artifact_role = artifact_roles,
  file = basename(artifact_paths),
  bytes = as.numeric(file.info(artifact_paths)$size),
  sha256 = vapply(
    artifact_paths,
    function(path) digest::digest(file = path, algo = "sha256", serialize = FALSE),
    character(1)
  ),
  stringsAsFactors = FALSE
)
write_tsv_atomic(manifest, manifest_path)

message(
  "Mitochondrial KDA workflow figure complete: ",
  format_count(values[["planned_runs"]]), " planned runs; ",
  format_count(values[["eligible_runs"]]), " eligible; ",
  format_count(values[["significant_runs"]]), " with significant drivers"
)
