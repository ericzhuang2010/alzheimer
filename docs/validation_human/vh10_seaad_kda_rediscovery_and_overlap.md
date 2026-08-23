# VH10 SEA-AD Fine-Supertype KDA Rediscovery and ROSMAP Overlap

**Status:** executed; `validated_complete` on 2026-08-20
**Code root:** `scripts/validation_human/`
**Result root:** `results/validation_human/10_seaad_kda_rediscovery/`
**ROSMAP reference:** Phase 18 candidate units frozen by VH09
**Execution:** completed locally; no H5AD or pseudobulk matrix was read
**Current scope:** one SEA-AD primary analysis using at least three effective
query genes; all sensitivity analyses are deferred and optional

**Amendment status:** a dated post-hoc exploratory SEA-AD rerun was authorized
on 2026-08-22 and is pending. The 2026-08-20 VH10 execution remains a
historical record but is superseded for amended SEA-AD and overlap conclusions.

## 2026-08-22 post-hoc exploratory protocol amendment — pending rerun

This amendment was made after inspection of the completed analysis and must be
reported as **post-hoc exploratory**, not prespecified or confirmatory. The
amended SEA-AD tier will use the following rules together:

| Component | Amended SEA-AD rule |
|---|---|
| Upstream DEG support | At least **3 donors per disease arm**, replacing five |
| Active query membership | Signed core-MitoCarta genes with within-contrast **`FDR < 0.05` only**; the `abs(logFC) > log2(1.3)` gate is removed |
| Runnable query | At least **3 effective genes** after network intersection, unchanged |
| Candidate selection | Coverage **at least 0.50** and aggregate ACAT BH **q at most 0.10**, replacing 0.80 and 0.05; other gates and ranking rules are unchanged |

The 1.3-fold Phase 18 rule is retained only as an auxiliary/reference summary,
not as active SEA-AD query membership. The complete 1,548-slot structural grid
is retained, but eligibility, completed directions, runnable queries, KDA
returns, candidate lists, and overlap must all be recomputed from the amended
upstream release.

ROSMAP remains the unchanged, read-only VH09-frozen reference. Its Phase 18
minimum-ten rule, 0.80 coverage threshold, 0.05 aggregate-q threshold,
candidate identities, and ranks are not changed or recomputed. Thus the
amended comparison deliberately applies cohort-specific thresholds: the new
SEA-AD exploratory rules above versus the original frozen ROSMAP rules.

All SEA-AD-derived and cross-cohort counts from the 2026-08-20 execution below
are **historical and superseded for the amended analysis**, including 520
completed directions, 42 active queries, 13 selected SEA-AD units, and six
strict overlaps. They are retained without alteration for provenance and are
not forecasts or acceptance targets for the rerun. Replacement counts are
pending validated rerun. ROSMAP-only frozen counts, including the 47 frozen
top-five units, remain valid.

## Historical execution result (superseded for SEA-AD; 2026-08-20)

VH10 completed locally and passed every query, network, R/Python reconstruction,
selection-freeze, Phase 18 conformance, and overlap check. The executed primary
tier produced:

| Stage | Executed result |
|---|---:|
| Structural SEA-AD direction slots | 1,548 |
| Completed source DEG directions | 520 |
| Active queries with at least 3 effective genes | 42 |
| `call_key_drivers()` calls with significant returns | 29 |
| `call_key_drivers()` calls with no significant return | 13 |
| Significant R return rows | 208 |
| Complete explicit gene-by-run rows after reconstruction | 9,596 |
| Complete candidate/run evidence rows | 366,852 |
| SEA-AD candidate units | 38,788 |
| SEA-AD units passing all candidate gates | 13 |
| SEA-AD top-five units | 13 |
| Unique genes among SEA-AD top-five units | 11 |
| Frozen ROSMAP top-five units | 47 |
| ROSMAP units testable in the common SEA-AD universe | 36 |
| Strict shared network-gene-class top-five units | 6 |
| Unique shared genes | 6 |

The six strict rediscoveries are `MT-CO2` and `MT-CYB` in Excitatory
neurons, plus `MT-CO2`, `MT-CO3`, `MT-CYB`, and `MT-ND5` in Inhibitory
neurons. No deferred sensitivity analysis was executed.

## 1. Decision and end goal

VH10 performed a Phase 18-shaped analysis with the executed SEA-AD fine DEG
results:

```text
SEA-AD Supertype x sex/APOE x DEG direction
                         |
                         v
              mitochondrial DEG query
                         |
                         v
          KDA on the matching frozen broad network
                         |
                         v
       Phase 18-compatible cross-run candidate selection
                         |
                         v
          independently frozen SEA-AD top-driver lists
                         |
                         v
          overlap with VH09-frozen ROSMAP Phase 18 units
```

The SEA-AD KDA query is a signed set of mitochondrial DEG genes. It is **not** a
list of the 47 ROSMAP candidates. All assessable network genes are considered
as possible SEA-AD key drivers. ROSMAP candidate identities are read only after
the SEA-AD candidate lists are checksum-frozen.

The primary SEA-AD analysis unit mirrors Phase 18 as closely as the taxonomy
allows:

```text
SEA-AD supertype + sex/APOE group + AD_up_mito or AD_down_mito
```

SEA-AD supertypes are not relabeled as ROSMAP fine cell types. Both cohorts are
aggregated only at the shared broad-network level during candidate selection
and overlap.

## 2. What the completed VH08 DEG results actually support

VH08 created the complete fine structural grid:

```text
129 supertypes x 6 sex/APOE groups x 2 directions = 1,548 direction slots
```

The 1,548 slots are not 1,548 runnable KDA calls. Under the single active
Phase 18-parity DEG query rule and its at-least-three-gene run threshold, the
executed attrition is:

| Stage | Direction slots | Meaning |
|---|---:|---|
| Structural fine grid | 1,548 | Every supertype, group, and signed direction |
| Source DEG contrast not estimable | 1,028 | 514 non-estimable contrasts x 2 directions |
| Completed DEG and ready for query construction | 520 | 260 completed contrasts x 2 directions |
| Effective query size 0 | 462 | No Phase 18-parity query gene remains in the induced network |
| Effective query size 1-2 | 16 | Below the active three-gene threshold |
| Effective query size 3-9 | 21 | Active KDA calls labeled `small_query` |
| Effective query size at least 10 | 21 | Active KDA calls labeled `phase18_sized` |
| **Effective query size at least 3** | **42** | **All active primary KDA calls** |

Only `F_e33`, `F_e4`, and `M_e33` produced completed fine contrasts. The
other three groups remain in the structural manifest with their original
non-estimable reasons; they are not silently removed.

A read-only replay of the actual DEG shards, frozen current-symbol/core-Mito
annotations, and induced network backgrounds produced the following active
`phase18_parity_query` counts:

| Broad network | Completed source directions | Active up calls | Active down calls |
|---|---:|---:|---:|
| Astrocytes | 20 | 1 | 0 |
| Excitatory neurons | 176 | 10 | 10 |
| Inhibitory neurons | 284 | 6 | 10 |
| Microglia | 6 | 1 | 0 |
| OPCs | 6 | 0 | 0 |
| Oligodendrocytes | 18 | 2 | 2 |
| Vasculature cells | 10 | 0 | 0 |
| **Total** | **520** | **20** | **22** |

Thus the active analysis has runs in Astrocytes, Excitatory neurons,
Inhibitory neurons, Microglia, and Oligodendrocytes. OPCs and Vasculature remain
structurally represented but are `not_testable_no_included_runs` under the
current three-gene threshold.

These are audited planning values, not hard-coded analytical inputs. VH10A must
recompute them from checksum-verified VH08 rows and frozen networks. A mismatch
is blocking.

## 3. Current primary analysis and deferred optional analyses

The current VH10 execution has exactly one query rule, one run scope, and one
result tier:

| Component | Active value |
|---|---|
| Query rule | `phase18_parity_query`: core MitoCarta, within-contrast `FDR < 0.05`, `abs(logFC) > log2(1.3)`, and the correct AD-up or AD-down sign |
| Run scope | `min3_all`: at least 3 effective query genes after network intersection |
| Result tier | `phase18_parity_query__min3_all` |

This tier retains the Phase 18 DEG query-membership rule while using the
prespecified three-gene minimum appropriate for the smaller SEA-AD query sets.
It is the only tier that VH10 will execute, select, freeze, compare with ROSMAP,
or require for completion now.

The following analyses are explicitly optional and deferred. They must not run
as part of the current VH10 execution:

| Deferred analysis | Change from the active primary analysis |
|---|---|
| Minimum-ten Phase 18-sized analysis | Restrict aggregation to effective queries with at least 10 genes |
| FDR-only query analysis | Remove the `abs(logFC) > log2(1.3)` gate while retaining the active three-gene minimum |
| Combined FDR-only/minimum-ten analysis | Remove the effect-size gate and restrict aggregation to queries with at least 10 genes |
| Leave-one-supertype-out stability | Recompute aggregation after removing one supertype at a time |
| Missing-as-one ACAT | Replace absent-background missing evidence with `p = 1` |
| Three-donor DEG/KDA analysis | Use a separately generated upstream DEG sensitivity release |

If a deferred analysis is authorized later, it must receive a separate tier ID,
result namespace, status, artifacts, and overlap report. It must not overwrite,
alter, or be pooled with the active primary result.

The seven pooled broad DEG contrasts and 42 broad stratified support contrasts
are not KDA selection inputs. They remain biological DEG anchors only. Mixing
them with the fine runs would change the recurrence and coverage denominator
and would no longer resemble Phase 18.

## 4. Independence and shared assets

SEA-AD contributes independent donors, counts, DEG estimates, tested-gene sets,
and signed mitochondrial queries. The following assets are deliberately
shared with ROSMAP Phase 18:

- the seven matching broad-cell Bayesian network files;
- `scripts/NetWeaver/fKDA.R` and `call_key_drivers()`;
- the current Phase 18 core-MitoCarta and two-driver-class annotation;
- explicit-candidate reconstruction and self-exclusion behavior;
- within-run BH, cross-run coverage, ACAT, aggregate BH, candidate gates, and
  ranking rules.

The result is an independent-cohort rediscovery analysis on a shared frozen
network scaffold, not a de novo SEA-AD network reconstruction.

The selection authority is the current two-class implementation:

- `config/phase18_key_driver_selection.yml`;
- `scripts/18_key_driver_selection.py`;
- `docs/phase_18_key_driver_selection/key_driver_selection_process.md`.

Historical three-case outputs are obsolete. Phase 12 supplies technical
network/background/KDA assets, not candidate identities or selection rules.

## 5. Inputs

### SEA-AD inputs

| Input | Purpose |
|---|---|
| `results/validation_human/08_deg/status.tsv` | Require VH08 `validated_complete` |
| `results/validation_human/08_deg/artifacts.tsv` | Verify all consumed VH08 files by size and SHA-256 |
| `results/validation_human/08_deg/query_handoff/fine_direction_manifest.tsv` | Preserve all 1,548 structural direction slots and source terminal states |
| `results/validation_human/08_deg/query_handoff/fine_query_input_index.tsv` | Locate and verify all 260 completed fine DEG result shards |
| `results/validation_human/08_deg/query_handoff/fine_direction_deg_summary.tsv` | Reproduce pre-network attrition as QC only |
| `results/validation_human/08_deg/fine_supertype_phase18_parity/tested/*.tsv.gz` | Full tested genome-wide DEG rows used to construct queries/backgrounds |
| `results/validation_human/03_genes/gene_annotation_master.tsv` | Frozen current-symbol and Phase 18 core-Mito mapping |
| `results/validation_human/04_supertype_manifest/supertype_to_broad_network.tsv` | Exact supertype-to-network mapping |
| `results/validation_human/07_contrasts/fine_contrast_manifest.tsv` | Donor support, eligibility, group, and design provenance |

### Shared KDA and Phase 18 conformance inputs

| Input | Purpose |
|---|---|
| `config/phase12_kda.yml` | Frozen network paths/checksums and base KDA parameters |
| Seven `data/bayesian_network/*/result.links3.links.txt` files | Shared broad-network scaffolds |
| `scripts/NetWeaver/fKDA.R` | Authoritative KDA engine |
| `results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz` | Cross-check current Phase 18 gene class and MitoCarta identity |
| `config/phase18_key_driver_selection.yml` | Current selection thresholds and class definitions |
| `scripts/18_key_driver_selection.py` | Current statistical reconstruction and selection authority |
| Phase 18 process document | Checksum-only conformance input before SEA-AD selection freeze |

### Inputs forbidden before SEA-AD selection freeze

VH10A, VH10B, and VH10C must not read:

- `results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv`;
- any VH09 candidate-bearing table;
- Phase 18 rows filtered to selected or passing genes; or
- the candidate-name section of a process document as machine input.

Those files become inputs only to VH10D.

## 6. VH10A — Freeze inputs and construct fine KDA queries

### 6.1 Structural manifest

Start from exactly 1,548 unique VH08 direction slots. Apply the single active
`phase18_parity_query` rule to every slot, producing exactly 1,548
query-rule/slot records. No optional query rule is constructed.

Each row retains:

- direction slot and source contrast IDs;
- supertype ID and label;
- broad network;
- sex/APOE signature group;
- `AD_up_mito` or `AD_down_mito`;
- source DEG terminal status and reason;
- result/filter/annotation paths and checksums;
- query-rule ID;
- pre-network and effective query sizes;
- induced-background size;
- query-size tier and terminal KDA eligibility.

A stable KDA run ID is created only for a runnable query:

```text
seaad::<query_rule>::<supertype_id>::<signature_group>::<direction>
```

### 6.2 Tested universe and induced background

For a completed contrast:

```text
tested_symbols
    = unique nonmissing current_symbol_for_kda values
      from rows with test_status == tested

induced_network
    = frozen broad-network edges whose source and target
      are both in tested_symbols

background
    = unique endpoints of induced_network
```

The background is contrast-specific. The whole network or all tested DEG rows
must not be substituted for the induced-network endpoint universe.

### 6.3 Directional query construction

For the active query rule and each sign:

```text
source query
    = unique current symbols satisfying:
      is_core_mito_phase18 == TRUE
      AND the query rule's FDR/effect predicate
      AND logFC sign matches AD_up_mito or AD_down_mito

effective query
    = source query intersect background
```

Duplicate feature rows use set semantics: a current symbol enters if any mapped
tested row satisfies the exact predicate. Conflicting current-symbol identity
or core-Mito annotation that could change membership is blocking. Feature-level
logFC/FDR differences do not replace the any-pass set rule.

Every effective query must be a subset of its recorded background. Query and
background members are written explicitly with hashes; sizes alone are
insufficient provenance.

### 6.4 Terminal query states

Every query-rule/slot row receives exactly one terminal state:

- `source_contrast_not_estimable`;
- `source_contrast_failed`;
- `query_empty`;
- `query_below_minimum` for effective size 1-2;
- `eligible_small_query` for effective size 3-9;
- `eligible_phase18_sized` for effective size at least 10.

Both `eligible_small_query` and `eligible_phase18_sized` enter KDA in the
current VH10 execution.

### 6.5 Blocking replay counts

VH10A must independently reproduce:

- 1,548 structural direction slots;
- 1,548 query-rule/slot records under the one active query rule;
- 520 completed source direction slots;
- 42 runnable queries with at least three effective genes;
- 20 AD-up and 22 AD-down active calls;
- the network/direction distribution in Section 2.

### VH10A outputs

```text
10a_inputs/
├── seaad_kda_run_manifest.tsv
├── seaad_kda_signature_members.tsv.gz
├── seaad_kda_background_members.tsv.gz
├── query_attrition.tsv
├── network_identity.tsv
├── input_checks.tsv
├── artifacts.tsv
└── status.tsv
```

## 7. VH10B — Run KDA and reconstruct complete run evidence

### 7.1 Executed KDA calls

The execution completed 42 active calls:

```text
1 Astrocyte call
20 Excitatory-neuron calls
16 Inhibitory-neuron calls
1 Microglia call
4 Oligodendrocyte calls
```

No FDR-only KDA call or separate minimum-ten aggregation is part of the current
execution. The 21 active calls that already contain at least 10 effective genes
remain part of the single minimum-three primary tier.

### 7.2 Frozen call parameters

For every runnable run, call `call_key_drivers()` with:

| Parameter | Value |
|---|---|
| Network | Run-specific induced network |
| `nLayerToTest` | 3 |
| `nLayersToExpand` | 0 |
| `bg.size` | Number of run-specific background genes |
| `directed` | `TRUE` |
| `reduce.within.nlayer` | 2 |
| `fdr` | 0.05 |
| `p.correction.method` | BH |
| `return.overlap` | `TRUE` |

The complete explicit candidate family must be reconstructed exactly as in
Phase 18 because `call_key_drivers()` returns only its significant subset.

### 7.3 Phase 18-compatible run reconstruction

For every run:

1. expand from the effective query through three undirected layers to form the
   explicit candidate family;
2. test cumulative directed downstream neighborhoods at layers 1, 2, and 3;
3. calculate the same upper-tail hypergeometric statistic and two-decimal fold
   enrichment;
4. choose the smallest-log-p layer with the lower layer as exact tie-breaker;
5. apply BH across the complete explicit family, including explicit zero-overlap
   tests;
6. reproduce the `call_key_drivers()` significant return exactly;
7. for a core-Mito driver that is itself in the query, subtract its guaranteed
   self-overlap from overlap, neighborhood, query, and background counts at
   every layer, then reselect the best layer;
8. recompute final within-run BH across the same explicit family; and
9. define conservative support only when other-query overlap is at least 2,
   final fold enrichment is greater than 1, and final run q is at most 0.05.

The implementation must reuse the current Phase 18 helpers directly or extract
a shared core covered by unchanged Phase 18 regression fixtures. A separate
unvalidated ACAT, BH, hypergeometric, self-exclusion, or ranking implementation
is not acceptable.

### 7.4 Evidence states

For aggregation, every network-level candidate/run pair is classified as:

- `explicit_test` or `explicit_zero_overlap`: use final raw p;
- `implicit_zero_overlap`: candidate is in the run background but outside the
  explicit family, use p = 1;
- `absent_from_background`: candidate is outside that run background, record
  missing and omit from primary ACAT.

Non-runnable structural slots create no synthetic evidence and never enter a
coverage denominator.

### VH10B outputs

```text
10b_kda/
├── seaad_kda_call_returns.tsv.gz
├── seaad_kda_significant_returns.tsv
├── seaad_kda_candidate_tests.tsv.gz
├── run_reconstruction_checks.tsv
├── run_qc.tsv
├── artifacts.tsv
└── status.tsv
```

No `model_objects/` directory is created. KDA uses fixed networks and table-based
enrichment tests, not fitted edgeR objects.

## 8. VH10C — Select and freeze independent SEA-AD candidates

### 8.1 Candidate unit and class

Within the active query rule, active run scope, and each broad network, define
the candidate unit as:

```text
broad_network + key_driver + case_id
```

Class is fixed independently of query membership:

- `mt_driver`: current Phase 18 core-Mito gene;
- `non_mt_driver`: all other assessable network genes.

Query membership changes self-exclusion only; it never creates a third class.

### 8.2 Cross-run aggregation

For the single active primary tier and each broad network:

1. define the candidate universe as the union of included run backgrounds;
2. include only successfully completed runs allowed by that tier;
3. set the network coverage denominator to that exact included-run count;
4. use final raw p for explicit evidence, p = 1 for implicit evidence, and omit
   absent-background evidence;
5. require coverage of at least 0.80 before reporting primary ACAT;
6. combine usable p-values with equal-weight Phase 18 ACAT and identical
   boundary handling;
7. apply BH within the broad network across both driver classes and all
   coverage-qualified candidate units with reportable ACAT p-values;
8. require all three Phase 18 candidate gates:
   - coverage at least 0.80;
   - at least one conservative supporting run;
   - aggregate ACAT q at most 0.05;
9. rank passing candidates within `broad_network + case_id` by aggregate q,
   aggregate p, then alphabetical current symbol; and
10. retain ranks 1-5 without backfilling.

Absent-from-background evidence is omitted from primary ACAT exactly as in the
active Phase 18 rule. The optional missing-as-one ACAT is not calculated now.

### 8.3 Evidence-depth interpretation

The active at-least-three-gene tier has these included-run counts before KDA
failure handling:

- Astrocytes: 1;
- Excitatory neurons: 20;
- Inhibitory neurons: 16;
- Microglia: 1;
- OPCs: 0;
- Oligodendrocytes: 4;
- Vasculature: 0.

A one-run network can technically produce a Phase 18-gated candidate, but it
must be labeled `single_run_network_evidence` and cannot be described as
recurrent. A network with zero included runs receives
`not_testable_no_included_runs`, not an empty biological result.
Leave-one-supertype-out stability is deferred and is not a current output or
candidate gate.

### 8.4 Independence freeze

Write and checksum-freeze every SEA-AD candidate summary and top-five list
before opening a candidate-bearing VH09 file. The freeze records:

- row and list counts;
- selected unit keys and ranks;
- analysis tier IDs;
- input and output SHA-256 values;
- freeze timestamp;
- code/config/Git identity.

### VH10C outputs

```text
10c_seaad_selection/
├── seaad_candidate_summary.tsv.gz
├── seaad_top5.tsv
├── seaad_list_status.tsv
├── seaad_selection_freeze.tsv
├── selection_checks.tsv
├── artifacts.tsv
└── status.tsv
```

The number of SEA-AD selected candidates is an outcome, not a planned count.
Five is a maximum per testable broad-network/driver-class list.

## 9. VH10D — Unblind ROSMAP and calculate overlap

VH10D may start only after the VH10C freeze is valid and immutable. It then
reads the VH09-frozen 47-unit ROSMAP Phase 18 top-five set. The 78 passing
Phase 18 candidate units are used only by the conformance gate, not as a second
sensitivity overlap tier.

### 9.1 Phase 18 conformance gate

Before overlap, the shared selection core must reproduce the current ROSMAP
Phase 18 reference with the minimum restored to 10, including:

- 95,557 canonical explicit gene-by-run rows from 161 included runs;
- 1,641 original significant returns;
- 10,433 explicitly represented gene-network candidate units;
- the complete union-of-backgrounds aggregate universe and BH family;
- 78 `driver_candidate` units;
- 47 top-five units with exact strict keys and ranks.

A mismatch is blocking. This replay validates the shared code but cannot alter
the already frozen SEA-AD list.

### 9.2 Strict overlap key and common universe

The primary overlap key is:

```text
broad_network + key_driver + case_id
```

For the active primary tier, each broad network, and each driver class, define
the common
assessable universe `U` as units that:

1. occur in both cohorts' union-of-backgrounds candidate universes;
2. meet the 0.80 coverage rule in both cohorts; and
3. have reportable primary ACAT evidence in both cohorts.

Do not use only the 10,433 explicit Phase 18 units as the universe; implicit p=1
units participate in Phase 18 aggregation and multiple-testing correction.
All selected-set counts, Jaccard denominators, and hypergeometric overlap tests
must be restricted to `U`.

### 9.3 Required overlap results

For every assessable broad-network/driver-class list in the active primary
tier, report:

- ROSMAP selected units in `U`;
- independently selected SEA-AD units in `U`;
- strict intersection count and identities;
- SEA-AD precision;
- ROSMAP recall among testable units;
- Jaccard index;
- hypergeometric overlap p-value using `U`;
- shared, ROSMAP-only, and SEA-AD-only units with ranks.

Each of the 47 frozen ROSMAP selected units receives one status:

| Status | Meaning |
|---|---|
| `rediscovered_top5` | Selected in both cohort-specific top-five lists |
| `seaad_driver_candidate_not_top5` | Passed SEA-AD gates but ranked below five |
| `tested_not_selected` | Assessable in SEA-AD but failed at least one selection gate |
| `not_testable` | No eligible SEA-AD run or outside the common assessable universe |

`not_testable` units are excluded from the replication denominator and are not
negative replications. In particular, the current DEG evidence predicts no
primary KDA assessment for Phase 18 OPC or Vasculature candidates.

A 25-unique-gene overlap that ignores network/class is reported only as a
secondary descriptive analysis.

### VH10D outputs

```text
10d_overlap/
├── phase18_selection_parity_checks.tsv
├── phase18_candidate_universe.tsv.gz
├── rosmap_seaad_candidate_overlap.tsv
├── rosmap_seaad_overlap_summary.tsv
├── rosmap_seaad_gene_only_overlap.tsv
├── overlap_checks.tsv
├── artifacts.tsv
└── status.tsv
```

## 10. Implemented code and repository end state

### Implemented code

```text
scripts/validation_human/
├── seaad_kda_validation_config.yml
├── 10_prepare_seaad_kda_inputs.py
├── 10_run_seaad_kda.R
├── 10_select_seaad_kda_candidates.py
└── 10_compare_rosmap_overlap.py

tests/validation_human/
└── test_vh10_phase18_selection_parity.py
```

The implemented split keeps the SEA-AD selection freeze and ROSMAP unblinding
as separate executable stages.

### Result root

```text
results/validation_human/10_seaad_kda_rediscovery/
├── 10a_inputs/
├── 10b_kda/
├── 10c_seaad_selection/
├── 10d_overlap/
├── checks.tsv
├── artifacts.tsv
└── status.tsv
```

### Added, changed, removed, and preserved

- **Added:** isolated VH09/VH10 scripts, shared validation configuration,
  contract tests, and result directories.
- **Changed:** this process document now records the executed result. No
  existing ROSMAP or VH00-VH08 analysis result was changed, and the Phase 18
  authority code was reused read-only without refactoring.
- **Removed:** nothing. The old broad-primary/98-slot design is removed from the
  plan, not deleted from an executed result tree.
- **Preserved read-only:** VH00-VH08 outputs, Phase 18 outputs and authority
  files, Phase 09 annotation, seven network files, and `fKDA.R`.

All new results and scripts remain inside the separate validation namespaces.
No sensitivity-specific result directory or file is created in the current
VH10 execution.

## 11. Executed commands and environment

VH10 read compact DEG shards and network edge lists. It did not read the
37.9-GB H5AD or the 6.4-GB pseudobulk bundle. All 42 KDA calls, the complete
table reconstruction, and the 161-run ROSMAP conformance replay completed
locally well within the 12-hour target. Minerva was not required.

The executed local interfaces were:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
export PYTHONDONTWRITEBYTECODE=1

.venv/bin/python -B scripts/validation_human/10_prepare_seaad_kda_inputs.py \
  --config scripts/validation_human/seaad_kda_validation_config.yml

Rscript scripts/validation_human/10_run_seaad_kda.R \
  --config scripts/validation_human/seaad_kda_validation_config.yml

.venv/bin/python -B scripts/validation_human/10_select_seaad_kda_candidates.py \
  --config scripts/validation_human/seaad_kda_validation_config.yml

.venv/bin/python -B scripts/validation_human/10_compare_rosmap_overlap.py \
  --config scripts/validation_human/seaad_kda_validation_config.yml
```

The scripts' help and syntax checks passed, all four execution stages reported
`validated_complete`, and the VH09/VH10 contract suite passed all six tests.

## 12. Completion criteria

VH10 completed after all of the following criteria were met:

1. all 1,548 structural direction slots remain present and the single active
   query rule produces exactly 1,548 query-rule/slot records;
2. source-DEG terminal states are preserved without converting non-estimable
   slots into biological nulls;
3. tested symbols, induced networks, backgrounds, query predicates, symbol set
   semantics, and core-Mito membership reproduce the frozen rules exactly;
4. the audited 520 completed source directions and 42 active queries with at
   least three effective genes are independently reproduced, or any mismatch
   is resolved before KDA;
5. all effective queries are subsets of their recorded backgrounds and every
   member table is checksum-frozen;
6. every eligible query receives a terminal KDA record and no ineligible slot
   enters an aggregation denominator;
7. Phase 18 explicit-family reconstruction, directed-layer tests, within-run
   BH, self-exclusion, final BH, and conservative-support logic pass parity
   fixtures;
8. the single active tier recomputes its candidate universe, coverage, ACAT,
   aggregate BH, gates, ranks, and lists;
9. the primary selection uses fine-supertype runs only; broad DEG anchors never
   enter its denominator;
10. SEA-AD top lists are checksum-frozen before any VH09 candidate-bearing file
    is read;
11. the post-freeze Phase 18 conformance replay reproduces the exact 78 passing
    and 47 selected units and their ranks;
12. overlap uses the strict network-gene-class key and the common assessable
    universe, with `not_testable` excluded from replication denominators;
13. no deferred sensitivity analysis is executed or required for completion;
14. all blocking checks pass; and
15. the root `status.tsv` reports `validation_status = validated_complete`.

## 13. Interpretation boundary

The strongest defensible conclusion will be:

> SEA-AD independently rediscovered *k* of the *n* ROSMAP Phase 18 candidate
> units that were assessable using SEA-AD fine-supertype mitochondrial DEG
> queries on the same frozen broad-network scaffold.

The denominator is not automatically 47. It is the number of frozen ROSMAP
units in the common assessable universe for the active minimum-three primary
tier. Results from 3-9-gene queries and one-run networks must be labeled with
their evidence depth. Deferred sensitivity analyses contribute no evidence to
the current interpretation. A shared network-associated key driver supports
prioritization and replication of network evidence; it does not by itself
establish causal regulation.
