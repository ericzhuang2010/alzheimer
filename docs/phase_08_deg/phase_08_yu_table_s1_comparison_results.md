# Phase 08 Comparison with Yu Supplemental Table S1

Completed the full Phase 08 comparison against Yu Supplemental Table S1 using `scripts/08_compare_yu_table_s1.R`.

## Key results

- Yu DEGs: 118,297
- Phase 08 DEGs: 111,601
- Shared: 106,599
- Yu-only: 11,698
- Phase 08-only: 5,002
- Recall: 90.11%
- Precision: 95.52%
- Jaccard: 86.46%
- Direction agreement: 100%
- Pearson/Spearman logFC correlation: 1.0
- Alignment tier: `below_target`
- Structural validation: `validated_complete` — 13/13 checks passed

The alignment tier is driven by recall and Jaccard falling below their targets. Effect sizes agree essentially exactly. All 11,698 Yu-only calls failed the current within-contrast FDR threshold, rather than differing in direction or fold change.

Of 324 comparisons, 321 completed and three were non-estimable because of insufficient cells: CAMs, Mic MKI67, and Fib SLC4A4 for `M_e2x_AD_vs_M_e2x_NCI`.

## Outputs

- [Overall summary](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_summary.tsv)
- [Validation status](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_status.tsv)
- [Per-contrast comparison](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_contrast.tsv)
- [Per-cell-type comparison](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_by_cell_type.tsv)
- [Row-level mismatches](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_mismatches.tsv.gz)
- [Validation checks](../../results/minerva_production/08_mast/yu_table_s1_validation/yu_table_s1_comparison_checks.tsv)
