#!/usr/bin/env python3
"""VH08F/VH08B finalizer for independent SEA-AD DEG releases."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_dir,
    require_phase,
    sha256_file,
    status_frame,
    utc_now,
    write_artifacts,
)


FINE_STATUS_SCHEMA = "seaad_deg_fine_status_v1"
BROAD_STATUS_SCHEMA = "seaad_deg_broad_status_v1"


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", keep_default_na=False)


def result_summary(row, project_root: Path, effect_cut: float):
    if row.terminal_status != "completed":
        return {
            "contrast_id": row.contrast_id,
            "deg_tier": row.deg_tier,
            "terminal_status": row.terminal_status,
            "tested_features": pd.NA,
            "fdr_significant": pd.NA,
            "phase18_parity": pd.NA,
            "fdr_up": pd.NA,
            "fdr_down": pd.NA,
            "parity_up": pd.NA,
            "parity_down": pd.NA,
        }, None

    path = project_root / row.result_path
    if sha256_file(path) != row.result_sha256:
        raise ValueError(f"Result checksum mismatch: {path}")
    table = pd.read_csv(path, sep="\t")
    numeric = table[["logFC", "logCPM", "F", "PValue", "FDR"]].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"Nonfinite DEG statistic: {path}")
    if not (
        table["PValue"].between(0, 1) & table["FDR"].between(0, 1)
    ).all():
        raise ValueError(f"Invalid P/FDR range: {path}")
    expected_direction = np.where(
        table["logFC"] > 0,
        "Dementia_up",
        np.where(table["logFC"] < 0, "Dementia_down", "zero"),
    )
    if not np.array_equal(
        table["effect_direction"].to_numpy(), expected_direction
    ):
        raise ValueError(f"Effect direction mismatch: {path}")
    if table["feature_index"].duplicated().any():
        raise ValueError(f"Duplicate tested feature: {path}")

    fdr = table["FDR"] < 0.05
    parity = fdr & (table["logFC"].abs() > effect_cut)
    summary = {
        "contrast_id": row.contrast_id,
        "deg_tier": row.deg_tier,
        "terminal_status": row.terminal_status,
        "tested_features": len(table),
        "fdr_significant": int(fdr.sum()),
        "phase18_parity": int(parity.sum()),
        "fdr_up": int((fdr & table["logFC"].gt(0)).sum()),
        "fdr_down": int((fdr & table["logFC"].lt(0)).sum()),
        "parity_up": int((parity & table["logFC"].gt(0)).sum()),
        "parity_down": int((parity & table["logFC"].lt(0)).sum()),
    }
    return summary, path


def summarize_results(
    status: pd.DataFrame, project_root: Path, effect_cut: float
) -> tuple[pd.DataFrame, list[Path]]:
    summaries = []
    result_paths = []
    for row in status.itertuples(index=False):
        summary, result_path = result_summary(row, project_root, effect_cut)
        summaries.append(summary)
        if result_path is not None:
            result_paths.append(result_path)
        if row.filter_path:
            filter_path = project_root / row.filter_path
            if sha256_file(filter_path) != row.filter_sha256:
                raise ValueError(f"Filter checksum mismatch: {filter_path}")
    return pd.DataFrame(summaries), result_paths


def validate_runner(
    release_root: Path, expected_schema: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    status_path = release_root / "run_status.tsv"
    checks_path = release_root / "run_checks.tsv"
    if not status_path.exists() or not checks_path.exists():
        raise FileNotFoundError(f"Runner records are missing under {release_root}")
    status = read_table(status_path)
    checks = pd.read_csv(checks_path, sep="\t")
    if (
        len(status) != 1
        or status.loc[0, "schema_version"] != expected_schema
        or status.loc[0, "task_status"] != "worker_complete"
    ):
        raise ValueError(f"Runner did not complete for {release_root.name}")
    if not checks["passed"].astype(bool).all():
        raise ValueError(f"Runner checks failed for {release_root.name}")
    return status, checks


def code_bundle_sha(project_root: Path) -> str:
    code_paths = [
        project_root / "scripts/validation_human/08_run_deg.R",
        project_root / "scripts/validation_human/08_finalize_deg_release.py",
        project_root / "scripts/validation_human/08_split_deg_release.py",
        project_root / "scripts/validation_human/seaad_common.py",
    ]
    payload = "\n".join(
        f"{path.relative_to(project_root)}={sha256_file(path)}"
        for path in code_paths
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def write_complete_artifacts(
    release_root: Path, project_root: Path
) -> pd.DataFrame:
    excluded = {
        (release_root / "artifacts.tsv").resolve(),
        (release_root / "status.tsv").resolve(),
    }
    paths = sorted(
        path.resolve()
        for path in release_root.rglob("*")
        if path.is_file() and path.resolve() not in excluded
    )
    return write_artifacts(paths, project_root, release_root / "artifacts.tsv")


def terminal_contract_checks(status: pd.DataFrame):
    eligible = status["eligibility_status"].eq("eligible")
    not_estimable = eligible & status["terminal_status"].eq("not_estimable")
    return [
        (
            "no_failed_contrasts",
            not status["terminal_status"].eq("failed").any(),
            int(status["terminal_status"].eq("failed").sum()),
            0,
            "",
        ),
        (
            "eligible_terminal_contract",
            status.loc[eligible, "terminal_status"]
            .isin(["completed", "not_estimable"])
            .all(),
            True,
            True,
            "not_estimable only permits no_genes_after_filterByExpr",
        ),
        (
            "recognized_post_design_reason",
            set(status.loc[not_estimable, "terminal_reason"]).issubset(
                {"no_genes_after_filterByExpr"}
            ),
            "|".join(sorted(set(status.loc[not_estimable, "terminal_reason"]))),
            "no_genes_after_filterByExpr",
            "",
        ),
    ]


def finalize_fine(
    config,
    config_path: Path,
    project_root: Path,
    output_root: Path,
    release_root: Path,
    effect_cut: float,
    started: str,
    bundle_sha: str,
) -> int:
    run_status, _ = validate_runner(
        release_root, "seaad_deg_fine_run_status_v1"
    )
    status_path = (
        release_root
        / "fine_supertype_phase18_parity"
        / "fine_contrast_status.tsv"
    )
    fine_status = read_table(status_path)
    contrast_summary, result_paths = summarize_results(
        fine_status, project_root, effect_cut
    )

    vh07_direction = read_table(
        output_root / "07_contrasts/fine_direction_manifest.tsv"
    )
    final_direction = vh07_direction.merge(
        fine_status[
            [
                "contrast_id",
                "terminal_status",
                "terminal_reason",
                "tested_feature_count",
                "filtered_feature_count",
                "result_path",
                "result_sha256",
                "filter_path",
                "filter_sha256",
            ]
        ],
        on="contrast_id",
        how="left",
        validate="many_to_one",
    )
    final_direction["source_terminal_status"] = final_direction["terminal_status"]
    final_direction["query_handoff_status"] = np.select(
        [
            final_direction["source_terminal_status"].eq("completed"),
            final_direction["source_terminal_status"].eq("not_estimable"),
            final_direction["source_terminal_status"].eq("failed"),
        ],
        [
            "ready_for_query_construction",
            "source_contrast_not_estimable",
            "source_contrast_failed",
        ],
        default="source_contrast_failed",
    )
    final_direction = final_direction.drop(columns=["terminal_status"])

    fine_summary = contrast_summary.loc[
        contrast_summary["deg_tier"].eq("fine_supertype_phase18_parity")
    ].set_index("contrast_id")
    direction_summary = final_direction[
        [
            "direction_slot",
            "direction_slot_id",
            "contrast_id",
            "deg_tier",
            "supertype_id",
            "supertype_label",
            "broad_network",
            "signature_group",
            "deg_direction",
            "phase18_signature_direction",
            "source_terminal_status",
            "query_handoff_status",
        ]
    ].copy()
    counts = []
    for row in direction_summary.itertuples(index=False):
        if (
            row.contrast_id not in fine_summary.index
            or row.source_terminal_status != "completed"
        ):
            counts.append(
                {
                    "fdr_significant_tested_feature_count": pd.NA,
                    "phase18_parity_tested_feature_count": pd.NA,
                    "effect_gate_excluded_tested_feature_count": pd.NA,
                }
            )
            continue
        source = fine_summary.loc[row.contrast_id]
        suffix = "up" if row.deg_direction == "Dementia_up" else "down"
        fdr_count = int(source[f"fdr_{suffix}"])
        parity_count = int(source[f"parity_{suffix}"])
        counts.append(
            {
                "fdr_significant_tested_feature_count": fdr_count,
                "phase18_parity_tested_feature_count": parity_count,
                "effect_gate_excluded_tested_feature_count": (
                    fdr_count - parity_count
                ),
            }
        )
    direction_summary = pd.concat(
        [direction_summary, pd.DataFrame(counts)], axis=1
    )
    direction_summary["summary_scope"] = (
        "pre_symbol_deduplication_pre_mitocarta_pre_network"
    )

    fine_index = read_table(
        release_root
        / "fine_supertype_phase18_parity"
        / "fine_result_index.tsv"
    )
    annotation_path = output_root / "03_genes/gene_annotation_master.tsv"
    query_index = fine_index.copy()
    query_index["annotation_path"] = str(
        annotation_path.relative_to(project_root)
    )
    query_index["annotation_sha256"] = sha256_file(annotation_path)
    query_index["phase18_parity_query_rule"] = config["query_rules"][
        "phase18_parity_query"
    ]
    query_index["fdr_only_query_sensitivity_rule"] = config["query_rules"][
        "fdr_only_query_sensitivity"
    ]
    query_index["authoritative_query_membership_frozen"] = False

    query_dir = release_root / "query_handoff"
    paths = {
        "direction": query_dir / "fine_direction_manifest.tsv",
        "query_index": query_dir / "fine_query_input_index.tsv",
        "direction_summary": query_dir / "fine_direction_deg_summary.tsv",
        "summary": release_root / "deg_summary.tsv",
        "diagnostics": release_root / "model_diagnostics.tsv.gz",
        "checks": release_root / "deg_checks.tsv",
        "artifacts": release_root / "artifacts.tsv",
        "status": release_root / "status.tsv",
    }
    diagnostics = pd.read_csv(
        release_root / "run_model_diagnostics.tsv.gz", sep="\t"
    )
    checks = [
        (
            "fine_contrast_rows",
            len(fine_status) == config["expected_identity"]["fine_contrasts"],
            len(fine_status),
            config["expected_identity"]["fine_contrasts"],
            "",
        ),
        (
            "fine_direction_rows",
            len(final_direction) == config["expected_identity"]["fine_directions"],
            len(final_direction),
            config["expected_identity"]["fine_directions"],
            "",
        ),
        (
            "fine_contrast_ids_unique",
            fine_status["contrast_id"].is_unique,
            fine_status["contrast_id"].nunique(),
            len(fine_status),
            "",
        ),
        (
            "fine_direction_ids_unique",
            final_direction["direction_slot_id"].is_unique,
            final_direction["direction_slot_id"].nunique(),
            len(final_direction),
            "",
        ),
        *terminal_contract_checks(fine_status),
        (
            "direction_handoff_status_complete",
            final_direction["query_handoff_status"]
            .isin(
                [
                    "ready_for_query_construction",
                    "source_contrast_not_estimable",
                    "source_contrast_failed",
                ]
            )
            .all(),
            True,
            True,
            "",
        ),
        (
            "completed_directions_remain_ready",
            final_direction.loc[
                final_direction["source_terminal_status"].eq("completed"),
                "query_handoff_status",
            ]
            .eq("ready_for_query_construction")
            .all(),
            True,
            True,
            "zero qualifying genes remain ready",
        ),
        (
            "query_rules_distinct",
            config["query_rules"]["phase18_parity_query"]
            != config["query_rules"]["fdr_only_query_sensitivity"],
            True,
            True,
            "",
        ),
        (
            "direction_summary_rows",
            len(direction_summary) == config["expected_identity"]["fine_directions"],
            len(direction_summary),
            config["expected_identity"]["fine_directions"],
            "",
        ),
        (
            "fine_diagnostic_rows",
            len(diagnostics) == config["expected_identity"]["included_supertypes"],
            len(diagnostics),
            config["expected_identity"]["included_supertypes"],
            "",
        ),
        (
            "all_result_files_validated",
            len(result_paths)
            == int(fine_status["terminal_status"].eq("completed").sum()),
            len(result_paths),
            int(fine_status["terminal_status"].eq("completed").sum()),
            "",
        ),
    ]
    checks_table = checks_frame(checks)
    atomic_write_tsv(final_direction, paths["direction"])
    atomic_write_tsv(query_index, paths["query_index"])
    atomic_write_tsv(direction_summary, paths["direction_summary"])
    atomic_write_tsv(contrast_summary, paths["summary"])
    atomic_write_tsv(diagnostics, paths["diagnostics"])
    atomic_write_tsv(checks_table, paths["checks"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    artifacts = write_complete_artifacts(release_root, project_root)
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH08F",
        state,
        project_root,
        config_path,
        started,
        failed,
        release_scope="fine",
        fine_structural_contrasts=len(fine_status),
        fine_completed=int(fine_status["terminal_status"].eq("completed").sum()),
        fine_not_estimable=int(
            fine_status["terminal_status"].eq("not_estimable").sum()
        ),
        fine_directions=len(final_direction),
        query_ready_directions=int(
            final_direction["query_handoff_status"]
            .eq("ready_for_query_construction")
            .sum()
        ),
        result_files=len(result_paths),
        artifact_count=len(artifacts),
        artifact_manifest_sha256=sha256_file(paths["artifacts"]),
        code_bundle_sha256=bundle_sha,
        fine_direction_manifest_sha256=sha256_file(paths["direction"]),
        fine_query_input_index_sha256=sha256_file(paths["query_index"]),
        run_status_sha256=sha256_file(release_root / "run_status.tsv"),
        source_model_config_sha256=run_status.loc[0, "config_sha256"],
        vh07_status_sha256=sha256_file(output_root / "07_contrasts/status.tsv"),
    )
    status["schema_version"] = FINE_STATUS_SCHEMA
    atomic_write_tsv(status, paths["status"])
    print(
        f"VH08F status: {state}; fine completed="
        f"{status.loc[0, 'fine_completed']}; query-ready directions="
        f"{status.loc[0, 'query_ready_directions']}"
    )
    return 0 if not failed else 2


def finalize_broad(
    config,
    config_path: Path,
    project_root: Path,
    output_root: Path,
    release_root: Path,
    effect_cut: float,
    started: str,
    bundle_sha: str,
) -> int:
    run_status, _ = validate_runner(
        release_root, "seaad_deg_broad_run_status_v1"
    )
    pooled_status = read_table(
        release_root / "broad_pooled_anchor/contrast_status.tsv"
    )
    broad_status = read_table(
        release_root / "broad_stratified_support/contrast_status.tsv"
    )
    all_status = pd.concat(
        [pooled_status, broad_status], ignore_index=True
    )
    contrast_summary, result_paths = summarize_results(
        all_status, project_root, effect_cut
    )
    diagnostics = pd.read_csv(
        release_root / "run_model_diagnostics.tsv.gz", sep="\t"
    )
    checks = [
        (
            "pooled_status_rows",
            len(pooled_status)
            == config["expected_identity"]["broad_pooled_contrasts"],
            len(pooled_status),
            config["expected_identity"]["broad_pooled_contrasts"],
            "",
        ),
        (
            "broad_status_rows",
            len(broad_status)
            == config["expected_identity"]["broad_stratified_contrasts"],
            len(broad_status),
            config["expected_identity"]["broad_stratified_contrasts"],
            "",
        ),
        (
            "broad_contrast_ids_unique",
            all_status["contrast_id"].is_unique,
            all_status["contrast_id"].nunique(),
            len(all_status),
            "",
        ),
        *terminal_contract_checks(all_status),
        (
            "broad_diagnostic_rows",
            len(diagnostics) == 14,
            len(diagnostics),
            14,
            "seven pooled plus seven stratified model diagnostics",
        ),
        (
            "all_result_files_validated",
            len(result_paths)
            == int(all_status["terminal_status"].eq("completed").sum()),
            len(result_paths),
            int(all_status["terminal_status"].eq("completed").sum()),
            "",
        ),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "summary": release_root / "deg_summary.tsv",
        "diagnostics": release_root / "model_diagnostics.tsv.gz",
        "checks": release_root / "deg_checks.tsv",
        "artifacts": release_root / "artifacts.tsv",
        "status": release_root / "status.tsv",
    }
    atomic_write_tsv(contrast_summary, paths["summary"])
    atomic_write_tsv(diagnostics, paths["diagnostics"])
    atomic_write_tsv(checks_table, paths["checks"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    artifacts = write_complete_artifacts(release_root, project_root)
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH08B",
        state,
        project_root,
        config_path,
        started,
        failed,
        release_scope="broad",
        broad_pooled_structural_contrasts=len(pooled_status),
        broad_pooled_completed=int(
            pooled_status["terminal_status"].eq("completed").sum()
        ),
        broad_pooled_not_estimable=int(
            pooled_status["terminal_status"].eq("not_estimable").sum()
        ),
        broad_stratified_structural_contrasts=len(broad_status),
        broad_stratified_completed=int(
            broad_status["terminal_status"].eq("completed").sum()
        ),
        broad_stratified_not_estimable=int(
            broad_status["terminal_status"].eq("not_estimable").sum()
        ),
        result_files=len(result_paths),
        artifact_count=len(artifacts),
        artifact_manifest_sha256=sha256_file(paths["artifacts"]),
        code_bundle_sha256=bundle_sha,
        run_status_sha256=sha256_file(release_root / "run_status.tsv"),
        source_model_config_sha256=run_status.loc[0, "config_sha256"],
        vh07_status_sha256=sha256_file(output_root / "07_contrasts/status.tsv"),
    )
    status["schema_version"] = BROAD_STATUS_SCHEMA
    atomic_write_tsv(status, paths["status"])
    print(
        f"VH08B status: {state}; pooled completed="
        f"{status.loc[0, 'broad_pooled_completed']}; stratified completed="
        f"{status.loc[0, 'broad_stratified_completed']}"
    )
    return 0 if not failed else 2


def main() -> int:
    args = parse_config_cli("VH08F/VH08B: finalize SEA-AD DEG releases")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_phase(output_root, "03_genes")
    require_phase(output_root, "07_contrasts")
    fine_root = phase_dir(output_root, "08_deg_fine")
    broad_root = phase_dir(output_root, "08_deg_broad")
    effect_cut = math.log2(float(config["thresholds"]["absolute_fold_change"]))
    bundle_sha = code_bundle_sha(project_root)
    fine_code = finalize_fine(
        config,
        config_path,
        project_root,
        output_root,
        fine_root,
        effect_cut,
        started,
        bundle_sha,
    )
    broad_code = finalize_broad(
        config,
        config_path,
        project_root,
        output_root,
        broad_root,
        effect_cut,
        started,
        bundle_sha,
    )
    return max(fine_code, broad_code)


if __name__ == "__main__":
    raise SystemExit(main())
