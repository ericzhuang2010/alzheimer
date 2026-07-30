## 4. Why the circular figure uses the summary and manifest

The full result table has 10,172 significant driver rows. Drawing one sector
for every row would produce an unreadable figure and would repeat the same
network–driver combination many times.

The circular figure therefore uses two complementary files:

1. `kda_key_driver_summary.tsv` provides one compact row per
   broad-network–driver pair.
2. `kda_run_manifest.tsv` supplies the eligible-run denominators that are
   absent from the result-only summary.

It also reads:

- `kda_status.tsv`, to require `validated_complete`; and
- `kda_checks.tsv`, to require that every validation check passed.

It does not read the Phase 12 signature- or background-membership tables to
draw this overview, and it does not rerun KDA.

## 5. How the plotted rows are selected

### 5.1 Networks included

Only networks with at least one row in `kda_key_driver_summary.tsv` can
contribute a driver sector. Seven networks meet that condition:

```text
Astrocytes
Excitatory_neurons
Inhibitory_neurons
Microglia
OPCs
Oligodendrocytes
Vasculature_cells
```

CAMs and T cells have no eligible KDA run, so there is no defensible driver to
display for them. The figure states this at the bottom instead of displaying
an artificial zero.

### 5.2 Top-five selection within each network

The default figure selects five network-specific rows from each of the seven
result-producing networks.

Rows are sorted deterministically within a network by:

1. decreasing `significant_runs`;
2. increasing `minimum_adjusted_p_value`;
3. decreasing `maximum_fold_enrichment`; and
4. alphabetical `key_driver`.

The first five rows are retained.

This creates:

```text
7 networks × 5 drivers = 35 displayed sectors
```

This is a within-network selection. It ensures that smaller cell classes are
represented instead of allowing the neuronal networks, which have many more
eligible analyses, to occupy nearly the entire figure.

The complete list and its exact ordering are written to:

```text
results/figures/phase12_kda/phase12_kda_netweaver_plotted_data.tsv
```

## 6. How the eligible denominators are calculated

Raw `significant_runs` counts cannot be fairly compared across networks.
There are many more eligible neuronal analyses because there are many more
neuronal fine cell types.

The script starts with manifest rows satisfying:

```text
eligibility_status == "eligible"
```

It then counts eligible runs separately by broad network and analysis tier.
It also counts distinct fine cell types with at least one eligible run in each
network.

The actual denominators used in the current figure are:

| Broad network | Eligible primary runs | Eligible secondary runs | Eligible total runs | Eligible fine cell types |
|---|---:|---:|---:|---:|
| Astrocytes | 52 | 45 | 97 | 3 |
| Excitatory neurons | 212 | 206 | 418 | 14 |
| Inhibitory neurons | 164 | 203 | 367 | 21 |
| Microglia | 20 | 24 | 44 | 2 |
| OPCs | 15 | 15 | 30 | 1 |
| Oligodendrocytes | 14 | 15 | 29 | 1 |
| Vasculature | 12 | 24 | 36 | 2 |

For example, 38 significant Astrocyte calls and 38 significant Excitatory
neuron calls would not have the same recurrence meaning. The corresponding
denominators would be 97 and 418.

## 7. Every derived plotting value

For each selected network–driver row, the script adds the following raw
denominators and derived values to the plotted-data TSV.

### 7.1 Overall recurrence

```text
recurrence_fraction =
    significant_runs / eligible_runs
```

This is displayed as the height of track `R`.

It answers:

> In what fraction of this broad network's eligible Phase 12 analyses was
> this driver significant?

### 7.2 Primary recurrence

```text
primary_recurrence_fraction =
    primary_runs / eligible_primary_runs
```

This is heatmap track `P`.

### 7.3 Secondary-pool recurrence

```text
secondary_recurrence_fraction =
    secondary_runs / eligible_secondary_runs
```

This is heatmap track `S`.

### 7.4 Eligible fine-cell-type coverage

```text
fine_cell_coverage_fraction =
    fine_cell_types / eligible_fine_cell_types
```

This is heatmap track `C`.

It answers:

> In what fraction of fine cell types that had any eligible KDA analysis in
> this network was the driver reported at least once?

It does not show how many sex/APOE groups or directions supported the driver
within each fine cell type.

### 7.5 Global-driver call share

```text
global_call_fraction =
    global_calls / significant_runs
```

This is heatmap track `G`.

It answers:

> Among the runs that reported this driver, in what fraction did NetWeaver
> retain it as a global driver within that run?

Again, "global" is local to one KDA run and NetWeaver's reduction procedure.

### 7.6 Adjusted-P evidence strength

First calculate:

```text
minus_log10_minimum_adjusted_p =
    -log10(minimum_adjusted_p_value)
```

Then cap and normalize it:

```text
minimum_adjusted_p_strength =
    min(minus_log10_minimum_adjusted_p, 25) / 25
```

This is heatmap track `Q`.

The display cap prevents one extremely small P value from making all other
colors nearly indistinguishable. A value at the cap corresponds to an
adjusted P value of \(10^{-25}\) or smaller. The exact uncapped value is
retained in the plotted-data TSV.

This track uses the single smallest adjusted P value observed for the
network–driver pair. It is not an average evidence measure across runs.

### 7.7 Maximum fold-enrichment strength

First calculate:

```text
log2_maximum_fold_enrichment =
    log2(maximum_fold_enrichment)
```

Then cap and normalize it:

```text
maximum_fold_enrichment_strength =
    min(log2_maximum_fold_enrichment, 12) / 12
```

This is heatmap track `FE`.

A log2 value of 12 corresponds to a fold enrichment of 4,096. The current
selected values do not exceed this cap, but the cap keeps the rendering stable
for other choices of `--top-per-network`.

Like track `Q`, this uses the most extreme observed result, not an average
over supporting runs.

### 7.8 Primary-versus-secondary composition

Track `T` uses the raw significant-call counts:

```text
primary share   = primary_runs / significant_runs
secondary share = secondary_runs / significant_runs
```

The primary component is blue and the secondary-pool component is orange.

This track describes the composition of the calls that occurred. It does not
correct for the unequal numbers of primary and secondary opportunities.
Tracks `P` and `S` provide those denominator-corrected recurrence rates.

## 8. Worked example: Astrocyte `MT-CO2`

The plotted-data row for the Astrocyte `MT-CO2` sector starts from this Phase
12 summary:

| Field | Value |
|---|---:|
| `significant_runs` | 38 |
| `fine_cell_types` | 3 |
| `primary_runs` | 15 |
| `secondary_runs` | 23 |
| `global_calls` | 38 |
| `minimum_adjusted_p_value` | \(9.049202 \times 10^{-17}\) |
| `maximum_fold_enrichment` | 315.53 |

The manifest-derived denominators are:

| Denominator | Value |
|---|---:|
| Eligible primary runs | 52 |
| Eligible secondary runs | 45 |
| Eligible total runs | 97 |
| Eligible fine cell types | 3 |

The plotted values are therefore:

```text
R  = 38 / 97 = 0.3917526

P  = 15 / 52 = 0.2884615

S  = 23 / 45 = 0.5111111

C  = 3 / 3 = 1

G  = 38 / 38 = 1

Q  = -log10(9.049202e-17) / 25
   = 16.0433897 / 25
   = 0.6417356

FE = log2(315.53) / 12
   = 8.3016334 / 12
   = 0.6918028
```

The `T` track is:

```text
primary share   = 15 / 38 = 0.3947368
secondary share = 23 / 38 = 0.6052632
```

Thus, this one Phase 12 summary row plus its network-specific manifest
denominators determines one labeled sector and all eight displayed tracks for
that sector.

## 9. How NetWeaver turns the plotting table into the circle

### 9.1 The NetWeaver files are functions, not standalone scripts

The files under:

```text
untracked/NetWeaver/R/
```

are the source files of an R package. They are low-level functions that must
be composed into a workflow. The intended pattern is documented in:

```text
untracked/NetWeaver/README.md
untracked/NetWeaver/examples/netweaver.Md
untracked/NetWeaver/vignettes/netweaver.Rmd
```

The package vignette shows that non-genomic units, such as network modules,
can be represented as "hypothetical chromosomes." The Phase 12 adapter uses
the same idea for network-specific key drivers.

The adapter sources only the circular plotting functions. It deliberately
does not source `untracked/NetWeaver/R/fKDA.R` and does not recalculate any
Phase 12 statistic. Phase 12 itself used the frozen corrected KDA source:

```text
scripts/NetWeaver/fKDA.R
```

### 9.2 Hypothetical chromosomes

Each selected network–driver pair receives a unique internal sector ID:

```text
driver_001
driver_002
...
driver_035
```

The unique ID is necessary because the same gene can occur in multiple
networks. Each sector is assigned artificial coordinates:

```text
Start = 1
End   = 100
```

These values have no genomic meaning. They simply give NetWeaver equal-width
containers to draw.

### 9.3 Plot initialization

`rc.initialize()` registers the 35 artificial sectors, their order, and
their broad-network colors. The figure uses:

```text
14 available tracks
chromosome padding = 0.08
track padding = 0.08
track height = 0.15
```

`rc.plot.area()` then opens the circular plotting canvas.

### 9.4 Outer labels and network colors

`rc.plot.ideogram()` draws the outer ring.

- Each sector is labeled with its real `key_driver` gene symbol.
- The artificial `driver_NNN` identifier is not shown.
- The sector color identifies the broad network.
- Repeated gene labels in different colors are separate network-specific
  results.

The current colors are:

| Broad network | Color |
|---|---|
| Astrocytes | Green |
| Excitatory neurons | Orange |
| Inhibitory neurons | Blue |
| Microglia | Magenta |
| OPCs | Light blue |
| Oligodendrocytes | Yellow |
| Vasculature | Vermillion |

The colors encode network identity only. They do not encode AD-up versus
AD-down direction.

### 9.5 Recurrence bar

`rc.plot.histogram()` draws track `R`.

The bar height is `recurrence_fraction`, and its scale is fixed from zero to
one. Because the maximum is fixed at one rather than rescaled to the largest
selected value, bar heights remain interpretable as fractions.

The bar color repeats the broad-network color.

### 9.6 Primary/secondary stacked bar

`rc.plot.barchart()` draws track `T` as a ratio-normalized stacked bar.

- Blue is the primary share.
- Orange is the secondary-pool share.

The two components fill the entire track because they sum to one.

### 9.7 Six normalized heatmap tracks

`rc.plot.heatmap()` draws tracks `P`, `S`, `C`, `G`, `Q`, and `FE`.

All six inputs are between zero and one. NetWeaver maps them to a common
light-yellow-to-dark-red palette:

- light means closer to zero;
- dark means closer to one.

The cell-type coverage track contains values of one among the selected rows,
so the heatmap's internal maximum is exactly one. NetWeaver therefore does
not introduce an additional data-dependent rescaling.

### 9.8 Center recurrence links

The current 35 sectors represent 15 unique gene symbols. Six genes occur in
more than one selected network:

| Gene | Selected networks/sectors |
|---|---:|
| `MT-CO2` | 7 |
| `MT-CO3` | 5 |
| `MT-CYB` | 4 |
| `MT-ND4` | 4 |
| `MT-ATP6` | 3 |
| `MT-ND1` | 3 |

`rc.plot.link()` connects occurrences of the same gene across networks.

For each repeated gene, the code uses its first selected sector as an anchor
and connects it to the other selected sectors carrying that gene. Link width
increases with the number of selected occurrences.

These gray links mean only:

> The same gene is among the displayed top-five drivers in multiple broad
> networks.

They are not Bayesian-network edges, directed paths, regulatory interactions,
or statistical tests between networks.

### 9.9 Labels, legends, and central annotation

`rc.plot.track.id()` adds the compact track keys at the top of the circle.
Base R graphics add:

- the title and subtitle;
- a broad-network color legend explicitly labeled as applying to the outer
  sectors and `R` bars;
- a `T`-track composition legend showing blue for primary calls and
  orange-red for pooled calls;
- a low-to-high heat-ring legend showing the light-yellow-to-dark-red scale
  shared by `P`, `S`, `C`, `G`, `Q`, and `FE`;
- the track-definition legend;
- the central Phase 12 label;
- the statement that links represent identical genes across networks; and
- the note that CAMs and T cells had no eligible KDA runs.

### 9.10 Rendering

The drawing function is run twice:

1. once with the SVG device at 12 by 12 inches; and
2. once with the Cairo PNG device at 3600 by 3600 pixels and 300 dpi.

Files are first written to temporary paths and renamed only after a nonempty
render completes. The plotted-data TSV is also written atomically.

## 10. How to read the figure

Read one sector from the outside toward the center:

1. **Gene label:** identifies the selected key driver.
2. **Outer color:** identifies the broad network.
3. **`R`:** shows how frequently the driver was significant across all
   eligible analyses in that network.
4. **`T`:** shows whether the observed calls came more from primary strata or
   secondary pools.
5. **`P`:** shows primary recurrence after dividing by eligible primary runs.
6. **`S`:** shows secondary-pool recurrence after dividing by eligible
   secondary runs.
7. **`C`:** shows coverage across eligible fine cell types.
8. **`G`:** shows how often the driver had NetWeaver's within-run global
   label.
9. **`Q`:** summarizes the strongest adjusted-P evidence observed for the
   driver.
10. **`FE`:** summarizes the strongest fold enrichment observed for the
    driver.
11. **Gray center link, when present:** indicates that the same gene is also a
    displayed top driver in another broad network.

Useful visual patterns include:

- a tall `R` bar and dark `P` and `S` tracks: recurrence in both primary and
  pooled analyses;
- dark `C`: recurrence across many eligible fine cell types rather than a
  single subtype;
- dark `G`: frequent retention as a within-run global driver;
- dark `Q` and `FE` but a short `R`: a strong result in at least one run but
  limited recurrence;
- a center link: the gene is a selected recurrent driver in several broad
  networks.

## 11. What the figure means scientifically

The figure is a compact prioritization overview. It combines three different
ideas:

1. **Recurrence:** how often a driver was reported across eligible Phase 12
   runs;
2. **Breadth:** how many eligible fine cell types and both analysis tiers
   contributed; and
3. **Strongest observed evidence:** the minimum adjusted P value and maximum
   fold enrichment for that network–driver pair.

A driver with broad recurrence is a candidate for follow-up because its
network-neighborhood enrichment is not confined to one Phase 12 analysis.
A gene connected across the center has network-specific driver evidence in
multiple broad cell classes.

However, the figure is a summary of KDA calls. It does not establish that a
driver:

- changes expression in AD;
- activates or represses its covered mitochondrial genes;
- is causal for AD;
- is upstream in every network or fine cell type;
- is a safe or effective therapeutic target; or
- has been independently replicated.

Those conclusions would require additional direction-specific inspection,
genetic/QTL evidence, robustness analysis, and experimental validation.

## 12. Important limitations of this figure

### 12.1 Only the top five drivers per network are shown

The Phase 12 summary contains 889 network–driver rows, while the figure shows
35. A missing gene may still have significant Phase 12 results; it may simply
rank below the fifth row in its network.

Use `kda_key_driver_summary.tsv` for the complete recurrence table.

### 12.2 Direction is collapsed

The summary and figure combine:

```text
AD_up_mito
AD_down_mito
AD_both_mito
```

The colors do not distinguish those directions. A driver can therefore have
recurrence driven primarily by AD-up signatures, AD-down signatures, combined
signatures, or a mixture.

Use `kda_results.tsv.gz` and filter `signature_direction` to determine the
source of the signal.

### 12.3 Sex/APOE groups and pools are collapsed

The figure separates primary from secondary calls but does not display
individual groups such as `F_e2`, `M_e4`, or `e33_pool`. Those details remain
in `signature_group`.

### 12.4 Secondary pools are overlapping summaries

A dark secondary track is not evidence from five independent replications.
The pools share source groups and are set-union summaries.

### 12.5 Minimum P and maximum fold enrichment are maxima of evidence

Tracks `Q` and `FE` display the strongest observed result for a
network–driver pair. They can be dark because of a single strong run even if
the driver has limited recurrence. They should be interpreted together with
`R`, `P`, `S`, and `C`.

### 12.6 Network-specific recurrence remains conditional on opportunity

The figure corrects call counts by eligible runs, but networks differ in
topology, background genes, signature sizes, induced edges, and fine-cell
composition. Equal recurrence fractions in two networks are not automatically
equal biological effect sizes.

### 12.7 A key driver can be a signature member

`is_signature` records whether the driver itself belongs to the mitochondrial
query. Some drivers are significant partly because the query includes the
driver and its downstream neighborhood. Inspect this flag and
`overlap_items` when prioritizing individual genes.

### 12.8 `global_key_driver` is a within-run label

The `G` track should not be read as study-wide globality. It summarizes a
NetWeaver reduction label applied independently in each run.

### 12.9 CAMs and T cells are not negative findings

They had no eligible KDA runs. Their absence from the circle represents
insufficient effective query size or source eligibility, not evidence of no
driver biology.

## 13. How to investigate one sector in the detailed results

For example, to inspect every Astrocyte `MT-CO2` call:

```r
phase12_dir <- "results/minerva_production/12_kda"

results <- read.delim(
  gzfile(file.path(phase12_dir, "kda_results.tsv.gz")),
  sep = "\t",
  quote = "",
  check.names = FALSE
)

manifest <- read.delim(
  file.path(phase12_dir, "kda_run_manifest.tsv"),
  sep = "\t",
  quote = "",
  check.names = FALSE
)

mt_co2 <- subset(
  results,
  broad_network == "Astrocytes" & key_driver == "MT-CO2"
)

mt_co2 <- merge(
  mt_co2,
  manifest[, c(
    "kda_run_id",
    "source_groups",
    "source_contrast_ids",
    "effective_query_genes",
    "effective_background_genes"
  )],
  by = "kda_run_id",
  all.x = TRUE,
  sort = FALSE
)

mt_co2[, c(
  "kda_run_id",
  "analysis_tier",
  "fine_cell_type",
  "signature_group",
  "signature_direction",
  "best_layer",
  "overlap_count",
  "signature_size",
  "fold_enrichment",
  "adjusted_p_value",
  "is_signature",
  "is_root_node",
  "global_key_driver",
  "overlap_items"
)]
```

This reveals which exact fine cell types, sex/APOE groups, pools, and
directions support the circular summary.

## 14. Reproducing the figure

Run this command from the project root:

```bash
Rscript scripts/figures/visualize_phase12_kda_netweaver.R
```

The explicit equivalent is:

```bash
Rscript scripts/figures/visualize_phase12_kda_netweaver.R \
  --input-dir results/minerva_production/12_kda \
  --netweaver-dir untracked/NetWeaver \
  --output-dir results/figures/phase12_kda \
  --basename phase12_kda_netweaver \
  --top-per-network 5
```

To display a different number of drivers per result-producing network, change
`--top-per-network`. For example:

```bash
Rscript scripts/figures/visualize_phase12_kda_netweaver.R \
  --top-per-network 10 \
  --basename phase12_kda_netweaver_top10
```

Increasing this value makes the circle denser and the gene labels harder to
read. It does not change any Phase 12 result; it only changes the display
subset.

## 15. Source-to-figure traceability summary

The complete path from Phase 12 data to one displayed sector is:

```text
kda_run_manifest.tsv
    │
    ├── eligible primary-run denominator
    ├── eligible secondary-run denominator
    ├── eligible total-run denominator
    └── eligible fine-cell-type denominator
             │
             ▼
kda_key_driver_summary.tsv
    │
    ├── select top five drivers per broad network
    ├── significant, primary, secondary, and global call counts
    ├── fine-cell-type count
    ├── minimum adjusted P value
    └── maximum fold enrichment
             │
             ▼
phase12_kda_netweaver_plotted_data.tsv
    │
    ├── one row per displayed network–driver sector
    ├── raw Phase 12 summary values
    ├── manifest-derived denominators
    └── exact normalized plotting values
             │
             ▼
NetWeaver rc.* plotting functions
    │
    ├── outer driver/network sectors
    ├── recurrence bar
    ├── primary/secondary composition
    ├── six normalized heat tracks
    └── same-gene cross-network links
             │
             ▼
phase12_kda_netweaver.svg
phase12_kda_netweaver.png
```

This separation is intentional: the validated Phase 12 bundle remains
unchanged, the intermediate plotting table makes every transformation
auditable, and NetWeaver is used only for rendering.
