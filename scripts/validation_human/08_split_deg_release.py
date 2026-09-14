#!/usr/bin/env python3
"""Losslessly split the validated unified VH08 DEG release by resolution."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    sha256_file,
    utc_now,
)


OLD_RELEASE_NAME = "08_deg"
FINE_RELEASE_NAME = "08_deg_fine"
BROAD_RELEASE_NAME = "08_deg_broad"


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split the validated SEA-AD VH08 DEG release"
    )
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", keep_default_na=False)


def rewrite_prefix(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    rewritten = text.replace(old, new)
    if old in rewritten:
        raise ValueError(f"Old release prefix remains in {path}")
    if text == rewritten:
        return
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(rewritten, encoding="utf-8")
    os.replace(temporary, path)


def validate_manifest(source_root: Path, project_root: Path) -> pd.DataFrame:
    status = read_table(source_root / "status.tsv")
    if (
        len(status) != 1
        or status.loc[0, "validation_status"] != "validated_complete"
    ):
        raise ValueError("Unified VH08 source is not validated_complete")
    artifacts = read_table(source_root / "artifacts.tsv")
    for row in artifacts.itertuples(index=False):
        path = project_root / row.path
        if (
            not path.is_file()
            or path.stat().st_size != int(row.bytes)
            or sha256_file(path) != row.digest_value
        ):
            raise ValueError(f"Unified VH08 artifact mismatch: {path}")
    return status


def move_subtree(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing migration source: {source}")
    if destination.exists():
        raise FileExistsError(f"Migration target already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def inherited_check(old_checks: pd.DataFrame, check: str) -> bool:
    row = old_checks.loc[old_checks["check"].eq(check), "passed"]
    if len(row) != 1:
        raise ValueError(f"Missing inherited runner check: {check}")
    return bool(row.iloc[0])


def write_runner_records(
    source_root: Path,
    fine_root: Path,
    broad_root: Path,
    config_sha256: str,
) -> None:
    old_status = read_table(source_root / "run_status.tsv")
    old_checks = pd.read_csv(source_root / "run_checks.tsv", sep="\t")
    diagnostics = pd.read_csv(
        source_root / "run_model_diagnostics.tsv.gz", sep="\t"
    )
    fine_status = read_table(
        fine_root
        / "fine_supertype_phase18_parity"
        / "fine_contrast_status.tsv"
    )
    pooled_status = read_table(
        broad_root / "broad_pooled_anchor/contrast_status.tsv"
    )
    broad_status = read_table(
        broad_root / "broad_stratified_support/contrast_status.tsv"
    )
    broad_all = pd.concat([pooled_status, broad_status], ignore_index=True)

    fine_paths = [
        Path(value)
        for value in fine_status.loc[
            fine_status["terminal_status"].eq("completed"), "result_path"
        ]
    ]
    broad_paths = [
        Path(value)
        for value in broad_all.loc[
            broad_all["terminal_status"].eq("completed"), "result_path"
        ]
    ]
    project_root = fine_root.parents[2]
    fine_exist = sum((project_root / path).is_file() for path in fine_paths)
    broad_exist = sum((project_root / path).is_file() for path in broad_paths)

    fine_checks = checks_frame(
        [
            ("fine_status_rows", len(fine_status) == 774, len(fine_status), 774, ""),
            (
                "no_failed_contrasts",
                not fine_status["terminal_status"].eq("failed").any(),
                int(fine_status["terminal_status"].eq("failed").sum()),
                0,
                "",
            ),
            (
                "eligible_fine_terminal",
                fine_status.loc[
                    fine_status["eligibility_status"].eq("eligible"),
                    "terminal_status",
                ]
                .isin(["completed", "not_estimable"])
                .all(),
                True,
                True,
                "",
            ),
            (
                "statistics_finite",
                inherited_check(old_checks, "statistics_finite"),
                True,
                True,
                "inherited from byte-identical unified release",
            ),
            (
                "BH_reproduced",
                inherited_check(old_checks, "BH_reproduced"),
                True,
                True,
                "inherited from byte-identical unified release",
            ),
            (
                "sample_replay_reproduced",
                inherited_check(old_checks, "sample_replay_reproduced"),
                True,
                True,
                "inherited from byte-identical unified release",
            ),
            (
                "result_files_exist",
                fine_exist == len(fine_paths),
                fine_exist,
                len(fine_paths),
                "",
            ),
        ]
    )
    broad_checks = checks_frame(
        [
            ("pooled_status_rows", len(pooled_status) == 7, len(pooled_status), 7, ""),
            ("broad_status_rows", len(broad_status) == 42, len(broad_status), 42, ""),
            (
                "no_failed_contrasts",
                not broad_all["terminal_status"].eq("failed").any(),
                int(broad_all["terminal_status"].eq("failed").sum()),
                0,
                "",
            ),
            (
                "eligible_pooled_terminal",
                pooled_status.loc[
                    pooled_status["eligibility_status"].eq("eligible"),
                    "terminal_status",
                ]
                .isin(["completed", "not_estimable"])
                .all(),
                True,
                True,
                "",
            ),
            (
                "eligible_broad_terminal",
                broad_status.loc[
                    broad_status["eligibility_status"].eq("eligible"),
                    "terminal_status",
                ]
                .isin(["completed", "not_estimable"])
                .all(),
                True,
                True,
                "",
            ),
            (
                "statistics_finite",
                inherited_check(old_checks, "statistics_finite"),
                True,
                True,
                "inherited from byte-identical unified release",
            ),
            (
                "BH_reproduced",
                inherited_check(old_checks, "BH_reproduced"),
                True,
                True,
                "inherited from byte-identical unified release",
            ),
            (
                "sample_replay_reproduced",
                diagnostics.loc[
                    diagnostics["deg_tier"].isin(
                        ["broad_pooled_anchor", "broad_stratified_support"]
                    ),
                    "replay_reproduced",
                ]
                .astype(bool)
                .all(),
                True,
                True,
                "",
            ),
            (
                "result_files_exist",
                broad_exist == len(broad_paths),
                broad_exist,
                len(broad_paths),
                "",
            ),
        ]
    )
    if not fine_checks["passed"].all() or not broad_checks["passed"].all():
        raise ValueError("Split runner validation failed")

    fine_diagnostics = diagnostics.loc[
        diagnostics["deg_tier"].eq("fine_supertype_phase18_parity")
    ].copy()
    broad_diagnostics = diagnostics.loc[
        diagnostics["deg_tier"].isin(
            ["broad_pooled_anchor", "broad_stratified_support"]
        )
    ].copy()
    atomic_write_tsv(fine_checks, fine_root / "run_checks.tsv")
    atomic_write_tsv(broad_checks, broad_root / "run_checks.tsv")
    atomic_write_tsv(
        fine_diagnostics, fine_root / "run_model_diagnostics.tsv.gz"
    )
    atomic_write_tsv(
        broad_diagnostics, broad_root / "run_model_diagnostics.tsv.gz"
    )

    common = {
        "started_at_utc": old_status.loc[0, "started_at_utc"],
        "completed_at_utc": old_status.loc[0, "completed_at_utc"],
        "config_sha256": config_sha256,
    }
    fine_run_status = pd.DataFrame(
        [
            {
                "schema_version": "seaad_deg_fine_run_status_v1",
                "task": "VH08F_edgeR_runner",
                "release_scope": "fine",
                "task_status": "worker_complete",
                "failed_checks": "",
                **common,
                "fine_completed": int(
                    fine_status["terminal_status"].eq("completed").sum()
                ),
                "fine_no_genes_after_filter": int(
                    fine_status["terminal_reason"]
                    .eq("no_genes_after_filterByExpr")
                    .sum()
                ),
                "result_files": len(fine_paths),
            }
        ]
    )
    broad_run_status = pd.DataFrame(
        [
            {
                "schema_version": "seaad_deg_broad_run_status_v1",
                "task": "VH08B_edgeR_runner",
                "release_scope": "broad",
                "task_status": "worker_complete",
                "failed_checks": "",
                **common,
                "pooled_completed": int(
                    pooled_status["terminal_status"].eq("completed").sum()
                ),
                "broad_stratified_completed": int(
                    broad_status["terminal_status"].eq("completed").sum()
                ),
                "result_files": len(broad_paths),
            }
        ]
    )
    atomic_write_tsv(fine_run_status, fine_root / "run_status.tsv")
    atomic_write_tsv(broad_run_status, broad_root / "run_status.tsv")


def main() -> int:
    args = parse_cli()
    _, config_path, project_root, output_root = load_config(args.config)
    source_root = output_root / OLD_RELEASE_NAME
    fine_root = output_root / FINE_RELEASE_NAME
    broad_root = output_root / BROAD_RELEASE_NAME
    if fine_root.exists() or broad_root.exists():
        raise FileExistsError("Split DEG release target already exists")
    source_status = validate_manifest(source_root, project_root)

    fine_root.mkdir()
    broad_root.mkdir()
    move_subtree(
        source_root / "fine_supertype_phase18_parity",
        fine_root / "fine_supertype_phase18_parity",
    )
    move_subtree(source_root / "query_handoff", fine_root / "query_handoff")
    move_subtree(
        source_root / "broad_pooled_anchor",
        broad_root / "broad_pooled_anchor",
    )
    move_subtree(
        source_root / "broad_stratified_support",
        broad_root / "broad_stratified_support",
    )
    move_subtree(
        source_root / "filters" / "broad",
        broad_root / "filters" / "broad",
    )

    old_prefix = f"results/validation_human/{OLD_RELEASE_NAME}/"
    fine_prefix = f"results/validation_human/{FINE_RELEASE_NAME}/"
    broad_prefix = f"results/validation_human/{BROAD_RELEASE_NAME}/"
    for path in fine_root.rglob("*.tsv"):
        rewrite_prefix(path, old_prefix, fine_prefix)
    for path in broad_root.rglob("*.tsv"):
        rewrite_prefix(path, old_prefix, broad_prefix)

    write_runner_records(
        source_root,
        fine_root,
        broad_root,
        source_status.loc[0, "config_sha256"],
    )
    source_record = pd.DataFrame(
        [
            {
                "source_release": "VH08_unified_pre_split",
                "source_status_sha256": sha256_file(source_root / "status.tsv"),
                "source_artifacts_sha256": sha256_file(
                    source_root / "artifacts.tsv"
                ),
                "source_file_count": (
                    len(read_table(source_root / "artifacts.tsv")) + 2
                ),
                "migrated_at_utc": utc_now(),
                "migration_rule": "payload_bytes_preserved_paths_rebound",
            }
        ]
    )
    atomic_write_tsv(source_record, fine_root / "migration_source.tsv")
    atomic_write_tsv(source_record, broad_root / "migration_source.tsv")
    print(
        "VH08 payload split complete; run 08_finalize_deg_release.py "
        "to publish independent release manifests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
