# Phase 19b combo-driver genetic-support freeze

## Status

**Current Phase 19 candidate authority.**

This bundle freezes all 228 non-MT genes returned by the Phase 20
direction-combined KDA aggregation, preserving 381 sex/APOE × broad-network
contexts. It supersedes the original 25-gene Phase 18 freeze and the previous
433-gene non-combo Phase 20 rerun.

Source:

```text
results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv
```

`candidates.tsv` contains one row per gene. `candidate_contexts.tsv` preserves
every returned group/network unit and a non-MT display rank recomputed within
each category. `candidate_loci.tsv` maps 226 genes to GENCODE v44 GRCh38
loci; `AL035071.1` and `AL139260.1` remain explicitly unmapped.

The matched SEA-AD combo list assigns three P1 cross-cohort genes: `LAGE3`,
`MIPOL1`, and `PAPOLA`. The remaining freeze contains 113 P2 and 112 P3 genes.

The public-summary Tier 1 screen is complete in
`../19b_genetic_support_tier1/`. Regional outputs in
`../19b_genetic_support_regional/` are explicitly partial because the raw GWAS
files needed to scan 30 newly introduced autosomal genes are unavailable on
this machine.
