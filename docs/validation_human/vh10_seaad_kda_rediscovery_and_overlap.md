# VH10 SEA-AD Fine-Supertype KDA Rediscovery and ROSMAP Overlap

> **PARTIALLY DEPRECATED (2026-08-29).** The gated candidate selection
> (`10c_seaad_selection`) and its ROSMAP overlap (`10d_overlap`) described
> here are superseded by the authoritative returned-only simple aggregation in
> `results/validation_human/11_sex_apoe_kda_simple_aggr`
> (`scripts/validation_human/11_seaad_sex_apoe_kda_simple_aggr.py`). The VH10
> run universe, `10a_inputs`, and the 42 validated KDA calls in `10b_kda`
> remain the frozen, non-deprecated inputs of that aggregation. The current
> cross-cohort overlap analysis is in
> `docs/validation_human/rosmap_seaad_simple_aggr_driver_analysis.md`.

**Status:** selection-only partial rerun executed; `validated_complete` on
2026-08-23 (America/New_York)
**Code root:** `scripts/validation_human/`
**Result root:** `results/validation_human/10_seaad_kda_rediscovery/`
**ROSMAP reference:** Phase 18 candidate units frozen by VH09
**Execution:** completed locally from the checksum-frozen amended VH08 release;
no H5AD or pseudobulk matrix was read
**Current scope:** one post-hoc exploratory SEA-AD tier using at least three
effective query genes

## Current post-hoc exploratory protocol — executed

This amendment was made after inspection of the completed primary analysis and
is reported as **post-hoc exploratory**, not prespecified or confirmatory. The
executed SEA-AD tier used the following rules together:

| Component | Executed SEA-AD rule |
|---|---|
| Upstream DEG support | At least **3 donors per disease arm**, replacing five |
| Active query membership | Signed core-MitoCarta genes with within-contrast **`FDR < 0.05` only**; the `abs(logFC) > log2(1.3)` gate was not applied |
| Runnable query | At least **3 effective genes** after network intersection, unchanged |
| Candidate selection | Coverage **at least 0.80** and aggregate ACAT BH **q at most 0.05**; other gates and ranking rules were unchanged |

The complete 1,548-slot structural grid was retained. The amended upstream
release contains 381 completed fine contrasts and 762 completed signed
directions. VH10 derived 42 active calls from those artifacts: 21 small-query
calls and 21 Phase-18-sized calls.

| Stage | Validated amended result |
|---|---:|
| `call_key_drivers()` calls with significant returns | 27 |
| Calls with no significant return | 15 |
| Significant R return rows | 201 |
| Complete explicit gene-by-run rows | 10,912 |
| Complete candidate/run evidence rows | 366,852 |
| SEA-AD candidate units | 38,788 |
| SEA-AD units passing/displayed | 11 |
| Unique selected SEA-AD genes | 9 |
| Frozen ROSMAP top-five units | 47 |
| ROSMAP units testable in SEA-AD | 36 |
| Strict shared network-gene-class units | 6 |

The 2026-08-23 partial rerun reused the unchanged 42 calls and 201 significant
R returns; it regenerated query-tier metadata, KDA reconstruction tables,
SEA-AD selection, and ROSMAP overlap without rerunning DEG models or
`call_key_drivers()`. The stricter q gate removed `MT-ND1`, `RPL30`, and
`KANSL1L`; the coverage gate removed none of the formerly selected units.

ROSMAP remained the unchanged, read-only VH09-frozen reference. Its Phase 18
minimum-ten rule, 0.80 coverage threshold, 0.05 aggregate-q threshold,
candidate identities, and ranks were not changed. The overlap phase replayed
all 161 frozen ROSMAP runs and exactly reproduced 78 passing and 47 selected
units before comparison.

The 2026-08-20 SEA-AD execution below is retained only as a historical,
superseded record.
