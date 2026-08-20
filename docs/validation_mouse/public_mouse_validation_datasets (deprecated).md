# Public Mouse Datasets for APOE, Sex, and Alzheimer’s Disease Validation

Date searched: August 19, 2026

## Email request

The professor is asking for a mouse-brain dataset with:

- Human APOE3 versus APOE4
- Female versus male
- AD-model versus matched non-AD background
- Single-cell or single-nucleus RNA-seq
- Preferably independent mice rather than pooled samples

## Bottom line

I did not find one publicly available sc/snRNA-seq dataset satisfying the complete APOE × sex × AD/control factorial design. The strongest exact-factor dataset is bulk RNA-seq of sorted microglia. Several single-cell datasets provide complementary subsets of the design.

## A. Study intent

The goal is external mouse validation of this repository's human sex × APOE × AD findings, particularly mitochondrial and cell-type-specific programs. The ideal experimental unit is an individual mouse, with enough mice in every factorial group for interaction testing.

## B. Best-fit study pattern

The realistic approach is multi-dataset triangulation:

1. Test the complete APOE × sex × AD interaction in the exact-factor bulk dataset.
2. Use partial single-cell datasets to localize the effects to specific cell states.
3. Do not combine these studies into one corrected expression matrix or treat cells as biological replicates.

## C. Workload options

| Configuration | Datasets | What it supports |
|---|---|---|
| Lite | GSE163857 | Direct factorial validation in sorted microglia |
| Standard — recommended | Lite + GSE213446 + GSE127893 | Factorial microglial evidence plus single-cell APOE–tau and sex–amyloid localization |
| Advanced | Standard + GSE212606 + GSE241553 + GSE185063 | Broader cell-type and model convergence |
| Publication+ | Advanced + newly generated or author-obtained full-factorial snRNA-seq | Definitive cell-type-specific APOE × sex × AD interaction testing |

## D. Primary recommendation

Use **GSE163857** as the primary validation dataset. It contains female and male mice with human APOE3 or APOE4 on either targeted-replacement control or 5xFAD backgrounds. It therefore contains all eight combinations of APOE × sex × disease background.

However, it is bulk RNA-seq of FACS-sorted microglia, not single-cell. The control strata are also small and imbalanced—apparently only approximately 1–3 mice in several control cells—so the three-way interaction will have limited power. Raw and processed data are public through [GEO GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857), with the associated publication available through [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC8551075/).

## E. Ranked public datasets

| Rank | Dataset | Design coverage | Major limitation | Recommended role |
|---:|---|---|---|---|
| **1** | [GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857) | APOE3/4 × female/male × 5xFAD/control | Bulk sorted microglia; imbalanced controls | Primary direct-factorial validation |
| **2** | [GSE213446](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213446) | APOE3/4 × P301S tauopathy/non-tau; hippocampal snRNA-seq | One library per condition; sex not exposed in GEO; tau rather than amyloid model | Best single-nucleus APOE × disease-background reference |
| **3** | [GSE127893](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127893) | Female/male × AppNL-G-F/WT × age; microglial scRNA-seq | Mouse Apoe, not human APOE3/4; two mice pooled per condition | Strongest sex × amyloid single-cell reference |
| **4** | [GSE241553](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241553) | Human APOE3/4, balanced sexes, cortex scRNA-seq; 24 mice | All groups are on an amyloid background | APOE × sex effects within AD |
| **5** | [GSE212606](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212606) | Both sexes; WT, 5xFAD and LOAD-model whole-brain single-cell profiling | LOAD mice combine APOE4 with TREM2-R47H; no APOE3 comparison | Broad cell-type and sex/disease validation |
| **6** | [GSE185063](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE185063) | APOE3/4 control-background cortical snRNA-seq | No AD background; sex balance requires sample-level audit | Possible control-only complement |
| **7** | [GSE212317](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212317) / [GSE213391](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE213391) | APOE3/4 scRNA/spatial data with strong metabolic relevance | Female-only, pooled brains and age/modality confounding | Mitochondrial/immunometabolic comparison |

The likely AD-only APOE resource already being discussed is [GSE225503](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225503), part of [GSE239999](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE239999). It includes human APOE2/3/4 on a 5xFAD background but lacks matched non-AD mice and pools multiple mice per sample.

## F. Core analysis modules

For the recommended Standard configuration:

1. Audit sample-level sex, genotype, disease background, age, tissue, pooling and mouse identifiers.
2. Convert the human mitochondrial signatures to one-to-one mouse orthologs.
3. Fit GSE163857 using a factorial model such as:

   `expression ~ sex * APOE * disease`

4. Report effect sizes and confidence intervals, emphasizing the three-way and relevant two-way interactions.
5. Score the same frozen gene modules in GSE213446 and GSE127893.
6. Compare effect directions within homologous cell types—especially microglia—without merging the studies.

## G. Validation strategy

A claim should be considered supported when:

- The corresponding GSE163857 interaction has a consistent effect with reasonable uncertainty.
- The same mouse-ortholog gene set or pathway changes in the expected direction in an appropriate single-cell dataset.
- The signal is biologically localized to relevant cell types rather than driven solely by cellular composition.

For pooled or one-library-per-group studies, use descriptive module and effect-direction validation, not ordinary inferential pseudobulk testing.

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

## H. Proposed workflow

1. Download the GSE163857 processed mouse count matrix and metadata.
2. Reconstruct the eight factorial groups and verify replicate counts.
3. Run microglial differential expression and mitochondrial module analysis.
4. Download processed matrices for GSE213446 and GSE127893.
5. Reannotate or harmonize only the relevant cell labels.
6. Calculate mouse-ortholog mitochondrial scores by cell type or library.
7. Produce a cross-study concordance table without pooling observations across studies.
8. Escalate to additional datasets only if the Standard set leaves specific conclusions unresolved.

## I. Evidence hierarchy

1. Replicated full-factor interaction in GSE163857
2. Replicated within-study single-cell effect with independent mice
3. Consistent cell-type module direction in pooled or unreplicated single-cell data
4. Cross-model pathway concordance
5. Visual similarity without replicate-aware statistics

## J. Suggested figures

- Dataset coverage matrix for APOE, sex, disease, tissue and modality
- Forest plot of factorial mitochondrial-module effects from GSE163857
- Cell-type heatmap of cross-dataset module concordance
- Microglial pathway dot plot across human PFC, 5xFAD and P301S datasets

## K. Key verified resources

- Moser et al., “Microglial transcription profiles in mouse and human are driven by APOE4 and sex”: [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8551075/) and [GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857)
- Sex and amyloid effects in AppNL-G-F microglia: [paper](https://pubmed.ncbi.nlm.nih.gov/31018141/) and [GSE127893](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127893)
- Whole-brain EasySci profiling of WT, 5xFAD and APOE4/TREM2 LOAD mice: [paper](https://www.nature.com/articles/s41588-023-01572-y) and [GSE212606](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212606)

## L. Main risks

- There is no exact public full-factorial single-cell dataset in the search results.
- Several attractive datasets contain pooled mice or only one library per condition.
- P301S tauopathy and 5xFAD/AppNL-G-F amyloid models are not interchangeable.
- Combining an AD-only study with an unrelated control-only study makes disease effects inseparable from laboratory and batch effects.
- Human-to-mouse comparisons require frozen ortholog mapping and should emphasize pathway-level convergence.

## Recommendation to the professor

Use **GSE163857** for the direct APOE × sex × AD/control test, and use **GSE213446** plus **GSE127893** for single-cell localization. Present the result as triangulated external validation, since an exact single-cell cohort does not appear to be publicly available.
