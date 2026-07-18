# Resumable Per-RDS Execution on Minerva

## Purpose and current scope

The pipeline can select one enabled RDS row with `--rds-id`. This allows independent Phase 08 MAST tasks to run on separate Minerva compute nodes while sharing read-only upstream data.

Checksum-aware resume is currently implemented for `--phase mast` only. Other phases still follow their existing execution behavior even when `resume: true`; they must not be assumed resumable until they have task-specific artifact validation.

The implementation is in:

- `scripts/run_pipeline.R`: top-level `--rds-id` and `--force` options, task selection, and collision-free per-RDS task-graph names.
- `scripts/run_one_rds.R`: strict MAST completion validation and skip/rerun decision.
- `config/minerva_production_execution.yml`: `resume: true` enables the skip check.

## Behavior with and without `--rds-id`

### No `--rds-id`

The controller selects all nine enabled production RDS rows and visits them sequentially in manifest order. It does not launch them concurrently.

For Phase 08, each row is checked before execution:

- a fully validated, checksum-matching row is skipped quickly;
- an incomplete, failed, missing, stale, or checksum-mismatched row is executed; and
- after that row finishes, the controller advances to the next row.

Therefore this command is a sequential resume of the complete Phase 08 stage:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast
```

### With `--rds-id`

The controller selects exactly one enabled manifest row. This is the recommended unit for assigning independent work to separate compute nodes:

```bash
RDS_ID=astrocytes

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID"
```

Valid Minerva production IDs are:

```text
astrocytes
excitatory_set1
excitatory_set2
excitatory_set3
immune
inhibitory
opcs
oligodendrocytes
vasculature
```

Use one distinct ID per node. Do not run the same ID concurrently on two nodes because both processes would target the same RDS-specific outputs, log, and status.

## What counts as safely completed

The MAST task is skipped only when every layer below validates against the current checkout and current inputs.

1. The controller status must contain the expected task ID and source RDS, matching execution identity, exit code zero, and `validated_complete`.
2. The controller's scientific-script, scientific-configuration, and RDS-manifest SHA-256 values must match current files.
3. The scientific MAST status must have schema `mast_de_status_v1`, the expected task/source, matching code/config/manifest checksums, `validated_complete`, and zero failed contrasts.
4. The current normalized RDS, contrast manifest, pseudobulk sample table, and pseudobulk DE result must match the checksums recorded by MAST.
5. Every artifact recorded in the MAST artifact manifest must still exist with its recorded byte count and SHA-256 and must be labeled `validated_complete`.

Only then does execution print:

```text
Resume: skipping validated task mast:<rds_id> because code, inputs, statuses, and artifact checksums match.
```

If any check fails, the task runs again. When an old controller status exists, the runner prints the mismatched validation categories before rerunning.

## What happens after a failure or node loss

| Previous event | State seen on rerun | Decision |
| --- | --- | --- |
| The scientific script returned an error normally | Controller status is `failed` or has a nonzero exit code | Rerun |
| The node died before controller status was written | Status is absent, incomplete, or stale | Rerun |
| Some result files were written but final status/artifact validation did not complete | One or more required status, byte-count, or checksum checks fail | Rerun |
| A previous validated result exists but a later forced run died after changing an artifact | Old status no longer matches current artifact bytes/checksums | Rerun |
| A previous validated result exists and an interrupted run changed nothing | All validated files and checksums still match | Safe skip |
| Scientific outputs finished, but the node died before the controller wrote its final status | Scientific files may be complete, but the controller layer is not validated | Conservative rerun |
| Script, scientific config, manifest, normalized RDS, contrast manifest, or Phase 07 input changed | At least one checksum differs | Rerun |
| All completion layers and checksums match | Validated result is unchanged | Skip |

The presence of an output file alone never causes a skip. Temporary or partial files are not accepted as completed results. The scientific scripts publish their individual final files atomically, but a crash between files can still leave a mixed bundle; the artifact-manifest checks detect that case.

Resume granularity is one complete RDS task, not one contrast inside an RDS. If a node dies after several MAST contrasts have been fitted but before that RDS publishes a fully validated bundle, the replacement run starts that RDS from the beginning. Other RDS tasks that already have complete checksum-matching bundles are still skipped.

## Recovery procedure

After a failed task or lost node:

1. Start a replacement Minerva compute node.
2. Synchronize the same promoted Git revision used by the other Phase 08 nodes.
3. Run the Minerva new-session and MKL setup in Section 7.3 of the research plan.
4. Reissue the same `--rds-id` command.
5. Read the resume message. A validated task skips; otherwise it reruns.
6. After all nine IDs finish, run the combined Phase 08 validation from the research plan.

Do not delete partial files merely to make resume work. The validation logic decides whether the bundle is reusable. Preserve logs and failed statuses for diagnosis.

## Dry runs and task graphs

A dry run validates selection and script availability but does not execute the full checksum-aware resume decision:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --dry-run
```

The selected task must have `script_exists = TRUE`. Per-RDS graphs have unique names:

```text
results/minerva_production/00_environment/
  minerva_production_mast_<rds_id>_task_graph.tsv
```

The graph name prevents different RDS nodes from overwriting one shared planning graph.

## Intentional reruns

Use `--force` only when a validated result must intentionally be recomputed. It bypasses the MAST resume skip:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --force
```

Without `--force`, a changed checksum already causes an automatic rerun, so force is not needed after code, configuration, manifest, or input changes.

## Operational rules for multi-node execution

- Use the same Git revision, `renv` environment, scientific config, RDS manifest, execution config, and MKL 2019 setup on every node.
- Assign each RDS ID to at most one active node.
- Use the scoped `LD_PRELOAD="$MKL_PRELOAD"` prefix for the controller so all child R processes inherit the working MKL link group.
- Do not mix `R/4.3.3` with the newer standalone MKL modules.
- Do not run an all-RDS Phase 08 controller at the same time as per-RDS Phase 08 controllers.
- Run the combined 756-row Phase 08 validation only after all nine RDS tasks have terminal statuses.

## Relationship to the research plan

The authoritative Minerva environment/MKL setup and combined Phase 08 validation remain in `docs/mitochondria_sex_apoe_research_plan.md`. This file explains the reusable selection, resume, failure-detection, and recovery mechanics in isolation.
