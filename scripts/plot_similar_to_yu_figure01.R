#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_args <- function(args) {
  out <- list(output = "results/11_similar_to_yu_figure01.pdf")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/plot_similar_to_yu_figure01.R ",
        "[--output results/11_similar_to_yu_figure01.pdf]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!identical(key, "--output") || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out$output <- args[[i + 1L]]
    i <- i + 2L
  }
  out
}

as_logical <- function(x) {
  !is.na(x) & toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_tsv <- function(x, path, gzip = FALSE) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid(), if (gzip) ".gz" else "")
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA",
    compress = if (gzip) "gzip" else "none"
  )
  if (!file.rename(tmp, path)) stop("Could not publish ", path, call. = FALSE)
}

shade_color <- function(base_color, fraction) {
  fraction <- min(max(as.numeric(fraction), 0), 1)
  if (fraction <= 0) return("#FFFFFF")
  strength <- 0.16 + 0.84 * sqrt(fraction)
  base <- grDevices::col2rgb(base_color)[, 1L] / 255
  mixed <- 1 - (1 - base) * strength
  grDevices::rgb(mixed[[1L]], mixed[[2L]], mixed[[3L]])
}

short_group <- function(sex, apoe) {
  paste(ifelse(sex == "Female", "F", "M"), apoe)
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("data.table", quietly = TRUE)) {
  stop("Package 'data.table' is required", call. = FALSE)
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
output_path <- absolute_path(args$output, project_root)
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)

mast_dir <- file.path(project_root, "results", "minerva_production", "08_mast")
annotation_path <- file.path(
  project_root, "results", "minerva_production", "03_annotations",
  "tested_gene_universe.tsv"
)
manifest_path <- file.path(project_root, "config", "minerva_rds_manifest.tsv")

mast_paths <- sort(list.files(
  mast_dir, pattern = "[.]mast_de[.]tsv[.]gz$", full.names = TRUE
))
contrast_status_paths <- sort(list.files(
  mast_dir, pattern = "[.]mast_contrast_status[.]tsv$", full.names = TRUE
))
mast_status_paths <- sort(list.files(
  mast_dir, pattern = "[.]mast_de_status[.]tsv$", full.names = TRUE
))

if (length(mast_paths) != 9L || length(contrast_status_paths) != 9L ||
    length(mast_status_paths) != 9L) {
  stop(
    "Expected nine Phase 08 MAST result, contrast-status, and task-status files",
    call. = FALSE
  )
}
if (!file.exists(annotation_path) || !file.exists(manifest_path)) {
  stop("Required annotation or RDS manifest is missing", call. = FALSE)
}

read_many <- function(paths) {
  data.table::rbindlist(
    lapply(paths, data.table::fread, showProgress = FALSE),
    fill = TRUE, use.names = TRUE
  )
}

message("Reading Phase 08 MAST task statuses")
mast_status <- read_many(mast_status_paths)
if (nrow(mast_status) != 9L ||
    !all(mast_status$validation_status == "validated_complete")) {
  stop("Every Phase 08 MAST task must be validated_complete", call. = FALSE)
}

message("Reading Phase 08 MAST contrast statuses")
status <- read_many(contrast_status_paths)
status[, paper_matched := as_logical(paper_matched)]
direct_status <- status[
  paper_matched & contrast_family == "AD_vs_NCI" &
    grepl("^AD_vs_NCI__(Female|Male)__(e2|e33|e4)$", contrast_name)
]
direct_status[, sex := sub(
  "^AD_vs_NCI__([^_]+)__.*$", "\\1", contrast_name
)]
direct_status[, apoe_group := sub(
  "^AD_vs_NCI__[^_]+__(.*)$", "\\1", contrast_name
)]
direct_status[, group_id := paste(sex, apoe_group, sep = "__")]
direct_status[, eligible := terminal_status == "validated_complete"]

if (any(direct_status$terminal_status == "failed")) {
  stop("At least one paper-matched MAST contrast failed", call. = FALSE)
}

rds_manifest <- data.table::fread(manifest_path)
rds_manifest <- rds_manifest[as_logical(enabled)]
preferred_rds_order <- c(
  "astrocytes", "excitatory_set1", "excitatory_set2", "excitatory_set3",
  "inhibitory", "oligodendrocytes", "opcs", "immune", "vasculature"
)
if (!setequal(rds_manifest$rds_id, preferred_rds_order)) {
  stop("Production RDS manifest differs from the expected nine RDS IDs", call. = FALSE)
}

cell_meta <- unique(direct_status[, .(rds_id, cell_type_high_resolution)])
cell_meta[, rds_rank := match(rds_id, preferred_rds_order)]
data.table::setorder(cell_meta, rds_rank, cell_type_high_resolution)
cell_order <- cell_meta$cell_type_high_resolution
if (nrow(cell_meta) != 54L || anyDuplicated(cell_order)) {
  stop("Expected exactly 54 uniquely named fine cell types", call. = FALSE)
}

group_order <- c(
  "Female__e2", "Female__e33", "Female__e4",
  "Male__e2", "Male__e33", "Male__e4"
)
if (nrow(direct_status) != length(cell_order) * length(group_order)) {
  stop("Direct MAST status grid is not 54 cell types by six groups", call. = FALSE)
}
status_key <- paste(
  direct_status$cell_type_high_resolution, direct_status$group_id, sep = "\r"
)
if (anyDuplicated(status_key) || !setequal(unique(direct_status$group_id), group_order)) {
  stop("Direct MAST status keys or group definitions are invalid", call. = FALSE)
}

message("Reading Phase 08 MAST differential-expression rows")
mast <- read_many(mast_paths)
mast <- mast[
  contrast_family == "AD_vs_NCI" &
    grepl("^AD_vs_NCI__(Female|Male)__(e2|e33|e4)$", contrast_name)
]
mast[, paper_deg := as_logical(paper_deg)]
mast[, sex := sub("^AD_vs_NCI__([^_]+)__.*$", "\\1", contrast_name)]
mast[, apoe_group := sub("^AD_vs_NCI__[^_]+__(.*)$", "\\1", contrast_name)]
mast[, group_id := paste(sex, apoe_group, sep = "__")]

paper_rule <- is.finite(mast$fdr_bh_within_contrast) &
  mast$fdr_bh_within_contrast < 0.05 &
  is.finite(mast$logFC) &
  abs(mast$logFC) > mast$paper_effect_threshold_log2 &
  (mast$pct_ad >= 0.10 | mast$pct_nci >= 0.10)
if (!identical(as.logical(mast$paper_deg), as.logical(paper_rule))) {
  mismatch <- sum(mast$paper_deg != paper_rule, na.rm = TRUE)
  stop("Phase 08 paper_deg validation failed for ", mismatch, " rows", call. = FALSE)
}

result_key <- paste(mast$rds_id, mast$contrast_id, mast$gene, sep = "\r")
if (anyDuplicated(result_key)) {
  stop("Phase 08 MAST result keys are not unique", call. = FALSE)
}

message("Reading frozen MitoCarta annotations")
annotations <- data.table::fread(
  annotation_path,
  select = c("rds_id", "feature", "mitocarta_symbol", "is_mitocarta"),
  showProgress = FALSE
)
annotations[, is_mitocarta := as_logical(is_mitocarta)]
mitocarta_map <- annotations[
  is_mitocarta & !is.na(mitocarta_symbol) & nzchar(mitocarta_symbol),
  .(rds_id, gene = feature, canonical_gene = mitocarta_symbol)
]
if (anyDuplicated(paste(mitocarta_map$rds_id, mitocarta_map$gene, sep = "\r"))) {
  stop("MitoCarta feature keys are not unique", call. = FALSE)
}

mito <- merge(
  mast, mitocarta_map,
  by = c("rds_id", "gene"), all = FALSE, sort = FALSE
)
if (!nrow(mito)) stop("No Phase 08 genes mapped to MitoCarta", call. = FALSE)
mito[, feature_state := data.table::fcase(
  paper_deg & logFC > 0, 1L,
  paper_deg & logFC < 0, -1L,
  default = 0L
)]

# Count each canonical MitoCarta gene once per contrast. If several assayed
# aliases map to one canonical gene, a canonical DEG is called when at least
# one mapped Phase 08 feature is a paper DEG. Opposite significant aliases are
# recorded as direction conflicts and excluded from directional summaries.
canonical <- mito[, .(
  source_features = paste(sort(unique(gene)), collapse = ";"),
  source_feature_count = data.table::uniqueN(gene),
  any_up = any(feature_state == 1L),
  any_down = any(feature_state == -1L)
), by = .(
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  sex, apoe_group, group_id, canonical_gene
)]
canonical[, canonical_state := data.table::fcase(
  any_up & !any_down, 1L,
  any_down & !any_up, -1L,
  !any_up & !any_down, 0L,
  default = NA_integer_
)]
canonical[, direction_conflict := is.na(canonical_state)]
conflicts <- canonical[direction_conflict == TRUE]
message("Canonical alias-direction conflicts recorded: ", nrow(conflicts))

canonical_key <- paste(
  canonical$contrast_id, canonical$canonical_gene, sep = "\r"
)
if (anyDuplicated(canonical_key)) {
  stop("Canonical MitoCarta contrast keys are not unique", call. = FALSE)
}

direct_summary <- canonical[, .(
  tested_mitocarta = .N,
  direction_conflicts = sum(direction_conflict),
  up_degs = sum(canonical_state == 1L, na.rm = TRUE),
  down_degs = sum(canonical_state == -1L, na.rm = TRUE),
  unchanged = sum(canonical_state == 0L, na.rm = TRUE)
), by = .(
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  sex, apoe_group, group_id
)]

main_tiles <- merge(
  direct_status[, .(
    rds_id, cell_type_high_resolution, contrast_id, contrast_name,
    sex, apoe_group, group_id, eligible, terminal_status,
    donors_ad, donors_nci, status_message = message
  )],
  direct_summary,
  by = c(
    "rds_id", "cell_type_high_resolution", "contrast_id", "contrast_name",
    "sex", "apoe_group", "group_id"
  ),
  all.x = TRUE, sort = FALSE
)
if (any(main_tiles$eligible & is.na(main_tiles$tested_mitocarta))) {
  stop("At least one eligible MAST contrast has no tested MitoCarta genes", call. = FALSE)
}
if (any(
  main_tiles$eligible &
    main_tiles$up_degs + main_tiles$down_degs + main_tiles$unchanged +
      main_tiles$direction_conflicts != main_tiles$tested_mitocarta
)) {
  stop("Direct MitoCarta state counts do not sum to tested denominators", call. = FALSE)
}
main_tiles[, donor_label := ifelse(
  eligible, paste0(donors_ad, "/", donors_nci), ""
)]

comparison_categories <- c(
  "same_direction", "first_only", "second_only", "opposite_direction"
)
category_colors <- c(
  same_direction = "#2CA25F",
  first_only = "#F28E2B",
  second_only = "#756BB1",
  opposite_direction = "#DE2D26"
)

build_pair_panel <- function(panel_id, definitions) {
  tile_rows <- list()
  gene_rows <- list()
  for (definition_index in seq_len(nrow(definitions))) {
    definition <- definitions[definition_index]
    pair_id <- definition$pair_id
    for (cell_type in cell_order) {
      first_group <- paste(definition$first_sex, definition$first_apoe, sep = "__")
      second_group <- paste(definition$second_sex, definition$second_apoe, sep = "__")
      first_status <- direct_status[
        cell_type_high_resolution == cell_type & group_id == first_group
      ]
      second_status <- direct_status[
        cell_type_high_resolution == cell_type & group_id == second_group
      ]
      if (nrow(first_status) != 1L || nrow(second_status) != 1L) {
        stop("Could not identify both MAST statuses for ", pair_id, " / ", cell_type)
      }
      eligible <- first_status$eligible[[1L]] && second_status$eligible[[1L]]
      donor_label <- if (eligible) paste0(
        first_status$donors_ad[[1L]], "/", first_status$donors_nci[[1L]], "|",
        second_status$donors_ad[[1L]], "/", second_status$donors_nci[[1L]]
      ) else ""
      if (eligible) {
        first <- canonical[
          cell_type_high_resolution == cell_type & group_id == first_group,
          .(canonical_gene, first_state = canonical_state)
        ]
        second <- canonical[
          cell_type_high_resolution == cell_type & group_id == second_group,
          .(canonical_gene, second_state = canonical_state)
        ]
        paired <- merge(first, second, by = "canonical_gene", all = FALSE)
        if (!nrow(paired)) {
          stop("No jointly tested MitoCarta genes for ", pair_id, " / ", cell_type)
        }
        paired[, category := data.table::fcase(
          is.na(first_state) | is.na(second_state),
          "direction_conflict_excluded",
          first_state != 0L & second_state != 0L & first_state == second_state,
          "same_direction",
          first_state != 0L & second_state == 0L, "first_only",
          first_state == 0L & second_state != 0L, "second_only",
          first_state != 0L & second_state != 0L & first_state == -second_state,
          "opposite_direction",
          default = "neither"
        )]
        jointly_tested <- nrow(paired)
        direction_conflicts_excluded <- sum(
          paired$category == "direction_conflict_excluded"
        )
        denominator <- jointly_tested - direction_conflicts_excluded
        if (denominator <= 0L) {
          stop("No direction-classifiable MitoCarta genes for ", pair_id,
               " / ", cell_type)
        }
        counts <- table(factor(
          paired$category[paired$category != "direction_conflict_excluded"],
          levels = c(comparison_categories, "neither")
        ))
        if (sum(counts) != denominator) {
          stop("Pairwise categories do not partition the tested intersection")
        }
        paired[, `:=`(
          record_type = "pairwise_state",
          panel = panel_id,
          pair_id = pair_id,
          pair_label = definition$pair_label,
          cell_type_high_resolution = cell_type,
          first_group = first_group,
          second_group = second_group,
          jointly_tested_mitocarta = jointly_tested,
          direction_conflicts_excluded = direction_conflicts_excluded,
          jointly_classifiable_mitocarta = denominator
        )]
        gene_rows[[length(gene_rows) + 1L]] <- paired
      } else {
        denominator <- NA_integer_
        jointly_tested <- NA_integer_
        direction_conflicts_excluded <- NA_integer_
        counts <- stats::setNames(rep(NA_integer_, 5L), c(
          comparison_categories, "neither"
        ))
      }
      for (category in comparison_categories) {
        category_short <- switch(
          category,
          same_direction = "same direction",
          first_only = paste0(definition$first_short, " only"),
          second_only = paste0(definition$second_short, " only"),
          opposite_direction = "opposite directions"
        )
        tile_rows[[length(tile_rows) + 1L]] <- data.table::data.table(
          panel = panel_id,
          pair_id = pair_id,
          pair_label = definition$pair_label,
          row_id = paste(pair_id, category, sep = "::"),
          row_label = paste0(definition$pair_label, " | ", category_short),
          category = category,
          rds_id = first_status$rds_id[[1L]],
          cell_type_high_resolution = cell_type,
          first_group = first_group,
          second_group = second_group,
          first_contrast_id = first_status$contrast_id[[1L]],
          second_contrast_id = second_status$contrast_id[[1L]],
          eligible = eligible,
          count = if (eligible) as.integer(counts[[category]]) else NA_integer_,
          tested_mitocarta = denominator,
          jointly_tested_mitocarta = jointly_tested,
          direction_conflicts_excluded = direction_conflicts_excluded,
          donor_label = donor_label,
          first_terminal_status = first_status$terminal_status[[1L]],
          second_terminal_status = second_status$terminal_status[[1L]]
        )
      }
    }
  }
  list(
    tiles = data.table::rbindlist(tile_rows, use.names = TRUE),
    genes = if (length(gene_rows)) {
      data.table::rbindlist(gene_rows, use.names = TRUE, fill = TRUE)
    } else {
      data.table::data.table()
    }
  )
}

female_definitions <- data.table::data.table(
  pair_id = c("female_e2_vs_e33", "female_e4_vs_e33", "female_e2_vs_e4"),
  pair_label = c("F e2 vs F e33", "F e4 vs F e33", "F e2 vs F e4"),
  first_sex = "Female", second_sex = "Female",
  first_apoe = c("e2", "e4", "e2"),
  second_apoe = c("e33", "e33", "e4"),
  first_short = c("F e2", "F e4", "F e2"),
  second_short = c("F e33", "F e33", "F e4")
)
male_definitions <- data.table::data.table(
  pair_id = c("male_e2_vs_e33", "male_e4_vs_e33", "male_e2_vs_e4"),
  pair_label = c("M e2 vs M e33", "M e4 vs M e33", "M e2 vs M e4"),
  first_sex = "Male", second_sex = "Male",
  first_apoe = c("e2", "e4", "e2"),
  second_apoe = c("e33", "e33", "e4"),
  first_short = c("M e2", "M e4", "M e2"),
  second_short = c("M e33", "M e33", "M e4")
)
sex_definitions <- data.table::data.table(
  pair_id = c("female_vs_male_e2", "female_vs_male_e33", "female_vs_male_e4"),
  pair_label = c("F vs M e2", "F vs M e33", "F vs M e4"),
  first_sex = "Female", second_sex = "Male",
  first_apoe = c("e2", "e33", "e4"),
  second_apoe = c("e2", "e33", "e4"),
  first_short = c("F e2", "F e33", "F e4"),
  second_short = c("M e2", "M e33", "M e4")
)

message("Building pairwise MitoCarta DEG classifications")
female_panel <- build_pair_panel("C", female_definitions)
male_panel <- build_pair_panel("D", male_definitions)
sex_panel <- build_pair_panel("E", sex_definitions)
pair_tiles <- data.table::rbindlist(list(
  female_panel$tiles, male_panel$tiles, sex_panel$tiles
), use.names = TRUE)
pair_genes <- data.table::rbindlist(list(
  female_panel$genes, male_panel$genes, sex_panel$genes
), use.names = TRUE, fill = TRUE)

if (any(pair_tiles$eligible & !is.finite(pair_tiles$tested_mitocarta))) {
  stop("Eligible pairwise tiles lack tested-gene denominators", call. = FALSE)
}
if (any(!pair_tiles$category %in% comparison_categories)) {
  stop("Unexpected plotted pairwise category", call. = FALSE)
}

rds_display <- c(
  astrocytes = "Astrocytes",
  excitatory_set1 = "Excitatory I",
  excitatory_set2 = "Excitatory II",
  excitatory_set3 = "Excitatory III",
  inhibitory = "Inhibitory",
  oligodendrocytes = "Oligodendrocytes",
  opcs = "OPCs",
  immune = "Immune",
  vasculature = "Vasculature"
)
rds_colors <- c(
  astrocytes = "#8DD3C7",
  excitatory_set1 = "#FFFFB3",
  excitatory_set2 = "#FDB462",
  excitatory_set3 = "#FB8072",
  inhibitory = "#80B1D3",
  oligodendrocytes = "#BEBADA",
  opcs = "#BC80BD",
  immune = "#CCEBC5",
  vasculature = "#D9D9D9"
)

cell_rds <- stats::setNames(cell_meta$rds_id, cell_meta$cell_type_high_resolution)

draw_heatmap <- function(
    tile_table, row_order, row_labels, row_colors,
    title, panel_label, subtitle, show_x_labels = TRUE,
    label_cex = 0.27) {
  nr <- length(row_order)
  nc <- length(cell_order)
  if (show_x_labels) {
    graphics::par(mar = c(10.2, 15.5, 4.2, 3.5), xpd = NA)
  } else {
    graphics::par(mar = c(1.2, 15.5, 4.2, 3.5), xpd = NA)
  }
  graphics::plot.new()
  graphics::plot.window(
    xlim = c(0.5, nc + 0.5), ylim = c(0.5, nr + 1.45), xaxs = "i", yaxs = "i"
  )

  max_count <- max(tile_table$count[tile_table$eligible], na.rm = TRUE)
  if (!is.finite(max_count) || max_count < 1) max_count <- 1
  lookup <- stats::setNames(
    seq_len(nrow(tile_table)),
    paste(tile_table$row_id, tile_table$cell_type_high_resolution, sep = "\r")
  )

  for (row_index in seq_along(row_order)) {
    row_id <- row_order[[row_index]]
    y <- nr - row_index + 1L
    for (column_index in seq_along(cell_order)) {
      cell_type <- cell_order[[column_index]]
      index <- lookup[[paste(row_id, cell_type, sep = "\r")]]
      if (is.null(index) || is.na(index)) {
        stop("Missing plotting tile: ", row_id, " / ", cell_type)
      }
      tile <- tile_table[index]
      if (!tile$eligible[[1L]]) {
        fill <- "#D9D9D9"
        label <- "NE"
        text_color <- "#555555"
      } else {
        fill <- shade_color(row_colors[[row_id]], tile$count[[1L]] / max_count)
        label <- paste0(
          tile$count[[1L]], "/", tile$tested_mitocarta[[1L]], "\n",
          tile$donor_label[[1L]]
        )
        text_color <- if (tile$count[[1L]] / max_count > 0.45) "white" else "#222222"
      }
      graphics::rect(
        column_index - 0.5, y - 0.5, column_index + 0.5, y + 0.5,
        col = fill, border = "white", lwd = 0.35
      )
      graphics::text(
        column_index, y, labels = label, cex = label_cex,
        col = text_color, font = if (identical(label, "NE")) 2 else 1
      )
    }
  }

  y_positions <- nr - seq_along(row_order) + 1L
  graphics::axis(
    2, at = y_positions, labels = row_labels[row_order],
    las = 1, tick = FALSE, cex.axis = 0.60, line = -0.3
  )
  for (i in seq_along(row_order)) {
    y <- y_positions[[i]]
    graphics::rect(
      0.05, y - 0.24, 0.32, y + 0.24,
      col = row_colors[[row_order[[i]]]], border = NA
    )
  }

  if (show_x_labels) {
    graphics::text(
      seq_len(nc), 0.36, labels = cell_order,
      srt = 90, adj = c(1, 0.5), cex = 0.42
    )
  }

  group_runs <- rle(unname(cell_rds[cell_order]))
  ends <- cumsum(group_runs$lengths)
  starts <- c(1L, head(ends, -1L) + 1L)
  for (i in seq_along(group_runs$values)) {
    rds_id <- group_runs$values[[i]]
    graphics::rect(
      starts[[i]] - 0.5, nr + 0.68, ends[[i]] + 0.5, nr + 0.92,
      col = rds_colors[[rds_id]], border = "white", lwd = 0.5
    )
    graphics::text(
      mean(c(starts[[i]], ends[[i]])), nr + 1.13,
      labels = rds_display[[rds_id]], cex = 0.49, font = 2
    )
    if (i < length(group_runs$values)) {
      graphics::abline(v = ends[[i]] + 0.5, col = "#555555", lwd = 0.8)
    }
  }

  graphics::box(lwd = 0.8)
  graphics::mtext(
    paste0(panel_label, ". ", title), side = 3, line = 2.4,
    adj = 0, font = 2, cex = 0.92
  )
  graphics::mtext(subtitle, side = 3, line = 1.15, adj = 0, cex = 0.60)
  graphics::mtext(
    paste0("Color intensity scales with category count (page maximum = ", max_count, ")"),
    side = 4, line = 1.2, cex = 0.53
  )
}

make_main_plot_table <- function(direction) {
  if (!direction %in% c("up", "down")) stop("Invalid direction")
  value_column <- if (direction == "up") "up_degs" else "down_degs"
  table <- data.table::copy(main_tiles)
  table[, `:=`(
    row_id = group_id,
    count = get(value_column),
    tested_mitocarta = tested_mitocarta
  )]
  table
}

main_row_labels <- stats::setNames(
  c("Female e2", "Female e33", "Female e4", "Male e2", "Male e33", "Male e4"),
  group_order
)
up_row_colors <- stats::setNames(rep("#CB181D", length(group_order)), group_order)
down_row_colors <- stats::setNames(rep("#2171B5", length(group_order)), group_order)

pair_row_orders <- list()
pair_row_labels <- list()
pair_row_colors <- list()
for (panel in c("C", "D", "E")) {
  panel_value <- panel
  table <- pair_tiles[panel == panel_value]
  pair_ids <- unique(table$pair_id)
  order <- unlist(lapply(pair_ids, function(pair_id) {
    paste(pair_id, comparison_categories, sep = "::")
  }), use.names = FALSE)
  labels <- unique(table[, .(row_id, row_label)])
  colors <- unique(table[, .(row_id, category)])
  pair_row_orders[[panel]] <- order
  pair_row_labels[[panel]] <- stats::setNames(labels$row_label, labels$row_id)
  pair_row_colors[[panel]] <- stats::setNames(
    category_colors[colors$category], colors$row_id
  )
}

message("Writing companion tile and gene-classification tables")
tile_output_path <- sub("[.]pdf$", "_tiles.tsv", output_path, ignore.case = TRUE)
gene_output_path <- sub("[.]pdf$", "_genes.tsv.gz", output_path, ignore.case = TRUE)
checks_output_path <- sub("[.]pdf$", "_checks.tsv", output_path, ignore.case = TRUE)

main_tile_output <- data.table::rbindlist(list(
  make_main_plot_table("up")[, panel := "A"],
  make_main_plot_table("down")[, panel := "B"]
), use.names = TRUE, fill = TRUE)
main_tile_output[, category := ifelse(panel == "A", "upregulated", "downregulated")]
main_tile_output[, percent := ifelse(
  eligible, 100 * count / tested_mitocarta, NA_real_
)]
pair_tile_output <- data.table::copy(pair_tiles)
pair_tile_output[, percent := ifelse(
  eligible, 100 * count / tested_mitocarta, NA_real_
)]
tile_output <- data.table::rbindlist(list(
  main_tile_output,
  pair_tile_output
), use.names = TRUE, fill = TRUE)
tile_output[, `:=`(
  schema_version = "mitocarta_mast_yu_tiles_v1",
  method_branch = "mast",
  deg_rule = "phase08_paper_deg",
  annotation_source = "Human_MitoCarta3.0"
)]
data.table::setcolorder(tile_output, c(
  "schema_version", "panel", "method_branch", "category",
  "rds_id", "cell_type_high_resolution", "row_id", "row_label",
  "eligible", "count", "tested_mitocarta", "percent", "donor_label"
))
atomic_write_tsv(tile_output, tile_output_path)

direct_gene_output <- canonical[, .(
  schema_version = "mitocarta_mast_yu_genes_v1",
  record_type = "direct_state",
  panel = "A_B",
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  group_id, canonical_gene, canonical_state,
  direction_conflict, source_features, source_feature_count,
  pair_id = NA_character_, first_state = NA_integer_,
  second_state = NA_integer_, category = NA_character_,
  jointly_tested_mitocarta = NA_integer_,
  direction_conflicts_excluded = NA_integer_,
  jointly_classifiable_mitocarta = NA_integer_
)]
pair_gene_output <- pair_genes[, .(
  schema_version = "mitocarta_mast_yu_genes_v1",
  record_type, panel,
  rds_id = NA_character_, cell_type_high_resolution,
  contrast_id = NA_character_, contrast_name = NA_character_,
  group_id = NA_character_, canonical_gene,
  canonical_state = NA_integer_, direction_conflict = NA,
  source_features = NA_character_, source_feature_count = NA_integer_, pair_id,
  first_state, second_state, category, jointly_tested_mitocarta,
  direction_conflicts_excluded, jointly_classifiable_mitocarta
)]
gene_output <- data.table::rbindlist(list(
  direct_gene_output, pair_gene_output
), use.names = TRUE, fill = TRUE)
atomic_write_tsv(gene_output, gene_output_path, gzip = TRUE)

message("Rendering four-page PDF: ", output_path)
tmp_pdf <- paste0(output_path, ".tmp.", Sys.getpid(), ".pdf")
grDevices::pdf(
  tmp_pdf, width = 24, height = 14, onefile = TRUE,
  family = "Helvetica", useDingbats = FALSE
)
render_error <- NULL
tryCatch({
  graphics::layout(matrix(1:2, nrow = 2L), heights = c(1, 1.15))
  draw_heatmap(
    make_main_plot_table("up"), group_order, main_row_labels, up_row_colors,
    "Upregulated MitoCarta genes in AD", "A",
    "Phase 08 MAST paper_deg; label line 1 = DEGs/tested canonical MitoCarta genes; line 2 = AD/NCI donors",
    show_x_labels = FALSE, label_cex = 0.29
  )
  draw_heatmap(
    make_main_plot_table("down"), group_order, main_row_labels, down_row_colors,
    "Downregulated MitoCarta genes in AD", "B",
    "Phase 08 MAST paper_deg; label line 1 = DEGs/tested canonical MitoCarta genes; line 2 = AD/NCI donors",
    show_x_labels = TRUE, label_cex = 0.29
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    female_panel$tiles, pair_row_orders[["C"]], pair_row_labels[["C"]],
    pair_row_colors[["C"]],
    "APOE comparisons within females", "C",
    "Joint direction-classifiable Phase 08 MAST universe; alias-direction conflicts excluded; line 2 = first AD/NCI donors | second AD/NCI donors",
    show_x_labels = TRUE, label_cex = 0.245
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    male_panel$tiles, pair_row_orders[["D"]], pair_row_labels[["D"]],
    pair_row_colors[["D"]],
    "APOE comparisons within males", "D",
    "Joint direction-classifiable Phase 08 MAST universe; alias-direction conflicts excluded; line 2 = first AD/NCI donors | second AD/NCI donors",
    show_x_labels = TRUE, label_cex = 0.245
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    sex_panel$tiles, pair_row_orders[["E"]], pair_row_labels[["E"]],
    pair_row_colors[["E"]],
    "Female-versus-male comparisons within APOE groups", "E",
    "Joint direction-classifiable Phase 08 MAST universe; alias-direction conflicts excluded; line 2 = female AD/NCI donors | male AD/NCI donors",
    show_x_labels = TRUE, label_cex = 0.245
  )
}, error = function(e) {
  render_error <<- conditionMessage(e)
})
grDevices::dev.off()
if (!is.null(render_error)) {
  if (file.exists(tmp_pdf)) unlink(tmp_pdf)
  stop("Figure rendering failed: ", render_error, call. = FALSE)
}
if (!file.rename(tmp_pdf, output_path)) {
  stop("Could not publish final PDF", call. = FALSE)
}

checks <- data.table::data.table(
  schema_version = "mitocarta_mast_yu_checks_v1",
  check = c(
    "nine_phase08_tasks_validated",
    "direct_status_grid_54_by_6",
    "no_failed_direct_contrasts",
    "phase08_paper_deg_rule_reproduced",
    "all_plotted_genes_mitocarta",
    "canonical_direction_conflicts_recorded",
    "direct_states_partition_tested_genes",
    "pairwise_intersections_have_denominators",
    "all_panels_present",
    "pdf_exists_nonempty",
    "companion_tables_exist_nonempty"
  ),
  passed = c(
    nrow(mast_status) == 9L && all(mast_status$validation_status == "validated_complete"),
    nrow(direct_status) == 54L * 6L,
    !any(direct_status$terminal_status == "failed"),
    identical(as.logical(mast$paper_deg), as.logical(paper_rule)),
    nrow(mito) > 0L,
    sum(canonical$direction_conflict) == nrow(conflicts),
    all(
      main_tiles$up_degs[main_tiles$eligible] +
        main_tiles$down_degs[main_tiles$eligible] +
        main_tiles$unchanged[main_tiles$eligible] +
        main_tiles$direction_conflicts[main_tiles$eligible] ==
        main_tiles$tested_mitocarta[main_tiles$eligible]
    ),
    all(is.finite(pair_tiles$tested_mitocarta[pair_tiles$eligible])),
    identical(sort(unique(tile_output$panel)), c("A", "B", "C", "D", "E")),
    file.exists(output_path) && file.info(output_path)$size > 0,
    file.exists(tile_output_path) && file.info(tile_output_path)$size > 0 &&
      file.exists(gene_output_path) && file.info(gene_output_path)$size > 0
  ),
  observed = c(
    nrow(mast_status),
    nrow(direct_status),
    sum(direct_status$terminal_status == "failed"),
    sum(mast$paper_deg != paper_rule, na.rm = TRUE),
    data.table::uniqueN(canonical$canonical_gene),
    nrow(conflicts),
    sum(main_tiles$eligible),
    sum(pair_tiles$eligible),
    paste(sort(unique(tile_output$panel)), collapse = ";"),
    if (file.exists(output_path)) file.info(output_path)$size else 0,
    sum(file.exists(c(tile_output_path, gene_output_path)))
  ),
  expected = c(
    "9 validated_complete",
    "324",
    "0",
    "0 mismatches",
    ">0 canonical MitoCarta genes",
    "all conflicts explicitly recorded",
    "all eligible direct contrasts partitioned",
    "all eligible pairwise tiles",
    "A;B;C;D;E",
    ">0 bytes",
    "2"
  )
)
atomic_write_tsv(checks, checks_output_path)
if (any(!checks$passed)) {
  stop(
    "Figure checks failed: ", paste(checks$check[!checks$passed], collapse = ", "),
    call. = FALSE
  )
}

cat("Figure: ", output_path, "\n", sep = "")
cat("Pages: 4\n")
cat("Fine cell types: ", length(cell_order), "\n", sep = "")
cat("Unique canonical MitoCarta genes represented: ",
    data.table::uniqueN(canonical$canonical_gene), "\n", sep = "")
cat("Canonical alias-direction conflict rows excluded from direction calls: ",
    nrow(conflicts), "\n", sep = "")
cat("Eligible direct MAST contrasts: ", sum(main_tiles$eligible), " of ",
    nrow(main_tiles), "\n", sep = "")
cat("Tile table: ", tile_output_path, "\n", sep = "")
cat("Gene classifications: ", gene_output_path, "\n", sep = "")
cat("Checks: ", checks_output_path, "\n", sep = "")
