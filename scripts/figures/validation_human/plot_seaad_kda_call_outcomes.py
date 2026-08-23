#!/usr/bin/env python3
"""Render slide-ready SEA-AD KDA call outcomes and selection sequence."""

from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_kda_call_outcomes_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_kda_call_outcomes_fontcache"
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
        "svg.hashsalt": "seaad_kda_call_outcomes_v2",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
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


SCHEMA = "seaad_kda_call_outcomes_figure_v2"
PLOT_SCHEMA = "seaad_kda_call_outcomes_plot_data_v2"
FIGURE_ID = "seaad_kda_call_outcomes"
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
DIRECTION_ORDER = ["up", "down"]
DIRECTION_LABELS = {"up": "Dementia-up", "down": "Dementia-down"}
DIRECTION_MARKERS = {"up": "^", "down": "v"}

DEG_CONFIG_PATH = "scripts/validation_human/seaad_deg_config.yml"
VALIDATION_CONFIG_PATH = "scripts/validation_human/seaad_phase18_validation_config.yml"
INPUT_PATHS = {
    "vh10b_status": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv",
    "vh10b_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/artifacts.tsv",
    "run_qc": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/run_qc.tsv",
    "vh10c_status": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv",
    "vh10c_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/artifacts.tsv",
    "selection_checks": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/selection_checks.tsv",
    "selection_freeze": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_selection_freeze.tsv",
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
SEAAD = "#009E73"
ORANGE = "#E69F00"
NO_RETURN = "#D9DDE1"
NO_RETURN_EDGE = "#69737D"
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
    vh10 = configs["validation_config"]["vh10"]
    analysis = vh10["analysis"]
    selection = vh10["selection"]
    query_rule_id = str(analysis["query_rule_id"])
    result_tier_id = str(analysis["result_tier_id"])
    fdr_threshold = float(analysis["fdr_threshold_exclusive"])
    query_gene_minimum = int(analysis["minimum_effective_query_genes"])
    donor_minimum = int(deg_config["thresholds"]["min_donors_per_disease_arm"])
    reference_fold_change = float(deg_config["thresholds"]["absolute_fold_change"])
    query_rules = deg_config["query_rules"]
    require(query_rule_id in query_rules, "VH10 query rule is absent from DEG config")
    active_query_rule = str(query_rules[query_rule_id])
    require(
        "posthoc_exploratory" in result_tier_id,
        "Active SEA-AD tier is not labeled post-hoc exploratory",
    )
    require(
        donor_minimum == 3,
        "Active SEA-AD donor threshold is not three per disease arm",
    )
    require(
        "abs(logFC)" not in active_query_rule and "AND" not in active_query_rule,
        "Active SEA-AD KDA query is not FDR-only",
    )
    require(
        math.isclose(float(deg_config["thresholds"]["fdr"]), fdr_threshold),
        "DEG and VH10 FDR thresholds disagree",
    )
    minimum_coverage = float(selection["minimum_coverage"])
    aggregate_q_threshold = float(selection["aggregate_q_threshold"])
    minimum_support = int(selection["minimum_conservative_supporting_runs"])
    display_limit = int(selection["display_limit"])
    require(
        math.isclose(minimum_coverage, 0.80),
        "Authoritative VH10 coverage threshold is not the retained 0.80",
    )
    require(
        math.isclose(aggregate_q_threshold, 0.05),
        "Authoritative VH10 aggregate-q threshold is not the retained 0.05",
    )
    require(query_gene_minimum == 3, "Active KDA minimum is not three query genes")
    network_order = [str(value) for value in vh10["network_order"]]
    require(
        len(network_order) == len(NETWORK_LABELS)
        and set(network_order) == set(NETWORK_LABELS),
        "Configured VH10 network order changed",
    )
    configured_directions = [str(value) for value in analysis["directions"]]
    direction_map = {"AD_up_mito": "up", "AD_down_mito": "down"}
    require(
        set(configured_directions) == set(direction_map),
        "Configured signed query directions changed",
    )

    status_b = one_row(frames["vh10b_status"], "VH10B status")
    status_c = one_row(frames["vh10c_status"], "VH10C status")
    for label, status in (("VH10B", status_b), ("VH10C", status_c)):
        require(status["validation_status"] == "validated_complete", f"{label} is not validated_complete")
        require(str(status["failed_checks"]).strip() == "", f"{label} reports failed checks")
        require(
            status["config_sha256"] == digests[VALIDATION_CONFIG_PATH],
            f"{label} status does not match the active VH10 config",
        )

    selection_checks = frames["selection_checks"]
    require_columns(selection_checks, ["check", "passed"], "VH10C selection checks")
    require(selection_checks["passed"].map(truth).all(), "VH10C contains a failed selection check")
    validate_source_artifact(
        frames["vh10b_artifacts"], INPUT_PATHS["run_qc"], digests[INPUT_PATHS["run_qc"]]
    )
    validate_source_artifact(
        frames["vh10c_artifacts"],
        INPUT_PATHS["selection_checks"],
        digests[INPUT_PATHS["selection_checks"]],
    )
    validate_source_artifact(
        frames["vh10c_artifacts"],
        INPUT_PATHS["selection_freeze"],
        digests[INPUT_PATHS["selection_freeze"]],
    )

    freeze = one_row(frames["selection_freeze"], "VH10C selection freeze")
    require_columns(
        frames["selection_freeze"],
        [
            "query_rule_id",
            "result_tier_id",
            "minimum_coverage",
            "aggregate_q_threshold",
            "minimum_conservative_supporting_runs",
            "candidate_units",
            "passing_candidate_units",
            "selected_top5_units",
            "selected_unique_genes",
            "config_sha256",
            "rosmap_candidate_files_read",
            "freeze_status",
        ],
        "VH10C selection freeze",
    )
    require(
        freeze["query_rule_id"] == query_rule_id
        and freeze["result_tier_id"] == result_tier_id,
        "VH10C freeze query/tier identity disagrees with config",
    )
    require(
        math.isclose(float(freeze["minimum_coverage"]), minimum_coverage)
        and math.isclose(float(freeze["aggregate_q_threshold"]), aggregate_q_threshold)
        and as_int(freeze["minimum_conservative_supporting_runs"])
        == minimum_support,
        "VH10C freeze thresholds disagree with config",
    )
    require(
        freeze["config_sha256"] == digests[VALIDATION_CONFIG_PATH],
        "VH10C freeze does not match the active config",
    )
    require(
        status_c["freeze_sha256"] == digests[INPUT_PATHS["selection_freeze"]],
        "VH10C status does not identify the consumed freeze",
    )
    require(
        not truth(freeze["rosmap_candidate_files_read"])
        and freeze["freeze_status"] == "independent_seaad_selection_frozen",
        "SEA-AD selection was not frozen before ROSMAP candidate unblinding",
    )

    runs = frames["run_qc"].copy()
    require_columns(
        runs,
        [
            "kda_run_id",
            "broad_network",
            "signature_group",
            "signature_direction",
            "effective_query_genes",
            "significant_key_drivers",
            "terminal_status",
        ],
        "KDA run QC",
    )
    require(
        len(runs) == as_int(status_b["active_kda_calls"])
        and not runs["kda_run_id"].duplicated().any(),
        "KDA run keys disagree with VH10B status",
    )
    require(set(runs["broad_network"]).issubset(set(network_order)), "Unknown KDA broad network")
    require(set(runs["signature_direction"]) == set(direction_map), "KDA signature directions changed")
    runs["direction"] = runs["signature_direction"].map(direction_map)
    runs["effective_query_genes"] = pd.to_numeric(
        runs["effective_query_genes"], errors="raise"
    ).astype(int)
    require(
        runs["effective_query_genes"].ge(query_gene_minimum).all(),
        "A completed KDA call falls below the configured query minimum",
    )
    runs["significant_return_rows"] = pd.to_numeric(
        runs["significant_key_drivers"], errors="raise"
    ).astype(int)
    runs["has_significant_return"] = runs["significant_return_rows"].gt(0)
    expected_terminal = np.where(
        runs["has_significant_return"], "completed_significant", "completed_no_significant"
    )
    require(np.array_equal(runs["terminal_status"].to_numpy(), expected_terminal), "KDA terminal status disagrees with return count")
    active_calls = len(runs)
    calls_with_return = int(runs["has_significant_return"].sum())
    calls_without_return = int((~runs["has_significant_return"]).sum())
    significant_return_rows = int(runs["significant_return_rows"].sum())
    require(
        calls_with_return == as_int(status_b["completed_significant_calls"])
        and calls_without_return
        == as_int(status_b["completed_no_significant_calls"])
        and significant_return_rows == as_int(status_b["significant_return_rows"]),
        "Run-QC outcome counts disagree with VH10B status",
    )
    group_calls = runs["signature_group"].value_counts().astype(int).to_dict()

    observed_outcomes: dict[tuple[str, str], tuple[int, int]] = {}
    for network in network_order:
        for direction in DIRECTION_ORDER:
            cell = runs.loc[
                runs["broad_network"].eq(network) & runs["direction"].eq(direction)
            ]
            observed_outcomes[(network, direction)] = (
                int(cell["has_significant_return"].sum()),
                int((~cell["has_significant_return"]).sum()),
            )

    candidate_units = as_int(status_c["candidate_units"])
    passing_units = as_int(status_c["passing_candidate_units"])
    selected_units = as_int(status_c["selected_top5_units"])
    selected_unique_genes = as_int(status_c["selected_unique_genes"])
    require(
        candidate_units == as_int(freeze["candidate_units"])
        and passing_units == as_int(freeze["passing_candidate_units"])
        and selected_units == as_int(freeze["selected_top5_units"])
        and selected_unique_genes == as_int(freeze["selected_unique_genes"]),
        "VH10C status and frozen selection counts disagree",
    )
    require(
        math.isclose(float(status_c["minimum_coverage"]), minimum_coverage)
        and math.isclose(
            float(status_c["aggregate_q_threshold"]), aggregate_q_threshold
        )
        and as_int(status_c["minimum_conservative_supporting_runs"])
        == minimum_support,
        "VH10C status thresholds disagree with config",
    )
    require(
        as_int(status_c["testable_networks"]) == runs["broad_network"].nunique(),
        "VH10C testable-network count disagrees with completed calls",
    )
    selection_stages = [
        ("completed_calls", active_calls, "completed KDA calls"),
        (
            "calls_with_return",
            calls_with_return,
            "calls with ≥1 significant return",
        ),
        ("significant_rows", significant_return_rows, "significant return rows"),
        ("aggregate_candidates", candidate_units, "aggregate candidate units"),
        ("passing_units", passing_units, "units passed all gates"),
    ]
    method_steps = [
        "run BH",
        f"support ≥{minimum_support}",
        f"coverage ≥{minimum_coverage:.2f}",
        "ACAT",
        f"network BH q≤{aggregate_q_threshold:.2f}",
        "class rank",
    ]

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
        "result_tier_id": result_tier_id,
        "donor_minimum": donor_minimum,
        "fdr_threshold": fdr_threshold,
        "reference_fold_change": reference_fold_change,
        "query_gene_minimum": query_gene_minimum,
        "minimum_coverage": minimum_coverage,
        "aggregate_q_threshold": aggregate_q_threshold,
        "minimum_support": minimum_support,
        "display_limit": display_limit,
        "network_order": network_order,
        "runs": runs,
        "outcomes": observed_outcomes,
        "group_calls": group_calls,
        "active_calls": active_calls,
        "calls_with_return": calls_with_return,
        "calls_without_return": calls_without_return,
        "significant_return_rows": significant_return_rows,
        "candidate_units": candidate_units,
        "passing_units": passing_units,
        "selected_units": selected_units,
        "selected_unique_genes": selected_unique_genes,
        "selection_stages": selection_stages,
        "method_steps": method_steps,
        "rosmap_blinded": True,
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
        "direction": "",
        "direction_label": "",
        "direction_marker": "",
        "kda_run_id": "",
        "signature_group": "",
        "call_status": "",
        "significant_return_rows": "",
        "with_return_calls": "",
        "without_return_calls": "",
        "total_calls": "",
        "stage_id": "",
        "stage_value": "",
        "stage_label": "",
        "method_step": "",
        "analysis_role": "",
        "query_rule_id": "",
        "result_tier_id": "",
        "donor_minimum_per_arm": "",
        "fdr_threshold_exclusive": "",
        "minimum_effective_query_genes": "",
        "minimum_coverage": "",
        "aggregate_q_threshold": "",
        "minimum_conservative_supporting_runs": "",
        "display_limit_per_network_class": "",
        "rosmap_candidate_files_read": "",
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    network_order = bundle["network_order"]
    network_rank = {network: index for index, network in enumerate(network_order)}
    direction_rank = {direction: index for index, direction in enumerate(DIRECTION_ORDER)}
    runs = bundle["runs"].sort_values(
        ["broad_network", "direction", "has_significant_return", "kda_run_id"],
        key=lambda values: (
            values.map(network_rank)
            if values.name == "broad_network"
            else values.map(direction_rank)
            if values.name == "direction"
            else -values.astype(int)
            if values.name == "has_significant_return"
            else values
        ),
        kind="stable",
    )
    cell_offsets: dict[tuple[str, str], int] = {}
    for row in runs.itertuples(index=False):
        key = (row.broad_network, row.direction)
        offset = cell_offsets.get(key, 0)
        cell_offsets[key] = offset + 1
        record = _empty_record("call", f"call::{row.kda_run_id}")
        record.update(
            {
                "display_order": network_rank[row.broad_network] * 20 + direction_rank[row.direction] * 10 + offset,
                "broad_network": row.broad_network,
                "broad_network_label": NETWORK_LABELS[row.broad_network],
                "direction": row.direction,
                "direction_label": DIRECTION_LABELS[row.direction],
                "direction_marker": DIRECTION_MARKERS[row.direction],
                "kda_run_id": row.kda_run_id,
                "signature_group": row.signature_group,
                "call_status": "with_significant_return" if row.has_significant_return else "without_significant_return",
                "significant_return_rows": int(row.significant_return_rows),
            }
        )
        rows.append(record)

    for network_index, network in enumerate(network_order):
        for direction_index, direction in enumerate(DIRECTION_ORDER):
            with_return, without_return = bundle["outcomes"][(network, direction)]
            record = _empty_record("outcome_cell", f"cell::{network}::{direction}")
            record.update(
                {
                    "display_order": network_index * 2 + direction_index,
                    "broad_network": network,
                    "broad_network_label": NETWORK_LABELS[network],
                    "direction": direction,
                    "direction_label": DIRECTION_LABELS[direction],
                    "direction_marker": DIRECTION_MARKERS[direction],
                    "with_return_calls": with_return,
                    "without_return_calls": without_return,
                    "total_calls": with_return + without_return,
                }
            )
            rows.append(record)

    for index, (stage_id, value, label) in enumerate(bundle["selection_stages"]):
        record = _empty_record("selection_stage", f"stage::{stage_id}")
        record.update(
            {
                "display_order": index,
                "stage_id": stage_id,
                "stage_value": value,
                "stage_label": label,
            }
        )
        rows.append(record)
    for index, step in enumerate(bundle["method_steps"]):
        record = _empty_record("method_step", f"method::{index + 1}")
        record.update({"display_order": index, "method_step": step})
        rows.append(record)
    frame = pd.DataFrame(rows)
    frame["analysis_role"] = bundle["analysis_role"]
    frame["query_rule_id"] = bundle["query_rule_id"]
    frame["result_tier_id"] = bundle["result_tier_id"]
    frame["donor_minimum_per_arm"] = bundle["donor_minimum"]
    frame["fdr_threshold_exclusive"] = bundle["fdr_threshold"]
    frame["minimum_effective_query_genes"] = bundle["query_gene_minimum"]
    frame["minimum_coverage"] = bundle["minimum_coverage"]
    frame["aggregate_q_threshold"] = bundle["aggregate_q_threshold"]
    frame["minimum_conservative_supporting_runs"] = bundle["minimum_support"]
    frame["display_limit_per_network_class"] = bundle["display_limit"]
    frame["rosmap_candidate_files_read"] = False
    expected_records = (
        bundle["active_calls"]
        + len(network_order) * len(DIRECTION_ORDER)
        + len(bundle["selection_stages"])
        + len(bundle["method_steps"])
    )
    require(
        len(frame) == expected_records,
        f"Expected {expected_records} plot records, observed {len(frame)}",
    )
    require(frame["record_id"].is_unique, "Plot record IDs are duplicated")
    return frame


def _cell_positions(start_x: float, center_y: float, count: int) -> list[tuple[float, float]]:
    positions: list[tuple[float, float]] = []
    for index in range(count):
        column = index % 5
        row = index // 5
        y = center_y + (0.13 if row == 0 else -0.13)
        positions.append((start_x + column * 0.54, y))
    return positions


def draw_figure(bundle: Mapping[str, Any], plot_data: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    fig.text(0.018, 0.958, "A  KDA call outcomes", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.650, 0.958, "B  Evidence → selection", ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    fig.text(0.475, 0.955, "POST-HOC EXPLORATORY", ha="center", va="top", fontsize=16, weight="bold", color=ORANGE)
    fig.text(0.195, 0.877, "● ≥1 return     ○ none     counts: with | none", ha="left", va="center", fontsize=16, color=MID)
    fig.text(0.815, 0.878, "MitoCarta DEG query", ha="center", va="center", fontsize=16, color=MID)
    fig.text(0.815, 0.831, "→ MT or non-MT network drivers", ha="center", va="center", fontsize=16, color=MID)

    matrix_ax = fig.add_axes([0.195, 0.145, 0.435, 0.675])
    matrix_ax.set_xlim(-0.6, 11.4)
    matrix_ax.set_ylim(-0.65, 6.75)
    matrix_ax.set_xticks([])
    network_order = bundle["network_order"]
    y_positions = {
        network: len(network_order) - 1 - index
        for index, network in enumerate(network_order)
    }
    matrix_ax.set_yticks(
        [y_positions[network] for network in network_order],
        [NETWORK_LABELS[network] for network in network_order],
    )
    matrix_ax.tick_params(axis="y", length=0, pad=8, labelsize=16)
    for spine in matrix_ax.spines.values():
        spine.set_visible(False)
    for index, network in enumerate(network_order):
        if index % 2 == 1:
            matrix_ax.axhspan(y_positions[network] - 0.42, y_positions[network] + 0.42, color="#F5F7F8", zorder=0)
    starts = {"up": 0.0, "down": 7.0}
    matrix_ax.text(1.25, 6.62, "▲ Dementia-up", ha="center", va="bottom", fontsize=17, weight="bold", color=TEXT)
    matrix_ax.text(8.25, 6.62, "▼ Dementia-down", ha="center", va="bottom", fontsize=17, weight="bold", color=TEXT)

    calls = plot_data.loc[plot_data["record_type"].eq("call")]
    cells = plot_data.loc[plot_data["record_type"].eq("outcome_cell")]
    for network in network_order:
        y = y_positions[network]
        for direction in DIRECTION_ORDER:
            start_x = starts[direction]
            cell_calls = calls.loc[
                calls["broad_network"].eq(network) & calls["direction"].eq(direction)
            ].sort_values("display_order")
            positions = _cell_positions(start_x, y, len(cell_calls))
            if cell_calls.empty:
                matrix_ax.text(start_x + 1.08, y, "—", ha="center", va="center", fontsize=18, color="#9AA2AA")
            else:
                for (_, call), (x, dot_y) in zip(cell_calls.iterrows(), positions):
                    filled = call["call_status"] == "with_significant_return"
                    matrix_ax.scatter(
                        [x], [dot_y],
                        marker=DIRECTION_MARKERS[direction], s=88,
                        facecolor=NAVY if filled else NO_RETURN,
                        edgecolor=NAVY if filled else NO_RETURN_EDGE,
                        linewidth=1.1, zorder=4,
                    )
            cell = cells.loc[
                cells["broad_network"].eq(network) & cells["direction"].eq(direction)
            ].iloc[0]
            count_x = start_x + 3.18
            matrix_ax.text(
                count_x, y,
                f"{as_int(cell['with_return_calls'])} | {as_int(cell['without_return_calls'])}",
                ha="center", va="center", fontsize=16, weight="bold", color=TEXT,
            )
    matrix_ax.axvline(5.15, color="#C3C8CD", linewidth=1.0)

    sequence_ax = fig.add_axes([0.655, 0.145, 0.330, 0.650])
    sequence_ax.set_xlim(0, 1)
    sequence_ax.set_ylim(0, 1)
    sequence_ax.axis("off")
    box_y = [0.82, 0.63, 0.44, 0.25, 0.06]
    box_fills = ["#DDF3EB", "#DCEAF3", "#E7EEF5", "#F0F2F4", "#FBE8C7"]
    box_edges = [SEAAD, "#0072B2", "#537A9D", "#737C85", ORANGE]
    for index, ((stage_id, value, label), y, fill, edge) in enumerate(
        zip(bundle["selection_stages"], box_y, box_fills, box_edges)
    ):
        sequence_ax.add_patch(
            mpatches.FancyBboxPatch(
                (0.03, y), 0.94, 0.14,
                boxstyle="round,pad=0.006,rounding_size=0.014",
                facecolor=fill, edgecolor=edge, linewidth=1.5,
            )
        )
        display_label = {
            "calls_with_return": "calls with ≥1\nsignificant return",
            "significant_rows": "significant return\nrows",
            "aggregate_candidates": "aggregate candidate\nunits",
            "passing_units": "units passed\nall gates",
        }.get(stage_id, label)
        sequence_ax.text(0.17, y + 0.070, f"{value:,}", ha="center", va="center", fontsize=20, weight="bold", color=NAVY)
        sequence_ax.text(0.36, y + 0.070, display_label, ha="left", va="center", fontsize=16, linespacing=0.92, color=TEXT)
        if index < len(bundle["selection_stages"]) - 1:
            sequence_ax.annotate(
                "", xy=(0.50, box_y[index + 1] + 0.145), xytext=(0.50, y - 0.004),
                arrowprops={"arrowstyle": "-|>", "color": MID, "linewidth": 1.2},
            )
    fig.add_artist(
        mpatches.FancyBboxPatch(
            (0.018, 0.018), 0.964, 0.075,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            transform=fig.transFigure, facecolor="#F4F6F7", edgecolor="#AAB1B8", linewidth=1.0,
        )
    )
    fig.text(
        0.50, 0.055,
        "  →  ".join(bundle["method_steps"]),
        ha="center", va="center", fontsize=16, weight="bold", color=TEXT,
    )

    metadata = visible_text_metadata(fig)
    require(metadata["minimum_font_points"] >= MINIMUM_FONT_PT, "A visible label is smaller than 16 pt")
    require(not metadata["canvas_clipped_text"], "Text leaves canvas: " + " | ".join(metadata["canvas_clipped_text"]))
    return fig, metadata


def render_images(
    bundle: Mapping[str, Any], plot_data: pd.DataFrame, staging: Path, dpi: int
) -> tuple[list[Path], dict[str, Any]]:
    fig, metadata = draw_figure(bundle, plot_data)
    paths = render_three_formats(
        fig, staging, FIGURE_ID, dpi=dpi,
        title="SEA-AD KDA call outcomes and selection sequence",
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
    calls = plot_data.loc[plot_data["record_type"].eq("call")]
    cells = plot_data.loc[plot_data["record_type"].eq("outcome_cell")]
    stages = plot_data.loc[plot_data["record_type"].eq("selection_stage")]
    observed_outcomes = {
        (row.broad_network, row.direction): (
            as_int(row.with_return_calls), as_int(row.without_return_calls)
        )
        for row in cells.itertuples(index=False)
    }
    observed_stages = [
        (row.stage_id, as_int(row.stage_value), row.stage_label)
        for row in stages.sort_values("display_order").itertuples(index=False)
    ]
    observed_methods = (
        plot_data.loc[plot_data["record_type"].eq("method_step")]
        .sort_values("display_order")["method_step"]
        .tolist()
    )
    expected_records = (
        bundle["active_calls"]
        + len(bundle["network_order"]) * len(DIRECTION_ORDER)
        + len(bundle["selection_stages"])
        + len(bundle["method_steps"])
    )
    checks = [
        record("upstream_phases_complete", True, "VH10B|VH10C validated_complete", "VH10B|VH10C validated_complete", "Validated during input loading."),
        record("compact_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS) + 2, len(bundle["input_digests"]), len(INPUT_PATHS) + 2, "Every consumed compact source and config has a full-file SHA-256; bulky unconsumed KDA tables are not required."),
        record("posthoc_exploratory_label", bundle["analysis_role"] == "posthoc_exploratory", bundle["analysis_role"], "posthoc_exploratory", "The amended SEA-AD analysis is labeled post-hoc exploratory."),
        record("donor_three_protocol", bundle["donor_minimum"] == 3, bundle["donor_minimum"], 3, "Minimum donors per disease arm inherited from VH08."),
        record("active_query_is_fdr_only", "abs(logFC)" not in bundle["active_query_rule"], bundle["active_query_rule"], f"FDR < {bundle['fdr_threshold']:g}", "The KDA query has no fold-change gate."),
        record("query_minimum", bundle["query_gene_minimum"] == 3, bundle["query_gene_minimum"], 3, "Minimum effective query genes per KDA call."),
        record("coverage_retained", math.isclose(bundle["minimum_coverage"], 0.80), bundle["minimum_coverage"], 0.80, "The planned 0.80 coverage gate is retained."),
        record("aggregate_q_retained", math.isclose(bundle["aggregate_q_threshold"], 0.05), bundle["aggregate_q_threshold"], 0.05, "The planned aggregate network-BH q threshold is retained."),
        record("rosmap_blinded_selection", bundle["rosmap_blinded"], False, False, "ROSMAP candidate files were not read while freezing SEA-AD selection."),
        record("call_count", len(calls) == bundle["active_calls"], len(calls), bundle["active_calls"], "One plot record per completed KDA call."),
        record("call_ids_unique", calls["kda_run_id"].is_unique, "unique", "unique", "KDA call IDs are unique."),
        record("calls_with_returns", calls["call_status"].eq("with_significant_return").sum() == bundle["calls_with_return"], calls["call_status"].eq("with_significant_return").sum(), bundle["calls_with_return"], "Calls with at least one significant return."),
        record("calls_without_returns", calls["call_status"].eq("without_significant_return").sum() == bundle["calls_without_return"], calls["call_status"].eq("without_significant_return").sum(), bundle["calls_without_return"], "Calls without a significant return."),
        record("significant_return_rows", calls["significant_return_rows"].map(as_int).sum() == bundle["significant_return_rows"], calls["significant_return_rows"].map(as_int).sum(), bundle["significant_return_rows"], "Significant KDA return rows."),
        record("outcome_cell_count", len(cells) == len(bundle["network_order"]) * 2, len(cells), len(bundle["network_order"]) * 2, "Configured networks by two signed directions."),
        record("outcome_matrix", observed_outcomes == bundle["outcomes"], str(observed_outcomes), str(bundle["outcomes"]), "Exact with-return/without-return counts, including zero-call cells."),
        record("selection_sequence", observed_stages == bundle["selection_stages"], str(observed_stages), str(bundle["selection_stages"]), "Exact evidence-to-selection stage values."),
        record("candidate_units", as_int(stages.loc[stages["stage_id"].eq("aggregate_candidates"), "stage_value"].iloc[0]) == bundle["candidate_units"], as_int(stages.loc[stages["stage_id"].eq("aggregate_candidates"), "stage_value"].iloc[0]), bundle["candidate_units"], "Aggregate candidate units."),
        record("passing_units", as_int(stages.loc[stages["stage_id"].eq("passing_units"), "stage_value"].iloc[0]) == bundle["passing_units"], as_int(stages.loc[stages["stage_id"].eq("passing_units"), "stage_value"].iloc[0]), bundle["passing_units"], "Candidate units passing all gates."),
        record("selected_units", bundle["selected_units"] <= bundle["passing_units"], bundle["selected_units"], f"<= {bundle['passing_units']}", "Selected class-ranked units are a subset of passing units."),
        record("method_steps", observed_methods == bundle["method_steps"], str(observed_methods), str(bundle["method_steps"]), "Aggregation steps and active thresholds."),
        record("plot_record_count", len(plot_data) == expected_records, len(plot_data), expected_records, "Calls, outcome cells, stages, and method steps."),
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
    caption = f"""# SEA-AD KDA call outcomes: caption

**In the post-hoc exploratory SEA-AD rerun, {bundle['calls_with_return']:,} of {bundle['active_calls']:,} completed KDA calls produced at least one significant return.** Each triangle in the outcome matrix is one completed call. Filled navy triangles denote a call with at least one significant return; light triangles denote none. Upward and downward orientation preserves signed-query direction independently of color. Direct cell labels report `with return | none`, and zero-call cells remain explicit. The sequence at right changes units deliberately: {bundle['active_calls']:,} calls yielded {bundle['calls_with_return']:,} calls with returns and {bundle['significant_return_rows']:,} significant return rows; cross-run aggregation evaluated {bundle['candidate_units']:,} broad-network gene/class candidate units, of which {bundle['passing_units']:,} passed all gates and {bundle['selected_units']:,} were retained after class ranking ({bundle['selected_unique_genes']:,} unique genes). The signed core-MitoCarta DEG set is the KDA query, while candidate drivers are all assessable genes in the induced network; a mitochondrial query can therefore identify a non-MT driver. SEA-AD selection was frozen without reading ROSMAP candidate files.
"""
    methods = f"""# SEA-AD KDA call outcomes: methods

The renderer reads the active DEG and VH10 configurations plus the validated VH10B status and compact registered run-QC table and the validated VH10C status, selection checks, and selection freeze. It validates full-file SHA-256 values for consumed compact inputs only; bulky call-return and candidate-test tables are not required because they are not plotted. Status and freeze config hashes must match the active VH10 configuration, and the freeze digest must match VH10C status. The active post-hoc exploratory tier is `{bundle['result_tier_id']}`. Queries use `{bundle['query_rule_id']}` (`{bundle['active_query_rule']}`), at least {bundle['donor_minimum']} donors per disease arm upstream, and at least {bundle['query_gene_minimum']} effective query genes per KDA call. The inherited {bundle['reference_fold_change']:g}-fold rule is not an active KDA query gate. The retained selection gates are conservative support ≥{bundle['minimum_support']}, coverage ≥{bundle['minimum_coverage']:.2f}, and network-BH aggregate q ≤{bundle['aggregate_q_threshold']:.2f}; the per-network/class display limit is {bundle['display_limit']}.

Each `significant_key_drivers > 0` flag must agree with its terminal status. Network-by-direction counts are reconstructed from individual calls and checked across all {len(bundle['network_order']) * 2} configured cells, including network/direction combinations with no call. The five equal-size sequence boxes are not area-scaled because units change from calls to return rows to aggregate candidate units. The aggregation ribbon preserves the executed order: `{' → '.join(bundle['method_steps'])}`. The SEA-AD selection freeze must state `rosmap_candidate_files_read=False`; ROSMAP remains a frozen external comparison and its candidate identities or thresholds are not used to select SEA-AD units.

The asset is titleless at slide level, uses a 12.0 × 5.3 inch canvas, and keeps all visible text at 16 pt or larger. SVG/PDF retain vector geometry and searchable text; PNG is 5,400 × 2,385 pixels at 450 DPI. Direction is encoded by triangle orientation, and call status is encoded by fill plus direct labels, so the figure remains interpretable in grayscale.

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
        "donor_minimum_per_arm",
        "fdr_threshold_exclusive",
        "minimum_effective_query_genes",
        "minimum_coverage",
        "aggregate_q_threshold",
        "minimum_conservative_supporting_runs",
        "display_limit_per_network_class",
        "rosmap_candidate_files_read",
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
    require(
        all(not truth(value) for value in plot_data["rosmap_candidate_files_read"]),
        "Published plot data does not preserve the ROSMAP-blinded boundary",
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
    print(f"KDA call-outcomes package validation passed: {output_root}")


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
        image_paths, render_meta = render_images(bundle, plot_data, staging, dpi)
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
                    "donor_minimum_per_arm": bundle["donor_minimum"],
                    "fdr_threshold_exclusive": bundle["fdr_threshold"],
                    "minimum_effective_query_genes": bundle["query_gene_minimum"],
                    "minimum_coverage": bundle["minimum_coverage"],
                    "aggregate_q_threshold": bundle["aggregate_q_threshold"],
                    "minimum_conservative_supporting_runs": bundle["minimum_support"],
                    "display_limit_per_network_class": bundle["display_limit"],
                    "rosmap_candidate_files_read": False,
                    "completed_calls": bundle["active_calls"],
                    "calls_with_returns": bundle["calls_with_return"],
                    "calls_without_returns": bundle["calls_without_return"],
                    "significant_return_rows": bundle["significant_return_rows"],
                    "candidate_units": bundle["candidate_units"],
                    "passing_units": bundle["passing_units"],
                    "selected_units": bundle["selected_units"],
                    "selected_unique_genes": bundle["selected_unique_genes"],
                    "group_call_counts": "|".join(
                        f"{group}:{count}"
                        for group, count in sorted(bundle["group_calls"].items())
                    ),
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
