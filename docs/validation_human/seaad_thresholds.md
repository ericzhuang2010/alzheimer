# SEA-AD post-hoc exploratory threshold amendment

**Status:** selection-only amendment executed; `validated_complete`
**Initial amendment date:** 2026-08-22
**Selection update date:** 2026-08-23
**Latest execution date:** 2026-08-23 (America/New_York)
**Scope:** SEA-AD only

## Purpose and interpretation

This record amends the SEA-AD analysis contract for one explicitly **post-hoc
exploratory** rerun. It does not redefine the completed primary SEA-AD result,
and it does not change or rerun the frozen ROSMAP Phase 18 analysis. Results
from this tier are labeled exploratory and use a distinct result-tier
identifier. Per the execution request, they replace the former SEA-AD files in
the canonical validation output directory; no parallel copy of the former
SEA-AD result was retained.

## Current executed SEA-AD gates

The 2026-08-23 partial rerun restored the original aggregate coverage and
aggregate-q cutoffs while retaining the 2026-08-22 donor and DEG-query
amendments:

| Stage | Original SEA-AD gate | 2026-08-22 tier | Current 2026-08-23 tier |
|---|---:|---:|---:|
| Contrast eligibility | At least 5 donors/arm | At least 3 donors/arm | **At least 3 donors/arm** |
| DEG query membership | FDR `< 0.05` and `abs(log2FC) > log2(1.3)` | FDR `< 0.05` only | **FDR `< 0.05` only** |
| Aggregate coverage | Coverage `>= 0.80` | Coverage `>= 0.50` | **Coverage `>= 0.80`** |
| Aggregate significance | Aggregate `q <= 0.05` | Aggregate `q <= 0.10` | **Aggregate `q <= 0.05`** |

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
  `posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05`
- Canonical output:
  `results/validation_human/10_seaad_kda_rediscovery/`
- Code revision recorded by the outputs:
  `fc80751b41cb7028cb55d4bd25773e31675bff13`
- VH10 configuration SHA-256:
  `e98c2e70727e1dc748307b7f818f57f375360355655e589191a04b651a4b46ee`

| Stage | Validated amended result |
|---|---:|
| Fine contrasts meeting the 3-donor support gate | 382 |
| Model-feasible/completed fine contrasts | 381 |
| Completed signed source directions | 762 |
| Active KDA calls (effective query size >=3) | 42 |
| Calls with significant KDA returns | 27 |
| Calls without significant KDA returns | 15 |
| Passing/displayed SEA-AD candidate units | 11 |
| Unique selected SEA-AD genes | 9 |
| Frozen ROSMAP units testable in SEA-AD | 36 of 47 |
| Strict shared network-gene-class units | 6 |
| Unique shared genes | 6 |

The active-call distribution is 20 AD-up and 22 AD-down calls: Astrocytes
1/0, Excitatory neurons 10/10, Inhibitory neurons 6/10, Microglia 1/0,
Oligodendrocytes 2/2, and no active calls in OPCs or Vasculature.

The selection-only rerun reused the unchanged 42 KDA calls and their 201
significant R return rows. It removed three formerly selected units because
their recomputed aggregate q remained above 0.05: `MT-ND1` in Inhibitory
neurons (q=0.0867), `RPL30` in Inhibitory neurons (q=0.0850), and `KANSL1L`
in Oligodendrocytes (q=0.0902). All 11 retained units have coverage 1.0, so
the restored 0.80 coverage gate removed no formerly selected unit.

## ROSMAP remained frozen

ROSMAP candidate construction, KDA run scope, minimum effective query size,
coverage threshold, support rule, aggregate-q threshold, selected units, and
ranks remained exactly as frozen in Phase 18. The current SEA-AD coverage and
aggregate-q gates now match the frozen ROSMAP values, although other cohort and
query-construction rules remain distinct. The overlap phase replayed the
161 frozen ROSMAP runs and reproduced 78 passing and 47 selected ROSMAP units
before comparison.

The governing source records are:

- [`scripts/validation_human/seaad_deg_config.yml`](../../scripts/validation_human/seaad_deg_config.yml)
- [`scripts/validation_human/seaad_phase18_validation_config.yml`](../../scripts/validation_human/seaad_phase18_validation_config.yml)
- [`config/phase12_kda.yml`](../../config/phase12_kda.yml)
- [`config/phase18_key_driver_selection.yml`](../../config/phase18_key_driver_selection.yml)
