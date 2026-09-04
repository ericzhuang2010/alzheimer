#!/usr/bin/env bash
set -euo pipefail

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
print(resolve(c["inputs"]["wgs_raw_plink_prefix"]))
print(resolve(c["inputs"]["wgs_plink_prefix"]))
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
PY
)

RAW_PREFIX="${CFG[0]}"
QC_PREFIX="${CFG[1]}"
KEEP="${CFG[13]}/11_seaad_rimbanet/11a_audit/wgs_keep.tsv"
SEX_UPDATE="${CFG[13]}/11_seaad_rimbanet/11a_audit/wgs_sex.tsv"
mkdir -p "$(dirname "$QC_PREFIX")"
[[ -s "$KEEP" ]] || {
  echo "Missing explicit WGS keep file from VH11A: $KEEP" >&2
  exit 3
}
[[ -s "$SEX_UPDATE" ]] || {
  echo "Missing explicit WGS sex update from VH11A: $SEX_UPDATE" >&2
  exit 3
}
command -v plink2 >/dev/null || { echo "plink2 is required" >&2; exit 3; }

if [[ -s "${RAW_PREFIX}.pgen" && ( -s "${RAW_PREFIX}.pvar" || -s "${RAW_PREFIX}.pvar.zst" ) && -s "${RAW_PREFIX}.psam" ]]; then
  INPUT=(--pfile "$RAW_PREFIX")
elif [[ -s "${RAW_PREFIX}.bed" && -s "${RAW_PREFIX}.bim" && -s "${RAW_PREFIX}.fam" ]]; then
  INPUT=(--bfile "$RAW_PREFIX")
else
  echo "No PLINK1/PLINK2 source set found at $RAW_PREFIX" >&2
  exit 3
fi

plink2 "${INPUT[@]}" \
  --keep "$KEEP" \
  --update-sex "$SEX_UPDATE" \
  --mind "${CFG[2]}" \
  --geno "${CFG[3]}" \
  --maf "${CFG[4]}" \
  --mac "${CFG[5]}" \
  --hwe "${CFG[6]}" midp \
  --make-pgen \
  --out "$QC_PREFIX"

plink2 --pfile "$QC_PREFIX" \
  --indep-pairwise 200 50 0.2 \
  --out "${QC_PREFIX}.ld"
plink2 --pfile "$QC_PREFIX" \
  --check-sex \
  --out "${QC_PREFIX}.sexcheck"
plink2 --pfile "$QC_PREFIX" \
  --make-king-table \
  --out "${QC_PREFIX}.kinship"
plink2 --pfile "$QC_PREFIX" \
  --het \
  --out "${QC_PREFIX}.heterozygosity"
plink2 --pfile "$QC_PREFIX" \
  --extract "${QC_PREFIX}.ld.prune.in" \
  --pca "${CFG[9]}" approx \
  --out "${QC_PREFIX}.ancestry"
plink2 --pfile "$QC_PREFIX" \
  --export A-transpose \
  --out "${QC_PREFIX}.dosage"

python3 - "$CONFIG" "${QC_PREFIX}.sexcheck" "${QC_PREFIX}.kinship.kin0" <<'PY'
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
if not sex_path.exists():
    raise SystemExit(f"Missing PLINK sex-check output: {sex_path}")
sex = pd.read_csv(sex_path, sep=r"\s+")
status_column = "STATUS" if "STATUS" in sex.columns else None
if status_column is None:
    raise SystemExit("Cannot identify sex-check status column")
sex_failures = int(
    (~sex[status_column].astype(str).isin(["OK", "PASS"])).sum()
)
if config["genetics"]["require_sexcheck_pass"] and sex_failures:
    raise SystemExit(f"Sex check failed for {sex_failures} samples")

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
pd.DataFrame([{
    "sexcheck_samples": len(sex),
    "sexcheck_failures": sex_failures,
    "related_pairs_above_threshold": related_pairs,
}]).to_csv(resolve(config["genetics"]["ancestry_covariates"]).parent /
           "sample_genetic_qc_summary.tsv", sep="\t", index=False)
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
).dropna(subset=["wgs_sample_id"])
id_to_donor = dict(zip(crosswalk["wgs_sample_id"], crosswalk["donor_id"]))
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
geno_path = resolve(config["genetics"]["genotype_matrix"])
pos_path = resolve(config["genetics"]["variant_positions"])
pcs_path = resolve(config["genetics"]["ancestry_covariates"])
for path in (geno_path, pos_path, pcs_path):
    path.parent.mkdir(parents=True, exist_ok=True)
geno.to_csv(geno_path, sep="\t", index=False, compression="gzip")
positions.to_csv(pos_path, sep="\t", index=False, compression="gzip")
pd.DataFrame([{
    "imputation": config["genetics"]["missing_genotype_imputation"],
    "missing_dosages_before": missing_before,
    "missing_dosages_after": 0,
    "variants": len(geno),
    "samples": len(dosage_columns),
}]).to_csv(geno_path.parent / "genotype_imputation_summary.tsv", sep="\t", index=False)

pcs = pd.read_csv(sys.argv[3], sep=r"\s+")
if "#FID" in pcs.columns:
    pcs = pcs.rename(columns={"#FID": "FID", "IID": "wgs_sample_id"})
elif "IID" in pcs.columns:
    pcs = pcs.rename(columns={"IID": "wgs_sample_id"})
else:
    pcs = pcs.rename(columns={pcs.columns[0]: "wgs_sample_id"})
pcs["donor_id"] = pcs["wgs_sample_id"].map(id_to_donor)
if pcs["donor_id"].isna().any():
    raise SystemExit("Cannot map all ancestry-PC samples to SEA-AD donors")
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
files = [
    prefix.with_suffix(".pgen"), prefix.with_suffix(".pvar"),
    prefix.with_suffix(".psam"),
    resolve(c["genetics"]["genotype_matrix"]),
    resolve(c["genetics"]["variant_positions"]),
    resolve(c["genetics"]["ancestry_covariates"]),
    resolve(c["genetics"]["genotype_matrix"]).parent / "genotype_imputation_summary.tsv",
    resolve(c["genetics"]["ancestry_covariates"]).parent / "sample_genetic_qc_summary.tsv",
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
    "stage": "VH11C_GENOTYPE", "state": "validated_complete"
}]).to_csv(out / "genotype_status.tsv", sep="\t", index=False)
PY

echo "VH11C genotype preparation validated"
