# Phase 18 non-MT driver evidence atlas and tables

## Status

**Revised and implemented:** 2026-08-15

This document describes the current evidence atlas for the selected
`non_mt_driver` genes.

Current implementation and outputs:

- [renderer](../../../../scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_non_mt_evidence_atlas.py)
- [PNG figure](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt.png)
- [PDF figure](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt.pdf)
- [SVG figure](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt.svg)
- [gene summary table](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_summary.tsv)
- [gene-network detail table](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_network_details.tsv)

The source of truth is
[`call_key_driver_returns.tsv`](../../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv),
schema `phase18_call_key_driver_returns_v1`. The atlas no longer depends on
legacy Phase 18 auxiliary tables.

## Goal

The atlas summarizes the evidence behind the genes displayed in the non-MT
driver circle. It answers three questions:

1. In which broad cell-type networks was each gene selected?
2. In how many KDA runs was each gene returned as significant, and how broad
   was that support?
3. Were its passing gene-network results stable when one fine cell type was
   omitted?

The atlas is descriptive. It reports the existing Phase 18 selection and does
not create another score or change which genes pass.

## Analysis universe

The selected-gene universe is derived from `top5_display = TRUE` for
`case_id = non_mt_driver` in the canonical return table. It contains 15 unique
genes across 21 displayed gene-network contexts:

```text
ANKRD11, APOE, ATP6V1F, DYNLT1, FTL, LAMTOR5, LAPTM4A, NCOA1,
RPL11, RPL15, RPL38, RPLP1, RPS13, RPS15, SELENOW
```

These genes have 22 total passing gene-network contexts. The additional
passing context is RPS15 in Excitatory neurons, which passed selection but was
ranked 20 and therefore was not among that network's five displayed genes.

All 15 genes are outside the fixed 1,136-gene core MitoCarta inventory. A
separate marker identifies membership in the broader mitochondrial reference;
that annotation does not change the non-MT-driver definition.

## Figure design

### Panel A — network evidence matrix

Panel A remains unchanged.

- Rows are the 15 selected genes.
- Columns are the seven broad cell-type networks.
- A filled tile means the gene-network context passed all selection gates.
- Fill encodes capped `-log10(aggregate_acat_q)`.
- The tile number is the within-network non-MT-driver rank.
- A solid border marks a context shown in the circle's top five.
- A dashed border marks a passing context below the five-gene display cap.
- A diamond beside a symbol marks membership in the broader mitochondrial
  reference.

Panel A is gene-by-broad-network. It should not be interpreted as a run count.

### Panel B — run occurrence and evidence breadth

Panel B is revised to answer the main follow-up question directly: for each
selected gene, in how many KDA runs was it returned as a significant key
driver?

Run counts use all included `non_mt_driver` KDA calls in which that gene was
explicitly tested. They are not restricted to the gene's passing broad-network
contexts. The denominator therefore varies by gene because a gene need not be
tested in every KDA call.

Panel B contains six aligned tracks.

#### 1. Significant KDA runs / tested runs

```text
significant_kda_run_count
  = number of explicitly tested runs with
    significant_by_call_key_drivers = TRUE

explicitly_tested_run_count
  = number of included runs containing an explicit tested row for the gene
```

The label is shown as `significant/tested`, for example `29/84` for RPL11.
This is the direct count of how often `call_key_drivers()` returned the gene as
significant.

#### 2. Conservative-support runs / tested runs

```text
conservative_supporting_run_count
  = number of explicitly tested runs with conservative_support = TRUE
```

Conservative support is stricter than a significant KDA return. It additionally
requires at least two other query genes, enrichment greater than 1, and final
run q at most 0.05. The label is shown as `support/tested`, for example `25/84`
for RPL11.

This track separates raw significant occurrence from the evidence actually
used by the conservative Phase 18 aggregation. For these selected genes,
conservative-support runs are always a subset of significant KDA runs.

#### 3. Supporting fine cell types

```text
supporting_fine_cell_type_count
  = number of distinct fine_cell_type values among conservative-support runs
```

The current selected-gene range is 1–18, so the figure label reads
`observed range 1–18`. The upper value is the observed maximum among the 15
selected genes, not the theoretical maximum: the 161 included calls span 34
distinct fine cell types. This track indicates biological breadth and prevents
a large run count from being mistaken for support across many cell types.

#### 4. Passing broad networks

```text
passing_broad_network_count
  = number of broad networks in which the gene has
    terminal_candidate_status = driver_candidate
```

Maximum possible value: 7. A gene can contribute at most one candidate result
per broad network because the final candidate table has one aggregated row per
gene-by-broad-network combination.

#### 5. Supporting sex/APOE groups

```text
supporting_group_count
  = number of distinct signature_group values among conservative-support runs
```

Maximum possible value: 6. This is a breadth summary, not an interaction test.

#### 6. Supporting AD directions

```text
supporting_direction_count
  = number of distinct signature_direction values among
    conservative-support runs
```

Maximum possible value: 2 (`AD_up_mito` and `AD_down_mito`). This shows whether
support is limited to one query direction or appears in both.

The revised Panel B intentionally does not repeat the best aggregate ACAT q
value because Panel A already shows network-specific aggregate q evidence.
Keeping run occurrence and breadth separate from q avoids implying a new
combined ranking.

### Panel B reference counts

Across the 15 selected genes, the current canonical table contains:

- 830 explicitly tested gene-by-run rows;
- 149 significant KDA returns; and
- 135 conservative-supporting runs.

These totals count gene-by-run rows, not unique KDA calls. The complete Phase
18 input contains 161 included KDA calls; one call can test and return multiple
selected genes.

### Panel C — network stability

Panel C shows the current leave-one-fine-cell-type-out diagnostics for every
passing gene-network context:

- `stability_candidate_fraction`: fraction of assessable omissions for which
  the gene remained a driver candidate; and
- `stability_worst_rank`: worst within-case rank across assessable omissions,
  capped at 25 in the plot.

Points retain the broad-network colors used in Panel A. An `x` means stability
was not assessable. Values are shown separately by network and are not pooled
into a gene-wide inferential score.

The former degree-matched robustness track is omitted because it is not
available in the current canonical return table and cannot be reproduced from
that table alone.

## Companion tables

### Gene summary

`phase18_evidence_atlas_non_mt_gene_summary.tsv` contains one row per selected gene. Important
Panel B fields are:

| Column | Unit | Meaning |
|---|---|---|
| `explicitly_tested_run_count` | gene | Included KDA runs in which the gene was explicitly tested |
| `significant_kda_run_count` | gene | Tested runs that returned the gene as significant |
| `significant_kda_run_fraction` | gene | Significant runs divided by tested runs |
| `conservative_supporting_run_count` | gene | Tested runs meeting conservative-support criteria |
| `conservative_supporting_run_fraction` | gene | Conservative-support runs divided by tested runs |
| `significant_fine_cell_type_count` | gene | Distinct fine cell types with a significant KDA return |
| `supporting_fine_cell_type_count` | gene | Distinct fine cell types with conservative support |
| `passing_broad_network_count` | gene | Broad networks in which the gene passed final selection |
| `supporting_group_count` | gene | Sex/APOE groups represented among conservative-support runs |
| `supporting_direction_count` | gene | AD directions represented among conservative-support runs |

The table also records the exact sets of networks, fine cell types, groups, and
directions, plus the best and worst aggregate q values across each gene's
passing network contexts.

### Gene-network details

`phase18_evidence_atlas_non_mt_gene_network_details.tsv` contains one row for each of the 22
passing gene-by-broad-network contexts. It records:

- circle-display status and within-case rank;
- eligible and usable run counts, coverage, and conservative support;
- aggregate ACAT P and q values; and
- leave-one-fine-cell-type stability diagnostics.

This table is the auditable source for Panels A and C. The gene summary is the
auditable source for Panel B.

## Implementation

Run from the repository root:

```bash
python -B scripts/figures/analysis/phase_18_key_driver_selection/plot_phase18_non_mt_evidence_atlas.py \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt \
  --png-dpi 450 \
  --visual-review-status complete
```

The script reads the canonical return table, validates the fixed selection
universe, creates the tables, renders PNG/PDF/SVG outputs, writes caption and
methods files, and replaces the complete output package atomically.

## Validation requirements

Generation must stop if any blocking check fails. Current targets are:

- input: 95,557 rows, 104 columns, 161 included calls, 6,149 tested genes;
- selected universe: 15 genes, 21 displayed contexts, 22 passing contexts;
- Panel A grid: 105 unique gene-network cells;
- Panel B: 830 tested rows, 149 significant returns, 135 conservative-support
  rows, with `support <= significant <= tested` for every gene;
- every displayed rank is at most 5;
- every passing aggregate q is in `(0, 0.05]`;
- PNG is 5,400 × 3,600 pixels at 450 DPI;
- PDF and SVG are nonempty vector outputs; and
- final-size color and grayscale review is complete.

The current package passes all 27 recorded checks in
[`phase18_evidence_atlas_non_mt_checks.tsv`](../../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_checks.tsv).
