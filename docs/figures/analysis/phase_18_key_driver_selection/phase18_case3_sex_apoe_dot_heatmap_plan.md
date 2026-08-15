# Phase 18 non-MT Driver Sex/APOE Dot-Heatmap Plan — Legacy Inputs

> The former Case 3 maps to `non_mt_driver`. The old auxiliary inputs predate
> the two-class recomputation and must be regenerated from the current
> `call_key_driver_returns.tsv` before this figure is rerun.

## Status and purpose

**Status:** Planned; not yet implemented  
**Prepared:** 2026-08-14

This plan specifies a Phase 18 sex/APOE-stratified evidence figure for the
genes displayed in the Case 3 circular graph. Its visual grammar is based on:

```text
results/figures/analysis/phase12_kda/sex_apoe_figure/
  phase12_kda_sex_apoe.png
```

The Phase 12 figure is a layout reference only. The new plot must use the
validated Phase 18 row universe, final run-level P values, final conservative
support definition, coverage logic, and annotations.

Working title:

> Sex- and APOE-stratified support for Case 3 key-driver candidates

Working subtitle:

> Primary AD-up and AD-down mitochondrial queries; descriptive strata, not interaction tests

The figure asks where the Case 3 drivers receive their run-level evidence:
across women and men, APOE groups, AD-up and AD-down mitochondrial signatures,
and fine-cell-type queries within each broad Bayesian network.

It does not test a sex-by-APOE interaction, prove sex specificity, or replace
the Phase 18 candidate selection.

## Bottom-line design

Create one dot heatmap with:

- one row per passing Case 3 gene-network context involving a circle gene;
- 12 fixed columns: six primary sex/APOE groups for AD-up and the same six for
  AD-down;
- dot fill for stratum-level ACAT evidence;
- dot area for the fraction of usable fine-cell-type queries that are
  conservatively supporting;
- explicit symbols for tested with zero support, eligible with no usable test,
  and no eligible query;
- a broad-network color strip;
- an indicator showing whether the context was actually in the top-five
  circle; and
- right-side tracks for the frozen network-level aggregate ACAT q value,
  support/usable counts, coverage, and evidence tier.

## Frozen row universe

Use the same three-level universe contract as Plan 1.

1. Derive the 15 unique genes in the official Case 3 circle.
2. Reconcile the 21 displayed gene-network contexts.
3. For those genes, include all passing Case 3 gene-network contexts.

The default heatmap therefore has 22 rows in the current validated bundle.
The additional row is `RPS15` in `Excitatory_neurons`, within-case rank 20,
which passed all candidate gates but was outside the top-five circle display
cap.

Mark the 21 circle-displayed rows with a solid row-side symbol and the one
additional passing context with an open symbol. Do not silently omit the
additional context: it is directly relevant to interpreting RPS15 after the
gene entered scope through another network.

An optional `--strict-circle-rows` rendering may restrict the visualization to
21 displayed rows for a secondary export, but the primary figure and plotted
data use all 22 passing contexts. Any optional export must be separately named
and must not replace the primary output.

The current 15/21/22 counts are blocking reconciliation targets, not hard-coded
scientific inputs.

## Column structure

Use the frozen primary group order:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

Repeat that order for both directions:

| Direction block | Columns |
|---|---|
| `AD_up_mito` | `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, `M_e4` |
| `AD_down_mito` | `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, `M_e4` |

Display labels should use two-level headers:

- top level: `AD-up mitochondrial query` and `AD-down mitochondrial query`;
- second level: `Female` over the first three groups and `Male` over the last
  three; and
- third level: `APOE ε2`, `APOE ε3/ε3`, and `APOE ε4`.

The methods must retain the source IDs and the exact project definitions of
the ε2 and ε4 groups. Do not expand them into “carrier” terminology unless the
source manifest explicitly defines them that way.

## Row ordering and labels

Use the same gene-level `atlas_display_order` defined in Plan 1:

1. decreasing number of passing broad networks;
2. decreasing number of unique conservatively supporting fine cell types;
3. decreasing number of conservatively supporting run-specific queries; and
4. symbol alphabetically.

Within a repeated gene, order rows by the fixed seven-network order. The
visible row label is `current_symbol`; place the broad-network name in an
adjacent aligned column or use a network strip with a direct text label. Do
not rely on color alone.

Call this a display order, never a statistical rank. Preserve the original
network-specific `within_case_rank` in the row-annotation TSV.

## Unit of aggregation

One heatmap cell represents a single:

```text
current symbol × broad network × signature direction × primary sex/APOE group
```

Within that cell, the observations are the eligible fine-cell-type KDA runs
for the fixed broad network. These runs differ in fine-cell-type query but
reuse the same broad Bayesian network. They are repeated evidence contexts,
not independent biological replicates.

Create the full Cartesian grid before joins:

```text
22 gene-network rows × 12 strata = 264 heatmap cells
```

Rows with no eligible or usable run must remain explicit; they must not vanish
from the plot or denominator audit.

## Stratum-level statistics

### Eligible, usable, and supporting counts

For each heatmap cell calculate:

```text
eligible_query_count
  = number of included fine-cell-type runs in the network/group/direction cell
    for which the Case 3 gene is eligible

usable_query_count
  = number of those rows with usable_test = TRUE and a finite final_raw_p

conservative_support_count
  = number of those rows with conservative_support = TRUE

support_fraction
  = conservative_support_count / usable_query_count, when usable > 0

coverage_fraction
  = usable_query_count / eligible_query_count, when eligible > 0
```

For Case 3, membership is not query-dependent, but eligibility and usability
still must be derived from the run-level table rather than assumed.

### ACAT evidence

For each cell, construct one ordered P-value vector over all eligible runs:
use `final_raw_p` when `usable_test = TRUE` and a missing value otherwise.
Include nonsignificant P values and valid P = 1 results; never prefilter to
conservative-support or significant rows.

The implementation must call the canonical `acat_combine(...,
missing_action="omit")` from:

```text
scripts/18_export_significant_returns.py
```

Do not copy or independently reimplement its zero, one, and extreme-P handling.
Import it through a tested loader or move it into a shared production utility
only if the production script and all existing validation tests are updated in
the same implementation change.

For the primary cell result, `missing_action="omit"` combines every usable
value and omits the explicitly represented unavailable tests. The cell-level
result is:

```text
stratum_acat_p
```

It is a descriptive combined P value. Do not label it q, and do not use it to
change candidate membership. Also pass the same eligible-run vector to the
canonical function with `missing_action="one"` to calculate
`stratum_missing_as_one_acat_p` for the plotted-data sensitivity audit; do not
display it as the primary color.

No across-cell Benjamini-Hochberg correction is needed for the descriptive
color map. If a future analysis wants formal stratum discoveries, that is a
separate inferential plan that must define its test family in advance.

### Frozen network-level annotations

The right-side evidence track uses the existing network-specific
`aggregate_acat_q` from `key_driver_candidates.tsv`. It must not be recomputed
from the 12 displayed cells. Also show:

```text
conservative_support_count / usable_run_count
usable_run_count / eligible_run_count
evidence_tier
within_case_rank
circle_displayed
```

This distinguishes the descriptive strata from the official Phase 18
network-level selection evidence.

## Visual encoding

### Heatmap-cell states

Use four mutually exclusive states:

| State | Definition | Mark |
|---|---|---|
| Supporting tested cell | `usable > 0` and `support > 0` | Filled circle |
| Tested, zero conservative support | `usable > 0` and `support = 0` | Small open circle |
| Eligible, no usable test | `eligible > 0` and `usable = 0` | Gray X |
| No eligible query | `eligible = 0` | Pale cell with short dash |

For supporting cells:

- dot area represents `support_fraction`, with area—not radius—scaled
  linearly over 0–1;
- fill represents capped `-log10(stratum_acat_p)` on a colorblind-safe
  sequential palette; and
- a thin dark outline maintains visibility at low evidence and in grayscale.

The open-circle state intentionally emphasizes the lack of a run meeting all
conservative support gates. Its exact ACAT P remains available in plotted data
and tooltips are not required for the static figure.

### Evidence scale

Use one fixed evidence cap for every heatmap cell. Determine and freeze the cap
after auditing the validated distribution, record it in the figure manifest,
and label the legend `capped -log10(stratum ACAT P)`. Do not select a separate
cap by direction, sex, APOE group, network, or row.

Use a separate right-side mini-axis for `-log10(network aggregate ACAT q)` so
readers cannot confuse the stratum P color with the official network q value.
The right-side q track should use neutral dark points/lines rather than reuse
the heatmap fill palette.

### Row annotations

Add:

- a network color strip plus network text;
- a solid/open circle-display marker;
- an evidence-tier strip with a text legend;
- a small `mito_extended` marker where applicable; and
- right-side count labels for `support/usable` and `usable/eligible`.

Legends must sit to the right of the figure in a compact vertical stack and
must not cover data. Use tight item spacing while retaining at least 7-pt text
at final size.

## Authoritative inputs

Read only the validated Phase 18 production bundle:

```text
results/minerva_production/18_key_driver_selection/
```

Required files:

| File | Use |
|---|---|
| `key_driver_status.tsv` | Require terminal `validated_complete` status. |
| `key_driver_checks.tsv` | Require all blocking checks to pass. |
| `key_driver_artifacts.tsv` | Verify the hashes/bytes of all scientific inputs. |
| `key_driver_analysis_manifest.tsv` | Verify thresholds, rank rule, and display cap. |
| `key_driver_top5.tsv` | Freeze the 21 circle-display contexts. |
| `key_driver_figure_data.tsv` | Reconcile the 15 circle genes. |
| `key_driver_candidates.tsv` | Select all passing contexts and obtain frozen network-level annotations. |
| `key_driver_candidate_tests.tsv.gz` | Supply complete final run-level P values, usability, support gates, group, and direction. |
| `key_driver_conservative_support.tsv.gz` | Independently reconcile support counts and run IDs. |
| `key_driver_run_manifest.tsv` | Freeze the included primary run universe and stratum labels. |
| `key_driver_case_manifest.tsv` | Verify the exact Case 3 definition. |

The Phase 12 heatmap, plotted data, and R renderer can be consulted for layout
conventions only:

```text
results/figures/analysis/phase12_kda/sex_apoe_figure/
  phase12_kda_sex_apoe.png
  phase12_kda_sex_apoe_plotted_data.tsv

scripts/figures/analysis/phease12_kda/
  visualize_phase12_kda_sex_apoe.R
```

They must not supply P values, row membership, support calls, or denominators.

## Planned implementation

Use the shared universe/preflight module from Plan 1 plus a dedicated
preparation script and renderer:

```text
scripts/figures/analysis/phase_18_key_driver_selection/
  phase18_case3_common.py
  prepare_phase18_case3_sex_apoe.py
  visualize_phase18_case3_sex_apoe.R
```

Plan 2 must remain runnable on its own. It may share source code with Plan 1,
but it must derive its inputs directly from the validated Phase 18 bundle and
must not require Plan 1's output directory to exist.

Implementation phases:

1. **Preflight:** verify validated status, checks, source artifacts, manifests,
   Case 3 definition, and primary run scope.
2. **Freeze rows:** derive the 15 genes, 21 displayed contexts, and 22 passing
   contexts with the common module.
3. **Construct the grid:** create every 22 × 12 row-stratum combination before
   attaching run-level results.
4. **Attach eligible runs:** join the included run manifest by broad network,
   group, and direction; then join the target gene's candidate-test row by
   `kda_run_id`, network, symbol, and case.
5. **Aggregate cells:** compute eligible/usable/support counts and both primary
   omit-missing and sensitivity missing-as-one ACAT P values with the canonical
   Phase 18 function.
6. **Reconcile:** verify all cell totals against candidate and conservative
   support tables.
7. **Render:** draw SVG/PDF/PNG from a frozen plotted-data table and row
   annotation table.
8. **Review:** inspect at final physical size, in grayscale, and with
   deuteranopia, protanopia, and tritanopia simulations.
9. **Publish atomically:** publish only a complete, validated package.

## Planned data products

### Heatmap plotted data

`phase18_case3_sex_apoe_plot_data.tsv` contains exactly one row per heatmap
cell and at least:

```text
schema_version
case_id
current_symbol
broad_network
atlas_display_order
network_order
circle_displayed
within_case_rank
signature_direction
direction_order
signature_group
group_order
eligible_query_count
usable_query_count
missing_query_count
coverage_fraction
conservative_support_count
support_fraction
stratum_acat_p
stratum_missing_as_one_acat_p
negative_log10_stratum_acat_p
capped_negative_log10_stratum_acat_p
cell_state
```

### Row annotation data

`phase18_case3_sex_apoe_row_annotations.tsv` contains exactly one row per
passing gene-network context and at least:

```text
schema_version
case_id
current_symbol
broad_network
atlas_display_order
network_order
circle_displayed
circle_display_rank
within_case_rank
evidence_tier
extended_reference_member
eligible_run_count
usable_run_count
conservative_support_count
coverage_fraction
recurrence_fraction
aggregate_acat_p
aggregate_acat_q
negative_log10_aggregate_acat_q
```

### Run-level aggregation audit

Write a compressed audit table containing the exact input rows used in every
cell:

```text
phase18_case3_sex_apoe_aggregation_audit.tsv.gz
```

It must retain `kda_run_id`, fine cell type, group, direction, gene, network,
eligibility, test status, usability, final raw P, all conservative-support
gates, and final conservative-support flag. This makes every dot reproducible.

## Blocking validation checks

### Bundle and row universe

- production status is not `validated_complete`;
- any blocking production check is absent or failed;
- any used input hash/byte count differs from the artifact manifest;
- a row is not exactly `case3_not_core_mito` or has `is_core_mito != FALSE`;
- the provenance universe does not reconcile to 15 genes, 21 displayed
  contexts, and 22 passing contexts;
- the below-cap context reconciliation is not the current RPS15–excitatory
  row; or
- a gene-network key is duplicated.

### Grid and run joins

- the default plot grid is not exactly 22 × 12 = 264 rows;
- the six group IDs or two direction IDs are incomplete, duplicated, or out
  of order;
- an included primary run is assigned to the wrong broad network, group, or
  direction;
- an eligible gene-run opportunity lacks exactly one candidate-test row;
- a candidate-test row falls outside the included primary run manifest; or
- `final_raw_p` is nonfinite or outside `[0, 1]` when `usable_test = TRUE`.

### Count reconciliation

For every gene-network row:

- the sum of 12 cell `eligible_query_count` values must equal
  `eligible_run_count`;
- the sum of 12 `usable_query_count` values must equal `usable_run_count`;
- the sum of 12 `conservative_support_count` values must equal the frozen
  candidate-table support count;
- support must not exceed usable, and usable must not exceed eligible;
- recomputed overall coverage and recurrence must match the candidate table;
- the exact set of supporting run IDs must match
  `key_driver_conservative_support.tsv.gz`; and
- circle-display status, aggregate q, evidence tier, and within-case rank must
  match the frozen candidate/top-five tables.

### ACAT correctness

- the production ACAT reference example must pass at its existing tolerance;
- every stratum ACAT must use all and only usable final raw P values;
- no cell may be combined from significant/supporting rows alone;
- a cell with no usable P values must have missing ACAT fields;
- a cell with all usable P values equal to 1 must have ACAT P = 1;
- independently recombining all 12 strata's underlying raw P rows with the
  canonical function must reproduce the candidate's `aggregate_acat_p` within
  floating-point tolerance; and
- no stratum P value may be written into a q-value field.

The last reconciliation combines the underlying run-level P values, not the 12
already combined stratum P values.

### Visual-state integrity

- each heatmap cell maps to exactly one of the four declared states;
- supporting dots never have zero support;
- open tested dots always have usable tests and zero conservative support;
- X marks always have eligible queries but zero usable tests;
- dash cells always have zero eligible queries;
- the evidence cap and dot-size scale are shared across all 264 cells; and
- the network-level q track is visually and textually distinct from the
  stratum-level P color scale.

## Output package

Write to:

```text
results/figures/analysis/phase_18_key_driver_selection/case3_sex_apoe/
```

Planned files:

```text
phase18_case3_sex_apoe.svg
phase18_case3_sex_apoe.pdf
phase18_case3_sex_apoe.png
phase18_case3_sex_apoe_plot_data.tsv
phase18_case3_sex_apoe_row_annotations.tsv
phase18_case3_sex_apoe_aggregation_audit.tsv.gz
phase18_case3_sex_apoe_caption.md
phase18_case3_sex_apoe_methods.md
phase18_case3_sex_apoe_manifest.tsv
phase18_case3_sex_apoe_checks.tsv
phase18_case3_sex_apoe_artifacts.tsv
phase18_case3_sex_apoe_status.tsv
```

The manifest records source/script hashes, run timestamp, software versions,
row and cell counts, group/direction order, palette, evidence cap, dot-size
range, fonts, and physical dimensions.

## Publication and accessibility specification

- Authoritative formats: SVG and PDF.
- Raster preview: PNG at 450 dpi.
- Initial canvas: 15 × 11 inches for 22 rows; freeze the final size after
  final-size review.
- Typeface: one sans-serif family throughout.
- Minimum final-size text: 7 pt; panel/block titles 11–12 pt; main title
  13–14 pt.
- Use dot-area scaling with a printed size legend at 0.25, 0.50, 0.75, and
  1.00 support fraction.
- Keep legends in a compact right-side stack outside the heatmap.
- Use dark outlines and distinct shapes so interpretation does not depend on
  hue.
- Confirm label alignment, no clipping, and distinguishable states in
  grayscale and common color-vision simulations.
- Verify that the figure remains readable when reduced to the intended journal
  width; if not, split AD-up and AD-down into aligned panels without changing
  row order or scale.

## Interpretation limits required in caption and methods

The published package must state:

- The patterns are descriptive strata and are not formal sex, APOE, or
  sex-by-APOE interaction tests.
- A missing/untested cell is not evidence of no biological effect.
- An open circle means tested but no run passed every conservative support
  gate; it does not necessarily mean the combined P value equals 1.
- Fine-cell-type queries within a row reuse one broad Bayesian network and are
  not independent external replications.
- Stratum colors show descriptive ACAT P values; the right-side track shows
  the frozen network-level aggregate q used in Phase 18.
- Case 3 means outside core MitoCarta, not necessarily unrelated to
  mitochondrial function.
- The circle top-five rule is a display cap, which is why the primary figure
  retains one additional passing RPS15 context.
- Bayesian-network key-driver evidence prioritizes candidates but does not
  prove experimental causality.

## Completion criteria

Plan 2 is complete only when:

1. the default 22-row, 264-cell plotted-data table and all declared outputs
   exist and are nonempty;
2. every bundle, universe, count, ACAT, and visual-state check passes;
3. output status is `validated_complete` and all source/output SHA-256 hashes
   are recorded;
4. SVG/PDF remain vector and PNG metadata confirms 450 dpi;
5. manual final-size and accessibility reviews are recorded;
6. figure, plotted data, and run-level audit reconcile exactly; and
7. the caption contains every interpretation limit above.
