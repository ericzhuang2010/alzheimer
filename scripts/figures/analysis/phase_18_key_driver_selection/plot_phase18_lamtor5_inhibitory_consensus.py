#!/usr/bin/env python3
"""Build and render the Phase 18 LAMTOR5 inhibitory consensus network in Cytoscape."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import py4cytoscape as p4c
from PIL import Image

import plot_phase18_cox7c_inhibitory_consensus as common


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "LAMTOR5"
    / "inhibitory"
)
CANONICAL = ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
BACKGROUNDS = ROOT / "results/minerva_production/12_kda/kda_background_members.tsv.gz"
SIGNATURES = ROOT / "results/minerva_production/12_kda/kda_signature_members.tsv"
NETWORK = ROOT / "data/bayesian_network/Inhibitory_neurons/result.links3.links.txt"
ANNOTATION = ROOT / "results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz"
MAST_FILES = [ROOT / "results/minerva_production/08_mast/inhibitory.yu_mast_de.tsv.gz"]
MSIGDB = ROOT / "data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt"

DRIVER = "LAMTOR5"
NETWORK_NAME = "Inhibitory_neurons"
NETWORK_LABEL = "Inhibitory neurons"
SUPPORTING_RUNS = 5
QUERY_HIT_THRESHOLD = 1
MAX_DOWNSTREAM_DEPTH = 3
MAX_UPSTREAM_DEPTH = 2
SCHEMA = "phase18_lamtor5_inhibitory_consensus_v1"
OUTPUT_PREFIX = "phase18_lamtor5_inhibitory_consensus"
FIGURE_STEM = "phase18_lamtor5_inhibitory_consensus_network_pathways"
STYLE_NAME = "Phase18 LAMTOR5 inhibitory radial consensus pathway outlines"

EXPECTED_DIRECT_IN = {"COX7C"}
EXPECTED_DIRECT_OUT = {
    "ATP5PF", "DAD1", "ERH", "LSM1", "MAML1", "PFDN4", "POLR2K",
    "PYURF", "SPCS2",
}
EXPECTED_UPSTREAM_CONTEXT = {"COX7C", "RPS15"}
EXPECTED_QUERY_HITS = {
    "ATP5IF1", "ATP5MG", "ATP5PF", "CISD1", "COX5A", "MRPL50",
    "MRPS14", "NDUFB1", "NDUFB2", "NDUFB4", "NDUFB9", "NDUFS3",
    "PAICS", "SOD1",
}
PATHWAY_THEMES = (
    {
        "pathway": "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA",
        "code": "O",
        "label": "ETC / oxidative phosphorylation",
        "color": "#0072B2",
        "expected_members": {
            "ATP5IF1", "ATP5MG", "ATP5PF", "COX5A", "COX7C", "NDUFA12",
            "NDUFB1", "NDUFB2", "NDUFB4", "NDUFB9", "NDUFS3",
        },
        "must_be_significant": True,
    },
    {
        "pathway": "REACTOME_COMPLEX_I_BIOGENESIS",
        "code": "I",
        "label": "Mitochondrial complex I biogenesis",
        "color": "#009E73",
        "expected_members": {"NDUFA12", "NDUFB1", "NDUFB2", "NDUFB4", "NDUFB9", "NDUFS3", "PYURF"},
        "must_be_significant": True,
    },
    {
        "pathway": "REACTOME_MITOCHONDRIAL_PROTEIN_DEGRADATION",
        "code": "D",
        "label": "Mitochondrial protein degradation",
        "color": "#D55E00",
        "expected_members": {"ATP5MG", "ATP5PF", "COX5A", "NDUFS3"},
        "must_be_significant": True,
    },
    {
        "pathway": "REACTOME_TRANSLATION",
        "code": "T",
        "label": "Translation",
        "color": "#7B3294",
        "expected_members": {"MRPL50", "MRPS14", "RPS15", "SPCS2", "SRP14"},
        "must_be_significant": False,
    },
    {
        "pathway": "REACTOME_MTORC1_MEDIATED_SIGNALLING",
        "code": "M",
        "label": "mTORC1-mediated signaling",
        "color": "#CC79A7",
        "expected_members": {"LAMTOR5"},
        "must_be_significant": False,
    },
)

DEG_COLORS = common.DEG_COLORS
DEG_LABELS = common.DEG_LABELS
PATHWAY_OUTLINE_PADDING = 32.0
COLLISION_PADDING = 16.0
U1_RADIUS = 360.0
U2_RADIUS = 620.0
D1_RADIUS = 650.0
D2_RADIUS = 950.0
D3_RADIUS = 1250.0
D1_ANGLES = {
    "DAD1": -160.0,
    "ERH": -130.0,
    "LSM1": -100.0,
    "ATP5PF": -60.0,
    "MAML1": -20.0,
    "PFDN4": 20.0,
    "PYURF": 60.0,
    "POLR2K": 105.0,
    "SPCS2": 150.0,
}
D2_ANGLES = {
    "ATP5IF1": -150.0,
    "NDUFA12": -115.0,
    "NDUFB2": -80.0,
    "NDUFS3": -45.0,
    "RAB11A": -10.0,
    "SOD1": 25.0,
    "MRPS14": 100.0,
    "SRP14": 140.0,
}
D3_ANGLES = {
    "ATP5MG": -160.0,
    "COX5A": -130.0,
    "NDUFB1": -100.0,
    "NDUFB9": -70.0,
    "PAICS": -10.0,
    "CISD1": 25.0,
    "NDUFB4": 55.0,
    "MRPL50": 140.0,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth_series(series: pd.Series) -> pd.Series:
    return common.truth_series(series)


def configure_common() -> None:
    """Point shared pure helpers at the LAMTOR5 analysis inputs."""
    common.BACKGROUNDS = BACKGROUNDS
    common.SIGNATURES = SIGNATURES
    common.ANNOTATION = ANNOTATION
    common.MSIGDB = MSIGDB
    common.DRIVER = DRIVER
    common.NETWORK_NAME = NETWORK_NAME
    common.SUPPORTING_RUNS = SUPPORTING_RUNS
    common.QUERY_HIT_THRESHOLD = QUERY_HIT_THRESHOLD
    common.SCHEMA = SCHEMA
    common.OUTPUT_PREFIX = OUTPUT_PREFIX
    common.FIGURE_STEM = FIGURE_STEM
    common.STYLE_NAME = STYLE_NAME
    common.PATHWAY_THEMES = PATHWAY_THEMES


def load_support_rows() -> pd.DataFrame:
    columns = [
        "kda_run_id", "broad_network", "key_driver", "final_layer",
        "final_overlap_count", "self_excluded", "conservative_support",
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
    require(len(rows) == SUPPORTING_RUNS, f"Expected {SUPPORTING_RUNS} supporting runs, found {len(rows)}")
    require(rows["kda_run_id"].is_unique, "Supporting run IDs are not unique")
    require(rows["final_layer"].between(2, 3).all(), "A supporting final layer lies outside D2-D3")
    require(not truth_series(rows["self_excluded"]).any(), "LAMTOR5 was unexpectedly self-excluded")
    return rows


def load_graph() -> nx.DiGraph:
    edges = pd.read_csv(NETWORK, sep="\t", header=None, names=["source", "target"])
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    require(nx.is_directed_acyclic_graph(graph), "The inhibitory Bayesian network is not acyclic")
    require(graph.number_of_nodes() == 9579 and graph.number_of_edges() == 10534, "Unexpected network dimensions")
    require(set(graph.predecessors(DRIVER)) == EXPECTED_DIRECT_IN, "LAMTOR5 direct incoming edges changed")
    require(set(graph.successors(DRIVER)) == EXPECTED_DIRECT_OUT, "LAMTOR5 direct outgoing edges changed")
    return graph


def load_deg(display_genes: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"up": 0, "down": 0})
    for path in MAST_FILES:
        rows = pd.read_csv(path, sep="\t", usecols=["gene", "paper_deg", "logFC"], low_memory=False)
        rows = rows.loc[rows["gene"].isin(display_genes) & truth_series(rows["paper_deg"])]
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
        require(nx.shortest_path_length(graph, DRIVER, target) <= MAX_DOWNSTREAM_DEPTH, f"Hit beyond D3: {target}")
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
        require(DRIVER in induced, f"LAMTOR5 is absent from the effective background for {run_id}")
        lengths = nx.single_source_shortest_path_length(induced, DRIVER, cutoff=int(row.final_layer))
        hits = signatures[run_id] & set(lengths)
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
                "driver_self_excluded": False,
                "reconstructed_query_hit_count": len(hits),
                "reconstructed_query_hits": ";".join(sorted(hits)),
            }
        )

    retained_hits = {gene for gene, count in query_hit_occurrence.items() if count >= QUERY_HIT_THRESHOLD}
    require(retained_hits == EXPECTED_QUERY_HITS, f"Unexpected retained query hits: {sorted(retained_hits)}")
    require(neighborhood_occurrence[DRIVER] == SUPPORTING_RUNS, "LAMTOR5 is not in all supporting neighborhoods")
    downstream_lengths = nx.single_source_shortest_path_length(graph, DRIVER, cutoff=MAX_DOWNSTREAM_DEPTH)
    upstream_lengths = nx.single_source_shortest_path_length(graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH)
    upstream_context = set(upstream_lengths) - {DRIVER}
    require(upstream_context == EXPECTED_UPSTREAM_CONTEXT, "LAMTOR5 upstream context changed")

    display = display_for_hits(graph, retained_hits)
    display_nodes = set(display)
    require(display.number_of_nodes() == 28 and display.number_of_edges() == 28, "Unexpected display dimensions")
    require(nx.is_directed_acyclic_graph(display) and nx.is_weakly_connected(display), "Displayed graph is invalid")
    annotation = common.load_annotation(display_nodes)
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
                "directed_depth_from_lamtor5": downstream_lengths.get(gene) if gene != DRIVER else 0,
                "upstream_depth_to_lamtor5": upstream_lengths.get(gene) if gene != DRIVER else None,
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

    edge_rows = [
        {
            "schema_version": SCHEMA,
            "network": NETWORK_NAME,
            "source": source,
            "target": target,
            "is_directly_incident_to_lamtor5": source == DRIVER or target == DRIVER,
            "is_upstream_context_edge": source in upstream_context and (target in upstream_context or target == DRIVER),
            "source_directed_depth": downstream_lengths.get(source),
            "target_directed_depth": downstream_lengths.get(target),
            "source_upstream_depth": upstream_lengths.get(source) if source != DRIVER else None,
            "target_upstream_depth": upstream_lengths.get(target) if target != DRIVER else None,
            "source_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(source, 0),
            "target_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(target, 0),
        }
        for source, target in sorted(display.edges)
    ]
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


def build_pathway_tables(graph: nx.DiGraph, nodes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gene_sets = common.load_gene_sets()
    annotated_universe = set().union(*(row["genes"] for row in gene_sets))
    background = set(graph.nodes) & annotated_universe
    displayed = set(nodes["gene"]) & background
    require(len(background) == 6537 and len(displayed) == 27, "Unexpected ORA background or mapped display size")
    rows: list[dict[str, Any]] = []
    for gene_set in gene_sets:
        members = gene_set["genes"] & background
        if not 15 <= len(members) <= 500:
            continue
        overlap = displayed & members
        raw_p = common.hypergeom_upper_tail(len(overlap), len(background), len(members), len(displayed))
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
    adjusted = common.benjamini_hochberg([float(row["raw_hypergeometric_p"]) for row in rows])
    themes = {theme["pathway"]: theme for theme in PATHWAY_THEMES}
    for row, q_value in zip(rows, adjusted):
        row["bh_fdr"] = q_value
        theme = themes.get(row["pathway"])
        row["selected_nonredundant_representative"] = bool(theme)
        row["pathway_code"] = theme["code"] if theme else None
        row["pathway_display_label"] = theme["label"] if theme else None
        row["pathway_color"] = theme["color"] if theme else None
        row["selection_rule"] = (
            "nonredundant representative; FDR-significant unless explicitly labeled contextual"
            if theme else None
        )
    rows.sort(key=lambda row: (float(row["raw_hypergeometric_p"]), str(row["pathway"])))
    selected = {row["pathway"]: row for row in rows if row["selected_nonredundant_representative"]}
    require(set(selected) == set(themes), "A selected pathway representative is missing")
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
    require(len(memberships) == 28, f"Expected 28 pathway membership rows, found {len(memberships)}")
    return pd.DataFrame(rows), pd.DataFrame(memberships)


def node_display_size(gene: str, occurrence_count: int) -> float:
    if gene == DRIVER:
        return 180.0
    recurrence_size = 120.0 + 5.0 * occurrence_count
    label_size = 132.0 + 7.0 * max(0, len(gene) - 5)
    return round(max(recurrence_size, label_size), 1)


def radial_positions(nodes: pd.DataFrame) -> tuple[dict[str, tuple[float, float]], float, str]:
    positions: dict[str, tuple[float, float]] = {
        DRIVER: (0.0, 0.0),
        "COX7C": (-U1_RADIUS, 0.0),
        "RPS15": (-U2_RADIUS, 0.0),
    }
    for gene_angles, radius in ((D1_ANGLES, D1_RADIUS), (D2_ANGLES, D2_RADIUS), (D3_ANGLES, D3_RADIUS)):
        for gene, angle_degrees in gene_angles.items():
            angle = math.radians(angle_degrees)
            positions[gene] = (radius * math.cos(angle), radius * math.sin(angle))
    require(set(positions) == set(nodes["gene"]), "Radial layout did not assign every node")
    sizes = {
        row.gene: node_display_size(row.gene, int(row.supporting_neighborhood_occurrence_count))
        + PATHWAY_OUTLINE_PADDING
        for row in nodes.itertuples()
    }
    minimum_clearance = float("inf")
    closest_pair = ""
    genes = nodes["gene"].tolist()
    for index, gene_a in enumerate(genes):
        for gene_b in genes[index + 1:]:
            distance = math.dist(positions[gene_a], positions[gene_b])
            required = (sizes[gene_a] + sizes[gene_b]) / 2.0 + COLLISION_PADDING
            clearance = distance - required
            if clearance < minimum_clearance:
                minimum_clearance = clearance
                closest_pair = f"{gene_a}/{gene_b}"
            require(clearance >= 0, f"Radial layout collision: {gene_a} and {gene_b}")
    return positions, minimum_clearance, closest_pair


def pathway_outline(codes: list[str]) -> str:
    if not codes:
        return ""
    colors = ",".join(next(theme["color"] for theme in PATHWAY_THEMES if theme["code"] == code) for code in codes)
    values = ",".join("1" for _ in codes)
    return (
        "circoschart: arcstart=270 firstarc=.78 firstarcwidth=.16 arcwidth=.16 "
        f'borderwidth=0 colorlist="{colors}" valuelist="{values}" showlabels=false'
    )


def prepare_cytoscape_tables(
    nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, float, str]:
    cy_nodes = nodes.copy()
    cy_edges = edges.copy()
    cy_nodes["query_hit_bool"] = truth_series(cy_nodes["is_query_hit_meeting_display_threshold"])
    cy_edges["direct_edge_bool"] = truth_series(cy_edges["is_directly_incident_to_lamtor5"])

    def display_label(row: pd.Series) -> str:
        upstream = pd.to_numeric(pd.Series([row["upstream_depth_to_lamtor5"]]), errors="coerce").iloc[0]
        if pd.notna(upstream):
            return f"{row['gene']}\nU{int(upstream)}"
        return f"{row['gene']}\n{int(row['supporting_neighborhood_occurrence_count'])}/{SUPPORTING_RUNS}"

    cy_nodes["display_label"] = cy_nodes.apply(display_label, axis=1)
    cy_nodes["display_font_size"] = cy_nodes["gene"].str.len().map(lambda length: 20 if length >= 9 else 21 if length >= 7 else 22)
    cy_nodes["display_size"] = cy_nodes.apply(
        lambda row: node_display_size(row["gene"], int(row["supporting_neighborhood_occurrence_count"])), axis=1
    )
    cy_nodes["query_hit_class"] = cy_nodes["query_hit_bool"].map({True: "query_hit", False: "not_query_hit"})
    positions, minimum_clearance, closest_pair = radial_positions(nodes)
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
    cy_edges["direct_edge_class"] = cy_edges["direct_edge_bool"].map({True: "direct_lamtor5", False: "other_displayed"})
    return cy_nodes, cy_edges, minimum_clearance, closest_pair


def add_annotations(network_suid: int) -> None:
    def add_text(label: str, x: float, y: float, name: str, size: int = 16, style: str = "plain", color: str = "#222222") -> None:
        p4c.add_annotation_text(
            text=label, x_pos=x, y_pos=y, font_size=size, font_family="SansSerif", font_style=style,
            color=color, name=name, canvas="foreground", z_order=20, network=network_suid,
        )

    def add_symbol(x: float, y: float, name: str, fill: str, border: str = "#555555", border_width: int = 2, size: int = 28) -> None:
        p4c.add_annotation_shape(
            type="ELLIPSE", x_pos=x, y_pos=y, fill_color=fill, opacity=100, border_thickness=border_width,
            border_color=border, border_opacity=100, height=size, width=size, name=name,
            canvas="foreground", z_order=10, network=network_suid,
        )

    title_x, title_y = -1350.0, -1530.0
    add_text("LAMTOR5-centered inhibitory-neuron consensus network", title_x, title_y, "figure_title", 29, "bold", "#111111")
    add_text(
        "U1-U2 nodes are upstream context; D1-D3 nodes lie downstream; arrows follow the Bayesian-network direction",
        title_x, title_y + 55, "figure_subtitle", 16, color="#555555",
    )
    legend_x, legend_top = 1420.0, -1080.0
    text_x = legend_x + 46.0
    add_text("HOW TO READ", legend_x, legend_top, "legend_title", 20, "bold", "#111111")
    add_text("Node size and x/5 show neighborhood recurrence", legend_x, legend_top + 52, "legend_recurrence_1")
    add_text("across the 5 supporting runs", legend_x, legend_top + 86, "legend_recurrence_2")
    add_text("U1/U2: upstream distance to LAMTOR5", legend_x, legend_top + 126, "legend_upstream")
    add_text("Thick black border: mitochondrial query hit at >=1/5", legend_x, legend_top + 166, "legend_query_hit")

    deg_heading_y = legend_top + 218
    add_text("NODE FILL  ·  PHASE 8 DIRECT DEG", legend_x, deg_heading_y, "legend_deg_heading", 17, "bold", "#111111")
    for index, (deg_class, label) in enumerate(DEG_LABELS):
        y = deg_heading_y + 45 + index * 48
        add_symbol(legend_x, y, f"legend_deg_symbol_{index}", DEG_COLORS[deg_class])
        add_text(label, text_x, y + 8, f"legend_deg_text_{index}", color="#333333")

    pathway_heading_y = deg_heading_y + 275
    add_text("PATHWAY OUTLINE", legend_x, pathway_heading_y, "legend_pathway_heading", 17, "bold", "#111111")
    add_text("OXPHOS, complex I, and protein degradation pass BH FDR < 0.05; translation and mTORC1 are contextual", legend_x, pathway_heading_y + 39, "legend_pathway_note", 15, color="#555555")
    for index, theme in enumerate(PATHWAY_THEMES):
        y = pathway_heading_y + 84 + index * 48
        add_symbol(legend_x, y, f"legend_pathway_symbol_{theme['code']}", "#FFFFFF", theme["color"], 6, 30)
        add_text(theme["label"], text_x, y + 6, f"legend_pathway_text_{theme['code']}", color="#333333")

    radial_heading_y = pathway_heading_y + 84 + len(PATHWAY_THEMES) * 48 + 45
    add_text("RADIAL DISTANCE", legend_x, radial_heading_y, "legend_radial_heading", 17, "bold", "#111111")
    add_text("U1-U2: upstream context; D1-D3: minimum downstream steps", legend_x, radial_heading_y + 43, "legend_radial_text")
    scope_heading_y = radial_heading_y + 110
    add_text("DISPLAY SCOPE", legend_x, scope_heading_y, "legend_scope_heading", 17, "bold", "#111111")
    add_text("28 nodes / 28 edges", legend_x, scope_heading_y + 43, "legend_scope_counts")
    add_text("All LAMTOR5 edges: 1 incoming, 9 outgoing", legend_x, scope_heading_y + 80, "legend_scope_direct")
    add_text("D3 paths to all 14 observed query hits", legend_x, scope_heading_y + 117, "legend_scope_hits")
    add_text("All model edges among displayed nodes are retained", legend_x, scope_heading_y + 154, "legend_scope_edges")
    add_text("Display threshold >=1/5 is a coverage choice, not a significance cutoff", legend_x, scope_heading_y + 202, "legend_scope_threshold", 15, color="#555555")


def render_cytoscape(nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame, output_dir: Path) -> None:
    cy_nodes, cy_edges, minimum_clearance, closest_pair = prepare_cytoscape_tables(nodes, edges, membership)
    version = p4c.cytoscape_version_info()
    require(version.get("cytoscapeVersion") == "3.10.4", f"Expected Cytoscape 3.10.4, found {version}")
    p4c.close_session(False)
    network_suid = p4c.create_network_from_data_frames(
        nodes=cy_nodes,
        edges=cy_edges,
        title="Phase 18 LAMTOR5 radial inhibitory-neuron consensus network",
        collection="Phase 18 LAMTOR5 deep dive",
        node_id_list="gene",
        source_id_list="source",
        target_id_list="target",
        interaction_type_list="interaction",
    )
    common.create_style()
    p4c.set_visual_style(STYLE_NAME, network=network_suid)
    p4c.set_node_position_bypass(cy_nodes["gene"].tolist(), cy_nodes["cy_x"].tolist(), cy_nodes["cy_y"].tolist(), network=network_suid)
    p4c.set_node_color_bypass([DRIVER], "#111111", network=network_suid)
    p4c.set_node_label_color_bypass([DRIVER], "#FFFFFF", network=network_suid)
    p4c.set_node_border_color_bypass([DRIVER], "#111111", network=network_suid)
    p4c.set_node_border_width_bypass([DRIVER], 5.0, network=network_suid)
    p4c.set_node_font_size_bypass([DRIVER], 27, network=network_suid)
    p4c.set_node_property_bypass([DRIVER], [180.0], "NODE_SIZE", network=network_suid)
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
        "direct_outgoing_edges": 9,
        "supporting_run_count": SUPPORTING_RUNS,
        "query_hit_threshold": QUERY_HIT_THRESHOLD,
        "query_hit_count": len(EXPECTED_QUERY_HITS),
        "threshold_rationale": "1/5 retains all 14 observed hits in a readable 28-node graph; 2/5 loses 5 hits and 7 nodes",
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
        p4c.export_image(filename=str(path), type=image_type, overwrite_file=True, all_graphics_details=True, export_text_as_font=True, network=network_suid)
        require(path.exists() and path.stat().st_size > 0, f"Cytoscape did not create {path}")
        export_log["exports"][image_type.lower()] = {"file": path.name, "bytes": path.stat().st_size}
    png_path = output_dir / f"{FIGURE_STEM}.png"
    p4c.export_image(filename=str(png_path), type="PNG", zoom=300, overwrite_file=True, all_graphics_details=True, transparent_background=False, network=network_suid)
    require(png_path.exists() and png_path.stat().st_size > 0, "Cytoscape did not create the PNG")
    export_log["exports"]["png"] = {"file": png_path.name, "bytes": png_path.stat().st_size, "zoom_percent": 300}
    (output_dir / f"{FIGURE_STEM}_cytoscape_export.json").write_text(json.dumps(export_log, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(export_log, indent=2))


def write_graphml(path: Path, nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame) -> None:
    graph = nx.DiGraph(network=NETWORK_NAME, driver=DRIVER, query_hit_display_threshold="1/5")
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


def write_documentation(output_dir: Path, pathway_ora: pd.DataFrame) -> None:
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_nonredundant_representative"])].set_index("pathway")
    summaries = []
    for theme in PATHWAY_THEMES:
        row = selected.loc[theme["pathway"]]
        status = "FDR-significant" if float(row["bh_fdr"]) < 0.05 else "contextual"
        summaries.append(f"{theme['label']} ({int(row['overlap_gene_count'])} genes; BH FDR = {float(row['bh_fdr']):.3g}; {status})")
    caption = f"""# LAMTOR5 inhibitory-neuron consensus network with pathway outlines

LAMTOR5-centered inhibitory-neuron Bayesian-network neighborhood reconstructed from five conservative-support runs. The 1/5 display threshold retains all 14 observed mitochondrial query hits in a 28-node, 28-edge graph. Raising the threshold to 2/5 would retain nine hits and 21 nodes. The display retains the two-node upstream context, all one incoming and nine outgoing LAMTOR5 edges, D3 paths to retained hits, and every model edge among displayed nodes.

Node size and `x/5` show supporting-neighborhood occurrence; U1/U2 show upstream graph distance. Thick black borders mark query hits meeting 1/5. Fill shows stored Phase 8 direct-DEG direction. Pathway outlines show {', '.join(summaries)}. Translation and mTORC1-mediated signaling are contextual annotations; pathway membership and enrichment do not establish pathway activation or a causal effect of LAMTOR5.
"""
    methods = f"""# Methods: LAMTOR5 inhibitory-neuron consensus network

Five conservative-support LAMTOR5 rows were read from `call_key_driver_returns.tsv`. For each run, the inhibitory-neuron Bayesian network was restricted to its recorded effective background and reconstructed through the stored final D3 layer. Effective query genes came from `kda_signature_members.tsv`. All reconstructed query-overlap counts matched the stored final overlap counts.

Query-hit recurrence was counted separately from neighborhood occurrence. Threshold profiling showed that 1/5 retains all 14 observed hits and yields 28 nodes/28 edges, whereas 2/5 retains nine hits and yields 21 nodes/20 edges. The 1/5 cutoff therefore preserves five single-run hits while remaining readable and comparable to other Phase 18 network figures. The threshold is a coverage choice, not a statistical test.

Pathway ORA used 27 displayed genes represented in MSigDB C2:CP v2026.1. The explicit universe was 6,537 inhibitory-neuron Bayesian-network genes represented in that collection. One-sided hypergeometric tests were run for 1,706 pathways with 15-500 mapped background genes and corrected by Benjamini-Hochberg. Five nonredundant representatives are displayed: {', '.join(summaries)}. Translation and mTORC1-mediated signaling are contextual annotations and are not statistically significant after correction.

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
    png = output_dir / f"{FIGURE_STEM}.png"
    pdf = output_dir / f"{FIGURE_STEM}.pdf"
    svg = output_dir / f"{FIGURE_STEM}.svg"
    cys = output_dir / f"{FIGURE_STEM}_cytoscape.cys"
    style = output_dir / f"{FIGURE_STEM}_cytoscape_style.xml"
    with Image.open(png) as image:
        width, height = image.size
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_nonredundant_representative"])]
    threshold_two = sensitivity.loc[sensitivity["threshold_count"].eq(2)].iloc[0]
    selected_significant = int((pd.to_numeric(selected["bh_fdr"]) < 0.05).sum())
    all_significant = int((pd.to_numeric(pathway_ora["bh_fdr"]) < 0.05).sum())
    checks = [
        ("supporting_run_count", SUPPORTING_RUNS == 5, str(SUPPORTING_RUNS)),
        ("selected_threshold", QUERY_HIT_THRESHOLD == 1, "1/5"),
        ("threshold_2_hit_count", int(threshold_two["retained_query_hit_count"]) == 9, str(threshold_two["retained_query_hit_count"])),
        ("node_count", len(nodes) == 28, str(len(nodes))),
        ("edge_count", len(edges) == 28, str(len(edges))),
        ("query_hit_count", int(truth_series(nodes["is_query_hit_meeting_display_threshold"]).sum()) == 14, "14"),
        ("all_direct_incoming", int(truth_series(nodes["is_direct_incoming_neighbor"]).sum()) == 1, "1"),
        ("all_direct_outgoing", int(truth_series(nodes["is_direct_outgoing_neighbor"]).sum()) == 9, "9"),
        ("pathway_representative_count", len(selected) == 5, str(len(selected))),
        ("pathway_membership_rows", len(membership) == 28, str(len(membership))),
        ("selected_fdr_significant_pathways", selected_significant == 3, str(selected_significant)),
        ("all_fdr_significant_pathways", all_significant == 18, str(all_significant)),
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


def run(output_dir: Path) -> None:
    configure_common()
    output_dir.mkdir(parents=True, exist_ok=True)
    support_rows = load_support_rows()
    graph = load_graph()
    backgrounds, signatures = common.load_run_sets(set(support_rows["kda_run_id"].astype(str)))
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
        common.write_tsv(output_dir / filename, frame)
    write_graphml(output_dir / "phase18_lamtor5_inhibitory.graphml", nodes, edges, pathway_membership)
    render_cytoscape(nodes, edges, pathway_membership, output_dir)
    write_documentation(output_dir, pathway_ora)
    checks = validate_outputs(output_dir, nodes, edges, sensitivity, pathway_ora, pathway_membership)
    common.write_tsv(output_dir / f"{FIGURE_STEM}_checks.tsv", checks)
    common.write_manifest(output_dir)
    print(f"Wrote {output_dir / (FIGURE_STEM + '.png')}")
    print("Display: 28 nodes, 28 edges, 14 query hits at >=1/5")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir.resolve())


if __name__ == "__main__":
    main()
