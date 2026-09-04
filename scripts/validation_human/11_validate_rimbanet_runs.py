#!/usr/bin/env python3
"""Require a complete, parseable set of RIMBANet stochastic searches."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd

from rimbanet_common import (
    load_rimbanet_config,
    parse_edge_file,
    parser,
    stage_dir,
    validate_network,
    write_stage_contract,
)
from seaad_common import atomic_write_tsv, sha256_file


def main() -> int:
    args = parser("Validate all RIMBANet searches", network=True).parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    network = validate_network(config, args.network)
    run_dir = stage_dir(output_root, "11f_runs") / network
    run_dir.mkdir(parents=True, exist_ok=True)
    expected = int(config["rimbanet"]["number_of_searches"])
    prefix = str(config["rimbanet"]["output_prefix"])
    rows = []
    valid_count = 0
    artifacts: list[Path] = []
    for task_id in range(1, expected + 1):
        status_path = run_dir / f"task.{task_id}.status.tsv"
        output_path = run_dir / f"{prefix}.{task_id}"
        log_path = run_dir / f"junkK.{task_id}"
        resource_path = run_dir / f"resource.{task_id}.txt"
        row = {
            "network": network,
            "task_id": task_id,
            "expected_seed": int(config["rimbanet"]["base_seed"]) + task_id,
            "status_present": status_path.exists(),
            "output_present": output_path.exists() and output_path.stat().st_size > 0,
            "log_present": log_path.exists() and log_path.stat().st_size > 0,
            "state": "missing",
            "exit_code": pd.NA,
            "edge_count": pd.NA,
            "elapsed_seconds": pd.NA,
            "max_rss_kb": pd.NA,
            "resource_usage_present": resource_path.exists(),
            "output_sha256": pd.NA,
            "dag": False,
            "likelihood_record": False,
            "valid": False,
            "details": "",
        }
        try:
            if not status_path.exists():
                raise ValueError("missing status")
            status = pd.read_csv(status_path, sep="\t", dtype=str)
            if len(status) != 1:
                raise ValueError("status must contain one row")
            state = status.iloc[0]
            row["state"] = state["state"]
            row["exit_code"] = state["exit_code"]
            if pd.notna(state.get("elapsed_seconds")):
                row["elapsed_seconds"] = int(state["elapsed_seconds"])
            if pd.notna(state.get("max_rss_kb")) and state.get("max_rss_kb") != "":
                row["max_rss_kb"] = int(state["max_rss_kb"])
            if state["state"] != "validated_complete" or state["exit_code"] != "0":
                raise ValueError("task status is not validated_complete")
            if int(state["seed"]) != row["expected_seed"]:
                raise ValueError("seed mismatch")
            if not output_path.exists() or not log_path.exists():
                raise ValueError("missing output/log")
            edges = parse_edge_file(output_path)
            if not edges:
                raise ValueError("empty edge set")
            if len(edges) != len(set(edges)):
                raise ValueError("duplicate edge")
            graph = nx.DiGraph(edges)
            row["dag"] = nx.is_directed_acyclic_graph(graph)
            if not row["dag"]:
                raise ValueError("search output is not a DAG")
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            row["likelihood_record"] = "LIKELIHOOD" in log_text
            if not row["likelihood_record"]:
                raise ValueError("missing LIKELIHOOD record")
            observed_sha = sha256_file(output_path)
            if observed_sha != state["output_sha256"]:
                raise ValueError("output checksum mismatch")
            row["edge_count"] = len(edges)
            row["output_sha256"] = observed_sha
            row["valid"] = True
            valid_count += 1
        except Exception as exc:  # preserve every failed task in the ledger
            row["details"] = str(exc)
        rows.append(row)
        if row["valid"]:
            artifacts.extend([status_path, output_path, log_path])
            if resource_path.exists():
                artifacts.append(resource_path)

    ledger = pd.DataFrame(rows)
    ledger_path = run_dir / "run_ledger.tsv"
    atomic_write_tsv(ledger, ledger_path)
    valid_ledger = ledger.loc[ledger["valid"].astype(bool)]
    elapsed = pd.to_numeric(valid_ledger["elapsed_seconds"], errors="coerce")
    rss = pd.to_numeric(valid_ledger["max_rss_kb"], errors="coerce")
    runtime_report = pd.DataFrame(
        [
            {
                "network": network,
                "valid_searches": valid_count,
                "elapsed_min_seconds": elapsed.min(),
                "elapsed_median_seconds": elapsed.median(),
                "elapsed_max_seconds": elapsed.max(),
                "total_task_hours": elapsed.sum() / 3600.0,
                "tasks_with_max_rss": int(rss.notna().sum()),
                "max_rss_median_mb": rss.median() / 1024.0,
                "max_rss_maximum_mb": rss.max() / 1024.0,
            }
        ]
    )
    runtime_path = run_dir / "runtime_report.tsv"
    atomic_write_tsv(runtime_report, runtime_path)
    artifacts.extend([ledger_path, runtime_path])
    checks = [
        ("expected_task_rows", len(ledger) == expected, len(ledger), expected, ""),
        ("all_tasks_valid", valid_count == expected, valid_count, expected, ""),
        ("all_seeds_unique", ledger["expected_seed"].is_unique, ledger["expected_seed"].nunique(), expected, ""),
        ("explicit_consensus_denominator", int(config["consensus"]["denominator"]) == expected, config["consensus"]["denominator"], expected, ""),
    ]
    failed = [name for name, passed, *_ in checks if not passed]
    state = "validated_complete" if not failed else "blocked_incomplete_searches"
    write_stage_contract(
        run_dir,
        "VH11F",
        state,
        config_path,
        project_root,
        checks,
        artifacts,
        network=network,
        valid_searches=valid_count,
        expected_searches=expected,
        failed_checks=";".join(failed),
    )
    if network == config["cohort"]["pilot_network"]:
        pilot = pd.DataFrame(
            [
                {
                    "schema_version": "seaad_rimbanet_pilot_gate_v1",
                    "network": network,
                    "state": (
                        "searches_validated"
                        if state == "validated_complete"
                        else "blocked"
                    ),
                    "valid_searches": valid_count,
                    "required_searches": expected,
                }
            ]
        )
        atomic_write_tsv(pilot, run_dir.parent / "pilot_gate.tsv")
    print(f"VH11F status: {state}; network={network}; valid={valid_count}/{expected}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
