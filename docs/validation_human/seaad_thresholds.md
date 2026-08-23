# SEA-AD post-hoc exploratory threshold amendment

**Status:** amendment approved and recorded; execution pending  
**Date:** 2026-08-22  
**Scope:** SEA-AD only

## Purpose and interpretation

This record amends the SEA-AD analysis contract for one explicitly **post-hoc
exploratory** rerun. It does not redefine the completed primary SEA-AD result,
and it does not change or rerun the frozen ROSMAP Phase 18 analysis. Results
from this tier must be labeled exploratory and kept under a distinct result-tier
identifier. Per the execution request, it replaces the former SEA-AD files in
the canonical validation output directory rather than preserving a parallel
copy of the former results.

## Approved SEA-AD changes

Exactly four decision gates change:

| Stage | Previous SEA-AD gate | Amended exploratory gate |
|---|---:|---:|
| Contrast eligibility | At least 5 independent donors in each disease arm | **At least 3 independent donors in each disease arm** |
| DEG query membership | Within-contrast BH FDR `< 0.05` and `abs(log2FC) > log2(1.3)` | **Within-contrast BH FDR `< 0.05` only**, retaining the observed sign for the up/down query |
| Aggregate coverage | Coverage `>= 0.80` | **Coverage `>= 0.50`** |
| Aggregate significance | Network-wide BH-adjusted aggregate `q <= 0.05` | **Network-wide BH-adjusted aggregate `q <= 0.10`** |

The FDR-only rule is the active DEG-query rule for this exploratory tier. The
1.3-fold-change requirement is not applied in that tier.

## Gates that remain unchanged

All other scientific and technical rules remain as previously specified:

- The biological replicate is the donor; nuclei are not treated as independent
  replicates.
- A donor–supertype pseudobulk profile requires at least 20 nuclei.
- The six sex/APOE groups, fine-supertype grid, disease contrast, covariates,
  grouped edgeR design, TMM normalization, robust quasi-likelihood fitting,
  `filterByExpr`, and within-contrast BH adjustment remain unchanged.
- Query genes must be core-MitoCarta genes and enter the up or down query
  according to the sign of `log2FC`.
- A query gene must occur in the exact tested-gene-induced network background.
- An effective query still requires at least 3 genes before KDA is run.
- KDA still tests layers 1–3.
- A conservative supporting run still requires within-run BH `q <= 0.05`,
  overlap with at least 2 other query genes, and fold enrichment `> 1`.
- Aggregate evidence still uses ACAT followed by BH adjustment within the
  applicable network family and requires at least 1 conservative supporting
  run. Only the coverage and final aggregate-q cutoffs change as listed above.
- The assessable driver universe, MT versus non-MT classification, ranking and
  tie rules, maximum display of 5 genes per network and driver class, and
  no-backfill rule remain unchanged.

## ROSMAP remains frozen

ROSMAP candidate construction, KDA run scope, minimum effective query size,
coverage threshold, support rule, aggregate-q threshold, selected units, and
ranks remain exactly as frozen in Phase 18. No SEA-AD amendment is to be
applied retroactively to ROSMAP. Any later overlap analysis must compare the
new exploratory SEA-AD tier with the existing frozen ROSMAP candidate set and
state that the two cohorts used different SEA-AD-versus-ROSMAP thresholds.

The governing source records are:

- [`scripts/validation_human/seaad_deg_config.yml`](../../scripts/validation_human/seaad_deg_config.yml)
- [`scripts/validation_human/seaad_phase18_validation_config.yml`](../../scripts/validation_human/seaad_phase18_validation_config.yml)
- [`config/phase12_kda.yml`](../../config/phase12_kda.yml)
- [`config/phase18_key_driver_selection.yml`](../../config/phase18_key_driver_selection.yml)

## Execution pending / results to fill

No amended DEG, KDA, selection, or overlap result has yet been produced or is
claimed in this record. After the isolated rerun validates successfully, fill
in:

- exploratory result-tier ID, output path, execution date, code revision, and
  configuration hash;
- eligible/completed DEG contrasts and up/down query counts;
- active KDA calls and their terminal outcomes;
- passing and displayed MT/non-MT units and unique genes; and
- strict unit-level and gene-level overlap with the frozen ROSMAP candidates.

Do not populate these fields from the previous primary run or from projected
counts. They must be derived from the validated amended artifacts.
