#!/usr/bin/env python3
"""Render the slide-ready SEA-AD fine-supertype DEG landscape."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_fine_deg_landscape_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_fine_deg_landscape_fontcache"
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
        "svg.hashsalt": "seaad_fine_deg_landscape_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
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


SCHEMA = "seaad_fine_deg_landscape_figure_v1"
PLOT_SCHEMA = "seaad_fine_deg_landscape_plot_data_v1"
FIGURE_ID = "seaad_fine_deg_landscape"
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 5.3
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 2_385
MINIMUM_FONT_PT = 16.0
DEG_TIER = "fine_supertype_phase18_parity"

GROUP_ORDER = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
PLOTTED_GROUPS = ["F_e33", "F_e4", "M_e33"]
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
EXPECTED_NETWORK_SUPERTYPES = {
    "Astrocytes": 6,
    "Excitatory_neurons": 41,
    "Inhibitory_neurons": 67,
    "Microglia": 4,
    "OPCs": 3,
    "Oligodendrocytes": 4,
    "Vasculature_cells": 4,
}
EXPECTED_GROUP_STATUS = {
    "F_e2": (0, 129),
    "F_e33": (100, 29),
    "F_e4": (68, 61),
    "M_e2": (0, 129),
    "M_e33": (92, 37),
    "M_e4": (0, 129),
}
EXPECTED_SIGNED_TOTALS = {
    ("F_e33", "Dementia_up"): 249,
    ("F_e33", "Dementia_down"): 6,
    ("F_e4", "Dementia_up"): 111,
    ("F_e4", "Dementia_down"): 31,
    ("M_e33", "Dementia_up"): 7_697,
    ("M_e33", "Dementia_down"): 14_098,
}

INPUT_PATHS = {
    "vh08_status": "results/validation_human/08_deg/status.tsv",
    "vh08_artifacts": "results/validation_human/08_deg/artifacts.tsv",
    "vh08_checks": "results/validation_human/08_deg/deg_checks.tsv",
    "deg_summary": "results/validation_human/08_deg/deg_summary.tsv",
    "direction_summary": "results/validation_human/08_deg/query_handoff/fine_direction_deg_summary.tsv",
    "contrast_status": "results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv",
}
EXPECTED_INPUT_SHA256 = {
    "vh08_status": "1d85549f1e242458bd3526edbfd1b6f4a11dc742c97e0646fb2be7ea20a84063",
    "vh08_artifacts": "a2ec6f1537caa4cf35a57cacbbbcce34489f45de2b8c9bb6d8b87710838b659b",
    "vh08_checks": "d0f2b02c53f549adc2bc6fbe30aebd40060ae1f24fd7a1e630cb7c1ede620342",
    "deg_summary": "5163077ce6c9e6c91ae911cd6dad3f2ad0afb49a5e4eb1dcefc39ca64385194c",
    "direction_summary": "c800e06b941cd5b8edbff4b043d389ff669b529aefffd154a254aa1d2db3f04b",
    "contrast_status": "70a4361ef124896aead1c35360547bbc5578ae8c88a8f12cafff83d648ead65b",
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
UP = "#D55E00"
DOWN = "#0072B2"
NOT_ESTIMABLE = "#C8CDD2"
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


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column].replace("", np.nan), errors="coerce")


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

    status = one_row(frames["vh08_status"], "VH08 status")
    require(status["validation_status"] == "validated_complete", "VH08 is not validated_complete")
    require(str(status["failed_checks"]).strip() == "", "VH08 reports failed checks")
    require(as_int(status["fine_structural_contrasts"]) == 774, "VH08 structural contrast count changed")
    require(as_int(status["fine_completed"]) == 260, "VH08 completed contrast count changed")
    require(as_int(status["fine_not_estimable"]) == 514, "VH08 not-estimable count changed")
    require(as_int(status["fine_directions"]) == 1548, "VH08 direction count changed")
    checks = frames["vh08_checks"]
    require_columns(checks, ["check", "passed"], "VH08 checks")
    require(checks["passed"].map(truth).all(), "VH08 contains a failed DEG check")

    for key in ("vh08_checks", "deg_summary", "direction_summary", "contrast_status"):
        validate_source_artifact(
            frames["vh08_artifacts"], INPUT_PATHS[key], digests[INPUT_PATHS[key]]
        )

    contrast = frames["contrast_status"].copy()
    require_columns(
        contrast,
        [
            "contrast_id",
            "deg_tier",
            "supertype_id",
            "supertype_label",
            "broad_network",
            "signature_group",
            "terminal_status",
        ],
        "fine contrast status",
    )
    require(len(contrast) == 774, "Fine contrast table does not contain 774 rows")
    require(not contrast["contrast_id"].duplicated().any(), "Fine contrast IDs are duplicated")
    require(set(contrast["deg_tier"]) == {DEG_TIER}, "Fine contrast tier changed")
    require(set(contrast["signature_group"]) == set(GROUP_ORDER), "Signature groups changed")
    require(set(contrast["broad_network"]) == set(NETWORK_ORDER), "Broad networks changed")
    require(set(contrast["terminal_status"]) == {"completed", "not_estimable"}, "Terminal statuses changed")

    fine = frames["deg_summary"].loc[
        frames["deg_summary"]["deg_tier"].eq(DEG_TIER)
    ].copy()
    require_columns(
        fine,
        ["contrast_id", "terminal_status", "fdr_significant", "phase18_parity"],
        "fine DEG summary",
    )
    require(len(fine) == 774 and not fine["contrast_id"].duplicated().any(), "Fine DEG summary keys changed")
    merged = contrast.merge(
        fine[["contrast_id", "terminal_status", "fdr_significant", "phase18_parity"]],
        on="contrast_id",
        how="left",
        validate="one_to_one",
        suffixes=("_status", "_summary"),
    )
    require(
        merged["terminal_status_status"].eq(merged["terminal_status_summary"]).all(),
        "Fine terminal status disagrees across tables",
    )
    merged = merged.rename(columns={"terminal_status_status": "terminal_status"}).drop(
        columns="terminal_status_summary"
    )
    merged["parity_count"] = _numeric(merged, "phase18_parity")
    merged["fdr_count"] = _numeric(merged, "fdr_significant")
    completed = merged["terminal_status"].eq("completed")
    require(merged.loc[completed, "parity_count"].notna().all(), "Completed parity counts are missing")
    require(merged.loc[completed, "fdr_count"].notna().all(), "Completed FDR counts are missing")
    require(merged.loc[~completed, "parity_count"].isna().all(), "Not-estimable parity counts are populated")

    network_counts = (
        merged[["supertype_id", "broad_network"]]
        .drop_duplicates()
        .groupby("broad_network")
        .size()
        .astype(int)
        .to_dict()
    )
    require(network_counts == EXPECTED_NETWORK_SUPERTYPES, "Fine-supertype network counts changed")
    status_counts = merged.groupby(["signature_group", "terminal_status"]).size().to_dict()
    observed_group_status = {
        group: (
            int(status_counts.get((group, "completed"), 0)),
            int(status_counts.get((group, "not_estimable"), 0)),
        )
        for group in GROUP_ORDER
    }
    require(observed_group_status == EXPECTED_GROUP_STATUS, "Group estimability counts changed")

    directions = frames["direction_summary"].copy()
    require_columns(
        directions,
        [
            "direction_slot_id",
            "contrast_id",
            "signature_group",
            "deg_direction",
            "source_terminal_status",
            "phase18_parity_tested_feature_count",
        ],
        "fine direction summary",
    )
    require(len(directions) == 1548, "Fine direction summary row count changed")
    require(not directions["direction_slot_id"].duplicated().any(), "Direction slot IDs are duplicated")
    ready = directions.loc[directions["source_terminal_status"].eq("completed")].copy()
    ready["parity_count"] = _numeric(ready, "phase18_parity_tested_feature_count")
    require(len(ready) == 520 and ready["parity_count"].notna().all(), "Completed direction handoff changed")
    signed_totals = {
        (group, direction): int(value)
        for (group, direction), value in ready.groupby(
            ["signature_group", "deg_direction"]
        )["parity_count"].sum().items()
    }
    require(
        {key: signed_totals.get(key, 0) for key in EXPECTED_SIGNED_TOTALS}
        == EXPECTED_SIGNED_TOTALS,
        "Signed parity-hit totals changed",
    )
    by_contrast = ready.groupby("contrast_id")["parity_count"].sum()
    expected_by_contrast = merged.loc[completed].set_index("contrast_id")["parity_count"]
    require(
        by_contrast.sort_index().index.equals(expected_by_contrast.sort_index().index)
        and np.array_equal(
            by_contrast.sort_index().to_numpy(dtype=float),
            expected_by_contrast.sort_index().to_numpy(dtype=float),
        ),
        "Direction totals do not reconstruct contrast parity totals",
    )

    total_fdr = int(merged["fdr_count"].sum())
    total_parity = int(merged["parity_count"].sum())
    signal_contrasts = int(merged["parity_count"].fillna(0).gt(0).sum())
    m_e33_parity = int(
        merged.loc[merged["signature_group"].eq("M_e33"), "parity_count"].sum()
    )
    require((total_fdr, total_parity, signal_contrasts, m_e33_parity) == (24_404, 22_192, 74, 21_795), "DEG result anchors changed")

    supertype_totals = (
        merged.groupby(["supertype_id", "broad_network"], as_index=False)["parity_count"]
        .sum()
        .rename(columns={"parity_count": "supertype_total"})
    )
    network_rank = {network: index for index, network in enumerate(NETWORK_ORDER)}
    supertype_totals["network_order"] = supertype_totals["broad_network"].map(network_rank)
    supertype_totals = supertype_totals.sort_values(
        ["network_order", "supertype_total", "supertype_id"],
        ascending=[True, False, True],
        kind="stable",
    ).reset_index(drop=True)
    supertype_totals["row_order"] = np.arange(len(supertype_totals))
    merged = merged.merge(
        supertype_totals[["supertype_id", "row_order", "supertype_total"]],
        on="supertype_id",
        how="left",
        validate="many_to_one",
    )
    require(merged["row_order"].notna().all(), "Supertype row order is incomplete")

    input_bundle_sha256 = sha256_strings(
        f"{path}\t{digest}" for path, digest in sorted(digests.items())
    )
    return {
        "project_root": project_root,
        "frames": frames,
        "input_digests": digests,
        "input_bundle_sha256": input_bundle_sha256,
        "merged": merged,
        "supertype_totals": supertype_totals,
        "signed_totals": signed_totals,
        "total_fdr": total_fdr,
        "total_parity": total_parity,
        "signal_contrasts": signal_contrasts,
        "m_e33_parity": m_e33_parity,
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
        "supertype_id": "",
        "supertype_label": "",
        "row_order": "",
        "signature_group": "",
        "deg_direction": "",
        "terminal_status": "",
        "raw_count": "",
        "plot_value": "",
        "metric_id": "",
        "display_value": "",
        "display_label": "",
        "value_scope": "feature_contrast_incidence",
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    merged = bundle["merged"]
    group_rank = {group: index for index, group in enumerate(GROUP_ORDER)}
    cells = merged.sort_values(
        ["row_order", "signature_group"],
        key=lambda values: values.map(group_rank) if values.name == "signature_group" else values,
        kind="stable",
    )
    for row in cells.itertuples(index=False):
        record = _empty_record("heatmap_cell", f"cell::{row.contrast_id}")
        count = "" if row.terminal_status == "not_estimable" else int(row.parity_count)
        value = "" if count == "" else f"{math.log10(1 + count):.9f}"
        record.update(
            {
                "display_order": int(row.row_order) * len(GROUP_ORDER) + group_rank[row.signature_group],
                "broad_network": row.broad_network,
                "broad_network_label": NETWORK_LABELS[row.broad_network],
                "supertype_id": row.supertype_id,
                "supertype_label": row.supertype_label,
                "row_order": int(row.row_order),
                "signature_group": row.signature_group,
                "terminal_status": row.terminal_status,
                "raw_count": count,
                "plot_value": value,
                "metric_id": "phase18_parity_feature_contrast_hits",
                "display_value": count,
                "display_label": "Parity-qualified hits",
            }
        )
        rows.append(record)

    direction_order = {"Dementia_down": 0, "Dementia_up": 1}
    for group_index, group in enumerate(PLOTTED_GROUPS):
        for direction in ("Dementia_down", "Dementia_up"):
            count = EXPECTED_SIGNED_TOTALS[(group, direction)]
            record = _empty_record("signed_group_total", f"signed::{group}::{direction}")
            record.update(
                {
                    "display_order": group_index * 2 + direction_order[direction],
                    "signature_group": group,
                    "deg_direction": direction,
                    "raw_count": count,
                    "plot_value": f"{math.log10(1 + count):.9f}",
                    "metric_id": "phase18_parity_feature_contrast_hits",
                    "display_value": f"{count:,}",
                    "display_label": "Dementia down" if direction.endswith("down") else "Dementia up",
                }
            )
            rows.append(record)

    chip_values = [
        ("completed_contrasts", "260 / 774", "completed contrasts"),
        ("fdr_significant_hits", "24,404", "FDR-significant hits"),
        ("parity_hits", "22,192", "parity-qualified hits"),
        ("signal_contrasts", "74", "contrasts with signal"),
        ("m_e33_share", "98.2%", "of parity hits in M_e33"),
    ]
    for order, (metric, value, label) in enumerate(chip_values):
        record = _empty_record("result_chip", f"chip::{metric}")
        record.update(
            {
                "display_order": order,
                "metric_id": metric,
                "display_value": value,
                "display_label": label,
            }
        )
        rows.append(record)
    frame = pd.DataFrame(rows)
    require(len(frame) == 785, f"Expected 785 plot records, observed {len(frame)}")
    require(frame["record_id"].is_unique, "Plot record IDs are duplicated")
    return frame


def _draw_status_key(fig: Any) -> None:
    y = 0.879
    fig.add_artist(
        mpatches.Rectangle(
            (0.335, y - 0.012), 0.018, 0.026, transform=fig.transFigure,
            facecolor=NOT_ESTIMABLE, edgecolor=MID, linewidth=0.8,
        )
    )
    fig.text(0.358, y, "not estimable", ha="left", va="center", fontsize=16, color=TEXT)
    fig.add_artist(
        mpatches.Rectangle(
            (0.470, y - 0.012), 0.018, 0.026, transform=fig.transFigure,
            facecolor=WHITE, edgecolor=MID, linewidth=0.8,
        )
    )
    fig.text(0.493, y, "zero hits", ha="left", va="center", fontsize=16, color=TEXT)


def draw_figure(bundle: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    fig.text(0.02, 0.958, "A  Fine-supertype DEG landscape", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.645, 0.958, "B  Signed parity-hit totals", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    _draw_status_key(fig)
    fig.text(0.825, 0.877, "mirrored log10 scale • exact counts", ha="center", va="center", fontsize=16, color=MID)

    heat_ax = fig.add_axes([0.200, 0.205, 0.390, 0.610])
    merged = bundle["merged"]
    matrix = np.full((129, len(GROUP_ORDER)), -0.25, dtype=float)
    group_rank = {group: index for index, group in enumerate(GROUP_ORDER)}
    for row in merged.itertuples(index=False):
        i = int(row.row_order)
        j = group_rank[row.signature_group]
        if row.terminal_status == "completed":
            matrix[i, j] = math.log10(1 + int(row.parity_count))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "white_to_navy", ["#FFFFFF", "#C9D7E7", "#6F98BE", NAVY]
    )
    cmap.set_under(NOT_ESTIMABLE)
    maximum = float(matrix.max())
    image = heat_ax.imshow(
        matrix,
        origin="upper",
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        norm=mcolors.Normalize(vmin=0, vmax=maximum),
    )
    heat_ax.set_xticks(range(len(GROUP_ORDER)), GROUP_ORDER)
    heat_ax.xaxis.tick_top()
    heat_ax.tick_params(axis="x", length=0, pad=6, labelsize=16)
    heat_ax.set_yticks([])
    heat_ax.set_xlim(-1.0, len(GROUP_ORDER) - 0.5)
    for spine in heat_ax.spines.values():
        spine.set_visible(False)

    supertype_totals = bundle["supertype_totals"]
    start = 0
    label_y_positions = np.linspace(0.765, 0.255, len(NETWORK_ORDER))
    for network, label_y in zip(NETWORK_ORDER, label_y_positions):
        count = EXPECTED_NETWORK_SUPERTYPES[network]
        center = start + (count - 1) / 2
        heat_ax.add_patch(
            mpatches.Rectangle(
                (-0.72, start - 0.5), 0.22, count,
                facecolor=NETWORK_COLORS[network], edgecolor="none", clip_on=False,
            )
        )
        fig.text(0.177, label_y, NETWORK_LABELS[network], ha="right", va="center", fontsize=16, color=TEXT)
        fig.add_artist(
            mpatches.ConnectionPatch(
                xyA=(0.183, label_y), coordsA=fig.transFigure,
                xyB=(-0.73, center), coordsB=heat_ax.transData,
                color=NETWORK_COLORS[network], linewidth=1.3, zorder=5,
            )
        )
        if start > 0:
            heat_ax.axhline(start - 0.5, color=WHITE, linewidth=1.2, zorder=4)
        observed = supertype_totals.loc[supertype_totals["broad_network"].eq(network)]
        require(len(observed) == count, f"Network row count changed for {network}")
        start += count
    require(start == 129, "Network bands do not cover 129 rows")
    for x in np.arange(0.5, len(GROUP_ORDER) - 0.5, 1):
        heat_ax.axvline(x, color=WHITE, linewidth=0.8, alpha=0.9)

    color_ax = fig.add_axes([0.602, 0.245, 0.014, 0.52])
    colorbar = fig.colorbar(image, cax=color_ax)
    ticks = [0, maximum / 2, maximum]
    colorbar.set_ticks(ticks)
    colorbar.set_ticklabels(["0", f"{maximum / 2:.1f}", f"{maximum:.1f}"])
    colorbar.ax.tick_params(labelsize=16, length=3)
    colorbar.outline.set_linewidth(0.8)

    bar_ax = fig.add_axes([0.675, 0.220, 0.30, 0.54])
    y_positions = np.array([4.0, 2.0, 0.0])
    down_counts = np.array([EXPECTED_SIGNED_TOTALS[(group, "Dementia_down")] for group in PLOTTED_GROUPS])
    up_counts = np.array([EXPECTED_SIGNED_TOTALS[(group, "Dementia_up")] for group in PLOTTED_GROUPS])
    down_widths = np.log10(1 + down_counts)
    up_widths = np.log10(1 + up_counts)
    bar_ax.barh(y_positions, -down_widths, height=0.34, color=DOWN, edgecolor=NAVY, linewidth=0.8)
    bar_ax.barh(y_positions, up_widths, height=0.34, color=UP, edgecolor="#7A2E0B", linewidth=0.8)
    bar_ax.axvline(0, color=TEXT, linewidth=1.1)
    for y, count, width in zip(y_positions, down_counts, down_widths):
        bar_ax.text(-width - 0.12, y, f"{count:,}", ha="right", va="center", fontsize=16, weight="bold", color=DOWN)
    for y, count, width in zip(y_positions, up_counts, up_widths):
        bar_ax.text(width + 0.12, y, f"{count:,}", ha="left", va="center", fontsize=16, weight="bold", color=UP)
    bar_ax.set_yticks([])
    for y, group in zip(y_positions, PLOTTED_GROUPS):
        bar_ax.text(0, y + 0.48, group, ha="center", va="center", fontsize=16, weight="bold", color=TEXT)
    bar_ax.set_xlim(-5.1, 5.1)
    bar_ax.set_ylim(-0.62, 5.15)
    bar_ax.set_xticks([])
    for spine in bar_ax.spines.values():
        spine.set_visible(False)
    bar_ax.text(0.23, 1.04, "▼ Dementia-down", transform=bar_ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=DOWN)
    bar_ax.text(0.77, 1.04, "▲ Dementia-up", transform=bar_ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=UP)
    fig.text(0.825, 0.177, "Incidences—not unique genes", ha="center", va="center", fontsize=16, color=MID)

    chips = [
        ("260 / 774", "completed\ncontrasts"),
        ("24,404", "FDR-significant\nhits"),
        ("22,192", "parity-qualified\nhits"),
        ("74", "contrasts with\nsignal"),
        ("98.2%", "parity hits\nin M_e33"),
    ]
    left, gap, width, bottom, height = 0.025, 0.010, 0.184, 0.010, 0.145
    for index, (value, label) in enumerate(chips):
        x = left + index * (width + gap)
        fig.add_artist(
            mpatches.FancyBboxPatch(
                (x, bottom), width, height,
                boxstyle="round,pad=0.004,rounding_size=0.007",
                transform=fig.transFigure, facecolor="#F4F7F9", edgecolor="#9AA3AC", linewidth=1.0,
            )
        )
        fig.text(x + width / 2, bottom + 0.105, value, ha="center", va="center", fontsize=19, weight="bold", color=NAVY)
        fig.text(x + width / 2, bottom + 0.043, label, ha="center", va="center", fontsize=16, linespacing=0.95, color=TEXT)

    metadata = visible_text_metadata(fig)
    require(metadata["minimum_font_points"] >= MINIMUM_FONT_PT, "A visible label is smaller than 16 pt")
    require(not metadata["canvas_clipped_text"], "Text leaves canvas: " + " | ".join(metadata["canvas_clipped_text"]))
    return fig, metadata


def render_images(bundle: Mapping[str, Any], staging: Path, dpi: int) -> tuple[list[Path], dict[str, Any]]:
    fig, metadata = draw_figure(bundle)
    paths = render_three_formats(
        fig, staging, FIGURE_ID, dpi=dpi,
        title="SEA-AD fine-supertype DEG landscape",
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
    cells = plot_data.loc[plot_data["record_type"].eq("heatmap_cell")]
    signed = plot_data.loc[plot_data["record_type"].eq("signed_group_total")]
    chips = plot_data.loc[plot_data["record_type"].eq("result_chip")]
    observed_signed = {
        (row.signature_group, row.deg_direction): as_int(row.raw_count)
        for row in signed.itertuples(index=False)
    }
    checks = [
        record("vh08_validated", True, "validated_complete", "validated_complete", "Validated during input loading."),
        record("frozen_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS), len(bundle["input_digests"]), len(INPUT_PATHS), "Every source matches its frozen SHA-256."),
        record("heatmap_cell_count", len(cells) == 774, len(cells), 774, "One cell per fine-supertype contrast."),
        record("heatmap_keys_unique", not cells[["supertype_id", "signature_group"]].duplicated().any(), "unique", "unique", "Each supertype–group cell is unique."),
        record("heatmap_supertype_count", cells["supertype_id"].nunique() == 129, cells["supertype_id"].nunique(), 129, "All retained supertypes are represented."),
        record("completed_contrast_count", cells["terminal_status"].eq("completed").sum() == 260, cells["terminal_status"].eq("completed").sum(), 260, "Completed contrast cells."),
        record("not_estimable_count", cells["terminal_status"].eq("not_estimable").sum() == 514, cells["terminal_status"].eq("not_estimable").sum(), 514, "Not-estimable contrast cells."),
        record("signed_totals", observed_signed == EXPECTED_SIGNED_TOTALS, str(observed_signed), str(EXPECTED_SIGNED_TOTALS), "Exact Dementia-up/down parity-hit totals."),
        record("fdr_total", bundle["total_fdr"] == 24_404, bundle["total_fdr"], 24_404, "FDR-significant feature–contrast hits."),
        record("parity_total", bundle["total_parity"] == 22_192, bundle["total_parity"], 22_192, "Parity-qualified feature–contrast hits."),
        record("signal_contrasts", bundle["signal_contrasts"] == 74, bundle["signal_contrasts"], 74, "Completed contrasts with at least one parity hit."),
        record("m_e33_share", round(100 * bundle["m_e33_parity"] / bundle["total_parity"], 1) == 98.2, f"{100 * bundle['m_e33_parity'] / bundle['total_parity']:.1f}%", "98.2%", "Share of parity hits in M_e33."),
        record("result_chip_count", len(chips) == 5, len(chips), 5, "Five exact result chips."),
        record("plot_record_count", len(plot_data) == 785, len(plot_data), 785, "Heatmap, signed totals, and chips."),
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
    caption = """# SEA-AD fine-supertype DEG landscape: caption

**Fine-supertype differential-expression signal was concentrated in M_e33 neuronal contrasts.** The heatmap shows all 129 retained SEA-AD supertypes across the six fixed sex/APOE groups. Completed cells are colored by `log10(1 + Phase 18-parity feature–contrast hits)`; gray cells were not estimable and white cells were completed with zero parity-qualified hits. Supertypes are grouped by the seven broad networks and ordered within network by total parity-hit count. Mirrored bars show exact Dementia-up and Dementia-down totals for the three groups with completed contrasts. Of 774 structural contrasts, 260 completed and 74 contained at least one parity-qualified hit. There were 24,404 FDR-significant and 22,192 parity-qualified feature–contrast incidences; 21,795 (98.2%) of the latter occurred in M_e33. Counts are feature–contrast incidences, not unique genes.
"""
    methods = f"""# SEA-AD fine-supertype DEG landscape: methods

The renderer reads the validated VH08 status, checks, fine contrast status, fine direction handoff, and DEG summary. It requires exact registered full-file SHA-256 values, `validated_complete` status, no failed VH08 check, 774 unique fine-supertype contrasts, and 1,548 unique signed direction slots. The heatmap uses the `{DEG_TIER}` tier only. A completed cell is the sum of its Dementia-up and Dementia-down parity-qualified feature hits; direction-level counts are independently required to reconstruct the contrast-level total. Not-estimable cells remain distinct from completed zero-hit cells. Rows follow the fixed seven-network order, then descending total parity hits and stable `supertype_id` within network. Bars use `log10(1 + count)` length while printing untransformed counts. The figure does not use broad pooled or broad stratified DEG tiers.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Color is backed by direct labels and distinct white/gray states.

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
    require(len(plot_data) == 785 and plot_data["record_id"].is_unique, "Published plot data changed")
    image_results = image_checks(
        SCHEMA,
        FIGURE_ID,
        [output_root / f"{FIGURE_ID}.{extension}" for extension in ("png", "pdf", "svg")],
        dpi=as_int(status["png_dpi"]),
        width=PNG_WIDTH,
        height=PNG_HEIGHT,
    )
    require(all(row["status"] == "pass" for row in image_results), "Published image checks failed")
    print(f"Fine-DEG landscape package validation passed: {output_root}")


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
        image_paths, render_meta = render_images(bundle, staging, dpi)
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
                    "fine_contrasts": 774,
                    "completed_contrasts": 260,
                    "parity_hits": bundle["total_parity"],
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
