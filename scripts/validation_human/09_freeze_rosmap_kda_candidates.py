#!/usr/bin/env python3
"""VH09: freeze canonical ROSMAP Phase 18 candidate units for SEA-AD validation."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    git_revision,
    load_config,
    parse_config_cli,
    repo_path,
    sha256_file,
    status_frame,
    utc_now,
    write_artifacts,
)


KEY = ["broad_network", "key_driver", "case_id"]
EVIDENCE = [
    "coverage_fraction",
    "conservative_support_count",
    "aggregate_acat_p",
    "aggregate_acat_q",
    "terminal_candidate_status",
    "within_case_rank",
    "top5_display",
]
REQUIRED = ["kda_run_id", *KEY, *EVIDENCE]


def truth(value) -> bool:
    return str(value).strip().lower() in {"true", "t", "1", "yes"}


def main() -> int:
    args = parse_config_cli("VH09: freeze ROSMAP Phase 18 candidate units")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    cfg = config["vh09"]
    expected = cfg["expected"]

    authority_rows = []
    authority_paths = {}
    for item in cfg["authority"]:
        path = repo_path(project_root, item["path"])
        observed = sha256_file(path)
        if observed != item["sha256"]:
            raise ValueError(f"Authority checksum mismatch for {item['role']}: {path}")
        authority_paths[item["role"]] = path
        authority_rows.append(
            {
                "role": item["role"],
                "path": str(path.relative_to(project_root)),
                "bytes": path.stat().st_size,
                "sha256": observed,
            }
        )

    vh08 = pd.read_csv(authority_paths["vh08_status"], sep="\t", keep_default_na=False)
    if len(vh08) != 1 or vh08.loc[0, "validation_status"] != "validated_complete":
        raise ValueError("VH08 is not validated_complete")

    returns_path = authority_paths["phase18_call_returns"]
    table = pd.read_csv(
        returns_path,
        sep="\t",
        usecols=REQUIRED,
        keep_default_na=False,
        low_memory=False,
    )
    table["top5_display_bool"] = table["top5_display"].map(truth)

    unit_variation = (
        table.groupby(KEY, sort=False, dropna=False)[EVIDENCE]
        .nunique(dropna=False)
    )
    varying = unit_variation.gt(1).any(axis=1)
    if varying.any():
        raise ValueError(f"Selection fields vary within {int(varying.sum())} candidate units")

    units = table.drop_duplicates(KEY, keep="first").copy()
    units["top5_display"] = units["top5_display_bool"]
    units = units.drop(columns=["top5_display_bool"])
    passing = units.loc[
        units["terminal_candidate_status"].eq("driver_candidate")
    ].copy()
    selected = units.loc[units["top5_display"]].copy()
    selected_genes = (
        selected.groupby("key_driver", sort=True)
        .agg(
            selected_unit_count=("key_driver", "size"),
            broad_network_memberships=(
                "broad_network",
                lambda values: "|".join(sorted(set(values))),
            ),
            driver_class_memberships=(
                "case_id",
                lambda values: "|".join(sorted(set(values))),
            ),
        )
        .reset_index()
    )

    mapping = pd.read_csv(
        authority_paths["supertype_network_map"], sep="\t", keep_default_na=False
    )
    seaad_networks = sorted(set(mapping["broad_network"]))
    expected_networks = list(expected["broad_networks"])
    selected_networks = sorted(set(selected["broad_network"]))

    rank_numeric = pd.to_numeric(selected["within_case_rank"], errors="coerce")
    selected_rank_keys_unique = not selected.duplicated(
        ["broad_network", "case_id", "within_case_rank"]
    ).any()
    explicit_keys = table[["kda_run_id", "key_driver"]]
    classes = sorted(set(units["case_id"]))

    checks = checks_frame(
        [
            ("vh08_validated_complete", True, vh08.loc[0, "validation_status"], "validated_complete", ""),
            ("explicit_row_count", len(table) == expected["explicit_rows"], len(table), expected["explicit_rows"], ""),
            (
                "explicit_run_gene_keys_unique",
                not explicit_keys.duplicated().any()
                and len(explicit_keys) == expected["explicit_run_gene_keys"],
                len(explicit_keys.drop_duplicates()),
                expected["explicit_run_gene_keys"],
                "",
            ),
            ("candidate_unit_count", len(units) == expected["candidate_units"], len(units), expected["candidate_units"], ""),
            ("candidate_fields_constant", not varying.any(), int(varying.sum()), 0, ""),
            ("passing_unit_count", len(passing) == expected["passing_units"], len(passing), expected["passing_units"], ""),
            ("selected_unit_count", len(selected) == expected["selected_units"], len(selected), expected["selected_units"], ""),
            (
                "selected_unique_gene_count",
                len(selected_genes) == expected["selected_unique_genes"],
                len(selected_genes),
                expected["selected_unique_genes"],
                "",
            ),
            ("driver_classes_exact", classes == sorted(expected["driver_classes"]), "|".join(classes), "|".join(sorted(expected["driver_classes"])), ""),
            ("selected_units_are_passing", selected["terminal_candidate_status"].eq("driver_candidate").all(), True, True, ""),
            ("selected_ranks_in_top5", rank_numeric.notna().all() and rank_numeric.between(1, 5).all(), f"{rank_numeric.min()}-{rank_numeric.max()}", "1-5", ""),
            ("selected_rank_keys_unique", selected_rank_keys_unique, selected_rank_keys_unique, True, ""),
            ("seaad_network_scope_exact", seaad_networks == sorted(expected_networks), "|".join(seaad_networks), "|".join(sorted(expected_networks)), ""),
            ("selected_network_scope_exact", selected_networks == sorted(expected_networks), "|".join(selected_networks), "|".join(sorted(expected_networks)), ""),
        ]
    )
    if not checks["passed"].all():
        failed = checks.loc[~checks["passed"], "check"].tolist()
        raise ValueError(f"VH09 blocking checks failed: {failed}")

    count_rows = []
    for network in expected_networks:
        for case_id in expected["driver_classes"]:
            subset = units.loc[
                units["broad_network"].eq(network) & units["case_id"].eq(case_id)
            ]
            count_rows.append(
                {
                    "broad_network": network,
                    "case_id": case_id,
                    "explicit_candidate_units": len(subset),
                    "passing_candidate_units": int(
                        subset["terminal_candidate_status"].eq("driver_candidate").sum()
                    ),
                    "selected_top5_units": int(subset["top5_display"].sum()),
                }
            )
    counts = pd.DataFrame(count_rows)
    scope = pd.DataFrame(
        {
            "phase18_broad_network": expected_networks,
            "seaad_broad_network": expected_networks,
            "identity_status": "exact_shared_machine_id",
            "selected_phase18_units": [
                int(selected["broad_network"].eq(network).sum())
                for network in expected_networks
            ],
        }
    )

    authority = pd.DataFrame(authority_rows)
    authority = pd.concat(
        [
            authority,
            pd.DataFrame(
                [
                    {
                        "role": "vh09_code",
                        "path": str(Path(__file__).resolve().relative_to(project_root)),
                        "bytes": Path(__file__).stat().st_size,
                        "sha256": sha256_file(__file__),
                    },
                    {
                        "role": "validation_config",
                        "path": str(config_path.relative_to(project_root)),
                        "bytes": config_path.stat().st_size,
                        "sha256": sha256_file(config_path),
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    final_dir = output_root / cfg["output_directory"]
    if final_dir.exists() and any(final_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty VH09 directory: {final_dir}")
    stage = output_root / f".{cfg['output_directory']}.tmp.{os.getpid()}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    outputs = {
        "selected": stage / "phase18_selected_candidate_units.tsv",
        "passing": stage / "phase18_passing_candidate_units.tsv",
        "genes": stage / "phase18_selected_genes.tsv",
        "counts": stage / "phase18_candidate_unit_counts.tsv",
        "scope": stage / "shared_network_scope.tsv",
        "authority": stage / "phase18_selection_authority.tsv",
        "checks": stage / "candidate_freeze_checks.tsv",
    }
    columns = [*KEY, *EVIDENCE]
    atomic_write_tsv(selected[columns].sort_values(["broad_network", "case_id", "within_case_rank"]), outputs["selected"])
    atomic_write_tsv(passing[columns].sort_values(["broad_network", "case_id", "within_case_rank"]), outputs["passing"])
    atomic_write_tsv(selected_genes, outputs["genes"])
    atomic_write_tsv(counts, outputs["counts"])
    atomic_write_tsv(scope, outputs["scope"])
    atomic_write_tsv(authority, outputs["authority"])
    atomic_write_tsv(checks, outputs["checks"])

    if final_dir.exists():
        final_dir.rmdir()
    os.replace(stage, final_dir)
    final_outputs = [final_dir / path.name for path in outputs.values()]
    artifacts = write_artifacts(final_outputs, project_root, final_dir / "artifacts.tsv")
    selected_path = final_dir / outputs["selected"].name
    passing_path = final_dir / outputs["passing"].name
    status = status_frame(
        "VH09",
        "validated_complete",
        project_root,
        config_path,
        started,
        explicit_rows=len(table),
        candidate_units=len(units),
        passing_units=len(passing),
        selected_units=len(selected),
        selected_unique_genes=len(selected_genes),
        selected_sha256=sha256_file(selected_path),
        passing_sha256=sha256_file(passing_path),
        artifact_count=len(artifacts),
    )
    atomic_write_tsv(status, final_dir / "status.tsv")
    print(f"VH09 validated_complete: {final_dir}")
    print(f"selected_units={len(selected)} passing_units={len(passing)} unique_genes={len(selected_genes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
