#!/usr/bin/env python3
"""VH04: map every H5AD observation to one isolated broad pseudobulk group."""

from __future__ import annotations

import numpy as np
import pandas as pd
import h5py

from seaad_common import (
    atomic_save_npy,
    atomic_write_tsv,
    checks_frame,
    decode_scalar,
    decode_strings,
    load_config,
    parse_config_cli,
    phase_output_dir,
    read_categorical_codes,
    repo_path,
    require_validated_status,
    sha256_array,
    sha256_strings,
    status_frame,
    utc_now,
)


def codes_and_categories(h5, field):
    encoded = read_categorical_codes(h5, field)
    if encoded is None:
        raise ValueError(f"Expected categorical H5AD field: {field}")
    return encoded


def category_mask(codes, categories, requested):
    lookup = {str(value): index for index, value in enumerate(categories)}
    target = [lookup[value] for value in requested if value in lookup]
    return np.isin(codes, target)


def main() -> int:
    args = parse_config_cli("VH04: build nucleus-to-group manifest")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    vh01_status = require_validated_status(output_root / "01_audit/status.tsv")
    require_validated_status(output_root / "02_cohort/status.tsv")
    require_validated_status(output_root / "03_genes/status.tsv")
    output_dir = phase_output_dir(output_root, "04_cell_manifest")

    cohort = pd.read_csv(output_root / "02_cohort/donor_cohort_primary.tsv", sep="\t")
    cohort["donor_id"] = cohort["donor_id"].astype(str)
    cohort_lookup = cohort.set_index("donor_id")
    contexts = list(config["broad_context_order"])
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])

    with h5py.File(h5ad_path, "r") as h5:
        obs = h5["obs"]
        index_name = decode_scalar(obs.attrs["_index"])
        observation_ids = decode_strings(obs[index_name][...])
        donor_codes, donor_categories = codes_and_categories(h5, config["cohort"]["donor_field"])
        method_codes, method_categories = codes_and_categories(h5, config["assay"]["method_field"])
        class_codes, class_categories = codes_and_categories(h5, "Class")
        subclass_codes, subclass_categories = codes_and_categories(h5, "Subclass")
        supertype_codes, supertype_categories = codes_and_categories(h5, "Supertype")
        used = obs[config["assay"]["used_field"]][...].astype(bool)

    n_obs = len(observation_ids)
    included_donor_category_codes = [
        index for index, donor in enumerate(donor_categories) if str(donor) in cohort_lookup.index
    ]
    donor_included = np.isin(donor_codes, included_donor_category_codes)
    method_included = category_mask(
        method_codes, method_categories, [config["assay"]["method_value"]]
    )
    base_included = used & method_included & donor_included

    context_index = np.full(n_obs, -1, dtype=np.int8)
    mapping_memberships = np.zeros(n_obs, dtype=np.int8)
    micro_excluded = np.zeros(n_obs, dtype=bool)
    for index, context in enumerate(contexts):
        rule = config["broad_contexts"][context]
        if rule["field"] == "Class":
            match = category_mask(class_codes, class_categories, rule["values"])
        elif rule["field"] == "Subclass":
            match = category_mask(subclass_codes, subclass_categories, rule["values"])
        else:
            raise ValueError(f"Unsupported broad mapping field: {rule['field']}")
        if context == "Microglia":
            excluded = category_mask(
                supertype_codes,
                supertype_categories,
                rule.get("excluded_supertypes", []),
            )
            micro_excluded = match & excluded
            match = match & ~excluded
        mapping_memberships += match.astype(np.int8)
        assign = base_included & match
        if np.any(context_index[assign] >= 0):
            raise ValueError(f"Broad mappings overlap while assigning {context}")
        context_index[assign] = index

    selected = context_index >= 0
    included_donors = sorted(cohort["donor_id"].tolist())
    included_index = {donor: index for index, donor in enumerate(included_donors)}
    donor_category_to_included = np.full(len(donor_categories), -1, dtype=np.int16)
    for category_index, donor in enumerate(donor_categories):
        if str(donor) in included_index:
            donor_category_to_included[category_index] = included_index[str(donor)]
    donor_primary_index = donor_category_to_included[donor_codes.astype(np.int64)]
    pair_codes = donor_primary_index.astype(np.int32) * len(contexts) + context_index.astype(np.int32)
    pair_counts = np.bincount(
        pair_codes[selected], minlength=len(included_donors) * len(contexts)
    ).astype(np.int64)
    present_pairs = np.flatnonzero(pair_counts > 0)
    pair_to_group = np.full(pair_counts.size, -1, dtype=np.int32)
    pair_to_group[present_pairs] = np.arange(len(present_pairs), dtype=np.int32)
    group_codes = np.full(n_obs, -1, dtype=np.int32)
    group_codes[selected] = pair_to_group[pair_codes[selected]]

    complete_rows = []
    manifest_rows = []
    for donor_position, donor in enumerate(included_donors):
        donor_metadata = cohort_lookup.loc[donor]
        for context_position, context in enumerate(contexts):
            pair = donor_position * len(contexts) + context_position
            nuclei = int(pair_counts[pair])
            group_code = int(pair_to_group[pair])
            base = {
                "donor_id": donor,
                "context": context,
                "nuclei": nuclei,
                "group_code": group_code if group_code >= 0 else pd.NA,
                "primary_nuclei_eligible": nuclei >= int(config["thresholds"]["primary_min_nuclei"]),
                "sensitivity_nuclei_eligible": nuclei >= int(config["thresholds"]["sensitivity_min_nuclei"]),
            }
            complete_rows.append(base)
            if group_code >= 0:
                manifest_rows.append(
                    {
                        "group_code": group_code,
                        "pseudobulk_id": f"{context}__{donor}",
                        "donor_id": donor,
                        "context": context,
                        "nuclei": nuclei,
                        "diagnosis": donor_metadata["diagnosis"],
                        "sex": donor_metadata["sex"],
                        "apoe_group": donor_metadata["apoe_group"],
                        "apoe_genotype": donor_metadata["apoe_genotype"],
                        "age_death": donor_metadata["age_death"],
                        "pmi": donor_metadata["pmi"],
                        "study": donor_metadata["study"],
                        "age_death_scaled": donor_metadata["age_death_scaled"],
                        "pmi_scaled": donor_metadata["pmi_scaled"],
                    }
                )

    reason_code = np.full(n_obs, 4, dtype=np.int8)
    reason_code[~used] = 1
    reason_code[used & ~method_included] = 2
    reason_code[used & method_included & ~donor_included] = 3
    reason_code[base_included & micro_excluded & (context_index < 0)] = 5
    reason_code[selected] = 0
    reasons = np.asarray(
        ["selected", "not_used_in_analysis", "non_primary_method", "donor_not_in_primary_cohort", "no_primary_broad_mapping", "excluded_immune_supertype"],
        dtype=object,
    )

    selection = pd.DataFrame(
        {
            "observation_index": np.arange(n_obs, dtype=np.int64),
            "nucleus_id": observation_ids,
            "donor_id": pd.Categorical(
                [str(donor_categories[int(code)]) for code in donor_codes]
            ),
            "selected": selected,
            "context": pd.Categorical.from_codes(
                context_index, categories=contexts
            ),
            "group_code": group_codes,
            "exclusion_reason": pd.Categorical.from_codes(reason_code, categories=reasons),
        }
    )
    group_manifest = pd.DataFrame(manifest_rows).sort_values("group_code")
    donor_context = pd.DataFrame(complete_rows)
    exclusion_summary = (
        selection.groupby("exclusion_reason", observed=False)
        .size()
        .rename("nuclei")
        .reset_index()
    )
    observation_checksum = sha256_strings(observation_ids)
    group_checksum = sha256_array(group_codes)
    expected_observation_checksum = str(vh01_status.loc[0, "observation_order_sha256"])

    checks = [
        ("observation_count", n_obs == int(config["expected"]["observations"]), n_obs, config["expected"]["observations"], ""),
        ("observation_order_checksum", observation_checksum == expected_observation_checksum, observation_checksum, expected_observation_checksum, ""),
        ("mapping_rules_nonoverlap", int(mapping_memberships.max()) <= 1, int(mapping_memberships.max()), 1, ""),
        ("selected_group_codes_valid", bool(np.all(group_codes[selected] >= 0)), int(np.sum(group_codes[selected] < 0)), 0, ""),
        ("excluded_group_codes_negative", bool(np.all(group_codes[~selected] == -1)), int(np.sum(group_codes[~selected] != -1)), 0, ""),
        ("all_contexts_present", set(group_manifest["context"]) == set(contexts), "|".join(sorted(group_manifest["context"].unique())), "|".join(sorted(contexts)), ""),
        ("all_primary_donors_represented", group_manifest["donor_id"].nunique() == len(included_donors), group_manifest["donor_id"].nunique(), len(included_donors), ""),
        ("only_primary_method_selected", bool(np.all(method_included[selected])), int(np.sum(~method_included[selected])), 0, ""),
        ("only_primary_donors_selected", bool(np.all(donor_included[selected])), int(np.sum(~donor_included[selected])), 0, ""),
        ("group_manifest_codes_contiguous", group_manifest["group_code"].tolist() == list(range(len(group_manifest))), str((group_manifest["group_code"].min(), group_manifest["group_code"].max())), f"0..{len(group_manifest)-1}", ""),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "codes": output_dir / "nucleus_to_group_code.npy",
        "selection": output_dir / "nucleus_selection.tsv.gz",
        "manifest": output_dir / "pseudobulk_group_manifest.tsv",
        "counts": output_dir / "donor_context_nucleus_counts.tsv",
        "exclusions": output_dir / "nucleus_exclusion_summary.tsv",
        "checksum": output_dir / "observation_order_checksum.tsv",
        "checks": output_dir / "cell_manifest_checks.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_save_npy(group_codes, paths["codes"])
    atomic_write_tsv(selection, paths["selection"])
    atomic_write_tsv(group_manifest, paths["manifest"])
    atomic_write_tsv(donor_context, paths["counts"])
    atomic_write_tsv(exclusion_summary, paths["exclusions"])
    atomic_write_tsv(
        pd.DataFrame([{"observations": n_obs, "observation_order_sha256": observation_checksum, "group_code_sha256": group_checksum}]),
        paths["checksum"],
    )
    atomic_write_tsv(checks_table, paths["checks"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH04",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        observations=n_obs,
        selected_nuclei=int(selected.sum()),
        pseudobulk_groups=len(group_manifest),
        represented_donors=group_manifest["donor_id"].nunique(),
        observation_order_sha256=observation_checksum,
        group_code_sha256=group_checksum,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH04 status: {validation_status}; selected nuclei: {int(selected.sum())}; groups: {len(group_manifest)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
