# RIMBANet runtime

This image builds the legacy Linux RIMBANet executable against its bundled
Xerces-C++ 2.8 source and installs the SEA-AD preparation dependencies.

The upstream repository does not contain an explicit license file. Do not
publish or redistribute the resulting image, source, or binary until the
license is confirmed. On Minerva, the checkout and image live under the
disposable `/sc/arion/scratch/zhuane01/alzheimer/` storage root so they do not
consume the limited `/sc/arion/work/zhuane01` allocation.

From the repository root:

```bash
git clone https://github.com/mw201608/BayesianNetwork.git \
  external_tools/BayesianNetwork
git -C external_tools/BayesianNetwork checkout \
  ebd5f4a6c31da22705622e71b6dc5f1eae195fdd

docker build -f containers/rimbanet/Dockerfile \
  -t seaad-rimbanet:ebd5f4a6 .
docker image inspect seaad-rimbanet:ebd5f4a6 \
  --format '{{index .RepoDigests 0}}'
```

For a direct x86-64 Apptainer build on Minerva, keep this project repository in
the work allocation but build all downloadable/reproducible assets, including
the external RIMBANet checkout, in scratch:

```bash
export PROJECT_ROOT=/sc/arion/work/zhuane01/alzheimer
export RIMBANET_STORAGE_ROOT=/sc/arion/scratch/zhuane01/alzheimer
export RIMBANET_SOURCE="$RIMBANET_STORAGE_ROOT/external_tools/BayesianNetwork"
export RIMBANET_IMAGE="$RIMBANET_STORAGE_ROOT/external_tools/containers/seaad-rimbanet.sif"
export APPTAINER_CACHEDIR="$RIMBANET_STORAGE_ROOT/cache/apptainer"
export APPTAINER_TMPDIR="$RIMBANET_STORAGE_ROOT/tmp/apptainer"

module load apptainer  # only if apptainer is not already available
mkdir -p \
  "$RIMBANET_STORAGE_ROOT/external_tools/containers" \
  "$APPTAINER_CACHEDIR" \
  "$APPTAINER_TMPDIR"
if [[ ! -d "$RIMBANET_SOURCE/.git" ]]; then
  git clone https://github.com/mw201608/BayesianNetwork.git "$RIMBANET_SOURCE"
fi
git -C "$RIMBANET_SOURCE" checkout \
  ebd5f4a6c31da22705622e71b6dc5f1eae195fdd

# %files paths are resolved from the current directory, so build from the
# scratch storage root where external_tools/BayesianNetwork is staged.
cd "$RIMBANET_STORAGE_ROOT"
apptainer build --fakeroot "$RIMBANET_IMAGE" \
  "$PROJECT_ROOT/containers/rimbanet/Apptainer.def"
APPTAINERENV_R_PROFILE_USER=/dev/null apptainer test "$RIMBANET_IMAGE"
sha256sum "$RIMBANET_IMAGE"
cd "$PROJECT_ROOT"
```

The definition file copies the pinned, local `external_tools/BayesianNetwork`
checkout relative to the build working directory. If Minerva does not enable
fakeroot builds for the allocation, build a private x86-64 OCI image on an
approved builder and convert that image to SIF in the same scratch location.

Disabling `R_PROFILE_USER` for the built-in test prevents a bound checkout's
`.Rprofile` from activating its host `renv` library and masking the R packages
installed in the image. Production R entry points additionally use
`Rscript --vanilla`.

Minerva scratch is disposable. The checkout and image must be reproducible
from the pinned commit and this definition, and the SIF checksum must be
recorded in the execution config. Rebuild or restage them after a purge; never
keep the only copy of controlled raw data or final network releases in scratch.
The complete recovery procedure is in the
[scratch reproduction runbook](../../docs/build_network/seaad-rimbanet-scratch-reproduction.md).

The build must succeed and the image digest must replace
`TO_BE_FROZEN` in `config/seaad_rimbanet_execution.yml` before production.
Record the SIF SHA-256 in the execution config.

The repository wrappers require these container commands:

- `testBN`
- `generateBIF`
- `Rscript` with `MatrixEQTL`, `cit`, `data.table`, `digest`, `edgeR`, and
  `yaml`
- `plink2`, `bcftools`, Perl 5, bash, `bc`, and GNU coreutils

The image is intentionally not built automatically. Its build context includes
the locally pinned external checkout, and production execution is blocked until
the image digest and RIMBANet binary checksum are frozen.
