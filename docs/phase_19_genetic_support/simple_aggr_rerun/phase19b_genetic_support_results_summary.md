# Phase 19b genetic-support rerun results

**Completed:** 2026-09-14
**Authoritative candidate source:** `results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv`
**Scope:** 228 non-MT genes, 381 sex/APOE × broad-network contexts; QTL/coloc follow-up restricted a priori to P1+P2 (116 genes, 269 contexts).

## Outcome

All six Phase 19b workstreams are terminal and validated. Tier 1 graded 2 genes strong, 1 moderate, 9 weak, and 216 none found. The combined gene-level result contains 2 strong, 1 moderate, 9 weak, and 216 none found.

The four GWAS regional scans found genome-wide-significant variants near 20 unique genes. These are proximity annotations only and were not used as gene-level validation.

MAGMA tested 832 of 912 candidate-trait rows. At the frozen family-wise threshold `0.05 / (228 × 4) = 5.4824561e-05`, 6 gene-trait rows (3 unique genes: APOE, INTS8, PLCG2) passed. The three CSF full-genome scans were reused only after exact historical result checksum validation; clinical AD was run fresh with MAGMA v1.10 using the published total sample count (111,326 cases/proxy cases + 677,663 controls).

The public NG00184 fine-mapping audit yielded 538 gene-context-modality routes, including 269 source-significant routes across 90 genes. Public QTL sources are broad-cell/bulk-brain and not sex/APOE-stratified, so they do not validate a sex/APOE-specific KDA effect.

The coloc gate considered 2152 QTL × GWAS-trait decisions; 47 had both a regional GWAS signal and a source-significant QTL signal. None had a complete fitted multi-signal QTL model plus compatible source-matched LD/full statistics, so zero valid H0-H4 tests were produced. These routes are explicitly `not_assessable`, not negative colocalizations.

## Gene-level interpretation

A corrected MAGMA association is counted as weak gene-level statistical support. Regional GWAS proximity and QTL signal without a valid disease-QTL colocalization are annotation only. No Phase 19b gene receives strong colocalization support from the available public inputs.

## Result bundles

- `results/minerva_production/19b_genetic_support_candidates/` — frozen candidates and loci (WS0).
- `results/minerva_production/19b_genetic_support_tier1/` — public summary screen (WS1).
- `results/minerva_production/19b_genetic_support_regional/` — four complete regional GWAS scans (WS2).
- `results/minerva_production/19b_genetic_support_magma/` — four-trait candidate MAGMA results and provenance (WS3).
- `results/minerva_production/19b_genetic_support_qtl/` — P1/P2 QTL fine-mapping and coverage audit (WS4).
- `results/minerva_production/19b_genetic_support_coloc/` — coloc gate decisions and final gene table (WS5).

The five `19_genetic_support_* (deprecated)` bundles are immutable historical outputs for the earlier 25-gene Phase 18 freeze. They are retained for provenance and are not current inputs except for the explicitly checksum-validated CSF MAGMA result reuse documented above.
