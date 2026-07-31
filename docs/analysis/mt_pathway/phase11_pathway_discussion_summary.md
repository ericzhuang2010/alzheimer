# Sex- and APOE-dependent mitochondrial transcription in Alzheimer’s disease: five-page summary

> **Pagination note.** Markdown has no fixed page size. The five sections below are designed as five concise narrative pages, with explicit page breaks for conversion to PDF or Word. The complete reference list is retained after the five-page narrative and is not counted toward that page target.

## Page 1 of 5 — Main result and evidentiary status

### Main conclusion

The primary finding is a **sex- and APOE-dependent reversal of the Alzheimer’s disease (AD)-associated oxidative-phosphorylation (OXPHOS) response**, strongest in excitatory neurons:

| Stratum | Dominant AD-versus-NCI mitochondrial response |
|---|---|
| Female APOE ε2 | OXPHOS transcripts increase |
| Male APOE ε2 | OXPHOS transcripts decrease; largest total mitochondrial DEG burden |
| Female APOE ε4 | OXPHOS transcripts strongly decrease |
| Male APOE ε4 | Weaker, mixed response, including increases in selected excitatory subtypes |
| APOE ε3/ε3 | Lower aggregate mitochondrial burden, with strong effects confined to selected neuronal states |

This analysis therefore moves beyond the general conclusion that mitochondria are altered in AD. Its new contribution is that the **direction** of mitochondrial remodeling depends jointly on sex, APOE genotype, and cell type. The clearest new hypothesis is the female-ε2-up/male-ε2-down OXPHOS reversal. Female ε4 shows the strongest externally supported loss pattern, whereas the ε2 sex reversal currently has the least independent validation.

The result is a robust descriptive and pathway-level pattern, but **not a demonstrated causal interaction**. No mitochondrial gene passed the Phase 10 directional-similarity false-discovery-rate (FDR) threshold, and the current MAST models did not directly test AD-by-sex or AD-by-APOE interaction terms. A significant change in one stratum and no change in another is not itself a significant difference between strata. “Divergence” here therefore means different stratified AD-versus-no-cognitive-impairment (NCI) signatures, not a formally proven interaction or causal mechanism.

### What is established versus new

The analysis recapitulates within ROSMAP the broad mitochondrial, respiratory-chain, sex, and APOE signals reported by [Yu et al. (2026)](https://doi.org/10.1002/alz.71463). It does not constitute independent replication because it reanalyzes the same underlying resource. What is new is the prespecified mitochondrial focus, the explicit direction switch across sex–APOE strata, the localization of that switch to particular cell states, and the separation of strong pathway convergence from nonsignificant single-gene similarity results.

### Study design

After Yu-compatible exclusions, the cohort included 276 donors: 142 NCI and 134 AD. Within each of 54 fine cell types, AD was compared with NCI in six strata. Models adjusted for total RNA count, age at death, and postmortem interval. A DEG required within-contrast BH FDR `< 0.05` and absolute fold change `> 1.3`. Of 324 planned contrasts, 321 were estimable.

| Stratum | AD donors | NCI donors |
|---|---:|---:|
| Female ε2 carrier | 8 | 17 |
| Female ε3/ε3 | 37 | 45 |
| Female ε4 carrier | 26 | 11 |
| Male ε2 carrier | 7 | 6 |
| Male ε3/ε3 | 29 | 53 |
| Male ε4 carrier | 27 | 10 |

The analysis encoded each gene–cell-type AD effect as up (`+1`), nonsignificant (`0`), or down (`−1`) and compared these states across sex and genotype. Pathway tests used the 200 highest- and lowest-similarity mitochondrial genes against comparison-specific MitoCarta backgrounds ([Rath et al., 2021](https://doi.org/10.1093/nar/gkaa1011)). These are mitochondrial-domain enrichment tests, not transcriptome-wide tests.

<div style="page-break-after: always;"></div>

## Page 2 of 5 — Core quantitative findings

### Male ε2 has the greatest burden, but direction separates the strata

The mitochondrial DEG counts are gene-by-cell-type occurrences, not unique genes or independent biological replicates.

| Stratum | Significant / tested | AD up | AD down |
|---|---:|---:|---:|
| Female ε2 | 1,128 / 37,647 (3.00%) | 935 | 193 |
| Female ε3/ε3 | 821 / 36,775 (2.23%) | 554 | 267 |
| Female ε4 | 1,633 / 37,006 (4.41%) | 269 | 1,364 |
| Male ε2 | 3,753 / 35,380 (10.61%) | 1,613 | 2,140 |
| Male ε3/ε3 | 869 / 35,304 (2.46%) | 377 | 492 |
| Male ε4 | 1,058 / 35,290 (3.00%) | 510 | 548 |

Male ε2 has by far the largest response, spanning excitatory and inhibitory neurons, astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`. Its small sample—7 AD and 6 NCI donors—makes this both an important finding and the highest-priority target for donor-aware validation.

### OXPHOS is the dominant recurring pathway

OXPHOS subunits are the most recurrently altered mitochondrial program in all six strata:

| Stratum | OXPHOS occurrences / tested | AD up | AD down |
|---|---:|---:|---:|
| Female ε2 | 403 / 3,736 (10.79%) | 398 | 5 |
| Female ε3/ε3 | 332 / 3,677 (9.03%) | 319 | 13 |
| Female ε4 | 324 / 3,641 (8.90%) | 50 | 274 |
| Male ε2 | 659 / 3,505 (18.80%) | 95 | 564 |
| Male ε3/ε3 | 171 / 3,534 (4.84%) | 85 | 86 |
| Male ε4 | 227 / 3,589 (6.32%) | 141 | 86 |

Complexes I, III, IV, and V drive the signal; Complex II is much less involved. Complex IV is especially prominent. The pattern persists after excluding mtDNA-encoded genes: nuclear OXPHOS occurrences remain strongly up in female ε2 (`258 up / 4 down`) and strongly down in female ε4 (`17 / 234`) and male ε2 (`77 / 444`). In male ε3/ε3 and ε4, nuclear subunits more often decrease while mtDNA subunits often increase. This raises a **mitonuclear-discordance hypothesis**, but expression alone cannot establish mitonuclear imbalance.

All six low-similarity tails are enriched for OXPHOS (47–56 OXPHOS genes per 200-gene tail; 2.13–2.66-fold enrichment; BH FDR `1.99e-8` to `1.18e-16`). Thirty-five OXPHOS genes occur in every low tail, and 11 or 12 of 12 measured Complex IV genes occur in each comparison. Many nominal pathway labels—electron transport, aerobic respiration, and Alzheimer, Parkinson, or Huntington disease sets—reuse these same respiratory-chain genes and should be treated as one OXPHOS theme. Conversely, **zero individual genes pass directional BH FDR**; the smallest adjusted value is 0.743. Low-tail membership is prioritization evidence, not gene-level statistical significance.

### The clearest reversals are genotype-specific

Within ε2, 153 jointly tested OXPHOS gene–cell-type pairs show exact opposite directions, always female up and male down. `Exc L3-4 RORB CUX2` alone contains 31, including `COX5B` (`+0.740` versus `−1.247`), `NDUFB11` (`+0.858` versus `−1.911`), and `UQCRQ` (`+0.799` versus `−1.466`). The same direction appears in other superficial excitatory neurons, `Ast GRM3`, OPCs, inhibitory neurons, and male-ε2 `Mic P2RY12`.

Within ε4, female decreases contrast with selected male increases. `Exc RELN CHD7` contains 19 female-down/male-up reversals, including `NDUFB7` (`−2.011` versus `+2.322`), `UQCR10` (`−1.053` versus `+1.629`), and `ATP5F1E` (`−1.268` versus `+1.268`). Female ε4 also has 38 OXPHOS genes down in `Exc L2-3 CBLN2 LINC02306`. APOE ε3/ε3 has weaker aggregate divergence, although male `Exc NRGN` has 48 downregulated OXPHOS genes among 58 tested.

Most divergence across all mitochondrial genes is not an exact reversal: 89%–95% of informative pairs cross the DEG threshold in only one comparator. OXPHOS reversals within ε2 and selected ε4 excitatory states are the notable exceptions.

<div style="page-break-after: always;"></div>

## Page 3 of 5 — Biological interpretation and prior evidence

### Female ε4 has the strongest mechanistic convergence

Human risk, imaging, spectroscopy, and metabolomic studies support sex–APOE stratification, but they do not directly measure the local AD-associated mitochondrial transcript response. APOE ε4 has shown stronger associations with conversion or biomarker profiles in women in some age ranges, while ε2/ε3 appears more protective in women than men ([Altmann et al., 2014](https://doi.org/10.1002/ana.24135); [Neu et al., 2017](https://doi.org/10.1001/jamaneurol.2017.2188)). Female ε4 carriers have also shown hypometabolism, lower high-energy-phosphate ratios, and stronger serum metabolic associations in selected cohorts ([Sampedro et al., 2015](https://doi.org/10.18632/oncotarget.5185); [Jett et al., 2023](https://doi.org/10.1371/journal.pone.0281302); [Arnold et al., 2020](https://doi.org/10.1038/s41467-020-14959-w)). Counterevidence shows that APOE4 metabolic effects vary by age, disease stage, region, and endpoint ([Sundermann et al., 2018](https://doi.org/10.1016/j.dadm.2018.06.004)).

Experimental models give the female-ε4 decrease a plausible mechanism. APOE4 can shift metabolism toward glycolysis, reduce respiration and ATP-linked capacity, impair fatty-acid support between astrocytes and neurons, disrupt mitochondrial dynamics and mitophagy, and couple lysosomal cholesterol accumulation to defective mitochondrial clearance ([Farmer et al., 2021](https://doi.org/10.1186/s13024-021-00483-y); [Qi et al., 2021](https://doi.org/10.1016/j.celrep.2020.108572); [Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4); [Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). Female AD cortex has also shown lower Complex IV respiration ([Yang et al., 2025](https://doi.org/10.1002/alz.70645)). These studies converge with the local female-ε4 loss of OXPHOS, import, chaperone, mitophagy, and redox transcripts, but differ in species, tissue, stage, and outcome and therefore do not replicate it.

Higher transcription or respiration need not mean efficient energy production. APOE4 astrocytes have shown higher respiration alongside lower mitochondrial ATP production and greater proton leak ([Budny et al., 2025](https://doi.org/10.3389/fncel.2025.1603657)). Peripheral APOE4 can also combine lower endothelial mitochondrial programs with higher cytosolic heat-shock genes ([Liu et al., 2022](https://doi.org/10.1038/s41593-022-01127-0)). The local male-ε4 increases could therefore be compensatory or uncoupled rather than protective.

### The ε2 reversal is the most novel result

Female APOE2 mice show stronger glucose metabolism and predicted PPARγ/PGC-1α activity than APOE3 or APOE4 mice ([Wu et al., 2018](https://doi.org/10.1523/JNEUROSCI.2262-17.2018)), which is compatible with female-ε2 OXPHOS induction. It does not explain male-ε2 OXPHOS loss because that experiment used females, small groups, and baseline APOE comparisons rather than an AD response. No located primary study jointly tests APOE2, sex, AD, cell type, and mitochondrial function. The ε2 switch must therefore be presented as a specific, testable hypothesis, not as an established protective mechanism.

### Cell type and mitochondrial maintenance sharpen the model

Earlier single-cell studies show sex- and cell-state-dependent AD responses ([Mathys et al., 2019](https://doi.org/10.1038/s41586-019-1195-2); [Belonwu et al., 2022](https://doi.org/10.1007/s12035-021-02591-8)). RORB- and RELN-positive excitatory neurons are selectively vulnerable in AD, supporting the anatomic location—but not the sex/APOE direction—of the present effects ([Leng et al., 2021](https://doi.org/10.1038/s41593-020-00764-7); [Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). Genotype- and cell-type-dependent human AD responses and APOE4/sex-sensitive glial states further support donor-aware, cell-specific analysis ([Li et al., 2025](https://doi.org/10.1016/j.neuron.2025.02.017); [Moser et al., 2021](https://doi.org/10.1016/j.isci.2021.103238); [Tcw et al., 2022](https://doi.org/10.1016/j.cell.2022.05.017)).

Orthogonal human brain studies support OXPHOS dysfunction but expose key confounders. AD has been associated with lower respiratory-chain proteins, flux, Complex IV activity, and ATP-synthase activity or oxidative damage ([Trumpff et al., 2022](https://doi.org/10.1016/j.heliyon.2022.e09353); [Troutwine et al., 2022](https://doi.org/10.1016/j.nbd.2022.105781); [Valla et al., 2001](https://doi.org/10.1523/JNEUROSCI.21-13-04923.2001); [Valla et al., 2010](https://doi.org/10.3233/JAD-2010-100129); [Wang et al., 2020](https://doi.org/10.1186/s13024-020-00384-6); [Terni et al., 2010](https://doi.org/10.1111/j.1750-3639.2009.00266.x)). However, lower RNA or protein may reflect lower mitochondrial content, selective neuronal loss, or survivor bias. Nuclear and mtDNA components can also move differently ([Lunnon et al., 2017](https://doi.org/10.1016/j.neurobiolaging.2016.12.029)), and brain mtDNA copy number can fall in AD ([Klein et al., 2021](https://doi.org/10.1186/s13024-021-00495-8)). Stable TCA transcripts do not prove stable enzyme activity because AD brain shows nonuniform TCA-enzyme changes ([Bubber et al., 2005](https://doi.org/10.1002/ana.20474)).

Secondary programs are directionally coherent with a broader maintenance defect: female ε4 shows all-down mitochondrial chaperone occurrences and lower import and redox programs; male ε2 shows extensive translation and import remodeling; mitophagy is mainly up in female ε2 and down in male ε2. Bulk AD tissue has instead shown UPRmt activation and higher HSP60, implying cell-, stage-, or genotype-specific compensation ([Beck et al., 2016](https://doi.org/10.2174/1567205013666151221145445)). Mitophagy induction and PINK1 restoration improve AD-like phenotypes in models ([Fang et al., 2019](https://doi.org/10.1038/s41593-018-0332-9); [Du et al., 2017](https://doi.org/10.1093/brain/awx258)). Respiratory-chain disruption can itself increase APOE expression and secretion, so APOE and mitochondrial dysfunction may form a feedback loop rather than a one-way pathway ([Wynne et al., 2023](https://doi.org/10.7554/eLife.85779)).

<div style="page-break-after: always;"></div>

## Page 4 of 5 — Experimental priorities

The current data nominate regulators but cannot establish key drivers. A key-driver claim requires a directed network neighborhood enriched for the relevant mitochondrial signature, followed by causal perturbation. The existing core-MitoCarta prioritization also omits important nuclear regulators, including `PPARGC1A`, `PPARGC1B`, `ESRRA`, `NRF1`, `SMARCD3`, `NR1D1`, `HSF1`, and `GABPB1`.

### Recommended first-wave panel

| Priority | Candidate | Why it is prioritized | Direct test |
|---:|---|---|---|
| 1 | `ATP5IF1` | Strongest integrated local sex/APOE evidence: 34 DEG contexts, 20 cell types, 5/6 strata, and eight exact reversals | Test bidirectional, dose-dependent control of ATP synthase, ATP-linked respiration, mtROS, and coupling |
| 2 | `TUFM` | 19 contexts across all strata plus the strongest prior AD-like perturbation evidence | Restore mitochondrial translation in female ε4 and male ε2; measure respiration, ROS, amyloid, and tau-related outcomes |
| 3 | `TOMM7` | 25 contexts, all strata, and clean ε2 sex reversals; precise import/mitophagy mechanism | Measure PINK1 stabilization, Parkin recruitment, mitophagy flux, and OXPHOS |
| 4 | `PPARGC1B` | Eleven significant increases, all confined to male ε2 | Determine whether induction is protective compensation or maladaptive signaling |
| 5 | `PPARGC1A` | Plausible upstream biogenesis axis with extensive AD literature | Use as a dose- and stage-sensitive benchmark, not an assumed protective intervention |
| 6 | `SMARCD3` | Broad local response but little direct mechanistic evidence | Retain only if network or chromatin analysis places it upstream |

`ATP5IF1` best mirrors the overall direction switch: it rises in female ε2 but falls in female ε4 and most male contexts, including reversals in RORB- and RELN-positive excitatory neurons. Mouse studies show that changing ATPase inhibitory factor 1 alters active ATP synthase, respiration, mtROS, synaptic transmission, and cognition, but also show why dose and direction matter ([Esparza-Moltó et al., 2021](https://doi.org/10.1371/journal.pbio.3001252)).

`TUFM` falls in AD-like mouse brain, and its knockdown increases ROS, BACE1/Aβ, apoptosis, and selected tau phosphorylation; overexpression produces reciprocal effects ([Zhong et al., 2021](https://doi.org/10.1096/fj.202002461R)). `TOMM7` is required for PINK1 stabilization and Parkin recruitment after mitochondrial damage ([Hasson et al., 2013](https://doi.org/10.1038/nature12748)). These provide stronger causal anchors than expression recurrence alone.

`PPARGC1B` is most likely a male-ε2 compensation response because it rises where downstream OXPHOS predominantly falls. Prior APOE4 and amyloid models instead show reduced PGC-1β with energetic or signaling deficits ([Qi et al., 2021](https://doi.org/10.1016/j.celrep.2020.108572); [Liu et al., 2017](https://doi.org/10.1007/s10571-016-0425-5)). `PPARGC1A` is credible but context-dependent: it decreases with human AD severity, and experimental restoration can reduce amyloid and improve memory, yet sustained overexpression can worsen amyloid, phospho-tau, and neuronal loss ([Qin et al., 2009](https://doi.org/10.1001/archneurol.2008.588); [Katsouri et al., 2016](https://doi.org/10.1073/pnas.1606171113); [Dumont et al., 2014](https://doi.org/10.1096/fj.13-236331)).

`SIRT3` should be included as a literature-supported comparator. Some studies connect lower SIRT3 or PGC-1α/SIRT3 signaling to AD or APOE4 and show rescue of mitochondrial dysfunction after SIRT3 restoration ([Lee et al., 2018](https://doi.org/10.1111/acel.12679); [Yin et al., 2019](https://doi.org/10.18632/aging.102516); [Yin et al., 2020](https://doi.org/10.1212/WNL.0000000000009582)), whereas another reports increased SIRT3 RNA and cleaved protein in AD ([Weir et al., 2012](https://doi.org/10.1371/journal.pone.0048225)). Activity and mitochondrial acetylation are therefore more informative than transcript abundance alone.

Secondary candidates are `HSPD1` for the female-ε4 proteostasis phenotype; `UQCC2` for Complex III assembly or compensation; and `HSF1`, `ESRRA`, `NR1D1`, `GABPB1`, `FIS1`, `SLIRP`, `APOO`, and `FKBP8` for network-dependent follow-up. `MT-ND2`, `MT-ND4`, `MT-CO2`, `COX4I1`, `COX5B`, and `ATP5F1E` should initially be treated as phenotype sentinels, not upstream regulators. `MT-ND2` is especially useful because it is significant in 102 cell-type/stratum contexts and appears in all six low-similarity tails.

The evidentiary standard should follow prior AD studies that moved from sex-aware or multi-omic network nomination to genotype-aware perturbation, as done for `LRP10` and `ATP6V1A` ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5); [Wang et al., 2021](https://doi.org/10.1016/j.neuron.2020.11.002)). Those studies establish a workflow, not validation of the present candidates.

<div style="page-break-after: always;"></div>

## Page 5 of 5 — Model, limitations, and decisive next steps

### Working model

AD produces coordinated respiratory-chain remodeling whose direction is conditional rather than uniform. APOE ε2 is associated with OXPHOS induction in females and suppression in males. APOE ε4 is associated with broad suppression in females and a weaker, mixed, sometimes upward response in males. The most coherent changes occur in superficial RORB-positive and RELN-positive excitatory neurons, with additional effects in astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`. Changes in translation, import, chaperones, mitophagy, and redox defense indicate that the OXPHOS signature is embedded in mitochondrial maintenance stress. Male-ε2 `PPARGC1B` induction may be compensation for downstream respiratory failure.

### Limitations that control interpretation

1. The analysis lacks formal AD-by-sex, AD-by-APOE, and three-way interaction tests.
2. Nuclei, rather than donors, are the current model observations; donors are the biological replicates.
3. The male-ε2 group is small, and three male-ε2 cell-type contrasts were not estimable.
4. The `−1/0/+1` score discards continuous effect size, and most differences are one-stratum threshold crossings rather than exact reversals.
5. No individual mitochondrial similarity score passes FDR; fixed 200-gene tails cover roughly 27%–29% of the eligible background.
6. Pathway databases repeatedly label the same respiratory genes, inflating the apparent number of distinct mechanisms.
7. RNA does not measure mitochondrial mass, mtDNA copy number, protein abundance, complex activity, oxygen consumption, ATP production, coupling, or proton leak.
8. Cell loss, survivor bias, postmortem effects, and mtRNA quality can mimic or modify an expression response.
9. The regulator list lacks local causal-network, genetics, QTL, proteomic, and perturbation integration.
10. This ROSMAP reanalysis is not independent replication; prior studies use heterogeneous and sometimes overlapping cohorts and endpoints.

### Decisive next steps

First, construct donor-by-cell-type pseudobulk profiles for the leading excitatory clusters, `Ast GRM3`, OPCs, and `Mic P2RY12`. Fit targeted AD-by-sex contrasts within genotype and AD-by-APOE contrasts within sex; fit the three-way interaction if power permits. Test OXPHOS and complexes I/III/IV/V with direction-aware ranked gene-set methods. Model nuclear- and mtDNA-encoded components separately and directly test mitonuclear balance.

Second, perform cell-type-specific Bayesian-network or directed-network key-driver analysis. Require a final driver to show enrichment of its one- or two-step network neighborhood for the relevant stratum-specific signature, compatible edge direction, and support across a related cluster or independent network. Add AD GWAS fine mapping, brain eQTL/sQTL and TWAS colocalization, chromatin, proteomic, phosphoproteomic, essentiality, and tractability evidence.

Third, perturb `TUFM` and `ATP5IF1` as co-leads, followed by `TOMM7`, `PPARGC1B`, `PPARGC1A`, and conditionally `SMARCD3`, with `SIRT3` as an external comparator. Use APOE-isogenic ε2/ε3/ε4 models across multiple XX and XY donor backgrounds, cortical neurons and astrocytes, and neuron–astrocyte co-culture. Use gain- and loss-of-function and dose-response designs. Measure oxygen consumption, extracellular acidification, ATP, complex I/III/IV/V abundance and activity, membrane potential, ROS, mitochondrial mass and morphology, mitophagy flux, ATP-linked respiration, proton leak, coupling efficiency, APOE secretion, and the structural sentinel genes.

### Bottom line

The defensible conclusion is specific: **AD-associated mitochondrial transcription depends jointly on sex, APOE genotype, and cell type, with OXPHOS increasing in female ε2, decreasing in male ε2 and female ε4, and remaining mixed in male ε4.** The effect is concentrated in vulnerable excitatory populations and extends to mitochondrial maintenance pathways. It is not yet a proven statistical interaction, functional change, or causal network. `ATP5IF1` has the strongest local stratified evidence, `TUFM` the strongest AD-like perturbation support, `TOMM7` the clearest mitophagy mechanism, and `PPARGC1B` the most distinctive male-ε2 compensation hypothesis.

## Source map

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
