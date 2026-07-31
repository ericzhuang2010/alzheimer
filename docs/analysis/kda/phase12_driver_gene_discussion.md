# Phase 12 key-driver analysis: driver-gene prioritization and biological interpretation

**Analysis date:** 2026-07-30  
**Production output:** [`results/minerva_production/12_kda/`](../../../results/minerva_production/12_kda/)  
**Scope:** cell-type-, sex-, and APOE-stratified key-driver analysis (KDA) of
Alzheimer's disease (AD)-associated core mitochondrial gene signatures

## Executive summary: discoveries and novelty assessment

Phase 12 is technically complete and suitable for hypothesis generation. It
does **not** establish causal AD drivers. A reported gene is a **putative key
driver whose directed downstream Bayesian-network neighborhood is enriched for
a particular mitochondrial AD signature**.

The literature review was updated through **2026-07-30** using targeted
PubMed/Europe PMC and publisher searches for each candidate, AD, the relevant
cell type, mitochondrial biology, and the specific downstream genes. Primary
research was prioritized. The novelty labels below apply to the **specific
Phase 12 claim**, not to the first appearance of a gene in biology:

- **Rediscovery / confirmation:** prior work already supports the same broad
  AD and cell-biological relationship.
- **New network extension:** prior work supports the gene or pathway, but not
  the cell-type-specific directed mitochondrial neighborhood found here.
- **New Phase 12 hypothesis:** no directly matching prior report was identified
  for the specific relationship. This is a qualified literature assessment,
  not proof of absolute publication priority.

| Discovery or hypothesis | Novelty status | Summary interpretation |
|---|---|---|
| Respiratory-chain and OXPHOS genes form the dominant network core | **Rediscovery plus new cell-type/topology extension** | Human AD studies already show mitochondrial and OXPHOS dysregulation. Phase 12 adds recurrent directed neighborhoods, but self-membership and mtRNA coexpression prevent a causal-driver claim. |
| Astrocytic `APOE` centers a `TUFM`/`LDHB`/ATP-synthase program | **Rediscovery plus new network extension** | APOE-dependent astrocyte metabolism, mitochondrial dynamics, and mitophagy are established. The compact `APOE` neighborhood and its ε2/sex pattern are new hypotheses. |
| Neuronal `GABARAPL2` centers `CHCHD2` and `PARK7` neighborhoods | **Preclinically confirmed AD biology plus new network extension** | GABARAPL2-dependent autophagosome–lysosome fusion has direct AD-model support. Its recurrent human excitatory-neuron placement and `PARK7` relationship are not yet validated. |
| Neuronal `SELENOW` organizes mitochondrial redox/proteostasis programs | **Preclinically confirmed AD biology plus new network extension** | SELENOW has already been shown to regulate tau homeostasis and cognition in an AD mouse model. Its subtype-specific human mitochondrial-network placement is new. |
| Microglial `SLC11A1` links `ACSL1` to mitochondrial iron importer `SLC25A37` | **Expression-level rediscovery plus new network extension** | Prior AD transcriptomic work nominated microglial `SLC11A1`; stroke experiments establish its lysosomal-iron mechanism. The three-gene AD network relationship is new and narrow. |
| Neuronal `LAMTOR5` links Ragulator signaling to `ATP5IF1` | **New Phase 12 hypothesis** | Ragulator–mTORC1 biology is established, but the recurrent AD neuronal `LAMTOR5`–`ATP5IF1` relationship has not been directly reported. |
| OPC `FTL` links iron storage to a `GPX4`/`FTH1`/mitochondrial program | **New Phase 12 hypothesis** | Oligodendroglial iron dependence and AD ferritin redistribution are established; `FTL` as a sex/APOE-stratified OPC network organizer is new. |
| `RPL11` connects ribosomal stress to mitochondrial neighborhoods | **Established biology plus new network extension** | Ribosome dysfunction in AD and extra-ribosomal RPL11 stress signaling are established. Its cross-lineage `APOO`/`TOMM7`/`SLIRP` topology is new. |
| `RPS15` is a recurrent cross-network candidate | **New in AD mitochondrial networks** | RPS15 has established stress and neurodegeneration biology outside AD, but no direct AD-specific upstream mitochondrial role was identified. |
| Excitatory `WDR82` centers an AD-up mtRNA/OXPHOS motif | **New in AD cell-type networks** | WDR82 has prior chromatin and non-neural mitochondrial/OXPHOS functions and was previously nominated in a bulk AD network. Its excitatory-neuron mitochondrial placement is new. |
| `BEX3` links death signaling to neuronal/OPC mitochondrial maintenance | **New in AD networks** | Neural-death biology is established, but the human AD network relationship is unvalidated. |
| `TMEM147` links excitatory ER/cholesterol machinery to mitochondrial signatures | **New AD network hypothesis** | ER translocon and cholesterol functions are established; no directly matching AD neuronal/OXPHOS report was identified. |
| `ANKRD11` marks an OPC iron/mitochondrial program | **New cell-type network hypothesis** | Neuronal chromatin functions are established, but the OPC mitochondrial relationship is new. |
| `HSPA1A` links vascular stress to `HSPD1` | **New, low-confidence hypothesis** | AD proteostasis evidence exists for both chaperones, but the directed relationship is small-query dependent and may reflect shared stress. |
| The pre-network mitochondrial shortlist is mainly a downstream assay panel | **New analytical synthesis** | `ATP5IF1`, `TUFM`, `HSPD1`, and `PARK7` remain important, but Phase 12 more often positions them downstream of other candidates. |
| Sex/APOE-direction patterns differ across candidates | **New descriptive hypothesis** | The patterns can guide stratified validation, but they are not formal interaction effects. |
| Cell-type-specific lipid, autophagy, iron/redox, and stress systems converge on one respiratory core | **New integrative hypothesis** | This is the most parsimonious synthesis of Phase 12, not a demonstrated causal model. |

The unfiltered result is dominated by mtDNA and structural OXPHOS genes. A
conservative screen emphasizing primary directional runs, excluding mtDNA and
driver self-overlap, and requiring multi-gene support produces a more useful
regulatory shortlist.

If experimental capacity is limited, a balanced first-pass panel is:

> **Established or independently supported anchors:** `APOE`, `GABARAPL2`,
> `SELENOW`, and `SLC11A1`
>
> **New or topology-led tests:** `LAMTOR5`, `FTL`, `RPL11`, and `WDR82`

`RPS15`, `BEX3`, `TMEM147`, `ANKRD11`, and `HSPA1A` form a second tier.
`ATP5IF1`, `TUFM`, `HSPD1`, `PARK7`, mtDNA genes, and structural OXPHOS genes
are priority downstream readouts rather than the default perturbation targets.

## 1. What Phase 12 tested

### 1.1 Analysis design

Phase 12 projected cell-type-specific core mitochondrial AD-versus-NCI
signatures onto matching broad Bayesian networks.

The primary design contained:

- 54 fine cell types;
- six sex/APOE groups: `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, and `M_e4`;
- three signature definitions: `AD_up_mito`, `AD_down_mito`, and
  `AD_both_mito`; and
- 972 planned primary analyses.

The secondary design contained five prespecified pools:

- female;
- male;
- ε2;
- ε3/ε3; and
- ε4.

The five pools and three signature definitions produced 810 planned secondary
analyses. The complete design therefore contained 1,782 planned runs.

Secondary pools are useful sensitivity summaries, but they are not independent
replications. They reuse primary signatures, and the sex and APOE pools
overlap.

### 1.2 Query and background

For each run, Phase 12:

1. selected the matching Phase 08 AD-versus-NCI result;
2. restricted the candidate signature to the Phase 09
   `core_mito_protein` universe;
3. constructed the AD-up, AD-down, or union signature;
4. obtained the exact genes tested in the contributing contrast or contrasts;
5. induced the matching broad network on those tested genes;
6. defined the effective background as the nodes in that induced network; and
7. intersected the mitochondrial signature with that background.

A run was eligible when its source contrast was validated, its induced network
was nonempty, and at least three query genes remained in the effective
background.

This run-specific background is important. Two signatures that use the same
broad network can have different tested genes, induced edges, backgrounds, and
effective query sizes.

### 1.3 KDA statistic

The exact configuration was:

| Parameter | Value |
|---|---:|
| Directed network | `TRUE` |
| Maximum tested neighborhood | 3 cumulative layers |
| Signature expansion | 0 layers |
| Global-driver reduction radius | 2 layers |
| Within-run correction | Benjamini–Hochberg |
| Reported cutoff | adjusted P ≤ 0.05 |

For candidate driver \(d\), a cumulative directed neighborhood at one, two, or
three layers was tested. Let:

- \(M\) be the effective background size;
- \(m\) be the candidate's cumulative neighborhood size;
- \(k\) be the effective signature size; and
- \(q\) be the number of signature genes in the neighborhood.

The fold enrichment is:

\[
\mathrm{FE} = \frac{q/m}{k/M} = \frac{qM}{mk}.
\]

An upper-tail hypergeometric test measures whether \(q\) or more signature
genes are unexpectedly concentrated in a neighborhood of size \(m\). The layer
with the smallest raw P value is retained for each candidate, and
Benjamini–Hochberg correction is then applied across retained candidate-level
P values within that run.

The `global_key_driver` flag is a redundancy-reduction label within one run. A
significant driver is marked global when it is not within two downstream
layers of another significant driver in that run. It does **not** mean
study-wide significance or universal importance.

The executed method is documented in
[`call_key_drivers_explained.md`](call_key_drivers_explained.md), and the
frozen implementation is
[`scripts/NetWeaver/fKDA.R`](../../../scripts/NetWeaver/fKDA.R). Bayesian
network KDA has precedent in AD discovery, but prior work obtained causal
confidence by integrating genetics and multi-omics and then experimentally
validating the prediction; the Phase 12 enrichment result is the nomination
step, not that complete chain of evidence
([Beckmann et al., 2020](https://doi.org/10.1038/s41467-020-17405-z)).

## 2. Production quality and result landscape

### 2.1 Technical validity

The production status is `validated_complete`.

| Quantity | Result |
|---|---:|
| Planned runs | 1,782 |
| Eligible runs | 1,021 |
| Skipped runs | 761 |
| Failed runs | 0 |
| Runs with ≥1 reported driver | 840 |
| Reported driver rows | 10,172 |
| Unique driver genes | 717 |
| Broad-network–driver pairs | 889 |
| Failed validation checks | 0 |

All 11 recorded validation checks passed. The prior full-table audit also
reproduced the enrichment arithmetic and hypergeometric statistics, checked
signature/background membership, verified artifact hashes, and independently
reconstructed directed paths for representative results. See
[`phase12_minerva_kda_results_sanity_check.md`](phase12_minerva_kda_results_sanity_check.md).

### 2.2 Eligibility and output by network

| Broad network | Planned | Eligible | Significant runs | Driver rows | Unique drivers | Significant / eligible |
|---|---:|---:|---:|---:|---:|---:|
| Astrocytes | 99 | 97 | 64 | 473 | 89 | 66.0% |
| CAMs | 33 | 0 | 0 | 0 | 0 | — |
| Excitatory neurons | 462 | 418 | 345 | 5,923 | 398 | 82.5% |
| Inhibitory neurons | 825 | 367 | 318 | 3,037 | 257 | 86.6% |
| Microglia | 99 | 44 | 39 | 170 | 37 | 88.6% |
| OPCs | 33 | 30 | 24 | 230 | 47 | 80.0% |
| Oligodendrocytes | 33 | 29 | 17 | 145 | 41 | 58.6% |
| T cells | 33 | 0 | 0 | 0 | 0 | — |
| Vasculature | 165 | 36 | 33 | 194 | 20 | 91.7% |

CAMs and T cells produced no eligible KDA runs. Their absence is an input-size
or source-validation outcome, not evidence that those lineages have no
mitochondrial drivers.

The median effective query size was 13 genes for primary analyses and 25 genes
for secondary analyses. Seventy-seven primary and 48 secondary eligible runs
contained only three or four genes.

### 2.3 Why raw recurrence is not enough

The 10,172 reported rows contain several features that can exaggerate an
apparently impressive driver:

| Feature | Rows | Fraction |
|---|---:|---:|
| mtDNA-encoded driver | 3,036 | 29.8% |
| Driver is itself a query member | 5,349 | 52.6% |
| Only one query gene covered | 1,662 | 16.3% |
| Effective query smaller than 10 genes | 2,300 | 22.6% |

These categories overlap. They are not errors. They explain why an isolated
result can have very high fold enrichment: placing one query gene in a
one- or two-gene neighborhood against a background of thousands can generate a
large enrichment ratio.

## 3. Conservative driver-prioritization framework

No reported P value was changed or recalculated for this report. Instead,
existing significant calls were prioritized descriptively.

Primary evidence was given more weight than pooled evidence because pooled
signatures reuse primary data. To reduce derived duplication and trivial
enrichment, the most conservative screen retained result rows satisfying all
of the following:

1. `analysis_tier == primary`;
2. direction was `AD_up_mito` or `AD_down_mito`, not the derived union
   `AD_both_mito`;
3. the driver was not mtDNA encoded;
4. the driver was not a member of that run's effective query;
5. `overlap_count >= 2`; and
6. `signature_size >= 10`.

Driver membership was reconstructed from the exact overlap list. This resolves
the small number of raw `is_signature == NA` values without treating them as
automatically true or false.

The screen retained:

- 694 result rows;
- 200 unique genes;
- 103 primary runs; and
- 6.8% of the complete result table.

This is an interpretive robustness screen, not a new null-hypothesis test. It
does not provide a new FDR estimate.

## 4. Respiratory-chain hubs recapitulate established AD mitochondrial dysregulation — [Rediscovery plus new cell-type/topology extension]

**Discovery.** The unfiltered Phase 12 recurrence ranking is dominated by
mtDNA-encoded and nuclear structural OXPHOS genes.

**Conclusion.** Phase 12 robustly recovers a recurrent directed
respiratory-chain subnetwork associated with AD mitochondrial signatures. It
does not show that structural respiratory subunits are tractable upstream
causal regulators; most should be treated as sentinels and assay readouts.

**Data-driven evidence.**

| Driver | Calls | Primary | Networks | Fine cell types | Global calls | Driver-self calls |
|---|---:|---:|---:|---:|---:|---:|
| `MT-CO2` | 550 | 216 | 7 | 44 | 505 | 347 |
| `MT-ND4` | 402 | 153 | 7 | 43 | 10 | 362 |
| `MT-CO3` | 399 | 153 | 7 | 42 | 47 | 258 |
| `MT-CYB` | 397 | 153 | 5 | 38 | 16 | 232 |
| `MT-ND5` | 314 | 123 | 3 | 37 | 3 | 194 |
| `MT-ND4L` | 293 | 121 | 5 | 34 | 102 | 240 |
| `MT-ND1` | 245 | 99 | 5 | 32 | 3 | 178 |
| `MT-ATP6` | 233 | 95 | 4 | 20 | 2 | 198 |

Nuclear OXPHOS genes show the same structure. `COX4I1` has 169 calls across
five networks and 21 fine cell types, but is a query member in 149 calls.
`COX7C`, `UQCR10`, `COX6B1`, and `COX7B` are also recurrent and mostly
self-containing. `MT-CO2` is the notable exception: 203 of its 550 calls do
not contain `MT-CO2` itself, and 505 calls are global.

**Prior work and interpretation.** Laser-captured AD neurons show reduced
electron-transport and energy-metabolism transcripts
([Liang et al., 2008](https://doi.org/10.1073/pnas.0709259105)), while another
human study found opposite OXPHOS directions in whole hippocampus and isolated
pyramidal neurons, demonstrating the importance of cell composition
([Rice et al., 2015](https://doi.org/10.3233/JAD-142937)). A 2026 study further
showed an Aβ-sensitive neuronal `MT-ND4` RNA-quality-control mechanism that
activates innate immune signaling
([Pan et al., 2026](https://doi.org/10.1126/sciadv.adz0887)). These papers
confirm the biological relevance of respiratory and mtRNA dysregulation, not
the Phase 12 edge direction.

**Limits and decisive test.** mtDNA polycistronic transcription, abundance,
RNA quality, self-membership, and shared network motifs can all inflate
recurrence. Exclude mtDNA genes from the candidate set while retaining them in
the query, then test whether nuclear upstream rankings survive mtRNA-abundance,
degree, and network-topology matching.

## 5. Cross-candidate quantitative comparison

`Strict directional` refers to the conservative screen defined above.
`Minimum primary q` is the smallest within-run BH-adjusted P value among
primary calls and is not a phase-wide q value.

| Gene | Total / primary calls | Networks / fine types | Global calls | Self-independent primary calls | Strict directional calls | Strict fine types | Minimum primary q |
|---|---:|---:|---:|---:|---:|---:|---:|
| `RPL11` | 131 / 53 | 4 / 17 | 118 | 53 | 29 | 16 | 1.03×10^-11 |
| `RPS15` | 123 / 50 | 5 / 22 | 23 | 50 | 26 | 19 | 4.57×10^-14 |
| `WDR82` | 70 / 42 | 1 / 12 | 70 | 42 | 21 | 12 | 5.53×10^-6 |
| `LAMTOR5` | 96 / 38 | 2 / 15 | 9 | 38 | 20 | 13 | 1.03×10^-5 |
| `SELENOW` | 95 / 35 | 2 / 14 | 89 | 35 | 16 | 10 | 2.57×10^-8 |
| `GABARAPL2` | 79 / 32 | 2 / 13 | 26 | 32 | 17 | 11 | 3.39×10^-5 |
| `TMEM147` | 78 / 30 | 1 / 10 | 5 | 30 | 15 | 10 | 9.58×10^-7 |
| `BEX3` | 36 / 13 | 3 / 7 | 26 | 13 | 7 | 7 | 1.00×10^-3 |
| `APOE` | 20 / 7 | 1 / 3 | 7 | 7 | 4 | 3 | 3.33×10^-4 |
| `FTL` | 12 / 4 | 1 / 1 | 0 | 4 | 2 | 1 | 2.09×10^-6 |
| `ANKRD11` | 12 / 4 | 1 / 1 | 12 | 4 | 2 | 1 | 8.81×10^-6 |
| `SLC11A1` | 9 / 3 | 1 / 2 | 5 | 3 | 1 | 1 | 9.29×10^-4 |
| `HSPA1A` | 20 / 10 | 2 / 5 | 14 | 10 | 1 | 1 | 1.17×10^-2 |
| `PARK7` | 6 / 3 | 2 / 3 | 6 | 1 | 0 | 0 | 2.98×10^-2 |

This table is intentionally not collapsed into one score. Recurrence,
within-run upstream position, cell-type match, prior disease evidence, and
experimental tractability answer different questions.

## 6. Astrocytic APOE centers a TUFM/LDHB mitochondrial program — [Rediscovery plus new network extension]

**Discovery.** `APOE` is a self-independent astrocyte key-driver candidate
whose neighborhoods repeatedly contain `TUFM`, `LDHB`, ATP-synthase subunits,
and mitochondrial-dynamics genes.

**Conclusion.** The broad finding confirms established APOE-dependent
astrocyte mitochondrial and metabolic biology. The specific directed
`APOE`–`TUFM` neighborhood, its multi-isoform pattern, and its sex/APOE
directions are new network hypotheses. `APOE` is the strongest
disease-anchored, cell-type-matched Phase 12 candidate.

**Data-driven evidence.**

- 20 total astrocyte calls and seven primary calls across all three astrocyte
  fine types;
- no primary driver self-membership; seven global calls in total, including
  two primary calls (one directional and one derived `AD_both_mito` call);
- four conservative directional calls across three fine types;
- three to five covered mitochondrial genes per conservative call;
- primary directions in female-ε2 AD-up, male-ε2 AD-down, and male-ε4
  AD-down; and
- `TUFM` downstream in all seven primary `APOE` calls: four directional and
  three derived `AD_both_mito` calls.

Representative neighborhoods are:

- `Ast GRM3`, male-ε2 AD-down: `ATP5PB`, `LDHB`, `TUFM`, `ATP5F1A`, `AGT`;
- `Ast DPP10`, male-ε2 AD-down: `ATP5PB`, `LDHB`, `TUFM`, `AGT`; and
- `Ast GRM3`, female-ε2 AD-up: `LDHB`, `TUFM`, `CHCHD10`.

**Prior work and interpretation.** APOE4-expressing astrocytes have altered
mitochondrial dynamics, reduced mitophagy, and impaired mitochondrial function
([Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4)).
Stable-isotope tracing showed APOE-isoform-dependent glycolytic, pentose
phosphate, and TCA-cycle flux in astrocytes
([Williams et al., 2020](https://doi.org/10.1016/j.nbd.2020.104742)).
APOE4 also impairs neuron–astrocyte fatty-acid transfer and astrocytic fatty-acid
oxidation ([Qi et al., 2021](https://doi.org/10.1016/j.celrep.2020.108572)).
These studies validate the broad biological bridge; none establishes the
Phase 12 `APOE`–`TUFM` direction.

**Limits and decisive test.** Most prior experiments compare APOE4 with APOE3,
whereas Phase 12 is not exclusively ε4. Test isogenic APOE2/3/4 astrocytes with
paired APOE perturbation/rescue, then measure the prespecified `TUFM`, `LDHB`,
`CHCHD10`, `ATP5PB`, and `ATP5F1A` program together with respiration,
mitophagy, and carbon flux.

## 7. GABARAPL2 links autophagic flux to CHCHD2 and PARK7 — [Preclinically confirmed AD biology plus new network extension]

**Discovery.** `GABARAPL2` is a recurrent neuronal candidate whose primary
neighborhoods repeatedly contain mitochondrial quality-control genes,
especially `CHCHD2` and `PARK7`.

**Conclusion.** GABARAPL2-dependent autophagosome–lysosome fusion and an AD
role are already experimentally supported. Phase 12 independently extends
that biology to human excitatory-neuron mitochondrial neighborhoods.
`GABARAPL2` is a high-priority anchor; `PARK7` is better supported as its
downstream stress readout than as an upstream Phase 12 driver.

**Data-driven evidence.**

- 79 total and 32 primary calls across excitatory and inhibitory networks;
- 17 conservative directional calls across 11 fine cell types;
- 26 global calls and complete primary self-independence;
- `CHCHD2` in 25 primary neighborhoods across ten fine cell types;
- `PARK7` in 16 primary neighborhoods across seven fine cell types; and
- support across female-ε2 AD-up, female-ε4 AD-down, male-ε2 up and down,
  male-ε3/ε3 down, and male-ε4 up.

Other covered genes include `ATP5MC3`, `BAX`, mitochondrial ribosomal genes,
and iron–sulfur genes.

**Prior work and interpretation.** GABARAP-family proteins are required for
autophagosome–lysosome fusion
([Wang et al., 2015](https://doi.org/10.1073/pnas.1507263112)). In 5xFAD mice,
SIK2-dependent phosphorylation of GABARAPL2 promoted fusion, and a
phosphomimetic GABARAPL2 construct improved amyloid, synaptic, and behavioral
phenotypes ([Dai et al., 2025](https://doi.org/10.1186/s40035-025-00514-4)).
Separately, CHCHD2 and CHCHD10 were shown to interact preferentially with
GABARAP-family proteins and promote aggregate clearance
([Zhou et al., 2026](https://doi.org/10.1080/15548627.2026.2678427)). This
directly supports one Phase 12 neighborhood component, but not the
`GABARAPL2`–`PARK7` relation.

**Limits and decisive test.** GABARAP paralogs are partly redundant, and
phosphorylation-dependent activity is not equivalent to RNA abundance or KDA
placement. Perturb `GABARAPL2` and its Ser72 state in excitatory neurons, then
measure flux, mitophagy, `CHCHD2`, `PARK7`, respiration, and AD phenotypes.

## 8. SELENOW organizes neuronal mitochondrial programs — [Preclinically confirmed AD biology plus new network extension]

**Discovery.** `SELENOW` is a predominantly global excitatory/inhibitory
candidate linked to mitochondrial carrier, assembly, translation, redox, and
proteostasis genes.

**Conclusion.** SELENOW is **not a wholly novel AD candidate**: a 2024 study
directly established a protective tau-homeostasis role in an AD mouse model.
The new Phase 12 contribution is its recurrent, subtype-specific placement
upstream of human neuronal mitochondrial programs.

**Data-driven evidence.**

- 95 total and 35 primary calls across two neuronal networks and 14 fine cell
  types;
- 89 global calls and complete primary self-independence;
- 16 conservative directional calls across ten fine cell types;
- clearest recurrence in female-ε2 AD-up, male-ε2 AD-down, and female-ε4
  AD-down; and
- recurrent coverage of `SLC25A4`, `PRELID1`, `NDUFB11`, `COA3`, `CHCHD10`,
  mitochondrial ribosomal genes, and `CLPP`; `FIS1` occurs in two primary
  neighborhoods.

**Prior work and interpretation.** SELENOW binds tau and promotes its
ubiquitin–proteasome clearance; SELENOW loss impaired synapses, LTP, and memory,
whereas overexpression reduced tau pathology and improved behavior in 3xTg-AD
mice ([Ren et al., 2024](https://doi.org/10.1038/s42003-024-06572-0)).
SELENOW loss also changes redox tone and mitochondrial metabolism in
inflammatory macrophages
([Misra et al., 2023](https://doi.org/10.1016/j.redox.2022.102571)), which
supports mitochondrial plausibility but is not neuronal AD evidence.

**Limits and decisive test.** The 95 calls reuse broad networks, pooled
signatures, and repeated motifs. The covered genes do not define a canonical
ferroptosis signature. Test SELENOW knockdown and rescue in human excitatory
and inhibitory neurons, measuring the prespecified neighborhood, respiration,
redox state, tau handling, and toxicity separately.

## 9. SLC11A1 links microglial lysosomal iron to ACSL1 and SLC25A37 — [Expression-level rediscovery plus new network extension]

**Discovery.** A compact male-ε4 microglial neighborhood positions `SLC11A1`
upstream of `ACSL1` and the mitochondrial iron importer `SLC25A37`.

**Conclusion.** Microglial `SLC11A1` association with AD has already been
reported at the expression level, and its lysosomal-iron transport mechanism
has been demonstrated outside AD. The exact `SLC11A1`–`ACSL1`–`SLC25A37`
relationship is a new, biologically coherent, but statistically narrow Phase
12 hypothesis.

**Data-driven evidence.**

- nine total calls, including three primary and six secondary calls, in two
  microglial fine types;
- the three primary rows contain one independent directional result and two
  derived `AD_both_mito` results;
- the independent `Mic P2RY12`, male-ε4 AD-up call covers `ACSL1` and
  `SLC25A37` in a four-gene layer-1 neighborhood against a 12-gene signature:
  fold enrichment 191.96 and adjusted P = 0.0070;
- `ACSL1` and `SLC25A37` occur in all three primary neighborhoods; and
- one conservative directional call passes the strict screen.

**Prior work and interpretation.** A 2025 bulk/single-cell reanalysis reported
`SLC11A1` upregulation in AD microglia, although the AD single-cell cohort was
small and the study did not perturb the gene
([Zhou et al., 2025](https://doi.org/10.2147/JIR.S497418)). In white-matter
stroke, microglial SLC11A1 acted as an H+/Fe2+ antiporter that accumulated
lysosomal iron; microglia-specific knockdown or inhibition improved debris
clearance and repair
([Qiu et al., 2026](https://doi.org/10.1002/advs.202511482)). `ACSL1`-positive
lipid-droplet microglia are enriched in APOE4/4 AD brain
([Haney et al., 2024](https://doi.org/10.1038/s41586-024-07185-7)), and
SLC25A37 is an established mitochondrial iron importer
([Shaw et al., 2006](https://doi.org/10.1038/nature04512)). Conversely, an
older candidate-gene study found no major LOAD association for `SLC11A1`
([Jamieson et al., 2005](https://doi.org/10.1016/j.neulet.2004.10.038)).

**Limits and decisive test.** The very large enrichment arises from two query
genes in a four-gene neighborhood. `ACSL1` is not the canonical ferroptosis
enzyme `ACSL4`, and no Phase 12 result measures iron, lipid peroxidation, or
cell death. Perturb `SLC11A1` in APOE-isogenic microglia and jointly measure
lysosomal iron, mitochondrial iron, `ACSL1`, `SLC25A37`, phagocytosis, and
respiration.

## 10. LAMTOR5 links neuronal Ragulator signaling to ATP5IF1 — [New Phase 12 hypothesis]

**Discovery.** `LAMTOR5` is a recurrent excitatory/inhibitory candidate whose
primary neighborhoods repeatedly contain `ATP5IF1`.

**Conclusion.** The Ragulator nutrient-sensing mechanism is established, but
the specific neuronal AD `LAMTOR5`–`ATP5IF1` relationship is a new
literature-supported hypothesis. `LAMTOR5` is best viewed as a recurrent local
bridge, not a universal network root.

**Data-driven evidence.**

- 96 total and 38 primary calls across two networks, 15 fine cell types, and
  complete primary self-independence;
- 20 conservative directional calls across 13 fine cell types;
- recurrence in female-ε2 AD-up, female-ε4 AD-down, and male-ε2 AD-down;
- `ATP5IF1` in 28 primary neighborhoods across 11 fine cell types; and
- only 9 of 96 calls marked global.

**Prior work and interpretation.** LAMTOR5 is part of the pentameric Ragulator
complex that controls lysosomal Rag GTPases and amino-acid-sensitive mTORC1
signaling
([Bar-Peled et al., 2012](https://doi.org/10.1016/j.cell.2012.07.032)).
Structural work places the LAMTOR4–LAMTOR5 heterodimer within the
lysosome-anchored complex
([Mu et al., 2017](https://doi.org/10.1038/celldisc.2017.49)). This supplies a
route from nutrient sensing to autophagy, protein synthesis, and mitochondrial
state, but no prior paper located in the targeted review established
`LAMTOR5` upstream of `ATP5IF1` in AD neurons.

**Limits and decisive test.** Ragulator effects are context dependent, KDA
edges have no sign, and only a minority of calls are global. Paired CRISPRi and
CRISPRa should test whether `LAMTOR5` coherently moves `ATP5IF1`, lysosomal
mTORC1, autophagic flux, and respiration without nonspecific toxicity.

## 11. FTL links OPC iron storage to a GPX4-containing mitochondrial program — [New Phase 12 hypothesis]

**Discovery.** `FTL` is a local OPC network candidate whose two independent
directional neighborhoods cover `FTH1`, `GPX4`, OXPHOS genes, and
mitochondrial dynamics/stress genes.

**Conclusion.** Oligodendroglial iron biology and AD ferritin redistribution
are well established, but `FTL` as a sex/APOE-stratified OPC organizer of a
GPX4-containing mitochondrial program is new. The data support an iron/redox
susceptibility hypothesis, not demonstrated ferroptosis.

**Data-driven evidence.**

- 12 total calls, four primary calls, one OPC network, complete primary
  self-independence, and zero global calls;
- female-ε3/ε3 AD-up: 7 of 22 query genes in a 146-gene layer-2 neighborhood,
  fold enrichment 15.53, adjusted P = 1.89×10^-5;
- male-ε2 AD-down: 12 of 81 query genes in a 123-gene layer-2 neighborhood,
  fold enrichment 8.18, adjusted P = 2.09×10^-6; and
- recurrent overlap with `FTH1`, `GPX4`, `COX5B`, `UQCR10`, and `NDUFB5`;
  the male-ε2 neighborhood additionally includes `FIS1`, `SLC25A4`, `PARK7`,
  `ATP5IF1`, `PHB2`, `ATP5MC3`, and `ATP5PF`.

**Prior work and interpretation.** Iron, transferrin, and ferritin are
predominantly oligodendroglial in brain and redistribute around AD plaques
([Connor et al., 1992](https://doi.org/10.1002/jnr.490310111)). H-ferritin
uptake supplies iron to oligodendrocytes
([Todorich et al., 2011](https://doi.org/10.1002/glia.21164)), and ferroxidase
deficiency causes oligodendroglial iron accumulation and oxidative injury
([Chen et al., 2019](https://doi.org/10.1038/s41598-019-46019-9)). Iron
overload lowers GPX4 and induces ferroptotic features in an oligodendrocyte
cell model
([Li et al., 2023](https://doi.org/10.1007/s11064-022-03807-6)). Human AD
cortex also shows altered iron-handling proteins, including increased FTL
([Ashraf et al., 2020](https://doi.org/10.1016/j.redox.2020.101494)).
None of these studies establishes OPC `FTL` as the upstream regulator found
here.

**Limits and decisive test.** FTL may be protective iron sequestration rather
than a pathogenic signal; the two independent calls have opposite AD
directions, and `FTL` is never global. Perturb and rescue `FTL` in OPCs while
measuring labile iron, ferritin, `GPX4`, lipid peroxidation, ferroptosis
sensitivity, mitochondrial function, and differentiation.

## 12. RPL11 links ribosomal stress to mitochondrial neighborhoods — [Established biology plus new network extension]

**Discovery.** `RPL11` is the most consistently upstream, non-mtDNA,
self-independent Phase 12 candidate and connects ribosomal-stress topology to
mitochondrial membrane, import, and RNA-maintenance genes.

**Conclusion.** RPL11 stress signaling and ribosome dysfunction in AD are not
new. The cross-lineage `RPL11`–`APOO`/`TOMM7`/`SLIRP` network relationship is
new and computationally strong, but it remains vulnerable to housekeeping-hub
bias.

**Data-driven evidence.**

- 131 total and 53 primary calls across four networks and 17 fine cell types;
- 118 global calls, complete primary self-independence, and up to 21 covered
  signature genes;
- 29 conservative directional calls across 16 fine cell types and all six
  primary sex/APOE groups;
- `APOO` in 15 primary neighborhoods across seven fine cell types;
- `TOMM7` in four primary neighborhoods across two fine cell types; and
- `SLIRP` in two primary neighborhoods.

**Prior work and interpretation.** RPL11 directly participates in the
ribosomal-stress MDM2–p53 checkpoint
([Zhang et al., 2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003)).
Ribosome dysfunction and RNA oxidation were detected early in human MCI and AD
brain ([Ding et al., 2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005)).
RPL11 protein was also increased in purified AD brain capillaries, although
not in matched parenchyma
([Suzuki et al., 2022](https://doi.org/10.1177/0271678X221111602)). These
findings support a stress interpretation but do not validate a cross-cell
mitochondrial driver.

**Limits and decisive test.** Degree, expression abundance, ribosomal
housekeeping status, and shared broad networks can create stable hubs. Require
degree- and expression-matched empirical nulls and an independent network
before prioritizing an RPL11 perturbation; then separate mitochondrial effects
from general translation arrest and p53 toxicity.

## 13. RPS15 is a recurrent cross-network candidate — [New in AD mitochondrial networks]

**Discovery.** `RPS15` is highly recurrent and completely self-independent,
but is much less often the most upstream nonredundant driver than `RPL11`.

**Conclusion.** The exact RPS15-to-mitochondrial AD topology is new. Prior
stress and neurodegeneration biology makes it plausible, but its low global
fraction and ribosomal-hub risk place it below `RPL11`.

**Data-driven evidence.**

- 123 total and 50 primary calls across five networks and 22 fine cell types;
- 26 conservative directional calls across 19 fine cell types;
- complete primary self-independence and up to 19 covered signature genes; but
- only 23 global calls, or 18.7% of all calls, compared with 90.1% for
  `RPL11`.

**Prior work and interpretation.** RPS15 can bind and inhibit MDM2, stabilize
p53, and promote arrest or death in non-neural models
([Daftuar et al., 2013](https://doi.org/10.1371/journal.pone.0068667)).
In Parkinsonian models, LRRK2-dependent RPS15 phosphorylation contributed to
neuronal toxicity
([Martin et al., 2014](https://doi.org/10.1016/j.cell.2014.01.064)). The
targeted review found no direct AD-specific RPS15 perturbation study.

**Limits and decisive test.** Apply the same matched-null and independent-
network tests as for `RPL11`. Perturbation should include translation rate,
p53, viability, and mitochondrial readouts so a generic ribosomal-stress effect
is not mistaken for a specific mitochondrial mechanism.

## 14. WDR82 links excitatory chromatin regulation to an AD-up mtRNA/OXPHOS motif — [New in AD cell-type networks]

**Discovery.** `WDR82` is an entirely global, excitatory-neuron candidate whose
conservative evidence is restricted to AD-up signatures and repeatedly covers
an mtDNA/OXPHOS motif.

**Conclusion.** WDR82 is not a wholly new biological or AD-network gene:
chromatin recruitment, non-neural mitochondrial effects, and a prior bulk AD
hub nomination exist. Its fine-cell excitatory AD-up placement is the new
Phase 12 hypothesis.

**Data-driven evidence.**

- 70 total calls, 42 primary calls, and all 70 calls global;
- 21 conservative directional calls across 12 of 14 excitatory fine cell
  types;
- complete primary self-independence;
- conservative calls only in AD-up signatures; and
- recurrent coverage of `MT-ND4L`, `MT-ND5`, `MT-ND3`, and `MT-ND1`.

The strongest stratum is female ε3/ε3, followed by female ε2, male ε4, and
male ε3/ε3.

**Prior work and interpretation.** WDR82 recruits SETD1A H3K4-methylation
machinery to transcribed promoters through RNA polymerase II
([Lee and Skalnik, 2008](https://doi.org/10.1128/MCB.01356-07)). A bulk
hippocampal AD expression/PPI reanalysis previously nominated WDR82 as a hub
([Hu et al., 2015](https://doi.org/10.3892/mmr.2015.4271)). Outside neurons,
WDR82 perturbation changes OXPHOS, mitochondrial abundance, membrane potential,
and ROS during reprogramming
([Cui et al., 2023](https://doi.org/10.1007/s00018-023-04871-z)). None of
these establishes the Phase 12 excitatory relationship.

**Limits and decisive test.** Near-identical mtDNA overlaps across related fine
cell types may be repeated queries of one fixed network motif. Test independent
excitatory networks and perturb WDR82 while measuring chromatin occupancy,
mtRNA abundance, OXPHOS expression, respiration, and toxicity.

## 15. Second-line candidate mechanisms

### 15.1 BEX3 links neuronal/OPC death signaling to mitochondrial maintenance — [New in AD networks]

**Discovery.** `BEX3` connects excitatory, inhibitory, and OPC mitochondrial
programs to a neural cell-death signaling protein.

**Conclusion.** Prior work supports BEX3/NADE neural-death biology, but not the
Phase 12 human AD topology. It is a plausible second-line candidate, not a
confirmed AD driver.

**Data-driven evidence.** `BEX3` has 36 total and 13 primary calls across three
networks and seven fine cell types, including 26 global calls and seven
conservative directional calls. Covered genes include `ARMCX3`, `ISCU`,
`TIMM17A`, `MRPL20`, `PSAP`, `PINK1`, and `VDAC2`.

**Prior work and interpretation.** BEX3/NADE participates in p75NTR-associated
death signaling, and its suppression attenuated zinc-triggered cortical-neuron
death; it was also induced after ischemic injury
([Park et al., 2000](https://doi.org/10.1523/JNEUROSCI.20-24-09096.2000)).
This supplies a neural-death mechanism, not direct human AD validation.

**Limits and decisive test.** BEX3 biology can differ across species and
contexts. Test the predicted mitochondrial program alongside p75NTR signaling,
apoptosis threshold, and general toxicity in each nominated cell type.

### 15.2 TMEM147 links excitatory ER/cholesterol machinery to mitochondrial signatures — [New AD network hypothesis]

**Discovery.** `TMEM147` is a recurrent excitatory-neuron candidate whose
neighborhoods contain `PRDX5`, `NDUFB10`, `NDUFB11`, `DBI`, and
`GADD45GIP1`.

**Conclusion.** This is the cleanest new AD–mitochondrial link among the
second-line genes. Prior work establishes ER protein-biogenesis and cholesterol
functions, but no primary AD neuronal/OXPHOS validation was identified.

**Data-driven evidence.** `TMEM147` has 78 total calls, 30 primary calls, five
global calls, and 15 conservative directional calls across ten excitatory fine
cell types. All calls use one broad excitatory network.

**Prior work and interpretation.** TMEM147 interacts with lamin B receptor and
sterol-reductase machinery and affects cholesterol homeostasis
([Christodoulou et al., 2020](https://doi.org/10.1242/jcs.245357)). It is also
part of a ribosome-associated ER multipass translocon
([McGilvray et al., 2020](https://doi.org/10.7554/eLife.56889)). Nicalin, a
TMEM147-complex protein, should not be confused with the γ-secretase component
nicastrin; Phase 12 provides no γ-secretase evidence.

**Limits and decisive test.** The fixed excitatory motif could reflect ER/lipid
coexpression rather than mitochondrial regulation. Perturb TMEM147 and jointly
assay sterol homeostasis, ER translocation, the predicted gene set, and
mitochondrial function.

### 15.3 ANKRD11 marks an OPC iron/mitochondrial program — [New cell-type network hypothesis]

**Discovery.** `ANKRD11` is a narrow but entirely global OPC chromatin
candidate with neighborhoods nearly identical to those of `FTL`.

**Conclusion.** ANKRD11 has established chromatin and neuronal-development
functions, but no direct OPC mitochondrial mechanism. The result may represent
a second upstream control point or an alternative representative of the same
fixed OPC topology.

**Data-driven evidence.** `ANKRD11` has 12 total and four primary calls, all
self-independent and all global. Its two independent directional primary
signals are female-ε3/ε3 AD-up (7/22 overlap, adjusted P = 9.37×10^-5) and
male-ε2 AD-down (13/81 overlap, adjusted P = 8.81×10^-6). Covered genes include
`FTH1`, `GPX4`, `PARK7`, `FIS1`, `ATP5IF1`, and respiratory-chain genes.

**Prior work and interpretation.** ANKRD11 regulates chromatin, neuronal
differentiation, dendrites, and BDNF/TrkB signaling
([Ka and Kim, 2018](https://doi.org/10.1016/j.nbd.2017.12.008)). That biology
does not establish an OPC, iron, or mitochondrial role.

**Limits and decisive test.** Compare `ANKRD11` and `FTL` with conditional and
joint perturbations in OPCs. If their predicted downstream programs are
indistinguishable, network redundancy rather than two independent mechanisms
is the more parsimonious explanation.

### 15.4 HSPA1A–HSPD1 defines a vascular/stress axis — [New, low-confidence hypothesis]

**Discovery.** `HSPA1A` is a self-independent stress candidate whose primary
neighborhoods always contain mitochondrial chaperonin `HSPD1`.

**Conclusion.** The exact HSPA1A–HSPD1 endothelial AD relationship is new but
fragile. A shared upstream heat-shock or proteotoxic-stress response is at
least as plausible as direct HSPA1A control of HSPD1.

**Data-driven evidence.** `HSPA1A` has 20 calls across vascular and inhibitory
networks, ten primary calls, 14 global calls, and `HSPD1` downstream in all ten
primary calls. Only one call passes the conservative directional screen. The
best matched vascular primary result is female-ε4 endothelial AD-down, covering
`MRPS6` and `HSPD1` in a 51-gene layer-3 neighborhood, but the effective query
contains only four genes.

**Prior work and interpretation.** HSPA1A protein was reduced in AD cortical
samples in an APP-processing interactome study
([Gerber et al., 2019](https://doi.org/10.1186/s40478-019-0660-3)), whereas
HSPD1 and other mitochondrial UPR genes were increased in familial and
sporadic AD cortex
([Beck et al., 2016](https://doi.org/10.2174/1567205013666151221145445)).
Those results support stress/proteostasis involvement but not the directed
edge.

**Limits and decisive test.** The call is small-query dependent, HSPA1A is
cytosolic inducible Hsp70 rather than mitochondrial HSPA9, and KDA has no edge
sign. Test paired perturbation in brain endothelial cells with HSF1 activity,
HSPD1, mitochondrial proteostasis, respiration, and barrier function as
separate readouts.

## 16. The previous mitochondrial shortlist becomes a downstream assay panel — [New analytical synthesis]

**Discovery.** Phase 12 frequently positions pre-network mitochondrial
candidates downstream of newly nominated non-mitochondrial or signaling
candidates.

**Conclusion.** The earlier shortlist remains biologically valuable, but its
strongest use is now as a prespecified downstream response panel for driver
perturbations rather than as the default set of upstream targets.

**Data-driven evidence.**

| Upstream Phase 12 candidate | Previous candidate downstream | Primary calls containing the pair | Directional + derived `AD_both_mito` | Fine cell types | Interpretation |
|---|---|---:|---:|---:|---|
| `LAMTOR5` | `ATP5IF1` | 28 | 15 + 13 | 11 | Neuronal lysosome/Ragulator-to-energy hypothesis |
| `GABARAPL2` | `PARK7` | 16 | 9 + 7 | 7 | Autophagic-flux-to-mitochondrial-stress hypothesis |
| `APOE` | `TUFM` | 7 | 4 + 3 | 3 | Astrocyte APOE-to-mitochondrial-translation/metabolism hypothesis |
| `HSPA1A` | `HSPD1` | 10 | 5 + 5 | 5 | Stress-response-to-mitochondrial-proteostasis hypothesis |
| `RPL11` | `APOO` | 15 | 8 + 7 | 7 | Ribosome/stress-to-mitochondrial-membrane hypothesis |
| `RPL11` | `TOMM7` | 4 | 2 + 2 | 2 | Ribosome/stress-to-protein-import hypothesis |
| `ANKRD11` | `ATP5IF1`, `FIS1`, `PARK7` | 2 each | 1 + 1 each | 1 | OPC chromatin-to-energy/dynamics/redox hypothesis |
| `FTL` | `ATP5IF1`, `FIS1`, `PARK7` | 2 each | 1 + 1 each | 1 | OPC iron-to-energy/dynamics/redox hypothesis |

The `AD_both_mito` rows are derived unions that reuse genes from the
directional signatures; they are displayed separately above and must not be
treated as independent confirmations.

`ATP5IF1` is absent from the KDA driver summary. `TUFM` has 39 calls across two
networks but is always a signature member and never global. `PARK7` has only
six KDA calls, three primary calls, one self-independent primary call, and no
call passing the conservative directional screen.

**Prior work and interpretation.** The pre-network evidence is documented in
[`pre_network_prioritization_report.md`](../mt_pathway/pre_network_prioritization_report.md).
Phase 12 does not negate that evidence; it changes the inferred location of
these genes within the proposed regulatory chain.

**Limits and decisive test.** Directed network proximity is not molecular
epistasis. Perturb each proposed upstream candidate and require coherent
movement of several prespecified downstream genes plus mitochondrial function
before adopting the hierarchy.

## 17. Sex/APOE directions nominate stratified tests — [New descriptive hypothesis]

**Discovery.** The strongest candidate patterns differ descriptively across
sex/APOE strata and AD-up versus AD-down signatures.

**Conclusion.** These patterns are useful for choosing validation contexts,
but they are not formal AD-by-sex, AD-by-APOE, or three-way interactions and
must not be presented as genotype-specific causation.

**Data-driven evidence.**

- **Female ε2 AD-up:** `APOE` in astrocytes and `RPL11`, `RPS15`,
  `LAMTOR5`, `SELENOW`, `GABARAPL2`, and `TMEM147` in neurons.
- **Female ε3/ε3 AD-up:** especially `WDR82` in excitatory neurons and
  `FTL`/`ANKRD11` in OPCs.
- **Female ε4 AD-down:** `BEX3`, `LAMTOR5`, `GABARAPL2`, `SELENOW`, and
  `HSPA1A`.
- **Male ε2 AD-down:** the broadest recurrent neuronal and glial pattern,
  including `RPL11`, `RPS15`, `LAMTOR5`, `GABARAPL2`, `BEX3`, `FTL`, and
  `ANKRD11`.
- **Male ε4:** the independent directional microglial `SLC11A1` signal and
  additional astrocyte `APOE` support.

**Prior work and interpretation.** The APOE studies reviewed in Section 6
principally compare APOE4 with APOE3, whereas Phase 12 also highlights ε2
contexts. This mismatch is informative: validation should compare APOE2,
APOE3, and APOE4 rather than reduce every finding to an APOE4 effect.

**Limits and decisive test.** Donor number, power, query size, and eligible
network coverage differ by group. Fine cell types reuse broad networks, and
`AD_both_mito` reuses directional genes. Fit donor-aware formal interaction
models before making sex- or APOE-specific claims.

## 18. Cell-type control systems converge on a respiratory core — [New integrative hypothesis]

**Discovery.** The prioritized results separate into cell-type-specific
control systems that converge on the same respiratory-chain phenotype:
astrocyte lipid/metabolic support, neuronal lysosome/autophagy, glial
iron/redox handling, and transcription/translation/proteostasis stress.

**Conclusion.** The parsimonious model is not one universal AD driver. It is a
set of cell-type-specific upstream systems converging on a recurrent
mitochondrial core. This is an organizing hypothesis, not a causal pathway
diagram.

**Data-driven evidence.**

| Network | Most useful candidates | Interpretation |
|---|---|---|
| Astrocytes | `APOE`, `RPL11` | APOE links to `TUFM`, `LDHB`, ATP-synthase, and dynamics/metabolism genes. |
| Excitatory neurons | `RPL11`, `WDR82`, `SELENOW`, `GABARAPL2`, `TMEM147`, `LAMTOR5` | Transcription/translation, redox, lysosome–autophagy, and ER/lipid control. |
| Inhibitory neurons | `RPS15`, `LAMTOR5`, `BEX3`, `HSPA1A` | Strong male-ε2 and female-ε4 AD-down structure. |
| Microglia | `SLC11A1`, `RPL11` | Lysosomal iron and ribosome/redox hypotheses, with limited eligible breadth. |
| OPCs | `FTL`, `ANKRD11`, `RPS15`, `BEX3` | Iron/redox and chromatin hypotheses in two principal directional contexts. |
| Oligodendrocytes | `RPL11` | Clearest multi-gene, self-independent nuclear candidate. |
| Vasculature | `HSPA1A` | Stress/proteostasis hypothesis, but small-query dependent. |
| CAMs | None evaluated | No eligible KDA run. |
| T cells | None evaluated | No eligible KDA run. |

The four mechanistic axes are:

1. **Astrocyte lipid/metabolic support:** `APOE` to `TUFM`, `LDHB`,
   `CHCHD10`, `ATP5PB`, and `ATP5F1A`.
2. **Lysosome/nutrient sensing/autophagy:** `LAMTOR5` and `GABARAPL2` to
   `ATP5IF1`, `CHCHD2`, `PARK7`, mitoribosomal genes, and OXPHOS subunits.
3. **Iron/selenium/redox:** `FTL`, `SLC11A1`, and `SELENOW` to `GPX4`,
   `FTH1`, `SLC25A37`, `ACSL1`, `FIS1`, and respiratory genes.
4. **Chromatin/ribosome/proteostasis stress:** `WDR82`, `RPL11`, `RPS15`,
   `ANKRD11`, `TMEM147`, and `HSPA1A`.

**Prior work and interpretation.** The ability of broader multiscale AD KDA
to generate experimentally testable hypotheses is demonstrated by VGF
validation
([Beckmann et al., 2020](https://doi.org/10.1038/s41467-020-17405-z)).
Phase 12 is narrower and has not integrated genetics or perturbation evidence
to the same degree.

The `PLCG2` result illustrates why coherence matters. The protective P522R
allele is a functional hypermorph
([Magno et al., 2019](https://doi.org/10.1186/s13195-019-0469-0)), yet all 28
Phase 12 `PLCG2` calls are in the inhibitory-neuron network and cover only one
query gene. This is not a convincing mitochondrial KDA confirmation.

**Limits and decisive test.** Among a panel of established AD genes, only
`APOE` and `PLCG2` appear in the KDA summary, and `VGF` is absent. That does not
refute the missing genes; Phase 12 asks the narrower question of core
mitochondrial DEG neighborhoods. The integrated model becomes credible only
if candidate perturbations reproduce multi-gene neighborhoods, mitochondrial
phenotypes, AD-relevant outcomes, and the predicted cell-type context.

## 19. Limitations that must accompany paper claims

### 19.1 Statistical scope

- BH adjustment is performed **within each KDA run**, not across 1,782 runs.
- The result table contains only significant candidates, so a valid
  phase-wide BH correction cannot be reconstructed from it.
- The algorithm selects the smallest raw P value across up to three layers and
  does not separately correct for layer selection.
- `minimum_adjusted_p_value` in the summary is the minimum of within-run values
  and is not a meta-analysis P value.

### 19.2 Dependence

- AD-up and AD-both signatures overlap by construction.
- Secondary pools reuse primary signatures and overlap with one another.
- Fine cell types within a broad lineage reuse the same broad network.
- Recurrent calls are therefore robustness observations, not independent
  replications.

### 19.3 Network interpretation

- Bayesian-network direction is a probabilistic orientation, not experimental
  proof of molecular causation.
- Edges do not encode activation versus inhibition.
- A significant driver need not be differentially expressed.
- A driver can be a query member and receive a self-overlap.
- Generic high-expression or high-connectivity genes can become stable network
  hubs.
- `global_key_driver` is only a within-run redundancy flag.
- Most broad networks lack complete local provenance for construction priors,
  edge weights, and edge-support sensitivity.

### 19.4 Biological scope

- The query universe is restricted to `core_mito_protein`; drivers of broader
  mitochondrial-related or non-mitochondrial AD programs can be missed.
- CAMs and T cells had no eligible run.
- Very small queries generate fragile, high-enrichment calls.
- Postmortem expression can reflect disease consequence, cell state, agonal
  factors, and treatment rather than disease initiation.
- Phase 08 evidence is not a donor-level, independent replication or a formal
  sex/APOE interaction analysis.
- Human genetics, colocalized eQTLs, protein data, and perturbation results have
  not yet been integrated for most nominated genes.

The paper should consistently use **putative key driver**, **candidate upstream
regulator**, or **network-nominated driver**.

## 20. Recommended confirmation analyses

### 20.1 Computational validation

1. **Degree- and expression-matched empirical nulls.** For each top
   candidate–run pair, compare the observed enrichment with randomized
   signatures matched for query size, network degree, mitochondrial
   annotation, and expression abundance.
2. **Candidate-exclusion rerun.** Exclude signature genes from the candidate
   set before testing and rerun BH correction, rather than filtering
   significant rows afterward.
3. **Layer sensitivity.** Analyze fixed one-, two-, and three-layer profiles
   and account explicitly for searching multiple layers.
4. **Network sensitivity.** Test edge reversal/uncertain-edge removal,
   alternative Bayesian-network realizations, and, where available,
   weight-supported edges.
5. **Independent KDA engine.** Use the separately maintained Wang KDA 0.2
   implementation as a labeled validation profile.
6. **Query-universe sensitivity.** Compare `core_mito_protein` with the broader
   mitochondrial-related universe.
7. **mtDNA-candidate sensitivity.** Keep mtDNA genes in the signature but
   exclude them as candidate drivers to determine whether nuclear upstream
   rankings remain stable.
8. **Donor-level validation.** Re-estimate the underlying AD signatures with
   donor-aware pseudobulk or mixed models and formal interaction terms.
9. **Genetic triangulation.** Add AD GWAS, cell-type eQTL, colocalization,
   Mendelian-randomization where appropriate, and rare-variant evidence.
10. **External network replication.** Confirm the top neighborhood
    relationships in an independently inferred cell-type network.

### 20.2 Experimental validation

Because edge sign is unknown, the safest design is paired CRISPRi and CRISPRa
or knockdown and rescue, rather than assuming that inhibition is therapeutic.

| Cell system | Candidate perturbations | Priority readouts |
|---|---|---|
| Isogenic APOE astrocytes | `APOE` isoform replacement, knockdown, and rescue | respiration, ATP, glycolytic/TCA flux, mitophagy, mitochondrial morphology, `TUFM`, `LDHB`, `CHCHD10` |
| Excitatory neurons | `LAMTOR5`, `GABARAPL2`, `WDR82`, `SELENOW`, `TMEM147`, `RPL11` | lysosomal mTORC1, autophagic flux, mitophagy, OXPHOS, membrane potential, ROS, `ATP5IF1`, `PARK7`, candidate-specific downstream genes |
| Inhibitory neurons | `LAMTOR5`, `RPS15`, `BEX3`, `HSPA1A` | mitochondrial respiration, proteostasis, apoptosis threshold, direction-specific downstream panel |
| OPCs / differentiating oligodendroglia | `FTL`, `ANKRD11`, `RPS15`, `BEX3` | labile iron, ferritin, lipid peroxidation, GPX4, ferroptosis sensitivity, differentiation/myelination, mitochondrial respiration |
| Microglia | `SLC11A1`, `RPL11` | lysosomal iron, `SLC25A37`, `ACSL1`, phagocytosis, inflammatory state, mitochondrial respiration |
| Endothelial/vascular cells | `HSPA1A` | mitochondrial proteostasis, barrier function, `HSPD1`, `MRPS6`, respiration |

The most informative experiment is not merely whether perturbation changes one
downstream transcript. It is whether perturbing the candidate:

1. moves several prespecified Phase 12 overlap genes in the expected coherent
   direction;
2. changes mitochondrial function;
3. rescues or worsens an AD-relevant phenotype;
4. does so in the predicted cell type; and
5. shows the predicted APOE/sex context without being explained by general
   toxicity.

## 21. Paper-ready interpretation

### Results language

> Cell-type-matched directed-network enrichment analysis identified a
> recurrent respiratory-chain core across seven broad brain-cell networks.
> Because mtDNA and structural OXPHOS genes frequently belonged to the queried
> signatures, we applied a conservative prioritization requiring primary,
> direction-specific, non-mtDNA, non-self, multi-gene calls from signatures of
> at least ten genes. This highlighted cross-network ribosomal-stress
> candidates RPL11 and RPS15; excitatory-neuron WDR82, SELENOW, GABARAPL2, and
> TMEM147; neuronal LAMTOR5; astrocytic APOE; OPC FTL and ANKRD11; and
> microglial SLC11A1. APOE, GABARAPL2, SELENOW, and SLC11A1 independently
> recapitulated prior disease or cell-biological evidence while adding new
> directed mitochondrial neighborhoods. LAMTOR5–ATP5IF1, OPC FTL, RPS15, the
> excitatory WDR82 motif, and the second-line candidates remained new
> network-level hypotheses requiring independent validation.

### Discussion language

> The KDA results support a model in which cell-type-specific lipid,
> lysosome–autophagy, iron/redox, and transcription/translation-stress
> pathways converge on a common mitochondrial respiratory program in AD.
> Several pre-network mitochondrial candidates were repositioned as downstream
> readouts: ATP5IF1 occurred repeatedly downstream of LAMTOR5, TUFM downstream
> of astrocytic APOE, and PARK7 downstream of GABARAPL2. GABARAPL2 also
> repeatedly covered CHCHD2, a relationship now supported by independent
> GABARAP-family interaction experiments. HSPD1 occurred downstream of HSPA1A,
> although a shared stress response remains an alternative explanation. These
> directed-neighborhood enrichments nominate regulatory
> hypotheses but do not establish causal edge direction or therapeutic effect,
> because multiple-testing control was within each run, fine-cell signatures
> reused broad networks, and pooled and union signatures were not independent.

## 22. Reproducibility pointers

Primary source tables:

- [`kda_status.tsv`](../../../results/minerva_production/12_kda/kda_status.tsv)
- [`kda_checks.tsv`](../../../results/minerva_production/12_kda/kda_checks.tsv)
- [`kda_run_manifest.tsv`](../../../results/minerva_production/12_kda/kda_run_manifest.tsv)
- [`kda_results.tsv.gz`](../../../results/minerva_production/12_kda/kda_results.tsv.gz)
- [`kda_key_driver_summary.tsv`](../../../results/minerva_production/12_kda/kda_key_driver_summary.tsv)
- [`kda_signature_members.tsv.gz`](../../../results/minerva_production/12_kda/kda_signature_members.tsv.gz)
- [`kda_background_members.tsv.gz`](../../../results/minerva_production/12_kda/kda_background_members.tsv.gz)

Reviewed method/configuration:

- [`config/phase12_kda.yml`](../../../config/phase12_kda.yml)
- [`scripts/12_run_kda.R`](../../../scripts/12_run_kda.R)
- [`scripts/NetWeaver/fKDA.R`](../../../scripts/NetWeaver/fKDA.R)
- [`phase_12_kda_plan.md`](../../phase_12_kda/phase_12_kda_plan.md)

Related explanations:

- [`phase12_minerva_kda_results_sanity_check.md`](phase12_minerva_kda_results_sanity_check.md)
- [`call_key_drivers_explained.md`](call_key_drivers_explained.md)
- [`phase12_kda_results_explained.md`](phase12_kda_results_explained.md)
- [`phase12_kda_circular_figure_explained.md`](phase12_kda_circular_figure_explained.md)

## 23. References

- Ashraf A, Jeandriens J, Parkes HG, So PW. Iron dyshomeostasis, lipid
  peroxidation and perturbed expression of cystine/glutamate antiporter in
  Alzheimer's disease: evidence of ferroptosis. *Redox Biology*. 2020;32:101494.
  [doi:10.1016/j.redox.2020.101494](https://doi.org/10.1016/j.redox.2020.101494).
- Bar-Peled L, Schweitzer LD, Zoncu R, Sabatini DM. Ragulator is a GEF for the
  Rag GTPases that signal amino acid levels to mTORC1. *Cell*.
  2012;150(6):1196–1208.
  [doi:10.1016/j.cell.2012.07.032](https://doi.org/10.1016/j.cell.2012.07.032).
- Beck JS, Mufson EJ, Counts SE. Evidence for mitochondrial UPR gene activation
  in familial and sporadic Alzheimer's disease. *Current Alzheimer Research*.
  2016;13(6):610–614.
  [doi:10.2174/1567205013666151221145445](https://doi.org/10.2174/1567205013666151221145445).
- Beckmann ND, Lin WJ, Wang M, et al. Multiscale causal networks identify VGF as
  a key regulator of Alzheimer's disease. *Nature Communications*. 2020;11:3942.
  [doi:10.1038/s41467-020-17405-z](https://doi.org/10.1038/s41467-020-17405-z).
- Chen Z, Jiang R, Chen M, et al. Multi-copper ferroxidase deficiency leads to
  iron accumulation and oxidative damage in astrocytes and oligodendrocytes.
  *Scientific Reports*. 2019;9:9437.
  [doi:10.1038/s41598-019-46019-9](https://doi.org/10.1038/s41598-019-46019-9).
- Christodoulou A, Maimaris G, Makrigiorgi A, et al. TMEM147 interacts with
  lamin B receptor, regulates its localization and levels, and affects
  cholesterol homeostasis. *Journal of Cell Science*. 2020;133(16):jcs245357.
  [doi:10.1242/jcs.245357](https://doi.org/10.1242/jcs.245357).
- Connor JR, Menzies SL, St Martin SM, Mufson EJ. A histochemical study of iron,
  transferrin, and ferritin in Alzheimer's diseased brains. *Journal of
  Neuroscience Research*. 1992;31(1):75–83.
  [doi:10.1002/jnr.490310111](https://doi.org/10.1002/jnr.490310111).
- Cui G, Zhou J, Sun J, et al. WD repeat domain 82 (Wdr82) facilitates mouse
  iPSCs generation by interfering mitochondrial oxidative phosphorylation and
  glycolysis. *Cellular and Molecular Life Sciences*. 2023;80(8):218.
  [doi:10.1007/s00018-023-04871-z](https://doi.org/10.1007/s00018-023-04871-z).
- Daftuar L, Zhu Y, Jacq X, Prives C. Ribosomal proteins RPL37, RPS15 and RPS20
  regulate the Mdm2-p53-MdmX network. *PLOS ONE*. 2013;8(7):e68667.
  [doi:10.1371/journal.pone.0068667](https://doi.org/10.1371/journal.pone.0068667).
- Dai X, Ye Z, Wang C, et al. SIK2-mediated phosphorylation of GABARAPL2
  facilitates autophagosome–lysosome fusion and rescues neurodegeneration in an
  Alzheimer's disease model. *Translational Neurodegeneration*. 2025;14:53.
  [doi:10.1186/s40035-025-00514-4](https://doi.org/10.1186/s40035-025-00514-4).
- Ding Q, Markesbery WR, Chen Q, Li F, Keller JN. Ribosome dysfunction is an
  early event in Alzheimer's disease. *Journal of Neuroscience*.
  2005;25(40):9171–9175.
  [doi:10.1523/JNEUROSCI.3040-05.2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005).
- Gerber H, Mosser S, Boury-Jamot B, et al. The APMAP interactome reveals new
  modulators of APP processing and beta-amyloid production that are altered in
  Alzheimer's disease. *Acta Neuropathologica Communications*. 2019;7:13.
  [doi:10.1186/s40478-019-0660-3](https://doi.org/10.1186/s40478-019-0660-3).
- Haney MS, Pálovics R, Munson CN, et al. APOE4/4 is linked to damaging lipid
  droplets in Alzheimer's disease microglia. *Nature*. 2024;628(8006):154–161.
  [doi:10.1038/s41586-024-07185-7](https://doi.org/10.1038/s41586-024-07185-7).
- Hu W, Lin X, Chen K. Integrated analysis of differential gene expression
  profiles in hippocampi to identify candidate genes involved in Alzheimer's
  disease. *Molecular Medicine Reports*. 2015;12(5):6679–6687.
  [doi:10.3892/mmr.2015.4271](https://doi.org/10.3892/mmr.2015.4271).
- Jamieson SE, White JK, Howson JMM, et al. Candidate gene association study of
  solute carrier family 11a members 1 (SLC11A1) and 2 (SLC11A2) genes in
  Alzheimer's disease. *Neuroscience Letters*. 2005;374(2):124–128.
  [doi:10.1016/j.neulet.2004.10.038](https://doi.org/10.1016/j.neulet.2004.10.038).
- Ka M, Kim WY. ANKRD11 associated with intellectual disability and autism
  regulates dendrite differentiation via the BDNF/TrkB signaling pathway.
  *Neurobiology of Disease*. 2018;111:138–152.
  [doi:10.1016/j.nbd.2017.12.008](https://doi.org/10.1016/j.nbd.2017.12.008).
- Lee JH, Skalnik DG. Wdr82 is a C-terminal domain-binding protein that recruits
  the Setd1A histone H3-Lys4 methyltransferase complex to transcription start
  sites of transcribed human genes. *Molecular and Cellular Biology*.
  2008;28(2):609–618.
  [doi:10.1128/MCB.01356-07](https://doi.org/10.1128/MCB.01356-07).
- Li Y, Wang B, Yang J, Liu R, Xie J, Wang J. Iron overload causes ferroptosis
  but not apoptosis in MO3.13 oligodendrocytes. *Neurochemical Research*.
  2023;48(3):830–838.
  [doi:10.1007/s11064-022-03807-6](https://doi.org/10.1007/s11064-022-03807-6).
- Liang WS, Reiman EM, Valla J, et al. Alzheimer's disease is associated with
  reduced expression of energy metabolism genes in posterior cingulate
  neurons. *Proceedings of the National Academy of Sciences USA*.
  2008;105(11):4441–4446.
  [doi:10.1073/pnas.0709259105](https://doi.org/10.1073/pnas.0709259105).
- Magno L, Lessard CB, Martins M, et al. Alzheimer's disease phospholipase
  C-gamma-2 (PLCG2) protective variant is a functional hypermorph. *Alzheimer's
  Research & Therapy*. 2019;11:16.
  [doi:10.1186/s13195-019-0469-0](https://doi.org/10.1186/s13195-019-0469-0).
- Martin I, Kim JW, Lee BD, et al. Ribosomal protein S15 phosphorylation
  mediates LRRK2 neurodegeneration in Parkinson's disease. *Cell*.
  2014;157(2):472–485.
  [doi:10.1016/j.cell.2014.01.064](https://doi.org/10.1016/j.cell.2014.01.064).
- McGilvray PT, Anghel SA, Sundaram A, et al. An ER translocon for multi-pass
  membrane protein biogenesis. *eLife*. 2020;9:e56889.
  [doi:10.7554/eLife.56889](https://doi.org/10.7554/eLife.56889).
- Misra S, Lee TJ, Sebastian A, et al. Loss of selenoprotein W in murine
  macrophages alters the hierarchy of selenoprotein expression, redox tone, and
  mitochondrial functions during inflammation. *Redox Biology*. 2023;59:102571.
  [doi:10.1016/j.redox.2022.102571](https://doi.org/10.1016/j.redox.2022.102571).
- Mu Z, Wang L, Deng W, Wang J, Wu G. Structural insight into the Ragulator
  complex which anchors mTORC1 to the lysosomal membrane. *Cell Discovery*.
  2017;3:17049.
  [doi:10.1038/celldisc.2017.49](https://doi.org/10.1038/celldisc.2017.49).
- Pan W, Yang L, Zhang Y, et al. Neuronal YTHDF2 suppresses innate immune
  activation in Aβ pathology by promoting m6A-dependent decay of cytosolic
  mitochondrial mRNAs. *Science Advances*. 2026;12(25):eadz0887.
  [doi:10.1126/sciadv.adz0887](https://doi.org/10.1126/sciadv.adz0887).
- Park JA, Lee JY, Sato TA, Koh JY. Co-induction of p75NTR and
  p75NTR-associated death executor in neurons after zinc exposure in cortical
  culture or transient ischemia in the rat. *Journal of Neuroscience*.
  2000;20(24):9096–9103.
  [doi:10.1523/JNEUROSCI.20-24-09096.2000](https://doi.org/10.1523/JNEUROSCI.20-24-09096.2000).
- Qi G, Mi Y, Shi X, Gu H, Brinton RD, Yin F. ApoE4 impairs neuron-astrocyte
  coupling of fatty acid metabolism. *Cell Reports*. 2021;34(1):108572.
  [doi:10.1016/j.celrep.2020.108572](https://doi.org/10.1016/j.celrep.2020.108572).
- Qiu L, Zhang Y, Tang Y, et al. Inhibition of SLC11A1-mediated lysosomal iron
  accumulation in microglia promotes repair following white matter stroke.
  *Advanced Science*. 2026;13(19):e11482.
  [doi:10.1002/advs.202511482](https://doi.org/10.1002/advs.202511482).
- Ren B, Situ J, Huang X, et al. Selenoprotein W modulates tau homeostasis in an
  Alzheimer's disease mouse model. *Communications Biology*. 2024;7:872.
  [doi:10.1038/s42003-024-06572-0](https://doi.org/10.1038/s42003-024-06572-0).
- Rice AC, Ladd AC, Bennett JP Jr. Postmortem Alzheimer's disease hippocampi
  show oxidative phosphorylation gene expression opposite that of isolated
  pyramidal neurons. *Journal of Alzheimer's Disease*. 2015;45(4):1051–1059.
  [doi:10.3233/JAD-142937](https://doi.org/10.3233/JAD-142937).
- Schmukler E, Solomon S, Simonovitch S, et al. Altered mitochondrial dynamics
  and function in APOE4-expressing astrocytes. *Cell Death & Disease*.
  2020;11:578.
  [doi:10.1038/s41419-020-02776-4](https://doi.org/10.1038/s41419-020-02776-4).
- Shaw GC, Cope JJ, Li L, et al. Mitoferrin is essential for erythroid iron
  assimilation. *Nature*. 2006;440(7080):96–100.
  [doi:10.1038/nature04512](https://doi.org/10.1038/nature04512).
- Suzuki M, Tezuka K, Handa T, et al. Upregulation of ribosome complexes at the
  blood-brain barrier in Alzheimer's disease patients. *Journal of Cerebral
  Blood Flow & Metabolism*. 2022;42(11):2134–2150.
  [doi:10.1177/0271678X221111602](https://doi.org/10.1177/0271678X221111602).
- Todorich B, Zhang X, Connor JR. H-ferritin is the major source of iron for
  oligodendrocytes. *Glia*. 2011;59(6):927–935.
  [doi:10.1002/glia.21164](https://doi.org/10.1002/glia.21164).
- Wang H, Sun HQ, Zhu X, et al. GABARAPs regulate PI4P-dependent
  autophagosome:lysosome fusion. *Proceedings of the National Academy of
  Sciences USA*. 2015;112(22):7015–7020.
  [doi:10.1073/pnas.1507263112](https://doi.org/10.1073/pnas.1507263112).
- Williams HC, Farmer BC, Piron MA, et al. APOE alters glucose flux through
  central carbon pathways in astrocytes. *Neurobiology of Disease*.
  2020;136:104742.
  [doi:10.1016/j.nbd.2020.104742](https://doi.org/10.1016/j.nbd.2020.104742).
- Zhang Y, Wolf GW, Bhat K, et al. Ribosomal protein L11 negatively regulates
  oncoprotein MDM2 and mediates a p53-dependent ribosomal-stress checkpoint
  pathway. *Molecular and Cellular Biology*. 2003;23(23):8902–8912.
  [doi:10.1128/MCB.23.23.8902-8912.2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003).
- Zhou H, Peng Y, Huo X, et al. Integrating bulk and single-cell transcriptomic
  data to identify ferroptosis-associated inflammatory gene in Alzheimer's
  disease. *Journal of Inflammation Research*. 2025;18:2105–2122.
  [doi:10.2147/JIR.S497418](https://doi.org/10.2147/JIR.S497418).
- Zhou W, Zhang MM, Tang W, et al. CHCHD2 and CHCHD10 promoted autophagic
  clearance of protein aggregates via GABARAPs. *Autophagy*. 2026:1–30.
  [doi:10.1080/15548627.2026.2678427](https://doi.org/10.1080/15548627.2026.2678427).
