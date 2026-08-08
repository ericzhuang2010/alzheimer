# Practical next-step plan for the Alzheimer mitochondrial project

**Prepared:** 2026-08-07

**Plain-language revision:** 2026-08-08

**Status:** planning document; the new donor-level tests have not been completed

## 1. Start here: what are we trying to learn?

### 1.1 The research question

Cells need mitochondria to make energy. The respiratory machinery inside mitochondria is unusual because its parts come from two places:

- mitochondrial DNA, or **mtDNA**, provides 13 respiratory genes;
- nuclear DNA provides many more genes needed for OXPHOS, mitochondrial protein production, and mitochondrial structure.

The project asks:

1. Does Alzheimer disease change these mitochondrial gene programs?
2. Is the Alzheimer-related change different between females and males, or between APOE groups?
3. Is the change different in astrocytes, excitatory neurons, and inhibitory neurons?
4. Do three network-nominated systems consistently point to the same biological change?

The three systems are:

- `APOE–TUFM` in astrocytes;
- `LAMTOR5–ATP5IF1` in neurons;
- `GABARAPL2–CHCHD2`/`PARK7` in excitatory neurons.

### 1.2 The claim we are trying to earn

The strongest possible conclusion would be:

> Alzheimer disease changes the relationship between mtDNA respiratory genes and nuclear mitochondrial genes. The change depends on sex and/or APOE and differs between brain cell types. Donor-level and network analyses support one or more of the three candidate systems, and the main finding is seen again in independent data or receives protein-level support.

This is a **goal**, not a current conclusion. The final wording must become narrower if any part fails.

### 1.3 Why the existing results are not enough

The existing MAST, pathway, and KDA results are useful clues. They show descriptive sex/APOE patterns and nominate interesting genes. They do not yet prove the claim because:

- the existing MAST tests treat nuclei as observations, while the independent biological samples are people;
- “significant in females but not in males” does not prove that females and males differ;
- a mitochondrial DEG list can make a mitochondrial network neighborhood look enriched by construction;
- highly connected network genes can be nominated more often simply because they are hubs;
- the current findings have not yet been tested in an independent cohort.

The next work therefore starts with people as the sample unit and direct statistical comparisons.

## 2. The full project in one page

```text
Round 0: decide the rules before viewing new results
    ↓
Round 1: test whether the donor-level biological pattern exists in ROSMAP
    ↓
STOP AND REVIEW Gates 1–3
    ├── unsupported → narrow or stop the claim
    └── supported   → continue only with the surviving results
                         ↓
Round 2: test whether surviving network candidates beat fair network controls
                         ↓
Round 3: test frozen findings in independent RNA and protein data
                         ↓
Round 4, optional: perturbation and rescue experiments for causal language
```

| Round | Main question | Main work | Decision enabled |
|---:|---|---|---|
| 0 | Are the data and rules ready? | Freeze donors, cell groups, contrasts, gene modules, thresholds, and software versions | Whether Round 1 can begin |
| 1 | Does the proposed biological pattern exist in donor-level ROSMAP data? | Pseudobulk, direct sex/APOE tests, respiratory modules, cell-type comparison, mitonuclear tests, candidate readouts, and stability checks | Which claim parts and candidates survive |
| 2 | Are the surviving network candidates more convincing than matched chance results? | Corrected KDA, two kinds of null comparison, network perturbation, and one alternative network | Which candidate names can remain |
| 3 | Is the result seen in other people or another measurement type? | Independent RNA replication and protein support | Whether to say “replicated” or “protein-supported” |
| 4 | Does changing a candidate cause the respiratory phenotype? | Cell experiments with perturbation and rescue | Whether causal words are allowed |

**What to do now:** complete Round 0, then build the donor-level data in Round 1 Task 1. Do not start new KDA null simulations or external outcome analysis yet.

Do not begin the expensive Round 2 network simulations because an exploratory KDA plot looks interesting. Round 2 is allowed only for candidate systems that first show a matching donor-level phenotype in Round 1.

## 3. Essential words used in this plan

| Term | Plain-language meaning |
|---|---|
| Donor | One human participant. Donors, not individual nuclei, are the independent samples. |
| NCI | No cognitive impairment; the comparison group used here. |
| PMI | Postmortem interval: the time between death and tissue preservation. It is included as a model adjustment. |
| Pseudobulk | Add the raw counts from the same donor and cell type so that each donor contributes one expression profile per cell type. |
| AD effect | The AD-versus-NCI difference after accounting for age and postmortem interval. |
| Modifier or interaction | A direct test of whether the AD effect differs between two groups, such as females versus males. |
| Module | A set of genes with a related job, summarized by one score. |
| OXPHOS | Oxidative phosphorylation, the respiratory system that makes most cellular ATP. It includes mtDNA-encoded and nuclear-encoded genes. |
| Mitonuclear relationship | How the mtDNA respiratory signal and the nuclear mitochondrial signal move together. |
| MIB/MICOS | A group of proteins that helps organize the inner mitochondrial membrane and its folds, called cristae. |
| Confidence interval, or CI | A range of effect sizes consistent with the data. A wide interval means high uncertainty. |
| P value | Evidence against no effect for one test. |
| q value or FDR | A P value adjusted for running many tests. Here, `q ≤ 0.05` is the main significance rule. |
| Smallest effect size of interest, or SESOI | The smallest change considered large enough to matter biologically. It must be chosen before viewing the new AD results. |
| Bootstrap | Repeat the analysis after resampling donors to see whether the result keeps the same direction. |
| Leave-one-donor-out | Repeat the analysis after removing each donor, one at a time. |
| Residual | The amount by which an observed value is above or below a model's predicted value. |
| PC1 | An alternative way to combine genes using their strongest shared expression pattern. |
| Target-excluded module | Remove the highlighted gene from its module score so the gene cannot create its own supporting result. |
| KDA | Key-driver analysis: a network test asking whether a candidate sits unusually close to many query genes. |
| Null comparison | Create fair matched chance examples and ask whether the real result is more extreme. |
| Independent replication | Repeat the frozen test in a different group of donors. |
| Protein support | Test the same idea using protein measurements instead of RNA. This is a different measurement type, but it is not independent if the donors overlap. |

## 4. How the evidence matrix and gates work

The evidence matrix is the project's **scorecard**. Each row is one statement we may want to make. An analysis writes results into one or more rows.

A gate is the rule used to judge a row. A round tells us when to perform the work. Therefore:

```text
task → saved result → matrix row → gate decision → next allowed task
```

Passing an early gate does not prove the whole story. It only supports that row and gives permission to continue.

| Claim ID | Plain-language question | Round and tasks | Gate | If it does not pass |
|---|---|---|---|---|
| C1 | Does sex or APOE truly change the AD respiratory effect? | Round 1 Tasks 2, 3, and 7 | Gate 1A | Remove sex/APOE modification |
| C2 | Is the modifier effect truly different between cell types? | Round 1 Tasks 5 and 7 | Gate 1B | Say “cell-context-resolved,” not “cell-type-specific” |
| C3 | Does AD change the relationship between mtDNA and nuclear respiratory signals? | Round 1 Tasks 4 and 7 | Gate 2 | Remove “mitonuclear”; describe only the supported compartment/program |
| C4 | Does `APOE–TUFM` have the predicted astrocyte phenotype? | Round 1 Tasks 2, 3, 5, 6, and 7 | Gate 3A | Do not run Round 2 for this system |
| C5 | Does `LAMTOR5–ATP5IF1` have the predicted neuronal phenotype? | Round 1 Tasks 2, 3, 5, 6, and 7 | Gate 3B | Do not run Round 2 for this system |
| C6 | Does `GABARAPL2–CHCHD2`/`PARK7` have the predicted excitatory-neuron phenotype? | Round 1 Tasks 2, 3, 5, 6, and 7 | Gate 3C | Do not run Round 2 for this system |
| C7 | Does each surviving candidate beat fair network controls? | Round 2 | Gate 4 | Keep that candidate only as an exploratory hypothesis |
| C8 | Does the frozen respiratory result appear in an independent RNA cohort? | Round 3 RNA | Gate 5A | Call it an internally supported discovery, not replicated |
| C9 | Does a surviving program receive protein-level support? | Round 3 protein | Gate 5B | Do not claim protein support for that result |

Each row receives one of these statuses:

- `pass`: all required rules were met;
- `fail`: the test was precise enough, but the required evidence was not present;
- `inconclusive`: the uncertainty was too large to decide;
- `not_testable`: the needed data or sample size was missing;
- `not_started` or `running`: work status only.

A large estimated effect with a very wide CI is **inconclusive**, not proof.

## 5. What is already available

### 5.1 Donors and groups

The ROSMAP discovery cohort contains 276 donors: 142 NCI and 134 AD.

| Sex/APOE group | NCI | AD | Total |
|---|---:|---:|---:|
| Female ε2 carrier | 17 | 8 | 25 |
| Female ε3/ε3 | 45 | 37 | 82 |
| Female ε4 carrier | 11 | 26 | 37 |
| Male ε2 carrier | 6 | 7 | 13 |
| Male ε3/ε3 | 53 | 29 | 82 |
| Male ε4 carrier | 10 | 27 | 37 |

Male ε2 is especially small. No result that depends only on 6 NCI and 7 AD donors should carry the main claim.

### 5.2 Data and code that can be reused

| Item | Location | Current use |
|---|---|---|
| Nine Seurat RDS inputs | [RDS manifest](../../config/minerva_rds_manifest.tsv) | Points to the full raw-count objects on Minerva |
| Main analysis settings | [analysis parameters](../../config/analysis_parameters.yml) | Cohort rules, thresholds, mtDNA genes, and seed |
| Minerva input/output settings | [Minerva configuration](../../config/minerva_shared.yml) | Production paths and resource settings |
| Validated cohort tables | `results/minerva_production/02_cohort/` | Donor membership, group counts, and per-RDS intersections |
| Validated cell QC | `results/minerva_production/04_qc/` | Barcode matching, cell labels, mitochondrial-read metrics, and QC flags |
| MitoCarta annotations | `results/minerva_production/03_annotations/` | Mitochondrial genes and pathway definitions |
| Fine-cell pseudobulk builder | [07_make_pseudobulk.R](../../scripts/07_make_pseudobulk.R) | Sums raw counts by donor and fine cell type and checks count conservation |
| Contrast builder | [07_build_contrast_manifest.R](../../scripts/07_build_contrast_manifest.R) | Creates within-group AD effects and seven direct modifier contrasts |
| edgeR runner | [07_run_pseudobulk_de.R](../../scripts/07_run_pseudobulk_de.R) | Runs filtering, TMM normalization, robust quasi-likelihood models, age/PMI adjustment |

### 5.3 New work that still needs code

The existing scripts cover fine-cell pseudobulk and the direct gene-level contrasts. New or extended workflows are still needed for:

- broad astrocyte, excitatory-neuron, and inhibitory-neuron pseudobulk;
- donor respiratory module scores and pathway tests;
- direct comparisons between cell types;
- the three mitonuclear endpoints;
- candidate summary/status tables;
- donor bootstrap, leave-one-donor-out, and depth/QC sensitivity;
- the locked evidence-matrix review.

### 5.4 Why broad cell classes are the main test

The current Phase 04 QC gives these preliminary usable donor counts at the 20-nucleus threshold. Each entry is `NCI/AD`.

| Fine cell type | Female ε2 | Female ε3/ε3 | Female ε4 | Male ε2 | Male ε3/ε3 | Male ε4 |
|---|---:|---:|---:|---:|---:|---:|
| `Ast GRM3` | 16/6 | 41/36 | 8/24 | 5/7 | 45/27 | 10/24 |
| `Exc L2-3 CBLN2 LINC02306` | 17/8 | 45/36 | 11/25 | 6/7 | 52/28 | 10/27 |
| `Exc L3-4 RORB CUX2` | 16/8 | 45/36 | 11/25 | 5/7 | 52/27 | 10/26 |

Five donors per required group is the minimum for fitting a model. Ten per group is preferred for a headline result. The ε2 fine-cell comparisons usually fall below 10, and some inhibitory fine types fall below 5. Therefore:

- broad classes carry the main inference;
- fine types show where a broad result may be located;
- a significant fine type cannot rescue a failed broad-cell test.

## 6. Round 0: prepare the study before testing the claim

Do not inspect new confirmatory group effects until this section is complete.

### Round 0A. Freeze the rules

**Why this matters**

If gene sets, contrasts, or thresholds change after looking at results, it becomes easy to choose the version that looks best by chance.

**Inputs**

- the configuration and manifest files in Section 5.2;
- current discovery MAST, pathway, and KDA outputs;
- the three candidate systems;
- MitoCarta gene and pathway tables.

**Exactly what to do**

1. Create a new analysis version and record the Git commit, R version, package versions, input sizes, and SHA-256 checksums.
2. Resolve ambiguous gene names, especially `RPL13` versus `MRPL13`.
3. Freeze the broad-cell mapping and the named fine types. Confirm that the three excitatory RDS files contain different nuclei before combining them.
4. Freeze seven direct modifier tests:
   - AD × sex within ε2;
   - AD × sex within ε3/ε3;
   - AD × sex within ε4;
   - AD × APOE ε2 versus ε3/ε3 within females;
   - AD × APOE ε2 versus ε3/ε3 within males;
   - AD × APOE ε4 versus ε3/ε3 within females;
   - AD × APOE ε4 versus ε3/ε3 within males.
5. Add the two three-way tests only if the planned claim says APOE changes the sex difference. Otherwise keep them secondary.
6. Freeze the primary gene modules:
   - 13 mtDNA-encoded respiratory genes;
   - nuclear-encoded OXPHOS structural genes, with all 13 mtDNA genes removed;
   - mitochondrial translation;
   - MIB/MICOS and inner-membrane organization.
7. Freeze complexes I–V, ATP synthase, and candidate-specific quality control as focused follow-ups, not a new pathway search.
8. Freeze the candidate-specific contrasts, cell contexts, mediator genes, and expected directions.
9. Freeze the multiple-testing groups:
   - 84 donor module-score tests: 4 modules × 7 modifiers × 3 broad cell classes;
   - a separate 84-test competitive pathway family using the same module × modifier × cell combinations;
   - 63 primary mitonuclear tests: 3 endpoints × 7 modifiers × 3 broad cell classes;
   - the written list of cell-type comparisons;
   - the written list of candidate-system tests.
10. Choose the SESOI without looking at AD interaction estimates. Write the numeric value and the exact CI rule in the manifest.
11. Define exactly what counts as “QC sensitivity agrees.” For example, freeze whether the sign must agree and how much the effect is allowed to shrink.
12. Freeze random seeds, the 20- and 50-nucleus thresholds, and all pass/fail rules in Section 8.

**Files to produce**

```text
results/<version>/audit/primary_analysis_manifest.tsv
results/<version>/audit/input_artifact_manifest.tsv
results/<version>/audit/gene_identifier_corrections.tsv
results/<version>/audit/frozen_cell_contexts.tsv
results/<version>/audit/frozen_contrasts.tsv
results/<version>/audit/frozen_respiratory_modules.tsv
results/<version>/audit/frozen_candidate_systems.tsv
results/<version>/audit/multiplicity_families.tsv
results/<version>/audit/seed_manifest.tsv
```

**Ready to continue when**

Every planned choice has a versioned value. Blank SESOI or QC-agreement rules mean Round 0 is not finished.

### Round 0B. Check data coverage and expected precision

**Why this matters**

A test may run in software but still be too uncertain to support a conclusion.

**Inputs**

- validated cohort and QC tables;
- frozen group and cell-type definitions;
- raw-count availability for each RDS.

**Exactly what to do**

1. Count usable donors in every diagnosis × sex × APOE × cell-context group at 20 nuclei.
2. Repeat the count at 50 nuclei.
3. Mark a contrast `not_testable` if any required group has fewer than 5 donors.
4. Mark a contrast as below the preferred headline level if any required group has fewer than 10 donors.
5. Estimate gene dispersion and module-score variation using masked group labels or NCI donors only.
6. Estimate expected CI widths for the frozen SESOI.
7. Check module coverage without examining AD effects.

A proposed module-coverage minimum is:

- at least 70% of the frozen module genes measured;
- at least 5 measured genes in the module;
- at least 10 of the 13 mtDNA protein-coding genes for the mtDNA module.

Freeze the final rule before Round 1.

**Files to produce**

```text
results/<version>/audit/prespecified_eligibility.tsv
results/<version>/audit/blinded_module_coverage.tsv
results/<version>/audit/precision_feasibility.tsv
results/<version>/audit/round0_readiness.tsv
```

**Ready to continue when**

The three broad classes have estimable primary contrasts and every unavailable or low-power comparison is labeled before effects are viewed.

### Round 0C. Check external-data feasibility

**Why this matters**

Round 3 cannot test sex/APOE replication if the external dataset lacks APOE or has too few donors in the relevant groups.

**Exactly what to check**

- independent donor identity;
- sex and APOE fields;
- diagnosis or pathology definition;
- broad-cell coverage;
- frozen gene and protein coverage;
- a defensible ROSMAP-to-validation cell mapping;
- data-access requirements and expected download size.

Save:

```text
results/<version>/audit/external_feasibility.tsv
```

This is an access check only. Do not inspect validation outcomes or use them to change the Round 1 definitions.

## 7. Round 1: test whether the biological pattern exists

Round 1 uses existing ROSMAP raw counts. It does not require FASTQ/BAM processing, new human samples, external outcome analysis, KDA null simulations, or laboratory experiments.

The correct order is:

```text
Task 1: build donor profiles
    ↓
Task 2: estimate direct sex/APOE effects
    ↓
Task 3: test respiratory programs
    ↓
Tasks 4–6: mitonuclear, cell-type, and candidate tests
    ↓
Task 7: stress-test every frozen result from Tasks 2–6
    ↓
Task 8: lock the results, fill the scorecard, and decide what survives
```

### Task 1. Build one expression profile per donor and cell context

**Question answered**

Can we create valid donor-level data with enough donors for each planned comparison?

**Why this is needed**

One donor may contribute hundreds or thousands of nuclei. Those nuclei share genetics, diagnosis, sex, APOE, age, and tissue conditions. They are not hundreds of independent people. Adding their raw counts makes the donor the sample unit.

**Inputs**

- the nine RDS paths in `config/minerva_rds_manifest.tsv`;
- sparse raw `RNA` UMI counts, not Seurat-normalized values;
- per-RDS cohort files in `results/minerva_production/02_cohort/`;
- barcode-level QC files in `results/minerva_production/04_qc/`;
- donor diagnosis, sex, APOE, age at death, and PMI;
- frozen fine-to-broad cell mapping;
- `scripts/07_make_pseudobulk.R`.

The full RDS files are on Minerva under:

```text
/sc/arion/projects/zhangb03a/shared/ROSMAP/Synapse/snRNAseq_MIT/GeneExpression/10x/processed
```

**Exactly what to do**

1. Process one RDS in each fresh R session to avoid memory problems.
2. Confirm the object contains a sparse, finite, nonnegative, integer `RNA` count matrix with gene names and cell barcodes.
3. Normalize every donor ID to the frozen eight-character `projid` form.
4. Match count-matrix columns to QC barcodes one-to-one.
5. Keep nuclei from the validated 276-donor analytic cohort.
6. Use the existing script to sum raw counts by donor × fine cell type.
7. Build broad astrocyte, excitatory-neuron, and inhibitory-neuron profiles by summing all disjoint fine-type counts for the same donor.
8. For excitatory neurons, prove that sets 1–3 do not reuse barcodes before combining them.
9. Include all cohort-retained fine profiles when building a broad profile. Apply the nucleus threshold after broad aggregation, not before it.
10. Attach donor and technical metadata: diagnosis, sex, APOE, age, PMI, number of nuclei, total UMI, detected genes, mtDNA-read fraction, MitoCarta-read fraction, and QC flags.
11. Mark `primary_eligible` when a donor/context has at least 20 nuclei.
12. Mark `sensitivity_eligible` separately when it has at least 50 nuclei.
13. Build a contrast-specific eligibility table with donor IDs, counts, nuclei, and the reason for every excluded test.

**Quality checks**

- every pseudobulk column has exactly one donor and one cell context;
- no donor/context pair appears twice;
- diagnosis, sex, APOE, age, and PMI are complete;
- gene-wise and total UMI counts are exactly conserved;
- broad counts exactly equal the sum of their fine counts;
- no excitatory barcode is counted twice;
- every fitted design is full rank;
- every required group has at least 5 donors.

Any count-conservation or identity failure stops downstream use of that object.

**Files to produce**

```text
results/<version>/pseudobulk/<rds>.pseudobulk_counts.rds
results/<version>/pseudobulk/<rds>.pseudobulk_samples.tsv
results/<version>/pseudobulk/<rds>.pseudobulk_count_conservation.tsv
results/<version>/pseudobulk/broad_class.pseudobulk_counts.rds
results/<version>/pseudobulk/broad_class.pseudobulk_samples.tsv
results/<version>/pseudobulk/pseudobulk_sample_eligibility.tsv
results/<version>/pseudobulk/pseudobulk_qc.tsv
results/<version>/pseudobulk/pseudobulk_build_status.tsv
```

**What this task can conclude**

Nothing biological. It creates valid inputs or marks a planned comparison `not_testable`.

### Task 2. Test whether sex or APOE changes the AD effect

**Question answered**

Is the AD-versus-NCI difference genuinely different between sex or APOE groups?

**Why this is needed**

Suppose a gene is significant in females and not significant in males. That may happen because the female estimate is more precise, even if both effects are similar. We must directly compare the two AD effects.

**The exact comparisons**

For sex within one APOE group:

```text
(AD − NCI in females) − (AD − NCI in males)
```

For APOE within one sex:

```text
(AD − NCI in ε2 or ε4) − (AD − NCI in ε3/ε3)
```

These are called difference-of-differences or interaction tests.

**Inputs**

- Task 1 count matrices and sample metadata;
- frozen contrasts and eligibility;
- age and PMI;
- `scripts/07_build_contrast_manifest.R`;
- `scripts/07_run_pseudobulk_de.R`.

**Exactly what to do**

1. Fit the three broad classes first. Fit only the frozen eligible fine types for localization.
2. Create an edgeR count object for each cell context.
3. Use `filterByExpr` with the exact model to remove genes with too little information.
4. Recalculate library sizes and use TMM normalization to adjust for different total count depths between donor profiles.
5. Save the TMM logCPM matrix because Tasks 3–6 need it.
6. Fit the robust edgeR quasi-likelihood model, which estimates donor-to-donor variation before testing a group difference:

   ```text
   ~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled
   ```

7. Test the seven frozen direct modifiers from Round 0.
8. Save the six within-stratum AD-versus-NCI effects for plots, but do not mistake them for interaction tests.
9. Save, for every gene and contrast:
   - signed difference-of-differences;
   - model-based standard error;
   - 95% CI;
   - raw P value and BH-adjusted q value;
   - tested-gene background;
   - donor and nucleus counts.
10. Audit the current script's reconstructed CI. Use exact model covariance or donor-bootstrap intervals for final claims rather than relying on `abs(logFC)/sqrt(F)` alone.
11. Inspect model rank, residual degrees of freedom, dispersion, TMM factors, library size, and MDS/PCA plots.

**Quality and interpretation checks**

- rank-deficient tests, where the model cannot separate the requested groups/covariates, and missing-group tests are `not_testable`;
- a wide CI that includes both zero and meaningful effects is `inconclusive`;
- individual significant genes do not prove a respiratory program;
- fine-cell significance cannot rescue a failed broad-cell result;
- do not add batch or RIN only because it improves a focal P value.

**Files to produce**

```text
results/<version>/pseudobulk/contrast_manifest.tsv
results/<version>/pseudobulk/contrast_eligibility.tsv
results/<version>/pseudobulk/tmm_logcpm_by_context.rds
results/<version>/pseudobulk/gene_interaction_results.tsv.gz
results/<version>/pseudobulk/within_stratum_ad_effects.tsv.gz
results/<version>/pseudobulk/model_diagnostics.tsv
results/<version>/pseudobulk/pseudobulk_de_status.tsv
```

**Matrix rows updated**

C1 and the mediator-gene parts of C4–C6. No row passes until Task 7 stability is complete.

### Task 3. Test whether many respiratory genes move together

**Question answered**

Does the sex/APOE modifier affect a coordinated respiratory program rather than one isolated gene?

**Why this is needed**

One gene can look unusual by chance. A prespecified set of related genes moving together is more convincing and easier to compare across datasets.

**Inputs**

- Task 2 TMM logCPM and complete ranked gene statistics;
- exact tested genes for every model;
- frozen module definitions;
- MitoCarta measured-gene and pathway tables;
- frozen identifier corrections.

**Exactly what to do**

1. Intersect each frozen module with the genes actually tested in that cell context.
2. Report the original number of genes, measured genes, tested genes, and every excluded gene.
3. Keep the nuclear OXPHOS score separate from all 13 mtDNA genes.
4. Keep OXPHOS structural subunits primary. Report assembly factors separately.
5. For every donor and cell context, standardize each gene using the NCI mean and SD, then average genes to make an understandable module score.
6. Save the NCI reference mean and SD for every gene.
7. Build an alternative PC1 score using NCI donors only. Orient it in the same direction as the mean score before looking at AD effects.
8. Fit the same seven direct modifier tests to donor module scores, adjusting for age and PMI.
9. Test whether the ranked genes support each module while accounting for correlation between genes (`camera`).
10. Repeat with a full-ranked enrichment method (`fgseaMultilevel`) as a sensitivity check.
11. Compare each observed module result with at least 1,000 non-mitochondrial gene sets matched for expression, detection, and gene length.
12. Check whether one gene or one OXPHOS complex is creating the whole result.
13. For candidate-system scores, remove the named target before scoring:
   - translation minus `TUFM`;
   - ATP synthase minus `ATP5IF1`;
   - quality control minus `CHCHD2` and `PARK7`.

**Primary testing groups**

There are 4 modules × 7 modifiers × 3 broad classes = 84 combinations. Apply BH FDR separately to the 84 donor module-score tests and the 84 `camera` competitive pathway tests. Complexes, fine types, and candidate-specific modules are written follow-ups, not rescue searches.

**Module reliability checks**

- frozen gene-coverage rule passes;
- zero-variance genes are removed and reported;
- mean score and PC1 have the same biological direction;
- flag the module if their absolute correlation is below `0.70`;
- report median correlation between genes and PC1 variance explained.

**Files to produce**

```text
results/<version>/modules/module_membership_and_coverage.tsv
results/<version>/modules/donor_module_scores.tsv.gz
results/<version>/modules/nci_score_reference_parameters.tsv
results/<version>/modules/module_interaction_results.tsv
results/<version>/modules/camera_results.tsv
results/<version>/modules/fgsea_sensitivity.tsv
results/<version>/modules/matched_nonmitochondrial_nulls.tsv.gz
results/<version>/modules/module_reliability.tsv
```

**Matrix rows updated**

C1 and the module parts of C4–C6. This is still same-cohort evidence, not independent replication.

### Task 4. Test the mtDNA–nuclear relationship

**Question answered**

Does AD change the relationship between mtDNA respiratory expression and nuclear OXPHOS expression?

**Why this is needed**

An OXPHOS result can mean different things:

- nuclear OXPHOS genes changed together;
- mtDNA transcript abundance changed;
- the usual relationship between the two compartments changed.

Only the third supports the phrase “mitonuclear alteration.”

**Inputs**

- Task 3 donor mtDNA and nuclear OXPHOS scores;
- NCI reference parameters;
- donor group, age, PMI, and QC metadata.

**Exactly what to do**

Use all three endpoints. Do not choose whichever one gives the smallest P value.

1. **Standardized difference**

   ```text
   NCI-standardized mtDNA score − NCI-standardized nuclear OXPHOS score
   ```

   This asks whether one compartment is higher than the other relative to the NCI reference.

2. **NCI-reference residual**

   In NCI donors, fit:

   ```text
   mtDNA score ~ nuclear OXPHOS score + sex + APOE + age + PMI
   ```

   Freeze that NCI reference relationship. For every donor, calculate how far the observed mtDNA score is above or below the predicted value.

3. **Coupling-slope change**

   Test whether the strength of the mtDNA-versus-nuclear relationship changes with AD and the frozen sex/APOE modifier.

4. Fit the seven direct modifier contrasts for the standardized difference and residual.
5. Fit the group-specific slope model and derive the same direct modifier comparisons for the slope.
6. Adjust the 3 endpoints × 7 modifiers × 3 broad cell classes = 63 tests together.
7. Keep mtDNA and nuclear component scores visible in every table and plot.
8. Repeat using:
   - NCI-trained PC1 scores;
   - leave-one-out or cross-fitted NCI predictions;
   - removal of each mtDNA gene, one at a time;
   - nuclear complex-specific scores;
   - mitochondrial-read-fraction adjustment;
   - the frozen low-quality-profile exclusion.

**Files to produce**

```text
results/<version>/mitonuclear/donor_mitonuclear_scores.tsv.gz
results/<version>/mitonuclear/nci_reference_models.tsv
results/<version>/mitonuclear/mitonuclear_results.tsv
results/<version>/mitonuclear/coupling_slope_results.tsv
results/<version>/mitonuclear/gene_influence.tsv
results/<version>/mitonuclear/qc_sensitivity.tsv
```

**Matrix row updated**

C3.

**What this task cannot prove**

These are RNA abundance relationships. They do not directly measure oxygen consumption, ATP production, mitochondrial mass, or organelle function.

### Task 5. Test whether the effect truly differs between cell types

**Question answered**

Is the modifier effect statistically different between astrocytes, excitatory neurons, and inhibitory neurons?

**Why this is needed**

A smaller P value in astrocytes than neurons does not prove the effects differ. We must directly compare the two estimated effects while recognizing that the same donor contributes several cell types.

**Inputs**

- Task 3 donor module scores;
- broad-cell data and repeated donor IDs;
- frozen cell comparisons;
- mediator-gene expression for focused sensitivity tests.

**Exactly what to do**

1. Stack broad-cell donor scores into one long table.
2. Keep missing donor/cell profiles missing; do not invent values.
3. Fit a mixed model with one random donor effect. In technical form:

   ```text
   fixed:  score ~ 0 + cell_type:diagnosis_sex_APOE_group + age + PMI
   random: ~ 1 | projid
   cell-specific residual variance: varIdent(~ 1 | cell_type)
   ```

4. Use `nlme::lme` for the small number of module outcomes.
5. Directly compare the same modifier between:
   - astrocytes and neuronal classes for `APOE–TUFM`;
   - excitatory and inhibitory neurons for `LAMTOR5–ATP5IF1`;
   - excitatory and inhibitory neurons for `GABARAPL2–CHCHD2`/`PARK7`.
6. Report the difference between cell effects, standard error, CI, P value, q value, donors in each class, and donors present in both classes.
7. Require at least 5 paired donors per required group for fitting and prefer at least 10 for a headline comparison.
8. Repeat with only donors represented in both compared classes.
9. Use `voom`/`dream` or limma donor blocking as a gene-level sensitivity.
10. Record model convergence, donor variance, cell-specific residual variance, and donor influence.

**Files to produce**

```text
results/<version>/heterogeneity/celltype_eligibility.tsv
results/<version>/heterogeneity/celltype_results.tsv
results/<version>/heterogeneity/complete_case_sensitivity.tsv
results/<version>/heterogeneity/model_diagnostics.tsv
```

**Matrix rows updated**

C2 and the cell-context evidence for C4–C6.

**What this task cannot prove**

If this test fails, a result may still be described in a named cell context. It cannot be called “cell-type-specific.”

### Task 6. Test each candidate system in its exact context

**Question answered**

Does each network candidate have a matching donor-level gene/module pattern in the correct cell type?

**Why this is needed**

The network simulations in Round 2 are expensive. A candidate should not enter them if its predicted partner and biological program show no matching donor-level phenotype.

**Inputs**

- Task 2 gene effects;
- Task 3 full and target-excluded module results;
- Task 4 mitonuclear results where relevant;
- Task 5 cell-type comparisons;
- frozen candidate contrasts and expected directions.

**Systems to test**

| System | Main cell context | Fine-type localization | Named mediator/readout | Target-excluded module | Companion result |
|---|---|---|---|---|---|
| `APOE–TUFM` | Astrocytes | `Ast GRM3` if eligible | `TUFM` | Mitochondrial translation without `TUFM` | Nuclear OXPHOS/mitonuclear result |
| `LAMTOR5–ATP5IF1` | Excitatory neurons; inhibitory secondary | Frozen RORB fine types | `ATP5IF1` | ATP synthase without `ATP5IF1` | Nuclear OXPHOS |
| `GABARAPL2–CHCHD2`/`PARK7` | Excitatory neurons | Frozen excitatory fine types | `CHCHD2` primary; `PARK7` secondary | Quality control without `CHCHD2` and `PARK7` | Respiratory/mitonuclear result |

**Exactly what to do**

1. For each system, report the frozen direct modifier effect in the broad primary context.
2. Show the matching within-stratum AD effects only as supporting plots.
3. Report the named mediator effect and CI.
4. Report the target-excluded module effect and CI.
5. Report the companion respiratory result.
6. Add the formal cell-type comparison from Task 5.
7. Localize in the frozen fine type only when it passed Round 0 eligibility.
8. Calculate candidate–mediator correlation after accounting for age, PMI, group, library size, and QC.
9. Test whether candidate–mediator coherence changes with AD/sex/APOE as supporting evidence.
10. Create a provisional result row for each system. Final Gate 3 status waits for Task 7 stability.

The candidate gene itself does not need to be a DEG. The named mediator and target-excluded module provide the phenotype check.

**Files to produce**

```text
results/<version>/candidates/candidate_test_manifest.tsv
results/<version>/candidates/candidate_gene_effects.tsv
results/<version>/candidates/candidate_module_effects.tsv
results/<version>/candidates/candidate_context_results.tsv
results/<version>/candidates/candidate_mediator_coherence.tsv
results/<version>/candidates/candidate_provisional_status.tsv
```

**Matrix rows updated**

C4, C5, and C6 separately. `PARK7` cannot rescue an unsupported primary `CHCHD2` result.

**What this task cannot prove**

Correlation does not prove mediation, molecular direction, or regulation.

### Task 7. Stress-test every planned result

**Question answered**

Does the result remain when one donor, depth imbalance, module-scoring choice, or mitochondrial-read artifact is changed?

**Why this is needed**

A result is not reliable if one donor or one reasonable analysis choice creates it.

**Inputs**

- every frozen headline estimate from Tasks 2–6, including nonsignificant results;
- raw counts and cell membership from Task 1;
- normalized data, models, module scores, and QC metrics;
- frozen random seeds.

**Exactly what to do**

1. **Leave one donor out:** remove each donor once and refit the result. Carry that donor's profiles out of every cell class together.
2. **Donor bootstrap:** resample donors within each of the 12 diagnosis × sex × APOE groups for 1,000 repetitions. Keep all cell profiles from a sampled donor together.
3. **Balance donor counts:** downsample larger required groups to the smaller group for 1,000 repetitions.
4. **Balance nucleus depth:** return to raw nuclei, downsample donors to a common depth, reaggregate, and refit for 100 repetitions.
5. Repeat using only donor/cell profiles with at least 50 nuclei.
6. Repeat mean module scores with the frozen NCI-trained PC1 score.
7. For small modules, remove one gene at a time.
8. Add mitochondrial-read fraction and frozen QC covariates as sensitivity adjustments.
9. Exclude the frozen low-quality profiles and refit.
10. Repeat nuclear-only OXPHOS after removing all mtDNA genes.
11. Apply these tests to every prespecified row, not only the significant ones.

**For every estimate, record**

- full-data effect;
- bootstrap median and 95% interval;
- percentage of bootstrap effects with the prespecified sign;
- smallest and largest leave-one-out effect;
- number of leave-one-out sign reversals;
- largest single-donor influence;
- 20- versus 50-nucleus result;
- downsampled result;
- alternative-score and QC-adjusted result.

**Files to produce**

```text
results/<version>/stability/leave_one_donor_out.tsv.gz
results/<version>/stability/donor_bootstrap.tsv.gz
results/<version>/stability/donor_downsampling.tsv.gz
results/<version>/stability/nucleus_depth_sensitivity.tsv.gz
results/<version>/stability/threshold50_results.tsv
results/<version>/stability/module_score_sensitivity.tsv
results/<version>/stability/mitochondrial_qc_sensitivity.tsv
results/<version>/stability/headline_stability.tsv
```

**Matrix rows updated**

The stability fields for C1–C6.

### Task 8. Stop, review all Round 1 results, and choose the next branch

**Question answered**

Which parts of the planned claim are supported, which are unsupported, and which are too uncertain to judge?

**Why this is needed**

Looking at all evidence at a fixed review point prevents later analyses from quietly changing the original question.

**Inputs**

- every validated Task 1–7 output;
- the frozen manifest and deviations log;
- the gate rules in Section 8;
- C1–C6 in the evidence matrix.

**Exactly what to do**

1. Freeze checksums for every Round 1 result.
2. Reject outputs without `validated_complete` status.
3. List every deviation from Round 0 and explain whether it changes the primary analysis.
4. Fill each C1–C6 row from saved result tables, not by copying numbers from figures.
5. Assign `pass`, `fail`, `inconclusive`, or `not_testable`.
6. Apply the gate rules exactly once.
7. Write the claim wording now allowed.
8. List the candidate/context rows authorized for Round 2.
9. Draft Figures 1 and 2 even if results are negative or inconclusive.

**Files to produce**

```text
results/<version>/review/focal_evidence_matrix.tsv
results/<version>/review/round1_gate_status.tsv
results/<version>/review/round1_gate_report.md
results/<version>/review/permitted_claim_after_round1.md
results/<version>/review/round2_authorization_manifest.tsv
```

The one-page report should show claim ID, exact comparison, effect and CI, q value, donor counts, stability result, decision, permitted wording, and next step.

## 8. The Round 1 gate rules

This is the single authoritative decision table for Round 1.

| Gate | Everyday-language question | All required conditions | If passed | If failed or inconclusive |
|---|---|---|---|---|
| 1A | Does sex or APOE change a respiratory AD effect? | A frozen broad-cell donor module-score modifier has `q ≤ 0.05`; competitive pathway result is directionally compatible; effect meets the frozen SESOI/CI rule; ≥80% bootstrap effects keep the direction; no leave-one-donor-out sign reversal; frozen QC/score sensitivity agrees; at least one carrying contrast has the preferred ≥10 donors in every required group, or later receives direct external modifier replication | Keep sex/APOE modification | Remove it, or label a low-power result inconclusive |
| 1B | Does the effect truly differ between cell types? | Direct between-cell contrast has `q ≤ 0.05`; named-cell effect passes Gate 1A-style stability; paired-donor rule passes | Use “cell-type-specific” | Use “cell-context-resolved” only |
| 2 | Is the mtDNA–nuclear relationship changed? | At least 2 of 3 endpoints agree in direction and have `q ≤ 0.05`; one is the NCI residual or slope; PC1 and QC sensitivities agree | Use “mitonuclear alteration” | Say only nuclear OXPHOS, mtDNA transcript abundance, or respiratory program—whichever is actually supported |
| 3A | Does `APOE–TUFM` have a matching astrocyte phenotype? | Target-excluded translation module has `q ≤ 0.05`, meets SESOI/CI and stability rules; `TUFM` has compatible direction plus candidate-family `q ≤ 0.10` or a CI excluding a meaningful opposite effect | Authorize this system for Round 2 | Do not run its Round 2 validation |
| 3B | Does `LAMTOR5–ATP5IF1` have a matching neuronal phenotype? | Same rule using target-excluded ATP synthase and `ATP5IF1` | Authorize this system for Round 2 | Do not run its Round 2 validation |
| 3C | Does `GABARAPL2–CHCHD2`/`PARK7` have a matching excitatory phenotype? | Same rule using target-excluded quality control and primary `CHCHD2`; `PARK7` is secondary | Authorize this system for Round 2 | Do not run its Round 2 validation; `PARK7` cannot rescue `CHCHD2` |

Five donors per group permits model fitting; it is not strong confirmation. A candidate or modifier carried only by below-10 ε2 groups remains provisional/inconclusive until directly supported in adequate external strata.

### Round 1 branching table

| Result | What it means | Next action |
|---|---|---|
| Gates 1A, 1B, and 2 pass | Full cell-type-specific sex/APOE mitonuclear phenotype is supported internally | Run Round 2 only for candidate Gates 3A–C that passed |
| Gates 1A and 2 pass; 1B does not | Modifier and mitonuclear result survive, but cell-type difference is unproven | Use “cell-context-resolved”; run Round 2 only for passing candidates |
| Gate 1A passes; Gate 2 fails; nuclear OXPHOS remains | Sex/APOE changes a nuclear respiratory program, not proven mitonuclear imbalance | Rewrite the claim; validate only candidates that match the narrower phenotype |
| Gate 2 passes; Gate 1A fails | A mitonuclear AD result may exist, but sex/APOE modification is unsupported | Stop modifier-specific KDA; write a new narrower authorization |
| Gates 1A and 2 fail | The strong phenotype is unsupported | Stop Rounds 2–4 for this claim and report the result |
| One candidate gate fails | That candidate lacks its required donor phenotype | Remove only that candidate from Round 2 |
| A result is inconclusive | The data cannot distinguish a meaningful effect from no effect | Seek more donors or report uncertainty; do not call it a pass |

## 9. Later rounds: do only what Round 1 authorizes

### Round 2. Test surviving network candidates against fair controls

**Why this is needed**

KDA can nominate a gene because the query contains related genes or because the candidate is a highly connected hub. Round 2 asks whether the candidate remains unusual after controlling for both problems.

**Inputs**

- only candidate/context rows listed in `round2_authorization_manifest.tsv`;
- donor-supported directional signatures and modules;
- cell-matched Bayesian networks;
- exact tested-gene × network background;
- complete KDA results, not significant rows only;
- frozen layers, seeds, and candidate family.

**Exactly what to do**

1. Use only primary directional mitochondrial signatures.
2. Require at least 10 effective query genes.
3. Remove all query genes from the possible driver list. This prevents a query gene from nominating itself.
4. Exclude mtDNA structural genes as candidate drivers.
5. Test network layers 1, 2, and 3 separately and correct for choosing among layers.
6. Save every tested candidate, including nonsignificant results.
7. Generate at least 1,000 **query-matched nulls**: random gene lists with similar size, expression, detection, mitochondrial composition, mtDNA fraction, degree, and coverage.
8. Generate at least 1,000 **topology-matched nulls**: compare the candidate with genes having similar in-degree, out-degree, centrality, local/global status, layer-neighborhood size, expression, detection, and coverage. A directed degree-preserving rewired network can also be used.
9. Perturb edges and test whether the candidate remains highly ranked.
10. Build one donor-level coexpression/MEGENA network from broad-cell pseudobulk.
11. Test whether the candidate and mediator occupy the same preserved mitochondrial module or are closer than degree-matched chance.
12. Remove query genes and the shared respiratory core, then test whether the three systems still have more distinct neighborhoods than matched candidate pairs.

**Gate 4: every condition must pass for each candidate**

- corrected KDA `q ≤ 0.05`;
- empirical `q ≤ 0.05` under both null families;
- observed evidence above the 95th null percentile;
- top-decile candidate rank in at least 80% of network perturbations;
- alternative-network proximity/module support at `q ≤ 0.05`;
- alternative-network support preserved in at least 80% of donor bootstraps.

**Files to produce**

```text
results/<version>/kda/kda_fixed_layer_complete.tsv.gz
results/<version>/kda/kda_query_nulls.tsv.gz
results/<version>/kda/kda_topology_nulls.tsv.gz
results/<version>/kda/network_perturbation_results.tsv.gz
results/<version>/networks/alternative_network_support.tsv
results/<version>/networks/candidate_distinctness.tsv
results/<version>/kda/robust_driver_summary.tsv
```

If none pass, keep the donor respiratory result and describe all KDA candidates as hypothesis-generating. Network arrows never prove activation, inhibition, or causality.

### Round 3A. Independent RNA replication

**Why this is needed**

A result can be stable inside ROSMAP and still be specific to that cohort. Independent replication asks whether the frozen result appears in different people.

**Preferred input**

SEA-AD donor-level single-nucleus RNA data if Round 0 confirms the needed metadata and coverage.

**Exactly what to do**

1. Keep the ROSMAP modules, directions, contrasts, and broad-cell mappings frozen.
2. Map cell classes before viewing validation effects.
3. Rebuild donor-level profiles and the frozen module scores.
4. Test the respiratory/mitonuclear result without searching for new pathways.
5. Test surviving candidate/mediator coherence.
6. Repeat the direct sex/APOE modifier only if every required external group is adequately represented.
7. Compare standardized ROSMAP and validation effects with CIs.
8. Record differences in region, diagnosis, pathology, and cell taxonomy.

**Gate 5A**

Independent replication requires the same direction and `q ≤ 0.05` for the frozen module or success under a frozen meta-analysis. If external sex/APOE groups are inadequate, the dataset can replicate the broad respiratory program but cannot replicate the modifier claim.

Save:

```text
results/<version>/validation/seaad_replication.tsv
```

### Round 3B. Protein support

**Why this is needed**

RNA abundance is not the same as protein abundance. Protein data provide a different measurement of the same biological idea.

**Exactly what to do**

1. Prefer an independent MSBB/BLSA protein cohort when accessible.
2. Test only frozen OXPHOS, translation, ATP-synthase, quality-control, candidate, and mediator results.
3. Report protein coverage before testing.
4. Label missing proteins `not_measured`, not failed.
5. Compare protein direction and effect with the RNA result without demanding that every gene match.
6. Use sex/APOE interactions only when sample size supports the frozen contrast.
7. Label overlapping ROSMAP proteomics as same-cohort protein support, not independent replication.

**Gate 5B**

Protein support requires a concordant frozen candidate/mediator or module result at `q ≤ 0.05`.

Save:

```text
results/<version>/validation/protein_validation.tsv
```

### Round 4. Optional experiments for causal language

Only strong Round 1–3 survivors should enter this round. Use cell-context-matched, preferably isogenic models and include:

- loss and gain of candidate function;
- measurement of the named mediator and respiratory program;
- mediator rescue;
- direct mitochondrial function such as oxygen consumption or ATP-related readouts;
- cell-health and toxicity controls;
- randomization, blinding, biological replicates, and a written sample-size plan.

Only perturbation plus rescue can support words such as “regulates,” “mediates,” or “drives respiration.”

## 10. Figures and when to make them

| Figure | What it should show | Needed work | Earliest final version |
|---|---|---|---:|
| Figure 1 | Direct sex/APOE respiratory-module effects, CIs, donor counts, and formal cell-type differences | Round 1 Tasks 2, 3, 5, and 7 | After Round 1 |
| Figure 2 | Donor mtDNA versus nuclear OXPHOS, residual/imbalance effects, coupling slopes, and stability | Round 1 Tasks 4 and 7 | After Round 1 |
| Figure 3 | One evidence row per surviving candidate: donor phenotype, layer-3 subnetwork, two null percentiles, perturbation stability, and alternative network | Passing Gate 3 plus Round 2 | After Round 2 |
| Figure 4 | ROSMAP-versus-independent-RNA effects and protein evidence, with `not_measured` separate from `unsupported` | Round 3 | After Round 3 |

### Figure 1 details

Use a Yu-inspired signed dot heatmap plus compact forest plots. Show the direct interaction estimate, not only six separate AD effects. Every panel must display 95% CI, q value, and analysis-specific donor counts.

### Figure 2 details

Use Mathys-inspired donor-level scatter and effect panels. Show mtDNA and nuclear components, the NCI prediction line, residuals, slope changes, bootstrap consistency, leave-one-out influence, and the small male-ε2 sample size.

### Figure 3 details

Use Wang-inspired candidate rows. Color nodes by signed donor-level AD effect, size nodes by connectivity, mark mitochondrial genes, and call network lines edges rather than activation/inhibition arrows. Supply Cytoscape-ready node and edge tables.

### Figure 4 details

Show standardized effects and CIs in discovery and validation data. Separate independent RNA replication, independent protein support, same-cohort protein support, `not_measured`, and `tested_unsupported`.

Existing Yu-style discovery figures remain useful background or supplementary figures. They should not replace the donor-level main figures.

Every figure requires:

- plotted-data TSV;
- SVG or PDF vector graphic;
- PNG preview;
- caption;
- short methods note;
- analysis version and source-result IDs.

## 11. Immediate work checklist

This is the practical order to follow.

- [ ] Create the new analysis version and artifact manifest.
- [ ] Fix and record ambiguous gene identifiers.
- [ ] Freeze broad/fine cell contexts and seven direct modifier contrasts.
- [ ] Freeze the four primary modules and candidate-specific target-excluded modules.
- [ ] Fill in the numeric SESOI, CI rule, and QC-agreement rule.
- [ ] Produce the 20-/50-nucleus donor eligibility table.
- [ ] Confirm broad-cell and module coverage is sufficient.
- [ ] Extend the pseudobulk code to create broad cell classes.
- [ ] Run and validate donor pseudobulk on Minerva.
- [ ] Run the seven direct interaction models and save exact CIs plus TMM logCPM.
- [ ] Calculate donor module scores, `camera`, and matched non-mitochondrial controls.
- [ ] Run the three mitonuclear endpoints.
- [ ] Run formal cell-type comparisons.
- [ ] Assemble the three provisional candidate-system results.
- [ ] Run all donor, depth, score, and QC stability checks.
- [ ] Stop and hold the locked Round 1 review.
- [ ] Update C1–C6 and write the Round 2 authorization file.
- [ ] Run Round 2 only for authorized candidates.
- [ ] Run Round 3 only for frozen surviving claims.

## 12. Common output requirements

Every inferential result table should contain these fields when applicable:

```text
analysis_version, round, task_id, claim_id, gate,
cell_context, contrast_id, exact_comparison, effect,
standard_error, ci95_low, ci95_high, p_value, q_value,
multiple_testing_group, donor_counts, nucleus_counts,
tested_module_genes, tested_gene_background,
sensitivity_status, validation_status,
input_checksum, code_checksum, random_seed
```

Use `NA` when a field does not apply. Do not drop the column or leave the meaning unclear.

Suggested folder structure:

```text
results/<version>/audit/
results/<version>/pseudobulk/
results/<version>/modules/
results/<version>/mitonuclear/
results/<version>/heterogeneity/
results/<version>/candidates/
results/<version>/stability/
results/<version>/review/
results/<version>/kda/
results/<version>/networks/
results/<version>/validation/
results/<version>/figures/
```

## 13. Work that is not part of Round 1

Do not expand the first round with attractive but unrelated analyses:

- unrestricted searches across fatty-acid oxidation, TCA, import, iron, stress, or other pathway catalogues;
- new Tier 2/3 candidate lists;
- cognition, resilience, or detailed pathology analyses;
- GWAS, QTL, or chromatin integration;
- circular-plot redesign;
- full KDA reruns, network nulls, or multiple new networks before the Round 1 review;
- all-54-fine-cell primary claims;
- external outcome analysis before Round 1 definitions and results are locked;
- causal language from RNA or network results.

These can become later projects only when a surviving claim or a failed gate gives them a specific purpose.

## 14. Essential source files

Professor requirements:

- [August 4 meeting notes](../email_notes/notes_08042026.txt)
- [August 4 subnetwork request](../email_notes/email_08042026.txt)

Current project interpretation:

- [Joint Phase 11–12 mitochondrial discussion](../analysis/phase11_phase12_joint_mitochondrial_discussion.md)
- [Detailed evidence for the three candidate systems](../analysis/phase11_phase12_selected_mitochondrial_connections.md)
- [Most recent DEG–KDA presentation](<../presentations/DEG-KDA Final Results v2.pdf>)

Current network results:

- [KDA results](../../results/minerva_production/12_kda/kda_results.tsv.gz)
- [KDA run manifest](../../results/minerva_production/12_kda/kda_run_manifest.tsv)

Paper and figure precedents:

- [Mathys single-cell atlas](<../related_papers/mathys single-cell atlas reveals correlates.pdf>)
- [Yu sex/APOE study](../related_papers/yu_paper/Yu_sex_apoe.pdf)
- [Wang multiscale protein-network study](../related_papers/wang_multiscale_modeling.pdf)

Independent validation resource:

- [SEA-AD resource and analysis code](https://github.com/AllenInstitute/SEA-AD_2024)
