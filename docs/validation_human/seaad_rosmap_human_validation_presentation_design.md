# SEA-AD–ROSMAP human-validation presentation design

**Status:** refresh specification for the 2026-08-23 SEA-AD rerun

**PowerPoint:**
[seaad_rosmap_human_validation_08252026.pptx](../presentations/seaad_rosmap_human_validation_08252026.pptx)

**Format:** 15 slides in the existing order: 9 main slides and 6 appendix
slides. No slide is added, removed, or rearranged.

**Audience:** scientific collaborators who understand DEG and KDA at a high
level.

**Deck title:** *Cross-cohort rediscovery of ROSMAP key drivers in SEA-AD*

**Main message:** the exploratory SEA-AD rerun supports a focused neuronal
mitochondrial signal from ROSMAP, while non-MT overlap remains absent.

## Analysis contract shown in the deck

This is a **post-hoc exploratory rerun**, not the original prespecified
analysis. It uses:

- at least 3 donors in each disease arm;
- signed core-MitoCarta DEG queries with FDR `< 0.05` and no fold-change
  cutoff;
- minimum effective query size 3;
- candidate coverage `>= 0.80`;
- aggregate ACAT BH q `<= 0.05`; and
- at least one conservative supporting run.

SEA-AD contributes independent donor-level expression evidence. The broad
networks and KDA/selection machinery are shared with ROSMAP; this is not an
independent SEA-AD network reconstruction.

## Main slides

### Slide 1 — SEA-AD recovers a focused neuronal mitochondrial signal

Show two result chips:

- `11 SEA-AD selected units (9 genes)`
- `6 strict ROSMAP matches (4 genes), all MT`

Say that the same gene can count as more than one unit when it appears in more
than one broad network. Add a small `Post-hoc exploratory rerun` label.

### Slide 2 — SEA-AD evidence was independent; the scaffold was shared

Keep the four-step workflow:

```text
SEA-AD donors
    -> donor-level DEG contrasts and signed mitochondrial queries
    -> KDA on the matching frozen broad network
    -> freeze the SEA-AD list
    -> compare with frozen ROSMAP results
```

Retain the `78 donors` and `129 fine supertypes × 6 sex/APOE groups` labels.
State briefly that the donor threshold and DEG query definition were amended
for this exploratory rerun. Do not describe the rerun as blinded or
prespecified.

### Slide 3 — Donor support and query size reduce the planned grid to 42 KDA calls

Use one simple funnel:

```text
1,548 planned cell-type × group × direction combinations
    -> 762 directions from 381 completed DEG contrasts
    -> 42 mitochondrial gene sets large enough for KDA
```

Four sex/APOE groups contributed completed contrasts: `F_e33`, `F_e4`,
`M_e33`, and `M_e4`. `F_e2` and `M_e2` did not have adequate donor
support. Emphasize that donors, not nuclei, determine biological replication.

### Slide 4 — MT drivers concentrate in excitatory and inhibitory neurons

Use the refreshed canonical figure:
[seaad_mt_driver_circular.png](../../results/figures/validation_human/seaad_two_case_circular/seaad_mt_driver_circular.png).

Main point: SEA-AD selected 8 MT units representing 6 genes, all in the
Excitatory and Inhibitory networks. `MT-CO2` and `MT-CYB` recur in both
networks. Center curves show recurrence, not network edges.

### Slide 5 — SEA-AD selected three non-MT drivers across two neuronal networks

Use the refreshed canonical figure:
[seaad_non_mt_driver_circular.png](../../results/figures/validation_human/seaad_two_case_circular/seaad_non_mt_driver_circular.png).

Show the three genes only:

- Excitatory: `HGSNAT`
- Inhibitory: `BEX3`, `RPS27A`

Explain that zero ROSMAP overlap does not mean SEA-AD found no non-MT
drivers. `Non-MT` means outside the frozen core-MitoCarta class, not unrelated
to mitochondria.

### Slide 6 — Six ROSMAP units reappear in the same network and driver class

Use:
[seaad_rosmap_strict_overlap_ranks.png](../../results/figures/validation_human/seaad_rosmap_strict_overlap_ranks/seaad_rosmap_strict_overlap_ranks.png).

The strict endpoint requires the same broad network, gene, and driver class.
Report:

- `36 of 47 ROSMAP units were testable in SEA-AD`;
- `6 strict units = 4 genes`; and
- all strict matches are neuronal MT drivers.

Qualify this as the strict comparison within the exploratory rerun. Any
p-values printed in the figure are nominal per-list tests.

### Slide 7 — Gene-level overlap is complete for SEA-AD MT genes and zero for non-MT

Use:
[seaad_rosmap_top_driver_gene_overlap_slide.png](../../results/figures/validation_human/seaad_rosmap_top_driver_gene_overlap_slide/seaad_rosmap_top_driver_gene_overlap_slide.png).

At the network-collapsed gene level:

- MT: 4 ROSMAP-only, 6 shared, 0 SEA-AD-only;
- non-MT: 15 ROSMAP-only, 0 shared, 3 SEA-AD-only.

Present this as a secondary descriptive view. The primary result is the
same-network comparison on Slide 6.

### Slide 8 — Zero non-MT overlap reflects limited qualifying evidence, not proof of absence

Use:
[seaad_rosmap_non_mt_diagnostic.png](../../results/figures/validation_human/seaad_rosmap_non_mt_diagnostic/seaad_rosmap_non_mt_diagnostic.png).

Explain the ROSMAP non-MT fate in plain language:

```text
21 ROSMAP non-MT units
    -> 4 not testable because no eligible SEA-AD OPC run existed
    -> 17 assessable
         -> 14 had no qualifying significant return
         -> 3 had one qualifying return
    -> 0 passed final across-run selection
```

The three one-return genes were `DYNLT1`, `RPS15`, and `RPL38`. A single
return was insufficient to satisfy the final coverage, aggregate-q, and
support rules. Do not describe an unselected or untestable gene as
biologically absent.

### Slide 9 — SEA-AD supports a focused neuronal MT signal; broader validation remains incomplete

Keep the three-card conclusion:

| Supported | Not established | Next step |
|---|---|---|
| Same-network neuronal MT rediscovery | Replication of the non-MT list or untestable groups | Add donor coverage and test other independent cohorts/networks |

State that this is post-hoc exploratory evidence. KDA prioritization does not
establish causality.

## Appendix slides

### Slide 10 — Detailed validation setup

Use the refreshed
[seaad_rosmap_validation_setup.png](../../results/figures/validation_human/seaad_rosmap_validation_setup/seaad_rosmap_validation_setup.png).

The figure should carry the amended donor/FDR-only setup and the current
sequence: 381 completed contrasts, 762 directions, 42 KDA calls, and 11
selected units representing 9 genes.

### Slide 11 — Fine-supertype DEG landscape

Use
[seaad_fine_deg_landscape.png](../../results/figures/validation_human/seaad_fine_deg_landscape/seaad_fine_deg_landscape.png).

Explain only if asked:

- 381 of 774 contrasts completed;
- the active FDR-only query produced 24,423 DEG feature-by-contrast
  incidences across 85 contrasts with signal; and
- the 1.3-fold count is an auxiliary reference, not an active gate.

Feature-by-contrast incidences are not unique genes.

### Slide 12 — KDA call outcomes

Use
[seaad_kda_call_outcomes.png](../../results/figures/validation_human/seaad_kda_call_outcomes/seaad_kda_call_outcomes.png).

Report 42 calls: 27 returned at least one significant driver and 15 did not.
The significant-return table contains 201 rows. Final selection retained 11
units representing 9 genes.

### Slide 13 — Query and selection rules

Show the current rules in one compact sequence:

```text
donors >=3/arm
    -> signed core-MitoCarta genes with FDR <0.05
    -> effective query size >=3
    -> coverage >=0.80
    -> aggregate q <=0.05 + at least one conservative supporting run
    -> display at most 5 passing genes per network/class; no backfill
```

State explicitly that there is no active fold-change cutoff.

### Slide 14 — Selected drivers and ROSMAP testability

List the 11 SEA-AD units (9 genes) and the ROSMAP unit fates. For the 14 broad
network/class lists, show the three states:

- 4 lists with ranked SEA-AD selections;
- 6 tested lists with no passing candidate; and
- 4 lists with no eligible run.

Do not force five displayed genes when fewer than five pass.

### Slide 15 — Provenance and limitations

State that:

- this is the post-hoc donor-3/FDR-only exploratory rerun;
- coverage `>=0.80` and aggregate q `<=0.05` remained active;
- validated SEA-AD result and figure packages are the deck sources;
- frozen ROSMAP results were unchanged; and
- compact transferred results do not support new volcano plots or complete
  candidate-q distribution plots.

## Plain-language terms

| Slide term | Meaning |
|---|---|
| planned direction | one fine cell type × group × DEG direction |
| KDA call | one signed query large enough to execute |
| selected unit | broad network + gene + driver class |
| strict match | same network, gene, and class in both cohorts |
| gene-level overlap | same gene after ignoring network |
| not testable | no matching eligible SEA-AD run existed |
| tested but not selected | evidence was evaluated but did not pass final selection |

SEA-AD compares `Dementia` with `No dementia`; ROSMAP compares `AD` with
`NCI`.

## Build and review requirements

- Preserve the existing 15-slide structure and slide order.
- Replace the eight embedded figures on Slides 4–8 and 10–12 with the
  refreshed canonical PNGs, retaining contain/no-crop placement.
- Update slide-native numbers, speaker notes, alt text, and source lines.
- Keep one conclusion and one main visual per slide.
- Label the result as post-hoc exploratory wherever the interpretation could
  otherwise imply a prespecified confirmatory analysis.
- Keep `6 strict units = 4 genes` distinct from `6 shared MT genes` in the
  network-collapsed view.
- Review the rebuilt deck at projection size in color and grayscale.

The reproducible builder is
[build_seaad_rosmap_human_validation_deck.py](../../scripts/presentations/build_seaad_rosmap_human_validation_deck.py).
