# Using the Wang KDA maintained interface

## Scope

This is the practical runbook for preparing KDA inputs, running global driver
searches, testing biological signatures, resuming jobs, and combining results.

Before using it:

- install and verify KDA using
  [wang_kda_package_installation.md](wang_kda_package_installation.md); and
- consult
  [wang_kda_interface_implementation.md](wang_kda_interface_implementation.md)
  for scientific definitions and internal contracts.

Run commands from the repository root.

## Minerva paths and input preflight

Use storage according to the data lifetime:

| Content | Minerva location |
|---|---|
| Git checkout, project library, and small KDA tables | `/sc/arion/work/zhuane01/alzheimer` |
| Shared source data and large/shared production results | An approved path under `/sc/arion/projects/zhangb03a/` |
| Disposable intermediates only | `/sc/arion/scratch/zhuane01/` |

Scratch is purged and must not contain the only copy of an input or result.

The nine final networks are tracked under `data/bayesian_network/`. Verify
their audited checksums before a Minerva production run:

```bash
sha256sum -c <<'CHECKSUMS'
220c2dff6b1c95cb8654f9b19347f1c388ed539a369aa7c581cd748ff988634d  data/bayesian_network/Astrocytes/result.links3.links.txt
8d0c911d1c6607d1ec21e28736c41875dc3f87947417a240763ce7a30cac7bf5  data/bayesian_network/CAMs/result.links3.links.txt
bfbb4859dd7298a1f1dfa9cb459e781b379ae4e57114e4858eacbcbf88786c8e  data/bayesian_network/Excitatory_neurons/result.links3.links.txt
9c2eb47351ece8af211487a8edb5143c594a59486da3a87af33555b4e3d41aa4  data/bayesian_network/Inhibitory_neurons/result.links3.links.txt
aa53b942e9496d5d91376f76045a3c29722c024f8bdfbe6b9b7a3a15950d21bb  data/bayesian_network/Microglia/result.links3.links.txt
9660d52ed4d318cebdda93b42b8e57d79f6aadd21a1e0e50a5d0612ac5ed9683  data/bayesian_network/OPCs/result.links3.links.txt
e9f2dfb2d957368d4b98e96489c9ab9edc34cfa9f789a2490bf161c98e27b746  data/bayesian_network/Oligodendrocytes/result.links3.links.txt
8cfae0bbe2fcb296ace3c649e525201320439c4fc1ca8e942e2f9a446b8ed03c  data/bayesian_network/T_cells/result.links3.links.txt
97e53fd2f9871d1e763b741aec5955556f7a9d12df94102fc4e623a906ac75c6  data/bayesian_network/Vasculature_cells/result.links3.links.txt
CHECKSUMS
```

Every line must report `OK`.

## Recommended execution sequence

### 1. Verify the package and interface

```bash
Rscript scripts/analysis/kda/smoke_test_kda.R
```

Do not proceed if any smoke test fails.

### 2. Prepare the primary KDA inputs

```bash
Rscript scripts/analysis/kda/prepare_kda_inputs.R \
  --query-universe core_mito \
  --output-dir results/minerva_production/12_kda/inputs
```

Defaults:

```text
Phase 08: results/minerva_production/08_mast
Phase 09: results/minerva_production/09_annotate_genes
Networks: data/bayesian_network
Output:   results/minerva_production/12_kda/inputs
```

The primary preparation creates 963 candidate direction-specific rows. In the
validated inputs, 494 are eligible and 469 remain documented as ineligible
because their effective query contains fewer than three genes.

Inspect preparation:

```bash
Rscript -e '
library(data.table)
m <- fread("results/minerva_production/12_kda/inputs/kda_run_manifest.tsv")
print(m[, .N, by = .(network_id, eligible)][order(network_id, -eligible)])
print(m[eligible == FALSE, .N, by = skip_reason])
'
```

For the broader sensitivity universe, use a separate output directory:

```bash
Rscript scripts/analysis/kda/prepare_kda_inputs.R \
  --query-universe all_mito_related \
  --output-dir results/minerva_production/12_kda/inputs_all_mito_related
```

Do not mix primary and sensitivity membership files in one manifest.

### 3. Run the smoke-tested real-network pilot

Start with one broad network and inspect runtime/memory before scaling. The
existing Minerva template pilots the smallest network:

```bash
Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Vasculature_cells \
  --network data/bayesian_network/Vasculature_cells/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

Global defaults are:

```text
driver search:       6 directed layers
enrichment network:  3 directed layers
hub boost:           enabled
driver in neighbors: excluded
```

Inspect:

```bash
column -t -s $'\t' \
  results/minerva_production/12_kda/global/Vasculature_cells/global_drivers.tsv \
  | less -S
```

### 4. Run one prespecified Microglia query

First create/reuse the Microglia global cache:

```bash
Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Microglia \
  --network data/bayesian_network/Microglia/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

Then enrich the `Mic P2RY12`, male, APOE e2 AD-down core query:

```bash
Rscript scripts/analysis/kda/run_signature_enrichment.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --run-id immune_Mic_P2RY12_Male_e2_core_mito_AD_down_mito \
  --global-dir results/minerva_production/12_kda/global \
  --output-dir results/minerva_production/12_kda/enrichment
```

The validated input sizes for this contrast are:

```text
background:       4,233 network-mapped genes
all_mito:         88 original / 87 effective
AD_up_mito:       41 original / 41 effective
AD_down_mito:     47 original / 46 effective
```

### 5. Use the orchestrating pipeline

For one run:

```bash
Rscript scripts/analysis/kda/run_kda_pipeline.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --run-id immune_Mic_P2RY12_Male_e2_core_mito_AD_down_mito \
  --output-dir results/minerva_production/12_kda
```

This creates/reuses the matching global network cache, then runs the requested
enrichment. A one-run invocation deliberately does not rewrite shared combined
tables.

For all eligible manifest rows, run without `--run-id`:

```bash
Rscript scripts/analysis/kda/run_kda_pipeline.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --output-dir results/minerva_production/12_kda
```

This is serial and potentially long. On Minerva, it is usually better to run
global networks and per-query enrichments as separate scheduled jobs.

### 6. Combine independently completed runs

After all per-run jobs finish, combine them once:

```bash
Rscript scripts/analysis/kda/run_kda_pipeline.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --output-dir results/minerva_production/12_kda \
  --combine-only
```

Do not run this command concurrently from multiple jobs.

## Minerva interactive execution

Do lightweight checks on the login node, then request a compute shell:

```bash
cd /sc/arion/work/zhuane01/alzheimer

bsub -q interactive \
  -P acc_zhangb03a \
  -n 1 \
  -W 04:00 \
  -R 'rusage[mem=16000]' \
  -R 'span[hosts=1]' \
  -Is /bin/bash
```

On the compute node:

```bash
cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt
export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv

Rscript scripts/analysis/kda/smoke_test_kda.R

Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Vasculature_cells \
  --network data/bayesian_network/Vasculature_cells/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

Commands run synchronously. Keep the terminal connected, and type `exit` when
finished.

## Minerva LSF batch execution

The tracked pilot template is:

```text
scripts/analysis/kda/run_global_kda_minerva.lsf
```

It requests one CPU, four hours, and 16 GB because KDA is serial. Create the
log directory before submitting:

```bash
mkdir -p results/minerva_production/12_kda/logs
bsub < scripts/analysis/kda/run_global_kda_minerva.lsf
```

Monitor with:

```bash
bjobs
bjobs -l JOB_ID
bpeek JOB_ID
```

Stop a job with:

```bash
bkill JOB_ID
```

Use the first completion report to right-size walltime and memory before
running the other networks. More requested cores will not speed up this serial
implementation.

For per-signature batch jobs, use the same environment setup and call:

```bash
Rscript scripts/analysis/kda/run_signature_enrichment.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --run-id RUN_ID \
  --global-dir results/minerva_production/12_kda/global \
  --output-dir results/minerva_production/12_kda/enrichment
```

Each job writes only its own `<run_id>/` directory. Run `--combine-only`
serially after all jobs complete.

## Command reference

Every R command accepts `--help` or `-h`.

### Installer

```bash
Rscript scripts/analysis/kda/install_kda.R --help
```

### Input preparation

```bash
Rscript scripts/analysis/kda/prepare_kda_inputs.R --help
```

Important options:

```text
--phase08-dir DIR
--annotation-dir DIR
--network-root DIR
--output-dir DIR
--query-universe core_mito|all_mito_related
--force
```

### Global KDA

```bash
Rscript scripts/analysis/kda/run_global_kda.R --help
```

Important options:

```text
--network-id ID
--network PATH
--output-dir DIR
--driver-search-layers N
--enrichment-layers N
--include-driver
--no-boost-hubs
--force
```

### Signature enrichment

```bash
Rscript scripts/analysis/kda/run_signature_enrichment.R --help
```

Important options:

```text
--manifest PATH
--run-id ID
--global-dir DIR
--output-dir DIR
--p-adjust-method BH
--alpha 0.05
--force
```

### Pipeline

```bash
Rscript scripts/analysis/kda/run_kda_pipeline.R --help
```

Important options:

```text
--manifest PATH
--output-dir DIR
--run-id ID
--driver-search-layers N
--enrichment-layers N
--include-driver
--no-boost-hubs
--p-adjust-method BH
--alpha 0.05
--combine-only
--force
```

## Output layout

```text
results/minerva_production/12_kda/
├── inputs/
│   ├── kda_run_manifest.tsv
│   ├── signature_members.tsv.gz
│   ├── background_members.tsv.gz
│   ├── query_gene_diagnostics.tsv.gz
│   ├── kda_query_qc.tsv
│   └── run_manifest.json
├── global/
│   └── <network_id>/
│       ├── global_drivers.tsv
│       ├── driver_neighborhood_members.tsv.gz
│       ├── raw_kda_drivers.tsv
│       ├── raw_kda_parameters.tsv
│       ├── raw_kda_downstream.tsv
│       ├── raw_kda.rds
│       └── run_manifest.json
├── enrichment/
│   └── <run_id>/
│       ├── query_coverage.tsv
│       ├── driver_enrichment.tsv
│       ├── overlap_members.tsv.gz
│       └── run_manifest.json
└── combined/
    ├── all_driver_enrichment.tsv.gz
    └── significant_drivers.tsv
```

## Reading the enrichment output

The primary table is `driver_enrichment.tsv`.

| Column | Meaning |
|---|---|
| `driver` | Global KDA candidate being tested. |
| `query_size_original` | Mitochondrial DEG query before network/background mapping. |
| `query_size_effective` | Query genes present in the exact background. |
| `background_size` | Tested genes represented in the matching network. |
| `neighborhood_size` | Driver downstream neighborhood after background restriction. |
| `overlap_size` | Effective-query genes in that neighborhood. |
| `overlap_genes` | Semicolon-delimited overlapping genes. |
| `fold_enrichment` | Observed neighborhood query rate divided by background query rate. |
| `p_value` | One-sided hypergeometric P value. |
| `q_value` | Within-signature adjusted P value. |
| `significant` | Whether `q_value <= alpha`. |
| `driver_in_query` | Whether the driver is itself a query gene. |
| `driver_in_background` | Whether the driver was measurable/tested in the contrast. |
| `wang_global_keydriver_flag` | KDA's separate final hierarchy/hub flag. |

All returned global candidates are tested. Do not filter candidates before
enrichment based only on `wang_global_keydriver_flag`.

## Resume and replacement behavior

- A completed run with matching checksums and parameters is reused.
- An incompatible completed or partial output fails.
- `--force` explicitly authorizes replacement of the maintained output files.
- Prefer a new output directory when changing scientific settings.
- Global KDA is cached per network and must not be rerun for every signature.
- Do not manually edit generated TSVs while expecting cache reuse.

## Common failures

- **KDA 0.2 unavailable:** follow the package-installation guide.
- **Effective query below three genes:** choose an eligible manifest row; the
  ineligible row remains in preparation QC.
- **Background outside the network:** regenerate inputs rather than editing
  membership files.
- **Network checksum mismatch:** ensure the manifest and global cache refer to
  the same network file.
- **Nonempty incompatible output directory:** inspect it, then use a new
  directory or explicit `--force`.
- **No significant driver:** this is a valid result, not a pipeline failure.
- **Candidate driver absent from background:** enrichment still tests its
  background-restricted downstream neighborhood and emits a warning.

