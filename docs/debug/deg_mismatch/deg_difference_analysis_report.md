# DEG Difference Analysis Report

I have analyzed Vera Yu's differential expression gene (DEG) results reported in the `Table S1. DEGs` tab of `ALZ-22-e71463-s002.xlsx`, which is provided as one of the supplemental information of the paper. This tab contains 118,297 DEG data rows. Each row represents a gene–cell-type–contrast DEG result.

## Row number breakdown by contrast

| Contrast | Interpretation | Rows | Percent |
|---|---|---:|---:|
| `F_e2x_AD_vs_F_e2x_NCI` | Female, APOE ε2 carrier, AD vs NCI | 10,952 | 9.26% |
| `F_e33_AD_vs_F_e33_NCI` | Female, APOE ε3/ε3, AD vs NCI | 11,236 | 9.50% |
| `F_e4x_AD_vs_F_e4x_NCI` | Female, APOE ε4 carrier, AD vs NCI | 20,942 | 17.70% |
| `M_e2x_AD_vs_M_e2x_NCI` | Male, APOE ε2 carrier, AD vs NCI | 45,781 | 38.70% |
| `M_e33_AD_vs_M_e33_NCI` | Male, APOE ε3/ε3, AD vs NCI | 13,120 | 11.09% |
| `M_e4x_AD_vs_M_e4x_NCI` | Male, APOE ε4 carrier, AD vs NCI | 16,266 | 13.75% |
| **Total** |  | **118,297** | **100%** |

Yu's spreadsheet contains only DEG rows satisfying both of the following criteria:

- absolute fold change greater than 1.3 (`abs(avg_log2FC) > log2(1.3)`); and
- adjusted p-value less than 0.05 (`p_val_adj < 0.05`).

## Comparison with my DEG results

I can only compare my results with the DEG rows provided in Yu's spreadsheet. Because the spreadsheet does not include Yu's non-DEG results, a row absent from the spreadsheet cannot be compared directly at the raw-statistic level.

**In this comparison, “my side” includes only my DEG rows that meet the same thresholds: absolute fold change greater than 1.3 (`abs(logFC) > log2(1.3)`) and adjusted p-value less than 0.05 (`fdr_bh_within_contrast < 0.05`).** Rows were matched using the combination of cell type, contrast, and gene.

| Contrast | Yu DEG rows | My DEG rows | Overlapping rows | In Yu but missing from my side | Additional from my side |
|---|---:|---:|---:|---:|---:|
| `F_e2x_AD_vs_F_e2x_NCI` | 10,952 | 10,698 | 10,002 | 950 | 696 |
| `F_e33_AD_vs_F_e33_NCI` | 11,236 | 11,130 | 10,999 | 237 | 131 |
| `F_e4x_AD_vs_F_e4x_NCI` | 20,942 | 20,029 | 18,804 | 2,138 | 1,225 |
| `M_e2x_AD_vs_M_e2x_NCI` | 45,781 | 41,681 | 39,919 | 5,862 | 1,762 |
| `M_e33_AD_vs_M_e33_NCI` | 13,120 | 13,809 | 12,924 | 196 | 885 |
| `M_e4x_AD_vs_M_e4x_NCI` | 16,266 | 14,254 | 13,951 | 2,315 | 303 |
| **Total** | **118,297** | **111,601** | **106,599** | **11,698** | **5,002** |

“In Yu but missing from my side” means a DEG row reported by Yu that is not called as a DEG in my results. “Additional from my side” means a DEG row called in my results that is absent from Yu's DEG spreadsheet.

## Adjusted p-value comparison for all Yu DEG rows

All 118,297 rows in Yu's DEG spreadsheet have exactly one corresponding tested row in my Phase 08 results, matched by cell type, contrast, and gene. This comparison uses the adjusted p-value from every matched row on my side, including rows where my adjusted p-value does not pass the 0.05 DEG threshold.

| Yu DEG rows | Matched rows on my side | Missing adjusted p-values on my side | My adjusted `p < 0.05` | My adjusted `p >= 0.05` |
|---:|---:|---:|---:|---:|
| 118,297 | 118,297 | 0 | 106,599 | 11,698 |

### Absolute adjusted p-value difference

I calculated the absolute adjusted p-value difference for every matched row:

`absolute difference = abs(my adjusted p-value - Yu adjusted p-value)`

The absolute difference remains defined when either adjusted p-value is zero. The counts below are cumulative.

| Maximum absolute difference | Rows within tolerance | Percent of all 118,297 rows |
|---:|---:|---:|
| ≤0.001 | 66,349 | 56.09% |
| ≤0.005 | 84,240 | 71.21% |
| ≤0.010 | 93,547 | 79.08% |
| ≤0.020 | 102,587 | 86.72% |
| ≤0.050 | 111,244 | 94.04% |
| ≤0.100 | 115,017 | 97.23% |
| ≤0.250 | 117,607 | 99.42% |
| ≤0.500 | 118,197 | 99.92% |

The median absolute adjusted p-value difference is `0.000422`. The 75th percentile is `0.00699`, the 90th percentile is `0.0284`, and the maximum is `0.980`. Overall, 79.08% of matched rows differ by no more than 0.01 in absolute adjusted p-value and 86.72% differ by no more than 0.02.

![Cumulative absolute adjusted p-value difference tolerances](adjusted_p_value_absolute_difference.png)

*Figure 1. Number and percentage of the 118,297 matched Yu rows within each cumulative absolute adjusted p-value difference tolerance.*

## P-value comparison for all Yu DEG rows

All 118,297 rows in Yu's DEG spreadsheet have exactly one corresponding tested row with a finite raw p-value in my Phase 08 results. This comparison uses the raw p-value from every matched row on my side, including rows where my p-value does not pass 0.05.

| Yu DEG rows | Matched rows on my side | Missing p-values on my side | My `p < 0.05` | My `p >= 0.05` |
|---:|---:|---:|---:|---:|
| 118,297 | 118,297 | 0 | 113,668 | 4,629 |

### Absolute p-value difference

I calculated the absolute raw p-value difference for every matched row:

`absolute difference = abs(my p-value - Yu p-value)`

The counts below are cumulative.

| Maximum absolute difference | Rows within tolerance | Percent of all 118,297 rows |
|---:|---:|---:|
| ≤0.001 | 83,993 | 71.00% |
| ≤0.005 | 99,758 | 84.33% |
| ≤0.010 | 105,611 | 89.28% |
| ≤0.020 | 110,385 | 93.31% |
| ≤0.050 | 114,797 | 97.04% |
| ≤0.100 | 116,869 | 98.79% |
| ≤0.250 | 118,054 | 99.79% |
| ≤0.500 | 118,242 | 99.95% |

The median absolute p-value difference is `0.0000524`. The 75th percentile is `0.00162`, the 90th percentile is `0.0112`, and the maximum is `0.979`. Overall, 89.28% of matched rows differ by no more than 0.01 in absolute p-value and 93.31% differ by no more than 0.02.

![Cumulative absolute p-value difference tolerances](p_value_absolute_difference.png)

*Figure 2. Number and percentage of the 118,297 matched Yu rows within each cumulative absolute raw p-value difference tolerance.*

## Potential source of the mismatch

### 1. Exact software environment

Yu reports Seurat version 5 but does not report the exact Seurat, MAST, R, Matrix, or supporting-package versions. My code used:

- R 4.3.3;
- Seurat 5.5.1;
- SeuratObject 5.4.0;
- MAST 1.28.0; and
- Matrix 1.6.5.

Differences in Seurat's MAST library version, MAST likelihood-ratio calculations, convergence handling, or supporting numerical libraries could change p-values and adjusted p-value while leaving log2FC unchanged.
