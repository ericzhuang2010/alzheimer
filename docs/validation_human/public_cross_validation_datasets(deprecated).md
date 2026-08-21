# Public Alzheimer Datasets for Cross-Cohort Validation

The best first external dataset is **GSE237718**, a Mayo Clinic temporal-cortex snRNA-seq cohort deliberately balanced across APOE2, APOE3, APOE4, sex, and AD/control status. It most closely reproduces this repository's six sex-APOE strata. It should be paired with **SEA-AD A9/PFC** for a same-region replication, then supplemented with the independent MSSM/HBCC components of **NPS-AD** if their controlled APOE metadata can be obtained.

This is best described as **independent cross-cohort validation**, rather than cross-validation in the machine-learning sense.

## A. Study intent summary

The repository study tests whether sex and APOE modify Alzheimer-associated mitochondrial programs in donor-level pseudobulk data from ROSMAP prefrontal cortex. Its primary design includes:

- Female and male x APOE2 carrier, APOE3/3, and APOE4 carrier.
- Astrocytes, excitatory neurons, and inhibitory neurons as primary cell classes.
- Mitochondrial OXPHOS, mitochondrial translation, MICOS/MIB, and mitonuclear coupling.
- Candidate regulatory drivers including APOE, COX7C, SELENOW, LAMTOR5, RPL11, FTL, and ANKRD11.

This is documented in the [study proposal](../research_class/HSR_2026_27_mitochondria_sex_APOE_AD_proposal_draft.md) and [cross-validation guide](kda_phase_18/phase18_key_driver_cross_validation_guide.md).

## B. Best-fit study pattern

The best fit is primarily:

- **Pattern B:** identify reproducible cell-type-specific disease states and modifiers.
- **Pattern E:** validate the mitochondrial modules and downstream targets of nominated key drivers.

External cohorts should be analyzed separately using donor-level pseudobulk. They should not be integrated with ROSMAP before validation, because that would blur the independence of the replication evidence.

## C. Ranked public datasets

The datasets are ranked by cohort independence, sex/APOE metadata, anatomical match, donor-level resolution, relevant cell coverage, sample size, and accessibility.

| Rank | Dataset | Design and fit | Recommended use | Main limitation |
|---:|---|---|---|---|
| **1** | [GSE237718](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE237718), Mayo temporal cortex | 56 retained donors: 29 AD and 27 controls; both sexes; deliberately sampled APOE2/3, APOE3/3, APOE3/4, and APOE4/4; 10x snRNA-seq | Best direct replication of sex x APOE x AD effects and frozen mitochondrial modules | Temporal rather than prefrontal cortex; only about 4-5 donors in most broad sex-APOE-diagnosis cells |
| **2** | [SEA-AD](https://brain-map.org/consortia/sea-ad/our-data), especially A9/PFC | 84 deeply characterized donors; both sexes; public APOE genotype and pathology; MTG and A9/PFC snRNA-seq | Best fully open, independent, same-region replication; ideal for continuous pathology and APOE3/APOE4 effects | Only two APOE2 carriers with dementia in the metadata, so APOE2 disease contrasts are severely underpowered |
| **3** | [NPS-AD/PsychAD](https://psych-ad.org/data/), independent MSSM and HBCC cohorts | Population-scale DLPFC atlas; 1,494 donors overall and more than 6.3 million nuclei; open processed data through [CELLxGENE](https://cellxgene.cziscience.com/collections/84ce6837-548d-4a1f-919f-0bc0d9a3952f) | Strongest option for well-powered DLPFC disease, sex, cell-state, and mitochondrial replication | Exact APOE fields require a controlled-metadata audit; cross-disorder cohort requires careful diagnostic filtering |
| **4** | [GSE174367](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174367), Morabito et al. | Frontal cortex, 19 donors; paired snRNA-seq, snATAC-seq, and bulk RNA-seq | Best orthogonal regulatory validation for transcription factors, enhancers, and key-driver target modules | Too small for credible sex x APOE interaction testing; APOE is not provided in the GEO sample metadata |
| **5** | [GSE254205](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE254205), Haney et al. | Frontal cortex AD APOE4/4 versus AD APOE3/3 and matched APOE3/3 controls; snRNA-seq plus microglial RNA/ATAC experiments | Best focused APOE4 microglial lipid/mitochondrial mechanism validation | Specialized design, principally microglial; does not reproduce the complete six-stratum design |
| **6** | [GSE167490](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE167490) | Prefrontal cortex, 16 APOE2/3 donors: 10 AD and 6 non-symptomatic controls; astrocyte/oligodendrocyte enriched | Useful focused test of whether APOE2-associated astrocyte and oligodendrocyte signals replicate | No within-cohort APOE-genotype contrast and limited sample size |
| **7** | [GSE157827](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE157827) | Prefrontal cortex, 21 donors: 12 AD and 9 controls; approximately 169,000 nuclei across major brain cell classes | General PFC disease-direction and mitochondrial-module validation | Public GEO metadata do not provide the sex/APOE structure needed for the main modifiers |
| **8** | [GSE243292](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243292) | DLPFC, 15 donors spanning normal aging, pathological aging, and AD; APOE/TREM2 genotypes | Small pilot for genotype-related astrocyte and microglial effects | Very small, no APOE2 group, and insufficient sex metadata for the primary design |

### Why GSE237718 ranks first

The public metadata resolve into approximately 4-5 donors in every broad combination of:

- AD/control
- Female/male
- APOE2 carrier, APOE3/3, or APOE4 carrier

That makes it the only fully open cohort identified here that closely reconstructs all six of the repository's sex-APOE strata. The associated study also explicitly investigates APOE-genotype-specific cellular pathology ([Cell paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12333916/)).

Its small group sizes mean the complete discovery analysis should not simply be rerun with dozens of interaction tests. It is better suited to a **frozen, reduced replication family**.

### Why SEA-AD ranks above NPS-AD for immediate use

SEA-AD supplies public donor-level APOE, sex, cognition, and pathology metadata together with open processed data, and A9 is anatomically close to the discovery PFC region. Its weakness is the shortage of APOE2 dementia cases.

NPS-AD is much larger and may ultimately become the strongest validation resource. However:

- The RADC component overlaps the ROSMAP source population and should not be called independent.
- The MSSM and HBCC components are the appropriate independent subsets.
- The open CELLxGENE annotations do not expose enough APOE information to confirm all six strata.
- Full clinical and genotype metadata are distributed through the [AD Knowledge Portal release](https://news.adknowledgeportal.org/data-release-25-6-june-2025-2/) and require access/eligibility checks.

If the MSSM/HBCC metadata contain usable APOE genotype and sufficient AD/control donors, NPS-AD should conditionally move to rank 1 or 2.

## D. Recommended primary plan

Use a three-layer validation strategy:

1. **GSE237718:** direct design replication.
2. **SEA-AD A9:** same-region replication using APOE3/APOE4 and continuous pathology.
3. **GSE174367:** multiomic support for key-driver regulatory relationships.

Add NPS-AD MSSM/HBCC once its controlled metadata pass the independence, diagnosis, and APOE feasibility audit.

## E. Analysis modules

| Module | Primary validation question |
|---|---|
| Donor-level pseudobulk DE | Do AD effects have the same direction within each broad cell type? |
| Frozen mitochondrial modules | Are OXPHOS, mitochondrial translation, MICOS/MIB, and mitonuclear coupling scores reproducible? |
| Modifier effects | Do APOE or sex change the AD effect in the same direction? |
| Key-driver targets | Are predicted target sets of APOE, SELENOW, LAMTOR5, RPL11, FTL, ANKRD11, or COX7C shifted coherently? |
| Regulatory support | Are target genes connected through accessible regulatory elements in GSE174367? |
| Effect-size synthesis | Are donor-level effects directionally concordant across independent cohorts? |

## F. Four workload configurations

| Configuration | Scope |
|---|---|
| **Lite** | GSE237718 only; three primary cell types, four frozen mitochondrial modules, and a small set of prespecified APOE contrasts |
| **Standard - recommended** | Lite plus SEA-AD A9; use APOE3/APOE4 and pathology-continuum validation in SEA-AD |
| **Advanced** | Standard plus NPS-AD MSSM/HBCC after metadata approval, followed by cohort-level effect-size meta-analysis |
| **Publication+** | Advanced plus GSE174367 regulatory evidence and orthogonal bulk/proteomic validation from [MSBB](https://www.synapse.org/Synapse%3Asyn3159438) or [MayoRNAseq](https://www.synapse.org/Synapse%3Asyn5550404) |

Each configuration is a strict extension of the preceding one.

## G. Validation criteria

A signal should count as replicated when it shows:

- The same direction in the same broad cell type.
- A reasonably compatible effect size and confidence interval.
- Module- or target-set-level significance after correcting within the frozen validation family.
- No dependence on one donor or a large change in cell-type composition.
- Consistency across alternate pathology definitions where available.

An external nominal *P* < 0.05 alone should not be the criterion. Interaction estimates with only 4-5 donors per stratum should be reported as exploratory even if nominally significant.

## H. Workflow

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

1. Freeze the discovery claims, gene modules, cell types, and contrast hierarchy before inspecting validation results.
2. Download and audit donor metadata first; generate diagnosis x sex x APOE feasibility tables.
3. Confirm donor independence from ROSMAP and check whether any datasets share brain-bank donors.
4. Harmonize detailed annotations into the repository's seven broad cell classes.
5. Aggregate raw counts to donor x broad-cell pseudobulk.
6. Require the same minimum nucleus and donor-quality rules across strata.
7. Fit count models at the donor level, including age, sex, APOE, diagnosis/pathology, technical covariates, and interactions only when supported by sample size.
8. Test frozen mitochondrial modules and key-driver target sets without redefining them in each validation cohort.
9. Analyze every cohort independently, then compare or meta-analyze effect sizes; do not pool nuclei across cohorts.
10. Report unsupported, directionally concordant, and statistically replicated findings separately.

## I. Evidence hierarchy

From strongest to weakest:

1. Same cell type, same contrast, same direction in an independent cohort.
2. Same module and cell type under a closely related pathology definition.
3. Same biological pathway in another brain region.
4. Regulatory or proteomic support for the same key driver.
5. Disease-only replication without sex/APOE information.

## J. Expected deliverables

The most useful outputs would be:

- Dataset feasibility and donor-overlap table.
- Forest plots of per-cohort mitochondrial-module effects.
- Heatmap of discovery-versus-validation effect directions.
- Sex x APOE x disease effect plots with donor counts displayed.
- Key-driver target-set replication matrix.
- A clear table labeling each claim as replicated, directionally supported, not replicated, or not testable.

## K. Access summary

Fully open processed data are available immediately for GSE237718, SEA-AD, GSE174367, GSE254205, GSE167490, GSE157827, and GSE243292. NPS-AD processed expression is open through CELLxGENE, while some detailed clinical/genotype fields require Synapse/AD Knowledge Portal access.

## L. Main risks

- **Pseudoreplication:** nuclei or sequencing lanes must never be treated as independent subjects.
- **ROSMAP overlap:** exclude the NPS-AD RADC component from independent validation.
- **Region differences:** temporal cortex results may legitimately differ from PFC.
- **Sparse APOE2 cases:** especially severe in SEA-AD dementia cases.
- **Label mismatch:** cognitive diagnosis, pathological AD, dementia, and continuous neuropathology are not interchangeable.
- **Selection after seeing results:** modules and contrasts must be frozen beforehand.
- **Bulk-data confounding:** MSBB/Mayo bulk results are supportive but cannot establish cell-intrinsic replication.

The recommended sequence is therefore: **start with GSE237718, use SEA-AD A9 as the second cohort, and begin the NPS-AD MSSM/HBCC access-and-metadata audit in parallel.**
