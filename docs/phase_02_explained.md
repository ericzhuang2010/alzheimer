# Phase 02 cohort results explained

All 16 files in `results/minerva_production/02_cohort` are tab-separated tables. This directory contains donor selection and donor-level clinical covariates—not gene-expression matrices, individual nuclei, specimens, or sequencing libraries.

## Main analytic cohort

[`global_cohort_276.tsv`](../results/minerva_production/02_cohort/global_cohort_276.tsv) — **276 donors × 28 columns**

This is the authoritative analytic cohort. Each row is one donor identified by `projid`.

The principal model-ready columns are:

- `diagnosis`: `NCI` or `AD`
- `sex`: `Female` or `Male`
- `apoe_group`: `e2`, `e33`, or `e4`
- `age_death_numeric`: numeric age at death
- `age_90plus`: whether age was originally recorded as 90+
- `pmi_numeric`: postmortem interval
- `pmi_log1p`: `log(1 + PMI)`
- `age_death_scaled`, `pmi_scaled`: standardized covariates used in models

It also retains the original clinical columns, including `Study`, `msex`, `educ`, `race`, `spanish`, `apoe_genotype`, age variables, MMSE variables, `braaksc`, `ceradsc`, `cogdx`, `dcfdx_lv`, and `individualID`.

The cohort was constructed as follows:

| Selection rule | Donors remaining |
|---|---:|
| Represented in cell metadata | 427 |
| Retain NCI or AD | 290 |
| Exclude sex-discordant donors | 287 |
| Exclude APOE e2/e4 genotype | 279 |
| Require APOE genotype | 277 |
| Require PMI | 276 |
| Require age at death and valid sex | 276 |

## RDS-specific cohort files

Each of the following has the same 28 donor-level columns as the global cohort. It is the intersection of the 276 eligible donors with donors represented in that RDS file.

| Cohort file | Donors in source RDS | Eligible donors retained | Eligible donor(s) absent |
|---|---:|---:|---|
| [`astrocytes_cohort_276.tsv`](../results/minerva_production/02_cohort/astrocytes_cohort_276.tsv) | 427 | 276 | None |
| [`excitatory_set1_cohort_276.tsv`](../results/minerva_production/02_cohort/excitatory_set1_cohort_276.tsv) | 427 | 276 | None |
| [`excitatory_set2_cohort_275.tsv`](../results/minerva_production/02_cohort/excitatory_set2_cohort_275.tsv) | 425 | 275 | `15144878` |
| [`excitatory_set3_cohort_275.tsv`](../results/minerva_production/02_cohort/excitatory_set3_cohort_275.tsv) | 426 | 275 | `10102206` |
| [`immune_cohort_276.tsv`](../results/minerva_production/02_cohort/immune_cohort_276.tsv) | 426 | 276 | None |
| [`inhibitory_cohort_275.tsv`](../results/minerva_production/02_cohort/inhibitory_cohort_275.tsv) | 423 | 275 | `15144878` |
| [`oligodendrocytes_cohort_276.tsv`](../results/minerva_production/02_cohort/oligodendrocytes_cohort_276.tsv) | 427 | 276 | None |
| [`opcs_cohort_276.tsv`](../results/minerva_production/02_cohort/opcs_cohort_276.tsv) | 427 | 276 | None |
| [`vasculature_cohort_274.tsv`](../results/minerva_production/02_cohort/vasculature_cohort_274.tsv) | 423 | 274 | `11072071`, `20261901` |

The number in each filename is a **donor count**, not a nuclei count. The same donors occur in several files, so these counts must not be added together.

## Supporting and validation files

### `cohort_exclusion_flow.tsv`

[`cohort_exclusion_flow.tsv`](../results/minerva_production/02_cohort/cohort_exclusion_flow.tsv) has **7 rows × 6 columns**. It records the sequential donor filters shown above. For each step it reports:

- filtering rule
- donors before filtering
- donors excluded at that step
- donors remaining

Four donors showed sex-expression discordance, but only three were removed at that filtering step because one had already been excluded by the diagnosis filter.

### `cohort_group_counts.tsv`

[`cohort_group_counts.tsv`](../results/minerva_production/02_cohort/cohort_group_counts.tsv) has **120 rows × 7 columns**. It contains donor counts for every:

`sex × APOE group × diagnosis`

combination, separately for the global cohort and each of the nine RDS-specific cohorts. That is 12 combinations across 10 scopes.

Global counts are:

| Sex | APOE group | NCI | AD |
|---|---|---:|---:|
| Female | e2 | 17 | 8 |
| Female | e33 | 45 | 37 |
| Female | e4 | 11 | 26 |
| Male | e2 | 6 | 7 |
| Male | e33 | 53 | 29 |
| Male | e4 | 10 | 27 |

This file is useful for checking whether each comparison has enough donors.

### `cohort_rds_intersections.tsv`

[`cohort_rds_intersections.tsv`](../results/minerva_production/02_cohort/cohort_rds_intersections.tsv) has **9 rows × 8 columns**. It has one summary row per RDS file, containing:

- RDS identifier and source path
- all donors represented in that RDS
- eligible donors retained
- eligible donors absent
- absent `projid` values
- path to the resulting cohort file

This is the compact index explaining why some cohort files contain 274 or 275 donors instead of 276.

### `sex_linked_expression_check.tsv`

[`sex_linked_expression_check.tsv`](../results/minerva_production/02_cohort/sex_linked_expression_check.tsv) has **427 donors × 12 columns**. It is a donor-level sex QC table aggregated across the nine RDS files. It includes:

- reported clinical sex
- sex inferred by comparing `XIST` and `UTY` expression
- concordance result
- number of nuclei
- total raw UMI counts
- `XIST` and `UTY` counts and counts per million

There are 423 concordant and 4 discordant donors. The discordant `projid` values are `10277308`, `11326252`, `15114174`, and `50301963`.

### `cohort_checks.tsv`

[`cohort_checks.tsv`](../results/minerva_production/02_cohort/cohort_checks.tsv) has **5 rows × 5 columns**. It contains machine-readable validation tests covering:

- 427 starting metadata donors
- 276 final global donors
- expected diagnosis/sex/APOE group counts
- no duplicate global `projid`
- no missing required derived fields

All five checks passed.

### `cohort_status.tsv`

[`cohort_status.tsv`](../results/minerva_production/02_cohort/cohort_status.tsv) has **1 row × 18 columns**. It records run provenance rather than scientific observations:

- execution phase, backend, and run ID
- nine input RDS files
- generating script
- configuration and code hashes
- Git revision
- elapsed time and peak RAM
- donor and RDS counts
- timestamp and validation status

This run is marked `validated_complete`.

## Which cohort file should be used?

Use `global_cohort_276.tsv` for the overall donor definition. When analyzing one cell-class RDS object, use its matching RDS-specific cohort file.

None of the Phase 02 tables provides specimen-level or library-level identifiers.
