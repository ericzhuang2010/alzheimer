#!/usr/bin/env python3
"""Shared preparation and plotting helpers for Phase 12 KDA network figures."""

from __future__ import annotations

import csv
import gzip
import hashlib
import math
import os
import tempfile
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(PROJECT_ROOT / "results" / ".matplotlib_cache"),
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402
from scipy.stats import cauchy, spearmanr  # noqa: E402


SCHEMA_VERSION = "phase12_kda_network_figures_v1"
PHASE12_DIR = PROJECT_ROOT / "results" / "minerva_production" / "12_kda"
PHASE08_DIR = PROJECT_ROOT / "results" / "minerva_production" / "08_mast"
ANNOTATION_DIR = PROJECT_ROOT / "results" / "minerva_production" / "03_annotations"
FIGURE_DATA_DIR = PROJECT_ROOT / "results" / "figures" / "analysis" / "phase12_kda"
DEFAULT_OUTPUT_DIR = FIGURE_DATA_DIR / "network_figures"

NETWORK_ORDER = [
    "Astrocytes",
    "Excitatory_neurons",
    "Inhibitory_neurons",
    "Microglia",
    "OPCs",
    "Oligodendrocytes",
    "Vasculature_cells",
]
NETWORK_LABELS = {
    "Astrocytes": "Astrocytes",
    "Excitatory_neurons": "Excitatory neurons",
    "Inhibitory_neurons": "Inhibitory neurons",
    "Microglia": "Microglia",
    "OPCs": "OPCs",
    "Oligodendrocytes": "Oligodendrocytes",
    "Vasculature_cells": "Vasculature",
    "CAMs": "CAMs",
    "T_cells": "T cells",
}
NETWORK_COLORS = {
    "Astrocytes": "#009E73",
    "Excitatory_neurons": "#E69F00",
    "Inhibitory_neurons": "#0072B2",
    "Microglia": "#CC79A7",
    "OPCs": "#56B4E9",
    "Oligodendrocytes": "#F0E442",
    "Vasculature_cells": "#D55E00",
    "CAMs": "#999999",
    "T_cells": "#000000",
}
EXPRESSION_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "phase12_blue_gray_orange",
    ["#0072B2", "#F2F2F2", "#D55E00"],
)
EXPRESSION_NORM = mcolors.TwoSlopeNorm(vmin=-1.5, vcenter=0.0, vmax=1.5)
COMPLEX_V_COLOR = "#7B3294"
NODE_DIAMETER_BASE = 7.0
NODE_DIAMETER_PER_DEGREE = 1.0
NODE_DIAMETER_CAP = 24.0
KEY_DRIVER_AREA_MULTIPLIER = 1.25
OVERLAP_RING_DIAMETER_PADDING = 3.0
COMPLEX_V_RING_DIAMETER_PADDING = 5.0

FOCUSED_ATP_DRIVERS = {
    "APOE",
    "LAMTOR5",
    "GABARAPL2",
    "RPL11",
    "RPS15",
    "FTL",
    "ANKRD11",
}
CONNECTIVITY_LABEL_GENES = [
    "APOE",
    "LAMTOR5",
    "GABARAPL2",
    "RPL11",
    "RPS15",
    "FTL",
    "ANKRD11",
    "SELENOW",
    "WDR82",
    "SLC11A1",
    "HSPA1A",
]

ACAT_EXAMPLE = [
    [0.5746569, 0.7090122, 0.7965851, 0.1149619],
    [0.6513363, 0.6671072, 0.5985140, 0.4991580],
    [0.1632148, 0.9312446, 0.9105127, 0.2293418],
    [0.8836971, 0.8424568, 0.2578088, 0.3955429],
    [0.6770827, 0.7551785, 0.3221481, 0.5570227],
]
ACAT_EXAMPLE_EXPECTED = [
    0.4768092003,
    0.6079561876,
    0.7884404860,
    0.7135191247,
    0.5935618969,
]


WANG_PANEL_SPECS = [
    {
        "panel": "A",
        "run_id": "primary_Ast_GRM3_M_e2_AD_down_mito",
        "driver": "APOE",
        "network": "Astrocytes",
        "fine_cell_type": "Ast GRM3",
        "sex": "Male",
        "apoe_group": "e2",
        "labels": {"APOE", "TUFM", "ATP5PB", "LDHB", "ATP5F1A", "CHCHD10", "AGT"},
        "targets": ["TUFM", "ATP5PB", "ATP5F1A", "CHCHD10"],
        "short_title": "Astrocyte APOE",
    },
    {
        "panel": "B",
        "run_id": "primary_Exc_L3_4_RORB_CUX2_M_e2_AD_down_mito",
        "driver": "LAMTOR5",
        "network": "Excitatory_neurons",
        "fine_cell_type": "Exc L3-4 RORB CUX2",
        "sex": "Male",
        "apoe_group": "e2",
        "labels": {
            "LAMTOR5", "ATP5IF1", "POP7", "ATP5MC2", "TMEM11", "CHCHD10",
            "NDUFA6", "TMEM126A", "NDUFB6", "MRPL4",
        },
        "targets": ["ATP5IF1", "ATP5MC2"],
        "short_title": "Excitatory-neuron LAMTOR5",
    },
    {
        "panel": "C",
        "run_id": "primary_Exc_L4_5_RORB_GABRG1_M_e2_AD_down_mito",
        "driver": "GABARAPL2",
        "network": "Excitatory_neurons",
        "fine_cell_type": "Exc L4-5 RORB GABRG1",
        "sex": "Male",
        "apoe_group": "e2",
        "labels": {
            "GABARAPL2", "CHCHD2", "MAGEF1", "SNAPC5", "PARK7", "NDUFA4",
            "ATP5MC3", "MRPS18B", "BAX",
        },
        "targets": ["CHCHD2", "PARK7", "ATP5MC3"],
        "short_title": "Excitatory-neuron GABARAPL2",
    },
]

SEX_REVERSAL_SPECS = [
    {
        "row": "APOE | Ast GRM3",
        "driver": "APOE",
        "network": "Astrocytes",
        "fine_cell_type": "Ast GRM3",
        "max_layer": 2,
        "labels": {"APOE", "TUFM", "ATP5PB", "LDHB", "ATP5F1A", "CHCHD10", "AGT"},
        "targets": ["TUFM", "ATP5PB", "ATP5F1A", "CHCHD10"],
        "female_run": "primary_Ast_GRM3_F_e2_AD_up_mito",
        "male_run": "primary_Ast_GRM3_M_e2_AD_down_mito",
    },
    {
        "row": "LAMTOR5 | Exc L4-5 RORB IL1RAPL2",
        "driver": "LAMTOR5",
        "network": "Excitatory_neurons",
        "fine_cell_type": "Exc L4-5 RORB IL1RAPL2",
        "max_layer": 3,
        "labels": {
            "LAMTOR5", "ATP5IF1", "POP7", "ATP5MC2", "TMEM11", "CHCHD10",
            "NDUFA6", "TMEM126A", "NDUFB6",
        },
        "targets": ["ATP5IF1", "ATP5MC2", "CHCHD10"],
        "female_run": "primary_Exc_L4_5_RORB_IL1RAPL2_F_e2_AD_up_mito",
        "male_run": "primary_Exc_L4_5_RORB_IL1RAPL2_M_e2_AD_down_mito",
    },
    {
        "row": "GABARAPL2 | Exc L4-5 RORB IL1RAPL2",
        "driver": "GABARAPL2",
        "network": "Excitatory_neurons",
        "fine_cell_type": "Exc L4-5 RORB IL1RAPL2",
        "max_layer": 3,
        "labels": {
            "GABARAPL2", "CHCHD2", "MAGEF1", "SNAPC5", "PARK7", "NDUFA4",
            "ATP5MC3", "MRPL18", "MRPL27", "BAX", "ARF5",
        },
        "targets": ["CHCHD2", "PARK7", "ATP5MC3"],
        "female_run": "primary_Exc_L4_5_RORB_IL1RAPL2_F_e2_AD_up_mito",
        "male_run": "primary_Exc_L4_5_RORB_IL1RAPL2_M_e2_AD_down_mito",
    },
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def open_text(path: Path):
    return gzip.open(path, "rt", newline="") if path.suffix == ".gz" else path.open("r", newline="")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required file does not exist: {path}")
    with open_text(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_tsv(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Required file does not exist: {path}")
    with open_text(path) as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def write_tsv(rows: Sequence[Mapping[str, object]], path: Path, fieldnames: Sequence[str] | None = None) -> None:
    ensure_parent(path)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["schema_version"]
    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
    ) as handle:
        tmp = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _format_value(row.get(key, "")) for key in fieldnames})
    os.replace(tmp, path)


def _format_value(value: object) -> object:
    if value is None:
        return "NA"
    if isinstance(value, float) and math.isnan(value):
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def parse_bool(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES"}


def parse_float(value: object, default: float = math.nan) -> float:
    try:
        if value in (None, "", "NA"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: object, default: int = 0) -> int:
    try:
        if value in (None, "", "NA"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _acat_statistic(p_value: float) -> float:
    if p_value < 1e-15:
        return 1.0 / (p_value * math.pi)
    return math.tan((0.5 - p_value) * math.pi)


def acat_combine_netweaver(
    p_values: Sequence[float | None],
    *,
    na_action: str = "na.to1",
    tolerance: float = 1e-300,
) -> float:
    """Combine p-values with the edge-case behavior used by NetWeaver ACAT."""
    if na_action not in {"na.omit", "na.to1"}:
        raise ValueError(f"Unsupported ACAT missing-value action: {na_action}")
    values = np.asarray(
        [math.nan if value is None else float(value) for value in p_values],
        dtype=float,
    )
    if np.any(np.isinf(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError("ACAT input p-values must be finite values in [0, 1] or missing")
    if na_action == "na.omit":
        values = values[~np.isnan(values)]
    else:
        values[np.isnan(values)] = 1.0
    if values.size == 0:
        return math.nan
    if np.all(values == 1):
        return 1.0
    if np.any(values == 0):
        positive = values[values > 0]
        replacement = min(float(np.min(positive)), tolerance) if positive.size else tolerance
        values[values == 0] = replacement
    if np.any(values == 1):
        values[values == 1] = float(np.max(values[values < 1])) / 2.0 + 0.5
    statistics = np.asarray([_acat_statistic(float(value)) for value in values])
    return float(cauchy.sf(float(np.mean(statistics))))


def validate_acat_example() -> float:
    observed = [acat_combine_netweaver(row) for row in ACAT_EXAMPLE]
    return max(abs(value - expected) for value, expected in zip(observed, ACAT_EXAMPLE_EXPECTED))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_artifacts() -> list[dict[str, str]]:
    return read_tsv(PHASE12_DIR / "kda_artifacts.tsv")


def artifact_path(row: Mapping[str, str]) -> Path:
    path = Path(row["path"])
    return path if path.is_absolute() else PROJECT_ROOT / path


def validate_phase12_bundle(check_hashes: bool = True) -> list[dict[str, str]]:
    status = read_tsv(PHASE12_DIR / "kda_status.tsv")
    checks = read_tsv(PHASE12_DIR / "kda_checks.tsv")
    if len(status) != 1 or status[0].get("validation_status") != "validated_complete":
        raise RuntimeError("The network figures require the validated_complete Phase 12 bundle")
    failed = [row["check_id"] for row in checks if not parse_bool(row.get("passed"))]
    if failed:
        raise RuntimeError(f"Phase 12 checks failed: {', '.join(failed)}")
    figure_checks_path = FIGURE_DATA_DIR / "phase12_kda_figure_data_checks.tsv"
    if figure_checks_path.is_file():
        figure_checks = read_tsv(figure_checks_path)
        failed_figure = [row["check_id"] for row in figure_checks if not parse_bool(row.get("passed"))]
        if failed_figure:
            raise RuntimeError(f"Existing Phase 12 figure-data checks failed: {', '.join(failed_figure)}")
    artifacts = load_artifacts()
    if check_hashes:
        required_outputs = {
            "kda_run_manifest.tsv",
            "kda_background_members.tsv.gz",
            "kda_signature_members.tsv.gz",
            "kda_results.tsv.gz",
        }
        for row in artifacts:
            path = artifact_path(row)
            role = row.get("artifact_role", "")
            if role.startswith("network_") or (role == "phase12_output" and path.name in required_outputs):
                if not path.is_file():
                    raise FileNotFoundError(f"Artifact is missing: {path}")
                observed = sha256_file(path)
                if observed != row["sha256"]:
                    raise RuntimeError(f"Artifact hash mismatch: {path}")
    return artifacts


def network_paths_from_artifacts(artifacts: Sequence[Mapping[str, str]]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for row in artifacts:
        role = row.get("artifact_role", "")
        if role.startswith("network_"):
            paths[role.removeprefix("network_")] = artifact_path(row)
    return paths


def load_networks(
    artifacts: Sequence[Mapping[str, str]] | None = None,
    network_names: Iterable[str] | None = None,
) -> dict[str, nx.DiGraph]:
    artifacts = list(artifacts) if artifacts is not None else load_artifacts()
    paths = network_paths_from_artifacts(artifacts)
    requested = list(network_names) if network_names is not None else sorted(paths)
    graphs: dict[str, nx.DiGraph] = {}
    for network in requested:
        path = paths.get(network)
        if path is None or not path.is_file():
            raise FileNotFoundError(f"Missing network edge list for {network}")
        graph = nx.DiGraph()
        with path.open() as handle:
            for line_number, line in enumerate(handle, start=1):
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    raise RuntimeError(f"Malformed edge on line {line_number} of {path}")
                source, target = parts[:2]
                if source and target and source != target:
                    graph.add_edge(source, target)
        if not graph.number_of_edges() or not nx.is_directed_acyclic_graph(graph):
            raise RuntimeError(f"Network is empty or not a DAG: {network}")
        graphs[network] = graph
    return graphs


def degree_records(graphs: Mapping[str, nx.DiGraph]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for network, graph in graphs.items():
        totals = sorted(dict(graph.degree()).values())
        node_count = len(totals)
        for gene in sorted(graph.nodes):
            total = graph.degree(gene)
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "broad_network": network,
                    "gene": gene,
                    "in_degree": graph.in_degree(gene),
                    "out_degree": graph.out_degree(gene),
                    "total_degree": total,
                    "degree_percentile": bisect_right(totals, total) / node_count,
                    "network_nodes": graph.number_of_nodes(),
                    "network_edges": graph.number_of_edges(),
                }
            )
    return rows


def degree_lookup(rows: Sequence[Mapping[str, object]]) -> dict[tuple[str, str], Mapping[str, object]]:
    return {(str(row["broad_network"]), str(row["gene"])): row for row in rows}


def load_complex_v_genes() -> set[str]:
    genes: set[str] = set()
    path = ANNOTATION_DIR / "mitocarta_pathways.tsv"
    for row in iter_tsv(path):
        if row["pathway"] in {"CV subunits", "CV assembly factors"}:
            genes.update(gene.strip() for gene in row["genes"].split(",") if gene.strip())
    if len(genes) != 26:
        raise RuntimeError(f"Expected 26 MitoCarta Complex V genes, observed {len(genes)}")
    return genes


def load_kda_results() -> list[dict[str, str]]:
    return read_tsv(PHASE12_DIR / "kda_results.tsv.gz")


def result_lookup(rows: Sequence[Mapping[str, str]]) -> dict[tuple[str, str], Mapping[str, str]]:
    lookup: dict[tuple[str, str], Mapping[str, str]] = {}
    for row in rows:
        key = (row["kda_run_id"], row["key_driver"])
        if key in lookup:
            raise RuntimeError(f"Duplicate KDA result row: {key}")
        lookup[key] = row
    return lookup


def load_run_members(path: Path, run_ids: Iterable[str]) -> dict[str, set[str]]:
    requested = set(run_ids)
    members = {run_id: set() for run_id in requested}
    for row in iter_tsv(path):
        run_id = row["kda_run_id"]
        if run_id in requested:
            if "effective_member" not in row or parse_bool(row.get("effective_member")):
                members[run_id].add(row["gene"])
    missing = [run_id for run_id, genes in members.items() if not genes]
    if missing:
        raise RuntimeError(f"No run members found for: {', '.join(sorted(missing))}")
    return members


def downstream_nodes(graph: nx.DiGraph, driver: str, layers: int) -> tuple[set[str], dict[str, int]]:
    if driver not in graph:
        raise RuntimeError(f"Driver {driver} is absent from the induced graph")
    distances = dict(nx.single_source_shortest_path_length(graph, driver, cutoff=layers))
    return set(distances), distances


def lexicographic_shortest_path(graph: nx.DiGraph, source: str, target: str) -> list[str]:
    if source not in graph or target not in graph or not nx.has_path(graph, source, target):
        raise RuntimeError(f"No directed path from {source} to {target}")
    return min(tuple(path) for path in nx.all_shortest_paths(graph, source, target))


def path_edges(path: Sequence[str]) -> set[tuple[str, str]]:
    return set(zip(path[:-1], path[1:]))


def reconstruct_run_neighborhood(
    result_row: Mapping[str, str],
    full_graph: nx.DiGraph,
    backgrounds: Mapping[str, set[str]],
) -> dict[str, object]:
    run_id = result_row["kda_run_id"]
    driver = result_row["key_driver"]
    best_layer = parse_int(result_row["best_layer"])
    background = backgrounds[run_id]
    induced = full_graph.subgraph(background).copy()
    nodes, distances = downstream_nodes(induced, driver, best_layer)
    expected = parse_int(result_row["neighborhood_size"])
    if len(nodes) != expected:
        raise RuntimeError(
            f"Neighborhood-size mismatch for {run_id}/{driver}: reconstructed {len(nodes)}, expected {expected}"
        )
    overlap = {gene for gene in result_row.get("overlap_items", "").split(";") if gene}
    if not overlap.issubset(nodes):
        raise RuntimeError(f"Overlap genes fall outside reconstructed neighborhood for {run_id}/{driver}")
    return {
        "run_id": run_id,
        "driver": driver,
        "best_layer": best_layer,
        "background": background,
        "induced_graph": induced,
        "nodes": nodes,
        "distances": distances,
        "subgraph": induced.subgraph(nodes).copy(),
        "overlap": overlap,
    }


def load_de_for_contexts(
    context_genes: Mapping[tuple[str, str, str], set[str]],
) -> dict[tuple[str, str, str, str], dict[str, object]]:
    results: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for path in sorted(PHASE08_DIR.glob("*.yu_mast_de.tsv.gz")):
        for row in iter_tsv(path):
            if row.get("contrast_family") != "AD_vs_NCI":
                continue
            context = (row["cell_type_high_resolution"], row["sex"], row["apoe_group"])
            genes = context_genes.get(context)
            if genes is None or row["gene"] not in genes:
                continue
            key = (*context, row["gene"])
            value = {
                "logFC": parse_float(row.get("logFC")),
                "fdr_bh_within_contrast": parse_float(row.get("fdr_bh_within_contrast")),
                "paper_deg": parse_bool(row.get("paper_deg")),
                "donors_ad": parse_int(row.get("donors_ad")),
                "donors_nci": parse_int(row.get("donors_nci")),
                "contrast_id": row.get("contrast_id", ""),
            }
            if key in results and results[key] != value:
                raise RuntimeError(f"Conflicting Phase 08 DEG rows for {key}")
            results[key] = value
    return results


def node_area(total_degree: int) -> float:
    """Return marker area with diameter linearly scaled to full-network degree.

    Wang et al. Figure 6 describes node size as proportional to link degree.
    NetworkX/Matplotlib accepts marker area in points squared, so square the
    linearly scaled diameter after applying a legibility floor and upper cap.
    """
    diameter = min(
        NODE_DIAMETER_CAP,
        NODE_DIAMETER_BASE + NODE_DIAMETER_PER_DEGREE * max(total_degree, 0),
    )
    return diameter**2


def key_driver_node_area(total_degree: int) -> float:
    """Return the consistently enlarged Wang-style area for a key driver."""
    return KEY_DRIVER_AREA_MULTIPLIER * node_area(total_degree)


def node_ring_area(total_degree: int, diameter_padding: float) -> float:
    diameter = math.sqrt(node_area(total_degree))
    return (diameter + diameter_padding) ** 2


def centered_offsets(count: int) -> list[float]:
    values: list[float] = []
    step = 0
    while len(values) < count:
        if step == 0:
            values.append(0.0)
        else:
            values.append(float(step))
            if len(values) < count:
                values.append(float(-step))
        step += 1
    scale = max(1.0, max(abs(value) for value in values))
    return [0.92 * value / scale for value in values]


def hierarchical_layout(
    graph: nx.DiGraph,
    driver: str,
    priority_genes: Iterable[str] = (),
    distances: Mapping[str, int] | None = None,
) -> dict[str, tuple[float, float]]:
    priority = set(priority_genes)
    if distances is None:
        distances = nx.single_source_shortest_path_length(graph, driver)
    max_layer = max(distances.values()) if distances else 1
    layers: dict[int, list[str]] = defaultdict(list)
    for node in graph.nodes:
        layers[int(distances.get(node, max_layer))].append(node)
    positions: dict[str, tuple[float, float]] = {}
    for layer in sorted(layers):
        nodes = sorted(layers[layer], key=lambda gene: (gene not in priority, gene))
        offsets = centered_offsets(len(nodes))
        for index, (gene, y_value) in enumerate(zip(nodes, offsets)):
            x_value = -0.9 + 1.8 * layer / max(1, max_layer)
            if len(nodes) > 12 and layer > 0:
                x_value += 0.025 * ((index % 3) - 1)
            positions[gene] = (x_value, y_value)
    positions[driver] = (-0.9, 0.0)
    return positions


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 8,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def save_figure(fig: plt.Figure, basename: Path, formats: Sequence[str] = ("pdf", "svg", "png")) -> list[Path]:
    ensure_parent(basename)
    outputs: list[Path] = []
    for fmt in formats:
        output = basename.with_suffix(f".{fmt}")
        ensure_parent(output)
        with tempfile.NamedTemporaryFile(
            suffix=f".{fmt}",
            delete=False,
            dir=output.parent,
            prefix=f".{output.stem}.",
        ) as handle:
            tmp = Path(handle.name)
        kwargs = {"bbox_inches": "tight"}
        if fmt == "png":
            kwargs["dpi"] = 300
        fig.savefig(tmp, format=fmt, **kwargs)
        if not tmp.is_file() or tmp.stat().st_size == 0:
            raise RuntimeError(f"Renderer produced an empty file: {output}")
        os.replace(tmp, output)
        outputs.append(output)
    return outputs


def update_generation_log(output_dir: Path, paths: Iterable[Path], role: str) -> None:
    log_path = output_dir / "phase12_kda_network_figures_generation_log.tsv"
    rows = (
        [
            row
            for row in read_tsv(log_path)
            if (PROJECT_ROOT / row["path"]).is_file()
        ]
        if log_path.is_file()
        else []
    )
    by_path = {row["path"]: row for row in rows}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for path in paths:
        relative = str(path.relative_to(PROJECT_ROOT))
        by_path[relative] = {
            "schema_version": SCHEMA_VERSION,
            "artifact_role": role,
            "path": relative,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "timestamp_utc": timestamp,
        }
    ordered = [by_path[key] for key in sorted(by_path)]
    write_tsv(
        ordered,
        log_path,
        ["schema_version", "artifact_role", "path", "sha256", "bytes", "timestamp_utc"],
    )


def build_convergence_pairs(
    kda_rows: Sequence[Mapping[str, str]],
    complex_v: set[str],
    graphs: Mapping[str, nx.DiGraph],
    degrees: Mapping[tuple[str, str], Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in kda_rows:
        if row["analysis_tier"] != "primary" or row["signature_direction"] not in {
            "AD_up_mito",
            "AD_down_mito",
        }:
            continue
        driver = row["key_driver"]
        overlap = {gene for gene in row.get("overlap_items", "").split(";") if gene}
        if (
            driver.startswith("MT-")
            or driver in overlap
            or parse_int(row["overlap_count"]) < 2
            or parse_int(row["signature_size"]) < 10
        ):
            continue
        network = row["broad_network"]
        for target in sorted((overlap & complex_v) - {driver}):
            key = (network, driver, target)
            record = grouped.setdefault(
                key,
                {
                    "run_ids": set(),
                    "fine_cell_types": set(),
                    "up_runs": 0,
                    "down_runs": 0,
                },
            )
            if row["kda_run_id"] not in record["run_ids"]:
                record["run_ids"].add(row["kda_run_id"])
                record["fine_cell_types"].add(row["fine_cell_type"])
                if row["signature_direction"] == "AD_up_mito":
                    record["up_runs"] += 1
                else:
                    record["down_runs"] += 1
    rows: list[dict[str, object]] = []
    for (network, driver, target), record in sorted(grouped.items()):
        graph = graphs[network]
        path = lexicographic_shortest_path(graph, driver, target)
        distance = len(path) - 1
        if distance > 3:
            raise RuntimeError(f"Complex V overlap path exceeds three layers: {network}/{driver}/{target}")
        degree = degrees[(network, driver)]
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "broad_network": network,
                "driver": driver,
                "complex_v_target": target,
                "qualifying_calls": len(record["run_ids"]),
                "ad_up_calls": record["up_runs"],
                "ad_down_calls": record["down_runs"],
                "fine_cell_types": len(record["fine_cell_types"]),
                "shortest_path_distance": distance,
                "shortest_path": ";".join(path),
                "driver_in_degree": degree["in_degree"],
                "driver_out_degree": degree["out_degree"],
                "driver_total_degree": degree["total_degree"],
                "driver_degree_percentile": degree["degree_percentile"],
                "run_ids": ";".join(sorted(record["run_ids"])),
            }
        )
    return rows


def build_acat_candidate_summary() -> list[dict[str, object]]:
    """Aggregate complete primary-directional raw p-values using ACAT."""
    example_error = validate_acat_example()
    if example_error > 5e-10:
        raise RuntimeError(
            f"NetWeaver-compatible ACAT failed the professor example: error={example_error:.3g}"
        )

    candidate_path = FIGURE_DATA_DIR / "phase12_kda_primary_directional_candidate_tests.tsv.gz"
    run_ids: dict[str, set[str]] = defaultdict(set)
    accumulators: dict[tuple[str, str], dict[str, object]] = {}

    for row in iter_tsv(candidate_path):
        if (
            row["analysis_tier"] != "primary"
            or row["signature_direction"] not in {"AD_up_mito", "AD_down_mito"}
            or not parse_bool(row["ranking_candidate"])
        ):
            continue
        network = row["broad_network"]
        if network not in NETWORK_ORDER:
            continue
        run_ids[network].add(row["kda_run_id"])
        key = (network, row["key_driver"])
        record = accumulators.setdefault(
            key,
            {
                "ranking_runs": 0,
                "significant_runs": 0,
                "zero_p_values": 0,
                "one_p_values": 0,
                "nonzero_below_one": 0,
                "sum_statistics": 0.0,
                "minimum_positive": math.inf,
                "maximum_below_one": -math.inf,
            },
        )

        raw_p = parse_float(row["raw_p_value"])
        if math.isfinite(raw_p):
            if raw_p < 0 or raw_p > 1:
                raise RuntimeError(f"Candidate raw p-value is outside [0, 1]: {key}/{raw_p}")
            record["ranking_runs"] = parse_int(record["ranking_runs"]) + 1
            if raw_p == 0:
                record["zero_p_values"] = parse_int(record["zero_p_values"]) + 1
            elif raw_p == 1:
                record["one_p_values"] = parse_int(record["one_p_values"]) + 1
                record["minimum_positive"] = min(parse_float(record["minimum_positive"]), raw_p)
            else:
                record["nonzero_below_one"] = parse_int(record["nonzero_below_one"]) + 1
                record["sum_statistics"] = parse_float(record["sum_statistics"]) + _acat_statistic(raw_p)
                record["minimum_positive"] = min(parse_float(record["minimum_positive"]), raw_p)
                record["maximum_below_one"] = max(parse_float(record["maximum_below_one"]), raw_p)

        adjusted_p = parse_float(row["adjusted_p_value"])
        if math.isfinite(adjusted_p) and adjusted_p <= 0.05:
            record["significant_runs"] = parse_int(record["significant_runs"]) + 1

    missing_networks = [network for network in NETWORK_ORDER if not run_ids[network]]
    if missing_networks:
        raise RuntimeError(f"No primary-directional ACAT runs for: {', '.join(missing_networks)}")

    rows: list[dict[str, object]] = []
    for (network, key_driver), record in accumulators.items():
        tested_runs = parse_int(record["ranking_runs"])
        if tested_runs < 1:
            continue
        eligible_runs = len(run_ids[network])
        if tested_runs > eligible_runs:
            raise RuntimeError(f"Candidate has more tests than eligible runs: {network}/{key_driver}")

        zero_count = parse_int(record["zero_p_values"])
        below_one_count = parse_int(record["nonzero_below_one"])
        missing_or_one_count = eligible_runs - tested_runs + parse_int(record["one_p_values"])
        if zero_count == 0 and below_one_count == 0:
            combined_p = 1.0
        else:
            statistic_sum = parse_float(record["sum_statistics"])
            maximum_below_one = parse_float(record["maximum_below_one"])
            if zero_count:
                minimum_positive = parse_float(record["minimum_positive"])
                zero_replacement = min(minimum_positive, 1e-300) if math.isfinite(minimum_positive) else 1e-300
                statistic_sum += zero_count * _acat_statistic(zero_replacement)
                maximum_below_one = max(maximum_below_one, zero_replacement)
            if missing_or_one_count:
                one_replacement = maximum_below_one / 2.0 + 0.5
                statistic_sum += missing_or_one_count * _acat_statistic(one_replacement)
            combined_p = float(cauchy.sf(statistic_sum / eligible_runs))

        if not math.isfinite(combined_p) or combined_p < 0 or combined_p > 1:
            raise RuntimeError(f"ACAT produced an invalid p-value: {network}/{key_driver}")
        significant_runs = parse_int(record["significant_runs"])
        rows.append(
            {
                "broad_network": network,
                "key_driver": key_driver,
                "acat_combined_p": combined_p,
                "acat_negative_log10_p": -math.log10(max(combined_p, np.finfo(float).tiny)),
                "ranking_runs": tested_runs,
                "eligible_directional_runs": eligible_runs,
                "ranking_coverage_fraction": tested_runs / eligible_runs,
                "primary_directional_significant_runs": significant_runs,
                "primary_directional_recurrence_fraction": significant_runs / tested_runs,
                "acat_input_p_value": "raw_p_value",
                "acat_na_action": "na.to1",
                "mtDNA_encoded": key_driver.startswith("MT-"),
            }
        )

    network_index = {network: index for index, network in enumerate(NETWORK_ORDER)}
    rows.sort(
        key=lambda row: (
            network_index[str(row["broad_network"])],
            parse_float(row["acat_combined_p"]),
            -parse_int(row["ranking_runs"]),
            -parse_float(row["primary_directional_recurrence_fraction"]),
            str(row["key_driver"]),
        )
    )
    return rows


def build_connectivity_points(
    degrees: Mapping[tuple[str, str], Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in build_acat_candidate_summary():
        key = (str(row["broad_network"]), str(row["key_driver"]))
        if key not in degrees:
            raise RuntimeError(f"ACAT candidate is absent from network: {key}")
        degree = degrees[key]
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                **row,
                "in_degree": degree["in_degree"],
                "out_degree": degree["out_degree"],
                "total_degree": degree["total_degree"],
                "degree_percentile": degree["degree_percentile"],
                "node_size_area": node_area(parse_int(degree["total_degree"])),
            }
        )
    return rows


def prepare_common_data(output_dir: Path = DEFAULT_OUTPUT_DIR, check_hashes: bool = True) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = validate_phase12_bundle(check_hashes=check_hashes)
    graphs = load_networks(artifacts)
    degree_rows = degree_records(graphs)
    degrees = degree_lookup(degree_rows)
    complex_v = load_complex_v_genes()
    kda_rows = load_kda_results()
    pairs = build_convergence_pairs(kda_rows, complex_v, graphs, degrees)
    points = build_connectivity_points(degrees)

    selected_pairs = {
        ("Astrocytes", "APOE", "ATP5PB"): 2,
        ("Excitatory_neurons", "LAMTOR5", "ATP5IF1"): 12,
        ("Inhibitory_neurons", "LAMTOR5", "ATP5IF1"): 3,
        ("Excitatory_neurons", "GABARAPL2", "ATP5MC3"): 15,
        ("Inhibitory_neurons", "RPS15", "ATP5PF"): 6,
        ("OPCs", "FTL", "ATP5IF1"): 1,
    }
    pair_lookup = {
        (str(row["broad_network"]), str(row["driver"]), str(row["complex_v_target"])): int(row["qualifying_calls"])
        for row in pairs
    }
    pair_mismatches = sum(pair_lookup.get(key) != expected for key, expected in selected_pairs.items())

    selected_run_specs = {(spec["run_id"], spec["driver"]) for spec in WANG_PANEL_SPECS}
    for spec in SEX_REVERSAL_SPECS:
        selected_run_specs.add((spec["female_run"], spec["driver"]))
        selected_run_specs.add((spec["male_run"], spec["driver"]))
    run_ids = {run_id for run_id, _ in selected_run_specs}
    backgrounds = load_run_members(PHASE12_DIR / "kda_background_members.tsv.gz", run_ids)
    signatures = load_run_members(PHASE12_DIR / "kda_signature_members.tsv.gz", run_ids)
    kda_lookup = result_lookup(kda_rows)
    neighborhood_mismatches = 0
    overlap_signature_mismatches = 0
    for run_id, driver in sorted(selected_run_specs):
        row = kda_lookup[(run_id, driver)]
        try:
            record = reconstruct_run_neighborhood(row, graphs[row["broad_network"]], backgrounds)
        except RuntimeError:
            neighborhood_mismatches += 1
            continue
        if not record["overlap"].issubset(signatures[run_id]):
            overlap_signature_mismatches += 1

    degree_path = output_dir / "phase12_kda_network_degrees.tsv"
    complex_path = output_dir / "phase12_kda_complex_v_genes.tsv"
    pair_path = output_dir / "phase12_kda_atp_convergence_pairs.tsv"
    point_path = output_dir / "phase12_kda_connectivity_evidence_points.tsv"
    checks_path = output_dir / "phase12_kda_network_data_checks.tsv"

    write_tsv(degree_rows, degree_path)
    write_tsv(
        [{"schema_version": SCHEMA_VERSION, "gene": gene} for gene in sorted(complex_v)],
        complex_path,
        ["schema_version", "gene"],
    )
    write_tsv(pairs, pair_path)
    write_tsv(points, point_path)
    check_rows = [
        {"schema_version": SCHEMA_VERSION, "check_id": "validated_phase12_bundle", "passed": True, "observed": 1, "expected": 1},
        {"schema_version": SCHEMA_VERSION, "check_id": "bayesian_networks_are_dags", "passed": all(nx.is_directed_acyclic_graph(g) for g in graphs.values()), "observed": sum(nx.is_directed_acyclic_graph(g) for g in graphs.values()), "expected": len(graphs)},
        {"schema_version": SCHEMA_VERSION, "check_id": "complex_v_gene_count", "passed": len(complex_v) == 26, "observed": len(complex_v), "expected": 26},
        {"schema_version": SCHEMA_VERSION, "check_id": "selected_atp_pair_counts", "passed": pair_mismatches == 0, "observed": pair_mismatches, "expected": 0},
        {"schema_version": SCHEMA_VERSION, "check_id": "selected_neighborhood_sizes", "passed": neighborhood_mismatches == 0, "observed": neighborhood_mismatches, "expected": 0},
        {"schema_version": SCHEMA_VERSION, "check_id": "overlap_genes_in_effective_signatures", "passed": overlap_signature_mismatches == 0, "observed": overlap_signature_mismatches, "expected": 0},
        {"schema_version": SCHEMA_VERSION, "check_id": "connectivity_points_present", "passed": len(points) > 0, "observed": len(points), "expected": ">0"},
    ]
    write_tsv(check_rows, checks_path)
    failed = [row["check_id"] for row in check_rows if not row["passed"]]
    if failed:
        raise RuntimeError(f"Network figure data checks failed: {', '.join(failed)}")
    outputs = [degree_path, complex_path, pair_path, point_path, checks_path]
    update_generation_log(output_dir, outputs, "prepared_data")
    return outputs


def load_prepared_degrees(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[tuple[str, str], dict[str, object]]:
    path = output_dir / "phase12_kda_network_degrees.tsv"
    if not path.is_file():
        prepare_common_data(output_dir)
    rows: list[dict[str, object]] = []
    for row in read_tsv(path):
        rows.append(
            {
                **row,
                "in_degree": parse_int(row["in_degree"]),
                "out_degree": parse_int(row["out_degree"]),
                "total_degree": parse_int(row["total_degree"]),
                "degree_percentile": parse_float(row["degree_percentile"]),
            }
        )
    return degree_lookup(rows)  # type: ignore[arg-type]


def load_prepared_complex_v(output_dir: Path = DEFAULT_OUTPUT_DIR) -> set[str]:
    path = output_dir / "phase12_kda_complex_v_genes.tsv"
    if not path.is_file():
        prepare_common_data(output_dir)
    return {row["gene"] for row in read_tsv(path)}


def selected_result_bundle(
    specs: Sequence[Mapping[str, object]],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    check_hashes: bool = True,
) -> tuple[
    list[dict[str, str]],
    dict[tuple[str, str], Mapping[str, str]],
    dict[str, nx.DiGraph],
    dict[str, set[str]],
    dict[tuple[str, str], dict[str, object]],
    set[str],
]:
    if not (output_dir / "phase12_kda_network_data_checks.tsv").is_file():
        prepare_common_data(output_dir, check_hashes=check_hashes)
    artifacts = validate_phase12_bundle(check_hashes=check_hashes)
    kda_rows = load_kda_results()
    lookup = result_lookup(kda_rows)
    networks = {str(spec["network"]) for spec in specs}
    graphs = load_networks(artifacts, networks)
    run_ids: set[str] = set()
    for spec in specs:
        if "run_id" in spec:
            run_ids.add(str(spec["run_id"]))
        else:
            run_ids.update({str(spec["female_run"]), str(spec["male_run"])})
    backgrounds = load_run_members(PHASE12_DIR / "kda_background_members.tsv.gz", run_ids)
    return kda_rows, lookup, graphs, backgrounds, load_prepared_degrees(output_dir), load_prepared_complex_v(output_dir)


def expression_color(logfc: float) -> object:
    return "#FFFFFF" if math.isnan(logfc) else EXPRESSION_CMAP(EXPRESSION_NORM(np.clip(logfc, -1.5, 1.5)))


def metadata_line(result: Mapping[str, str]) -> str:
    return (
        f"L={parse_int(result['best_layer'])} | n={parse_int(result['neighborhood_size'])} | "
        f"overlap={parse_int(result['overlap_count'])} | FE={parse_float(result['fold_enrichment']):.1f} | "
        f"q={parse_float(result['adjusted_p_value']):.2g}"
    )


def highlighted_paths(
    graph: nx.DiGraph,
    driver: str,
    targets: Iterable[str],
) -> tuple[set[tuple[str, str]], dict[str, str]]:
    edges: set[tuple[str, str]] = set()
    paths: dict[str, str] = {}
    for target in sorted(set(targets)):
        if target not in graph or not nx.has_path(graph, driver, target):
            continue
        path = lexicographic_shortest_path(graph, driver, target)
        edges.update(path_edges(path))
        paths[target] = ";".join(path)
    return edges, paths


def panel_node_rows(
    *,
    figure: str,
    panel: str,
    result: Mapping[str, str],
    record: Mapping[str, object],
    position: Mapping[str, tuple[float, float]],
    degrees: Mapping[tuple[str, str], Mapping[str, object]],
    complex_v: set[str],
    expression: Mapping[tuple[str, str, str, str], Mapping[str, object]],
    fine_cell_type: str,
    sex: str,
    apoe_group: str,
    candidate_genes: Iterable[str],
) -> list[dict[str, object]]:
    network = result["broad_network"]
    driver = result["key_driver"]
    overlap = set(record["overlap"])  # type: ignore[arg-type]
    distances = record["distances"]  # type: ignore[assignment]
    candidates = set(candidate_genes)
    rows: list[dict[str, object]] = []
    for gene in sorted(record["nodes"]):  # type: ignore[arg-type]
        degree = degrees[(network, gene)]
        de = expression.get((fine_cell_type, sex, apoe_group, gene), {})
        x_value, y_value = position[gene]
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "figure": figure,
                "panel": panel,
                "kda_run_id": result["kda_run_id"],
                "broad_network": network,
                "fine_cell_type": fine_cell_type,
                "sex": sex,
                "apoe_group": apoe_group,
                "driver": driver,
                "gene": gene,
                "layer": distances[gene],
                "x": x_value,
                "y": y_value,
                "in_degree": degree["in_degree"],
                "out_degree": degree["out_degree"],
                "total_degree": degree["total_degree"],
                "degree_percentile": degree["degree_percentile"],
                "node_size_area": node_area(parse_int(degree["total_degree"])),
                "logFC": de.get("logFC", math.nan),
                "fdr_bh_within_contrast": de.get("fdr_bh_within_contrast", math.nan),
                "paper_deg": de.get("paper_deg", False),
                "donors_ad": de.get("donors_ad", 0),
                "donors_nci": de.get("donors_nci", 0),
                "is_driver": gene == driver,
                "is_overlap": gene in overlap,
                "is_complex_v": gene in complex_v,
                "is_candidate": gene in candidates,
                "display_label": gene if gene in candidates or gene == driver else "",
            }
        )
    return rows


def panel_edge_rows(
    *,
    figure: str,
    panel: str,
    result: Mapping[str, str],
    graph: nx.DiGraph,
    highlight_edges: set[tuple[str, str]],
    active_edges: set[tuple[str, str]] | None = None,
) -> list[dict[str, object]]:
    active_edges = set(graph.edges) if active_edges is None else active_edges
    return [
        {
            "schema_version": SCHEMA_VERSION,
            "figure": figure,
            "panel": panel,
            "kda_run_id": result["kda_run_id"],
            "broad_network": result["broad_network"],
            "driver": result["key_driver"],
            "source": source,
            "target": target,
            "active_in_run": (source, target) in active_edges,
            "highlight_path": (source, target) in highlight_edges,
            "edge_style": "highlighted_path" if (source, target) in highlight_edges else "context",
            "line_width": 1.8 if (source, target) in highlight_edges else 0.7,
        }
        for source, target in sorted(graph.edges)
    ]


def draw_network_panel(
    ax: plt.Axes,
    graph: nx.DiGraph,
    position: Mapping[str, tuple[float, float]],
    rows: Sequence[Mapping[str, object]],
    highlight_edges: set[tuple[str, str]],
    labels: Iterable[str],
    title: str,
    subtitle: str,
    panel_letter: str | None = None,
    inactive_edges: set[tuple[str, str]] | None = None,
    inactive_nodes: set[str] | None = None,
) -> None:
    row_lookup = {str(row["gene"]): row for row in rows}
    inactive_edges = inactive_edges or set()
    inactive_nodes = inactive_nodes or set()
    base_edges = [edge for edge in graph.edges if edge not in highlight_edges]
    if base_edges:
        edge_colors = ["#D8D8D8" if edge not in inactive_edges else "#EEEEEE" for edge in base_edges]
        nx.draw_networkx_edges(
            graph,
            position,
            edgelist=base_edges,
            ax=ax,
            edge_color=edge_colors,
            width=0.7,
            alpha=0.65,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=8,
            node_size=0,
            min_source_margin=4,
            min_target_margin=5,
        )
    if highlight_edges:
        nx.draw_networkx_edges(
            graph,
            position,
            edgelist=sorted(highlight_edges),
            ax=ax,
            edge_color="#333333",
            width=1.8,
            alpha=0.95,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=10,
            node_size=0,
            min_source_margin=5,
            min_target_margin=6,
        )
    regular = [gene for gene in graph.nodes if not parse_bool(row_lookup[gene]["is_driver"])]
    drivers = [gene for gene in graph.nodes if parse_bool(row_lookup[gene]["is_driver"])]
    for genes, shape in ((regular, "o"), (drivers, "D")):
        if not genes:
            continue
        sizes = [
            key_driver_node_area(parse_int(row_lookup[gene]["total_degree"]))
            if shape == "D"
            else node_area(parse_int(row_lookup[gene]["total_degree"]))
            for gene in genes
        ]
        colors = ["#FAFAFA" if gene in inactive_nodes else expression_color(parse_float(row_lookup[gene]["logFC"])) for gene in genes]
        borders = ["#CCCCCC" if gene in inactive_nodes else "#303030" for gene in genes]
        nx.draw_networkx_nodes(
            graph,
            position,
            nodelist=genes,
            node_size=sizes,
            node_color=colors,
            node_shape=shape,
            edgecolors=borders,
            linewidths=0.65,
            ax=ax,
        )
    overlap_nodes = [gene for gene in graph.nodes if parse_bool(row_lookup[gene]["is_overlap"])]
    if overlap_nodes:
        nx.draw_networkx_nodes(
            graph,
            position,
            nodelist=overlap_nodes,
            node_size=[
                node_ring_area(parse_int(row_lookup[g]["total_degree"]), OVERLAP_RING_DIAMETER_PADDING)
                for g in overlap_nodes
            ],
            node_color="none",
            edgecolors="#111111",
            linewidths=1.65,
            ax=ax,
        )
    complex_nodes = [gene for gene in graph.nodes if parse_bool(row_lookup[gene]["is_complex_v"])]
    if complex_nodes:
        nx.draw_networkx_nodes(
            graph,
            position,
            nodelist=complex_nodes,
            node_size=[
                node_ring_area(parse_int(row_lookup[g]["total_degree"]), COMPLEX_V_RING_DIAMETER_PADDING)
                for g in complex_nodes
            ],
            node_color="none",
            edgecolors=COMPLEX_V_COLOR,
            linewidths=2.0,
            ax=ax,
        )
    label_set = set(labels) | set(drivers)
    for gene in sorted(label_set & set(graph.nodes)):
        x_value, y_value = position[gene]
        if gene in drivers or x_value < 0.25:
            text_offset = (0, 7)
            horizontal_alignment = "center"
            vertical_alignment = "bottom"
        else:
            text_offset = (7, ((sum(ord(char) for char in gene) % 3) - 1) * 4)
            horizontal_alignment = "left"
            vertical_alignment = "center"
        ax.annotate(
            gene,
            (x_value, y_value),
            xytext=text_offset,
            textcoords="offset points",
            ha=horizontal_alignment,
            va=vertical_alignment,
            fontsize=6.6,
            fontweight="bold" if gene in drivers else "normal",
            color="#111111",
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
            zorder=10,
        )
    ax.set_title(title, loc="left", fontweight="bold", y=1.07, pad=2)
    ax.text(0.0, 1.005, subtitle, transform=ax.transAxes, ha="left", va="bottom", fontsize=7.2, color="#444444")
    if panel_letter:
        ax.text(-0.04, 1.13, panel_letter, transform=ax.transAxes, ha="left", va="top", fontsize=14, fontweight="bold")
    ax.set_xlim(-1.12, 1.13)
    ax.set_ylim(-1.2, 1.18)
    ax.axis("off")


def add_network_legend(ax: plt.Axes) -> None:
    ax.axis("off")
    ax.text(0.0, 0.98, "Visual encodings", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    handles = [
        Line2D([0], [0], marker="D", color="none", markerfacecolor="#F2F2F2", markeredgecolor="#303030", markersize=8, label="Key driver"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#F2F2F2", markeredgecolor="#111111", markeredgewidth=1.8, markersize=8, label="KDA overlap gene"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#F2F2F2", markeredgecolor=COMPLEX_V_COLOR, markeredgewidth=2.0, markersize=9, label="ATP synthase / Complex V"),
        Line2D([0, 1], [0, 0], color="#333333", linewidth=1.8, label="Highlighted directed path"),
        Line2D([0, 1], [0, 0], color="#D8D8D8", linewidth=0.8, label="Other directed edge"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.82), frameon=False, handlelength=2.7, labelspacing=1.0)
    ax.text(
        0.48,
        0.82,
        "Node fill: AD vs NCI logFC\nblue = lower in AD; orange = higher in AD\nwhite = unavailable\n\nNode diameter: full-network total degree (linear)\n\nBlack outer ring: gene is in the KDA overlap\nPurple outer ring: MitoCarta Complex V gene",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        linespacing=1.45,
    )
    ax.text(
        0.0,
        0.08,
        "Together, the selected candidate systems connect\nmitochondrial translation and stress-control genes\nto ATP-synthase components.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.2,
        fontweight="bold",
        color="#333333",
        linespacing=1.35,
    )


def generate_wang_subnetworks(output_dir: Path = DEFAULT_OUTPUT_DIR, check_hashes: bool = True) -> list[Path]:
    configure_matplotlib()
    _, lookup, graphs, backgrounds, degrees, complex_v = selected_result_bundle(
        WANG_PANEL_SPECS, output_dir, check_hashes
    )
    records: list[tuple[Mapping[str, object], Mapping[str, str], dict[str, object]]] = []
    contexts: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for spec in WANG_PANEL_SPECS:
        result = lookup[(str(spec["run_id"]), str(spec["driver"]))]
        record = reconstruct_run_neighborhood(result, graphs[str(spec["network"])], backgrounds)
        records.append((spec, result, record))
        contexts[(str(spec["fine_cell_type"]), str(spec["sex"]), str(spec["apoe_group"]))].update(record["nodes"])  # type: ignore[arg-type]
    expression = load_de_for_contexts(contexts)

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 9.2), constrained_layout=True)
    all_nodes: list[dict[str, object]] = []
    all_edges: list[dict[str, object]] = []
    all_paths: list[dict[str, object]] = []
    for ax, (spec, result, record) in zip(axes.flat[:3], records):
        subgraph = record["subgraph"]
        position = hierarchical_layout(subgraph, str(spec["driver"]), spec["labels"], record["distances"])
        highlight, paths = highlighted_paths(subgraph, str(spec["driver"]), spec["targets"])
        node_rows = panel_node_rows(
            figure="wang_subnetworks",
            panel=str(spec["panel"]),
            result=result,
            record=record,
            position=position,
            degrees=degrees,
            complex_v=complex_v,
            expression=expression,
            fine_cell_type=str(spec["fine_cell_type"]),
            sex=str(spec["sex"]),
            apoe_group=str(spec["apoe_group"]),
            candidate_genes=spec["labels"],
        )
        all_nodes.extend(node_rows)
        all_edges.extend(panel_edge_rows(figure="wang_subnetworks", panel=str(spec["panel"]), result=result, graph=subgraph, highlight_edges=highlight))
        for target, path in paths.items():
            all_paths.append({"schema_version": SCHEMA_VERSION, "panel": spec["panel"], "driver": spec["driver"], "target": target, "path": path})
        draw_network_panel(
            ax,
            subgraph,
            position,
            node_rows,
            highlight,
            spec["labels"],
            f"{spec['short_title']} neighborhood",
            f"{spec['fine_cell_type']} | {spec['sex']} | APOE {spec['apoe_group']} | AD-down mitochondrial signature\n{metadata_line(result)}",
            str(spec["panel"]),
        )
    add_network_legend(axes.flat[3])
    scalar = plt.cm.ScalarMappable(norm=EXPRESSION_NORM, cmap=EXPRESSION_CMAP)
    colorbar = fig.colorbar(scalar, ax=list(axes.flat[:3]), orientation="horizontal", shrink=0.54, aspect=35, pad=0.025)
    colorbar.set_label("AD vs NCI log fold-change (matched cell type, sex, and APOE group)")
    fig.suptitle("Directed KDA neighborhoods connect key drivers to mitochondrial and ATP-synthase genes", fontsize=15, fontweight="bold")
    basename = output_dir / "phase12_kda_wang_subnetworks"
    figure_paths = save_figure(fig, basename)
    plt.close(fig)
    node_path = output_dir / "phase12_kda_wang_subnetworks_nodes.tsv"
    edge_path = output_dir / "phase12_kda_wang_subnetworks_edges.tsv"
    path_path = output_dir / "phase12_kda_wang_subnetworks_paths.tsv"
    write_tsv(all_nodes, node_path)
    write_tsv(all_edges, edge_path)
    write_tsv(all_paths, path_path)
    outputs = figure_paths + [node_path, edge_path, path_path]
    update_generation_log(output_dir, outputs, "figure_1_wang_subnetworks")
    return outputs


def generate_sex_reversal_networks(output_dir: Path = DEFAULT_OUTPUT_DIR, check_hashes: bool = True) -> list[Path]:
    configure_matplotlib()
    _, lookup, graphs, backgrounds, degrees, complex_v = selected_result_bundle(
        SEX_REVERSAL_SPECS, output_dir, check_hashes
    )
    prepared: list[dict[str, object]] = []
    contexts: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for spec in SEX_REVERSAL_SPECS:
        female_result = lookup[(str(spec["female_run"]), str(spec["driver"]))]
        male_result = lookup[(str(spec["male_run"]), str(spec["driver"]))]
        graph = graphs[str(spec["network"])]
        female = reconstruct_run_neighborhood(female_result, graph, backgrounds)
        male = reconstruct_run_neighborhood(male_result, graph, backgrounds)
        union_nodes = set(female["nodes"]) | set(male["nodes"])
        union_graph = graph.subgraph(union_nodes).copy()
        union_distances = {
            gene: min(
                int(female["distances"].get(gene, 99)),  # type: ignore[union-attr]
                int(male["distances"].get(gene, 99)),  # type: ignore[union-attr]
            )
            for gene in union_nodes
        }
        if max(union_distances.values()) > int(spec["max_layer"]):
            raise RuntimeError(f"Aligned comparison exceeds requested depth for {spec['row']}")
        position = hierarchical_layout(union_graph, str(spec["driver"]), spec["labels"], union_distances)
        prepared.append(
            {
                "spec": spec,
                "female_result": female_result,
                "male_result": male_result,
                "female": female,
                "male": male,
                "union_nodes": union_nodes,
                "union_graph": union_graph,
                "union_distances": union_distances,
                "position": position,
            }
        )
        contexts[(str(spec["fine_cell_type"]), "Female", "e2")].update(union_nodes)
        contexts[(str(spec["fine_cell_type"]), "Male", "e2")].update(union_nodes)
    expression = load_de_for_contexts(contexts)

    fig, axes = plt.subplots(3, 2, figsize=(15.5, 15.2), constrained_layout=True)
    all_nodes: list[dict[str, object]] = []
    all_edges: list[dict[str, object]] = []
    all_paths: list[dict[str, object]] = []
    panel_index = 0
    for row_index, bundle in enumerate(prepared):
        spec = bundle["spec"]
        union_graph = bundle["union_graph"]
        union_nodes = bundle["union_nodes"]
        union_distances = bundle["union_distances"]
        position = bundle["position"]
        for column_index, (condition, sex, result_key, record_key) in enumerate(
            (("Female AD-up", "Female", "female_result", "female"), ("Male AD-down", "Male", "male_result", "male"))
        ):
            panel_index += 1
            panel = chr(64 + panel_index)
            result = bundle[result_key]
            record = bundle[record_key]
            active_graph = record["subgraph"]
            synthetic_record = {
                "nodes": union_nodes,
                "distances": union_distances,
                "overlap": record["overlap"],
            }
            node_rows = panel_node_rows(
                figure="sex_reversal_networks",
                panel=panel,
                result=result,
                record=synthetic_record,
                position=position,
                degrees=degrees,
                complex_v=complex_v,
                expression=expression,
                fine_cell_type=str(spec["fine_cell_type"]),
                sex=sex,
                apoe_group="e2",
                candidate_genes=spec["labels"],
            )
            active_nodes = set(record["nodes"])
            for row in node_rows:
                row["active_in_run"] = row["gene"] in active_nodes
                row["comparison_row"] = spec["row"]
                row["condition"] = condition
            active_edges = set(active_graph.edges)
            highlight, paths = highlighted_paths(active_graph, str(spec["driver"]), spec["targets"])
            edge_rows = panel_edge_rows(
                figure="sex_reversal_networks",
                panel=panel,
                result=result,
                graph=union_graph,
                highlight_edges=highlight,
                active_edges=active_edges,
            )
            for target, path in paths.items():
                all_paths.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "panel": panel,
                        "comparison_row": spec["row"],
                        "condition": condition,
                        "driver": spec["driver"],
                        "target": target,
                        "path": path,
                    }
                )
            draw_network_panel(
                axes[row_index, column_index],
                union_graph,
                position,
                node_rows,
                highlight,
                set(spec["labels"]) & active_nodes,
                f"{spec['row']} | {condition}",
                f"APOE e2 | {metadata_line(result)} | shared union layout",
                panel,
                inactive_edges=set(union_graph.edges) - active_edges,
                inactive_nodes=set(union_nodes) - active_nodes,
            )
            all_nodes.extend(node_rows)
            all_edges.extend(edge_rows)
    axes[0, 0].text(0.5, 1.18, "Female: AD-up mitochondrial signature", transform=axes[0, 0].transAxes, ha="center", fontsize=11, fontweight="bold")
    axes[0, 1].text(0.5, 1.18, "Male: AD-down mitochondrial signature", transform=axes[0, 1].transAxes, ha="center", fontsize=11, fontweight="bold")
    scalar = plt.cm.ScalarMappable(norm=EXPRESSION_NORM, cmap=EXPRESSION_CMAP)
    colorbar = fig.colorbar(scalar, ax=list(axes.flat), orientation="horizontal", shrink=0.45, aspect=42, pad=0.015)
    colorbar.set_label("AD vs NCI log fold-change within the displayed sex and APOE e2 group")
    fig.suptitle("Sex-reversed mitochondrial KDA signals retain shared driver-centered network structure", fontsize=15, fontweight="bold")
    fig.text(
        0.5,
        -0.005,
        "Columns use the same node coordinates within each row. Pale nodes/edges are absent from that condition's reconstructed KDA neighborhood; black/purple rings remain condition-specific.",
        ha="center",
        fontsize=7.5,
        color="#444444",
    )
    basename = output_dir / "phase12_kda_sex_reversal_networks"
    figure_paths = save_figure(fig, basename)
    plt.close(fig)
    node_path = output_dir / "phase12_kda_sex_reversal_networks_nodes.tsv"
    edge_path = output_dir / "phase12_kda_sex_reversal_networks_edges.tsv"
    path_path = output_dir / "phase12_kda_sex_reversal_networks_paths.tsv"
    write_tsv(all_nodes, node_path)
    write_tsv(all_edges, edge_path)
    write_tsv(all_paths, path_path)
    outputs = figure_paths + [node_path, edge_path, path_path]
    update_generation_log(output_dir, outputs, "figure_2_sex_reversal")
    return outputs


def _typed_convergence_rows(output_dir: Path) -> list[dict[str, object]]:
    path = output_dir / "phase12_kda_atp_convergence_pairs.tsv"
    if not path.is_file():
        prepare_common_data(output_dir)
    rows: list[dict[str, object]] = []
    for row in read_tsv(path):
        rows.append(
            {
                **row,
                "qualifying_calls": parse_int(row["qualifying_calls"]),
                "ad_up_calls": parse_int(row["ad_up_calls"]),
                "ad_down_calls": parse_int(row["ad_down_calls"]),
                "fine_cell_types": parse_int(row["fine_cell_types"]),
                "shortest_path_distance": parse_int(row["shortest_path_distance"]),
                "driver_total_degree": parse_int(row["driver_total_degree"]),
                "driver_degree_percentile": parse_float(row["driver_degree_percentile"]),
            }
        )
    return rows


def _network_abbreviation(network: str) -> str:
    return {
        "Astrocytes": "Ast",
        "Excitatory_neurons": "Exc",
        "Inhibitory_neurons": "Inh",
        "Microglia": "Mic",
        "OPCs": "OPC",
        "Oligodendrocytes": "Oli",
        "Vasculature_cells": "Vasc",
    }.get(network, network)


def draw_convergence_map(
    rows: Sequence[Mapping[str, object]],
    *,
    figsize: tuple[float, float],
    title: str,
) -> tuple[plt.Figure, list[dict[str, object]]]:
    driver_support = Counter()
    target_support = Counter()
    for row in rows:
        calls = parse_int(row["qualifying_calls"])
        driver_support[(str(row["broad_network"]), str(row["driver"]))] += calls
        target_support[str(row["complex_v_target"])] += calls
    driver_nodes = sorted(
        {(str(row["broad_network"]), str(row["driver"])) for row in rows},
        key=lambda item: (
            NETWORK_ORDER.index(item[0]) if item[0] in NETWORK_ORDER else 999,
            -driver_support[item],
            item[1],
        ),
    )
    targets = sorted(
        {str(row["complex_v_target"]) for row in rows},
        key=lambda target: (-target_support[target], target),
    )
    driver_positions = {
        node: y for node, y in zip(driver_nodes, np.linspace(0.96, 0.04, len(driver_nodes)))
    }
    target_positions = {
        target: y for target, y in zip(targets, np.linspace(0.91, 0.09, len(targets)))
    }
    fig, ax = plt.subplots(figsize=figsize)
    layout_rows: list[dict[str, object]] = []
    for row in sorted(rows, key=lambda item: (str(item["broad_network"]), str(item["driver"]), str(item["complex_v_target"]))):
        network = str(row["broad_network"])
        driver = str(row["driver"])
        target = str(row["complex_v_target"])
        y0 = driver_positions[(network, driver)]
        y1 = target_positions[target]
        calls = parse_int(row["qualifying_calls"])
        distance = parse_int(row["shortest_path_distance"])
        driver_total_degree = parse_int(row["driver_total_degree"])
        driver_area = key_driver_node_area(driver_total_degree)
        target_area = 80 + 20 * math.sqrt(target_support[target])
        line_style = {1: "-", 2: "--", 3: ":"}.get(distance, ":")
        arrow = FancyArrowPatch(
            (0.18, y0),
            (0.82, y1),
            transform=ax.transAxes,
            connectionstyle="arc3,rad=0.0",
            arrowstyle="-|>",
            mutation_scale=6.5,
            linewidth=0.55 + 0.43 * math.sqrt(calls),
            linestyle=line_style,
            color=NETWORK_COLORS.get(network, "#777777"),
            alpha=0.52,
            zorder=1,
        )
        ax.add_patch(arrow)
        layout_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "broad_network": network,
                "driver": driver,
                "complex_v_target": target,
                "driver_y": y0,
                "target_y": y1,
                "qualifying_calls": calls,
                "shortest_path_distance": distance,
                "driver_total_degree": driver_total_degree,
                "driver_node_size_area": driver_area,
                "target_supporting_calls": target_support[target],
                "target_node_size_area": target_area,
            }
        )
    for network, driver in driver_nodes:
        matching = [row for row in rows if row["broad_network"] == network and row["driver"] == driver]
        total_degrees = {parse_int(row["driver_total_degree"]) for row in matching}
        if len(total_degrees) != 1:
            raise RuntimeError(f"Inconsistent full-network degree for convergence driver: {network}/{driver}")
        total_degree = total_degrees.pop()
        y_value = driver_positions[(network, driver)]
        ax.scatter(
            [0.18],
            [y_value],
            transform=ax.transAxes,
            s=key_driver_node_area(total_degree),
            marker="o",
            facecolor=NETWORK_COLORS.get(network, "#777777"),
            edgecolor="#222222",
            linewidth=0.55,
            zorder=3,
        )
        ax.text(
            0.145,
            y_value,
            f"{driver} ({_network_abbreviation(network)})",
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=7.2 if len(driver_nodes) < 25 else 5.7,
        )
    for target in targets:
        y_value = target_positions[target]
        target_area = 80 + 20 * math.sqrt(target_support[target])
        ax.scatter(
            [0.82],
            [y_value],
            transform=ax.transAxes,
            s=target_area,
            marker="o",
            facecolor="#FFFFFF",
            edgecolor=COMPLEX_V_COLOR,
            linewidth=1.8,
            zorder=3,
        )
        ax.text(0.85, y_value, target, transform=ax.transAxes, ha="left", va="center", fontsize=7.5)
    ax.text(0.18, 1.015, "Key drivers", transform=ax.transAxes, ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.text(0.82, 1.015, "MitoCarta Complex V overlap genes", transform=ax.transAxes, ha="center", va="bottom", fontsize=10, fontweight="bold")
    network_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=NETWORK_COLORS[n], markeredgecolor="#222222", markersize=6, label=NETWORK_LABELS[n])
        for n in NETWORK_ORDER
        if any(str(row["broad_network"]) == n for row in rows)
    ]
    distance_handles = [
        Line2D([0, 1], [0, 0], color="#555555", linestyle=style, linewidth=1.2, label=f"Directed distance {distance}")
        for distance, style in ((1, "-"), (2, "--"), (3, ":"))
    ]
    legend1 = ax.legend(handles=network_handles, loc="lower left", bbox_to_anchor=(0.0, -0.11), ncol=min(4, len(network_handles)), frameon=False)
    ax.add_artist(legend1)
    ax.legend(handles=distance_handles, loc="lower right", bbox_to_anchor=(1.0, -0.11), ncol=3, frameon=False)
    ax.text(
        0.5,
        -0.03,
        "Edge width = qualifying primary directional KDA calls; driver size = Wang scale from full-network total degree; target area = total supporting calls",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.2,
        color="#444444",
    )
    ax.set_title(title, fontsize=14, fontweight="bold", pad=42)
    ax.axis("off")
    return fig, layout_rows


def generate_atp_convergence(output_dir: Path = DEFAULT_OUTPUT_DIR, check_hashes: bool = True) -> list[Path]:
    configure_matplotlib()
    validate_phase12_bundle(check_hashes=check_hashes)
    rows = _typed_convergence_rows(output_dir)
    focused = [row for row in rows if str(row["driver"]) in FOCUSED_ATP_DRIVERS]
    if len(focused) != 27 or len(rows) != 93:
        raise RuntimeError(f"Unexpected convergence-map sizes: focused={len(focused)}, complete={len(rows)}")
    fig, focused_layout = draw_convergence_map(
        focused,
        figsize=(13.5, 9.5),
        title="Recurrent KDA convergence on ATP synthase / Complex V genes",
    )
    basename = output_dir / "phase12_kda_atp_convergence"
    main_paths = save_figure(fig, basename)
    plt.close(fig)

    complete_fig, complete_layout = draw_convergence_map(
        rows,
        figsize=(16.0, 22.0),
        title="Complete primary directional KDA convergence on ATP synthase / Complex V genes",
    )
    complete_paths = save_figure(
        complete_fig,
        output_dir / "phase12_kda_atp_convergence_complete",
        formats=("pdf",),
    )
    plt.close(complete_fig)
    focused_layout_path = output_dir / "phase12_kda_atp_convergence_layout.tsv"
    complete_layout_path = output_dir / "phase12_kda_atp_convergence_complete_layout.tsv"
    write_tsv(focused_layout, focused_layout_path)
    write_tsv(complete_layout, complete_layout_path)
    outputs = main_paths + complete_paths + [focused_layout_path, complete_layout_path]
    update_generation_log(output_dir, outputs, "figure_3_atp_convergence")
    return outputs


def _typed_connectivity_rows(output_dir: Path) -> list[dict[str, object]]:
    path = output_dir / "phase12_kda_connectivity_evidence_points.tsv"
    if not path.is_file():
        prepare_common_data(output_dir)
    rows: list[dict[str, object]] = []
    for row in read_tsv(path):
        rows.append(
            {
                **row,
                "acat_combined_p": parse_float(row["acat_combined_p"]),
                "acat_negative_log10_p": parse_float(row["acat_negative_log10_p"]),
                "ranking_runs": parse_int(row["ranking_runs"]),
                "primary_directional_significant_runs": parse_int(row["primary_directional_significant_runs"]),
                "primary_directional_recurrence_fraction": parse_float(row["primary_directional_recurrence_fraction"]),
                "total_degree": parse_int(row["total_degree"]),
                "degree_percentile": parse_float(row["degree_percentile"]),
            }
        )
    return rows


def _connectivity_correlations(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for network in NETWORK_ORDER:
        subset = [row for row in rows if row["broad_network"] == network]
        if len(subset) < 3:
            continue
        x_values = [parse_float(row["degree_percentile"]) for row in subset]
        y_values = [parse_float(row["acat_negative_log10_p"]) for row in subset]
        statistic = spearmanr(x_values, y_values)
        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "broad_network": network,
                "n_candidates": len(subset),
                "spearman_rho": float(statistic.statistic),
                "p_value": float(statistic.pvalue),
            }
        )
    return output


def generate_connectivity_evidence(output_dir: Path = DEFAULT_OUTPUT_DIR, check_hashes: bool = True) -> list[Path]:
    configure_matplotlib()
    validate_phase12_bundle(check_hashes=check_hashes)
    rows = _typed_connectivity_rows(output_dir)
    correlations = _connectivity_correlations(rows)
    if len(correlations) != 7:
        raise RuntimeError(f"Expected seven broad-network correlations, observed {len(correlations)}")

    fig, (ax_scatter, ax_rho) = plt.subplots(
        1,
        2,
        figsize=(14.2, 6.2),
        gridspec_kw={"width_ratios": [1.65, 1.0]},
        constrained_layout=True,
    )
    for network in NETWORK_ORDER:
        subset = [row for row in rows if row["broad_network"] == network]
        if not subset:
            continue
        ax_scatter.scatter(
            [row["degree_percentile"] for row in subset],
            [row["acat_negative_log10_p"] for row in subset],
            s=[18 + 38 * math.sqrt(parse_int(row["primary_directional_significant_runs"])) for row in subset],
            c=NETWORK_COLORS[network],
            alpha=0.58,
            edgecolors="white",
            linewidths=0.35,
            label=NETWORK_LABELS[network],
            rasterized=True,
        )
    selected_labels: list[Mapping[str, object]] = []
    for gene in CONNECTIVITY_LABEL_GENES:
        candidates = [row for row in rows if row["key_driver"] == gene]
        if not candidates:
            continue
        selected_labels.append(
            max(
                candidates,
                key=lambda row: (
                    parse_int(row["primary_directional_significant_runs"]),
                    parse_float(row["acat_negative_log10_p"]),
                    parse_float(row["degree_percentile"]),
                ),
            )
        )
    label_offsets = {
        "APOE": (8, 9),
        "LAMTOR5": (8, -15),
        "GABARAPL2": (-9, -11),
        "RPL11": (-9, 16),
        "RPS15": (8, 5),
        "FTL": (-10, 3),
        "ANKRD11": (8, 10),
        "SELENOW": (7, -17),
        "WDR82": (-9, 7),
        "SLC11A1": (-9, -10),
        "HSPA1A": (8, 9),
    }
    for index, row in enumerate(selected_labels):
        x_value = parse_float(row["degree_percentile"])
        y_value = parse_float(row["acat_negative_log10_p"])
        ax_scatter.scatter(
            [x_value],
            [y_value],
            s=58,
            c=NETWORK_COLORS[str(row["broad_network"])],
            edgecolors="#111111",
            linewidths=0.8,
            zorder=5,
        )
        dx, dy = label_offsets.get(str(row["key_driver"]), (7, 7))
        ax_scatter.annotate(
            f"{row['key_driver']} ({_network_abbreviation(str(row['broad_network']))})",
            (x_value, y_value),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx >= 0 else "right",
            va="bottom" if dy >= 0 else "top",
            fontsize=6.6,
            fontweight="bold",
            arrowprops={"arrowstyle": "-", "color": "#777777", "linewidth": 0.45},
        )
    ax_scatter.axhline(0, color="#BBBBBB", linewidth=0.8, linestyle="--")
    ax_scatter.set_xlim(-0.02, 1.03)
    ax_scatter.set_xlabel("Within-network total-degree percentile")
    ax_scatter.set_ylabel("\u2212log10(ACAT P)")
    ax_scatter.set_title("A  Candidate-level connectivity and KDA evidence", loc="left", fontweight="bold")
    ax_scatter.grid(color="#EEEEEE", linewidth=0.6)
    ax_scatter.legend(loc="lower left", frameon=False, ncol=2, fontsize=6.5)
    ax_scatter.text(
        0.015,
        0.985,
        "Point area = number of significant\nprimary directional KDA calls",
        transform=ax_scatter.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        color="#444444",
    )

    ordered_correlations = sorted(
        correlations,
        key=lambda row: NETWORK_ORDER.index(str(row["broad_network"])),
        reverse=True,
    )
    y_positions = np.arange(len(ordered_correlations))
    rho_values = [parse_float(row["spearman_rho"]) for row in ordered_correlations]
    bar_colors = [NETWORK_COLORS[str(row["broad_network"])] for row in ordered_correlations]
    ax_rho.hlines(y_positions, 0, rho_values, colors=bar_colors, linewidth=3, alpha=0.75)
    ax_rho.scatter(rho_values, y_positions, s=65, c=bar_colors, edgecolors="#222222", linewidths=0.5, zorder=3)
    ax_rho.axvline(0, color="#777777", linewidth=0.8)
    ax_rho.set_yticks(y_positions, [NETWORK_LABELS[str(row["broad_network"])] for row in ordered_correlations])
    for y_value, row in zip(y_positions, ordered_correlations):
        rho = parse_float(row["spearman_rho"])
        p_value = parse_float(row["p_value"])
        ax_rho.text(
            rho + (0.025 if rho >= 0 else -0.025),
            y_value,
            f"rho={rho:.2f}\np={'<1e-300' if p_value == 0 else f'{p_value:.2g}'}, n={row['n_candidates']}",
            ha="left" if rho >= 0 else "right",
            va="center",
            fontsize=6.6,
        )
    limit = max(0.45, max(abs(value) for value in rho_values) + 0.22)
    ax_rho.set_xlim(-limit, limit)
    ax_rho.set_xlabel("Spearman rho")
    ax_rho.set_title("B  Within-network association", loc="left", fontweight="bold")
    ax_rho.grid(axis="x", color="#EEEEEE", linewidth=0.6)
    for spine in ("top", "right", "left"):
        ax_rho.spines[spine].set_visible(False)
    fig.suptitle("Network connectivity is contextual evidence, not a substitute for KDA significance", fontsize=15, fontweight="bold")
    basename = output_dir / "phase12_kda_connectivity_evidence"
    main_paths = save_figure(fig, basename)
    plt.close(fig)

    diagnostic_fig, diagnostic_axes = plt.subplots(4, 2, figsize=(12.5, 15.0), constrained_layout=True)
    for ax, network in zip(diagnostic_axes.flat, NETWORK_ORDER):
        subset = [row for row in rows if row["broad_network"] == network]
        ax.scatter(
            [row["total_degree"] for row in subset],
            [row["acat_negative_log10_p"] for row in subset],
            s=[12 + 25 * math.sqrt(parse_int(row["primary_directional_significant_runs"])) for row in subset],
            c=NETWORK_COLORS[network],
            alpha=0.6,
            edgecolors="white",
            linewidths=0.3,
            rasterized=True,
        )
        correlation = next(row for row in correlations if row["broad_network"] == network)
        ax.set_title(f"{NETWORK_LABELS[network]} | rho={parse_float(correlation['spearman_rho']):.2f}", loc="left", fontweight="bold")
        ax.axhline(0, color="#BBBBBB", linewidth=0.7, linestyle="--")
        ax.set_xlabel("Full-network total degree")
        ax.set_ylabel("\u2212log10(ACAT P)")
        ax.grid(color="#EEEEEE", linewidth=0.5)
    diagnostic_axes.flat[-1].axis("off")
    diagnostic_fig.suptitle("Diagnostic: raw network degree versus ACAT KDA evidence", fontsize=14, fontweight="bold")
    diagnostic_paths = save_figure(
        diagnostic_fig,
        output_dir / "phase12_kda_connectivity_evidence_by_network",
        formats=("pdf",),
    )
    plt.close(diagnostic_fig)

    correlation_path = output_dir / "phase12_kda_connectivity_evidence_correlations.tsv"
    label_path = output_dir / "phase12_kda_connectivity_evidence_labels.tsv"
    write_tsv(correlations, correlation_path)
    write_tsv(selected_labels, label_path)
    outputs = main_paths + diagnostic_paths + [correlation_path, label_path]
    update_generation_log(output_dir, outputs, "figure_4_connectivity_evidence")
    return outputs
