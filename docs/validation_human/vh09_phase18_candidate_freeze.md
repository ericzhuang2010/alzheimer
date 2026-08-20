# VH09 ROSMAP Phase 18 Candidate Freeze

**Status:** executed; `validated_complete` on 2026-08-20
**Code:** `scripts/validation_human/09_freeze_rosmap_kda_candidates.py`
**Configuration:** `scripts/validation_human/seaad_phase18_validation_config.yml`
**Output:** `results/validation_human/09_rosmap_kda_candidates/`
**Execution:** completed locally; Minerva was not required

## Execution result

VH09 passed every authority-hash, schema, uniqueness, class, rank, count, and
network-identity gate. The frozen outputs contain:

- 95,557 canonical explicit gene-by-run rows;
- 10,433 canonical candidate units;
- 78 passing Phase 18 candidate units retained as a conformance reference;
- 47 top-five units used as the primary ROSMAP validation target; and
- 25 unique genes among those 47 units.

The 78-unit passing table was not used to execute a sensitivity comparison in
VH10. It was used only to require exact Phase 18 selection parity before
unblinding the primary 47-unit set.

## 1. Purpose and boundary

VH09 freezes the ROSMAP Phase 18 discoveries that will be compared with an
independently generated SEA-AD key-driver list in VH10. It performs no SEA-AD
query construction, KDA, candidate scoring, reranking, or overlap analysis.

The authoritative Phase 18 candidate unit is:

```text
broad_network + key_driver + case_id
```

where `case_id` is exactly one of:

- `mt_driver`;
- `non_mt_driver`.

The current canonical Phase 18 table contains:

- 95,557 explicit gene-by-run rows;
- 10,433 candidate units represented by at least one explicit run row;
- 78 units with `terminal_candidate_status = driver_candidate`;
- 47 units with `top5_display = TRUE`;
- 25 unique genes among those 47 selected units.

The 47 selected units, not merely the 25 unique symbols, are the primary ROSMAP
validation target because the same gene selected in two broad networks is two
different discoveries.

## 2. What VH09 does not do

VH09 does **not** use the 47 ROSMAP units as SEA-AD KDA queries. The SEA-AD
queries are mitochondrial DEG signatures from the VH08 fine-supertype by
sex/APOE contrasts.

VH09 also does not create a ROSMAP-candidate-by-SEA-AD-contrast cross-product.
That older 553-row concept belonged to the retired broad-only validation plan
and would encourage targeted scoring of known ROSMAP winners. VH10 instead:

1. constructs SEA-AD queries without reading candidate-bearing VH09 files;
2. runs KDA over all assessable network genes;
3. selects and checksum-freezes the independent SEA-AD lists; and only then
4. reads VH09 to measure ROSMAP/SEA-AD overlap.

There is no scientifically meaningful `phase18_selected_directions.tsv`
output. A Phase 18 candidate unit aggregates evidence across its contributing
fine-cell, group, and direction runs; direction is run provenance, not part of
the selected-unit key.

## 3. Authoritative inputs

| Input | Role |
|---|---|
| `results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv` | Canonical current Phase 18 explicit test and candidate-selection table |
| `results/minerva_production/18_key_driver_selection/call_key_driver_significant_returns.tsv` | Corroborating run-return subset; not used to select candidates |
| `config/phase18_key_driver_selection.yml` | Current two-class selection constants and run-scope authority |
| `scripts/18_key_driver_selection.py` | Current reconstruction, self-exclusion, ACAT, BH, gate, and ranking authority |
| `docs/phase_18_key_driver_selection/key_driver_selection_process.md` | Human-readable current selection contract |
| `results/validation_human/08_deg/status.tsv` | Sequence gate: require the clean SEA-AD DEG release to be complete |
| `results/validation_human/04_supertype_manifest/supertype_to_broad_network.tsv` | Verify the seven shared broad-network names only; no DEG or candidate scoring |

Phase 12 is not a source of candidates. Its network, background, annotation,
and `fKDA.R` assets are technical inputs to VH10, not VH09 selection inputs.
Archived three-case Phase 18 files are not selection authorities.

All authoritative inputs, the VH09 code, and the configuration must be
full-file SHA-256 frozen. Input identity mismatch is blocking.

## 4. Process

### VH09A — Validate the Phase 18 authority

1. Require the canonical return table and all current authority files.
2. Freeze paths, sizes, SHA-256 values, schemas, and the Git revision.
3. Require the current two driver classes and reject any historical third
   query-member class.
4. Require uniqueness of `kda_run_id + key_driver` in the explicit table.
5. Require selection-bearing fields to be constant within each candidate unit.
6. Reproduce the canonical counts: 95,557 rows and 10,433 explicit-table
   candidate units.

### VH09B — Freeze passing and selected units

Deduplicate to one row per:

```text
broad_network + key_driver + case_id
```

Retain the Phase 18 aggregate evidence and display fields needed for later
comparison:

- `coverage_fraction`;
- `conservative_support_count`;
- `aggregate_acat_p`;
- `aggregate_acat_q`;
- `terminal_candidate_status`;
- `within_case_rank`;
- `top5_display`.

Create two immutable sets:

- primary set: 47 units with `top5_display = TRUE`;
- conformance set: 78 units with
  `terminal_candidate_status = driver_candidate`.

Require 25 unique genes in the primary set. Preserve network and driver-class
membership for every symbol; do not collapse the primary table to 25 rows.

### VH09C — Freeze shared network scope

The 47 selected units occur in the same seven broad-network names used by the
SEA-AD supertype mapping:

- Astrocytes;
- Excitatory neurons;
- Inhibitory neurons;
- Microglia;
- OPCs;
- Oligodendrocytes;
- Vasculature cells.

Store the exact machine IDs used by both cohorts. This is a name/identity gate,
not a claim that every network will have a runnable SEA-AD query. VH10 decides
SEA-AD assessability after query construction.

### VH09D — Write the immutable freeze

Write outputs atomically, then generate checksums and a terminal status. A
failed count, key, class, rank, or checksum gate must yield `failed`, never a
partial candidate freeze.

## 5. Outputs

| File | End state |
|---|---|
| `phase18_selected_candidate_units.tsv` | Exactly 47 selected gene-network-class units with ranks and aggregate evidence |
| `phase18_passing_candidate_units.tsv` | Exactly 78 passing units retained for Phase 18 conformance checking; no sensitivity comparison was executed |
| `phase18_selected_genes.tsv` | The 25 unique selected symbols with all network/class memberships retained |
| `phase18_candidate_unit_counts.tsv` | Counts by broad network, driver class, passing status, and display status |
| `shared_network_scope.tsv` | Exact ROSMAP/SEA-AD broad-network identity crosswalk |
| `phase18_selection_authority.tsv` | Paths, sizes, schemas, Git identity, and SHA-256 values for current authority files |
| `candidate_freeze_checks.tsv` | Blocking identity, count, uniqueness, class, rank, and network checks |
| `artifacts.tsv` | Full-file output checksums and roles |
| `status.tsv` | One terminal VH09 record and principal output checksums |

No SEA-AD candidate or contrast table is written in VH09.

## 6. End state and repository changes

After the completed VH09 execution:

- ROSMAP has one immutable 47-unit primary target and one immutable 78-unit
  passing-unit conformance reference;
- candidate units retain their broad-network and driver-class identity;
- the independent SEA-AD selection code can checksum the VH09 authority but
  cannot read candidate-bearing tables before its own list is frozen; and
- VH10D can unblind the frozen ROSMAP units for overlap analysis.

Executed repository changes:

- **Added:** the VH09 script, shared validation configuration, isolated result
  directory, and validation tests;
- **Changed:** this document now records the executed result;
- **Removed:** no repository file. The old proposed 553-row cross-product and
  selected-direction outputs are removed from the contract, but neither exists
  in the clean rebuilt results;
- **Preserved read-only:** all Phase 18, VH08, network, and annotation inputs.

## 7. Executed local command

The executed interface was:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -B scripts/validation_human/09_freeze_rosmap_kda_candidates.py \
  --config scripts/validation_human/seaad_phase18_validation_config.yml
```

The script's `--help`, Python compilation, contract checks, and full execution
all passed. VH09 completed locally in under one minute.

## 8. Completion criteria

VH09 is complete only when:

1. every authority file matches its frozen full-file SHA-256;
2. the canonical table contains 95,557 unique explicit gene-by-run rows;
3. candidate-unit fields are constant after deduplication by the strict key;
4. exactly 78 units pass the Phase 18 candidate gates;
5. exactly 47 units are selected for top-five display;
6. those 47 units represent exactly 25 unique genes;
7. only `mt_driver` and `non_mt_driver` occur;
8. the selected units use the seven shared broad-network IDs;
9. no SEA-AD DEG, query, or candidate identity affects the freeze; and
10. all checks pass with `status.tsv: validation_status = validated_complete`.
