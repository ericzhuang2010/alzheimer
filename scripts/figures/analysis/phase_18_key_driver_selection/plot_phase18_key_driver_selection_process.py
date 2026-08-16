#!/usr/bin/env python3
"""Render the Phase 18 key-driver selection-process figure.

The renderer reads the canonical all-tested call_key_drivers table and
visualizes stored selection results. It does not recompute KDA enrichment,
ACAT P values, or multiple-testing corrections.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "phase18_selection_process_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "phase18_selection_process_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
from PIL import Image  # noqa: E402


SCHEMA = "phase18_key_driver_selection_process_figure_v1"
INPUT_SCHEMA = "phase18_call_key_driver_returns_v1"
FIGURE_ID = "phase18_key_driver_selection_process"
FIGURE_WIDTH_IN = 7.2
FIGURE_HEIGHT_IN = 5.1
DEFAULT_PNG_DPI = 450

CLASS_ORDER = ["mt_driver", "non_mt_driver"]
CLASS_LABELS = {
    "mt_driver": "MT driver",
    "non_mt_driver": "Non-MT driver",
}
CLASS_COLORS = {
    "mt_driver": "#0072B2",
    "non_mt_driver": "#E69F00",
}
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
    "Vasculature_cells": "Vasculature cells",
}

EXPECTED_ROWS = 95_557
EXPECTED_COLUMNS = 104
EXPECTED_RUNS = 161
EXPECTED_GENES = 6_149
EXPECTED_UNITS = 10_433
EXPECTED_GATE_COUNTS = [10_433, 9_846, 243, 78]
EXPECTED_CANDIDATES = {"mt_driver": 41, "non_mt_driver": 37}
EXPECTED_CANDIDATE_GENES = {"mt_driver": 20, "non_mt_driver": 30}
EXPECTED_DISPLAY = {"mt_driver": 26, "non_mt_driver": 21}
EXPECTED_DISPLAY_MATRIX = {
    ("Astrocytes", "mt_driver"): (6, 5),
    ("Astrocytes", "non_mt_driver"): (5, 5),
    ("Excitatory_neurons", "mt_driver"): (13, 5),
    ("Excitatory_neurons", "non_mt_driver"): (21, 5),
    ("Inhibitory_neurons", "mt_driver"): (11, 5),
    ("Inhibitory_neurons", "non_mt_driver"): (5, 5),
    ("Microglia", "mt_driver"): (2, 2),
    ("Microglia", "non_mt_driver"): (1, 1),
    ("OPCs", "mt_driver"): (3, 3),
    ("OPCs", "non_mt_driver"): (4, 4),
    ("Oligodendrocytes", "mt_driver"): (2, 2),
    ("Oligodendrocytes", "non_mt_driver"): (1, 1),
    ("Vasculature_cells", "mt_driver"): (4, 4),
    ("Vasculature_cells", "non_mt_driver"): (0, 0),
}

DECLARED_OUTPUTS = [
    f"{FIGURE_ID}.png",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_status.tsv",
]

DARK = "#27364A"
TEXT = "#20252B"
MID_GRAY = "#68727D"
LIGHT_GRAY = "#E6E9ED"
PALE_GRAY = "#F5F6F7"
PALE_BLUE = "#EAF2F7"
ARROW = "#74808B"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=(
            "results/minerva_production/18_key_driver_selection/"
            "call_key_driver_returns.tsv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "results/figures/analysis/phase_18_key_driver_selection/"
            "key_driver_selection_process"
        ),
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    parser.add_argument(
        "--validate-output",
        help="Validate an existing output directory and exit.",
    )
    args = parser.parse_args(argv)
    if not 300 <= args.png_dpi <= 600:
        parser.error("--png-dpi must be between 300 and 600")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {
        "true",
        "t",
        "1",
        "yes",
    }


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def integer(value: Any) -> int:
    value_as_number = number(value)
    require(math.isfinite(value_as_number), f"Expected integer, observed {value!r}")
    return int(round(value_as_number))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = [
        "schema_version",
        "figure_id",
        "panel_id",
        "record_type",
        "stage_order",
        "broad_network",
        "case_id",
    ]
    observed: list[str] = []
    for row in rows:
        for column in row:
            if column not in observed:
                observed.append(column)
    return [column for column in preferred if column in observed] + [
        column for column in observed if column not in preferred
    ]


def clean_value(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, float) and not math.isfinite(value):
        return "NA"
    return value


def write_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty table: {path}")
    columns = ordered_columns(rows)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean_value(row.get(column)) for column in columns})
    os.replace(temporary, path)


def read_tsv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"Missing TSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def check_record(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    detail: str = "",
    *,
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "figure_id": FIGURE_ID,
        "check_id": check_id,
        "blocking": "TRUE" if blocking else "FALSE",
        "passed": "TRUE" if passed else "FALSE",
        "observed": observed,
        "expected": expected,
        "detail": detail,
    }


def load_bundle(input_path: Path) -> dict[str, Any]:
    require(input_path.exists(), f"Missing canonical input: {input_path}")
    required_columns = {
        "schema_version",
        "kda_run_id",
        "broad_network",
        "key_driver",
        "case_id",
        "is_core_mito",
        "coverage_fraction",
        "conservative_support_count",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
    }
    repeated_columns = [
        "is_core_mito",
        "coverage_fraction",
        "conservative_support_count",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
    ]

    row_count = 0
    run_ids: set[str] = set()
    genes: set[str] = set()
    run_gene_keys: set[tuple[str, str]] = set()
    gene_classes: dict[str, set[str]] = {}
    aggregates: dict[tuple[str, str, str], dict[str, str]] = {}
    aggregate_values: dict[tuple[str, str, str], tuple[str, ...]] = {}
    inconsistent_aggregate_rows = 0

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(reader.fieldnames is not None, "Input TSV has no header")
        require(len(reader.fieldnames) == EXPECTED_COLUMNS, "Unexpected input column count")
        missing = sorted(required_columns - set(reader.fieldnames))
        require(not missing, f"Input missing required columns: {', '.join(missing)}")
        for row in reader:
            row_count += 1
            require(row["schema_version"] == INPUT_SCHEMA, "Unexpected input schema")
            run_id = row["kda_run_id"]
            gene = row["key_driver"]
            case_id = row["case_id"]
            network = row["broad_network"]
            run_ids.add(run_id)
            genes.add(gene)
            run_gene_key = (run_id, gene)
            require(
                run_gene_key not in run_gene_keys,
                f"Duplicate kda_run_id + key_driver row: {run_id}, {gene}",
            )
            run_gene_keys.add(run_gene_key)
            gene_classes.setdefault(gene, set()).add(case_id)

            aggregate_key = (network, gene, case_id)
            values = tuple(row[column] for column in repeated_columns)
            if aggregate_key in aggregate_values:
                if aggregate_values[aggregate_key] != values:
                    inconsistent_aggregate_rows += 1
            else:
                aggregates[aggregate_key] = row
                aggregate_values[aggregate_key] = values

    require(row_count == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS:,} rows, found {row_count:,}")
    require(len(run_ids) == EXPECTED_RUNS, f"Expected {EXPECTED_RUNS} runs, found {len(run_ids)}")
    require(len(genes) == EXPECTED_GENES, f"Expected {EXPECTED_GENES:,} genes, found {len(genes):,}")
    require(len(aggregates) == EXPECTED_UNITS, f"Expected {EXPECTED_UNITS:,} candidate units, found {len(aggregates):,}")
    require(inconsistent_aggregate_rows == 0, "Aggregate fields vary within a candidate unit")
    require(all(len(classes) == 1 for classes in gene_classes.values()), "A gene has more than one driver class")
    require(set().union(*gene_classes.values()) == set(CLASS_ORDER), "Unexpected driver classes")
    require(
        set(network for network, _, _ in aggregates) == set(NETWORK_ORDER),
        "Unexpected broad-network set",
    )

    coverage_keys: set[tuple[str, str, str]] = set()
    coverage_support_keys: set[tuple[str, str, str]] = set()
    all_gate_keys: set[tuple[str, str, str]] = set()
    stored_candidate_keys: set[tuple[str, str, str]] = set()
    displayed_keys: set[tuple[str, str, str]] = set()

    for key, row in aggregates.items():
        coverage_pass = number(row["coverage_fraction"]) >= 0.80
        support_pass = number(row["conservative_support_count"]) >= 1
        aggregate_q_pass = number(row["aggregate_acat_q"]) <= 0.05
        if coverage_pass:
            coverage_keys.add(key)
        if coverage_pass and support_pass:
            coverage_support_keys.add(key)
        if coverage_pass and support_pass and aggregate_q_pass:
            all_gate_keys.add(key)
        if row["terminal_candidate_status"] == "driver_candidate":
            stored_candidate_keys.add(key)
        if truth(row["top5_display"]):
            displayed_keys.add(key)

        case_id = key[2]
        if case_id == "mt_driver":
            require(truth(row["is_core_mito"]), f"MT driver is not core mitochondrial: {key}")
        else:
            require(not truth(row["is_core_mito"]), f"Non-MT driver is core mitochondrial: {key}")

    gate_counts = [
        len(aggregates),
        len(coverage_keys),
        len(coverage_support_keys),
        len(all_gate_keys),
    ]
    require(gate_counts == EXPECTED_GATE_COUNTS, f"Gate counts changed: {gate_counts}")
    require(all_gate_keys == stored_candidate_keys, "Numeric gates and stored driver-candidate status disagree")
    require(displayed_keys <= stored_candidate_keys, "A displayed unit is not a driver candidate")

    candidate_counts: dict[str, int] = {}
    candidate_gene_counts: dict[str, int] = {}
    display_counts: dict[str, int] = {}
    display_matrix: dict[tuple[str, str], tuple[int, int]] = {}
    for case_id in CLASS_ORDER:
        case_candidates = {key for key in stored_candidate_keys if key[2] == case_id}
        case_displayed = {key for key in displayed_keys if key[2] == case_id}
        candidate_counts[case_id] = len(case_candidates)
        candidate_gene_counts[case_id] = len({key[1] for key in case_candidates})
        display_counts[case_id] = len(case_displayed)
        for network in NETWORK_ORDER:
            passing_n = sum(key[0] == network for key in case_candidates)
            displayed_n = sum(key[0] == network for key in case_displayed)
            display_matrix[(network, case_id)] = (passing_n, displayed_n)

    require(candidate_counts == EXPECTED_CANDIDATES, f"Candidate class counts changed: {candidate_counts}")
    require(candidate_gene_counts == EXPECTED_CANDIDATE_GENES, f"Candidate gene counts changed: {candidate_gene_counts}")
    require(display_counts == EXPECTED_DISPLAY, f"Display class counts changed: {display_counts}")
    require(display_matrix == EXPECTED_DISPLAY_MATRIX, "Network-by-class display matrix changed")
    require(len(displayed_keys) == 47, "Expected 47 displayed positions")
    require(len({key[1] for key in displayed_keys}) == 25, "Expected 25 unique displayed genes")
    require(len({key[1] for key in stored_candidate_keys}) == 50, "Expected 50 unique candidate genes")

    for network in NETWORK_ORDER:
        for case_id in CLASS_ORDER:
            group_keys = [
                key
                for key in stored_candidate_keys
                if key[0] == network and key[2] == case_id
            ]
            group_keys.sort(
                key=lambda key: (
                    number(aggregates[key]["aggregate_acat_q"]),
                    number(aggregates[key]["aggregate_acat_p"]),
                    key[1],
                )
            )
            for expected_rank, key in enumerate(group_keys, start=1):
                row = aggregates[key]
                require(
                    integer(row["within_case_rank"]) == expected_rank,
                    f"Stored rank changed for {key}",
                )
                require(
                    truth(row["top5_display"]) == (expected_rank <= 5),
                    f"Stored top-five flag changed for {key}",
                )
            require(
                sum(key in displayed_keys for key in group_keys) <= 5,
                f"More than five displayed units for {network}, {case_id}",
            )

    plot_rows: list[dict[str, Any]] = [
        {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "panel_id": "A",
            "record_type": "starting_evidence",
            "stage_order": 1,
            "counting_unit": "included_kda_call",
            "count": len(run_ids),
            "source_column": "kda_run_id",
        },
        {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "panel_id": "A",
            "record_type": "starting_evidence",
            "stage_order": 2,
            "counting_unit": "explicit_gene_run_row",
            "count": row_count,
            "unique_gene_count": len(genes),
            "source_column": "kda_run_id + key_driver",
        },
        {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "panel_id": "A",
            "record_type": "candidate_universe",
            "stage_order": 3,
            "counting_unit": "gene_broad_network_driver_class",
            "count": len(aggregates),
            "source_column": "broad_network + key_driver + case_id",
        },
    ]
    gate_names = ["represented", "coverage", "support", "aggregate_acat_q"]
    for index, (gate_name, retained) in enumerate(zip(gate_names, gate_counts)):
        previous = gate_counts[index - 1] if index else None
        plot_rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "panel_id": "B",
                "record_type": "conditional_gate_funnel",
                "stage_order": index,
                "gate_name": gate_name,
                "counting_unit": "gene_broad_network_driver_class",
                "input_n": previous,
                "retained_n": retained,
                "removed_n": None if previous is None else previous - retained,
                "conditional_retention_fraction": (
                    None if previous is None else retained / previous
                ),
            }
        )
    for case_id in CLASS_ORDER:
        plot_rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "panel_id": "C",
                "record_type": "class_summary",
                "case_id": case_id,
                "candidate_unit_count": candidate_counts[case_id],
                "candidate_unique_gene_count": candidate_gene_counts[case_id],
                "displayed_position_count": display_counts[case_id],
            }
        )
        for network in NETWORK_ORDER:
            passing_n, displayed_n = display_matrix[(network, case_id)]
            plot_rows.append(
                {
                    "schema_version": SCHEMA,
                    "figure_id": FIGURE_ID,
                    "panel_id": "C",
                    "record_type": "network_class_display",
                    "broad_network": network,
                    "case_id": case_id,
                    "candidate_unit_count": passing_n,
                    "displayed_position_count": displayed_n,
                }
            )

    return {
        "input_path": input_path,
        "input_sha256": sha256_file(input_path),
        "row_count": row_count,
        "column_count": EXPECTED_COLUMNS,
        "run_count": len(run_ids),
        "gene_count": len(genes),
        "unit_count": len(aggregates),
        "gate_counts": gate_counts,
        "candidate_counts": candidate_counts,
        "candidate_gene_counts": candidate_gene_counts,
        "display_counts": display_counts,
        "display_matrix": display_matrix,
        "candidate_unique_genes": len({key[1] for key in stored_candidate_keys}),
        "display_unique_genes": len({key[1] for key in displayed_keys}),
        "plot_rows": plot_rows,
    }


def configure_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 7,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "svg.hashsalt": SCHEMA,
            "svg.fonttype": "none",
            "pdf.compression": 9,
            "pdf.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def lighten(color: str, fraction: float = 0.85) -> tuple[float, float, float]:
    red, green, blue = matplotlib.colors.to_rgb(color)
    return (
        red + (1 - red) * fraction,
        green + (1 - green) * fraction,
        blue + (1 - blue) * fraction,
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: Any,
    edgecolor: str = DARK,
    linewidth: float = 0.8,
    radius: float = 0.018,
) -> None:
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle=f"round,pad=0.004,rounding_size={radius}",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
        )
    )


def horizontal_arrow(ax: plt.Axes, start: float, end: float, y: float) -> None:
    ax.annotate(
        "",
        xy=(end, y),
        xytext=(start, y),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops={"arrowstyle": "-|>", "color": ARROW, "lw": 0.8},
    )


def panel_heading(ax: plt.Axes, letter: str, title: str) -> None:
    ax.text(
        0.0,
        1.015,
        letter,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        color=TEXT,
        va="bottom",
    )
    ax.text(
        0.052,
        1.015,
        title,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        color=TEXT,
        va="bottom",
    )


def render_panel_a(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    ax.set_axis_off()
    panel_heading(ax, "A", "Starting evidence and aggregation")

    rounded_box(ax, 0.03, 0.56, 0.94, 0.32, facecolor=PALE_BLUE, edgecolor="#7D99AA")
    ax.text(
        0.50,
        0.78,
        f"{bundle['row_count']:,}",
        transform=ax.transAxes,
        fontsize=17,
        fontweight="bold",
        color=DARK,
        ha="center",
        va="center",
    )
    ax.text(
        0.50,
        0.665,
        "explicit gene × run rows",
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
    )
    ax.text(
        0.50,
        0.595,
        f"{bundle['run_count']} included KDA calls  •  {bundle['gene_count']:,} unique tested genes",
        transform=ax.transAxes,
        fontsize=6.8,
        color=MID_GRAY,
        ha="center",
        va="center",
    )

    ax.annotate(
        "",
        xy=(0.13, 0.40),
        xytext=(0.13, 0.55),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops={"arrowstyle": "-|>", "color": ARROW, "lw": 0.8},
    )
    ax.text(
        0.20,
        0.475,
        "combine across eligible runs\nwithin network × driver class",
        transform=ax.transAxes,
        fontsize=6.3,
        color=MID_GRAY,
        ha="left",
        va="center",
        linespacing=1.15,
    )

    rounded_box(ax, 0.10, 0.10, 0.80, 0.27, facecolor="#F1F4F6", edgecolor="#87929C")
    ax.text(
        0.50,
        0.275,
        f"{bundle['unit_count']:,}",
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        color=DARK,
        ha="center",
        va="center",
    )
    ax.text(
        0.50,
        0.18,
        "gene × broad-network × driver-class units",
        transform=ax.transAxes,
        fontsize=7.1,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
    )
    ax.text(
        0.50,
        0.025,
        "The counting unit changes; box sizes are not proportional.",
        transform=ax.transAxes,
        fontsize=6.5,
        color=MID_GRAY,
        ha="center",
        va="bottom",
    )


def render_panel_b(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    ax.set_axis_off()
    panel_heading(ax, "B", "All three candidate gates are required")
    counts = bundle["gate_counts"]
    stages = [
        ("Represented", counts[0], "candidate units", None, None),
        ("Coverage", counts[1], "≥80% usable runs", counts[0] - counts[1], counts[1] / counts[0]),
        ("Support", counts[2], "≥1 supporting run", counts[1] - counts[2], counts[2] / counts[1]),
        ("ACAT q", counts[3], "q ≤ 0.05", counts[2] - counts[3], counts[3] / counts[2]),
    ]
    xs = [0.005, 0.255, 0.505, 0.755]
    width = 0.22

    ax.plot([0.275, 0.955], [0.89, 0.89], transform=ax.transAxes, color=DARK, lw=0.8)
    ax.plot([0.275, 0.275], [0.85, 0.89], transform=ax.transAxes, color=DARK, lw=0.8)
    ax.plot([0.955, 0.955], [0.85, 0.89], transform=ax.transAxes, color=DARK, lw=0.8)
    ax.text(
        0.615,
        0.91,
        "all three required (AND)",
        transform=ax.transAxes,
        fontsize=7,
        fontweight="bold",
        color=DARK,
        ha="center",
        va="bottom",
    )

    for index, (name, count, rule, removed, fraction) in enumerate(stages):
        facecolor = PALE_GRAY if index == 0 else lighten("#56B4E9", 0.82 - index * 0.06)
        edgecolor = "#8B949D" if index == 0 else "#4D91B5"
        rounded_box(ax, xs[index], 0.27, width, 0.51, facecolor=facecolor, edgecolor=edgecolor)
        ax.text(
            xs[index] + width / 2,
            0.715,
            name,
            transform=ax.transAxes,
            fontsize=7.2,
            fontweight="bold",
            color=TEXT,
            ha="center",
            va="center",
        )
        ax.text(
            xs[index] + width / 2,
            0.56,
            f"{count:,}",
            transform=ax.transAxes,
            fontsize=14.5,
            fontweight="bold",
            color=DARK,
            ha="center",
            va="center",
        )
        ax.text(
            xs[index] + width / 2,
            0.445,
            rule,
            transform=ax.transAxes,
            fontsize=6.7,
            color=TEXT,
            ha="center",
            va="center",
        )
        if removed is not None and fraction is not None:
            ax.text(
                xs[index] + width / 2,
                0.345,
                f"{removed:,} removed\n{100 * fraction:.1f}% kept",
                transform=ax.transAxes,
                fontsize=6.2,
                color=MID_GRAY,
                ha="center",
                va="center",
                linespacing=1.12,
            )
        if index < len(stages) - 1:
            horizontal_arrow(ax, xs[index] + width + 0.006, xs[index + 1] - 0.006, 0.525)

    ax.text(
        0.50,
        0.17,
        "Counts are conditional in the displayed order.\n"
        "The final decision is the intersection of all three gates.",
        transform=ax.transAxes,
        fontsize=6.4,
        color=MID_GRAY,
        ha="center",
        va="center",
        linespacing=1.2,
    )
    ax.text(
        0.50,
        0.065,
        "78 passing units = 0.75% of the represented candidate units",
        transform=ax.transAxes,
        fontsize=7.2,
        fontweight="bold",
        color=DARK,
        ha="center",
        va="center",
    )


def render_panel_c(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    ax.set_axis_off()
    panel_heading(ax, "C", "Rank within each network and driver class; retain up to five")

    pill_specs = [
        (0.02, "78 passing units", "50 unique genes", PALE_GRAY, "#87929C"),
        (0.375, "14 ranked lists", "7 networks × 2 classes", PALE_BLUE, "#7D99AA"),
        (0.73, "47 displayed positions", "25 unique genes", "#E9F2EE", "#6C9B84"),
    ]
    pill_width = 0.25
    for index, (x, main, secondary, face, edge) in enumerate(pill_specs):
        rounded_box(ax, x, 0.805, pill_width, 0.13, facecolor=face, edgecolor=edge, radius=0.025)
        ax.text(
            x + pill_width / 2,
            0.885,
            main,
            transform=ax.transAxes,
            fontsize=7.6,
            fontweight="bold",
            color=DARK,
            ha="center",
            va="center",
        )
        ax.text(
            x + pill_width / 2,
            0.835,
            secondary,
            transform=ax.transAxes,
            fontsize=6.4,
            color=MID_GRAY,
            ha="center",
            va="center",
        )
        if index < 2:
            horizontal_arrow(ax, x + pill_width + 0.012, pill_specs[index + 1][0] - 0.012, 0.87)

    x_left = 0.02
    widths = [0.35, 0.305, 0.305]
    xs = [x_left, x_left + widths[0], x_left + widths[0] + widths[1]]
    header_y = 0.655
    header_height = 0.115
    row_height = 0.073

    header_specs = [
        ("Broad network", "cell: passing → displayed", "#EEF0F2", "#9BA3AA"),
        (
            "MT driver",
            f"{bundle['candidate_counts']['mt_driver']} → {bundle['display_counts']['mt_driver']} displayed",
            lighten(CLASS_COLORS["mt_driver"], 0.80),
            CLASS_COLORS["mt_driver"],
        ),
        (
            "Non-MT driver",
            f"{bundle['candidate_counts']['non_mt_driver']} → {bundle['display_counts']['non_mt_driver']} displayed",
            lighten(CLASS_COLORS["non_mt_driver"], 0.78),
            CLASS_COLORS["non_mt_driver"],
        ),
    ]
    for x, width, (title, subtitle, face, edge) in zip(xs, widths, header_specs):
        ax.add_patch(
            mpatches.Rectangle(
                (x, header_y),
                width,
                header_height,
                transform=ax.transAxes,
                facecolor=face,
                edgecolor=edge,
                linewidth=0.8,
            )
        )
        ax.text(
            x + width / 2,
            header_y + 0.071,
            title,
            transform=ax.transAxes,
            fontsize=7.4,
            fontweight="bold",
            color=TEXT,
            ha="center",
            va="center",
        )
        ax.text(
            x + width / 2,
            header_y + 0.027,
            subtitle,
            transform=ax.transAxes,
            fontsize=6.3,
            color=MID_GRAY,
            ha="center",
            va="center",
        )

    for row_index, network in enumerate(NETWORK_ORDER):
        y = header_y - (row_index + 1) * row_height
        neutral_face = "#FAFAFA" if row_index % 2 == 0 else "#F2F3F4"
        ax.add_patch(
            mpatches.Rectangle(
                (xs[0], y),
                widths[0],
                row_height,
                transform=ax.transAxes,
                facecolor=neutral_face,
                edgecolor="#C7CCD1",
                linewidth=0.55,
            )
        )
        ax.text(
            xs[0] + 0.012,
            y + row_height / 2,
            NETWORK_LABELS[network],
            transform=ax.transAxes,
            fontsize=7,
            color=TEXT,
            ha="left",
            va="center",
        )
        for class_index, case_id in enumerate(CLASS_ORDER, start=1):
            passing_n, displayed_n = bundle["display_matrix"][(network, case_id)]
            color = CLASS_COLORS[case_id]
            cell_face = lighten(color, 0.92 if row_index % 2 == 0 else 0.87)
            ax.add_patch(
                mpatches.Rectangle(
                    (xs[class_index], y),
                    widths[class_index],
                    row_height,
                    transform=ax.transAxes,
                    facecolor=cell_face,
                    edgecolor=lighten(color, 0.55),
                    linewidth=0.55,
                )
            )
            ax.text(
                xs[class_index] + widths[class_index] / 2,
                y + row_height / 2,
                f"{passing_n}  →  {displayed_n}",
                transform=ax.transAxes,
                fontsize=7.6,
                fontweight="bold",
                color=DARK,
                ha="center",
                va="center",
            )

    ax.text(
        0.50,
        0.065,
        "Rank by aggregate ACAT q, then ACAT p, then gene symbol  •  retain ranks 1–5  •  no backfilling",
        transform=ax.transAxes,
        fontsize=6.8,
        color=MID_GRAY,
        ha="center",
        va="center",
    )


def render_figure(bundle: Mapping[str, Any]) -> plt.Figure:
    configure_style()
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor="white")
    fig.text(
        0.025,
        0.982,
        "Phase 18 key-driver selection",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT,
        ha="left",
        va="top",
    )
    fig.text(
        0.025,
        0.948,
        "From 95,557 run-level tests to 47 displayed gene × network positions",
        fontsize=7.3,
        color=MID_GRAY,
        ha="left",
        va="top",
    )
    grid = fig.add_gridspec(
        2,
        2,
        left=0.025,
        right=0.99,
        bottom=0.045,
        top=0.895,
        hspace=0.24,
        wspace=0.13,
        width_ratios=[0.40, 0.60],
        height_ratios=[0.94, 1.30],
    )
    panel_a = fig.add_subplot(grid[0, 0])
    panel_b = fig.add_subplot(grid[0, 1])
    panel_c = fig.add_subplot(grid[1, :])
    render_panel_a(panel_a, bundle)
    render_panel_b(panel_b, bundle)
    render_panel_c(panel_c, bundle)
    return fig


def render_images(fig: plt.Figure, output_dir: Path, dpi: int) -> list[Path]:
    paths: list[Path] = []
    for extension in ("svg", "pdf", "png"):
        final = output_dir / f"{FIGURE_ID}.{extension}"
        temporary = output_dir / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Creator": "Phase 18 key-driver selection-process renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {
                "Creator": "Phase 18 key-driver selection-process renderer",
                "Date": None,
            }
        else:
            metadata = {"Software": "Phase 18 key-driver selection-process renderer"}
        fig.savefig(
            temporary,
            format=extension,
            dpi=dpi if extension == "png" else None,
            facecolor="white",
            metadata=metadata,
        )
        require(temporary.exists() and temporary.stat().st_size > 0, f"Empty image: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths


CAPTION = """# Phase 18 key-driver selection-process figure caption

**Phase 18 key-driver selection from run-level tests to top-five lists.** **A,** The canonical table contains 95,557 explicitly tested gene × run results from 161 included KDA calls and 6,149 unique tested genes. Repeated run-level evidence is represented by 10,433 unique gene × broad-network × driver-class units. **B,** Candidate units must pass all three gates: at least 80% usable-run coverage, at least one conservatively supporting run, and aggregate ACAT q ≤ 0.05. The displayed conditional sequence retains 9,846, 243, and 78 units, respectively. **C,** The 78 passing units are ranked separately within seven broad networks and two driver classes. Retaining ranks 1–5 without backfilling yields 47 displayed gene × network positions: 26 MT-driver and 21 non-MT-driver positions, representing 25 unique gene symbols. Counts are exact and descriptive.
"""


METHODS = """# Phase 18 key-driver selection-process figure methods

The renderer reads `call_key_driver_returns.tsv`, verifies the `phase18_call_key_driver_returns_v1` schema, and validates one unique row per `kda_run_id + key_driver`. It deduplicates repeated aggregate fields to one `broad_network + key_driver + case_id` record and verifies that the fields are constant within that unit.

The displayed gate sequence is calculated from the stored `coverage_fraction >= 0.80`, `conservative_support_count >= 1`, and `aggregate_acat_q <= 0.05` fields. The intersection is required to match `terminal_candidate_status = driver_candidate`. Passing candidates are ordered within each broad-network × driver-class list by ascending `aggregate_acat_q`, ascending `aggregate_acat_p`, and gene symbol. Stored `within_case_rank` and `top5_display` values are checked against this ordering. The renderer does not recompute KDA enrichment, run-level P values, ACAT P values, or BH corrections.

Counts are deterministic properties of the saved table, so uncertainty intervals and significance annotations are not applicable. Okabe–Ito blue and orange identify the two driver classes and are supplemented by explicit class labels and exact counts. PDF and SVG are vector outputs; PNG is exported at 450 DPI.
"""


def image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    checks = [
        check_record(
            "vector_and_raster_outputs",
            set(lookup) == {".svg", ".pdf", ".png"},
            "|".join(sorted(lookup)),
            ".pdf|.png|.svg",
        ),
        check_record(
            "image_outputs_nonempty",
            all(path.stat().st_size > 0 for path in image_paths),
            sum(path.stat().st_size > 0 for path in image_paths),
            3,
        ),
    ]
    svg_text = lookup[".svg"].read_text(encoding="utf-8")
    checks.append(check_record("svg_is_vector", "<svg" in svg_text, "<svg present", "<svg present"))
    checks.append(check_record("svg_text_preserved", "<text" in svg_text, "<text present", "<text present"))
    with lookup[".pdf"].open("rb") as handle:
        pdf_header = handle.read(5)
    checks.append(check_record("pdf_signature", pdf_header == b"%PDF-", pdf_header.decode("latin1"), "%PDF-"))
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        png_dpi = image.info.get("dpi", (math.nan, math.nan))
    expected_width = round(FIGURE_WIDTH_IN * dpi)
    expected_height = round(FIGURE_HEIGHT_IN * dpi)
    checks.append(check_record("png_width", width == expected_width, width, expected_width))
    checks.append(check_record("png_height", height == expected_height, height, expected_height))
    dpi_ok = all(math.isfinite(value) and abs(value - dpi) <= 1 for value in png_dpi)
    checks.append(check_record("png_resolution", dpi_ok, f"{png_dpi[0]:.2f}|{png_dpi[1]:.2f}", f"{dpi}|{dpi}"))
    return checks


def build_checks(
    bundle: Mapping[str, Any],
    image_paths: Sequence[Path],
    dpi: int,
    visual_review_status: str,
) -> list[dict[str, Any]]:
    matrix_string = "|".join(
        f"{network}:{case_id}:{bundle['display_matrix'][(network, case_id)][0]}>{bundle['display_matrix'][(network, case_id)][1]}"
        for network in NETWORK_ORDER
        for case_id in CLASS_ORDER
    )
    expected_matrix_string = "|".join(
        f"{network}:{case_id}:{EXPECTED_DISPLAY_MATRIX[(network, case_id)][0]}>{EXPECTED_DISPLAY_MATRIX[(network, case_id)][1]}"
        for network in NETWORK_ORDER
        for case_id in CLASS_ORDER
    )
    checks = [
        check_record("input_schema", True, INPUT_SCHEMA, INPUT_SCHEMA),
        check_record("input_rows", bundle["row_count"] == EXPECTED_ROWS, bundle["row_count"], EXPECTED_ROWS),
        check_record("input_columns", bundle["column_count"] == EXPECTED_COLUMNS, bundle["column_count"], EXPECTED_COLUMNS),
        check_record("included_calls", bundle["run_count"] == EXPECTED_RUNS, bundle["run_count"], EXPECTED_RUNS),
        check_record("unique_tested_genes", bundle["gene_count"] == EXPECTED_GENES, bundle["gene_count"], EXPECTED_GENES),
        check_record("represented_candidate_units", bundle["unit_count"] == EXPECTED_UNITS, bundle["unit_count"], EXPECTED_UNITS),
        check_record("conditional_gate_counts", bundle["gate_counts"] == EXPECTED_GATE_COUNTS, "|".join(map(str, bundle["gate_counts"])), "|".join(map(str, EXPECTED_GATE_COUNTS))),
        check_record("candidate_class_counts", bundle["candidate_counts"] == EXPECTED_CANDIDATES, bundle["candidate_counts"], EXPECTED_CANDIDATES),
        check_record("candidate_unique_genes", bundle["candidate_unique_genes"] == 50, bundle["candidate_unique_genes"], 50),
        check_record("display_class_counts", bundle["display_counts"] == EXPECTED_DISPLAY, bundle["display_counts"], EXPECTED_DISPLAY),
        check_record("displayed_positions", sum(bundle["display_counts"].values()) == 47, sum(bundle["display_counts"].values()), 47),
        check_record("displayed_unique_genes", bundle["display_unique_genes"] == 25, bundle["display_unique_genes"], 25),
        check_record("network_class_matrix", matrix_string == expected_matrix_string, matrix_string, expected_matrix_string),
        check_record("top_five_limit", all(displayed <= 5 for _, displayed in bundle["display_matrix"].values()), max(displayed for _, displayed in bundle["display_matrix"].values()), "<=5"),
        check_record("colorblind_safe_palette", True, "Okabe-Ito blue|orange + labels", "colorblind-safe + redundant labels"),
        check_record("minimum_text_size", True, ">=6.2 pt; primary labels >=7 pt", ">=6 pt"),
        check_record("no_uncertainty_bars", True, "not applicable to deterministic counts", "not applicable"),
        check_record("visual_review_complete", visual_review_status == "complete", visual_review_status, "complete", "Manual review of clipping, readability, color, and grayscale redundancy.", blocking=False),
    ]
    checks.extend(image_checks(image_paths, dpi))
    return checks


def validate_output(directory: Path, expected_visual_status: str | None = None) -> None:
    require(directory.exists() and directory.is_dir(), f"Missing output directory: {directory}")
    observed_files = sorted(path.name for path in directory.iterdir() if path.is_file())
    require(observed_files == sorted(DECLARED_OUTPUTS), f"Output declaration mismatch: {observed_files}")
    status_rows = read_tsv(directory / f"{FIGURE_ID}_status.tsv")
    require(len(status_rows) == 1, "Figure status must contain one row")
    status = status_rows[0]
    visual_status = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual_status == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual_status == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Unexpected validation status")
    checks = read_tsv(directory / f"{FIGURE_ID}_checks.tsv")
    blocking_failures = [
        row["check_id"]
        for row in checks
        if truth(row["blocking"]) and not truth(row["passed"])
    ]
    require(not blocking_failures, f"Blocking checks failed: {', '.join(blocking_failures)}")
    if visual_status == "complete":
        require(all(truth(row["passed"]) for row in checks), "Completed package contains a failed check")
    image_rows = image_checks(
        [directory / f"{FIGURE_ID}.{extension}" for extension in ("svg", "pdf", "png")],
        integer(status["png_dpi"]),
    )
    require(all(truth(row["passed"]) for row in image_rows), "Output image validation failed")
    print(f"Phase 18 selection-process output validation passed: {directory}")


def publish(
    input_path: Path,
    output_dir: Path,
    dpi: int,
    visual_review_status: str,
) -> None:
    require(not output_dir.exists(), f"Refusing to overwrite existing output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".phase18_selection_process.staging.", dir=output_dir.parent)
    )
    try:
        bundle = load_bundle(input_path)
        figure = render_figure(bundle)
        image_paths = render_images(figure, staging, dpi)
        write_tsv(staging / f"{FIGURE_ID}_plot_data.tsv", bundle["plot_rows"])
        write_text(staging / f"{FIGURE_ID}_caption.md", CAPTION)
        write_text(staging / f"{FIGURE_ID}_methods.md", METHODS)

        checks = build_checks(bundle, image_paths, dpi, visual_review_status)
        write_tsv(staging / f"{FIGURE_ID}_checks.tsv", checks)
        blocking_failures = sum(
            truth(row["blocking"]) and not truth(row["passed"]) for row in checks
        )
        pending_nonblocking = sum(
            not truth(row["blocking"]) and not truth(row["passed"]) for row in checks
        )
        require(blocking_failures == 0, "A blocking figure-package check failed")
        validation_status = (
            "validated_complete"
            if visual_review_status == "complete" and pending_nonblocking == 0
            else "awaiting_visual_review"
        )
        status = {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "input_path": str(input_path),
            "input_sha256": bundle["input_sha256"],
            "renderer_sha256": sha256_file(Path(__file__).resolve()),
            "figure_width_inches": FIGURE_WIDTH_IN,
            "figure_height_inches": FIGURE_HEIGHT_IN,
            "png_dpi": dpi,
            "input_rows": bundle["row_count"],
            "candidate_units": bundle["unit_count"],
            "driver_candidates": sum(bundle["candidate_counts"].values()),
            "displayed_positions": sum(bundle["display_counts"].values()),
            "declared_outputs": len(DECLARED_OUTPUTS),
            "checks": len(checks),
            "failed_blocking_checks": blocking_failures,
            "pending_nonblocking_checks": pending_nonblocking,
            "visual_review_status": visual_review_status,
            "validation_status": validation_status,
        }
        write_tsv(staging / f"{FIGURE_ID}_status.tsv", [status])
        validate_output(staging, visual_review_status)
        staging.replace(output_dir)
        print(f"Phase 18 key-driver selection-process figure published: {output_dir}")
        print("Gate counts: 10,433 -> 9,846 -> 243 -> 78; displayed positions: 47")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd().resolve()
    if args.validate_output:
        validate_output((root / args.validate_output).resolve())
        return 0
    input_path = (root / args.input).resolve()
    output_dir = (root / args.output_dir).resolve()
    publish(input_path, output_dir, args.png_dpi, args.visual_review_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
