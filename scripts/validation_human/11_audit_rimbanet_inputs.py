#!/usr/bin/env python3
"""Audit full-integrative SEA-AD RIMBANet prerequisites and donor matching."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

from seaad_common import atomic_write_tsv
from rimbanet_common import (
    configured_path,
    load_rimbanet_config,
    parser,
    provenance_path,
    safe_project_path,
    stage_dir,
    write_stage_contract,
)


def plink_files(prefix: Path) -> list[Path]:
    pgen = [
        prefix.with_suffix(".pgen"),
        prefix.with_suffix(".pvar"),
        prefix.with_suffix(".psam"),
    ]
    pgen_zst = [pgen[0], Path(f"{pgen[1]}.zst"), pgen[2]]
    bed = [
        prefix.with_suffix(".bed"),
        prefix.with_suffix(".bim"),
        prefix.with_suffix(".fam"),
    ]
    for candidate in (pgen, pgen_zst, bed):
        if all(path.exists() for path in candidate):
            return candidate
    return []


def git_head(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def read_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    args = parser("Audit SEA-AD RIMBANet construction inputs").parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    output = stage_dir(output_root, "11a_audit")
    checks: list[tuple[str, bool, object, object, str]] = []
    artifacts: list[Path] = []

    cohort_path = safe_project_path(project_root, config["inputs"]["cohort"])
    cohort = pd.read_csv(cohort_path, sep="\t", dtype={"donor_id": str})
    included = cohort.loc[cohort["included_primary"].map(read_bool)].copy()
    expected_donors = int(config["expected_identity"]["analysis_donors"])
    checks.append(
        (
            "analysis_donor_count",
            len(included) == expected_donors and included["donor_id"].is_unique,
            len(included),
            expected_donors,
            "",
        )
    )
    artifacts.append(cohort_path)

    mapping_path = safe_project_path(project_root, config["inputs"]["celltype_mapping"])
    mapping = pd.read_csv(mapping_path, sep="\t")
    observed_networks = sorted(mapping["broad_network"].dropna().astype(str).unique())
    expected_networks = sorted(str(value) for value in config["networks"])
    checks.append(
        (
            "celltype_mapping_networks",
            observed_networks == expected_networks,
            ",".join(observed_networks),
            ",".join(expected_networks),
            "",
        )
    )
    artifacts.append(mapping_path)

    profiles_path = safe_project_path(
        project_root, config["inputs"]["broad_profile_manifest"]
    )
    profiles = pd.read_csv(profiles_path, sep="\t", dtype={"donor_id": str})
    expected_profiles = expected_donors * len(expected_networks)
    checks.append(
        (
            "broad_profile_count",
            len(profiles) == expected_profiles,
            len(profiles),
            expected_profiles,
            "",
        )
    )
    artifacts.append(profiles_path)

    pseudobulk_dir = configured_path(
        project_root, config["inputs"]["pseudobulk_directory"], must_exist=False
    )
    missing_pseudobulk = []
    for network in config["networks"]:
        for suffix in (
            config["expression"]["counts_suffix"],
            config["expression"]["samples_suffix"],
        ):
            path = pseudobulk_dir / f"{network}{suffix}"
            if path.exists():
                artifacts.append(path)
            else:
                missing_pseudobulk.append(provenance_path(path, project_root))
    checks.append(
        (
            "all_pseudobulk_shards_present",
            not missing_pseudobulk,
            len(missing_pseudobulk),
            0,
            ";".join(missing_pseudobulk),
        )
    )

    prefix = configured_path(
        project_root, config["inputs"]["wgs_raw_plink_prefix"], must_exist=False
    )
    genotype_files = plink_files(prefix)
    artifacts.extend(genotype_files)
    checks.append(
        (
            "controlled_wgs_plink_present",
            bool(genotype_files),
            len(genotype_files),
            3,
            provenance_path(prefix, project_root),
        )
    )

    crosswalk_path = configured_path(
        project_root, config["inputs"]["wgs_sample_crosswalk"], must_exist=False
    )
    donor_crosswalk = included[["donor_id", "sex"]].copy()
    donor_crosswalk["wgs_fid"] = "0"
    donor_crosswalk["wgs_sample_id"] = pd.NA
    donor_crosswalk["matched_wgs"] = False
    crosswalk_ok = False
    if crosswalk_path.exists():
        raw_crosswalk = pd.read_csv(crosswalk_path, sep="\t", dtype=str)
        required = {"donor_id", "wgs_sample_id"}
        if required.issubset(raw_crosswalk.columns):
            selected_columns = ["donor_id", "wgs_sample_id"]
            if "wgs_fid" in raw_crosswalk.columns:
                selected_columns.append("wgs_fid")
            donor_crosswalk = donor_crosswalk.drop(
                columns=["wgs_fid", "wgs_sample_id", "matched_wgs"]
            ).merge(
                raw_crosswalk[selected_columns].drop_duplicates(),
                on="donor_id",
                how="left",
                validate="one_to_one",
            )
            if "wgs_fid" not in donor_crosswalk.columns:
                donor_crosswalk["wgs_fid"] = "0"
            donor_crosswalk["wgs_fid"] = donor_crosswalk["wgs_fid"].fillna("0")
            donor_crosswalk["matched_wgs"] = donor_crosswalk[
                "wgs_sample_id"
            ].notna()
            crosswalk_ok = (
                raw_crosswalk["donor_id"].is_unique
                and raw_crosswalk["wgs_sample_id"].is_unique
                and int(donor_crosswalk["matched_wgs"].sum())
                >= int(config["genetics"]["minimum_matched_donors"])
            )
            artifacts.append(crosswalk_path)
    crosswalk_output = output / "donor_crosswalk.tsv"
    atomic_write_tsv(donor_crosswalk, crosswalk_output)
    artifacts.append(crosswalk_output)
    keep = donor_crosswalk.loc[
        donor_crosswalk["matched_wgs"], ["wgs_fid", "wgs_sample_id"]
    ].copy()
    keep = keep.rename(columns={"wgs_fid": "#FID", "wgs_sample_id": "IID"})
    keep_path = output / "wgs_keep.tsv"
    atomic_write_tsv(keep, keep_path)
    artifacts.append(keep_path)
    sex_codes = {"Male": "1", "Female": "2"}
    sex_update = donor_crosswalk.loc[
        donor_crosswalk["matched_wgs"], ["wgs_fid", "wgs_sample_id", "sex"]
    ].copy()
    sex_update["SEX"] = sex_update["sex"].map(sex_codes)
    sex_update = sex_update.rename(
        columns={"wgs_fid": "#FID", "wgs_sample_id": "IID"}
    )[["#FID", "IID", "SEX"]]
    sex_path = output / "wgs_sex.tsv"
    atomic_write_tsv(sex_update, sex_path)
    artifacts.append(sex_path)
    checks.append(
        (
            "wgs_sex_update_complete",
            not sex_update["SEX"].isna().any(),
            int(sex_update["SEX"].notna().sum()),
            len(sex_update),
            "",
        )
    )
    checks.append(
        (
            "wgs_expression_crosswalk_valid",
            crosswalk_ok,
            int(donor_crosswalk["matched_wgs"].sum()),
            f">={config['genetics']['minimum_matched_donors']} unique explicit matches",
            provenance_path(crosswalk_path, project_root),
        )
    )

    encode_path = configured_path(
        project_root, config["inputs"]["encode_tf_targets"], must_exist=False
    )
    encode_frozen = (
        encode_path.exists()
        and config["encode"]["source_sha256"] != "TO_BE_FROZEN"
        and "TO_BE_FROZEN" not in str(config["encode"]["release"])
    )
    if encode_path.exists():
        artifacts.append(encode_path)
    checks.append(
        (
            "encode_tf_targets_present_and_frozen",
            encode_frozen,
            encode_path.exists(),
            True,
            provenance_path(encode_path, project_root),
        )
    )

    rimbanet_root = configured_path(
        project_root, config["method"]["external_checkout"], must_exist=False
    )
    observed_commit = git_head(rimbanet_root) if rimbanet_root.exists() else "missing"
    checks.append(
        (
            "rimbanet_source_commit",
            observed_commit == config["method"]["source_commit"],
            observed_commit,
            config["method"]["source_commit"],
            "",
        )
    )

    sources_path = safe_project_path(
        project_root, config["encode"]["source_manifest"]
    )
    artifacts.append(sources_path)
    source_table = pd.read_csv(sources_path, sep="\t", dtype=str)
    checks.append(
        (
            "source_manifest_unique",
            source_table["source_id"].is_unique,
            source_table["source_id"].nunique(),
            len(source_table),
            "",
        )
    )

    failed = [name for name, passed, *_ in checks if not passed]
    state = "validated_complete" if not failed else "blocked_missing_prerequisites"
    write_stage_contract(
        output,
        "VH11A",
        state,
        config_path,
        project_root,
        checks,
        artifacts,
        failed_checks=";".join(failed),
        matched_wgs_donors=int(donor_crosswalk["matched_wgs"].sum()),
    )
    print(f"VH11A status: {state}; failed={len(failed)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
