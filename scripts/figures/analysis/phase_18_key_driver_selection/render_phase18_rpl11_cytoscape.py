#!/usr/bin/env python3
"""Render the Phase 18 RPL11 consensus network with Cytoscape.

This script intentionally treats Cytoscape as the rendering engine.  It reads the
validated consensus node, edge, and pathway-membership tables produced by the
RPL11 deep-dive analysis, creates a Cytoscape network and visual style, fixes the
published node positions, and asks Cytoscape to export PNG, PDF, and SVG files.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import networkx as nx
import pandas as pd
import py4cytoscape as p4c


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RPL11_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "RPL11"
)
OUTPUT_STEM = "phase18_rpl11_excitatory_consensus_network_pathways"
NETWORK_TITLE = "Phase 18 RPL11 radial excitatory consensus network"
COLLECTION_TITLE = "Phase 18 RPL11 deep dive"
STYLE_NAME = "Phase18 RPL11 radial consensus pathway outlines"
DISPLAY_NETWORK = "Excitatory_neurons"
FIGURE_TITLE = "RPL11-centered excitatory-neuron consensus network"
FIGURE_SUBTITLE = (
    "Radial position groups nodes by minimum downstream distance; "
    "arrows follow the Bayesian-network direction"
)
TITLE_X = -950.0
TITLE_Y = -1000.0
LEGEND_X = 970.0
LEGEND_TOP_Y = -770.0

DEG_COLORS = {
    "up_only": "#D55E00",
    "down_only": "#56B4E9",
    "mixed": "#F0E442",
    "not_deg": "#D9D9D9",
}
PATHWAY_THEMES = {
    "R": ("Cytosolic ribosome", "#6F4E9C", "#FFFFFF"),
    "O": ("ETC / oxidative phosphorylation", "#0072B2", "#FFFFFF"),
    "D": ("Mitochondrial protein degradation", "#D55E00", "#FFFFFF"),
    "C": ("Cristae formation", "#009E73", "#FFFFFF"),
}
EXPECTED_NODE_COUNT = 35
EXPECTED_EDGE_COUNT = 34
EXPECTED_DIRECT_INCOMING = 0
EXPECTED_DIRECT_OUTGOING = 9
EXPECTED_SUPPORTING_RUNS = 20
EXPECTED_RECURRENT_THRESHOLD = 4
RADII = {1: 270.0, 2: 460.0, 3: 650.0}
UPSTREAM_RADII: dict[int, float] = {}
RECURRENCE_SIZE_STEP = 1.50
PATHWAY_OUTLINE_PADDING = 32.0
COLLISION_PADDING = 18.0
BRANCH_ORDER = (
    "RPS13",
    "RPL5",
    "COX7C",
    "SRP14",
    "RPS27A",
    "RPS23",
    "RPL30",
    "SMDT1",
    "RPL6",
)


def configure_network(network: str) -> None:
    """Select one validated RPL11 network while retaining a shared visual grammar."""

    global OUTPUT_STEM, NETWORK_TITLE, STYLE_NAME, DISPLAY_NETWORK
    global FIGURE_TITLE, FIGURE_SUBTITLE, TITLE_X, TITLE_Y, LEGEND_X, LEGEND_TOP_Y
    global PATHWAY_THEMES, EXPECTED_NODE_COUNT, EXPECTED_EDGE_COUNT
    global EXPECTED_DIRECT_INCOMING, EXPECTED_DIRECT_OUTGOING
    global EXPECTED_SUPPORTING_RUNS, EXPECTED_RECURRENT_THRESHOLD
    global RADII, UPSTREAM_RADII, RECURRENCE_SIZE_STEP, BRANCH_ORDER

    if network == "excitatory":
        return
    if network != "astrocytes":
        raise ValueError(f"Unsupported RPL11 network: {network}")

    OUTPUT_STEM = "phase18_rpl11_astrocyte_consensus_network_pathways"
    NETWORK_TITLE = "Phase 18 RPL11 radial astrocyte consensus network"
    STYLE_NAME = "Phase18 RPL11 astrocyte radial consensus pathway outlines"
    DISPLAY_NETWORK = "Astrocytes"
    FIGURE_TITLE = "RPL11-centered astrocyte consensus network"
    FIGURE_SUBTITLE = (
        "U1-U2 nodes are upstream context; D1-D3 nodes lie downstream; "
        "arrows follow the Bayesian-network direction"
    )
    TITLE_X = -650.0
    TITLE_Y = -920.0
    LEGEND_X = 650.0
    LEGEND_TOP_Y = -600.0
    PATHWAY_THEMES = {
        "R": ("Cytosolic ribosome", "#6F4E9C", "#FFFFFF"),
        "O": ("ETC / oxidative phosphorylation", "#0072B2", "#FFFFFF"),
        "C": ("Cristae formation", "#009E73", "#FFFFFF"),
    }
    EXPECTED_NODE_COUNT = 18
    EXPECTED_EDGE_COUNT = 17
    EXPECTED_DIRECT_INCOMING = 1
    EXPECTED_DIRECT_OUTGOING = 3
    EXPECTED_SUPPORTING_RUNS = 3
    EXPECTED_RECURRENT_THRESHOLD = 1
    RADII = {1: 260.0, 2: 470.0, 3: 680.0}
    UPSTREAM_RADII = {1: 230.0, 2: 420.0}
    RECURRENCE_SIZE_STEP = 10.0
    BRANCH_ORDER = ("CWC15", "COX7C", "PRDX1")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin({"TRUE", "T", "1", "YES"})


def node_display_size(gene: str, occurrence_count: int) -> float:
    """Return a diameter large enough for both recurrence and the two-line label."""

    if gene == "RPL11":
        return 156.0
    recurrence_size = 96.0 + RECURRENCE_SIZE_STEP * occurrence_count
    label_size = 92.0 + 10.0 * max(0, len(gene) - 4)
    return round(max(recurrence_size, label_size), 1)


def radial_tree_positions(nodes: pd.DataFrame, edges: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Lay out the validated directed tree around RPL11 with checked clearance."""

    graph = nx.from_pandas_edgelist(
        edges,
        source="source",
        target="target",
        create_using=nx.DiGraph,
    )
    graph.add_nodes_from(nodes["gene"])
    require(nx.is_directed_acyclic_graph(graph), "The displayed consensus graph is not acyclic")
    require(nx.is_tree(graph.to_undirected()), "The displayed consensus graph is no longer a tree")

    if DISPLAY_NETWORK == "Astrocytes":
        require(set(graph.predecessors("RPL11")) == {"RPLP1"}, "The astrocyte direct parent changed")
        require(set(graph.successors("RPL11")) == set(BRANCH_ORDER), "The astrocyte direct children changed")
        require(set(nx.ancestors(graph, "RPL11")) == {"RPLP1", "RPS25"}, "The astrocyte upstream chain changed")
        require(
            set(nx.descendants(graph, "RPL11")) == set(nodes["gene"]) - {"RPL11", "RPLP1", "RPS25"},
            "The astrocyte downstream display changed",
        )
        # Place upstream context to the left and downstream branches across the
        # right semicircle. The fixed angles preserve parent-child grouping and
        # keep the compact arrows legible without drawing guide rings.
        angle_degrees = {
            "CWC15": -85.0,
            "COX7C": -10.0,
            "PRDX1": 75.0,
            "ATP5F1E": -80.0,
            "ATP5PF": -55.0,
            "DYNLL1": -30.0,
            "NDUFB4": -5.0,
            "TOMM7": 20.0,
            "UQCRB": 45.0,
            "PSAP": 90.0,
            "ATP5ME": -95.0,
            "COX6C": -70.0,
            "UQCRH": -30.0,
            "SLIRP": 45.0,
            "CYB5R3": 90.0,
        }
        positions = {
            "RPL11": (0.0, 0.0),
            "RPLP1": (-UPSTREAM_RADII[1], 0.0),
            "RPS25": (-UPSTREAM_RADII[2], 0.0),
        }
        downstream_depth = dict(zip(nodes["gene"], nodes["directed_depth_from_rpl11"]))
        for gene, angle_degrees_value in angle_degrees.items():
            depth = int(downstream_depth[gene])
            angle = math.radians(angle_degrees_value)
            positions[gene] = (RADII[depth] * math.cos(angle), RADII[depth] * math.sin(angle))
    else:
        require(nx.is_arborescence(graph), "The displayed consensus graph is no longer a rooted directed tree")
        require(graph.in_degree("RPL11") == 0, "RPL11 must remain the radial root")
        require(set(nx.descendants(graph, "RPL11")) == set(nodes["gene"]) - {"RPL11"}, "Not every node is downstream of RPL11")
        require(set(graph.successors("RPL11")) == set(BRANCH_ORDER), "The fixed radial branch order no longer matches D1")

        depth_by_gene = dict(zip(nodes["gene"], nodes["directed_depth_from_rpl11"]))
        for gene in graph:
            require(nx.shortest_path_length(graph, "RPL11", gene) == int(depth_by_gene[gene]), f"Depth mismatch for {gene}")

        # Evenly space every depth around its own circle. The order remains a
        # deterministic branch-preserving preorder, while each deeper circle
        # is rotated toward its parent nodes.
        def ordered_subtree(gene: str) -> list[str]:
            children = sorted(graph.successors(gene))
            return [gene] + [descendant for child in children for descendant in ordered_subtree(child)]

        ordered_genes = [gene for branch in BRANCH_ORDER for gene in ordered_subtree(branch)]
        require(len(ordered_genes) == len(set(ordered_genes)), "The radial preorder contains duplicates")
        require(set(ordered_genes) == set(nodes["gene"]) - {"RPL11"}, "The radial preorder is incomplete")

        positions = {"RPL11": (0.0, 0.0)}
        angle_by_gene: dict[str, float] = {"RPL11": 0.0}
        for depth in sorted(RADII):
            depth_genes = [gene for gene in ordered_genes if int(depth_by_gene[gene]) == depth]
            require(depth_genes, f"No nodes found at radial depth {depth}")
            step = 2.0 * math.pi / len(depth_genes)
            base_angles = [index * step for index in range(len(depth_genes))]
            if depth == 1:
                phase = math.radians(-70.0)
            else:
                parent_angles = [angle_by_gene[next(graph.predecessors(gene))] for gene in depth_genes]
                offsets = [parent_angle - base_angle for parent_angle, base_angle in zip(parent_angles, base_angles)]
                phase = math.atan2(sum(math.sin(value) for value in offsets), sum(math.cos(value) for value in offsets))
            for gene, base_angle in zip(depth_genes, base_angles):
                angle = phase + base_angle
                angle_by_gene[gene] = angle
                radius = RADII[depth]
                positions[gene] = (radius * math.cos(angle), radius * math.sin(angle))

    require(set(positions) == set(nodes["gene"]), "Radial layout did not assign every displayed node")

    # Fail loudly if a future input change would reintroduce overlapping nodes.
    size_by_gene = {
        row.gene: node_display_size(row.gene, int(row.supporting_neighborhood_occurrence_count))
        + PATHWAY_OUTLINE_PADDING
        for row in nodes.itertuples()
    }
    genes = nodes["gene"].tolist()
    for index, gene_a in enumerate(genes):
        for gene_b in genes[index + 1 :]:
            x_a, y_a = positions[gene_a]
            x_b, y_b = positions[gene_b]
            distance = math.hypot(x_a - x_b, y_a - y_b)
            required = (size_by_gene[gene_a] + size_by_gene[gene_b]) / 2.0 + COLLISION_PADDING
            require(distance >= required, f"Radial layout collision: {gene_a} and {gene_b}")
    return positions


def pathway_outline(codes: list[str]) -> str:
    """Return a segmented, node-centered outer ring for pathway memberships."""

    if not codes:
        return ""
    colors = ",".join(PATHWAY_THEMES[code][1] for code in codes)
    values = ",".join("1" for _ in codes)
    return (
        'circoschart: arcstart=270 firstarc=.78 firstarcwidth=.16 arcwidth=.16 '
        f'borderwidth=0 colorlist="{colors}" valuelist="{values}" showlabels=false'
    )


def load_inputs(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    node_path = input_dir / f"{OUTPUT_STEM.removesuffix('_pathways')}_nodes.tsv"
    edge_path = input_dir / f"{OUTPUT_STEM.removesuffix('_pathways')}_edges.tsv"
    analysis_prefix = OUTPUT_STEM.removesuffix("_network_pathways")
    membership_path = input_dir / f"{analysis_prefix}_pathway_membership.tsv"
    for path in (node_path, edge_path, membership_path):
        require(path.exists(), f"Required Cytoscape input is missing: {path}")

    nodes = pd.read_csv(node_path, sep="\t", keep_default_na=False)
    edges = pd.read_csv(edge_path, sep="\t", keep_default_na=False)
    membership = pd.read_csv(membership_path, sep="\t", keep_default_na=False)

    require(len(nodes) == EXPECTED_NODE_COUNT, f"Expected {EXPECTED_NODE_COUNT} nodes, found {len(nodes)}")
    require(len(edges) == EXPECTED_EDGE_COUNT, f"Expected {EXPECTED_EDGE_COUNT} edges, found {len(edges)}")
    require(nodes["gene"].is_unique, "Consensus node table contains duplicate genes")
    require(set(edges["source"]).union(edges["target"]) <= set(nodes["gene"]), "An edge endpoint is absent from the node table")
    require(set(membership["gene"]) <= set(nodes["gene"]), "A pathway member is absent from the displayed node table")

    nodes["is_recurrent_query_hit_bool"] = as_bool(nodes["is_recurrent_query_hit"])
    nodes["is_cytosolic_ribosomal_bool"] = as_bool(nodes["is_cytosolic_ribosomal"])
    edges["is_directly_incident_bool"] = as_bool(edges["is_directly_incident_to_rpl11"])
    nodes["supporting_neighborhood_occurrence_count"] = pd.to_numeric(
        nodes["supporting_neighborhood_occurrence_count"], errors="raise"
    ).astype(int)
    nodes["directed_depth_from_rpl11"] = pd.to_numeric(nodes["directed_depth_from_rpl11"], errors="coerce")
    nodes["upstream_depth_to_rpl11"] = pd.to_numeric(nodes["upstream_depth_to_rpl11"], errors="coerce")
    if {"x", "y"} <= set(nodes.columns):
        nodes["x"] = pd.to_numeric(nodes["x"], errors="raise")
        nodes["y"] = pd.to_numeric(nodes["y"], errors="raise")

    require((nodes["supporting_neighborhood_occurrence_count"] <= EXPECTED_SUPPORTING_RUNS).all(), "A node occurrence exceeds the supporting-run count")
    require((nodes["query_hit_display_threshold"].astype(int) == EXPECTED_RECURRENT_THRESHOLD).all(), "Unexpected recurrence threshold")
    require(nodes.loc[nodes["gene"].eq("RPL11"), "is_direct_incoming_neighbor"].astype(str).str.upper().eq("FALSE").all(), "RPL11 cannot be its own incoming neighbor")
    direct_out = int(nodes["is_direct_outgoing_neighbor"].astype(str).str.upper().eq("TRUE").sum())
    direct_in = int(nodes["is_direct_incoming_neighbor"].astype(str).str.upper().eq("TRUE").sum())
    require(direct_in == EXPECTED_DIRECT_INCOMING, f"Expected 0 direct incoming neighbors, found {direct_in}")
    require(direct_out == EXPECTED_DIRECT_OUTGOING, f"Expected 9 direct outgoing neighbors, found {direct_out}")

    return nodes, edges, membership


def prepare_cytoscape_tables(
    nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cy_nodes = nodes.copy()
    cy_edges = edges.copy()

    def display_label(row: pd.Series) -> str:
        if pd.notna(row["upstream_depth_to_rpl11"]):
            return f"{row['gene']}\nU{int(row['upstream_depth_to_rpl11'])}"
        return f"{row['gene']}\n{int(row['supporting_neighborhood_occurrence_count'])}/{EXPECTED_SUPPORTING_RUNS}"

    cy_nodes["display_label"] = cy_nodes.apply(display_label, axis=1)
    cy_nodes["display_font_size"] = cy_nodes["gene"].str.len().map(lambda length: 19 if length >= 7 else 20)
    cy_nodes["display_size"] = cy_nodes.apply(
        lambda row: node_display_size(row["gene"], int(row["supporting_neighborhood_occurrence_count"])), axis=1
    )
    cy_nodes["recurrent_class"] = cy_nodes["is_recurrent_query_hit_bool"].map({True: "recurrent", False: "not_recurrent"})
    cy_nodes["driver_class"] = cy_nodes["gene"].eq("RPL11").map({True: "driver", False: "not_driver"})
    positions = radial_tree_positions(nodes, edges)
    cy_nodes["cy_x"] = cy_nodes["gene"].map(lambda gene: positions[gene][0])
    cy_nodes["cy_y"] = cy_nodes["gene"].map(lambda gene: positions[gene][1])

    codes_by_gene = {
        gene: [code for code in PATHWAY_THEMES if code in set(group["pathway_code"])]
        for gene, group in membership.groupby("gene")
    }
    cy_nodes["pathway_codes"] = cy_nodes["gene"].map(lambda gene: ";".join(codes_by_gene.get(gene, [])))
    cy_nodes["pathway_outline"] = cy_nodes["gene"].map(lambda gene: pathway_outline(codes_by_gene.get(gene, [])))
    cy_nodes["pathway_outline_size"] = cy_nodes["display_size"] + PATHWAY_OUTLINE_PADDING

    cy_edges["interaction"] = "directed"
    cy_edges["direct_edge_class"] = cy_edges["is_directly_incident_bool"].map(
        {True: "direct_rpl11", False: "other_displayed"}
    )
    return cy_nodes, cy_edges


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
        "NODE_LABEL_MAX_WIDTH": 110,
        "NODE_SHAPE": "ELLIPSE",
        "NODE_SIZE": 64,
        "NODE_TRANSPARENCY": 255,
        "EDGE_CURVED": False,
        "EDGE_LINE_TYPE": "SOLID",
        "EDGE_UNSELECTED_PAINT": "#A8A8A8",
        "EDGE_STROKE_UNSELECTED_PAINT": "#A8A8A8",
        "EDGE_TARGET_ARROW_SHAPE": "DELTA",
        "EDGE_TARGET_ARROW_UNSELECTED_PAINT": "#777777",
        "EDGE_WIDTH": 1.2,
        "EDGE_TRANSPARENCY": 215,
    }
    mappings = [
        mapping("NODE_LABEL", "display_label", "p"),
        mapping("NODE_SIZE", "display_size", "p"),
        mapping("NODE_LABEL_FONT_SIZE", "display_font_size", "p"),
        mapping(
            "NODE_FILL_COLOR",
            "phase08_deg_class",
            "d",
            list(DEG_COLORS),
            list(DEG_COLORS.values()),
        ),
        mapping(
            "NODE_BORDER_WIDTH",
            "recurrent_class",
            "d",
            ["not_recurrent", "recurrent"],
            [1.8, 4.5],
        ),
        mapping(
            "NODE_BORDER_PAINT",
            "recurrent_class",
            "d",
            ["not_recurrent", "recurrent"],
            ["#555555", "#111111"],
        ),
        mapping(
            "EDGE_WIDTH",
            "direct_edge_class",
            "d",
            ["other_displayed", "direct_rpl11"],
            [1.2, 2.8],
        ),
        mapping(
            "EDGE_UNSELECTED_PAINT",
            "direct_edge_class",
            "d",
            ["other_displayed", "direct_rpl11"],
            ["#A8A8A8", "#4D4D4D"],
        ),
        mapping(
            "EDGE_STROKE_UNSELECTED_PAINT",
            "direct_edge_class",
            "d",
            ["other_displayed", "direct_rpl11"],
            ["#A8A8A8", "#4D4D4D"],
        ),
    ]
    mappings.extend(
        [
            mapping("NODE_CUSTOMGRAPHICS_1", "pathway_outline", "p"),
            mapping("NODE_CUSTOMGRAPHICS_SIZE_1", "pathway_outline_size", "p"),
        ]
    )

    p4c.create_visual_style(STYLE_NAME, defaults=defaults, mappings=mappings)
    p4c.lock_node_dimensions(True, style_name=STYLE_NAME)
    p4c.set_node_custom_position(
        node_anchor="C",
        graphic_anchor="C",
        justification="c",
        x_offset=0.0,
        y_offset=0.0,
        slot=1,
        style_name=STYLE_NAME,
    )


def add_annotations(network_suid: int) -> None:
    # These are Cytoscape annotations, not post-export additions.
    def add_text(
        label: str,
        x_pos: float,
        y_pos: float,
        name: str,
        size: int = 16,
        style: str = "plain",
        color: str = "#222222",
    ) -> None:
        p4c.add_annotation_text(
            text=label,
            x_pos=x_pos,
            y_pos=y_pos,
            font_size=size,
            font_family="SansSerif",
            font_style=style,
            color=color,
            name=name,
            canvas="foreground",
            z_order=20,
            network=network_suid,
        )

    def add_symbol(
        x_pos: float,
        y_pos: float,
        name: str,
        fill: str,
        shape: str = "ELLIPSE",
        border: str = "#555555",
        border_width: int = 2,
        size: int = 28,
    ) -> None:
        p4c.add_annotation_shape(
            type=shape,
            x_pos=x_pos,
            y_pos=y_pos,
            fill_color=fill,
            opacity=100,
            border_thickness=border_width,
            border_color=border,
            border_opacity=100,
            height=size,
            width=size,
            name=name,
            canvas="foreground",
            z_order=10,
            network=network_suid,
        )

    add_text(
        FIGURE_TITLE,
        TITLE_X,
        TITLE_Y,
        "figure_title",
        size=29,
        style="bold",
        color="#111111",
    )
    add_text(
        FIGURE_SUBTITLE,
        TITLE_X,
        TITLE_Y + 55,
        "figure_subtitle",
        size=16,
        color="#555555",
    )

    legend_x = LEGEND_X
    legend_top = LEGEND_TOP_Y
    text_x = legend_x + 46
    add_text("HOW TO READ", legend_x, legend_top, "legend_title", size=20, style="bold", color="#111111")
    add_text(
        f"Node size and x/{EXPECTED_SUPPORTING_RUNS} show neighborhood recurrence",
        legend_x,
        legend_top + 52,
        "legend_recurrence_1",
    )
    add_text(
        f"across the {EXPECTED_SUPPORTING_RUNS} supporting runs",
        legend_x,
        legend_top + 86,
        "legend_recurrence_2",
    )

    add_text("Thick black border: recurrent mitochondrial query hit", legend_x, legend_top + 130, "legend_recurrent_text")

    deg_heading_y = legend_top + 180
    add_text("NODE FILL  ·  PHASE 8 DIRECT DEG", legend_x, deg_heading_y, "legend_deg_heading", size=17, style="bold", color="#111111")
    deg_items = (
        ("mixed", "Both AD-up and AD-down"),
        ("down_only", "AD-down only"),
        ("up_only", "AD-up only"),
        ("not_deg", "No stored direct DEG"),
    )
    for index, (deg_class, label) in enumerate(deg_items):
        y_pos = deg_heading_y + 45 + index * 48
        add_symbol(legend_x, y_pos, f"legend_deg_symbol_{index}", DEG_COLORS[deg_class])
        add_text(label, text_x, y_pos + 8, f"legend_deg_text_{index}", color="#333333")

    pathway_heading_y = deg_heading_y + 275
    add_text("PATHWAY OUTLINE", legend_x, pathway_heading_y, "legend_pathway_heading", size=17, style="bold", color="#111111")
    add_text("Colored outer boundary; segments show multiple memberships", legend_x, pathway_heading_y + 39, "legend_pathway_note", size=15, color="#555555")
    for index, (code, (label, color, _)) in enumerate(PATHWAY_THEMES.items()):
        y_pos = pathway_heading_y + 84 + index * 48
        add_symbol(
            legend_x,
            y_pos,
            f"legend_pathway_symbol_{code}",
            "#FFFFFF",
            border=color,
            border_width=6,
            size=30,
        )
        add_text(label, text_x, y_pos + 6, f"legend_pathway_text_{code}", color="#333333")

    pathway_last_y = pathway_heading_y + 84 + (len(PATHWAY_THEMES) - 1) * 48
    radial_heading_y = pathway_last_y + 97
    add_text("RADIAL DISTANCE", legend_x, radial_heading_y, "legend_ring_heading", size=17, style="bold", color="#111111")
    downstream_levels = ", ".join(f"D{depth}" for depth in sorted(RADII))
    radial_text = f"{downstream_levels}: minimum downstream steps from RPL11"
    if UPSTREAM_RADII:
        radial_text = "U1-U2: upstream context; " + radial_text
    add_text(radial_text, legend_x, radial_heading_y + 43, "legend_ring_text")

    scope_heading_y = radial_heading_y + 115
    add_text("DISPLAY SCOPE", legend_x, scope_heading_y, "legend_scope_heading", size=17, style="bold", color="#111111")
    add_text(
        f"All direct RPL11 edges: {EXPECTED_DIRECT_INCOMING} incoming, {EXPECTED_DIRECT_OUTGOING} outgoing",
        legend_x,
        scope_heading_y + 43,
        "legend_scope_direct",
    )
    add_text(
        f"Deeper mitochondrial hits retained at {EXPECTED_RECURRENT_THRESHOLD}/{EXPECTED_SUPPORTING_RUNS} or more",
        legend_x,
        scope_heading_y + 80,
        "legend_scope_threshold",
    )
    if UPSTREAM_RADII:
        add_text(
            "Upstream U1-U2 nodes provide context and are not counted in KDA neighborhoods",
            legend_x,
            scope_heading_y + 117,
            "legend_scope_upstream",
            size=15,
            color="#555555",
        )


def render(input_dir: Path, output_dir: Path, png_zoom: int) -> None:
    nodes, edges, membership = load_inputs(input_dir)
    cy_nodes, cy_edges = prepare_cytoscape_tables(nodes, edges, membership)
    output_dir.mkdir(parents=True, exist_ok=True)

    version = p4c.cytoscape_version_info()
    require(version.get("cytoscapeVersion") == "3.10.4", f"Expected Cytoscape 3.10.4, found {version}")

    p4c.close_session(False)
    network_suid = p4c.create_network_from_data_frames(
        nodes=cy_nodes,
        edges=cy_edges,
        title=NETWORK_TITLE,
        collection=COLLECTION_TITLE,
        node_id_list="gene",
        source_id_list="source",
        target_id_list="target",
        interaction_type_list="interaction",
    )
    create_style()
    p4c.set_visual_style(STYLE_NAME, network=network_suid)
    p4c.lock_node_dimensions(True, style_name=STYLE_NAME)

    p4c.set_node_position_bypass(
        cy_nodes["gene"].tolist(),
        cy_nodes["cy_x"].tolist(),
        cy_nodes["cy_y"].tolist(),
        network=network_suid,
    )
    # RPL11 is deliberately black with white text, independent of DEG fill.
    p4c.set_node_color_bypass(["RPL11"], "#111111", network=network_suid)
    p4c.set_node_label_color_bypass(["RPL11"], "#FFFFFF", network=network_suid)
    p4c.set_node_border_color_bypass(["RPL11"], "#111111", network=network_suid)
    p4c.set_node_border_width_bypass(["RPL11"], 5.0, network=network_suid)
    p4c.set_node_font_size_bypass(["RPL11"], 25, network=network_suid)
    p4c.set_node_property_bypass(["RPL11"], [156.0], "NODE_SIZE", network=network_suid)
    add_annotations(network_suid)
    # Annotation coordinates are in the Cytoscape network coordinate system;
    # refit only after all foreground graphics exist so export bounds include
    # the title, right legend, depth headers, and lower summary box.
    p4c.fit_content(network=network_suid)

    # Save editable Cytoscape sources alongside the rendered figure.
    session_path = output_dir / f"{OUTPUT_STEM}_cytoscape.cys"
    style_path = output_dir / f"{OUTPUT_STEM}_cytoscape_style"
    p4c.save_session(str(session_path), overwrite_file=True)
    p4c.export_visual_styles(
        filename=str(style_path),
        type="XML",
        styles=STYLE_NAME,
        overwrite_file=True,
    )

    export_log: dict[str, object] = {
        "cytoscape_version": version.get("cytoscapeVersion"),
        "py4cytoscape_version": p4c.__version__,
        "network": DISPLAY_NETWORK,
        "network_suid": network_suid,
        "node_count": len(cy_nodes),
        "edge_count": len(cy_edges),
        "direct_incoming_edges": EXPECTED_DIRECT_INCOMING,
        "direct_outgoing_edges": EXPECTED_DIRECT_OUTGOING,
        "supporting_run_count": EXPECTED_SUPPORTING_RUNS,
        "recurrent_query_hit_threshold": EXPECTED_RECURRENT_THRESHOLD,
        "layout": "collision_checked_radial_tree_without_guide_rings",
        "radial_level_radii": {f"D{depth}": radius for depth, radius in RADII.items()},
        "upstream_level_radii": {f"U{depth}": radius for depth, radius in UPSTREAM_RADII.items()},
        "guide_rings_drawn": False,
        "pathway_encoding": "segmented_colored_outer_outline",
        "exports": {},
    }
    for image_type in ("SVG", "PDF"):
        path = output_dir / f"{OUTPUT_STEM}.{image_type.lower()}"
        p4c.export_image(
            filename=str(path),
            type=image_type,
            overwrite_file=True,
            all_graphics_details=True,
            export_text_as_font=True,
            network=network_suid,
        )
        require(path.exists() and path.stat().st_size > 0, f"Cytoscape did not create {path}")
        export_log["exports"][image_type.lower()] = {"file": path.name, "bytes": path.stat().st_size}

    png_path = output_dir / f"{OUTPUT_STEM}.png"
    p4c.export_image(
        filename=str(png_path),
        type="PNG",
        zoom=png_zoom,
        overwrite_file=True,
        all_graphics_details=True,
        transparent_background=False,
        network=network_suid,
    )
    require(png_path.exists() and png_path.stat().st_size > 0, f"Cytoscape did not create {png_path}")
    export_log["exports"]["png"] = {
        "file": png_path.name,
        "bytes": png_path.stat().st_size,
        "zoom_percent": png_zoom,
    }

    log_path = output_dir / f"{OUTPUT_STEM}_cytoscape_export.json"
    log_path.write_text(json.dumps(export_log, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(export_log, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", choices=("excitatory", "astrocytes"), default="excitatory")
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--png-zoom", type=int, default=300)
    args = parser.parse_args()
    configure_network(args.network)
    input_dir = args.input_dir
    if input_dir is None:
        input_dir = DEFAULT_RPL11_DIR / ("astrocyte" if args.network == "astrocytes" else "excitatory")
    render(input_dir.resolve(), args.output_dir.resolve(), args.png_zoom)


if __name__ == "__main__":
    main()
