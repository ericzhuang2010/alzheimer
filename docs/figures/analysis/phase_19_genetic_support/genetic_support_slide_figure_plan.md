# Human genetic support slide figure plan

## Status

**Implemented and validated:** 2026-08-16.

The reproducible renderer is
[`plot_genetic_support_slide_summary.py`](../../../../scripts/figures/analysis/phase_19_genetic_support/plot_genetic_support_slide_summary.py),
with automated validation in
[`test_phase19_genetic_support_slide_summary.py`](../../../../tests/test_phase19_genetic_support_slide_summary.py).
The nine-file validated package is under
[`results/figures/analysis/phase_19_genetic_support`](../../../../results/figures/analysis/phase_19_genetic_support/),
including the [PNG slide asset](../../../../results/figures/analysis/phase_19_genetic_support/genetic_support_slide_summary.png),
[vector PDF](../../../../results/figures/analysis/phase_19_genetic_support/genetic_support_slide_summary.pdf),
and [editable SVG](../../../../results/figures/analysis/phase_19_genetic_support/genetic_support_slide_summary.svg).

All automated tests and independent artifact checks passed. The final graphic
was reviewed in color and grayscale at the intended slide size. The
presentation itself was not modified.

The visible figure must not contain the internal phase number or the phrase
“Phase 19.” Internal paths, scripts, schemas, and provenance records may retain
the existing phase-based repository organization.

## End state

Create one reproducible, slide-native landscape figure that answers:

1. How were the 47 candidate-context results distributed across evidence
   grades?
2. Which candidates received direct positive or limited human-genetic support?
3. Which candidates had no direct mapping in the registered filtered source?
4. Which candidates could not be assessed with the available nuclear
   GWAS/xQTL resource?

The final figure will show all 25 genes without forcing the audience to read a
47-row portrait matrix. It will preserve the difference between:

- **strong evidence**;
- **weak/limited evidence**;
- **no direct mapping in the registered filtered source**; and
- **not assessable with the available source**.

The main conclusion visible in the figure will be:

> Direct human-genetic support is concentrated in APOE. COX7C and SELENOW have
> limited evidence; most other nuclear candidates remain unresolved, and the
> mtDNA candidates require a different genetic resource.

This is an evidence-summary figure, not a statistical-effect plot. It will not
display P-value significance stars, confidence intervals, causal arrows, or
area-scaled symbols that could imply quantitative certainty beyond the source.

## Intended presentation use

The figure is intended for the third proposed inserted slide, immediately
before the current first-batch validation-panel slide.

Recommended slide title:

```text
HUMAN GENETIC SUPPORT • RESULTS
```

Recommended slide headline:

```text
APOE stands out; COX7C and SELENOW remain limited; most candidates are unresolved
```

The slide title and headline should remain PowerPoint text rather than being
baked into the graphic. This keeps the figure reusable and makes slide text
editable.

The proposed data and method slides do not need separate external figures.
Their small data-source blocks and evidence-screening workflow can be drawn
with native PowerPoint shapes. This plan therefore covers only the conclusion
figure.

## Proposed figure layout

Use a wide three-part composition designed for the deck's 16:9 format:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ A. Candidate-context outcomes (n = 47)                                      │
│ [Strong 1] [Weak 3] [No direct map 23] [Not assessable 20]  Moderate = 0   │
├──────────────────────────────────────┬───────────────────────────────────────┤
│ B. Direct candidate-level findings   │ C. Unresolved candidates              │
│                                      │                                       │
│ APOE      Astrocytes       STRONG    │ No direct map                         │
│ direct AD fine-map; fallback context │ 16 nuclear genes • 23 contexts       │
│                                      │ gene chips listed explicitly          │
│ COX7C     Astro + inhibitory WEAK    │                                       │
│ one bulk sQTL result                 │ Not assessable                        │
│                                      │ 6 mtDNA genes • 20 contexts          │
│ SELENOW   Excitatory       WEAK      │ gene chips listed explicitly          │
│ TWAS-list flag; details unavailable  │                                       │
├──────────────────────────────────────┴───────────────────────────────────────┤
│ No direct map ≠ no genetic role • Not assessable ≠ negative                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Panel A: candidate-context outcome distribution

Show one horizontal stacked bar containing all 47 mutually exclusive
candidate-context results:

| Category | Candidate-context units | Share |
|---|---:|---:|
| Strong | 1 | 2.1% |
| Moderate | 0 | 0.0% |
| Weak | 3 | 6.4% |
| No direct mapping | 23 | 48.9% |
| Not assessable | 20 | 42.6% |
| **Total** | **47** | **100.0%** |

The bar will contain segments only for nonzero categories. `Moderate = 0` will
be stated beside the bar so the absence of a moderate result is not hidden.

Each nonzero segment will contain its count when space permits. The one-unit
strong segment is too narrow for internal text and should use an external
leader label. Counts, category names, and distinct patterns must accompany
color so the bar remains understandable in grayscale.

The bar is a count composition, not a probability distribution. The caption
must say that a gene appearing in multiple broad-network contexts contributes
one unit per displayed context.

### Panel B: direct candidate-level findings

Use three horizontal evidence cards in descending grade order.

#### APOE card

Visible fields:

```text
APOE • Astrocytes
STRONG GENE-LEVEL SUPPORT
rs429358 • AD fine-map inclusion 1.0 • P ≈ 1.88 × 10⁻¹⁵⁵
Context: fallback brain evidence; not an exact astrocyte colocalization
```

The card must distinguish strong AD gene evidence from exact astrocyte
mechanistic validation.

#### COX7C card

Visible fields:

```text
COX7C • Astrocytes + inhibitory neurons
WEAK / LIMITED
rs2010322 • bulk sQTL CL5 • AD P ≈ 2.64 × 10⁻⁶
One source result shown in two network contexts; not two replications
```

Do not show the two COX7C contexts as independent evidence events.

#### SELENOW card

Visible fields:

```text
SELENOW • Excitatory neurons
WEAK / LIMITED
Reported in the source TWAS gene list
Model statistic and exact excitatory context unavailable in the public table
```

Do not invent a TWAS Z score, P value, direction, or tissue label.

### Panel C: unresolved candidates

Split the panel into two visibly different blocks.

#### No direct mapping in the registered filtered source

Show the 16 nuclear genes contributing 23 candidate-context units:

```text
ANKRD11  ATP6V1F  COX4I1  COX6B1  DYNLT1  FTL  LAMTOR5  LAPTM4A
NCOA1    RPL11    RPL15   RPL38   RPLP1   RPS13  RPS15  UQCR10
```

Use neutral filled gene chips. The block heading and footer must avoid the
shorter word `negative`. The exact label is:

```text
NO DIRECT MAPPING IN THE REGISTERED FILTERED SOURCE
```

#### Not assessable with the available source

Show the six mtDNA genes contributing 20 candidate-context units:

```text
MT-ATP6  MT-CO2  MT-CO3  MT-CYB  MT-ND4  MT-ND5
```

Use open, outlined chips with an `NA` marker or diagonal pattern. The block
should state:

```text
mtDNA-specific heteroplasmy, haplogroup, copy-number, and NUMT-aware data were absent
```

This encoding must not resemble a failed significance test.

### Interpretive boundary ribbon

Use a full-width ribbon along the bottom:

```text
No direct map ≠ no genetic role    •    Not assessable ≠ negative
```

Optional second line, if space remains at the intended slide size:

```text
Evidence categories summarize source coverage and direct mapping; they are not causal probabilities.
```

## Visual design specification

### Canvas and export size

- Target figure aspect ratio: approximately `2.65:1`.
- Matplotlib canvas: `12.4 × 4.7 inches`.
- Intended placement on a 13.333 × 7.5 inch slide: approximately
  `x = 0.45`, `y = 1.48`, `w = 12.43`, `h = 4.71` inches.
- Reserve slide space above the graphic for the editable header and below it
  for the presentation's source line.
- Export PNG at 450 DPI with a white or transparent background.
- Export vector PDF and SVG versions for review and reuse.

### Typography

- Use the deck's sans-serif visual language: Arial, Helvetica, or a compatible
  fallback.
- Final-size minimum text: 9 pt for gene chips and detail lines.
- Card gene names: 15–17 pt, bold.
- Category headings: 11–13 pt, bold.
- Panel labels `A`, `B`, and `C`: 12–14 pt, bold.
- Avoid rotated text and legends that require back-and-forth lookup.

### Color and redundant encoding

Use the colorblind-safe Okabe–Ito family already compatible with the deck:

| Category | Primary color | Redundant encoding |
|---|---|---|
| Strong | blue `#0072B2` | solid circle/card edge + direct `STRONG` label |
| Moderate | green `#009E73` | direct text only because count is zero |
| Weak/limited | orange `#E69F00` | solid diamond/card edge + `WEAK / LIMITED` label |
| No direct mapping | neutral gray `#BDBDBD` | filled gray chip + full category text |
| Not assessable | white with charcoal `#404040` outline | open chip + `NA` or diagonal hatch |

Do not use red versus green as the main contrast. Do not use opacity alone to
distinguish `none_found` from `not_assessable`.

### Grayscale behavior

The figure must remain interpretable after grayscale conversion:

- strong and weak cards retain different border weights or symbols;
- no-direct-map chips remain filled;
- not-assessable chips remain open or hatched;
- every category is directly labeled; and
- the stacked bar uses borders/patterns in addition to color.

### Elements deliberately excluded

- no statistical significance stars;
- no error bars, because the plotted values are deterministic classification
  counts rather than estimates;
- no gene-to-disease causal arrows;
- no proportional circles whose area could exaggerate evidence strength;
- no genome-wide Manhattan plot;
- no full 47-row portrait matrix;
- no source-specific acronyms without a short definition; and
- no internal phase identifier in visible artwork.

## Authoritative inputs

The renderer will read only the validated human-genetic-support bundle:

```text
results/minerva_production/19_genetic_support/
├── genetic_support_candidate_manifest.tsv
├── genetic_support_common_variant_evidence.tsv.gz
├── genetic_support_colocalization.tsv.gz
├── genetic_support_assessability.tsv
├── genetic_support_evidence_summary.tsv
├── genetic_support_checks.tsv
└── genetic_support_status.tsv
```

Primary input:

```text
genetic_support_evidence_summary.tsv
```

Supporting inputs will be used only to verify the card annotations and
interpretive boundaries:

- candidate manifest: exact gene/network/case keys;
- common-variant evidence: rsIDs, AD P values, and inclusion scores;
- colocalization summary: source context and confidence label;
- assessability table: route-specific reason text;
- checks and status: validated Tier 1 identity and completion state.

No count, gene list, P value, grade, or context label will be hand-entered into
the renderer. The expected anchors below are validation targets, not an
alternative data source.

## Frozen numerical and categorical anchors

The implementation must reproduce all of these values before drawing:

| Quantity | Expected value |
|---|---:|
| Candidate-context rows | 47 |
| Unique genes | 25 |
| Strong contexts | 1 |
| Moderate contexts | 0 |
| Weak contexts | 3 |
| No-direct-mapping contexts | 23 |
| Not-assessable contexts | 20 |
| Strong genes | APOE |
| Weak genes | COX7C, SELENOW |
| Nuclear genes with no direct mapping | 16 |
| mtDNA genes not assessable | 6 |

Candidate-card anchors:

| Gene | Context(s) | Source detail |
|---|---|---|
| APOE | Astrocytes | rs429358; AD inclusion score 1.0; minimum reported P approximately `1.879585 × 10^-155`; fallback brain context. |
| COX7C | Astrocytes; inhibitory neurons | rs2010322; minimum reported P approximately `2.642295 × 10^-6`; bulk `ROSMAP_AC_sQTL`; CL5. |
| SELENOW | Excitatory neurons | Source TWAS gene-list membership; detailed model statistic and context unavailable. |

The displayed counts must satisfy:

```text
1 + 0 + 3 + 23 + 20 = 47 candidate-context units
1 APOE context + 2 COX7C contexts + 1 SELENOW context = 4 supported/limited contexts
4 + 23 + 20 = 47
```

## Files to add when the figure is implemented

### Source and test files

```text
scripts/figures/analysis/phase_19_genetic_support/
    plot_genetic_support_slide_summary.py

tests/
    test_phase19_genetic_support_slide_summary.py
```

The plotting script will contain separate functions for:

1. input and schema validation;
2. derivation of context and gene summaries;
3. construction of candidate-card annotations;
4. construction of figure plot-data tables;
5. rendering; and
6. output-only validation.

### Generated figure package

```text
results/figures/analysis/phase_19_genetic_support/
    genetic_support_slide_summary.png
    genetic_support_slide_summary.pdf
    genetic_support_slide_summary.svg
    genetic_support_slide_summary_plot_data.tsv
    genetic_support_slide_summary_checks.tsv
    genetic_support_slide_summary_caption.md
    genetic_support_slide_summary_methods.md
    genetic_support_slide_summary_artifacts.tsv
    genetic_support_slide_summary_status.tsv
```

The plot-data table must contain every displayed number, gene, context label,
grade, annotation string, order, and style key. The artifact manifest will
record bytes and SHA-256 hashes for every declared output except itself and the
status file.

## Existing files to change when the figure is implemented

None for the standalone figure task.

The implementation must not modify:

- the validated genetic-support result bundle;
- the human-genetic-support analysis script or configuration;
- Phase 18 results or figures;
- the presentation; or
- the presentation-builder script.

Presentation insertion and slide renumbering will be a later, separately
reviewed task after the standalone figure has passed visual and numerical QC.

## Files to delete

None.

If an exploratory preview already exists when implementation begins, it should
be moved to an archive directory rather than silently overwritten unless it is
an explicitly declared staging file.

## Implementation sequence

### Task 1: validate the source bundle

1. Verify all required input files exist.
2. Verify the status row reports `validated_complete_tier1`.
3. Verify the summary schema is `human_genetic_support_tier1_v1`.
4. Verify 47 unique `candidate_id` values and 25 genes.
5. Verify every grade belongs to the frozen vocabulary.
6. Verify all blocking source checks passed.

Stop before drawing if any check fails.

### Task 2: derive the plotted data

1. Count candidate-context units by final grade.
2. Derive gene lists within each grade without manual ordering.
3. Preserve the presentation-friendly network labels from the candidate
   manifest.
4. Extract APOE and COX7C variant annotations from the detailed evidence table.
5. Extract SELENOW TWAS-list status without manufacturing missing statistics.
6. Verify that the two COX7C rows point to one shared source result.
7. Write the complete plot-data table before rendering.

### Task 3: render the landscape composition

1. Construct the stacked count bar in Panel A.
2. Draw the three direct-evidence cards in Panel B.
3. Draw the two unresolved-candidate blocks and all gene chips in Panel C.
4. Add the interpretive-boundary ribbon.
5. Export PNG, PDF, and SVG from the same Matplotlib figure object.
6. Ensure the visible artwork contains no internal phase label.

### Task 4: create documentation and manifests

1. Generate the plot-data table.
2. Generate blocking/nonblocking checks.
3. Write a standalone caption.
4. Write concise methods and source notes.
5. Hash declared artifacts.
6. Write the status file last.

### Task 5: automated validation

The test will build the complete figure package in a temporary directory and
verify:

- source schemas and hashes are not changed;
- all 25 genes are displayed exactly once at the gene-summary level;
- all 47 context units contribute exactly once to Panel A;
- grade counts are `1, 0, 3, 23, 20`;
- APOE is the only strong gene;
- COX7C and SELENOW are the only weak genes;
- all six mtDNA genes occur only in the not-assessable block;
- no-direct-map and not-assessable labels are never shortened to `negative`;
- missing H0-H4 and SELENOW model statistics are not converted to numeric
  values or displayed as zero;
- all declared outputs exist and are nonempty;
- artifact hashes reproduce; and
- PNG dimensions and DPI meet the export contract.

### Task 6: visual review

Review the PNG at the exact intended slide placement, not only at full-screen
zoom. Confirm:

- all gene chips are readable from a normal presentation view;
- APOE, COX7C, and SELENOW cards have a clear visual hierarchy;
- the one-unit strong bar segment remains visible without exaggeration;
- no text overlaps or clips;
- `none_found` and `not_assessable` remain visually distinct;
- the graphic remains interpretable in grayscale;
- the footer boundary is readable; and
- the composition fits between the deck header and source line.

If the 16 no-direct-map gene chips are too dense at the planned size, widen
Panel C or use two chip rows. Do not reduce final text below 9 pt.

## Validation checklist

- [x] The source bundle is validated before rendering.
- [x] The figure contains 25 unique gene names.
- [x] Panel A totals exactly 47 candidate-context units.
- [x] The grade counts are 1 strong, 0 moderate, 3 weak, 23 no direct mapping,
  and 20 not assessable.
- [x] APOE is not presented as exact astrocyte mechanistic validation.
- [x] COX7C's two contexts are not presented as independent replications.
- [x] SELENOW has no invented numeric TWAS result.
- [x] Nearby-only variants are not presented as direct gene evidence.
- [x] H0-H4 values are not shown because they were unavailable.
- [x] All mtDNA genes use the not-assessable encoding.
- [x] The word `negative` appears only in the boundary statement explaining
  that not assessable is not negative.
- [x] Colors are colorblind-safe and every category has redundant encoding.
- [x] The figure works in grayscale.
- [x] Text is at least 9 pt at intended slide size.
- [x] PNG, PDF, and SVG exports contain identical data and ordering.
- [x] Caption, methods, plot data, checks, artifacts, and status are present.
- [x] The visible figure contains no internal phase identifier.
- [x] The presentation and presentation-builder script remain unchanged during
  standalone figure implementation.

## Draft caption

**Human genetic support across key-driver candidates.** Panel A summarizes 47
gene × broad-network candidate contexts across prespecified evidence grades.
One APOE/astrocyte context has strong gene-level AD support, while two COX7C
contexts and one SELENOW context have weak or limited support. Panel B states
the direct evidence and context limitations for these three genes. Panel C
shows 16 nuclear genes (23 contexts) with no direct mapping in the registered
filtered summary and six mtDNA genes (20 contexts) that cannot be assessed with
the available nuclear GWAS/xQTL resource. “No direct mapping” is a source-search
outcome rather than evidence of no genetic role; “not assessable” is not a
negative result.

## Draft source line for the future slide

```text
Source: validated human-genetic-support summary; FunGen-xQTL public snapshot; GENCODE v44; HGNC 2026-06-05
```

The future slide source line should use these public resource names and should
not expose internal phase numbering.
