#!/usr/bin/env python3
"""VH04: freeze 129-supertype taxonomy, selection, and fine/broad group codes."""

from __future__ import annotations

import re

import h5py
import numpy as np
import pandas as pd

from seaad_common import (
    atomic_save_npy,
    atomic_write_tsv,
    checks_frame,
    decode_scalar,
    decode_strings,
    load_config,
    parse_config_cli,
    phase_dir,
    read_categorical_codes,
    repo_path,
    require_phase,
    sha256_array,
    sha256_strings,
    status_frame,
    utc_now,
    write_artifacts,
)


def slug(label):
    value = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return value or "unnamed"


def map_broad(class_label, subclass_label):
    if subclass_label == "Astrocyte":
        return "Astrocytes"
    if class_label == "Neuronal: Glutamatergic":
        return "Excitatory_neurons"
    if class_label == "Neuronal: GABAergic":
        return "Inhibitory_neurons"
    if subclass_label == "Microglia-PVM":
        return "Microglia"
    if subclass_label == "OPC":
        return "OPCs"
    if subclass_label == "Oligodendrocyte":
        return "Oligodendrocytes"
    if subclass_label in {"Endothelial", "VLMC"}:
        return "Vasculature_cells"
    return None


def main() -> int:
    args = parse_config_cli("VH04: build supertype and nucleus manifests")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    vh01 = require_phase(output_root, "01_audit")
    require_phase(output_root, "02_cohort")
    require_phase(output_root, "03_genes")
    output_dir = phase_dir(output_root, "04_supertype_manifest")
    expected = config["expected_identity"]
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    cohort = pd.read_csv(output_root / "02_cohort/donor_cohort_primary.tsv", sep="	", dtype={"donor_id": str})
    cohort = cohort.sort_values("donor_id").reset_index(drop=True)
    cohort_lookup = cohort.set_index("donor_id")

    with h5py.File(h5ad_path, "r") as h5:
        obs = h5["obs"]
        index_name = decode_scalar(obs.attrs["_index"])
        observation_ids = decode_strings(obs[index_name][...])
        donor_codes, donor_categories = read_categorical_codes(h5, config["cohort"]["donor_field"])
        method_codes, method_categories = read_categorical_codes(h5, config["assay"]["method_field"])
        class_codes, class_categories = read_categorical_codes(h5, "Class")
        subclass_codes, subclass_categories = read_categorical_codes(h5, "Subclass")
        supertype_codes, supertype_categories = read_categorical_codes(h5, "Supertype")
        used = obs[config["assay"]["used_field"]][...].astype(bool)

    n_obs = len(observation_ids)
    supertype_counts = np.bincount(supertype_codes[supertype_codes >= 0], minlength=len(supertype_categories))
    _, first_indices = np.unique(supertype_codes, return_index=True)
    first_by_supertype = np.full(len(supertype_categories), -1, dtype=np.int64)
    first_by_supertype[supertype_codes[first_indices].astype(int)] = first_indices
    first_class = class_codes[first_by_supertype]
    first_subclass = subclass_codes[first_by_supertype]
    taxonomy_invariant = bool(
        np.all(class_codes == first_class[supertype_codes.astype(int)])
        and np.all(subclass_codes == first_subclass[supertype_codes.astype(int)])
    )

    raw_rows = []
    excluded_names = set(config["taxonomy"]["excluded_microglia_supertypes"])
    broad_order = config["taxonomy"]["broad_network_order"]
    for code, label in enumerate(supertype_categories):
        class_label = str(class_categories[int(first_class[code])])
        subclass_label = str(subclass_categories[int(first_subclass[code])])
        broad = map_broad(class_label, subclass_label)
        relevant = broad is not None
        excluded = relevant and str(label) in excluded_names
        raw_rows.append({
            "raw_supertype_code": code,
            "supertype_label": str(label),
            "subclass": subclass_label,
            "class": class_label,
            "broad_network": broad,
            "raw_nuclei": int(supertype_counts[code]),
            "relevant_lineage": relevant,
            "excluded_by_protocol": excluded,
            "included": relevant and not excluded,
        })
    inventory = pd.DataFrame(raw_rows)
    relevant_inventory = inventory.loc[inventory["relevant_lineage"]].copy()
    included = relevant_inventory.loc[relevant_inventory["included"]].copy()
    included["broad_order"] = included["broad_network"].map({value: i for i, value in enumerate(broad_order)})
    included = included.sort_values(["broad_order", "raw_supertype_code"]).reset_index(drop=True)
    included["supertype_index"] = np.arange(len(included), dtype=int)
    included["supertype_id"] = [
        f"st{index + 1:03d}_{slug(label)}"
        for index, label in enumerate(included["supertype_label"])
    ]
    broad_index = {value: index for index, value in enumerate(broad_order)}
    included["broad_network_index"] = included["broad_network"].map(broad_index).astype(int)
    mapping = included[[
        "supertype_index", "supertype_id", "supertype_label", "subclass", "class",
        "broad_network", "broad_network_index", "raw_supertype_code",
    ]].copy()
    safe_ids = mapping[["supertype_index", "supertype_id", "supertype_label"]].copy()

    donor_position = {donor: index for index, donor in enumerate(cohort["donor_id"])}
    donor_category_position = np.full(len(donor_categories), -1, dtype=np.int16)
    for code, donor in enumerate(donor_categories):
        if str(donor) in donor_position:
            donor_category_position[code] = donor_position[str(donor)]
    donor_pos = donor_category_position[donor_codes.astype(int)]
    method_lookup = {str(value): index for index, value in enumerate(method_categories)}
    primary_method = method_codes == method_lookup[config["assay"]["method_value"]]

    raw_to_supertype = np.full(len(supertype_categories), -1, dtype=np.int16)
    raw_to_broad = np.full(len(supertype_categories), -1, dtype=np.int8)
    for row in mapping.itertuples(index=False):
        raw_to_supertype[row.raw_supertype_code] = row.supertype_index
        raw_to_broad[row.raw_supertype_code] = row.broad_network_index
    supertype_pos = raw_to_supertype[supertype_codes.astype(int)]
    broad_pos = raw_to_broad[supertype_codes.astype(int)]
    base_selected = used & primary_method & (donor_pos >= 0)
    selected = base_selected & (supertype_pos >= 0)

    fine_codes = np.full(n_obs, -1, dtype=np.int32)
    broad_codes = np.full(n_obs, -1, dtype=np.int16)
    fine_codes[selected] = donor_pos[selected].astype(np.int32) * len(mapping) + supertype_pos[selected].astype(np.int32)
    broad_codes[selected] = donor_pos[selected].astype(np.int16) * len(broad_order) + broad_pos[selected].astype(np.int16)
    fine_counts = np.bincount(fine_codes[selected], minlength=len(cohort) * len(mapping)).astype(np.int64)
    broad_counts = np.bincount(broad_codes[selected], minlength=len(cohort) * len(broad_order)).astype(np.int64)

    profile_rows = []
    for donor_idx, donor in enumerate(cohort["donor_id"]):
        metadata = cohort_lookup.loc[donor]
        for row in mapping.to_dict("records"):
            code = donor_idx * len(mapping) + row["supertype_index"]
            nuclei = int(fine_counts[code])
            profile_rows.append({
                "fine_group_code": code,
                "pseudobulk_id": f"{row['supertype_id']}__{donor}",
                "donor_id": donor,
                "supertype_index": row["supertype_index"],
                "supertype_id": row["supertype_id"],
                "supertype_label": row["supertype_label"],
                "subclass": row["subclass"],
                "class": row["class"],
                "broad_network": row["broad_network"],
                "nuclei": nuclei,
                "primary_profile_eligible": nuclei >= config["thresholds"]["primary_min_nuclei"],
                "sensitivity_profile_eligible": nuclei >= config["thresholds"]["sensitivity_min_nuclei"],
                "diagnosis": metadata["diagnosis"],
                "sex": metadata["sex"],
                "apoe_group": metadata["apoe_group"],
                "signature_group": metadata["signature_group"],
                "age_death": metadata["age_death"],
                "pmi": metadata["pmi"],
                "study": metadata["study"],
                "age_death_scaled": metadata["age_death_scaled"],
                "pmi_scaled": metadata["pmi_scaled"],
            })
    profiles = pd.DataFrame(profile_rows)
    support = (
        profiles.loc[profiles["primary_profile_eligible"]]
        .groupby(["supertype_id", "supertype_label", "broad_network", "signature_group", "diagnosis"], observed=True)
        .size().rename("donors").reset_index()
        .pivot_table(index=["supertype_id", "supertype_label", "broad_network", "signature_group"], columns="diagnosis", values="donors", fill_value=0)
        .reset_index()
    )
    for column in ["Dementia", "No dementia"]:
        if column not in support:
            support[column] = 0
    full_support = pd.MultiIndex.from_product(
        [mapping["supertype_id"], [row["group_id"] for row in config["cohort"]["signature_groups"]]],
        names=["supertype_id", "signature_group"],
    ).to_frame(index=False)
    full_support = full_support.merge(mapping[["supertype_id", "supertype_label", "broad_network"]], on="supertype_id", how="left")
    full_support = full_support.merge(support, on=["supertype_id", "supertype_label", "broad_network", "signature_group"], how="left")
    full_support[["Dementia", "No dementia"]] = full_support[["Dementia", "No dementia"]].fillna(0).astype(int)
    minimum = int(config["thresholds"]["min_donors_per_disease_arm"])
    full_support["support_pass"] = (full_support["Dementia"] >= minimum) & (full_support["No dementia"] >= minimum)
    full_support["support_reason"] = np.where(full_support["support_pass"], "", "disease_arm_below_5")

    reason = np.full(n_obs, 5, dtype=np.int8)
    reason[~used] = 1
    reason[used & ~primary_method] = 2
    reason[used & primary_method & (donor_pos < 0)] = 3
    excluded_immune = np.isin(
        supertype_codes,
        [index for index, value in enumerate(supertype_categories) if str(value) in excluded_names],
    )
    reason[base_selected & excluded_immune] = 4
    reason[selected] = 0
    reason_labels = ["selected", "not_used_in_analysis", "non_primary_method", "donor_not_in_analysis_cohort", "excluded_immune_supertype", "outside_frozen_taxonomy"]
    donor_labels = np.asarray([str(value) for value in donor_categories], dtype=object)[donor_codes.astype(int)]
    supertype_labels = np.asarray([str(value) for value in supertype_categories], dtype=object)[supertype_codes.astype(int)]
    selected_supertype_labels = np.empty(n_obs, dtype=object)
    selected_supertype_labels[:] = None
    selected_supertype_labels[selected] = mapping.set_index("supertype_index").loc[supertype_pos[selected], "supertype_id"].to_numpy()
    selected_broad_labels = np.empty(n_obs, dtype=object)
    selected_broad_labels[:] = None
    selected_broad_labels[selected] = np.asarray(broad_order, dtype=object)[broad_pos[selected]]
    selection = pd.DataFrame({
        "observation_index": np.arange(n_obs, dtype=np.int64),
        "nucleus_id": observation_ids,
        "donor_id": pd.Categorical(donor_labels),
        "raw_supertype": pd.Categorical(supertype_labels),
        "selected": selected,
        "supertype_id": pd.Categorical(selected_supertype_labels, categories=mapping["supertype_id"]),
        "broad_network": pd.Categorical(selected_broad_labels, categories=broad_order),
        "fine_group_code": fine_codes,
        "direct_broad_group_code": broad_codes,
        "exclusion_reason": pd.Categorical.from_codes(reason, categories=reason_labels),
    })
    exclusion_summary = selection.groupby("exclusion_reason", observed=False).size().rename("nuclei").reset_index()
    direct_broad_rows = []
    for donor_idx, donor in enumerate(cohort["donor_id"]):
        for network_idx, network in enumerate(broad_order):
            direct_broad_rows.append({
                "direct_broad_group_code": donor_idx * len(broad_order) + network_idx,
                "pseudobulk_id": f"{network}__{donor}",
                "donor_id": donor,
                "broad_network": network,
                "nuclei": int(broad_counts[donor_idx * len(broad_order) + network_idx]),
            })
    direct_broad_profiles = pd.DataFrame(direct_broad_rows)

    observed_distribution = mapping.groupby("broad_network", observed=True).size().to_dict()
    expected_distribution = config["taxonomy"]["expected_supertype_counts"]
    observation_sha = sha256_strings(observation_ids)
    fine_sha = sha256_array(fine_codes)
    broad_sha = sha256_array(broad_codes)
    checks = [
        ("observation_count", n_obs == expected["observations"], n_obs, expected["observations"], ""),
        ("observation_order", observation_sha == str(vh01.loc[0, "observation_order_sha256"]), observation_sha, str(vh01.loc[0, "observation_order_sha256"]), ""),
        ("taxonomy_invariant_within_supertype", taxonomy_invariant, taxonomy_invariant, True, ""),
        ("relevant_raw_supertypes", len(relevant_inventory) == 131, len(relevant_inventory), 131, ""),
        ("excluded_supertypes_exact", set(relevant_inventory.loc[~relevant_inventory["included"], "supertype_label"]) == excluded_names, "|".join(sorted(relevant_inventory.loc[~relevant_inventory["included"], "supertype_label"])), "|".join(sorted(excluded_names)), ""),
        ("included_supertypes", len(mapping) == expected["included_supertypes"], len(mapping), expected["included_supertypes"], ""),
        ("broad_distribution", observed_distribution == expected_distribution, str(observed_distribution), str(expected_distribution), ""),
        ("selected_nuclei", int(selected.sum()) == expected["selected_nuclei"], int(selected.sum()), expected["selected_nuclei"], ""),
        ("fine_profile_grid", len(profiles) == expected["fine_profiles"], len(profiles), expected["fine_profiles"], ""),
        ("fine_codes_valid", bool(np.all(fine_codes[selected] >= 0) and np.all(fine_codes[~selected] < 0)), int(np.sum(fine_codes[selected] < 0) + np.sum(fine_codes[~selected] >= 0)), 0, ""),
        ("broad_codes_valid", bool(np.all(broad_codes[selected] >= 0) and np.all(broad_codes[~selected] < 0)), int(np.sum(broad_codes[selected] < 0) + np.sum(broad_codes[~selected] >= 0)), 0, ""),
        ("support_preflight_rows", len(full_support) == expected["fine_contrasts"], len(full_support), expected["fine_contrasts"], ""),
        ("support_preflight_pass", int(full_support["support_pass"].sum()) == expected["fine_support_passing"], int(full_support["support_pass"].sum()), expected["fine_support_passing"], ""),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "inventory": output_dir / "supertype_inventory.tsv",
        "mapping": output_dir / "supertype_to_broad_network.tsv",
        "safe": output_dir / "supertype_safe_ids.tsv",
        "fine_codes": output_dir / "nucleus_to_supertype_group_code.npy",
        "broad_codes": output_dir / "nucleus_to_direct_broad_group_code.npy",
        "selection": output_dir / "nucleus_selection.tsv.gz",
        "profiles": output_dir / "donor_supertype_nucleus_counts.tsv",
        "broad_profiles": output_dir / "donor_direct_broad_nucleus_counts.tsv",
        "exclusions": output_dir / "nucleus_exclusion_summary.tsv",
        "support": output_dir / "support_preflight.tsv",
        "checks": output_dir / "cell_manifest_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(relevant_inventory, paths["inventory"])
    atomic_write_tsv(mapping, paths["mapping"])
    atomic_write_tsv(safe_ids, paths["safe"])
    atomic_save_npy(fine_codes, paths["fine_codes"])
    atomic_save_npy(broad_codes, paths["broad_codes"])
    atomic_write_tsv(selection, paths["selection"])
    atomic_write_tsv(profiles, paths["profiles"])
    atomic_write_tsv(direct_broad_profiles, paths["broad_profiles"])
    atomic_write_tsv(exclusion_summary, paths["exclusions"])
    atomic_write_tsv(full_support, paths["support"])
    atomic_write_tsv(checks_table, paths["checks"])
    write_artifacts([paths[key] for key in ["inventory", "mapping", "safe", "fine_codes", "broad_codes", "selection", "profiles", "broad_profiles", "exclusions", "support", "checks"]], project_root, paths["artifacts"])
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH04", state, project_root, config_path, started, failed,
        observations=n_obs, selected_nuclei=int(selected.sum()),
        included_supertypes=len(mapping), fine_profiles=len(profiles),
        support_passing_contrasts=int(full_support["support_pass"].sum()),
        observation_order_sha256=observation_sha,
        fine_group_code_sha256=fine_sha,
        direct_broad_group_code_sha256=broad_sha,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH04 status: {state}; selected={int(selected.sum())}; supertypes={len(mapping)}; support={int(full_support['support_pass'].sum())}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
