#!/usr/bin/env python3
"""Build COX7C astrocyte consensus tables and render the figure in Cytoscape."""

from __future__ import annotations

import argparse
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "COX7C"
    / "astrocytes"
)
CANONICAL = ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
BACKGROUNDS = ROOT / "results/minerva_production/12_kda/kda_background_members.tsv.gz"
SIGNATURES = ROOT / "results/minerva_production/12_kda/kda_signature_members.tsv"
NETWORK = ROOT / "data/bayesian_network/Astrocytes/result.links3.links.txt"
ANNOTATION = ROOT / "results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz"
MAST = ROOT / "results/minerva_production/08_mast/astrocytes.yu_mast_de.tsv.gz"
MSIGDB = ROOT / "data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt"

DRIVER = "COX7C"
NETWORK_NAME = "Astrocytes"
SUPPORTING_RUNS = 2
QUERY_HIT_THRESHOLD = 1
MAX_DOWNSTREAM_DEPTH = 2
MAX_UPSTREAM_DEPTH = 2
SCHEMA = "phase18_cox7c_astrocyte_consensus_v1"
OUTPUT_PREFIX = "phase18_cox7c_astrocyte_consensus"
FIGURE_STEM = "phase18_cox7c_astrocyte_consensus_network_pathways"

EXPECTED_QUERY_HITS = {
    "ATP5F1E",
    "ATP5ME",
    "ATP5PF",
    "COX5B",
    "COX6C",
    "NDUFB4",
    "SLIRP",
    "TOMM7",
    "UQCRB",
    "UQCRH",
}
EXPECTED_DIRECT_IN = {"RPL11"}
EXPECTED_DIRECT_OUT = {
    "ATP5F1E",
    "ATP5PD",
    "ATP5PF",
    "C8orf59",
    "CCM2",
    "COMMD6",
    "COPS9",
    "DYNLL1",
    "LAMTOR5",
    "NDUFB4",
    "RPL27",
    "RPL35A",
    "SSB",
    "TOMM7",
    "UQCRB",
}
EXPECTED_UPSTREAM_CONTEXT = {"RPL11", "RPLP1"}
PATHWAY_THEMES = (
    {
        "pathway": "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA",
        "code": "O",
        "label": "ETC / oxidative phosphorylation",
        "color": "#0072B2",
        "expected_members": {
            "ATP5F1E",
            "ATP5ME",
            "ATP5PD",
            "ATP5PF",
            "COX5B",
            "COX6C",
            "COX7C",
            "NDUFB4",
            "UQCRB",
            "UQCRH",
        },
    },
    {
        "pathway": "REACTOME_CRISTAE_FORMATION",
        "code": "C",
        "label": "Cristae formation",
        "color": "#009E73",
        "expected_members": {"ATP5F1E", "ATP5ME", "ATP5PD", "ATP5PF"},
    },
    {
        "pathway": "WP_CYTOPLASMIC_RIBOSOMAL_PROTEINS",
        "code": "R",
        "label": "Cytosolic ribosome",
        "color": "#6F4E9C",
        "expected_members": {"RPL11", "RPL27", "RPL35A", "RPLP1"},
    },
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin({"TRUE", "T", "1", "YES"})


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
    require(len(rows) == SUPPORTING_RUNS, f"Expected 2 supporting runs, found {len(rows)}")
    require(rows["kda_run_id"].is_unique, "Supporting run IDs are not unique")
    require(rows["final_layer"].eq(2).all(), "Both supporting COX7C runs must use final D2")
    require(truth_series(rows["self_excluded"]).all(), "COX7C was not self-excluded in every supporting run")
    return rows


def load_graph() -> nx.DiGraph:
    edges = pd.read_csv(NETWORK, sep="\t", header=None, names=["source", "target"])
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    require(nx.is_directed_acyclic_graph(graph), "The astrocyte Bayesian network is not acyclic")
    require(graph.number_of_nodes() == 8285 and graph.number_of_edges() == 8881, "Unexpected network dimensions")
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
    require(all(backgrounds.values()), "At least one supporting run lacks an effective background")
    require(set(signatures) == run_ids and all(signatures.values()), "At least one supporting run lacks an effective query")
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
    upstream = set(nx.single_source_shortest_path_length(graph.reverse(copy=False), DRIVER, cutoff=2)) - {DRIVER}
    path_nodes = {DRIVER}
    for target in hits:
        require(nx.shortest_path_length(graph, DRIVER, target) <= MAX_DOWNSTREAM_DEPTH, f"Hit lies beyond D2: {target}")
        for path in nx.all_shortest_paths(graph, DRIVER, target):
            path_nodes.update(path)
    nodes = path_nodes | EXPECTED_DIRECT_IN | EXPECTED_DIRECT_OUT | upstream
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
        hits = (signatures[run_id] & set(lengths)) - {DRIVER}
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
                "driver_self_excluded": True,
                "reconstructed_query_hit_count": len(hits),
                "reconstructed_query_hits": ";".join(sorted(hits)),
            }
        )

    retained_hits = {gene for gene, count in query_hit_occurrence.items() if count >= QUERY_HIT_THRESHOLD}
    require(retained_hits == EXPECTED_QUERY_HITS, f"Unexpected retained query hits: {sorted(retained_hits)}")
    require(neighborhood_occurrence[DRIVER] == SUPPORTING_RUNS, "COX7C is not present in both neighborhoods")

    downstream_lengths = nx.single_source_shortest_path_length(graph, DRIVER, cutoff=MAX_DOWNSTREAM_DEPTH)
    upstream_lengths = nx.single_source_shortest_path_length(
        graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH
    )
    upstream_context = set(upstream_lengths) - {DRIVER}
    require(upstream_context == EXPECTED_UPSTREAM_CONTEXT, "COX7C upstream context changed")

    display = display_for_hits(graph, retained_hits)
    display_nodes = set(display)
    require(display.number_of_nodes() == 23, f"Expected 23 display nodes, found {display.number_of_nodes()}")
    require(display.number_of_edges() == 23, f"Expected 23 display edges, found {display.number_of_edges()}")
    require(nx.is_directed_acyclic_graph(display), "Displayed COX7C graph is not acyclic")
    require(nx.is_weakly_connected(display), "Displayed COX7C graph is disconnected")
    require(display.has_edge("RPLP1", "RPL27"), "Expected RPLP1-to-RPL27 contextual edge is absent")

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
                "driver_was_self_excluded_from_query_overlap": gene == DRIVER,
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
        source_up = source in upstream_context
        target_down = target in downstream_lengths and target != DRIVER
        edge_rows.append(
            {
                "schema_version": SCHEMA,
                "network": NETWORK_NAME,
                "source": source,
                "target": target,
                "is_directly_incident_to_cox7c": source == DRIVER or target == DRIVER,
                "is_upstream_context_edge": source_up and (target in upstream_context or target == DRIVER),
                "is_cross_context_edge": source_up and target_down,
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
    require(len(result) == 4115, f"Expected 4,115 MSigDB pathways, found {len(result)}")
    return result


def build_pathway_tables(graph: nx.DiGraph, nodes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gene_sets = load_gene_sets()
    annotated_universe = set().union(*(row["genes"] for row in gene_sets))
    background = set(graph.nodes) & annotated_universe
    displayed = set(nodes["gene"]) & background
    require(len(background) == 5769, f"Unexpected mapped astrocyte background: {len(background)}")
    require(len(displayed) == 22, f"Unexpected mapped displayed-gene count: {len(displayed)}")

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
        selected = bool(theme)
        row["selected_nonredundant_representative"] = selected
        row["pathway_code"] = theme["code"] if selected else None
        row["pathway_display_label"] = theme["label"] if selected else None
        row["pathway_color"] = theme["color"] if selected else None
        row["selection_rule"] = (
            "prespecified nonredundant representative with BH FDR < 0.05"
            if selected
            else None
        )
    rows.sort(key=lambda row: (float(row["raw_hypergeometric_p"]), str(row["pathway"])))

    selected = {row["pathway"]: row for row in rows if row["selected_nonredundant_representative"]}
    require(set(selected) == set(theme_by_pathway), "A selected pathway representative is missing")
    memberships: list[dict[str, Any]] = []
    gene_set_by_name = {row["pathway"]: row for row in gene_sets}
    for theme in PATHWAY_THEMES:
        result = selected[theme["pathway"]]
        members = displayed & gene_set_by_name[theme["pathway"]]["genes"]
        require(members == theme["expected_members"], f"Unexpected members for {theme['pathway']}")
        require(float(result["bh_fdr"]) < 0.05, f"Selected pathway is not FDR significant: {theme['pathway']}")
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
                    "fdr_significant_0_05": True,
                }
            )
    require(len(memberships) == 18, f"Expected 18 pathway membership rows, found {len(memberships)}")
    return pd.DataFrame(rows), pd.DataFrame(memberships)


def write_tsv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="")
    require(path.exists() and path.stat().st_size > 0, f"Failed to write {path}")


def write_graphml(path: Path, nodes: pd.DataFrame, edges: pd.DataFrame, membership: pd.DataFrame) -> None:
    graph = nx.DiGraph(network=NETWORK_NAME, driver=DRIVER, query_hit_display_threshold="1/2")
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
        source = str(record.pop("source"))
        target = str(record.pop("target"))
        attributes = {key: "" if pd.isna(value) else value for key, value in record.items() if key != "schema_version"}
        graph.add_edge(source, target, **attributes)
    nx.write_graphml(graph, path)
    require(path.exists() and path.stat().st_size > 0, "GraphML export failed")


def write_documentation(output_dir: Path, pathway_ora: pd.DataFrame) -> None:
    selected = pathway_ora.loc[truth_series(pathway_ora["selected_nonredundant_representative"])].set_index("pathway")
    summaries = []
    for theme in PATHWAY_THEMES:
        row = selected.loc[theme["pathway"]]
        summaries.append(
            f"{theme['label']} ({int(row['overlap_gene_count'])} genes; BH FDR = {float(row['bh_fdr']):.3g})"
        )
    caption = f"""# COX7C astrocyte consensus network with pathway outlines

COX7C-centered astrocyte Bayesian-network neighborhood reconstructed from the two conservative-support COX7C runs. Arrows follow the stored Bayesian-network direction and represent model-derived hypotheses. The display retains the direct incoming edge, all 15 direct outgoing edges, the U2 upstream extension, every model edge among displayed nodes, and D2 paths to mitochondrial query hits observed in at least one supporting run.

The 1/2 display threshold yields 23 nodes and 23 edges and retains ten self-excluded query hits: `ATP5F1E`, `ATP5ME`, `ATP5PF`, `COX5B`, `COX6C`, `NDUFB4`, `SLIRP`, `TOMM7`, `UQCRB`, and `UQCRH`. Raising the threshold to 2/2 would retain only four hits while reducing the display to 19 nodes. Thus 1/2 is a coverage choice for visualization, not a statistical cutoff. Node size and `x/2` show supporting-neighborhood occurrence; U1/U2 show upstream graph distance. Thick black borders mark retained query hits, and fill shows stored Phase 8 direct-DEG direction.

Colored outer boundaries show three nonredundant, FDR-significant pathway representatives: {', '.join(summaries)}. Segmented outlines indicate multiple memberships.
"""
    methods = f"""# Methods: COX7C astrocyte consensus network

## Consensus reconstruction

The two conservative-support COX7C rows were read from `call_key_driver_returns.tsv`. Each astrocyte Bayesian network was restricted to the run's recorded effective background, and its D2 COX7C neighborhood was reconstructed. Effective query genes came from `kda_signature_members.tsv`. Because COX7C belongs to both mitochondrial queries, it was removed before counting final overlap, matching the Phase 18 self-exclusion rule. The reconstructed overlaps exactly matched the stored final overlap counts of six and eight.

Neighborhood occurrence counts the supporting run-specific D2 neighborhoods containing a gene. Query-hit occurrence separately counts the self-excluded effective queries in which the gene occurred in that neighborhood. The selected threshold is at least one of two runs. It retains ten hits and yields 23 nodes; 2/2 retains four hits and yields 19 nodes. The figure also includes all direct COX7C edges, the upstream chain `RPLP1 -> RPL11 -> COX7C`, and the additional displayed model edge `RPLP1 -> RPL27`.

## Pathway annotations

ORA used the 22 displayed genes represented in MSigDB C2:CP v2026.1. The explicit universe was 5,769 astrocyte Bayesian-network genes represented in that collection. One-sided hypergeometric tests were run for 1,594 pathways with 15-500 mapped background genes, followed by Benjamini-Hochberg correction. The three displayed, nonredundant representatives are {', '.join(summaries)}; all meet BH FDR < 0.05. An outline indicates membership, not pathway activity or experimental causality.

## Rendering

The validated graph tables were rendered in Cytoscape 3.10.4 using a deterministic, collision-checked radial layout without guide rings. COX7C is centered, upstream context occupies the left sector, D1 nodes form the inner radial arc, and D2 hits remain near their D1 parents. Node and pathway colors use a colorblind-safe palette. PNG is exported at 300% zoom, PDF and SVG are retained as vector formats, and the editable `.cys` session and visual-style XML are saved beside the figure.
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
    checks = [
        ("supporting_run_count", SUPPORTING_RUNS == 2, str(SUPPORTING_RUNS)),
        ("selected_threshold", QUERY_HIT_THRESHOLD == 1, "1/2"),
        ("threshold_2_hit_loss", int(threshold_two["retained_query_hit_count"]) == 4, str(threshold_two["retained_query_hit_count"])),
        ("node_count", len(nodes) == 23, str(len(nodes))),
        ("edge_count", len(edges) == 23, str(len(edges))),
        ("query_hit_count", int(truth_series(nodes["is_query_hit_meeting_display_threshold"]).sum()) == 10, "10"),
        ("all_direct_incoming", int(truth_series(nodes["is_direct_incoming_neighbor"]).sum()) == 1, "1"),
        ("all_direct_outgoing", int(truth_series(nodes["is_direct_outgoing_neighbor"]).sum()) == 15, "15"),
        ("pathway_representative_count", len(selected) == 3, str(len(selected))),
        ("selected_pathways_fdr_below_0_05", bool((selected["bh_fdr"] < 0.05).all()), str(selected["bh_fdr"].max())),
        ("pathway_membership_rows", len(membership) == 18, str(len(membership))),
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
    rows = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path != manifest_path:
            rows.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_tsv(manifest_path, pd.DataFrame(rows))


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_rows = load_support_rows()
    graph = load_graph()
    backgrounds, signatures = load_run_sets(set(support_rows["kda_run_id"].astype(str)))
    nodes, edges, sensitivity, run_summary = build_consensus_tables(
        graph, support_rows, backgrounds, signatures
    )
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
    write_graphml(output_dir / "phase18_cox7c_astrocyte.graphml", nodes, edges, pathway_membership)

    from render_phase18_cox7c_astrocyte_cytoscape import render as render_cytoscape

    render_cytoscape(output_dir, output_dir, png_zoom=300)
    write_documentation(output_dir, pathway_ora)
    checks = validate_outputs(output_dir, nodes, edges, sensitivity, pathway_ora, pathway_membership)
    write_tsv(output_dir / f"{FIGURE_STEM}_checks.tsv", checks)
    write_manifest(output_dir)

    print(f"Wrote {output_dir / (FIGURE_STEM + '.png')}")
    print("Display: 23 nodes, 23 edges, 10 self-excluded query hits at >=1/2")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir.resolve())


if __name__ == "__main__":
    main()
