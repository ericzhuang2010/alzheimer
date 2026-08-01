# Pooled versus sex/APOE-stratified DEG analysis

No—the results would not be the same.

Phase 08 currently fits, for each fine cell type, six separate models:

\[
\text{expression} \sim \text{AD/NCI} + nCount\_RNA + age + PMI
\]

with the data first restricted to each sex × APOE group. Consequently, every group gets its own logFC, p-value, detection percentage, and within-contrast FDR ([Phase 08 plan](phase_08_yu_deg_alignment_plan.md#analysis-population), [model specification](phase_08_yu_deg_alignment_plan.md#mast-model)).

If you pool all donors and run one AD-versus-NCI test, you get only one cohort-average AD effect per gene. Splitting that DEG table afterward would merely copy the same global result into six groups; it cannot recover group-specific effects. This can:

- Hide a DEG that is strong in only one group.
- Cancel opposite effects across groups.
- Produce apparent DEGs from unequal sex/APOE composition between AD and NCI.
- Change `min.pct` gene filtering, logFC, p-values, and FDR.
- Give much smaller p-values simply because the pooled sample is larger.

A single joint model could use `diagnosis × sex × APOE` interactions and calculate six group-specific contrasts. That is statistically legitimate, but it still will not generally reproduce the six separate MAST fits because model parameters and uncertainty are shared across groups.

So my recommendation is:

- Keep the six separate fits for Phase 08 because its purpose is Yu-compatible, sex/APOE-specific DEG analysis.
- If you also want the overall AD signature, add a separate pooled AD-versus-NCI analysis.
- For primary inference across donors, prefer the donor-level pseudobulk branch in Phase 07; Phase 08 MAST treats nuclei as cell-level observations and is documented as a comparability analysis rather than the primary donor-level test.
