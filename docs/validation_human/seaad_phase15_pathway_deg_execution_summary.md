# SEA-AD VH15 DEG Pathway Analysis Execution Summary

## Release status

Both requested pathway releases completed locally and passed their blocking
contracts:

- `results/validation_human/15_pathway_deg_fine/`: `validated_complete`
  with 19/19 blocking checks passed.
- `results/validation_human/15_pathway_deg_broad/`: `validated_complete`
  with 25/25 blocking checks passed.
- The independent production test
  `tests/validation_human/test_seaad_phase15_pathway_analysis.R` passed.
- Re-running either production command recognized the existing release as
  complete and hash-valid without rewriting it.

## Fine-cell results

The fine release retained all 774 structural fine-cell x sex/APOE contrasts:
381 were estimable and 393 were explicitly non-estimable. All 258 APOE e2
contrasts were non-estimable because the Dementia arm did not meet the donor
minimum.

Strict DEG ORA produced:

- 462,078 complete query-by-program records;
- 11,450 statistically testable records;
- 42 locally significant records and 24 globally significant records; and
- 42 local discoveries confined to neuronal APOE e3/e3 strata:
  20 in female e3/e3 and 22 in male e3/e3.

The significant records came from four fine neuronal types:
`L2/3 IT_1`, `Lamp5_2`, `Pvalb_2`, and `Pvalb_14`. The strongest recurring
theme was mtDNA-encoded OXPHOS/OXPHOS subunits.

The separate 22-query KDA companion produced 18 locally significant and nine
globally significant records. The strongest examples included female e3/e3
`L2/3 IT_1` and male e3/e3 `Pvalb_14` mtDNA-encoded OXPHOS
over-representation. This companion reuses KDA input genes and is not
independent evidence from the primary DEG ORA. It also uses VH10's FDR-only,
merged-direction KDA query rule rather than the strict
FDR-plus-fold-change rule used for the primary fine-cell ORA.

## Broad-cell results

The broad release analyzed the 42 sex/APOE-stratified broad-cell contrasts:
28 were estimable and all 14 APOE e2 contrasts were explicitly
non-estimable. The seven pooled anchors were excluded because they do not
have a direct sex/APOE ROSMAP counterpart.

Primary full-rank GSEA produced:

- 8,358 complete contrast-by-program records;
- 4,360 statistically testable records;
- 256 locally significant records and 218 globally significant records.

The direction counts among locally significant GSEA records were:

- female e3/e3: 9 Dementia-up and 37 Dementia-down;
- female e4: 72 Dementia-up and 22 Dementia-down;
- male e3/e3: 26 Dementia-up and 3 Dementia-down; and
- male e4: 75 Dementia-up and 12 Dementia-down.

Recurring programs included nuclear structural OXPHOS, mtDNA-encoded OXPHOS,
OXPHOS/OXPHOS subunits, Complex I/CI subunits, mitochondrial ribosome, and
mitochondrial translation. In particular, all 21 locally significant
mtDNA-encoded OXPHOS GSEA records were Dementia-up, whereas nuclear structural
OXPHOS included both up and down shifts.

Thresholded broad ORA produced 77 locally significant and 64 globally
significant records. Only seven local discoveries passed the strict tier; the
larger relaxed and exploratory result sets should remain sensitivity and
hypothesis-generating evidence.

Four structurally eligible GSEA records had no finite result returned by
`fgsea`. They are explicitly labeled `fgsea_no_finite_result` and
`not_testable`, rather than being counted as negative findings.

## Broad-versus-fine strict ORA

There were three records with locally significant support at both
resolutions, all for the legacy mtDNA-encoded OXPHOS program:

1. male e3/e3 inhibitory neurons, Dementia-up;
2. male e3/e3 inhibitory neurons, any direction; and
3. male e3/e3 excitatory neurons, Dementia-up.

The full classification contained 17 fine-only, four broad-only, 2,029
neither, and 23,021 not-comparable records. The large not-comparable count
mainly reflects non-estimable SEA-AD strata or DEG queries below the
three-gene minimum; it must not be interpreted as cross-resolution
disagreement.

## Interpretation notes

- Counts are pathway **records**, not counts of wholly independent biological
  mechanisms. The 46 broad MitoCarta definitions are also represented inside
  the 149-pathway complete collection, and related hierarchy levels overlap.
- GSEA and ORA answer different questions. GSEA can detect coordinated weak
  shifts even when too few genes pass a hard DEG threshold for ORA.
- SEA-AD's small sex/APOE strata reduce estimability. Missing or non-testable
  support is not evidence against a ROSMAP result.
- SEA-AD has no matched composition-adjusted broad DEG release, so a
  composition-sensitivity analysis was not fabricated.
- A post-release audit confirmed that filter-derived fine backgrounds exactly
  matched the per-contrast tested core-mito universe in all 381 completed
  contrasts (334,917 background rows on each side), and that all 3,904
  MitoCarta memberships exactly matched the frozen ROSMAP Phase 11 reference.
