# Phase 18 Key-Driver Selection Process Figure Plan

## Status

**Implemented and validated:** 2026-08-15

The reproducible renderer is
[`plot_phase18_key_driver_selection_process.py`](../../../../scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_key_driver_selection_process.py).
The validated figure package is under
[`key_driver_selection_process`](../../../../results/figures/analysis/phase_18_key_driver_selection/key_driver_selection_process/),
including the [PNG preview](../../../../results/figures/analysis/phase_18_key_driver_selection/key_driver_selection_process/phase18_key_driver_selection_process.png),
[PDF](../../../../results/figures/analysis/phase_18_key_driver_selection/key_driver_selection_process/phase18_key_driver_selection_process.pdf),
and [SVG](../../../../results/figures/analysis/phase_18_key_driver_selection/key_driver_selection_process/phase18_key_driver_selection_process.svg).
All automated checks passed, and the final rendering was reviewed in color and
grayscale at its intended 183 mm width.

## Purpose

Create one publication-ready figure that summarizes the selection process in
[`key_driver_selection_process.md`](../../../phase_18_key_driver_selection/key_driver_selection_process.md).
The figure should answer three questions:

1. What is the starting evidence?
2. How do the three candidate gates reduce it?
3. How are passing candidates converted into the final top-five lists?

This is a descriptive workflow figure. It reports deterministic counts and
does not introduce a new statistical analysis.

## Main message

```text
95,557 explicit gene × run tests from 161 KDA calls
        ↓ aggregate within broad network and driver class
10,433 represented gene × broad-network × driver-class units
        ↓ coverage, support, and aggregate-q gates
78 passing candidate units
        ↓ rank separately in 7 networks × 2 driver classes
47 displayed gene × network positions
```

The last number is **47 displayed positions**, not 47 unique genes. A gene can
be displayed in more than one broad network. The 47 positions contain 25
unique gene symbols.

## Proposed figure

Use one landscape figure with three panels. A two-row layout will keep the
workflow readable at manuscript size:

```text
┌──────────────────────────────┬───────────────────────────────────────────┐
│ A. Starting evidence         │ B. All three gates are required           │
│ 161 calls                   │ 10,433 → 9,846 → 243 → 78             │
│ 95,557 gene × run rows     │          coverage  support  ACAT q          │
│ 6,149 tested genes          │                                           │
│       ↓ aggregate           │                                           │
│ 10,433 candidate units      │                                           │
├──────────────────────────────┴───────────────────────────────────────────┤
│ C. Rank within broad network × driver class; retain at most five     │
│ 78 candidates: 41 MT + 37 non-MT                                  │
│ 7 × 2 matrix: passing → displayed                                  │
│ Final: 47 displayed positions: 26 MT + 21 non-MT                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Panel A: starting evidence and change of unit

Show two connected blocks:

- **Run-level evidence:** 161 included `call_key_drivers()` calls, 95,557
  explicit gene × run rows, and 6,149 unique explicitly tested genes.
- **Candidate units represented in the TSV:** 10,433 unique combinations of
  `broad_network + key_driver + case_id`.

Place a labeled aggregation boundary between the blocks:

```text
Combine each gene's evidence across eligible runs within one broad network
```

Do not draw a proportional funnel between 95,557 and 10,433 because the
counting unit changes. Use equal-width process blocks and state the unit next
to every number.

### Panel B: the three candidate gates

Show the gates in the same order as the process document. The connecting
arrows report **conditional** retention counts:

| Stage | Candidate units retained | Removed at this displayed step | Conditional retention |
|---|---:|---:|---:|
| Represented in the TSV | 10,433 | — | — |
| Coverage `>= 0.80` | 9,846 | 587 | 94.4% |
| Also support count `>= 1` | 243 | 9,603 | 2.5% |
| Also aggregate ACAT q `<= 0.05` | 78 | 165 | 32.1% |

Add a bracket labeled **all three required (AND)**. The sequence is only a
clear way to show attrition; the final decision is the conjunction of the
three gates and does not depend on gate order.

Under the support and ACAT gates, include short definitions:

- support: at least one conservatively supporting run;
- ACAT q: cross-run combined P value after broad-network BH correction.

The 78 final units are 0.75% of the 10,433 represented candidate units.

### Panel C: ranking and top-five display

First split the 78 passing candidate units by driver class:

- **MT driver:** 41 candidate units, representing 20 unique genes;
- **non-MT driver:** 37 candidate units, representing 30 unique genes.

Then show a 7-row × 2-column matrix. Each cell should read
`passing → displayed`:

| Broad network | MT driver | non-MT driver |
|---|---:|---:|
| Astrocytes | 6 → 5 | 5 → 5 |
| Excitatory neurons | 13 → 5 | 21 → 5 |
| Inhibitory neurons | 11 → 5 | 5 → 5 |
| Microglia | 2 → 2 | 1 → 1 |
| OPCs | 3 → 3 | 4 → 4 |
| Oligodendrocytes | 2 → 2 | 1 → 1 |
| Vasculature cells | 4 → 4 | 0 → 0 |
| **Total** | **41 → 26** | **37 → 21** |

End with a prominent result block:

```text
47 displayed gene × network positions
26 MT + 21 non-MT; 25 unique gene symbols
```

State beside the matrix that ranking is performed separately in each
`broad_network + case_id` list using:

1. smaller `aggregate_acat_q`;
2. smaller `aggregate_acat_p`; and
3. alphabetical gene symbol.

Also state **up to five; no backfilling** so the cells with fewer than five
are interpreted correctly.

## Visual design

- Canvas: approximately 183 mm wide × 120–130 mm tall.
- Final text size: at least 7 pt; panel labels and main counts should be
  larger.
- Use a clean sans-serif font and bold panel labels `A`, `B`, and `C`.
- Use neutral gray/navy for the shared workflow and gate boxes.
- Use a colorblind-safe blue (`#0072B2`) for MT drivers and orange
  (`#E69F00`) for non-MT drivers.
- Repeat the class names in text; do not rely on color alone.
- Use pale gray for removed counts and darker text for retained counts.
- Use uniform box widths rather than a Sankey or area-scaled funnel.
- Do not add error bars or significance stars: every plotted value is an
  observed processing count, not an estimate.

## Authoritative input and calculations

Read only:

```text
results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv
```

The renderer should:

1. verify `schema_version = phase18_call_key_driver_returns_v1`;
2. count unique calls with `kda_run_id`;
3. count input rows and unique `key_driver` values;
4. deduplicate by `broad_network + key_driver + case_id`;
5. verify that the repeated aggregate fields are constant within each
   deduplicated unit;
6. calculate the conditional gate counts from `coverage_fraction`,
   `conservative_support_count`, and `aggregate_acat_q`;
7. verify that the final gate intersection equals
   `terminal_candidate_status == "driver_candidate"`;
8. derive the class, network, rank, and display counts from `case_id`,
   `within_case_rank`, and `top5_display`.

The renderer should not recompute run-level enrichment, ACAT P values, or BH
corrections. Those statistics are already stored in the TSV.

## Implementation plan

Create:

```text
scripts/figures/analysis/phase_18_key_driver_selection/
    plot_phase18_key_driver_selection_process.py
```

Use Python with Matplotlib. Build the workflow from vector-native rectangles,
arrows, text, and matrix cells so the PDF and SVG remain editable. Keep data
preparation separate from drawing:

1. load and validate the TSV;
2. build one small summary table for Panels A and B;
3. build one network × class table for Panel C;
4. run all numerical checks before creating the figure;
5. render the same layout to PNG, PDF, and SVG;
6. write the exact plotted values and validation checks beside the figure.

## Planned outputs

Write the figure package under:

```text
results/figures/analysis/phase_18_key_driver_selection/
    key_driver_selection_process/
```

Planned files:

```text
phase18_key_driver_selection_process.png
phase18_key_driver_selection_process.pdf
phase18_key_driver_selection_process.svg
phase18_key_driver_selection_process_plot_data.tsv
phase18_key_driver_selection_process_checks.tsv
phase18_key_driver_selection_process_caption.md
phase18_key_driver_selection_process_methods.md
phase18_key_driver_selection_process_status.tsv
```

Export the PNG at 450 DPI with a white background. Preserve text and shapes as
vectors in the PDF and SVG.

## Validation checklist

The script should fail before drawing if any of these checks fail:

- exactly 95,557 input rows and 104 columns;
- exactly 161 unique `kda_run_id` values;
- exactly 6,149 unique explicitly tested genes;
- no duplicate `kda_run_id + key_driver` rows;
- exactly 10,433 represented candidate units;
- repeated aggregate and ranking fields are constant within each candidate
  unit;
- sequential gate counts are 10,433 → 9,846 → 243 → 78;
- 78 passing units split into 41 MT and 37 non-MT;
- all 78 passing units satisfy all three numeric gate rules;
- no failing unit has `terminal_candidate_status = driver_candidate`;
- each `broad_network + case_id` list has at most five `top5_display = TRUE`
  units;
- displayed counts sum to 47, split into 26 MT and 21 non-MT;
- the 7 × 2 matrix matches the frozen counts above;
- the 47 displayed positions contain 25 unique gene symbols;
- all declared files are present and nonempty after rendering.

Finally, inspect the figure at its intended physical size in color and
grayscale. Check that units are readable, arrows do not imply a causal
relationship, and no label is clipped.

## Draft caption

**Phase 18 key-driver selection from run-level tests to top-five lists.**
Panel A shows 95,557 explicitly tested gene × run results from 161 included
KDA calls and their aggregation into 10,433 represented gene × broad-network
× driver-class units. Panel B applies the coverage, conservative-support,
and aggregate-ACAT-q gates; 78 units pass all three. Panel C ranks passing
candidates separately within each of seven broad networks and two driver
classes and retains at most five per list, yielding 47 displayed gene ×
network positions (26 MT and 21 non-MT; 25 unique gene symbols). Lists are not
backfilled when fewer than five genes pass all gates.
