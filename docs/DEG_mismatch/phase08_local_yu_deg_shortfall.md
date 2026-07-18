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

## Supporting artifacts

- [Overall comparison summary](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_summary.tsv)
- [Comparison by Yu contrast](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_contrast.tsv)
- [Comparison by cell type](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_cell_type.tsv)
- [Row-level mismatch report](../../results/local_pilot/08_mast/yu_table_s1_validation/yu_table_s1_mismatches.tsv.gz)
- [Phase 08 scientific status](../../results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv)
