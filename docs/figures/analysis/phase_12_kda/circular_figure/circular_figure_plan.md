# Visualizing Phase 12 KDA with NetWeaver

## What the NetWeaver `R/` directory contains

`untracked/NetWeaver/R/` is a package source directory, not a collection of
independent command-line plotting scripts. The `rc.*` files are low-level
functions that are meant to be composed in the order demonstrated by:

```text
untracked/NetWeaver/README.md
untracked/NetWeaver/examples/netweaver.Md
untracked/NetWeaver/vignettes/netweaver.Rmd
```

The key idea in that example is to treat any repeated analysis unit as a
"hypothetical chromosome." For Phase 12, the repeated units in the overview
are selected `broad_network`–`key_driver` pairs rather than genomic
coordinates.

The reproducible adapter is:

```text
scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R
```

It sources only NetWeaver's circular plotting functions. It deliberately does
not source `untracked/NetWeaver/R/fKDA.R` or rerun KDA. The validated Phase 12
analysis used the frozen, corrected engine at `scripts/NetWeaver/fKDA.R`; the
figure reads its published results.

## Phase 12 inputs

The default input is the validated production bundle:

```text
results/minerva_production/12_kda/
```

The figure uses:

| File | Visualization use |
|---|---|
| `kda_status.tsv` | Require phase status `validated_complete` |
| `kda_checks.tsv` | Require every Phase 12 validation check to pass |
| `kda_run_manifest.tsv` | Derive eligible-run and eligible-cell-type denominators |
| `kda_key_driver_summary.tsv` | Select recurrent drivers and obtain recurrence, tier, global-driver, adjusted-P, and fold-enrichment summaries |

The script writes figures outside the nine-file Phase 12 output bundle, under
`results/figures/analysis/phase12_kda/circular_figure/`.

## Run it

From the project root:

```bash
Rscript scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R
```

Useful options:

```bash
Rscript scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R \
  --input-dir results/minerva_production/12_kda \
  --netweaver-dir untracked/NetWeaver \
  --output-dir results/figures/analysis/phase12_kda/circular_figure \
  --basename phase12_kda_netweaver \
  --top-per-network 5
```

Show the full option list with:

```bash
Rscript scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R --help
```

The default run creates:

```text
results/figures/analysis/phase12_kda/circular_figure/
├── phase12_kda_circular.svg
├── phase12_kda_circular.png
└── phase12_kda_circular_plotted_data.tsv
```

The SVG is the editable vector figure. The PNG is 3600 by 3600 pixels at
300 dpi. The TSV records every selected row, raw value, denominator, plotted
fraction, capped evidence value, sector ID, and color.

## How Phase 12 maps to NetWeaver functions

| NetWeaver function | Phase 12 role |
|---|---|
| `rc.initialize()` | Register each selected network–driver pair as a hypothetical chromosome |
| `rc.plot.area()` | Create the circular canvas |
| `rc.plot.ideogram()` | Draw driver sectors, colored by broad network, and label genes |
| `rc.plot.histogram()` | Show significant-run recurrence as a height from 0 to 1 |
| `rc.plot.barchart()` | Show the composition of significant calls from primary strata versus secondary pools |
| `rc.plot.heatmap()` | Draw six normalized evidence tracks |
| `rc.plot.link()` | Connect occurrences of the same selected gene in different networks |
| `rc.plot.track.id()` | Place compact track keys at the top of the circle |

The other `rc.plot.*` functions are useful for coordinate-level genomic
features, trends, or intervals, but Phase 12's published KDA summaries do not
contain a natural genomic-position axis. A sunburst is also a poorer fit for
the main result because it would imply a strict hierarchy between primary and
pooled calls; the secondary pools are overlapping set-union summaries.

## Driver selection and track definitions

Within each broad network that produced at least one significant key driver,
the default figure selects five rows in this deterministic order:

1. decreasing `significant_runs`;
2. increasing `minimum_adjusted_p_value`;
3. decreasing `maximum_fold_enrichment`; and
4. alphabetical `key_driver`.

The circular tracks run from outside to inside:

| Key | Quantity | Definition |
|---|---|---|
| `R` | All-run recurrence | `significant_runs / eligible_runs` within the same broad network |
| `T` | Tier composition | Primary and secondary-pool contributions to that driver's significant calls |
| `P` | Primary recurrence | `primary_runs / eligible_primary_runs` |
| `S` | Pooled recurrence | `secondary_runs / eligible_secondary_runs` |
| `C` | Cell-type coverage | `fine_cell_types / eligible_fine_cell_types` |
| `G` | Global-driver share | `global_calls / significant_runs` |
| `Q` | Adjusted-P evidence | `min(-log10(minimum_adjusted_p_value), 25) / 25` |
| `FE` | Fold-enrichment evidence | `min(log2(maximum_fold_enrichment), 12) / 12` |

`R` is a bar-height track. `T` is a two-color stacked composition track.
`P` through `FE` use the same light-to-dark 0-to-1 heat scale. Exact values
remain in `phase12_kda_circular_plotted_data.tsv`; caps affect display only.

The eligible-run denominators are essential. Raw recurrence counts are not
directly comparable across broad networks because the neuronal networks
contain many more fine cell types and therefore many more Phase 12 runs than,
for example, OPCs or oligodendrocytes.

## Interpretation

- A sector is a network-specific key-driver summary, not a chromosome.
- A darker or taller recurrence track means the driver was called in a larger
  fraction of eligible analyses for that same network.
- A center link means that the same gene was selected in more than one broad
  network. It is not a Bayesian-network edge and does not imply an interaction
  between cell classes.
- `global_key_driver` is NetWeaver's within-run reduction label. It does not
  mean a driver is global across all brain cell classes.
- Primary and secondary-pool calls are displayed separately because pooled
  signatures are overlapping set-union summaries, not independent
  replications.
- KDA reports enrichment in directed network neighborhoods. It does not by
  itself establish activation, inhibition, causal direction, or therapeutic
  actionability.
- CAMs and T cells appear in the validated Phase 12 manifest but had no
  eligible KDA runs, so they cannot contribute driver sectors. The figure
  states this explicitly rather than treating them as negative results.
