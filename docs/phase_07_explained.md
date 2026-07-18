# Phase 07 Explained: Donor-Level Pseudobulk Differential Expression

## 1. Purpose of Phase 07

Phase 07 is the primary donor-level differential-expression analysis. Its main scientific question is:

> Within a high-resolution cell type and a sex–APOE stratum, is gene expression different between donors with Alzheimer disease (AD) and donors with no cognitive impairment (NCI)?

It also tests whether the AD-versus-NCI effect differs between sexes or APOE strata.

The phase avoids treating thousands of nuclei from the same person as thousands of independent observations. Nuclei from the same donor and high-resolution cell type are first added together. The resulting donor-by-cell-type expression profile is one **pseudobulk sample**. edgeR then compares these independent donor-level samples.

Phase 07 consists of three ordered operations:

1. **Phase 07.1 — `pseudobulk`:** sum raw RNA counts by donor and high-resolution cell type.
2. **Phase 07.2 — `contrasts`:** create and freeze the complete manifest of planned comparisons, including comparisons that lack enough donors.
3. **Phase 07.3 — `pseudobulk_de`:** fit edgeR quasi-likelihood models and test every eligible comparison.

They form this data flow:

```text
raw Seurat RNA counts + Phase 02 cohort + Phase 04 nucleus QC
                              |
                              v
       donor x high-resolution-cell-type count columns
                     (Phase 07.1)
                              |
                              +-----------------------+
                              |                       |
                              v                       v
                pseudobulk count matrix       sample metadata
                              |                       |
                              +-----------+-----------+
                                          |
                                          v
                     frozen 14-test manifest per cell type
                                 (Phase 07.2)
                                          |
                                          v
                   one edgeR model per high-resolution cell type
                                 (Phase 07.3)
                                          |
                                          v
                    one result row per gene x eligible contrast
```

The three operations must be run in order. Phase 07.2 needs all Phase 07.1 sample tables, and Phase 07.3 needs both the count bundles and the frozen contrast manifest.

## 2. The statistical unit: donor-level pseudobulk

### 2.1 What a pseudobulk sample is

For one broad-cell-type RDS, Phase 07 groups included nuclei by:

- `projid`, the donor identifier; and
- `cell_type_high_resolution`, the fine cell-type label.

For every gene, it sums the raw counts across all nuclei in that group:

```text
pseudobulk count(gene g, donor d, fine type c)
    = sum of raw RNA counts for gene g
      over all included nuclei from donor d and fine type c
```

Thus, one donor can contribute multiple pseudobulk samples within a broad RDS if that donor has nuclei in multiple fine cell types. A donor contributes at most one pseudobulk sample to a particular fine cell type.

### 2.2 Why the aggregation is necessary

Nuclei from one donor share genetics, disease status, sex, APOE group, age, tissue handling, and many technical effects. They are nested observations, not independent biological replicates. Treating them as independent would exaggerate the sample size and could produce overly small p-values.

Phase 07 uses donors as the replicates. The number of nuclei still matters because it affects the reliability of a donor's aggregated count profile, but it does not increase the number of independent donors.

### 2.3 What Phase 07 does not aggregate

Phase 07 does not combine:

- different donors;
- different high-resolution cell types; or
- different genes.

It also does not use the normalized values created in Phase 05 as the response for edgeR. edgeR requires integer-like raw counts and performs its own library-size normalization. Phase 07.1 therefore reads the source RDS and aggregates the RNA `counts` assay. Phase 04 QC determines which nuclei are included.

## 3. Inputs and prerequisites

For each enabled broad-cell-type RDS, Phase 07 uses the following information.

| Input | Purpose |
|---|---|
| Source Seurat RDS in `data/processed/` | Supplies the raw RNA count matrix and nucleus identifiers. |
| Phase 02 cohort intersection | Identifies donors eligible for the scientific cohort and supplies diagnosis, sex, APOE, age, and PMI fields. |
| Phase 04 per-nucleus QC table | Identifies included nuclei and supplies mitochondrial and MitoCarta count summaries. |
| Phase 04 validated status | Prevents pseudobulk construction from using an unvalidated QC result. |
| `config/analysis_parameters.yml` | Supplies the 20-nucleus primary threshold, 50-nucleus sensitivity threshold, donor threshold, model, and covariate settings. |
| Enabled RDS manifest/configuration | Maps stable `rds_id` values to source RDS files and determines which broad cell types are processed. |

The primary pseudobulk threshold is at least 20 included nuclei per donor–fine-cell-type sample. A separate sensitivity flag uses at least 50 nuclei. The planned contrast threshold is at least five eligible donors in **every** group needed by the contrast.

## 4. Phase 07.1: construct pseudobulk counts

The owning script is `scripts/07_make_pseudobulk.R`, invoked through `scripts/run_pipeline.R --phase pseudobulk`.

### 4.1 Detailed procedure

For each broad-cell-type RDS, the script:

1. Resolves exactly one enabled RDS record from the execution manifest.
2. Requires a validated Phase 04 QC status for that RDS.
3. Loads the source Seurat object, updates it to the current Seurat object representation when necessary, and validates it.
4. Extracts the sparse raw RNA count matrix.
5. Joins the Phase 04 QC table to the RDS by nucleus barcode.
6. Verifies that the join is one-to-one and that every RDS nucleus has exactly one QC record.
7. Keeps nuclei whose `cohort_included` flag is true, whose donor occurs in the Phase 02 cohort, and whose fine cell-type label is nonblank.
8. Creates one group for every unique `(projid, cell_type_high_resolution)` combination.
9. Assigns stable pseudobulk IDs of the form `<rds_id>__pb00001`, `<rds_id>__pb00002`, and so on.
10. Builds a sparse nucleus-to-pseudobulk indicator matrix.
11. Multiplies the gene-by-nucleus count matrix by that indicator matrix. This efficiently sums the counts without expanding the full matrix into dense memory.
12. Builds one metadata row for every pseudobulk count column.
13. Marks samples with at least 20 nuclei as primary eligible and samples with at least 50 nuclei as sensitivity eligible.
14. Performs count-conservation and schema checks before declaring the task valid.

The output count matrix has:

- rows = genes/features in the source RNA assay;
- columns = donor–high-resolution-cell-type pseudobulk samples; and
- values = sums of raw counts across the included nuclei.

No log transformation, scaling, TMM normalization, regression, or differential testing occurs in Phase 07.1.

### 4.2 Per-sample QC summaries

In addition to expression counts, Phase 07.1 aggregates useful QC quantities for every donor–fine-cell-type sample:

- number of included nuclei;
- total RNA UMI count;
- total mitochondrial count;
- aggregate and median mitochondrial percentage;
- total MitoCarta count;
- aggregate and median MitoCarta percentage; and
- number of nuclei flagged by the robust QC rules.

An aggregate percentage is calculated from summed counts, for example:

```text
aggregate_percent_mt = 100 x sum(mitochondrial counts) / sum(total RNA counts)
```

This differs from `median_percent_mt`, which is the median of the individual nuclei's mitochondrial percentages.

### 4.3 Phase 07.1 output directory

The output directory is:

```text
results/<execution_stage>/07_pseudobulk/
```

For Minerva production, `<execution_stage>` is `minerva_production`. Each RDS produces five files. Phase 07.1 uses the source RDS filename without its `.rds` extension as the artifact prefix. For example, `Vasculature_cells.rds` produces `Vasculature_cells.pseudobulk_counts.rds`; this prefix is not necessarily identical to the stable `rds_id` (`vasculature` in this example).

### 4.4 `<source_rds_basename>.pseudobulk_counts.rds`

This is an R list rather than a tabular file. It is the main machine-readable bundle consumed by Phase 07.3.

| List element | Meaning |
|---|---|
| `schema_version` | Version of the bundle schema, currently `pseudobulk_counts_v1`. |
| `rds_id` | Stable identifier for the broad-cell-type RDS. |
| `source_rds` | Path of the source Seurat object. |
| `source_rds_sha256` | SHA-256 checksum of the source RDS. |
| `assay` | Source assay, normally RNA. |
| `count_source` | Documents that values came from `RNA_counts`. |
| `counts` | Sparse `dgCMatrix`; genes are rows and pseudobulk samples are columns. |
| `samples` | Sample metadata data frame, equivalent to the sample TSV described below. |
| `source_features` | Number of genes/features in the source count matrix. |
| `source_nuclei` | Number of nuclei in the source RDS before cohort/QC inclusion. |
| `included_nuclei` | Number of nuclei used in the pseudobulk aggregates. |
| `source_counts_sha256` | Digest of the source count object used for conservation/provenance. |
| `pseudobulk_counts_sha256` | Digest of the resulting pseudobulk count matrix. |

The count matrix column names are the `pseudobulk_id` values in `samples`. Their order must match exactly.

### 4.5 `<source_rds_basename>.pseudobulk_samples.tsv`

Each row is one donor × high-resolution-cell-type pseudobulk sample. It is not one nucleus and not one gene.

| Column | Meaning |
|---|---|
| `schema_version` | Version of the sample-table schema. |
| `rds_id` | Broad-cell-type RDS identifier. |
| `source_rds` | Source Seurat RDS path. |
| `pseudobulk_id` | Stable ID that also names a column in the count matrix. |
| `sample_index` | Sequential sample position within the RDS bundle. |
| `projid` | Donor identifier; the biological replicate. |
| `cell_type_high_resolution` | Fine cell type whose nuclei were aggregated. |
| `diagnosis` | Donor diagnostic group used in the model, such as AD or NCI. |
| `sex` | Donor sex stratum. |
| `apoe_group` | Analysis APOE stratum: `e2`, `e33`, or `e4`. |
| `age_death_numeric` | Numeric age at death used to create the age covariate. |
| `age_90plus` | Flag recording a 90-or-older age category when supplied by the cohort data. |
| `pmi_numeric` | Postmortem interval (PMI), the time between death and tissue preservation/collection, in the source unit. |
| `pmi_log1p` | `log(1 + PMI)` representation retained for provenance or sensitivity work. |
| `age_death_scaled` | Centered/scaled age covariate used in the primary edgeR design. |
| `pmi_scaled` | Centered/scaled PMI covariate used in the primary edgeR design. |
| `nuclei` | Number of included nuclei summed into this sample. |
| `total_umi_count` | Sum of RNA UMI counts across those nuclei; also the pseudobulk library size before filtering. |
| `total_mt_count` | Sum of mitochondrial-gene counts across the nuclei. |
| `aggregate_percent_mt` | `100 × total_mt_count / total_umi_count`. |
| `median_percent_mt` | Median per-nucleus mitochondrial percentage. |
| `total_mitocarta_count` | Sum of counts assigned to MitoCarta genes. |
| `aggregate_percent_mitocarta` | `100 × total_mitocarta_count / total_umi_count`. |
| `median_percent_mitocarta` | Median per-nucleus MitoCarta percentage. |
| `robust_flagged_nuclei` | Number of aggregated nuclei carrying any robust QC flag. |
| `primary_eligible` | `TRUE` when `nuclei >= 20`; only these samples enter the primary edgeR model. |
| `sensitivity_eligible` | `TRUE` when `nuclei >= 50`. |
| `primary_ineligibility_reason` | Blank if eligible; otherwise `nuclei_below_20`. |
| `sensitivity_ineligibility_reason` | Blank if eligible; otherwise `nuclei_below_50`. |

The table may contain samples that are ineligible for the primary model. Keeping them makes exclusions auditable; Phase 07.3 explicitly filters on `primary_eligible`.

#### Concrete example: the local Vasculature sample table

The validated local-pilot file is:

```text
results/local_pilot/07_pseudobulk/Vasculature_cells.pseudobulk_samples.tsv
```

It contains sample metadata and aggregated QC summaries; it does **not** contain the gene-by-sample expression counts or differential-expression results. Its dimensions and totals are:

- 1,053 rows, each representing one donor × one high-resolution vascular cell type;
- 29 metadata/QC columns;
- 1,053 unique `pseudobulk_id` values;
- 274 distinct donors;
- five high-resolution vascular cell types;
- 12,904 analytic-cohort nuclei;
- 38,053,722 raw RNA UMIs;
- 196 samples meeting the 20-nucleus primary threshold; and
- 37 samples meeting the 50-nucleus sensitivity threshold.

A donor can appear in more than one row because the same donor may contribute nuclei to multiple fine cell types. Within a particular fine cell type, however, one donor has at most one pseudobulk row. This explains why there are 1,053 pseudobulk samples but only 274 distinct donors.

The breakdown is:

| Fine cell type | Meaning | Pseudobulk samples/donors | Included nuclei | Primary eligible | Sensitivity eligible |
|---|---|---:|---:|---:|---:|
| `End` | Endothelial cells | 263 | 4,756 | 87 | 20 |
| `Fib FLRT2` | FLRT2-associated fibroblast subtype | 262 | 2,592 | 36 | 3 |
| `Fib SLC4A4` | SLC4A4-associated fibroblast subtype | 78 | 588 | 7 | 3 |
| `Per` | Pericytes | 250 | 3,800 | 58 | 9 |
| `SMC` | Smooth muscle cells | 200 | 1,168 | 8 | 2 |
| **Total** |  | **1,053** | **12,904** | **196** | **37** |

The first row provides a concrete interpretation:

| Field | Value | Interpretation |
|---|---|---|
| `pseudobulk_id` | `vasculature__pb00001` | Unique sample ID and matching count-matrix column name. |
| `projid` | `03713990` | Donor ID. Read this column as character data so the leading zero is preserved. |
| `cell_type_high_resolution` | `End` | This row aggregates the donor's endothelial nuclei. |
| `diagnosis` | `NCI` | The donor is in the no-cognitive-impairment group. |
| `sex` | `Male` | Sex stratum used in planned contrasts. |
| `apoe_group` | `e33` | APOE analysis stratum. |
| `nuclei` | 11 | Eleven endothelial nuclei were summed. |
| `total_umi_count` | 40,248 | Total raw RNA UMI count across those nuclei. |
| `aggregate_percent_mt` | approximately 0.733% | Aggregate mitochondrial fraction. |
| `primary_eligible` | `FALSE` | Eleven nuclei are below the 20-nucleus primary threshold. |
| `sensitivity_eligible` | `FALSE` | Eleven nuclei are below the 50-nucleus sensitivity threshold. |

The gene counts for this sample are not stored in the TSV. They are the 33,538 gene values in the `vasculature__pb00001` column of:

```text
results/local_pilot/07_pseudobulk/Vasculature_cells.pseudobulk_counts.rds
```

All 1,053 samples have count-matrix columns, including those below the primary threshold. Phase 07.2 uses `primary_eligible` rows to count donors in each diagnosis × sex × APOE group and decide which contrasts meet the five-donors-per-required-group rule. Phase 07.3 then subsets the count matrix to primary-eligible rows before fitting edgeR. The 50-nucleus `sensitivity_eligible` flag is retained for sensitivity analysis and does not replace the 20-nucleus rule in the primary model.

`robust_flagged_nuclei` is descriptive in this table: it counts included nuclei carrying at least one Phase 04 robust QC flag. The implemented Phase 07 primary sample eligibility rule is based directly on `nuclei >= 20`, not on requiring `robust_flagged_nuclei` to be zero.

### 4.6 `<source_rds_basename>.pseudobulk_count_conservation.tsv`

Each row is one validation check, not a biological observation.

| Column | Meaning |
|---|---|
| `schema_version` | Check-table schema version. |
| `rds_id` | RDS being checked. |
| `check` | Stable check name. |
| `passed` | Whether the requirement passed. |
| `observed` | Measured value or summary. |
| `expected` | Required value or condition. |

The checks cover:

1. validated Phase 04 status;
2. complete barcode joining;
3. pseudobulk matrix dimensions;
4. exactly one metadata row per matrix column;
5. conservation of the included-nucleus count;
6. agreement between pseudobulk column totals and sample UMI totals;
7. exact gene-wise conservation of counts;
8. maximum per-gene count difference of zero;
9. exact total-UMI conservation;
10. complete cohort metadata; and
11. consistency of the 20-nucleus primary eligibility flag.

The gene-wise check is important: for each gene, the total across the output pseudobulk columns must equal the total across the included source nuclei. Pseudobulk construction must rearrange and sum counts, not create or lose them.

### 4.7 `<source_rds_basename>.pseudobulk_manifest.tsv`

Each row describes one core Phase 07.1 artifact.

| Column | Meaning |
|---|---|
| `schema_version` | Artifact-manifest schema version. |
| `rds_id` | Owning RDS. |
| `artifact` | Logical artifact name. |
| `path` | Artifact path. |
| `bytes` | File size. |
| `sha256` | SHA-256 checksum. |
| `records` | Logical row/record count. For the RDS bundle, this is the number of pseudobulk columns. |
| `validation_status` | Artifact validation state. |

The manifest normally records the count bundle, sample table, and conservation-check table. It allows later phases to verify exactly which files were used.

### 4.8 `<source_rds_basename>.pseudobulk_status.tsv`

This is a one-row task summary used by the pipeline controller and final validation.

| Column | Meaning |
|---|---|
| `schema_version` | Status schema version. |
| `execution_stage` | `local_pilot`, `minerva_production`, or another configured stage. |
| `execution_phase` | Numeric execution-scope label from the execution config: 1 for local pilot or 2 for Minerva production. This is distinct from scientific Phase 07 and from the `pseudobulk` pipeline mode. |
| `backend` | Execution backend. |
| `run_id` | Identifier for the controller run. |
| `stable_task_id` | Stable task key, normally `pseudobulk:<rds_id>`. |
| `source_rds` | Source RDS path. |
| `source_rds_sha256` | Source RDS checksum. |
| `scientific_script` | Scientific script path. |
| `scientific_code_bundle_sha256` | Checksum representing the scientific code bundle. |
| `scientific_config_sha256` | Scientific configuration checksum. |
| `manifest_sha256` | Input RDS-manifest checksum. |
| `cohort_sha256` | Phase 02 cohort-input checksum. |
| `qc_sha256` | Phase 04 QC-input checksum. |
| `features` | Count-matrix gene/feature count. |
| `pseudobulk_samples` | Number of pseudobulk columns/sample rows. |
| `included_nuclei` | Total nuclei aggregated. |
| `analytic_donors` | Unique donors represented. |
| `fine_cell_types` | Unique high-resolution cell types represented. |
| `primary_eligible_samples` | Number of samples meeting the 20-nucleus rule. |
| `source_counts_sha256` | Digest of input counts. |
| `pseudobulk_counts_sha256` | Digest of output counts. |
| `total_umi_count` | Total UMI count after aggregation; must match the included input. |
| `peak_ram_gib` | Recorded peak memory use. |
| `elapsed_seconds` | Task elapsed time. |
| `validation_status` | Overall task state, expected to be `validated_complete`. |
| `failed_checks` | Semicolon-separated failed check names, blank on success. |
| `git_revision` | Git revision used for the run. |
| `timestamp_utc` | Completion timestamp in UTC. |

## 5. Phase 07.2: freeze the contrast manifest

The owning script is `scripts/07_build_contrast_manifest.R`, invoked with `--phase contrasts`. It reads all validated Phase 07.1 sample tables and creates a complete, explicit list of tests.

This operation does not fit a model and does not produce gene-level p-values. It answers:

- Which comparisons were planned?
- Which donor groups does each comparison require?
- How many eligible donors and nuclei are available in every group?
- Is the comparison statistically eligible under the minimum-donor rule?

Recording ineligible comparisons is essential. Their absence from the DE file then means “planned but not estimable,” not “forgotten.”

### 5.1 Analysis groups

The model group is the interaction of three donor attributes:

```text
diagnosis × sex × APOE group
```

With two diagnoses, two sexes, and three APOE groups, there can be 12 group levels:

```text
AD__Female__e2    NCI__Female__e2
AD__Female__e33   NCI__Female__e33
AD__Female__e4    NCI__Female__e4
AD__Male__e2      NCI__Male__e2
AD__Male__e33     NCI__Male__e33
AD__Male__e4      NCI__Male__e4
```

Only primary-eligible pseudobulk samples count toward contrast eligibility.

### 5.2 The 14 planned contrasts per high-resolution cell type

Every high-resolution cell type receives the same 14 planned tests.

#### Six paper-matched AD-versus-NCI contrasts

These are direct within-stratum comparisons:

1. `AD_vs_NCI__Female__e2`
2. `AD_vs_NCI__Female__e33`
3. `AD_vs_NCI__Female__e4`
4. `AD_vs_NCI__Male__e2`
5. `AD_vs_NCI__Male__e33`
6. `AD_vs_NCI__Male__e4`

For example:

```text
AD_vs_NCI__Female__e33
    = mean expression in AD, Female, e33 donors
      minus mean expression in NCI, Female, e33 donors
```

A positive log fold change means higher expression in AD for that sex–APOE stratum. These six tests carry `paper_matched = TRUE`.

#### Three sex-interaction contrasts

For each APOE group, Phase 07 compares the AD effect in females with the AD effect in males:

```text
(AD_Female - NCI_Female) - (AD_Male - NCI_Male)
```

The contrast names are:

1. `AD_effect_Female_minus_Male__e2`
2. `AD_effect_Female_minus_Male__e33`
3. `AD_effect_Female_minus_Male__e4`

A positive effect means the AD-minus-NCI change is more positive in females than in males. It does not simply mean females express the gene more highly than males.

#### Four APOE-interaction contrasts

Within each sex, Phase 07 compares the AD effect in e2 or e4 with the AD effect in the e33 reference group:

```text
(AD_e2 - NCI_e2) - (AD_e33 - NCI_e33)
(AD_e4 - NCI_e4) - (AD_e33 - NCI_e33)
```

There are two comparisons for females and two for males:

1. `AD_effect_e2_minus_e33__Female`
2. `AD_effect_e4_minus_e33__Female`
3. `AD_effect_e2_minus_e33__Male`
4. `AD_effect_e4_minus_e33__Male`

#### One global heterogeneity test

The final test is:

```text
AD_effect_heterogeneity_across_sex_APOE
```

This is a multi-degree-of-freedom omnibus test of whether all six sex–APOE-specific AD effects are equal. It jointly compares five effects with the Female–e33 AD effect used as the internal reference.

The null hypothesis is:

```text
AD effect in Female e2
= AD effect in Female e33
= AD effect in Female e4
= AD effect in Male e2
= AD effect in Male e33
= AD effect in Male e4
```

A significant omnibus result says at least one stratum-specific AD effect differs from another. It does not, by itself, identify which pair is responsible.

### 5.3 Eligibility rule

A contrast is eligible only if every required group contains at least five unique primary-eligible donors.

Examples:

- A direct Female-e33 AD-versus-NCI test needs at least five AD Female e33 donors and at least five NCI Female e33 donors.
- A Female-minus-Male e33 interaction needs at least five donors in all four AD/NCI × Female/Male e33 groups.
- The global heterogeneity test needs at least five donors in all 12 diagnosis × sex × APOE groups.

If any required group is short, the manifest keeps the row with `eligibility_status = ineligible` and records the reason. Phase 07.3 does not fit that contrast.

### 5.4 Production manifest size

The production cohort has 54 high-resolution cell types. Therefore the planned manifest contains:

```text
54 cell types × 14 contrasts = 756 rows
```

Of these:

```text
54 × 6 paper-matched contrasts = 324 rows
54 × 8 interaction/omnibus contrasts = 432 rows
```

These are planned tests, not 756 pairs of individual donors. Each row describes a group-level comparison within one fine cell type.

### 5.5 Phase 07.2 output directory and files

The output directory is:

```text
results/<execution_stage>/07_contrasts/
```

Because the contrast set combines all RDS sample tables, its files use the execution-stage prefix rather than an individual `rds_id`.

### 5.6 `<execution_stage>_contrast_manifest.tsv`

Each row is one planned contrast for one high-resolution cell type. Eligible and ineligible rows are both present.

| Column | Meaning |
|---|---|
| `schema_version` | Contrast-manifest schema version. |
| `manifest_row` | Stable sequential row number. |
| `contrast_id` | Globally unique ID combining RDS, sanitized fine cell type, and contrast name. |
| `rds_id` | Broad-cell-type RDS containing the fine cell type. |
| `cell_type_high_resolution` | Fine cell type to be modeled. |
| `contrast_family` | Direct AD/NCI, sex interaction, APOE interaction, or global heterogeneity family. |
| `contrast_name` | Human-readable stable contrast name. |
| `contrast_kind` | `single_df` for one linear contrast or `multi_df` for the omnibus test. |
| `paper_matched` | `TRUE` for the six direct Yu-style AD-versus-NCI strata; otherwise `FALSE`. |
| `contrast_terms` | Encoded group coefficients and weights used to build the edgeR contrast vector/matrix. |
| `required_groups` | All diagnosis–sex–APOE group labels required by the test. |
| `group_donor_counts` | Donor counts for each required group. |
| `group_nuclei_counts` | Included-nucleus totals for each required group. |
| `numerator_donors` | Donors in the AD numerator for direct paper-matched contrasts. |
| `denominator_donors` | Donors in the NCI denominator for direct paper-matched contrasts. |
| `numerator_nuclei` | Included nuclei represented by the direct contrast numerator. |
| `denominator_nuclei` | Included nuclei represented by the direct contrast denominator. |
| `minimum_donors_per_required_group` | Eligibility threshold, normally 5. |
| `eligibility_status` | Explicit `eligible` or `ineligible` state. |
| `ineligibility_reason` | Missing/undersized required groups when ineligible; blank when eligible. |
| `source_sample_files` | Phase 07.1 sample table(s) used to derive counts and eligibility. |

The numerator/denominator fields are populated for direct AD-versus-NCI tests. For interaction and global tests, the comparison involves more than a simple two-group numerator and denominator, so those four fields may be `NA`; use `contrast_terms`, `required_groups`, and the group-count fields instead.

### 5.7 `<execution_stage>_contrast_manifest_checks.tsv`

Each row is one global manifest validation check with these columns:

- `schema_version`
- `check`
- `passed`
- `observed`
- `expected`

The checks require:

1. globally unique pseudobulk sample IDs;
2. at least one analysis unit;
3. exactly six paper-matched rows per fine cell type;
4. exactly 14 total rows per fine cell type;
5. globally unique contrast IDs; and
6. a complete eligibility status for every planned row.

### 5.8 `<execution_stage>_contrast_manifest_artifacts.tsv`

Each row records the manifest or check file and includes:

- `schema_version`
- `artifact`
- `path`
- `bytes`
- `sha256`
- `records`
- `validation_status`

### 5.9 `<execution_stage>_contrast_manifest_status.tsv`

This one-row task status contains:

| Column | Meaning |
|---|---|
| `schema_version` | Status schema version. |
| `execution_stage` | Local pilot or Minerva production stage. |
| `execution_phase` | Numeric execution-scope label from the execution config: 1 for local pilot or 2 for Minerva production. The pipeline mode itself is identified by the task/script. |
| `backend` | Execution backend. |
| `run_id` | Controller run ID. |
| `stable_task_id` | Stable global contrast-manifest task ID. |
| `scientific_script` | Script that built the manifest. |
| `scientific_code_bundle_sha256` | Scientific code checksum. |
| `scientific_config_sha256` | Scientific configuration checksum. |
| `rds_manifest_sha256` | RDS manifest checksum. |
| `sample_table_count` | Number of Phase 07.1 sample tables read. |
| `sample_table_sha256` | Combined provenance checksum for those tables. |
| `analysis_units` | Number of RDS × fine-cell-type units. |
| `paper_matched_rows` | Number of direct AD-versus-NCI rows. |
| `interaction_rows` | Number of interaction/omnibus rows. |
| `eligible_rows` | Planned rows meeting donor requirements. |
| `ineligible_rows` | Planned rows failing donor requirements. |
| `peak_ram_gib` | Peak memory use. |
| `elapsed_seconds` | Elapsed time. |
| `validation_status` | Expected final state: `validated_complete`. |
| `failed_checks` | Failed check names, blank on success. |
| `git_revision` | Git revision. |
| `timestamp_utc` | Completion time in UTC. |

## 6. Phase 07.3: edgeR differential-expression models

The owning script is `scripts/07_run_pseudobulk_de.R`, invoked with `--phase pseudobulk_de`.

Phase 07.3 processes each broad RDS independently, but within an RDS it fits one model for each high-resolution cell type. That fitted model is reused for every eligible contrast belonging to the same fine cell type.

### 6.1 Samples entering a model

For a given high-resolution cell type, Phase 07.3 selects Phase 07.1 sample rows satisfying:

```text
cell_type_high_resolution == the current fine cell type
AND primary_eligible == TRUE
```

Each selected count-matrix column represents one donor. Samples that had fewer than 20 included nuclei remain documented in Phase 07.1 but do not enter the primary model.

### 6.2 Design matrix

The donor group is:

```r
group <- interaction(diagnosis, sex, apoe_group, drop = TRUE)
```

The implemented design is equivalent to:

```r
model.matrix(~ 0 + group + age_death_scaled + pmi_scaled)
```

The `~ 0 + group` part estimates a separate mean for every observed diagnosis–sex–APOE group. The two continuous covariates adjust for:

- age at death; and
- postmortem interval (PMI).

Both are scaled before fitting. Adjustment means that the group contrasts compare AD and NCI while accounting for systematic expression differences associated with age or PMI.

The script requires the design matrix to be full rank. If a coefficient cannot be estimated because of exact redundancy or missing variation, that fine-cell-type model fails explicitly rather than silently dropping a term.

### 6.3 edgeR processing

For each high-resolution cell type, the script performs the following steps:

1. Creates an edgeR `DGEList` from the raw pseudobulk counts.
2. Calls `filterByExpr(y, design)` to remove genes with insufficient expression for the available library sizes and design groups.
3. Removes the filtered genes and recalculates library sizes.
4. Calls `calcNormFactors`, using edgeR's TMM normalization to account for library-size and composition differences.
5. Calls `estimateDisp(..., robust = TRUE)` to estimate biological dispersion robustly.
6. Calls `glmQLFit(..., robust = TRUE)` to fit negative-binomial quasi-likelihood generalized linear models.
7. Builds each eligible contrast from the frozen Phase 07.2 terms.
8. Calls `glmQLFTest` for the contrast.
9. Calls `topTags(..., n = Inf, sort.by = "none")` to retain every tested gene in original model order, not only significant genes.
10. Applies Benjamini–Hochberg correction separately within each contrast.

edgeR models count variability across donors. The number of nuclei is not placed into the design as if nuclei were replicates. Its contribution is through the summed counts, library size, and the sample eligibility threshold.

### 6.4 Direct and interaction tests

For a `single_df` contrast, the model produces a signed `logFC`. Its meaning follows the encoded contrast:

- positive direct AD-versus-NCI `logFC`: higher in AD;
- negative direct AD-versus-NCI `logFC`: lower in AD;
- positive Female-minus-Male interaction: the AD effect is more positive in females; and
- positive e4-minus-e33 interaction: the AD effect is more positive in e4 than in e33.

The script reports the quasi-likelihood F statistic. For one-degree-of-freedom tests it also computes an approximate standard error from `abs(logFC) / sqrt(F)` and uses the fitted degrees of freedom to form an approximate 95% confidence interval.

### 6.5 Global heterogeneity test

The global contrast is a five-column contrast matrix comparing five stratum-specific AD effects with the Female-e33 AD effect. `glmQLFTest` performs a multi-degree-of-freedom test.

There is no single signed log fold change for a multi-parameter omnibus hypothesis. Therefore:

- `logFC`, `standard_error`, and confidence limits are `NA`;
- `effect_size` is the maximum absolute component log2 fold change; and
- `effect_type` is `maximum_absolute_heterogeneity_log2FC`.

This effect size is nonnegative and describes the largest component difference. Direction must be examined in the component/stratum-specific tests rather than inferred from the omnibus effect.

### 6.6 Detection rate

For each tested gene and contrast, `detection_rate_required_groups` is the fraction of relevant donor-level pseudobulk samples with a raw count greater than zero after gene filtering.

It is not the fraction of individual nuclei expressing the gene. It is a donor-sample detection measure.

### 6.7 Multiple testing in Phase 07

`fdr_bh_within_contrast` is calculated independently for each contrast over all genes tested in that contrast.

For example, the BH adjustment for `AD_vs_NCI__Female__e33` in `Ast.GRM3` uses the p-values of the genes tested in that one comparison. It does not combine:

- other fine cell types;
- other sex–APOE contrasts;
- MAST results; or
- pathway results.

The broader, explicitly defined multiple-testing families are added later in Phase 11. Phase 07's within-contrast FDR remains useful and is retained.

### 6.8 Pseudobulk basis and the “up to 14 contrasts per gene” rule

Yes, Phase 07.3 differential-expression testing is based on the donor-level pseudobulk counts constructed in Phase 07.1. For one high-resolution cell type:

- raw counts from the eligible nuclei belonging to the same donor are summed;
- one donor–cell-type aggregate is one pseudobulk sample;
- each count-matrix column entering edgeR therefore represents one donor; and
- individual nuclei are not treated as independent replicates.

edgeR applies expression filtering, TMM normalization, dispersion estimation, model fitting, and quasi-likelihood testing to this pseudobulk count matrix.

Each retained gene can be tested in **up to 14 contrasts per high-resolution cell type**. The 14 planned contrasts are:

```text
6 direct AD-versus-NCI contrasts
+ 3 sex-interaction contrasts
+ 4 APOE-interaction contrasts
+ 1 global heterogeneity contrast
= 14 planned contrasts
```

“Up to” is important. Four conditions determine how many result rows a gene actually receives:

1. The gene must pass edgeR's `filterByExpr` for that fine-cell-type model.
2. A contrast is run only if every diagnosis × sex × APOE group it requires has at least five primary-eligible donors.
3. If only `k` of the 14 planned contrasts are eligible, each retained gene normally produces `k` result rows for that fine cell type.
4. An ineligible contrast produces no gene rows, but remains explicitly recorded in `<rds_id>.pseudobulk_contrast_status.tsv`.

Consequently:

```text
result rows for one fine cell type
    = genes retained by edgeR × eligible contrasts for that fine cell type
```

The global heterogeneity test counts as one of the 14 contrast rows per gene even though it is a multi-degree-of-freedom test.

For the local Vasculature pilot:

```text
Endothelial (End):
    5,935 retained genes × 3 eligible contrasts = 17,805 rows

Pericyte (Per):
    5,199 retained genes × 1 eligible contrast = 5,199 rows

Total:
    17,805 + 5,199 = 23,004 gene-result rows
```

Thus, 14 is the maximum number of planned test results per retained gene and fine cell type; it is not guaranteed for every gene or cell type.

## 7. Phase 07.3 output files

The output directory is:

```text
results/<execution_stage>/07_pseudobulk_de/
```

Each broad RDS produces six files. Their prefix is the lower-case stable `rds_id`, for example `vasculature.pseudobulk_de.tsv.gz`.

### 7.1 `<rds_id>.pseudobulk_de.tsv.gz`

This is the primary gene-level result table. It is gzip-compressed TSV text.

#### What one row represents

One row is:

```text
one gene
× one eligible contrast
× one high-resolution cell type
× one broad-cell-type RDS
```

A row is **not** a pseudobulk sample. The donor-level pseudobulk samples were the columns of the model input matrix. One DE row summarizes a statistical test across multiple donor samples.

The same gene can appear many times because it is tested in multiple contrasts and cell types. Ineligible contrasts produce no gene rows; they are represented in the contrast-status file.

#### Column dictionary

| Column | Meaning |
|---|---|
| `schema_version` | Gene-result schema version. |
| `rds_id` | Broad-cell-type RDS identifier. |
| `source_rds` | Source Seurat RDS path. |
| `cell_type_high_resolution` | Fine cell type whose donors were modeled. |
| `manifest_row` | Link to the exact frozen Phase 07.2 manifest row. |
| `contrast_id` | Globally unique contrast identifier. |
| `contrast_family` | Direct AD/NCI, sex interaction, APOE interaction, or global heterogeneity family. |
| `contrast_name` | Stable human-readable contrast name. |
| `contrast_kind` | `single_df` or `multi_df`. |
| `paper_matched` | Whether this is one of the six direct paper-matched AD-versus-NCI comparisons. |
| `gene` | Tested feature/gene name from the count-matrix row. |
| `effect_type` | `log2_fold_change` for single-df contrasts or the maximum-absolute heterogeneity type for the omnibus test. |
| `effect_size` | Primary numeric effect. Equals signed `logFC` for single-df tests; maximum absolute component effect for the omnibus test. |
| `logFC` | edgeR estimated log2 fold change for single-df tests; `NA` for the omnibus test. |
| `standard_error` | Approximate standard error for a single-df logFC; `NA` for the omnibus test. |
| `ci95_low` | Approximate lower 95% confidence limit for single-df logFC. |
| `ci95_high` | Approximate upper 95% confidence limit for single-df logFC. |
| `logCPM` | edgeR average log2 counts per million, an abundance summary across modeled libraries. |
| `F` | edgeR quasi-likelihood F statistic. For the omnibus test it assesses several contrast dimensions jointly. |
| `p_value` | Raw p-value from `glmQLFTest`. |
| `fdr_bh_within_contrast` | BH-adjusted p-value over the genes in this one contrast. |
| `detection_rate_required_groups` | Fraction of the contrast's required donor pseudobulk samples with count greater than zero. |
| `numerator_donors` | Number of AD donors for a direct paper-matched contrast; typically `NA` for interaction/omnibus tests. |
| `denominator_donors` | Number of NCI donors for a direct paper-matched contrast; typically `NA` for interaction/omnibus tests. |
| `numerator_nuclei` | Included nuclei underlying the direct contrast numerator. |
| `denominator_nuclei` | Included nuclei underlying the direct contrast denominator. |
| `model_samples` | Total primary-eligible donor–fine-cell-type pseudobulk samples used in the fitted model. |
| `model_donors` | Unique donors used in the fitted model. Within one fine type this normally equals `model_samples`. |

The file contains all genes retained by `filterByExpr`, not only differentially expressed genes. To identify candidate DE genes, filter by the desired FDR and effect-size criteria while preserving the contrast and cell-type identifiers.

### 7.2 `<rds_id>.pseudobulk_model_diagnostics.tsv`

Each row describes one high-resolution-cell-type model.

| Column | Meaning |
|---|---|
| `schema_version` | Diagnostic schema version. |
| `rds_id` | Broad RDS identifier. |
| `cell_type_high_resolution` | Fine cell type. |
| `samples` | Primary-eligible pseudobulk samples available to the model. |
| `donors` | Unique donors available to the model. |
| `input_genes` | Genes present before `filterByExpr`. |
| `tested_genes` | Genes retained and modeled after filtering. |
| `design_columns` | Number of group and covariate columns in the design matrix. |
| `design_rank` | Rank of that design matrix; it must equal `design_columns`. |
| `residual_df_min` | Smallest residual degrees of freedom across fitted genes. |
| `model_status` | Usually `fitted`, `not_fit_no_eligible_contrasts`, or `failed`. |
| `message` | Diagnostic explanation, especially when not fitted or failed. |

A fine cell type with no eligible contrasts does not need an edgeR fit. It is retained as `not_fit_no_eligible_contrasts` so the absence of gene results is explained.

### 7.3 `<rds_id>.pseudobulk_contrast_status.tsv`

Each row corresponds to one Phase 07.2 manifest row belonging to the RDS. It is the authoritative reconciliation between planned tests and completed tests.

| Column | Meaning |
|---|---|
| `schema_version` | Contrast-status schema version. |
| `rds_id` | Broad RDS identifier. |
| `manifest_row` | Exact planned manifest row. |
| `contrast_id` | Unique contrast ID. |
| `cell_type_high_resolution` | Fine cell type. |
| `contrast_family` | Contrast family. |
| `contrast_name` | Contrast name. |
| `eligibility_status` | Eligibility determined in Phase 07.2. |
| `terminal_status` | `validated_complete`, `ineligible`, or `failed`. |
| `genes_returned` | Number of gene rows produced for a completed contrast; zero for ineligible tests. |
| `message` | Reason for ineligibility/failure or a completion note. |

The status file should have exactly one terminal row for every planned contrast in the RDS, whether or not the contrast generated gene results.

### 7.4 `<rds_id>.pseudobulk_de_checks.tsv`

Each row is one RDS-level validation check with columns:

- `schema_version`
- `rds_id`
- `check`
- `passed`
- `observed`
- `expected`

The six checks require:

1. one terminal status per manifest row;
2. completion of every eligible contrast;
3. explicit representation of every ineligible contrast;
4. unique `(cell type, contrast, gene)` result keys;
5. p-values within `[0, 1]`; and
6. within-contrast FDR values within `[0, 1]`.

### 7.5 `<rds_id>.pseudobulk_de_artifacts.tsv`

Each row records one primary Phase 07.3 artifact.

| Column | Meaning |
|---|---|
| `schema_version` | Artifact schema version. |
| `rds_id` | Owning RDS. |
| `artifact` | Logical artifact name. |
| `path` | File path. |
| `bytes` | File size. |
| `sha256` | File checksum. |
| `records` | Number of rows/records. |
| `validation_status` | Artifact validation state. |

It records the compressed DE result, model diagnostics, contrast status, and validation checks.

### 7.6 `<rds_id>.pseudobulk_de_status.tsv`

This one-row controller/scientific status summarizes the entire RDS task.

| Column | Meaning |
|---|---|
| `schema_version` | Status schema version. |
| `execution_stage` | Local pilot or Minerva production. |
| `execution_phase` | Numeric execution-scope label from the execution config: 1 for local pilot or 2 for Minerva production. This is not the scientific phase number. |
| `backend` | Execution backend. |
| `run_id` | Controller run ID. |
| `stable_task_id` | Stable task ID, normally `pseudobulk_de:<rds_id>`. |
| `source_rds` | Source RDS path. |
| `scientific_script` | Owning scientific script. |
| `scientific_code_bundle_sha256` | Scientific code checksum. |
| `scientific_config_sha256` | Scientific configuration checksum. |
| `rds_manifest_sha256` | RDS manifest checksum. |
| `pseudobulk_bundle_sha256` | Checksum of the Phase 07.1 count bundle. |
| `contrast_manifest_sha256` | Checksum of the frozen Phase 07.2 manifest. |
| `fine_cell_types` | Fine cell types represented in the RDS manifest subset. |
| `manifest_rows` | Planned contrasts belonging to the RDS. |
| `eligible_contrasts` | Planned contrasts meeting donor requirements. |
| `completed_contrasts` | Eligible contrasts fitted successfully. |
| `ineligible_contrasts` | Planned contrasts explicitly marked ineligible. |
| `failed_contrasts` | Eligible contrasts ending in failure. |
| `result_rows` | Gene-level rows written to the compressed DE table. |
| `significant_fdr_005` | Rows with within-contrast BH FDR below 0.05; no separate effect-size threshold is applied to this count. |
| `peak_ram_gib` | Peak memory use. |
| `elapsed_seconds` | Elapsed time. |
| `validation_status` | Expected final state: `validated_complete`. |
| `failed_checks` | Failed validation checks, blank on success. |
| `git_revision` | Git revision. |
| `timestamp_utc` | Completion time in UTC. |

## 8. How result-row counts arise

The number of gene-result rows is not the number of donors, nuclei, or pseudobulk samples. For one RDS it is:

```text
sum, over fitted fine cell types,
    tested genes for that fine type × eligible contrasts for that fine type
```

Different fine cell types can retain different numbers of genes after `filterByExpr`. Ineligible contrasts contribute zero result rows but still contribute one row to the contrast-status file.

In the local Vasculature pilot:

- Endothelial (`End`) retained 5,935 genes and had three eligible contrasts;
- Pericyte (`Per`) retained 5,199 genes and had one eligible contrast; and
- the remaining fine cell types had no eligible contrast.

Therefore:

```text
5,935 × 3 + 5,199 × 1 = 23,004 gene-result rows
```

This exact reconciliation is a useful integrity check.

## 9. Local-pilot checkpoint

The shared code paths and output schemas are the same for the local pilot and Minerva production; execution configuration changes the RDS set, paths, and resource scope.

The completed local Vasculature pilot produced:

- 33,538 input features;
- 1,053 donor–fine-cell-type pseudobulk samples;
- 12,904 included nuclei from 274 donors and five fine cell types;
- 196 samples meeting the 20-nucleus primary rule;
- 38,053,722 total UMIs, conserved exactly;
- 70 planned contrasts (`5 × 14`);
- 30 paper-matched rows and 40 interaction/omnibus rows;
- 4 eligible and 66 ineligible contrasts;
- 23,004 gene-level edgeR result rows; and
- all Phase 07 scientific/controller statuses `validated_complete`.

The four eligible tests were:

- Endothelial Female-e33 AD versus NCI;
- Endothelial Male-e33 AD versus NCI;
- Endothelial Female-minus-Male AD-effect interaction in e33; and
- Pericyte Female-e33 AD versus NCI.

Three result rows had within-contrast FDR below 0.05, all in the Endothelial Male-e33 direct comparison:

| Gene | log2 fold change | Approximate 95% CI | Within-contrast FDR |
|---|---:|---:|---:|
| `PLPP1` | 1.541 | 0.915 to 2.166 | 0.0149 |
| `HBA1` | 4.745 | 2.833 to 6.658 | 0.0149 |
| `HBA2` | 4.197 | 2.446 to 5.947 | 0.0178 |

These values are a pilot verification, not a substitute for the complete Minerva production analysis. The Minerva Phase 07 artifact directories are not currently synchronized into this local checkout, so production-specific row totals should be read from the Minerva status files. The production manifest structure is nevertheless fixed at 54 fine cell types × 14 planned contrasts = 756 rows.

## 10. Validation and interpretation checklist

Before interpreting Phase 07 results, verify all of the following:

1. Every Phase 07.1 RDS status is `validated_complete`.
2. Every Phase 07.1 count-conservation check passed.
3. The Phase 07.2 manifest contains exactly 14 rows per fine cell type and six paper-matched rows per fine cell type.
4. Every manifest row has an explicit eligibility status.
5. Every Phase 07.3 RDS status is `validated_complete`.
6. Every eligible contrast has `terminal_status = validated_complete`.
7. Every ineligible contrast has `terminal_status = ineligible` and zero result rows.
8. No contrast has `terminal_status = failed`.
9. Gene-result keys are unique.
10. P-values and FDR values are within `[0, 1]`.
11. Checksums identify the intended code, config, RDS, pseudobulk bundle, and contrast manifest.

When reading a significant row, always report at least:

- the broad RDS and high-resolution cell type;
- the exact contrast;
- whether it is direct, interaction, or omnibus;
- the effect size and its direction where defined;
- donor and nucleus support;
- detection rate;
- the multiple-testing scope; and
- whether the result comes from local pilot or Minerva production.

## 11. Common interpretation mistakes

### Mistake 1: treating a DE row as one pseudobulk

A pseudobulk is one donor–fine-cell-type count column in Phase 07.1. A Phase 07.3 DE row is one gene-level statistical result calculated across multiple pseudobulk donor samples.

### Mistake 2: treating nuclei as independent samples

The independent model samples are donors. `numerator_nuclei` and `denominator_nuclei` describe underlying data volume; they are not the model's replicate count.

### Mistake 3: reading an interaction as a simple group difference

`AD_effect_Female_minus_Male__e33` tests a difference of AD effects:

```text
(AD - NCI in females) - (AD - NCI in males)
```

It does not test female expression minus male expression.

### Mistake 4: assigning direction to the omnibus test

The global heterogeneity test has no single direction. Its reported effect is a maximum absolute component effect, and its p-value tests several parameters jointly.

### Mistake 5: assuming a missing gene table means an unplanned test

An ineligible planned contrast intentionally has no gene rows. Confirm its state in `pseudobulk_contrast_status.tsv` and its donor deficit in the frozen contrast manifest.

### Mistake 6: interpreting within-contrast FDR as study-wide FDR

Phase 07 adjusts across genes inside one contrast. Phase 11 defines and calculates the broader testing families.

## 12. Execution notes

The canonical Phase 07 commands and the required Minerva shell/MKL setup are maintained in Section 14 of `docs/mitochondria_sex_apoe_research_plan.md`. In order, the pipeline modes are:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase contrasts

LD_PRELOAD="$MKL_PRELOAD" Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk_de
```

On Minerva, Phase 07.3's edgeR fit must use the documented, matching Intel MKL runtime and scoped `LD_PRELOAD="$MKL_PRELOAD"` prefix. Run the representative edgeR/MKL preflight in the research plan first. A simple small-matrix test is not sufficient because it may not load the same MKL architecture component used by edgeR's fitting path.

Do not run Phase 07.2 before every intended Phase 07.1 sample table is validated. Do not run Phase 07.3 against a contrast manifest that can still change. If Phase 07 inputs, eligibility thresholds, scientific configuration, or code change, regenerate the dependent outputs rather than mixing artifacts from different scientific states.
