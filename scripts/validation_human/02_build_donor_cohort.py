#!/usr/bin/env python3
"""VH02: derive the authoritative donor cohort from H5AD observation metadata."""

from __future__ import annotations

import numpy as np
import pandas as pd
import h5py

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    decode_scalar,
    load_config,
    parse_config_cli,
    phase_output_dir,
    read_categorical_codes,
    repo_path,
    require_validated_status,
    status_frame,
    utc_now,
)


def donor_level_field(h5: h5py.File, field: str, donor_codes: np.ndarray, first_indices: np.ndarray):
    encoded = read_categorical_codes(h5, field)
    if encoded is not None:
        codes, categories = encoded
        first_codes = codes[first_indices]
        values = np.asarray(
            [None if int(code) < 0 else str(categories[int(code)]) for code in first_codes],
            dtype=object,
        )
        expected = first_codes[donor_codes.astype(np.int64)]
        mismatch = codes != expected
        return values, mismatch
    data = h5["obs"][field][...]
    values = data[first_indices]
    expected = values[donor_codes.astype(np.int64)]
    if np.issubdtype(data.dtype, np.floating):
        mismatch = ~(np.isclose(data, expected, equal_nan=True))
    else:
        mismatch = data != expected
    return values, mismatch


def main() -> int:
    args = parse_config_cli("VH02: build SEA-AD donor cohort")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_validated_status(output_root / "01_audit/status.tsv")
    output_dir = phase_output_dir(output_root, "02_cohort")
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    cohort_config = config["cohort"]
    expected = config["expected"]

    fields = {
        "neurotypical_reference": cohort_config["neurotypical_reference_field"],
        "diagnosis_source": cohort_config["diagnosis_field"],
        "sex_source": cohort_config["sex_field"],
        "apoe_genotype": cohort_config["apoe_field"],
        "age_death": cohort_config["age_field"],
        "pmi_source": cohort_config["pmi_field"],
        "study_source": cohort_config["study_field"],
        "pathology_source": cohort_config["pathology_field"],
    }

    with h5py.File(h5ad_path, "r") as h5:
        donor_encoded = read_categorical_codes(h5, cohort_config["donor_field"])
        if donor_encoded is None:
            raise ValueError("Donor ID must be categorically encoded")
        donor_codes, donor_categories = donor_encoded
        n_donors = len(donor_categories)
        first_indices = np.full(n_donors, donor_codes.size, dtype=np.int64)
        np.minimum.at(first_indices, donor_codes.astype(np.int64), np.arange(donor_codes.size, dtype=np.int64))
        if np.any(first_indices == donor_codes.size):
            raise ValueError("At least one donor category is unused")
        donor_nuclei = np.bincount(donor_codes.astype(np.int64), minlength=n_donors)

        donor_table = pd.DataFrame(
            {
                "donor_id": donor_categories.astype(str),
                "source_nuclei": donor_nuclei.astype(np.int64),
                "first_observation_index": first_indices,
            }
        )
        invariance_rows = []
        for output_name, field in fields.items():
            values, mismatch = donor_level_field(h5, field, donor_codes, first_indices)
            donor_table[output_name] = values
            mismatches = np.bincount(
                donor_codes.astype(np.int64), weights=mismatch.astype(np.int64), minlength=n_donors
            ).astype(np.int64)
            for index, donor in enumerate(donor_categories):
                invariance_rows.append(
                    {
                        "donor_id": str(donor),
                        "field": field,
                        "invariant": mismatches[index] == 0,
                        "mismatching_nuclei": mismatches[index],
                    }
                )

    donor_table["age_death"] = pd.to_numeric(donor_table["age_death"], errors="coerce")
    donor_table["pmi"] = pd.to_numeric(donor_table["pmi_source"], errors="coerce")
    donor_table["diagnosis"] = donor_table["diagnosis_source"].astype("string")
    donor_table["sex"] = donor_table["sex_source"].astype("string")
    donor_table["study"] = donor_table["study_source"].astype("string")

    apoe_lookup = {}
    for group, genotypes in cohort_config["apoe_groups"].items():
        for genotype in genotypes:
            apoe_lookup[str(genotype)] = str(group)
    donor_table["apoe_group"] = donor_table["apoe_genotype"].map(apoe_lookup)

    reference = donor_table["neurotypical_reference"].astype(str).str.lower().eq("true")
    excluded_apoe = donor_table["apoe_genotype"].isin(cohort_config["excluded_apoe"])
    invalid_diagnosis = ~donor_table["diagnosis"].isin(cohort_config["included_diagnoses"])
    incomplete = donor_table[
        ["diagnosis", "sex", "apoe_group", "age_death", "pmi", "study"]
    ].isna().any(axis=1)

    reason = np.full(len(donor_table), "included", dtype=object)
    reason[reference.to_numpy()] = "neurotypical_reference"
    reason[(~reference & excluded_apoe).to_numpy()] = "APOE_2_4"
    reason[(~reference & ~excluded_apoe & invalid_diagnosis).to_numpy()] = "invalid_diagnosis"
    reason[(~reference & ~excluded_apoe & ~invalid_diagnosis & incomplete).to_numpy()] = "incomplete_model_covariates"
    donor_table["exclusion_reason"] = reason
    donor_table["included_primary"] = donor_table["exclusion_reason"].eq("included")

    primary = donor_table.loc[donor_table["included_primary"]].copy()
    age_mean = primary["age_death"].mean()
    age_sd = primary["age_death"].std(ddof=1)
    pmi_mean = primary["pmi"].mean()
    pmi_sd = primary["pmi"].std(ddof=1)
    primary["age_death_scaled"] = (primary["age_death"] - age_mean) / age_sd
    primary["pmi_scaled"] = (primary["pmi"] - pmi_mean) / pmi_sd
    primary = primary.sort_values("donor_id").reset_index(drop=True)

    invariance = pd.DataFrame(invariance_rows)
    group_counts = (
        primary.groupby(["diagnosis", "sex", "apoe_group"], observed=True)
        .size()
        .rename("donors")
        .reset_index()
        .sort_values(["diagnosis", "sex", "apoe_group"])
    )
    pathology = (
        primary.groupby(["diagnosis", "pathology_source"], dropna=False, observed=True)
        .size()
        .rename("donors")
        .reset_index()
    )
    flow = pd.DataFrame(
        [
            {"stage": "source_donors", "donors": len(donor_table)},
            {"stage": "after_reference_exclusion", "donors": int((~reference).sum())},
            {"stage": "after_APOE_2_4_exclusion", "donors": int((~reference & ~excluded_apoe).sum())},
            {"stage": "primary_complete_covariates", "donors": len(primary)},
        ]
    )

    checks = [
        ("source_donor_count", len(donor_table) == expected["source_donors"], len(donor_table), expected["source_donors"], ""),
        ("donor_fields_invariant", bool(invariance["invariant"].all()), int((~invariance["invariant"]).sum()), 0, ""),
        ("primary_donor_count", len(primary) == expected["primary_donors"], len(primary), expected["primary_donors"], ""),
        ("dementia_donor_count", int((primary["diagnosis"] == "Dementia").sum()) == expected["dementia_donors"], int((primary["diagnosis"] == "Dementia").sum()), expected["dementia_donors"], ""),
        ("no_dementia_donor_count", int((primary["diagnosis"] == "No dementia").sum()) == expected["no_dementia_donors"], int((primary["diagnosis"] == "No dementia").sum()), expected["no_dementia_donors"], ""),
        ("complete_model_covariates", not primary[["diagnosis", "sex", "apoe_group", "age_death", "pmi", "study"]].isna().any().any(), int(primary[["diagnosis", "sex", "apoe_group", "age_death", "pmi", "study"]].isna().sum().sum()), 0, ""),
        ("excluded_reference_count", int(reference.sum()) == 3, int(reference.sum()), 3, ""),
        ("excluded_APOE_2_4_count", int((~reference & excluded_apoe).sum()) == 2, int((~reference & excluded_apoe).sum()), 2, ""),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "all": output_dir / "donor_metadata_all.tsv",
        "primary": output_dir / "donor_cohort_primary.tsv",
        "flow": output_dir / "cohort_exclusion_flow.tsv",
        "groups": output_dir / "donor_group_counts.tsv",
        "pathology": output_dir / "cognitive_pathology_crosstab.tsv",
        "invariance": output_dir / "donor_invariance_checks.tsv",
        "checks": output_dir / "cohort_checks.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(donor_table.sort_values("donor_id"), paths["all"])
    atomic_write_tsv(primary, paths["primary"])
    atomic_write_tsv(flow, paths["flow"])
    atomic_write_tsv(group_counts, paths["groups"])
    atomic_write_tsv(pathology, paths["pathology"])
    atomic_write_tsv(invariance, paths["invariance"])
    atomic_write_tsv(checks_table, paths["checks"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH02",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        source_donors=len(donor_table),
        primary_donors=len(primary),
        dementia_donors=int((primary["diagnosis"] == "Dementia").sum()),
        no_dementia_donors=int((primary["diagnosis"] == "No dementia").sum()),
        age_mean=age_mean,
        age_sd=age_sd,
        pmi_mean=pmi_mean,
        pmi_sd=pmi_sd,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH02 status: {validation_status}; primary donors: {len(primary)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
