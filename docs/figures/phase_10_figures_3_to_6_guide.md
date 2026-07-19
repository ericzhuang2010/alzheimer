# Building Figure 3–6 Similarity Heatmaps from Phase 10

Phase 10 provides everything needed to construct the non-pathway “A” panels
of Yu Figures 3–6. It does not draw them itself. The relevant handoff is
described in the
[Phase 10 plan](../phase_10_similarity/phase_10_mitochondrial_similarity_plan.md#downstream-handoff),
and the cross-cell-type construction is explained in
[Which Cell Types Are Used in Figures 3, 4, 5, and 6?](../phase_10_similarity/similarity_calculation_cross_celltypes_explained.md).

These will be mitochondrial analogues of Yu's figures, not exact
transcriptome-wide reproductions.

## Figure mapping

| Figure analogue | `comparison_id` | Gene selection | Dimensions summarized |
|---|---|---|---:|
| Figure 3A | `female_vs_male_all_apoe` | Top 25 and bottom 25 | 54 cell types × 3 APOE groups = 162 |
| Figure 4A | `e2_vs_e33_all_sexes` | Top 25 and bottom 25 | 54 cell types × 2 sexes = 108 |
| Figure 5A | `e4_vs_e33_all_sexes` | Top 25 and bottom 25 | 54 cell types × 2 sexes = 108 |
| Figure 6A, ε2 | `female_vs_male_e2` | Top 10 and bottom 10 | 54 cell types |
| Figure 6A, ε3/ε3 | `female_vs_male_e33` | Top 10 and bottom 10 | 54 cell types |
| Figure 6A, ε4 | `female_vs_male_e4` | Top 10 and bottom 10 | 54 cell types |

For this task, ignore every rank-set row with `requested_k == 200`; those
rows were retained for pathway analysis.

## Which output supplies what?

Use four Phase 10 files:

- `mitochondrial_similarity_rank_sets.tsv` selects the exact top and bottom
  genes and supplies their plotting order.
- `mitochondrial_similarity_results.tsv.gz` supplies the nine state-pair
  counts, similarity score, FDR, and coverage.
- `mitochondrial_similarity_state_pairs.tsv.gz` supplies the underlying
  cell-type/stratum states and missingness; use it to audit or reconstruct
  the counts.
- `similarity_comparison_manifest.tsv` supplies comparison labels, vector
  definitions, and expected dimensions.

Use `core_mito` for the primary figure. Use `all_mito_related` only for a
separately labeled inclusive figure.

## Heatmap contents

For every selected gene, plot the frequencies of the nine possible state
pairs:

| State pair | Meaning |
|---|---|
| `(+1,+1)` | Significantly up in both groups |
| `(-1,-1)` | Significantly down in both groups |
| `(+1,0)`, `(-1,0)` | Significant only in the first group |
| `(0,+1)`, `(0,-1)` | Significant only in the second group |
| `(+1,-1)`, `(-1,+1)` | Significant in opposite directions |
| `(0,0)` | Nonsignificant in both groups |

The corresponding columns in
`mitochondrial_similarity_results.tsv.gz` are:

```text
S_pos1_pos1
S_neg1_neg1
S_pos1_0
S_neg1_0
S_0_pos1
S_0_neg1
S_pos1_neg1
S_neg1_pos1
S_0_0
```

These counts are pooled across all applicable cell types and strata. They
must not be calculated separately within each cell type and then averaged.

## Construction procedure

For each figure:

1. Filter `mitochondrial_similarity_rank_sets.tsv` to the appropriate
   `comparison_id`.
2. Select one `analysis_universe`, preferably `core_mito`.
3. Select `requested_k == 25` for Figures 3–5 or `requested_k == 10` for
   Figure 6.
4. Retain both `high_score` and `low_score` tails.
5. Use `selection_order` to order genes within each tail.
6. Join the selected genes to
   `mitochondrial_similarity_results.tsv.gz`.
7. Reshape the nine `S_*` columns into a long gene-by-state-pair table.
8. Draw a heatmap with genes as rows, state pairs as columns, and occurrence
   count as fill.
9. Show the high-score and low-score tails as separate row blocks.
10. Annotate each gene with its score, stored FDR, and
    `paired_tests / nominal_dimensions`.

Do not filter the displayed genes by FDR after selecting the tails. The
top/bottom sets are score-based. Instead, mark genes with
`directional_fdr_bh <= 0.05`, for example with an asterisk.

## Compact R example

Run this against the completed Minerva output:

```r
library(data.table)
library(ggplot2)

root <- "results/minerva_production/10_similarity"

status <- fread(file.path(root, "similarity_status.tsv"))
stopifnot(
  status$validation_status == "validated_complete",
  status$permutations == 10000L
)

rank_sets <- fread(
  file.path(root, "mitochondrial_similarity_rank_sets.tsv")
)
results <- fread(
  file.path(root, "mitochondrial_similarity_results.tsv.gz")
)

pair_columns <- c(
  S_pos1_pos1 = "(+1,+1) same",
  S_neg1_neg1 = "(-1,-1) same",
  S_pos1_0    = "(+1,0) different",
  S_neg1_0    = "(-1,0) different",
  S_0_pos1    = "(0,+1) different",
  S_0_neg1    = "(0,-1) different",
  S_pos1_neg1 = "(+1,-1) opposite",
  S_neg1_pos1 = "(-1,+1) opposite",
  S_0_0       = "(0,0) neither"
)

make_similarity_panel <- function(
    comparison_value,
    requested_value,
    universe_value = "core_mito") {

  selected <- rank_sets[
    comparison_id == comparison_value &
      analysis_universe == universe_value &
      requested_k == requested_value
  ]

  stopifnot(nrow(selected) > 0L)

  counts <- results[
    comparison_id == comparison_value,
    c(
      "comparison_id",
      "similarity_feature_id",
      names(pair_columns)
    ),
    with = FALSE
  ]

  plot_data <- merge(
    selected,
    counts,
    by = c("comparison_id", "similarity_feature_id"),
    all.x = TRUE
  )

  plot_data[, tail_order := match(
    tail, c("high_score", "low_score")
  )]
  setorder(plot_data, tail_order, selection_order)

  plot_data[, gene_label := fifelse(
    !is.na(symbol_hgnc_current) & nzchar(symbol_hgnc_current),
    symbol_hgnc_current,
    similarity_feature_id
  )]

  # Disambiguate features sharing the same displayed symbol.
  plot_data[, gene_label := if (.N > 1L) {
    paste0(gene_label, " [", similarity_feature_id, "]")
  } else {
    gene_label
  }, by = gene_label]

  long <- melt(
    plot_data,
    id.vars = c(
      "comparison_id", "tail", "selection_order",
      "gene_label", "similarity_score",
      "directional_fdr_bh", "paired_tests",
      "nominal_dimensions"
    ),
    measure.vars = names(pair_columns),
    variable.name = "pair_column",
    value.name = "occurrences"
  )

  long[, pair_label := factor(
    pair_columns[pair_column],
    levels = unname(pair_columns)
  )]

  long[, gene_label := factor(
    gene_label,
    levels = rev(unique(plot_data$gene_label))
  )]

  ggplot(long, aes(
    x = pair_label,
    y = gene_label,
    fill = occurrences
  )) +
    geom_tile(color = "white", linewidth = 0.2) +
    facet_grid(
      tail ~ .,
      scales = "free_y",
      space = "free_y"
    ) +
    scale_fill_viridis_c(name = "Occurrences") +
    labs(
      title = comparison_value,
      subtitle = paste(
        universe_value,
        "— high and low Zhang–Yu similarity scores"
      ),
      x = "Paired AD-versus-NCI ternary states",
      y = NULL
    ) +
    theme_bw() +
    theme(
      axis.text.x = element_text(
        angle = 45, hjust = 1
      ),
      panel.spacing.y = grid::unit(0.5, "lines")
    )
}
```

Construct the panels as follows:

```r
figure3a <- make_similarity_panel(
  "female_vs_male_all_apoe", 25
)

figure4a <- make_similarity_panel(
  "e2_vs_e33_all_sexes", 25
)

figure5a <- make_similarity_panel(
  "e4_vs_e33_all_sexes", 25
)

figure6_e2 <- make_similarity_panel(
  "female_vs_male_e2", 10
)

figure6_e33 <- make_similarity_panel(
  "female_vs_male_e33", 10
)

figure6_e4 <- make_similarity_panel(
  "female_vs_male_e4", 10
)
```

Figure 6A is the combination of the three Figure 6 panels. For example, with
`patchwork`:

```r
library(patchwork)

figure6a <- figure6_e2 / figure6_e33 / figure6_e4
```

Save the figures under a later figure-phase directory, not inside
`10_similarity`, because Phase 10 explicitly prohibits figure artifacts:

```r
figure_root <- "results/minerva_production/<later_figure_phase>"
dir.create(figure_root, recursive = TRUE, showWarnings = FALSE)

ggsave(file.path(figure_root, "figure03a_similarity.pdf"),
       figure3a, width = 10, height = 12)
ggsave(file.path(figure_root, "figure04a_similarity.pdf"),
       figure4a, width = 10, height = 12)
ggsave(file.path(figure_root, "figure05a_similarity.pdf"),
       figure5a, width = 10, height = 12)
ggsave(file.path(figure_root, "figure06a_similarity.pdf"),
       figure6a, width = 10, height = 18)
```

## Reporting and validation requirements

- For genes with
  `score_scope == "coverage_adjusted_cross_celltype"`, report
  `paired_tests / nominal_dimensions` in the figure or caption.
- Missing states must remain missing; they must never be converted to
  `(0,0)`.
- A zero category count in the heatmap means that no observed paired
  dimension had that state pair. It is not an imputation of missing states.
- Use the stored universe-specific `directional_fdr_bh`; do not recalculate
  FDR after selecting or viewing candidate genes.
- Do not call a high-score gene significantly concordant or a low-score gene
  significantly divergent unless its stored FDR passes the prespecified
  threshold.
- Keep `similarity_feature_id` as the true row identity. A gene symbol is a
  display label and may need disambiguation.
