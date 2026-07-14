#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)
started_at <- Sys.time()

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL, mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode", "--mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/15_make_figures.R --config FILE ",
        "[--execution-config FILE] [--task-mode figures | --mode figures]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  selected_mode <- out$task_mode %||% out$mode %||% "figures"
  if (!identical(selected_mode, "figures")) {
    stop("Phase 15 mode must be 'figures'", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  ifelse(grepl("^/", path), path, file.path(root, path))
}

relative_path <- function(path, root) {
  sub(paste0("^", root, "/?"), "", path)
}

as_logical <- function(x) {
  !is.na(x) & toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
}

atomic_write_tsv <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  data.table::fwrite(x, tmp, sep = "\t", quote = FALSE, na = "NA")
  if (!file.rename(tmp, path)) stop("Could not atomically write ", path, call. = FALSE)
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

sha256_lines <- function(values) {
  path <- tempfile("phase15_inputs_", fileext = ".txt")
  on.exit(unlink(path), add = TRUE)
  writeLines(sort(unique(as.character(values))), path, useBytes = TRUE)
  sha256_file(path)
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(gsub("[^0-9.]", "", line[[1L]])) / (1024^2)
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "--verify", "HEAD"),
    stdout = TRUE, stderr = FALSE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    "unborn_or_non_git_repository"
  } else {
    result[[1L]]
  }
}

require_file <- function(path, description) {
  if (!file.exists(path)) stop("Missing ", description, ": ", path, call. = FALSE)
  path
}

require_files <- function(paths, description) {
  if (!length(paths) || any(!file.exists(paths))) {
    stop("Missing ", description, call. = FALSE)
  }
  sort(paths)
}

read_table <- function(path) {
  data.table::fread(path, data.table = FALSE, showProgress = FALSE)
}

read_many <- function(paths) {
  as.data.frame(data.table::rbindlist(
    lapply(paths, data.table::fread, showProgress = FALSE),
    fill = TRUE, use.names = TRUE
  ))
}

require_columns <- function(table, columns, description) {
  missing <- setdiff(columns, names(table))
  if (length(missing)) {
    stop(description, " is missing columns: ", paste(missing, collapse = ", "), call. = FALSE)
  }
}

finite_range <- function(values, default = c(-1, 1), pad = 0.05) {
  values <- values[is.finite(values)]
  if (!length(values)) return(default)
  result <- range(values)
  if (diff(result) == 0) result <- result + c(-1, 1) * max(abs(result[[1L]]) * pad, 0.1)
  result + c(-1, 1) * diff(result) * pad
}

short_text <- function(x, width = 44L) {
  x <- as.character(x)
  ifelse(nchar(x) <= width, x, paste0(substr(x, 1L, width - 3L), "..."))
}

point_figure <- function(effect, labels, title, xlab, colors = "#2C7FB8", low = NULL, high = NULL) {
  keep <- is.finite(effect) & !is.na(labels)
  effect <- effect[keep]
  labels <- labels[keep]
  colors <- rep(colors, length.out = length(keep))[keep]
  if (!is.null(low)) low <- low[keep]
  if (!is.null(high)) high <- high[keep]
  if (!length(effect)) stop("No finite effects available")
  y <- seq_along(effect)
  limits <- finite_range(c(effect, low, high, 0))
  old <- graphics::par(mar = c(5, 18, 4, 2))
  on.exit(graphics::par(old), add = TRUE)
  graphics::plot(
    effect, y, pch = 19, col = colors, yaxt = "n", ylab = "", xlab = xlab,
    main = title, xlim = limits
  )
  if (!is.null(low) && !is.null(high)) {
    valid <- is.finite(low) & is.finite(high)
    graphics::segments(low[valid], y[valid], high[valid], y[valid], col = colors[valid])
    graphics::points(effect, y, pch = 19, col = colors)
  }
  graphics::axis(2, at = y, labels = labels, las = 2, cex.axis = 0.58)
  graphics::abline(v = 0, lty = 2, col = "grey45")
  graphics::box()
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))
if (!requireNamespace("yaml", quietly = TRUE)) stop("Package 'yaml' is required", call. = FALSE)
if (!requireNamespace("data.table", quietly = TRUE)) stop("Package 'data.table' is required", call. = FALSE)

project_root <- normalizePath(getwd(), mustWork = TRUE)
config_path <- absolute_path(args$config, project_root)
invisible(require_file(config_path, "analysis-stage configuration"))
config <- yaml::read_yaml(config_path)
execution_config <- if (!is.null(args$execution_config)) {
  execution_path <- absolute_path(args$execution_config, project_root)
  require_file(execution_path, "execution configuration")
  yaml::read_yaml(execution_path)
} else {
  list(execution = list())
}
execution <- execution_config$execution %||% list()
pilot <- isTRUE(config$scope$pilot)
execution_stage <- as.character(execution$execution_stage %||% if (pilot) {
  "local_pilot"
} else {
  "minerva_production"
})
output_status <- if (pilot) {
  as.character(config$pilot_limits$required_status %||% "nonfinal_smoke_test")
} else {
  "final"
}
output_root <- absolute_path(config$outputs$root, project_root)
analysis_path <- absolute_path(config$project$analysis_config, project_root)
manifest_path <- absolute_path(config$project$manifest, project_root)
invisible(require_file(analysis_path, "scientific configuration"))
invisible(require_file(manifest_path, "RDS manifest"))

figure_dir <- file.path(output_root, "15_figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

validation_status_path <- require_file(
  file.path(output_root, "14_validation", "validation_status.tsv"),
  "Phase 14 validation status"
)
validation_status_table <- read_table(validation_status_path)
if (nrow(validation_status_table) != 1L ||
    !identical(validation_status_table$validation_status[[1L]], "validated_complete")) {
  stop("Phase 14 validation must be validated_complete before Phase 15", call. = FALSE)
}

contrast_candidates <- list.files(
  file.path(output_root, "07_contrasts"), pattern = "contrast_manifest[.]tsv$",
  full.names = TRUE
)
contrast_candidates <- contrast_candidates[
  !grepl("artifacts|checks|status", basename(contrast_candidates))
]
preferred_contrast <- contrast_candidates[
  basename(contrast_candidates) == paste0(execution_stage, "_contrast_manifest.tsv")
]
contrast_path <- if (length(preferred_contrast) == 1L) preferred_contrast else contrast_candidates
if (length(contrast_path) != 1L) {
  stop("Contrast manifest selection must identify exactly one file", call. = FALSE)
}

input_paths <- list(
  validation = validation_status_path,
  cohort = require_file(
    file.path(output_root, "02_cohort", "cohort_exclusion_flow.tsv"), "cohort flow"
  ),
  group_coverage = require_files(list.files(
    file.path(output_root, "06_descriptive"), pattern = "_group_coverage[.]tsv$",
    full.names = TRUE
  ), "group-coverage tables"),
  donor_qc = require_files(list.files(
    file.path(output_root, "04_qc"), pattern = "_donor_celltype_qc[.]tsv$",
    full.names = TRUE
  ), "donor-level mitochondrial QC tables"),
  contrasts = contrast_path,
  gene_results = require_file(
    file.path(output_root, "11_multiple_testing", "gene_multiple_testing.tsv.gz"),
    "multiple-testing gene results"
  ),
  fraction = require_files(list.files(
    file.path(output_root, "09_downstream"), pattern = "[.]mito_fraction_models[.]tsv$",
    full.names = TRUE
  ), "mitochondrial-fraction model tables"),
  pathway = require_file(
    file.path(output_root, "11_multiple_testing", "pathway_multiple_testing.tsv.gz"),
    "multiple-testing pathway results"
  ),
  balance = require_files(list.files(
    file.path(output_root, "09_downstream"), pattern = "[.]mitonuclear_balance[.]tsv$",
    full.names = TRUE
  ), "mitonuclear-balance tables"),
  similarity = require_file(
    file.path(output_root, "11_multiple_testing", "similarity_multiple_testing.tsv.gz"),
    "multiple-testing similarity results"
  ),
  sensitivity = require_file(
    file.path(output_root, "12_sensitivity", "sensitivity_robustness.tsv"),
    "sensitivity robustness results"
  ),
  power = require_file(
    file.path(output_root, "13_power", if (pilot) "power_smoke.tsv" else "power_results.tsv.gz"),
    "power results"
  )
)
flat_input_paths <- unique(unlist(input_paths, use.names = FALSE))
upstream_sha_before <- vapply(flat_input_paths, sha256_file, character(1))

cohort <- read_table(input_paths$cohort)
coverage <- read_many(input_paths$group_coverage)
donor_qc <- read_many(input_paths$donor_qc)
contrasts <- read_table(input_paths$contrasts)
genes <- read_table(input_paths$gene_results)
fraction <- read_many(input_paths$fraction)
pathways <- read_table(input_paths$pathway)
balance <- read_many(input_paths$balance)
similarity <- read_table(input_paths$similarity)
sensitivity <- read_table(input_paths$sensitivity)
power <- read_table(input_paths$power)

require_columns(cohort, c("step", "rule", "donors_remaining"), "Cohort flow")
require_columns(coverage, c(
  "cell_type_high_resolution", "sex", "apoe_group", "diagnosis", "donors"
), "Group coverage")
require_columns(donor_qc, c(
  "projid", "cell_type_high_resolution", "diagnosis", "aggregate_percent_mt"
), "Donor-level QC")
require_columns(contrasts, c(
  "contrast_id", "numerator_donors", "denominator_donors", "eligibility_status"
), "Contrast manifest")
require_columns(genes, c(
  "gene", "method_branch", "cell_type_high_resolution", "contrast_id", "logFC",
  "fdr_bh_within_contrast", "fdr_bh_mtdna_global", "is_mtdna_protein_gene"
), "Gene results")
require_columns(fraction, c(
  "cell_type_high_resolution", "contrast_name", "effect_size", "ci95_low", "ci95_high",
  "fdr_bh_mito_fraction_family", "model_donors"
), "Mitochondrial-fraction results")
require_columns(pathways, c(
  "method_branch", "cell_type_high_resolution", "contrast_id", "contrast_name",
  "pathway", "rank_mean_difference", "rank_fdr_bh_global_branch", "terminal_status"
), "Pathway results")
require_columns(balance, c(
  "projid", "cell_type_high_resolution", "diagnosis", "mitonuclear_log2_per_gene_balance"
), "Mitonuclear balance")
require_columns(similarity, c(
  "gene", "method_branch", "comparison_id", "similarity_score",
  "empirical_fdr_bh_global_method_branch", "paired_tests", "is_mitocarta"
), "Similarity results")
require_columns(sensitivity, c(
  "sensitivity_id", "terminal_status", "result_rows", "repetitions_completed"
), "Sensitivity robustness")
require_columns(power, c(
  "scenario_id", "method_branch", "cell_type_high_resolution", "gene", "effect_log2",
  "power", "false_positive_rate", "donors_ad", "donors_nci", "terminal_status"
), "Power results")

manifest_rows <- list()
render_figure <- function(
    figure_id, title, source_paths, inferential, donor_counts_displayed,
    sample_size_unit, plotter, estimable = TRUE, not_estimable_reason = "") {
  output_path <- file.path(figure_dir, paste0(figure_id, ".pdf"))
  tmp <- paste0(output_path, ".tmp.", Sys.getpid(), ".pdf")
  render_status <- if (estimable) "validated_complete" else "not_estimable"
  message <- if (estimable) "" else not_estimable_reason
  error <- NULL
  tryCatch({
    grDevices::pdf(tmp, width = 14, height = 8.5, onefile = TRUE)
    graphics::par(oma = c(1.5, 1, 2.5, 1))
    if (estimable) {
      plotter()
    } else {
      graphics::plot.new()
      graphics::text(0.5, 0.58, title, cex = 1.3, font = 2)
      graphics::text(0.5, 0.45, paste("Not estimable:", not_estimable_reason), cex = 0.9)
    }
    graphics::mtext(
      paste0("Phase 15 | ", execution_stage, " | ", output_status),
      side = 3, outer = TRUE, line = 0.4, adj = 1, cex = 0.75, col = "#555555"
    )
    grDevices::dev.off()
    if (!file.rename(tmp, output_path)) stop("Could not publish figure")
  }, error = function(e) {
    error <<- conditionMessage(e)
    if (grDevices::dev.cur() > 1L) grDevices::dev.off()
    if (file.exists(tmp)) unlink(tmp)
  })
  if (!is.null(error)) {
    render_status <- "failed"
    message <- error
  }
  manifest_rows[[length(manifest_rows) + 1L]] <<- data.frame(
    schema_version = "figure_manifest_v1",
    execution_stage = execution_stage,
    output_status = output_status,
    figure_id = figure_id,
    title = title,
    path = relative_path(output_path, project_root),
    render_status = render_status,
    message = message,
    source_paths = paste(relative_path(source_paths, project_root), collapse = ";"),
    inferential = inferential,
    donor_counts_displayed = donor_counts_displayed,
    sample_size_unit = sample_size_unit,
    bytes = if (file.exists(output_path)) as.numeric(file.info(output_path)$size) else NA_real_,
    sha256 = sha256_file(output_path),
    stringsAsFactors = FALSE
  )
}

render_figure(
  "01_cohort_flow", "Cohort inclusion flow", input_paths$cohort,
  FALSE, TRUE, "donor", function() {
    labels <- paste0("Step ", cohort$step, ": ", short_text(gsub("_", " ", cohort$rule), 36L))
    old <- graphics::par(mar = c(8, 5, 4, 2))
    on.exit(graphics::par(old), add = TRUE)
    bars <- graphics::barplot(
      cohort$donors_remaining, names.arg = labels, las = 2, col = "#4C78A8",
      ylab = "Donors remaining", main = paste0("Cohort flow [", execution_stage, "]")
    )
    graphics::text(bars, cohort$donors_remaining, labels = cohort$donors_remaining, pos = 3)
  }
)

coverage$group_label <- paste(coverage$diagnosis, coverage$sex, coverage$apoe_group, sep = "\n")
coverage_matrix <- stats::xtabs(donors ~ cell_type_high_resolution + group_label, data = coverage)
render_figure(
  "02_group_coverage", "Sex-APOE-diagnosis donor coverage", input_paths$group_coverage,
  FALSE, TRUE, "donor", function() {
    z <- as.matrix(coverage_matrix)
    old <- graphics::par(mar = c(10, 8, 4, 2))
    on.exit(graphics::par(old), add = TRUE)
    graphics::image(
      seq_len(ncol(z)), seq_len(nrow(z)), t(z), axes = FALSE,
      col = grDevices::colorRampPalette(c("#F7FBFF", "#6BAED6", "#08306B"))(30),
      xlab = "", ylab = "", main = paste0("Donor coverage [", execution_stage, "]")
    )
    graphics::axis(1, at = seq_len(ncol(z)), labels = colnames(z), las = 2, cex.axis = 0.6)
    graphics::axis(2, at = seq_len(nrow(z)), labels = rownames(z), las = 2, cex.axis = 0.7)
    grid <- expand.grid(x = seq_len(ncol(z)), y = seq_len(nrow(z)))
    graphics::text(grid$x, grid$y, labels = as.vector(t(z)), cex = 0.6)
    graphics::box()
  }
)

donor_qc$box_group <- paste(donor_qc$cell_type_high_resolution, donor_qc$diagnosis, sep = "\n")
box_counts <- table(donor_qc$box_group)
box_labels <- paste0(names(box_counts), "\nn=", as.integer(box_counts), " donors")
render_figure(
  "03_mitochondrial_summary", "Donor-level mitochondrial RNA fraction", input_paths$donor_qc,
  FALSE, TRUE, "donor", function() {
    old <- graphics::par(mar = c(10, 5, 4, 2))
    on.exit(graphics::par(old), add = TRUE)
    graphics::boxplot(
      donor_qc$aggregate_percent_mt ~ factor(donor_qc$box_group, levels = names(box_counts)),
      names = box_labels, las = 2, col = "#9ECAE1", outline = FALSE,
      ylab = "Aggregate percent mitochondrial reads",
      main = paste0("Donor-level mitochondrial summary [", execution_stage, "]")
    )
  }
)

fraction <- fraction[is.finite(fraction$effect_size), , drop = FALSE]
fraction_labels <- paste0(
  fraction$cell_type_high_resolution, " | ", short_text(fraction$contrast_name, 30L),
  " | n=", fraction$model_donors, " donors"
)
fraction_colors <- ifelse(
  is.finite(fraction$fdr_bh_mito_fraction_family) & fraction$fdr_bh_mito_fraction_family < 0.05,
  "#D7301F", "#3182BD"
)
render_figure(
  "04_mitochondrial_fraction_effects", "Donor-level mitochondrial-fraction effects",
  input_paths$fraction, TRUE, TRUE, "donor", function() {
    point_figure(
      fraction$effect_size, fraction_labels,
      paste0("Mitochondrial-fraction effects [", execution_stage, "]"),
      "Log odds ratio (95% CI)", fraction_colors, fraction$ci95_low, fraction$ci95_high
    )
  }, nrow(fraction) > 0L, "no estimable mitochondrial-fraction models"
)

donor_index <- match(genes$contrast_id, contrasts$contrast_id)
genes$donor_label <- ifelse(
  is.na(donor_index), "n=not available",
  paste0(
    "n=", contrasts$numerator_donors[donor_index], "/",
    contrasts$denominator_donors[donor_index], " donors"
  )
)
genes$mtdna <- as_logical(genes$is_mtdna_protein_gene)
genes$plot_fdr <- ifelse(
  is.finite(genes$fdr_bh_mtdna_global),
  genes$fdr_bh_mtdna_global, genes$fdr_bh_within_contrast
)
resolved_donor_counts <- !is.na(donor_index) &
  is.finite(contrasts$numerator_donors[donor_index]) &
  is.finite(contrasts$denominator_donors[donor_index])
mtdna <- genes[
  genes$mtdna & is.finite(genes$logFC) & resolved_donor_counts,
  , drop = FALSE
]
mtdna <- mtdna[order(mtdna$plot_fdr, -abs(mtdna$logFC)), , drop = FALSE]
mtdna <- head(mtdna, 40L)
mtdna_labels <- paste0(
  mtdna$method_branch, " | ", mtdna$cell_type_high_resolution, " | ", mtdna$gene,
  " | ", short_text(sub("^[^:]+::[^:]+::", "", mtdna$contrast_id), 20L),
  " | ", mtdna$donor_label
)
mtdna_colors <- ifelse(mtdna$plot_fdr < 0.05, "#D7301F", "#3182BD")
render_figure(
  "05_mtdna_gene_effects", "mtDNA gene effects", input_paths$gene_results,
  TRUE, TRUE, "donor", function() {
    point_figure(
      mtdna$logFC, mtdna_labels, paste0("Top mtDNA effects [", execution_stage, "]"),
      "Log2 fold change", mtdna_colors
    )
  }, nrow(mtdna) > 0L, "no finite mtDNA gene effects"
)

pathway_donor_index <- match(pathways$contrast_id, contrasts$contrast_id)
pathways$donor_label <- ifelse(
  is.na(pathway_donor_index), "n=not available",
  paste0(
    "n=", contrasts$numerator_donors[pathway_donor_index], "/",
    contrasts$denominator_donors[pathway_donor_index], " donors"
  )
)
pathway_plot <- pathways[
  pathways$terminal_status == "validated_complete" & is.finite(pathways$rank_mean_difference) &
    !is.na(pathway_donor_index) &
    is.finite(contrasts$numerator_donors[pathway_donor_index]) &
    is.finite(contrasts$denominator_donors[pathway_donor_index]),
  , drop = FALSE
]
pathway_plot <- pathway_plot[
  order(pathway_plot$rank_fdr_bh_global_branch, -abs(pathway_plot$rank_mean_difference)),
  , drop = FALSE
]
pathway_plot <- head(pathway_plot, 35L)
pathway_labels <- paste0(
  pathway_plot$method_branch, " | ", pathway_plot$cell_type_high_resolution, " | ",
  short_text(pathway_plot$pathway, 35L), " | ", pathway_plot$donor_label
)
pathway_colors <- ifelse(pathway_plot$rank_fdr_bh_global_branch < 0.05, "#D7301F", "#31A354")
render_figure(
  "06_pathway_effects", "MitoCarta pathway effects", input_paths$pathway,
  TRUE, TRUE, "donor", function() {
    point_figure(
      pathway_plot$rank_mean_difference, pathway_labels,
      paste0("Top pathway rank effects [", execution_stage, "]"),
      "Mean rank difference: pathway minus complement", pathway_colors
    )
  }, nrow(pathway_plot) > 0L, "no estimable pathway rank effects"
)

balance$box_group <- paste(balance$cell_type_high_resolution, balance$diagnosis, sep = "\n")
balance_counts <- table(balance$box_group)
balance_labels <- paste0(names(balance_counts), "\nn=", as.integer(balance_counts), " donors")
render_figure(
  "07_mitonuclear_balance", "Donor-level mitonuclear balance", input_paths$balance,
  FALSE, TRUE, "donor", function() {
    old <- graphics::par(mar = c(10, 5, 4, 2))
    on.exit(graphics::par(old), add = TRUE)
    graphics::boxplot(
      balance$mitonuclear_log2_per_gene_balance ~ factor(
        balance$box_group, levels = names(balance_counts)
      ),
      names = balance_labels, las = 2, col = "#A1D99B", outline = FALSE,
      ylab = "Log2 mtDNA:nuclear OXPHOS balance per measured gene",
      main = paste0("Mitonuclear balance [", execution_stage, "]")
    )
  }
)

eligible_contrasts <- contrasts[contrasts$eligibility_status == "eligible", , drop = FALSE]
donor_range <- range(c(
  eligible_contrasts$numerator_donors, eligible_contrasts$denominator_donors
), na.rm = TRUE)
similarity_plot <- similarity[
  as_logical(similarity$is_mitocarta) & is.finite(similarity$similarity_score), , drop = FALSE
]
if (!nrow(similarity_plot)) {
  similarity_plot <- similarity[is.finite(similarity$similarity_score), , drop = FALSE]
}
similarity_plot <- similarity_plot[
  order(similarity_plot$empirical_fdr_bh_global_method_branch, -abs(similarity_plot$similarity_score)),
  , drop = FALSE
]
similarity_plot <- head(similarity_plot, 35L)
similarity_labels <- paste0(
  similarity_plot$method_branch, " | ", similarity_plot$gene, " | ",
  short_text(similarity_plot$comparison_id, 32L), " | paired tests=", similarity_plot$paired_tests
)
similarity_colors <- ifelse(
  similarity_plot$empirical_fdr_bh_global_method_branch < 0.05, "#D7301F", "#756BB1"
)
render_figure(
  "08_similarity", "Zhang-Yu similarity", input_paths$similarity,
  TRUE, TRUE, "donor", function() {
    point_figure(
      similarity_plot$similarity_score, similarity_labels,
      paste0(
        "MitoCarta similarity [", execution_stage, "] | eligible source contrasts: ",
        donor_range[[1L]], "-", donor_range[[2L]], " donors per side"
      ),
      "Similarity score", similarity_colors
    )
  }, nrow(similarity_plot) > 0L, "no finite similarity results"
)

sensitivity$bar_label <- paste0(
  short_text(sensitivity$sensitivity_id, 34L), "\n", sensitivity$terminal_status,
  ifelse(sensitivity$repetitions_completed > 0, paste0("; reps=", sensitivity$repetitions_completed), "")
)
sensitivity_colors <- c(
  validated_complete = "#31A354", not_estimable = "#FDAE6B",
  blocked_missing_input = "#9E9AC8", failed = "#DE2D26"
)
render_figure(
  "09_sensitivity", "Sensitivity and robustness completion", input_paths$sensitivity,
  FALSE, TRUE, "donor_or_result_row", function() {
    old <- graphics::par(mar = c(12, 5, 4, 2))
    on.exit(graphics::par(old), add = TRUE)
    bars <- graphics::barplot(
      sensitivity$result_rows, names.arg = sensitivity$bar_label, las = 2,
      col = unname(sensitivity_colors[sensitivity$terminal_status]),
      ylab = "Result rows", main = paste0("Robustness status [", execution_stage, "]")
    )
    graphics::text(bars, sensitivity$result_rows, labels = sensitivity$result_rows, pos = 3, cex = 0.7)
  }
)

scenario_ids <- sort(unique(power$scenario_id))
power_estimable <- length(scenario_ids) > 0L && any(power$terminal_status == "validated_complete")
render_figure(
  "10_power", "Power by simulated effect", input_paths$power,
  TRUE, TRUE, "simulated_donor", function() {
    rows <- ceiling(length(scenario_ids) / 2)
    old <- graphics::par(mfrow = c(rows, 2), mar = c(4, 4, 4, 1))
    on.exit(graphics::par(old), add = TRUE)
    method_colors <- c(
      pseudobulk_edgeR_known_dispersion = "#1F78B4",
      paper_like_mast_hurdle = "#E31A1C"
    )
    for (scenario in scenario_ids) {
      table <- power[power$scenario_id == scenario, , drop = FALSE]
      observed <- ifelse(table$effect_log2 == 0, table$false_positive_rate, table$power)
      graphics::plot(
        NA, xlim = finite_range(table$effect_log2, c(0, 1)), ylim = c(0, 1),
        xlab = "Simulated log2 effect", ylab = "Power (FPR at effect=0)",
        main = paste0(
          table$cell_type_high_resolution[[1L]], " | ", table$gene[[1L]],
          " | donors ", table$donors_ad[[1L]], "/", table$donors_nci[[1L]]
        )
      )
      for (method in unique(table$method_branch)) {
        selected <- table$method_branch == method
        order_index <- order(table$effect_log2[selected])
        graphics::lines(
          table$effect_log2[selected][order_index], observed[selected][order_index],
          type = "b", pch = 19, col = method_colors[[method]] %||% "grey30"
        )
      }
      graphics::abline(h = unique(table$target_power)[[1L]], lty = 2, col = "grey45")
      graphics::legend(
        "bottomright", legend = unique(table$method_branch),
        col = method_colors[unique(table$method_branch)], lty = 1, pch = 19,
        cex = 0.55, bty = "n"
      )
    }
  }, power_estimable, "no validated power scenarios"
)

figure_manifest <- do.call(rbind, manifest_rows)
planned_ids <- sprintf("%02d_%s", 1:10, c(
  "cohort_flow", "group_coverage", "mitochondrial_summary",
  "mitochondrial_fraction_effects", "mtdna_gene_effects", "pathway_effects",
  "mitonuclear_balance", "similarity", "sensitivity", "power"
))

upstream_sha_after <- vapply(flat_input_paths, sha256_file, character(1))
checks <- data.frame(
  schema_version = "figure_checks_v1",
  check = c(
    "phase14_validation_complete", "all_planned_figures_have_manifest_row",
    "all_figures_terminal", "all_figure_files_exist", "all_figure_files_nonempty",
    "all_figure_checksums_recorded", "inferential_figures_display_donor_counts",
    "no_nucleus_used_as_inferential_sample_size", "execution_labels_match_scope",
    "upstream_artifacts_unchanged"
  ),
  passed = c(
    identical(validation_status_table$validation_status[[1L]], "validated_complete"),
    identical(sort(figure_manifest$figure_id), sort(planned_ids)),
    all(figure_manifest$render_status %in% c("validated_complete", "not_estimable")),
    all(file.exists(absolute_path(figure_manifest$path, project_root))),
    all(is.finite(figure_manifest$bytes) & figure_manifest$bytes > 0),
    all(!is.na(figure_manifest$sha256) & nzchar(figure_manifest$sha256)),
    all(figure_manifest$donor_counts_displayed[figure_manifest$inferential]),
    !any(figure_manifest$sample_size_unit == "nucleus_inferential"),
    all(figure_manifest$execution_stage == execution_stage) &&
      all(figure_manifest$output_status == output_status),
    identical(unname(upstream_sha_before), unname(upstream_sha_after))
  ),
  observed = c(
    validation_status_table$validation_status[[1L]], nrow(figure_manifest),
    paste(sort(unique(figure_manifest$render_status)), collapse = ";"),
    sum(file.exists(absolute_path(figure_manifest$path, project_root))),
    sum(is.finite(figure_manifest$bytes) & figure_manifest$bytes > 0),
    sum(!is.na(figure_manifest$sha256) & nzchar(figure_manifest$sha256)),
    sum(figure_manifest$donor_counts_displayed[figure_manifest$inferential]),
    paste(sort(unique(figure_manifest$sample_size_unit)), collapse = ";"),
    paste(execution_stage, output_status, sep = ";"),
    if (identical(unname(upstream_sha_before), unname(upstream_sha_after))) "unchanged" else "changed"
  ),
  expected = c(
    "validated_complete", length(planned_ids), "validated_complete_or_not_estimable",
    length(planned_ids), length(planned_ids), length(planned_ids),
    sum(figure_manifest$inferential), "donor_or_simulated_donor",
    paste(execution_stage, output_status, sep = ";"), "unchanged"
  ),
  stringsAsFactors = FALSE
)
failed_checks <- checks$check[!checks$passed]
validation_status <- if (length(failed_checks)) "failed" else "validated_complete"

manifest_path_out <- file.path(figure_dir, "figure_manifest.tsv")
checks_path <- file.path(figure_dir, "figure_checks.tsv")
artifacts_path <- file.path(figure_dir, "figure_artifacts.tsv")
status_path <- file.path(figure_dir, "figure_status.tsv")
atomic_write_tsv(figure_manifest, manifest_path_out)
atomic_write_tsv(checks, checks_path)

artifact_files <- c(
  absolute_path(figure_manifest$path, project_root), manifest_path_out, checks_path
)
artifacts <- data.frame(
  schema_version = "figure_artifacts_v1",
  artifact = basename(artifact_files),
  path = relative_path(artifact_files, project_root),
  bytes = as.numeric(file.info(artifact_files)$size),
  sha256 = vapply(artifact_files, sha256_file, character(1)),
  records = c(rep(NA_integer_, nrow(figure_manifest)), nrow(figure_manifest), nrow(checks)),
  validation_status = validation_status,
  stringsAsFactors = FALSE
)
atomic_write_tsv(artifacts, artifacts_path)

status <- data.frame(
  schema_version = "figures_status_v1",
  execution_stage = execution_stage,
  execution_phase = execution$execution_phase %||% NA_integer_,
  backend = execution$backend %||% NA_character_,
  run_id = execution$run_id %||% NA_character_,
  stable_task_id = "global:figures",
  source_rds = paste(sort(unique(coverage$rds_id)), collapse = ";"),
  scientific_script = "scripts/15_make_figures.R",
  scientific_code_bundle_sha256 = sha256_file(file.path(project_root, "scripts/15_make_figures.R")),
  scientific_config_sha256 = sha256_file(analysis_path),
  rds_manifest_sha256 = sha256_file(manifest_path),
  upstream_input_bundle_sha256 = sha256_lines(
    paste(names(upstream_sha_before), upstream_sha_before, sep = "=")
  ),
  output_status = output_status,
  planned_figures = length(planned_ids),
  rendered_figures = sum(figure_manifest$render_status == "validated_complete"),
  not_estimable_figures = sum(figure_manifest$render_status == "not_estimable"),
  failed_figures = sum(figure_manifest$render_status == "failed"),
  inferential_figures = sum(figure_manifest$inferential),
  inferential_figures_with_donor_counts = sum(
    figure_manifest$inferential & figure_manifest$donor_counts_displayed
  ),
  peak_ram_gib = peak_ram_gib(),
  elapsed_seconds = as.numeric(difftime(Sys.time(), started_at, units = "secs")),
  validation_status = validation_status,
  failed_checks = paste(failed_checks, collapse = ";"),
  git_revision = git_revision(project_root),
  timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  stringsAsFactors = FALSE
)
atomic_write_tsv(status, status_path)

cat("Phase 15 figure output: ", figure_dir, "\n", sep = "")
cat("Planned figures: ", status$planned_figures, "\n", sep = "")
cat("Rendered figures: ", status$rendered_figures, "\n", sep = "")
cat("Not estimable figures: ", status$not_estimable_figures, "\n", sep = "")
cat("Failed figures: ", status$failed_figures, "\n", sep = "")
cat("Phase 15 status: ", validation_status, "\n", sep = "")
if (length(failed_checks)) {
  cat("Failed checks: ", paste(failed_checks, collapse = ", "), "\n", sep = "")
  quit(status = 2L)
}
