# Tutorial: understanding Section 10, “OPC FTL connects ferritin to GPX4, FTH1, and respiratory genes”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers with a high-school-level biology background  
**Purpose:** explain the proposed OPC iron/redox network without incorrectly claiming that ferroptosis was observed

## 1. The central idea

Oligodendrocyte precursor cells (OPCs) eventually produce oligodendrocytes,
which make the insulating myelin around nerve fibers. These cells need iron
but can be harmed when iron promotes lipid oxidation. In two sex/APOE
contexts, Phase 12 places the ferritin light-chain gene `FTL` in an OPC network
with iron storage, antioxidant, mitochondrial-dynamics, and respiratory genes.
This suggests an iron/redox vulnerability program. It does **not** show that
the cells underwent ferroptosis, an iron-dependent form of cell death.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **OPC** | Oligodendrocyte precursor cell, an immature cell capable of becoming a myelin-producing oligodendrocyte. |
| **Ferritin** | A protein shell that safely stores iron. It is built from heavy-chain FTH1 and light-chain FTL subunits. |
| **Labile iron** | Chemically available iron that can participate in reactions; excess labile iron can promote oxidative damage. |
| **GPX4** | An enzyme that repairs oxidized membrane lipids and helps prevent ferroptosis. |
| **Lipid peroxidation** | Oxidative damage to membrane lipids. |
| **Ferroptosis** | A regulated, iron-dependent cell-death process characterized by overwhelming lipid peroxidation. |
| **Myelination** | Formation of the insulating myelin sheath around nerve fibers. |
| **Adjusted P value** | A significance value corrected for multiple testing. |

## 3. Title and novelty label

“FTL connects” means FTL is the center of an enriched computational
neighborhood. It does not say FTL physically controls every listed gene.

The exact sex/APOE-stratified OPC network is labeled new. The broader facts
that oligodendroglia depend on iron and that AD involves altered iron and lipid
oxidation are already supported by prior research.

## 4. Discovery sentence

> **“An OPC iron/redox neighborhood centered on `FTL` occurs in the
> female-ε3/ε3 AD-up and male-ε2 AD-down contexts, linking ferritin to `GPX4`,
> `FTH1`, mitochondrial dynamics, and OXPHOS genes.”**

The same general motif occurs with opposite query directions:

- female ε3/ε3: the relevant mitochondrial query is higher in AD;
- male ε2: it is lower in AD.

The shared motif may be a common iron/redox system responding differently by
context. It does not mean FTL itself is necessarily AD-up in one and AD-down
in the other, because KDA tests network overlap rather than direct differential
expression of the candidate.

## 5. Conclusion paragraph

> **“Oligodendroglial iron dependence and AD iron/lipid-peroxidation biology
> are established.”**

Previous studies support the importance of iron to oligodendroglia and show
iron/ferritin/lipid-oxidation changes in AD.

> **“The exact `FTL`-centered, sex/APOE-stratified OPC network is new.”**

What is new is the combination of candidate, fine cell class, sex/APOE
contexts, query direction, and covered mitochondrial genes.

> **“It supports an iron/redox susceptibility hypothesis, not a claim that
> Phase 11 or Phase 12 demonstrated ferroptosis.”**

Ferroptosis requires evidence of a particular death mechanism, ideally
including lipid-peroxidation-dependent death and rescue by a ferroptosis
inhibitor. RNA/network enrichment is insufficient.

> **“FTL may be protective iron sequestration rather than a pathogenic
> regulator.”**

More ferritin can be a defense: storing iron may prevent it from catalyzing
damaging reactions. Therefore, an FTL-centered signal could mark compensation,
not a disease-causing process.

## 6. Evidence, item by item

Phase 11 provides context: female ε3/ε3 is moderately mitochondrial AD-up,
whereas male ε2 has the largest mitochondrial DEG burden and is broadly
AD-down or mixed in OPCs and other lineages.

Phase 12 reports 12 FTL calls, four primary OPC calls, and no global calls. All
four primary calls are self-independent. Self-independence is favorable, but
the absence of global calls means FTL was not the most upstream nonredundant
candidate in the broader hierarchy.

### Female ε3/ε3 AD-up

Seven of 22 query genes fall within a 146-gene FTL neighborhood. The
15.53-fold enrichment and adjusted P value `1.89 × 10^-5` indicate that this
overlap is much larger than expected under the enrichment model.

### Male ε2 AD-down

Twelve of 81 query genes fall within a 123-gene FTL neighborhood. The
8.18-fold enrichment and adjusted P value `2.09 × 10^-6` also support
non-random overlap.

Both overlaps contain `FTH1`, `GPX4`, `COX5B`, and `UQCR10`. `NDUFB5` is
specific to the female ε3/ε3 overlap. The male ε2 neighborhood additionally
contains `FIS1`, `PARK7`, `ATP5IF1`, and other respiratory genes.

The counts describe network overlap, not protein activity or cell death.

## 7. Prior work

Iron, transferrin, and ferritin are prominent in oligodendroglia and change
distribution around AD plaques
([Connor et al., 1992](https://doi.org/10.1002/jnr.490310111)).
Oligodendrocytes can take up iron through H-ferritin/FTH1
([Todorich et al., 2011](https://doi.org/10.1002/glia.21164)); that mechanism
should not be incorrectly attributed specifically to FTL.

Iron overload lowers GPX4 and produces ferroptotic features in an
oligodendrocyte model
([Li et al., 2023](https://doi.org/10.1007/s11064-022-03807-6)), while primary
OPC ferroptosis contributes to experimental white-matter injury
([Shen et al., 2022](https://doi.org/10.1038/s41419-022-04712-0)).
Human AD tissue shows altered ferritin, lipid peroxidation, and ferroptosis
suppressors
([Ashraf et al., 2020](https://doi.org/10.1016/j.redox.2020.101494);
[Thorwald et al., 2025](https://doi.org/10.1002/alz.14541)).

These studies make the hypothesis plausible but do not validate the exact OPC
network.

## 8. Decisive experiment

FTL should be increased, reduced, and rescued in OPCs under controlled iron
loading. Measurements should include:

- labile iron and ferritin composition;
- GPX4 abundance and activity;
- lipid peroxidation;
- respiration;
- OPC survival, differentiation, and myelination.

To claim ferroptosis, cell death should be prevented by a mechanistically
appropriate ferroptosis inhibitor or genetic rescue, rather than merely being
associated with iron and GPX4 changes.

## 9. One-sentence takeaway

The new FTL-centered OPC motif links iron storage to antioxidant and
respiratory genes in two opposite-direction contexts, but it may represent
protection or susceptibility and is not evidence that ferroptosis occurred.
