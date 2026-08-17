#!/usr/bin/env python3
"""Build APOE astrocyte consensus tables and render the figure in Cytoscape."""

from __future__ import annotations

import argparse
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Wedge
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "APOE"
    / "astrocytes"
)
CANONICAL = ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
BACKGROUNDS = ROOT / "results/minerva_production/12_kda/kda_background_members.tsv.gz"
NETWORK = ROOT / "data/bayesian_network/Astrocytes/result.links3.links.txt"
ANNOTATION = ROOT / "results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz"
MAST = ROOT / "results/minerva_production/08_mast/astrocytes.yu_mast_de.tsv.gz"
MSIGDB = ROOT / "data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt"

DRIVER = "APOE"
NETWORK_NAME = "Astrocytes"
SUPPORTING_RUNS = 4
QUERY_HIT_THRESHOLD = 1
MAX_DOWNSTREAM_DEPTH = 2
MAX_UPSTREAM_DEPTH = 2
SCHEMA = "phase18_apoe_astrocyte_consensus_v1"
OUTPUT_PREFIX = "phase18_apoe_astrocyte_consensus"
FIGURE_STEM = "phase18_apoe_astrocyte_consensus_network_pathways"

EXPECTED_QUERY_HITS = {"AGT", "ATP5F1A", "ATP5PB", "CHCHD10", "LDHB", "NME3", "TUFM"}
EXPECTED_DIRECT_IN = {"CKB", "LAPTM4A"}
EXPECTED_DIRECT_OUT = {
    "ATP5PB",
    "C1orf56",
    "CHCHD10",
    "CST3",
    "DNASE2",
    "HLA-A",
    "LDHB",
    "PLTP",
    "TEX264",
    "TRAPPC4",
    "TUFM",
}
EXPECTED_UPSTREAM_CONTEXT = {"CKB", "GPX4", "ITM2B", "LAPTM4A"}

DEG_COLORS = {
    "up_only": "#D55E00",
    "down_only": "#56B4E9",
    "mixed": "#F0E442",
    "not_deg": "#D9D9D9",
}
DEG_LABELS = {
    "up_only": "AD-up only",
    "down_only": "AD-down only",
    "mixed": "Both directions",
    "not_deg": "No stored direct DEG",
}
PATHWAY_THEMES = (
    {
        "pathway": "REACTOME_AMYLOID_FIBER_FORMATION",
        "code": "A",
        "label": "Amyloid fiber formation",
        "color": "#7B3294",
        "expected_members": {"APOE", "CST3", "ITM2B"},
    },
    {
        "pathway": "REACTOME_NR1H3_NR1H2_REGULATE_GENE_EXPRESSION_LINKED_TO_CHOLESTEROL_TRANSPORT_AND_EFFLUX",
        "code": "L",
        "label": "Cholesterol transport / efflux",
        "color": "#E69F00",
        "expected_members": {"APOE", "PLTP"},
    },
    {
        "pathway": "REACTOME_CRISTAE_FORMATION",
        "code": "C",
        "label": "Cristae formation",
        "color": "#009E73",
        "expected_members": {"ATP5F1A", "ATP5PB"},
    },
)

# Fixed, branch-aware layout. D1 occupies the right semicircle; each D2 query hit
# remains radially aligned with its D1 parent. The two upstream chains sit left.
D1_ANGLES_DEGREES = {
    "C1orf56": -88.0,
    "DNASE2": -70.0,
    "HLA-A": -52.0,
    "CST3": -34.0,
    "PLTP": -17.0,
    "ATP5PB": 0.0,
    "CHCHD10": 17.0,
    "LDHB": 34.0,
    "TEX264": 52.0,
    "TRAPPC4": 70.0,
    "TUFM": 88.0,
}
D2_ANGLES_DEGREES = {"AGT": -34.0, "ATP5F1A": 34.0, "NME3": 88.0}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin({"TRUE", "T", "1", "YES"})


def split_genes(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [gene.strip() for gene in str(value).split(";") if gene.strip()]


def hypergeom_upper_tail(overlap: int, population: int, successes: int, draws: int) -> float:
    if overlap <= 0:
        return 1.0
    denominator = math.comb(population, draws)
    upper = min(successes, draws)
    numerator = sum(
        math.comb(successes, value) * math.comb(population - successes, draws - value)
        for value in range(overlap, upper + 1)
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
        "published_overlap_items",
        "final_layer",
        "conservative_support",
    ]
    rows = pd.read_csv(CANONICAL, sep="\t", usecols=columns, low_memory=False)
    rows = rows.loc[
        rows["broad_network"].eq(NETWORK_NAME)
        & rows["key_driver"].eq(DRIVER)
        & truth_series(rows["conservative_support"])
    ].copy()
    rows["final_layer"] = pd.to_numeric(rows["final_layer"], errors="raise").astype(int)
    rows = rows.sort_values("kda_run_id").reset_index(drop=True)
    require(len(rows) == SUPPORTING_RUNS, f"Expected {SUPPORTING_RUNS} supporting runs, found {len(rows)}")
    require(rows["kda_run_id"].is_unique, "Supporting run IDs are not unique")
    require(rows["final_layer"].between(1, MAX_DOWNSTREAM_DEPTH).all(), "A final layer lies beyond D2")
    return rows


def load_graph() -> nx.DiGraph:
    edges = pd.read_csv(NETWORK, sep="\t", header=None, names=["source", "target"])
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    require(nx.is_directed_acyclic_graph(graph), "The astrocyte Bayesian network is not acyclic")
    require(graph.number_of_nodes() == 8285 and graph.number_of_edges() == 8881, "Unexpected network dimensions")
    require(DRIVER in graph, "APOE is absent from the astrocyte Bayesian network")
    require(set(graph.predecessors(DRIVER)) == EXPECTED_DIRECT_IN, "APOE direct incoming edges changed")
    require(set(graph.successors(DRIVER)) == EXPECTED_DIRECT_OUT, "APOE direct outgoing edges changed")
    return graph


def load_run_backgrounds(run_ids: set[str]) -> dict[str, set[str]]:
    backgrounds = {run_id: set() for run_id in run_ids}
    for chunk in pd.read_csv(BACKGROUNDS, sep="\t", usecols=["kda_run_id", "gene"], chunksize=500_000):
        selected = chunk.loc[chunk["kda_run_id"].isin(run_ids)]
        for run_id, group in selected.groupby("kda_run_id"):
            backgrounds[str(run_id)].update(group["gene"].astype(str))
    require(all(backgrounds.values()), "At least one supporting run lacks an effective background")
    return backgrounds


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


def radial_positions() -> dict[str, tuple[float, float]]:
    positions = {
        DRIVER: (0.0, 0.0),
        "CKB": (-2.45, 1.22),
        "GPX4": (-4.45, 1.78),
        "LAPTM4A": (-2.45, -1.22),
        "ITM2B": (-4.45, -1.78),
    }
    for gene, angle_degrees in D1_ANGLES_DEGREES.items():
        angle = math.radians(angle_degrees)
        positions[gene] = (3.15 * math.cos(angle), 3.15 * math.sin(angle))
    for gene, angle_degrees in D2_ANGLES_DEGREES.items():
        angle = math.radians(angle_degrees)
        positions[gene] = (5.05 * math.cos(angle), 5.05 * math.sin(angle))
    return positions


def build_consensus_tables(
    graph: nx.DiGraph,
    support_rows: pd.DataFrame,
    backgrounds: dict[str, set[str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    neighborhood_occurrence: Counter[str] = Counter()
    query_hit_occurrence: Counter[str] = Counter()
    for row in support_rows.itertuples(index=False):
        induced = graph.subgraph(backgrounds[str(row.kda_run_id)])
        require(DRIVER in induced, f"APOE is absent from the effective background for {row.kda_run_id}")
        lengths = nx.single_source_shortest_path_length(induced, DRIVER, cutoff=int(row.final_layer))
        neighborhood_occurrence.update(lengths.keys())
        query_hit_occurrence.update(split_genes(row.published_overlap_items))

    retained_hits = {
        gene for gene, count in query_hit_occurrence.items() if count >= QUERY_HIT_THRESHOLD
    }
    require(retained_hits == EXPECTED_QUERY_HITS, f"Unexpected retained query hits: {sorted(retained_hits)}")
    require(neighborhood_occurrence[DRIVER] == SUPPORTING_RUNS, "APOE is not present in every supporting neighborhood")
    require(max(neighborhood_occurrence.values()) <= SUPPORTING_RUNS, "Neighborhood occurrence exceeds four runs")

    downstream_lengths = nx.single_source_shortest_path_length(graph, DRIVER, cutoff=MAX_DOWNSTREAM_DEPTH)
    upstream_lengths = nx.single_source_shortest_path_length(
        graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH
    )
    upstream_context = set(upstream_lengths) - {DRIVER}
    require(upstream_context == EXPECTED_UPSTREAM_CONTEXT, "APOE upstream context changed")

    path_nodes = {DRIVER}
    for target in retained_hits:
        require(target in downstream_lengths, f"Retained hit is not within D2: {target}")
        for path in nx.all_shortest_paths(graph, DRIVER, target):
            require(len(path) - 1 <= MAX_DOWNSTREAM_DEPTH, f"A shortest path exceeds D2: {target}")
            path_nodes.update(path)

    display_nodes = path_nodes | EXPECTED_DIRECT_IN | EXPECTED_DIRECT_OUT | upstream_context
    display = graph.subgraph(display_nodes).copy()
    require(display.number_of_nodes() == 19, f"Expected 19 display nodes, found {display.number_of_nodes()}")
    require(display.number_of_edges() == 18, f"Expected 18 display edges, found {display.number_of_edges()}")
    require(nx.is_tree(display.to_undirected()), "Displayed APOE graph is not a tree")
    require(set(radial_positions()) == display_nodes, "Fixed layout does not match displayed nodes")

    annotation = load_annotation(display_nodes)
    deg = load_deg(display_nodes)
    positions = radial_positions()
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
        if gene in path_nodes and gene not in retained_hits and gene != DRIVER:
            reasons.append("shortest_path_connector")
        evidence = deg[gene]
        neighborhood_count = int(neighborhood_occurrence.get(gene, 0))
        hit_count = int(query_hit_occurrence.get(gene, 0))
        node_rows.append(
            {
                "schema_version": SCHEMA,
                "network": NETWORK_NAME,
                "gene": gene,
                "included_reason": "|".join(reasons),
                "directed_depth_from_apoe": downstream_lengths.get(gene) if gene != DRIVER else 0,
                "upstream_depth_to_apoe": upstream_lengths.get(gene) if gene != DRIVER else None,
                "is_direct_incoming_neighbor": gene in EXPECTED_DIRECT_IN,
                "is_direct_outgoing_neighbor": gene in EXPECTED_DIRECT_OUT,
                "supporting_neighborhood_occurrence_count": neighborhood_count,
                "supporting_neighborhood_occurrence_fraction": neighborhood_count / SUPPORTING_RUNS,
                "query_hit_occurrence_count": hit_count,
                "query_hit_occurrence_fraction": hit_count / SUPPORTING_RUNS,
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
                "layout_x": positions[gene][0],
                "layout_y": positions[gene][1],
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
                "is_directly_incident_to_apoe": source == DRIVER or target == DRIVER,
                "is_upstream_context_edge": source in upstream_context,
                "source_directed_depth": downstream_lengths.get(source),
                "target_directed_depth": downstream_lengths.get(target),
                "source_upstream_depth": upstream_lengths.get(source) if source != DRIVER else None,
                "target_upstream_depth": upstream_lengths.get(target) if target != DRIVER else None,
                "source_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(source, 0),
                "target_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(target, 0),
            }
        )

    sensitivity_rows = []
    for threshold in range(1, SUPPORTING_RUNS + 1):
        hits = {gene for gene, count in query_hit_occurrence.items() if count >= threshold}
        threshold_path_nodes = {DRIVER}
        for target in hits:
            for path in nx.all_shortest_paths(graph, DRIVER, target):
                if len(path) - 1 <= MAX_DOWNSTREAM_DEPTH:
                    threshold_path_nodes.update(path)
        threshold_nodes = threshold_path_nodes | EXPECTED_DIRECT_IN | EXPECTED_DIRECT_OUT | upstream_context
        threshold_graph = graph.subgraph(threshold_nodes)
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
    return pd.DataFrame(node_rows), pd.DataFrame(edge_rows), pd.DataFrame(sensitivity_rows)


def load_gene_sets() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with MSIGDB.open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            require(len(fields) >= 3, "Malformed MSigDB GMT row")
            result.append({"pathway": fields[0], "url": fields[1], "genes": set(fields[2:])})
    require(len(result) == 4115, f"Expected 4,115 MSigDB pathways, found {len(result)}")
    return result


def build_pathway_tables(graph: nx.DiGraph, nodes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gene_sets = load_gene_sets()
    annotated_universe = set().union(*(row["genes"] for row in gene_sets))
    background = set(graph.nodes) & annotated_universe
    displayed = set(nodes["gene"]) & background
    require(len(background) == 5769, f"Unexpected mapped astrocyte background size: {len(background)}")
    require(len(displayed) == 19, f"Unexpected mapped displayed-gene count: {len(displayed)}")

    rows: list[dict[str, Any]] = []
    for gene_set in gene_sets:
        members = gene_set["genes"] & background
        if not 15 <= len(members) <= 500:
            continue
        overlap = displayed & members
        raw_p = hypergeom_upper_tail(len(overlap), len(background), len(members), len(displayed))
        fold = (
            (len(overlap) / len(displayed)) / (len(members) / len(background))
            if overlap
            else 0.0
        )
        rows.append(
            {
                "schema_version": SCHEMA,
                "library": "MSigDB C2:CP v2026.1 Hs symbols",
                "network": NETWORK_NAME,
                "pathway": gene_set["pathway"],
                "pathway_url": gene_set["url"],
                "background_definition": "all astrocyte Bayesian-network genes represented in MSigDB C2:CP",
                "background_gene_count": len(background),
                "displayed_mapped_gene_count": len(displayed),
                "pathway_background_gene_count": len(members),
                "overlap_gene_count": len(overlap),
                "overlap_genes": ";".join(sorted(overlap)),
                "fold_enrichment": fold,
                "raw_hypergeometric_p": raw_p,
            }
        )
    require(len(rows) == 1594, f"Unexpected eligible pathway-test count: {len(rows)}")
    adjusted = benjamini_hochberg([float(row["raw_hypergeometric_p"]) for row in rows])
    theme_by_pathway = {theme["pathway"]: theme for theme in PATHWAY_THEMES}
    for row, q_value in zip(rows, adjusted):
        row["bh_fdr"] = q_value
        theme = theme_by_pathway.get(row["pathway"])
        selected = bool(theme and int(row["overlap_gene_count"]) >= 2)
        row["selected_contextual_representative"] = selected
        row["pathway_code"] = theme["code"] if selected else None
        row["pathway_display_label"] = theme["label"] if selected else None
        row["pathway_color"] = theme["color"] if selected else None
        row["selection_rule"] = (
            "nonredundant contextual representative with at least 2 displayed members; no FDR-significance claim"
            if selected
            else None
        )
    rows.sort(key=lambda row: (float(row["raw_hypergeometric_p"]), str(row["pathway"])))

    selected = {row["pathway"]: row for row in rows if row["selected_contextual_representative"]}
    require(set(selected) == set(theme_by_pathway), "Selected pathway representatives changed")
    memberships: list[dict[str, Any]] = []
    for theme in PATHWAY_THEMES:
        result = selected[theme["pathway"]]
        overlap = set(split_genes(result["overlap_genes"]))
        require(overlap == theme["expected_members"], f"Unexpected {theme['label']} membership: {sorted(overlap)}")
        for gene in sorted(overlap):
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
                    "fdr_significant_0_05": float(result["bh_fdr"]) < 0.05,
                }
            )
    require(not any(row["fdr_significant_0_05"] for row in memberships), "A selected contextual theme became FDR significant")
    return pd.DataFrame(rows), pd.DataFrame(memberships)


def node_radius(gene: str, neighborhood_count: int) -> float:
    if gene == DRIVER:
        return 0.55
    if gene in EXPECTED_UPSTREAM_CONTEXT:
        return 0.43
    return 0.39 + 0.022 * neighborhood_count


def add_pathway_ring(
    ax: mpl.axes.Axes,
    center: tuple[float, float],
    radius: float,
    colors: list[str],
) -> None:
    if not colors:
        return
    segment = 360.0 / len(colors)
    for index, color in enumerate(colors):
        ax.add_patch(
            Wedge(
                center,
                radius + 0.09,
                90.0 + index * segment,
                90.0 + (index + 1) * segment - (2.0 if len(colors) > 1 else 0.0),
                width=0.055,
                facecolor=color,
                edgecolor="none",
                zorder=4,
            )
        )


def plot_figure(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    membership: pd.DataFrame,
    pathway_ora: pd.DataFrame,
    output_dir: Path,
) -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    node_by_gene = nodes.set_index("gene")
    positions = {row.gene: (float(row.layout_x), float(row.layout_y)) for row in nodes.itertuples()}
    memberships_by_gene = {
        gene: group.sort_values("pathway_code")["pathway_color"].tolist()
        for gene, group in membership.groupby("gene")
    }
    selected_ora = pathway_ora.loc[truth_series(pathway_ora["selected_contextual_representative"])].set_index("pathway")

    fig = plt.figure(figsize=(18.0, 11.0), facecolor="white")
    network_ax = fig.add_axes([0.035, 0.075, 0.69, 0.79])
    legend_ax = fig.add_axes([0.755, 0.075, 0.225, 0.79])
    fig.text(0.045, 0.945, "APOE-centered astrocyte consensus network", fontsize=25, weight="bold", color="#111111")
    fig.text(
        0.045,
        0.905,
        "U1-U2 nodes are upstream context; D1-D2 nodes lie downstream; arrows follow the Bayesian-network direction",
        fontsize=13,
        color="#4D4D4D",
    )

    network_ax.set_aspect("equal")
    network_ax.set_xlim(-5.35, 5.7)
    network_ax.set_ylim(-5.45, 5.45)
    network_ax.axis("off")

    # Draw model-directed edges beneath the nodes. APOE-incident edges are darker and thicker.
    for row in edges.itertuples(index=False):
        direct = bool(row.is_directly_incident_to_apoe)
        arrow = FancyArrowPatch(
            positions[row.source],
            positions[row.target],
            arrowstyle="-|>",
            mutation_scale=13 if direct else 11,
            linewidth=2.05 if direct else 1.25,
            color="#4D4D4D" if direct else "#A0A0A0",
            alpha=0.93,
            shrinkA=29,
            shrinkB=31,
            connectionstyle="arc3,rad=0.0",
            zorder=1,
        )
        network_ax.add_patch(arrow)

    for gene, row in node_by_gene.iterrows():
        center = positions[gene]
        radius = node_radius(gene, int(row["supporting_neighborhood_occurrence_count"]))
        colors = memberships_by_gene.get(gene, [])
        add_pathway_ring(network_ax, center, radius, colors)
        is_hit = bool(row["is_query_hit_meeting_display_threshold"])
        fill = DEG_COLORS[str(row["phase08_deg_class"])]
        if gene == DRIVER:
            fill = "#303030"
        network_ax.add_patch(
            Circle(
                center,
                radius,
                facecolor=fill,
                edgecolor="#111111" if is_hit or gene == DRIVER else "#5A5A5A",
                linewidth=3.2 if is_hit else (2.5 if gene == DRIVER else 1.25),
                zorder=5,
            )
        )
        if gene in EXPECTED_UPSTREAM_CONTEXT:
            level = int(float(row["upstream_depth_to_apoe"]))
            second_line = f"U{level}"
        else:
            second_line = f"{int(row['supporting_neighborhood_occurrence_count'])}/{SUPPORTING_RUNS}"
        text_color = "white" if gene == DRIVER else "#111111"
        font_size = 8.0 if len(gene) >= 8 else 8.8
        network_ax.text(
            center[0],
            center[1] + 0.075,
            gene,
            ha="center",
            va="center",
            fontsize=font_size + (1.8 if gene == DRIVER else 0.0),
            weight="bold",
            color=text_color,
            zorder=6,
        )
        network_ax.text(
            center[0],
            center[1] - 0.16,
            second_line,
            ha="center",
            va="center",
            fontsize=7.3 if gene != DRIVER else 8.2,
            color=text_color,
            zorder=6,
        )

    # Minimal radial labels orient the viewer without adding guide rings.
    network_ax.text(-4.6, 2.58, "upstream context", fontsize=10, color="#666666", ha="center")
    network_ax.text(2.8, 5.05, "downstream neighborhood", fontsize=10, color="#666666", ha="center")

    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis("off")
    legend_ax.plot([0.0, 0.0], [0.0, 1.0], color="#D0D0D0", linewidth=1.0, transform=legend_ax.transAxes)

    def heading(y: float, label: str) -> None:
        legend_ax.text(0.06, y, label, fontsize=12.5, weight="bold", color="#111111", va="top")

    heading(0.98, "HOW TO READ")
    legend_ax.text(0.06, 0.935, "Gene + x/4 = neighborhood occurrence", fontsize=9.2, color="#333333", va="top")
    legend_ax.text(0.06, 0.903, "U1/U2 = upstream distance to APOE", fontsize=9.2, color="#333333", va="top")
    legend_ax.add_patch(Circle((0.09, 0.847), 0.025, transform=legend_ax.transAxes, facecolor="white", edgecolor="#111111", linewidth=2.8))
    legend_ax.text(0.15, 0.847, "Query hit observed in >=1 of 4 runs", transform=legend_ax.transAxes, va="center", fontsize=9.2)
    legend_ax.annotate("", xy=(0.135, 0.795), xytext=(0.055, 0.795), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": "#666666", "lw": 1.7})
    legend_ax.text(0.15, 0.795, "Bayesian-network direction", transform=legend_ax.transAxes, va="center", fontsize=9.2)
    legend_ax.text(0.06, 0.755, "Larger node = seen in more supporting\nrun-specific neighborhoods", fontsize=9.2, color="#333333", va="top", linespacing=1.25)

    heading(0.68, "NODE FILL: DIRECT DEG")
    y = 0.63
    for deg_class in ("up_only", "down_only", "mixed", "not_deg"):
        legend_ax.add_patch(Rectangle((0.06, y - 0.017), 0.034, 0.034, transform=legend_ax.transAxes, facecolor=DEG_COLORS[deg_class], edgecolor="#555555", linewidth=0.8))
        legend_ax.text(0.12, y, DEG_LABELS[deg_class], transform=legend_ax.transAxes, va="center", fontsize=9.2)
        y -= 0.044

    heading(0.435, "PATHWAY OUTLINE")
    legend_ax.text(0.06, 0.396, "Contextual annotations; none has BH FDR < 0.05", fontsize=8.8, color="#555555", va="top")
    y = 0.342
    for theme in PATHWAY_THEMES:
        result = selected_ora.loc[theme["pathway"]]
        legend_ax.add_patch(Circle((0.078, y), 0.018, transform=legend_ax.transAxes, facecolor="white", edgecolor=theme["color"], linewidth=3.0))
        legend_ax.text(0.12, y + 0.010, theme["label"], transform=legend_ax.transAxes, va="center", fontsize=9.0, weight="bold")
        legend_ax.text(0.12, y - 0.016, f"n={int(result['overlap_gene_count'])}; FDR={float(result['bh_fdr']):.3g}", transform=legend_ax.transAxes, va="center", fontsize=8.2, color="#555555")
        y -= 0.061

    heading(0.135, "DISPLAY SCOPE")
    legend_ax.text(
        0.06,
        0.095,
        "19 nodes / 18 edges\nAll 2 incoming + 11 outgoing APOE edges\nD2 paths to all 7 observed query hits",
        fontsize=8.9,
        color="#333333",
        va="top",
        linespacing=1.3,
    )
    fig.text(
        0.045,
        0.025,
        "Display threshold: >=1/4 supporting runs (coverage choice, not a significance cutoff). Directional edges are model-derived hypotheses.",
        fontsize=10.5,
        color="#555555",
    )

    for suffix in ("png", "pdf", "svg"):
        destination = output_dir / f"{FIGURE_STEM}.{suffix}"
        fig.savefig(destination, dpi=240 if suffix == "png" else None, facecolor="white")
    plt.close(fig)


def write_tsv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="")
    require(path.exists() and path.stat().st_size > 0, f"Failed to write {path}")


def write_graphml(path: Path, nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame) -> None:
    graph = nx.DiGraph(network=NETWORK_NAME, driver=DRIVER, query_hit_display_threshold="1/4")
    memberships_by_gene = {
        gene: ";".join(group.sort_values("pathway_code")["pathway_code"].astype(str))
        for gene, group in membership.groupby("gene")
    }
    for row in nodes.to_dict(orient="records"):
        gene = str(row.pop("gene"))
        attributes = {
            key: ("" if pd.isna(value) else value)
            for key, value in row.items()
            if key != "schema_version"
        }
        attributes["pathway_codes"] = memberships_by_gene.get(gene, "")
        graph.add_node(gene, **attributes)
    for row in edges.to_dict(orient="records"):
        source = str(row.pop("source"))
        target = str(row.pop("target"))
        attributes = {
            key: ("" if pd.isna(value) else value)
            for key, value in row.items()
            if key != "schema_version"
        }
        graph.add_edge(source, target, **attributes)
    nx.write_graphml(graph, path)
    require(path.exists() and path.stat().st_size > 0, "GraphML export failed")


def format_fdr(value: float) -> str:
    return f"{value:.3g}"


def write_documentation(
    output_dir: Path,
    pathway_ora: pd.DataFrame,
    nodes: pd.DataFrame,
) -> None:
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_contextual_representative"])].set_index("pathway")
    theme_sentences = []
    for theme in PATHWAY_THEMES:
        row = selected.loc[theme["pathway"]]
        theme_sentences.append(
            f"{theme['label']} ({int(row['overlap_gene_count'])} genes; BH FDR = {format_fdr(float(row['bh_fdr']))})"
        )
    caption = f"""# APOE astrocyte consensus network with pathway outlines

APOE-centered astrocyte Bayesian-network neighborhood reconstructed from the four conservative-support APOE runs. Arrows follow the stored Bayesian-network direction and should be interpreted as model-derived regulatory hypotheses, not experimental proof of direct regulation. The display retains both direct incoming APOE edges, all 11 direct outgoing edges, two upstream extensions, and the paths to every mitochondrial query hit observed in at least one supporting run.

The 1/4 display threshold yields 19 nodes and 18 edges, including seven query hits: `AGT`, `ATP5F1A`, `ATP5PB`, `CHCHD10`, `LDHB`, `NME3`, and `TUFM`. It was selected because increasing the threshold to 2/4 removes three observed hits while reducing the display by only two nodes. The threshold is a coverage choice for visualization, not a significance cutoff. For downstream nodes, node size and `x/4` show how many run-specific selected APOE neighborhoods contained the gene; this is distinct from query-hit recurrence. Upstream nodes are labeled U1 or U2. Thick black borders identify query hits meeting the threshold. Fill shows stored Phase 8 direct-DEG direction.

Colored outer boundaries show three nonredundant contextual annotations: {', '.join(theme_sentences)}. None meets BH FDR < 0.05 after testing 1,594 pathways, so the rings organize biological context and are not claims of significant enrichment. Absence of an outline means only that a gene is not in these displayed representatives.
"""
    methods = f"""# Methods: APOE astrocyte consensus network

## End product

The figure is a 19-node, 18-edge directed tree centered on APOE. It includes every direct APOE edge in the full astrocyte Bayesian network (`CKB -> APOE`, `LAPTM4A -> APOE`, and 11 APOE outgoing edges), the second upstream steps `GPX4 -> CKB` and `ITM2B -> LAPTM4A`, and the shortest paths through D2 to the retained query hits.

## Consensus reconstruction and display threshold

Four rows with conservative APOE support in the Astrocytes broad network were read from `call_key_driver_returns.tsv`. For each row, the astrocyte Bayesian network was restricted to that run's recorded effective KDA background. The downstream APOE neighborhood was then reconstructed through its selected final layer (D1 or D2). Neighborhood occurrence counts how many of these four run-specific neighborhoods contain a gene. Query-hit occurrence was separately counted from `published_overlap_items`.

The display threshold is at least one query-hit occurrence among four supporting runs (1/4). Threshold profiling showed: 1/4 retains 7 hits and yields 19 nodes; 2/4 retains 4 hits and yields 17 nodes; 3/4 retains 3 hits and still yields 17 nodes; 4/4 retains 1 hit and yields 16 nodes. Because 2/4 would lose `ATP5F1A`, `CHCHD10`, and `NME3` for only a two-node reduction, 1/4 was chosen to preserve information without making the graph crowded. This is solely a figure inclusion rule, not a new statistical threshold.

## Node and edge encodings

Arrows retain the direction in `data/bayesian_network/Astrocytes/result.links3.links.txt`. APOE-incident edges are darker and thicker. Thick black node borders mark query hits meeting 1/4. For downstream nodes, size and the printed `x/4` value encode supporting-neighborhood occurrence. U1/U2 labels denote upstream graph distance and do not represent downstream KDA occurrence. Node fill summarizes direct differential-expression records in `astrocytes.yu_mast_de.tsv.gz`: orange is AD-up only, blue is AD-down only, yellow is both directions, and gray has no stored direct DEG.

## Pathway annotations

Over-representation analysis used MSigDB C2:CP v2026.1 human gene symbols. The custom universe comprised 5,769 astrocyte Bayesian-network genes represented in the library; all 19 displayed genes mapped. One-sided hypergeometric tests were performed for 1,594 pathways with 15-500 mapped background genes and corrected by Benjamini-Hochberg. The displayed pathway representatives are {', '.join(theme_sentences)}. No selected theme has BH FDR < 0.05. They were chosen as nonredundant contextual annotations with at least two displayed members; the rings must not be interpreted as significant pathway enrichment, pathway activity, or causality.

## Rendering and limitations

The validated graph tables were rendered in Cytoscape 3.10.4 using a deterministic, collision-checked radial layout. APOE is centered; U1 and U2 occupy the left context sector at radii 300 and 510 Cytoscape units, while D1 and D2 use radii 480 and 720. No guide rings are drawn. Colored outer outlines are rendered with Cytoscape enhancedGraphics. PNG is exported at 300% zoom, PDF and SVG are retained as vector formats, and the editable `.cys` session and Cytoscape visual-style XML are saved beside the figure. The graph is a focused display rather than the full 8,285-node astrocyte network. Bayesian-network direction is a model-derived hypothesis, and all biological interpretations require independent validation.
"""
    (output_dir / f"{FIGURE_STEM}_caption.md").write_text(caption, encoding="utf-8")
    (output_dir / f"{FIGURE_STEM}_methods.md").write_text(methods, encoding="utf-8")


def validate_outputs(output_dir: Path, nodes: pd.DataFrame, edges: pd.DataFrame, pathway_ora: pd.DataFrame) -> pd.DataFrame:
    png = output_dir / f"{FIGURE_STEM}.png"
    pdf = output_dir / f"{FIGURE_STEM}.pdf"
    svg = output_dir / f"{FIGURE_STEM}.svg"
    with Image.open(png) as image:
        width, height = image.size
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_contextual_representative"])]
    checks = [
        ("supporting_run_count", SUPPORTING_RUNS == 4, str(SUPPORTING_RUNS)),
        ("selected_threshold", QUERY_HIT_THRESHOLD == 1, "1/4"),
        ("node_count", len(nodes) == 19, str(len(nodes))),
        ("edge_count", len(edges) == 18, str(len(edges))),
        ("query_hit_count", int(truth_series(nodes["is_query_hit_meeting_display_threshold"]).sum()) == 7, "7"),
        ("all_direct_incoming", int(truth_series(nodes["is_direct_incoming_neighbor"]).sum()) == 2, "2"),
        ("all_direct_outgoing", int(truth_series(nodes["is_direct_outgoing_neighbor"]).sum()) == 11, "11"),
        ("pathway_representative_count", len(selected) == 3, str(len(selected))),
        ("no_selected_pathway_fdr_below_0_05", not (selected["bh_fdr"] < 0.05).any(), str(selected["bh_fdr"].min())),
        ("png_dimensions", width >= 2200 and height >= 1300, f"{width}x{height}"),
        ("png_nonempty", png.stat().st_size > 100_000, str(png.stat().st_size)),
        ("pdf_nonempty", pdf.stat().st_size > 5_000, str(pdf.stat().st_size)),
        ("svg_nonempty", svg.stat().st_size > 20_000, str(svg.stat().st_size)),
        (
            "cytoscape_session_nonempty",
            (output_dir / f"{FIGURE_STEM}_cytoscape.cys").stat().st_size > 10_000,
            str((output_dir / f"{FIGURE_STEM}_cytoscape.cys").stat().st_size),
        ),
        (
            "cytoscape_style_nonempty",
            (output_dir / f"{FIGURE_STEM}_cytoscape_style.xml").stat().st_size > 5_000,
            str((output_dir / f"{FIGURE_STEM}_cytoscape_style.xml").stat().st_size),
        ),
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
    rows = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path != manifest_path:
            rows.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_tsv(manifest_path, pd.DataFrame(rows))


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_rows = load_support_rows()
    graph = load_graph()
    backgrounds = load_run_backgrounds(set(support_rows["kda_run_id"].astype(str)))
    nodes, edges, sensitivity = build_consensus_tables(graph, support_rows, backgrounds)
    pathway_ora, pathway_membership = build_pathway_tables(graph, nodes)

    table_outputs = {
        f"{OUTPUT_PREFIX}_network_nodes.tsv": nodes,
        f"{OUTPUT_PREFIX}_network_edges.tsv": edges,
        f"{OUTPUT_PREFIX}_pathway_ora.tsv": pathway_ora,
        f"{OUTPUT_PREFIX}_pathway_membership.tsv": pathway_membership,
        f"{OUTPUT_PREFIX}_threshold_sensitivity.tsv": sensitivity,
    }
    for filename, frame in table_outputs.items():
        write_tsv(output_dir / filename, frame)
    write_graphml(output_dir / "phase18_apoe_astrocyte.graphml", nodes, edges, pathway_membership)
    # Cytoscape is the authoritative rendering engine. The legacy Matplotlib
    # plotting function remains above only to document the superseded design.
    from render_phase18_apoe_astrocyte_cytoscape import render as render_cytoscape

    render_cytoscape(output_dir, output_dir, png_zoom=300)
    write_documentation(output_dir, pathway_ora, nodes)
    checks = validate_outputs(output_dir, nodes, edges, pathway_ora)
    write_tsv(output_dir / f"{FIGURE_STEM}_checks.tsv", checks)
    write_manifest(output_dir)

    selected = pathway_ora.loc[truth_series(pathway_ora["selected_contextual_representative"])]
    print(f"Wrote {output_dir / (FIGURE_STEM + '.png')}")
    print(f"Display: {len(nodes)} nodes, {len(edges)} edges, 7 query hits at >=1/4")
    print(f"Contextual pathway FDR range: {selected['bh_fdr'].min():.4g}-{selected['bh_fdr'].max():.4g}; none < 0.05")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir.resolve())


if __name__ == "__main__":
    main()
