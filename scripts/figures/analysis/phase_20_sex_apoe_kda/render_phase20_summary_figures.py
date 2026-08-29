#!/usr/bin/env python3
"""Render validated Phase 20 fine-cell summary figures with matplotlib.

DEPRECATED (2026-08-29): these figures visualize the deprecated
coverage/support candidate selection
(``results/minerva_production/20_sex_apoe_kda (deprecated)``); the figure
bundles were renamed to
``results/figures/analysis/phase_20_sex_apoe_kda (deprecated)``. The
authoritative figures are rendered by
``scripts/figures/analysis/phase_20_sex_apoe_simple_aggr/
render_phase20_simple_aggr_figures.py`` from the returned-only simple
aggregation. Retained for provenance only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "phase20_matplotlib")
)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.colors import Normalize


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
SCHEMA_ROOT = "phase20_sex_apoe_non_mt_figure_v2"
GROUPS = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
NETWORKS = [
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
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9"]


def truth(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_values=["NA"])


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep="\t", index=False, na_rep="NA", lineterminator="\n")


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def validate_inputs(result_dir: Path) -> dict[str, Path]:
    paths = {
        "status": result_dir / "phase20_status.tsv",
        "checks": result_dir / "phase20_checks.tsv",
        "artifacts": result_dir / "phase20_artifacts.tsv",
        "manifest": result_dir / "phase20_category_manifest.tsv",
        "candidates": result_dir / "phase20_relaxed_candidates.tsv",
        "top5": result_dir / "phase20_top5_summary.tsv",
        "stability": result_dir / "phase20_stability_summary.tsv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Phase 20 inputs: " + ", ".join(missing))
    status = read_tsv(paths["status"])
    if len(status) != 1 or status.iloc[0]["validation_status"] != "validated_complete":
        raise ValueError("Phase 20 production status is not validated_complete")
    if int(status.iloc[0]["included_runs"]) != 295:
        raise ValueError("Figure renderer requires the 295-run minimum-query-3 release")
    checks = read_tsv(paths["checks"])
    failed = checks[
        checks["severity"].eq("error") & ~checks["passed"].map(truth)
    ]
    if not failed.empty:
        raise ValueError("Phase 20 production has failed checks")
    artifacts = read_tsv(paths["artifacts"])
    registered = artifacts.set_index("path")
    for role in ("manifest", "candidates", "top5", "stability"):
        path = paths[role]
        if path.name not in registered.index:
            raise ValueError(f"Unregistered figure input: {path.name}")
        if registered.loc[path.name, "sha256"] != sha256_file(path):
            raise ValueError(f"Figure-input hash mismatch: {path.name}")
    return paths


def save_bundle(
    figure_root: Path,
    figure_id: str,
    fig: mpl.figure.Figure,
    data: pd.DataFrame,
    caption: str,
    methods: str,
) -> dict[str, Any]:
    bundle = figure_root / figure_id
    bundle.mkdir(parents=True, exist_ok=True)
    stem = f"phase20_{figure_id}"
    paths = {
        "png": bundle / f"{stem}.png",
        "svg": bundle / f"{stem}.svg",
        "pdf": bundle / f"{stem}.pdf",
        "data": bundle / f"{stem}_plot_data.tsv",
        "caption": bundle / f"{stem}_caption.md",
        "methods": bundle / f"{stem}_methods.md",
    }
    write_tsv(data, paths["data"])
    fig.savefig(paths["png"], dpi=300, bbox_inches="tight")
    fig.savefig(paths["svg"], bbox_inches="tight")
    # Matplotlib pads some SVG element lines with spaces.  Normalize those
    # lines before registering hashes so generated text artifacts remain
    # friendly to repository whitespace checks.
    svg_text = paths["svg"].read_text(encoding="utf-8")
    normalized_svg = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
    paths["svg"].write_text(normalized_svg, encoding="utf-8")
    fig.savefig(paths["pdf"], bbox_inches="tight")
    plt.close(fig)
    paths["caption"].write_text(caption.rstrip() + "\n")
    paths["methods"].write_text(methods.rstrip() + "\n")
    checks_path = bundle / f"{stem}_checks.tsv"
    checks = pd.DataFrame(
        [
            {
                "schema_version": f"{SCHEMA_ROOT}_checks_v1",
                "check_id": "plot_data_nonempty",
                "severity": "error",
                "observed": len(data),
                "expected": ">0",
                "passed": len(data) > 0,
            },
            {
                "schema_version": f"{SCHEMA_ROOT}_checks_v1",
                "check_id": "all_declared_files_exist",
                "severity": "error",
                "observed": sum(path.is_file() for path in paths.values()),
                "expected": len(paths),
                "passed": all(path.is_file() for path in paths.values()),
            },
            {
                "schema_version": f"{SCHEMA_ROOT}_checks_v1",
                "check_id": "non_mt_scope",
                "severity": "error",
                "observed": "non_mt_driver",
                "expected": "non_mt_driver",
                "passed": True,
            },
        ]
    )
    write_tsv(checks, checks_path)
    status_path = bundle / f"{stem}_status.tsv"
    status = pd.DataFrame(
        [
            {
                "schema_version": f"{SCHEMA_ROOT}_status_v1",
                "figure_id": figure_id,
                "plot_data_rows": len(data),
                "failed_checks": int((~checks["passed"]).sum()),
                "validation_status": "validated_complete",
            }
        ]
    )
    write_tsv(status, status_path)
    registered = [*paths.values(), checks_path, status_path]
    artifact_rows = []
    for order, path in enumerate(registered, start=1):
        artifact_rows.append(
            {
                "schema_version": f"{SCHEMA_ROOT}_artifacts_v1",
                "artifact_order": order,
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    write_tsv(
        pd.DataFrame(artifact_rows), bundle / f"{stem}_artifacts.tsv"
    )
    return {
        "schema_version": f"{SCHEMA_ROOT}_manifest_v1",
        "figure_id": figure_id,
        "directory": str(bundle),
        "plot_data_rows": len(data),
        "validation_status": "validated_complete",
    }


def category_label(group: str, network: str) -> str:
    return f"{group} · {NETWORK_LABELS[network]}"


def add_title(ax: mpl.axes.Axes, title: str, subtitle: str) -> None:
    ax.set_title(title, loc="left", pad=28)
    ax.text(
        0,
        1.01,
        subtitle,
        transform=ax.transAxes,
        color="#4b5563",
        va="bottom",
        fontsize=9,
    )


def plot_coverage(manifest: pd.DataFrame) -> mpl.figure.Figure:
    matrix = np.zeros((len(GROUPS), len(NETWORKS)))
    fine = np.zeros_like(matrix)
    lookup = manifest.set_index(["signature_group", "broad_network"])
    for i, group in enumerate(GROUPS):
        for j, network in enumerate(NETWORKS):
            row = lookup.loc[(group, network)]
            matrix[i, j] = int(row["included_run_count"])
            fine[i, j] = int(row["fine_cell_type_count"])
    fig, ax = plt.subplots(figsize=(12, 5.5))
    image = ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            color = "white" if matrix[i, j] >= 15 else "#1f2937"
            ax.text(
                j,
                i,
                f"{int(matrix[i, j])}\n{int(fine[i, j])} fine",
                ha="center",
                va="center",
                fontsize=8,
                color=color,
            )
    ax.set_xticks(range(len(NETWORKS)), [NETWORK_LABELS[x] for x in NETWORKS], rotation=35, ha="right")
    ax.set_yticks(range(len(GROUPS)), GROUPS)
    ax.set_xlabel("")
    ax.set_ylabel("Sex/APOE group")
    add_title(
        ax,
        "KDA run coverage for the 42 Phase 20 categories",
        "Effective query ≥3; each cell gives included runs and distinct fine cell types",
    )
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Included runs")
    fig.tight_layout()
    return fig


def candidate_axes(candidates: pd.DataFrame) -> tuple[list[str], list[str]]:
    present = {
        (row.signature_group, row.broad_network)
        for row in candidates.itertuples()
    }
    categories = [
        category_label(group, network)
        for group in GROUPS
        for network in NETWORKS
        if (group, network) in present
    ]
    recurrence = candidates.groupby("current_symbol").size()
    best_q = candidates.groupby("current_symbol")["relaxed_category_acat_q"].min()
    genes = sorted(
        recurrence.index,
        key=lambda gene: (-int(recurrence[gene]), float(best_q[gene]), gene),
    )
    return categories, genes


def plot_evidence(candidates: pd.DataFrame) -> mpl.figure.Figure:
    categories, genes = candidate_axes(candidates)
    x_index = {value: index for index, value in enumerate(categories)}
    y_index = {value: index for index, value in enumerate(genes)}
    values = np.full((len(genes), len(categories)), np.nan)
    strict: list[tuple[int, int]] = []
    for row in candidates.itertuples():
        x = x_index[category_label(row.signature_group, row.broad_network)]
        y = y_index[row.current_symbol]
        values[y, x] = -np.log10(max(float(row.relaxed_category_acat_q), 1e-300))
        if truth(row.strict_non_mt_reference):
            strict.append((x, y))
    fig, ax = plt.subplots(figsize=(17, max(8, 0.24 * len(genes) + 2.5)))
    masked = np.ma.masked_invalid(values)
    image = ax.imshow(masked, cmap="cividis", aspect="auto", interpolation="none")
    if strict:
        ax.scatter(
            [x for x, _ in strict],
            [y for _, y in strict],
            facecolors="none",
            edgecolors="white",
            linewidths=1.1,
            s=28,
        )
    ax.set_xticks(range(len(categories)), categories, rotation=45, ha="right")
    ax.set_yticks(range(len(genes)), genes)
    ax.set_xlabel("Sex/APOE · broad cell type")
    ax.set_ylabel("Non-MT driver")
    add_title(
        ax,
        "Relaxed non-MT key-driver evidence by category",
        "White circles also pass the strict non-MT reference",
    )
    colorbar = fig.colorbar(image, ax=ax, pad=0.01)
    colorbar.set_label("−log10(category q)")
    fig.tight_layout()
    return fig


def plot_top5(top5: pd.DataFrame) -> tuple[mpl.figure.Figure, pd.DataFrame]:
    ranked = top5[
        top5["list_status"].eq("ranked_candidates")
        & top5["current_symbol"].notna()
    ].copy()
    present = {
        (row.signature_group, row.broad_network) for row in ranked.itertuples()
    }
    categories = [
        category_label(group, network)
        for group in GROUPS
        for network in NETWORKS
        if (group, network) in present
    ]
    y_index = {value: index for index, value in enumerate(categories)}
    fig, ax = plt.subplots(figsize=(12, max(7, 0.42 * len(categories) + 2.5)))
    for row in ranked.itertuples():
        x = int(float(row.relaxed_rank)) - 1
        y = y_index[category_label(row.signature_group, row.broad_network)]
        strict = truth(row.strict_non_mt_reference)
        rect = patches.Rectangle(
            (x - 0.48, y - 0.42),
            0.96,
            0.84,
            facecolor="#56B4E9" if strict else "#E69F00",
            edgecolor="white",
            linewidth=1,
        )
        ax.add_patch(rect)
        ax.text(x, y, row.current_symbol, ha="center", va="center", fontsize=8)
    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(len(categories) - 0.5, -0.5)
    ax.set_xticks(range(5), range(1, 6))
    ax.set_yticks(range(len(categories)), categories)
    ax.set_xlabel("Within-category rank")
    ax.set_ylabel("Sex/APOE · broad cell type")
    add_title(
        ax,
        "Top five relaxed non-MT key drivers",
        "Only candidate-containing categories are shown; no list is backfilled",
    )
    handles = [
        patches.Patch(color="#56B4E9", label="Strict reference"),
        patches.Patch(color="#E69F00", label="Relaxed only"),
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right")
    fig.tight_layout()
    return fig, ranked


def recurrence_data(candidates: pd.DataFrame) -> pd.DataFrame:
    work = candidates.copy()
    work["strict_flag"] = work["strict_non_mt_reference"].map(truth).astype(int)
    grouped = (
        work.groupby("current_symbol", as_index=False)
        .agg(
            category_count=("current_symbol", "size"),
            group_count=("signature_group", "nunique"),
            broad_network_count=("broad_network", "nunique"),
            strict_category_count=("strict_flag", "sum"),
            best_relaxed_q=("relaxed_category_acat_q", "min"),
        )
        .sort_values(
            ["category_count", "best_relaxed_q", "current_symbol"],
            ascending=[False, True, True],
        )
        .head(20)
        .reset_index(drop=True)
    )
    return grouped


def plot_recurrence(recurrence: pd.DataFrame) -> mpl.figure.Figure:
    ordered = recurrence.iloc[::-1].reset_index(drop=True)
    norm = Normalize(
        vmin=float(ordered["strict_category_count"].min()),
        vmax=max(
            float(ordered["strict_category_count"].max()),
            float(ordered["strict_category_count"].min()) + 1,
        ),
    )
    cmap = mpl.colormaps["cividis"]
    colors = [cmap(norm(value)) for value in ordered["strict_category_count"]]
    fig, ax = plt.subplots(figsize=(8, 7))
    bars = ax.barh(
        ordered["current_symbol"], ordered["category_count"], color=colors
    )
    for bar, value in zip(bars, ordered["category_count"]):
        ax.text(
            bar.get_width() + 0.08,
            bar.get_y() + bar.get_height() / 2,
            str(int(value)),
            va="center",
            fontsize=8,
        )
    ax.set_xlim(0, float(ordered["category_count"].max()) + 1.3)
    ax.set_xlabel("Number of candidate-containing categories")
    ax.set_ylabel("")
    add_title(
        ax,
        "Most recurrent relaxed non-MT key drivers",
        "Each gene is counted once per Phase 20 category",
    )
    scalar = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, ax=ax, pad=0.02)
    colorbar.set_label("Strict-reference categories")
    fig.tight_layout()
    return fig


def plot_stability(stability: pd.DataFrame) -> tuple[mpl.figure.Figure, pd.DataFrame]:
    stable = stability[stability["candidate_retention_fraction"].notna()].copy()
    stable["candidate_retention_fraction"] = pd.to_numeric(
        stable["candidate_retention_fraction"]
    )
    stable["assessable_repetitions"] = pd.to_numeric(
        stable["assessable_repetitions"]
    )
    genes = sorted(
        stable["current_symbol"].unique(),
        key=lambda gene: (
            stable.loc[
                stable["current_symbol"].eq(gene), "candidate_retention_fraction"
            ].min(),
            gene,
        ),
    )
    y_index = {gene: index for index, gene in enumerate(genes)}
    labels = sorted(stable["evidence_label"].dropna().unique())
    colors = {label: OKABE_ITO[index % len(OKABE_ITO)] for index, label in enumerate(labels)}
    fig, ax = plt.subplots(figsize=(10, max(8, 0.24 * len(genes) + 2.5)))
    for label in labels:
        subset = stable[stable["evidence_label"].eq(label)]
        ax.scatter(
            subset["candidate_retention_fraction"],
            [y_index[gene] for gene in subset["current_symbol"]],
            s=18 + 5 * subset["assessable_repetitions"],
            alpha=0.78,
            color=colors[label],
            edgecolor="white",
            linewidth=0.35,
            label=label.replace("_", " "),
        )
    ax.axvline(0.8, linestyle="--", color="#6b7280", linewidth=1)
    ax.set_xlim(-0.03, 1.03)
    ax.set_yticks(range(len(genes)), genes)
    ax.set_xlabel("Candidate-retention fraction")
    ax.set_ylabel("Non-MT driver")
    add_title(
        ax,
        "Leave-one-fine-cell-type-out candidate retention",
        "Only candidates with assessable multi-fine-type replicates",
    )
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    fig.tight_layout()
    return fig, stable


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--figure-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    result_dir = (
        args.result_dir.resolve()
        if args.result_dir
        else root / "results" / "minerva_production" / "20_sex_apoe_kda"
    )
    figure_root = (
        args.figure_root.resolve()
        if args.figure_root
        else root / "results" / "figures" / "analysis" / "phase_20_sex_apoe_kda"
    )
    figure_root.mkdir(parents=True, exist_ok=True)
    configure_style()
    paths = validate_inputs(result_dir)
    manifest = read_tsv(paths["manifest"])
    candidates = read_tsv(paths["candidates"])
    top5 = read_tsv(paths["top5"])
    stability = read_tsv(paths["stability"])
    candidates["relaxed_category_acat_q"] = pd.to_numeric(
        candidates["relaxed_category_acat_q"]
    )

    figure_rows = []
    figure_rows.append(
        save_bundle(
            figure_root,
            "category_coverage",
            plot_coverage(manifest),
            manifest,
            "# Phase 20 category coverage\n\nPhase 20-included KDA runs and distinct fine cell types for all 42 categories.",
            "# Methods\n\nCounts come from `phase20_category_manifest.tsv` after requiring at least three effective query genes.",
        )
    )
    figure_rows.append(
        save_bundle(
            figure_root,
            "driver_category_evidence",
            plot_evidence(candidates),
            candidates,
            "# Phase 20 driver-by-category evidence\n\nRelaxed non-MT candidates; white circles denote strict-reference support.",
            "# Methods\n\nFill is −log10 of the non-MT-only within-category BH q value. Only candidate-containing categories are plotted.",
        )
    )
    top_fig, ranked_top = plot_top5(top5)
    figure_rows.append(
        save_bundle(
            figure_root,
            "top5_candidates",
            top_fig,
            ranked_top,
            "# Phase 20 top-five candidates\n\nUp to five passing relaxed non-MT drivers per candidate-containing category.",
            "# Methods\n\nRanks use category q, ACAT P, and gene symbol. Categories without a passing candidate are not backfilled or plotted.",
        )
    )
    recurrence = recurrence_data(candidates)
    figure_rows.append(
        save_bundle(
            figure_root,
            "driver_recurrence",
            plot_recurrence(recurrence),
            recurrence,
            "# Phase 20 driver recurrence\n\nTop recurrent non-MT drivers across relaxed candidate-containing categories.",
            "# Methods\n\nEach gene is counted once per category. Fill records how many of those occurrences also meet the strict reference.",
        )
    )
    stability_fig, stable_data = plot_stability(stability)
    figure_rows.append(
        save_bundle(
            figure_root,
            "stability_summary",
            stability_fig,
            stable_data,
            "# Phase 20 stability\n\nCandidate retention after omitting each fine cell type in turn.",
            "# Methods\n\nEach replicate rebuilds the complete non-MT BH family. The dashed line marks 80% retention.",
        )
    )
    write_tsv(
        pd.DataFrame(figure_rows), figure_root / "phase20_figure_manifest.tsv"
    )
    print(f"wrote={figure_root}")
    print(f"figure_bundles={len(figure_rows)}")
    print("validation_status=validated_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
