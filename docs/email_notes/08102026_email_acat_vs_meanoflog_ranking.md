# MeanOfLog versus ACAT key-driver ranking

## Main difference

The two methods emphasize different patterns of evidence across KDA runs:

| Method | Ranking quantity | Best value | Favors |
|---|---:|---:|---|
| MeanOfLog | Mean of \(-\log_{10}(p)\) | Larger | Consistent evidence across many DEG signatures |
| ACAT | Combined Cauchy p-value | Smaller | One or several exceptionally small p-values |

MeanOfLog is closely related to the geometric mean p-value. ACAT is more
sensitive to the strongest tail evidence. Thus, MeanOfLog tends to prioritize
genes supported moderately or strongly across many signatures, whereas ACAT can
promote a gene with an exceptionally strong result in a smaller number of
signatures.

For the Phase 12 ACAT figure, raw KDA p-values from the primary directional
AD-up and AD-down runs were combined with `na.action = "na.to1"`, following the
professor's NetWeaver example. Genes were ordered by the combined ACAT p-value,
ascending.

## Simple example

Suppose two genes were tested in four DEG signatures:

| Gene | Four KDA p-values | MeanOfLog | ACAT p-value |
|---|---|---:|---:|
| Consistent evidence | 0.01, 0.01, 0.01, 0.01 | **2.000** | 0.010 |
| One extreme result | 0.000001, 0.5, 0.5, 0.5 | 1.726 | **0.000004** |

MeanOfLog ranks the consistently supported gene first because all four
signatures provide evidence. ACAT ranks the second gene first because its one
extremely small p-value dominates the Cauchy combination.

## Phase 12 example: excitatory neurons

| Gene | MeanOfLog rank | MeanOfLog | Raw p-values < 0.001 | Smallest p-value | ACAT p-value | ACAT rank |
|---|---:|---:|---:|---:|---:|---:|
| MT-CYB | **2** | **2.382** | 35/133 | \(8.57\times10^{-13}\) | \(2.52\times10^{-11}\) | 5 |
| UQCR10 | 6 | 1.758 | 24/133 | **\(4.93\times10^{-17}\)** | **\(6.55\times10^{-15}\)** | **2** |

MT-CYB has broader and more consistent evidence, so MeanOfLog prefers it.
UQCR10 has a much more extreme minimum p-value, so ACAT promotes it from rank 6
to rank 2.

Consequently:

- MeanOfLog top three: `MT-CO2`, `MT-CYB`, `COX6B1`
- ACAT top three: `MT-CO2`, `UQCR10`, `COX4I1`

## Phase 12 example: microglia

| Gene | MeanOfLog rank | MeanOfLog | Smallest p-value | ACAT p-value | ACAT rank |
|---|---:|---:|---:|---:|---:|
| MT-ND4 | **2** | **2.0198** | \(1.37\times10^{-8}\) | \(1.15\times10^{-7}\) | 3 |
| MT-CO3 | 3 | 2.0098 | **\(2.75\times10^{-9}\)** | **\(3.29\times10^{-8}\)** | **2** |

The MeanOfLog scores are almost tied. MT-CO3 has the stronger tail result, so
ACAT reverses their order.

## Phase 12 example: OPCs

| Gene | MeanOfLog rank | MeanOfLog | Smallest p-value | ACAT p-value | ACAT rank |
|---|---:|---:|---:|---:|---:|
| FTL | **3** | **2.2005** | \(1.79\times10^{-8}\) | \(1.46\times10^{-7}\) | 4 |
| MT-CO2 | 4 | 2.0333 | **\(2.08\times10^{-9}\)** | **\(1.87\times10^{-8}\)** | **3** |

MeanOfLog selects FTL for the top three, whereas ACAT selects MT-CO2.

## Overall effect on the reduced circular figure

Astrocytes, oligodendrocytes, and vasculature retain exactly the same top-three
order under both methods. Microglia retains the same three genes but reverses
the order of MT-ND4 and MT-CO3. The largest change occurs in excitatory neurons,
where two of the three displayed genes change.

Supporting files:

- [MeanOfLog plotted data](../../results/figures/analysis/phase12_kda/reduced_circular_figure/phase12_kda_reduced_circular_plotted_data.tsv)
- [ACAT plotted data](../../results/figures/analysis/phase12_kda/reduced_circular_figure_ACAT/phase12_kda_reduced_circular_ACAT_plotted_data.tsv)
- [Complete ACAT ranking](../../results/figures/analysis/phase12_kda/reduced_circular_figure_ACAT/phase12_kda_reduced_circular_ACAT_acat_summary.tsv)
- [ACAT reduced circular figure](../../results/figures/analysis/phase12_kda/reduced_circular_figure_ACAT/phase12_kda_reduced_circular_ACAT.png)
