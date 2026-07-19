# Generating Mitochondrial Analogues of Yu Figures 3–6

## Purpose and boundary

This guide defines the downstream figure-generation workflow after Phase 11
has produced and validated all required data. It owns the visual choices and
image artifacts that are intentionally outside the Phase 11 data plan.

The scientific data specifications are defined in:

- [Phase 10 mitochondrial similarity plan](../phase_10_similarity/phase_10_mitochondrial_similarity_plan.md)
- [Phase 11 mitochondrial pathway data plan](../phase_11_pathway/phase_11_mitochondrial_pathway_data_plan.md)
- [Cross-cell-type similarity calculation explained](../phase_10_similarity/similarity_calculation_cross_celltypes_explained.md)

The figure workflow may:

- select the prespecified downstream profile;
- apply deterministic display-only pathway limits;
- turn validated long tables into heatmaps and dot plots;
- assemble panels A and B;
- write captions and a figure manifest; and
- export PDF and PNG files.

It must not:

- recalculate a similarity score or Phase 10 rank;
- reconstruct ternary DEG states;
- replace a stored top/bottom rank set;
- recalculate an ORA P value or BH FDR;
- change a query or background;
- substitute nominal pathways when no pathway passes the prespecified FDR; or
- write any image into `results/<environment>/10_similarity/` or
  `results/<environment>/11_pathway/`.

These are mitochondrial-restricted Yu analogues, not exact reproductions of
the paper's transcriptome-wide figures.

## Required validated inputs

The primary figure workflow reads:

```text
results/<environment>/10_similarity/similarity_status.tsv
results/<environment>/11_pathway/pathway_status.tsv
results/<environment>/11_pathway/similarity_panel_data.tsv.gz
results/<environment>/11_pathway/pathway_panel_data.tsv.gz
results/<environment>/11_pathway/downstream_panel_manifest.tsv
results/<environment>/11_pathway/pathway_reference_manifest.tsv
results/<environment>/11_pathway/pathway_artifacts.tsv
results/<environment>/11_pathway/pathway_checks.tsv
```

The Phase 10 status supplies the provenance of the similarity calculation.
The Phase 11 status, checks, and artifact manifest establish that the
panel-ready data is complete. The figure script should not reread Phase 08 or
Phase 09.

For production:

```text
Phase 10 validation_status = validated_complete
Phase 10 permutations = 10000
Phase 11 validation_status = validated_complete
```

For the local Vasculature smoke test, both input bundles are nonfinal and every
figure must carry `nonfinal_smoke_test` in its subtitle or watermark.

## Figure output directory

Write visual artifacts outside the scientific data phases:

```text
results/<environment>/figures/yu_mitochondrial/
```

Required primary files are:

```text
figure03_mitochondrial_yu_analogue.pdf
figure03_mitochondrial_yu_analogue.png
figure04_mitochondrial_yu_analogue.pdf
figure04_mitochondrial_yu_analogue.png
figure05_mitochondrial_yu_analogue.pdf
figure05_mitochondrial_yu_analogue.png
figure06_mitochondrial_yu_analogue.pdf
figure06_mitochondrial_yu_analogue.png
figure_manifest.tsv
figure_checks.tsv
```

The recommended implementation is:

```text
scripts/figures/phase11_figures_3_to_6.R
```

The figure script is a downstream consumer, not a Phase 11 pipeline task.

## Primary and sensitivity profiles

Use the profile labels frozen in
`downstream_panel_manifest.tsv`:

| Profile | Analysis universe | Pathway collection | Role |
|---|---|---|---|
| `primary_yu_mito` | `core_mito` | `msigdb_c2_cp_v2026_1` | Required Figures 3–6 |
| `focused_mitopathways` | `core_mito` | `mitocarta_mitopathways_v3_0` | Focused mitochondrial supplement |
| `inclusive_yu_sensitivity` | `all_mito_related` | `msigdb_c2_cp_v2026_1` | Inclusive-gene sensitivity |

Do not replace `primary_yu_mito` with a sensitivity profile because its
panels look more interesting. Sensitivity figures must be labeled and exported
separately.

## Figure mapping

| Figure panel | Comparison | Similarity-tail features | Pathway query |
|---|---|---:|---|
| 3A | `female_vs_male_all_apoe` | high 25 + low 25 | — |
| 3B | `female_vs_male_all_apoe` | — | high 200 + low 200 |
| 4A | `e2_vs_e33_all_sexes` | high 25 + low 25 | — |
| 4B | `e2_vs_e33_all_sexes` | — | high 200 + low 200 |
| 5A | `e4_vs_e33_all_sexes` | high 25 + low 25 | — |
| 5B | `e4_vs_e33_all_sexes` | — | high 200 + low 200 |
| 6A, e2 | `female_vs_male_e2` | high 10 + low 10 | — |
| 6A, e33 | `female_vs_male_e33` | high 10 + low 10 | — |
| 6A, e4 | `female_vs_male_e4` | high 10 + low 10 | — |
| 6B | the three within-APOE comparisons | — | low 200 for each |

Figure 6B uses `low_score` because Yu Results section 3.5 describes pathway
analysis of the bottom 200 similarity-ranked genes. The paper caption's phrase
“top 200 genes with the greatest sex differences” is interpreted as the same
most-divergent set, not the high-similarity tail.

## Preflight

From the repository root:

```bash
Rscript -e '
library(data.table)

sim_root <- "results/minerva_production/10_similarity"
path_root <- "results/minerva_production/11_pathway"

sim_status <- fread(file.path(sim_root, "similarity_status.tsv"))
path_status <- fread(file.path(path_root, "pathway_status.tsv"))
path_checks <- fread(file.path(path_root, "pathway_checks.tsv"))
path_artifacts <- fread(file.path(path_root, "pathway_artifacts.tsv"))
panels <- fread(file.path(path_root, "downstream_panel_manifest.tsv"))

stopifnot(
  sim_status$schema_version == "mitochondrial_similarity_status_v1",
  sim_status$validation_status == "validated_complete",
  sim_status$permutations == 10000L,
  path_status$schema_version == "mitochondrial_pathway_status_v1",
  path_status$validation_status == "validated_complete",
  all(path_checks$passed[path_checks$blocking]),
  all(path_artifacts$validation_status == "validated_complete"),
  all(c("primary_yu_mito", "focused_mitopathways",
        "inclusive_yu_sensitivity") %in% panels$profile_id)
)

cat("Validated Phase 10 and Phase 11 figure inputs are ready\n")
'
```

The figure script must repeat the relevant checks and record all input hashes
in `figure_manifest.tsv`.

## Panel A: similarity occurrence heatmaps

### Input fields

Use `similarity_panel_data.tsv.gz`. The final schema should provide at least:

- `figure_analogue`;
- `panel_id`;
- `comparison_id`;
- `analysis_universe`;
- `tail`;
- `requested_k` and `selected_k`;
- `selection_order`;
- `similarity_feature_id`;
- current symbol and display label;
- `pair_column`, `pair_label`, and `pair_order`;
- `occurrence_count` and `occurrence_fraction`;
- `similarity_score`;
- universe-specific `directional_fdr_bh`;
- `paired_tests` and `nominal_dimensions`;
- `score_scope`;
- `mito_tier`; and
- `genome_origin`.

### State-pair order

Use this fixed column order:

| Order | State pair | Interpretation |
|---:|---|---|
| 1 | `(+1,+1)` | significant up in both |
| 2 | `(-1,-1)` | significant down in both |
| 3 | `(+1,0)` | significant up only in first |
| 4 | `(-1,0)` | significant down only in first |
| 5 | `(0,+1)` | significant up only in second |
| 6 | `(0,-1)` | significant down only in second |
| 7 | `(+1,-1)` | opposite directions |
| 8 | `(-1,+1)` | opposite directions |
| 9 | `(0,0)` | nonsignificant in both |

### Row order and annotations

For each comparison:

1. show the `high_score` block first;
2. show the `low_score` block second;
3. preserve Phase 10 `selection_order` within each block;
4. use current HGNC symbol as the label;
5. append `[similarity_feature_id]` if symbols are duplicated;
6. annotate score and `paired_tests / nominal_dimensions`; and
7. mark `directional_fdr_bh < 0.05` without removing nonsignificant ranked
   features.

The primary fill is `occurrence_count`, which follows Yu's occurrence-count
description. A separately labeled sensitivity heatmap may use
`occurrence_fraction`. Never mix counts and fractions in one scale.

### Missingness

Missing Phase 10 positions are already excluded from `paired_tests`.
Consequently:

- zero occurrence means zero observed pairs in that category;
- zero does not mean a missing pair was imputed to `(0,0)`;
- coverage-adjusted features must show their observed/nominal dimensions; and
- only `complete_yu_vector` features may be described as complete fixed-N
  vectors.

### Heatmap construction skeleton

```r
library(data.table)
library(ggplot2)

similarity_data <- fread(
  "results/minerva_production/11_pathway/similarity_panel_data.tsv.gz"
)

make_panel_a <- function(comparison_value, requested_value,
                         universe_value = "core_mito") {
  d <- similarity_data[
    comparison_id == comparison_value &
      requested_k == requested_value &
      analysis_universe == universe_value
  ]
  stopifnot(nrow(d) > 0L)

  d[, tail := factor(
    tail,
    levels = c("high_score", "low_score"),
    labels = c("Highest similarity", "Lowest similarity")
  )]
  setorder(d, tail, selection_order, pair_order)

  gene_order <- unique(d[order(tail, selection_order), gene_label])
  d[, gene_label := factor(gene_label, levels = rev(gene_order))]
  d[, pair_label := factor(pair_label, levels = unique(
    d[order(pair_order), pair_label]
  ))]

  ggplot(d, aes(
    x = pair_label,
    y = gene_label,
    fill = occurrence_count
  )) +
    geom_tile(color = "white", linewidth = 0.2) +
    facet_grid(tail ~ ., scales = "free_y", space = "free_y") +
    scale_fill_viridis_c(name = "Occurrences") +
    labs(x = "Paired AD-versus-NCI ternary states", y = NULL) +
    theme_bw() +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1),
      panel.spacing.y = grid::unit(0.5, "lines")
    )
}
```

This code controls display only. It must not derive scores, ranks, state-pair
counts, or FDR values.

## Panel B: pathway enrichment dot plots

### Input fields

Use `pathway_panel_data.tsv.gz`. It should provide at least:

- `profile_id`;
- `figure_analogue` and `panel_id`;
- `comparison_id`, `analysis_universe`, and `tail`;
- `pathway_collection`, `pathway_id`, and display label;
- `test_status` and testability reason;
- `source_pathway_size` and `background_pathway_size`;
- `query_size` and `background_size`;
- `overlap_count`;
- `gene_ratio`, `background_ratio`, `fold_enrichment`, and
  `pathway_hit_rate`;
- `p_value`, `tail_fdr_bh`, and `global_fdr_bh`;
- `tail_fdr_significant`;
- deterministic `statistical_order`;
- `small_pathway_status`;
- `overlap_genes`; and
- per-query significant-pathway count.

### Display-only pathway selection

The complete Phase 11 table is authoritative. For each displayed query:

1. retain `test_status == "tested"`;
2. retain `tail_fdr_bh < 0.05`;
3. order by stored `statistical_order`;
4. display at most the first 15 pathways;
5. record the number omitted only because of the visual cap; and
6. never replace an empty result with nominal or arbitrary pathways.

If zero pathways pass, render an empty facet with:

```text
No C2:CP pathways at BH FDR < 0.05
```

For the focused MitoPathways supplement, change the collection name in the
message and mark pathways with 5–9 background members as lower confidence.

### Dot-plot encodings

Use:

- x-axis: `gene_ratio = overlap_count / query_size`;
- point size: `overlap_count`;
- point color: `-log10(tail_fdr_bh)` or a clearly labeled adjusted-P scale;
- y-axis: readable pathway label;
- Figures 3–5 facets: highest versus lowest similarity tails; and
- Figure 6 facets: e2, e33, and e4 low-score tails.

Do not use fold enrichment as the x-axis while labeling it gene ratio. The
caption must distinguish:

```text
GeneRatio = k / n
BackgroundRatio = M / N
Fold enrichment = (k / n) / (M / N)
```

### Dot-plot construction skeleton

```r
pathway_data <- fread(
  "results/minerva_production/11_pathway/pathway_panel_data.tsv.gz"
)

select_display_pathways <- function(d, max_pathways = 15L) {
  tested <- d[
    test_status == "tested" &
      !is.na(tail_fdr_bh) &
      tail_fdr_bh < 0.05
  ]
  setorder(tested, statistical_order)
  tested[, display_rank := seq_len(.N), by = query_id]
  tested[, display_selected := display_rank <= max_pathways]
  tested
}

make_panel_b <- function(comparison_value,
                         profile_value = "primary_yu_mito") {
  d <- pathway_data[
    profile_id == profile_value &
      comparison_id == comparison_value
  ]
  selected <- select_display_pathways(d)[display_selected]

  if (!nrow(selected)) {
    return(
      ggplot() +
        annotate(
          "text", x = 0.5, y = 0.5,
          label = "No C2:CP pathways at BH FDR < 0.05"
        ) +
        xlim(0, 1) + ylim(0, 1) +
        theme_void()
    )
  }

  selected[, pathway_label := factor(
    pathway_label,
    levels = rev(unique(pathway_label))
  )]

  ggplot(selected, aes(
    x = gene_ratio,
    y = pathway_label,
    size = overlap_count,
    color = -log10(tail_fdr_bh)
  )) +
    geom_point(alpha = 0.9) +
    facet_wrap(~ tail, scales = "free_y") +
    scale_color_viridis_c(name = expression(-log[10]("BH FDR"))) +
    labs(
      x = "Gene ratio (overlap genes / admitted query genes)",
      y = NULL,
      size = "Overlap"
    ) +
    theme_bw()
}
```

This compact helper handles a comparison in which every requested facet is
empty. The production implementation must also join the requested query IDs
from `downstream_panel_manifest.tsv` so that, when only one of two Figure
3–5 tails is empty, that individual tail still receives an explicit empty
facet.

For Figure 6B, select the three within-APOE `low_score` query IDs together
and facet by APOE group rather than calling this single-comparison helper.

## Assemble Figures 3–5

For each of Figures 3, 4, and 5:

1. create panel A with the appropriate comparison and `requested_k = 25`;
2. create panel B from the same comparison's high- and low-200 C2:CP queries;
3. label the panels `A` and `B`;
4. place A above B unless landscape legibility is better;
5. add a shared title identifying the biological comparison;
6. state `core_mito; mitochondrial-restricted Yu analogue`; and
7. include actual query/background sizes and the C2:CP release in the caption.

Recommended titles:

| Figure | Title |
|---|---|
| 3 | Sex-shared and sex-divergent mitochondrial transcriptional responses in AD |
| 4 | APOE e2-shared and e2-divergent mitochondrial transcriptional responses in AD |
| 5 | APOE e4-shared and e4-divergent mitochondrial transcriptional responses in AD |

## Assemble Figure 6

Figure 6A contains three vertically arranged heatmap blocks:

1. Female-versus-Male within e2;
2. Female-versus-Male within e33; and
3. Female-versus-Male within e4.

Each block uses `requested_k = 10` and both high/low tails.

Figure 6B contains only the three low-score 200-gene pathway queries, faceted
by e2, e33, and e4. Keep a shared gene-ratio scale when it remains readable;
otherwise state that x-axis ranges differ.

Combine the three heatmap blocks into panel A, then combine A with B into the
complete Figure 6.

## Export settings

Use vector PDF as the primary manuscript artifact and 300-dpi PNG as a review
artifact. Recommended starting dimensions are:

| Figure | Width | Height |
|---|---:|---:|
| 3 | 11 in | 15 in |
| 4 | 11 in | 15 in |
| 5 | 11 in | 15 in |
| 6 | 12 in | 22 in |

Adjust dimensions only for legibility; do not change data selection. Use an
atomic temporary file followed by rename so incomplete images never appear at
the final path.

Example:

```r
library(patchwork)

figure03 <- figure03a / figure03b +
  plot_annotation(tag_levels = "A")

ggsave(
  "results/minerva_production/figures/yu_mitochondrial/figure03_mitochondrial_yu_analogue.pdf",
  figure03, width = 11, height = 15, units = "in"
)
ggsave(
  "results/minerva_production/figures/yu_mitochondrial/figure03_mitochondrial_yu_analogue.png",
  figure03, width = 11, height = 15, units = "in", dpi = 300
)
```

The implementation should wrap exports in an atomic helper rather than writing
directly to the final file as this compact example does.

## Caption requirements

Every primary caption must state:

- the figure is a mitochondrial-restricted Yu analogue;
- the Phase 10 analysis universe is `core_mito`;
- panel A uses stored high/low Zhang–Yu rank sets;
- occurrences are pooled over the applicable cross-cell-type vector;
- missing paired states are excluded, not converted to nonsignificant;
- panel B uses actual mapped query size `n`;
- the background is the comparison-specific ranking-eligible mitochondrial
  universe of size `N`;
- pathways are Human MSigDB C2:CP v2026.1.Hs;
- points encode gene ratio, overlap, and within-query BH FDR; and
- `all_mito_related` and MitoPathways analyses are sensitivities.

Do not call a high-score gene significantly concordant or a low-score gene
significantly divergent unless its stored Phase 10 FDR supports that statement.
Likewise, do not call a pathway enriched unless its stored Phase 11
`tail_fdr_bh < 0.05`.

## Supplemental figures

After the four primary figures are frozen, the same visual workflow may
produce:

```text
supplementary_core_mitopathways.pdf
supplementary_all_mito_related_c2_cp.pdf
supplementary_occurrence_fraction_heatmaps.pdf
```

Each must identify its nonprimary profile in the title and caption. Do not mix
profiles within an unlabeled panel.

## Figure manifest

Write one record per final image with:

- figure ID and profile;
- PDF/PNG path;
- width, height, DPI, and page count;
- Phase 10 status hash;
- Phase 11 status, panel-data, and manifest hashes;
- figure-script hash;
- R, ggplot2, and patchwork versions;
- creation timestamp and Git revision;
- source comparison/query IDs;
- display cap and number of significant/omitted pathways;
- file bytes and SHA-256; and
- validation status.

The figure manifest documents visual provenance but must not alter Phase 11's
scientific status.

## Visual and data validation

### Panel A checks

- Figures 3–5 contain 25 high and 25 low features.
- Every Figure 6 APOE block contains 10 high and 10 low features.
- Feature and tail order matches `selection_order`.
- All nine state-pair categories appear in fixed order, including zero-count
  categories.
- Tile values equal `occurrence_count`.
- Coverage-adjusted features show observed/nominal dimensions.
- No gene is filtered by FDR after rank-set selection.

### Panel B checks

- Figures 3–5 use both high- and low-score 200 queries.
- Figure 6 uses only the three low-score 200 queries.
- Primary figures use `core_mito × msigdb_c2_cp_v2026_1`.
- Every plotted point has `test_status = tested` and
  `tail_fdr_bh < 0.05`.
- Display order follows stored statistical order.
- At most 15 pathways occur per displayed query.
- Empty significant results produce an explicit empty panel.
- Point x, size, and color reproduce stored gene ratio, overlap, and FDR.

### Artifact checks

- Four PDF and four PNG primary images exist and are nonempty.
- PDFs open and have the expected page count.
- PNGs are 300 dpi at the recorded dimensions.
- No figure was written into `10_similarity/` or `11_pathway/`.
- Every image appears in `figure_manifest.tsv` with a matching checksum.
- A rerun with identical inputs produces identical panel-data selection; minor
  binary differences caused by PDF metadata are reported if present.

## Completion criteria

The figure workflow is complete when:

- validated Phase 10 and Phase 11 production bundles are the only scientific
  inputs;
- four primary mitochondrial Figure 3–6 analogues exist in PDF and PNG;
- every panel follows the frozen mapping and profile;
- no statistical result has been recalculated;
- all captions disclose universe, coverage, query/background, pathway release,
  and FDR scope;
- visual checks pass; and
- the figure manifest hashes every input and image.
