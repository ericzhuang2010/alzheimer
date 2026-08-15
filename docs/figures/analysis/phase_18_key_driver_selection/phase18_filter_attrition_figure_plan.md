# Phase 18 figure plan: gene attrition across the five key-driver filters

## Status and purpose

**Status:** Implemented and validated on 2026-08-14  
**Prepared:** 2026-08-14

The reproducible renderer is
[plot_phase18_filter_attrition.py](../../../../scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_filter_attrition.py).
The validated figure package is under
[filter_attrition](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/),
including the [PNG preview](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition.png),
[SVG](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition.svg),
[PDF](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition.pdf),
[plotted data](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition_plot_data.tsv),
[membership audit](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition_membership.tsv.gz),
and [terminal status](../../../../results/figures/analysis/phase_18_key_driver_selection/filter_attrition/phase18_filter_attrition_status.tsv).

The package contains exactly 10 declared outputs. All automated blocking
checks passed. The rendered figure was manually reviewed at final size in
color, grayscale, and a deuteranopia simulation; no label clipping or
panel-boundary overlap remained in the approved rendering.

This document specifies one publication-ready figure showing how Phase 18
evidence is reduced by the five prespecified key-driver filters. The figure
must keep the three cases defined in the
[unified key-driver selection proposal](../../../phase_18_key_driver_selection/unified_key_driver_selection_proposal.md)
separate:

1. **Case 1 — MT-related and in query:** the driver is one of the 1,136 core
   MitoCarta genes and belongs to that run's query;
2. **Case 2 — MT-related and not in query:** the driver is one of the 1,136
   core MitoCarta genes but does not belong to that run's query; and
3. **Case 3 — not MT-related:** the driver is outside the 1,136-gene core
   MitoCarta inventory.

The central question is:

> How much evidence remains after each Phase 18 filter, and at which filter
> are genes in each of the three cases removed?

The figure is descriptive. It visualizes deterministic counts from the
validated Phase 18 bundle; it does not perform a new statistical test or
change candidate selection.

## Bottom-line design

Create one four-panel figure:

- **Panel A:** the shared Filter 1 run-scope gate and a simple map of all five
  filters;
- **Panel B:** Case 1 attrition through Filters 2–5;
- **Panel C:** Case 2 attrition through Filters 2–5; and
- **Panel D:** Case 3 attrition through Filters 2–5.

Panels B–D must use the same layout and definitions. Distinct gene symbols
are the visually primary counts after aggregation. Smaller secondary labels
show gene × broad-network × case aggregate counts so the figure remains
reconcilable with the authoritative Phase 18 funnel.

Do not create three separate figures. The three cases must remain visible
together, while still being clearly separated.

## Essential counting-unit rule

The five filters do not all operate on the same type of record. Calling every
number a “gene count” would be incorrect.

| Filter | What is counted | Plain-language meaning |
|---|---|---|
| Filter 1 | Run slots | Which fine-cell-type × primary sex/APOE × direction analyses are usable? |
| Filter 2 | Gene × included-run opportunities | For one gene in one included run, was a valid KDA result available? |
| Filter 3 | Gene × broad-network × case aggregates | Does the gene have at least one conservatively supporting run in this network and case? |
| Filter 4 | Gene × broad-network × case aggregates | Was the gene usable in at least 80% of its eligible case-runs? |
| Filter 5 | Gene × broad-network × case aggregates | Does the combined ACAT result pass gene-level false-discovery-rate correction? |

Here, a **run slot** is one fine cell type, one primary sex/APOE group, and one
AD direction. A **gene × run opportunity** is one chance to test a gene in one
run. **KDA**, or key driver analysis, asks whether the genes near or downstream
of a candidate in an inferred network contain more query genes than expected.
The **query** is the run-specific set of core mitochondrial genes altered in
AD. A **gene × network aggregate** combines that gene's run-level evidence
inside one broad network and one case.

This difference must be visible in the figure:

```text
Filter 1              Filter 2                 Filters 3–5
run slots    ->   gene × run results   ->   gene × network × case results
                                      aggregation boundary
```

Do not connect differently scaled widths across this boundary as if they were
the same population. In particular, do not use a single Sankey ribbon whose
width flows numerically from 161 runs to 1,299,782 usable gene × run results.

## The five filters in plain language

### Filter 1: keep the common Phase 12 run set

Start with the 648 possible primary directional run slots:

```text
54 fine cell types
× 6 primary sex/APOE groups
× 2 directions, AD-up and AD-down
= 648 run slots
```

Keep only validated Phase 12 runs with at least 10 effective query genes.
This leaves 161 included runs. Filter 1 occurs before genes are assigned to a
case, so it is shared by Cases 1–3 and must be shown once rather than repeated
three times.

### Filter 2: require a usable gene-level result

For each included run and each gene in the matching broad-network opportunity
set, determine whether a valid enrichment P value is available.

- An explicit KDA result is usable.
- An implicit or explicit zero-overlap result with P = 1 is also usable; it is
  valid evidence of no enrichment.
- A gene absent from the run background has no test and is stored as missing.
- An invalid calculation is missing and would be a blocking validation issue.

Filter 2 removes unusable **gene × run results**, not necessarily the entire
gene. A gene with some missing runs may still proceed, and Filter 4 later asks
whether its usable-run coverage reaches 80%.

### Filter 3: require at least one conservatively supporting run

Within one gene × network × case result, at least one run must satisfy all of
the following:

- effective query size is at least 10;
- the driver reaches at least two other query genes;
- fold enrichment is greater than 1; and
- the recalculated run-level q value is at most 0.05.

For Case 1, “other query genes” excludes the driver itself. A valid run that
does not meet this conservative-support definition still contributes its P
value to ACAT, but the gene cannot become a final driver candidate unless at
least one run passes this filter.

### Filter 4: require at least 80% coverage

Coverage is the fraction of eligible case-runs in which the gene has a usable
result. Require coverage of at least 0.80. This is a completeness requirement,
not a significance test.

### Filter 5: require significant combined evidence

ACAT combines the gene's usable run-level P values within a broad network and
case. The resulting ACAT P values are adjusted for testing many genes. Require
the gene-level ACAT q value to be at most 0.05.

A **q value** is a P value adjusted for multiple testing. It limits the
expected false-discovery proportion among the selected results.

## Authoritative inputs

Read only the validated production bundle:

```text
results/minerva_production/18_key_driver_selection/
```

Required files are:

| File | Figure use |
|---|---|
| `key_driver_status.tsv` | Require one row with `validation_status = validated_complete` |
| `key_driver_artifacts.tsv` | Verify hashes and byte counts for the scientific inputs used by the figure |
| `key_driver_case_manifest.tsv` | Freeze the three case IDs, order, labels, and exact definitions |
| `key_driver_filter_funnel.tsv` | Authoritative Filter 1 counts, Filter 2 overall counts, and sequential Filter 3–5 aggregate counts |
| `key_driver_candidate_tests.tsv.gz` | Derive Filter 2 counts separately for Cases 1–3 |
| `key_driver_gene_case_summary.tsv.gz` | Derive distinct-gene retention and first-failure membership for Filters 3–5 |
| `key_driver_candidates.tsv` | Confirm the final 109 gene–network candidate rows |

The renderer must verify the recorded input hashes before drawing. It must not
read Phase 12 result rows directly or recalculate KDA, ACAT, q values, coverage,
or conservative support.

## Frozen production checkpoints

These values define the expected first rendering. The plotted-data table and
figure checks must reproduce them exactly.

### Filter 1: shared run-scope count

| Entering run slots | Included runs | Excluded run slots | Retained |
|---:|---:|---:|---:|
| 648 | 161 | 487 | 24.8% |

The 161 included runs cover seven broad networks. CAMs and T cells have no
included Phase 18 runs, but they remain represented by explicit no-result
statuses elsewhere in the Phase 18 bundle.

### Filter 2: case-specific gene × run opportunities

| Case | Opportunities | Usable results | Unusable/missing results | Retained |
|---|---:|---:|---:|---:|
| Case 1: MT-related and in query | 7,073 | 7,073 | 0 | 100.0% |
| Case 2: MT-related and not in query | 112,484 | 98,790 | 13,694 | 87.8% |
| Case 3: not MT-related | 1,343,593 | 1,193,919 | 149,674 | 88.9% |
| **All cases** | **1,463,150** | **1,299,782** | **163,368** | **88.8%** |

The 163,368 missing results are genes absent from a run-specific background.
The validated bundle contains zero invalid Filter 2 calculations.

Usable results include both tested enrichment values and valid P = 1 null
results. Therefore, the figure must not label all usable results as
“significant tests.”

### Filters 3–5: distinct genes remaining within each case

A distinct gene is counted once per case at each stage, even if it appears in
several broad networks. It remains at a stage when at least one of its
network-specific aggregates remains at that stage.

| Case | Before Filter 3 | After Filter 3 | After Filter 4 | After Filter 5 |
|---|---:|---:|---:|---:|
| Case 1: MT-related and in query | 877 | 47 | 47 | 27 |
| Case 2: MT-related and not in query | 902 | 34 | 33 | 18 |
| Case 3: not MT-related | 11,319 | 150 | 143 | 30 |

The corresponding numbers of distinct genes first removed at each step are:

| Case | First removed at Filter 3 | First removed at Filter 4 | First removed at Filter 5 | Final genes retained |
|---|---:|---:|---:|---:|
| Case 1 | 830 | 0 | 20 | 27 |
| Case 2 | 868 | 1 | 15 | 18 |
| Case 3 | 11,169 | 7 | 113 | 30 |

“First removed” means the gene had at least one network-specific aggregate
entering the step but no aggregate remaining after that step. A gene that
fails in one network but passes in another remains in the distinct-gene count.

Do not add the final case-specific distinct-gene counts and call the result a
global unique-gene count. The same core MitoCarta gene can appear in both Case
1 and Case 2. The final bundle contains 57 unique symbols across all cases,
not 27 + 18 + 30 = 75 globally unique genes.

### Filters 3–5: authoritative gene–network aggregate counts

The smaller secondary labels in Panels B–D must report the authoritative
network-specific aggregate counts:

| Case | Before Filter 3 | After Filter 3 | After Filter 4 | After Filter 5 |
|---|---:|---:|---:|---:|
| Case 1 | 2,046 | 77 | 77 | 49 |
| Case 2 | 3,625 | 43 | 42 | 23 |
| Case 3 | 43,947 | 172 | 164 | 37 |
| **All cases** | **49,618** | **292** | **283** | **109** |

The first-removed aggregate counts are:

| Case | Filter 3 | Filter 4 | Filter 5 | Final candidate aggregates |
|---|---:|---:|---:|---:|
| Case 1 | 1,969 | 0 | 28 | 49 |
| Case 2 | 3,582 | 1 | 19 | 23 |
| Case 3 | 43,775 | 8 | 127 | 37 |

These aggregate counts are the authoritative additive funnel because a gene
can legitimately be a candidate in more than one broad network.

## Figure layout

Use a double-column landscape canvas, 183 mm wide by approximately 152 mm
tall. All text must remain at least 7 pt at final size.

### Panel A: shared scope and counting-unit map

Show a compact left-to-right flow:

```text
648 primary directional run slots
              |
       Filter 1: common run set
              |
      161 included + 487 excluded
              |
       branch into three cases
```

Under or beside this flow, show five labeled filter boxes with their native
counting units. Place a visible vertical divider between Filter 2 and Filter 3
labeled:

```text
Combine run-level evidence into gene × network × case results
```

Do not show causal arrows. These are data-processing arrows only.

### Panels B–D: one aligned attrition row per case

Each case panel should contain:

1. a Filter 2 horizontal bar split into usable and unavailable gene × run
   results, with exact counts and the retained percentage;
2. the aggregation-boundary marker;
3. an input tile showing distinct genes and gene–network aggregates entering
   Filter 3;
4. one tile each for Filters 3, 4, and 5, showing:
   - the large distinct-gene count remaining;
   - the smaller aggregate count remaining;
   - the number first removed at that filter; and
   - the conditional percentage retained from the preceding stage; and
5. a final label stating “genes retained in at least one broad network,” not
   merely “significant genes.”

The same positions and label hierarchy must be used in all three panels.
Exact counts, rather than box width, are the primary comparison because the
Case 3 universe is much larger than the Case 1 and Case 2 universes.

The image itself should show counts rather than thousands of individual gene
symbols. The companion membership table must preserve the exact gene and
network rows first removed at Filters 3, 4, or 5. This division keeps the
figure readable without hiding which records contributed to each count.

Recommended panel titles are:

- **B. Case 1 — MT-related and in query**
- **C. Case 2 — MT-related and not in query**
- **D. Case 3 — outside core MitoCarta**

Add the short parenthetical subtitle “self-overlap removed” to Case 1.

## Visual encoding

Use a restrained, color-vision-safe design:

| Element | Encoding |
|---|---|
| Case 1 | Okabe–Ito blue, `#0072B2` |
| Case 2 | Okabe–Ito bluish green, `#009E73` |
| Case 3 | Okabe–Ito reddish purple, `#CC79A7` |
| Evidence retained | Solid case color plus exact count |
| First removed/unavailable | Light gray fill with diagonal hatch and dark outline |
| Shared processing elements | Neutral charcoal and light gray |

Color must not be the only encoding. Case names, exact counts, panel position,
and hatch patterns must preserve meaning in grayscale.

Do not use:

- a rainbow or red–green palette;
- 3D funnels or perspective effects;
- area-scaled circles, whose sizes would obscure small surviving groups;
- significance stars;
- a continuous color scale for deterministic pass/fail status; or
- ribbons that imply Filter 1, Filter 2, and Filter 3 share a counting unit.

The count labels should use thousands separators. Percentages should use one
decimal place. Use `0`, not a blank cell, when no gene or aggregate is removed.

## Derived plotted-data contract

The renderer should publish one tidy plotted-data table with at least:

```text
panel_id
case_order
case_id
case_label
filter_number
filter_name
counting_unit
input_n
pass_n
first_removed_n
remaining_n
conditional_retained_fraction
distinct_gene_input_n
distinct_gene_first_removed_n
distinct_gene_remaining_n
source_file
source_report_type
source_summary_scope
derivation_rule
```

For Filters 1–2, fields that are not meaningful for the native unit must be
stored as missing, not zero.

Also publish a compressed membership table for Filters 3–5 with one row per
gene × broad-network × case aggregate and these fields:

```text
broad_network
case_id
current_symbol
conservative_support_pass
coverage_pass
aggregate_q_pass
first_failed_filter
terminal_candidate_status
```

This table allows a reader to identify which individual gene–network result
was first removed at each filter without trying to print thousands of gene
names inside the figure.

## Counting derivations

### Filter 1

Read the `native_filter`, `overall`, Filter 1 row from
`key_driver_filter_funnel.tsv`. Do not recalculate eligibility from Phase 12.

### Filter 2 by case

Group `key_driver_candidate_tests.tsv.gz` by `case_id` and count:

- total rows as opportunities;
- `usable_test = TRUE` as usable;
- `usable_test = FALSE` as unavailable;
- explicit, implicit-zero-overlap, absent-background, and invalid statuses as
  audit components.

The three case totals must sum exactly to the overall native Filter 2 row.

### Filters 3–5 aggregate attrition

Use the `sequential_candidate_funnel` rows at
`summary_scope = broad_network_case`. Sum aggregate row counts across broad
networks within each case. These sums are valid because a gene–network
aggregate belongs to exactly one broad network and case.

Do not sum the per-network distinct-gene fields. The same gene can occur in
multiple networks.

### Filters 3–5 distinct-gene attrition

Derive distinct-gene counts directly from
`key_driver_gene_case_summary.tsv.gz`:

1. group by case and current gene symbol;
2. treat a gene as remaining after Filter 3 if at least one network row has
   `conservative_support_pass = TRUE`;
3. treat it as remaining after Filter 4 if at least one network row passes
   conservative support and coverage;
4. treat it as remaining after Filter 5 if at least one network row passes
   conservative support, coverage, and aggregate q; and
5. define first removal by set difference between adjacent stages.

The operation is an “any network passes” summary within each case. It does not
replace the network-specific candidate definition.

## Statistical and interpretive rules

- Counts are exact properties of the validated bundle, not estimates. Error
  bars and confidence intervals are therefore not applicable.
- Do not run a hypothesis test comparing attrition percentages among cases.
  The cases have different biological definitions and different opportunity
  universes.
- Do not interpret a larger number of Case 3 removals as evidence that Case 3
  genes are biologically worse. Case 3 starts with a much larger gene universe.
- Do not call Filter 2 failures “non-significant genes.” They are unavailable
  gene × run results.
- Do not call Filter 3 failures “ACAT failures.” Filter 3 is the conservative
  supporting-run requirement.
- Do not call every final distinct gene a separate independent discovery. A
  gene may be retained in multiple networks, and the same core gene may occur
  in both Case 1 and Case 2.
- “Driver candidate” means supported network association under the Phase 18
  rules; it does not prove causal regulation of Alzheimer's disease or
  mitochondria.

## Proposed caption

**Phase 18 attrition across five key-driver filters.** Panel A shows the shared
run-scope gate: 161 of 648 primary sex/APOE-direction run slots were validated
and contained at least 10 effective query genes. Panels B–D show the three
prespecified cases separately. Filter 2 counts usable and unavailable gene ×
run results; valid zero-overlap results with P = 1 are counted as usable.
After run-level evidence is combined within broad network and case, the large
numbers show distinct gene symbols remaining after the conservative-support,
80% coverage, and ACAT q ≤ 0.05 filters. Smaller labels show the corresponding
gene × broad-network × case counts. Case 1 enrichment excludes the driver's
guaranteed self-overlap. Counts are exact and descriptive; differences in
attrition are not formal comparisons among cases.

## Implementation files and output organization

Proposed renderer:

```text
scripts/figures/analysis/phase_18_key_driver_selection/
  plot_phase18_filter_attrition.py
```

Proposed output directory:

```text
results/figures/analysis/phase_18_key_driver_selection/filter_attrition/
```

Required outputs:

```text
phase18_filter_attrition.svg
phase18_filter_attrition.pdf
phase18_filter_attrition.png
phase18_filter_attrition_plot_data.tsv
phase18_filter_attrition_membership.tsv.gz
phase18_filter_attrition_caption.md
phase18_filter_attrition_methods.md
phase18_filter_attrition_sources.tsv
phase18_filter_attrition_checks.tsv
phase18_filter_attrition_status.tsv
```

The SVG and PDF are the authoritative vector figures. Export the PNG at
300–450 dpi for review. Never use JPEG for this line-art figure.

The renderer must refuse to overwrite an existing validated output directory.
Write to a sibling staging directory, validate all files, and publish the
directory atomically.

## Automated validation checks

The figure package must fail validation unless all of the following pass:

1. the Phase 18 status is `validated_complete`;
2. the case manifest contains exactly the three ordered cases defined above;
3. Filter 1 reconciles as 648 = 161 + 487;
4. case-specific Filter 2 opportunities sum to 1,463,150;
5. case-specific usable Filter 2 results sum to 1,299,782;
6. case-specific unavailable Filter 2 results sum to 163,368;
7. Filter 2 contains zero invalid calculations;
8. every sequential Filter 3–5 row satisfies input = pass + first removed;
9. each next-step aggregate input equals the preceding aggregate pass count;
10. the case totals before Filter 3 sum to 49,618 aggregate rows;
11. the Filter 3, 4, and 5 aggregate survivor totals are respectively 292,
    283, and 109;
12. the final 109 rows match `key_driver_candidates.tsv` exactly by network,
    case, and current symbol;
13. the final distinct-gene counts are 27, 18, and 30 in Cases 1, 2, and 3;
14. the union across all final cases contains 57 unique symbols;
15. all plotted labels match the plotted-data table;
16. no field that is not applicable to Filters 1–2 is silently stored as zero;
17. the SVG and PDF contain vector text and shapes;
18. the PNG has the requested dimensions and resolution; and
19. source and output SHA-256 hashes are recorded.

## Manual review checklist

- [x] The shared Filter 1 panel is not repeated as three independent case
  counts.
- [x] The Filter 2 labels say gene × run results, not genes.
- [x] The aggregation boundary is obvious.
- [x] Panels B–D use identical structure and case order.
- [x] Large labels represent distinct genes; smaller labels represent
  gene–network aggregates.
- [x] First-removed counts and remaining counts are not confused.
- [x] Case 1 states that self-overlap was removed.
- [x] Zero removals are printed as `0`.
- [x] Text is readable at final manuscript size.
- [x] No labels are clipped in SVG, PDF, or PNG.
- [x] The figure remains interpretable in grayscale.
- [x] Color-vision-deficiency simulation preserves the three case identities.
- [x] The caption defines KDA, coverage, ACAT, and q value in plain language.
- [x] The figure does not imply causal regulation or formal case-to-case
  comparisons.

## Implementation sequence

1. [x] Freeze this figure plan and file names.
2. [x] Implement source-hash and status preflight checks.
3. [x] Build and validate the Filter 1 and Filter 2 native-unit summaries.
4. [x] Build and validate the case-specific Filter 3–5 aggregate funnel.
5. [x] Derive distinct-gene stage membership and first-removal sets.
6. [x] Write the plotted-data and membership tables before rendering.
7. [x] Render Panels A–D with shared styles and accessible encodings.
8. [x] Export SVG, PDF, and high-resolution PNG.
9. [x] Run automated package checks.
10. [x] Review the three formats at final size, in grayscale, and under a
    color-vision-deficiency simulation.
11. [x] Write checks and status last, then publish atomically.

## Completion criteria

This figure task is complete only when the one four-panel figure:

- shows all five filters with the correct native counting units;
- shows Cases 1, 2, and 3 separately;
- makes distinct-gene attrition directly readable for Filters 3–5;
- remains auditable against the network-specific aggregate funnel;
- reproduces every frozen production checkpoint above;
- passes automated and manual accessibility checks; and
- is accompanied by plotted data, membership, methods, caption, provenance,
  checks, and validated terminal status files.

All completion criteria were satisfied on 2026-08-14.
