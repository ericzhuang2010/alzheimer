#!/usr/bin/env python3
"""Audit full-integrative SEA-AD RIMBANet prerequisites and donor matching."""

from __future__ import annotations

import re
import subprocess
import tarfile
from pathlib import Path

import pandas as pd

from seaad_common import atomic_write_tsv, sha256_file
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

def read_vcf_samples(archive_path: Path, member: str) -> list[str]:
    with tarfile.open(archive_path, "r:gz") as archive:
        handle = archive.extractfile(member)
        if handle is None:
            raise ValueError(f"Missing VCF archive member: {member}")
        for raw_line in handle:
            if raw_line.startswith(b"#CHROM\t"):
                fields = raw_line.decode("utf-8").rstrip("\r\n").split("\t")
                return [value.strip() for value in fields[9:]]
    raise ValueError(f"VCF sample header not found in {member}")


def summary_metrics(path: Path) -> dict[str, int]:
    table = pd.read_csv(path, sep="\t", dtype={"metric": str})
    if list(table.columns) != ["metric", "value"] or not table["metric"].is_unique:
        raise ValueError(f"Malformed metric summary: {path}")
    values = pd.to_numeric(table["value"], errors="raise").astype(int)
    return dict(zip(table["metric"], values, strict=True))



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

    identity = config["expected_identity"]
    genotype_specs = [
        (
            "genotype_source_archive_frozen",
            "genotype_source_archive",
            "genotype_source_sha256",
            "genotype_source_bytes",
        ),
        (
            "genotype_d1_manifest_frozen",
            "genotype_d1_manifest",
            "genotype_d1_manifest_sha256",
            None,
        ),
        (
            "genotype_d2_manifest_frozen",
            "genotype_d2_manifest",
            "genotype_d2_manifest_sha256",
            None,
        ),
        (
            "genotype_reference_fasta_frozen",
            "genotype_reference_fasta",
            "genotype_reference_sha256",
            None,
        ),
        (
            "genotype_reference_fai_frozen",
            "genotype_reference_fai",
            "genotype_reference_fai_sha256",
            None,
        ),
        (
            "genotype_final_audit_frozen",
            "genotype_final_audit",
            "genotype_final_audit_sha256",
            None,
        ),
    ]
    genotype_paths: dict[str, Path] = {}
    for check_name, input_key, hash_key, bytes_key in genotype_specs:
        path = configured_path(
            project_root, config["inputs"][input_key], must_exist=False
        )
        genotype_paths[input_key] = path
        expected_sha256 = str(identity[hash_key])
        expected_bytes = int(identity[bytes_key]) if bytes_key else None
        if path.exists() and path.is_file():
            observed_bytes = path.stat().st_size
            observed_sha256 = sha256_file(path)
            passed = observed_sha256 == expected_sha256 and (
                expected_bytes is None or observed_bytes == expected_bytes
            )
            observed = f"bytes={observed_bytes};sha256={observed_sha256}"
        else:
            passed = False
            observed = "missing"
        expected_value = f"sha256={expected_sha256}"
        if expected_bytes is not None:
            expected_value = f"bytes={expected_bytes};{expected_value}"
        checks.append(
            (
                check_name,
                passed,
                observed,
                expected_value,
                provenance_path(path, project_root),
            )
        )

    final_audit_path = genotype_paths["genotype_final_audit"]
    audit_values: dict[str, int] = {}
    if final_audit_path.exists():
        try:
            audit_values = summary_metrics(final_audit_path)
            artifacts.append(final_audit_path)
        except (OSError, ValueError):
            audit_values = {}
    expected_audit_values = {
        "source_variant_rows": int(identity["genotype_source_variant_rows"]),
        "source_eligible_ids": int(identity["genotype_eligible_markers"]),
        "final_unique_reference_aligned": int(
            identity["genotype_final_unique_variants"]
        ),
    }
    audit_contract_ok = all(
        audit_values.get(name) == value
        for name, value in expected_audit_values.items()
    )
    checks.append(
        (
            "genotype_final_transformation_contract",
            audit_contract_ok,
            ";".join(
                f"{name}={audit_values.get(name, 'missing')}"
                for name in expected_audit_values
            ),
            ";".join(
                f"{name}={value}" for name, value in expected_audit_values.items()
            ),
            provenance_path(final_audit_path, project_root),
        )
    )

    source_archive = genotype_paths["genotype_source_archive"]
    source_samples: list[str] = []
    if source_archive.exists():
        try:
            source_samples = read_vcf_samples(
                source_archive, str(config["inputs"]["genotype_source_member"])
            )
        except (OSError, tarfile.TarError, UnicodeDecodeError, ValueError):
            source_samples = []
    sample_pattern = re.compile(r"^[0-9]+_(.+)$")
    source_sample_contract = (
        len(source_samples) == int(identity["genotype_source_samples"])
        and len(set(source_samples)) == len(source_samples)
        and all(sample_pattern.fullmatch(value) for value in source_samples)
    )
    checks.append(
        (
            "genotype_source_sample_header",
            source_sample_contract,
            len(source_samples),
            identity["genotype_source_samples"],
            provenance_path(source_archive, project_root),
        )
    )

    crosswalk_path = configured_path(
        project_root, config["inputs"]["genotype_sample_crosswalk"], must_exist=False
    )
    donor_crosswalk = included[["donor_id", "sex"]].copy()
    donor_crosswalk["genotype_fid"] = "0"
    donor_crosswalk["genotype_sample_id"] = pd.NA
    donor_crosswalk["matched_genotype"] = False
    crosswalk_ok = False
    crosswalk_permissions_ok = False
    crosswalk_sha256 = "missing"
    if crosswalk_path.exists() and crosswalk_path.is_file():
        crosswalk_sha256 = sha256_file(crosswalk_path)
        raw_crosswalk = pd.read_csv(crosswalk_path, sep="\t", dtype=str)
        required = {"donor_id", "genotype_sample_id"}
        schema_ok = required.issubset(raw_crosswalk.columns)
        if schema_ok:
            raw_crosswalk = raw_crosswalk.copy()
            if "genotype_fid" not in raw_crosswalk.columns:
                raw_crosswalk["genotype_fid"] = "0"
            donor_unique = raw_crosswalk["donor_id"].is_unique
            sample_unique = raw_crosswalk["genotype_sample_id"].is_unique
            exact_donors = set(raw_crosswalk["donor_id"]) == set(included["donor_id"])
            sample_set = set(raw_crosswalk["genotype_sample_id"])
            samples_present = sample_set.issubset(set(source_samples))
            suffixes_valid = all(
                (match := sample_pattern.fullmatch(str(row.genotype_sample_id)))
                and match.group(1) == str(row.donor_id)
                for row in raw_crosswalk.itertuples(index=False)
            )
            extra_samples = len(set(source_samples) - sample_set)
            crosswalk_ok = (
                crosswalk_sha256 == str(identity["genotype_crosswalk_sha256"])
                and donor_unique
                and sample_unique
                and exact_donors
                and samples_present
                and suffixes_valid
                and len(raw_crosswalk) == int(identity["genotype_primary_samples"])
                and extra_samples == int(identity["genotype_extra_samples"])
            )
            if donor_unique:
                donor_crosswalk = donor_crosswalk.drop(
                    columns=[
                        "genotype_fid",
                        "genotype_sample_id",
                        "matched_genotype",
                    ]
                ).merge(
                    raw_crosswalk[
                        ["donor_id", "genotype_fid", "genotype_sample_id"]
                    ],
                    on="donor_id",
                    how="left",
                    validate="one_to_one",
                )
                donor_crosswalk["genotype_fid"] = donor_crosswalk[
                    "genotype_fid"
                ].fillna("0")
                donor_crosswalk["matched_genotype"] = donor_crosswalk[
                    "genotype_sample_id"
                ].notna()
        crosswalk_permissions_ok = crosswalk_path.stat().st_mode & 0o077 == 0
        artifacts.append(crosswalk_path)

    checks.append(
        (
            "protected_crosswalk_frozen",
            crosswalk_sha256 == str(identity["genotype_crosswalk_sha256"]),
            crosswalk_sha256,
            identity["genotype_crosswalk_sha256"],
            provenance_path(crosswalk_path, project_root),
        )
    )
    checks.append(
        (
            "genotype_expression_crosswalk_valid",
            crosswalk_ok,
            int(donor_crosswalk["matched_genotype"].sum()),
            f"{identity['genotype_primary_samples']} exact unique matches",
            provenance_path(crosswalk_path, project_root),
        )
    )
    checks.append(
        (
            "protected_crosswalk_permissions",
            crosswalk_permissions_ok,
            oct(crosswalk_path.stat().st_mode & 0o777) if crosswalk_path.exists() else "missing",
            "no group/other permissions",
            provenance_path(crosswalk_path, project_root),
        )
    )

    crosswalk_output = output / "donor_crosswalk.tsv"
    atomic_write_tsv(donor_crosswalk, crosswalk_output)
    artifacts.append(crosswalk_output)

    keep = donor_crosswalk.loc[
        donor_crosswalk["matched_genotype"],
        ["genotype_fid", "genotype_sample_id"],
    ].rename(
        columns={"genotype_fid": "#FID", "genotype_sample_id": "IID"}
    )
    keep_path = output / "array_keep.tsv"
    atomic_write_tsv(keep, keep_path)
    artifacts.append(keep_path)

    sex_codes = {"male": "1", "female": "2"}
    sex_update = donor_crosswalk.loc[
        donor_crosswalk["matched_genotype"],
        ["genotype_fid", "genotype_sample_id", "sex"],
    ].copy()
    sex_update["SEX"] = sex_update["sex"].astype(str).str.lower().map(sex_codes)
    sex_update = sex_update.rename(
        columns={"genotype_fid": "#FID", "genotype_sample_id": "IID"}
    )[["#FID", "IID", "SEX"]]
    sex_path = output / "array_sex.tsv"
    atomic_write_tsv(sex_update, sex_path)
    artifacts.append(sex_path)
    checks.append(
        (
            "genotype_sex_update_complete",
            len(sex_update) == expected_donors and not sex_update["SEX"].isna().any(),
            int(sex_update["SEX"].notna().sum()),
            expected_donors,
            "",
        )
    )


    encode_path = configured_path(
        project_root, config["inputs"]["encode_tf_targets"], must_exist=False
    )
    encode_contract = config["encode"]
    encode_observed = "missing"
    encode_frozen = False
    if encode_path.exists() and encode_path.is_file():
        artifacts.append(encode_path)
        try:
            encode_table = pd.read_csv(encode_path, sep="\t", dtype=str)
            required_columns = ["parent", "child", "source", "release"]
            encode_sha256 = sha256_file(encode_path)
            schema_ok = list(encode_table.columns) == required_columns
            content_ok = (
                schema_ok
                and len(encode_table) == int(encode_contract["output_edges"])
                and encode_table[["parent", "child"]].notna().all().all()
                and not encode_table.duplicated(["parent", "child"]).any()
                and not encode_table["parent"].eq(encode_table["child"]).any()
                and encode_table["source"].eq("ENCODE").all()
                and encode_table["release"].eq(str(encode_contract["release"])).all()
                and encode_table[["parent", "child"]].values.tolist()
                == encode_table.sort_values(["parent", "child"])[
                    ["parent", "child"]
                ].values.tolist()
                and encode_table["parent"].nunique()
                == int(encode_contract["output_unique_tfs"])
                and encode_table["child"].nunique()
                == int(encode_contract["output_unique_targets"])
            )
            encode_frozen = (
                content_ok
                and encode_path.stat().st_size == int(encode_contract["output_bytes"])
                and encode_sha256 == str(encode_contract["output_sha256"])
                and "TO_BE_FROZEN" not in str(encode_contract["release"])
            )
            encode_observed = (
                f"rows={len(encode_table)};bytes={encode_path.stat().st_size};"
                f"sha256={encode_sha256}"
            )
        except (OSError, ValueError, KeyError, pd.errors.ParserError) as error:
            encode_observed = f"invalid:{type(error).__name__}"
    checks.append(
        (
            "encode_tf_targets_present_and_frozen",
            encode_frozen,
            encode_observed,
            (
                f"rows={encode_contract['output_edges']};"
                f"bytes={encode_contract['output_bytes']};"
                f"sha256={encode_contract['output_sha256']}"
            ),
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
        matched_genotype_donors=int(donor_crosswalk["matched_genotype"].sum()),
    )
    print(f"VH11A status: {state}; failed={len(failed)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
