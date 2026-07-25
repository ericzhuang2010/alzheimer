# Sex- and APOE-dependent mitochondrial transcriptional responses in Alzheimer’s disease

## Scope and interpretation status

This report synthesizes the validated Minerva Phase 08–11 outputs and the mitochondrial analogues of Figures 1 and 3–6. It follows the comparison logic and discussion style of [Yu et al. (2026)](https://doi.org/10.1002/alz.71463), but restricts the primary analysis to mitochondrial genes and MitoCarta pathways.

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

### “High similarity” mostly means a shared lack of threshold-level response

The most positive mitochondrial similarity scores are close to zero, and none is significant. High-tail enrichment includes the TCA cycle in the pooled sex comparison and protein import/homeostasis in ε2 versus ε3/ε3, but the supporting state pairs are 97%–99% `(0,0)`. These pathways should be described as **relatively stable or commonly below the DEG threshold**, not as concordantly activated or repressed.

This distinction is important for Figures 3–5. The plotted high-tail points in Figures 4 and 5 are pathway matches, but none passes the primary C2:CP tail FDR. The figure captions state this correctly.

## Relationship to the Yu study

The mitochondrial results reproduce and extend the most relevant findings in Yu:

1. **Male ε2 has the largest transcriptional response.** The mitochondrial subset shows the same ranking, with particularly strong OXPHOS loss in superficial excitatory neurons, astrocytes, OPCs, oligodendrocytes, and `Mic P2RY12`.
2. **Female ε4 and male ε2 are the genotype outliers within their respective sexes.** Mitochondrial pathways contribute a coherent direction to both: female ε4 and male ε2 generally lose nuclear OXPHOS, protein-maintenance, and stress-defense transcripts.
3. **Yu’s ε4-versus-ε3/ε3 OXPHOS finding is reproduced.** The focused analysis shows that this comparison is mainly a female excitatory-neuron result.
4. **Yu’s Figure 6 electron-transport signal is strengthened.** OXPHOS is enriched in the sex-divergent tail within ε2, ε3/ε3, and ε4, but the direction and driving cell types differ by genotype.
5. **`MT-ND2` remains a leading phenotype gene.** It is significant in 102 AD-versus-NCI cell-type/stratum contexts and lies in all six low-similarity tails. It is therefore an excellent mitochondrial response marker, but it is an mtDNA-encoded Complex I subunit rather than an obvious upstream regulator.

There is also an important difference. Yu’s transcriptome-wide analysis reports many significant similarity and divergence genes, whereas the mitochondrial-restricted Phase 10 analysis has no gene-level FDR hits. The defensible conclusion is therefore that **mitochondrial pathways show coordinated stratified divergence even though no individual mitochondrial similarity score is significant after mitochondrial-family correction**.

The observed link between respiratory-chain state and APOE context is biologically plausible but not established by these data. Experimental work has shown that disruption of respiratory complexes I, III, or IV can increase APOE expression and secretion, including in human iPSC-derived astrocytes ([Wynne et al., 2023](https://elifesciences.org/articles/85779)). That result supports a possible feedback between respiratory-chain stress and APOE biology; it does not prove that the transcript patterns here have the same mechanism.

## Provisional key-regulator prioritization

### Why this is a pre-network nomination

The current repository can identify genes with strong local evidence and plausible control functions, but it cannot yet establish network key drivers. A causal key-driver claim requires evidence that a candidate’s directed network neighborhood is significantly enriched for the relevant mitochondrial DEG signature.

The existing [pre-network prioritization](pre_network_prioritization_report.md) is valuable but should not be used as a final causal ranking for two reasons:

- it scores only the MitoCarta core universe and therefore omits non-MitoCarta nuclear regulators in the extended mitochondrial-biogenesis and UPRmt sets, including `PPARGC1A`, `PPARGC1B`, `ESRRA`, `NRF1`, `SMARCD3`, `NR1D1`, `HSF1`, and `GABPB1`; and
- its “lineage” count is based on nine RDS partitions, treating three excitatory files as three lineages. Collapsing these yields seven biological compartments and reduces the apparent breadth of several assembly-factor candidates.

Similarity-tail membership and membership in an enriched pathway are useful evidence of context, but neither establishes that the candidate regulates the pathway. They should have less weight than directed network support, formal interaction evidence, genetic support, and perturbation data.

### Recommended perturbation panel

The following is a prioritized **experimental panel**, not a list of proven key drivers. It deliberately combines mitochondrial-localized control points with nuclear upstream regulators that the core-only score misses.

| Priority | Candidate | Control axis | Local evidence | Main experimental hypothesis |
|---:|---|---|---|---|
| 1 | `ATP5IF1` | ATP-synthase control | 34 DEG contexts across 20 cell types and 5/6 strata; 8 up / 26 down; eight exact paired reversals | A bioenergetic control point that switches with sex and APOE rather than simply tracking mitochondrial mass |
| 2 | `PPARGC1B` | nuclear mitochondrial biogenesis | 11 DEG contexts, all up and all in male ε2 | A male-ε2-specific compensatory biogenesis response to respiratory-chain loss |
| 3 | `TUFM` | mitochondrial translation elongation | 19 contexts across 16 cell types and all six strata; 3 up / 16 down | Loss of mitochondrial translation control contributes to the female-ε4/male-ε2 respiratory phenotype |
| 4 | `TOMM7` | protein import and mitophagy | 25 contexts across 19 cell types and all six strata; 7 up / 18 down | Sex-dependent import/quality-control failure couples damaged organelles to the OXPHOS response |
| 5 | `PPARGC1A` | nuclear mitochondrial biogenesis | 11 contexts across 9 cell types; 9 up / 2 down | A broader upstream compensation program that may modify, rather than initiate, OXPHOS loss |
| 6 | `SMARCD3` | chromatin/mitochondrial-biogenesis program | 19 contexts across 14 cell types and all six strata; 16 up / 3 down | A broadly responsive chromatin regulator whose network position may distinguish driver from generic response |

`ATP5IF1` has the best integrated local evidence. It is increased in four female-ε2 contexts but decreased in ten female-ε4 contexts and predominantly decreased in male ε2, ε3/ε3, and ε4. It reverses from female ε2 to female ε4 in `Exc L4-5 RORB IL1RAPL2` (`+0.420` to `−0.519`) and `Exc L5/6 IT Car3` (`+0.429` to `−0.814`), from female to male ε2 in `Exc L4-5 RORB IL1RAPL2` (`+0.420` to `−0.497`), and from female to male ε4 in `Exc RELN CHD7` (`−1.029` to `+0.801`). This makes it the best analogue of Yu’s detailed `CLU` vignette.

`PPARGC1B` is the sharpest interaction-specific hypothesis. Its expression is significantly higher in AD in 11 male-ε2 cell types and in no other stratum. Because OXPHOS is mainly lower in male ε2, `PPARGC1B` induction may be an attempted compensatory response rather than the cause of respiratory-chain loss. That apparent upstream/downstream mismatch is experimentally informative: suppressing or augmenting `PPARGC1B` can test whether the response is protective, ineffective, or maladaptive.

`TUFM` and `TOMM7` show clean sex reversals within ε2. `TUFM` changes from `+0.506` in female ε2 to `−0.939` in male ε2 in `Ast GRM3`. `TOMM7` changes from female up to male down in `Exc L3-4 RORB CUX2` (`+0.460` versus `−0.837`) and `Exc L4-5 RORB IL1RAPL2` (`+0.619` versus `−0.582`). These provide distinct mitochondrial translation and organelle-surveillance perturbation axes.

`PPARGC1A` and `SMARCD3` are included because a true pathway regulator need not be localized to mitochondria. They were excluded from the primary similarity universe by design, so they have no core-mito Phase 10 rank or pathway-tail support. Their priority depends more heavily on network key-driver and genetic validation.

### Secondary candidates and phenotype sentinels

Secondary perturbation candidates are:

- `HSPD1`, the broadest core-mito proteostasis candidate (37 contexts, 5 up / 32 down), especially for the female-ε4 chaperone-loss phenotype;
- `UQCC2`, a Complex III assembly factor with 8 of its 12 significant contexts increased in male ε2, potentially another compensatory response;
- `HSF1`, `ESRRA`, `NR1D1`, and `GABPB1`, upstream extended-set candidates with weaker or more cell-restricted local evidence;
- `FIS1`, `SLIRP`, and `APOO`, strong dynamics, mtRNA, or cristae-effector candidates that may be downstream responders; and
- `FKBP8`, a biologically plausible mitophagy candidate whose direction is highly context dependent.

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

Begin with `ATP5IF1`, `PPARGC1B`, `TUFM`, `TOMM7`, `PPARGC1A`, and `SMARCD3` in male and female isogenic APOE2/3/4 cortical-neuron and astrocyte systems. Use both loss- and gain-of-function where feasible, because the human data suggest that direction depends on stratum.

Primary readouts should include:

- oxygen-consumption and extracellular-acidification rates;
- ATP abundance and ATP synthase activity;
- complexes I, III, IV, and V abundance and activity;
- mitochondrial membrane potential and ROS;
- mitochondrial mass, morphology, and mitophagy flux;
- APOE expression and secretion; and
- the structural sentinels `MT-ND2`, `MT-ND4`, `MT-CO2`, `COX4I1`, `COX5B`, and `ATP5F1E`.

A particularly informative design would restore `ATP5IF1`, `TUFM`, or `TOMM7` in the male-ε2 and female-ε4 contexts, where they tend to fall, while performing the reciprocal perturbation in female ε2. For `PPARGC1B`, the first question should be whether its male-ε2 induction is protective compensation: knockdown should worsen respiratory phenotypes if it is protective and improve them if it is maladaptive.

## Conclusion

The most defensible conclusion is that AD-associated mitochondrial transcription is **jointly conditioned by sex, APOE genotype, and cell type**. OXPHOS is the dominant divergent pathway, but its direction changes across strata: female ε2 is predominantly upward, male ε2 and female ε4 are predominantly downward, and male ε4 is mixed with selected excitatory increases. The effect is strongest in superficial and RELN-positive excitatory neurons and is accompanied by changes in mitochondrial translation, protein import, chaperones, mitophagy, and redox defense.

`ATP5IF1` is the strongest mitochondrial-localized perturbation candidate from the current data. `PPARGC1B`, `PPARGC1A`, and `SMARCD3` broaden the search to upstream nuclear mitochondrial-biogenesis control, while `TUFM` and `TOMM7` provide translation and organelle-quality-control axes. These genes should be called **pre-network priorities**, not key drivers, until donor-aware interaction tests, cell-type Bayesian-network KDA, genetic integration, and perturbation experiments establish causality.

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
