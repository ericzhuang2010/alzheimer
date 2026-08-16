#!/usr/bin/env python3
"""Prepare validated source tables for the RPL11 astrocyte Cytoscape figure."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
    / "analysis"
    / "phase_18_key_driver_selection"
    / "RPL11"
)
CANONICAL = ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
BACKGROUNDS = ROOT / "results/minerva_production/12_kda/kda_background_members.tsv.gz"
NETWORK = ROOT / "data/bayesian_network/Astrocytes/result.links3.links.txt"
ANNOTATION = ROOT / "results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz"
MAST = ROOT / "results/minerva_production/08_mast/astrocytes.yu_mast_de.tsv.gz"
MSIGDB = ROOT / "data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt"

SCHEMA = "phase18_rpl11_astrocyte_consensus_v2"
NETWORK_NAME = "Astrocytes"
DRIVER = "RPL11"
SUPPORTING_RUNS = 3
RECURRENCE_THRESHOLD = 1
MAX_DOWNSTREAM_DEPTH = 3
MAX_UPSTREAM_DEPTH = 2
OUTPUT_PREFIX = "phase18_rpl11_astrocyte_consensus"
PATHWAY_THEMES = (
    {
        "pathway": "KEGG_RIBOSOME",
        "code": "R",
        "label": "Cytosolic ribosome",
        "color": "#6F4E9C",
        "contextual": True,
    },
    {
        "pathway": "WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA",
        "code": "O",
        "label": "ETC / oxidative phosphorylation",
        "color": "#0072B2",
        "contextual": False,
    },
    {
        "pathway": "REACTOME_CRISTAE_FORMATION",
        "code": "C",
        "label": "Cristae formation",
        "color": "#009E73",
        "contextual": False,
    },
)


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
    """Exact P(X >= overlap) without adding a SciPy dependency to this helper."""

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
    require(len(rows) == SUPPORTING_RUNS, f"Expected {SUPPORTING_RUNS} supporting astrocyte runs, found {len(rows)}")
    require(rows["kda_run_id"].is_unique, "Supporting astrocyte run identifiers are not unique")
    rows["final_layer"] = pd.to_numeric(rows["final_layer"], errors="raise").astype(int)
    require(rows["final_layer"].between(1, MAX_DOWNSTREAM_DEPTH).all(), "A final layer lies outside D1-D3")
    return rows


def load_graph() -> nx.DiGraph:
    edges = pd.read_csv(NETWORK, sep="\t", header=None, names=["source", "target"])
    graph = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    require(nx.is_directed_acyclic_graph(graph), "The astrocyte Bayesian network is not acyclic")
    require(graph.number_of_nodes() == 8285 and graph.number_of_edges() == 8881, "Unexpected astrocyte network dimensions")
    require(DRIVER in graph, "RPL11 is absent from the astrocyte network")
    require(graph.in_degree(DRIVER) == 1 and graph.out_degree(DRIVER) == 3, "Unexpected RPL11 direct degree")
    return graph


def load_run_backgrounds(run_ids: set[str]) -> dict[str, set[str]]:
    result = {run_id: set() for run_id in run_ids}
    for chunk in pd.read_csv(BACKGROUNDS, sep="\t", usecols=["kda_run_id", "gene"], chunksize=500_000):
        selected = chunk.loc[chunk["kda_run_id"].isin(run_ids)]
        for run_id, group in selected.groupby("kda_run_id"):
            result[str(run_id)].update(group["gene"].astype(str))
    require(all(result.values()), "At least one supporting run lacks a recorded effective background")
    return result


def load_annotation(display_genes: set[str]) -> dict[str, dict[str, Any]]:
    columns = ["symbol_hgnc_current", "hgnc_name", "is_mitocarta3"]
    rows = pd.read_csv(ANNOTATION, sep="\t", usecols=columns, low_memory=False)
    rows = rows.loc[rows["symbol_hgnc_current"].isin(display_genes)].copy()
    result: dict[str, dict[str, Any]] = {}
    for row in rows.itertuples(index=False):
        gene = str(row.symbol_hgnc_current)
        name = "" if pd.isna(row.hgnc_name) else str(row.hgnc_name)
        ribosomal = name.lower().startswith("ribosomal protein") and "mitochondrial" not in name.lower()
        current = result.setdefault(gene, {"is_core_mito": False, "is_cytosolic_ribosomal": False})
        current["is_core_mito"] = bool(current["is_core_mito"] or str(row.is_mitocarta3).upper() in {"TRUE", "T", "1"})
        current["is_cytosolic_ribosomal"] = bool(current["is_cytosolic_ribosomal"] or ribosomal)
    require(DRIVER in result, "RPL11 lacks a gene annotation")
    return result


def load_deg(display_genes: set[str]) -> dict[str, dict[str, Any]]:
    rows = pd.read_csv(MAST, sep="\t", usecols=["gene", "paper_deg", "logFC"], low_memory=False)
    rows = rows.loc[rows["gene"].isin(display_genes) & truth_series(rows["paper_deg"])].copy()
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"up": 0, "down": 0})
    for row in rows.itertuples(index=False):
        direction = "up" if float(row.logFC) > 0 else "down"
        result[str(row.gene)][direction] += 1
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


def build_consensus_tables(
    graph: nx.DiGraph,
    support_rows: pd.DataFrame,
    backgrounds: dict[str, set[str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    neighborhood_occurrence: Counter[str] = Counter()
    query_hit_occurrence: Counter[str] = Counter()
    for row in support_rows.itertuples(index=False):
        induced = graph.subgraph(backgrounds[str(row.kda_run_id)])
        require(DRIVER in induced, f"RPL11 is absent from the effective background for {row.kda_run_id}")
        lengths = nx.single_source_shortest_path_length(induced, DRIVER, cutoff=int(row.final_layer))
        neighborhood_occurrence.update(lengths.keys())
        query_hit_occurrence.update(split_genes(row.published_overlap_items))

    recurrent_hits = {
        gene for gene, count in query_hit_occurrence.items() if count >= RECURRENCE_THRESHOLD
    }
    require(neighborhood_occurrence[DRIVER] == SUPPORTING_RUNS, "RPL11 should occur in all supporting neighborhoods")
    require(
        all(0 <= count <= SUPPORTING_RUNS for count in neighborhood_occurrence.values()),
        "A neighborhood-recurrence count exceeds the three supporting runs",
    )
    require(
        recurrent_hits
        == {
            "ATP5F1E",
            "ATP5ME",
            "ATP5PF",
            "COX6C",
            "COX7C",
            "CYB5R3",
            "NDUFB4",
            "PSAP",
            "SLIRP",
            "TOMM7",
            "UQCRB",
            "UQCRH",
        },
        f"Unexpected recurrent astrocyte hits: {sorted(recurrent_hits)}",
    )

    direct_in = set(graph.predecessors(DRIVER))
    direct_out = set(graph.successors(DRIVER))
    upstream_lengths = nx.single_source_shortest_path_length(
        graph.reverse(copy=False), DRIVER, cutoff=MAX_UPSTREAM_DEPTH
    )
    upstream_context = set(upstream_lengths) - {DRIVER}
    downstream_lengths = nx.single_source_shortest_path_length(
        graph, DRIVER, cutoff=MAX_DOWNSTREAM_DEPTH
    )
    path_nodes = {DRIVER}
    for target in recurrent_hits:
        require(target in downstream_lengths, f"Recurrent hit lies beyond D3: {target}")
        for path in nx.all_shortest_paths(graph, DRIVER, target):
            if len(path) - 1 <= MAX_DOWNSTREAM_DEPTH:
                path_nodes.update(path)
    display_nodes = path_nodes | direct_in | direct_out | upstream_context
    display = graph.subgraph(display_nodes).copy()

    require(direct_in == {"RPLP1"}, f"Unexpected direct incoming genes: {sorted(direct_in)}")
    require(direct_out == {"COX7C", "CWC15", "PRDX1"}, f"Unexpected direct outgoing genes: {sorted(direct_out)}")
    require(upstream_context == {"RPLP1", "RPS25"}, f"Unexpected upstream context: {sorted(upstream_context)}")
    require(display.number_of_nodes() == 18 and display.number_of_edges() == 17, "Unexpected displayed graph dimensions")
    require(nx.is_tree(display.to_undirected()), "The displayed astrocyte network is not a tree")

    annotation = load_annotation(display_nodes)
    deg = load_deg(display_nodes)
    node_rows: list[dict[str, Any]] = []
    for gene in sorted(display_nodes):
        reasons: list[str] = []
        if gene == DRIVER:
            reasons.append("driver")
        if gene in upstream_context:
            reasons.append("upstream_context")
        if gene in direct_in:
            reasons.append("all_direct_incoming")
        if gene in direct_out:
            reasons.append("all_direct_outgoing")
        if gene in recurrent_hits:
            reasons.append("recurrent_query_hit")
        if gene in path_nodes and gene not in recurrent_hits and gene != DRIVER:
            reasons.append("shortest_path_connector")
        evidence = deg[gene]
        occurrence = neighborhood_occurrence.get(gene, 0)
        hit_count = query_hit_occurrence.get(gene, 0)
        node_rows.append(
            {
                "schema_version": SCHEMA,
                "network": NETWORK_NAME,
                "gene": gene,
                "included_reason": "|".join(reasons),
                "directed_depth_from_rpl11": downstream_lengths.get(gene) if gene != DRIVER else 0,
                "upstream_depth_to_rpl11": upstream_lengths.get(gene) if gene != DRIVER else None,
                "is_direct_incoming_neighbor": gene in direct_in,
                "is_direct_outgoing_neighbor": gene in direct_out,
                "supporting_neighborhood_occurrence_count": occurrence,
                "supporting_neighborhood_occurrence_fraction": occurrence / SUPPORTING_RUNS,
                "query_hit_occurrence_count": hit_count,
                "query_hit_occurrence_fraction": hit_count / SUPPORTING_RUNS,
                "query_hit_display_threshold": RECURRENCE_THRESHOLD,
                "is_recurrent_query_hit": gene in recurrent_hits,
                "is_core_mitocarta": bool(annotation.get(gene, {}).get("is_core_mito")),
                "is_cytosolic_ribosomal": bool(annotation.get(gene, {}).get("is_cytosolic_ribosomal")),
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
                "is_directly_incident_to_rpl11": source == DRIVER or target == DRIVER,
                "is_upstream_context_edge": source in upstream_context,
                "source_directed_depth": downstream_lengths.get(source),
                "target_directed_depth": downstream_lengths.get(target),
                "source_upstream_depth": upstream_lengths.get(source) if source != DRIVER else None,
                "target_upstream_depth": upstream_lengths.get(target) if target != DRIVER else None,
                "source_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(source, 0),
                "target_supporting_neighborhood_occurrence_count": neighborhood_occurrence.get(target, 0),
            }
        )
    return pd.DataFrame(node_rows), pd.DataFrame(edge_rows)


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
    require(len(displayed) == 18, f"Unexpected mapped displayed-gene count: {len(displayed)}")

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
        selected = bool(
            theme
            and int(row["overlap_gene_count"]) >= 3
            and (q_value < 0.05 or bool(theme["contextual"]))
        )
        row["selected_representative"] = selected
        row["pathway_code"] = theme["code"] if selected else None
        row["pathway_display_label"] = theme["label"] if selected else None
        row["pathway_color"] = theme["color"] if selected else None
        row["selection_rule"] = (
            (
                "prespecified contextual pathway with at least 3 displayed genes"
                if theme and bool(theme["contextual"]) and q_value >= 0.05
                else "nonredundant representative with BH FDR < 0.05 and at least 3 displayed genes"
            )
            if selected
            else None
        )
    rows.sort(key=lambda row: (float(row["raw_hypergeometric_p"]), str(row["pathway"])))

    selected = {row["pathway"]: row for row in rows if row["selected_representative"]}
    require(set(selected) == set(theme_by_pathway), f"Unexpected selected pathway representatives: {sorted(selected)}")
    require(selected["KEGG_RIBOSOME"]["overlap_gene_count"] == 3, "Unexpected ribosome overlap")
    require(
        selected["WP_ELECTRON_TRANSPORT_CHAIN_OXPHOS_SYSTEM_IN_MITOCHONDRIA"]["overlap_gene_count"] == 8,
        "Unexpected ETC/OXPHOS overlap",
    )
    require(selected["REACTOME_CRISTAE_FORMATION"]["overlap_gene_count"] == 3, "Unexpected cristae overlap")

    memberships: list[dict[str, Any]] = []
    for theme in PATHWAY_THEMES:
        result = selected[theme["pathway"]]
        for gene in split_genes(result["overlap_genes"]):
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
                }
            )
    require(len(memberships) == 14, f"Expected 14 pathway-membership rows, found {len(memberships)}")
    return pd.DataFrame(rows), pd.DataFrame(memberships)


def write_tsv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="")
    require(path.exists() and path.stat().st_size > 0, f"Failed to write {path}")


def prepare(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_rows = load_support_rows()
    graph = load_graph()
    backgrounds = load_run_backgrounds(set(support_rows["kda_run_id"].astype(str)))
    nodes, edges = build_consensus_tables(graph, support_rows, backgrounds)
    pathway_ora, pathway_membership = build_pathway_tables(graph, nodes)

    outputs = {
        f"{OUTPUT_PREFIX}_network_nodes.tsv": nodes,
        f"{OUTPUT_PREFIX}_network_edges.tsv": edges,
        f"{OUTPUT_PREFIX}_pathway_ora.tsv": pathway_ora,
        f"{OUTPUT_PREFIX}_pathway_membership.tsv": pathway_membership,
    }
    for filename, frame in outputs.items():
        write_tsv(output_dir / filename, frame)

    summary = {
        "network": NETWORK_NAME,
        "supporting_runs": SUPPORTING_RUNS,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "direct_incoming_edges": 1,
        "direct_outgoing_edges": 3,
        "upstream_context": ["RPLP1", "RPS25"],
        "recurrent_query_hits": sorted(nodes.loc[truth_series(nodes["is_recurrent_query_hit"]), "gene"]),
        "pathway_test_count": len(pathway_ora),
        "selected_pathways": pathway_membership["pathway"].drop_duplicates().tolist(),
        "outputs": {
            filename: {"rows": len(frame), "bytes": (output_dir / filename).stat().st_size}
            for filename, frame in outputs.items()
        },
    }
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    prepare(args.output_dir.resolve())


if __name__ == "__main__":
    main()
