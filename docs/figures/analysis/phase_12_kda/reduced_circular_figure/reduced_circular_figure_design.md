# Phase 12 KDA Figure A design: reduced circular cross-network overview

## Status and purpose

This document specifies the replacement for the current eight-track circular
figure:

```text
results/figures/analysis/phase12_kda/circular_figure/phase12_kda_circular.png
```

Figure A is an overview of network-level key-driver ranking and cross-network
recurrence. It is not intended to show every Phase 12 summary statistic or the
sex/APOE-specific pattern. Those comparisons belong in Figure B, specified in
[`phase_12_kda_panel_b_sex_apoe_dot_heatmap_design.md`](phase_12_kda_panel_b_sex_apoe_dot_heatmap_design.md).

The figure should answer one question:

> Which key drivers have the strongest consistent KDA evidence within each
> broad network, and which selected drivers recur across networks?

## Bottom-line design

Retain the circular layout, but reduce it to:

1. a thin outer network band;
2. one quantitative MeanOfLog score ring;
3. driver labels; and
4. low-opacity center links connecting the same driver across networks.

The center should contain a compact legend inside an opaque white disk. No
other quantitative rings should be drawn.

## Why the current figure needs simplification

The current figure displays eight tracks: `R`, `T`, `P`, `S`, `C`, `G`, `Q`,
and `FE`. Inspection of the 35 plotted network-driver rows shows that:

- total recurrence correlates approximately 0.96 with both primary and pooled
  recurrence;
- eligible fine-cell-type coverage equals 1.0 for 34 of 35 rows;
- 25 of 35 global-call fractions are exactly 0 or 1;
- the adjusted-P ring shows the single smallest adjusted P value rather than
  cross-run consistency; and
- the fold-enrichment ring shows a maximum that can be driven by a small query
  or neighborhood.

The 35 displayed rows represent only 15 unique genes, and 28 of the 35 rows
are mtDNA-prefixed genes. Thus, the unfiltered overview is predominantly a
recurrent respiratory-chain sentinel view. It should not visually imply that
all displayed structural mitochondrial genes are upstream causal regulators.

The biological interpretation and the reasons to distinguish recurrent
sentinels from putative upstream candidates are documented in
[`phase12_driver_gene_discussion.md`](phase12_driver_gene_discussion.md).

## Statistical ranking requirement

### Primary score

Within broad network \(n\), calculate the MeanOfLog score for candidate driver
\(g\) across the relevant KDA runs:

\[
S_{n,g} = \frac{1}{K_{n,g}}
\sum_{r=1}^{K_{n,g}} -\log_{10}(p_{n,g,r}).
\]

Standardize within broad network:

\[
S^{\mathrm{std}}_{n,g} =
\frac{S_{n,g}}{\max_g S_{n,g}}.
\]

Use `mean_of_log_score_standardized` for ordering and radial bar height. The
base of the logarithm changes the reported numeric scale but not the ordering;
base 10 is preferred because it is easier to explain in the legend and caption.

### Runs included in the primary score

Use only eligible primary directional analyses:

```text
analysis_tier == "primary"
signature_direction in {"AD_up_mito", "AD_down_mito"}
eligibility_status == "eligible"
```

Do not include:

- secondary pooled signatures; or
- the derived `AD_both_mito` signature.

The excluded analyses reuse primary information and would double-count
overlapping signatures in the main ranking.

### Complete P-value matrix requirement

Do not calculate MeanOfLog from `kda_results.tsv` or
`kda_key_driver_summary.tsv`. Both contain only significant results or
significant-result summaries. A score computed from them would omit
nonsignificant tests and favor candidates according to which rows survived
filtering.

The Phase 12 workflow must export a pre-FDR candidate-test table before the
line in `scripts/NetWeaver/fKDA.R` that filters to `adj.P.Value <= fdr`.
Recommended output:

```text
results/minerva_production/12_kda/kda_candidate_tests.tsv.gz
```

At minimum it should contain:

```text
schema_version
kda_run_id
analysis_tier
fine_cell_type
broad_network
signature_group
signature_direction
key_driver
raw_log_p_value
raw_p_value
adjusted_p_value
overlap_count
neighborhood_size
signature_size
tested_candidate
```

Zero-overlap candidates evaluated by KDA should retain \(p=1\). A candidate
that was genuinely not tested should remain missing unless an explicit audit
shows that absence is mathematically equivalent to a zero-overlap test. The
aggregation table must report `ranking_runs` and `eligible_directional_runs`
so score coverage is visible and auditable.

This requirement follows the ranking recommendation in
[`email_08042026_circular_figure_sort_order.md`](../../email_notes/email_08042026_circular_figure_sort_order.md).

## Driver selection

### Networks

Display the seven broad networks with eligible, significant Phase 12 KDA
results:

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons
4. Microglia
5. OPCs
6. Oligodendrocytes
7. Vasculature

CAMs and T cells should not receive empty sectors. State in the caption that
they had no eligible KDA runs; their absence is not a negative KDA result.

### Number of drivers

Display the top three drivers per broad network after MeanOfLog ranking:

```text
7 networks x 3 drivers = at most 21 network-driver sectors
```

Three per network is preferred over the current five because it preserves
representation of smaller networks while keeping labels and center links
readable at journal size.

### Deterministic selection order

Within each broad network, order candidates by:

1. decreasing `mean_of_log_score_standardized`;
2. decreasing `ranking_runs` or ranking coverage;
3. decreasing primary directional significant-run fraction; and
4. alphabetical `key_driver`.

The primary directional recurrence fraction is a tie-breaker and an exported
annotation, not a second ring.

Do not force a previously highlighted gene into Figure A if it falls outside
the prespecified selection. Mechanistically important nuclear candidates are
handled in Figure B.

## Figure geometry

### Canvas

- Target a double-column figure width of 178-183 mm.
- Use an approximately square canvas, initially 7.1 x 7.1 inches.
- Design and inspect the figure at final print size, not only as a 3600-pixel
  screen image.
- Keep at least 8-10 mm of clear margin around all radial labels.

### Sector order and spacing

Use the network order listed above, clockwise from 12 o'clock. Within a
network, arrange the three drivers in decreasing MeanOfLog order.

Use:

- a visibly larger angular gap between networks; and
- a narrow gap between drivers belonging to the same network.

Suggested starting values are 4-6 degrees between networks and approximately
1 degree between drivers, to be refined at final print size.

All driver sectors should have equal angular width. Sector width must not
encode score, recurrence, network size, or number of eligible runs.

### Outer network band

Draw a thin categorical band outside the score ring. Color it by broad
network. The band should be thick enough to group adjacent driver sectors but
should not resemble an additional quantitative track.

Place the network name once above or outside the midpoint of each network
block. Do not require the reader to infer network identity solely from the
legend.

### MeanOfLog score ring

Draw one radial bar per network-driver sector:

```text
bar height = mean_of_log_score_standardized
range = 0 to 1
```

Use a single neutral dark color for all score bars, such as dark navy or dark
slate. Do not color score bars by network; network identity is already encoded
by the outer band.

Use a pale neutral background track and subtle reference circles at 0.25,
0.50, 0.75, and 1.00. Label only 0, 0.5, and 1.0 in the center legend or at one
unobtrusive radial axis.

### Driver labels

- Place one gene symbol outside each driver sector.
- Use black text for nuclear-encoded candidates.
- Use medium gray text or a small gray dot for mtDNA-encoded drivers.
- Use the same font style for all gene symbols; do not use color to imply
  direction, significance, or causality.
- Automatically flip labels in the lower half of the circle so every label is
  upright.
- Do not color every label by network.

The mtDNA marker is a biological interpretation aid, not a significance
encoding. Its legend text should read `mtDNA-encoded sentinel candidate`.

### Cross-network links

Connect repeated selected genes across broad networks with thin gray curves.
The link means only:

> The same gene was selected in more than one broad network.

It must not be described as a Bayesian-network edge or an interaction between
cell classes.

To control clutter:

- draw one bundled link structure per repeated gene rather than every possible
  pairwise connection;
- use line width no greater than approximately 0.5-0.8 pt at final size;
- use 15-25% opacity;
- draw links beneath the central legend disk; and
- do not encode score with link width or color.

If multiple link geometries are possible, connect each repeated gene's
highest-scoring sector to its other occurrences. This yields \(m-1\) curves
for a gene appearing in \(m\) networks rather than \(m(m-1)/2\) curves.

### Center legend

Reserve an opaque white center disk large enough for a compact, four-item
legend. The legend should explain:

1. colored outer band = broad network;
2. radial bar height = standardized mean \(-\log_{10}p\);
3. gray curve = same selected driver in another network; and
4. gray gene marker = mtDNA-encoded sentinel candidate.

Do not place the figure title, driver count, track abbreviations, or a second
paragraph of explanatory text in the center.

## Color and typography

### Network colors

Retain the current Okabe-Ito-style network colors if possible:

| Network | Color |
|---|---|
| Astrocytes | `#009E73` |
| Excitatory neurons | `#E69F00` |
| Inhibitory neurons | `#0072B2` |
| Microglia | `#CC79A7` |
| OPCs | `#56B4E9` |
| Oligodendrocytes | `#F0E442` |
| Vasculature | `#D55E00` |

Use these colors only for the thin network band and its compact legend. All
other elements should be neutral navy, gray, black, or white. This removes the
current competition among network colors, primary/pooled colors, and the
yellow-orange-red heat scale.

### Typography

- Sans-serif font throughout, preferably Arial or Helvetica.
- Figure title: 10-12 pt at final size.
- Network labels: 8-9 pt, semibold.
- Driver labels: at least 7 pt.
- Center legend and numeric references: at least 7 pt.
- Sentence case throughout.

Suggested title:

> Recurrent mitochondrial KDA evidence across brain cell networks

Suggested subtitle, only if space permits:

> Drivers ranked within network by standardized mean negative log KDA P value

## Elements explicitly removed from Figure A

The following current elements should not appear as circular rings:

| Current element | Disposition |
|---|---|
| `R`, all-run recurrence | Exported annotation or tie-breaker only |
| `T`, primary/pooled composition | Remove from main figure |
| `P`, primary recurrence | Exported annotation; Figure B uses directional recurrence |
| `S`, pooled recurrence | Supplement only |
| `C`, fine-cell-type coverage | Remove; nearly saturated in current selection |
| `G`, global-call fraction | Supplementary table or optional label-side glyph |
| `Q`, minimum adjusted-P strength | Replace with MeanOfLog |
| `FE`, maximum fold enrichment | Supplementary table only |

Do not reuse the current `R`, `T`, `P`, `S`, `C`, `G`, `Q`, or `FE` track-key
abbreviations.

## Required plotted-data output

Write a plotted-data table beside the figure. Recommended filename:

```text
results/figures/analysis/phase12_kda/reduced_circular_figure/
  phase12_kda_figure_a_circular_plotted_data.tsv
```

Required fields:

```text
schema_version
broad_network
network_display_order
key_driver
driver_display_order_within_network
mean_of_log_score
mean_of_log_score_standardized
ranking_runs
eligible_directional_runs
ranking_coverage_fraction
primary_directional_significant_runs
primary_directional_recurrence_fraction
mtDNA_encoded
selected_network_count
network_color
selection_rule
```

The figure script must plot stored values from this table and must not derive
the ranking from significant-only data during rendering.

## Suggested caption

> **Cross-network overview of mitochondrial key-driver evidence.** Within each
> broad brain-cell network, candidate drivers were ranked by the standardized
> mean negative log KDA P value across eligible primary directional
> mitochondrial signatures (`AD_up_mito` and `AD_down_mito`). Secondary pooled
> and combined-direction signatures were excluded to avoid double-counting
> overlapping inputs. The three highest-ranked candidates per network are
> shown. Outer colors identify broad networks, radial bar height represents the
> standardized MeanOfLog score, and gray center links connect repeated
> selections of the same gene across networks; links are not network edges.
> Gray-marked labels denote mtDNA-encoded candidates, which are interpreted as
> recurrent respiratory-chain sentinels rather than automatically as upstream
> causal regulators. CAMs and T cells had no eligible KDA runs.

## Validation and acceptance criteria

### Data validation

- [ ] The complete pre-FDR candidate-test table exists and has a documented
      schema.
- [ ] MeanOfLog is calculated from eligible primary directional runs only.
- [ ] Secondary pools and `AD_both_mito` are absent from the ranking input.
- [ ] Every displayed score reconciles with the underlying run-level table.
- [ ] `ranking_runs`, eligible runs, and missing-test handling are explicit.
- [ ] Exactly the top three candidates per result-producing network are drawn,
      subject only to documented ties.
- [ ] CAMs and T cells are not represented as zero-result sectors.

### Visual validation

- [ ] Only one quantitative circular ring is present.
- [ ] Network identity is readable without consulting color alone.
- [ ] All gene labels are upright and at least 7 pt at final size.
- [ ] Center links remain subordinate to score bars and labels.
- [ ] The center legend is readable and does not overlap visible links.
- [ ] The figure remains interpretable in grayscale.
- [ ] No red-green comparison is required.

### Export validation

- [ ] Export vector PDF and SVG versions.
- [ ] Export a PNG preview at 300-600 dpi.
- [ ] Use embedded fonts or convert text safely according to journal policy.
- [ ] Verify the vector file at the intended 178-183 mm width.
- [ ] Keep the plotted-data TSV and figure-generation log beside the outputs.

## References informing the design

- Professor's ranking interpretation and required matrix caveat:
  [`email_08042026_circular_figure_sort_order.md`](../../email_notes/email_08042026_circular_figure_sort_order.md)
- Current figure construction:
  [`phase_12_kda_circular_figure_plan.md`](phase_12_kda_circular_figure_plan.md)
- Biological interpretation and conservative prioritization:
  [`phase12_driver_gene_discussion.md`](phase12_driver_gene_discussion.md)
- Wang KDP ranking implementation:
  [PHG_protein_bnGlobalKDA_ranking.R](https://github.com/wange230/proteomics_networks/blob/main/codes/Baysian_network/KDA_analysis/PHG_protein_bnGlobalKDA_ranking.R)
- NetWeaver MeanOfLog implementation:
  [ensemble.rank.R](https://github.com/mw201608/NetWeaver/blob/master/R/ensemble.rank.R)
- Circular-layout rationale:
  [Circos](https://pmc.ncbi.nlm.nih.gov/articles/PMC2752132/) and
  [circlize](https://academic.oup.com/bioinformatics/article/30/19/2811/2422259)

## Implementation and generated artifacts (2026-08-09)

The design was implemented in the same script and output directory pattern as
the original Phase 12 circular figure.

Primary figure script:

```text
scripts/figures/analysis/phease12_kda/
  visualize_phase12_kda_reduced_circular.R
```

Shared preparation and helper scripts:

```text
scripts/figures/analysis/phease12_kda/
  prepare_phase12_kda_figure_data.R
  phase12_kda_figure_common.R
```

Generated Panel A files:

```text
results/figures/analysis/phase12_kda/reduced_circular_figure/
  phase12_kda_reduced_circular.png
  phase12_kda_reduced_circular.pdf
  phase12_kda_reduced_circular.svg
  phase12_kda_reduced_circular_plotted_data.tsv
  phase12_kda_reduced_circular_generation_log.tsv
```

The implemented panel contains 21 network-driver sectors: exactly three for
each of the seven broad networks with eligible primary directional KDA runs.
They represent 10 unique drivers. The plotted-data table stores the complete
selection, ranking coverage, standardized MeanOfLog scores, sector angles,
network colors, and recurrence-link counts.

The complete candidate matrix was reconstructed from the frozen Phase 12 fKDA
implementation, validated inputs, network neighborhoods, effective
backgrounds, and run manifest. Every archived significant-result row was
reproduced exactly for all 295 eligible primary directional runs. A candidate
present in a run's effective background but absent from the explicit
three-layer target set has zero overlap by construction and is retained with
P = 1; a candidate absent from the effective background remains missing. This
rule and the per-run reconciliation are exported beside the figure.

Visual inspection was performed on the 7.1 x 7.1 inch, 450-dpi PNG after
rendering. The final version has one quantitative ring, upright radial labels,
direct network text labels, a white center legend, and color-independent
network identification.
