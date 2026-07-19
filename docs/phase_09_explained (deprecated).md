# Phase 09 Explained: Mitochondrial Read Fraction, Pathways, and Mitonuclear Balance

## 1. Phase 09 in one sentence

Phase 09 stops looking at genes only one at a time and asks three broader questions:

1. **Mitochondrial read fraction:** What fraction of a donor's RNA counts comes from the 13 protein-coding genes in mitochondrial DNA, and does that fraction differ between AD and NCI or across sex–APOE groups?
2. **Mitochondrial pathways:** Do groups of mitochondrial genes tend to move together, even if individual genes are not significant by themselves?
3. **Mitonuclear balance:** Within each donor and fine cell type, how much expression comes from mtDNA-encoded oxidative-phosphorylation genes compared with nuclear-DNA-encoded oxidative-phosphorylation genes?

Phase 09 has two ordered pipeline operations:

1. **Phase 09.1 — `mito_fraction`:** fit donor-level models of mitochondrial read fraction.
2. **Phase 09.2 — `pathways`:** analyze frozen MitoCarta pathways in both the Phase 07 pseudobulk and Phase 08 MAST branches, and calculate donor-level mitonuclear summaries.

The owning scripts are:

```text
scripts/09_run_mito_fraction_models.R
scripts/09_run_mito_pathways.R
```

## 2. A high-school-level biology introduction

### 2.1 What mitochondria do

Mitochondria are structures inside cells that help convert energy from food into ATP, a molecule cells use as an energy currency. The energy-producing machinery is called **oxidative phosphorylation**, usually shortened to **OXPHOS**. OXPHOS includes five major protein machines called complexes I through V.

### 2.2 Mitochondria use two genomes

Most human genes are stored in the cell nucleus. Mitochondria also contain a small genome called mitochondrial DNA, or **mtDNA**.

The mitochondrial genome encodes only 13 OXPHOS proteins used here:

```text
MT-ND1, MT-ND2, MT-CO1, MT-CO2, MT-ATP8, MT-ATP6, MT-CO3,
MT-ND3, MT-ND4L, MT-ND4, MT-ND5, MT-ND6, MT-CYB
```

Most other mitochondrial proteins are encoded by nuclear DNA, produced outside the mitochondrion, and imported into it. Healthy energy production therefore requires coordination between the mitochondrial and nuclear genomes. This coordination motivates the mitonuclear-balance calculation.

### 2.3 What an RNA count means

Single-nucleus RNA sequencing counts short molecular tags called UMIs. A larger UMI count for a gene usually means that more RNA from that gene was captured. It is not a direct measurement of protein amount or mitochondrial activity.

For one donor–fine-cell-type pseudobulk sample:

```text
total_umi_count = counts from all measured genes
total_mt_count  = counts from the 13 mtDNA protein-coding genes
```

The mitochondrial read fraction is approximately:

```text
total_mt_count / total_umi_count
```

### 2.4 Why mitochondrial read fraction must be interpreted carefully

A higher mitochondrial read fraction can have several explanations:

- genuine mitochondrial biology;
- more mitochondrial transcripts;
- fewer nuclear transcripts;
- cell stress;
- RNA degradation;
- tissue-handling differences; or
- sequencing/capture effects.

Therefore, a difference in mitochondrial read fraction does **not** automatically prove that mitochondria are healthier, more numerous, or more active. It is a useful signal that must be interpreted alongside gene, pathway, QC, and donor-level results.

## 3. Essential statistical vocabulary

### Pseudobulk sample

Counts from all eligible nuclei belonging to one donor and one high-resolution cell type are added together. This donor–cell-type aggregate is one pseudobulk sample.

### Contrast

A contrast is a planned comparison. Examples include:

```text
AD versus NCI among Female e33 donors
AD effect in Female e33 minus AD effect in Male e33
```

Phase 09 reuses the frozen Phase 07 contrast manifest rather than inventing new comparisons.

### Covariate

A covariate is an additional measured variable that may influence the outcome even though it is not the main comparison of interest. In Phase 09.1:

- the **outcome** is the donor-level mitochondrial read fraction;
- the **main comparison** is a planned diagnosis × sex × APOE contrast; and
- the **covariates** are age at death and postmortem interval (PMI).

#### Why age at death is included

Age can be associated with mitochondrial biology and RNA measurements. Suppose, for example, that the AD donors in one comparison are older on average than the NCI donors. If older donors also tend to have a different mitochondrial read fraction, a simple unadjusted AD-minus-NCI comparison would mix together two possible influences:

```text
observed difference
    = possible diagnosis-associated difference
    + possible age-associated difference
    + other variation
```

The model includes age so that the AD-versus-NCI effect is estimated while comparing donors at the same modeled age. This is often described as **holding age constant**. It is a mathematical model comparison; the script does not change anyone's recorded age or physically pair every AD donor with an NCI donor.

#### What PMI means and why it is included

PMI means **postmortem interval**: the time between a person's death and tissue preservation or collection. During a longer interval, RNA can degrade and cells can undergo postmortem changes. These effects may alter measured RNA counts or the proportion assigned to mitochondrial genes.

If PMI differs systematically between AD and NCI donors, an unadjusted comparison might partly reflect tissue-handling time rather than diagnosis. Including PMI allows the model to estimate the planned group contrast while holding the modeled PMI value constant.

#### What “adjusting for” a covariate means

Conceptually, the Phase 09.1 model separates three components:

```text
modeled mitochondrial-fraction log odds
    = diagnosis–sex–APOE group component
    + age component
    + PMI component
```

The contrast is then calculated from the group components after the age and PMI components have been included. The original UMI counts are not edited or “corrected” in the output file; adjustment occurs when the regression coefficients and their uncertainty are estimated.

#### Why the variables are scaled

The model uses `age_death_scaled` and `pmi_scaled`. Scaling is approximately:

```text
scaled value = (original value - analytic-cohort mean) / analytic-cohort standard deviation
```

Therefore:

- `0` is approximately the analytic-cohort average;
- `+1` is one standard deviation above the average; and
- `-1` is one standard deviation below the average.

Scaling puts age and PMI on comparable numerical scales and can make model fitting more stable. It does not discard information, make the donors the same age, or change the scientific contrast.

#### What covariate adjustment cannot guarantee

Adjustment reduces confounding by the measured age and PMI variables under the model assumptions, but it does not prove causation. It cannot automatically correct for:

- an unmeasured variable that differs between groups;
- inaccurate age or PMI values;
- a strongly nonlinear relationship when the model includes only a linear term;
- very little age or PMI overlap between comparison groups; or
- too few donors to distinguish group and covariate effects.

For this reason, the output records the covariates, design rank, residual degrees of freedom, convergence, and dispersion. These diagnostics must be checked before interpreting an adjusted contrast.

### p-value

A p-value measures how surprising the observed result would be if the tested null hypothesis were true. A small p-value is evidence against the null hypothesis, but it is not the probability that the scientific conclusion is true.

### FDR

Testing many hypotheses increases the chance of false positives. Benjamini–Hochberg false-discovery-rate correction, or BH FDR, adjusts p-values within a declared family of tests.

### Pathway

A pathway is a predefined group of genes that participate in a shared biological job, such as OXPHOS, mitochondrial translation, or complex I assembly.

## 4. Phase 09 data flow

```text
Phase 03 frozen MitoCarta pathways
                |
                +---------------------------------------------+
                                                              |
Phase 07 pseudobulk counts and samples                        |
                |                                             |
                +--> Phase 09.1 mtDNA-read-fraction models    |
                |                                             |
                +--> donor-level mitonuclear summaries <------+
                                                              |
Phase 07 edgeR gene results ----------------------------------+
                                                              |
Phase 08 MAST gene results -----------------------------------+
                |                                             |
                +--> Phase 09.2 pathway tests in two branches-+
```

All Phase 09 files for one execution stage are written under:

```text
results/<execution_stage>/09_downstream/
```

For production, this is:

```text
results/minerva_production/09_downstream/
```

Each broad-cell-type RDS is processed separately. File prefixes use the lower-case stable `rds_id`, such as `vasculature`, `astrocytes`, or `immune`.

## 5. Inputs and prerequisites

| Input | Why Phase 09 needs it |
|---|---|
| Phase 07 pseudobulk count bundle | Supplies donor-level raw counts and sample metadata. |
| Phase 07 pseudobulk sample table | Supplies donor, fine-cell-type, diagnosis, sex, APOE, age, PMI, nucleus count, total UMI count, and mtDNA count. |
| Phase 07 frozen contrast manifest | Supplies the 14 planned contrasts per fine cell type and their eligibility. |
| Phase 07 edgeR DE results | Supplies gene rankings and pseudobulk significance calls for pathway analysis. |
| Phase 08 MAST results | Supplies an independent cell-level gene ranking and paper-style DEG calls for pathway analysis. |
| Phase 03 `mitocarta_pathways.tsv` | Supplies frozen Human MitoCarta3.0 pathway definitions. |
| Phase 03 tested gene universe | Supplies audited gene-universe provenance. The actual pathway background is recalculated from genes present in each DE branch and contrast. |
| Human MitoCarta3.0 source workbook | Supplies the authoritative pathway source; its configured SHA-256 checksum must match. |
| Phase 04 donor-cell-type QC artifact | Supplies validated upstream QC provenance for the fraction task. |

Required upstream status files must be `validated_complete`. Phase 09 refuses to continue with unsupported schemas, missing pathways, changed MitoCarta checksums, invalid count pairs, or invalid upstream statuses.

# Part I: Phase 09.1 Mitochondrial Read-Fraction Models

## 6. Scientific question for Phase 09.1

For each high-resolution cell type, Phase 09.1 asks:

> After accounting for donor age and PMI, does the fraction of RNA counts coming from the 13 mtDNA protein-coding genes differ for a planned AD/sex/APOE contrast?

This is not a gene-by-gene analysis. It treats all 13 mtDNA counts as one combined numerator.

## 7. Statistical unit and eligibility

The independent statistical observation is one primary-eligible donor–fine-cell-type pseudobulk sample.

Only samples satisfying:

```text
primary_eligible = TRUE
nuclei >= 20
```

enter the model. A donor has at most one pseudobulk sample within a fine cell type.

Phase 09.1 applies the same contrast eligibility frozen in Phase 07.2. Every group required by a contrast must have at least five primary-eligible donors.

For every fine cell type, the manifest can contain up to 14 planned contrasts:

```text
6 direct AD-versus-NCI contrasts
3 sex interactions
4 APOE interactions
1 global heterogeneity test
```

Ineligible contrasts remain in the contrast-status output but do not produce model-result rows.

## 8. What Phase 09.1 models

For each donor-level pseudobulk sample, the response has two counts:

```text
mitochondrial     = total_mt_count
non-mitochondrial = total_umi_count - total_mt_count
```

The model is a **quasibinomial logistic regression**.

### 8.1 Why use two counts instead of only a percentage?

Suppose two donors both have a 2% mitochondrial fraction:

- Donor A: 2 mitochondrial counts out of 100 total counts.
- Donor B: 2,000 mitochondrial counts out of 100,000 total counts.

The percentage is the same, but Donor B's fraction is measured with much more count information. Supplying the numerator and denominator allows the model to use that information.

### 8.2 Why “quasi” binomial?

A simple binomial model assumes a specific amount of variation. Biological donors commonly vary more than that assumption allows. The quasibinomial model estimates an extra dispersion factor so uncertainty can reflect this additional variability.

### 8.3 Model design

For one fine cell type, the implemented design is equivalent to:

```r
~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled
```

It estimates a separate baseline for every observed diagnosis × sex × APOE group and adjusts for:

- scaled age at death; and
- scaled PMI.

In simplified mathematical form:

```text
log odds of mitochondrial read fraction
    = group coefficient
    + age coefficient × scaled age
    + PMI coefficient × scaled PMI
```

For a direct AD-versus-NCI contrast, the tested effect is the difference between the relevant AD and NCI group coefficients. Because both groups share the fitted age and PMI terms, that difference represents the model's AD-versus-NCI comparison at the same modeled age and PMI.

The total UMI count is already supplied as the denominator of the two-count response, so Phase 09.1 does not add `total_umi_count` as a separate linear covariate. This differs from the nucleus-level Phase 08 MAST model, which includes per-nucleus `nCount_RNA` as a latent variable.

The model must be full rank. In simple language, the available donors must contain enough independent information to estimate all requested coefficients.

## 9. Phase 09.1 effects and tests

### 9.1 Single-degree-of-freedom contrasts

Direct AD-versus-NCI, sex-interaction, and APOE-interaction contrasts produce a **log odds ratio**.

The mitochondrial odds for a fraction `p` are:

```text
odds = p / (1 - p)
```

The output contains:

```text
effect_size = log odds ratio
odds_ratio  = exp(effect_size)
```

For a direct AD-versus-NCI contrast:

- `odds_ratio > 1`: the adjusted mtDNA-read odds are higher in AD;
- `odds_ratio < 1`: the adjusted mtDNA-read odds are lower in AD; and
- `odds_ratio = 1`: no estimated difference.

An odds ratio of 1.5 does not mean “50 percentage points higher.” It means the odds are multiplied by 1.5. When the underlying fraction is small, odds and fraction changes can still be modest.

For an interaction, the sign applies to a difference of effects. For example:

```text
(AD - NCI in Female e33) - (AD - NCI in Male e33)
```

A negative interaction means the AD effect is more negative, or less positive, in females than in males. It does not simply mean females have a lower mitochondrial fraction.

### 9.2 Global heterogeneity contrast

The global test jointly asks whether the six sex–APOE-specific AD effects are all equal. It is a multi-degree-of-freedom F test.

Because there is no single signed difference:

- `effect_type` is `maximum_absolute_log_odds_heterogeneity`;
- `effect_size` is the largest absolute component difference;
- `odds_ratio`, standard error, and confidence limits are `NA`; and
- direction must be studied using the single-degree-of-freedom contrasts.

### 9.3 Multiple testing

After all eligible fraction contrasts for one RDS are tested, Phase 09.1 applies BH correction across all of those result rows. The result is stored in:

```text
fdr_bh_mito_fraction_family
```

This is an RDS-level Phase 09.1 family. Phase 11 later applies and audits broader study-level multiple-testing families.

## 10. Phase 09.1 output files

Each RDS produces six uncompressed tab-separated text files. A TSV file has:

- one header row containing column names;
- one record per subsequent line;
- tab characters separating fields; and
- the literal text `NA` for unavailable values.

### 10.1 `<rds_id>.mito_fraction_models.tsv`

This is the main Phase 09.1 scientific result.

One row represents:

```text
one high-resolution cell type × one eligible planned contrast
```

It is not one gene and not one donor. Because the outcome is the combined mtDNA fraction, one eligible contrast produces one row.

| Column | Meaning |
|---|---|
| `schema_version` | Result schema, currently `mito_fraction_results_v1`. |
| `rds_id` | Stable broad-cell-type RDS identifier. |
| `source_rds` | Source Seurat RDS path. |
| `cell_type_high_resolution` | Fine cell type modeled. |
| `manifest_row` | Matching row in the frozen Phase 07 contrast manifest. |
| `contrast_id` | Globally unique contrast identifier. |
| `contrast_family` | Direct AD/NCI, sex interaction, APOE interaction, or global heterogeneity. |
| `contrast_name` | Human-readable contrast name. |
| `contrast_kind` | `single_df` or `multi_df`. |
| `model_method` | `donor_level_quasibinomial_logit`. |
| `numerator_field` | Count used as the mitochondrial numerator: `total_mt_count`. |
| `denominator_field` | Total-count field: `total_umi_count`. |
| `effect_type` | `log_odds_ratio` or the maximum-absolute heterogeneity type. |
| `effect_size` | Log odds ratio for single-df tests; maximum absolute component for the global test. |
| `odds_ratio` | `exp(effect_size)` for single-df tests; `NA` for the omnibus test. |
| `standard_error` | Standard error of a single-df log odds ratio. |
| `ci95_low` | Lower 95% confidence limit on the log-odds scale. |
| `ci95_high` | Upper 95% confidence limit on the log-odds scale. |
| `statistic` | t statistic for single-df tests or F statistic for the omnibus test. |
| `statistic_type` | `t` or `F`. |
| `numerator_df` | Numerator degrees of freedom: 1 for single-df tests or the omnibus rank. |
| `denominator_df` | Model residual degrees of freedom. |
| `p_value` | Raw contrast p-value. |
| `fdr_bh_mito_fraction_family` | BH FDR across completed fraction tests in this RDS. |
| `required_group_mt_counts` | Semicolon-separated mtDNA count totals for every group required by the contrast. |
| `required_group_total_counts` | Semicolon-separated total UMI counts for every required group. |
| `positive_groups_mt_counts` | mtDNA counts from groups with positive contrast coefficients. |
| `positive_groups_total_counts` | Total UMI counts from positive-coefficient groups. |
| `negative_groups_mt_counts` | mtDNA counts from groups with negative contrast coefficients. |
| `negative_groups_total_counts` | Total UMI counts from negative-coefficient groups. |
| `model_donors` | All primary-eligible donors in the fine-cell-type model, not only the two groups of a direct contrast. |
| `model_nuclei` | Total nuclei underlying all samples in the fitted fine-cell-type model. |
| `dispersion` | Estimated quasibinomial overdispersion. |
| `covariates` | Model adjustment fields, currently `age_death_scaled;pmi_scaled`. |

For a multi-df global contrast, the positive/negative-group summaries are not a simple two-sided comparison. Use `required_group_*`, the F statistic, and the component contrasts rather than treating those fields as a numerator and denominator.

### 10.2 `<rds_id>.mito_fraction_diagnostics.tsv`

One row represents one high-resolution-cell-type model.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_fraction_diagnostics_v1`. |
| `rds_id` | Broad RDS identifier. |
| `cell_type_high_resolution` | Fine cell type. |
| `donors` | Donor-level samples in the fitted model. |
| `groups` | Observed diagnosis × sex × APOE group levels. |
| `design_columns` | Semicolon-separated model coefficients. |
| `design_rank` | Independent information rank of the design. |
| `residual_df` | Residual degrees of freedom. |
| `dispersion` | Estimated extra-binomial variation. |
| `converged` | Whether model fitting reached a stable numerical solution. |
| `model_status` | `fitted`, `not_fit_no_eligible_contrasts`, `failed`, or `failed_not_converged`. |
| `message` | Explanation of a skipped or failed model. |

For `not_fit_no_eligible_contrasts`, the diagnostic uses zero placeholders because no model was attempted; that does not mean the source RDS contained zero donors.

### 10.3 `<rds_id>.mito_fraction_contrast_status.tsv`

One row represents every planned Phase 07 manifest contrast belonging to the RDS, including ineligible contrasts.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_fraction_contrast_status_v1`. |
| `rds_id` | RDS identifier. |
| `manifest_row` | Frozen manifest row. |
| `contrast_id` | Unique contrast ID. |
| `cell_type_high_resolution` | Fine cell type. |
| `contrast_family` | Contrast family. |
| `contrast_name` | Contrast name. |
| `eligibility_status` | Eligibility inherited from Phase 07.2. |
| `terminal_status` | `validated_complete`, `ineligible`, or `failed`. |
| `message` | Ineligibility reason or failure message. |

This file explains why a planned contrast does or does not appear in the main model table.

### 10.4 `<rds_id>.mito_fraction_checks.tsv`

Each row is one automated validation check with columns:

```text
schema_version, rds_id, check, passed, observed, expected
```

The nine checks require:

1. exactly one terminal status per manifest row;
2. every eligible contrast completed;
3. every ineligible contrast was explicit;
4. unique result contrast IDs;
5. mitochondrial counts never exceed total counts;
6. p-values are finite and between 0 and 1;
7. FDR values are finite and between 0 and 1;
8. all fitted models use donor-level samples; and
9. execution stage is recorded.

### 10.5 `<rds_id>.mito_fraction_artifacts.tsv`

Each row inventories one of the four primary artifacts: models, diagnostics, contrast status, or checks.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_fraction_artifacts_v1`. |
| `rds_id` | Owning RDS. |
| `artifact` | Artifact filename. |
| `path` | Project-relative path. |
| `bytes` | File size. |
| `sha256` | SHA-256 checksum. |
| `records` | Number of rows in the artifact. |
| `validation_status` | Shared validation state. |

### 10.6 `<rds_id>.mito_fraction_status.tsv`

This one-row file summarizes the entire RDS-level fraction task.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_fraction_status_v1`. |
| `execution_stage` | `local_pilot` or `minerva_production`. |
| `execution_phase` | Numeric execution scope: 1 for local pilot or 2 for production; not scientific Phase 09. |
| `backend` | Execution backend. |
| `run_id` | Controller run identifier. |
| `stable_task_id` | Normally `mito_fraction:<rds_id>`. |
| `source_rds` | Source RDS path. |
| `scientific_script` | Owning script path. |
| `scientific_code_bundle_sha256` | Scientific script checksum. |
| `scientific_config_sha256` | Analysis-configuration checksum. |
| `rds_manifest_sha256` | RDS-manifest checksum. |
| `donor_celltype_qc_sha256` | Upstream donor-cell-type QC checksum. |
| `pseudobulk_bundle_sha256` | Phase 07 count-bundle checksum. |
| `pseudobulk_samples_sha256` | Phase 07 sample-table checksum. |
| `contrast_manifest_sha256` | Frozen contrast-manifest checksum. |
| `model_method` | Donor-level quasibinomial logit. |
| `manifest_rows` | Planned contrast rows for the RDS. |
| `eligible_contrasts` | Contrasts meeting donor requirements. |
| `completed_contrasts` | Eligible contrasts completed successfully. |
| `ineligible_contrasts` | Explicitly ineligible contrasts. |
| `failed_contrasts` | Eligible contrasts that failed. |
| `significant_fdr_005` | Fraction-result rows with Phase 09.1 FDR below 0.05. |
| `peak_ram_gib` | Peak memory use. |
| `elapsed_seconds` | Runtime. |
| `validation_status` | Expected final value: `validated_complete`. |
| `failed_checks` | Failed check names, blank on success. |
| `git_revision` | Git commit used. |
| `timestamp_utc` | Completion time in UTC. |

# Part II: Phase 09.2 Mitochondrial Pathway Analysis

## 11. Why analyze pathways?

Imagine a pathway as a sports team. One player having a slightly unusual game may not be convincing. If most players on the team shift in the same direction, the team-level pattern can be convincing even when no single player is extreme.

Likewise, a biological pathway can show a coordinated shift even if individual genes have moderate p-values. Phase 09.2 asks whether genes in a frozen MitoCarta pathway tend to rank differently from other tested genes.

## 12. Two separate method branches

Phase 09.2 repeats pathway analysis using two gene-level sources:

1. `pseudobulk`: primary donor-aware Phase 07 edgeR results.
2. `mast`: secondary nucleus-level Phase 08 MAST results.

The branches are not pooled. One pathway can therefore have separate pseudobulk and MAST rows for the same direct contrast.

### 12.1 Pseudobulk ranking score

For each edgeR gene row:

```text
signed_statistic = sign(logFC) × sqrt(max(F, 0))
ranking_method   = signed_sqrt_edgeR_QLF
```

A large positive score means strong evidence in the positive contrast direction. A large negative score means strong evidence in the negative direction.

The pseudobulk significant-gene flag is:

```text
fdr_bh_within_contrast < 0.05
```

### 12.2 MAST ranking score

For each MAST gene row, the two-sided p-value is converted to the size of a normal-distribution score and the logFC sign is attached:

```text
signed_statistic = sign(logFC) × qnorm(p_value / 2, lower.tail = FALSE)
ranking_method   = signed_MAST_normal_score
```

The MAST significant-gene flag is the Phase 08 `paper_deg` value, which requires within-contrast FDR, effect size, and detection criteria.

### 12.3 Which contrasts enter pathway analysis?

The pseudobulk branch can include eligible direct, sex-interaction, and APOE-interaction contrasts because they have a signed logFC. The multi-df global heterogeneity result has no single signed logFC, so it cannot form a signed gene ranking and is removed from this pathway analysis.

The MAST branch includes only the eligible six paper-matched direct AD-versus-NCI contrasts because Phase 08 does not fit interaction or omnibus models.

Only finite scores and nonblank, unique gene names enter a branch–contrast ranking.

## 13. Frozen MitoCarta pathway definitions

Phase 09.2 reads:

```text
results/<execution_stage>/03_annotations/mitocarta_pathways.tsv
```

The definitions originated from the `C MitoPathways` sheet of Human MitoCarta3.0. The source workbook's SHA-256 must match the value frozen in the analysis configuration.

In the validated pilot annotation:

- 154 source rows were present;
- 5 blank/incomplete pathway rows were explicitly excluded; and
- 149 named pathway definitions were tested.

Blank rows are not silently treated as pathways.

## 14. The gene background and pathway eligibility

For one method branch and one contrast, the **background** is every unique gene with a finite signed score in that branch–contrast result.

This is important. The background is not every human gene and not every MitoCarta gene. It is the set of genes that could actually have appeared in that particular analysis.

For each frozen pathway:

```text
members    = pathway genes found in the background
nonmembers = background genes not in the pathway
```

A pathway test is eligible only when:

```text
at least 5 tested pathway genes
and at least 5 tested non-pathway genes
```

An ineligible pathway still receives a result row with:

```text
terminal_status = ineligible
message = fewer_than_5_tested_genes_in_pathway_or_complement
```

This preserves the complete planned pathway inventory.

## 15. Two pathway tests per eligible row

### 15.1 Ranked-distribution test

Phase 09.2 compares the signed scores of pathway members with the signed scores of all background nonmembers using a Wilcoxon rank-sum test.

It records:

```text
rank_mean_pathway
rank_mean_complement
rank_mean_difference
```

The direction is:

- positive difference: `up_in_AD_or_positive_effect`;
- negative difference: `down_in_AD_or_negative_effect`; or
- zero difference: `no_direction`.

For a direct AD-versus-NCI contrast, positive means the pathway tends upward in AD and negative means it tends downward in AD. For an interaction, “positive” and “negative” refer to the encoded interaction direction, not simply AD up or down.

The p-value comes from the rank-sum comparison, not from a test of the arithmetic means themselves.

### 15.2 Over-representation analysis

Over-representation analysis, or ORA, asks:

> Does this pathway contain more significant genes than expected from its size and the number of significant genes in the tested background?

It uses a 2 × 2 Fisher exact test:

| | Significant gene | Not significant |
|---|---:|---:|
| In pathway | `a` | `b` |
| Outside pathway | `c` | `d` |

The ORA odds ratio is:

- greater than 1 when significant genes are enriched in the pathway;
- approximately 1 when there is no enrichment; and
- less than 1 when significant genes are depleted from the pathway.

The pseudobulk and MAST branches use their own significant-gene definitions, so their ORA results should not be treated as identical tests.

### 15.3 Pathway multiple testing

For every method branch × individual `contrast_id`, Phase 09.2 separately applies BH correction across eligible pathways:

```text
rank_fdr_bh_within_branch_contrast
ora_fdr_bh_within_branch_contrast
```

Rank and ORA corrections are also separate. Phase 11 later applies broader pathway families across cell types and contrasts.

## 16. Main pathway output: `<rds_id>.pathway_results.tsv`

One row represents:

```text
one method branch × one contrast × one frozen pathway
```

Both eligible and ineligible pathway rows are present.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_pathway_results_v1`. |
| `execution_stage` | Local pilot or Minerva production. |
| `rds_id` | Broad RDS identifier. |
| `source_rds` | Source Seurat RDS. |
| `method_branch` | `pseudobulk` or `mast`. |
| `cell_type_high_resolution` | Fine cell type. |
| `contrast_id` | Unique source contrast. |
| `contrast_family` | Direct or interaction family. |
| `contrast_name` | Human-readable contrast name. |
| `ranking_method` | Signed edgeR QLF or signed MAST normal score. |
| `pathway` | MitoCarta pathway name. |
| `hierarchy` | Unique MitoCarta hierarchy label. |
| `gene_set_source` | `Human_MitoCarta3.0_MitoPathways`. |
| `gene_set_source_sha256` | Frozen MitoCarta workbook checksum. |
| `pathway_table_sha256` | Phase 03 pathway-table checksum. |
| `background_sha256` | Checksum of the branch–contrast gene background. |
| `background_genes` | Number of genes in that background. |
| `pathway_genes_frozen` | Genes in the frozen pathway definition. |
| `pathway_genes_tested` | Frozen pathway genes found in this background. |
| `rank_mean_pathway` | Mean signed score among tested pathway members. |
| `rank_mean_complement` | Mean signed score among background nonmembers. |
| `rank_mean_difference` | Pathway mean minus complement mean. |
| `direction` | Positive, negative, or no-direction label. |
| `rank_p_value` | Wilcoxon rank-sum p-value. |
| `rank_fdr_bh_within_branch_contrast` | BH FDR across eligible pathways for this branch and contrast. |
| `significant_background_genes` | Significant genes in the complete tested background. |
| `significant_pathway_genes` | Significant genes among tested pathway members. |
| `ora_odds_ratio` | Fisher-test enrichment odds ratio. |
| `ora_p_value` | Raw Fisher-test p-value. |
| `ora_fdr_bh_within_branch_contrast` | BH ORA FDR across eligible pathways for this branch and contrast. |
| `terminal_status` | `validated_complete` or `ineligible`. |
| `message` | Ineligibility explanation, otherwise blank. |

The number of rows is:

```text
number of branch–contrast rankings × number of frozen pathway definitions
```

It is not the number of significant pathways.

### 16.1 Main columns to examine first

The 32 columns provide complete provenance, but most biological interpretation begins with the following smaller set:

| Question | Main columns | Why they matter |
|---|---|---|
| Was the pathway actually tested? | `terminal_status`, `message` | An `ineligible` row is not a negative result. |
| What analysis produced the row? | `method_branch`, `ranking_method` | Pseudobulk is donor-level primary inference; MAST is the secondary nucleus-level branch. |
| What biological comparison is this? | `cell_type_high_resolution`, `contrast_name`, `contrast_family` | A pathway result has meaning only inside its fine cell type and exact contrast. |
| Which pathway is being tested? | `pathway`, `hierarchy` | Identifies the frozen MitoCarta gene set. |
| How much of the pathway was measured? | `pathway_genes_frozen`, `pathway_genes_tested`, `background_genes` | Shows the gene coverage supporting the test. |
| Did pathway genes shift together? | `rank_mean_difference`, `direction`, `rank_fdr_bh_within_branch_contrast` | These are the main ranked-distribution result fields. |
| Was the pathway enriched for individually significant genes? | `significant_pathway_genes`, `significant_background_genes`, `ora_odds_ratio`, `ora_fdr_bh_within_branch_contrast` | These are the main ORA result fields. |

The raw `rank_p_value` and `ora_p_value` are useful for auditing, but the corresponding FDR columns should normally be used to decide whether a result passed the Phase 09.2 multiple-testing threshold.

### 16.2 Step-by-step interpretation of one row

#### Step 1: require a completed test

Start with:

```text
terminal_status
message
```

- `validated_complete`: enough pathway and background genes were available, and both tests completed.
- `ineligible`: the pathway or its complement contained fewer than five tested genes. The p-value and FDR fields are then `NA`.

Do not translate `ineligible` as “the pathway was not changed.” It means the planned test did not have enough measured genes to be performed under the prespecified rule.

#### Step 2: identify the method branch

Read:

```text
method_branch
ranking_method
```

- `pseudobulk` / `signed_sqrt_edgeR_QLF`: donor-level Phase 07 evidence and the project's primary inferential branch.
- `mast` / `signed_MAST_normal_score`: nucleus-level Phase 08 evidence used for paper comparability and secondary support.

Scores from the two branches are constructed differently. Do not compare their `rank_mean_difference` values as if they used the same measurement scale. Compare direction, within-branch rank, FDR, gene coverage, and agreement of the scientific conclusion.

#### Step 3: identify the exact biological question

Read together:

```text
rds_id
cell_type_high_resolution
contrast_family
contrast_name
pathway
```

For example:

```text
rds_id                    = vasculature
cell_type_high_resolution = End
contrast_name              = AD_vs_NCI__Female__e33
pathway                    = OXPHOS
```

This row concerns the OXPHOS pathway in endothelial cells, comparing AD with NCI among Female e33 donors. It says nothing directly about another fine cell type, males, e2/e4 groups, or a different pathway.

For a direct `AD_vs_NCI` contrast:

- positive direction means pathway genes tend toward higher expression in AD;
- negative direction means they tend toward lower expression in AD.

For an interaction, use the full contrast formula. For example:

```text
AD_effect_Female_minus_Male__e33
    = (AD - NCI in Female e33) - (AD - NCI in Male e33)
```

A negative pathway direction means the pathway's AD effect is more negative, or less positive, in females than in males. It does not simply mean the pathway is down in AD.

#### Step 4: evaluate gene coverage

Read:

```text
background_genes
pathway_genes_frozen
pathway_genes_tested
```

Example:

```text
pathway_genes_frozen = 169
pathway_genes_tested = 80
```

This means the frozen MitoCarta pathway contains 169 genes, but only 80 had usable statistics in this method–contrast background. The test is based on those 80 genes.

A useful descriptive coverage fraction is:

```text
pathway_genes_tested / pathway_genes_frozen
```

Lower coverage does not automatically invalidate a result—the formal minimum is five tested genes—but it narrows the result to the measured subset and should make interpretation more cautious.

`background_genes` is the total number of genes that could participate in this particular branch–contrast analysis. It is the correct comparison universe for both ranked testing and ORA.

#### Step 5: interpret the ranked-distribution result

Read:

```text
rank_mean_pathway
rank_mean_complement
rank_mean_difference
direction
rank_p_value
rank_fdr_bh_within_branch_contrast
```

The key descriptive calculation is:

```text
rank_mean_difference
    = rank_mean_pathway - rank_mean_complement
```

- A positive value means pathway genes have more positive signed statistics than other tested genes on average.
- A negative value means pathway genes have more negative signed statistics.
- A value near zero means little average separation.

The `direction` column converts that sign into a readable label. The magnitude is a difference between constructed ranking scores, not a log fold change and not a percentage. It should not be described as “the pathway changed by 0.5-fold.”

The Wilcoxon `rank_p_value` tests whether the pathway's score distribution differs from the complement. The preferred Phase 09.2 significance column is:

```text
rank_fdr_bh_within_branch_contrast
```

Under the prespecified local threshold:

```text
rank_fdr_bh_within_branch_contrast < 0.05
```

indicates a ranked pathway result that survives correction across eligible pathways in that one method branch and contrast.

This test can detect many modest, coordinated shifts. It does not require individual pathway genes to be significant.

#### Step 6: interpret the ORA result separately

Read:

```text
significant_background_genes
significant_pathway_genes
ora_odds_ratio
ora_p_value
ora_fdr_bh_within_branch_contrast
```

`significant_background_genes` is the number of significant genes among all tested genes in that branch and contrast. `significant_pathway_genes` is how many of those significant genes belong to the pathway.

The counts require denominators. Six significant pathway genes out of 10 tested pathway genes is different from six out of 100, so always read `pathway_genes_tested` at the same time.

The odds-ratio interpretation is:

- `ora_odds_ratio > 1`: significant genes are enriched in the pathway;
- `ora_odds_ratio ≈ 1`: no enrichment;
- `ora_odds_ratio < 1`: significant genes are depleted from the pathway.

Use:

```text
ora_fdr_bh_within_branch_contrast < 0.05
```

for the prespecified local ORA significance threshold. A large odds ratio with a non-significant FDR is not sufficient evidence; small gene counts can produce unstable estimates.

ORA depends on the branch-specific definition of a significant gene:

- pseudobulk: Phase 07 within-contrast FDR below 0.05;
- MAST: Phase 08 `paper_deg = TRUE`, which also includes effect-size and detection requirements.

Consequently, pseudobulk and MAST ORA counts are not directly interchangeable.

#### Step 7: consider ranked testing and ORA together

The two tests answer different questions and can legitimately disagree:

| Ranked test | ORA | Interpretation |
|---|---|---|
| Significant | Significant | The full pathway distribution shifts and the pathway is enriched for individually significant genes. |
| Significant | Not significant | Many pathway genes may shift modestly together, but few or none cross the individual-gene significance threshold. |
| Not significant | Significant | A smaller subset of pathway genes may be strongly significant even though the complete pathway distribution does not shift uniformly. |
| Not significant | Not significant | No local FDR-controlled pathway evidence under either Phase 09.2 test. This is not proof of no biological effect. |

Neither test should automatically replace the other. Report which test supports the conclusion.

#### Step 8: remember the FDR scope

Both Phase 09.2 FDR values are corrected across eligible pathways only within:

```text
one method_branch × one contrast_id
```

They do not control FDR across all cell types, all contrasts, all RDS files, or both methods together. Phase 11 supplies the broader study-level pathway corrections. A final cross-study claim should consult the Phase 11 result as well as the Phase 09 row.

### 16.3 Worked example: coordinated pseudobulk OXPHOS shift

The local pilot contains this row:

```text
method_branch                                  = pseudobulk
cell_type_high_resolution                     = End
contrast_name                                 = AD_vs_NCI__Female__e33
pathway                                       = OXPHOS
terminal_status                               = validated_complete
background_genes                              = 5,935
pathway_genes_frozen                          = 169
pathway_genes_tested                          = 80
rank_mean_difference                          = -0.4734
direction                                     = down_in_AD_or_negative_effect
rank_p_value                                  = 2.42 × 10^-6
rank_fdr_bh_within_branch_contrast            = 7.75 × 10^-5
significant_background_genes                  = 0
significant_pathway_genes                     = 0
ora_odds_ratio                                = 0
ora_fdr_bh_within_branch_contrast             = 1
```

Interpretation:

1. The test completed and used 80 measured OXPHOS genes out of 169 frozen genes.
2. OXPHOS genes tended to have more negative pseudobulk statistics than the other 5,855 tested genes.
3. The ranked result survives local pathway correction and supports a coordinated negative OXPHOS shift in AD among Female e33 endothelial donors.
4. No individual gene in that complete contrast passed the Phase 07 within-contrast FDR threshold, so ORA had no significant genes to enrich and was not significant.

This is the classic “rank significant, ORA not significant” pattern: many modest gene shifts can create pathway-level coordination without individual genes crossing a hard cutoff.

### 16.4 Worked example: MAST ORA without a ranked shift

Another pilot row is:

```text
method_branch                                  = mast
cell_type_high_resolution                     = End
contrast_name                                 = AD_vs_NCI__Male__e33
pathway                                       = OXPHOS
terminal_status                               = validated_complete
background_genes                              = 5,228
pathway_genes_frozen                          = 169
pathway_genes_tested                          = 60
rank_mean_difference                          = 0.5404
direction                                     = up_in_AD_or_positive_effect
rank_fdr_bh_within_branch_contrast            = 0.5356
significant_background_genes                  = 39
significant_pathway_genes                     = 6
ora_odds_ratio                                = 17.25
ora_fdr_bh_within_branch_contrast             = 1.25 × 10^-4
```

Interpretation:

1. Six of the 60 tested OXPHOS genes were MAST `paper_deg` genes, out of 39 such genes in the entire 5,228-gene background.
2. The ORA odds ratio indicates strong enrichment, and the ORA result survives local correction.
3. The full OXPHOS score distribution did not pass ranked-pathway FDR, so the evidence is concentrated in a subset of genes rather than a uniform pathway-wide rank shift.
4. Because this is the MAST branch, it is secondary nucleus-level evidence and should be compared with donor-level pseudobulk results before making a primary inference.

The two worked examples use different sex contrasts and illustrate the two test types; they should not be interpreted as a direct female-versus-male comparison.

### 16.5 A practical reporting template

A clear pathway statement should include:

```text
method branch
broad RDS and high-resolution cell type
exact contrast
pathway name
tested genes / frozen genes
rank direction, rank mean difference, and rank FDR
significant pathway genes / tested pathway genes
ORA odds ratio and ORA FDR
local versus Phase 11 multiple-testing scope
```

For example:

> In the local-pilot donor-level pseudobulk branch, the OXPHOS pathway in endothelial cells showed a negative ranked shift for Female-e33 AD versus NCI (80 of 169 pathway genes tested; rank mean difference -0.473; within-branch-contrast rank FDR 7.75 × 10^-5). ORA was not significant because no individual gene in that contrast passed the Phase 07 within-contrast FDR threshold. This is a pilot, locally corrected pathway result and requires production and Phase 11 confirmation.

# Part III: Mitonuclear Balance

## 17. What mitonuclear balance means

OXPHOS uses proteins encoded by both mtDNA and nuclear DNA. Phase 09.2 calculates whether the average raw UMI count per measured mtDNA OXPHOS gene is larger or smaller than the average raw UMI count per measured nuclear OXPHOS gene.

For each primary-eligible donor–fine-cell-type pseudobulk sample:

```text
mt average      = mtDNA OXPHOS UMIs / measured mtDNA OXPHOS genes
nuclear average = nuclear OXPHOS UMIs / measured nuclear OXPHOS genes

balance = log2((mt average + 0.5) / (nuclear average + 0.5))
```

The value `0.5` is a pseudocount that prevents division by zero and stabilizes samples with very small counts.

Interpretation:

- `balance > 0`: average captured RNA per mtDNA OXPHOS gene is higher;
- `balance = 0`: the two per-gene averages are equal; and
- `balance < 0`: average captured RNA per nuclear OXPHOS gene is higher.

This is a descriptive expression balance, not a direct measurement of protein assembly, ATP production, mitochondrial number, or organelle health. The absolute value can be strongly positive because mtDNA transcripts and nuclear transcripts have different biology and capture properties. Comparisons across matched groups are usually more meaningful than interpreting the absolute value alone.

## 18. `<rds_id>.mitonuclear_balance.tsv`

One row represents one primary-eligible donor × high-resolution-cell-type pseudobulk sample.

| Column | Meaning |
|---|---|
| `schema_version` | `mitonuclear_balance_v1`. |
| `execution_stage` | Local pilot or production. |
| `rds_id` | Broad RDS identifier. |
| `source_rds` | Source RDS path. |
| `pseudobulk_id` | Matching Phase 07 pseudobulk count-matrix column. |
| `projid` | Donor identifier; read as text to preserve leading zeros. |
| `cell_type_high_resolution` | Fine cell type. |
| `diagnosis` | AD or NCI. |
| `sex` | Female or Male analysis stratum. |
| `apoe_group` | e2, e33, or e4 stratum. |
| `nuclei` | Nuclei aggregated into the pseudobulk sample. |
| `total_umi_count` | Raw counts across all measured genes. |
| `mtdna_oxphos_umi` | Counts from the configured 13 mtDNA protein genes. |
| `nuclear_oxphos_umi` | Counts from MitoCarta OXPHOS subunits excluding those 13 mtDNA genes. |
| `mtdna_oxphos_measured_genes` | Number of measured mtDNA OXPHOS genes. |
| `nuclear_oxphos_measured_genes` | Number of measured nuclear OXPHOS genes. |
| `mtdna_oxphos_fraction_total` | mtDNA OXPHOS counts divided by total UMI count. |
| `nuclear_oxphos_fraction_total` | Nuclear OXPHOS counts divided by total UMI count. |
| `mitonuclear_log2_per_gene_balance` | Log2 ratio of the pseudocount-adjusted per-gene averages. |
| `complex_i_umi` | Counts from measured MitoCarta complex I genes. |
| `complex_ii_umi` | Counts from measured complex II genes. |
| `complex_iii_umi` | Counts from measured complex III genes. |
| `complex_iv_umi` | Counts from measured complex IV genes. |
| `complex_v_umi` | Counts from measured complex V genes. |
| `mitochondrial_ribosome_umi` | Counts from measured mitochondrial-ribosome genes. |
| `mitochondrial_translation_umi` | Counts from measured mitochondrial-translation genes. |
| `complex_i_measured_genes` | Number of measured complex I genes used in the sum. |
| `complex_ii_measured_genes` | Number of measured complex II genes. |
| `complex_iii_measured_genes` | Number of measured complex III genes. |
| `complex_iv_measured_genes` | Number of measured complex IV genes. |
| `complex_v_measured_genes` | Number of measured complex V genes. |
| `mitochondrial_ribosome_measured_genes` | Number of measured mitochondrial-ribosome genes. |
| `mitochondrial_translation_measured_genes` | Number of measured mitochondrial-translation genes. |
| `gene_set_source` | Human MitoCarta3.0 MitoPathways. |
| `gene_set_source_sha256` | Frozen source checksum. |

This file contains no p-values. It supplies auditable donor-level summaries for descriptive analysis, plotting, and later sensitivity analyses.

## 19. Remaining Phase 09.2 output files

### 19.1 `<rds_id>.pathway_checks.tsv`

Each row is one automated check with the standard columns:

```text
schema_version, rds_id, check, passed, observed, expected
```

The 12 checks require:

1. unique method–contrast–pathway keys;
2. both pseudobulk and MAST branches;
3. every named frozen pathway represented for every branch–contrast;
4. blank pathway rows explicitly excluded;
5. nonempty and constant backgrounds within each branch–contrast;
6. correct external MitoCarta checksum;
7. valid rank-test p-values;
8. valid rank-test FDR values;
9. valid ORA p-values;
10. one mitonuclear row per primary-eligible pseudobulk sample;
11. finite mitonuclear numerator, denominator, and balance inputs; and
12. correct execution stage.

### 19.2 `<rds_id>.pathway_artifacts.tsv`

Each row inventories one of three core artifacts: pathway results, mitonuclear balance, or checks.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_pathway_artifacts_v1`. |
| `rds_id` | Owning RDS. |
| `artifact` | Artifact filename. |
| `path` | Project-relative path. |
| `bytes` | File size. |
| `sha256` | File checksum. |
| `records` | Row count. |
| `validation_status` | Shared validation status. |

### 19.3 `<rds_id>.pathway_status.tsv`

This one-row file summarizes the entire pathway/mitonuclear task.

| Column | Meaning |
|---|---|
| `schema_version` | `mito_pathway_status_v1`. |
| `execution_stage` | Local pilot or production. |
| `execution_phase` | Numeric scope label: 1 local, 2 production. |
| `backend` | Execution backend. |
| `run_id` | Controller run ID. |
| `stable_task_id` | Normally `pathways:<rds_id>`. |
| `source_rds` | Source RDS path. |
| `scientific_script` | `scripts/09_run_mito_pathways.R`. |
| `scientific_code_bundle_sha256` | Script checksum. |
| `scientific_config_sha256` | Analysis-config checksum. |
| `rds_manifest_sha256` | RDS-manifest checksum. |
| `pseudobulk_de_sha256` | Phase 07 gene-result checksum. |
| `mast_de_sha256` | Phase 08 gene-result checksum. |
| `pseudobulk_bundle_sha256` | Raw pseudobulk-bundle checksum. |
| `tested_universe_sha256` | Phase 03 tested-universe checksum. |
| `pathway_table_sha256` | Phase 03 pathway-table checksum. |
| `gene_set_source_sha256` | Human MitoCarta3.0 workbook checksum. |
| `pathway_source_rows` | Rows read from the Phase 03 pathway table before blank filtering. |
| `pathway_definitions` | Valid named pathway definitions tested. |
| `excluded_blank_pathway_rows` | Explicitly excluded blank definitions. |
| `de_branches` | Number of result methods, expected to be 2. |
| `branch_contrasts` | Unique method-branch × contrast rankings. |
| `pathway_result_rows` | Total rows in the pathway result table. |
| `eligible_pathway_tests` | Rows meeting the minimum-gene rule. |
| `significant_rank_fdr_005` | Eligible ranked-pathway rows with local FDR below 0.05. |
| `significant_ora_fdr_005` | Eligible ORA rows with local FDR below 0.05. |
| `mitonuclear_rows` | Rows in the balance table. |
| `peak_ram_gib` | Peak memory use. |
| `elapsed_seconds` | Runtime. |
| `validation_status` | Expected final value: `validated_complete`. |
| `failed_checks` | Failed check names, blank on success. |
| `git_revision` | Git commit. |
| `timestamp_utc` | Completion time in UTC. |

## 20. Validated local Vasculature example

The local pilot under `results/local_pilot/09_downstream/` completed with both task statuses `validated_complete`.

### 20.1 Mitochondrial fraction

The Vasculature contrast manifest contained 70 planned rows:

```text
5 fine cell types × 14 contrasts = 70
```

Only four were eligible, so the outputs contained:

- 4 model-result rows;
- 70 contrast-status rows;
- 5 fine-cell-type diagnostic rows;
- 66 explicitly ineligible contrasts;
- 0 failed contrasts; and
- 0 fraction results with BH FDR below 0.05.

The four estimates were:

| Fine cell type | Contrast | Log odds effect | Odds ratio | Raw p-value | Phase 09.1 FDR |
|---|---|---:|---:|---:|---:|
| End | Female e33 AD vs NCI | -0.0550 | 0.9465 | 0.8035 | 0.8035 |
| End | Male e33 AD vs NCI | 0.4233 | 1.5270 | 0.0638 | 0.2553 |
| End | Female-minus-Male AD effect in e33 | -0.4783 | 0.6198 | 0.1321 | 0.2641 |
| Per | Female e33 AD vs NCI | -0.0982 | 0.9065 | 0.6240 | 0.8035 |

These pilot results do not provide FDR-controlled evidence of a mitochondrial-fraction difference.

### 20.2 Pathways

The pilot had:

- 2 method branches;
- 4 eligible pseudobulk contrasts;
- 3 eligible paper-style MAST contrasts;
- 7 unique method-branch × contrast rankings;
- 149 frozen pathway definitions;
- `7 × 149 = 1,043` pathway-result rows;
- 426 eligible pathway tests and 617 explicitly ineligible rows;
- 7 ranked-pathway results with local FDR below 0.05; and
- 4 ORA results with local FDR below 0.05.

The seven significant ranked results were all from the pseudobulk branch. In Endothelial Female-e33 AD versus NCI, OXPHOS, OXPHOS subunits, complexes IV and V, and their subunit pathways had negative mean rank differences. The OXPHOS-subunit pathway also had a negative rank shift for the Endothelial Female-minus-Male e33 interaction.

The four significant ORA results came from the MAST Endothelial Male-e33 AD-versus-NCI branch: OXPHOS, OXPHOS subunits, complex I, and complex I subunits were enriched for MAST `paper_deg` genes.

These are local-pilot verification results. Production results should be read from the corresponding Minerva files and status rows.

### 20.3 Mitonuclear balance

The pilot balance table contained 196 rows, exactly matching the 196 primary-eligible Vasculature pseudobulk samples:

| Fine cell type | Rows |
|---|---:|
| End | 87 |
| Fib FLRT2 | 36 |
| Fib SLC4A4 | 7 |
| Per | 58 |
| SMC | 8 |
| **Total** | **196** |

The balance ranged from approximately 2.166 to 6.654, with a median of 4.570. These positive absolute values mean the average captured count per measured mtDNA OXPHOS gene was greater than the average per measured nuclear OXPHOS gene. They are descriptive values, not evidence by themselves of better or worse mitochondrial function.

## 21. How to inspect the TSV files

From the project root, a small table can be viewed with:

```bash
column -s $'\t' -t \
  results/local_pilot/09_downstream/vasculature.mito_fraction_models.tsv |
  less -S
```

In R, preserve `projid` as text:

```r
fraction <- read.delim(
  "results/local_pilot/09_downstream/vasculature.mito_fraction_models.tsv",
  check.names = FALSE
)

pathways <- read.delim(
  "results/local_pilot/09_downstream/vasculature.pathway_results.tsv",
  check.names = FALSE
)

balance <- read.delim(
  "results/local_pilot/09_downstream/vasculature.mitonuclear_balance.tsv",
  check.names = FALSE,
  colClasses = c(projid = "character")
)
```

Example significant-pathway filters are:

```r
rank_significant <- pathways[
  pathways$terminal_status == "validated_complete" &
    pathways$rank_fdr_bh_within_branch_contrast < 0.05,
]

ora_significant <- pathways[
  pathways$terminal_status == "validated_complete" &
    pathways$ora_fdr_bh_within_branch_contrast < 0.05,
]
```

## 22. Canonical execution order

The exact Minerva session setup and validation commands are maintained in the research plan. The two scientific modes run in this order:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mito_fraction

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathways
```

Do not interpret an RDS until both one-row status files report:

```text
validation_status = validated_complete
```

and every row in both check tables has:

```text
passed = TRUE
```

## 23. Interpretation cautions

1. **Mitochondrial fraction is not mitochondrial function.** It is a sequencing proportion influenced by biology and technical quality.
2. **An odds ratio is not a percentage-point difference.** It changes odds, not the fraction directly.
3. **A pathway result is not a single gene result.** It summarizes a predefined gene set relative to the tested background.
4. **Rank and ORA answer different questions.** A pathway can show a coordinated rank shift without containing many individually significant genes, or vice versa.
5. **Pseudobulk and MAST remain separate branches.** MAST has many nucleus-level observations but no donor random effect; pseudobulk is the primary donor-level inference.
6. **Interaction direction requires the full contrast formula.** A negative interaction is not automatically “down in AD.”
7. **Local FDR is not study-wide FDR.** Phase 11 supplies broader correction families.
8. **Ineligible does not mean negative.** It means the pathway or contrast could not be tested under the prespecified minimum-data rule.
9. **Mitonuclear balance is descriptive.** It does not directly measure protein stoichiometry, respiratory-complex assembly, or ATP production.
10. **Always check provenance.** The MitoCarta checksum, pathway-table checksum, DE-input checksums, code, configuration, and status files identify the exact scientific inputs used.
