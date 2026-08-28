# Phase 08 broad-cell DEG plan: 6 sex/APOE groups × 7 broad cell types

> Implementation status (2026-08-28): the shared scripts are implemented and
> the one-broad-cell Vasculature local pilot is `validated_complete`. See
> [local_pilot_results.md](local_pilot_results.md). Minerva production has not
> yet been launched.

## Decision summary

This branch will produce one AD-versus-NCI differential-expression result for
each of the following 42 structural categories:

```text
6 sex/APOE groups × 7 broad cell types = 42 contrasts
```

The current Phase 08 output does **not** contain these contrasts. It contains
fine-cell-type MAST contrasts (54 fine types × 6 groups). A broad-cell DEG
cannot be obtained by summing or averaging the fine-type log fold changes,
p-values, or DEG lists.

The recommended primary analysis is instead:

1. start from the existing Phase 07 donor-by-fine-cell-type raw-count
   pseudobulk bundles;
2. sum raw counts across the fine cell types belonging to the same broad cell
   type for each donor;
3. recompute sample eligibility at the donor-by-broad-cell level;
4. fit seven donor-level edgeR quasi-likelihood models; and
5. extract six stratum-specific AD-minus-NCI contrasts from each model.

This gives the requested 42 broad-cell DEG results while retaining the donor
as the biological replicate. It also avoids loading the three large
excitatory Seurat objects together.

The new scientific output will be stored only under:

```text
results/minerva_production/08_deg_broad/
```

It will not overwrite or modify `08_mast/`, Phase 12, Phase 18, or Phase 20.
Phase 12 is not a runtime dependency of this branch.

## 1. Scientific question and estimand

For a given donor and broad cell type, sum the raw UMI counts from all included
fine cell types in that broad cell type. Within each sex/APOE stratum, estimate:

```text
log2 expression in AD − log2 expression in NCI
```

Thus:

- positive `logFC` means higher broad-cell expression in AD;
- negative `logFC` means lower broad-cell expression in AD;
- the donor, not the nucleus, is the replicate; and
- the primary result is the **marginal broad-cell effect**. It can reflect both
  expression changes within fine types and changes in the mixture of fine
  types inside the broad population.

That marginal effect is the most direct broad-cell signature for a subsequent
broad-network KDA. A composition-adjusted model will be produced as a
sensitivity analysis, not substituted for the primary result.

## 2. Fixed analysis scope

### Sex/APOE groups

| Group ID | Sex | APOE group |
|---|---|---|
| `F_e2` | Female | e2 |
| `F_e33` | Female | e33 |
| `F_e4` | Female | e4 |
| `M_e2` | Male | e2 |
| `M_e33` | Male | e33 |
| `M_e4` | Male | e4 |

### Broad-cell mapping

The new branch will own a frozen mapping file at
`config/phase08_broad_cell_mapping.tsv`; it will not read a deprecated phase at
runtime. The mapping will contain these 52 included fine cell types:

| Broad cell type | Fine cell types included | Count |
|---|---|---:|
| `Astrocytes` | Ast CHI3L1; Ast DPP10; Ast GRM3 | 3 |
| `Excitatory_neurons` | Exc L2-3 CBLN2 LINC02306; Exc L3-4 RORB CUX2; Exc L3-5 RORB PLCH1; Exc L4-5 RORB GABRG1; Exc L4-5 RORB IL1RAPL2; Exc L5 ET; Exc L5-6 RORB LINC02196; Exc L5/6 IT Car3; Exc L5/6 NP; Exc L6 CT; Exc L6 THEMIS NFIA; Exc L6b; Exc NRGN; Exc RELN CHD7 | 14 |
| `Inhibitory_neurons` | Inh ALCAM TRPM3; Inh CUX2 MSR1; Inh ENOX2 SPHKAP; Inh FBN2 EPB41L4A; Inh GPC5 RIT2; Inh L1 PAX6 CA4; Inh L1-2 PAX6 SCGN; Inh L1-6 LAMP5 CA13; Inh L3-5 SST MAFB; Inh L5-6 PVALB STON2; Inh L5-6 SST TH; Inh L6 SST NPY; Inh LAMP5 NRG1 (Rosehip); Inh LAMP5 RELN; Inh PTPRK FAM19A1; Inh PVALB CA8 (Chandelier); Inh PVALB HTR4; Inh PVALB SULF1; Inh RYR3 TSHZ2; Inh SGCD PDE3A; Inh SORCS1 TTN; Inh VIP ABI3BP; Inh VIP CLSTN2; Inh VIP THSD7B; Inh VIP TSHZ2 | 25 |
| `Microglia` | Mic MKI67; Mic P2RY12; Mic TPT1 | 3 |
| `OPCs` | OPC | 1 |
| `Oligodendrocytes` | Oli | 1 |
| `Vasculature_cells` | End; Fib FLRT2; Fib SLC4A4; Per; SMC | 5 |

`CAMs` and `T cells` are deliberately excluded because the requested scope is
the seven broad cell types above. No other observed fine type may be silently
dropped or reassigned. The mapping preflight must report exactly 52 included
fine types, seven broad types, and the two explicit exclusions.

## 3. Input authority and why Minerva is recommended

### Preferred inputs

Use all nine existing Phase 07 count bundles on Minerva:

```text
results/minerva_production/07_pseudobulk/*.pseudobulk_counts.rds
```

Each bundle contains raw RNA counts and metadata for donor-by-fine-cell-type
pseudobulk samples. The broad aggregation must use **all** cohort-included
fine-type samples in these bundles, including fine-type samples whose existing
`primary_eligible` flag is false. Eligibility must be recalculated only after
the fine types have been summed to a donor-by-broad-cell sample. Filtering out
small fine-type samples before summation would bias the broad result.

The following are also required:

- the Phase 07 sample metadata and validated status/artifact records;
- `config/minerva_rds_manifest.tsv` for the nine source-RDS identities;
- the analytic-cohort covariates already carried in the Phase 07 bundles;
- `results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz`
  for gene symbols and mitochondrial tier labels; and
- the new frozen broad-cell mapping and analysis config.

The code must record the path, byte count, and SHA-256 of every input.

### Why not use the local machine for production

The local checkout currently does not contain the Phase 07 pseudobulk count
bundles or the nine normalized Phase 05 RDS files. The Minerva manifest also
estimates peak RAM of 64 GiB, 128 GiB, and 64 GiB for the three excitatory
objects. Therefore production should run on Minerva, where the source data were
created and validated.

If the nine Phase 07 bundles exist on Minerva, the broad aggregation itself
should need only a moderate-memory job because it operates on donor-level sparse
count matrices. The large normalized Seurat objects do not need to be opened.

If the Phase 07 bundles are missing on Minerva, regenerate only the Phase 07
pseudobulk-count prerequisite on a high-memory Minerva node. Do not regenerate
Phase 08 MAST DEGs and do not load the three excitatory RDS objects
simultaneously.

## 4. Broad pseudobulk construction

For each of the nine Phase 07 bundles:

1. validate schema, source status, source checksum, sparse count representation,
   feature names, sample order, and cohort fields;
2. join each fine cell type to the frozen broad mapping;
3. exclude only `CAMs` and `T cells` as declared above;
4. aggregate raw counts by `projid + broad_cell_type` within the bundle;
5. aggregate nucleus count and QC totals with the same grouping; and
6. write an atomic intermediate shard and release the source bundle from memory.

Then merge the nine intermediate shards:

- for the three excitatory shards, sum columns with the same
  `projid + Excitatory_neurons` key;
- assert exact feature identity and feature order before summing; do not silently
  take a feature intersection;
- assert that diagnosis, sex, APOE, age, and PMI agree for the same donor across
  shards;
- create exactly one column per donor and broad cell type; and
- verify gene-wise and sample-wise count conservation.

The fact that excitatory fine types reside in three RDS files is an input-storage
detail, not three biological replicates.

### Donor-by-broad-cell eligibility

Recompute these flags after broad aggregation:

| Rule | Use |
|---|---|
| At least 20 nuclei in a donor-by-broad sample | Primary inclusion, matching the Phase 07 project default |
| At least 50 nuclei | Higher-depth sensitivity flag |
| At least 5 eligible AD donors and 5 eligible NCI donors in a stratum | Minimum estimability gate |
| At least 10 eligible donors in each arm | Confirmatory-support flag; record but do not require for the primary table |

Every one of the 42 structural contrasts must remain in the manifest. A contrast
that fails an estimability rule is `not_estimable` with the donor/nucleus counts
and a precise reason; it is never omitted or represented as a zero-DEG result.

## 5. Primary edgeR model

Fit one model per broad cell type using all eligible donor samples for that broad
type. Define a 12-level group factor from diagnosis, sex, and APOE:

```r
group <- interaction(diagnosis, sex, apoe_group, sep = "__")
design <- model.matrix(
  ~ 0 + group + age_death_scaled + pmi_scaled,
  data = broad_sample_metadata
)
```

For every broad cell type:

1. create an edgeR `DGEList` from raw integer counts;
2. use `edgeR::filterByExpr(y, design = design)`;
3. calculate TMM normalization factors;
4. estimate dispersions with `robust = TRUE`;
5. fit `edgeR::glmQLFit(..., robust = TRUE)`; and
6. test the six AD-minus-NCI contrasts with `glmQLFTest`.

For example, `F_e2` is:

```text
AD__Female__e2 − NCI__Female__e2
```

This joint parameterization produces a separate diagnosis effect for every
sex/APOE group while borrowing information for dispersion estimation and using
the same age and PMI adjustment as the established Phase 07 model. Record model
rank, design columns, sample/donor counts, tested genes, residual degrees of
freedom, and all errors.

### Multiple testing

Store for every tested gene:

- raw p-value;
- BH q-value within its broad-cell × sex/APOE contrast;
- optional study-wide BH q-value across all 42 contrast-gene tests;
- `logFC`, `logCPM`, quasi-likelihood F statistic, standard error, and 95% CI;
- donor and nucleus counts in both diagnosis arms; and
- the fraction of required-group pseudobulk samples with a nonzero count.

The within-contrast BH value is the primary q-value. The global value is a
more conservative sensitivity measure and must not replace it silently.

## 6. Prespecified DEG/signature thresholds

The complete numerical DEG table is the scientific result and must always be
retained. Thresholds only define downstream signature membership, so the DE
model never has to be rerun to examine another tier.

To address the concern that six-way stratification could yield too few
mitochondrial query genes and therefore too few key drivers, use the following
prespecified tiers:

| Tier | DEG rule | Intended use |
|---|---|---|
| Strict reference | within-contrast BH q `< 0.05` and `abs(logFC) > log2(1.3)` | Direct reference to the strict Phase 08/Yu cutoff |
| Relaxed primary | within-contrast BH q `<= 0.10` and `abs(logFC) >= log2(1.2)` | Recommended broad-cell KDA handoff |
| Exploratory | within-contrast BH q `<= 0.20`, with direction from the sign of `logFC` and no hard fold-change cutoff | Clearly labeled hypothesis generation only |

The relaxed primary tier changes both thresholds that most directly control
query size: q-value from 0.05 to 0.10 and absolute fold change from 1.3-fold to
1.2-fold. The exploratory tier relaxes them further. These tiers must be applied
identically to all 42 categories; do not choose a threshold separately for each
category after inspecting its results.

Thresholds that can reasonably be relaxed are:

- DEG q-value;
- DEG absolute fold-change cutoff; and
- later key-driver q-value/coverage thresholds in a separately specified KDA
  phase.

Thresholds that should **not** be relaxed to manufacture a result are:

- minimum donors per diagnosis arm below five;
- full-rank model and finite-covariate requirements;
- exact raw-count conservation;
- minimum effective network-mapped KDA query size of three; or
- exclusion of mitochondrial genes from the final driver-candidate universe.

Do not backfill a sparse category with its top-ranked genes. If even the
exploratory tier has fewer than three effective network-mapped mitochondrial
query genes, the downstream KDA category is explicitly not estimable.

### Mitochondrial genes versus mitochondrial drivers

The DEG table must contain all genes. It must also carry the Phase 09
`mito_tier` annotation so that a future KDA can form up- and down-regulated
`core_mito_protein` query sets. That is different from calling a mitochondrial
gene a driver.

This phase produces no drivers. In a later broad KDA, the final driver candidate
must be non-MT, consistent with the Phase 20 decision. The non-MT driver filter
must be enforced before driver multiple-testing adjustment.

## 7. Composition sensitivity

The primary marginal model intentionally sums all fine types within a broad
type. As a sensitivity analysis:

1. compute donor-level fine-type proportions within each broad cell type;
2. transform and center them using a prespecified zero-handling rule;
3. derive proportion PCs without using diagnosis labels;
4. include at most the first two PCs, and never more PCs than the design can
   support; and
5. rerun the same six contrasts.

Report primary-versus-sensitivity sign concordance, logFC correlation, and DEG
overlap. A rank-deficient composition model is `not_estimable`; it does not
invalidate the marginal primary model.

A second orthogonal sensitivity may meta-analyze the fine-type effects within a
broad type. That answers whether an effect is shared across fine types, which is
not the same estimand as the marginal broad-cell pseudobulk effect. It must not
be labeled as the primary broad DEG.

## 8. Planned implementation files

The implementation phase should add these files:

| Path | Purpose |
|---|---|
| `config/phase08_broad_deg.yml` | Frozen scope, thresholds, inputs, output schemas, and expected checks |
| `config/phase08_broad_cell_mapping.tsv` | Exact 52-fine-type to seven-broad-type mapping plus explicit CAM/T exclusions |
| `scripts/08_build_broad_pseudobulk.R` | Validate and sum Phase 07 raw-count bundles into donor-by-broad samples |
| `scripts/08_run_broad_pseudobulk_de.R` | Build the 42-row manifest and run the seven edgeR QL models |
| `scripts/08_run_broad_deg_composition_sensitivity.R` | Fit the diagnosis-blind fine-composition-PC sensitivity models |
| `scripts/08_finalize_broad_deg.R` | Combine results, annotate genes, create threshold tiers and KDA handoff tables |
| `scripts/08_validate_broad_deg.R` | Execute structural, numerical, provenance, and conservation checks |
| `scripts/08_broad_deg_minerva.lsf` | Reproducible Minerva batch entry point |
| `tests/test_phase08_broad_deg.R` | Synthetic tests for mapping, shard merging, contrasts, thresholds, and failure states |

The new mode may later be registered with `scripts/run_pipeline.R`, but the
first implementation should have a standalone, resumable entry point because
this analysis combines data across RDS boundaries and does not fit the existing
per-RDS `mast` task scope.

## 9. Exact output layout

All new scientific artifacts will be written under:

```text
results/minerva_production/08_deg_broad/
├── 00_inputs/
│   ├── phase07_pseudobulk_input_authority.tsv
│   ├── broad_cell_mapping.tsv
│   ├── broad_deg_contrast_manifest.tsv
│   └── phase08_broad_deg_config_snapshot.yml
├── 01_pseudobulk_shards/
│   └── <rds_id>.broad_pseudobulk_shard.rds
├── 02_broad_pseudobulk/
│   ├── <broad_cell_type>.broad_pseudobulk_counts.rds
│   ├── broad_pseudobulk_samples.tsv.gz
│   ├── broad_fine_type_composition.tsv.gz
│   └── broad_pseudobulk_count_conservation.tsv.gz
├── 03_deg/
│   ├── <broad_cell_type>.broad_deg.tsv.gz
│   ├── <broad_cell_type>.model_diagnostics.tsv
│   └── <broad_cell_type>.contrast_status.tsv
├── 04_sensitivity/
│   ├── broad_deg_composition_adjusted.tsv.gz
│   └── broad_deg_sensitivity_summary.tsv
├── logs/
├── broad_deg_results.tsv.gz
├── broad_deg_contrast_status.tsv
├── broad_deg_model_diagnostics.tsv
├── broad_deg_strict_signatures.tsv.gz
├── broad_deg_relaxed_signatures.tsv.gz
├── broad_deg_exploratory_signatures.tsv.gz
├── broad_core_mito_kda_query_handoff.tsv.gz
├── broad_deg_filter_funnel.tsv
├── broad_deg_checks.tsv
├── broad_deg_artifacts.tsv
└── broad_deg_status.tsv
```

Intermediate files are retained for audit and resume. Writes must be atomic.
The combined files are generated only after all eligible broad types finish or
receive an explicit terminal status.

## 10. Implementation and execution sequence

### A. Implement and test locally with synthetic data

1. Freeze the config and mapping.
2. Implement exact sparse aggregation and cross-RDS donor merging.
3. Implement the joint edgeR model and 42-row manifest.
4. Test count conservation, duplicate donor keys, conflicting metadata,
   missing fine types, non-estimable contrasts, rank deficiency, threshold
   boundary behavior, and deterministic ordering.
5. Use a small synthetic fixture; do not require ROSMAP RDS files for unit tests.

### B. Minerva input preflight

Confirm that all nine validated Phase 07 raw-count bundles are present. If they
are present, no Phase 05 normalization or Phase 08 MAST rerun is needed.

### C. Build broad pseudobulk data

Process one source bundle at a time, write and validate each shard, then combine
the shards. Resume must skip a shard only when code, config, source hashes, schema,
byte size, and output hash all match.

### D. Fit DEG models and finalize

Fit one model per broad type, generate all six contrast statuses, combine the
full result, attach annotations, construct the three signature tiers, and run
the composition sensitivity.

### E. Validate and promote

Run all acceptance gates below. Only a `validated_complete` status can be used
as input to a future broad-cell KDA.

## 11. Minerva commands

These commands assume the implementation files listed in Section 8 have first
been added to the repository and synchronized to
`/sc/arion/work/zhuane01/alzheimer`. They will not work before implementation.

### 11.1 Initialize the Minerva environment

```bash
cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt

export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv
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
```

Check the software environment:

```bash
Rscript -e '
stopifnot(
  as.character(getRversion()) == "4.3.3",
  requireNamespace("Matrix", quietly = TRUE),
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("edgeR", quietly = TRUE),
  requireNamespace("limma", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE)
)
cat("edgeR", as.character(packageVersion("edgeR")), "\n")
'
```

### 11.2 Check the preferred Phase 07 count inputs

This preflight reads one bundle at a time and verifies that there are exactly
nine validated count sources:

```bash
Rscript -e '
root <- "results/minerva_production/07_pseudobulk"
files <- sort(list.files(
  root, pattern = "[.]pseudobulk_counts[.]rds$", full.names = TRUE
))
print(files)
stopifnot(length(files) == 9L)
for (path in files) {
  bundle <- readRDS(path)
  stopifnot(
    identical(bundle$schema_version, "pseudobulk_counts_v1"),
    inherits(bundle$counts, "sparseMatrix"),
    identical(colnames(bundle$counts), bundle$samples$pseudobulk_id)
  )
  cat(bundle$rds_id, nrow(bundle$counts), ncol(bundle$counts), "\n")
  rm(bundle)
  gc()
}
'
```

If this passes, skip Section 11.3.

### 11.3 Fallback only: regenerate missing Phase 07 pseudobulk bundles

Request a single 160-GiB compute allocation. Minerva's `rusage[mem=...]` is per
core, so this uses one core. The `express` queue follows the current repository
convention; replace it with the account-approved CPU queue if Minerva rejects
the requested walltime or memory.

```bash
bsub -Is \
  -P acc_zhangb03a \
  -q express \
  -n 1 \
  -W 12:00 \
  -R "rusage[mem=160000]" \
  -R "span[hosts=1]" \
  /bin/bash
```

Inside that compute allocation, initialize the environment as in Section 11.1,
then dry-run and execute only Phase 07 pseudobulk construction:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk \
  --dry-run

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pseudobulk
```

Do not use `--force`; validated bundles should be resumed/skipped. If the
allocation ends, request another allocation and run the same command again.

### 11.4 Preflight the new broad branch

On a compute node:

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_build_broad_pseudobulk.R \
  --config config/phase08_broad_deg.yml \
  --preflight
```

The preflight must make no scientific output and must report:

- nine source bundles;
- 52 included fine types and two explicit exclusions;
- seven broad types;
- six group definitions and 42 structural contrasts;
- exact feature compatibility across the excitatory shards; and
- all required packages and inputs available.

### 11.5 Submit the broad DEG batch job

The planned `scripts/08_broad_deg_minerva.lsf` should contain:

```bash
#!/bin/bash
#BSUB -J phase08_broad_deg
#BSUB -P acc_zhangb03a
#BSUB -q express
#BSUB -n 1
#BSUB -W 08:00
#BSUB -R "rusage[mem=32000]"
#BSUB -R "span[hosts=1]"
#BSUB -L /bin/bash
#BSUB -oo results/minerva_production/08_deg_broad/logs/%J.out
#BSUB -eo results/minerva_production/08_deg_broad/logs/%J.err

set -euo pipefail

cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt

export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv
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

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_build_broad_pseudobulk.R \
  --config config/phase08_broad_deg.yml \
  --resume

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_run_broad_pseudobulk_de.R \
  --config config/phase08_broad_deg.yml \
  --resume

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_run_broad_deg_composition_sensitivity.R \
  --config config/phase08_broad_deg.yml \
  --resume

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_finalize_broad_deg.R \
  --config config/phase08_broad_deg.yml

LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_validate_broad_deg.R \
  --config config/phase08_broad_deg.yml
```

Submit and monitor it with:

```bash
mkdir -p results/minerva_production/08_deg_broad/logs
bsub < scripts/08_broad_deg_minerva.lsf
bjobs -l JOB_ID
tail -f results/minerva_production/08_deg_broad/logs/JOB_ID.out
```

Because this path reuses donor-level Phase 07 bundles, start with 32 GiB and
record peak RAM. If the job is killed for memory, change only the LSF request to
64 GiB and resume; do not change the scientific config or thresholds.

### 11.6 Final validation command

```bash
LD_PRELOAD="$MKL_PRELOAD" \
Rscript scripts/08_validate_broad_deg.R \
  --config config/phase08_broad_deg.yml \
  --require-status validated_complete
```

Then inspect the structural result without loading the full gene table:

```bash
Rscript -e '
root <- "results/minerva_production/08_deg_broad"
manifest <- read.delim(file.path(
  root, "00_inputs", "broad_deg_contrast_manifest.tsv"
))
status <- read.delim(file.path(root, "broad_deg_contrast_status.tsv"))
checks <- read.delim(file.path(root, "broad_deg_checks.tsv"))
scientific <- read.delim(file.path(root, "broad_deg_status.tsv"))
print(table(status$terminal_status))
stopifnot(
  nrow(manifest) == 42L,
  !anyDuplicated(manifest$contrast_id),
  length(unique(manifest$group_id)) == 6L,
  length(unique(manifest$broad_cell_type)) == 7L,
  all(status$terminal_status %in% c(
    "validated_complete", "not_estimable"
  )),
  !any(status$terminal_status == "failed"),
  all(checks$passed),
  identical(scientific$validation_status, "validated_complete")
)
'
```

## 12. Acceptance criteria

### Structural gates

- Exactly 42 unique contrast-manifest rows.
- Exactly six sex/APOE groups and seven requested broad cell types.
- Exactly 52 included fine types, with CAMs and T cells explicitly excluded.
- One donor-by-broad sample at most per donor and broad type.
- Every structural contrast has one terminal status.

### Input and aggregation gates

- Nine validated Phase 07 raw-count bundles with recorded SHA-256 values.
- Exact gene identity/order compatibility before cross-shard addition.
- Gene-wise total counts conserved from selected fine inputs to broad outputs.
- Sample library sizes equal the sums of their contributing fine samples.
- Donor clinical metadata agree across all contributing shards.
- No fine-level eligibility filter is applied before broad aggregation.

### Model and result gates

- Seven full-rank primary model attempts and six declared contrasts per model.
- All completed result keys are unique by
  `broad_cell_type + group_id + gene`.
- AD-minus-NCI direction is verified with a synthetic positive-control gene.
- All p-values and q-values are finite and within `[0,1]`.
- Stored within-contrast BH q-values reproduce from stored p-values.
- Strict, relaxed, and exploratory membership flags reproduce exactly from
  stored numeric fields, including equality-boundary tests.
- A completed zero-DEG category is distinguishable from `not_estimable` and
  `failed`.

### Provenance and reproducibility gates

- Every declared artifact has byte size and SHA-256 recorded.
- Config, mapping, code checksums, git revision, R/package versions, LSF job ID,
  hostname, elapsed time, and peak RAM are recorded.
- Re-running with unchanged inputs produces byte-identical ordered tables.
- No existing Phase 08, Phase 12, Phase 18, or Phase 20 file is modified.
- Final status is `validated_complete`; otherwise the output is not promoted.

## 13. Downstream handoff and scope boundary

This plan ends with validated broad-cell DEG and query-handoff data. It does not
run KDA and does not produce key drivers.

A future broad KDA would use one broad-cell DEG signature directly for each of
the 42 categories and the matching broad Bayesian network. It would therefore
have 42 primary category runs rather than aggregating evidence from multiple
fine-cell-type KDA runs. That future phase must have its own frozen config,
non-MT driver-candidate filter, multiple-testing family, thresholds, and output
directory.

The existing Phase 20 result remains an aggregation of fine-cell KDA evidence.
It is a different analysis and should not be overwritten by the future direct
broad-signature KDA.

## 14. Key clarification

This is **not** only a change to the last step that aggregates the same gene
across runs. That description applies to Phase 20's aggregation of already-run
fine-cell KDA evidence.

To obtain a genuine broad-cell DEG, the change occurs before differential
expression: raw donor counts are summed across the fine cell types in the same
broad cell type, and AD-versus-NCI is then re-estimated for the resulting broad
samples. Existing fine-cell DEG statistics must not be averaged or combined and
called a broad-cell DEG.
