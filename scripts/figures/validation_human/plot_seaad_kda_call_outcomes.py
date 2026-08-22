#!/usr/bin/env python3
"""Render slide-ready SEA-AD KDA call outcomes and selection sequence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_kda_call_outcomes_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_kda_call_outcomes_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 16,
        "axes.labelsize": 16,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "svg.fonttype": "none",
        "svg.hashsalt": "seaad_kda_call_outcomes_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _slide_figure_common import (  # noqa: E402
    as_int,
    build_artifacts,
    check_record,
    image_checks,
    one_row,
    read_tsv,
    render_three_formats,
    require,
    require_columns,
    sha256_file,
    sha256_strings,
    truth,
    validate_artifacts,
    validate_source_artifact,
    visible_text_metadata,
    write_text,
    write_tsv,
)


SCHEMA = "seaad_kda_call_outcomes_figure_v1"
PLOT_SCHEMA = "seaad_kda_call_outcomes_plot_data_v1"
FIGURE_ID = "seaad_kda_call_outcomes"
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 5.3
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 2_385
MINIMUM_FONT_PT = 16.0

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
DIRECTION_ORDER = ["up", "down"]
DIRECTION_LABELS = {"up": "Dementia-up", "down": "Dementia-down"}
DIRECTION_MARKERS = {"up": "^", "down": "v"}

EXPECTED_OUTCOMES = {
    ("Astrocytes", "up"): (0, 1),
    ("Astrocytes", "down"): (0, 0),
    ("Excitatory_neurons", "up"): (4, 6),
    ("Excitatory_neurons", "down"): (10, 0),
    ("Inhibitory_neurons", "up"): (4, 2),
    ("Inhibitory_neurons", "down"): (8, 2),
    ("Microglia", "up"): (0, 1),
    ("Microglia", "down"): (0, 0),
    ("OPCs", "up"): (0, 0),
    ("OPCs", "down"): (0, 0),
    ("Oligodendrocytes", "up"): (1, 1),
    ("Oligodendrocytes", "down"): (2, 0),
    ("Vasculature_cells", "up"): (0, 0),
    ("Vasculature_cells", "down"): (0, 0),
}
EXPECTED_GROUP_CALLS = {"M_e33": 40, "F_e33": 1, "F_e4": 1}
SELECTION_STAGES = [
    ("completed_calls", 42, "completed KDA calls"),
    ("calls_with_return", 29, "calls with ≥1 significant return"),
    ("significant_rows", 208, "significant return rows"),
    ("aggregate_candidates", 38_788, "aggregate candidate units"),
    ("selected_units", 13, "units passed all gates"),
]
METHOD_STEPS = [
    "run BH",
    "conservative support",
    "coverage ≥0.80",
    "ACAT",
    "network BH",
    "class rank",
]

INPUT_PATHS = {
    "vh10b_status": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv",
    "vh10b_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/artifacts.tsv",
    "run_qc": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/run_qc.tsv",
    "vh10c_status": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv",
    "vh10c_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/artifacts.tsv",
    "selection_checks": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/selection_checks.tsv",
}
EXPECTED_INPUT_SHA256 = {
    "vh10b_status": "db308f382993c033b6126e996e860f8bcdb3a5d826e2aeea2daf54511e1d4e92",
    "vh10b_artifacts": "d3b012e7b9cf383bf489d259a2f3bcfbbd26f5682a2362efd9422f5d0e3d58c1",
    "run_qc": "a9f16f073075fb4cd0e2ef259fa73a489eb4aa3b2c10504ca2b9fb98dbb570e0",
    "vh10c_status": "c12e21e961c670d69b04789b149fece950c036c68187c75588e19838f91a7023",
    "vh10c_artifacts": "2fe7d1af68e3e4971e19516706d496118719d3422cf198ef010e1000b83b52c1",
    "selection_checks": "eda96be41bc9af33257ba447ed623c29e0ffcf521ce1fd77df6b5cd0fff5ae97",
}

OUTPUT_FILES = [
    f"{FIGURE_ID}.png",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_artifacts.tsv",
    f"{FIGURE_ID}_status.tsv",
]
PAYLOAD_FILES = OUTPUT_FILES[:-2]

TEXT = "#20252A"
MID = "#5F6770"
NAVY = "#0F233D"
SEAAD = "#009E73"
ORANGE = "#E69F00"
NO_RETURN = "#D9DDE1"
NO_RETURN_EDGE = "#69737D"
WHITE = "#FFFFFF"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output-root",
        default=f"results/figures/validation_human/{FIGURE_ID}",
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status", choices=("pending", "complete"), default="pending"
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-output")
    args = parser.parse_args(argv)
    if args.png_dpi != DEFAULT_PNG_DPI:
        parser.error(f"--png-dpi must equal {DEFAULT_PNG_DPI}")
    return args


def load_bundle(project_root: Path) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    frames: dict[str, pd.DataFrame] = {}
    digests: dict[str, str] = {}
    for key, relative in INPUT_PATHS.items():
        path = project_root / relative
        digest = sha256_file(path)
        require(digest == EXPECTED_INPUT_SHA256[key], f"Frozen SHA-256 changed for {relative}")
        frames[key] = read_tsv(path)
        digests[relative] = digest

    status_b = one_row(frames["vh10b_status"], "VH10B status")
    status_c = one_row(frames["vh10c_status"], "VH10C status")
    for label, status in (("VH10B", status_b), ("VH10C", status_c)):
        require(status["validation_status"] == "validated_complete", f"{label} is not validated_complete")
        require(str(status["failed_checks"]).strip() == "", f"{label} reports failed checks")
    require(as_int(status_b["active_kda_calls"]) == 42, "Active KDA call count changed")
    require(as_int(status_b["completed_significant_calls"]) == 29, "Calls with return changed")
    require(as_int(status_b["completed_no_significant_calls"]) == 13, "Calls without return changed")
    require(as_int(status_b["significant_return_rows"]) == 208, "Significant return-row count changed")
    require(as_int(status_c["candidate_units"]) == 38_788, "Aggregate candidate-unit count changed")
    require(as_int(status_c["passing_candidate_units"]) == 13, "Passing candidate-unit count changed")
    require(as_int(status_c["selected_top5_units"]) == 13, "Selected display-unit count changed")

    selection_checks = frames["selection_checks"]
    require_columns(selection_checks, ["check", "passed"], "VH10C selection checks")
    require(selection_checks["passed"].map(truth).all(), "VH10C contains a failed selection check")
    validate_source_artifact(
        frames["vh10b_artifacts"], INPUT_PATHS["run_qc"], digests[INPUT_PATHS["run_qc"]]
    )
    validate_source_artifact(
        frames["vh10c_artifacts"],
        INPUT_PATHS["selection_checks"],
        digests[INPUT_PATHS["selection_checks"]],
    )

    runs = frames["run_qc"].copy()
    require_columns(
        runs,
        [
            "kda_run_id",
            "broad_network",
            "signature_group",
            "signature_direction",
            "significant_key_drivers",
            "terminal_status",
        ],
        "KDA run QC",
    )
    require(len(runs) == 42 and not runs["kda_run_id"].duplicated().any(), "KDA run keys changed")
    require(set(runs["broad_network"]).issubset(set(NETWORK_ORDER)), "Unknown KDA broad network")
    direction_map = {"AD_up_mito": "up", "AD_down_mito": "down"}
    require(set(runs["signature_direction"]) == set(direction_map), "KDA signature directions changed")
    runs["direction"] = runs["signature_direction"].map(direction_map)
    runs["significant_return_rows"] = pd.to_numeric(
        runs["significant_key_drivers"], errors="raise"
    ).astype(int)
    runs["has_significant_return"] = runs["significant_return_rows"].gt(0)
    expected_terminal = np.where(
        runs["has_significant_return"], "completed_significant", "completed_no_significant"
    )
    require(np.array_equal(runs["terminal_status"].to_numpy(), expected_terminal), "KDA terminal status disagrees with return count")
    require(int(runs["has_significant_return"].sum()) == 29, "Run table no longer contains 29 calls with returns")
    require(int((~runs["has_significant_return"]).sum()) == 13, "Run table no longer contains 13 calls without returns")
    require(int(runs["significant_return_rows"].sum()) == 208, "Run table no longer sums to 208 return rows")
    group_calls = runs["signature_group"].value_counts().astype(int).to_dict()
    require(group_calls == EXPECTED_GROUP_CALLS, "KDA group distribution changed")

    observed_outcomes: dict[tuple[str, str], tuple[int, int]] = {}
    for network in NETWORK_ORDER:
        for direction in DIRECTION_ORDER:
            cell = runs.loc[
                runs["broad_network"].eq(network) & runs["direction"].eq(direction)
            ]
            observed_outcomes[(network, direction)] = (
                int(cell["has_significant_return"].sum()),
                int((~cell["has_significant_return"]).sum()),
            )
    require(observed_outcomes == EXPECTED_OUTCOMES, "Network-by-direction KDA outcomes changed")

    input_bundle_sha256 = sha256_strings(
        f"{path}\t{digest}" for path, digest in sorted(digests.items())
    )
    return {
        "project_root": project_root,
        "frames": frames,
        "input_digests": digests,
        "input_bundle_sha256": input_bundle_sha256,
        "runs": runs,
        "outcomes": observed_outcomes,
        "candidate_units": as_int(status_c["candidate_units"]),
        "selected_units": as_int(status_c["selected_top5_units"]),
    }


def _empty_record(record_type: str, record_id: str) -> dict[str, Any]:
    return {
        "schema_version": PLOT_SCHEMA,
        "figure_id": FIGURE_ID,
        "record_type": record_type,
        "record_id": record_id,
        "display_order": "",
        "broad_network": "",
        "broad_network_label": "",
        "direction": "",
        "direction_label": "",
        "direction_marker": "",
        "kda_run_id": "",
        "signature_group": "",
        "call_status": "",
        "significant_return_rows": "",
        "with_return_calls": "",
        "without_return_calls": "",
        "total_calls": "",
        "stage_id": "",
        "stage_value": "",
        "stage_label": "",
        "method_step": "",
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    network_rank = {network: index for index, network in enumerate(NETWORK_ORDER)}
    direction_rank = {direction: index for index, direction in enumerate(DIRECTION_ORDER)}
    runs = bundle["runs"].sort_values(
        ["broad_network", "direction", "has_significant_return", "kda_run_id"],
        key=lambda values: (
            values.map(network_rank)
            if values.name == "broad_network"
            else values.map(direction_rank)
            if values.name == "direction"
            else -values.astype(int)
            if values.name == "has_significant_return"
            else values
        ),
        kind="stable",
    )
    cell_offsets: dict[tuple[str, str], int] = {}
    for row in runs.itertuples(index=False):
        key = (row.broad_network, row.direction)
        offset = cell_offsets.get(key, 0)
        cell_offsets[key] = offset + 1
        record = _empty_record("call", f"call::{row.kda_run_id}")
        record.update(
            {
                "display_order": network_rank[row.broad_network] * 20 + direction_rank[row.direction] * 10 + offset,
                "broad_network": row.broad_network,
                "broad_network_label": NETWORK_LABELS[row.broad_network],
                "direction": row.direction,
                "direction_label": DIRECTION_LABELS[row.direction],
                "direction_marker": DIRECTION_MARKERS[row.direction],
                "kda_run_id": row.kda_run_id,
                "signature_group": row.signature_group,
                "call_status": "with_significant_return" if row.has_significant_return else "without_significant_return",
                "significant_return_rows": int(row.significant_return_rows),
            }
        )
        rows.append(record)

    for network_index, network in enumerate(NETWORK_ORDER):
        for direction_index, direction in enumerate(DIRECTION_ORDER):
            with_return, without_return = bundle["outcomes"][(network, direction)]
            record = _empty_record("outcome_cell", f"cell::{network}::{direction}")
            record.update(
                {
                    "display_order": network_index * 2 + direction_index,
                    "broad_network": network,
                    "broad_network_label": NETWORK_LABELS[network],
                    "direction": direction,
                    "direction_label": DIRECTION_LABELS[direction],
                    "direction_marker": DIRECTION_MARKERS[direction],
                    "with_return_calls": with_return,
                    "without_return_calls": without_return,
                    "total_calls": with_return + without_return,
                }
            )
            rows.append(record)

    for index, (stage_id, value, label) in enumerate(SELECTION_STAGES):
        record = _empty_record("selection_stage", f"stage::{stage_id}")
        record.update(
            {
                "display_order": index,
                "stage_id": stage_id,
                "stage_value": value,
                "stage_label": label,
            }
        )
        rows.append(record)
    for index, step in enumerate(METHOD_STEPS):
        record = _empty_record("method_step", f"method::{index + 1}")
        record.update({"display_order": index, "method_step": step})
        rows.append(record)
    frame = pd.DataFrame(rows)
    require(len(frame) == 67, f"Expected 67 plot records, observed {len(frame)}")
    require(frame["record_id"].is_unique, "Plot record IDs are duplicated")
    return frame


def _cell_positions(start_x: float, center_y: float, count: int) -> list[tuple[float, float]]:
    positions: list[tuple[float, float]] = []
    for index in range(count):
        column = index % 5
        row = index // 5
        y = center_y + (0.13 if row == 0 else -0.13)
        positions.append((start_x + column * 0.54, y))
    return positions


def draw_figure(bundle: Mapping[str, Any], plot_data: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    fig.text(0.018, 0.958, "A  KDA call outcomes", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.650, 0.958, "B  Evidence → selection", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.195, 0.877, "● ≥1 return     ○ none     counts: with | none", ha="left", va="center", fontsize=16, color=MID)
    fig.text(0.815, 0.878, "MT queries → assessable network genes", ha="center", va="center", fontsize=16, color=MID)
    fig.text(0.815, 0.831, "drivers classified MT or non-MT", ha="center", va="center", fontsize=16, color=MID)

    matrix_ax = fig.add_axes([0.195, 0.145, 0.435, 0.675])
    matrix_ax.set_xlim(-0.6, 11.4)
    matrix_ax.set_ylim(-0.65, 6.75)
    matrix_ax.set_xticks([])
    y_positions = {network: 6 - index for index, network in enumerate(NETWORK_ORDER)}
    matrix_ax.set_yticks(
        [y_positions[network] for network in NETWORK_ORDER],
        [NETWORK_LABELS[network] for network in NETWORK_ORDER],
    )
    matrix_ax.tick_params(axis="y", length=0, pad=8, labelsize=16)
    for spine in matrix_ax.spines.values():
        spine.set_visible(False)
    for index, network in enumerate(NETWORK_ORDER):
        if index % 2 == 1:
            matrix_ax.axhspan(y_positions[network] - 0.42, y_positions[network] + 0.42, color="#F5F7F8", zorder=0)
    starts = {"up": 0.0, "down": 7.0}
    matrix_ax.text(1.25, 6.62, "▲ Dementia-up", ha="center", va="bottom", fontsize=17, weight="bold", color=TEXT)
    matrix_ax.text(8.25, 6.62, "▼ Dementia-down", ha="center", va="bottom", fontsize=17, weight="bold", color=TEXT)

    calls = plot_data.loc[plot_data["record_type"].eq("call")]
    cells = plot_data.loc[plot_data["record_type"].eq("outcome_cell")]
    for network in NETWORK_ORDER:
        y = y_positions[network]
        for direction in DIRECTION_ORDER:
            start_x = starts[direction]
            cell_calls = calls.loc[
                calls["broad_network"].eq(network) & calls["direction"].eq(direction)
            ].sort_values("display_order")
            positions = _cell_positions(start_x, y, len(cell_calls))
            if cell_calls.empty:
                matrix_ax.text(start_x + 1.08, y, "—", ha="center", va="center", fontsize=18, color="#9AA2AA")
            else:
                for (_, call), (x, dot_y) in zip(cell_calls.iterrows(), positions):
                    filled = call["call_status"] == "with_significant_return"
                    matrix_ax.scatter(
                        [x], [dot_y],
                        marker=DIRECTION_MARKERS[direction], s=88,
                        facecolor=NAVY if filled else NO_RETURN,
                        edgecolor=NAVY if filled else NO_RETURN_EDGE,
                        linewidth=1.1, zorder=4,
                    )
            cell = cells.loc[
                cells["broad_network"].eq(network) & cells["direction"].eq(direction)
            ].iloc[0]
            count_x = start_x + 3.18
            matrix_ax.text(
                count_x, y,
                f"{as_int(cell['with_return_calls'])} | {as_int(cell['without_return_calls'])}",
                ha="center", va="center", fontsize=16, weight="bold", color=TEXT,
            )
    matrix_ax.axvline(5.15, color="#C3C8CD", linewidth=1.0)

    sequence_ax = fig.add_axes([0.655, 0.145, 0.330, 0.650])
    sequence_ax.set_xlim(0, 1)
    sequence_ax.set_ylim(0, 1)
    sequence_ax.axis("off")
    box_y = [0.82, 0.63, 0.44, 0.25, 0.06]
    box_fills = ["#DDF3EB", "#DCEAF3", "#E7EEF5", "#F0F2F4", "#FBE8C7"]
    box_edges = [SEAAD, "#0072B2", "#537A9D", "#737C85", ORANGE]
    for index, ((stage_id, value, label), y, fill, edge) in enumerate(
        zip(SELECTION_STAGES, box_y, box_fills, box_edges)
    ):
        sequence_ax.add_patch(
            mpatches.FancyBboxPatch(
                (0.03, y), 0.94, 0.14,
                boxstyle="round,pad=0.006,rounding_size=0.014",
                facecolor=fill, edgecolor=edge, linewidth=1.5,
            )
        )
        display_label = {
            "calls_with_return": "calls with ≥1\nsignificant return",
            "significant_rows": "significant return\nrows",
            "aggregate_candidates": "aggregate candidate\nunits",
            "selected_units": "units passed\nall gates",
        }.get(stage_id, label)
        sequence_ax.text(0.17, y + 0.070, f"{value:,}", ha="center", va="center", fontsize=20, weight="bold", color=NAVY)
        sequence_ax.text(0.36, y + 0.070, display_label, ha="left", va="center", fontsize=16, linespacing=0.92, color=TEXT)
        if index < len(SELECTION_STAGES) - 1:
            sequence_ax.annotate(
                "", xy=(0.50, box_y[index + 1] + 0.145), xytext=(0.50, y - 0.004),
                arrowprops={"arrowstyle": "-|>", "color": MID, "linewidth": 1.2},
            )
    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.018, 0.018), 0.964, 0.075,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            transform=fig.transFigure, facecolor="#F4F6F7", edgecolor="#AAB1B8", linewidth=1.0,
        )
    )
    fig.text(
        0.50, 0.055,
        "run BH  →  conservative support  →  coverage ≥0.80  →  ACAT  →  network BH  →  class rank",
        ha="center", va="center", fontsize=16, weight="bold", color=TEXT,
    )

    metadata = visible_text_metadata(fig)
    require(metadata["minimum_font_points"] >= MINIMUM_FONT_PT, "A visible label is smaller than 16 pt")
    require(not metadata["canvas_clipped_text"], "Text leaves canvas: " + " | ".join(metadata["canvas_clipped_text"]))
    return fig, metadata


def render_images(
    bundle: Mapping[str, Any], plot_data: pd.DataFrame, staging: Path, dpi: int
) -> tuple[list[Path], dict[str, Any]]:
    fig, metadata = draw_figure(bundle, plot_data)
    paths = render_three_formats(
        fig, staging, FIGURE_ID, dpi=dpi,
        title="SEA-AD KDA call outcomes and selection sequence",
    )
    plt.close(fig)
    return paths, metadata


def build_checks(
    bundle: Mapping[str, Any],
    plot_data: pd.DataFrame,
    image_paths: Sequence[Path],
    render_meta: Mapping[str, Any],
    *,
    dpi: int,
    visual_review_status: str,
) -> pd.DataFrame:
    record = lambda *args, **kwargs: check_record(SCHEMA, FIGURE_ID, *args, **kwargs)
    calls = plot_data.loc[plot_data["record_type"].eq("call")]
    cells = plot_data.loc[plot_data["record_type"].eq("outcome_cell")]
    stages = plot_data.loc[plot_data["record_type"].eq("selection_stage")]
    observed_outcomes = {
        (row.broad_network, row.direction): (
            as_int(row.with_return_calls), as_int(row.without_return_calls)
        )
        for row in cells.itertuples(index=False)
    }
    observed_stages = [
        (row.stage_id, as_int(row.stage_value), row.stage_label)
        for row in stages.sort_values("display_order").itertuples(index=False)
    ]
    checks = [
        record("upstream_phases_complete", True, "VH10B|VH10C validated_complete", "VH10B|VH10C validated_complete", "Validated during input loading."),
        record("frozen_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS), len(bundle["input_digests"]), len(INPUT_PATHS), "Every compact source matches its frozen SHA-256."),
        record("call_count", len(calls) == 42, len(calls), 42, "One plot record per completed KDA call."),
        record("call_ids_unique", calls["kda_run_id"].is_unique, "unique", "unique", "KDA call IDs are unique."),
        record("calls_with_returns", calls["call_status"].eq("with_significant_return").sum() == 29, calls["call_status"].eq("with_significant_return").sum(), 29, "Calls with at least one significant return."),
        record("calls_without_returns", calls["call_status"].eq("without_significant_return").sum() == 13, calls["call_status"].eq("without_significant_return").sum(), 13, "Calls without a significant return."),
        record("significant_return_rows", calls["significant_return_rows"].map(as_int).sum() == 208, calls["significant_return_rows"].map(as_int).sum(), 208, "Significant KDA return rows."),
        record("outcome_cell_count", len(cells) == 14, len(cells), 14, "Seven networks by two signed directions."),
        record("outcome_matrix", observed_outcomes == EXPECTED_OUTCOMES, str(observed_outcomes), str(EXPECTED_OUTCOMES), "Exact with-return/without-return counts, including zero-call cells."),
        record("selection_sequence", observed_stages == SELECTION_STAGES, str(observed_stages), str(SELECTION_STAGES), "Exact evidence-to-selection stage values."),
        record("candidate_units", bundle["candidate_units"] == 38_788, bundle["candidate_units"], 38_788, "Aggregate candidate units."),
        record("selected_units", bundle["selected_units"] == 13, bundle["selected_units"], 13, "Units passing all gates and displayed."),
        record("method_steps", plot_data["record_type"].eq("method_step").sum() == 6, plot_data["record_type"].eq("method_step").sum(), 6, "Six frozen aggregation steps."),
        record("plot_record_count", len(plot_data) == 67, len(plot_data), 67, "Calls, outcome cells, stages, and method steps."),
        record("plot_record_ids_unique", plot_data["record_id"].is_unique, "unique", "unique", "Plot records are uniquely keyed."),
        record("minimum_font_size", render_meta["minimum_font_points"] >= MINIMUM_FONT_PT, render_meta["minimum_font_points"], f">={MINIMUM_FONT_PT}", "All visible text is projection scale."),
        record("canvas_text_clipping", not render_meta["canvas_clipped_text"], len(render_meta["canvas_clipped_text"]), 0, "No visible text leaves the canvas."),
    ]
    checks.extend(
        image_checks(
            SCHEMA, FIGURE_ID, image_paths, dpi=dpi, width=PNG_WIDTH, height=PNG_HEIGHT
        )
    )
    if visual_review_status == "complete":
        checks.append(record("visual_review", True, "complete", "complete", "Reviewed at slide size in color and grayscale.", severity="nonblocking"))
    else:
        checks.append(record("visual_review", False, "pending", "complete", "Manual color/grayscale review remains pending.", severity="nonblocking", status="pending"))
    frame = pd.DataFrame(checks)
    blocking = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking.empty, "Blocking checks failed: " + ", ".join(blocking["check_id"]))
    return frame


def documentation() -> tuple[str, str]:
    caption = """# SEA-AD KDA call outcomes: caption

**Twenty-nine of 42 SEA-AD KDA calls produced at least one significant return, chiefly in neuronal networks.** Each triangle in the outcome matrix is one completed call. Filled navy triangles denote a call with at least one significant return; light triangles denote none. Upward and downward triangle orientation preserves signed-query direction independently of color. Direct cell labels report `with return | none`, and zero-call cells remain explicit. The sequence at right changes units deliberately: 42 calls yielded 29 calls with returns and 208 significant return rows; cross-run aggregation evaluated 38,788 broad-network gene/class candidate units, of which 13 passed all support, coverage, ACAT, network-BH, and class-rank gates. The signed core-MitoCarta DEG set is the KDA query, while candidate drivers are all assessable genes in the induced network; a mitochondrial query can therefore identify a non-MT driver.
"""
    methods = f"""# SEA-AD KDA call outcomes: methods

The renderer reads the validated VH10B run-QC table and status plus the validated VH10C status and selection checks. It requires exact registered full-file SHA-256 values, 42 unique completed KDA calls, 29 calls with at least one significant return, 13 calls with none, and 208 significant return rows. Each `significant_key_drivers > 0` flag must agree with its terminal status. Network-by-direction counts are reconstructed from individual calls and checked against all 14 cells, including OPC and Vasculature combinations with no included call. The five equal-size sequence boxes are not area-scaled because units change from calls to return rows to aggregate candidate units. The aggregation ribbon preserves the executed order: `{' → '.join(METHOD_STEPS)}`.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Direction is encoded by triangle orientation, and call status is encoded by fill plus direct labels, so the figure remains interpretable in grayscale.

## Reproduction command

```bash
python scripts/figures/validation_human/{Path(__file__).name} \\
  --output-root results/figures/validation_human/{FIGURE_ID} \\
  --visual-review-status pending
```
"""
    return caption, methods


def validate_output(
    project_root: Path,
    output_root: Path,
    *,
    expected_visual_status: str | None = None,
) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(output_root.is_dir(), f"Missing output directory: {output_root}")
    require(
        sorted(path.name for path in output_root.iterdir() if path.is_file())
        == sorted(OUTPUT_FILES),
        "Output package file set changed",
    )
    status = one_row(read_tsv(output_root / f"{FIGURE_ID}_status.tsv"), "figure status")
    require(status["schema_version"] == SCHEMA and status["figure_id"] == FIGURE_ID, "Figure status identity changed")
    visual = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Figure validation status changed")
    checks = read_tsv(output_root / f"{FIGURE_ID}_checks.tsv")
    require(not ((checks["severity"] == "blocking") & (checks["status"] != "pass")).any(), "Published package has failed blocking checks")
    if visual == "complete":
        require(checks["status"].eq("pass").all(), "Completed package has incomplete checks")
    artifacts_path = output_root / f"{FIGURE_ID}_artifacts.tsv"
    require(sha256_file(artifacts_path) == status["artifact_manifest_sha256"], "Artifact-manifest SHA changed")
    artifacts = read_tsv(artifacts_path)
    require(not artifacts["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status entered hash scope")
    validate_artifacts(project_root=project_root, output_root=output_root, artifacts=artifacts, payload_files=PAYLOAD_FILES)
    plot_data = read_tsv(output_root / f"{FIGURE_ID}_plot_data.tsv")
    require(len(plot_data) == 67 and plot_data["record_id"].is_unique, "Published plot data changed")
    image_results = image_checks(
        SCHEMA,
        FIGURE_ID,
        [output_root / f"{FIGURE_ID}.{extension}" for extension in ("png", "pdf", "svg")],
        dpi=as_int(status["png_dpi"]),
        width=PNG_WIDTH,
        height=PNG_HEIGHT,
    )
    require(all(row["status"] == "pass" for row in image_results), "Published image checks failed")
    print(f"KDA call-outcomes package validation passed: {output_root}")


def publish(
    project_root: Path,
    output_root: Path,
    *,
    dpi: int,
    visual_review_status: str,
    force: bool,
) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(project_root.is_dir(), f"Missing project root: {project_root}")
    if output_root.exists() and not force:
        raise FileExistsError(f"Output exists; use --force for recoverable replacement: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{FIGURE_ID}.staging.", dir=output_root.parent))
    try:
        bundle = load_bundle(project_root)
        plot_data = build_plot_data(bundle)
        image_paths, render_meta = render_images(bundle, plot_data, staging, dpi)
        write_tsv(plot_data, staging / f"{FIGURE_ID}_plot_data.tsv")
        caption, methods = documentation()
        write_text(staging / f"{FIGURE_ID}_caption.md", caption)
        write_text(staging / f"{FIGURE_ID}_methods.md", methods)
        checks = build_checks(
            bundle, plot_data, image_paths, render_meta,
            dpi=dpi, visual_review_status=visual_review_status,
        )
        write_tsv(checks, staging / f"{FIGURE_ID}_checks.tsv")
        renderer = Path(__file__).resolve()
        common = SCRIPT_DIR / "_slide_figure_common.py"
        artifacts = build_artifacts(
            schema=SCHEMA,
            figure_id=FIGURE_ID,
            project_root=project_root,
            input_digests=bundle["input_digests"],
            staging=staging,
            script_paths=[renderer, common],
            payload_files=PAYLOAD_FILES,
        )
        artifacts_path = staging / f"{FIGURE_ID}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        validation_status = "validated_complete" if visual_review_status == "complete" and pending == 0 else "awaiting_visual_review"
        status = pd.DataFrame(
            [
                {
                    "schema_version": SCHEMA,
                    "figure_id": FIGURE_ID,
                    "validation_status": validation_status,
                    "visual_review_status": visual_review_status,
                    "failed_blocking_checks": int(((checks["severity"] == "blocking") & (checks["status"] != "pass")).sum()),
                    "pending_nonblocking_checks": int(((checks["severity"] == "nonblocking") & (checks["status"] != "pass")).sum()),
                    "input_bundle_sha256": bundle["input_bundle_sha256"],
                    "renderer_sha256": sha256_file(renderer),
                    "common_helper_sha256": sha256_file(common),
                    "artifact_manifest_sha256": sha256_file(artifacts_path),
                    "figure_width_inches": FIGURE_WIDTH_IN,
                    "figure_height_inches": FIGURE_HEIGHT_IN,
                    "png_dpi": dpi,
                    "png_width": PNG_WIDTH,
                    "png_height": PNG_HEIGHT,
                    "input_files": len(bundle["input_digests"]),
                    "output_files": len(OUTPUT_FILES),
                    "plot_data_rows": len(plot_data),
                    "completed_calls": 42,
                    "calls_with_returns": 29,
                    "significant_return_rows": 208,
                    "candidate_units": bundle["candidate_units"],
                    "selected_units": bundle["selected_units"],
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        write_tsv(status, staging / f"{FIGURE_ID}_status.tsv")
        validate_output(project_root, staging, expected_visual_status=visual_review_status)
        if output_root.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            output_root.replace(output_root.parent / f".{output_root.name}.backup.{timestamp}.{os.getpid()}")
        staging.replace(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"Published {len(OUTPUT_FILES)} figure-package files: {output_root}")


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if args.validate_output:
        validate_output(project_root, resolve(project_root, args.validate_output))
        return 0
    publish(
        project_root,
        resolve(project_root, args.output_root),
        dpi=args.png_dpi,
        visual_review_status=args.visual_review_status,
        force=args.force,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
