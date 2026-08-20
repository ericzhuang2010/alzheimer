#!/usr/bin/env python3
"""VH02: rebuild and freeze the authoritative 78-donor SEA-AD cohort."""

from __future__ import annotations

import h5py
import numpy as np
import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    bool_value,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_dir,
    read_categorical_codes,
    read_obs_values,
    repo_path,
    require_phase,
    status_frame,
    utc_now,
    write_artifacts,
)


def main() -> int:
    args = parse_config_cli("VH02: build authoritative SEA-AD donor cohort")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_phase(output_root, "01_audit")
    output_dir = phase_dir(output_root, "02_cohort")
    expected = config["expected_identity"]
    cohort_cfg = config["cohort"]
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])

    fields = [
        cohort_cfg["neurotypical_reference_field"],
        cohort_cfg["diagnosis_field"],
        cohort_cfg["sex_field"],
        cohort_cfg["apoe_field"],
        cohort_cfg["age_field"],
        cohort_cfg["pmi_field"],
        cohort_cfg["study_field"],
        cohort_cfg["pathology_field"],
    ]
    with h5py.File(h5ad_path, "r") as h5:
        donor_encoded = read_categorical_codes(h5, cohort_cfg["donor_field"])
        if donor_encoded is None:
            raise ValueError("Donor ID must be categorical")
        donor_codes, donor_categories = donor_encoded
        unique_codes, first_indices = np.unique(donor_codes, return_index=True)
        if np.any(unique_codes < 0):
            raise ValueError("Missing donor ID in H5AD observations")
        first_by_code = dict(zip(unique_codes.astype(int), first_indices.astype(int)))
        donor_rows = []
        invariance_rows = []
        field_values = {}
        for field in fields:
            values = read_obs_values(h5, field)
            field_values[field] = values
            first_values = np.asarray([values[first_by_code[index]] for index in range(len(donor_categories))], dtype=object)
            expected_values = first_values[donor_codes.astype(int)]
            if values.dtype.kind in "fiu":
                left = np.asarray(values, dtype=float)
                right = np.asarray(expected_values, dtype=float)
                matches = (left == right) | (np.isnan(left) & np.isnan(right))
            else:
                matches = np.asarray([
                    (a is None and b is None) or str(a) == str(b)
                    for a, b in zip(values, expected_values)
                ])
            invariance_rows.append({
                "field": field,
                "observations": len(values),
                "mismatch_count_within_donor": int(np.sum(~matches)),
                "invariant_within_donor": bool(np.all(matches)),
            })
        for code, donor in enumerate(donor_categories):
            index = first_by_code[code]
            donor_rows.append({
                "donor_id": str(donor),
                "neurotypical_reference": bool_value(field_values[cohort_cfg["neurotypical_reference_field"]][index]),
                "diagnosis": str(field_values[cohort_cfg["diagnosis_field"]][index]),
                "sex": str(field_values[cohort_cfg["sex_field"]][index]),
                "apoe_genotype": str(field_values[cohort_cfg["apoe_field"]][index]),
                "age_death": pd.to_numeric(field_values[cohort_cfg["age_field"]][index], errors="coerce"),
                "pmi": pd.to_numeric(field_values[cohort_cfg["pmi_field"]][index], errors="coerce"),
                "study": str(field_values[cohort_cfg["study_field"]][index]),
                "pathology": str(field_values[cohort_cfg["pathology_field"]][index]),
                "source_nuclei": int(np.sum(donor_codes == code)),
            })

    donors = pd.DataFrame(donor_rows).sort_values("donor_id").reset_index(drop=True)
    apoe_lookup = {
        genotype: group
        for group, genotypes in cohort_cfg["apoe_groups"].items()
        for genotype in genotypes
    }
    donors["apoe_group"] = donors["apoe_genotype"].map(apoe_lookup)
    reasons = []
    for row in donors.itertuples(index=False):
        if row.neurotypical_reference:
            reason = "neurotypical_reference"
        elif row.diagnosis not in cohort_cfg["included_diagnoses"]:
            reason = "phenotype_not_in_analysis"
        elif row.apoe_genotype in cohort_cfg["excluded_apoe"]:
            reason = "excluded_apoe_2_4"
        elif row.apoe_group is None or pd.isna(row.apoe_group):
            reason = "unmapped_apoe"
        elif row.sex not in {"Female", "Male"}:
            reason = "invalid_sex"
        elif not np.isfinite(row.age_death) or not np.isfinite(row.pmi) or not row.study:
            reason = "incomplete_or_nonfinite_covariate"
        else:
            reason = ""
        reasons.append(reason)
    donors["exclusion_reason"] = reasons
    donors["included_primary"] = donors["exclusion_reason"].eq("")
    primary = donors.loc[donors["included_primary"]].copy()
    primary["signature_group"] = primary["sex"].map({"Female": "F", "Male": "M"}) + "_" + primary["apoe_group"]
    age_center = float(primary["age_death"].mean())
    age_scale = float(primary["age_death"].std(ddof=1))
    pmi_center = float(primary["pmi"].mean())
    pmi_scale = float(primary["pmi"].std(ddof=1))
    primary["age_death_scaled"] = (primary["age_death"] - age_center) / age_scale
    primary["pmi_scaled"] = (primary["pmi"] - pmi_center) / pmi_scale
    primary = primary.sort_values("donor_id").reset_index(drop=True)

    group_counts = (
        primary.groupby(["diagnosis", "sex", "apoe_group", "signature_group"], observed=True)
        .size().rename("donors").reset_index()
    )
    expected_groups = {
        ("Dementia", "Female", "e2"): 1,
        ("Dementia", "Female", "e33"): 13,
        ("Dementia", "Female", "e4"): 9,
        ("Dementia", "Male", "e2"): 1,
        ("Dementia", "Male", "e33"): 9,
        ("Dementia", "Male", "e4"): 4,
        ("No dementia", "Female", "e2"): 6,
        ("No dementia", "Female", "e33"): 13,
        ("No dementia", "Female", "e4"): 5,
        ("No dementia", "Male", "e2"): 4,
        ("No dementia", "Male", "e33"): 10,
        ("No dementia", "Male", "e4"): 3,
    }
    observed_groups = {
        (row.diagnosis, row.sex, row.apoe_group): int(row.donors)
        for row in group_counts.itertuples(index=False)
    }
    invariance = pd.DataFrame(invariance_rows)
    checks = [
        ("source_donors", len(donors) == expected["source_donors"], len(donors), expected["source_donors"], ""),
        ("analysis_donors", len(primary) == expected["analysis_donors"], len(primary), expected["analysis_donors"], ""),
        ("dementia_donors", int(primary["diagnosis"].eq("Dementia").sum()) == expected["dementia_donors"], int(primary["diagnosis"].eq("Dementia").sum()), expected["dementia_donors"], ""),
        ("no_dementia_donors", int(primary["diagnosis"].eq("No dementia").sum()) == expected["no_dementia_donors"], int(primary["diagnosis"].eq("No dementia").sum()), expected["no_dementia_donors"], ""),
        ("clinical_fields_invariant", bool(invariance["invariant_within_donor"].all()), int((~invariance["invariant_within_donor"]).sum()), 0, ""),
        ("twelve_arm_counts", observed_groups == expected_groups, str(observed_groups), str(expected_groups), ""),
        ("model_covariates_complete", not primary[["diagnosis", "sex", "apoe_group", "age_death", "pmi", "study"]].isna().any().any(), int(primary[["diagnosis", "sex", "apoe_group", "age_death", "pmi", "study"]].isna().sum().sum()), 0, ""),
        ("signature_groups_valid", set(primary["signature_group"]) == {row["group_id"] for row in cohort_cfg["signature_groups"]}, "|".join(sorted(primary["signature_group"].unique())), "F_e2|F_e33|F_e4|M_e2|M_e33|M_e4", ""),
    ]
    checks_table = checks_frame(checks)
    exclusion_flow = pd.concat([
        pd.DataFrame([{"stage": "source", "reason": "all_source_donors", "donors": len(donors)}]),
        donors.loc[~donors["included_primary"]].groupby("exclusion_reason").size().rename("donors").reset_index().rename(columns={"exclusion_reason": "reason"}).assign(stage="excluded"),
        pd.DataFrame([{"stage": "included", "reason": "analysis_cohort", "donors": len(primary)}]),
    ], ignore_index=True)
    scaling = pd.DataFrame([
        {"covariate": "age_death", "center": age_center, "scale": age_scale, "n_donors": len(primary)},
        {"covariate": "pmi", "center": pmi_center, "scale": pmi_scale, "n_donors": len(primary)},
    ])
    pathology = (
        primary.groupby(["diagnosis", "pathology"], observed=True)
        .size().rename("donors").reset_index()
    )

    paths = {
        "all": output_dir / "donor_metadata_all.tsv",
        "primary": output_dir / "donor_cohort_primary.tsv",
        "flow": output_dir / "cohort_exclusion_flow.tsv",
        "groups": output_dir / "donor_group_counts.tsv",
        "scaling": output_dir / "covariate_scaling.tsv",
        "pathology": output_dir / "cognitive_pathology_crosstab.tsv",
        "invariance": output_dir / "donor_invariance_checks.tsv",
        "checks": output_dir / "cohort_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    for frame, key in [
        (donors, "all"), (primary, "primary"), (exclusion_flow, "flow"),
        (group_counts, "groups"), (scaling, "scaling"), (pathology, "pathology"),
        (invariance, "invariance"), (checks_table, "checks"),
    ]:
        atomic_write_tsv(frame, paths[key])
    write_artifacts([paths[key] for key in ["all", "primary", "flow", "groups", "scaling", "pathology", "invariance", "checks"]], project_root, paths["artifacts"])
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH02", state, project_root, config_path, started, failed,
        source_donors=len(donors), analysis_donors=len(primary),
        dementia_donors=int(primary["diagnosis"].eq("Dementia").sum()),
        no_dementia_donors=int(primary["diagnosis"].eq("No dementia").sum()),
        age_center=age_center, age_scale=age_scale,
        pmi_center=pmi_center, pmi_scale=pmi_scale,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH02 status: {state}; donors={len(primary)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
