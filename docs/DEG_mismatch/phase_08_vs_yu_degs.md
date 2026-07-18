# Phase 08 Differentially Expressed Genes Versus Yu et al.

No—the Phase 08 DEGs are not exactly the same as Yu's, but the overlap is high once restricted to contrasts Phase 08 actually ran.

I compared exact `(cell type, sex–APOE contrast, gene)` calls from Yu's [Table S1 workbook](../yu_paper/ALZ-22-e71463-s002.xlsx) with all nine production files in the [Phase 08 outputs](../../results/minerva_production/08_mast/).

| Comparison scope | Yu DEGs | Phase 08 DEGs | Shared | Yu recovered | Phase 08 supported by Yu |
|---|---:|---:|---:|---:|---:|
| All 324 Yu contrasts | 118,297 | 87,710 | 78,773 | 66.6% | 89.8% |
| Only the 188 contrasts Phase 08 ran | 90,345 | 87,710 | 78,773 | **87.2%** | **89.8%** |

For the comparable 188 contrasts:

- Jaccard overlap was **79.3%**.
- All **78,773 shared calls had the same direction**.
- Effect sizes were almost identical: Pearson \(r=0.998\), Spearman \(ρ=0.995\).
- Median absolute log2FC difference was only **0.0085**.

If "same genes" means gene symbols collapsed across all cell types and contrasts, agreement is even higher:

- Yu: 14,840 unique DEG symbols.
- Phase 08: 14,102.
- Shared: **14,006**.
- Gene-list Jaccard overlap: **93.8%**.

## Why They Are Not Identical

The main reason is Phase 08's additional eligibility filtering. It requires at least 20 nuclei per donor-cell type and five donors per contrast arm, configured in [`analysis_parameters.yml`](../../config/analysis_parameters.yml#L89) and applied before MAST in [`08_run_mast.R`](../../scripts/08_run_mast.R#L302).

Consequently:

- Yu ran or described all **324** cell-type × sex–APOE contrasts.
- Phase 08 completed **188** and declared **136 ineligible**.
- Those ineligible contrasts contain **27,952 Yu DEG calls**.
- Male ε2 was most affected: only 10 of 54 cell types were eligible.

Among Yu calls in the 188 comparable contrasts, the remaining mismatches were:

| Reason a Yu DEG was not reproduced | Count |
|---|---:|
| Failed current Phase 08 FDR | 8,907 |
| Failed current fold-change threshold | 1,577 |
| Failed both | 830 |
| Gene not returned by current MAST detection filter | 258 |

Conversely, Phase 08 produced **8,937 new calls** that did not pass Yu's Table S1 criteria. These shifts are consistent with using different donor/cell subsets even though the MAST procedure itself is closely matched: the same Seurat `FindMarkers`, MAST, 10% detection filter, covariates, BH FDR, and 1.3-fold threshold ([implementation](../../scripts/08_run_mast.R#L383)).

## Mitochondrial-Specific Agreement

| Subset, comparable contrasts | Yu | Phase 08 | Shared | Yu recovered | Phase 08 supported |
|---|---:|---:|---:|---:|---:|
| 13 mtDNA genes | 664 | 678 | 596 | **89.8%** | **87.9%** |
| MitoCarta genes | 7,056 | 6,905 | 6,129 | **86.9%** | **88.8%** |

For `MT-ND2`, Phase 08 reproduced **70 of 76** Yu calls occurring in eligible contrasts, all with the same direction. Yu reported 102 `MT-ND2` calls overall; most of the additional missing calls occurred in contrasts Phase 08 deemed ineligible.

The [supplemental DOCX](../yu_paper/ALZ-22-e71463-s001.docx) contains only the sex-discordance and scDesign3 power figures; it does not define additional DEG calls beyond Table S1.

## Conclusion

The gene universe and biological effects are very similar, but the condition-specific DEG sets are not identical—there is about **87–90% agreement for contrasts that both analyses cover**.
