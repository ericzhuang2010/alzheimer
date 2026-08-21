# SEA-AD–ROSMAP Human-Validation Setup Figure Plan

## Status

**Implemented and validated on 2026-08-20.**

Figure ID: `seaad_rosmap_validation_setup`

Implementation:

- renderer: `scripts/figures/validation_human/plot_seaad_rosmap_validation_setup.py`;
- tests: `tests/validation_human/test_seaad_rosmap_validation_setup.py`; and
- validated package: `results/figures/validation_human/seaad_rosmap_validation_setup/`.

This document defines one slide-native setup figure for the human-validation
section. It is intentionally based on the validated compact artifacts already
downloaded under `results/validation_human`. Neither Phase 05 nor Phase 06 is
required for this schematic.

The design must make three facts immediately clear:

1. SEA-AD supplies independent donor-level expression evidence and independent
   signed mitochondrial queries.
2. SEA-AD and ROSMAP use the same frozen broad-network and Phase 18 selection
   scaffold, except that the SEA-AD effective-query minimum is 3 genes rather
   than 10.
3. Candidate-bearing ROSMAP tables are held out from the SEA-AD KDA/selection
   code and are first read for comparison after the SEA-AD list has been
   checksum-frozen.

## Purpose

Create one reproducible landscape figure that explains how the SEA-AD
validation was set up before the audience sees the key-driver and overlap
results. The figure should answer:

1. What is independent between SEA-AD and ROSMAP?
2. How do 129 SEA-AD supertypes and six sex/APOE groups become signed KDA
   queries?
3. What technical assets and selection rules are shared?
4. When are the frozen ROSMAP results opened?
5. What is the exact unit used for the final comparison?

This is a workflow and study-design figure. It is not an effect-size plot, a
causal diagram, or an area-proportional funnel.

## Main message

> Independent SEA-AD donor-level DEG queries were analyzed with the frozen
> Phase 18 network/KDA scaffold; the SEA-AD list was selected and frozen before
> candidate-bearing ROSMAP tables were read for a strict network–gene–class
> comparison.

## Intended slide use

Recommended slide title:

```text
HUMAN VALIDATION • STUDY SETUP
```

Recommended slide headline:

```text
Independent SEA-AD queries; shared frozen KDA scaffold; post-freeze ROSMAP comparison
```

Keep the slide title, headline, and source line as editable PowerPoint text.
Do not bake them into the figure asset.

The setup figure should appear before the SEA-AD top-five and ROSMAP-overlap
figures. Consequently, the canonical setup asset stops at the comparison rule
and does not reveal the number of rediscovered units. A result-annotated badge
is specified below as an optional later-slide variant.

## Deliverable configurations

| Configuration | Deliverable | Trade-off |
|---|---|---|
| Lite | Native-slide boxes and arrows only | Fast, but not data-bound or automatically validated |
| Standard | Code-rendered SVG/PDF/PNG with frozen counts | Reproducible main schematic with a compact validation table |
| **Advanced — selected** | Standard plus plot-data, checks, methods, caption, hashes, and color/grayscale review | Best balance for this presentation and later reuse |
| Publication+ | Advanced plus a separately composed manuscript-size version and formal accessibility package | Useful only if this becomes a paper figure |

The Advanced configuration was implemented. The canonical package includes
the three image formats, plot data, checks, caption, methods, provenance
hashes, and final validation status.

## Proposed composition

Use a single wide asset with four labeled regions:

- **A. Independent SEA-AD evidence** — the dominant solid blue/teal lane;
- **B. Shared frozen technical scaffold** — a neutral slate band connected by
  dashed lines only to the steps it supports;
- **C. Frozen ROSMAP reference** — a smaller orange outlined lane shown with a
  holdout lock during SEA-AD analysis; and
- **D. Post-freeze comparison** — a terminal dual-outline box to the right of
  an explicit post-freeze opening gate.

### Wireframe

```text
 A. INDEPENDENT SEA-AD EVIDENCE
 ┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
 │ 78 donors    │ → │ Donor × 129     │ → │ Within-stratum  │
 │ 1.189M nuclei│   │ supertypes      │   │ edgeR QL DEG    │
 │ donor=replicate│ │ 6 fixed groups  │   │ 1,548 slots     │
 └──────────────┘   └──────────────────┘   └────────┬─────────┘
                                                    ▼
                                       ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
                                       │ Signed core-Mito │ → │ Directed KDA +  │ → │ SEA-AD FREEZE   │
                                       │ query; |Qeff| ≥3 │   │ Phase 18 select │   │ 13 units        │
                                       └──────────────────┘   │ 42 KDA calls    │   └────────┬─────────┘
                                                              └──────────────────┘            │
 B. SHARED FROZEN TECHNICAL SCAFFOLD
        [7 broad networks] [current symbol/core MitoCarta] [fKDA] [BH–ACAT–gates–rank]
                   · · · dashed connectors to query/KDA/selection only · · ·

 C. ROSMAP REFERENCE
 ┌──────────────────────────────────────────────────────────┐
 │ Phase 18: 54 fine types across 9 source networks        │
 │ 6 groups × 2 = 648 slots; minimum 10                    │
 │ 161 included runs and 47 units in 7 matched networks    │
 └───────────────────────────────────────────────┬──────────┘
                                                 │  🔒 held out / not read
                                 ╎ OPEN FOR COMPARISON ONLY AFTER SEA-AD FREEZE ╎
                                                 ├──────────────────────────┐
 SEA-AD frozen list ─────────────────────────────┘                          │
                                                                            ▼
                                                         D. STRICT COMPARISON
                                                         broad network + gene
                                                         + driver class
                                                         common assessable universe
```

The final renderer may place the SEA-AD boxes on one line or wrap them onto two
lines, but every solid analysis arrow must preserve the scientific sequence.
There must be no connector from a ROSMAP candidate box into the SEA-AD query,
KDA, or selection boxes.

## Panel A — Independent SEA-AD evidence

Use a solid teal/blue lane occupying approximately 70–75% of the visual
weight. The lane should contain five steps.

### A1. Independent cohort

Visible copy:

```text
SEA-AD cohort
78 donors
37 Dementia | 41 No dementia
1,189,172 selected nuclei
Donor = statistical replicate
```

The donor statement is essential. Nuclei must never be presented as
independent replicates.

### A2. Donor × fine-supertype pseudobulk

Visible copy:

```text
Donor-level pseudobulk
129 distinct supertypes
each assigned to 1 of 7 matching networks
6 fixed sex/APOE groups
F/M × {e2, e33, e4}
```

Use a small mapping strip or compact annotation beneath the box:

```text
Astro 6 | Exc 41 | Inh 67 | Micro 4 | OPC 3 | Oligo 4 | Vasc 4
```

The mapping selects a broad network and later aggregation stratum; it does not
pool fine supertypes before DEG or KDA. The seven counts sum to 129. Add a
small note or icon key for the profile and contrast support gates:

```text
profile ≥20 nuclei; direct contrast ≥5 donors per phenotype arm
```

Do not imply that all six strata were estimable for every supertype. APOE2/4
donors were excluded from this grouping contract.

### A3. Within-stratum differential expression

Visible copy:

```text
Within-stratum edgeR QL DEG
Dementia − No dementia
129 × 6 = 774 contrasts
up ▲ / down ▼ = 1,548 structural slots
```

Use a compact model footer:

```text
one grouped model per supertype; adjusted for age at death, PMI, and study
```

The frozen model is
`~ 0 + diagnosis_sex_apoe_group + age_death_scaled + pmi_scaled + study`;
each eligible group uses a direct Dementia-minus-No-dementia contrast from its
supertype's joint model.

Attach a neutral attrition badge:

```text
260 contrasts completed → 520 completed-source directions
ready for query construction
514 contrasts not estimable
```

If space permits, show the six fixed groups as equal-width chips rather than a
second chart. Use solid chips for the groups that yielded completed fine
contrasts and gray dashed chips for zero-completion groups:

```text
F_e2 0 | F_e33 100 | F_e4 68 | M_e2 0 | M_e33 92 | M_e4 0
               completed contrasts by fixed group
```

The chip widths must remain equal; the counts are labels, not area encodings.

The word **structural** must remain beside 1,548. These are planned directional
slots, not 1,548 runnable KDA calls. The six strata are separate direct disease
contrasts, not sex-by-APOE interaction tests.

The public-facing phenotype labels must remain `Dementia` and `No dementia`.
Do not relabel the SEA-AD reference arm as `NCI`. The downstream machine labels
`AD_up_mito` and `AD_down_mito` are compatibility aliases for the signed
Dementia contrast.

### A4. Signed mitochondrial query and network background

Make this the most visually prominent decision box in Panel A.

Visible copy:

```text
Signed core-MitoCarta query
FDR < 0.05
|log2FC| > log2(1.3)
Dementia-up ▲ or Dementia-down ▼
Qeff = Q0 ∩ induced-network background
run if |Qeff| ≥ 3 genes
```

The renderer's methods record must preserve the exact set definitions:

```text
Q0 = unique current symbols that are tested, core MitoCarta,
     FDR < 0.05, |logFC| > log2(1.3), and have the required sign

B  = endpoints of edges in the matching broad network after inducing
     the network on the exact tested-symbol set

Qeff = Q0 ∩ B
```

Do not replace `B` with a simple tested-gene/network-node intersection. Isolated
tested network nodes that have no retained induced edge are not in the
background.

Attach a compact outcome badge:

```text
42 runnable queries / KDA calls
20 up | 22 down
21 queries contain 3–9 genes | 21 contain ≥10
```

### A5. Directed KDA, aggregation, selection, and SEA-AD freeze

This may be one wide box or two connected boxes if the text is crowded.

Visible KDA copy:

```text
Directed KDA
matching frozen broad network
3-hop candidate family; test directed downstream layers 1–3
42 calls: 29 with ≥1 significant return | 13 with none
```

Visible selection copy:

```text
Phase 18-compatible selection
aggregate within broad network
MT and non-MT driver classes separate
coverage ≥0.80 • ACAT q ≤0.05 • support ≥1
rank q, p, symbol; show up to 5, no backfill
```

End the SEA-AD lane with a visually distinct checksum/lock card:

```text
SEA-AD LIST FROZEN
13 network–gene–class units
8 MT | 5 non-MT; 11 gene symbols
```

The KDA candidate universe is the assessable network genes, not the 47 ROSMAP
candidates and not the mitochondrial query members alone. The display limit is
a cap; it does not force five genes into every network/class list.

The methods record should also state that each broad network's aggregate
candidate universe is the union of included-run backgrounds. Explicit final
raw P values enter ACAT, usable implicit tests contribute P = 1, and
background-absent runs are omitted. Aggregate BH is applied within a broad
network across coverage-passing genes from both driver classes before support
or candidate-status filtering.

## Panel B — Shared frozen technical scaffold

Use a light slate band directly below the SEA-AD query, KDA, and selection
steps. Connect the band with thin dashed lines rather than solid workflow
arrows.

Visible copy:

```text
SHARED, FROZEN TECHNICAL SCAFFOLD
7 broad Bayesian networks • current-symbol/core-MitoCarta annotation
fKDA engine • MT self-exclusion • within-run BH • ACAT • aggregate BH
coverage/support/q gates • class-specific ranking
```

Add a short high-contrast boundary label:

```text
Shared network/KDA assets and selector — not cohorts, DEG models,
queries, or candidate identities
```

The shared scaffold should connect to both analyses, but the ROSMAP lane may
show its already-completed Phase 18 process in compressed form. The graphic
must not imply that the seven networks were inferred de novo in SEA-AD.

The independence boundary represented by the band is:

| Independent/cohort-specific | Shared and frozen |
|---|---|
| donors and phenotype labels | seven broad-network files |
| fine-cell taxonomy | current-symbol/core-MitoCarta annotation |
| DEG estimator and tested-gene universe | fKDA engine and parameters |
| signed DEG membership and effective queries | self-exclusion, BH, ACAT, gates, classes, and ranking |
| candidate selection output | strict comparison key |

The only intentional numerical departure in downstream KDA run inclusion is:

| Cohort | Minimum effective query size |
|---|---:|
| SEA-AD | 3 genes |
| ROSMAP Phase 18 | 10 genes |

All selection-bearing aggregation, gate, correction, class, and ranking rules
remain Phase 18-compatible.

For provenance, a conservative supporting run means final overlap of at least
two other query genes, final fold enrichment greater than one, and final
within-run BH q at most 0.05. ACAT combines final raw run P values; usable
implicit tests contribute P = 1 and background-absent runs are omitted.

## Panel C — Frozen ROSMAP reference

Use a narrow orange/gold lane separated from Panel A by white space. Use an
outlined style so it reads as a frozen reference rather than a second
discovery flow being rerun in this figure.

Visible copy:

```text
ROSMAP Phase 18 reference
276 global analytic donors
Original scope: 54 fine cell types | 9 source networks
54 × 6 groups × 2 directions = 648 structural slots
minimum query 10
Matched scope: 7 SEA-AD networks
161 included KDA runs
47 frozen top-five units | 25 gene symbols
```

The ROSMAP phenotype is AD versus NCI; it must not be used to relabel the
SEA-AD phenotype. The 54 ROSMAP fine cell types span nine original source
networks, including CAMs and T cells; those two networks contribute no
included Phase 18 run or selected unit. The 161 included runs and all 47
selected units therefore lie in the seven networks matched to SEA-AD. The 54
ROSMAP fine cell types and 129 SEA-AD supertypes are cohort-specific
taxonomies. Do not draw one-to-one fine-type links. Their legitimate shared
comparison level is the seven frozen broad networks.

Place a closed lock on the ROSMAP output and label it:

```text
Candidate-bearing tables held out and not read by SEA-AD KDA/selection code
```

The orange arrow may cross the post-freeze opening gate only after the SEA-AD
freeze card has been reached.

## Panel D — Post-freeze strict comparison

Use a dual blue/orange outline and a vertical dashed gate labeled:

```text
OPEN FOR COMPARISON ONLY AFTER SEA-AD FREEZE
```

Visible comparison copy:

```text
Strict rediscovery comparison
unit = broad network + gene + driver class
compare within the common assessable universe
```

Encode three possible states without implying that missing evidence is a
negative result:

- shared/rediscovered;
- testable but not rediscovered; and
- not testable in SEA-AD.

### Optional results badge

For a later results slide, and only when explicitly enabled, add:

```text
13 SEA-AD units
36 of 47 ROSMAP units testable
6 strict shared units
```

If the optional badge is shown, the caption must state that the six strict
network–gene–class units contain four distinct strict-match symbols. The
network-agnostic gene-only overlap contains six symbols and is a different
analysis. Do not label the strict result as “six unique genes.”

The canonical setup asset leaves this results badge off so the subsequent
overlap slide carries the result.

## Visual encoding

### Canvas and placement

- Design for a 13.333 × 7.5 inch, 16:9 slide.
- Reserve slide title/headline space and an editable source line.
- Target figure placement: approximately `x = 0.45`, `y = 1.48`,
  `w = 12.43`, `h = 4.71` inches.
- Render the standalone asset at the same 2.64:1 aspect ratio.
- Export the PNG at 450 DPI with a white background; preserve vector text and
  shapes in PDF and SVG.

### Color and shape

| Meaning | Primary encoding | Color |
|---|---|---|
| SEA-AD independent evidence | Solid boxes and arrows | blue `#0072B2`, teal `#009E73`, pale teal `#DDEFF2` |
| ROSMAP frozen reference | Orange outline and pale fill | orange `#E69F00`, pale gold `#FFF2CC` |
| Shared scaffold | Neutral band and dashed connectors | navy `#17365D`, slate `#5B6573`, pale gray `#EEF1F4` |
| Dementia-up query | Up triangle plus text | vermilion `#D55E00` |
| Dementia-down query | Down triangle plus text | blue `#0072B2` |
| Not estimable/unavailable | Gray, dashed outline | gray `#B8BDC5` |
| Post-freeze opening boundary | Lock plus dashed vertical rule | navy `#0F233D` |

Never rely on color alone. Repeat cohort, direction, lock, and status labels in
text and use shape/line-style redundancy. The palette must remain legible in
grayscale and for common color-vision deficiencies.

### Typography and density

- Use Arial, Helvetica, or another clean sans-serif font.
- Region labels: 16–18 pt bold at intended slide placement.
- Box headings: 14–16 pt bold.
- Body labels and counts: at least 12–14 pt after placement.
- Use at most six visible lines per process box.
- Make `1,548 structural slots`, `42 KDA calls`, `SEA-AD LIST FROZEN`, and the
  post-freeze opening gate the strongest typographic anchors.
- Keep detailed formulas and caveats in the caption/methods record if they
  cannot remain readable at slide size.

### Arrow grammar

- Solid arrow: chronological analysis flow within one cohort.
- Dashed connector: a shared frozen asset or rule used by a process.
- Orange outlined arrow: movement of the held-out ROSMAP reference.
- Dashed vertical rule with lock: protocol/read-order boundary.
- No arrow may suggest that ROSMAP candidate identities seed SEA-AD query
  construction or candidate testing.

Do not use a Sankey, area-scaled funnel, screenshots, decorative network hairballs,
red–green encoding, significance stars, or causal arrowheads.

## Authoritative numerical anchors

The renderer must treat the following values as validation assertions, not as
free text typed independently into drawing code.

| Topic | Frozen value |
|---|---:|
| SEA-AD analysis donors | 78 = 37 Dementia + 41 No dementia |
| SEA-AD selected nuclei | 1,189,172 |
| Included SEA-AD supertypes | 129 |
| Fixed sex/APOE groups | 6 |
| Fine DEG contrasts | 774 = 129 × 6 |
| Structural direction slots | 1,548 = 774 × 2 |
| Completed fine contrasts | 260 |
| Not-estimable fine contrasts | 514 |
| Completed contrasts by group | F_e33 100; F_e4 68; M_e33 92; other groups 0 |
| Completed-source directions | 520 |
| Active SEA-AD KDA calls | 42 = 20 up + 22 down |
| SEA-AD query-size tiers | 21 with 3–9 genes; 21 with ≥10 genes |
| SEA-AD KDA call outcomes | 29 calls with ≥1 significant return; 13 with none |
| SEA-AD selected units | 13 = 8 MT + 5 non-MT; 11 symbols |
| ROSMAP global analytic donor universe | 276 |
| ROSMAP original fine/network scope | 54 fine types across 9 source networks |
| ROSMAP Phase 18 structural slots | 648 = 54 × 6 × 2 |
| ROSMAP included Phase 18 runs | 161 |
| Frozen ROSMAP selected units | 47; 25 symbols |
| Shared broad networks | 7 |

The SEA-AD supertype counts by broad network must be read or derived as:

| Broad network | Included SEA-AD supertypes |
|---|---:|
| Astrocytes | 6 |
| Excitatory neurons | 41 |
| Inhibitory neurons | 67 |
| Microglia | 4 |
| OPCs | 3 |
| Oligodendrocytes | 4 |
| Vasculature cells | 4 |
| **Total** | **129** |

The full SEA-AD structural-slot partition is:

```text
1,548 = 1,028 source-contrast-not-estimable
      +   462 effective-query size 0
      +    16 effective-query size 1–2
      +    21 effective-query size 3–9
      +    21 effective-query size ≥10
```

Only the last two categories contribute to the 42 active KDA calls.

## Interpretation guardrails

The figure, caption, and speaker notes must preserve all of the following:

1. `1,548` is the structural number of signed slots; only `42` were runnable.
2. Donors, not nuclei, are the statistical replicates in SEA-AD DEG.
3. The six strata are separate disease contrasts, not interaction tests.
4. SEA-AD compares Dementia with No dementia; ROSMAP compares AD with NCI.
5. SEA-AD and ROSMAP fine labels are not one-to-one.
6. Existing broad pooled DEG anchors did not enter the headline fine-supertype
   KDA analysis.
7. The seven broad networks and selection machinery are shared and frozen;
   they were not reconstructed from SEA-AD.
8. ROSMAP candidate identities did not define the SEA-AD query or KDA
   candidate universe.
9. SEA-AD's query minimum is 3; ROSMAP Phase 18's is 10.
10. Only 42 KDA calls were run. No FDR-only 84-call branch was executed.
11. “Top five” means at most five per network/class list, with no backfill.
12. KDA prioritization is network evidence, not proof of causal regulation.
13. A ROSMAP unit that is not testable in SEA-AD is unavailable evidence, not
    a failed replication.
14. Six strict shared units, if later annotated, are not six unique strict
    genes.

## Research-risk review

- **Strongest evidence in the setup:** the SEA-AD selection freeze records
  that candidate-bearing ROSMAP files were not read during SEA-AD KDA and
  selection.
- **Most important shared assumption:** both cohorts are projected onto the
  same seven frozen broad-network scaffolds despite different fine-cell
  taxonomies and phenotype definitions.
- **Main false-positive concern:** half of the active SEA-AD calls use small
  3–9-gene queries, which is why the threshold difference must be visible.
- **Main overinterpretation risk:** recurrence under a shared network and
  selector is narrower than a fully independent de novo network replication.
- **Fallback if the slide is too dense:** retain the independence/lock diagram
  and move the detailed 1,548-to-42 attrition arithmetic into a separate query
  construction figure; do not shrink labels below the readability floor.

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

## Data and implementation workflow

### Authoritative inputs

Read only the compact validated artifacts required for visible claims:

| Figure content | Authoritative artifact |
|---|---|
| SEA-AD donor totals and phenotype/group counts | `results/validation_human/02_cohort/status.tsv`; `donor_group_counts.tsv` |
| SEA-AD current-symbol and gene-annotation authority | `results/validation_human/03_genes/status.tsv`; `gene_annotation_master.tsv` |
| Selected nuclei, 129 supertypes, and support counts | `results/validation_human/04_supertype_manifest/status.tsv`; `supertype_to_broad_network.tsv`; `donor_supertype_nucleus_counts.tsv` |
| 774 contrasts and 1,548 directions | `results/validation_human/07_contrasts/status.tsv` |
| Completed/not-estimable DEG counts and group distribution | `results/validation_human/08_deg/status.tsv`; `fine_supertype_phase18_parity/fine_contrast_status.tsv`; `query_handoff/fine_direction_manifest.tsv` |
| DEG model, covariates, and profile/contrast gates | `scripts/validation_human/seaad_deg_config.yml` |
| Query rule and threshold | `scripts/validation_human/seaad_phase18_validation_config.yml` |
| Query attrition, networks, and recorded input checks | `results/validation_human/10_seaad_kda_rediscovery/10a_inputs/status.tsv`; `input_authority.tsv`; `input_checks.tsv`; `network_identity.tsv`; `query_attrition.tsv`; `seaad_kda_run_manifest.tsv` |
| KDA call outcomes | `results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv` |
| SEA-AD freeze and selected units | `results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv`; `seaad_selection_freeze.tsv`; `seaad_top5.tsv` |
| ROSMAP global donor count | `results/minerva_production/02_cohort/cohort_status.tsv` |
| Frozen ROSMAP units | `results/validation_human/09_rosmap_kda_candidates/status.tsv`; `phase18_selected_candidate_units.tsv`; `shared_network_scope.tsv` |
| ROSMAP fine-type, source-network, and KDA/run scope | `results/minerva_production/12_kda/kda_status.tsv`; `kda_run_manifest.tsv`; `config/phase12_kda.yml`; `config/phase18_key_driver_selection.yml` |
| Strict comparison definition and optional badge | `results/validation_human/10_seaad_kda_rediscovery/10d_overlap/status.tsv`; `rosmap_seaad_candidate_overlap.tsv` |

Phases 05 and 06 are not inputs. Their compact pseudobulk/QC artifacts are not
present in this download, so library-size, detected-gene, mitochondrial-fraction,
MDS/PCA, and pseudobulk-reconciliation panels cannot be substantiated locally.
None of those elements belongs in this setup schematic. Do not add a Phase 05
or Phase 06 QC claim or proxy panel.

The compact setup renderer validates the recorded VH10A rule checks, authority
hashes, network identities, manifest counts, and attrition summaries; it does
not reconstruct query/background membership. Full membership recomputation
would additionally require the currently absent
`10a_inputs/seaad_kda_signature_members.tsv.gz` and
`10a_inputs/seaad_kda_background_members.tsv.gz` plus the currently absent
VH08 tested/filter shards registered in the phase artifact manifest. Their
registered hashes remain available. Do not silently weaken a recorded-rule
validation into a claim of full re-derivation.

### Renderer structure

Create:

```text
scripts/figures/validation_human/
    plot_seaad_rosmap_validation_setup.py

tests/
    validation_human/test_seaad_rosmap_validation_setup.py
```

The renderer should:

1. validate the required upstream `status.tsv` records before extracting any
   plotted value;
2. read and derive every count shown in the asset;
3. verify all cross-file arithmetic and identity constraints;
4. build a tidy plot-data table with one row per visible block, badge, label,
   or connector;
5. render one Matplotlib object to PNG, PDF, and SVG;
6. write caption, methods, checks, input hashes, and output hashes; and
7. write the final figure status only after every artifact and visual check
   has passed.

Use vector-native rectangles, arrows, brackets, triangles, and a lock drawn
from simple paths. Do not depend on an external icon font or raster artwork.

### Generated figure package

Write atomically under:

```text
results/figures/validation_human/seaad_rosmap_validation_setup/
```

Generated files:

```text
seaad_rosmap_validation_setup.png
seaad_rosmap_validation_setup.pdf
seaad_rosmap_validation_setup.svg
seaad_rosmap_validation_setup_plot_data.tsv
seaad_rosmap_validation_setup_checks.tsv
seaad_rosmap_validation_setup_caption.md
seaad_rosmap_validation_setup_methods.md
seaad_rosmap_validation_setup_artifacts.tsv
seaad_rosmap_validation_setup_status.tsv
```

The plot-data table must contain every visible number, label, ordering key,
style key, source path, and whether the value was read or derived. Record
SHA-256 values for each authoritative input, the renderer, and the seven
payload files other than the artifact manifest and final status. The artifact
manifest must not hash itself. The final status is written after and references
the completed artifact manifest rather than being hashed by that manifest.

## Automated validation contract

The renderer or test must fail before publishing if any blocking check fails.

### Input and status checks

- VH02, VH03, VH04, VH07, VH08, VH09, VH10A, VH10B, VH10C, and VH10D report
  `validated_complete`.
- All visible source files exist, are nonempty, and match their registered
  hashes when a hash is available.
- The seven broad-network machine identifiers match exactly between SEA-AD
  and the frozen Phase 18 scope.

### Arithmetic and identity checks

- `78 = 37 + 41` SEA-AD donors.
- the seven supertype counts sum to 129;
- `129 × 6 = 774` contrasts;
- `774 × 2 = 1,548` direction slots;
- `260 + 514 = 774` contrasts;
- completed contrasts by group are exactly F_e33 = 100, F_e4 = 68,
  M_e33 = 92, and zero in F_e2, M_e2, and M_e4;
- `520 + 1,028 = 1,548` directions;
- `462 + 16 + 21 + 21 = 520` completed-source directions;
- `21 + 21 = 42` active calls;
- `20 + 22 = 42` up/down active calls;
- `29 + 13 = 42` KDA call outcomes;
- SEA-AD selected units equal 13, split into 8 MT and 5 non-MT, with 11
  unique symbols after filtering `seaad_top5.tsv` to
  `list_status == ranked_candidates` and nonmissing symbols/ranks;
- `54 × 6 × 2 = 648` ROSMAP structural slots;
- the 54 ROSMAP fine types span nine original source networks;
- ROSMAP included runs equal 161;
- all 161 included runs and all 47 selected units lie in the seven networks
  matched to SEA-AD;
- frozen ROSMAP selected units equal 47, with 25 unique symbols; and
- the comparison key is exactly `broad_network + gene + case_id` after both
  cohort-specific symbol fields have been normalized to the frozen current
  symbol.

### Scientific-rule checks

- the SEA-AD query predicate uses exclusive `FDR < 0.05` and
  `abs(logFC) > log2(1.3)` with the correct sign;
- the SEA-AD minimum effective query size is 3 and the ROSMAP minimum is 10;
- `config/phase12_kda.yml` retains the
  `exact_contrast_tested_intersect_induced_network` background policy,
  VH10A records `effective_queries_subset_background == True`, and the
  recorded authority, network, and result hashes validate; this compact check
  is not represented as membership re-derivation;
- the SEA-AD selector uses the two current driver classes only;
- coverage is at least 0.80, conservative support is at least one, and
  aggregate ACAT q is at most 0.05;
- ranking is within broad network and driver class by q, p, then symbol, with
  a display cap of five and no backfill;
- `seaad_selection_freeze.tsv` records
  `rosmap_candidate_files_read == False`, and the comparison stage begins only
  from a valid frozen SEA-AD selection; and
- no ROSMAP candidate identity appears in the SEA-AD query or candidate-input
  nodes of the plot-data graph.

### Output checks

- all nine declared output files exist and are nonempty;
- PNG dimensions and DPI match the declared export contract;
- the PDF begins with a valid PDF signature;
- the SVG contains vector paths/shapes and searchable text;
- output hashes in `artifacts.tsv` match the seven payload files in its
  declared hash scope; the manifest does not self-hash and does not claim a
  hash for the later status file;
- no text extends beyond its box or canvas; and
- the status file is written last and reports `validated_complete` only after
  all other checks pass.

## Manual visual review

Review the final asset at its intended PowerPoint placement, not only when
zoomed in. Confirm:

1. the independent SEA-AD lane is visually dominant;
2. the shared scaffold is unmistakably shared but does not look like shared
   candidate evidence;
3. the ROSMAP lane cannot be read as an input to SEA-AD query construction;
4. the lock and post-freeze opening order remain clear in grayscale;
5. `1,548 structural slots` cannot be confused with 1,548 KDA calls;
6. `No dementia` is not shown as `NCI`;
7. up/down direction is identifiable without color;
8. every count has an explicit unit;
9. no label is clipped; and
10. the figure remains readable from a normal presentation viewing distance.

## Draft caption

**Independent SEA-AD validation of ROSMAP Phase 18 key drivers.** SEA-AD
expression evidence was generated from donor-level pseudobulk profiles across
129 fine supertypes and six fixed sex/APOE groups. The 774 direct
Dementia-versus-No-dementia contrasts produced 1,548 prespecified signed
direction slots; 260 contrasts were estimable, yielding 520 completed-source
directions ready for query construction. One grouped edgeR quasi-likelihood
model was fit per supertype with adjustment for age at death, PMI, and study.
Core-MitoCarta genes meeting within-contrast FDR and effect-size
criteria were intersected with the tested-gene-induced background of the
matching frozen broad network. Forty-two effective queries contained at least
three genes and entered directed KDA. Candidate evidence was aggregated and
ranked with the frozen Phase 18 two-class selection rules, after which the
13-unit SEA-AD list was checksum-frozen. Candidate-bearing tables for the
47-unit ROSMAP Phase 18 reference were not read by the SEA-AD KDA/selection
code and were opened for comparison only after this freeze. Comparison used
the strict broad-network, gene, and driver-class key in the common assessable
universe. The expression cohorts and queries were independent; the seven
broad networks, annotation, KDA engine, and selection machinery were
intentionally shared.

## Draft source line

```text
Source: validated SEA-AD donor-level pseudobulk DEG and KDA outputs; frozen ROSMAP Phase 18 reference; shared broad Bayesian-network scaffold.
```

## Completion record

The implementation is complete because:

- the canonical setup-only composition is rendered without the optional
  overlap-result badge;
- the optional results badge remains disabled for the setup slide;
- all visible numbers are read or deterministically derived from the
  authoritative compact artifacts;
- the output package and validation contract above are implemented;
- the rendered asset passes automated checks plus color and grayscale review
  at the intended 16:9 slide placement; and
- `tests/validation_human/test_seaad_rosmap_validation_setup.py` passes.
