#!/usr/bin/env python3
"""VH09: freeze ROSMAP Phase 18 candidate units for SEA-AD validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_output_dir,
    repo_path,
    require_validated_status,
    sha256_file,
    status_frame,
    utc_now,
)


UNIT_FIELDS = [
    "broad_network",
    "key_driver",
    "case_id",
    "case_label",
    "is_core_mito",
    "mito_tier",
    "coverage_fraction",
    "conservative_support_count",
    "supporting_fine_cell_type_count",
    "supporting_fine_cell_types",
    "supporting_group_count",
    "supporting_groups",
    "supporting_direction_count",
    "supporting_directions",
    "aggregate_acat_p",
    "aggregate_acat_q",
    "terminal_candidate_status",
    "within_case_rank",
    "top5_display",
    "stability_assessable_repetitions",
    "stability_nominal_fraction",
    "stability_q_fraction",
    "stability_candidate_fraction",
    "stability_worst_rank",
    "evidence_tier",
    "case_driver_candidate_count",
    "case_displayed_candidate_count",
]

CONTRAST_FIELDS = [
    "slot",
    "contrast_id",
    "context",
    "contrast_family",
    "sex",
    "apoe_group",
    "contrast_name",
    "eligibility_status",
    "ineligibility_reason",
    "dementia_donors",
    "no_dementia_donors",
]


def is_true(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().isin({"TRUE", "T", "1", "YES"})


def require_columns(frame: pd.DataFrame, required: list[str], label: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def artifact_row(role: str, path: Path, project_root: Path) -> dict[str, Any]:
    return {
        "artifact_role": role,
        "artifact": path.name,
        "path": str(path.resolve(strict=True).relative_to(project_root)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def main() -> int:
    args = parse_config_cli("VH09: freeze ROSMAP Phase 18 candidates for SEA-AD validation")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    if config.get("schema_version") != "seaad_phase18_validation_config_v1":
        raise ValueError("Unexpected VH09 configuration schema")

    input_paths = {
        name: repo_path(project_root, value)
        for name, value in config["inputs"].items()
    }
    observed_hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    expected_hashes = config["expected_sha256"]
    hash_mismatches = [
        name
        for name, observed in observed_hashes.items()
        if observed != str(expected_hashes.get(name, ""))
    ]
    if hash_mismatches:
        raise ValueError(
            "VH09 frozen input checksum mismatch: " + ", ".join(hash_mismatches)
        )

    require_validated_status(input_paths["vh08_status"])
    rules = config["rules"]
    expected = config["expected"]
    output_dir = phase_output_dir(output_root, config["outputs"]["phase_directory"])

    phase18 = pd.read_csv(
        input_paths["phase18_returns"],
        sep="	",
        usecols=UNIT_FIELDS,
        dtype=str,
        keep_default_na=False,
    )
    require_columns(phase18, UNIT_FIELDS, "Phase 18 returns")
    key = list(rules["candidate_key"])
    grouped = phase18.groupby(key, sort=False, dropna=False)
    constant_counts = grouped[UNIT_FIELDS].nunique(dropna=False)
    unit_fields_constant = not bool((constant_counts > 1).any(axis=1).any())
    units = grouped.first().reset_index()
    units["candidate_unit_id"] = units[key].astype(str).agg("|".join, axis=1)

    passing = units.loc[
        units["terminal_candidate_status"].eq(rules["passing_status"])
    ].copy()
    selected = passing.loc[is_true(passing[rules["selected_flag"]])].copy()

    network_order = {
        value: index for index, value in enumerate(rules["broad_network_order"])
    }
    class_order = {
        value: index for index, value in enumerate(rules["driver_class_order"])
    }
    for frame in (passing, selected):
        frame["_network_order"] = frame["broad_network"].map(network_order)
        frame["_class_order"] = frame["case_id"].map(class_order)
        frame["_rank"] = pd.to_numeric(frame["within_case_rank"], errors="coerce")
        frame.sort_values(
            ["_network_order", "_class_order", "_rank", "key_driver"],
            inplace=True,
        )
        frame.drop(
            columns=["_network_order", "_class_order", "_rank"], inplace=True
        )

    phase18_sha = observed_hashes["phase18_returns"]
    unit_output_columns = [
        "schema_version",
        "candidate_unit_id",
        *UNIT_FIELDS,
        "phase18_source_sha256",
    ]
    for frame, schema in (
        (passing, "seaad_phase18_passing_candidate_unit_v1"),
        (selected, "seaad_phase18_selected_candidate_unit_v1"),
    ):
        frame.insert(0, "schema_version", schema)
        frame["phase18_source_sha256"] = phase18_sha
        frame.reset_index(drop=True, inplace=True)

    gene_rows = []
    for gene, rows in selected.groupby("key_driver", sort=True):
        case_ids = sorted(rows["case_id"].unique())
        labels = sorted(rows["case_label"].unique())
        core_values = sorted(rows["is_core_mito"].unique())
        tiers = sorted(rows["mito_tier"].unique())
        gene_rows.append(
            {
                "schema_version": "seaad_phase18_selected_gene_v1",
                "key_driver": gene,
                "case_id": case_ids[0] if len(case_ids) == 1 else "CONFLICT",
                "case_label": labels[0] if len(labels) == 1 else "CONFLICT",
                "is_core_mito": (
                    core_values[0] if len(core_values) == 1 else "CONFLICT"
                ),
                "mito_tier": tiers[0] if len(tiers) == 1 else "CONFLICT",
                "selected_network_count": rows["broad_network"].nunique(),
                "selected_networks": "|".join(
                    value
                    for value in rules["broad_network_order"]
                    if value in set(rows["broad_network"])
                ),
                "selected_candidate_unit_count": len(rows),
                "phase18_source_sha256": phase18_sha,
            }
        )
    selected_genes = pd.DataFrame(gene_rows)

    direction_rows = []
    direction_order = list(rules["direction_order"])
    direction_map = dict(rules["direction_map"])
    selected_direction_count_matches = True
    for row in selected.itertuples(index=False):
        observed = {
            value for value in row.supporting_directions.split("|") if value
        }
        selected_direction_count_matches &= (
            len(observed) == int(row.supporting_direction_count)
        )
        for direction in direction_order:
            if direction not in observed:
                continue
            direction_rows.append(
                {
                    "schema_version": "seaad_phase18_selected_direction_v1",
                    "candidate_direction_id": (
                        f"{row.candidate_unit_id}|{direction}"
                    ),
                    "candidate_unit_id": row.candidate_unit_id,
                    "broad_network": row.broad_network,
                    "key_driver": row.key_driver,
                    "case_id": row.case_id,
                    "case_label": row.case_label,
                    "phase18_within_case_rank": row.within_case_rank,
                    "phase18_direction": direction,
                    "seaad_direction": direction_map[direction],
                    "phase18_source_sha256": phase18_sha,
                }
            )
    selected_directions = pd.DataFrame(direction_rows)

    contrast_manifest = pd.read_csv(
        input_paths["seaad_contrast_manifest"],
        sep="	",
        dtype=str,
        keep_default_na=False,
    )
    require_columns(
        contrast_manifest, CONTRAST_FIELDS, "SEA-AD contrast manifest"
    )
    contrast_manifest = contrast_manifest[CONTRAST_FIELDS].copy()
    validation = selected_directions.merge(
        contrast_manifest,
        left_on="broad_network",
        right_on="context",
        how="left",
        validate="many_to_many",
    )
    validation["validation_tier"] = validation["contrast_family"].map(
        {
            "primary": "primary_confirmatory",
            "secondary": "secondary_supportive",
        }
    )
    validation["planning_status"] = validation["eligibility_status"].map(
        {
            "eligible": "planned_scoring",
            "not_estimable": "contrast_not_estimable",
        }
    )
    validation["validation_test_id"] = (
        validation["candidate_direction_id"] + "|" + validation["contrast_id"]
    )
    validation["schema_version"] = (
        "seaad_phase18_candidate_validation_plan_v1"
    )
    validation_columns = [
        "schema_version",
        "validation_test_id",
        "candidate_direction_id",
        "candidate_unit_id",
        "broad_network",
        "key_driver",
        "case_id",
        "case_label",
        "phase18_within_case_rank",
        "phase18_direction",
        "seaad_direction",
        "validation_tier",
        "planning_status",
        *CONTRAST_FIELDS,
        "phase18_source_sha256",
    ]
    validation = validation[validation_columns].copy()
    validation["_network_order"] = validation["broad_network"].map(network_order)
    validation["_class_order"] = validation["case_id"].map(class_order)
    validation["_rank"] = pd.to_numeric(
        validation["phase18_within_case_rank"]
    )
    validation["_direction_order"] = validation["phase18_direction"].map(
        {value: index for index, value in enumerate(direction_order)}
    )
    validation["_slot"] = pd.to_numeric(validation["slot"])
    validation.sort_values(
        [
            "_network_order",
            "_class_order",
            "_rank",
            "_direction_order",
            "_slot",
        ],
        inplace=True,
    )
    validation.drop(
        columns=[
            "_network_order",
            "_class_order",
            "_rank",
            "_direction_order",
            "_slot",
        ],
        inplace=True,
    )
    validation.reset_index(drop=True, inplace=True)

    selected_rank_contiguous = all(
        sorted(pd.to_numeric(rows["within_case_rank"]).astype(int).tolist())
        == list(range(1, len(rows) + 1))
        for _, rows in selected.groupby(["broad_network", "case_id"])
    )
    class_consistent = bool(
        (
            selected["case_id"].eq("mt_driver")
            == is_true(selected["is_core_mito"])
        ).all()
    )
    primary = contrast_manifest.loc[
        contrast_manifest["contrast_family"].eq("primary")
    ]
    secondary = contrast_manifest.loc[
        contrast_manifest["contrast_family"].eq("secondary")
    ]
    checks = [
        (
            "frozen_input_hashes",
            not hash_mismatches,
            ";".join(hash_mismatches),
            "all_match",
            "",
        ),
        (
            "candidate_unit_fields_constant",
            unit_fields_constant,
            unit_fields_constant,
            True,
            "within broad_network + key_driver + case_id",
        ),
        (
            "phase18_candidate_units",
            len(units) == expected["phase18_candidate_units"],
            len(units),
            expected["phase18_candidate_units"],
            "",
        ),
        (
            "phase18_passing_units",
            len(passing) == expected["phase18_passing_units"],
            len(passing),
            expected["phase18_passing_units"],
            "terminal_candidate_status == driver_candidate",
        ),
        (
            "phase18_selected_units",
            len(selected) == expected["phase18_selected_units"],
            len(selected),
            expected["phase18_selected_units"],
            "top5_display == TRUE among passing units",
        ),
        (
            "phase18_selected_genes",
            len(selected_genes) == expected["phase18_selected_genes"],
            len(selected_genes),
            expected["phase18_selected_genes"],
            "",
        ),
        (
            "selected_candidate_keys_unique",
            selected["candidate_unit_id"].is_unique,
            selected["candidate_unit_id"].nunique(),
            len(selected),
            "",
        ),
        (
            "selected_units_are_passing",
            selected["terminal_candidate_status"]
            .eq(rules["passing_status"])
            .all(),
            "|".join(sorted(selected["terminal_candidate_status"].unique())),
            rules["passing_status"],
            "",
        ),
        (
            "selected_class_consistent",
            class_consistent,
            class_consistent,
            True,
            "mt_driver iff is_core_mito",
        ),
        (
            "selected_ranks_contiguous",
            selected_rank_contiguous,
            selected_rank_contiguous,
            True,
            "within broad network and driver class",
        ),
        (
            "selected_broad_networks",
            selected["broad_network"].nunique()
            == expected["selected_broad_networks"],
            selected["broad_network"].nunique(),
            expected["selected_broad_networks"],
            "",
        ),
        (
            "selected_network_set_matches_seaad",
            set(selected["broad_network"])
            == set(rules["broad_network_order"]),
            "|".join(sorted(selected["broad_network"].unique())),
            "|".join(sorted(rules["broad_network_order"])),
            "",
        ),
        (
            "selected_direction_counts_match",
            selected_direction_count_matches,
            selected_direction_count_matches,
            True,
            "stored supporting_direction_count equals parsed directions",
        ),
        (
            "selected_direction_units",
            len(selected_directions) == expected["selected_direction_units"],
            len(selected_directions),
            expected["selected_direction_units"],
            "",
        ),
        (
            "selected_direction_keys_unique",
            selected_directions["candidate_direction_id"].is_unique,
            selected_directions["candidate_direction_id"].nunique(),
            len(selected_directions),
            "",
        ),
        (
            "seaad_primary_contrasts",
            len(primary) == expected["seaad_primary_contrasts"],
            len(primary),
            expected["seaad_primary_contrasts"],
            "",
        ),
        (
            "seaad_primary_all_eligible",
            primary["eligibility_status"].eq("eligible").all(),
            int(primary["eligibility_status"].eq("eligible").sum()),
            len(primary),
            "",
        ),
        (
            "seaad_secondary_slots",
            len(secondary) == expected["seaad_secondary_slots"],
            len(secondary),
            expected["seaad_secondary_slots"],
            "",
        ),
        (
            "seaad_secondary_eligible",
            int(secondary["eligibility_status"].eq("eligible").sum())
            == expected["seaad_secondary_eligible"],
            int(secondary["eligibility_status"].eq("eligible").sum()),
            expected["seaad_secondary_eligible"],
            "",
        ),
        (
            "seaad_secondary_not_estimable",
            int(secondary["eligibility_status"].eq("not_estimable").sum())
            == expected["seaad_secondary_not_estimable"],
            int(secondary["eligibility_status"].eq("not_estimable").sum()),
            expected["seaad_secondary_not_estimable"],
            "",
        ),
        (
            "validation_manifest_rows",
            len(validation) == expected["validation_manifest_rows"],
            len(validation),
            expected["validation_manifest_rows"],
            "",
        ),
        (
            "validation_test_ids_unique",
            validation["validation_test_id"].is_unique,
            validation["validation_test_id"].nunique(),
            len(validation),
            "",
        ),
        (
            "planned_scoring_rows",
            int(validation["planning_status"].eq("planned_scoring").sum())
            == expected["planned_scoring_rows"],
            int(validation["planning_status"].eq("planned_scoring").sum()),
            expected["planned_scoring_rows"],
            "",
        ),
        (
            "contrast_not_estimable_rows",
            int(
                validation["planning_status"]
                .eq("contrast_not_estimable")
                .sum()
            )
            == expected["contrast_not_estimable_rows"],
            int(
                validation["planning_status"]
                .eq("contrast_not_estimable")
                .sum()
            ),
            expected["contrast_not_estimable_rows"],
            "",
        ),
        (
            "seven_contrast_slots_per_direction",
            validation.groupby("candidate_direction_id")["contrast_id"]
            .nunique()
            .eq(7)
            .all(),
            int(
                validation.groupby("candidate_direction_id")["contrast_id"]
                .nunique()
                .min()
            ),
            7,
            "one primary plus six secondary slots",
        ),
    ]
    checks_table = checks_frame(checks)

    paths = {
        "passing": output_dir / "phase18_passing_candidate_units.tsv",
        "selected": output_dir / "phase18_selected_candidate_units.tsv",
        "genes": output_dir / "phase18_selected_genes.tsv",
        "directions": output_dir / "phase18_selected_directions.tsv",
        "plan": output_dir / "seaad_candidate_validation_manifest.tsv",
        "checks": output_dir / "candidate_freeze_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(passing[unit_output_columns], paths["passing"])
    atomic_write_tsv(selected[unit_output_columns], paths["selected"])
    atomic_write_tsv(selected_genes, paths["genes"])
    atomic_write_tsv(selected_directions, paths["directions"])
    atomic_write_tsv(validation, paths["plan"])
    atomic_write_tsv(checks_table, paths["checks"])

    artifact_records = [
        artifact_row("input", input_paths[name], project_root)
        for name in input_paths
    ]
    artifact_records.extend(
        [
            artifact_row("config", config_path, project_root),
            artifact_row(
                "code", Path(__file__).resolve(strict=True), project_root
            ),
        ]
    )
    artifact_records.extend(
        artifact_row(
            "result" if name != "checks" else "checks",
            paths[name],
            project_root,
        )
        for name in [
            "passing",
            "selected",
            "genes",
            "directions",
            "plan",
            "checks",
        ]
    )
    artifacts = pd.DataFrame(artifact_records)
    atomic_write_tsv(artifacts, paths["artifacts"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH09",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        phase18_candidate_units=len(units),
        phase18_passing_units=len(passing),
        phase18_selected_units=len(selected),
        phase18_selected_genes=len(selected_genes),
        selected_broad_networks=selected["broad_network"].nunique(),
        selected_direction_units=len(selected_directions),
        validation_manifest_rows=len(validation),
        planned_scoring_rows=int(
            validation["planning_status"].eq("planned_scoring").sum()
        ),
        contrast_not_estimable_rows=int(
            validation["planning_status"]
            .eq("contrast_not_estimable")
            .sum()
        ),
        phase18_returns_sha256=phase18_sha,
        selected_units_sha256=sha256_file(paths["selected"]),
        validation_manifest_sha256=sha256_file(paths["plan"]),
        vh08_status_sha256=observed_hashes["vh08_status"],
    )
    atomic_write_tsv(status, paths["status"])
    print(
        f"VH09 status: {validation_status}; selected units: {len(selected)}; "
        f"genes: {len(selected_genes)}; validation rows: {len(validation)}"
    )
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
