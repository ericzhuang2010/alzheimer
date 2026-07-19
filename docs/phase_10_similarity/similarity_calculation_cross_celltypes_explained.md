# Which Cell Types Are Used in Figures 3, 4, 5, and 6?

**Figures 3, 4, 5, and 6 do not use one specific cell type. They combine the differential-expression results from all 54 high-resolution cell clusters.**

The important distinction is:

> The authors first ran differential expression separately within each cell cluster. Only afterward did they combine the resulting **up / unchanged / down states** across cell clusters to calculate one Zhang–Yu similarity score per gene.

They did **not** combine raw expression from different cell types into one differential-expression test, and they did **not** average fold changes across cell types.

---

## How the analysis proceeds

For every gene, cell cluster, and sex–APOE group, the AD-versus-NCI MAST result was converted to:

\[
+1 = \text{significantly upregulated in AD}
\]

\[
0 = \text{not significantly changed}
\]

\[
-1 = \text{significantly downregulated in AD}
\]

The authors then joined these states across all 54 cell clusters into long vectors and compared the vectors.

## Cell-cluster use in each figure

| Figure | Biological comparison | Cell clusters included | Number of matched positions per gene |
|---|---|---:|---:|
| **Figure 3** | Females versus males | All 54 clusters across all three APOE groups | \(54 \times 3 = 162\) |
| **Figure 4** | APOE ε2x versus APOE ε3/ε3 | All 54 clusters across both sexes | \(54 \times 2 = 108\) |
| **Figure 5** | APOE ε4x versus APOE ε3/ε3 | All 54 clusters across both sexes | \(54 \times 2 = 108\) |
| **Figure 6** | Females versus males, separately within ε2x, ε3/ε3, and ε4x | All 54 clusters for each APOE comparison | \(54\) per APOE genotype |

These 54 clusters span excitatory and inhibitory neuron subtypes, astrocyte subtypes, oligodendrocytes, oligodendrocyte precursor cells, immune populations, and vascular populations.

---

# Figure 3: Females versus males

For every gene, the female vector contains:

```text
54 clusters × F_ε2x AD-vs-NCI states
54 clusters × F_ε33 AD-vs-NCI states
54 clusters × F_ε4x AD-vs-NCI states
```

The male vector contains the corresponding:

```text
54 clusters × M_ε2x AD-vs-NCI states
54 clusters × M_ε33 AD-vs-NCI states
54 clusters × M_ε4x AD-vs-NCI states
```

Therefore:

\[
N = 54 \times 3 = 162
\]

For example, a small section of a gene's vectors might look like this:

| Matched position | Female state | Male state |
|---|---:|---:|
| Astrocyte cluster 1, ε2x | +1 | -1 |
| Astrocyte cluster 2, ε2x | 0 | 0 |
| Excitatory cluster 1, ε2x | +1 | +1 |
| Microglia cluster, ε4x | -1 | 0 |

The Zhang–Yu score summarizes all 162 matched positions.

Therefore, Figure 3A's **Same**, **Different**, and **Opposite** counts represent occurrences across all cell clusters and APOE groups, not one particular cell type.

Figure 3B then takes the globally ranked top 200 and bottom 200 genes and performs pathway enrichment. It is therefore also an **all-cell-cluster pathway result**.

---

# Figure 4: APOE ε2x versus APOE ε3/ε3

For every gene, the ε2x vector contains:

```text
F_ε2x AD-vs-NCI across 54 clusters
M_ε2x AD-vs-NCI across 54 clusters
```

The ε3/ε3 vector contains:

```text
F_ε33 AD-vs-NCI across 54 clusters
M_ε33 AD-vs-NCI across 54 clusters
```

Therefore:

\[
N = 54 \times 2 = 108
\]

Figure 4A ranks genes by whether their AD response is similar or different between ε2x and ε3/ε3 across the full collection of cell clusters and both sexes.

Figure 4B performs pathway enrichment on the top and bottom genes from this **global APOE ε2x-versus-ε3/ε3 score**.

Again, no single cell type is being used.

---

# Figure 5: APOE ε4x versus APOE ε3/ε3

The same structure is used for APOE ε4x:

```text
ε4x vector:
F_ε4x AD-vs-NCI across 54 clusters
M_ε4x AD-vs-NCI across 54 clusters
```

This is compared with:

```text
ε3/ε3 vector:
F_ε33 AD-vs-NCI across 54 clusters
M_ε33 AD-vs-NCI across 54 clusters
```

Therefore:

\[
N = 54 \times 2 = 108
\]

Figure 5A ranks genes according to their global ε4x-versus-ε3/ε3 similarity.

Figure 5B applies pathway enrichment to those global ranked gene lists. This is where oxidative-phosphorylation and electron-transport pathways appeared among the most divergent genes.

However, Figure 5B alone does **not** tell us which cell type produced that mitochondrial signal.

---

# Figure 6: Females versus males within each APOE genotype

Figure 6 performs three separate Zhang–Yu analyses:

1. Female versus male within APOE ε2x
2. Female versus male within APOE ε3/ε3
3. Female versus male within APOE ε4x

For APOE ε2x, for example:

```text
Female vector:
F_ε2x AD-vs-NCI across 54 clusters

Male vector:
M_ε2x AD-vs-NCI across 54 clusters
```

Therefore:

\[
N = 54
\]

The same applies to the ε3/ε3 and ε4x comparisons.

Figure 6A shows the most concordant and most divergent genes for each of these three all-cluster comparisons.

Figure 6B performs pathway enrichment on the 200 most sex-divergent genes for each APOE genotype. These are labeled **Bottom 200** because they have the lowest similarity scores.

---

# Why this distinction matters for the mitochondrial study

To reproduce Figures 3–6, the workflow should be:

1. Perform the six MAST contrasts separately in every one of the 54 cell clusters.
2. Convert every result to -1, 0, or +1.
3. Combine the states across all 54 clusters according to the Figure 3, 4, 5, or 6 comparison.
4. Calculate one Zhang–Yu score per gene.
5. Rank the genes.
6. Run pathway enrichment on the selected top or bottom genes.

That produces a **cross-cell-type, system-level result**.

However, the mitochondrial project will probably also need an additional analysis:

> Which specific cell clusters are responsible for a mitochondrial pathway appearing in Figure 5B or Figure 6B?

The original Figure 5B cannot answer that directly. To identify the responsible cell types, examine the underlying -1/0/+1 states and fold changes cluster by cluster, or run mitochondrial pathway analysis separately within each cell cluster.

## Two distinct outputs

| Analysis | Question answered |
|---|---|
| Reproduction of Figures 3–6 | Which genes and pathways show consistent or divergent patterns across the entire collection of cell clusters? |
| Cell-cluster-specific mitochondrial analysis | In which exact neuron, astrocyte, microglial, or other cluster is the mitochondrial pathway changing? |

For faithful reproduction, **all 54 clusters are used**. For identifying the biological cell population driving a mitochondrial result, a separate cluster-specific follow-up is required.
