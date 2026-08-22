#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
value_after <- function(flag) {
  index <- match(flag, args)
  if (is.na(index) || index == length(args)) {
    stop(paste("Missing", flag))
  }
  args[[index + 1]]
}

root <- value_after("--input-root")
matrix_path <- file.path(root, "endophenotype_context_biomarker_matrix.tsv")
gate_path <- file.path(root, "endophenotype_gate_decisions.tsv")
evidence <- read.delim(matrix_path, check.names = FALSE, stringsAsFactors = FALSE)
gate <- read.delim(gate_path, check.names = FALSE, stringsAsFactors = FALSE)

traits <- c("csf_abeta42", "csf_total_tau", "csf_ptau181")
trait_labels <- c("CSF A-beta 42", "CSF total tau", "CSF p-tau181")
genes <- sort(unique(evidence$gene))
grade_levels <- c("not_assessable", "none_found", "weak", "moderate", "strong")
grade_colors <- c("#D9D9D9", "#F7F7F7", "#FDD49E", "#FC8D59", "#B30000")

best_grade <- function(values) {
  observed <- match(values, grade_levels) - 1
  grade_levels[max(observed, na.rm = TRUE) + 1]
}

collapsed <- aggregate(
  extension_grade ~ gene + trait_id,
  data = evidence,
  FUN = best_grade
)
score <- matrix(NA_real_, nrow = length(traits), ncol = length(genes),
                dimnames = list(traits, genes))
for (i in seq_len(nrow(collapsed))) {
  score[collapsed$trait_id[[i]], collapsed$gene[[i]]] <-
    match(collapsed$extension_grade[[i]], grade_levels) - 1
}

draw_matrix <- function() {
  par(mar = c(8, 10, 4, 8), xpd = NA)
  image(
    x = seq_along(traits), y = seq_along(genes), z = score,
    col = grade_colors, breaks = seq(-0.5, 4.5, by = 1),
    axes = FALSE, xlab = "", ylab = "",
    main = "Phase 19 CSF endophenotype genetic evidence"
  )
  axis(1, at = seq_along(traits), labels = trait_labels, las = 2, cex.axis = 0.9)
  axis(2, at = seq_along(genes), labels = genes, las = 2, cex.axis = 0.72)
  for (x in seq_along(traits)) {
    for (y in seq_along(genes)) {
      label <- c("NA", "0", "W", "M", "S")[score[x, y] + 1]
      text(x, y, label, cex = 0.62)
    }
  }
  legend(
    x = length(traits) + 0.7, y = length(genes),
    legend = c("not assessable", "none found", "weak", "moderate", "strong"),
    fill = grade_colors, bty = "n", cex = 0.75
  )
  mtext("Scores summarize the best Phase 18 context for each gene/biomarker pair.",
        side = 1, line = 6.5, cex = 0.75)
}

pdf(file.path(root, "endophenotype_evidence_matrix.pdf"), width = 9.5, height = 11)
draw_matrix()
dev.off()

png(file.path(root, "endophenotype_evidence_matrix.png"),
    width = 1900, height = 2200, res = 200)
draw_matrix()
dev.off()

gate$plot_value <- suppressWarnings(-log10(as.numeric(gate$regional_min_p)))
gate$plot_value[!is.finite(gate$plot_value)] <- 0
gate$plot_value <- pmin(gate$plot_value, 50)
pdf(file.path(root, "endophenotype_locus_plots.pdf"), width = 12, height = 8)
for (trait_index in seq_along(traits)) {
  subset <- gate[gate$trait_id == traits[[trait_index]], ]
  subset <- subset[order(subset$plot_value, decreasing = TRUE), ]
  colors <- ifelse(subset$regional_signal == "TRUE", "#B30000", "#5B8DB8")
  par(mar = c(9, 5, 4, 2))
  barplot(
    subset$plot_value, names.arg = subset$gene, las = 2, col = colors,
    ylab = expression(-log[10](italic(P))), ylim = c(0, max(9, subset$plot_value + 1)),
    main = paste(trait_labels[[trait_index]], "candidate-region screens")
  )
  abline(h = -log10(5e-8), col = "#B30000", lty = 2, lwd = 2)
  legend("topright", legend = c("regional P < 5e-8", "below gate"),
         fill = c("#B30000", "#5B8DB8"), bty = "n")
}
dev.off()
