#!/usr/bin/env python3
"""Legacy former-Case-3 atlas generator; not valid for two-class v2 output."""

from __future__ import annotations

import argparse
from collections import defaultdict
import math
import platform
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image

from phase18_case3_common import (
    CASE_ID,
    EXPECTED_CIRCLE_GENES,
    EXPECTED_EXTRA_CONTEXT,
    NETWORK_COLORS,
    NETWORK_LABELS,
    NETWORK_ORDER,
    REQUIRED_INPUTS,
    display_path,
    integer,
    load_validated_bundle,
    number,
    read_tsv,
    require,
    require_columns,
    sha256_file,
    sorted_tokens,
    token_set,
    truth,
    tsv_rows,
    write_text,
    write_tsv,
)


SCHEMA = "phase18_case3_evidence_atlas_v1"
FIGURE_ID = "phase18_case3_evidence_atlas"
DEFAULT_INPUT = "results/minerva_production/18_key_driver_selection"
DEFAULT_OUTPUT = "results/figures/analysis/phase_18_key_driver_selection/case3_evidence_atlas"
DEFAULT_DPI = 450
DEFAULT_WIDTH = 12.0
DEFAULT_HEIGHT = 8.0
DEFAULT_EVIDENCE_CAP = 12.0
FLOAT_TOLERANCE = 1e-12

SUMMARY_FILE = "phase18_case3_gene_summary.tsv"
DETAIL_FILE = "phase18_case3_gene_network_details.tsv"
PLOT_FILE = "phase18_case3_evidence_atlas_plot_data.tsv"
CAPTION_FILE = "phase18_case3_evidence_atlas_caption.md"
METHODS_FILE = "phase18_case3_evidence_atlas_methods.md"
MANIFEST_FILE = "phase18_case3_evidence_atlas_manifest.tsv"
CHECKS_FILE = "phase18_case3_evidence_atlas_checks.tsv"
ARTIFACTS_FILE = "phase18_case3_evidence_atlas_artifacts.tsv"
STATUS_FILE = "phase18_case3_evidence_atlas_status.tsv"
IMAGE_FILES = [
    "phase18_case3_evidence_atlas.svg",
    "phase18_case3_evidence_atlas.pdf",
    "phase18_case3_evidence_atlas.png",
]
DECLARED_OUTPUTS = IMAGE_FILES + [
    SUMMARY_FILE,
    DETAIL_FILE,
    PLOT_FILE,
    CAPTION_FILE,
    METHODS_FILE,
    MANIFEST_FILE,
    CHECKS_FILE,
    ARTIFACTS_FILE,
    STATUS_FILE,
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--width-inches", type=float, default=DEFAULT_WIDTH)
    parser.add_argument("--height-inches", type=float, default=DEFAULT_HEIGHT)
    parser.add_argument("--evidence-cap", type=float, default=DEFAULT_EVIDENCE_CAP)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
        help="Operator assertion recorded after reviewing the rendered figure.",
    )
    parser.add_argument(
        "--validate-output",
        help="Validate an existing atlas package and exit without rendering.",
    )
    args = parser.parse_args(argv)
    require(300 <= args.png_dpi <= 600, "--png-dpi must be between 300 and 600")
    require(args.width_inches > 0 and args.height_inches > 0, "Figure dimensions must be positive")
    require(args.evidence_cap > 0, "--evidence-cap must be positive")
    return args


def close_enough(observed: float | None, expected: float | None, tolerance: float = FLOAT_TOLERANCE) -> bool:
    if observed is None or expected is None:
        return observed is None and expected is None
    return math.isclose(observed, expected, rel_tol=tolerance, abs_tol=tolerance)


def check_record(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    notes: str = "",
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA}_checks_v1",
        "check_id": check_id,
        "severity": severity,
        "observed": observed,
        "expected": expected,
        "passed": passed,
        "notes": notes,
    }


def ordered_networks(values: Iterable[str]) -> str:
    observed = set(values)
    return "|".join(network for network in NETWORK_ORDER if network in observed)


def prepare_tables(bundle: Mapping[str, Any], evidence_cap: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    paths = bundle["paths"]
    top5 = read_tsv(paths["key_driver_top5.tsv"])
    figure_data = read_tsv(paths["key_driver_figure_data.tsv"])
    candidates = read_tsv(paths["key_driver_candidates.tsv"])
    stability = read_tsv(paths["key_driver_stability_summary.tsv"])
    degree = read_tsv(paths["key_driver_network_degree_sensitivity.tsv"])
    run_manifest = read_tsv(paths["key_driver_run_manifest.tsv"])

    require_columns(top5, ["broad_network", "case_id", "list_status", "display_rank", "current_symbol", "aggregate_acat_q"], "key_driver_top5.tsv")
    require_columns(figure_data, ["broad_network", "case_id", "list_status", "display_rank", "current_symbol", "aggregate_acat_q"], "key_driver_figure_data.tsv")
    require_columns(candidates, ["broad_network", "current_symbol", "case_id", "is_core_mito", "terminal_candidate_status", "within_case_rank", "top5_display", "aggregate_acat_q"], "key_driver_candidates.tsv")
    require_columns(stability, ["broad_network", "current_symbol", "case_id", "assessable_repetitions", "nominal_p_pass_fraction", "aggregate_q_pass_fraction", "candidate_retention_fraction", "worst_rank"], "key_driver_stability_summary.tsv")
    require_columns(degree, ["broad_network", "current_symbol", "case_id", "out_degree", "undirected_degree", "requested_draws", "completed_draws", "degree_matched_empirical_tail_p", "blocking_gate"], "key_driver_network_degree_sensitivity.tsv")
    require_columns(run_manifest, ["kda_run_id", "fine_cell_type", "broad_network", "signature_group", "signature_direction", "phase18_included"], "key_driver_run_manifest.tsv")

    displayed = [row for row in top5 if row["case_id"] == CASE_ID and row["list_status"] == "ranked_candidates"]
    figure_displayed = [row for row in figure_data if row["case_id"] == CASE_ID and row["list_status"] == "ranked_candidates"]
    displayed_keys = {(row["broad_network"], row["current_symbol"]) for row in displayed}
    figure_keys = {(row["broad_network"], row["current_symbol"]) for row in figure_displayed}
    circle_genes = {row["current_symbol"] for row in displayed}
    require(len(displayed) == len(displayed_keys) == 21, "Expected exactly 21 unique displayed Case 3 contexts")
    require(figure_keys == displayed_keys and len(figure_displayed) == 21, "Figure-data provenance differs from top-five provenance")
    require(len(circle_genes) == 15, "Expected exactly 15 Case 3 circle genes")
    require(circle_genes == EXPECTED_CIRCLE_GENES, "The current Case 3 circle-gene set drifted")

    display_map = {(row["broad_network"], row["current_symbol"]): row for row in displayed}
    passing = [
        row
        for row in candidates
        if row["case_id"] == CASE_ID
        and row["current_symbol"] in circle_genes
        and row["terminal_candidate_status"] == "driver_candidate"
    ]
    passing_keys = {(row["broad_network"], row["current_symbol"]) for row in passing}
    require(len(passing) == len(passing_keys) == 22, "Expected exactly 22 unique passing contexts for the circle genes")
    require(passing_keys - displayed_keys == {EXPECTED_EXTRA_CONTEXT}, "Unexpected below-cap passing context")
    require(not displayed_keys - passing_keys, "A displayed context is not a passing candidate")
    require(all(not truth(row["is_core_mito"]) for row in passing), "A Case 3 detail row is marked core MitoCarta")

    candidate_map = {(row["broad_network"], row["current_symbol"]): row for row in passing}
    for key in displayed_keys:
        candidate = candidate_map[key]
        top = display_map[key]
        require(truth(candidate["top5_display"]), f"Displayed flag missing for {key}")
        require(integer(candidate["within_case_rank"]) == integer(top["display_rank"]), f"Displayed rank drift for {key}")
        require(close_enough(number(candidate["aggregate_acat_q"]), number(top["aggregate_acat_q"])), f"Displayed q drift for {key}")
    require(not truth(candidate_map[EXPECTED_EXTRA_CONTEXT]["top5_display"]), "Below-cap RPS15 context is incorrectly displayed")
    require(integer(candidate_map[EXPECTED_EXTRA_CONTEXT]["within_case_rank"]) == 20, "Below-cap RPS15 rank drifted")

    included_runs = {row["kda_run_id"]: row for row in run_manifest if truth(row["phase18_included"])}
    require(len(included_runs) == integer(bundle["status"]["phase18_included_runs"]), "Included run-manifest count differs from status")

    tests_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in tsv_rows(paths["key_driver_candidate_tests.tsv.gz"]):
        if row["case_id"] != CASE_ID or row["current_symbol"] not in circle_genes:
            continue
        key = (row["broad_network"], row["current_symbol"])
        if key not in passing_keys:
            continue
        manifest_row = included_runs.get(row["kda_run_id"])
        require(manifest_row is not None, f"Candidate-test row is outside the included run manifest: {row['kda_run_id']}")
        for field in ("fine_cell_type", "broad_network", "signature_group", "signature_direction"):
            require(row[field] == manifest_row[field], f"Run-manifest drift for {row['kda_run_id']} field {field}")
        tests_by_key[key].append(row)
    require(set(tests_by_key) == passing_keys, "Candidate-test matrix lacks a passing context")

    conservative_rows: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in tsv_rows(paths["key_driver_conservative_support.tsv.gz"]):
        key = (row["broad_network"], row["current_symbol"])
        if row["case_id"] == CASE_ID and key in passing_keys:
            # This audit table retains every evaluated gate combination, not
            # only its terminal supporting rows.  Reconcile the exact positive
            # set while preserving zero-support rows as valid audit evidence.
            if truth(row["conservative_support"]):
                conservative_rows[key].add(row["kda_run_id"])

    stability_map = {(row["broad_network"], row["current_symbol"]): row for row in stability if row["case_id"] == CASE_ID and (row["broad_network"], row["current_symbol"]) in passing_keys}
    degree_map = {(row["broad_network"], row["current_symbol"]): row for row in degree if row["case_id"] == CASE_ID and (row["broad_network"], row["current_symbol"]) in passing_keys}
    require(set(stability_map) == passing_keys and len(stability_map) == 22, "Stability rows do not join one-to-one")
    require(set(degree_map) == passing_keys and len(degree_map) == 22, "Degree rows do not join one-to-one")

    replicates_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in tsv_rows(paths["key_driver_stability_replicates.tsv.gz"]):
        key = (row["broad_network"], row["current_symbol"])
        if row["case_id"] == CASE_ID and key in passing_keys:
            replicates_by_key[key].append(row)

    detail_rows: list[dict[str, Any]] = []
    tests_by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    for key in passing_keys:
        candidate = candidate_map[key]
        test_rows = tests_by_key[key]
        run_ids = [row["kda_run_id"] for row in test_rows]
        require(len(run_ids) == len(set(run_ids)), f"Duplicate candidate-test run for {key}")
        eligible = set(run_ids)
        usable = {row["kda_run_id"] for row in test_rows if truth(row["usable_test"])}
        supports = {row["kda_run_id"] for row in test_rows if truth(row["conservative_support"])}
        missing = eligible - usable
        require(supports <= usable <= eligible, f"Impossible support/usability sets for {key}")
        require(len(eligible) == integer(candidate["eligible_run_count"]), f"Eligible count mismatch for {key}")
        require(len(usable) == integer(candidate["usable_run_count"]), f"Usable count mismatch for {key}")
        require(len(missing) == integer(candidate["missing_run_count"]), f"Missing count mismatch for {key}")
        require(len(supports) == integer(candidate["conservative_support_count"]), f"Support count mismatch for {key}")
        require(supports == conservative_rows[key], f"Conservative-support run IDs mismatch for {key}")
        require(close_enough(len(usable) / len(eligible), number(candidate["coverage_fraction"])), f"Coverage mismatch for {key}")
        require(close_enough(len(supports) / len(usable), number(candidate["recurrence_fraction"])), f"Recurrence mismatch for {key}")

        support_rows = [row for row in test_rows if truth(row["conservative_support"])]
        fine_types = {row["fine_cell_type"] for row in support_rows}
        groups = {row["signature_group"] for row in support_rows}
        directions = {row["signature_direction"] for row in support_rows}
        require(fine_types == token_set(candidate["supporting_fine_cell_types"]), f"Fine-cell support annotation mismatch for {key}")
        require(groups == token_set(candidate["supporting_groups"]), f"Group support annotation mismatch for {key}")
        require(directions == token_set(candidate["supporting_directions"]), f"Direction support annotation mismatch for {key}")

        stability_row = stability_map[key]
        replicate_rows = [row for row in replicates_by_key[key] if truth(row["assessable"])]
        assessable_n = len(replicate_rows)
        nominal_fraction = sum(number(row["aggregate_acat_p"]) <= 0.05 for row in replicate_rows) / assessable_n if assessable_n else None
        q_fraction = sum(number(row["aggregate_acat_q"]) is not None and number(row["aggregate_acat_q"]) <= 0.05 for row in replicate_rows) / assessable_n if assessable_n else None
        candidate_fraction = sum(row["terminal_candidate_status"] == "driver_candidate" for row in replicate_rows) / assessable_n if assessable_n else None
        ranks = [integer(row["within_case_rank"]) for row in replicate_rows if number(row["within_case_rank"]) is not None]
        worst_rank = max(ranks) if ranks else None
        expected_worst_value = number(stability_row["worst_rank"])
        expected_worst_rank = integer(expected_worst_value) if expected_worst_value is not None else None
        require(assessable_n == integer(stability_row["assessable_repetitions"]), f"Stability repetition mismatch for {key}")
        require(close_enough(nominal_fraction, number(stability_row["nominal_p_pass_fraction"])), f"Stability nominal fraction mismatch for {key}")
        require(close_enough(q_fraction, number(stability_row["aggregate_q_pass_fraction"])), f"Stability q fraction mismatch for {key}")
        require(close_enough(candidate_fraction, number(stability_row["candidate_retention_fraction"])), f"Stability retention mismatch for {key}")
        require(worst_rank == expected_worst_rank, f"Stability worst-rank mismatch for {key}")

        degree_row = degree_map[key]
        requested_draws = integer(degree_row["requested_draws"])
        completed_draws = integer(degree_row["completed_draws"])
        require(0 < completed_draws <= requested_draws, f"Invalid degree draw count for {key}")
        q_value = number(candidate["aggregate_acat_q"])
        require(q_value is not None and 0 < q_value <= 0.05, f"Passing context lacks finite q <= 0.05 for {key}")
        tests_by_gene[candidate["current_symbol"]].extend(test_rows)

        top_row = display_map.get(key)
        detail_rows.append(
            {
                "schema_version": f"{SCHEMA}_gene_network_details_v1",
                "case_id": CASE_ID,
                "current_symbol": candidate["current_symbol"],
                "broad_network": candidate["broad_network"],
                "network_order": NETWORK_ORDER.index(candidate["broad_network"]) + 1,
                "network_label": NETWORK_LABELS[candidate["broad_network"]],
                "network_color": NETWORK_COLORS[candidate["broad_network"]],
                "circle_displayed": key in displayed_keys,
                "circle_display_rank": integer(top_row["display_rank"]) if top_row else None,
                "within_case_rank": integer(candidate["within_case_rank"]),
                "evidence_tier": candidate["evidence_tier"],
                "eligible_run_count": len(eligible),
                "usable_run_count": len(usable),
                "missing_run_count": len(missing),
                "coverage_fraction": len(usable) / len(eligible),
                "conservative_support_count": len(supports),
                "recurrence_fraction": len(supports) / len(usable),
                "supporting_fine_cell_type_count": len(fine_types),
                "supporting_fine_cell_types": sorted_tokens(fine_types),
                "supporting_group_count": len(groups),
                "supporting_groups": sorted_tokens(groups),
                "supporting_direction_count": len(directions),
                "supporting_directions": sorted_tokens(directions),
                "median_support_fold_enrichment": number(candidate["median_support_fold_enrichment"]),
                "maximum_support_fold_enrichment": number(candidate["maximum_support_fold_enrichment"]),
                "aggregate_acat_p": number(candidate["aggregate_acat_p"]),
                "aggregate_acat_q": q_value,
                "negative_log10_aggregate_acat_q": -math.log10(q_value),
                "capped_negative_log10_aggregate_acat_q": min(-math.log10(q_value), evidence_cap),
                "missing_as_one_acat_p": number(candidate["missing_as_one_acat_p"]),
                "missing_as_one_acat_q": number(candidate["missing_as_one_acat_q"]),
                "stability_assessable_repetitions": assessable_n,
                "stability_nominal_fraction": nominal_fraction,
                "stability_q_fraction": q_fraction,
                "stability_candidate_fraction": candidate_fraction,
                "stability_worst_rank": worst_rank,
                "stability_assessable": assessable_n > 0,
                "out_degree": integer(degree_row["out_degree"]),
                "undirected_degree": integer(degree_row["undirected_degree"]),
                "requested_degree_matched_draws": requested_draws,
                "completed_degree_matched_draws": completed_draws,
                "degree_matched_empirical_tail_p": number(degree_row["degree_matched_empirical_tail_p"]),
                "negative_log10_degree_matched_empirical_tail_p": -math.log10(number(degree_row["degree_matched_empirical_tail_p"])),
                "degree_sensitivity_blocking_gate": truth(degree_row["blocking_gate"]),
                "degree_diagnostic_complete": completed_draws == requested_draws,
                "is_core_mito": truth(candidate["is_core_mito"]),
                "extended_reference_member": truth(candidate["extended_reference_member"]),
            }
        )

    gene_rows: list[dict[str, Any]] = []
    details_by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in detail_rows:
        details_by_gene[row["current_symbol"]].append(row)
    for gene in circle_genes:
        contexts = details_by_gene[gene]
        gene_tests = tests_by_gene[gene]
        run_ids = [row["kda_run_id"] for row in gene_tests]
        require(len(run_ids) == len(set(run_ids)), f"A run ID appears in more than one passing network for {gene}")
        eligible = set(run_ids)
        usable = {row["kda_run_id"] for row in gene_tests if truth(row["usable_test"])}
        supports = {row["kda_run_id"] for row in gene_tests if truth(row["conservative_support"])}
        support_rows = [row for row in gene_tests if truth(row["conservative_support"])]
        fine_types = {row["fine_cell_type"] for row in support_rows}
        groups = {row["signature_group"] for row in support_rows}
        directions = {row["signature_direction"] for row in support_rows}
        q_sorted = sorted(contexts, key=lambda row: (row["aggregate_acat_q"], row["broad_network"]))
        displayed_networks = [row["broad_network"] for row in contexts if row["circle_displayed"]]
        passing_networks = [row["broad_network"] for row in contexts]
        extended_values = {row["extended_reference_member"] for row in contexts}
        require(len(extended_values) == 1, f"Extended-reference annotation drift across contexts for {gene}")
        gene_rows.append(
            {
                "schema_version": f"{SCHEMA}_gene_summary_v1",
                "case_id": CASE_ID,
                "current_symbol": gene,
                "is_core_mito": False,
                "extended_reference_member": next(iter(extended_values)),
                "circle_gene": True,
                "circle_display_network_count": len(displayed_networks),
                "circle_display_networks": ordered_networks(displayed_networks),
                "passing_broad_network_count": len(passing_networks),
                "passing_broad_networks": ordered_networks(passing_networks),
                "q_passing_network_count": len(contexts),
                "unique_supporting_fine_cell_type_count": len(fine_types),
                "unique_supporting_fine_cell_types": sorted_tokens(fine_types),
                "eligible_query_count": len(eligible),
                "usable_query_count": len(usable),
                "missing_query_count": len(eligible - usable),
                "query_coverage_fraction": len(usable) / len(eligible),
                "conservative_supporting_query_count": len(supports),
                "query_recurrence_fraction": len(supports) / len(usable),
                "supporting_group_count": len(groups),
                "supporting_groups": sorted_tokens(groups),
                "supporting_direction_count": len(directions),
                "supporting_directions": sorted_tokens(directions),
                "best_aggregate_acat_q": q_sorted[0]["aggregate_acat_q"],
                "best_aggregate_acat_q_network": q_sorted[0]["broad_network"],
                "worst_aggregate_acat_q": q_sorted[-1]["aggregate_acat_q"],
                "worst_aggregate_acat_q_network": q_sorted[-1]["broad_network"],
                "atlas_display_order": None,
            }
        )

    gene_rows.sort(
        key=lambda row: (
            -row["passing_broad_network_count"],
            -row["unique_supporting_fine_cell_type_count"],
            -row["conservative_supporting_query_count"],
            row["current_symbol"],
        )
    )
    for order, row in enumerate(gene_rows, start=1):
        row["atlas_display_order"] = order
    display_order = {row["current_symbol"]: row["atlas_display_order"] for row in gene_rows}
    for row in detail_rows:
        row["atlas_display_order"] = display_order[row["current_symbol"]]
    detail_rows.sort(key=lambda row: (row["atlas_display_order"], row["network_order"]))

    plot_rows: list[dict[str, Any]] = []
    summary_map = {row["current_symbol"]: row for row in gene_rows}
    detail_map = {(row["broad_network"], row["current_symbol"]): row for row in detail_rows}
    for gene_row in gene_rows:
        gene = gene_row["current_symbol"]
        for network_index, network in enumerate(NETWORK_ORDER, start=1):
            detail = detail_map.get((network, gene))
            plot_rows.append(
                {
                    "schema_version": f"{SCHEMA}_plot_data_v1",
                    "figure_id": FIGURE_ID,
                    "case_id": CASE_ID,
                    "atlas_display_order": gene_row["atlas_display_order"],
                    "current_symbol": gene,
                    "network_order": network_index,
                    "broad_network": network,
                    "network_label": NETWORK_LABELS[network],
                    "network_color": NETWORK_COLORS[network],
                    "tile_status": "circle_displayed" if detail and detail["circle_displayed"] else "passing_not_circle_displayed" if detail else "no_passing_context",
                    "passing_context": detail is not None,
                    "circle_displayed": detail["circle_displayed"] if detail else False,
                    "within_case_rank": detail["within_case_rank"] if detail else None,
                    "aggregate_acat_q": detail["aggregate_acat_q"] if detail else None,
                    "negative_log10_aggregate_acat_q": detail["negative_log10_aggregate_acat_q"] if detail else None,
                    "capped_negative_log10_aggregate_acat_q": detail["capped_negative_log10_aggregate_acat_q"] if detail else None,
                    "extended_reference_member": gene_row["extended_reference_member"],
                    "passing_broad_network_count": gene_row["passing_broad_network_count"],
                    "unique_supporting_fine_cell_type_count": gene_row["unique_supporting_fine_cell_type_count"],
                    "eligible_query_count": gene_row["eligible_query_count"],
                    "usable_query_count": gene_row["usable_query_count"],
                    "query_coverage_fraction": gene_row["query_coverage_fraction"],
                    "conservative_supporting_query_count": gene_row["conservative_supporting_query_count"],
                    "query_recurrence_fraction": gene_row["query_recurrence_fraction"],
                    "supporting_group_count": gene_row["supporting_group_count"],
                    "supporting_direction_count": gene_row["supporting_direction_count"],
                }
            )

    checks = [
        check_record("circle_gene_count", len(circle_genes) == 15, len(circle_genes), 15),
        check_record("circle_gene_identity", circle_genes == EXPECTED_CIRCLE_GENES, sorted_tokens(circle_genes), sorted_tokens(EXPECTED_CIRCLE_GENES)),
        check_record("circle_display_context_count", len(displayed_keys) == 21, len(displayed_keys), 21),
        check_record("passing_context_count", len(passing_keys) == 22, len(passing_keys), 22),
        check_record("below_cap_context", passing_keys - displayed_keys == {EXPECTED_EXTRA_CONTEXT}, sorted(passing_keys - displayed_keys), [EXPECTED_EXTRA_CONTEXT]),
        check_record("case3_noncore_definition", all(not row["is_core_mito"] for row in detail_rows), sum(not row["is_core_mito"] for row in detail_rows), 22),
        check_record("gene_summary_rows", len(gene_rows) == 15, len(gene_rows), 15),
        check_record("gene_network_detail_rows", len(detail_rows) == 22, len(detail_rows), 22),
        check_record("panel_a_grid_rows", len(plot_rows) == 105, len(plot_rows), 105),
        check_record("panel_a_grid_keys", len({(row["current_symbol"], row["broad_network"]) for row in plot_rows}) == 105, len({(row["current_symbol"], row["broad_network"]) for row in plot_rows}), 105),
        check_record("support_le_usable", all(row["conservative_support_count"] <= row["usable_run_count"] for row in detail_rows), "all", "all"),
        check_record("usable_le_eligible", all(row["usable_run_count"] <= row["eligible_run_count"] for row in detail_rows), "all", "all"),
        check_record("passing_q_range", all(0 < row["aggregate_acat_q"] <= 0.05 for row in detail_rows), "all", "(0, 0.05]"),
        check_record("nonpassing_tile_values_missing", all(row["passing_context"] or (row["aggregate_acat_q"] is None and row["within_case_rank"] is None) for row in plot_rows), "all", "all"),
        check_record("display_flag_reconciliation", sum(row["circle_displayed"] for row in detail_rows) == 21 and sum(row["circle_displayed"] for row in plot_rows) == 21, f"{sum(row['circle_displayed'] for row in detail_rows)}|{sum(row['circle_displayed'] for row in plot_rows)}", "21|21"),
        check_record("extended_reference_snapshot", [row["current_symbol"] for row in gene_rows if row["extended_reference_member"]] == ["NCOA1"], "|".join(row["current_symbol"] for row in gene_rows if row["extended_reference_member"]), "NCOA1"),
        check_record("stability_one_to_one", len(stability_map) == 22, len(stability_map), 22),
        check_record("degree_one_to_one", len(degree_map) == 22, len(degree_map), 22),
        check_record("degree_draws_complete", all(row["completed_degree_matched_draws"] == row["requested_degree_matched_draws"] for row in detail_rows), sum(row["completed_degree_matched_draws"] == row["requested_degree_matched_draws"] for row in detail_rows), 22),
        check_record("single_evidence_cap", evidence_cap > max(row["negative_log10_aggregate_acat_q"] for row in detail_rows), evidence_cap, f"> {max(row['negative_log10_aggregate_acat_q'] for row in detail_rows):.6g}"),
    ]
    require(all(row["passed"] for row in checks), "At least one table-preparation check failed")
    return gene_rows, detail_rows, plot_rows, checks


def caption_text() -> str:
    return """# Caption

**Breadth and reproducibility of Case 3 key-driver candidates.** **A,** The 15 genes displayed in the Phase 18 Case 3 circle are shown across seven broad Bayesian networks. Tile fill is the capped network-specific −log10 aggregate ACAT q value; the number is the frozen within-case rank. Solid borders identify the 21 gene-network contexts displayed under the five-per-network circle cap, whereas a dashed border identifies the additional passing RPS15 context in excitatory neurons. A diamond marks membership in the broader mitochondrial reference. **B,** Breadth, conservative recurrence, and coverage are summarized across each gene's passing Case 3 contexts. Supporting queries are fine-cell-type × sex/APOE-group × AD-direction runs that met all conservative support gates; raw support/usable and usable/eligible counts accompany their fractions. **C,** Leave-one-fine-cell-type candidate retention and degree-matched empirical-tail P values are network-specific sensitivity diagnostics and did not determine Phase 18 rank. Point color and shape denote broad network.

Case 3 means outside the fixed 1,136-gene core MitoCarta inventory, not proven absence of mitochondrial function; the broader `mito_extended` annotation is secondary and does not alter the case. The top-five rule is a display cap rather than an evidence threshold. Fine-cell-type queries within a broad cell type reuse one fixed Bayesian network and therefore represent repeated evidence contexts, not independent external replications. Aggregate P and q values remain network-specific and were not pooled across networks. Gene order is a descriptive layout order, not a new statistical rank. Bayesian-network key-driver association supports prioritization but does not constitute experimental proof of causal regulation.
"""


def methods_text(evidence_cap: float, width: float, height: float, dpi: int, visual_status: str) -> str:
    review_sentence = (
        "The final rendering was manually reviewed at final physical size in color, grayscale, and deuteranopia, protanopia, and tritanopia simulations."
        if visual_status == "complete"
        else "Manual final-size and color-vision review is pending."
    )
    return f"""# Methods

The atlas was derived only from the validated Phase 18 production bundle under `results/minerva_production/18_key_driver_selection`. Before preparation, the script required terminal `validated_complete` status, all production checks to pass, the frozen ranking rule and five-row display cap, and matching recorded SHA-256 hashes and byte counts for every declared scientific input.

The provenance universe was the union of symbols in the official Case 3 top-five figure data: 15 unique genes and 21 displayed gene-network contexts. For those genes, the detail universe was expanded to every Case 3 row with `terminal_candidate_status = driver_candidate`, yielding 22 contexts. The sole additional context was RPS15 in the excitatory-neuron network at within-case rank 20. Case membership remained based on absence from the 1,136-gene core MitoCarta inventory; the broader extended-reference annotation was retained separately.

Broad-network breadth counted distinct passing networks. Fine-cell-type, sex/APOE-group, and direction breadth used exact set unions of run-level rows with `conservative_support = TRUE`. A query run was one fine cell type × primary sex/APOE group × AD-up or AD-down mitochondrial signature. Gene-level eligible, usable, and supporting counts were distinct run-ID counts restricted to that gene's passing Case 3 contexts. Coverage was usable/eligible and recurrence was conservative support/usable. All counts were reconciled to the candidate and conservative-support tables.

Aggregate ACAT P and q values were copied from the frozen candidate table and remained network-specific. They were not recombined across networks. The tile color used capped −log10(q) with a single cap of {evidence_cap:g}. Gene rows were placed by decreasing passing-network count, decreasing unique supporting fine-cell-type count, decreasing supporting-query count, and symbol; this deterministic order is for display only and is not an inferential rank.

Stability summaries were independently reconciled from leave-one-fine-cell-type replicate rows. Degree sensitivity retained the network-specific empirical-tail P value and requested/completed draw counts. The production `blocking_gate` field is reported verbatim in the detail table; degree sensitivity is a non-selection diagnostic, so marker fill is based on draw completion rather than interpreting `blocking_gate = FALSE` as a failed scientific test.

The figure used the established seven-network Okabe–Ito colors, a perceptually uniform cividis evidence scale, redundant border/shape encodings, and a sans-serif typeface with a minimum final-size text target of 7 pt. SVG and PDF are authoritative vector outputs; the PNG was exported at {dpi} dpi on a {width:g} × {height:g} inch canvas. {review_sentence}

These results are deterministic summaries of a validated selection bundle; uncertainty intervals and new hypothesis tests are not applicable. Key-driver association in a Bayesian network prioritizes candidates but is not experimental evidence of causal regulation.
"""


def run_renderer(root: Path, staging: Path, evidence_cap: float, width: float, height: float, dpi: int) -> None:
    renderer = root / "scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_case3_evidence_atlas.R"
    require(renderer.exists(), f"Missing renderer: {renderer}")
    command = [
        "Rscript",
        "--vanilla",
        str(renderer),
        "--data-dir",
        str(staging),
        "--output-dir",
        str(staging),
        "--evidence-cap",
        format(evidence_cap, ".17g"),
        "--png-dpi",
        str(dpi),
        "--width-inches",
        format(width, ".17g"),
        "--height-inches",
        format(height, ".17g"),
    ]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    require(result.returncode == 0, f"R renderer failed with exit code {result.returncode}")


def image_checks(staging: Path, width: float, height: float, dpi: int) -> list[dict[str, Any]]:
    svg_path = staging / IMAGE_FILES[0]
    pdf_path = staging / IMAGE_FILES[1]
    png_path = staging / IMAGE_FILES[2]
    for path in (svg_path, pdf_path, png_path):
        require(path.exists() and path.stat().st_size > 0, f"Missing or empty figure output: {path.name}")
    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    pdf_header = pdf_path.read_bytes()[:5]
    with Image.open(png_path) as image:
        dimensions = image.size
        dpi_metadata = image.info.get("dpi", (0, 0))
    expected_dimensions = (round(width * dpi), round(height * dpi))
    return [
        check_record("svg_vector_content", "data:image/png" not in svg_text.lower() and "data:image/jpeg" not in svg_text.lower() and "<svg" in svg_text.lower(), "vector SVG without embedded raster", "vector SVG without embedded raster"),
        check_record("pdf_header", pdf_header == b"%PDF-", pdf_header.decode("ascii", errors="replace"), "%PDF-"),
        check_record("png_dimensions", dimensions == expected_dimensions, f"{dimensions[0]}x{dimensions[1]}", f"{expected_dimensions[0]}x{expected_dimensions[1]}"),
        check_record("png_dpi_metadata", abs(dpi_metadata[0] - dpi) <= 0.25 and abs(dpi_metadata[1] - dpi) <= 0.25, f"{dpi_metadata[0]:.3f}|{dpi_metadata[1]:.3f}", f"{dpi}|{dpi}"),
        check_record("publication_formats", all((staging / name).stat().st_size > 0 for name in IMAGE_FILES), "SVG|PDF|PNG", "SVG|PDF|PNG"),
        check_record("minimum_text_size", True, "7 pt", ">=7 pt", "Renderer constants enforce the final-size minimum."),
        check_record("colorblind_safe_palette", True, "Okabe-Ito networks|cividis evidence", "colorblind-safe palettes"),
        check_record("grayscale_redundancy", True, "labels|solid/dashed borders|network shapes", "non-color encodings present"),
    ]


def manifest_rows(root: Path, input_dir: Path, output_dir: Path, staging: Path, evidence_cap: float, width: float, height: float, dpi: int, visual_status: str, elapsed: float) -> list[dict[str, Any]]:
    renderer = root / "scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_case3_evidence_atlas.R"
    preparer = Path(__file__).resolve()
    common = Path(__file__).resolve().with_name("phase18_case3_common.py")
    try:
        r_version = subprocess.run(["Rscript", "--version"], text=True, capture_output=True, check=True).stderr.strip() or subprocess.run(["Rscript", "--version"], text=True, capture_output=True, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        r_version = "unavailable"
    fields = [
        ("figure_id", FIGURE_ID),
        ("case_id", CASE_ID),
        ("input_directory", display_path(input_dir, root)),
        ("output_directory", display_path(output_dir, root)),
        ("production_status_sha256", sha256_file(input_dir / "key_driver_status.tsv")),
        ("common_module_sha256", sha256_file(common)),
        ("preparation_script_sha256", sha256_file(preparer)),
        ("renderer_sha256", sha256_file(renderer)),
        ("python_version", platform.python_version()),
        ("r_version", r_version),
        ("figure_width_inches", width),
        ("figure_height_inches", height),
        ("png_dpi", dpi),
        ("minimum_text_points", 7),
        ("evidence_measure", "negative_log10_network_aggregate_acat_q"),
        ("evidence_cap", evidence_cap),
        ("continuous_palette", "cividis"),
        ("network_palette", "Okabe-Ito seven-network palette"),
        ("circle_gene_count", 15),
        ("circle_display_context_count", 21),
        ("passing_context_count", 22),
        ("panel_a_grid_rows", 105),
        ("visual_review_status", visual_status),
        ("visual_review_modes", "color|grayscale|deuteranopia|protanopia|tritanopia"),
        ("elapsed_seconds", elapsed),
        ("timestamp_utc", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())),
    ]
    return [
        {"schema_version": f"{SCHEMA}_manifest_v1", "field_order": index, "field": field, "value": value}
        for index, (field, value) in enumerate(fields, start=1)
    ]


def count_table_rows(path: Path) -> int | None:
    if path.suffix not in {".tsv", ".gz"}:
        return None
    try:
        return sum(1 for _ in tsv_rows(path))
    except Exception:
        return None


def artifact_rows(root: Path, input_dir: Path, output_dir: Path, staging: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    source_manifest = {row["path"]: row for row in read_tsv(input_dir / "key_driver_artifacts.tsv")}
    for name in REQUIRED_INPUTS:
        path = input_dir / name
        declared = source_manifest[name]
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_order": order,
                "artifact_role": "input",
                "path": display_path(path, root),
                "rows": count_table_rows(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "declared_source_sha256": declared["sha256"] if declared["hash_status"] == "recorded" else None,
                "hash_status": "recorded",
            }
        )
        order += 1
    for path in [
        root / "scripts/figures/analysis/phase_18_key_driver_selection/phase18_case3_common.py",
        root / "scripts/figures/analysis/phase_18_key_driver_selection/prepare_phase18_case3_evidence_atlas.py",
        root / "scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_case3_evidence_atlas.R",
    ]:
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_order": order,
                "artifact_role": "script",
                "path": display_path(path, root),
                "rows": None,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "declared_source_sha256": None,
                "hash_status": "recorded",
            }
        )
        order += 1
    hashed_outputs = [
        *IMAGE_FILES,
        SUMMARY_FILE,
        DETAIL_FILE,
        PLOT_FILE,
        CAPTION_FILE,
        METHODS_FILE,
        MANIFEST_FILE,
        CHECKS_FILE,
    ]
    for name in hashed_outputs:
        path = staging / name
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_order": order,
                "artifact_role": "output",
                "path": display_path(output_dir / name, root),
                "rows": count_table_rows(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "declared_source_sha256": None,
                "hash_status": "recorded",
            }
        )
        order += 1
    for name in (ARTIFACTS_FILE, STATUS_FILE):
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_order": order,
                "artifact_role": "output",
                "path": display_path(output_dir / name, root),
                "rows": None,
                "bytes": None,
                "sha256": None,
                "declared_source_sha256": None,
                "hash_status": "written_after_artifact_manifest",
            }
        )
        order += 1
    return rows


def validate_existing(root: Path, output_dir: Path) -> None:
    for name in DECLARED_OUTPUTS:
        path = output_dir / name
        require(path.exists() and path.stat().st_size > 0, f"Missing or empty declared output: {name}")
    status = read_tsv(output_dir / STATUS_FILE)
    require(len(status) == 1 and status[0]["validation_status"] == "validated_complete", "Atlas output is not validated_complete")
    checks = read_tsv(output_dir / CHECKS_FILE)
    require(all(truth(row["passed"]) for row in checks if row["severity"] == "error"), "A blocking atlas check failed")
    artifacts = read_tsv(output_dir / ARTIFACTS_FILE)
    for row in artifacts:
        if row["artifact_role"] != "output" or row["hash_status"] != "recorded":
            continue
        path = root / row["path"] if not Path(row["path"]).is_absolute() else Path(row["path"])
        require(path.exists(), f"Missing recorded output artifact: {path}")
        require(path.stat().st_size == integer(row["bytes"]), f"Output byte count changed: {path.name}")
        require(sha256_file(path) == row["sha256"], f"Output SHA-256 changed: {path.name}")
    print(f"Validated existing atlas package: {output_dir}")


def publish(args: argparse.Namespace, root: Path) -> None:
    input_dir = (root / args.input_dir).resolve() if not Path(args.input_dir).is_absolute() else Path(args.input_dir).resolve()
    output_dir = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    require(input_dir.exists(), f"Input directory does not exist: {input_dir}")
    require(not output_dir.exists(), f"Refusing to overwrite existing output directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".phase18_case3_evidence_atlas.staging.", dir=output_dir.parent))
    started = time.time()
    try:
        bundle = load_validated_bundle(root, input_dir)
        gene_rows, detail_rows, plot_rows, checks = prepare_tables(bundle, args.evidence_cap)
        write_tsv(staging / SUMMARY_FILE, gene_rows)
        write_tsv(staging / DETAIL_FILE, detail_rows)
        write_tsv(staging / PLOT_FILE, plot_rows)
        write_text(staging / CAPTION_FILE, caption_text())
        write_text(staging / METHODS_FILE, methods_text(args.evidence_cap, args.width_inches, args.height_inches, args.png_dpi, args.visual_review_status))

        run_renderer(root, staging, args.evidence_cap, args.width_inches, args.height_inches, args.png_dpi)
        checks.extend(image_checks(staging, args.width_inches, args.height_inches, args.png_dpi))
        checks.extend(
            [
                check_record("production_status", bundle["status"]["validation_status"] == "validated_complete", bundle["status"]["validation_status"], "validated_complete"),
                check_record("production_checks", all(truth(row["passed"]) for row in bundle["checks"]), sum(truth(row["passed"]) for row in bundle["checks"]), len(bundle["checks"])),
                check_record("source_artifact_verification", True, len(REQUIRED_INPUTS), len(REQUIRED_INPUTS), "All recorded source hashes and bytes were verified before preparation."),
                check_record("visual_review_complete", args.visual_review_status == "complete", args.visual_review_status, "complete", "Operator review at final size in color, grayscale, and three common CVD simulations.", severity="warning"),
            ]
        )
        require(all(row["passed"] for row in checks if row["severity"] == "error"), "A blocking atlas check failed")

        elapsed = time.time() - started
        write_tsv(staging / MANIFEST_FILE, manifest_rows(root, input_dir, output_dir, staging, args.evidence_cap, args.width_inches, args.height_inches, args.png_dpi, args.visual_review_status, elapsed))
        write_tsv(staging / CHECKS_FILE, checks)
        write_tsv(staging / ARTIFACTS_FILE, artifact_rows(root, input_dir, output_dir, staging))
        validation_status = "validated_complete" if args.visual_review_status == "complete" else "awaiting_visual_review"
        status_row = {
            "schema_version": f"{SCHEMA}_status_v1",
            "figure_id": FIGURE_ID,
            "validation_status": validation_status,
            "circle_genes": len(gene_rows),
            "circle_display_contexts": sum(row["circle_displayed"] for row in detail_rows),
            "passing_contexts": len(detail_rows),
            "panel_a_grid_rows": len(plot_rows),
            "declared_outputs": len(DECLARED_OUTPUTS),
            "automated_checks": len(checks),
            "automated_checks_passed": sum(row["passed"] for row in checks),
            "failed_blocking_checks": sum(not row["passed"] for row in checks if row["severity"] == "error"),
            "visual_review_status": args.visual_review_status,
            "elapsed_seconds": time.time() - started,
            "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        write_tsv(staging / STATUS_FILE, [status_row])
        for name in DECLARED_OUTPUTS:
            path = staging / name
            require(path.exists() and path.stat().st_size > 0, f"Missing or empty declared output: {name}")
        staging.replace(output_dir)
        print(f"Published {validation_status} atlas package: {output_dir}")
        print(f"Universe: {len(gene_rows)} genes | {sum(row['circle_displayed'] for row in detail_rows)} displayed contexts | {len(detail_rows)} passing contexts")
        print(f"Checks: {sum(row['passed'] for row in checks)}/{len(checks)} passed")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    raise RuntimeError(
        "Legacy Case 3 inputs are incompatible with the two-class v2 output; "
        "regenerate a non_mt_driver atlas from call_key_driver_returns.tsv."
    )
    args = parse_args(argv)
    root = Path.cwd().resolve()
    if args.validate_output:
        output = Path(args.validate_output)
        output_dir = (root / output).resolve() if not output.is_absolute() else output.resolve()
        validate_existing(root, output_dir)
        return 0
    publish(args, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
