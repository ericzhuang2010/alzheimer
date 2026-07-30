# Effect of the Phase 08 10% detection filter on Phase 12 KDA networks

## Purpose

This note evaluates the concern that the Phase 08 requirement:

```text
pct_ad >= 0.10 OR pct_nci >= 0.10
```

removed a large fraction of genes and, consequently, many edges from the
Bayesian networks used in Phase 12 key-driver analysis (KDA).

It answers four questions:

1. How many assay genes were removed by the 10% detection filter?
2. Is low-expression filtering a general single-cell differential-expression
   practice?
3. How much of each Bayesian network remained after Phase 12 restricted it to
   genes tested in the matching Phase 08 contrast or pool?
4. Does the observed filtering invalidate the Phase 12 KDA results, or does it
   require a sensitivity analysis?

## Short answer

Low-detection filtering before single-cell differential-expression testing is
standard practice. However, there is no universal correct threshold, and
10% is more restrictive than Seurat's current `FindMarkers()` default of 1%.
In this project, 10% was not an arbitrary new choice: it was inherited from
the Yu-style analysis that Phase 08 was designed to reproduce.

Across the 321 validated Phase 08 contrasts:

```text
median assay features removed: 72.7%
median assay features tested:  27.3%
```

That number is high but is calculated against all 33,538 assay features,
including many genes that are very sparse within an exact fine-cell-type ×
sex × APOE × diagnosis comparison.

The network impact is generally less severe because the Bayesian networks are
already enriched for genes expressed in their corresponding cell classes.
Among the seven networks that produced Phase 12 KDA results, median retained
edge fractions were approximately:

```text
primary contrasts:  64% to 90%, depending on network
secondary pools:    62% to 89%, depending on network
```

Thus, the typical result-producing network did not lose 73% of its edges.
Median edge removal was closer to 10%–38%, depending on network and tier.

CAMs and T cells are important exceptions. Only about 1%–4% of their edges
survived the contrast-specific restriction. They produced no eligible Phase
12 KDA runs. Their absence must be interpreted as a lack of an adequate
tested network/signature universe, not as a biological negative result.

The current Phase 12 results remain valid conditional on the prespecified 10%
tested-gene universe. Nevertheless, a lower-threshold sensitivity analysis is
scientifically warranted, particularly for CAMs, T cells, oligodendrocytes,
microglia, and vasculature.

## 1. What the 10% filter does

Phase 08 runs Seurat `FindMarkers()` with MAST separately for every
fine-cell-type, sex, and APOE comparison:

```r
Seurat::FindMarkers(
  ident.1 = "AD",
  ident.2 = "NCI",
  test.use = "MAST",
  min.pct = 0.10,
  logfc.threshold = 0,
  ...
)
```

A gene is tested when it is detected in at least 10% of cells in either AD or
NCI:

```text
pct_ad >= 0.10 OR pct_nci >= 0.10
```

The logical OR is important. A gene does not need to reach 10% in both groups.
A gene detected in 20% of AD cells and 0% of NCI cells is retained and can
still represent a group-specific signal.

Because `logfc.threshold = 0`, there is no fold-change prefilter. The
detection-percentage rule is the feature filter controlling which genes
receive a MAST result row.

Genes that fail the filter are not deleted from the expression objects.
Phase 09 preserves them and labels their contrast-level status:

```text
present_but_filtered_min_pct
```

They simply have no Phase 08 P value or DEG status for that contrast.

## 2. How many genes were removed?

### 2.1 Source table

The production counts come from:

```text
results/minerva_production/09_annotate_genes/
    annotation_qc_by_contrast.tsv
```

For a validated contrast:

- `assay_feature_rows` is the number of assay features;
- `phase08_returned_rows` is the number of genes tested by MAST; and
- `filtered_rows` is the number labeled
  `present_but_filtered_min_pct`.

For every validated production contrast:

```text
phase08_returned_rows + filtered_rows = assay_feature_rows
```

The assay contains 33,538 features.

### 2.2 Production summary

There are 321 validated Phase 08 contrasts. Three additional planned
contrasts were not estimable and are not included in the percentage summary.

| Statistic across validated contrasts | Filtered genes | Filtered percentage |
|---|---:|---:|
| Minimum | 19,360 | 57.7% |
| First quartile | 22,631 | 67.5% |
| Median | 24,383 | 72.7% |
| Mean | 24,616 | 73.4% |
| Third quartile | 26,389 | 78.7% |
| Maximum | 29,604 | 88.3% |

The complementary tested-gene counts are:

| Statistic | Genes tested by MAST |
|---|---:|
| Minimum | 3,934 |
| First quartile | 7,149 |
| Median | 9,155 |
| Mean | 8,922 |
| Third quartile | 10,907 |
| Maximum | 14,178 |

The weighted result across all validated contrasts is:

```text
73.4% filtered
26.6% tested
```

### 2.3 Example

For:

```text
Ast CHI3L1 / Female / APOE e2 / AD versus NCI
```

the counts are:

```text
assay features:  33,538
tested by MAST:   8,300  (24.7%)
filtered:        25,238  (75.3%)
```

### 2.4 Why the percentage can be this high

The denominator contains every feature in the assay. The filter is then
applied within an exact fine-cell-type × sex × APOE contrast. Many assay
features have little or no detectable expression within such a narrow cell
population even if they are expressed elsewhere in the brain dataset.

Single-nucleus RNA-seq also contains many zero measurements due to a
combination of genuine low expression and incomplete transcript capture.
Consequently, a high percentage relative to the entire assay feature list is
not, by itself, evidence of an implementation error.

## 3. Is low-detection filtering general practice?

### 3.1 Yes, the principle is standard

Filtering genes that are detected in very few cells is a common
differential-expression practice because such genes have:

- little information for estimating a group effect;
- unstable detection-rate and expression estimates;
- weak statistical power;
- a greater risk of numerical or separation problems; and
- a multiple-testing cost despite having little chance of producing a stable
  result.

The official Seurat `FindMarkers()` documentation explicitly includes
`min.pct`, defining it as the minimum fraction of cells in either population
in which a gene must be detected. Seurat describes it as a way to avoid
testing genes that are very infrequently expressed:

<https://satijalab.org/seurat/reference/findmarkers>

MAST also provides a `filterLowExpressedGenes()` function whose documented
default threshold is 0.1:

<https://rglab.github.io/MAST/reference/filterLowExpressedGenes.html>

The MAST documentation example reports 72% of genes removed at a 10%
threshold. That example is not evidence that 72% is always desirable, but it
shows that a removal fraction of this magnitude is not unprecedented when a
10% detection rule is applied to sparse single-cell data.

The original MAST paper explains why detection and nondetection are central
to its two-part hurdle model:

<https://doi.org/10.1186/s13059-015-0844-5>

### 3.2 No, 10% is not a universal default

The general practice is to filter low-information genes. The exact 10%
threshold is not universally required.

The current Seurat default is:

```text
min.pct = 0.01
```

Therefore, this project's 10% rule is ten times the current Seurat default
and should be described as a relatively restrictive, prespecified threshold.

Its justification here is replication: the local Yu-method documentation and
source materials specify genes detected in at least 10% of cells, and the
original analysis code uses:

```r
min.pct = 0.1
```

Relevant local records are:

```text
docs/yu_paper/Yu_sex_apoe_method.md
docs/yu_paper/code/
    mathys_DEG_analysis_subcluster_MAST_interaction.Rmd
docs/yu_paper/code/
    mathys_DEG_analysis_subcluster_sex-cogdx_apoe-cogdx.Rmd
config/analysis_parameters.yml
```

Using 10% for the primary Yu-style analysis is therefore methodologically
defensible. It does not establish that Phase 12 KDA is insensitive to the
choice.

### 3.3 When filtering is least problematic

The filter is most defensible when:

- it is chosen before examining the result;
- the same rule is applied to every comparison;
- it depends on expression opportunity rather than on the eventual P value;
- either comparison group can satisfy the rule;
- genes that fail are treated as untested, not as non-DEGs; and
- downstream backgrounds are restricted to the same tested universe.

The current pipeline satisfies these conditions. In particular, Phase 12 does
not convert filtered genes to a zero or non-DEG state. It removes them from
the matching network background.

### 3.4 When filtering becomes concerning

The concern grows when:

- the threshold removes network regulators of biological interest;
- retention differs strongly among cell types or groups;
- small or sparse strata lose most of their network;
- network reachability and neighborhood sizes change substantially;
- secondary-pool intersections compound the filtering;
- the key-driver conclusions change at a plausible lower threshold; or
- a network has too little surviving structure for KDA.

Several of these concerns apply here, especially to CAMs and T cells.

## 4. How Phase 12 removes network edges

For one primary contrast, Phase 12 defines:

```r
tested <- sort(unique(source_rows$mapped_gene))
```

For a secondary pool, it uses the intersection of tested genes from every
contributing primary group:

```r
tested <- Reduce(
  intersect,
  lapply(sources, function(x) x$tested)
)
```

It then restricts the full matching Bayesian network:

```r
induced <- full_net[
  full_net[[1]] %in% tested &
  full_net[[2]] %in% tested,
]
```

An edge is retained only when both its source and target received a Phase 08
result in the relevant contrast, or in every source contrast for a secondary
pool.

The effective background is:

```r
background <- sort(unique(c(
  induced[[1]],
  induced[[2]]
)))
```

Thus, a tested gene that becomes isolated after edge removal is not part of
the KDA background.

## 5. How network retention was measured

### 5.1 Full-network denominator

Each network was read with the same rules as Phase 12:

- use the first two columns as directed edge endpoints;
- remove missing or empty endpoints;
- remove self-edges; and
- deduplicate edges.

The resulting full-network sizes are:

| Broad network | Full edges | Full nodes |
|---|---:|---:|
| Astrocytes | 8,881 | 8,285 |
| CAMs | 15,598 | 15,260 |
| Excitatory neurons | 13,759 | 10,441 |
| Inhibitory neurons | 10,534 | 9,579 |
| Microglia | 6,826 | 6,604 |
| OPCs | 8,610 | 8,249 |
| Oligodendrocytes | 9,067 | 8,190 |
| T cells | 10,481 | 10,360 |
| Vasculature | 5,266 | 5,290 |

### 5.2 Unit summarized

The Phase 12 manifest contains one row per signature direction. The three
directions for the same fine cell type and group use the same tested-gene
universe and the same induced network.

To avoid counting the same network restriction three times, the calculation
collapsed manifest rows to unique combinations of:

```text
analysis tier
fine cell type
broad network
signature group
source status
tested-gene count
induced edge count
effective background count
```

Only source-complete universes were retained. This produced:

```text
321 primary network universes
264 secondary network universes
585 total source-complete network universes
```

### 5.3 Retention formulas

```text
edge retention =
    induced_network_edges / full_network_edges

node retention =
    effective_background_genes / full_network_nodes
```

These are network-retention measures after restriction to the Phase 08
tested-gene universe.

They should not be attributed exclusively to `min.pct`. Gene-symbol mapping
and the relationship between assay genes and network nodes can also affect
retention. The assay-overlap check below shows, however, that identifier and
assay coverage are high for all nine networks.

## 6. Network identifiers and assay coverage

Before contrast-level filtering, the network nodes overlap the assay feature
universe well:

| Broad network | Network nodes represented in assay | Full edges with both endpoints represented |
|---|---:|---:|
| Astrocytes | 96.6% | 93.5% |
| CAMs | 95.9% | 91.8% |
| Excitatory neurons | 96.5% | 93.2% |
| Inhibitory neurons | 96.7% | 93.4% |
| Microglia | 96.8% | 95.4% |
| OPCs | 96.6% | 94.2% |
| Oligodendrocytes | 96.5% | 93.9% |
| T cells | 96.2% | 91.2% |
| Vasculature | 97.1% | 95.2% |

Therefore, the severe CAM and T-cell pruning is not primarily explained by a
global identifier mismatch or by their network genes being absent from the
immune expression object. The large additional loss occurs when the 10%
detection rule is applied within the exact CAM or T-cell sex/APOE contrast,
and when secondary pools intersect those contrast-specific tested sets.

## 7. Observed Phase 12 edge and node retention

The following values are medians across source-complete, unique network
universes.

| Broad network | Primary edges retained | Secondary edges retained | Primary nodes retained | Secondary nodes retained |
|---|---:|---:|---:|---:|
| Astrocytes | 73.2% | 69.9% | 73.7% | 70.7% |
| CAMs | 1.31% | 1.25% | 1.57% | 1.49% |
| Excitatory neurons | 89.7% | 88.8% | 91.4% | 90.6% |
| Inhibitory neurons | 84.2% | 82.1% | 85.2% | 83.2% |
| Microglia | 76.8% | 69.7% | 76.4% | 69.1% |
| OPCs | 85.5% | 82.3% | 85.6% | 82.4% |
| Oligodendrocytes | 64.3% | 61.6% | 63.9% | 61.4% |
| T cells | 3.52% | 3.10% | 4.00% | 3.49% |
| Vasculature | 69.8% | 64.3% | 70.7% | 65.1% |

Across all 585 source-complete universes:

| Quantity | Median | Interquartile range |
|---|---:|---:|
| Edges retained | 82.1% | 69.8%–87.5% |
| Nodes retained | 83.2% | 70.7%–88.8% |

The overall values should be interpreted cautiously because the many neuronal
fine cell types give neuronal networks more weight. The per-network table is
more informative.

### 7.1 Primary versus secondary

Across all source-complete primary universes:

```text
median edges retained: 83.2%
median nodes retained: 84.9%
```

Across all source-complete secondary universes:

```text
median edges retained: 81.0%
median nodes retained: 82.1%
```

The lower secondary retention is expected because a secondary pool keeps a
gene only if it was tested in every contributing primary contrast.

### 7.2 Result-producing networks

Excluding CAMs and T cells, median edge removal by network is approximately:

| Broad network | Primary edges removed | Secondary edges removed |
|---|---:|---:|
| Astrocytes | 26.8% | 30.1% |
| Excitatory neurons | 10.3% | 11.2% |
| Inhibitory neurons | 15.8% | 17.9% |
| Microglia | 23.2% | 30.3% |
| OPCs | 14.5% | 17.7% |
| Oligodendrocytes | 35.7% | 38.4% |
| Vasculature | 30.2% | 35.7% |

These losses are scientifically meaningful, but they are much smaller than
the 73% assay-feature filtering percentage.

## 8. Why 73% gene filtering does not imply 73% edge loss

The 33,538 assay features include many genes that are:

- not nodes in a particular broad Bayesian network;
- very sparsely expressed in the matching cell class;
- reference or low-information features outside the modeled regulatory
  structure; or
- expressed in other cell types but not in the exact fine-cell stratum.

The Bayesian networks are already enriched for genes relevant to their cell
class. Consequently, network nodes are much more likely than an arbitrary
assay feature to pass the expression filter.

There is also a nonlinear relationship between node and edge retention. An
edge survives only if both endpoints survive. If node removal were random and
independent, retaining a fraction \(r\) of nodes would retain roughly
\(r^2\) of edges. In real biological networks, removal is not random:
highly expressed, connected genes may be preferentially retained, while
sparse peripheral genes may be preferentially removed. That helps explain
why several networks retain a high fraction of edges.

## 9. CAM and T-cell outliers

### 9.1 Observed Phase 08 sizes

CAM contrasts typically tested about 4,223 genes, and T-cell contrasts about
4,669 genes, out of 33,538 assay features.

Representative cell counts were also much smaller than for abundant
neuronal or microglial populations:

- CAM median AD-plus-NCI cells across the six groups: approximately 203;
- T-cell median AD-plus-NCI cells: approximately 233.

One CAM primary contrast was not estimable because the NCI arm contained only
one cell.

Small populations do not automatically imply low tested-gene counts, and
tested-gene count alone does not fully explain edge retention. Nevertheless,
the combination of sparse expression, fine stratification, and a network
whose connected genes rarely pass the exact contrast filter leaves only a
small induced graph.

### 9.2 Interpretation

For CAMs and T cells:

```text
approximately 96%–99% of full edges were removed
```

This is too much pruning to treat their Phase 12 absence as a negative
biological result. The current production pipeline correctly records them as
ineligible rather than claiming that no key drivers exist.

Their network and query coverage should be treated as a limitation and a
priority for sensitivity analysis.

## 10. Does filtering invalidate the seven result-producing networks?

Not automatically.

The current KDA enrichment tests are internally coherent because:

1. filtered genes are treated as untested rather than as non-DEGs;
2. the network is restricted to the same tested-gene universe;
3. the mitochondrial signature is intersected with that effective
   background;
4. `bg.size` equals the number of nodes in the restricted network;
5. every reported driver and overlap gene belongs to the run-specific
   background; and
6. Phase 12 independently validated the enrichment arithmetic.

Therefore, the reported P values and fold enrichments are valid for the
restricted network that was actually tested.

The limitation is scope:

> A Phase 12 result describes key-driver enrichment within the detectable,
> tested portion of the matching Bayesian network under the 10% rule.

It does not establish that the same driver would be selected in a less
restrictive network universe.

The networks with roughly 60%–70% edge retention—especially
oligodendrocytes, vasculature, astrocytes, and pooled microglia—deserve more
caution than the neuronal and OPC networks with more than 80% retained.

## 11. Recommended sensitivity analysis

### 11.1 Preserve the primary analysis

The 10% threshold should remain the primary Yu-style replication setting
because it was prespecified and inherited from the target method.

It should not be changed retrospectively in the published production bundle.
A sensitivity analysis should write to a separate output root and retain
separate provenance.

### 11.2 Rerun at lower thresholds

Recommended sensitivity values are:

```text
min.pct = 0.05
min.pct = 0.01
```

The 1% value matches Seurat's current default and provides a useful lower
bound. The 5% value is an intermediate setting.

`logfc.threshold` should remain zero so that the sensitivity changes only the
detection-percentage universe.

### 11.3 Phase 08 must be rerun

It is not valid to take the current Phase 12 signatures and simply add
filtered network nodes back to the background.

Lowering `min.pct` changes:

- which genes receive MAST P values;
- the within-contrast BH multiple-testing universe;
- which genes satisfy the Phase 08 DEG rule;
- the AD-up, AD-down, and combined mitochondrial signatures;
- the tested genes available for network restriction;
- the induced network and background;
- KDA candidate neighborhoods; and
- potentially the key-driver calls.

Therefore, a rigorous sensitivity analysis must rerun Phase 08 and the
dependent Phase 09 and Phase 12 products.

### 11.4 Compare these outputs

For each threshold and network, compare:

1. Phase 08 genes tested and genes called as mitochondrial DEGs;
2. induced edges and effective background nodes;
3. effective mitochondrial query size;
4. number of eligible and significant KDA runs;
5. key-driver overlap using Jaccard similarity;
6. stability of top-driver recurrence ranks;
7. stability of `global_key_driver` calls;
8. changes in neighborhood size, fold enrichment, and adjusted P value;
9. changes in covered mitochondrial genes; and
10. whether CAMs or T cells acquire an adequate induced network and query.

### 11.5 Useful robustness categories

Drivers can be classified as:

| Category | Definition |
|---|---|
| Threshold-stable | Reported at 10%, 5%, and 1% with comparable recurrence |
| Directionally stable | Supporting AD-up/down direction remains consistent |
| Expanded-universe supported | Becomes stronger but remains present when the universe expands |
| Threshold-dependent | Appears only at one threshold or changes rank substantially |
| Lost after expansion | No longer significant when additional genes enlarge the testing/background universe |

The primary conclusions should emphasize threshold-stable drivers.

## 12. Recommended reporting language

The Phase 12 methods should state:

> Phase 08 tested genes detected in at least 10% of AD or NCI nuclei within
> each fine-cell-type, sex, and APOE contrast, following the prespecified
> Yu-style workflow. Phase 12 restricted each matching Bayesian network to
> edges whose two endpoints were tested in the relevant contrast, or in all
> contributing contrasts for pooled analyses. KDA results are therefore
> conditional on this run-specific detectable network universe.

The limitations should state:

> The 10% detection threshold removed a median of 72.7% of all assay features.
> Result-producing networks retained a median of approximately 62%–90% of
> edges depending on network and analysis tier, whereas CAM and T-cell
> networks retained only approximately 1%–4% and yielded no eligible KDA
> runs. CAM and T-cell absence is an eligibility limitation rather than a
> negative result. Lower `min.pct` sensitivity analyses are needed to assess
> key-driver stability to network-universe pruning.

## 13. Overall assessment

The concern is legitimate but should be separated into two findings:

1. **Assay-wide gene filtering is high:** approximately 73% of all assay
   features fail the contrast-specific 10% rule.
2. **Most result-producing networks are less severely affected:** their
   median edge retention is approximately 62%–90%, not 27%.

The primary Phase 12 results are not numerically invalid. They are conditional
results from a prespecified, internally consistent tested-network universe.

The high filtering does create a robustness question. This is especially
important for:

- CAMs and T cells, whose networks are almost completely pruned;
- oligodendrocytes and vasculature, with roughly one-third of edges removed;
- pooled analyses, where intersection across source contrasts compounds
  pruning; and
- any driver whose significance depends on a small or highly altered
  neighborhood.

The appropriate response is not to insert untested genes into the current
background. It is to retain the 10% result as the primary Yu-compatible
analysis and run prespecified 5% and 1% Phase 08-to-Phase 12 sensitivity
branches.

## 14. Reproducibility notes

The gene-filter percentages in this note were derived from:

```text
results/minerva_production/09_annotate_genes/
    annotation_qc_by_contrast.tsv
```

The induced edge and background-node counts were taken from:

```text
results/minerva_production/12_kda/
    kda_run_manifest.tsv
```

The full network denominators were recalculated from:

```text
data/bayesian_network/<broad_network>/result.links3.links.txt
```

using the same edge-cleaning rules as `scripts/12_run_kda.R`.

Network overlap with the expression assay was calculated from:

```text
results/minerva_production/09_annotate_genes/
    gene_annotation_master.tsv.gz
```

using the Phase 09 current-symbol mapping. All percentages are descriptive
audits of the validated production artifacts; no Phase 08, Phase 09, or
Phase 12 result was modified.
