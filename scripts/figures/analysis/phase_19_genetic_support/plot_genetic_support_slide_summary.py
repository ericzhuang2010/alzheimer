#!/usr/bin/env python3
"""Render the standalone human-genetic-support slide summary figure."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / "tmp" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandas as pd


SCHEMA = "genetic_support_slide_summary_v1"
INPUT_SCHEMA = "human_genetic_support_tier1_v1"
FIGURE_SIZE = (12.4, 4.7)
PNG_DPI = 450
OUTPUT_FILES = [
    "genetic_support_slide_summary.png",
    "genetic_support_slide_summary.pdf",
    "genetic_support_slide_summary.svg",
    "genetic_support_slide_summary_plot_data.tsv",
    "genetic_support_slide_summary_checks.tsv",
    "genetic_support_slide_summary_caption.md",
    "genetic_support_slide_summary_methods.md",
    "genetic_support_slide_summary_artifacts.tsv",
    "genetic_support_slide_summary_status.tsv",
]
REQUIRED_INPUTS = [
    "genetic_support_candidate_manifest.tsv",
    "genetic_support_common_variant_evidence.tsv.gz",
    "genetic_support_colocalization.tsv.gz",
    "genetic_support_assessability.tsv",
    "genetic_support_evidence_summary.tsv",
    "genetic_support_checks.tsv",
    "genetic_support_status.tsv",
]
GRADE_ORDER = ["strong", "moderate", "weak", "none_found", "not_assessable"]
EXPECTED_GRADE_COUNTS = {
    "strong": 1,
    "moderate": 0,
    "weak": 3,
    "none_found": 23,
    "not_assessable": 20,
}
EXPECTED_NO_DIRECT = {
    "ANKRD11", "ATP6V1F", "COX4I1", "COX6B1", "DYNLT1", "FTL", "LAMTOR5",
    "LAPTM4A", "NCOA1", "RPL11", "RPL15", "RPL38", "RPLP1", "RPS13",
    "RPS15", "UQCR10",
}
EXPECTED_MTDNA = {"MT-ATP6", "MT-CO2", "MT-CO3", "MT-CYB", "MT-ND4", "MT-ND5"}

NAVY = "#17365D"
DARK = "#333333"
MID = "#5B6573"
LIGHT = "#D7DEE8"
PALE = "#F7F9FC"
BLUE = "#0072B2"
PALE_BLUE = "#E9F3F8"
GREEN = "#009E73"
ORANGE = "#E69F00"
PALE_ORANGE = "#FFF4DD"
GRAY = "#BDBDBD"
PALE_GRAY = "#F1F1F1"
WHITE = "#FFFFFF"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-root",
        default="results/minerva_production/19_genetic_support_tier1",
    )
    parser.add_argument(
        "--output-root",
        default="results/figures/analysis/phase_19_genetic_support",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: Any) -> bool:
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES"}


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="NA", lineterminator="\n")


def pretty_context(value: str) -> str:
    return value.replace("_", " ")


def format_contexts(values: list[str]) -> str:
    pretty = [pretty_context(value) for value in values]
    if len(pretty) == 1:
        return pretty[0]
    if len(pretty) == 2:
        return f"{pretty[0]} + {pretty[1].lower()}"
    return ", ".join(pretty)


def format_scientific(value: float, digits: int = 2) -> str:
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return rf"${mantissa} \times 10^{{{int(exponent)}}}$"


def validate_inputs(input_root: Path) -> dict[str, pd.DataFrame]:
    missing = [name for name in REQUIRED_INPUTS if not (input_root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing figure inputs: " + ", ".join(missing))
    frames = {
        "candidate": pd.read_csv(input_root / REQUIRED_INPUTS[0], sep="\t", low_memory=False),
        "common": pd.read_csv(input_root / REQUIRED_INPUTS[1], sep="\t", low_memory=False),
        "coloc": pd.read_csv(input_root / REQUIRED_INPUTS[2], sep="\t", low_memory=False),
        "assessability": pd.read_csv(input_root / REQUIRED_INPUTS[3], sep="\t", low_memory=False),
        "summary": pd.read_csv(input_root / REQUIRED_INPUTS[4], sep="\t", low_memory=False),
        "source_checks": pd.read_csv(input_root / REQUIRED_INPUTS[5], sep="\t", low_memory=False),
        "source_status": pd.read_csv(input_root / REQUIRED_INPUTS[6], sep="\t", low_memory=False),
    }
    for name, frame in frames.items():
        if "schema_version" not in frame.columns:
            raise ValueError(f"{name} lacks schema_version")
        if set(frame["schema_version"].dropna()) != {INPUT_SCHEMA}:
            raise ValueError(f"Unexpected input schema in {name}")
    summary = frames["summary"]
    if len(summary) != 47 or summary["candidate_id"].nunique() != 47:
        raise ValueError("Expected 47 unique candidate-context rows")
    if summary["gene"].nunique() != 25:
        raise ValueError("Expected 25 unique genes")
    if set(summary["final_grade"]) - set(GRADE_ORDER):
        raise ValueError("Unexpected evidence grade")
    observed = summary["final_grade"].value_counts().to_dict()
    for grade, expected in EXPECTED_GRADE_COUNTS.items():
        if int(observed.get(grade, 0)) != expected:
            raise ValueError(f"Grade count mismatch for {grade}")
    status = frames["source_status"]
    if len(status) != 1 or status.loc[0, "technical_status"] != "validated_complete_tier1":
        raise ValueError("Source bundle is not validated_complete_tier1")
    blocking = frames["source_checks"].loc[frames["source_checks"]["severity"].eq("blocking")]
    if not blocking["status"].eq("pass").all():
        raise ValueError("At least one source blocking check did not pass")
    return frames


def get_direct_row(common: pd.DataFrame, gene: str, evidence_id: str) -> pd.Series:
    direct = common["direct_candidate_mapping"].map(truth)
    subset = common.loc[direct & common["gene"].eq(gene) & common["rsid"].eq(evidence_id)]
    if len(subset) != 1:
        raise ValueError(f"Expected one direct {gene}/{evidence_id} row, found {len(subset)}")
    return subset.iloc[0]


def derive_plot_data(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, Any]]:
    summary = frames["summary"].copy()
    common = frames["common"].copy()
    coloc = frames["coloc"].copy()
    outcome_labels = {
        "strong": "Strong",
        "moderate": "Moderate",
        "weak": "Weak / limited",
        "none_found": "No direct mapping",
        "not_assessable": "Not assessable",
    }
    style_keys = {
        "strong": "strong_blue",
        "moderate": "moderate_green",
        "weak": "weak_orange",
        "none_found": "no_direct_gray",
        "not_assessable": "not_assessable_open",
    }
    rows: list[dict[str, Any]] = []
    counts = summary["final_grade"].value_counts().to_dict()
    for order, grade in enumerate(GRADE_ORDER, 1):
        count = int(counts.get(grade, 0))
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "outcome_segment",
                "display_order": order,
                "gene": "NA",
                "contexts": "NA",
                "final_grade": grade,
                "context_count": count,
                "value": count,
                "share": count / len(summary),
                "primary_label": outcome_labels[grade],
                "secondary_label": f"{count} candidate-context units",
                "tertiary_label": "NA",
                "evidence_id": "NA",
                "style_key": style_keys[grade],
                "source_rows": "genetic_support_evidence_summary.tsv",
            }
        )

    apoe = get_direct_row(common, "APOE", "rs429358")
    cox7c = get_direct_row(common, "COX7C", "rs2010322")
    selenow = common.loc[
        common["gene"].eq("SELENOW") & common["evidence_route"].eq("twas_gene_list")
    ]
    if len(selenow) != 1:
        raise ValueError("Expected one SELENOW TWAS-list row")
    cox_coloc = coloc.loc[coloc["gene"].eq("COX7C") & coloc["rsid"].eq("rs2010322")]
    if len(cox_coloc) != 1:
        raise ValueError("Expected one COX7C colocalization-summary row")

    card_specs = []
    for gene in ["APOE", "COX7C", "SELENOW"]:
        gene_rows = summary.loc[summary["gene"].eq(gene)].sort_values("broad_network")
        contexts = format_contexts(gene_rows["broad_network"].tolist())
        grade = str(gene_rows["final_grade"].iloc[0])
        if gene == "APOE":
            detail = (
                f"{apoe['rsid']}  •  AD fine-map inclusion {float(apoe['ad_max_inclusion_score']):.1f}"
                f"  •  P ≈ {format_scientific(float(apoe['min_pvalue']))}"
            )
            limit = "Fallback brain evidence; not an exact astrocyte colocalization"
            evidence_id = str(apoe["rsid"])
        elif gene == "COX7C":
            confidence = str(cox_coloc.iloc[0]["public_confidence_level"])
            detail = (
                f"{cox7c['rsid']}  •  bulk sQTL {confidence}"
                f"  •  AD P ≈ {format_scientific(float(cox7c['min_pvalue']))}"
            )
            limit = "One source result shown in two network contexts; not two replications"
            evidence_id = str(cox7c["rsid"])
        else:
            detail = "Reported in the source TWAS gene list"
            limit = "Model statistic and exact excitatory context unavailable in the public table"
            evidence_id = "TWAS_gene_list"
        card_specs.append((gene, contexts, grade, len(gene_rows), detail, limit, evidence_id))

    for order, (gene, contexts, grade, context_count, detail, limit, evidence_id) in enumerate(card_specs, 1):
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "candidate_card",
                "display_order": order,
                "gene": gene,
                "contexts": contexts,
                "final_grade": grade,
                "context_count": context_count,
                "value": context_count,
                "share": context_count / len(summary),
                "primary_label": "STRONG GENE-LEVEL SUPPORT" if grade == "strong" else "WEAK / LIMITED",
                "secondary_label": detail,
                "tertiary_label": limit,
                "evidence_id": evidence_id,
                "style_key": "strong_blue" if grade == "strong" else "weak_orange",
                "source_rows": "genetic_support_evidence_summary.tsv|genetic_support_common_variant_evidence.tsv.gz|genetic_support_colocalization.tsv.gz",
            }
        )

    positive_genes = {"APOE", "COX7C", "SELENOW"}
    no_direct = set(summary.loc[summary["final_grade"].eq("none_found"), "gene"])
    not_assessable = set(summary.loc[summary["final_grade"].eq("not_assessable"), "gene"])
    if no_direct != EXPECTED_NO_DIRECT:
        raise ValueError("Unexpected no-direct-mapping gene set")
    if not_assessable != EXPECTED_MTDNA:
        raise ValueError("Unexpected not-assessable mtDNA gene set")
    for record_type, genes, grade, style_key in [
        ("no_direct_gene", sorted(no_direct), "none_found", "no_direct_gray"),
        ("not_assessable_gene", sorted(not_assessable), "not_assessable", "not_assessable_open"),
    ]:
        for order, gene in enumerate(genes, 1):
            gene_rows = summary.loc[summary["gene"].eq(gene)]
            rows.append(
                {
                    "schema_version": SCHEMA,
                    "record_type": record_type,
                    "display_order": order,
                    "gene": gene,
                    "contexts": format_contexts(sorted(gene_rows["broad_network"].tolist())),
                    "final_grade": grade,
                    "context_count": len(gene_rows),
                    "value": len(gene_rows),
                    "share": len(gene_rows) / len(summary),
                    "primary_label": gene,
                    "secondary_label": "NA",
                    "tertiary_label": "NA",
                    "evidence_id": "NA",
                    "style_key": style_key,
                    "source_rows": "genetic_support_evidence_summary.tsv",
                }
            )
    rows.append(
        {
            "schema_version": SCHEMA,
            "record_type": "boundary",
            "display_order": 1,
            "gene": "NA",
            "contexts": "NA",
            "final_grade": "NA",
            "context_count": 47,
            "value": 47,
            "share": 1.0,
            "primary_label": "No direct map ≠ no genetic role    •    Not assessable ≠ negative",
            "secondary_label": "Evidence categories summarize source coverage and direct mapping; they are not causal probabilities.",
            "tertiary_label": "NA",
            "evidence_id": "NA",
            "style_key": "boundary_navy",
            "source_rows": "genetic_support_evidence_summary.tsv|genetic_support_assessability.tsv",
        }
    )
    plot_data = pd.DataFrame(rows)
    visible_text = "\n".join(
        plot_data[["primary_label", "secondary_label", "tertiary_label", "gene", "contexts"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
    )
    if "phase 19" in visible_text.lower() or "phase19" in visible_text.lower():
        raise ValueError("Internal phase label leaked into visible plot data")
    context_gene_total = (
        int(summary.loc[summary["gene"].isin(positive_genes)].shape[0])
        + int(summary.loc[summary["gene"].isin(no_direct)].shape[0])
        + int(summary.loc[summary["gene"].isin(not_assessable)].shape[0])
    )
    if context_gene_total != 47:
        raise ValueError("Gene-category context counts do not sum to 47")
    derived = {
        "total_contexts": len(summary),
        "unique_genes": summary["gene"].nunique(),
        "grade_counts": {grade: int(counts.get(grade, 0)) for grade in GRADE_ORDER},
        "no_direct_genes": sorted(no_direct),
        "not_assessable_genes": sorted(not_assessable),
        "no_direct_contexts": int(summary["final_grade"].eq("none_found").sum()),
        "not_assessable_contexts": int(summary["final_grade"].eq("not_assessable").sum()),
        "visible_text": visible_text,
    }
    return plot_data, derived


def rounded_box(ax: plt.Axes, x: float, y: float, w: float, h: float, *,
                face: str = WHITE, edge: str = LIGHT, linewidth: float = 1.0,
                radius: float = 0.012, hatch: str | None = None, zorder: int = 1) -> None:
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.004,rounding_size={radius}",
        transform=ax.transAxes, facecolor=face, edgecolor=edge,
        linewidth=linewidth, hatch=hatch, zorder=zorder,
    )
    ax.add_patch(patch)


def text(ax: plt.Axes, x: float, y: float, value: str, *, size: float = 10,
         color: str = DARK, weight: str = "normal", ha: str = "left",
         va: str = "center", zorder: int = 5, linespacing: float = 1.1) -> None:
    ax.text(
        x, y, value, transform=ax.transAxes, fontsize=size, color=color,
        fontweight=weight, ha=ha, va=va, zorder=zorder, linespacing=linespacing,
        family="sans-serif",
    )


def panel_heading(ax: plt.Axes, letter: str, title: str, x: float, y: float) -> None:
    text(ax, x, y, letter, size=13, color=NAVY, weight="bold")
    text(ax, x + 0.024, y, title, size=12.2, color=NAVY, weight="bold")


def draw_outcome_panel(ax: plt.Axes, plot_data: pd.DataFrame, total: int) -> None:
    rounded_box(ax, 0.012, 0.735, 0.976, 0.252, face=WHITE, edge=LIGHT, linewidth=0.9)
    panel_heading(ax, "A", f"Candidate-context outcomes  (n = {total})", 0.028, 0.953)
    text(ax, 0.965, 0.953, "Moderate = 0", size=9.6, color=GREEN, weight="bold", ha="right")
    segments = plot_data.loc[
        plot_data["record_type"].eq("outcome_segment") & plot_data["value"].gt(0)
    ].sort_values("display_order")
    bar_x, bar_y, bar_w, bar_h = 0.048, 0.795, 0.904, 0.071
    colors = {
        "strong": BLUE,
        "weak": ORANGE,
        "none_found": GRAY,
        "not_assessable": WHITE,
    }
    offset = 0.0
    centers = {}
    for row in segments.itertuples(index=False):
        width = bar_w * float(row.value) / total
        hatch = "////" if row.final_grade == "not_assessable" else None
        rect = Rectangle(
            (bar_x + offset, bar_y), width, bar_h, transform=ax.transAxes,
            facecolor=colors[row.final_grade], edgecolor=DARK, linewidth=0.8,
            hatch=hatch, zorder=2,
        )
        ax.add_patch(rect)
        centers[row.final_grade] = bar_x + offset + width / 2
        if row.final_grade == "none_found":
            text(ax, centers[row.final_grade], bar_y + bar_h / 2,
                 f"No direct mapping  •  {int(row.value)}", size=10.2,
                 color=DARK, weight="bold", ha="center")
        elif row.final_grade == "not_assessable":
            text(ax, centers[row.final_grade], bar_y + bar_h / 2,
                 f"Not assessable  •  {int(row.value)}", size=10.2,
                 color=DARK, weight="bold", ha="center")
        offset += width
    for grade, label, label_x, color in [
        ("strong", "Strong  •  1", 0.064, BLUE),
        ("weak", "Weak / limited  •  3", 0.174, ORANGE),
    ]:
        center = centers[grade]
        ax.annotate(
            label, xy=(center, bar_y + bar_h), xycoords=ax.transAxes,
            xytext=(label_x, 0.886), textcoords=ax.transAxes,
            ha="center", va="center", fontsize=9.4, fontweight="bold", color=color,
            arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.8},
            zorder=6,
        )
    text(ax, 0.048, 0.763,
         "One unit = one displayed gene × broad-network context; repeated genes can contribute more than one unit.",
         size=9.0, color=MID)


def draw_candidate_cards(ax: plt.Axes, plot_data: pd.DataFrame) -> None:
    rounded_box(ax, 0.012, 0.147, 0.528, 0.572, face=WHITE, edge=LIGHT, linewidth=0.9)
    panel_heading(ax, "B", "Direct candidate-level findings", 0.028, 0.687)
    cards = plot_data.loc[plot_data["record_type"].eq("candidate_card")].sort_values("display_order")
    ys = [0.512, 0.345, 0.178]
    for row, y in zip(cards.itertuples(index=False), ys):
        strong = row.final_grade == "strong"
        edge = BLUE if strong else ORANGE
        face = PALE_BLUE if strong else PALE_ORANGE
        rounded_box(ax, 0.030, y, 0.492, 0.139, face=face, edge=edge, linewidth=1.25, radius=0.010)
        text(ax, 0.045, y + 0.103, row.gene, size=15.2, color=NAVY, weight="bold")
        context_x = {"APOE": 0.126, "COX7C": 0.135, "SELENOW": 0.151}[row.gene]
        text(ax, context_x, y + 0.103, row.contexts, size=9.8, color=MID, weight="bold")
        text(ax, 0.506, y + 0.103, row.primary_label, size=9.0, color=edge, weight="bold", ha="right")
        text(ax, 0.045, y + 0.063, row.secondary_label, size=9.6, color=DARK, weight="bold")
        text(ax, 0.045, y + 0.025, row.tertiary_label, size=9.0, color=MID)


def draw_chip(ax: plt.Axes, x: float, y: float, w: float, label: str, *,
              face: str, edge: str, hatch: str | None = None) -> None:
    rounded_box(ax, x, y, w, 0.040, face=face, edge=edge, linewidth=0.8,
                radius=0.006, hatch=hatch, zorder=2)
    text(ax, x + w / 2, y + 0.020, label, size=9.0, color=DARK,
         weight="bold", ha="center", zorder=4)


def draw_unresolved_panel(ax: plt.Axes, plot_data: pd.DataFrame, derived: dict[str, Any]) -> None:
    rounded_box(ax, 0.552, 0.147, 0.436, 0.572, face=WHITE, edge=LIGHT, linewidth=0.9)
    panel_heading(ax, "C", "Unresolved candidates", 0.568, 0.687)

    rounded_box(ax, 0.570, 0.402, 0.400, 0.244, face=PALE_GRAY, edge=GRAY,
                linewidth=0.9, radius=0.010)
    text(ax, 0.586, 0.616, "NO DIRECT MAPPING IN THE REGISTERED FILTERED SOURCE",
         size=9.2, color=NAVY, weight="bold")
    text(ax, 0.586, 0.584,
         f"{len(derived['no_direct_genes'])} nuclear genes  •  {derived['no_direct_contexts']} contexts",
         size=9.3, color=MID, weight="bold")
    genes = plot_data.loc[plot_data["record_type"].eq("no_direct_gene")].sort_values("display_order")
    chip_x = [0.584, 0.678, 0.772, 0.866]
    chip_y = [0.526, 0.477, 0.428, 0.379]
    for index, row in enumerate(genes.itertuples(index=False)):
        draw_chip(ax, chip_x[index % 4], chip_y[index // 4], 0.083, row.gene,
                  face=WHITE, edge="#929292")

    rounded_box(ax, 0.570, 0.174, 0.400, 0.190, face=WHITE, edge=DARK,
                linewidth=1.0, radius=0.010)
    text(ax, 0.586, 0.337, "NOT ASSESSABLE WITH THE AVAILABLE SOURCE",
         size=9.2, color=NAVY, weight="bold")
    text(ax, 0.586, 0.305,
         f"{len(derived['not_assessable_genes'])} mtDNA genes  •  {derived['not_assessable_contexts']} contexts",
         size=9.3, color=MID, weight="bold")
    mt = plot_data.loc[plot_data["record_type"].eq("not_assessable_gene")].sort_values("display_order")
    mt_x = [0.584, 0.711, 0.838]
    mt_y = [0.250, 0.202]
    for index, row in enumerate(mt.itertuples(index=False)):
        draw_chip(ax, mt_x[index % 3], mt_y[index // 3], 0.114, f"NA · {row.gene}",
                  face=WHITE, edge=DARK)
    text(ax, 0.586, 0.184,
         "Requires mtDNA-specific heteroplasmy, haplogroup, copy-number + NUMT controls.",
         size=9.0, color=MID)


def render_figure(plot_data: pd.DataFrame, derived: dict[str, Any], staging: Path) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "hatch.linewidth": 0.6,
        }
    )
    fig = plt.figure(figsize=FIGURE_SIZE, facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    draw_outcome_panel(ax, plot_data, derived["total_contexts"])
    draw_candidate_cards(ax, plot_data)
    draw_unresolved_panel(ax, plot_data, derived)
    rounded_box(ax, 0.012, 0.020, 0.976, 0.092, face=NAVY, edge=NAVY,
                linewidth=0.8, radius=0.008)
    text(ax, 0.500, 0.077,
         "No direct map ≠ no genetic role    •    Not assessable ≠ negative",
         size=12.0, color=WHITE, weight="bold", ha="center")
    text(ax, 0.500, 0.044,
         "Evidence categories summarize source coverage and direct mapping; they are not causal probabilities.",
         size=9.0, color="#DDE7F2", ha="center")
    fig.savefig(staging / OUTPUT_FILES[0], dpi=PNG_DPI, facecolor=WHITE)
    fig.savefig(staging / OUTPUT_FILES[1], facecolor=WHITE, metadata={"CreationDate": None})
    fig.savefig(staging / OUTPUT_FILES[2], facecolor=WHITE, metadata={"Date": None})
    plt.close(fig)


def build_checks(plot_data: pd.DataFrame, derived: dict[str, Any], frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    summary = frames["summary"]
    card_genes = set(plot_data.loc[plot_data["record_type"].eq("candidate_card"), "gene"])
    chip_genes = set(plot_data.loc[plot_data["record_type"].isin(["no_direct_gene", "not_assessable_gene"]), "gene"])
    displayed_genes = card_genes | chip_genes
    values = [
        ("source_status", "validated_complete_tier1", frames["source_status"].loc[0, "technical_status"]),
        ("candidate_context_rows", 47, len(summary)),
        ("unique_candidate_ids", 47, summary["candidate_id"].nunique()),
        ("unique_genes", 25, summary["gene"].nunique()),
        ("strong_contexts", 1, derived["grade_counts"]["strong"]),
        ("moderate_contexts", 0, derived["grade_counts"]["moderate"]),
        ("weak_contexts", 3, derived["grade_counts"]["weak"]),
        ("no_direct_contexts", 23, derived["grade_counts"]["none_found"]),
        ("not_assessable_contexts", 20, derived["grade_counts"]["not_assessable"]),
        ("displayed_gene_union", 25, len(displayed_genes)),
        ("displayed_gene_identity", "matches_summary", "matches_summary" if displayed_genes == set(summary["gene"]) else "mismatch"),
        ("candidate_card_genes", "APOE|COX7C|SELENOW", "|".join(sorted(card_genes))),
        ("no_direct_gene_count", 16, len(derived["no_direct_genes"])),
        ("not_assessable_gene_count", 6, len(derived["not_assessable_genes"])),
        ("visible_internal_phase_label", "absent", "absent" if "phase 19" not in derived["visible_text"].lower() and "phase19" not in derived["visible_text"].lower() else "present"),
        ("figure_size_inches", "12.4x4.7", f"{FIGURE_SIZE[0]}x{FIGURE_SIZE[1]}"),
        ("png_dpi", PNG_DPI, PNG_DPI),
    ]
    rows = []
    for check_id, expected, observed in values:
        status = "pass" if str(expected) == str(observed) else "fail"
        rows.append([SCHEMA, check_id, "blocking", status, expected, observed])
    checks = pd.DataFrame(
        rows,
        columns=["schema_version", "check_id", "severity", "status", "expected", "observed"],
    )
    if not checks["status"].eq("pass").all():
        failed = checks.loc[checks["status"].ne("pass"), "check_id"].tolist()
        raise ValueError("Figure checks failed: " + ", ".join(failed))
    return checks


def write_documentation(staging: Path) -> None:
    caption = """# Human genetic support across key-driver candidates

Panel A summarizes 47 gene × broad-network candidate contexts across
prespecified evidence grades. One APOE/astrocyte context has strong gene-level
AD support, while two COX7C contexts and one SELENOW context have weak or
limited support. Panel B states the direct evidence and context limitations for
these three genes. Panel C shows 16 nuclear genes (23 contexts) with no direct
mapping in the registered filtered summary and six mtDNA genes (20 contexts)
that cannot be assessed with the available nuclear GWAS/xQTL resource. “No
direct mapping” is a source-search outcome rather than evidence of no genetic
role; “not assessable” is not a negative result.
"""
    methods = """# Figure methods

The figure was generated from the validated human-genetic-support output
bundle. Candidate-context grades and network labels were read from
`genetic_support_evidence_summary.tsv`; variant annotations were read from
`genetic_support_common_variant_evidence.tsv.gz`; source context and confidence
labels were checked against `genetic_support_colocalization.tsv.gz`; and route
limitations were checked against `genetic_support_assessability.tsv`.

Counts are deterministic classifications, not statistical estimates, so no
error bars or significance annotations are shown. The horizontal bar counts
each displayed gene × broad-network context once. Gene chips list each unique
gene once within its terminal gene-level category. The two COX7C contexts use
the same underlying bulk-sQTL source record and are not independent
replications. Inclusion/confidence scores were not relabeled as classical
colocalization H0-H4 probabilities. The 12.4 × 4.7 inch composition uses direct
labels, colorblind-safe colors, filled versus open/hatch encoding, and vector
PDF/SVG exports for slide use and audit.
"""
    (staging / OUTPUT_FILES[5]).write_text(caption, encoding="utf-8")
    (staging / OUTPUT_FILES[6]).write_text(methods, encoding="utf-8")


def publish(input_root: Path, output_root: Path, force: bool) -> None:
    frames = validate_inputs(input_root)
    plot_data, derived = derive_plot_data(frames)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".genetic_support_slide_summary.", dir=output_root.parent))
    try:
        render_figure(plot_data, derived, staging)
        checks = build_checks(plot_data, derived, frames)
        write_tsv(plot_data, staging / OUTPUT_FILES[3])
        write_tsv(checks, staging / OUTPUT_FILES[4])
        write_documentation(staging)
        artifact_rows = []
        for name in OUTPUT_FILES[:-2]:
            path = staging / name
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError(f"Missing or empty declared artifact: {name}")
            rows: int | str = "NA"
            if name.endswith(".tsv"):
                rows = len(pd.read_csv(path, sep="\t"))
            artifact_rows.append([SCHEMA, name, path.stat().st_size, sha256(path), rows, "validated"])
        artifacts = pd.DataFrame(
            artifact_rows,
            columns=["schema_version", "path", "bytes", "sha256", "rows", "validation_state"],
        )
        write_tsv(artifacts, staging / OUTPUT_FILES[7])
        status = pd.DataFrame(
            [{
                "schema_version": SCHEMA,
                "technical_status": "validated_complete",
                "scientific_status": "descriptive_evidence_summary",
                "candidate_contexts": derived["total_contexts"],
                "unique_genes": derived["unique_genes"],
                "output_files": len(OUTPUT_FILES),
                "visible_internal_phase_label": False,
                "completed_utc": datetime.now(timezone.utc).isoformat(),
            }]
        )
        write_tsv(status, staging / OUTPUT_FILES[8])
        actual = sorted(path.name for path in staging.iterdir() if path.is_file())
        if actual != sorted(OUTPUT_FILES):
            raise ValueError(f"Output contract mismatch: {actual}")
        if output_root.exists():
            if not force:
                raise FileExistsError(f"Output exists; use --force to replace: {output_root}")
            backup_root = Path.cwd() / "tmp" / "phase19_genetic_support_figure_backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / f"{output_root.name}_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{os.getpid()}"
            output_root.replace(backup)
        staging.replace(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"Published {len(OUTPUT_FILES)} validated figure files to {output_root}")


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    publish(resolve(root, args.input_root), resolve(root, args.output_root), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
