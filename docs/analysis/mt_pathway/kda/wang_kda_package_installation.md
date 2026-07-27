# Wang KDA package installation

## Scope

This document covers only installation and verification of Wang's third-party
KDA package. For the project-maintained wrapper design, see
[wang_kda_interface_implementation.md](wang_kda_interface_implementation.md).
For analysis commands, see
[wang_kda_interface_usage.md](wang_kda_interface_usage.md).

Package installation does not prepare KDA inputs or run an analysis.

## Package identity

The Wang repository supplies:

```text
Package: KDA
Version: 0.2
Date: 2014-07-29
Author: Bin Zhang
License: Artistic-2.0
```

The Wang paper calls the version `0.02`; the archive and its `DESCRIPTION` use
`0.2`. The maintained interface requires exactly KDA 0.2 and records both
labels in run manifests.

Expected source archive:

```text
archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

Expected SHA-256:

```text
7b185e16ef855a4d19061722f3920100777c19acd8357107a31928b73fe9e70f
```

The archive is pure R and does not require a compiler, Python, Conda, CUDA, or
a GPU.

## Required R environment

The project records R 4.3.3 in `renv.lock` and activates `renv` through the
repository-root `.Rprofile`. The KDA interface also uses:

- `data.table`;
- `digest`;
- `jsonlite`; and
- `R.utils`, used by `data.table` for gzip output.

Run installation commands from the repository root.

## Obtain the pinned source archive

The archive is intentionally gitignored. Download the exact file from the
pinned Wang repository commit:

```bash
mkdir -p archive/wang_kda_code/KDA_analysis

wget -O archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz.download \
  https://raw.githubusercontent.com/wange230/proteomics_networks/c0f51fa7e1195be4469fbad122dd5e96db31a397/codes/Baysian_network/KDA_analysis/KDA-0.2.tar.gz

printf '%s  %s\n' \
  '7b185e16ef855a4d19061722f3920100777c19acd8357107a31928b73fe9e70f' \
  'archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz.download' \
  | sha256sum -c - \
  && mv archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz.download \
        archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

The checksum command must report `OK`. A failed download remains at the
`.download` path and must not be installed.

Verify an existing archive with:

```bash
sha256sum archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

Never install an unpinned branch or a file with a different checksum.

## Local workstation installation

Restore KDA and the maintained interface dependencies:

```bash
Rscript -e 'renv::restore(
  packages = c("KDA", "data.table", "digest", "jsonlite", "R.utils"),
  prompt = FALSE
)'
```

Alternatively, the maintained installer verifies the archive, R version,
package version, and required exports:

```bash
Rscript scripts/analysis/kda/install_kda.R \
  --archive archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz
```

The installer is a no-op if the correct KDA version is already installed. Use
`--force` only to repair or audit the package installation.

Verify the result:

```bash
Rscript -e '
stopifnot(as.character(packageVersion("KDA")) == "0.2")
stopifnot(all(c("keydriverInSubnetwork", "downStreamGenes") %in%
              getNamespaceExports("KDA")))
cat("KDA version:", as.character(packageVersion("KDA")), "\n")
cat("KDA location:", find.package("KDA"), "\n")
'
```

Do not run `renv::snapshot()` merely to restore the recorded environment.

## Minerva installation

### Repository and storage

The established checkout is:

```text
/sc/arion/work/zhuane01/alzheimer
```

Use the reusable cache:

```bash
mkdir -p /sc/arion/work/zhuane01/.cache/renv
export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv
```

Use the same cache setting in interactive and LSF sessions. Do not copy the
workstation's `renv/library/`; Minerva must create its own platform-specific
project library.

Before requesting resources, check the current allocation and queues:

```bash
mybalance
groups
showquota -u "$USER"
showquota -p zhangb03a
bqueues
```

The examples use `acc_zhangb03a`. Confirm access with `mybalance`.

### Interactive installation

From the login node, update the checkout and download the archive using the
pinned procedure above. Then request an interactive compute shell:

```bash
cd /sc/arion/work/zhuane01/alzheimer
git pull --ff-only

bsub -q interactive \
  -P acc_zhangb03a \
  -n 1 \
  -W 01:00 \
  -R 'rusage[mem=8000]' \
  -R 'span[hosts=1]' \
  -Is /bin/bash
```

After the prompt changes to a compute node:

```bash
cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt

mkdir -p /sc/arion/work/zhuane01/.cache/renv
export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv

Rscript -e 'renv::restore(
  packages = c("KDA", "data.table", "digest", "jsonlite", "R.utils"),
  prompt = FALSE
)'

Rscript -e '
stopifnot(as.character(packageVersion("KDA")) == "0.2")
stopifnot(all(c("keydriverInSubnetwork", "downStreamGenes") %in%
              getNamespaceExports("KDA")))
cat("KDA version:", as.character(packageVersion("KDA")), "\n")
cat("KDA location:", find.package("KDA"), "\n")
'
```

Type `exit` when installation verification is complete.

### LSF batch installation

Interactive installation is easier to diagnose, but the same restore can run
as an LSF batch job. Save the following outside `scripts/analysis/kda/` as a
temporary site-specific job file, for example `install_kda_minerva.lsf`:

```bash
#!/bin/bash
#BSUB -J install_kda
#BSUB -P acc_zhangb03a
#BSUB -q express
#BSUB -n 1
#BSUB -W 01:00
#BSUB -R "rusage[mem=8000]"
#BSUB -R "span[hosts=1]"
#BSUB -L /bin/bash
#BSUB -oo results/minerva_production/12_kda/logs/install_%J.out
#BSUB -eo results/minerva_production/12_kda/logs/install_%J.err

set -euo pipefail

cd /sc/arion/work/zhuane01/alzheimer
source docs/minerva/cmd_to_run_after_logging_in.txt
export RENV_PATHS_CACHE=/sc/arion/work/zhuane01/.cache/renv

Rscript -e 'renv::restore(
  packages = c("KDA", "data.table", "digest", "jsonlite", "R.utils"),
  prompt = FALSE
)'

Rscript -e '
stopifnot(as.character(packageVersion("KDA")) == "0.2")
stopifnot(all(c("keydriverInSubnetwork", "downStreamGenes") %in%
              getNamespaceExports("KDA")))
cat("KDA version:", as.character(packageVersion("KDA")), "\n")
cat("KDA location:", find.package("KDA"), "\n")
'
```

Submit it from the repository root:

```bash
mkdir -p results/minerva_production/12_kda/logs
bsub < install_kda_minerva.lsf
```

Monitor with `bjobs`, `bjobs -l JOB_ID`, and `bpeek JOB_ID`.

## Expected filesystem end state

After installation:

| Path | Expected state |
|---|---|
| `renv/library/R-4.3/<platform>/KDA/` | KDA 0.2 project-library entry, often linked to the machine's `renv` cache. |
| Other requested package entries under `renv/library/` | Created if previously missing. |
| `archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz` | Unchanged, checksum-verified source archive. |
| `renv.lock` | Unchanged during restore. |
| `scripts/analysis/kda/` | Unchanged during package installation. |
| `data/bayesian_network/` | Unchanged. |
| KDA analysis results | None created. |
| Deleted repository files | None. |

`renv_restore.log` and `renv_restore_retry.log` are diagnostic logs, not
installed package contents. They may be deleted after a successful restore if
they are no longer needed for troubleshooting.

## Troubleshooting

- **Archive missing:** download it to the exact path recorded above.
- **Checksum mismatch:** do not install it; download the pinned file again.
- **Wrong R version:** load R 4.3.3 before restoring.
- **KDA is absent after restore:** confirm that the archive exists before
  running `renv::restore()`.
- **Gzip output later fails:** restore `R.utils`.
- **Minerva download fails:** source
  `docs/minerva/cmd_to_run_after_logging_in.txt` so the repository's proxy
  settings are active.

