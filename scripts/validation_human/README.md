# SEA-AD Fine-Supertype DEG Validation

This directory implements the clean VH00-VH08 rebuild specified in
docs/validation_human/seaad_deg_processing_plan.md.

Run phases from the repository root with the frozen config:

~~~bash
export PYTHONDONTWRITEBYTECODE=1
export SEAAD_DEG_CONFIG=scripts/validation_human/seaad_deg_config.yml

.venv/bin/python scripts/validation_human/00_check_environment.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/01_audit_inputs.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/02_build_donor_cohort.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/03_harmonize_genes.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/04_build_supertype_manifest.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/05_stream_pseudobulk.py --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/06_validate_pseudobulk.R --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/07_build_contrast_manifests.R --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/08_run_deg.R --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/08_finalize_deg_release.py --config "$SEAAD_DEG_CONFIG"
~~~

All scientific outputs are isolated under results/validation_human/. Raw
inputs, Phase 18 references, networks, and unrelated ROSMAP results are opened
read-only.

## VH11: full-integrative SEA-AD RIMBANet networks

VH11 builds seven donor-level broad-cell networks with matched SEA-AD GDA-8
eQTL/CIT and pinned ENCODE TF-target priors. It never substitutes the
expression-only variant when genetics or TF priors are missing.

Run the platform-independent synthetic test locally:

~~~bash
bash scripts/validation_human/11_smoke_test_rimbanet_local.sh
~~~

The complete Minerva setup, Apptainer build, input-preparation, LSF submission,
resume, consensus, and release commands are in
`docs/build_network/seaad-rimbanet-build.plan.md`.

On Minerva, keep the repository and compact final releases in the work
allocation. The frozen VH11 configs route the RIMBANet checkout, SIF, staged
pseudobulk/GDA-8/ENCODE inputs, generated matrices, 7,000 search outputs,
intermediates, and logs to disposable scratch:

~~~text
/sc/arion/work/zhuane01/alzheimer       code, configs, final releases
/sc/arion/scratch/zhuane01/alzheimer    reproducible/downloadable bulk files
~~~

Start from the repository root and export both roots:

~~~bash
export PROJECT_ROOT=/sc/arion/work/zhuane01/alzheimer
export RIMBANET_STORAGE_ROOT=/sc/arion/scratch/zhuane01/alzheimer
export RIMBANET_OUTPUT_ROOT="$RIMBANET_STORAGE_ROOT/results/validation_human"
export RIMBANET_LOG_ROOT="$RIMBANET_OUTPUT_ROOT/11_seaad_rimbanet/logs"
export RIMBANET_IMAGE="$RIMBANET_STORAGE_ROOT/external_tools/containers/seaad-rimbanet.sif"
export SEAAD_RIMBANET_CONFIG=config/seaad_rimbanet.yml
export SEAAD_RIMBANET_EXECUTION=config/seaad_rimbanet_execution.yml
cd "$PROJECT_ROOT"

.venv/bin/python scripts/validation_human/11_audit_rimbanet_inputs.py \
  --config "$SEAAD_RIMBANET_CONFIG"
.venv/bin/python scripts/validation_human/11_check_rimbanet_environment.py \
  --config "$SEAAD_RIMBANET_CONFIG" \
  --execution-config "$SEAAD_RIMBANET_EXECUTION"
~~~

Both commands must report `validated_complete`. A blocked status is a hard
prerequisite failure, not permission to continue expression-only.

Prepare expression for the seven networks:

~~~bash
for network in \
  Astrocytes Excitatory_neurons Inhibitory_neurons Microglia \
  OPCs Oligodendrocytes Vasculature_cells
do
  Rscript --vanilla scripts/validation_human/11_prepare_rimbanet_expression.R \
    --config "$SEAAD_RIMBANET_CONFIG" --network "$network"
done

bash scripts/validation_human/11_prepare_seaad_genotypes.sh \
  --config "$SEAAD_RIMBANET_CONFIG"

for network in \
  Astrocytes Excitatory_neurons Inhibitory_neurons Microglia \
  OPCs Oligodendrocytes Vasculature_cells
do
  Rscript --vanilla scripts/validation_human/11_run_celltype_eqtl.R \
    --config "$SEAAD_RIMBANET_CONFIG" --network "$network" --stage all
  Rscript --vanilla scripts/validation_human/11_discretize_rimbanet_expression.R \
    --config "$SEAAD_RIMBANET_CONFIG" --network "$network"

  # Run inside the pinned Linux image so testBN is available.
  python scripts/validation_human/11_prepare_rimbanet_inputs.py \
    --config "$SEAAD_RIMBANET_CONFIG" --network "$network" \
    --binary /usr/local/bin/testBN
  python scripts/validation_human/11_build_rimbanet_priors.py \
    --config "$SEAAD_RIMBANET_CONFIG" --network "$network"
done
~~~

The production gate is Microglia. On Minerva, submit its 1,000-task LSF array
through the checked wrapper first:

~~~bash
export CONFIG="$SEAAD_RIMBANET_CONFIG"
export NETWORK=Microglia
export LSF_PROJECT=YOUR_MINERVA_ALLOCATION
.venv/bin/python scripts/validation_human/11_submit_rimbanet_minerva.py \
  --config "$SEAAD_RIMBANET_CONFIG" \
  --execution-config "$SEAAD_RIMBANET_EXECUTION" \
  --network Microglia --lsf-project "$LSF_PROJECT"

.venv/bin/python scripts/validation_human/11_validate_rimbanet_runs.py \
  --config "$SEAAD_RIMBANET_CONFIG" --network Microglia

apptainer exec --bind "$PROJECT_ROOT:$PROJECT_ROOT" \
  --bind "$RIMBANET_STORAGE_ROOT:$RIMBANET_STORAGE_ROOT" \
  --pwd "$PROJECT_ROOT" "$RIMBANET_IMAGE" \
  bash scripts/validation_human/11_build_rimbanet_consensus.sh \
    --config "$SEAAD_RIMBANET_CONFIG" --network Microglia \
    --binary /usr/local/bin/testBN

apptainer exec --bind "$PROJECT_ROOT:$PROJECT_ROOT" \
  --bind "$RIMBANET_STORAGE_ROOT:$RIMBANET_STORAGE_ROOT" \
  --pwd "$PROJECT_ROOT" "$RIMBANET_IMAGE" \
  python scripts/validation_human/11_validate_publish_seaad_networks.py \
    --config "$SEAAD_RIMBANET_CONFIG" --network Microglia \
    --binary /usr/local/bin/testBN
~~~

Only after
`$RIMBANET_OUTPUT_ROOT/11_seaad_rimbanet/11f_runs/pilot_gate.tsv` records
`passed` should the same
submit/validate/consensus/publish sequence be run for the other six networks.
Successful task outputs are resume-safe: a task is reused only when its config
and combined input hashes match. Consensus is blocked unless all 1,000 task
records validate, so missing jobs cannot change the denominator.

Final permitted release files are copied atomically to the persistent
`data/bayesian_network/SEAAD_A9_2024/<cell_type>/` directory. Controlled
GDA-8 data, dense matrices, priors, container/source files, and per-search outputs remain
in scratch. Scratch may be purged, so retain input identities/checksums and the
final release in the work checkout and rebuild/restage bulk artifacts when
needed. Follow the
[scratch reproduction runbook](../../docs/build_network/seaad-rimbanet-scratch-reproduction.md)
for the path-by-path rebuild order, validation checks, and inputs that are not
yet frozen. Current ROSMAP networks and VH10 KDA configuration are not changed
by VH11.
