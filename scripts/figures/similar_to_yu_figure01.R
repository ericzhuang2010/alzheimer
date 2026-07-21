#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_args <- function(args) {
  out <- list(
    output = paste0(
      "results/figures/figure01/",
      "figure01_mitochondrial_yu_analogue.pdf"
    ),
    gene_scope = "all_mito_related"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/figures/similar_to_yu_figure01.R ",
        "[--output PATH] ",
        "[--gene-scope all_mito_related|core_mito]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% c("--output", "--gene-scope") || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    value <- args[[i + 1L]]
    if (identical(key, "--output")) {
      out$output <- value
    } else {
      out$gene_scope <- value
    }
    i <- i + 2L
  }
  if (!out$gene_scope %in% c("all_mito_related", "core_mito")) {
    stop(
      "--gene-scope must be all_mito_related or core_mito",
      call. = FALSE
    )
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
  if (gzip) {
    raw_tmp <- paste0(tmp, ".raw")
    data.table::fwrite(
      x, raw_tmp, sep = "\t", quote = FALSE, na = "NA", compress = "none"
    )
    input <- file(raw_tmp, open = "rb")
    output <- gzfile(tmp, open = "wb")
    repeat {
      chunk <- readBin(input, what = "raw", n = 1024L * 1024L)
      if (!length(chunk)) break
      writeBin(chunk, output)
    }
    close(input)
    close(output)
    unlink(raw_tmp)
  } else {
    data.table::fwrite(
      x, tmp, sep = "\t", quote = FALSE, na = "NA", compress = "none"
    )
  }
  if (!file.rename(tmp, path)) stop("Could not publish ", path, call. = FALSE)
}

sha256_file <- function(path) {
  digest::digest(file = path, algo = "sha256")
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
for (package in c("data.table", "digest")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package '", package, "' is required", call. = FALSE)
  }
}

project_root <- normalizePath(getwd(), mustWork = TRUE)
output_path <- absolute_path(args$output, project_root)
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)

phase09_dir <- file.path(
  project_root, "results", "minerva_production", "09_annotate_genes"
)
phase09_paths <- c(
  status = file.path(phase09_dir, "annotation_status.tsv"),
  checks = file.path(phase09_dir, "annotation_checks.tsv"),
  artifacts = file.path(phase09_dir, "annotation_artifacts.tsv"),
  annotated = file.path(phase09_dir, "deg_all_annotated.tsv.gz")
)
manifest_path <- file.path(project_root, "config", "minerva_rds_manifest.tsv")

if (!all(file.exists(phase09_paths)) || !file.exists(manifest_path)) {
  stop("Required Phase 09 annotation input or RDS manifest is missing", call. = FALSE)
}

message("Validating Phase 09 annotation bundle")
annotation_status <- data.table::fread(phase09_paths[["status"]])
annotation_checks <- data.table::fread(phase09_paths[["checks"]])
annotation_artifacts <- data.table::fread(phase09_paths[["artifacts"]])
if (
  nrow(annotation_status) != 1L ||
    annotation_status$schema_version[[1L]] != "mitochondrial_annotation_status_v1" ||
    annotation_status$validation_status[[1L]] != "validated_complete"
) {
  stop("Phase 09 annotation status is not validated_complete", call. = FALSE)
}
if (
  !nrow(annotation_checks) ||
    !all(as_logical(annotation_checks$passed))
) {
  stop("At least one Phase 09 annotation check failed", call. = FALSE)
}
if (
  !nrow(annotation_artifacts) ||
    !all(annotation_artifacts$validation_status == "validated_complete")
) {
  stop("Phase 09 artifact manifest is not validated_complete", call. = FALSE)
}
annotated_artifact <- annotation_artifacts[
  artifact == "deg_all_annotated.tsv.gz"
]
if (nrow(annotated_artifact) != 1L) {
  stop("Phase 09 artifact manifest lacks one annotated DEG table", call. = FALSE)
}
annotated_size_before <- as.numeric(
  file.info(phase09_paths[["annotated"]])$size
)
annotated_sha256_before <- sha256_file(phase09_paths[["annotated"]])
annotated_artifact_valid <- (
  annotated_size_before ==
    as.numeric(annotated_artifact$bytes[[1L]])
) && (
  annotated_sha256_before ==
    annotated_artifact$sha256[[1L]]
)
if (!annotated_artifact_valid) {
  stop("Phase 09 annotated DEG artifact fails size or SHA-256 validation", call. = FALSE)
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

phase09_columns <- c(
  "schema_version", "rds_id", "contrast_id", "cell_type_high_resolution",
  "sex", "apoe_group", "contrast_family", "contrast_name",
  "terminal_status", "contrast_donors_ad", "contrast_donors_nci",
  "contrast_status_message", "feature_id_original", "reference_only_id",
  "reference_only", "symbol_hgnc_current", "hgnc_id",
  "ensembl_id_stable", "mapping_status", "mito_tier", "genome_origin",
  "tested_status", "deg_state", "phase08_row_present", "logFC", "pct_ad",
  "pct_nci", "fdr_bh_within_contrast", "paper_effect_threshold_log2",
  "paper_deg"
)
message("Reading validated Phase 09 annotated DEG rows")
annotated <- data.table::fread(
  phase09_paths[["annotated"]],
  select = phase09_columns,
  showProgress = FALSE
)
if (
  !nrow(annotated) ||
    !all(annotated$schema_version == "annotated_yu_mast_results_v1")
) {
  stop("Unexpected or empty Phase 09 annotated DEG schema", call. = FALSE)
}
annotated[, `:=`(
  reference_only = as_logical(reference_only),
  phase08_row_present = as_logical(phase08_row_present),
  paper_deg = as_logical(paper_deg)
)]
direct <- annotated[
  contrast_family == "AD_vs_NCI" &
    grepl("^AD_vs_NCI__(Female|Male)__(e2|e33|e4)$", contrast_name)
]
direct[, group_id := paste(sex, apoe_group, sep = "__")]

direct_status <- unique(direct[, .(
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  sex, apoe_group, group_id, terminal_status,
  donors_ad = contrast_donors_ad,
  donors_nci = contrast_donors_nci,
  status_message = contrast_status_message
)])
direct_status[, eligible := terminal_status == "validated_complete"]
if (any(direct_status$terminal_status == "failed")) {
  stop("At least one paper-matched Phase 09 contrast failed", call. = FALSE)
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
  stop("Direct Phase 09 status keys or group definitions are invalid", call. = FALSE)
}

returned <- direct[phase08_row_present == TRUE]
paper_rule <- is.finite(returned$fdr_bh_within_contrast) &
  returned$fdr_bh_within_contrast < 0.05 &
  is.finite(returned$logFC) &
  abs(returned$logFC) > returned$paper_effect_threshold_log2 &
  (returned$pct_ad >= 0.10 | returned$pct_nci >= 0.10)
if (!identical(as.logical(returned$paper_deg), as.logical(paper_rule))) {
  mismatch <- sum(returned$paper_deg != paper_rule, na.rm = TRUE)
  stop("Phase 09 paper_deg validation failed for ", mismatch, " rows", call. = FALSE)
}

allowed_tiers <- c("core_mito_protein", "mtdna_noncoding", "mito_extended")
scope_tiers <- if (args$gene_scope == "core_mito") {
  "core_mito_protein"
} else {
  allowed_tiers
}
scope_label <- if (args$gene_scope == "core_mito") {
  "core mitochondrial"
} else {
  "mitochondrial-related"
}
mito <- direct[mito_tier %in% scope_tiers]
if (!nrow(mito)) stop("No Phase 09 rows belong to the selected scope", call. = FALSE)

tested_statuses <- c(
  "tested_not_significant", "significant_up", "significant_down"
)
state_mapping_ok <- (
  mito$tested_status == "significant_up" & mito$deg_state == 1L
) | (
  mito$tested_status == "significant_down" & mito$deg_state == -1L
) | (
  mito$tested_status == "tested_not_significant" & mito$deg_state == 0L
) | (
  !mito$tested_status %in% tested_statuses & is.na(mito$deg_state)
)
if (!all(state_mapping_ok)) {
  stop("Phase 09 tested_status-to-state mapping is invalid", call. = FALSE)
}

tested <- mito[
  tested_status %in% tested_statuses & phase08_row_present == TRUE &
    reference_only == FALSE
]
if (!nrow(tested)) stop("No tested genes remain in the selected scope", call. = FALSE)
tested[, feature_state := as.integer(deg_state)]
tested_key <- paste(tested$rds_id, tested$contrast_id, tested$feature_id_original, sep = "\r")
if (anyDuplicated(tested_key)) {
  stop("Phase 09 tested assay-feature keys are not unique", call. = FALSE)
}

# Phase 09 defines the exact assayed feature as the analysis identity.
# Stable HGNC and Ensembl annotations are retained, but many-to-one mappings
# are not silently collapsed to one canonical symbol.
direct_summary <- tested[, .(
  tested_mito_features = .N,
  tested_core_mito = sum(mito_tier == "core_mito_protein"),
  tested_mtdna_noncoding = sum(mito_tier == "mtdna_noncoding"),
  tested_mito_extended = sum(mito_tier == "mito_extended"),
  up_degs = sum(feature_state == 1L),
  down_degs = sum(feature_state == -1L),
  unchanged = sum(feature_state == 0L),
  up_core_mito = sum(feature_state == 1L & mito_tier == "core_mito_protein"),
  down_core_mito = sum(feature_state == -1L & mito_tier == "core_mito_protein"),
  up_mtdna_noncoding = sum(feature_state == 1L & mito_tier == "mtdna_noncoding"),
  down_mtdna_noncoding = sum(feature_state == -1L & mito_tier == "mtdna_noncoding"),
  up_mito_extended = sum(feature_state == 1L & mito_tier == "mito_extended"),
  down_mito_extended = sum(feature_state == -1L & mito_tier == "mito_extended")
), by = .(
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  sex, apoe_group, group_id
)]

main_tiles <- merge(
  direct_status[, .(
    rds_id, cell_type_high_resolution, contrast_id, contrast_name,
    sex, apoe_group, group_id, eligible, terminal_status,
    donors_ad, donors_nci, status_message
  )],
  direct_summary,
  by = c(
    "rds_id", "cell_type_high_resolution", "contrast_id", "contrast_name",
    "sex", "apoe_group", "group_id"
  ),
  all.x = TRUE, sort = FALSE
)
if (any(main_tiles$eligible & is.na(main_tiles$tested_mito_features))) {
  stop("At least one eligible contrast has no tested mitochondrial genes", call. = FALSE)
}
if (any(
  main_tiles$eligible &
    main_tiles$up_degs + main_tiles$down_degs + main_tiles$unchanged !=
      main_tiles$tested_mito_features
)) {
  stop("Direct mitochondrial state counts do not sum to tested denominators", call. = FALSE)
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
        first <- tested[
          cell_type_high_resolution == cell_type & group_id == first_group,
          .(
            feature_id_original, symbol_hgnc_current, hgnc_id,
            ensembl_id_stable, mapping_status, mito_tier, genome_origin,
            first_tested_status = tested_status,
            first_state = feature_state, first_logFC = logFC,
            first_fdr_bh_within_contrast = fdr_bh_within_contrast,
            first_paper_deg = paper_deg
          )
        ]
        second <- tested[
          cell_type_high_resolution == cell_type & group_id == second_group,
          .(
            feature_id_original, second_mito_tier = mito_tier,
            second_tested_status = tested_status,
            second_state = feature_state, second_logFC = logFC,
            second_fdr_bh_within_contrast = fdr_bh_within_contrast,
            second_paper_deg = paper_deg
          )
        ]
        paired <- merge(first, second, by = "feature_id_original", all = FALSE)
        if (!nrow(paired)) {
          stop(
            "No jointly tested mitochondrial features for ",
            pair_id, " / ", cell_type
          )
        }
        if (any(paired$mito_tier != paired$second_mito_tier)) {
          stop("Mitochondrial tier changed between paired contrasts")
        }
        paired[, category := data.table::fcase(
          first_state != 0L & second_state != 0L & first_state == second_state,
          "same_direction",
          first_state != 0L & second_state == 0L, "first_only",
          first_state == 0L & second_state != 0L, "second_only",
          first_state != 0L & second_state != 0L & first_state == -second_state,
          "opposite_direction",
          default = "neither"
        )]
        jointly_tested <- nrow(paired)
        denominator <- jointly_tested
        jointly_tested_core_mito <- sum(
          paired$mito_tier == "core_mito_protein"
        )
        jointly_tested_mtdna_noncoding <- sum(
          paired$mito_tier == "mtdna_noncoding"
        )
        jointly_tested_mito_extended <- sum(
          paired$mito_tier == "mito_extended"
        )
        if (denominator <= 0L) {
          stop("No jointly tested mitochondrial features for ", pair_id,
               " / ", cell_type)
        }
        counts <- table(factor(
          paired$category,
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
          rds_id = first_status$rds_id[[1L]],
          cell_type_high_resolution = cell_type,
          first_group = first_group,
          second_group = second_group,
          jointly_tested_mito_features = jointly_tested,
          jointly_tested_core_mito = sum(mito_tier == "core_mito_protein"),
          jointly_tested_mtdna_noncoding = sum(mito_tier == "mtdna_noncoding"),
          jointly_tested_mito_extended = sum(mito_tier == "mito_extended")
        )]
        paired[, second_mito_tier := NULL]
        gene_rows[[length(gene_rows) + 1L]] <- paired
      } else {
        denominator <- NA_integer_
        jointly_tested <- NA_integer_
        jointly_tested_core_mito <- NA_integer_
        jointly_tested_mtdna_noncoding <- NA_integer_
        jointly_tested_mito_extended <- NA_integer_
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
          tested_mito_features = denominator,
          jointly_tested_mito_features = jointly_tested,
          jointly_tested_core_mito = jointly_tested_core_mito,
          jointly_tested_mtdna_noncoding = jointly_tested_mtdna_noncoding,
          jointly_tested_mito_extended = jointly_tested_mito_extended,
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

message("Building pairwise mitochondrial DEG classifications")
female_panel <- build_pair_panel("C", female_definitions)
male_panel <- build_pair_panel("D", male_definitions)
sex_panel <- build_pair_panel("E", sex_definitions)
pair_tiles <- data.table::rbindlist(list(
  female_panel$tiles, male_panel$tiles, sex_panel$tiles
), use.names = TRUE)
pair_genes <- data.table::rbindlist(list(
  female_panel$genes, male_panel$genes, sex_panel$genes
), use.names = TRUE, fill = TRUE)

if (any(pair_tiles$eligible & !is.finite(pair_tiles$tested_mito_features))) {
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

panel_legend_items <- list(
  A = c("Upregulated DEG count" = "#CB181D"),
  B = c("Downregulated DEG count" = "#2171B5"),
  C = c(
    "Same direction" = category_colors[["same_direction"]],
    "First group only" = category_colors[["first_only"]],
    "Second group only" = category_colors[["second_only"]],
    "Opposite directions" = category_colors[["opposite_direction"]]
  ),
  D = c(
    "Same direction" = category_colors[["same_direction"]],
    "First group only" = category_colors[["first_only"]],
    "Second group only" = category_colors[["second_only"]],
    "Opposite directions" = category_colors[["opposite_direction"]]
  ),
  E = c(
    "Same direction" = category_colors[["same_direction"]],
    "First group only" = category_colors[["first_only"]],
    "Second group only" = category_colors[["second_only"]],
    "Opposite directions" = category_colors[["opposite_direction"]]
  )
)

draw_color_legend <- function(
    nc, nr, item_colors, max_count, pairwise = FALSE) {
  if (!length(item_colors) || is.null(names(item_colors))) {
    stop("A named color vector is required for each panel legend")
  }
  shade_steps <- seq(0, 1, length.out = 5L)
  x_start <- nc + 1.1
  swatch_width <- 0.72
  swatch_gap <- 0.08
  legend_y <- nr + 0.25
  item_gap <- if (length(item_colors) > 1L) 2.05 else 1.80

  graphics::text(
    x_start, legend_y, labels = "Color legend",
    adj = c(0, 0.5), cex = 0.62, font = 2
  )
  legend_y <- legend_y - 0.72
  for (item_label in names(item_colors)) {
    base_color <- unname(item_colors[[item_label]])
    graphics::text(
      x_start, legend_y, labels = item_label,
      adj = c(0, 0.5), cex = 0.50, font = 2
    )
    bar_top <- legend_y - 0.30
    bar_bottom <- legend_y - 0.68
    for (shade_index in seq_along(shade_steps)) {
      left <- x_start + (shade_index - 1L) * (swatch_width + swatch_gap)
      graphics::rect(
        left, bar_bottom, left + swatch_width, bar_top,
        col = shade_color(base_color, shade_steps[[shade_index]]),
        border = "#8A8A8A", lwd = 0.45
      )
    }
    bar_end <- x_start + length(shade_steps) * swatch_width +
      (length(shade_steps) - 1L) * swatch_gap
    graphics::text(
      x_start, bar_bottom - 0.12, labels = "0",
      adj = c(0, 1), cex = 0.44
    )
    graphics::text(
      bar_end, bar_bottom - 0.12, labels = as.character(max_count),
      adj = c(1, 1), cex = 0.44
    )
    legend_y <- legend_y - item_gap
  }

  graphics::rect(
    x_start, legend_y - 0.03, x_start + 0.56, legend_y + 0.35,
    col = "#D9D9D9", border = "#8A8A8A", lwd = 0.45
  )
  graphics::text(
    x_start + 0.72, legend_y + 0.16,
    labels = "NE = contrast not estimable",
    adj = c(0, 0.5), cex = 0.47
  )
  legend_y <- legend_y - 0.72
  graphics::text(
    x_start, legend_y,
    labels = "White to full color = increasing count",
    adj = c(0, 1), cex = 0.45
  )
  if (pairwise) {
    graphics::text(
      x_start, legend_y - 0.56,
      labels = "First/second group follows each row label",
      adj = c(0, 1), cex = 0.45
    )
  }
}

draw_heatmap <- function(
    tile_table, row_order, row_labels, row_colors,
    title, panel_label, subtitle, show_x_labels = TRUE,
    label_cex = 0.27, legend_items, pairwise_legend = FALSE) {
  nr <- length(row_order)
  nc <- length(cell_order)
  if (show_x_labels) {
    graphics::par(mar = c(10.2, 15.5, 4.2, 13.0), xpd = NA)
  } else {
    graphics::par(mar = c(1.2, 15.5, 4.2, 13.0), xpd = NA)
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
          tile$count[[1L]], "/", tile$tested_mito_features[[1L]], "\n",
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
    las = 1, tick = FALSE, cex.axis = 0.78, line = -0.3
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
      srt = 90, adj = c(1, 0.5), cex = 0.56
    )
  }

  group_runs <- rle(unname(cell_rds[cell_order]))
  ends <- cumsum(group_runs$lengths)
  starts <- c(1L, head(ends, -1L) + 1L)
  for (i in seq_along(group_runs$values)) {
    rds_id <- group_runs$values[[i]]
    group_label_y <- nr + 1.13 + ifelse(rds_id == "opcs", 0.20, 0)
    graphics::rect(
      starts[[i]] - 0.5, nr + 0.68, ends[[i]] + 0.5, nr + 0.92,
      col = rds_colors[[rds_id]], border = "white", lwd = 0.5
    )
    graphics::text(
      mean(c(starts[[i]], ends[[i]])), group_label_y,
      labels = rds_display[[rds_id]], cex = 0.70, font = 2
    )
    if (i < length(group_runs$values)) {
      boundary <- ends[[i]] + 0.5
      graphics::segments(
        boundary, 0.5, boundary, nr + 0.92,
        col = "#555555", lwd = 0.8, xpd = FALSE
      )
    }
  }

  graphics::box(lwd = 0.8)
  graphics::mtext(
    paste0(panel_label, ". ", title), side = 3, line = 2.4,
    adj = 0, font = 2, cex = 0.92
  )
  graphics::mtext(subtitle, side = 3, line = 1.15, adj = 0, cex = 0.60)
  draw_color_legend(
    nc = nc, nr = nr, item_colors = legend_items,
    max_count = max_count, pairwise = pairwise_legend
  )
}

make_main_plot_table <- function(direction) {
  if (!direction %in% c("up", "down")) stop("Invalid direction")
  value_column <- if (direction == "up") "up_degs" else "down_degs"
  table <- data.table::copy(main_tiles)
  table[, `:=`(
    row_id = group_id,
    count = get(value_column)
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
  eligible, 100 * count / tested_mito_features, NA_real_
)]
pair_tile_output <- data.table::copy(pair_tiles)
pair_tile_output[, percent := ifelse(
  eligible, 100 * count / tested_mito_features, NA_real_
)]
tile_output <- data.table::rbindlist(list(
  main_tile_output,
  pair_tile_output
), use.names = TRUE, fill = TRUE)
tile_output[, `:=`(
  schema_version = "mito_related_mast_yu_tiles_v2",
  method_branch = "mast",
  deg_rule = "phase08_paper_deg",
  annotation_source = "validated_phase09_mitochondrial_tiers",
  phase09_annotated_sha256 = annotated_sha256_before,
  analysis_universe = args$gene_scope,
  included_mito_tiers = paste(scope_tiers, collapse = ";")
)]
data.table::setcolorder(tile_output, c(
  "schema_version", "analysis_universe", "included_mito_tiers",
  "panel", "method_branch", "category",
  "rds_id", "cell_type_high_resolution", "row_id", "row_label",
  "eligible", "count", "tested_mito_features", "percent", "donor_label"
))
atomic_write_tsv(tile_output, tile_output_path)

direct_gene_output <- tested[, .(
  schema_version = "mito_related_mast_yu_genes_v2",
  phase09_annotated_sha256 = annotated_sha256_before,
  analysis_universe = args$gene_scope,
  included_mito_tiers = paste(scope_tiers, collapse = ";"),
  record_type = "direct_state",
  panel = "A_B",
  rds_id, cell_type_high_resolution, contrast_id, contrast_name,
  group_id, feature_id_original, symbol_hgnc_current, hgnc_id,
  ensembl_id_stable, mapping_status, mito_tier, genome_origin,
  tested_status, feature_state, paper_deg, logFC, fdr_bh_within_contrast,
  first_group = NA_character_, second_group = NA_character_,
  first_tested_status = NA_character_, second_tested_status = NA_character_,
  pair_id = NA_character_, first_state = NA_integer_,
  second_state = NA_integer_, category = NA_character_,
  first_logFC = NA_real_, second_logFC = NA_real_,
  first_fdr_bh_within_contrast = NA_real_,
  second_fdr_bh_within_contrast = NA_real_,
  first_paper_deg = NA, second_paper_deg = NA,
  jointly_tested_mito_features = NA_integer_,
  jointly_tested_core_mito = NA_integer_,
  jointly_tested_mtdna_noncoding = NA_integer_,
  jointly_tested_mito_extended = NA_integer_
)]
pair_gene_output <- pair_genes[, .(
  schema_version = "mito_related_mast_yu_genes_v2",
  phase09_annotated_sha256 = annotated_sha256_before,
  analysis_universe = args$gene_scope,
  included_mito_tiers = paste(scope_tiers, collapse = ";"),
  record_type, panel,
  rds_id, cell_type_high_resolution,
  contrast_id = NA_character_, contrast_name = NA_character_,
  group_id = NA_character_, feature_id_original, symbol_hgnc_current,
  hgnc_id, ensembl_id_stable, mapping_status, mito_tier, genome_origin,
  tested_status = NA_character_, feature_state = NA_integer_,
  paper_deg = NA, logFC = NA_real_, fdr_bh_within_contrast = NA_real_,
  first_group, second_group, first_tested_status, second_tested_status,
  pair_id, first_state, second_state, category,
  first_logFC, second_logFC, first_fdr_bh_within_contrast,
  second_fdr_bh_within_contrast, first_paper_deg, second_paper_deg,
  jointly_tested_mito_features, jointly_tested_core_mito,
  jointly_tested_mtdna_noncoding, jointly_tested_mito_extended
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
    paste0("Number of ", scope_label, " genes upregulated in AD"), "A",
    paste0(
      "Validated Phase 09 tiers; Phase 08 MAST paper_deg; ",
      "line 1 = DEGs/tested assay features; line 2 = AD/NCI donors"
    ),
    show_x_labels = FALSE, label_cex = 0.29,
    legend_items = panel_legend_items[["A"]]
  )
  draw_heatmap(
    make_main_plot_table("down"), group_order, main_row_labels, down_row_colors,
    paste0("Number of ", scope_label, " genes downregulated in AD"), "B",
    paste0(
      "Validated Phase 09 tiers; Phase 08 MAST paper_deg; ",
      "line 1 = DEGs/tested assay features; line 2 = AD/NCI donors"
    ),
    show_x_labels = TRUE, label_cex = 0.29,
    legend_items = panel_legend_items[["B"]]
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    female_panel$tiles, pair_row_orders[["C"]], pair_row_labels[["C"]],
    pair_row_colors[["C"]],
    "APOE comparisons within females", "C",
    paste0(
      "Jointly tested Phase 09 assay features in ", args$gene_scope,
      "; line 2 = first AD/NCI donors | second AD/NCI donors"
    ),
    show_x_labels = TRUE, label_cex = 0.245,
    legend_items = panel_legend_items[["C"]], pairwise_legend = TRUE
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    male_panel$tiles, pair_row_orders[["D"]], pair_row_labels[["D"]],
    pair_row_colors[["D"]],
    "APOE comparisons within males", "D",
    paste0(
      "Jointly tested Phase 09 assay features in ", args$gene_scope,
      "; line 2 = first AD/NCI donors | second AD/NCI donors"
    ),
    show_x_labels = TRUE, label_cex = 0.245,
    legend_items = panel_legend_items[["D"]], pairwise_legend = TRUE
  )

  graphics::layout(matrix(1L))
  draw_heatmap(
    sex_panel$tiles, pair_row_orders[["E"]], pair_row_labels[["E"]],
    pair_row_colors[["E"]],
    "Sex-based comparisons within APOE groups", "E",
    paste0(
      "Jointly tested Phase 09 assay features in ", args$gene_scope,
      "; line 2 = female AD/NCI donors | male AD/NCI donors"
    ),
    show_x_labels = TRUE, label_cex = 0.245,
    legend_items = panel_legend_items[["E"]], pairwise_legend = TRUE
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

phase09_input_unchanged <- (
  as.numeric(file.info(phase09_paths[["annotated"]])$size) ==
    annotated_size_before
) && (
  sha256_file(phase09_paths[["annotated"]]) == annotated_sha256_before
)

checks <- data.table::data.table(
  schema_version = "mito_related_mast_yu_checks_v2",
  check = c(
    "phase09_status_validated",
    "phase09_checks_pass",
    "phase09_annotated_artifact_valid",
    "phase09_annotated_input_unchanged",
    "direct_status_grid_54_by_6",
    "no_failed_direct_contrasts",
    "phase08_paper_deg_rule_reproduced",
    "selected_mito_tiers_exact",
    "tested_feature_keys_unique",
    "direct_states_partition_tested_genes",
    "direct_tier_denominators_sum",
    "pairwise_intersections_have_denominators",
    "pairwise_tier_denominators_sum",
    "all_panels_present",
    "pdf_exists_nonempty",
    "companion_tables_exist_nonempty"
  ),
  passed = c(
    nrow(annotation_status) == 1L &&
      annotation_status$validation_status[[1L]] == "validated_complete",
    nrow(annotation_checks) > 0L && all(as_logical(annotation_checks$passed)),
    annotated_artifact_valid,
    phase09_input_unchanged,
    nrow(direct_status) == 54L * 6L,
    !any(direct_status$terminal_status == "failed"),
    identical(as.logical(returned$paper_deg), as.logical(paper_rule)),
    setequal(unique(mito$mito_tier), scope_tiers),
    !anyDuplicated(tested_key),
    all(
      main_tiles$up_degs[main_tiles$eligible] +
        main_tiles$down_degs[main_tiles$eligible] +
        main_tiles$unchanged[main_tiles$eligible] ==
        main_tiles$tested_mito_features[main_tiles$eligible]
    ),
    all(
      main_tiles$tested_core_mito[main_tiles$eligible] +
        main_tiles$tested_mtdna_noncoding[main_tiles$eligible] +
        main_tiles$tested_mito_extended[main_tiles$eligible] ==
        main_tiles$tested_mito_features[main_tiles$eligible]
    ),
    all(is.finite(pair_tiles$tested_mito_features[pair_tiles$eligible])),
    all(
      pair_tiles$jointly_tested_core_mito[pair_tiles$eligible] +
        pair_tiles$jointly_tested_mtdna_noncoding[pair_tiles$eligible] +
        pair_tiles$jointly_tested_mito_extended[pair_tiles$eligible] ==
        pair_tiles$jointly_tested_mito_features[pair_tiles$eligible]
    ),
    identical(sort(unique(tile_output$panel)), c("A", "B", "C", "D", "E")),
    file.exists(output_path) && file.info(output_path)$size > 0,
    file.exists(tile_output_path) && file.info(tile_output_path)$size > 0 &&
      file.exists(gene_output_path) && file.info(gene_output_path)$size > 0
  ),
  observed = c(
    annotation_status$validation_status[[1L]],
    sum(as_logical(annotation_checks$passed)),
    annotated_artifact_valid,
    phase09_input_unchanged,
    nrow(direct_status),
    sum(direct_status$terminal_status == "failed"),
    sum(returned$paper_deg != paper_rule, na.rm = TRUE),
    paste(sort(unique(mito$mito_tier)), collapse = ";"),
    anyDuplicated(tested_key),
    sum(main_tiles$eligible),
    sum(main_tiles$eligible),
    sum(pair_tiles$eligible),
    sum(pair_tiles$eligible),
    paste(sort(unique(tile_output$panel)), collapse = ";"),
    if (file.exists(output_path)) file.info(output_path)$size else 0,
    sum(file.exists(c(tile_output_path, gene_output_path)))
  ),
  expected = c(
    "validated_complete",
    "all Phase 09 checks pass",
    "TRUE",
    "TRUE",
    "324",
    "0",
    "0 mismatches",
    paste(scope_tiers, collapse = ";"),
    "0 duplicate keys",
    "all eligible direct contrasts partitioned",
    "all eligible direct tier totals",
    "all eligible pairwise tiles",
    "all eligible pairwise tier totals",
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
cat("Analysis universe: ", args$gene_scope, "\n", sep = "")
cat("Included mitochondrial tiers: ", paste(scope_tiers, collapse = ";"), "\n", sep = "")
cat("Unique tested assay features represented: ",
    data.table::uniqueN(tested$feature_id_original), "\n", sep = "")
cat("Eligible direct MAST contrasts: ", sum(main_tiles$eligible), " of ",
    nrow(main_tiles), "\n", sep = "")
cat("Tile table: ", tile_output_path, "\n", sep = "")
cat("Gene classifications: ", gene_output_path, "\n", sep = "")
cat("Checks: ", checks_output_path, "\n", sep = "")
