# ROSMAP sex/APOE × broad-cell KDA analysis

This document analyzes the aggregated ROSMAP KDA results before considering SEA-AD validation.

## Analysis scope

- Cohort: ROSMAP only.
- Source: `results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv`.
- Category: one of six sex/APOE groups crossed with one of seven broad cell types, giving 42 possible categories.
- Analysis unit: one non-mitochondrial key-driver gene in one category.
- Mitochondrial key drivers (`is_core_mito = TRUE`) are excluded.
- A gene is counted at most once in a category.
- Fine-cell identities and fine-cell-level recurrence are not used in this section.

After these restrictions, the aggregated table contains 381 gene × category records representing 228 unique non-mitochondrial key-driver genes. Twenty-nine of the 42 possible categories contain at least one such record.

## 1. Distribution of key-driver occurrence across categories

For every key-driver gene, its occurrence count is the number of distinct sex/APOE × broad-cell categories in which it appears. The distribution is:

| Number of categories containing the gene | Number of genes | Percentage of 228 genes | Gene × category records contributed |
|---:|---:|---:|---:|
| 1 | 158 | 69.3% | 158 |
| 2 | 34 | 14.9% | 68 |
| 3 | 19 | 8.3% | 57 |
| 4 | 7 | 3.1% | 28 |
| 5 | 3 | 1.3% | 15 |
| 6 | 2 | 0.9% | 12 |
| 7 | 2 | 0.9% | 14 |
| 8 | 1 | 0.4% | 8 |
| 9 | 0 | 0.0% | 0 |
| 10 | 1 | 0.4% | 10 |
| 11 | 1 | 0.4% | 11 |
| 12–42 | 0 | 0.0% | 0 |
| **Total** | **228** | **100.0%** | **381** |

### Summary

- 158 genes (69.3%) occur in exactly one category.
- 70 genes (30.7%) occur in at least two categories.
- 36 genes (15.8%) occur in at least three categories.
- 192 genes (84.2%) occur in no more than two categories.
- The broadest key driver occurs in 11 of the 42 possible categories.

The distribution is strongly right-skewed: most key drivers are restricted to one observed category, while a small group recurs across several categories.

This is a descriptive occurrence distribution, not yet evidence that the 158 single-category genes are biologically category-specific. Thirteen of the 42 structural categories do not contribute a non-mitochondrial aggregated driver record, and the categories differ in KDA opportunity. Later specificity analyses should distinguish a tested absence from a category in which a driver could not have been evaluated.

## 2. Key drivers occurring in more than one category

Seventy of the 228 non-mitochondrial key-driver genes occur in at least two of the 42 sex/APOE × broad-cell categories. Together, these 70 genes account for 223 of the 381 gene × category records.

| Gene | Number of categories | Categories |
|---|---:|---|
| ACAT2 | 2 | F_e33 × Inhibitory neurons<br>M_e2 × Inhibitory neurons |
| ANKRD11 | 2 | F_e33 × OPCs<br>M_e2 × OPCs |
| APOE | 3 | F_e2 × Astrocytes<br>M_e2 × Astrocytes<br>M_e4 × Astrocytes |
| ATG101 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| ATP6AP2 | 3 | F_e2 × Inhibitory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| ATP6V0B | 2 | F_e2 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| ATP6V1F | 3 | F_e4 × Inhibitory neurons<br>M_e2 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| B3GAT3 | 2 | M_e33 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| BEX1 | 2 | M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| BEX3 | 3 | F_e4 × Inhibitory neurons<br>M_e2 × OPCs<br>M_e33 × Excitatory neurons |
| BTF3 | 3 | F_e2 × Excitatory neurons<br>F_e33 × Inhibitory neurons<br>M_e2 × Excitatory neurons |
| CCDC85B | 2 | F_e4 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| CHORDC1 | 2 | M_e33 × Inhibitory neurons<br>M_e33 × Microglia |
| CUTA | 2 | F_e33 × Excitatory neurons<br>M_e2 × Inhibitory neurons |
| DYNLL1 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| DYNLT1 | 3 | F_e33 × Excitatory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Excitatory neurons |
| EDF1 | 2 | F_e33 × Excitatory neurons<br>F_e33 × Inhibitory neurons |
| FAU | 2 | F_e2 × Astrocytes<br>M_e2 × Inhibitory neurons |
| FTL | 2 | F_e33 × OPCs<br>M_e2 × OPCs |
| GABARAPL2 | 5 | F_e2 × Excitatory neurons<br>F_e2 × Inhibitory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| GALNT2 | 2 | F_e33 × Inhibitory neurons<br>M_e2 × Inhibitory neurons |
| GAPDH | 5 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons<br>M_e2 × OPCs<br>M_e33 × Inhibitory neurons |
| GATAD1 | 3 | F_e2 × Inhibitory neurons<br>F_e33 × Inhibitory neurons<br>M_e2 × Inhibitory neurons |
| GNG3 | 2 | F_e2 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| HSPA1A | 3 | F_e4 × Inhibitory neurons<br>F_e4 × Vasculature<br>M_e33 × Inhibitory neurons |
| HSPH1 | 2 | F_e4 × Vasculature<br>M_e33 × Microglia |
| KTN1 | 2 | F_e33 × Inhibitory neurons<br>M_e2 × Inhibitory neurons |
| LAGE3 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| LAMTOR5 | 6 | F_e2 × Excitatory neurons<br>F_e33 × Inhibitory neurons<br>F_e4 × Excitatory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Excitatory neurons<br>M_e2 × Inhibitory neurons |
| LAPTM4A | 2 | M_e2 × Astrocytes<br>M_e4 × Astrocytes |
| MAGEF1 | 3 | F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| MAP1LC3A | 2 | M_e33 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| METTL21A | 2 | F_e4 × Inhibitory neurons<br>M_e33 × Inhibitory neurons |
| MIPOL1 | 2 | F_e4 × Inhibitory neurons<br>M_e33 × Inhibitory neurons |
| MT3 | 2 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons |
| PCBP4 | 3 | F_e4 × Inhibitory neurons<br>M_e33 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| PER3 | 2 | F_e33 × Inhibitory neurons<br>F_e4 × Inhibitory neurons |
| PGAM1 | 4 | M_e2 × Inhibitory neurons<br>M_e33 × Excitatory neurons<br>M_e4 × Excitatory neurons<br>M_e4 × Inhibitory neurons |
| PGK1 | 3 | F_e33 × Astrocytes<br>F_e4 × Astrocytes<br>M_e4 × Astrocytes |
| PLCG2 | 3 | F_e2 × Inhibitory neurons<br>F_e33 × Inhibitory neurons<br>F_e4 × Inhibitory neurons |
| PRDX1 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| PSMB6 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| RABAC1 | 4 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| RPL11 | 10 | F_e2 × Astrocytes<br>F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Astrocytes<br>M_e2 × Excitatory neurons<br>M_e2 × Oligodendrocytes<br>M_e33 × Excitatory neurons<br>M_e4 × Astrocytes<br>M_e4 × Microglia |
| RPL15 | 7 | F_e2 × Astrocytes<br>F_e2 × Inhibitory neurons<br>F_e4 × Astrocytes<br>F_e4 × Excitatory neurons<br>M_e2 × Astrocytes<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons |
| RPL29 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| RPL36 | 2 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons |
| RPL36AL | 4 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| RPL6 | 3 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| RPLP1 | 8 | F_e2 × Astrocytes<br>F_e2 × Inhibitory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Astrocytes<br>M_e2 × Inhibitory neurons<br>M_e33 × Inhibitory neurons<br>M_e4 × Astrocytes<br>M_e4 × Inhibitory neurons |
| RPLP2 | 4 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| RPS13 | 5 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Inhibitory neurons<br>M_e4 × Excitatory neurons |
| RPS15 | 11 | F_e2 × Astrocytes<br>F_e2 × Excitatory neurons<br>F_e2 × Inhibitory neurons<br>F_e33 × Excitatory neurons<br>F_e33 × OPCs<br>F_e4 × Inhibitory neurons<br>M_e2 × Excitatory neurons<br>M_e2 × Inhibitory neurons<br>M_e2 × OPCs<br>M_e33 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| RPS25 | 2 | M_e33 × Inhibitory neurons<br>M_e4 × Astrocytes |
| RPS4X | 2 | F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| SELENOM | 7 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons<br>M_e4 × Inhibitory neurons |
| SELENOW | 6 | F_e2 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Excitatory neurons<br>M_e33 × Excitatory neurons<br>M_e33 × Inhibitory neurons |
| SPATS2L | 2 | F_e4 × Vasculature<br>M_e33 × Vasculature |
| SRSF7 | 2 | F_e33 × Excitatory neurons<br>F_e33 × Inhibitory neurons |
| SSR2 | 2 | F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| SYN1 | 4 | F_e2 × Inhibitory neurons<br>F_e33 × Inhibitory neurons<br>F_e4 × Inhibitory neurons<br>M_e2 × Inhibitory neurons |
| TMEM147 | 4 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>F_e4 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| TPI1 | 2 | F_e2 × Excitatory neurons<br>M_e2 × Excitatory neurons |
| TRERF1 | 2 | F_e33 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
| TTC8 | 2 | F_e4 × Excitatory neurons<br>M_e4 × Excitatory neurons |
| TUBA1A | 2 | F_e33 × Inhibitory neurons<br>M_e33 × OPCs |
| UBB | 2 | M_e33 × Inhibitory neurons<br>M_e33 × OPCs |
| UBC | 2 | F_e4 × Excitatory neurons<br>M_e33 × OPCs |
| WDR82 | 4 | F_e2 × Excitatory neurons<br>F_e33 × Excitatory neurons<br>M_e33 × Excitatory neurons<br>M_e4 × Excitatory neurons |
| ZNF280D | 2 | F_e4 × Inhibitory neurons<br>M_e4 × Inhibitory neurons |
