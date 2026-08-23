# Public Mouse Transcriptomic Datasets for Validating Human PFC Alzheimer Findings

## Detailed comparison of APOE, sex, disease, brain region, modality, and biological replication

**Revised report**  
**Search and metadata re-audit date:** August 23, 2026  
**Human discovery tissue:** prefrontal cortex (PFC)  
**Primary validation themes:** APOE isoform, sex, Alzheimer-related pathology, cell type, and mitochondrial biology

---

## Contents

1. [Executive summary](#executive-summary)
2. [What changed after learning that the human data are from PFC](#1-what-changed-after-learning-that-the-human-data-are-from-pfc)
3. [How regional evidence should be labeled](#2-how-regional-evidence-should-be-labeled)
4. [Evaluation criteria](#3-evaluation-criteria-used-in-this-report)
5. [Master comparison matrix](#4-master-comparison-matrix)
6. [Recommended tiered setup](#5-recommended-tiered-setup)
7. [Detailed dataset profiles](#6-detailed-dataset-profiles)
8. [Mapping to the human PFC comparison groups](#7-how-the-datasets-map-to-the-human-pfc-comparison-groups)
9. [Recommended analysis plan](#8-recommended-analysis-plan)
10. [Mitochondrial validation considerations](#9-mitochondrial-validation-considerations)
11. [Dataset combinations by cell type](#10-recommended-dataset-combinations-by-human-pfc-cell-type)
12. [Practical data access](#11-practical-data-access-comparison)
13. [Metadata audit checklist](#12-metadata-audit-checklist)
14. [Claims and risks](#13-claims-that-are-supported-versus-claims-to-avoid)
15. [Suggested figures](#15-suggested-figures-for-the-eventual-validation-paper)
16. [Definitive new experiment](#16-definitive-new-mouse-experiment-if-public-data-are-insufficient)
17. [Final recommendation](#17-final-recommendation)
18. [Primary public resources](#18-primary-public-resources)
19. [Search limitations](#19-search-and-interpretation-limitations)

---

## Executive summary

The original search asked for a mouse-brain dataset containing human APOE3 versus APOE4, female versus male mice, an Alzheimer disease (AD)-model versus matched non-AD comparison, single-cell or single-nucleus RNA sequencing, and independent mice. The new information that the human discovery tissue is **prefrontal cortex (PFC)** adds an important requirement: the most persuasive mouse evidence should come from **frontal/PFC tissue**, or at least from a clearly identified cortical dissection.

### Updated bottom line

> **No openly auditable public dataset identified in this re-audit satisfies the complete design:** explicit mouse PFC or frontal cortex, human APOE3 versus APOE4, both sexes, AD-model versus matched non-AD mice, broad scRNA-seq or snRNA-seq coverage, and enough independent mice in every group.

The available datasets divide the desired experiment into separate pieces. Therefore, the best public-data strategy is no longer to name one universal “primary dataset.” It is to use **three complementary core anchors**, followed by one or more cell-type-specific disease references:

1. **[GSE185063](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE185063)** — the strongest **broad cortical snRNA-seq APOE3-versus-APOE4 anchor**. It localizes APOE-associated effects across neurons, astrocytes, microglia, oligodendroglia, OPCs, and vascular cells. Its main limitations are no AD model and no reliable public mouse-level sex map.
2. **[GSE241553](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241553)** — the strongest **cortical, sex-balanced, single-cell mechanistic APOE anchor under amyloid pathology**. It conditionally turns human apoE3 or apoE4 on in microglia and CNS-associated macrophages (CAMs). It is not a conventional whole-animal APOE3-versus-APOE4 cohort and has no non-amyloid control group.
3. **[GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857)** — the only candidate here with the complete **APOE3/APOE4 × female/male × 5xFAD/control** design. It is bulk RNA-seq of sorted microglia and is not PFC- or cortex-specific; several control cells contain only one to three mice.

For the missing broad **AD-versus-control** component, select a supporting dataset according to the human cell type:

- **Cortical broad-cell disease direction:** [GSE140399](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140399), but only descriptively because three mice were pooled into one library per genotype and region.
- **Replicated broad-cell disease direction:** [GSE140510](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140510), with three independent mice per genotype, but the public record describes mouse brain rather than an explicit PFC/cortical dissection.
- **Astrocyte and age progression:** [GSE143758](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758), whose strongest all-cell atlas is hippocampal; its cortical component contains only four astrocyte samples, one per age-by-genotype combination.
- **Sex-by-amyloid microglial state support:** [GSE127892](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127892), from cortex and hippocampus, but two mice were pooled per condition and the experiment uses mouse Apoe rather than human APOE isoforms.
- **APOE2 and microglial aging:** [GSE225503](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225503) / [GSE239999](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE239999), with APOE2/APOE3/APOE4 in 5xFAD immune cells; there is no non-AD group and public sex metadata are insufficient.

### Revised recommendation in one sentence

> Use **GSE185063** for cortical cell-type localization, **GSE241553** for sex-aware microglia/CAM-specific APOE induction under amyloid, and **GSE163857** for the direct APOE-by-sex-by-disease microglial test; then add a disease-direction dataset selected for the human PFC cell type being validated.

---

## 1. What changed after learning that the human data are from PFC

The earlier report correctly concluded that a full-factorial public single-cell cohort was not available. The PFC information changes the **priority and interpretation** of the candidates.

### 1.1 Brain region becomes a major selection criterion

Human PFC is part of the cerebral cortex, but “mouse cortex” is not automatically equivalent to mouse PFC. A GEO record labeled only **cortex** may represent a large cortical mantle, a posterior region, or a mixed dissection. Unless the methods identify frontal, medial prefrontal, prelimbic, infralimbic, or anterior cingulate tissue, the result should be described as **cortical validation**, not **mouse PFC replication**.

### 1.2 Regional matching matters most for neurons

Neuronal identities and transcriptional programs depend strongly on cortical area, cortical layer, and projection target. Therefore:

- Human PFC excitatory neurons should preferably be compared with mouse frontal/mPFC excitatory neurons.
- A comparison with an unspecified mouse cortical excitatory population is useful but less exact.
- A comparison with hippocampal pyramidal neurons is cross-region support, not regional replication.

For microglia, astrocytes, oligodendrocytes, and vascular cells, broad stress, immune, lipid, and mitochondrial pathways may generalize more readily across regions. Region still matters, because local plaques, neurons, vessels, and pathology shape glial states.

### 1.3 GSE185063 becomes the leading regional/cell-type anchor

GSE185063 uses mouse cortex and true snRNA-seq with broad cell-type coverage. It is now the best candidate for asking **where in cortical tissue** an APOE-associated human PFC signal appears. It cannot test disease or a reliable sex interaction from the public metadata.

### 1.4 GSE241553 remains important, but its role becomes narrower

GSE241553 is cortical, sex-balanced, and single-cell, but it is a **conditional microglia/CAM APOE induction experiment**. It does not compare standard whole-animal APOE3 versus APOE4 genotypes across all brain cells. It should primarily support microglial mechanisms and downstream cortical responses under amyloid pathology.

### 1.5 GSE163857 remains the factorial anchor, not the regional anchor

GSE163857 directly contains APOE, sex, and disease factors, but it profiles sorted brain microglia by bulk RNA-seq and does not provide a PFC-specific dissection. It supplies strong **factor matching** and weak **regional matching**.

### 1.6 GSE143758 is secondary for a PFC project

The main all-cell GSE143758 atlas is hippocampal. Its small cortical component is astrocyte-focused and has only one sample in each age-by-genotype cell. It remains valuable for disease-associated astrocyte and age-related pathway support, but not as the primary validation of a human PFC result.

### 1.7 Correction to the earlier GSE127884/GSE127893 shorthand

The most relevant sex-by-amyloid arm is **GSE127892**, which profiles cortical and hippocampal microglia from female and male AppNL-G-F and control mice across ages. **GSE127884** is a different arm involving male APP/PS1, Apoe-null, and control genotypes at 18 months. Neither uses human APOE3/APOE4, and both expose cell/well GEO records that must not be counted as independent mice.

---

## 2. How regional evidence should be labeled

| Regional category | What the mouse tissue provides | Appropriate wording | Datasets in this audit |
|---|---|---|---|
| **Direct PFC/frontal** | Explicit frontal, medial prefrontal, prelimbic, infralimbic, or anterior cingulate dissection | “Regionally matched mouse frontal/PFC validation” | **None identified** with the required APOE/sex/AD single-cell design |
| **Cortical** | Cortex or cortical mantle, but not a defined PFC subdivision | “Cortical cross-species validation” | GSE185063, GSE241553, GSE140399 |
| **Mixed cortex + hippocampus** | Both regions used, possibly combined or incompletely separated | “Mixed cortical/hippocampal support” | GSE225503, GSE127892, GSE127884 |
| **Non-regional or broad brain** | Brain, whole brain, or a broad hemisphere preparation | “Brain-wide” or “non-region-specific cell-type support” | GSE163857, GSE140510, GSE212606, GSE212317 |
| **Hippocampal** | Hippocampus-specific data | “Cross-region pathway validation” | GSE143758 main atlas, GSE213446 |

> **Important:** A batch-correction method cannot convert hippocampus into PFC. Brain region is a biological difference, not merely a technical batch effect.

---

## 3. Evaluation criteria used in this report

| Criterion | Strong match | Partial match | Not matched |
|---|---|---|---|
| **Region** | Explicit mouse PFC/frontal cortex | Unspecified cortex; mixed cortex/hippocampus | Hippocampus, whole brain, or unclear region for a PFC claim |
| **APOE** | Human APOE3 vs APOE4 in the intended biological context | APOE4 combined with another risk allele; conditional cell-specific APOE; mouse Apoe manipulation | No APOE factor |
| **Sex** | Female and male labels for each independent mouse, with usable replication | Both sexes mentioned but mouse-level mapping missing; pooled sex groups | One sex only or sex unavailable |
| **Disease** | AD-model and matched non-AD controls within the same study | All animals have amyloid/tau pathology, or model differs from the human question | No disease factor |
| **Modality** | snRNA-seq or scRNA-seq with mouse identity | Bulk sorted cells; pooled single-cell libraries | No usable expression data |
| **Replication** | Independent mice per group | Mouse pooling, one library per condition, or very small groups | Cells/wells only with no recoverable animal unit |
| **Cell breadth** | Neurons, glia, and vascular populations | One compartment or glia-enriched data | One sorted cell type only |
| **Public usability** | Processed counts plus animal-level metadata | Counts available but metadata audit required | Key identities unavailable |

### Biological replicate rule

The independent biological unit is usually the **mouse**, not the cell, nucleus, well, hemisphere, or sequencing lane.

```text
3 mice × 5,000 microglia per mouse

Correct inferential sample size: n = 3 mice
Incorrect inferential sample size: n = 15,000 cells
```

Pooling two or three mice before sequencing does not create independent mouse-level profiles. It creates one pooled experimental profile.

---

## 4. Master comparison matrix

### 4.1 Core and near-core datasets

| Dataset | Tissue / PFC fit | Modality | APOE design | Sex | Disease contrast | True biological units | Cell-type breadth | Best use for this project | Main limitation |
|---|---|---|---|---|---|---|---|---|---|
| **GSE185063** | Cortex / cortical mantle; **good cortical, not explicit PFC** | snRNA-seq | Human APOE3 vs APOE4 KI | Paper reports both sexes, but public per-mouse sex map is unresolved | None | 16 samples; 4 mice per APOE-by-age group | Broad neurons, glia, OPCs, vascular cells | Main cortical cell-type localization of APOE-associated PFC modules | No AD model; cannot safely test sex without author metadata |
| **GSE241553** | Cortex; **good cortical, not explicit PFC** | scRNA-seq | Conditional human apoE3 or apoE4 induction in microglia/CAMs | 3F + 3M per group | All mice are amyloid-model; control vs tamoxifen is induction, not AD vs control | 24 mice; 6 per group | Multiple cortical populations; mechanistically strongest in microglia/CAMs | Cortical sex-aware APOE induction under amyloid; downstream cell communication | Not whole-animal APOE genotype; no non-amyloid group; n=3 per sex-by-group cell |
| **GSE163857** | Sorted brain microglia; **not PFC-specific** | Bulk RNA-seq | Human APOE3 vs APOE4 targeted replacement | Female and male | 5xFAD vs targeted-replacement control | 30 mouse samples; several controls n=1–3 | Microglia only | Direct APOE × sex × disease benchmark | Bulk; no regional localization; imbalanced and underpowered controls |
| **GSE140399** | Cortex and hippocampus separately; **cortical arm available** | snRNA-seq | No human APOE isoform; TREM2 factor | Not a usable study factor from GEO | 5xFAD vs WT, with/without Trem2 | 3 mice pooled into each region-by-genotype library | Broad | Descriptive cortical AD direction for neurons and glia | One pooled library per condition; ordinary inferential testing is invalid |
| **GSE140510** | Mouse brain; **not explicit cortex/PFC** | snRNA-seq | No human APOE isoform; TREM2 factor | Not a usable study factor | 5xFAD vs WT, with/without Trem2 | 12 independent mice; 3 per genotype | Broad | Replicated broad-cell AD-direction support | Regional mismatch; no APOE or sex factor |
| **GSE143758** | Main atlas hippocampus; four small cortex records | snRNA-seq | No human APOE isoform | Main study overwhelmingly male; only 2 females total | 5xFAD vs WT | Main 7-month atlas: 8 mice, 10 preparations; cortex: 4 mice total | Broad in 7-month hippocampus; cortex processed file is astrocyte-focused | Astrocyte, age, and cross-region AD support | Not PFC; no APOE; cortex subset has one mouse per age-by-genotype cell |

### 4.2 Specialized and lower-priority datasets

| Dataset | Tissue / PFC fit | Modality | APOE design | Sex | Disease contrast | Replication issue | Best use | Main limitation |
|---|---|---|---|---|---|---|---|---|
| **GSE225503 / GSE239999** | CD45+ cells from cortical and hippocampal regions; separation must be audited | scRNA-seq / multiome | Human APOE2, APOE3, APOE4 KI | Not exposed adequately in GEO | All mice are 5xFAD | GEO records are multiplexed experiment files; HTO metadata must recover mice | APOE2/3/4 immune aging, microglial states, chromatin | No non-AD group; immune only; sex unavailable; not PFC |
| **GSE127892** | Cortex and hippocampus | plate-based scRNA-seq of microglia | Mouse Apoe context; no human isoform comparison | Female and male | AppNL-G-F vs WT across ages | 2 mice per condition pooled; 32 condition pools | Sex-by-amyloid microglial trajectories | Pooling removes mouse-level replication; microglia only |
| **GSE212606** | Mouse brains; non-regional | EasySci single-cell RNA/ATAC | LOAD model combines APOE4 with TREM2 R47H; no clean APOE3 comparator | Both sexes | WT, 5xFAD, and APOE4/TREM2-R47H model | GEO has aggregate records; animal manifest required | Broad sex/disease/cell-type convergence; >300 subtypes | Cannot isolate APOE4 from TREM2; not cortex/PFC |
| **GSE213446** | Hippocampus | snRNA-seq | APOE3/APOE4 with/without P301S tauopathy | Sex-dependent biology reported, but public sample-level map absent | P301S tauopathy vs non-tau | One public library per listed condition; animals per library not auditable | APOE-by-tau cross-model pathway support | Hippocampus, not PFC; tau model; limited inferential replication |
| **GSE212317 / GSE213391** | Whole left hemispheres excluding brainstem/cerebellum | Glia-enriched scRNA-seq plus spatial/bulk resources | APOE3/APOE4; middle-age groups are 5xFAD | Female only | Age and amyloid comparisons are not a clean balanced factorial design | 3 mice pooled per scRNA group; one library per group | APOE immunometabolism and mitochondrial/lipid pathway support | Female only, pooled, non-regional, age/disease confounding |
| **GSE127884** | Cortex and hippocampus | plate-based single-cell microglial RNA-seq | Mouse Apoe-null vs mouse Apoe; no human E3/E4 | Male only | APP/PS1 vs controls at 18 months | Thousands of GEO records are cells/wells, not mice | Apoe dependence of amyloid-associated microglial states | No human isoform or sex comparison; animal replication not exposed cleanly |

---

## 5. Recommended tiered setup

### Tier 1 — Core public-data package

| Role | Dataset | Primary question answered |
|---|---|---|
| **Cortical APOE cell-type anchor** | GSE185063 | In which mouse cortical cell types does the human PFC APOE-associated module appear? |
| **Cortical mechanistic APOE-by-sex anchor under amyloid** | GSE241553 | Does inducing microglial/CAM apoE3 or apoE4 alter cortical cells differently in females and males under amyloid pathology? |
| **Direct factorial microglial anchor** | GSE163857 | Does APOE4 interact with sex and 5xFAD status in independently sampled mouse microglia? |

These three datasets should be analyzed separately. Their raw count matrices should **not** be merged into one integrated mouse atlas for differential-expression testing.

### Tier 2 — Add one disease-direction anchor selected by cell type

| Human PFC cell type | Recommended disease support | Reason |
|---|---|---|
| **Microglia** | GSE127892 and/or GSE140510 | Sex-by-amyloid microglial states in GSE127892; independent mouse replication and broad disease response in GSE140510 |
| **Astrocytes** | GSE140399 plus GSE143758 | Cortical disease direction from GSE140399; stronger astrocyte-state and age evidence from GSE143758 |
| **Excitatory / inhibitory neurons** | GSE140399 and GSE140510 | GSE140399 is cortical but pooled; GSE140510 is replicated but non-regional |
| **Oligodendrocytes / OPCs** | GSE140399, GSE140510, GSE212606 | Broad disease-related oligodendroglial states; interpret regional evidence separately |
| **Endothelial cells / pericytes** | GSE185063 for APOE; GSE140399 or GSE212606 for disease direction | Strong cortical vascular APOE localization, but no ideal matched cortical AD-control vascular cohort in the audited set |

### Tier 3 — Specialized questions

- Add **GSE225503/GSE239999** when APOE2 or very old 5xFAD microglial states are central.
- Add **GSE212606** when broad cell population shifts, rare cell types, or sex-consistent disease effects are needed.
- Add **GSE213446** for APOE-by-tau cross-model support.
- Add **GSE212317/GSE213391** for female APOE immunometabolism, glycolysis, TCA-cycle, and lipid-metabolism support.

### Minimal, preferred, and definitive configurations

| Configuration | Datasets | What can be claimed |
|---|---|---|
| **Minimal defensible** | GSE185063 + GSE241553 + GSE163857 | Triangulated cortical APOE localization, sex-aware microglial APOE induction under amyloid, and direct factorial microglial support |
| **Preferred public-data** | Minimal + one cell-type-specific disease anchor + optional APOE2 resource | Adds AD-direction support in the relevant cell type and region where possible |
| **Definitive new experiment** | New frontal/mPFC snRNA-seq cohort with APOE3/4 × sex × AD/control | Direct regionally matched cell-type-specific interaction testing |

---

## 6. Detailed dataset profiles

## 6.1 GSE185063 — broad cortical snRNA-seq APOE anchor

**Public record:** [GEO GSE185063](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE185063)  
**Associated paper:** [Barisano et al., Journal of Experimental Medicine, 2022](https://pubmed.ncbi.nlm.nih.gov/36040482/)  
**Processed-data format:** H5 files in a GEO tar archive; raw reads in SRA  
**Approximate GEO processed archive size at re-audit:** 579 MB

### Design

GSE185063 contains 10x single-nucleus RNA-seq from cortex of APOE3 and APOE4 knock-in flox/flox mice. The associated study compares two age ranges, approximately 2–3 months and 9–12 months, with four mice in each APOE-by-age group, for 16 mouse samples total.

| Factor | Levels / information |
|---|---|
| Tissue | Cortex; the publication describes cortical mantle sampling after removal of hippocampus and visible white matter |
| APOE | Human APOE3 versus APOE4 knock-in |
| Age | Approximately 2–3 months and 9–12 months |
| Sex | Both sexes were used in the broader study, but a trustworthy per-GSM sex map is not exposed clearly in GEO |
| AD model | None |
| Modality | snRNA-seq |
| Replication | Four mice per APOE-by-age group |
| Cell types | Excitatory and inhibitory neurons, astrocytes, microglia, oligodendrocytes, OPCs, endothelial cells, pericytes/vascular populations, and other cortical nuclei |

### Why it is highly valuable for human PFC validation

This is the best regional and cellular match among the APOE datasets in the audited set. Human PFC is cortex, and snRNA-seq is also well suited to frozen postmortem brain and captures neurons better than many dissociation-based scRNA-seq experiments. Therefore, it is the preferred dataset for asking whether a human PFC APOE-associated mitochondrial or cell-state module is present in corresponding mouse cortical cell classes.

Examples:

- Human PFC excitatory-neuron APOE4 module → mouse cortical excitatory neurons.
- Human PFC astrocyte mitochondrial module → mouse cortical astrocytes.
- Human PFC endothelial/pericyte APOE signal → mouse cortical vascular populations.
- Human PFC oligodendrocyte or OPC signal → corresponding mouse cortical populations.

### What it can test

A replicate-aware model can be fitted independently within each cell type:

```text
counts ~ APOE * age + batch
```

The APOE coefficient asks whether APOE4 differs from APOE3. The interaction asks whether the APOE difference changes with age.

A strong validation result would show that a frozen human PFC module:

1. is detectably expressed in the homologous mouse cortical cell type;
2. changes in the predicted APOE4-versus-APOE3 direction;
3. has a coherent pathway-level effect rather than relying on one gene;
4. is similar at both ages or changes in a biologically interpretable age-dependent way.

### What it cannot test

- It cannot estimate AD-model versus control effects because no AD model is included.
- It cannot establish an APOE-by-disease interaction.
- It should not be used for sex-specific claims until a verified per-mouse sex map is obtained.
- It is cortex, not explicitly mouse PFC.

### Critical metadata caution

The sample suffix **F** in names such as `E3F` or `E4F` denotes the floxed genotype, not female sex. Inferring sex from this suffix would misclassify the design.

### Recommended use

Treat GSE185063 as the **first dataset for broad cortical cell-type localization**, not as a complete disease-validation cohort. Request from the authors:

- sex of every GSM sample;
- sex balance within each APOE-by-age group;
- confirmation that each GSM corresponds to one independent mouse;
- exact cortical dissection boundaries.

---

## 6.2 GSE241553 — cortical microglia/CAM APOE induction with balanced sexes

**Public record:** [GEO GSE241553](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241553)  
**Associated paper:** [Liu et al., Nature Immunology, 2023; PMID 37857825](https://pubmed.ncbi.nlm.nih.gov/37857825/)  
**Processed-data format:** per-sample MTX/TSV matrices in a GEO tar archive; raw reads in SRA  
**Approximate processed archive size:** 335 MB

### What “with or without expressing apoE3 or apoE4” means

This is a conditional expression experiment. The mice carry an engineered human APOE3 or APOE4 cassette that can be turned on mainly in microglia and CNS-associated macrophages (CAMs) by tamoxifen. The non-induced controls carry the corresponding engineered line but do not have the human apoE cassette activated in the same way.

It is not a standard comparison in which every cell in one mouse is APOE3 and every cell in another mouse is APOE4.

### Four groups

| Group | Engineered line | Tamoxifen induction | Human apoE in microglia/CAMs | Female mice | Male mice | Total |
|---|---|---|---|---:|---:|---:|
| **E3-C** | APOE3 | No | Off / non-induced | 3 | 3 | 6 |
| **E3-T** | APOE3 | Yes | apoE3 induced | 3 | 3 | 6 |
| **E4-C** | APOE4 | No | Off / non-induced | 3 | 3 | 6 |
| **E4-T** | APOE4 | Yes | apoE4 induced | 3 | 3 | 6 |
| **Total** |  |  |  | **12** | **12** | **24** |

All four groups are amyloid-model mice. Therefore, `C` versus `T` is **control versus induction**, not non-AD versus AD.

### Tissue and modality

- Tissue is labeled **cortex**, not PFC.
- Cells were dissociated and analyzed by 10x scRNA-seq.
- The experiment includes multiple cortical populations, but the direct genetic perturbation is centered on microglia/CAMs.

### Best comparison

A simple E4-T versus E3-T comparison is informative but can be affected by baseline differences between the two engineered lines. A stronger isoform-specific analysis uses a difference-in-differences contrast:

```text
(E4-T - E4-C) - (E3-T - E3-C)
```

This asks whether turning on apoE4 changes the transcriptome differently from turning on apoE3 after accounting for each line's non-induced baseline.

To test sex differences, estimate that contrast separately in females and males, or fit:

```text
counts ~ sex * APOE_line * induction + batch
```

The three-way interaction asks whether the difference between apoE4 and apoE3 induction effects differs by sex.

### Statistical strength and weakness

The overall cohort contains 24 independent mice, which is excellent compared with many public single-cell mouse studies. However, a sex-by-line-by-induction cell contains only three mice. That is suitable for a planned, exploratory interaction analysis but not a high-powered genome-wide search for subtle three-way interactions.

Prioritize:

- pre-specified human-derived gene modules;
- effect sizes and confidence intervals;
- mouse-level pseudobulk;
- consistency across individual mice;
- a limited number of planned contrasts.

### Direct versus indirect interpretation

| Cell type | Interpretation of an effect |
|---|---|
| Microglia / CAMs | Most directly related to the induced apoE3/apoE4 perturbation |
| Astrocytes | Likely downstream response to altered microglial/CAM signaling |
| Oligodendrocytes / OPCs | Potential downstream intercellular effect |
| Endothelial / vascular cells | Potential downstream immune–vascular communication effect |
| Neurons | Indirect response; scRNA dissociation may also recover fewer neuronal cells than snRNA-seq |

### What it can support

Appropriate statement:

> A human PFC microglial module showed a concordant sex-aware response to microglia/CAM-specific apoE3 versus apoE4 induction in mouse cortex under amyloid pathology.

Inappropriate statements:

- “The full APOE-by-sex-by-AD interaction was replicated.”
- “The experiment compared healthy and AD mice.”
- “Every cortical cell carried APOE3 or APOE4.”
- “The human PFC finding was replicated specifically in mouse PFC.”

### Recommended use

Use GSE241553 as the **cortical mechanistic microglia/CAM APOE-by-sex anchor under amyloid**, especially for human microglial, immune, lipid-metabolism, mitochondrial-stress, antigen-presentation, or complement-related findings.

---

## 6.3 GSE163857 — direct APOE × sex × disease benchmark in sorted microglia

**Public record:** [GEO GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857)  
**Associated paper:** [Moser et al., 2021; PMID 34746703](https://pubmed.ncbi.nlm.nih.gov/34746703/)  
**Processed-data format:** mouse count matrix as compressed CSV; raw reads in SRA  
**Approximate processed mouse count-file size:** 1.9 MB

### Design

The mouse arm contains bulk RNA-seq of sorted microglia from human APOE targeted-replacement mice on either a non-5xFAD targeted-replacement background or a 5xFAD background. Female and male mice are included for APOE3 and APOE4.

This is the only audited candidate with all eight APOE-by-sex-by-disease cells.

### Exact mouse sample counts reconstructed from GEO names

| Sex | APOE | Background | Mouse samples |
|---|---|---|---:|
| Female | E3/E3 | Targeted-replacement control | 2 |
| Female | E3/E3 | 5xFAD | 5 |
| Female | E4/E4 | Targeted-replacement control | 2 |
| Female | E4/E4 | 5xFAD | 5 |
| Male | E3/E3 | Targeted-replacement control | 1 |
| Male | E3/E3 | 5xFAD | 7 |
| Male | E4/E4 | Targeted-replacement control | 3 |
| Male | E4/E4 | 5xFAD | 5 |
| **Total** |  |  | **30** |

### Why it is essential

It maps closely to four of the human project's sex-by-APOE AD-versus-control questions:

```text
Female E3: 5xFAD vs control
Female E4: 5xFAD vs control
Male E3:   5xFAD vs control
Male E4:   5xFAD vs control
```

It also permits direct estimation of:

- APOE effect within disease;
- sex effect within an APOE/disease stratum;
- APOE × disease;
- sex × disease;
- sex × APOE;
- sex × APOE × disease.

### Recommended model

```text
counts ~ sex * APOE * disease
```

Because several control cells contain only one to three mice, the full three-way interaction may be unstable. The most defensible strategy is:

1. fit the factorial model;
2. report the three-way estimate and uncertainty;
3. pre-specify the four AD-versus-control contrasts above;
4. report APOE4-versus-APOE3 within female 5xFAD and male 5xFAD separately;
5. emphasize effect size and confidence intervals rather than a binary significant/not-significant decision.

### Strengths

- Exact human APOE3/APOE4, sex, and disease-background factors.
- Independent mouse samples.
- Simple processed count matrix.
- Microglia directly match a major AD-relevant human PFC cell type.

### Limitations

- Bulk sorted microglia, not single-cell or single-nucleus data.
- No broad neurons, astrocytes, oligodendrocytes, OPCs, or vascular cells.
- Tissue is not explicitly PFC or cortex in the public design.
- Several control strata are extremely small.
- Targeted-replacement E3/E3 and E4/E4 mice differ from many human carrier groups, which often include heterozygotes.

### Recommended use

Use GSE163857 as the **direct factorial microglial benchmark**. It should not be the only validation dataset, but it is the strongest public test of the exact APOE-by-sex-by-disease question.

---

## 6.4 GSE140399 — cortical AD-direction reference with pooled mice

**Public record:** [GEO GSE140399](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140399)  
**Associated study:** [Zhou et al., Nature Medicine, 2020; PMID 31932797](https://pubmed.ncbi.nlm.nih.gov/31932797/)  
**Processed-data format:** MTX/TSV; raw reads in SRA  
**Approximate processed archive size:** 71 MB

### Design

This study profiles 15-month-old mouse cortex and hippocampus for four genotypes:

- WT;
- Trem2 knockout;
- 5xFAD;
- Trem2 knockout × 5xFAD.

It uses snRNA-seq and includes broad neural, glial, and vascular populations. The cortex and hippocampus are separate public libraries, which is valuable for regional interpretation.

### Critical pooling limitation

The GEO record states that cells from **three mice per genotype were pooled for sequencing**. For each region-by-genotype combination, there is one pooled library.

```text
3 mice pooled together
        ↓
1 cortex library

This is not n = 3 independent expression profiles.
For differential-expression inference, it is effectively one pool.
```

### What it can do

- Test whether a frozen human PFC pathway shifts in the same direction in 5xFAD cortex versus WT cortex.
- Localize disease-associated direction across cortical neurons and glial populations.
- Compare cortex and hippocampus descriptively.
- Evaluate whether a disease signal depends on TREM2, descriptively.

### What it cannot do reliably

- Ordinary mouse-level pseudobulk hypothesis testing.
- Estimate biological variability among mice within a genotype.
- Validate human APOE isoform or sex interactions.

### Recommended use

Use GSE140399 as a **descriptive cortical disease-direction anchor**. For example, if a human PFC astrocyte mitochondrial module is lower in AD, ask whether the same frozen module is directionally lower in the 5xFAD cortical astrocyte pool. Label the result “descriptive cortical concordance,” not independent replication.

---

## 6.5 GSE140510 — replicated broad-cell AD reference without a clear cortical label

**Public record:** [GEO GSE140510](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140510)  
**Associated study:** [Zhou et al., Nature Medicine, 2020; PMID 31932797](https://pubmed.ncbi.nlm.nih.gov/31932797/)  
**Processed-data format:** MTX/TSV; raw reads in SRA  
**Approximate processed archive size:** 704 MB

### Design

This seven-month snRNA-seq experiment contains 12 independently processed mice:

| Genotype | Independent mice |
|---|---:|
| WT | 3 |
| Trem2 knockout | 3 |
| 5xFAD | 3 |
| Trem2 knockout × 5xFAD | 3 |

The public GEO record explicitly states that three biologically independent mice per genotype were individually processed and sequenced.

### Strength compared with GSE140399

GSE140510 permits mouse-level pseudobulk and basic genotype comparisons because the mice are separately sequenced.

### Regional limitation

The public record describes nuclei from mouse brains and does not provide a clearly defined PFC or cortical dissection in the sample labels. Therefore, it offers stronger replication than GSE140399 but weaker regional matching to human PFC.

### Recommended model

For a simple disease comparison among Trem2-intact mice:

```text
counts ~ disease
```

using WT versus WT_5xFAD within each cell type.

For the complete genotype design:

```text
counts ~ disease * Trem2_status
```

### Recommended use

Use GSE140510 as a **replicated broad-cell AD-direction anchor** when inferential replication matters more than exact cortical localization. Keep its result separate from GSE140399 rather than combining them.

---

## 6.6 GSE143758 — hippocampal all-cell and astrocyte-focused disease/age reference

**Public record:** [GEO GSE143758](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758)  
**Associated paper:** [Habib et al., Nature Neuroscience, 2020; PMID 32341542](https://pubmed.ncbi.nlm.nih.gov/32341542/)  
**Processed-data format:** three compressed count matrices plus raw SRA data

### Why GEO lists 37 samples

The 37 GEO records span multiple ages, brain regions, technical preparations, and subexperiments. They are not 37 independent mice in one matched comparison.

### Main seven-month hippocampal atlas

| Quantity | Count |
|---|---:|
| Independent mice | 8 |
| WT mice | 4 |
| 5xFAD mice | 4 |
| Sequencing sample preparations | 10 |
| High-quality nuclei reported in the main atlas | Approximately 54,769 |
| Region | Hippocampus |
| Broad cell types | Yes |

The difference between 8 mice and 10 preparations arises because some hemisphere-derived preparations are repeated/technical samples. Statistical inference should retain the mouse as the biological unit.

### Broader age course

The study includes a larger astrocyte-focused age series across multiple age groups. It is useful for asking whether a disease-associated astrocyte or mitochondrial program emerges early and increases with age, but age strata are uneven and the oldest group is not fully matched.

### Female representation

Only two female mice were included in the entire study—one WT and one 5xFAD—while the main seven-month atlas was male. This is not sufficient for a formal sex-by-disease interaction.

### Cortical subset

The GEO series includes four cortical records:

| Age | WT cortex | 5xFAD cortex |
|---|---:|---:|
| 7 months | 1 | 1 |
| 10 months | 1 | 1 |

The public cortical processed file is astrocyte-focused. One mouse in each age-by-genotype cell is descriptive, not inferential.

### What it can support

- 5xFAD-versus-WT disease direction in the main hippocampal all-cell atlas.
- Disease-associated astrocyte state and pathway validation.
- Age progression of astrocyte programs.
- Cross-region support when a human PFC pathway is also altered in hippocampus.
- Descriptive cortical astrocyte consistency.

### What it cannot support

- Human APOE3-versus-APOE4 effects.
- A powered sex comparison.
- Broad cortical/PFC cell-type validation.
- A formal cortical disease comparison from the four-sample subset.

### Recommended use

Use GSE143758 as **secondary astrocyte and cross-region AD evidence**, especially for reactive astrocyte, lipid, stress, lysosomal, mitochondrial, and age-progressive modules. Do not present the main atlas as a mouse PFC dataset.

---

## 6.7 GSE225503 / GSE239999 — APOE2/APOE3/APOE4 immune-cell aging resource

**Public records:** [GSE225503](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225503) and [GSE239999](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE239999)  
**Associated paper:** [Millet et al., Immunity, 2024; PMID 38159571](https://pubmed.ncbi.nlm.nih.gov/38159571/)  
**Processed-data format:** large Seurat RDS objects, H5/TSV files, and raw SRA data  
**Approximate principal RDS sizes:** 1.5–2.5 GB each

### Design

The study isolates CD45-positive immune cells from hippocampal and cortical regions of 5xFAD mice carrying human APOE knock-in alleles. The public scRNA-seq/multiome subseries includes:

- APOE2, APOE3, and APOE4 at 10 weeks;
- APOE2, APOE3, and APOE4 at 20 weeks;
- APOE4 at 60 weeks in the first subseries;
- APOE3 and APOE4 at 96 weeks;
- additional 60-week uptake and treatment experiments in the SuperSeries;
- a separate bulk CD45-positive experiment with five replicates per APOE allele.

### Important interpretation of the eight GEO “samples”

The eight GSE225503 records are multiplexed experiment-level files such as scRNA-seq data and HTO demultiplexing data. They are not eight individual mice. Mouse-level identities may be encoded in HTO and Seurat metadata and must be reconstructed before replicate-aware analysis.

### Regional issue

The GEO description says cells came from **hippocampal and cortical regions**. Before making a cortical claim, inspect the processed object to determine whether:

- region is present as a cell- or mouse-level field;
- cortex and hippocampus were separately processed;
- regions were combined before sequencing;
- each mouse contributed both regions.

If region is not separable, the dataset should be described as mixed cortical/hippocampal immune-cell evidence.

### Strengths

- Only major candidate in this report with APOE2, APOE3, and APOE4 in an AD-model context.
- Multiple disease stages/ages.
- Immune and microglial state resolution.
- Multiome data can connect gene expression with chromatin accessibility.
- Particularly useful for exhausted-like or aging microglial states.

### Limitations

- All animals are 5xFAD; no non-AD background.
- CD45-positive enrichment excludes neurons and most nonimmune brain cells.
- Public sex information is insufficient for the desired interaction analysis.
- APOE alleles are not represented at every age in a balanced way.
- Mouse-level replication and region labels require a metadata audit.

### Recommended model after metadata recovery

If independent mouse identity, age, APOE, and region can be recovered:

```text
counts ~ APOE * age + region + batch
```

Sex should be added only when a verified mouse-level sex field exists.

### Recommended use

Use this dataset when the human PFC result involves:

- APOE2 protection or APOE2-versus-APOE3/E4 ordering;
- microglial aging;
- exhausted-like immune states;
- amyloid uptake;
- late-stage immune pathways;
- chromatin support for an expression signature.

Do not use it as the primary test of AD-versus-control or sex effects.

---

## 6.8 GSE127892 — sex-by-amyloid microglial trajectories in cortex and hippocampus

**Public record:** [GEO GSE127892](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127892)  
**Associated paper:** [Frigerio et al., Cell Reports, 2019; PMID 31018141](https://pubmed.ncbi.nlm.nih.gov/31018141/)  
**Modality:** plate-based single-cell RNA-seq of microglia

### Design

GSE127892 profiles microglia from cortex and hippocampus of female and male AppNL-G-F mice and age-matched controls at approximately 3, 6, 12, and 21 months.

The design contains 32 conditions:

```text
2 regions × 2 sexes × 2 disease backgrounds × 4 ages = 32 conditions
```

The GEO record states that two mice were used per condition and pooled. Thus, approximately 64 mice contributed overall, but the animals are not separately represented in the expression profiles.

### Why the GEO page lists 12,288 samples

The 12,288 GSM records correspond to cell/well measurements from the plate-based experiment. They do not represent 12,288 mice or 12,288 independently prepared biological samples.

### Strengths

- Explicit female and male design.
- Amyloid-model versus control comparison.
- Cortex and hippocampus.
- Multiple ages and disease stages.
- High value for microglial activation trajectories and sex differences.

### Limitations

- Two mice per condition were pooled.
- Microglia only.
- Uses endogenous mouse Apoe biology, not human APOE3/APOE4 isoforms.
- No independent mouse-level variance within each condition pool.

### Recommended use

Use GSE127892 to ask whether the direction of a human PFC microglial sex-by-AD module is consistent with sex-dependent amyloid-associated microglial state progression in mouse cortex. Treat findings as **condition-level descriptive support**, not as a replicated mouse-level interaction test.

---

## 6.9 GSE212606 — very broad sex-aware whole-brain AD atlas

**Public record:** [GEO GSE212606](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212606)  
**Associated paper:** [Sziraki et al., Nature Genetics, 2023; PMID 37774676](https://pubmed.ncbi.nlm.nih.gov/37774676/)  
**Processed-data archive:** approximately 12.8 GB plus supporting files

### Design

EasySci was used to profile approximately 1.5 million mouse single-cell transcriptomes and approximately 400,000 chromatin-accessibility profiles across ages, genotypes, and both sexes. The study includes:

- an early-onset 5xFAD model;
- a late-onset model combining APOE4 with TREM2 R47H;
- WT/reference animals;
- more than 300 reported cell subtypes.

### Strengths

- Exceptional breadth and rare-cell coverage.
- Both sexes.
- Multiple ages.
- Two AD-related models.
- RNA and ATAC modalities.
- Useful for broad cell-population shifts and consistency across males and females.

### Limitations for this project

- Brain-wide, not PFC or cortex-specific.
- The late-onset model combines APOE4 with TREM2 R47H, so an observed difference cannot be attributed to APOE4 alone.
- There is no clean APOE3 comparator for the LOAD model.
- GEO exposes aggregate records; an animal-level manifest is needed for pseudobulk.
- The scale and complexity make it a high-workload dataset.

### Recommended use

Use GSE212606 for:

- broad sex-by-disease cell-type convergence;
- rare cell population changes;
- checking whether a mitochondrial or stress pathway appears across many brain cell classes;
- complementary chromatin evidence.

Do not use it as a direct APOE3-versus-APOE4 validation dataset.

---

## 6.10 GSE213446 — hippocampal APOE-by-tau snRNA-seq

**Public record:** [GEO GSE213446](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213446)  
**Processed-data format:** MTX/TSV archive; raw reads in SRA  
**Approximate processed archive size:** 2.0 GB

### Design

The public series contains ten hippocampal snRNA-seq libraries from 9-month-old mice across:

- APOE3 and APOE4 without P301S;
- P301S-APOE3, P301S-APOE4, and P301S-APOE knockout;
- water versus antibiotic treatment.

The associated biological study reports sex- and APOE-dependent responses to microbiome perturbation, tau pathology, gliosis, and neurodegeneration. However, the GEO series does not provide a reliable per-library sex map or transparent mouse count per library.

### Strengths

- True snRNA-seq.
- Human APOE3/APOE4.
- Tauopathy versus non-tau backgrounds.
- Broad hippocampal cell types.
- Useful for testing whether an APOE-associated pathway generalizes from amyloid to tau-driven pathology.

### Limitations

- Hippocampus, not PFC.
- P301S tauopathy is not equivalent to 5xFAD amyloid pathology or human late-onset AD.
- One public library is listed per condition.
- Mouse-level replication and sex cannot be reconstructed from the GEO series page alone.
- Antibiotic treatment introduces another biological factor.

### Recommended use

Use GSE213446 only as **cross-region, cross-pathology APOE support**, preferably at the pathway/module level. Obtain animal-level metadata before any inferential claim.

---

## 6.11 GSE212317 / GSE213391 — female APOE immunometabolism resource

**Public records:** [GSE212317](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212317) and [GSE213391](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213391)  
**Associated paper:** [Farmer et al., 2023; PMID 36871219](https://pubmed.ncbi.nlm.nih.gov/36871219/)

### Design

The scRNA-seq subseries includes six glia-enriched libraries:

- APOE3 young;
- APOE3 middle;
- APOE3 aged;
- APOE4 young;
- APOE4 middle;
- APOE4 aged.

The GEO design states that the mice were female. The middle-age APOE3 and APOE4 groups are 5xFAD, while the young and aged comparison groups represent different age/pathology contexts. Each scRNA-seq library was generated from pooled brain tissue from three mice, using whole left hemispheres excluding brainstem and cerebellum.

### Strengths

- Direct emphasis on APOE-dependent microglial immunometabolism.
- Strong relevance to glycolysis, TCA cycle, lipid metabolism, and inflammatory metabolism.
- APOE3 versus APOE4.
- Single-cell, spatial transcriptomic, and bulk components in the SuperSeries.

### Limitations

- Female only; no sex comparison.
- Three mice pooled per scRNA-seq group, leaving one library per group.
- Non-regional broad-hemisphere preparation.
- Age and amyloid status are not arranged as a clean balanced factorial design.
- Glia-enriched rather than broad neuronal coverage.

### Recommended use

Use it as **descriptive mechanistic support for female APOE immunometabolism**, especially when the human PFC result involves microglial glycolysis, TCA-cycle disruption, HIF1A-related programs, or lipid handling. Do not use it to estimate a sex interaction or a clean APOE-by-disease interaction.

---

## 6.12 GSE127884 — mouse Apoe dependence of amyloid microglial states

**Public record:** [GEO GSE127884](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127884)  
**Associated study:** [Frigerio et al., Cell Reports, 2019; PMID 31018141](https://pubmed.ncbi.nlm.nih.gov/31018141/)

### Design

This arm profiles cortical and hippocampal microglia from 18-month-old male mice in four conditions:

- APP/PS1 with mouse Apoe;
- APP/PS1 with Apoe knockout;
- C57BL/6 control;
- C57BL/6 with Apoe knockout.

The GEO page lists 3,072 samples because individual cells/wells are registered as GSM records.

### What it contributes

It asks whether endogenous mouse Apoe is required for amyloid-associated microglial activation states. This is biologically relevant to APOE mechanisms, but it does not compare human APOE3 with APOE4.

### Limitations

- Male only.
- Mouse Apoe presence/absence, not human isoforms.
- Microglia only.
- Animal-level replication cannot be inferred from the number of GEO records.
- Cortex and hippocampus are not PFC-specific.

### Recommended use

Use only as mechanistic support for **Apoe dependence** of amyloid-associated microglial states, not as validation of human APOE isoform or sex findings.

---

## 7. How the datasets map to the human PFC comparison groups

The human project contains sex- and APOE-stratified AD-versus-control comparisons. A useful shorthand is:

- `F_e2x`: female APOE ε2 carrier group;
- `F_e33`: female APOE ε3/ε3;
- `F_e4x`: female APOE ε4 carrier group;
- `M_e2x`: male APOE ε2 carrier group;
- `M_e33`: male APOE ε3/ε3;
- `M_e4x`: male APOE ε4 carrier group.

The mouse datasets do not reproduce all six human strata. The table below shows the closest mapping.

| Human PFC question | Closest mouse dataset | Closest mouse contrast | What is missing or different |
|---|---|---|---|
| Female ε3/ε3: AD vs control | GSE163857 | Female E3/E3 5xFAD vs female E3/E3 targeted-replacement control | Bulk brain microglia; not PFC; mouse amyloid model |
| Female ε4 carrier: AD vs control | GSE163857 | Female E4/E4 5xFAD vs female E4/E4 targeted-replacement control | Mouse is homozygous E4/E4; many human carriers are heterozygous |
| Male ε3/ε3: AD vs control | GSE163857 | Male E3/E3 5xFAD vs male E3/E3 control | Only one male E3 control mouse |
| Male ε4 carrier: AD vs control | GSE163857 | Male E4/E4 5xFAD vs male E4/E4 control | Bulk, non-regional, homozygous E4/E4 |
| Female or male ε2 carrier: AD vs control | No exact public candidate | GSE225503 supplies APOE2 under 5xFAD but no non-AD or usable sex factor | Cannot estimate ε2-by-sex AD-control interaction |
| APOE4 vs APOE3 in cortex | GSE185063 | E4 vs E3 by age and cortical cell type | No AD model; sex map unresolved |
| APOE4 vs APOE3 under amyloid with sex | GSE241553 | Difference-in-differences of E4 vs E3 induction, separately by sex | Conditional microglia/CAM perturbation; no non-amyloid group |
| Sex-by-amyloid microglial response | GSE127892 | Female vs male AppNL-G-F/WT condition patterns | Mouse Apoe, pooled mice, no human isoform |
| Broad AD cell-type direction | GSE140399 or GSE140510 | 5xFAD vs WT in homologous cell types | No APOE/sex; regional/replication trade-off |

### Human carrier groups versus mouse homozygous lines

A human ε4-carrier group may include ε3/ε4 and sometimes ε2/ε4 individuals, while many mouse experiments use E4/E4 targeted-replacement or knock-in animals. Similarly, a human ε2-carrier group may be heterogeneous. Therefore:

- compare direction and pathway coherence, not only absolute effect size;
- document human genotype composition;
- avoid describing a homozygous mouse E4/E4 contrast as identical to a human “ε4 carrier” contrast;
- consider sensitivity analyses restricted to human ε3/ε4 when sample size permits.

---

## 8. Recommended analysis plan

## 8.1 Freeze the human PFC result first

Before examining mouse outcomes, define and save:

- human cell type or cluster;
- contrast, such as `F_e4x AD vs NCI`;
- effect direction;
- gene list or ranked statistics;
- mitochondrial pathway/module definition;
- inclusion threshold;
- intended primary mouse dataset and contrast.

This prevents changing the gene set after seeing the mouse result.

## 8.2 Convert human genes to mouse orthologs

An ortholog is a corresponding gene in another species. Use a versioned mapping source and retain:

| Human gene | Mouse ortholog | Mapping type | Keep? | Reason |
|---|---|---|---|---|
| APOE | Apoe | One-to-one | Yes | Clear ortholog |
| Example gene | Multiple mouse genes | One-to-many | Usually separate sensitivity analysis | Ambiguous correspondence |
| Human-specific gene | None | No ortholog | No | Cannot test directly in mouse |

Prefer one-to-one orthologs for the primary analysis. Report how many genes were mapped, lost, or ambiguous.

## 8.3 Analyze every study separately

Do not merge count matrices from different studies and then fit one differential-expression model. The studies differ in:

- brain region;
- disease model;
- age;
- sex balance;
- APOE engineering strategy;
- scRNA-seq versus snRNA-seq versus bulk;
- cell isolation;
- laboratory and sequencing platform.

Instead, estimate a separate effect in each dataset and compare the **direction, magnitude, and pathway enrichment** across studies.

## 8.4 Use mouse-level pseudobulk when possible

For each study, cell type, and mouse:

```text
all counts from one mouse's microglia
                  ↓ sum
one microglial count vector for that mouse
```

Then use DESeq2, edgeR, limma-voom, or another replicate-aware method. Set a minimum cell/nucleus count per mouse-cell-type combination before creating pseudobulk profiles.

## 8.5 Recommended models and contrasts

| Dataset | Primary model or comparison | Inferential status |
|---|---|---|
| **GSE185063** | `counts ~ APOE * age + batch` by cell type | Strong, with 4 mice/group; add sex only after verified map |
| **GSE241553** | `counts ~ sex * APOE_line * induction + batch`; focus on `(E4T-E4C)-(E3T-E3C)` | Replicate-aware but three mice per sex-by-group cell; interactions exploratory |
| **GSE163857** | `counts ~ sex * APOE * disease`; pre-specify four sex/APOE-specific disease contrasts | Direct but control cells are small/imbalanced |
| **GSE140399** | 5xFAD cortical pool vs WT cortical pool | Descriptive only; no ordinary inferential P values |
| **GSE140510** | `counts ~ disease * Trem2_status` by cell type | Replicate-aware, n=3/genotype |
| **GSE143758 main** | 7-month hippocampal 5xFAD vs WT, mouse-level pseudobulk | Replicate-aware for main atlas; not sex/APOE/PFC |
| **GSE143758 cortex** | 5xFAD vs WT direction within age | Descriptive only; one mouse per cell |
| **GSE225503** | `counts ~ APOE * age + region + batch` after recovering HTO mouse identity | Depends on metadata recovery |
| **GSE127892** | Condition-level sex/amyloid/age direction | Descriptive because mice were pooled |
| **GSE212606** | `counts ~ sex * disease_model * age + batch` after animal manifest recovery | Potentially strong but complex and non-regional |
| **GSE213446** | Module direction across APOE/tau/treatment libraries | Descriptive until animal-level replication is documented |
| **GSE212317** | APOE3 vs APOE4 within matched age/pathology context | Descriptive; pooled female-only libraries |

## 8.6 Prefer module and ranked-list validation over exact DEG overlap

Exact overlap of individually significant genes is often small because of species, modality, region, age, and sample-size differences. More robust validation endpoints include:

1. **Module score direction:** Is a frozen mitochondrial module higher or lower in the predicted group?
2. **Ranked gene-set enrichment:** Are human-up genes enriched near the top of the mouse ranked list?
3. **Effect-size concordance:** Are ortholog log-fold changes positively correlated?
4. **Sign concordance:** What fraction of mapped genes changes in the same direction?
5. **Pathway concordance:** Are oxidative phosphorylation, mitochondrial translation, lipid metabolism, mitophagy, stress, or inflammatory pathways concordant?
6. **Cell-type localization:** Does the signal appear in the homologous mouse cell type rather than only in bulk composition?

## 8.7 Pre-specify evidence strength

| Evidence level | Example |
|---|---|
| **Level A: strong** | Same directional effect in a homologous cortical cell type with independent mice, plus direct factorial support in GSE163857 |
| **Level B: moderate** | Same cortical cell-type pathway direction, but one factor such as disease or sex is missing |
| **Level C: supportive** | Same pathway in a non-regional or hippocampal dataset with independent mice |
| **Level D: descriptive** | Same direction in a pooled or one-library-per-condition study |
| **Not supported** | Opposite effect in multiple well-matched datasets, or no detectable expression in the homologous cell type |

---

## 9. Mitochondrial validation considerations

The project is particularly interested in mitochondrial biology. Several technical and biological issues affect interpretation.

### 9.1 snRNA-seq is not an ideal assay for mitochondrially encoded RNA

Nuclei contain less mature cytoplasmic RNA than whole cells. Mitochondrial-genome transcripts are usually sparse in snRNA-seq and are often used as a quality-control signal rather than a complete biological readout.

For cross-species snRNA-seq validation, prioritize:

- nuclear-encoded oxidative-phosphorylation genes;
- mitochondrial ribosomal proteins;
- mitochondrial protein import;
- TCA-cycle enzymes;
- fatty-acid oxidation;
- mitochondrial dynamics and quality control;
- mitophagy;
- redox and oxidative-stress pathways;
- lipid handling and immunometabolism.

Do not interpret failure to reproduce an mtDNA-encoded transcript signal in nuclei as strong biological evidence against the human result.

### 9.2 scRNA-seq and snRNA-seq measure different RNA compartments

A pathway may appear stronger in GSE241553 scRNA-seq than in GSE185063 snRNA-seq because whole-cell data contain more cytoplasmic RNA. Compare direction and pathway enrichment, not raw module-score magnitude across modalities.

### 9.3 Cell-state changes can alter mitochondrial signals

A lower oxidative-phosphorylation module may reflect:

- a true metabolic shift;
- activation or stress state;
- changes in cell subtype composition;
- lower RNA complexity;
- cell damage or dissociation effects;
- disease-associated replacement of one state by another.

Therefore, analyze both:

1. **within-state expression changes**, and
2. **changes in the abundance of cell states**.

### 9.4 Suggested mitochondrial module set

Use a small number of frozen, non-overlapping or minimally overlapping modules:

| Module | Example biological interpretation |
|---|---|
| OXPHOS complexes I–V | Electron transport and ATP production |
| TCA cycle | Central mitochondrial carbon metabolism |
| Mitochondrial translation | Mitochondrial ribosome and protein synthesis |
| Mitophagy / quality control | Removal of damaged mitochondria |
| Fusion / fission | Mitochondrial dynamics |
| ROS defense | Oxidative-stress handling |
| Fatty-acid oxidation | Lipid-derived mitochondrial energy |
| Glycolysis | Non-mitochondrial energy shift, useful as a contrast |
| Lipid / cholesterol handling | Highly relevant to APOE and microglia |

Record the exact gene members and versions. Do not redefine a module separately for each mouse dataset.

---

## 10. Recommended dataset combinations by human PFC cell type

## 10.1 Microglia

Microglia have the strongest public-data setup.

```text
Human PFC microglial result
        │
        ├── GSE185063: cortical APOE3 vs APOE4 localization
        ├── GSE241553: cortical microglia/CAM APOE induction × sex under amyloid
        ├── GSE163857: direct APOE × sex × 5xFAD/control test
        ├── GSE127892: sex × amyloid state trajectory, descriptive
        └── GSE225503: APOE2/3/4 aging states, optional
```

**Recommended minimum:** GSE185063 + GSE241553 + GSE163857.  
**Best optional additions:** GSE127892 for sex/amyloid trajectories and GSE225503 for APOE2.

## 10.2 Astrocytes

```text
Human PFC astrocyte result
        │
        ├── GSE185063: cortical APOE localization
        ├── GSE140399: cortical 5xFAD direction, descriptive
        ├── GSE140510: replicated broad-brain disease direction
        └── GSE143758: disease-associated astrocyte and age support
```

GSE241553 may show astrocyte responses, but these are likely downstream of microglial/CAM APOE induction and should be labeled accordingly.

## 10.3 Excitatory and inhibitory neurons

```text
Human PFC neuronal result
        │
        ├── GSE185063: best cortical APOE reference
        ├── GSE140399: cortical disease direction, pooled/descriptive
        ├── GSE140510: replicated disease direction, non-regional
        └── GSE212606: broad disease/sex population support
```

Avoid treating hippocampal neurons in GSE143758 or GSE213446 as equivalent to PFC cortical neurons. Use them only for cross-region pathway support.

## 10.4 Oligodendrocytes and OPCs

Use GSE185063 for cortical APOE effects and GSE140399/GSE140510 for disease direction. GSE212606 can add rare-state and population-level context.

## 10.5 Endothelial cells and pericytes

GSE185063 is particularly strong for cortical vascular APOE biology. The current public set lacks an equally strong, replicated, cortex-specific APOE-by-sex-by-AD vascular cohort. Disease support from GSE140399 or GSE212606 should be labeled as partial.

---

## 11. Practical data-access comparison

| Dataset | Processed public data | Raw data | Approximate workload | Main preparation task |
|---|---|---|---|---|
| **GSE163857** | Compressed CSV count matrix | SRA | Low | Reconstruct 30 mouse groups from sample names |
| **GSE241553** | Per-sample MTX/TSV | SRA | Moderate | Build 24-mouse metadata; annotate cell types; pseudobulk |
| **GSE185063** | H5 files | SRA | Moderate | Combine 16 mice; verify age and request sex map |
| **GSE140399** | MTX/TSV | SRA | Low–moderate | Keep cortex/hippocampus separate; mark pools |
| **GSE140510** | MTX/TSV | SRA | Moderate | Build mouse-level object and cell-type pseudobulk |
| **GSE143758** | Three count matrices | SRA | Moderate | Separate main atlas, age course, and cortex subset; reconstruct mouse IDs |
| **GSE225503** | Large Seurat RDS and multiome objects | SRA | High | Recover HTO mouse identity, region, APOE, age, sex if available |
| **GSE127892** | Cell/well records and processed data | Public sequence data | High | Reconstruct condition pools; do not treat wells as mice |
| **GSE212606** | Very large processed archive | SRA | Very high | Obtain animal manifest and subset relevant cell types |
| **GSE213446** | MTX/TSV | SRA | Moderate | Determine mice per library and sex from authors/supplements |
| **GSE212317** | MTX/TSV | SRA | Moderate | Mark one pooled female library per group |

### Suggested download order

1. **GSE163857** — fastest direct-factor result.
2. **GSE185063** — broad cortical cell localization.
3. **GSE241553** — cortical microglial mechanism and sex analysis.
4. One selected AD-direction dataset according to the human cell type.
5. Specialized datasets only after the core results identify a specific unresolved question.

---

## 12. Metadata audit checklist

Before statistical analysis, create one row per independent mouse or pool with the fields below.

| Field | Why it matters |
|---|---|
| `dataset` | Keeps studies separate |
| `GSM` / library ID | Links analysis to public record |
| `mouse_id` | Defines the biological replicate |
| `pool_id` | Prevents pooled mice from being treated as independent |
| `sex` | Required for sex effects |
| `APOE_model` | E3/E4 targeted replacement, conditional induction, APOE4/TREM2, mouse Apoe-null, etc. are different |
| `APOE_state` | E2, E3, E4, off/on, or unavailable |
| `disease_model` | 5xFAD, AppNL-G-F, APP/PS1, P301S, or control |
| `age` | Disease stage and age are major confounders |
| `region` | PFC, cortex, hippocampus, mixed, or whole brain |
| `hemisphere` | Repeated hemispheres from one mouse are not independent animals |
| `treatment` | Tamoxifen, antibiotic, antibody, or other intervention |
| `library_batch` | Technical adjustment |
| `cell_type_original` | Preserves study labels |
| `cell_type_harmonized` | Enables broad cross-study comparison |
| `n_cells_or_nuclei` | Supports minimum-count filters |
| `data_modality` | Bulk, scRNA, snRNA, multiome |
| `inference_allowed` | Yes, descriptive only, or unresolved |

### Required author contacts or supplementary-data checks

- **GSE185063:** mouse-level sex map and exact cortical boundaries.
- **GSE241553:** confirm all model components used for the scRNA cohort and any batch variable not exposed in GEO.
- **GSE225503:** HTO-to-mouse map, region field, sex, and number of mice per age/allele.
- **GSE212606:** animal-level manifest connecting cells to mouse, sex, age, genotype, and batch.
- **GSE213446:** number and sex of mice contributing to every library.
- **GSE143758:** mouse-to-library and hemisphere mapping, especially for the 10 preparations in the 8-mouse main atlas.

---

## 13. Claims that are supported versus claims to avoid

| Evidence obtained | Safe wording | Wording to avoid |
|---|---|---|
| Human PFC and GSE185063 same cell-type APOE direction | “Cortical cross-species APOE concordance” | “Direct mouse PFC replication” |
| GSE241553 difference-in-differences consistent with human microglia | “Concordant microglia/CAM-specific APOE induction response under amyloid” | “Whole-brain APOE genotype effect” |
| GSE163857 three-way pattern consistent | “Factorial microglial support for APOE-by-sex-by-disease interaction” | “PFC-specific interaction replication” |
| GSE140399 pooled cortical direction consistent | “Descriptive cortical concordance” | “Statistically replicated in three mice per group” |
| GSE143758 hippocampal astrocyte pathway consistent | “Cross-region astrocyte pathway support” | “Mouse cortical/PFC validation” |
| GSE225503 APOE2 ordering consistent | “APOE2/3/4 immune-cell support under 5xFAD” | “APOE2-by-sex AD-control interaction” |
| Multiple separate studies show consistent modules | “Triangulated external validation” or “convergent support” | “One integrated mouse replication cohort” |

---

## 14. Major risks and how to control them

| Risk | Why it can mislead | Control |
|---|---|---|
| **Pseudoreplication** | Thousands of cells can create artificially small P values | Use mouse-level pseudobulk or replicate-aware models |
| **Pool inflation** | Two or three pooled mice look like several animals but provide one expression profile | Mark the pool as one inferential unit; descriptive analysis only when there is one pool/group |
| **Region substitution** | Hippocampal biology may differ from PFC | Label regional evidence explicitly; prioritize cortex for neurons |
| **APOE model substitution** | Conditional microglial APOE, whole-animal targeted replacement, APOE4/TREM2, and Apoe knockout answer different questions | Preserve model-specific interpretation |
| **Disease-model substitution** | 5xFAD, AppNL-G-F, APP/PS1, and P301S capture different pathologies | Report model separately; do not call them interchangeable AD replicates |
| **Carrier versus homozygous mismatch** | Human ε4 carriers may be E3/E4; mice may be E4/E4 | Focus on effect direction and pathway-level support; document dosage |
| **scRNA versus snRNA mismatch** | Cytoplasmic and nuclear RNA recovery differ | Compare ranked effects/modules, not raw expression magnitude |
| **Cell-composition confounding** | A module shift may arise from more of one cell state | Analyze expression and state abundance separately |
| **Underpowered interactions** | Three-way interaction estimates can be unstable | Pre-specify contrasts, report confidence intervals, avoid “no effect” claims from nonsignificance |
| **Post-selection** | Choosing genes after inspecting mouse results weakens independence | Freeze human modules and planned tests first |
| **Cross-study merging** | Laboratory, region, model, and disease become inseparable | Analyze separately and combine only effect summaries |

---

## 15. Suggested figures for the eventual validation paper

### Figure 1 — Dataset coverage matrix

Rows: datasets. Columns: PFC/cortex, APOE2/3/4, sex, disease control, modality, independent mice, cell types. Use direct/partial/absent symbols.

### Figure 2 — Human-to-mouse evidence map

```text
Human PFC discovery
      │
      ├── GSE185063: cortical cell-type APOE localization
      ├── GSE241553: cortical microglia/CAM APOE induction × sex under amyloid
      ├── GSE163857: direct APOE × sex × disease in microglia
      └── cell-type disease anchor: GSE140399 / GSE140510 / GSE143758 / GSE127892
```

### Figure 3 — Forest plot of planned module effects

For each dataset, show:

- estimated module difference;
- 95% confidence interval when valid;
- region;
- cell type;
- design label such as “factorial,” “cortical partial,” or “descriptive pool.”

### Figure 4 — Cell-type concordance heatmap

Rows: frozen human PFC modules.  
Columns: mouse dataset × cell type × contrast.  
Color: signed enrichment score or standardized module effect.

### Figure 5 — Interaction plot for GSE241553

Plot E3-C, E3-T, E4-C, and E4-T separately for female and male mice. Show one point per mouse and the difference-in-differences estimate.

### Figure 6 — GSE163857 factorial contrasts

Plot four disease effects:

- female E3 5xFAD vs control;
- female E4 5xFAD vs control;
- male E3 5xFAD vs control;
- male E4 5xFAD vs control.

This is more interpretable than presenting only one three-way-interaction P value.

---

## 16. Definitive new mouse experiment, if public data are insufficient

A direct test would require a new cohort with:

| Factor | Levels |
|---|---|
| APOE | Humanized APOE3 and APOE4 |
| Sex | Female and male |
| Disease | AD model and matched non-AD control |
| Region | Clearly defined frontal or medial prefrontal cortex |
| Modality | snRNA-seq to retain neurons, glia, and vascular cells |
| Biological unit | One independent library or recoverable multiplexed identity per mouse |

This creates eight groups:

```text
2 APOE × 2 sex × 2 disease = 8 groups
```

A planning target of 6–8 mice per group would require 48–64 mice before accounting for attrition and quality-control failures. A formal power simulation should use pilot mouse-level module variance and expected cell recovery.

Design requirements:

- same age and pathology stage across all groups;
- randomized nuclei isolation and library preparation;
- every batch contains multiple APOE, sex, and disease groups;
- exact dissection coordinates recorded;
- no pooling that loses mouse identity;
- sufficient nuclei per priority cell type;
- adjacent tissue retained for amyloid, tau, gliosis, vascular, and protein validation;
- frozen human gene modules and contrasts registered before mouse analysis.

---

## 17. Final recommendation

### Recommended core

1. **GSE185063** — first for cortical cell-type localization of APOE-associated human PFC modules.
2. **GSE241553** — second for sex-aware, microglia/CAM-specific apoE3/apoE4 induction effects in cortex under amyloid pathology.
3. **GSE163857** — third for the direct APOE-by-sex-by-disease microglial benchmark.

### Add one disease-direction dataset based on the human cell type

- Microglia: GSE127892 and/or GSE140510.
- Astrocytes: GSE140399 plus GSE143758.
- Neurons: GSE140399 plus GSE140510; optionally GSE212606.
- Oligodendrocytes/OPCs: GSE140399/GSE140510 and GSE212606.
- Vascular cells: GSE185063 for APOE, with partial disease support from GSE140399 or GSE212606.

### Specialized additions

- APOE2: GSE225503/GSE239999.
- Tau cross-model support: GSE213446.
- Female microglial immunometabolism: GSE212317/GSE213391.
- Apoe-dependence of amyloid microglial activation: GSE127884.

### Publication framing

The scientifically defensible conclusion is not that one mouse dataset replicates the complete human PFC result. It is that **multiple mouse studies provide complementary, convergent evidence across region, cell type, APOE context, sex, and disease model**.

A suitable methods statement would be:

> We performed triangulated external validation using independent public mouse datasets selected for complementary design strengths. Cortical APOE-associated cell-type localization was evaluated in GSE185063; sex-aware microglia/CAM-specific APOE induction under amyloid pathology was evaluated in GSE241553; and the complete APOE-by-sex-by-disease factorial pattern was evaluated in sorted microglia from GSE163857. Additional datasets were used only for pre-specified disease, age, APOE2, or cross-region pathway questions. Each study was analyzed separately at the mouse or pool level, and evidence was combined through effect-direction and gene-set concordance rather than raw-expression integration.

---

## 18. Primary public resources

1. **GSE185063** — cortical APOE3/APOE4 snRNA-seq: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE185063) · [PubMed 36040482](https://pubmed.ncbi.nlm.nih.gov/36040482/)
2. **GSE241553** — cortical microglia/CAM conditional APOE3/APOE4 scRNA-seq: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241553) · [PubMed 37857825](https://pubmed.ncbi.nlm.nih.gov/37857825/)
3. **GSE163857** — APOE × sex × 5xFAD/control bulk sorted microglia: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857) · [PubMed 34746703](https://pubmed.ncbi.nlm.nih.gov/34746703/)
4. **GSE140399** — 15-month cortex/hippocampus 5xFAD/Trem2 snRNA-seq, pooled mice: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140399) · [PubMed 31932797](https://pubmed.ncbi.nlm.nih.gov/31932797/)
5. **GSE140510** — 7-month replicated 5xFAD/Trem2 snRNA-seq: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140510) · [PubMed 31932797](https://pubmed.ncbi.nlm.nih.gov/31932797/)
6. **GSE143758** — 5xFAD/WT hippocampal and astrocyte snRNA-seq: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758) · [PubMed 32341542](https://pubmed.ncbi.nlm.nih.gov/32341542/)
7. **GSE225503 / GSE239999** — APOE2/3/4 5xFAD brain immune scRNA/multiome: [GSE225503](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225503) · [GSE239999](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE239999) · [PubMed 38159571](https://pubmed.ncbi.nlm.nih.gov/38159571/)
8. **GSE127892** — female/male AppNL-G-F/WT cortical and hippocampal microglia: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127892) · [PubMed 31018141](https://pubmed.ncbi.nlm.nih.gov/31018141/)
9. **GSE127884** — APP/PS1 and Apoe-null microglia: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127884) · [PubMed 31018141](https://pubmed.ncbi.nlm.nih.gov/31018141/)
10. **GSE212606** — EasySci whole-brain aging and AD atlas: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212606) · [PubMed 37774676](https://pubmed.ncbi.nlm.nih.gov/37774676/)
11. **GSE213446** — APOE/tau hippocampal snRNA-seq: [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213446)
12. **GSE212317 / GSE213391** — APOE immunometabolism: [GSE212317](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212317) · [GSE213391](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213391) · [PubMed 36871219](https://pubmed.ncbi.nlm.nih.gov/36871219/)

---

## 19. Search and interpretation limitations

- This report prioritizes public studies whose design can be audited from GEO/SRA and linked primary papers.
- “No exact dataset identified” does not prove that no unpublished, controlled-access, or incompletely indexed cohort exists.
- GEO “Samples” can mean mice, pooled libraries, experiment-level multiplexes, or individual cells/wells. The meaning was evaluated separately for each accession.
- Some per-mouse metadata remain unavailable publicly and require author contact or inspection of processed-object metadata.
- Mouse PFC is not a perfect one-to-one anatomical equivalent of human PFC. Even an explicit mouse mPFC cohort would still require cautious cross-species interpretation.
- The report assesses dataset suitability; it does not report newly calculated biological results from the count matrices.

**Search conclusion as of August 23, 2026:** within the openly auditable public candidate set reviewed here, no dataset explicitly provides mouse PFC/frontal cortex together with the complete human APOE3/APOE4 × sex × AD/control single-cell or single-nucleus design. A role-based, multi-dataset validation strategy remains the strongest defensible public-data approach.
