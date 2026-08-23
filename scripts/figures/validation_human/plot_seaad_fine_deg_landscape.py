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
        "svg.hashsalt": "seaad_fine_deg_landscape_v2",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

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


SCHEMA = "seaad_fine_deg_landscape_figure_v2"
PLOT_SCHEMA = "seaad_fine_deg_landscape_plot_data_v2"
FIGURE_ID = "seaad_fine_deg_landscape"
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 5.3
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 2_385
MINIMUM_FONT_PT = 16.0
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
DEG_CONFIG_PATH = "scripts/validation_human/seaad_deg_config.yml"
VALIDATION_CONFIG_PATH = "scripts/validation_human/seaad_phase18_validation_config.yml"
INPUT_PATHS = {
    "vh08_status": "results/validation_human/08_deg/status.tsv",
    "vh08_artifacts": "results/validation_human/08_deg/artifacts.tsv",
    "vh08_checks": "results/validation_human/08_deg/deg_checks.tsv",
    "deg_summary": "results/validation_human/08_deg/deg_summary.tsv",
    "direction_summary": "results/validation_human/08_deg/query_handoff/fine_direction_deg_summary.tsv",
    "query_index": "results/validation_human/08_deg/query_handoff/fine_query_input_index.tsv",
    "contrast_status": "results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv",
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
    config_paths = {
        "deg_config": DEG_CONFIG_PATH,
        "validation_config": VALIDATION_CONFIG_PATH,
    }
    configs: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    for key, relative in config_paths.items():
        path = project_root / relative
        require(path.is_file(), f"Missing configuration: {path}")
        with path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        require(isinstance(config, dict), f"Configuration is not a mapping: {path}")
        configs[key] = config
        digests[relative] = sha256_file(path)

    frames: dict[str, pd.DataFrame] = {}
    for key, relative in INPUT_PATHS.items():
        path = project_root / relative
        digest = sha256_file(path)
        frames[key] = read_tsv(path)
        digests[relative] = digest

    deg_config = configs["deg_config"]
    validation = configs["validation_config"]["vh10"]
    analysis = validation["analysis"]
    expected = deg_config["expected_identity"]
    structural_contrasts = int(expected["fine_contrasts"])
    structural_directions = int(expected["fine_directions"])
    supertype_count = int(expected["included_supertypes"])
    donor_minimum = int(deg_config["thresholds"]["min_donors_per_disease_arm"])
    nuclei_minimum = int(deg_config["thresholds"]["primary_min_nuclei"])
    fdr_threshold = float(deg_config["thresholds"]["fdr"])
    reference_fold_change = float(
        deg_config["thresholds"]["absolute_fold_change"]
    )
    query_rule_id = str(analysis["query_rule_id"])
    result_tier_id = str(analysis["result_tier_id"])
    require(
        "posthoc_exploratory" in result_tier_id,
        "Active SEA-AD tier is not labeled post-hoc exploratory",
    )
    require(donor_minimum == 3, "Active SEA-AD donor threshold is not three per arm")
    require(
        int(analysis["minimum_effective_query_genes"]) == 3,
        "Active SEA-AD KDA minimum is not three genes",
    )
    require(
        math.isclose(float(analysis["fdr_threshold_exclusive"]), fdr_threshold),
        "DEG and VH10 FDR thresholds disagree",
    )
    query_rules = deg_config["query_rules"]
    require(query_rule_id in query_rules, "VH10 query rule is absent from DEG config")
    active_query_rule = str(query_rules[query_rule_id])
    require(
        "abs(logFC)" not in active_query_rule and "AND" not in active_query_rule,
        "Active query is not FDR-only",
    )
    reference_ids = [
        key
        for key, value in query_rules.items()
        if key != query_rule_id and "abs(logFC)" in str(value)
    ]
    require(len(reference_ids) == 1, "Phase 18 fold-change reference is not unique")
    reference_rule_id = reference_ids[0]
    reference_rule = str(query_rules[reference_rule_id])
    group_order = [
        str(row["group_id"]) for row in deg_config["cohort"]["signature_groups"]
    ]
    network_order = list(deg_config["taxonomy"]["broad_network_order"])
    network_supertype_counts = {
        str(key): int(value)
        for key, value in deg_config["taxonomy"]["expected_supertype_counts"].items()
    }
    require(
        structural_contrasts == supertype_count * len(group_order)
        and structural_directions == 2 * structural_contrasts,
        "Configured fine-grid identity is inconsistent",
    )
    require(
        list(network_supertype_counts) == network_order
        and sum(network_supertype_counts.values()) == supertype_count,
        "Configured network/supertype identity is inconsistent",
    )

    status = one_row(frames["vh08_status"], "VH08 status")
    require(status["validation_status"] == "validated_complete", "VH08 is not validated_complete")
    require(str(status["failed_checks"]).strip() == "", "VH08 reports failed checks")
    require(
        status["config_sha256"] == digests[DEG_CONFIG_PATH],
        "VH08 status does not match the active DEG config",
    )
    authority = validation["input_authority"]
    for authority_key, source_key in (
        ("vh08_status", "vh08_status"),
        ("vh08_artifacts", "vh08_artifacts"),
    ):
        item = authority[authority_key]
        require(
            item["path"] == INPUT_PATHS[source_key]
            and item["sha256"] == digests[INPUT_PATHS[source_key]],
            f"VH10 authority is stale for {authority_key}",
        )
    require(
        as_int(status["fine_structural_contrasts"]) == structural_contrasts,
        "VH08 structural contrast count disagrees with config",
    )
    require(
        as_int(status["fine_directions"]) == structural_directions,
        "VH08 direction count disagrees with config",
    )
    checks = frames["vh08_checks"]
    require_columns(checks, ["check", "passed"], "VH08 checks")
    require(checks["passed"].map(truth).all(), "VH08 contains a failed DEG check")

    for key in (
        "vh08_checks",
        "deg_summary",
        "direction_summary",
        "query_index",
        "contrast_status",
    ):
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
    require(
        len(contrast) == structural_contrasts,
        "Fine contrast row count disagrees with config",
    )
    require(not contrast["contrast_id"].duplicated().any(), "Fine contrast IDs are duplicated")
    require(contrast["deg_tier"].nunique() == 1, "Fine DEG tier is not unique")
    deg_tier_id = str(contrast["deg_tier"].iloc[0])
    require(set(contrast["signature_group"]) == set(group_order), "Signature groups disagree with config")
    require(set(contrast["broad_network"]) == set(network_order), "Broad networks disagree with config")
    require(set(contrast["terminal_status"]) == {"completed", "not_estimable"}, "Terminal statuses changed")

    fine = frames["deg_summary"].loc[
        frames["deg_summary"]["deg_tier"].eq(deg_tier_id)
    ].copy()
    require_columns(
        fine,
        ["contrast_id", "terminal_status", "fdr_significant", "phase18_parity"],
        "fine DEG summary",
    )
    require(
        len(fine) == structural_contrasts
        and not fine["contrast_id"].duplicated().any(),
        "Fine DEG summary keys disagree with the contrast manifest",
    )
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
    merged["active_count"] = _numeric(merged, "fdr_significant")
    merged["reference_count"] = _numeric(merged, "phase18_parity")
    completed = merged["terminal_status"].eq("completed")
    require(merged.loc[completed, "active_count"].notna().all(), "Completed active counts are missing")
    require(merged.loc[completed, "reference_count"].notna().all(), "Completed reference counts are missing")
    require(merged.loc[~completed, "active_count"].isna().all(), "Not-estimable active counts are populated")
    require(merged.loc[~completed, "reference_count"].isna().all(), "Not-estimable reference counts are populated")
    require(
        merged.loc[completed, "reference_count"].le(
            merged.loc[completed, "active_count"]
        ).all(),
        "Phase 18 reference hits are not a subset of FDR-only hits",
    )

    network_counts = (
        merged[["supertype_id", "broad_network"]]
        .drop_duplicates()
        .groupby("broad_network")
        .size()
        .astype(int)
        .to_dict()
    )
    require(
        network_counts == network_supertype_counts,
        "Fine-supertype network counts disagree with config",
    )
    status_counts = merged.groupby(["signature_group", "terminal_status"]).size().to_dict()
    observed_group_status = {
        group: (
            int(status_counts.get((group, "completed"), 0)),
            int(status_counts.get((group, "not_estimable"), 0)),
        )
        for group in group_order
    }

    query_index = frames["query_index"].copy()
    active_rule_column = f"{query_rule_id}_rule"
    reference_rule_column = f"{reference_rule_id}_rule"
    require_columns(
        query_index,
        [
            "contrast_id",
            active_rule_column,
            reference_rule_column,
            "authoritative_query_membership_frozen",
        ],
        "fine query input index",
    )
    completed_ids = set(merged.loc[completed, "contrast_id"])
    require(
        set(query_index["contrast_id"]) == completed_ids
        and not query_index["contrast_id"].duplicated().any(),
        "Fine query index does not identify each completed contrast exactly once",
    )
    require(
        set(query_index[active_rule_column]) == {active_query_rule}
        and set(query_index[reference_rule_column]) == {reference_rule},
        "Query-index rules disagree with config",
    )
    require(
        not query_index["authoritative_query_membership_frozen"].map(truth).any(),
        "VH08 improperly froze downstream query membership",
    )

    directions = frames["direction_summary"].copy()
    require_columns(
        directions,
        [
            "direction_slot_id",
            "contrast_id",
            "signature_group",
            "deg_direction",
            "deg_tier",
            "source_terminal_status",
            "fdr_significant_tested_feature_count",
            "phase18_parity_tested_feature_count",
        ],
        "fine direction summary",
    )
    require(
        len(directions) == structural_directions,
        "Fine direction summary row count disagrees with config",
    )
    require(not directions["direction_slot_id"].duplicated().any(), "Direction slot IDs are duplicated")
    require(set(directions["deg_tier"]) == {deg_tier_id}, "Direction DEG tier disagrees with contrasts")
    ready = directions.loc[directions["source_terminal_status"].eq("completed")].copy()
    ready["active_count"] = _numeric(
        ready, "fdr_significant_tested_feature_count"
    )
    ready["reference_count"] = _numeric(
        ready, "phase18_parity_tested_feature_count"
    )
    require(
        len(ready) == 2 * int(completed.sum())
        and ready[["active_count", "reference_count"]].notna().all().all(),
        "Completed direction handoff does not pair completed contrasts",
    )
    signed_totals = {
        (group, direction): int(value)
        for (group, direction), value in ready.groupby(
            ["signature_group", "deg_direction"]
        )["active_count"].sum().items()
    }
    for count_column in ("active_count", "reference_count"):
        by_contrast = ready.groupby("contrast_id")[count_column].sum().sort_index()
        expected_by_contrast = (
            merged.loc[completed].set_index("contrast_id")[count_column].sort_index()
        )
        require(
            by_contrast.index.equals(expected_by_contrast.index)
            and np.array_equal(
                by_contrast.to_numpy(dtype=float),
                expected_by_contrast.to_numpy(dtype=float),
            ),
            f"Direction totals do not reconstruct contrast {count_column}",
        )

    completed_contrasts = int(completed.sum())
    not_estimable_contrasts = int((~completed).sum())
    require(
        as_int(status["fine_completed"]) == completed_contrasts
        and as_int(status["fine_not_estimable"]) == not_estimable_contrasts,
        "VH08 status disagrees with contrast terminal states",
    )
    require(
        as_int(status["query_ready_directions"]) == len(ready),
        "VH08 status disagrees with ready directions",
    )
    total_active = int(merged["active_count"].sum())
    total_reference = int(merged["reference_count"].sum())
    signal_contrasts = int(merged["active_count"].fillna(0).gt(0).sum())
    group_active_totals = {
        group: int(
            merged.loc[merged["signature_group"].eq(group), "active_count"].sum()
        )
        for group in group_order
    }
    dominant_group = max(group_order, key=group_active_totals.get)
    dominant_group_hits = group_active_totals[dominant_group]
    dominant_group_share = (
        100.0 * dominant_group_hits / total_active if total_active else 0.0
    )
    plotted_groups = [
        group for group in group_order if observed_group_status[group][0] > 0
    ]
    require("M_e4" in plotted_groups, "Donor-3 rerun did not add completed M_e4 contrasts")

    supertype_totals = (
        merged.groupby(["supertype_id", "broad_network"], as_index=False)["active_count"]
        .sum()
        .rename(columns={"active_count": "supertype_total"})
    )
    network_rank = {network: index for index, network in enumerate(network_order)}
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
        "analysis_role": "posthoc_exploratory",
        "query_rule_id": query_rule_id,
        "active_query_rule": active_query_rule,
        "reference_rule_id": reference_rule_id,
        "reference_rule": reference_rule,
        "result_tier_id": result_tier_id,
        "deg_tier_id": deg_tier_id,
        "donor_minimum": donor_minimum,
        "nuclei_minimum": nuclei_minimum,
        "fdr_threshold": fdr_threshold,
        "reference_fold_change": reference_fold_change,
        "group_order": group_order,
        "plotted_groups": plotted_groups,
        "network_order": network_order,
        "network_supertype_counts": network_supertype_counts,
        "observed_group_status": observed_group_status,
        "structural_contrasts": structural_contrasts,
        "structural_directions": structural_directions,
        "supertype_count": supertype_count,
        "completed_contrasts": completed_contrasts,
        "not_estimable_contrasts": not_estimable_contrasts,
        "merged": merged,
        "supertype_totals": supertype_totals,
        "signed_totals": signed_totals,
        "total_active": total_active,
        "total_reference": total_reference,
        "signal_contrasts": signal_contrasts,
        "dominant_group": dominant_group,
        "dominant_group_hits": dominant_group_hits,
        "dominant_group_share": dominant_group_share,
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
        "analysis_role": "",
        "query_rule_id": "",
        "result_tier_id": "",
        "deg_tier_id": "",
        "donor_minimum_per_arm": "",
        "fdr_threshold_exclusive": "",
        "reference_fold_change": "",
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    merged = bundle["merged"]
    group_order = bundle["group_order"]
    group_rank = {group: index for index, group in enumerate(group_order)}
    cells = merged.sort_values(
        ["row_order", "signature_group"],
        key=lambda values: values.map(group_rank) if values.name == "signature_group" else values,
        kind="stable",
    )
    for row in cells.itertuples(index=False):
        record = _empty_record("heatmap_cell", f"cell::{row.contrast_id}")
        count = "" if row.terminal_status == "not_estimable" else int(row.active_count)
        value = "" if count == "" else f"{math.log10(1 + count):.9f}"
        record.update(
            {
                "display_order": int(row.row_order) * len(group_order) + group_rank[row.signature_group],
                "broad_network": row.broad_network,
                "broad_network_label": NETWORK_LABELS.get(
                    row.broad_network, row.broad_network.replace("_", " ")
                ),
                "supertype_id": row.supertype_id,
                "supertype_label": row.supertype_label,
                "row_order": int(row.row_order),
                "signature_group": row.signature_group,
                "terminal_status": row.terminal_status,
                "raw_count": count,
                "plot_value": value,
                "metric_id": f"{bundle['query_rule_id']}_feature_contrast_hits",
                "display_value": count,
                "display_label": "FDR-only active hits",
            }
        )
        rows.append(record)

    direction_order = {"Dementia_down": 0, "Dementia_up": 1}
    for group_index, group in enumerate(bundle["plotted_groups"]):
        for direction in ("Dementia_down", "Dementia_up"):
            count = int(bundle["signed_totals"].get((group, direction), 0))
            record = _empty_record("signed_group_total", f"signed::{group}::{direction}")
            record.update(
                {
                    "display_order": group_index * 2 + direction_order[direction],
                    "signature_group": group,
                    "deg_direction": direction,
                    "raw_count": count,
                    "plot_value": f"{math.log10(1 + count):.9f}",
                    "metric_id": f"{bundle['query_rule_id']}_feature_contrast_hits",
                    "display_value": f"{count:,}",
                    "display_label": "Dementia down" if direction.endswith("down") else "Dementia up",
                }
            )
            rows.append(record)

    chip_values = [
        (
            "completed_contrasts",
            f"{bundle['completed_contrasts']:,} / {bundle['structural_contrasts']:,}",
            "completed contrasts",
        ),
        ("active_query_hits", f"{bundle['total_active']:,}", "FDR-only active hits"),
        (
            "reference_hits",
            f"{bundle['total_reference']:,}",
            f"{bundle['reference_fold_change']:g}-fold reference hits",
        ),
        (
            "signal_contrasts",
            f"{bundle['signal_contrasts']:,}",
            "contrasts with active signal",
        ),
        (
            "dominant_group_share",
            f"{bundle['dominant_group_share']:.1f}%",
            f"active hits in {bundle['dominant_group']}",
        ),
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
    frame["analysis_role"] = bundle["analysis_role"]
    frame["query_rule_id"] = bundle["query_rule_id"]
    frame["result_tier_id"] = bundle["result_tier_id"]
    frame["deg_tier_id"] = bundle["deg_tier_id"]
    frame["donor_minimum_per_arm"] = bundle["donor_minimum"]
    frame["fdr_threshold_exclusive"] = bundle["fdr_threshold"]
    frame["reference_fold_change"] = bundle["reference_fold_change"]
    expected_records = (
        bundle["structural_contrasts"]
        + 2 * len(bundle["plotted_groups"])
        + len(chip_values)
    )
    require(
        len(frame) == expected_records,
        f"Expected {expected_records} plot records, observed {len(frame)}",
    )
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
    fig.text(0.645, 0.958, "B  Signed FDR-only totals", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.020, 0.879, "POST-HOC EXPLORATORY", ha="left", va="center", fontsize=16, weight="bold", color=UP)
    _draw_status_key(fig)
    fig.text(0.825, 0.877, "mirrored log10 scale • exact counts", ha="center", va="center", fontsize=16, color=MID)

    heat_ax = fig.add_axes([0.200, 0.205, 0.390, 0.610])
    merged = bundle["merged"]
    group_order = bundle["group_order"]
    network_order = bundle["network_order"]
    matrix = np.full(
        (bundle["supertype_count"], len(group_order)), -0.25, dtype=float
    )
    group_rank = {group: index for index, group in enumerate(group_order)}
    for row in merged.itertuples(index=False):
        i = int(row.row_order)
        j = group_rank[row.signature_group]
        if row.terminal_status == "completed":
            matrix[i, j] = math.log10(1 + int(row.active_count))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "white_to_navy", ["#FFFFFF", "#C9D7E7", "#6F98BE", NAVY]
    )
    cmap.set_under(NOT_ESTIMABLE)
    maximum = max(1.0, float(matrix.max()))
    image = heat_ax.imshow(
        matrix,
        origin="upper",
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        norm=mcolors.Normalize(vmin=0, vmax=maximum),
    )
    heat_ax.set_xticks(range(len(group_order)), group_order)
    heat_ax.xaxis.tick_top()
    heat_ax.tick_params(axis="x", length=0, pad=6, labelsize=16)
    heat_ax.set_yticks([])
    heat_ax.set_xlim(-1.0, len(group_order) - 0.5)
    for spine in heat_ax.spines.values():
        spine.set_visible(False)

    supertype_totals = bundle["supertype_totals"]
    start = 0
    label_y_positions = np.linspace(0.765, 0.255, len(network_order))
    for network, label_y in zip(network_order, label_y_positions):
        count = bundle["network_supertype_counts"][network]
        center = start + (count - 1) / 2
        network_color = NETWORK_COLORS.get(network, NAVY)
        network_label = NETWORK_LABELS.get(network, network.replace("_", " "))
        heat_ax.add_patch(
            mpatches.Rectangle(
                (-0.72, start - 0.5), 0.22, count,
                facecolor=network_color, edgecolor="none", clip_on=False,
            )
        )
        fig.text(0.177, label_y, network_label, ha="right", va="center", fontsize=16, color=TEXT)
        fig.add_artist(
            mpatches.ConnectionPatch(
                xyA=(0.183, label_y), coordsA=fig.transFigure,
                xyB=(-0.73, center), coordsB=heat_ax.transData,
                color=network_color, linewidth=1.3, zorder=5,
            )
        )
        if start > 0:
            heat_ax.axhline(start - 0.5, color=WHITE, linewidth=1.2, zorder=4)
        observed = supertype_totals.loc[supertype_totals["broad_network"].eq(network)]
        require(len(observed) == count, f"Network row count changed for {network}")
        start += count
    require(
        start == bundle["supertype_count"],
        "Network bands do not cover all configured supertype rows",
    )
    for x in np.arange(0.5, len(group_order) - 0.5, 1):
        heat_ax.axvline(x, color=WHITE, linewidth=0.8, alpha=0.9)

    color_ax = fig.add_axes([0.602, 0.245, 0.014, 0.52])
    colorbar = fig.colorbar(image, cax=color_ax)
    ticks = [0, maximum / 2, maximum]
    colorbar.set_ticks(ticks)
    colorbar.set_ticklabels(["0", f"{maximum / 2:.1f}", f"{maximum:.1f}"])
    colorbar.ax.tick_params(labelsize=16, length=3)
    colorbar.outline.set_linewidth(0.8)

    bar_ax = fig.add_axes([0.675, 0.220, 0.30, 0.54])
    plotted_groups = bundle["plotted_groups"]
    require(plotted_groups, "No completed groups are available for Panel B")
    y_positions = np.linspace(4.5, 0.0, len(plotted_groups))
    down_counts = np.array(
        [bundle["signed_totals"].get((group, "Dementia_down"), 0) for group in plotted_groups]
    )
    up_counts = np.array(
        [bundle["signed_totals"].get((group, "Dementia_up"), 0) for group in plotted_groups]
    )
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
    for y, group in zip(y_positions, plotted_groups):
        bar_ax.text(
            0,
            y + 0.39,
            group,
            ha="center",
            va="center",
            fontsize=16,
            weight="bold",
            color=TEXT,
            bbox={"facecolor": WHITE, "edgecolor": "none", "pad": 0.3},
        )
    maximum_width = max(1.0, float(max(down_widths.max(), up_widths.max())))
    bar_ax.set_xlim(-(maximum_width + 1.4), maximum_width + 1.4)
    bar_ax.set_ylim(-0.58, 5.25)
    bar_ax.set_xticks([])
    for spine in bar_ax.spines.values():
        spine.set_visible(False)
    bar_ax.text(0.23, 1.04, "▼ Dementia-down", transform=bar_ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=DOWN)
    bar_ax.text(0.77, 1.04, "▲ Dementia-up", transform=bar_ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=UP)
    fig.text(0.825, 0.177, "Feature–contrast incidences", ha="center", va="center", fontsize=16, color=MID)

    chips = [
        (
            f"{bundle['completed_contrasts']:,} / {bundle['structural_contrasts']:,}",
            "completed\ncontrasts",
        ),
        (f"{bundle['total_active']:,}", "FDR-only active\nhits"),
        (
            f"{bundle['total_reference']:,}",
            f"{bundle['reference_fold_change']:g}-fold reference\nhits",
        ),
        (f"{bundle['signal_contrasts']:,}", "contrasts with\nactive signal"),
        (
            f"{bundle['dominant_group_share']:.1f}%",
            f"active hits\nin {bundle['dominant_group']}",
        ),
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
    svg_path = next(path for path in paths if path.suffix == ".svg")
    write_text(
        svg_path,
        "\n".join(
            line.rstrip()
            for line in svg_path.read_text(encoding="utf-8").splitlines()
        ),
    )
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
    expected_records = (
        bundle["structural_contrasts"]
        + 2 * len(bundle["plotted_groups"])
        + 5
    )
    checks = [
        record("vh08_validated", True, "validated_complete", "validated_complete", "Validated during input loading."),
        record("compact_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS) + 2, len(bundle["input_digests"]), len(INPUT_PATHS) + 2, "Every consumed compact source and config has a full-file SHA-256; bulky unconsumed shards are not required."),
        record("posthoc_exploratory_label", bundle["analysis_role"] == "posthoc_exploratory", bundle["analysis_role"], "posthoc_exploratory", "The amended SEA-AD analysis is labeled post-hoc exploratory."),
        record("donor_three_protocol", bundle["donor_minimum"] == 3, bundle["donor_minimum"], 3, "Minimum donors per disease arm."),
        record("active_query_is_fdr_only", "abs(logFC)" not in bundle["active_query_rule"], bundle["active_query_rule"], f"FDR < {bundle['fdr_threshold']:g}", "The active heatmap measure has no fold-change gate."),
        record("phase18_rule_is_reference", bundle["reference_fold_change"] > 1, bundle["reference_rule"], "auxiliary 1.3-fold reference", "The inherited fold gate is reported only as reference context."),
        record("m_e4_included", "M_e4" in bundle["plotted_groups"], "|".join(bundle["plotted_groups"]), "contains M_e4", "The donor-3 rerun contributes completed M_e4 contrasts."),
        record("heatmap_cell_count", len(cells) == bundle["structural_contrasts"], len(cells), bundle["structural_contrasts"], "One cell per configured fine-supertype contrast."),
        record("heatmap_keys_unique", not cells[["supertype_id", "signature_group"]].duplicated().any(), "unique", "unique", "Each supertype–group cell is unique."),
        record("heatmap_supertype_count", cells["supertype_id"].nunique() == bundle["supertype_count"], cells["supertype_id"].nunique(), bundle["supertype_count"], "All configured supertypes are represented."),
        record("completed_contrast_count", cells["terminal_status"].eq("completed").sum() == bundle["completed_contrasts"], cells["terminal_status"].eq("completed").sum(), bundle["completed_contrasts"], "Completed contrast cells agree with VH08 status."),
        record("not_estimable_count", cells["terminal_status"].eq("not_estimable").sum() == bundle["not_estimable_contrasts"], cells["terminal_status"].eq("not_estimable").sum(), bundle["not_estimable_contrasts"], "Not-estimable contrast cells agree with VH08 status."),
        record("signed_totals", observed_signed == bundle["signed_totals"], str(observed_signed), str(bundle["signed_totals"]), "Exact Dementia-up/down FDR-only totals."),
        record("active_total", bundle["total_active"] == int(bundle["merged"]["active_count"].sum()), bundle["total_active"], int(bundle["merged"]["active_count"].sum()), "FDR-only feature–contrast incidences."),
        record("reference_total", bundle["total_reference"] == int(bundle["merged"]["reference_count"].sum()), bundle["total_reference"], int(bundle["merged"]["reference_count"].sum()), "Phase 18 reference incidences."),
        record("reference_subset", bundle["total_reference"] <= bundle["total_active"], bundle["total_reference"], f"<= {bundle['total_active']}", "Reference hits are a subset of active FDR-only hits."),
        record("signal_contrasts", bundle["signal_contrasts"] == int(bundle["merged"]["active_count"].fillna(0).gt(0).sum()), bundle["signal_contrasts"], int(bundle["merged"]["active_count"].fillna(0).gt(0).sum()), "Completed contrasts with active signal."),
        record("result_chip_count", len(chips) == 5, len(chips), 5, "Five exact result chips."),
        record("plot_record_count", len(plot_data) == expected_records, len(plot_data), expected_records, "Heatmap, signed totals, and chips."),
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


def documentation(bundle: Mapping[str, Any]) -> tuple[str, str]:
    caption = f"""# SEA-AD fine-supertype DEG landscape: caption

**Post-hoc exploratory SEA-AD differential-expression signal remained concentrated in {bundle['dominant_group']} after lowering donor support to {bundle['donor_minimum']} per disease arm and removing the active fold-change gate.** The heatmap shows all {bundle['supertype_count']} retained SEA-AD supertypes across the {len(bundle['group_order'])} fixed sex/APOE groups. Completed cells are colored by `log10(1 + FDR-only feature–contrast hits)` under `{bundle['active_query_rule']}`; gray cells were not estimable and white cells were completed with zero active hits. Supertypes are grouped by the {len(bundle['network_order'])} broad networks and ordered within network by total active-hit count. Mirrored bars show exact Dementia-up and Dementia-down totals for the {len(bundle['plotted_groups'])} groups with completed contrasts, including M_e4. Of {bundle['structural_contrasts']:,} structural contrasts, {bundle['completed_contrasts']:,} completed and {bundle['signal_contrasts']:,} contained at least one FDR-only hit. There were {bundle['total_active']:,} active FDR-only incidences; {bundle['total_reference']:,} also met the auxiliary {bundle['reference_fold_change']:g}-fold Phase 18 reference gate. {bundle['dominant_group']} contributed {bundle['dominant_group_hits']:,} ({bundle['dominant_group_share']:.1f}%) active incidences. Counts are feature–contrast incidences, not unique genes.
"""
    methods = f"""# SEA-AD fine-supertype DEG landscape: methods

The renderer reads the validated VH08 status and compact registered checks, fine contrast status, direction handoff, query index, and DEG summary together with the active DEG and VH10 configurations. It validates only consumed compact files against the VH08 artifact manifest; absent bulky DEG shards, filters, and diagnostics are not figure inputs. Status/config and VH10-authority hashes must agree. The active post-hoc exploratory query is `{bundle['query_rule_id']}` (`{bundle['active_query_rule']}`), with at least {bundle['donor_minimum']} donors per disease arm and at least {bundle['nuclei_minimum']} nuclei per profile. The inherited `{bundle['reference_rule_id']}` rule (`{bundle['reference_rule']}`) is auxiliary context only. The heatmap uses the `{bundle['deg_tier_id']}` tier and {bundle['result_tier_id']} protocol identity. Each completed cell is the sum of its Dementia-up and Dementia-down FDR-only feature hits; direction-level counts must independently reconstruct the contrast total. Not-estimable cells remain distinct from completed zero-hit cells. Rows follow the configured network order, then descending active hits and stable `supertype_id`. Bars use `log10(1 + count)` length while printing untransformed counts. Broad pooled/stratified tiers and ROSMAP candidate identities are not used.

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
    require(
        len(plot_data) == as_int(status["plot_data_rows"])
        and plot_data["record_id"].is_unique,
        "Published plot data changed",
    )
    for column in (
        "analysis_role",
        "query_rule_id",
        "result_tier_id",
        "deg_tier_id",
        "donor_minimum_per_arm",
        "fdr_threshold_exclusive",
        "reference_fold_change",
    ):
        require(column in plot_data.columns, f"Published plot data lacks {column}")
        require(
            plot_data[column].astype(str).nunique() == 1,
            f"Published plot-data protocol field is not unique: {column}",
        )
    require(
        set(plot_data["analysis_role"].astype(str)) == {"posthoc_exploratory"},
        "Published plot data is not labeled post-hoc exploratory",
    )
    require(
        set(pd.to_numeric(plot_data["donor_minimum_per_arm"], errors="raise"))
        == {3},
        "Published plot data does not retain the donor-three amendment",
    )
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
        caption, methods = documentation(bundle)
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
                    "analysis_role": bundle["analysis_role"],
                    "query_rule_id": bundle["query_rule_id"],
                    "result_tier_id": bundle["result_tier_id"],
                    "deg_tier_id": bundle["deg_tier_id"],
                    "donor_minimum_per_arm": bundle["donor_minimum"],
                    "fdr_threshold_exclusive": bundle["fdr_threshold"],
                    "reference_fold_change": bundle["reference_fold_change"],
                    "fine_contrasts": bundle["structural_contrasts"],
                    "completed_contrasts": bundle["completed_contrasts"],
                    "not_estimable_contrasts": bundle["not_estimable_contrasts"],
                    "active_fdr_only_hits": bundle["total_active"],
                    "phase18_reference_hits": bundle["total_reference"],
                    "active_signal_contrasts": bundle["signal_contrasts"],
                    "plotted_groups": "|".join(bundle["plotted_groups"]),
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
