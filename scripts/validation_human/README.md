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
