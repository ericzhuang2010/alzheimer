#!/usr/bin/env python3
"""Render the frozen ROSMAP/SEA-AD top-driver gene set comparison.

This is a descriptive gene-symbol view.  It collapses broad-network identity
and does not recompute candidate selection, strict replication, or an overlap
P value.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_venn_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_venn_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "seaad_rosmap_top_driver_gene_venn_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "hatch.linewidth": 0.55,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402
from PIL import Image  # noqa: E402
import pandas as pd  # noqa: E402


SCHEMA = "seaad_rosmap_top_driver_gene_venn_v1"
PLOT_SCHEMA = "seaad_rosmap_top_driver_gene_venn_plot_data_v1"
SUMMARY_SCHEMA = "seaad_rosmap_top_driver_gene_venn_region_summary_v1"
FIGURE_ID = "seaad_rosmap_top_driver_gene_venn"
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 7.2
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 3_240
RADIUS_FACTOR = 0.43

QUERY_RULE = "fdr_only_query_sensitivity"
RESULT_TIER = "posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05"
CLASS_ORDER = ["mt_driver", "non_mt_driver"]
CLASS_LABELS = {"mt_driver": "MT driver class", "non_mt_driver": "Non-MT driver class"}

ROSMAP_FILL = "#DCEEF7"
ROSMAP_EDGE = "#0072B2"
SEAAD_FILL = "#FBE6C5"
SEAAD_EDGE = "#D55E00"
COMMON_FILL = "#E8DCEB"
TEXT = "#202020"
MID = "#5E6670"
WHITE = "#FFFFFF"

OUTPUT_FILES = [
    f"{FIGURE_ID}.png",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_region_summary.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_artifacts.tsv",
    f"{FIGURE_ID}_status.tsv",
]
PAYLOAD_FILES = OUTPUT_FILES[:8]

INPUT_PATHS = {
    "vh09_status": "results/validation_human/09_rosmap_kda_candidates/status.tsv",
    "vh09_artifacts": "results/validation_human/09_rosmap_kda_candidates/artifacts.tsv",
    "vh09_checks": "results/validation_human/09_rosmap_kda_candidates/candidate_freeze_checks.tsv",
    "rosmap_selected": "results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv",
    "vh10c_status": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv",
    "vh10c_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/artifacts.tsv",
    "vh10c_checks": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/selection_checks.tsv",
    "seaad_top5": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv",
    "seaad_freeze": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_selection_freeze.tsv",
    "vh10d_status": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/status.tsv",
    "vh10d_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/artifacts.tsv",
    "vh10d_checks": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/overlap_checks.tsv",
    "unit_overlap": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv",
    "gene_overlap": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_gene_only_overlap.tsv",
}

EXPECTED_INPUT_SHA256 = {
    "vh09_status": "e5504ef3edb8264064d40b8307ded3f2277e9230e39f1029162aba4b11f52568",
    "vh09_artifacts": "9cb622cb3d1affc93eac21d598d51ada31b5f74a2355f477cce78c6cbe6f6ced",
    "vh09_checks": "74cacf128d42e62d63780a1e7f2658fec4dee0b701d5c8009c59e6df6614b8a8",
    "rosmap_selected": "e758720f7dcd80d1d6ef72fc7f95bfa20e3784931114e59c716a0e85b681d443",
    "vh10c_status": "490bd9d785584c471c5acfc2b1834f2b3e670f25833a89c0c280048540cef43e",
    "vh10c_artifacts": "c154e3013b9ff473cbc66a6e7c2710978b5014c56faff8b8f915452073dcf0dc",
    "vh10c_checks": "3595944ac839e1b2b91494ecf6e4f0e6a74a01fe30340e1f9bc406b03d977f49",
    "seaad_top5": "31dd58753e2d205e56028cd71f73323bdde11385c1f1cd041a6157318a63ab97",
    "seaad_freeze": "2db010c801b1d03907ca8850e1e9b8a064531ce6e4396a688f9c39ff6c331bf6",
    "vh10d_status": "1e80ad3914e12a63e7bd6f5ee005eebd4889bc32a3dc952e48c2b1575c12ac5e",
    "vh10d_artifacts": "fc15576f85f1d53670ff2efe211256c6f0f4d27b6f609fbbad5b4fa8b6c90f41",
    "vh10d_checks": "83e1413b1b9b30b9e11c643bc837070ec6278d1f88ee299c1bb9caf1e95cc5c3",
    "unit_overlap": "2230ac092af573402df9a6c6041c552648efccdc29176118c0b6dc83d72700f6",
    "gene_overlap": "729bd92d24125e39b92331cfbc846cc30976c68bffa9d9d48767686871b233fc",
}

EXPECTED_REGIONS = {
    "mt_driver": {
        "rosmap_only": {"COX4I1", "COX6B1", "COX7C", "UQCR10"},
        "common": {"MT-ATP6", "MT-CO2", "MT-CO3", "MT-CYB", "MT-ND4", "MT-ND5"},
        "seaad_only": set(),
    },
    "non_mt_driver": {
        "rosmap_only": {
            "ANKRD11", "APOE", "ATP6V1F", "DYNLT1", "FTL", "LAMTOR5",
            "LAPTM4A", "NCOA1", "RPL11", "RPL15", "RPL38", "RPLP1",
            "RPS13", "RPS15", "SELENOW",
        },
        "common": set(),
        "seaad_only": {"BEX3", "HGSNAT", "RPS27A"},
    },
}


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
        parser.error(f"--png-dpi must equal the frozen value {DEFAULT_PNG_DPI}")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "t", "1", "yes"}


def as_int(value: Any, label: str = "value") -> int:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Expected integer {label}, observed {value!r}") from exc
    rounded = int(round(number))
    require(math.isfinite(number) and abs(number - rounded) < 1e-9, f"Expected integer {label}")
    return rounded


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    require(path.is_file(), f"Missing TSV: {path}")
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, sep="\t", index=False, lineterminator="\n")
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def one_row(frame: pd.DataFrame, label: str) -> pd.Series:
    require(len(frame) == 1, f"Expected one row in {label}, observed {len(frame)}")
    return frame.iloc[0]


def require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    require(not missing, f"Missing columns in {label}: {missing}")


def validate_source_artifact(manifest: pd.DataFrame, relative: str, digest: str) -> None:
    require_columns(manifest, ["path", "digest_algorithm", "digest_scope", "digest_value"], "source artifact manifest")
    rows = manifest.loc[manifest["path"].eq(relative)]
    require(len(rows) == 1, f"Input is not uniquely registered: {relative}")
    row = rows.iloc[0]
    require(row["digest_algorithm"] == "sha256", f"Non-SHA256 registration: {relative}")
    require(row["digest_scope"] == "full_file", f"Non-full-file registration: {relative}")
    require(row["digest_value"] == digest, f"Registered digest mismatch: {relative}")


def _memberships_by_gene(frame: pd.DataFrame, gene_column: str) -> dict[tuple[str, str], str]:
    answer: dict[tuple[str, str], str] = {}
    for (case_id, gene), group in frame.groupby(["case_id", gene_column], sort=True):
        answer[(case_id, gene)] = "|".join(sorted(set(group["broad_network"])))
    return answer


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

    vh09 = one_row(frames["vh09_status"], "VH09 status")
    vh10c = one_row(frames["vh10c_status"], "VH10C status")
    vh10d = one_row(frames["vh10d_status"], "VH10D status")
    for label, row in (("VH09", vh09), ("VH10C", vh10c), ("VH10D", vh10d)):
        require(row["validation_status"] == "validated_complete", f"{label} is not validated_complete")
        require(str(row.get("failed_checks", "")).strip() == "", f"{label} reports failed checks")
    for label in ("vh09_checks", "vh10c_checks", "vh10d_checks"):
        checks = frames[label]
        require_columns(checks, ["passed"], label)
        require(checks["passed"].map(truth).all(), f"Failed upstream check in {label}")

    require(as_int(vh09["selected_units"]) == 47, "ROSMAP selected-unit count changed")
    require(as_int(vh09["selected_unique_genes"]) == 25, "ROSMAP unique-gene count changed")
    require(vh09["selected_sha256"] == EXPECTED_INPUT_SHA256["rosmap_selected"], "ROSMAP status digest changed")
    require(as_int(vh10c["selected_top5_units"]) == 11, "SEA-AD selected-unit count changed")
    require(as_int(vh10c["selected_unique_genes"]) == 9, "SEA-AD unique-gene count changed")
    require(as_int(vh10d["rosmap_selected_units"]) == 47, "VH10D ROSMAP count changed")
    require(as_int(vh10d["seaad_selected_units"]) == 11, "VH10D SEA-AD count changed")
    require(as_int(vh10d["shared_unique_genes"]) == 6, "VH10D shared-gene count changed")

    registrations = {
        "vh09_checks": "vh09_artifacts",
        "rosmap_selected": "vh09_artifacts",
        "vh10c_checks": "vh10c_artifacts",
        "seaad_top5": "vh10c_artifacts",
        "seaad_freeze": "vh10c_artifacts",
        "vh10d_checks": "vh10d_artifacts",
        "unit_overlap": "vh10d_artifacts",
        "gene_overlap": "vh10d_artifacts",
    }
    for key, manifest_key in registrations.items():
        validate_source_artifact(frames[manifest_key], INPUT_PATHS[key], digests[INPUT_PATHS[key]])

    freeze = one_row(frames["seaad_freeze"], "SEA-AD freeze")
    require(not truth(freeze["rosmap_candidate_files_read"]), "SEA-AD freeze was not ROSMAP blind")
    require(freeze["query_rule_id"] == QUERY_RULE, "SEA-AD query rule changed")
    require(freeze["result_tier_id"] == RESULT_TIER, "SEA-AD result tier changed")
    require(as_int(freeze["selected_top5_units"]) == 11, "SEA-AD freeze count changed")
    require(freeze["top5_sha256"] == EXPECTED_INPUT_SHA256["seaad_top5"], "SEA-AD freeze digest changed")

    rosmap = frames["rosmap_selected"].copy()
    require_columns(rosmap, ["broad_network", "key_driver", "case_id", "top5_display"], "ROSMAP selected units")
    require(rosmap["top5_display"].map(truth).all(), "ROSMAP file contains non-display rows")
    require(len(rosmap) == 47, "ROSMAP selected table does not contain 47 units")
    require(set(rosmap["case_id"]) == set(CLASS_ORDER), "ROSMAP driver classes changed")

    seaad_all = frames["seaad_top5"].copy()
    require_columns(seaad_all, ["query_rule_id", "result_tier_id", "broad_network", "case_id", "list_status", "current_symbol"], "SEA-AD top list")
    require(set(seaad_all["query_rule_id"]) == {QUERY_RULE}, "SEA-AD query rule changed")
    require(set(seaad_all["result_tier_id"]) == {RESULT_TIER}, "SEA-AD result tier changed")
    seaad = seaad_all.loc[seaad_all["list_status"].eq("ranked_candidates")].copy()
    require(len(seaad) == 11, "SEA-AD ranked table does not contain 11 units")
    require(~seaad["current_symbol"].isin({"", "NA"}).any(), "SEA-AD ranked row has a sentinel symbol")
    require(set(seaad["case_id"]) == set(CLASS_ORDER), "SEA-AD driver classes changed")

    rosmap_sets = {case: set(rosmap.loc[rosmap["case_id"].eq(case), "key_driver"]) for case in CLASS_ORDER}
    seaad_sets = {case: set(seaad.loc[seaad["case_id"].eq(case), "current_symbol"]) for case in CLASS_ORDER}
    require(not (rosmap_sets["mt_driver"] & rosmap_sets["non_mt_driver"]), "ROSMAP gene assigned to both classes")
    require(not (seaad_sets["mt_driver"] & seaad_sets["non_mt_driver"]), "SEA-AD gene assigned to both classes")
    require({case: len(rosmap_sets[case]) for case in CLASS_ORDER} == {"mt_driver": 10, "non_mt_driver": 15}, "ROSMAP class gene counts changed")
    require({case: len(seaad_sets[case]) for case in CLASS_ORDER} == {"mt_driver": 6, "non_mt_driver": 3}, "SEA-AD class gene counts changed")

    regions: dict[str, dict[str, set[str]]] = {}
    for case in CLASS_ORDER:
        regions[case] = {
            "rosmap_only": rosmap_sets[case] - seaad_sets[case],
            "common": rosmap_sets[case] & seaad_sets[case],
            "seaad_only": seaad_sets[case] - rosmap_sets[case],
        }
        require(regions[case] == EXPECTED_REGIONS[case], f"Frozen region identities changed for {case}")

    unit_overlap = frames["unit_overlap"]
    require_columns(unit_overlap, ["result_tier_id", "gene", "case_id", "rosmap_top5", "seaad_top5"], "unit overlap")
    require(set(unit_overlap["result_tier_id"]) == {RESULT_TIER}, "Unit-overlap tier changed")
    unit_rosmap = {case: set(unit_overlap.loc[unit_overlap["case_id"].eq(case) & unit_overlap["rosmap_top5"].map(truth), "gene"]) for case in CLASS_ORDER}
    unit_seaad = {case: set(unit_overlap.loc[unit_overlap["case_id"].eq(case) & unit_overlap["seaad_top5"].map(truth), "gene"]) for case in CLASS_ORDER}
    require(unit_rosmap == rosmap_sets, "Class-specific overlap does not reproduce ROSMAP sets")
    require(unit_seaad == seaad_sets, "Class-specific overlap does not reproduce SEA-AD sets")

    gene_overlap = frames["gene_overlap"]
    require_columns(gene_overlap, ["gene", "rosmap_top5_any_network_class", "seaad_top5_any_network_class", "shared_gene"], "gene-only overlap")
    require(set(gene_overlap.loc[gene_overlap["rosmap_top5_any_network_class"].map(truth), "gene"]) == set().union(*rosmap_sets.values()), "Gene-only ROSMAP cross-check changed")
    require(set(gene_overlap.loc[gene_overlap["seaad_top5_any_network_class"].map(truth), "gene"]) == set().union(*seaad_sets.values()), "Gene-only SEA-AD cross-check changed")
    require(set(gene_overlap.loc[gene_overlap["shared_gene"].map(truth), "gene"]) == regions["mt_driver"]["common"], "Gene-only common set changed")

    input_bundle_sha256 = sha256_strings(f"{path}\t{digest}" for path, digest in sorted(digests.items()))
    return {
        "project_root": project_root,
        "frames": frames,
        "input_digests": digests,
        "input_bundle_sha256": input_bundle_sha256,
        "rosmap": rosmap,
        "seaad": seaad,
        "regions": regions,
        "rosmap_memberships": _memberships_by_gene(rosmap, "key_driver"),
        "seaad_memberships": _memberships_by_gene(seaad, "current_symbol"),
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for case in CLASS_ORDER:
        for region in ("rosmap_only", "common", "seaad_only"):
            for order, gene in enumerate(sorted(bundle["regions"][case][region]), start=1):
                rows.append(
                    {
                        "schema_version": PLOT_SCHEMA,
                        "figure_id": FIGURE_ID,
                        "case_id": case,
                        "case_label": CLASS_LABELS[case],
                        "gene": gene,
                        "region": region,
                        "region_order": order,
                        "rosmap_selected": region in {"rosmap_only", "common"},
                        "seaad_selected": region in {"seaad_only", "common"},
                        "rosmap_networks": bundle["rosmap_memberships"].get((case, gene), ""),
                        "seaad_networks": bundle["seaad_memberships"].get((case, gene), ""),
                    }
                )
    frame = pd.DataFrame(rows)
    require(len(frame) == 28, f"Expected 28 class-gene rows, observed {len(frame)}")
    require(not frame.duplicated(["case_id", "gene"]).any(), "Plot keys are duplicated")
    return frame


def radius(n: int) -> float:
    return RADIUS_FACTOR * math.sqrt(n)


def build_region_summary(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows = []
    for case in CLASS_ORDER:
        regions = bundle["regions"][case]
        rosmap_n = len(regions["rosmap_only"] | regions["common"])
        seaad_n = len(regions["seaad_only"] | regions["common"])
        nested = case == "mt_driver"
        rosmap_x = 0.0 if nested else -1.55
        seaad_x = 0.25 if nested else 1.25
        center_distance = abs(seaad_x - rosmap_x)
        x_min, x_max = ((-2.2, 2.2) if nested else (-3.35, 2.55))
        y_min, y_max = ((-1.8, 2.0) if nested else (-1.9, 1.95))
        for region in ("rosmap_only", "common", "seaad_only"):
            rows.append({
                "schema_version": SUMMARY_SCHEMA,
                "figure_id": FIGURE_ID,
                "case_id": case,
                "region": region,
                "region_count": len(regions[region]),
                "region_genes": "|".join(sorted(regions[region])),
                "rosmap_unique_genes": rosmap_n,
                "seaad_unique_genes": seaad_n,
                "rosmap_radius": f"{radius(rosmap_n):.9f}",
                "seaad_radius": f"{radius(seaad_n):.9f}",
                "radius_rule": "0.43*sqrt(unique_gene_count)",
                "geometry": "nested_containment" if nested else "disjoint",
                "rosmap_center_x": f"{rosmap_x:.9f}",
                "seaad_center_x": f"{seaad_x:.9f}",
                "center_y": "0.000000000",
                "center_distance": f"{center_distance:.9f}",
                "geometry_margin": f"{(radius(rosmap_n) - radius(seaad_n) - center_distance) if nested else (center_distance - radius(rosmap_n) - radius(seaad_n)):.9f}",
                "panel_x_min": f"{x_min:.9f}",
                "panel_x_max": f"{x_max:.9f}",
                "panel_y_min": f"{y_min:.9f}",
                "panel_y_max": f"{y_max:.9f}",
            })
    return pd.DataFrame(rows)


def _label_grid(ax: Any, genes: list[str], xs: Sequence[float], ys: Sequence[float], *, size: float = 8.2) -> None:
    positions = [(x, y) for y in ys for x in xs]
    require(len(positions) >= len(genes), "Insufficient label-grid positions")
    for gene, (x, y) in zip(genes, positions):
        ax.text(x, y, gene, ha="center", va="center", fontsize=size, color=TEXT, zorder=8)


def _draw_mt(ax: Any, regions: Mapping[str, set[str]]) -> None:
    r_ros = radius(10)
    r_sea = radius(6)
    ros_center = (0.0, 0.0)
    sea_center = (0.25, 0.0)
    ax.add_patch(Circle(ros_center, r_ros, facecolor=ROSMAP_FILL, edgecolor=ROSMAP_EDGE, linewidth=1.5, zorder=1))
    ax.add_patch(Circle(sea_center, r_sea, facecolor=COMMON_FILL, edgecolor=SEAAD_EDGE, linewidth=1.5, linestyle=(0, (5, 3)), hatch="///", zorder=2))
    ax.text(-1.08, 1.13, "ROSMAP Phase 18 • 10", ha="center", va="center", fontsize=9.3, weight="bold", color=ROSMAP_EDGE)
    ax.text(0.35, 0.82, "SEA-AD • 6", ha="center", va="center", fontsize=9.3, weight="bold", color=SEAAD_EDGE)
    ax.text(0.31, 0.56, "Common • 6", ha="center", va="center", fontsize=9.0, weight="bold", color=TEXT)
    _label_grid(ax, sorted(regions["common"]), (-0.10, 0.68), (0.26, -0.04, -0.34), size=8.4)

    # The crescent is too narrow for four full symbols at slide size, so use a
    # direct, leader-linked callout anchored to the exposed ROSMAP-only area.
    ax.annotate(
        "ROSMAP only • 4\n" + "\n".join(sorted(regions["rosmap_only"])),
        xy=(-1.04, 0.0), xycoords="data", xytext=(-2.05, 0.0), textcoords="data",
        ha="center", va="center", fontsize=8.3, color=TEXT,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": WHITE, "edgecolor": ROSMAP_EDGE, "linewidth": 1.0},
        arrowprops={"arrowstyle": "-", "color": ROSMAP_EDGE, "linewidth": 1.0}, zorder=9,
    )
    ax.text(0.35, -1.25, "SEA-AD only: 0 (∅)", ha="center", va="center", fontsize=8.2, color=MID)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-1.8, 2.0)


def _draw_non_mt(ax: Any, regions: Mapping[str, set[str]]) -> None:
    r_ros = radius(15)
    r_sea = radius(3)
    ros_center = (-1.55, 0.0)
    sea_center = (1.25, 0.0)
    ax.add_patch(Circle(ros_center, r_ros, facecolor=ROSMAP_FILL, edgecolor=ROSMAP_EDGE, linewidth=1.5, zorder=1))
    ax.add_patch(Circle(sea_center, r_sea, facecolor=SEAAD_FILL, edgecolor=SEAAD_EDGE, linewidth=1.5, linestyle=(0, (5, 3)), hatch="///", zorder=2))
    ax.text(-1.55, 1.38, "ROSMAP Phase 18 • 15", ha="center", va="center", fontsize=9.3, weight="bold", color=ROSMAP_EDGE)
    ax.text(1.25, 0.58, "SEA-AD • 3", ha="center", va="center", fontsize=9.3, weight="bold", color=SEAAD_EDGE)
    ax.text(-1.55, 1.07, "ROSMAP only • 15", ha="center", va="center", fontsize=8.7, weight="bold", color=TEXT)
    display_genes = [f"{gene}†" if gene in {"ANKRD11", "FTL", "NCOA1"} else gene for gene in sorted(regions["rosmap_only"])]
    _label_grid(ax, display_genes, (-2.37, -1.55, -0.73), (0.68, 0.34, 0.0, -0.34, -0.68), size=7.7)
    ax.text(1.25, 0.30, "SEA-AD only • 3", ha="center", va="center", fontsize=8.7, weight="bold", color=TEXT)
    _label_grid(ax, sorted(regions["seaad_only"]), (1.25,), (0.02, -0.23, -0.48), size=8.2)
    ax.text(0.45, 1.52, "Common: 0 (∅)", ha="center", va="center", fontsize=8.7, weight="bold", color=TEXT)
    ax.text(0.45, 1.29, "No shared top-list gene", ha="center", va="center", fontsize=7.7, color=MID)
    ax.text(-1.55, -1.48, "† SEA-AD OPC KDA unavailable", ha="center", va="center", fontsize=7.2, color=MID)
    ax.set_xlim(-3.35, 2.55)
    ax.set_ylim(-1.9, 1.95)


def draw_figure(bundle: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    fig.subplots_adjust(left=0.035, right=0.985, bottom=0.135, top=0.82, wspace=0.06)
    fig.text(0.5, 0.94, "Gene-level overlap of selected top key drivers", ha="center", va="center", fontsize=18, weight="bold", color=TEXT)
    fig.text(0.5, 0.895, "Unique symbols; networks collapsed • SEA-AD post-hoc exploratory", ha="center", va="center", fontsize=10.5, color=MID)
    for index, (ax, case) in enumerate(zip(axes, CLASS_ORDER)):
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.set_title(CLASS_LABELS[case], fontsize=12.2, weight="bold", color=TEXT, pad=12)
        ax.text(0.0, 1.055, "AB"[index], transform=ax.transAxes, ha="left", va="bottom", fontsize=15, weight="bold", color=TEXT)
        if case == "mt_driver":
            _draw_mt(ax, bundle["regions"][case])
            ax.text(0.5, 1.005, "Phase 18 core MitoCarta; not mtDNA-only", transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5, color=MID)
        else:
            _draw_non_mt(ax, bundle["regions"][case])
        ax.text(0.5, -0.055, "Area proportional to unique-gene count", transform=ax.transAxes, ha="center", va="top", fontsize=7.3, color=MID)
    fig.text(0.5, 0.045, "Descriptive gene-level view • networks collapsed • no overlap P value", ha="center", va="center", fontsize=8.0, color=MID)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    visible_text = list(fig.texts) + [text for ax in axes for text in ax.texts]
    minimum_font = min(text.get_fontsize() for text in visible_text if text.get_visible() and text.get_text())
    fig_bbox = fig.bbox
    clipped = []
    for artist in visible_text:
        if not artist.get_visible() or not artist.get_text():
            continue
        bbox = artist.get_window_extent(renderer=renderer)
        if bbox.x0 < fig_bbox.x0 - 1 or bbox.y0 < fig_bbox.y0 - 1 or bbox.x1 > fig_bbox.x1 + 1 or bbox.y1 > fig_bbox.y1 + 1:
            clipped.append(artist.get_text())
    require(not clipped, "Text leaves canvas: " + " | ".join(clipped))
    require(minimum_font >= 7.0, f"Minimum font too small: {minimum_font}")
    return fig, {"minimum_font_points": minimum_font, "canvas_clipped_text": clipped}


def render_images(bundle: Mapping[str, Any], staging: Path, dpi: int) -> tuple[list[Path], dict[str, Any]]:
    fig, meta = draw_figure(bundle)
    paths = []
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{FIGURE_ID}.{extension}"
        temporary = staging / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata = {"Title": "ROSMAP and SEA-AD top-driver gene overlap", "Creator": "Validation-human figure renderer", "CreationDate": None, "ModDate": None}
        elif extension == "svg":
            metadata = {"Title": "ROSMAP and SEA-AD top-driver gene overlap", "Creator": "Validation-human figure renderer", "Date": None}
        else:
            metadata = {"Software": "Validation-human figure renderer"}
        fig.savefig(temporary, format=extension, dpi=dpi if extension == "png" else None, facecolor=WHITE, bbox_inches=None, pad_inches=0, metadata=metadata)
        if extension == "svg":
            normalize_svg_whitespace(temporary)
        require(temporary.stat().st_size > 1000, f"Rendered file is too small: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths, meta


def normalize_svg_whitespace(path: Path) -> None:
    """Strip line-end whitespace while preserving one final newline."""
    raw = path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in raw.splitlines()) + "\n"
    if normalized != raw:
        path.write_text(normalized, encoding="utf-8")
    require(
        not any(line != line.rstrip() for line in normalized.splitlines()),
        f"SVG retains trailing whitespace: {path}",
    )


def check_record(check_id: str, passed: bool, observed: Any, expected: Any, details: str, *, severity: str = "blocking", status: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA, "figure_id": FIGURE_ID, "check_id": check_id,
        "severity": severity, "status": status or ("pass" if passed else "fail"),
        "observed": observed, "expected": expected, "details": details,
    }


def image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    checks = [
        check_record("image_export_set", set(lookup) == {".png", ".pdf", ".svg"}, "|".join(sorted(lookup)), ".pdf|.png|.svg", "Three image formats."),
        check_record("image_exports_nonempty", all(path.stat().st_size > 1000 for path in image_paths), "all >1000" if all(path.stat().st_size > 1000 for path in image_paths) else "small file", "all >1000", "Image exports are nontrivial."),
    ]
    svg = lookup[".svg"].read_text(encoding="utf-8").lower()
    checks.extend([
        check_record("svg_searchable_text", "<text" in svg, "present" if "<text" in svg else "missing", "present", "SVG text remains searchable."),
        check_record("svg_vector_paths", "<path" in svg, "present" if "<path" in svg else "missing", "present", "SVG includes vector paths."),
        check_record("svg_no_trailing_whitespace", not any(line != line.rstrip() for line in svg.splitlines()), "none", "none", "SVG lines have no trailing whitespace."),
        check_record("pdf_signature", lookup[".pdf"].read_bytes()[:5] == b"%PDF-", lookup[".pdf"].read_bytes()[:5].decode("latin1"), "%PDF-", "PDF signature is valid."),
    ])
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        embedded = image.info.get("dpi", (math.nan, math.nan))
        mode = image.mode
    checks.extend([
        check_record("png_dimensions", (width, height) == (PNG_WIDTH, PNG_HEIGHT), f"{width}x{height}", f"{PNG_WIDTH}x{PNG_HEIGHT}", "PNG dimensions are frozen."),
        check_record("png_resolution", all(math.isfinite(v) and abs(v - dpi) <= 1 for v in embedded), f"{embedded[0]:.2f}|{embedded[1]:.2f}", f"{dpi}|{dpi}", "Embedded PNG resolution."),
        check_record("png_color_mode", mode in {"RGB", "RGBA"}, mode, "RGB or RGBA", "Slide-compatible color mode."),
    ])
    return checks


def build_checks(bundle: Mapping[str, Any], plot_data: pd.DataFrame, summary: pd.DataFrame, image_paths: Sequence[Path], render_meta: Mapping[str, Any], dpi: int, visual_review_status: str) -> pd.DataFrame:
    observed_counts = {(row.case_id, row.region): as_int(row.region_count) for row in summary.itertuples(index=False)}
    expected_counts = {("mt_driver", "rosmap_only"): 4, ("mt_driver", "common"): 6, ("mt_driver", "seaad_only"): 0, ("non_mt_driver", "rosmap_only"): 15, ("non_mt_driver", "common"): 0, ("non_mt_driver", "seaad_only"): 3}
    mt_geometry = summary.loc[summary["case_id"].eq("mt_driver")].iloc[0]
    non_mt_geometry = summary.loc[summary["case_id"].eq("non_mt_driver")].iloc[0]
    svg_text = next(path for path in image_paths if path.suffix == ".svg").read_text(encoding="utf-8")
    all_gene_labels = all(gene in svg_text for gene in plot_data["gene"])
    both_empty_labels = "SEA-AD only: 0 (∅)" in svg_text and "Common: 0 (∅)" in svg_text
    geometry_fields = {
        "mt_driver": (0.0, 0.25, 0.0, -2.2, 2.2, -1.8, 2.0),
        "non_mt_driver": (-1.55, 1.25, 0.0, -3.35, 2.55, -1.9, 1.95),
    }
    observed_geometry_fields = {
        case: tuple(float(summary.loc[summary["case_id"].eq(case)].iloc[0][column]) for column in ("rosmap_center_x", "seaad_center_x", "center_y", "panel_x_min", "panel_x_max", "panel_y_min", "panel_y_max"))
        for case in CLASS_ORDER
    }
    checks = [
        check_record("upstream_phases_complete", True, "VH09|VH10C|VH10D validated_complete", "VH09|VH10C|VH10D validated_complete", "Validated during loading."),
        check_record("frozen_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS), len(bundle["input_digests"]), len(INPUT_PATHS), "Every compact input matches its frozen SHA-256."),
        check_record("seaad_rosmap_blinded_freeze", True, "False", "False", "SEA-AD was frozen before ROSMAP unblinding."),
        check_record("selected_unit_counts", len(bundle["rosmap"]) == 47 and len(bundle["seaad"]) == 11, f"{len(bundle['rosmap'])}|{len(bundle['seaad'])}", "47|11", "Selected network-gene units."),
        check_record("unique_gene_counts", bundle["rosmap"]["key_driver"].nunique() == 25 and bundle["seaad"]["current_symbol"].nunique() == 9, f"{bundle['rosmap']['key_driver'].nunique()}|{bundle['seaad']['current_symbol'].nunique()}", "25|9", "Unique symbols after network collapse."),
        check_record("plot_row_count", len(plot_data) == 28, len(plot_data), 28, "Unique class-gene rows."),
        check_record("plot_keys_unique", not plot_data.duplicated(["case_id", "gene"]).any(), "unique", "unique", "No gene is duplicated within a class."),
        check_record("region_summary_rows", len(summary) == 6, len(summary), 6, "All three regions are explicit in both classes, including zero-count regions."),
        check_record("region_counts", observed_counts == expected_counts, str(observed_counts), str(expected_counts), "Frozen MT and non-MT regions."),
        check_record("region_gene_identities", all(bundle["regions"][case] == EXPECTED_REGIONS[case] for case in CLASS_ORDER), "exact", "exact", "All gene labels match the frozen region lists."),
        check_record("common_area_scale", summary["radius_rule"].eq("0.43*sqrt(unique_gene_count)").all(), "0.43*sqrt(n)", "0.43*sqrt(n)", "One area-per-gene scale across panels."),
        check_record("geometry_logic", summary.set_index("case_id")["geometry"].to_dict() == {"mt_driver": "nested_containment", "non_mt_driver": "disjoint"}, str(summary.set_index("case_id")["geometry"].to_dict()), "MT nested|non-MT disjoint", "Zero regions are represented honestly."),
        check_record("frozen_geometry_fields", observed_geometry_fields == geometry_fields, str(observed_geometry_fields), str(geometry_fields), "Circle centers and panel limits match the designed layout."),
        check_record("mt_containment_inequality", float(mt_geometry["center_distance"]) + float(mt_geometry["seaad_radius"]) <= float(mt_geometry["rosmap_radius"]), mt_geometry["geometry_margin"], ">=0", "SEA-AD MT circle is fully contained."),
        check_record("non_mt_disjoint_inequality", float(non_mt_geometry["center_distance"]) >= float(non_mt_geometry["rosmap_radius"]) + float(non_mt_geometry["seaad_radius"]), non_mt_geometry["geometry_margin"], ">=0", "Non-MT circles are separated."),
        check_record("svg_all_gene_labels", all_gene_labels, int(sum(gene in svg_text for gene in plot_data["gene"])), 28, "Every frozen region gene is searchable SVG text."),
        check_record("exploratory_tier_visible", "SEA-AD post-hoc exploratory" in svg_text, "present" if "SEA-AD post-hoc exploratory" in svg_text else "missing", "present", "The revised SEA-AD analysis tier is visible."),
        check_record("svg_empty_set_labels", both_empty_labels, "both present" if both_empty_labels else "missing", "both present", "Both zero regions are stated with the empty-set symbol."),
        check_record("minimum_font_size", render_meta["minimum_font_points"] >= 7.0, render_meta["minimum_font_points"], ">=7.0", "Minimum visible font."),
        check_record("canvas_text_clipping", not render_meta["canvas_clipped_text"], len(render_meta["canvas_clipped_text"]), 0, "No text leaves the canvas."),
    ]
    checks.extend(image_checks(image_paths, dpi))
    if visual_review_status == "complete":
        checks.append(check_record("visual_review", True, "complete", "complete", "Reviewed at slide size in color and grayscale.", severity="nonblocking"))
    else:
        checks.append(check_record("visual_review", False, "pending", "complete", "Manual color/grayscale review remains pending.", severity="nonblocking", status="pending"))
    frame = pd.DataFrame(checks)
    blocking = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking.empty, "Blocking checks failed: " + ", ".join(blocking["check_id"]))
    return frame


def documentation() -> tuple[str, str]:
    caption = """# ROSMAP–SEA-AD top-driver gene Venn figure: caption

**Gene-level overlap of selected ROSMAP Phase 18 and SEA-AD top key drivers.** Selected symbols were deduplicated across broad-network top-five lists within each driver class. The MT diagram shows exact containment: all six SEA-AD MT genes occurred somewhere in the ten-gene ROSMAP MT set, while four MT genes were ROSMAP only. MT-ATP6 and MT-ND4 are common at gene level but were selected in different broad networks, so they are not strict same-network rediscoveries. The non-MT sets were disjoint: 15 ROSMAP genes and three SEA-AD genes with no shared symbol. Daggers mark ANKRD11, FTL, and NCOA1, which were ROSMAP OPC-only selections; SEA-AD had no included OPC KDA run, so their absence is not a tested negative. Circle area is proportional to unique-gene count. This descriptive comparison ignores network identity and has no overlap P value; strict replication is defined separately by broad network, gene, and driver class within the common assessable universe. SEA-AD is the post-hoc exploratory FDR-only donor-3/query-3/coverage-80%/aggregate-q-0.05 result.
"""
    methods = f"""# ROSMAP–SEA-AD top-driver gene Venn figure: methods

The renderer reads the validated VH09 ROSMAP Phase 18 selected units and independently frozen VH10C SEA-AD top lists, then uses compact VH10D overlap tables only as cross-checks. It requires `validated_complete` upstream statuses, zero failed upstream checks, registered full-file SHA-256 values, `rosmap_candidate_files_read = False`, and the exact `{QUERY_RULE}` / `{RESULT_TIER}` SEA-AD selection contract. That SEA-AD contract is explicitly post-hoc exploratory: FDR < 0.05 with no fold-change cutoff, at least three donors in each disease arm, effective query size ≥ 3, aggregate coverage ≥ 0.80, aggregate BH q ≤ 0.05, and at least one qualifying supporting run. The frozen ROSMAP Phase 18 list retains its original selection rules. The renderer does not read the full candidate universes or recompute selection.

Top-display rows are split by exact `case_id` and gene symbols are deduplicated across broad networks. Circle area follows `radius = 0.43 × sqrt(unique genes)` with the same scale in both panels. Because SEA-AD MT is a strict subset of ROSMAP MT, those circles are nested. Because the non-MT intersection is empty, those circles are disjoint. Every gene is printed alphabetically within its region; no P value is calculated for this descriptive view. Fill, outline style, hatch, direct labels, and counts provide redundant encoding. SVG and PDF are vector exports, and SVG text remains searchable. The PNG is 5400 × 3240 at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/{Path(__file__).name} \\
  --output-root results/figures/validation_human/{FIGURE_ID} \\
  --visual-review-status pending
```
"""
    return caption, methods


def table_rows(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA"
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0)


def build_artifacts(bundle: Mapping[str, Any], staging: Path, renderer: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for relative, digest in sorted(bundle["input_digests"].items()):
        path = bundle["project_root"] / relative
        rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "input", "logical_name": relative, "path": relative, "bytes": path.stat().st_size, "sha256": digest, "rows": table_rows(path), "validation_state": "validated_frozen_input"})
    relative_renderer = str(renderer.relative_to(bundle["project_root"]))
    rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "script", "logical_name": "renderer", "path": relative_renderer, "bytes": renderer.stat().st_size, "sha256": sha256_file(renderer), "rows": "NA", "validation_state": "validated_script"})
    for name in PAYLOAD_FILES:
        path = staging / name
        require(path.is_file() and path.stat().st_size > 0, f"Missing payload: {name}")
        rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "output", "logical_name": name, "path": name, "bytes": path.stat().st_size, "sha256": sha256_file(path), "rows": table_rows(path), "validation_state": "validated_output"})
    frame = pd.DataFrame(rows)
    require(frame["path"].is_unique, "Artifact paths are duplicated")
    require(set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Output artifact scope changed")
    require(not frame["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status entered hash scope")
    return frame


def validate_output(project_root: Path, output_root: Path, *, expected_visual_status: str | None = None) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(output_root.is_dir(), f"Missing output directory: {output_root}")
    require(sorted(path.name for path in output_root.iterdir() if path.is_file()) == sorted(OUTPUT_FILES), "Output package file set changed")
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
    require(set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Artifact output scope changed")
    require(not artifacts["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status is self-hashed")
    require(len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1, "Expected one script artifact")
    for row in artifacts.itertuples(index=False):
        path = output_root / row.path if row.artifact_role == "output" else project_root / row.path
        require(path.is_file(), f"Missing artifact: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact digest changed: {row.path}")
    plot = read_tsv(output_root / f"{FIGURE_ID}_plot_data.tsv")
    require(len(plot) == 28 and not plot.duplicated(["case_id", "gene"]).any(), "Published plot data changed")
    summary = read_tsv(output_root / f"{FIGURE_ID}_region_summary.tsv")
    require(len(summary) == 6 and not summary.duplicated(["case_id", "region"]).any() and set(summary["geometry"]) == {"nested_containment", "disjoint"}, "Published region summary changed")
    require(all(row["status"] == "pass" for row in image_checks([output_root / f"{FIGURE_ID}.{extension}" for extension in ("png", "pdf", "svg")], as_int(status["png_dpi"]))), "Published image checks failed")
    print(f"ROSMAP/SEA-AD gene Venn package validation passed: {output_root}")


def replace_output_package(staging: Path, output_root: Path) -> None:
    """Atomically replace a package and remove its recovery copy on success."""
    backup: Path | None = None
    try:
        if output_root.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            backup = output_root.parent / f".{output_root.name}.backup.{timestamp}.{os.getpid()}"
            output_root.replace(backup)
        staging.replace(output_root)
    except Exception:
        if backup is not None and backup.exists() and not output_root.exists():
            backup.replace(output_root)
        raise
    else:
        if backup is not None and backup.exists():
            shutil.rmtree(backup)


def publish(project_root: Path, output_root: Path, *, dpi: int, visual_review_status: str, force: bool) -> None:
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
        summary = build_region_summary(bundle)
        image_paths, render_meta = render_images(bundle, staging, dpi)
        write_tsv(plot_data, staging / f"{FIGURE_ID}_plot_data.tsv")
        write_tsv(summary, staging / f"{FIGURE_ID}_region_summary.tsv")
        caption, methods = documentation()
        write_text(staging / f"{FIGURE_ID}_caption.md", caption)
        write_text(staging / f"{FIGURE_ID}_methods.md", methods)
        checks = build_checks(bundle, plot_data, summary, image_paths, render_meta, dpi, visual_review_status)
        write_tsv(checks, staging / f"{FIGURE_ID}_checks.tsv")
        renderer = Path(__file__).resolve()
        artifacts = build_artifacts(bundle, staging, renderer)
        artifacts_path = staging / f"{FIGURE_ID}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        validation_status = "validated_complete" if visual_review_status == "complete" and pending == 0 else "awaiting_visual_review"
        status = pd.DataFrame([{
            "schema_version": SCHEMA, "figure_id": FIGURE_ID,
            "validation_status": validation_status, "visual_review_status": visual_review_status,
            "failed_blocking_checks": int(((checks["severity"] == "blocking") & (checks["status"] != "pass")).sum()),
            "pending_nonblocking_checks": int(((checks["severity"] == "nonblocking") & (checks["status"] != "pass")).sum()),
            "input_bundle_sha256": bundle["input_bundle_sha256"], "renderer_sha256": sha256_file(renderer),
            "artifact_manifest_sha256": sha256_file(artifacts_path), "figure_width_inches": FIGURE_WIDTH_IN,
            "figure_height_inches": FIGURE_HEIGHT_IN, "png_dpi": dpi, "png_width": PNG_WIDTH,
            "png_height": PNG_HEIGHT, "input_files": len(bundle["input_digests"]), "output_files": len(OUTPUT_FILES),
            "plot_data_rows": len(plot_data), "rosmap_selected_units": len(bundle["rosmap"]),
            "seaad_selected_units": len(bundle["seaad"]), "rosmap_unique_genes": bundle["rosmap"]["key_driver"].nunique(),
            "seaad_unique_genes": bundle["seaad"]["current_symbol"].nunique(), "common_unique_genes": 6,
            "contract_scope": "frozen_gene_level_descriptive_comparison", "completed_utc": datetime.now(timezone.utc).isoformat(),
        }])
        write_tsv(status, staging / f"{FIGURE_ID}_status.tsv")
        validate_output(project_root, staging, expected_visual_status=visual_review_status)
        replace_output_package(staging, output_root)
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
    publish(project_root, resolve(project_root, args.output_root), dpi=args.png_dpi, visual_review_status=args.visual_review_status, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
