# Proposed figures for Phase 13 respiratory-modifier analysis

## Implementation status

Implemented and validated on 2026-08-09. The reproducible renderer is
[plot_phase13_respiratory_modifier_figures.R](../../../../scripts/figures/analysis/phase13_respiratory_modifier/plot_phase13_respiratory_modifier_figures.R),
and the package-level validation summary is
[phase13_figure_package_status.tsv](../../../../results/figures/analysis/phase13_respiratory_modifier/phase13_figure_package_status.tsv).

The generated figure families are:

- [Complete modifier landscape](../../../../results/figures/analysis/phase13_respiratory_modifier/modifier_landscape/phase13_modifier_landscape.png)
- [Direct-respiratory forest](../../../../results/figures/analysis/phase13_respiratory_modifier/direct_respiratory_forest/phase13_direct_respiratory_forest.png)
- [Testability, donor support, and precision](../../../../results/figures/analysis/phase13_respiratory_modifier/testability_qc/phase13_testability_qc.png)
- [Adjusted stratum-effect atlas](../../../../results/figures/analysis/phase13_respiratory_modifier/stratum_effects/phase13_stratum_effects.png)
- [Stability atlas](../../../../results/figures/analysis/phase13_respiratory_modifier/stability_atlas/phase13_stability_atlas.png)
- [Module-member gene-support atlases](../../../../results/figures/analysis/phase13_respiratory_modifier/gene_support_atlas/)

All six families passed their recorded checks with zero failures. Each family
contains reproducible plotted data, a caption, a methods note, source/output
hashes, validation checks, and status metadata in addition to the requested
vector and high-resolution raster outputs. The rendered files were manually
reviewed for label clipping, panel-boundary artifacts, color accessibility,
and redundant non-color status encodings.

## Production result that the figures must communicate

Phase 13 should have three core figures and three supplementary figure
families. The design must emphasize that the production run was technically
complete but scientifically inconclusive:

- 196 tests were planned; 180 were estimable and 16 were not testable.
- The final statuses were 180 `inconclusive`, 16 `not_testable`, and zero
  `supported`.
- Seven module-score tests had nominal \(P < 0.05\), but none passed the
  complete-family false-discovery-rate correction; the minimum score
  \(q\) value was 0.876.
- Only one of the 98 direct-respiratory tests had nominal \(P < 0.05\).
- No CAMERA test passed false-discovery-rate correction; the minimum CAMERA
  \(q\) value was 0.346.
- All 16 not-testable results occurred in the vasculature context.

The figures should therefore explain the complete effect landscape,
uncertainty, donor support, and robustness. They should not visually promote
nominal findings as confirmed results.

## Core Figure 1: complete modifier landscape

### Purpose

Present all 196 planned modifier tests without selecting attractive rows.

### Proposed panels

1. **Analysis schematic:** show the six sex/APOE-specific adjusted AD-minus-NCI
   effects and how one formal difference-of-differences modifier is calculated.
2. **Signed estimate atlas:** four \(7 \times 7\) heatmaps, with:
   - rows representing the seven broad cell contexts;
   - columns representing the seven prespecified sex/APOE contrasts;
   - one panel for each mitochondrial module;
   - color representing the signed standardized modifier estimate;
   - gray crossed cells representing not-testable combinations; and
   - cell outlines representing the final gate status.
3. **Outcome summary:** report zero supported, 180 inconclusive, and 16
   not-testable rows, together with the minimum module-score and CAMERA
   \(q\) values.

The two direct-respiratory modules should be visually separated from the two
respiration-supporting modules:

- direct respiratory: mtDNA OXPHOS and nuclear structural OXPHOS;
- supporting programs: mitochondrial translation and MIB/MICOS inner-membrane
  organization.

## Core Figure 2: direct-respiratory forest

### Purpose

Make effect sizes and uncertainty, rather than nominal P values, the central
evidence for the primary respiratory question.

### Proposed content

Display all 98 tests from the two direct-respiratory modules:

```text
7 contexts × 7 modifiers × 2 direct-respiratory modules = 98 tests
```

For every row, show:

- the signed estimate;
- its 95% confidence interval;
- a vertical zero line;
- a shaded \([-0.25,+0.25]\) project-defined meaningful-effect band;
- the minimum donor count among the four required diagnosis-by-group cells;
- the family-wide \(q\) value; and
- the final testability and scientific status.

The figure should be split into two module panels or pages so that all labels
remain readable. Results should remain in their frozen context and contrast
order.

The nominal OPC nuclear-OXPHOS sex difference within APOE ε3/ε3 should remain
visible with every other row, but it should not receive a significance star:

```text
estimate = 0.815
95% CI = [0.130, 1.501]
P = 0.0199
q = 0.876
```

This row is nominally detectable but does not pass the complete-family
correction or the frozen Phase 13 scientific gate.

## Core Figure 3: testability, donor support, and precision

### Purpose

Explain why the complete result is inconclusive and why vasculature contains
the not-testable rows.

### Proposed panels

1. **Donor-count heatmap:** seven contexts by twelve
   diagnosis/sex/APOE groups. Color represents the number of donors passing
   the 20-nucleus threshold. Use outlines for:
   - fewer than five donors: not estimable;
   - five to nine donors: estimable but below the confirmatory threshold;
   - at least ten donors: confirmatory donor-count threshold met.
2. **Precision plot:** minimum required-group donor count on the x-axis and
   confidence-interval width on the y-axis for all 196 tests. Add a vertical
   reference at ten donors and encode module and final status without hiding
   overlapping points.
3. **Module-coverage matrix:** seven contexts by four modules, labeled with
   genes used/reference genes and the frozen coverage decision.
4. **Gate-component summary:** report how many rows passed each prespecified
   component, including donor count, module coverage, interval, score FDR,
   CAMERA FDR, bootstrap direction, leave-one-donor-out, alternative scoring,
   and omission checks.

The gate-component panel must be labeled as a set of non-independent pass
counts, not as a sequential attrition funnel.

## Supplementary Figure 1: adjusted stratum-effect atlas

Display all 168 adjusted AD-minus-NCI component effects:

```text
7 contexts × 4 modules × 6 sex/APOE strata = 168 effects
```

Use heatmaps with the same signed scale as the modifier landscape. These
effects explain whether a modifier estimate arose because one group's AD
effect became more positive, more negative, or reversed direction. They are
descriptive components of the direct test and must not be presented as 168
additional primary hypotheses.

## Supplementary Figure 2: stability atlas

Preserve the frozen 196-test order and display the following row-specific
checks as pass, fail, or not testable:

- bootstrap same-direction fraction;
- balanced-resampling same-direction fraction;
- leave-one-donor-out sign reversals;
- 20- versus 50-nucleus agreement;
- mean-z versus PC1 agreement;
- QC-adjusted estimate agreement;
- severe-QC-exclusion agreement; and
- gene or respiratory-complex omission sensitivity.

A compact matrix is preferable to hundreds of separate distributions. A
small accompanying reliability panel can show, for each context-module pair,
the mean-z/PC1 correlation and PC1 variance explained.

## Supplementary Figure 3: module-member gene-support atlas

For each frozen module, show every admitted member gene rather than only genes
passing a differential-expression threshold. Order genes by frozen respiratory
complex or functional category and show:

- the signed gene-level modifier estimate;
- the 95% confidence interval;
- module membership and admitted-score status; and
- context and contrast identifiers.

This atlas is an exploratory decomposition of the module result. A genome-wide
single-gene volcano plot should not be used as evidence that the Phase 13
module-level claim passed.

Because no Phase 13 row was classified as supported, provisional, or
statistically detectable-but-small, detailed donor pages should not be selected
automatically. Selecting the smallest P value after seeing the results would
visually privilege a row that failed the frozen gate. If a donor-level panel is
needed for teaching, its example row and selection rationale should be fixed
and labeled as illustrative rather than inferential.

## Visual and statistical standards

- Use a shared zero-centered `PuOr` scale for signed estimates.
- Use the same numerical color limits across comparable module panels.
- If values are clipped for readability, mark the clipped cells and state the
  limits explicitly.
- Display not-testable values as gray or blank, never as zero.
- Preserve the frozen context, contrast, and module ordering.
- Use the established cell-context colors only as categorical side strips;
  do not mix them with the continuous effect scale.
- Do not use significance stars. Display exact or suitably rounded \(q\)
  values and final gate statuses.
- Include 95% confidence intervals and donor counts wherever an estimate is
  highlighted.
- Use vector SVG/PDF outputs plus a 300–450-dpi PNG preview.
- Use at least 7-point text at final print size and check both color-vision
  accessibility and grayscale readability.

## Recommended directory organization

No proposed file or directory name uses the abbreviation `c1`. The result
tree should mirror the documentation grouping used for other analysis phases:

```text
results/figures/analysis/phase13_respiratory_modifier/
├── modifier_landscape/
├── direct_respiratory_forest/
├── testability_qc/
├── stratum_effects/
├── stability_atlas/
└── gene_support_atlas/
```

The matching documentation root should be:

```text
docs/figures/analysis/phase_13_respiratory_modifier/
```

Each figure family should include:

- SVG and PDF vector outputs;
- a high-resolution PNG preview;
- a plotted-data TSV or TSV.GZ;
- a caption and short methods note;
- source-result identifiers and hashes;
- figure validation checks and status; and
- an explicit record of the colorblind and grayscale review.

## Authoritative Phase 13 source tables

- [Production status](../../../../results/minerva_production/13_respiratory_modifier/respiratory_status.tsv)
- [Module-level results](../../../../results/minerva_production/13_respiratory_modifier/respiratory_module_results.tsv)
- [Adjusted stratum effects](../../../../results/minerva_production/13_respiratory_modifier/respiratory_module_stratum_effects.tsv)
- [Final gate decisions](../../../../results/minerva_production/13_respiratory_modifier/respiratory_gate_decisions.tsv)
- [Donor module scores](../../../../results/minerva_production/13_respiratory_modifier/respiratory_donor_module_scores.tsv.gz)
- [Donor sample metadata](../../../../results/minerva_production/13_respiratory_modifier/respiratory_donor_samples.tsv.gz)
- [Module coverage](../../../../results/minerva_production/13_respiratory_modifier/respiratory_module_coverage.tsv)
- [Module reliability](../../../../results/minerva_production/13_respiratory_modifier/respiratory_module_reliability.tsv)
- [CAMERA results](../../../../results/minerva_production/13_respiratory_modifier/respiratory_camera_results.tsv)
- [Stability summary](../../../../results/minerva_production/13_respiratory_modifier/respiratory_stability_summary.tsv)
- [Gene-level modifier results](../../../../results/minerva_production/13_respiratory_modifier/respiratory_gene_interaction_results.tsv.gz)
