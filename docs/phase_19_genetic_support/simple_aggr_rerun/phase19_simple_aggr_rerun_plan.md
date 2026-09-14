# Phase 19 rerun plan: genetic support for the simple-aggregation drivers

**Status:** WS0–WS5 completed and validated; Phase 19b is authoritative
**Updated:** 2026-09-14
**Candidate scope:** all 228 non-MT returned drivers from
`results/minerva_production/20_sex_apoe_kda_combo` (381 gene × sex/APOE ×
broad-network units; category-aggregate SHA-256
`ba506a24d5fc925d732a7a9537b5c0201bf415b6848096068807db744e5498fd`)
**Companion files:**
[`missing_input_manifest.tsv`](missing_input_manifest.tsv),
[`missing_input_paths.txt`](missing_input_paths.txt)

## 1. Purpose and relationship to the completed Phase 19

The completed original Phase 19 workstreams screened the 25 genes of the
earlier Phase 18 top-five candidate freeze. That freeze is historical. The
authoritative ROSMAP driver list is now the Phase 20 direction-combined,
returned-only aggregation: 228 non-MT genes across 381 units and 29 populated
sex/APOE × broad-cell categories.

The 19b pipeline reruns genetic support against the new candidate freeze. The
original 2026-08 Phase 19 result bundles are historical and now carry the
suffix ` (deprecated)`; current rerun outputs go to the separate `19b_*`
result directories. See the
[`Phase 19b result summary`](phase19b_genetic_support_results_summary.md) for
the completed result.

All execution rules of the [overall plan](../overall_plan.md) apply unchanged
(freeze before looking, separate result roots, no-signal vs not-assessable
distinction, harmonization and LD requirements, ROSMAP-overlap audits, local
bounded acquisitions, unique-gene counting). One rule is added:

11. At 228 candidate windows (~2 Mb each), a nearby genome-wide-significant
    GWAS variant is expected for many genes by proximity alone. Regional
    signals are recorded as annotation and gating information only; they must
    never be reported as gene-level support without a downstream gene-level
    route (MAGMA, QTL signal, or colocalization).

## 2. WS0 — candidate freeze (new; run first; fully local)

Implementation: `scripts/19b_genetic_support_simple_aggr.py`.

- **Input:** `combo_key_drivers_by_category.tsv` from
  `20_sex_apoe_kda_combo`, filtered to `is_core_mito = FALSE`; verify the
  registered SHA-256 above before freezing.
- **Units:** one candidate row per unique gene (228) plus a companion
  context table with the 381 gene × category rows (sex/APOE group, broad
  network, returned-call count, exploratory score, display rank).
- **Gene mapping:** GENCODE v44 basic (GRCh38) + HGNC 2026-06-05, exactly as
  Tier 1; gene body ± 1 Mb windows. Both references are already local. Any
  symbol without a unique mapping is recorded with a terminal
  `symbol_mapping_failed` status, not silently dropped (the list includes
  non-coding symbols such as `LIFR-AS1`, so expect a small number).
- **Priority tiers, frozen before any genetic lookup:**
  - **P1 (deep workup):** the three genes also returned by the matched SEA-AD
    combo workflow: `LAGE3`, `MIPOL1`, and `PAPOLA`.
  - **P2 (standard workup):** 113 genes in a category top-five display or
    with ≥ 2 categories or ≥ 3 returned calls.
  - **P3 (batch annotation only):** the remaining 112 one-off genes.
- **Output:** `results/minerva_production/19b_genetic_support_candidates/`
  with manifest/loci/checks/status files following the
  `genetic_support_candidate_manifest.tsv` and
  `genetic_support_candidate_loci.tsv` schemas, so downstream stages can be
  reused with minimal change.

## 3. Workstreams, in execution order

| WS | Analysis | Genes | Inputs | Where it can run |
|---|---|---|---|---|
| WS1 | Tier-1-style public summary screen (FunGen fine-mapping, xQTL, TWAS lists) | all 228 | complete locally | this Mac |
| WS2 | Regional clinical-AD and CSF GWAS screen (min P, lead variant per window) | all 226 mapped genes × four traits; X routes retain structural source status | four official GWAS files, checksum registered | completed locally |
| WS3 | MAGMA gene-based tests: clinical AD + 3 CSF biomarkers | all 228, with explicit reference-model gaps | official MAGMA v1.10 Mac build and `g1000_eur`; checksum-validated CSF reuse | completed locally |
| WS4 | QTL coverage + signal gates (NG00184 fine-mapping) | P1 + P2 only | three official fine-mapping archives, exact registered MD5 | completed locally |
| WS5 | Colocalization / same-variant tests | signal-positive routes gated for complete models + compatible LD | released tables are incomplete model summaries | completed as a terminal assessability audit; no valid H0–H4 run |

Design changes relative to the 2026-08 execution:

- **Thresholds are re-frozen for the new scale.** MAGMA candidate correction
  is `0.05 / (228 × 4 traits) = 5.48245614e-5`. QTL signal gates remain gene-specific
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

## 4. Pre-execution input availability audit (superseded)

This table records the 2026-08-29 planning state. On 2026-09-14 the four GWAS
files, official MAGMA v1.10 macOS distribution and `g1000_eur` reference, and
the three NG00184 fine-mapping archives needed by the frozen Phase 19b scope
were acquired and checksum-validated. The full 14.34 GB contingency transfer
was therefore unnecessary.

Verified on 2026-08-29 against the five published input inventories:

| Input group | Files | Size | Local status |
|---|---:|---:|---|
| Tier 1 sources (FunGen snapshot, GENCODE v44, HGNC) | 9 | ~0.12 GB | **all present; WS1 completed** |
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

## 5. Archived contingency commands (not needed for the completed run)

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

## 6. Completed order of operations

1. WS0 froze 228 genes/381 contexts and mapped 226 genes.
2. WS1 screened all 228 genes against the frozen FunGen summary snapshot.
3. WS2 streamed all four current GWAS sources across every mapped window.
4. WS3 fixed the four-trait threshold, ran clinical-AD MAGMA with v1.10, and
   reused the three unchanged full-genome CSF scans only after exact checksum
   validation.
5. WS4 streamed the three checksum-validated NG00184 archives for the frozen
   116-gene/269-context P1+P2 scope.
6. WS5 enumerated every QTL × GWAS-trait decision and produced no H0–H4 values
   where compatible fitted models and LD/full statistics were absent.
7. Results were consolidated in
   [`phase19b_genetic_support_results_summary.md`](phase19b_genetic_support_results_summary.md),
   with unique genes kept separate from context and route counts.

## 7. What this rerun can and cannot change

WS1 covers all 228 current genes and reports 2 strong, 1 moderate, 9 weak, and
216 `none_found` public-summary grades. WS2 is a current-source scan rather
than a cache-based partial result. WS3 tested 832 of 912 candidate-trait rows;
six rows across APOE, INTS8, and PLCG2 passed the frozen four-trait correction.
WS4 extracted 69,308 released fine-mapping rows and covers all 538
prespecified P1/P2 context-modality routes; 269 routes across 90 genes carry a
source-significant QTL signal,
while preserving the fact that the public QTL data are not sex/APOE-stratified.
WS5 gated 2,152 QTL-by-trait decisions. Forty-seven passed both signal gates,
but WS5 is terminally `not_assessable` for those routes: released PIP/credible-set
rows are not complete fitted multi-signal models, and compatible source-matched
LD/full QTL statistics are absent. Consequently, model-incompatible routes are
`not_assessable`, not negative colocalizations.
