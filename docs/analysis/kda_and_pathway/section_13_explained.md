# Tutorial: understanding Section 13, “RPL11 connects ribosomal stress to APOO, TOMM7, and SLIRP”

**Source section:** [Joint Phase 11–12 synthesis](phase11_phase12_joint_mitochondrial_discussion.md)  
**Audience:** readers who want to understand why a common ribosomal protein can be both compelling and risky as a candidate  
**Purpose:** explain the RPL11 network result without confusing cytosolic ribosomal stress with mitochondrial ribosome biology

## 1. The central idea

`RPL11` is a protein in cytosolic ribosomes, the machines that translate most
cellular messenger RNAs. When ribosome production is disturbed, RPL11 can
activate a p53 stress checkpoint. Phase 12 places RPL11 in an unusually
consistent upstream, self-independent network position across many cells and
groups. Its neighborhoods include `APOO`, `TOMM7`, and `SLIRP`, three Phase 11
mitochondrial candidates. This could connect general ribosomal stress to
mitochondrial membrane, import, and RNA maintenance—or it could reflect a
highly expressed housekeeping hub.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Ribosome** | A molecular machine that translates RNA instructions into protein. |
| **Cytosolic ribosome** | A ribosome in the main body of the cell; it differs from a mitochondrial ribosome. |
| **Ribosomal stress** | A disruption of ribosome production or function that can activate cell-cycle arrest or death pathways. |
| **MDM2–p53 checkpoint** | A stress-control system in which MDM2 normally restrains p53; RPL11 can inhibit MDM2 and stabilize p53. |
| **Housekeeping gene** | A gene used broadly for basic cellular functions. High expression and broad connectivity can make such genes recur in networks. |
| **APOO/MIC26** | A mitochondrial inner-membrane protein associated with cristae organization. |
| **TOMM7** | A component of the outer-membrane protein-import machinery with a role in PINK1/Parkin mitophagy. |
| **SLIRP** | A mitochondrial RNA-binding protein involved in mtRNA stability. |
| **Empirical null** | A comparison distribution created from matched genes or randomized analyses rather than only a theoretical formula. |

## 3. Discovery sentence

> **“`RPL11` is the most consistently upstream, non-mtDNA,
> candidate-self-independent Phase 12 candidate and connects ribosomal-stress
> topology to the Phase 11 mitochondrial membrane, import, and RNA-maintenance
> candidates `APOO`, `TOMM7`, and `SLIRP`.”**

This sentence ranks RPL11 by several favorable properties:

- it is not one of the mtDNA structural genes that dominate raw KDA;
- all primary calls are self-independent;
- it repeatedly survives as a global, nonredundant candidate; and
- it recurs across many cell types and all six strata.

“Connects” still means network coverage. It does not prove RPL11 physically
binds or selectively regulates all three mitochondrial genes.

## 4. Conclusion paragraph

> **“RPL11 stress signaling and ribosome dysfunction in AD are established.”**

The RPL11–MDM2–p53 stress mechanism is established in cell biology, and early
ribosomal dysfunction/RNA oxidation has been reported in MCI and AD.

> **“The cross-lineage `RPL11`–`APOO`/`TOMM7`/`SLIRP` relationship is new and
> computationally strong, but its breadth could reflect a highly expressed
> housekeeping hub rather than a selective mitochondrial control mechanism.”**

Broad recurrence has two interpretations:

1. RPL11 is a true common control point connecting ribosomal and mitochondrial
   stress.
2. RPL11 appears because ubiquitous, well-connected ribosomal genes have many
   opportunities to overlap broad queries.

Matched null analyses and narrow perturbations are needed to distinguish them.

## 5. Evidence, item by item

### Overall RPL11 recurrence

- 131 total calls
- 53 primary calls
- four networks
- 17 fine cell types
- 118 global calls
- all primary calls candidate-self-independent
- 29 conservative directional calls across 16 fine types and all six strata

The global fraction is `118 / 131 = 90.1%`. This means RPL11 usually remains
the most upstream nonredundant representative rather than being removed as a
downstream duplicate.

### Exact mitochondrial bridges

| Phase 11 candidate | Primary RPL11 neighborhoods | Fine types | Directional | Derived union |
|---|---:|---:|---:|---:|
| `APOO` | 15 | 7 | 8 | 7 |
| `TOMM7` | 4 | 2 | 2 | 2 |
| `SLIRP` | 2 | not separately stated | 1 | 1 |

The union calls summarize combined queries and are not independent validation.
The APOO link is the most recurrent; TOMM7 and especially SLIRP rest on fewer
directional contexts.

Phase 11 had already prioritized TOMM7 for import/mitophagy follow-up and
treated APOO and SLIRP as possible mitochondrial membrane or mtRNA mediators.
Phase 12 adds a possible upstream ribosomal-stress candidate.

## 6. Prior work

RPL11 can bind MDM2 and activate p53 during ribosomal stress
([Zhang et al., 2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003)).
Ribosome dysfunction and RNA oxidation appear early in MCI and AD brain
([Ding et al., 2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005)).
RPL11 protein was elevated in purified AD brain capillaries but not matched
parenchyma
([Suzuki et al., 2022](https://doi.org/10.1177/0271678X221111602)), suggesting
that tissue compartment can matter.

TOMM7 has an experimental role in stabilizing PINK1 and recruiting Parkin
after mitochondrial damage
([Hasson et al., 2013](https://doi.org/10.1038/nature12748)).

These studies validate component functions, not an RPL11-directed
APOO/TOMM7/SLIRP chain.

## 7. Important interpretation warning

RPL11 is a **cytosolic** ribosomal protein. Its recurrence is not, by itself,
evidence that mitochondrial ribosomes are changing. A mitochondrial-ribosome
claim would require mitoribosomal genes, mitochondrial translation, or
mitoribosome measurements.

## 8. Decisive tests

First, compare RPL11 with genes matched for:

- expression level;
- network degree;
- ribosomal-gene status; and
- cell-type breadth.

Repeat the analysis in an independently inferred network and exclude candidates
from their own queries.

If RPL11 remains prioritized, perturb it mildly enough to avoid wholesale
translation collapse. Measure APOO, TOMM7, SLIRP, mitochondrial protein import,
mtRNA stability, and respiration alongside total translation, p53 activation,
viability, and cell death. A selective mitochondrial effect that occurs before
general toxicity would be more convincing than a change seen only after the
cell is globally stressed.

## 9. One-sentence takeaway

RPL11 is the most robust self-independent non-mtDNA network candidate and may
link ribosomal stress to mitochondrial maintenance, but its housekeeping-hub
status and p53 effects must be separated from selective mitochondrial control.
