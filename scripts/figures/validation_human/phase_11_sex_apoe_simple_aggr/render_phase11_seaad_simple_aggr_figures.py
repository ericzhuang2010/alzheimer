#!/usr/bin/env python3
"""Render non-MT figures from the SEA-AD simple returned-only aggregation.

This renderer mirrors the Phase 20 simple-aggregation figure bundles for the
SEA-AD validation cohort. It does not rerun KDA or ACAT. It reads the
validated category aggregate from ``results/validation_human/
11_sex_apoe_kda_simple_aggr``, confirms every row is a non-core-MT driver,
assigns display ranks within each sex/APOE-by-broad-cell category, and writes
two publication-ready figure bundles: driver recurrence and top-five
candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence


os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "phase11_seaad_simple_aggr_matplotlib"),
)
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patches  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from PIL import Image  # noqa: E402


ROOT = Path(__file__).resolve().parents[4]
SKILL_SCRIPTS = ROOT / ".agents" / "skills" / "scientific-visualization" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from figure_export import save_publication_figure  # noqa: E402
from style_presets import apply_publication_style  # noqa: E402


SOURCE_ANALYSIS_ID = "seaad_simple_returned_only_non_core_mt_acat_v1"
FIGURE_SCHEMA_ROOT = "phase11_seaad_simple_aggr_non_mt_figure_v1"
TRUE_VALUES = {"TRUE", "T", "1", "YES"}
BLUE = "#56B4E9"  # Okabe-Ito sky blue
ORANGE = "#E69F00"  # Okabe-Ito orange
TEXT_COLOR = "#222222"
MUTED_COLOR = "#4B5563"
GRID_COLOR = "#D1D5DB"

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

EXPECTED_INCLUDED_RUNS = 42
EXPECTED_CATEGORY_ROWS = 96
EXPECTED_NON_MT_ROWS = 96
EXPECTED_NON_MT_GENES = 91
EXPECTED_NON_MT_CATEGORIES = 4
EXPECTED_RETURNED_OCCURRENCES = 121
EXPECTED_SINGLETON_UNITS = 80
EXPECTED_RECURRENT_UNITS = 16
EXPECTED_TOP5_ROWS = 18
EXPECTED_MAX_CATEGORY_RECURRENCE = 2
EXPECTED_TOP_RECURRENT_GENE = "HGSNAT"
RECURRENCE_DISPLAY_LIMIT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--figure-root", type=Path)
    return parser.parse_args()


def truth(value: Any) -> bool:
    return str(value).strip().upper() in TRUE_VALUES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        na_values=["NA"],
    )


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, na_rep="NA", lineterminator="\n")


def require_columns(
    frame: pd.DataFrame, required: Iterable[str], label: str
) -> None:
    missing = sorted(set(required) - set(frame.columns))
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


def category_label(group: str, network: str) -> str:
    return f"{group} · {NETWORK_LABELS[network]}"


def add_title(axis: plt.Axes, title: str, subtitle: str) -> None:
    axis.set_title(title, loc="left", pad=28, fontsize=13, fontweight="bold")
    axis.text(
        0,
        1.01,
        subtitle,
        transform=axis.transAxes,
        color=MUTED_COLOR,
        va="bottom",
        fontsize=9,
    )


def configure_style() -> None:
    apply_publication_style("default")
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "phase11_seaad_simple_aggr_non_mt_v1",
            "figure.constrained_layout.use": False,
            "savefig.bbox": None,
        }
    )


def validate_source(result_dir: Path) -> dict[str, Any]:
    paths = {
        "status": result_dir / "simple_status.tsv",
        "checks": result_dir / "simple_checks.tsv",
        "artifacts": result_dir / "simple_artifacts.tsv",
        "categories": result_dir / "simple_category_gene_aggregates.tsv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing simple-aggregation input(s): " + ", ".join(missing))

    status = read_tsv(paths["status"])
    source_checks = read_tsv(paths["checks"])
    artifacts = read_tsv(paths["artifacts"])
    categories = read_tsv(paths["categories"])

    require_columns(
        status,
        [
            "analysis_id",
            "cohort",
            "execution_status",
            "interpretation_status",
            "included_run_count",
            "category_gene_unit_count",
            "failed_check_count",
        ],
        "simple aggregation status",
    )
    if len(status) != 1:
        raise ValueError("simple_status.tsv must contain exactly one row")
    status_row = status.iloc[0]
    if status_row["analysis_id"] != SOURCE_ANALYSIS_ID:
        raise ValueError(f"Unexpected source analysis: {status_row['analysis_id']}")
    if status_row["cohort"] != "SEAAD":
        raise ValueError(f"Unexpected source cohort: {status_row['cohort']}")
    if status_row["execution_status"] != "complete":
        raise ValueError("Simple aggregation is not complete")
    if int(status_row["failed_check_count"]) != 0:
        raise ValueError("Simple aggregation reports failed checks")
    if int(status_row["included_run_count"]) != EXPECTED_INCLUDED_RUNS:
        raise ValueError("Figure renderer requires the frozen 42-call SEA-AD source")

    require_columns(source_checks, ["check_id", "severity", "passed"], "source checks")
    failed_source_checks = source_checks[
        source_checks["severity"].eq("error") & ~source_checks["passed"].map(truth)
    ]
    if not failed_source_checks.empty:
        raise ValueError("Simple aggregation contains failed source checks")

    require_columns(artifacts, ["role", "path", "sha256"], "source artifacts")
    registered = artifacts[artifacts["role"].eq("output_category_aggregates")]
    if len(registered) != 1:
        raise ValueError("Category aggregate must have exactly one artifact registration")
    registered_row = registered.iloc[0]
    if Path(registered_row["path"]).resolve() != paths["categories"].resolve():
        raise ValueError("Registered category-aggregate path does not match the input")
    category_hash = sha256_file(paths["categories"])
    if registered_row["sha256"] != category_hash:
        raise ValueError("Category-aggregate hash does not match its source registry")

    require_columns(
        categories,
        [
            "signature_group",
            "sex",
            "apoe_group",
            "broad_network",
            "current_symbol",
            "case_id",
            "is_core_mito",
            "returned_call_count",
            "returned_fine_cell_type_count",
            "returned_fine_cell_types",
            "minimum_returned_within_call_q",
            "median_returned_within_call_q",
            "maximum_returned_within_call_q",
            "acat_of_returned_within_call_q",
            "returned_run_q_acat_score",
            "requested_final_q",
            "final_value_method",
            "inferential_status",
            "formal_fdr_controlled_q",
            "rank",
        ],
        "category aggregates",
    )
    if len(categories) != int(status_row["category_gene_unit_count"]):
        raise ValueError("Category aggregate row count does not match source status")

    return {
        "paths": paths,
        "status": status,
        "source_checks": source_checks,
        "artifacts": artifacts,
        "categories": categories,
        "category_hash": category_hash,
    }


def derive_non_mt_rows(source: dict[str, Any]) -> pd.DataFrame:
    categories = source["categories"].copy()
    non_mt = categories[
        categories["case_id"].eq("non_mt_driver")
        & ~categories["is_core_mito"].map(truth)
    ].copy()
    if len(non_mt) != len(categories):
        raise ValueError("SEA-AD category aggregate must contain only non-MT rows")

    non_mt["returned_call_count"] = pd.to_numeric(
        non_mt["returned_call_count"], errors="raise"
    ).astype(int)
    non_mt["source_category_rank"] = pd.to_numeric(
        non_mt["rank"], errors="raise"
    ).astype(int)
    non_mt["returned_run_q_acat_score"] = pd.to_numeric(
        non_mt["returned_run_q_acat_score"], errors="raise"
    )
    non_mt["requested_final_q"] = pd.to_numeric(
        non_mt["requested_final_q"], errors="raise"
    )
    if not np.isfinite(non_mt["returned_run_q_acat_score"]).all():
        raise ValueError("Non-finite returned-q ACAT score")
    if not non_mt["returned_run_q_acat_score"].between(0, 1, inclusive="both").all():
        raise ValueError("Returned-q ACAT score outside [0, 1]")
    if not np.allclose(
        non_mt["returned_run_q_acat_score"],
        non_mt["requested_final_q"],
        rtol=0,
        atol=0,
    ):
        raise ValueError("Requested score alias differs from the canonical score")

    non_mt["_group_order"] = non_mt["signature_group"].map(
        {value: index for index, value in enumerate(GROUP_ORDER)}
    )
    non_mt["_network_order"] = non_mt["broad_network"].map(
        {value: index for index, value in enumerate(NETWORK_ORDER)}
    )
    if non_mt[["_group_order", "_network_order"]].isna().any().any():
        raise ValueError("Unexpected signature group or broad network")
    non_mt = non_mt.sort_values(
        [
            "_group_order",
            "_network_order",
            "returned_run_q_acat_score",
            "current_symbol",
        ],
        kind="mergesort",
    ).reset_index(drop=True)
    non_mt["non_mt_rank"] = (
        non_mt.groupby(["signature_group", "broad_network"], sort=False).cumcount()
        + 1
    )
    non_mt["category_label"] = [
        category_label(group, network)
        for group, network in zip(non_mt["signature_group"], non_mt["broad_network"])
    ]
    non_mt["aggregation_display"] = np.where(
        non_mt["returned_call_count"].ge(2),
        "ACAT across ≥2 returned calls",
        "One-call q passthrough",
    )
    non_mt["score_neg_log10"] = -np.log10(
        np.maximum(non_mt["returned_run_q_acat_score"].to_numpy(float), 1e-300)
    )
    non_mt["source_analysis_id"] = SOURCE_ANALYSIS_ID
    non_mt["source_category_aggregate_sha256"] = source["category_hash"]
    return non_mt


def derive_top5(non_mt: pd.DataFrame) -> pd.DataFrame:
    top5 = non_mt[non_mt["non_mt_rank"].le(5)].copy()
    top5["schema_version"] = f"{FIGURE_SCHEMA_ROOT}_top5_plot_data_v1"
    fields = [
        "schema_version",
        "signature_group",
        "sex",
        "apoe_group",
        "broad_network",
        "category_label",
        "current_symbol",
        "case_id",
        "is_core_mito",
        "source_category_rank",
        "non_mt_rank",
        "returned_call_count",
        "returned_fine_cell_type_count",
        "returned_fine_cell_types",
        "minimum_returned_within_call_q",
        "median_returned_within_call_q",
        "maximum_returned_within_call_q",
        "acat_of_returned_within_call_q",
        "returned_run_q_acat_score",
        "requested_final_q",
        "score_neg_log10",
        "final_value_method",
        "aggregation_display",
        "inferential_status",
        "formal_fdr_controlled_q",
        "source_analysis_id",
        "source_category_aggregate_sha256",
    ]
    return top5[fields].reset_index(drop=True)


def derive_recurrence(non_mt: pd.DataFrame) -> pd.DataFrame:
    work = non_mt.copy()
    work["acat_combined_category"] = work["returned_call_count"].ge(2).astype(int)
    work["singleton_category"] = work["returned_call_count"].eq(1).astype(int)
    recurrence = (
        work.groupby("current_symbol", as_index=False)
        .agg(
            category_count=("current_symbol", "size"),
            sex_apoe_group_count=("signature_group", "nunique"),
            broad_network_count=("broad_network", "nunique"),
            total_returned_call_count=("returned_call_count", "sum"),
            acat_combined_category_count=("acat_combined_category", "sum"),
            singleton_category_count=("singleton_category", "sum"),
            best_returned_run_q_acat_score=("returned_run_q_acat_score", "min"),
            median_returned_run_q_acat_score=("returned_run_q_acat_score", "median"),
        )
        .sort_values(
            [
                "category_count",
                "best_returned_run_q_acat_score",
                "current_symbol",
            ],
            ascending=[False, True, True],
            kind="mergesort",
        )
        .head(RECURRENCE_DISPLAY_LIMIT)
        .reset_index(drop=True)
    )
    recurrence.insert(0, "display_rank", np.arange(1, len(recurrence) + 1))
    recurrence.insert(0, "case_id", "non_mt_driver")
    recurrence.insert(0, "schema_version", f"{FIGURE_SCHEMA_ROOT}_recurrence_plot_data_v1")
    recurrence["source_analysis_id"] = SOURCE_ANALYSIS_ID
    recurrence["source_category_aggregate_sha256"] = source_hash_from_rows(non_mt)
    return recurrence


def source_hash_from_rows(non_mt: pd.DataFrame) -> str:
    values = non_mt["source_category_aggregate_sha256"].drop_duplicates().tolist()
    if len(values) != 1:
        raise ValueError("Expected one source category-aggregate hash")
    return str(values[0])


def plot_recurrence(recurrence: pd.DataFrame) -> plt.Figure:
    ordered = recurrence.iloc[::-1].reset_index(drop=True)
    maximum = max(1, int(ordered["acat_combined_category_count"].max()))
    norm = Normalize(vmin=0, vmax=maximum)
    cmap = matplotlib.colormaps["cividis"]
    colors = [cmap(norm(value)) for value in ordered["acat_combined_category_count"]]
    figure, axis = plt.subplots(figsize=(8, 7))
    bars = axis.barh(ordered["current_symbol"], ordered["category_count"], color=colors)
    for bar, value in zip(bars, ordered["category_count"]):
        axis.text(
            bar.get_width() + 0.04,
            bar.get_y() + bar.get_height() / 2,
            str(int(value)),
            va="center",
            fontsize=8,
            color=TEXT_COLOR,
        )
    axis.set_xlim(0, float(ordered["category_count"].max()) + 0.75)
    axis.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    axis.set_xlabel("Number of non-MT key-driver categories")
    axis.set_ylabel("")
    add_title(
        axis,
        "Most recurrent SEA-AD simple-aggregation non-MT key drivers",
        "Each gene is counted once per sex/APOE × broad-cell category; 4 SEA-AD categories have returns",
    )
    scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = figure.colorbar(scalar, ax=axis, pad=0.02)
    colorbar.set_label("Categories aggregated across ≥2 returned calls")
    colorbar.locator = matplotlib.ticker.MaxNLocator(integer=True)
    colorbar.update_ticks()
    figure.subplots_adjust(left=0.20, right=0.88, top=0.84, bottom=0.11)
    return figure


def draw_top5_panel(
    axis: plt.Axes, rows: pd.DataFrame, sex: str, panel: str, max_rows: int
) -> None:
    categories = rows["category_label"].drop_duplicates().tolist()
    y_index = {value: index for index, value in enumerate(categories)}
    for row in rows.itertuples():
        x = int(row.non_mt_rank) - 1
        y = y_index[row.category_label]
        recurrent = int(row.returned_call_count) >= 2
        rectangle = patches.Rectangle(
            (x - 0.48, y - 0.42),
            0.96,
            0.84,
            facecolor=BLUE if recurrent else ORANGE,
            edgecolor="white",
            linewidth=0.8,
        )
        axis.add_patch(rectangle)
        axis.text(x, y, row.current_symbol, ha="center", va="center", fontsize=7.2)

    axis.set_xlim(-0.5, 4.5)
    axis.set_ylim(max_rows - 0.5, -0.5)
    axis.set_xticks(range(5), range(1, 6))
    axis.set_yticks(range(len(categories)), categories)
    axis.set_xlabel("Non-MT within-category rank")
    axis.set_ylabel("Sex/APOE · broad cell type" if panel == "A" else "")
    axis.set_title(f"{panel}  {sex}", loc="left", fontsize=10, fontweight="bold", pad=8)
    axis.tick_params(axis="y", labelsize=7.5)
    axis.grid(False)
    for y in np.arange(0.5, max_rows - 0.5, 1):
        axis.axhline(y, color=GRID_COLOR, linewidth=0.35, zorder=0)


def plot_top5(top5: pd.DataFrame) -> plt.Figure:
    female = top5[top5["sex"].eq("Female")]
    male = top5[top5["sex"].eq("Male")]
    maximum_rows = max(
        female["category_label"].nunique(), male["category_label"].nunique()
    )
    height = max(4.4, 0.72 * maximum_rows + 2.9)
    figure, axes = plt.subplots(1, 2, figsize=(13, height))
    draw_top5_panel(axes[0], female, "Female", "A", maximum_rows)
    draw_top5_panel(axes[1], male, "Male", "B", maximum_rows)
    figure.suptitle(
        "Top five SEA-AD simple-aggregation non-MT key drivers",
        x=0.06,
        y=0.965,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.06,
        0.905,
        "Ranked after excluding core-MT genes; categories without a non-MT return are omitted",
        ha="left",
        color=MUTED_COLOR,
        fontsize=9,
    )
    handles = [
        patches.Patch(facecolor=BLUE, edgecolor="white", label="ACAT: ≥2 returned calls"),
        patches.Patch(
            facecolor=ORANGE,
            edgecolor="white",
            label="One-call q passthrough",
        ),
    ]
    figure.legend(
        handles=handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=2,
        fontsize=8,
    )
    figure.subplots_adjust(left=0.16, right=0.985, top=0.82, bottom=0.19, wspace=0.38)
    return figure


def png_metadata(path: Path) -> tuple[str, str, bool]:
    with Image.open(path) as image:
        dimensions = f"{image.width}x{image.height}"
        dpi = image.info.get("dpi", (0.0, 0.0))
        dpi_text = f"{dpi[0]:.1f}x{dpi[1]:.1f}"
        dpi_ok = abs(dpi[0] - 300) <= 1 and abs(dpi[1] - 300) <= 1
    return dimensions, dpi_text, dpi_ok


def bundle_file_checks(paths: dict[str, Path], expected_dimensions: str) -> list[dict[str, Any]]:
    core = ["png", "svg", "pdf", "data", "caption", "methods"]
    dimensions, dpi_text, dpi_ok = png_metadata(paths["png"])
    pdf_ok = paths["pdf"].read_bytes()[:4] == b"%PDF"
    svg_head = paths["svg"].read_text(encoding="utf-8", errors="replace")[:2000]
    svg_ok = "<svg" in svg_head
    return [
        check(
            "core_artifacts_exist",
            sum(paths[name].is_file() for name in core),
            len(core),
            all(paths[name].is_file() for name in core),
        ),
        check(
            "core_artifacts_nonempty",
            sum(paths[name].is_file() and paths[name].stat().st_size > 0 for name in core),
            len(core),
            all(paths[name].is_file() and paths[name].stat().st_size > 0 for name in core),
        ),
        check("png_dimensions", dimensions, expected_dimensions, dimensions == expected_dimensions),
        check("png_resolution_dpi", dpi_text, "300x300 (±1)", dpi_ok),
        check("pdf_signature", "%PDF" if pdf_ok else "invalid", "%PDF", pdf_ok),
        check("svg_root", "<svg" if svg_ok else "missing", "<svg", svg_ok),
    ]


def common_checks(source: dict[str, Any], non_mt: pd.DataFrame) -> list[dict[str, Any]]:
    keys = list(
        zip(non_mt["signature_group"], non_mt["broad_network"], non_mt["current_symbol"])
    )
    category_counts = non_mt.groupby(["signature_group", "broad_network"]).size()
    ranks_contiguous = all(
        sorted(group["non_mt_rank"].astype(int).tolist()) == list(range(1, len(group) + 1))
        for _, group in non_mt.groupby(["signature_group", "broad_network"], sort=False)
    )
    rank_parity = non_mt["non_mt_rank"].astype(int).equals(
        non_mt["source_category_rank"].astype(int)
    )
    return [
        check("source_execution_status", source["status"].iloc[0]["execution_status"], "complete", True),
        check("source_failed_checks", 0, 0, True),
        check("source_category_hash", source["category_hash"], source["category_hash"], True),
        check("all_class_category_rows", len(source["categories"]), EXPECTED_CATEGORY_ROWS, len(source["categories"]) == EXPECTED_CATEGORY_ROWS),
        check("non_mt_category_rows", len(non_mt), EXPECTED_NON_MT_ROWS, len(non_mt) == EXPECTED_NON_MT_ROWS),
        check("non_mt_unique_genes", non_mt["current_symbol"].nunique(), EXPECTED_NON_MT_GENES, non_mt["current_symbol"].nunique() == EXPECTED_NON_MT_GENES),
        check("categories_with_non_mt", len(category_counts), EXPECTED_NON_MT_CATEGORIES, len(category_counts) == EXPECTED_NON_MT_CATEGORIES),
        check("non_mt_scope", int(non_mt["is_core_mito"].map(truth).sum()), 0, not non_mt["is_core_mito"].map(truth).any()),
        check("non_mt_case_id", int(non_mt["case_id"].ne("non_mt_driver").sum()), 0, non_mt["case_id"].eq("non_mt_driver").all()),
        check("category_gene_keys_unique", len(set(keys)), EXPECTED_NON_MT_ROWS, len(set(keys)) == len(non_mt)),
        check("returned_call_occurrences", int(non_mt["returned_call_count"].sum()), EXPECTED_RETURNED_OCCURRENCES, int(non_mt["returned_call_count"].sum()) == EXPECTED_RETURNED_OCCURRENCES),
        check("singleton_category_units", int(non_mt["returned_call_count"].eq(1).sum()), EXPECTED_SINGLETON_UNITS, int(non_mt["returned_call_count"].eq(1).sum()) == EXPECTED_SINGLETON_UNITS),
        check("recurrent_category_units", int(non_mt["returned_call_count"].ge(2).sum()), EXPECTED_RECURRENT_UNITS, int(non_mt["returned_call_count"].ge(2).sum()) == EXPECTED_RECURRENT_UNITS),
        check("non_mt_ranks_contiguous", "TRUE" if ranks_contiguous else "FALSE", "TRUE", ranks_contiguous),
        check("display_rank_matches_source_rank", "TRUE" if rank_parity else "FALSE", "TRUE", rank_parity),
        check("formal_fdr_flags", int(non_mt["formal_fdr_controlled_q"].map(truth).sum()), 0, not non_mt["formal_fdr_controlled_q"].map(truth).any()),
    ]


def recurrence_checks(
    source: dict[str, Any], non_mt: pd.DataFrame, recurrence: pd.DataFrame
) -> list[dict[str, Any]]:
    expected = derive_recurrence(non_mt)
    parity = recurrence.equals(expected)
    return common_checks(source, non_mt) + [
        check("recurrence_plot_rows", len(recurrence), RECURRENCE_DISPLAY_LIMIT, len(recurrence) == RECURRENCE_DISPLAY_LIMIT),
        check("recurrence_genes_unique", recurrence["current_symbol"].nunique(), RECURRENCE_DISPLAY_LIMIT, recurrence["current_symbol"].nunique() == RECURRENCE_DISPLAY_LIMIT),
        check("recurrence_source_parity", "TRUE" if parity else "FALSE", "TRUE", parity),
        check("maximum_category_recurrence", int(recurrence["category_count"].max()), EXPECTED_MAX_CATEGORY_RECURRENCE, int(recurrence["category_count"].max()) == EXPECTED_MAX_CATEGORY_RECURRENCE),
        check("top_recurrent_gene", recurrence.iloc[0]["current_symbol"], EXPECTED_TOP_RECURRENT_GENE, recurrence.iloc[0]["current_symbol"] == EXPECTED_TOP_RECURRENT_GENE),
    ]


def top5_checks(
    source: dict[str, Any], non_mt: pd.DataFrame, top5: pd.DataFrame
) -> list[dict[str, Any]]:
    expected_keys = set(
        zip(
            non_mt.loc[non_mt["non_mt_rank"].le(5), "signature_group"],
            non_mt.loc[non_mt["non_mt_rank"].le(5), "broad_network"],
            non_mt.loc[non_mt["non_mt_rank"].le(5), "current_symbol"],
        )
    )
    observed_keys = set(zip(top5["signature_group"], top5["broad_network"], top5["current_symbol"]))
    per_category = top5.groupby(["signature_group", "broad_network"]).size()
    return common_checks(source, non_mt) + [
        check("top5_plot_rows", len(top5), EXPECTED_TOP5_ROWS, len(top5) == EXPECTED_TOP5_ROWS),
        check("top5_category_count", len(per_category), EXPECTED_NON_MT_CATEGORIES, len(per_category) == EXPECTED_NON_MT_CATEGORIES),
        check("top5_maximum_per_category", int(per_category.max()), 5, int(per_category.max()) == 5),
        check("top5_rank_bounds", f"{int(top5['non_mt_rank'].min())}-{int(top5['non_mt_rank'].max())}", "1-5", top5["non_mt_rank"].between(1, 5).all()),
        check("top5_source_key_parity", len(observed_keys & expected_keys), len(expected_keys), observed_keys == expected_keys),
        check("top5_keys_unique", len(observed_keys), len(top5), len(observed_keys) == len(top5)),
    ]


def normalize_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(
        "\n".join(line.rstrip() for line in text.splitlines()) + "\n",
        encoding="utf-8",
    )


def save_bundle(
    *,
    figure_root: Path,
    figure_id: str,
    figure: plt.Figure,
    plot_data: pd.DataFrame,
    caption: str,
    methods: str,
    scientific_checks: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    bundle = figure_root / figure_id
    bundle.mkdir(parents=True, exist_ok=True)
    stem = f"phase11_seaad_simple_aggr_{figure_id}"
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

    write_tsv(plot_data, paths["data"])
    paths["caption"].write_text(caption.rstrip() + "\n", encoding="utf-8")
    paths["methods"].write_text(methods.rstrip() + "\n", encoding="utf-8")
    width, height = figure.get_size_inches()
    expected_dimensions = f"{int(width * 300)}x{int(height * 300)}"
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
    normalize_svg(paths["svg"])

    checks = list(scientific_checks)
    checks.extend(bundle_file_checks(paths, expected_dimensions))
    checks_frame = pd.DataFrame(checks)
    write_tsv(checks_frame, paths["checks"])
    failed = int((~checks_frame["passed"].astype(bool)).sum())
    validation_status = "validated_complete" if failed == 0 else "validation_failed"
    status = pd.DataFrame(
        [
            {
                "schema_version": f"{FIGURE_SCHEMA_ROOT}_status_v1",
                "figure_id": figure_id,
                "scope": "non_mt_driver",
                "source_analysis_id": SOURCE_ANALYSIS_ID,
                "plot_data_rows": len(plot_data),
                "failed_checks": failed,
                "validation_status": validation_status,
            }
        ]
    )
    write_tsv(status, paths["status"])

    artifact_rows: list[dict[str, Any]] = []
    registered = ["png", "svg", "pdf", "data", "caption", "methods", "checks", "status"]
    for order, name in enumerate(registered, start=1):
        path = paths[name]
        artifact_rows.append(
            {
                "schema_version": f"{FIGURE_SCHEMA_ROOT}_artifacts_v1",
                "artifact_order": order,
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    write_tsv(pd.DataFrame(artifact_rows), paths["artifacts"])

    expected_inventory = {path.name for path in paths.values()}
    observed_inventory = {path.name for path in bundle.iterdir() if path.is_file()}
    if observed_inventory != expected_inventory:
        raise RuntimeError(
            f"Unexpected inventory for {figure_id}: "
            f"expected={sorted(expected_inventory)}, observed={sorted(observed_inventory)}"
        )
    if failed:
        failed_ids = checks_frame.loc[~checks_frame["passed"].astype(bool), "check_id"].tolist()
        raise RuntimeError(f"{figure_id} failed checks: {', '.join(failed_ids)}")

    return {
        "schema_version": f"{FIGURE_SCHEMA_ROOT}_manifest_v1",
        "figure_id": figure_id,
        "directory": str(bundle),
        "plot_data_rows": len(plot_data),
        "validation_status": validation_status,
    }


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    result_dir = (
        args.result_dir.resolve()
        if args.result_dir
        else root / "results" / "validation_human" / "11_sex_apoe_kda_simple_aggr"
    )
    figure_root = (
        args.figure_root.resolve()
        if args.figure_root
        else root
        / "results"
        / "figures"
        / "validation_human"
        / "phase_11_sex_apoe_simple_aggr"
    )
    figure_root.mkdir(parents=True, exist_ok=True)

    configure_style()
    source = validate_source(result_dir)
    non_mt = derive_non_mt_rows(source)
    recurrence = derive_recurrence(non_mt)
    top5 = derive_top5(non_mt)

    common_methods = """The renderer reads the validated `simple_category_gene_aggregates.tsv` table from `results/validation_human/11_sex_apoe_kda_simple_aggr` and verifies its registered SHA-256 hash, source completion status, and source checks. The source already excludes core-MitoCarta drivers, so every row is a `case_id = non_mt_driver`, `is_core_mito = FALSE` unit; the renderer re-verifies this scope. No KDA or ACAT calculation is rerun. Rows are ordered within each `signature_group × broad_network` category by `returned_run_q_acat_score`, then gene symbol, and the resulting display rank is confirmed to match the stored source rank.

The score is the requested exploratory returned-only value from the 42 active SEA-AD KDA calls: a singleton stock within-call BH q is passed through unchanged, whereas two or more returned q values are combined by equal-weight ACAT. It is post-selected and is not a formally FDR-controlled cross-call q value; the figures are descriptive rankings of stock-significant returns. Only 4 of the 42 structural sex/APOE-by-broad-cell categories have non-MT returns, and 40 of the 42 active calls sit in M_e33, so category breadth is bounded by the unbalanced call distribution."""

    recurrence_caption = """# SEA-AD simple-aggregation driver recurrence

The 20 most recurrent SEA-AD non-MT key drivers across sex/APOE-by-broad-cell categories. Bar length is the number of categories containing the gene; only 4 SEA-AD categories have non-MT returns, so the maximum possible recurrence is small. Fill records how many of those category occurrences combine two or more significant call returns by ACAT; the remainder are one-call q passthroughs."""
    recurrence_methods = f"""# Methods

{common_methods}

For recurrence, each gene is counted at most once in each category. Genes are ordered by category count (descending), best returned-q ACAT score (ascending), and symbol; the first 20 are displayed. Five genes appear in two categories; the remaining displayed genes appear in one and are ordered by their best exploratory score."""

    top5_caption = """# SEA-AD simple-aggregation top-five candidates

Up to five SEA-AD non-MT key drivers per sex/APOE-by-broad-cell category, split into female and male panels. Blue tiles represent scores ACAT-combined across at least two significant call returns; orange tiles represent a single within-call q passthrough. Categories without any non-MT return are omitted, which leaves one female category (F_e33 · Excitatory neurons, three genes) and three male categories (all M_e33)."""
    top5_methods = f"""# Methods

{common_methods}

For the top-five display, ranks 1–5 within each return-bearing category are retained without backfilling or an additional significance threshold. This leaves 18 plotted gene-category rows across 4 categories; the F_e33 excitatory category contributes only its three returned genes. The word “candidates” names the requested display and does not imply a new confirmatory error-rate claim."""

    manifest_rows = [
        save_bundle(
            figure_root=figure_root,
            figure_id="driver_recurrence",
            figure=plot_recurrence(recurrence),
            plot_data=recurrence,
            caption=recurrence_caption,
            methods=recurrence_methods,
            scientific_checks=recurrence_checks(source, non_mt, recurrence),
        ),
        save_bundle(
            figure_root=figure_root,
            figure_id="top5_candidates",
            figure=plot_top5(top5),
            plot_data=top5,
            caption=top5_caption,
            methods=top5_methods,
            scientific_checks=top5_checks(source, non_mt, top5),
        ),
    ]
    manifest_path = figure_root / "phase11_seaad_simple_aggr_figure_manifest.tsv"
    write_tsv(pd.DataFrame(manifest_rows), manifest_path)
    print(f"wrote={figure_root}")
    print(f"figure_bundles={len(manifest_rows)}")
    print(f"non_mt_category_gene_rows={len(non_mt)}")
    print(f"categories_with_non_mt={non_mt.groupby(['signature_group', 'broad_network']).ngroups}")
    print(f"top5_plot_rows={len(top5)}")
    print("validation_status=validated_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
