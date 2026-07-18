# Why Local Phase 08 Has Fewer DEGs Than Yu et al.

The difference comes from MAST p-values and Benjamini–Hochberg-adjusted FDR, not from fold changes, cell selection, or the fold-change threshold.

## Count reconciliation

| Call category | Count |
|---|---:|
| Shared Yu/Phase 08 DEGs | 615 |
| Yu-only DEGs | 101 |
| Phase-08-only DEGs | 30 |
| Net difference | 101 − 30 = **71 fewer** |

Therefore:

- Yu Vasculature DEGs: `615 + 101 = 716`;
- local Phase 08 DEGs: `615 + 30 = 645`.

## What happened to the 101 Yu-only DEGs

For all 101 Yu-only genes:

- the gene was returned and tested by Phase 08;
- its log2FC passed `abs(logFC) > log2(1.3)`;
- its detection fractions and log2FC matched Yu exactly;
- it failed only the current run's BH FDR `< 0.05`;
- 98 of 101 had a larger raw MAST p-value than Yu;
- the median current-to-Yu raw-p-value ratio was 2.35.

For example, Yu reports `ABCD3` with raw p-value `0.000209` and FDR `0.0221`. The local run produced the identical log2FC and detection fractions but raw p-value `0.00169` and FDR `0.0995`, so it was not called as a DEG.

## Likely source of the difference

The most likely source is an incompletely specified inferential implementation detail. The [Yu paper](../yu_paper/Yu_sex_apoe.pdf) specifies Seurat v5, MAST, `min.pct = 0.1`, and the `nCount_RNA`, PMI, and age covariates, but it does not freeze exact Seurat/MAST versions or fully describe covariate encoding. The local run used Seurat 5.5.1 and MAST 1.28.0.

Differences in raw MAST p-values are subsequently propagated through BH correction. The paper also does not provide the complete non-DEG testing universe, so its BH denominator cannot be reconstructed directly from Supplemental Table S1.

The one local non-estimable comparison did not cause the deficit. Yu had no DEG in that Fib SLC4A4, Male, APOE-e2 stratum, where the local data contained zero AD cells and 11 NCI cells.

## Do the genes with the highest fold changes match?

The fold-change values themselves match exactly for all 716 Yu Vasculature DEGs, including the genes with the largest effects. However, some high-fold-change genes are not retained as local Phase 08 DEGs because MAST requires both the fold-change threshold and BH FDR `< 0.05`.

When all five Vasculature cell types and their contrasts are pooled and ranked by absolute log2FC:

| Rank cutoff | Yu genes retained as Phase 08 DEGs | Exact overlap between the two top lists |
|---|---:|---:|
| Top 10 | 7/10 | 7/10 |
| Top 25 | 20/25 | 20/25 |
| Top 50 | 42/50 | 42/50 |
| Top 100 | 85/100 | 85/100 |
| Top 200 | 170/200 | 170/200 |

Among the directional rankings, Phase 08 retained six of Yu's top 10 upregulated calls and eight of Yu's top 10 downregulated calls.

The three Yu genes missing from the absolute-log2FC top 10 were:

| Gene | Cell type and contrast | log2FC | Local FDR |
|---|---|---:|---:|
| `DET1` | Per, Male APOE-e2 | 5.852 | 0.0519 |
| `MTRNR2L1` | SMC, Male APOE-e4 | −4.781 | 0.0772 |
| `PFN1` | Per, Male APOE-e2 | −4.410 | 0.0636 |

Their local log2FC values are identical to Yu's. They are excluded only because their local FDR values exceed 0.05.

## What could legitimately change the local FDR?

The evidence indicates that the priority is reproducing Yu's raw MAST p-values, not altering the BH cutoff after seeing Table S1. The most plausible remaining explanations are listed below in priority order.

### 1. Exact software environment

Yu reports Seurat version 5 but does not report exact Seurat, MAST, R, Matrix, or supporting-package versions. The local run used:

- R 4.3.3;
- Seurat 5.5.1;
- SeuratObject 5.4.0;
- MAST 1.28.0;
- Matrix 1.6.5.

Differences in Seurat's MAST wrapper, MAST likelihood-ratio calculations, convergence handling, or supporting numerical libraries could change p-values while leaving log2FC unchanged. This is currently the strongest candidate.

### 2. Exact MAST invocation

The paper may have used Seurat defaults from a different version or a direct MAST call with unreported settings. Items to verify include convergence rules, empirical-Bayes variance regularization, coefficient selection, failed-gene handling, sparse-versus-dense input, and the precise likelihood-ratio test implementation.

### 3. Exact clinical covariates and encoding

Potential differences include the clinical metadata revision, age-at-death handling for participants aged 90 or older, and the exact `nCount_RNA` field. A read-only diagnostic on End/Female/APOE-e33 compared several covariate specifications:

| Model variant | Local DEGs | Yu calls recovered |
|---|---:|---:|
| Current full model | 47 | 46/53 |
| Raw rather than scaled age and PMI | 47 | 46/53 |
| `nCount_RNA` only | 33 | 32/53 |
| No covariates | 29 | 29/53 |
| Log-transformed `nCount_RNA` with age and PMI | 44 | 43/53 |

Raw versus scaled age and PMI reproduces the current result exactly, as expected because linear centering and scaling do not change the fitted model space. Removing age and PMI or transforming `nCount_RNA` made agreement worse. The full paper-specified covariate set should therefore be retained.

### 4. Gene eligibility and failed-fit handling

Yu may have removed genes with convergence failures or missing statistics before BH correction. That would alter the number of p-values being adjusted. This appears less likely because Yu's reported p-value/FDR relationships are generally consistent with the same per-contrast testing universe used locally, which ranges from 4,400 to 6,690 returned genes.

## Adjustments tested but not recommended

Several changes can increase the number of local DEGs, but they do not reproduce Yu's gene set and would change the predeclared method.

| Alternative | Local calls | Shared with Yu | Recall | Precision | Assessment |
|---|---:|---:|---:|---:|---|
| Current BH over all returned genes | 645 | 615 | 85.9% | 95.3% | Current paper-aligned rule |
| BH only after fold-change filtering | 1,076 | 683 | 95.4% | 63.5% | Inappropriate post-selection adjustment |
| BH using all 33,538 object features | 307 | 307 | 42.9% | 100.0% | Too conservative and inconsistent with Yu's apparent universe |
| Raw `p < 0.05` without BH | 8,445 | 716 | 100.0% | 8.5% | Does not control the stated FDR |

Simply relaxing the FDR cutoff also matches only the total count, not the identities of Yu's DEGs:

| Local FDR cutoff | Local calls | Shared with Yu | Recall | Precision |
|---|---:|---:|---:|---:|
| 0.050 | 645 | 615 | 85.9% | 95.3% |
| 0.055 | 685 | 636 | 88.8% | 92.8% |
| 0.060 | 707 | 644 | 89.9% | 91.1% |
| 0.075 | 790 | 667 | 93.2% | 84.4% |
| 0.100 | 935 | 690 | 96.4% | 73.8% |

An FDR cutoff of approximately 0.0612 produces 717 local calls, close to Yu's count of 716, but only 645 are shared. Both recall and precision are approximately 90%, so this would force the count without reproducing the results.

Changing `min.pct`, applying BH only after seeing the fold changes, removing the stated covariates, omitting BH, or adding batch correction would contradict the paper or reduce agreement. These changes should not be promoted merely because they change the DEG count.

## Recommended investigation

The best next step is to obtain Yu's analysis script and `sessionInfo()`. If those are unavailable, run a controlled Seurat/MAST version matrix on representative contrasts and compare raw p-values across every available Yu DEG rather than choosing a version based on the final count. A candidate environment should improve agreement consistently across cell types and contrasts without changing the predefined thresholds, covariates, or testing family.

## Supporting artifacts

- [Overall comparison summary](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_summary.tsv)
- [Comparison by Yu contrast](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_contrast.tsv)
- [Comparison by cell type](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_cell_type.tsv)
- [Row-level mismatch report](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_mismatches.tsv.gz)
- [Phase 08 scientific status](../../results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv)
