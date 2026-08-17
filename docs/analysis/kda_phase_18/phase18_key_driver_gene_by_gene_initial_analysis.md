# Phase 18 key-driver genes: initial gene-by-gene analysis

**Date:** 2026-08-15  
**Status:** Initial interpretation and validation plan

## 1. Scope and interpretation rules

Phase 18 selected up to five genes per broad cell-type network in each of two classes:

- **MT drivers:** genes in the fixed core mitochondrial inventory.
- **Non-MT drivers:** genes outside that inventory. “Non-MT” does not mean that a gene has no mitochondrial function.

The current result contains **25 unique displayed genes**: 15 non-MT genes and 10 MT genes. Because a gene can be selected in more than one broad network, these genes form **47 displayed gene × broad-network contexts**. The source table contains 95,557 explicitly tested gene × run rows from 161 included `call_key_drivers()` calls. Phase 18 first aggregates evidence within each gene × broad-network unit, applies coverage, conservative-support, and ACAT-q gates, and then retains at most five passing genes per network and driver class.

This report uses the current Phase 18 selection and figures:

- [Non-MT circular figure](../../../results/figures/analysis/phase_18_key_driver_selection/two_case_circular/phase18_non_mt_driver_circular.png)
- [MT circular figure](../../../results/figures/analysis/phase_18_key_driver_selection/two_case_circular/phase18_mt_driver_circular.png)
- [Non-MT evidence atlas](../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt.png)
- [MT evidence atlas](../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_mt/phase18_evidence_atlas_mt.png)
- [Non-MT sex/APOE figure](../../../results/figures/analysis/phase_18_key_driver_selection/sex_apoe_non_mt/phase18_sex_apoe_non_mt.png)
- [MT sex/APOE figure](../../../results/figures/analysis/phase_18_key_driver_selection/sex_apoe_mt/phase18_sex_apoe_mt.png)
- [Selection-process figure](../../../results/figures/analysis/phase_18_key_driver_selection/key_driver_selection_process/phase18_key_driver_selection_process.png)

The Phase 12 key-driver selection and its figures are deprecated and are not used here. Earlier DEG and pathway results remain useful as within-cohort biological context, but they are not independent validation.

### How to read the evidence

The evidence layers answer different questions:

1. **Phase 18 KDA:** Is the gene's Bayesian-network neighborhood repeatedly enriched for the relevant mitochondrial DEG query?
2. **Phase 18 recurrence:** In how many runs, fine cell types, sex/APOE groups, directions, and broad networks is this relationship observed?
3. **Earlier DEG evidence:** Is the candidate gene itself differentially expressed? KDA does not require this, and KDA direction does not imply that the driver itself changes in the same direction as the query.
4. **Prior literature:** Is there independent human, genetic, protein, model-system, or perturbational evidence?
5. **Experimental validation:** Does changing the candidate alter the predicted mitochondrial targets and cellular phenotype?

“Tested runs” below means included KDA calls in which the gene had an explicit test row; it is not the number of eligible runs. “Significant runs” means `significant_by_call_key_drivers = TRUE`. “Conservative support” further requires at least two other query genes in the neighborhood, fold enrichment greater than one, and within-run q ≤ 0.05. Runs within one broad cell type reuse the same Bayesian network, so they are repeated biological contexts rather than independent network replications.

Bayesian-network key-driver status is a topology-and-enrichment result. It nominates a candidate regulator or module anchor; it does not prove causal molecular regulation. This distinction is especially important for ribosomal proteins and structural electron-transport-chain subunits.

## 2. Result overview

### 2.1 Non-MT drivers

| Gene | Displayed / passing networks | Significant / tested runs | Conservative support | Supporting fine cell types | Best Phase 18 context | Earlier direct-DEG contexts* |
|---|---:|---:|---:|---:|---|---:|
| RPL11 | 4 / 4 | 29 / 84 | 25 | 15 | Excitatory, q = 1.84 × 10^-9 | 30 |
| RPS15 | 2 / 3 | 26 / 90 | 25 | 18 | OPC, q = 3.97 × 10^-12 | 47 |
| LAMTOR5 | 2 / 2 | 20 / 73 | 17 | 13 | Excitatory, q = 2.59 × 10^-3 | 25 |
| RPLP1 | 2 / 2 | 15 / 79 | 14 | 9 | Astrocyte, q = 2.38 × 10^-3 | 49 |
| SELENOW | 1 / 1 | 16 / 83 | 15 | 10 | Excitatory, q = 5.75 × 10^-6 | 32 |
| RPS13 | 1 / 1 | 12 / 72 | 10 | 8 | Excitatory, q = 5.39 × 10^-6 | 25 |
| ATP6V1F | 1 / 1 | 5 / 62 | 5 | 4 | Inhibitory, q = 2.63 × 10^-2 | 30 |
| APOE | 1 / 1 | 4 / 14 | 4 | 3 | Astrocyte, q = 1.27 × 10^-2 | 21 |
| RPL38 | 1 / 1 | 3 / 52 | 3 | 3 | Inhibitory, q = 4.10 × 10^-2 | 37 |
| RPL15 | 1 / 1 | 10 / 96 | 8 | 7 | Astrocyte, q = 3.71 × 10^-3 | 32 |
| DYNLT1 | 1 / 1 | 2 / 41 | 2 | 2 | Excitatory, q = 2.59 × 10^-3 | 13 |
| LAPTM4A | 1 / 1 | 2 / 9 | 2 | 2 | Astrocyte, q = 1.27 × 10^-2 | 22 |
| ANKRD11 | 1 / 1 | 2 / 45 | 2 | 1 | OPC, q = 7.12 × 10^-4 | 8 |
| FTL | 1 / 1 | 2 / 21 | 2 | 1 | OPC, q = 2.19 × 10^-4 | 43 |
| NCOA1 | 1 / 1 | 1 / 9 | 1 | 1 | OPC, q = 4.59 × 10^-2 | 5 |

\*Number among 321 estimable fine-cell-type × sex/APOE × AD-contrast rows meeting the stored Phase 8 `paper_deg` rule (within-contrast BH FDR < 0.05 and absolute fold change > 1.3). These results come from the same study and should not be treated as replication.

The dominant non-MT themes are ribosomal stress/translation, lysosome–mTOR signaling, iron handling, intracellular transport, and APOE biology. RPL11 has the broadest cross-network footprint. RPS15 has the broadest fine-cell-type support. SELENOW has the clearest direct AD perturbation literature. LAMTOR5 and ATP6V1F form a mechanistically coherent lysosome–mitochondria axis. The OPC genes are promising but supported by few KDA runs and therefore need particular caution.

### 2.2 MT drivers

| Gene | Displayed / passing networks | Significant / tested runs | Conservative support | Supporting fine cell types | Best Phase 18 context | Earlier direct-DEG contexts* |
|---|---:|---:|---:|---:|---|---:|
| MT-CO2 | 7 / 7 | 65 / 89 | 62 | 29 | Excitatory, q = 8.34 × 10^-21 | 67 |
| MT-ND4 | 4 / 5 | 53 / 93 | 32 | 20 | Oligodendrocyte, q = 1.14 × 10^-3 | 77 |
| MT-CO3 | 4 / 4 | 42 / 84 | 17 | 13 | Vascular, q = 2.37 × 10^-14 | 62 |
| MT-ATP6 | 2 / 3 | 37 / 64 | 25 | 16 | Astrocyte, q = 7.75 × 10^-5 | 56 |
| COX4I1 | 2 / 3 | 29 / 93 | 24 | 16 | Excitatory, q = 1.52 × 10^-8 | 46 |
| COX7C | 2 / 3 | 37 / 94 | 25 | 14 | Inhibitory, q = 6.24 × 10^-6 | 42 |
| MT-CYB | 2 / 2 | 46 / 80 | 37 | 21 | Inhibitory, q = 6.89 × 10^-8 | 64 |
| COX6B1 | 1 / 1 | 27 / 75 | 23 | 12 | Excitatory, q = 5.96 × 10^-7 | 37 |
| UQCR10 | 1 / 1 | 27 / 81 | 25 | 13 | Excitatory, q = 2.76 × 10^-10 | 31 |
| MT-ND5 | 1 / 1 | 33 / 83 | 8 | 7 | Inhibitory, q = 2.69 × 10^-6 | 52 |

For MT drivers, Phase 18 removed a driver's guaranteed overlap with itself when it belonged to the query. Thus, MT-CO2 was not selected merely because MT-CO2 appeared in the MT query: its post-exclusion neighborhood still contained other query genes. Nevertheless, these structural respiratory-chain genes are initially better interpreted as **sentinels or network anchors of coordinated respiratory remodeling** than as conventional upstream regulators or immediate drug targets.

## 3. Non-MT drivers, one gene at a time

### 3.1 RPL11 — broad ribosomal-stress candidate

**Phase 18 result.** RPL11 is the strongest broadly recurrent non-MT candidate: it is displayed in astrocyte, excitatory-neuron, microglial, and oligodendrocyte networks. The excitatory result is particularly strong, with conservative support in 20 of 97 runs and aggregate q = 1.84 × 10^-9. The astrocyte and excitatory contexts are stable to leave-one-fine-cell-type omission. The microglial and oligodendrocyte calls are supported by only one run each and are less secure.

**Biological interpretation.** RPL11 is a large-subunit ribosomal protein and a canonical sensor of nucleolar/ribosomal stress. Free RPL11 can inhibit MDM2 and activate p53 [3]. Neuronal work also links RPL11-dependent ribosomal stress to p53 activation and cell death [4]. Human AD capillary proteomics reported increased RPL11 and RPL15 protein in brain microvessels [1], while older AD work supports early ribosomal dysfunction more generally [2]. This makes RPL11 biologically plausible, but it leaves two competing models: RPL11 may transmit a stress response that affects mitochondrial programs, or it may simply mark a highly connected translation/stress module.

The earlier DEG results show RPL11 changes in 30 contexts, mostly AD-down. The Phase 18 sex/APOE panel is mixed—female ε2 support is often AD-up, whereas male ε2 and female ε4 support is commonly AD-down—matching the broader mitochondrial-direction pattern observed previously. That agreement is useful internally but does not establish an RPL11-specific genotype interaction.

**Validation priority.** Extract the directed RPL11 neighborhood through two to three layers in excitatory and astrocyte networks; test whether mitochondrial targets remain enriched after matching candidate genes for expression, degree, and ribosomal annotation. In APOE-isogenic human excitatory neurons and astrocytes, use partial CRISPRi/CRISPRa rather than complete loss, measure predicted downstream MT genes, p53 activation, nascent translation, oxygen consumption, and viability, and include p53 inhibition or rescue. Spatial or vascular proteomics should determine whether the prior human protein signal is endothelial/capillary rather than parenchymal.

### 3.2 RPS15 — recurrent inhibitory/OPC ribosomal candidate

**Phase 18 result.** RPS15 is displayed in inhibitory neurons and OPCs and also passes the candidate gates in excitatory neurons, where it ranks 20th and therefore falls outside the five-gene display cap. Its 25 conservative-support runs span 18 fine cell types, the largest fine-cell-type breadth among non-MT genes. Inhibitory-neuron stability is strong; the OPC context cannot be stress-tested well because only six eligible OPC runs are available.

**Biological interpretation.** RPS15 is a small-subunit ribosomal protein. Like RPL11, RPS15 can interact with the MDM2–p53 checkpoint [5]. RPS15 is also a substrate of LRRK2 in a neurodegeneration model, although that evidence comes from Parkinson-related biology and should not be transferred directly to AD [6]. A targeted search did not identify convincing RPS15-specific AD perturbation evidence. Its broad KDA recurrence and 47 direct-DEG contexts make it a strong network observation but also raise the possibility of generic translation-state or network-degree effects.

The sex/APOE summary is directionally heterogeneous: support is often female ε2 AD-up but male ε2 AD-down. This is consistent with context-dependent translation remodeling rather than a single uniform disease effect.

**Validation priority.** Compare RPS15 with other ribosomal candidates using degree- and expression-matched network permutations. In inhibitory neurons and OPCs, perturb RPS15 modestly and assay mitochondrial translation, cytosolic translation, p53, integrated-stress-response markers, respiratory reserve, and the exact KDA-predicted targets. A result that selectively changes the predicted mitochondrial neighborhood without global translational collapse would support a specific driver role.

### 3.3 LAMTOR5 — lysosomal nutrient sensing linked to mitochondrial output

**Phase 18 result.** LAMTOR5 is selected in excitatory and inhibitory neurons, with 17 conservative-support runs across 13 fine cell types. Both networks show complete candidate retention in the available leave-one-fine-cell-type analysis. This is a more focused signal than the ribosomal genes but is reproduced in two neuronal network types.

**Biological interpretation.** LAMTOR5 is part of the lysosomal Ragulator complex, which activates Rag GTPases and recruits mTORC1 to lysosomes [7]. mTORC1 controls mitochondrial biogenesis and function [8], and Aβ can disrupt lysosome-to-mitochondria mTORC1 signaling [9]. More recent cellular work connects LAMTOR5 itself to V-ATPase assembly and lysosomal acidification [10]. Thus, Phase 18 nominates a credible route from lysosomal sensing to mitochondrial gene coordination. A targeted search did not find a direct LAMTOR5 perturbation study in AD, so the gene-specific AD claim remains new.

The KDA support is split across directions and sex/APOE groups, with female ε2 AD-up and female ε4/male ε2 AD-down contexts prominent. The earlier direct DEG signal occurs in 25 contexts. This suggests that LAMTOR5 may mediate different adaptive or failing states rather than a universally increased or decreased pathway.

**Validation priority.** In APOE-isogenic excitatory and inhibitory neurons, perform LAMTOR5 CRISPRi/CRISPRa followed by amino-acid withdrawal/re-feeding. Measure lysosomal pH, Ragulator/mTORC1 localization, phospho-S6K/4EBP1, mitophagy, mitochondrial mass, membrane potential, oxygen consumption, and predicted downstream MT genes. Rescue with an sgRNA-resistant LAMTOR5 construct and test whether manipulating mTORC1 or lysosomal acidification phenocopies or blocks the effect.

### 3.4 RPLP1 — astrocyte/inhibitory translation-state candidate

**Phase 18 result.** RPLP1 is selected in astrocytes and inhibitory neurons. Fourteen conservative-support runs span nine fine cell types. It retains candidate status in all 12 assessable inhibitory-neuron omissions and in two of three astrocyte omissions. The earlier DEG analysis identifies RPLP1 in 49 contexts, mostly AD-down.

**Biological interpretation.** RPLP1 is part of the ribosomal P-stalk, which recruits and activates translation factors. Unlike RPL11, it is not a canonical p53 checkpoint protein. A targeted primary-literature search did not identify convincing RPLP1-specific AD evidence. Its joint appearance with RPL11, RPL15, RPS13, RPS15, and RPL38 argues for a broader ribosomal/translation-state module. The main open question is whether distinct ribosomal proteins carry selective mitochondrial target relationships or merely inherit the same dense ribosomal network structure.

**Validation priority.** First test specificity computationally: remove all ribosomal-protein genes in turn, compare neighborhood overlap, and use degree-preserving permutations. Experimentally, titrate partial RPLP1 knockdown in astrocytes and inhibitory neurons and combine ribosome profiling or nascent-protein labeling with mitochondrial transcript/protein assays. Strong support would require selective effects on the Phase 18-predicted mitochondrial targets at perturbations that do not broadly suppress protein synthesis.

### 3.5 SELENOW — excitatory-neuron antioxidant and tau-clearance candidate

**Phase 18 result.** SELENOW is selected only in the excitatory network, but the signal is strong: 15 conservative-support runs across 10 fine cell types, aggregate q = 5.75 × 10^-6, and complete candidate retention under all assessable omissions. It is supported in four primary sex/APOE groups and both AD directions.

**Biological interpretation.** SELENOW is a small redox-active selenoprotein. Crucially, recent direct AD-model evidence shows that SELENOW binds tau, promotes its ubiquitin–proteasome clearance, and that SELENOW overexpression improves tau pathology and memory in 3xTg-AD mice [13]. Independent work supports antioxidant and respiration-related functions of SELENOW [14,15]. Phase 18 therefore does not merely nominate an abstract redox gene; it connects a experimentally supported tau-protective factor to an excitatory mitochondrial network.

The earlier DEG analysis finds SELENOW changes in 32 contexts, mostly AD-down. That is consistent with loss of a protective response in several strata, although the KDA support itself includes both directions and cannot be read as SELENOW expression direction.

**Validation priority.** Replicate SELENOW protein and transcript changes in human excitatory subtypes, then perturb SELENOW in APOE-isogenic neurons with Aβ or tau stress. Measure tau clearance, proteasome activity, ROS, glutathione/redox state, oxygen consumption, and the exact mitochondrial neighborhood. A rescue with wild-type versus redox-active-site mutant SELENOW would distinguish redox-dependent from scaffolding/proteostasis mechanisms. This is a high-priority candidate because the external AD biology and Phase 18 network evidence are mutually reinforcing.

### 3.6 RPS13 — excitatory ribosomal candidate with little gene-specific AD evidence

**Phase 18 result.** RPS13 is the rank-2 non-MT excitatory candidate, supported by 10 conservative runs across eight fine cell types, aggregate q = 5.39 × 10^-6, and complete leave-one-fine-cell-type retention. The earlier DEG signal occurs in 25 contexts, mainly AD-down.

**Biological interpretation.** RPS13 is a small-subunit ribosomal protein. The Phase 18 evidence is statistically strong and stable, but a targeted search did not identify convincing RPS13-specific AD mechanistic evidence. Its co-selection with RPL11 and the other ribosomal genes makes a translation/ribosomal-stress explanation more likely than six independent ribosomal mechanisms.

**Validation priority.** Treat RPS13 as a test of module specificity. Compare its directed targets with RPL11 and RPS15, quantify target-set overlap, and ask whether its KDA rank survives removal of shared ribosomal neighbors. Partial perturbation in excitatory neurons should be paired with global translation controls, respiratory phenotyping, and rescue. If RPS13 and RPL11 drive distinct mitochondrial target subsets, the specialized-ribosome model becomes more credible; if they produce indistinguishable global stress, the module-anchor interpretation is favored.

### 3.7 ATP6V1F — inhibitory-neuron lysosomal-acidification candidate

**Phase 18 result.** ATP6V1F is selected in inhibitory neurons. All five conservative-support runs are in AD-down mitochondrial-query contexts and span four fine cell types. The candidate is retained in 11 of 12 assessable leave-one-fine-cell-type analyses, so it is reasonably stable despite modest support.

**Biological interpretation.** ATP6V1F encodes the F subunit of the catalytic V1 sector of the vacuolar H+-ATPase. V-ATPase-dependent lysosomal acidification is required for autophagic clearance; lysosomal de-acidification has been observed before extracellular amyloid deposition in AD mouse models [11]. ATP6V1F therefore fits the same lysosome–mitochondria theme as LAMTOR5, but a targeted search did not identify strong ATP6V1F-specific AD perturbation evidence. The one-direction KDA pattern suggests a focused hypothesis: impaired ATP6V1F-linked acidification may accompany mitochondrial down-regulation in inhibitory neurons.

**Validation priority.** Confirm ATP6V1F abundance and V-ATPase assembly in inhibitory subtypes. Use graded CRISPRi and rescue to measure lysosomal pH, autophagic flux, mitophagy, respiratory function, and predicted mitochondrial targets. Bafilomycin is useful as a positive control but is not gene-specific; the decisive experiment is whether ATP6V1F rescue restores both lysosomal and mitochondrial phenotypes without globally changing cell survival.

### 3.8 APOE — established AD gene connected to an astrocyte mitochondrial module

**Phase 18 result.** APOE is selected only in the astrocyte network, with four significant and conservative-support runs among 14 tested. Support spans three fine cell types, three primary sex/APOE groups, and both mitochondrial directions. Its leave-one-fine-cell-type retention is two thirds, so the result is credible but less stable than the top neuronal candidates.

**Biological interpretation.** APOE is not a novel AD gene; the new result is its placement as a key driver of astrocyte mitochondrial DEG neighborhoods. Human iPSC and cellular studies show that APOE4 can disrupt astrocyte lysosomal cholesterol handling, mitophagy, mitochondrial dynamics, and fatty-acid metabolism [16–19]. Phase 18 is therefore aligned with a well-supported APOE–astrocyte–mitochondria mechanism.

The supporting runs are not simply an ε4-only effect: female ε2 support is AD-up, while male ε2 and male ε4 support is AD-down. This could reflect sex/genotype dependence, disease-stage adaptation, or sampling variability. It must not be described as an interaction until a donor-level disease × sex × APOE model is fit.

**Validation priority.** Use APOE2/3/4 isogenic human astrocytes from both sexes or sex-chromosome backgrounds, with disease-relevant stress, and test mitochondrial respiration, substrate use, cholesterol distribution, mitophagy, lipid-droplet transfer, and the Phase 18 target neighborhood. Fit donor-level pseudobulk interaction models in the human data. Cross-species APOE-knock-in single-cell data, when available, should test whether the same astrocyte subtypes and target genes recur.

### 3.9 RPL38 — thin inhibitory specialized-translation signal

**Phase 18 result.** RPL38 is the fifth-ranked inhibitory non-MT candidate. Only three of 52 tested runs are significant and conservatively supportive, all from one primary group and one direction. Aggregate q = 0.041 is close to the threshold, although candidate retention is high in the available omission analysis.

**Biological interpretation.** RPL38 has precedent as a component of heterogeneous or specialized ribosomes that can selectively affect translation of particular transcript classes [20]. No convincing RPL38-specific AD evidence was identified. The 37 earlier DEG contexts show that its abundance is disease-responsive, but its Phase 18 support is narrow. This is an interesting specialized-translation hypothesis, not yet a leading driver claim.

**Validation priority.** Validate only after degree/expression-matched null analysis. In inhibitory neurons, compare RPL38 perturbation with RPL11 or RPS15 and measure both global translation and translation of predicted mitochondrial targets. Evidence for selective target translation at mild perturbation would elevate RPL38; a generic integrated stress response would demote it.

### 3.10 RPL15 — astrocyte ribosomal candidate with human vascular protein support

**Phase 18 result.** RPL15 is selected in astrocytes, with eight conservative-support runs across seven fine cell types and complete leave-one-fine-cell-type retention. It is widely tested (96 runs) but significant in only 10, suggesting a context-restricted rather than global relationship.

**Biological interpretation.** RPL15 is a large-subunit ribosomal protein. Human AD capillary proteomics reported increased RPL15, together with RPL11, in brain microvessels [1]. The current Phase 18 result is astrocytic, so the literature does not validate the cell type and may instead flag vascular contamination or a shared neurovascular translation response. The earlier DEG signal is mostly AD-down, which also differs from the reported capillary protein increase.

**Validation priority.** Use spatial transcriptomics, nuclei-quality checks, and vascular-marker adjustment to determine whether the astrocyte signal is intrinsic. Protein-level validation should separate astrocyte endfeet from endothelial/pericyte compartments. As for the other ribosomal genes, mild perturbation and target-selectivity controls are essential.

### 3.11 DYNLT1 — excitatory axonal-transport candidate with sparse support

**Phase 18 result.** DYNLT1 is the fifth-ranked excitatory non-MT candidate, but only two of 41 tested runs provide significant conservative support. These two runs come from two fine cell types, two groups, and opposite directions. Its candidate status is retained in 13 of 14 assessable omissions, indicating that the aggregated result is not driven by one obvious omission even though the direct support is sparse.

**Biological interpretation.** DYNLT1 is a dynein light chain involved in retrograde intracellular transport. Axonal transport and dynein/dynactin function are disrupted in AD models, including by familial APP perturbation [12], but a targeted search did not identify a strong DYNLT1-specific AD perturbation result. The gene could connect transport of mitochondria, autophagosomes, or signaling cargo to an excitatory mitochondrial program.

**Validation priority.** Inspect edge direction and the identity of DYNLT1's first- and second-layer targets before assigning mechanism. In long-process human neurons, perturb DYNLT1 modestly and quantify mitochondrial motility, retrograde autophagosome transport, axonal ATP, respiration, and the predicted target genes. Include general dynein-complex controls to determine whether the effect is DYNLT1-specific.

### 3.12 LAPTM4A — sparse astrocyte lysosomal candidate

**Phase 18 result.** LAPTM4A is selected in astrocytes. It was explicitly tested in only nine runs and supported in two, both from the same primary group and direction. It retains candidate status in all assessable omissions, but the evidence base is small.

**Biological interpretation.** LAPTM4A is a lysosomal membrane protein. Work outside the nervous system supports lysosomal localization, ubiquitin-ligase interactions, and a role in lysosome/autophagy homeostasis [21,22]. A targeted search did not identify a direct AD or astrocyte-mitochondrial LAPTM4A study. It should not be conflated with the paralog LAPTM4B, for which more cancer and autophagy literature exists. The alignment with APOE and LAMTOR5 makes the astrocyte lysosome–mitochondria hypothesis attractive, but Phase 18 support is too sparse for a strong claim.

**Validation priority.** Confirm expression and protein localization in human astrocytes. CRISPRi/CRISPRa should measure lysosomal pH, autophagic flux, cholesterol trafficking, mitophagy, and the predicted mitochondrial targets. Test genetic interaction with APOE genotype. Replication in another astrocyte network or cohort is especially important.

### 3.13 ANKRD11 — exploratory OPC chromatin regulator

**Phase 18 result.** ANKRD11 is selected in the OPC network with aggregate q = 7.12 × 10^-4, but only two of 45 tested runs are significant and conservatively supportive, representing one fine cell type. OPC has only six eligible KDA runs, so leave-one-fine-cell-type stability cannot be assessed meaningfully.

**Biological interpretation.** ANKRD11 is a chromatin/transcriptional co-regulator required for neuronal development and dendritic differentiation; experimental work connects it to histone acetylation and BDNF/TrkB signaling [23]. The current finding instead points to OPC mitochondrial networks. A targeted search did not reveal direct ANKRD11 evidence in AD OPCs, iron metabolism, or mitochondrial control. Its eight earlier direct-DEG contexts are all AD-up, which supplies a consistent expression observation but remains within-cohort.

**Validation priority.** Treat ANKRD11 as a new-finding candidate. Replicate the OPC KDA in another network or cohort, examine chromatin accessibility and ANKRD11 motif/cofactor enrichment near predicted targets, and use OPC CRISPRi with differentiation, respiration, myelination, and target-expression readouts. CUT&RUN/CUT&Tag would test whether predicted targets are directly occupied. Because support comes from one fine cell type, subtype specificity should be reproduced before broad interpretation.

### 3.14 FTL — exploratory OPC iron/ferroptosis candidate

**Phase 18 result.** FTL is the rank-2 OPC non-MT candidate, with a strong aggregate q (2.19 × 10^-4) but only two significant, conservative-support runs and one supporting fine cell type. The earlier DEG analysis finds FTL in 43 contexts, mainly AD-down.

**Biological interpretation.** FTL encodes ferritin light chain and is central to intracellular iron storage. Brain iron and ferritin abnormalities have long been reported in AD [24], oligodendrocytes acquire iron through ferritin-related mechanisms [25], and iron overload can promote oligodendrocyte ferroptotic injury [26]. Human AD tissue also shows iron associated with lipid peroxidation [27]. These data make an OPC iron–mitochondria connection plausible, but they do not establish FTL as an upstream driver in OPCs. FTL may instead be a sensitive marker of iron load, oxidative stress, or lineage state.

**Validation priority.** Confirm the OPC subtype and exclude microglial/ambient-RNA contributions. Measure labile iron, ferritin protein, lipid peroxidation, glutathione, mitochondrial respiration, and ferroptosis sensitivity after FTL perturbation. Use iron chelation, ferrostatin-1, and FTL rescue to separate iron-dependent from generic stress effects. Spatial proteomics or histology should test whether the signal localizes to OPCs near plaques or damaged white matter.

### 3.15 NCOA1 — threshold-level OPC nuclear-receptor candidate

**Phase 18 result.** NCOA1 is the weakest displayed OPC candidate: one significant and conservative-support run among nine tested, one fine cell type, one group, one direction, and aggregate q = 0.0459. No useful omission stability estimate is available.

**Biological interpretation.** NCOA1/SRC-1 is a transcriptional coactivator for nuclear receptors, including estrogen receptors, and has been linked experimentally to hippocampal estrogen signaling and memory [28]. However, Ncoa1 deletion did not materially change amyloid deposition or glial activation in an APP/PS1 mouse study [29]. Human association reports near NCOA1 are preliminary and require replication [30,31]. Phase 18 may point to an OPC-specific hormonal/metabolic role missed by amyloid-centered models, but the present statistical support is minimal.

**Validation priority.** Keep NCOA1 exploratory. First replicate the exact OPC context and fit formal sex/APOE interaction models. If it survives, perturb NCOA1 under estrogen-receptor agonism/antagonism and assay OPC differentiation, lipid synthesis, respiration, and predicted targets. Results should be compared with the prior APP/PS1 null finding rather than presented as established AD biology.

## 4. MT drivers, one gene at a time

### 4.1 MT-CO2 — ubiquitous complex-IV network sentinel

**Phase 18 result.** MT-CO2 is the only gene selected in all seven broad networks. It is significant in 65 of 89 tested runs, has 62 conservative-support runs across 29 fine cell types, and is retained as a candidate in every assessable omission. It is rank 1 in most networks. The self-overlap correction means these results depend on enrichment for other mitochondrial query genes around MT-CO2, not MT-CO2 alone.

**Biological interpretation.** MT-CO2 encodes mitochondrially encoded cytochrome-c oxidase subunit II of complex IV. Reduced cytochrome-c oxidase activity is a recurring AD observation [32,33], and older postmortem studies reported altered complex-IV transcripts, including MT-CO2-related measures [34,35]. The earlier DEG results show MT-CO2 in 67 contexts, predominantly AD-up, with especially broad female ε2 and female ε3 up-direction support and male ε2 down-direction support. This is compatible with context-dependent compensation versus failure.

MT-CO2's ubiquity makes it an excellent marker of coordinated respiratory remodeling but a less convincing conventional upstream regulator. Its apparent centrality could reflect mtRNA abundance, mitochondrial mass, mtDNA copy number, cell survival, or network topology.

**Validation priority.** Measure MT-CO2 RNA, protein, complex-IV assembly/activity, mitochondrial mass, mtDNA copy number, and heteroplasmy in the same samples. Re-run network tests with mitochondrial abundance covariates and degree-matched nulls. Perturbing a core mtDNA-encoded subunit is likely to create nonspecific respiratory failure; if experimental perturbation is used, it should be graded and interpreted as a module-function test, with rescue and complex-IV-specific controls.

### 4.2 MT-ND4 — broad complex-I sentinel with direct AD mechanistic leads

**Phase 18 result.** MT-ND4 is displayed in microglia, OPCs, oligodendrocytes, and vascular cells and also passes in excitatory neurons outside the top-five display. It has 32 conservative-support runs across 20 fine cell types. The earlier DEG analysis identifies MT-ND4 in 77 contexts, the largest direct-DEG breadth among the selected genes.

**Biological interpretation.** MT-ND4 encodes a core complex-I membrane subunit. Reduced MT-ND4 expression was reported in AD temporal cortex [36]. A mechanistic study linked SIRT3 loss and p53 activation to repression of mitochondrial genes including MT-ND4; SIRT3 restoration improved ND4 expression and respiration in AD-related models [37]. Recent work further implicates abnormal cytosolic accumulation and m6A-dependent handling of MT-ND4 RNA in Aβ-induced neuronal innate immune activation [38]. These studies make MT-ND4 more than a generic respiratory marker, although none proves that it is the upstream driver inferred by KDA.

**Validation priority.** Separate three possible mechanisms: complex-I deficiency, altered mtDNA/transcription, and mislocalized immunostimulatory mtRNA. Measure complex-I assembly/activity, mtDNA copy number and heteroplasmy, MT-ND4 RNA localization/modification, cytosolic mitochondrial RNA, and innate-immune signaling. Test SIRT3/p53 and YTHDF2-related rescue paths in the relevant cell types. Microglial and glial contexts deserve particular attention because RNA-sensing consequences may differ from respiratory effects.

### 4.3 MT-CO3 — recurrent complex-IV sentinel across four networks

**Phase 18 result.** MT-CO3 is selected in astrocytes, inhibitory neurons, OPCs, and vascular cells. It is significant in 42 of 84 tested runs but has only 17 conservative-support runs, showing why the stricter support definition matters. Its strongest aggregate result is vascular, based on a single eligible vascular run; astrocyte and inhibitory results provide broader recurrence.

**Biological interpretation.** MT-CO3 encodes another mtDNA-encoded complex-IV core subunit. Older human AD studies reported reduced or altered MT-CO3/complex-IV transcript measures [34,35], while the current direct-DEG results are mostly AD-up. The discrepancy may reflect cell type, disease stage, normalization, survivor bias, or compensatory mtRNA accumulation. Phase 18 supports complex IV as a coherent module but does not yet distinguish MT-CO3-specific regulation from general respiratory-chain remodeling.

**Validation priority.** Analyze MT-CO3 together with MT-CO2, COX4I1, COX6B1, and COX7C at RNA, protein, assembly, and enzymatic levels. The key test is mitonuclear stoichiometry: does mtDNA-encoded subunit RNA rise while nuclear subunits or assembled complex-IV activity fall? Vascular confirmation requires additional runs or independent tissue because its extreme q value rests on a very small context count.

### 4.4 MT-ATP6 — complex-V sentinel with strong up-direction DEG evidence

**Phase 18 result.** MT-ATP6 is displayed in astrocyte and vascular networks and also passes in excitatory neurons outside the top five. It has 25 conservative-support runs across 16 fine cell types. The earlier DEG signal appears in 56 contexts, mostly AD-up.

**Biological interpretation.** MT-ATP6 encodes an mtDNA-encoded membrane subunit of ATP synthase. ATP synthase is an early oxidative target in AD brain [39], but gene-specific evidence for MT-ATP6 as a causal AD regulator is limited. The result may represent attempted compensation, altered mitochondrial abundance, or complex-V dysfunction despite increased transcript.

**Validation priority.** Measure ATP synthase assembly, oligomerization, ATP production, membrane potential, and MT-ATP6 protein rather than relying on transcript alone. Compare astrocytes and excitatory neurons across sex/APOE strata. Joint measurement of mtDNA copy number and mitochondrial mass is essential. A useful perturbation would test whether normalizing complex-V function restores the broader predicted mitochondrial module, not merely whether severe MT-ATP6 depletion injures cells.

### 4.5 COX4I1 — nuclear-encoded complex-IV anchor and mitonuclear comparator

**Phase 18 result.** COX4I1 is displayed in astrocyte and excitatory networks and also passes in inhibitory neurons. It has 24 conservative-support runs across 16 fine cell types and a strong excitatory aggregate q of 1.52 × 10^-8. Unlike MT-CO2 and MT-CO3, COX4I1 is nuclear encoded.

**Biological interpretation.** COX4I1 provides an important mitonuclear contrast within the complex-IV cluster. The earlier DEG results show 46 contexts, predominantly AD-down, whereas mtDNA-encoded complex-IV genes are often AD-up. A small postmortem study found reduced respiratory-chain function and several complex proteins in AD but did not detect a COX4I1 protein difference [32]. This mixed evidence is compatible with mitonuclear imbalance or cell-type-specific regulation rather than uniform loss of all complex-IV components.

**Validation priority.** Measure COX4I1 RNA and protein alongside MT-CO2/MT-CO3 and assembled complex-IV activity. Test nuclear–mitochondrial transcript ratios at donor and cell-type levels and adjust for mitochondrial mass. Partial COX4I1 perturbation can then ask whether Phase 18 target changes exceed the expected consequences of generic complex-IV impairment.

### 4.6 COX7C — nuclear complex-IV anchor in astrocyte/inhibitory networks

**Phase 18 result.** COX7C is displayed in astrocytes and inhibitory neurons and passes in excitatory neurons outside the display cap. Twenty-five conservative-support runs span 14 fine cell types. The inhibitory result is strong and stable; the astrocyte omission analysis places it in a less stable tier.

**Biological interpretation.** COX7C is a small nuclear-encoded complex-IV subunit. Its 42 earlier direct-DEG contexts are mostly AD-down, again contrasting with many mtDNA-encoded genes. A small candidate-gene study reported only limited/nominal evidence near COX7C and COX6B1, not decisive genetic support [40]. There is little direct gene-specific AD perturbation evidence. Phase 18 therefore mainly supports COX7C as part of a reproducible complex-IV/mitonuclear program.

**Validation priority.** Include COX7C in the first validation panel for both
displayed broad networks: astrocytes and inhibitory neurons. Prioritize protein
stoichiometry, complex-IV assembly, and network-target validation over simple
expression replication. Compare COX7C with COX4I1 to see whether the two
nuclear subunits have distinct directed neighborhoods. Astrocyte results should
be replicated because their stability is weaker. The later public genetic
screen adds one direct but weak bulk-sQTL mapping for COX7C; that single source
result supports prioritization but is not two independent replications across
the two network contexts.

### 4.7 MT-CYB — complex-III sentinel in excitatory and inhibitory neurons

**Phase 18 result.** MT-CYB is selected in excitatory and inhibitory networks, with 37 conservative-support runs across 21 fine cell types and complete omission stability. The earlier DEG result appears in 64 contexts, mainly AD-up.

**Biological interpretation.** MT-CYB encodes cytochrome b, the mtDNA-encoded catalytic core of complex III. Peripheral AD work has reported altered cytochrome-b protein [41], and a recent mtDNA association study reported potentially protective rare MT-CYB variants, but this needs independent replication [42]. These observations are substantially weaker than the Phase 18 network recurrence. As with other mtDNA-encoded subunits, increased transcript can coexist with impaired assembled-complex function.

**Validation priority.** Measure complex-III assembly/activity, supercomplex organization, ROS generation, MT-CYB heteroplasmy, and protein abundance. Use excitatory and inhibitory neuronal models to test whether a milder complex-III manipulation recapitulates the predicted target module. Genetic findings should be replicated in independent ancestry-matched cohorts before influencing causal interpretation.

### 4.8 COX6B1 — excitatory nuclear complex-IV candidate

**Phase 18 result.** COX6B1 is selected only in excitatory neurons, but the evidence is substantial: 23 conservative-support runs across 12 fine cell types, aggregate q = 5.96 × 10^-7, and complete candidate retention. The earlier DEG signal occurs in 37 contexts with mixed direction.

**Biological interpretation.** COX6B1 is a nuclear-encoded complex-IV subunit important for holoenzyme organization and activity. Gene-specific AD evidence is limited; the reported human genetic signal is nominal and not sufficient for a causal claim [40]. The strength and stability of the Phase 18 excitatory result therefore represent a potentially useful new cell-type-specific observation.

**Validation priority.** Test COX6B1 protein, complex-IV/supercomplex assembly, and respiration in excitatory subtypes. Compare its directed neighborhood with COX4I1 and MT-CO2. CRISPRi with dose titration and rescue can determine whether the predicted mitochondrial targets respond before global respiratory collapse. Human eQTL/colocalization and proteomic-QTL analyses could provide independent causal support.

### 4.9 UQCR10 — strong novel excitatory complex-III candidate

**Phase 18 result.** UQCR10 is the rank-2 excitatory MT driver, with aggregate q = 2.76 × 10^-10, 25 conservative-support runs across 13 fine cell types, support in all six primary sex/APOE groups and both directions, and complete omission stability. This is one of the strongest network results outside the recurrent mtDNA-encoded genes.

**Biological interpretation.** UQCR10 is a small nuclear-encoded complex-III subunit. A targeted search did not identify convincing UQCR10-specific AD genetic or perturbation evidence. That makes it a genuinely novel Phase 18 candidate, but also one for which structural-module centrality is the main alternative explanation. The 31 earlier direct-DEG contexts, mostly AD-down, support disease responsiveness but not causality.

**Validation priority.** UQCR10 deserves focused excitatory-neuron validation. Measure complex-III and supercomplex assembly, cytochrome-c reduction, ROS, respiration, and predicted targets after graded CRISPRi/CRISPRa and rescue. Compare its effects with MT-CYB perturbation: a distinct target signature would argue for a specific regulatory/assembly role, whereas identical global complex-III failure would support the sentinel interpretation. Human genetic colocalization and protein evidence should be actively sought.

### 4.10 MT-ND5 — inhibitory complex-I candidate with a significant/conservative-support gap

**Phase 18 result.** MT-ND5 is selected only in inhibitory neurons. Although 33 of 83 tested runs are called significant, only eight meet the conservative-support definition; these span seven fine cell types. The difference implies that many significant returns have limited other-query overlap or fail the stricter enrichment/q conditions. Its aggregate q remains strong at 2.69 × 10^-6.

**Biological interpretation.** MT-ND5 encodes another mtDNA-encoded complex-I membrane subunit. The earlier DEG result appears in 52 contexts, predominantly AD-up. Unlike MT-ND4, direct MT-ND5-specific AD mechanistic evidence is sparse. The inhibitory specificity could be real, or it could reflect network topology and mitochondrial transcript covariance.

**Validation priority.** Compare MT-ND5 directly with MT-ND4 in inhibitory neurons. Measure complex-I assembly/activity, NADH redox state, respiration, ROS, mtDNA copy number/heteroplasmy, and RNA localization. Inspect the 25 significant but non-conservative runs to identify which condition failed; if most contain only one other query gene, the aggregate signal should be framed as statistically strong but biologically less dense.

## 5. Cross-gene synthesis

### 5.1 The strongest mechanistic non-MT candidates

- **SELENOW** has the best direct AD perturbation precedent and a strong, stable excitatory Phase 18 signal.
- **APOE** has extensive external astrocyte–mitochondria evidence; Phase 18 contributes network and context specificity rather than a novel AD gene.
- **LAMTOR5** provides a plausible lysosome–mTORC1–mitochondria mechanism with stable evidence in two neuronal networks, but needs direct AD validation.
- **RPL11** is the broadest non-MT network candidate and has human AD capillary protein support plus a defined ribosomal-stress/p53 pathway. Specificity versus generic ribosomal stress is the central question.
- **FTL and ANKRD11** are potentially interesting OPC findings, but their support is confined to one fine cell type and cannot yet be called robust.

### 5.2 A ribosomal module, not yet six separate causal genes

RPL11, RPS15, RPLP1, RPS13, RPL38, and RPL15 form a conspicuous translation/ribosomal cluster. The cluster may reflect:

1. biologically important ribosomal stress and p53 signaling;
2. selective translation of mitochondrial or stress-response transcripts;
3. high expression and dense network connectivity; or
4. a general disease/quality response rather than upstream mitochondrial regulation.

The next analysis should compare these genes as a module, quantify shared directed targets, and use expression/degree/ribosomal-class matched nulls. Only genes with reproducible target specificity should advance as individual mechanistic drivers.

### 5.3 A convergent lysosome–mitochondria axis

LAMTOR5, ATP6V1F, LAPTM4A, and APOE converge on lysosomal sensing, acidification, lipid handling, autophagy, or mitophagy. This convergence is more mechanistically informative than any one sparse candidate. A combined perturbation design could test whether the genes occupy the same pathway: APOE-dependent lipid stress → lysosomal dysfunction/Ragulator signaling → impaired mitophagy and mitochondrial output.

### 5.4 MT drivers show coordinated respiratory remodeling

The MT list contains complex I (MT-ND4, MT-ND5), complex III (MT-CYB, UQCR10), complex IV (MT-CO2, MT-CO3, COX4I1, COX6B1, COX7C), and complex V (MT-ATP6). The mixture of mtDNA- and nuclear-encoded subunits is valuable for testing mitonuclear imbalance. Human AD studies report lower mtDNA quantity and compartment-specific mitochondrial-expression changes [43–45], while mitochondrial translation perturbation can alter APOE, amyloid, and tau phenotypes [46].

The earlier DEG results often show mtDNA-encoded genes AD-up but nuclear-encoded respiratory subunits AD-down. This could indicate compensation, altered mitochondrial mass, RNA-processing differences, or failure to assemble functional complexes. Therefore, RNA-only confirmation is insufficient. Protein stoichiometry, assembled-complex activity, mtDNA quantity/quality, and mitochondrial mass must be measured together.

### 5.5 Sex/APOE patterns are hypotheses, not interactions

Across many non-MT and MT genes, supporting mitochondrial queries tend to be AD-up in female ε2 contexts and AD-down in male ε2 or female ε4 contexts. This echoes the earlier pathway-level pattern, but the current panels count supporting KDA contexts; they do not fit interaction terms and do not account for donor-level dependence. Male ε2 is also a relatively small stratum in the source cohort. Formal donor-level pseudobulk models are required before claiming sex- or APOE-specific gene effects.

## 6. Recommended validation program

### 6.1 Immediate computational validation

1. **Directed neighborhood figures:** For each priority gene, export two to three upstream/downstream layers, highlight mitochondrial query genes, label edge direction, and render editable SVGs in Cytoscape.
2. **Network-specific nulls:** Recalculate enrichment against genes matched for expression, Bayesian-network degree, neighborhood size, and functional class. Include a ribosomal-gene matched null for the ribosomal candidates.
3. **Robustness across network construction:** Repeat KDA with alternative edge-confidence thresholds or independently inferred networks where available.
4. **Fine-cell recurrence:** Use an UpSet or compact membership plot to show exactly which fine cell types support each gene, rather than only their counts.
5. **Formal sex/APOE tests:** Fit donor-level disease × sex × APOE models for candidate expression and target-module scores. Do not treat nuclei as independent donors.
6. **Mitochondrial technical covariates:** Test sensitivity to mitochondrial read fraction, mtDNA copy number where available, RNA quality, cell/nucleus quality, and inferred mitochondrial mass.

### 6.2 Orthogonal human evidence

- Search AD GWAS, rare-variant, eQTL/sQTL, colocalization, and proteomic-QTL evidence for the non-established candidates.
- Validate protein abundance and complex assembly in cell-type-resolved proteomic or spatial datasets.
- Analyze mtDNA copy number, heteroplasmy, and mitochondrial RNA processing/localization for MT-ND4, MT-ND5, MT-CYB, MT-CO2, MT-CO3, and MT-ATP6.
- Use spatial transcriptomics or imaging to confirm OPC FTL/ANKRD11 and astrocyte RPL15/LAPTM4A localization.
- Test recurrence in independent human cohorts and in APOE-targeted-replacement single-cell models when those data become available.

### 6.3 Experimental sequence

Use a staged design rather than perturbing all 25 genes immediately:

1. **Wave 1 mechanistic non-MT genes:** SELENOW, APOE, LAMTOR5, RPL11, and FTL or ANKRD11.
2. **Wave 2 pathway/module genes:** RPS15, ATP6V1F, LAPTM4A, RPLP1/RPS13/RPL15/RPL38, DYNLT1, and NCOA1.
3. **Representative MT sentinels:** MT-CO2 and MT-ND4, plus one nuclear comparator from each prominent complex—COX4I1 or COX6B1 for complex IV and UQCR10 for complex III.

For every perturbation, use graded CRISPRi/CRISPRa, an orthogonal reagent, and rescue. Measure the predicted network targets first, then pathway-specific phenotypes, respiration, and viability. A candidate should be called a functional driver only if perturbation changes its predicted downstream module at a dose that does not merely cause generalized cell stress or death.

## 7. Initial prioritization and conclusions

The current evidence supports three different kinds of conclusions:

- **Externally reinforced AD candidates:** APOE and SELENOW.
- **Mechanistically plausible new or under-studied candidates:** LAMTOR5, ATP6V1F, LAPTM4A, FTL, ANKRD11, DYNLT1, and UQCR10. These are the most valuable targets for new validation, with confidence varying substantially by recurrence.
- **Module-level candidates/sentinels:** the ribosomal cluster and most structural respiratory-chain genes. They strongly identify altered translation and oxidative-phosphorylation modules but require extra work before individual genes are called upstream regulators.

The most defensible first story is not that all 25 genes independently drive AD. It is that Phase 18 identifies several coherent cell-type-specific systems—ribosomal stress, lysosome–mTOR/mitophagy, iron handling, intracellular transport, and mitonuclear respiratory remodeling—and nominates individual genes within those systems for causal testing.

## 8. Primary literature cited

The list below emphasizes primary human, animal, or mechanistic studies identified in a targeted literature search through 2026-08-15. Lack of a listed gene-specific paper means that no convincing direct study was identified in this targeted search, not that none exists.

1. Suzuki H, et al. Brain capillary proteomics in Alzheimer's disease, including RPL11 and RPL15 changes. *J Cereb Blood Flow Metab.* 2022. [doi:10.1177/0271678X221111602](https://doi.org/10.1177/0271678X221111602)
2. Ding Q, et al. Ribosome dysfunction is an early event in Alzheimer's disease. *J Neurosci.* 2005. [doi:10.1523/JNEUROSCI.3040-05.2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005)
3. Zhang Y, et al. Ribosomal protein L11 inhibits MDM2 and activates p53. *Mol Cell Biol.* 2003. [doi:10.1128/MCB.23.23.8902-8912.2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003)
4. Slomnicki LP, et al. Pro-apoptotic requirement of ribosomal protein L11 in ribosomal stress-challenged cortical neurons. *Mol Neurobiol.* 2018. [doi:10.1007/s12035-016-0336-y](https://doi.org/10.1007/s12035-016-0336-y)
5. Daftuar L, et al. Ribosomal protein S15 and the MDM2–p53 pathway. *PLoS ONE.* 2013. [doi:10.1371/journal.pone.0068667](https://doi.org/10.1371/journal.pone.0068667)
6. Martin I, et al. LRRK2 phosphorylation of ribosomal protein S15 and neurodegeneration. *Cell.* 2014. [doi:10.1016/j.cell.2014.01.064](https://doi.org/10.1016/j.cell.2014.01.064)
7. Bar-Peled L, et al. Ragulator is a GEF for Rag GTPases and activates mTORC1 at lysosomes. *Cell.* 2012. [doi:10.1016/j.cell.2012.07.032](https://doi.org/10.1016/j.cell.2012.07.032)
8. Morita M, et al. mTORC1 controls mitochondrial activity and biogenesis. *Cell Metab.* 2013. [doi:10.1016/j.cmet.2013.10.001](https://doi.org/10.1016/j.cmet.2013.10.001)
9. Norambuena A, et al. Aβ disrupts lysosome-to-mitochondria mTORC1 signaling. 2018. [PMC6236329](https://pmc.ncbi.nlm.nih.gov/articles/PMC6236329/)
10. Zhang W, et al. Defective LAMTOR5 leads to autoimmunity by deregulating V-ATPase and lysosomal acidification. *Adv Sci.* 2024. [doi:10.1002/advs.202400446](https://doi.org/10.1002/advs.202400446)
11. Lee JH, et al. Faulty autolysosome acidification in AD mouse models before extracellular amyloid deposition. *Nat Neurosci.* 2022. [Nature article](https://www.nature.com/articles/s41593-022-01084-8)
12. Swedish Alzheimer's disease APP variant perturbs retrograde molecular-motor activity and axonal transport pathways. 2024. [PMC10997842](https://pmc.ncbi.nlm.nih.gov/articles/PMC10997842/)
13. Ren L, et al. SELENOW promotes tau clearance and improves pathology and memory in 3xTg-AD mice. *Commun Biol.* 2024. [doi:10.1038/s42003-024-06572-0](https://doi.org/10.1038/s42003-024-06572-0)
14. Misra S, et al. SELENOW regulates macrophage redox state and mitochondrial respiration. *Redox Biol.* 2023. [doi:10.1016/j.redox.2022.102571](https://doi.org/10.1016/j.redox.2022.102571)
15. Jeong D, et al. Antioxidant function of selenoprotein W. *FEBS Lett.* 2002. [doi:10.1016/S0014-5793(02)02628-5](https://doi.org/10.1016/S0014-5793(02)02628-5)
16. Lee JH, et al. APOE4-associated lysosomal cholesterol accumulation impairs astrocyte mitophagy and oxidative phosphorylation. *Cell Rep.* 2023. [doi:10.1016/j.celrep.2023.113183](https://doi.org/10.1016/j.celrep.2023.113183)
17. Schmukler E, et al. APOE4 alters mitochondrial dynamics and mitophagy in astrocytes. *Cell Death Dis.* 2020. [doi:10.1038/s41419-020-02776-4](https://doi.org/10.1038/s41419-020-02776-4)
18. Qi G, et al. ApoE4 impairs neuron–astrocyte fatty-acid coupling and oxidation. *Cell Rep.* 2021. [doi:10.1016/j.celrep.2020.108572](https://doi.org/10.1016/j.celrep.2020.108572)
19. Williams HC, et al. APOE genotype alters astrocyte carbon flux and mitochondrial metabolism. *Neurobiol Dis.* 2020. [doi:10.1016/j.nbd.2020.104742](https://doi.org/10.1016/j.nbd.2020.104742)
20. Xue S, et al. RNA regulons in Hox 5′ UTRs confer ribosome specificity to gene regulation. *Nature.* 2015. [doi:10.1038/nature14010](https://doi.org/10.1038/nature14010)
21. Milkereit R, et al. LAPTM4A lysosomal localization and NEDD4-family interaction. 2011. [PMC3214061](https://pmc.ncbi.nlm.nih.gov/articles/PMC3214061/)
22. LAPTM4A as a regulator of lysosome/autophagy homeostasis. 2026. [PubMed 42020342](https://pubmed.ncbi.nlm.nih.gov/42020342/)
23. Ka M, et al. ANKRD11 controls neuronal differentiation and dendrite development through chromatin regulation and BDNF/TrkB signaling. *Neurobiol Dis.* 2018. [doi:10.1016/j.nbd.2017.12.008](https://doi.org/10.1016/j.nbd.2017.12.008)
24. Connor JR, et al. Iron and ferritin in Alzheimer's disease brain. *J Neurosci Res.* 1992. [doi:10.1002/jnr.490310111](https://doi.org/10.1002/jnr.490310111)
25. Todorich B, et al. H-ferritin-mediated iron uptake by oligodendrocytes. *Glia.* 2011. [doi:10.1002/glia.21164](https://doi.org/10.1002/glia.21164)
26. Li S, et al. Iron overload promotes oligodendrocyte ferroptosis. *Neurochem Res.* 2023. [doi:10.1007/s11064-022-03807-6](https://doi.org/10.1007/s11064-022-03807-6)
27. Ashraf A, et al. Iron, lipid peroxidation, and ferroptosis-related pathology in human AD brain. *Redox Biol.* 2020. [doi:10.1016/j.redox.2020.101494](https://doi.org/10.1016/j.redox.2020.101494)
28. Bian C, et al. SRC-1/NCOA1 in hippocampal estrogen signaling and memory. *J Steroid Biochem Mol Biol.* 2017. [doi:10.1016/j.jsbmb.2017.08.003](https://doi.org/10.1016/j.jsbmb.2017.08.003)
29. Ncoa1/SRC-1 deletion does not materially alter amyloid deposition or gliosis in APP/PS1 mice. 2020. [PMC7311769](https://pmc.ncbi.nlm.nih.gov/articles/PMC7311769/)
30. NCOA1 rare-variant association with midlife plasma Aβ in African Americans, without external replication. 2017. [PMC5509141](https://pmc.ncbi.nlm.nih.gov/articles/PMC5509141/)
31. NCOA1-region association in an Ashkenazi Jewish AD GWAS. 2023. [PMC10689571](https://pmc.ncbi.nlm.nih.gov/articles/PMC10689571/)
32. Troutwine BR, et al. Mitochondrial respiratory-chain function and proteins in postmortem AD brain. *Neurobiol Dis.* 2022. [doi:10.1016/j.nbd.2022.105781](https://doi.org/10.1016/j.nbd.2022.105781)
33. Maurer I, et al. Reduced cytochrome-c oxidase activity in AD temporal cortex and hippocampus. *Neurobiol Aging.* 2000. [doi:10.1016/S0197-4580(00)00112-3](https://doi.org/10.1016/S0197-4580(00)00112-3)
34. Chandrasekaran K, et al. Impairment of mitochondrial cytochrome-oxidase gene expression in AD. *Mol Brain Res.* 1994. [doi:10.1016/0169-328X(94)90147-3](https://doi.org/10.1016/0169-328X(94)90147-3)
35. Chandrasekaran K, et al. Region-specific mitochondrial transcript changes in AD brain. 1999. [PubMed 10447460](https://pubmed.ncbi.nlm.nih.gov/10447460/)
36. Simonian NA, et al. Reduced MT-ND4 expression in AD temporal cortex. *Brain Res.* 1996. [PubMed 8725003](https://pubmed.ncbi.nlm.nih.gov/8725003/)
37. Lee J, et al. SIRT3–p53 regulation of mitochondrial genes including MT-ND4 in AD-related models. *Aging Cell.* 2018. [doi:10.1111/acel.12679](https://doi.org/10.1111/acel.12679)
38. Pan Y, et al. YTHDF2-dependent handling of cytosolic m6A-modified MT-ND4 RNA in Aβ-induced neuronal innate immunity. *Sci Adv.* 2026. [doi:10.1126/sciadv.adz0887](https://doi.org/10.1126/sciadv.adz0887)
39. Terni B, et al. Mitochondrial ATP synthase is an early oxidative target in AD brain. *Brain Pathol.* 2010. [doi:10.1111/j.1750-3639.2009.00266.x](https://doi.org/10.1111/j.1750-3639.2009.00266.x)
40. Chen C, et al. Candidate mitochondrial-gene association study including COX6B1 and COX7C; evidence was limited after correction. 2018. [PMC6135758](https://pmc.ncbi.nlm.nih.gov/articles/PMC6135758/)
41. Cytochrome-b protein changes in peripheral blood mononuclear cells in AD. 2016. [doi:10.1155/2016/5923938](https://doi.org/10.1155/2016/5923938)
42. MT-CYB rare-variant association study in AD; requires independent replication. 2026. [SAGE article](https://journals.sagepub.com/doi/abs/10.1177/13872877261442231)
43. Klein H-U, et al. Mitochondrial DNA quantity and quality across 1,361 human brain samples in AD. *Mol Neurodegener.* 2021. [doi:10.1186/s13024-021-00495-8](https://doi.org/10.1186/s13024-021-00495-8)
44. Mastroeni D, et al. Compartment-dependent mitonuclear gene-expression changes in AD brain. *Alzheimers Dement.* 2017. [doi:10.1016/j.jalz.2016.09.003](https://doi.org/10.1016/j.jalz.2016.09.003)
45. Lunnon K, et al. Mitochondrial gene-expression differences in blood in AD. *Neurobiol Aging.* 2017. [doi:10.1016/j.neurobiolaging.2016.12.029](https://doi.org/10.1016/j.neurobiolaging.2016.12.029)
46. Gabrielli M, et al. Perturbation of mitochondrial translation alters APOE, amyloid, and tau-related phenotypes. *Alzheimer's Dement.* 2024. [doi:10.1002/alz.14275](https://doi.org/10.1002/alz.14275)

## 9. Internal data sources

- [Phase 18 key-driver selection process](../../phase_18_key_driver_selection/key_driver_selection_process.md)
- [Phase 18 non-MT evidence-atlas data](../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_non_mt/phase18_evidence_atlas_non_mt_gene_summary.tsv)
- [Phase 18 MT evidence-atlas data](../../../results/figures/analysis/phase_18_key_driver_selection/evidence_atlas_mt/phase18_evidence_atlas_mt_gene_summary.tsv)
- [Phase 18 non-MT sex/APOE plot data](../../../results/figures/analysis/phase_18_key_driver_selection/sex_apoe_non_mt/phase18_sex_apoe_non_mt_plot_data.tsv)
- [Phase 18 MT sex/APOE plot data](../../../results/figures/analysis/phase_18_key_driver_selection/sex_apoe_mt/phase18_sex_apoe_mt_plot_data.tsv)
- [Phase 8 MAST DEG outputs](../../../results/minerva_production/08_mast/), used for the direct-DEG context counts in Section 2
- [Earlier joint mitochondrial discussion](../kda_and_pathway/phase11_phase12_joint_mitochondrial_discussion.md), used only for earlier DEG/pathway context and conceptual framing; deprecated Phase 12 key-driver selections and figures were not used.
- [Notes after the 2026-08-12 presentation](../../email_notes/notes_after_08122026_presentation.txt)
