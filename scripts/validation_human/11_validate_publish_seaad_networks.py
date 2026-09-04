#!/usr/bin/env python3
"""Validate, rerun-check, and publish one immutable SEA-AD RIMBANet network."""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd
import yaml

from rimbanet_common import (
    load_rimbanet_config,
    parse_edge_file,
    provenance_path,
    safe_project_path,
    stage_dir,
    validate_network,
    write_stage_contract,
)
from seaad_common import (
    atomic_copy,
    atomic_write_text,
    atomic_write_tsv,
    sha256_file,
)


def edge_counts(paths: list[Path]) -> Counter:
    counts: Counter = Counter()
    for path in paths:
        edges = parse_edge_file(path)
        if len(edges) != len(set(edges)):
            raise ValueError(f"Duplicate edges in {path}")
        counts.update(edges)
    return counts


def selected_edges(
    counts: Counter, denominator: int, direction_min: float, adjacency_min: float
) -> set[tuple[str, str]]:
    result = set()
    pairs = {tuple(sorted(edge)) for edge in counts if edge[0] != edge[1]}
    for left, right in pairs:
        forward = counts[(left, right)] / denominator
        reverse = counts[(right, left)] / denominator
        if forward >= direction_min and forward + reverse >= adjacency_min and forward >= reverse:
            result.add((left, right))
        if reverse >= direction_min and forward + reverse >= adjacency_min and reverse >= forward:
            result.add((right, left))
    return result


def jaccard(left: set, right: set) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def update_release_manifest(release_root: Path, network: str) -> Path:
    rows = []
    for path in sorted((release_root / network).glob("*")):
        if path.is_file():
            rows.append(
                {
                    "cell_type": network,
                    "path": str(path.relative_to(release_root)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    manifest_path = release_root / "release_manifest.tsv"
    if manifest_path.exists():
        existing = pd.read_csv(manifest_path, sep="\t", dtype=str)
        existing = existing.loc[existing["cell_type"] != network]
        frame = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    else:
        frame = pd.DataFrame(rows)
    atomic_write_tsv(frame.sort_values(["cell_type", "path"]), manifest_path)
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--network", required=True)
    parser.add_argument("--binary")
    parser.add_argument("--consensus-script")
    parser.add_argument(
        "--skip-rerun-check",
        action="store_true",
        help="Fixture-only; production release requires a byte-identical rerun",
    )
    args = parser.parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    network = validate_network(config, args.network)
    expected = int(config["rimbanet"]["number_of_searches"])
    prefix = str(config["rimbanet"]["output_prefix"])
    run_dir = stage_dir(output_root, "11f_runs", create=False) / network
    consensus_dir = stage_dir(output_root, "11g_consensus", create=False) / network
    input_dir = stage_dir(output_root, "11e_inputs", create=False) / network
    prior_dir = stage_dir(output_root, "11d_priors", create=False) / network
    qc_dir = stage_dir(output_root, "11h_release_qc") / network
    qc_dir.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(run_dir / "run_ledger.tsv", sep="\t")
    if len(ledger) != expected or not ledger["valid"].astype(bool).all():
        raise ValueError("Run ledger is not complete")
    run_paths = [run_dir / f"{prefix}.{task}" for task in range(1, expected + 1)]
    counts = edge_counts(run_paths)
    candidate_path = consensus_dir / "result.links.3"
    final_path = consensus_dir / "result.links3.links.txt"
    runtime_path = run_dir / "runtime_report.tsv"
    candidate = set(parse_edge_file(candidate_path))
    final_edges = parse_edge_file(final_path)
    final = set(final_edges)
    nodes_table = pd.read_csv(input_dir / "nodes.tsv", sep="\t")
    nodes = set(nodes_table["source_symbol"].astype(str))

    direction_min = float(config["consensus"]["minimum_direction_support"])
    adjacency_min = float(config["consensus"]["minimum_adjacency_support"])
    independently_selected = selected_edges(
        counts, expected, direction_min, adjacency_min
    )
    support_rows = []
    for parent, child in sorted(candidate):
        forward_count = counts[(parent, child)]
        reverse_count = counts[(child, parent)]
        support_rows.append(
            {
                "parent": parent,
                "child": child,
                "forward_count": forward_count,
                "reverse_count": reverse_count,
                "denominator": expected,
                "forward_proportion": forward_count / expected,
                "reverse_proportion": reverse_count / expected,
                "adjacency_proportion": (forward_count + reverse_count) / expected,
                "direction_tie": forward_count == reverse_count,
                "selected_consensus": True,
                "retained_final": (parent, child) in final,
                "removed_by_deloop": (parent, child) not in final,
            }
        )
    support = pd.DataFrame(support_rows)
    support_path = consensus_dir / "edge_support.tsv.gz"
    temporary = support_path.with_name(f"{support_path.name}.tmp")
    support.to_csv(temporary, sep="\t", index=False, compression="gzip")
    temporary.replace(support_path)

    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(final_edges)
    maximum_indegree = max((degree for _, degree in graph.in_degree()), default=0)
    reciprocal = sum(1 for u, v in final if (v, u) in final) // 2
    duplicates = len(final_edges) - len(final)

    midpoint = expected // 2
    first_counts = edge_counts(run_paths[:midpoint])
    second_counts = edge_counts(run_paths[midpoint:])
    first = selected_edges(first_counts, midpoint, direction_min, adjacency_min)
    second = selected_edges(
        second_counts, expected - midpoint, direction_min, adjacency_min
    )

    rerun_identical = False
    original_hashes = {
        name: sha256_file(consensus_dir / name)
        for name in [
            "result.links.3",
            "result.linksMatrix.3",
            "result.links3",
            "result.links3.links.txt",
        ]
    }
    if args.skip_rerun_check:
        rerun_identical = True
    else:
        consensus_script = (
            Path(args.consensus_script).resolve()
            if args.consensus_script
            else project_root
            / "scripts/validation_human/11_build_rimbanet_consensus.sh"
        )
        command = [
            "bash",
            str(consensus_script),
            "--config",
            str(config_path),
            "--network",
            network,
        ]
        if args.binary:
            command.extend(["--binary", args.binary])
        result = subprocess.run(command, cwd=project_root, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Consensus rerun failed: {result.stderr[-2000:]}")
        rerun_identical = all(
            sha256_file(consensus_dir / name) == digest
            for name, digest in original_hashes.items()
        )

    checks = [
        ("exact_search_denominator", len(run_paths) == expected, len(run_paths), expected, ""),
        ("legacy_candidate_rule_parity", candidate == independently_selected, len(candidate ^ independently_selected), 0, ""),
        ("final_subset_of_consensus", final.issubset(candidate), len(final - candidate), 0, ""),
        ("final_edges_unique", duplicates == 0, duplicates, 0, ""),
        ("no_self_loops", nx.number_of_selfloops(graph) == 0, nx.number_of_selfloops(graph), 0, ""),
        ("no_reciprocal_edges", reciprocal == 0, reciprocal, 0, ""),
        ("all_nodes_known", all(u in nodes and v in nodes for u, v in final), len({n for edge in final for n in edge} - nodes), 0, ""),
        ("directed_acyclic_graph", nx.is_directed_acyclic_graph(graph), nx.is_directed_acyclic_graph(graph), True, ""),
        ("maximum_indegree", maximum_indegree <= int(config["release_checks"]["maximum_indegree"]), maximum_indegree, f"<={config['release_checks']['maximum_indegree']}", ""),
        ("byte_identical_consensus_rerun", rerun_identical, rerun_identical, True, "fixture skip is not permitted for production"),
        (
            "pilot_runtime_report_present",
            network != config["cohort"]["pilot_network"] or runtime_path.is_file(),
            runtime_path.is_file(),
            True,
            "",
        ),
    ]
    failed = [name for name, passed, *_ in checks if not passed]
    state = "validated_complete" if not failed else "failed"
    qc = pd.DataFrame(
        [
            {
                "network": network,
                "searches": expected,
                "nodes": len(nodes),
                "candidate_edges": len(candidate),
                "final_edges": len(final),
                "removed_by_deloop": len(candidate - final),
                "roots": sum(degree == 0 for _, degree in graph.in_degree()),
                "leaves": sum(degree == 0 for _, degree in graph.out_degree()),
                "weak_components": nx.number_weakly_connected_components(graph),
                "density": nx.density(graph),
                "maximum_indegree": maximum_indegree,
                "half_search_directed_jaccard": jaccard(first, second),
                "rerun_identical": rerun_identical,
                "release_state": state,
            }
        ]
    )
    qc_path = qc_dir / "network_qc.tsv"
    atomic_write_tsv(qc, qc_path)
    write_stage_contract(
        qc_dir,
        "VH11H",
        state,
        config_path,
        project_root,
        checks,
        [support_path, candidate_path, final_path, qc_path],
        network=network,
        failed_checks=";".join(failed),
    )
    if network == config["cohort"]["pilot_network"]:
        atomic_write_tsv(
            pd.DataFrame(
                [
                    {
                        "schema_version": "seaad_rimbanet_pilot_gate_v1",
                        "network": network,
                        "state": "passed" if not failed else "blocked",
                        "valid_searches": len(ledger),
                        "required_searches": expected,
                        "consensus_qc": state,
                        "runtime_report": provenance_path(
                            runtime_path, project_root
                        ),
                    }
                ]
            ),
            run_dir.parent / "pilot_gate.tsv",
        )
    if failed:
        print(f"VH11H failed: network={network}; {','.join(failed)}")
        return 2

    release_root = safe_project_path(
        project_root, config["release_root"], must_exist=False
    )
    destination = release_root / network
    destination.mkdir(parents=True, exist_ok=True)
    copies = {
        final_path: destination / "result.links3.links.txt",
        support_path: destination / "edge_support.tsv.gz",
        input_dir / "nodes.tsv": destination / "nodes.tsv",
        input_dir / "sample_manifest.tsv": destination / "sample_manifest.tsv",
        input_dir / "gene_manifest.tsv": destination / "gene_manifest.tsv",
        prior_dir / "prior_summary.tsv": destination / "prior_summary.tsv",
        qc_path: destination / "network_qc.tsv",
    }
    for source, target in copies.items():
        if not source.exists():
            raise FileNotFoundError(source)
        atomic_copy(source, target)
    manifest = {
        "schema_version": "seaad_rimbanet_network_manifest_v1",
        "release_id": config["release_id"],
        "network": network,
        "method": config["method"]["name"],
        "mode": config["method"]["mode"],
        "rimbanet_source_commit": config["method"]["source_commit"],
        "config_path": str(config_path.relative_to(project_root)),
        "config_sha256": sha256_file(config_path),
        "searches": expected,
        "nodes": len(nodes),
        "edges": len(final),
        "direction_interpretation": (
            "prior-constrained probabilistic upstream relation; not signed or proven causal"
        ),
        "files": {
            target.name: sha256_file(target) for target in copies.values()
        },
    }
    manifest_path = destination / "network_manifest.yml"
    atomic_write_text(yaml.safe_dump(manifest, sort_keys=False), manifest_path)
    release_manifest = update_release_manifest(release_root, network)
    print(f"VH11 release published: {network}; edges={len(final)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
