# Phase 08 Comparison with Yu Supplemental Table S1

This document preserves the original full-production and local mismatch
investigation. The mismatch was resolved on 2026-07-22: the previous cohort
source top-coded 99 eligible ages as `90+` and Phase 02 converted them to 90,
whereas Yu used donor-specific exact ages from 90.04 to 108.28.

After switching Phase 02 to the checksum-frozen Yu 2022 clinical table and
rerunning local Phases 02, 05, and 08, Vasculature has 716 Yu DEGs, 716 Phase
08 DEGs, and 716 shared DEGs. Recall, precision, and Jaccard are all 100%, and
the alignment tier is `exact`. The older counts below remain useful as a
record of how the age-censoring defect propagated from raw MAST p-values into
BH FDR. Full Minerva production outputs remain historical until all nine RDS
branches are regenerated with the corrected cohort.

## Full Minerva production comparison

The complete Phase 08 result was compared with all 118,297 DEG rows in Yu Supplemental Table S1 using `scripts/08_compare_yu_table_s1.R`.

| Metric | Full production result |
|---|---:|
| Yu DEGs | 118,297 |
| Phase 08 DEGs | 111,601 |
| Shared DEGs | 106,599 |
| Yu-only DEGs | 11,698 |
| Phase-08-only DEGs | 5,002 |
| Recall | 90.11% |
| Precision | 95.52% |
| Jaccard similarity | 86.46% |
| Direction agreement | 100% |
| Pearson logFC correlation | 1.0 |
| Spearman logFC correlation | 1.0 |

The final alignment tier is `below_target` because recall and Jaccard similarity fall below their prespecified targets. This designation does not indicate a structural failure: the production comparison is `validated_complete`, and all 13 structural validation checks passed.

Effect sizes agree essentially exactly. All 11,698 Yu-only calls were present and tested but failed the current within-contrast BH FDR threshold; they were not lost because of a different effect direction or fold-change value. This full-production result therefore supports the same interpretation reached in the local diagnostic below: the remaining discrepancy is inferential rather than an expression-value mismatch.

Of the 324 planned fine-cell-type-by-stratum comparisons, 321 completed. Three Male/APOE-e2 AD-versus-NCI comparisons were non-estimable because one diagnosis arm had too few cells:

- CAMs;
- Mic MKI67; and
- Fib SLC4A4.

These terminal statuses were retained explicitly rather than silently omitted.

### Full-production outputs

- [Overall summary](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_summary.tsv)
- [Validation status](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_status.tsv)
- [Per-contrast comparison](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_contrast.tsv)
- [Per-cell-type comparison](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_cell_type.tsv)
- [Row-level mismatches](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_mismatches.tsv.gz)
- [Validation checks](../../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_checks.tsv)

The remaining sections examine the local five-cell-type Vasculature result in detail to identify why otherwise matching effects cross the FDR boundary differently.

## Local Vasculature count reconciliation

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

## Raw p-value comparison before adjustment

Yes—the unadjusted MAST p-values were also compared directly. Every Yu DEG row could be paired to a Phase 08 tested row by cell type, contrast, and gene. This comparison is necessarily one-sided because Supplemental Table S1 contains only Yu's reported DEGs; it does not provide raw p-values for Yu non-DEGs, so a paired p-value comparison is not possible for Phase-08-only genes.

| Scope and subset | Paired Yu rows | Phase 08 raw `p < 0.05` | Phase 08 p-value larger than Yu | Median Phase-08/Yu p-value ratio | Spearman correlation of raw p-values | Pearson correlation of `-log10(p)` |
|---|---:|---:|---:|---:|---:|---:|
| Full production, all Yu DEGs | 118,297 | 113,668 (96.1%) | 76,548 (64.7%) | 1.84 | 0.939 | 0.957 |
| Full production, Yu-only DEGs | 11,698 | 7,069 (60.4%) | 11,595 (99.1%) | 4.54 | 0.596 | 0.426 |
| Local Vasculature, all Yu DEGs | 716 | 716 (100%) | 460 (64.2%) | 1.24 | 0.948 | 0.970 |
| Local Vasculature, Yu-only DEGs | 101 | 101 (100%) | 98 (97.0%) | 2.35 | 0.603 | 0.701 |

Across all Yu rows, raw p-values are strongly correlated, but Phase 08 tends to produce larger values. That tendency is much stronger in the actual mismatches: Phase 08 has the larger raw p-value for 99.1% of the full-production Yu-only calls and 97.0% of the local Yu-only calls. In full production, 4,629 of the 11,698 Yu-only rows do not even pass raw `p < 0.05`; in the local Vasculature analysis all 101 do pass raw `p < 0.05`, but their upward-shifted values become non-significant after BH correction. The p-value ratios and log-scale correlation exclude 149 full-production pairs with a zero p-value in either result; the raw-p Spearman correlation and cutoff counts retain them.

The DEG sets were also recalculated by replacing only `FDR < 0.05` with raw `p < 0.05`, while retaining the same absolute-fold-change and detection-fraction criteria:

| Scope | Yu DEGs | Phase 08 raw-p calls | Shared | Recall | Precision | Jaccard similarity |
|---|---:|---:|---:|---:|---:|---:|
| Full production | 118,297 | 201,724 | 113,668 | 96.1% | 56.3% | 55.1% |
| Local Vasculature | 716 | 8,445 | 716 | 100% | 8.5% | 8.5% |

Thus, using unadjusted `p < 0.05` improves recall but does not reproduce Yu's DEG set: it introduces 88,056 full-production and 7,729 local calls absent from Yu Table S1. The raw-p comparison strengthens the conclusion that the mismatch begins in the MAST p-values and is then amplified by multiple-testing correction; it does not support replacing the paper's adjusted-p-value criterion with an unadjusted cutoff.

## Likely source of the difference

The most likely source is an incompletely specified inferential implementation detail. The [Yu paper](../../yu_paper/Yu_sex_apoe.pdf) specifies Seurat v5, MAST, `min.pct = 0.1`, and the `nCount_RNA`, PMI, and age covariates, but it does not freeze exact Seurat/MAST versions or fully describe covariate encoding. The local run used Seurat 5.5.1 and MAST 1.28.0.

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

- [Overall comparison summary](../../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_summary.tsv)
- [Comparison by Yu contrast](../../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_contrast.tsv)
- [Comparison by cell type](../../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_cell_type.tsv)
- [Row-level mismatch report](../../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_mismatches.tsv.gz)
- [Phase 08 scientific status](../../../results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv)
