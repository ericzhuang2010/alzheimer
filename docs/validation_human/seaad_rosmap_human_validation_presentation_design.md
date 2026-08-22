# SEA-AD–ROSMAP human-validation presentation design

**Status:** implemented and validated; PowerPoint assembled on 2026-08-22

**PowerPoint:**
[`seaad_rosmap_human_validation.pptx`](../presentations/seaad_rosmap_human_validation.pptx)

**Default format:** 9 main slides, 10–12 minutes, 16:9 widescreen

**Audience:** scientific collaborators who understand DEG and KDA at a high level

**Deck title:** *Cross-cohort rediscovery of ROSMAP key drivers in SEA-AD*

**One-sentence message:** independent SEA-AD expression evidence supports a
focused neuronal mitochondrial signal seen in ROSMAP, while broader and
non-MT replication remains limited.

The detailed technical figure plan remains available in
[`seaad_rosmap_human_validation_presentation_figures_plan.md`](../figures/validation_human/seaad_rosmap_human_validation_presentation_figures_plan.md).
That document remains the asset-construction reference; the simpler nine-slide
sequence and slide assignments in this design supersede its earlier storyboard.

## 1. Keep the deck simple

- One conclusion per slide.
- One main visual per slide.
- Use no more than three slide-native number callouts outside a validated
  figure.
- Put formulas, thresholds, full tables, and audit details in the appendix.
- Use plain language first; define technical terms only when they are needed.
- Do not repeat numbers already printed inside a figure.
- Use the existing canonical MT and non-MT circular figures. Do not create
  additional versions.

The audience should be able to retell the story as:

1. SEA-AD provided independent expression evidence.
2. Donor coverage limited how many mitochondrial DEG queries could be tested.
3. SEA-AD recovered a focused neuronal MT signal from ROSMAP.
4. The non-MT lists did not overlap, but this is not evidence that the genes
   are biologically absent.

## 2. Main deck

### Slide 1 — SEA-AD independently recovers a focused neuronal mitochondrial signal from ROSMAP

**Purpose:** give the result before explaining the workflow.

**Layout:** title, one-sentence subtitle, and two large result chips.

**Subtitle:** independent SEA-AD expression evidence analyzed on a shared,
frozen network/KDA scaffold.

**Show only:**

- `13 SEA-AD selected units`
- `6 same-network MitoCarta-class (MT) matches`

**What to say:** SEA-AD did not reproduce every ROSMAP driver. It recovered a
small, coherent neuronal mitochondrial subset.

**Boundary:** a selected unit is a broad network + gene + driver class. The
same gene can therefore count in more than one network.

---

### Slide 2 — SEA-AD evidence was independent; the network and KDA rules were shared

**Purpose:** explain the setup and prevent the impression that known ROSMAP
genes were simply rescored.

**Visual:** a simple four-step native workflow:

```text
SEA-AD donors
    → donor-level expression and signed mitochondrial DEG queries
    → KDA on the matching frozen broad network
    → freeze the SEA-AD list, then compare with ROSMAP
```

Add two small labels:

- `78 donors`
- `129 fine supertypes × 6 sex/APOE groups`

**What to say:** the donors, expression data, DEG results, and queries came
from SEA-AD. The broad networks and KDA/selection machinery were deliberately
held fixed so the result could be compared with ROSMAP Phase 18.

**Boundary:** this is independent expression evidence on a shared scaffold,
not an independent reconstruction of the networks.

**Detailed appendix asset:**
[`seaad_rosmap_validation_setup.png`](../../results/figures/validation_human/seaad_rosmap_validation_setup/seaad_rosmap_validation_setup.png)

---

### Slide 3 — Only 42 directions produced mitochondrial gene sets large enough for KDA

**Purpose:** explain why the executed analysis is much smaller than the
planned grid.

**Visual:** one horizontal funnel with three boxes:

```text
1,548 planned cell-type × group × direction combinations
    → 520 directions from completed DEG contrasts
    → 42 mitochondrial gene sets large enough for KDA
```

**Small note:** only three of six sex/APOE groups contributed estimable fine
contrasts. Independent donors determined contrast estimability; more nuclei
from the same donors do not add biological replicates.

**What to say:** a planned comparison is not the same as an executed KDA call.
Donor support reduced the design to 520 completed directions; most remaining
directions did not contain enough mitochondrial genes for KDA.

**Do not show here:** exact donor-arm counts, the full 129-supertype heatmap,
query-size bins, or the complete selection formula.

**Sources:**
[`fine_contrast_status.tsv`](../../results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv),
[`query_attrition.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10a_inputs/query_attrition.tsv), and
[`10c_seaad_selection/status.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv).

---

### Slide 4 — SEA-AD MT drivers concentrate in excitatory and inhibitory neurons

**Purpose:** show the positive SEA-AD driver result.

**Visual:** use the canonical figure nearly full slide:
[`seaad_mt_driver_circular.png`](../../results/figures/validation_human/seaad_two_case_circular/seaad_mt_driver_circular.png).

Do not add a second table or legend. Add at most one short footer:

> MT-CO2 and MT-CYB recur in both neuronal networks.

**What to say:** SEA-AD selected eight MT network–gene units representing six
genes, all in Excitatory and Inhibitory networks.

**Boundary:** the center curves show recurrence of a gene across networks;
they are not network edges.

---

### Slide 5 — SEA-AD selected five non-MT drivers across three networks

**Purpose:** establish that SEA-AD produced non-MT candidates before discussing
the lack of cross-cohort overlap.

**Visual:** use the canonical figure nearly full slide:
[`seaad_non_mt_driver_circular.png`](../../results/figures/validation_human/seaad_two_case_circular/seaad_non_mt_driver_circular.png).

Add at most one short footer:

> Five genes were selected across Excitatory, Inhibitory, and Oligodendrocyte networks.

**What to say:** zero ROSMAP overlap does not mean SEA-AD found no non-MT
drivers. SEA-AD selected five; they were simply different from the final
ROSMAP non-MT list.

**Boundary:** `non-MT` means outside the frozen core-MitoCarta class. It does
not mean unrelated to mitochondria.

---

### Slide 6 — Six ROSMAP units reappear in the same neuronal network and driver class

**Purpose:** present the primary cross-cohort endpoint.

**Visual:**
[`seaad_rosmap_strict_overlap_ranks.png`](../../results/figures/validation_human/seaad_rosmap_strict_overlap_ranks/seaad_rosmap_strict_overlap_ranks.png).

**What to say:** the strict comparison requires the same broad network, the
same gene, and the same driver class. Six units pass that definition, all in
neuronal MT lists. Because two genes recur in both networks, the six units
represent four unique genes.

**Testability line:** `36 of 47 ROSMAP units were testable; 11 had no eligible
SEA-AD run.`

**Point to the figure's existing label:** `6 strict units = 4 genes, all MT`.

**Do not add:** precision, recall, Jaccard, or another table of p-values. The
figure already contains the supporting ranks.

**Boundary:** p-values printed in the figure are nominal per-list tests; they
are not corrected across lists.

---

### Slide 7 — Ignoring network, all six SEA-AD MT genes occur in ROSMAP; non-MT overlap is zero

**Purpose:** provide the requested gene-level Venn view.

**Visual:**
[`seaad_rosmap_top_driver_gene_overlap_slide.png`](../../results/figures/validation_human/seaad_rosmap_top_driver_gene_overlap_slide/seaad_rosmap_top_driver_gene_overlap_slide.png).

**What to say:** after counting each gene once regardless of network, the six
SEA-AD MT genes all occur somewhere in the ROSMAP list. The non-MT gene sets
are disjoint.

**Boundary:** this is a secondary descriptive view. The primary result is the
same-network comparison on Slide 6. No gene-level overlap p-value should be
reported.

---

### Slide 8 — Zero non-MT overlap does not mean the biology is absent

**Purpose:** explain the negative result in plain language.

**Visual:**
[`seaad_rosmap_non_mt_diagnostic.png`](../../results/figures/validation_human/seaad_rosmap_non_mt_diagnostic/seaad_rosmap_non_mt_diagnostic.png).

**What to say:** four ROSMAP non-MT units were not testable because SEA-AD had
no eligible OPC run. Seventeen were testable, but only four had a run that met
the support gate and none passed final selection across runs.

Within each of three sex/APOE groups, SEA-AD had fewer than five independent
donors in at least one disease arm. This reduced matching evidence, but it is
not claimed to be the sole explanation.

**Boundary:** `not selected` does not mean absent from the network or
biologically disproved. The zero overlap occurred before the top-five display
cap.

---

### Slide 9 — SEA-AD supports a focused neuronal MT signal; broader validation remains incomplete

**Purpose:** end with a restrained conclusion.

**Layout:** three simple cards, with no additional plots.

| Supported | Not established | Next step |
|---|---|---|
| Same-network neuronal MT rediscovery | Replication of the non-MT list or untestable groups | Add donor coverage and test additional independent cohorts/networks |

**What to say:** the strongest result is a focused neuronal MT signal. The
analysis does not establish broad replication of every ROSMAP driver, and KDA
prioritization alone does not prove causality.

## 3. Appendix

Keep the appendix available for questions, but do not walk through it unless
requested.

### A1 — Detailed validation setup and donor support

Use the detailed
[`seaad_rosmap_validation_setup.png`](../../results/figures/validation_human/seaad_rosmap_validation_setup/seaad_rosmap_validation_setup.png)
only as an appendix reference.

- cohort exclusions and the 78-donor composition;
- exact disease-arm counts for all six sex/APOE groups; and
- reminder that biological replication is donor-level.

### A2 — Fine-supertype DEG landscape

Use
[`seaad_fine_deg_landscape.png`](../../results/figures/validation_human/seaad_fine_deg_landscape/seaad_fine_deg_landscape.png).

Explain only if asked that the plotted counts are feature-by-contrast
incidences, not unique genes.

### A3 — KDA call outcomes

Use
[`seaad_kda_call_outcomes.png`](../../results/figures/validation_human/seaad_kda_call_outcomes/seaad_kda_call_outcomes.png).

This slide can explain the difference between a run with a significant return
and a driver that passes final across-run selection.

### A4 — Query and selection rules

Keep the technical rules on one appendix slide:

- signed core-MitoCarta DEG query;
- SEA-AD minimum effective query size 3 versus ROSMAP minimum 10;
- within-run support, cross-run coverage, ACAT, and BH correction; and
- maximum five displayed genes per network/class list, with no backfill.

Exact formulas and implementation details remain in the analysis documents,
not in the main deck.

### A5 — Full selected-driver and testability tables

Include the 13 SEA-AD selected units, all ROSMAP selected-unit fates, and the
three list states:

- selected/ranked;
- tested but no candidate passed; and
- not testable because no eligible run existed.

### A6 — Provenance and limitations

- all inputs used by the deck must come from validated result or figure
  packages;
- no optional sensitivity branch was executed;
- VH05/VH06 QC figures are not required for the claims in this deck; and
- compact transferred results do not support new volcano plots or complete
  candidate-q distribution plots.

## 4. Plain-language terminology

| Use on slides | Meaning |
|---|---|
| planned comparison | one fine cell type × group × direction combination |
| KDA call | one query that was large enough and actually executed |
| selected unit | broad network + gene + driver class |
| strict match | the same network, gene, and class in both cohorts |
| gene-level overlap | the same gene anywhere, with network ignored |
| not testable | no matching eligible SEA-AD run existed |
| tested but not selected | evidence was evaluated but did not pass final selection |

Define once in speech:

- `MT driver` means the frozen core-MitoCarta class, not necessarily an
  mtDNA-encoded gene.
- `non-MT driver` means outside that class, not unrelated to mitochondria.
- SEA-AD compares `Dementia` with `No dementia`; ROSMAP compares `AD` with
  `NCI`.

## 5. Visual and speaking rules

- Use 16:9 slides with a white or very light background.
- Use a 30–34 pt conclusion title and at least 20 pt slide-native body text.
- Put one figure nearly full width; never pair the two circular figures on one
  slide.
- Use SEA-AD teal, ROSMAP orange, and navy for shared results. Keep text labels
  and line styles so interpretation does not depend on color.
- Do not add new result chips beside figures that already display the result.
- Keep source lines small but readable and keep explanatory text in speaker
  notes.

For each slide, speaker notes need only three short sections:

1. `What to point at`
2. `Main takeaway`
3. `Boundary / transition`

## 6. Essential interpretation guardrails

- Say `independent SEA-AD expression evidence on a shared frozen scaffold`.
- Do not claim an independent SEA-AD network reconstruction.
- Do not call 1,548 planned comparisons 1,548 KDA calls; exactly 42 calls ran.
- Do not report 84 calls or describe an unexecuted sensitivity as completed.
- Do not call the 11 untestable ROSMAP units negative replications.
- Keep `6 strict units = 4 genes` separate from `6 shared MT genes` in the
  network-collapsed Venn.
- Derive the four strict-match genes from the six strict shared rows, not from
  the network-collapsed `shared_unique_genes` field.
- Do not interpret zero non-MT overlap as proof of absent biology.
- Do not present KDA prioritization as causal proof.

## 7. Build and review

The final deck should:

- contain exactly 9 main slides in the order above;
- use the canonical circular package and the validated strict-overlap,
  gene-overlap, and non-MT diagnostic packages;
- draw only Slides 1–3 and 9 with editable PowerPoint shapes;
- embed figures with contain/no-crop placement;
- include a source line and short speaker notes on every scientific slide;
- load visible numbers from validated source tables rather than hard-coding
  them; and
- be reviewed at projection size in color and grayscale.

Before delivery, verify that the deck contains no stale paths, placeholder
text, `84 calls`, `six unique strict genes`, or wording that treats an
untestable unit as a failed replication.

## 8. Completion record

- Delivered 9 main slides plus 6 appendix slides in 16:9 PowerPoint format.
- Kept the canonical MT and non-MT circular figures as the only circle assets.
- Added speaker notes, alt text, source lines, and editable native diagrams.
- Validated the PPTX structure and scientific denominators, then reviewed a
  Microsoft PowerPoint export slide-by-slide in color and grayscale.
- Reproducible builder:
  [`build_seaad_rosmap_human_validation_deck.py`](../../scripts/presentations/build_seaad_rosmap_human_validation_deck.py).
- Validation report:
  [`seaad_rosmap_human_validation_status.tsv`](../../results/presentations/validation_human/seaad_rosmap_human_validation/seaad_rosmap_human_validation_status.tsv).
