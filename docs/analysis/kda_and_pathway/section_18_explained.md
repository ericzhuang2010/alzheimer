# Tutorial: understanding Section 18, “HSPA1A connects stress to HSPD1 in vascular and inhibitory networks”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers with a high-school-level biology background  
**Purpose:** explain the low-confidence HSPA1A–HSPD1 hypothesis and keep three similarly named chaperones distinct

## 1. The central idea

Cells use heat-shock proteins as molecular helpers, or chaperones, to prevent
damaged proteins from misfolding. `HSPA1A` is an inducible chaperone mainly in
the cytosol. `HSPD1` is a chaperonin inside mitochondria. Phase 12 repeatedly
puts HSPD1 inside HSPA1A-centered vascular or inhibitory-neuron neighborhoods.
One vascular result matches a female-ε4 mitochondrial-chaperone decrease from
Phase 11. The link is interesting but fragile, and both genes may simply
respond to the same stress rather than one controlling the other.

## 2. Keep these genes separate

| Gene | Common name/location | Why it matters here |
|---|---|---|
| `HSPA1A` | Inducible Hsp70, mainly cytosolic | Phase 12 candidate |
| `HSPA9` | Mortalin/mtHsp70, mitochondrial | Covered in the conservative inhibitory-neuron query |
| `HSPD1` | Hsp60, mitochondrial chaperonin | Recurrent proposed mediator/readout |

Similar heat-shock names do not make the proteins interchangeable.

## 3. Discovery paragraph

> **“`HSPA1A` is a candidate-self-independent stress candidate whose primary
> Phase 12 neighborhoods always contain mitochondrial chaperonin `HSPD1`.”**

HSPD1 appears in all ten primary HSPA1A neighborhoods. Because the candidate
is self-independent, HSPA1A was not nominated merely by being in the query.
“Always” applies to this set of ten results, not to every cell or every
possible HSPA1A network.

> **“Its best vascular neighborhood is enriched for an HSPD1-containing
> female-ε4 AD-down query, aligning with the Phase 11 chaperone-loss phenotype
> without showing that HSPA1A itself is down.”**

The query genes are AD-down, and HSPD1 is among them. KDA tests whether those
query genes cluster below HSPA1A. It does not require HSPA1A RNA itself to be
AD-down. Therefore, “HSPA1A–HSPD1 network alignment” is accurate;
“HSPA1A loss drives the network” is not.

## 4. Conclusion paragraph

> **“The exact HSPA1A–HSPD1 AD topology is new but fragile.”**

The specific computational connection was not established by prior studies.
It is fragile because the strongest contextual matches depend on small queries
or a single conservative result.

> **“The vascular result has the most direct cross-phase alignment, whereas
> the sole conservative call is inhibitory-neuronal.”**

The best match to Phase 11 occurs in endothelial cells, but the only call
passing the strict conservative directional screen comes from Rosehip
inhibitory neurons. No single result supplies both advantages.

> **“A shared heat-shock or proteotoxic-stress response is at least as
> plausible as direct HSPA1A control of HSPD1.”**

Both chaperones can react to protein damage. Their co-occurrence could reflect
parallel responses to one stressor rather than a directed regulatory edge.

## 5. Evidence, item by item

Phase 11 contains 37 female-ε4 mitochondrial-chaperone DEG occurrences. All
are AD-down, and HSPD1 supplies much of the count.

HSPA1A has 20 Phase 12 calls across vascular and inhibitory networks, ten
primary calls, and 14 global calls. HSPD1 occurs in all ten primary
neighborhoods: five directional and five derived unions.

The one conservative call is female-ε4 AD-down in `Inh LAMP5 NRG1
(Rosehip)`. It covers HSPA9 and HSPD1 in a four-gene layer-2 neighborhood
against a 55-gene query, with 71.97-fold enrichment and adjusted P `0.0117`.
The fold is large because two query genes lie in a tiny neighborhood, but it
is still one result.

The best vascular primary result is female-ε4 endothelial AD-down. It covers
MRPS6 and HSPD1 in a 51-gene layer-3 neighborhood, but only four effective
query genes were available. A four-gene query is sensitive to the inclusion
or exclusion of a single gene.

## 6. Prior work

HSPA1A protein was reduced in AD cortical samples in an APP-processing
interactome study
([Gerber et al., 2019](https://doi.org/10.1186/s40478-019-0660-3)).
In contrast, HSPD1 and other mitochondrial unfolded-protein-response genes
were increased in familial and sporadic AD cortex
([Beck et al., 2016](https://doi.org/10.2174/1567205013666151221145445)).
APOE4 can compromise cerebrovascular function
([Liu et al., 2022](https://doi.org/10.1038/s41593-022-01127-0)).

Different bulk directions do not necessarily contradict the fine-cell result:
tissue composition, disease stage, cell type, and stress severity may differ.
They also do not validate the directed HSPA1A→HSPD1 relationship.

## 7. Decisive experiment

Test HSPA1A in both brain endothelial cells and the nominated inhibitory
neuronal subtype. Reduce, increase, and rescue HSPA1A while separately
measuring:

- HSF1 heat-shock signaling;
- HSPD1 and HSPA9;
- mitochondrial protein folding and aggregation;
- respiration and membrane potential;
- stress survival;
- endothelial barrier function or inhibitory-neuron electrophysiology.

Time-resolved experiments should ask whether HSPD1 changes specifically after
HSPA1A perturbation or whether both genes move together only under a shared
stress exposure.

## 8. One-sentence takeaway

HSPD1 repeatedly sits inside self-independent HSPA1A networks, but the
cross-phase evidence is split between vascular and inhibitory cells and is
equally compatible with a shared stress response, making this a new,
low-confidence hypothesis.
