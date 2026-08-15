# Phase 18 non-MT Driver Evidence Atlas Plan — Legacy Inputs

> The former Case 3 maps directly to the current `non_mt_driver` class.
> However, the frozen counts and auxiliary input tables below predate the
> two-class recomputation. Regenerate them from
> `key_driver_significant_returns.tsv` schema
> `phase18_significant_kda_returns_v2` before producing a current atlas.

## Status and purpose

**Status:** Implemented and validated on 2026-08-14  
**Prepared:** 2026-08-14

The implementation consists of the shared
[Case 3 validation module](../../../../scripts/figures/analysis/phase_18_key_driver_selection/phase18_case3_common.py),
[atlas preparation and packaging script](../../../../scripts/figures/analysis/phase_18_key_driver_selection/prepare_phase18_case3_evidence_atlas.py),
and [R renderer](../../../../scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_case3_evidence_atlas.R).
The validated output package is under
[case3_evidence_atlas](../../../../results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas/),
including the [PNG preview](../../../../results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas/phase18_case3_evidence_atlas.png),
[gene summary](../../../../results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas/phase18_case3_gene_summary.tsv),
and [gene-network detail table](../../../../results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas/phase18_case3_gene_network_details.tsv).

The completed package contains all 12 declared outputs. All 32 checks passed,
the terminal status is `validated_complete`, and final-size review was
completed in color, grayscale, deuteranopia, protanopia, and tritanopia
simulations.

This plan specifies a publication-ready evidence atlas and two auditable tables
for the genes displayed in the validated Phase 18 Case 3 circular graph:

```text
results/figures/analysis/phase_18_key_driver_selection/three_case_circular/
  phase18_case3_not_core_mito_circular.png
```

Case 3 is defined as:

```text
case3_not_core_mito
```

These drivers are outside the fixed 1,136-gene core MitoCarta inventory. That
definition does not establish that a gene lacks mitochondrial biology. The
broader `mito_extended` annotation must remain visible as a secondary
annotation and must not change Case 3 membership.

The atlas answers four questions for each circle gene:

1. In how many broad cell-type networks is it a passing Case 3 driver?
2. Across how many fine cell types and run-specific queries is it supported?
3. How complete and recurrent is its evidence?
4. Is its evidence stable to fine-cell-type omission and robust to network
   degree?

This is a descriptive follow-up to the frozen Phase 18 selection. It must not
recompute candidate status, alter the five selection gates, or create a new
global gene ranking.

## Bottom-line deliverables

Create one primary three-part atlas and two companion tables.

### Primary figure

Working title:

> Breadth and reproducibility of Case 3 key-driver candidates

Working subtitle:

> Drivers outside the 1,136-gene core MitoCarta inventory

The figure will contain:

- **Panel A — network evidence matrix:** 15 circle genes by seven broad
  networks, with passing status, circle-display status, within-network rank,
  and network-specific aggregate ACAT q value;
- **Panel B — breadth and recurrence tracks:** passing-network count, unique
  supporting fine-cell-type count, conservatively supporting query count,
  usable/eligible query coverage, and supporting sex/APOE-group and direction
  breadth; and
- **Panel C — network-specific robustness:** stability-retention and
  degree-matched empirical-tail results shown as separate network-colored
  points, never pooled into a new inferential score.

### Companion tables

1. `phase18_case3_gene_summary.tsv`: exactly one row per circle gene.
2. `phase18_case3_gene_network_details.tsv`: exactly one row per passing Case
   3 gene-network context involving a circle gene.

The TSVs are primary scientific outputs, not incidental plotting files.

## Frozen row universes

Three related universes must be named and kept separate.

### 1. Circle-gene provenance universe

The gene universe is the union of current symbols displayed in the official
Case 3 circle. The current validated snapshot has 15 genes:

```text
ANKRD11, APOE, ATP6V1F, DYNLT1, FTL, LAMTOR5, LAPTM4A, NCOA1,
RPL11, RPL15, RPL38, RPLP1, RPS13, RPS15, SELENOW
```

The preparation script must derive this set from the validated Phase 18
top-five/figure data rather than hard-code it. The list above is a blocking
reconciliation target for the current frozen bundle.

### 2. Circle-display gene-network universe

The current circle contains 21 displayed Case 3 gene-network rows. These are
the `top5_display = TRUE` contexts for the 15 provenance genes.

### 3. Deeper passing-context universe

For the 15 provenance genes, include every Case 3 gene-network row whose
`terminal_candidate_status = driver_candidate`, even if it fell below the
five-row display cap in that network. The current bundle contains 22 such
rows. The sole additional context is `RPS15` in `Excitatory_neurons`, with
within-case rank 20.

This 22-row universe is the default for the detail table and robustness
tracks. A `circle_displayed` flag must identify the 21 rows shown in the
circle. This prevents the arbitrary top-five display cap from erasing relevant
evidence about a gene already placed in scope by the circle.

The 15/21/22 counts and the identity of the additional context are validation
targets, not renderer constants.

## Precise metric definitions

The phrase “cell types” can refer to broad networks or fine cell types. Both
must be reported with unambiguous names.

### Broad-network breadth

For one gene:

```text
passing_broad_network_count
  = number of distinct broad_network values among its passing Case 3 contexts
```

Also retain `circle_display_network_count`, the number of those contexts shown
in the top-five circle.

### Fine-cell-type breadth

For one gene:

```text
unique_supporting_fine_cell_type_count
  = size of the exact set union of supporting_fine_cell_types
    across its passing Case 3 contexts
```

Do not sum the already aggregated per-network counts without checking the
underlying symbols. Derive the union from conservatively supporting run rows
in `key_driver_candidate_tests.tsv.gz`, then reconcile it to the pipe-delimited
candidate-table annotations.

### Run-specific query support

A run-specific query is one:

```text
fine cell type × sex/APOE group × signature direction
```

For one gene, across its passing Case 3 contexts:

```text
conservative_supporting_query_count
  = number of distinct kda_run_id values with conservative_support = TRUE

usable_query_count
  = number of distinct kda_run_id values with usable_test = TRUE

eligible_query_count
  = number of distinct eligible kda_run_id values

query_recurrence_fraction
  = conservative_supporting_query_count / usable_query_count

query_coverage_fraction
  = usable_query_count / eligible_query_count
```

The numerator must never appear without its denominator. The figure should
show `support/usable` beside the recurrence mark and `usable/eligible` beside
the coverage mark. Conservative support retains all final Phase 18 gates:
effective query size at least 10, at least two other query genes, fold
enrichment greater than 1, and recalculated run q at most 0.05.

### Sex/APOE-group and direction breadth

Use exact set unions across conservatively supporting run IDs:

- `supporting_group_count`, from the six primary groups;
- `supporting_groups`, as a sorted pipe-delimited set;
- `supporting_direction_count`, 0–2; and
- `supporting_directions`, `AD_up_mito`, `AD_down_mito`, or both.

These are breadth annotations, not interaction tests.

### Aggregate evidence

Aggregate ACAT P and q values remain gene-network-specific. Panel A can encode
`-log10(aggregate_acat_q)` separately for every passing network context.

At the gene-summary level, report only descriptive endpoints:

- `best_aggregate_acat_q` and its network;
- `worst_aggregate_acat_q` and its network; and
- the number of q-passing network contexts.

Do not average q values, combine them across networks, or label the best q as a
gene-wide q value.

### Stability and degree robustness

For each passing gene-network context, retain:

- stability assessable repetitions;
- nominal-P pass fraction;
- aggregate-q pass fraction;
- candidate-retention fraction;
- worst within-case rank;
- out-degree and undirected degree;
- completed and requested degree-matched draws;
- degree-matched empirical-tail P value; and
- the production `blocking_gate` annotation.

Panel C must show network-specific points. It must not average empirical P
values or retention fractions into a new selection score. Exact values remain
in the gene-network detail table.

## Figure design

### Shared ordering

The seven broad networks use the established order and colors:

| Order | Source ID | Display label | Color |
|---:|---|---|---|
| 1 | `Astrocytes` | Astrocytes | `#009E73` |
| 2 | `Excitatory_neurons` | Excitatory neurons | `#E69F00` |
| 3 | `Inhibitory_neurons` | Inhibitory neurons | `#0072B2` |
| 4 | `Microglia` | Microglia | `#CC79A7` |
| 5 | `OPCs` | OPCs | `#56B4E9` |
| 6 | `Oligodendrocytes` | Oligodendrocytes | `#F0E442` |
| 7 | `Vasculature_cells` | Vasculature | `#D55E00` |

Order genes for display by:

1. decreasing `passing_broad_network_count`;
2. decreasing `unique_supporting_fine_cell_type_count`;
3. decreasing `conservative_supporting_query_count`; and
4. `current_symbol` alphabetically.

Call this `atlas_display_order`, not rank. State in the caption that it is a
layout order and has no inferential meaning.

### Panel A: network evidence matrix

Create a complete 15 × 7 tile grid. Each cell has one of three states:

1. **No passing context:** pale neutral background, no q-value encoding.
2. **Passing context not displayed in circle:** evidence-colored fill with a
   light dashed outline.
3. **Passing context displayed in circle:** the same evidence-colored fill
   with a dark solid outline.

Encode the network-specific `-log10(aggregate_acat_q)` with a colorblind-safe
sequential palette such as cividis. Use one prespecified cap for the entire
figure; determine it once during implementation from the validated bundle,
freeze it in the figure manifest, and label capped values in the legend.

Place `within_case_rank` as a small integer inside each passing tile. Do not
use fill or tile size to encode the atlas display order. Add a small gene-side
marker for `extended_reference_member`, with a text legend; currently this is
expected for NCOA1 only and must be checked rather than hard-coded.

### Panel B: breadth and recurrence tracks

Align the following tracks to the same 15 gene rows:

- passing broad networks, range 0–7;
- unique supporting fine cell types;
- conservative support among usable queries, with `support/usable` text;
- usable among eligible queries, with `usable/eligible` text;
- supporting primary sex/APOE groups, range 0–6; and
- supported AD directions, range 0–2.

Use points or compact bars with direct count labels. For recurrence and
coverage, map the fraction to position or length but print the raw counts.
Avoid pie charts and avoid using marker area for raw counts.

All gene-level run counts refer only to the gene's passing Case 3 network
contexts. Put “among passing Case 3 contexts” in the panel subheading or
caption.

### Panel C: network-specific robustness

Use two aligned mini-tracks:

- candidate-retention fraction on a fixed 0–1 axis; and
- `-log10(degree_matched_empirical_tail_p)` on a labeled fixed axis.

Plot one point per passing gene-network context and color it by broad network.
Use a distinct open marker when requested sensitivity draws are incomplete or
the production blocking gate is not passed. Print exact draw counts and worst
rank in the detail table rather than crowding the figure.

The caption must say that these are sensitivity diagnostics and did not
determine the Phase 18 candidate rank.

## Table specifications

### Gene summary table

`phase18_case3_gene_summary.tsv` must include at least:

```text
schema_version
case_id
current_symbol
is_core_mito
extended_reference_member
circle_gene
circle_display_network_count
circle_display_networks
passing_broad_network_count
passing_broad_networks
unique_supporting_fine_cell_type_count
unique_supporting_fine_cell_types
eligible_query_count
usable_query_count
missing_query_count
query_coverage_fraction
conservative_supporting_query_count
query_recurrence_fraction
supporting_group_count
supporting_groups
supporting_direction_count
supporting_directions
best_aggregate_acat_q
best_aggregate_acat_q_network
worst_aggregate_acat_q
worst_aggregate_acat_q_network
atlas_display_order
```

The table must be deterministically sorted by `atlas_display_order` and carry
an explicit note in the methods file that this is not a statistical rank.

### Gene-network detail table

`phase18_case3_gene_network_details.tsv` must contain all 22 passing contexts
in the current snapshot and include at least:

```text
schema_version
case_id
current_symbol
broad_network
circle_displayed
circle_display_rank
within_case_rank
evidence_tier
eligible_run_count
usable_run_count
missing_run_count
coverage_fraction
conservative_support_count
recurrence_fraction
supporting_fine_cell_type_count
supporting_fine_cell_types
supporting_group_count
supporting_groups
supporting_direction_count
supporting_directions
median_support_fold_enrichment
maximum_support_fold_enrichment
aggregate_acat_p
aggregate_acat_q
missing_as_one_acat_p
missing_as_one_acat_q
stability_assessable_repetitions
stability_nominal_fraction
stability_q_fraction
stability_candidate_fraction
stability_worst_rank
out_degree
undirected_degree
requested_degree_matched_draws
completed_degree_matched_draws
degree_matched_empirical_tail_p
degree_sensitivity_blocking_gate
extended_reference_member
```

Sort by `atlas_display_order`, then fixed broad-network order. Preserve
unrounded numeric columns in TSV outputs; rounding is for labels only.

## Authoritative inputs

Read the validated production bundle only:

```text
results/minerva_production/18_key_driver_selection/
```

Required files:

| File | Use |
|---|---|
| `key_driver_status.tsv` | Require terminal `validated_complete` status. |
| `key_driver_checks.tsv` | Require every blocking check to pass. |
| `key_driver_artifacts.tsv` | Verify hashes/bytes for all used inputs. |
| `key_driver_analysis_manifest.tsv` | Verify case rules, thresholds, rank order, and display cap. |
| `key_driver_top5.tsv` | Freeze the 21 circle-displayed gene-network contexts. |
| `key_driver_figure_data.tsv` | Reconcile the exact circle provenance universe and annotations. |
| `key_driver_candidates.tsv` | Obtain all passing contexts, aggregate evidence, coverage, support, and annotations. |
| `key_driver_candidate_tests.tsv.gz` | Derive exact run-ID set unions and query denominators. |
| `key_driver_conservative_support.tsv.gz` | Independently reconcile conservative supporting runs. |
| `key_driver_stability_summary.tsv` | Add network-specific stability diagnostics. |
| `key_driver_stability_replicates.tsv.gz` | Audit stability summaries and worst ranks. |
| `key_driver_network_degree_sensitivity.tsv` | Add network-degree robustness diagnostics. |
| `key_driver_run_manifest.tsv` | Reconcile eligible run IDs and group/direction labels. |

The Phase 12 products and figures are visual references only and must not
supply scientific values.

## Planned implementation

Use a preparation/validation script and a renderer:

```text
scripts/figures/analysis/phase_18_key_driver_selection/
  phase18_case3_common.py
  prepare_phase18_case3_evidence_atlas.py
  visualize_phase18_case3_evidence_atlas.R
```

`phase18_case3_common.py` should contain the shared validated-bundle preflight,
network order, circle-universe derivation, and exact token-set helpers also
used by Plan 2. It must not contain mutable scientific results.

Implementation phases:

1. **Preflight:** validate production status, blocking checks, artifacts, case
   ID, rank order, and display cap before creating temporary outputs.
2. **Freeze provenance:** derive the 15 circle genes and 21 displayed contexts
   from `key_driver_top5.tsv` and `key_driver_figure_data.tsv`.
3. **Expand context:** select every passing Case 3 context for those genes;
   reconcile the expected 22 rows and the one below-cap RPS15 context.
4. **Build run-level sets:** join candidate-test and run-manifest rows by
   `kda_run_id`; compute distinct eligible, usable, and supporting run-ID sets.
5. **Build tables:** produce the gene summary, gene-network details, and a
   complete 15 × 7 plotting grid.
6. **Validate tables:** execute all blocking reconciliations below.
7. **Render:** create the matched SVG, PDF, and PNG from the validated plotting
   files, not directly from raw production inputs.
8. **Review:** inspect at final physical size in color, grayscale, deuteranopia,
   protanopia, and tritanopia simulations.
9. **Publish atomically:** move a complete temporary package into the final
   output directory only after all checks pass.

## Blocking validation checks

The preparation or renderer must stop if any condition fails.

### Bundle and provenance

- production status is not `validated_complete`;
- a blocking production check is absent or failed;
- a used input hash or byte count differs from `key_driver_artifacts.tsv`;
- the case ID is not exactly `case3_not_core_mito`;
- any provenance/detail row has `is_core_mito != FALSE`;
- the current bundle does not reconcile to 15 circle genes, 21 displayed
  contexts, and 22 passing contexts for those genes;
- the set difference between passing and displayed contexts is not exactly the
  expected current RPS15–excitatory row; or
- a gene-network key is duplicated.

### Count and set reconciliation

- any summary gene lacks a circle-provenance row;
- the gene summary does not contain exactly one row per provenance gene;
- a displayed row does not match the circle display rank and q value;
- a passing context is not a `driver_candidate`;
- `conservative_support_count > usable_run_count`;
- `usable_run_count > eligible_run_count`;
- recomputed coverage or recurrence differs from the candidate table beyond a
  documented floating-point tolerance;
- the distinct run-level fine-cell, group, or direction sets disagree with the
  candidate annotations; or
- stability or degree rows fail a one-to-one join to a passing context.

### Figure-data integrity

- the Panel A grid is not exactly 15 × 7 = 105 rows;
- a nonpassing tile contains an ACAT value or rank;
- a passing tile lacks a finite q value in `(0, 0.05]`;
- circle-display flags disagree between the tile grid and detail table;
- an evidence cap or axis limit is selected independently per panel; or
- any displayed numeric label was calculated from rounded source values.

## Output package

Write to:

```text
results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas/
```

Planned files:

```text
phase18_case3_evidence_atlas.svg
phase18_case3_evidence_atlas.pdf
phase18_case3_evidence_atlas.png
phase18_case3_gene_summary.tsv
phase18_case3_gene_network_details.tsv
phase18_case3_evidence_atlas_plot_data.tsv
phase18_case3_evidence_atlas_caption.md
phase18_case3_evidence_atlas_methods.md
phase18_case3_evidence_atlas_manifest.tsv
phase18_case3_evidence_atlas_checks.tsv
phase18_case3_evidence_atlas_artifacts.tsv
phase18_case3_evidence_atlas_status.tsv
```

The manifest records source paths and hashes, script hashes, run timestamp,
software versions, figure dimensions, evidence cap, palette, font sizes, and
the 15/21/22 universe counts.

## Publication and accessibility specification

- Authoritative formats: SVG and PDF.
- Raster preview: PNG at 450 dpi.
- Initial canvas: 12 × 8 inches; adjust height only during final-size review,
  then freeze dimensions in the manifest.
- Typeface: one sans-serif family throughout.
- Minimum final-size text: 7 pt; panel titles 11–12 pt; main title 13–14 pt.
- Legends sit outside data regions and must not cover marks.
- Use redundant encodings: fill plus solid/dashed borders for circle-display
  status, and point shape plus color for sensitivity state.
- Confirm legibility in grayscale and common color-vision simulations.
- Verify that network yellow remains distinguishable through borders and text,
  not color alone.

## Interpretation limits required in caption and methods

The published package must state:

- Case 3 means outside core MitoCarta, not proven nonmitochondrial function.
- The `mito_extended` annotation is secondary and does not alter the case.
- “Top five” is a display cap; it is not an additional evidence threshold.
- A fixed broad network is reused across multiple fine-cell-type queries, so
  those query runs are repeated evidence contexts, not independent external
  replications.
- Aggregate P and q values are network-specific and were not pooled across
  networks in this figure.
- The atlas display order is descriptive and is not a new rank.
- Key-driver association in a Bayesian network supports prioritization but is
  not experimental proof of causal regulation.

## Completion criteria

Plan 1 is complete only when:

1. all planned tables and formats exist and are nonempty;
2. every blocking check passes;
3. the output status is `validated_complete`;
4. source and output SHA-256 hashes are recorded;
5. SVG/PDF remain vector, PNG metadata confirms 450 dpi, and the three formats
   show the same content;
6. manual final-size and accessibility review is documented; and
7. the caption and methods include every interpretation limit above.
