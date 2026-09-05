#!/usr/bin/env bash
set -euo pipefail
umask 077

usage() {
  echo "Usage: $0 --config FILE" >&2
}

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
[[ -n "$CONFIG" ]] || { usage; exit 2; }

PROJECT_ROOT="$(pwd -P)"
CFG=()
while IFS= read -r line; do
  CFG[${#CFG[@]}]="$line"
done < <(python3 - "$CONFIG" <<'PY'
import sys, yaml
from pathlib import Path
c = yaml.safe_load(open(sys.argv[1]))
project = Path.cwd().resolve()
def resolve(value):
    path = Path(value)
    return (path if path.is_absolute() else project / path).resolve()
print(resolve(c["inputs"]["genotype_raw_plink_prefix"]))
print(resolve(c["inputs"]["genotype_plink_prefix"]))
print(c["genetics"]["sample_missingness_maximum"])
print(c["genetics"]["variant_missingness_maximum"])
print(c["genetics"]["maf_minimum"])
print(c["genetics"]["mac_minimum"])
print(c["genetics"]["hwe_p_minimum"])
print(c["genetics"]["relatedness_kinship_maximum"])
print(str(c["genetics"]["require_sexcheck_pass"]).lower())
print(c["genetics"]["ancestry_pcs"])
print(resolve(c["genetics"]["genotype_matrix"]))
print(resolve(c["genetics"]["variant_positions"]))
print(resolve(c["genetics"]["ancestry_covariates"]))
print(resolve(c.get("storage", {}).get("generated_output_root", c["output_root"])))
print(resolve(c["genetics"]["plink2_binary"]))
print(c["genetics"]["plink2_binary_sha256"])
print(c["genetics"]["plink2_version"])
print(c["genetics"]["minimum_matched_donors"])
print(c["genetics"]["sexcheck_max_female_xf"])
print(c["genetics"]["sexcheck_min_male_xf"])
print(c["genetics"]["plink2_threads"])
print(c["genetics"]["plink2_memory_mb"])
PY
)

RAW_PREFIX="${CFG[0]}"
QC_PREFIX="${CFG[1]}"
KEEP="${CFG[13]}/11_seaad_rimbanet/11a_audit/array_keep.tsv"
SEX_UPDATE="${CFG[13]}/11_seaad_rimbanet/11a_audit/array_sex.tsv"
AUDIT_STATUS="${CFG[13]}/11_seaad_rimbanet/11a_audit/status.tsv"
PLINK2="${CFG[14]}"
mkdir -p "$(dirname "$QC_PREFIX")"
[[ -s "$KEEP" ]] || {
  echo "Missing explicit genotype keep file from VH11A: $KEEP" >&2
  exit 3
}
[[ -s "$SEX_UPDATE" ]] || {
  echo "Missing explicit genotype sex update from VH11A: $SEX_UPDATE" >&2
  exit 3
}
if ! awk -F '\t' \
  'NR > 1 && $2 == "VH11A" && $3 == "validated_complete" { found = 1 }
   END { exit !found }' \
  "$AUDIT_STATUS"
then
  echo "VH11A is not validated_complete: $AUDIT_STATUS" >&2
  exit 3
fi
CURRENT_CONFIG_SHA256="$(sha256sum "$CONFIG" | awk '{print $1}')"
AUDIT_CONFIG_SHA256="$(
  awk -F '\t' '
    NR == 1 {
      for (i = 1; i <= NF; i++) {
        if ($i == "config_sha256") column = i
      }
      next
    }
    NR == 2 && column { print $column }
  ' "$AUDIT_STATUS"
)"
[[ "$AUDIT_CONFIG_SHA256" == "$CURRENT_CONFIG_SHA256" ]] || {
  echo "VH11A config SHA-256 does not match the active config" >&2
  echo "audit=$AUDIT_CONFIG_SHA256 active=$CURRENT_CONFIG_SHA256" >&2
  exit 3
}
[[ -x "$PLINK2" ]] || {
  echo "Pinned PLINK2 executable is unavailable: $PLINK2" >&2
  exit 3
}
PLINK2_SHA256="$(sha256sum "$PLINK2" | awk '{print $1}')"
[[ "$PLINK2_SHA256" == "${CFG[15]}" ]] || {
  echo "Pinned PLINK2 SHA-256 mismatch: $PLINK2" >&2
  echo "observed=$PLINK2_SHA256 expected=${CFG[15]}" >&2
  exit 3
}
PLINK2_VERSION="$("$PLINK2" --version)"
[[ "$PLINK2_VERSION" == "${CFG[16]}" ]] || {
  echo "Pinned PLINK2 version mismatch: $PLINK2_VERSION" >&2
  exit 3
}
PLINK2_THREADS="${CFG[20]}"
PLINK2_MEMORY_MB="${CFG[21]}"
if [[ -n "${LSB_DJOB_NUMPROC:-}" ]] && \
   (( LSB_DJOB_NUMPROC < PLINK2_THREADS ))
then
  echo "LSF allocated $LSB_DJOB_NUMPROC slots; PLINK2 requires $PLINK2_THREADS" >&2
  exit 3
fi
PLINK2_RUN=(
  "$PLINK2"
  --threads "$PLINK2_THREADS"
  --memory "$PLINK2_MEMORY_MB"
)

python3 scripts/validation_human/11_import_seaad_array.py --config "$CONFIG"

"${PLINK2_RUN[@]}" \
  --vcf "${RAW_PREFIX}.vcf.gz" \
  --vcf-require-gt \
  --const-fid 0 \
  --keep "$KEEP" \
  --update-sex "$SEX_UPDATE" \
  --split-par hg38 \
  --sort-vars \
  --make-pgen \
  --out "$RAW_PREFIX"

"${PLINK2_RUN[@]}" --pfile "$RAW_PREFIX" \
  --mind "${CFG[2]}" \
  --geno "${CFG[3]}" \
  --maf "${CFG[4]}" \
  --mac "${CFG[5]}" \
  --hwe "${CFG[6]}" midp \
  --make-pgen \
  --out "$QC_PREFIX"

"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --indep-pairwise 200 50 0.2 \
  --out "${QC_PREFIX}.ld"
"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --extract "${QC_PREFIX}.ld.prune.in" \
  --check-sex \
    "max-female-xf=${CFG[18]}" \
    "min-male-xf=${CFG[19]}" \
  --out "${QC_PREFIX}.sexcheck"
"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --extract "${QC_PREFIX}.ld.prune.in" \
  --make-king-table \
  --out "${QC_PREFIX}.kinship"
"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --het \
  --out "${QC_PREFIX}.heterozygosity"
"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --extract "${QC_PREFIX}.ld.prune.in" \
  --pca "${CFG[9]}" \
  --out "${QC_PREFIX}.ancestry"
"${PLINK2_RUN[@]}" --pfile "$QC_PREFIX" \
  --export A-transpose \
  --out "${QC_PREFIX}.dosage"

python3 - \
  "$CONFIG" \
  "${QC_PREFIX}.sexcheck" \
  "${QC_PREFIX}.kinship.kin0" \
  "${RAW_PREFIX}.psam" \
  "${QC_PREFIX}.psam" <<'PY'
import sys
from pathlib import Path
import pandas as pd
import yaml

config = yaml.safe_load(open(sys.argv[1]))
project = Path.cwd().resolve()
def resolve(value):
    path = Path(value)
    return (path if path.is_absolute() else project / path).resolve()
sex_path = Path(sys.argv[2])
king_path = Path(sys.argv[3])
raw_psam_path = Path(sys.argv[4])
qc_psam_path = Path(sys.argv[5])
if not sex_path.exists():
    raise SystemExit(f"Missing PLINK sex-check output: {sex_path}")
if not king_path.exists():
    raise SystemExit(f"Missing PLINK KING output: {king_path}")
sex = pd.read_csv(sex_path, sep=r"\s+")
status_column = "STATUS" if "STATUS" in sex.columns else None
if status_column is None:
    raise SystemExit("Cannot identify sex-check status column")
sex_failures = int(
    (~sex[status_column].astype(str).isin(["OK", "PASS"])).sum()
)
if config["genetics"]["require_sexcheck_pass"] and sex_failures:
    raise SystemExit(f"Sex check failed for {sex_failures} samples")

def read_iids(path):
    frame = pd.read_csv(path, sep=r"\s+", dtype=str)
    iid_column = "#IID" if "#IID" in frame.columns else "IID"
    if iid_column not in frame.columns:
        raise SystemExit(f"Cannot identify IID column in {path}")
    values = frame[iid_column].dropna().astype(str)
    if values.duplicated().any():
        raise SystemExit(f"Duplicate sample IDs in {path}")
    return set(values)

raw_samples = read_iids(raw_psam_path)
qc_samples = read_iids(qc_psam_path)
expected_primary = int(config["expected_identity"]["genotype_primary_samples"])
minimum_matched = int(config["genetics"]["minimum_matched_donors"])
if len(raw_samples) != expected_primary:
    raise SystemExit(
        f"Raw matched genotype cohort has {len(raw_samples)} samples; "
        f"expected {expected_primary}"
    )
if not qc_samples.issubset(raw_samples):
    raise SystemExit("Post-QC genotype samples are not a subset of the matched cohort")
if len(qc_samples) < minimum_matched:
    raise SystemExit(
        f"Only {len(qc_samples)} genotype samples survived QC; "
        f"minimum is {minimum_matched}"
    )
if len(sex) != len(qc_samples):
    raise SystemExit("Sex-check report does not contain every post-QC sample")

related_pairs = 0
if king_path.exists() and king_path.stat().st_size:
    king = pd.read_csv(king_path, sep=r"\s+")
    kinship_column = next(
        (column for column in ["KINSHIP", "Kinship"] if column in king.columns), None
    )
    if kinship_column is None:
        raise SystemExit("Cannot identify KING kinship column")
    related_pairs = int(
        (pd.to_numeric(king[kinship_column]) >
         float(config["genetics"]["relatedness_kinship_maximum"])).sum()
    )
if related_pairs:
    raise SystemExit(f"{related_pairs} donor pairs exceed the kinship threshold")
summary_root = resolve(config["genetics"]["ancestry_covariates"]).parent
pd.DataFrame([{
    "matched_samples_before_qc": len(raw_samples),
    "samples_removed_by_missingness": len(raw_samples - qc_samples),
    "samples_retained_after_qc": len(qc_samples),
    "sexcheck_samples": len(sex),
    "sexcheck_failures": sex_failures,
    "related_pairs_above_threshold": related_pairs,
}]).to_csv(
    summary_root / "sample_genetic_qc_summary.tsv", sep="\t", index=False
)
excluded_samples = sorted(raw_samples - qc_samples)
pd.DataFrame(
    [
        {
            "genotype_sample_id": sample_id,
            "exclusion_reason": "sample_missingness_above_threshold",
        }
        for sample_id in excluded_samples
    ],
    columns=["genotype_sample_id", "exclusion_reason"],
).to_csv(
    summary_root / "sample_genetic_qc_exclusions.tsv", sep="\t", index=False
)
PY

python3 - "$CONFIG" "${QC_PREFIX}.dosage.traw" "${QC_PREFIX}.ancestry.eigenvec" <<'PY'
import sys
from pathlib import Path
import pandas as pd
import yaml

config = yaml.safe_load(open(sys.argv[1]))
project = Path.cwd().resolve()
def resolve(value):
    path = Path(value)
    return (path if path.is_absolute() else project / path).resolve()
generated_root = resolve(
    config.get("storage", {}).get("generated_output_root", config["output_root"])
)
crosswalk = pd.read_csv(
    generated_root / "11_seaad_rimbanet/11a_audit/donor_crosswalk.tsv",
    sep="\t", dtype=str,
).dropna(subset=["genotype_sample_id"])
id_to_donor = dict(
    zip(crosswalk["genotype_sample_id"], crosswalk["donor_id"])
)
traw = pd.read_csv(sys.argv[2], sep=r"\s+")
meta = ["CHR", "SNP", "(C)M", "POS", "COUNTED", "ALT"]
sample_cols = [c for c in traw.columns if c not in meta]
if not sample_cols:
    raise SystemExit("PLINK dosage export has no sample columns")
geno = traw[["SNP", *sample_cols]].rename(columns={"SNP": "variant_id"})
rename = {}
for column in sample_cols:
    candidates = [column, column.split("_", 1)[-1]]
    matches = [id_to_donor[value] for value in candidates if value in id_to_donor]
    if len(set(matches)) != 1:
        raise SystemExit(f"Cannot uniquely map PLINK dosage column {column!r}")
    rename[column] = matches[0]
geno = geno.rename(columns=rename)
minimum_matched = int(config["genetics"]["minimum_matched_donors"])
primary_samples = int(config["expected_identity"]["genotype_primary_samples"])
if not minimum_matched <= len(rename) <= primary_samples:
    raise SystemExit(
        f"PLINK dosage export has {len(rename)} mapped donors; expected "
        f"between {minimum_matched} and {primary_samples}"
    )
if len(set(rename.values())) != len(rename):
    raise SystemExit("PLINK dosage columns do not map one-to-one to donors")
if geno["variant_id"].duplicated().any():
    raise SystemExit("PLINK dosage export contains duplicate variant IDs")
dosage_columns = [column for column in geno.columns if column != "variant_id"]
geno[dosage_columns] = geno[dosage_columns].apply(pd.to_numeric, errors="coerce")
missing_before = int(geno[dosage_columns].isna().sum().sum())
row_means = geno[dosage_columns].mean(axis=1)
if row_means.isna().any():
    raise SystemExit("At least one variant has no observed dosage")
geno[dosage_columns] = geno[dosage_columns].T.fillna(row_means).T
if geno[dosage_columns].isna().any().any():
    raise SystemExit("Mean-dosage imputation left missing values")
positions = traw[["SNP", "CHR", "POS", "COUNTED", "ALT"]].rename(
    columns={"SNP": "variant_id", "CHR": "chromosome", "POS": "position",
             "COUNTED": "effect_allele", "ALT": "other_allele"}
)
positions["chromosome"] = positions["chromosome"].replace(
    {"PAR1": "X", "PAR2": "X"}
)
geno_path = resolve(config["genetics"]["genotype_matrix"])
pos_path = resolve(config["genetics"]["variant_positions"])
pcs_path = resolve(config["genetics"]["ancestry_covariates"])
for path in (geno_path, pos_path, pcs_path):
    path.parent.mkdir(parents=True, exist_ok=True)
gzip_options = {"method": "gzip", "compresslevel": 6, "mtime": 0}
geno.to_csv(geno_path, sep="\t", index=False, compression=gzip_options)
positions.to_csv(
    pos_path, sep="\t", index=False, compression=gzip_options
)
pd.DataFrame([{
    "imputation": config["genetics"]["missing_genotype_imputation"],
    "missing_dosages_before": missing_before,
    "missing_dosages_after": 0,
    "variants": len(geno),
    "samples": len(dosage_columns),
}]).to_csv(geno_path.parent / "genotype_imputation_summary.tsv", sep="\t", index=False)

pcs = pd.read_csv(sys.argv[3], sep=r"\s+")
if "#FID" in pcs.columns:
    pcs = pcs.rename(
        columns={"#FID": "genotype_fid", "IID": "genotype_sample_id"}
    )
elif "IID" in pcs.columns:
    pcs = pcs.rename(columns={"IID": "genotype_sample_id"})
else:
    pcs = pcs.rename(columns={pcs.columns[0]: "genotype_sample_id"})
pcs["donor_id"] = pcs["genotype_sample_id"].map(id_to_donor)
if pcs["donor_id"].isna().any():
    raise SystemExit("Cannot map all ancestry-PC samples to SEA-AD donors")
if pcs["donor_id"].duplicated().any():
    raise SystemExit("Ancestry-PC samples do not map one-to-one to donors")
pcs.to_csv(pcs_path, sep="\t", index=False)
PY

STATUS_DIR="${CFG[13]}/11_seaad_rimbanet/11c_genetics"
mkdir -p "$STATUS_DIR"
python3 - "$CONFIG" "$QC_PREFIX" "$STATUS_DIR" <<'PY'
import hashlib, pathlib, sys, yaml
import pandas as pd
c = yaml.safe_load(open(sys.argv[1]))
prefix = pathlib.Path(sys.argv[2])
out = pathlib.Path(sys.argv[3])
project = pathlib.Path.cwd().resolve()
def resolve(value):
    path = pathlib.Path(value)
    return (path if path.is_absolute() else project / path).resolve()
raw_prefix = resolve(c["inputs"]["genotype_raw_plink_prefix"])
files = [
    pathlib.Path(f"{raw_prefix}.import_status.tsv"),
    pathlib.Path(f"{raw_prefix}.import_summary.tsv"),
    pathlib.Path(f"{raw_prefix}.variant_mapping.tsv.gz"),
    pathlib.Path(f"{raw_prefix}.vcf.gz"),
    prefix.with_suffix(".pgen"), prefix.with_suffix(".pvar"),
    prefix.with_suffix(".psam"),
    resolve(c["genetics"]["genotype_matrix"]),
    resolve(c["genetics"]["variant_positions"]),
    resolve(c["genetics"]["ancestry_covariates"]),
    resolve(c["genetics"]["genotype_matrix"]).parent / "genotype_imputation_summary.tsv",
    resolve(c["genetics"]["ancestry_covariates"]).parent / "sample_genetic_qc_summary.tsv",
    resolve(c["genetics"]["ancestry_covariates"]).parent / "sample_genetic_qc_exclusions.tsv",
]
rows = []
def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()
for path in files:
    if not path.exists() and path.suffix == ".pvar":
        path = pathlib.Path(f"{path}.zst")
    if not path.exists():
        raise SystemExit(f"Missing expected genotype artifact: {path}")
    h = sha256(path)
    rows.append({"path": str(path), "bytes": path.stat().st_size, "sha256": h})
pd.DataFrame(rows).to_csv(out / "genotype_artifacts.tsv", sep="\t", index=False)
pd.DataFrame([{
    "schema_version": "seaad_rimbanet_genotype_status_v1",
    "stage": "VH11C_GENOTYPE",
    "state": "validated_complete",
    "plink2_version": c["genetics"]["plink2_version"],
    "plink2_sha256": c["genetics"]["plink2_binary_sha256"],
}]).to_csv(out / "genotype_status.tsv", sep="\t", index=False)
PY

echo "VH11C genotype preparation validated"
