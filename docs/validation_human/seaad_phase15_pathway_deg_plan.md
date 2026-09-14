# SEA-AD VH15 DEG Pathway Analysis Plan

## Objective

Run pathway/program analysis for the independent SEA-AD fine- and broad-cell
DEG releases in a form that can be compared directly with the corresponding
ROSMAP analyses:

- fine output: `results/validation_human/15_pathway_deg_fine/`
- broad output: `results/validation_human/15_pathway_deg_broad/`

The analysis is restricted to mitochondrial genes and mitochondrial
pathways/programs. It does not test whole-transcriptome pathways.

## Shared pathway catalog

Both resolutions use one frozen catalog:

1. the four legacy respiratory/mitochondrial programs;
2. 46 broad MitoCarta3.0 programs at hierarchy depths 1-2;
3. all 149 MitoCarta3.0 pathways at hierarchy depths 1-3.

The source is the checksum-frozen
`data/reference/Human.MitoCarta3.0.xls`. Both releases publish the normalized
program membership used in every test.

## Fine-cell analysis

The fine analysis mirrors the ROSMAP fine-cell ORA contract.

- Unit: 129 fine cell types x six sex/APOE strata = 774 structural contrasts.
- Estimability: 381 contrasts completed; 393 remain explicitly
  non-estimable. All 258 APOE e2 contrasts (129 female and 129 male) are
  non-estimable because the Dementia arm is below the donor minimum.
- DEG rule: FDR < 0.05 and absolute fold change > 1.3.
- Queries per contrast: any-direction, Dementia-up, and Dementia-down
  mitochondrial DEGs.
- Background: core mitochondrial genes that passed `filterByExpr` and were
  tested in that fine-cell context.
- Method: one-sided hypergeometric over-representation analysis (ORA).
- Multiple testing: BH FDR within each query and pathway collection, plus
  declared global families by query mode and collection.

A separate companion applies the same ORA catalog to the 22 eligible
merged-direction SEA-AD KDA input queries. Those VH10 queries use the
FDR-only sensitivity rule, not the strict FDR-plus-fold-change rule used by
the primary pathway analysis. The companion is therefore labeled separately
and is not mixed with the primary pre-network DEG analysis.

## Broad-cell analysis

The broad analysis mirrors the ROSMAP sex/APOE broad-cell contract.

- Unit: seven broad cell types x six sex/APOE strata = 42 structural
  contrasts.
- Estimability: 28 contrasts completed; all 14 APOE e2 contrasts remain
  explicitly non-estimable.
- Primary method: preranked GSEA across every tested core mitochondrial gene.
- Rank statistic: `sign(logFC) * sqrt(max(F, 0))`.
- Thresholded companion: ORA at strict, relaxed, and exploratory DEG tiers.
- Background: the tested core mitochondrial universe for each broad cell
  type.
- Multiple testing: BH FDR within contrast and pathway collection, plus
  declared global families.

The seven pooled Dementia-versus-No-dementia anchors are excluded from the
primary release because they do not represent sex/APOE strata and therefore
do not have a direct ROSMAP counterpart. SEA-AD also lacks the
ROSMAP-equivalent composition-adjusted DEG release, so no
composition-sensitivity GSEA is imputed or fabricated.

## Broad-versus-fine comparison

Strict broad ORA records are compared with fine ORA records after grouping
fine cells by broad cell type, sex, APOE group, query direction, and pathway.
Each record is classified as:

- `concordant_support`
- `broad_only`
- `fine_only`
- `neither`
- `not_comparable`

`not_comparable` is required whenever either resolution is not testable.

## Validation and provenance

Both releases:

- validate every declared VH08 input artifact by size and SHA-256;
- use fine-cell filter-derived tested backgrounds that reproduce the
  per-contrast tested core-mito universes exactly in all 381 completed
  contrasts;
- reproduce all 3,904 frozen MitoCarta pathway memberships from the ROSMAP
  Phase 11 reference exactly;
- bind the exact config, scripts, pathway sources, and upstream manifests;
- reproduce ORA p-values from the reported contingency-table counts;
- reproduce BH FDR significance flags;
- verify that every query gene belongs to its statistical background;
- preserve non-estimable contrasts rather than treating them as null results;
- publish through a process-specific staging directory followed by an atomic
  rename; and
- refuse to overwrite an existing invalid release.

The production test is
`tests/validation_human/test_seaad_phase15_pathway_analysis.R`.
