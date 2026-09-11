# Harmonized broad-cell KDA donor-threshold sensitivity: 3 versus 5 per arm

**Assessment date:** 2026-09-11  
**ROSMAP source/KDA:** Phase 21 / Phase 22  
**SEA-AD source/KDA:** VH13 / VH14

## Question and interpretation

This sensitivity analysis asks what happens when the disease-contrast
eligibility requirement is raised from at least 3 to at least 5 **donors per
disease arm** in both cohorts.

The value 3 in this workflow is not a nucleus threshold. Donors are the
biological replicates in the broad-cell pseudobulk models. The separate
profile-level requirement remains at least 20 nuclei per donor x broad-cell
profile and is not changed here.

## Method

The 5-donor result is an exact eligibility-gating sensitivity derived from the
frozen run manifests:

1. retain a source contrast only when both recorded disease-arm donor counts
   are at least 5;
2. retain a KDA run only when its source contrast remains eligible; and
3. count the significant KDA returns belonging to retained runs.

No DEG or KDA model was refitted. Raising an eligibility gate does not alter
the samples, query, network, or statistics for a retained contrast; it only
removes contrasts with an arm size of 3 or 4. For ROSMAP, the Phase 21
regression checks also show that the 40 retained contrasts reproduce the prior
minimum-5 Phase 08 results within the recorded cross-platform tolerances.

## Primary comparison

| Cohort | Minimum donors/arm | Eligible contrasts | KDA runs | Significant driver rows | Unique raw driver genes | Unique non-`MT-*` drivers |
|---|---:|---:|---:|---:|---:|---:|
| ROSMAP | 3 | 42 | 3 | 39 | 39 | 33 |
| ROSMAP | 5 | 40 | 2 | 13 | 13 | 13 |
| SEA-AD | 3 | 28 | 5 | 24 | 21 | 18 |
| SEA-AD | 5 | 20 | 5 | 24 | 21 | 18 |

Relative to the 3-donor gate:

- ROSMAP loses 2 eligible contrasts (4.8%), 1 of 3 KDA runs (33.3%), and
  26 of 39 significant driver rows (66.7%). Its unique non-`MT-*` driver count
  falls from 33 to 13 (60.6%).
- SEA-AD loses 8 eligible contrasts (28.6%), but loses no KDA runs and no
  returned drivers.

The structural design still contains 42 possible broad-cell x sex/APOE
contrasts in each cohort. “Eligible contrasts” above means the number that pass
the donor gate and have an estimable source DEG contrast.

## Which contrasts are removed?

### ROSMAP

Only two ROSMAP contrasts fail the 5-donor gate:

| Broad cell | Group | AD / NCI donors | Status at minimum 3 | Effect at minimum 5 |
|---|---|---:|---|---|
| Vasculature cells | F_e2 | 3 / 10 | Effective query had 1 gene; KDA not run | Contrast removed; no driver-count effect |
| Vasculature cells | M_e2 | 4 / 3 | KDA run with 78 effective query genes and 26 drivers | Contrast and all 26 returned driver rows removed |

The removed `Vasculature cells x M_e2` call accounts for the entire ROSMAP
change in KDA output. It was already labeled `exploratory_min3_support`. It
contributed 26 of 39 ROSMAP driver rows, including all six ROSMAP `MT-*`
driver rows. Of its 26 returns, 20 were non-`MT-*` genes.

The 5-donor ROSMAP result therefore contains only:

- `Astrocytes x F_e4`: 4 significant drivers; and
- `OPCs x F_e4`: 9 significant drivers.

### SEA-AD

Eight currently estimable SEA-AD contrasts fail the 5-donor gate:

- all seven `M_e4` broad-cell contrasts, each with 4 Dementia and 3
  No-dementia donors; and
- `Vasculature cells x F_e4`, with 9 Dementia and 4 No-dementia donors.

All eight had empty mitochondrial DEG queries under the existing analysis.
None had reached KDA, so removing them changes the eligible-contrast count but
does not change the five KDA runs or any returned driver.

The five retained SEA-AD calls remain `Astrocytes x F_e4` and four `M_e33`
calls: excitatory neurons, inhibitory neurons, microglia, and
oligodendrocytes.

## Global-driver sensitivity

The KDA output contains all significant candidate drivers and separately marks
the less-redundant `global_key_driver` subset.

| Cohort | Minimum donors/arm | Global-driver rows | Unique global drivers | Unique global non-`MT-*` drivers |
|---|---:|---:|---:|---:|
| ROSMAP | 3 | 14 | 14 | 13 |
| ROSMAP | 5 | 9 | 9 | 9 |
| SEA-AD | 3 | 14 | 12 | 9 |
| SEA-AD | 5 | 14 | 12 | 9 |

These non-`MT-*` counts are descriptive post hoc filters. A compliant final
release should apply the frozen driver-eligibility rule before within-call BH
correction rather than merely remove `MT-*` rows afterward.

## Interpretation

Raising the donor threshold to 5 has very different effects in the two
cohorts:

- **ROSMAP becomes much less dominated by a low-support call.** The
  large 4-versus-3-donor vasculature result disappears, leaving 13 drivers from
  two better-supported `F_e4` calls. This is a scientifically cleaner summary,
  although it has less coverage.
- **SEA-AD loses contrast coverage but not KDA evidence.** Every newly excluded
  contrast already had an empty query, so the downstream KDA result is exactly
  unchanged.
- **The cross-cohort validation conclusion is unchanged.** At both thresholds,
  the only exact executed stratum shared by the cohorts is
  `Astrocytes x F_e4`, and it has zero shared drivers. The admissible non-`MT-*`
  gene overlap also remains zero.
- **A 5-donor gate is still not confirmatory support.** The plan's
  confirmatory tier requires at least 10 donors per arm. All five retained
  SEA-AD calls remain nonconfirmatory because their arm counts are 9/5 or
  9/10.

Therefore, a 5-donor gate improves the defensibility of the ROSMAP descriptive
result by removing the dominant minimum-3 exploratory call, but it does not
create additional ROSMAP/SEA-AD validation and does not solve the limited
matched-stratum problem.

## Source artifacts

- ROSMAP input manifest:
  `results/minerva_production/21_harmonized_broad_kda_inputs/query_manifest.tsv`
- ROSMAP KDA manifest and returns:
  `results/minerva_production/22_harmonized_broad_kda_combo/`
- ROSMAP Phase 08 regression checks:
  `results/minerva_production/21_harmonized_broad_kda_inputs/00_source_deg_min3/phase08_regression_checks.tsv`
- SEA-AD input manifest:
  `results/validation_human/13_harmonized_broad_kda_inputs/query_manifest.tsv`
- SEA-AD KDA manifest and returns:
  `results/validation_human/14_harmonized_broad_kda_combo/`

No existing result or plan file was modified for this sensitivity analysis.
