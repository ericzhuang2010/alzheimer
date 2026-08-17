#!/usr/bin/env python3
"""Render the Phase 18 APOE astrocyte consensus network with Cytoscape.

The validated APOE node, edge, and pathway-membership tables are treated as
the source of truth. Cytoscape creates the network, visual style, annotations,
editable session, and PNG/PDF/SVG exports.
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
DEFAULT_INPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "APOE"
    / "astrocytes"
)
OUTPUT_STEM = "phase18_apoe_astrocyte_consensus_network_pathways"
ANALYSIS_PREFIX = "phase18_apoe_astrocyte_consensus"
NETWORK_TITLE = "Phase 18 APOE radial astrocyte consensus network"
COLLECTION_TITLE = "Phase 18 APOE deep dive"
STYLE_NAME = "Phase18 APOE astrocyte radial consensus pathway outlines"

SUPPORTING_RUNS = 4
QUERY_HIT_THRESHOLD = 1
EXPECTED_NODE_COUNT = 19
EXPECTED_EDGE_COUNT = 18
EXPECTED_DIRECT_INCOMING = 2
EXPECTED_DIRECT_OUTGOING = 11
EXPECTED_QUERY_HITS = 7

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
PATHWAY_THEMES = {
    "A": ("Amyloid fiber formation", "#7B3294"),
    "L": ("Cholesterol transport / efflux", "#E69F00"),
    "C": ("Cristae formation", "#009E73"),
}

# Direct APOE children occupy a broad arc, leaving a clear sector on the left
# for the two upstream branches. Each D2 hit stays radially aligned with its D1
# parent. Guide rings are intentionally omitted from the finished figure.
D1_RADIUS = 480.0
D2_RADIUS = 720.0
U1_RADIUS = 300.0
U2_RADIUS = 510.0
D1_ANGLES = {
    "TUFM": -120.0,
    "TRAPPC4": -96.0,
    "TEX264": -72.0,
    "LDHB": -48.0,
    "CHCHD10": -24.0,
    "ATP5PB": 0.0,
    "PLTP": 24.0,
    "CST3": 48.0,
    "HLA-A": 72.0,
    "DNASE2": 96.0,
    "C1orf56": 120.0,
}
D2_ANGLES = {
    "NME3": -120.0,
    "ATP5F1A": -48.0,
    "AGT": 48.0,
}
UPSTREAM_ANGLES = {
    "CKB": 160.0,
    "GPX4": 155.0,
    "LAPTM4A": 200.0,
    "ITM2B": 205.0,
}
PATHWAY_OUTLINE_PADDING = 32.0
COLLISION_PADDING = 16.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin({"TRUE", "T", "1", "YES"})


def node_display_size(gene: str, occurrence_count: int) -> float:
    """Return a circle diameter that contains the two-line label."""

    if gene == "APOE":
        return 156.0
    recurrence_size = 102.0 + 8.0 * occurrence_count
    label_size = 106.0 + 9.0 * max(0, len(gene) - 5)
    return round(max(recurrence_size, label_size), 1)


def load_inputs(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    node_path = input_dir / f"{ANALYSIS_PREFIX}_network_nodes.tsv"
    edge_path = input_dir / f"{ANALYSIS_PREFIX}_network_edges.tsv"
    membership_path = input_dir / f"{ANALYSIS_PREFIX}_pathway_membership.tsv"
    for path in (node_path, edge_path, membership_path):
        require(path.exists(), f"Required Cytoscape input is missing: {path}")

    nodes = pd.read_csv(node_path, sep="\t", keep_default_na=False)
    edges = pd.read_csv(edge_path, sep="\t", keep_default_na=False)
    membership = pd.read_csv(membership_path, sep="\t", keep_default_na=False)

    require(len(nodes) == EXPECTED_NODE_COUNT, f"Expected 19 nodes, found {len(nodes)}")
    require(len(edges) == EXPECTED_EDGE_COUNT, f"Expected 18 edges, found {len(edges)}")
    require(nodes["gene"].is_unique, "Consensus node table contains duplicate genes")
    require(set(edges["source"]).union(edges["target"]) <= set(nodes["gene"]), "An edge endpoint is absent")
    require(set(membership["gene"]) <= set(nodes["gene"]), "A pathway member is absent")

    nodes["query_hit_bool"] = as_bool(nodes["is_query_hit_meeting_display_threshold"])
    nodes["supporting_neighborhood_occurrence_count"] = pd.to_numeric(
        nodes["supporting_neighborhood_occurrence_count"], errors="raise"
    ).astype(int)
    nodes["directed_depth_from_apoe"] = pd.to_numeric(nodes["directed_depth_from_apoe"], errors="coerce")
    nodes["upstream_depth_to_apoe"] = pd.to_numeric(nodes["upstream_depth_to_apoe"], errors="coerce")
    edges["direct_edge_bool"] = as_bool(edges["is_directly_incident_to_apoe"])

    require(int(nodes["query_hit_bool"].sum()) == EXPECTED_QUERY_HITS, "Unexpected query-hit count")
    require(
        (nodes["query_hit_display_threshold_count"].astype(int) == QUERY_HIT_THRESHOLD).all(),
        "Unexpected query-hit threshold",
    )
    require(
        (nodes["supporting_neighborhood_occurrence_count"] <= SUPPORTING_RUNS).all(),
        "A node occurrence exceeds the supporting-run count",
    )
    direct_in = int(as_bool(nodes["is_direct_incoming_neighbor"]).sum())
    direct_out = int(as_bool(nodes["is_direct_outgoing_neighbor"]).sum())
    require(direct_in == EXPECTED_DIRECT_INCOMING, f"Expected 2 direct parents, found {direct_in}")
    require(direct_out == EXPECTED_DIRECT_OUTGOING, f"Expected 11 direct children, found {direct_out}")
    return nodes, edges, membership


def radial_positions(nodes: pd.DataFrame, edges: pd.DataFrame) -> dict[str, tuple[float, float]]:
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    graph.add_nodes_from(nodes["gene"])
    require(nx.is_directed_acyclic_graph(graph), "Displayed APOE graph is not acyclic")
    require(nx.is_tree(graph.to_undirected()), "Displayed APOE graph is no longer a tree")
    require(set(graph.predecessors("APOE")) == {"CKB", "LAPTM4A"}, "APOE direct parents changed")
    require(set(graph.successors("APOE")) == set(D1_ANGLES), "APOE direct children changed")
    require(set(nx.ancestors(graph, "APOE")) == {"CKB", "GPX4", "LAPTM4A", "ITM2B"}, "Upstream context changed")

    positions: dict[str, tuple[float, float]] = {"APOE": (0.0, 0.0)}
    for gene, angle_degrees in D1_ANGLES.items():
        angle = math.radians(angle_degrees)
        positions[gene] = (D1_RADIUS * math.cos(angle), D1_RADIUS * math.sin(angle))
    for gene, angle_degrees in D2_ANGLES.items():
        angle = math.radians(angle_degrees)
        positions[gene] = (D2_RADIUS * math.cos(angle), D2_RADIUS * math.sin(angle))
    for gene, angle_degrees in UPSTREAM_ANGLES.items():
        radius = U1_RADIUS if gene in {"CKB", "LAPTM4A"} else U2_RADIUS
        angle = math.radians(angle_degrees)
        positions[gene] = (radius * math.cos(angle), radius * math.sin(angle))
    require(set(positions) == set(nodes["gene"]), "Radial layout did not assign every node")

    # Conservatively reserve outline padding for every node during clearance.
    size_by_gene = {
        row.gene: node_display_size(row.gene, int(row.supporting_neighborhood_occurrence_count))
        + PATHWAY_OUTLINE_PADDING
        for row in nodes.itertuples()
    }
    genes = nodes["gene"].tolist()
    minimum_clearance = float("inf")
    closest_pair = ""
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
    return positions


def pathway_outline(codes: list[str]) -> str:
    if not codes:
        return ""
    colors = ",".join(PATHWAY_THEMES[code][1] for code in codes)
    values = ",".join("1" for _ in codes)
    return (
        'circoschart: arcstart=270 firstarc=.78 firstarcwidth=.16 arcwidth=.16 '
        f'borderwidth=0 colorlist="{colors}" valuelist="{values}" showlabels=false'
    )


def prepare_cytoscape_tables(
    nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cy_nodes = nodes.copy()
    cy_edges = edges.copy()

    def display_label(row: pd.Series) -> str:
        if pd.notna(row["upstream_depth_to_apoe"]):
            return f"{row['gene']}\nU{int(row['upstream_depth_to_apoe'])}"
        return f"{row['gene']}\n{int(row['supporting_neighborhood_occurrence_count'])}/{SUPPORTING_RUNS}"

    cy_nodes["display_label"] = cy_nodes.apply(display_label, axis=1)
    cy_nodes["display_font_size"] = cy_nodes["gene"].str.len().map(lambda length: 19 if length >= 7 else 20)
    cy_nodes["display_size"] = cy_nodes.apply(
        lambda row: node_display_size(row["gene"], int(row["supporting_neighborhood_occurrence_count"])), axis=1
    )
    cy_nodes["query_hit_class"] = cy_nodes["query_hit_bool"].map({True: "query_hit", False: "not_query_hit"})
    positions = radial_positions(nodes, edges)
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
    cy_edges["direct_edge_class"] = cy_edges["direct_edge_bool"].map(
        {True: "direct_apoe", False: "other_displayed"}
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
        "NODE_LABEL_MAX_WIDTH": 125,
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
        mapping("EDGE_WIDTH", "direct_edge_class", "d", ["other_displayed", "direct_apoe"], [1.2, 2.8]),
        mapping("EDGE_UNSELECTED_PAINT", "direct_edge_class", "d", ["other_displayed", "direct_apoe"], ["#A8A8A8", "#4D4D4D"]),
        mapping("EDGE_STROKE_UNSELECTED_PAINT", "direct_edge_class", "d", ["other_displayed", "direct_apoe"], ["#A8A8A8", "#4D4D4D"]),
        mapping("NODE_CUSTOMGRAPHICS_1", "pathway_outline", "p"),
        mapping("NODE_CUSTOMGRAPHICS_SIZE_1", "pathway_outline_size", "p"),
    ]
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
        border: str = "#555555",
        border_width: int = 2,
        size: int = 28,
    ) -> None:
        p4c.add_annotation_shape(
            type="ELLIPSE",
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

    title_x, title_y = -720.0, -920.0
    add_text("APOE-centered astrocyte consensus network", title_x, title_y, "figure_title", 29, "bold", "#111111")
    add_text(
        "U1-U2 nodes are upstream context; D1-D2 nodes lie downstream; arrows follow the Bayesian-network direction",
        title_x,
        title_y + 55,
        "figure_subtitle",
        16,
        color="#555555",
    )

    legend_x, legend_top = 780.0, -650.0
    text_x = legend_x + 46.0
    add_text("HOW TO READ", legend_x, legend_top, "legend_title", 20, "bold", "#111111")
    add_text("Node size and x/4 show neighborhood recurrence", legend_x, legend_top + 52, "legend_recurrence_1")
    add_text("across the 4 supporting runs", legend_x, legend_top + 86, "legend_recurrence_2")
    add_text("U1/U2: upstream distance to APOE", legend_x, legend_top + 126, "legend_upstream")
    add_text("Thick black border: mitochondrial query hit at >=1/4", legend_x, legend_top + 166, "legend_query_hit")

    deg_heading_y = legend_top + 218
    add_text("NODE FILL  ·  PHASE 8 DIRECT DEG", legend_x, deg_heading_y, "legend_deg_heading", 17, "bold", "#111111")
    for index, (deg_class, label) in enumerate(DEG_LABELS):
        y_pos = deg_heading_y + 45 + index * 48
        add_symbol(legend_x, y_pos, f"legend_deg_symbol_{index}", DEG_COLORS[deg_class])
        add_text(label, text_x, y_pos + 8, f"legend_deg_text_{index}", color="#333333")

    pathway_heading_y = deg_heading_y + 275
    add_text("PATHWAY OUTLINE", legend_x, pathway_heading_y, "legend_pathway_heading", 17, "bold", "#111111")
    add_text("Contextual annotations; none has BH FDR < 0.05", legend_x, pathway_heading_y + 39, "legend_pathway_note", 15, color="#555555")
    for index, (code, (label, color)) in enumerate(PATHWAY_THEMES.items()):
        y_pos = pathway_heading_y + 84 + index * 48
        add_symbol(legend_x, y_pos, f"legend_pathway_symbol_{code}", "#FFFFFF", color, 6, 30)
        add_text(label, text_x, y_pos + 6, f"legend_pathway_text_{code}", color="#333333")

    scope_heading_y = pathway_heading_y + 84 + len(PATHWAY_THEMES) * 48 + 55
    add_text("DISPLAY SCOPE", legend_x, scope_heading_y, "legend_scope_heading", 17, "bold", "#111111")
    add_text("19 nodes / 18 edges", legend_x, scope_heading_y + 43, "legend_scope_counts")
    add_text("All APOE edges: 2 incoming, 11 outgoing", legend_x, scope_heading_y + 80, "legend_scope_direct")
    add_text("D2 paths to all 7 observed query hits", legend_x, scope_heading_y + 117, "legend_scope_hits")
    add_text(
        "Display threshold >=1/4 is a coverage choice, not a significance cutoff",
        legend_x,
        scope_heading_y + 165,
        "legend_scope_threshold",
        15,
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
        cy_nodes["gene"].tolist(), cy_nodes["cy_x"].tolist(), cy_nodes["cy_y"].tolist(), network=network_suid
    )
    p4c.set_node_color_bypass(["APOE"], "#111111", network=network_suid)
    p4c.set_node_label_color_bypass(["APOE"], "#FFFFFF", network=network_suid)
    p4c.set_node_border_color_bypass(["APOE"], "#111111", network=network_suid)
    p4c.set_node_border_width_bypass(["APOE"], 5.0, network=network_suid)
    p4c.set_node_font_size_bypass(["APOE"], 25, network=network_suid)
    p4c.set_node_property_bypass(["APOE"], [156.0], "NODE_SIZE", network=network_suid)
    add_annotations(network_suid)
    p4c.fit_content(network=network_suid)

    session_path = output_dir / f"{OUTPUT_STEM}_cytoscape.cys"
    style_path = output_dir / f"{OUTPUT_STEM}_cytoscape_style"
    p4c.save_session(str(session_path), overwrite_file=True)
    p4c.export_visual_styles(filename=str(style_path), type="XML", styles=STYLE_NAME, overwrite_file=True)

    export_log: dict[str, object] = {
        "cytoscape_version": version.get("cytoscapeVersion"),
        "py4cytoscape_version": p4c.__version__,
        "network": "Astrocytes",
        "driver": "APOE",
        "network_suid": network_suid,
        "node_count": len(cy_nodes),
        "edge_count": len(cy_edges),
        "direct_incoming_edges": EXPECTED_DIRECT_INCOMING,
        "direct_outgoing_edges": EXPECTED_DIRECT_OUTGOING,
        "supporting_run_count": SUPPORTING_RUNS,
        "query_hit_threshold": QUERY_HIT_THRESHOLD,
        "query_hit_count": EXPECTED_QUERY_HITS,
        "threshold_rationale": "1/4 retains all 7 observed hits in a readable 19-node tree; 2/4 loses 3 hits but removes only 2 nodes",
        "layout": "collision_checked_radial_tree_without_guide_rings",
        "radial_level_radii": {"D1": D1_RADIUS, "D2": D2_RADIUS, "U1": U1_RADIUS, "U2": U2_RADIUS},
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
    (output_dir / f"{OUTPUT_STEM}_cytoscape_export.json").write_text(
        json.dumps(export_log, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(export_log, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--png-zoom", type=int, default=300)
    args = parser.parse_args()
    render(args.input_dir.resolve(), args.output_dir.resolve(), args.png_zoom)


if __name__ == "__main__":
    main()
