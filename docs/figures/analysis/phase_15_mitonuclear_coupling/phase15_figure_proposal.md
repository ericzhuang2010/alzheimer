# Proposed figures for Phase 15 mitonuclear-coupling analysis

## Implementation status

Implemented and validated on 2026-08-10. The reproducible renderer is
[plot_phase15_mitonuclear_coupling_figures.py](../../../../scripts/figures/analysis/phase15_mitonuclear_coupling/plot_phase15_mitonuclear_coupling_figures.py),
and the package-level validation summary is
[phase15_figure_package_status.tsv](../../../../results/figures/analysis/phase15_mitonuclear_coupling/phase15_figure_package_status.tsv).

The generated figure families are:

- [Complete C3 evidence landscape](../../../../results/figures/analysis/phase15_mitonuclear_coupling/complete_evidence_landscape/phase15_complete_evidence_landscape.png)
- [Primary-context mitonuclear geometry](../../../../results/figures/analysis/phase15_mitonuclear_coupling/primary_coupling_geometry/phase15_primary_coupling_geometry.png)
- [Testability, precision, and stability](../../../../results/figures/analysis/phase15_mitonuclear_coupling/testability_precision_stability/phase15_testability_precision_stability.png)
- [Complete endpoint forest](../../../../results/figures/analysis/phase15_mitonuclear_coupling/complete_endpoint_forest/phase15_complete_endpoint_forest.png)
- [Adjusted stratum-effect atlas](../../../../results/figures/analysis/phase15_mitonuclear_coupling/stratum_effects/phase15_stratum_effects.png)
- [Slope-departure atlas: representative astrocyte page](../../../../results/figures/analysis/phase15_mitonuclear_coupling/slope_departure_atlas/phase15_slope_departure_atlas_astrocytes.png)
- [Row-level stability atlas](../../../../results/figures/analysis/phase15_mitonuclear_coupling/stability_atlas/phase15_stability_atlas.png)
- [Score and NCI-reference reliability](../../../../results/figures/analysis/phase15_mitonuclear_coupling/score_reference_reliability/phase15_score_reference_reliability.png)

All eight families passed their recorded checks with zero failures. The
package contains 42 image artifacts: SVG, PDF, and 300-dpi PNG outputs for the
seven single figures and all seven context pages of the slope-departure atlas.
Each family also contains plotted data, a caption, methods, source/output
hashes, checks, and terminal status metadata. The rendered previews were
manually reviewed for title and label clipping, panel boundaries, color
accessibility, grayscale-redundant status encodings, and correct treatment of
not-testable results.

The figures explain the complete evidence, its uncertainty, and why the
prespecified C3 gate did not pass. They do not promote nominally small P values
into positive biological claims.

## Production result that the figures must communicate

Phase 15 tested whether AD changes the RNA-level relationship between a
13-gene mtDNA OXPHOS score and an 86-gene nuclear structural-OXPHOS score.
The production bundle contains:

```text
21 general endpoint tests
+ 147 sex/APOE-modifier endpoint tests
= 168 formal endpoint tests
```

The observed outcome is:

- 158 endpoint rows are `inconclusive` and 10 are `not_testable`;
- no endpoint is `supported` and no endpoint has family-wide `q <= 0.05`;
- none of the 168 confidence intervals lies wholly inside the prespecified
  `[-0.25, +0.25]` small-effect region, so the result is not a precise null;
- all seven general C3 gates are `inconclusive`;
- 46 modifier C3 gates are `inconclusive` and three are `not_testable`;
- the primary overall C3 decision is `inconclusive`; and
- the residual bridge is not authorized.

The endpoint-level breakdown is:

| Result family | Rows | Inconclusive | Not testable | Nominal P < 0.05 | Minimum q |
|---|---:|---:|---:|---:|---:|
| Primary general | 9 | 9 | 0 | 0 | 0.665 |
| Secondary general | 12 | 11 | 1 | 0 | 0.828 |
| Primary modifier | 63 | 63 | 0 | 1 | 0.983 |
| Secondary modifier | 84 | 75 | 9 | 1 | 0.982 |

The only two nominal endpoint results are both coupling-slope modifiers:

| Context and contrast | Estimate (95% CI) | P | q | Eligibility | Stability | Final endpoint status |
|---|---:|---:|---:|---|---|---|
| Excitatory neurons, male e2 minus male e33 | 1.268 (0.031, 2.506) | 0.0446 | 0.983 | Provisional low power | Passed | Inconclusive |
| OPCs, female minus male within e33 | 0.701 (0.023, 1.378) | 0.0427 | 0.982 | Confirmatory donor count | Failed | Inconclusive |

These rows may be visible in a complete plot, but they should receive no star,
special color, enlarged label, or dedicated donor panel. The first is based on
four required group counts of `7|6|28|53`; the second fails the frozen stability
rules. Neither row supports a modifier-specific C3 claim.

The ten not-testable endpoint rows all involve vasculature:

- the general coupling-slope endpoint has zero predictor-range overlap; and
- all three endpoints are not testable for each of three modifier contrasts:
  female-minus-male e2, female e2-minus-e33, and male e2-minus-e33.

The three affected modifier questions contain required cells with only three
or four donors. Missing or structurally untestable estimates must be shown as
such, never as zero.

## Core Figure 1: complete C3 evidence landscape

### Purpose

Show the full prespecified analysis and its terminal decisions in one figure.
This should be the lead Phase 15 figure because it prevents visual selection of
attractive rows and makes the negative/inconclusive conclusion immediately
auditable.

### Proposed panels

**A. Analysis schematic.** Show the donor-level mtDNA score `M`, nuclear score
`N`, and the three complementary endpoints:

1. standardized compartment difference, `D = M - N`;
2. cross-fitted NCI-reference residual, observed `M` minus predicted `M`; and
3. AD-minus-NCI coupling-slope change.

Continue the schematic through the general or sex/APOE contrast, endpoint
status, three-endpoint C3 gate, and primary overall decision. Use association
lines rather than causal arrows.

**B. General-effect forest.** Display all 21 general results as seven context
groups with three endpoint rows per context. Each row should show:

- the adjusted estimate and 95% confidence interval;
- a zero line and a shaded `[-0.25, +0.25]` SESOI band;
- family-wide q value;
- total NCI and AD donor-context counts;
- context role (primary confirmatory or secondary extension);
- stability status; and
- exact endpoint status.

Use separate aligned x-axes for the three endpoint units. Do not imply that a
0.25-unit difference, residual, and slope are the same physical quantity.

**C. Complete modifier atlas.** Use three aligned `7 contexts x 7 modifiers`
heatmaps, one per endpoint. Color represents the signed estimate. Add redundant
symbols or borders for interval exclusion, low-power eligibility, stability,
and final status. Gray crossed cells denote the nine not-testable vasculature
endpoint rows. Preserve the frozen context and contrast ordering.

Use endpoint-specific zero-centered limits, fixed across all panels and
supplementary plots for that endpoint. If clipping is necessary, mark clipped
tiles with directional triangles and state each numerical limit.

**D. Decision summary.** Report:

```text
Endpoint tests: 0 supported, 158 inconclusive, 10 not testable
General gates: 0 supported, 7 inconclusive
Modifier gates: 0 supported, 46 inconclusive, 3 not testable
Primary overall C3: inconclusive
Residual bridge: not authorized
```

Also report the four minimum family q values. This panel should distinguish
“inconclusive” from both “supported absence” and “not testable.”

## Core Figure 2: primary-context mitonuclear geometry

### Purpose

Show what the mitonuclear relationship looks like at donor level in the three
primary contexts without substituting descriptive geometry for the formal
adjusted tests.

### Proposed panels

**A-C. Donor score-pair scatters.** Show one panel each for astrocytes,
excitatory neurons, and inhibitory neurons:

- x-axis: nuclear structural-OXPHOS NCI-standardized score `N`;
- y-axis: mtDNA OXPHOS NCI-standardized score `M`;
- one point per donor-context profile;
- diagnosis encoded with Okabe-Ito blue/orange and a redundant point shape;
- sex/APOE stratum indicated by small facet strips or an adjacent rug, not six
  additional colors; and
- each held-out NCI donor's saved predicted `M` shown as a smaller open marker
  at the same `N`, with a thin vertical segment to observed `M`; these segments
  make the cross-fitted NCI residuals visible without refitting a line; and
- saved group slopes and their 95% confidence intervals summarized in a small
  aligned inset rather than drawing 12 visually competing fitted lines.

The three primary contexts must all be shown. Do not select only the context
with the smallest P value.

**D-F. Adjusted departure curves.** For the same three contexts, plot the saved
general AD-minus-NCI prediction departure against the nuclear score over the
validated common range. Show zero, common-range limits, and any saved
checkpoint substitution. Label the frozen descriptive
`slope_rewiring_observed` flag, while stating that this flag is outside Gate 2
and does not establish C3 support.

**G. Formal primary triplets.** Place the nine primary general endpoint
estimates and their confidence intervals beside the geometry panels. This
panel connects the visual relationships to the actual inferential result:
every primary general endpoint and all three primary general gates are
inconclusive.

### Interpretation constraint

Raw score-pair scatters are descriptive. They do not replace covariate-adjusted
HC3 estimates, equal-stratum general contrasts, cross-fitted residuals, or the
family-wide correction. Any line derived from raw points must be labeled
descriptive. The cross-fitted predictions, departure curves, and formal
estimates should be read from the saved result tables; the figure renderer
should not invent a reference-line confidence band that is absent from the
validated bundle.

## Core Figure 3: testability, precision, and stability

### Purpose

Explain why Phase 15 remains inconclusive despite a complete and technically
valid production run.

### Proposed panels

**A. Donor-support heatmap.** Display the 84 context-by-group cells:

```text
7 contexts x 12 diagnosis/sex/APOE groups
```

Fill represents the number of donors passing the 20-nucleus profile rule.
Use outlines or hatching for:

- fewer than five donors: modifier contrast not estimable;
- five to nine donors: estimable but provisional low power; and
- at least ten donors: confirmatory modifier-count threshold met.

Add a small secondary mark for the number remaining under the 50-nucleus
sensitivity threshold. Visually separate primary and secondary contexts.

**B. Precision versus support.** Plot minimum required-group donor count on the
x-axis and confidence-interval width on the y-axis for all 168 endpoint tests.
Facet by endpoint, encode general versus modifier by shape, and mark primary
versus secondary by outline. Use a vertical threshold at 10 donors for
modifier rows and label the general thresholds separately. Crossed gray marks
represent not-testable rows.

**C. Stability-component summary.** For general and modifier results
separately, report pass counts for:

- whole-donor bootstrap direction;
- balanced resampling direction;
- leave-one-donor-out sign stability;
- 20- versus 50-nucleus agreement;
- mean-z versus PC1 agreement;
- nuclear-only normalization;
- severe-QC exclusion;
- robust-QC covariate adjustment;
- repeated NCI-reference assignment;
- gene/complex influence;
- slope-range/nonlinearity sensitivity; and
- the complete mandatory-sensitivity decision.

These are correlated, non-independent diagnostic counts. Present them as a
component matrix or dot plot, not as a sequential attrition funnel.

**D. Status pathway.** Use a compact decision rail rather than a Sankey or
funnel:

```text
validated complete production
-> 168 terminal endpoint rows
-> no family-wide endpoint support
-> no compatible two-endpoint C3 gate
-> primary overall inconclusive
-> bridge not authorized
```

Include the 10 not-testable endpoint rows as a separate branch, not as failed
effects.

## Supplementary Figure 1: complete endpoint forest

Provide a paginated or tall forest plot containing every one of the 168 formal
endpoint tests in frozen order. Show estimates, 95% confidence intervals,
SESOI bands, P and q values, donor counts, eligibility, stability, context role,
and endpoint status. This is the numerical companion to Core Figure 1 and the
best location for exact row-level lookup.

Do not sort by P value. If separate pages are needed, split by endpoint and
scope while preserving the frozen context and contrast order.

## Supplementary Figure 2: adjusted stratum-effect atlas

Display all 126 adjusted AD-minus-NCI stratum effects:

```text
7 contexts x 6 sex/APOE strata x 3 endpoints
```

Use three endpoint-specific heatmaps or forests. These rows explain how the
general averages and difference-of-differences modifiers were formed; they are
not 126 additional primary hypotheses. Use the same signed scales and endpoint
labels as Core Figure 1.

## Supplementary Figure 3: complete slope-departure atlas

Show the saved prediction-departure curves for all 56 context-level C3
questions:

```text
7 general questions + 49 modifier questions
```

Use one page per context with general first and modifiers in frozen order.
Mark the common nuclear-score range and distinguish range mismatch from an
estimated curve. The 2 general and 17 modifier
`slope_rewiring_observed = TRUE` flags may be labeled descriptively, but must
not be drawn as passing gates: all corresponding compatibility classifications
are `none`, and no C3 gate is supported.

## Supplementary Figure 4: row-level stability atlas

Preserve all 168 endpoint rows and display each mandatory stability component
as pass, fail, or not applicable. Recommended columns are bootstrap, balance,
leave-one-donor-out, 50-nucleus threshold, PC1, normalization, QC, repeated
reference assignments, omission influence, slope sensitivity, and final
stability status.

Use distinct symbols for “not applicable” and “failed.” Place general and
modifier results in separate blocks so the much larger modifier family does
not obscure the general results.

## Supplementary Figure 5: score and reference-model reliability

### Proposed content

1. **Score reliability:** for all 14 context-by-module pairs, show NCI mean-z
   versus PC1 correlation and PC1 variance explained. All pairs passed the
   frozen reliability rule; observed correlations range from 0.945 to 0.999.
2. **Omission influence:** summarize direction retention and relative magnitude
   after omitting each mtDNA gene or nuclear respiratory complex. Do not plot
   thousands of overlapping curves; use worst-case deviation and sign-reversal
   counts per context/endpoint/scope.
3. **Cross-fit diagnostics:** show held-out NCI observed-versus-predicted values,
   residual distributions, fold sample sizes, and zero held-out/training
   overlap.
4. **Normalization/QC sensitivity:** summarize the saved nuclear-only
   normalization and QC-adjustment estimates relative to each primary estimate.

This figure establishes measurement reliability and leakage control. It does
not convert an inconclusive biological result into support.

## Visual and statistical standards

- Use a full-width layout of approximately 178-183 mm for dense core figures.
- Use at least 7-point text at final print size and bold, consistent panel
  labels.
- Export SVG and PDF vector files plus a 300-450-dpi PNG preview. Do not use
  JPEG for plots.
- Use `PuOr` or another colorblind-safe diverging map centered at zero for
  signed estimates. Use perceptually uniform sequential maps for counts and
  uncertainty.
- Use Okabe-Ito colors plus redundant shapes for categorical encodings.
- Verify color-vision accessibility and grayscale readability.
- Keep endpoint units explicit; do not place unlike endpoint units on one
  unlabeled numerical axis.
- Show individual donor-context points when feasible and define all intervals
  as 95% confidence intervals.
- Display exact or suitably rounded q values. Do not use significance stars.
- Preserve frozen context, endpoint, stratum, and contrast order.
- Separate primary-confirmatory and secondary-extension results visually.
- Render `not_testable` as gray hatching/crosses or gaps, never as zero.
- Encode status using both color and shape or border style.
- If heatmap values are clipped, show directional clipping marks and report the
  locked limits in the caption.
- State that the statistical unit is one donor within one broad cell context;
  the 1,825 score pairs are donor-context profiles, not 1,825 independent
  people.
- Do not draw causal arrows or claim altered respiration, ATP production,
  mitochondrial mass, organelle dysfunction, or candidate-gene causation.

## Figures that should not be used as primary evidence

- A volcano plot of 168 tests would overemphasize P values and hide the
  three-endpoint gate structure.
- A figure containing only the two nominal slope rows would be post-result
  selection.
- A bar chart of means without donor points or confidence intervals would hide
  the uncertainty driving the conclusion.
- A correlation-significance comparison between AD and NCI is not the formal
  slope-contrast test.
- A network or pathway diagram is not evidence for the Phase 15 C3 gate.
- A red-green status palette or “traffic light” figure is not accessible and
  cannot distinguish inconclusive from not testable without color.

## Recommended implementation order

1. Core Figure 1: complete C3 evidence landscape.
2. Core Figure 3: donor support, precision, and stability.
3. Core Figure 2: primary-context geometry using only saved donor and model
   prediction data.
4. Supplementary Figure 1: complete endpoint forest.
5. Supplementary Figures 2-5.

This order first locks the complete inferential story and status encodings,
then adds explanatory geometry and detailed diagnostics.

## Recommended directory organization

```text
results/figures/analysis/phase15_mitonuclear_coupling/
├── complete_evidence_landscape/
├── primary_coupling_geometry/
├── testability_precision_stability/
├── complete_endpoint_forest/
├── stratum_effects/
├── slope_departure_atlas/
├── stability_atlas/
└── score_reference_reliability/
```

Each figure family should contain:

- SVG and PDF vector outputs;
- a high-resolution PNG preview;
- the exact plotted-data TSV or TSV.GZ;
- a caption and short methods note;
- source-result paths and SHA-256 hashes;
- validation checks and a terminal figure status; and
- a recorded colorblind and grayscale review.

## Authoritative Phase 15 source tables

### Decisions and formal effects

- [Production status](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_status.tsv)
- [Claim summary](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_claim_summary.tsv)
- [General endpoint results](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_general_results.tsv)
- [Modifier endpoint results](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_modifier_results.tsv)
- [General C3 gates](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_general_gate_decisions.tsv)
- [Modifier C3 gates](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_modifier_gate_decisions.tsv)
- [Adjusted stratum effects](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_stratum_effects.tsv)

### Donor geometry, prediction, and eligibility

- [Figure-ready donor points and predictions](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_figure_data.tsv.gz)
- [Donor endpoint values](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_donor_endpoints.tsv.gz)
- [Donor score pairs](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_score_pairs.tsv.gz)
- [Prediction departure grid](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_prediction_grid.tsv.gz)
- [Group slopes and correlations](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_group_slopes.tsv)
- [Donor eligibility](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_donor_eligibility.tsv)

### Reliability, sensitivity, and provenance

- [General stability summary](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_general_stability_summary.tsv)
- [Modifier stability summary](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_modifier_stability_summary.tsv)
- [Score reliability](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_score_reliability.tsv)
- [Gene and complex influence](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_gene_complex_influence.tsv)
- [QC and normalization sensitivity](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_qc_normalization_sensitivity.tsv)
- [NCI reference models](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_nci_reference_models.tsv)
- [Cross-fit folds](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_crossfit_folds.tsv)
- [Model diagnostics](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_model_diagnostics.tsv)
- [Production checks](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_checks.tsv)
- [Artifact manifest](../../../../results/minerva_production/15_mitonuclear_coupling/mitonuclear_artifacts.tsv)

All inferential values, statuses, and predictions should be read from these
validated tables. A figure renderer may reshape or join them, but it should not
refit models, recalculate P or q values, redefine thresholds, or reclassify any
endpoint or gate.
