#!/usr/bin/env python3
"""Update slides 1-24 of the dated sex/APOE KDA deck with combo results.

The combo design merges significant up- and downregulated mitochondrial DEGs
within each contrast, deduplicates the union, and permits at most one KDA call
per contrast.  This script derives every displayed count from the ROSMAP and
SEA-AD combo outputs, renders replacement top-five and recurrence figures,
updates speaker notes, and preserves the existing sensitivity section on
slides 25 onward.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "sex_apoe_combo_slides_mpl")
)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patches  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize  # noqa: E402
from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_phase11_seaad_simple_aggr_part2 as ui  # noqa: E402

SKILL_SCRIPTS = ROOT / ".agents/skills/scientific-visualization/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from figure_export import save_publication_figure  # noqa: E402
from style_presets import apply_publication_style  # noqa: E402


DEFAULT_DECK = (
    ROOT / "docs/presentations/09162026/sex_apoe_kda_fine_broad_09162026.pptx"
)
ROS_DIR = ROOT / "results/minerva_production/20_sex_apoe_kda_combo"
SEA_DIR = ROOT / "results/validation_human/12_sex_apoe_kda_combo"
AUDIT_ROOT = ROOT / "results/presentations/09162026_sex_apoe_kda_combo_update"

GROUP_ORDER = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
NETWORK_ORDER = [
    "Astrocytes",
    "Excitatory_neurons",
    "Inhibitory_neurons",
    "Microglia",
    "OPCs",
    "Oligodendrocytes",
    "Vasculature_cells",
]
TOP5_BROAD_CELL_ORDER = [
    "Astrocytes",
    "Excitatory_neurons",
    "Inhibitory_neurons",
    "OPCs",
    "Oligodendrocytes",
    "Vasculature_cells",
    "Microglia",
]
APOE_ORDER = ["e2", "e33", "e4"]
NETWORK_LABELS = {
    "Astrocytes": "Astrocytes",
    "Excitatory_neurons": "Excitatory neurons",
    "Inhibitory_neurons": "Inhibitory neurons",
    "Microglia": "Microglia",
    "OPCs": "OPCs",
    "Oligodendrocytes": "Oligodendrocytes",
    "Vasculature_cells": "Vasculature",
}
BROAD_CELL_COLORS = {
    "Astrocytes": "#88CCB0",
    "Excitatory_neurons": "#77BDEB",
    "Inhibitory_neurons": "#F3B562",
    "Microglia": "#E89072",
    "OPCs": "#D5A6BD",
    "Oligodendrocytes": "#B0D7E8",
    "Vasculature_cells": "#E9D66B",
}

BLUE = "#56B4E9"
TEAL = "#009E73"
ORANGE = "#E69F00"
TEXT = "#222222"
MUTED = "#4B5563"
GRID = "#D1D5DB"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-root", type=Path, default=AUDIT_ROOT)
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Regenerate and validate combo figures without modifying a deck",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep="\t", keep_default_na=False, na_values=["NA"])


def semantic_slide_fingerprint(slide) -> tuple[Any, ...]:
    rows = []
    for shape in slide.shapes:
        text = shape.text if getattr(shape, "has_text_frame", False) else ""
        rows.append(
            (
                int(shape.shape_type),
                shape.name,
                int(shape.left),
                int(shape.top),
                int(shape.width),
                int(shape.height),
                text,
            )
        )
    notes = slide.notes_slide.notes_text_frame
    return tuple(rows), notes.text if notes is not None else ""


def set_text(slide, shape_name: str, value: str) -> None:
    matches = [shape for shape in slide.shapes if shape.name == shape_name]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one shape named {shape_name!r}, found {len(matches)}"
        )
    frame = matches[0].text_frame
    first = frame.paragraphs[0]
    if first.runs:
        first.runs[0].text = value
        for run in first.runs[1:]:
            run.text = ""
    else:
        first.add_run().text = value
    for paragraph in frame.paragraphs[1:]:
        paragraph._element.getparent().remove(paragraph._element)


def set_split_text(
    slide,
    shape_name: str,
    prefix: str,
    tail: str,
    *,
    prefix_size: float,
    tail_size: float,
) -> None:
    set_text(slide, shape_name, prefix)
    paragraph = next(
        shape for shape in slide.shapes if shape.name == shape_name
    ).text_frame.paragraphs[0]
    first = paragraph.runs[0]
    first.font.size = Pt(prefix_size)
    if len(paragraph.runs) > 1:
        final = paragraph.runs[1]
    else:
        final = paragraph.add_run()
        final.font.name = first.font.name
        final.font.bold = first.font.bold
        final.font.italic = first.font.italic
        try:
            final.font.color.rgb = first.font.color.rgb
        except AttributeError:
            pass
    final.text = tail
    final.font.size = Pt(tail_size)
    for run in paragraph.runs[2:]:
        run.text = ""


def set_notes(slide, goal: str, walkthrough: str, boundary: str, transition: str) -> None:
    ui.add_notes(
        slide,
        goal=goal,
        walkthrough=walkthrough,
        boundary=boundary,
        transition=transition,
    )


def clear_slide(slide) -> None:
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = ui.OFF_WHITE


def remove_named_shapes(slide, shape_names: Iterable[str]) -> None:
    for shape_name in shape_names:
        matches = [shape for shape in slide.shapes if shape.name == shape_name]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one shape named {shape_name!r}, found {len(matches)}"
            )
        matches[0]._element.getparent().remove(matches[0]._element)


def remove_slide_range(prs: Presentation, start: int, stop: int) -> list[str]:
    """Remove a zero-based half-open slide range and return its titles."""
    titles: list[str] = []
    for index in range(stop - 1, start - 1, -1):
        slide = prs.slides[index]
        title = next(
            (
                " ".join(shape.text.split())
                for shape in slide.shapes
                if getattr(shape, "has_text_frame", False) and shape.text.strip()
            ),
            "",
        )
        titles.append(title)
        slide_id = prs.slides._sldIdLst[index]
        prs.part.drop_rel(slide_id.rId)
        prs.slides._sldIdLst.remove(slide_id)
    return list(reversed(titles))


def reorder_slide_block(prs: Presentation, source_indices: list[int]) -> list[str]:
    """Reorder one contiguous slide block using zero-based source indices."""
    start = min(source_indices)
    if sorted(source_indices) != list(range(start, start + len(source_indices))):
        raise ValueError("source_indices must describe one contiguous slide block")
    slide_id_list = prs.slides._sldIdLst
    selected = [slide_id_list[index] for index in source_indices]
    titles = [
        next(
            (
                " ".join(shape.text.split())
                for shape in prs.slides[index].shapes
                if getattr(shape, "has_text_frame", False) and shape.text.strip()
            ),
            "",
        )
        for index in source_indices
    ]
    for slide_id in selected:
        slide_id_list.remove(slide_id)
    for offset, slide_id in enumerate(selected):
        slide_id_list.insert(start + offset, slide_id)
    return titles


def replace_picture(slide, old_shape_name: str, image_path: Path, alt: str) -> Any:
    matches = [shape for shape in slide.shapes if shape.name == old_shape_name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one picture named {old_shape_name!r}")
    old = matches[0]
    parent = old._element.getparent()
    old_index = parent.index(old._element)
    left, top, width, height = old.left, old.top, old.width, old.height
    parent.remove(old._element)
    picture = slide.shapes.add_picture(
        str(image_path), left, top, width=width, height=height
    )
    ui.set_alt_text(picture, alt)
    element = picture._element
    element.getparent().remove(element)
    parent.insert(old_index, element)
    return picture


def prepare_facts() -> dict[str, Any]:
    ros_manifest = read_tsv(ROS_DIR / "combo_run_manifest.tsv")
    ros_categories = read_tsv(ROS_DIR / "combo_key_drivers_by_category.tsv")
    ros_summary = read_tsv(ROS_DIR / "combo_category_summary.tsv")
    ros_returned = read_tsv(ROS_DIR / "combo_returned_call_rows.tsv.gz")
    ros_queries = read_tsv(ROS_DIR / "combo_query_members.tsv.gz")

    sea_manifest = read_tsv(SEA_DIR / "10a_inputs/seaad_kda_run_manifest.tsv")
    sea_status = read_tsv(SEA_DIR / "simple_status.tsv")
    sea_checks = read_tsv(SEA_DIR / "simple_checks.tsv")
    sea_categories = read_tsv(SEA_DIR / "simple_category_gene_aggregates.tsv")
    sea_summary = read_tsv(SEA_DIR / "simple_category_summary.tsv")

    if len(sea_status) != 1:
        raise RuntimeError("SEA-AD combo simple_status.tsv must contain one row")
    sea_status_row = sea_status.iloc[0]
    if (
        sea_status_row["execution_status"] != "complete"
        or int(sea_status_row["failed_check_count"]) != 0
        or not sea_checks["passed"].astype(str).str.upper().eq("TRUE").all()
    ):
        raise RuntimeError("SEA-AD combo output is not validated complete")

    ros_non_mt = ros_categories.loc[
        ~ros_categories["is_core_mito"].astype(str).str.upper().isin(["TRUE", "T", "1"])
    ].copy()
    ros_non_mt = ros_non_mt.rename(
        columns={
            "broad_cell_type": "broad_network",
            "key_driver": "current_symbol",
            "contributing_call_count": "returned_call_count",
            "simple_aggregation_score": "returned_run_q_acat_score",
        }
    )
    ros_non_mt["returned_call_count"] = pd.to_numeric(
        ros_non_mt["returned_call_count"], errors="raise"
    ).astype(int)
    ros_non_mt["returned_run_q_acat_score"] = pd.to_numeric(
        ros_non_mt["returned_run_q_acat_score"], errors="raise"
    )

    sea_non_mt = sea_categories.copy()
    sea_non_mt["returned_call_count"] = pd.to_numeric(
        sea_non_mt["returned_call_count"], errors="raise"
    ).astype(int)
    sea_non_mt["returned_run_q_acat_score"] = pd.to_numeric(
        sea_non_mt["returned_run_q_acat_score"], errors="raise"
    )

    for frame in (ros_non_mt, sea_non_mt):
        frame["_group_order"] = frame["signature_group"].map(
            {name: index for index, name in enumerate(GROUP_ORDER)}
        )
        frame["_network_order"] = frame["broad_network"].map(
            {name: index for index, name in enumerate(NETWORK_ORDER)}
        )
        if frame[["_group_order", "_network_order"]].isna().any().any():
            raise RuntimeError("Unexpected group or broad-network label")
        frame.sort_values(
            [
                "_group_order",
                "_network_order",
                "returned_run_q_acat_score",
                "current_symbol",
            ],
            inplace=True,
            kind="mergesort",
        )
        frame["display_rank"] = (
            frame.groupby(["signature_group", "broad_network"], sort=False).cumcount()
            + 1
        )
        frame["category_gene_count"] = frame.groupby(
            ["signature_group", "broad_network"], sort=False
        )["current_symbol"].transform("nunique")
        frame["category_label"] = [
            f"{group} · {NETWORK_LABELS[network]}"
            for group, network in zip(
                frame["signature_group"], frame["broad_network"], strict=True
            )
        ]

    ros_included = ros_manifest["included_at_thresholds"].astype(str).str.upper().eq("TRUE")
    ros_valid = ros_manifest["passes_cell_floor"].astype(str).str.upper().eq("TRUE")
    ros_effective = pd.to_numeric(ros_manifest["effective_query_genes"], errors="raise")

    shared_genes = sorted(
        set(ros_non_mt["current_symbol"]) & set(sea_non_mt["current_symbol"])
    )
    matched = sea_non_mt.merge(
        ros_non_mt,
        on=["signature_group", "broad_network", "current_symbol"],
        suffixes=("_sea", "_ros"),
    )
    pairs = sea_non_mt.merge(
        ros_non_mt, on="current_symbol", suffixes=("_sea", "_ros")
    )
    same_network = pairs["broad_network_sea"].eq(pairs["broad_network_ros"])
    same_group = pairs["signature_group_sea"].eq(pairs["signature_group_ros"])

    ros_top5 = ros_non_mt[ros_non_mt["display_rank"].le(5)].copy()
    sea_top5 = sea_non_mt[sea_non_mt["display_rank"].le(5)].copy()
    ros_recurrence = derive_recurrence(ros_non_mt)
    sea_recurrence = derive_recurrence(sea_non_mt)

    facts = {
        "ros_manifest": ros_manifest,
        "ros_categories": ros_non_mt,
        "ros_summary": ros_summary,
        "ros_returned": ros_returned,
        "ros_queries": ros_queries,
        "ros_top5": ros_top5,
        "ros_recurrence": ros_recurrence,
        "ros_planned": len(ros_manifest),
        "ros_not_valid": int((~ros_valid).sum()),
        "ros_query_zero": int((ros_valid & ros_effective.eq(0)).sum()),
        "ros_query_1_2": int((ros_valid & ros_effective.between(1, 2)).sum()),
        "ros_calls": int(ros_included.sum()),
        "ros_significant_calls": int(
            ros_manifest.loc[ros_included, "phase12_terminal_status"]
            .eq("completed_significant")
            .sum()
        ),
        "ros_empty_calls": int(
            ros_manifest.loc[ros_included, "phase12_terminal_status"]
            .eq("completed_no_significant")
            .sum()
        ),
        "ros_all_returned": len(ros_returned),
        "ros_mt_returned": int(
            ros_returned["is_core_mito"].astype(str).str.upper().eq("TRUE").sum()
        ),
        "ros_non_mt_rows": int(ros_non_mt["returned_call_count"].sum()),
        "ros_units": len(ros_non_mt),
        "ros_genes": ros_non_mt["current_symbol"].nunique(),
        "ros_categories_count": ros_non_mt[
            ["signature_group", "broad_network"]
        ].drop_duplicates().shape[0],
        "ros_top5_count": len(ros_top5),
        "ros_fine_types": ros_manifest.loc[ros_included, "fine_cell_type"].nunique(),
        "sea_manifest": sea_manifest,
        "sea_categories": sea_non_mt,
        "sea_summary": sea_summary,
        "sea_top5": sea_top5,
        "sea_recurrence": sea_recurrence,
        "sea_planned": len(sea_manifest),
        "sea_not_estimable": int(
            sea_manifest["terminal_status"].eq("source_contrast_not_estimable").sum()
        ),
        "sea_query_zero": int(sea_manifest["terminal_status"].eq("query_empty").sum()),
        "sea_query_1_2": int(
            sea_manifest["terminal_status"].eq("query_below_minimum").sum()
        ),
        "sea_calls": int(sea_status_row["included_run_count"]),
        "sea_significant_calls": int(
            sea_status_row["completed_significant_call_count"]
        ),
        "sea_empty_calls": int(sea_status_row["completed_empty_call_count"]),
        "sea_all_returned": int(sea_status_row["all_class_stock_returned_row_count"]),
        "sea_mt_returned": int(sea_status_row["mt_excluded_returned_row_count"]),
        "sea_non_mt_rows": int(sea_status_row["non_mt_retained_returned_row_count"]),
        "sea_units": len(sea_non_mt),
        "sea_genes": sea_non_mt["current_symbol"].nunique(),
        "sea_categories_count": sea_non_mt[
            ["signature_group", "broad_network"]
        ].drop_duplicates().shape[0],
        "sea_top5_count": len(sea_top5),
        "shared_genes": shared_genes,
        "exact_matches": len(matched),
        "pair_count": len(pairs),
        "same_network_pairs": int(same_network.sum()),
        "same_group_pairs": int(same_group.sum()),
        "same_exact_pairs": int((same_network & same_group).sum()),
    }

    expected = {
        "ros_planned": 324,
        "ros_not_valid": 3,
        "ros_query_zero": 95,
        "ros_query_1_2": 32,
        "ros_calls": 194,
        "ros_significant_calls": 164,
        "ros_empty_calls": 30,
        "ros_all_returned": 1833,
        "ros_mt_returned": 1210,
        "ros_non_mt_rows": 623,
        "ros_units": 381,
        "ros_genes": 228,
        "ros_categories_count": 29,
        "ros_top5_count": 123,
        "ros_fine_types": 43,
        "sea_planned": 774,
        "sea_not_estimable": 393,
        "sea_query_zero": 348,
        "sea_query_1_2": 11,
        "sea_calls": 22,
        "sea_significant_calls": 20,
        "sea_empty_calls": 2,
        "sea_all_returned": 112,
        "sea_mt_returned": 58,
        "sea_non_mt_rows": 54,
        "sea_units": 44,
        "sea_genes": 43,
        "sea_categories_count": 5,
        "sea_top5_count": 17,
        "exact_matches": 0,
        "pair_count": 6,
        "same_network_pairs": 0,
        "same_group_pairs": 1,
        "same_exact_pairs": 0,
    }
    for key, value in expected.items():
        if facts[key] != value:
            raise RuntimeError(f"Source drift for {key}: {facts[key]} != {value}")
    if shared_genes != ["LAGE3", "MIPOL1", "PAPOLA"]:
        raise RuntimeError(f"Unexpected shared genes: {shared_genes}")
    if not ros_manifest["query_mode"].eq("AD_both_mito").all():
        raise RuntimeError("ROSMAP manifest is not uniformly merged up/down")
    if not sea_manifest["query_mode"].eq("merged_up_down").all():
        raise RuntimeError("SEA-AD manifest is not uniformly merged up/down")
    return facts


def derive_recurrence(non_mt: pd.DataFrame) -> pd.DataFrame:
    work = non_mt.copy()
    work["acat_category"] = work["returned_call_count"].ge(2).astype(int)
    return (
        work.groupby("current_symbol", as_index=False)
        .agg(
            category_count=("current_symbol", "size"),
            sex_apoe_group_count=("signature_group", "nunique"),
            broad_network_count=("broad_network", "nunique"),
            total_returned_call_count=("returned_call_count", "sum"),
            acat_category_count=("acat_category", "sum"),
            best_score=("returned_run_q_acat_score", "min"),
        )
        .sort_values(
            ["category_count", "best_score", "current_symbol"],
            ascending=[False, True, True],
            kind="mergesort",
        )
        .head(20)
        .reset_index(drop=True)
    )


def configure_plot_style() -> None:
    apply_publication_style("default")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "figure.constrained_layout.use": False,
        }
    )


def draw_top5_panel(axis, rows: pd.DataFrame, sex: str, panel: str) -> None:
    categories = rows["category_label"].drop_duplicates().tolist()
    y_index = {value: index for index, value in enumerate(categories)}
    for row in rows.itertuples():
        x = int(row.display_rank) - 1
        y = y_index[row.category_label]
        recurrent = int(row.returned_call_count) >= 2
        rectangle = patches.Rectangle(
            (x - 0.48, y - 0.42),
            0.96,
            0.84,
            facecolor=BLUE if recurrent else ORANGE,
            edgecolor="#2F4F5F" if recurrent else "white",
            hatch="///" if recurrent else None,
            linewidth=0.7,
        )
        axis.add_patch(rectangle)
        axis.text(x, y, row.current_symbol, ha="center", va="center", fontsize=7.0)
    axis.set_xlim(-0.5, 4.5)
    axis.set_ylim(len(categories) - 0.5, -0.5)
    axis.set_xticks(range(5), range(1, 6))
    axis.set_yticks(range(len(categories)), categories)
    axis.set_xlabel("Non-MT within-category rank")
    axis.set_ylabel("Sex/APOE · broad cell type" if panel == "A" else "")
    axis.set_title(f"{panel}  {sex}", loc="left", fontsize=10, fontweight="bold")
    axis.grid(False)
    for y in np.arange(0.5, len(categories) - 0.5, 1):
        axis.axhline(y, color=GRID, linewidth=0.35, zorder=0)


def plot_top5(rows: pd.DataFrame, cohort: str) -> plt.Figure:
    female = rows[rows["sex"].eq("Female")]
    male = rows[rows["sex"].eq("Male")]
    maximum_rows = max(
        female["category_label"].nunique(), male["category_label"].nunique()
    )
    height = max(5.1, 0.47 * maximum_rows + 2.7)
    subtitle_y = 0.98 - 0.36 / height
    axes_top = min(0.87, 0.98 - 0.85 / height)
    figure, axes = plt.subplots(1, 2, figsize=(15, height))
    draw_top5_panel(axes[0], female, "Female", "A")
    draw_top5_panel(axes[1], male, "Male", "B")
    figure.suptitle(
        f"Top five {cohort} non-MT key drivers",
        x=0.06,
        y=0.98,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.06,
        subtitle_y,
        "Re-ranked after excluding core-MT drivers; categories without returns are omitted",
        ha="left",
        color=MUTED,
        fontsize=9,
    )
    handles = [
        patches.Patch(
            facecolor=BLUE,
            edgecolor="#2F4F5F",
            hatch="///",
            label="ACAT: ≥2 returned calls",
        ),
        patches.Patch(
            facecolor=ORANGE, edgecolor="white", label="One-call q passthrough"
        ),
    ]
    figure.legend(
        handles=handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=2,
        fontsize=8,
    )
    figure.subplots_adjust(
        left=0.15, right=0.985, top=axes_top, bottom=0.12, wspace=0.35
    )
    return figure


def top5_broad_cell_row_slots(
    rows: pd.DataFrame,
) -> list[tuple[str, str]]:
    present = set(zip(rows["broad_network"], rows["apoe_group"], strict=True))
    return [
        (network, apoe)
        for network in TOP5_BROAD_CELL_ORDER
        for apoe in APOE_ORDER
        if (network, apoe) in present
    ]


def draw_top5_broad_cell_panel(
    axis,
    rows: pd.DataFrame,
    sex: str,
    panel: str,
    row_slots: list[tuple[str, str]],
) -> None:
    category_index = {slot: index for index, slot in enumerate(row_slots)}
    sex_prefix = "F" if sex == "Female" else "M"
    category_labels = [
        f"{NETWORK_LABELS[network]} · {sex_prefix}_{apoe}"
        for network, apoe in row_slots
    ]

    for row in rows.itertuples():
        x = int(row.display_rank) - 1
        y = category_index[(row.broad_network, row.apoe_group)]
        rectangle = patches.Rectangle(
            (x - 0.48, y - 0.42),
            0.96,
            0.84,
            facecolor=BROAD_CELL_COLORS[row.broad_network],
            edgecolor="#4B5563",
            linewidth=0.45,
        )
        axis.add_patch(rectangle)
        axis.text(
            x,
            y,
            row.current_symbol,
            ha="center",
            va="center",
            fontsize=7.0,
            color=TEXT,
        )

    category_counts = (
        rows.groupby(["broad_network", "apoe_group"], sort=False)[
            "category_gene_count"
        ]
        .first()
        .astype(int)
    )
    for category, count in category_counts.items():
        if count <= 5:
            continue
        y = category_index[category]
        axis.text(
            4.64,
            y,
            f"n={count}",
            ha="left",
            va="center",
            fontsize=10.0,
            color=MUTED,
            fontweight="bold",
        )

    axis.set_xlim(-0.5, 5.45)
    axis.set_ylim(len(row_slots) - 0.5, -0.5)
    axis.set_xticks(range(5), range(1, 6))
    axis.set_yticks(range(len(row_slots)), category_labels)
    axis.set_xlabel("Within-category rank (1 = strongest)")
    axis.set_ylabel("Broad cell type · sex/APOE group" if panel == "A" else "")
    axis.set_title(f"{panel}  {sex}", loc="left", fontsize=10, fontweight="bold")
    axis.grid(False)

    networks = [network for network, _ in row_slots]
    for index in range(1, len(networks)):
        if networks[index] != networks[index - 1]:
            axis.axhline(index - 0.5, color="#9CA3AF", linewidth=0.9, zorder=0)


def plot_top5_by_broad_cell(
    rows: pd.DataFrame,
    cohort: str,
    *,
    figure_width: float = 20.5,
    minimum_height: float = 5.1,
) -> plt.Figure:
    female = rows[rows["sex"].eq("Female")]
    male = rows[rows["sex"].eq("Male")]
    row_slots = top5_broad_cell_row_slots(rows)
    height = max(minimum_height, 0.47 * len(row_slots) + 2.7)
    subtitle_y = 0.98 - 0.36 / height
    axes_top = min(0.87, 0.98 - 0.85 / height)
    figure, axes = plt.subplots(1, 2, figsize=(figure_width, height))
    draw_top5_broad_cell_panel(axes[0], female, "Female", "A", row_slots)
    draw_top5_broad_cell_panel(axes[1], male, "Male", "B", row_slots)
    figure.suptitle(
        f"Top five {cohort} non-MT key drivers",
        x=0.06,
        y=0.98,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.06,
        subtitle_y,
        "Rows align APOE groups across sex; blank rows mark categories without returns\n"
        "n = total non-MT driver genes in that category (shown when n > 5)",
        ha="left",
        va="center",
        color=MUTED,
        fontsize=9.5,
    )
    figure.text(
        0.81,
        subtitle_y - 0.018,
        "SCORE USED FOR WITHIN-CATEGORY RANKING\n"
        "1 returned call: within-call BH-adjusted KDA P\n"
        "≥2 returned calls: ACAT of returned adjusted P values\n"
        "Lower = stronger; rank 1 is lowest  •  ties alphabetical",
        ha="center",
        va="center",
        color=TEXT,
        fontsize=10.5,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#F7F9FC",
            "edgecolor": GRID,
            "linewidth": 0.7,
        },
    )
    present_networks = set(rows["broad_network"])
    handles = [
        patches.Patch(
            facecolor=BROAD_CELL_COLORS[network],
            edgecolor="#4B5563",
            linewidth=0.45,
            label=NETWORK_LABELS[network],
        )
        for network in TOP5_BROAD_CELL_ORDER
        if network in present_networks
    ]
    figure.legend(
        handles=handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.005),
        ncol=7,
        fontsize=8,
    )
    figure.subplots_adjust(
        left=0.125, right=0.985, top=axes_top, bottom=0.15, wspace=0.30
    )
    return figure


def plot_recurrence(
    rows: pd.DataFrame,
    cohort: str,
    *,
    bar_color: str | None = None,
) -> plt.Figure:
    ordered = rows.iloc[::-1].reset_index(drop=True)
    if bar_color is None:
        maximum = max(1, int(ordered["acat_category_count"].max()))
        norm = Normalize(vmin=0, vmax=maximum)
        cmap = matplotlib.colormaps["cividis"]
        colors: Any = [
            cmap(norm(value)) for value in ordered["acat_category_count"]
        ]
    else:
        colors = bar_color
    figure, axis = plt.subplots(figsize=(8, 7))
    bars = axis.barh(ordered["current_symbol"], ordered["category_count"], color=colors)
    for bar, value in zip(bars, ordered["category_count"], strict=True):
        axis.text(
            bar.get_width() + 0.06,
            bar.get_y() + bar.get_height() / 2,
            str(int(value)),
            va="center",
            fontsize=8,
            color=TEXT,
        )
    axis.set_xlim(0, float(ordered["category_count"].max()) + 1.25)
    axis.set_xlabel("Number of non-MT key-driver categories")
    axis.set_ylabel("")
    axis.set_title(
        f"Most recurrent {cohort} non-MT key drivers",
        loc="left",
        pad=30,
        fontsize=13,
        fontweight="bold",
    )
    axis.text(
        0,
        1.01,
        "Each gene is counted once per sex/APOE × broad-cell category",
        transform=axis.transAxes,
        color=MUTED,
        va="bottom",
        fontsize=9,
    )
    if bar_color is None:
        scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
        colorbar = figure.colorbar(scalar, ax=axis, pad=0.02)
        colorbar.set_label("Categories aggregated across ≥2 returned calls")
        right = 0.88
    else:
        right = 0.97
    figure.subplots_adjust(left=0.20, right=right, top=0.84, bottom=0.11)
    return figure


def prepare_broad_cell_recurrence(
    rows: pd.DataFrame,
    broad_network: str,
    *,
    cohort: str,
) -> pd.DataFrame:
    broad_cell_rows = rows.loc[
        rows["broad_network"].eq(broad_network),
        ["signature_group", "current_symbol"],
    ].drop_duplicates()
    if broad_cell_rows.empty:
        raise RuntimeError(f"No {cohort} {broad_network} key drivers found")
    unexpected_groups = sorted(
        set(broad_cell_rows["signature_group"]) - set(GROUP_ORDER)
    )
    if unexpected_groups:
        raise RuntimeError(
            f"Unexpected {cohort} {broad_network} groups: "
            + ", ".join(unexpected_groups)
        )
    recurrence = (
        broad_cell_rows.groupby("current_symbol", sort=False)["signature_group"]
        .nunique()
        .astype(int)
    )
    genes = sorted(recurrence.index, key=lambda gene: (-recurrence[gene], gene))
    present = set(
        zip(
            broad_cell_rows["signature_group"],
            broad_cell_rows["current_symbol"],
            strict=True,
        )
    )
    rows_out = []
    for group_index, group in enumerate(GROUP_ORDER, start=1):
        sex, apoe_group = group.split("_", maxsplit=1)
        for gene_index, gene in enumerate(genes, start=1):
            is_present = (group, gene) in present
            rows_out.append(
                {
                    "signature_group": group,
                    "sex": "Female" if sex == "F" else "Male",
                    "apoe_group": apoe_group,
                    "current_symbol": gene,
                    "is_key_driver_in_category": is_present,
                    "recurrence_across_six_categories": int(recurrence[gene]),
                    "group_order": group_index,
                    "gene_order": gene_index,
                }
            )
    plot_data = pd.DataFrame(rows_out)
    if int(plot_data["is_key_driver_in_category"].sum()) != len(broad_cell_rows):
        raise RuntimeError(
            f"{cohort} {broad_network} recurrence matrix lost category units"
        )
    return plot_data


def plot_broad_cell_recurrence(
    plot_data: pd.DataFrame,
) -> plt.Figure:
    genes = (
        plot_data[["current_symbol", "gene_order"]]
        .drop_duplicates()
        .sort_values("gene_order")["current_symbol"]
        .tolist()
    )
    recurrence = (
        plot_data.drop_duplicates("current_symbol")
        .set_index("current_symbol")["recurrence_across_six_categories"]
        .astype(int)
    )
    maximum_recurrence = int(recurrence.max())
    group_counts = (
        plot_data.loc[plot_data["is_key_driver_in_category"]]
        .groupby("signature_group")["current_symbol"]
        .nunique()
        .reindex(GROUP_ORDER, fill_value=0)
    )
    row_positions = {
        "F_e2": 0,
        "F_e33": 1,
        "F_e4": 2,
        "M_e2": 4,
        "M_e33": 5,
        "M_e4": 6,
    }
    matrix = np.full((7, len(genes)), np.nan)
    matrix[[0, 1, 2, 4, 5, 6], :] = 0
    gene_index = {gene: index for index, gene in enumerate(genes)}
    for row in plot_data.loc[plot_data["is_key_driver_in_category"]].itertuples():
        matrix[row_positions[row.signature_group], gene_index[row.current_symbol]] = (
            row.recurrence_across_six_categories
        )

    recurrence_colors = [
        matplotlib.colormaps["cividis"](value)
        for value in np.linspace(0.12, 0.92, 5)
    ]
    absent_color = "#EEF1F4"
    heatmap_cmap = ListedColormap([absent_color, *recurrence_colors])
    heatmap_cmap.set_bad("#FFFFFF")
    norm = BoundaryNorm(np.arange(-0.5, 6.5, 1), heatmap_cmap.N)

    figure = plt.figure(figsize=(12.6, 5.55))
    axis = figure.add_axes([0.095, 0.31, 0.885, 0.51])
    axis.imshow(
        matrix,
        cmap=heatmap_cmap,
        norm=norm,
        interpolation="none",
        aspect="auto",
    )
    axis.set_xticks(np.arange(len(genes)))
    axis.set_xticklabels(
        genes,
        rotation=90,
        ha="center",
        va="top",
        fontsize=max(4.2, min(5.4, 455 / len(genes))),
    )
    axis.set_yticks([0, 1, 2, 4, 5, 6])
    axis.set_yticklabels(
        [f"{group}  (n={int(group_counts[group])})" for group in GROUP_ORDER],
        fontsize=8.5,
    )
    axis.tick_params(axis="x", length=0, pad=3)
    axis.tick_params(axis="y", length=0, pad=5)
    axis.set_xlabel("Unique non-MT key-driver genes", fontsize=9.5, labelpad=8)
    axis.set_ylabel("")
    axis.set_xticks(np.arange(-0.5, len(genes), 1), minor=True)
    axis.set_yticks(np.arange(-0.5, 7, 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=0.35)
    axis.tick_params(which="minor", bottom=False, left=False)
    for spine in axis.spines.values():
        spine.set_visible(False)

    axis.text(
        -0.095,
        0.79,
        "FEMALE",
        transform=axis.transAxes,
        rotation=90,
        ha="center",
        va="center",
        color=BLUE,
        fontsize=8.5,
        fontweight="bold",
    )
    axis.text(
        -0.095,
        0.21,
        "MALE",
        transform=axis.transAxes,
        rotation=90,
        ha="center",
        va="center",
        color=TEAL,
        fontsize=8.5,
        fontweight="bold",
    )

    start = 0
    for value in sorted(recurrence.unique(), reverse=True):
        count = int((recurrence == value).sum())
        end = start + count
        if count >= 6:
            axis.text(
                (start + end - 1) / 2,
                -0.87,
                f"{value} categor{'y' if value == 1 else 'ies'}",
                ha="center",
                va="bottom",
                fontsize=6.3,
                color=TEXT,
                fontweight="bold",
                clip_on=False,
            )
        if end < len(genes):
            axis.axvline(end - 0.5, color="#64748B", linewidth=0.8)
        start = end

    figure.text(
        0.045,
        0.955,
        "Colored tile = gene is a key driver in that category; color = recurrence across all six categories.",
        ha="left",
        va="center",
        fontsize=9.2,
        color=TEXT,
    )
    legend_handles = [
        patches.Patch(
            facecolor=absent_color,
            edgecolor="#CBD2D9",
            linewidth=0.5,
            label="Not returned",
        )
    ] + [
        patches.Patch(
            facecolor=recurrence_colors[value - 1],
            edgecolor="#4B5563",
            linewidth=0.35,
            label=str(value),
        )
        for value in range(1, maximum_recurrence + 1)
    ]
    figure.legend(
        handles=legend_handles,
        title="Number of categories containing the gene",
        loc="upper right",
        bbox_to_anchor=(0.985, 0.995),
        frameon=False,
        ncol=6,
        columnspacing=0.8,
        handlelength=1.15,
        handleheight=0.8,
        fontsize=7.5,
        title_fontsize=8.2,
    )
    return figure


def export_figure(figure: plt.Figure, base: Path) -> list[Path]:
    base.parent.mkdir(parents=True, exist_ok=True)
    saved = save_publication_figure(
        figure,
        base,
        formats=["png", "svg", "pdf"],
        dpi=300,
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(figure)
    if len(saved) != 3:
        raise RuntimeError(f"Failed to export complete figure bundle: {base}")
    return saved


def render_figures(facts: dict[str, Any], figure_root: Path) -> dict[str, Path]:
    configure_plot_style()
    paths: dict[str, Path] = {}
    for prefix, cohort in (("ros", "ROSMAP"), ("sea", "SEA-AD")):
        top5 = facts[f"{prefix}_top5"]
        recurrence = facts[f"{prefix}_recurrence"]
        top5_base = figure_root / prefix / f"{prefix}_combo_top5"
        recurrence_base = figure_root / prefix / f"{prefix}_combo_recurrence"
        top5_figure = (
            plot_top5_by_broad_cell(top5, cohort)
            if prefix == "ros"
            else plot_top5_by_broad_cell(
                top5,
                cohort,
                figure_width=12.6,
                minimum_height=6.0,
            )
        )
        export_figure(top5_figure, top5_base)
        recurrence_figure = plot_recurrence(
            recurrence,
            cohort,
            bar_color=BLUE,
        )
        export_figure(recurrence_figure, recurrence_base)
        top5_plot_data = top5.copy()
        top5_plot_data["_sex_order"] = top5_plot_data["sex"].map(
            {"Female": 0, "Male": 1}
        )
        row_index = {
            slot: index + 1
            for index, slot in enumerate(
                top5_broad_cell_row_slots(top5_plot_data)
            )
        }
        top5_plot_data["aligned_row_index"] = [
            row_index[(network, apoe)]
            for network, apoe in zip(
                top5_plot_data["broad_network"],
                top5_plot_data["apoe_group"],
                strict=True,
            )
        ]
        top5_plot_data["broad_cell_color"] = top5_plot_data[
            "broad_network"
        ].map(BROAD_CELL_COLORS)
        top5_plot_data.sort_values(
            [
                "_sex_order",
                "aligned_row_index",
                "display_rank",
            ],
            inplace=True,
            kind="mergesort",
        )
        top5_plot_data.drop(columns="_sex_order", inplace=True)
        top5_plot_data.to_csv(
            top5_base.with_name(top5_base.name + "_plot_data.tsv"),
            sep="\t",
            index=False,
            lineterminator="\n",
        )
        recurrence.to_csv(
            recurrence_base.with_name(recurrence_base.name + "_plot_data.tsv"),
            sep="\t",
            index=False,
            lineterminator="\n",
        )
        paths[f"{prefix}_top5"] = top5_base.with_suffix(".png")
        paths[f"{prefix}_recurrence"] = recurrence_base.with_suffix(".png")
    for broad_network, stem, path_key in [
        (
            "Excitatory_neurons",
            "ros_excitatory_driver_recurrence_matrix",
            "ros_excitatory_recurrence",
        ),
        (
            "Inhibitory_neurons",
            "ros_inhibitory_driver_recurrence_matrix",
            "ros_inhibitory_recurrence",
        ),
        (
            "Astrocytes",
            "ros_astrocyte_driver_recurrence_matrix",
            "ros_astrocyte_recurrence",
        ),
        (
            "OPCs",
            "ros_opc_driver_recurrence_matrix",
            "ros_opc_recurrence",
        ),
    ]:
        plot_data = prepare_broad_cell_recurrence(
            facts["ros_categories"],
            broad_network,
            cohort="ROSMAP",
        )
        base = figure_root / "ros" / stem
        export_figure(plot_broad_cell_recurrence(plot_data), base)
        plot_data.to_csv(
            base.with_name(base.name + "_plot_data.tsv"),
            sep="\t",
            index=False,
            lineterminator="\n",
        )
        paths[path_key] = base.with_suffix(".png")
    sea_excitatory_plot_data = prepare_broad_cell_recurrence(
        facts["sea_categories"],
        "Excitatory_neurons",
        cohort="SEA-AD",
    )
    sea_excitatory_base = (
        figure_root / "sea" / "sea_excitatory_driver_recurrence_matrix"
    )
    export_figure(
        plot_broad_cell_recurrence(sea_excitatory_plot_data),
        sea_excitatory_base,
    )
    sea_excitatory_plot_data.to_csv(
        sea_excitatory_base.with_name(
            sea_excitatory_base.name + "_plot_data.tsv"
        ),
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    paths["sea_excitatory_recurrence"] = sea_excitatory_base.with_suffix(
        ".png"
    )
    return paths


def update_rosmap_section_divider(slide) -> None:
    set_text(slide, "TextBox 3", "ROSMAP KDA analysis")
    remove_named_shapes(slide, ["TextBox 4"])
    step_text = {
        "TextBox 9": ("Run DEG", 2034828),
        "TextBox 12": ("Call key driver", 2790427),
        "TextBox 15": ("ACAT aggregation", 3551805),
        "TextBox 18": ("Result analysis", 4295829),
    }
    for shape_name, (text, top) in step_text.items():
        set_text(slide, shape_name, text)
        shape = next(item for item in slide.shapes if item.name == shape_name)
        shape.top = top
        shape.height = 226216


def update_four_steps_slide(slide) -> None:
    text_updates = {
        "TextBox 2": "Four steps: one KDA query per contrast",
        "TextBox 7": "DEG",
        "TextBox 10": "AD-versus-NCI DEG for each contrast",
        "TextBox 14": "Mitochondrial query",
        "TextBox 15": "MT DEGs",
        "TextBox 17": "Build query per contrast with MT DEGs",
        "TextBox 22": "Use call_key_drivers",
        "TextBox 24": (
            "KDA run for valid DEG contrast valid\n"
            "number of genes in query ≥ 3"
        ),
        "TextBox 28": "Category result",
        "TextBox 29": "gene × category",
        "TextBox 31": (
            "Aggregate genes across fine cell type for the same broad cell "
            "type with ACAT."
        ),
    }
    for shape_name, text in text_updates.items():
        set_text(slide, shape_name, text)

    geometry = {
        "TextBox 7": (804672, 2267712, 2157984, 347788),
        "TextBox 10": (932688, 4192099, 1901952, 403187),
        "TextBox 15": (3639312, 3017520, 2157984, 255455),
        "TextBox 17": (3767328, 4192099, 1901952, 403187),
        "TextBox 22": (6473952, 3017520, 2157984, 255455),
        "TextBox 24": (6601968, 4105152, 1940298, 577081),
        "TextBox 31": (9436608, 4105152, 1901952, 577081),
    }
    for shape_name, (left, top, width, height) in geometry.items():
        shape = next(item for item in slide.shapes if item.name == shape_name)
        shape.left = left
        shape.top = top
        shape.width = width
        shape.height = height


def insert_broad_cell_recurrence_slide(
    prs: Presentation,
    figure_path: Path,
    *,
    cohort: str = "ROSMAP",
    broad_cell_adjective: str,
    unique_gene_count: int,
    category_unit_count: int,
    transition: str,
    insert_index: int = 10,
    title: str | None = None,
    subtitle: str | None = None,
) -> None:
    ui.set_notes_body_template(
        prs.slides[0].notes_slide.notes_placeholder._element
    )
    slide = ui.new_slide(prs)
    ui.add_title_block(
        slide,
        title
        or f"{cohort} {broad_cell_adjective} drivers recur across sex/APOE groups",
        subtitle
        or f"{unique_gene_count} unique non-MT genes across {category_unit_count} gene × category combinations; columns are ordered by recurrence, then alphabetically.",
    )
    picture = slide.shapes.add_picture(
        str(figure_path),
        Inches(0.58),
        Inches(1.34),
        width=Inches(12.17),
        height=Inches(5.36),
    )
    ui.set_alt_text(
        picture,
        f"Matrix of {unique_gene_count} {cohort} {broad_cell_adjective} non-mitochondrial key-driver genes across six female and male sex/APOE categories; colored cells mark category membership and color indicates recurrence across categories.",
    )
    picture.name = (
        f"{cohort} {broad_cell_adjective} non-MT key-driver recurrence matrix"
    )
    set_notes(
        slide,
        f"Show how {cohort} {broad_cell_adjective} key drivers recur across the six sex/APOE categories.",
        f"Rows are the three female groups followed by the three male groups. Columns contain all {unique_gene_count} distinct non-mitochondrial key-driver genes observed in the {broad_cell_adjective} broad cell type. A colored tile means the gene is present in that category; its color gives the total number of the six categories containing that gene. Columns are ordered from highest to lowest recurrence and alphabetically within ties.",
        "Category recurrence is descriptive presence across returned-only category results. It is not an effect size, an independent replication count, or a sex/APOE interaction test.",
        transition,
    )
    slide_id_list = prs.slides._sldIdLst
    new_slide_id = slide_id_list[-1]
    slide_id_list.remove(new_slide_id)
    slide_id_list.insert(insert_index, new_slide_id)


def update_slides_1_to_18(prs: Presentation, facts: dict[str, Any], figures: dict[str, Path]) -> None:
    slides = prs.slides

    # Slide 1
    set_text(slides[0], "TextBox 2", "ROSMAP and SEA-AD sex/APOE key-driver analysis")
    remove_named_shapes(
        slides[0],
        [
            "TextBox 1",
            "TextBox 3",
            "Rounded Rectangle 4",
            "TextBox 6",
            "TextBox 7",
            "Rounded Rectangle 8",
            "TextBox 9",
            "TextBox 10",
            "TextBox 11",
        ],
    )
    set_notes(
        slides[0],
        "Introduce the analysis in both cohorts.",
        "Part I summarizes 194 ROSMAP KDA calls and 381 non-MT gene-by-category units. Part II summarizes 22 SEA-AD calls against SEA-AD-specific networks and 44 units.",
        "Each contrast contributes at most one mitochondrial DEG query and one KDA call.",
        "Compare the cohort and run structures before reviewing each branch.",
    )

    # Slide 2
    set_text(
        slides[1],
        "TextBox 2",
        "Summary for two cohorts: ROSMAP and SEA-AD",
    )
    set_text(
        slides[1],
        "TextBox 3",
        "Each contrast contributes at most one mitochondrial DEG query; significant non-MT returns are aggregated by category.",
    )
    set_text(slides[1], "TextBox 8", "324")
    set_text(slides[1], "TextBox 9", "planned contrasts")
    set_text(slides[1], "TextBox 11", "194")
    set_text(slides[1], "TextBox 12", "KDA calls")
    set_text(slides[1], "TextBox 14", "381")
    set_text(slides[1], "TextBox 15", "gene × category combinations")
    set_text(
        slides[1],
        "TextBox 17",
        "Builds one query with DEG MT genes for each contrast.",
    )
    set_text(
        slides[1],
        "TextBox 19",
        "Aggregate KDA returned key driver using ACAT for each category",
    )
    set_text(
        slides[1],
        "TextBox 21",
        "Final 381 combinations represent 228 unique genes in 29 categories.",
    )
    set_text(slides[1], "TextBox 26", "774")
    set_text(slides[1], "TextBox 27", "planned contrasts")
    set_text(slides[1], "TextBox 29", "22")
    set_text(slides[1], "TextBox 30", "KDA calls")
    set_text(slides[1], "TextBox 32", "44")
    set_text(slides[1], "TextBox 33", "gene × category combinations")
    set_text(
        slides[1], "TextBox 35", "Uses SEA-AD-specific Bayesian networks."
    )
    set_text(
        slides[1],
        "TextBox 37",
        "Final 44 combinations represent 43 unique genes in 5 categories",
    )
    set_text(
        slides[1],
        "TextBox 39",
        "20 of 22 calls are M_e33.",
    )
    set_notes(
        slides[1],
        "Give a side-by-side map of the two analyses.",
        "ROSMAP is the primary analysis: 324 planned contrasts yield 194 KDA calls and 381 gene-by-category combinations, representing 228 unique genes in 29 categories. SEA-AD is the validation analysis: 774 planned contrasts yield 22 KDA calls and 44 combinations, representing 43 unique genes in five categories.",
        "Twenty of 22 SEA-AD calls are M_e33. Categories without calls are unavailable, not negative tests.",
        "Review the ROSMAP branch first.",
    )

    # Slide 3
    update_rosmap_section_divider(slides[2])
    set_notes(
        slides[2],
        "Introduce the ROSMAP fine-cell KDA branch.",
        "The section defines the one-query-per-contrast design, the eligibility funnel, query construction, and returned-only simple aggregation.",
        "The analysis uses existing validated KDA results and does not pool sex/APOE groups.",
        "Start with the four counting units.",
    )

    # Slide 4
    update_four_steps_slide(slides[3])
    set_notes(
        slides[3],
        "Separate contrast, mitochondrial query, KDA call, and category result.",
        "A contrast is one signed DEG result and contributes one core-MT DEG query. A mapped query of at least three genes becomes one KDA call. A category is one sex/APOE group crossed with one broad network; returned non-MT drivers from eligible fine-cell runs are aggregated within it.",
        "A candidate driver can be a non-DEG, non-mitochondrial network gene.",
        "Apply the definitions to the 324-contrast universe.",
    )

    # Slide 5
    set_text(slides[4], "TextBox 2", "54 fine cell types create 324 planned contrasts")
    set_text(
        slides[4],
        "TextBox 3",
        "Each contrast contributes one mitochondrial DEG query and at most one KDA call.",
    )
    set_text(slides[4], "TextBox 8", "324 DEG contrasts")
    next(
        shape for shape in slides[4].shapes if shape.name == "TextBox 8"
    ).height = 347788
    set_text(slides[4], "TextBox 9", "one query per contrast")
    set_text(slides[4], "TextBox 11", "194 call_key_drivers calls")
    set_text(
        slides[4],
        "TextBox 12",
        "All valid DEG contrast and number of genes in queries ≥3",
    )
    next(
        shape for shape in slides[4].shapes if shape.name == "TextBox 12"
    ).height = 375487
    call_count_box = next(
        shape for shape in slides[4].shapes if shape.name == "TextBox 11"
    )
    # Match the wider, slightly left-shifted call-count box on the reviewed
    # slide 5 so the full label has the intended breathing room.
    call_count_box.left = 8310880
    call_count_box.width = 3145536
    set_text(slides[4], "TextBox 14", "Mutually exclusive contrast outcome")
    set_text(slides[4], "TextBox 16", "Contrasts")
    set_text(slides[4], "TextBox 24", "3")
    set_text(slides[4], "TextBox 32", "95")
    set_text(slides[4], "TextBox 40", "32")
    set_text(slides[4], "TextBox 48", "194")
    set_text(slides[4], "TextBox 64", "324")
    set_text(slides[4], "TextBox 66", "194 calls")
    set_text(slides[4], "TextBox 30", "Number of genes in query: 0")
    query_zero = next(
        shape for shape in slides[4].shapes if shape.name == "TextBox 30"
    )
    query_zero.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    set_split_text(
        slides[4],
        "TextBox 38",
        "Number of genes in query: ",
        "1–2",
        prefix_size=9,
        tail_size=9.5,
    )
    query_one_two = next(
        shape for shape in slides[4].shapes if shape.name == "TextBox 38"
    )
    query_one_two.top = 4356132
    query_one_two.height = 203133
    set_split_text(
        slides[4],
        "TextBox 46",
        "Number of genes in query: ",
        ">=3",
        prefix_size=9,
        tail_size=9.5,
    )
    set_notes(
        slides[4],
        "Show how 324 contrasts become 194 KDA calls.",
        "Three source contrasts are invalid, 95 valid contrasts have an empty effective query, 32 retain one or two mapped genes, and 194 meet the three-gene floor.",
        "Skipped contrasts have no KDA result and are not completed null tests.",
        "Clarify the execution gate and source failures.",
    )

    # Slide 6
    set_text(slides[5], "TextBox 11", "194")
    set_text(slides[5], "TextBox 12", "included KDA calls")
    set_text(
        slides[5], "TextBox 14", "All 194 validated completed calls enter the aggregate."
    )
    set_text(slides[5], "TextBox 16", "164 significant • 30 completed empty")
    set_text(
        slides[5],
        "TextBox 18",
        "The 164 significant calls returned 1,833 rows before mitochondrial filtering.",
    )
    set_text(
        slides[5],
        "TextBox 55",
        "3 unavailable comparisons = 3 unavailable KDA calls",
    )
    set_notes(
        slides[5],
        "Clarify the three-gene execution floor and the three invalid source contrasts.",
        "All 194 calls meeting the mapped-query floor were completed: 164 returned significant drivers and 30 returned none. The three concrete invalid MAST contrasts remain unavailable.",
        "The minimum is an execution rule; small queries and low cell counts still require cautious interpretation.",
        "Inspect how the mitochondrial query is constructed.",
    )

    # Slide 7
    set_text(
        slides[6],
        "TextBox 14",
        "Significant positive and negative DEGs enter the query.",
    )
    set_text(
        slides[6],
        "TextBox 16",
        "Query = DEG rule ∩ core_mito_protein",
    )
    set_text(
        slides[6],
        "TextBox 33",
        "Membership counts can repeat genes across contrasts; each contrast contributes one query.",
    )
    set_notes(
        slides[6],
        "Explain the ROSMAP mitochondrial query.",
        "The DEG filters identify 4,258 positive and 5,004 negative core-MT memberships. Together these are 9,262 provisional memberships across contrasts; 7,933 remain after network-background mapping. Each contrast contributes one query and at most one KDA call.",
        "These are repeated memberships across contrasts, not unique genes and not driver counts.",
        "Review the returned non-MT top-five display.",
    )

    # Slides 8-10
    set_text(slides[7], "TextBox 2", "Top five: 123 non-MT entries across 29 categories")
    top5_picture = replace_picture(
        slides[7],
        "Simple returned-only Phase 20 female and male panels showing up to five non-MT genes per sex/APOE by broad-cell category",
        figures["ros_top5"],
        "ROSMAP top-five non-MT key drivers by sex/APOE and broad-cell category",
    )
    top5_picture.left = Inches(0.67)
    top5_picture.top = Inches(0.87)
    top5_picture.width = Inches(12.00)
    top5_picture.height = Inches(6.53)
    set_notes(
        slides[7],
        "Present the ROSMAP top-five results.",
        "The figure displays up to five non-MT drivers in each of 29 populated categories, for 123 displayed entries. For rows containing more than five drivers, n reports the total number of distinct non-MT driver genes in that category. For a gene returned by one KDA call, the ranking score is that call's within-call BH-adjusted KDA P value. For a gene returned by at least two calls, the score is the equal-weight ACAT combination of the returned adjusted P values. Lower scores rank more strongly; ties are resolved alphabetically. Female and male rows are aligned by broad cell type and APOE group, with blank counterpart rows where only one sex has returns. Microglia is placed last because no female Microglia category has returned drivers. Each broad-cell color is held constant across panels.",
        "Top five is a display cap, and returned-only scores are exploratory without final across-gene FDR control.",
        "Summarize recurrence across categories.",
    )

    set_text(slides[8], "TextBox 2", "RPS15 recurs across 11 returned-only categories")
    replace_picture(
        slides[8],
        "Simple returned-only Phase 20 bar chart of the twenty non-MT genes appearing in the most sex/APOE by broad-cell categories",
        figures["ros_recurrence"],
        "ROSMAP recurrence chart for the twenty broadest non-MT key drivers",
    )
    remove_named_shapes(slides[8], ["Oval 11", "TextBox 12"])
    set_text(
        slides[8],
        "TextBox 14",
        "RPS15: 11 categories, 6 groups, 4 networks.",
    )
    set_text(
        slides[8],
        "TextBox 16",
        "RPL11: 10 categories, 6 groups, 4 networks.",
    )
    for shape_name, top, height in [
        ("Oval 13", 2770632, 77724),
        ("TextBox 14", 2642615, 403187),
        ("Oval 15", 3328415, 77724),
        ("TextBox 16", 3200399, 403187),
    ]:
        shape = next(item for item in slides[8].shapes if item.name == shape_name)
        shape.top = top
        shape.height = height
    set_notes(
        slides[8],
        "Interpret category recurrence.",
        "RPS15 occurs in 11 categories from 22 returned calls. RPL11 occurs in 10 categories from 24 calls. Bar length and the end label show the category count.",
        "Category presence is descriptive and not independent replication.",
        "Summarize the full ROSMAP output scale.",
    )

    set_text(
        slides[9],
        "TextBox 2",
        "ROSMAP KDA summary: 381 non-MT gene x category combinations represent 228 distinct genes",
    )
    next(
        shape for shape in slides[9].shapes if shape.name == "TextBox 2"
    ).height = 701731
    set_text(
        slides[9],
        "TextBox 6",
        "non-MT gene returned from call_key_driver (before aggregation)",
    )
    ros_returned_label = next(
        shape for shape in slides[9].shapes if shape.name == "TextBox 6"
    )
    ros_returned_label.height = 606320
    ros_returned_label.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    ros_returned_label.text_frame.add_paragraph()
    set_text(
        slides[9],
        "TextBox 9",
        "non-MT gene × category combinations",
    )
    next(
        shape for shape in slides[9].shapes if shape.name == "TextBox 9"
    ).height = 350865
    for name, value in {
        "TextBox 5": "623",
        "TextBox 8": "381",
        "TextBox 11": "228",
        "TextBox 14": "29",
        "TextBox 17": "123",
    }.items():
        set_text(slides[9], name, value)
    set_text(
        slides[9],
        "TextBox 23",
        "F_e4 81 • M_e33 79 • M_e2 70\nF_e33 56 • F_e2 54 • M_e4 41",
    )
    set_text(
        slides[9],
        "TextBox 25",
        "Excitatory 153 • Inhibitory 146 • Astrocytes 32 • OPCs 21\nOligo 18 • Vasculature 6 • Microglia 5",
    )
    set_text(slides[9], "TextBox 28", "Most recurrent genes")
    next(
        shape for shape in slides[9].shapes if shape.name == "TextBox 28"
    ).height = 289310
    top_six = [("RPS15", 11), ("RPL11", 10), ("RPLP1", 8), ("RPL15", 7), ("SELENOM", 7), ("SELENOW", 6)]
    for (gene_box, bar_name, count_box), (gene, count) in zip(
        [
            ("TextBox 29", "Rectangle 30", "TextBox 31"),
            ("TextBox 32", "Rectangle 33", "TextBox 34"),
            ("TextBox 35", "Rectangle 36", "TextBox 37"),
            ("TextBox 38", "Rectangle 39", "TextBox 40"),
            ("TextBox 41", "Rectangle 42", "TextBox 43"),
            ("TextBox 44", "Rectangle 45", "TextBox 46"),
        ],
        top_six,
        strict=True,
    ):
        set_text(slides[9], gene_box, gene)
        set_text(slides[9], count_box, str(count))
        bar = next(shape for shape in slides[9].shapes if shape.name == bar_name)
        bar.width = Inches(2.62 * count / 11)
    set_notes(
        slides[9],
        "Summarize the scale and distribution of the ROSMAP output.",
        "The 623 retained non-MT returned rows form 381 gene-by-category units representing 228 genes across 29 categories. The lower panels show their group, network, and recurrence distributions.",
        "Counts condition on significant within-call returns and unequal call opportunities.",
        "Move to the SEA-AD-specific-network analysis.",
    )

    # Slides 11-15
    set_text(slides[10], "TextBox 3", "SEA-AD KDA analysis")
    remove_named_shapes(slides[10], ["TextBox 4"])
    set_notes(
        slides[10],
        "Introduce the SEA-AD-specific-network analysis.",
        "The section moves from 774 supertype-by-stratum contrasts to 22 executable KDA calls, then shows top-five, recurrence, and aggregate summaries.",
        "The active calls are strongly concentrated in M_e33.",
        "Start with the contrast-level funnel.",
    )

    set_text(slides[11], "TextBox 1", "129 SEA-AD supertypes create 774 planned contrasts")
    set_text(
        slides[11],
        "TextBox 2",
        "One mitochondrial DEG query per supertype × sex/APOE contrast.",
    )
    set_text(slides[11], "TextBox 7", "774 DEG contrasts")
    next(
        shape for shape in slides[11].shapes if shape.name == "TextBox 7"
    ).height = 347788
    set_text(slides[11], "TextBox 8", "one query per contrast")
    set_text(slides[11], "TextBox 10", "22 call_key_drivers calls")
    next(
        shape for shape in slides[11].shapes if shape.name == "TextBox 10"
    ).height = 347788
    set_text(
        slides[11],
        "TextBox 11",
        "All valid DEG contrast and number of genes in query ≥ 3",
    )
    next(
        shape for shape in slides[11].shapes if shape.name == "TextBox 11"
    ).height = 433965
    set_text(slides[11], "TextBox 13", "Mutually exclusive contrast outcome")
    set_text(slides[11], "TextBox 15", "Contrasts")
    for name, value in {
        "TextBox 21": "393",
        "TextBox 27": "348",
        "TextBox 33": "11",
        "TextBox 39": "22",
        "TextBox 51": "774",
        "TextBox 53": "22 calls",
    }.items():
        set_text(slides[11], name, value)
    set_text(
        slides[11],
        "TextBox 54",
        "Availability remains unbalanced: 20 M_e33 calls, one F_e33 call, and one F_e4 call.",
    )
    for shape_name, text, top, height in [
        ("TextBox 19", "Source DEG contrast not valid", 3386869, 203133),
        ("TextBox 25", "Number of genes in query: 0", 3816637, 203133),
        ("TextBox 31", "Number of genes in query: 1–2", 4246404, 203133),
        ("TextBox 37", "Number of genes in query: >=3", 4676173, 203133),
    ]:
        set_text(slides[11], shape_name, text)
        shape = next(
            item for item in slides[11].shapes if item.name == shape_name
        )
        shape.top = top
        shape.height = height
    set_notes(
        slides[11],
        "Show how 774 SEA-AD contrasts reduce to 22 executable calls.",
        "There are 393 non-estimable source contrasts, 348 estimable contrasts with an empty FDR-only query, 11 with one or two mapped genes, and 22 meeting the three-gene floor.",
        "A skipped contrast is unavailable and is not a negative validation result.",
        "Inspect the returned non-MT candidates.",
    )

    set_text(slides[12], "TextBox 1", "Top-five display: 17 non-MT entries across 5 categories")
    sea_top5_picture = replace_picture(
        slides[12],
        "VH12 SEA-AD-network top-five non-mitochondrial key drivers by sex/APOE and broad-cell category",
        figures["sea_top5"],
        "SEA-AD top-five non-MT key drivers by sex/APOE and broad-cell category",
    )
    sea_top5_picture.left = Inches(0.67)
    sea_top5_picture.top = Inches(1.05)
    sea_top5_picture.width = Inches(12.00)
    sea_top5_picture.height = Inches(5.71)
    remove_named_shapes(slides[12], ["TextBox 3"])
    set_notes(
        slides[12],
        "Present leading SEA-AD non-MT candidates.",
        "Seventeen entries appear across F_e33 excitatory, F_e4 astrocyte, and three M_e33 categories. As on the ROSMAP display, rows are aligned across female and male panels, colors identify broad cell types consistently, and n gives the total non-MT driver count when a category contains more than five genes. Within each category, one returned call passes through its within-call adjusted KDA P value, while at least two returned calls are combined by ACAT; lower scores rank more strongly.",
        "Top five is a display cap and the five populated categories expose strong availability imbalance.",
        "Review recurrence across those categories.",
    )

    set_text(slides[13], "TextBox 1", "PJVK is the only gene recurring across 2 SEA-AD categories")
    replace_picture(
        slides[13],
        "VH12 SEA-AD-network bar chart of the twenty most recurrent non-mitochondrial key drivers",
        figures["sea_recurrence"],
        "SEA-AD recurrence chart for the twenty broadest non-MT key drivers",
    )
    set_text(
        slides[13],
        "TextBox 13",
        "PJVK: 2 categories, 1 group, 2 networks.",
    )
    set_text(
        slides[13],
        "TextBox 17",
        "The remaining 19 displayed genes occur in one category.",
    )
    remove_named_shapes(
        slides[13],
        ["Oval 10", "TextBox 11", "Oval 14", "TextBox 15"],
    )
    for shape_name, top in {
        "Oval 12": 2770632,
        "TextBox 13": 2642615,
        "Oval 16": 3328415,
        "TextBox 17": 3200399,
    }.items():
        next(shape for shape in slides[13].shapes if shape.name == shape_name).top = top
    set_notes(
        slides[13],
        "Interpret SEA-AD category recurrence.",
        "PJVK is the only gene present in two categories: M_e33 excitatory and inhibitory neurons. Every other gene on the top-20 display occurs in one category.",
        "Five return-bearing categories impose a low recurrence ceiling.",
        "Summarize the SEA-AD output scale.",
    )

    set_text(
        slides[14],
        "TextBox 1",
        "SEA-AD KDA summary: 44 non-MT gene x category combinations represent 43 distinct genes",
    )
    next(
        shape for shape in slides[14].shapes if shape.name == "TextBox 1"
    ).height = 809452
    set_text(
        slides[14],
        "TextBox 4",
        "non-MT gene returned from call_key_driver (before aggregation)",
    )
    next(
        shape for shape in slides[14].shapes if shape.name == "TextBox 4"
    ).height = 498598
    set_text(
        slides[14],
        "TextBox 7",
        "gene × category combinations",
    )
    next(
        shape for shape in slides[14].shapes if shape.name == "TextBox 7"
    ).height = 350865
    for name, value in {
        "TextBox 3": "54",
        "TextBox 6": "44",
        "TextBox 9": "43",
        "TextBox 12": "5",
        "TextBox 15": "17",
    }.items():
        set_text(slides[14], name, value)
    set_text(slides[14], "TextBox 19", "Where the 44 combinations occur")
    next(
        shape for shape in slides[14].shapes if shape.name == "TextBox 19"
    ).height = 289310
    set_text(
        slides[14], "TextBox 21", "M_e33 39 • F_e4 3 • F_e33 2 • other groups 0"
    )
    set_text(
        slides[14],
        "TextBox 23",
        "Excitatory 27 • Inhibitory 12 • Astrocytes 3 • Oligo 2\nMicroglia, OPCs, Vasculature 0",
    )
    set_text(
        slides[14],
        "TextBox 28",
        "20 call_key_driver with returned results; 2 completed empty.",
    )
    next(
        shape for shape in slides[14].shapes if shape.name == "TextBox 28"
    ).height = 224677
    set_text(
        slides[14],
        "TextBox 30",
        "112 significant return rows before mitochondrial filtering.",
    )
    set_text(slides[14], "TextBox 32", "58 core-MitoCarta rows excluded.")
    set_text(slides[14], "TextBox 34", "54 non-MT rows retained for aggregation.")
    remove_named_shapes(slides[14], ["TextBox 35"])
    set_notes(
        slides[14],
        "Summarize the SEA-AD output.",
        "The 54 retained rows form 44 category units representing 43 genes across five categories. Thirty-nine units and 20 of 22 active calls are M_e33.",
        "Returned-only scores remain exploratory and are not final-FDR controlled across genes.",
        "Compare the driver sets across cohorts.",
    )

    # Slides 16-18
    set_text(
        slides[15],
        "TextBox 4",
        "ROSMAP and SEA-AD results are compared at gene and matched-context levels.",
    )
    set_notes(
        slides[15],
        "Frame the cross-cohort comparison.",
        "Part 3 compares driver symbols, category contexts, and all six cross-cohort unit pairings formed by the shared genes.",
        "This is a cross-cohort and cross-network comparison, not an isolated test of cohort biology.",
        "Define gene- and category-level agreement.",
    )

    for name, value in {
        "TextBox 7": "228",
        "TextBox 10": "43",
        "TextBox 17": "381",
        "TextBox 20": "44",
    }.items():
        set_text(slides[16], name, value)
    set_text(
        slides[16],
        "TextBox 22",
        "Strict context agreement; assessed within five SEA-AD return-bearing categories.",
    )
    set_text(
        slides[16],
        "TextBox 23",
        "Four SEA-AD return-bearing categories also contain ROSMAP returns, yet none shares a driver.",
    )
    set_notes(
        slides[16],
        "Define gene-level and category-level agreement.",
        "Gene-level overlap asks whether a symbol appears anywhere among 228 ROSMAP and 43 SEA-AD genes. Category agreement also requires the same sex/APOE group and broad network among 381 and 44 units.",
        "Availability limits context comparison; four populated categories exist in both result sets.",
        "State the gene-level overlap.",
    )

    set_text(slides[17], "TextBox 1", "3 of 43 SEA-AD drivers also return in ROSMAP")
    set_text(
        slides[17],
        "TextBox 2",
        "The two cohorts show limited gene overlap and no exact category match.",
    )
    set_text(slides[17], "TextBox 4", "43")
    set_text(slides[17], "TextBox 7", "3 (7%)")
    set_text(slides[17], "TextBox 10", "0")
    set_text(slides[17], "TextBox 14", "The 3 shared genes")
    set_text(slides[17], "TextBox 15", "LAGE3  •  MIPOL1  •  PAPOLA")
    set_text(
        slides[17],
        "TextBox 16",
        "None appears on both cohorts’ top-20 recurrence displays.",
    )
    set_text(
        slides[17],
        "TextBox 17",
        "All three are M_e33 in SEA-AD, but their ROSMAP categories differ.",
    )
    set_notes(
        slides[17],
        "State the gene-level overlap.",
        "LAGE3, MIPOL1, and PAPOLA are shared: three of 43 SEA-AD genes, or seven percent. No shared gene keeps both group and broad-cell context.",
        "Gene overlap is exploratory and influenced by cohort-specific topology and unbalanced call availability.",
        "Inspect the three genes' contexts directly.",
    )


def rebuild_slides_19_to_24(prs: Presentation) -> None:
    slides = prs.slides

    # Slide 19: direct gene-by-context matrix.
    slide = slides[18]
    clear_slide(slide)
    ui.add_title_block(
        slide,
        "No driver-category pair matches exactly",
        "The three shared genes reappear in different sex/APOE and/or broad-cell contexts.",
    )
    ui.add_table(
        slide,
        ["Gene", "SEA-AD category", "ROSMAP category or categories", "Preserved context"],
        [
            ["LAGE3", "M_e33 · Inhibitory", "F_e2, F_e4, M_e2 · Excitatory", "None"],
            ["MIPOL1", "M_e33 · Excitatory", "F_e4, M_e33 · Inhibitory", "M_e33 group only"],
            ["PAPOLA", "M_e33 · Oligodendrocytes", "F_e4 · OPCs", "None"],
        ],
        0.82,
        1.63,
        [1.35, 2.60, 4.65, 2.75],
        row_h=0.78,
        header_h=0.52,
        font_size=9.3,
    )
    ui.add_rect(slide, 0.90, 5.15, 11.50, 1.08, color=ui.PALE_RED, outline=None)
    ui.add_text(
        slide,
        "0 of 44 SEA-AD gene × category units has an exact ROSMAP match.",
        1.16,
        5.43,
        10.98,
        0.38,
        size=17,
        color=ui.VERMILION_TEXT,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )
    set_notes(
        slide,
        "Show the direct context matrix for all three shared genes.",
        "LAGE3 and PAPOLA retain neither group nor broad cell type. MIPOL1 retains M_e33 in one ROSMAP category but switches from excitatory to inhibitory neurons.",
        "Zero exact matches is conditional on the available returned-only units, not a negative result for unexecuted categories.",
        "Separate gene overlap from context preservation.",
    )

    # Slide 20: three gene cards.
    slide = slides[19]
    clear_slide(slide)
    ui.add_title_block(
        slide,
        "Only MIPOL1 preserves the sex/APOE group",
        "No shared gene preserves broad-cell context in this analysis.",
    )
    cards = [
        (
            "LAGE3",
            ui.PALE_SKY,
            ui.BLUE,
            "SEA-AD\nM_e33 · Inhibitory",
            "ROSMAP\nF_e2 / F_e4 / M_e2 · Excitatory",
            "No matching dimension",
        ),
        (
            "MIPOL1",
            ui.PALE_GREEN,
            ui.TEAL,
            "SEA-AD\nM_e33 · Excitatory",
            "ROSMAP\nF_e4 / M_e33 · Inhibitory",
            "M_e33 preserved once",
        ),
        (
            "PAPOLA",
            ui.PALE_GOLD,
            ui.GOLD,
            "SEA-AD\nM_e33 · Oligodendrocytes",
            "ROSMAP\nF_e4 · OPCs",
            "No matching dimension",
        ),
    ]
    for index, (gene, bg, accent, sea, ros, result) in enumerate(cards):
        x = 0.65 + index * 4.12
        ui.add_rect(slide, x, 1.55, 3.82, 4.70, color=bg, outline=None)
        ui.add_text(
            slide,
            gene,
            x + 0.28,
            1.87,
            3.26,
            0.46,
            size=20,
            color=ui.NAVY,
            bold=True,
            font=ui.FONT_HEAD,
        )
        ui.add_text(slide, sea, x + 0.28, 2.58, 3.26, 0.86, size=12, color=ui.DARK)
        ui.add_text(slide, ros, x + 0.28, 3.66, 3.26, 1.12, size=12, color=ui.DARK)
        ui.add_rect(slide, x + 0.24, 5.17, 3.34, 0.64, color=ui.WHITE, outline=accent)
        ui.add_text(
            slide,
            result,
            x + 0.36,
            5.34,
            3.10,
            0.28,
            size=10.5,
            color=ui.readable_accent(accent),
            bold=True,
            align=PP_ALIGN.CENTER,
        )
    set_notes(
        slide,
        "Summarize partial context preservation for each shared gene.",
        "MIPOL1 produces the only same-group pairing: SEA-AD M_e33 excitatory versus ROSMAP M_e33 inhibitory. LAGE3 and PAPOLA change both group and broad cell type.",
        "The categories are non-independent because a gene can occupy multiple ROSMAP units.",
        "Count all cross-cohort unit pairings.",
    )

    # Slide 21: pairing table.
    slide = slides[20]
    clear_slide(slide)
    ui.add_title_block(
        slide,
        "Six cross-cohort unit pairings arise from three shared genes",
        "A SEA-AD unit is paired with every ROSMAP unit carrying the same gene.",
    )
    ui.add_table(
        slide,
        ["Gene", "SEA-AD units", "ROSMAP units", "Cross-cohort pairs", "Same group", "Same cell type", "Exact"],
        [
            ["LAGE3", "1", "3", "3", "0", "0", "0"],
            ["MIPOL1", "1", "2", "2", "1", "0", "0"],
            ["PAPOLA", "1", "1", "1", "0", "0", "0"],
            ["TOTAL", "3", "6", "6", "1", "0", "0"],
        ],
        0.68,
        1.72,
        [1.50, 1.50, 1.55, 2.05, 1.55, 1.75, 1.15],
        row_h=0.58,
        header_h=0.62,
        font_size=9.0,
        highlight_last=True,
    )
    ui.add_rect(slide, 0.90, 5.35, 11.50, 0.88, color=ui.PALE_SKY, outline=None)
    ui.add_text(
        slide,
        "Only one of six pairings preserves sex/APOE group; none preserves broad-cell type.",
        1.15,
        5.60,
        11.00,
        0.34,
        size=15.5,
        color=ui.BLUE,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    set_notes(
        slide,
        "Make the unit-pair denominator explicit.",
        "LAGE3 contributes three pairings, MIPOL1 two, and PAPOLA one. Only the MIPOL1 M_e33 pairing preserves the group; no pairing preserves cell type or full context.",
        "Pairings are descriptive and non-independent.",
        "Summarize the corresponding percentages.",
    )

    # Slide 22: three context metrics.
    slide = slides[21]
    clear_slide(slide)
    ui.add_title_block(
        slide,
        "Context preservation is minimal across six pairings",
        "Exact replication requires both the same sex/APOE group and the same broad-cell type.",
    )
    metrics = [
        ("0%", "same broad cell type\n0 of 6 pairings", ui.PALE_SKY, ui.BLUE),
        ("17%", "same sex/APOE group\n1 of 6 pairings", ui.PALE_GOLD, ui.GOLD),
        ("0%", "exact category match\n0 of 6 pairings", ui.PALE_RED, ui.VERMILION),
    ]
    for index, (value, label, bg, accent) in enumerate(metrics):
        x = 0.72 + index * 4.15
        ui.add_rect(slide, x, 1.58, 3.72, 2.72, color=bg, outline=None)
        ui.add_text(
            slide,
            value,
            x + 0.25,
            1.98,
            3.22,
            0.88,
            size=34,
            color=ui.readable_accent(accent),
            bold=True,
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
            font=ui.FONT_HEAD,
        )
        ui.add_text(
            slide,
            label,
            x + 0.30,
            3.05,
            3.12,
            0.75,
            size=11.5,
            color=ui.DARK,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
    ui.add_rect(slide, 0.90, 4.85, 11.50, 1.28, color=ui.WHITE, outline=ui.LIGHT)
    ui.add_panel_title(slide, "Interpretation", 1.20, 5.10, 10.80, accent=ui.PURPLE)
    ui.add_text(
        slide,
        "The SEA-AD driver set has limited gene overlap with ROSMAP and no matched cell-type context. Cohort and network topology changed together.",
        1.22,
        5.58,
        10.80,
        0.42,
        size=11.4,
        color=ui.DARK,
    )
    set_notes(
        slide,
        "Quantify context preservation across all six shared-gene pairings.",
        "No pairing shares broad cell type, one shares sex/APOE group, and no pairing shares both. The one same-group pairing is MIPOL1 in M_e33.",
        "These are descriptive proportions, not formal replication probabilities.",
        "Show the ROSMAP sex distribution of the shared genes.",
    )

    # Slide 23: sex membership.
    slide = slides[22]
    clear_slide(slide)
    ui.add_title_block(
        slide,
        "Shared SEA-AD M_e33 genes span both ROSMAP sexes",
        "All three shared genes are M_e33 in SEA-AD; ROSMAP sex membership is mixed.",
    )
    ui.add_rect(slide, 0.66, 1.55, 5.95, 4.55, color=ui.PALE_SKY, outline=None)
    ui.add_panel_title(slide, "Gene membership", 0.96, 1.87, 5.20, accent=ui.BLUE)
    rows = [
        ("Male-only (0)", "None"),
        ("Female-only (1)", "PAPOLA"),
        ("Both sexes (2)", "LAGE3, MIPOL1"),
    ]
    for index, (label, genes) in enumerate(rows):
        y = 2.52 + index * 1.02
        ui.add_text(slide, label, 0.98, y, 1.72, 0.30, size=10.3, color=ui.GRAY, bold=True)
        ui.add_text(slide, genes, 2.78, y, 3.25, 0.55, size=12.0, color=ui.DARK)
    ui.add_rect(slide, 6.90, 1.55, 5.78, 4.55, color=ui.PALE_GRAY, outline=None)
    ui.add_panel_title(slide, "ROSMAP sex distribution", 7.20, 1.87, 5.00, accent=ui.GRAY)
    bar_rows = [
        ("Male-only", 0, ui.BLUE),
        ("Female-only", 1, ui.VERMILION),
        ("Both sexes", 2, ui.GRAY),
    ]
    for index, (label, value, color) in enumerate(bar_rows):
        y = 2.60 + index * 0.90
        ui.add_text(slide, label, 7.22, y, 2.60, 0.28, size=10.5, color=ui.DARK)
        if value:
            ui.add_rect(
                slide,
                7.22,
                y + 0.32,
                3.90 * value / 2,
                0.24,
                color=color,
                outline=None,
                radius=False,
            )
        ui.add_text(slide, str(value), 11.35, y + 0.28, 0.95, 0.28, size=11, color=ui.DARK, bold=True)
    ui.add_text(
        slide,
        "MIPOL1 and LAGE3 occur in both female and male ROSMAP categories; PAPOLA occurs only in F_e4.",
        7.22,
        5.35,
        5.20,
        0.62,
        size=11.0,
        color=ui.GRAY,
    )
    set_notes(
        slide,
        "Show the ROSMAP sex membership of the three shared SEA-AD M_e33 genes.",
        "PAPOLA is female-only in ROSMAP. LAGE3 and MIPOL1 appear in both ROSMAP sexes. None is male-only.",
        "Observed sex membership is not a sex-interaction test and reflects unequal returned-only opportunities.",
        "Close with supported findings and limits.",
    )

    # Slide 24: conclusion.
    slide = slides[23]
    clear_slide(slide)
    ui.add_title_block(slide, "What the cross-cohort comparison does—and does not—show")
    ui.add_rect(slide, 0.66, 1.30, 5.95, 5.05, color=ui.PALE_GREEN, outline=None)
    ui.add_panel_title(slide, "Supported", 0.97, 1.62, 5.20, accent=ui.TEAL)
    ui.add_bullets(
        slide,
        [
            "3 of 43 SEA-AD drivers also occur in ROSMAP: LAGE3, MIPOL1, PAPOLA.",
            "No shared driver preserves both sex/APOE group and broad-cell type.",
            "MIPOL1 preserves M_e33 once but switches excitatory → inhibitory.",
            "PJVK is the only SEA-AD gene recurring across two categories.",
        ],
        0.99,
        2.16,
        5.28,
        size=11.2,
        accent=ui.TEAL,
        line_h=0.79,
    )
    ui.add_rect(slide, 6.90, 1.30, 5.78, 5.05, color=ui.PALE_RED, outline=None)
    ui.add_panel_title(slide, "Limits", 7.21, 1.62, 5.05, accent=ui.VERMILION)
    ui.add_bullets(
        slide,
        [
            "No broad-cell match occurs among the six shared-gene unit pairings.",
            "Only M_e33 is well represented among SEA-AD active calls (20 of 22).",
            "Cohort and network topology changed together; their effects are inseparable.",
            "Returned-only ACAT scores are exploratory and not final-FDR controlled.",
        ],
        7.23,
        2.16,
        5.10,
        size=11.2,
        accent=ui.VERMILION,
        line_h=0.79,
    )
    ui.add_text(
        slide,
        "Takeaway: three genes are shared, but there are zero exact sex/APOE × broad-cell validation matches.",
        0.88,
        6.65,
        11.60,
        0.30,
        size=11.1,
        color=ui.PURPLE,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    set_notes(
        slide,
        "State the cross-cohort conclusion without overclaiming validation.",
        "The comparison finds three shared genes and no exact category match. MIPOL1 retains M_e33 but changes cell type; PJVK is the only within-SEA-AD recurrent gene across categories.",
        "The comparison is descriptive, post-selected, unbalanced across strata, and confounds cohort with network topology.",
        "Continue to the sensitivity-analysis section.",
    )


def update_sensitivity_terminology(prs: Presentation) -> None:
    """Remove direction-combination terminology from the sensitivity section."""
    set_text(prs.slides[24], "TextBox 1", "PART 3")
    next(
        shape for shape in prs.slides[24].shapes if shape.name == "TextBox 1"
    ).height = 216982
    set_text(
        prs.slides[27],
        "TextBox 157",
        "One query is used per contrast, so query-passing contrasts and KDA runs are identical here.",
    )


def validate_deck(prs: Presentation, later_before: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, observed: Any, expected: Any, passed: bool) -> None:
        checks.append(
            {
                "check_id": check_id,
                "observed": observed,
                "expected": expected,
                "passed": bool(passed),
            }
        )

    add("slide_count", len(prs.slides), 30, len(prs.slides) == 30)
    later_after = [semantic_slide_fingerprint(prs.slides[index]) for index in range(24, len(prs.slides))]
    unchanged_later_positions = [1, 2, 4, 5]
    add(
        "non_query_sensitivity_slides_semantically_unchanged",
        sum(later_before[index] == later_after[index] for index in unchanged_later_positions),
        len(unchanged_later_positions),
        all(later_before[index] == later_after[index] for index in unchanged_later_positions),
    )
    first_24 = [prs.slides[index] for index in range(24)]
    text_1_24 = "\n".join(
        shape.text
        for slide in first_24
        for shape in slide.shapes
        if getattr(shape, "has_text_frame", False)
    )
    add("old_648_removed", text_1_24.count("648"), 0, "648" not in text_1_24)
    add("old_1548_removed", text_1_24.count("1,548"), 0, "1,548" not in text_1_24)
    add(
        "old_directional_slot_heading_removed",
        text_1_24.count("planned directional slots"),
        0,
        "planned directional slots" not in text_1_24,
    )
    all_presentation_text = "\n".join(
        [
            shape.text
            for slide in prs.slides
            for shape in slide.shapes
            if getattr(shape, "has_text_frame", False)
        ]
        + [
            slide.notes_slide.notes_text_frame.text
            for slide in prs.slides
            if slide.notes_slide.notes_text_frame is not None
        ]
    )
    disallowed_design_terms = ["merged", "combo", "up/down", "AD-up", "AD-down"]
    observed_design_terms = [
        term for term in disallowed_design_terms if term.lower() in all_presentation_text.lower()
    ]
    add(
        "default_query_design_terms_omitted",
        ";".join(observed_design_terms),
        "none",
        not observed_design_terms,
    )
    add("three_shared_genes_present", "LAGE3  •  MIPOL1  •  PAPOLA" in text_1_24, True, "LAGE3  •  MIPOL1  •  PAPOLA" in text_1_24)
    add("zero_exact_match_present", "0 of 44" in text_1_24, True, "0 of 44" in text_1_24)
    add(
        "slides_have_notes",
        sum(
            bool(slide.notes_slide.notes_text_frame and slide.notes_slide.notes_text_frame.text.strip())
            for slide in first_24
        ),
        24,
        all(
            slide.notes_slide.notes_text_frame
            and slide.notes_slide.notes_text_frame.text.strip()
            for slide in first_24
        ),
    )
    return checks


def write_audit(
    audit_root: Path,
    checks: list[dict[str, Any]],
    facts: dict[str, Any],
    deck_path: Path,
    backup_path: Path,
    figures: dict[str, Path],
) -> None:
    audit_root.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(checks)
    frame.insert(0, "schema_version", "sex_apoe_combo_slide_update_checks_v1")
    frame.to_csv(
        audit_root / "combo_slide_update_checks.tsv",
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    if not frame["passed"].all():
        failed = frame.loc[~frame["passed"], "check_id"].tolist()
        raise RuntimeError("Deck checks failed: " + ", ".join(failed))

    summary = pd.DataFrame(
        [
            {
                "schema_version": "sex_apoe_combo_slide_update_summary_v1",
                "rosmap_planned_contrasts": facts["ros_planned"],
                "rosmap_kda_calls": facts["ros_calls"],
                "rosmap_non_mt_rows": facts["ros_non_mt_rows"],
                "rosmap_category_units": facts["ros_units"],
                "rosmap_unique_genes": facts["ros_genes"],
                "seaad_planned_contrasts": facts["sea_planned"],
                "seaad_kda_calls": facts["sea_calls"],
                "seaad_non_mt_rows": facts["sea_non_mt_rows"],
                "seaad_category_units": facts["sea_units"],
                "seaad_unique_genes": facts["sea_genes"],
                "shared_genes": ";".join(facts["shared_genes"]),
                "exact_category_matches": facts["exact_matches"],
            }
        ]
    )
    summary.to_csv(
        audit_root / "combo_slide_update_summary.tsv",
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    artifacts = [
        ("updated_deck", deck_path),
        ("input_deck_backup", backup_path),
        ("rosmap_combo_manifest", ROS_DIR / "combo_run_manifest.tsv"),
        ("rosmap_combo_categories", ROS_DIR / "combo_key_drivers_by_category.tsv"),
        ("seaad_combo_manifest", SEA_DIR / "10a_inputs/seaad_kda_run_manifest.tsv"),
        ("seaad_combo_categories", SEA_DIR / "simple_category_gene_aggregates.tsv"),
    ] + [(role, path) for role, path in figures.items()]
    pd.DataFrame(
        [
            {
                "schema_version": "sex_apoe_combo_slide_update_artifacts_v1",
                "role": role,
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for role, path in artifacts
        ]
    ).to_csv(
        audit_root / "combo_slide_update_artifacts.tsv",
        sep="\t",
        index=False,
        lineterminator="\n",
    )


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_root = args.audit_root.resolve()
    if not args.figures_only and not input_path.is_file():
        raise FileNotFoundError(input_path)

    facts = prepare_facts()
    figures = render_figures(facts, audit_root / "figures")
    if args.figures_only:
        artifact_rows = []
        for role, png_path in sorted(figures.items()):
            base = png_path.with_suffix("")
            paths = [
                png_path,
                base.with_suffix(".svg"),
                base.with_suffix(".pdf"),
                base.with_name(base.name + "_plot_data.tsv"),
            ]
            for path in paths:
                if not path.is_file() or path.stat().st_size == 0:
                    raise RuntimeError(f"Missing or empty figure artifact: {path}")
                artifact_rows.append(
                    {
                        "role": role,
                        "path": str(
                            path.relative_to(ROOT)
                            if path.is_relative_to(ROOT)
                            else path
                        ),
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
        audit_root.mkdir(parents=True, exist_ok=True)
        artifacts_path = audit_root / "combo_figure_artifacts.tsv"
        pd.DataFrame(artifact_rows).to_csv(
            artifacts_path,
            sep="\t",
            index=False,
            lineterminator="\n",
        )
        status = pd.DataFrame(
            [
                {
                    "execution_status": "complete",
                    "rosmap_non_mt_category_units": len(facts["ros_categories"]),
                    "rosmap_non_mt_genes": facts["ros_genes"],
                    "rosmap_top5_entries": facts["ros_top5_count"],
                    "seaad_non_mt_category_units": len(facts["sea_categories"]),
                    "seaad_non_mt_genes": facts["sea_genes"],
                    "seaad_top5_entries": facts["sea_top5_count"],
                    "figure_roles": len(figures),
                    "artifact_files": len(artifact_rows),
                    "artifact_manifest_sha256": sha256_file(artifacts_path),
                }
            ]
        )
        status.to_csv(
            audit_root / "combo_figure_status.tsv",
            sep="\t",
            index=False,
            lineterminator="\n",
        )
        print(
            f"Rendered {len(figures)} validated combo figure roles "
            f"({len(artifact_rows)} files)"
        )
        return 0

    input_hash = sha256_file(input_path)
    backup_dir = audit_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"input_deck_{input_hash[:12]}.pptx"
    if not backup_path.exists():
        shutil.copy2(input_path, backup_path)

    prs = Presentation(input_path)
    if len(prs.slides) != 30:
        raise RuntimeError(f"Expected 30 slides, found {len(prs.slides)}")
    later_before = [semantic_slide_fingerprint(prs.slides[index]) for index in range(24, 30)]

    update_slides_1_to_18(prs, facts, figures)
    rebuild_slides_19_to_24(prs)
    update_sensitivity_terminology(prs)
    checks = validate_deck(prs, later_before)
    reordered_titles = reorder_slide_block(prs, [9, 8, 7])
    expected_rosmap_order = [
        "ROSMAP KDA summary: 381 non-MT gene x category combinations represent 228 distinct genes",
        "RPS15 recurs across 11 returned-only categories",
        "Top five: 123 non-MT entries across 29 categories",
    ]
    checks.append(
        {
            "check_id": "rosmap_slides_reordered_summary_recurrence_top5",
            "observed": " | ".join(reordered_titles),
            "expected": " | ".join(expected_rosmap_order),
            "passed": reordered_titles == expected_rosmap_order,
        }
    )
    reordered_titles = reorder_slide_block(prs, [14, 13, 12])
    expected_seaad_order = [
        "SEA-AD KDA summary: 44 non-MT gene x category combinations represent 43 distinct genes",
        "PJVK is the only gene recurring across 2 SEA-AD categories",
        "Top-five display: 17 non-MT entries across 5 categories",
    ]
    checks.append(
        {
            "check_id": "seaad_slides_reordered_summary_recurrence_top5",
            "observed": " | ".join(reordered_titles),
            "expected": " | ".join(expected_seaad_order),
            "passed": reordered_titles == expected_seaad_order,
        }
    )
    ros_excitatory = facts["ros_categories"].loc[
        facts["ros_categories"]["broad_network"].eq("Excitatory_neurons")
    ]
    insert_broad_cell_recurrence_slide(
        prs,
        figures["ros_excitatory_recurrence"],
        broad_cell_adjective="excitatory-neuron",
        unique_gene_count=int(ros_excitatory["current_symbol"].nunique()),
        category_unit_count=len(ros_excitatory),
        transition="Compare this pattern with inhibitory neurons.",
    )
    ros_inhibitory = facts["ros_categories"].loc[
        facts["ros_categories"]["broad_network"].eq("Inhibitory_neurons")
    ]
    insert_broad_cell_recurrence_slide(
        prs,
        figures["ros_inhibitory_recurrence"],
        broad_cell_adjective="inhibitory-neuron",
        unique_gene_count=int(ros_inhibitory["current_symbol"].nunique()),
        category_unit_count=len(ros_inhibitory),
        transition="Compare this pattern with astrocytes.",
        insert_index=11,
    )
    ros_astrocytes = facts["ros_categories"].loc[
        facts["ros_categories"]["broad_network"].eq("Astrocytes")
    ]
    insert_broad_cell_recurrence_slide(
        prs,
        figures["ros_astrocyte_recurrence"],
        broad_cell_adjective="astrocyte",
        unique_gene_count=int(ros_astrocytes["current_symbol"].nunique()),
        category_unit_count=len(ros_astrocytes),
        transition="Compare this pattern with OPCs.",
        insert_index=12,
    )
    ros_opcs = facts["ros_categories"].loc[
        facts["ros_categories"]["broad_network"].eq("OPCs")
    ]
    insert_broad_cell_recurrence_slide(
        prs,
        figures["ros_opc_recurrence"],
        broad_cell_adjective="OPC",
        unique_gene_count=int(ros_opcs["current_symbol"].nunique()),
        category_unit_count=len(ros_opcs),
        transition="Move to the SEA-AD KDA analysis.",
        insert_index=13,
    )
    sea_excitatory = facts["sea_categories"].loc[
        facts["sea_categories"]["broad_network"].eq("Excitatory_neurons")
    ]
    insert_broad_cell_recurrence_slide(
        prs,
        figures["sea_excitatory_recurrence"],
        cohort="SEA-AD",
        broad_cell_adjective="excitatory-neuron",
        unique_gene_count=int(sea_excitatory["current_symbol"].nunique()),
        category_unit_count=len(sea_excitatory),
        title="SEA-AD excitatory-neuron drivers occur in two sex/APOE groups",
        subtitle="27 unique non-MT genes across 27 gene × category combinations; no gene recurs across sex/APOE categories.",
        transition="Move to the sensitivity analyses.",
        insert_index=19,
    )
    excitatory_slide_text = "\n".join(
        shape.text
        for shape in prs.slides[10].shapes
        if getattr(shape, "has_text_frame", False)
    )
    inhibitory_slide_text = "\n".join(
        shape.text
        for shape in prs.slides[11].shapes
        if getattr(shape, "has_text_frame", False)
    )
    astrocyte_slide_text = "\n".join(
        shape.text
        for shape in prs.slides[12].shapes
        if getattr(shape, "has_text_frame", False)
    )
    opc_slide_text = "\n".join(
        shape.text
        for shape in prs.slides[13].shapes
        if getattr(shape, "has_text_frame", False)
    )
    sea_excitatory_slide_text = "\n".join(
        shape.text
        for shape in prs.slides[19].shapes
        if getattr(shape, "has_text_frame", False)
    )
    checks.append(
        {
            "check_id": "rosmap_excitatory_recurrence_inserted_after_top5",
            "observed": "ROSMAP excitatory-neuron drivers recur"
            in excitatory_slide_text,
            "expected": True,
            "passed": "ROSMAP excitatory-neuron drivers recur"
            in excitatory_slide_text,
        }
    )
    checks.append(
        {
            "check_id": "rosmap_inhibitory_recurrence_inserted_after_excitatory",
            "observed": "ROSMAP inhibitory-neuron drivers recur"
            in inhibitory_slide_text,
            "expected": True,
            "passed": "ROSMAP inhibitory-neuron drivers recur"
            in inhibitory_slide_text,
        }
    )
    checks.append(
        {
            "check_id": "rosmap_astrocyte_recurrence_inserted_after_inhibitory",
            "observed": "ROSMAP astrocyte drivers recur"
            in astrocyte_slide_text,
            "expected": True,
            "passed": "ROSMAP astrocyte drivers recur"
            in astrocyte_slide_text,
        }
    )
    checks.append(
        {
            "check_id": "rosmap_opc_recurrence_inserted_after_astrocyte",
            "observed": "ROSMAP OPC drivers recur" in opc_slide_text,
            "expected": True,
            "passed": "ROSMAP OPC drivers recur" in opc_slide_text,
        }
    )
    checks.append(
        {
            "check_id": "seaad_excitatory_recurrence_inserted_after_top5",
            "observed": "SEA-AD excitatory-neuron drivers occur"
            in sea_excitatory_slide_text,
            "expected": True,
            "passed": "SEA-AD excitatory-neuron drivers occur"
            in sea_excitatory_slide_text,
        }
    )
    checks.append(
        {
            "check_id": "slide_count_before_cross_cohort_removal",
            "observed": len(prs.slides),
            "expected": 35,
            "passed": len(prs.slides) == 35,
        }
    )
    removed_titles = remove_slide_range(prs, 20, 29)
    checks.append(
        {
            "check_id": "cross_cohort_slides_16_to_24_removed",
            "observed": len(removed_titles),
            "expected": 9,
            "passed": len(removed_titles) == 9,
        }
    )
    checks.append(
        {
            "check_id": "output_slide_count_after_removal",
            "observed": len(prs.slides),
            "expected": 26,
            "passed": len(prs.slides) == 26,
        }
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=output_path.stem + ".", suffix=".pptx", dir=output_path.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        prs.save(temp_path)
        reopened = Presentation(temp_path)
        if len(reopened.slides) != 26:
            raise RuntimeError("Saved deck failed reopen/slide-count validation")
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    write_audit(audit_root, checks, facts, output_path, backup_path, figures)
    print(f"Updated deck: {output_path}")
    print(f"Backup: {backup_path}")
    print(f"Audit: {audit_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
