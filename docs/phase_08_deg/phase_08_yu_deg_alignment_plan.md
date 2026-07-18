# Phase 08: Yu-Compatible Cell-Level MAST Differential Expression

## Status and replacement decision

This document defines the new Phase 08. It replaces the donor-screened Phase 08 v1 implementation that inherited model eligibility from Phase 07 while retaining the established `08_mast/` directory name.

The replacement is a standalone Yu-replication branch:

- Use all Phase 05 nuclei marked `cohort_included` for the requested fine cell type, sex, APOE group, and diagnosis.
- Construct the six Yu AD-versus-NCI strata for every fine cell type.
- Do not read Phase 07 contrast eligibility, pseudobulk samples, or pseudobulk DEG results.
- Keep Phase 07 unchanged as the donor-aware primary analysis.
- Continue writing Phase 08 under `results/<environment>/08_mast/`.
- Treat legacy `08_mast/*.mast_*` v1 artifacts as deprecated historical output.
- Distinguish the replacement with `08_mast/*.yu_mast_*` filenames and v2 schemas.

The v1 comparison with Yu is retained in `docs/DEG_mismatch/phase08_vs_yu_degs.md`. Historical v1 artifacts may be retained in the same directory for audit, but the new Phase 08 and its downstream consumers must select only `*.yu_mast_*` v2 artifacts and must never read legacy `*.mast_*` v1 artifacts.

## High-level purpose

Reproduce the cell-level differential-expression analysis reported by Yu et al. as closely as the available data, metadata, and software versions allow. Within each fine cell type and each sex-by-APOE stratum, compare AD with NCI using the Phase 05 normalized RNA `data` layer and Seurat's MAST implementation.

The production design contains:

- 54 fine cell types;
- two sex groups: Female and Male;
- three APOE groups: `e2`, `e33`, and `e4`;
- six AD-versus-NCI comparisons per fine cell type;
- 324 planned cell-type/contrast status rows.

The local pilot uses the identical code and parameters for five Vasculature fine cell types and therefore produces 30 planned status rows.

MAST remains a Yu-comparability analysis rather than the primary donor-level inference. Cell-level covariates do not make nuclei from the same donor statistically independent. Phase 07 pseudobulk remains primary.

## Exact scientific definition

### Analysis population

For each fine cell type and sex-by-APOE stratum, select nuclei satisfying all of the following:

1. `cohort_included == TRUE`;
2. `cell_type_high_resolution` equals the target fine cell type;
3. `sex` equals the target sex;
4. `apoe_group` equals the target APOE group;
5. `diagnosis` is AD or NCI.

Use every selected nucleus. Do not apply Phase 07's minimum of 20 nuclei per donor-cell-type unit, minimum of five donors per diagnosis arm, `primary_eligible` flag, or contrast `eligibility_status`.

Record cell counts and unique-donor counts for AD and NCI separately. Low counts are warnings, not replication exclusion criteria. A comparison is `not_estimable` only when the model cannot be fit, such as when an arm has zero cells, a required covariate is unavailable or nonfinite, or the design is non-estimable. Every planned comparison must still have one explicit terminal status.

### Six Yu contrasts

| Internal contrast | Yu stratum | Numerator | Denominator |
|---|---|---|---|
| `AD_vs_NCI__Female__e2` | `F_e2x` | Female APOE-e2 AD | Female APOE-e2 NCI |
| `AD_vs_NCI__Female__e33` | `F_e33x` | Female APOE-e33 AD | Female APOE-e33 NCI |
| `AD_vs_NCI__Female__e4` | `F_e4x` | Female APOE-e4 AD | Female APOE-e4 NCI |
| `AD_vs_NCI__Male__e2` | `M_e2x` | Male APOE-e2 AD | Male APOE-e2 NCI |
| `AD_vs_NCI__Male__e33` | `M_e33x` | Male APOE-e33 AD | Male APOE-e33 NCI |
| `AD_vs_NCI__Male__e4` | `M_e4x` | Male APOE-e4 AD | Male APOE-e4 NCI |

The effect direction is always AD minus NCI. Positive `logFC` means higher expression in AD.

### MAST model

For every estimable comparison, use:

```r
Seurat::FindMarkers(
  object = stratum_object,
  ident.1 = "AD",
  ident.2 = "NCI",
  group.by = "diagnosis",
  assay = "RNA",
  slot = "data",
  test.use = "MAST",
  min.pct = 0.10,
  logfc.threshold = 0,
  latent.vars = c("nCount_RNA", "age_death_scaled", "pmi_scaled"),
  densify = FALSE,
  verbose = FALSE
)
```

The Phase 05 normalized RNA `data` layer is the expression input. Do not use integrated, `scale.data`, pseudobulk, or SCTransform values.

### DEG rule

Within each completed comparison:

1. retain the genes returned by `FindMarkers` after `min.pct = 0.10`;
2. calculate Benjamini-Hochberg adjusted p-values within that returned gene set;
3. call a Yu-compatible DEG when `FDR < 0.05` and `abs(logFC) > log2(1.3)`;
4. preserve raw p-value, BH FDR, the Seurat Bonferroni value if available, `pct.1`, `pct.2`, and log2 fold change.

The comparisons are strict: `< 0.05` and `> log2(1.3)`. Supplemental Table S1 is a post-fit validation target only. Never tune the model or thresholds from the Table S1 labels.

## Inputs and dependencies

### Required scientific inputs

| Input | Local pilot | Minerva production | Role |
|---|---|---|---|
| Phase 05 normalized RDS | `results/local_pilot/05_normalized/Vasculature_cells.normalized.rds` | One `*.normalized.rds` per enabled manifest row under `results/minerva_production/05_normalized/` | Normalized RNA values and cell metadata. |
| Phase 05 status | Matching `*.normalization_status.tsv` | Nine matching status files | Must be `validated_complete`; freezes normalized-object provenance. |
| RDS manifest | `config/local_pilot_rds_manifest.tsv` | `config/minerva_rds_manifest.tsv` | Selects the source object and expected fine-cell-type count. |
| Scientific config | `config/analysis_parameters.yml` | The same file and checksum | Supplies direction, strata, covariates, alpha, and fold-change threshold. |
| Pipeline config | `config/local_pilot.yml` | `config/minerva_shared.yml` | Supplies output root and manifest path. |
| Execution config | `config/local_pilot_execution.yml` | `config/minerva_production_execution.yml` | Supplies environment identity, logs, resources, and resume behavior. |

The normalized RDS must contain:

- `projid`;
- `cohort_included`;
- `cell_type_high_resolution`;
- `diagnosis`;
- `sex`;
- `apoe_group`;
- `nCount_RNA`;
- `age_death_scaled`;
- `pmi_scaled`.

Phase 08 builds its own six-stratum manifest from these Phase 05 metadata. Phase 06 group-coverage tables may be used only as an independent reconciliation check; they do not control model eligibility.

### Yu validation inputs

| Input | SHA-256 | Role |
|---|---|---|
| `docs/yu_paper/ALZ-22-e71463-s002.xlsx` | `333898a4c1b89a484b56f51164bdc2fd553a43f7938fc1db2e19b1b8a7dc1ff0` | Supplemental Table S1 DEG acceptance oracle. |
| `docs/yu_paper/ALZ-22-e71463-s001.docx` | `731176fd5947403bc72115be2c34fa55fc49dd7d697e7aadfa86ca67ac620aaf` | Supporting supplemental figures; not a model input. |

### Explicit non-inputs

The new Phase 08 must not read or hash:

- `results/<environment>/07_contrasts/`;
- `results/<environment>/07_pseudobulk/`;
- `results/<environment>/07_pseudobulk_de/`;
- any Phase 07 eligibility field.

MAST-versus-pseudobulk comparison belongs in Phase 12, after the two independent branches have completed.

## Outputs and files created

### Per-RDS Phase 08 bundle

For every RDS ID, create the following under `results/<environment>/08_mast/`:

| File pattern | Contents |
|---|---|
| `<rds_id>.yu_mast_contrast_manifest.tsv` | Six rows per fine cell type with stratum, Yu label, cell/donor counts, analysis population, and model eligibility. |
| `<rds_id>.yu_mast_de.tsv.gz` | All returned genes, effect sizes, detection fractions, raw p-values, FDR, Yu DEG flag, and provenance. |
| `<rds_id>.yu_mast_model_diagnostics.tsv` | One row per planned comparison with counts, covariates, design dimensions, fit status, and message. |
| `<rds_id>.yu_mast_contrast_status.tsv` | One terminal status per planned comparison. |
| `<rds_id>.yu_mast_de_checks.tsv` | Structural, numerical, and provenance checks. |
| `<rds_id>.yu_mast_de_artifacts.tsv` | Artifact paths, byte counts, record counts, SHA-256 values, and status. |
| `<rds_id>.yu_mast_de_status.tsv` | One task summary using `yu_mast_de_status_v2`. |

Every result and status row records `analysis_population = yu_all_cohort_included_nuclei`. The result schema is `yu_mast_de_results_v2`, with corresponding v2 manifest, status, diagnostic, check, and artifact schemas.

The controller also creates:

| File pattern | Contents |
|---|---|
| `results/<environment>/status/mast__<rds_id>.tsv` | Controller exit code, execution identity, code/config hashes, elapsed time, and log path. |
| `results/<environment>/logs/mast__<rds_id>.log` | Captured stdout and stderr. |
| `results/<environment>/00_environment/<environment>_mast*_task_graph.tsv` | Stable task IDs and code/config/schema hashes from the dry run or execution. |

### Yu Table S1 validation bundle

Create the following under `results/<environment>/08_mast/yu_table_s1_validation/`:

| File | Contents |
|---|---|
| `yu_table_s1_comparison_summary.tsv` | Overall overlap, recall, precision, Jaccard, direction, and effect-size metrics. |
| `yu_table_s1_comparison_by_contrast.tsv` | Metrics for each Yu sex/APOE stratum. |
| `yu_table_s1_comparison_by_cell_type.tsv` | Metrics for each fine cell type. |
| `yu_table_s1_mismatches.tsv.gz` | Row-level Yu-only and Phase-08-only calls with mismatch reasons. |
| `yu_table_s1_comparison_checks.tsv` | XLSX checksum, sheet, mapping, uniqueness, coverage, and numeric checks. |
| `yu_table_s1_comparison_status.tsv` | Validation scope and alignment tier: `exact`, `method_equivalent`, or `below_target`. |

The local comparison covers only Vasculature. Only the complete Minerva comparison covers all 118,297 Table S1 DEG rows.

## Code and configuration changes required before execution

### Replace or add

| File | Required change |
|---|---|
| `scripts/08_run_mast.R` | Replace v1 selection and Phase 07 gating with the all-cohort implementation; write `08_mast/*.yu_mast_*` v2 artifacts. |
| `scripts/08_compare_yu_table_s1.R` | Add a read-only Table S1 comparator and mismatch-report generator. |
| `scripts/run_one_rds.R` | Validate v2 resume from Phase 05, code, config, manifest, and artifact hashes; remove Phase 07 hash requirements. |
| `scripts/run_pipeline.R` | Register output schema `yu_mast_de_v2`. |
| `config/analysis_parameters.yml` | Make analysis population, `min.pct`, logFC threshold, latent variables, alpha, and Yu fold-change threshold explicit. |

### Update downstream consumers

The following must consume `08_mast/*.yu_mast_*` v2 artifacts instead of legacy `08_mast/*.mast_*` v1 artifacts. The directory does not change; the file patterns, schemas, status semantics, and scientific coverage do:

- `scripts/09_run_mito_pathways.R`;
- `scripts/10_similarity_analysis.R`;
- `scripts/11_apply_multiple_testing.R`;
- `scripts/12_sensitivity_analysis.R` where fields differ;
- `scripts/14_validate_outputs.R`;
- `scripts/15_make_figures.R` where Phase 08 paths are used;
- `scripts/plot_similar_to_yu_figure01.R`.

After validation, update `docs/research_plans/mitochondria_sex_apoe_research_plan.md`, `docs/phase_08_explained.md`, and `docs/DEG_mismatch/phase08_vs_yu_degs.md`.

## Local pilot: run the 30-row Vasculature design

### Input

- the validated Phase 05 Vasculature normalized object;
- five Vasculature fine cell types from its metadata;
- six Yu strata per cell type;
- the shared scientific and local execution configs.

No Phase 07 file is required.

### Output

One Vasculature v2 bundle under `results/local_pilot/08_mast/`, one controller status, one log, one task graph, and the Vasculature-only Table S1 validation bundle.

### What changes

The task reads the normalized object, creates 30 manifest rows, subsets nuclei in memory, and runs every estimable comparison. It does not alter the normalized RDS or any output from Phases 00-07. The known male/APOE-e2/AD `Fib SLC4A4` zero-cell arm, if still present in Phase 05 metadata, must be `not_estimable` rather than omitted.

### Preflight

Do not execute Phase 08 until the v2 files above are implemented. Confirm inputs and packages:

```bash
test -r results/local_pilot/05_normalized/Vasculature_cells.normalized.rds
test -r results/local_pilot/05_normalized/Vasculature_cells.normalization_status.tsv

Rscript -e '
stopifnot(
  requireNamespace("Seurat", quietly = TRUE),
  requireNamespace("SeuratObject", quietly = TRUE),
  requireNamespace("MAST", quietly = TRUE),
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("readxl", quietly = TRUE)
)
cat("Seurat", as.character(packageVersion("Seurat")), "\n")
cat("MAST", as.character(packageVersion("MAST")), "\n")
'
```

### Execute

Use `--force` for the first v2 run so an old `mast:vasculature` controller status cannot be mistaken for the replacement task:

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mast \
  --rds-id vasculature \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase mast \
  --rds-id vasculature \
  --force

Rscript scripts/08_compare_yu_table_s1.R \
  --config config/local_pilot.yml \
  --yu-supplement docs/yu_paper/ALZ-22-e71463-s002.xlsx \
  --rds-id vasculature
```

Expected dry-run result: exactly one `mast:vasculature` task, `script_exists = TRUE`, and output schema `yu_mast_de_v2`.

### Validate

```bash
Rscript -e '
root <- "results/local_pilot/08_mast"
scientific <- read.delim(file.path(root, "vasculature.yu_mast_de_status.tsv"))
manifest <- read.delim(file.path(root, "vasculature.yu_mast_contrast_manifest.tsv"))
contrasts <- read.delim(file.path(root, "vasculature.yu_mast_contrast_status.tsv"))
checks <- read.delim(file.path(root, "vasculature.yu_mast_de_checks.tsv"))
controller <- read.delim("results/local_pilot/status/mast__vasculature.tsv")
comparison_checks <- read.delim(file.path(
  root, "yu_table_s1_validation", "yu_table_s1_comparison_checks.tsv"
))

print(table(contrasts$terminal_status))
stopifnot(
  identical(scientific$schema_version, "yu_mast_de_status_v2"),
  identical(scientific$validation_status, "validated_complete"),
  identical(scientific$analysis_population, "yu_all_cohort_included_nuclei"),
  nrow(manifest) == 30L,
  nrow(contrasts) == 30L,
  !anyDuplicated(manifest$contrast_id),
  !any(contrasts$terminal_status == "failed"),
  all(contrasts$terminal_status %in% c("validated_complete", "not_estimable")),
  all(checks$passed),
  identical(controller$validation_status, "validated_complete"),
  controller$exit_code == 0L,
  all(comparison_checks$passed)
)
'
```

### Required local output check

- one v2 scientific status and one validated controller status;
- exactly 30 manifest and contrast-status rows;
- every estimable comparison is `validated_complete`;
- every non-estimable comparison has an explicit reason;
- no `failed` comparison;
- unique `(cell type, Yu contrast, gene)` result keys;
- finite p-values and FDR values in `[0,1]`;
- the strict Yu DEG rule reproduces `paper_deg` from stored numeric fields;
- the normalized RDS checksum is unchanged;
- no Phase 07 path or checksum appears in the scientific status;
- the XLSX checksum and Vasculature-only validation scope are recorded.

The local pilot is nonfinal. It validates the shared code path and Vasculature subset, not the complete 54-cell-type match.

## Minerva production: run all 324 planned rows

### Input

- nine validated Phase 05 normalized RDS files under `results/minerva_production/05_normalized/`;
- nine matching normalization statuses;
- `config/minerva_rds_manifest.tsv` with all enabled rows;
- the promoted v2 scripts and shared scientific config;
- the frozen Yu XLSX for post-fit validation.

No Phase 07 output is required. Phase 08 may run independently of Phase 07 after Phase 05 completes.

### Output

Nine per-RDS v2 bundles under `results/minerva_production/08_mast/`, nine controller statuses, nine logs, task graphs, and one complete Table S1 validation bundle. Combined scope is 54 fine cell types and 324 status rows.

### Phase 05 availability preflight

Run on a Minerva compute node from the project root:

```bash
Rscript -e '
manifest <- read.delim("config/minerva_rds_manifest.tsv", check.names = FALSE)
manifest <- manifest[
  toupper(as.character(manifest$enabled)) %in% c("TRUE", "T", "1", "YES"), ]
base <- sub("[.][Rr][Dd][Ss]$", "", basename(manifest$input_rds))
rds <- file.path(
  "results/minerva_production/05_normalized", paste0(base, ".normalized.rds"))
status <- file.path(
  "results/minerva_production/05_normalized",
  paste0(base, ".normalization_status.tsv"))
print(data.frame(
  rds_id = manifest$rds_id,
  normalized_exists = file.exists(rds),
  status_exists = file.exists(status)))
stopifnot(length(rds) == 9L, all(file.exists(rds)), all(file.exists(status)))
statuses <- do.call(rbind, lapply(status, read.delim))
stopifnot(all(statuses$validation_status == "validated_complete"))
'
```

If normalized files are absent, recreate the Phase 05 prerequisite without changing its method:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase normalize
```

### Minerva runtime setup

Use the initialized R 4.3.3/renv environment from the main research plan on a 192-GiB compute node, not a login node:

```bash
cd /sc/arion/work/zhuane01/alzheimer

export MKLROOT=/hpc/packages/minerva-centos7/intel/parallel_studio_xe_2019/compilers_and_libraries/linux/mkl
export MKL_LIB="$MKLROOT/lib/intel64_lin"
export MKL_PRELOAD="$MKL_LIB/libmkl_gf_lp64.so:$MKL_LIB/libmkl_gnu_thread.so:$MKL_LIB/libmkl_core.so"
export LD_LIBRARY_PATH="$MKL_LIB:$LD_LIBRARY_PATH"
export LD_RUN_PATH="$LD_LIBRARY_PATH"
export MKL_ENABLE_INSTRUCTIONS=AVX2
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
unset LD_DEBUG LD_DEBUG_OUTPUT

Rscript -e '
stopifnot(
  as.character(packageVersion("Seurat")) == "5.5.1",
  as.character(packageVersion("MAST")) == "1.28.0",
  requireNamespace("readxl", quietly = TRUE)
)
'
```

### Execute the full phase on one node

Use `--force` for the first v2 launch. Omit it on later resumptions so validated v2 tasks are skipped.

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --force
```

Expected dry-run result: nine stable `mast:<rds_id>` tasks, all scripts present, one shared `08_run_mast.R` checksum, and output schema `yu_mast_de_v2`.

Resume in another allocation with:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast
```

### Recommended multi-node execution by RDS

The RDS tasks are independent. Assign one distinct ID to each node and never run the same ID on two nodes simultaneously:

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

On each initialized node:

```bash
RDS_ID=astrocytes  # replace with the RDS assigned to this node

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase mast \
  --rds-id "$RDS_ID" \
  --force
```

Use `--force` only for the first v2 run of that RDS. After interruption, rerun without `--force`. Resume must skip only v2 artifacts whose code, config, inputs, schemas, byte counts, and SHA-256 values still match.

### Run the complete Yu comparison

After all nine tasks validate:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_compare_yu_table_s1.R \
  --config config/minerva_shared.yml \
  --yu-supplement docs/yu_paper/ALZ-22-e71463-s002.xlsx
```

### Validate Minerva production

```bash
LD_PRELOAD="$MKL_PRELOAD" Rscript -e '
root <- "results/minerva_production/08_mast"
scientific_files <- list.files(
  root, pattern = "[.]yu_mast_de_status[.]tsv$", full.names = TRUE)
manifest_files <- list.files(
  root, pattern = "[.]yu_mast_contrast_manifest[.]tsv$", full.names = TRUE)
contrast_files <- list.files(
  root, pattern = "[.]yu_mast_contrast_status[.]tsv$", full.names = TRUE)
check_files <- list.files(
  root, pattern = "[.]yu_mast_de_checks[.]tsv$", full.names = TRUE)
controller_files <- list.files(
  "results/minerva_production/status",
  pattern = "^mast__.*[.]tsv$", full.names = TRUE)

stopifnot(
  length(scientific_files) == 9L,
  length(manifest_files) == 9L,
  length(contrast_files) == 9L,
  length(check_files) == 9L,
  length(controller_files) == 9L)

scientific <- do.call(rbind, lapply(scientific_files, read.delim))
manifest <- do.call(rbind, lapply(manifest_files, read.delim))
contrasts <- do.call(rbind, lapply(contrast_files, read.delim))
checks <- do.call(rbind, lapply(check_files, read.delim))
controller <- do.call(rbind, lapply(controller_files, read.delim))
comparison_checks <- read.delim(file.path(
  root, "yu_table_s1_validation", "yu_table_s1_comparison_checks.tsv"))
comparison_status <- read.delim(file.path(
  root, "yu_table_s1_validation", "yu_table_s1_comparison_status.tsv"))

print(table(contrasts$terminal_status))
print(comparison_status)
stopifnot(
  all(scientific$schema_version == "yu_mast_de_status_v2"),
  all(scientific$validation_status == "validated_complete"),
  all(scientific$analysis_population == "yu_all_cohort_included_nuclei"),
  nrow(manifest) == 324L,
  nrow(contrasts) == 324L,
  length(unique(manifest$cell_type_high_resolution)) == 54L,
  length(unique(manifest$yu_contrast)) == 6L,
  !anyDuplicated(manifest$contrast_id),
  !any(contrasts$terminal_status == "failed"),
  all(contrasts$terminal_status %in% c("validated_complete", "not_estimable")),
  all(checks$passed),
  all(controller$validation_status == "validated_complete"),
  all(controller$exit_code == 0L),
  all(comparison_checks$passed),
  comparison_status$alignment_tier %in% c("method_equivalent", "exact"))

cat("Phase 08 Yu-compatible Minerva production validated successfully\n")
'
```

### Required Minerva output check

- nine v2 scientific and controller statuses;
- exactly 54 fine cell types, six Yu contrasts, and 324 manifest/status rows;
- every estimable comparison completed and every non-estimable row has a reason;
- no failed comparison and no duplicate result key;
- all checks and artifact hashes pass;
- normalized RDS hashes remain unchanged;
- statuses contain no Phase 07 hash;
- a complete checksum-validated Table S1 comparison bundle exists;
- alignment is at least `method_equivalent` before downstream promotion.

## Yu alignment acceptance criteria

### Structural gate

- 54 fine cell types and six Yu labels;
- exactly 324 planned comparisons with terminal statuses;
- completed zero-DEG results distinguishable from failed or missing fits;
- non-estimable rows have explicit reasons;
- unique `(cell type, Yu contrast, gene)` keys;
- 118,297 unique DEG keys parsed from Table S1.

### Method-equivalent gate

Minimum promotion targets:

- shared-call log2FC direction agreement at least 99.9%;
- shared-call Pearson log2FC correlation at least 0.995;
- median absolute shared-call log2FC difference at most 0.01;
- Table S1 DEG recall at least 95%;
- Table S1 DEG precision at least 95%;
- exact-call Jaccard index at least 90%.

### Exact-reproduction target

The preferred result is:

- exactly 118,297 DEG keys;
- no Yu-only or Phase-08-only keys;
- identical directions;
- log2FC, detection fractions, raw p-values, and adjusted p-values equal within predeclared tolerances.

The paper identifies Seurat v5 but does not fully pin every package version. Minerva currently uses Seurat 5.5.1 and MAST 1.28.0. If method equivalence passes but exact reproduction does not, retain the model and report the residual causes. Do not alter thresholds after seeing Table S1.

## Residual mismatch investigation order

If production is below the method-equivalent gate, investigate:

1. exact cell membership and AD/NCI direction;
2. the Phase 05 RNA `data` layer;
3. `nCount_RNA`, age, PMI, scaling, missingness, and capping;
4. the `min.pct` feature universe and BH adjustment universe;
5. gene-symbol and Ensembl mapping, including duplicate symbols;
6. R, Seurat, SeuratObject, and MAST version differences.

Classify mismatches as: comparison not estimable, gene not returned, FDR failure, fold-change failure, both threshold failures, direction difference, Yu-only call, or Phase-08-only call.

## Downstream handoff

After the structural and method-equivalent gates pass:

1. keep `08_mast/` as the active Phase 08 path and allow consumers to select only `*.yu_mast_*` v2 artifacts;
2. rerun Phase 09 pathway analysis;
3. rerun Phase 10 Yu-style similarity analysis;
4. rerun Phase 11 multiple-testing summaries;
5. rerun Phase 12 MAST-versus-pseudobulk sensitivity analysis;
6. rerun Phase 14 validation and Phase 15 figures.

Phase 10 must represent a tested non-DEG state as zero rather than dropping the dimension. The full Yu design gives 162 female pairwise, 108 male pairwise, and 108 cross-sex dimensions across 54 cell types.

## Completion criteria

The new Phase 08 is complete when:

- v1 code paths and outputs are no longer consumed;
- local Vasculature produces 30 explicit v2 status rows;
- Minerva produces 324 explicit v2 status rows across 54 fine cell types;
- Phase 08 reads no Phase 07 artifact;
- all numerical, provenance, task, and artifact checks pass;
- Table S1 comparison is reproducible;
- alignment is at least `method_equivalent` and residual differences are attributed;
- downstream phases consume only `08_mast/*.yu_mast_*` v2 artifacts.
