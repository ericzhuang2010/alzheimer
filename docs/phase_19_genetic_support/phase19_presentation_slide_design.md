# Phase 19 presentation slide design

**Default format:** 10–12 minute scientific update, 16:9 widescreen, 10 main
slides plus appendix<br>
**Source summary:** [Phase 19 human genetic support: consolidated results](phase19_genetic_support_results_summary.md)<br>
**Core narrative:** Phase 19 strongly supports APOE, finds limited suggestive
evidence for a few other genes, and shows why absence of current genetic support
must be separated from biological refutation.

## 1. Design principles

- Use a conclusion as every slide title; avoid generic titles such as “Results.”
- Keep one main message and one main visual per slide.
- Distinguish `none_found`, a failed prespecified signal gate, and
  `not_assessable`; they are not interchangeable.
- Describe regional GWAS signals as locus evidence, not causal-gene assignment.
- Describe unresolved H0-H4 analyses as `PP.H4 unavailable`, not `H4 = 0`.
- Put detailed accessions, thresholds, and provenance issues in the appendix
  unless the audience is primarily methods-focused.

### Visual system

Use a white background and a colorblind-safe palette consistently:

| Meaning | Color | Hex |
|---|---|---|
| Strong support | Blue | `#0072B2` |
| Weak/suggestive support | Amber | `#E69F00` |
| Unresolved/input-limited | Vermillion | `#D55E00` |
| No support found under the tested design | Light gray | `#BDBDBD` |
| Not assessable/outside scope | White with dark outline | `#4D4D4D` outline |

Use Aptos, Arial, or another presentation-safe sans serif. Recommended minimums
are 30–34 pt for titles, 20–24 pt for body text, 16–18 pt for figure labels, and
13–15 pt for source notes. Do not place the full portrait evidence matrices on a
main slide.

## 2. Main-deck storyboard

### Slide 1 — Phase 19: human genetic support for Phase 18 key drivers

**Subtitle:** Public-data evaluation of 25 genes across 47 gene-by-network
contexts

**Layout:** Clean title slide with three small result chips at the bottom:

- `APOE — strong`
- `COX7C / SELENOW — weak`
- `RPS15 — promising, unresolved`

**Speaker message:** This phase tested whether network-derived key drivers also
have inherited human-genetic support; it did not retest or rerank Phase 18.

---

### Slide 2 — Phase 19 asks a narrower question than Phase 18

**Visual:** A two-stage diagram:

```text
Phase 18: network-associated key drivers
47 gene × network contexts / 25 unique genes
                         |
                         v
Phase 19: inherited human-genetic support
19 nuclear genes tested in nuclear GWAS/QTL routes
6 mtDNA genes require a separate design
```

**Content:**

- Phase 18 identifies genes central to disease-associated network modules.
- Phase 19 asks whether AD or AD-endophenotype associations map directly to a
  candidate and, where inputs permit, share an association signal with its QTL.
- A network driver can be biologically important without being a germline
  susceptibility gene.

**Speaker message:** The two phases provide complementary evidence and should
not be expected to return identical rankings.

---

### Slide 3 — A frozen, gated design prevents overinterpretation

**Visual needed:** New horizontal workflow schematic with dataset labels below
each gate:

```text
Frozen Phase 18 candidates
        -> regional AD / CSF GWAS signal
        -> candidate molecular-QTL signal
        -> allele, model, and source-LD compatibility
        -> primary multi-signal H0-H4 analysis
```

Place the main data resources underneath:

- FunGen-xQTL public summary for direct fine-mapping/xQTL/TWAS screening;
- Bellenguez clinical-AD GWAS for the 19 nuclear candidate regions;
- NG00184 and eQTL Catalogue brain eQTL/sQTL resources;
- three CSF GWAS: amyloid-beta 42, total tau, and p-tau181; and
- targeted APOE and RPS15 follow-up resources.

Add a small legend: “A route stops when an upstream requirement fails.” Keep
numeric thresholds in the appendix.

**Speaker message:** The design was intentionally conservative and distinguishes
a measured negative from missing or incompatible inputs.

---

### Slide 4 — Only APOE achieved strong formal support

**Visual needed:** New compact horizontal outcome scorecard for the 47 formal
candidate-context rows:

| Outcome | Context rows | Annotation |
|---|---:|---|
| Strong | 1 | APOE |
| Weak | 3 | COX7C in two contexts from one record; SELENOW in one context |
| Moderate | 0 | None |
| None found | 23 | No direct mapping in the registered Tier 1 screen |
| Not assessable | 20 | Six mtDNA genes across 20 contexts |

Use a 47-unit stacked bar or five large count tiles. Annotate that the two COX7C
rows are not independent replications. Add a separate outlined badge:
“Supplemental RPS15 audit: weak/suggestive, not integrated into the formal
47-row grade.”

**Existing figure use:** The full
[Tier 1 evidence matrix](../../results/minerva_production/19_genetic_support_tier1/genetic_support_evidence_matrix.pdf)
belongs in the appendix, not on this slide.

**Speaker message:** Formal support is concentrated in one gene; most other rows
are either unsupported by this screen or not testable with the chosen data.

---

### Slide 5 — APOE has convergent AD and CSF biomarker evidence

**Layout:** Two-thirds figure, one-third evidence summary.

**Reuse:** Page 1 of the
[Tier 1 locus plots](../../results/minerva_production/19_genetic_support_tier1/genetic_support_locus_plots.pdf),
showing direct APOE entries and `rs429358`.

**Right-side evidence chips:**

- Direct `rs429358` mapping; 95% credible-set member;
- AD inclusion score `1.0`, minimum reported `P ≈ 1.88e-155`;
- only candidate passing the regional and corrected MAGMA gates for all three
  CSF traits; and
- exact astrocyte expression/splicing mechanism remains unresolved.

At the bottom, show three small biomarker boxes—amyloid-beta 42, total tau, and
p-tau181—each labeled “regional + gene-based signal.” Do not display the
single-signal pQTL sensitivity result as confirmatory colocalization.

**Speaker message:** APOE is strongly supported as an AD gene, but Phase 19 does
not establish that the association acts through the exact Phase 18 astrocyte
mechanism.

---

### Slide 6 — Non-APOE signals remain suggestive, regional, or unresolved

**Visual needed:** Four equal evidence cards:

| Gene | Evidence | Why it is not validated |
|---|---|---|
| COX7C | Weak bulk-brain sQTL mapping; AD-significant candidate window | One source record projected to two contexts; exact cell support and valid H0-H4 result absent |
| SELENOW | Public TWAS-list membership | No model statistic, replication result, or exact excitatory-neuron context |
| RPS15 | AD region `P = 4.089e-30`; several bulk-brain QTL tracks | Primary model/LD inputs incomplete; exact OPC and inhibitory-neuron support not established |
| ANKRD11 | AD region `P = 1.283e-11` | Tested eQTL failed its gate; sQTL route unassessable; regional proximity is not gene assignment |

Emphasize RPS15 with an outlined banner: “Highest-priority unresolved non-APOE
candidate.”

**Optional inset:** Page 2 of the
[Tier 1 locus plots](../../results/minerva_production/19_genetic_support_tier1/genetic_support_locus_plots.pdf)
for COX7C. Put the four-panel
[recovery locus plot](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_locus_plots.pdf)
in the appendix unless it is redesigned with larger labels.

**Speaker message:** Significant regional association alone does not identify
which gene mediates the locus.

---

### Slide 7 — All 54 Tier 2 routes stopped before a valid shared-signal analysis

**Visual needed:** New route-attrition bar or funnel:

```text
54 nuclear eQTL/sQTL routes
  42  no regional AD GWAS signal
   4  no candidate QTL signal
   2  model or LD incompatible
   6  not assessable
   0  valid primary H0-H4 results
```

The clearest design is a horizontal stacked bar for the 54 terminal routes plus
a large `0` callout at the right for resolved H0-H4 analyses. Avoid implying
that these are sequential counts or that `PP.H4 = 0`; the posterior was not
available.

**Speaker message:** The main bottleneck was upstream evidence and input
completeness, not a series of completed colocalizations favoring distinct
signals.

---

### Slide 8 — “No support” has three non-equivalent meanings

**Visual:** Three columns with one example in each:

1. **Signal-negative under the tested design**
   - 15 of 19 nuclear genes lacked a clinical-AD regional signal at the frozen
     threshold.
   - All 18 non-APOE nuclear genes failed the CSF follow-up gates.
2. **Technically unresolved**
   - complete candidate QTL models, variant order, or source-matched LD missing;
   - exact cell-type QTL small, unavailable, or context-mismatched.
3. **Mechanism outside the current design**
   - mtDNA, rare or structural variation, trans regulation, interactions,
     disease stage, progression, resilience, or post-transcriptional effects.

Add a highlighted footer: “The six mtDNA genes were not tested negatively.”

**Speaker message:** Current negative evidence lowers confidence in a simple
common cis-germline mechanism; it does not refute a downstream or state-specific
functional role.

---

### Slide 9 — The next work should resolve key loci, then broaden mechanisms

**Visual:** Three-horizon roadmap:

| Horizon | Priority |
|---|---|
| Repair now | Regenerate malformed empty outputs, complete APOE pQTL provenance, correct the QTD000579 modality label, and reconcile GWAS sample metadata |
| Resolve next | Obtain complete source-QTL statistics/models and matched LD for APOE and RPS15; use larger exact-cell eQTL/sQTL; run candidate-frozen brain/CSF pQTL, PWAS, and multi-model TWAS |
| Broaden later | Replicated rare-variant tests, dedicated mtDNA analysis, formal sex/APOE interactions, multi-ancestry and progression/pathology phenotypes, independent network replication and perturbation |

If the audience is not methods-focused, move the “repair now” row to an appendix
and give more space to the two scientific horizons.

**Speaker message:** The immediate scientific opportunity is resolving APOE and
RPS15 with complete, signal-aware molecular-QTL packages.

---

### Slide 10 — Phase 19 narrows the candidate landscape without closing it

**Visual:** Four large take-home statements, using the evidence colors:

1. **APOE:** strong, convergent gene-level support.
2. **COX7C and SELENOW:** weak/suggestive summary evidence.
3. **RPS15:** most interesting unresolved non-APOE candidate; ANKRD11 is regional
   evidence only.
4. **No extension validated a new gene:** absence reflects a mixture of tested
   negatives, unavailable inputs, and mechanisms outside the current design.

Finish with: `full_phase19_complete = FALSE`.

**Speaker message:** Phase 19 is a disciplined genetic annotation of the Phase
18 list, not broad genetic validation or rejection of the network drivers.

## 3. Recommended appendix slides

1. Exact Phase 18 candidate lists by network and driver class.
2. Dataset inventory, versions, sample sizes, and purpose.
3. Frozen thresholds, evidence grades, and terminal-state definitions.
4. Full Tier 1 47-context evidence matrix.
5. Tier 2 route matrix and four regional AD locus plots.
6. CSF 19-gene-by-3-trait evidence matrix and MAGMA details.
7. RPS15 public-source audit: three positive fallback QTL tracks and exact-cell
   negatives.
8. Reproducibility and provenance caveats.

## 4. Figure plan

### New figures recommended for the main deck

| Figure | Slide | Data source | Priority |
|---|---:|---|---|
| Frozen gated workflow with dataset labels | 3 | Analysis contracts and execution reports | Essential |
| Compact 47-context formal outcome scorecard | 4 | [`genetic_support_status.tsv`](../../results/minerva_production/19_genetic_support_tier1/genetic_support_status.tsv) and [`genetic_support_evidence_summary.tsv`](../../results/minerva_production/19_genetic_support_tier1/genetic_support_evidence_summary.tsv) | Essential |
| Four-gene evidence cards | 6 | Tier 1, Tier 2 recovery, CSF, and RPS15 summaries | Essential |
| 54-route terminal-state/attrition graphic | 7 | [`recovery_route_decisions.tsv`](../../results/minerva_production/19_genetic_support_tier2_recovery/recovery_route_decisions.tsv) | Essential |
| Compact CSF outcome graphic: 3 APOE-positive decisions versus 54 without qualifying signal | 5 or appendix | [`endophenotype_gate_decisions.tsv`](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_gate_decisions.tsv) | Optional |

These figures can all be generated from existing result tables; no external or
stock imagery is needed.

### Existing figures to reuse

- **Main deck:** APOE Tier 1 locus plot; optionally the COX7C Tier 1 locus plot.
- **Appendix or after redesign:** four-panel recovery locus plot; total-tau and
  p-tau181 candidate-region plots.
- **Appendix only:** the Tier 1, Tier 2, recovery, and endophenotype evidence
  matrices because their portrait aspect ratio and dense labels do not work well
  on a 16:9 slide.

### Figure to avoid until repaired

Do not use page 1 of the
[CSF endophenotype locus plots](../../results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_locus_plots.pdf)
for amyloid-beta 42 as currently rendered. The APOE regional P value is stored as
numerical zero; the plotting code converts the resulting nonfinite `-log10(P)`
to a zero-height bar, visually implying no APOE signal even though APOE passed
both the regional and MAGMA gates. Regenerate the plot using a documented finite
floor or display cap before presentation.

## 5. Shorter and longer versions

- **Five-minute update:** Slides 1, 2–3 combined, 4, 5–7 combined, and 10.
- **Fifteen-minute scientific talk:** Use all 10 slides and add the detailed
  dataset/threshold appendix only during questions.
- **Methods review:** Keep the 10-slide story but promote the dataset inventory,
  frozen thresholds, and reproducibility caveats into the main deck.
