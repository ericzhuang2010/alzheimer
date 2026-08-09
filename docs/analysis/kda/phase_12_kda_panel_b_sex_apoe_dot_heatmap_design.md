# Phase 12 KDA Figure B design: sex/APOE directional dot heatmap

## Status and purpose

This document specifies the focused sex/APOE figure that accompanies the
reduced circular overview in
[`phase_12_kda_panel_a_reduced_circular_figure_design.md`](phase_12_kda_panel_a_reduced_circular_figure_design.md).

Figure B should answer:

> In which sex/APOE strata and AD-associated mitochondrial directions are the
> prioritized, biologically interpretable key-driver candidates supported?

It should not imply that descriptive differences among strata are formal
AD-by-sex, AD-by-APOE, or three-way interactions.

## Bottom-line design

Create one rectangular figure with two aligned dot-heatmap facets:

1. `AD-up mitochondrial signature`; and
2. `AD-down mitochondrial signature`.

Each facet has the same rows and the same six sex/APOE columns:

```text
                 Female                         Male
             e2    e3/3    e4              e2    e3/3    e4

AD-up        dots showing strength and recurrence
AD-down      dots showing strength and recurrence
```

Use:

- dot color for mean negative log KDA P value;
- dot area for significant-run recurrence;
- row grouping for broad network; and
- a small right-side bar for the overall standardized MeanOfLog ranking score.

Do not wrap these comparisons into additional circular rings.

## Scientific framing

The unfiltered Phase 12 recurrence results are dominated by mtDNA-encoded and
structural OXPHOS candidates. Those findings support a recurrent respiratory
sentinel core but do not automatically identify tractable upstream regulators.

Figure B should focus on the nuclear, query-independent candidates emerging
from the conservative interpretation described in
[`phase12_driver_gene_discussion.md`](phase12_driver_gene_discussion.md).
Examples include:

```text
RPL11
RPS15
WDR82
LAMTOR5
SELENOW
GABARAPL2
TMEM147
BEX3
APOE
FTL
ANKRD11
SLC11A1
HSPA1A
PARK7
```

This list defines a prespecified candidate pool for figure preparation, not a
guarantee that every gene will be displayed. Final row eligibility and order
must follow the rules below after the complete MeanOfLog matrix has been
constructed.

## Input analyses

### Included analyses

Use only KDA runs satisfying:

```text
analysis_tier == "primary"
signature_direction in {"AD_up_mito", "AD_down_mito"}
eligibility_status == "eligible"
signature_group in {"F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"}
```

### Excluded analyses

Exclude:

- all secondary pooled signatures; and
- `AD_both_mito`.

The pooled signatures reuse primary data, and `AD_both_mito` is a derived
union of the directional signatures. Including them would duplicate evidence
and obscure the sex/APOE-direction structure that Figure B is meant to show.

## Complete P-value matrix requirement

Figure B requires the same pre-FDR candidate-test table specified for Figure A:

```text
results/minerva_production/12_kda/kda_candidate_tests.tsv.gz
```

Do not compute group-specific mean negative log P values from
`kda_results.tsv`. That table includes only significant candidates. Averaging
only its rows would convert significance filtering into a biased score.

The pre-FDR output must preserve:

- every candidate evaluated in each eligible run;
- raw log P values before numerical exponentiation;
- raw P values where representable;
- adjusted P values for individual-run significance calls;
- zero-overlap evaluated candidates with \(p=1\); and
- explicit missingness for candidates that were not tested.

Use the stored raw log P value to avoid numeric underflow:

\[
-\log_{10}(p) = \frac{-\log(p)}{\log(10)}.
\]

Missing tests must not be silently converted to \(p=1\). If an audit proves
that a candidate outside the returned target set is mathematically equivalent
to a tested zero-overlap candidate, document that rule and apply it before
aggregation.

## Candidate-row eligibility and selection

### Conservative evidence definition

For interpretive prioritization, a significant result row is conservative if:

1. it comes from a primary run;
2. direction is `AD_up_mito` or `AD_down_mito`;
3. the driver is not mtDNA encoded;
4. the driver is not a member of that run's effective query;
5. `overlap_count >= 2`; and
6. `signature_size >= 10`.

This is a robustness screen, not a new P-value or FDR procedure.

### Display candidate pool

Start from the prespecified highlighted-gene pool above. Expand each gene into
a network-driver row only in networks where it has at least one primary
directional significant result and sufficient complete-matrix ranking
coverage.

For the main Figure B:

- retain network-driver rows with at least one conservative result;
- target 12-20 displayed rows;
- cap at three rows per broad network if more than 20 rows qualify; and
- if a cap is required, retain rows by decreasing overall standardized
  MeanOfLog score, then conservative fine-cell-type coverage, then gene symbol.

`PARK7` should appear only if it satisfies the same final evidence rule. Its
biological interest alone should not override a failed conservative screen.

Do not add mtDNA genes merely because they rank highly. Their unfiltered
cross-network behavior belongs in Figure A and supplementary tables.

### Row ordering

Group rows in the same broad-network order used in Figure A:

1. Astrocytes
2. Excitatory neurons
3. Inhibitory neurons
4. Microglia
5. OPCs
6. Oligodendrocytes
7. Vasculature

Within each network, sort rows by:

1. decreasing overall `mean_of_log_score_standardized` across all eligible
   primary directional runs;
2. decreasing number of conservative directional fine cell types; and
3. alphabetical `key_driver`.

Keep exactly the same row order in the AD-up and AD-down facets. Do not cluster
rows or columns independently because that would disrupt direct comparison
between the two directions.

## Statistical summaries displayed

For each network-driver, signature group, and direction, define the following.

### Evidence strength shown by color

For the \(K\) tested candidate-run results in the cell:

\[
E = \frac{1}{K}\sum_{r=1}^{K}-\log_{10}(p_r).
\]

Display `mean_minus_log10_p` with one common color scale across both direction
facets. Do not standardize color separately by sex, APOE group, direction, or
facet; separate scales would make color comparisons invalid.

If a display cap is necessary, choose it before examining candidate identities,
for example from a documented high percentile of all eligible plotted cells.
Store both capped and uncapped values and state the cap in the legend and
caption.

### Recurrence shown by dot area

Define:

\[
R = \frac{\text{runs with within-run BH-adjusted }P\leq 0.05}
{\text{candidate runs tested}}.
\]

Map dot area, not radius, to `significant_run_fraction`. Suggested reference
sizes are 0%, 25%, 50%, 75%, and 100%.

For a tested cell with zero significant runs, draw a very small pale outlined
dot so it remains distinguishable from missing data.

### Missing and ineligible cells

Use three visually distinct states:

| State | Display |
|---|---|
| Tested, one or more significant runs | Filled dot; color and size encode values |
| Tested, zero significant runs | Small pale outlined dot |
| No eligible/tested candidate run | Light gray `x` or diagonally hatched cell |

Do not use a blank white cell for both a true zero and missingness.

### Overall ranking score shown at right

Add one narrow horizontal bar column at the right side of the heatmaps:

```text
bar length = overall mean_of_log_score_standardized
range = 0 to 1 within broad network
```

Use a neutral dark navy or slate bar. This column explains row order and links
Figure B to the Figure A ranking without introducing another color scale.

Optionally print `ranking_runs/eligible_directional_runs` as small text to the
right of the bar. Do not print individual P values inside heatmap cells.

## Figure layout

### Canvas

- Use a double-column width of 178-183 mm.
- Initial canvas target: approximately 7.1 inches wide by 5.5-7.0 inches high,
  depending on the final number of rows.
- Allocate approximately 42% of the heatmap width to each direction facet and
  10-16% to the overall-score bar and legends.
- Use enough row height to keep gene symbols at least 7 pt at final size.

If more than 20 network-driver rows pass the selection rule, do not shrink the
font below 7 pt. Move additional candidates to a supplementary dot heatmap.

### Direction facets

Place the two direction facets side by side:

```text
AD-up mitochondrial signature | AD-down mitochondrial signature
```

Use identical:

- row order;
- column order;
- dot-size scale;
- color scale; and
- cell dimensions.

The direction titles should be text headers, not red/blue facet colors.

### Sex/APOE columns

Within both facets, order columns as:

```text
Female: e2, e3/3, e4 | Male: e2, e3/3, e4
```

Use a two-level header:

- upper level: `Female` and `Male`;
- lower level: `e2`, `e3/3`, and `e4`.

Separate Female and Male blocks with a slightly wider vertical gap or a subtle
gray rule. Do not assign six categorical fill colors to the strata.

### Network grouping of rows

Use one narrow row-annotation strip colored by broad network. Also print the
network name at the start or midpoint of each row block so the figure remains
interpretable without color.

Insert a small horizontal gap or faint rule between network blocks. Do not put
a heavy grid around every cell.

### Legends

Place compact legends together at the right or bottom:

1. color: `Mean -log10(KDA P)`;
2. dot area: `Significant tested runs (%)`;
3. pale outline: `Tested; no significant run`;
4. gray `x`: `No eligible/tested run`; and
5. side bar: `Overall standardized MeanOfLog score`.

Avoid abbreviations such as `Q`, `FE`, `R`, or `S` in the legend.

## Color and accessibility

### Continuous evidence palette

Use a perceptually uniform sequential palette such as `cividis` or `viridis`.
`cividis` is preferred because it retains strong grayscale behavior.

Suggested conventions:

- low evidence: pale yellow-gray;
- high evidence: dark blue;
- missing/ineligible: neutral light gray;
- dot outline: medium gray or black; and
- overall score bars: one dark neutral navy.

Do not use a red-green or red-blue diverging palette because the quantity is
nonnegative evidence strength, not a signed effect.

### Redundant encoding

The figure must remain interpretable if color discrimination is impaired:

- dot size redundantly shows recurrence;
- facet position shows direction;
- column labels show sex/APOE stratum;
- row text and separators show network; and
- a distinct `x` or hatch shows missingness.

## Typography

- Sans-serif font throughout, preferably Arial or Helvetica.
- Figure title: 10-12 pt.
- Direction headers: 9-10 pt, semibold.
- Sex headers: 8-9 pt.
- APOE column labels: 7-8 pt.
- Gene labels: at least 7 pt.
- Network block labels: 7-8 pt, semibold.
- Legend text: at least 7 pt.

Suggested title:

> Sex- and APOE-stratified support for prioritized mitochondrial key drivers

Suggested subtitle:

> Primary directional KDA evidence; descriptive strata, not formal interaction tests

## Expected biological patterns

The design should make it possible to see, without forcing these outcomes:

- female e2 AD-up support involving astrocytic `APOE` and neuronal candidates
  such as `RPL11`, `RPS15`, `LAMTOR5`, `SELENOW`, `GABARAPL2`, and `TMEM147`;
- female e3/3 AD-up support for excitatory `WDR82` and OPC `FTL`/`ANKRD11`;
- female e4 AD-down support involving `BEX3`, `LAMTOR5`, `GABARAPL2`,
  `SELENOW`, and `HSPA1A`;
- the broad male e2 AD-down pattern; and
- male e4 microglial `SLC11A1` and astrocytic `APOE` support.

These are expected descriptive checks based on existing results, not plotting
rules. The code must not alter row inclusion, order, scale, or annotation to
make those patterns appear stronger.

## Interpretation constraints

The figure and caption must make the following explicit:

- dots summarize KDA runs, not donors or independent biological replications;
- broad-network reuse across fine cell types does not create independent
  network structures;
- differing query sizes, eligible runs, and donor power can affect patterns;
- AD-up and AD-down refer to the direction of the mitochondrial DEG signature,
  not activation or inhibition by the driver;
- KDA enrichment does not establish causal control; and
- visual sex/APOE differences are descriptive until tested with donor-aware
  interaction models.

Do not add asterisks comparing sex or APOE columns unless a separate formal
interaction analysis has been performed and documented.

## Required group-level plotted-data output

Write a long-format table beside the figure. Recommended filename:

```text
results/figures/analysis/phase12_kda/
  phase12_kda_figure_b_sex_apoe_plotted_data.tsv
```

Required fields:

```text
schema_version
broad_network
network_display_order
key_driver
driver_display_order
signature_group
sex
apoe_group
signature_direction
candidate_runs_tested
eligible_runs
ranking_coverage_fraction
significant_runs
significant_run_fraction
mean_minus_log10_p
mean_minus_log10_p_display
evidence_color_cap
overall_mean_of_log_score
overall_mean_of_log_score_standardized
conservative_significant_runs
conservative_fine_cell_types
display_status
selection_rule
```

The plotting script must use this prepared table. It must not recompute
selection, MeanOfLog scores, or significance from the significant-only Phase
12 table during rendering.

## Suggested caption

> **Sex- and APOE-stratified KDA evidence for prioritized mitochondrial
> regulators.** Rows show selected network-driver pairs passing a conservative
> primary-directional prioritization screen; columns show female and male APOE
> e2, e3/3, and e4 strata. AD-up and AD-down mitochondrial signatures are shown
> in aligned facets. Dot color represents the mean negative log10 raw KDA P
> value across tested candidate runs, and dot area represents the fraction of
> those runs with within-run BH-adjusted P <= 0.05. Small outlined dots denote
> tested cells with no significant run, whereas gray crosses denote no eligible
> or tested candidate run. Right-side bars show the overall standardized
> MeanOfLog score used for within-network ordering. Secondary pooled and
> combined-direction signatures were excluded to avoid duplicated evidence.
> Stratum differences are descriptive and do not constitute formal AD-by-sex
> or AD-by-APOE interaction tests.

## Implementation recommendation

The figure can be produced in R using `ggplot2` with aligned panels assembled
by `patchwork` or `cowplot`:

- `geom_point()` for the dot heatmap;
- a shared `scale_color_cividis_c()` for evidence strength;
- an area-correct `scale_size_area()` for recurrence;
- a separate narrow `geom_col()` panel for overall score; and
- `facet_grid()` or prepared factor levels for network grouping.

Axes-level control is important. Do not let automatic faceting independently
reorder or rescale the two directions.

## Validation and acceptance criteria

### Data validation

- [ ] The complete pre-FDR candidate-test table exists.
- [ ] Only eligible primary AD-up and AD-down runs contribute.
- [ ] Secondary pools and `AD_both_mito` are absent.
- [ ] Every group-level mean reconciles with run-level raw log P values.
- [ ] Every recurrence fraction reconciles with tested and significant run
      counts.
- [ ] Missing, tested-zero, and tested-significant states are distinct.
- [ ] Candidate selection follows the documented conservative rule.
- [ ] Row order is identical across direction facets.

### Visual validation

- [ ] Both facets share identical color and size limits.
- [ ] Dot area, not radius, is proportional to recurrence.
- [ ] Female and Male column blocks are visually separated and directly
      labeled.
- [ ] Networks are identified by both text and a narrow color strip.
- [ ] Gene labels remain at least 7 pt at final size.
- [ ] Missing cells cannot be mistaken for zero evidence.
- [ ] The figure remains interpretable in grayscale.
- [ ] No color implies AD-up versus AD-down direction.
- [ ] No visual significance brackets imply untested interactions.

### Export validation

- [ ] Export vector PDF and SVG versions.
- [ ] Export a PNG preview at 300-600 dpi.
- [ ] Verify readability at 178-183 mm final width.
- [ ] Confirm embedded or journal-compatible fonts.
- [ ] Save the plotted-data TSV and figure-generation log with the figure.

## References informing the design

- Professor's figure comments:
  [`notes_08042026.txt`](../../email_notes/notes_08042026.txt)
- MeanOfLog ranking recommendation:
  [`email_08042026_circular_figure_sort_order.md`](../../email_notes/email_08042026_circular_figure_sort_order.md)
- Phase 12 biological prioritization and stratum patterns:
  [`phase12_driver_gene_discussion.md`](phase12_driver_gene_discussion.md)
- Figure A companion design:
  [`phase_12_kda_panel_a_reduced_circular_figure_design.md`](phase_12_kda_panel_a_reduced_circular_figure_design.md)
- Wang KDP ranking implementation:
  [PHG_protein_bnGlobalKDA_ranking.R](https://github.com/wange230/proteomics_networks/blob/main/codes/Baysian_network/KDA_analysis/PHG_protein_bnGlobalKDA_ranking.R)
- NetWeaver MeanOfLog implementation:
  [ensemble.rank.R](https://github.com/mw201608/NetWeaver/blob/master/R/ensemble.rank.R)

## Implementation and generated artifacts (2026-08-09)

The design was implemented in the same Phase 12 script and figure directories
used by the original circular figure.

Primary figure script:

```text
scripts/figures/analysis/phease12_kda/
  visualize_phase12_kda_panel_b_sex_apoe.R
```

Shared preparation and helper scripts:

```text
scripts/figures/analysis/phease12_kda/
  prepare_phase12_kda_figure_data.R
  phase12_kda_figure_common.R
```

Generated Panel B files:

```text
results/figures/analysis/phase12_kda/
  phase12_kda_panel_b_sex_apoe.png
  phase12_kda_panel_b_sex_apoe.pdf
  phase12_kda_panel_b_sex_apoe.svg
  phase12_kda_panel_b_sex_apoe_plotted_data.tsv
  phase12_kda_panel_b_sex_apoe_generation_log.tsv
```

The implemented panel contains 16 prioritized network-driver rows and 192
sex/APOE-by-direction cells. Candidate selection followed the documented
conservative screen and retained at most three rows per network. The selected
rows comprise Astrocytes (`RPL11`, `APOE`, `RPS15`), Excitatory neurons
(`RPL11`, `TMEM147`, `SELENOW`), Inhibitory neurons (`RPS15`, `LAMTOR5`,
`BEX3`), Microglia (`RPL11`, `SLC11A1`, `RPS15`), OPCs (`RPS15`, `FTL`,
`ANKRD11`), and Oligodendrocytes (`RPL11`). No Vasculature candidate from the
prespecified pool passed the same row-level criteria, so an empty network block
was not drawn.

One common color scale is used across both direction facets. Its upper display
limit is the prespecified 95th percentile of finite plotted-cell evidence,
5.000102 mean -log10(KDA P); uncapped values remain in the plotted-data TSV.
The table also preserves all three display states: 45 tested-significant cells,
128 tested cells with no significant run, and 19 cells with no eligible or
tested run.

Visual inspection was performed on the 7.1 x 7.2 inch, 450-dpi PNG after
rendering. Network names and color strips were moved outside the gene-label
column to avoid collisions, and the subtitle explicitly states that the strata
are descriptive rather than formal interaction tests.
