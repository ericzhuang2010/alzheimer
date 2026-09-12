# Tutorial: understanding Section 12, “Microglial SLC11A1 connects ACSL1 to mitochondrial iron importer SLC25A37”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers with a high-school-level biology background  
**Purpose:** explain the proposed microglial iron/lipid/mitochondrial triad and why it is preliminary

## 1. The central idea

Microglia are the brain's resident immune cells. They digest material in
lysosomes, store lipids in droplets, and must control iron carefully.
In male-ε4 `Mic P2RY12` cells, Phase 12 identifies a very small network in
which `SLC11A1` is associated with `ACSL1` and `SLC25A37`. The three genes
could connect lysosomal iron handling, lipid-droplet metabolism, and delivery
of iron to mitochondria. Each component has outside support, but the exact
three-gene mechanism is new and rests on only one self-independent directional
network result.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Microglia** | Immune and maintenance cells that reside in the brain. |
| **Mic P2RY12** | A microglial fine-cell population marked by the homeostatic microglial gene `P2RY12`. |
| **SLC11A1** | A metal-ion transporter associated with immune-cell iron handling. |
| **ACSL1** | An enzyme that activates long-chain fatty acids for lipid metabolism and storage. |
| **SLC25A37/mitoferrin-1** | A transporter that moves iron into mitochondria. |
| **Lipid droplet** | A cellular compartment that stores neutral lipids. |
| **Lysosome** | An acidic recycling compartment that can also store and release iron. |
| **Antiporter** | A transporter moving two substances in opposite directions across a membrane. |
| **Layer-1 neighborhood** | Genes directly adjacent to the candidate in the analyzed network. |

## 3. A crucial gene-name warning

`ACSL1` is not `ACSL4`.

- `ACSL1` is prominent in lipid-droplet microglia and general fatty-acid
  handling.
- `ACSL4` helps create the oxidizable membrane lipids that sensitize cells to
  ferroptosis.

The result contains **ACSL1**. It must not be cited as though ACSL4 was found.

## 4. Discovery sentence

> **“Phase 12 identifies a compact male-ε4 `Mic P2RY12` `SLC11A1`
> neighborhood containing lipid-droplet enzyme `ACSL1` and mitochondrial iron
> importer `SLC25A37`.”**

“Compact” means the relevant layer-1 neighborhood has only four genes.
`ACSL1` and `SLC25A37` are two query genes captured in it. A small direct
neighborhood can suggest specificity, but it can also be statistically
fragile because the conclusion depends on very few genes.

## 5. Conclusion paragraph

> **“The individual components have external support of differing strength:
> SLC11A1 is associated with inflammatory AD microglia, ACSL1 marks
> APOE4-enriched lipid-droplet microglia, and SLC25A37 transports
> mitochondrial iron.”**

The outside evidence is not uniform. SLC25A37's transport function is
well-established. ACSL1 has strong relevance to APOE4 lipid-droplet microglia.
SLC11A1 has AD-expression support and direct iron-transport evidence in
microglia from a different disease model.

> **“The exact triad is new.”**

No located primary paper demonstrated an
SLC11A1–ACSL1–SLC25A37 pathway in AD microglia.

> **“It does not explain the distinct male-ε2 microglial OXPHOS-down signal
> from Phase 11, and ACSL1 must not be confused with ferroptosis enzyme
> ACSL4.”**

The network result is male ε4 and AD-up; the strong Phase 11 microglial OXPHOS
result is male ε2 and mainly AD-down. Because the groups and directions differ,
the triad cannot simply be presented as the mechanism behind that Phase 11
signal.

## 6. Evidence, item by item

In male-ε2 `Mic P2RY12`, 12 of 23 tested OXPHOS-subunit occurrences are
significant, and 11 are AD-down. This describes a strong local Phase 11
phenotype but in a different APOE stratum.

`SLC11A1` has nine Phase 12 calls, including three primary rows across two
microglial fine types. Only one primary row is both directional and
candidate-self-independent. The other two are derived `AD_both_mito` union
rows and should not be counted as separate directional replications.

The key male-ε4 AD-up result has:

- two covered query genes: `ACSL1` and `SLC25A37`;
- a four-gene direct neighborhood;
- a 12-gene query;
- fold enrichment `191.96`; and
- adjusted P `0.0070`.

The enormous fold enrichment reflects how unlikely it is to draw two query
genes into such a tiny neighborhood under the statistical model. The absolute
evidence is still two genes in one directional result, so effect replication
and experimental validation matter more than the striking fold number.

## 7. Prior work

Integrated human analyses nominated SLC11A1 in inflammatory AD microglia
([Zhou et al., 2025](https://doi.org/10.2147/JIR.S497418)).
In a white-matter stroke model, microglial SLC11A1 acted as an H+/Fe2+
antiporter and promoted lysosomal iron accumulation
([Qiu et al., 2026](https://doi.org/10.1002/advs.202511482)).

ACSL1-positive lipid-droplet microglia are enriched in APOE4/4 AD brain, and
ACSL1 inhibition reduces Aβ-induced lipid droplets in human iPSC-derived
microglia
([Haney et al., 2024](https://doi.org/10.1038/s41586-024-07185-7)).

SLC25A37 is an established mitochondrial iron importer
([Shaw et al., 2006](https://doi.org/10.1038/nature04512)), and its loss in
brain affects respiration and memory
([Baldauf et al., 2019](https://doi.org/10.1016/j.neulet.2019.134521)).
No direct microglial SLC11A1–SLC25A37 mechanism was located.

## 8. Decisive experiment

Perturb and rescue SLC11A1 in matched APOE3/3 and APOE4/4 microglia, then
measure:

- lysosomal iron and mitochondrial iron separately;
- ACSL1 and SLC25A37 RNA/protein;
- lipid-droplet formation;
- phagocytosis;
- mitochondrial respiration;
- lipid peroxidation and viability.

Changing both compartments in the predicted sequence would support the triad.
Ferroptosis should not be claimed unless a defined death mechanism is shown
and rescued by a ferroptosis-specific intervention.

## 9. One-sentence takeaway

The male-ε4 SLC11A1 neighborhood offers a plausible new link between
lysosomal iron, ACSL1-positive lipid storage, and mitochondrial iron import,
but it is based on one tiny directional network and does not demonstrate
ferroptosis or explain the male-ε2 OXPHOS signal.
