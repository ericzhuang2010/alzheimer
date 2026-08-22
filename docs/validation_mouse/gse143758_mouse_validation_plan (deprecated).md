# GSE143758 Mouse snRNA-seq Validation Plan

**Status:** no-go for the intended disease-by-sex validation; conditional auxiliary male-disease plan only<br>
**Date:** 2026-08-22<br>
**Selected resource:** [GEO GSE143758](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758)<br>
**Recommended workload:** no execution for the sex endpoint; Standard only if the change to an auxiliary male-disease question is explicitly accepted<br>
**Intended primary endpoint:** disease-by-sex interaction; `not_testable` in GSE143758<br>
**Conditional auxiliary endpoint:** mouse-level 5xFAD-minus-WT effects in the seven-month male hippocampus, evaluated in seven human-aligned broad cell contexts with a metadata-gated block design<br>
**Sex endpoint:** `not_testable` from the public deposit; the paper reports only one female mouse per genotype, and those female data are absent from GEO/SRA<br>
**APOE endpoint:** `not_testable`; GSE143758 has no human APOE isoform manipulation<br>
**Proposed implementation root:** `scripts/validation_mouse/`<br>
**Proposed result root:** `results/validation_mouse/gse143758/`

This plan replaces the abandoned [GSE163857 microglia plan](./gse163857_mouse_microglia_validation_plan.md). It retains the useful principles of animal-level replication, frozen ortholog mapping, and separate estimation within each species. It does not retain that plan's microglia-only scope, APOE3/APOE4 factorial design, bulk-RNA assumptions, or exact mouse-to-human APOE matching.

## A. Study Intent Summary

### Research question

The intended primary question is:

> Does the 5xFAD-minus-WT effect differ between female and male mice?

Its formal estimand would be:

```text
(5xFAD_Female - WT_Female) - (5xFAD_Male - WT_Male)
```

That interaction cannot be estimated from the public GSE143758 deposit. GEO/SRA do not expose a sex field, but every public record that maps to Supplementary Table 1 maps to a male mouse. The associated paper reports one female WT and one female 5xFAD mouse, but their expression data are not in the GEO processed matrices or current SRA manifest. Even if those two samples are obtained, one animal per female genotype supplies no within-group variance and cannot support an inferential disease-by-sex interaction. Missing or unreplicated evidence must remain `not_testable`, never zero. Therefore, GSE143758 fails the go gate for its intended sex-validation role.

If a change of question is explicitly accepted, the dataset-supported auxiliary question is:

> In seven-month-old male 5xFAD mice, which cell-type-specific disease effects and prespecified mitochondrial or key-driver programs show directional concordance with frozen human AD-minus-NCI references?

### What the study can and cannot answer

| Question | GSE143758 evidence | Planned status |
|---|---|---|
| Male 5xFAD versus WT effects at seven months | Four WT and four 5xFAD mice, all major hippocampal cell classes | Conditional auxiliary analysis |
| Disease-by-sex interaction | All mapped public records correspond to male mice; GEO/SRA omit sex | `not_testable` |
| Descriptive female replication | One female mouse per genotype is reported but not deposited | Access-dependent and descriptive only |
| Human APOE2/APOE3/APOE4 modifier replication | No human APOE knock-in factor | `not_testable` |
| Astrocyte disease changes across age | Twenty-eight male mice in an unbalanced, batch-linked time course | Secondary/exploratory |
| Independent cortical replication | Four cortex samples from mice also used for hippocampus | Descriptive region sensitivity only |

### Biological and translational aim

The plan tests whether disease-related transcriptional organization is conserved across species, not whether 5xFAD recapitulates late-onset human AD. The mouse model is an aggressive familial-amyloid model, the primary mouse tissue is hippocampus, and the main human ROSMAP reference is prefrontal cortex. Therefore, permitted language is **cross-species concordance**, **external support**, or **lack of support**. The analysis cannot establish human disease mechanism, sex modification, or APOE-genotype specificity.

## B. Best-Fit Study Pattern

The dominant pattern is a **validation-aware, key-cell/key-state study** with a secondary cell-atlas and composition layer.

- The mouse is the biological replicate.
- Raw UMI counts are aggregated to `mouse x broad cell context` before expression inference.
- Library partitions, hemispheres, and nuclei are repeated technical or cellular measurements, not independent animals.
- Published cell labels are reused only after exact cell-ID reconciliation and marker review.
- Mouse and human effects are estimated separately and compared only after one-to-one ortholog mapping.
- Prespecified respiratory modules and Phase 18 candidate units are evaluated before exploratory pathways.
- Trajectory, cell-cell communication, and causal network reconstruction are not required for the conditional auxiliary question.

The paper reports tests that matched animals by batch/littermate, but Supplementary Table 1 does not expose a litter or pair-ID field. `G1`, `G3`, `S1`, and `S2` are therefore candidate reconstructed pairs, not source-declared pair IDs. The auxiliary count model uses pairing only after those relationships are independently corroborated and frozen. If pairing cannot be verified without using expression outcomes, the prespecified fallback is a lysis-protocol block.

## C. Four Workload Configurations

Each configuration is a strict superset of the preceding one.

| Configuration | Included work | Appropriate claim |
|---|---|---|
| **Lite** | Main seven-month male hippocampus; exact published-cell join; seven broad cell contexts; mouse-level pseudobulk; 5xFAD-versus-WT DEG; two direct respiratory modules; effect sizes, CIs, and influence checks under the frozen design | Within-dataset male disease association |
| **Standard — recommended only for the auxiliary question** | Lite plus `HR00` descriptive human-reference reconstruction or explicit fine-cell fallback, all four frozen respiratory modules, animal-level composition, one-to-one ortholog concordance with each human male APOE stratum, all assessable frozen Phase 18 units, and the male astrocyte time-course sensitivity | Directional cross-species male disease concordance with prespecified program analysis |
| **Advanced** | Standard plus conditional raw-SRA reprocessing, independent broad-cell annotation, all-age/all-cell reconstruction if raw provenance is resolved, cortex sensitivity, and an author-data audit for the two reported female samples | Processing robustness and broader descriptive context |
| **Publication+** | Advanced plus a genuinely sex-balanced independent mouse cohort, orthogonal RNA/protein/histology validation, and candidate perturbation/rescue where causal language is intended | Replicated sex-dependent or functional claims |

### Recommendation

The primary decision is **no-go for sex validation**. Do not execute any workload under a sex-validation label.

If the changed male-only auxiliary question is explicitly accepted, use **Standard**. It answers the strongest question supported by the deposited data while retaining the project-specific mitochondrial and Phase 18 targets. Advanced raw reprocessing is not a prerequisite because the deposited matrices contain integer raw UMI counts and the current raw manifest does not unambiguously reconstruct every main-cohort library. Publication+ cannot be achieved with GSE143758 alone.

## D. Recommended Primary Decision and Conditional Auxiliary Plan

### Endpoint hierarchy

| Tier | Endpoint | Role |
|---|---|---|
| 0 | Disease-by-sex interaction | Intended primary; `not_testable`, causing the no-go decision |
| 1 | Mouse-level 5xFAD-minus-WT effects for the two direct respiratory modules in seven broad cell contexts | Prespecified auxiliary male analysis |
| 2 | Genome-wide pseudobulk DEG, cell-composition effects, all four respiratory modules, and one-to-one ortholog effect concordance | Prespecified auxiliary secondary |
| 3 | All assessable Phase 18 `broad_network x key_driver x case_id` units and their frozen target sets | Prespecified auxiliary secondary, conditional on manifest freeze |
| 4 | Male astrocyte age-by-genotype patterns and cortex direction checks | Exploratory/sensitivity |
| 5 | APOE modifier claims | `not_testable` |

The two direct modules are `mtdna_oxphos_13` and `nuclear_oxphos_structural_86`. `mitochondrial_translation_155` and `mib_micos_inner_membrane_19` are supporting programs. Their definitions survive in [the frozen module table](../../config/phase13_respiratory_modules.tsv) and [Phase 13 configuration](../../config/phase13_respiratory_modifier.yml), but they are prospective readouts here—not already confirmed human findings. The prior Phase 13 analysis produced zero supported tests and must be represented as inconclusive, as documented in the [Phase 13 figure proposal](../figures/analysis/phase_13_respiratory_modifier/phase13_figure_proposal.md).

### Conditional auxiliary cell-context crosswalk

The published 23 mouse clusters are collapsed to the seven broad networks used by the human Phase 18 work. This broad mapping is the auxiliary mouse summary because hippocampal CA/DG/Sub fields do not have one-to-one counterparts among ROSMAP prefrontal cortical fine types.

| Mouse context | Published cluster(s) | Exact human expression reference | Comparison mode |
|---|---|---|---|
| Astrocytes | 1 `Astrocytes.1`; 2 `Astrocytes.2` | `Ast CHI3L1`, `Ast DPP10`, and `Ast GRM3` | Existing fine-cell effects separately; conditional direct donor-level broad aggregate |
| Excitatory neurons | 12 and 14-23 excitatory/DG/CA/Sub clusters | Every admitted ROSMAP excitatory fine label, enumerated in the mapping manifest | Existing fine-cell effects separately; conditional direct donor-level broad aggregate; no layer/field equivalence claim |
| Inhibitory neurons | 7-9 GABAergic clusters | Every admitted ROSMAP inhibitory fine label, enumerated in the mapping manifest | Existing fine-cell effects separately; conditional direct donor-level broad aggregate |
| Microglia | 11 `Microglia` | `Mic P2RY12`, `Mic TPT1`, and `Mic MKI67` | Fine labels separately; CAMs and T cells excluded; Phase 13 `immune_cells` is not a microglia substitute |
| OPCs | 10 `OPCs` | Exact human fine label `OPC` | Existing fine-cell effect; conditional donor-level `opcs` aggregate |
| Oligodendrocytes | 6 `Oligo` | Exact human fine label `Oli` | Existing fine-cell effect; conditional donor-level `oligodendrocytes` aggregate |
| Vasculature cells | 4 endothelial, 5 fibroblast, and 13 pericyte | `End`, `Fib FLRT2`, `Fib SLC4A4`, and `Per` | Fine labels separately; broad Phase 13 vasculature is a partial match because mouse SMC is absent |

Cluster 3 (`Ependymal`) has no direct target in the current human reference and remains descriptive. Every mapping must pass a marker and contamination audit before it is frozen; label similarity alone is insufficient.

Create a frozen mapping manifest with one row per `mouse_cluster x mouse_broad_context x exact_human_fine_label x human_broad_context x comparison_mode`. Never obtain a broad human effect by averaging fine-cell log fold changes. A broad effect is valid only when raw counts are aggregated directly to `donor x declared human broad context` before modeling.

### Human-reference readiness gate

The current checkout does **not** contain an authoritative, released ROSMAP broad-context effect table. The available references have different roles:

1. **Existing fine-cell descriptive track:** the exact Phase 08 tables under [`results/minerva_production/08_mast/`](../../results/minerva_production/08_mast/) contain cell-level MAST effects. Use each exact fine-cell row separately for sign/rank displays. Do not pool them, treat nuclei as donors, or use their `q` values as a donor-level human support gate.
2. **Conditional donor-level descriptive module track (`HR00`):** [`respiratory_pseudobulk_counts.rds`](../../results/minerva_production/13_respiratory_modifier/respiratory_pseudobulk_counts.rds) survives, but the corresponding Phase 13 result tables and scripts are absent/deprecated. Before mouse unblinding, checksum and validate that RDS and reconstruct a descriptive reference using the frozen [Phase 13 configuration](../../config/phase13_respiratory_modifier.yml). Fit the configured model `~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled + study` with HC3 covariance, then materialize male AD-minus-NCI module effects for `e2`, `e33`, and `e4`.

For `HR00`, a stratum effect is estimable only with a full-rank design and at least five donor profiles per diagnosis arm. Enumerate all 42 direct-module slots (`7 human contexts x 3 male APOE strata x 2 direct modules`) and the separate 42 supporting-module slots, but report donor counts, estimates, HC3 95% CIs, and nominal `p` values as descriptive reconstruction outputs only. Do **not** create a new BH family or human support gate from this retrospectively narrowed set. Phase 13 defined these stratum effects as descriptive components, and its complete formal family produced zero supported findings; reconstructing the components cannot change that historical evidence state. `immune_cells` and vasculature rows retain explicit partial-mapping flags and cannot support a strict microglia or SMC-free vasculature match.

`HR00` must release a source/hash manifest, donor counts, model diagnostics, complete structural slots, effect/CI/nominal-`p`, the inherited Phase 13 evidence status, and context composition under `results/validation_mouse/gse143758/HR00_human_reference/`. If it is not reconstructed successfully, donor-level broad directional comparison is `not_testable`; only the fine-cell descriptive track may run. Whether reconstructed or not, neither Phase 08 nor `HR00` can supply `supported_concordance` in this study.

### Conditional auxiliary estimand and sign convention

For gene or module `g` in broad cell context `c`:

```text
mouse_effect[g,c] = log2 expression(5xFAD male) - log2 expression(WT male)
```

Positive values mean higher expression in 5xFAD. Human effects retain the repository convention:

```text
human_effect[g,c,stratum] = AD - NCI
```

The mouse effect is compared separately with human male `e2`, `e33`, and `e4` effects. Those comparisons are stratified human references, not matched mouse genotypes. Female human effects may be shown as context but cannot convert the male-only mouse analysis into sex validation.

The formal human sex targets remain, for each `a` in `{e2, e33, e4}`:

```text
sex_F_minus_M__a = (AD_F_a - NCI_F_a) - (AD_M_a - NCI_M_a)
```

They stay in the output manifest as human references with mouse status `not_testable`. Human APOE-modifier contrasts likewise remain out of scope for this non-APOE mouse model.

### Small-sample interpretation

The primary cohort contains eight mice arranged as four candidate matched pairs. If VM02 independently verifies those pairs, a paired t-test sensitivity calculation at 80% power and two-sided alpha 0.05 is approximately `d_z = 2.13`, before multiple-testing correction. Conditional on exchangeability and symmetry of the paired differences, an exact sign-flip diagnostic would have only 16 assignments and a minimum attainable two-sided `p = 0.125`. It is not a design-based randomization test because genotype was inherited rather than randomized, and it cannot pass BH 0.05 across the 14 primary module hypotheses. If pairing is not verified, report the corresponding sensitivity for the frozen lysis-block model instead. Consequently:

- thousands of nuclei improve expression measurement but not biological replication;
- gene-level FDR discoveries will be limited to unusually large and consistent effects;
- shrunken effect sizes, 95% CIs, animal-level direction, and design-appropriate influence stability lead interpretation;
- no post-hoc observed-power calculation is permitted; report design sensitivity instead; and
- a non-significant result is not evidence that the effect is absent.

## E. Data Strategy and Example Dataset Directions

### Verified public-data inventory

Facts below were checked on 2026-08-22 against the [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758), [GEO family SOFT](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143758/soft/GSE143758_family.soft.gz), [Habib et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262034/), its [Supplementary Table 1](https://pmc.ncbi.nlm.nih.gov/articles/instance/9262034/bin/NIHMS1578105-supplement-1578105_Sup_Tables.xlsx), the official [Figure 1 source-data workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41593-020-0624-8/MediaObjects/41593_2020_624_MOESM3_ESM.xlsx), and [SRA SRP243446](https://www.ncbi.nlm.nih.gov/sra?term=SRP243446).

| Resource | Deposited content | Audit result | Planned use |
|---|---|---|---|
| Paper supplement inventory | 34 unique mice and 40 tissue/library rows | 32 male plus two female mice; four cortex rows reuse hippocampal mice and two main-cohort mice have bilateral partitions | Cohort reconstruction |
| [Seven-month hippocampus, all nuclei](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143758/suppl/GSE143758_Admouse_Hippocampus_7m_AllNuclei_UMIcounts.txt.gz) | 18,438 unique genes x 55,367 nucleus columns; ten library prefixes | Eight male mice, four WT and four 5xFAD; ten partitions, nine GSM/SRX records, and ten SRRs; 54,769 cells match official source annotations after parser-level dequotation and 598 matrix cells do not | Auxiliary primary |
| [Hippocampal astrocyte time course](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143758/suppl/GSE143758_Admouse_Hippocampus_3TimeCourses_Astrocytes_WT_AD_Aging.csv.gz) | 20,970 genes x 25,076 nucleus columns; 28 male mice | Paper reports 23,863 retained astrocytes; age, batch, chemistry, and genotype support are unbalanced | Secondary |
| [Seven-/ten-month cortex astrocytes](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143758/suppl/GSE143758_Admouse_Crtx_7-10m_Astrocytes_UMIcounts.csv.gz) | 19,468 genes x 6,312 nucleus columns; four male mice | GEO calls the region `Cortex`; the paper specifies prefrontal cortex; paper reports 6,062 retained cells; the same mice also contributed hippocampus | Descriptive region sensitivity |
| GEO/SRA submission | 32 supplement-mapped male mice, 38 tissue/library rows, 37 GSM/SRX experiments, and 86 SRR runs | Sex is reconstructed from the supplement; one main-cohort GSM/SRX bundles two generically named SRRs, so its L/R run mapping is not explicit | Conditional Advanced input |
| Female hippocampus | HC_447 WT and HC_462 5xFAD, one mouse each, are reported in the supplement | Absent from the three GEO matrices and current GSE/SRA manifest | Access audit only; inferential sex analysis prohibited |

The two files ending in `.csv.gz` are semicolon-delimited. The serialized cell IDs include enclosing quote characters, which must be removed by the file parser before comparison. After parser-level dequotation, use exact IDs; no fuzzy rewriting is permitted. The all-nuclei tab-delimited matrix also omits the expected top-left header placeholder, so its header and data rows differ by one field. Import code must test these conditions explicitly rather than relying on file extensions or generic readers.

The main matrix contains 1,020,856,746 count entries before labels. A generic dense double-precision representation needs more than 8 GB for the numeric payload alone and substantially more with parser/object overhead. VM03 must stream or chunk cell summaries and pseudobulk aggregation, or first convert the matrix to a validated on-disk sparse format; unrestricted dense import is prohibited.

The model is heterozygous Tg6799/5XFAD on a C57BL/6-SJL background, with non-transgenic littermate controls. GEO labels WT records as C57BL/6. Preserve both source descriptions and do not reinterpret the controls as an unrelated pure-C57BL/6 cohort.

[Single Cell Portal SCP302](https://singlecell.broadinstitute.org/single_cell/study/SCP302/mouse-alzheimers-and-disease-astrocytes) currently lists 7,345 cells plus metadata and diffusion coordinates, but reports `gene_count=0` and no expression matrix; portal downloads also require authentication. It does not restore the missing female counts and is a supporting availability record, not an analysis input.

### Main-cohort mouse map

The expected biological map must be independently reproduced from the supplement and cell-ID prefixes before expression values are examined.

| Candidate pair | WT partition(s) | 5xFAD partition(s) | Lysis | Biological units |
|---|---|---|---|---:|
| `G3` | `HipR-WT-G3-2w` | `HipR-AD-G3-2w` | EZ | 2 mice |
| `G1` | `HipR-WT-G1-4w` | `HipR-AD-G1-4w` | EZ | 2 mice |
| `S1` | `Wt-Hip-S1-L` | `Untreated-Hip-S1-L` | NP40 | 2 mice |
| `S2` | `Wt-Hip-S2-L`, `Wt-Hip-S2-R` | `Untreated-Hip-S2-L`, `Untreated-Hip-S2-R` | NP40 | 2 mice, not 4 |

The S2 left/right partitions must be summed within mouse before inference. `Untreated` denotes baseline 5xFAD rather than a treatment arm. These candidate pair labels must not enter the model until their batch/littermate interpretation passes the independent VM02 gate.

### Mandatory discrepancy register

The frozen manifest must preserve both source values and adjudicated values for every discrepancy.

| Discrepancy | Required adjudication |
|---|---|
| 55,367 deposited main-matrix cells versus 54,769 official analysis cells | After parser-level CSV dequotation, require an exact source-annotation join; exclude and enumerate the 598 unmatched matrix-only cells from the primary analysis; prohibit fuzzy ID normalization |
| Figure 1 broad astrocytes versus six-state astrocyte reference | The all-cell sheet has 7,716 cluster-1/2 astrocytes; the six-state sheet has 7,345 IDs, of which 7,341 occur in the count matrix/all-cell sheet; retain 7,341 usable state-reference cells, enumerate four missing IDs and 375 broad astrocytes omitted from the state sheet, and never equate the two label systems |
| 25,076 deposited time-course astrocytes versus 23,863 reported analysis cells | Reconstruct the retained set if identifiers permit; otherwise run a documented re-QC sensitivity and do not call the sets identical |
| 6,312 deposited cortical astrocytes versus 6,062 reported analysis cells | Same rule as the time course |
| Supplement labels `CRTX_7mAD343` as WT and `CRTX_10mWT124` as AD | Adjudicate from mouse ID, GEO title/strain, and paired hippocampus record; retain the original typo in provenance columns |
| `WT_M768_13.3m` versus matrix prefix `M268` | Freeze an alias only after multi-source confirmation |
| `HIP_6wWT330` versus `WT-Hip-6w-S331` | Freeze an alias only after multi-source confirmation |
| Ten processed main prefixes, nine GSM/SRX records, and ten SRRs | GSM4276892/SRX7583992 contains two generically named runs; do not claim exact L/R raw reconstruction until their mapping to `Untreated-Hip-S2-L/R` is resolved |
| GEO omits sex | Restore sex from the paper supplement and validate male main-cohort assignment with sex-chromosome expression as QC, not as a substitute for metadata |
| Supplement labels 30 rows as 10x v2 and ten as v3, while the paper text reports 22 v2 and ten v3 samples | Preserve both source statements and reconcile what each denominator counts before raw reprocessing |
| Supplement assigns all six main NP40 rows to batch 2, while matrix prefixes include `NP40.Batch1` and `NP40.Batch3` | Keep source-specific batch fields; do not collapse them into one adjudicated batch without raw/read-structure evidence |
| GEO uses `Cortex`, while the paper specifies prefrontal cortex | Preserve the GEO source value and use `prefrontal cortex per paper` only as an adjudicated description |

### Data and artifact locations

Proposed implementation locations are:

```text
data/gse143758/                              # local large inputs; never commit raw matrices/FASTQ
config/validation_mouse/gse143758_mouse_validation.yml
scripts/validation_mouse/
tests/validation_mouse/
results/validation_mouse/gse143758/
```

Before implementation, add an explicit mouse-validation artifact policy to `.gitignore`. Commit only compact manifests, results, logs, and checksums authorized by that policy. Every remote input must have a URL, retrieval date, byte size, and SHA-256 checksum.

## F. Core Analysis Modules and Method Choices

### 1. Metadata, cell identity, and QC

- Parse each nucleus ID to a library partition, then map partition to mouse, pair, genotype, hemisphere, lysis protocol, age, sex, tissue, chemistry, and source accession.
- Enforce one-to-one nucleus-to-library and library-to-mouse relationships.
- Remove only serialization quotes through the declared parser, then join the all-nuclei count matrix to the 54,769 official source-data annotations by exact canonical cell ID; prohibit broader fuzzy normalization.
- Exclude the 598 matrix-only cells from the primary analysis; retain them in an exclusion manifest.
- Keep the 7,716 broad cluster-1/2 astrocytes distinct from the 7,341 count-backed six-state reference cells; preserve the four missing state IDs and 375 broad-only astrocytes in explicit reconciliation tables.
- Summarize genes detected, UMI depth, mitochondrial fraction, sex-chromosome expression, doublet score/flag where available, and cell counts per `mouse x published cluster`.
- Review canonical positive and negative markers within each published cluster. Annotation review is blinded to genotype-level results.
- Integrated or corrected embeddings may be used for QC visualization only. DE and module tests use unintegrated raw counts or derived mouse-level summaries.

### 1a. Published biological calibration (non-target)

Before interpreting mitochondrial or Phase 18 results, reproduce a small, frozen calibration panel from the paper and source workbooks:

- higher within-astrocyte DAA-state representation and lower homeostatic/Gfap-low representation in 5xFAD;
- higher microglial representation in 5xFAD in the main all-nuclei cohort; and
- directional enrichment of the paper-defined DAA and DAM marker programs in their appropriate published cell context.

Use mouse-level proportions or pseudobulks and show every animal. Calibration is a pipeline positive control, not a ROSMAP endpoint, and its tests form a separate family. It cannot alter cell thresholds, module definitions, target sets, or the support gate. A failed calibration triggers an annotation/provenance review and makes downstream null results less interpretable; it does not authorize threshold tuning until the expected pattern appears.

### 2. Mouse-level pseudobulk and DEG

For each frozen broad cell context:

1. Sum integer UMIs by `gene x mouse`, combining hemispheric and library partitions from the same mouse.
2. Require the context in all eight mice and at least 20 retained nuclei per mouse for the prespecified auxiliary-primary tier. A 50-nucleus rule is a frozen sensitivity tier. Contexts failing 20 nuclei in any mouse become `not_testable` for that tier and may be descriptive.
3. Retain a gene if it has at least ten counts in at least four of the eight mouse pseudobulks for that context. Record all filtered genes.
4. Fit DESeq2 independently in each context using raw integer counts.

If the four pair IDs pass the metadata gate, use:

```r
design = ~ pair_id + genotype
contrast = 5xFAD - WT
```

If pairing cannot be independently verified, freeze the fallback before results:

```r
design = ~ lysis_protocol + genotype
contrast = 5xFAD - WT
```

Do not include both pair and lysis in the same eight-mouse model because pair already absorbs its batch/lysis structure. DESeq2's default Wald test and interval use an asymptotic normal approximation. Report the unshrunk log2 fold change with its Wald standard error and 95% CI separately from the shrunken log2 fold change. If an apeglm interval is produced, label it as a shrinkage/posterior interval rather than a frequentist Wald CI. Also report the Wald statistic, raw `p`, BH `q`, base mean, per-mouse counts, and Cook's/influence flags. Run edgeR quasi-likelihood as a method sensitivity, not as an opportunity to choose the more significant result.

The frozen model assumes independent mice after within-mouse collapsing, a full-rank design, and an adequate negative-binomial mean-dispersion fit. Validate those assumptions with design-rank checks, size-factor and library-size review, dispersion-fit plots, sample distances, and influence diagnostics. With eight mice, a formal residual-normality test is not a reliable model-selection device; diagnostics trigger transparent sensitivity analysis, not outcome-driven switching.

If pairing is verified, the prespecified robustness analysis is leave-one-pair-out refitting. Under the lysis fallback, use leave-one-mouse-out refitting plus genotype effects displayed separately within each lysis stratum. Report direction retention, estimate range, and whether any unit changes the scientific status. Do not remove a biologically valid mouse solely because it weakens a result.

For broad contexts that merge biologically distinct published clusters, repeat module and leading-gene estimates at published-cluster resolution where support permits. Display heterogeneity and flag any broad effect driven by a genotype-related subtype-composition shift; do not automatically interpret the pooled broad effect as cell-intrinsic regulation.

### 3. Cell-composition analysis

- Compute published-cluster and broad-context proportions per mouse after the exact retained-cell join.
- If pairing is verified, lead with the mean within-pair 5xFAD-minus-WT difference, its model-based 95% CI with an explicit small-sample assumption caveat, the median/range, and all four pairwise differences. Under the fallback, lead with the lysis-adjusted effect and show every animal.
- Use a pair-blocked model or conditional exact sign-flip diagnostic only after pair verification and an explicit exchangeability/symmetry assumption; acknowledge that the exact two-sided `p` cannot be below 0.125 with four pairs.
- Treat all proportions jointly in a global compositional sensitivity when feasible; individual-cell-type `q` values form a separate BH family.
- Report lysis-specific capture patterns. A composition change is not automatically a biological abundance change because nuclei recovery differs by protocol.
- For each bilateral S2 mouse, compare the primary pooled-cell proportion with the mean of the left- and right-partition proportions. This sensitivity prevents two captured hemispheres from implicitly receiving a different composition weight than single-partition mice.

### 4. Respiratory-module analysis

Use the four frozen human module definitions without outcome-driven editing. Map them to mouse through a versioned one-to-one ortholog table, then apply the existing minimum-coverage rules from the Phase 13 configuration.

Two complementary analyses are required:

1. **Auxiliary-primary animal-level module score:** equal-weight mean of gene-wise standardized variance-stabilized pseudobulk expression. If pairs are verified, fit `score ~ pair_id + genotype` and report the genotype estimate, t-based 95% CI and test with three residual degrees of freedom, and all four paired differences. Under the fallback, fit `score ~ lysis_protocol + genotype`, report five residual degrees of freedom, and show all eight animals. Inspect residuals graphically; do not use a low-powered normality test to select the model.
2. **Corroborative competitive gene-set test:** CAMERA on TMM/voom-transformed mouse pseudobulks with the same frozen design, the context's tested genes as the universe, and inter-gene correlation retained. CAMERA direction is relative to the background gene universe, not a self-contained module-shift estimate. Report direction, correlation estimate, raw `p`, and BH `q`, and flag its fragility under the paired model's three residual degrees of freedom.

The 14 direct-module score tests (`7 contexts x 2 modules`) form the sole auxiliary-primary support family. `supported` requires that score family's BH `q < 0.05`; CAMERA cannot independently promote a failed score result. The 14 direct-module CAMERA tests are a separate corroboration family, and the two supporting modules form separately labeled secondary score and CAMERA families. Testability requires both ortholog and within-context expression coverage; mtDNA genes must not be interpreted from percent-mito QC metrics.

### 5. Cross-species concordance

- Freeze a human-source manifest that records cohort, region, contrast, cell resolution, replicate unit, statistical engine, and evidence status. Prefer donor-level pseudobulk estimates for effect comparison. If the only available gene-level reference is the Phase 08 cell-level MAST branch, use its effect signs and ranks descriptively. Neither Phase 08 nor the retrospective `HR00` reconstruction may supply a confirmatory human gate.
- Freeze Ensembl releases and retain only unambiguous one-to-one mouse-human orthologs.
- Record unmapped, one-to-many, symbol-collision, expression-filtered, and admitted genes.
- Never merge mouse and human raw expression or compare absolute expression magnitudes.
- Compare mouse male 5xFAD-minus-WT effects with ROSMAP male AD-minus-NCI effects in `e2`, `e33`, and `e4` separately. For Phase 08, keep every mapped human fine-cell comparison separate. For `HR00`, compare only directly aggregated donor-level broad module effects and retain partial-context flags.
- Lead with the effect scatter, admitted-ortholog count, sign agreement, Spearman effect correlation, concordance of module directions, and enrichment of frozen human fine-cell ranked signatures in mouse. A naive gene-wise bootstrap treats correlated genes as independent; any such CI is descriptive only. An inferential CI requires a correlation-aware block-resampling scheme frozen without mouse-outcome selection.
- Require at least 20 admitted orthologs for an effect correlation; otherwise mark it `not_testable`. Module-specific tests use the frozen module coverage rules instead.
- Enumerate every Phase 08 signature-enrichment slot, expected direction, coverage gate, and mapped fine-cell label before mouse unblinding; apply BH across that complete declared family. These results remain descriptive even when their enrichment `q` passes because the human source is cell-level MAST. Effect correlations are descriptive summaries rather than separate significance gates.
- Treat human female effects as contextual panels only. The formal human sex-modifier contrasts remain human references and are not directly replicated by male-only mice.

Cross-species comparison labels are:

| Label | Definition |
|---|---|
| `directionally_concordant` | Same sign with adequate mapping and coverage; descriptive regardless of significance |
| `directionally_opposed` | Opposite signs with adequate mapping and coverage; descriptive when donor-level uncertainty is unavailable |
| `supported_concordance` | Same sign, strict context mapping, mouse direct-module score BH gate passed, and a genuinely independent human confirmation passed under a prospectively declared family; unavailable from Phase 08, Phase 13, or `HR00` |
| `discordant` | Opposing effects supported in both species under prospectively declared families with adequate mapping and coverage; unavailable from the current human references |
| `inconclusive` | Estimable but neither concordance nor discordance rule is met |
| `not_testable` | Missing biological replication, non-estimable design, or inadequate mapping/coverage |
| `filtered` | A planned feature failed a frozen technical eligibility rule |

Passing a mouse gate is recorded as `supported`; failing it is `tested_not_supported`, which means only that the prespecified gate was not passed—not that the null is proven. There is no additional cross-species significance test. Because the current formal human Phase 13 module analysis has zero supported modifier tests and `HR00` only reconstructs its descriptive stratum components, current respiratory-module comparisons can be called only `directionally_concordant`, `directionally_opposed`, `inconclusive`, or `not_testable`. `supported_concordance` and `discordant` are reserved for a future genuinely independent, prospectively specified human confirmation and cannot be assigned in this analysis.

### 6. Male astrocyte time course

The time course is cross-sectional, not longitudinal within animal. All 28 samples use EZ lysis. Twelve AD-WT pairs are available through 14 months; four WT mice are unmatched. Exactly four of the eight main-cohort mice also occur in this time course, so its seven-/eight-month result is only partly independent.

| Age bin | WT | 5xFAD | Matched pairs | Permitted use |
|---|---:|---:|---:|---|
| 1.5-2 months | 3 | 3 | 3 | Pair differences and continuous-age model |
| 4-5 months | 2 | 2 | 2 | Pair differences and continuous-age model |
| 7-8 months | 4 | 4 | 4 | Pair differences; exactly four mice overlap the main cohort |
| 10 months | 1 | 1 | 1 | Pair difference only; no standalone age-bin inference |
| 13-14 months | 4 | 2 | 2 | Pair differences; two additional WT mice excluded from genotype interaction |
| approximately 20 months | 2 | 0 | 0 | WT-aging context only; no disease contrast |

Reconcile all 25,076 deposited columns with mouse IDs and the reported 23,863-cell analysis set. Transfer six-state/DAA labels only from the frozen 7,341-cell, seven-month reference with a prespecified confidence threshold and an explicit `unassigned` state. State proportions use **all retained astrocytes** as their denominator; this astrocyte-only matrix cannot estimate astrocyte abundance among all nuclei or microglial abundance across age.

For each prespecified module score or validated state proportion, make the primary time-course quantity the 12 matched differences:

```text
D_pair = value_5xFAD - value_WT
D_pair ~ centered_age_pair
```

The equivalent animal-level model is `value ~ pair_id + genotype + genotype:age_pair`, with ten residual degrees of freedom before additional terms. Exclude the two unmatched 13.3-month WT mice from the genotype interaction; retain them and the two 19.6-month WT mice only for a separately labeled WT-aging display. One nominal pair has AD age 7.3 versus WT age 8.1 months; flag it and repeat the slope without that pair. Batch 6 is also the v3 chemistry group, so batch and chemistry cannot be separately estimated. Categorical age bins contain only 3/2/4/1/2 pairs and are display/sensitivity strata, not robust age-specific inference. Gene-wise age-by-genotype testing remains exploratory.

No result may be described as a within-mouse trajectory or proof that one astrocyte state transforms into another.

### 7. Phase 18 candidate layer

The current target is 47 `broad_network x key_driver x case_id` units representing 25 genes, not 25 interchangeable gene-only rows. The unit list is in [phase18_selected_candidate_units.tsv](../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv), and the gene inventory is in [phase18_selected_genes.tsv](../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_genes.tsv). A selected unit has no single direction: direction belongs to its contributing `kda_run_id` provenance.

Before mouse results are viewed:

- build and checksum the run-level candidate-context and predicted-target manifests required by the [Phase 18 cross-validation guide](../analysis/kda_phase_18/phase18_key_driver_cross_validation_guide.md), retaining `kda_run_id`, fine cell type, sex, APOE group, signature direction, KDA layer, target genes, and target recurrence;
- map candidate and target genes through the same one-to-one ortholog release;
- keep one candidate selected in two human networks as two validation units;
- create one frozen union target module per `candidate unit x signature_direction`, deduplicating each gene once while retaining run-level recurrence annotations; never merge `AD_up_mito` and `AD_down_mito` targets into one directional test;
- retain all assessable units computationally, while highlighting APOE, COX7C, SELENOW, LAMTOR5, RPL11, FTL, and ANKRD11 only for presentation.

The primary Phase 18 endpoint is the direction-specific frozen target module, not candidate-gene differential expression. Test each structural `47 units x 2 signature directions` slot with the animal-level module-score model. `AD_up_mito` prespecifies a positive mouse 5xFAD-minus-WT effect and `AD_down_mito` a negative effect. A slot is testable with at least 70% one-to-one target coverage and at least two measured targets, but it can pass the support gate only with at least five measured targets, the expected direction, BH `q < 0.05` across all estimable unit-direction slots, and no single-mouse/design-block reversal. Run-level target-set enrichments are recurrence diagnostics, not independent opportunities to promote the unit.

If both direction-specific modules for one unit pass in their opposite expected directions, report the unit as context-heterogeneous; do not collapse it to a single direction. If neither passes, use `tested_not_supported`, not “refuted.” Candidate-gene expression and rank are supporting endpoints only. In particular, mouse `Apoe` expression tests a generic disease response, not a human APOE-isoform effect.

Mouse target-module support can strengthen a network-associated candidate. It cannot establish that the candidate is a causal key driver.

## G. Validation and Extension Layers

### Within-dataset validation

1. Exact cell-ID and mouse-ID reconciliation.
2. Marker-consistent reproduction of the 23 published clusters.
3. Pseudobulk sample distances and PCA showing genotype interpretation is not dominated by one candidate pair, mouse, or lysis protocol.
4. Leave-one-pair-out stability if pairing is verified; otherwise leave-one-mouse-out and within-lysis sensitivity for primary module and gene effects.
5. DESeq2 versus edgeR direction/effect robustness.
6. Published-cluster versus broad-context aggregation sensitivity.

### Cross-resource validation

1. Compare separately with each frozen ROSMAP male APOE stratum.
2. Use time-course astrocytes as an internal age extension, not an independent cohort.
3. Use cortical astrocytes only as a paired-region presence/direction check because the same four mice supplied hippocampus.
4. If the reported female data are obtained, verify mouse identity, raw-count provenance, and absence of duplicate libraries. Report two per-animal profiles descriptively without a sex-interaction `p` value.
5. Seek a separate sex-balanced mouse snRNA-seq cohort for a genuine disease-by-sex validation.

The final evidence matrix must also import the already frozen SEA-AD Phase 18 assessment as an independent-human column. Current SEA-AD results make 36 of 47 ROSMAP units testable and strictly rediscover six—all MT units—while no non-MT ROSMAP top-five unit was rediscovered. Preserve each exact SEA-AD `strictly_rediscovered`, `tested_not_selected`, or `not_testable` state from the [VH09/VH10 execution summary](../validation_human/vh09_vh10_execution_summary.md). Mouse evidence is a new column and must never overwrite or relabel the SEA-AD result.

### Orthogonal extension

For Publication+, first perform an a priori animal-level power or simulation analysis for a minimum meaningful disease-by-sex interaction using an independently justified variance estimate. Do not use nuclei as the sample size or the unreplicated female profiles as a variance pilot. Then validate the most reproducible cell-context/module findings with RNAscope or immunofluorescence in independently sampled male and female WT/5xFAD animals. If causal key-driver language is intended, add lineage-appropriate perturbation and rescue with a prespecified mitochondrial or disease-relevant phenotype.

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

## H. Step-by-Step Workflow

### HR00 — Reconstruct or formally disable the descriptive donor-level human reference

**Actions**

- Checksum and validate `respiratory_pseudobulk_counts.rds`, its seven donor/context sample tables, analysis fingerprint, and the frozen Phase 13 config/module definitions.
- Reimplement the configured donor-level module-score model independently of the deleted/deprecated Phase 13 result scripts.
- Materialize male AD-minus-NCI module effects for all `7 contexts x 3 APOE strata x 4 modules`, with donor counts, design rank, HC3 estimate/CI, nominal `p`, complete direct/supporting structural slots, context mapping mode, diagnostics, and the inherited Phase 13 evidence status. Do not compute a new confirmatory BH gate for the narrowed stratum-effect set.
- Record the exact Phase 08 fine-cell MAST files and hashes as the descriptive gene-level track; prohibit arithmetic pooling of fine effects.

**Blocking gate:** if the donor RDS/config identity, design, or outputs cannot be validated, set donor-level broad human directional comparisons to `not_testable`. VM08 may then run only the explicitly descriptive Phase 08 fine-cell track. A successful reconstruction enables descriptive broad-effect comparison, not confirmatory human support.

### VM00 — Freeze scope, hypotheses, and state vocabulary

**Actions**

- Create the single validation YAML with input URLs/checksums, cohort rules, exact-resolution cell crosswalk, `HR00`/Phase 08 reference paths and evidence levels, ortholog release, module IDs, Phase 18 run/unit hashes, count filters, design formulas, contrast signs, FDR families, seeds, and software/container versions.
- Freeze male 5xFAD-minus-WT as the only executable auxiliary disease contrast.
- Materialize structural slots for sex and APOE endpoints with status `not_testable` and an explicit reason.
- Freeze `supported`, `tested_not_supported`, `not_testable`, and `filtered` test states plus `directionally_concordant`, `directionally_opposed`, `supported_concordance`, `discordant`, and `inconclusive` comparison labels. Mark `supported_concordance` and `discordant` structurally unavailable for the current Phase 08/Phase 13/`HR00` sources.

**Blocking gate:** no mouse expression result is inspected until the config, exact human source tier, mapping rows, expected directions, family membership, and all reference hashes are frozen.

### VM01 — Acquire and checksum primary sources

**Actions**

- Download the GEO SOFT/MINiML metadata, three processed matrices, SRA run manifest, paper supplement, and official source-data cell annotations.
- Record URL, accession, retrieval timestamp, byte size, and SHA-256 for every file.
- Inventory the authors' [5xFAD-sNucSeq repository](https://github.com/naomihabiblab/5xFAD-sNucSeq) as code/supporting material; do not treat it as an independent dataset.

**Blocking gate:** missing or changed remote objects produce a nonzero exit and a manifest diff; they are never silently substituted.

### VM02 — Reconstruct the animal and library manifest

**Actions**

- Build one row per library partition with all original source fields and adjudicated fields.
- Assign stable internal mouse IDs and test whether the four candidate pair IDs can be independently corroborated without using expression outcomes.
- Collapse left/right partitions to their shared mouse ID.
- Resolve the cortex genotype typos and sample aliases through explicit provenance columns.
- Audit female records across supplement, GEO, SRA, processed matrices, and cell IDs.

**Blocking gate:** every primary nucleus must map uniquely to one partition and one mouse. Any pair admitted to the model must have independent provenance and contain one WT and one 5xFAD mouse; unverified candidate pairs trigger the lysis-block fallback rather than entering the model.

### VM03 — Reconcile matrices and official annotations

**Actions**

- Import each matrix using format-aware parsers with row-width assertions and parser-level dequotation.
- Confirm integer nonnegative counts, unique gene symbols, unique nucleus IDs, and expected dimensions.
- Use streaming/chunked aggregation or a validated on-disk sparse conversion; fail if code attempts an unrestricted dense in-memory load of the approximately 1.02-billion-entry main matrix.
- Join parser-canonical main-matrix IDs exactly to official source annotations and reproduce 54,769 matched plus 598 matrix-only cells, with no fuzzy ID normalization.
- Emit matched, unmatched, duplicate, and exclusion manifests.
- Reconcile 7,716 broad all-cell astrocytes with 7,345 six-state source IDs and reproduce 7,341 count-backed state-reference cells, four absent state IDs, and 375 broad-only cells.
- Reconcile time-course and cortex matrix counts with their reported retained counts.

**Blocking gate:** count/annotation mismatches must be resolved or explicitly excluded before QC or aggregation.

### VM04 — Validate cell labels and freeze the crosswalk

**Actions**

- Reproduce per-mouse counts for all 23 published clusters.
- Review canonical positive/negative markers, doublet-enriched patterns, and cross-lineage contamination.
- Confirm every primary broad context is present in all eight mice and apply the 20-nucleus gate.
- Freeze both the published-cluster and seven-network crosswalks.
- Run the separately frozen DAA/DAM and composition calibration panel before mitochondrial or Phase 18 results are exposed.

**Blocking gate:** no outcome-based relabeling, merging, or threshold changes are permitted after genotype summaries are unblinded. A calibration failure pauses target interpretation for provenance review but cannot be repaired by tuning target-analysis thresholds.

### VM05 — Build and validate mouse-level pseudobulks

**Actions**

- Aggregate raw UMI counts to `gene x mouse x cell_context`.
- Reconcile summed pseudobulk UMIs to admitted cell-level UMIs exactly.
- Generate per-mouse library sizes, detected genes, composition, PCA, sample distances, and pair links.
- Apply and record the frozen gene filter separately in each cell context.

**Blocking gate:** each admitted UMI must be counted exactly once; eight biological columns—not ten library columns—must enter every primary context.

### VM06 — Estimate male disease and composition effects

**Actions**

- Fit the model selected by the frozen VM02 pairing decision: pair-blocked if verified, otherwise lysis-blocked.
- Apply log-fold-change shrinkage and BH correction within each broad-context genome-wide family.
- Fit the predeclared edgeR robustness model.
- Compute design-appropriate influence results—leave one pair out if verified, otherwise leave one mouse out—and animal-level composition effects.
- Produce complete result slots, including filtered and not-testable features.

**Blocking gate:** no cell-level differential-expression `p` values enter the evidence matrix.

### VM07 — Test frozen respiratory modules

**Actions**

- Apply the frozen ortholog and expression-coverage gates.
- Fit animal-level scores and ranked gene-set tests for all four modules.
- Correct the primary and supporting families separately as declared in VM00.
- Run nuclear-only and mtDNA-coverage sensitivities without redefining the primary result.

**Blocking gate:** a module below its frozen coverage threshold is `not_testable`; missing genes never receive zero expression or zero effect.

### VM08 — Perform cross-species concordance

**Actions**

- Load checksum-frozen human effects with method, replicate unit, donor counts, source path/hash, cell resolution, and inherited evidence status; do not rerun or select human results based on mouse outcomes.
- Compare mouse effects independently with male `e2`, `e33`, and `e4` human strata, keeping Phase 08 fine rows separate and `HR00` broad module rows explicitly marked.
- Compute sign agreement, effect-rank correlation with CI, module-direction agreement, and frozen-signature enrichment.
- Render female human effects only as context and keep formal sex/APOE mouse slots `not_testable`.

**Blocking gate:** every comparison row must retain species, tissue, cell-resolution, APOE-reference label, ortholog count, and human evidence status.

### VM09 — Run the male astrocyte time-course extension

**Actions**

- Freeze the 28-mouse age/genotype/batch/chemistry manifest, 12 candidate matched pairs, four unmatched WT mice, and cell-retention rule.
- Transfer six-state labels from the frozen 7,341-cell reference using a prespecified confidence/unassigned rule; create animal-level astrocyte pseudobulks and within-astrocyte state proportions.
- For prespecified module scores and state proportions, fit the 12-pair difference-on-age model through 14 months and reproduce ten residual degrees of freedom.
- Repeat the slope without the age-mismatched 7.3-versus-8.1-month pair; show categorical bins only as sensitivity.
- Exclude unmatched WT mice from the genotype interaction, display them only in a WT-aging context, and never estimate a disease contrast at approximately 20 months.
- Keep batch and chemistry source fields but do not fit both when batch 6 and v3 are aliased.

**Blocking gate:** do not interpret a genotype-by-age term when pair provenance fails, the design matrix is rank-deficient, or one batch/age pair determines the slope.

### VM10 — Evaluate frozen Phase 18 candidate units

**Actions**

- Freeze run-level candidate provenance, direction-specific union target modules, ortholog coverage, and all 94 structural `unit x direction` slots before loading mouse results.
- Test target-module direction/effect as primary and candidate expression/rank as supporting; keep run-level enrichments as recurrence diagnostics.
- Correct across all estimable unit-direction slots in the complete declared family and retain network-specific unit identity.
- Join the frozen SEA-AD unit statuses as a separate evidence column without changing either cohort's state.
- Produce a seven-candidate presentation view without changing the computational denominator.

**Blocking gate:** no target may be added or removed because it performs well or poorly in GSE143758.

### VM11 — Run conditional Advanced branches

**Actions**

- Attempt raw-SRA reconstruction only after every processed prefix has an unambiguous raw record.
- Compare processed-count and raw-rebuilt effects if reconstruction becomes complete.
- Analyze cortical astrocytes as within-mouse region sensitivity only.
- If female data are received, validate provenance and produce two descriptive per-animal profiles without inferential sex testing.

**Blocking gate:** partial raw reconstruction cannot replace the complete processed auxiliary cohort; unreplicated female data cannot enter a disease-by-sex model.

### VM12 — Validate and release the evidence package

**Actions**

- Run contract tests for dimensions, IDs, checksums, design rank, contrasts, family sizes, status completeness, and figure-data identity.
- Write outputs atomically with phase status and artifact manifests.
- Render prespecified figures only from frozen result tables.
- Produce a claim ledger linking every sentence-level conclusion to an evidence row and its permitted claim level.

**Release gate:** all planned slots must appear exactly once; failed, filtered, inconclusive, and not-testable results remain visible.

## I. Validation Evidence Hierarchy

| Level | Evidence | Maximum claim |
|---:|---|---|
| 0 | File, ID, and metadata reconciliation | Dataset is technically usable |
| 1 | Mouse-level main-cohort effect with adequate cell and mapping coverage | Male 5xFAD association in this cohort |
| 2 | Animal-level consistency, design-appropriate influence stability, and method agreement | Robust within-dataset male association |
| 3 | Prespecified module/signature comparison with an exact frozen human source | Directional cross-species concordance only; `HR00` remains descriptive |
| 4 | Time-course or cortex direction agreement | Internal contextual support, not independent replication |
| 5 | Independent sex-balanced mouse cohort | Replicated mouse disease-by-sex effect |
| 6 | Independent human support plus orthogonal tissue assay | Multi-resource translational support |
| 7 | Lineage-specific perturbation and rescue | Functional-driver evidence |

GSE143758 alone can reach Levels 1-2 for auxiliary male disease effects. It can contribute to Level 3 only with an exact frozen human reference, and it cannot reach Level 5 because its public records provide no female arm. No transcriptomic level by itself establishes causality.

## J. Figure and Deliverable Plan

### Core figures

1. **Design and feasibility map:** all cohorts, animals, library partitions, sex availability, repeated hemispheres, and explicit `not_testable` APOE/sex cells.
2. **Main-cohort QC:** per-mouse cell counts, pseudobulk library sizes, PCA/sample distance, pair links, lysis protocol, and the 54,769/598 annotation reconciliation.
3. **Male disease landscape:** broad-context composition effects and forest plots of the two direct respiratory module estimates, showing all animals and conditional candidate-pair links only if verified.
4. **Cross-species concordance:** mouse male effects against human male `e2`, `e33`, and `e4` in separate panels, with mapping coverage and evidence status.
5. **Astrocyte age extension:** all 12 matched differences, continuous-age slope and sensitivity, four unmatched WT context mice, state-transfer confidence, and batch/chemistry labels.
6. **Phase 18 candidate support:** complete unit-level matrix plus a seven-candidate annotated presentation panel.

### Supplementary figures

- Published-cluster marker audit and per-mouse counts.
- Matrix/source-data join and excluded-cell audit.
- Design-appropriate influence and DESeq2/edgeR sensitivity.
- Ortholog and module coverage.
- Published-cluster versus broad-context results.
- Cortex and any obtained female descriptive profiles, labeled non-independent or non-inferential.

### Required machine-readable deliverables

```text
VM00_frozen_config_and_source_hashes
HR00_human_reference_effects_and_status
VM01_dataset_inventory
VM02_mouse_library_manifest
VM02_metadata_discrepancy_register
VM03_cell_annotation_join_and_exclusions
VM04_cell_context_crosswalk_and_marker_qc
VM05_pseudobulk_counts_and_reconciliation
VM06_de_results_and_composition_results
VM06_influence_results
VM07_ortholog_and_module_coverage
VM07_module_score_and_competitive_enrichment_results
VM08_cross_species_concordance
VM09_astrocyte_timecourse_results
VM10_phase18_candidate_and_target_results
VM12_complete_status_manifest
VM12_claim_ledger
```

Every table must include stable IDs, exact denominator, effect sign, estimate, uncertainty, multiplicity family, testability state, and provenance hash. Figures must ship with their plotted-data tables and captions.

## K. Verified Reference Layer

### Dataset and literature sources

- [GSE143758 GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE143758): series design, 37 public samples, and three processed matrices.
- [GSE143758 family SOFT](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE143nnn/GSE143758/soft/GSE143758_family.soft.gz): sample titles, strain, age, tissue, and SRA/BioProject links.
- [Habib et al., 2020, *Nature Neuroscience*](https://pmc.ncbi.nlm.nih.gov/articles/PMC9262034/), DOI [10.1038/s41593-020-0624-8](https://doi.org/10.1038/s41593-020-0624-8): eight-mouse main cohort, 54,769 high-quality nuclei, 23 clusters, male design, time course, and reported female/cortex extensions.
- [Supplementary Table 1](https://pmc.ncbi.nlm.nih.gov/articles/instance/9262034/bin/NIHMS1578105-supplement-1578105_Sup_Tables.xlsx): mouse, sex, genotype, tissue, lysis, chemistry, and batch reconstruction.
- [Figure 1 source-data workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41593-020-0624-8/MediaObjects/41593_2020_624_MOESM3_ESM.xlsx): official main-cohort nucleus IDs, sample/library IDs, condition, and published cluster/state annotations. Animal mapping and S2 L/R collapsing come from the supplement-derived join, not this workbook alone.
- [SRA SRP243446](https://www.ncbi.nlm.nih.gov/sra?term=SRP243446) and [BioProject PRJNA602299](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA602299): public raw-read inventory.
- [SRA RunInfo](https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=SRP243446): experiment/run structure, including the two generically named runs bundled under GSM4276892/SRX7583992.
- [Single Cell Portal SCP302](https://singlecell.broadinstitute.org/single_cell/study/SCP302/mouse-alzheimers-and-disease-astrocytes): supporting astrocyte metadata and embeddings; no public expression matrix or missing female count recovery as of the audit date.
- [Authors' analysis repository](https://github.com/naomihabiblab/5xFAD-sNucSeq): supporting analysis code and time-course embedding inputs; not a substitute for missing female raw counts.

### Project-specific frozen references

- The instruction that GSE143758 is for the sex-difference question, while APOE-isoform dataset search continues, is in [email_08192026.txt](../email_notes/email_08192026.txt).
- The ROSMAP Phase 08 gene-level branch is cell-level MAST for paper comparability and does not replace donor-level inference, as documented in [processing_pipeline_phase_summaries.md](../processing_pipeline_phase_summaries.md).
- The four respiratory modules are defined in [phase13_respiratory_modules.tsv](../../config/phase13_respiratory_modules.tsv) and [phase13_respiratory_modifier.yml](../../config/phase13_respiratory_modifier.yml).
- The descriptive human mitochondrial patterns and their caveats are summarized in [phase11_pathway_discussion_summary.md](../analysis/mt_pathway/phase11_pathway_discussion_summary.md).
- The formal Phase 13 outcome—180 estimable but inconclusive tests, 16 not testable, zero supported—is documented in [phase13_figure_proposal.md](../figures/analysis/phase_13_respiratory_modifier/phase13_figure_proposal.md).
- The current Phase 18 targets are [phase18_selected_candidate_units.tsv](../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv), [phase18_selected_genes.tsv](../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_genes.tsv), and the [cross-validation guide](../analysis/kda_phase_18/phase18_key_driver_cross_validation_guide.md).
- Current independent-human Phase 18 evidence—36 of 47 units testable in SEA-AD, six strict MT rediscoveries, and zero strict non-MT rediscoveries—is frozen in [vh09_vh10_execution_summary.md](../validation_human/vh09_vh10_execution_summary.md).
- The project preference for direction, rank/enrichment, cell-type consistency, mitochondrial enrichment, effect sizes, and CIs is recorded in [meeting_08182026_summary_action_items.md](../email_notes/meeting_08182026_summary_action_items.md).

### Reference interpretation rule

The human mitochondrial patterns are discovery references, not ground truth. The four modules are prespecified biological programs, but current formal human modifier tests are inconclusive. The mouse work can add evidence; it cannot retroactively convert an inconclusive human result into a confirmed mechanism.

## L. Self-Critical Risk Review

| Risk | Consequence | Mitigation | Residual limitation |
|---|---|---|---|
| All supplement-mapped public records are male; GEO/SRA omit sex | Intended disease-by-sex question cannot be tested | Structural `not_testable` status; seek independent sex-balanced cohort | Fundamental; no analysis method fixes absent animals |
| Auxiliary male analysis silently replaces the requested sex question | Scientifically different result presented as validation | Overall no-go status; require explicit acceptance and separate auxiliary labeling | Male results cannot answer the original question |
| Reported females are one WT/one 5xFAD and not deposited | Temptation to overinterpret two profiles | Access/provenance audit; descriptive plots only | No female variance estimate |
| Eight main-cohort mice, four per genotype | Low power and unstable gene-wise inference | Prespecified modules, shrinkage, CIs, all-animal display, design-appropriate influence checks, design sensitivity | Moderate effects will remain inconclusive |
| Bilateral S2 libraries | Pseudoreplication if treated as mice | Collapse by mouse before modeling; contract test for eight columns | Hemisphere effects cannot be estimated independently |
| Pair and lysis structure | Confounding or overparameterization | Verify pair IDs; pair model primary, lysis fallback; never include redundant blocks | Only three residual degrees of freedom in paired model |
| Processed/final cell-count differences | Inclusion of unpublished QC failures or inconsistent denominators | Exact source-data join and exclusion manifests | Time-course/cortex retained sets may remain partly unrecoverable |
| Dense main matrix has approximately 1.02 billion entries | Memory exhaustion or silent truncation during generic import | Streaming/chunked summaries or checksummed on-disk sparse conversion; reconciliation tests | Cell-level operations require deliberate engineering |
| Raw manifest does not fully reconstruct processed prefixes | Incomplete raw rebuild could bias Advanced comparison | Processed integer UMI matrices are primary; raw branch only after complete provenance | Full end-to-end raw reproduction may remain unavailable |
| Time-course age, batch, chemistry, and genotype support are linked | Spurious or non-identifiable time trends | Twelve-pair difference slope, age-mismatch exclusion, categorical display, no separate batch/v3 terms | Time-course interaction remains exploratory |
| Cortex uses the same mice and has one per genotype per age | False claim of independent regional replication | Label as paired region sensitivity; no inferential cortex DE | Region generalization remains weak |
| Hippocampus versus human PFC | Fine-cell and regional effects may disagree for legitimate reasons | Broad conservative crosswalk; separate fine displays; no forced matches | Discordance is not necessarily biological refutation |
| 5xFAD versus late-onset human AD | Model-specific amyloid effects may not translate | Use concordance language and compare effect organization, not disease identity | External validity remains model-limited |
| snRNA-seq undercaptures cytoplasmic/mitochondrial RNA | Weak or selective mtDNA signal | Explicit gene coverage, nuclear OXPHOS co-primary, no percent-mito substitution | mtDNA module may be uninformative in some contexts |
| Ortholog ambiguity and symbol drift | Artificial loss or sign mismatch | Versioned one-to-one map and full exclusion accounting | Some human genes cannot be evaluated |
| Authoritative ROSMAP broad effect tables are absent | Cross-species workflow could load a nonexistent or deprecated reference | Blocking `HR00` reconstruction with exact RDS/config hashes, or descriptive Phase 08 fine-cell fallback | Broad directional comparison is unavailable if reconstruction fails; reconstruction still cannot confer confirmatory support |
| Broad-cell aggregation | Dilution or composition-driven effects | Broad tier is the mouse auxiliary summary; publish cluster heterogeneity and require direct donor aggregation for any human broad reference | Fine-state localization and partial mappings remain exploratory |
| Reuse of human discovery results and current dataset | Selective endpoint choice | Freeze all modules, signatures, candidate units, and families before mouse results | Evidence is validation-oriented, not a fresh independent hypothesis source |
| Expression/network association interpreted as mechanism | Overstated biological claim | Claim ledger and evidence hierarchy; require perturbation/rescue for causality | Transcriptomic concordance remains associative |

### Final go/no-go rule

The decision for the intended **disease-by-sex validation is no-go**. GSE143758 may proceed only as a separately labeled Standard auxiliary analysis of male disease effects after the changed question is explicitly accepted and `HR00` is either completed or formally disabled in favor of descriptive fine-cell comparisons. Report disease-by-sex and APOE objectives as `not_testable`. A sex-dependent mouse conclusion requires an independent cohort with replicated female and male WT and AD-model animals; obtaining the two reported female profiles alone is not sufficient.
