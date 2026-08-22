# SEA-AD–ROSMAP human-validation presentation figure plan

## Status and scope

**Status:** all external analytical figures in this plan are implemented and
validated. The existing `seaad_two_case_circular` package remains the sole
canonical MT/non-MT circular source; no presentation-specific duplicate is
maintained. The remaining workflow, support, testability, and explanatory
diagrams are designed here for native PowerPoint construction during deck
assembly.

**Companion deck design:**
[`seaad_rosmap_human_validation_presentation_design.md`](../../validation_human/seaad_rosmap_human_validation_presentation_design.md)

This plan defines the figures needed for the completed SEA-AD human-validation
presentation. It uses the executed VH02, VH04, VH07–VH10 results and the three
existing validated figure packages. VH05 pseudobulk matrices and VH06
pseudobulk-QC artifacts are intentionally out of scope: the presentation does
not require PCA/MDS, library-size, detected-gene, or mitochondrial-fraction QC
plots.

The agreed hybrid build uses:

- the existing validated MT/non-MT circular pair plus separately rendered,
  validated analytical figures where a standalone evidence graphic is needed;
- seven native, editable PowerPoint compositions for the opening summary,
  simplified setup, cohort/taxonomy overview, donor support, query attrition,
  testability, and closing conclusions; and
- the detailed existing setup and original Venn figures for appendix use.

The canonical circular figures serve both the main deck and appendix and
should receive nearly a full slide. The detailed setup and original Venn remain
useful in the appendix; they should not be cropped or reduced into the main
deck because their embedded labels are too small for projection.

## 1. Figure suite

| Figure ID or composition | Deck slide | Build type | Status | Main question |
|---|---:|---|---|---|
| `seaad_rosmap_validation_setup_slide` | 2 | native slide using validated setup as source | pending deck assembly | What was independent, what was shared, and when was ROSMAP opened? |
| `seaad_donor_support_and_estimability` | 4 | native slide | pending deck assembly | Why were only 260 of 774 DEG contrasts estimable? |
| `seaad_fine_deg_landscape` | 5 | external package | validated complete | Where was the fine-supertype DEG signal concentrated? |
| `seaad_query_attrition_and_availability` | 6 | native slide | pending deck assembly | How did 1,548 structural directions become 42 KDA calls? |
| `seaad_kda_call_outcomes` | 7 | external package | validated complete | Which runnable queries returned key-driver evidence? |
| `seaad_two_case_circular` — MT | 8 | existing canonical package | validated complete | Which MT drivers were selected, and which recur across networks? |
| `seaad_two_case_circular` — non-MT | 9 | existing canonical package | validated complete | Which non-MT drivers were selected, and which lists were unavailable? |
| `seaad_rosmap_testability` | 10 | native slide | pending deck assembly | Which ROSMAP selected units could be tested in SEA-AD? |
| `seaad_rosmap_strict_overlap_ranks` | 11 | external package | validated complete | Which drivers recurred in the same network and class? |
| `seaad_rosmap_top_driver_gene_overlap_slide` | 12 | external derivative | validated complete | Which unique genes overlap after network identity is collapsed? |
| `seaad_rosmap_non_mt_diagnostic` | 13 | external package | validated complete | Why did the final non-MT lists have no common genes? |

Slides 1, 3, and 14 should use editable slide-native elements rather than
additional rendered figures. Appendix tables should also remain editable
unless a table is too large to render reliably in PowerPoint.

For a shorter ten-minute, ten-slide deck, four pairs can be merged without
changing any scientific definitions:

1. the native cohort/taxonomy overview with donor support and estimability;
2. the fine-DEG landscape with query attrition;
3. non-MT selected drivers with the non-MT evidence-fate diagram; and
4. ROSMAP testability with strict paired-rank overlap.

The canonical figure packages should nevertheless remain separate so the
longer and shorter decks can be assembled from the same validated assets.

## 2. Shared visual and technical contract

### Slide placement

- PowerPoint canvas: 13.333 × 7.5 inches.
- Default figure canvas: approximately 12.0 × 5.3 inches, leaving the editable
  conclusion title, takeaway, and source line outside the image.
- Do not bake the slide title, conclusion headline, page number, or source line
  into an asset.
- Use contain/no-crop placement. Never crop an existing figure to hide its
  title or legend.
- Main labels must be at least 16 pt at their final slide placement. Panel
  headings should be 18–22 pt.
- Use Arial, Aptos, Helvetica, or another presentation-safe sans serif.

### Color and redundant encoding

| Meaning | Color | Additional encoding |
|---|---|---|
| SEA-AD | teal `#009E73` | solid fill or line |
| ROSMAP | orange `#E69F00` | outlined or hatched |
| shared/rediscovered | navy `#0F233D` | bold line and direct label |
| Dementia-up | vermilion `#D55E00` | up triangle |
| Dementia-down | blue `#0072B2` | down triangle |
| tested, no passing result | light gray `#BDBDBD` | solid gray plus text |
| not estimable/not testable | white with dark-gray border | dashed border or cross-hatch plus text |

The MT circular derivative retains the frozen seven-network palette. Every
status must also be represented by a label, shape, hatch, or line style so the
figures remain interpretable in grayscale.

### Terminology shown on figures

- Use `Dementia` and `No dementia` for SEA-AD; do not substitute `AD` and
  `NCI`.
- Use `structural direction slots` for 1,548 and `KDA calls` for 42.
- Use `call with ≥1 significant return`, not `significant call`.
- Use `MT driver class (core MitoCarta)` where space permits; MT does not mean
  mtDNA-only in the general method.
- Use `not testable` rather than `failed replication` when no included SEA-AD
  run existed.
- Keep `no passing candidate`, `tested but not selected`, and `not testable`
  visually and verbally distinct.
- The strict unit is `broad network + gene + driver class`.
- The gene-level Venn is secondary and collapses network identity.

### Figure package contract

Each separately rendered figure is generated as a self-contained package
under:

```text
results/figures/validation_human/<figure_id>/
```

Each package should contain:

```text
<figure_id>.png
<figure_id>.pdf
<figure_id>.svg
<figure_id>_plot_data.tsv
<figure_id>_checks.tsv
<figure_id>_caption.md
<figure_id>_methods.md
<figure_id>_artifacts.tsv
<figure_id>_status.tsv
```

Add another table only when the visual has a distinct relational object, such
as overlap links or paired ranks. Export PNG at 450 DPI and preserve text and
vector geometry in SVG/PDF. The artifacts table hashes source inputs, the
renderer, and payload outputs; it does not hash itself or the subsequently
written status file. Write status last after automated validation and manual
color/grayscale review.

## 3. Figure 1 — validation setup slide derivative

**Figure ID:** `seaad_rosmap_validation_setup_slide`

**Deck use:** Slide 2

**Build mode:** editable native PowerPoint shapes; use the validated detailed
setup package as the frozen source rather than creating another external asset.

**Source asset:** validated
[`seaad_rosmap_validation_setup`](../../../results/figures/validation_human/seaad_rosmap_validation_setup)

### Main message

SEA-AD supplied independent donor-level expression evidence and signed
mitochondrial queries; the seven broad networks and KDA/selection machinery
were shared and frozen; candidate-bearing ROSMAP tables were read only after
the SEA-AD list was frozen.

### Layout

Use a simplified panoramic workflow with three lanes:

```text
SEA-AD: 78 donors → 129 supertypes × 6 groups → signed DEG queries
       → 42 KDA calls → Phase 18-compatible selection → freeze 13 units
                          ↑ shared frozen scaffold
ROSMAP: 47 frozen units ── held out during SEA-AD selection ──┐
SEA-AD frozen list ────────────────────────────────────────────┴→ strict comparison
```

The shared-scaffold ribbon contains only:

```text
7 broad networks • core-MitoCarta/current symbols • fKDA • BH/ACAT/gates/ranking
```

The final comparison box reads:

```text
broad network + gene + driver class
within the common assessable universe
```

### Visible anchors

- 78 SEA-AD donors;
- 129 supertypes × 6 groups × 2 directions = 1,548 structural slots;
- 42 SEA-AD KDA calls;
- 13 frozen SEA-AD units;
- 47 frozen ROSMAP units; and
- SEA-AD minimum effective query 3 versus ROSMAP minimum 10.

Do not reveal the overlap result in this setup asset. Do not draw any ROSMAP
arrow into SEA-AD DEG, query construction, KDA, or selection.

### Implementation note

Re-render from the validated plot data and current source tables. Do not crop
or shrink the current detailed PNG. The current detailed asset remains in the
appendix.

## 4. Figure 2 — donor support and DEG estimability

**Figure ID:** `seaad_donor_support_and_estimability`

**Deck use:** Slide 4

**Build mode:** editable native PowerPoint bars, threshold line, and callout.

### Main message

Only three of the six fixed sex/APOE groups had enough independent donors to
support any fine-supertype contrast, and supertype-specific nucleus support
reduced completion further to 260 of 774 contrasts.

### Layout

Use two aligned panels and one result callout.

**Panel A — cohort-wide donor support.** Show paired horizontal bars for
Dementia and No-dementia donors in all six groups. Draw the five-donor threshold
as a labeled vertical line.

| Group | Dementia | No dementia |
|---|---:|---:|
| `F_e2` | 1 | 6 |
| `F_e33` | 13 | 13 |
| `F_e4` | 9 | 5 |
| `M_e2` | 1 | 4 |
| `M_e33` | 9 | 10 |
| `M_e4` | 4 | 3 |

**Panel B — fine-contrast completion.** For each group, show a 129-unit stacked
bar split into completed and not estimable:

| Group | Completed | Not estimable |
|---|---:|---:|
| `F_e2` | 0 | 129 |
| `F_e33` | 100 | 29 |
| `F_e4` | 68 | 61 |
| `M_e2` | 0 | 129 |
| `M_e33` | 92 | 37 |
| `M_e4` | 0 | 129 |

**Callout:** `260 / 774 contrasts completed; 514 not estimable; 0 failed`.

### Required qualifier

The donor bars are cohort-wide. A donor enters a particular supertype contrast
only if that donor has a pseudobulk profile with at least 20 nuclei for that
supertype. Therefore a group with 13/13 donors overall can still have fewer
than 129 completed supertype contrasts.

### Sources

- [`donor_group_counts.tsv`](../../../results/validation_human/02_cohort/donor_group_counts.tsv)
- [`fine_contrast_status.tsv`](../../../results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv)
- [`07_contrasts/status.tsv`](../../../results/validation_human/07_contrasts/status.tsv)

## 5. Figure 3 — fine-supertype DEG landscape

**Figure ID:** `seaad_fine_deg_landscape`

**Deck use:** Slide 5

### Main message

Fine-supertype DEG signal was overwhelmingly concentrated in the `M_e33`
group and in excitatory and inhibitory neuronal contrasts.

### Layout

**Panel A — 129 × 6 heatmap.** Each row is a retained SEA-AD supertype and each
column is one fixed sex/APOE group. Color completed cells by:

```text
log10(1 + number of Phase 18-parity feature hits)
```

where the cell count is the sum of Dementia-up and Dementia-down hits for that
contrast. Use gray for not-estimable cells and white for completed cells with
zero hits. Group rows into the seven broad networks with labeled side bands.
Do not label all 129 rows on the main slide. Within a broad network, order by
total parity-hit count descending and then stable `supertype_id`.

**Panel B — signed group totals.** Use mirrored `log10(1 + count)` bars for the
three groups with completed contrasts, while printing the exact untransformed
count at every bar end:

| Group | Dementia-up | Dementia-down |
|---|---:|---:|
| `F_e33` | 249 | 6 |
| `F_e4` | 111 | 31 |
| `M_e33` | 7,697 | 14,098 |

**Result chips:**

- 260 completed contrasts;
- 24,404 FDR-significant feature–contrast hits;
- 22,192 also passed `abs(logFC) > log2(1.3)`;
- 74 completed contrasts had at least one parity-qualified hit; and
- 21,795 / 22,192 = 98.2% of parity hits occurred in `M_e33`.

### Interpretation guardrails

The plotted values are feature–contrast incidences, not unique genes. FDR was
controlled within each completed contrast. The broad pooled and broad
stratified DEG tiers did not enter the fine-run KDA denominator.

### Sources

- [`deg_summary.tsv`](../../../results/validation_human/08_deg/deg_summary.tsv)
- [`fine_direction_deg_summary.tsv`](../../../results/validation_human/08_deg/query_handoff/fine_direction_deg_summary.tsv)
- [`fine_contrast_status.tsv`](../../../results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv)

## 6. Figure 4 — query attrition and network availability

**Figure ID:** `seaad_query_attrition_and_availability`

**Deck use:** Slide 6

**Build mode:** editable native PowerPoint boxes, connectors, and count bars.

### Main message

The 1,548 planned signed directions were mostly unavailable or empty after the
mitochondrial and network-background gates; exactly 42 became KDA calls.

### Layout

**Panel A — exact-count branching diagram.** Use equal-height boxes and direct
counts rather than an area-scaled Sankey:

```text
1,548 structural signed directions
├── 1,028 source contrasts not estimable
└── 520 completed-source directions
    ├── 462 effective query size 0
    ├── 16 effective query size 1–2
    ├── 21 active query size 3–9
    └── 21 active query size ≥10
```

The final two branches converge on a `42 KDA calls` badge.

**Panel B — active calls by network and direction.** Use paired up/down bars or
a seven-row tile matrix:

| Network | Up | Down | Total |
|---|---:|---:|---:|
| Astrocytes | 1 | 0 | 1 |
| Excitatory neurons | 10 | 10 | 20 |
| Inhibitory neurons | 6 | 10 | 16 |
| Microglia | 1 | 0 | 1 |
| OPCs | 0 | 0 | 0 |
| Oligodendrocytes | 2 | 2 | 4 |
| Vasculature | 0 | 0 | 0 |

Add compact group chips: `40 M_e33`, `1 F_e33`, and `1 F_e4`.

### Interpretation guardrails

- `1,548` is not a run count.
- The executed primary analysis contains 42 calls, not 84.
- Lowering the KDA minimum from 10 to 3 admitted 21 additional small-query
  calls; it did not change DEG membership or create query genes.

### Sources

- [`query_attrition.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10a_inputs/query_attrition.tsv)
- [`seaad_kda_run_manifest.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv)

## 7. Figure 5 — KDA call outcomes and aggregation sequence

**Figure ID:** `seaad_kda_call_outcomes`

**Deck use:** Slide 7

### Main message

Twenty-nine of 42 KDA calls produced at least one significant return, mainly
in neuronal networks, but final drivers required recurrent cross-run evidence
and aggregate correction.

### Layout

**Panel A — network × direction outcomes.** Show a seven-network × two-direction
dot matrix. Each dot represents one completed call; filled navy dots indicate
a call with at least one significant return and open/light-gray dots indicate
a call with none. Print the row totals directly:

| Network/direction | With ≥1 significant return | With none |
|---|---:|---:|
| Astrocytes up | 0 | 1 |
| Excitatory up | 4 | 6 |
| Excitatory down | 10 | 0 |
| Inhibitory up | 4 | 2 |
| Inhibitory down | 8 | 2 |
| Microglia up | 0 | 1 |
| Oligodendrocytes up | 1 | 1 |
| Oligodendrocytes down | 2 | 0 |

Use up/down triangles in the row labels so direction is not represented by
color alone.

**Panel B — evidence-to-selection sequence.** Use a separate compact,
non-area-scaled sequence. Do not draw it as a funnel because the steps change
units from calls to return rows to aggregate candidate units:

```text
42 completed KDA calls
→ 29 with ≥1 significant return
→ 208 significant return rows
→ cross-run evidence for 38,788 aggregate candidate units
→ 13 units passed all gates and were displayed
```

Under the sequence, show the method ribbon:

```text
run BH → conservative support → coverage ≥0.80 → ACAT → network BH → class rank
```

### Required explanatory note

The signed core-MitoCarta DEG set is the KDA query. Candidate drivers are all
assessable genes in the induced broad network, which are subsequently
classified as MT or non-MT. A mitochondrial query can therefore identify a
non-MT driver.

### Sources

- [`run_qc.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10b_kda/run_qc.tsv)
- [`10b_kda/status.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv)
- [`10c_seaad_selection/status.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv)

## 8. Figure 6 — canonical MT driver circular figure

**Figure/package ID:** `seaad_two_case_circular`

**Deck use:** Slide 8

**Canonical asset:**
[`seaad_mt_driver_circular.png`](../../../results/figures/validation_human/seaad_two_case_circular/seaad_mt_driver_circular.png)

### Main message

SEA-AD selected eight MT network–gene units representing six genes, all in
Excitatory and Inhibitory networks; `MT-CO2` and `MT-CYB` recurred in both.

### Visible content

| Network | Rank order |
|---|---|
| Excitatory neurons | `MT-CO2`, `MT-CYB`, `MT-ND4`, `MT-ATP6` |
| Inhibitory neurons | `MT-CO2`, `MT-ND5`, `MT-CO3`, `MT-CYB` |

Retain:

- the fixed seven-network order and five slots per network;
- radial `-log10(aggregate q)` bars with a common cap of 15;
- the two recurrence curves for `MT-CO2` and `MT-CYB`;
- mtDNA markers; and
- distinct encodings for `no passing candidate` and `no included KDA run`.

Use this canonical figure without creating or maintaining a second circular
version. Give it the largest practical slide area and keep the note that the
curves show recurrence, not network edges. All eight selected units happen to
be mtDNA encoded, but the class remains the Phase 18 core-MitoCarta class.

## 9. Figure 7 — canonical non-MT driver circular figure

**Figure/package ID:** `seaad_two_case_circular`

**Deck use:** Slide 9

**Canonical asset:**
[`seaad_non_mt_driver_circular.png`](../../../results/figures/validation_human/seaad_two_case_circular/seaad_non_mt_driver_circular.png)

### Main message

SEA-AD selected five non-MT drivers across three networks; no selected non-MT
gene recurred across networks, and two networks had no runnable KDA evidence.

### Content to emphasize

Use the canonical circular figure without creating a dot-plot or second
circular rendering. In the spoken explanation, identify the five selected
genes and distinguish ranked, testable/no-passing, and no-included-run lists.

| Network | Gene | Aggregate q | Conservative supports |
|---|---|---:|---:|
| Excitatory neurons | `HGSNAT` | 0.00218 | 7 |
| Inhibitory neurons | `BEX3` | 0.00185 | 1 |
| Inhibitory neurons | `RPS27A` | 0.00264 | 2 |
| Inhibitory neurons | `RPL30` | 0.0441 | 1 |
| Oligodendrocytes | `KANSL1L` | 0.0451 | 1 |

The circular figure already preserves all seven list states: ranked lists in
Excitatory, Inhibitory, and Oligodendrocytes; testable/no-passing lists in
Astrocytes and Microglia; and no-included-run lists in OPCs and Vasculature.
Top five remains a maximum with no backfill.

### Sources

- [`seaad_top5.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv)
- [`seaad_list_status.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_list_status.tsv)

## 10. Figure 8 — ROSMAP-unit testability in SEA-AD

**Figure ID:** `seaad_rosmap_testability`

**Deck use:** Slide 10

**Build mode:** editable native PowerPoint count flows and availability strip.

### Main message

Only 36 of the 47 frozen ROSMAP selected units had an assessable matching
network/class unit in SEA-AD; the other 11 came from OPC or Vasculature, where
SEA-AD had no included KDA run.

### Layout

**Panel A — class-specific denominator and overlap.** For each class, draw the
ROSMAP denominator chain first, then place the independently selected SEA-AD
list in a separate box. Join the testable ROSMAP and SEA-AD boxes only through
a small shared-unit bridge; do not imply that the SEA-AD list was derived from
the ROSMAP list.

| Driver class | ROSMAP selected | Testable in SEA-AD | Not testable | SEA-AD selected | Strict shared |
|---|---:|---:|---:|---:|---:|
| MT | 26 | 19 | 7 | 8 | 6 |
| Non-MT | 21 | 17 | 4 | 5 | 0 |
| Total | 47 | 36 | 11 | 13 | 6 |

The flow from `47` must visibly split into `36 testable` and `11 not testable`
before any overlap result is shown.

**Panel B — seven-network availability strip.** For each network, display the
number of included SEA-AD KDA calls and the fate of ROSMAP selected units:

| Network | SEA-AD KDA calls | Untestable ROSMAP units |
|---|---:|---:|
| Astrocytes | 1 | 0 |
| Excitatory neurons | 20 | 0 |
| Inhibitory neurons | 16 | 0 |
| Microglia | 1 | 0 |
| OPCs | 0 | 7: 3 MT + 4 non-MT |
| Oligodendrocytes | 4 | 0 |
| Vasculature | 0 | 4 MT |

Use a dashed/crossed state for OPC and Vasculature. Do not encode them as
negative replication results.

### Sources

- [`phase18_selected_candidate_units.tsv`](../../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv)
- [`seaad_kda_run_manifest.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv)
- [`rosmap_seaad_candidate_overlap.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv)

## 11. Figure 9 — strict network-aware overlap and paired ranks

**Figure ID:** `seaad_rosmap_strict_overlap_ranks`

**Deck use:** Slide 11

### Main message

All six strict rediscoveries were neuronal MT units; Inhibitory MT showed the
strongest recurrence, with all four SEA-AD selected units also appearing in
the ROSMAP top five for the same network and class.

### Layout

**Panel A — endpoint scorecard.** Use two class rows:

```text
MT:     19 ROSMAP units testable | 8 SEA-AD selected | 6 strict shared
non-MT: 17 ROSMAP units testable | 5 SEA-AD selected | 0 strict shared
```

**Panel B — paired ranks.** Use separate Excitatory and Inhibitory slopegraph
facets. ROSMAP ranks are on the orange left axis and SEA-AD ranks on the teal
right axis. Navy lines identify strict matches. Show unmatched top-list
endpoints in light gray so the audience sees the full selected lists rather
than only the successful pairs.

| Network | Gene | ROSMAP rank | SEA-AD rank |
|---|---|---:|---:|
| Excitatory neurons | `MT-CO2` | 1 | 1 |
| Excitatory neurons | `MT-CYB` | 5 | 2 |
| Inhibitory neurons | `MT-CO2` | 1 | 1 |
| Inhibitory neurons | `MT-CO3` | 2 | 3 |
| Inhibitory neurons | `MT-CYB` | 3 | 4 |
| Inhibitory neurons | `MT-ND5` | 4 | 2 |

The unmatched endpoints are:

- Excitatory ROSMAP: `UQCR10` rank 2, `COX4I1` rank 3, and `COX6B1` rank 4;
- Excitatory SEA-AD: `MT-ND4` rank 3 and `MT-ATP6` rank 4; and
- Inhibitory ROSMAP: `COX7C` rank 5.

Add direct network summaries beneath the facets:

- Excitatory MT: shared 2; Jaccard 0.286; nominal overlap
  p = 2.33 × 10^-4;
- Inhibitory MT: shared 4; Jaccard 0.800; nominal overlap
  p = 1.22 × 10^-9.

Top result chips may show `6 / 13 SEA-AD units shared` and `6 / 36 testable
ROSMAP units recovered`, but must also state `6 strict units = 4 unique strict
symbols`.

### Interpretation guardrails

The p-values are nominal, per-list hypergeometric tests. Do not add stars or
imply correction across lists. The slopegraph shows selection-rank agreement,
not effect-size agreement or causal direction.

### Sources

- [`rosmap_seaad_candidate_overlap.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv)
- [`rosmap_seaad_overlap_summary.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_overlap_summary.tsv)

## 12. Figure 10 — descriptive gene-level overlap

**Figure ID:** `seaad_rosmap_top_driver_gene_overlap_slide`

**Deck use:** Slide 12

**Source asset:** validated
[`seaad_rosmap_top_driver_gene_venn`](../../../results/figures/validation_human/seaad_rosmap_top_driver_gene_venn)

### Main message

After broad-network identity is collapsed, all six SEA-AD MT genes appear
somewhere in the ROSMAP MT set, whereas the two non-MT gene sets are disjoint.

### Layout

Use two titleless Euler/Venn panels with the deck-wide cohort colors.

**MT panel:** SEA-AD is fully contained within ROSMAP.

- ROSMAP only: 4 — `COX4I1`, `COX6B1`, `COX7C`, `UQCR10`;
- common: 6 — `MT-ATP6`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND4`, `MT-ND5`;
- SEA-AD only: 0.

**Non-MT panel:** the two circles are disjoint.

- ROSMAP only: 15 — `ANKRD11`, `APOE`, `ATP6V1F`, `DYNLT1`, `FTL`,
  `LAMTOR5`, `LAPTM4A`, `NCOA1`, `RPL11`, `RPL15`, `RPL38`, `RPLP1`,
  `RPS13`, `RPS15`, `SELENOW`;
- common: 0;
- SEA-AD only: 5 — `BEX3`, `HGSNAT`, `KANSL1L`, `RPL30`, `RPS27A`.

Use ROSMAP orange outline/hatch and SEA-AD teal solid fill. Directly label all
regions, including both empty regions. Gene lists may be placed in
leader-linked callout blocks outside the circles to maintain 16-pt text.

### Required note

Label the asset `descriptive gene-level view; network identity collapsed`.
`MT-ATP6` and `MT-ND4` are common only in this gene-level view because they
were selected in different broad networks across cohorts. Daggers on
`ANKRD11`, `FTL`, and `NCOA1` indicate genes selected only in ROSMAP OPC, for
which SEA-AD had no included OPC run.

Do not show a gene-level overlap p-value.

## 13. Figure 11 — why the non-MT lists are disjoint

**Figure ID:** `seaad_rosmap_non_mt_diagnostic`

**Deck use:** Slide 13

**Build mode:** validated external figure package containing a fate tree,
reverse-lookup table, and coverage ribbon.

**Canonical package:**
[`seaad_rosmap_non_mt_diagnostic`](../../../results/figures/validation_human/seaad_rosmap_non_mt_diagnostic)

### Main message

The zero non-MT intersection is a final selected-list result. Most ROSMAP
non-MT units were assessable in SEA-AD, but support was sparse and none passed
SEA-AD cross-run aggregation; conversely, several SEA-AD non-MT genes had some
ROSMAP evidence but none passed the ROSMAP final gates.

### Layout

Use a two-panel explanatory figure.

**Panel A — fate of the 21 ROSMAP non-MT selected units in SEA-AD.** Use a
plain branching diagram:

```text
21 ROSMAP selected non-MT network–gene units
├── 4 OPC units not testable in SEA-AD
└── 17 assessable in SEA-AD
    ├── 13 had no qualifying SEA-AD supporting run
    └── 4 had one qualifying SEA-AD supporting run
        └── 0 passed aggregate SEA-AD selection
```

Name the four units with one SEA-AD supporting run in a small callout:
`DYNLT1` in Excitatory and `RPS15`, `RPLP1`, and `RPL38` in Inhibitory.

**Panel B — where the five SEA-AD non-MT drivers appear in ROSMAP.** Use a
five-row evidence table rather than another Venn:

| SEA-AD selected unit | ROSMAP evidence in the matching network | ROSMAP final result |
|---|---|---|
| Excitatory `HGSNAT` | some included-run support | exploratory; aggregate q = 0.641 |
| Inhibitory `BEX3` | multiple included-run supports | exploratory; aggregate q = 0.157 |
| Inhibitory `RPS27A` | included-run support | exploratory; aggregate q = 1.000 |
| Inhibitory `RPL30` | significant returns only in excluded size-3 runs; no conservative support in the included scope | exploratory; aggregate q = 1.000 |
| Oligodendrocyte `KANSL1L` | no explicit primary ROSMAP candidate return | not selected |

Use plain-language status labels such as `some run evidence, aggregate gate
not passed` rather than requiring the audience to interpret q-values alone.

**Coverage ribbon:**

```text
ROSMAP: 161 included runs across six groups
SEA-AD: 42 calls; 40 were M_e33; three groups could not be estimated
```

The ribbon should say that SEA-AD lacked enough independent donors in several
sex/APOE disease arms. It must not imply that the 17 assessable units were
untestable or that missing strata are the sole explanation.

### Interpretation guardrails

- Zero overlap occurred before the top-five display cap; it is not a ranking
  truncation artifact.
- `Not selected` does not mean absent from the network or biologically
  disproved.
- More nuclei from the same donors cannot replace missing independent donors.
- Do not label the four OPC units as failures.

### Sources

- [`rosmap_seaad_candidate_overlap.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv)
- [`seaad_kda_significant_returns.tsv`](../../../results/validation_human/10_seaad_kda_rediscovery/10b_kda/seaad_kda_significant_returns.tsv)
- [`call_key_driver_returns.tsv`](../../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)
- [`seaad_rosmap_non_mt_key_driver_overlap_explanation.md`](../../validation_human/seaad_rosmap_non_mt_key_driver_overlap_explanation.md)

## 14. Slide-native visuals that do not need figure packages

### Opening result chips

Slide 1 should show four editable chips:

```text
42 SEA-AD KDA calls
13 selected units / 11 genes
36 of 47 ROSMAP units testable
6 strict shared units, all MT
```

Add `6 strict units = 4 strict-match symbols` in the speaker notes or a small
qualifier.

### Cohort and taxonomy overview

Slide 3 should use editable shapes for:

- 83 source donors → exclude 2 APOE2/4 and 3 neurotypical-reference donors →
  78 analysis donors;
- 37 Dementia and 41 No-dementia donors;
- 1,189,172 selected nuclei; and
- 129 supertypes mapped to seven matching broad networks:
  Astrocytes 6, Excitatory 41, Inhibitory 67, Microglia 4, OPCs 3,
  Oligodendrocytes 4, and Vasculature 4.

These shapes define the cohort; they are not a pseudobulk-QC figure.

### Closing summary

Slide 14 should use three editable columns:

- `Supported`: focused neuronal MT rediscovery;
- `Not established`: non-MT replication, causal direction, or conclusions for
  untestable networks/groups; and
- `Next analyses`: separately frozen sensitivities and additional cohorts.

## 15. Automated validation across the figure suite

At minimum, automated checks should verify:

1. all required phase statuses are `validated_complete`;
2. registered source tables match their recorded SHA-256 values;
3. the exact ordered six groups and seven shared networks are preserved;
4. 129 × 6 = 774 contrasts and 774 × 2 = 1,548 direction slots;
5. 260 completed + 514 not estimable = 774;
6. 1,028 + 462 + 16 + 21 + 21 = 1,548;
7. 42 active calls = 20 up + 22 down = 21 small + 21 size-at-least-10;
8. 42 calls = 29 with at least one significant return + 13 with none;
9. the SEA-AD display contains exactly 13 ranked units: 8 MT and 5 non-MT,
   representing 11 genes;
10. ROSMAP contains 47 selected units; 36 are testable and 11 are not;
11. the six strict shared units and their paired ranks match the frozen table;
12. six strict units resolve to four unique strict-match symbols;
13. gene-level partitions are MT 4/6/0 and non-MT 15/0/5;
14. all visible gene labels are present as searchable SVG text;
15. no figure reports 84 executed calls, labels a not-testable unit a failure,
    or calls the gene-level Venn the primary endpoint;
16. PNG dimensions/DPI, PDF signatures, SVG vector/text preservation, font
    sizes, clipping, and output hashes pass; and
17. no renderer requires a VH05 or VH06 input.

Manual review must be completed at intended slide size in color and grayscale.
The reviewer should specifically check that small labels remain readable,
status hatches remain distinct, paired-rank lines do not cross gene labels,
and the strict and gene-only overlap figures cannot be mistaken for one
another.

## 16. External-figure completion record

| Figure ID | Renderer | Test | Package checks |
|---|---|---|---:|
| `seaad_fine_deg_landscape` | `plot_seaad_fine_deg_landscape.py` | `test_seaad_fine_deg_landscape.py` | 26 / 26 |
| `seaad_kda_call_outcomes` | `plot_seaad_kda_call_outcomes.py` | `test_seaad_kda_call_outcomes.py` | 26 / 26 |
| `seaad_two_case_circular` | `plot_seaad_two_case_circular.py` | `test_seaad_two_case_circular.py` | 45 / 45 |
| `seaad_rosmap_strict_overlap_ranks` | `plot_seaad_rosmap_overlap_slide_figures.py` | `test_seaad_rosmap_overlap_slide_figures.py` | 25 / 25 |
| `seaad_rosmap_top_driver_gene_overlap_slide` | `plot_seaad_rosmap_overlap_slide_figures.py` | `test_seaad_rosmap_overlap_slide_figures.py` | 25 / 25 |
| `seaad_rosmap_non_mt_diagnostic` | `plot_seaad_rosmap_non_mt_diagnostic.py` | `test_seaad_rosmap_non_mt_diagnostic.py` | 39 / 39 |

All completed packages have `validation_status = validated_complete`,
`visual_review_status = complete`, zero failed or pending checks, 450-DPI PNGs,
and SVG/PDF companions. The canonical two-case circular package uses its
original 12 × 7.2-inch canvas; no slide-specific duplicate is retained.

## 17. Deliberately excluded figures

The following are not needed for this presentation and should not block deck
construction:

- pseudobulk PCA or MDS;
- library-size, detected-gene, or mitochondrial-fraction QC;
- VH05 fine-to-broad count-reconciliation plots;
- per-contrast volcano plots;
- a 260-contrast top-DEG heatmap requiring the absent tested-result shards;
- full candidate-q distributions requiring absent audit intermediates; and
- new query-member network diagrams.

If those become scientifically necessary later, they should receive separate
plans and restored source artifacts rather than being inferred from the compact
summary tables.

## 18. Definition of done

The external presentation figure set is complete because:

- all six agreed separate analytical figures are implemented as validated
  packages;
- the original detailed setup, circular, and Venn figures remain available for
  appendix use;
- every visible count and gene identity is loaded from a registered source,
  not hard-coded in the renderer;
- each figure communicates one conclusion at projection distance;
- no figure depends on VH05 or VH06;
- all external-figure automated checks pass; and
- manual review confirmed readable labels and accurate scientific boundaries
  in both color and grayscale.

The full presentation remains pending until the native slide compositions are
built and the assembled PowerPoint passes its own layout and provenance checks.
