# Phase 18 Two-Class Circular Figures

## Status

Implemented and validated from the current two-class Phase 18 results.

## Purpose

Generate one circular figure for each driver class:

1. `mt_driver`: core mitochondrial drivers
2. `non_mt_driver`: drivers outside the core mitochondrial set

Each figure shows up to five passing genes per broad network. Fewer than five
are shown when fewer genes pass the Phase 18 coverage, conservative-support,
and aggregate-q gates; failing genes are not used as backfills.

## Input

[`call_key_driver_returns.tsv`](../../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)

The renderer deduplicates the run-level table to one record per:

```text
broad_network + key_driver + case_id
```

It retains `terminal_candidate_status = driver_candidate`, ranks within broad
network and driver class by `aggregate_acat_q`, `aggregate_acat_p`, and gene
symbol, and displays ranks 1–5.

## Renderer

[`visualize_phase18_two_case_circular.R`](../../../../scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_two_case_circular.R)

The renderer validates the canonical schema, row count, run count, aggregate
fields, candidate gates, ranks, and display flags before drawing.

## Output directory

```text
results/figures/analysis/phase_18_key_driver_selection/two_case_circular/
```

The two figure basenames are:

```text
phase18_mt_driver_circular
phase18_non_mt_driver_circular
```

Each is exported as SVG, PDF, and 450-DPI PNG. The directory also contains the
exact plotted data, repeated-gene link table, caption, methods, checks, and
validation status.

## Visual encoding

- Outer band: broad-network identity using a colorblind-aware palette
- Navy radial bar: `-log10(aggregate_acat_q)`, capped at 15
- Gray center curve: the same displayed gene occurring in multiple networks
- Gray unused slot: fewer than five genes passed in that list
- MT figure dot: mtDNA-encoded gene
- Non-MT figure diamond: member of the extended mitochondrial reference

The legend is in a dedicated right-side panel. The plot center has no opaque
circle, so repeated-gene links remain visible.

## Reproduction

```bash
Rscript --vanilla \
  scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_two_case_circular.R \
  --input results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/two_case_circular \
  --top-per-network 5 \
  --evidence-cap 15 \
  --png-dpi 450
```
