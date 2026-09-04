#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --config FILE --network NAME [--binary PATH]" >&2
}

CONFIG=""
NETWORK=""
BINARY="${RIMBANET_BINARY:-testBN}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --network) NETWORK="$2"; shift 2 ;;
    --binary) BINARY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
[[ -n "$CONFIG" && -n "$NETWORK" ]] || { usage; exit 2; }

PROJECT_ROOT="$(pwd -P)"
VALUES=()
while IFS= read -r line; do
  VALUES[${#VALUES[@]}]="$line"
done < <(python3 - "$CONFIG" "$NETWORK" <<'PY'
import sys, yaml
from pathlib import Path
c = yaml.safe_load(open(sys.argv[1]))
if sys.argv[2] not in c["networks"]:
    raise SystemExit("Unknown network")
project = Path.cwd().resolve()
output = Path(c.get("storage", {}).get("generated_output_root", c["output_root"]))
external = Path(c["method"]["external_checkout"])
if not output.is_absolute():
    output = project / output
if not external.is_absolute():
    external = project / external
print(output.resolve())
print(c["phase_directory"])
print(external.resolve())
print(c["rimbanet"]["number_of_searches"])
print(c["rimbanet"]["output_prefix"])
print(c["consensus"]["minimum_adjacency_support"])
print(c["cohort"]["pilot_network"])
print(str(c["cohort"]["require_pilot_before_scaleout"]).lower())
PY
)
INPUT_DIR="${VALUES[0]}/${VALUES[1]}/11e_inputs/$NETWORK"
RUN_DIR="${VALUES[0]}/${VALUES[1]}/11f_runs/$NETWORK"
CONSENSUS_DIR="${VALUES[0]}/${VALUES[1]}/11g_consensus/$NETWORK"
COUNTER="${VALUES[2]}/script/countDirectLinksMatrix.pl"
VALIDATION_STATUS="$RUN_DIR/status.tsv"
[[ -s "$VALIDATION_STATUS" ]] || { echo "Missing run-validation status" >&2; exit 3; }
grep -q $'\tvalidated_complete\t' "$VALIDATION_STATUS" || {
  echo "All searches must validate before consensus" >&2
  exit 3
}
if [[ "${VALUES[7]}" == "true" && "$NETWORK" != "${VALUES[6]}" ]]; then
  PILOT="${VALUES[0]}/${VALUES[1]}/11f_runs/pilot_gate.tsv"
  [[ -s "$PILOT" ]] && grep -q $'\tpassed\t' "$PILOT" || {
    echo "Microglia pilot gate has not passed" >&2
    exit 3
  }
fi
[[ -s "$COUNTER" ]] || { echo "Missing pinned legacy counter: $COUNTER" >&2; exit 3; }
for path in data.discretized.txt node.xml bn.param.txt prior.txt banned.txt; do
  [[ -s "$INPUT_DIR/$path" ]] || { echo "Missing input $path" >&2; exit 3; }
done
if [[ "$BINARY" == */* ]]; then
  [[ -x "$BINARY" ]] || { echo "Binary is not executable: $BINARY" >&2; exit 3; }
else
  command -v "$BINARY" >/dev/null || { echo "Binary not found: $BINARY" >&2; exit 3; }
fi

mkdir -p "$CONSENSUS_DIR"
rm -f "$CONSENSUS_DIR/.in_progress"
touch "$CONSENSUS_DIR/.in_progress"
trap 'rm -f "$CONSENSUS_DIR/.in_progress"' EXIT

PARAMS=()
while IFS= read -r line; do
  PARAMS[${#PARAMS[@]}]="$line"
done < "$INPUT_DIR/bn.param.txt"
N_SAMPLE="${PARAMS[0]}"
(
  cd "$CONSENSUS_DIR"
  perl "$COUNTER" \
    "$INPUT_DIR/data.discretized.txt" \
    "$RUN_DIR/${VALUES[4]}" \
    1 "${VALUES[3]}" \
    result.links.3 result.linksMatrix.3 "${VALUES[5]}"

  "$BINARY" -f 0 \
    -b "$INPUT_DIR/node.xml" \
    -d "$INPUT_DIR/data.discretized.txt" \
    -t 0 \
    -D "$N_SAMPLE" \
    -o result.links3 \
    -c result.links.3 > junk3.log

  grep -- '->' result.links3 |
    perl -ne 'if (/^\s*([^\s;]+)\s*->\s*([^\s;\[]+)/) { print "$1\t$2\n" }' \
    > result.links3.links.txt.tmp
  mv result.links3.links.txt.tmp result.links3.links.txt
)

[[ -s "$CONSENSUS_DIR/result.links3.links.txt" ]] || {
  echo "Legacy de-loop produced no final edges" >&2
  exit 4
}
echo "RIMBANet consensus complete: $NETWORK"
