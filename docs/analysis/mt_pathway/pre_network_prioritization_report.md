# Pre-network mitochondrial regulator prioritization

## Bottom line

This is an evidence-integrated nomination analysis, not a causal key-driver analysis. The existing repository supports strong mitochondrial pathway divergence, but the local data do not include the cell-type Bayesian networks needed to establish network hubs.

The analysis deliberately separates nuclear regulatory-control candidates from structural OXPHOS/mtDNA markers. Structural genes can be excellent experimental readouts without being plausible upstream regulators.

## Preliminary perturbation shortlist

- **1. ATP5IF1 (Tier A)** — control annotation; AD-vs-NCI DEG in 34 contexts across 20 cell types, 8 broad lineages, and 5/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 90.4/100; median control-gene rank 1 across three weighting schemes.
- **2. TUFM (Tier A)** — genome_expression; AD-vs-NCI DEG in 19 contexts across 16 cell types, 7 broad lineages, and 6/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 74.4/100; median control-gene rank 2 across three weighting schemes.
- **3. HSPD1 (Tier A)** — proteostasis_import; AD-vs-NCI DEG in 37 contexts across 26 cell types, 9 broad lineages, and 6/6 strata; bottom-200 divergent tail in 4/6 comparisons spanning 3/3 comparison families. Balanced evidence score 74.2/100; median control-gene rank 3 across three weighting schemes.
- **4. TOMM7 (Tier A)** — dynamics_surveillance,proteostasis_import; AD-vs-NCI DEG in 25 contexts across 19 cell types, 7 broad lineages, and 6/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 69.5/100; median control-gene rank 4 across three weighting schemes.
- **5. FKBP8 (Tier A)** — dynamics_surveillance; AD-vs-NCI DEG in 28 contexts across 17 cell types, 6 broad lineages, and 6/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 68.1/100; median control-gene rank 5 across three weighting schemes.
- **6. UQCC2 (Tier A)** — oxphos_assembly; AD-vs-NCI DEG in 12 contexts across 10 cell types, 6 broad lineages, and 4/6 strata; bottom-200 divergent tail in 5/6 comparisons spanning 3/3 comparison families. Balanced evidence score 72.6/100; median control-gene rank 6 across three weighting schemes.
- **7. DMAC1 (Tier A)** — oxphos_assembly; AD-vs-NCI DEG in 12 contexts across 10 cell types, 4 broad lineages, and 5/6 strata; bottom-200 divergent tail in 5/6 comparisons spanning 3/3 comparison families. Balanced evidence score 72.0/100; median control-gene rank 7 across three weighting schemes.
- **8. TMEM126B (Tier A)** — oxphos_assembly; AD-vs-NCI DEG in 11 contexts across 9 cell types, 4 broad lineages, and 5/6 strata; bottom-200 divergent tail in 5/6 comparisons spanning 3/3 comparison families. Balanced evidence score 69.5/100; median control-gene rank 9 across three weighting schemes.
- **9. APOO (Tier B)** — dynamics_surveillance; AD-vs-NCI DEG in 21 contexts across 16 cell types, 8 broad lineages, and 4/6 strata; bottom-200 divergent tail in 4/6 comparisons spanning 3/3 comparison families. Balanced evidence score 66.3/100; median control-gene rank 9 across three weighting schemes.
- **10. MRPS7 (Tier B)** — genome_expression; AD-vs-NCI DEG in 13 contexts across 12 cell types, 5 broad lineages, and 5/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 65.9/100; median control-gene rank 10 across three weighting schemes.
- **11. TIMM13 (Tier B)** — proteostasis_import; AD-vs-NCI DEG in 17 contexts across 13 cell types, 4 broad lineages, and 5/6 strata; bottom-200 divergent tail in 6/6 comparisons spanning 3/3 comparison families. Balanced evidence score 64.0/100; median control-gene rank 10 across three weighting schemes.
- **12. FIS1 (Tier B)** — dynamics_surveillance; AD-vs-NCI DEG in 22 contexts across 15 cell types, 5 broad lineages, and 5/6 strata; bottom-200 divergent tail in 5/6 comparisons spanning 3/3 comparison families. Balanced evidence score 63.0/100; median control-gene rank 12 across three weighting schemes.
- **13. SLIRP (Tier B)** — genome_expression; AD-vs-NCI DEG in 20 contexts across 16 cell types, 7 broad lineages, and 3/6 strata; bottom-200 divergent tail in 5/6 comparisons spanning 3/3 comparison families. Balanced evidence score 61.3/100; median control-gene rank 13 across three weighting schemes.
- **14. NDUFAF4 (Tier B)** — oxphos_assembly; AD-vs-NCI DEG in 12 contexts across 10 cell types, 4 broad lineages, and 4/6 strata; bottom-200 divergent tail in 4/6 comparisons spanning 3/3 comparison families. Balanced evidence score 63.8/100; median control-gene rank 14 across three weighting schemes.
- **15. PARK7 (Tier B)** — dynamics_surveillance,proteostasis_import; AD-vs-NCI DEG in 21 contexts across 17 cell types, 7 broad lineages, and 4/6 strata; bottom-200 divergent tail in 3/6 comparisons spanning 3/3 comparison families. Balanced evidence score 62.9/100; median control-gene rank 14 across three weighting schemes.

## Sentinel/readout genes

These genes carry strong mitochondrial phenotype signal but should not be called key regulators from these data alone:

- **MT-ND2** — 102 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 97.5/100.
- **COX4I1** — 46 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 96.0/100.
- **MT-ND4** — 77 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 95.9/100.
- **MT-CO2** — 67 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 94.5/100.
- **COX5B** — 37 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 94.4/100.
- **ATP5F1E** — 41 significant AD-vs-NCI contexts, 6/6 divergent tails, balanced evidence score 94.4/100.

## Evidence used

- Phase 09 MAST mitochondrial DEG recurrence, effect size, cell-type breadth, broad-lineage breadth, and sex/APOE stratum breadth.
- Phase 10 bottom-200 similarity-tail recurrence and rank across six sex/APOE comparison definitions.
- Phase 11 query-level support from FDR-significant MitoCarta and MSigDB pathway enrichments; redundant pathway counts are reported but are not treated as independent evidence.
- MitoCarta pathway annotations and HGNC names to distinguish control processes from structural/pathway-effector roles.
- Three transparent score weightings (balanced, DEG-heavy, and context-heavy) to expose ranking sensitivity.

## Important limits

- Phase 08 supplied modeled statistics for up to **321/324** planned contexts; three male-e2 contrasts were not estimable.
- Gene-level Phase 10 directional FDR hits in this analysis: **0**. Similarity ranks are therefore descriptive; pathway-level coordination is stronger than single-gene evidence.
- The six comparison definitions are nested, so 6/6 tail recurrence is robustness evidence, not six independent replications.
- Current DEG evidence is MAST cell-level inference, not donor-level pseudobulk or formal AD-by-sex/APOE interaction testing.
- MSigDB pathway hits are highly redundant, especially for OXPHOS and neurodegeneration collections.
- No Bayesian-network KDA, coexpression centrality, AD GWAS, eQTL, or perturbation evidence is included in the score.

## Required confirmation step

Project pathway/contrast-specific DEG signatures onto the matching cell-type Bayesian networks, test directed neighborhoods by hypergeometric enrichment with BH correction, and retain candidates that are both locally supported here and significant network key drivers. Treat mtDNA/OXPHOS sentinels as downstream assay readouts.

## Output files

- `pre_network_candidate_scores.tsv`: all core-mito candidates and fully decomposed scores.
- `pre_network_shortlist.tsv`: nuclear regulatory-control shortlist.
- `pre_network_shortlist_contexts.tsv`: every significant context for shortlisted genes.
- `pre_network_shortlist_strata.tsv`: sex/APOE stratum summaries.
- `pre_network_shortlist_lineages.tsv`: normalized broad-lineage summaries.
- `pre_network_sentinel_markers.tsv`: structural phenotype markers.
