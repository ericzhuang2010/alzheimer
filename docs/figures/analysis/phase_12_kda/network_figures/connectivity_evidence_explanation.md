# Phase 12 connectivity-versus-KDA-evidence figure explained

![Network connectivity is contextual evidence, not a substitute for KDA significance](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence.png)

## What question the figure addresses

This figure asks whether genes with stronger aggregate KDA evidence also tend
to be highly connected nodes in their complete broad-cell-type Bayesian
networks.

That is an important diagnostic because a highly connected node has a large
network neighborhood and may have more opportunities to overlap a query gene
set. Connectivity can therefore contribute to KDA ranking behavior. The figure
does not treat connectivity as an independent validation of a key driver.

The plotted universe contains 50,165 candidate-by-network records with at
least one eligible primary directional KDA ranking test. A gene can appear once
in each broad network in which it was tested.

## Panel A: candidate-level connectivity and KDA evidence

Each point represents one candidate gene in one broad-cell-type network.

### X-axis: within-network total-degree percentile

Total degree is the number of incoming plus outgoing connections for the gene
in the complete corresponding Bayesian network. It is not degree within one
of the small displayed subnetworks.

Degree is converted to a percentile separately within each broad network:

- a value near 1 identifies one of that network's most highly connected
  genes;
- a value near 0 identifies a relatively weakly connected gene;
- genes tied at the same degree receive the same upper-rank percentile.

For example, the `APOE` astrocyte value of 0.986 means its total degree of 13
is at approximately the 98.6th percentile of the astrocyte network.

### Y-axis: −log10(ACAT P)

For each candidate gene in each broad network, ACAT first combines its raw KDA
P values across all eligible primary `AD_up_mito` and `AD_down_mito` runs.
Secondary pooled analyses and the derived `AD_both_mito` signature are excluded.
If a candidate lacks a test in an otherwise eligible run, that missing value
is treated as P = 1 (`na.to1`), matching the NetWeaver ACAT implementation used
for the other ACAT figures.

For an eligible-run P-value vector \(p_1,\ldots,p_K\), the equal-weight ACAT
statistic is

\[
T = \frac{1}{K}\sum_{r=1}^{K}
\tan\!\left[\left(\frac{1}{2}-p_r\right)\pi\right],
\qquad
P_{\mathrm{ACAT}} = \frac{1}{2} -
\frac{\arctan(T)}{\pi}.
\]

The implementation uses the NetWeaver-compatible numerical handling for very
small values and exact boundary values of 0 and 1. Nonsignificant tests remain
in the calculation; the aggregation is not restricted to significant KDA
results.

The plotted value is then

\[
E_{n,g} = -\log_{10}\!\left(P_{\mathrm{ACAT},n,g}\right).
\]

ACAT is the aggregation step. The −log10 operation happens only afterward to
make small combined P values easy to display:

- ACAT P = 0.05 gives a y-value of 1.301;
- ACAT P = 10⁻⁵ gives a y-value of 5;
- ACAT P = 1 gives a y-value of 0.

A larger y-value therefore means stronger combined ACAT evidence. The
transformation is strictly monotonic, so it does not change candidate ordering
or the Spearman correlations. Unlike the previous display, the ACAT values are
not normalized separately by each network's maximum.

### Point color

Color identifies the broad-cell-type network:

- green: astrocytes;
- orange: excitatory neurons;
- dark blue: inhibitory neurons;
- pink: microglia;
- light blue: OPCs;
- yellow: oligodendrocytes;
- vermilion: vasculature.

### Point area

Point area increases with the number of primary directional runs in which the
candidate passed the adjusted KDA significance threshold:

```text
point_area = 18 + 38 * sqrt(number_of_significant_runs)
```

Point size therefore represents significant-run recurrence, not full-network
degree. Connectivity is encoded only on the x-axis in this figure. A point
with zero significant runs remains visible because of the 18-point baseline.

The labeled candidates are overplotted with a fixed black-bordered marker so
their positions are easy to find. Their actual significant-run counts should
be read from the accompanying data rather than inferred from the black outline.

### Why only selected genes are labeled

The labeled genes were prespecified:

`APOE`, `LAMTOR5`, `GABARAPL2`, `RPL11`, `RPS15`, `FTL`, `ANKRD11`,
`SELENOW`, `WDR82`, `SLC11A1`, and `HSPA1A`.

When a gene was present in more than one broad network, one context was chosen
for labeling by the following ordered rule:

1. most significant primary directional runs;
2. largest −log10(ACAT P) value;
3. highest degree percentile.

The labels are therefore annotations of nominated genes, not an automated list
of the most extreme scatterplot points.

## Values for the seven central candidate systems

| Candidate and labeled network | Total degree | Degree percentile | ACAT P | −log10(ACAT P) | Significant/ranking runs |
|---|---:|---:|---:|---:|---:|
| `APOE` — astrocytes | 13 | 0.986 | 3.36 × 10⁻⁵ | 4.474 | 4/34 |
| `LAMTOR5` — excitatory neurons | 10 | 0.981 | 5.84 × 10⁻⁶ | 5.234 | 13/129 |
| `GABARAPL2` — excitatory neurons | 11 | 0.986 | 2.20 × 10⁻⁵ | 4.657 | 18/133 |
| `RPL11` — excitatory neurons | 9 | 0.976 | 8.92 × 10⁻¹³ | 12.050 | 24/133 |
| `RPS15` — inhibitory neurons | 18 | 0.995 | 4.22 × 10⁻⁶ | 5.374 | 14/92 |
| `FTL` — OPCs | 31 | 0.996 | 1.46 × 10⁻⁷ | 6.837 | 2/9 |
| `ANKRD11` — OPCs | 28 | 0.996 | 7.89 × 10⁻⁷ | 6.103 | 2/9 |

These candidates are all high-degree nodes, but their combined KDA evidence
and recurrence counts differ substantially. The y-values are on one absolute
−log10(P) scale; however, the OPC candidates aggregate only nine eligible
runs, whereas the excitatory-neuron candidates aggregate as many as 133.

## Panel B: within-network Spearman associations

Panel B calculates a separate Spearman rank correlation between degree
percentile and −log10(ACAT P) within each broad network.
Spearman correlation measures monotonic rank association and does not require
a linear relationship or normally distributed variables.

| Broad network | Candidate records | Spearman rho | Nominal P value |
|---|---:|---:|---:|
| Astrocytes | 7,547 | 0.523 | <1 × 10⁻³⁰⁰ |
| Excitatory neurons | 9,926 | 0.550 | <1 × 10⁻³⁰⁰ |
| Inhibitory neurons | 9,054 | 0.523 | <1 × 10⁻³⁰⁰ |
| Microglia | 5,547 | 0.360 | 1.29 × 10⁻¹⁶⁹ |
| OPCs | 7,567 | 0.401 | 3.21 × 10⁻²⁹⁰ |
| Oligodendrocytes | 5,851 | 0.286 | 9.96 × 10⁻¹¹¹ |
| Vasculature | 4,673 | 0.170 | 1.55 × 10⁻³¹ |

The values stored as P = 0 for the first three networks are numerical
underflow, not literal zero probability; the figure reports them as
`P < 1e-300`.

The associations are positive in every network. They are moderate in
astrocytes and excitatory and inhibitory neurons, smaller in microglia and
OPCs, and weakest in oligodendrocytes and vasculature. The enormous candidate
counts make even the weak vasculature association highly significant, so rho
is more informative than the P value for judging magnitude.

## Main interpretation

The figure supports two related conclusions:

1. More highly connected genes tend to receive stronger aggregate KDA ranking
   evidence.
2. Connectivity does not determine the KDA score perfectly: all correlations
   are well below 1, and genes with similar degree percentiles show substantial
   vertical variation in ACAT evidence.

The first conclusion is a warning against treating a large network node as
independent support for biological importance. The second shows that degree is
not a one-to-one substitute for cross-run KDA evidence.

However, this figure does **not** formally demonstrate that an individual
candidate has more evidence than expected after adjusting for degree. That
would require a prespecified degree-matched permutation analysis, regression,
or residual/rank comparison. The present correlations are descriptive hub-bias
diagnostics.

## Important limitations

- The Spearman P values are nominal and exploratory. No bootstrap confidence
  intervals are displayed, and the seven network correlations are not shown
  with a multiple-testing correction.
- Candidate nodes within a network are not guaranteed to be statistically
  independent: they share network structure and many of the same KDA query
  runs. Standard Spearman P values may therefore overstate precision.
- The y-axis uses raw KDA P values for ranking, while point area counts runs
  passing the adjusted KDA threshold. These are related but different
  quantities.
- Ranking coverage varies. Of 50,165 plotted records, 10,468 have coverage
  below 80% of eligible directional runs. ACAT treats each missing test as
  P = 1 (`na.to1`), so missingness contributes conservative null evidence.
  Coverage and the missing-value rule are retained in the TSV but are not
  separately encoded in the plot.
- The y-axis uses one absolute −log10(P) scale rather than network-specific
  normalization. Even so, ACAT values can reflect different eligible-run
  counts and shared dependence structures across networks, so cross-network
  numerical comparisons should remain descriptive.
- The candidate universe includes mtDNA-encoded genes as well as nuclear
  genes. The plot is a complete ranking diagnostic, not a restricted display
  of the seven highlighted nuclear candidates.
- Correlation does not establish that connectivity causes KDA evidence or that
  any labeled candidate causally regulates disease biology.

## Supporting files

- [Vector figure](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence.svg)
- [Complete plotted points](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence_points.tsv)
- [Within-network correlations](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence_correlations.tsv)
- [Labeled candidate records](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence_labels.tsv)
- [Raw-degree diagnostic supplement](../../../../../results/figures/analysis/phase12_kda/network_figures/phase12_kda_connectivity_evidence_by_network.pdf)
- [Figure-generation implementation](../../../../../scripts/figures/analysis/phease12_kda/phase12_kda_network_figure_common.py)
