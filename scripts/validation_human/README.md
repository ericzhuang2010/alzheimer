# SEA-AD human validation pipeline

This directory contains the isolated implementation of the SEA-AD broad-cell
pseudobulk DEG plan in
`docs/validation_human/seaad_deg_processing_plan.md`.

All code and job definitions live below `scripts/validation_human/`. All
generated scientific files, including smoke outputs, checkpoints, logs, model
objects, and temporary files, live below `results/validation_human/`.
Existing ROSMAP scripts and results are read-only references.

Run from the repository root:

```bash
export SEAAD_DEG_CONFIG=scripts/validation_human/seaad_deg_config.yml
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python scripts/validation_human/00_check_environment.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/01_audit_inputs.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/02_build_donor_cohort.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/03_harmonize_genes.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/04_build_nucleus_group_manifest.py --config "$SEAAD_DEG_CONFIG"
.venv/bin/python scripts/validation_human/05_stream_broad_pseudobulk.py --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/06_validate_pseudobulk.R --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/07_build_contrast_manifest.R --config "$SEAAD_DEG_CONFIG"
Rscript scripts/validation_human/08_run_broad_deg.R --config "$SEAAD_DEG_CONFIG"
```

Every phase requires validated upstream status, uses atomic output writes, and
returns a nonzero exit code when a hard gate fails.
