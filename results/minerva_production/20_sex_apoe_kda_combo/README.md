# Phase 20 sex/APOE direction-combined KDA

## Status

**Current ROSMAP KDA aggregation authority.**

Current downstream candidate, human-validation, pathway, figure, and
presentation workflows should use this directory rather than the historical
Phase 18 aggregate or the earlier non-combo Phase 20 release.

## Scope

Each eligible fine-cell contrast contributes one primary `AD_both_mito` query:
the deduplicated union of its AD-up and AD-down core-MitoCarta DEGs. Eligible
calls require at least three cells per disease arm and at least three effective
query genes.

Only drivers returned as significant within an individual Phase 12 KDA call
enter the aggregate. Within each sex/APOE group × broad-cell category:

- a singleton retains its within-call BH-adjusted KDA P value;
- a recurrent driver receives an equal-weight ACAT score over its returned
  within-call adjusted P values; and
- no additional across-gene multiple-testing correction is applied.

The aggregate score is therefore exploratory and is used for ranking, not as a
formally FDR-controlled cross-call q value.

## Current counts

- 324 structural contrasts;
- 194 eligible KDA calls;
- 164 calls with at least one returned driver;
- 1,833 significant gene × call returns;
- 840 gene × sex/APOE × broad-cell aggregate rows;
- 381 non-MT aggregate rows representing 228 genes in 29 populated
  categories; and
- 123 displayed entries when non-MT genes are reranked and limited to five per
  populated category.

## Files

- `combo_run_manifest.tsv`: complete structural and eligibility ledger.
- `combo_query_members.tsv.gz`: query membership and direction provenance.
- `combo_returned_call_rows.tsv.gz`: significant within-call KDA returns.
- `combo_key_drivers_by_category.tsv`: current gene-by-category aggregates.
- `combo_category_summary.tsv`: complete category-level status summary.

The frozen run-level KDA authority is
`results/minerva_production/12_rosmap_sex_apoe_mito_kda_runs/`. This directory
is its current direction-combined reporting layer.
