# SEA-AD post-hoc exploratory threshold amendment

**Status:** executed; `validated_complete`
**Authorization date:** 2026-08-22
**Execution date:** 2026-08-22 (America/New_York; UTC completion 2026-08-23)
**Scope:** SEA-AD only

## Purpose and interpretation

This record amends the SEA-AD analysis contract for one explicitly **post-hoc
exploratory** rerun. It does not redefine the completed primary SEA-AD result,
and it does not change or rerun the frozen ROSMAP Phase 18 analysis. Results
from this tier are labeled exploratory and use a distinct result-tier
identifier. Per the execution request, they replace the former SEA-AD files in
the canonical validation output directory; no parallel copy of the former
SEA-AD result was retained.

## Executed SEA-AD changes

Exactly four decision gates changed:

| Stage | Previous SEA-AD gate | Executed exploratory gate |
|---|---:|---:|
| Contrast eligibility | At least 5 independent donors in each disease arm | **At least 3 independent donors in each disease arm** |
| DEG query membership | Within-contrast BH FDR `< 0.05` and `abs(log2FC) > log2(1.3)` | **Within-contrast BH FDR `< 0.05` only**, retaining the observed sign for the up/down query |
| Aggregate coverage | Coverage `>= 0.80` | **Coverage `>= 0.50`** |
| Aggregate significance | Network-wide BH-adjusted aggregate `q <= 0.05` | **Network-wide BH-adjusted aggregate `q <= 0.10`** |

The FDR-only rule is the active DEG-query rule for this exploratory tier. The
1.3-fold-change requirement is retained only as an auxiliary historical
summary and was not applied to active query membership.

## Gates that remained unchanged

- The biological replicate is the donor; nuclei are not independent replicates.
- A donor–supertype pseudobulk profile requires at least 20 nuclei.
- The six sex/APOE groups, fine-supertype grid, disease contrast, covariates,
  grouped edgeR design, TMM normalization, robust quasi-likelihood fitting,
  `filterByExpr`, and within-contrast BH adjustment remain unchanged.
- Query genes must be core-MitoCarta genes, use the sign of `log2FC`, and
  occur in the exact tested-gene-induced network background.
- An effective query still requires at least 3 genes; KDA still tests layers
  1–3.
- A conservative supporting run still requires within-run BH `q <= 0.05`,
  overlap with at least 2 other query genes, and fold enrichment `> 1`.
- Aggregate evidence still uses ACAT followed by BH adjustment within the
  applicable network family and requires at least 1 conservative supporting
  run.
- MT/non-MT classification, ranking and tie rules, the maximum display of 5
  genes per network and driver class, and the no-backfill rule remain unchanged.

## Validated execution

- Result tier:
  `posthoc_exploratory__fdr_only__donor3__query3__coverage50__q10`
- Canonical output:
  `results/validation_human/10_seaad_kda_rediscovery/`
- Code revision recorded by the outputs:
  `f377c0554918d7920f0bf69fb5293543f46d1bc0`
- VH10 configuration SHA-256:
  `621e7ce7f7ec09bde2c112c19ac55b156b0440e0fd21da08f008e65947ea3b81`

| Stage | Validated amended result |
|---|---:|
| Fine contrasts meeting the 3-donor support gate | 382 |
| Model-feasible/completed fine contrasts | 381 |
| Completed signed source directions | 762 |
| Active KDA calls (effective query size >=3) | 42 |
| Calls with significant KDA returns | 27 |
| Calls without significant KDA returns | 15 |
| Passing/displayed SEA-AD candidate units | 14 |
| Unique selected SEA-AD genes | 12 |
| Frozen ROSMAP units testable in SEA-AD | 36 of 47 |
| Strict shared network-gene-class units | 6 |
| Unique shared genes | 6 |

The active-call distribution is 20 AD-up and 22 AD-down calls: Astrocytes
1/0, Excitatory neurons 10/10, Inhibitory neurons 6/10, Microglia 1/0,
Oligodendrocytes 2/2, and no active calls in OPCs or Vasculature.

Three selected units have aggregate q values between 0.05 and 0.10:
`MT-ND1` in Inhibitory neurons (q=0.0971), `RPL30` in Inhibitory neurons
(q=0.0953), and `KANSL1L` in Oligodendrocytes (q=0.0902). All 14 selected
units have coverage 1.0; therefore the coverage relaxation did not itself admit
a selected unit in this execution.

## ROSMAP remained frozen

ROSMAP candidate construction, KDA run scope, minimum effective query size,
coverage threshold, support rule, aggregate-q threshold, selected units, and
ranks remained exactly as frozen in Phase 18. The overlap phase replayed the
161 frozen ROSMAP runs and reproduced 78 passing and 47 selected ROSMAP units
before comparison. Thus the cross-cohort comparison deliberately uses the
amended SEA-AD thresholds above versus the original frozen ROSMAP thresholds.

The governing source records are:

- [`scripts/validation_human/seaad_deg_config.yml`](../../scripts/validation_human/seaad_deg_config.yml)
- [`scripts/validation_human/seaad_phase18_validation_config.yml`](../../scripts/validation_human/seaad_phase18_validation_config.yml)
- [`config/phase12_kda.yml`](../../config/phase12_kda.yml)
- [`config/phase18_key_driver_selection.yml`](../../config/phase18_key_driver_selection.yml)
