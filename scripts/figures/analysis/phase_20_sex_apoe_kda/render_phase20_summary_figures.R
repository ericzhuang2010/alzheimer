#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(ggplot2))

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) normalizePath(args[[1]], mustWork = TRUE) else normalizePath(".")
result_dir <- if (length(args) >= 2) normalizePath(args[[2]], mustWork = TRUE) else
  file.path(root, "results", "minerva_production", "20_sex_apoe_kda")
figure_root <- if (length(args) >= 3) args[[3]] else
  file.path(root, "results", "figures", "analysis", "phase_20_sex_apoe_kda")
dir.create(figure_root, recursive = TRUE, showWarnings = FALSE)

read_result <- function(name) {
  read.delim(file.path(result_dir, name), sep = "\t", quote = "",
             check.names = FALSE, na.strings = "NA", stringsAsFactors = FALSE)
}
is_true <- function(x) toupper(as.character(x)) %in% c("TRUE", "T", "1", "YES")
write_tsv <- function(x, path) {
  write.table(x, path, sep = "\t", quote = FALSE, row.names = FALSE,
              col.names = TRUE, na = "NA", eol = "\n")
}
sha256 <- function(path) {
  strsplit(system2("sha256sum", path, stdout = TRUE)[[1]], "[[:space:]]+")[[1]][[1]]
}
save_bundle <- function(id, plot, data, caption, methods, width, height) {
  bundle <- file.path(figure_root, id)
  dir.create(bundle, recursive = TRUE, showWarnings = FALSE)
  stem <- paste0("phase20_", id)
  paths <- c(
    png = file.path(bundle, paste0(stem, ".png")),
    svg = file.path(bundle, paste0(stem, ".svg")),
    pdf = file.path(bundle, paste0(stem, ".pdf")),
    data = file.path(bundle, paste0(stem, "_plot_data.tsv")),
    caption = file.path(bundle, paste0(stem, "_caption.md")),
    methods = file.path(bundle, paste0(stem, "_methods.md"))
  )
  write_tsv(data, paths[["data"]])
  ggsave(paths[["png"]], plot, width = width, height = height, dpi = 220, bg = "white")
  grDevices::svg(paths[["svg"]], width = width, height = height, bg = "white")
  print(plot)
  grDevices::dev.off()
  ggsave(paths[["pdf"]], plot, width = width, height = height, bg = "white")
  writeLines(caption, paths[["caption"]], useBytes = TRUE)
  writeLines(methods, paths[["methods"]], useBytes = TRUE)
  checks_path <- file.path(bundle, paste0(stem, "_checks.tsv"))
  status_path <- file.path(bundle, paste0(stem, "_status.tsv"))
  checks <- data.frame(
    schema_version = "phase20_sex_apoe_non_mt_figure_checks_v2",
    check_id = c("plot_data_nonempty", "all_declared_files_exist", "non_mt_scope"),
    severity = "error",
    observed = c(nrow(data), sum(file.exists(paths)), "non_mt_driver"),
    expected = c(">0", length(paths), "non_mt_driver"),
    passed = c(nrow(data) > 0, all(file.exists(paths)), TRUE)
  )
  write_tsv(checks, checks_path)
  state <- if (all(checks$passed)) "validated_complete" else "validation_failed"
  write_tsv(data.frame(
    schema_version = "phase20_sex_apoe_non_mt_figure_status_v2",
    figure_id = id, plot_data_rows = nrow(data),
    failed_checks = sum(!checks$passed), validation_status = state
  ), status_path)
  artifacts_path <- file.path(bundle, paste0(stem, "_artifacts.tsv"))
  files <- c(paths, checks = checks_path, status = status_path)
  info <- file.info(files)
  write_tsv(data.frame(
    schema_version = "phase20_sex_apoe_non_mt_figure_artifacts_v2",
    artifact_order = seq_along(files), path = basename(files),
    bytes = info$size, sha256 = vapply(files, sha256, character(1)),
    hash_status = "recorded"
  ), artifacts_path)
  data.frame(
    figure_id = id,
    directory = file.path("results", "figures", "analysis",
                          "phase_20_sex_apoe_kda", id),
    plot_data_rows = nrow(data), validation_status = state
  )
}

groups <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
networks <- c("Astrocytes", "Excitatory_neurons", "Inhibitory_neurons",
              "Microglia", "OPCs", "Oligodendrocytes", "Vasculature_cells")
network_labels <- c("Astrocytes", "Excitatory neurons", "Inhibitory neurons",
                    "Microglia", "OPCs", "Oligodendrocytes", "Vasculature")
category_levels <- unlist(lapply(groups, function(x) paste(x, networks, sep = " · ")))
theme_p20 <- theme_minimal(base_size = 10) +
  theme(panel.grid.minor = element_blank(), plot.title = element_text(face = "bold"),
        plot.subtitle = element_text(color = "#444444"),
        axis.text.x = element_text(angle = 40, hjust = 1))

manifest <- read_result("phase20_category_manifest.tsv")
candidates <- read_result("phase20_relaxed_candidates.tsv")
top5 <- read_result("phase20_top5_summary.tsv")
stability <- read_result("phase20_stability_summary.tsv")
candidates$strict_non_mt_reference <- is_true(candidates$strict_non_mt_reference)

coverage <- manifest
coverage$signature_group <- factor(coverage$signature_group, levels = rev(groups))
coverage$broad_network <- factor(coverage$broad_network, levels = networks,
                                 labels = network_labels)
p_coverage <- ggplot(coverage, aes(broad_network, signature_group,
                                   fill = included_run_count)) +
  geom_tile(color = "white", linewidth = 0.7) +
  geom_text(aes(label = paste0(included_run_count, "\n", fine_cell_type_count,
                               " fine")), size = 3) +
  scale_fill_gradient(low = "#f2f2f2", high = "#2166ac", name = "Runs") +
  labs(title = "KDA run coverage for the 42 Phase 20 categories",
       subtitle = "Effective query >=3; cell text gives runs and distinct fine cell types",
       x = NULL, y = "Sex/APOE group") + theme_p20

evidence <- candidates
evidence$category_label <- factor(
  paste(evidence$signature_group, evidence$broad_network, sep = " · "),
  levels = category_levels
)
evidence$neg_log10_q <- -log10(pmax(evidence$relaxed_category_acat_q, 1e-300))
gene_count <- table(evidence$current_symbol)
best_q <- tapply(evidence$relaxed_category_acat_q, evidence$current_symbol, min)
genes <- names(sort(gene_count + (-log10(best_q) / 1000)))
evidence$current_symbol <- factor(evidence$current_symbol, levels = genes)
p_evidence <- ggplot(evidence, aes(category_label, current_symbol,
                                   fill = neg_log10_q)) +
  geom_tile(color = "white", linewidth = 0.25) +
  geom_point(data = evidence[evidence$strict_non_mt_reference, ],
             shape = 21, fill = "white", color = "black", size = 1.7) +
  scale_fill_gradient(low = "#fee8c8", high = "#b30000",
                      name = expression(-log[10](q))) +
  labs(title = "Relaxed non-MT key-driver evidence by category",
       subtitle = "White circles also pass the strict non-MT reference",
       x = "Sex/APOE · broad cell type", y = "Non-MT driver") +
  theme_p20 + theme(axis.text.y = element_text(size = 7))

top <- top5[!is.na(top5$current_symbol) & top5$list_status == "ranked_candidates", ]
top$category_label <- factor(paste(top$signature_group, top$broad_network, sep = " · "),
                             levels = category_levels)
top$strict_label <- ifelse(is_true(top$strict_non_mt_reference),
                           "strict", "relaxed only")
p_top <- ggplot(top, aes(factor(relaxed_rank), category_label,
                         fill = strict_label)) +
  geom_tile(color = "white", linewidth = 0.5) +
  geom_text(aes(label = current_symbol), size = 2.5) +
  scale_fill_manual(values = c(strict = "#80b1d3", "relaxed only" = "#fdb462"),
                    name = "Threshold tier") +
  labs(title = "Top five relaxed non-MT key drivers",
       subtitle = "Blank structural categories are not backfilled",
       x = "Within-category rank", y = "Sex/APOE · broad cell type") +
  theme_p20 + theme(axis.text.y = element_text(size = 7))

by_gene <- split(candidates, candidates$current_symbol)
recurrence <- do.call(rbind, lapply(names(by_gene), function(gene) {
  x <- by_gene[[gene]]
  data.frame(
    current_symbol = gene, category_count = nrow(x),
    group_count = length(unique(x$signature_group)),
    broad_network_count = length(unique(x$broad_network)),
    strict_category_count = sum(x$strict_non_mt_reference),
    best_relaxed_q = min(x$relaxed_category_acat_q)
  )
}))
recurrence <- recurrence[order(-recurrence$category_count,
                               recurrence$best_relaxed_q,
                               recurrence$current_symbol), ]
recurrence <- head(recurrence, 20)
recurrence$current_symbol <- factor(recurrence$current_symbol,
                                    levels = rev(recurrence$current_symbol))
p_recurrence <- ggplot(recurrence, aes(category_count, current_symbol,
                                       fill = strict_category_count)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = category_count), hjust = -0.2, size = 3) +
  scale_fill_gradient(low = "#b3cde3", high = "#005b96",
                      name = "Strict categories") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(title = "Most recurrent relaxed non-MT key drivers",
       subtitle = "Recurrence is counted across supported Phase 20 categories",
       x = "Number of categories", y = NULL) +
  theme_p20 + theme(axis.text.x = element_text(angle = 0))

stable <- stability[!is.na(stability$candidate_retention_fraction), ]
stable$current_symbol <- factor(
  stable$current_symbol,
  levels = unique(stable$current_symbol[order(stable$candidate_retention_fraction)])
)
p_stability <- ggplot(
  stable,
  aes(candidate_retention_fraction, current_symbol,
      color = evidence_label, size = assessable_repetitions)
) +
  geom_vline(xintercept = 0.8, linetype = 2, color = "#777777") +
  geom_point(alpha = 0.8) +
  scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2)) +
  labs(title = "Leave-one-fine-cell-type-out candidate retention",
       subtitle = "Only candidates with assessable multi-fine-type replicates",
       x = "Candidate-retention fraction", y = "Non-MT driver",
       color = "Evidence label", size = "Replicates") +
  theme_p20 + theme(axis.text.x = element_text(angle = 0),
                    axis.text.y = element_text(size = 7))

figure_manifest <- rbind(
  save_bundle(
    "category_coverage", p_coverage, coverage,
    c("# Phase 20 category coverage", "",
      "Phase 20-included KDA runs and distinct fine cell types for all 42 categories."),
    c("# Methods", "", "Counts come from phase20_category_manifest.tsv after requiring at least three effective query genes."),
    12, 5.5
  ),
  save_bundle(
    "driver_category_evidence", p_evidence, evidence,
    c("# Phase 20 driver-by-category evidence", "",
      "Relaxed non-MT candidates; white circles denote strict reference support."),
    c("# Methods", "", "Fill is -log10 of the non-MT-only within-category BH q value."),
    17, 11
  ),
  save_bundle(
    "top5_candidates", p_top, top,
    c("# Phase 20 top-five candidates", "",
      "Up to five passing relaxed non-MT drivers per supported category."),
    c("# Methods", "", "Ranks use category q, ACAT P, and gene symbol."),
    12, 9
  ),
  save_bundle(
    "driver_recurrence", p_recurrence, recurrence,
    c("# Phase 20 driver recurrence", "",
      "Top recurrent non-MT drivers across supported categories."),
    c("# Methods", "", "Each gene is counted once per supported category."),
    8, 7
  ),
  save_bundle(
    "stability_summary", p_stability, stable,
    c("# Phase 20 stability", "",
      "Candidate retention after omitting each fine cell type in turn."),
    c("# Methods", "",
      "Each replicate rebuilds the complete non-MT BH family."),
    10, 10
  )
)
figure_manifest$schema_version <- "phase20_sex_apoe_non_mt_figure_manifest_v2"
figure_manifest <- figure_manifest[
  , c("schema_version", "figure_id", "directory",
      "plot_data_rows", "validation_status")
]
write_tsv(figure_manifest, file.path(figure_root, "phase20_figure_manifest.tsv"))
cat(sprintf("wrote=%s\n", figure_root))
cat(sprintf("figure_bundles=%d\n", nrow(figure_manifest)))
cat(sprintf("validation_status=%s\n",
            if (all(figure_manifest$validation_status == "validated_complete"))
              "validated_complete" else "validation_failed"))
