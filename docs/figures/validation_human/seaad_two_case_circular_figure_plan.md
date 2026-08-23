# SEA-AD MT and Non-MT Circular Figures

> **Historical figure specification (superseded 2026-08-23):** The generated
> assets were not rebuilt for the coverage-0.80/q-0.05 selection-only rerun.
> Current analytical results are in
> [vh09_vh10_execution_summary.md](../../validation_human/vh09_vh10_execution_summary.md).


## Status

**Implemented and validated on 2026-08-20.**

Figure/package ID: `seaad_two_case_circular`

## Purpose

Produce two data-bound circular figures from the independently frozen SEA-AD
key-driver selection:

1. `mt_driver`: core-MitoCarta key drivers; and
2. `non_mt_driver`: key drivers outside the frozen core-MitoCarta set.

The figures deliberately reuse the visual grammar of the Phase 18 circular
figures while preserving SEA-AD-specific testability. Each broad-network/class
list has five fixed display slots, but only passing candidates are shown;
failing genes never backfill an unused rank.

## Main message

> SEA-AD selected eight MT and five non-MT network–gene units. The evidence is
> concentrated in excitatory and inhibitory neuronal networks, with one
> additional non-MT driver in oligodendrocytes; networks with no included KDA
> run are shown as unavailable rather than as negative results.

These are SEA-AD selection figures, not overlap figures. They must not read or
display ROSMAP candidate identities or rediscovery outcomes.

## Relationship to the Phase 18 figures

Reference implementation:

- `results/figures/analysis/phase_18_key_driver_selection/two_case_circular/`
- `scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_two_case_circular.R`

The SEA-AD figures retain:

- the exact seven-network order and color palette;
- five fixed slots per network;
- the same clockwise geometry, slot gaps, and network gaps;
- navy radial bars for `-log10(aggregate_acat_q)`, capped at 15;
- repeated-gene center links;
- the mtDNA dot on the MT figure;
- the extended-mitochondrial-reference diamond on the non-MT figure; and
- ranks based on aggregate q, aggregate P, then symbol, with no backfill.

The required SEA-AD extension is a truthful distinction between:

- `no_passing_candidate`: included KDA runs existed, but no gene passed all
  candidate gates; and
- `not_testable_no_included_runs`: the broad network had no included SEA-AD
  KDA run.

Those states must differ by fill, border/line style, and direct text—not by
color alone.

## Frozen selection contract

The canonical display authority is:

```text
results/validation_human/10_seaad_kda_rediscovery/
  10c_seaad_selection/seaad_top5.tsv
```

It is interpreted only for:

```text
query_rule_id = phase18_parity_query
result_tier_id = phase18_parity_query__min3_all
```

The frozen selection contains:

| Quantity | Value |
|---|---:|
| Network × class lists | 14 |
| Ranked lists | 5 |
| Testable lists with no passing candidate | 5 |
| Not-testable lists with no included runs | 4 |
| Selected network–gene–class units | 13 |
| MT units | 8 |
| Non-MT units | 5 |
| Unique selected symbols | 11 |

All 13 passing units are displayed because no SEA-AD list contains more than
four passing genes.

### MT figure

| Broad network | Displayed genes in rank order |
|---|---|
| Excitatory neurons | MT-CO2, MT-CYB, MT-ND4, MT-ATP6 |
| Inhibitory neurons | MT-CO2, MT-ND5, MT-CO3, MT-CYB |
| Astrocytes, Microglia, Oligodendrocytes | no passing candidate |
| OPCs, Vasculature | no included KDA run |

The eight units comprise six unique genes. Every displayed MT unit is
mtDNA-encoded. MT-CO2 and MT-CYB each recur in two networks, producing exactly
two center links.

### Non-MT figure

| Broad network | Displayed genes in rank order |
|---|---|
| Excitatory neurons | HGSNAT |
| Inhibitory neurons | BEX3, RPS27A, RPL30 |
| Oligodendrocytes | KANSL1L |
| Astrocytes, Microglia | no passing candidate |
| OPCs, Vasculature | no included KDA run |

The five units are five unique genes, so the non-MT circle has no center link.
Only RPS27A belongs to the frozen extended mitochondrial reference.

## Visual design

### Canvas and geometry

- Canvas: 12 × 7.2 inches.
- Export: SVG and PDF vectors plus 5400 × 3240 PNG at 450 DPI.
- Left circular panel: 60% of canvas width.
- Right compact legend: 40% of canvas width.
- Seven network blocks × five ranks = 35 fixed slots per figure.
- Start angle: 90 degrees; proceed clockwise.
- Gap between network blocks: 6 degrees.
- Gap between slots within a network: 1 degree.
- Score track radii: 0.62–0.94.
- Reference circles: evidence values 5, 10, and 15.
- Outer network band radii: 0.98–1.07.
- Gene-label radii by rank: 1.12, 1.23, 1.34, 1.23, 1.12.
- Network-label radius: 1.51.

Use a compact internal heading (`SEA-AD • MT drivers` or
`SEA-AD • Non-MT drivers`) so the presentation slide can keep its title and
headline editable.

### Network colors

Use the existing colorblind-aware Phase 12/18 mapping:

| Network | Color |
|---|---|
| Astrocytes | `#009E73` |
| Excitatory neurons | `#E69F00` |
| Inhibitory neurons | `#0072B2` |
| Microglia | `#CC79A7` |
| OPCs | `#56B4E9` |
| Oligodendrocytes | `#F0E442`, with a dark outline |
| Vasculature | `#D55E00` |

### Slot and evidence grammar

| State | Encoding |
|---|---|
| Ranked candidate | pale score track plus navy evidence bar |
| Unused rank after a shorter passing list | light gray |
| Testable, no passing candidate | medium-light solid gray; direct label |
| No included KDA run | darker gray with dashed/crossed treatment; direct label |

Bar height is:

```text
min[-log10(aggregate_acat_q), 15] / 15
```

Both figures must use the same scale. Excitatory MT-CO2 is the only SEA-AD
unit whose displayed score is capped.

Center curves join the same displayed gene across different broad networks
within one driver class. They are recurrence links, not Bayesian-network
edges. Link construction anchors the occurrence with the greatest uncapped
evidence and joins it to every other occurrence.

## Authoritative inputs

| Purpose | File |
|---|---|
| VH10C completion and counts | `results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv` |
| Frozen display rows | `.../10c_seaad_selection/seaad_top5.tsv` |
| Complete list statuses | `.../10c_seaad_selection/seaad_list_status.tsv` |
| Candidate-gate checks | `.../10c_seaad_selection/selection_checks.tsv` |
| Independent selection freeze | `.../10c_seaad_selection/seaad_selection_freeze.tsv` |
| Registered compact-result hashes | `.../10c_seaad_selection/artifacts.tsv` |
| SEA-AD run counts by network | `.../10a_inputs/seaad_kda_run_manifest.tsv` |
| SEA-AD selection settings/order | `scripts/validation_human/seaad_phase18_validation_config.yml` |
| Driver annotation markers | `results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz` |

The Phase 18 annotation is a shared technical reference, not a candidate list.
No VH09 or VH10D candidate/overlap table enters these figures.

The registered full `seaad_candidate_summary.tsv.gz` is absent locally. It is
not required to render the already-frozen top lists. The figure package must
say that it validates the compact frozen display contract; it must not claim
to rederive or rerank all 38,788 SEA-AD candidate units.

## Implementation

Renderer:

```text
scripts/figures/validation_human/plot_seaad_two_case_circular.py
```

Automated test:

```text
tests/validation_human/test_seaad_two_case_circular.py
```

Output directory:

```text
results/figures/validation_human/seaad_two_case_circular/
```

The package contains 13 files:

```text
seaad_mt_driver_circular.png
seaad_mt_driver_circular.pdf
seaad_mt_driver_circular.svg
seaad_non_mt_driver_circular.png
seaad_non_mt_driver_circular.pdf
seaad_non_mt_driver_circular.svg
seaad_two_case_circular_plot_data.tsv
seaad_two_case_circular_links.tsv
seaad_two_case_circular_caption.md
seaad_two_case_circular_methods.md
seaad_two_case_circular_checks.tsv
seaad_two_case_circular_artifacts.tsv
seaad_two_case_circular_status.tsv
```

The renderer writes to a staging directory, validates it, and atomically
publishes the complete directory. The artifact manifest hashes the 11 payload
files plus authoritative inputs and the renderer. It does not hash itself or
the later-written status file.

The canonical package was rendered after manual review of both panels in
color and grayscale. Its status records `validation_status =
validated_complete` and `visual_review_status = complete`.

## Automated validation contract

Publication is blocked unless:

- VH10C reports `validated_complete` and zero failed checks;
- the compact VH10C files match their registered SHA-256 values;
- the freeze records `rosmap_candidate_files_read = False`;
- exactly 14 network/class lists are present in the frozen list-status table;
- the top-list file has 22 rows: 13 ranked rows and nine sentinel rows;
- ranked rows contain 8 MT and 5 non-MT units and 11 unique symbols;
- every ranked row has coverage at least 0.80, conservative support at least
  one, aggregate q at most 0.05, and a continuous stored rank;
- the display cap is five and no list is backfilled;
- the fixed plot table contains 70 rows partitioned as 13 ranked, 12 unused
  ranks, 25 no-passing slots, and 20 not-testable slots;
- the recurrence table contains exactly two MT links and zero non-MT links;
- all eight MT units are core-MitoCarta and mtDNA encoded;
- all five non-MT units are outside core MitoCarta, with only RPS27A marked as
  an extended-reference member;
- all six image files exist and are nonempty;
- PNG dimensions and embedded resolution are correct;
- PDF and SVG signatures are valid, with searchable SVG text and vector paths;
- every declared artifact hash validates; and
- the final status is written last and reports `validated_complete` only after
  completed color and grayscale review.

## Interpretation guardrails

1. MT/non-MT classifies the candidate driver gene, not the DEG query.
2. Gray slots do not represent genes that narrowly missed the threshold.
3. A no-passing list had analyzable KDA runs but no passing candidate.
4. A not-testable list had no included KDA run and is unavailable evidence.
5. Center links show recurrence of one selected symbol across networks; they
   are not regulatory or Bayesian-network edges.
6. Bar height is capped display evidence, not an effect size.
7. “Top five” is a maximum, not a requirement to show five genes.
8. These figures do not show ROSMAP rediscovery or causal validation.

## Draft caption

**SEA-AD MT and non-MT key-driver candidates across broad brain-cell
networks.** Each circle shows one frozen SEA-AD driver class. Within each broad
network, up to five genes passing the 80% coverage, conservative-support, and
aggregate ACAT q ≤ 0.05 gates are displayed in rank order. Navy bar height is
`-log10(aggregate ACAT q)` on a common scale capped at 15. Outer colors denote
broad networks. Center curves connect repeated displayed genes across
networks and are not network edges. Dots mark mtDNA-encoded MT genes; diamonds
mark non-MT genes in the extended mitochondrial reference. Solid gray slots
mark testable lists with no passing candidate, whereas dashed/crossed slots
mark networks with no included KDA run. Failing genes were not used as
backfills.

## Draft source line

```text
Source: validated SEA-AD VH10C frozen key-driver lists; shared Phase 18 gene annotation and broad-network display scaffold.
```
