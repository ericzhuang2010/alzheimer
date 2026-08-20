# SEA-AD Broad-Cell Pseudobulk DEG Processing Plan

**Status:** implemented and executed locally; VH00–VH08 are `validated_complete`  
**Date:** 2026-08-19  
**Scope endpoint:** validated genome-wide SEA-AD differential-expression results for seven primary pooled contrasts and the estimable sex/APOE-specific secondary contrasts  
**Production output root:** `results/validation_human/`  
**Implementation root:** `scripts/validation_human/`

**Execution outcome:** VH05 processed all 1,395,601 nuclei locally in 6 minutes 40 seconds with approximately 748 MiB peak RAM and exact selected-UMI conservation. Minerva was not needed. VH08 completed seven primary and 20 eligible secondary DEG results while retaining 22 secondary slots as explicitly not estimable.

## 1. Objective and endpoint

This plan processes the SEA-AD DLPFC single-nucleus RNA-seq H5AD into donor-level broad-cell pseudobulk counts and then fits donor-aware edgeR differential-expression models.

The required scientific endpoint is:

```text
7 primary genome-wide DEG result sets
    = 7 broad cell populations × pooled Dementia-versus-No-dementia

20 predicted secondary genome-wide DEG result sets
    = Female e33 in 7 broad populations
    + Male e33 in 7 broad populations
    + Female e4 in 6 broad populations

22 planned secondary slots recorded as not_estimable
    = Female e2 in 7 broad populations
    + Male e2 in 7 broad populations
    + Male e4 in 7 broad populations
    + Female e4 in vasculature
```

The exact number of completed secondary contrasts remains subject to the frozen eligibility checks after pseudobulk construction. Based on the audited SEA-AD metadata and a threshold of at least 20 nuclei per donor-cell population and at least five donors per disease arm, the expected number is 20.

Each completed result set will contain genome-wide effect estimates, not only significant genes:

- gene symbol and harmonized identifiers;
- `logFC`, with positive values meaning higher expression in dementia;
- average abundance/logCPM;
- edgeR quasi-likelihood statistic;
- raw p-value;
- within-contrast BH FDR;
- explicit tested/filtered status; and
- an effect-direction field derived from the sign of `logFC`.

AD-up and AD-down are not separate DEG fits. They are derived from the signed result of one disease contrast.

### Out of scope for this plan

The following start only after the DEG endpoint is validated:

- testing frozen Phase 18 target modules;
- KDA replay;
- constructing AD-up/AD-down KDA query lists;
- testing all 24 SEA-AD subclasses or 131 supertypes;
- fine-cell cross-validation;
- pathway enrichment; and
- publication figures.

## 2. Frozen scientific decisions

### 2.1 Statistical unit

The independent unit is one donor. Raw UMIs will be summed into one count profile for each:

```text
donor × broad cell population
```

Nuclei will never be treated as independent human replicates.

### 2.2 Expression input

Use only:

```text
layers["UMIs"]
```

The normalized H5AD `X` matrix, scVI coordinates, UMAP coordinates, and neighbor graphs are not DEG inputs.

### 2.3 Primary assay population

The primary analysis uses `method = 10Xv3.1` only. The reference donors use a different chemistry, and the 10xMulti GEX nuclei are reserved for a later sensitivity analysis.

### 2.4 Donor cohort

The expected cohort is 78 donors:

- start with 83 SEA-AD donors;
- exclude three neurotypical reference donors;
- exclude two APOE `2/4` donors to match the ROSMAP grouping rule; and
- require complete cognitive status, sex, APOE, age at death, PMI, and study.

APOE grouping is frozen as:

```text
e2  = 2/2 or 2/3
e33 = 3/3
e4  = 3/4 or 4/4
2/4 = excluded
```

The primary phenotype is:

```text
Dementia versus No dementia
```

The SEA-AD `No dementia` category must not be renamed `NCI`; it is the closest available cognitive comparator but is not guaranteed to equal the ROSMAP NCI definition.

### 2.5 Broad-cell mapping

The seven primary populations are frozen as:

| Validation context | SEA-AD rule |
|---|---|
| `Astrocytes` | `Subclass == "Astrocyte"` |
| `Excitatory_neurons` | `Class == "Neuronal: Glutamatergic"` |
| `Inhibitory_neurons` | `Class == "Neuronal: GABAergic"` |
| `Microglia` | `Subclass == "Microglia-PVM"`, excluding `Lymphocyte` and `Monocyte` supertypes |
| `OPCs` | `Subclass == "OPC"` |
| `Oligodendrocytes` | `Subclass == "Oligodendrocyte"` |
| `Vasculature_cells` | `Subclass` in `Endothelial`, `VLMC` |

Each selected nucleus belongs to exactly one broad context.

### 2.6 Eligibility thresholds

- Primary donor-cell eligibility: at least 20 selected nuclei.
- Sensitivity flag: at least 50 selected nuclei.
- A direct disease contrast requires at least five eligible dementia donors and five eligible no-dementia donors.
- A model must be full rank.
- A contrast that fails a gate is written as `not_estimable`; it is never silently omitted and never converted to a null result.

### 2.7 DEG models

For each broad context, fit two models.

Primary pooled model:

```text
~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study
```

The primary coefficient/contrast is Dementia minus No dementia.

Secondary group model:

```text
~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled + study
```

The six planned direct contrasts are Dementia minus No dementia within Female/Male × e2/e33/e4. Only eligible contrasts are tested.

Within each broad context, a single frozen `filterByExpr` gene universe will be created from all primary-eligible donors using disease status as the grouping variable. The same filtered gene universe will be used for the pooled and secondary models in that context. TMM normalization and robust edgeR quasi-likelihood fitting will be used.

BH correction is applied separately within each completed genome-wide contrast.

## 3. Repository end state

### 3.1 Files planned under `scripts/validation_human/`

```text
scripts/validation_human/
├── README.md
├── seaad_deg_config.yml
├── seaad_common.py
├── 00_check_environment.py
├── 01_audit_inputs.py
├── 02_build_donor_cohort.py
├── 03_harmonize_genes.py
├── 04_build_nucleus_group_manifest.py
├── 05_stream_broad_pseudobulk.py
├── 06_validate_pseudobulk.R
├── 07_build_contrast_manifest.R
├── 08_run_broad_deg.R
└── minerva/
    └── 05_stream_broad_pseudobulk.lsf
```

All new scientific processing code is confined to `scripts/validation_human/`. Existing ROSMAP scripts are read as references but are not modified or called as hidden dependencies.

### 3.2 Planned results tree

```text
results/validation_human/
├── 00_environment/
├── 01_audit/
├── 02_cohort/
├── 03_genes/
├── 04_cell_manifest/
├── 05_pseudobulk/
├── 06_pseudobulk_qc/
├── 07_contrasts/
└── 08_deg/
    ├── primary/
    ├── secondary/
    └── model_objects/
```

### 3.3 Added, changed, removed, and preserved

At full implementation:

- **Added:** the scripts, configuration, LSF job, phase outputs, checks, statuses, and final DEG release described in this document.
- **Changed:** no existing ROSMAP scientific script, config, result, or documentation file needs to change.
- **Removed:** no existing repository file and no scientific intermediate is deleted by the pipeline.
- **Preserved read-only:** the SEA-AD H5AD and metadata CSV; both remain byte-for-byte unchanged.
- **Temporary behavior:** atomic `.tmp.<pid>` files may be created beside an output and are renamed only after a successful write. A failed temporary file may be reported for manual cleanup, but production code must not recursively delete directories.

### 3.4 Namespace isolation contract

At implementation time, the following are hard requirements:

- All new executable code, configuration, helper modules, README files, and Minerva job files must be created only below `scripts/validation_human/`.
- All new scientific results, intermediate files, checkpoints, smoke-test outputs, logs, status files, manifests, model objects, and temporary files must be created only below `results/validation_human/`.
- Files outside those two roots are inputs or references and must be opened read-only; existing ROSMAP scripts and results must never be overwritten, renamed, moved, or deleted.
- Every phase must canonicalize its configured output path and fail before writing if that path is not inside `results/validation_human/`.
- Output paths containing `..` or resolving through a symlink outside the validation result root must be rejected.
- Pipeline-generated logs, plots, `.RData`, `Rplots.pdf`, caches, and temporary files must not be written to the repository root, existing result directories, or existing script directories.
- Local and Minerva commands must use the same isolated relative roots under their respective repository checkout.

The addition of this plan itself creates only:

```text
docs/validation_human/seaad_deg_processing_plan.md
```

It does not yet create the planned scripts or scientific results.

## 4. Execution overview

The current local machine has 15 GiB RAM, 16 CPU cores, and adequate disk space. Most phases are small because they use metadata or the compact donor-level matrix.

| Phase | Main task | Preferred execution | Minerva required? |
|---|---|---|---|
| VH00 | Environment/config freeze | Local | No |
| VH01 | H5AD/CSV audit | Local | No |
| VH02 | Donor cohort | Local | No |
| VH03 | Gene harmonization | Local | No |
| VH04 | Nucleus-to-group manifest | Local | No |
| VH05 | Stream 8 billion UMI entries into pseudobulk | Local first; Minerva fallback | No; Minerva strongly recommended if local is too slow or unstable |
| VH06 | Pseudobulk validation/export | Local | No |
| VH07 | Contrast eligibility/design audit | Local | No |
| VH08 | edgeR DEG models, complete-grid release, and final checks | Local | No |

No phase is scientifically required to run on Minerva. VH05 is the only phase for which Minerva is a likely operational requirement: the UMI CSR layer contains 7,989,685,110 stored entries, representing approximately 17.34 GiB of gzip-compressed HDF5 storage and 89.30 GiB of logical count/index data. The block-streaming implementation is designed to fit within local memory, so VH05 will be attempted locally first. If the complete local run reaches `validated_complete` and passes exact conservation and checksum gates, it must not be repeated on Minerva. Minerva is the fallback for excessive runtime, repeated interruption, memory pressure, or an otherwise unstable local production run.

## 5. Common local invocation

After implementation, run local commands from the repository root:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
export SEAAD_DEG_CONFIG=scripts/validation_human/seaad_deg_config.yml
export PYTHONDONTWRITEBYTECODE=1
```

Python phases use the project virtual environment:

```bash
.venv/bin/python <script> --config "$SEAAD_DEG_CONFIG"
```

R phases use the repository R environment:

```bash
Rscript <script> --config "$SEAAD_DEG_CONFIG"
```

Every script must support `--help`, fail on unknown arguments, write a one-row status file, and use nonzero exit status on a failed gate.

## 6. VH00 — Freeze configuration and check environments

### Purpose

Create the single machine-readable contract used by every later phase and verify that the local and Minerva software can read/write the required formats.

### Inputs

- `data/seaad/SEAAD_A9_RNAseq_final-nuclei.2024-02-13.h5ad`
- `data/seaad/SEAAD_A9_RNAseq_final-nuclei_metadata.2024-02-13.csv`
- repository `.venv`
- repository R/renv environment
- frozen decisions in Section 2

### Planned repository changes

- **Create:** `scripts/validation_human/README.md`
- **Create:** `scripts/validation_human/seaad_deg_config.yml`
- **Create:** `scripts/validation_human/seaad_common.py`
- **Create:** `scripts/validation_human/00_check_environment.py`
- **Create outputs:** `results/validation_human/00_environment/`
- **Modify:** nothing existing
- **Delete:** nothing

The config will contain input paths, output root, expected dimensions, cohort rules, broad mappings, thresholds, formulas, random seeds, and expected contrast counts. Paths may be overridden on Minerva through explicit CLI options; scientific rules may not be overridden silently.

### Processing and checks

- Verify Python, h5py, NumPy, SciPy, pandas, and PyYAML.
- Verify R, edgeR, limma, Matrix, data.table, yaml, and digest.
- Verify both input files exist and are readable.
- Record software versions, git revision, host, date, config checksum, and input sizes.
- Refuse to run if the configured output root is outside `results/validation_human`.

### Outputs

```text
results/validation_human/00_environment/environment.tsv
results/validation_human/00_environment/config_snapshot.yml
results/validation_human/00_environment/environment_checks.tsv
results/validation_human/00_environment/status.tsv
```

### Local command

```bash
.venv/bin/python scripts/validation_human/00_check_environment.py \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

All required packages and input paths pass, and `status.tsv` contains `validated_complete`.

## 7. VH01 — Audit the SEA-AD inputs

### Purpose

Establish the structural and semantic integrity of the H5AD and its companion CSV without loading the expression matrix into memory.

### Inputs

- VH00 config snapshot and validated status
- SEA-AD H5AD
- SEA-AD metadata CSV

### Planned repository changes

- **Create:** `scripts/validation_human/01_audit_inputs.py`
- **Create outputs:** `results/validation_human/01_audit/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing and checks

- Verify 1,395,601 observations and 36,601 genes.
- Verify `X` is CSR and marked `ln(UP10K+1)`.
- Verify `layers/UMIs` is CSR with the same shape, indices, and row pointers as `X`.
- Sample values to confirm that the UMI layer is nonnegative and integer-valued despite float32 storage.
- Verify CSV row count, 133 columns, exact header agreement, and matching first/last nucleus identifiers.
- Inventory required observation fields and categorical levels.
- Verify unique gene symbols and record that `gene_ids` duplicates symbols rather than Ensembl IDs.
- Record dataset/object checksums. A full H5AD SHA-256 may be optional because it is I/O-intensive; if omitted, record size, mtime, HDF5 structure digest, and a sampled-content digest.

### Outputs

```text
results/validation_human/01_audit/h5ad_structure.tsv
results/validation_human/01_audit/obs_schema.tsv
results/validation_human/01_audit/category_inventory.tsv
results/validation_human/01_audit/gene_inventory_raw.tsv
results/validation_human/01_audit/csv_h5ad_alignment.tsv
results/validation_human/01_audit/audit_checks.tsv
results/validation_human/01_audit/artifacts.tsv
results/validation_human/01_audit/status.tsv
```

### Local command

```bash
.venv/bin/python scripts/validation_human/01_audit_inputs.py \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

The H5AD and CSV dimensions agree, required datasets and metadata fields exist, and the UMI layer passes sampled raw-count checks.

## 8. VH02 — Build the authoritative donor cohort

### Purpose

Collapse repeated nucleus metadata into one verified donor table and apply the frozen cohort and phenotype rules.

### Inputs

- VH01 validated status and category inventory
- H5AD `obs` donor and clinical fields
- frozen cohort rules in the config

### Planned repository changes

- **Create:** `scripts/validation_human/02_build_donor_cohort.py`
- **Create outputs:** `results/validation_human/02_cohort/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing

- Extract one row per `Donor ID`.
- Verify that donor-level clinical fields do not vary within a donor.
- Convert numeric age and PMI safely; distinguish nonnumeric reference labels from missing data.
- Derive `diagnosis`, `sex`, `apoe_group`, scaled age, and scaled PMI.
- Apply the reference and APOE `2/4` exclusions.
- Preserve the source values beside every derived field.
- Tabulate diagnosis × sex × APOE and diagnosis × pathology.

### Expected donor counts

```text
83 source donors
- 3 neurotypical reference donors
- 2 APOE 2/4 donors
= 78 primary analysis donors

37 Dementia
41 No dementia
```

### Outputs

```text
results/validation_human/02_cohort/donor_metadata_all.tsv
results/validation_human/02_cohort/donor_cohort_primary.tsv
results/validation_human/02_cohort/cohort_exclusion_flow.tsv
results/validation_human/02_cohort/donor_group_counts.tsv
results/validation_human/02_cohort/cognitive_pathology_crosstab.tsv
results/validation_human/02_cohort/donor_invariance_checks.tsv
results/validation_human/02_cohort/cohort_checks.tsv
results/validation_human/02_cohort/status.tsv
```

### Local command

```bash
.venv/bin/python scripts/validation_human/02_build_donor_cohort.py \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

Exactly one internally consistent row exists for every donor, all 78 included donors have complete model covariates, and expected group counts match the audited source.

## 9. VH03 — Harmonize genes and freeze feature order

### Purpose

Create the immutable feature order used by pseudobulk and DEG outputs and attach stable identifiers where possible.

### Inputs

- VH01 raw gene inventory
- existing `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz`
- existing `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt`
- existing MitoCarta and mitochondrial-reference artifacts

### Planned repository changes

- **Create:** `scripts/validation_human/03_harmonize_genes.py`
- **Create outputs:** `results/validation_human/03_genes/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing

- Preserve the exact 36,601 H5AD symbol order as the matrix row identity.
- Map symbols to approved HGNC symbols and GENCODE v44 IDs when unambiguous.
- Mark exact, alias, ambiguous, and unresolved mappings explicitly.
- Annotate mtDNA protein-coding genes and MitoCarta membership.
- Calculate a deterministic feature-order checksum used by VH05-VH08.
- Never drop or merge an H5AD feature during pseudobulk construction.

### Outputs

```text
results/validation_human/03_genes/gene_annotation_master.tsv
results/validation_human/03_genes/gene_aliases_used.tsv
results/validation_human/03_genes/gene_mapping_ambiguities.tsv
results/validation_human/03_genes/feature_order.tsv
results/validation_human/03_genes/gene_checks.tsv
results/validation_human/03_genes/status.tsv
```

### Local command

```bash
.venv/bin/python scripts/validation_human/03_harmonize_genes.py \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

The feature order contains exactly 36,601 unique source features, its checksum is frozen, and no ambiguous mapping changes the original matrix row identity.

## 10. VH04 — Build the nucleus-to-pseudobulk group manifest

### Purpose

Select the nuclei used by the primary analysis and create a compact row-aligned mapping from each H5AD observation to one donor × broad-context pseudobulk group.

### Inputs

- VH01 validated observation schema
- VH02 primary donor cohort
- VH03 feature-order status
- H5AD observation fields:
  - `Donor ID`
  - `method`
  - `Used in analysis`
  - `Class`
  - `Subclass`
  - `Supertype`
  - nucleus index

### Planned repository changes

- **Create:** `scripts/validation_human/04_build_nucleus_group_manifest.py`
- **Create outputs:** `results/validation_human/04_cell_manifest/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing

- Require `Used in analysis == True`.
- Require `method == 10Xv3.1`.
- Require donor membership in the VH02 primary cohort.
- Apply the seven frozen broad mapping rules.
- Exclude Microglia-PVM nuclei labeled `Lymphocyte` or `Monocyte` from the primary Microglia context.
- Assign each selected nucleus one integer pseudobulk-group code.
- Assign excluded nuclei code `-1` and an explicit exclusion reason.
- Freeze the H5AD observation-order checksum so VH05 cannot aggregate a misaligned mapping.

### Outputs

```text
results/validation_human/04_cell_manifest/nucleus_to_group_code.npy
results/validation_human/04_cell_manifest/nucleus_selection.tsv.gz
results/validation_human/04_cell_manifest/pseudobulk_group_manifest.tsv
results/validation_human/04_cell_manifest/donor_context_nucleus_counts.tsv
results/validation_human/04_cell_manifest/nucleus_exclusion_summary.tsv
results/validation_human/04_cell_manifest/observation_order_checksum.tsv
results/validation_human/04_cell_manifest/cell_manifest_checks.tsv
results/validation_human/04_cell_manifest/status.tsv
```

The `.npy` array is the computational handoff to VH05; the compressed TSV is the auditable human-readable record.

### Local command

```bash
.venv/bin/python scripts/validation_human/04_build_nucleus_group_manifest.py \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

- Every selected nucleus has exactly one group.
- No excluded donor or non-10Xv3.1 nucleus is selected.
- All seven contexts are present.
- All 78 donors are represented before the 20-nucleus eligibility filter.
- Observation-order checksums agree with VH01.

## 11. VH05 — Stream raw UMIs into broad pseudobulk counts

### Purpose

Aggregate the raw UMI CSR layer without materializing the full 1.4-million × 36,601 matrix.

### Inputs

- SEA-AD H5AD `layers/UMIs/{data,indices,indptr}`
- VH03 frozen feature order
- VH04 `nucleus_to_group_code.npy`
- VH04 pseudobulk group manifest
- VH00 config snapshot

### Planned repository changes

- **Create:** `scripts/validation_human/05_stream_broad_pseudobulk.py`
- **Create:** `scripts/validation_human/minerva/05_stream_broad_pseudobulk.lsf`
- **Create outputs:** `results/validation_human/05_pseudobulk/`
- **Modify:** nothing existing
- **Delete:** nothing

### Streaming algorithm

1. Open only the UMI CSR datasets through h5py.
2. Read bounded consecutive observation blocks.
3. Verify integer-valued nonnegative counts and valid feature indices.
4. Aggregate each block into donor-context groups using sparse operations.
5. Add block totals to an on-disk/checkpointed pseudobulk accumulator.
6. Record source UMI and selected-nucleus totals for conservation checks.
7. Write final genes × pseudobulk-samples counts in frozen VH03 feature order.

The implementation must never load `X`, the complete UMI `data` vector, or the complete UMI `indices` vector into memory.

### Outputs

```text
results/validation_human/05_pseudobulk/seaad_broad_pseudobulk_counts.tsv.gz
results/validation_human/05_pseudobulk/seaad_broad_pseudobulk_samples.tsv
results/validation_human/05_pseudobulk/block_progress.tsv
results/validation_human/05_pseudobulk/checkpoint_latest.npz
results/validation_human/05_pseudobulk/count_conservation.tsv
results/validation_human/05_pseudobulk/pseudobulk_checks.tsv
results/validation_human/05_pseudobulk/artifacts.tsv
results/validation_human/05_pseudobulk/status.tsv
results/validation_human/05_pseudobulk/logs/
```

The counts table has one `gene` column followed by pseudobulk sample columns. The sample table defines the exact column order.

### Local smoke test

The local smoke test is deliberately nonproduction and writes outside the production phase directory:

```bash
.venv/bin/python scripts/validation_human/05_stream_broad_pseudobulk.py \
  --config "$SEAAD_DEG_CONFIG" \
  --max-observations 10000 \
  --output-dir results/validation_human/smoke/05_pseudobulk
```

It must confirm block parsing, group assignment, count conservation, and resumability. It cannot promote production status.

### Local production command — try first

The local production run writes to the canonical VH05 output directory. A conservative block size of 1,000 observations limits temporary CSR memory. The process is resumable, so rerunning the same command continues from `checkpoint_latest.npz` rather than restarting.

Run from a persistent terminal such as `tmux`:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
export SEAAD_DEG_CONFIG=scripts/validation_human/seaad_deg_config.yml
mkdir -p results/validation_human/05_pseudobulk/logs
set -o pipefail
/usr/bin/time -v \
  .venv/bin/python scripts/validation_human/05_stream_broad_pseudobulk.py \
  --config "$SEAAD_DEG_CONFIG" \
  --block-observations 1000 \
  --resume \
  2>&1 | tee results/validation_human/05_pseudobulk/logs/local_production.log
```

If interrupted, run the same command again. Do not delete the checkpoint. After the command exits successfully, inspect:

```bash
sed -n '1,40p' results/validation_human/05_pseudobulk/status.tsv
sed -n '1,120p' results/validation_human/05_pseudobulk/pseudobulk_checks.tsv
sed -n '1,120p' results/validation_human/05_pseudobulk/count_conservation.tsv
```

Proceed directly to VH06 when the status is `validated_complete` and all checks pass. Do not submit the Minerva job in that case.

### Minerva fallback production command

Use Minerva only if the local production run is impractically slow, repeatedly interrupted, exceeds the safe local-memory envelope, or fails for a resource-related reason. The planned LSF request is one CPU job with four slots, approximately 64 GiB total memory, and a 24-hour walltime. GPU resources are not needed.

The planned LSF file must explicitly keep scheduler stdout and stderr inside the isolated validation result root:

```text
#BSUB -oo /sc/arion/work/zhuane01/alzheimer/results/validation_human/05_pseudobulk/logs/minerva_%J.out
#BSUB -eo /sc/arion/work/zhuane01/alzheimer/results/validation_human/05_pseudobulk/logs/minerva_%J.err
```

Before submission, the repository and VH00-VH04 outputs are assumed available at:

```text
/sc/arion/work/zhuane01/alzheimer
```

The H5AD is assumed available at the same configured relative path as locally. Large-file transfer should use Globus when it is not already present.

Submit with:

```bash
ssh zhuane01@minerva.hpc.mssm.edu
cd /sc/arion/work/zhuane01/alzheimer
mkdir -p results/validation_human/05_pseudobulk/logs
bsub < scripts/validation_human/minerva/05_stream_broad_pseudobulk.lsf
```

Monitor with:

```bash
bjobs
bpeek <JOB_ID>
```

The LSF script will run the equivalent of:

```bash
/sc/arion/work/zhuane01/envs/alzheimer-seaad/bin/python \
  scripts/validation_human/05_stream_broad_pseudobulk.py \
  --config scripts/validation_human/seaad_deg_config.yml \
  --resume
```

The exact Python executable is frozen in the config during VH00. If that environment does not yet exist, create it under `/sc/arion/work/zhuane01/envs/` using a Miniforge module and install only Python, h5py, NumPy, SciPy, pandas, and PyYAML.

If Minerva was used, copy the compact pseudobulk outputs back locally after successful completion. For these outputs, `rsync` is acceptable:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
rsync -av --partial \
  zhuane01@minerva.hpc.mssm.edu:/sc/arion/work/zhuane01/alzheimer/results/validation_human/05_pseudobulk/ \
  results/validation_human/05_pseudobulk/
```

### Completion gate

- Every input row was visited exactly once.
- Selected source UMI totals equal pseudobulk UMI totals exactly.
- Counts are finite, nonnegative integers.
- Gene and sample order checksums match VH03 and VH04.
- The production status is `validated_complete`, not `smoke_complete`.

## 12. VH06 — Validate and export the pseudobulk bundle

### Purpose

Convert the portable VH05 tables into the compact R bundle consumed by edgeR and independently validate all count, sample, and eligibility relationships.

### Inputs

- VH05 production counts and sample table
- VH05 conservation table and validated status
- VH02 donor cohort
- VH03 feature order
- VH04 donor-context nucleus counts

### Planned repository changes

- **Create:** `scripts/validation_human/06_validate_pseudobulk.R`
- **Create outputs:** `results/validation_human/06_pseudobulk_qc/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing and checks

- Read the counts table and verify gene/sample order.
- Require nonnegative integer counts and nonzero library sizes.
- Verify donor and clinical joins by ID, never row order.
- Recalculate nuclei, library size, and mitochondrial UMI summaries.
- Create `primary_eligible = nuclei >= 20` and `sensitivity_eligible = nuclei >= 50`.
- Preserve ineligible donor-context profiles in the bundle with explicit reasons.
- Save a genes × samples count matrix and matching sample table in one RDS.

### Expected primary coverage

- 78 eligible donor profiles in each of Astrocytes, Excitatory neurons, Inhibitory neurons, Microglia, OPCs, and Oligodendrocytes.
- 76 eligible donor profiles in Vasculature.

These are expectations, not hard-coded substitutions. A mismatch must be explained in QC rather than overwritten.

### Outputs

```text
results/validation_human/06_pseudobulk_qc/seaad_broad_pseudobulk.rds
results/validation_human/06_pseudobulk_qc/pseudobulk_samples.tsv
results/validation_human/06_pseudobulk_qc/donor_context_eligibility.tsv
results/validation_human/06_pseudobulk_qc/library_qc.tsv
results/validation_human/06_pseudobulk_qc/count_conservation_recheck.tsv
results/validation_human/06_pseudobulk_qc/pseudobulk_qc_checks.tsv
results/validation_human/06_pseudobulk_qc/status.tsv
```

### Local command

```bash
Rscript scripts/validation_human/06_validate_pseudobulk.R \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

The RDS reloads successfully, counts and metadata columns align exactly, conservation passes independently, and the expected broad-context donor coverage is either reproduced or accompanied by a blocking discrepancy report.

## 13. VH07 — Build the contrast manifest and audit designs

### Purpose

Declare every planned primary and secondary result before fitting expression models and decide estimability using donor counts and matrix rank alone.

### Inputs

- VH06 validated pseudobulk bundle
- VH02 cohort rules
- frozen formulas and thresholds in the config

### Planned repository changes

- **Create:** `scripts/validation_human/07_build_contrast_manifest.R`
- **Create outputs:** `results/validation_human/07_contrasts/`
- **Modify:** nothing existing
- **Delete:** nothing

### Processing

For each of seven contexts:

- subset `primary_eligible == TRUE` profiles;
- construct and rank-check the pooled design;
- construct and rank-check the 12-level disease × sex × APOE group design;
- create one pooled primary contrast;
- create six planned direct secondary contrasts;
- count required donors for each arm;
- label each slot `eligible` or with a precise non-estimability reason; and
- store exact contrast coefficient vectors.

### Expected manifest

```text
7 primary slots: all eligible
42 secondary slots:
    20 eligible
    22 not_estimable
49 total planned status rows
```

### Outputs

```text
results/validation_human/07_contrasts/contrast_manifest.tsv
results/validation_human/07_contrasts/contrast_eligibility.tsv
results/validation_human/07_contrasts/design_columns.tsv
results/validation_human/07_contrasts/design_rank_checks.tsv
results/validation_human/07_contrasts/donor_counts_by_required_group.tsv
results/validation_human/07_contrasts/contrast_checks.tsv
results/validation_human/07_contrasts/status.tsv
```

### Local command

```bash
Rscript scripts/validation_human/07_build_contrast_manifest.R \
  --config "$SEAAD_DEG_CONFIG"
```

### Completion gate

All 49 slots are present exactly once, all seven primary designs are full rank, every eligible contrast meets donor thresholds, and every ineligible contrast has an auditable reason.

## 14. VH08 — Fit broad-cell edgeR DEG models and build the final release

### Purpose

Fit every VH07-eligible primary and secondary contrast, then assemble and validate the complete, self-describing DEG release in the same phase.

### Inputs

- VH06 pseudobulk RDS and validated status
- VH07 complete 49-slot contrast manifest, coefficient vectors, eligibility table, and validated status
- VH03 immutable 36,601-feature inventory, feature order, and annotation tables
- frozen edgeR and release settings from the config
- prior status and artifact tables needed for provenance

### Planned repository changes

- **Create:** `scripts/validation_human/08_run_broad_deg.R`
- **Create outputs:** `results/validation_human/08_deg/`
- **Folded scope:** complete-grid assembly, checksums, provenance, and endpoint validation run inside VH08; no separate release phase or output directory is planned
- **Modify:** nothing existing
- **Delete:** nothing

### Model fitting per broad context

1. Subset primary-eligible donor profiles.
2. Construct an edgeR `DGEList` from raw pseudobulk counts.
3. Freeze the context gene universe with `filterByExpr`, grouping by disease status.
4. Recalculate library sizes and apply TMM normalization.
5. Fit the pooled design with robust dispersion estimation and `glmQLFit(..., robust = TRUE)`.
6. Test the primary Dementia-minus-No-dementia contrast.
7. Fit the full-rank secondary group design over the same samples and gene universe.
8. Test only VH07-eligible direct sex/APOE contrasts.
9. Apply BH FDR separately within each completed contrast.
10. Write explicit status rows for all untested slots.

The result direction is always:

```text
positive logFC = higher in Dementia
negative logFC = lower in Dementia
```

### Final release assembly within VH08

11. Combine the model-native tested rows for all completed contrasts.
12. Join each completed contrast to the immutable 36,601-feature inventory to create a complete feature-by-completed-contrast grid.
13. Label genes outside the context-specific `filterByExpr` universe as `filtered`, not as nonsignificant and not with fabricated zero statistics.
14. Preserve non-estimable contrasts only in the contrast status table; do not generate gene-level rows for them.
15. Add direction labels from `logFC` without imposing an extra DEG significance threshold.
16. Verify exactly seven completed primary contrasts and the VH07-predicted completed secondary count, expected to be 20.
17. Write SHA-256 checksums, provenance, a machine-readable artifact manifest, and the final completion status.

### Outputs

Per-contrast model-native results:

```text
results/validation_human/08_deg/primary/<context>__Dementia_vs_No_dementia.tsv.gz
results/validation_human/08_deg/secondary/<context>__<sex>__<apoe>__Dementia_vs_No_dementia.tsv.gz
```

Combined model-native tested rows:

```text
results/validation_human/08_deg/primary_deg_all.tsv.gz
results/validation_human/08_deg/secondary_deg_all.tsv.gz
```

Final complete DEG tables for downstream validation:

```text
results/validation_human/08_deg/seaad_primary_deg_complete.tsv.gz
results/validation_human/08_deg/seaad_secondary_deg_complete.tsv.gz
```

Supporting release and audit files:

```text
results/validation_human/08_deg/seaad_deg_contrast_manifest.tsv
results/validation_human/08_deg/seaad_deg_contrast_status.tsv
results/validation_human/08_deg/seaad_deg_summary.tsv
results/validation_human/08_deg/seaad_gene_testability.tsv.gz
results/validation_human/08_deg/gene_filter_status.tsv.gz
results/validation_human/08_deg/model_diagnostics.tsv
results/validation_human/08_deg/deg_checks.tsv
results/validation_human/08_deg/artifacts.tsv
results/validation_human/08_deg/model_objects/<context>.edgeR.rds
results/validation_human/08_deg/status.tsv
```

`model_objects/` contains technical edgeR fit artifacts for reproducibility and auditing. It is not a third DEG result family; the scientific result families remain `primary/` and `secondary/`, with the two `seaad_*_deg_complete.tsv.gz` files as the final consolidated endpoint.

### Local command

```bash
Rscript scripts/validation_human/08_run_broad_deg.R \
  --config "$SEAAD_DEG_CONFIG"
```

VH08 should fit comfortably on the local machine because each context has at most 78 donor columns and 36,601 source genes. The large nucleus-level matrix is no longer opened. Minerva is optional, not required, and the same command can be used there after activating the project R environment and setting `SEAAD_DEG_CONFIG`.

### Final completion gate

The SEA-AD DEG endpoint is complete only when:

- `status.tsv` is `validated_complete`;
- exactly seven primary contrast files and seven primary result sets are complete;
- the completed secondary count matches VH07, expected to be 20;
- all expected non-estimable secondary slots remain explicit, expected to be 22 if the anticipated coverage is reproduced;
- ineligible slots have no fabricated gene statistics;
- every completed result has unique genes, finite statistics where tested, the frozen coefficient direction, and valid within-contrast BH FDR;
- complete DEG tables distinguish tested and filtered genes across the full 36,601-feature inventory;
- saved model objects reload and reproduce sampled result rows;
- every final output is traceable to input, config, code, and git checksums; and
- no raw input or prior result has been altered.

## 15. Result interpretation boundary

VH08 provides DEG evidence but does not itself validate a Phase 18 key driver. These DEG results become the input for later frozen-module validation.

In particular:

- a candidate driver does not need to be a significant DEG;
- an individual target crossing FDR is not the module-level success criterion;
- e2 and Male-e4 are expected to be unassessable, not negative replications;
- the 20 secondary results are secondary because their donor groups are smaller; and
- the seven pooled broad-cell results are the primary external human validation substrate.

## 16. Phase dependency graph

```text
VH00 environment/config
  ↓
VH01 input audit
  ├──────────────→ VH03 gene harmonization
  ↓
VH02 donor cohort
  ↓
VH04 nucleus/group manifest ← VH03 feature-order gate
  ↓
VH05 streaming pseudobulk [local first; Minerva fallback]
  ↓
VH06 pseudobulk validation [local]
  ↓
VH07 contrast/design manifest
  ↓
VH08 edgeR fitting + final 7-primary and expected-20-secondary DEG release
```
