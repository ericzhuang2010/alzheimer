#!/usr/bin/env python3
"""VH08 finalizer: validate edgeR shards and publish the DEG/query handoff."""

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


def read_table(path):
    return pd.read_csv(path, sep="	", keep_default_na=False)


def result_summary(row, project_root, effect_cut):
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
    table = pd.read_csv(path, sep="	")
    numeric = table[["logFC", "logCPM", "F", "PValue", "FDR"]].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"Nonfinite DEG statistic: {path}")
    if not ((table["PValue"].between(0, 1)) & (table["FDR"].between(0, 1))).all():
        raise ValueError(f"Invalid P/FDR range: {path}")
    expected_direction = np.where(
        table["logFC"] > 0, "Dementia_up",
        np.where(table["logFC"] < 0, "Dementia_down", "zero"),
    )
    if not np.array_equal(table["effect_direction"].to_numpy(), expected_direction):
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


def main() -> int:
    args = parse_config_cli("VH08: finalize SEA-AD DEG release")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_phase(output_root, "03_genes")
    require_phase(output_root, "07_contrasts")
    output_dir = phase_dir(output_root, "08_deg")
    run_status_path = output_dir / "run_status.tsv"
    run_checks_path = output_dir / "run_checks.tsv"
    if not run_status_path.exists() or not run_checks_path.exists():
        raise FileNotFoundError("VH08 runner records are missing")
    run_status = read_table(run_status_path)
    run_checks = pd.read_csv(run_checks_path, sep="	")
    if len(run_status) != 1 or run_status.loc[0, "task_status"] != "worker_complete":
        raise ValueError("VH08 runner did not complete")
    if not run_checks["passed"].astype(bool).all():
        raise ValueError("VH08 runner checks did not pass")

    fine_status_path = output_dir / "fine_supertype_phase18_parity/fine_contrast_status.tsv"
    pooled_status_path = output_dir / "broad_pooled_anchor/contrast_status.tsv"
    broad_status_path = output_dir / "broad_stratified_support/contrast_status.tsv"
    fine_status = read_table(fine_status_path)
    pooled_status = read_table(pooled_status_path)
    broad_status = read_table(broad_status_path)
    all_status = pd.concat([fine_status, pooled_status, broad_status], ignore_index=True)
    effect_cut = math.log2(float(config["thresholds"]["absolute_fold_change"]))

    summaries = []
    result_paths = []
    for row in all_status.itertuples(index=False):
        summary, path = result_summary(row, project_root, effect_cut)
        summaries.append(summary)
        if path is not None:
            result_paths.append(path)
        if row.filter_path:
            filter_path = project_root / row.filter_path
            if sha256_file(filter_path) != row.filter_sha256:
                raise ValueError(f"Filter checksum mismatch: {filter_path}")
    contrast_summary = pd.DataFrame(summaries)

    vh07_direction = read_table(output_root / "07_contrasts/fine_direction_manifest.tsv")
    final_direction = vh07_direction.merge(
        fine_status[[
            "contrast_id", "terminal_status", "terminal_reason",
            "tested_feature_count", "filtered_feature_count",
            "result_path", "result_sha256", "filter_path", "filter_sha256",
        ]],
        on="contrast_id", how="left", validate="many_to_one",
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
    direction_summary = final_direction[[
        "direction_slot", "direction_slot_id", "contrast_id", "deg_tier",
        "supertype_id", "supertype_label", "broad_network", "signature_group",
        "deg_direction", "phase18_signature_direction", "source_terminal_status",
        "query_handoff_status",
    ]].copy()
    counts = []
    for row in direction_summary.itertuples(index=False):
        if row.contrast_id not in fine_summary.index or row.source_terminal_status != "completed":
            counts.append({
                "fdr_significant_tested_feature_count": pd.NA,
                "phase18_parity_tested_feature_count": pd.NA,
                "effect_gate_excluded_tested_feature_count": pd.NA,
            })
            continue
        source = fine_summary.loc[row.contrast_id]
        suffix = "up" if row.deg_direction == "Dementia_up" else "down"
        fdr_count = int(source[f"fdr_{suffix}"])
        parity_count = int(source[f"parity_{suffix}"])
        counts.append({
            "fdr_significant_tested_feature_count": fdr_count,
            "phase18_parity_tested_feature_count": parity_count,
            "effect_gate_excluded_tested_feature_count": fdr_count - parity_count,
        })
    direction_summary = pd.concat([direction_summary, pd.DataFrame(counts)], axis=1)
    direction_summary["summary_scope"] = "pre_symbol_deduplication_pre_mitocarta_pre_network"

    fine_index = read_table(output_dir / "fine_supertype_phase18_parity/fine_result_index.tsv")
    annotation_path = output_root / "03_genes/gene_annotation_master.tsv"
    query_index = fine_index.copy()
    query_index["annotation_path"] = str(annotation_path.relative_to(project_root))
    query_index["annotation_sha256"] = sha256_file(annotation_path)
    query_index["phase18_parity_query_rule"] = config["query_rules"]["phase18_parity_query"]
    query_index["fdr_only_query_sensitivity_rule"] = config["query_rules"]["fdr_only_query_sensitivity"]
    query_index["authoritative_query_membership_frozen"] = False

    diagnostics_source = output_dir / "run_model_diagnostics.tsv.gz"
    diagnostics = pd.read_csv(diagnostics_source, sep="	")
    code_paths = sorted(
        path for path in (project_root / "scripts/validation_human").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    code_payload = chr(10).join(
        f"{path.relative_to(project_root)}={sha256_file(path)}" for path in code_paths
    )
    code_bundle_sha = hashlib.sha256(code_payload.encode()).hexdigest()

    checks = [
        ("fine_contrast_rows", len(fine_status) == config["expected_identity"]["fine_contrasts"], len(fine_status), config["expected_identity"]["fine_contrasts"], ""),
        ("fine_direction_rows", len(final_direction) == config["expected_identity"]["fine_directions"], len(final_direction), config["expected_identity"]["fine_directions"], ""),
        ("fine_contrast_ids_unique", fine_status["contrast_id"].is_unique, fine_status["contrast_id"].nunique(), len(fine_status), ""),
        ("fine_direction_ids_unique", final_direction["direction_slot_id"].is_unique, final_direction["direction_slot_id"].nunique(), len(final_direction), ""),
        ("pooled_status_rows", len(pooled_status) == 7, len(pooled_status), 7, ""),
        ("broad_status_rows", len(broad_status) == 42, len(broad_status), 42, ""),
        ("no_failed_contrasts", not all_status["terminal_status"].eq("failed").any(), int(all_status["terminal_status"].eq("failed").sum()), 0, ""),
        ("eligible_terminal_contract", all_status.loc[all_status["eligibility_status"].eq("eligible"), "terminal_status"].isin(["completed", "not_estimable"]).all(), True, True, "not_estimable only permits no_genes_after_filterByExpr"),
        ("recognized_post_design_reason", set(all_status.loc[(all_status["eligibility_status"].eq("eligible")) & (all_status["terminal_status"].eq("not_estimable")), "terminal_reason"]).issubset({"no_genes_after_filterByExpr"}), "|".join(sorted(set(all_status.loc[(all_status["eligibility_status"].eq("eligible")) & (all_status["terminal_status"].eq("not_estimable")), "terminal_reason"]))), "no_genes_after_filterByExpr", ""),
        ("direction_handoff_status_complete", final_direction["query_handoff_status"].isin(["ready_for_query_construction", "source_contrast_not_estimable", "source_contrast_failed"]).all(), True, True, ""),
        ("completed_directions_remain_ready", final_direction.loc[final_direction["source_terminal_status"].eq("completed"), "query_handoff_status"].eq("ready_for_query_construction").all(), True, True, "zero qualifying genes remain ready"),
        ("query_rules_distinct", config["query_rules"]["phase18_parity_query"] != config["query_rules"]["fdr_only_query_sensitivity"], True, True, ""),
        ("direction_summary_rows", len(direction_summary) == config["expected_identity"]["fine_directions"], len(direction_summary), config["expected_identity"]["fine_directions"], ""),
        ("all_result_files_validated", len(result_paths) == int(all_status["terminal_status"].eq("completed").sum()), len(result_paths), int(all_status["terminal_status"].eq("completed").sum()), ""),
    ]
    checks_table = checks_frame(checks)

    query_dir = output_dir / "query_handoff"
    query_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "direction": query_dir / "fine_direction_manifest.tsv",
        "query_index": query_dir / "fine_query_input_index.tsv",
        "direction_summary": query_dir / "fine_direction_deg_summary.tsv",
        "summary": output_dir / "deg_summary.tsv",
        "diagnostics": output_dir / "model_diagnostics.tsv.gz",
        "checks": output_dir / "deg_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(final_direction, paths["direction"])
    atomic_write_tsv(query_index, paths["query_index"])
    atomic_write_tsv(direction_summary, paths["direction_summary"])
    atomic_write_tsv(contrast_summary, paths["summary"])
    atomic_write_tsv(diagnostics, paths["diagnostics"])
    atomic_write_tsv(checks_table, paths["checks"])

    generated_paths = [
        fine_status_path, pooled_status_path, broad_status_path,
        output_dir / "fine_supertype_phase18_parity/fine_result_index.tsv",
        output_dir / "broad_pooled_anchor/result_index.tsv",
        output_dir / "broad_stratified_support/result_index.tsv",
        run_status_path, run_checks_path,
    ]
    generated_paths.extend(result_paths)
    generated_paths.extend(project_root / value for value in all_status["filter_path"].unique() if value)
    generated_paths.extend(
        path for path in output_dir.rglob("*.tsv")
        if path not in {paths["artifacts"], paths["status"]}
    )
    generated_paths.extend([diagnostics_source, paths["diagnostics"]])
    generated_paths = sorted(set(Path(path).resolve() for path in generated_paths if Path(path).exists()))
    write_artifacts(generated_paths, project_root, paths["artifacts"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH08", state, project_root, config_path, started, failed,
        fine_structural_contrasts=len(fine_status),
        fine_completed=int(fine_status["terminal_status"].eq("completed").sum()),
        fine_not_estimable=int(fine_status["terminal_status"].eq("not_estimable").sum()),
        fine_directions=len(final_direction),
        query_ready_directions=int(final_direction["query_handoff_status"].eq("ready_for_query_construction").sum()),
        broad_pooled_completed=int(pooled_status["terminal_status"].eq("completed").sum()),
        broad_stratified_completed=int(broad_status["terminal_status"].eq("completed").sum()),
        result_files=len(result_paths),
        code_bundle_sha256=code_bundle_sha,
        fine_direction_manifest_sha256=sha256_file(paths["direction"]),
        fine_query_input_index_sha256=sha256_file(paths["query_index"]),
        vh07_status_sha256=sha256_file(output_root / "07_contrasts/status.tsv"),
    )
    atomic_write_tsv(status, paths["status"])
    print(
        f"VH08 status: {state}; fine completed={status.loc[0, 'fine_completed']}; "
        f"query-ready directions={status.loc[0, 'query_ready_directions']}"
    )
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
