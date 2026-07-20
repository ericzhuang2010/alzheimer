# Phase 11: Test mitochondrial pathways

After mitochondrial genes have been annotated, the next question is no longer simply:

> Which individual mitochondrial genes are differentially expressed?

Instead, we ask:

> Do groups of mitochondrial genes that work together show a coordinated change in Alzheimer’s disease?

That is what **testing mitochondrial pathways** means.

A pathway is a group of genes whose products cooperate in the same biological process. Examples include:

- Respiratory-chain Complex I
- Complex II
- Complex III
- Complex IV
- ATP synthase, or Complex V
- Oxidative phosphorylation
- TCA cycle
- Mitochondrial translation
- Mitochondrial protein import
- Mitophagy
- Mitochondrial fission and fusion
- Reactive-oxygen-species defense
- Mitochondrial DNA maintenance

The original paper performed pathway enrichment with **GOtest**, **MSigDB C2:CP canonical pathways**, and a hypergeometric test with Benjamini–Hochberg correction. In Figure 5B, the most divergent genes from the APOE ε4-versus-ε3/ε3 comparison were enriched for mitochondrial pathways including oxidative phosphorylation and respiratory electron transport.

Our mitochondrial-focused study will go further by testing carefully defined mitochondrial pathways in every cell cluster and every primary AD-versus-NCI contrast.

The Zhang–Yu similarity calculation is not part of Phase 11. Phase 10 has
already defined and calculated the cross-cell-type similarity scores,
permutation p values, FDR values, ranks, and high- and low-score gene sets.
Phase 11 must consume those validated outputs rather than reconstructing DEG
states or recalculating similarity scores. The Phase 10 methodology and
cross-cell-type aggregation rule are documented in:

- [Phase 10 mitochondrial similarity plan](../phase_10_similarity/phase_10_mitochondrial_similarity_plan.md)
- [Cross-cell-type similarity calculation explained](../phase_10_similarity/similarity_calculation_cross_celltypes_explained.md)

---

## 1. Annotation versus pathway testing

These are two different steps.

### Annotation

Annotation tells us what each gene does.

For example:

| Gene | Annotation |
|---|---|
| `MT-ND2` | Complex I subunit encoded by mitochondrial DNA |
| `NDUFS1` | Complex I subunit encoded by nuclear DNA |
| `NDUFAF1` | Complex I assembly factor |
| `TFAM` | Mitochondrial DNA maintenance and transcription |
| `PINK1` | Mitophagy and mitochondrial quality control |
| `OPA1` | Mitochondrial fusion and cristae organization |

### Pathway testing

Pathway testing asks whether genes from one functional group tend to appear together among the strongest AD-related changes.

For example:

> Are Complex I genes collectively shifted toward lower expression in female APOE ε4 excitatory neurons?

Or:

> Are mitophagy genes collectively increased in male APOE ε2 microglia?

Annotation defines the groups. Pathway analysis tests whether the groups show meaningful patterns.

---

## 2. Why pathway testing is necessary

Individual mitochondrial genes may have modest changes.

Imagine that Complex I contains 45 genes measured in one cell cluster. The results might look like this:

| Gene | AD-versus-NCI log2FC | Adjusted p value |
|---|---:|---:|
| NDUFS1 | −0.22 | 0.08 |
| NDUFV1 | −0.19 | 0.11 |
| NDUFA9 | −0.25 | 0.04 |
| NDUFB8 | −0.18 | 0.09 |
| NDUFS3 | −0.21 | 0.07 |
| NDUFA2 | −0.16 | 0.15 |

Only `NDUFA9` passes adjusted \(p<0.05\). If we look only at significant genes, we might conclude:

> Only one Complex I gene changed.

But the more important pattern is that almost every gene has a negative fold change.

Pathway analysis may reveal:

> Complex I genes are collectively shifted downward, even though most individual genes do not reach significance by themselves.

This is especially useful in transcriptomic studies because biological pathways often change through many small, coordinated effects rather than one enormous gene-expression change.

---

## 3. What will be tested?

For the first mitochondrial-pathway analysis, we will use the same six primary DEG contrasts:

1. `F_ε2x_AD vs F_ε2x_NCI`
2. `F_ε33_AD vs F_ε33_NCI`
3. `F_ε4x_AD vs F_ε4x_NCI`
4. `M_ε2x_AD vs M_ε2x_NCI`
5. `M_ε33_AD vs M_ε33_NCI`
6. `M_ε4x_AD vs M_ε4x_NCI`

Each contrast is tested separately in each of the 54 cell clusters.

Therefore, for every mitochondrial pathway, we could have as many as:

\[
6 \times 54 = 324
\]

pathway results.

For example, the Complex I pathway would be tested in:

```text
Ast GRM3, F_ε2x AD vs NCI
Ast GRM3, F_ε33 AD vs NCI
Ast GRM3, F_ε4x AD vs NCI
Ast GRM3, M_ε2x AD vs NCI
Ast GRM3, M_ε33 AD vs NCI
Ast GRM3, M_ε4x AD vs NCI
```

Then the same six tests would be performed in `Ast CHI3L1`, `Ast DPP10`, every excitatory-neuron cluster, every inhibitory-neuron cluster, microglia, oligodendrocytes, and the other cell populations.

---

## 4. Define the mitochondrial pathway collection

We should freeze the pathway definitions before examining the DEG results.

The main source should be the curated **MitoPathways** annotations linked to the MitoCarta mitochondrial-gene inventory. We should also create a smaller set of biologically interpretable pathways for the primary analysis.

### Recommended primary pathways

#### Energy production

| Pathway | What it does |
|---|---|
| Complex I | Transfers electrons from NADH into the respiratory chain |
| Complex II | Connects the TCA cycle with the respiratory chain |
| Complex III | Transfers electrons from coenzyme Q to cytochrome c |
| Complex IV | Transfers electrons to oxygen |
| Complex V | Uses the proton gradient to make ATP |
| Oxidative phosphorylation | Combined process that generates ATP |
| Respiratory-chain assembly | Builds and stabilizes the respiratory complexes |
| Supercomplex organization | Organizes respiratory complexes into larger structures |

#### Mitochondrial metabolism

| Pathway | What it does |
|---|---|
| TCA cycle | Extracts energy from nutrients |
| Pyruvate metabolism | Connects glucose metabolism with mitochondria |
| Fatty-acid oxidation | Uses fats to produce energy |
| Amino-acid metabolism | Processes amino acids inside mitochondria |
| Coenzyme Q metabolism | Produces an electron carrier used by the respiratory chain |
| Heme metabolism | Helps produce heme-containing proteins |
| Iron–sulfur cluster synthesis | Produces cofactors required by many mitochondrial enzymes |

#### Mitochondrial gene expression

| Pathway | What it does |
|---|---|
| mtDNA replication | Copies mitochondrial DNA |
| mtDNA repair | Maintains mitochondrial DNA integrity |
| Mitochondrial transcription | Produces RNA from mitochondrial DNA |
| Mitochondrial RNA processing | Processes mitochondrial RNA |
| Mitoribosome | Builds mitochondrial proteins |
| Mitochondrial translation | Produces proteins encoded by mtDNA |

#### Protein maintenance

| Pathway | What it does |
|---|---|
| TOM/TIM protein import | Imports nuclear-encoded proteins into mitochondria |
| Mitochondrial chaperones | Helps mitochondrial proteins fold correctly |
| Mitochondrial proteases | Removes damaged or incorrectly folded proteins |
| Mitochondrial unfolded-protein response | Responds to protein stress inside mitochondria |

#### Dynamics and quality control

| Pathway | What it does |
|---|---|
| Mitochondrial fusion | Joins mitochondria together |
| Mitochondrial fission | Divides mitochondria |
| Cristae organization | Maintains inner-membrane structure |
| Mitophagy | Removes damaged mitochondria |
| Mitochondrial trafficking | Moves mitochondria through cells and neuronal processes |

#### Stress and signaling

| Pathway | What it does |
|---|---|
| ROS detoxification | Limits damage caused by reactive oxygen species |
| Calcium handling | Regulates mitochondrial calcium |
| Apoptosis | Controls mitochondria-associated cell-death signaling |
| Mitochondrial biogenesis | Regulates production of new mitochondria |

A gene may belong to several pathways. For example, `SDHA` belongs to both Complex II and the TCA cycle. That is expected.

---

## 5. Two complementary pathway-testing methods

We should perform two kinds of pathway analysis.

### Method A: Overrepresentation analysis

This method uses the list of significant DEGs.

It asks:

> Does this pathway contain more significant genes than expected by chance?

This is similar to the hypergeometric enrichment method used in the original paper. The authors tested pathway overrepresentation with GOtest and applied BH correction for multiple pathway tests.

### Method B: Ranked gene-set enrichment

This method uses the complete DEG result table, including genes that did not individually pass the significance cutoff.

It asks:

> Do genes from this pathway tend to collect near the top or bottom of the complete ranked gene list?

This should be our primary pathway method because it can detect coordinated but modest mitochondrial changes.

The two methods answer related but different questions.

| Method | Input | Main question |
|---|---|---|
| Overrepresentation | Significant DEGs only | Are pathway genes unusually common among significant DEGs? |
| Ranked enrichment | All tested genes | Do pathway genes collectively lean upward or downward? |

Using both provides a stronger interpretation.

---

## 6. Method A: overrepresentation analysis in detail

For each cell-cluster–contrast combination, we first create two significant gene lists:

```text
Significantly upregulated genes
Significantly downregulated genes
```

Using the paper’s threshold:

\[
\text{BH-adjusted }p<0.05
\]

and:

\[
|FC|>1.3
\]

If the result uses log2 fold change, the 1.3-fold cutoff is:

\[
|\log_2FC|>\log_2(1.3)\approx0.379
\]

### Test upregulated and downregulated genes separately

This is essential.

If we combine upregulated and downregulated genes into one list, we could discover that “Complex I is enriched,” but we would not know whether Complex I increased or decreased.

We should therefore run:

```text
Complex I enrichment among upregulated genes
Complex I enrichment among downregulated genes
```

separately.

### Gene ratio used in enrichment figures

The enrichment figure should report the **gene ratio** for every plotted
pathway. For a given query gene list:

\[
\text{GeneRatio}
=
\frac{k}{n}
=
\frac{\text{number of query genes in the pathway}}
{\text{number of unique query genes admitted to the enrichment test}}
\]

Here, the query list may be a significant-up list, a significant-down list, or
a Phase 10 high- or low-similarity rank set. The denominator \(n\) is the
actual number of unique query genes retained after identifier mapping and
intersection with the declared background. It must not be hard-coded to 200:
a Phase 10 tail may contain fewer than 200 genes because of eligibility,
coverage, or disjoint-tail capping.

Gene ratio is different from:

\[
\text{pathway hit rate}=\frac{k}{M}
\]

where \(M\) is the number of pathway genes in the background, and from:

\[
\text{background ratio}=\frac{M}{N}
\]

where \(N\) is the total background size. Fold enrichment can be reported as:

\[
\text{fold enrichment}
=
\frac{k/n}{M/N}
\]

The figure-ready table must retain \(k\), \(n\), \(M\), and \(N\), not only
the displayed decimal gene ratio.

### Example of overrepresentation

Suppose that in female APOE ε4 excitatory neurons:

- 15,000 genes were tested.
- 500 genes were significantly downregulated.
- 60 tested genes belong to Complex I.
- 12 of those 60 Complex I genes were significantly downregulated.

Using \(k=12\), \(n=500\), \(M=60\), and \(N=15{,}000\), the figure's gene
ratio is:

\[
\text{GeneRatio}=\frac{12}{500}=0.024
\]

Thus, 2.4% of the significant-down query list belongs to Complex I. The
pathway hit rate is:

\[
\frac{12}{60}=0.20
\]

so 20% of tested Complex I genes were downregulated. The background ratio is:

\[
\frac{60}{15000}=0.004
\]

and the fold enrichment is:

\[
\frac{0.024}{0.004}=6.0
\]

This means Complex I genes are approximately six times more common among the downregulated genes than expected from the transcriptome-wide rate.

A hypergeometric or one-sided Fisher’s exact test asks whether this excess is larger than expected by chance.

### The contingency table

The statistical test can be represented like this:

| | In Complex I | Not in Complex I |
|---|---:|---:|
| Significantly downregulated | 12 | 488 |
| Not significantly downregulated | 48 | 14,452 |

The test asks:

> If significant genes were randomly distributed, would we expect 12 or more Complex I genes among the 500 downregulated genes?

A small p value suggests that the pathway is overrepresented.

### Correct background gene universe

The background should be:

> All genes that were actually tested by MAST in that specific cell cluster and contrast.

It should not automatically be every human gene or every gene in MitoCarta.

For example, the background for:

```text
Exc L5 ET, F_ε4x_AD vs F_ε4x_NCI
```

should be all genes that passed `min.pct = 0.1` and were tested in that exact comparison.

This matters because the original workflow’s expression filtering can differ across cell clusters and sex–APOE groups. A gene absent from the result table may have been untested rather than unchanged.

For exact replication of the paper, we can also reproduce its stated background of all genes in the dataset. But for the mitochondrial-focused analysis, the contrast-specific tested-gene universe is more defensible.

### Outputs from overrepresentation analysis

For every pathway, cell cluster, contrast, and direction, save:

| Output | Meaning |
|---|---|
| `pathway` | Pathway name |
| `cell_cluster` | Cell population |
| `contrast` | Sex–APOE AD-vs-NCI comparison |
| `direction` | Upregulated or downregulated |
| `pathway_size_total` | Total genes in the pathway |
| `pathway_size_tested` | Pathway genes tested in this comparison |
| `overlap_count` | Significant genes in the pathway |
| `query_size` | Unique query genes admitted to the enrichment test |
| `background_size` | Genes in the declared test universe |
| `gene_ratio` | `overlap_count / query_size`; value displayed in the figure |
| `background_ratio` | `pathway_size_tested / background_size` |
| `pathway_hit_rate` | Fraction of tested pathway genes that were significant |
| `enrichment_ratio` | `gene_ratio / background_ratio` |
| `p_value` | Raw enrichment p value |
| `FDR` | BH-adjusted p value |
| `overlap_genes` | Significant genes driving the enrichment |

---

## 7. Method B: ranked gene-set enrichment in detail

Ranked enrichment does not require a gene to pass an arbitrary significance threshold.

Instead, every tested gene receives a ranking score.

A simple ranking might look like:

| Rank | Gene | Direction | Strength |
|---:|---|---|---:|
| 1 | Gene A | Strongly higher in AD | Very positive |
| 2 | Gene B | Higher in AD | Positive |
| ... | ... | ... | ... |
| 7,500 | Gene C | No clear change | Near zero |
| ... | ... | ... | ... |
| 14,999 | Gene D | Lower in AD | Negative |
| 15,000 | Gene E | Strongly lower in AD | Very negative |

The pathway test asks where the pathway genes occur in this ranked list.

If Complex I genes are concentrated near the bottom, Complex I is interpreted as downregulated.

If mitophagy genes are concentrated near the top, mitophagy is interpreted as upregulated.

If pathway genes are scattered randomly throughout the list, there is little evidence for coordinated pathway change.

### Recommended ranking statistic

The best option is a signed model statistic from the MAST analysis, if it is available.

Conceptually:

\[
\text{ranking score}
=
\text{sign of fold change}
\times
\text{strength of evidence}
\]

If the MAST test statistic is not available and the Seurat output contains only fold change and raw p value, a practical ranking score is:

\[
R=
\operatorname{sign}(\log_2FC)
\times
[-\log_{10}(p_{\text{raw}})]
\]

Example:

| Gene | log2FC | Raw p | Ranking score |
|---|---:|---:|---:|
| Gene A | +0.50 | 0.0001 | +4 |
| Gene B | −0.30 | 0.001 | −3 |
| Gene C | +0.08 | 0.30 | +0.52 |
| Gene D | −0.02 | 0.80 | −0.10 |

Do not normally rank using the BH-adjusted p value. The raw test statistic or raw p value preserves more information.

Because cell-level MAST can produce extremely small p values, we should also perform a sensitivity analysis ranking genes by log2FC alone. A pathway result that is similar under both ranking strategies is more convincing.

### What ranked enrichment reports

Typical outputs include:

| Output | Meaning |
|---|---|
| Enrichment score | How strongly pathway genes concentrate at one end of the ranking |
| Normalized enrichment score | Enrichment adjusted for pathway size |
| Raw p value | Significance before correction |
| FDR | Significance after testing many pathways |
| Leading-edge genes | Genes contributing most strongly to the pathway signal |
| Direction | Upward or downward in AD |

The **leading-edge genes** are especially important. They identify the smaller group of pathway genes responsible for most of the enrichment.

For example:

```text
Pathway: Complex I
Normalized enrichment score: −1.84
FDR: 0.008
Leading edge:
NDUFS1, NDUFV1, NDUFA9, NDUFB8, NDUFS3, NDUFA2
```

This would mean:

> Complex I genes are collectively shifted toward lower expression in AD, and these six genes contribute most strongly to the result.

---

## 8. A complete worked example

Suppose we analyze:

```text
Cell cluster: Exc L5 ET
Contrast: F_ε4x_AD vs F_ε4x_NCI
Pathway: Complex I
```

### Individual-gene results

Imagine that 55 Complex I genes were tested:

- 43 have negative log2FC values.
- 12 have positive log2FC values.
- 6 negative genes pass FDR < 0.05.
- No positive genes pass FDR < 0.05.

### Overrepresentation result

Suppose the significant-down list contains more Complex I genes than expected:

```text
Enrichment ratio = 3.8
Raw p = 0.0004
BH FDR = 0.009
```

Interpretation:

> Complex I genes are overrepresented among significantly downregulated genes.

### Ranked-enrichment result

Suppose the complete ranked list gives:

```text
Normalized enrichment score = −1.72
BH FDR = 0.013
```

Interpretation:

> Even Complex I genes that are not individually significant tend to shift toward lower expression.

### Combined conclusion

Because both methods agree, we could conclude:

> Complex I shows a coordinated AD-associated reduction in female APOE ε4 L5 ET excitatory neurons.

We would then identify the leading genes and later ask whether the same pattern is present in:

- Other excitatory-neuron subclusters
- Male APOE ε4 carriers
- Female APOE ε3/ε3 donors
- Astrocytes
- Microglia

The formal comparisons between sex and APOE groups belong to the later interaction phase.

---

## 9. Pathway coverage must be checked first

A pathway cannot be tested reliably if most of its genes were not measured or failed the expression filter.

For every pathway and every cluster–contrast combination, calculate:

\[
\text{coverage}
=
\frac{\text{number of pathway genes tested}}
{\text{total number of pathway genes}}
\]

Example:

| Pathway | Total genes | Tested genes | Coverage |
|---|---:|---:|---:|
| Complex I | 60 | 54 | 90% |
| Mitophagy | 35 | 27 | 77% |
| Mitochondrial tRNA modification | 18 | 5 | 28% |

The Complex I test is well covered.

The mitochondrial tRNA-modification test may be unreliable because only 5 of 18 genes were tested.

### Suggested pathway-eligibility rule

For the primary analysis, require:

- At least 10 tested genes, and
- At least 30% pathway coverage.

For small, strongly predefined pathways such as individual respiratory complexes, we may allow five tested genes, but these results should be labeled as lower confidence.

Every output should report pathway coverage even when the pathway is significant.

---

## 10. Multiple-testing correction

We will be testing many pathways.

For example:

\[
54\text{ clusters}
\times
6\text{ contrasts}
\times
\text{many mitochondrial pathways}
\]

Without correction, many pathways could appear significant by chance.

### Primary FDR family

For each:

```text
cell cluster × contrast × analysis type
```

adjust all mitochondrial-pathway p values together using Benjamini–Hochberg.

For example:

```text
Exc L5 ET × F_ε4x AD vs NCI × ranked enrichment
```

is one correction family.

### Secondary global FDR

As a stricter sensitivity analysis, combine all mitochondrial-pathway tests across all clusters and contrasts and calculate a global BH FDR.

Results can then be labeled:

| Label | Meaning |
|---|---|
| `local_FDR_significant` | Significant within its cluster and contrast |
| `global_FDR_significant` | Significant after correction across the full study |
| `nominal_only` | Raw p value small, but FDR threshold not passed |

Global correction will be much stricter. A pathway passing both local and global FDR is especially strong.

---

## 11. Broad pathways first, detailed pathways second

Many mitochondrial pathways overlap.

For example:

```text
Oxidative phosphorylation
    ├── Complex I
    ├── Complex II
    ├── Complex III
    ├── Complex IV
    └── Complex V
```

If oxidative phosphorylation, Complex I, and respiratory electron transport are all significant, these are not necessarily three completely independent biological discoveries. They may be different levels of the same signal.

A sensible strategy is hierarchical.

### Level 1: broad categories

Test broad pathways such as:

- Oxidative phosphorylation
- Mitochondrial metabolism
- Mitochondrial gene expression
- Protein import and homeostasis
- Dynamics and quality control
- Stress and signaling

### Level 2: specific subpathways

If oxidative phosphorylation is significant, inspect:

- Complex I
- Complex II
- Complex III
- Complex IV
- Complex V
- Respiratory-chain assembly
- Supercomplex organization

This keeps interpretation organized and avoids presenting highly overlapping pathway names as independent findings.

---

## 12. Two possible statistical backgrounds

There are two reasonable questions we can ask.

### Transcriptome-wide enrichment

Use all genes tested by MAST as the background.

Question:

> Is Complex I more altered than the transcriptome overall?

This should be our primary analysis.

### Mitochondrial-internal enrichment

Use only tested mitochondrial genes as the background.

Question:

> Among mitochondrial genes, is Complex I more altered than other mitochondrial pathways?

This can be useful as a secondary analysis.

For example, transcriptome-wide testing may show that mitochondrial genes overall are strongly downregulated. A mitochondrial-internal test could then reveal that Complex I is even more affected than other mitochondrial systems.

The two analyses answer different questions and should be clearly labeled.

---

## 13. Quality-control and sensitivity analyses

Several checks are important.

### Analyze mtDNA genes separately

Because this is single-nucleus RNA-seq, mitochondrial-DNA transcripts may be captured differently from nuclear-encoded mitochondrial genes.

Run the pathway analysis:

1. With all mitochondrial genes
2. With nuclear-encoded mitochondrial genes only
3. With mtDNA-encoded genes only, when enough are measured

If oxidative-phosphorylation enrichment disappears when 13 mtDNA protein genes are removed, the result may be driven mainly by mitochondrial-transcript capture.

If it remains strong among nuclear-encoded respiratory genes, the signal is more robust.

### Check whether one gene drives the result

Suppose a pathway is significant only because `MT-ND2` has an extreme score.

Remove the strongest gene and rerun the pathway test.

A robust pathway should usually remain directionally similar when one dominant gene is removed.

### Check leading-edge consistency

If several related cell clusters show the same pathway, ask whether the same genes drive it.

For example:

| Cell cluster | Leading Complex I genes |
|---|---|
| Exc L5 ET | NDUFS1, NDUFA9, NDUFV1 |
| Exc L6 CT | NDUFS1, NDUFA9, NDUFS3 |
| Exc NRGN | NDUFV1, NDUFA9, NDUFB8 |

This suggests a coherent neuronal Complex I signal.

If every cluster is driven by unrelated genes, the pathway interpretation may be less stable.

### Distinguish “not significant” from “not testable”

A pathway may fail because:

- It is truly unchanged.
- Its effect is small.
- The subgroup has limited statistical power.
- Too few pathway genes were detected.
- The cell cluster contains too few cells.

The supplemental power analysis shows that small and moderate effects were difficult to detect, particularly in the smaller male APOE ε2 group.

Therefore, every pathway result should include coverage and sample/cell-count information.

---

## 14. How this differs from the original paper

The original paper’s pathway analysis mainly examined selected gene lists, such as the top and bottom genes ranked by Zhang–Yu similarity. Figures 3–6 show pathway enrichment among genes with the greatest similarity or divergence across sex and APOE comparisons. The paper used MSigDB canonical pathway sets and a hypergeometric overrepresentation test.

Our mitochondrial analysis should include two layers, with a strict boundary
between Phase 10 similarity calculation and Phase 11 pathway testing.

### Layer 1: pathway enrichment of Phase 10 similarity tails

Phase 11 should read the validated Phase 10 bundle from:

```text
results/<environment>/10_similarity/
```

The required handoff files are:

- `mitochondrial_similarity_results.tsv.gz` for score, coverage, eligibility,
  rank, and FDR metadata;
- `mitochondrial_similarity_rank_sets.tsv` for the prespecified high- and
  low-score gene lists;
- `similarity_comparison_manifest.tsv` for comparison definitions and figure
  analogues; and
- `similarity_status.tsv`, `similarity_checks.tsv`, and
  `similarity_artifacts.tsv` to verify that the bundle is complete.

Phase 11 must not recalculate ternary states, pooled cross-cell-type scores,
permutation p values, FDR values, ranks, or top/bottom selections. It should:

1. Validate the Phase 10 status, checks, schemas, and artifact hashes.
2. Use each stored high- or low-score rank set as the enrichment query.
3. Use the corresponding Phase 10
   `comparison_id × analysis_universe` ranking-eligible genes as the
   background.
4. Run MSigDB C2:CP enrichment for Yu comparability and the frozen
   mitochondrial pathway collection for the focused analysis.
5. Calculate `GeneRatio = overlap_count / query_size` from the actual mapped
   rank set used in each test.

These are **Yu-style mitochondrial analogues**, not an exact transcriptome-wide
reproduction of the published figures, because Phase 10 deliberately restricts
the ranked universe to the `core_mito` and `all_mito_related` mitochondrial
sets and applies an explicit missing-state coverage policy. The enrichment is
still a global, cross-cell-type result: Phase 10 pooled matched states across
all applicable cell clusters before assigning one similarity score per gene.

### Layer 2: mitochondrial-focused direct testing

For every primary cell-cluster-specific AD-versus-NCI contrast:

- Test curated mitochondrial pathways directly.
- Use both ranked enrichment and overrepresentation.
- Separate upregulated and downregulated pathways.
- Report pathway direction, coverage, FDR, and leading genes.

This second layer is the major new contribution.

The attached supplemental document adds the sex-marker QC and power-analysis figures but does not provide an additional mitochondrial pathway-analysis protocol.

---

## 15. How pathway results should be summarized

### Enrichment dot plots

For the Phase 10 high/low tails and the direct up/down overrepresentation
analyses, create a figure-ready table and dot plot in which:

- the x-axis is `gene_ratio`;
- point size is `overlap_count`;
- point color represents BH-adjusted FDR; and
- facets identify the comparison, similarity tail or DEG direction, and
  analysis universe.

The figure caption must define gene ratio as \(k/n\), state that \(n\) is the
actual query size used in the test, and distinguish it from pathway hit rate,
pathway coverage, and fold enrichment. A large gene ratio describes the share
of the submitted query list assigned to a pathway; it is not an expression
effect size.

### Pathway-by-group matrices

For the direct cell-cluster-specific analysis, create a matrix like this:

| Pathway | Fε2 Exc | Fε33 Exc | Fε4 Exc | Mε2 Exc | Mε33 Exc | Mε4 Exc |
|---|---:|---:|---:|---:|---:|---:|
| Complex I | −0.4 | −0.8 | **−1.9** | +0.2 | −0.3 | −0.5 |
| Complex IV | −0.1 | −0.4 | **−1.5** | +0.1 | −0.2 | −0.4 |
| Mitophagy | +0.3 | +0.7 | **+1.4** | +0.8 | +0.4 | +0.5 |
| ROS defense | +0.2 | +0.6 | **+1.2** | +0.4 | +0.3 | +0.4 |

The entries could be normalized enrichment scores. Bold values could indicate FDR-significant pathways.

We would make separate matrices for:

- Excitatory-neuron subclusters
- Inhibitory-neuron subclusters
- Astrocytes
- Microglia
- Oligodendrocytes
- OPCs
- Other cell populations where coverage is sufficient

This produces a **mitochondrial pathway atlas**.

---

## 16. Recommended output files

The pathway phase should generate:

```text
01_mito_pathway_coverage.tsv
02_mito_pathway_ranked_enrichment.tsv
03_mito_pathway_ORA_upregulated.tsv
04_mito_pathway_ORA_downregulated.tsv
05_mito_pathway_leading_edge_genes.tsv
06_mito_pathway_summary_matrix.tsv
07_mito_pathway_QC_report.md
08_similarity_tail_pathway_ORA.tsv
09_pathway_figure_data.tsv
```

The main ranked-enrichment table should contain:

| Column | Meaning |
|---|---|
| `pathway` | Mitochondrial pathway |
| `cell_cluster` | Cell cluster |
| `contrast` | AD-vs-NCI comparison |
| `n_pathway_total` | Total genes in pathway |
| `n_pathway_tested` | Pathway genes tested |
| `coverage` | Tested fraction |
| `enrichment_score` | Raw enrichment |
| `normalized_enrichment_score` | Size-normalized enrichment |
| `direction` | Higher or lower in AD |
| `p_value` | Raw p value |
| `FDR_local` | BH FDR within contrast |
| `FDR_global` | BH FDR across study |
| `leading_edge_genes` | Main driver genes |

---

## 17. The actionable workflow

The pathway-testing phase should proceed in this order:

1. **Validate the Phase 10 similarity handoff.**  
   Require a complete Phase 10 status, passing checks, matching artifact
   hashes, and the expected comparison, result, and rank-set schemas.

2. **Freeze mitochondrial pathway definitions.**  
   Use the mitochondrial annotation and gene-to-pathway table created in Phase 2.

3. **Run overrepresentation analysis on the stored Phase 10 tails.**  
   Use the high- and low-score rank sets without recalculating similarity,
   and use the matching ranking-eligible analysis universe as background.

4. **Calculate and retain figure quantities.**  
   For every ORA result, save overlap count, actual query size, tested pathway
   size, background size, gene ratio, background ratio, fold enrichment, p
   value, and FDR.

5. **Create pathway coverage tables.**  
   Determine which pathway genes were present and tested in every cell cluster and contrast.

6. **Create a ranked all-gene list for each direct DEG analysis.**  
   Prefer a signed MAST statistic; otherwise use signed \(-\log_{10}(p)\), with log2FC ranking as a sensitivity analysis.

7. **Run ranked mitochondrial pathway enrichment.**  
   Use all tested genes as the primary ranking universe.

8. **Create significant-up and significant-down DEG lists.**

9. **Run overrepresentation analysis separately for up- and downregulated genes.**

10. **Apply BH multiple-testing correction.**  
   Calculate local and global FDR values.

11. **Extract leading-edge and overlapping genes.**

12. **Repeat with nuclear-encoded mitochondrial genes only.**

13. **Perform leave-one-gene-out sensitivity checks for the strongest pathways.**

14. **Create enrichment dot plots, pathway heatmaps, and summary matrices.**

15. **Carry the pathway results into the next phase.**  
    The next phase formally tests whether pathway changes differ by sex or APOE genotype.

# Core interpretation

The individual-gene phase might tell us:

> `NDUFS1` is lower in female APOE ε4 AD excitatory neurons.

The pathway phase can tell us something much more biologically meaningful:

> A coordinated group of Complex I and oxidative-phosphorylation genes is shifted downward in female APOE ε4 AD excitatory neurons, with the signal driven by several nuclear- and mtDNA-encoded respiratory-chain genes.

That distinction—moving from isolated genes to coordinated mitochondrial systems—is the purpose of testing mitochondrial pathways.
