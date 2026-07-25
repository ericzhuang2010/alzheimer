# Sex- and APOE-dependent mitochondrial transcriptional responses in Alzheimer’s disease

## Scope and interpretation status

This report synthesizes the validated Minerva Phase 08–11 outputs and the mitochondrial analogues of Figures 1 and 3–6. It follows the comparison logic and discussion style of [Yu et al. (2026)](https://doi.org/10.1002/alz.71463), but restricts the primary analysis to mitochondrial genes and MitoCarta pathways.

The discussion also evaluates primary prior literature. “Recapitulation” is reserved for results recovered by this mitochondrial reanalysis of the same ROSMAP resource; “convergence” denotes compatible evidence from a different endpoint, tissue, cohort, or model; and “replication” would require the same sex-by-APOE AD contrast in an independent brain cohort. No located study meets that final standard for the complete mitochondrial direction switch reported here.

The literature search was updated through 25 July 2026 and prioritized original human brain, imaging/metabolic, single-cell, and mechanistic perturbation studies, with special attention to papers cited by Yu. It is a targeted narrative review rather than a registered systematic review; absence of a located study should be interpreted accordingly.

The central result is a **sex- and APOE-dependent switch in the AD-associated oxidative-phosphorylation (OXPHOS) response**, most clearly expressed in excitatory neurons:

- female APOE ε2 carriers show predominantly higher OXPHOS transcript abundance in AD than NCI;
- male APOE ε2 carriers show predominantly lower OXPHOS transcript abundance in AD;
- female APOE ε4 carriers also show predominantly lower OXPHOS transcript abundance in AD;
- male APOE ε4 carriers show a weaker, mixed response, with several excitatory subtypes showing increases; and
- APOE ε3/ε3 has a lower aggregate mitochondrial DEG burden, although selected excitatory subtypes still have strong responses.

This is a strong pathway-level and descriptive cell-type pattern, but it is **not yet a demonstrated causal interaction**. No mitochondrial gene passed the Phase 10 directional similarity FDR, and the current MAST branch does not fit formal AD-by-sex or AD-by-APOE interaction terms. “Different between strata” below therefore means that the stratified AD-versus-NCI signatures differ; it does not mean that a direct interaction test is significant.

## Analytical frame

The cohort contains 276 donors after the Yu-compatible exclusions: 142 NCI and 134 AD. Six strata were analyzed:

| Stratum | AD donors | NCI donors |
|---|---:|---:|
| Female ε2 carrier | 8 | 17 |
| Female ε3/ε3 | 37 | 45 |
| Female ε4 carrier | 26 | 11 |
| Male ε2 carrier | 7 | 6 |
| Male ε3/ε3 | 29 | 53 |
| Male ε4 carrier | 27 | 10 |

Within each of 54 fine cell types, AD was compared with NCI separately in each stratum. The MAST models included total RNA count, age at death, and postmortem interval. A Yu-compatible DEG required within-contrast BH FDR `< 0.05` and absolute fold change `> 1.3`, equivalent to `|log2FC| > 0.3785`. Of 324 planned contrasts, 321 were estimable. Male-ε2 CAMs, male-ε2 `Mic MKI67`, and male-ε2 `Fib SLC4A4` could not be estimated because one comparison arm had too few cells.

The Zhang–Yu analysis compares **paired AD-versus-NCI states**, not baseline expression between sexes or APOE genotypes. For each gene and fine cell type, significant AD upregulation is encoded `+1`, no threshold-level DEG is `0`, and significant AD downregulation is `−1`. The six mitochondrial comparisons are:

1. female versus male across all APOE groups;
2. ε2 versus ε3/ε3 across both sexes;
3. ε4 versus ε3/ε3 across both sexes; and
4. female versus male separately within ε2, ε3/ε3, and ε4.

The primary similarity universe is the set of MitoCarta `core_mito_protein` features with sufficient paired coverage. The pathway analysis tests fixed 200-gene high- and low-score tails against comparison-specific mitochondrial backgrounds. Consequently, pathway enrichment here asks which mitochondrial functions are unusually concentrated among relatively shared or divergent mitochondrial genes; it is not a transcriptome-wide enrichment test.

## Results

### Mitochondrial DEG burden is greatest in male ε2 and is directionally different across strata

The first Yu-style summary counts significant core-mitochondrial gene-by-cell-type occurrences. These are recurrence counts across fine cell types, not counts of unique genes and not independent biological replicates.

| Stratum | Significant occurrences / tested | Percent | AD up | AD down | Main pattern |
|---|---:|---:|---:|---:|---|
| Female ε2 | 1,128 / 37,647 | 3.00% | 935 | 193 | predominantly increased |
| Female ε3/ε3 | 821 / 36,775 | 2.23% | 554 | 267 | moderately increased |
| Female ε4 | 1,633 / 37,006 | 4.41% | 269 | 1,364 | strongly decreased |
| Male ε2 | 3,753 / 35,380 | 10.61% | 1,613 | 2,140 | largest and broadly decreased/mixed |
| Male ε3/ε3 | 869 / 35,304 | 2.46% | 377 | 492 | relatively limited and mixed |
| Male ε4 | 1,058 / 35,290 | 3.00% | 510 | 548 | mixed |

Male ε2 therefore has the largest mitochondrial transcriptional response, paralleling the genome-wide result in Yu. The effect is distributed across excitatory and inhibitory neurons, astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`. The small male-ε2 donor count makes its magnitude especially important to validate with donor-aware models: it may represent a strong biological response, instability from a small stratum, nucleus-level pseudoreplication, or a mixture of these.

The female comparison is qualitatively different. Female ε2 and ε3/ε3 signatures are mainly upward, whereas female ε4 is strongly downward. In males, ε2 is the outlying genotype, while ε3/ε3 and ε4 have much smaller aggregate burdens. This refines Yu’s conclusion that female ε4 and male ε2 are the most genotype-distinct transcriptional groups by showing that mitochondrial programs contribute substantially to both patterns.

### OXPHOS is the dominant mitochondrial pathway

OXPHOS subunits are the most recurrently altered MitoCarta program in every stratum. Direction, rather than simple presence or absence of a response, distinguishes the sex–APOE groups.

| Stratum | OXPHOS DEG occurrences / tested | AD up | AD down | Unique OXPHOS genes significant in at least one cell type |
|---|---:|---:|---:|---:|
| Female ε2 | 403 / 3,736 (10.79%) | 398 | 5 | 68 |
| Female ε3/ε3 | 332 / 3,677 (9.03%) | 319 | 13 | 54 |
| Female ε4 | 324 / 3,641 (8.90%) | 50 | 274 | 70 |
| Male ε2 | 659 / 3,505 (18.80%) | 95 | 564 | 79 |
| Male ε3/ε3 | 171 / 3,534 (4.84%) | 85 | 86 | 60 |
| Male ε4 | 227 / 3,589 (6.32%) | 141 | 86 | 65 |

Complexes I, III, IV, and V follow this pattern. Complex IV is especially prominent: its recurrence is 14.9% upward in female ε2, 12.4% mainly downward in female ε4, and 25.7% mainly downward in male ε2. Complex II is much less involved. The signal therefore resembles coordinated remodeling of the proton-pumping respiratory chain and ATP synthase rather than a uniform change in every mitochondrial metabolic enzyme.

This pattern is not produced only by mitochondrial-genome transcripts. After excluding mtDNA-encoded genes, nuclear OXPHOS-subunit occurrences remain strongly upward in female ε2 (`258 up / 4 down`) and strongly downward in female ε4 (`17 / 234`) and male ε2 (`77 / 444`). Male ε3/ε3 and male ε4 show more nuclear-subunit decreases (`11 / 75` and `41 / 61`) while their mtDNA subunits are often increased (`74 / 11` and `100 / 25`). That separation raises a hypothesis of sex- and APOE-dependent **mitonuclear discordance**, but a direct donor-level mitonuclear-balance model is required before using that term as a conclusion.

### The lowest-similarity tails converge on OXPHOS in all six comparisons

The focused MitoCarta pathway results show that OXPHOS-subunit genes are concentrated in every 200-gene low-similarity tail.

| Comparison | Eligible core-mito background | OXPHOS genes in low tail | Fold enrichment | Tail BH FDR |
|---|---:|---:|---:|---:|
| Female versus male, all APOE | 700 | 53 / 200 | 2.47 | `9.36e-14` |
| ε2 versus ε3/ε3, both sexes | 708 | 53 / 200 | 2.50 | `5.42e-14` |
| ε4 versus ε3/ε3, both sexes | 686 | 48 / 200 | 2.23 | `1.21e-9` |
| Female versus male, ε2 | 732 | 56 / 200 | 2.66 | `1.18e-16` |
| Female versus male, ε3/ε3 | 705 | 49 / 200 | 2.33 | `6.63e-11` |
| Female versus male, ε4 | 679 | 47 / 200 | 2.13 | `1.99e-8` |

Thirty-five OXPHOS genes occur in all six low tails, and Complex IV contributes 11 or 12 of its 12 measured background members in every comparison. The corresponding C2:CP results contain 32–64 significant pathways per low-tail query, but many are repeated views of the same respiratory-chain genes: oxidative phosphorylation, electron transport, aerobic respiration, and the Parkinson, Huntington, and Alzheimer pathway sets. The focused MitoCarta results indicate that these should be interpreted as one dominant respiratory-chain theme rather than dozens of independent mechanisms.

This pathway-level convergence is stronger than the single-gene similarity evidence. Across the six core-mito comparisons, **zero genes pass directional BH FDR**; the smallest adjusted value is 0.743. Low-tail membership therefore supplies a descriptive prioritization rank, not significant evidence that any individual gene is sex- or APOE-divergent.

### APOE changes the direction of the sex effect

The most compelling paired pattern is within APOE ε2. Across jointly tested OXPHOS gene–cell-type pairs, there are 153 exact opposite-direction occurrences, and all have the same orientation: AD-associated upregulation in females and downregulation in males. In `Exc L3-4 RORB CUX2` alone, 31 OXPHOS genes have exact opposite states. Examples include:

- `COX5B`: female `+0.740`, male `−1.247`;
- `NDUFB11`: female `+0.858`, male `−1.911`; and
- `UQCRQ`: female `+0.799`, male `−1.466`.

The same female-up/male-down program is visible in `Exc L4-5 RORB IL1RAPL2`, `Exc L2-3 CBLN2 LINC02306`, `Ast GRM3`, OPCs, and selected inhibitory neurons. This is not merely a neuron-wide artifact: male-ε2 `Mic P2RY12` has 12 significant OXPHOS-subunit occurrences out of 23 tested, 11 of which are down.

Within APOE ε4, the dominant direction is different. Female ε4 is mainly down, while male ε4 is more mixed and is upward in selected excitatory states. `Exc RELN CHD7` contains 19 exact female-down/male-up OXPHOS reversals, including:

- `NDUFB7`: female `−2.011`, male `+2.322`;
- `UQCR10`: female `−1.053`, male `+1.629`; and
- `ATP5F1E`: female `−1.268`, male `+1.268`.

In `Exc L2-3 CBLN2 LINC02306`, another 38 OXPHOS genes are significantly down only in female ε4. The ε4 sex effect is thus concentrated in specific superficial and RELN-positive excitatory populations rather than being uniform across all neurons.

APOE ε3/ε3 has the weakest aggregate sex divergence and only eight exact female-up/male-down OXPHOS pairs. It is not biologically silent, however. Male-ε3/ε3 `Exc NRGN` has 48 downregulated OXPHOS genes among 58 tested, showing that strong effects can be restricted to one neuronal state and disappear in an aggregate summary.

### APOE divergence is itself sex-dependent

The ε2-versus-ε3/ε3 comparison is driven mainly by males. In superficial excitatory neurons, male ε2 has widespread OXPHOS loss while male ε3/ε3 has little change or selected increases. Female ε2 and female ε3/ε3, by contrast, often share an upward AD response. Thus, the global ε2-versus-ε3/ε3 low tail should not be interpreted as a sex-invariant ε2 effect.

The ε4-versus-ε3/ε3 comparison is driven mainly by females. In `Exc L2-3 CBLN2 LINC02306`, female ε4 has 36 ε4-only OXPHOS decreases and exact reversals for `MT-CO1` and `MT-ND2`, whereas the matching male cell type is largely shared or null. This direction and localization agree with Yu’s transcriptome-wide observation that female ε4 has the most distinct female APOE signature.

Across all core mitochondrial genes—not only OXPHOS—approximately 89%–95% of informative paired occurrences are significant in only one comparator rather than significant in opposite directions. “Divergence” therefore usually means **stratum-restricted threshold-level regulation**, not literal direction reversal. The OXPHOS reversals in ε2 and the selected ε4 excitatory populations are notable exceptions.

### Secondary mitochondrial programs support a broader stress-and-maintenance response

OXPHOS is dominant, but several other programs refine the biological picture:

| Program | Strongest descriptive pattern |
|---|---|
| Mitochondrial chaperones | Female ε4 has 37 significant occurrences, all down; `HSPD1` supplies much of this signal. |
| Protein import and sorting | Female ε4 has 8 up / 46 down occurrences; male ε2 has 46 up / 58 down and the greatest overall burden. |
| Mitochondrial translation | Male ε2 has widespread remodeling; the mitochondrial-ribosome set has 111 up / 194 down occurrences across 74 unique genes. |
| Mitophagy | Female ε2 is mainly up (23 / 1), whereas male ε2 is mainly down (14 / 46). |
| ROS and glutathione metabolism | Female ε4 is mainly down (11 / 44); the within-ε4 low tail is formally enriched for this pathway (11/200, fold enrichment 2.20, FDR 0.037). |
| TCA cycle | Direct DEG recurrence is much lower than OXPHOS. Its apparent high-tail enrichment reflects relative stability rather than a shared activated response. |

These directional summaries pool gene-by-cell-type occurrences and are not formal gene-set tests. They are best used to nominate follow-up pathways. The formal tail enrichment most strongly supports OXPHOS; ROS/glutathione within ε4 is a secondary finding, and the five-gene mitochondrial-permeability-transition-pore enrichments in ε2-versus-ε3/ε3 and the ε3/ε3 sex comparison are lower-confidence because of their small gene sets.

A small bulk-postmortem study reported mitochondrial unfolded-protein-response (UPRmt) transcript activation and increased HSP60 protein in both sporadic AD and PSEN1 familial AD frontal cortex ([Beck et al., 2016](https://doi.org/10.2174/1567205013666151221145445)). That result runs in the opposite direction to the all-down female-ε4 chaperone occurrences here. The studies are not directly contradictory because the earlier work pooled cell types and did not stratify by sex or APOE. One testable interpretation is that the female-ε4 signal represents failure or loss of a compensatory UPRmt that can be visible in bulk AD tissue; another is that the direction changes with cell type, stage, or mitochondrial burden. The current data therefore support `HSPD1` as a subgroup-sensitive proteostasis readout, not yet as a causal regulator.

### “High similarity” mostly means a shared lack of threshold-level response

The most positive mitochondrial similarity scores are close to zero, and none is significant. High-tail enrichment includes the TCA cycle in the pooled sex comparison and protein import/homeostasis in ε2 versus ε3/ε3, but the supporting state pairs are 97%–99% `(0,0)`. These pathways should be described as **relatively stable or commonly below the DEG threshold**, not as concordantly activated or repressed.

This distinction is important for Figures 3–5. The plotted high-tail points in Figures 4 and 5 are pathway matches, but none passes the primary C2:CP tail FDR. The figure captions state this correctly.

## Discussion in the context of prior work

### The clinical literature supports stratification, but does not by itself explain the mitochondrial switch

Large human studies establish that sex modifies some APOE-associated phenotypes, although the effect is not uniform across genotype, age, disease stage, or outcome. In pooled longitudinal cohorts, APOE ε4 was more strongly associated with conversion and a more AD-like CSF tau/Aβ profile in women in particular analyses ([Altmann et al., 2014](https://doi.org/10.1002/ana.24135)). A subsequent meta-analysis of almost 58,000 participants found that the ε3/ε4-associated odds of AD were similar in men and women across ages 55–85 overall, but higher in women from ages 65–75; importantly for the present study, ε2/ε3 was more protective in women than in men (odds ratios 0.51 and 0.71, respectively; [Neu et al., 2017](https://doi.org/10.1001/jamaneurol.2017.2188)). These studies justify sex-by-genotype analysis, but they measure risk or progression, not an AD-associated mitochondrial response. The local female-ε2 increase should therefore not be labeled a protective mechanism, nor the male-ε2 decrease a mechanism of reduced protection, without longitudinal and functional evidence.

Human imaging and metabolomic work gives more specific energetic context. Among cognitively normal older adults, female APOE4 carriers showed widespread FDG hypometabolism and cortical thinning relative to female non-carriers, whereas male carriers showed only limited hypometabolism and some regions of cortical thickening ([Sampedro et al., 2015](https://doi.org/10.18632/oncotarget.5185)). In midlife adults, women had lower brain phosphocreatine-to-ATP and phosphocreatine-to-inorganic-phosphate ratios than men, and APOE4 was associated with lower ratios in frontal regions ([Jett et al., 2023](https://doi.org/10.1371/journal.pone.0281302)). Serum metabolomics further identified sex-dependent associations between AD biomarkers and acylcarnitines, with the strongest combined sex/APOE signals occurring in APOE4-positive women ([Arnold et al., 2020](https://doi.org/10.1038/s41467-020-14959-w)). These observations converge with energetic vulnerability in female ε4, but FDG uptake, high-energy-phosphate ratios, whole-body or serum metabolites, and OXPHOS RNA are not interchangeable measurements.

There is also meaningful counterevidence to a simple “female APOE4 always equals hypometabolism” model. In another ADNI analysis, APOE4-associated hypometabolism and smaller hippocampal volume were detected in men among cognitively normal participants, metabolic associations involved both sexes at MCI, and no APOE4–hypometabolism association was detected in established AD ([Sundermann et al., 2018](https://doi.org/10.1016/j.dadm.2018.06.004)). The Sampedro, Sundermann, Altmann, Jett, and Arnold analyses also share ADNI participants to varying degrees and should not be counted as fully independent replications. Together they indicate that sex–APOE metabolic effects are age-, stage-, region-, and endpoint-dependent—precisely the type of heterogeneity seen across the six local strata.

### Female ε4 OXPHOS loss has the strongest mechanistic convergence

Several experimental systems support a route from APOE4 to altered mitochondrial substrate use, respiration, and quality control:

- Humanized-APOE mouse brain and astrocytes shifted glucose flux toward aerobic glycolysis and away from TCA entry/OXPHOS; in the accompanying human cohort, lower resting energy expenditure and oxygen consumption were most evident in young female ε4 carriers ([Farmer et al., 2021](https://doi.org/10.1186/s13024-021-00483-y)). The human measurement was whole-body indirect calorimetry, however, not brain respiration.
- APOE4 mouse neurons had lower maximal respiration, spare capacity, ATP, respiratory-chain proteins, and `Ppargc1a`/`Ppargc1b`, while APOE4 astrocytes had impaired fatty-acid oxidation and reduced ability to metabolically support neurons ([Qi et al., 2021](https://doi.org/10.1016/j.celrep.2020.108572)).
- Isogenic human iPSC-derived APOE4 astrocytes showed increased glycolysis, reduced mitochondrial respiration, lysosomal cholesterol accumulation, impaired autophagic removal of damaged mitochondria, and rescue after cholesterol depletion ([Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). APOE4 astrocyte models also show reduced fission and mitophagy, with improved mitochondrial function after rapamycin treatment ([Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4)).
- In a small postmortem functional study without APOE stratification, female AD prefrontal cortex had lower Complex IV respiration than female control cortex, whereas the corresponding male contrast was not significant ([Yang et al., 2025](https://doi.org/10.1002/alz.70645)).

The local female-ε4 decrease in OXPHOS—particularly Complex IV, import, chaperone, mitophagy, and redox genes—is directionally consistent with these results. The studies differ substantially in species, age, cell type, disease state, and endpoint, and most do not jointly model sex, APOE, and AD. They therefore provide **mechanistic convergence, not replication** of the local AD-versus-NCI contrast. The local male-ε4 mixed or selected upward response could represent compensation, a surviving-cell state, or a different stage of metabolic remodeling; increased transcripts cannot be interpreted as preserved respiratory capacity.

Indeed, an isogenic human astrocyte study reported *higher* APOE4 mitochondrial respiration together with lower mitochondrial ATP production and greater proton leak ([Budny et al., 2025](https://doi.org/10.3389/fncel.2025.1603657)). This apparently opposite result is informative: elevated respiratory activity or OXPHOS RNA can reflect inefficient, uncoupled, or compensatory flux. It provides a concrete alternative explanation for the selected male-ε4 increases and reinforces the need to measure ATP-linked respiration, coupling efficiency, and proton leak separately.

An endothelial study cited by Yu adds another useful qualification. Peripheral APOE4 worsened vascular and amyloid phenotypes in mice and increased endothelial `Hspa1a`, `Hspa1b`, and `Hsp90aa1` while decreasing mitochondrial/ETC programs ([Liu et al., 2022](https://doi.org/10.1038/s41593-022-01127-0)). Thus, an APOE4-associated stress response can combine ETC loss with *increased* cytosolic heat-shock genes. That differs from the all-down mitochondrial-chaperone pattern in local female ε4 and argues against treating every heat-shock family member as one directional pathway.

### The ε2 sex reversal is the most novel—and least externally validated—finding

Female human-APOE targeted-replacement mice expressing APOE2 had a more robust glucose-metabolic profile than APOE3 or APOE4 mice, while APOE4 was most deficient; pathway analysis predicted PPARγ/PGC-1α activation in APOE2 and inhibition in APOE4, and PGC-1α expression improved respiration in APOE4-expressing cells ([Wu et al., 2018](https://doi.org/10.1523/JNEUROSCI.2262-17.2018)). This supplies a plausible link between the female-ε2 upward response and the `PPARGC1A`/`PPARGC1B` axis. It does not explain the male-ε2 decrease: the in vivo experiment used female mice, had very small genotype groups, assessed baseline isoform differences rather than an AD response, and emphasized glucose and ketone metabolism rather than the full respiratory chain.

The stronger epidemiologic protection of ε2/ε3 in women than men reported by Neu and the metabolically robust female-APOE2 mouse phenotype reported by Wu are therefore **directionally compatible context**, not evidence that higher OXPHOS transcription mediates ε2 protection. No located primary study simultaneously tests APOE2, sex, AD, cell type, and mitochondrial function. The 153 exact female-up/male-down ε2 OXPHOS occurrences—especially the 31 in `Exc L3-4 RORB CUX2`—should be presented as the study’s clearest new hypothesis. Because the male-ε2 stratum has only 13 donors, it is also the finding most in need of independent and donor-aware replication.

### Prior single-cell work helps localize the signal

Prior human single-cell studies anticipated sex-dependent and cell-specific AD responses. The original ROSMAP single-nucleus analysis found that female cells were overrepresented in disease-associated subpopulations and that sex differences were especially evident in oligodendrocytes ([Mathys et al., 2019](https://doi.org/10.1038/s41586-019-1195-2)). A sex-stratified reanalysis of public prefrontal and entorhinal datasets found that mitochondrial abnormality and coupled electron/ATP metabolic programs in entorhinal neurons were downregulated in women and upregulated in men ([Belonwu et al., 2022](https://doi.org/10.1007/s12035-021-02591-8)). That resembles the local female-down/male-up direction in selected ε4 excitatory populations but conflicts with the ε2 direction. APOE stratification, brain region, and disease stage may explain why a pooled sex effect hides genotype-specific reversals.

These are not independent replications: Mathys, Belonwu, Yu, and the present analysis reuse overlapping ROSMAP or public single-nucleus data. Their value is that they show how aggregation across genotype, region, or cell state can reverse or erase mitochondrial effects. The strongest local signal in superficial RORB-positive excitatory clusters is biologically notable because RORB marks selectively vulnerable entorhinal excitatory populations, and related RORB-positive neocortical populations also show vulnerability ([Leng et al., 2021](https://doi.org/10.1038/s41593-020-00764-7)). This does not make `RORB` the causal regulator of the OXPHOS signature; selective loss and survivor-state bias remain alternative explanations.

The `Exc RELN CHD7` result has a parallel anatomic rationale. A six-region human atlas emphasized depletion of RELN-positive entorhinal excitatory neurons during AD progression ([Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). RORB/RELN vulnerability studies support the *location* of the local signal, not its sex/APOE direction or a mitochondrial cause. A recent temporal-cortex study spanning APOE2 carriers, APOE3 homozygotes, and APOE4 carriers also found strongly genotype- and cell-type-dependent AD responses using two-part mixed models with donor identity as a random effect ([Li et al., 2025](https://doi.org/10.1016/j.neuron.2025.02.017)). It is an external precedent for the proposed donor-aware design, although its leading synaptic, myelin, and inflammatory findings do not validate the OXPHOS switch.

The glial results also have relevant precedents. APOE4 and female sex jointly amplified a distinct disease-associated microglial transcriptional program in human-APOE FAD mice and human iPSC-derived microglia ([Moser et al., 2021](https://doi.org/10.1016/j.isci.2021.103238)). Isogenic human glial models show APOE4-dependent cholesterol/lysosome dysregulation in astrocytes and microglia ([Tcw et al., 2022](https://doi.org/10.1016/j.cell.2022.05.017)). These studies make the `Ast GRM3` and `Mic P2RY12` signals plausible components of a multicellular metabolic response, but neither validates the local male-ε2 microglial direction. The prominence of excitatory neurons here, together with documented APOE4 astrocyte defects, motivates neuron–astrocyte co-culture rather than isolated-neuron perturbation alone.

### Human biochemical data support an OXPHOS phenotype while exposing two major confounders

The dominance of OXPHOS agrees with several orthogonal human studies. Across three DLPFC proteomic cohorts, AD was associated with lower Complex I protein abundance, although much of the difference was attributable to a 2%–4% reduction in overall mitochondrial protein content ([Trumpff et al., 2022](https://doi.org/10.1016/j.heliyon.2022.e09353)). In a small rapid-autopsy prefrontal cohort, AD and APOE4 were associated with lower respiratory-chain flux or maximal activity, while APOE4 differences were not mirrored by respiratory-chain protein abundance ([Troutwine et al., 2022](https://doi.org/10.1016/j.nbd.2022.105781)). The heavy confounding of APOE4 with AD status and absence of sex stratification limit that result, but it directly illustrates transcript/protein/activity decoupling.

Complex IV also has unusually consistent anatomic evidence. Cytochrome-oxidase activity was lower across posterior-cingulate cortical layers in AD, with the largest decrement in superficial layer I and a reported greater decrement in women ([Valla et al., 2001](https://doi.org/10.1523/JNEUROSCI.21-13-04923.2001)); the sex observation was secondary rather than a modern interaction test. Young adult APOE4 carriers without overt amyloid or tau pathology likewise had lower posterior-cingulate cytochrome-oxidase activity, especially in superficial laminae ([Valla et al., 2010](https://doi.org/10.3233/JAD-2010-100129)). These studies do not sample the same region or molecular cell types, but the conjunction of Complex IV and superficial cortical localization is a notable independent parallel to the `RORB`/`RELN` results.

An integrated analysis of cortex, CSF, and serum proteomes identified a broad decrease in mitochondrial proteins in AD CSF and found that 22 of 37 cross-tissue signature proteins were mitochondrial ([Wang et al., 2020](https://doi.org/10.1186/s13024-020-00384-6)). ATP synthase was already oxidatively modified with reduced activity at Braak stages I/II in entorhinal cortex ([Terni et al., 2010](https://doi.org/10.1111/j.1750-3639.2009.00266.x)), while the recent sex-stratified functional study found female-specific Complex IV respiratory loss in AD ([Yang et al., 2025](https://doi.org/10.1002/alz.70645)). These data support prioritizing Complexes I, IV, and V for protein/activity assays.

They also expose two interpretive confounders. First, lower respiratory-chain RNA or protein can reflect lower mitochondrial content or selective loss of high-energy-demand neurons rather than repression within intact mitochondria. The local within-cell-type nuclei analysis reduces bulk-composition confounding but does not remove neuronal subtype loss, altered nuclear state, or survivor bias. Donor-level estimates of mitochondrial mass, mtDNA copy number, and cell abundance are needed alongside expression.

Second, nuclear and mtDNA components need not move together. In human DLPFC, nuclear Complex I subunits were more tightly co-regulated with one another than with mtDNA-encoded subunits, and mtDNA copy number did not determine mtDNA-subunit protein abundance ([Trumpff et al., 2022](https://doi.org/10.1016/j.heliyon.2022.e09353)). In AD and MCI blood, nuclear OXPHOS and mitochondrial-translation transcripts decreased while several mtDNA transcripts—including `MT-ND2`, `MT-ATP6`, and `MT-CO1/2/3`—increased despite unchanged mtDNA copy number ([Lunnon et al., 2017](https://doi.org/10.1016/j.neurobiolaging.2016.12.029)). This is a direct precedent for the local nuclear-down/mtDNA-up pattern in some male strata, but it is peripheral blood evidence. In ROSMAP and other brain regions, mtDNA copy number was 7%–14% lower in AD and was associated more strongly with tau than amyloid ([Klein et al., 2021](https://doi.org/10.1186/s13024-021-00495-8)); that partially overlapping cohort result further shows why expression alone cannot identify the source of apparent mitonuclear imbalance.

The relative stability of TCA-cycle transcripts likewise should not be taken as intact TCA function. Human AD brain has shown selective decreases in pyruvate dehydrogenase, isocitrate dehydrogenase, and α-ketoglutarate dehydrogenase activities, but increases in succinate dehydrogenase and malate dehydrogenase ([Bubber et al., 2005](https://doi.org/10.1002/ana.20474)). Such nonuniform enzymatic remodeling can occur without a broad transcript-level DEG signature.

### Mitochondrial maintenance pathways may participate in a feedback loop with AD pathology and APOE

The import, translation, chaperone, mitophagy, and redox findings are mechanistically connected rather than merely secondary pathway labels. Defective mitophagy has been observed in AD patient hippocampus and patient-derived neurons, and inducing mitophagy improved amyloid, tau, and cognitive phenotypes across cellular, nematode, and mouse models ([Fang et al., 2019](https://doi.org/10.1038/s41593-018-0332-9)). Neuronal PINK1 restoration similarly improved mitochondrial, synaptic, amyloid, and cognitive phenotypes in AD models ([Du et al., 2017](https://doi.org/10.1093/brain/awx258)). These studies make the local mitophagy/import signal and `TOMM7` hypothesis biologically coherent, although neither study tested TOMM7, sex, or APOE.

Causal direction may also run both ways. Genetic or pharmacologic disruption of respiratory complexes I, III, or IV strongly increased APOE expression and secretion in multiple systems, including human iPSC-derived astrocytes ([Wynne et al., 2023](https://doi.org/10.7554/eLife.85779)). APOE4 can therefore alter mitochondrial function, while respiratory-chain dysfunction can alter APOE biology. The present postmortem contrasts cannot distinguish an APOE-driven mitochondrial lesion from a mitochondrial-stress-to-APOE response or a self-reinforcing loop.

## Relationship to the Yu study

The mitochondrial results recapitulate within the same ROSMAP resource and then extend the most relevant findings in Yu:

1. **Male ε2 has the largest transcriptional response.** The mitochondrial subset shows the same ranking, with particularly strong OXPHOS loss in superficial excitatory neurons, astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`.
2. **Female ε4 and male ε2 are the genotype outliers within their respective sexes.** Mitochondrial pathways contribute a coherent direction to both: female ε4 and male ε2 generally lose nuclear OXPHOS, protein-maintenance, and stress-defense transcripts.
3. **Yu’s ε4-versus-ε3/ε3 OXPHOS finding is recapitulated.** The focused analysis shows that this comparison is mainly a female excitatory-neuron result.
4. **Yu’s Figure 6 electron-transport signal is strengthened.** OXPHOS is enriched in the sex-divergent tail within ε2, ε3/ε3, and ε4, but the direction and driving cell types differ by genotype.
5. **`MT-ND2` remains a leading phenotype gene.** It is significant in 102 AD-versus-NCI cell-type/stratum contexts and lies in all six low-similarity tails. It is therefore an excellent mitochondrial response marker, but it is an mtDNA-encoded Complex I subunit rather than an obvious upstream regulator.

There is also an important difference. Yu’s transcriptome-wide analysis reports many significant similarity and divergence genes, whereas the mitochondrial-restricted Phase 10 analysis has no gene-level FDR hits. The defensible conclusion is therefore that **mitochondrial pathways show coordinated stratified divergence even though no individual mitochondrial similarity score is significant after mitochondrial-family correction**.

Yu’s within-genotype pathway results emphasized translation/ribosome programs in ε2 and ε3/ε3 and chaperone programs in all three genotypes, especially ε4. The mitochondrial restriction exposes OXPHOS as the common divergent core beneath those broader stress and maintenance themes. The closest prior source for Yu’s discussion of increased blood `MT-ND2` is the nuclear-down/mtDNA-up blood study by [Lunnon et al. (2017)](https://doi.org/10.1016/j.neurobiolaging.2016.12.029); it is supportive of a mitonuclear-imbalance hypothesis but is not brain or cell-type evidence.

The observed link between respiratory-chain state and APOE context is biologically plausible but not established by these data. Experimental work has shown that disruption of respiratory complexes I, III, or IV can increase APOE expression and secretion, including in human iPSC-derived astrocytes ([Wynne et al., 2023](https://doi.org/10.7554/eLife.85779)). That result supports a possible feedback between respiratory-chain stress and APOE biology; it does not prove that the transcript patterns here have the same mechanism. No located prior paper directly validates the complete female-ε2-up/male-ε2-down/female-ε4-down/male-ε4-mixed OXPHOS switch.

## Provisional key-regulator prioritization

### Why this is a pre-network nomination

The current repository can identify genes with strong local evidence and plausible control functions, but it cannot yet establish network key drivers. A causal key-driver claim requires evidence that a candidate’s directed network neighborhood is significantly enriched for the relevant mitochondrial DEG signature.

The existing [pre-network prioritization](pre_network_prioritization_report.md) is valuable but should not be used as a final causal ranking for two reasons:

- it scores only the MitoCarta core universe and therefore omits non-MitoCarta nuclear regulators in the extended mitochondrial-biogenesis and UPRmt sets, including `PPARGC1A`, `PPARGC1B`, `ESRRA`, `NRF1`, `SMARCD3`, `NR1D1`, `HSF1`, and `GABPB1`; and
- its “lineage” count is based on nine RDS partitions, treating three excitatory files as three lineages. Collapsing these yields seven biological compartments and reduces the apparent breadth of several assembly-factor candidates.

Similarity-tail membership and membership in an enriched pathway are useful evidence of context, but neither establishes that the candidate regulates the pathway. They should have less weight than directed network support, formal interaction evidence, genetic support, and perturbation data.

### Recommended perturbation panel

The following is a prioritized **experimental panel**, not a list of proven key drivers. It deliberately combines mitochondrial-localized control points with nuclear upstream regulators that the core-only score misses.

| Local priority | Candidate | Control axis | Local evidence | Main experimental hypothesis |
|---:|---|---|---|---|
| 1 | `ATP5IF1` | ATP-synthase control | 34 DEG contexts across 20 cell types and 5/6 strata; 8 up / 26 down; eight exact paired reversals | A bioenergetic control point that switches with sex and APOE rather than simply tracking mitochondrial mass |
| 2 | `PPARGC1B` | nuclear mitochondrial biogenesis | 11 DEG contexts, all up and all in male ε2 | A male-ε2-specific compensatory biogenesis response to respiratory-chain loss |
| 3 | `TUFM` | mitochondrial translation elongation | 19 contexts across 16 cell types and all six strata; 3 up / 16 down | Loss of mitochondrial translation control contributes to the female-ε4/male-ε2 respiratory phenotype |
| 4 | `TOMM7` | protein import and mitophagy | 25 contexts across 19 cell types and all six strata; 7 up / 18 down | Sex-dependent import/quality-control failure couples damaged organelles to the OXPHOS response |
| 5 | `PPARGC1A` | nuclear mitochondrial biogenesis | 11 contexts across 9 cell types; 9 up / 2 down | A broader upstream compensation program that may modify, rather than initiate, OXPHOS loss |
| 6 | `SMARCD3` | chromatin/mitochondrial-biogenesis program | 19 contexts across 14 cell types and all six strata; 16 up / 3 down | A broadly responsive chromatin regulator whose network position may distinguish driver from generic response |

Two rankings should be kept separate. By **local sex/APOE evidence**, `ATP5IF1` is first and `PPARGC1B` is the most stratum-specific. By **triangulation with prior AD perturbation evidence**, `TUFM` is strongest. The recommended first experimental wave should therefore treat `TUFM` and `ATP5IF1` as co-leads, followed by `TOMM7`; `PPARGC1B` is the high-value male-ε2 hypothesis, `PPARGC1A` is a dose-sensitive positive-control axis, and `SMARCD3` is the deliberately exploratory/network-dependent candidate.

`ATP5IF1` has the best integrated local evidence. It is increased in four female-ε2 contexts but decreased in ten female-ε4 contexts and predominantly decreased in male ε2, ε3/ε3, and ε4. It reverses from female ε2 to female ε4 in `Exc L4-5 RORB IL1RAPL2` (`+0.420` to `−0.519`) and `Exc L5/6 IT Car3` (`+0.429` to `−0.814`), from female to male ε2 in `Exc L4-5 RORB IL1RAPL2` (`+0.420` to `−0.497`), and from female to male ε4 in `Exc RELN CHD7` (`−1.029` to `+0.801`). This makes it the best analogue of Yu’s detailed `CLU` vignette.

`PPARGC1B` is the sharpest interaction-specific hypothesis. Its expression is significantly higher in AD in 11 male-ε2 cell types and in no other stratum. Because OXPHOS is mainly lower in male ε2, `PPARGC1B` induction may be an attempted compensatory response rather than the cause of respiratory-chain loss. That apparent upstream/downstream mismatch is experimentally informative: suppressing or augmenting `PPARGC1B` can test whether the response is protective, ineffective, or maladaptive.

`TUFM` and `TOMM7` show clean sex reversals within ε2. `TUFM` changes from `+0.506` in female ε2 to `−0.939` in male ε2 in `Ast GRM3`. `TOMM7` changes from female up to male down in `Exc L3-4 RORB CUX2` (`+0.460` versus `−0.837`) and `Exc L4-5 RORB IL1RAPL2` (`+0.619` versus `−0.582`). These provide distinct mitochondrial translation and organelle-surveillance perturbation axes.

`PPARGC1A` and `SMARCD3` are included because a true pathway regulator need not be localized to mitochondria. They were excluded from the primary similarity universe by design, so they have no core-mito Phase 10 rank or pathway-tail support. Their priority depends more heavily on network key-driver and genetic validation.

### What prior perturbation studies add to the regulator ranking

| Candidate | Prior experimental evidence | Implication for this study |
|---|---|---|
| `TUFM` | TUFM fell in aged APP/PS1 hippocampus/cortex; knockdown increased ROS, BACE1/Aβ, apoptosis, and selected tau phosphorylation, while overexpression produced the reciprocal effects in cell models ([Zhong et al., 2021](https://doi.org/10.1096/fj.202002461R)). | Strongest direct AD-like mechanistic triangulation. Test whether restoring TUFM rescues female-ε4 and male-ε2 mitochondrial translation and respiration, while recognizing that the published work did not test sex or APOE. |
| `ATP5IF1` | Neuron-specific loss or overexpression in mice changed the fraction of active ATP synthase, respiration, mtROS signaling, synaptic transmission, and cognition; loss impaired memory and overexpression enhanced learning ([Esparza-Moltó et al., 2021](https://doi.org/10.1371/journal.pbio.3001252)). | Strong functional control point, but not an AD/APOE study. Because IF1-dependent mtROS can be mitohormetic, “more is better” is not justified; use bidirectional and dose-response perturbation. |
| `TOMM7` | A genome-wide functional screen showed that TOMM7 is required to stabilize PINK1 on damaged mitochondria and enable Parkin recruitment/mitophagy, including validation in iPSC-derived neurons ([Hasson et al., 2013](https://doi.org/10.1038/nature12748)). PINK1 restoration is beneficial in AD models ([Du et al., 2017](https://doi.org/10.1093/brain/awx258)). | Strong pathway mechanism but indirect AD evidence: no study located directly tests TOMM7 in AD, APOE, or sex. Measure PINK1 stabilization and mitophagy flux, not only OXPHOS RNA. |
| `PPARGC1B` | APOE4 neurons showed reduced PGC-1β together with respiratory-chain and bioenergetic deficits ([Qi et al., 2021](https://doi.org/10.1016/j.celrep.2020.108572)). In rat cortical neurons and N2a cells, Aβ25–35 lowered PGC-1β, whereas PGC-1β overexpression suppressed mTOR through a SIRT1/PPARγ-dependent mechanism; Tg2576 cortex also showed lower PGC-1β and higher mTOR ([Liu et al., 2017](https://doi.org/10.1007/s10571-016-0425-5)). | Adds preclinical AD relevance to an APOE-sensitive biogenesis axis, but neither study tests sex-by-APOE interaction or ε2. Because prior adverse models show loss while the local male-ε2 response is uniformly increased, compensation remains the leading interpretation until bidirectional perturbation resolves it. |
| `PPARGC1A` | PGC-1α decreased with dementia and amyloid pathology in human AD hippocampus ([Qin et al., 2009](https://doi.org/10.1001/archneurol.2008.588)); brain gene transfer lowered BACE1/Aβ and improved memory in APP23 mice ([Katsouri et al., 2016](https://doi.org/10.1073/pnas.1606171113)). Conversely, sustained overexpression increased amyloid, phospho-tau, and neuronal loss in another transgenic AD model ([Dumont et al., 2014](https://doi.org/10.1096/fj.13-236331)). | Biologically credible but explicitly dose-, model-, and stage-dependent. It is a useful benchmark, not a reason to assume activation will be protective in every stratum. |
| `SMARCD3` | No convincing primary study was located that directly links SMARCD3 to mitochondrial control in AD, sex–APOE biology, or brain-cell respiration. | Highest-novelty and highest-risk candidate. Retain only if cell-type network KDA or chromatin evidence places it upstream of the local mitochondrial signature. |

This evidence-qualified ranking avoids a common inversion: recurrent respiratory-chain subunits are excellent phenotype sentinels, whereas an experimentally useful regulator must alter the phenotype when perturbed. Prior sex-specific AD network work provides a close methodological precedent—network nomination followed by genotype- and sex-aware perturbation identified `LRP10` effects that varied by sex and APOE ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5)). A broader AD multi-omic study similarly took `ATP6V1A` from predicted neuronal driver to CRISPR perturbation and pharmacologic rescue ([Wang et al., 2021](https://doi.org/10.1016/j.neuron.2020.11.002)). Neither study validates the mitochondrial candidates here; they establish the evidentiary standard those candidates should meet.

### Secondary candidates and phenotype sentinels

Secondary perturbation candidates are:

- `HSPD1`, the broadest core-mito proteostasis candidate (37 contexts, 5 up / 32 down), especially for the female-ε4 chaperone-loss phenotype;
- `UQCC2`, a Complex III assembly factor with 8 of its 12 significant contexts increased in male ε2, potentially another compensatory response;
- `HSF1`, `ESRRA`, `NR1D1`, and `GABPB1`, upstream extended-set candidates with weaker or more cell-restricted local evidence;
- `SIRT3`, a literature-supported orthogonal comparator that should be scored against the local data: one human AD-cortex study found lower SIRT3 and showed that SIRT3 overexpression reversed mitochondrial p53-mediated repression of `MT-ND2`/`MT-ND4`, excess ROS, and lower oxygen consumption ([Lee et al., 2018](https://doi.org/10.1111/acel.12679)); APOE4 mice, APOE-isogenic neurons, and human APOE4-carrier temporal cortex also showed lower PGC-1α/SIRT3-axis measures ([Yin et al., 2019](https://doi.org/10.18632/aging.102516); [Yin et al., 2020](https://doi.org/10.1212/WNL.0000000000009582)); however, an earlier human AD study found increased SIRT3 RNA and cleaved protein and showed SIRT3 induction by oxidative stress ([Weir et al., 2012](https://doi.org/10.1371/journal.pone.0048225));
- `FIS1`, `SLIRP`, and `APOO`, strong dynamics, mtRNA, or cristae-effector candidates that may be downstream responders; and
- `FKBP8`, a biologically plausible mitophagy candidate whose direction is highly context dependent.

The external evidence for `HSPD1` and `UQCC2` as AD key regulators is much thinner than their local recurrence. `HSPD1` is best treated initially as a proteostasis readout, and `UQCC2` as a Complex III assembly/compensation hypothesis. In particular, `UQCC2` is an assembly factor and should not be conflated with the structurally distinct Complex III core protein `UQCRC2`, for which there is a different literature. `SIRT3` has stronger prior mechanistic and human-APOE evidence but weaker stated local support; its conflicting reported direction makes enzyme activity and downstream mitochondrial acetylation/respiration more informative than transcript abundance alone. Including it as a literature-supported challenger can reveal whether the local ranking outperforms literature-only nomination.

The best pharmacodynamic or pathway readouts should be kept separate from perturbation targets:

- `MT-ND2`: 102 significant contexts and all six low tails;
- `MT-ND4`: 77 contexts;
- `MT-CO2`: 67 contexts;
- `COX4I1`: 46 contexts;
- `ATP5F1E`: 41 contexts; and
- `COX5B`: 37 contexts.

These genes strongly report the mitochondrial phenotype, but their recurrence does not demonstrate upstream control.

## Working biological model

The data support a testable, restrained model:

1. AD is associated with coordinated respiratory-chain transcriptional remodeling rather than a uniform mitochondrial response.
2. APOE genotype changes the direction of the sex effect. In ε2, females tend to activate OXPHOS while males suppress it. In ε4, females tend to suppress OXPHOS while males show a weaker, mixed, or selected compensatory increase.
3. The most coherent switches occur in superficial and RELN-positive excitatory neurons, with secondary effects in astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`.
4. Female ε4 and male ε2 also show loss or remodeling of chaperone, import, translation, mitophagy, and redox programs, suggesting that the respiratory signature is embedded in broader mitochondrial maintenance stress.
5. Induction of nuclear biogenesis regulators, especially `PPARGC1B` in male ε2, may represent compensation for a failing downstream respiratory program.

This model predicts that the same perturbation will have different consequences depending on APOE genotype and sex context. It also predicts that transcript restoration alone may not normalize respiratory function if assembly, import, or proteostasis is limiting.

## Limitations

1. **No formal interaction test.** Separate significance in one stratum and not another does not prove AD-by-sex or AD-by-APOE interaction. The exact direction reversals are compelling hypotheses, not interaction-test results.
2. **Nuclei are the MAST observations.** The current branch includes relevant covariates but no donor random effect. Donors, not nuclei, are the biological replicates.
3. **Unequal and small strata.** Male ε2 has only 7 AD and 6 NCI donors globally, and three fine-cell contrasts are not estimable. Nulls and large recurrence counts both need donor-aware confirmation.
4. **Threshold dependence.** The Zhang–Yu score uses `−1/0/+1` DEG states and discards continuous effect magnitude. Most informative pairs are one-stratum-only threshold crossings.
5. **No significant gene-level similarity result.** All six mitochondrial directional-FDR families have zero hits. Low-tail genes and regulator scores are descriptive nominations.
6. **Large fixed tails.** A 200-gene query comprises approximately 27%–29% of each eligible core-mito background.
7. **Pathway redundancy.** C2:CP neurodegenerative-disease and respiratory pathways reuse the same OXPHOS genes. MitoCarta’s focused hierarchy is the more interpretable summary.
8. **Transcript is not respiratory flux.** Lower OXPHOS RNA does not directly establish lower oxygen consumption, ATP production, complex activity, membrane potential, or mitochondrial abundance.
9. **mtDNA expression is technically sensitive.** Cell quality, agonal state, postmortem effects, and mitochondrial RNA fraction can alter mtDNA transcripts. Persistence among nuclear OXPHOS genes strengthens the result but does not eliminate these concerns.
10. **Extended regulators were outside the primary score.** Their nomination comes from the Figure 1 direct-state artifact and curated extended mitochondrial pathways, not from Phase 10 similarity inference.
11. **No causal network or genetics layer is present locally.** Bayesian-network KDA, coexpression centrality, AD GWAS, brain eQTL/sQTL, TWAS, colocalization, and perturbation evidence have not yet been integrated.
12. **No independent cohort.** This is a focused reanalysis of the same ROSMAP data used by Yu. Medication-history and ancestry limitations discussed by Yu also apply.
13. **The prior-art studies are heterogeneous and partly overlapping.** Many assess baseline APOE genotype rather than AD-versus-NCI change, and their endpoints range from FDG uptake and serum metabolites to RNA, protein, or respiratory flux. ADNI-based clinical studies and ROSMAP-based molecular studies share participants to varying degrees, so citation count must not be mistaken for independent replication.

## Recommended confirmation and experimental sequence

### 1. Confirm the statistical interaction at the donor level

- Build donor-by-cell-type pseudobulk profiles for the leading excitatory clusters, `Ast GRM3`, OPC, and `Mic P2RY12`.
- Fit targeted AD-by-sex contrasts within each APOE group and AD-by-APOE contrasts within sex. If supported by sample size, fit the three-way AD-by-sex-by-APOE term.
- Test OXPHOS, complexes I/III/IV/V, translation, import, chaperone, mitophagy, and ROS programs with direction-aware ranked gene-set methods rather than only DEG overrepresentation.
- Model mtDNA- and nuclear-encoded OXPHOS components separately, followed by a direct mitonuclear-balance test.

### 2. Run cell-type-specific network key-driver analysis

- Map each fine cluster to the closest available ROSMAP coexpression and Bayesian network.
- Use pathway- and stratum-specific mitochondrial DEG signatures as queries, with all tested genes represented in the matching network as the background.
- Test directed one- and two-step neighborhoods for DEG enrichment, apply BH correction across candidate drivers, and record whether the direction of network edges agrees with the observed expression response.
- Require a final key driver to have local DEG or regulator evidence, significant network-neighborhood enrichment in a relevant cell type, and replication across a related cluster or independent network.
- Treat `MT-ND2`, `MT-ND4`, `MT-CO2`, `COX4I1`, and `ATP5F1E` as pathway readouts unless the network analysis provides unexpected upstream evidence.

### 3. Add orthogonal prioritization evidence

- AD GWAS fine-mapped genes and credible sets;
- cell-type brain eQTL/sQTL and TWAS colocalization;
- AD brain proteomic and phosphoproteomic replication;
- transcription-factor target and chromatin-accessibility support;
- essentiality, dosage tolerance, subcellular localization, and perturbation tractability; and
- evidence that the candidate changes mitochondrial function rather than only responding to it.

Genetic evidence should be an orthogonal score, not a substitute for the sex/APOE-specific expression and network evidence.

### 4. Perturb a mechanistically diverse panel

Begin with co-leads `TUFM` and `ATP5IF1`, followed by `TOMM7`, `PPARGC1B`, `PPARGC1A`, and the exploratory `SMARCD3`; include `SIRT3` as a literature-supported comparator. Use APOE-isogenic ε2/ε3/ε4 panels in multiple XX and XY donor backgrounds, differentiated into cortical neurons and astrocytes and then tested both separately and in co-culture. Use both loss- and gain-of-function and dose-response designs where feasible, because the human and prior experimental data both indicate that direction and coupling efficiency depend on context.

Primary readouts should include:

- oxygen-consumption and extracellular-acidification rates;
- ATP abundance and ATP synthase activity;
- complexes I, III, IV, and V abundance and activity;
- mitochondrial membrane potential and ROS;
- mitochondrial mass, morphology, and mitophagy flux;
- ATP-linked respiration, proton leak, and coupling efficiency, which distinguish productive OXPHOS from compensatory or uncoupled respiration;
- APOE expression and secretion; and
- the structural sentinels `MT-ND2`, `MT-ND4`, `MT-CO2`, `COX4I1`, `COX5B`, and `ATP5F1E`.

A particularly informative design would restore `TUFM`, `ATP5IF1`, or `TOMM7` in the male-ε2 and female-ε4 contexts, where they tend to fall, while performing the reciprocal perturbation in female ε2. For `TOMM7`, include PINK1 stabilization and Parkin recruitment as proximal readouts. For `PPARGC1B`, the first question should be whether its male-ε2 induction is protective compensation: knockdown should worsen respiratory phenotypes if it is protective and improve them if it is maladaptive.

## Conclusion

The most defensible conclusion is that AD-associated mitochondrial transcription is **jointly conditioned by sex, APOE genotype, and cell type**. OXPHOS is the dominant divergent pathway, but its direction changes across strata: female ε2 is predominantly upward, male ε2 and female ε4 are predominantly downward, and male ε4 is mixed with selected excitatory increases. The effect is strongest in superficial and RELN-positive excitatory neurons and is accompanied by changes in mitochondrial translation, protein import, chaperones, mitophagy, and redox defense.

`ATP5IF1` is the strongest mitochondrial-localized candidate from the local sex/APOE data, whereas `TUFM` has the strongest direct AD-like perturbation evidence in prior work; they are the recommended co-leads. `TOMM7` provides a mechanistically precise import/mitophagy axis, and `PPARGC1B` is the most distinctive male-ε2 compensation hypothesis. `PPARGC1A` is a useful but dose-sensitive benchmark, while `SMARCD3` should remain exploratory unless network or chromatin evidence supports an upstream role. These genes should be called **pre-network priorities**, not key drivers, until donor-aware interaction tests, cell-type Bayesian-network KDA, genetic integration, and perturbation experiments establish causality.

## Source map

Primary local results:

- [Figure 1A: direct mitochondrial DEG burden](../../../results/figures/figure01/figure01A_mitochondrial_yu_analogue.svg)
- [Figure 1C: female APOE comparisons](../../../results/figures/figure01/figure01C_mitochondrial_yu_analogue.svg)
- [Figure 1D: male APOE comparisons](../../../results/figures/figure01/figure01D_mitochondrial_yu_analogue.svg)
- [Figure 1E: sex comparisons within APOE](../../../results/figures/figure01/figure01E_mitochondrial_yu_analogue.svg)
- [Figures 3–6 captions](../../../results/figures/figures03_to_06/figure_captions.md)
- [Phase 09 mitochondrial DEG table](../../../results/minerva_production/09_annotate_genes/deg_mito_core.tsv.gz)
- [Phase 10 similarity results](../../../results/minerva_production/10_similarity/mitochondrial_similarity_results.tsv.gz)
- [Phase 10 paired states](../../../results/minerva_production/10_similarity/mitochondrial_similarity_state_pairs.tsv.gz)
- [Phase 11 pathway results](../../../results/minerva_production/11_pathway/similarity_tail_pathway_ora.tsv.gz)
- [Current pre-network candidate table](pre_network_shortlist.tsv)
- [Current pre-network stratum summary](pre_network_shortlist_strata.tsv)
- [Yu paper PDF](../../yu_paper/Yu_sex_apoe.pdf)

Pathway annotation uses [MitoCarta3.0](https://doi.org/10.1093/nar/gkaa1011), whose MitoPathways hierarchy contains overlapping broad and detailed annotations. All numerical pathway claims above use the stored Phase 11 query-specific BH FDR rather than visual rank alone.

## References

- Altmann A, Tian L, Henderson VW, Greicius MD. Sex modifies the APOE-related risk of developing Alzheimer disease. *Annals of Neurology*. 2014;75(4):563–573. [doi:10.1002/ana.24135](https://doi.org/10.1002/ana.24135)
- Arnold M, Nho K, Kueider-Paisley A, et al. Sex and APOE ε4 genotype modify the Alzheimer’s disease serum metabolome. *Nature Communications*. 2020;11:1148. [doi:10.1038/s41467-020-14959-w](https://doi.org/10.1038/s41467-020-14959-w)
- Beck JS, Mufson EJ, Counts SE. Evidence for mitochondrial UPR gene activation in familial and sporadic Alzheimer’s disease. *Current Alzheimer Research*. 2016;13(6):610–614. [doi:10.2174/1567205013666151221145445](https://doi.org/10.2174/1567205013666151221145445)
- Belonwu SA, Li Y, Bunis D, et al. Sex-stratified single-cell RNA-seq analysis identifies sex-specific and cell type-specific transcriptional responses in Alzheimer’s disease across two brain regions. *Molecular Neurobiology*. 2022;59:276–293. [doi:10.1007/s12035-021-02591-8](https://doi.org/10.1007/s12035-021-02591-8)
- Bubber P, Haroutunian V, Fisch G, Blass JP, Gibson GE. Mitochondrial abnormalities in Alzheimer brain: mechanistic implications. *Annals of Neurology*. 2005;57(5):695–703. [doi:10.1002/ana.20474](https://doi.org/10.1002/ana.20474)
- Budny V, Bodenmann C, Zürcher KJ, et al. APOE genotype-dependent differences in human astrocytic energy metabolism. *Frontiers in Cellular Neuroscience*. 2025;19:1603657. [doi:10.3389/fncel.2025.1603657](https://doi.org/10.3389/fncel.2025.1603657)
- Du F, Yu Q, Yan S, et al. PINK1 signalling rescues amyloid pathology and mitochondrial dysfunction in Alzheimer’s disease. *Brain*. 2017;140(12):3233–3251. [doi:10.1093/brain/awx258](https://doi.org/10.1093/brain/awx258)
- Dumont M, Stack C, Elipenahli C, et al. PGC-1α overexpression exacerbates β-amyloid and tau deposition in a transgenic mouse model of Alzheimer’s disease. *The FASEB Journal*. 2014;28(4):1745–1755. [doi:10.1096/fj.13-236331](https://doi.org/10.1096/fj.13-236331)
- Esparza-Moltó PB, Romero-Carramiñana I, Núñez de Arenas C, et al. Generation of mitochondrial reactive oxygen species is controlled by ATPase inhibitory factor 1 and regulates cognition. *PLoS Biology*. 2021;19(5):e3001252. [doi:10.1371/journal.pbio.3001252](https://doi.org/10.1371/journal.pbio.3001252)
- Fang EF, Hou Y, Palikaras K, et al. Mitophagy inhibits amyloid-β and tau pathology and reverses cognitive deficits in models of Alzheimer’s disease. *Nature Neuroscience*. 2019;22(3):401–412. [doi:10.1038/s41593-018-0332-9](https://doi.org/10.1038/s41593-018-0332-9)
- Farmer BC, Kluemper J, Johnson LA, et al. APOE4 lowers energy expenditure in females and impairs glucose oxidation by increasing flux through aerobic glycolysis. *Molecular Neurodegeneration*. 2021;16:62. [doi:10.1186/s13024-021-00483-y](https://doi.org/10.1186/s13024-021-00483-y)
- Guo L, Cao J, Hou J, et al. Sex specific molecular networks and key drivers of Alzheimer’s disease. *Molecular Neurodegeneration*. 2023;18:39. [doi:10.1186/s13024-023-00624-5](https://doi.org/10.1186/s13024-023-00624-5)
- Hasson SA, Kane LA, Yamano K, et al. High-content genome-wide RNAi screens identify regulators of Parkin upstream of mitophagy. *Nature*. 2013;504:291–295. [doi:10.1038/nature12748](https://doi.org/10.1038/nature12748)
- Jett S, Dyke JP, Boneu Yepez C, et al. Effects of sex and APOE ε4 genotype on brain mitochondrial high-energy phosphates in midlife individuals at risk for Alzheimer’s disease: a 31-phosphorus MR spectroscopy study. *PLoS One*. 2023;18(2):e0281302. [doi:10.1371/journal.pone.0281302](https://doi.org/10.1371/journal.pone.0281302)
- Katsouri L, Lim YM, Blondrath K, et al. PPARγ-coactivator-1α gene transfer reduces neuronal loss and amyloid-β generation by reducing β-secretase in an Alzheimer’s disease model. *Proceedings of the National Academy of Sciences of the United States of America*. 2016;113(43):12292–12297. [doi:10.1073/pnas.1606171113](https://doi.org/10.1073/pnas.1606171113)
- Klein H-U, Trumpff C, Yang H-S, et al. Characterization of mitochondrial DNA quantity and quality in the human aged and Alzheimer’s disease brain. *Molecular Neurodegeneration*. 2021;16:75. [doi:10.1186/s13024-021-00495-8](https://doi.org/10.1186/s13024-021-00495-8)
- Lee H, Cho S, Kim M-J, et al. ApoE4-dependent lysosomal cholesterol accumulation impairs mitochondrial homeostasis and oxidative phosphorylation in human astrocytes. *Cell Reports*. 2023;42:113183. [doi:10.1016/j.celrep.2023.113183](https://doi.org/10.1016/j.celrep.2023.113183)
- Lee J, Kim Y, Liu T, et al. SIRT3 deregulation is linked to mitochondrial dysfunction in Alzheimer’s disease. *Aging Cell*. 2018;17(1):e12679. [doi:10.1111/acel.12679](https://doi.org/10.1111/acel.12679)
- Leng K, Li E, Eser R, et al. Molecular characterization of selectively vulnerable neurons in Alzheimer’s disease. *Nature Neuroscience*. 2021;24:276–287. [doi:10.1038/s41593-020-00764-7](https://doi.org/10.1038/s41593-020-00764-7)
- Li Z, Martens YA, Ren Y, et al. APOE genotype determines cell-type-specific pathological landscape of Alzheimer’s disease. *Neuron*. 2025;113(9):1380–1397.e7. [doi:10.1016/j.neuron.2025.02.017](https://doi.org/10.1016/j.neuron.2025.02.017)
- Liu C-C, Zhao J, Fu Y, et al. Peripheral apoE4 enhances Alzheimer’s pathology and impairs cognition by compromising cerebrovascular function. *Nature Neuroscience*. 2022;25:1020–1033. [doi:10.1038/s41593-022-01127-0](https://doi.org/10.1038/s41593-022-01127-0)
- Liu Y-C, Gao X-X, Zhang Z-G, Lin Z-H, Zou Q-L. PPAR gamma coactivator 1 beta (PGC-1β) reduces mammalian target of rapamycin (mTOR) expression via a SIRT1-dependent mechanism in neurons. *Cellular and Molecular Neurobiology*. 2017;37(5):879–887. [doi:10.1007/s10571-016-0425-5](https://doi.org/10.1007/s10571-016-0425-5)
- Lunnon K, Keohane A, Pidsley R, et al. Mitochondrial genes are altered in blood early in Alzheimer’s disease. *Neurobiology of Aging*. 2017;53:36–47. [doi:10.1016/j.neurobiolaging.2016.12.029](https://doi.org/10.1016/j.neurobiolaging.2016.12.029)
- Mathys H, Boix CA, Akay LA, et al. Single-cell multiregion dissection of Alzheimer’s disease. *Nature*. 2024;632:858–868. [doi:10.1038/s41586-024-07606-7](https://doi.org/10.1038/s41586-024-07606-7)
- Mathys H, Davila-Velderrain J, Peng Z, et al. Single-cell transcriptomic analysis of Alzheimer’s disease. *Nature*. 2019;570(7761):332–337. [doi:10.1038/s41586-019-1195-2](https://doi.org/10.1038/s41586-019-1195-2)
- Moser VA, Workman MJ, Hurwitz SJ, et al. Microglial transcription profiles in mouse and human are driven by APOE4 and sex. *iScience*. 2021;24(11):103238. [doi:10.1016/j.isci.2021.103238](https://doi.org/10.1016/j.isci.2021.103238)
- Neu SC, Pa J, Kukull W, et al. Apolipoprotein E genotype and sex risk factors for Alzheimer disease: a meta-analysis. *JAMA Neurology*. 2017;74(10):1178–1189. [doi:10.1001/jamaneurol.2017.2188](https://doi.org/10.1001/jamaneurol.2017.2188)
- Qi G, Mi Y, Shi X, Gu H, Brinton RD, Yin F. ApoE4 impairs neuron–astrocyte coupling of fatty acid metabolism. *Cell Reports*. 2021;34(1):108572. [doi:10.1016/j.celrep.2020.108572](https://doi.org/10.1016/j.celrep.2020.108572)
- Qin W, Haroutunian V, Katsel P, et al. PGC-1α expression decreases in the Alzheimer disease brain as a function of dementia. *Archives of Neurology*. 2009;66(3):352–361. [doi:10.1001/archneurol.2008.588](https://doi.org/10.1001/archneurol.2008.588)
- Rath S, Sharma R, Gupta R, et al. MitoCarta3.0: an updated mitochondrial proteome now with sub-organelle localization and pathway annotations. *Nucleic Acids Research*. 2021;49(D1):D1541–D1547. [doi:10.1093/nar/gkaa1011](https://doi.org/10.1093/nar/gkaa1011)
- Sampedro F, Vilaplana E, de Leon MJ, et al. APOE-by-sex interactions on brain structure and metabolism in healthy elderly controls. *Oncotarget*. 2015;6:26663–26674. [doi:10.18632/oncotarget.5185](https://doi.org/10.18632/oncotarget.5185)
- Schmukler E, Solomon S, Simonovitch S, et al. Altered mitochondrial dynamics and function in APOE4-expressing astrocytes. *Cell Death & Disease*. 2020;11:578. [doi:10.1038/s41419-020-02776-4](https://doi.org/10.1038/s41419-020-02776-4)
- Sundermann EE, Tran M, Maki PM, Bondi MW. Sex differences in the association between apolipoprotein E ε4 allele and Alzheimer’s disease markers. *Alzheimer’s & Dementia: Diagnosis, Assessment & Disease Monitoring*. 2018;10:438–447. [doi:10.1016/j.dadm.2018.06.004](https://doi.org/10.1016/j.dadm.2018.06.004)
- Tcw J, Qian L, Pipalia NH, et al. Cholesterol and matrisome pathways dysregulated in astrocytes and microglia. *Cell*. 2022;185(13):2213–2233.e25. [doi:10.1016/j.cell.2022.05.017](https://doi.org/10.1016/j.cell.2022.05.017)
- Terni B, Boada J, Portero-Otin M, Pamplona R, Ferrer I. Mitochondrial ATP-synthase in the entorhinal cortex is a target of oxidative stress at stages I/II of Alzheimer’s disease pathology. *Brain Pathology*. 2010;20(1):222–233. [doi:10.1111/j.1750-3639.2009.00266.x](https://doi.org/10.1111/j.1750-3639.2009.00266.x)
- Trumpff C, Owusu-Ansah E, Klein H-U, et al. Mitochondrial respiratory chain protein co-regulation in the human brain. *Heliyon*. 2022;8(5):e09353. [doi:10.1016/j.heliyon.2022.e09353](https://doi.org/10.1016/j.heliyon.2022.e09353)
- Troutwine BR, Strope TA, Franczak E, et al. Mitochondrial function and Aβ in Alzheimer’s disease postmortem brain. *Neurobiology of Disease*. 2022;171:105781. [doi:10.1016/j.nbd.2022.105781](https://doi.org/10.1016/j.nbd.2022.105781)
- Valla J, Berndt JD, Gonzalez-Lima F. Energy hypometabolism in posterior cingulate cortex of Alzheimer’s patients: superficial laminar cytochrome oxidase associated with disease duration. *Journal of Neuroscience*. 2001;21(13):4923–4930. [doi:10.1523/JNEUROSCI.21-13-04923.2001](https://doi.org/10.1523/JNEUROSCI.21-13-04923.2001)
- Valla J, Yaari R, Wolf AB, et al. Reduced posterior cingulate mitochondrial activity in expired young adult carriers of the APOE ε4 allele, the major late-onset Alzheimer’s susceptibility gene. *Journal of Alzheimer’s Disease*. 2010;22(1):307–313. [doi:10.3233/JAD-2010-100129](https://doi.org/10.3233/JAD-2010-100129)
- Wang H, Dey KK, Chen P-C, et al. Integrated analysis of ultra-deep proteomes in cortex, cerebrospinal fluid and serum reveals a mitochondrial signature in Alzheimer’s disease. *Molecular Neurodegeneration*. 2020;15:43. [doi:10.1186/s13024-020-00384-6](https://doi.org/10.1186/s13024-020-00384-6)
- Wang M, Li A, Sekiya M, et al. Transformative network modeling of multi-omics data reveals detailed circuits, key regulators, and potential therapeutics for Alzheimer’s disease. *Neuron*. 2021;109(2):257–272.e14. [doi:10.1016/j.neuron.2020.11.002](https://doi.org/10.1016/j.neuron.2020.11.002)
- Weir HJM, Murray TK, Kehoe PG, et al. CNS SIRT3 expression is altered by reactive oxygen species and in Alzheimer’s disease. *PLoS One*. 2012;7(11):e48225. [doi:10.1371/journal.pone.0048225](https://doi.org/10.1371/journal.pone.0048225)
- Wu L, Zhang X, Zhao L. Human ApoE isoforms differentially modulate brain glucose and ketone body metabolism: implications for Alzheimer’s disease risk reduction and early intervention. *Journal of Neuroscience*. 2018;38(30):6665–6681. [doi:10.1523/JNEUROSCI.2262-17.2018](https://doi.org/10.1523/JNEUROSCI.2262-17.2018)
- Wynne ME, et al. APOE expression and secretion are modulated by mitochondrial dysfunction. *eLife*. 2023;12:e85779. [doi:10.7554/eLife.85779](https://doi.org/10.7554/eLife.85779)
- Yang AJT, Mohammad A, Crozier RWE, et al. Differences in inflammatory markers, mitochondrial function, and synaptic proteins in male and female Alzheimer’s disease post mortem brains. *Alzheimer’s & Dementia*. 2025;21(10):e70645. [doi:10.1002/alz.70645](https://doi.org/10.1002/alz.70645)
- Yin J, Nielsen M, Carcione T, Li S, Shi J. Apolipoprotein E regulates mitochondrial function through the PGC-1α-sirtuin 3 pathway. *Aging*. 2019;11(23):11148–11156. [doi:10.18632/aging.102516](https://doi.org/10.18632/aging.102516)
- Yin J, Reiman EM, Beach TG, et al. Effect of ApoE isoforms on mitochondria in Alzheimer disease. *Neurology*. 2020;94(23):e2404–e2411. [doi:10.1212/WNL.0000000000009582](https://doi.org/10.1212/WNL.0000000000009582)
- Yu G, Thorpe A, Zeng Q, et al. Single-cell transcriptomic analysis reveals APOE genotype-dependent sex differences in Alzheimer’s disease. *Alzheimer’s & Dementia*. 2026;22(5):e71463. [doi:10.1002/alz.71463](https://doi.org/10.1002/alz.71463)
- Zhong B-R, Zhou G-F, Song L, et al. TUFM is involved in Alzheimer’s disease-like pathologies that are associated with ROS. *The FASEB Journal*. 2021;35(5):e21445. [doi:10.1096/fj.202002461R](https://doi.org/10.1096/fj.202002461R)
