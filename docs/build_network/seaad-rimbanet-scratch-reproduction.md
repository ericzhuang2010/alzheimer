# Reproducing the SEA-AD RIMBANet Minerva scratch tree

## Purpose and recovery boundary

`/sc/arion/scratch/zhuane01/alzheimer` is a disposable cache for large files
that can be downloaded again or regenerated. It is not a backup. The
persistent recovery authority is the Git checkout at
`/sc/arion/work/zhuane01/alzheimer`, together with controlled-access
credentials and the small, untracked donor crosswalk.

If only the validated release is needed for KDA or downstream analysis, do
not rebuild scratch. Use the compact network release under
`data/bayesian_network/SEAAD_A9_2024/`. Rehydrate scratch only when rerunning,
auditing, or extending network construction.

Exact recovery is possible only after every required production source row in
`data/reference/rimbanet/sources.tsv` has a frozen release, checksum, and
non-placeholder status. As of September 4, 2026, the NIAGADS WGS release and
ENCODE TF-target transformation still contain `TO_BE_FROZEN` values. Those
are explicit blockers: a portal URL alone is not enough to reproduce the
scientific input exactly.

## Persistent material that must survive a scratch purge

Keep these items in `/sc/arion/work/zhuane01/alzheimer` or another approved
persistent/controlled location:

- the repository commit containing the code, container recipe, configs, and
  this runbook;
- `config/seaad_rimbanet.yml` and
  `config/seaad_rimbanet_execution.yml`, with all production placeholders
  frozen;
- `data/reference/rimbanet/sources.tsv`, with exact releases and SHA-256s;
- the small controlled identity map at
  `data/seaad_wgs/NG00174/sample_crosswalk.tsv` (untracked; protect according
  to its data-use agreement);
- the final `data/bayesian_network/SEAAD_A9_2024/` release and its checksums;
- authorization and retrieval instructions for controlled NIAGADS data.

Do not keep the only copy of an irreplaceable or manually curated file in
scratch.

## Scratch layout and reproduction authority

| Scratch path | Contents | Reproduction authority |
|---|---|---|
| `cache/apptainer/` | Download/build cache | Recreated automatically by Apptainer; no recovery needed |
| `tmp/apptainer/` | Container build temporary files | Recreated empty; never resume these files |
| `external_tools/BayesianNetwork/` | Pinned public source checkout | GitHub repository plus frozen commit |
| `external_tools/proteomics_networks/` | Optional Wang-workflow reference checkout | GitHub repository plus frozen commit; not a production dependency |
| `external_tools/containers/seaad-rimbanet.sif` | Linux x86-64 runtime | `containers/rimbanet/Apptainer.def` plus pinned source checkout |
| `data/reference/rimbanet/encode_tf_targets.tsv.gz` | Frozen TF-target input | Exact ENCODE release and transformation contract; currently not frozen |
| `data/seaad_wgs/NG00174/source/` | Controlled downloaded WGS/PLINK source | NIAGADS NG00174 approved download plus frozen file manifest; currently not frozen |
| `data/seaad_wgs/NG00174/derived/` | QC PLINK files, dosage matrix, positions, ancestry PCs | `11_prepare_seaad_genotypes.sh` |
| `results/validation_human/05_pseudobulk/direct_broad_counts/` | Seven broad-cell count/sample shards | Validated VH05 raw-UMI aggregation |
| `results/validation_human/11_seaad_rimbanet/11a_*` | Input/runtime audits | VH11 audit and environment scripts |
| `results/validation_human/11_seaad_rimbanet/11b_expression/` | Filtered, normalized, and adjusted expression | `11_prepare_rimbanet_expression.R` |
| `results/validation_human/11_seaad_rimbanet/11c_genetics/` | Genotype QC and cell-type eQTL results | Genotype and eQTL preparation scripts |
| `results/validation_human/11_seaad_rimbanet/11d_priors/` | CIT and combined prior evidence | eQTL/CIT and prior-building scripts |
| `results/validation_human/11_seaad_rimbanet/11e_inputs/` | Discretized matrices and exact RIMBANet inputs | Discretization and input-preparation scripts |
| `results/validation_human/11_seaad_rimbanet/11f_runs/` | 1,000 search outputs per network | LSF array task wrapper |
| `results/validation_human/11_seaad_rimbanet/11g_consensus/` | Recurrence and de-loop intermediates | Consensus wrapper and all 1,000 validated searches |
| `results/validation_human/11_seaad_rimbanet/11h_release_qc/` | Independent topology/release QC | Publication validator |
| `results/validation_human/11_seaad_rimbanet/logs/` | LSF logs | New submissions; logs are not scientific source data |

## 1. Recreate the empty layout

Run on Minerva:

```bash
export PROJECT_ROOT=/sc/arion/work/zhuane01/alzheimer
export RIMBANET_STORAGE_ROOT=/sc/arion/scratch/zhuane01/alzheimer
export RIMBANET_OUTPUT_ROOT="$RIMBANET_STORAGE_ROOT/results/validation_human"
export RIMBANET_LOG_ROOT="$RIMBANET_OUTPUT_ROOT/11_seaad_rimbanet/logs"
export RIMBANET_SOURCE="$RIMBANET_STORAGE_ROOT/external_tools/BayesianNetwork"
export RIMBANET_IMAGE="$RIMBANET_STORAGE_ROOT/external_tools/containers/seaad-rimbanet.sif"
export APPTAINER_CACHEDIR="$RIMBANET_STORAGE_ROOT/cache/apptainer"
export APPTAINER_TMPDIR="$RIMBANET_STORAGE_ROOT/tmp/apptainer"

mkdir -p \
  "$APPTAINER_CACHEDIR" \
  "$APPTAINER_TMPDIR" \
  "$RIMBANET_STORAGE_ROOT/external_tools/containers" \
  "$RIMBANET_STORAGE_ROOT/data/reference/rimbanet" \
  "$RIMBANET_STORAGE_ROOT/data/seaad_wgs/NG00174/source" \
  "$RIMBANET_STORAGE_ROOT/data/seaad_wgs/NG00174/derived" \
  "$RIMBANET_OUTPUT_ROOT/05_pseudobulk/direct_broad_counts" \
  "$RIMBANET_LOG_ROOT/preparation"

test -w "$PROJECT_ROOT"
test -w "$RIMBANET_STORAGE_ROOT"
df -h "$PROJECT_ROOT" "$RIMBANET_STORAGE_ROOT"
```

Do not create empty status files or copy old task status files into the new
tree. Status and provenance records must be regenerated by their owning
stage.

## 2. Reproduce the RIMBANet checkout

```bash
if [[ ! -d "$RIMBANET_SOURCE/.git" ]]; then
  git clone https://github.com/mw201608/BayesianNetwork.git "$RIMBANET_SOURCE"
fi
git -C "$RIMBANET_SOURCE" fetch --all --tags
git -C "$RIMBANET_SOURCE" checkout --detach \
  ebd5f4a6c31da22705622e71b6dc5f1eae195fdd
test "$(git -C "$RIMBANET_SOURCE" rev-parse HEAD)" = \
  "ebd5f4a6c31da22705622e71b6dc5f1eae195fdd"
```

Record the checkout identity in `data/reference/rimbanet/sources.tsv`. Do not
modify the external checkout in place.

The Wang proteomics repository is reference-only and is not required to run
the SEA-AD workflow. Recreate it only when auditing the historical method:

```bash
WANG_REFERENCE="$RIMBANET_STORAGE_ROOT/external_tools/proteomics_networks"
if [[ ! -d "$WANG_REFERENCE/.git" ]]; then
  git clone https://github.com/wange230/proteomics_networks.git \
    "$WANG_REFERENCE"
fi
git -C "$WANG_REFERENCE" fetch --all --tags
git -C "$WANG_REFERENCE" checkout --detach \
  c0f51fa7e1195be4469fbad122dd5e96db31a397
test "$(git -C "$WANG_REFERENCE" rev-parse HEAD)" = \
  "c0f51fa7e1195be4469fbad122dd5e96db31a397"
```

## 3. Rebuild and freeze the Apptainer image

The `%files` source in the definition is relative to the build working
directory, so build from the scratch root:

```bash
module load apptainer  # omit if already available
cd "$RIMBANET_STORAGE_ROOT"
apptainer build --fakeroot "$RIMBANET_IMAGE" \
  "$PROJECT_ROOT/containers/rimbanet/Apptainer.def"
apptainer test "$RIMBANET_IMAGE"
sha256sum "$RIMBANET_IMAGE"
cd "$PROJECT_ROOT"
```

Write the observed digest to `runtime.image_sha256` in
`config/seaad_rimbanet_execution.yml`. A rebuilt image is not eligible for
resume merely because it has the same filename; its digest and the contained
`testBN` checksum must match the frozen provenance. If `--fakeroot` is not
permitted, use the approved private x86-64 OCI-to-SIF route documented in
`containers/rimbanet/README.md`.

## 4. Reproduce or restage broad-cell pseudobulk shards

If a validated copy exists in the work checkout or approved project storage,
stage it with checksums:

```bash
PSEUDOBULK_SOURCE="$PROJECT_ROOT/results/validation_human/05_pseudobulk/direct_broad_counts"
PSEUDOBULK_SCRATCH="$RIMBANET_OUTPUT_ROOT/05_pseudobulk/direct_broad_counts"
mkdir -p "$PSEUDOBULK_SCRATCH"
rsync -a --checksum "$PSEUDOBULK_SOURCE/" "$PSEUDOBULK_SCRATCH/"
```

If no validated copy survives, regenerate it from the frozen A9 H5AD and
metadata with the VH00–VH06 workflow in
`scripts/validation_human/README.md`. The H5AD identity, metadata SHA-256,
donor selection, gene order, and VH05/VH06 statuses must all pass. Run the
rebuild from a scratch-backed checkout or staging area so the 37.9-GB H5AD,
1.4-GB metadata table, checkpoints, and new count shards do not consume the
work allocation. Then place only the seven `*.counts.tsv.gz` and companion
`*.samples.tsv` files at `PSEUDOBULK_SCRATCH`.

Do not use count shards from a different H5AD, cohort, feature order, or
configuration even if their filenames match.

## 5. Restore controlled WGS and regenerate derived genetics

The small curated donor/WGS identity crosswalk remains persistently at:

```text
/sc/arion/work/zhuane01/alzheimer/data/seaad_wgs/NG00174/sample_crosswalk.tsv
```

Restore the raw WGS files through the approved NIAGADS NG00174 mechanism into
the prefix declared by `inputs.wgs_raw_plink_prefix`. Do not invent an
automated URL or rename a different release to match the expected prefix.
Before production, freeze in `data/reference/rimbanet/sources.tsv`:

- the exact NG00174 release/version;
- every retrieved filename, byte count, and SHA-256;
- the retrieval method and date;
- genome build and allele conventions.

There is intentionally no download command in this runbook while the source
manifest says `TO_BE_FROZEN`. Recovery must stop at this step until approved
access and exact file identities are available.

Once the raw PLINK set and persistent crosswalk pass the VH11 audit, regenerate
all derived WGS files with the genotype preparation job in the main build
plan. Its canonical worker command is:

```bash
apptainer exec \
  --bind "$PROJECT_ROOT:$PROJECT_ROOT" \
  --bind "$RIMBANET_STORAGE_ROOT:$RIMBANET_STORAGE_ROOT" \
  --pwd "$PROJECT_ROOT" "$RIMBANET_IMAGE" \
  bash scripts/validation_human/11_prepare_seaad_genotypes.sh \
    --config config/seaad_rimbanet.yml
```

The stage must recreate the QC PLINK prefix, dosage matrix, variant positions,
ancestry PCs, QC summaries, artifact hashes, and `genotype_status.tsv`. Do not
copy derived files from another configuration.

## 6. Restore the ENCODE TF-target input

Retrieve and transform the exact release declared by the frozen ENCODE row in
`data/reference/rimbanet/sources.tsv`, then write the result to:

```text
/sc/arion/scratch/zhuane01/alzheimer/data/reference/rimbanet/encode_tf_targets.tsv.gz
```

The current release name, source checksum, and transformation rules are not
yet frozen, and the repository does not yet contain a canonical ENCODE
transformation script. Therefore this file is not exactly reproducible today.
Production and scratch recovery must remain blocked until the release,
download identity, column/identifier mapping, filtering rules, output sort
order, compression command, and final SHA-256 are recorded. Never substitute
a current ENCODE download for the missing frozen snapshot.

## 7. Regenerate VH11 products in dependency order

After source inputs and the image are restored, run stages in this order:

1. `11_audit_rimbanet_inputs.py` and
   `11_check_rimbanet_environment.py` recreate `11a_audit` and
   `11a_environment`.
2. The genotype preparation job recreates shared WGS-derived files and the
   shared `11c_genetics` status.
3. The seven-network preparation array runs expression preparation, cell-type
   eQTL/CIT, discretization, exact input generation, and prior assembly. This
   recreates `11b_expression` through `11e_inputs`.
4. Submit Microglia first. Its 1,000 LSF tasks recreate
   `11f_runs/Microglia`; validate all 1,000 before consensus.
5. Recreate `11g_consensus/Microglia`, run independent QC, and require the
   pilot gate to pass.
6. Submit and validate the remaining six 1,000-task arrays, then regenerate
   their consensus and release-QC directories.

Use the exact commands in the “Audit and prepare production inputs,” “Submit
and gate,” and “Scale out” sections of
`docs/build_network/seaad-rimbanet-build.plan.md`. Those commands bind both
storage roots and derive all output paths from the frozen configs.

Never rebuild a downstream directory by hand. If an upstream checksum changes,
invalidate and regenerate every dependent stage.

## 8. Verify recovery before resume

Recovery is valid only when all applicable checks pass:

```bash
test "$(git -C "$RIMBANET_SOURCE" rev-parse HEAD)" = \
  "ebd5f4a6c31da22705622e71b6dc5f1eae195fdd"
apptainer test "$RIMBANET_IMAGE"

cd "$PROJECT_ROOT"
.venv/bin/python scripts/validation_human/11_audit_rimbanet_inputs.py \
  --config config/seaad_rimbanet.yml

apptainer exec \
  --bind "$PROJECT_ROOT:$PROJECT_ROOT" \
  --bind "$RIMBANET_STORAGE_ROOT:$RIMBANET_STORAGE_ROOT" \
  --pwd "$PROJECT_ROOT" "$RIMBANET_IMAGE" \
  python scripts/validation_human/11_check_rimbanet_environment.py \
    --config config/seaad_rimbanet.yml \
    --execution-config config/seaad_rimbanet_execution.yml
```

Both scripts must report `validated_complete`. For a partial recovery, run
`11_validate_rimbanet_runs.py` for each affected network. Existing search
tasks may be reused only when their validated status, config hash, combined
input hash, and output hash match. Otherwise rerun them; never lower the
1,000-search denominator.

## Recovery status checklist

- [ ] Work checkout commit and frozen configuration identified.
- [ ] Persistent controlled donor crosswalk present.
- [ ] Scratch directory exists, is writable, and has sufficient free space.
- [ ] RIMBANet checkout is at the pinned commit.
- [ ] SIF passes `apptainer test`; image and binary SHA-256s match.
- [ ] Pseudobulk shards pass frozen identity and cohort checks.
- [ ] NIAGADS release and every raw WGS file are frozen and verified.
- [ ] ENCODE release and deterministic transformation are frozen and verified.
- [ ] VH11 audit and runtime environment are `validated_complete`.
- [ ] Each regenerated stage has matching artifact/status records.
- [ ] Microglia pilot passes before six-network scale-out.
- [ ] Compact final releases and release manifests exist persistently in work.
