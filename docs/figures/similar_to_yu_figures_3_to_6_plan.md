# Plan for Mitochondrial Analogues of Yu Figures 3–6

## Status and workflow boundary

This document defines the standalone figure-generation workflow that follows
the validated Phase 10 mitochondrial-similarity phase and the validated Phase
11 mitochondrial-pathway phase. It converts their frozen, panel-ready
production tables into mitochondrial analogues of Yu et al. Figures 3, 4, 5,
and 6. Figure generation is not assigned a pipeline phase number.

Execution status on 2026-07-19: the corrected workflow completed locally from
the validated Minerva production bundles. Panel-A columns are grouped into
separately colored Same, Different, and Opposite blocks, and panel B shows the
best-ranked pathway matches for both 200-gene score tails even when none pass
BH FDR. Four PDF and four 300-dpi PNG figures were regenerated under
`results/figures/figures03_to_06/`; all 71 blocking checks pass and
`figure_status.tsv` is `validated_complete`.

The figure workflow will:

- validate the complete Phase 10 and Phase 11 production handoffs;
- select the prespecified primary downstream profile;
- draw similarity occurrence heatmaps from stored Phase 11 panel-A rows;
- draw pathway-analysis dot plots from the complete stored Phase 11 ORA table;
- retain the best-ranked matched pathways for both high- and low-score tails,
  while distinguishing FDR-significant from nonsignificant results;
- assemble four complete Yu-style figure analogues;
- write captions, displayed-data tables, checks, and provenance manifests;
  and
- export manuscript-quality PDF and review-quality PNG files.

The implementation code will be placed under:

```text
scripts/figures/
```

The primary implementation script will be:

```text
scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R
```

All new figure artifacts will be placed under:

```text
results/figures/figures03_to_06/
```

The figure workflow must **not**:

- refit MAST or any other differential-expression model;
- read normalized Seurat objects or pseudobulk products;
- reconstruct Phase 09 ternary DEG states;
- recalculate a Phase 10 similarity score, empirical P value, FDR, or rank;
- replace a stored Phase 10 high- or low-score rank set;
- rerun Phase 11 ORA or recalculate its P values or FDR values;
- change a Phase 11 query, background, pathway collection, or gene mapping;
- substitute nominal pathways when no pathway passes the required FDR;
- write into `results/minerva_production/10_similarity/` or
  `results/minerva_production/11_pathway/`; or
- modify any result from an earlier phase.

The supporting design documents are:

- [Phase 10 mitochondrial similarity plan](../phase_10_similarity/phase_10_mitochondrial_similarity_plan.md)
- [Phase 11 mitochondrial pathway data plan](../phase_11_pathway/phase_11_mitochondrial_pathway_data_plan.md)
- [Phase 10 Figures 3–6 guide](phase_10_figures_3_to_6_guide.md)
- [Phase 11 Figures 3–6 guide](phase_11_mitochondrial_figures_3_to_6_guide.md)
- [Cross-cell-type similarity explanation](../phase_10_similarity/similarity_calculation_cross_celltypes_explained.md)

This plan is authoritative for the figure workflow's paths, execution,
outputs, and acceptance criteria. In particular, it supersedes the older
guides' example output paths by requiring all new images under
`results/figures/figures03_to_06/`.

## High-level purpose

Yu et al. used the Zhang–Yu similarity measure to rank genes by the agreement
or divergence of AD-versus-NCI transcriptional responses between sexes or
APOE groups. Their Figures 3–5 showed the highest- and lowest-scoring genes
and pathway enrichment of 200-gene score tails. Their Figure 6 repeated the
sex comparison within each APOE group.

Phase 10 has already calculated the mitochondrial-restricted scores and
frozen the rank sets. Phase 11 has already performed pathway enrichment and
prepared long-form plot data. The figure workflow will display those stored
results for:

- Figure 3 analogue: Female versus Male across all APOE groups;
- Figure 4 analogue: APOE e2 versus e33 across both sexes;
- Figure 5 analogue: APOE e4 versus e33 across both sexes; and
- Figure 6 analogue: Female versus Male separately within e2, e33, and e4.

These figures will be mitochondrial-restricted analogues, not exact
transcriptome-wide reproductions of the Yu figures. Their purpose is to show
which mitochondrial transcriptional responses are relatively shared or
divergent and which canonical pathways are overrepresented in the frozen
mitochondrial rank tails.

## Local execution decision

### Decision

The figure workflow should run locally against the completed Minerva
production tables. It does not require Phase 05 or Phase 07 outputs and does
not require another Minerva job.

### Evidence from the current repository

| Requirement | Observed local state on 2026-07-19 | Decision |
|---|---|---|
| Phase 10 production status | `validated_complete`; 6 comparisons; 10,000 permutations | Ready |
| Phase 11 production status | `validated_complete`; all blocking checks pass | Ready |
| Panel-ready similarity data | 3,780 rows in `similarity_panel_data.tsv.gz` | Ready |
| Panel-ready pathway data | 75,411 rows in `pathway_panel_data.tsv.gz` | Ready |
| Complete stored ORA data | 102,336 rows in `similarity_tail_pathway_ora.tsv.gz` | Ready |
| Phase 10 disk footprint | Approximately 23 MB | Small local input |
| Phase 11 disk footprint | Approximately 9 MB | Small local input |
| Required R packages | `data.table`, `ggplot2`, `patchwork`, `scales`, `yaml`, and `digest` installed | Ready |
| Headless graphics | Cairo PDF and PNG capabilities available | Ready |
| Phase 05 local production directory | Absent | Not required |
| Phase 07 local production directory | Absent | Not required |

The figure script will read only status, check, manifest, and panel-ready files
from Phases 10 and 11. It will not read Phase 10's 20 MB state-pair table during
normal figure construction, because Phase 11 has already validated and
reshaped those counts into `similarity_panel_data.tsv.gz`.

The local run is a final production rendering, not a local pilot. Every title,
caption, and status row will identify the scientific inputs as
`minerva_production` even though the lightweight rendering itself runs on the
local machine.

## Relationship to Yu and deliberate differences

### What remains the same

- Figures 3–5 panel A use the top 25 and bottom 25 similarity-ranked genes.
- Figures 3–5 panel B use the top 200 and bottom 200 score tails.
- Figure 6 panel A uses the top 10 and bottom 10 genes within each APOE group.
- Figure 6 panel B uses the most sex-divergent 200-gene tail within e2, e33,
  and e4.
- Heatmap intensity represents the observed frequency of paired ternary DEG
  states.
- Pathway panels show significantly enriched Human MSigDB C2:CP canonical
  pathways.
- The displayed pathway evidence includes gene ratio, overlap count, and
  Benjamini–Hochberg-adjusted P value.

### What changes

| Item | Yu figures | Planned mitochondrial figures |
|---|---|---|
| Gene universe | Transcriptome-wide | Phase 10 `core_mito` primary universe |
| Similarity ranks | Yu's published ranks | Frozen Phase 10 mitochondrial ranks |
| Missing paired states | Not detailed in the figure | Excluded from the observed denominator and disclosed as coverage |
| Panel-A feature identity | Gene symbol | Exact assay feature; disambiguated display symbol |
| Pathway background | All analyzed genes reported by Yu | Comparison-specific ranking-eligible mitochondrial genes |
| Pathway reference | C2:CP release not reported | Human MSigDB C2:CP v2026.1.Hs |
| Nonsignificant pathway result | Not clearly distinguished | Retained as an open point; only filled points pass BH FDR 0.05 |
| Display cap | Only shown pathways visible | Deterministic first 15 tested pathways with positive overlap per query |
| Sensitivity analyses | Not applicable | `all_mito_related` and MitoPathways retained as labeled, nonprimary options |

The caption of every primary figure must state that it is a
mitochondrial-restricted Yu analogue. A high-score or low-score rank alone
must not be described as statistically significant. Significance language is
allowed only when supported by the stored Phase 10 or Phase 11 FDR.

## Frozen figure specification

### Primary downstream profile

The required primary figures use the Phase 11 profile:

```text
profile_id = primary_yu_mito
analysis_universe = core_mito
pathway_collection = msigdb_c2_cp_v2026_1
```

The following profiles remain prespecified sensitivities but are outside the
primary figure-workflow completion gate:

| Profile | Universe | Collection | Role |
|---|---|---|---|
| `focused_mitopathways` | `core_mito` | `mitocarta_mitopathways_v3_0` | Focused mitochondrial pathway supplement |
| `inclusive_yu_sensitivity` | `all_mito_related` | `msigdb_c2_cp_v2026_1` | Inclusive-gene sensitivity |

Primary and sensitivity profiles must never be mixed in an unlabeled figure.
Sensitivity figures may be added only after the four primary figures pass all
acceptance checks.

### Figure and comparison mapping

| Figure | Panel | `comparison_id` | Rank tail and size | Nominal paired dimensions |
|---|---|---|---:|---:|
| 3 | A | `female_vs_male_all_apoe` | high 25 + low 25 | 162 |
| 3 | B | `female_vs_male_all_apoe` | high 200 + low 200 | — |
| 4 | A | `e2_vs_e33_all_sexes` | high 25 + low 25 | 108 |
| 4 | B | `e2_vs_e33_all_sexes` | high 200 + low 200 | — |
| 5 | A | `e4_vs_e33_all_sexes` | high 25 + low 25 | 108 |
| 5 | B | `e4_vs_e33_all_sexes` | high 200 + low 200 | — |
| 6 | A, e2 | `female_vs_male_e2` | high 10 + low 10 | 54 |
| 6 | A, e33 | `female_vs_male_e33` | high 10 + low 10 | 54 |
| 6 | A, e4 | `female_vs_male_e4` | high 10 + low 10 | 54 |
| 6 | B, e2 | `female_vs_male_e2` | high 200 + low 200 | — |
| 6 | B, e33 | `female_vs_male_e33` | high 200 + low 200 | — |
| 6 | B, e4 | `female_vs_male_e4` | high 200 + low 200 | — |

The corrected panel-B rule is uniform across all six comparisons: sort the
eligible genes by the stored Phase 10 similarity score, use the stored top 200
and bottom 200 rank sets, and display pathway matches for both. Figure 6
therefore contains paired highest- and lowest-similarity pathway facets within
each APOE group.

### Panel A: similarity occurrence heatmaps

#### Authoritative input and filtering

Panel A reads:

```text
results/minerva_production/11_pathway/similarity_panel_data.tsv.gz
```

It filters to `analysis_universe == "core_mito"`, the required
`comparison_id`, and `requested_k` of 25 or 10. It must use stored:

- `similarity_feature_id` and `display_label`;
- `tail`, `tail_order`, and `selection_order`;
- `pair_column`, `pair_label`, and `pair_order`;
- `occurrence_count` and `occurrence_fraction`;
- `similarity_score` and `directional_fdr_bh`;
- `paired_tests` and `nominal_dimensions`; and
- `score_scope`.

The primary fill value is `occurrence_count`, matching Yu's occurrence-count
description. `occurrence_fraction` may be used only in a separately labeled
sensitivity figure.

#### State-pair order

All nine paired states must remain present in the following fixed order, even
when a category has zero occurrences:

| Order | `pair_column` | Display | Interpretation | Header group |
|---:|---|---|---|---|
| 1 | `S_pos1_pos1` | `(+1,+1)` | significant up in both | Same |
| 2 | `S_neg1_neg1` | `(-1,-1)` | significant down in both | Same |
| 3 | `S_pos1_0` | `(+1,0)` | significant up only in first | Different |
| 4 | `S_neg1_0` | `(-1,0)` | significant down only in first | Different |
| 5 | `S_0_pos1` | `(0,+1)` | significant up only in second | Different |
| 6 | `S_0_neg1` | `(0,-1)` | significant down only in second | Different |
| 7 | `S_pos1_neg1` | `(+1,-1)` | significant in opposite directions | Opposite |
| 8 | `S_neg1_pos1` | `(-1,+1)` | significant in opposite directions | Opposite |
| 9 | `S_0_0` | `(0,0)` | nonsignificant in both observed tests | Not tiled |

A zero `occurrence_count` means no **observed paired dimension** had that
state pair. It must never represent an imputed missing pair. The script must
not reconstruct these counts from Phase 10. The `(0,0)` count remains in the
score denominator and is validated with the other eight cells, but it is not
displayed because the corrected Yu-style heatmap has only Same, Different,
and Opposite blocks.

#### Row order and labels

For each comparison:

1. display `high_score` before `low_score`;
2. preserve `selection_order` within each tail;
3. label the blocks `Highest similarity` and `Lowest similarity`;
4. use the stored disambiguated `display_label` rather than rebuilding gene
   labels;
5. include the stored score and `paired_tests / nominal_dimensions` in the
   row annotation;
6. append an asterisk when `directional_fdr_bh <= 0.05`; and
7. explain the asterisk in the caption.

No feature may be filtered after rank-tail selection. In particular, panel A
must not remove a ranked feature because its stored FDR exceeds 0.05.

The displayed columns form three blocks with their own sequential color
legends: Same is green, Different is orange, and Opposite is purple. All three
legends use the same occurrence-count limits within a full figure, so
intensities remain quantitatively comparable. Figure 6 shares those limits
across its three APOE blocks.

#### Expected primary panel-A sizes

| Figure | Features | State-pair rows |
|---|---:|---:|
| 3A | 25 high + 25 low = 50 | 400 |
| 4A | 25 high + 25 low = 50 | 400 |
| 5A | 25 high + 25 low = 50 | 400 |
| 6A | 3 × (10 high + 10 low) = 60 | 480 |
| Total | 210 displayed feature records | 1,680 |

The script first validates all 1,890 `core_mito` source rows, including the
210 `(0,0)` rows, then writes the exact 1,680 rows tiled in panel A.

### Panel B: pathway-enrichment dot plots

#### Authoritative input and filtering

Panel B reads:

```text
results/minerva_production/11_pathway/pathway_panel_data.tsv.gz
results/minerva_production/11_pathway/similarity_tail_pathway_ora.tsv.gz
results/minerva_production/11_pathway/pathway_query_manifest.tsv
results/minerva_production/11_pathway/downstream_panel_manifest.tsv
```

The query manifest defines the 12 primary high/low 200-gene queries. For each
query, the script will:

1. require `analysis_universe == "core_mito"` and the frozen C2:CP collection;
2. require `test_status == "tested"`;
3. require `overlap_count > 0` for a displayed pathway match;
4. order by stored `statistical_order`;
5. select at most the first 15 pathways for display;
6. retain and report the complete number passing stored
   `tail_fdr_bh < 0.05`; and
7. show nonsignificant matches rather than dropping the entire high tail.

The script must not recompute ORA, adjust P values again, choose a nominal
P-value cutoff, or call an open nonsignificant point enriched.

#### Dot-plot encodings

Use the stored values as follows:

- x-axis: `gene_ratio = overlap_count / query_size`;
- point size: `overlap_count`;
- point color: `-log10(tail_fdr_bh)`;
- point shape: filled when `tail_fdr_bh < 0.05`, open otherwise;
- y-axis: `pathway_label` in stored statistical order;
- Figures 3–5 facets: high-score tail followed by low-score tail; and
- Figure 6 facets: high and low tails paired within e2, e33, and e4.

The facets within one figure will share x, color, and size scales. A pathway
label will be wrapped deterministically at a configured width without
changing the underlying name.

If a query has no tested pathway with positive overlap, its facet retains its
title and displays:

```text
No tested pathways share a gene with this 200-gene tail
```

Gene ratio, background ratio, and fold enrichment must not be conflated. The
caption will define:

```text
GeneRatio       = k / n
BackgroundRatio = M / N
Fold enrichment = (k / n) / (M / N)
```

Only gene ratio is plotted on the x-axis.

#### Observed primary production baseline

The current validated Phase 11 input produces the following deterministic
display baseline:

| Panel-B query | Query/background | Positive-overlap matches | FDR-significant | Displayed |
|---|---:|---:|---:|---:|
| Figure 3 high | 200 / 700 | 241 | 0 | 15 |
| Figure 3 low | 200 / 700 | 292 | 81 | 15 |
| Figure 4 high | 200 / 708 | 283 | 0 | 15 |
| Figure 4 low | 200 / 708 | 294 | 58 | 15 |
| Figure 5 high | 200 / 686 | 231 | 0 | 15 |
| Figure 5 low | 200 / 686 | 295 | 53 | 15 |
| Figure 6 e2 high | 200 / 732 | 276 | 0 | 15 |
| Figure 6 e2 low | 200 / 732 | 301 | 39 | 15 |
| Figure 6 e33 high | 200 / 705 | 267 | 0 | 15 |
| Figure 6 e33 low | 200 / 705 | 310 | 52 | 15 |
| Figure 6 e4 high | 200 / 679 | 286 | 0 | 15 |
| Figure 6 e4 low | 200 / 679 | 273 | 29 | 15 |

The zero high-tail FDR counts remain visible as open points. This separates
the existence of pathway matches from evidence of statistically significant
overrepresentation.

### Figure assembly

Figures 3–5 will place panel A above panel B and use the following titles:

| Figure | Title |
|---|---|
| 3 | Sex-shared and sex-divergent mitochondrial transcriptional responses in AD |
| 4 | APOE e2-shared and e2-divergent mitochondrial transcriptional responses in AD |
| 5 | APOE e4-shared and e4-divergent mitochondrial transcriptional responses in AD |

Figure 6 panel A will contain three vertically arranged heatmap blocks in the
order e2, e33, and e4. Each block contains both highest- and lowest-similarity
genes. Figure 6 panel B will pair highest- and lowest-similarity pathway
facets in the same APOE order.

Every composite will:

- use panel tags `A` and `B`;
- state `core_mito; mitochondrial-restricted Yu analogue` in its subtitle;
- use consistent typography and margins across all four figures;
- place legends so they do not compress gene or pathway labels; and
- contain no post hoc annotations that are absent from the stored tables.

### Export specification

The primary manuscript artifact is vector PDF. A 300-dpi PNG is required for
review and presentation.

| Figure | Width | Height | PDF pages | PNG pixels at 300 dpi |
|---|---:|---:|---:|---:|
| 3 | 11 in | 15 in | 1 | 3300 × 4500 |
| 4 | 11 in | 15 in | 1 | 3300 × 4500 |
| 5 | 11 in | 15 in | 1 | 3300 × 4500 |
| 6 | 12 in | 30 in | 1 | 3600 × 9000 |

Use `grDevices::cairo_pdf` for PDF and a headless Cairo PNG device for PNG.
The local R installation reports both capabilities. Dimensions may be
increased during implementation only to resolve clipping or illegibility;
the data selection and panel mapping must remain unchanged, and final
dimensions must be recorded in the manifest.

### Caption requirements

Every primary caption must state:

- that the figure is a mitochondrial-restricted Yu analogue;
- that the primary Phase 10 universe is `core_mito`;
- which biological groups and cross-cell-type dimensions are compared;
- that panel A uses stored high/low Zhang–Yu score ranks;
- that heatmap counts pool observed paired states across the applicable
  cross-cell-type vector;
- that missing states are excluded rather than changed to `(0,0)`;
- what the score, FDR asterisk, and observed/nominal coverage annotation mean;
- that panel B uses the actual mapped query size `n` and the matching
  ranking-eligible background size `N`;
- that the pathway reference is Human MSigDB C2:CP v2026.1.Hs;
- that point x, size, and color encode gene ratio, overlap count, and
  within-query BH FDR;
- that filled versus open points distinguish FDR-significant from
  nonsignificant pathway matches;
- that the display includes top-ranked positive-overlap matches regardless of
  FDR and does not label nonsignificant matches as enriched; and
- that `all_mito_related` and MitoPathways are sensitivity profiles.

## Inputs and dependencies

### Required Phase 10 inputs

The figure workflow reads the following only to validate upstream provenance:

```text
results/minerva_production/10_similarity/similarity_status.tsv
results/minerva_production/10_similarity/similarity_checks.tsv
results/minerva_production/10_similarity/similarity_artifacts.tsv
```

The required production conditions are:

```text
schema_version = mitochondrial_similarity_status_v1
validation_status = validated_complete
comparison_families = 6
permutations = 10000
failed_checks = 0
```

Every Phase 10 check must pass, and every artifact record must match its
stored path, byte count, row count, schema, and SHA-256. The Phase 10 check
schema does not distinguish blocking from informational rows.

### Required Phase 11 inputs

```text
results/minerva_production/11_pathway/pathway_status.tsv
results/minerva_production/11_pathway/pathway_checks.tsv
results/minerva_production/11_pathway/pathway_artifacts.tsv
results/minerva_production/11_pathway/pathway_reference_manifest.tsv
results/minerva_production/11_pathway/pathway_query_manifest.tsv
results/minerva_production/11_pathway/downstream_panel_manifest.tsv
results/minerva_production/11_pathway/similarity_panel_data.tsv.gz
results/minerva_production/11_pathway/pathway_panel_data.tsv.gz
results/minerva_production/11_pathway/similarity_tail_pathway_ora.tsv.gz
```

The required production conditions are:

```text
schema_version = mitochondrial_pathway_status_v1
validation_status = validated_complete
comparison_families = 6
downstream_panel_definitions = 27
similarity_panel_rows = 3780
pathway_panel_rows = 75411
ora_rows = 102336
query_families = 24
failed_checks = 0
```

Every blocking Phase 11 check must pass. All Phase 11 artifacts must match
their stored size, row count, schema, and SHA-256. The reference manifest must
identify Human MSigDB C2:CP v2026.1.Hs with the exact checksum already frozen
by Phase 11.

### Required figure configuration

Create:

```text
config/yu_mitochondrial_figures_3_to_6.yml
```

It will freeze at minimum:

- input root `results/minerva_production`;
- output root `results/figures/figures03_to_06`;
- primary profile, universe, and pathway collection;
- Figure 3–6 comparison, panel, tail, and requested-rank-set mapping;
- nine validated state-pair columns, eight displayed columns, group colors,
  and order;
- pathway FDR threshold `0.05` and display cap `15`;
- the display rule `tested + overlap_count > 0`, ordered by stored
  `statistical_order`;
- row-label and pathway-label wrapping rules;
- titles, output filenames, dimensions, DPI, and graphics devices;
- color palettes and common theme settings;
- expected upstream schemas;
- expected figure-output table schemas; and
- whether optional sensitivity outputs are enabled, default `false`.

The configuration controls presentation only. It must not expose options to
change scores, ranks, queries, ORA values, or BH families.

### Required software

The local implementation may use only already available packages:

- `data.table` for input, validation, and companion tables;
- `ggplot2` for heatmaps and dot plots;
- `patchwork` for assembly;
- `scales` for axis and legend formatting;
- `yaml` for the frozen figure configuration; and
- `digest` or system `sha256sum` for provenance hashes.

No package may be installed dynamically by the figure script. If
implementation introduces a new package, it must be justified and pinned in
`renv.lock` before the final run. The current design does not require one.

### Explicit non-inputs

The figure workflow must not read:

- Phase 05 normalized RDS files or status tables;
- Phase 07 pseudobulk, contrast-manifest, or DE results;
- Phase 08 MAST files;
- Phase 09 annotation files;
- Phase 10 result, rank-set, state-pair, or permutation tables directly;
- raw Seurat or expression data;
- Yu Supplemental Table S2 as a rank or significance oracle;
- the Yu PDF as a runtime data source;
- raw MSigDB or MitoCarta reference files;
- previously displayed pathway subsets; or
- an existing figure as a scientific input.

The Yu paper and the Phase 10/11 documentation are design references only.

## Construction workflow

### 1. Parse and validate the figure invocation

- require execution from the repository root or resolve it explicitly;
- accept `--config`, `--input-root`, `--output-root`, and `--dry-run`;
- default to the production and figure paths frozen above;
- reject unknown options and missing values;
- resolve all paths before any output is created; and
- print the exact four-figure mapping during a dry run.

The first implementation will remain a standalone downstream script. It will
not be registered as a `scripts/run_pipeline.R` task because it consumes an
already complete global production bundle, runs locally, and writes outside
the environment-specific scientific result tree.

### 2. Validate upstream bundles

- require the Phase 10 and Phase 11 status conditions above;
- require every Phase 10 check and every blocking Phase 11 check to pass;
- independently verify every artifact checksum and byte count;
- verify recorded row counts and schemas for the two panel-ready tables;
- require the Phase 11 status to reference the same Phase 10 status and
  artifacts found at the input root;
- require all six comparison IDs and all three downstream profiles;
- require all 27 downstream panel definitions; and
- stop before plotting if any provenance or schema condition fails.

### 3. Build deterministic panel-A display data

- filter `similarity_panel_data.tsv.gz` to `core_mito`;
- instantiate the 12 required comparison-by-tail blocks from the frozen map;
- require 25 selected features per tail for Figures 3–5;
- require 10 selected features per tail and APOE group for Figure 6;
- require exactly nine ordered state-pair rows per selected feature;
- preserve stored `tail_order`, `selection_order`, and `pair_order`;
- validate that counts are nonnegative integers;
- validate that state-pair counts sum to `paired_tests` for every feature;
- retain `(0,0)` for that reconciliation, then exclude it from plotted rows;
- build score, FDR-marker, and coverage display labels without changing true
  feature identity; and
- write the exact 1,680-row primary display table used by the plots.

### 4. Draw panel-A heatmaps

- create one heatmap for each Figure 3–5 comparison;
- create one heatmap block for each Figure 6 APOE group;
- show high and low tails as visibly separate row blocks;
- retain all eight score-contributing Same/Different/Opposite columns,
  including zero-count categories;
- use green, orange, and purple sequential scales for Same, Different, and
  Opposite with common limits per composite figure;
- label the three groups and ternary meanings clearly; and
- never derive a score, rank, FDR, or occurrence count during plotting.

### 5. Build deterministic panel-B display data

- instantiate all 12 `core_mito` high/low 200-gene queries from
  `pathway_query_manifest.tsv`;
- join each query to the complete Phase 11 ORA rows;
- apply only the frozen `tested`, positive-overlap, statistical-order, and
  15-pathway display rules;
- preserve one explicit record if a query has no positive-overlap pathway;
- record matched, FDR-significant, displayed, and omitted counts per query;
- validate every selected row against its source row and query sizes; and
- write a display table containing selected pathways plus explicit empty-query
  records.

### 6. Draw panel-B dot plots

- create separate high- and low-tail subplots for Figures 3–5;
- create paired high/low subplots for e2, e33, and e4 in Figure 6;
- use stored gene ratio, overlap count, and tail FDR directly;
- share scales within each composite figure;
- show an explicit text panel for every empty query; and
- distinguish FDR-significant filled points from nonsignificant open points.

### 7. Assemble figures and captions

- combine panels A and B with fixed tags and titles;
- combine Figure 6 APOE blocks in e2, e33, e4 order;
- generate the four captions from frozen templates plus observed query,
  background, coverage, significant, displayed, and omitted counts;
- ensure captions never overstate rank-tail or pathway significance; and
- write `figure_captions.md` before image publication.

### 8. Atomically export and inventory artifacts

- render each PDF and PNG to a process-specific temporary filename with the
  same final extension;
- verify the temporary artifact is nonempty and readable;
- rename it to the final path only after successful rendering;
- calculate file bytes and SHA-256 after publication;
- record dimensions, DPI, source comparisons, queries, and input hashes; and
- never leave a partial final image after an interrupted run.

If a complete figure status already exists with identical input, config, and
script hashes, an ordinary rerun will validate the bundle and exit without
redrawing. If those hashes differ, the script will stop rather than silently
replace the existing result; intentional regeneration must use an explicit
implementation-defined replacement option.

### 9. Validate and publish status last

- run all input, selection, panel, image, caption, and provenance checks;
- write `figure_checks.tsv` with blocking flags and observed values;
- write `figure_manifest.tsv` with one row per final PDF or PNG;
- write `figure_status.tsv` only after every blocking check passes; and
- use `validated_complete` only for a complete production rendering.

## Outputs and files created

Create the following under:

```text
results/figures/figures03_to_06/
```

### Primary image files

```text
figure03_mitochondrial_yu_analogue.pdf
figure03_mitochondrial_yu_analogue.png
figure04_mitochondrial_yu_analogue.pdf
figure04_mitochondrial_yu_analogue.png
figure05_mitochondrial_yu_analogue.pdf
figure05_mitochondrial_yu_analogue.png
figure06_mitochondrial_yu_analogue.pdf
figure06_mitochondrial_yu_analogue.png
```

### Companion and validation files

| File | Contents |
|---|---|
| `displayed_similarity_data.tsv.gz` | Exact 1,680 primary panel-A rows with plot order, color group, and rendered labels. |
| `displayed_pathway_data.tsv.gz` | Exact displayed matched-pathway rows, FDR significance flags, and display ranks. |
| `pathway_display_summary.tsv` | One row per required query with query/background size and matched/significant/displayed/omitted counts. |
| `figure_captions.md` | Final caption for each of the four primary figures. |
| `figure_manifest.tsv` | One row per PDF/PNG with source IDs, dimensions, DPI, bytes, hashes, package versions, and validation status. |
| `figure_checks.tsv` | Blocking and informational input, selection, plotting, artifact, and provenance checks. |
| `figure_status.tsv` | One terminal figure-generation status row with input/config/script hashes, counts, versions, timing, and validation status. |

Use versioned schemas:

```text
yu_mitochondrial_displayed_similarity_v2
yu_mitochondrial_displayed_pathway_v2
yu_mitochondrial_pathway_display_summary_v2
yu_mitochondrial_figure_manifest_v2
yu_mitochondrial_figure_checks_v2
yu_mitochondrial_figure_status_v2
```

No new figure or companion table may be written beneath
`results/minerva_production/`.

## Files added or changed during implementation

### New files

| File | Required content |
|---|---|
| `config/yu_mitochondrial_figures_3_to_6.yml` | Frozen figure mapping, primary profile, state-pair display, pathway cap, titles, styling, export settings, and schemas. |
| `scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R` | Input validation, deterministic display selection, panel construction, assembly, atomic exports, checks, manifests, and status. |
| `docs/figures/similar_to_yu_figures_3_to_6_plan.md` | This implementation and execution plan. |

### Existing files that remain unchanged

- `scripts/run_pipeline.R` and all registered Phase 00–11 tasks;
- all Phase 00–11 scientific scripts and configs;
- every file under `results/minerva_production/`;
- Phase 10 and Phase 11 plan documents and figure guides;
- the Yu paper and supplemental files;
- normalized RDS files and raw expression inputs; and
- `renv.lock`, unless implementation demonstrably requires a new package.

## Local production execution

### Inputs

```text
results/minerva_production/10_similarity/
results/minerva_production/11_pathway/
config/yu_mitochondrial_figures_3_to_6.yml
```

### Output

```text
results/figures/figures03_to_06/
```

### Preflight

Run from the repository root:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

test -r results/minerva_production/10_similarity/similarity_status.tsv
test -r results/minerva_production/10_similarity/similarity_checks.tsv
test -r results/minerva_production/10_similarity/similarity_artifacts.tsv
test -r results/minerva_production/11_pathway/pathway_status.tsv
test -r results/minerva_production/11_pathway/pathway_checks.tsv
test -r results/minerva_production/11_pathway/pathway_artifacts.tsv
test -r results/minerva_production/11_pathway/pathway_query_manifest.tsv
test -r results/minerva_production/11_pathway/downstream_panel_manifest.tsv
test -r results/minerva_production/11_pathway/similarity_panel_data.tsv.gz
test -r results/minerva_production/11_pathway/pathway_panel_data.tsv.gz
test -r results/minerva_production/11_pathway/similarity_tail_pathway_ora.tsv.gz
test -r config/yu_mitochondrial_figures_3_to_6.yml

Rscript -e '
required <- c(
  "data.table", "ggplot2", "patchwork",
  "scales", "yaml", "digest"
)
stopifnot(all(vapply(required, requireNamespace,
                     logical(1), quietly = TRUE)))
stopifnot(capabilities("cairo"), capabilities("png"))

library(data.table)
sim <- fread(
  "results/minerva_production/10_similarity/similarity_status.tsv"
)
path <- fread(
  "results/minerva_production/11_pathway/pathway_status.tsv"
)
sim_checks <- fread(
  "results/minerva_production/10_similarity/similarity_checks.tsv"
)
path_checks <- fread(
  "results/minerva_production/11_pathway/pathway_checks.tsv"
)

stopifnot(
  sim$schema_version == "mitochondrial_similarity_status_v1",
  sim$validation_status == "validated_complete",
  sim$permutations == 10000L,
  path$schema_version == "mitochondrial_pathway_status_v1",
  path$validation_status == "validated_complete",
  all(sim_checks$passed),
  all(path_checks$passed[path_checks$blocking])
)
cat("Validated Phase 10/11 production inputs are ready locally\n")
'
```

The figure script repeats these checks and performs the authoritative hash,
schema, key, row-count, and panel-definition validations.

### Dry run

```bash
Rscript scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R \
  --config config/yu_mitochondrial_figures_3_to_6.yml \
  --input-root results/minerva_production \
  --output-root results/figures/figures03_to_06 \
  --dry-run
```

The dry run must:

- validate all inputs without writing final artifacts;
- report the 12 panel-A tail blocks and 12 panel-B queries;
- report 1,680 selected panel-A rows;
- report the matched/significant/displayed baseline by panel-B query;
- report four planned PDF and four planned PNG paths; and
- confirm that no Phase 05 or Phase 07 path is resolved.

### Execute

```bash
Rscript scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R \
  --config config/yu_mitochondrial_figures_3_to_6.yml \
  --input-root results/minerva_production \
  --output-root results/figures/figures03_to_06
```

### Validate

```bash
Rscript -e '
library(data.table)
root <- "results/figures/figures03_to_06"
status <- fread(file.path(root, "figure_status.tsv"))
checks <- fread(file.path(root, "figure_checks.tsv"))
manifest <- fread(file.path(root, "figure_manifest.tsv"))
sim_display <- fread(file.path(root, "displayed_similarity_data.tsv.gz"))
path_summary <- fread(file.path(root, "pathway_display_summary.tsv"))

stopifnot(
  status$schema_version == "yu_mitochondrial_figure_status_v2",
  status$validation_status == "validated_complete",
  all(checks$passed[checks$blocking]),
  nrow(manifest) == 8L,
  all(manifest$validation_status == "validated_complete"),
  all(file.exists(manifest$artifact_path)),
  nrow(sim_display) == 1680L,
  nrow(path_summary) == 12L,
  sum(manifest$format == "pdf") == 4L,
  sum(manifest$format == "png") == 4L
)
cat("Figure bundle validated successfully\n")
'

pdfinfo results/figures/figures03_to_06/figure03_mitochondrial_yu_analogue.pdf
file results/figures/figures03_to_06/figure03_mitochondrial_yu_analogue.png
```

Repeat the PDF and PNG inspection for Figures 4–6. Automated checks establish
structure and provenance; the final review must also inspect each rendered
figure at normal manuscript zoom for clipped labels and unreadable text.

## Required scientific and provenance checks

### Input checks

- Phase 10 and Phase 11 statuses are `validated_complete`.
- Every Phase 10 check and every blocking Phase 11 check passes.
- Every upstream artifact matches its recorded hash and byte count.
- Phase 11 provenance resolves to the current Phase 10 bundle.
- The two panel-ready schemas and required columns match exactly.
- Six comparison IDs and all 27 downstream panel definitions are present.
- The primary profile maps only to `core_mito × msigdb_c2_cp_v2026_1`.

### Panel-A checks

- Figures 3–5 each contain exactly 25 high and 25 low features.
- Figure 6 contains exactly 10 high and 10 low features for each APOE group.
- Every selected feature has exactly nine validated source state-pair rows and
  eight displayed rows.
- The final primary display table contains exactly 1,680 rows.
- Feature, tail, and pair orders reproduce stored Phase 11 order fields.
- State-pair counts are nonnegative and sum to `paired_tests` per feature.
- Zero-count categories remain visible within Same, Different, and Opposite.
- `(0,0)` is excluded only after nine-cell count reconciliation.
- No feature is removed by a post-selection FDR filter.
- Stored display labels, scores, FDR values, and coverage are unchanged.

### Panel-B checks

- Exactly 12 primary query facets are instantiated from the query manifest.
- Figures 3–6 use both high- and low-score 200-gene queries.
- Every displayed point has `test_status == "tested"` and
  `overlap_count > 0`.
- Every displayed order reproduces stored `statistical_order`.
- No query displays more than 15 pathways.
- Matched, displayed, and omitted counts reconcile exactly.
- Stored `tail_fdr_bh < 0.05` flags exactly determine filled versus open
  points.
- High-score facets remain populated even when their FDR-significant count is
  zero.
- Plotted x, size, and color values reproduce stored gene ratio, overlap, and
  tail FDR.
- No P value or FDR is recalculated.

### Artifact and provenance checks

- Four primary PDFs and four primary PNGs exist and are nonempty.
- Each PDF opens and contains exactly one page.
- PNG dimensions and DPI match the recorded export settings.
- Every image has a matching manifest row, byte count, and SHA-256.
- Captions exist for all four figures and contain all required disclosures.
- No new artifact is written beneath a Phase 10 or Phase 11 directory.
- The status records upstream status/panel-data hashes and the figure config
  and script hashes.
- A rerun with identical hashes validates and exits without changing the
  completed bundle.

### Visual review checks

- All gene labels are readable at normal manuscript zoom.
- No score, coverage, pathway, axis, facet, or legend label is clipped.
- High- and low-similarity blocks are visually distinct.
- Same, Different, and Opposite state blocks and their green, orange, and
  purple legends are clear.
- Open nonsignificant points cannot be mistaken for FDR-significant
  enrichment.
- Figure 6 e2, e33, and e4 blocks are in the frozen order.
- Color palettes remain interpretable in grayscale and for common forms of
  color-vision deficiency.
- Figure titles and captions consistently call the outputs mitochondrial
  analogues rather than reproductions.

## Acceptance criteria

### Structural gate

- The script is under `scripts/figures/`.
- All outputs are under `results/figures/figures03_to_06/`.
- The required eight primary images and seven companion files exist.
- All versioned schemas, required columns, and keys validate.
- No earlier-phase file is modified.

### Scientific gate

- Only validated Phase 10/11 production handoffs are scientific inputs.
- Primary figures use only `core_mito` and C2:CP v2026.1.Hs.
- Panel A uses stored occurrence counts, score ranks, FDR, and coverage.
- Panel B uses stored ORA ratios, overlap, FDR, and statistical order.
- Figure 6 uses both high- and low-score pathway tails.
- Nonsignificant pathway matches remain explicit and are not described as
  enriched.
- Captions accurately disclose the mitochondrial universe, missingness,
  pathway background, reference release, and FDR scope.

### Figure and provenance gate

- Four legible one-page PDF composites and matching 300-dpi PNGs pass visual
  review.
- Every displayed row can be traced to one Phase 11 source row.
- Every image can be traced to exact Phase 10/11, config, and script hashes.
- All blocking `figure_checks.tsv` rows pass.
- `figure_status.tsv` is published last with `validated_complete`.

## Downstream handoff

The four primary PDFs are the manuscript-ready outputs. PNGs are review and
presentation copies. `displayed_similarity_data.tsv.gz`,
`displayed_pathway_data.tsv.gz`, and `pathway_display_summary.tsv` provide the
exact data shown and allow captions or manuscript text to be audited without
rerunning the figure code.

After the primary figures are frozen, the same script may optionally produce
separately labeled sensitivity figures for:

```text
focused_mitopathways
inclusive_yu_sensitivity
occurrence_fraction
```

Those products must use distinct filenames and manifest profile fields. They
are not permitted to replace or silently alter the primary figures.

## Completion criteria

The figure workflow is complete when:

- the standalone figure script and figure config are implemented;
- the local dry run validates the production handoff;
- Figures 3–6 are exported as four PDF and four PNG files under
  `results/figures/figures03_to_06/`;
- panel-A and panel-B display selections match the frozen rules;
- high- and low-tail pathway matches are retained regardless of FDR;
- captions and companion tables are complete;
- all automated and visual checks pass;
- every artifact and input is hashed in the figure manifest; and
- the final figure status is `validated_complete`.

## Implementation checklist

### Implement

- [x] Add `config/yu_mitochondrial_figures_3_to_6.yml`.
- [x] Add `scripts/figures/generate_yu_mitochondrial_figures_3_to_6.R`.
- [x] Implement strict CLI and dry-run behavior.
- [x] Implement upstream status, check, schema, artifact, and hash validation.
- [x] Implement deterministic panel-A selection and occurrence heatmaps.
- [x] Implement deterministic panel-B matched-pathway selection for both tails.
- [x] Implement Figure 3–6 assembly and caption templates.
- [x] Implement atomic Cairo PDF/PNG export.
- [x] Implement displayed-data, summary, check, manifest, and status tables.
- [x] Implement identical-input resumability and changed-input refusal.

### Execute locally

- [x] Run the production preflight.
- [x] Run the figure-workflow dry run.
- [x] Confirm no Phase 05 or Phase 07 path is resolved.
- [x] Generate the four PDF and four PNG primary figures.
- [x] Run the independent validation command.
- [x] Inspect every PDF and PNG for legibility and clipping.
- [x] Confirm all eight image hashes match the manifest.

### Finalize

- [x] Freeze final dimensions and any presentation-only config adjustments.
- [x] Confirm all high-score pathway facets show the top stored matches and
  mark their zero FDR-significant counts with open points.
- [x] Confirm captions disclose all universe, coverage, background, release,
  and FDR details.
- [x] Confirm no prior-phase result changed.
- [x] Publish `figure_status.tsv` as `validated_complete`.
