# HSR 2026–27 Research Proposal — Eric Zhuang

> **Draft:** Replace the name placeholder and revise the wording into your own voice before submission. The final Google Drive folder must also contain PDF copies of all five papers listed in Section K, with the relevant methods highlighted.

## A. Study Intent Summary

### General problem or question

Alzheimer’s disease (AD) does not affect every person or brain cell in the same way. Sex and the *APOE* genotype are two important sources of this variation, but their combined effects on cellular energy-related pathways are not fully understood. Yu et al. compared AD with no cognitive impairment (NCI) across six sex–*APOE* groups and 54 brain cell types and reported sex- and *APOE*-dependent transcriptional patterns, including differences involving mitochondrial pathways ([Yu et al., 2026, full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC13158137)). Their analysis used a single-nucleus RNA-sequencing atlas of approximately 2.3 million prefrontal-cortex nuclei from 427 ROSMAP participants ([Mathys et al., 2023, full-text PDF](https://compbio.mit.edu/publications/Mathys_Cell_23.pdf)).

Mitochondrial oxidative phosphorylation (OXPHOS), which helps cells produce ATP, is unusual because its protein subunits are encoded by two genomes. Human mitochondrial DNA encodes 13 respiratory-chain proteins, while most mitochondrial proteins are encoded by nuclear DNA. MitoCarta3.0 provides a curated inventory of 1,136 human mitochondrial genes and 149 mitochondrial pathways that can be used to define these gene sets before statistical testing ([Rath et al., 2021, full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC7778944)).

The general question is:

> **Does AD alter mitochondrial respiratory gene-expression programs or the coordination between mitochondrial- and nuclear-encoded OXPHOS genes, and do these alterations depend on sex, *APOE* genotype, and brain cell type?**

Single-nucleus data add value because the question can be tested separately in neurons, astrocytes, immune cells, oligodendrocytes, oligodendrocyte precursor cells, and vascular cells rather than averaging all brain cells together.

### Specific goal statement

The goal of this study is to use existing ROSMAP prefrontal-cortex single-nucleus RNA-sequencing data to compare AD and NCI donors across female and male *APOE* ε2-carrier, ε3/ε3, and ε4-carrier groups. I will determine which broad brain cell types show sex- or *APOE*-dependent AD changes in four prespecified mitochondrial respiratory programs and then test whether AD changes the normal expression relationship between mitochondrial-DNA-encoded and nuclear-DNA-encoded OXPHOS genes.

### Hypothesis

I hypothesize that the AD-versus-NCI mitochondrial response will not be uniform. Instead, the magnitude or direction of respiratory-program expression and mitonuclear coordination will differ between females and males and between *APOE* ε4 carriers and ε3/ε3 donors, with the clearest effects occurring in neuronal or astrocyte profiles. A null or inconsistent result will be reported rather than interpreted as support for the hypothesis.

### Scope assumptions

This is a computational, discovery-first, validation-aware study using de-identified postmortem human data already available to the project. It measures RNA abundance, not oxygen consumption, ATP production, mitochondrial number, or causation. “Sex” refers to the recorded female/male variable available in the source metadata and should not be interpreted as gender identity.

## B. Best-Fit Study Pattern

The dominant design is **key-cell/key-program prioritization**: the analysis will identify which brain cell classes show the strongest and most reliable sex- or *APOE*-modified mitochondrial expression patterns. A supporting mechanistic-association layer will test mitonuclear expression coupling. This coupling analysis can show altered transcriptional coordination, but it cannot prove mitochondrial dysfunction or a causal molecular mechanism.

## C. Four Workload Configurations

| Configuration | Goal and required data | Analysis modules | Validation and deliverable | Main limitation |
| --- | --- | --- | --- | --- |
| **Lite** | Analyze the three primary cell classes—astrocytes, excitatory neurons, and inhibitory neurons—in the existing ROSMAP data | Donor pseudobulk, two OXPHOS scores, AD-by-sex and AD-by-*APOE* contrasts | Within-dataset checks; short report with 2–3 figures | Narrow cell coverage and limited pathway context |
| **Standard** | Extend Lite to all seven broad cell classes and four frozen respiratory modules | Lite plus mitonuclear coupling, direct modifier contrasts, multiple-testing correction, and robustness analyses | Full class project with reproducible tables and about five main figures | Supports association, not functional mechanism; one human cohort |
| **Advanced** | Extend Standard to selected, prespecified fine cell types and a conditionally suitable independent cohort | Standard plus focused pathway analysis, external replication, and candidate-gene prioritization | Stronger cross-dataset evidence | Requires verified compatible metadata, access, and additional computing time |
| **Publication+** | Extend Advanced with orthogonal or experimental follow-up | Advanced plus spatial/protein support or cell-model perturbation and mitochondrial functional assays | Multi-layer manuscript-level evidence | Not currently guaranteed by school laboratory resources or the seven-month schedule |

## D. Recommended Primary Plan

The **Standard** configuration is the best fit. It is substantial enough for seven months, uses data and code already present in the repository, and directly answers the biological question without depending on unverified external data or costly experiments. The Lite analysis is the minimum executable fallback if time or computing access becomes limited. Advanced and Publication+ components are upgrades only after the Standard analysis is complete and only if suitable data or laboratory support are verified.

## E. Data Strategy and Grouping Logic

The study will reuse the Mathys et al. ROSMAP prefrontal-cortex single-nucleus atlas and the cohort rules used by Yu et al. The starting atlas contains approximately 2.3 million nuclei from 427 donors. The repository reproduces an analytic cohort of 276 donors after retaining NCI and AD, removing ambiguous sex records, excluding *APOE* ε2/ε4 and missing-genotype donors, and requiring postmortem-interval data. The six analysis strata are female and male donors within *APOE* ε2-carrier, ε3/ε3, and ε4-carrier groups.

The required metadata are donor ID, diagnosis, recorded sex, *APOE* genotype, age at death, postmortem interval, ROS/MAP study membership, cell-type label, nucleus count, raw UMI count, and mitochondrial-read fraction. The donor is the independent biological sample. Individual nuclei from one donor are repeated measurements and will not be treated as separate people.

The three prespecified primary cell classes are astrocytes, excitatory neurons, and inhibitory neurons. Immune cells, oligodendrocytes, oligodendrocyte precursor cells, and vascular cells form a secondary extension. An independent dataset is not required for the primary plan; any external cohort would be only a reference candidate until its tissue, diagnosis, sex, *APOE*, donor-level replication, and count-data metadata are verified.

## F. Methods and Variables

### Variables

| Variable role | Definition |
| --- | --- |
| **Primary independent variables** | Diagnosis (AD or NCI), recorded sex (female or male), and *APOE* group (ε2 carrier, ε3/ε3, or ε4 carrier) |
| **Primary comparisons** | AD-minus-NCI effects and direct difference-in-differences contrasts testing whether that AD effect changes by sex or *APOE* group |
| **Primary dependent variables** | Donor-level expression scores for mitochondrial-DNA OXPHOS and nuclear-DNA OXPHOS structural genes |
| **Secondary dependent variables** | Mitochondrial-translation and inner-membrane/MICOS scores; mitochondrial-minus-nuclear standardized difference; NCI-reference residual; AD-minus-NCI coupling-slope change |
| **Controlled variables** | Age at death, postmortem interval, ROS/MAP study, library size, cell class, nucleus count, and prespecified RNA-quality measurements |
| **Statistical unit** | One donor × one broad cell class expression profile |

### Analysis modules and cited methods

| Module | Purpose | Planned method and important constraint |
| --- | --- | --- |
| **Cohort and quality control** | Reproduce the eligible cohort and detect low-quality or donor-dominated profiles | Use the published inclusion logic and existing cell annotations from Yu and Mathys; do not remove nuclei only because mitochondrial RNA is high, because mitochondrial expression is a study outcome |
| **Donor pseudobulk** | Prevent millions of nuclei from being treated as millions of independent people | Sum raw gene counts within each donor and cell class. Pseudobulk methods that preserve biological replicates reduce false discoveries compared with cell-level tests that ignore replicate variation ([Squair et al., 2021, full-text PDF](https://www.nature.com/articles/s41467-021-25960-2.pdf)) |
| **Mitochondrial gene sets** | Define biological features without selecting genes after seeing the results | Freeze the 13 mitochondrial-DNA OXPHOS genes and nuclear OXPHOS structural genes using MitoCarta3.0; use mitochondrial translation and MIB/MICOS inner-membrane modules as secondary programs |
| **Respiratory-program analysis** | Test whether the AD effect differs by sex or *APOE* | Calculate donor-level, NCI-standardized program scores and fit covariate-adjusted linear models. Estimate direct interaction contrasts rather than claiming two groups differ because one is significant and the other is not |
| **Gene-level supporting analysis** | Localize a module result to individual genes | Apply an edgeR robust quasi-likelihood model to raw pseudobulk counts, with expression filtering, library-size normalization, and a multifactor design ([Chen et al., 2016, full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC4934518)) |
| **Mitonuclear coupling** | Test whether mitochondrial expression is unexpectedly high or low relative to nuclear OXPHOS expression | Measure a standardized compartment difference, a cross-fitted NCI-reference residual, and an AD-minus-NCI slope change; require compatible evidence across endpoints before making a coupling claim |
| **Error control** | Limit false-positive findings across many cell types and contrasts | Report effect sizes and 95% confidence intervals and control the false-discovery rate with the Benjamini–Hochberg method within prespecified test families |

## G. Validation and Extension Layers

- **Within-dataset validation:** verify cohort counts, raw-count conservation, gene-set coverage, model fit, and agreement between related endpoints.
- **Alternative-analysis robustness:** repeat analyses with at least 50 nuclei per donor profile, leave one donor out, bootstrap donors, balance group sizes, adjust for mitochondrial-read fraction and RNA-quality measures, and compare mean-score results with an NCI-trained principal-component score.
- **Cross-dataset validation:** attempt only if another cohort has compatible brain tissue, AD/NCI definitions, recorded sex, *APOE*, donor IDs, cell classes, raw or suitable normalized expression, and enough independent donors.
- **Orthogonal validation:** future spatial, proteomic, histologic, or mitochondrial functional measurements could test whether an RNA pattern corresponds to altered cellular function.
- **Experimental follow-up:** a cell model with controlled *APOE* genotype and sex-related biological variables could test causation, but this is outside the guaranteed Standard plan.

## H. Step-by-Step Workflow

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

1. Freeze the research question, hypotheses, cell-class hierarchy, four mitochondrial modules, contrasts, exclusion rules, and false-discovery-rate families before examining final hypothesis-test results.
2. Reproduce the 276-donor ROSMAP AD/NCI cohort and the six sex–*APOE* strata; audit missing data and donor coverage within each cell class.
3. Aggregate raw UMI counts into one pseudobulk profile for each eligible donor and broad cell class; require at least 20 nuclei for the primary analysis.
4. Calculate quality-control summaries and confirm that all pseudobulk counts equal the sum of their source nuclei.
5. Construct NCI-standardized scores for the mitochondrial-DNA OXPHOS, nuclear OXPHOS, mitochondrial-translation, and MIB/MICOS inner-membrane modules.
6. Fit covariate-adjusted models for AD-versus-NCI effects within each sex–*APOE* stratum and calculate the seven prespecified direct sex/*APOE* modifier contrasts.
7. Test the three mitonuclear-coupling endpoints in the primary cell classes, followed by the four secondary cell classes.
8. Apply Benjamini–Hochberg correction separately to the prespecified primary and secondary result families.
9. Run nucleus-threshold, donor-bootstrap, leave-one-donor-out, group-balancing, score-construction, and RNA-quality sensitivity analyses.
10. Produce figures and tables that report positive, null, unstable, and inestimable results, then write conclusions limited to cell-type-specific RNA-expression associations.

## I. Validation Evidence Hierarchy

The Standard plan can provide **moderate evidence of a reproducible within-cohort transcriptional association** if the same signal survives direct interaction testing, multiple-testing correction, alternative scoring, and donor-resampling checks. It cannot establish altered respiration, reduced ATP, disease causation, or clinical usefulness. Cross-cohort replication would strengthen the evidence, while protein, spatial, or functional experiments would be required for a mechanistic claim.

## J. Figure, Deliverable, Timeline, and Feasibility Plan

### Planned figures and deliverables

1. Cohort, grouping, and pseudobulk workflow diagram.
2. Heatmap of AD-associated effects for four mitochondrial programs across sex, *APOE*, and cell class.
3. Forest plot of direct sex- and *APOE*-modifier contrasts.
4. Mitonuclear-coupling scatterplots and endpoint forest plots for the three primary cell classes.
5. Robustness and validation summary showing which findings survive all prespecified checks.

The final package will include a reproducible analysis script, frozen configuration files, quality-control tables, complete result tables, five main figures, supplemental robustness figures, and a written report. Advanced-only fine-cell, external-cohort, or experimental figures will not be required for successful completion of the Standard plan.

### Seven-month timeline

| Month | Milestone |
| --- | --- |
| 1 | Finalize literature review, cohort rules, hypotheses, gene sets, and contrasts |
| 2 | Audit metadata and expression objects; construct and validate donor pseudobulk profiles |
| 3 | Complete respiratory-module models and direct sex/*APOE* contrasts |
| 4 | Complete mitonuclear-coupling analyses |
| 5 | Run multiple-testing correction and all robustness analyses |
| 6 | Evaluate conditional external validation and create final figures and tables |
| 7 | Interpret results, write the report, revise figures, and prepare the presentation |

### Feasibility

The project requires no new human samples, reagents, or animal work. The processed expression objects, metadata, mitochondrial annotations, analysis code, and computing workflow are already present in the repository. A smaller local analysis can be used for code testing, while the full analysis can run on the available high-memory computing environment. The main feasibility risks are subgroup size, controlled-data authorization, computation time, and the possibility of null results; none requires purchasing laboratory equipment.

## K. Five-Item Primary/Secondary Paper Reference List

- [Yu et al. (2026), “Single-cell transcriptomic analysis reveals APOE genotype-dependent sex differences in Alzheimer’s disease” — full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC13158137)
- [Mathys et al. (2023), “Single-cell atlas reveals correlates of high cognitive function, dementia, and resilience to Alzheimer’s disease pathology” — full-text PDF](https://compbio.mit.edu/publications/Mathys_Cell_23.pdf)
- [Rath et al. (2021), “MitoCarta3.0: an updated mitochondrial proteome now with sub-organelle localization and pathway annotations” — full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC7778944)
- [Squair et al. (2021), “Confronting false discoveries in single-cell differential expression” — full-text PDF](https://www.nature.com/articles/s41467-021-25960-2.pdf)
- [Chen, Lun, and Smyth (2016), “From reads to genes to pathways: differential expression analysis of RNA-Seq experiments using Rsubread and the edgeR quasi-likelihood pipeline” — full-text PDF](https://europepmc.org/api/getPdf?pmcid=PMC4934518)

## L. Self-Critical Risk Review

- **Strongest part of the design:** a large human single-nucleus dataset is analyzed at the donor level with prespecified mitochondrial gene sets and direct sex/*APOE* interaction contrasts.
- **Most assumption-dependent part:** module scores are assumed to summarize biologically meaningful respiratory programs from postmortem RNA abundance.
- **Most likely false-positive source:** small sex–*APOE* subgroups combined with many cell-type and pathway comparisons.
- **Easiest result to overinterpret:** an altered RNA-expression score or correlation could be incorrectly described as impaired mitochondrial energy production.
- **Likely reviewer criticisms:** one cohort, postmortem confounding, unequal subgroup sizes, limited mitochondrial RNA capture, ancestry homogeneity, and absence of functional validation.
- **Fallback if the main signal does not validate:** report the prespecified null result, quantify the precision and detectable effect sizes, identify which modules and groups were adequately testable, and present the validated workflow without promoting exploratory findings to confirmatory conclusions.
