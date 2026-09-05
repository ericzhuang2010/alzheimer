#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$PROJECT_ROOT"

if [[ -x .venv/bin/python ]]; then
  PYTHON="${PYTHON:-.venv/bin/python}"
else
  PYTHON="${PYTHON:-python3}"
fi

command -v "$PYTHON" >/dev/null 2>&1 || {
  echo "Python is unavailable: $PYTHON" >&2
  exit 2
}
command -v Rscript >/dev/null 2>&1 || {
  echo "Rscript is required for local syntax checks" >&2
  exit 2
}
[[ -f external_tools/BayesianNetwork/script/countDirectLinksMatrix.pl ]] || {
  echo "Clone the pinned RIMBANet checkout under external_tools/BayesianNetwork first." >&2
  exit 2
}

PYTHON_SCRIPTS=(
  scripts/validation_human/rimbanet_common.py
  scripts/validation_human/11_audit_rimbanet_inputs.py
  scripts/validation_human/11_import_seaad_array.py
  scripts/validation_human/11_build_rimbanet_priors.py
  scripts/validation_human/11_check_rimbanet_environment.py
  scripts/validation_human/11_prepare_rimbanet_inputs.py
  scripts/validation_human/11_submit_rimbanet_minerva.py
  scripts/validation_human/11_validate_publish_seaad_networks.py
  scripts/validation_human/11_validate_rimbanet_runs.py
)
BASH_SCRIPTS=(
  scripts/validation_human/11_build_rimbanet_consensus.sh
  scripts/validation_human/11_prepare_rimbanet_minerva.lsf
  scripts/validation_human/11_prepare_seaad_genotypes.sh
  scripts/validation_human/11_run_rimbanet_task.sh
  scripts/validation_human/11_smoke_test_rimbanet_local.sh
  scripts/validation_human/11_submit_rimbanet_minerva.lsf
)
R_SCRIPTS=(
  scripts/validation_human/11_discretize_rimbanet_expression.R
  scripts/validation_human/11_prepare_rimbanet_expression.R
  scripts/validation_human/11_run_celltype_eqtl.R
)

"$PYTHON" -m py_compile "${PYTHON_SCRIPTS[@]}"
for script in "${BASH_SCRIPTS[@]}"; do
  bash -n "$script"
done
for script in "${R_SCRIPTS[@]}"; do
  Rscript --vanilla -e "parse(file='$script')" >/dev/null
done

"$PYTHON" -m pytest -q \
  tests/validation_human/test_seaad_rimbanet_contracts.py \
  tests/validation_human/test_seaad_rimbanet_network_contract.py

echo "Local SEA-AD RIMBANet smoke tests passed."
