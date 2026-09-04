#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --config FILE --network NAME --task-id N [--binary PATH]" >&2
}

CONFIG=""
NETWORK=""
TASK_ID=""
BINARY="${RIMBANET_BINARY:-testBN}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --network) NETWORK="$2"; shift 2 ;;
    --task-id) TASK_ID="$2"; shift 2 ;;
    --binary) BINARY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
[[ -n "$CONFIG" && -n "$NETWORK" && -n "$TASK_ID" ]] || { usage; exit 2; }
[[ "$TASK_ID" =~ ^[0-9]+$ ]] || { echo "task-id must be an integer" >&2; exit 2; }

PROJECT_ROOT="$(pwd -P)"
VALUES=()
while IFS= read -r line; do
  VALUES[${#VALUES[@]}]="$line"
done < <(python3 - "$CONFIG" "$NETWORK" "$TASK_ID" <<'PY'
import sys, yaml
from pathlib import Path
c = yaml.safe_load(open(sys.argv[1]))
network, task = sys.argv[2], int(sys.argv[3])
if c["schema_version"] != "seaad_rimbanet_config_v1":
    raise SystemExit("Unsupported config")
if network not in c["networks"]:
    raise SystemExit(f"Unknown network: {network}")
if not 1 <= task <= int(c["rimbanet"]["number_of_searches"]):
    raise SystemExit("Task ID outside configured search range")
project = Path.cwd().resolve()
output = Path(c.get("storage", {}).get("generated_output_root", c["output_root"]))
if not output.is_absolute():
    output = project / output
print(output.resolve())
print(c["phase_directory"])
print(c["rimbanet"]["base_seed"] + task)
print(c["rimbanet"]["trylist_maximum"])
print(c["rimbanet"]["mutual_information_cutoff"])
print(c["rimbanet"]["eqtl_threshold"])
print(c["rimbanet"]["prior_scaling"])
print(c["rimbanet"]["qratio_offset"])
print(c["rimbanet"]["alpha_base"])
print(c["rimbanet"]["alpha_sample_step"])
print(c["rimbanet"]["alpha_sample_divisor"])
print(c["rimbanet"]["output_prefix"])
PY
)

INPUT_DIR="${VALUES[0]}/${VALUES[1]}/11e_inputs/$NETWORK"
RUN_DIR="${VALUES[0]}/${VALUES[1]}/11f_runs/$NETWORK"
PARAM="$INPUT_DIR/bn.param.txt"
[[ -s "$PARAM" ]] || { echo "Missing parameter file: $PARAM" >&2; exit 3; }
PARAMS=()
while IFS= read -r line; do
  PARAMS[${#PARAMS[@]}]="$line"
done < "$PARAM"
[[ ${#PARAMS[@]} -eq 10 ]] || { echo "bn.param.txt must have 10 lines" >&2; exit 3; }

N_SAMPLE="${PARAMS[0]}"
N_NODE="${PARAMS[1]}"
NODE_FILE="${PARAMS[2]}"
DATA_FILE="${PARAMS[3]}"
BAN_FILE="${PARAMS[4]}"
PRIOR_FILE="${PARAMS[5]}"
for input in "$NODE_FILE" "$DATA_FILE" "$BAN_FILE" "$PRIOR_FILE"; do
  [[ -s "$INPUT_DIR/$input" ]] || { echo "Missing RIMBANet input: $input" >&2; exit 3; }
done
if [[ "$BINARY" == */* ]]; then
  [[ -x "$BINARY" ]] || { echo "RIMBANet binary not executable: $BINARY" >&2; exit 3; }
else
  command -v "$BINARY" >/dev/null || { echo "RIMBANet command not found: $BINARY" >&2; exit 3; }
fi

mkdir -p "$RUN_DIR"
CONFIG_SHA="$(shasum -a 256 "$CONFIG" | awk '{print $1}')"
INPUT_SHA="$(
  cat "$INPUT_DIR/$NODE_FILE" "$INPUT_DIR/$DATA_FILE" \
      "$INPUT_DIR/$BAN_FILE" "$INPUT_DIR/$PRIOR_FILE" |
  shasum -a 256 | awk '{print $1}'
)"
STATUS="$RUN_DIR/task.${TASK_ID}.status.tsv"
OUTPUT="$RUN_DIR/${VALUES[11]}.${TASK_ID}"
LOG="$RUN_DIR/junkK.${TASK_ID}"
if [[ -s "$STATUS" && -s "$OUTPUT" ]]; then
  OLD_STATE="$(awk -F $'\t' 'NR==2 {print $4}' "$STATUS")"
  OLD_CONFIG="$(awk -F $'\t' 'NR==2 {print $7}' "$STATUS")"
  OLD_INPUT="$(awk -F $'\t' 'NR==2 {print $8}' "$STATUS")"
  if [[ "$OLD_STATE" == "validated_complete" && "$OLD_CONFIG" == "$CONFIG_SHA" && "$OLD_INPUT" == "$INPUT_SHA" ]]; then
    echo "Task $TASK_ID already validated with matching inputs"
    exit 0
  fi
  echo "Refusing to overwrite task $TASK_ID with mismatched provenance" >&2
  exit 4
fi

SEED="${VALUES[2]}"
QRATIO="$(python3 -c "print(f'{1 / ($N_NODE + ${VALUES[7]}):.10f}')")"
ALPHA="$(python3 -c "print(${VALUES[8]} - ($N_SAMPLE // ${VALUES[10]}) * ${VALUES[9]})")"
TMP_DIR="$RUN_DIR/.task.${TASK_ID}.tmp.$$"
mkdir -p "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT
STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
START_EPOCH="$(date +%s)"
GNU_TIME=0
if [[ -x /usr/bin/time ]] &&
  /usr/bin/time -v -o "$TMP_DIR/time.probe" true >/dev/null 2>&1; then
  GNU_TIME=1
fi
rm -f "$TMP_DIR/time.probe"
COMMAND=(
  "$BINARY" -f 0 -M "${VALUES[3]}"
  -s "$SEED"
  -b "$NODE_FILE"
  -d "$DATA_FILE"
  -t "${VALUES[4]}"
  -T "${VALUES[5]}"
  -D "$N_SAMPLE"
  -r "${VALUES[6]}"
  -P "$PRIOR_FILE"
  -a "$ALPHA"
  -q "$QRATIO"
  -g "$BAN_FILE"
  -o "$TMP_DIR/result"
)

set +e
(
  cd "$INPUT_DIR"
  if [[ "$GNU_TIME" -eq 1 ]]; then
    /usr/bin/time -v -o "$TMP_DIR/resource.txt" "${COMMAND[@]}"
  else
    "${COMMAND[@]}"
  fi
) >"$TMP_DIR/log" 2>&1
EXIT_CODE=$?
set -e
FINISHED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
FINISH_EPOCH="$(date +%s)"
ELAPSED_SECONDS="$((FINISH_EPOCH - START_EPOCH))"

STATE="failed"
if [[ "$EXIT_CODE" -eq 0 && -s "$TMP_DIR/result" ]] && grep -q "LIKELIHOOD" "$TMP_DIR/log"; then
  STATE="validated_complete"
  mv "$TMP_DIR/result" "$OUTPUT"
  mv "$TMP_DIR/log" "$LOG"
  if [[ -s "$TMP_DIR/resource.txt" ]]; then
    mv "$TMP_DIR/resource.txt" "$RUN_DIR/resource.${TASK_ID}.txt"
  fi
fi
OUTPUT_SHA=""
EDGE_COUNT=0
MAX_RSS_KB=""
if [[ -s "$OUTPUT" ]]; then
  OUTPUT_SHA="$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
  EDGE_COUNT="$(grep -c -- '->' "$OUTPUT" || true)"
fi
if [[ -s "$RUN_DIR/resource.${TASK_ID}.txt" ]]; then
  MAX_RSS_KB="$(
    awk -F: '/Maximum resident set size/ {gsub(/^[[:space:]]+/, "", $2); print $2}' \
      "$RUN_DIR/resource.${TASK_ID}.txt"
  )"
fi
TMP_STATUS="$TMP_DIR/status.tsv"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  schema_version network task_id state seed exit_code config_sha256 input_sha256 \
  output_sha256 edge_count elapsed_seconds max_rss_kb started_utc finished_utc host \
  >"$TMP_STATUS"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  seaad_rimbanet_task_status_v1 "$NETWORK" "$TASK_ID" "$STATE" "$SEED" \
  "$EXIT_CODE" "$CONFIG_SHA" "$INPUT_SHA" "$OUTPUT_SHA" "$EDGE_COUNT" \
  "$ELAPSED_SECONDS" "$MAX_RSS_KB" "$STARTED" "$FINISHED" "$(hostname)" \
  >>"$TMP_STATUS"
mv "$TMP_STATUS" "$STATUS"

if [[ "$STATE" != "validated_complete" ]]; then
  cp "$TMP_DIR/log" "$RUN_DIR/junkK.${TASK_ID}.failed"
  if [[ -s "$TMP_DIR/resource.txt" ]]; then
    cp "$TMP_DIR/resource.txt" "$RUN_DIR/resource.${TASK_ID}.failed.txt"
  fi
  echo "RIMBANet task $TASK_ID failed" >&2
  exit 5
fi
echo "RIMBANet task $TASK_ID validated: edges=$EDGE_COUNT"
