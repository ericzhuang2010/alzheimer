# Phase 12 key-driver analysis: driver-gene prioritization and biological interpretation

**Analysis date:** 2026-07-30  
**Production output:** [`results/minerva_production/12_kda/`](../../../results/minerva_production/12_kda/)  
**Scope:** cell-type-, sex-, and APOE-stratified key-driver analysis (KDA) of
Alzheimer's disease (AD)-associated core mitochondrial gene signatures

## Executive conclusion

Phase 12 is technically complete and suitable for hypothesis generation. It
does **not**, by itself, establish causal AD drivers. The appropriate
interpretation is that a reported gene is a **putative key driver whose
directed downstream Bayesian-network neighborhood is enriched for a particular
mitochondrial AD signature**.

The unfiltered output is dominated by mtDNA and structural oxidative
phosphorylation (OXPHOS) genes. This is a biologically meaningful indication
that respiratory-chain programs form the center of the Phase 12 signal, but it
is not automatically evidence that these genes are tractable upstream
regulators. A conservative analysis that emphasizes primary rather than pooled
runs, excludes the derived `AD_both_mito` signature, removes mtDNA drivers and
driver self-overlap, requires at least two covered signature genes, and
requires a query of at least ten genes produces a more useful regulatory
shortlist.

The most important findings are:

1. **`APOE` is the strongest disease-anchored, cell-type-matched candidate.**
   It is an astrocyte driver in 20 total calls, including seven primary calls,
   all of which are independent of driver self-membership. Four conservative
   directional calls span three astrocyte subtypes and the female-ε2,
   male-ε2, and male-ε4 groups. `TUFM`, a leading pre-network mitochondrial
   candidate, is downstream of `APOE` in all seven primary `APOE` calls.
2. **`LAMTOR5` and `GABARAPL2` define a recurrent neuronal
   lysosome–autophagy axis.** `LAMTOR5` has 96 calls, including 38 primary
   calls across excitatory and inhibitory networks; 20 conservative
   directional calls span 13 fine cell types. Its neighborhoods contain
   `ATP5IF1` in 28 primary calls across 11 fine cell types. `GABARAPL2` has 79
   calls, including 32 primary calls, and its neighborhoods contain `PARK7` in
   16 primary calls.
3. **`FTL` and `SLC11A1` nominate cell-type-specific iron-handling programs.**
   `FTL` is a high-overlap OPC driver in female-ε3/ε3 AD-up and male-ε2
   AD-down signatures. `SLC11A1` is a microglial driver centered on `ACSL1`
   and the mitochondrial iron importer `SLC25A37`. These results support an
   iron/redox/ferroptosis hypothesis, but each signal is confined to one broad
   network and needs replication.
4. **`RPL11` is the strongest purely topology-derived upstream candidate.**
   It has 131 calls, 53 primary calls, 17 fine cell types, four broad networks,
   no driver self-overlap, and 118 within-run global calls. Twenty-nine
   conservative directional calls span 16 fine cell types and all six primary
   groups. Its recurrence is compelling, but the abundance of ribosomal
   drivers also raises a network-hub and cellular-stress interpretation that
   must be tested before calling `RPL11` an AD-specific regulator.
5. **`WDR82` and `SELENOW` are strong novel neuronal hypotheses.** `WDR82` is
   a completely global excitatory-neuron AD-up driver, with 42 primary calls
   and 21 conservative directional calls across 12 fine cell types. `SELENOW`
   has 95 calls across excitatory and inhibitory networks, 89 of them global,
   and 16 conservative directional calls. Neither yet has evidence in this
   dataset equivalent to causal perturbation or human AD genetics.
6. **`RPS15`, `BEX3`, `TMEM147`, and `ANKRD11` are valuable second-line
   candidates.** `RPS15` is exceptionally recurrent and self-independent but
   is usually not the most upstream significant driver. `BEX3` crosses three
   networks and links neuronal/OPC mitochondrial programs to a known cell-death
   signaling protein. `TMEM147` is a recurrent excitatory-neuron candidate
   with plausible lipid/ER biology. `ANKRD11` is a highly significant,
   within-run global OPC candidate, but is supported by only two independent
   directional primary signatures.
7. **The previous mitochondrial shortlist is better treated as a downstream
   assay panel than as the final driver list.** `ATP5IF1`, `TUFM`, `HSPD1`,
   and `PARK7` remain biologically useful, but Phase 12 more often places them
   downstream of newly nominated regulators than at the top of the network.

If experimental capacity is limited, a balanced first-pass panel is:

> **`APOE`, `LAMTOR5`, `GABARAPL2`, `FTL`, `SLC11A1`, `RPL11`, `WDR82`, and
> `SELENOW`.**

This panel deliberately balances established AD relevance, cell-type
specificity, recurrence, mechanistic diversity, and novelty. `BEX3`,
`TMEM147`, `ANKRD11`, and `RPS15` form a second tier. `HSPA1A` is a useful
vascular/stress candidate but is supported mainly by small signatures.

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
([Beckmann et al., 2020](https://www.nature.com/articles/s41467-020-17405-z)).

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

## 4. Dominant raw signal: respiratory-chain hubs

The unfiltered recurrence ranking is led by:

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

Nuclear OXPHOS genes show the same pattern. For example, `COX4I1` has 169
calls across five networks and 21 fine cell types, but it is a query member in
149 calls. `COX7C`, `UQCR10`, `COX6B1`, and `COX7B` are also recurrent and
mostly self-containing.

The defensible conclusion is:

> Phase 12 robustly identifies a recurrent, directed respiratory-chain
> subnetwork associated with AD mitochondrial signatures.

The stronger claim that mtDNA or structural OXPHOS subunits are upstream
causal AD regulators is not established. These genes are better treated as
sentinels and molecular readouts unless a non-self, multi-target network effect
is independently validated.

`MT-CO2` is the notable exception within this class: 203 of its 550 calls do
not contain `MT-CO2` itself, and it is marked global in 505 calls. This makes
it an important network organizer, but its repeated placement within tightly
coexpressed mtDNA neighborhoods still requires an mtRNA-abundance and network
topology sensitivity analysis.

## 5. Prioritized non-mtDNA candidates

### 5.1 Evidence matrix

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

The table is intentionally not converted into a single composite score. A
score would obscure the distinction between:

- broad computational recurrence;
- within-run upstream position;
- cell-type specificity;
- disease-specific prior evidence; and
- experimental tractability.

### 5.2 `APOE`: highest combined biological priority

`APOE` is supported by:

- 20 total astrocyte calls;
- seven primary calls across all three astrocyte fine types;
- no primary self-membership;
- four conservative directional calls;
- three to five covered mitochondrial genes per conservative call; and
- primary directions spanning female-ε2 AD-up, male-ε2 AD-down, and male-ε4
  AD-down.

Representative primary neighborhoods include:

- `Ast GRM3`, male-ε2 AD-down: `ATP5PB`, `LDHB`, `TUFM`, `ATP5F1A`, and `AGT`;
- `Ast DPP10`, male-ε2 AD-down: `ATP5PB`, `LDHB`, `TUFM`, and `AGT`; and
- `Ast GRM3`, female-ε2 AD-up: `LDHB`, `TUFM`, and `CHCHD10`.

This is particularly convincing because `APOE` is not merely rediscovered as
a query gene. Its outgoing network neighborhood covers a compact mitochondrial
program.

Independent experiments have shown APOE isoform-dependent changes in
astrocyte mitochondrial dynamics, mitophagy, and function
([Schmukler et al., 2020](https://pubmed.ncbi.nlm.nih.gov/32709881/)) and
astrocyte central-carbon metabolism
([Farmer et al., 2019/2020](https://pubmed.ncbi.nlm.nih.gov/31931141/)).
These external results are consistent with the Phase 12 astrocyte finding.

The Phase 12 pattern is **not exclusively ε4**. Experimental work should
therefore compare APOE isoforms and the direction of the corresponding
mitochondrial program rather than interpreting the result simply as an
APOE4 effect.

### 5.3 `LAMTOR5`: recurrent neuronal nutrient-sensing bridge

`LAMTOR5` is one of the most coherent novel candidates:

- 96 total and 38 primary calls;
- excitatory and inhibitory networks;
- 15 fine cell types;
- 20 conservative directional calls in 13 fine cell types;
- recurrence in female-ε2 AD-up, female-ε4 AD-down, and male-ε2 AD-down; and
- multi-gene neighborhoods containing `ATP5IF1` in 28 primary calls across 11
  fine cell types.

`LAMTOR5` is a component of the lysosomal Ragulator complex, which recruits
Rag GTPases and mTORC1 to the lysosome during nutrient sensing
([Sancak et al., 2010](https://pubmed.ncbi.nlm.nih.gov/20381137/);
[Mu et al., 2017](https://pubmed.ncbi.nlm.nih.gov/29285400/)).
That function gives a plausible route from lysosomal nutrient sensing to
autophagy, protein synthesis, and mitochondrial metabolic state.

Only 9 of 96 `LAMTOR5` calls are labeled global. Thus, `LAMTOR5` is best
described as a recurrent **local mechanistic bridge**, not consistently the
most upstream representative in a run.

### 5.4 `GABARAPL2`: excitatory autophagic-flux candidate

`GABARAPL2` has:

- 79 total and 32 primary calls;
- 17 conservative directional calls across 11 fine cell types;
- strongest recurrence in excitatory neurons;
- support in female-ε2 AD-up, female-ε4 AD-down, male-ε2 up and down,
  male-ε3/ε3 down, and male-ε4 up; and
- `PARK7` in its neighborhood in 16 primary calls across seven fine cell
  types.

Representative neighborhoods cover `CHCHD2`, `ATP5MC3`, `PARK7`, `BAX`,
mitochondrial ribosomal genes, and iron-sulfur genes. The pattern links
autophagosome machinery to mitochondrial maintenance rather than merely
capturing a structural OXPHOS subunit.

Recent experimental work reported that phosphorylation of GABARAPL2 promotes
autophagosome–lysosome fusion and that a phosphomimetic GABARAPL2 construct
improved amyloid and synaptic phenotypes in 5xFAD mice
([Dai et al., 2025](https://pubmed.ncbi.nlm.nih.gov/41126299/)). That study is
independent of Phase 12 and substantially strengthens the biological
plausibility of this candidate.

### 5.5 `FTL` and `SLC11A1`: complementary glial iron programs

#### `FTL` in OPCs

`FTL` is significant in:

- female-ε3/ε3 AD-up: 7 of 22 query genes in a 146-gene layer-2 neighborhood,
  fold enrichment 15.53, adjusted P = 1.89×10^-5; and
- male-ε2 AD-down: 12 of 81 query genes in a 123-gene layer-2 neighborhood,
  fold enrichment 8.18, adjusted P = 2.09×10^-6.

The covered program includes `FTH1`, `GPX4`, `PARK7`, `FIS1`, `SLC25A4`,
`ATP5IF1`, and respiratory-chain genes. `FTL` is never marked global, so it
should be treated as a strong local OPC program organizer rather than the
topmost network root.

Oligodendrocytes are iron-rich and vulnerable to iron-dependent oxidative
injury; experimental iron overload induces ferroptotic features in an
oligodendrocyte cell model
([Li et al., 2023](https://pubmed.ncbi.nlm.nih.gov/36352276/)). Histochemical
work in AD brain has also shown altered cellular distributions of iron,
transferrin, and ferritin around plaques
([Connor et al., 1992](https://pubmed.ncbi.nlm.nih.gov/1613823/)). These data
support an iron/redox interpretation, although they do not validate `FTL` as
the causal OPC driver.

#### `SLC11A1` in microglia

`SLC11A1` has three primary and six secondary calls in two microglial fine
types. Its primary male-ε4 AD-up result covers `ACSL1` and `SLC25A37` in a
four-gene layer-1 neighborhood against a 12-gene signature, with fold
enrichment 191.96 and adjusted P = 0.0070.

The compact neighborhood is statistically strong but narrow. Independent
work in microglia has shown that SLC11A1 can regulate lysosomal iron
accumulation and that reducing SLC11A1 alters microglial debris clearance
after white-matter injury
([Qiu et al., 2026](https://pubmed.ncbi.nlm.nih.gov/41580979/)). This is a
mechanistic bridge to the Phase 12 result, not direct AD validation.

Taken together, `FTL` and `SLC11A1` suggest that mitochondrial AD programs may
couple to iron storage in OPCs and lysosomal iron handling in microglia.

### 5.6 `RPL11` and `RPS15`: strongest recurrence, largest hub concern

`RPL11` and `RPS15` are the two most recurrent non-mtDNA, completely
self-independent candidates:

- `RPL11`: 131 calls, 53 primary calls, four networks, 17 fine cell types,
  118 global calls, and as many as 21 covered signature genes;
- `RPS15`: 123 calls, 50 primary calls, five networks, 22 fine cell types, and
  as many as 19 covered signature genes.

`RPL11` is especially strong in excitatory neurons and also recurs in
astrocytes, microglia, and oligodendrocytes. It covers `APOO` in 15 primary
calls, `TOMM7` in four, and `SLIRP` in two. `RPS15` is broadest in inhibitory
neurons and OPCs.

RPL11 has a recognized extra-ribosomal role in the nucleolar-stress/MDM2/p53
pathway
([Bursać et al., 2012](https://pubmed.ncbi.nlm.nih.gov/23169665/)).
Separately, impaired ribosomal function and RNA oxidation have been reported
early in human mild cognitive impairment and AD
([Ding et al., 2005](https://pubmed.ncbi.nlm.nih.gov/16207876/)).

These observations make a ribosome-stress interpretation plausible. They do
not prove that RPL11 or RPS15 is specific to mitochondrial AD biology. Highly
expressed housekeeping genes and ribosomal hubs can be stable network anchors.
Both genes should undergo degree-matched permutation, expression-level
matching, and independent-network validation before experimental priority is
based on recurrence alone.

`RPL11` is more compelling as an upstream candidate because 90.1% of its calls
are global, compared with 18.7% for `RPS15`.

### 5.7 `WDR82`: strong excitatory, AD-up-specific novel candidate

`WDR82` is unusually clean computationally:

- 70 total calls;
- 42 primary calls;
- all 70 calls global;
- 21 conservative directional calls;
- 12 of 14 excitatory fine cell types represented; and
- only AD-up conservative calls.

The strongest stratum is female ε3/ε3, followed by female ε2, male ε4, and
male ε3/ε3. Many neighborhoods repeatedly cover the mtDNA cluster
`MT-ND4L`, `MT-ND5`, `MT-ND3`, and `MT-ND1`.

WDR82 recruits SETD1A-mediated H3K4 methylation machinery to transcription
start sites through RNA polymerase II
([Lee and Skalnik, 2008](https://pubmed.ncbi.nlm.nih.gov/17998332/)).
That provides a plausible transcriptional mechanism but no direct AD or
mitochondrial causal validation.

The near-identical mtDNA overlap across many fine cell types is also a warning:
the recurrence may reflect one stable excitatory-network motif repeatedly
queried by related signatures. `WDR82` is a strong candidate for network and
perturbation validation, not yet a strong therapeutic claim.

### 5.8 `SELENOW`: global neuronal redox candidate

`SELENOW` has:

- 95 total and 35 primary calls;
- 89 global calls;
- excitatory and inhibitory support;
- 16 conservative directional calls across 10 fine cell types; and
- recurrent coverage of mitochondrial carrier, assembly, redox, and
  proteostasis genes.

Its clearest patterns are female-ε2 AD-up, male-ε2 AD-down, and female-ε4
AD-down. `FIS1` occurs in two primary `SELENOW` neighborhoods.

Selenoproteins participate in redox control, and loss of SELENOW alters redox
tone and mitochondrial metabolism in inflammatory macrophages
([Short et al., 2023](https://pubmed.ncbi.nlm.nih.gov/36516721/)). Evidence
specific to neuronal AD remains limited. `SELENOW` should therefore be
presented as a biologically plausible and topologically strong novel
hypothesis.

### 5.9 `BEX3` and `TMEM147`: second-line neuronal candidates

`BEX3` has 36 calls across excitatory, inhibitory, and OPC networks. Seven
conservative directional calls occur in:

- male-ε3/ε3 excitatory AD-down;
- female-ε4 and male-ε2 inhibitory AD-down; and
- male-ε2 OPC AD-down.

Covered genes include `ARMCX3`, `ISCU`, `TIMM17A`, `MRPL20`, `PSAP`, `PINK1`,
and `VDAC2`. BEX3 is also known as the p75NTR-associated death executor
(NADE), and experimental work has implicated this pathway in neuronal death
after zinc exposure and ischemic injury
([Park et al., 2000](https://pmc.ncbi.nlm.nih.gov/articles/PMC6773028/)).
This provides a cell-death mechanism but not AD-specific validation.

`TMEM147` has 78 excitatory-neuron calls, including 30 primary calls and 15
conservative directional calls across ten fine cell types. Its neighborhoods
repeatedly cover `PRDX5`, `NDUFB10`, `NDUFB11`, `DBI`, and `GADD45GIP1`.
TMEM147 localizes to the ER/nuclear envelope and experimentally affects
cholesterol homeostasis through sterol-reductase interactions
([Christodoulou et al., 2020](https://pubmed.ncbi.nlm.nih.gov/32694168/)).
That is intriguing in APOE/lipid-centered AD biology, but the evidence remains
indirect and restricted to one broad network.

### 5.10 `ANKRD11`: strong but narrow OPC chromatin candidate

`ANKRD11` has 12 OPC calls, including four primary calls. All are
self-independent and all are global. The two independent directional primary
signals are:

- female-ε3/ε3 AD-up: 7/22 overlap, adjusted P = 9.37×10^-5; and
- male-ε2 AD-down: 13/81 overlap, adjusted P = 8.81×10^-6.

The neighborhoods strongly overlap those of `FTL` and contain `FTH1`, `GPX4`,
`PARK7`, `FIS1`, `ATP5IF1`, and respiratory-chain genes.

ANKRD11 is a chromatin regulator with demonstrated functions in neuronal
differentiation and BDNF/TrkB signaling
([Ka and Kim, 2018](https://pubmed.ncbi.nlm.nih.gov/29274743/)). Its direct
connection to OPC mitochondrial biology or AD is not established. The exact
similarity between its two primary neighborhoods and the `FTL` neighborhoods
also makes it important to test whether both are alternative representatives
of the same fixed OPC topology.

### 5.11 `HSPA1A`: useful vascular/stress hypothesis, lower statistical robustness

`HSPA1A` has 20 calls across vasculature and inhibitory networks. It is
self-independent and global in 14 calls. `HSPD1` is downstream in all ten
primary `HSPA1A` calls.

The strongest biologically matched vascular primary result is female-ε4
endothelial AD-down, with two covered genes (`MRPS6` and `HSPD1`) in a
51-gene layer-3 neighborhood. However, its effective signature contains only
four genes. The recurrence and stress-proteostasis biology are interesting,
but the small-query dependence places `HSPA1A` below the main shortlist.

### 5.12 `PARK7`: important readout, weak Phase 12 upstream evidence

`PARK7` was a strong pre-network candidate but has only six KDA calls:

- three primary;
- three secondary;
- two broad networks; and
- one self-independent primary call.

It has no call passing the conservative directional screen. In contrast,
`PARK7` is covered by `GABARAPL2` in 16 primary calls and by `FTL` and
`ANKRD11` in two primary calls each. Phase 12 therefore supports `PARK7` more
strongly as a downstream mitochondrial stress readout than as the upstream
driver.

## 6. Network-specific conclusions

| Network | Most useful candidates | Interpretation |
|---|---|---|
| Astrocytes | `APOE`, `RPL11`; `RPL13` as a lower-confidence self-containing hit | `APOE` is the strongest AD-anchored result and connects to `TUFM`, `LDHB`, and mitochondrial dynamics/metabolism genes. |
| Excitatory neurons | `RPL11`, `WDR82`, `SELENOW`, `GABARAPL2`, `TMEM147`, `LAMTOR5` | The richest result set; supports transcription/translation, redox, lysosome–autophagy, and ER/lipid control of mitochondrial programs. |
| Inhibitory neurons | `RPS15`, `LAMTOR5`, `BEX3`, `HSPA1A`; `PLCG2` as a cautionary hit | Strong male-ε2 and female-ε4 AD-down structure. `PLCG2` is externally AD-relevant but every KDA call covers only one query gene and occurs in the unexpected inhibitory network. |
| Microglia | `SLC11A1`, `RPL11` | Supports lysosomal iron and ribosome/redox hypotheses, but only 44 eligible runs and two result-producing fine types limit breadth. |
| OPCs | `FTL`, `ANKRD11`, `RPS15`, `BEX3` | Strong iron/ferroptosis and chromatin hypotheses in female-ε3/ε3 AD-up and male-ε2 AD-down signatures. |
| Oligodendrocytes | `RPL11` | Most other nuclear hits are one-overlap results; `RPL11` is the clearest multi-gene, self-independent candidate. |
| Vasculature | `HSPA1A` | Stress/proteostasis candidate, but the primary endothelial query is very small. |
| CAMs | None evaluated | No eligible KDA run. |
| T cells | None evaluated | No eligible KDA run. |

### The `PLCG2` warning is informative

`PLCG2` is a known AD-relevant immune gene: the P522R allele is protective and
is a mild functional hypermorph in microglia
([Magno et al., 2019](https://pubmed.ncbi.nlm.nih.gov/30711010/)).
Phase 12 reports 28 `PLCG2` calls, but all are in the inhibitory-neuron network
and every call covers only one query gene. This is not a strong mitochondrial
KDA confirmation of `PLCG2`. Rather, it illustrates why external relevance,
large fold enrichment, or recurrence alone cannot override cell-type mismatch
and one-gene neighborhood structure.

Among a panel of established AD genes
(`APP`, `PSEN1`, `PSEN2`, `TREM2`, `ABCA7`, `BIN1`, `CLU`, `PICALM`, `SORL1`,
`CD33`, `INPP5D`, `CR1`, `SPI1`, `FERMT2`, `ADAM10`, `APOE`, and `PLCG2`),
only `APOE` and `PLCG2` appear in the KDA summary. `VGF`, which was
experimentally validated after a broader multiscale AD KDA, is absent. This
does not refute those genes; Phase 12 asks a narrower question about core
mitochondrial DEG programs.

## 7. Sex/APOE and direction patterns

The strongest descriptive patterns are:

- **Female ε2 AD-up:** `APOE` in astrocytes and `RPL11`, `RPS15`,
  `LAMTOR5`, `SELENOW`, `GABARAPL2`, and `TMEM147` in neurons.
- **Female ε3/ε3 AD-up:** especially `WDR82` in excitatory neurons and
  `FTL`/`ANKRD11` in OPCs.
- **Female ε4 AD-down:** `BEX3`, `LAMTOR5`, `GABARAPL2`, `SELENOW`, and
  `HSPA1A`.
- **Male ε2 AD-down:** the broadest recurrent neuronal and glial pattern,
  including `RPL11`, `RPS15`, `LAMTOR5`, `GABARAPL2`, `BEX3`, `FTL`, and
  `ANKRD11`.
- **Male ε4:** the clearest microglial `SLC11A1` signal and additional
  astrocyte `APOE` support.

These are **not formal AD-by-sex, AD-by-APOE, or three-way interactions**.
The groups can differ in donor number, statistical power, effective query
size, and eligible-network coverage. The fine cell types also reuse a broad
network, and the same gene can be counted in AD-up and the derived AD-both
signature. The patterns should guide stratified validation, not support claims
of sex- or genotype-specific causation without a direct interaction model.

## 8. Integration with the pre-network mitochondrial shortlist

The pre-network report prioritized mitochondrial control genes using
differential expression, recurrence, pathway annotation, and Phase 10
similarity:
[`pre_network_prioritization_report.md`](../mt_pathway/pre_network_prioritization_report.md).

Phase 12 changes their interpretation:

| Upstream Phase 12 candidate | Previous candidate downstream | Primary calls containing the pair | Fine cell types | Interpretation |
|---|---|---:|---:|---|
| `LAMTOR5` | `ATP5IF1` | 28 | 11 | Strong neuronal lysosome/mTOR-to-mitochondrial-energy hypothesis |
| `GABARAPL2` | `PARK7` | 16 | 7 | Autophagic-flux-to-mitochondrial-stress hypothesis |
| `APOE` | `TUFM` | 7 | 3 | Astrocyte APOE-to-mitochondrial-translation/metabolism hypothesis |
| `HSPA1A` | `HSPD1` | 10 | 5 | Stress-response-to-mitochondrial-proteostasis hypothesis |
| `RPL11` | `APOO` | 15 | 7 | Ribosome/stress-to-mitochondrial-membrane hypothesis |
| `RPL11` | `TOMM7` | 4 | 2 | Ribosome/stress-to-protein-import hypothesis |
| `ANKRD11` | `ATP5IF1`, `FIS1`, `PARK7` | 2 each | 1 | OPC chromatin-to-energy/dynamics/redox hypothesis |
| `FTL` | `ATP5IF1`, `FIS1`, `PARK7` | 2 each | 1 | OPC iron-to-energy/dynamics/redox hypothesis |

Important consequences:

- `ATP5IF1` is absent from the KDA driver summary but repeatedly appears
  downstream of `LAMTOR5`, `FTL`, and `ANKRD11`.
- `TUFM` is a recurrent KDA result (39 calls across two networks) but is always
  a signature member and is never global; its strongest new role is as an
  `APOE`-linked astrocyte readout.
- `HSPD1` is generally a signature member, while `HSPA1A` is the
  self-independent network candidate immediately upstream.
- `PARK7` has weak upstream KDA evidence but is repeatedly covered by
  `GABARAPL2`, `FTL`, and `ANKRD11`.

The earlier shortlist should not be discarded. It should become a targeted
downstream assay panel for perturbing Phase 12 drivers.

## 9. Mechanistic synthesis

The prioritized genes support four interacting biological axes.

### 9.1 Astrocyte lipid and metabolic support

`APOE` connects astrocyte genotype/lipid biology to mitochondrial translation,
carbon metabolism, and dynamics (`TUFM`, `LDHB`, `CHCHD10`, `ATP5PB`, and
`ATP5F1A`). This is the most direct bridge between known AD biology and the
Phase 12 mitochondrial phenotype.

### 9.2 Lysosome, nutrient sensing, and autophagic flux

`LAMTOR5` and `GABARAPL2` connect lysosomal nutrient sensing and
autophagosome–lysosome flux to `ATP5IF1`, `PARK7`, mitochondrial ribosomal
genes, OXPHOS subunits, and apoptosis genes. `HSPA1A` adds a proteostasis arm.

### 9.3 Iron, selenium, and oxidative injury

`FTL`, `SLC11A1`, and `SELENOW` identify complementary iron-storage,
lysosomal-iron, and redox programs. Their covered genes include `GPX4`,
`FTH1`, `SLC25A37`, `ACSL1`, `FIS1`, and OXPHOS components, suggesting a link
between iron availability, lipid oxidation, mitochondrial function, and glial
state.

### 9.4 Transcription, translation, and cellular stress

`WDR82`, `RPL11`, `RPS15`, and `ANKRD11` suggest that chromatin/transcription
and ribosome stress organize part of the mitochondrial response. `TMEM147`
adds ER/cholesterol regulation. This axis is computationally strong but also
the most vulnerable to generic hub, expression-level, and shared-network
effects.

A parsimonious working model is:

> AD-associated mitochondrial programs are not controlled by one universal
> regulator. They are organized by cell-type-specific upstream systems:
> astrocyte APOE metabolism, neuronal lysosome/autophagy and transcriptional
> stress, and glial iron/redox homeostasis, all converging on a recurrent
> respiratory-chain core.

## 10. Limitations that must accompany paper claims

### 10.1 Statistical scope

- BH adjustment is performed **within each KDA run**, not across 1,782 runs.
- The result table contains only significant candidates, so a valid
  phase-wide BH correction cannot be reconstructed from it.
- The algorithm selects the smallest raw P value across up to three layers and
  does not separately correct for layer selection.
- `minimum_adjusted_p_value` in the summary is the minimum of within-run values
  and is not a meta-analysis P value.

### 10.2 Dependence

- AD-up and AD-both signatures overlap by construction.
- Secondary pools reuse primary signatures and overlap with one another.
- Fine cell types within a broad lineage reuse the same broad network.
- Recurrent calls are therefore robustness observations, not independent
  replications.

### 10.3 Network interpretation

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

### 10.4 Biological scope

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

## 11. Recommended confirmation analyses

### 11.1 Computational validation

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

### 11.2 Experimental validation

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

## 12. Paper-ready interpretation

### Results language

> Cell-type-matched directed-network enrichment analysis identified a
> recurrent respiratory-chain core across seven broad brain-cell networks.
> Because mtDNA and structural OXPHOS genes frequently belonged to the queried
> signatures, we applied a conservative prioritization requiring primary,
> direction-specific, non-mtDNA, non-self, multi-gene calls from signatures of
> at least ten genes. This highlighted cross-network ribosomal-stress
> candidates RPL11 and RPS15; excitatory-neuron WDR82, SELENOW, GABARAPL2, and
> TMEM147; neuronal LAMTOR5; astrocytic APOE; OPC FTL and ANKRD11; and
> microglial SLC11A1. APOE, LAMTOR5, GABARAPL2, FTL, and SLC11A1 were
> prioritized for biological coherence, whereas RPL11, RPS15, WDR82, and
> SELENOW were prioritized as strong topology-derived hypotheses requiring
> independent network validation.

### Discussion language

> The KDA results support a model in which cell-type-specific lipid,
> lysosome–autophagy, iron/redox, and transcription/translation-stress
> pathways converge on a common mitochondrial respiratory program in AD.
> Several pre-network mitochondrial candidates were repositioned as downstream
> readouts: ATP5IF1 occurred repeatedly downstream of LAMTOR5, TUFM downstream
> of astrocytic APOE, PARK7 downstream of GABARAPL2, and HSPD1 downstream of
> HSPA1A. These directed-neighborhood enrichments nominate regulatory
> hypotheses but do not establish causal edge direction or therapeutic effect,
> because multiple-testing control was within each run, fine-cell signatures
> reused broad networks, and pooled and union signatures were not independent.

## 13. Reproducibility pointers

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
- [`phase12_kda_netweaver_figure_explained.md`](phase12_kda_netweaver_figure_explained.md)

## Bottom line

The strongest defensible claim is not that Phase 12 found one universal AD
driver. It found a recurrent mitochondrial respiratory core and several
cell-type-specific candidate control systems.

- **Best established bridge:** `APOE` in astrocytes.
- **Best neuronal mechanistic axis:** `LAMTOR5`–`ATP5IF1` and
  `GABARAPL2`–`PARK7`.
- **Best glial iron/redox axis:** `FTL` in OPCs and `SLC11A1` in microglia.
- **Strongest broad topology candidate:** `RPL11`.
- **Strongest excitatory novel candidates:** `WDR82` and `SELENOW`.
- **Useful second tier:** `BEX3`, `TMEM147`, `ANKRD11`, and `RPS15`.
- **Best sentinel/readout class:** mtDNA/OXPHOS genes, including `MT-CO2`,
  `MT-ND4`, `MT-CO3`, `MT-CYB`, `COX4I1`, and `ATP5F1E`.

These genes define a focused, testable experimental program. Causal wording
should be reserved until the top neighborhoods survive degree-matched
permutation, donor-level signature validation, independent-network
replication, and cell-type-specific perturbation.
