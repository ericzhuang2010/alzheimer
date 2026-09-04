#!/usr/bin/env python3
"""Combine expression, CIT, and ENCODE evidence into RIMBANet priors."""

from __future__ import annotations

import math
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd

from rimbanet_common import (
    configured_path,
    load_rimbanet_config,
    parser,
    stage_dir,
    validate_network,
    write_stage_contract,
)
from seaad_common import atomic_write_tsv


def read_nodes(path: Path) -> tuple[list[str], int]:
    nodes: list[str] = []
    fields = None
    with path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            values = line.rstrip("\n").split("\t")
            if len(values) < 2:
                raise ValueError(f"Bad discretized row {line_number}")
            fields = fields or len(values)
            if len(values) != fields:
                raise ValueError("Discretized rows have inconsistent widths")
            nodes.append(values[0])
    if not nodes or fields is None or len(nodes) != len(set(nodes)):
        raise ValueError("Discretized node list is empty or duplicated")
    return nodes, fields


def parse_base_prior(path: Path):
    rows = []
    with path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.split()
            if len(fields) < 5 or fields[1] != "->":
                raise ValueError(f"Bad base prior line {line_number}: {line.rstrip()}")
            rows.append(
                {
                    "parent": fields[0],
                    "child": fields[2],
                    "log_prior": float(fields[3]),
                    "mutual_information": fields[4],
                }
            )
    if not rows:
        raise ValueError("Base prior is empty")
    return rows


def evidence_rows(
    cit_path: Path, encode_path: Path, node_set: set[str], added_weight: float
) -> pd.DataFrame:
    rows = []
    if cit_path.exists():
        cit = pd.read_csv(cit_path, sep="\t")
        required = {"parent", "child"}
        if not required.issubset(cit.columns):
            raise ValueError("CIT table lacks parent/child")
        if "significant" in cit.columns:
            cit = cit.loc[cit["significant"].astype(str).str.lower().eq("true")]
        for row in cit.itertuples(index=False):
            parent, child = str(row.parent), str(row.child)
            if parent in node_set and child in node_set and parent != child:
                rows.append(
                    {
                        "parent": parent,
                        "child": child,
                        "source": "CIT",
                        "added_weight": added_weight,
                    }
                )
    if encode_path.exists():
        encode = pd.read_csv(encode_path, sep="\t")
        aliases = [
            ("parent", "child"),
            ("tf", "target"),
            ("source", "target"),
            ("TF", "target"),
        ]
        pair = next(
            ((left, right) for left, right in aliases if {left, right}.issubset(encode)),
            None,
        )
        if pair is None:
            raise ValueError("ENCODE table needs parent/child or tf/target columns")
        for row in encode[[pair[0], pair[1]]].itertuples(index=False, name=None):
            parent, child = map(str, row)
            if parent in node_set and child in node_set and parent != child:
                rows.append(
                    {
                        "parent": parent,
                        "child": child,
                        "source": "ENCODE",
                        "added_weight": added_weight,
                    }
                )
    return pd.DataFrame(
        rows, columns=["parent", "child", "source", "added_weight"]
    )


def resolve_conflicts(evidence: pd.DataFrame):
    if evidence.empty:
        return evidence.copy(), pd.DataFrame()
    grouped = (
        evidence.groupby(["parent", "child"], as_index=False)
        .agg(
            added_weight=("added_weight", "max"),
            sources=("source", lambda x: ",".join(sorted(set(x)))),
        )
        .sort_values(["parent", "child"])
    )
    by_pair = defaultdict(list)
    for row in grouped.itertuples(index=False):
        key = tuple(sorted((row.parent, row.child)))
        by_pair[key].append(row)
    selected, conflicts = [], []
    for key, rows in sorted(by_pair.items()):
        if len(rows) == 1:
            selected.append(rows[0])
            continue
        ranked = sorted(
            rows,
            key=lambda row: (-float(row.added_weight), row.parent, row.child),
        )
        winner = ranked[0]
        selected.append(winner)
        for loser in ranked[1:]:
            conflicts.append(
                {
                    "node_a": key[0],
                    "node_b": key[1],
                    "winner": f"{winner.parent}->{winner.child}",
                    "loser": f"{loser.parent}->{loser.child}",
                    "policy": "higher_weight_then_lexicographic",
                }
            )
    selected_frame = pd.DataFrame(
        [
            {
                "parent": row.parent,
                "child": row.child,
                "added_weight": row.added_weight,
                "sources": row.sources,
            }
            for row in selected
        ]
    )
    return selected_frame, pd.DataFrame(conflicts)


def write_prior(rows, path: Path) -> None:
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(
                f"{row['parent']} -> {row['child']} "
                f"{row['log_prior']:.17g} {row['mutual_information']}\n"
            )
    os.replace(temporary, path)


def write_identity_ban(nodes: list[str], path: Path) -> None:
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        for index in range(len(nodes)):
            row = ["0"] * len(nodes)
            row[index] = "1"
            handle.write(" ".join(row) + "\n")
    os.replace(temporary, path)


def main() -> int:
    args = parser("Build full-integrative RIMBANet priors", network=True).parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    network = validate_network(config, args.network)
    input_dir = stage_dir(output_root, "11e_inputs") / network
    prior_dir = stage_dir(output_root, "11d_priors") / network
    prior_dir.mkdir(parents=True, exist_ok=True)
    data_path = input_dir / "data.discretized.txt"
    base_path = input_dir / "prior.base.txt"
    if not data_path.exists() or not base_path.exists():
        raise FileNotFoundError(
            "Run discretization and input preparation through base-prior generation first"
        )
    nodes, number_of_fields = read_nodes(data_path)
    node_set = set(nodes)
    base = parse_base_prior(base_path)
    base_keys = {(row["parent"], row["child"]) for row in base}

    weight = float(config["priors"]["default_added_weight_multiplier"]) * math.log(
        number_of_fields
    )
    cit_path = prior_dir / "cit_edges.tsv.gz"
    encode_path = configured_path(
        project_root, config["inputs"]["encode_tf_targets"], must_exist=False
    )
    evidence = evidence_rows(cit_path, encode_path, node_set, weight)
    selected, conflicts = resolve_conflicts(evidence)
    selected_keys = {
        (str(row.parent), str(row.child)): float(row.added_weight)
        for row in selected.itertuples(index=False)
    }
    matched = set(selected_keys).intersection(base_keys)
    unmatched = set(selected_keys).difference(base_keys)
    for row in base:
        row["log_prior"] += selected_keys.get((row["parent"], row["child"]), 0.0)

    prior_path = input_dir / "prior.txt"
    banned_path = input_dir / "banned.txt"
    write_prior(base, prior_path)
    write_identity_ban(nodes, banned_path)
    combined_path = prior_dir / "combined_prior_evidence.tsv.gz"
    conflict_path = prior_dir / "prior_conflicts.tsv"
    atomic_write_tsv(selected, combined_path)
    atomic_write_tsv(conflicts, conflict_path)
    if unmatched:
        atomic_write_tsv(
            pd.DataFrame(sorted(unmatched), columns=["parent", "child"]),
            prior_dir / "unmatched_prior_evidence.tsv",
        )
    summary = pd.DataFrame(
        [
            {
                "network": network,
                "nodes": len(nodes),
                "base_prior_rows": len(base),
                "CIT_evidence_rows": int(
                    (evidence.get("source", pd.Series(dtype=str)) == "CIT").sum()
                ),
                "ENCODE_evidence_rows": int(
                    (evidence.get("source", pd.Series(dtype=str)) == "ENCODE").sum()
                ),
                "selected_prior_directions": len(selected),
                "matched_base_prior_directions": len(matched),
                "unmatched_base_prior_directions": len(unmatched),
                "direction_conflicts": len(conflicts),
                "added_weight": weight,
            }
        ]
    )
    summary_path = prior_dir / "prior_summary.tsv"
    atomic_write_tsv(summary, summary_path)

    banned_rows = sum(1 for _ in banned_path.open())
    checks = [
        ("full_integrative_mode", config["method"]["mode"] == "full_integrative", config["method"]["mode"], "full_integrative", ""),
        ("expression_fallback_disabled", not config["method"]["allow_expression_only_fallback"], config["method"]["allow_expression_only_fallback"], False, ""),
        ("CIT_source_present", cit_path.exists(), cit_path.exists(), True, ""),
        ("ENCODE_source_present", encode_path.exists(), encode_path.exists(), True, ""),
        ("prior_nonempty", prior_path.stat().st_size > 0, prior_path.stat().st_size, ">0", ""),
        ("banned_matrix_rows", banned_rows == len(nodes), banned_rows, len(nodes), ""),
        ("all_structural_evidence_matched", not unmatched, len(unmatched), 0, ""),
    ]
    failed = [name for name, passed, *_ in checks if not passed]
    state = "validated_complete" if not failed else "blocked_incomplete_priors"
    write_stage_contract(
        prior_dir,
        "VH11D",
        state,
        config_path,
        project_root,
        checks,
        [prior_path, banned_path, combined_path, conflict_path, summary_path],
        network=network,
        failed_checks=";".join(failed),
    )
    print(f"VH11D status: {state}; network={network}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
