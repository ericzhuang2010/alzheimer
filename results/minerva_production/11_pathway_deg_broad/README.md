# Broad-cell DEG mitochondrial pathway analysis

Validated Phase 11 release using ROSMAP donor-level broad-cell DEGs.

- Primary analysis: preranked GSEA over 42 structural contrasts (40 estimable).
- GSEA rank: `sign(logFC) * sqrt(F)` over tested core-mito genes.
- Threshold companion: ORA over strict, relaxed, and exploratory tiers.
- Program collections: legacy 4, broad MitoCarta 46, complete MitoCarta 149.
- Composition sensitivity: 28 estimable ranks.
- Local significance: BH FDR < 0.05 within the frozen local family.

Positive GSEA NES means genes tend toward the AD-up end; negative NES
means genes tend toward the AD-down end. NES is coordinated expression,
not direct evidence of pathway activity. Relaxed and exploratory ORA are
sensitivity and hypothesis-generating evidence, not confirmatory results.

The complete GSEA and ORA grids are authoritative. Significant-only files
are convenience subsets. Broad-versus-fine recurrence is descriptive
because strata and cell classes can share donors.
