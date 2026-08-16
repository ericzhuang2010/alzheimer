#!/usr/bin/env python3
"""Generate the Phase 18 RPL11 directed-network deep-dive package."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math
import os
import shutil
import statistics
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch
from scipy.stats import hypergeom


SCHEMA = "phase18_rpl11_deep_dive_v1"
RPL11 = "RPL11"
PRIMARY_NETWORKS = ("Excitatory_neurons", "Astrocytes")
SELECTED_NETWORKS = (
    "Excitatory_neurons",
    "Astrocytes",
    "Microglia",
    "Oligodendrocytes",
)
NETWORK_LABELS = {
    "Excitatory_neurons": "Excitatory neurons",
    "Astrocytes": "Astrocytes",
    "Microglia": "Microglia",
    "Oligodendrocytes": "Oligodendrocytes",
}
NETWORK_SHORT = {
    "Excitatory_neurons": "Exc",
    "Astrocytes": "Ast",
    "Microglia": "Mic",
    "Oligodendrocytes": "Oli",
}
NETWORK_INPUT = {
    network: ROOT / "data" / "bayesian_network" / network / "result.links3.links.txt"
    for network in PRIMARY_NETWORKS
}
CANONICAL = (
    ROOT
    / "results"
    / "minerva_production"
    / "18_key_driver_selection"
    / "call_key_driver_returns.tsv"
)
RUN_MANIFEST = ROOT / "results" / "minerva_production" / "12_kda" / "kda_run_manifest.tsv"
SIGNATURE_MEMBERS = (
    ROOT / "results" / "minerva_production" / "12_kda" / "kda_signature_members.tsv.gz"
)
BACKGROUND_MEMBERS = (
    ROOT / "results" / "minerva_production" / "12_kda" / "kda_background_members.tsv.gz"
)
MSIGDB_C2_CP = ROOT / "data" / "reference" / "msigdb" / "c2.cp.v2026.1.Hs.symbols.gmt"
ANNOTATION = (
    ROOT / "results" / "minerva_production" / "09_annotate_genes" / "gene_annotation_master.tsv.gz"
)
NORMALIZED = ROOT / "results" / "minerva_production" / "05_normalized"
MAST = ROOT / "results" / "minerva_production" / "08_mast"
MAST_FILES = {
    "Astrocytes": [MAST / "astrocytes.yu_mast_de.tsv.gz"],
    "Excitatory_neurons": [
        MAST / "excitatory_set1.yu_mast_de.tsv.gz",
        MAST / "excitatory_set2.yu_mast_de.tsv.gz",
        MAST / "excitatory_set3.yu_mast_de.tsv.gz",
    ],
}
RDS_TO_NETWORK = {
    "astrocytes": "Astrocytes",
    "excitatory_set1": "Excitatory_neurons",
    "excitatory_set2": "Excitatory_neurons",
    "excitatory_set3": "Excitatory_neurons",
}
EXPECTED = {
    "canonical_rows": 95557,
    "included_runs": 161,
    "Excitatory_neurons": {
        "nodes": 10441,
        "edges": 13759,
        "in_degree": 0,
        "out_degree": 9,
        "total_degree": 9,
        "downstream3": 114,
        "core_mito_downstream3": 25,
        "support": 20,
        "usable": 97,
        "aggregate_q": 1.8402234017260841e-09,
        "stability": "14/14",
    },
    "Astrocytes": {
        "nodes": 8285,
        "edges": 8881,
        "in_degree": 1,
        "out_degree": 3,
        "total_degree": 4,
        "downstream3": 106,
        "core_mito_downstream3": 22,
        "support": 3,
        "usable": 20,
        "aggregate_q": 3.440356841520878e-05,
        "stability": "2/3",
    },
}
RECURRENCE_THRESHOLD = {"Excitatory_neurons": 4, "Astrocytes": 2}
PATHWAY_THEMES = (
    {
        "pathway": "KEGG_RIBOSOME",
        "code": "R",
        "label": "Cytosolic ribosome",
        "color": "#6F4E9C",
    },
    {
        "pathway": "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA",
        "code": "O",
        "label": "ETC / oxidative phosphorylation",
        "color": "#0072B2",
    },
    {
        "pathway": "REACTOME_MITOCHONDRIAL_PROTEIN_DEGRADATION",
        "code": "D",
        "label": "Mitochondrial protein degradation",
        "color": "#D55E00",
    },
    {
        "pathway": "REACTOME_CRISTAE_FORMATION",
        "code": "C",
        "label": "Cristae formation",
        "color": "#009E73",
    },
)
RIBOSOMAL_DRIVERS = ("RPL11", "RPLP1", "RPL15", "RPS13", "RPS15", "RPL38")
OKABE_ITO = {
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "black": "#000000",
}
DEG_COLORS = {
    "up_only": OKABE_ITO["vermillion"],
    "down_only": OKABE_ITO["sky"],
    "mixed": OKABE_ITO["yellow"],
    "not_deg": "#D9D9D9",
}
OUTPUT_NAMES = [
    "excitatory/phase18_rpl11_excitatory_consensus_network_nodes.tsv",
    "excitatory/phase18_rpl11_excitatory_consensus_network_edges.tsv",
    "excitatory/phase18_rpl11_excitatory_consensus_pathway_ora.tsv",
    "excitatory/phase18_rpl11_excitatory_consensus_pathway_membership.tsv",
    "phase18_rpl11_deep_dive.png",
    "phase18_rpl11_deep_dive.pdf",
    "phase18_rpl11_deep_dive.svg",
    "phase18_rpl11_ribosomal_comparison.png",
    "phase18_rpl11_ribosomal_comparison.pdf",
    "phase18_rpl11_ribosomal_comparison.svg",
    "phase18_rpl11_query_overlap.png",
    "phase18_rpl11_query_overlap.pdf",
    "phase18_rpl11_query_overlap.svg",
    "phase18_rpl11_nodes.tsv",
    "phase18_rpl11_edges.tsv",
    "phase18_rpl11_layout.tsv",
    "phase18_rpl11_full_three_layer_nodes.tsv",
    "phase18_rpl11_full_three_layer_edges.tsv",
    "excitatory/phase18_rpl11_excitatory.graphml",
    "astrocyte/phase18_rpl11_astrocyte.graphml",
    "phase18_rpl11_run_target_matrix.tsv",
    "phase18_rpl11_run_annotations.tsv",
    "phase18_rpl11_matched_controls.tsv",
    "phase18_rpl11_matched_null_results.tsv",
    "phase18_rpl11_matching_balance.tsv",
    "phase18_rpl11_ribosomal_comparison.tsv",
    "phase18_rpl11_query_hit_membership.tsv",
    "phase18_rpl11_query_overlap_regions.tsv",
    "phase18_rpl11_deep_dive_caption.md",
    "phase18_rpl11_deep_dive_methods.md",
    "phase18_rpl11_deep_dive_checks.tsv",
    "phase18_rpl11_deep_dive_manifest.tsv",
    "phase18_rpl11_deep_dive_status.tsv",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def tokens(value: Any, separator: str = ";") -> list[str]:
    if value is None or str(value).strip() in {"", "NA", "None"}:
        return []
    return [item for item in str(value).split(separator) if item]


def clean(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return "NA" if not math.isfinite(value) else format(value, ".15g")
    return value


def open_text(path: Path):
    return gzip.open(path, "rt", newline="", encoding="utf-8") if path.suffix == ".gz" else path.open("r", newline="", encoding="utf-8")


def iter_tsv(path: Path) -> Iterable[dict[str, str]]:
    require(path.exists(), f"Missing input: {path}")
    with open_text(path) as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def write_tsv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str] | None = None) -> None:
    require(bool(rows), f"Refusing to write empty table: {path.name}")
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field)) for field in fields})
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    require(bool(text.strip()), f"Refusing to write empty text: {path.name}")
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text.rstrip() + "\n", encoding="utf-8")
    tmp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_figure(fig: mpl.figure.Figure, base: Path, dpi: int) -> None:
    for suffix in ("png", "pdf", "svg"):
        print(f"save={base.name}.{suffix}", flush=True)
        kwargs = {"dpi": dpi} if suffix == "png" else {}
        fig.savefig(base.with_suffix(f".{suffix}"), bbox_inches="tight", facecolor="white", **kwargs)
    plt.close(fig)


def check_row(checks: list[dict[str, Any]], check_id: str, passed: bool, observed: Any, expected: Any, message: str, blocking: bool = True) -> None:
    checks.append(
        {
            "schema_version": SCHEMA,
            "check_id": check_id,
            "status": "PASS" if passed else "FAIL",
            "blocking": blocking,
            "observed": observed,
            "expected": expected,
            "message": message,
        }
    )
    if blocking and not passed:
        raise RuntimeError(f"Blocking check failed [{check_id}]: {message}; observed={observed}, expected={expected}")


def load_canonical(checks: list[dict[str, Any]]) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], list[dict[str, str]]]]:
    rpl_rows: list[dict[str, str]] = []
    aggregate: dict[tuple[str, str, str], dict[str, str]] = {}
    rows_by_driver: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    row_count = 0
    run_ids: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    duplicates = 0
    constant_fields = (
        "coverage_fraction",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "conservative_support_count",
        "supporting_fine_cell_type_count",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
        "stability_assessable_repetitions",
        "stability_candidate_fraction",
    )
    for row in iter_tsv(CANONICAL):
        row_count += 1
        run_ids.add(row["kda_run_id"])
        pair = (row["kda_run_id"], row["key_driver"])
        if pair in seen_keys:
            duplicates += 1
        seen_keys.add(pair)
        key = (row["broad_network"], row["key_driver"], row["case_id"])
        previous = aggregate.get(key)
        if previous is None:
            aggregate[key] = row
        else:
            for field in constant_fields:
                require(previous[field] == row[field], f"Aggregate field drift for {key}: {field}")
        if row["key_driver"] == RPL11:
            rpl_rows.append(row)
        if row["key_driver"] in RIBOSOMAL_DRIVERS:
            rows_by_driver[(row["broad_network"], row["key_driver"])].append(row)
    check_row(checks, "canonical_row_count", row_count == EXPECTED["canonical_rows"], row_count, EXPECTED["canonical_rows"], "Canonical Phase 18 row count")
    check_row(checks, "canonical_run_count", len(run_ids) == EXPECTED["included_runs"], len(run_ids), EXPECTED["included_runs"], "Included call_key_drivers runs")
    check_row(checks, "canonical_unique_keys", duplicates == 0, duplicates, 0, "Unique run × tested-driver rows")
    check_row(checks, "rpl11_case", all(row["case_id"] == "non_mt_driver" for row in rpl_rows), sorted({row["case_id"] for row in rpl_rows}), "non_mt_driver", "RPL11 case classification")
    return rpl_rows, aggregate, rows_by_driver


def load_graph(path: Path, network: str, checks: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph(network=network)
    duplicate = self_edges = empty = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 2 or not fields[0] or not fields[1]:
                empty += 1
                continue
            source, target = fields[:2]
            if source == target:
                self_edges += 1
                continue
            if graph.has_edge(source, target):
                duplicate += 1
                continue
            graph.add_edge(source, target)
    expected = EXPECTED[network]
    check_row(checks, f"{network}_node_count", graph.number_of_nodes() == expected["nodes"], graph.number_of_nodes(), expected["nodes"], "Full-network node count")
    check_row(checks, f"{network}_edge_count", graph.number_of_edges() == expected["edges"], graph.number_of_edges(), expected["edges"], "Full-network edge count")
    check_row(checks, f"{network}_dag", nx.is_directed_acyclic_graph(graph), nx.is_directed_acyclic_graph(graph), True, "Bayesian network is acyclic")
    check_row(checks, f"{network}_edge_hygiene", duplicate + self_edges + empty == 0, f"duplicate={duplicate};self={self_edges};empty={empty}", 0, "Input edges require no cleaning")
    return graph


def exact_depths(graph: nx.DiGraph, source: str, cutoff: int, reverse: bool = False) -> dict[int, set[str]]:
    adjacency = graph.predecessors if reverse else graph.successors
    seen = {source}
    frontier = {source}
    result: dict[int, set[str]] = {}
    for depth in range(1, cutoff + 1):
        nxt = {neighbor for node in frontier for neighbor in adjacency(node)} - seen
        result[depth] = nxt
        seen.update(nxt)
        frontier = nxt
    return result


def cumulative_downstream_sizes(graph: nx.DiGraph, gene: str) -> tuple[int, int, int]:
    if gene not in graph:
        return (0, 0, 0)
    seen = {gene}
    frontier = {gene}
    sizes: list[int] = []
    for _ in range(3):
        frontier = {neighbor for node in frontier for neighbor in graph.successors(node)} - seen
        seen.update(frontier)
        sizes.append(len(seen))
    return tuple(sizes)  # includes the driver, matching KDA neighborhood size


def load_annotation_and_expression(checks: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, float]]]:
    nuclei_by_rds: dict[str, int] = {}
    manifest_names = {
        "astrocytes": "Astrocytes.normalization_manifest.tsv",
        "excitatory_set1": "Excitatory_neurons_set1.normalization_manifest.tsv",
        "excitatory_set2": "Excitatory_neurons_set2.normalization_manifest.tsv",
        "excitatory_set3": "Excitatory_neurons_set3.normalization_manifest.tsv",
    }
    for rds_id, filename in manifest_names.items():
        rows = list(iter_tsv(NORMALIZED / filename))
        selected = [row for row in rows if row["artifact"].endswith(".normalized.rds")]
        require(len(selected) == 1, f"Expected one normalized-RDS manifest row for {rds_id}")
        nuclei_by_rds[rds_id] = integer(selected[0]["records"])

    annotation: dict[str, dict[str, Any]] = {}
    accum: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for row in iter_tsv(ANNOTATION):
        gene = row.get("symbol_hgnc_current", "")
        if not gene or gene == "NA":
            continue
        hgnc_name = row.get("hgnc_name", "")
        ribosomal = hgnc_name.lower().startswith("ribosomal protein") and "mitochondrial" not in hgnc_name.lower()
        current = annotation.setdefault(
            gene,
            {
                "is_core_mito": False,
                "is_cytosolic_ribosomal": False,
                "hgnc_name": hgnc_name,
                "mito_tier": row.get("mito_tier", "NA"),
            },
        )
        current["is_core_mito"] = current["is_core_mito"] or truth(row.get("is_mitocarta3"))
        current["is_cytosolic_ribosomal"] = current["is_cytosolic_ribosomal"] or ribosomal
        rds_id = row.get("rds_id", "")
        network = RDS_TO_NETWORK.get(rds_id)
        if network:
            key = (network, gene)
            accum[key][0] += max(number(row.get("total_raw_counts"), 0.0), 0.0)
            accum[key][1] += max(number(row.get("nuclei_detected"), 0.0), 0.0)
    total_nuclei = {
        "Astrocytes": nuclei_by_rds["astrocytes"],
        "Excitatory_neurons": sum(nuclei_by_rds[key] for key in ("excitatory_set1", "excitatory_set2", "excitatory_set3")),
    }
    expression: dict[tuple[str, str], dict[str, float]] = {}
    for (network, gene), (counts, detected) in accum.items():
        total = float(total_nuclei[network])
        expression[(network, gene)] = {
            "total_raw_counts": counts,
            "nuclei_detected": detected,
            "total_nuclei": total,
            "log1p_counts_per_nucleus": math.log1p(counts / total),
            "detected_fraction": min(detected / total, 1.0),
        }
    check_row(checks, "annotation_rpl11", RPL11 in annotation, RPL11 in annotation, True, "RPL11 has Phase 9 annotation")
    check_row(checks, "expression_rpl11", all((network, RPL11) in expression for network in PRIMARY_NETWORKS), sorted(network for network in PRIMARY_NETWORKS if (network, RPL11) in expression), list(PRIMARY_NETWORKS), "RPL11 has expression/detection matching features")
    return annotation, expression


def load_support_membership(rpl_rows: Sequence[dict[str, str]], checks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, set[str]], dict[str, set[str]]]:
    support_rows = [row for row in rpl_rows if truth(row["conservative_support"]) and row["broad_network"] in SELECTED_NETWORKS]
    support_ids = {row["kda_run_id"] for row in support_rows}
    run_manifest = {row["kda_run_id"]: row for row in iter_tsv(RUN_MANIFEST) if row["kda_run_id"] in support_ids}
    signatures: dict[str, set[str]] = {run_id: set() for run_id in support_ids}
    for row in iter_tsv(SIGNATURE_MEMBERS):
        if row["kda_run_id"] in support_ids and truth(row["effective_member"]):
            signatures[row["kda_run_id"]].add(row["gene"])
    backgrounds: dict[str, set[str]] = {run_id: set() for run_id in support_ids}
    for row in iter_tsv(BACKGROUND_MEMBERS):
        if row["kda_run_id"] in support_ids:
            backgrounds[row["kda_run_id"]].add(row["gene"])
    check_row(checks, "support_run_manifest", len(run_manifest) == len(support_ids), len(run_manifest), len(support_ids), "All RPL11 support runs occur in the run manifest")
    check_row(checks, "support_query_nonempty", all(signatures.values()), sum(bool(value) for value in signatures.values()), len(signatures), "All support queries have effective members")
    check_row(checks, "support_background_nonempty", all(backgrounds.values()), sum(bool(value) for value in backgrounds.values()), len(backgrounds), "All support runs have background members")

    membership: list[dict[str, Any]] = []
    for row in sorted(support_rows, key=lambda item: (item["broad_network"], item["signature_direction"], item["fine_cell_type"], item["signature_group"])):
        hit_genes = tokens(row["published_overlap_items"])
        require(hit_genes, f"Support row lacks published overlap items: {row['kda_run_id']}")
        for gene in hit_genes:
            membership.append(
                {
                    "schema_version": SCHEMA,
                    "broad_network": row["broad_network"],
                    "kda_run_id": row["kda_run_id"],
                    "fine_cell_type": row["fine_cell_type"],
                    "signature_group": row["signature_group"],
                    "sex": row["sex"],
                    "apoe_group": row["apoe_group"],
                    "signature_direction": row["signature_direction"],
                    "final_layer": integer(row["final_layer"]),
                    "final_run_q": number(row["final_run_q"]),
                    "hit_gene": gene,
                }
            )
    return membership, run_manifest, signatures, backgrounds


def validate_primary_support_runs(
    rpl_rows: Sequence[dict[str, str]],
    graphs: Mapping[str, nx.DiGraph],
    signatures: Mapping[str, set[str]],
    backgrounds: Mapping[str, set[str]],
    checks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    support_rows = [row for row in rpl_rows if truth(row["conservative_support"]) and row["broad_network"] in PRIMARY_NETWORKS]
    matrix_rows: list[dict[str, Any]] = []
    run_annotations: list[dict[str, Any]] = []
    mismatch = 0
    counters = Counter()
    for index, row in enumerate(sorted(support_rows, key=lambda item: (PRIMARY_NETWORKS.index(item["broad_network"]), item["signature_direction"], item["fine_cell_type"], item["signature_group"])), start=1):
        network = row["broad_network"]
        run_id = row["kda_run_id"]
        background = backgrounds[run_id]
        query = signatures[run_id]
        induced = graphs[network].subgraph(background)
        layer = integer(row["final_layer"])
        lengths = nx.single_source_shortest_path_length(induced, RPL11, cutoff=layer) if RPL11 in induced else {}
        neighborhood = set(lengths)
        overlap = neighborhood & query
        published = set(tokens(row["published_overlap_items"]))
        fold = (len(overlap) * len(background) / len(neighborhood) / len(query)) if neighborhood and query else 0.0
        raw_p = float(hypergeom.sf(len(overlap) - 1, len(background), len(neighborhood), len(query))) if overlap else 1.0
        same = (
            overlap == published
            and len(overlap) == integer(row["final_overlap_count"])
            and len(neighborhood) == integer(row["final_neighborhood_size"])
            and abs(fold - number(row["final_fold_enrichment"])) <= 0.011
            and math.isclose(raw_p, number(row["final_raw_p"]), rel_tol=1e-8, abs_tol=1e-300)
        )
        mismatch += int(not same)
        counters[(network, layer)] += 1
        code = f"{NETWORK_SHORT[network]}{sum(1 for ann in run_annotations if ann['broad_network'] == network) + 1:02d}"
        run_annotations.append(
            {
                "schema_version": SCHEMA,
                "run_code": code,
                "kda_run_id": run_id,
                "broad_network": network,
                "fine_cell_type": row["fine_cell_type"],
                "signature_group": row["signature_group"],
                "sex": row["sex"],
                "apoe_group": row["apoe_group"],
                "signature_direction": row["signature_direction"],
                "final_layer": layer,
                "other_query_overlap": integer(row["other_query_overlap"]),
                "final_fold_enrichment": number(row["final_fold_enrichment"]),
                "final_run_q": number(row["final_run_q"]),
            }
        )
        for gene in sorted(overlap):
            matrix_rows.append(
                {
                    "schema_version": SCHEMA,
                    "run_code": code,
                    "kda_run_id": run_id,
                    "broad_network": network,
                    "hit_gene": gene,
                    "minimum_directed_depth": lengths[gene],
                }
            )
    check_row(checks, "primary_support_count", len(support_rows) == 23, len(support_rows), 23, "Primary-network conservative-support rows")
    check_row(checks, "primary_run_reconstruction", mismatch == 0, mismatch, 0, "Run-specific query hits, neighborhoods, fold enrichment, and raw P reproduce canonical rows")
    observed_layers = {
        "Excitatory_neurons": f"L2={counters[('Excitatory_neurons', 2)]};L3={counters[('Excitatory_neurons', 3)]}",
        "Astrocytes": f"L2={counters[('Astrocytes', 2)]};L3={counters[('Astrocytes', 3)]}",
    }
    check_row(checks, "support_layer_distribution", observed_layers == {"Excitatory_neurons": "L2=1;L3=19", "Astrocytes": "L2=2;L3=1"}, observed_layers, "Exc L2=1/L3=19; Ast L2=2/L3=1", "Supporting-run final-layer distribution")
    return matrix_rows, run_annotations


def load_deg(display_genes: Mapping[str, set[str]]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"up": 0, "down": 0, "contrasts": set()})
    for network, paths in MAST_FILES.items():
        wanted = display_genes[network]
        for path in paths:
            for row in iter_tsv(path):
                gene = row["gene"]
                if gene not in wanted or not truth(row["paper_deg"]):
                    continue
                direction = "up" if number(row["logFC"]) > 0 else "down"
                result[(network, gene)][direction] += 1
                result[(network, gene)]["contrasts"].add(row["contrast_id"])
    for value in result.values():
        if value["up"] and value["down"]:
            value["class"] = "mixed"
        elif value["up"]:
            value["class"] = "up_only"
        elif value["down"]:
            value["class"] = "down_only"
        else:
            value["class"] = "not_deg"
    return result


def build_network_tables(
    graphs: Mapping[str, nx.DiGraph],
    membership: Sequence[dict[str, Any]],
    annotation: Mapping[str, dict[str, Any]],
    checks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, nx.DiGraph], dict[str, dict[str, tuple[float, float]]], dict[str, set[str]]]:
    recurrence: dict[tuple[str, str], int] = Counter((row["broad_network"], row["hit_gene"]) for row in membership if row["broad_network"] in PRIMARY_NETWORKS)
    contexts: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: {"fine": set(), "groups": set(), "directions": set()})
    for row in membership:
        key = (row["broad_network"], row["hit_gene"])
        contexts[key]["fine"].add(row["fine_cell_type"])
        contexts[key]["groups"].add(row["signature_group"])
        contexts[key]["directions"].add(row["signature_direction"])

    display_graphs: dict[str, nx.DiGraph] = {}
    complete_graphs: dict[str, nx.DiGraph] = {}
    display_genes: dict[str, set[str]] = {}
    path_counts: dict[tuple[str, str], int] = Counter()
    roles: dict[tuple[str, str], str] = {}
    up_depth_all: dict[tuple[str, str], int] = {}
    down_depth_all: dict[tuple[str, str], int] = {}

    for network, graph in graphs.items():
        downstream = exact_depths(graph, RPL11, 3)
        upstream = exact_depths(graph, RPL11, 3, reverse=True)
        expected = EXPECTED[network]
        cumulative = set().union(*downstream.values())
        core_count = sum(bool(annotation.get(gene, {}).get("is_core_mito")) for gene in cumulative)
        check_row(checks, f"{network}_rpl11_indegree", graph.in_degree(RPL11) == expected["in_degree"], graph.in_degree(RPL11), expected["in_degree"], "RPL11 full-network in-degree")
        check_row(checks, f"{network}_rpl11_outdegree", graph.out_degree(RPL11) == expected["out_degree"], graph.out_degree(RPL11), expected["out_degree"], "RPL11 full-network out-degree")
        check_row(checks, f"{network}_rpl11_totaldegree", graph.degree(RPL11) == expected["total_degree"], graph.degree(RPL11), expected["total_degree"], "RPL11 full-network total degree")
        check_row(checks, f"{network}_downstream3", len(cumulative) == expected["downstream3"], len(cumulative), expected["downstream3"], "Downstream genes through layer 3")
        check_row(checks, f"{network}_core_mito_downstream3", core_count == expected["core_mito_downstream3"], core_count, expected["core_mito_downstream3"], "Core MitoCarta downstream genes through layer 3")
        if network == "Astrocytes":
            check_row(checks, "astro_upstream_chain", upstream[1] == {"RPLP1"} and upstream[2] == {"RPS25"} and not upstream[3], {d: sorted(v) for d, v in upstream.items()}, "RPLP1 at U1; RPS25 at U2", "Recorded astrocyte upstream chain")
        else:
            check_row(checks, "exc_no_upstream", not set().union(*upstream.values()), {d: sorted(v) for d, v in upstream.items()}, "none", "No recorded excitatory upstream parents")

        full_nodes = {RPL11} | cumulative | upstream[1] | upstream[2]
        complete_graph = graph.subgraph(full_nodes).copy()
        complete_graphs[network] = complete_graph

        targets = {gene for (net, gene), count in recurrence.items() if net == network and count >= RECURRENCE_THRESHOLD[network]}
        nodes = {RPL11} | upstream[1] | upstream[2]
        edges: set[tuple[str, str]] = set()
        for target in targets:
            distance = nx.shortest_path_length(graph, RPL11, target)
            require(distance <= 3, f"Retained target lies beyond layer 3: {network}/{target}")
            for path in nx.all_shortest_paths(graph, RPL11, target):
                if len(path) - 1 <= 3:
                    nodes.update(path)
                    edges.update(zip(path, path[1:]))
                    for gene in path:
                        path_counts[(network, gene)] += 1
        for depth in (2, 1):
            for node in upstream[depth]:
                for target in graph.successors(node):
                    if target in nodes and (target in upstream.get(depth - 1, set()) or target == RPL11):
                        edges.add((node, target))
        display = nx.DiGraph(network=network)
        display.add_nodes_from(nodes)
        display.add_edges_from(edges)
        display_graphs[network] = display
        display_genes[network] = nodes
        for depth, genes in upstream.items():
            for gene in genes:
                up_depth_all[(network, gene)] = depth
        for depth, genes in downstream.items():
            for gene in genes:
                down_depth_all[(network, gene)] = depth
        for gene in nodes:
            roles[(network, gene)] = "driver" if gene == RPL11 else ("upstream" if (network, gene) in up_depth_all else "downstream")

    deg = load_deg(display_genes)
    nodes_rows: list[dict[str, Any]] = []
    edges_rows: list[dict[str, Any]] = []
    full_nodes_rows: list[dict[str, Any]] = []
    full_edges_rows: list[dict[str, Any]] = []
    layouts: dict[str, dict[str, tuple[float, float]]] = {}

    for network in PRIMARY_NETWORKS:
        graph = graphs[network]
        display = display_graphs[network]
        positions = signed_depth_layout(display, up_depth_all, down_depth_all, network)
        layouts[network] = positions
        support_denominator = EXPECTED[network]["support"]
        for gene in sorted(display.nodes):
            info = annotation.get(gene, {})
            evidence = deg.get((network, gene), {"up": 0, "down": 0, "class": "not_deg", "contrasts": set()})
            key = (network, gene)
            nodes_rows.append(
                {
                    "schema_version": SCHEMA,
                    "network": network,
                    "gene": gene,
                    "minimum_upstream_depth": up_depth_all.get(key),
                    "minimum_downstream_depth": down_depth_all.get(key),
                    "network_role": roles[key],
                    "is_rpl11": gene == RPL11,
                    "is_upstream_context": roles[key] == "upstream",
                    "is_core_mitocarta": bool(info.get("is_core_mito")),
                    "is_cytosolic_ribosomal": bool(info.get("is_cytosolic_ribosomal")),
                    "is_required_intermediate": roles[key] == "downstream" and recurrence.get(key, 0) == 0,
                    "supporting_run_count": recurrence.get(key, 0),
                    "supporting_run_fraction": recurrence.get(key, 0) / support_denominator,
                    "supporting_fine_cell_type_count": len(contexts[key]["fine"]),
                    "supporting_groups": "|".join(sorted(contexts[key]["groups"])),
                    "supporting_directions": "|".join(sorted(contexts[key]["directions"])),
                    "phase08_paper_deg_any": evidence["up"] + evidence["down"] > 0,
                    "phase08_up_count": evidence["up"],
                    "phase08_down_count": evidence["down"],
                    "phase08_deg_class": evidence["class"],
                    "in_degree_full": graph.in_degree(gene),
                    "out_degree_full": graph.out_degree(gene),
                    "total_degree_full": graph.degree(gene),
                    "local_display_degree": display.degree(gene),
                    "shortest_path_count_from_rpl11": path_counts.get(key, 0),
                    "x": positions[gene][0],
                    "y": positions[gene][1],
                }
            )
        for source, target in sorted(display.edges):
            edges_rows.append(
                {
                    "schema_version": SCHEMA,
                    "network": network,
                    "source": source,
                    "target": target,
                    "source_upstream_depth": up_depth_all.get((network, source)),
                    "target_upstream_depth": up_depth_all.get((network, target)),
                    "source_downstream_depth": down_depth_all.get((network, source), 0 if source == RPL11 else None),
                    "target_downstream_depth": down_depth_all.get((network, target)),
                    "on_retained_shortest_path": roles[(network, source)] != "upstream",
                    "is_upstream_context_edge": roles[(network, source)] == "upstream",
                }
            )
        complete = complete_graphs[network]
        for gene in sorted(complete.nodes):
            full_nodes_rows.append(
                {
                    "schema_version": SCHEMA,
                    "network": network,
                    "gene": gene,
                    "minimum_upstream_depth": up_depth_all.get((network, gene)),
                    "minimum_downstream_depth": down_depth_all.get((network, gene), 0 if gene == RPL11 else None),
                    "is_core_mitocarta": bool(annotation.get(gene, {}).get("is_core_mito")),
                    "in_degree_full": graph.in_degree(gene),
                    "out_degree_full": graph.out_degree(gene),
                }
            )
        for source, target in sorted(complete.edges):
            full_edges_rows.append({"schema_version": SCHEMA, "network": network, "source": source, "target": target})
        for gene in complete.nodes:
            complete.nodes[gene].update(
                {
                    "network": network,
                    "minimum_upstream_depth": str(up_depth_all.get((network, gene), "NA")),
                    "minimum_downstream_depth": str(down_depth_all.get((network, gene), 0 if gene == RPL11 else "NA")),
                    "is_core_mitocarta": str(bool(annotation.get(gene, {}).get("is_core_mito"))),
                    "is_rpl11": str(gene == RPL11),
                }
            )
    return nodes_rows, edges_rows, full_nodes_rows, full_edges_rows, complete_graphs, layouts, display_genes


def signed_depth_layout(graph: nx.DiGraph, upstream: Mapping[tuple[str, str], int], downstream: Mapping[tuple[str, str], int], network: str) -> dict[str, tuple[float, float]]:
    groups: dict[int, list[str]] = defaultdict(list)
    for gene in graph.nodes:
        if gene == RPL11:
            signed = 0
        elif (network, gene) in upstream:
            signed = -upstream[(network, gene)]
        else:
            signed = downstream[(network, gene)]
        groups[signed].append(gene)
    positions: dict[str, tuple[float, float]] = {RPL11: (0.0, 0.0)}
    for depth, genes in sorted(groups.items()):
        if depth == 0:
            continue
        def key(gene: str) -> tuple[float, str]:
            linked = list(graph.predecessors(gene)) if depth > 0 else list(graph.successors(gene))
            values = [positions[item][1] for item in linked if item in positions]
            return (statistics.fmean(values) if values else 0.0, gene)
        ordered = sorted(genes, key=key)
        span = max(2.5, 0.78 * (len(ordered) - 1))
        ys = np.linspace(-span / 2, span / 2, len(ordered)) if len(ordered) > 1 else [0.0]
        for gene, y in zip(ordered, ys):
            positions[gene] = (float(depth), float(y))
    return positions


def build_excitatory_consensus_tables(
    graph: nx.DiGraph,
    rpl_rows: Sequence[dict[str, str]],
    backgrounds: Mapping[str, set[str]],
    membership: Sequence[dict[str, Any]],
    annotation: Mapping[str, dict[str, Any]],
    checks: list[dict[str, Any]],
) -> tuple[nx.DiGraph, list[dict[str, Any]], list[dict[str, Any]], dict[str, tuple[float, float]]]:
    """Build a readable union of the 20 supporting excitatory RPL11 neighborhoods."""
    network = "Excitatory_neurons"
    support_rows = [
        row
        for row in rpl_rows
        if row["broad_network"] == network and truth(row["conservative_support"])
    ]
    require(len(support_rows) == EXPECTED[network]["support"], "Unexpected excitatory support count")

    # A node occurs in a run when it belongs to that run's induced, selected-layer
    # RPL11 neighborhood. This is deliberately distinct from being a query hit.
    neighborhood_occurrence: Counter[str] = Counter()
    for row in support_rows:
        induced = graph.subgraph(backgrounds[row["kda_run_id"]])
        layer = integer(row["final_layer"])
        lengths = nx.single_source_shortest_path_length(induced, RPL11, cutoff=layer)
        neighborhood_occurrence.update(lengths.keys())

    query_hit_occurrence: Counter[str] = Counter(
        row["hit_gene"]
        for row in membership
        if row["broad_network"] == network
    )
    retained_hits = {
        gene
        for gene, count in query_hit_occurrence.items()
        if count >= RECURRENCE_THRESHOLD[network]
    }

    direct_in = set(graph.predecessors(RPL11))
    direct_out = set(graph.successors(RPL11))
    path_nodes = {RPL11}
    for target in retained_hits:
        for path in nx.all_shortest_paths(graph, RPL11, target):
            if len(path) - 1 <= 3:
                path_nodes.update(path)
    display_nodes = path_nodes | direct_in | direct_out
    display = graph.subgraph(display_nodes).copy()

    check_row(
        checks,
        "exc_consensus_all_direct_in",
        set(display.predecessors(RPL11)) == direct_in,
        sorted(display.predecessors(RPL11)),
        sorted(direct_in),
        "Standalone consensus includes every full-network edge into RPL11",
    )
    check_row(
        checks,
        "exc_consensus_all_direct_out",
        set(display.successors(RPL11)) == direct_out,
        sorted(display.successors(RPL11)),
        sorted(direct_out),
        "Standalone consensus includes every full-network edge out of RPL11",
    )
    check_row(
        checks,
        "exc_consensus_direct_degree",
        (len(direct_in), len(direct_out)) == (0, 9),
        f"in={len(direct_in)};out={len(direct_out)}",
        "in=0;out=9",
        "Fixed excitatory RPL11 direct-degree anchor",
    )

    depths = nx.single_source_shortest_path_length(graph, RPL11, cutoff=3)
    upstream_depths = nx.single_source_shortest_path_length(graph.reverse(copy=False), RPL11, cutoff=2)
    positions = consensus_layered_layout(display, depths, upstream_depths)
    deg = load_deg({"Excitatory_neurons": set(display.nodes), "Astrocytes": set()})
    support_n = len(support_rows)

    node_rows: list[dict[str, Any]] = []
    for gene in sorted(display.nodes):
        reasons: list[str] = []
        if gene == RPL11:
            reasons.append("driver")
        if gene in direct_in:
            reasons.append("all_direct_incoming")
        if gene in direct_out:
            reasons.append("all_direct_outgoing")
        if gene in retained_hits:
            reasons.append("recurrent_query_hit")
        if gene in path_nodes and gene not in retained_hits and gene != RPL11:
            reasons.append("shortest_path_connector")
        evidence = deg.get((network, gene), {"up": 0, "down": 0, "class": "not_deg"})
        occurrence = neighborhood_occurrence.get(gene, 0)
        hit_count = query_hit_occurrence.get(gene, 0)
        node_rows.append(
            {
                "schema_version": SCHEMA,
                "network": network,
                "gene": gene,
                "included_reason": "|".join(reasons),
                "directed_depth_from_rpl11": depths.get(gene),
                "upstream_depth_to_rpl11": upstream_depths.get(gene) if gene != RPL11 else None,
                "is_direct_incoming_neighbor": gene in direct_in,
                "is_direct_outgoing_neighbor": gene in direct_out,
                "supporting_neighborhood_occurrence_count": occurrence,
                "supporting_neighborhood_occurrence_fraction": occurrence / support_n,
                "query_hit_occurrence_count": hit_count,
                "query_hit_occurrence_fraction": hit_count / support_n,
                "query_hit_display_threshold": RECURRENCE_THRESHOLD[network],
                "is_recurrent_query_hit": gene in retained_hits,
                "is_core_mitocarta": bool(annotation.get(gene, {}).get("is_core_mito")),
                "is_cytosolic_ribosomal": bool(annotation.get(gene, {}).get("is_cytosolic_ribosomal")),
                "phase08_deg_class": evidence["class"],
                "phase08_up_count": evidence["up"],
                "phase08_down_count": evidence["down"],
                "in_degree_full": graph.in_degree(gene),
                "out_degree_full": graph.out_degree(gene),
                "in_degree_display": display.in_degree(gene),
                "out_degree_display": display.out_degree(gene),
                "x": positions[gene][0],
                "y": positions[gene][1],
            }
        )

    edge_rows: list[dict[str, Any]] = []
    for source, target in sorted(display.edges):
        edge_rows.append(
            {
                "schema_version": SCHEMA,
                "network": network,
                "source": source,
                "target": target,
                "is_directly_incident_to_rpl11": source == RPL11 or target == RPL11,
                "source_directed_depth": depths.get(source),
                "target_directed_depth": depths.get(target),
                "source_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(source, 0),
                "target_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(target, 0),
            }
        )

    check_row(
        checks,
        "exc_consensus_occurrence_range",
        all(0 <= row["supporting_neighborhood_occurrence_count"] <= support_n for row in node_rows),
        f"min={min(row['supporting_neighborhood_occurrence_count'] for row in node_rows)};max={max(row['supporting_neighborhood_occurrence_count'] for row in node_rows)}",
        f"0..{support_n}",
        "Node recurrence counts are bounded by the 20 supporting runs",
    )
    return display, node_rows, edge_rows, positions


def build_excitatory_pathway_tables(
    graph: nx.DiGraph,
    node_rows: Sequence[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Run offline custom-background ORA and map selected pathway representatives."""
    gene_sets: list[dict[str, Any]] = []
    with MSIGDB_C2_CP.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            require(len(fields) >= 3, "Malformed MSigDB GMT row")
            gene_sets.append({"pathway": fields[0], "url": fields[1], "genes": set(fields[2:])})
    check_row(
        checks,
        "msigdb_c2_cp_pathway_count",
        len(gene_sets) == 4115,
        len(gene_sets),
        4115,
        "MSigDB C2:CP v2026.1 Hs pathway count",
    )

    annotated_universe = set().union(*(row["genes"] for row in gene_sets))
    background = set(graph.nodes) & annotated_universe
    displayed = {row["gene"] for row in node_rows}
    query = displayed & background
    check_row(checks, "pathway_background_size", len(background) == 6952, len(background), 6952, "Full excitatory-network genes represented in MSigDB C2:CP")
    check_row(checks, "pathway_query_mapped", len(query) == 34, len(query), 34, "Displayed genes represented in MSigDB C2:CP")

    rows: list[dict[str, Any]] = []
    n_background = len(background)
    n_query = len(query)
    for gene_set in gene_sets:
        members = gene_set["genes"] & background
        if not 15 <= len(members) <= 500:
            continue
        overlap = query & members
        raw_p = float(hypergeom.sf(len(overlap) - 1, n_background, len(members), n_query)) if overlap else 1.0
        fold_enrichment = (len(overlap) / n_query) / (len(members) / n_background) if overlap else 0.0
        rows.append(
            {
                "schema_version": SCHEMA,
                "library": "MSigDB C2:CP v2026.1 Hs symbols",
                "pathway": gene_set["pathway"],
                "pathway_url": gene_set["url"],
                "background_definition": "all excitatory Bayesian-network genes represented in MSigDB C2:CP",
                "background_gene_count": n_background,
                "displayed_mapped_gene_count": n_query,
                "pathway_background_gene_count": len(members),
                "overlap_gene_count": len(overlap),
                "overlap_genes": ";".join(sorted(overlap)),
                "fold_enrichment": fold_enrichment,
                "raw_hypergeometric_p": raw_p,
            }
        )
    check_row(checks, "pathway_eligible_test_count", len(rows) == 1739, len(rows), 1739, "Pathways tested after 15–500 background-gene size filter")

    order = sorted(range(len(rows)), key=lambda index: rows[index]["raw_hypergeometric_p"])
    adjusted = [1.0] * len(rows)
    running = 1.0
    for reverse_index in range(len(order) - 1, -1, -1):
        row_index = order[reverse_index]
        rank = reverse_index + 1
        running = min(running, rows[row_index]["raw_hypergeometric_p"] * len(rows) / rank)
        adjusted[row_index] = min(running, 1.0)
    theme_by_pathway = {theme["pathway"]: theme for theme in PATHWAY_THEMES}
    for index, row in enumerate(rows):
        row["bh_fdr"] = adjusted[index]
        theme = theme_by_pathway.get(row["pathway"])
        row["selected_representative"] = theme is not None
        row["pathway_code"] = theme["code"] if theme else None
        row["pathway_display_label"] = theme["label"] if theme else None
        row["pathway_color"] = theme["color"] if theme else None
        row["selection_rule"] = "nonredundant representative with BH FDR < 0.05 and at least 3 displayed genes" if theme else None
    rows.sort(key=lambda row: (row["raw_hypergeometric_p"], row["pathway"]))

    selected_rows = {row["pathway"]: row for row in rows if truth(row["selected_representative"])}
    check_row(checks, "pathway_representatives_present", set(selected_rows) == set(theme_by_pathway), sorted(selected_rows), sorted(theme_by_pathway), "All declared pathway representatives occur in the tested collection")
    expected_overlaps = {
        "KEGG_RIBOSOME": 14,
        "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA": 12,
        "REACTOME_MITOCHONDRIAL_PROTEIN_DEGRADATION": 5,
        "REACTOME_CRISTAE_FORMATION": 3,
    }
    check_row(
        checks,
        "pathway_representative_overlap_counts",
        {name: selected_rows[name]["overlap_gene_count"] for name in expected_overlaps} == expected_overlaps,
        {name: selected_rows[name]["overlap_gene_count"] for name in expected_overlaps},
        expected_overlaps,
        "Selected representative pathway overlap counts",
    )
    check_row(
        checks,
        "pathway_representatives_fdr",
        all(selected_rows[name]["bh_fdr"] < 0.05 for name in expected_overlaps),
        {name: selected_rows[name]["bh_fdr"] for name in expected_overlaps},
        "all < 0.05",
        "Selected representative pathways pass BH FDR < 0.05",
    )

    membership_rows: list[dict[str, Any]] = []
    membership_by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for theme in PATHWAY_THEMES:
        result = selected_rows[theme["pathway"]]
        overlap = set(tokens(result["overlap_genes"]))
        for gene in sorted(overlap):
            record = {
                "schema_version": SCHEMA,
                "network": "Excitatory_neurons",
                "gene": gene,
                "pathway": theme["pathway"],
                "pathway_code": theme["code"],
                "pathway_display_label": theme["label"],
                "pathway_color": theme["color"],
                "pathway_url": result["pathway_url"],
                "pathway_background_gene_count": result["pathway_background_gene_count"],
                "display_overlap_gene_count": result["overlap_gene_count"],
                "raw_hypergeometric_p": result["raw_hypergeometric_p"],
                "bh_fdr": result["bh_fdr"],
            }
            membership_rows.append(record)
            membership_by_gene[gene].append(record)
    for gene in membership_by_gene:
        membership_by_gene[gene].sort(key=lambda row: next(i for i, theme in enumerate(PATHWAY_THEMES) if theme["pathway"] == row["pathway"]))
    check_row(checks, "pathway_membership_row_count", len(membership_rows) == 34, len(membership_rows), 34, "Selected pathway gene-membership rows")
    check_row(checks, "pathway_annotated_display_gene_count", len(membership_by_gene) == 29, len(membership_by_gene), 29, "Displayed genes carrying at least one selected pathway outline")
    return rows, membership_rows, membership_by_gene


def consensus_layered_layout(
    graph: nx.DiGraph,
    downstream_depths: Mapping[str, int],
    upstream_depths: Mapping[str, int],
) -> dict[str, tuple[float, float]]:
    """Deterministic layered layout with two visual lanes for a crowded depth 3."""
    groups: dict[int, list[str]] = defaultdict(list)
    for gene in graph.nodes:
        if gene == RPL11:
            continue
        if gene in downstream_depths:
            groups[downstream_depths[gene]].append(gene)
        elif gene in upstream_depths:
            groups[-upstream_depths[gene]].append(gene)
    positions: dict[str, tuple[float, float]] = {RPL11: (0.0, 0.0)}
    x_centers = {-2: -1.75, -1: -1.05, 1: 1.15, 2: 2.35, 3: 3.65}
    for depth in sorted(groups):
        genes = groups[depth]

        def parent_key(gene: str) -> tuple[float, str]:
            linked = graph.predecessors(gene) if depth > 0 else graph.successors(gene)
            parent_y = [positions[node][1] for node in linked if node in positions]
            return (statistics.fmean(parent_y) if parent_y else 0.0, gene)

        ordered = sorted(genes, key=parent_key)
        lane_count = 2 if depth == 3 and len(ordered) > 9 else 1
        lanes = [ordered[index::lane_count] for index in range(lane_count)]
        for lane_index, lane in enumerate(lanes):
            span = 1.55 * (len(lane) - 1)
            ys = np.linspace(-span / 2, span / 2, len(lane)) if len(lane) > 1 else [0.0]
            x = x_centers.get(depth, float(depth)) + (0.72 * lane_index if lane_count > 1 else 0.0)
            for gene, y in zip(lane, ys):
                positions[gene] = (float(x), float(y))
    return positions


def robust_scale_matrix(rows: Sequence[dict[str, Any]], features: Sequence[str]) -> tuple[np.ndarray, dict[str, tuple[float, float]]]:
    raw = np.asarray([[float(row[field]) for field in features] for row in rows], dtype=float)
    params: dict[str, tuple[float, float]] = {}
    scaled = np.zeros_like(raw)
    for index, field in enumerate(features):
        values = raw[:, index]
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median))) * 1.4826
        if not math.isfinite(mad) or mad <= 1e-12:
            q75, q25 = np.percentile(values, [75, 25])
            mad = float((q75 - q25) / 1.349)
        if not math.isfinite(mad) or mad <= 1e-12:
            mad = 1.0
        scaled[:, index] = (values - median) / mad
        params[field] = (median, mad)
    return scaled, params


def build_feature_rows(
    aggregate: Mapping[tuple[str, str, str], dict[str, str]],
    graphs: Mapping[str, nx.DiGraph],
    expression: Mapping[tuple[str, str], dict[str, float]],
    annotation: Mapping[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (network, gene, case_id), row in aggregate.items():
        if network not in PRIMARY_NETWORKS or case_id != "non_mt_driver":
            continue
        p_value = number(row["aggregate_acat_p"])
        coverage = number(row["coverage_fraction"])
        if not math.isfinite(p_value) or not math.isfinite(coverage) or coverage < 0.80 or gene not in graphs[network]:
            continue
        layer1, layer2, layer3 = cumulative_downstream_sizes(graphs[network], gene)
        exp = expression.get((network, gene), {})
        output[network].append(
            {
                "network": network,
                "gene": gene,
                "aggregate_acat_p": p_value,
                "aggregate_acat_q": number(row["aggregate_acat_q"]),
                "coverage_fraction": coverage,
                "conservative_support_count": integer(row["conservative_support_count"]),
                "supporting_fine_cell_type_count": integer(row["supporting_fine_cell_type_count"]),
                "stability_candidate_fraction": number(row["stability_candidate_fraction"]),
                "out_degree": graphs[network].out_degree(gene),
                "total_degree": graphs[network].degree(gene),
                "layer1_size": layer1,
                "layer2_size": layer2,
                "layer3_size": layer3,
                "log_layer1_size": math.log1p(layer1),
                "log_layer2_size": math.log1p(layer2),
                "log_layer3_size": math.log1p(layer3),
                "log1p_counts_per_nucleus": exp.get("log1p_counts_per_nucleus", math.nan),
                "detected_fraction": exp.get("detected_fraction", math.nan),
                "is_cytosolic_ribosomal": bool(annotation.get(gene, {}).get("is_cytosolic_ribosomal")),
            }
        )
    return output


def match_one(
    network: str,
    target_gene: str,
    pool_rows: Sequence[dict[str, Any]],
    null_model: str,
    max_controls: int = 250,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    target = next(row for row in pool_rows if row["gene"] == target_gene)
    features_a = ["out_degree", "total_degree", "log_layer1_size", "log_layer2_size", "log_layer3_size", "coverage_fraction"]
    features_b = features_a + ["log1p_counts_per_nucleus", "detected_fraction"]
    features = features_a if null_model == "topology" else features_b
    candidates = [row for row in pool_rows if row["gene"] != target_gene]
    if null_model == "ribosomal":
        candidates = [row for row in candidates if row["is_cytosolic_ribosomal"]]
    candidates = [row for row in candidates if all(math.isfinite(float(row[field])) for field in features)]
    require(all(math.isfinite(float(target[field])) for field in features), f"Target matching features missing: {network}/{target_gene}/{null_model}")
    combined = [target, *candidates]
    scaled, params = robust_scale_matrix(combined, features)
    distances = np.sqrt(np.sum((scaled[1:] - scaled[0]) ** 2, axis=1))
    order = np.argsort(distances, kind="stable")[: min(max_controls, len(candidates))]
    selected: list[dict[str, Any]] = []
    for rank, idx in enumerate(order, start=1):
        row = candidates[int(idx)]
        caliper = (
            abs(row["out_degree"] - target["out_degree"]) <= 1
            and abs(row["total_degree"] - target["total_degree"]) <= 2
            and abs(row["log_layer3_size"] - target["log_layer3_size"]) <= 0.25
            and (
                null_model == "topology"
                or (
                    abs((row["log1p_counts_per_nucleus"] - params["log1p_counts_per_nucleus"][0]) / params["log1p_counts_per_nucleus"][1] - (target["log1p_counts_per_nucleus"] - params["log1p_counts_per_nucleus"][0]) / params["log1p_counts_per_nucleus"][1]) <= 0.5
                    and abs(row["detected_fraction"] - target["detected_fraction"]) <= 0.10
                )
            )
        )
        selected.append(
            {
                "schema_version": SCHEMA,
                "network": network,
                "target_gene": target_gene,
                "null_model": null_model,
                "control_rank": rank,
                "control_gene": row["gene"],
                "matching_distance": float(distances[int(idx)]),
                "caliper_pass": caliper,
                "control_aggregate_acat_p": row["aggregate_acat_p"],
                "control_conservative_support_count": row["conservative_support_count"],
                "control_supporting_fine_cell_type_count": row["supporting_fine_cell_type_count"],
                "control_is_cytosolic_ribosomal": row["is_cytosolic_ribosomal"],
                **{f"target_{field}": target[field] for field in features},
                **{f"control_{field}": row[field] for field in features},
            }
        )
    n_extreme = sum(row["aggregate_acat_p"] <= target["aggregate_acat_p"] for row in (candidates[int(idx)] for idx in order))
    empirical = (1 + n_extreme) / (1 + len(selected)) if selected else math.nan
    caliper_rows = [row for row in selected if row["caliper_pass"]]
    caliper_extreme = sum(float(row["control_aggregate_acat_p"]) <= target["aggregate_acat_p"] for row in caliper_rows)
    caliper_empirical = (1 + caliper_extreme) / (1 + len(caliper_rows)) if caliper_rows else math.nan
    result = {
        "schema_version": SCHEMA,
        "network": network,
        "target_gene": target_gene,
        "null_model": null_model,
        "available_pool_n": len(candidates),
        "matched_control_n": len(selected),
        "caliper_control_n": sum(row["caliper_pass"] for row in selected),
        "target_aggregate_acat_p": target["aggregate_acat_p"],
        "target_conservative_support_count": target["conservative_support_count"],
        "target_supporting_fine_cell_type_count": target["supporting_fine_cell_type_count"],
        "empirical_tail_p": empirical,
        "caliper_empirical_tail_p": caliper_empirical,
        "interpretation": "descriptive" if len(selected) < 20 else "empirical",
    }
    balance: list[dict[str, Any]] = []
    for field in features:
        control_values = [float(row[f"control_{field}"]) for row in selected]
        difference = abs(float(target[field]) - statistics.median(control_values)) / params[field][1] if control_values else math.nan
        balance.append(
            {
                "schema_version": SCHEMA,
                "network": network,
                "target_gene": target_gene,
                "null_model": null_model,
                "feature": field,
                "target_value": target[field],
                "control_median": statistics.median(control_values) if control_values else math.nan,
                "source_median": params[field][0],
                "source_robust_scale": params[field][1],
                "absolute_standardized_difference": difference,
                "balance_status": "balanced" if math.isfinite(difference) and difference <= 0.5 else "residual_difference",
            }
        )
    result["matching_balance_status"] = "balanced" if all(row["balance_status"] == "balanced" for row in balance) else "residual_difference"
    return selected, result, balance


def build_matched_nulls(feature_rows: Mapping[str, list[dict[str, Any]]], checks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    controls: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    balance: list[dict[str, Any]] = []
    for network in PRIMARY_NETWORKS:
        pool = feature_rows[network]
        require(any(row["gene"] == RPL11 for row in pool), f"RPL11 absent from matching universe: {network}")
        for null_model in ("topology", "topology_expression", "ribosomal"):
            selected, result, rows = match_one(network, RPL11, pool, null_model)
            controls.extend(selected)
            results.append(result)
            balance.extend(rows)
    unique = len({(row["network"], row["null_model"], row["control_gene"]) for row in controls}) == len(controls)
    check_row(checks, "matched_controls_unique", unique, unique, True, "No duplicated controls within network/null model")
    check_row(checks, "matched_nulls_complete", len(results) == 6, len(results), 6, "Three null models for each primary network")
    check_row(checks, "ribosomal_null_annotation", all(row["control_gene"] != RPL11 and row["control_is_cytosolic_ribosomal"] for row in controls if row["null_model"] == "ribosomal"), True, True, "Ribosomal null contains curated cytosolic-ribosomal controls and excludes RPL11")
    return controls, results, balance


def build_query_regions(membership: Sequence[dict[str, Any]], checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sets: dict[tuple[str, str], set[str]] = defaultdict(set)
    run_counts: Counter[tuple[str, str]] = Counter()
    seen_run_direction: set[tuple[str, str, str]] = set()
    for row in membership:
        network = row["broad_network"]
        direction = row["signature_direction"].replace("_mito", "")
        sets[(network, direction)].add(row["hit_gene"])
        key = (network, direction, row["kda_run_id"])
        if key not in seen_run_direction:
            run_counts[(network, direction)] += 1
            seen_run_direction.add(key)
    regions: list[dict[str, Any]] = []
    for network in SELECTED_NETWORKS:
        up = sets[(network, "AD_up")]
        down = sets[(network, "AD_down")]
        categories = (
            ("AD-up only", up - down),
            ("Shared", up & down),
            ("AD-down only", down - up),
        )
        for region, genes in categories:
            regions.append(
                {
                    "schema_version": SCHEMA,
                    "broad_network": network,
                    "region": region,
                    "gene_count": len(genes),
                    "genes": ";".join(sorted(genes)),
                    "ad_up_supporting_query_count": run_counts[(network, "AD_up")],
                    "ad_down_supporting_query_count": run_counts[(network, "AD_down")],
                    "ad_up_union_gene_count": len(up),
                    "ad_down_union_gene_count": len(down),
                }
            )
    observed = {
        (row["broad_network"], row["region"]): row["gene_count"]
        for row in regions
    }
    expected = {
        ("Excitatory_neurons", "AD-up only"): 1,
        ("Excitatory_neurons", "Shared"): 20,
        ("Excitatory_neurons", "AD-down only"): 4,
        ("Astrocytes", "AD-up only"): 0,
        ("Astrocytes", "Shared"): 6,
        ("Astrocytes", "AD-down only"): 6,
        ("Microglia", "AD-up only"): 0,
        ("Microglia", "Shared"): 0,
        ("Microglia", "AD-down only"): 5,
        ("Oligodendrocytes", "AD-up only"): 0,
        ("Oligodendrocytes", "Shared"): 0,
        ("Oligodendrocytes", "AD-down only"): 4,
    }
    check_row(checks, "query_overlap_regions", all(observed[key] == value for key, value in expected.items()), {str(key): observed[key] for key in expected}, {str(key): value for key, value in expected.items()}, "Direction-level Venn and one-set counts")
    return regions


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else math.nan


def build_ribosomal_comparison(
    graphs: Mapping[str, nx.DiGraph],
    aggregate: Mapping[tuple[str, str, str], dict[str, str]],
    rows_by_driver: Mapping[tuple[str, str], list[dict[str, str]]],
    feature_rows: Mapping[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, set[str]]], dict[str, dict[str, set[str]]]]:
    neighborhoods: dict[str, dict[str, set[str]]] = defaultdict(dict)
    hits: dict[str, dict[str, set[str]]] = defaultdict(dict)
    output: list[dict[str, Any]] = []
    feature_by_gene = {network: {row["gene"]: row for row in rows} for network, rows in feature_rows.items()}
    for network in PRIMARY_NETWORKS:
        graph = graphs[network]
        for driver in RIBOSOMAL_DRIVERS:
            lengths = nx.single_source_shortest_path_length(graph, driver, cutoff=3) if driver in graph else {}
            neighborhoods[network][driver] = set(lengths) - {driver}
            driver_rows = rows_by_driver.get((network, driver), [])
            hits[network][driver] = {
                gene
                for row in driver_rows
                if truth(row["conservative_support"])
                for gene in tokens(row["published_overlap_items"])
            }
            agg = aggregate.get((network, driver, "non_mt_driver"))
            empirical = math.nan
            matched_n = 0
            if driver in feature_by_gene[network]:
                _, result, _ = match_one(network, driver, feature_rows[network], "topology_expression")
                empirical = result["empirical_tail_p"]
                matched_n = result["matched_control_n"]
            output.append(
                {
                    "schema_version": SCHEMA,
                    "record_type": "driver_summary",
                    "network": network,
                    "driver_a": driver,
                    "driver_b": "NA",
                    "neighborhood_jaccard": "NA",
                    "query_hit_jaccard": "NA",
                    "downstream_three_layer_gene_count": len(neighborhoods[network][driver]),
                    "query_hit_gene_count": len(hits[network][driver]),
                    "aggregate_acat_p": number(agg["aggregate_acat_p"]) if agg else math.nan,
                    "aggregate_acat_q": number(agg["aggregate_acat_q"]) if agg else math.nan,
                    "conservative_support_count": integer(agg["conservative_support_count"]) if agg else 0,
                    "terminal_candidate_status": agg["terminal_candidate_status"] if agg else "not_tested",
                    "topology_expression_matched_n": matched_n,
                    "topology_expression_empirical_tail_p": empirical,
                    "query_hit_genes": ";".join(sorted(hits[network][driver])),
                }
            )
        for driver_a in RIBOSOMAL_DRIVERS:
            for driver_b in RIBOSOMAL_DRIVERS:
                output.append(
                    {
                        "schema_version": SCHEMA,
                        "record_type": "pairwise_jaccard",
                        "network": network,
                        "driver_a": driver_a,
                        "driver_b": driver_b,
                        "neighborhood_jaccard": jaccard(neighborhoods[network][driver_a], neighborhoods[network][driver_b]),
                        "query_hit_jaccard": jaccard(hits[network][driver_a], hits[network][driver_b]),
                    }
                )
    return output, neighborhoods, hits


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.titlesize": 10,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7.5,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def panel_label(ax: mpl.axes.Axes, label: str) -> None:
    ax.text(-0.055, 1.035, label, transform=ax.transAxes, fontsize=13, fontweight="bold", va="bottom", ha="right")


def draw_locator(ax: mpl.axes.Axes, graph: nx.DiGraph, local_nodes: set[str], seed: int) -> None:
    inset = ax.inset_axes([0.80, 0.70, 0.18, 0.20])
    generations = list(nx.topological_generations(graph))
    positions: dict[str, tuple[float, float]] = {}
    rng = np.random.default_rng(seed)
    for x, generation in enumerate(generations):
        ordered = sorted(generation)
        ys = np.linspace(-1, 1, len(ordered)) if len(ordered) > 1 else np.array([0.0])
        if len(ordered) > 2:
            ys = ys[rng.permutation(len(ordered))]
        for gene, y in zip(ordered, ys):
            positions[gene] = (x / max(len(generations) - 1, 1), float(y))
    segments = [[positions[source], positions[target]] for source, target in graph.edges]
    collection = mpl.collections.LineCollection(segments, colors="#BDBDBD", linewidths=0.12, alpha=0.10, rasterized=True)
    inset.add_collection(collection)
    xy = np.asarray([positions[node] for node in graph.nodes])
    inset.scatter(xy[:, 0], xy[:, 1], s=0.15, color="#A6A6A6", alpha=0.22, rasterized=True)
    selected = np.asarray([positions[node] for node in local_nodes])
    inset.scatter(selected[:, 0], selected[:, 1], s=1.4, color=OKABE_ITO["orange"], alpha=0.75, rasterized=True)
    inset.scatter(*positions[RPL11], s=13, marker="*", color="black", zorder=4)
    inset.set_xlim(-0.03, 1.03)
    inset.set_ylim(-1.06, 1.06)
    inset.set_xticks([])
    inset.set_yticks([])
    inset.set_title("Full-network locator", fontsize=6.5, pad=1)
    for spine in inset.spines.values():
        spine.set_color("#BDBDBD")
        spine.set_linewidth(0.5)


def draw_network_panel(
    ax: mpl.axes.Axes,
    network: str,
    graph: nx.DiGraph,
    node_rows: Sequence[dict[str, Any]],
    edge_rows: Sequence[dict[str, Any]],
    positions: Mapping[str, tuple[float, float]],
    local_graph: nx.DiGraph,
) -> None:
    row_by_gene = {row["gene"]: row for row in node_rows if row["network"] == network}
    for edge in [row for row in edge_rows if row["network"] == network]:
        source, target = edge["source"], edge["target"]
        color = "#969696" if edge["is_upstream_context_edge"] else "#5B5B5B"
        style = "--" if edge["is_upstream_context_edge"] else "-"
        arrow = FancyArrowPatch(
            positions[source],
            positions[target],
            arrowstyle="-|>",
            mutation_scale=8,
            color=color,
            linewidth=0.75,
            linestyle=style,
            shrinkA=9,
            shrinkB=9,
            zorder=1,
            alpha=0.82,
        )
        ax.add_patch(arrow)
    for gene in sorted(local_graph.nodes, key=lambda item: (row_by_gene[item]["network_role"] != "driver", item)):
        row = row_by_gene[gene]
        degree = row["local_display_degree"]
        if gene == RPL11:
            size, color, marker, edgecolor = 950, "#111111", "o", "#111111"
        else:
            size = min(600, 190 + 62 * math.sqrt(max(degree, 1)))
            color = "white" if row["network_role"] == "upstream" else DEG_COLORS[row["phase08_deg_class"]]
            marker = "s" if row["is_cytosolic_ribosomal"] else "o"
            edgecolor = "#202020" if row["supporting_run_count"] > 0 else "#777777"
        linewidth = 2.0 if row["supporting_run_count"] > 0 else (1.4 if row["is_cytosolic_ribosomal"] else 0.8)
        ax.scatter(*positions[gene], s=size, c=[color], marker=marker, edgecolors=edgecolor, linewidths=linewidth, zorder=3)
        if row["supporting_run_count"] > 0:
            ax.scatter(*positions[gene], s=size * 1.20, facecolors="none", edgecolors="#000000", linewidths=0.65 + 1.4 * row["supporting_run_fraction"], zorder=2)
        label = gene
        if row["supporting_run_count"] > 0:
            label += f"\n{row['supporting_run_count']}/{EXPECTED[network]['support']}"
        fontsize = min(8.3, 5.3 + 0.45 * math.sqrt(max(degree, 1)))
        ax.text(*positions[gene], label, ha="center", va="center", fontsize=fontsize, color="white" if gene == RPL11 else "#111111", fontweight="bold" if gene == RPL11 or row["supporting_run_count"] > 0 else "normal", zorder=4, linespacing=0.9)
    depths = [row["minimum_downstream_depth"] for row in row_by_gene.values() if row["minimum_downstream_depth"] not in (None, "NA")]
    max_y = max(abs(y) for _, y in positions.values()) + 1.2
    for depth in range(1, 4):
        ax.axvline(depth, color="#EEEEEE", linewidth=0.5, zorder=0)
        ax.text(depth, max_y - 0.72, f"D{depth}", color="#777777", fontsize=7, ha="center", va="top")
    if network == "Astrocytes":
        ax.axvspan(-2.4, -0.55, color="#F7F7F7", zorder=-2)
        ax.text(-1.5, max_y - 0.18, "Upstream context\n(not used in KDA enrichment)", fontsize=6.8, ha="center", va="top", color="#666666")
    else:
        ax.text(0.02, 0.04, "No recorded upstream parents", transform=ax.transAxes, fontsize=7, color="#666666", va="bottom")
    agg_q = EXPECTED[network]["aggregate_q"]
    info = f"Support {EXPECTED[network]['support']}/{EXPECTED[network]['usable']} usable runs  |  aggregate q={agg_q:.2e}  |  stability {EXPECTED[network]['stability']}"
    if network == "Excitatory_neurons":
        info += "\n19/20 supporting runs selected layer 3"
    ax.text(0.01, 0.99, info, transform=ax.transAxes, ha="left", va="top", fontsize=7.2, bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#BDBDBD", "alpha": 0.93})
    draw_locator(ax, graph, set(local_graph.nodes), 18 if network == "Excitatory_neurons" else 19)
    x_values = [x for x, _ in positions.values()]
    ax.set_xlim(min(x_values) - 0.7, max(x_values) + 1.7)
    ax.set_ylim(-max_y, max_y)
    ax.set_title(f"{NETWORK_LABELS[network]}: RPL11-rooted directed subnetwork", loc="left", fontweight="bold", pad=8)
    ax.axis("off")


def matrix_array(matrix_rows: Sequence[dict[str, Any]], run_annotations: Sequence[dict[str, Any]], network: str | None = None, binary: bool = False) -> tuple[np.ndarray, list[str], list[str], list[dict[str, Any]]]:
    annotations = [row for row in run_annotations if network is None or row["broad_network"] == network]
    run_codes = [row["run_code"] for row in annotations]
    genes = sorted({row["hit_gene"] for row in matrix_rows if row["run_code"] in run_codes}, key=lambda gene: (-sum(row["hit_gene"] == gene and row["run_code"] in run_codes for row in matrix_rows), gene))
    lookup = {(row["hit_gene"], row["run_code"]): row["minimum_directed_depth"] for row in matrix_rows}
    array = np.zeros((len(genes), len(run_codes)), dtype=int)
    for i, gene in enumerate(genes):
        for j, code in enumerate(run_codes):
            value = lookup.get((gene, code), 0)
            array[i, j] = int(value > 0) if binary else value
    return array, genes, run_codes, annotations


def plot_depth_matrix(ax: mpl.axes.Axes, matrix_rows: Sequence[dict[str, Any]], annotations: Sequence[dict[str, Any]]) -> None:
    array, genes, codes, anns = matrix_array(matrix_rows, annotations)
    cmap = ListedColormap(["#FFFFFF", "#E5F5F9", "#99D8C9", "#2CA25F"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    image = ax.imshow(array, aspect="auto", interpolation="none", cmap=cmap, norm=norm)
    ax.set_xticks(range(len(codes)), codes, rotation=90)
    ax.set_yticks(range(len(genes)), genes)
    ax.tick_params(length=0, pad=1)
    ax.set_title("Supporting run × mitochondrial query-hit depth", loc="left", fontweight="bold")
    for j, ann in enumerate(anns):
        color = OKABE_ITO["orange"] if ann["signature_direction"].startswith("AD_up") else OKABE_ITO["blue"]
        ax.add_patch(mpl.patches.Rectangle((j - 0.5, -1.05), 1, 0.32, transform=ax.transData, facecolor=color, edgecolor="none", clip_on=False))
    cbar = plt.colorbar(image, ax=ax, fraction=0.025, pad=0.015, ticks=[0, 1, 2, 3])
    cbar.ax.set_yticklabels(["Absent", "D1", "D2", "D3"])
    cbar.set_label("First directed depth", fontsize=7)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)


def plot_matched_null(ax: mpl.axes.Axes, controls: Sequence[dict[str, Any]], results: Sequence[dict[str, Any]]) -> None:
    labels: list[str] = []
    positions: list[tuple[str, str]] = []
    for network in PRIMARY_NETWORKS:
        for null_model in ("topology", "topology_expression", "ribosomal"):
            labels.append(f"{NETWORK_SHORT[network]}\n{ {'topology':'Topology','topology_expression':'Topo.+expr.','ribosomal':'Ribosomal'}[null_model] }")
            positions.append((network, null_model))
    rng = np.random.default_rng(1802)
    for x, (network, null_model) in enumerate(positions):
        rows = [row for row in controls if row["network"] == network and row["null_model"] == null_model]
        values = [-math.log10(max(float(row["control_aggregate_acat_p"]), 1e-300)) for row in rows]
        jitter = rng.normal(0, 0.055, len(values))
        ax.scatter(x + jitter, values, s=10, color="#8C8C8C", alpha=0.38, edgecolors="none", rasterized=True)
        result = next(row for row in results if row["network"] == network and row["null_model"] == null_model)
        observed = -math.log10(max(float(result["target_aggregate_acat_p"]), 1e-300))
        ax.scatter(x, observed, marker="D", s=48, color="black", zorder=4)
        balance_label = "balanced" if result["matching_balance_status"] == "balanced" else "residual"
        alignment = "left" if x == 0 else ("right" if x == len(positions) - 1 else "center")
        ax.text(x, observed + 0.35, f"P={result['empirical_tail_p']:.3g}; n={result['matched_control_n']}\n{balance_label}", ha=alignment, va="bottom", fontsize=5.8)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_ylabel("−log10 aggregate ACAT P")
    ax.set_title("Matched-control specificity", loc="left", fontweight="bold")
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    observed_max = max(-math.log10(max(float(row["target_aggregate_acat_p"]), 1e-300)) for row in results)
    ax.set_ylim(-0.7, observed_max + 2.2)
    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#8C8C8C", markersize=5, label="Matched controls"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor="black", markersize=5, label="RPL11"),
    ]
    ax.legend(handles=legend, frameon=False, loc="lower right")


def consensus_node_diameter(occurrence: int) -> float:
    """Marker diameter in points; area therefore increases monotonically with recurrence."""
    return 32.0 + 1.2 * occurrence


def plot_excitatory_consensus_network(
    out: Path,
    dpi: int,
    graph: nx.DiGraph,
    node_rows: Sequence[dict[str, Any]],
    edge_rows: Sequence[dict[str, Any]],
    positions: Mapping[str, tuple[float, float]],
    checks: list[dict[str, Any]],
    pathway_membership: Mapping[str, Sequence[dict[str, Any]]] | None = None,
) -> None:
    """Render the standalone, recurrence-scaled version of former Panel A."""
    pathway_mode = pathway_membership is not None
    fig = plt.figure(figsize=(12.5, 11.0), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[4.7, 1.3], wspace=0.03)
    ax = fig.add_subplot(grid[0, 0])
    key = fig.add_subplot(grid[0, 1])
    row_by_gene = {row["gene"]: row for row in node_rows}
    diameters = {
        gene: consensus_node_diameter(integer(row_by_gene[gene]["supporting_neighborhood_occurrence_count"]))
        for gene in graph.nodes
    }

    y_values = [value[1] for value in positions.values()]
    y_pad = 1.1
    y_min, y_max = min(y_values) - y_pad, max(y_values) + y_pad
    ax.axvspan(-1.35, -0.25, color="#F5F5F5", zorder=-3)
    ax.text(-0.80, 0.8, "Incoming to RPL11\nnone recorded", ha="center", va="center", fontsize=8, color="#666666")
    for x, label in ((1.15, "D1"), (2.35, "D2"), (4.00, "D3")):
        ax.axvline(x, color="#E5E5E5", linewidth=0.7, zorder=-2)
        ax.text(x, y_max - 0.20, label, ha="center", va="top", fontsize=9, fontweight="bold", color="#6A6A6A")

    for edge in edge_rows:
        source, target = edge["source"], edge["target"]
        direct = truth(edge["is_directly_incident_to_rpl11"])
        arrow = FancyArrowPatch(
            positions[source],
            positions[target],
            arrowstyle="-|>",
            mutation_scale=10 if direct else 8,
            color="#303030" if direct else "#777777",
            linewidth=1.45 if direct else 0.72,
            shrinkA=diameters[source] / 2 + 1.5,
            shrinkB=diameters[target] / 2 + 1.5,
            alpha=0.90 if direct else 0.68,
            zorder=1,
            connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arrow)

    text_artists: list[tuple[mpl.text.Text, str, str, float]] = []
    for gene in sorted(graph.nodes, key=lambda item: (item == RPL11, row_by_gene[item]["directed_depth_from_rpl11"] or 0, item)):
        row = row_by_gene[gene]
        occurrence = integer(row["supporting_neighborhood_occurrence_count"])
        diameter = diameters[gene]
        marker = "s" if truth(row["is_cytosolic_ribosomal"]) and gene != RPL11 else "o"
        if gene == RPL11:
            facecolor, edgecolor, label_color = "#111111", "#111111", "white"
        else:
            facecolor = DEG_COLORS[row["phase08_deg_class"]]
            edgecolor, label_color = "#555555", "#111111"
        ax.scatter(
            *positions[gene],
            s=diameter**2,
            marker=marker,
            c=[facecolor],
            edgecolors=edgecolor,
            linewidths=1.15,
            zorder=3,
        )
        if truth(row["is_recurrent_query_hit"]):
            ax.scatter(
                *positions[gene],
                s=(diameter + 6.0) ** 2,
                marker=marker,
                facecolors="none",
                edgecolors="#000000",
                linewidths=1.25,
                zorder=2,
            )
        fontsize = 8.6 if len(gene) >= 7 else 9.0
        label = f"{gene}\n{occurrence}/20"
        artist = ax.text(
            *positions[gene],
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            linespacing=0.88,
            color=label_color,
            fontweight="bold" if gene == RPL11 or truth(row["is_recurrent_query_hit"]) else "normal",
            zorder=4,
        )
        text_artists.append((artist, gene, marker, diameter))
        if pathway_mode:
            memberships = list(pathway_membership.get(gene, []))
            vertical_offsets = [(index - (len(memberships) - 1) / 2) * 17.25 for index in range(len(memberships))]
            depth = integer(row["directed_depth_from_rpl11"], -1)
            if gene == RPL11:
                badge_side = -1.0
            elif depth == 3:
                badge_side = 1.0 if positions[gene][0] > 4.0 else -1.0
            else:
                badge_side = 1.0
            for vertical_offset, membership_row in zip(vertical_offsets, memberships):
                code = membership_row["pathway_code"]
                ax.annotate(
                    code,
                    xy=positions[gene],
                    xytext=(badge_side * (diameter / 2 + 12.0), vertical_offset),
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    fontsize=10.5,
                    fontweight="bold",
                    color="white" if code != "R" else "#111111",
                    bbox={
                        "boxstyle": "circle,pad=0.35",
                        "fc": membership_row["pathway_color"],
                        "ec": "white",
                        "lw": 0.7,
                    },
                    zorder=6,
                )

    ax.set_xlim(-1.40, 4.80)
    ax.set_ylim(y_min, y_max)
    ax.set_title(
        "Excitatory neurons: RPL11 consensus directed neighborhood across 20 supporting runs"
        + (" with pathway membership" if pathway_mode else ""),
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax.text(
        -0.80,
        y_min + 0.35,
        "All direct RPL11 edges\n0 incoming  |  9 outgoing\nDeeper mitochondrial hits: ≥4/20",
        ha="center",
        va="bottom",
        fontsize=7.4,
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#BDBDBD", "alpha": 0.96},
    )
    ax.axis("off")

    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.axis("off")
    key.text(0.02, 0.97, "How to read", fontsize=11, fontweight="bold", va="top")
    key.text(0.02, 0.91, "Node size", fontsize=8.5, fontweight="bold", va="top")
    key.text(0.02, 0.875, "Runs containing the node in the\nselected RPL11 neighborhood", fontsize=7.2, va="top", color="#555555")
    for y, count in zip((0.77, 0.66, 0.53), (8, 14, 20)):
        key.scatter(0.18, y, s=consensus_node_diameter(count) ** 2, facecolors="#D9D9D9", edgecolors="#555555", linewidths=1.0)
        key.text(0.48, y, f"{count}/20 runs", fontsize=7.6, va="center")

    if pathway_mode:
        key.text(0.02, 0.445, "Selected pathway badges", fontsize=8.5, fontweight="bold", va="top")
        for index, theme in enumerate(PATHWAY_THEMES):
            y = 0.405 - 0.038 * index
            key.text(
                0.065,
                y,
                theme["code"],
                ha="center",
                va="center",
                fontsize=10.8,
                fontweight="bold",
                color="white" if theme["code"] != "R" else "#111111",
                bbox={"boxstyle": "circle,pad=0.35", "fc": theme["color"], "ec": "white", "lw": 0.9},
            )
            key.text(0.16, y, theme["label"], fontsize=6.8, va="center")
        key.text(0.02, 0.247, "No badge = no membership in these four\nselected representatives", fontsize=6.2, color="#555555", va="top")
        encoding_title_y = 0.190
        encoding_legend_y = 0.175
        edge_key_y = 0.030
    else:
        encoding_title_y = 0.425
        encoding_legend_y = 0.395
        edge_key_y = 0.075
    key.text(0.02, encoding_title_y, "Node encoding", fontsize=8.5, fontweight="bold", va="top")
    encoding_handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor="white", markeredgecolor="#333333", markersize=9, label="Cytosolic ribosomal protein"),
        Line2D([0], [0], marker="o", color="black", markerfacecolor="white", markeredgewidth=2, markersize=9, label="Recurrent mitochondrial hit"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["mixed"], markeredgecolor="#555555", markersize=9, label="Direct DEG in both directions"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["down_only"], markeredgecolor="#555555", markersize=9, label="Direct DEG: AD-down only"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["up_only"], markeredgecolor="#555555", markersize=9, label="Direct DEG: AD-up only"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["not_deg"], markeredgecolor="#555555", markersize=9, label="No stored direct DEG"),
    ]
    key.legend(handles=encoding_handles, loc="upper left", bbox_to_anchor=(-0.02, encoding_legend_y), frameon=False, fontsize=6.6 if pathway_mode else 7.0, handletextpad=0.8, labelspacing=0.76 if pathway_mode else 1.05)
    if not pathway_mode:
        key.annotate("", xy=(0.37, edge_key_y), xytext=(0.05, edge_key_y), arrowprops={"arrowstyle": "-|>", "color": "#303030", "lw": 1.45})
        key.text(0.48, edge_key_y, "All edges directly incident\nto RPL11", fontsize=7.0, va="center")
    key.text(0.02, 0.006, "D1–D3 = minimum downstream distance", fontsize=6.6, color="#555555", va="bottom")

    fig.suptitle(
        "Phase 18 RPL11 excitatory-neuron network recurrence"
        + (" and pathway membership" if pathway_mode else ""),
        fontsize=15,
        fontweight="bold",
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_violations: list[str] = []
    pixels_per_point = fig.dpi / 72.0
    for artist, gene, marker, diameter in text_artists:
        bbox = artist.get_window_extent(renderer=renderer)
        center = ax.transData.transform(positions[gene])
        half_width = max(abs(bbox.x0 - center[0]), abs(bbox.x1 - center[0]))
        half_height = max(abs(bbox.y0 - center[1]), abs(bbox.y1 - center[1]))
        radius = diameter * pixels_per_point / 2.0
        fits = (
            math.hypot(half_width, half_height) <= radius - 1.0
            if marker == "o"
            else max(half_width, half_height) <= radius - 1.0
        )
        if not fits:
            label_violations.append(gene)
    check_row(
        checks,
        "exc_consensus_pathway_labels_inside_nodes" if pathway_mode else "exc_consensus_labels_inside_nodes",
        not label_violations,
        ";".join(label_violations) if label_violations else "none",
        "none",
        "Every gene symbol and recurrence label fits within its circle or box",
    )
    save_figure(
        fig,
        out / ("phase18_rpl11_excitatory_consensus_network_pathways" if pathway_mode else "phase18_rpl11_excitatory_consensus_network"),
        dpi,
    )


def plot_deep_dive(
    out: Path,
    dpi: int,
    graphs: Mapping[str, nx.DiGraph],
    display_graphs: Mapping[str, nx.DiGraph],
    node_rows: Sequence[dict[str, Any]],
    edge_rows: Sequence[dict[str, Any]],
    layouts: Mapping[str, Mapping[str, tuple[float, float]]],
    matrix_rows: Sequence[dict[str, Any]],
    run_annotations: Sequence[dict[str, Any]],
    controls: Sequence[dict[str, Any]],
    null_results: Sequence[dict[str, Any]],
) -> None:
    fig = plt.figure(figsize=(12.0, 9.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.04, 1.0], width_ratios=[1.15, 0.85])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    draw_network_panel(axes[0], "Excitatory_neurons", graphs["Excitatory_neurons"], node_rows, edge_rows, layouts["Excitatory_neurons"], display_graphs["Excitatory_neurons"])
    print("plot_deep_dive=panel_A", flush=True)
    draw_network_panel(axes[1], "Astrocytes", graphs["Astrocytes"], node_rows, edge_rows, layouts["Astrocytes"], display_graphs["Astrocytes"])
    print("plot_deep_dive=panel_B", flush=True)
    plot_depth_matrix(axes[2], matrix_rows, run_annotations)
    print("plot_deep_dive=panel_C", flush=True)
    plot_matched_null(axes[3], controls, null_results)
    print("plot_deep_dive=panel_D", flush=True)
    for label, ax in zip("ABCD", axes):
        panel_label(ax, label)
    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["up_only"], markeredgecolor="#777777", markersize=8, label="Direct DEG: AD-up only"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["down_only"], markeredgecolor="#777777", markersize=8, label="Direct DEG: AD-down only"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["mixed"], markeredgecolor="#777777", markersize=8, label="Direct DEG: both directions"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DEG_COLORS["not_deg"], markeredgecolor="#777777", markersize=8, label="No stored direct DEG"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="white", markeredgecolor="#333333", markersize=8, label="Cytosolic ribosomal protein"),
        Line2D([0], [0], marker="o", color="black", markerfacecolor="white", markeredgewidth=2, markersize=8, label="Recurrent mitochondrial query hit"),
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.015), ncol=6, frameon=False)
    fig.suptitle("Phase 18 RPL11 network evidence: upstream context, downstream mitochondrial modules, and specificity", fontsize=14, fontweight="bold")
    save_figure(fig, out / "phase18_rpl11_deep_dive", dpi)


def draw_venn(ax: mpl.axes.Axes, network: str, regions: Sequence[dict[str, Any]]) -> None:
    values = {row["region"]: row for row in regions if row["broad_network"] == network}
    up_only = values["AD-up only"]["gene_count"]
    shared = values["Shared"]["gene_count"]
    down_only = values["AD-down only"]["gene_count"]
    up_runs = values["Shared"]["ad_up_supporting_query_count"]
    down_runs = values["Shared"]["ad_down_supporting_query_count"]
    if network == "Astrocytes":
        ax.add_patch(Circle((0.18, 0), 0.95, facecolor=OKABE_ITO["blue"], alpha=0.32, edgecolor=OKABE_ITO["blue"], linewidth=2))
        ax.add_patch(Circle((-0.12, 0), 0.60, facecolor=OKABE_ITO["orange"], alpha=0.42, edgecolor=OKABE_ITO["orange"], linewidth=2))
        ax.text(-0.20, 0, str(shared), fontsize=18, fontweight="bold", ha="center", va="center")
        ax.text(0.72, 0, str(down_only), fontsize=18, fontweight="bold", ha="center", va="center")
        ax.text(-1.05, -0.90, f"AD-up only = {up_only}", fontsize=8, ha="center", va="center", color="#777777")
    else:
        ax.add_patch(Circle((-0.36, 0), 0.90, facecolor=OKABE_ITO["orange"], alpha=0.35, edgecolor=OKABE_ITO["orange"], linewidth=2))
        ax.add_patch(Circle((0.36, 0), 0.90, facecolor=OKABE_ITO["blue"], alpha=0.35, edgecolor=OKABE_ITO["blue"], linewidth=2))
        ax.text(-0.86, 0, str(up_only), fontsize=18, fontweight="bold", ha="center", va="center")
        ax.text(0, 0, str(shared), fontsize=18, fontweight="bold", ha="center", va="center")
        ax.text(0.86, 0, str(down_only), fontsize=18, fontweight="bold", ha="center", va="center")
    ax.text(-0.78, 1.0, f"AD-up union\n{values['AD-up only']['ad_up_union_gene_count']} genes from {up_runs} queries", color=OKABE_ITO["vermillion"], ha="center", va="bottom", fontweight="bold")
    ax.text(0.78, 1.0, f"AD-down union\n{values['AD-down only']['ad_down_union_gene_count']} genes from {down_runs} queries", color=OKABE_ITO["blue"], ha="center", va="bottom", fontweight="bold")
    ax.text(0, -1.05, "Counts are unique RPL11 mitochondrial query-hit genes\n(circle areas are not proportional)", ha="center", va="top", fontsize=7, color="#666666")
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.35, 1.45)
    ax.set_aspect("equal")
    ax.set_title(NETWORK_LABELS[network], loc="left", fontweight="bold")
    ax.axis("off")


def plot_binary_matrix(ax: mpl.axes.Axes, matrix_rows: Sequence[dict[str, Any]], annotations: Sequence[dict[str, Any]], network: str, title: str) -> None:
    array, genes, codes, anns = matrix_array(matrix_rows, annotations, network=network, binary=True)
    cmap = ListedColormap(["#FFFFFF", "#222222"])
    ax.imshow(array, aspect="auto", interpolation="none", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(codes)), codes, rotation=90)
    ax.set_yticks(range(len(genes)), genes)
    ax.tick_params(length=0, pad=1)
    ax.set_title(title, loc="left", fontweight="bold", pad=15)
    for j, ann in enumerate(anns):
        color = OKABE_ITO["orange"] if ann["signature_direction"].startswith("AD_up") else OKABE_ITO["blue"]
        ax.add_patch(mpl.patches.Rectangle((j - 0.5, -1.0), 1, 0.28, transform=ax.transData, facecolor=color, edgecolor="none", clip_on=False))
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)


def plot_query_overlap(
    out: Path,
    dpi: int,
    regions: Sequence[dict[str, Any]],
    membership: Sequence[dict[str, Any]],
    matrix_rows: Sequence[dict[str, Any]],
    run_annotations: Sequence[dict[str, Any]],
) -> None:
    fig = plt.figure(figsize=(10.5, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[0.82, 1.18], width_ratios=[1.2, 0.8])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    draw_venn(axes[0], "Excitatory_neurons", regions)
    draw_venn(axes[1], "Astrocytes", regions)
    plot_binary_matrix(axes[2], matrix_rows, run_annotations, "Excitatory_neurons", "Exact membership across 20 excitatory supporting queries")
    plot_binary_matrix(axes[3], matrix_rows, run_annotations, "Astrocytes", "Exact membership across 3 astrocyte supporting queries")
    mic = sorted({row["hit_gene"] for row in membership if row["broad_network"] == "Microglia"})
    oli = sorted({row["hit_gene"] for row in membership if row["broad_network"] == "Oligodendrocytes"})
    axes[3].text(1.05, 0.55, "Single-query summaries", transform=axes[3].transAxes, fontweight="bold", fontsize=8.5, va="top")
    axes[3].text(1.05, 0.46, f"Microglia, AD-down (1 query; {len(mic)} hits)\n" + ", ".join(mic), transform=axes[3].transAxes, fontsize=7, va="top", wrap=True, bbox={"boxstyle": "round,pad=0.3", "fc": "#F5F5F5", "ec": "#BDBDBD"})
    axes[3].text(1.05, 0.21, f"Oligodendrocytes, AD-down (1 query; {len(oli)} hits)\n" + ", ".join(oli), transform=axes[3].transAxes, fontsize=7, va="top", wrap=True, bbox={"boxstyle": "round,pad=0.3", "fc": "#F5F5F5", "ec": "#BDBDBD"})
    for label, ax in zip("ABCD", axes):
        panel_label(ax, label)
    fig.suptitle("RPL11-supporting mitochondrial queries: shared and context-specific network hits", fontsize=14, fontweight="bold")
    save_figure(fig, out / "phase18_rpl11_query_overlap", dpi)


def heatmap(ax: mpl.axes.Axes, data: np.ndarray, labels: Sequence[str], title: str) -> None:
    cmap = mpl.colormaps["cividis"].copy()
    cmap.set_bad("#E6E6E6")
    image = ax.imshow(data, vmin=0, vmax=1, cmap=cmap, interpolation="none")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = data[i, j]
            label = "NA" if not math.isfinite(value) else f"{value:.2f}"
            ax.text(j, i, label, ha="center", va="center", fontsize=6.2, color="white" if math.isfinite(value) and value < 0.42 else "black")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.tick_params(length=0)
    plt.colorbar(image, ax=ax, fraction=0.045, pad=0.02, label="Jaccard index")


def plot_ribosomal_comparison(
    out: Path,
    dpi: int,
    comparison: Sequence[dict[str, Any]],
    neighborhoods: Mapping[str, Mapping[str, set[str]]],
    hits: Mapping[str, Mapping[str, set[str]]],
) -> None:
    fig = plt.figure(figsize=(12.0, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.15])
    axes = [fig.add_subplot(grid[i, j]) for i in range(2) for j in range(3)]
    for row_index, network in enumerate(PRIMARY_NETWORKS):
        neigh = np.asarray([[jaccard(neighborhoods[network][a], neighborhoods[network][b]) for b in RIBOSOMAL_DRIVERS] for a in RIBOSOMAL_DRIVERS])
        hit = np.asarray([[jaccard(hits[network][a], hits[network][b]) for b in RIBOSOMAL_DRIVERS] for a in RIBOSOMAL_DRIVERS])
        heatmap(axes[row_index * 3], neigh, RIBOSOMAL_DRIVERS, f"{NETWORK_LABELS[network]}: three-layer neighborhoods")
        heatmap(axes[row_index * 3 + 1], hit, RIBOSOMAL_DRIVERS, f"{NETWORK_LABELS[network]}: mitochondrial query hits")
        summaries = [row for row in comparison if row.get("record_type") == "driver_summary" and row["network"] == network]
        y = np.arange(len(RIBOSOMAL_DRIVERS))
        p_values = []
        sizes = []
        colors = []
        empirical = []
        for driver in RIBOSOMAL_DRIVERS:
            row = next(item for item in summaries if item["driver_a"] == driver)
            p_values.append(-math.log10(max(float(row["aggregate_acat_p"]), 1e-300)) if math.isfinite(number(row["aggregate_acat_p"])) else 0.0)
            sizes.append(35 + 18 * int(row["conservative_support_count"]))
            colors.append("black" if driver == RPL11 else OKABE_ITO["sky"])
            empirical.append(row["topology_expression_empirical_tail_p"])
        axes[row_index * 3 + 2].scatter(p_values, y, s=sizes, c=colors, edgecolors="#333333", linewidths=0.6)
        for x, yy, value in zip(p_values, y, empirical):
            if math.isfinite(number(value)):
                axes[row_index * 3 + 2].text(x + 0.12, yy, f"Pemp={float(value):.3g}", va="center", fontsize=6.5)
        axes[row_index * 3 + 2].set_yticks(y, RIBOSOMAL_DRIVERS)
        axes[row_index * 3 + 2].invert_yaxis()
        axes[row_index * 3 + 2].set_xlabel("−log10 aggregate ACAT P")
        axes[row_index * 3 + 2].set_title(f"{NETWORK_LABELS[network]}: evidence and matched percentile", loc="left", fontweight="bold")
        axes[row_index * 3 + 2].grid(axis="x", color="#E6E6E6", linewidth=0.5)
        axes[row_index * 3 + 2].spines[["top", "right"]].set_visible(False)
    for label, ax in zip("ABCDEF", axes):
        panel_label(ax, label)
    fig.suptitle("RPL11 compared with other selected cytosolic-ribosomal drivers", fontsize=14, fontweight="bold")
    save_figure(fig, out / "phase18_rpl11_ribosomal_comparison", dpi)


def caption_text(null_results: Sequence[dict[str, Any]]) -> str:
    null_lines = "; ".join(
        f"{NETWORK_SHORT[row['network']]} {row['null_model'].replace('_', '+')}: n={row['matched_control_n']}, empirical P={row['empirical_tail_p']:.3g}"
        for row in null_results
    )
    return f"""# Phase 18 RPL11 deep-dive figure captions

## Pathway-annotated excitatory-neuron consensus network

The pathway-annotated network merges the 20 conservative-support excitatory-neuron runs on the fixed excitatory Bayesian network. RPL11 is centered, and downstream nodes are placed at progressively larger radial distances for minimum directed depths D1, D2, and D3; guide circles are not drawn. Nodes within each depth are distributed at equal angular intervals, each deeper circle is rotated to reduce angular displacement from parent nodes, and the renderer checks every pair of displayed nodes for adequate clearance. Node area increases with the number of run-specific, selected-layer RPL11 neighborhoods containing the node; the exact count is printed as `x/20`. This neighborhood-occurrence count is distinct from query-hit recurrence. All full-network edges directly incident to RPL11 are included (0 incoming and 9 outgoing). Deeper mitochondrial query hits are retained when they occur as RPL11 query hits in at least 4 of 20 runs, together with connecting shortest paths of no more than three directed edges. All recorded edges among the displayed nodes are drawn. All nodes are circular, thick dark borders denote recurrent mitochondrial query hits, and fill summarizes Phase 8 direct-DEG direction. A colored boundary marks membership in four nonredundant representative pathways: dark violet, cytosolic ribosome; blue, electron transport chain / oxidative phosphorylation; orange, mitochondrial protein degradation; and green, cristae formation. Boundary segments indicate multiple memberships. No colored pathway boundary means only that the gene is absent from these four displayed representatives, not that it has no pathway annotation. The representatives were selected from an offline over-representation analysis of MSigDB C2:CP v2026.1: 34 of 35 displayed genes were mapped, the background comprised 6,952 MSigDB-mapped genes in the full excitatory Bayesian network, pathway sizes were restricted to 15–500 background genes, and Benjamini–Hochberg correction covered all 1,739 tested pathways. Each displayed representative has BH FDR < 0.05 and at least three displayed members. Pathway membership and over-representation do not establish pathway activation or a direct causal effect of RPL11.

## RPL11 directed-network evidence

**A–B,** RPL11-centered Bayesian-network subnetworks for excitatory neurons and astrocytes, styled after the centered key-driver subnetworks in Wang et al. Figure 6. Arrows follow the recorded network orientation. Upstream nodes are shown only as context and were not used in KDA enrichment; the excitatory network records no RPL11 parent, whereas the astrocyte chain is `RPS25 → RPLP1 → RPL11`. Downstream nodes lie on shortest directed paths of at most three edges to recurrent mitochondrial query hits. Node area and label size scale with displayed degree, square nodes denote cytosolic ribosomal proteins, dark double borders denote recurrent mitochondrial query hits, and hit labels report supporting-run frequency. Fill summarizes stored Phase 8 direct-DEG direction across contrasts within the broad network. **C,** Exact first directed depth for every mitochondrial hit in 23 conservative-support runs. **D,** RPL11 aggregate ACAT evidence relative to unique topology-, topology/expression-, and ribosomal-matched controls. {null_lines}.

## Query-overlap figure

The excitatory and astrocyte Venn diagrams compare the union of mitochondrial genes reached in conservative-support AD-up queries with the corresponding AD-down union. The elements are genes, not runs, and circle areas are not proportional. Exact run membership is shown below each Venn diagram. Microglia and oligodendrocytes each contribute only one AD-down supporting query and are shown as one-set summaries rather than artificial overlaps.

## Ribosomal-driver comparison

Pairwise Jaccard indices compare complete three-layer downstream neighborhoods and mitochondrial query-hit unions among RPL11, RPLP1, RPL15, RPS13, RPS15, and RPL38. Evidence panels show aggregate ACAT P values; point area reflects conservative-support count, and labels give topology/expression-matched empirical tail P values where assessable.

Bayesian-network arrows are model-derived hypotheses, not experimental proof of direct molecular regulation. The 23 primary supporting runs reuse two fixed broad-cell-type networks and are repeated contexts rather than independent network replications.
"""


def methods_text() -> str:
    return """# Phase 18 RPL11 deep-dive methods

The package was generated directly from `call_key_driver_returns.tsv` (95,557 explicit gene × included-run rows; 161 included `call_key_drivers()` calls), the recorded broad-cell-type Bayesian networks, Phase 12 run signature/background membership used as upstream Phase 18 inputs, Phase 9 gene annotation, Phase 5 normalization manifests, and Phase 8 MAST direct-DEG results. No deprecated Phase 12 key-driver ranking, selected-gene list, or figure was used.

For an edge `A → B`, A is upstream and B is downstream. RPL11 downstream neighborhoods were reconstructed cumulatively through three directed steps. Run-specific graphs were induced on each run's effective background. For all 23 conservative-support RPL11 runs in excitatory neurons and astrocytes, the script reproduced the recorded overlap set, neighborhood size, fold enrichment, and raw hypergeometric P value. Main network panels retain recurrent query hits (at least 4/20 excitatory or 2/3 astrocyte support runs) and every full-network shortest path of length at most three connecting RPL11 to those hits. Up to two recorded upstream layers are shown separately and never enter enrichment counts. Complete three-layer graphs are exported in GraphML and TSV format.

The pathway-annotated excitatory consensus network uses the same 20 conservative-support runs but a different node-size definition. For each run, a node is counted when it occurs in the RPL11 neighborhood reconstructed on that run's effective background through that run's selected final layer. Node size and the printed `x/20` value encode this neighborhood-occurrence count, not the number of times the node is a mitochondrial query hit. The display includes all direct incoming and outgoing RPL11 neighbors from the full excitatory network; no direct-neighbor threshold was required because RPL11 has 0 incoming and 9 outgoing edges. Deeper mitochondrial targets retain the 4/20 query-hit recurrence threshold used to control display density. The final display draws every recorded edge among the retained nodes. The analysis script exports the validated node, edge, and pathway-membership tables; `render_phase18_rpl11_cytoscape.py` verifies that the displayed network is a rooted directed tree, centers RPL11, places D1–D3 nodes at fixed 270-, 460-, and 650-unit radial distances without drawing guide circles, equally spaces nodes within each depth, rotates deeper circles toward their parent nodes, and fails if any node pair lacks the required clearance. Label-aware node diameters range from 112 to 156 Cytoscape units, with node-label fonts of 19–25 points. Cytoscape exports the standalone PNG, PDF, SVG, editable session, and style.

For pathway annotation, the 35 displayed nodes were tested for pathway over-representation using the local MSigDB C2:CP v2026.1 human-symbol collection. The custom background was the 6,952 genes shared by the full excitatory Bayesian network and that collection; 34 displayed genes mapped to this universe (`FUNDC2` did not). Pathways containing 15–500 background genes were eligible. One-sided hypergeometric P values were calculated for all 1,739 eligible pathways and adjusted together by the Benjamini–Hochberg method. Four significant, nonredundant representatives with at least three displayed members were selected for annotation: KEGG ribosome (dark violet), WikiPathways electron transport chain / oxidative phosphorylation (blue), Reactome mitochondrial protein degradation (orange), and Reactome cristae formation (green). The complete tested table and exact gene-to-pathway memberships are exported. A Cytoscape enhancedGraphics circos outline traces the node boundary; multiple memberships divide that boundary into colored segments. The boundary encodes membership rather than inferred activity, direction, or causality.

Direct-DEG color is a broad-network summary: AD-up only, AD-down only, both directions across stored contrasts, or no stored direct-DEG evidence. DEG status does not determine graph inclusion. Cytosolic ribosomal proteins were identified from HGNC names beginning with “ribosomal protein” while excluding names containing “mitochondrial.”

The matched-control universe contains assessable non-MT genes in the same broad network with coverage at least 0.80 and a nonmissing aggregate ACAT P value. Topology matching uses out-degree, total degree, cumulative downstream size at layers 1–3, and coverage. The second null adds log1p(total raw counts / total nuclei) and detected-nucleus fraction; excitatory totals combine all three assay sets. The third null restricts controls to cytosolic ribosomal proteins and uses topology plus expression/detection features. Features are median/MAD standardized, unique controls are ranked by Euclidean distance, and up to 250 nearest controls are retained. Empirical tail P is `(1 + controls at least as extreme as RPL11) / (1 + unique controls)`. Fixed-caliper membership and its empirical tail P are exported as a sensitivity analysis; a missing caliper P means no control passed all calipers. Results with fewer than 20 controls are descriptive.

Direction-level Venn sets are unions of exact RPL11 query-hit genes across conservative-support AD-up or AD-down runs within each broad network. Exact individual-query membership remains available in the binary matrices and TSV. Figures use deterministic layouts, colorblind-aware palettes, redundant shapes/borders, and vector PDF/SVG export. The Matplotlib multi-panel PNGs use 450 DPI by default. The standalone consensus network is exported directly by Cytoscape, with its PNG rendered at 300% zoom.
"""


def write_status_and_manifest(out: Path, checks: list[dict[str, Any]], visual_review_status: str) -> None:
    failed = [row for row in checks if row["blocking"] and row["status"] != "PASS"]
    status = "validated_complete" if not failed and visual_review_status == "complete" else "generated_pending_visual_review"
    write_tsv(
        out / "phase18_rpl11_deep_dive_status.tsv",
        [
            {
                "schema_version": SCHEMA,
                "generation_status": status,
                "blocking_check_count": sum(bool(row["blocking"]) for row in checks),
                "failed_blocking_check_count": len(failed),
                "visual_review_status": visual_review_status,
                "output_file_count": len(OUTPUT_NAMES),
            }
        ],
    )
    manifest_rows: list[dict[str, Any]] = []
    inputs = [CANONICAL, RUN_MANIFEST, SIGNATURE_MEMBERS, BACKGROUND_MEMBERS, MSIGDB_C2_CP, ANNOTATION, *NETWORK_INPUT.values(), *[path for paths in MAST_FILES.values() for path in paths]]
    for path in inputs:
        manifest_rows.append(
            {
                "schema_version": SCHEMA,
                "artifact_type": "input",
                "artifact": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    for name in OUTPUT_NAMES:
        if name == "phase18_rpl11_deep_dive_manifest.tsv":
            continue
        path = out / name
        require(path.exists() and path.stat().st_size > 0, f"Missing declared output: {name}")
        manifest_rows.append(
            {
                "schema_version": SCHEMA,
                "artifact_type": "output",
                "artifact": name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    write_tsv(out / "phase18_rpl11_deep_dive_manifest.tsv", manifest_rows)


def generate(output_dir: Path, dpi: int, visual_review_status: str) -> None:
    configure_style()
    checks: list[dict[str, Any]] = []
    print("stage=load_canonical", flush=True)
    rpl_rows, aggregate, rows_by_driver = load_canonical(checks)
    print("stage=load_graphs", flush=True)
    graphs = {network: load_graph(path, network, checks) for network, path in NETWORK_INPUT.items()}
    print("stage=load_annotation_expression", flush=True)
    annotation, expression = load_annotation_and_expression(checks)
    print("stage=load_support_membership", flush=True)
    membership, _, signatures, backgrounds = load_support_membership(rpl_rows, checks)
    print("stage=validate_support_runs", flush=True)
    matrix_rows, run_annotations = validate_primary_support_runs(rpl_rows, graphs, signatures, backgrounds, checks)
    print("stage=build_network_tables", flush=True)
    nodes_rows, edges_rows, full_nodes_rows, full_edges_rows, complete_graphs, layouts, _ = build_network_tables(graphs, membership, annotation, checks)
    display_graphs = {
        network: nx.DiGraph([(row["source"], row["target"]) for row in edges_rows if row["network"] == network])
        for network in PRIMARY_NETWORKS
    }
    for network in PRIMARY_NETWORKS:
        display_graphs[network].add_nodes_from(row["gene"] for row in nodes_rows if row["network"] == network)
    print("stage=build_excitatory_consensus", flush=True)
    consensus_graph, consensus_nodes, consensus_edges, consensus_positions = build_excitatory_consensus_tables(
        graphs["Excitatory_neurons"], rpl_rows, backgrounds, membership, annotation, checks
    )
    print("stage=build_excitatory_pathways", flush=True)
    pathway_ora, pathway_membership_rows, _ = build_excitatory_pathway_tables(
        graphs["Excitatory_neurons"], consensus_nodes, checks
    )
    regions = build_query_regions(membership, checks)
    print("stage=matched_controls", flush=True)
    feature_rows = build_feature_rows(aggregate, graphs, expression, annotation)
    controls, null_results, balance = build_matched_nulls(feature_rows, checks)
    comparison, neighborhoods, hits = build_ribosomal_comparison(graphs, aggregate, rows_by_driver, feature_rows)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".RPL11-staging-", dir=output_dir.parent))
    try:
        excitatory_staging = staging / "excitatory"
        excitatory_staging.mkdir(parents=True, exist_ok=True)
        write_tsv(excitatory_staging / "phase18_rpl11_excitatory_consensus_network_nodes.tsv", consensus_nodes)
        write_tsv(excitatory_staging / "phase18_rpl11_excitatory_consensus_network_edges.tsv", consensus_edges)
        write_tsv(excitatory_staging / "phase18_rpl11_excitatory_consensus_pathway_ora.tsv", pathway_ora)
        write_tsv(excitatory_staging / "phase18_rpl11_excitatory_consensus_pathway_membership.tsv", pathway_membership_rows)
        write_tsv(staging / "phase18_rpl11_nodes.tsv", nodes_rows)
        write_tsv(staging / "phase18_rpl11_edges.tsv", edges_rows)
        write_tsv(staging / "phase18_rpl11_layout.tsv", [{"schema_version": SCHEMA, "network": network, "gene": gene, "x": xy[0], "y": xy[1]} for network, positions in layouts.items() for gene, xy in sorted(positions.items())])
        write_tsv(staging / "phase18_rpl11_full_three_layer_nodes.tsv", full_nodes_rows)
        write_tsv(staging / "phase18_rpl11_full_three_layer_edges.tsv", full_edges_rows)
        nx.write_graphml(complete_graphs["Excitatory_neurons"], excitatory_staging / "phase18_rpl11_excitatory.graphml")
        astrocyte_staging = staging / "astrocyte"
        astrocyte_staging.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(complete_graphs["Astrocytes"], astrocyte_staging / "phase18_rpl11_astrocyte.graphml")
        write_tsv(staging / "phase18_rpl11_run_target_matrix.tsv", matrix_rows)
        write_tsv(staging / "phase18_rpl11_run_annotations.tsv", run_annotations)
        write_tsv(staging / "phase18_rpl11_matched_controls.tsv", controls)
        write_tsv(staging / "phase18_rpl11_matched_null_results.tsv", null_results)
        write_tsv(staging / "phase18_rpl11_matching_balance.tsv", balance)
        write_tsv(staging / "phase18_rpl11_ribosomal_comparison.tsv", comparison)
        write_tsv(staging / "phase18_rpl11_query_hit_membership.tsv", membership)
        write_tsv(staging / "phase18_rpl11_query_overlap_regions.tsv", regions)
        write_text(staging / "phase18_rpl11_deep_dive_caption.md", caption_text(null_results))
        write_text(staging / "phase18_rpl11_deep_dive_methods.md", methods_text())
        print("stage=cytoscape_consensus_source_tables_ready", flush=True)
        print("stage=plot_deep_dive", flush=True)
        plot_deep_dive(staging, dpi, graphs, display_graphs, nodes_rows, edges_rows, layouts, matrix_rows, run_annotations, controls, null_results)
        print("stage=plot_query_overlap", flush=True)
        plot_query_overlap(staging, dpi, regions, membership, matrix_rows, run_annotations)
        print("stage=plot_ribosomal_comparison", flush=True)
        plot_ribosomal_comparison(staging, dpi, comparison, neighborhoods, hits)
        for base in ("phase18_rpl11_deep_dive", "phase18_rpl11_query_overlap", "phase18_rpl11_ribosomal_comparison"):
            for suffix in ("png", "pdf", "svg"):
                path = staging / f"{base}.{suffix}"
                check_row(checks, f"{base}_{suffix}", path.exists() and path.stat().st_size > 0, path.stat().st_size if path.exists() else 0, ">0 bytes", "Figure export exists and is nonempty")
        check_row(checks, "png_dpi", dpi >= 450, dpi, ">=450", "PNG export resolution")
        check_row(checks, "visual_review", visual_review_status == "complete", visual_review_status, "complete", "Final-size color and grayscale visual review", blocking=False)
        write_tsv(staging / "phase18_rpl11_deep_dive_checks.tsv", checks)
        write_status_and_manifest(staging, checks, visual_review_status)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            source = staging / name
            require(source.exists(), f"Staging output missing: {name}")
            destination = output_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    print(f"generated={output_dir}")
    print(f"files={len(OUTPUT_NAMES)}")
    print(f"checks={len(checks)}")
    print(f"visual_review_status={visual_review_status}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "figures" / "analysis" / "phase_18_key_driver_selection" / "RPL11",
    )
    parser.add_argument("--png-dpi", type=int, default=450)
    parser.add_argument("--visual-review-status", choices=("pending", "complete"), default="pending")
    args = parser.parse_args()
    generate(args.output_dir.resolve(), args.png_dpi, args.visual_review_status)


if __name__ == "__main__":
    main()
