# Comprehensive Research Plan

## Cell-type-specific mitochondrial transcriptional dysregulation in Alzheimer's disease across sex and APOE genotype

**Study type:** Secondary analysis of the ROSMAP prefrontal-cortex single-nucleus RNA-sequencing dataset used by Yu et al.  
**Primary data source:** MIT_ROSMAP single-nucleus multiomics study / Mathys et al. atlas  
**Plan date:** 2026-07-18  
**Document status:** Preregistration-ready draft; exact variable names, software versions, and final thresholds should be locked after the data-access and feasibility audit.

---

## Executive summary

This project will determine how mitochondrial-related gene programs change in Alzheimer's disease (AD), which brain cell types show the strongest changes, and whether those changes depend on sex and APOE genotype.

The study will reuse the large ROSMAP single-nucleus RNA-sequencing (snRNA-seq) atlas of postmortem prefrontal cortex. The Yu et al. paper analyzed 2.3 million nuclei from 427 donors in the source atlas and used a final AD-versus-no-cognitive-impairment subset of 276 donors after quality-control and eligibility exclusions. It reported several mitochondrial clues, including a strong sex-divergent signal for **MT-ND2** and enrichment of oxidative phosphorylation and electron-transport pathways among genes that behaved differently in APOE epsilon 4 carriers versus APOE epsilon 3/3 individuals. However, mitochondria were not the paper's primary focus, and the authors did not perform a comprehensive mitochondrial-gene analysis.

This follow-up study will improve on that work in five ways:

1. It will define a complete mitochondrial gene universe using **MitoCarta3.0**, its 149 curated MitoPathways, and carefully separated functional-regulator gene sets.
2. It will use the **donor**, not the individual nucleus, as the statistical replicate. The primary differential-expression workflow will therefore be donor-level pseudobulk analysis.
3. It will test mitochondrial pathways using the full ranked gene-expression results rather than relying mainly on arbitrary top-gene lists.
4. It will explicitly test AD-by-sex, AD-by-APOE, and AD-by-sex-by-APOE effects while acknowledging the limited power of small groups, especially male APOE epsilon 2 carriers.
5. It will distinguish **nuclear-encoded mitochondrial genes**, which are suitable for primary analysis in snRNA-seq, from **mitochondrial-DNA-encoded transcripts**, which are technically difficult to interpret in isolated nuclei and will be treated as secondary or exploratory evidence.

The expected output is a cell-type-resolved mitochondrial atlas containing gene-level effect sizes, mitochondrial pathway results, sex/APOE interaction results, pathology and cognition associations, prioritized candidate genes, external replication, and a reproducible analysis pipeline.

---

# 1. Background and rationale

## 1.1 Why mitochondria matter in this dataset

Mitochondria generate cellular energy, regulate redox balance, calcium signaling, lipid metabolism, stress responses, and cell death. Neurons are especially dependent on mitochondrial energy production, but astrocytes, microglia, oligodendrocytes, and vascular cells also use mitochondrial programs in cell-type-specific ways. A mitochondrial abnormality can therefore have different consequences in different brain cell populations.

The Yu et al. study provides a strong starting point because it found:

- **MT-ND2**, a mitochondrial-DNA-encoded Complex I gene, among the strongest sex-divergent AD-associated genes.
- Multiple mitochondrial genes among low-similarity or divergent gene lists in the sex and APOE comparisons.
- Enrichment of **oxidative phosphorylation**, **respiratory electron transport**, and the **mitochondrial electron-transport chain** among genes showing divergent AD responses in APOE epsilon 4 carriers versus APOE epsilon 3/3 individuals.
- A recommendation that future work investigate the translational relevance of sex- and APOE-dependent mitochondrial functions.

These results justify a dedicated mitochondrial study, but they do not answer several important questions:

- Which mitochondrial pathways are altered in each cell type?
- Are the results driven by nuclear-encoded mitochondrial genes, mitochondrial-DNA-encoded genes, or both?
- Are changes shared across cell types or concentrated in particular neuronal or glial subtypes?
- Do sex and APOE modify the AD effect on mitochondrial programs?
- Are transcriptomic mitochondrial changes associated with amyloid, tau, cognitive decline, or cognitive resilience?
- Do the signals replicate in an independent human AD single-nucleus dataset or an orthogonal ROSMAP data type?

## 1.2 Central technical caution

The source data are **single-nucleus**, not whole-cell, RNA-seq data. Most mature mitochondrial transcripts are located outside the nucleus. Consequently, isolated nuclei generally contain far fewer mitochondrial transcripts than intact cells. Mitochondrial reads in a nucleus library can partly reflect incomplete cytoplasmic stripping, ambient RNA, damaged nuclei, or other technical effects.

Therefore:

- **Nuclear-encoded mitochondrial genes will be the primary biological evidence.**
- **Mitochondrial-DNA-encoded genes will be analyzed separately and interpreted cautiously.**
- Percent mitochondrial reads will be treated mainly as a quality-control feature, not automatically as a measurement of mitochondrial activity.
- This study will describe **mitochondrial-related transcription**, not direct mitochondrial respiration, ATP production, membrane potential, or reactive oxygen species.

This distinction must be stated clearly in every manuscript, presentation, and interpretation.

---

# 2. Research question, aims, and hypotheses

## 2.1 Main research question

How are mitochondrial-related transcriptional programs altered in Alzheimer's disease across human brain cell types, and how are those alterations modified by sex and APOE genotype?

## 2.2 Specific Aim 1: Build a cell-type-resolved mitochondrial AD atlas

**Objective:** Identify mitochondrial genes and pathways that differ between AD and no cognitive impairment (NCI) within each major brain cell class and high-resolution cell cluster.

**Primary hypothesis:** AD is associated with cell-type-specific dysregulation of oxidative phosphorylation, mitochondrial translation, redox defense, mitochondrial protein quality control, and mitophagy, with the strongest effects in metabolically demanding neurons and disease-responsive glial populations.

**Primary outputs:**

- Donor-level gene-expression effect estimates for mitochondrial genes.
- Pathway-level effect estimates for curated mitochondrial functions.
- A map of shared versus cell-type-specific mitochondrial responses.

## 2.3 Specific Aim 2: Test whether sex and APOE modify mitochondrial AD responses

**Objective:** Determine whether the AD effect on mitochondrial transcription differs by sex, APOE genotype, or their combination.

**Primary hypotheses:**

1. APOE epsilon 4 carriers show greater dysregulation of oxidative phosphorylation and electron-transport programs than APOE epsilon 3/3 individuals.
2. Sex modifies APOE-associated mitochondrial responses, especially in excitatory neurons, astrocytes, and microglia.
3. APOE epsilon 2 carriers may show distinctive effects, but the small male epsilon 2 sample will limit detection of modest effects.

**Primary outputs:**

- AD-by-sex interaction estimates within each APOE group.
- AD-by-APOE interaction estimates within each sex.
- A carefully interpreted three-way AD-by-sex-by-APOE analysis.
- A mitochondrial-only reproduction of the Zhang-Yu pattern comparison as a secondary descriptive analysis.

## 2.4 Specific Aim 3: Relate mitochondrial programs to neuropathology and cognition

**Objective:** Test whether mitochondrial gene and pathway changes are associated with continuous measures of AD pathology and cognitive outcomes.

**Secondary hypotheses:**

- Mitochondrial pathway disruption increases with tau and amyloid burden.
- Some mitochondrial programs are more strongly related to cognition than to neuropathology and may contribute to vulnerability or resilience.
- Associations with cognition may differ across cell types and APOE backgrounds.

**Potential outcomes:** Braak stage, CERAD score, quantitative amyloid and tau measures, global cognitive score near death, longitudinal cognitive slope, and resilience-related phenotypes, subject to data availability and approved access.

## 2.5 Specific Aim 4: Prioritize and validate candidate mitochondrial mechanisms

**Objective:** Identify a small, well-supported set of candidate genes and pathways for later experimental study.

**Candidate-prioritization evidence will include:**

- Statistically supported AD association.
- Large and precise effect size.
- Consistency across related subclusters.
- Significant sex/APOE interaction.
- Membership in a coherent mitochondrial pathway.
- Association with pathology or cognition.
- Replication in an independent cohort.
- Orthogonal support from proteomics, chromatin accessibility, or other molecular data.

---

# 3. Study design

## 3.1 Overall design

This is a retrospective, observational, secondary analysis of de-identified postmortem human brain data.

The project will proceed in four phases:

| Phase | Purpose | Main product |
|---|---|---|
| 0. Feasibility and data audit | Confirm that required counts, metadata, cell labels, and mitochondrial genes are usable | Locked analysis specification |
| 1. Primary discovery | Estimate AD effects on mitochondrial genes and pathways by cell type | Cell-type mitochondrial AD atlas |
| 2. Stratified and interaction analysis | Test sex and APOE modification | Interaction maps and planned contrasts |
| 3. Validation and prioritization | Replicate signals and identify strongest candidates | Shortlist for experimental follow-up |

## 3.2 Primary versus exploratory scope

To limit false discoveries, the study will have a prespecified hierarchy.

### Primary cell classes

1. Excitatory neurons
2. Inhibitory neurons
3. Astrocytes
4. Microglia
5. Oligodendrocytes
6. Oligodendrocyte precursor cells

These classes contain the most nuclei and/or showed substantial AD-associated transcriptional changes in the Yu et al. analysis.

### Secondary cell classes

- Endothelial cells
- Pericytes
- Smooth muscle cells
- Fibroblasts
- CNS-associated macrophages
- T cells

These will be analyzed when enough donor-level observations and nuclei are available, but null results will be interpreted cautiously.

### Primary resolution

Major cell classes will be analyzed first because they provide better donor coverage and power.

### Secondary resolution

All 54 high-resolution clusters will then be analyzed. Subcluster results will be considered strongest when they:

- pass statistical thresholds,
- have adequate donor and nucleus counts,
- are supported by neighboring or biologically related subclusters,
- and are not driven by a small number of donors.

---

# 4. Data source, cohort, and access

## 4.1 Source dataset

The source atlas contains approximately 2.3 million nuclei from prefrontal cortex samples of 427 ROSMAP participants. It includes 54 high-resolution cell clusters grouped into 12 major cell classes.

The Yu et al. AD-versus-NCI analysis used 276 donors after excluding:

- four samples with inconsistent reported sex and XIST/UTY expression,
- APOE epsilon 2/epsilon 4 individuals,
- samples lacking required APOE or postmortem-interval information,
- MCI and other-dementia diagnostic groups.

## 4.2 Primary cohort

The primary analysis will reproduce the Yu et al. AD-versus-NCI eligibility definition so that results are directly comparable.

| Sex-APOE group | Total | AD | NCI |
|---|---:|---:|---:|
| Female APOE epsilon 2 carrier | 25 | 8 | 17 |
| Female APOE epsilon 3/3 | 82 | 37 | 45 |
| Female APOE epsilon 4 carrier | 37 | 26 | 11 |
| Male APOE epsilon 2 carrier | 13 | 7 | 6 |
| Male APOE epsilon 3/3 | 82 | 29 | 53 |
| Male APOE epsilon 4 carrier | 37 | 27 | 10 |
| **Total** | **276** | **134** | **142** |

APOE grouping will follow the paper for the main analysis:

- epsilon 2 carrier: epsilon 2/2 or epsilon 2/3
- epsilon 3/3 reference group
- epsilon 4 carrier: epsilon 3/4 or epsilon 4/4
- epsilon 2/4 excluded from the primary analysis

## 4.3 Expanded secondary cohort

A secondary analysis may use more of the 427-donor source atlas by including:

- MCI or intermediate cognitive states,
- continuous pathology measures,
- continuous cognition or decline measures,
- pathological AD without dementia,
- dementia with low AD pathology,
- cognitive-resilience phenotypes.

This expanded analysis should not replace the primary AD-versus-NCI analysis. It addresses disease progression and resilience rather than the same binary question.

## 4.4 Data access and governance

The data are available through the AD Knowledge Portal/Synapse, with controlled-access requirements for donor-level human data. Before analysis:

1. Register or verify the Synapse account.
2. Submit the required Data Use Certificate or access request.
3. Confirm the approved use includes sex, APOE, diagnosis, pathology, and cognitive variables.
4. Store controlled data only in an approved secure environment.
5. Never place donor-level controlled data in a public repository.
6. Make only code, synthetic examples, documentation, and approved summary results public.

## 4.5 Required data objects

At minimum, obtain:

- raw or integer gene-by-nucleus count matrix,
- donor/sample ID for every nucleus,
- 54-cluster annotation and major cell-class annotation,
- diagnosis or cognitive diagnosis,
- APOE genotype,
- reported sex,
- age at death,
- postmortem interval,
- sequencing batch and library identifiers,
- nucleus-level QC metrics,
- donor-level pathology and cognition variables for secondary aims,
- ancestry or genetic principal components if available,
- RNA quality variables if available.

---

# 5. Defining the mitochondrial gene universe

A central strength of this project will be a transparent, versioned definition of what counts as a mitochondrial-related gene.

## 5.1 Tier 1: MitoCarta3.0 mitochondrial-localized genes

Use the human MitoCarta3.0 inventory as the primary gene universe. It contains 1,136 human genes with strong evidence of mitochondrial localization and includes sub-mitochondrial compartment and pathway annotations.

This tier includes both:

- nuclear genes encoding mitochondrial proteins, and
- mitochondrial-DNA genes encoding mitochondrial proteins.

Create a frozen local copy of the MitoCarta table and record:

- download date,
- database version,
- gene symbol,
- Ensembl ID where available,
- mitochondrial compartment,
- MitoPathway membership,
- nuclear versus mitochondrial genome origin.

## 5.2 Tier 2: MitoPathways

Use the 149 hierarchical MitoPathways supplied with MitoCarta3.0. Prespecify a smaller primary panel to limit multiple testing.

### Recommended primary pathway panel

| Domain | Example pathway groups |
|---|---|
| Oxidative phosphorylation | Complex I, II, III, IV, V; respiratory electron transport; ATP synthesis |
| Mitochondrial translation | Mitoribosome, mitochondrial tRNA biology, translation initiation and elongation |
| Central metabolism | TCA cycle, pyruvate metabolism, fatty-acid beta oxidation, amino-acid metabolism |
| Redox biology | Reactive-oxygen-species detoxification, glutathione-related defense, thioredoxin systems |
| Mitochondrial quality control | Protein import, proteases, chaperones, unfolded-protein response-related programs |
| Dynamics and turnover | Fusion, fission, mitophagy, mitochondrial autophagy receptors |
| Genome maintenance | mtDNA replication, repair, transcription, nucleoid organization |
| Biogenesis | Mitochondrial transcription and replication regulators, organelle biogenesis |
| Calcium and signaling | Calcium transport, permeability-transition-related signaling, apoptosis-related programs |
| Lipid and cofactor metabolism | Cardiolipin, heme, iron-sulfur clusters, NAD-related metabolism, one-carbon metabolism |

## 5.3 Tier 3: mtDNA-encoded genes

The 13 mitochondrial-DNA-encoded protein-coding genes are:

- **MT-ND1, MT-ND2, MT-ND3, MT-ND4, MT-ND4L, MT-ND5, MT-ND6**
- **MT-CO1, MT-CO2, MT-CO3**
- **MT-CYB**
- **MT-ATP6, MT-ATP8**

MT-RNR1, MT-RNR2, and mitochondrial tRNAs may be retained for technical exploration if present, but they should not be central biological endpoints unless their detection and annotation are reliable.

**Interpretation rule:** mtDNA-encoded transcript results are exploratory because nuclei should contain little mature mitochondrial RNA. Every major mtDNA result must be checked for correlation with nuclear quality, cytoplasmic carryover, library depth, postmortem interval, and ambient contamination.

## 5.4 Tier 4: Mitochondrial regulators not necessarily localized to mitochondria

Some genes regulate mitochondrial biology without being resident mitochondrial proteins. Keep these in a separate annotation rather than mixing them silently into MitoCarta.

Examples include regulators of:

- biogenesis: **PPARGC1A, NRF1, GABPA, TFAM**
- integrated stress signaling: **ATF4, ATF5, DDIT3**
- mitophagy: **PINK1, PRKN, BNIP3, BNIP3L, FUNDC1**
- fusion/fission: **MFN1, MFN2, OPA1, DNM1L, FIS1**
- mitochondrial proteostasis: **LONP1, CLPP, HSPD1, HSPE1**
- redox regulation: **SOD2, PRDX3, TXN2**

These genes may overlap MitoCarta; the separate tier simply preserves the distinction between mitochondrial localization and mitochondrial regulation.

## 5.5 Gene-set version control

Create a machine-readable file such as:

`metadata/mitochondrial_gene_sets_v1.tsv`

Recommended columns:

- `gene_symbol`
- `ensembl_id`
- `genome_origin` (`nuclear` or `mtDNA`)
- `mitocarta_member`
- `mitocarta_compartment`
- `mitopathway_level1`
- `mitopathway_level2`
- `mitopathway_level3`
- `regulatory_category`
- `primary_or_exploratory`
- `source_version`

Resolve outdated symbols before analysis and preserve an audit trail of all mappings.

---

# 6. Phase 0: Feasibility and data audit

No hypothesis testing should begin until this audit is complete.

## 6.1 Count-matrix audit

Determine:

- whether counts are raw integers,
- whether intronic and exonic reads are included,
- whether mitochondrial chromosome features are present,
- how gene IDs were mapped,
- whether mitochondrial genes were filtered during original preprocessing,
- whether duplicate gene symbols exist,
- whether counts are available before normalization.

## 6.2 Donor-by-cell coverage audit

For each donor and cell cluster, calculate:

- number of nuclei,
- total pseudobulk library size,
- number of detected genes,
- number and fraction of detected MitoCarta genes,
- mtDNA-encoded read count,
- median nucleus QC metrics.

Produce a donor-by-cluster heatmap. This will identify clusters that appear large overall but are represented by too few nuclei in many individual donors.

## 6.3 Group-balance audit

For every major cell class and high-resolution cluster, tabulate the number of usable donors in each of the six sex-APOE-diagnosis combinations.

Flag any planned comparison with:

- fewer than five donors in a group,
- extreme imbalance in nuclei per donor,
- complete separation of diagnosis and batch,
- or one or two donors contributing a large fraction of all nuclei.

## 6.4 Metadata audit

Check:

- sex label versus XIST and Y-linked marker expression,
- APOE genotype coding,
- duplicate donors or libraries,
- missing covariates,
- age and postmortem-interval distributions by group,
- batch distribution by diagnosis, sex, and APOE,
- ancestry composition,
- pathology and cognition variable definitions.

## 6.5 Feasibility decision

At the end of Phase 0, lock:

- the final donor cohort,
- primary cell classes,
- minimum nuclei threshold,
- primary gene sets,
- primary contrasts,
- covariates,
- multiple-testing families,
- software environment.

Any change after this lock should be documented as a protocol amendment.

---

# 7. Quality control and preprocessing

## 7.1 Prefer the curated source object, but verify it

The source atlas already underwent extensive processing and cell annotation. Reusing the curated object improves comparability and avoids unnecessary re-clustering. However, verify the key QC decisions rather than assuming they are appropriate for a mitochondrial analysis.

## 7.2 Donor-level QC

- Reproduce the XIST/UTY sex-consistency check.
- Exclude or separately flag ambiguous sex-label samples.
- Confirm APOE genotype and the epsilon 2/4 exclusion.
- Inspect age, postmortem interval, RNA quality, batch, and sequencing depth.
- Identify outlier donors by principal-component analysis of pseudobulk profiles within each cell class.
- Perform leave-one-donor-out influence checks for important findings.

## 7.3 Nucleus-level QC

If starting from already filtered data, summarize rather than reapply arbitrary cutoffs. If raw nucleus data are used, evaluate:

- total UMIs,
- detected genes,
- doublet score,
- ambient RNA contamination,
- intronic fraction,
- mitochondrial transcript fraction,
- ribosomal transcript fraction,
- donor and batch distributions.

Avoid a universal mitochondrial-read cutoff copied from whole-cell scRNA-seq. In snRNA-seq, mitochondrial reads have a different technical meaning.

## 7.4 Minimum nuclei per donor-cell-type sample

Recommended primary rule:

- Retain a donor-cell-type pseudobulk sample if it contains at least **30 nuclei**.

Sensitivity analyses:

- minimum 10 nuclei,
- minimum 50 nuclei.

The final threshold should be based on the observed mean-variance behavior, not only convention. Rare cell types may require a different prespecified threshold.

## 7.5 Gene filtering

For each cell type, retain a gene for model fitting if it has adequate count support across donors. A reasonable starting rule is:

- counts-per-million above a small threshold in at least the size of the smallest modeled group, or
- a data-driven `filterByExpr` rule in edgeR.

Do not require a gene to be detected in a fixed percentage of individual nuclei for the primary pseudobulk model. The donor-level count distribution is the relevant unit.

## 7.6 Normalization

For pseudobulk counts:

- use TMM normalization or another validated bulk-RNA-seq count normalization,
- include library-size offsets in the model,
- use log-CPM or voom-transformed values only for visualization and some downstream scoring,
- do not use integrated or batch-corrected expression values for differential expression.

## 7.7 Do not regress away the target biology

Do not automatically regress out:

- mitochondrial pathway scores,
- mitochondrial gene percentage,
- oxidative-phosphorylation principal components,
- stress-response modules.

These may be part of the biological signal. Instead, use mitochondrial-read fraction as a sensitivity covariate only when evaluating whether mtDNA-transcript results are technical.

---

# 8. Primary statistical framework

## 8.1 Experimental unit

The **donor** is the biological replicate.

Individual nuclei from the same donor are not independent human samples. Treating thousands of nuclei as thousands of independent replicates can underestimate biological variability and inflate significance.

Therefore, the primary workflow will aggregate raw counts within each:

`donor x cell type or cluster`

This creates one pseudobulk expression profile per donor per cell population.

## 8.2 Recommended primary tools

A practical R workflow is:

- `SingleCellExperiment` or `Seurat` for object handling,
- `muscat` or a custom sparse aggregation function for pseudobulk construction,
- `edgeR` quasi-likelihood models for gene-level inference,
- `limma`/`camera` for correlation-aware gene-set testing,
- `fgsea` as a complementary ranked-list analysis,
- `ComplexHeatmap` and `ggplot2` for figures,
- `scDesign3` and/or `muscat` simulation tools for power and operating-characteristic studies.

Lock exact versions with `renv` after the feasibility audit.

## 8.3 Baseline AD model within each cell type

For the first-pass major-cell-class analysis, fit a donor-level model such as:

```text
expression ~ AD_status + sex + APOE_group + age_at_death + PMI + batch + ancestry_covariates
```

This estimates an average AD effect while adjusting for sex and APOE.

The exact covariate set should be selected before testing. Include a covariate only when it is measured reliably, has enough variation, and is not completely confounded with the comparison.

## 8.4 Full interaction model

For cell types with adequate donor coverage, fit:

```text
expression ~ AD_status * sex * APOE_group
           + age_at_death
           + PMI
           + batch
           + ancestry_covariates
           + optional RNA_quality_covariate
```

This expands to:

- main effects of AD, sex, and APOE,
- AD-by-sex,
- AD-by-APOE,
- sex-by-APOE,
- AD-by-sex-by-APOE.

Because the epsilon 2 groups are small, the three-way coefficient may be unstable. The full model should be used with planned contrasts and shrinkage-aware interpretation, not as a license to report every possible coefficient.

## 8.5 Planned contrasts

### Contrast family A: AD versus NCI within each sex-APOE group

- Female epsilon 2: AD - NCI
- Female epsilon 3/3: AD - NCI
- Female epsilon 4: AD - NCI
- Male epsilon 2: AD - NCI
- Male epsilon 3/3: AD - NCI
- Male epsilon 4: AD - NCI

These reproduce the paper's group structure.

### Contrast family B: Sex difference in the AD effect within each APOE group

For example, within APOE epsilon 4:

```text
(Female_AD - Female_NCI) - (Male_AD - Male_NCI)
```

This is the direct interaction question. It is not the same as comparing females and males among AD cases.

### Contrast family C: APOE difference in the AD effect within each sex

For example, in females:

```text
(Female_e4_AD - Female_e4_NCI)
-
(Female_e33_AD - Female_e33_NCI)
```

Repeat for epsilon 2 versus epsilon 3/3 and for males.

### Contrast family D: Three-way interaction

Test whether the sex difference in the AD effect changes across APOE groups. This is the most difficult contrast and should be treated as secondary unless simulation demonstrates adequate power.

## 8.6 Gene-level analysis

Fit models genome-wide, then create a mitochondrial-focused results table.

For each gene, cell type, and contrast report:

- log2 fold change,
- standard error,
- 95% confidence interval,
- raw p value,
- FDR-adjusted p value,
- mean expression,
- number of donors per group,
- median nuclei per donor,
- MitoCarta and MitoPathway annotations.

Do not define importance by p value alone. A small but precise effect and a large but uncertain effect mean different things.

## 8.7 Primary mitochondrial statistical family

For each primary cell class and primary contrast:

- control FDR across the expressed MitoCarta genes,
- report genome-wide FDR as a complementary column,
- and clearly label which correction defines the primary claim.

A more conservative alternative is to correct across all mitochondrial genes, primary cell classes, and primary contrasts together. Choose and preregister one strategy.

## 8.8 Pathway analysis

Use more than one method because each answers a different question.

### Method 1: CAMERA or another correlation-aware ranked gene-set test

Use the complete gene-level model statistics. CAMERA tests whether genes in a pathway tend to rank more strongly than genes outside it while accounting for correlation among pathway genes.

This should be the primary pathway analysis.

### Method 2: Preranked GSEA

Rank all expressed genes by a signed statistic such as:

```text
sign(log2FC) x -log10(p value)
```

or preferably the model's moderated test statistic. Run GSEA/fgsea on MitoPathways and selected external pathway sets.

Report normalized enrichment score, p value, adjusted p value, and leading-edge genes.

### Method 3: Over-representation analysis

Use a hypergeometric or Fisher test on a prespecified significant-gene list only as a secondary summary.

Use the correct background:

- To ask whether mitochondrial genes are overrepresented among all AD genes, use all expressed genes as background.
- To ask which mitochondrial subpathway is overrepresented among mitochondrial hits, use all expressed MitoCarta genes as background.

These are different questions and should not be mixed.

## 8.9 Pathway and module scores

Create donor-level scores for core mitochondrial programs using pseudobulk normalized expression.

Possible scoring methods:

- first principal component of pathway genes,
- mean standardized expression with direction-preserving checks,
- GSVA or singscore on donor-level pseudobulk profiles.

For each score, fit the same AD, sex, APOE, and interaction models used for gene-level analysis.

Pathway scores are easier to interpret and often more powerful than individual low-count genes, but they can hide genes changing in opposite directions. Always show the gene-level contribution to significant modules.

## 8.10 Mitonuclear coordination analysis

Analyze whether nuclear-encoded and mtDNA-encoded oxidative-phosphorylation signals remain coordinated.

Possible measures:

1. Correlation between nuclear OXPHOS and mtDNA OXPHOS scores within each cell type.
2. Difference between standardized nuclear and mtDNA pathway scores as an exploratory "mitonuclear imbalance" index.
3. Complex-specific coordination, especially Complex I because MT-ND2 was highlighted by the paper.

Because mtDNA transcripts are technically uncertain in nuclei, conclusions about mitonuclear imbalance must be labeled exploratory and repeated after controlling for nucleus-quality and mitochondrial-read metrics.

## 8.11 Cell-type specificity

For every mitochondrial gene and pathway:

- compare effect sizes across major cell classes,
- plot confidence intervals rather than only significance symbols,
- test heterogeneity across cell types,
- identify effects that are shared, neuron-specific, glia-specific, or restricted to one subtype.

A result that is significant in one cell type and nonsignificant in another is not automatically evidence that the two effects differ. A formal interaction or heterogeneity test is required.

## 8.12 High-resolution cluster analysis

After major-cell-class analysis:

- fit the same pseudobulk models in all eligible subclusters,
- use a stricter donor-coverage filter,
- group related subclusters in figures,
- compare signs and magnitudes across related neuronal layers or glial states,
- distinguish isolated findings from reproducible subtype patterns.

## 8.13 Reproduction of the Zhang-Yu analysis

As a secondary analysis, restrict the Zhang-Yu framework to mitochondrial genes.

For each mitochondrial gene:

- reproduce the ternary AD states (+1, 0, -1),
- calculate sex and APOE similarity scores,
- compare the mitochondrial-score distribution with the distribution for all genes,
- test whether particular MitoPathways are overrepresented among divergent genes.

This allows direct comparison with Yu et al., but it should not replace the primary continuous-effect analysis because ternary coding discards fold-change magnitude and can be sensitive to unequal statistical power.

---

# 9. Cell abundance and composition

Mitochondrial expression differences can coexist with changes in the abundance of cell types or cell states.

Perform a separate differential-abundance analysis using donor-level cell proportions.

Questions include:

- Are mitochondrial signals strongest in cell populations that are depleted or expanded in AD?
- Does a major-cell-class pseudobulk signal reflect a shift among its subclusters?
- Do sex and APOE affect cell abundance independently of transcriptional state?

Use a method appropriate for compositional data, and keep abundance results separate from within-cell-type expression results.

---

# 10. Associations with neuropathology and cognition

## 10.1 Why continuous outcomes are valuable

Binary diagnosis combines many biological states. Two AD donors can have different amyloid, tau, neuronal loss, and cognitive trajectories. Continuous outcomes may reveal stronger or more specific mitochondrial relationships.

## 10.2 Recommended secondary models

For each primary mitochondrial pathway score and selected genes, fit donor-level models such as:

```text
mitochondrial_score ~ tau_measure + sex + APOE + age + PMI + batch
```

```text
mitochondrial_score ~ amyloid_measure + sex + APOE + age + PMI + batch
```

```text
mitochondrial_score ~ cognitive_slope + sex + APOE + education + age + PMI + batch
```

Interaction terms can test whether pathology-score relationships differ by sex or APOE.

## 10.3 Avoid overadjustment

Do not include amyloid or tau as routine covariates in the primary AD-diagnosis model if the goal is to estimate the total AD-associated difference. Pathology may be part of the causal pathway.

Instead, run separate models for:

- total AD association,
- pathology association,
- cognition association,
- pathology-adjusted cognition association for resilience questions.

## 10.4 Resilience analysis

A valuable extension is to compare people with similar AD pathology but different cognitive outcomes.

Possible question:

> At a similar level of pathology, are preserved mitochondrial programs associated with better cognition?

This analysis may identify protective rather than disease-reactive mitochondrial mechanisms.

---

# 11. Statistical power and simulation

## 11.1 Why power is a major issue

The sex-APOE groups are imbalanced. The paper's scDesign3 analysis showed negligible power for small effects in APOE epsilon 2 carriers and substantially lower power in males than females. In the reported simulation, high power required roughly fold change 2.0 in females and 2.5 in males for the small epsilon 2 groups.

Therefore:

- absence of significance in male epsilon 2 carriers is weak evidence of no biological effect,
- apparent sex differences can be influenced by unequal detection power,
- interaction estimates and confidence intervals are more informative than comparing two separate significance calls.

## 11.2 Project-specific power simulation

Repeat and extend the simulation for the mitochondrial study.

### Simulation inputs

- actual donor counts in each group,
- observed nuclei per donor and cell type,
- observed pseudobulk library sizes,
- gene-specific mean and dispersion,
- donor-to-donor variability,
- batch and covariate structure,
- realistic mtDNA sparsity,
- pathway-correlated effects.

### Simulation scenarios

Test:

- fold changes from 1.1 to 2.5,
- effects in 5%, 10%, and 20% of MitoCarta genes,
- coherent pathway effects versus scattered single-gene effects,
- major cell classes versus rare subclusters,
- balanced versus observed group sizes,
- interaction effects of varying magnitude.

### Analysis of simulated data

1. Simulate nucleus-level data with scDesign3 or a comparable model.
2. Aggregate simulated counts to donor-level pseudobulk.
3. Run the exact planned edgeR and pathway pipeline.
4. Estimate sensitivity, false-discovery rate, confidence-interval coverage, and sign error.
5. Repeat at least 200 times per key scenario; target 500 when computationally feasible.

## 11.3 Power-based decision rules

- Treat a contrast as confirmatory only if simulation indicates acceptable error control and useful power for the expected effect range.
- Treat male epsilon 2 and rare-cell interaction results as exploratory unless effects are large and stable.
- Prioritize pathway-level endpoints when single-gene power is poor.
- Always report group sizes and confidence intervals alongside FDR.

---

# 12. Multiple testing plan

A comprehensive study can generate tens of thousands of p values. The testing hierarchy must be declared in advance.

## 12.1 Recommended hierarchy

### Level 1: Primary mitochondrial pathways

Test the prespecified core pathways in the six major cell classes and primary contrast family.

### Level 2: Genes within supported pathways

Interpret individual genes most strongly when their parent pathway is supported, while still reporting all gene-level results.

### Level 3: High-resolution subclusters and additional pathways

Treat as secondary and use their own clearly defined FDR families.

### Level 4: Exploratory mtDNA and three-way interactions

Report effect sizes and FDR but label as exploratory.

## 12.2 Suggested threshold

Use FDR below 0.05 for primary claims. Avoid a mandatory fold-change cutoff as the sole gate. Instead report:

- effect size,
- confidence interval,
- FDR,
- expression abundance,
- donor support,
- replication status.

A practical biological-priority filter may be added after statistical testing, such as absolute log2 fold change at least 0.20 or a pathway-score effect of at least 0.25 standard deviations, but this should not replace full reporting.

---

# 13. Sensitivity and robustness analyses

Every major conclusion should survive several relevant checks.

## 13.1 Analysis-method sensitivity

- Primary donor-level pseudobulk edgeR analysis.
- Alternative pseudobulk method, such as limma-voom or DESeq2.
- MAST/Seurat analysis only as a comparison with the original paper, with donor dependence explicitly acknowledged.

## 13.2 Cell-count threshold sensitivity

Repeat key analyses using minimum 10, 30, and 50 nuclei per donor-cell type.

## 13.3 mtDNA sensitivity

Repeat pathway and module analyses:

- including all MitoCarta genes,
- excluding all mtDNA-encoded genes,
- using only nuclear-encoded MitoCarta genes,
- adjusting for mitochondrial-read fraction,
- excluding nucleus libraries with unusually high mitochondrial carryover.

A result that disappears after excluding mtDNA genes may reflect a technically fragile signal.

## 13.4 Diagnosis sensitivity

Compare:

- clinical AD versus NCI,
- pathology-defined AD versus low pathology,
- continuous pathology,
- expanded progression models including MCI.

## 13.5 APOE coding sensitivity

Compare:

- three APOE categories used in the paper,
- epsilon 4 allele dosage where sample size allows,
- exclusion versus separate display of epsilon 2/4 individuals.

## 13.6 Covariate sensitivity

Repeat key models with reasonable alternate covariate sets, including or excluding:

- RNA quality,
- ancestry principal components,
- batch,
- mitochondrial-read fraction for mtDNA analyses,
- medication-related variables if they later become available.

Do not select a final result based on whichever covariate set produces the smallest p value.

## 13.7 Influence diagnostics

- Leave-one-donor-out analysis.
- Cook's distance or comparable influence measure for pseudobulk models.
- Trimmed or robust dispersion estimation.
- Check whether a result is driven by one sequencing batch or one extreme library.

## 13.8 Negative controls

Use negative controls to detect technical bias:

- randomly matched gene sets with similar expression and gene length,
- housekeeping pathways not expected to show sex-APOE-specific patterns,
- permutation of diagnosis labels within appropriate strata,
- comparison of mtDNA signals with quality metrics.

---

# 14. Validation strategy

## 14.1 Internal validation

Use:

- bootstrap resampling of donors,
- leave-one-donor-out analysis,
- consistency across related subclusters,
- agreement between gene-level and pathway-level results,
- agreement between binary diagnosis and continuous pathology.

A random train/test split is not ideal as the only validation because some sex-APOE groups are already small.

## 14.2 External single-nucleus replication

Use an independent human AD single-nucleus dataset, such as SEA-AD, when donor metadata and cell-type mappings allow the planned contrasts.

Replication steps:

1. Map cell classes to a common broad taxonomy.
2. Use the same mitochondrial gene sets.
3. Fit donor-level pseudobulk models.
4. Compare effect directions and magnitudes.
5. Test pathway-level concordance.
6. Treat brain-region differences as biological context, not only as failure to replicate.

The source ROSMAP tissue is prefrontal cortex, whereas external resources may use middle temporal gyrus or other regions. Full gene-level replication is therefore not expected; pathway and direction consistency may be more informative.

## 14.3 Orthogonal ROSMAP validation

Where matching donors and data are available, test whether transcriptomic mitochondrial findings have support from:

- bulk RNA-seq,
- brain proteomics,
- metabolomics,
- snATAC-seq or multiome chromatin accessibility,
- quantitative neuropathology.

Examples:

- Does reduced nuclear OXPHOS RNA correspond to reduced OXPHOS protein abundance?
- Are promoters or enhancers of candidate nuclear mitochondrial genes less accessible?
- Are pathway scores associated with metabolites linked to TCA or redox metabolism?

## 14.4 Experimental follow-up

The computational project should end with experimentally testable hypotheses.

A later validation study could use:

- isogenic APOE epsilon 3 and epsilon 4 iPSC-derived neurons,
- astrocytes or microglia from male and female donors,
- co-culture systems,
- mitochondrial respiration assays,
- ATP and membrane-potential measurements,
- reactive-oxygen-species assays,
- mitophagy reporters,
- CRISPR perturbation of prioritized genes.

Candidate experiments should be selected only after replication and pathway coherence are assessed.

---

# 15. Candidate prioritization framework

Create a candidate table rather than selecting genes by p value alone.

## 15.1 Suggested evidence columns

| Evidence domain | Example field |
|---|---|
| Statistical evidence | FDR, log2FC, confidence interval |
| Cell-type evidence | number of supported cell classes/subclusters |
| Interaction evidence | AD-by-sex or AD-by-APOE effect |
| Pathway coherence | MitoPathway enrichment and leading-edge membership |
| Disease relevance | association with tau, amyloid, cognition, or resilience |
| Technical robustness | stable after QC and mtDNA sensitivity checks |
| Replication | external cohort direction and p value |
| Orthogonal evidence | protein, chromatin, or metabolite support |
| Novelty | already established versus understudied in AD |
| Experimental tractability | available assays, perturbation feasibility |

## 15.2 Starting candidate categories

The analysis should be unbiased, but the following categories deserve prespecified attention:

- Complex I genes, including **MT-ND2** and nuclear **NDUF** genes.
- Other mtDNA OXPHOS genes highlighted in the paper.
- Mitochondrial translation and mitoribosome genes.
- Mitochondrial protein-quality-control genes.
- Biogenesis regulators such as **PPARGC1A** and **TFAM**.
- Mitophagy and dynamics genes.
- Redox-defense genes.
- Genes showing both mitochondrial pathway membership and strong sex/APOE interaction.

The final shortlist should contain approximately 10 to 30 candidates, not hundreds.

---

# 16. Expected figures and tables

## 16.1 Core figures

| Figure | Content |
|---|---|
| 1 | Study design, cohort filtering, and sample counts |
| 2 | Donor-by-cell-type coverage and mitochondrial detection QC |
| 3 | Major-cell-class AD effects for core mitochondrial pathways |
| 4 | Heatmap of mitochondrial gene log2FC values across cell classes |
| 5 | Oxidative-phosphorylation complex-specific results |
| 6 | AD-by-sex interaction effects within APOE groups |
| 7 | AD-by-APOE interaction effects within each sex |
| 8 | High-resolution subcluster map of significant pathways |
| 9 | Pathology and cognition association plots |
| 10 | External replication and candidate-prioritization summary |

## 16.2 Supplementary figures

- Full 54-cluster donor coverage.
- All MitoPathway results.
- mtDNA-specific QC and sensitivity plots.
- Leave-one-donor-out results.
- Alternative model comparisons.
- Power curves by cell type and contrast.
- Differential-abundance results.
- Mitochondrial-only Zhang-Yu results.

## 16.3 Core tables

| Table | Content |
|---|---|
| 1 | Cohort and covariate summary |
| 2 | Mitochondrial gene-set dictionary |
| 3 | Gene-level primary results |
| 4 | Pathway-level primary results |
| 5 | Sex/APOE interaction results |
| 6 | Pathology and cognition associations |
| 7 | Replication results |
| 8 | Prioritized candidate genes and evidence |

---

# 17. Reproducibility and data management

## 17.1 Recommended project structure

```text
mito_ad_rosmap/
  README.md
  LICENSE
  renv.lock
  config/
    analysis_config.yml
    contrasts.yml
  metadata/
    data_dictionary.md
    mitochondrial_gene_sets_v1.tsv
    sample_exclusion_log.tsv
  scripts/
    00_access_and_manifest.R
    01_feasibility_audit.R
    02_pseudobulk_build.R
    03_qc_reports.R
    04_primary_de.R
    05_pathway_analysis.R
    06_interaction_models.R
    07_pathology_cognition.R
    08_power_simulation.R
    09_validation.R
    10_figures_tables.R
  workflow/
    _targets.R
  results/
    qc/
    gene_level/
    pathways/
    interactions/
    validation/
  figures/
  reports/
  tests/
```

## 17.2 Workflow controls

- Use a workflow manager such as `targets`, Snakemake, or Nextflow.
- Record random seeds.
- Lock software versions with `renv` or containers.
- Store a data manifest with checksums.
- Write unit tests for sample filtering, contrasts, and gene-set mapping.
- Produce an automated HTML QC report.
- Keep raw data read-only.
- Never manually edit result tables.

## 17.3 Public materials

Public repository:

- code,
- workflow configuration,
- gene-set definitions,
- synthetic examples,
- documentation,
- approved aggregate results.

Controlled environment only:

- donor-level counts,
- donor metadata,
- sensitive clinical variables,
- individual-level results.

---

# 18. Risks, limitations, and mitigation

| Risk | Why it matters | Mitigation |
|---|---|---|
| mtDNA transcripts are underrepresented or contaminated in nuclei | Can make mitochondrial-gene results technical rather than biological | Make nuclear-encoded genes primary; analyze mtDNA separately; run QC and sensitivity analyses |
| Small male epsilon 2 group | Low power and unstable interactions | Treat as exploratory; emphasize confidence intervals; use simulations and pathway-level analyses |
| Pseudoreplication | Cell-level tests can inflate significance | Use donor-level pseudobulk as primary |
| Many cell types and contrasts | High multiple-testing burden | Prespecify primary cells, pathways, and contrasts; use hierarchical FDR |
| Cell-composition changes | Can mimic or obscure state changes | Analyze differential abundance separately; inspect subcluster proportions |
| Postmortem and technical effects | May correlate with mitochondrial/stress expression | Adjust for PMI, batch, RNA quality where available; run influence and sensitivity checks |
| Predominantly White cohort | Limits generalizability | State limitation clearly; seek ancestrally diverse replication |
| Medication history unavailable | Metabolic and inflammatory signals may be confounded | Acknowledge; test available health covariates; avoid causal claims |
| Transcript abundance is not mitochondrial function | RNA changes may not equal respiration changes | Use careful language; validate with proteomics/metabolomics and functional assays |
| Different brain regions in replication cohorts | Region-specific biology may reduce exact replication | Prioritize pathway and direction concordance; interpret regional heterogeneity |
| Annotation or gene-symbol mismatch | Can silently remove mitochondrial genes | Freeze gene-set version; map Ensembl IDs carefully; document exclusions |

---

# 19. Interpretation rules

The following rules should be written into the protocol before results are seen.

1. **A significant mitochondrial transcript change is not proof of mitochondrial dysfunction.**
2. **A nonsignificant result is not proof of no effect, especially in small groups.**
3. **Significant in one group and nonsignificant in another is not itself a significant interaction.**
4. **mtDNA transcript results require stronger technical scrutiny than nuclear-encoded mitochondrial genes.**
5. **Pathway enrichment does not show that every pathway gene moves in the same direction.**
6. **A pathway name is an annotation, not a direct functional assay.**
7. **Postmortem association does not establish cause or temporal order.**
8. **Replication and orthogonal evidence should determine which candidates move to experiments.**

---

# 20. Timeline and milestones

A realistic computational timeline is approximately 12 months after data access.

| Month | Work package | Milestone |
|---:|---|---|
| 1 | Access, documentation, environment setup | Approved data access and reproducible environment |
| 2 | Feasibility and QC audit | Locked cohort, gene sets, thresholds, and contrasts |
| 3 | Pseudobulk construction and baseline models | Validated major-cell-class count matrices |
| 4 | Aim 1 gene-level analysis | Major-cell-class mitochondrial AD atlas |
| 5 | Aim 1 pathway and module analysis | Primary mitochondrial pathway results |
| 6 | High-resolution cluster analysis | 54-cluster secondary atlas |
| 7 | Aim 2 sex and APOE interactions | Planned contrast and interaction tables |
| 8 | Power simulations and robustness | Power report and protocol amendments if required |
| 9 | Aim 3 pathology and cognition | Continuous-outcome results |
| 10 | External and orthogonal validation | Replication report |
| 11 | Candidate prioritization and figures | Final candidate shortlist and draft figures |
| 12 | Manuscript, code release, and archive | Reproducible submission package |

## Go/no-go checkpoints

### End of Month 2

Proceed only if:

- mitochondrial gene detection is adequate in the primary cell classes,
- donor coverage is sufficient for the primary contrasts,
- count and metadata integrity are verified.

### End of Month 5

If mtDNA transcript quality is poor, formally downgrade all mtDNA analyses to exploratory and continue with nuclear-encoded mitochondrial genes.

### End of Month 8

If interaction power is poor, refocus claims on effect-size estimation and pathway-level patterns rather than binary significance.

---

# 21. Minimal viable study versus full study

## 21.1 Minimal viable study

A strong first paper can be completed with:

- the 276-donor AD/NCI cohort,
- six major cell classes,
- MitoCarta3.0 and core MitoPathways,
- donor-level pseudobulk edgeR models,
- AD, AD-by-sex, and AD-by-APOE contrasts,
- CAMERA/GSEA pathway analysis,
- mtDNA sensitivity analysis,
- one external replication dataset,
- candidate prioritization.

## 21.2 Full study

The full version adds:

- all 54 clusters,
- MCI and disease-progression analyses,
- cognition and resilience,
- differential abundance,
- snATAC/multiome regulatory support,
- proteomic and metabolomic validation,
- co-expression or regulatory-network analysis,
- experimental follow-up.

---

# 22. Optional advanced analyses

These analyses can add value but should not delay the primary study.

## 22.1 Co-expression networks

Build donor-level co-expression networks within well-powered cell classes. Identify modules enriched for MitoCarta genes and test module eigengenes against AD, sex, APOE, pathology, and cognition.

Network construction should require enough donors and should include stability assessment. Do not infer causality from co-expression alone.

## 22.2 Cross-cell-type communication

Investigate whether mitochondrial stress programs in one cell class correlate with inflammatory or trophic signaling in another. Because the data are postmortem and cross-sectional, describe this as coordinated expression rather than proven communication.

## 22.3 Chromatin regulation

If matching snATAC or multiome data are available, test whether significant nuclear mitochondrial genes show corresponding changes in promoter/enhancer accessibility or transcription-factor motif activity.

Priority regulators may include NRF1, GABPA, PPARGC1A-linked programs, ATF4/ATF5 stress signaling, and HSF-related programs.

## 22.4 Multivariate borrowing across cell types

A hierarchical or multivariate shrinkage model can borrow information across related cell types and improve effect estimates. Use this only as a complement to transparent cell-type-specific models.

---

# 23. Concrete first ten actions

1. Obtain controlled access to the MIT_ROSMAP snRNA-seq counts and donor metadata.
2. Reproduce the Yu et al. 276-donor inclusion/exclusion flow.
3. Download and freeze MitoCarta3.0 and MitoPathways annotations.
4. Verify that mitochondrial genes are present in the raw count matrix.
5. Build donor-by-major-cell-class pseudobulk counts.
6. Produce donor coverage, library-size, and mitochondrial-detection QC reports.
7. Lock primary pathways, cell classes, covariates, and contrast families.
8. Fit baseline AD pseudobulk models and verify model diagnostics.
9. Run project-specific scDesign3/pseudobulk power simulations.
10. Begin the primary gene-set analysis before examining high-resolution exploratory results.

---

# 24. Suggested preregistration statement

> We will perform a donor-level pseudobulk analysis of ROSMAP prefrontal-cortex snRNA-seq data to estimate cell-type-specific associations between Alzheimer's disease and mitochondrial-related transcription. The primary gene universe will be the nuclear-encoded genes in MitoCarta3.0, with mitochondrial-DNA-encoded genes analyzed separately because of their limited and technically sensitive detection in isolated nuclei. Primary analyses will examine six major cell classes and prespecified mitochondrial pathways. We will test AD effects and planned AD-by-sex and AD-by-APOE contrasts using donor-level count models adjusted for prespecified technical and demographic covariates. Pathway inference will use full ranked gene statistics with correlation-aware testing. High-resolution clusters, three-way interactions, mtDNA transcript analyses, and expanded disease-progression outcomes will be secondary or exploratory. Statistical claims will require prespecified FDR control, effect-size reporting, model diagnostics, sensitivity analyses, and external or orthogonal validation where available.

---

# 25. Glossary

| Term | Meaning |
|---|---|
| AD | Alzheimer's disease |
| NCI | No cognitive impairment |
| APOE | Apolipoprotein E genotype |
| snRNA-seq | Single-nucleus RNA sequencing |
| Pseudobulk | Counts summed across nuclei from the same donor and cell type |
| MitoCarta | Curated inventory of mitochondrial-localized proteins/genes |
| MitoPathway | Curated mitochondrial functional gene set |
| OXPHOS | Oxidative phosphorylation |
| ETC | Electron-transport chain |
| mtDNA | Mitochondrial DNA |
| FDR | False discovery rate |
| Interaction | A test of whether an effect differs across another variable, such as sex or APOE |
| Log2FC | Log2 fold change; direction and magnitude of an expression difference |
| Leading-edge genes | Genes that contribute most strongly to a GSEA pathway signal |
| Differential abundance | A change in the proportion of a cell type or state |
| Mitonuclear coordination | Coordination between nuclear-encoded and mtDNA-encoded mitochondrial programs |

---

# 26. References and resources

1. Yu G, Thorpe A, Zeng Q, et al. *Single-cell transcriptomic analysis reveals APOE genotype-dependent sex differences in Alzheimer's disease.* Alzheimer's & Dementia. 2026;22:e71463. https://doi.org/10.1002/alz.71463
2. Mathys H, Peng Z, Boix CA, et al. *Single-cell atlas reveals correlates of high cognitive function, dementia, and resilience to Alzheimer's disease pathology.* Cell. 2023;186:4365-4385.e27. https://doi.org/10.1016/j.cell.2023.08.039
3. MIT_ROSMAP Single-Nucleus Multiomics Study, AD Knowledge Portal: https://adknowledgeportal.synapse.org/Explore/Studies/DetailsPage?Study=syn52293417
4. Rath S, Sharma R, Gupta R, et al. *MitoCarta3.0: an updated mitochondrial proteome now with sub-organelle localization and pathway annotations.* Nucleic Acids Research. 2021;49:D1541-D1547. https://doi.org/10.1093/nar/gkaa1011
5. Human MitoCarta3.0 resource: https://www.broadinstitute.org/mitocarta
6. Squair JW, Gautier M, Kathe C, et al. *Confronting false discoveries in single-cell differential expression.* Nature Communications. 2021;12:5692. https://doi.org/10.1038/s41467-021-25960-2
7. Crowell HL, Soneson C, Germain PL, et al. *muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data.* Nature Communications. 2020;11:6077. https://doi.org/10.1038/s41467-020-19894-4
8. Song D, Wang Q, Yan G, et al. *scDesign3 generates realistic in silico data for multimodal single-cell and spatial omics.* Nature Biotechnology. 2024;42:247-252. https://doi.org/10.1038/s41587-023-01772-1
9. Wu D, Smyth GK. *Camera: a competitive gene set test accounting for inter-gene correlation.* Nucleic Acids Research. 2012;40:e133. https://doi.org/10.1093/nar/gks461
10. Seattle Alzheimer's Disease Brain Cell Atlas data and documentation: https://brain-map.org/consortia/sea-ad/our-data
11. ROSMAP data dictionaries, Rush Alzheimer's Disease Center: https://www.radc.rush.edu/docs/dictionaries.htm

---

## Final recommendation

The strongest design is a **donor-level, pathway-first, cell-type-resolved analysis of nuclear-encoded mitochondrial genes**, with mtDNA transcripts handled as a carefully controlled secondary analysis. The main scientific opportunity is not simply to create a longer list of mitochondrial DEGs. It is to determine which mitochondrial systems are altered, in which cell types, under which sex and APOE contexts, and whether those systems track pathology, cognition, and replication evidence strongly enough to justify functional experiments.
