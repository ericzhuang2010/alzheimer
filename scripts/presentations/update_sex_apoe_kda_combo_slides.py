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
from matplotlib.colors import Normalize  # noqa: E402
from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Inches  # noqa: E402


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
NETWORK_LABELS = {
    "Astrocytes": "Astrocytes",
    "Excitatory_neurons": "Excitatory neurons",
    "Inhibitory_neurons": "Inhibitory neurons",
    "Microglia": "Microglia",
    "OPCs": "OPCs",
    "Oligodendrocytes": "Oligodendrocytes",
    "Vasculature_cells": "Vasculature",
}

BLUE = "#56B4E9"
ORANGE = "#E69F00"
TEXT = "#222222"
MUTED = "#4B5563"
GRID = "#D1D5DB"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-root", type=Path, default=AUDIT_ROOT)
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


def replace_picture(slide, old_shape_name: str, image_path: Path, alt: str) -> None:
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


def plot_recurrence(rows: pd.DataFrame, cohort: str) -> plt.Figure:
    ordered = rows.iloc[::-1].reset_index(drop=True)
    maximum = max(1, int(ordered["acat_category_count"].max()))
    norm = Normalize(vmin=0, vmax=maximum)
    cmap = matplotlib.colormaps["cividis"]
    colors = [cmap(norm(value)) for value in ordered["acat_category_count"]]
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
    scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = figure.colorbar(scalar, ax=axis, pad=0.02)
    colorbar.set_label("Categories aggregated across ≥2 returned calls")
    figure.subplots_adjust(left=0.20, right=0.88, top=0.84, bottom=0.11)
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
        export_figure(plot_top5(top5, cohort), top5_base)
        export_figure(plot_recurrence(recurrence, cohort), recurrence_base)
        top5.to_csv(
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
    return paths


def update_slides_1_to_18(prs: Presentation, facts: dict[str, Any], figures: dict[str, Path]) -> None:
    slides = prs.slides

    # Slide 1
    set_text(slides[0], "TextBox 2", "ROSMAP and SEA-AD sex/APOE key-driver analysis")
    set_text(
        slides[0],
        "TextBox 3",
        "Mitochondrial DEG queries with returned-only simple aggregation",
    )
    set_text(slides[0], "TextBox 6", "ROSMAP KDA")
    set_text(
        slides[0],
        "TextBox 7",
        "194 KDA calls → returned-only non-MT aggregation → 381 category units",
    )
    set_text(
        slides[0],
        "TextBox 11",
        "22 SEA-AD-network KDA calls → returned-only non-MT aggregation → 44 category units",
    )
    set_notes(
        slides[0],
        "Introduce the analysis in both cohorts.",
        "Part I summarizes 194 ROSMAP KDA calls and 381 non-MT gene-by-category units. Part II summarizes 22 SEA-AD calls against SEA-AD-specific networks and 44 units.",
        "Each contrast contributes at most one mitochondrial DEG query and one KDA call.",
        "Compare the cohort and run structures before reviewing each branch.",
    )

    # Slide 2
    set_text(slides[1], "TextBox 2", "Two cohorts, one aggregation rule")
    set_text(
        slides[1],
        "TextBox 3",
        "Each contrast contributes at most one mitochondrial DEG query; significant non-MT returns are aggregated by category.",
    )
    set_text(slides[1], "TextBox 8", "324")
    set_text(slides[1], "TextBox 9", "planned contrasts")
    set_text(slides[1], "TextBox 11", "194")
    set_text(slides[1], "TextBox 12", "included KDA calls")
    set_text(slides[1], "TextBox 14", "381")
    set_text(slides[1], "TextBox 15", "gene × category units")
    set_text(
        slides[1],
        "TextBox 17",
        "Builds one core-MT DEG query within each fine-cell contrast.",
    )
    set_text(
        slides[1],
        "TextBox 19",
        "Groups returned drivers within sex/APOE × broad network.",
    )
    set_text(
        slides[1],
        "TextBox 21",
        "Final 381 units represent 228 genes in 29 categories.",
    )
    set_text(slides[1], "TextBox 26", "774")
    set_text(slides[1], "TextBox 27", "planned contrasts")
    set_text(slides[1], "TextBox 29", "22")
    set_text(slides[1], "TextBox 30", "active KDA calls")
    set_text(slides[1], "TextBox 32", "44")
    set_text(slides[1], "TextBox 33", "gene × category units")
    set_text(
        slides[1], "TextBox 35", "Uses SEA-AD-specific Bayesian networks."
    )
    set_text(
        slides[1],
        "TextBox 37",
        "Donor ≥3 per arm; FDR-only query; mapped n ≥3.",
    )
    set_text(
        slides[1],
        "TextBox 39",
        "20 of 22 calls are M_e33; five categories have returns.",
    )
    category_band = ui.add_rect(
        slides[1],
        0.90,
        6.15,
        11.50,
        0.72,
        color=ui.PALE_GOLD,
        outline=ui.GOLD,
    )
    # Preserve the manual slide-2 placement from the reviewed deck.  Raw EMUs
    # avoid rounding away PowerPoint's fractional-inch coordinates.
    category_band.left = 838200
    category_band.top = 5754624
    category_text = ui.add_text(
        slides[1],
        "Category = one sex/APOE group × one broad cell type (for example, M_e33 × excitatory neurons). Returned drivers from eligible fine-cell or supertype KDA calls are combined within that category.",
        1.14,
        6.31,
        11.02,
        0.40,
        size=10.6,
        color=ui.GOLD_TEXT,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )
    category_text.left = 1042415
    category_text.top = 5905331
    set_notes(
        slides[1],
        "Give a side-by-side map of the two analyses.",
        "Define a category before using the counts: one sex/APOE group crossed with one broad cell type, such as M_e33 excitatory neurons. Returned drivers from eligible fine-cell or supertype KDA calls are aggregated within that category. ROSMAP contributes 194 calls and 381 gene-by-category units; SEA-AD contributes 22 active calls and 44 units.",
        "Twenty of 22 SEA-AD calls are M_e33. Categories without calls are unavailable, not negative tests.",
        "Review the ROSMAP branch first.",
    )

    # Slide 3
    set_text(slides[2], "TextBox 3", "ROSMAP KDA reaggregation")
    set_text(
        slides[2],
        "TextBox 4",
        "54 fine cell types define 324 contrasts; 194 calls from 43 fine types are aggregated within six groups and seven broad networks.",
    )
    set_notes(
        slides[2],
        "Introduce the ROSMAP fine-cell KDA branch.",
        "The section defines the one-query-per-contrast design, the eligibility funnel, query construction, and returned-only simple aggregation.",
        "The analysis uses existing validated KDA results and does not pool sex/APOE groups.",
        "Start with the four counting units.",
    )

    # Slide 4
    set_text(slides[3], "TextBox 2", "Four steps: one KDA query per contrast")
    set_text(slides[3], "TextBox 14", "Mitochondrial query")
    set_text(slides[3], "TextBox 15", "core-MT DEGs")
    set_text(slides[3], "TextBox 17", "One query per contrast")
    set_text(slides[3], "TextBox 28", "Category result")
    set_text(slides[3], "TextBox 29", "gene × category")
    set_text(
        slides[3],
        "TextBox 31",
        "Category = sex/APOE group × broad network",
    )
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
    set_text(slides[4], "TextBox 8", "324 signed results")
    set_text(slides[4], "TextBox 9", "one query per contrast")
    set_text(slides[4], "TextBox 11", "194 call_key_drivers calls")
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
    replace_picture(
        slides[7],
        "Simple returned-only Phase 20 female and male panels showing up to five non-MT genes per sex/APOE by broad-cell category",
        figures["ros_top5"],
        "ROSMAP top-five non-MT key drivers by sex/APOE and broad-cell category",
    )
    set_notes(
        slides[7],
        "Present the ROSMAP top-five results.",
        "The figure displays up to five non-MT drivers in each of 29 populated categories, for 123 displayed entries. Blue hatching denotes ACAT across at least two returned calls; orange denotes one-call q passthrough.",
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
    set_text(
        slides[8],
        "TextBox 14",
        "RPS15: 11 categories, 6 groups, 4 networks; ACAT in 4.",
    )
    set_text(
        slides[8],
        "TextBox 16",
        "RPL11: 10 categories, 6 groups, 4 networks; ACAT in 3.",
    )
    set_notes(
        slides[8],
        "Interpret category recurrence.",
        "RPS15 occurs in 11 categories from 22 returned calls. RPL11 occurs in 10 categories from 24 calls. Color encodes how many category scores combine at least two returned calls.",
        "Category presence is descriptive and not independent replication.",
        "Summarize the full ROSMAP output scale.",
    )

    set_text(slides[9], "TextBox 2", "Simple output: 381 non-MT category units represent 228 genes")
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
    set_text(slides[10], "TextBox 3", "SEA-AD network-specific KDA")
    set_text(
        slides[10],
        "TextBox 4",
        "129 supertypes define 774 contrasts; 22 KDA calls were run against SEA-AD-specific Bayesian networks.",
    )
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
    set_text(slides[11], "TextBox 7", "774 signed results")
    set_text(slides[11], "TextBox 8", "one query per contrast")
    set_text(slides[11], "TextBox 10", "22 KDA calls")
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
    set_notes(
        slides[11],
        "Show how 774 SEA-AD contrasts reduce to 22 executable calls.",
        "There are 393 non-estimable source contrasts, 348 estimable contrasts with an empty FDR-only query, 11 with one or two mapped genes, and 22 meeting the three-gene floor.",
        "A skipped contrast is unavailable and is not a negative validation result.",
        "Inspect the returned non-MT candidates.",
    )

    set_text(slides[12], "TextBox 1", "Top-five display: 17 non-MT entries across 5 categories")
    replace_picture(
        slides[12],
        "VH12 SEA-AD-network top-five non-mitochondrial key drivers by sex/APOE and broad-cell category",
        figures["sea_top5"],
        "SEA-AD top-five non-MT key drivers by sex/APOE and broad-cell category",
    )
    set_notes(
        slides[12],
        "Present leading SEA-AD non-MT candidates.",
        "Seventeen entries appear across F_e33 excitatory, F_e4 astrocyte, and three M_e33 categories. Blue hatching denotes ACAT across at least two calls; orange is one-call q passthrough.",
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
    set_text(slides[13], "TextBox 13", "PJVK: M_e33 excitatory + inhibitory neurons.")
    set_text(
        slides[13],
        "TextBox 15",
        "Its inhibitory category combines 3 returned calls by ACAT.",
    )
    set_text(
        slides[13],
        "TextBox 17",
        "The remaining 19 displayed genes occur in one category.",
    )
    set_notes(
        slides[13],
        "Interpret SEA-AD category recurrence.",
        "PJVK is the only gene present in two categories: M_e33 excitatory and inhibitory neurons. Every other gene on the top-20 display occurs in one category.",
        "Five return-bearing categories impose a low recurrence ceiling.",
        "Summarize the SEA-AD output scale.",
    )

    set_text(slides[14], "TextBox 1", "SEA-AD output: 44 non-MT units represent 43 genes")
    for name, value in {
        "TextBox 3": "54",
        "TextBox 6": "44",
        "TextBox 9": "43",
        "TextBox 12": "5",
        "TextBox 15": "17",
    }.items():
        set_text(slides[14], name, value)
    set_text(slides[14], "TextBox 19", "Where the 44 units occur")
    set_text(
        slides[14], "TextBox 21", "M_e33 39 • F_e4 3 • F_e33 2 • other groups 0"
    )
    set_text(
        slides[14],
        "TextBox 23",
        "Excitatory 27 • Inhibitory 12 • Astrocytes 3 • Oligo 2\nMicroglia, OPCs, Vasculature 0",
    )
    set_text(slides[14], "TextBox 28", "20 calls with returns; 2 completed empty.")
    set_text(
        slides[14],
        "TextBox 30",
        "112 significant return rows before mitochondrial filtering.",
    )
    set_text(slides[14], "TextBox 32", "58 core-MitoCarta rows excluded.")
    set_text(slides[14], "TextBox 34", "54 non-MT rows retained for aggregation.")
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
    unchanged_later_positions = [0, 1, 2, 4, 5]
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
    slide_2_text = "\n".join(
        shape.text
        for shape in prs.slides[1].shapes
        if getattr(shape, "has_text_frame", False)
    )
    category_definition = "Category = one sex/APOE group × one broad cell type"
    add(
        "category_defined_on_slide_2",
        category_definition in slide_2_text,
        True,
        category_definition in slide_2_text,
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
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    facts = prepare_facts()
    figures = render_figures(facts, audit_root / "figures")

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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=output_path.stem + ".", suffix=".pptx", dir=output_path.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        prs.save(temp_path)
        reopened = Presentation(temp_path)
        if len(reopened.slides) != 30:
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
