#!/usr/bin/env python3
"""Render the two requested Phase 20 broad-cell KDA summary figures.

DEPRECATED (2026-08-29): these figures visualize the deprecated direct
broad-cell analysis
(``results/minerva_production/20_sex_apoe_kda_broad (deprecated)``); the
figure bundles were renamed to
``results/figures/analysis/phase_20_sex_apoe_kda_broad (deprecated)``. The
authoritative figures come from the returned-only simple aggregation renderer
under ``scripts/figures/analysis/phase_20_sex_apoe_simple_aggr/``. Retained
for provenance only.

The broad-cell branch is a direct, direction-specific KDA analysis.  It does
not use ACAT or any other cross-run aggregation.  The first output keeps the
horizontal-bar visual role of the fine-cell recurrence figure, but plots
within-run evidence because no broad candidate recurs across runs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


# Matplotlib must be configured before it is imported.  The user's default
# cache location is not writable in all execution environments.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "phase20_broad_matplotlib")
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402


SCRIPT_ROOT = Path(__file__).resolve().parents[4]
SKILL_SCRIPTS = (
    SCRIPT_ROOT / ".agents" / "skills" / "scientific-visualization" / "scripts"
)
sys.path.insert(0, str(SKILL_SCRIPTS))
from figure_export import save_publication_figure  # noqa: E402
from style_presets import apply_publication_style  # noqa: E402


ANALYSIS_ID = "phase20_sex_apoe_kda_broad_v1"
FIGURE_SCHEMA_ROOT = "phase20_broad_non_mt_figure"
STRICT_COLOR = "#0072B2"  # Okabe-Ito blue
RELAXED_COLOR = "#E69F00"  # Okabe-Ito orange
TEXT_COLOR = "#222222"
MUTED_COLOR = "#5C5C5C"
GRID_COLOR = "#E5E5E5"

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
DIRECTION_ORDER = ["AD_up_mito", "AD_down_mito"]
NETWORK_LABEL = {
    "Astrocytes": "Astrocytes",
    "Excitatory_neurons": "Excitatory neurons",
    "Inhibitory_neurons": "Inhibitory neurons",
    "Microglia": "Microglia",
    "OPCs": "OPCs",
    "Oligodendrocytes": "Oligodendrocytes",
    "Vasculature_cells": "Vasculature",
}
DIRECTION_LABEL = {"AD_up_mito": "AD up", "AD_down_mito": "AD down"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=SCRIPT_ROOT,
        help="Repository root (defaults to the root inferred from this script).",
    )
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"Missing TSV header: {path}")
        return [dict(row) for row in reader]


def write_tsv(
    rows: Sequence[dict[str, Any]], path: Path, fieldnames: Sequence[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        "TRUE"
                        if value is True
                        else "FALSE"
                        if value is False
                        else "NA"
                        if value is None
                        else value
                    )
                    for key, value in row.items()
                }
            )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: Any) -> bool:
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES"}


def as_int(value: Any) -> int:
    return int(str(value))


def as_float(value: Any) -> float:
    return float(str(value))


def require_columns(
    rows: Sequence[dict[str, str]], required: Iterable[str], label: str
) -> None:
    if not rows:
        raise ValueError(f"{label} is empty")
    missing = sorted(set(required) - set(rows[0]))
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def check(
    check_id: str, observed: Any, expected: Any, passed: bool
) -> dict[str, Any]:
    return {
        "schema_version": f"{FIGURE_SCHEMA_ROOT}_checks_v1",
        "check_id": check_id,
        "severity": "error",
        "observed": observed,
        "expected": expected,
        "passed": bool(passed),
    }


def candidate_key(row: dict[str, str]) -> tuple[str, str]:
    return row["kda_run_id"], row["current_symbol"]


def order_key(row: dict[str, str]) -> tuple[int, int, int, int]:
    return (
        NETWORK_ORDER.index(row["broad_cell_type"]),
        GROUP_ORDER.index(row["group_id"]),
        DIRECTION_ORDER.index(row["signature_direction"]),
        as_int(row.get("direction_rank") or 0),
    )


def run_short_label(row: dict[str, str]) -> str:
    return " · ".join(
        [
            row["group_id"],
            NETWORK_LABEL[row["broad_cell_type"]],
            DIRECTION_LABEL[row["signature_direction"]],
        ]
    )


def load_source(root: Path) -> dict[str, Any]:
    result_dir = root / "results" / "minerva_production" / "20_sex_apoe_kda_broad"
    paths = {
        "status": result_dir / "phase20_broad_status.tsv",
        "checks": result_dir / "phase20_broad_checks.tsv",
        "artifacts": result_dir / "phase20_broad_artifacts.tsv",
        "directions": result_dir / "phase20_broad_direction_manifest.tsv",
        "candidates": result_dir / "phase20_broad_non_mt_candidates.tsv",
        "top5": result_dir / "phase20_broad_top5_summary.tsv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing broad KDA input(s): " + ", ".join(missing))

    tables = {name: read_tsv(path) for name, path in paths.items()}
    if len(tables["status"]) != 1:
        raise ValueError("phase20_broad_status.tsv must contain exactly one row")

    require_columns(
        tables["status"],
        [
            "analysis_id",
            "task_mode",
            "aggregation_method",
            "primary_completed_runs",
            "relaxed_non_mt_candidates",
            "strict_non_mt_candidates",
            "failed_checks",
            "validation_status",
        ],
        "broad status",
    )
    require_columns(
        tables["directions"],
        [
            "kda_run_id",
            "category_id",
            "broad_cell_type",
            "group_id",
            "signature_direction",
            "query_size_tier",
            "effective_query_genes",
            "non_mt_candidate_family_size",
            "relaxed_non_mt_candidates",
            "strict_non_mt_candidates",
            "terminal_status",
        ],
        "broad direction manifest",
    )
    candidate_required = [
        "analysis_id",
        "query_tier",
        "kda_run_id",
        "category_id",
        "contrast_id",
        "broad_cell_type",
        "group_id",
        "sex",
        "apoe_group",
        "signature_direction",
        "query_size_tier",
        "effective_query_genes",
        "current_symbol",
        "is_core_mito",
        "query_overlap",
        "fold_enrichment",
        "raw_p_value",
        "non_mt_run_q",
        "overlap_gate_pass",
        "fold_enrichment_gate_pass",
        "relaxed_q_gate_pass",
        "relaxed_primary_candidate",
        "strict_direct_reference",
        "direction_rank",
        "top5_display",
    ]
    require_columns(tables["candidates"], candidate_required, "broad candidates")
    require_columns(tables["top5"], candidate_required, "broad top-five summary")
    require_columns(
        tables["checks"], ["check_id", "passed"], "broad production checks"
    )
    require_columns(
        tables["artifacts"],
        ["path", "bytes", "sha256"],
        "broad production artifacts",
    )

    status = tables["status"][0]
    candidates = sorted(tables["candidates"], key=order_key)
    top5 = sorted(tables["top5"], key=order_key)
    completed = sorted(
        [
            row
            for row in tables["directions"]
            if row["terminal_status"].startswith("completed")
        ],
        key=order_key,
    )
    run_map = {row["kda_run_id"]: row for row in completed}

    artifact_map = {row["path"]: row for row in tables["artifacts"]}
    hashed_input_names = [
        "phase20_broad_direction_manifest.tsv",
        "phase20_broad_non_mt_candidates.tsv",
        "phase20_broad_top5_summary.tsv",
        "phase20_broad_checks.tsv",
    ]
    matching_hashes = 0
    for name in hashed_input_names:
        registered = artifact_map.get(name)
        path = result_dir / name
        if (
            registered is not None
            and as_int(registered["bytes"]) == path.stat().st_size
            and registered["sha256"] == sha256(path)
        ):
            matching_hashes += 1

    source_checks_passed = sum(truth(row["passed"]) for row in tables["checks"])
    source_failed_checks = len(tables["checks"]) - source_checks_passed
    source_checks = [
        check(
            "source_status_validated",
            status["validation_status"],
            "validated_complete",
            status["validation_status"] == "validated_complete",
        ),
        check(
            "source_failed_checks_zero",
            source_failed_checks,
            0,
            source_failed_checks == 0 and as_int(status["failed_checks"]) == 0,
        ),
        check(
            "source_direct_no_acat_contract",
            f"{status['task_mode']}|{status['aggregation_method']}",
            "direct_broad_kda_no_acat|none",
            status["task_mode"] == "direct_broad_kda_no_acat"
            and status["aggregation_method"] == "none",
        ),
        check(
            "source_registered_hashes_match",
            matching_hashes,
            len(hashed_input_names),
            matching_hashes == len(hashed_input_names),
        ),
    ]

    return {
        "result_dir": result_dir,
        "paths": paths,
        "status": status,
        "source_checks": source_checks,
        "candidates": candidates,
        "top5": top5,
        "completed": completed,
        "run_map": run_map,
    }


EVIDENCE_FIELDS = [
    "schema_version",
    "analysis_id",
    "kda_run_id",
    "category_id",
    "contrast_id",
    "broad_cell_type",
    "group_id",
    "sex",
    "apoe_group",
    "signature_direction",
    "query_size_tier",
    "effective_query_genes",
    "non_mt_candidate_family_size",
    "current_symbol",
    "direction_rank",
    "query_overlap",
    "fold_enrichment",
    "raw_p_value",
    "non_mt_run_q",
    "neg_log10_non_mt_run_q",
    "strict_direct_reference",
    "threshold_tier",
    "run_label",
]


TOP5_FIELDS = [
    "schema_version",
    "analysis_id",
    "kda_run_id",
    "category_id",
    "contrast_id",
    "broad_cell_type",
    "group_id",
    "sex",
    "apoe_group",
    "signature_direction",
    "query_size_tier",
    "effective_query_genes",
    "non_mt_candidate_family_size",
    "current_symbol",
    "direction_rank",
    "query_overlap",
    "fold_enrichment",
    "raw_p_value",
    "non_mt_run_q",
    "strict_direct_reference",
    "threshold_tier",
    "run_label",
]


def decorate_rows(
    rows: Sequence[dict[str, str]], source: dict[str, Any], schema: str
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for original in rows:
        row: dict[str, Any] = dict(original)
        run = source["run_map"][row["kda_run_id"]]
        row["schema_version"] = schema
        row["non_mt_candidate_family_size"] = run["non_mt_candidate_family_size"]
        row["neg_log10_non_mt_run_q"] = f"{-math.log10(as_float(row['non_mt_run_q'])):.12g}"
        row["threshold_tier"] = (
            "strict direct reference"
            if truth(row["strict_direct_reference"])
            else "relaxed only"
        )
        row["run_label"] = run_short_label(row)
        decorated.append(row)
    return decorated


def q_text(q_value: float) -> str:
    if q_value < 0.01:
        return f"q = {q_value:.2g}"
    return f"q = {q_value:.3f}"


def make_driver_evidence_figure(
    evidence: Sequence[dict[str, Any]], source: dict[str, Any]
) -> plt.Figure:
    run_ids = []
    for row in evidence:
        if row["kda_run_id"] not in run_ids:
            run_ids.append(row["kda_run_id"])

    counts = Counter(row["kda_run_id"] for row in evidence)
    ratios = [max(3, counts[run_id]) for run_id in run_ids]
    fig, axes = plt.subplots(
        len(run_ids),
        1,
        figsize=(8, 7),
        sharex=True,
        gridspec_kw={"height_ratios": ratios},
    )
    axes = np.atleast_1d(axes)
    x_max = max(as_float(row["neg_log10_non_mt_run_q"]) for row in evidence) + 0.52

    for axis, run_id in zip(axes, run_ids, strict=True):
        run_rows = sorted(
            [row for row in evidence if row["kda_run_id"] == run_id],
            key=lambda row: as_int(row["direction_rank"]),
        )
        run = source["run_map"][run_id]
        y_pos = np.arange(len(run_rows))
        values = [as_float(row["neg_log10_non_mt_run_q"]) for row in run_rows]
        colors = [
            STRICT_COLOR
            if row["threshold_tier"] == "strict direct reference"
            else RELAXED_COLOR
            for row in run_rows
        ]
        bars = axis.barh(
            y_pos,
            values,
            height=0.68,
            color=colors,
            edgecolor="white",
            linewidth=0.7,
        )
        for bar, row in zip(bars, run_rows, strict=True):
            if row["threshold_tier"] == "relaxed only":
                bar.set_hatch("///")
                bar.set_edgecolor("#704900")
            axis.text(
                as_float(row["neg_log10_non_mt_run_q"]) + 0.035,
                bar.get_y() + bar.get_height() / 2,
                q_text(as_float(row["non_mt_run_q"])),
                ha="left",
                va="center",
                fontsize=7.2,
                color=TEXT_COLOR,
            )

        axis.set_yticks(y_pos, [row["current_symbol"] for row in run_rows])
        axis.invert_yaxis()
        tier_note = (
            "small-query tier"
            if run["query_size_tier"] == "small_query_3_9"
            else "phase-18-sized query tier"
        )
        axis.set_title(
            f"{run_short_label(run)}  |  query n = {run['effective_query_genes']} "
            f"({tier_note}); BH family = {run['non_mt_candidate_family_size']}",
            loc="left",
            fontsize=9.3,
            fontweight="bold",
            color=TEXT_COLOR,
            pad=6,
        )
        axis.axvline(-math.log10(0.10), color="#8A8A8A", linestyle=":", linewidth=1)
        axis.axvline(-math.log10(0.05), color="#4F4F4F", linestyle="--", linewidth=1)
        axis.set_xlim(0, x_max)
        axis.grid(axis="x", color=GRID_COLOR, linewidth=0.75)
        axis.tick_params(axis="y", length=0, labelsize=8.2)
        axis.tick_params(axis="x", labelsize=8)
        axis.spines["left"].set_visible(False)
        axis.spines["bottom"].set_color("#777777")

    axes[-1].set_xlabel(
        r"Direct within-run evidence, $-\log_{10}$(non-core-MT BH q)", fontsize=9
    )
    fig.suptitle(
        "Direct broad-cell non-MT key-driver evidence",
        x=0.16,
        y=0.975,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    fig.text(
        0.16,
        0.925,
        "No cross-run recurrence: each of 12 relaxed candidates occurs in one primary KDA run.\n"
        "Bars show direct within-run evidence; no ACAT or cross-run aggregation was used.",
        ha="left",
        va="top",
        fontsize=9.5,
        color=MUTED_COLOR,
        linespacing=1.35,
    )
    empty_runs = [
        row
        for row in source["completed"]
        if as_int(row["relaxed_non_mt_candidates"]) == 0
    ]
    empty_note = "; ".join(
        f"{run_short_label(row)} (query n = {row['effective_query_genes']})"
        for row in empty_runs
    )
    fig.text(
        0.16,
        0.093,
        f"Completed with no selected candidate: {empty_note}.",
        ha="left",
        va="center",
        fontsize=7.7,
        color=MUTED_COLOR,
    )
    legend_handles = [
        Patch(facecolor=STRICT_COLOR, edgecolor="white", label="Strict: q ≤ 0.05"),
        Patch(
            facecolor=RELAXED_COLOR,
            edgecolor="#704900",
            hatch="///",
            label="Relaxed only: 0.05 < q ≤ 0.10",
        ),
        Line2D(
            [0], [0], color="#8A8A8A", linestyle=":", linewidth=1, label="q = 0.10"
        ),
        Line2D(
            [0], [0], color="#4F4F4F", linestyle="--", linewidth=1, label="q = 0.05"
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.56, 0.018),
        ncol=4,
        frameon=False,
        fontsize=7.4,
        handlelength=1.8,
        columnspacing=1.2,
    )
    fig.subplots_adjust(left=0.20, right=0.965, top=0.82, bottom=0.18, hspace=0.58)
    return fig


def make_top5_figure(
    top5: Sequence[dict[str, Any]], source: dict[str, Any]
) -> plt.Figure:
    completed = list(source["completed"])
    # Keep the two Astrocyte runs adjacent, followed by the OPC run.
    completed.sort(key=lambda row: order_key(row))
    row_index = {row["kda_run_id"]: index + 1 for index, row in enumerate(completed)}

    fig, axis = plt.subplots(figsize=(9, 4.5))
    axis.set_xlim(0.5, 5.5)
    axis.set_ylim(len(completed) + 0.5, 0.5)

    for x_value in np.arange(0.5, 6.0, 1.0):
        axis.axvline(x_value, color=GRID_COLOR, linewidth=0.8, zorder=0)
    for y_value in np.arange(0.5, len(completed) + 1.0, 1.0):
        axis.axhline(y_value, color=GRID_COLOR, linewidth=0.8, zorder=0)

    for row in top5:
        rank = as_int(row["direction_rank"])
        y_value = row_index[row["kda_run_id"]]
        strict = row["threshold_tier"] == "strict direct reference"
        rect = Rectangle(
            (rank - 0.48, y_value - 0.41),
            0.96,
            0.82,
            facecolor=STRICT_COLOR if strict else RELAXED_COLOR,
            edgecolor="white" if strict else "#704900",
            linewidth=0.8,
            hatch=None if strict else "///",
            zorder=2,
        )
        axis.add_patch(rect)
        axis.text(
            rank,
            y_value,
            row["current_symbol"],
            ha="center",
            va="center",
            fontsize=8.4,
            color="white" if strict else "#1F1F1F",
            fontweight="bold",
            zorder=3,
        )

    for run in completed:
        if as_int(run["relaxed_non_mt_candidates"]) == 0:
            axis.text(
                3,
                row_index[run["kda_run_id"]],
                "Completed · no selected candidate",
                ha="center",
                va="center",
                fontsize=8.3,
                color=MUTED_COLOR,
                style="italic",
                zorder=3,
            )

    axis.set_xticks(range(1, 6), [str(value) for value in range(1, 6)])
    axis.set_yticks(
        range(1, len(completed) + 1),
        [run_short_label(row) for row in completed],
    )
    axis.set_xlabel("Within-run rank", fontsize=9)
    axis.set_ylabel("Sex/APOE · broad cell type · DEG direction", fontsize=9)
    axis.tick_params(axis="y", length=0, labelsize=8.3)
    axis.tick_params(axis="x", length=0, labelsize=8)
    for spine in axis.spines.values():
        spine.set_visible(False)

    fig.suptitle(
        "Top five broad-cell non-MT key drivers",
        x=0.31,
        y=0.96,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    fig.text(
        0.31,
        0.895,
        "Frozen direct within-run ranks; empty ranks are not backfilled and no ACAT is used.\n"
        "All seven displayed candidates also pass the strict direct-reference threshold.",
        ha="left",
        va="top",
        fontsize=9.3,
        color=MUTED_COLOR,
        linespacing=1.35,
    )
    legend_handles = [
        Patch(facecolor=STRICT_COLOR, edgecolor="white", label="Strict: q ≤ 0.05"),
        Patch(
            facecolor=RELAXED_COLOR,
            edgecolor="#704900",
            hatch="///",
            label="Relaxed only: 0.05 < q ≤ 0.10",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.63, 0.025),
        ncol=2,
        frameon=False,
        fontsize=8,
        handlelength=2,
        columnspacing=1.8,
    )
    fig.subplots_adjust(left=0.31, right=0.97, top=0.76, bottom=0.23)
    return fig


def png_metadata(path: Path) -> tuple[str, str, bool]:
    with Image.open(path) as image:
        dimensions = f"{image.width}x{image.height}"
        dpi = image.info.get("dpi", (0.0, 0.0))
        dpi_text = f"{dpi[0]:.1f}x{dpi[1]:.1f}"
        dpi_ok = abs(dpi[0] - 300) <= 1 and abs(dpi[1] - 300) <= 1
    return dimensions, dpi_text, dpi_ok


def bundle_file_checks(
    paths: dict[str, Path], expected_dimensions: str
) -> list[dict[str, Any]]:
    core_names = ["png", "svg", "pdf", "data", "caption", "methods"]
    existing = sum(paths[name].is_file() for name in core_names)
    nonempty = sum(
        paths[name].is_file() and paths[name].stat().st_size > 0 for name in core_names
    )
    dimensions, dpi_text, dpi_ok = png_metadata(paths["png"])
    pdf_ok = paths["pdf"].read_bytes()[:4] == b"%PDF"
    svg_head = paths["svg"].read_text(encoding="utf-8", errors="replace")[:2000]
    svg_ok = "<svg" in svg_head
    return [
        check("core_artifacts_exist", existing, len(core_names), existing == len(core_names)),
        check(
            "core_artifacts_nonempty", nonempty, len(core_names), nonempty == len(core_names)
        ),
        check(
            "png_dimensions", dimensions, expected_dimensions, dimensions == expected_dimensions
        ),
        check("png_resolution_dpi", dpi_text, "300x300 (±1)", dpi_ok),
        check("pdf_signature", "%PDF" if pdf_ok else "invalid", "%PDF", pdf_ok),
        check("svg_root", "<svg" if svg_ok else "missing", "<svg", svg_ok),
    ]


def save_bundle(
    *,
    figure_root: Path,
    figure_id: str,
    stem: str,
    figure: plt.Figure,
    plot_rows: Sequence[dict[str, Any]],
    plot_fields: Sequence[str],
    caption: str,
    methods: str,
    scientific_checks: list[dict[str, Any]],
    expected_dimensions: str,
) -> dict[str, Any]:
    bundle = figure_root / figure_id
    bundle.mkdir(parents=True, exist_ok=True)
    paths = {
        "png": bundle / f"{stem}.png",
        "svg": bundle / f"{stem}.svg",
        "pdf": bundle / f"{stem}.pdf",
        "data": bundle / f"{stem}_plot_data.tsv",
        "caption": bundle / f"{stem}_caption.md",
        "methods": bundle / f"{stem}_methods.md",
        "checks": bundle / f"{stem}_checks.tsv",
        "status": bundle / f"{stem}_status.tsv",
        "artifacts": bundle / f"{stem}_artifacts.tsv",
    }

    write_tsv(plot_rows, paths["data"], plot_fields)
    paths["caption"].write_text(caption.rstrip() + "\n", encoding="utf-8")
    paths["methods"].write_text(methods.rstrip() + "\n", encoding="utf-8")
    saved = save_publication_figure(
        figure,
        bundle / stem,
        formats=["png", "svg", "pdf"],
        dpi=300,
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(figure)
    if len(saved) != 3:
        raise RuntimeError(f"Failed to export all formats for {figure_id}")

    all_checks = list(scientific_checks)
    all_checks.extend(bundle_file_checks(paths, expected_dimensions))
    write_tsv(
        all_checks,
        paths["checks"],
        ["schema_version", "check_id", "severity", "observed", "expected", "passed"],
    )
    failed = sum(not row["passed"] for row in all_checks)
    validation_status = "validated_complete" if failed == 0 else "validation_failed"
    write_tsv(
        [
            {
                "schema_version": f"{FIGURE_SCHEMA_ROOT}_status_v1",
                "figure_id": figure_id,
                "plot_data_rows": len(plot_rows),
                "failed_checks": failed,
                "validation_status": validation_status,
            }
        ],
        paths["status"],
        [
            "schema_version",
            "figure_id",
            "plot_data_rows",
            "failed_checks",
            "validation_status",
        ],
    )

    artifact_names = [
        "png",
        "svg",
        "pdf",
        "data",
        "caption",
        "methods",
        "checks",
        "status",
    ]
    artifact_rows = []
    for order, name in enumerate(artifact_names, start=1):
        path = paths[name]
        artifact_rows.append(
            {
                "schema_version": f"{FIGURE_SCHEMA_ROOT}_artifacts_v1",
                "artifact_order": order,
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "hash_status": "recorded",
            }
        )
    write_tsv(
        artifact_rows,
        paths["artifacts"],
        [
            "schema_version",
            "artifact_order",
            "path",
            "bytes",
            "sha256",
            "hash_status",
        ],
    )

    expected_inventory = {path.name for path in paths.values()}
    observed_inventory = {path.name for path in bundle.iterdir() if path.is_file()}
    if observed_inventory != expected_inventory:
        raise RuntimeError(
            f"Unexpected inventory for {figure_id}: "
            f"expected={sorted(expected_inventory)}, observed={sorted(observed_inventory)}"
        )
    for row in artifact_rows:
        path = bundle / str(row["path"])
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise RuntimeError(f"Artifact registry mismatch: {path}")
    if failed:
        failed_ids = [row["check_id"] for row in all_checks if not row["passed"]]
        raise RuntimeError(f"{figure_id} failed checks: {', '.join(failed_ids)}")

    return {
        "schema_version": f"{FIGURE_SCHEMA_ROOT}_manifest_v1",
        "figure_id": figure_id,
        "directory": str(bundle.relative_to(figure_root.parents[3])),
        "plot_data_rows": len(plot_rows),
        "validation_status": validation_status,
    }


def common_candidate_checks(
    source: dict[str, Any], candidates: Sequence[dict[str, str]]
) -> list[dict[str, Any]]:
    keys = [candidate_key(row) for row in candidates]
    symbols = [row["current_symbol"] for row in candidates]
    strict_count = sum(truth(row["strict_direct_reference"]) for row in candidates)
    relaxed_only_count = len(candidates) - strict_count
    gate_failures = sum(
        not (
            truth(row["overlap_gate_pass"])
            and truth(row["fold_enrichment_gate_pass"])
            and truth(row["relaxed_q_gate_pass"])
            and truth(row["relaxed_primary_candidate"])
            and as_int(row["query_overlap"]) >= 2
            and as_float(row["fold_enrichment"]) > 1
            and as_float(row["non_mt_run_q"]) <= 0.10 + 1e-12
        )
        for row in candidates
    )
    tier_mismatches = sum(
        truth(row["strict_direct_reference"])
        != (as_float(row["non_mt_run_q"]) <= 0.05 + 1e-12)
        for row in candidates
    )
    candidate_run_counts = Counter(symbols)
    recurring_genes = sum(count > 1 for count in candidate_run_counts.values())
    completed_positive = sum(
        as_int(row["relaxed_non_mt_candidates"]) > 0 for row in source["completed"]
    )
    completed_empty = len(source["completed"]) - completed_positive
    return list(source["source_checks"]) + [
        check("candidate_rows", len(candidates), 12, len(candidates) == 12),
        check("candidate_units_unique", len(set(keys)), 12, len(set(keys)) == 12),
        check("candidate_symbols_unique", len(set(symbols)), 12, len(set(symbols)) == 12),
        check("genes_recurring_across_runs", recurring_genes, 0, recurring_genes == 0),
        check(
            "completed_primary_runs",
            len(source["completed"]),
            3,
            len(source["completed"]) == 3,
        ),
        check(
            "candidate_positive_completed_runs",
            completed_positive,
            2,
            completed_positive == 2,
        ),
        check(
            "completed_zero_candidate_runs", completed_empty, 1, completed_empty == 1
        ),
        check("candidate_gate_failures", gate_failures, 0, gate_failures == 0),
        check(
            "core_mito_candidate_rows",
            sum(truth(row["is_core_mito"]) for row in candidates),
            0,
            all(not truth(row["is_core_mito"]) for row in candidates),
        ),
        check("strict_candidate_rows", strict_count, 9, strict_count == 9),
        check("relaxed_only_candidate_rows", relaxed_only_count, 3, relaxed_only_count == 3),
        check("strict_tier_q_mismatches", tier_mismatches, 0, tier_mismatches == 0),
    ]


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    source = load_source(root)
    figure_root = (
        root
        / "results"
        / "figures"
        / "analysis"
        / "phase_20_sex_apoe_kda_broad"
    )
    figure_root.mkdir(parents=True, exist_ok=True)

    apply_publication_style("default")
    plt.rcParams.update(
        {
            "figure.constrained_layout.use": False,
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.bbox": None,
        }
    )

    evidence = decorate_rows(
        source["candidates"], source, "phase20_broad_driver_evidence_plot_data_v1"
    )
    top5 = decorate_rows(
        source["top5"], source, "phase20_broad_top5_plot_data_v1"
    )

    common_checks = common_candidate_checks(source, source["candidates"])
    evidence_keys = {candidate_key(row) for row in evidence}
    source_candidate_keys = {candidate_key(row) for row in source["candidates"]}
    evidence_checks = common_checks + [
        check(
            "plot_source_key_parity",
            len(evidence_keys & source_candidate_keys),
            12,
            evidence_keys == source_candidate_keys,
        ),
        check(
            "plot_aggregation_fields",
            sum(
                any(token in field.lower() for token in ["acat", "coverage", "support"])
                for field in EVIDENCE_FIELDS
            ),
            0,
            not any(
                any(token in field.lower() for token in ["acat", "coverage", "support"])
                for field in EVIDENCE_FIELDS
            ),
        ),
    ]

    source_top5_keys = {candidate_key(row) for row in source["top5"]}
    expected_top5_keys = {
        candidate_key(row)
        for row in source["candidates"]
        if truth(row["top5_display"])
    }
    top5_counts = Counter(row["kda_run_id"] for row in source["top5"])
    top5_count_text = ";".join(
        f"{run_id}={top5_counts[run_id]}" for run_id in sorted(top5_counts)
    )
    expected_count_text = ";".join(
        [
            "broad__relaxed__Astrocytes__F_e4__AD_down_mito=2",
            "broad__relaxed__OPCs__F_e4__AD_down_mito=5",
        ]
    )
    rank_sets = {
        run_id: sorted(as_int(row["direction_rank"]) for row in source["top5"] if row["kda_run_id"] == run_id)
        for run_id in top5_counts
    }
    ranks_ok = sorted(rank_sets.values()) == [[1, 2], [1, 2, 3, 4, 5]]
    top5_checks = list(source["source_checks"]) + [
        check("top5_rows", len(top5), 7, len(top5) == 7),
        check(
            "top5_units_unique",
            len(source_top5_keys),
            7,
            len(source_top5_keys) == 7,
        ),
        check(
            "top5_source_subset_parity",
            len(source_top5_keys & expected_top5_keys),
            7,
            source_top5_keys == expected_top5_keys,
        ),
        check(
            "top5_run_counts", top5_count_text, expected_count_text, top5_count_text == expected_count_text
        ),
        check(
            "top5_rank_sets",
            "|".join(",".join(map(str, values)) for values in sorted(rank_sets.values())),
            "1,2|1,2,3,4,5",
            ranks_ok,
        ),
        check(
            "top5_display_flags",
            sum(truth(row["top5_display"]) for row in source["top5"]),
            7,
            all(truth(row["top5_display"]) for row in source["top5"]),
        ),
        check(
            "top5_strict_rows",
            sum(truth(row["strict_direct_reference"]) for row in source["top5"]),
            7,
            all(truth(row["strict_direct_reference"]) for row in source["top5"]),
        ),
        check(
            "top5_gate_failures",
            sum(
                not (
                    truth(row["relaxed_primary_candidate"])
                    and not truth(row["is_core_mito"])
                    and as_int(row["query_overlap"]) >= 2
                    and as_float(row["fold_enrichment"]) > 1
                    and as_float(row["non_mt_run_q"]) <= 0.10 + 1e-12
                )
                for row in source["top5"]
            ),
            0,
            all(
                truth(row["relaxed_primary_candidate"])
                and not truth(row["is_core_mito"])
                and as_int(row["query_overlap"]) >= 2
                and as_float(row["fold_enrichment"]) > 1
                and as_float(row["non_mt_run_q"]) <= 0.10 + 1e-12
                for row in source["top5"]
            ),
        ),
        check(
            "top5_plot_aggregation_fields",
            sum(
                any(token in field.lower() for token in ["acat", "coverage", "support"])
                for field in TOP5_FIELDS
            ),
            0,
            not any(
                any(token in field.lower() for token in ["acat", "coverage", "support"])
                for field in TOP5_FIELDS
            ),
        ),
    ]

    recurrence_caption = """# Phase 20 broad direct-driver evidence (recurrence analogue)

This horizontal-bar analogue to the fine-cell recurrence figure shows all 12 relaxed direct broad-cell non-core-MT candidates. Bar length is −log10 of the BH q value calculated within that candidate's own KDA run; blue bars pass the strict direct-reference threshold (q ≤ 0.05), and hatched orange bars pass only the relaxed threshold (0.05 < q ≤ 0.10).

No candidate recurs across the three completed primary broad-cell KDA runs: each of the 12 genes occurs in exactly one run. The Astrocytes · M_e33 · AD-down run completed with no selected candidate and therefore has no bar. There is no ACAT or cross-run inferential aggregation in this broad branch, and q values from different run-specific BH families are not a formal between-run comparison. “AD down” identifies the source DEG-query direction; it does not assert that the candidate driver gene itself is downregulated.
"""
    recurrence_methods = """# Methods

The renderer reads the validated production tables `phase20_broad_status.tsv`, `phase20_broad_checks.tsv`, `phase20_broad_artifacts.tsv`, `phase20_broad_direction_manifest.tsv`, and `phase20_broad_non_mt_candidates.tsv` from `results/minerva_production/20_sex_apoe_kda_broad`. Registered byte sizes and SHA-256 hashes are checked for the direction manifest, candidate table, production checks, and top-five table before plotting.

The plot contains one row per frozen relaxed primary candidate, without grouping, deduplication, reranking, or cross-run aggregation. Candidates must be non-core-MT, have query overlap ≥ 2, fold enrichment > 1, and a non-core-MT within-run BH q ≤ 0.10. The strict direct-reference tier uses the same gates with q ≤ 0.05. Stored `direction_rank` determines the vertical order within each run. Bars show −log10(`non_mt_run_q`); dotted and dashed reference lines mark q = 0.10 and q = 0.05, respectively. The run-specific BH family sizes are 151 genes for Astrocytes · F_e4 · AD down and 133 genes for OPCs · F_e4 · AD down; the completed Astrocytes · M_e33 · AD-down run tested a 78-gene non-core-MT family and selected zero candidates.

The figure uses Okabe-Ito blue and orange, with hatching as a redundant tier encoding. It is exported as a 300-DPI PNG and as vector SVG and PDF files. The output bundle records the exact plotted rows, checks, validation status, file sizes, and SHA-256 hashes.
"""
    top5_caption = """# Phase 20 broad top-five candidates

Up to five frozen relaxed non-core-MT candidates are shown per completed direct broad-cell KDA run. The Astrocytes · F_e4 · AD-down run contributes ELL2 and SLC44A3; the OPCs · F_e4 · AD-down run contributes CAMK2D, RAPGEF4, RAB3IP, FOXN3, and AC092691.1. All seven displayed genes also pass the strict direct-reference threshold (q ≤ 0.05).

Ranks are the stored within-run `direction_rank` values; missing ranks are left blank and are not backfilled. The completed Astrocytes · M_e33 · AD-down run selected no candidate and is displayed explicitly as empty. No ACAT or cross-run aggregation is used. “AD down” identifies the source DEG-query direction, not the expression direction of the candidate driver gene.
"""
    top5_methods = """# Methods

The renderer reads the validated production tables `phase20_broad_status.tsv`, `phase20_broad_checks.tsv`, `phase20_broad_artifacts.tsv`, `phase20_broad_direction_manifest.tsv`, `phase20_broad_non_mt_candidates.tsv`, and `phase20_broad_top5_summary.tsv` from `results/minerva_production/20_sex_apoe_kda_broad`. Registered source hashes are verified before plotting.

The seven plotted candidate tiles are an exact key-level copy of rows flagged `top5_display = TRUE` in the 12-row relaxed candidate table and stored in `phase20_broad_top5_summary.tsv`. The renderer does not rerank candidates. The upstream order is the direct within-run order, and at most ranks 1–5 are displayed. Candidate gates are query overlap ≥ 2, fold enrichment > 1, non-core-MT within-run BH q ≤ 0.10, and exclusion of core mitochondrial genes; the strict reference uses q ≤ 0.05. The empty completed run annotation comes from `phase20_broad_direction_manifest.tsv`.

Tiles use Okabe-Ito blue for strict direct-reference candidates and hatched orange for relaxed-only candidates. The latter remains in the legend even though all seven displayed rows are strict. The figure is exported as a 300-DPI PNG and as vector SVG and PDF files, with plot data, validation checks, status, and artifact hashes saved alongside it.
"""

    manifest_rows = [
        save_bundle(
            figure_root=figure_root,
            figure_id="driver_recurrence",
            stem="phase20_broad_driver_recurrence",
            figure=make_driver_evidence_figure(evidence, source),
            plot_rows=evidence,
            plot_fields=EVIDENCE_FIELDS,
            caption=recurrence_caption,
            methods=recurrence_methods,
            scientific_checks=evidence_checks,
            expected_dimensions="2400x2100",
        ),
        save_bundle(
            figure_root=figure_root,
            figure_id="top5_candidates",
            stem="phase20_broad_top5_candidates",
            figure=make_top5_figure(top5, source),
            plot_rows=top5,
            plot_fields=TOP5_FIELDS,
            caption=top5_caption,
            methods=top5_methods,
            scientific_checks=top5_checks,
            expected_dimensions="2700x1350",
        ),
    ]
    manifest_path = figure_root / "phase20_broad_figure_manifest.tsv"
    write_tsv(
        manifest_rows,
        manifest_path,
        [
            "schema_version",
            "figure_id",
            "directory",
            "plot_data_rows",
            "validation_status",
        ],
    )

    if not all(row["validation_status"] == "validated_complete" for row in manifest_rows):
        raise RuntimeError("One or more broad figure bundles failed validation")
    print(f"wrote={figure_root}")
    print(f"figure_bundles={len(manifest_rows)}")
    print("validation_status=validated_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
