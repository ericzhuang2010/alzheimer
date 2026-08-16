#!/usr/bin/env python3
"""Build the current Phase 18 non-MT-driver evidence atlas.

Panel A preserves the established network-evidence matrix. Panel B summarizes
how often each selected gene was returned as significant by call_key_drivers()
and adds stricter support and breadth statistics. Panel C shows the stability
diagnostics available in the canonical two-class TSV.
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
import time
from typing import Any, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "phase18_non_mt_atlas_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "phase18_non_mt_atlas_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
from PIL import Image  # noqa: E402


SCHEMA = "phase18_non_mt_evidence_atlas_v2"
INPUT_SCHEMA = "phase18_call_key_driver_returns_v1"
CASE_ID = "non_mt_driver"
FIGURE_ID = "phase18_evidence_atlas_non_mt"
DEFAULT_INPUT = (
    "results/minerva_production/18_key_driver_selection/"
    "call_key_driver_returns.tsv"
)
DEFAULT_OUTPUT = (
    "results/figures/analysis/phase_18_key_driver_selection/"
    "evidence_atlas_non_mt"
)
DEFAULT_DPI = 450
DEFAULT_WIDTH = 12.0
DEFAULT_HEIGHT = 8.0
DEFAULT_EVIDENCE_CAP = 12.0

SUMMARY_FILE = f"{FIGURE_ID}_gene_summary.tsv"
DETAIL_FILE = f"{FIGURE_ID}_gene_network_details.tsv"
PLOT_FILE = f"{FIGURE_ID}_plot_data.tsv"
CAPTION_FILE = f"{FIGURE_ID}_caption.md"
METHODS_FILE = f"{FIGURE_ID}_methods.md"
MANIFEST_FILE = f"{FIGURE_ID}_manifest.tsv"
CHECKS_FILE = f"{FIGURE_ID}_checks.tsv"
ARTIFACTS_FILE = f"{FIGURE_ID}_artifacts.tsv"
STATUS_FILE = f"{FIGURE_ID}_status.tsv"
IMAGE_FILES = [
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.png",
]
DECLARED_OUTPUTS = IMAGE_FILES + [
    SUMMARY_FILE,
    DETAIL_FILE,
    PLOT_FILE,
    CAPTION_FILE,
    METHODS_FILE,
    MANIFEST_FILE,
    CHECKS_FILE,
    ARTIFACTS_FILE,
    STATUS_FILE,
]

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
}
NETWORK_COLORS = {
    "Astrocytes": "#009E73",
    "Excitatory_neurons": "#E69F00",
    "Inhibitory_neurons": "#0072B2",
    "Microglia": "#CC79A7",
    "OPCs": "#56B4E9",
    "Oligodendrocytes": "#F0E442",
    "Vasculature_cells": "#D55E00",
}
EXPECTED_GENES = {
    "ANKRD11",
    "APOE",
    "ATP6V1F",
    "DYNLT1",
    "FTL",
    "LAMTOR5",
    "LAPTM4A",
    "NCOA1",
    "RPL11",
    "RPL15",
    "RPL38",
    "RPLP1",
    "RPS13",
    "RPS15",
    "SELENOW",
}
EXPECTED_EXTRA_CONTEXT = ("Excitatory_neurons", "RPS15")
EXPECTED_INPUT_ROWS = 95_557
EXPECTED_INPUT_COLUMNS = 104
EXPECTED_RUNS = 161
EXPECTED_ALL_GENES = 6_149
EXPECTED_SELECTED_TEST_ROWS = 830
EXPECTED_SELECTED_SIGNIFICANT_ROWS = 149
EXPECTED_SELECTED_SUPPORT_ROWS = 135

TEXT = "#252525"
MID = "#666E78"
GRID = "#E2E5E8"
EMPTY = "#F3F3F3"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--width-inches", type=float, default=DEFAULT_WIDTH)
    parser.add_argument("--height-inches", type=float, default=DEFAULT_HEIGHT)
    parser.add_argument("--evidence-cap", type=float, default=DEFAULT_EVIDENCE_CAP)
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
    if args.width_inches <= 0 or args.height_inches <= 0:
        parser.error("Figure dimensions must be positive")
    if args.evidence_cap <= 0:
        parser.error("--evidence-cap must be positive")
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


def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def integer(value: Any) -> int:
    result = number(value)
    require(result is not None, f"Expected integer-like value, observed {value!r}")
    return int(round(result))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_value(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, float) and not math.isfinite(value):
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = [
        "schema_version",
        "figure_id",
        "case_id",
        "atlas_display_order",
        "current_symbol",
        "network_order",
        "broad_network",
    ]
    observed: list[str] = []
    for row in rows:
        for column in row:
            if column not in observed:
                observed.append(column)
    return [column for column in preferred if column in observed] + [
        column for column in observed if column not in preferred
    ]


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


def write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def tokens(values: set[str]) -> str:
    return "|".join(sorted(value for value in values if value))


def ordered_networks(values: set[str]) -> str:
    return "|".join(network for network in NETWORK_ORDER if network in values)


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
        "schema_version": f"{SCHEMA}_checks_v1",
        "figure_id": FIGURE_ID,
        "check_id": check_id,
        "blocking": "TRUE" if blocking else "FALSE",
        "passed": "TRUE" if passed else "FALSE",
        "observed": observed,
        "expected": expected,
        "detail": detail,
    }


def load_bundle(input_path: Path, evidence_cap: float) -> dict[str, Any]:
    require(input_path.exists(), f"Missing canonical input: {input_path}")
    required = {
        "schema_version",
        "kda_run_id",
        "fine_cell_type",
        "broad_network",
        "signature_group",
        "signature_direction",
        "key_driver",
        "tested_by_call_key_drivers",
        "significant_by_call_key_drivers",
        "case_id",
        "is_core_mito",
        "extended_reference_member",
        "coverage_fraction",
        "conservative_support_count",
        "conservative_support",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
        "stability_assessable_repetitions",
        "stability_nominal_fraction",
        "stability_q_fraction",
        "stability_candidate_fraction",
        "stability_worst_rank",
        "evidence_tier",
    }
    repeated_fields = [
        "is_core_mito",
        "extended_reference_member",
        "coverage_fraction",
        "conservative_support_count",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
        "stability_assessable_repetitions",
        "stability_nominal_fraction",
        "stability_q_fraction",
        "stability_candidate_fraction",
        "stability_worst_rank",
        "evidence_tier",
    ]

    row_count = 0
    run_ids: set[str] = set()
    all_genes: set[str] = set()
    run_gene_keys: set[tuple[str, str]] = set()
    aggregates: dict[tuple[str, str], dict[str, str]] = {}
    aggregate_values: dict[tuple[str, str], tuple[str, ...]] = {}

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(reader.fieldnames is not None, "Input has no header")
        require(len(reader.fieldnames) == EXPECTED_INPUT_COLUMNS, "Unexpected input column count")
        missing = sorted(required - set(reader.fieldnames))
        require(not missing, f"Input missing required columns: {', '.join(missing)}")
        for row in reader:
            row_count += 1
            require(row["schema_version"] == INPUT_SCHEMA, "Unexpected input schema")
            run_id = row["kda_run_id"]
            gene = row["key_driver"]
            run_gene = (run_id, gene)
            require(run_gene not in run_gene_keys, f"Duplicate gene-run row: {run_gene}")
            run_gene_keys.add(run_gene)
            run_ids.add(run_id)
            all_genes.add(gene)
            if row["case_id"] != CASE_ID:
                continue
            key = (row["broad_network"], gene)
            values = tuple(row[field] for field in repeated_fields)
            if key in aggregate_values:
                require(aggregate_values[key] == values, f"Aggregate fields vary within {key}")
            else:
                aggregate_values[key] = values
                aggregates[key] = row

    require(row_count == EXPECTED_INPUT_ROWS, f"Expected {EXPECTED_INPUT_ROWS:,} rows, found {row_count:,}")
    require(len(run_ids) == EXPECTED_RUNS, f"Expected {EXPECTED_RUNS} runs, found {len(run_ids)}")
    require(len(all_genes) == EXPECTED_ALL_GENES, f"Expected {EXPECTED_ALL_GENES:,} genes, found {len(all_genes):,}")
    require(set(network for network, _ in aggregates) == set(NETWORK_ORDER), "Unexpected network set")

    displayed_keys = {key for key, row in aggregates.items() if truth(row["top5_display"])}
    circle_genes = {gene for _, gene in displayed_keys}
    passing_keys = {
        key
        for key, row in aggregates.items()
        if key[1] in circle_genes
        and row["terminal_candidate_status"] == "driver_candidate"
    }
    require(len(displayed_keys) == 21, "Expected 21 displayed non-MT contexts")
    require(len(circle_genes) == 15, "Expected 15 selected non-MT genes")
    require(circle_genes == EXPECTED_GENES, "Selected non-MT gene set changed")
    require(len(passing_keys) == 22, "Expected 22 passing contexts for selected genes")
    require(passing_keys - displayed_keys == {EXPECTED_EXTRA_CONTEXT}, "Unexpected passing context below display cap")
    require(not displayed_keys - passing_keys, "A displayed context is not a candidate")

    selected_rows: dict[str, list[dict[str, str]]] = {gene: [] for gene in circle_genes}
    with input_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["case_id"] == CASE_ID and row["key_driver"] in circle_genes:
                selected_rows[row["key_driver"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    passing_networks_by_gene: dict[str, set[str]] = {
        gene: {network for network, observed_gene in passing_keys if observed_gene == gene}
        for gene in circle_genes
    }
    displayed_networks_by_gene: dict[str, set[str]] = {
        gene: {network for network, observed_gene in displayed_keys if observed_gene == gene}
        for gene in circle_genes
    }

    for gene in circle_genes:
        rows = selected_rows[gene]
        observed_run_ids = [row["kda_run_id"] for row in rows]
        require(len(observed_run_ids) == len(set(observed_run_ids)), f"Duplicate selected run for {gene}")
        require(all(truth(row["tested_by_call_key_drivers"]) for row in rows), f"Untested explicit row for {gene}")
        significant = [row for row in rows if truth(row["significant_by_call_key_drivers"])]
        support = [row for row in rows if truth(row["conservative_support"])]
        require(
            {row["kda_run_id"] for row in support}
            <= {row["kda_run_id"] for row in significant},
            f"Conservative support is not a subset of significant KDA returns for {gene}",
        )
        significant_fine = {row["fine_cell_type"] for row in significant}
        support_fine = {row["fine_cell_type"] for row in support}
        support_groups = {row["signature_group"] for row in support}
        support_directions = {row["signature_direction"] for row in support}

        passing_networks = passing_networks_by_gene[gene]
        displayed_networks = displayed_networks_by_gene[gene]
        passing_support = [
            row
            for row in support
            if row["broad_network"] in passing_networks
        ]
        passing_support_fine = {row["fine_cell_type"] for row in passing_support}
        gene_contexts = [aggregates[(network, gene)] for network in passing_networks]
        q_contexts = sorted(
            gene_contexts,
            key=lambda row: (number(row["aggregate_acat_q"]), row["broad_network"]),
        )
        extended_values = {truth(row["extended_reference_member"]) for row in rows}
        require(len(extended_values) == 1, f"Extended-reference annotation varies for {gene}")
        require(all(not truth(row["is_core_mito"]) for row in rows), f"Non-MT gene marked core: {gene}")
        summary_rows.append(
            {
                "schema_version": f"{SCHEMA}_gene_summary_v1",
                "case_id": CASE_ID,
                "current_symbol": gene,
                "is_core_mito": False,
                "extended_reference_member": next(iter(extended_values)),
                "circle_gene": True,
                "circle_display_network_count": len(displayed_networks),
                "circle_display_networks": ordered_networks(displayed_networks),
                "passing_broad_network_count": len(passing_networks),
                "passing_broad_networks": ordered_networks(passing_networks),
                "explicitly_tested_run_count": len(rows),
                "significant_kda_run_count": len(significant),
                "significant_kda_run_fraction": len(significant) / len(rows),
                "conservative_supporting_run_count": len(support),
                "conservative_supporting_run_fraction": len(support) / len(rows),
                "significant_fine_cell_type_count": len(significant_fine),
                "significant_fine_cell_types": tokens(significant_fine),
                "supporting_fine_cell_type_count": len(support_fine),
                "supporting_fine_cell_types": tokens(support_fine),
                "supporting_group_count": len(support_groups),
                "supporting_groups": tokens(support_groups),
                "supporting_direction_count": len(support_directions),
                "supporting_directions": tokens(support_directions),
                "passing_context_supporting_run_count": len(passing_support),
                "passing_context_supporting_fine_cell_type_count": len(passing_support_fine),
                "best_aggregate_acat_q": number(q_contexts[0]["aggregate_acat_q"]),
                "best_aggregate_acat_q_network": q_contexts[0]["broad_network"],
                "worst_aggregate_acat_q": number(q_contexts[-1]["aggregate_acat_q"]),
                "worst_aggregate_acat_q_network": q_contexts[-1]["broad_network"],
                "atlas_display_order": None,
            }
        )

    summary_rows.sort(
        key=lambda row: (
            -row["passing_broad_network_count"],
            -row["passing_context_supporting_fine_cell_type_count"],
            -row["passing_context_supporting_run_count"],
            row["current_symbol"],
        )
    )
    for order, row in enumerate(summary_rows, start=1):
        row["atlas_display_order"] = order
    display_order = {row["current_symbol"]: row["atlas_display_order"] for row in summary_rows}

    for network, gene in sorted(
        passing_keys,
        key=lambda key: (display_order[key[1]], NETWORK_ORDER.index(key[0])),
    ):
        row = aggregates[(network, gene)]
        q_value = number(row["aggregate_acat_q"])
        require(q_value is not None and 0 < q_value <= 0.05, f"Invalid candidate q for {(network, gene)}")
        assessable = integer(row["stability_assessable_repetitions"]) > 0
        detail_rows.append(
            {
                "schema_version": f"{SCHEMA}_gene_network_details_v1",
                "case_id": CASE_ID,
                "atlas_display_order": display_order[gene],
                "current_symbol": gene,
                "network_order": NETWORK_ORDER.index(network) + 1,
                "broad_network": network,
                "network_label": NETWORK_LABELS[network],
                "network_color": NETWORK_COLORS[network],
                "circle_displayed": (network, gene) in displayed_keys,
                "within_case_rank": integer(row["within_case_rank"]),
                "evidence_tier": row["evidence_tier"],
                "eligible_run_count": integer(row["eligible_run_count"]),
                "usable_run_count": integer(row["usable_run_count"]),
                "coverage_fraction": number(row["coverage_fraction"]),
                "conservative_support_count": integer(row["conservative_support_count"]),
                "aggregate_acat_p": number(row["aggregate_acat_p"]),
                "aggregate_acat_q": q_value,
                "negative_log10_aggregate_acat_q": -math.log10(q_value),
                "capped_negative_log10_aggregate_acat_q": min(-math.log10(q_value), evidence_cap),
                "stability_assessable_repetitions": integer(row["stability_assessable_repetitions"]),
                "stability_nominal_fraction": number(row["stability_nominal_fraction"]),
                "stability_q_fraction": number(row["stability_q_fraction"]),
                "stability_candidate_fraction": number(row["stability_candidate_fraction"]),
                "stability_worst_rank": number(row["stability_worst_rank"]),
                "stability_assessable": assessable,
                "is_core_mito": truth(row["is_core_mito"]),
                "extended_reference_member": truth(row["extended_reference_member"]),
            }
        )

    detail_map = {(row["broad_network"], row["current_symbol"]): row for row in detail_rows}
    plot_rows: list[dict[str, Any]] = []
    for summary in summary_rows:
        gene = summary["current_symbol"]
        for network_index, network in enumerate(NETWORK_ORDER, start=1):
            key = (network, gene)
            detail = detail_map.get(key)
            passing = detail is not None
            displayed = key in displayed_keys
            plot_rows.append(
                {
                    "schema_version": f"{SCHEMA}_plot_data_v1",
                    "figure_id": FIGURE_ID,
                    "case_id": CASE_ID,
                    "atlas_display_order": summary["atlas_display_order"],
                    "current_symbol": gene,
                    "network_order": network_index,
                    "broad_network": network,
                    "network_label": NETWORK_LABELS[network],
                    "network_color": NETWORK_COLORS[network],
                    "tile_status": (
                        "circle_displayed"
                        if displayed
                        else "passing_not_circle_displayed"
                        if passing
                        else "no_passing_context"
                    ),
                    "passing_context": passing,
                    "circle_displayed": displayed,
                    "within_case_rank": detail["within_case_rank"] if detail else None,
                    "aggregate_acat_q": detail["aggregate_acat_q"] if detail else None,
                    "negative_log10_aggregate_acat_q": (
                        detail["negative_log10_aggregate_acat_q"] if detail else None
                    ),
                    "capped_negative_log10_aggregate_acat_q": (
                        detail["capped_negative_log10_aggregate_acat_q"] if detail else None
                    ),
                    "extended_reference_member": summary["extended_reference_member"],
                }
            )

    selected_test_rows = sum(row["explicitly_tested_run_count"] for row in summary_rows)
    selected_significant_rows = sum(row["significant_kda_run_count"] for row in summary_rows)
    selected_support_rows = sum(row["conservative_supporting_run_count"] for row in summary_rows)
    require(selected_test_rows == EXPECTED_SELECTED_TEST_ROWS, "Selected tested-run total changed")
    require(selected_significant_rows == EXPECTED_SELECTED_SIGNIFICANT_ROWS, "Selected significant-run total changed")
    require(selected_support_rows == EXPECTED_SELECTED_SUPPORT_ROWS, "Selected support-run total changed")

    return {
        "input_path": input_path,
        "input_sha256": sha256_file(input_path),
        "input_rows": row_count,
        "input_columns": EXPECTED_INPUT_COLUMNS,
        "run_count": len(run_ids),
        "all_gene_count": len(all_genes),
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "plot_rows": plot_rows,
        "displayed_contexts": len(displayed_keys),
        "passing_contexts": len(passing_keys),
        "selected_test_rows": selected_test_rows,
        "selected_significant_rows": selected_significant_rows,
        "selected_support_rows": selected_support_rows,
        "evidence_cap": evidence_cap,
    }


def configure_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 7,
            "axes.titlesize": 10,
            "svg.hashsalt": SCHEMA,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "pdf.compression": 9,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def contrast_text(color: Any) -> str:
    red, green, blue, _ = matplotlib.colors.to_rgba(color)
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "white" if luminance < 0.48 else TEXT


def panel_title(ax: plt.Axes, letter: str, title: str, subtitle: str) -> None:
    ax.text(-0.01, 1.045, letter, transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")
    ax.text(0.055, 1.045, title, transform=ax.transAxes, fontsize=10.5, fontweight="bold", va="bottom")
    ax.text(0.055, 1.006, subtitle, transform=ax.transAxes, fontsize=7.2, color=MID, va="bottom")


def render_panel_a(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    summary = bundle["summary_rows"]
    plot_rows = bundle["plot_rows"]
    evidence_cap = bundle["evidence_cap"]
    cmap = matplotlib.colormaps["cividis"]
    ax.set_xlim(-1.30, 7.50)
    ax.set_ylim(15.9, -2.20)
    ax.axis("off")
    panel_title(
        ax,
        "A",
        "Network evidence matrix",
        "Tile number = within-network non-MT-driver rank",
    )

    for row in plot_rows:
        x = row["network_order"] - 1
        y = row["atlas_display_order"] - 1
        passing = row["passing_context"]
        displayed = row["circle_displayed"]
        if passing:
            score = row["capped_negative_log10_aggregate_acat_q"]
            fill = cmap(max(0.0, min(1.0, score / evidence_cap)))
        else:
            fill = EMPTY
        border = "#202020" if displayed else "#666666" if passing else "#D6D6D6"
        linestyle = "--" if passing and not displayed else "-"
        linewidth = 1.2 if displayed else 0.75
        ax.add_patch(
            mpatches.Rectangle(
                (x - 0.42, y - 0.34),
                0.84,
                0.68,
                facecolor=fill,
                edgecolor=border,
                linewidth=linewidth,
                linestyle=linestyle,
            )
        )
        if passing:
            ax.text(
                x,
                y,
                str(row["within_case_rank"]),
                fontsize=7.1,
                fontweight="bold",
                color=contrast_text(fill),
                ha="center",
                va="center",
            )

    for row in summary:
        y = row["atlas_display_order"] - 1
        ax.text(-0.57, y, row["current_symbol"], fontsize=7.6, fontweight="bold", ha="right", va="center")
        if row["extended_reference_member"]:
            ax.scatter([-0.44], [y], marker="D", s=15, color="#111111", zorder=3)

    for index, network in enumerate(NETWORK_ORDER):
        ax.plot([index - 0.42, index + 0.42], [-0.55, -0.55], color=NETWORK_COLORS[network], lw=4, solid_capstyle="round")
        ax.text(index, -0.72, NETWORK_LABELS[network], fontsize=6.6, fontweight="bold", rotation=47, ha="left", va="bottom")

    gradient_start, gradient_end = -0.25, 2.55
    for index in range(70):
        fraction = index / 69
        x0 = gradient_start + fraction * (gradient_end - gradient_start)
        x1 = gradient_start + (index + 1) / 70 * (gradient_end - gradient_start)
        ax.add_patch(
            mpatches.Rectangle(
                (x0, 15.05),
                x1 - x0,
                0.22,
                facecolor=cmap(fraction),
                edgecolor="none",
            )
        )
    ax.add_patch(mpatches.Rectangle((gradient_start, 15.05), gradient_end - gradient_start, 0.22, fill=False, edgecolor="#555555", linewidth=0.7))
    ax.text((gradient_start + gradient_end) / 2, 14.85, "capped −log10(ACAT q)", fontsize=6.8, fontweight="bold", ha="center")
    ax.text(gradient_start, 15.43, "0", fontsize=6.5, ha="left")
    ax.text(gradient_end, 15.43, f"{evidence_cap:g}", fontsize=6.5, ha="right")

    ax.add_patch(mpatches.Rectangle((3.0, 15.02), 0.30, 0.28, facecolor="white", edgecolor="#202020", linewidth=1.2))
    ax.text(3.38, 15.16, "circle top five", fontsize=6.6, va="center")
    ax.add_patch(mpatches.Rectangle((4.72, 15.02), 0.30, 0.28, facecolor="white", edgecolor="#666666", linewidth=0.8, linestyle="--"))
    ax.text(5.10, 15.16, "passing, below cap", fontsize=6.6, va="center")
    ax.scatter([3.0], [15.67], marker="D", s=15, color="#111111")
    ax.text(3.18, 15.67, "broader mitochondrial reference", fontsize=6.6, va="center")


def draw_measure(
    ax: plt.Axes,
    y: float,
    start: float,
    width: float,
    value: float,
    maximum: float,
    label: str,
    *,
    color: str = "#252525",
) -> None:
    line_end = start + width * 0.68
    point = start + width * 0.68 * max(0.0, min(1.0, value / maximum))
    ax.plot([start, line_end], [y, y], color="#D2D6D9", lw=1.1, solid_capstyle="round")
    ax.plot([start, point], [y, y], color=color, lw=2.3, solid_capstyle="round")
    ax.scatter([point], [y], s=18, facecolor="white", edgecolor=color, linewidth=0.9, zorder=3)
    ax.text(start + width, y, label, fontsize=6.8, fontweight="bold", ha="right", va="center", color=TEXT)


def render_panel_b(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    summary = bundle["summary_rows"]
    ax.set_xlim(-0.05, 6.60)
    ax.set_ylim(15.9, -2.20)
    ax.axis("off")
    panel_title(
        ax,
        "B",
        "Run occurrence and evidence breadth",
        "Run counts use all included KDA calls in which the gene was explicitly tested",
    )
    for y in range(15):
        ax.plot([-0.05, 6.55], [y, y], color=GRID, lw=0.45, zorder=0)

    starts = [0.00, 1.16, 2.32, 3.38, 4.42, 5.45]
    widths = [1.05, 1.05, 0.95, 0.93, 0.92, 0.92]
    support_fine_max = max(row["supporting_fine_cell_type_count"] for row in summary)
    headers = [
        "Significant KDA\nruns / tested",
        "Conservative\nsupport / tested",
        f"Supporting fine\ncell types\n(observed range\n1–{support_fine_max})",
        "Passing\nnetworks\n(max 7)",
        "Sex/APOE\ngroups\n(max 6)",
        "AD\ndirections\n(max 2)",
    ]
    for start, width, header in zip(starts, widths, headers):
        ax.text(start + width / 2, -0.72, header, fontsize=6.1, fontweight="bold", ha="center", va="bottom", linespacing=1.12)

    for row in summary:
        y = row["atlas_display_order"] - 1
        tested = row["explicitly_tested_run_count"]
        draw_measure(
            ax,
            y,
            starts[0],
            widths[0],
            row["significant_kda_run_count"],
            max(item["significant_kda_run_count"] for item in summary),
            f"{row['significant_kda_run_count']}/{tested}",
            color="#0072B2",
        )
        draw_measure(
            ax,
            y,
            starts[1],
            widths[1],
            row["conservative_supporting_run_count"],
            max(item["conservative_supporting_run_count"] for item in summary),
            f"{row['conservative_supporting_run_count']}/{tested}",
            color="#009E73",
        )
        draw_measure(ax, y, starts[2], widths[2], row["supporting_fine_cell_type_count"], support_fine_max, str(row["supporting_fine_cell_type_count"]))
        draw_measure(ax, y, starts[3], widths[3], row["passing_broad_network_count"], 7, str(row["passing_broad_network_count"]))
        draw_measure(ax, y, starts[4], widths[4], row["supporting_group_count"], 6, str(row["supporting_group_count"]))
        draw_measure(ax, y, starts[5], widths[5], row["supporting_direction_count"], 2, str(row["supporting_direction_count"]))

    ax.text(
        0.0,
        15.45,
        "Significant KDA: returned significant by call_key_drivers().\n"
        "Conservative support: ≥2 other query genes, enrichment >1, and run q ≤0.05.",
        fontsize=6.1,
        color=MID,
        ha="left",
        va="center",
        linespacing=1.15,
    )


def render_panel_c(ax: plt.Axes, bundle: Mapping[str, Any]) -> None:
    details = bundle["detail_rows"]
    ax.set_xlim(-0.05, 3.30)
    ax.set_ylim(15.9, -2.20)
    ax.axis("off")
    panel_title(
        ax,
        "C",
        "Network stability",
        "Leave-one-fine-cell-type diagnostics",
    )
    for y in range(15):
        ax.plot([-0.05, 3.25], [y, y], color=GRID, lw=0.45, zorder=0)

    retention_start, retention_end = 0.05, 1.30
    rank_start, rank_end = 1.82, 3.17
    for x in (retention_start, retention_end, rank_start, rank_end):
        ax.plot([x, x], [-0.05, 14.55], color="#B8BEC3", lw=0.7)
    retention_reference = retention_start + 0.8 * (retention_end - retention_start)
    rank_reference = rank_start + (5 - 1) / (25 - 1) * (rank_end - rank_start)
    ax.plot([retention_reference, retention_reference], [-0.05, 14.55], color="#92999F", lw=0.8, linestyle=":")
    ax.plot([rank_reference, rank_reference], [-0.05, 14.55], color="#92999F", lw=0.8, linestyle=":")
    ax.text((retention_start + retention_end) / 2, -0.72, "Candidate retention\n(0–1)", fontsize=6.5, fontweight="bold", ha="center", va="bottom")
    ax.text((rank_start + rank_end) / 2, -0.72, "Worst rank\n(cap 25; lower better)", fontsize=6.5, fontweight="bold", ha="center", va="bottom")

    for row in details:
        jitter = (row["network_order"] - 4) * 0.035
        y = row["atlas_display_order"] - 1 + jitter
        color = row["network_color"]
        if row["stability_assessable"]:
            retention = row["stability_candidate_fraction"]
            worst_rank = min(row["stability_worst_rank"], 25)
            retention_x = retention_start + retention * (retention_end - retention_start)
            rank_x = rank_start + (worst_rank - 1) / (25 - 1) * (rank_end - rank_start)
            ax.scatter([retention_x], [y], s=23, facecolor=color, edgecolor="#303030", linewidth=0.6, zorder=3)
            ax.scatter([rank_x], [y], s=23, facecolor=color, edgecolor="#303030", linewidth=0.6, zorder=3)
        else:
            ax.scatter([retention_start, rank_start], [y, y], marker="x", s=22, color=color, linewidth=1.0, zorder=3)

    for value in (0, 0.5, 1):
        x = retention_start + value * (retention_end - retention_start)
        ax.text(x, 15.05, f"{value:g}", fontsize=6.3, ha="center")
    for value in (1, 5, 10, 15, 20, 25):
        x = rank_start + (value - 1) / (25 - 1) * (rank_end - rank_start)
        ax.text(x, 15.05, str(value), fontsize=6.1, ha="center")
    ax.text(0.02, 15.43, "Colors match Panel A.\n× = stability not assessable.", fontsize=6.1, color=MID, ha="left", linespacing=1.15)


def render_figure(bundle: Mapping[str, Any], width: float, height: float) -> plt.Figure:
    configure_style()
    fig = plt.figure(figsize=(width, height), facecolor="white")
    fig.text(0.018, 0.985, "Evidence atlas for selected non-MT key drivers", fontsize=14, fontweight="bold", ha="left", va="top", color=TEXT)
    fig.text(0.018, 0.947, "Drivers outside the 1,136-gene core MitoCarta inventory", fontsize=9.5, color=MID, ha="left", va="top")
    fig.text(
        0.018,
        0.918,
        f"15 selected genes  •  21 circle-displayed contexts  •  22 total passing contexts  •  {bundle['run_count']} included KDA calls",
        fontsize=7.5,
        color=MID,
        ha="left",
        va="top",
    )
    grid = fig.add_gridspec(
        1,
        3,
        left=0.025,
        right=0.992,
        bottom=0.06,
        top=0.835,
        wspace=0.055,
        width_ratios=[4.25, 4.90, 2.85],
    )
    render_panel_a(fig.add_subplot(grid[0, 0]), bundle)
    render_panel_b(fig.add_subplot(grid[0, 1]), bundle)
    render_panel_c(fig.add_subplot(grid[0, 2]), bundle)
    return fig


def render_images(
    fig: plt.Figure,
    directory: Path,
    width: float,
    height: float,
    dpi: int,
) -> list[Path]:
    paths: list[Path] = []
    for extension in ("svg", "pdf", "png"):
        final = directory / f"{FIGURE_ID}.{extension}"
        temporary = directory / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Creator": "Phase 18 non-MT evidence-atlas renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {
                "Creator": "Phase 18 non-MT evidence-atlas renderer",
                "Date": None,
            }
        else:
            metadata = {"Software": "Phase 18 non-MT evidence-atlas renderer"}
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


CAPTION = """# Phase 18 non-MT-driver evidence-atlas caption

**Evidence atlas for the 15 non-MT genes displayed in the Phase 18 circular figure.** **A,** Each tile represents one gene × broad-network context. Tile fill is capped network-specific −log10 aggregate ACAT q, the number is the within-network non-MT-driver rank, solid borders denote contexts displayed under the five-per-network cap, and the dashed border denotes the additional passing RPS15 context in excitatory neurons. **B,** Significant KDA runs count included `call_key_drivers()` calls in which `significant_by_call_key_drivers = TRUE`; each label reports significant runs divided by runs in which the gene was explicitly tested. Conservative-support runs are the subset also satisfying at least two other query genes, fold enrichment greater than one, and within-run q ≤ 0.05. Additional tracks show the number of conservatively supporting fine cell types, passing broad networks, primary sex/APOE groups, and AD directions. These Panel B run and breadth summaries use all included calls in which each selected gene was explicitly tested, not only its final passing network contexts. **C,** Candidate-retention fractions and worst ranks under leave-one-fine-cell-type omission are network-specific stability diagnostics and did not determine candidate selection.

Non-MT means outside the fixed 1,136-gene core MitoCarta inventory, not proven absence of mitochondrial function. The broader mitochondrial-reference annotation is secondary and does not alter the class. The top-five rule is a display cap, not an evidence threshold. Runs within a broad cell type reuse one Bayesian network and are repeated evidence contexts rather than independent external replications. Gene order is descriptive, and Bayesian-network key-driver association is not experimental proof of causal regulation.
"""


def methods_text(dpi: int, width: float, height: float, evidence_cap: float) -> str:
    return f"""# Methods

The atlas was generated directly from `call_key_driver_returns.tsv` with schema `{INPUT_SCHEMA}`. The renderer required 95,557 explicit gene × run rows, 161 included KDA calls, one unique `kda_run_id + key_driver` row, and constant aggregate fields within each `broad_network + key_driver + case_id` unit. The selected-gene universe was the 15 unique `non_mt_driver` symbols with `top5_display = TRUE`; these yielded 21 displayed contexts and 22 passing contexts after retaining every `terminal_candidate_status = driver_candidate` row for those genes.

Panel A copies the stored network-specific aggregate ACAT q values and ranks. Its color scale is capped at −log10(q) = {evidence_cap:g}. Panel B counts all explicit rows for each selected gene across the 161 included calls. A significant KDA run has `significant_by_call_key_drivers = TRUE`. A conservative-support run has `conservative_support = TRUE`; all such rows were required to be a subset of significant KDA returns. Fine-cell-type, primary-group, and direction breadth are exact set unions across conservative-support rows. Passing broad-network count is the number of selected-gene aggregate contexts with `terminal_candidate_status = driver_candidate`.

Panel C copies the stored leave-one-fine-cell-type stability summaries for every passing gene-network context. Candidate retention is the fraction of assessable omissions retaining `driver_candidate` status. Worst rank is the largest stored within-class rank across assessable omissions. Contexts with no assessable repetitions are marked with ×. Stability diagnostics are descriptive and were not used to change selection.

All plotted values are deterministic saved results, so uncertainty intervals and new hypothesis tests are not applicable. The figure uses a cividis evidence scale, Okabe–Ito network colors, redundant text/border encodings, and a sans-serif typeface. SVG and PDF are vector outputs; the PNG is {width:g} × {height:g} inches at {dpi} DPI.
"""


def image_checks(
    images: Sequence[Path],
    width: float,
    height: float,
    dpi: int,
) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in images}
    svg_text = lookup[".svg"].read_text(encoding="utf-8", errors="replace")
    with lookup[".pdf"].open("rb") as handle:
        pdf_header = handle.read(5)
    with Image.open(lookup[".png"]) as image:
        dimensions = image.size
        dpi_metadata = image.info.get("dpi", (math.nan, math.nan))
    expected_dimensions = (round(width * dpi), round(height * dpi))
    return [
        check_record("three_image_formats", set(lookup) == {".svg", ".pdf", ".png"}, "|".join(sorted(lookup)), ".pdf|.png|.svg"),
        check_record("images_nonempty", all(path.stat().st_size > 0 for path in images), sum(path.stat().st_size > 0 for path in images), 3),
        check_record("svg_vector_content", "<svg" in svg_text.lower() and "data:image" not in svg_text.lower(), "vector SVG", "vector SVG"),
        check_record("svg_text_preserved", "<text" in svg_text.lower(), "<text present", "<text present"),
        check_record("pdf_header", pdf_header == b"%PDF-", pdf_header.decode("latin1"), "%PDF-"),
        check_record("png_dimensions", dimensions == expected_dimensions, f"{dimensions[0]}x{dimensions[1]}", f"{expected_dimensions[0]}x{expected_dimensions[1]}"),
        check_record("png_dpi", all(math.isfinite(value) and abs(value - dpi) <= 1 for value in dpi_metadata), f"{dpi_metadata[0]:.2f}|{dpi_metadata[1]:.2f}", f"{dpi}|{dpi}"),
    ]


def build_checks(
    bundle: Mapping[str, Any],
    images: Sequence[Path],
    width: float,
    height: float,
    dpi: int,
    visual_review_status: str,
) -> list[dict[str, Any]]:
    summary = bundle["summary_rows"]
    details = bundle["detail_rows"]
    plots = bundle["plot_rows"]
    checks = [
        check_record("input_schema", True, INPUT_SCHEMA, INPUT_SCHEMA),
        check_record("input_rows", bundle["input_rows"] == EXPECTED_INPUT_ROWS, bundle["input_rows"], EXPECTED_INPUT_ROWS),
        check_record("input_columns", bundle["input_columns"] == EXPECTED_INPUT_COLUMNS, bundle["input_columns"], EXPECTED_INPUT_COLUMNS),
        check_record("included_runs", bundle["run_count"] == EXPECTED_RUNS, bundle["run_count"], EXPECTED_RUNS),
        check_record("all_tested_genes", bundle["all_gene_count"] == EXPECTED_ALL_GENES, bundle["all_gene_count"], EXPECTED_ALL_GENES),
        check_record("selected_genes", len(summary) == 15, len(summary), 15),
        check_record("displayed_contexts", bundle["displayed_contexts"] == 21, bundle["displayed_contexts"], 21),
        check_record("passing_contexts", bundle["passing_contexts"] == 22, bundle["passing_contexts"], 22),
        check_record("panel_a_grid", len(plots) == 105, len(plots), 105),
        check_record("panel_a_keys", len({(row["current_symbol"], row["broad_network"]) for row in plots}) == 105, len({(row["current_symbol"], row["broad_network"]) for row in plots}), 105),
        check_record("selected_tested_runs", bundle["selected_test_rows"] == EXPECTED_SELECTED_TEST_ROWS, bundle["selected_test_rows"], EXPECTED_SELECTED_TEST_ROWS),
        check_record("selected_significant_runs", bundle["selected_significant_rows"] == EXPECTED_SELECTED_SIGNIFICANT_ROWS, bundle["selected_significant_rows"], EXPECTED_SELECTED_SIGNIFICANT_ROWS),
        check_record("selected_support_runs", bundle["selected_support_rows"] == EXPECTED_SELECTED_SUPPORT_ROWS, bundle["selected_support_rows"], EXPECTED_SELECTED_SUPPORT_ROWS),
        check_record("support_subset", all(row["conservative_supporting_run_count"] <= row["significant_kda_run_count"] <= row["explicitly_tested_run_count"] for row in summary), "all", "support <= significant <= tested"),
        check_record("candidate_q_values", all(0 < row["aggregate_acat_q"] <= 0.05 for row in details), "all", "0 < q <= 0.05"),
        check_record("top_five_ranks", all((not row["circle_displayed"]) or row["within_case_rank"] <= 5 for row in details), "all", "displayed rank <=5"),
        check_record("nonpassing_tiles_empty", all(row["passing_context"] or row["aggregate_acat_q"] is None for row in plots), "all", "all"),
        check_record("colorblind_safe", True, "cividis + Okabe-Ito + labels", "colorblind-safe redundant encoding"),
        check_record("minimum_text", True, ">=6.1 pt; primary labels >=7 pt", ">=6 pt"),
        check_record("visual_review_complete", visual_review_status == "complete", visual_review_status, "complete", "Manual final-size color and grayscale review.", blocking=False),
    ]
    checks.extend(image_checks(images, width, height, dpi))
    return checks


def manifest_rows(
    bundle: Mapping[str, Any],
    width: float,
    height: float,
    dpi: int,
    visual_review_status: str,
) -> list[dict[str, Any]]:
    fields = [
        ("figure_id", FIGURE_ID),
        ("case_id", CASE_ID),
        ("input_path", str(bundle["input_path"])),
        ("input_sha256", bundle["input_sha256"]),
        ("renderer", str(Path(__file__).resolve())),
        ("renderer_sha256", sha256_file(Path(__file__).resolve())),
        ("figure_width_inches", width),
        ("figure_height_inches", height),
        ("png_dpi", dpi),
        ("evidence_cap", bundle["evidence_cap"]),
        ("continuous_palette", "cividis"),
        ("network_palette", "Okabe-Ito"),
        ("selected_gene_count", 15),
        ("circle_display_context_count", 21),
        ("passing_context_count", 22),
        ("included_kda_calls", bundle["run_count"]),
        ("panel_b_scope", "all explicit selected-gene rows across included calls"),
        ("visual_review_status", visual_review_status),
        ("timestamp_utc", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())),
    ]
    return [
        {
            "schema_version": f"{SCHEMA}_manifest_v1",
            "field_order": index,
            "field": field,
            "value": value,
        }
        for index, (field, value) in enumerate(fields, start=1)
    ]


def artifact_rows(
    bundle: Mapping[str, Any],
    staging: Path,
) -> list[dict[str, Any]]:
    rows = [
        {
            "schema_version": f"{SCHEMA}_artifacts_v1",
            "artifact_role": "input",
            "artifact_id": bundle["input_path"].name,
            "path": str(bundle["input_path"]),
            "bytes": bundle["input_path"].stat().st_size,
            "sha256": bundle["input_sha256"],
        },
        {
            "schema_version": f"{SCHEMA}_artifacts_v1",
            "artifact_role": "script",
            "artifact_id": Path(__file__).name,
            "path": str(Path(__file__).resolve()),
            "bytes": Path(__file__).stat().st_size,
            "sha256": sha256_file(Path(__file__).resolve()),
        },
    ]
    for name in [*IMAGE_FILES, SUMMARY_FILE, DETAIL_FILE, PLOT_FILE, CAPTION_FILE, METHODS_FILE, MANIFEST_FILE, CHECKS_FILE]:
        path = staging / name
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_role": "output",
                "artifact_id": name,
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def validate_output(directory: Path, expected_visual_status: str | None = None) -> None:
    require(directory.exists() and directory.is_dir(), f"Missing output directory: {directory}")
    files = sorted(path.name for path in directory.iterdir() if path.is_file())
    require(files == sorted(DECLARED_OUTPUTS), f"Output declaration mismatch: {files}")
    status_rows = read_tsv(directory / STATUS_FILE)
    require(len(status_rows) == 1, "Status table must contain one row")
    status = status_rows[0]
    if expected_visual_status is not None:
        require(status["visual_review_status"] == expected_visual_status, "Visual status changed")
    expected_validation = "validated_complete" if status["visual_review_status"] == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Unexpected validation status")
    checks = read_tsv(directory / CHECKS_FILE)
    blocking_failures = [row["check_id"] for row in checks if truth(row["blocking"]) and not truth(row["passed"])]
    require(not blocking_failures, f"Blocking checks failed: {', '.join(blocking_failures)}")
    if status["visual_review_status"] == "complete":
        require(all(truth(row["passed"]) for row in checks), "Completed package has a failed check")
    image_check_rows = image_checks(
        [directory / name for name in IMAGE_FILES],
        float(status["figure_width_inches"]),
        float(status["figure_height_inches"]),
        integer(status["png_dpi"]),
    )
    require(all(truth(row["passed"]) for row in image_check_rows), "Image validation failed")
    artifacts = read_tsv(directory / ARTIFACTS_FILE)
    for row in artifacts:
        path = Path(row["path"]) if Path(row["path"]).is_absolute() else directory / row["artifact_id"]
        require(path.exists(), f"Recorded artifact missing: {path}")
        require(path.stat().st_size == integer(row["bytes"]), f"Artifact bytes changed: {path}")
        require(sha256_file(path) == row["sha256"], f"Artifact hash changed: {path}")
    print(f"Validated Phase 18 non-MT evidence atlas: {directory}")


def publish(
    input_path: Path,
    output_dir: Path,
    width: float,
    height: float,
    dpi: int,
    evidence_cap: float,
    visual_review_status: str,
) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".phase18_non_mt_atlas.staging.", dir=output_dir.parent))
    try:
        bundle = load_bundle(input_path, evidence_cap)
        write_tsv(staging / SUMMARY_FILE, bundle["summary_rows"])
        write_tsv(staging / DETAIL_FILE, bundle["detail_rows"])
        write_tsv(staging / PLOT_FILE, bundle["plot_rows"])
        write_text(staging / CAPTION_FILE, CAPTION)
        write_text(staging / METHODS_FILE, methods_text(dpi, width, height, evidence_cap))
        figure = render_figure(bundle, width, height)
        images = render_images(figure, staging, width, height, dpi)
        checks = build_checks(bundle, images, width, height, dpi, visual_review_status)
        write_tsv(staging / CHECKS_FILE, checks)
        write_tsv(staging / MANIFEST_FILE, manifest_rows(bundle, width, height, dpi, visual_review_status))
        write_tsv(staging / ARTIFACTS_FILE, artifact_rows(bundle, staging))
        blocking_failures = sum(truth(row["blocking"]) and not truth(row["passed"]) for row in checks)
        pending_nonblocking = sum(not truth(row["blocking"]) and not truth(row["passed"]) for row in checks)
        require(blocking_failures == 0, "A blocking atlas check failed")
        validation_status = (
            "validated_complete"
            if visual_review_status == "complete" and pending_nonblocking == 0
            else "awaiting_visual_review"
        )
        status = {
            "schema_version": f"{SCHEMA}_status_v1",
            "figure_id": FIGURE_ID,
            "validation_status": validation_status,
            "circle_genes": len(bundle["summary_rows"]),
            "circle_display_contexts": bundle["displayed_contexts"],
            "passing_contexts": bundle["passing_contexts"],
            "panel_a_grid_rows": len(bundle["plot_rows"]),
            "selected_tested_runs": bundle["selected_test_rows"],
            "selected_significant_runs": bundle["selected_significant_rows"],
            "selected_support_runs": bundle["selected_support_rows"],
            "figure_width_inches": width,
            "figure_height_inches": height,
            "png_dpi": dpi,
            "declared_outputs": len(DECLARED_OUTPUTS),
            "automated_checks": len(checks),
            "automated_checks_passed": sum(truth(row["passed"]) for row in checks),
            "failed_blocking_checks": blocking_failures,
            "visual_review_status": visual_review_status,
            "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        write_tsv(staging / STATUS_FILE, [status])
        validate_output(staging, visual_review_status)

        output_dir.mkdir(parents=True, exist_ok=True)
        for name in DECLARED_OUTPUTS:
            os.replace(staging / name, output_dir / name)
        shutil.rmtree(staging, ignore_errors=True)
        validate_output(output_dir, visual_review_status)
        print(f"Published revised atlas: {output_dir}")
        print("Panel B totals: 830 tested gene-run rows; 149 significant KDA returns; 135 conservative-support runs")
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
    publish(
        input_path,
        output_dir,
        args.width_inches,
        args.height_inches,
        args.png_dpi,
        args.evidence_cap,
        args.visual_review_status,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
