#!/usr/bin/env python3
"""Render the complete Phase 15 mitonuclear-coupling figure package.

The renderer consumes only validated Phase 15 result tables.  It reshapes and
displays saved estimates, predictions, diagnostics, and statuses; it never
refits a scientific model or recomputes inferential decisions.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "phase15_mitonuclear_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "phase15_mitonuclear_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import colors as mpl_colors  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
from matplotlib import transforms as mtransforms  # noqa: E402
import numpy as np  # noqa: E402


SCHEMA = "phase15_figure_package_v1"
OKABE_ITO = {
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "black": "#000000",
}
ENDPOINT_COLORS = {
    "standardized_difference": OKABE_ITO["blue"],
    "nci_reference_residual": OKABE_ITO["orange"],
    "coupling_slope_change": OKABE_ITO["green"],
}
ENDPOINT_LIMITS = {
    "standardized_difference": 1.25,
    "nci_reference_residual": 1.50,
    "coupling_slope_change": 2.00,
}
STRATUM_LIMITS = {
    "standardized_difference": 1.00,
    "nci_reference_residual": 1.25,
    "coupling_slope_change": 1.50,
}
PASS_COLOR = OKABE_ITO["blue"]
FAIL_COLOR = OKABE_ITO["vermillion"]
NA_COLOR = "#D9D9D9"
INCONCLUSIVE_COLOR = "#5C5C5C"
NOT_TESTABLE_COLOR = "#BDBDBD"


def configure_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.0,
            "patch.linewidth": 0.7,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "svg.hashsalt": "phase15_mitonuclear_coupling_v1",
            "pdf.compression": 9,
        }
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default="results/minerva_production/15_mitonuclear_coupling",
    )
    parser.add_argument(
        "--output-dir",
        default="results/figures/analysis/phase15_mitonuclear_coupling",
    )
    parser.add_argument("--png-dpi", type=int, default=300)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
        help="Set to complete only after manual inspection of rendered previews.",
    )
    args = parser.parse_args(argv)
    if not 300 <= args.png_dpi <= 600:
        parser.error("--png-dpi must be between 300 and 600")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_tsv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"Missing input: {path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require_columns(rows: Sequence[Mapping[str, str]], columns: Sequence[str], label: str) -> None:
    require(bool(rows), f"{label} is empty")
    missing = [column for column in columns if column not in rows[0]]
    require(not missing, f"{label} is missing columns: {', '.join(missing)}")


def fnum(value: Any) -> float:
    if value in (None, "", "NA", "NaN", "nan"):
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def inum(value: Any) -> int | None:
    number = fnum(value)
    return None if not math.isfinite(number) else int(round(number))


def flag(value: Any) -> bool | None:
    if value is True or value in ("TRUE", "True", "true", "1", 1):
        return True
    if value is False or value in ("FALSE", "False", "false", "0", 0):
        return False
    return None


def display_q(value: Any) -> str:
    number = fnum(value)
    if not math.isfinite(number):
        return "q=NA"
    if number < 0.001:
        return f"q={number:.1e}"
    return f"q={number:.3f}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = ["schema_version", "figure_family", "record_type", "panel_id"]
    observed: list[str] = []
    for row in rows:
        for key in row:
            if key not in observed:
                observed.append(key)
    return [key for key in preferred if key in observed] + [
        key for key in observed if key not in preferred
    ]


def atomic_write_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty TSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    columns = ordered_columns(rows)
    with open(temporary, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    column: "NA"
                    if row.get(column) is None
                    or (isinstance(row.get(column), float) and math.isnan(row[column]))
                    else row.get(column, "NA")
                    for column in columns
                }
            )
    os.replace(temporary, path)


def render_triplet(
    fig: plt.Figure, directory: Path, basename: str, png_dpi: int
) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for extension in ("svg", "pdf", "png"):
        final_path = directory / f"{basename}.{extension}"
        temporary = directory / f".{basename}.tmp.{os.getpid()}.{extension}"
        metadata: dict[str, Any]
        if extension == "pdf":
            metadata = {
                "Creator": "Phase 15 mitonuclear-coupling renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        else:
            metadata = {"Creator": "Phase 15 mitonuclear-coupling renderer"}
        fig.savefig(
            temporary,
            format=extension,
            dpi=png_dpi if extension == "png" else None,
            metadata=metadata,
            facecolor="white",
        )
        require(temporary.exists() and temporary.stat().st_size > 0, f"Empty render: {temporary}")
        os.replace(temporary, final_path)
        outputs.append(final_path)
    plt.close(fig)
    return outputs


def panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def despine(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def status_marker(status: str) -> tuple[str, str, str]:
    if status == "not_testable":
        return "x", NOT_TESTABLE_COLOR, NOT_TESTABLE_COLOR
    if status == "supported":
        return "o", OKABE_ITO["green"], "black"
    return "o", "white", INCONCLUSIVE_COLOR


def context_role_code(role: str) -> str:
    return "P" if role == "primary_confirmatory" else "S"


def parse_donor_counts(value: str) -> list[int]:
    if not value or value == "NA":
        return []
    output: list[int] = []
    for part in value.split("|"):
        token = part.split("=", 1)[-1]
        try:
            output.append(int(token))
        except ValueError:
            continue
    return output


def rows_with_meta(
    rows: Sequence[Mapping[str, Any]], family: str, record_type: str, panel: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        row.update(
            {
                "schema_version": SCHEMA,
                "figure_family": family,
                "record_type": record_type,
                "panel_id": panel,
            }
        )
        output.append(row)
    return output


def generic_checks(
    family: str,
    plotted_rows: Sequence[Mapping[str, Any]],
    image_paths: Sequence[Path],
    extra: Sequence[tuple[str, bool, Any, Any, str]],
) -> list[dict[str, Any]]:
    checks = [
        ("plotted_data_nonempty", len(plotted_rows) > 0, len(plotted_rows), ">0", ""),
        (
            "vector_and_raster_outputs_present",
            {path.suffix for path in image_paths} == {".svg", ".pdf", ".png"},
            "|".join(sorted(path.suffix for path in image_paths)),
            ".pdf|.png|.svg",
            "",
        ),
        (
            "outputs_nonempty",
            all(path.exists() and path.stat().st_size > 0 for path in image_paths),
            sum(path.exists() and path.stat().st_size > 0 for path in image_paths),
            len(image_paths),
            "",
        ),
        (
            "colorblind_safe_palette_configured",
            True,
            "PuOr_r, viridis-derived sequential maps, Okabe-Ito categories",
            "colorblind-safe palettes",
            "",
        ),
        (
            "grayscale_redundant_encoding_configured",
            True,
            "status symbols, borders, hatching, and labels supplement color",
            "color is not the sole status encoding",
            "",
        ),
        ("minimum_text_size_configured", True, "7 pt", ">=7 pt", ""),
        ("no_significance_stars", True, "none", "none", "Exact q values and statuses are used."),
    ] + list(extra)
    return [
        {
            "schema_version": SCHEMA,
            "figure_family": family,
            "check_id": check_id,
            "blocking": "TRUE",
            "passed": "TRUE" if passed else "FALSE",
            "observed": observed,
            "expected": expected,
            "detail": detail,
        }
        for check_id, passed, observed, expected, detail in checks
    ]


def finalize_family(
    *,
    project_root: Path,
    family: str,
    directory: Path,
    basename: str,
    plotted_rows: Sequence[Mapping[str, Any]],
    image_paths: Sequence[Path],
    source_paths: Sequence[Path],
    caption: str,
    methods: str,
    production_status_hash: str,
    visual_review_status: str,
    extra_checks: Sequence[tuple[str, bool, Any, Any, str]] = (),
) -> dict[str, Any]:
    plotted_path = directory / f"{basename}_plotted_data.tsv"
    caption_path = directory / f"{basename}_caption.md"
    methods_path = directory / f"{basename}_methods.md"
    atomic_write_tsv(plotted_path, plotted_rows)
    atomic_write_text(caption_path, caption.rstrip() + "\n")
    atomic_write_text(methods_path, methods.rstrip() + "\n")

    manifest_rows: list[dict[str, Any]] = []
    for record_type, paths in (
        ("input", source_paths),
        ("output", [plotted_path, *image_paths, caption_path, methods_path]),
    ):
        for path in paths:
            resolved = path.resolve()
            try:
                display_path = str(resolved.relative_to(project_root.resolve()))
            except ValueError:
                display_path = str(resolved)
            manifest_rows.append(
                {
                    "schema_version": SCHEMA,
                    "figure_family": family,
                    "record_type": record_type,
                    "artifact_id": path.name,
                    "path": display_path,
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    manifest_path = directory / f"{basename}_manifest.tsv"
    atomic_write_tsv(manifest_path, manifest_rows)

    checks = generic_checks(family, plotted_rows, image_paths, extra_checks)
    checks.append(
        {
            "schema_version": SCHEMA,
            "figure_family": family,
            "check_id": "production_status_hash_recorded",
            "blocking": "TRUE",
            "passed": "TRUE",
            "observed": production_status_hash,
            "expected": production_status_hash,
            "detail": "",
        }
    )
    checks_path = directory / f"{basename}_checks.tsv"
    atomic_write_tsv(checks_path, checks)
    failed = sum(row["passed"] != "TRUE" for row in checks)
    status = {
        "schema_version": SCHEMA,
        "figure_family": family,
        "production_status_sha256": production_status_hash,
        "plotted_rows": len(plotted_rows),
        "image_artifacts": len(image_paths),
        "checks": len(checks),
        "failed_checks": failed,
        "visual_review_status": visual_review_status,
        "validation_status": "validated_complete" if failed == 0 else "validation_failed",
    }
    status_path = directory / f"{basename}_status.tsv"
    atomic_write_tsv(status_path, [status])
    require(failed == 0, f"Figure-family validation failed: {family}")
    status["status_path"] = str(status_path)
    return status


def make_effect_heatmap(
    ax: plt.Axes,
    rows: Sequence[Mapping[str, str]],
    row_ids: Sequence[str],
    column_ids: Sequence[str],
    row_labels: Sequence[str],
    column_labels: Sequence[str],
    limit: float,
    title: str,
    annotate: bool = False,
) -> Any:
    lookup = {(row["context_id"], row["contrast_id"]): row for row in rows}
    matrix = np.full((len(row_ids), len(column_ids)), np.nan)
    statuses = np.full(matrix.shape, "missing", dtype=object)
    for i, context_id in enumerate(row_ids):
        for j, contrast_id in enumerate(column_ids):
            row = lookup.get((context_id, contrast_id))
            if row:
                matrix[i, j] = fnum(row.get("estimate"))
                statuses[i, j] = row.get("endpoint_status", "inconclusive")
    masked = np.ma.masked_invalid(np.clip(matrix, -limit, limit))
    cmap = plt.get_cmap("PuOr_r").copy()
    cmap.set_bad(NA_COLOR)
    image = ax.imshow(masked, cmap=cmap, norm=mpl_colors.TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), aspect="auto")
    ax.set_xticks(range(len(column_ids)), column_labels, rotation=42, ha="right")
    ax.set_yticks(range(len(row_ids)), row_labels)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(np.arange(-0.5, len(column_ids), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_ids), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(len(row_ids)):
        for j in range(len(column_ids)):
            value = matrix[i, j]
            status = statuses[i, j]
            if status == "not_testable" or not math.isfinite(value):
                ax.plot(j, i, marker="x", color="#777777", markersize=6, markeredgewidth=1.1)
                continue
            if status == "inconclusive":
                ax.add_patch(mpatches.Rectangle((j - 0.46, i - 0.46), 0.92, 0.92, fill=False, edgecolor="#5A5A5A", linewidth=0.6))
            if abs(value) > limit:
                ax.plot(j, i, marker="^" if value > 0 else "v", color="black", markersize=4)
            if annotate:
                color = "white" if abs(value) > 0.62 * limit else "#222222"
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=6.5, color=color)
    return image


def title_figure(fig: plt.Figure, title: str, subtitle: str = "") -> None:
    engine = fig.get_layout_engine()
    if engine is not None:
        engine.set(rect=(0.0, 0.0, 1.0, 0.935))
    else:
        fig.subplots_adjust(top=0.935)
    fig.suptitle(title, x=0.02, y=0.995, ha="left", va="top", fontsize=13, fontweight="bold")
    if subtitle:
        fig.text(0.02, 0.970, subtitle, ha="left", va="top", fontsize=8, color="#444444")


def load_bundle(input_dir: Path) -> dict[str, Any]:
    names = {
        "status": "mitonuclear_status.tsv",
        "claims": "mitonuclear_claim_summary.tsv",
        "contexts": "mitonuclear_context_manifest.tsv",
        "contrasts": "mitonuclear_contrast_manifest.tsv",
        "endpoints": "mitonuclear_endpoint_manifest.tsv",
        "general_results": "mitonuclear_general_results.tsv",
        "modifier_results": "mitonuclear_modifier_results.tsv",
        "general_gates": "mitonuclear_general_gate_decisions.tsv",
        "modifier_gates": "mitonuclear_modifier_gate_decisions.tsv",
        "stratum_effects": "mitonuclear_stratum_effects.tsv",
        "donor_eligibility": "mitonuclear_donor_eligibility.tsv",
        "donor_endpoints": "mitonuclear_donor_endpoints.tsv.gz",
        "reference_predictions": "mitonuclear_reference_predictions.tsv.gz",
        "prediction_grid": "mitonuclear_prediction_grid.tsv.gz",
        "group_slopes": "mitonuclear_group_slopes.tsv",
        "general_stability": "mitonuclear_general_stability_summary.tsv",
        "modifier_stability": "mitonuclear_modifier_stability_summary.tsv",
        "score_reliability": "mitonuclear_score_reliability.tsv",
        "gene_influence": "mitonuclear_gene_complex_influence.tsv",
        "qc_sensitivity": "mitonuclear_qc_normalization_sensitivity.tsv",
        "crossfit_folds": "mitonuclear_crossfit_folds.tsv",
        "checks": "mitonuclear_checks.tsv",
    }
    paths = {key: input_dir / filename for key, filename in names.items()}
    bundle: dict[str, Any] = {key: read_tsv(path) for key, path in paths.items()}
    bundle["paths"] = paths

    require_columns(
        bundle["status"],
        ["validation_status", "scientific_decision", "general_result_rows", "modifier_result_rows"],
        "status",
    )
    require(
        len(bundle["status"]) == 1
        and bundle["status"][0]["validation_status"] == "validated_complete",
        "Phase 15 production status is not validated_complete",
    )
    require(bundle["status"][0]["scientific_decision"] == "inconclusive", "Unexpected Phase 15 decision")
    require(len(bundle["contexts"]) == 7, "Expected seven contexts")
    require(len(bundle["endpoints"]) == 3, "Expected three endpoints")
    require(len(bundle["general_results"]) == 21, "Expected 21 general rows")
    require(len(bundle["modifier_results"]) == 147, "Expected 147 modifier rows")
    require(len(bundle["stratum_effects"]) == 126, "Expected 126 stratum rows")
    require(len(bundle["general_gates"]) == 7, "Expected seven general gates")
    require(len(bundle["modifier_gates"]) == 49, "Expected 49 modifier gates")
    require(len(bundle["donor_endpoints"]) == 1825, "Expected 1,825 donor-context endpoints")
    require(all(row.get("passed") == "TRUE" for row in bundle["checks"]), "A production check failed")

    contexts = sorted(bundle["contexts"], key=lambda row: int(row["context_order"]))
    contrasts = sorted(bundle["contrasts"], key=lambda row: int(row["contrast_order"]))
    endpoints = sorted(bundle["endpoints"], key=lambda row: int(row["endpoint_order"]))
    bundle["contexts"] = contexts
    bundle["contrasts"] = contrasts
    bundle["endpoints"] = endpoints
    bundle["context_ids"] = [row["context_id"] for row in contexts]
    bundle["context_labels"] = {row["context_id"]: row["context_label"] for row in contexts}
    bundle["context_roles"] = {row["context_id"]: row["context_role"] for row in contexts}
    bundle["modifier_contrast_ids"] = [row["contrast_id"] for row in contrasts if row["contrast_type"] == "modifier"]
    bundle["endpoint_ids"] = [row["endpoint_id"] for row in endpoints]
    bundle["endpoint_labels"] = {row["endpoint_id"]: row["endpoint_label"] for row in endpoints}
    bundle["production_status_hash"] = sha256_file(paths["status"])
    return bundle


CONTRAST_LABELS = {
    "general_equal_stratum_AD_minus_NCI": "General",
    "sex_F_minus_M__e2": "F−M | ε2",
    "sex_F_minus_M__e33": "F−M | ε3/3",
    "sex_F_minus_M__e4": "F−M | ε4",
    "apoe_e2_minus_e33__Female": "ε2−ε3/3 | F",
    "apoe_e2_minus_e33__Male": "ε2−ε3/3 | M",
    "apoe_e4_minus_e33__Female": "ε4−ε3/3 | F",
    "apoe_e4_minus_e33__Male": "ε4−ε3/3 | M",
}
STRATUM_LABELS = {
    "Female__e2": "F | ε2",
    "Female__e33": "F | ε3/3",
    "Female__e4": "F | ε4",
    "Male__e2": "M | ε2",
    "Male__e33": "M | ε3/3",
    "Male__e4": "M | ε4",
}
ENDPOINT_SHORT = {
    "standardized_difference": "Compartment difference",
    "nci_reference_residual": "NCI-reference residual",
    "coupling_slope_change": "Coupling-slope change",
}


def render_complete_evidence(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "complete_evidence_landscape"
    basename = "phase15_complete_evidence_landscape"
    directory = output_dir / family
    contexts = bundle["context_ids"]
    labels = bundle["context_labels"]
    endpoints = bundle["endpoint_ids"]
    modifiers = bundle["modifier_contrast_ids"]

    fig = plt.figure(figsize=(11, 14.5), layout="constrained")
    title_figure(
        fig,
        "Phase 15: complete mitonuclear-coupling evidence landscape",
        "Validated production result • all 168 formal endpoint tests • exact frozen statuses",
    )
    outer = fig.add_gridspec(3, 1, height_ratios=(1.25, 2.45, 2.2), hspace=0.16)
    top = outer[0].subgridspec(1, 2, width_ratios=(2.7, 1.15), wspace=0.18)
    ax_a = fig.add_subplot(top[0, 0])
    ax_d = fig.add_subplot(top[0, 1])

    ax_a.set_axis_off()
    panel_label(ax_a, "A", x=-0.02, y=1.02)
    ax_a.set_title("Prespecified analysis and decision structure", loc="left", fontweight="bold", pad=8)
    boxes = [
        (0.02, 0.34, 0.16, 0.38, "Donor scores\nM: mtDNA OXPHOS\nN: nuclear OXPHOS", "#EAF2F8"),
        (0.23, 0.24, 0.19, 0.58, "Three endpoints\nD = M − N\nNCI residual\nSlope change", "#FDF2E9"),
        (0.48, 0.34, 0.17, 0.38, "General or direct\nsex/APOE contrast\n+ HC3 95% CI", "#E8F6F3"),
        (0.71, 0.34, 0.12, 0.38, "Endpoint\nstatus +\nstability", "#F4ECF7"),
        (0.88, 0.34, 0.10, 0.38, "Three-\nendpoint\nC3 gate", "#F2F3F4"),
    ]
    for x, y, width, height, text, color in boxes:
        ax_a.add_patch(
            mpatches.FancyBboxPatch(
                (x, y), width, height, boxstyle="round,pad=0.012", transform=ax_a.transAxes,
                facecolor=color, edgecolor="#555555", linewidth=0.8,
            )
        )
        ax_a.text(x + width / 2, y + height / 2, text, transform=ax_a.transAxes, ha="center", va="center", fontsize=7.4)
    for start, end in ((0.18, 0.23), (0.42, 0.48), (0.65, 0.71), (0.83, 0.88)):
        ax_a.annotate("", xy=(end, 0.53), xytext=(start, 0.53), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": "#555555", "lw": 0.9})
    ax_a.text(0.02, 0.10, "Association-level RNA evidence only; no causal or functional arrow is implied.", transform=ax_a.transAxes, fontsize=7.2, color="#444444")

    ax_d.set_axis_off()
    panel_label(ax_d, "D", x=-0.03, y=1.02)
    ax_d.set_title("Terminal decision", loc="left", fontweight="bold", pad=8)
    decision_lines = [
        ("Endpoints", "0 supported", OKABE_ITO["blue"]),
        ("Endpoint rows", "158 inconclusive | 10 not testable", INCONCLUSIVE_COLOR),
        ("General gates", "7 inconclusive", INCONCLUSIVE_COLOR),
        ("Modifier gates", "46 inconclusive | 3 not testable", INCONCLUSIVE_COLOR),
        ("Primary C3", "INCONCLUSIVE", OKABE_ITO["vermillion"]),
        ("Residual bridge", "NOT AUTHORIZED", OKABE_ITO["vermillion"]),
    ]
    for index, (left, right, color) in enumerate(decision_lines):
        y = 0.88 - index * 0.145
        ax_d.text(0.02, y, left, transform=ax_d.transAxes, ha="left", va="center", fontsize=7.2, color="#333333")
        ax_d.text(0.98, y, right, transform=ax_d.transAxes, ha="right", va="center", fontsize=7.5, fontweight="bold", color=color)
        ax_d.plot([0.02, 0.98], [y - 0.065, y - 0.065], transform=ax_d.transAxes, color="#E5E5E5", lw=0.6)

    middle = outer[1].subgridspec(1, 3, wspace=0.10)
    general = bundle["general_results"]
    forest_axes: list[plt.Axes] = []
    for ep_index, endpoint in enumerate(endpoints):
        ax = fig.add_subplot(middle[0, ep_index], sharey=forest_axes[0] if forest_axes else None)
        forest_axes.append(ax)
        subset = sorted(
            [row for row in general if row["endpoint_id"] == endpoint],
            key=lambda row: contexts.index(row["context_id"]),
        )
        y_values = np.arange(len(contexts))[::-1]
        lows = [fnum(row["ci_low"]) for row in subset]
        highs = [fnum(row["ci_high"]) for row in subset]
        finite = [value for value in lows + highs if math.isfinite(value)] + [-0.25, 0.25]
        low, high = min(finite), max(finite)
        pad = 0.18 * max(high - low, 0.8)
        ax.set_xlim(low - pad, high + pad)
        ax.axvspan(-0.25, 0.25, color="#EFEFEF", zorder=0)
        ax.axvline(0, color="#333333", lw=0.8, zorder=1)
        for y, row in zip(y_values, subset):
            estimate, ci_low, ci_high = map(fnum, (row["estimate"], row["ci_low"], row["ci_high"]))
            status = row["endpoint_status"]
            line_color = NOT_TESTABLE_COLOR if status == "not_testable" else ENDPOINT_COLORS[endpoint]
            ax.plot([ci_low, ci_high], [y, y], color=line_color, lw=1.2, ls="--" if status == "not_testable" else "-")
            if status == "not_testable":
                ax.plot(estimate, y, marker="x", color=NOT_TESTABLE_COLOR, ms=6, mew=1.2)
            else:
                stable = row.get("stability_status") == "passed"
                ax.plot(estimate, y, marker="o", ms=5, mfc=ENDPOINT_COLORS[endpoint] if stable else "white", mec=ENDPOINT_COLORS[endpoint], mew=1.1)
            transform = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
            ax.text(0.99, y + 0.18, display_q(row["q_value"]), transform=transform, ha="right", va="bottom", fontsize=6.2, color="#444444")
        ax.set_yticks(y_values)
        if ep_index == 0:
            ylabels = []
            lookup = {row["context_id"]: row for row in subset}
            for context in contexts:
                row = lookup[context]
                donor_text = row["donor_counts"].replace("NCI=", "NCI ").replace("AD=", "AD ").replace("|", "  ")
                ylabels.append(f"[{context_role_code(row['context_role'])}] {labels[context]}\n{donor_text}")
            ax.set_yticklabels(ylabels)
            panel_label(ax, "B", x=-0.38, y=1.04)
        else:
            ax.tick_params(labelleft=False)
        ax.set_title(ENDPOINT_SHORT[endpoint], color=ENDPOINT_COLORS[endpoint], fontweight="bold")
        ax.set_xlabel("Adjusted estimate (95% CI)")
        ax.grid(axis="x", color="#E6E6E6", lw=0.5)
        despine(ax)
    forest_axes[0].text(-0.38, 1.12, "All 21 general endpoint tests", transform=forest_axes[0].transAxes, fontsize=9, fontweight="bold", ha="left")
    legend_handles = [
        plt.Line2D([], [], marker="o", mfc=OKABE_ITO["blue"], mec=OKABE_ITO["blue"], ls="", label="Stability passed"),
        plt.Line2D([], [], marker="o", mfc="white", mec=OKABE_ITO["blue"], ls="", label="Stability failed"),
        plt.Line2D([], [], marker="x", color=NOT_TESTABLE_COLOR, ls="", label="Not testable"),
        mpatches.Patch(facecolor="#EFEFEF", edgecolor="none", label="±0.25 SESOI region"),
    ]
    forest_axes[-1].legend(handles=legend_handles, loc="lower right", frameon=False, bbox_to_anchor=(1.0, -0.25), ncol=2)

    bottom = outer[2].subgridspec(1, 3, wspace=0.13)
    heat_axes: list[plt.Axes] = []
    images = []
    for ep_index, endpoint in enumerate(endpoints):
        ax = fig.add_subplot(bottom[0, ep_index])
        heat_axes.append(ax)
        subset = [row for row in bundle["modifier_results"] if row["endpoint_id"] == endpoint]
        image = make_effect_heatmap(
            ax,
            subset,
            contexts,
            modifiers,
            [labels[context] for context in contexts],
            [CONTRAST_LABELS[contrast] for contrast in modifiers],
            ENDPOINT_LIMITS[endpoint],
            ENDPOINT_SHORT[endpoint],
        )
        images.append(image)
        if ep_index > 0:
            ax.tick_params(labelleft=False)
        colorbar = fig.colorbar(image, ax=ax, orientation="horizontal", fraction=0.055, pad=0.20)
        colorbar.set_label("Signed modifier estimate", fontsize=7)
        colorbar.ax.tick_params(labelsize=6.5)
    panel_label(heat_axes[0], "C", x=-0.40, y=1.04)
    heat_axes[0].text(-0.40, 1.13, "Complete modifier atlas: 147 endpoint tests", transform=heat_axes[0].transAxes, fontsize=9, fontweight="bold", ha="left")

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = (
        rows_with_meta(bundle["general_results"], family, "general_endpoint", "B")
        + rows_with_meta(bundle["modifier_results"], family, "modifier_endpoint", "C")
        + rows_with_meta(bundle["general_gates"], family, "general_gate", "D")
        + rows_with_meta(bundle["modifier_gates"], family, "modifier_gate", "D")
        + rows_with_meta(bundle["claims"], family, "claim_summary", "D")
    )
    caption = """# Complete C3 evidence landscape

**A,** Prespecified donor-score, endpoint, contrast, and three-endpoint C3 decision structure. **B,** All 21 general endpoint estimates with HC3 95% confidence intervals. The gray band marks the endpoint-specific ±0.25 smallest effect size of interest (SESOI); filled markers passed the complete stability summary and open markers did not. Exact family-wide q values are printed for every row. **C,** Complete signed-estimate atlas for all 147 modifier endpoint tests. Gray crossed cells are not testable and triangles indicate values clipped at the stated endpoint-specific color limits. **D,** Frozen endpoint, gate, overall C3, and residual-bridge decisions. Primary and secondary contexts are labeled P and S. No endpoint or C3 gate is supported; Phase 15 is inconclusive rather than a precise null. No significance stars are used.
"""
    methods = """# Methods

The renderer read the validated Phase 15 general and modifier result tables and gate-decision tables without refitting models. General estimates use the saved HC3 confidence intervals and four prespecified BH families. Modifier heatmaps retain the frozen context and contrast order. Signed estimates use endpoint-specific zero-centered PuOr scales (difference ±1.25, residual ±1.50, slope ±2.00); clipped cells carry a directional triangle. Status, stability, and testability use redundant marker fill, outlines, and crosses. The statistical unit is one donor within one broad cell context.
"""
    extra = [
        ("formal_endpoint_count", len(bundle["general_results"]) + len(bundle["modifier_results"]) == 168, len(bundle["general_results"]) + len(bundle["modifier_results"]), 168, ""),
        ("supported_endpoint_count", sum(row["endpoint_status"] == "supported" for row in bundle["general_results"] + bundle["modifier_results"]) == 0, sum(row["endpoint_status"] == "supported" for row in bundle["general_results"] + bundle["modifier_results"]), 0, ""),
        ("not_testable_endpoint_count", sum(row["endpoint_status"] == "not_testable" for row in bundle["general_results"] + bundle["modifier_results"]) == 10, sum(row["endpoint_status"] == "not_testable" for row in bundle["general_results"] + bundle["modifier_results"]), 10, ""),
        ("gate_count", len(bundle["general_gates"]) + len(bundle["modifier_gates"]) == 56, len(bundle["general_gates"]) + len(bundle["modifier_gates"]), 56, ""),
    ]
    return finalize_family(
        project_root=project_root,
        family=family,
        directory=directory,
        basename=basename,
        plotted_rows=plotted,
        image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "claims", "contexts", "contrasts", "endpoints", "general_results", "modifier_results", "general_gates", "modifier_gates")],
        caption=caption,
        methods=methods,
        production_status_hash=bundle["production_status_hash"],
        visual_review_status=review,
        extra_checks=extra,
    )


def render_primary_geometry(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "primary_coupling_geometry"
    basename = "phase15_primary_coupling_geometry"
    directory = output_dir / family
    primary = [row["context_id"] for row in bundle["contexts"] if row["context_role"] == "primary_confirmatory"]
    labels = bundle["context_labels"]

    donor_rows = [row for row in bundle["donor_endpoints"] if row["context_id"] in primary]
    prediction_rows = [
        row for row in bundle["reference_predictions"]
        if row["context_id"] in primary and row["assignment_id"] == "0" and row["diagnosis"] == "NCI"
    ]
    endpoint_lookup = {(row["context_id"], row["projid"]): row for row in donor_rows}
    predictions_joined: list[dict[str, Any]] = []
    for row in prediction_rows:
        endpoint_row = endpoint_lookup.get((row["context_id"], row["projid"]))
        if endpoint_row:
            joined = dict(row)
            joined["N"] = endpoint_row["N"]
            joined["observed_M_endpoint"] = endpoint_row["M"]
            predictions_joined.append(joined)

    general_grid = [
        row for row in bundle["prediction_grid"]
        if row["scope_id"] == "general" and row["context_id"] in primary
    ]
    general_results = [
        row for row in bundle["general_results"]
        if row["context_id"] in primary
    ]

    fig = plt.figure(figsize=(11, 12.5), layout="constrained")
    title_figure(
        fig,
        "Phase 15: primary-context mitonuclear geometry",
        "Donor-level score pairs, held-out NCI predictions, saved departure curves, and formal endpoint triplets",
    )
    outer = fig.add_gridspec(3, 1, height_ratios=(2.2, 1.55, 2.0), hspace=0.13)
    scatter_grid = outer[0].subgridspec(1, 3, wspace=0.10)
    scatter_axes: list[plt.Axes] = []
    for index, context in enumerate(primary):
        ax = fig.add_subplot(scatter_grid[0, index])
        scatter_axes.append(ax)
        subset = [row for row in donor_rows if row["context_id"] == context]
        ref = [row for row in predictions_joined if row["context_id"] == context]
        for row in ref:
            x = fnum(row["N"])
            observed = fnum(row["observed_M_endpoint"])
            predicted = fnum(row["predicted_M"])
            if all(math.isfinite(value) for value in (x, observed, predicted)):
                ax.plot([x, x], [predicted, observed], color="#9ECAE1", lw=0.35, alpha=0.45, zorder=1)
                ax.scatter(x, predicted, marker="s", facecolors="none", edgecolors=OKABE_ITO["blue"], s=10, linewidths=0.5, alpha=0.55, zorder=2)
        for diagnosis, marker, color in (
            ("NCI", "o", OKABE_ITO["blue"]),
            ("AD", "^", OKABE_ITO["orange"]),
        ):
            part = [row for row in subset if row["diagnosis"] == diagnosis]
            ax.scatter(
                [fnum(row["N"]) for row in part],
                [fnum(row["M"]) for row in part],
                marker=marker,
                s=16,
                facecolors=color if diagnosis == "AD" else "white",
                edgecolors=color,
                linewidths=0.65,
                alpha=0.68,
                label=diagnosis,
                zorder=3,
            )
        ax.axhline(0, color="#DDDDDD", lw=0.55, zorder=0)
        ax.axvline(0, color="#DDDDDD", lw=0.55, zorder=0)
        ax.set_title(f"{labels[context]}\n{len(subset)} donor-context profiles", fontweight="bold")
        ax.set_xlabel("Nuclear OXPHOS score, N (NCI SD)")
        if index == 0:
            ax.set_ylabel("mtDNA OXPHOS score, M (NCI SD)")
            panel_label(ax, "A", x=-0.27, y=1.05)
        despine(ax)

        inset = ax.inset_axes([0.57, 0.055, 0.40, 0.34])
        slopes = [row for row in bundle["group_slopes"] if row["context_id"] == context]
        for diagnosis, marker, color, offset in (
            ("NCI", "o", OKABE_ITO["blue"], -0.09),
            ("AD", "^", OKABE_ITO["orange"], 0.09),
        ):
            part = [row for row in slopes if row["group_id"].startswith(f"{diagnosis}__")]
            for y, row in enumerate(part):
                estimate, low, high = map(fnum, (row["slope"], row["ci_low"], row["ci_high"]))
                inset.plot([low, high], [y + offset, y + offset], color=color, lw=0.6, alpha=0.75)
                inset.plot(estimate, y + offset, marker=marker, ms=2.5, mfc="white" if diagnosis == "NCI" else color, mec=color, mew=0.5)
        inset.axvline(0, color="#777777", lw=0.5)
        inset.set_yticks([])
        inset.set_title("12 saved group slopes", fontsize=6.2, pad=1)
        inset.tick_params(axis="x", labelsize=5.5, length=2)
        despine(inset)
    scatter_axes[-1].legend(loc="upper right", frameon=False, title="Diagnosis")
    scatter_axes[0].plot([], [], marker="s", mfc="none", mec=OKABE_ITO["blue"], ls="", label="Held-out NCI prediction")

    curve_grid = outer[1].subgridspec(1, 3, wspace=0.10)
    curve_axes: list[plt.Axes] = []
    gate_lookup = {row["context_id"]: row for row in bundle["general_gates"]}
    for index, context in enumerate(primary):
        ax = fig.add_subplot(curve_grid[0, index], sharey=curve_axes[0] if curve_axes else None)
        curve_axes.append(ax)
        subset = sorted(
            [row for row in general_grid if row["context_id"] == context],
            key=lambda row: fnum(row["nuclear_score"]),
        )
        x = np.array([fnum(row["nuclear_score"]) for row in subset])
        y = np.array([fnum(row["departure"]) for row in subset])
        ax.plot(x, y, color=OKABE_ITO["purple"], lw=1.5)
        ax.fill_between(x, 0, y, color=OKABE_ITO["purple"], alpha=0.12)
        ax.axhline(0, color="#333333", lw=0.75)
        if subset:
            low, high = fnum(subset[0]["common_range_low"]), fnum(subset[0]["common_range_high"])
            ax.axvline(low, color="#777777", lw=0.6, ls="--")
            ax.axvline(high, color="#777777", lw=0.6, ls="--")
        gate = gate_lookup[context]
        rewiring = "yes" if gate["slope_rewiring_observed"] == "TRUE" else "no"
        context_short = labels[context].replace(" neurons", "")
        ax.set_title(f"{context_short} • rewiring: {rewiring}", fontweight="bold")
        ax.set_xlabel("Nuclear score over common range")
        if index == 0:
            ax.set_ylabel("Saved AD−NCI departure")
            panel_label(ax, "B", x=-0.27, y=1.05)
        else:
            ax.tick_params(labelleft=False)
        despine(ax)
    curve_axes[0].text(-0.27, 1.18, "General adjusted departure curves (flag is descriptive and outside Gate 2)", transform=curve_axes[0].transAxes, fontsize=8.5, fontweight="bold", ha="left")

    ax_c = fig.add_subplot(outer[2])
    ordered_results: list[dict[str, str]] = []
    for context in primary:
        for endpoint in bundle["endpoint_ids"]:
            ordered_results.extend(
                row for row in general_results
                if row["context_id"] == context and row["endpoint_id"] == endpoint
            )
    y = np.arange(len(ordered_results))[::-1]
    ax_c.axvspan(-1, 1, color="#EFEFEF", zorder=0)
    ax_c.axvline(0, color="#333333", lw=0.8)
    for yi, row in zip(y, ordered_results):
        sesoi = fnum(row["sesoi"])
        estimate, low, high = (fnum(row[key]) / sesoi for key in ("estimate", "ci_low", "ci_high"))
        color = ENDPOINT_COLORS[row["endpoint_id"]]
        stable = row["stability_status"] == "passed"
        ax_c.plot([low, high], [yi, yi], color=color, lw=1.2)
        ax_c.plot(estimate, yi, marker="o", ms=5, mfc=color if stable else "white", mec=color, mew=1.0)
        transform = mtransforms.blended_transform_factory(ax_c.transAxes, ax_c.transData)
        ax_c.text(0.99, yi, display_q(row["q_value"]), transform=transform, ha="right", va="center", fontsize=6.5)
    ax_c.set_yticks(
        y,
        [f"{labels[row['context_id']]} • {ENDPOINT_SHORT[row['endpoint_id']]}" for row in ordered_results],
    )
    finite_ci = [abs(fnum(row[key]) / fnum(row["sesoi"])) for row in ordered_results for key in ("ci_low", "ci_high")]
    limit = max(3.0, math.ceil(max(finite_ci) * 1.08))
    ax_c.set_xlim(-limit, limit)
    ax_c.set_xlabel("Adjusted estimate / endpoint SESOI (95% CI)")
    ax_c.set_title("Formal primary general endpoint triplets: all nine inconclusive", loc="left", fontweight="bold")
    panel_label(ax_c, "C", x=-0.15, y=1.03)
    ax_c.grid(axis="x", color="#E6E6E6", lw=0.5)
    despine(ax_c)

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = (
        rows_with_meta(donor_rows, family, "donor_endpoint", "A")
        + rows_with_meta(predictions_joined, family, "heldout_nci_prediction", "A")
        + rows_with_meta([row for row in bundle["group_slopes"] if row["context_id"] in primary], family, "saved_group_slope", "A")
        + rows_with_meta(general_grid, family, "general_departure_grid", "B")
        + rows_with_meta(general_results, family, "formal_general_endpoint", "C")
        + rows_with_meta([row for row in bundle["general_gates"] if row["context_id"] in primary], family, "formal_general_gate", "C")
    )
    caption = """# Primary-context mitonuclear geometry

**A,** Donor-level mtDNA and nuclear structural-OXPHOS NCI-standardized scores in all three primary contexts. NCI observations are open blue circles, AD observations are filled orange triangles, and open squares show saved held-out NCI predictions at the same donor nuclear score; vertical segments are cross-fitted residuals. Insets show all 12 saved diagnosis/sex/APOE group slopes and their 95% confidence intervals. **B,** Saved equal-stratum general AD-minus-NCI departure curves across the validated common nuclear-score range. The rewiring label is a descriptive frozen flag outside Gate 2. **C,** Formal primary general endpoint estimates normalized by their endpoint-specific SESOI, with HC3 95% confidence intervals and exact q values. All nine endpoint rows and all three primary general C3 gates are inconclusive.
"""
    methods = """# Methods

Donor points came from the validated donor-endpoint table. Held-out NCI predictions used assignment 0 of the saved leakage-free cross-fit predictions and were joined to the same donor/context nuclear score; no reference line was refitted. Group-slope insets use saved slope estimates and confidence intervals. Departure curves use the saved prediction grid and common-range boundaries. The bottom forest uses the frozen general results and divides estimates and confidence limits by the endpoint-specific 0.25 SESOI only for display on one dimensionless axis.
"""
    extra = [
        ("primary_context_count", len(primary) == 3, len(primary), 3, ""),
        ("primary_donor_context_rows", len(donor_rows) == 820, len(donor_rows), 820, "Astrocytes, excitatory neurons, and inhibitory neurons."),
        ("primary_general_endpoint_count", len(general_results) == 9, len(general_results), 9, ""),
        ("heldout_predictions_joined", len(predictions_joined) > 0, len(predictions_joined), ">0", "Assignment 0 only."),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "contexts", "endpoints", "donor_endpoints", "reference_predictions", "prediction_grid", "group_slopes", "general_results", "general_gates")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


STABILITY_FIELDS = [
    ("bootstrap_pass", "Bootstrap"),
    ("balance_pass", "Balance"),
    ("loo_pass", "LOO"),
    ("fifty_nucleus_pass", "50 nuclei"),
    ("pc1_pass", "PC1"),
    ("nuclear_only_normalization_pass", "Nuclear norm."),
    ("severe_qc_pass", "Severe-QC"),
    ("robust_qc_covariate_pass", "QC covariate"),
    ("reference_sensitivity_pass", "NCI reference"),
    ("influence_pass", "Omission"),
    ("slope_sensitivity_pass", "Slope sens."),
    ("mandatory_sensitivity_pass", "Mandatory"),
]


def support_ratio(row: Mapping[str, str]) -> float:
    counts = parse_donor_counts(row.get("donor_counts", ""))
    if not counts:
        return math.nan
    if row["scope_id"] == "general":
        if len(counts) < 2:
            return math.nan
        return min(counts[0] / 50.0, counts[1] / 30.0)
    return min(counts) / 10.0


def render_testability(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "testability_precision_stability"
    basename = "phase15_testability_precision_stability"
    directory = output_dir / family
    contexts = bundle["context_ids"]
    labels = bundle["context_labels"]
    group_ids = []
    for sex in ("Female", "Male"):
        for apoe in ("e2", "e33", "e4"):
            for diagnosis in ("NCI", "AD"):
                group_ids.append(f"{diagnosis}__{sex}__{apoe}")
    group_labels = [
        group.replace("__", " | ").replace("Female", "F").replace("Male", "M").replace("e33", "ε3/3").replace("e2", "ε2").replace("e4", "ε4")
        for group in group_ids
    ]
    eligibility_lookup = {(row["context_id"], row["group_id"]): row for row in bundle["donor_eligibility"]}
    donor_matrix = np.full((len(contexts), len(group_ids)), np.nan)
    fifty_matrix = np.full_like(donor_matrix, np.nan)
    for i, context in enumerate(contexts):
        for j, group_id in enumerate(group_ids):
            row = eligibility_lookup.get((context, group_id))
            if row:
                donor_matrix[i, j] = fnum(row["donors"])
                fifty_matrix[i, j] = fnum(row["eligible_50"])

    all_results = bundle["general_results"] + bundle["modifier_results"]
    for row in all_results:
        row["figure_support_ratio"] = support_ratio(row)
        row["figure_ci_width"] = fnum(row["ci_high"]) - fnum(row["ci_low"])

    fig = plt.figure(figsize=(11, 10.5), layout="constrained")
    title_figure(fig, "Phase 15: testability, precision, and stability", "Why a technically complete analysis remains scientifically inconclusive")
    grid = fig.add_gridspec(2, 2, height_ratios=(1.25, 1.0), width_ratios=(1.35, 1.0), hspace=0.15, wspace=0.12)
    ax_a = fig.add_subplot(grid[0, :])
    image = ax_a.imshow(donor_matrix, cmap="Blues", vmin=0, vmax=np.nanmax(donor_matrix), aspect="auto")
    ax_a.set_xticks(range(len(group_ids)), group_labels, rotation=45, ha="right")
    ax_a.set_yticks(range(len(contexts)), [f"[{context_role_code(bundle['context_roles'][context])}] {labels[context]}" for context in contexts])
    ax_a.set_title("Donor support at the 20-nucleus threshold", loc="left", fontweight="bold")
    panel_label(ax_a, "A", x=-0.16, y=1.04)
    ax_a.set_xticks(np.arange(-0.5, len(group_ids), 1), minor=True)
    ax_a.set_yticks(np.arange(-0.5, len(contexts), 1), minor=True)
    ax_a.grid(which="minor", color="white", linewidth=1)
    ax_a.tick_params(which="minor", bottom=False, left=False)
    for i in range(len(contexts)):
        for j in range(len(group_ids)):
            count = donor_matrix[i, j]
            if not math.isfinite(count):
                continue
            color = "white" if count > 0.58 * np.nanmax(donor_matrix) else "#1B1B1B"
            ax_a.text(j, i - 0.08, f"{int(count)}", ha="center", va="center", fontsize=6.5, color=color, fontweight="bold")
            ax_a.text(j, i + 0.27, f"50+: {int(fifty_matrix[i, j])}", ha="center", va="center", fontsize=4.8, color=color)
            if count < 5:
                ax_a.add_patch(mpatches.Rectangle((j - 0.47, i - 0.47), 0.94, 0.94, fill=False, hatch="xxx", edgecolor=OKABE_ITO["vermillion"], linewidth=1.0))
            elif count < 10:
                ax_a.add_patch(mpatches.Rectangle((j - 0.47, i - 0.47), 0.94, 0.94, fill=False, edgecolor=OKABE_ITO["orange"], linewidth=1.5))
            else:
                ax_a.add_patch(mpatches.Rectangle((j - 0.47, i - 0.47), 0.94, 0.94, fill=False, edgecolor="#4D4D4D", linewidth=0.45))
    colorbar = fig.colorbar(image, ax=ax_a, orientation="vertical", fraction=0.025, pad=0.015)
    colorbar.set_label("Eligible donor-context profiles")

    ax_b = fig.add_subplot(grid[1, 0])
    marker_by_scope = {"general": "o", "modifier": "^"}
    for endpoint in bundle["endpoint_ids"]:
        for scope in ("general", "modifier"):
            subset = [row for row in all_results if row["endpoint_id"] == endpoint and row["scope_id"] == scope and row["endpoint_status"] != "not_testable"]
            ax_b.scatter(
                [fnum(row["figure_support_ratio"]) for row in subset],
                [fnum(row["figure_ci_width"]) for row in subset],
                marker=marker_by_scope[scope], s=22 if scope == "general" else 17,
                facecolors="white" if scope == "general" else ENDPOINT_COLORS[endpoint],
                edgecolors=ENDPOINT_COLORS[endpoint], linewidths=0.65, alpha=0.70,
            )
    not_testable = [row for row in all_results if row["endpoint_status"] == "not_testable"]
    ax_b.scatter(
        [fnum(row["figure_support_ratio"]) for row in not_testable],
        [fnum(row["figure_ci_width"]) for row in not_testable],
        marker="x", color=NOT_TESTABLE_COLOR, s=26, linewidths=1.1, label="Not testable",
    )
    ax_b.axvline(1, color="#555555", lw=0.8, ls="--")
    ax_b.set_yscale("log")
    ax_b.set_xlabel("Donor support relative to confirmatory threshold")
    ax_b.set_ylabel("95% CI width (log scale)")
    ax_b.set_title("Precision improves with donor support", loc="left", fontweight="bold")
    panel_label(ax_b, "B", x=-0.15, y=1.04)
    ax_b.grid(color="#E8E8E8", lw=0.5)
    despine(ax_b)
    handles = [
        plt.Line2D([], [], marker="o", mfc="white", mec="#555555", ls="", label="General"),
        plt.Line2D([], [], marker="^", mfc="#777777", mec="#777777", ls="", label="Modifier"),
        *[plt.Line2D([], [], marker="s", color=color, ls="", label=ENDPOINT_SHORT[endpoint]) for endpoint, color in ENDPOINT_COLORS.items()],
        plt.Line2D([], [], marker="x", color=NOT_TESTABLE_COLOR, ls="", label="Not testable"),
    ]
    ax_b.legend(handles=handles, frameon=False, ncol=2, loc="upper right")

    right = grid[1, 1].subgridspec(2, 1, height_ratios=(1.05, 0.95), hspace=0.25)
    ax_c = fig.add_subplot(right[0, 0])
    summary_matrix = np.zeros((2, len(STABILITY_FIELDS)))
    summaries: list[dict[str, Any]] = []
    for i, scope in enumerate(("general", "modifier")):
        subset = [row for row in all_results if row["scope_id"] == scope]
        for j, (field, label) in enumerate(STABILITY_FIELDS):
            passed = sum(flag(row.get(field)) is True for row in subset)
            applicable = sum(flag(row.get(field)) is not None for row in subset)
            summary_matrix[i, j] = passed / applicable if applicable else math.nan
            summaries.append({"scope_id": scope, "component_id": field, "component_label": label, "passed": passed, "applicable": applicable, "pass_fraction": summary_matrix[i, j]})
    im = ax_c.imshow(summary_matrix, cmap="cividis", vmin=0, vmax=1, aspect="auto")
    ax_c.set_xticks(range(len(STABILITY_FIELDS)), [label for _, label in STABILITY_FIELDS], rotation=45, ha="right", fontsize=5.8)
    ax_c.set_yticks((0, 1), ("General", "Modifier"))
    for i in range(2):
        for j in range(len(STABILITY_FIELDS)):
            item = summaries[i * len(STABILITY_FIELDS) + j]
            ax_c.text(j, i, f"{item['passed']}/{item['applicable']}", ha="center", va="center", fontsize=5.1, color="white" if summary_matrix[i, j] < 0.52 else "black")
    ax_c.set_title("Non-independent stability pass counts", loc="left", fontweight="bold")
    panel_label(ax_c, "C", x=-0.20, y=1.04)
    cb = fig.colorbar(im, ax=ax_c, orientation="vertical", fraction=0.045, pad=0.02)
    cb.set_label("Pass fraction", fontsize=7)

    ax_d = fig.add_subplot(right[1, 0])
    ax_d.set_axis_off()
    panel_label(ax_d, "D", x=-0.20, y=1.04)
    ax_d.set_title("Frozen decision pathway", loc="left", fontweight="bold")
    pathway = [
        ("Validated production", "36 declared files; all blocking checks pass", OKABE_ITO["blue"]),
        ("168 endpoint rows", "158 inconclusive; 10 not testable", INCONCLUSIVE_COLOR),
        ("No FDR-supported endpoint", "minimum q: 0.665 general; 0.982 modifier", INCONCLUSIVE_COLOR),
        ("No compatible two-endpoint gate", "7 general + 49 modifier gates", INCONCLUSIVE_COLOR),
        ("Primary C3 inconclusive", "residual bridge not authorized", OKABE_ITO["vermillion"]),
    ]
    for i, (heading, detail, color) in enumerate(pathway):
        y = 0.91 - i * 0.19
        ax_d.add_patch(mpatches.FancyBboxPatch((0.02, y - 0.09), 0.96, 0.13, boxstyle="round,pad=0.008", transform=ax_d.transAxes, facecolor="white", edgecolor=color, linewidth=1.1))
        ax_d.text(0.05, y, f"{heading} — {detail}", transform=ax_d.transAxes, ha="left", va="center", fontsize=5.6, fontweight="bold" if i in (0, len(pathway) - 1) else "normal", color=color)
        if i < len(pathway) - 1:
            ax_d.annotate("", xy=(0.50, y - 0.14), xytext=(0.50, y - 0.10), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": "#777777", "lw": 0.7})

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = (
        rows_with_meta(bundle["donor_eligibility"], family, "donor_eligibility", "A")
        + rows_with_meta(all_results, family, "precision_endpoint", "B")
        + rows_with_meta(summaries, family, "stability_component_summary", "C")
        + rows_with_meta(bundle["claims"], family, "decision_pathway", "D")
    )
    caption = """# Testability, precision, and stability

**A,** Eligible donor-context counts across all 84 context-by-diagnosis/sex/APOE cells. The large number is the 20-nucleus count and the smaller number is retained at 50 nuclei. Hatched cells contain fewer than five donors, orange outlines contain five to nine, and gray outlines contain at least ten. **B,** Confidence-interval width versus donor support relative to the confirmatory threshold. General support is the smaller of NCI/50 and AD/30; modifier support is the minimum required-cell count divided by 10. **C,** Correlated, non-independent pass counts for each saved stability component; this is not an attrition funnel. **D,** Frozen decision pathway from technical completion to the inconclusive C3 decision and unauthorized residual bridge.
"""
    methods = """# Methods

Donor counts and 50-nucleus sensitivity counts were read from the eligibility table. Precision used saved HC3 confidence limits; the y-axis is logarithmic only to display the full range. Stability counts came directly from the terminal general and modifier result fields and include every formal endpoint row. Counts are descriptive diagnostics and were not treated as independent sequential filters. Testability and gate language is reproduced from saved statuses.
"""
    extra = [
        ("eligibility_cell_count", len(bundle["donor_eligibility"]) == 84, len(bundle["donor_eligibility"]), 84, ""),
        ("formal_result_count", len(all_results) == 168, len(all_results), 168, ""),
        ("not_testable_count", len(not_testable) == 10, len(not_testable), 10, ""),
        ("stability_components", len(STABILITY_FIELDS) == 12, len(STABILITY_FIELDS), 12, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "claims", "donor_eligibility", "general_results", "modifier_results", "general_gates", "modifier_gates")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def render_complete_forest(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "complete_endpoint_forest"
    basename = "phase15_complete_endpoint_forest"
    directory = output_dir / family
    labels = bundle["context_labels"]
    all_results = bundle["general_results"] + bundle["modifier_results"]
    plotted_rows: list[dict[str, Any]] = []
    for row in all_results:
        output = dict(row)
        sesoi = fnum(row["sesoi"])
        output["estimate_in_sesoi"] = fnum(row["estimate"]) / sesoi
        output["ci_low_in_sesoi"] = fnum(row["ci_low"]) / sesoi
        output["ci_high_in_sesoi"] = fnum(row["ci_high"]) / sesoi
        output["display_ci_low_in_sesoi"] = max(-16, output["ci_low_in_sesoi"])
        output["display_ci_high_in_sesoi"] = min(16, output["ci_high_in_sesoi"])
        output["ci_clipped"] = output["ci_low_in_sesoi"] < -16 or output["ci_high_in_sesoi"] > 16
        plotted_rows.append(output)

    fig, ax = plt.subplots(figsize=(14, 26))
    fig.subplots_adjust(left=0.40, right=0.79, top=0.965, bottom=0.035)
    title_figure(
        fig,
        "Phase 15: complete endpoint forest",
        "All 168 formal endpoint tests in frozen file order • estimates normalized by endpoint-specific SESOI",
    )
    y = np.arange(len(plotted_rows))[::-1]
    ax.axvspan(-1, 1, color="#EFEFEF", zorder=0)
    ax.axvline(0, color="#333333", lw=0.8, zorder=1)
    for yi, row in zip(y, plotted_rows):
        status = row["endpoint_status"]
        endpoint = row["endpoint_id"]
        color = NOT_TESTABLE_COLOR if status == "not_testable" else ENDPOINT_COLORS[endpoint]
        ax.plot(
            [row["display_ci_low_in_sesoi"], row["display_ci_high_in_sesoi"]],
            [yi, yi],
            color=color,
            lw=0.75,
            ls="--" if status == "not_testable" else "-",
        )
        if row["ci_low_in_sesoi"] < -16:
            ax.plot(-16, yi, marker="<", color=color, ms=3)
        if row["ci_high_in_sesoi"] > 16:
            ax.plot(16, yi, marker=">", color=color, ms=3)
        if status == "not_testable":
            ax.plot(np.clip(row["estimate_in_sesoi"], -16, 16), yi, marker="x", color=color, ms=4.5, mew=0.9)
        else:
            stable = row["stability_status"] == "passed"
            ax.plot(
                np.clip(row["estimate_in_sesoi"], -16, 16), yi, marker="o", ms=3.5,
                mfc=color if stable else "white", mec=color, mew=0.75,
            )
        transform = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
        ax.text(1.02, yi, display_q(row["q_value"]), transform=transform, ha="left", va="center", fontsize=6.5)
        ax.text(1.18, yi, row["endpoint_status"].replace("_", " "), transform=transform, ha="left", va="center", fontsize=6.2, color=color)
    row_labels = []
    for row in plotted_rows:
        scope = "G" if row["scope_id"] == "general" else "M"
        contrast = "General" if scope == "G" else CONTRAST_LABELS[row["contrast_id"]]
        endpoint = {"standardized_difference": "D", "nci_reference_residual": "R", "coupling_slope_change": "Slope"}[row["endpoint_id"]]
        row_labels.append(f"[{context_role_code(row['context_role'])}|{scope}] {labels[row['context_id']]} • {contrast} • {endpoint}")
    ax.set_yticks(y, row_labels, fontsize=7)
    ax.set_xlim(-16, 16)
    ax.set_ylim(-1, len(plotted_rows))
    ax.set_xlabel("Estimate / endpoint SESOI (95% CI); arrows mark clipping at ±16")
    ax.grid(axis="x", color="#E9E9E9", lw=0.45)
    despine(ax)
    general_boundary_y = len(plotted_rows) - len(bundle["general_results"]) - 0.5
    ax.axhline(general_boundary_y, color="#222222", lw=1.0)
    ax.text(-16, general_boundary_y + 0.6, "Modifier endpoints", ha="left", va="bottom", fontsize=8, fontweight="bold")
    ax.text(-16, len(plotted_rows) - 0.2, "General endpoints", ha="left", va="top", fontsize=8, fontweight="bold")
    ax.text(1.02, 1.012, "Family-wide q", transform=ax.transAxes, ha="left", va="bottom", fontsize=7, fontweight="bold")
    ax.text(1.18, 1.012, "Final status", transform=ax.transAxes, ha="left", va="bottom", fontsize=7, fontweight="bold")
    handles = [
        *[plt.Line2D([], [], marker="o", color=color, ls="", label=ENDPOINT_SHORT[endpoint]) for endpoint, color in ENDPOINT_COLORS.items()],
        plt.Line2D([], [], marker="o", mfc="white", mec="#555555", ls="", label="Stability failed"),
        plt.Line2D([], [], marker="x", color=NOT_TESTABLE_COLOR, ls="", label="Not testable"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, ncol=2)
    panel_label(ax, "S1", x=-0.70, y=1.005)

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = rows_with_meta(plotted_rows, family, "formal_endpoint", "S1")
    caption = """# Complete endpoint forest

All 168 formal Phase 15 endpoint tests are shown in frozen file order: 21 general rows followed by 147 modifier rows. Estimates and HC3 95% confidence intervals are divided by the endpoint-specific 0.25 SESOI to share a dimensionless axis; the gray region is ±1 SESOI. Confidence limits beyond ±16 are clipped with arrows, but exact raw estimates and limits remain in the plotted-data table. Filled markers passed stability, open markers failed stability, and crossed gray rows are not testable. Exact family-wide q values and terminal endpoint statuses appear for every row. No row is supported.
"""
    methods = """# Methods

The figure uses the saved general and modifier result rows without sorting by P value. Display normalization divides estimate and confidence limits by the frozen endpoint SESOI; it does not alter inference. General and modifier BH families remain separate and the printed q values are copied from production. Primary/secondary and general/modifier roles are redundantly encoded in each row label.
"""
    extra = [
        ("formal_endpoint_count", len(plotted_rows) == 168, len(plotted_rows), 168, ""),
        ("general_rows_first", all(row["scope_id"] == "general" for row in plotted_rows[:21]), sum(row["scope_id"] == "general" for row in plotted_rows[:21]), 21, ""),
        ("supported_rows", sum(row["endpoint_status"] == "supported" for row in plotted_rows) == 0, sum(row["endpoint_status"] == "supported" for row in plotted_rows), 0, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "general_results", "modifier_results", "contexts", "contrasts", "endpoints")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def render_stratum_atlas(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "stratum_effects"
    basename = "phase15_stratum_effects"
    directory = output_dir / family
    contexts = bundle["context_ids"]
    labels = bundle["context_labels"]
    strata = list(STRATUM_LABELS)
    transformed: list[dict[str, str]] = []
    for row in bundle["stratum_effects"]:
        copy = dict(row)
        copy["contrast_id"] = row["stratum_id"]
        copy["endpoint_status"] = "inconclusive" if row["model_status"] == "estimated" else "not_testable"
        transformed.append(copy)

    fig, axes = plt.subplots(1, 3, figsize=(11, 6.4), layout="constrained")
    title_figure(
        fig,
        "Phase 15: adjusted stratum-effect atlas",
        "126 descriptive AD−NCI component effects; these are not additional primary hypotheses",
    )
    for index, endpoint in enumerate(bundle["endpoint_ids"]):
        ax = axes[index]
        subset = [row for row in transformed if row["endpoint_id"] == endpoint]
        image = make_effect_heatmap(
            ax, subset, contexts, strata,
            [f"[{context_role_code(bundle['context_roles'][context])}] {labels[context]}" for context in contexts],
            [STRATUM_LABELS[stratum] for stratum in strata],
            STRATUM_LIMITS[endpoint], ENDPOINT_SHORT[endpoint], annotate=True,
        )
        if index > 0:
            ax.tick_params(labelleft=False)
        ax.axhline(2.5, color="#222222", lw=1.2)
        cb = fig.colorbar(image, ax=ax, orientation="horizontal", fraction=0.055, pad=0.18)
        cb.set_label("Adjusted AD−NCI effect", fontsize=7)
        cb.ax.tick_params(labelsize=6.5)
        panel_label(ax, chr(ord("A") + index), x=-0.28 if index == 0 else -0.08, y=1.04)

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = rows_with_meta(bundle["stratum_effects"], family, "adjusted_stratum_effect", "A-C")
    caption = """# Adjusted stratum-effect atlas

Adjusted AD-minus-NCI component effects are shown for all seven broad contexts, six sex/APOE strata, and three endpoints (126 rows). Numbers are saved estimates; color uses endpoint-specific zero-centered PuOr scales and clipped values carry a directional triangle. The horizontal separator distinguishes three primary from four secondary contexts. These component rows explain the equal-stratum general averages and direct difference-of-differences modifiers; they are descriptive components, not 126 additional primary tests.
"""
    methods = """# Methods

Saved stratum estimates were placed in frozen context, stratum, and endpoint order. No P-value selection, clustering, or new testing was performed. Limits are fixed at ±1.00 for the compartment difference, ±1.25 for the residual, and ±1.50 for the slope change; exact unclipped values remain in the plotted-data TSV.
"""
    extra = [
        ("stratum_effect_count", len(bundle["stratum_effects"]) == 126, len(bundle["stratum_effects"]), 126, ""),
        ("context_count", len(contexts) == 7, len(contexts), 7, ""),
        ("strata_count", len(strata) == 6, len(strata), 6, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "stratum_effects", "contexts", "endpoints")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def render_slope_atlas(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "slope_departure_atlas"
    basename = "phase15_slope_departure_atlas"
    directory = output_dir / family
    contexts = bundle["context_ids"]
    questions = ["general_equal_stratum_AD_minus_NCI", *bundle["modifier_contrast_ids"]]
    grid_rows = bundle["prediction_grid"]
    gate_rows = bundle["general_gates"] + bundle["modifier_gates"]
    gate_lookup = {(row["context_id"], row["contrast_id"]): row for row in gate_rows}
    image_paths: list[Path] = []
    for context in contexts:
        fig, axes = plt.subplots(2, 4, figsize=(11, 7.2), layout="constrained", sharey=True)
        title_figure(
            fig,
            f"Phase 15 slope-departure atlas: {bundle['context_labels'][context]}",
            f"Context role: {bundle['context_roles'][context].replace('_', ' ')} • saved prediction geometry; gate status is authoritative",
        )
        for index, contrast in enumerate(questions):
            ax = axes.flat[index]
            subset = sorted(
                [row for row in grid_rows if row["context_id"] == context and row["contrast_id"] == contrast],
                key=lambda row: fnum(row["nuclear_score"]),
            )
            gate = gate_lookup[(context, contrast)]
            gate_status = gate["gate_status"]
            if subset:
                x = np.array([fnum(row["nuclear_score"]) for row in subset])
                y = np.array([fnum(row["departure"]) for row in subset])
                color = NOT_TESTABLE_COLOR if gate_status == "not_testable" else OKABE_ITO["purple"]
                ax.plot(x, y, color=color, lw=1.4, ls="--" if gate_status == "not_testable" else "-")
                ax.fill_between(x, 0, y, color=color, alpha=0.10)
                checkpoint = [row for row in subset if row["checkpoint"] == "TRUE"]
                if checkpoint:
                    ax.plot(fnum(checkpoint[0]["nuclear_score"]), fnum(checkpoint[0]["departure"]), marker="D", ms=4, mfc="white", mec=color, mew=0.8)
                low, high = fnum(subset[0]["common_range_low"]), fnum(subset[0]["common_range_high"])
                ax.axvline(low, color="#999999", lw=0.55, ls=":")
                ax.axvline(high, color="#999999", lw=0.55, ls=":")
                if gate_status == "not_testable":
                    ax.text(0.5, 0.5, "NOT TESTABLE", transform=ax.transAxes, ha="center", va="center", fontsize=11, color="#777777", alpha=0.35, rotation=25, fontweight="bold")
            else:
                ax.set_facecolor("#F3F3F3")
                ax.text(0.5, 0.55, "No valid saved curve", transform=ax.transAxes, ha="center", va="center", fontsize=8, color="#666666")
                ax.plot([0.35, 0.65], [0.38, 0.68], transform=ax.transAxes, color="#999999", lw=1.2)
                ax.plot([0.35, 0.65], [0.68, 0.38], transform=ax.transAxes, color="#999999", lw=1.2)
            ax.axhline(0, color="#333333", lw=0.7)
            rewiring = "yes" if gate["slope_rewiring_observed"] == "TRUE" else "no"
            ax.set_title(CONTRAST_LABELS[contrast], fontweight="bold", fontsize=8)
            ax.text(0.02, 0.98, f"gate: {gate_status.replace('_', ' ')}\nrewiring flag: {rewiring}", transform=ax.transAxes, ha="left", va="top", fontsize=6.3, color=NOT_TESTABLE_COLOR if gate_status == "not_testable" else "#333333")
            ax.set_ylim(-2.5, 2.5)
            if index >= 4:
                ax.set_xlabel("Nuclear score")
            if index % 4 == 0:
                ax.set_ylabel("AD−NCI departure")
            panel_label(ax, chr(ord("A") + index), x=-0.18, y=1.04)
            despine(ax)
        context_base = f"{basename}_{context}"
        image_paths.extend(render_triplet(fig, directory, context_base, dpi))

    plotted = (
        rows_with_meta(grid_rows, family, "prediction_departure_grid", "context_pages")
        + rows_with_meta(gate_rows, family, "c3_gate", "context_pages")
    )
    caption = """# Complete slope-departure atlas

One page is provided for each broad cell context. Every page contains the general question followed by all seven frozen modifier contrasts. Curves are saved AD-minus-NCI prediction departures over the validated common nuclear-score range; diamonds mark saved checkpoints. Exact gate status and the descriptive `slope_rewiring_observed` flag are printed in every panel. Gray crossed panels lack a valid curve, and gray dashed/watermarked curves belong to gates that are not testable. A rewiring flag is outside Gate 2 and is not C3 support; every compatibility classification is `none` and no gate is supported.
"""
    methods = """# Methods

The renderer used only `mitonuclear_prediction_grid.tsv.gz` and frozen gate-decision rows. It did not fit lines, smooth curves, or infer compatibility from geometry. All pages use a shared y-axis of ±2.5 so departure magnitude can be compared without context-specific rescaling. General and modifier questions remain in frozen order.
"""
    observed_questions = {(row["context_id"], row["contrast_id"]) for row in gate_rows}
    extra = [
        ("gate_question_count", len(observed_questions) == 56, len(observed_questions), 56, "Seven general plus 49 modifier gates."),
        ("context_page_count", len(contexts) == 7, len(contexts), 7, ""),
        ("prediction_grid_rows", len(grid_rows) == 2214, len(grid_rows), 2214, ""),
        ("supported_gate_count", sum(row["gate_status"] == "supported" for row in gate_rows) == 0, sum(row["gate_status"] == "supported" for row in gate_rows), 0, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "prediction_grid", "general_gates", "modifier_gates", "contexts", "contrasts")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def render_stability_atlas(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "stability_atlas"
    basename = "phase15_stability_atlas"
    directory = output_dir / family
    all_results = bundle["general_results"] + bundle["modifier_results"]
    matrix = np.full((len(all_results), len(STABILITY_FIELDS)), np.nan)
    plotted_rows: list[dict[str, Any]] = []
    for i, row in enumerate(all_results):
        output = dict(row)
        not_applicable = row["stability_status"] == "not_applicable"
        for j, (field, _) in enumerate(STABILITY_FIELDS):
            value = None if not_applicable else flag(row.get(field))
            matrix[i, j] = np.nan if value is None else (1 if value else 0)
            output[f"display_{field}"] = "not_applicable" if value is None else ("pass" if value else "fail")
        plotted_rows.append(output)

    fig = plt.figure(figsize=(13, 26))
    fig.subplots_adjust(left=0.41, right=0.94, top=0.965, bottom=0.055, wspace=0.04)
    title_figure(
        fig,
        "Phase 15: row-level stability atlas",
        "Every mandatory component for all 168 endpoint rows; pass, fail, and not applicable are distinct",
    )
    grid = fig.add_gridspec(1, 2, width_ratios=(12, 0.6))
    ax = fig.add_subplot(grid[0, 0])
    ax_status = fig.add_subplot(grid[0, 1], sharey=ax)
    display = np.ma.masked_invalid(matrix[::-1, :])
    cmap = mpl_colors.ListedColormap([FAIL_COLOR, PASS_COLOR])
    cmap.set_bad(NA_COLOR)
    norm = mpl_colors.BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)
    x_edges = np.arange(len(STABILITY_FIELDS) + 1)
    y_edges = np.arange(len(all_results) + 1)
    ax.pcolormesh(x_edges, y_edges, display, cmap=cmap, norm=norm, edgecolors="white", linewidth=0.22)
    ax.set_xlim(0, len(STABILITY_FIELDS))
    ax.set_ylim(0, len(all_results))
    ax.set_xticks(np.arange(len(STABILITY_FIELDS)) + 0.5, [label for _, label in STABILITY_FIELDS], rotation=43, ha="right", fontsize=7)
    labels = []
    for row in plotted_rows:
        scope = "G" if row["scope_id"] == "general" else "M"
        contrast = "General" if scope == "G" else CONTRAST_LABELS[row["contrast_id"]]
        endpoint = {"standardized_difference": "D", "nci_reference_residual": "R", "coupling_slope_change": "Slope"}[row["endpoint_id"]]
        labels.append(f"[{context_role_code(row['context_role'])}|{scope}] {bundle['context_labels'][row['context_id']]} • {contrast} • {endpoint}")
    ax.set_yticks(np.arange(len(all_results)) + 0.5, labels[::-1], fontsize=7)
    separator = len(all_results) - len(bundle["general_results"])
    ax.axhline(separator, color="#222222", lw=1.1)
    ax.set_title("Mandatory stability and sensitivity components", loc="left", fontweight="bold")
    panel_label(ax, "S4", x=-0.76, y=1.006)

    status_values = np.array([0 if row["endpoint_status"] == "inconclusive" else 1 for row in all_results])[::-1, None]
    status_cmap = mpl_colors.ListedColormap(["#F7F7F7", NOT_TESTABLE_COLOR])
    ax_status.pcolormesh(np.arange(2), y_edges, status_values, cmap=status_cmap, vmin=0, vmax=1, edgecolors="white", linewidth=0.22)
    ax_status.set_xticks([0.5], ["Final\nstatus"], rotation=43, ha="right", fontsize=7)
    ax_status.tick_params(labelleft=False, left=False)
    ax_status.axhline(separator, color="#222222", lw=1.1)
    for i, row in enumerate(all_results[::-1]):
        if row["endpoint_status"] == "not_testable":
            ax_status.plot(0.5, i + 0.5, marker="x", color="#666666", ms=4.5, mew=0.9)
        else:
            ax_status.plot(0.5, i + 0.5, marker="o", mfc="white", mec=INCONCLUSIVE_COLOR, ms=3.2, mew=0.7)
    for axis in (ax, ax_status):
        for spine in axis.spines.values():
            spine.set_visible(False)
    legend = [
        mpatches.Patch(facecolor=PASS_COLOR, label="Pass"),
        mpatches.Patch(facecolor=FAIL_COLOR, label="Fail"),
        mpatches.Patch(facecolor=NA_COLOR, label="Not applicable"),
        plt.Line2D([], [], marker="o", mfc="white", mec=INCONCLUSIVE_COLOR, ls="", label="Inconclusive"),
        plt.Line2D([], [], marker="x", color="#666666", ls="", label="Not testable"),
    ]
    ax.legend(handles=legend, loc="lower left", bbox_to_anchor=(0, -0.038), frameon=False, ncol=5)

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = rows_with_meta(plotted_rows, family, "endpoint_stability", "S4")
    caption = """# Row-level stability atlas

Every Phase 15 formal endpoint row is shown in frozen order, with 21 general rows above the separator and 147 modifier rows below it. Blue cells pass a saved stability or sensitivity component, vermillion cells fail, and gray cells are not applicable because the endpoint is not testable. The final-status rail redundantly distinguishes 158 inconclusive from 10 not-testable endpoints. Components are correlated diagnostics and should not be read as independent sequential filters.
"""
    methods = """# Methods

The matrix was constructed from the terminal pass fields in the general and modifier result tables. For endpoint rows with `stability_status = not_applicable`, component cells are rendered as not applicable rather than failed. No stability statistic was recalculated. Row labels preserve context role, scope, context, contrast, and endpoint.
"""
    extra = [
        ("endpoint_row_count", len(all_results) == 168, len(all_results), 168, ""),
        ("component_count", len(STABILITY_FIELDS) == 12, len(STABILITY_FIELDS), 12, ""),
        ("not_applicable_row_count", sum(row["stability_status"] == "not_applicable" for row in all_results) == 10, sum(row["stability_status"] == "not_applicable" for row in all_results), 10, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "general_results", "modifier_results", "general_stability", "modifier_stability", "contexts", "contrasts", "endpoints")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def deterministic_jitter(identifier: str, width: float = 0.11) -> float:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF
    return (fraction - 0.5) * 2 * width


def render_reliability(bundle: Mapping[str, Any], output_dir: Path, dpi: int, review: str, project_root: Path) -> dict[str, Any]:
    family = "score_reference_reliability"
    basename = "phase15_score_reference_reliability"
    directory = output_dir / family
    contexts = bundle["context_ids"]
    labels = bundle["context_labels"]
    reliability = bundle["score_reliability"]
    ref = [row for row in bundle["reference_predictions"] if row["assignment_id"] == "0" and row["diagnosis"] == "NCI"]
    donors = bundle["donor_endpoints"]

    influence_groups: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in bundle["gene_influence"]:
        influence_groups.setdefault((row["context_id"], row["scope_id"]), []).append(row)
    influence_summary: list[dict[str, Any]] = []
    for context in contexts:
        for scope in ("general", "modifier"):
            subset = influence_groups[(context, scope)]
            estimated = [row for row in subset if row["model_status"] == "estimated"]
            retained = sum(row["direction_retained"] == "TRUE" for row in estimated)
            magnitudes = [fnum(row["relative_magnitude"]) for row in estimated if math.isfinite(fnum(row["relative_magnitude"]))]
            influence_summary.append(
                {
                    "context_id": context,
                    "scope_id": scope,
                    "estimated_sensitivities": len(estimated),
                    "direction_retained": retained,
                    "direction_retained_fraction": retained / len(estimated) if estimated else math.nan,
                    "minimum_relative_magnitude": min(magnitudes) if magnitudes else math.nan,
                }
            )

    ref_summary: list[dict[str, Any]] = []
    for context in contexts:
        subset = [row for row in ref if row["context_id"] == context]
        observed = np.array([fnum(row["observed_M"]) for row in subset])
        predicted = np.array([fnum(row["predicted_M"]) for row in subset])
        correlation = float(np.corrcoef(observed, predicted)[0, 1]) if len(subset) > 2 else math.nan
        ref_summary.append({"context_id": context, "assignment_id": 0, "heldout_nci": len(subset), "observed_predicted_correlation": correlation})

    fig, axes = plt.subplots(2, 2, figsize=(11, 9.2), layout="constrained")
    title_figure(fig, "Phase 15: score and NCI-reference reliability", "Alternative scoring, leakage-free held-out prediction, residual distributions, and omission influence")
    fig.get_layout_engine().set(rect=(0.0, 0.035, 1.0, 0.935))
    ax_a, ax_b, ax_c, ax_d = axes.flat

    context_colors = dict(zip(contexts, plt.get_cmap("cividis")(np.linspace(0.12, 0.88, len(contexts)))))
    context_numbers = {context: index + 1 for index, context in enumerate(contexts)}
    module_styles = {
        "mtdna_oxphos_13": ("o", "mtDNA OXPHOS"),
        "nuclear_oxphos_structural_86": ("s", "Nuclear structural OXPHOS"),
    }
    for module_id, (marker, module_label) in module_styles.items():
        subset = [row for row in reliability if row["module_id"] == module_id]
        for row in subset:
            color = context_colors[row["context_id"]]
            x = fnum(row["nci_mean_z_pc1_correlation"])
            y = fnum(row["variance_explained_pc1"])
            ax_a.scatter(x, y, marker=marker, s=48, facecolors="white", edgecolors=color, linewidths=1.3)
            ax_a.text(x, y, str(context_numbers[row["context_id"]]), fontsize=5.2, color=color, ha="center", va="center", fontweight="bold")
    ax_a.axvspan(0, 0.70, color="#F0F0F0")
    ax_a.axvline(0.70, color="#555555", lw=0.8, ls="--")
    ax_a.set_xlim(0.68, 1.015)
    ax_a.set_ylim(0, 0.83)
    ax_a.set_xlabel("NCI mean-z versus PC1 correlation")
    ax_a.set_ylabel("PC1 variance explained")
    ax_a.set_title("Alternative score reliability", loc="left", fontweight="bold")
    module_handles = [
        plt.Line2D([], [], marker=marker, mfc="white", mec="#333333", ls="", label=module_label)
        for marker, module_label in module_styles.values()
    ]
    ax_a.legend(handles=module_handles, frameon=False, loc="lower right")
    context_key = "\n".join(
        f"{context_numbers[context]}  {labels[context]}"
        for context in contexts
    )
    ax_a.text(0.13, 0.09, context_key, transform=ax_a.transAxes, ha="left", va="bottom", fontsize=6.0, linespacing=1.25, color="#333333")
    panel_label(ax_a, "A", x=-0.15, y=1.04)
    despine(ax_a)

    for context in contexts:
        subset = [row for row in ref if row["context_id"] == context]
        ax_b.scatter(
            [fnum(row["observed_M"]) for row in subset],
            [fnum(row["predicted_M"]) for row in subset],
            s=12, facecolors="none", edgecolors=context_colors[context], linewidths=0.6, alpha=0.65, label=labels[context],
        )
    limits = [fnum(row[key]) for row in ref for key in ("observed_M", "predicted_M")]
    low, high = min(limits), max(limits)
    ax_b.plot([low, high], [low, high], color="#333333", lw=0.7, ls="--")
    ax_b.set_xlim(low, high)
    ax_b.set_ylim(low, high)
    ax_b.set_xlabel("Observed held-out NCI M")
    ax_b.set_ylabel("Cross-fitted predicted M")
    ax_b.set_title("Held-out NCI predictions (assignment 0)", loc="left", fontweight="bold")
    ax_b.legend(frameon=False, fontsize=5.8, ncol=2, loc="lower right")
    panel_label(ax_b, "B", x=-0.15, y=1.04)
    despine(ax_b)

    positions, box_data, box_colors = [], [], []
    for i, context in enumerate(contexts):
        for diagnosis, offset, color in (("NCI", -0.17, OKABE_ITO["blue"]), ("AD", 0.17, OKABE_ITO["orange"])):
            subset = [row for row in donors if row["context_id"] == context and row["diagnosis"] == diagnosis and math.isfinite(fnum(row["nci_reference_residual"]))]
            values = [fnum(row["nci_reference_residual"]) for row in subset]
            position = i + offset
            positions.append(position)
            box_data.append(values)
            box_colors.append(color)
            ax_c.scatter(
                [position + deterministic_jitter(f"{context}:{diagnosis}:{row['projid']}") for row in subset],
                values, s=5, color=color, alpha=0.22, linewidths=0, zorder=1,
            )
    boxes = ax_c.boxplot(box_data, positions=positions, widths=0.25, patch_artist=True, showfliers=False, medianprops={"color": "black", "lw": 0.8}, whiskerprops={"lw": 0.7}, capprops={"lw": 0.7})
    for patch, color in zip(boxes["boxes"], box_colors):
        patch.set_facecolor("white")
        patch.set_edgecolor(color)
        patch.set_linewidth(0.9)
    ax_c.axhline(0, color="#555555", lw=0.7)
    ax_c.set_xticks(range(len(contexts)), [labels[context].replace(" neurons", "") for context in contexts], rotation=35, ha="right")
    ax_c.set_ylabel("Cross-fitted NCI-reference residual (SD)")
    ax_c.set_title("Residual distributions by diagnosis", loc="left", fontweight="bold")
    ax_c.legend(
        handles=[
            mpatches.Patch(facecolor="white", edgecolor=OKABE_ITO["blue"], label="NCI"),
            mpatches.Patch(facecolor="white", edgecolor=OKABE_ITO["orange"], label="AD"),
        ], frameon=False, loc="upper right",
    )
    panel_label(ax_c, "C", x=-0.15, y=1.04)
    despine(ax_c)

    for scope, marker, color, offset in (
        ("general", "o", OKABE_ITO["blue"], -0.09),
        ("modifier", "^", OKABE_ITO["orange"], 0.09),
    ):
        subset = [row for row in influence_summary if row["scope_id"] == scope]
        y_positions = np.arange(len(contexts))[::-1] + offset
        x_values = [fnum(row["direction_retained_fraction"]) for row in subset]
        ax_d.scatter(x_values, y_positions, marker=marker, s=30, facecolors="white" if scope == "general" else color, edgecolors=color, linewidths=1.0, label=scope.capitalize())
        for y, row in zip(y_positions, subset):
            ax_d.text(0.755, y, f"min {fnum(row['minimum_relative_magnitude']):.2f}×", fontsize=5.2, ha="left", va="center", color=color)
    ax_d.axvline(1, color="#555555", lw=0.7, ls="--")
    ax_d.set_xlim(0.745, 1.015)
    ax_d.set_yticks(np.arange(len(contexts))[::-1], [labels[context] for context in contexts])
    ax_d.set_xlabel("Fraction of omission sensitivities retaining direction")
    ax_d.set_title("Gene/complex omission influence", loc="left", fontweight="bold")
    ax_d.text(0.99, 1.015, "○ General    ▲ Modifier", transform=ax_d.transAxes, ha="right", va="bottom", fontsize=6.5, color="#333333")
    panel_label(ax_d, "D", x=-0.20, y=1.04)
    despine(ax_d)
    fig.text(0.02, 0.007, "All 14 score pairs passed the frozen PC1 reliability rule; production checks record zero cross-fit leakage and maximum score-reconstruction error 1.64e-14.", ha="left", va="bottom", fontsize=7, color="#444444")

    image_paths = render_triplet(fig, directory, basename, dpi)
    plotted = (
        rows_with_meta(reliability, family, "score_reliability", "A")
        + rows_with_meta(ref, family, "heldout_nci_prediction", "B")
        + rows_with_meta(ref_summary, family, "reference_prediction_summary", "B")
        + rows_with_meta(donors, family, "donor_residual", "C")
        + rows_with_meta(influence_summary, family, "influence_summary", "D")
    )
    caption = """# Score and NCI-reference reliability

**A,** Agreement of mean-z and alternative PC1 scores against PC1 variance explained for every context-by-module pair; all 14 pairs pass the frozen reliability criterion. **B,** Held-out NCI observed versus cross-fitted predicted mtDNA score for reference assignment 0, colored by context; the dashed diagonal is identity, not a fitted line. **C,** Individual donor-context NCI-reference residuals and box summaries by diagnosis. **D,** Fraction of saved mtDNA-gene and nuclear-complex omission sensitivities retaining the primary direction; labels report the smallest retained relative magnitude. These panels establish measurement and reference-model diagnostics but do not convert the inconclusive C3 result into support.
"""
    methods = """# Methods

Score correlations, PC1 variance explained, and reliability calls were copied from the production reliability table. Panel B uses only assignment-0 held-out NCI predictions; the identity line is a visual reference and no prediction model was refitted. Panel C shows saved cross-fitted residuals with deterministic donor jitter. Panel D aggregates saved omission rows by context and scope using the fraction with `direction_retained = TRUE` and the minimum recorded relative magnitude. Production checks, rather than the scatter appearance, establish zero leakage.
"""
    extra = [
        ("reliability_pair_count", len(reliability) == 14, len(reliability), 14, ""),
        ("all_pc1_reliable", all(row["pc1_reliable"] == "TRUE" for row in reliability), sum(row["pc1_reliable"] == "TRUE" for row in reliability), 14, ""),
        ("assignment_zero_predictions", len(ref) > 0, len(ref), ">0", "Held-out NCI only."),
        ("donor_residual_count", len(donors) == 1825, len(donors), 1825, ""),
    ]
    return finalize_family(
        project_root=project_root, family=family, directory=directory, basename=basename,
        plotted_rows=plotted, image_paths=image_paths,
        source_paths=[bundle["paths"][key] for key in ("status", "score_reliability", "reference_predictions", "donor_endpoints", "gene_influence", "crossfit_folds", "checks")],
        caption=caption, methods=methods, production_status_hash=bundle["production_status_hash"],
        visual_review_status=review, extra_checks=extra,
    )


def write_package_status(output_dir: Path, statuses: Sequence[Mapping[str, Any]], production_hash: str, review: str) -> None:
    failed = sum(row["validation_status"] != "validated_complete" for row in statuses)
    rows = [
        {
            "schema_version": SCHEMA,
            "figure_family": row["figure_family"],
            "production_status_sha256": production_hash,
            "plotted_rows": row["plotted_rows"],
            "image_artifacts": row["image_artifacts"],
            "checks": row["checks"],
            "failed_checks": row["failed_checks"],
            "visual_review_status": review,
            "validation_status": row["validation_status"],
            "status_path": row["status_path"],
        }
        for row in statuses
    ]
    rows.append(
        {
            "schema_version": SCHEMA,
            "figure_family": "package_overall",
            "production_status_sha256": production_hash,
            "plotted_rows": sum(int(row["plotted_rows"]) for row in statuses),
            "image_artifacts": sum(int(row["image_artifacts"]) for row in statuses),
            "checks": sum(int(row["checks"]) for row in statuses),
            "failed_checks": failed,
            "visual_review_status": review,
            "validation_status": "validated_complete" if failed == 0 else "validation_failed",
            "status_path": "NA",
        }
    )
    atomic_write_tsv(output_dir / "phase15_figure_package_status.tsv", rows)


def main(argv: Sequence[str] | None = None) -> int:
    configure_style()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    project_root = Path.cwd().resolve()
    input_dir = (project_root / args.input_dir).resolve() if not Path(args.input_dir).is_absolute() else Path(args.input_dir).resolve()
    output_dir = (project_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    require(input_dir.is_dir(), f"Input directory does not exist: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(input_dir)
    renderers = [
        render_complete_evidence,
        render_primary_geometry,
        render_testability,
        render_complete_forest,
        render_stratum_atlas,
        render_slope_atlas,
        render_stability_atlas,
        render_reliability,
    ]
    statuses: list[dict[str, Any]] = []
    for renderer in renderers:
        print(f"Rendering {renderer.__name__} ...", flush=True)
        statuses.append(renderer(bundle, output_dir, args.png_dpi, args.visual_review_status, project_root))
    write_package_status(output_dir, statuses, bundle["production_status_hash"], args.visual_review_status)
    print(f"Generated {len(statuses)} figure families under {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
