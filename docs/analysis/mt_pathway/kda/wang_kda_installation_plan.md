# Wang KDA installation and interface guide

## Decision

Yes. Put the project-maintained KDA interface under:

```text
scripts/analysis/kda/
```

Do not put Wang's unmodified third-party package and PHG scripts in
`scripts/`. Keep those preserved separately under
[`archive/wang_kda_code`](../../../../archive/wang_kda_code/SOURCE.md).
The `scripts/` subdirectory should contain only code maintained for this
project.

The recommended default is the two-stage workflow used by Wang:

1. identify global drivers once for each cell-type Bayesian network;
2. extract each driver's directed downstream neighborhood; and
3. test each mitochondrial DEG signature for enrichment in those
   neighborhoods using its matching measurable background.

The package installation is now complete on the local workstation: KDA 0.2 is
installed in the project `renv` library, recorded in `renv.lock`, and its two
required functions load successfully under R 4.3.3. The project-maintained
analysis interface described below has not yet been implemented, and Minerva
must perform its own `renv::restore()` because an R library installed on one
machine must not be copied to another.

## Current implementation status

- Complete locally: KDA 0.2 package installation, archive checksum
  verification, package load check, and `renv.lock` record.
- Not yet complete: `scripts/analysis/kda/`, query/background preparation,
  global-driver caching, signature enrichment, and production KDA runs.
- Not changed remotely: the local installation did not install anything on
  Minerva. Follow the [Minerva procedure](#minerva-installation-and-execution)
  after the updated repository and required KDA inputs are present
  there.

## Proposed directory layout

```text
scripts/analysis/kda/
├── install_kda.R
├── prepare_kda_inputs.R
├── run_global_kda.R
├── run_signature_enrichment.R
├── run_kda_pipeline.R
├── smoke_test_kda.R
└── lib/
    ├── cli.R
    ├── kda_io.R
    ├── kda_core.R
    ├── kda_enrichment.R
    └── kda_validation.R
```

Responsibilities:

- `install_kda.R`: verify the archive checksum and install KDA 0.2 into the
  active project `renv` library.
- `prepare_kda_inputs.R`: build query, background, and run-manifest tables from
  the Phase 08/09 differential-expression outputs.
- `run_global_kda.R`: find global candidate drivers once per Bayesian network.
- `run_signature_enrichment.R`: test query enrichment in candidate-driver
  neighborhoods.
- `run_kda_pipeline.R`: provide the stable user-facing command-line interface
  and orchestrate or resume the two stages.
- `smoke_test_kda.R`: run a small deterministic network test in which known
  upstream nodes must be recovered.
- `lib/`: contain reusable implementation functions without command-line side
  effects.

Do not edit the files in `archive/wang_kda_code` to make them run.
Preserving them unchanged makes comparisons with the upstream Wang repository
auditable.

## Installation requirements

### Existing project components

The repository already has:

- R 4.3.3 recorded in [`renv.lock`](../../../../renv.lock);
- `renv` activation through the root `.Rprofile`;
- `class`, `cluster`, `lattice`, and `rpart` recorded in `renv.lock`;
- `data.table`, `digest`, `jsonlite`, and `yaml`, which are sufficient for
  input/output, checksums, manifests, and configuration;
- the KDA source archive at
  [`KDA-0.2.tar.gz`](../../../../archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz).

The KDA package is pure R and installed without compilation during the local
smoke test. No Python environment is needed.

### Package identity

The downloaded archive has:

```text
Package: KDA
Version: 0.2
Date: 2014-07-29
Author: Bin Zhang
License: Artistic-2.0
```

Expected SHA-256:

```text
7b185e16ef855a4d19061722f3920100777c19acd8357107a31928b73fe9e70f
```

The Wang paper calls the package version `0.02`, while the archive and its
`DESCRIPTION` use `0.2`. The interface should require version `0.2` and record
this known discrepancy in every run manifest.

## Local installation and restore

The local workstation installation is complete. On this workstation or a new
machine, run commands from the repository root so `.Rprofile` activates the
project `renv`. The local archive must exist before restore because `renv.lock`
records KDA with `Source: Local`.

Verify the archive:

```bash
sha256sum archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

The output must match the expected SHA-256 above. Then restore the recorded
environment:

```bash
Rscript -e 'renv::restore(prompt = FALSE)'
```

This now installs KDA 0.2 automatically when it is missing. An explicit forced
reinstall is only needed to repair or audit the local package installation:

```bash
Rscript -e '
renv::load(".")
renv::install(
  "archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz",
  rebuild = TRUE,
  prompt = FALSE
)
'
```

Verify the installed version and required functions:

```bash
Rscript -e '
renv::status()
stopifnot(as.character(packageVersion("KDA")) == "0.2")
stopifnot(all(c("keydriverInSubnetwork", "downStreamGenes") %in%
              getNamespaceExports("KDA")))
cat("KDA", as.character(packageVersion("KDA")), "is available at",
    find.package("KDA"), "\n")
'
```

KDA 0.2 is already recorded in `renv.lock`; do not run
`renv::snapshot()` merely to restore it on another machine. If the maintained
interface later adds new package dependencies, snapshot deliberately and
review the complete lockfile diff before accepting it.

### Portability warning

The `.gitignore` rules now explicitly expose `data/bayesian_network/` even
though other local content under `data/*` remains ignored. Once these files are
added and committed, a fresh Git clone will contain the cell-type networks and
optional network summaries. The KDA archive under `archive/wang_kda_code/`
remains ignored and is not supplied by Git.

For workstation-only use, the installer can require the existing local
archive. For fully reproducible Git/Minerva execution, choose one of these
before deployment:

1. preserve the archive in an approved tracked vendor directory together with
   its license and checksum; or
2. make `install_kda.R` download the archive from the pinned upstream commit,
   verify the checksum, and then install it.

The installer must never silently install an unpinned latest version.

## Expected end state after installation

Package installation, interface implementation, and analysis execution are
three separate operations. Their filesystem effects should not be confused.

### End state after package installation only

After running `renv::restore()` and installing KDA 0.2:

| Operation | Path | Expected state |
|---|---|---|
| Created | `renv/library/R-4.3/<platform>/KDA/` | Project-library entry for KDA 0.2. Depending on `renv` configuration, this may be a link to the machine's `renv` cache. |
| Possibly created | Other entries under `renv/library/R-4.3/<platform>/` | `renv::restore()` creates any project-library entries that were missing before installation. |
| Possibly created | Machine-level `renv` cache entry | Exact cache path is machine-specific and outside this repository. |
| Modified locally once | `renv.lock` | Now contains the reviewed KDA 0.2 local-source record. Restoring from this lockfile on another machine does not modify it. |
| Unchanged | `archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz` | The source archive remains byte-identical to the downloaded copy. |
| Unchanged | `archive/wang_kda_code/KDA_analysis/*.R` | Wang's original PHG scripts remain untouched. |
| Unchanged | `.Rprofile`, `renv/activate.R`, Bayesian-network files, DEG results, and project analysis scripts | Installation does not rewrite these files. |
| Deleted | None | Installation should not delete any repository file or analysis result. |
| Analysis outputs created | None | Installing the package does not run KDA. |

The machine-specific `renv/library/` tree is ignored by Git. The completed
local installation therefore has one intended tracked change, the KDA record
in `renv.lock`; package-library and cache files remain untracked. A restore on
Minerva or another workstation should produce no further tracked changes. If a
future snapshot changes unrelated packages or repository metadata, stop and
review the environment rather than accepting it automatically.

Verify the installation location and clean package state with:

```bash
Rscript -e '
renv::load(".")
library(KDA)
cat("version:", as.character(packageVersion("KDA")), "\n")
cat("library:", find.package("KDA"), "\n")
'

git status --short
```

### End state after the maintained interface is implemented

Interface implementation is a later source-code change, not a side effect of
installing KDA. It is expected to create:

```text
scripts/analysis/kda/
├── install_kda.R
├── prepare_kda_inputs.R
├── run_global_kda.R
├── run_signature_enrichment.R
├── run_kda_pipeline.R
├── smoke_test_kda.R
└── lib/
    ├── cli.R
    ├── kda_io.R
    ├── kda_core.R
    ├── kda_enrichment.R
    └── kda_validation.R
```

At that point:

- the new `scripts/analysis/kda/` files are tracked project source;
- `renv.lock` contains the reviewed KDA 0.2 record;
- Wang's downloaded source remains unchanged;
- no existing mitochondrial-analysis script is replaced or deleted; and
- no KDA result files exist until a run command is executed.

### End state after the first KDA analysis run

Only an actual analysis run should create the generated files described in
the [output contracts](#output-contracts), under:

```text
results/minerva_production/12_kda/
```

Those outputs include prepared inputs, global drivers, driver neighborhoods,
signature enrichment statistics, manifests, and combined result tables.
Running the analysis must not modify the package archive, the Bayesian
networks, the MAST/Phase 09 source results, or the maintained wrapper code.

No installation or analysis step should delete files automatically. Rerunning
a completed analysis should either validate and reuse matching outputs or
require an explicit `--force`/new output directory when parameters or input
checksums differ.

## Minerva installation and execution

### Minerva-specific decisions

Minerva uses IBM LSF, not Slurm. Use `bsub`, LSF queues, and an allocation
account; do not use `sbatch`, `srun`, or Slurm partitions. The current Minerva
LSF documentation lists `express` for jobs up to 12 hours, `premium` for normal
jobs up to 144 hours, and `interactive` for interactive compute sessions. Check
what is currently available with `bqueues` before submission. See the official
[LSF scheduler guide](https://labs.icahn.mssm.edu/minervalab/documentation/lsf-job-scheduler/).

KDA is pure R. It needs one CPU process, no GPU, no CUDA, and no Conda
environment. Use the repository's R 4.3.3 `renv` environment. Minerva manages R
with Lmod, and the exact available versions can change, so check with
`module -r spider '^R$'`; this project currently uses `module load R/4.3.3`.
See Minerva's [Lmod guide](https://labs.icahn.mssm.edu/minervalab/documentation/software-environment-lmod/),
[R guide](https://labs.icahn.mssm.edu/minervalab/documentation/r/), and
[`renv` guide](https://labs.icahn.mssm.edu/minervalab/documentation/renv/).

There are two supported execution workflows:

1. **Interactive/manual:** log in, request an interactive compute shell, and
   type each KDA command manually while the terminal remains attached.
2. **LSF batch:** put the same environment setup and KDA command in an LSF job
   script and submit it with `bsub < job.lsf`; the job runs unattended.

An interactive compute shell is requested through LSF, but it is operationally
different from a batch job: no job script is required and commands run
immediately at the prompt. Directly after SSH login, the login node may be used
for lightweight preflight commands such as `cd`, `git status`, `mybalance`,
`bqueues`, file transfer, and checksum verification. Do not run global KDA or
signature enrichment directly on the login node; use either workflow below so
the computation runs on a compute node.

### Paths and storage

Use the established repository location:

```text
/sc/arion/work/zhuane01/alzheimer
```

Recommended placement is:

| Content | Minerva location | Reason |
|---|---|---|
| Git checkout, project `renv` library, and small KDA inputs | `/sc/arion/work/zhuane01/alzheimer` | Fast personal work storage and the repository's existing location. |
| Shared source data and large/shared final outputs | `/sc/arion/projects/zhangb03a/...` | Project storage. Use a project result directory via `--output-dir` if KDA outputs become large or need to be shared. |
| Disposable job intermediates only | `/sc/arion/scratch/zhuane01/...` | Scratch is purged and must not contain the only copy. |
| Small configuration files | `/hpc/users/zhuane01` | Home is backed up but slow and quota-limited. |

The current repository convention writes KDA results below
`results/minerva_production/12_kda/`, which is under `/sc/arion/work`. This is
reasonable for initial KDA tables. Move or directly write large/shared
production outputs to an approved `/sc/arion/projects/zhangb03a/...` directory.
Neither work nor project storage is backed up, so keep code in Git and archive
irreplaceable inputs/results separately. See Minerva's
[storage guide](https://labs.icahn.mssm.edu/minervalab/documentation/storage-and-file-permission-management/).

Check the allocation and storage before starting:

```bash
mybalance
groups
showquota -u "$USER"
showquota -p zhangb03a
ls -ld /sc/arion/work/zhuane01/alzheimer
ls -ld /sc/arion/projects/zhangb03a
bqueues
```

The natural allocation shown in the local Minerva notes is
`acc_zhangb03a`. Confirm it with `mybalance` rather than assuming access.

### Stage the KDA inputs

After the `.gitignore` change is committed, a Git clone or `git pull` provides
all files under `data/bayesian_network/`, including the nine final
`result.links3.links.txt` networks. The KDA package bundle under
`archive/wang_kda_code/` remains gitignored and must be transferred separately.

From the local workstation repository root, transfer the Wang bundle while
preserving its relative path:

```bash
rsync -av --relative \
  archive/wang_kda_code/ \
  zhuane01@minerva.hpc.mssm.edu:/sc/arion/work/zhuane01/alzheimer/
```

For a larger or restartable transfer, use Minerva
[Globus](https://labs.icahn.mssm.edu/minervalab/documentation/file-transfer-globus/).
Do not transfer the workstation's `renv/library/`; Minerva must build its own
platform-specific project library from `renv.lock`.

On Minerva, verify the transferred archive and the Git-provided network inputs
before restoring:

```bash
cd /sc/arion/work/zhuane01/alzheimer

sha256sum -c <<'CHECKSUMS'
7b185e16ef855a4d19061722f3920100777c19acd8357107a31928b73fe9e70f  archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
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

All ten lines must report `OK`. A checksum failure means the file is missing or
differs from the locally audited input; do not run the analysis until that is
resolved.

### Workflow 1: interactive/manual execution

From a Minerva login node, request an interactive compute session for package
restore, validation, or the first network pilot:

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

After the prompt changes to a compute node, initialize the same environment
used by the existing analysis:

```bash
cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt

Rscript --version
Rscript -e 'cat("renv ", as.character(packageVersion("renv")), "\n", sep = "")'
```

The sourced setup loads `R/4.3.3`, configures the Minerva proxy, sets one-thread
BLAS/OpenMP variables, and creates the repository's temporary directory. The
KDA archive itself is local and does not need the network, but `renv::restore()`
may need the configured proxy to obtain other missing packages.

Optional: Minerva generally recommends package caches under work storage. To
put the shared `renv` cache there, set this before every restore and in every
later batch job:

```bash
mkdir -p /sc/arion/work/zhuane01/.cache/renv
export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv
```

Consistency matters: either use that setting in all KDA sessions/jobs or leave
it unset and use the existing default. The active project library remains
under the repository either way.

Restore exactly what is recorded in `renv.lock`:

```bash
Rscript -e 'renv::restore(prompt = FALSE)'
```

Because the KDA lockfile entry has `Source: Local`, this command requires the
transferred archive at exactly:

```text
archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

Verify the restored environment and the package interface:

```bash
Rscript -e '
renv::status()
stopifnot(as.character(packageVersion("KDA")) == "0.2")
stopifnot(all(c("keydriverInSubnetwork", "downStreamGenes") %in%
              getNamespaceExports("KDA")))
cat("KDA version:", as.character(packageVersion("KDA")), "\n")
cat("KDA library:", find.package("KDA"), "\n")
'
```

Expected results are `No issues found`, KDA version `0.2`, and a package path
inside the Minerva checkout's project `renv` library. Installation creates no
KDA analysis results.

For installation only, the package verification above completes the
interactive workflow. After the maintained interface exists, run its smoke
test and the first real-network pilot manually in the same allocated compute
shell:

```bash
Rscript scripts/analysis/kda/smoke_test_kda.R

Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Vasculature_cells \
  --network data/bayesian_network/Vasculature_cells/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

These commands run synchronously and print progress in the terminal. Keep the
terminal connected until the command finishes. Type `exit` after completion to
leave the interactive allocation. Do not run either command until the
maintained scripts exist; currently only package installation and verification
are available.

### Workflow 2: LSF batch execution

Batch mode is for unattended, longer, or production execution. It uses the
same repository, environment setup, KDA CLI, inputs, and output directory as
the interactive workflow. The difference is that the command is placed inside
a job script with `#BSUB` resource directives. Do not submit this job until the
maintained interface and its input files exist. First pilot
`Vasculature_cells`, inspect runtime and peak memory, and then adjust resources
before Microglia and the complete nine-network run.

A reasonable initial serial LSF template is:

```bash
#!/bin/bash
#BSUB -J kda_vasc_global
#BSUB -P acc_zhangb03a
#BSUB -q express
#BSUB -n 1
#BSUB -W 04:00
#BSUB -R "rusage[mem=16000]"
#BSUB -R "span[hosts=1]"
#BSUB -L /bin/bash
#BSUB -oo results/minerva_production/12_kda/logs/%J.out
#BSUB -eo results/minerva_production/12_kda/logs/%J.err

cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt

# Uncomment only if the same cache setting was used during restore.
# export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv

Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Vasculature_cells \
  --network data/bayesian_network/Vasculature_cells/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

Save the template as, for example,
`scripts/analysis/kda/run_global_kda_minerva.lsf` after the interface exists.
Create the log directory before submission because LSF cannot open a log file
whose parent directory is missing:

```bash
mkdir -p results/minerva_production/12_kda/logs
bsub < scripts/analysis/kda/run_global_kda_minerva.lsf
```

Monitor and control it with:

```bash
bjobs
bjobs -l JOB_ID
bpeek JOB_ID
bkill JOB_ID
```

`rusage[mem=16000]` means 16,000 MB per requested core. KDA is serial here, so
requesting more cores without changing the implementation will not make it
faster. The first request is deliberately provisional; use the LSF completion
report to right-size memory and walltime. No GPU queue should be used.

Once the pilot and the query/background inputs pass validation, use the
manifest interface described below for production. Global KDA should run once
per network and be cached by network checksum; it must not be rerun for every
signature.

### Expected Minerva end state after restore

| Operation | Minerva path | Expected state |
|---|---|---|
| Present from Git | `/sc/arion/work/zhuane01/alzheimer/renv.lock` | Contains the KDA 0.2 local-source record. |
| Transferred, gitignored | `archive/wang_kda_code/` | Audited archive, provenance, license, and Wang reference scripts. |
| Present from Git | `data/bayesian_network/` | Contains the nine checksum-verified final networks and the five optional combined-network/QC summary files. |
| Created by restore | `renv/library/R-4.3/<platform>/KDA/` | Minerva-specific project-library entry for KDA 0.2, often linked to an `renv` cache. |
| Optional cache | `/sc/arion/work/zhuane01/.cache/renv/` | Created only if `RENV_PATHS_CACHE` is adopted consistently. |
| Created before batch submission | `results/minerva_production/12_kda/logs/` | Empty initially; LSF creates `%J.out` and `%J.err` when a job runs. |
| Analysis outputs | `results/minerva_production/12_kda/global/`, `enrichment/`, and `combined/` | Absent after installation; created only by the future maintained interface. |
| Deleted | None | Transfer, restore, and verification do not delete source data or results. |

Do not run `renv::snapshot()` on Minerva merely because the platform-specific
library path differs. The tracked lockfile is the source of truth; use
`renv::status()` to verify consistency. A production KDA run must not modify
`renv.lock`, the package archive, Bayesian-network inputs, or MAST/Phase 09
source results.

## What the installer should do

`install_kda.R` should:

1. locate the repository root;
2. confirm that R is compatible with the project lockfile;
3. locate the KDA archive supplied by `--archive`;
4. require the expected SHA-256;
5. activate the project `renv`;
6. skip installation when KDA 0.2 is already available;
7. install the archive when it is absent or the wrong version;
8. load `KDA` and verify the two required functions:

   ```r
   KDA::keydriverInSubnetwork
   KDA::downStreamGenes
   ```

9. print the package version, archive checksum, and installation library.

Proposed command:

```bash
Rscript scripts/analysis/kda/install_kda.R \
  --archive archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

## Package functions used by the interface

### `keydriverInSubnetwork()`

This is the core function used by Wang's PHG script:

```r
KDA::keydriverInSubnetwork(
  linkpairs,
  signature,
  background = NULL,
  directed = TRUE,
  nlayers = 6,
  enrichedNodes_percent_cut = -1,
  FET_pvalue_cut = 0.05,
  boost_hubs = TRUE,
  dynamic_search = TRUE,
  bonferroni_correction = TRUE,
  expanded_network_as_signature = FALSE
)
```

For Wang-style global driver discovery:

- `linkpairs` is the complete two-column network;
- `signature` is every node in that network;
- `directed = TRUE`;
- `nlayers = 6`.

The function returns a three-element list:

```text
[[1]] selected driver table
[[2]] cutoff/parameter table
[[3]] downstream-count table for all network nodes
```

### `downStreamGenes()`

This extracts the directed neighborhood of a candidate:

```r
KDA::downStreamGenes(
  netpairs,
  seednodes,
  N = 3,
  directed = TRUE
)
```

The function includes the seed node in its returned set. The project wrapper
should remove the seed before enrichment by default, while providing an
explicit compatibility option if exact Wang-script behavior is required.

### `keyDriverAnalysis()`

The package also exposes a high-level, signature-oriented wrapper:

```r
KDA::keyDriverAnalysis(
  inputnetwork,
  signature,
  directed = TRUE,
  nlayer_expansion = 1,
  nlayer_search = 6,
  enrichedNodes_percent_cut = -1,
  boost_hubs = TRUE,
  dynamic_search = TRUE,
  FET_pvalue_cut = 0.05,
  use_corrected_pvalue = TRUE,
  outputfile = NULL
)
```

This can be retained as a secondary comparison mode, but it should not be the
default Wang-reproduction interface. It has several limitations:

- `inputnetwork` must be an in-memory matrix/data frame, despite documentation
  describing it as a file;
- it does not accept an actual background gene vector;
- its expansion direction cannot be separated cleanly from the direction used
  for downstream searching;
- it returns only internally selected drivers rather than all tested nodes;
- its result columns are coerced to character;
- its built-in `outputfile`/visualization path fails under the current R
  environment.

Always use `outputfile = NULL` and let the project wrapper write validated
tables.

## Recommended scientific workflow

### Stage A: global drivers, once per network

For each of the nine broad cell-type networks:

1. read the headerless two-column `result.links3.links.txt`;
2. label columns `from` and `to`;
3. validate nonmissing gene identifiers, no duplicate edges, and no self-edges;
4. treat the first column as upstream and the second as downstream;
5. pass all network nodes as the KDA signature;
6. run directed, six-layer global KDA;
7. save the raw package return values;
8. extract three-layer downstream neighborhoods for every returned candidate.

This expensive stage should be cached by network checksum. It should not be
rerun for every fine-cell/sex/APOE signature.

### Stage B: enrichment, once per biological signature

For each fine-cell/sex/APOE mitochondrial signature:

1. identify the matching broad cell-type network;
2. load the signature-specific background;
3. define the effective query as query genes present in the background;
4. intersect each driver neighborhood with the background;
5. count the overlap between the neighborhood and effective query;
6. calculate a one-sided hypergeometric P value;
7. calculate fold enrichment;
8. apply BH correction across all candidate drivers for that signature;
9. report the overlapping genes and coverage diagnostics.

For a background of size \(N\), query size \(K\), neighborhood size \(n\), and
observed overlap \(k\):

```r
p_value <- phyper(
  q = k - 1,
  m = K,
  n = N - K,
  k = n,
  lower.tail = FALSE
)

fold_enrichment <- (k / n) / (K / N)
```

Use `stats::p.adjust(p_value, method = "BH")` for the primary within-signature
correction. Retain the Wang/Bonferroni package outputs as separate fields
rather than mixing the two corrections.

## Proposed maintained R interface

The main reusable function should be:

```r
run_celltype_kda <- function(
  network,
  signatures,
  backgrounds,
  driver_search_layers = 6L,
  enrichment_layers = 3L,
  include_driver_in_neighborhood = FALSE,
  boost_hubs = TRUE,
  p_adjust_method = "BH",
  alpha = 0.05
)
```

Arguments:

- `network`: validated two-column character data frame, `from` and `to`;
- `signatures`: named list of query gene vectors;
- `backgrounds`: named list of background vectors using the same names as
  `signatures`;
- `driver_search_layers`: KDA global search depth, initially six;
- `enrichment_layers`: downstream neighborhood depth, initially three to match
  Wang's enrichment scripts;
- `include_driver_in_neighborhood`: default `FALSE`;
- `boost_hubs`: preserve the Wang package setting but record it;
- `p_adjust_method`: primary external correction, `BH`;
- `alpha`: adjusted-P threshold.

Return:

```r
list(
  run_manifest = ...,
  query_coverage = ...,
  global_drivers = ...,
  neighborhoods = ...,
  enrichment = ...,
  significant_drivers = ...,
  raw_kda = ...
)
```

## Proposed command-line interface

The stable user-facing command should operate from a run manifest:

```bash
Rscript scripts/analysis/kda/run_kda_pipeline.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --run-id Mic_P2RY12__male_e2__AD_down_mito \
  --output-dir results/minerva_production/12_kda
```

Stage-specific commands should also be available for Minerva:

```bash
Rscript scripts/analysis/kda/run_global_kda.R \
  --network-id Microglia \
  --network data/bayesian_network/Microglia/result.links3.links.txt \
  --output-dir results/minerva_production/12_kda/global
```

```bash
Rscript scripts/analysis/kda/run_signature_enrichment.R \
  --manifest results/minerva_production/12_kda/inputs/kda_run_manifest.tsv \
  --run-id Mic_P2RY12__male_e2__AD_down_mito \
  --global-dir results/minerva_production/12_kda/global \
  --output-dir results/minerva_production/12_kda/enrichment
```

The runner should use the repository's existing base-R `commandArgs()` parsing
style rather than adding a new CLI package.

## Input contracts

### Network file

Headerless TSV:

```text
REGULATOR_X    GENE_Y
GENE_Y         TOMM7
```

Rules:

- exactly two fields;
- first field is upstream;
- second field is downstream;
- no blank identifiers;
- no duplicate edges;
- no self-edges;
- expected to be a DAG for the final Bayesian networks.

### Signature membership table

Long-form TSV:

```text
run_id                                  gene
Mic_P2RY12__male_e2__all_mito           TUFM
Mic_P2RY12__male_e2__all_mito           TOMM7
Mic_P2RY12__male_e2__AD_down_mito       TUFM
Mic_P2RY12__male_e2__AD_down_mito       TOMM7
```

### Background membership table

Long-form TSV:

```text
run_id                                  gene
Mic_P2RY12__male_e2__all_mito           GENE1
Mic_P2RY12__male_e2__all_mito           GENE2
```

The background for each run is:

```text
genes tested in that exact MAST contrast
    ∩
nodes represented in the matching Bayesian network
```

The query must be a subset of its background after network mapping.

### Run manifest

Minimum columns:

```text
run_id
network_id
network_path
fine_cell_type
sex
apoe_group
comparison
query_direction
signature_path
background_path
```

The manifest should also record query-definition and DEG-threshold versions.

## Output contracts

Recommended output tree:

```text
results/minerva_production/12_kda/
├── inputs/
│   ├── kda_run_manifest.tsv
│   ├── signature_members.tsv.gz
│   └── background_members.tsv.gz
├── global/
│   └── <network_id>/
│       ├── global_drivers.tsv
│       ├── driver_neighborhood_members.tsv.gz
│       ├── raw_kda_drivers.tsv
│       ├── raw_kda_parameters.tsv
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

The primary enrichment table should include:

```text
run_id
network_id
driver
query_size_original
query_size_effective
background_size
neighborhood_size
overlap_size
overlap_genes
fold_enrichment
p_value
q_value
significant
driver_in_query
driver_in_background
wang_global_keydriver_flag
driver_search_layers
enrichment_layers
```

## Required validation

The interface should fail rather than silently continue when:

- KDA 0.2 is unavailable;
- the archive checksum is wrong;
- a network file has other than two columns;
- a network direction is ambiguous;
- a `run_id` is duplicated;
- a signature lacks a matching background;
- the effective query has fewer than three network-mapped genes;
- a background is not a subset of network nodes;
- the effective query is not a subset of its background;
- KDA returns malformed columns;
- an output directory contains an incompatible completed run.

Warnings rather than failures may be appropriate when:

- the effective query is small but still above the package minimum;
- network coverage is low;
- no driver passes the enrichment threshold;
- a candidate driver is absent from the contrast-specific background.

Every run manifest should record:

- Git commit;
- R and KDA versions;
- archive checksum;
- network checksum;
- signature and background checksums;
- all layer, hub, and correction settings;
- original and effective query sizes;
- start/end time and completion status.

## Smoke tests

At minimum, `smoke_test_kda.R` should test:

1. package version equals 0.2;
2. a synthetic `DRIVER1 → Q1...Q10` network recovers `DRIVER1`;
3. reversing all edges prevents the same upstream result;
4. the three-layer neighborhood follows directed paths correctly;
5. the driver is excluded from its neighborhood by default;
6. a known hypergeometric example matches `stats::phyper`;
7. BH adjustment is performed within a signature;
8. malformed or inconsistent query/background inputs fail.

The current package has already passed the first synthetic upstream-driver
test in an isolated installation.

## Implementation order

1. Implement and test `install_kda.R`.
2. Implement the `lib/` validation and input functions.
3. Implement global KDA and neighborhood caching for one small network.
4. Reproduce the synthetic smoke test.
5. Build the Phase 09 query/background preparation step.
6. Run one prespecified microglia signature end to end.
7. Inspect coverage, runtime, and raw results.
8. Scale global KDA to all nine networks.
9. Run the primary signature panel.
10. Run secondary signatures and sensitivity analyses.

The first production analysis should remain small and fully inspectable before
submitting the complete multi-network job set.
