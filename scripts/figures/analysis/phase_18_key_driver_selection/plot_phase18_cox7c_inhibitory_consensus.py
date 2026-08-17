#!/usr/bin/env python3
"""Build and render the Phase 18 COX7C inhibitory consensus network in Cytoscape."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import py4cytoscape as p4c
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "COX7C"
    / "inhibitory"
)
CANONICAL = ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
BACKGROUNDS = ROOT / "results/minerva_production/12_kda/kda_background_members.tsv.gz"
SIGNATURES = ROOT / "results/minerva_production/12_kda/kda_signature_members.tsv"
NETWORK = ROOT / "data/bayesian_network/Inhibitory_neurons/result.links3.links.txt"
ANNOTATION = ROOT / "results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz"
MAST = ROOT / "results/minerva_production/08_mast/inhibitory.yu_mast_de.tsv.gz"
MSIGDB = ROOT / "data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt"

DRIVER = "COX7C"
NETWORK_NAME = "Inhibitory_neurons"
NETWORK_LABEL = "Inhibitory neurons"
SUPPORTING_RUNS = 6
QUERY_HIT_THRESHOLD = 1
MAX_DOWNSTREAM_DEPTH = 3
MAX_UPSTREAM_DEPTH = 2
SCHEMA = "phase18_cox7c_inhibitory_consensus_v1"
OUTPUT_PREFIX = "phase18_cox7c_inhibitory_consensus"
FIGURE_STEM = "phase18_cox7c_inhibitory_consensus_network_pathways"
STYLE_NAME = "Phase18 COX7C inhibitory radial consensus pathway outlines"

EXPECTED_QUERY_HITS = {
    "ATP5F1E",
    "ATP5IF1",
    "ATP5PF",
    "COX6B1",
    "DMAC2",
    "MRPL50",
    "MRPS14",
    "NDUFA1",
    "NDUFB2",
    "NDUFS3",
    "PAICS",
    "SLC8B1",
    "SOD1",
    "TXN",
    "UQCR10",
}
EXPECTED_DIRECT_IN = {"RPS15"}
EXPECTED_DIRECT_OUT = {
    "AC004540.1",
    "AC092329.3",
    "ATP5F1E",
    "ATP5MD",
    "ELOF1",
    "LAMTOR5",
    "NAA38",
    "NDUFA1",
    "RAB11A",
    "SEC62",
    "SSB",
    "TMSB10",
    "TPT1",
    "UQCR10",
    "ZKSCAN5",
}
EXPECTED_UPSTREAM_CONTEXT = {"RPS15", "RPLP1"}
PATHWAY_THEMES = (
    {
        "pathway": "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA",
        "code": "O",
        "label": "ETC / oxidative phosphorylation",
        "color": "#0072B2",
        "expected_members": {
            "ATP5F1E",
            "ATP5IF1",
            "ATP5PF",
            "COX6B1",
            "COX7C",
            "NDUFA1",
            "NDUFB2",
            "NDUFS3",
            "UQCR10",
        },
        "must_be_significant": True,
    },
    {
        "pathway": "REACTOME_COMPLEX_I_BIOGENESIS",
        "code": "I",
        "label": "Mitochondrial complex I biogenesis",
        "color": "#009E73",
        "expected_members": {"DMAC2", "NDUFA1", "NDUFB2", "NDUFS3"},
        "must_be_significant": True,
    },
    {
        "pathway": "REACTOME_DETOXIFICATION_OF_REACTIVE_OXYGEN_SPECIES",
        "code": "X",
        "label": "ROS detoxification",
        "color": "#7B3294",
        "expected_members": {"SOD1", "TXN"},
        "must_be_significant": False,
    },
)

DEG_COLORS = {
    "up_only": "#D55E00",
    "down_only": "#56B4E9",
    "mixed": "#F0E442",
    "not_deg": "#D9D9D9",
}
DEG_LABELS = (
    ("mixed", "Both AD-up and AD-down"),
    ("down_only", "AD-down only"),
    ("up_only", "AD-up only"),
    ("not_deg", "No stored direct DEG"),
)

D1_RADIUS = 640.0
D2_RADIUS = 900.0
D3_RADIUS = 1180.0
U1_RADIUS = 360.0
U2_RADIUS = 620.0
D1_ANGLES = {
    "LAMTOR5": -140.0,
    "AC004540.1": -120.0,
    "AC092329.3": -100.0,
    "ATP5F1E": -80.0,
    "ATP5MD": -60.0,
    "ELOF1": -40.0,
    "NAA38": -20.0,
    "NDUFA1": 0.0,
    "RAB11A": 20.0,
    "SEC62": 40.0,
    "SSB": 60.0,
    "TMSB10": 80.0,
    "TPT1": 100.0,
    "UQCR10": 120.0,
    "ZKSCAN5": 140.0,
}
D2_ANGLES = {
    "ATP5PF": -150.0,
    "POLR2K": -125.0,
    "DMAC2": -40.0,
    "PAICS": 10.0,
    "PHF11": 30.0,
    "SRP14": 105.0,
    "COX6B1": 135.0,
}
D3_ANGLES = {
    "ATP5IF1": -165.0,
    "NDUFB2": -150.0,
    "NDUFS3": -135.0,
    "SOD1": -120.0,
    "MRPS14": -100.0,
    "SLC8B1": 30.0,
    "MRPL50": 105.0,
    "TXN": 145.0,
}
PATHWAY_OUTLINE_PADDING = 32.0
COLLISION_PADDING = 16.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin({"TRUE", "T", "1", "YES"})


def hypergeom_upper_tail(overlap: int, population: int, successes: int, draws: int) -> float:
    if overlap <= 0:
        return 1.0
    denominator = math.comb(population, draws)
    numerator = sum(
        math.comb(successes, value) * math.comb(population - successes, draws - value)
        for value in range(overlap, min(successes, draws) + 1)
        if 0 <= draws - value <= population - successes
    )
    return float(numerator / denominator)


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [1.0] * len(p_values)
    running = 1.0
    for reverse_index in range(len(order) - 1, -1, -1):
        row_index = order[reverse_index]
        rank = reverse_index + 1
        running = min(running, p_values[row_index] * len(p_values) / rank)
        adjusted[row_index] = min(running, 1.0)
    return adjusted


def load_support_rows() -> pd.DataFrame:
    columns = [
        "kda_run_id",
        "broad_network",
        "key_driver",
        "final_layer",
        "final_overlap_count",
        "self_excluded",
        "conservative_support",
    ]
    rows = pd.read_csv(CANONICAL, sep="\t", usecols=columns, low_memory=False)
    rows = rows.loc[
        rows["broad_network"].eq(NETWORK_NAME)
        & rows["key_driver"].eq(DRIVER)
        & truth_series(rows["conservative_support"])
    ].copy()
    rows["final_layer"] = pd.to_numeric(rows["final_layer"], errors="raise").astype(int)
    rows["final_overlap_count"] = pd.to_numeric(rows["final_overlap_count"], errors="raise").astype(int)
    rows = rows.sort_values("kda_run_id").reset_index(drop=True)
    require(len(rows) == SUPPORTING_RUNS, f"Expected 6 supporting runs, found {len(rows)}")
    require(rows["kda_run_id"].is_unique, "Supporting run IDs are not unique")
    require(rows["final_layer"].between(2, 3).all(), "A supporting final layer lies outside D2-D3")
    require(int(truth_series(rows["self_excluded"]).sum()) == 5, "Unexpected self-exclusion count")
    return rows


def load_graph() -> nx.DiGraph:
    edges = pd.read_csv(NETWORK, sep="\t", header=None, names=["source", "target"])
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    require(nx.is_directed_acyclic_graph(graph), "The inhibitory Bayesian network is not acyclic")
    require(graph.number_of_nodes() == 9579 and graph.number_of_edges() == 10534, "Unexpected network dimensions")
    require(set(graph.predecessors(DRIVER)) == EXPECTED_DIRECT_IN, "COX7C direct incoming edges changed")
    require(set(graph.successors(DRIVER)) == EXPECTED_DIRECT_OUT, "COX7C direct outgoing edges changed")
    return graph


def load_run_sets(run_ids: set[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    backgrounds = {run_id: set() for run_id in run_ids}
    for chunk in pd.read_csv(BACKGROUNDS, sep="\t", usecols=["kda_run_id", "gene"], chunksize=500_000):
        selected = chunk.loc[chunk["kda_run_id"].isin(run_ids)]
        for run_id, group in selected.groupby("kda_run_id"):
            backgrounds[str(run_id)].update(group["gene"].astype(str))
    signature_rows = pd.read_csv(
        SIGNATURES,
        sep="\t",
        usecols=["kda_run_id", "gene", "effective_member"],
        low_memory=False,
    )
    signature_rows = signature_rows.loc[
        signature_rows["kda_run_id"].isin(run_ids) & truth_series(signature_rows["effective_member"])
    ]
    signatures = {
        run_id: set(group["gene"].astype(str))
        for run_id, group in signature_rows.groupby("kda_run_id")
    }
    require(all(backgrounds.values()), "A supporting run lacks an effective background")
    require(set(signatures) == run_ids and all(signatures.values()), "A supporting run lacks an effective query")
    return backgrounds, signatures


def load_annotation(display_genes: set[str]) -> dict[str, dict[str, Any]]:
    rows = pd.read_csv(
        ANNOTATION,
        sep="\t",
        usecols=["symbol_hgnc_current", "hgnc_name", "is_mitocarta3"],
        low_memory=False,
    )
    rows = rows.loc[rows["symbol_hgnc_current"].isin(display_genes)]
    result: dict[str, dict[str, Any]] = {}
    for row in rows.itertuples(index=False):
        gene = str(row.symbol_hgnc_current)
        current = result.setdefault(gene, {"hgnc_name": "", "is_core_mito": False})
        if not pd.isna(row.hgnc_name):
            current["hgnc_name"] = str(row.hgnc_name)
        current["is_core_mito"] = bool(
            current["is_core_mito"] or str(row.is_mitocarta3).strip().upper() in {"TRUE", "T", "1"}
        )
    return result


def load_deg(display_genes: set[str]) -> dict[str, dict[str, Any]]:
    rows = pd.read_csv(MAST, sep="\t", usecols=["gene", "paper_deg", "logFC"], low_memory=False)
    rows = rows.loc[rows["gene"].isin(display_genes) & truth_series(rows["paper_deg"])]
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"up": 0, "down": 0})
    for row in rows.itertuples(index=False):
        result[str(row.gene)]["up" if float(row.logFC) > 0 else "down"] += 1
    for gene in display_genes:
        evidence = result[gene]
        if evidence["up"] and evidence["down"]:
            evidence["class"] = "mixed"
        elif evidence["up"]:
            evidence["class"] = "up_only"
        elif evidence["down"]:
            evidence["class"] = "down_only"
        else:
            evidence["class"] = "not_deg"
    return dict(result)


def display_for_hits(graph: nx.DiGraph, hits: set[str]) -> nx.DiGraph:
    upstream = set(
        nx.single_source_shortest_path_length(graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH)
    ) - {DRIVER}
    nodes = {DRIVER} | EXPECTED_DIRECT_IN | EXPECTED_DIRECT_OUT | upstream
    for target in hits:
        require(nx.shortest_path_length(graph, DRIVER, target) <= MAX_DOWNSTREAM_DEPTH, f"Hit lies beyond D3: {target}")
        for path in nx.all_shortest_paths(graph, DRIVER, target):
            nodes.update(path)
    return graph.subgraph(nodes).copy()


def build_consensus_tables(
    graph: nx.DiGraph,
    support_rows: pd.DataFrame,
    backgrounds: dict[str, set[str]],
    signatures: dict[str, set[str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    neighborhood_occurrence: Counter[str] = Counter()
    query_hit_occurrence: Counter[str] = Counter()
    run_rows: list[dict[str, Any]] = []
    for row in support_rows.itertuples(index=False):
        run_id = str(row.kda_run_id)
        induced = graph.subgraph(backgrounds[run_id])
        require(DRIVER in induced, f"COX7C is absent from the effective background for {run_id}")
        lengths = nx.single_source_shortest_path_length(induced, DRIVER, cutoff=int(row.final_layer))
        hits = signatures[run_id] & set(lengths)
        self_excluded = str(row.self_excluded).strip().upper() in {"TRUE", "T", "1", "YES"}
        if self_excluded:
            hits.discard(DRIVER)
        require(len(hits) == int(row.final_overlap_count), f"Final overlap mismatch for {run_id}")
        neighborhood_occurrence.update(lengths.keys())
        query_hit_occurrence.update(hits)
        run_rows.append(
            {
                "schema_version": SCHEMA,
                "kda_run_id": run_id,
                "final_layer": int(row.final_layer),
                "effective_query_size": len(signatures[run_id]),
                "effective_background_size": len(backgrounds[run_id]),
                "reconstructed_neighborhood_size_including_driver": len(lengths),
                "driver_self_excluded": self_excluded,
                "reconstructed_query_hit_count": len(hits),
                "reconstructed_query_hits": ";".join(sorted(hits)),
            }
        )

    retained_hits = {gene for gene, count in query_hit_occurrence.items() if count >= QUERY_HIT_THRESHOLD}
    require(retained_hits == EXPECTED_QUERY_HITS, f"Unexpected retained query hits: {sorted(retained_hits)}")
    require(neighborhood_occurrence[DRIVER] == SUPPORTING_RUNS, "COX7C is not present in all supporting neighborhoods")
    downstream_lengths = nx.single_source_shortest_path_length(graph, DRIVER, cutoff=MAX_DOWNSTREAM_DEPTH)
    upstream_lengths = nx.single_source_shortest_path_length(
        graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH
    )
    upstream_context = set(upstream_lengths) - {DRIVER}
    require(upstream_context == EXPECTED_UPSTREAM_CONTEXT, "COX7C upstream context changed")

    display = display_for_hits(graph, retained_hits)
    display_nodes = set(display)
    require(display.number_of_nodes() == 33, f"Expected 33 nodes, found {display.number_of_nodes()}")
    require(display.number_of_edges() == 34, f"Expected 34 edges, found {display.number_of_edges()}")
    require(nx.is_directed_acyclic_graph(display), "Displayed graph is not acyclic")
    require(nx.is_weakly_connected(display), "Displayed graph is disconnected")
    require(display.has_edge("ATP5PF", "RAB11A"), "Expected ATP5PF-to-RAB11A cross edge is absent")
    require(display.has_edge("POLR2K", "SRP14"), "Expected POLR2K-to-SRP14 cross edge is absent")

    annotation = load_annotation(display_nodes)
    deg = load_deg(display_nodes)
    node_rows: list[dict[str, Any]] = []
    for gene in sorted(display_nodes):
        reasons: list[str] = []
        if gene == DRIVER:
            reasons.append("driver")
        if gene in upstream_context:
            reasons.append("upstream_context")
        if gene in EXPECTED_DIRECT_IN:
            reasons.append("all_direct_incoming")
        if gene in EXPECTED_DIRECT_OUT:
            reasons.append("all_direct_outgoing")
        if gene in retained_hits:
            reasons.append("query_hit_meeting_display_threshold")
        if gene not in retained_hits and gene not in upstream_context and gene not in EXPECTED_DIRECT_OUT and gene != DRIVER:
            reasons.append("shortest_path_connector")
        evidence = deg[gene]
        node_rows.append(
            {
                "schema_version": SCHEMA,
                "network": NETWORK_NAME,
                "gene": gene,
                "included_reason": "|".join(reasons),
                "directed_depth_from_cox7c": downstream_lengths.get(gene) if gene != DRIVER else 0,
                "upstream_depth_to_cox7c": upstream_lengths.get(gene) if gene != DRIVER else None,
                "is_direct_incoming_neighbor": gene in EXPECTED_DIRECT_IN,
                "is_direct_outgoing_neighbor": gene in EXPECTED_DIRECT_OUT,
                "supporting_neighborhood_occurrence_count": int(neighborhood_occurrence.get(gene, 0)),
                "supporting_neighborhood_occurrence_fraction": neighborhood_occurrence.get(gene, 0) / SUPPORTING_RUNS,
                "query_hit_occurrence_count": int(query_hit_occurrence.get(gene, 0)),
                "query_hit_occurrence_fraction": query_hit_occurrence.get(gene, 0) / SUPPORTING_RUNS,
                "query_hit_display_threshold_count": QUERY_HIT_THRESHOLD,
                "query_hit_display_threshold_fraction": QUERY_HIT_THRESHOLD / SUPPORTING_RUNS,
                "is_query_hit_meeting_display_threshold": gene in retained_hits,
                "is_core_mitocarta": bool(annotation.get(gene, {}).get("is_core_mito", False)),
                "hgnc_name": annotation.get(gene, {}).get("hgnc_name", ""),
                "phase08_deg_class": evidence["class"],
                "phase08_up_count": evidence["up"],
                "phase08_down_count": evidence["down"],
                "in_degree_full": graph.in_degree(gene),
                "out_degree_full": graph.out_degree(gene),
                "in_degree_display": display.in_degree(gene),
                "out_degree_display": display.out_degree(gene),
            }
        )

    edge_rows: list[dict[str, Any]] = []
    for source, target in sorted(display.edges):
        edge_rows.append(
            {
                "schema_version": SCHEMA,
                "network": NETWORK_NAME,
                "source": source,
                "target": target,
                "is_directly_incident_to_cox7c": source == DRIVER or target == DRIVER,
                "is_upstream_context_edge": source in upstream_context and (target in upstream_context or target == DRIVER),
                "is_cross_branch_edge": (source, target) in {("ATP5PF", "RAB11A"), ("POLR2K", "SRP14")},
                "source_directed_depth": downstream_lengths.get(source),
                "target_directed_depth": downstream_lengths.get(target),
                "source_upstream_depth": upstream_lengths.get(source) if source != DRIVER else None,
                "target_upstream_depth": upstream_lengths.get(target) if target != DRIVER else None,
                "source_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(source, 0),
                "target_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(target, 0),
            }
        )

    sensitivity_rows: list[dict[str, Any]] = []
    for threshold in range(1, SUPPORTING_RUNS + 1):
        hits = {gene for gene, count in query_hit_occurrence.items() if count >= threshold}
        threshold_graph = display_for_hits(graph, hits)
        sensitivity_rows.append(
            {
                "schema_version": SCHEMA,
                "threshold_count": threshold,
                "threshold_fraction": threshold / SUPPORTING_RUNS,
                "retained_query_hit_count": len(hits),
                "retained_query_hits": ";".join(sorted(hits)),
                "display_node_count": threshold_graph.number_of_nodes(),
                "display_edge_count": threshold_graph.number_of_edges(),
                "is_selected_for_figure": threshold == QUERY_HIT_THRESHOLD,
            }
        )
    return pd.DataFrame(node_rows), pd.DataFrame(edge_rows), pd.DataFrame(sensitivity_rows), pd.DataFrame(run_rows)


def load_gene_sets() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with MSIGDB.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            require(len(fields) >= 3, "Malformed MSigDB GMT row")
            result.append({"pathway": fields[0], "url": fields[1], "genes": set(fields[2:])})
    require(len(result) == 4115, f"Expected 4,115 pathways, found {len(result)}")
    return result


def build_pathway_tables(graph: nx.DiGraph, nodes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gene_sets = load_gene_sets()
    annotated_universe = set().union(*(row["genes"] for row in gene_sets))
    background = set(graph.nodes) & annotated_universe
    displayed = set(nodes["gene"]) & background
    require(len(background) == 6537, f"Unexpected mapped inhibitory background: {len(background)}")
    require(len(displayed) == 29, f"Unexpected mapped displayed-gene count: {len(displayed)}")
    rows: list[dict[str, Any]] = []
    for gene_set in gene_sets:
        members = gene_set["genes"] & background
        if not 15 <= len(members) <= 500:
            continue
        overlap = displayed & members
        raw_p = hypergeom_upper_tail(len(overlap), len(background), len(members), len(displayed))
        fold = (len(overlap) / len(displayed)) / (len(members) / len(background)) if overlap else 0.0
        rows.append(
            {
                "schema_version": SCHEMA,
                "library": "MSigDB C2:CP v2026.1 Hs symbols",
                "network": NETWORK_NAME,
                "pathway": gene_set["pathway"],
                "pathway_url": gene_set["url"],
                "background_definition": "all inhibitory-neuron Bayesian-network genes represented in MSigDB C2:CP",
                "background_gene_count": len(background),
                "displayed_mapped_gene_count": len(displayed),
                "pathway_background_gene_count": len(members),
                "overlap_gene_count": len(overlap),
                "overlap_genes": ";".join(sorted(overlap)),
                "fold_enrichment": fold,
                "raw_hypergeometric_p": raw_p,
            }
        )
    require(len(rows) == 1706, f"Unexpected eligible pathway-test count: {len(rows)}")
    adjusted = benjamini_hochberg([float(row["raw_hypergeometric_p"]) for row in rows])
    theme_by_pathway = {theme["pathway"]: theme for theme in PATHWAY_THEMES}
    for row, q_value in zip(rows, adjusted):
        row["bh_fdr"] = q_value
        theme = theme_by_pathway.get(row["pathway"])
        selected = bool(theme)
        row["selected_nonredundant_representative"] = selected
        row["pathway_code"] = theme["code"] if selected else None
        row["pathway_display_label"] = theme["label"] if selected else None
        row["pathway_color"] = theme["color"] if selected else None
        row["selection_rule"] = (
            "nonredundant representative; FDR-significant unless explicitly labeled contextual"
            if selected
            else None
        )
    rows.sort(key=lambda row: (float(row["raw_hypergeometric_p"]), str(row["pathway"])))

    selected = {row["pathway"]: row for row in rows if row["selected_nonredundant_representative"]}
    require(set(selected) == set(theme_by_pathway), "A selected pathway representative is missing")
    gene_set_by_name = {row["pathway"]: row for row in gene_sets}
    memberships: list[dict[str, Any]] = []
    for theme in PATHWAY_THEMES:
        result = selected[theme["pathway"]]
        members = displayed & gene_set_by_name[theme["pathway"]]["genes"]
        require(members == theme["expected_members"], f"Unexpected members for {theme['pathway']}")
        significant = float(result["bh_fdr"]) < 0.05
        require(significant == theme["must_be_significant"], f"Unexpected FDR status for {theme['pathway']}")
        for gene in sorted(members):
            memberships.append(
                {
                    "schema_version": SCHEMA,
                    "network": NETWORK_NAME,
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
                    "fdr_significant_0_05": significant,
                }
            )
    require(len(memberships) == 15, f"Expected 15 pathway membership rows, found {len(memberships)}")
    return pd.DataFrame(rows), pd.DataFrame(memberships)


def node_display_size(gene: str, occurrence_count: int) -> float:
    if gene == DRIVER:
        return 170.0
    recurrence_size = 118.0 + 7.0 * occurrence_count
    label_size = 128.0 + 7.0 * max(0, len(gene) - 5)
    return round(max(recurrence_size, label_size), 1)


def radial_positions(nodes: pd.DataFrame, edges: pd.DataFrame) -> tuple[dict[str, tuple[float, float]], float, str]:
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    graph.add_nodes_from(nodes["gene"])
    require(nx.is_directed_acyclic_graph(graph), "Displayed graph is not acyclic")
    require(nx.is_weakly_connected(graph), "Displayed graph is disconnected")
    require(set(graph.predecessors(DRIVER)) == EXPECTED_DIRECT_IN, "Direct parent changed")
    require(set(graph.successors(DRIVER)) == set(D1_ANGLES), "Direct children changed")
    positions: dict[str, tuple[float, float]] = {
        DRIVER: (0.0, 0.0),
        "RPS15": (-U1_RADIUS, 0.0),
        "RPLP1": (-U2_RADIUS, 0.0),
    }
    for genes, radius in ((D1_ANGLES, D1_RADIUS), (D2_ANGLES, D2_RADIUS), (D3_ANGLES, D3_RADIUS)):
        for gene, angle_degrees in genes.items():
            angle = math.radians(angle_degrees)
            positions[gene] = (radius * math.cos(angle), radius * math.sin(angle))
    require(set(positions) == set(nodes["gene"]), "Radial layout did not assign every node")
    size_by_gene = {
        row.gene: node_display_size(row.gene, int(row.supporting_neighborhood_occurrence_count))
        + PATHWAY_OUTLINE_PADDING
        for row in nodes.itertuples()
    }
    minimum_clearance = float("inf")
    closest_pair = ""
    genes = nodes["gene"].tolist()
    for index, gene_a in enumerate(genes):
        for gene_b in genes[index + 1 :]:
            distance = math.dist(positions[gene_a], positions[gene_b])
            required = (size_by_gene[gene_a] + size_by_gene[gene_b]) / 2.0 + COLLISION_PADDING
            clearance = distance - required
            if clearance < minimum_clearance:
                minimum_clearance = clearance
                closest_pair = f"{gene_a}/{gene_b}"
            require(clearance >= 0, f"Radial layout collision: {gene_a} and {gene_b}")
    print(f"Minimum conservative node clearance: {minimum_clearance:.1f} units ({closest_pair})")
    return positions, minimum_clearance, closest_pair


def pathway_outline(codes: list[str]) -> str:
    if not codes:
        return ""
    colors = ",".join(next(theme["color"] for theme in PATHWAY_THEMES if theme["code"] == code) for code in codes)
    values = ",".join("1" for _ in codes)
    return (
        'circoschart: arcstart=270 firstarc=.78 firstarcwidth=.16 arcwidth=.16 '
        f'borderwidth=0 colorlist="{colors}" valuelist="{values}" showlabels=false'
    )


def prepare_cytoscape_tables(
    nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, float, str]:
    cy_nodes = nodes.copy()
    cy_edges = edges.copy()
    cy_nodes["query_hit_bool"] = truth_series(cy_nodes["is_query_hit_meeting_display_threshold"])
    cy_edges["direct_edge_bool"] = truth_series(cy_edges["is_directly_incident_to_cox7c"])

    def display_label(row: pd.Series) -> str:
        upstream = pd.to_numeric(pd.Series([row["upstream_depth_to_cox7c"]]), errors="coerce").iloc[0]
        if pd.notna(upstream):
            return f"{row['gene']}\nU{int(upstream)}"
        return f"{row['gene']}\n{int(row['supporting_neighborhood_occurrence_count'])}/{SUPPORTING_RUNS}"

    cy_nodes["display_label"] = cy_nodes.apply(display_label, axis=1)
    cy_nodes["display_font_size"] = cy_nodes["gene"].str.len().map(lambda length: 20 if length >= 9 else 21 if length >= 7 else 22)
    cy_nodes["display_size"] = cy_nodes.apply(
        lambda row: node_display_size(row["gene"], int(row["supporting_neighborhood_occurrence_count"])), axis=1
    )
    cy_nodes["query_hit_class"] = cy_nodes["query_hit_bool"].map({True: "query_hit", False: "not_query_hit"})
    positions, minimum_clearance, closest_pair = radial_positions(nodes, edges)
    cy_nodes["cy_x"] = cy_nodes["gene"].map(lambda gene: positions[gene][0])
    cy_nodes["cy_y"] = cy_nodes["gene"].map(lambda gene: positions[gene][1])
    theme_codes = [theme["code"] for theme in PATHWAY_THEMES]
    codes_by_gene = {
        gene: [code for code in theme_codes if code in set(group["pathway_code"])]
        for gene, group in membership.groupby("gene")
    }
    cy_nodes["pathway_codes"] = cy_nodes["gene"].map(lambda gene: ";".join(codes_by_gene.get(gene, [])))
    cy_nodes["pathway_outline"] = cy_nodes["gene"].map(lambda gene: pathway_outline(codes_by_gene.get(gene, [])))
    cy_nodes["pathway_outline_size"] = cy_nodes["display_size"] + PATHWAY_OUTLINE_PADDING
    cy_edges["interaction"] = "directed"
    cy_edges["direct_edge_class"] = cy_edges["direct_edge_bool"].map(
        {True: "direct_cox7c", False: "other_displayed"}
    )
    return cy_nodes, cy_edges, minimum_clearance, closest_pair


def mapping(visual_property: str, column: str, mapping_type: str, table_values=None, visual_values=None):
    return p4c.map_visual_property(
        visual_property,
        column,
        mapping_type,
        table_column_values=[] if table_values is None else table_values,
        visual_prop_values=[] if visual_values is None else visual_values,
    )


def create_style() -> None:
    if STYLE_NAME in p4c.get_visual_style_names():
        p4c.delete_visual_style(STYLE_NAME)
    defaults = {
        "NETWORK_BACKGROUND_PAINT": "#FFFFFF",
        "NODE_FILL_COLOR": "#D9D9D9",
        "NODE_BORDER_PAINT": "#555555",
        "NODE_BORDER_WIDTH": 1.8,
        "NODE_LABEL_COLOR": "#111111",
        "NODE_LABEL_FONT_FACE": "SansSerif.bold,plain,16",
        "NODE_LABEL_FONT_SIZE": 16,
        "NODE_LABEL_POSITION": "C,C,c,0.00,0.00",
        "NODE_LABEL_MAX_WIDTH": 132,
        "NODE_SHAPE": "ELLIPSE",
        "NODE_SIZE": 100,
        "NODE_TRANSPARENCY": 255,
        "EDGE_CURVED": False,
        "EDGE_LINE_TYPE": "SOLID",
        "EDGE_UNSELECTED_PAINT": "#A8A8A8",
        "EDGE_STROKE_UNSELECTED_PAINT": "#A8A8A8",
        "EDGE_TARGET_ARROW_SHAPE": "DELTA",
        "EDGE_TARGET_ARROW_UNSELECTED_PAINT": "#777777",
        "EDGE_WIDTH": 1.2,
        "EDGE_TRANSPARENCY": 220,
    }
    mappings = [
        mapping("NODE_LABEL", "display_label", "p"),
        mapping("NODE_SIZE", "display_size", "p"),
        mapping("NODE_LABEL_FONT_SIZE", "display_font_size", "p"),
        mapping("NODE_FILL_COLOR", "phase08_deg_class", "d", list(DEG_COLORS), list(DEG_COLORS.values())),
        mapping("NODE_BORDER_WIDTH", "query_hit_class", "d", ["not_query_hit", "query_hit"], [1.8, 4.5]),
        mapping("NODE_BORDER_PAINT", "query_hit_class", "d", ["not_query_hit", "query_hit"], ["#555555", "#111111"]),
        mapping("EDGE_WIDTH", "direct_edge_class", "d", ["other_displayed", "direct_cox7c"], [1.2, 2.8]),
        mapping("EDGE_UNSELECTED_PAINT", "direct_edge_class", "d", ["other_displayed", "direct_cox7c"], ["#A8A8A8", "#4D4D4D"]),
        mapping("EDGE_STROKE_UNSELECTED_PAINT", "direct_edge_class", "d", ["other_displayed", "direct_cox7c"], ["#A8A8A8", "#4D4D4D"]),
        mapping("NODE_CUSTOMGRAPHICS_1", "pathway_outline", "p"),
        mapping("NODE_CUSTOMGRAPHICS_SIZE_1", "pathway_outline_size", "p"),
    ]
    p4c.create_visual_style(STYLE_NAME, defaults=defaults, mappings=mappings)
    p4c.lock_node_dimensions(True, style_name=STYLE_NAME)
    p4c.set_node_custom_position(
        node_anchor="C", graphic_anchor="C", justification="c", x_offset=0.0, y_offset=0.0, slot=1, style_name=STYLE_NAME
    )


def add_annotations(network_suid: int) -> None:
    def add_text(label: str, x: float, y: float, name: str, size: int = 16, style: str = "plain", color: str = "#222222") -> None:
        p4c.add_annotation_text(
            text=label, x_pos=x, y_pos=y, font_size=size, font_family="SansSerif", font_style=style,
            color=color, name=name, canvas="foreground", z_order=20, network=network_suid
        )

    def add_symbol(x: float, y: float, name: str, fill: str, border: str = "#555555", border_width: int = 2, size: int = 28) -> None:
        p4c.add_annotation_shape(
            type="ELLIPSE", x_pos=x, y_pos=y, fill_color=fill, opacity=100, border_thickness=border_width,
            border_color=border, border_opacity=100, height=size, width=size, name=name,
            canvas="foreground", z_order=10, network=network_suid
        )

    title_x, title_y = -1320.0, -1510.0
    add_text("COX7C-centered inhibitory-neuron consensus network", title_x, title_y, "figure_title", 29, "bold", "#111111")
    add_text(
        "U1-U2 nodes are upstream context; D1-D3 nodes lie downstream; arrows follow the Bayesian-network direction",
        title_x, title_y + 55, "figure_subtitle", 16, color="#555555"
    )

    legend_x, legend_top = 1370.0, -1080.0
    text_x = legend_x + 46.0
    add_text("HOW TO READ", legend_x, legend_top, "legend_title", 20, "bold", "#111111")
    add_text("Node size and x/6 show neighborhood recurrence", legend_x, legend_top + 52, "legend_recurrence_1")
    add_text("across the 6 supporting runs", legend_x, legend_top + 86, "legend_recurrence_2")
    add_text("U1/U2: upstream distance to COX7C", legend_x, legend_top + 126, "legend_upstream")
    add_text("Thick black border: mitochondrial query hit at >=1/6", legend_x, legend_top + 166, "legend_query_hit")

    deg_heading_y = legend_top + 218
    add_text("NODE FILL  ·  PHASE 8 DIRECT DEG", legend_x, deg_heading_y, "legend_deg_heading", 17, "bold", "#111111")
    for index, (deg_class, label) in enumerate(DEG_LABELS):
        y = deg_heading_y + 45 + index * 48
        add_symbol(legend_x, y, f"legend_deg_symbol_{index}", DEG_COLORS[deg_class])
        add_text(label, text_x, y + 8, f"legend_deg_text_{index}", color="#333333")

    pathway_heading_y = deg_heading_y + 275
    add_text("PATHWAY OUTLINE", legend_x, pathway_heading_y, "legend_pathway_heading", 17, "bold", "#111111")
    add_text("OXPHOS and complex I are BH-significant; ROS is contextual", legend_x, pathway_heading_y + 39, "legend_pathway_note", 15, color="#555555")
    for index, theme in enumerate(PATHWAY_THEMES):
        y = pathway_heading_y + 84 + index * 48
        add_symbol(legend_x, y, f"legend_pathway_symbol_{theme['code']}", "#FFFFFF", theme["color"], 6, 30)
        add_text(theme["label"], text_x, y + 6, f"legend_pathway_text_{theme['code']}", color="#333333")

    radial_heading_y = pathway_heading_y + 84 + len(PATHWAY_THEMES) * 48 + 45
    add_text("RADIAL DISTANCE", legend_x, radial_heading_y, "legend_radial_heading", 17, "bold", "#111111")
    add_text("U1-U2: upstream context; D1-D3: minimum downstream steps", legend_x, radial_heading_y + 43, "legend_radial_text")
    scope_heading_y = radial_heading_y + 110
    add_text("DISPLAY SCOPE", legend_x, scope_heading_y, "legend_scope_heading", 17, "bold", "#111111")
    add_text("33 nodes / 34 edges", legend_x, scope_heading_y + 43, "legend_scope_counts")
    add_text("All COX7C edges: 1 incoming, 15 outgoing", legend_x, scope_heading_y + 80, "legend_scope_direct")
    add_text("D3 paths to all 15 observed query hits", legend_x, scope_heading_y + 117, "legend_scope_hits")
    add_text("All model edges among displayed nodes are retained", legend_x, scope_heading_y + 154, "legend_scope_edges")
    add_text(
        "Display threshold >=1/6 is a coverage choice, not a significance cutoff",
        legend_x, scope_heading_y + 202, "legend_scope_threshold", 15, color="#555555"
    )


def render_cytoscape(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    membership: pd.DataFrame,
    output_dir: Path,
    png_zoom: int = 300,
) -> None:
    cy_nodes, cy_edges, minimum_clearance, closest_pair = prepare_cytoscape_tables(nodes, edges, membership)
    version = p4c.cytoscape_version_info()
    require(version.get("cytoscapeVersion") == "3.10.4", f"Expected Cytoscape 3.10.4, found {version}")
    p4c.close_session(False)
    network_suid = p4c.create_network_from_data_frames(
        nodes=cy_nodes,
        edges=cy_edges,
        title="Phase 18 COX7C radial inhibitory-neuron consensus network",
        collection="Phase 18 COX7C deep dive",
        node_id_list="gene",
        source_id_list="source",
        target_id_list="target",
        interaction_type_list="interaction",
    )
    create_style()
    p4c.set_visual_style(STYLE_NAME, network=network_suid)
    p4c.lock_node_dimensions(True, style_name=STYLE_NAME)
    p4c.set_node_position_bypass(
        cy_nodes["gene"].tolist(), cy_nodes["cy_x"].tolist(), cy_nodes["cy_y"].tolist(), network=network_suid
    )
    p4c.set_node_color_bypass([DRIVER], "#111111", network=network_suid)
    p4c.set_node_label_color_bypass([DRIVER], "#FFFFFF", network=network_suid)
    p4c.set_node_border_color_bypass([DRIVER], "#111111", network=network_suid)
    p4c.set_node_border_width_bypass([DRIVER], 5.0, network=network_suid)
    p4c.set_node_font_size_bypass([DRIVER], 27, network=network_suid)
    p4c.set_node_property_bypass([DRIVER], [170.0], "NODE_SIZE", network=network_suid)
    add_annotations(network_suid)
    p4c.fit_content(network=network_suid)

    session_path = output_dir / f"{FIGURE_STEM}_cytoscape.cys"
    style_path = output_dir / f"{FIGURE_STEM}_cytoscape_style"
    p4c.save_session(str(session_path), overwrite_file=True)
    p4c.export_visual_styles(filename=str(style_path), type="XML", styles=STYLE_NAME, overwrite_file=True)
    export_log: dict[str, Any] = {
        "cytoscape_version": version.get("cytoscapeVersion"),
        "py4cytoscape_version": p4c.__version__,
        "network": NETWORK_NAME,
        "driver": DRIVER,
        "network_suid": network_suid,
        "node_count": len(cy_nodes),
        "edge_count": len(cy_edges),
        "direct_incoming_edges": 1,
        "direct_outgoing_edges": 15,
        "supporting_run_count": SUPPORTING_RUNS,
        "query_hit_threshold": QUERY_HIT_THRESHOLD,
        "query_hit_count": len(EXPECTED_QUERY_HITS),
        "threshold_rationale": "1/6 retains all 15 observed hits in a readable 33-node graph; 2/6 loses 7 hits and removes 10 nodes",
        "layout": "collision_checked_radial_DAG_without_guide_rings",
        "radial_level_radii": {"D1": D1_RADIUS, "D2": D2_RADIUS, "D3": D3_RADIUS, "U1": U1_RADIUS, "U2": U2_RADIUS},
        "minimum_conservative_node_clearance": minimum_clearance,
        "closest_node_pair": closest_pair,
        "guide_rings_drawn": False,
        "pathway_encoding": "segmented_colored_outer_outline",
        "exports": {},
    }
    for image_type in ("SVG", "PDF"):
        path = output_dir / f"{FIGURE_STEM}.{image_type.lower()}"
        p4c.export_image(
            filename=str(path), type=image_type, overwrite_file=True, all_graphics_details=True,
            export_text_as_font=True, network=network_suid
        )
        require(path.exists() and path.stat().st_size > 0, f"Cytoscape did not create {path}")
        export_log["exports"][image_type.lower()] = {"file": path.name, "bytes": path.stat().st_size}
    png_path = output_dir / f"{FIGURE_STEM}.png"
    p4c.export_image(
        filename=str(png_path), type="PNG", zoom=png_zoom, overwrite_file=True,
        all_graphics_details=True, transparent_background=False, network=network_suid
    )
    require(png_path.exists() and png_path.stat().st_size > 0, "Cytoscape did not create the PNG")
    export_log["exports"]["png"] = {"file": png_path.name, "bytes": png_path.stat().st_size, "zoom_percent": png_zoom}
    (output_dir / f"{FIGURE_STEM}_cytoscape_export.json").write_text(
        json.dumps(export_log, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(export_log, indent=2))


def write_tsv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="")
    require(path.exists() and path.stat().st_size > 0, f"Failed to write {path}")


def write_graphml(path: Path, nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame) -> None:
    graph = nx.DiGraph(network=NETWORK_NAME, driver=DRIVER, query_hit_display_threshold="1/6")
    codes_by_gene = {
        gene: ";".join(group.sort_values("pathway_code")["pathway_code"].astype(str))
        for gene, group in membership.groupby("gene")
    }
    for record in nodes.to_dict(orient="records"):
        gene = str(record.pop("gene"))
        attributes = {key: "" if pd.isna(value) else value for key, value in record.items() if key != "schema_version"}
        attributes["pathway_codes"] = codes_by_gene.get(gene, "")
        graph.add_node(gene, **attributes)
    for record in edges.to_dict(orient="records"):
        source = str(record.pop("source")); target = str(record.pop("target"))
        attributes = {key: "" if pd.isna(value) else value for key, value in record.items() if key != "schema_version"}
        graph.add_edge(source, target, **attributes)
    nx.write_graphml(graph, path)
    require(path.exists() and path.stat().st_size > 0, "GraphML export failed")


def write_documentation(output_dir: Path, pathway_ora: pd.DataFrame) -> None:
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_nonredundant_representative"])].set_index("pathway")
    summaries = []
    for theme in PATHWAY_THEMES:
        row = selected.loc[theme["pathway"]]
        status = "FDR-significant" if float(row["bh_fdr"]) < 0.05 else "contextual"
        summaries.append(f"{theme['label']} ({int(row['overlap_gene_count'])} genes; BH FDR = {float(row['bh_fdr']):.3g}; {status})")
    caption = f"""# COX7C inhibitory-neuron consensus network with pathway outlines

COX7C-centered inhibitory-neuron Bayesian-network neighborhood reconstructed from six conservative-support runs. The 1/6 display threshold retains all 15 observed mitochondrial query hits in a 33-node, 34-edge graph. Raising the threshold to 2/6 would retain eight hits and 23 nodes, so 1/6 was selected to preserve informative single-run biology; it is a coverage rule, not a significance cutoff. The display retains the direct incoming edge, all 15 direct outgoing edges, U1-U2 upstream context, D3 paths to retained hits, and every model edge among displayed nodes.

Node size and `x/6` show supporting-neighborhood occurrence; U1/U2 show upstream graph distance. Thick black borders mark query hits meeting 1/6. Fill shows stored Phase 8 direct-DEG direction. Pathway outlines show {', '.join(summaries)}. The ROS outline is contextual and must not be interpreted as statistically significant enrichment.
"""
    methods = f"""# Methods: COX7C inhibitory-neuron consensus network

Six conservative-support COX7C rows were read from `call_key_driver_returns.tsv`. For each run, the inhibitory-neuron Bayesian network was restricted to its recorded effective background and reconstructed through the stored final D2 or D3 layer. Effective query genes came from `kda_signature_members.tsv`; COX7C was excluded when the Phase 18 row recorded self-exclusion. All six reconstructed query-overlap counts matched the stored final overlap counts.

Query-hit recurrence was counted separately from neighborhood occurrence. Threshold profiling showed that 1/6 retains 15 hits and yields 33 nodes/34 edges, whereas 2/6 retains eight hits and yields 23 nodes/23 edges. The 1/6 threshold therefore preserves seven additional single-run hits while remaining comparable in size to the existing RPL11 network figure. All direct COX7C edges, the upstream chain `RPLP1 -> RPS15 -> COX7C`, shortest paths through D3, and all model edges induced by the displayed nodes were retained.

Pathway ORA used the 29 displayed genes represented in MSigDB C2:CP v2026.1. The explicit universe was 6,537 inhibitory-neuron Bayesian-network genes represented in that collection. One-sided hypergeometric tests were run for 1,706 pathways with 15-500 mapped background genes and corrected by Benjamini-Hochberg. The displayed representatives are {', '.join(summaries)}. The ROS term is shown only to organize `SOD1` and `TXN`; its BH FDR exceeds 0.05.

The graph was rendered in Cytoscape 3.10.4 with a deterministic, collision-checked radial layout and no guide rings. Colors use a colorblind-safe palette. PNG was exported at 300% zoom; PDF and SVG are vector exports, and the editable `.cys` session and visual-style XML are saved beside the figure.
"""
    (output_dir / f"{FIGURE_STEM}_caption.md").write_text(caption, encoding="utf-8")
    (output_dir / f"{FIGURE_STEM}_methods.md").write_text(methods, encoding="utf-8")


def validate_outputs(
    output_dir: Path,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    sensitivity: pd.DataFrame,
    pathway_ora: pd.DataFrame,
    membership: pd.DataFrame,
) -> pd.DataFrame:
    png = output_dir / f"{FIGURE_STEM}.png"; pdf = output_dir / f"{FIGURE_STEM}.pdf"; svg = output_dir / f"{FIGURE_STEM}.svg"
    cys = output_dir / f"{FIGURE_STEM}_cytoscape.cys"; style = output_dir / f"{FIGURE_STEM}_cytoscape_style.xml"
    with Image.open(png) as image:
        width, height = image.size
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_nonredundant_representative"])]
    threshold_two = sensitivity.loc[sensitivity["threshold_count"].eq(2)].iloc[0]
    checks = [
        ("supporting_run_count", SUPPORTING_RUNS == 6, str(SUPPORTING_RUNS)),
        ("selected_threshold", QUERY_HIT_THRESHOLD == 1, "1/6"),
        ("threshold_2_hit_count", int(threshold_two["retained_query_hit_count"]) == 8, str(threshold_two["retained_query_hit_count"])),
        ("node_count", len(nodes) == 33, str(len(nodes))),
        ("edge_count", len(edges) == 34, str(len(edges))),
        ("query_hit_count", int(truth_series(nodes["is_query_hit_meeting_display_threshold"]).sum()) == 15, "15"),
        ("all_direct_incoming", int(truth_series(nodes["is_direct_incoming_neighbor"]).sum()) == 1, "1"),
        ("all_direct_outgoing", int(truth_series(nodes["is_direct_outgoing_neighbor"]).sum()) == 15, "15"),
        ("pathway_representative_count", len(selected) == 3, str(len(selected))),
        ("pathway_membership_rows", len(membership) == 15, str(len(membership))),
        ("png_dimensions", width >= 2200 and height >= 1300, f"{width}x{height}"),
        ("png_nonempty", png.stat().st_size > 100_000, str(png.stat().st_size)),
        ("pdf_nonempty", pdf.stat().st_size > 5_000, str(pdf.stat().st_size)),
        ("svg_nonempty", svg.stat().st_size > 20_000, str(svg.stat().st_size)),
        ("cytoscape_session_nonempty", cys.stat().st_size > 10_000, str(cys.stat().st_size)),
        ("cytoscape_style_nonempty", style.stat().st_size > 5_000, str(style.stat().st_size)),
    ]
    frame = pd.DataFrame(checks, columns=["check", "passed", "observed"])
    require(frame["passed"].all(), f"Output validation failed: {frame.loc[~frame['passed'], 'check'].tolist()}")
    return frame


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(output_dir: Path) -> None:
    manifest_path = output_dir / f"{FIGURE_STEM}_manifest.tsv"
    rows = [
        {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path != manifest_path
    ]
    write_tsv(manifest_path, pd.DataFrame(rows))


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_rows = load_support_rows()
    graph = load_graph()
    backgrounds, signatures = load_run_sets(set(support_rows["kda_run_id"].astype(str)))
    nodes, edges, sensitivity, run_summary = build_consensus_tables(graph, support_rows, backgrounds, signatures)
    pathway_ora, pathway_membership = build_pathway_tables(graph, nodes)
    table_outputs = {
        f"{OUTPUT_PREFIX}_network_nodes.tsv": nodes,
        f"{OUTPUT_PREFIX}_network_edges.tsv": edges,
        f"{OUTPUT_PREFIX}_supporting_runs.tsv": run_summary,
        f"{OUTPUT_PREFIX}_pathway_ora.tsv": pathway_ora,
        f"{OUTPUT_PREFIX}_pathway_membership.tsv": pathway_membership,
        f"{OUTPUT_PREFIX}_threshold_sensitivity.tsv": sensitivity,
    }
    for filename, frame in table_outputs.items():
        write_tsv(output_dir / filename, frame)
    write_graphml(output_dir / "phase18_cox7c_inhibitory.graphml", nodes, edges, pathway_membership)
    render_cytoscape(nodes, edges, pathway_membership, output_dir)
    write_documentation(output_dir, pathway_ora)
    checks = validate_outputs(output_dir, nodes, edges, sensitivity, pathway_ora, pathway_membership)
    write_tsv(output_dir / f"{FIGURE_STEM}_checks.tsv", checks)
    write_manifest(output_dir)
    print(f"Wrote {output_dir / (FIGURE_STEM + '.png')}")
    print("Display: 33 nodes, 34 edges, 15 query hits at >=1/6")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir.resolve())


if __name__ == "__main__":
    main()
