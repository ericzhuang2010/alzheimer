# Phase 19 rerun plan: genetic support for the simple-aggregation drivers

**Status:** planned; not executed
**Date:** 2026-08-29
**Candidate scope:** all 433 non-MT driver genes from
`results/minerva_production/20_sex_apoe_kda_simple_aggr` (689 gene × category
units; category-aggregate SHA-256
`4e0ab4204ba837ec7ca0d5920e27f2557849f6acbc0d92189d5737193eab8ebd`)
**Companion files:**
[`missing_input_manifest.tsv`](missing_input_manifest.tsv),
[`missing_input_paths.txt`](missing_input_paths.txt)

## 1. Purpose and relationship to the completed Phase 19

The completed Phase 19 workstreams screened the 25 genes of the earlier
Phase 18 top-five candidate freeze. That freeze has been superseded: the
authoritative ROSMAP driver list is now the returned-only simple aggregation
(433 non-MT genes across 32 sex/APOE × broad-cell categories). Only 15 of the
433 current drivers have any genetic screening result, and those 15 were
inherited from the old freeze rather than selected from the current list.

This plan reruns the genetic-support pipeline against a new candidate freeze
drawn from the simple aggregation. The five completed 2026-08 result bundles
remain immutable; every rerun output goes to new `19b_*` result directories.

All execution rules of the [overall plan](../overall_plan.md) apply unchanged
(freeze before looking, separate result roots, no-signal vs not-assessable
distinction, harmonization and LD requirements, ROSMAP-overlap audits, local
bounded acquisitions, unique-gene counting). One rule is added:

11. At 433 candidate windows (~2 Mb each), a nearby genome-wide-significant
    GWAS variant is expected for many genes by proximity alone. Regional
    signals are recorded as annotation and gating information only; they must
    never be reported as gene-level support without a downstream gene-level
    route (MAGMA, QTL signal, or colocalization).

## 2. WS0 — candidate freeze (new; run first; fully local)

New script `scripts/19b_freeze_simple_aggr_candidates.py`:

- **Input:** `simple_category_gene_aggregates.tsv` from
  `20_sex_apoe_kda_simple_aggr`, filtered to `case_id = non_mt_driver`,
  `is_core_mito = FALSE`; verify the registered SHA-256 above and the source
  bundle's `validated`/zero-failed-check status before freezing.
- **Units:** one candidate row per unique gene (433 expected) plus a companion
  context table with the 689 gene × category rows (sex/APOE group, broad
  network, returned-call count, exploratory score, display rank).
- **Gene mapping:** GENCODE v44 basic (GRCh38) + HGNC 2026-06-05, exactly as
  Tier 1; gene body ± 1 Mb windows. Both references are already local. Any
  symbol without a unique mapping is recorded with a terminal
  `symbol_mapping_failed` status, not silently dropped (the list includes
  non-coding symbols such as `LIFR-AS1`, so expect a small number).
- **Priority tiers, frozen before any genetic lookup:**
  - **P1 (deep workup):** the 35 genes that also return in the SEA-AD
    validation aggregation (includes the four unscreened cross-cohort leads
    WDR82, HGSNAT, TTC8, BEX3, and previously screened genes such as RPS15).
  - **P2 (standard workup):** genes in a category top-five display or with
    ≥ 2 categories or ≥ 3 returned calls (≈ 140 genes; exact count fixed at
    freeze time).
  - **P3 (batch annotation only):** the remaining one-off genes (~260).
- **Output:** `results/minerva_production/19b_genetic_support_candidates/`
  with manifest/loci/checks/status files following the
  `genetic_support_candidate_manifest.tsv` and
  `genetic_support_candidate_loci.tsv` schemas, so downstream stages can be
  reused with minimal change.

## 3. Workstreams, in execution order

| WS | Analysis | Genes | Inputs | Where it can run |
|---|---|---|---|---|
| WS1 | Tier-1-style public summary screen (FunGen fine-mapping, xQTL, TWAS lists) | all 433 | all present locally | this Mac, now |
| WS2 | Regional clinical-AD GWAS screen (min P, lead variant per window) | all 433 | Bellenguez `GCST90027158` full GRCh38 sumstats (755 MB) — **missing locally** | Mac after transfer, or other machine |
| WS3 | MAGMA gene-based tests: clinical AD + 3 CSF biomarkers | all 433 | CSF GWAS + FUMA `g1000_eur` + MAGMA v1.10 (~9 GB) — **missing locally**; the MAGMA binary is a **Linux** build | other machine (Linux) |
| WS4 | QTL coverage + signal gates (NG00184 fine-mapping; eQTL Catalogue r7 panels) | P1 + P2 only | NG00184 tars + eQTL Catalogue models (~6 GB) — **missing locally** | either, after transfer |
| WS5 | Colocalization / same-variant tests | only routes with both signals and complete models + matched LD | same as WS4 | either |

Design changes relative to the 2026-08 execution:

- **Thresholds are re-frozen for the new scale.** MAGMA candidate correction
  becomes `0.05 / (433 × 4 traits)` (or per-trait `0.05 / 433`; fix one rule in
  the WS3 config before running). QTL signal gates remain gene-specific
  regional Bonferroni as in the recovery workstream.
- **Regional results are annotation, not grades** (rule 11). The Tier-1 grade
  vocabulary (`strong`/`moderate`/`weak`/`none_found`/`not_assessable`) is kept
  for gene-level routes only.
- **Depth follows the frozen priority tiers.** WS4/WS5 effort is limited to
  P1 + P2; P3 genes stop after WS1–WS3 batch annotation.
- **mtDNA and mitochondrial-protein drivers are out of scope** — the candidate
  universe is the non-MT list by construction.
- **Known repairs are folded in:** regenerate the two invalid zero-row gzip
  outputs with a fixed writer; enumerate the four NG00130.v2 APOE pQTL files in
  the input inventory (see discovery command below); reconcile the encoded
  Bellenguez case/control counts before any fine-mapping use; correct the
  `QTD000579` eQTL/sQTL modality labels; keep all documented paths
  repository-relative.

Expected new result roots (old bundles untouched):

```text
results/minerva_production/19b_genetic_support_candidates/
results/minerva_production/19b_genetic_support_tier1/
results/minerva_production/19b_genetic_support_regional/
results/minerva_production/19b_genetic_support_magma/
results/minerva_production/19b_genetic_support_qtl/
results/minerva_production/19b_genetic_support_coloc/
```

## 4. Input availability audit (this machine)

Verified on 2026-08-29 against the five published input inventories:

| Input group | Files | Size | Local status |
|---|---:|---:|---|
| Tier 1 sources (FunGen snapshot, GENCODE v44, HGNC) | 9 | ~0.12 GB | **all present** — WS1 can run now |
| Tier 2 regional (Bellenguez GWAS, NG00184 fine-mapping tars, tier2 source copies) | 41 | 2.04 GB | missing |
| Tier 2 recovery (eQTL Catalogue r7 metadata, SuSiE credible sets/LBF, LeafCutter, NG00067 registry, extracted regions) | 33 | 2.97 GB | missing |
| Endophenotype (3 CSF GWAS raw + harmonized + indexes, MAGMA gene locations, FUMA `g1000_eur`, MAGMA binary, NG00184 archives) | 29 | 9.13 GB | missing |
| OPC/RPS15 (extracted NG00184 chromosome-19 bundle) | 1 | 0.21 GB | missing |
| **Total missing** | **104** | **14.34 GB** | see manifest |

The complete list with recorded sizes and SHA-256 hashes is in
[`missing_input_manifest.tsv`](missing_input_manifest.tsv); the bare path list
for transfer tools is [`missing_input_paths.txt`](missing_input_paths.txt).

Two additional gaps that the manifest cannot cover:

- The four **NG00130.v2 APOE CSF pQTL files** were used by the endophenotype
  workstream but never enumerated in its input inventory. They must be located
  on the other machine (discovery command below) and added to the manifest
  before the WS3 follow-up is reproducible.
- `external_tools/magma_v1.10/magma` is a **Linux executable**; it transfers
  for archival completeness but cannot run on this Mac (macOS/ARM). Plan
  WS3 on the other machine, or obtain a macOS MAGMA build separately.

## 5. Commands to run on the other machine

All commands assume the repository checkout root on the other machine
(`cd /path/to/alzheimer` first). Pull the current repo state before starting so
the manifest files exist there (`git pull`, or copy the two manifest files
over manually).

### 5.1 Verify which required inputs exist and match their recorded hashes

```bash
manifest=docs/phase_19_genetic_support/simple_aggr_rerun/missing_input_manifest.tsv

# presence check (fast)
awk -F'\t' 'NR>1 {print $1}' "$manifest" | while IFS= read -r p; do
  [ -e "$p" ] || echo "ABSENT: $p"
done | tee /tmp/p19_absent.txt
echo "absent_count=$(wc -l < /tmp/p19_absent.txt)"

# integrity check (~14 GB of hashing; several minutes)
awk -F'\t' 'NR>1 {print $3"  "$1}' "$manifest" | shasum -a 256 -c - \
  | tee /tmp/p19_hash_report.txt
echo "ok=$(grep -c ': OK$' /tmp/p19_hash_report.txt)  failed=$(grep -c 'FAILED' /tmp/p19_hash_report.txt)"
```

If `shasum` is unavailable on that Linux host, replace the second block with
`sha256sum -c`  (same input format).

### 5.2 Locate the uninventoried NG00130 APOE pQTL files

```bash
find . -iname '*NG00130*' 2>/dev/null
for acc in GCST90424891 GCST90425531 GCST90425532 GCST90426314; do
  find . -iname "*${acc}*" 2>/dev/null
done
# record whatever this finds (path, size, sha256) and send the listing back:
# sha256sum <each found file>
```

### 5.3 Option A — copy the missing inputs to this Mac (~14.3 GB)

Run from the repository root on the other machine (relative paths are
preserved; the Mac-side destination is the repo root):

```bash
rsync -av --files-from=docs/phase_19_genetic_support/simple_aggr_rerun/missing_input_paths.txt \
  . rzhuang@<this-mac-hostname>:/Users/rzhuang/Documents/VscodeProjects/alzheimer/
```

Alternatively pull from the Mac side (run on this Mac):

```bash
rsync -av --files-from=docs/phase_19_genetic_support/simple_aggr_rerun/missing_input_paths.txt \
  <user>@<other-machine>:/path/to/alzheimer/ .
```

After transfer, rerun the hash check of §5.1 on this Mac before unfreezing any
workstream.

### 5.4 Option B — run the heavy workstreams on the other machine instead

Copying is optional: WS2–WS5 can run where the data already live. In that
case, on the other machine:

```bash
git pull                       # bring over the WS0/19b scripts once written
# run WS0 freeze + WS2/WS3/WS4/WS5 stage scripts there
```

and copy back only the small validated `19b_*` result bundles:

```bash
rsync -av results/minerva_production/19b_genetic_support_* \
  rzhuang@<this-mac-hostname>:/Users/rzhuang/Documents/VscodeProjects/alzheimer/results/minerva_production/
```

WS3 (MAGMA) must run on the Linux machine regardless, unless a macOS MAGMA
build is installed here. Recommended split: run WS0 and WS1 on this Mac now;
transfer the 2.04 GB tier-2-regional group for WS2 if local execution is
preferred; leave WS3 on Linux; decide WS4/WS5 placement by whichever machine
holds the QTL archives when the P1/P2 routes are fixed.

## 6. Order of operations

1. **Now, this Mac:** write and run WS0 (freeze + tiers) and WS1 (Tier-1-style
   screen for all 433) — no missing inputs.
2. **Other machine:** run §5.1 verification and §5.2 NG00130 discovery; report
   results.
3. Choose Option A or B per workstream; complete WS2 (regional annotation) and
   WS3 (MAGMA, Linux).
4. Fix the P1/P2 QTL route table from WS1–WS3 outcomes; run WS4, then WS5 only
   where complete models and matched LD exist.
5. Consolidate into a `19b` results summary mirroring
   [`phase19_genetic_support_results_summary.md`](../phase19_genetic_support_results_summary.md),
   reporting unique supported genes separately from route counts.

## 7. What this rerun can and cannot change

Realistic expectations, given the completed screen's bottlenecks: WS1–WS3
extend coverage from 15 to all 433 drivers cheaply and may surface new
regional or gene-based leads (e.g., for WDR82, HGSNAT, TTC8, BEX3). WS5
remains limited by the same public data gaps that blocked APOE and RPS15
colocalization in August — complete fitted multi-signal QTL models and
source-matched LD are still the rate-limiting inputs, and no amount of
candidate-list updating changes that.
