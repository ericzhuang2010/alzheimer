# Phase 11 explained: multiple testing, mitochondrial priorities, and every final figure

## 1. The short answer

Yes: the main biological interest of this project is mitochondrial biology in Alzheimer's disease, especially whether mitochondrial RNA patterns differ by sex, APOE group, diagnosis, and brain cell type.

However, the project does **not** test only mitochondrial genes. It first performs differential-expression analysis on every gene that passes the relevant expression filter. It then marks the mitochondrial subsets and gives them their own prespecified multiple-testing corrections.

That design can be summarized as:

```text
all adequately detected genes
            |
            v
genome-wide differential-expression results
            |
            +------------------------------+
            |                              |
            v                              v
  mitochondrial subsets            genome-wide context
  - 13 mtDNA genes                  - specificity checks
  - MitoCarta genes                 - background for pathways
  - MitoCarta pathways              - global sensitivity analysis
            |
            v
Phase 11: apply clearly defined FDR corrections
```

Phase 11 is the project's statistical bookkeeping and decision-rule phase. It does not fit a new disease model. It gathers completed results, defines which tests belong together, applies Benjamini-Hochberg false-discovery-rate corrections, labels mitochondrial results, validates the combined tables, and writes final corrected outputs.

The implementation is [scripts/11_apply_multiple_testing.R](../scripts/11_apply_multiple_testing.R). The multiple-testing settings are frozen in [config/analysis_parameters.yml](../config/analysis_parameters.yml).

## 2. Why keep genome-wide results if mitochondria are the main interest?

Keeping genome-wide results is useful for five reasons.

1. **It avoids discarding information too early.** A gene not listed in MitoCarta could still influence mitochondria indirectly.
2. **It provides context.** We can ask whether mitochondrial genes look unusual compared with the rest of the transcriptome.
3. **It supplies a pathway background.** A pathway test needs to compare genes inside a pathway with an appropriate set of other tested genes.
4. **It supports sensitivity analysis.** A mitochondrial result may pass a prespecified mitochondrial correction but not an extremely strict correction over every gene, cell type, and contrast. Reporting both shows how dependent the conclusion is on the chosen question.
5. **It makes the analysis auditable.** Readers can see that the mitochondrial family was selected because of the research question, not chosen afterward because it happened to contain small p-values.

The biological priority and the statistical workflow are therefore different ideas:

- **Biological priority:** mitochondrial genes and pathways.
- **Initial measurement and DE testing:** every adequately detected gene.
- **Focused decision rules:** separate corrections for mtDNA, MitoCarta, pathways, and similarity.

## 3. Essential vocabulary

### 3.1 Feature and gene

In a single-cell RNA count matrix, a **feature** is one row that the assay can record. In this project, a feature is essentially a gene or gene-level identifier.

Each source RNA matrix has 33,538 feature rows. That does not mean all 33,538 genes are detectably expressed in every cell type or tested in every contrast. Expression filters reduce the number tested.

For example, the production MAST diagnostics report between 4,328 and 12,798 tested genes per fitted contrast, with an average of about 9,198.

### 3.2 mtDNA protein-coding genes

Human mitochondrial DNA directly encodes 13 proteins. The configured list is:

```text
MT-ND1, MT-ND2, MT-CO1, MT-CO2, MT-ATP8, MT-ATP6, MT-CO3,
MT-ND3, MT-ND4L, MT-ND4, MT-ND5, MT-ND6, MT-CYB
```

These are called the **mtDNA protein-coding genes** in this project. They form the narrowest and most directly mitochondrial gene set.

### 3.3 MitoCarta genes

MitoCarta 3.0 is a curated inventory of proteins associated with mitochondria. Most MitoCarta proteins are encoded by nuclear DNA, not by mtDNA.

The frozen MitoCarta source contains 1,136 canonical entries. The assay can contain more mapped feature labels than canonical entries because aliases or multiple feature identifiers can map to the same canonical mitochondrial gene. In the current annotation tables, approximately 1,194 assay features per RDS are marked as MitoCarta features, and roughly 1,138-1,161 have nonzero counts depending on the source object.

The relationship is approximately:

```text
13 mtDNA protein genes
        are contained within
about 1,100-1,200 MitoCarta-related gene features
        are contained within
up to 33,538 assayed gene features
```

### 3.4 Cell type, donor, and nucleus

- A **donor** is one person.
- A **nucleus** is one measured nucleus from that person's brain tissue.
- A **fine cell type** is one of the 54 high-resolution cell clusters.
- A **pseudobulk sample** sums counts from all eligible nuclei belonging to one donor and one fine cell type.

One donor can contribute many nuclei. Thousands of nuclei from one person are not thousands of independent people. The primary pseudobulk branch therefore treats the donor as the independent sample.

### 3.5 Contrast

A **contrast** is a planned statistical comparison. Examples are:

```text
AD_vs_NCI__Female__e33
AD_effect_Female_minus_Male__e4
AD_effect_e2_minus_e33__Male
AD_effect_heterogeneity_across_sex_APOE
```

The first asks whether AD and NCI differ among female APOE e33 donors. The second asks whether the AD-versus-NCI effect differs between females and males among APOE e4 donors. The final contrast asks whether the AD effect is heterogeneous anywhere among the six sex-APOE groups.

### 3.6 Method branch

The project keeps two differential-expression branches separate.

| Branch | Basic idea | Role |
|---|---|---|
| `pseudobulk` | Sum counts per donor and fine cell type, then use edgeR quasi-likelihood models. | Primary donor-level analysis. |
| `mast` | Use Seurat `FindMarkers` with MAST on nucleus-level normalized values and covariates. | Paper-comparability analysis. |

Phase 11 never pools the p-values from these two branches into one family. Every global correction is performed separately for pseudobulk and MAST.

### 3.7 Effect size, p-value, and FDR

- An **effect size** says how large a difference is and usually gives its direction.
- A **p-value** asks how surprising the observed test statistic would be if the null hypothesis were true.
- **FDR**, or false discovery rate, is a correction for examining many hypotheses.

A p-value is not the probability that the biological claim is true. An FDR of 0.05 is also not a statement that one particular result has exactly a 5% chance of being false. It is a rule designed to control the expected fraction of false discoveries across a declared family of tests.

## 4. Why multiple testing is necessary

Imagine flipping a fair coin four times. Getting four heads is unusual, but possible. Now imagine giving 10,000 students four flips each. Some student will probably get four heads just by chance.

Gene testing has the same issue. If 10,000 unrelated null hypotheses are each tested at raw `p < 0.05`, chance alone could produce roughly:

```text
10,000 x 0.05 = 500
```

small p-values.

This does not mean all 500 would be false in a real experiment. It illustrates why `p < 0.05` cannot be interpreted without knowing how many opportunities there were to obtain a small p-value.

### 4.1 What is a testing family?

A **testing family** is the set of hypotheses being considered together for one scientific question.

Examples in this project are:

- all tested genes within one method/cell-type/contrast;
- all mtDNA gene tests across every cell type and contrast in one method branch;
- all MitoCarta gene tests across every cell type and contrast in one method branch; and
- all eligible pathway-rank tests in one method branch.

The family must be declared clearly because changing the family changes the adjusted FDR.

### 4.2 How Benjamini-Hochberg works

Phase 11 uses the Benjamini-Hochberg method, abbreviated **BH**.

For a family containing `m` p-values:

1. Sort the p-values from smallest to largest.
2. Give them ranks `1, 2, ..., m`.
3. Initially scale each sorted p-value by `m / rank`.
4. Enforce a nondecreasing adjusted sequence and cap values at 1.
5. Return each adjusted value to its original test row.

For a small example:

| Sorted rank | Raw p-value | Initial BH value |
|---:|---:|---:|
| 1 | 0.001 | `0.001 x 5 / 1 = 0.005` |
| 2 | 0.010 | `0.010 x 5 / 2 = 0.025` |
| 3 | 0.030 | `0.030 x 5 / 3 = 0.050` |
| 4 | 0.040 | `0.040 x 5 / 4 = 0.050` |
| 5 | 0.200 | `0.200 x 5 / 5 = 0.200` |

The first four pass an FDR threshold of 0.05 in this toy example.

### 4.3 Why one row can have several FDR values

A mitochondrial gene row can belong to several scientifically meaningful families:

1. all genes in its own contrast;
2. all genome-wide gene tests across the branch;
3. all mtDNA tests across the branch, if it is one of the 13 mtDNA genes; and
4. all MitoCarta tests across the branch, if it is a MitoCarta gene.

Consequently, one raw p-value can have several adjusted values. This is not a contradiction. Each FDR answers a different question.

For example:

- `fdr_bh_within_contrast < 0.05` means the gene stands out among genes tested in that one contrast.
- `fdr_bh_mtdna_global < 0.05` means it stands out when all prespecified mtDNA tests across cell types and contrasts are considered.
- `fdr_bh_global_genome_sensitivity < 0.05` means it survives an extremely broad correction across all gene-test rows in that method branch.

The targeted mitochondrial family is scientifically legitimate because mitochondrial biology was specified as the research focus before examining the final results. It would not be legitimate to invent a small family afterward merely because its members looked promising.

## 5. What Phase 11 does and does not do

### 5.1 Phase 11 does

- Require all needed upstream status files to say `validated_complete`.
- Read pseudobulk gene results from Phase 07.
- Read MAST gene results from Phase 08.
- Read mitochondrial pathway results from Phase 09.
- Read Zhang-Yu similarity results from Phase 10.
- Read the frozen Phase 03 mitochondrial annotations.
- Combine the two gene-result branches into a consistent schema.
- Add mtDNA and MitoCarta flags.
- Apply BH correction to declared global families.
- Add family identifiers so every adjusted result has an explicit scope.
- Write a family manifest, validation checks, checksums, and a status summary.

### 5.2 Phase 11 does not

- Read the raw nucleus matrix and refit differential expression.
- Change a log fold change.
- Change a raw p-value generated upstream.
- combine pseudobulk and MAST into a meta-analysis.
- create a new biological pathway definition.
- calculate the Zhang-Yu similarity score itself.
- make the final PDF figures.

The final PDFs are made later by Phase 15. Phase 11 supplies corrected tables used directly by Figures 05, 06, and 08.

## 6. Where Phase 11 fits in the pipeline

```text
Phase 03: frozen gene and mitochondrial annotations
                         |
Phase 07: pseudobulk DE -+
                         |
Phase 08: MAST DE -------+----> Phase 11: global multiple testing
                         |                  |
Phase 09: pathways ------+                  +--> Phase 12 sensitivity
                         |                  +--> Phase 14 validation
Phase 10: similarity ----+                  +--> Phase 15 figures
```

Phase 11 is a **global** task. It runs once after all per-RDS Phase 07-09 jobs and the global Phase 10 job are complete. This prevents an early-finishing cell-class object from receiving an artificially incomplete "global" correction.

## 7. Inputs and prerequisites

Phase 11 looks for these inputs under the configured output root.

| Upstream phase | Required files | Purpose |
|---|---|---|
| Phase 03 | `03_annotations/tested_gene_universe.tsv` and `annotation_status.tsv` | Map each gene to mtDNA and MitoCarta flags. |
| Phase 07 | Every `07_pseudobulk_de/*.pseudobulk_de.tsv.gz` plus status files | Primary gene-level p-values, fold changes, and within-contrast FDR. |
| Phase 08 | Every `08_mast/*.mast_de.tsv.gz` plus status files | Paper-comparable gene-level results. |
| Phase 09 | Every `09_downstream/*.pathway_results.tsv` plus status files | Pathway-rank and over-representation p-values. |
| Phase 10 | `10_downstream/similarity_results.tsv` plus status | Similarity scores, empirical p-values, and within-comparison FDR. |

The script checks that:

- every required status file exists;
- each status table has exactly one row;
- its schema name is correct;
- `validation_status` is exactly `validated_complete`;
- the number of result files agrees with the number of validated status files; and
- the configuration contains all eight required family names.

If any requirement fails, Phase 11 stops instead of making a partial result look final.

## 8. The exact Phase 11 workflow

### Step 1: read configuration

The script reads:

- the project root;
- the scientific configuration;
- the RDS manifest;
- the output root;
- whether the run is pilot or production;
- `alpha = 0.05`; and
- the Yu-comparable absolute fold-change threshold of 1.3.

The log2 threshold corresponding to a 1.3-fold change is:

```text
log2(1.3) = approximately 0.3785
```

### Step 2: verify the family definitions

Phase 11 refuses to continue unless all eight expected family names are present in the configuration. This is an important protection against silently forgetting a planned correction.

### Step 3: locate and validate upstream artifacts

The script discovers every production or pilot result file by filename pattern. It then reads and validates all associated status files.

### Step 4: checksum every upstream input

Before reading the data, Phase 11 computes a SHA-256 checksum for every upstream result and status file. A checksum is like a long digital fingerprint. If one byte changes, the fingerprint should change.

The same checksums are calculated again after output generation. Phase 11 fails validation if an upstream input changed while it was running.

### Step 5: construct the gene annotation map

The Phase 03 tested-gene universe contains one row per source RDS and feature. Phase 11 collapses this to one row per gene and asks:

```text
Was this gene ever marked as an mtDNA protein gene?
Was this gene ever marked as a MitoCarta gene?
```

Missing matches are assigned `FALSE`, not silently left ambiguous.

### Step 6: standardize pseudobulk and MAST gene tables

Both branches are converted to a common set of columns, including:

- method branch;
- RDS ID;
- fine cell type;
- contrast identifiers;
- gene;
- log2 fold change;
- raw p-value; and
- within-contrast FDR.

The two standardized tables are stacked, but the `method_branch` column keeps them separate.

### Step 7: attach mitochondrial flags and family IDs

Each gene row receives:

- `is_mtdna_protein_gene`;
- `is_mitocarta`;
- a genome-wide global family ID;
- an mtDNA family ID when applicable; and
- a MitoCarta family ID when applicable.

### Step 8: calculate gene-level global FDR values

Within each method branch, Phase 11 calculates:

```text
fdr_bh_global_genome_sensitivity
fdr_bh_mtdna_global
fdr_bh_mitocarta_global
```

Non-mtDNA genes receive `NA` for the mtDNA-family FDR. Non-MitoCarta genes receive `NA` for the MitoCarta-family FDR. This prevents a targeted FDR from being mistakenly attached to an ineligible gene.

### Step 9: add decision flags

The gene table receives four major Boolean flags:

```text
yu_comparable_deg
global_genome_significant
mtdna_global_significant
mitocarta_global_significant
```

The Yu-comparable rule is:

```text
within-contrast FDR < 0.05
AND
absolute log2 fold change > log2(1.3)
```

The global flags use their corresponding global FDR values and `alpha = 0.05`.

Every gene row also gets this warning:

```text
unequal_power_possible;absence_of_evidence_is_not_evidence_of_no_effect
```

That warning matters because small donor groups, rare cell types, and lowly expressed genes have less power. A nonsignificant result does not prove that the true effect is exactly zero.

### Step 10: correct pathway results

Phase 09 already produced two tests for each eligible pathway row:

1. a ranked-distribution test; and
2. an over-representation analysis, abbreviated ORA.

Phase 11 applies BH correction across every eligible pathway row in one method branch, separately for the ranked test and ORA.

Rows with `terminal_status != validated_complete` remain outside the global calculation and keep missing global FDR values.

### Step 11: correct similarity results

Phase 10 already computed Zhang-Yu similarity scores and empirical p-values. Phase 11 applies BH across every similarity gene/comparison row within one method branch to create:

```text
empirical_fdr_bh_global_method_branch
```

This is stricter than the Phase 10 FDR calculated separately within one comparison.

### Step 12: create the family manifest

For each method branch and family type, Phase 11 records:

- family name;
- entity type;
- correction method;
- alpha;
- scope in plain language;
- number of tests;
- number of subfamilies; and
- number passing the relevant FDR threshold.

This table is the clearest answer to the question, "How many tests were corrected together?"

### Step 13: run validation checks

Phase 11 verifies uniqueness, FDR ranges, completeness of mitochondrial-family values, pathway and similarity correction coverage, configured family coverage, execution labels, upstream validation, and input immutability.

### Step 14: write outputs atomically

Each table is first written to a temporary filename and then renamed to its final name. This reduces the chance that a crash leaves a half-written file with a final-looking path.

## 9. The eight testing families

| Family | What belongs to it? | Where its first correction is made | Main interpretation |
|---|---|---|---|
| `genomewide_gene_within_method_cell_type_contrast` | All genes tested in one method branch, fine cell type, and contrast. | Phase 07 or 08; Phase 11 preserves it. | Does this gene stand out within this particular DE analysis? |
| `genomewide_gene_global_across_cell_types_and_contrasts_sensitivity` | Every gene-test row across all cell types and contrasts, separately per branch. | Phase 11 | Does it survive the broadest gene-level sensitivity correction? |
| `mtdna_gene_global_across_cell_types_and_contrasts` | All rows for the 13 mtDNA genes across cell types and contrasts, separately per branch. | Phase 11 | Does the result survive the prespecified narrow mitochondrial-genome family? |
| `mitocarta_gene_global_across_cell_types_and_contrasts` | All MitoCarta gene-test rows across cell types and contrasts, separately per branch. | Phase 11 | Does it survive the broader mitochondrial-proteome family? |
| `pathway_rank_global_across_cell_types_and_contrasts` | Every eligible pathway ranked-distribution test, separately per branch. | Phase 11 | Do pathway genes collectively shift in signed rank evidence? |
| `pathway_ora_global_across_cell_types_and_contrasts` | Every eligible pathway over-representation test, separately per branch. | Phase 11 | Is the pathway enriched for genes called significant upstream? |
| `similarity_within_method_comparison` | Similarity genes within one branch and one comparison definition. | Phase 10; Phase 11 records it. | Is a similarity result unusual within this specific comparison? |
| `similarity_global_across_comparisons_sensitivity` | Every similarity gene/comparison row in one method branch. | Phase 11 | Does similarity survive correction across all comparison definitions? |

### 9.1 Why the branches are separated

Pseudobulk and MAST use different observation structures and statistical models. Treating their p-values as interchangeable members of one correction family would blur two distinct analyses. Phase 11 therefore gives each branch its own family ID and BH calculation.

### 9.2 Why mtDNA and MitoCarta are separate

The 13 mtDNA genes address a narrow, highly prespecified question. MitoCarta addresses a much broader mitochondrial question involving approximately a thousand nuclear- and mitochondrial-encoded genes.

A smaller family usually has a less severe multiple-testing burden. That increased sensitivity is valid only because the small family was scientifically specified in advance.

### 9.3 Why pathway rank and ORA are separate

They test different things:

- The **rank test** uses the whole signed gene-ranking distribution.
- **ORA** counts how many pathway genes crossed a significance threshold.

A pathway could have many modest shifts and pass the rank test without containing many individually significant genes. Conversely, a pathway could contain a small cluster of called genes and look stronger in ORA.

## 10. An implementation caveat about interaction labels

The current Phase 11 code creates `hypothesis_context` using this logic:

```text
if contrast_kind == "interaction_df": tested_interaction
otherwise: within_group_ad_vs_nci
```

However, the Phase 07 contrast manifest labels both direct one-number contrasts and one-number interaction contrasts as `single_df`. It uses `multi_df` for the global heterogeneity test. It does not use `interaction_df`.

Therefore:

> Do not use `hypothesis_context` to decide whether a row is a direct AD-versus-NCI comparison or an interaction.

Use these fields instead:

- `contrast_family = AD_vs_NCI` for direct within-group comparisons;
- `contrast_family = sex_interaction` for sex interactions;
- `contrast_family = apoe_interaction` for APOE interactions; and
- `contrast_family = global_heterogeneity` for the multi-df global test.

This is a labeling issue in the combined output. It does not change upstream effect sizes or p-values, but it is important for correct interpretation.

## 11. Phase 11 output files

The intended output directory is:

```text
results/<execution_stage>/11_multiple_testing/
```

### 11.1 `gene_multiple_testing.tsv.gz`

This is the combined pseudobulk and MAST gene table.

| Column | Plain-language meaning |
|---|---|
| `gene` | Gene or assay feature identifier. |
| `method_branch` | `pseudobulk` or `mast`. |
| `rds_id` | Broad source cell-class object. |
| `cell_type_high_resolution` | Fine cell type. |
| `contrast_id` | Globally unique contrast key. |
| `contrast_family` | Direct AD/NCI, sex interaction, APOE interaction, or global heterogeneity. |
| `contrast_name` | Human-readable comparison name. |
| `hypothesis_context` | Intended context label; currently unreliable for interaction identification, as explained above. |
| `logFC` | Estimated log2 fold change for signed single-df gene contrasts. |
| `p_value` | Raw upstream p-value. |
| `fdr_bh_within_contrast` | BH FDR among genes in that particular branch and contrast. |
| `within_contrast_family_id` | Exact ID of that within-contrast family. |
| `is_mtdna_protein_gene` | Whether this is one of the 13 configured mtDNA genes. |
| `is_mitocarta` | Whether the feature maps to MitoCarta. |
| `global_genome_family_id` | Broad genome-wide family ID for the branch. |
| `mtdna_family_id` | mtDNA family ID, or missing for non-mtDNA genes. |
| `mitocarta_family_id` | MitoCarta family ID, or missing for non-MitoCarta genes. |
| `fdr_bh_global_genome_sensitivity` | BH FDR across every gene-test row in the branch. |
| `fdr_bh_mtdna_global` | BH FDR across all mtDNA rows in the branch. |
| `fdr_bh_mitocarta_global` | BH FDR across all MitoCarta rows in the branch. |
| `yu_comparable_deg` | Within-contrast FDR below 0.05 and absolute fold change above 1.3. |
| `global_genome_significant` | Broad global genome FDR below 0.05. |
| `mtdna_global_significant` | mtDNA global FDR below 0.05. |
| `mitocarta_global_significant` | MitoCarta global FDR below 0.05. |
| `interpretation_guardrail` | Warning about unequal power and nonsignificant findings. |

### 11.2 `pathway_multiple_testing.tsv.gz`

This table preserves all Phase 09 pathway columns and adds:

- execution and output labels;
- the global rank-family ID;
- the global ORA-family ID;
- `rank_fdr_bh_global_branch`; and
- `ora_fdr_bh_global_branch`.

Only rows with `terminal_status = validated_complete` enter these global corrections.

### 11.3 `similarity_multiple_testing.tsv.gz`

This table preserves all Phase 10 similarity details and adds:

- `global_similarity_family_id`; and
- `empirical_fdr_bh_global_method_branch`.

The table still contains the number of paired tests, similarity components, score, empirical p-value, within-comparison FDR, permutation count, seed, and mitochondrial flags.

### 11.4 `multiple_testing_family_manifest.tsv`

This is one row per method-branch/family combination. There should be 16 rows:

```text
8 family types x 2 method branches = 16 rows
```

For pathway and similarity families, the method branches are also pseudobulk and MAST because those upstream results were calculated separately from each DE branch.

### 11.5 `multiple_testing_checks.tsv`

The 13 checks are:

1. gene keys are unique;
2. pathway keys are unique;
3. similarity keys are unique;
4. every gene p-value has explicit family IDs;
5. gene FDR values are between 0 and 1;
6. every mtDNA row has an mtDNA FDR and every non-mtDNA row does not;
7. every MitoCarta row has a MitoCarta FDR and every non-MitoCarta row does not;
8. every eligible pathway row has both global pathway FDRs;
9. every similarity row has a global similarity FDR;
10. all configured families appear in the family manifest;
11. execution labels match the configured stage;
12. all upstream status files are validated; and
13. upstream artifact checksums are unchanged.

### 11.6 `multiple_testing_artifacts.tsv`

This inventory records the path, size, SHA-256 checksum, row count, and validation status of the three main corrected tables, the family manifest, and the checks table.

### 11.7 `multiple_testing_status.tsv`

This one-row summary records:

- execution provenance;
- script and configuration checksums;
- BH and alpha settings;
- row counts;
- counts of mitochondrial test rows;
- counts passing each global family;
- runtime and peak memory; and
- the final Phase 11 validation status.

The `execution_phase` field in this file is an execution-scope label such as pilot `1` or production `2`. It is not the scientific phase number. The scientific task is Phase 11 regardless of that field.

## 12. A concrete pilot example

The checked-in local pilot contains Phase 11 outputs and is useful for understanding the schema. It is **not** a final biological result because it includes only the vasculature pilot and is labeled `nonfinal_smoke_test`.

The pilot status reports:

```text
gene result rows:                         37,962
pathway result rows:                       1,043
similarity result rows:                   21,176
mtDNA gene-test rows:                         77
MitoCarta gene-test rows:                  2,456
within-contrast significant rows:             89
global genome significant rows:               93
global mtDNA significant rows:                10
global MitoCarta significant rows:             12
global rank-pathway significant rows:           2
global ORA-pathway significant rows:            4
global similarity significant rows:             0
validation status:              validated_complete
```

Why are there 77 mtDNA rows rather than only 13? Because a **test row** is a gene in a particular method, cell type, and contrast. The same mtDNA gene can be tested repeatedly across different planned comparisons.

## 13. Current production-artifact note

As reviewed on 2026-07-16, the checked-in Phase 14 production audit says the Phase 11 production task completed as `validated_complete`. It records approximately 5.50 GiB peak RAM and 123.56 seconds runtime. The Phase 14 artifact audit also records that the five declared Phase 11 artifacts existed and passed its file, size, checksum, and validation checks at audit time.

The current workspace does **not** contain the directory:

```text
results/minerva_production/11_multiple_testing/
```

Therefore, exact production Phase 11 row counts cannot currently be reread directly from its status and family-manifest files without restoring or rerunning those outputs.

The current Phase 15 manifest shows that the missing production tables were present when Figures 05, 06, and 08 were created. It records their source paths and the checksums of the resulting PDFs. This distinction is important:

- the audit proves the Phase 11 production run had validated outputs at that time;
- the current checkout retains downstream PDFs and audit records; but
- the absent Phase 11 directory should be restored before independently rechecking or reporting exact production table rows.

## 14. How to answer common Phase 11 questions

### 14.1 "Is this mtDNA gene significant?"

Use this sequence:

1. Confirm `is_mtdna_protein_gene = TRUE`.
2. Confirm the method branch.
3. Confirm the fine cell type and contrast.
4. Read `logFC` for direction and size.
5. Read `fdr_bh_mtdna_global` for the prespecified mtDNA-wide conclusion.
6. Also read `fdr_bh_within_contrast` and `fdr_bh_global_genome_sensitivity` for context.
7. Check donor counts in the contrast manifest.
8. Check the owning Phase 07 or Phase 08 diagnostics.

### 14.2 "Is this MitoCarta gene significant?"

Use the same process, but require `is_mitocarta = TRUE` and use `fdr_bh_mitocarta_global` as the main focused family.

### 14.3 "Is this pathway significant?"

First decide which question is intended:

- use `rank_fdr_bh_global_branch` for a collective signed ranking shift; or
- use `ora_fdr_bh_global_branch` for enrichment among genes called significant.

Then check method branch, pathway membership size, tested background, contrast, donor counts, direction, and terminal status.

### 14.4 "Are the female and male patterns different?"

Use the similarity table only after checking:

- the exact `comparison_id`;
- `similarity_score`;
- `paired_tests`;
- the component counts;
- `empirical_p_value_directional`;
- within-comparison FDR; and
- `empirical_fdr_bh_global_method_branch`.

An extreme score based on only one or two paired tests is fragile and should not be presented as strong evidence merely because it equals `-1` or `+1`.

## 15. Which final figures depend on Phase 11?

Phase 15 creates ten final PDFs. Only three read Phase 11 tables directly:

| Figure | Direct Phase 11 dependency? | Phase 11 contribution |
|---|---|---|
| 01 cohort flow | No | None; cohort context. |
| 02 group coverage | No | None; power and coverage context. |
| 03 mitochondrial summary | No | None; descriptive mitochondrial fraction. |
| 04 mitochondrial-fraction effects | No | Uses a Phase 09 family correction. |
| 05 mtDNA gene effects | **Yes** | Global mtDNA FDR and combined gene branches. |
| 06 pathway effects | **Yes** | Global pathway-rank FDR. |
| 07 mitonuclear balance | No | Descriptive Phase 09 balance. |
| 08 similarity | **Yes** | Global similarity FDR. |
| 09 sensitivity | Indirectly | Phase 12 compares Phase 11 and upstream choices. |
| 10 power | No | Phase 13 simulation results. |

The remaining figures are still essential because they show cohort construction, donor coverage, descriptive biology, model estimates, robustness, and power needed to interpret the Phase 11 discoveries responsibly.

## 16. Conventions shared by the figures

### 16.1 Descriptive versus inferential

- A **descriptive** plot summarizes observed values without claiming an adjusted statistical difference.
- An **inferential** plot displays estimates or tests intended to generalize beyond the observed samples.

Figures 01, 02, 03, and 07 are descriptive. Figures 04, 05, 06, 08, and 10 are inferential or simulation-based inferential diagnostics. Figure 09 is a workflow/robustness status summary.

### 16.2 The zero line

Figures 04, 05, 06, and 08 contain a vertical dashed zero line.

- Right of zero means positive under that figure's definition.
- Left of zero means negative.
- Zero means no signed difference or neutral score under that definition.

The units differ between figures. A pathway rank difference is not a log fold change, and a similarity score is not an expression effect.

### 16.3 Colors

Red usually marks an FDR below 0.05 in Figures 04-08, but the exact family differs. Never write simply "red means significant" without naming the family.

### 16.4 Donor counts

Labels such as `n=37/45 donors` mean 37 numerator donors and 45 denominator donors. Labels such as `n=208 donors` in Figure 04 mean 208 donors in the fitted complete cell-type model, not 208 donors on each side.

## 17. Figure 01: cohort inclusion flow

[Open the production PDF](../results/minerva_production/15_figures/01_cohort_flow.pdf)

### Question

How did the study arrive at its final set of donors?

### Construction

Each blue bar is the number of donors remaining after a cumulative rule.

| Step | Rule | Donors remaining |
|---:|---|---:|
| 1 | Represented in master cell metadata | 427 |
| 2 | Retain NCI or AD | 290 |
| 3 | Exclude prespecified sex-discordant donors | 287 |
| 4 | Exclude APOE e2/e4 | 279 |
| 5 | Require APOE genotype | 277 |
| 6 | Require postmortem interval, or PMI | 276 |
| 7 | Require age at death and valid sex | 276 |

### How to read it

The bar height is the number remaining, not the number excluded. For example, Step 2 leaves 290 donors; it removes `427 - 290 = 137` donors.

### Why it matters for Phase 11

Every downstream p-value ultimately depends on this cohort definition. Exclusions change the donors available to each contrast and therefore change precision and power.

### What it does not prove

It does not prove that excluded donors are biologically identical to included donors. It also does not show how many donors are present in each fine cell type or subgroup.

## 18. Figure 02: sex-APOE-diagnosis donor coverage

[Open the production PDF](../results/minerva_production/15_figures/02_group_coverage.pdf)

### Question

How many donors are available in every fine-cell-type, diagnosis, sex, and APOE combination?

### Layout

- Rows: 54 fine cell types.
- Columns: 12 groups from `2 diagnoses x 2 sexes x 3 APOE groups`.
- Tile number: exact donor count.
- Pale blue: fewer donors.
- Dark blue: more donors.

The production plot contains `54 x 12 = 648` tiles. Tile counts range from 0 to 53. The only zero is:

```text
Fib SLC4A4 | AD | Male | e2 = 0 donors
```

### How to read it

Find one row, then compare AD and NCI tiles within the same sex and APOE group. Small numbers warn that an estimate may be unstable or a contrast may fail the minimum-donor rule.

### Why e2 often looks lighter

APOE e2 is less common than e33, so e2 groups tend to contain fewer donors. That means e2 comparisons often have less statistical power even when the biological effect is similar.

### What it is not

This is not an expression heat map. A darker tile means more donors, not more RNA or stronger disease biology. Donor counts cannot be summed across rows because the same donor can contribute multiple cell types.

## 19. Figure 03: donor-level mitochondrial RNA fraction

[Open the production PDF](../results/minerva_production/15_figures/03_mitochondrial_summary.pdf)

### Question

What fraction of donor-level RNA counts comes from the 13 mtDNA protein-coding genes in each fine cell type and diagnosis?

### Quantity

For one donor and one fine cell type:

```text
aggregate percent mitochondrial
  = 100 x summed UMI counts from 13 mtDNA genes
          -------------------------------------
                 summed counts from all genes
```

Counts are summed across that donor's nuclei before the percentage is calculated.

### Box-plot anatomy

- Middle line: median.
- Lower box edge: 25th percentile.
- Upper box edge: 75th percentile.
- Box: middle 50% of donors.
- Whiskers: values within the usual 1.5-interquartile-range rule.
- `n=` label: contributing donors.
- Outlier dots are hidden for readability, but upstream values were not deleted.

The production source contains 13,886 donor/fine-cell-type rows, 108 diagnosis/cell-type boxes, and approximately 38-142 donors per box. Observed percentages range from 0% to about 14.09%.

### How to read it

Compare AD and NCI boxes for the same fine cell type. A higher AD median is an unadjusted descriptive difference.

### What it does not prove

This plot does not adjust for age, PMI, sex, or APOE and does not show an FDR. A high mitochondrial percentage can reflect biology, stress, or technical RNA-quality effects. Figure 03 alone cannot distinguish these explanations.

## 20. Figure 04: mitochondrial-fraction model effects

[Open the production PDF](../results/minerva_production/15_figures/04_mitochondrial_fraction_effects.pdf)

### Question

After accounting for age at death and PMI, do mitochondrial RNA fractions differ across planned AD, sex, and APOE contrasts?

### Model

Phase 09 fits donor-level quasibinomial models using:

```text
mitochondrial counts versus non-mitochondrial counts
~ diagnosis-sex-APOE group + scaled age + scaled PMI
```

### Plot elements

- Point: modeled effect.
- Horizontal line: 95% confidence interval when defined.
- Dashed vertical line: zero.
- Red: `fdr_bh_mito_fraction_family < 0.05`.
- Blue: that family FDR is not below 0.05.

For a direct one-degree-of-freedom AD/NCI row, a positive log odds ratio means higher adjusted mitochondrial odds in AD. A negative value means lower adjusted odds.

### Interactions

For an interaction such as:

```text
(AD - NCI in females) - (AD - NCI in males)
```

a negative point means the AD effect is more negative, or less positive, in females. It does not simply mean females have a lower raw mitochondrial fraction.

### Global heterogeneity warning

The ten multi-df global rows do not have one signed log odds ratio. Their positive plotted value is the largest absolute heterogeneity component. Do not assign a positive biological direction to such a row.

### Production snapshot

The plot contains 386 finite effects: 376 single-df and 10 multi-df rows. Ten are red, all from `excitatory_set3`; nine are single-df and one is global heterogeneity.

### Important limitation

The `n=` label is the number of donors in the complete fitted fine-cell-type model, not the donor count on each side of that particular contrast.

## 21. Figure 05: top mtDNA gene effects

[Open the production PDF](../results/minerva_production/15_figures/05_mtdna_gene_effects.pdf)

### Question

Which tests involving the 13 mtDNA protein-coding genes rank most strongly after the Phase 11 mtDNA correction?

### Phase 11 dependency

The source is intended to be:

```text
results/minerva_production/11_multiple_testing/gene_multiple_testing.tsv.gz
```

### Selection

Phase 15:

1. keeps mtDNA rows;
2. requires finite log fold change and resolved donor counts;
3. sorts by global mtDNA FDR;
4. breaks ties by absolute log2 fold change; and
5. plots only the first 40 rows.

Absence from the PDF does not mean a gene was untested or unimportant.

### Labels

Each row contains:

```text
method | fine cell type | gene | contrast | n=numerator/denominator donors
```

### X-axis

The x-axis is log2 fold change.

- `+1` means approximately a two-fold increase.
- `-1` means approximately a two-fold decrease.
- `+0.5` means approximately `2^0.5 = 1.41` times expression.

For direct AD/NCI contrasts, positive means higher in AD and negative means lower in AD.

### Colors

- Red: the plotted FDR is below 0.05.
- Blue: it is not below 0.05.

For an mtDNA row, the preferred plotted value is `fdr_bh_mtdna_global`; the code falls back to within-contrast FDR only if the global value is unavailable.

The current production top 40 are red. The displayed rows include multiple mtDNA genes in oligodendrocytes and excitatory-neuron cell types, with both pseudobulk and MAST represented in the combined source.

### What not to conclude

- The top 40 are not 40 independent genes; the same gene can appear in multiple cell types and contrasts.
- Red does not establish causality.
- Pseudobulk and MAST effect values are not replicate measurements from the same model.
- The PDF has no confidence intervals, so consult the source and upstream diagnostics.

## 22. Figure 06: MitoCarta pathway effects

[Open the production PDF](../results/minerva_production/15_figures/06_pathway_effects.pdf)

### Question

Which mitochondrial pathways show the strongest collective shift in gene-level differential-expression ranks?

### Phase 11 dependency

The source is intended to be:

```text
results/minerva_production/11_multiple_testing/pathway_multiple_testing.tsv.gz
```

### How the pathway score is built

Phase 09 assigns each tested gene a signed ranking statistic. For each pathway it compares genes inside the pathway with tested genes outside it.

The plotted effect is:

```text
rank_mean_difference
  = mean signed rank of pathway genes
    - mean signed rank of complement genes
```

### X-axis

- Positive: pathway genes tend toward more positive AD-related evidence than the complement.
- Negative: pathway genes tend toward more negative evidence.
- Zero: no mean ranking difference.

This value is not a fold change or an RNA amount.

### Selection and colors

Phase 15 keeps eligible, finite rows with donor counts, sorts by Phase 11 global pathway-rank FDR and absolute effect, and plots the first 35.

- Red: `rank_fdr_bh_global_branch < 0.05`.
- Green: it is not below 0.05.

The current production top 35 are red. Both pseudobulk and MAST rows appear, and OXPHOS-related pathways dominate the displayed set.

### What not to conclude

- A positive pathway result does not mean every member gene increased.
- It does not directly measure ATP production.
- The pseudobulk and MAST rank statistics use different scales.
- This PDF shows the rank-test effect, not the ORA odds ratio.

## 23. Figure 07: donor-level mitonuclear balance

[Open the production PDF](../results/minerva_production/15_figures/07_mitonuclear_balance.pdf)

### Question

How does RNA from mtDNA-encoded OXPHOS genes compare with RNA from nuclear-encoded OXPHOS genes?

### Formula

For one eligible donor and fine cell type:

```text
mt average = mtDNA OXPHOS UMI / measured mtDNA OXPHOS genes

nuclear average = nuclear OXPHOS UMI / measured nuclear OXPHOS genes

balance = log2((mt average + 0.5) / (nuclear average + 0.5))
```

The 0.5 values prevent division by zero and stabilize very small counts.

### Y-axis interpretation

- `0`: equal adjusted UMI per measured gene.
- `+1`: mtDNA average is approximately twice the nuclear average.
- `-1`: mtDNA average is approximately half the nuclear average.
- `+6`: approximate ratio of `2^6 = 64` on this RNA-count scale.

### Production snapshot

The input contains 8,269 primary-eligible donor/fine-cell-type rows, 106 represented diagnosis/cell-type boxes, and values from about 0.294 to 8.876. Some boxes contain very few donors; one displayed example has `n=1`.

### What it does not prove

This is descriptive RNA balance. It does not directly measure protein abundance, respiratory-chain assembly, oxygen use, ATP production, or mitochondrial health. A one-donor box is one observation, not a stable population distribution.

## 24. Figure 08: Zhang-Yu similarity

[Open the production PDF](../results/minerva_production/15_figures/08_similarity.pdf)

### Question

Are the directions of significant AD-related changes similar or different between two sex or APOE settings?

### Phase 11 dependency

The source is intended to be:

```text
results/minerva_production/11_multiple_testing/similarity_multiple_testing.tsv.gz
```

Phase 10 computes scores and empirical p-values. Phase 11 adds the global similarity FDR used for plot coloring and ordering.

### Ternary states

Each eligible gene/stratum DE result becomes:

```text
+1 = significantly increased in AD
 0 = not called significantly changed
-1 = significantly decreased in AD
```

### Score contributions

- Same nonzero direction: `+1`.
- Significant on one side and unchanged on the other: `-0.5`.
- Opposite significant directions: `-1`.
- Both unchanged: `0`.

The average contribution gives a score from `-1` to `+1`.

- `+1`: complete directional agreement among contributing pairs.
- `-1`: complete directional opposition.
- `0`: neutral overall, either from unchanged pairs or cancellation.

### Labels and sample sizes

`paired tests=6` means six matched cell-type/stratum state pairs. It does not mean six donors. The title's `5-53 donors per side` is the range across eligible source contrasts, not a row-specific sample size.

### Colors

- Red: `empirical_fdr_bh_global_method_branch < 0.05`.
- Purple: global similarity FDR is not below 0.05.

### Production snapshot

Phase 15 first restricts to finite MitoCarta rows, sorts by global FDR and absolute score, and displays 35. In the current production PDF:

- all 35 are purple;
- the visible selected rows are from MAST;
- most compare female with male within e2;
- one displayed row compares within e33; and
- paired-test counts range from 1 to 10.

Several scores are exactly `-1` or `+1` because extreme averages are easy to obtain from one or two pairs. Their global FDRs do not support treating these extreme-looking points as globally significant.

## 25. Figure 09: sensitivity and robustness completion

[Open the production PDF](../results/minerva_production/15_figures/09_sensitivity.pdf)

### Question

Which planned robustness analyses completed, which were blocked by missing inputs, and how many output rows did they produce?

### Bar meaning

The bar height is the number of result rows. It is not an effect size, success percentage, donor count, or count of significant discoveries.

### Colors

- Green: `validated_complete`.
- Orange: `not_estimable`.
- Purple: `blocked_missing_input`.
- Red: `failed`.

### Production snapshot

| Sensitivity branch | Status | Result rows | Repetitions |
|---|---|---:|---:|
| `pseudobulk_vs_mast` | validated complete | 695,393 | 0 |
| `global_vs_within_contrast_fdr` | validated complete | 1,082,689 | 0 |
| `flagged_nuclei_exclusion` | validated complete | 373 | 0 |
| `nuclei_minimum_50` | validated complete | 229 | 0 |
| `alternative_age_pmi_encoding` | validated complete | 386 | 0 |
| `leave_one_donor_out` | validated complete | 386 | 43 |
| `donor_bootstrap` | validated complete | 386 | 1,000 |
| `validated_batch_covariate` | blocked missing input | 0 | 0 |
| `normalization_sctransform` | blocked missing input | 0 | 0 |
| `per_object_vs_results_only_harmonization` | blocked missing input | 0 | 0 |
| `alternative_external_mitochondrial_sets` | blocked missing input | 0 | 0 |

The first two bars are so large that completed branches with hundreds of rows look almost flat. Read the printed values rather than only comparing bar heights.

A blocked analysis is not a negative biological finding. It means the required alternative input was unavailable.

## 26. Figure 10: power by simulated effect

[Open the production PDF](../results/minerva_production/15_figures/10_power.pdf)

### Question

If an artificial AD effect of a known size is planted into simulated data, how often do two analysis approaches detect it?

### Panels

| Panel | Fine cell type | Gene | AD/NCI donors |
|---:|---|---|---:|
| 1 | Inh L5-6 SST TH | MT-ND6 | 5/8 |
| 2 | Inh L5-6 SST TH | MT-CO3 | 5/8 |
| 3 | Oli | MT-ND6 | 7/6 |
| 4 | Oli | MT-CO2 | 7/6 |
| 5 | Oli | MT-ND6 | 37/45 |
| 6 | Oli | MT-CO2 | 37/45 |

### Axes and lines

- X-axis: true simulated log2 AD effect.
- Y-axis at effect zero: false-positive rate.
- Y-axis at nonzero effect: power.
- Dashed horizontal line: target power of 0.80.
- Blue: donor-level pseudobulk edgeR with known dispersion.
- Red: simplified paper-like hurdle benchmark.

The production simulation uses:

```text
6 scenarios x 2 methods x 6 effect sizes x 100 repetitions
= 7,200 simulated fits
```

### Power versus false positives

High power is useful only if false positives are controlled when the true effect is zero. The zero-effect rates are:

| Scenario | Pseudobulk edgeR | Paper-like hurdle |
|---:|---:|---:|
| 1 | 0.01 | 0.06 |
| 2 | 0.06 | 0.46 |
| 3 | 0.03 | 0.61 |
| 4 | 0.03 | 0.83 |
| 5 | 0.00 | 0.50 |
| 6 | 0.03 | 0.76 |

Except for Scenario 1, the red benchmark has severely inflated false-positive rates. Its high apparent detection rate cannot be interpreted as trustworthy superior power. A method that declares many null simulations positive will also appear to detect many planted effects.

### Donor-number lesson

The 37/45-donor pseudobulk scenarios reach the 0.80 target at smaller effects than several 5/8- or 7/6-donor scenarios. This is why Figure 02's uneven donor coverage and the Phase 11 unequal-power warning are so important.

### Simulation limitation

Each point uses 100 repetitions, so it has Monte Carlo uncertainty. These six scenarios illustrate selected genes and donor layouts; they do not guarantee identical power for every gene and cell type.

## 27. A responsible interpretation checklist

Before describing a Phase 11 or figure result, ask:

1. Is this pilot or production?
2. Is the result descriptive or inferential?
3. Which method branch produced it?
4. Which fine cell type and contrast does it represent?
5. Is it a direct AD/NCI effect or an interaction?
6. What is the effect's unit and direction?
7. Which exact FDR family is being used?
8. How many tests were in that family?
9. How many donors are on each side?
10. Is the cell type rare or the group unbalanced?
11. Do pseudobulk and MAST agree in direction?
12. Did relevant sensitivity analyses support the conclusion?
13. Is a nonsignificant result being incorrectly described as proof of no effect?
14. Is an association being incorrectly described as a causal mechanism?

## 28. Running Phase 11

### Local pilot

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase multiple_testing
```

The pilot output is labeled `nonfinal_smoke_test` and should be used to validate code flow, not to report final biology.

### Production

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase multiple_testing
```

Production should be run only after every intended Phase 07-10 upstream result and status artifact is present and validated. If an upstream accepted result changes, Phase 11 must be rerun so its global families contain exactly the final accepted inputs.

## 29. Final takeaway

The project is mitochondria-focused, but it uses genome-wide differential expression to preserve context and avoid an overly narrow first pass. Phase 11 then turns a very large collection of p-values into interpretable, prespecified decision families.

The most relevant Phase 11 questions for this project are:

- Do any of the 13 mtDNA genes survive correction across all mtDNA tests?
- Do MitoCarta genes survive the broader mitochondrial correction?
- Do MitoCarta pathways show coordinated rank shifts or enrichment?
- Are AD-related mitochondrial patterns similar or divergent across sex and APOE settings?
- Are conclusions stable across pseudobulk, MAST, sensitivity, and power analyses?

The FDR threshold is only one part of the answer. Effect size, direction, donor coverage, method calibration, pathway meaning, and robustness must be interpreted together.
