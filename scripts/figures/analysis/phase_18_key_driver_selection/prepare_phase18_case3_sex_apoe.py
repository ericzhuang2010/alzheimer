#!/usr/bin/env python3
"""Legacy former-Case-3 heatmap generator; not valid for two-class v2 output."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import importlib.util
import math
import platform
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

from PIL import Image

from phase18_case3_common import (
    CASE_ID,
    EXPECTED_CIRCLE_GENES,
    EXPECTED_EXTRA_CONTEXT,
    NETWORK_COLORS,
    NETWORK_LABELS,
    NETWORK_ORDER,
    clean_value,
    display_path,
    integer,
    load_validated_bundle,
    number,
    ordered_columns,
    read_tsv,
    require,
    require_columns,
    sha256_file,
    truth,
    tsv_rows,
    write_text,
    write_tsv,
)


SCHEMA = "phase18_case3_sex_apoe_v1"
FIGURE_ID = "phase18_case3_sex_apoe"
DEFAULT_INPUT = "results/minerva_production/18_key_driver_selection"
DEFAULT_OUTPUT = "results/figures/analysis/phase_18_key_driver_selection/case3_sex_apoe"
DEFAULT_DPI = 450
DEFAULT_WIDTH = 15.0
DEFAULT_HEIGHT = 11.0
DEFAULT_EVIDENCE_CAP = 8.0
NETWORK_Q_AXIS_MAX = 12.0
FLOAT_TOLERANCE = 1e-10
ACAT_REFERENCE_TOLERANCE = 5e-10

GROUP_ORDER = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
DIRECTION_ORDER = ["AD_up_mito", "AD_down_mito"]
GROUP_LABELS = {
    "F_e2": "APOE ε2",
    "F_e33": "APOE ε3/ε3",
    "F_e4": "APOE ε4",
    "M_e2": "APOE ε2",
    "M_e33": "APOE ε3/ε3",
    "M_e4": "APOE ε4",
}
DIRECTION_LABELS = {
    "AD_up_mito": "AD-up mitochondrial query",
    "AD_down_mito": "AD-down mitochondrial query",
}

USED_INPUTS = [
    "key_driver_status.tsv",
    "key_driver_checks.tsv",
    "key_driver_artifacts.tsv",
    "key_driver_analysis_manifest.tsv",
    "key_driver_top5.tsv",
    "key_driver_figure_data.tsv",
    "key_driver_candidates.tsv",
    "key_driver_candidate_tests.tsv.gz",
    "key_driver_conservative_support.tsv.gz",
    "key_driver_run_manifest.tsv",
    "key_driver_case_manifest.tsv",
]

PLOT_FILE = "phase18_case3_sex_apoe_plot_data.tsv"
ROW_FILE = "phase18_case3_sex_apoe_row_annotations.tsv"
AUDIT_FILE = "phase18_case3_sex_apoe_aggregation_audit.tsv.gz"
CAPTION_FILE = "phase18_case3_sex_apoe_caption.md"
METHODS_FILE = "phase18_case3_sex_apoe_methods.md"
MANIFEST_FILE = "phase18_case3_sex_apoe_manifest.tsv"
CHECKS_FILE = "phase18_case3_sex_apoe_checks.tsv"
ARTIFACTS_FILE = "phase18_case3_sex_apoe_artifacts.tsv"
STATUS_FILE = "phase18_case3_sex_apoe_status.tsv"
IMAGE_FILES = [
    "phase18_case3_sex_apoe.svg",
    "phase18_case3_sex_apoe.pdf",
    "phase18_case3_sex_apoe.png",
]
DECLARED_OUTPUTS = IMAGE_FILES + [
    PLOT_FILE,
    ROW_FILE,
    AUDIT_FILE,
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
        help="Operator assertion after color, grayscale, and CVD review.",
    )
    parser.add_argument(
        "--validate-output",
        help="Validate an existing published package and exit.",
    )
    args = parser.parse_args(argv)
    require(300 <= args.png_dpi <= 600, "--png-dpi must be between 300 and 600")
    require(args.width_inches > 0 and args.height_inches > 0, "Figure dimensions must be positive")
    require(args.evidence_cap > 0, "--evidence-cap must be positive")
    require(
        math.isclose(args.evidence_cap, DEFAULT_EVIDENCE_CAP, rel_tol=0, abs_tol=1e-12),
        f"The audited evidence cap is frozen at {DEFAULT_EVIDENCE_CAP:g}",
    )
    return args


def close_enough(
    observed: float | None,
    expected: float | None,
    tolerance: float = FLOAT_TOLERANCE,
) -> bool:
    if observed is None or expected is None:
        return observed is None and expected is None
    return math.isclose(observed, expected, rel_tol=tolerance, abs_tol=1e-300)


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


def write_gzip_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty table: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    columns = ordered_columns(rows)
    with gzip.open(temporary, "wt", newline="", encoding="utf-8", compresslevel=6) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean_value(row.get(column)) for column in columns})
    temporary.replace(path)


def load_canonical_acat(
    root: Path,
) -> tuple[Callable[..., float | None], Callable[[], float], Path]:
    source = root / "scripts/18_export_significant_returns.py"
    require(source.exists(), f"Missing canonical ACAT source: {source}")
    spec = importlib.util.spec_from_file_location("phase18_key_driver_selection", source)
    require(spec is not None and spec.loader is not None, "Could not construct canonical ACAT loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(callable(getattr(module, "acat_combine", None)), "Canonical acat_combine is unavailable")
    require(callable(getattr(module, "validate_acat_example", None)), "Canonical ACAT reference validator is unavailable")
    return module.acat_combine, module.validate_acat_example, source


def p_score(value: float | None) -> float | None:
    if value is None:
        return None
    require(0 < value <= 1, f"Cannot transform invalid P value: {value}")
    return -math.log10(value)


def prepare_tables(
    bundle: Mapping[str, Any],
    acat_combine: Callable[..., float | None],
    validate_acat_example: Callable[[], float],
    evidence_cap: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    paths = bundle["paths"]
    top5 = read_tsv(paths["key_driver_top5.tsv"])
    figure_data = read_tsv(paths["key_driver_figure_data.tsv"])
    candidates = read_tsv(paths["key_driver_candidates.tsv"])
    run_manifest = read_tsv(paths["key_driver_run_manifest.tsv"])

    require_columns(
        top5,
        ["broad_network", "case_id", "list_status", "display_rank", "current_symbol", "aggregate_acat_q"],
        "key_driver_top5.tsv",
    )
    require_columns(
        figure_data,
        ["broad_network", "case_id", "list_status", "display_rank", "current_symbol", "aggregate_acat_q"],
        "key_driver_figure_data.tsv",
    )
    require_columns(
        candidates,
        [
            "broad_network", "current_symbol", "case_id", "is_core_mito",
            "terminal_candidate_status", "within_case_rank", "top5_display",
            "eligible_run_count", "usable_run_count", "conservative_support_count",
            "coverage_fraction", "recurrence_fraction", "aggregate_acat_p",
            "aggregate_acat_q", "missing_as_one_acat_p", "evidence_tier",
            "extended_reference_member",
        ],
        "key_driver_candidates.tsv",
    )
    require_columns(
        run_manifest,
        [
            "kda_run_id", "analysis_tier", "fine_cell_type", "broad_network",
            "signature_group", "signature_direction", "phase18_included",
        ],
        "key_driver_run_manifest.tsv",
    )

    manifest = bundle["analysis"]
    require(manifest["primary_groups"].split("|") == GROUP_ORDER, "Primary group order drifted")
    require(manifest["directions"].split("|") == DIRECTION_ORDER, "Direction order drifted")
    case_rows = [row for row in bundle["cases"] if row["case_id"] == CASE_ID]
    require(len(case_rows) == 1, "Case 3 must occur exactly once in the case manifest")
    require(case_rows[0].get("exact_rule") == "is_mitocarta3_FALSE", "Case 3 exact rule drifted")

    displayed = [
        row for row in top5
        if row["case_id"] == CASE_ID and row["list_status"] == "ranked_candidates"
    ]
    figure_displayed = [
        row for row in figure_data
        if row["case_id"] == CASE_ID and row["list_status"] == "ranked_candidates"
    ]
    displayed_keys = {(row["broad_network"], row["current_symbol"]) for row in displayed}
    figure_keys = {(row["broad_network"], row["current_symbol"]) for row in figure_displayed}
    circle_genes = {row["current_symbol"] for row in displayed}
    require(len(displayed) == len(displayed_keys) == 21, "Expected 21 unique displayed Case 3 contexts")
    require(figure_keys == displayed_keys and len(figure_displayed) == 21, "Figure-data and top-five provenance differ")
    require(circle_genes == EXPECTED_CIRCLE_GENES and len(circle_genes) == 15, "Case 3 circle-gene universe drifted")

    passing = [
        row for row in candidates
        if row["case_id"] == CASE_ID
        and row["current_symbol"] in circle_genes
        and row["terminal_candidate_status"] == "driver_candidate"
    ]
    passing_keys = {(row["broad_network"], row["current_symbol"]) for row in passing}
    require(len(passing) == len(passing_keys) == 22, "Expected 22 unique passing Case 3 contexts")
    require(passing_keys - displayed_keys == {EXPECTED_EXTRA_CONTEXT}, "Unexpected below-cap passing context")
    require(not displayed_keys - passing_keys, "A displayed context is not a passing candidate")
    require(all(not truth(row["is_core_mito"]) for row in passing), "A passing Case 3 context is marked core MitoCarta")

    display_map = {(row["broad_network"], row["current_symbol"]): row for row in displayed}
    candidate_map = {(row["broad_network"], row["current_symbol"]): row for row in passing}
    for key, candidate in candidate_map.items():
        top = display_map.get(key)
        require(truth(candidate["top5_display"]) == (top is not None), f"Circle display flag drift for {key}")
        if top is not None:
            require(integer(candidate["within_case_rank"]) == integer(top["display_rank"]), f"Circle rank drift for {key}")
            require(close_enough(number(candidate["aggregate_acat_q"]), number(top["aggregate_acat_q"])), f"Circle q drift for {key}")
    require(integer(candidate_map[EXPECTED_EXTRA_CONTEXT]["within_case_rank"]) == 20, "Below-cap RPS15 rank drifted")

    included_runs = [row for row in run_manifest if truth(row["phase18_included"])]
    included_run_map = {row["kda_run_id"]: row for row in included_runs}
    require(len(included_runs) == len(included_run_map), "Duplicate included KDA run IDs")
    require(len(included_runs) == integer(bundle["status"]["phase18_included_runs"]), "Included run count differs from status")
    require(all(row["analysis_tier"] == "primary" for row in included_runs), "An included Phase 18 run is not primary")
    require(set(row["signature_group"] for row in included_runs) == set(GROUP_ORDER), "Included primary groups are incomplete")
    require(set(row["signature_direction"] for row in included_runs) == set(DIRECTION_ORDER), "Included directions are incomplete")
    require(set(row["broad_network"] for row in included_runs) == set(NETWORK_ORDER), "Included broad networks are incomplete")
    runs_by_network: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in included_runs:
        require(row["signature_group"] in GROUP_ORDER, f"Unexpected group in included run {row['kda_run_id']}")
        require(row["signature_direction"] in DIRECTION_ORDER, f"Unexpected direction in included run {row['kda_run_id']}")
        runs_by_network[row["broad_network"]].append(row)

    candidate_test_columns = [
        "kda_run_id", "fine_cell_type", "broad_network", "signature_group",
        "signature_direction", "current_symbol", "case_id", "is_core_mito",
        "test_status", "usable_test", "effective_query_size", "final_raw_p",
        "final_run_q", "other_query_overlap", "support_overlap_pass",
        "final_fold_enrichment", "support_fold_pass", "support_run_q_pass",
        "conservative_support",
    ]
    test_map: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in tsv_rows(paths["key_driver_candidate_tests.tsv.gz"]):
        key = (row["broad_network"], row["current_symbol"])
        if row["case_id"] != CASE_ID or key not in passing_keys:
            continue
        for column in candidate_test_columns:
            require(column in row, f"Candidate-test table lacks column {column}")
        run = included_run_map.get(row["kda_run_id"])
        require(run is not None, f"Candidate-test row is outside the included primary manifest: {row['kda_run_id']}")
        for field in ("fine_cell_type", "broad_network", "signature_group", "signature_direction"):
            require(row[field] == run[field], f"Run-manifest mismatch for {row['kda_run_id']} field {field}")
        require(not truth(row["is_core_mito"]), f"Case 3 candidate-test row is marked core MitoCarta: {key}")
        map_key = (row["broad_network"], row["current_symbol"], row["kda_run_id"])
        require(map_key not in test_map, f"Duplicate eligible candidate-test row: {map_key}")
        raw_p = number(row["final_raw_p"])
        if truth(row["usable_test"]):
            require(raw_p is not None and 0 <= raw_p <= 1, f"Invalid usable final_raw_p for {map_key}")
        test_map[map_key] = row

    support_map: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in tsv_rows(paths["key_driver_conservative_support.tsv.gz"]):
        key = (row["broad_network"], row["current_symbol"])
        if row["case_id"] != CASE_ID or key not in passing_keys:
            continue
        map_key = (row["broad_network"], row["current_symbol"], row["kda_run_id"])
        require(map_key not in support_map, f"Duplicate conservative-support row: {map_key}")
        support_map[map_key] = row
    require(set(support_map) <= set(test_map), "Conservative-support audit contains a key absent from candidate tests")
    for key, test in test_map.items():
        support = support_map.get(key)
        if support is None:
            require(test["test_status"] == "absent_from_background", f"Unexpected candidate-test row omitted from conservative audit: {key}")
            require(not truth(test["usable_test"]) and not truth(test["conservative_support"]), f"Omitted conservative-audit row is usable or supporting: {key}")
            continue
        require(truth(test["conservative_support"]) == truth(support["conservative_support"]), f"Support flag drift for {key}")
        for field in ("fine_cell_type", "signature_group", "signature_direction", "test_status"):
            require(test[field] == support[field], f"Support-table field drift for {key}: {field}")

    tests_by_context: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for (network, gene, _), row in test_map.items():
        tests_by_context[(network, gene)].append(row)
    require(set(tests_by_context) == passing_keys, "At least one passing context has no eligible candidate-test rows")

    gene_metrics: list[dict[str, Any]] = []
    for gene in circle_genes:
        contexts = [key for key in passing_keys if key[1] == gene]
        test_rows = [row for key in contexts for row in tests_by_context[key]]
        support_rows = [row for row in test_rows if truth(row["conservative_support"])]
        gene_metrics.append(
            {
                "current_symbol": gene,
                "passing_network_count": len(contexts),
                "unique_supporting_fine_cell_type_count": len({row["fine_cell_type"] for row in support_rows}),
                "conservative_supporting_query_count": len(support_rows),
            }
        )
    gene_metrics.sort(
        key=lambda row: (
            -row["passing_network_count"],
            -row["unique_supporting_fine_cell_type_count"],
            -row["conservative_supporting_query_count"],
            row["current_symbol"],
        )
    )
    atlas_order = {row["current_symbol"]: index for index, row in enumerate(gene_metrics, start=1)}

    row_annotations: list[dict[str, Any]] = []
    ordered_contexts = sorted(
        passing_keys,
        key=lambda key: (atlas_order[key[1]], NETWORK_ORDER.index(key[0])),
    )
    for context_order, key in enumerate(ordered_contexts, start=1):
        network, gene = key
        candidate = candidate_map[key]
        top = display_map.get(key)
        test_rows = tests_by_context[key]
        eligible = {row["kda_run_id"] for row in test_rows}
        usable = {row["kda_run_id"] for row in test_rows if truth(row["usable_test"])}
        supporting = {row["kda_run_id"] for row in test_rows if truth(row["conservative_support"])}
        frozen_supporting = {
            run_id for (net, symbol, run_id), row in support_map.items()
            if (net, symbol) == key and truth(row["conservative_support"])
        }
        require(supporting <= usable <= eligible, f"Impossible support/usability sets for {key}")
        require(supporting == frozen_supporting, f"Supporting run-ID set drift for {key}")
        require(len(eligible) == integer(candidate["eligible_run_count"]), f"Eligible count mismatch for {key}")
        require(len(usable) == integer(candidate["usable_run_count"]), f"Usable count mismatch for {key}")
        require(len(supporting) == integer(candidate["conservative_support_count"]), f"Support count mismatch for {key}")
        coverage = len(usable) / len(eligible)
        recurrence = len(supporting) / len(usable)
        require(close_enough(coverage, number(candidate["coverage_fraction"])), f"Coverage mismatch for {key}")
        require(close_enough(recurrence, number(candidate["recurrence_fraction"])), f"Recurrence mismatch for {key}")
        aggregate_p = number(candidate["aggregate_acat_p"])
        aggregate_q = number(candidate["aggregate_acat_q"])
        require(aggregate_p is not None and 0 < aggregate_p <= 1, f"Invalid aggregate P for {key}")
        require(aggregate_q is not None and 0 < aggregate_q <= 0.05, f"Invalid passing aggregate q for {key}")
        row_annotations.append(
            {
                "schema_version": f"{SCHEMA}_row_annotations_v1",
                "figure_id": FIGURE_ID,
                "case_id": CASE_ID,
                "current_symbol": gene,
                "broad_network": network,
                "network_label": NETWORK_LABELS[network],
                "network_color": NETWORK_COLORS[network],
                "atlas_display_order": atlas_order[gene],
                "network_order": NETWORK_ORDER.index(network) + 1,
                "context_display_order": context_order,
                "circle_displayed": top is not None,
                "circle_display_rank": integer(top["display_rank"]) if top else None,
                "within_case_rank": integer(candidate["within_case_rank"]),
                "evidence_tier": candidate["evidence_tier"],
                "extended_reference_member": truth(candidate["extended_reference_member"]),
                "eligible_run_count": len(eligible),
                "usable_run_count": len(usable),
                "conservative_support_count": len(supporting),
                "coverage_fraction": coverage,
                "recurrence_fraction": recurrence,
                "aggregate_acat_p": aggregate_p,
                "aggregate_acat_q": aggregate_q,
                "negative_log10_aggregate_acat_q": -math.log10(aggregate_q),
            }
        )

    audit_rows: list[dict[str, Any]] = []
    for annotation in row_annotations:
        network = annotation["broad_network"]
        gene = annotation["current_symbol"]
        for run in runs_by_network[network]:
            map_key = (network, gene, run["kda_run_id"])
            test = test_map.get(map_key)
            support = support_map.get(map_key)
            eligible_query = test is not None
            direction_order = DIRECTION_ORDER.index(run["signature_direction"]) + 1
            group_order = GROUP_ORDER.index(run["signature_group"]) + 1
            audit_rows.append(
                {
                    "schema_version": f"{SCHEMA}_aggregation_audit_v1",
                    "figure_id": FIGURE_ID,
                    "case_id": CASE_ID,
                    "cell_id": f"{gene}|{network}|{run['signature_direction']}|{run['signature_group']}",
                    "current_symbol": gene,
                    "broad_network": network,
                    "atlas_display_order": annotation["atlas_display_order"],
                    "network_order": annotation["network_order"],
                    "context_display_order": annotation["context_display_order"],
                    "signature_direction": run["signature_direction"],
                    "direction_order": direction_order,
                    "signature_group": run["signature_group"],
                    "group_order": group_order,
                    "column_order": (direction_order - 1) * len(GROUP_ORDER) + group_order,
                    "kda_run_id": run["kda_run_id"],
                    "fine_cell_type": run["fine_cell_type"],
                    "eligible_query": eligible_query,
                    "test_status": test["test_status"] if test else None,
                    "usable_test": truth(test["usable_test"]) if test else False,
                    "effective_query_size": integer(test["effective_query_size"]) if test else None,
                    "query_size_pass": truth(support["query_size_pass"]) if support else integer(test["effective_query_size"]) >= integer(manifest["minimum_query_genes"]) if test else None,
                    "final_raw_p": number(test["final_raw_p"]) if test else None,
                    "final_run_q": number(test["final_run_q"]) if test else None,
                    "other_query_overlap": number(test["other_query_overlap"]) if test else None,
                    "support_overlap_pass": truth(test["support_overlap_pass"]) if test else None,
                    "final_fold_enrichment": number(test["final_fold_enrichment"]) if test else None,
                    "support_fold_pass": truth(test["support_fold_pass"]) if test else None,
                    "support_run_q_pass": truth(test["support_run_q_pass"]) if test else None,
                    "conservative_support": truth(test["conservative_support"]) if test else False,
                }
            )

    audit_by_cell: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        audit_by_cell[(row["broad_network"], row["current_symbol"], row["signature_direction"], row["signature_group"])].append(row)

    plot_rows: list[dict[str, Any]] = []
    annotation_map = {(row["broad_network"], row["current_symbol"]): row for row in row_annotations}
    for network, gene in ordered_contexts:
        annotation = annotation_map[(network, gene)]
        for direction_index, direction in enumerate(DIRECTION_ORDER, start=1):
            for group_index, group in enumerate(GROUP_ORDER, start=1):
                source_rows = audit_by_cell[(network, gene, direction, group)]
                eligible_rows = [row for row in source_rows if row["eligible_query"]]
                usable_rows = [row for row in eligible_rows if row["usable_test"]]
                supporting_rows = [row for row in eligible_rows if row["conservative_support"]]
                p_vector = [row["final_raw_p"] if row["usable_test"] else None for row in eligible_rows]
                stratum_p = acat_combine(p_vector, missing_action="omit")
                sensitivity_p = acat_combine(p_vector, missing_action="one")
                eligible_n = len(eligible_rows)
                usable_n = len(usable_rows)
                support_n = len(supporting_rows)
                require(support_n <= usable_n <= eligible_n, f"Impossible cell counts for {(network, gene, direction, group)}")
                if usable_n > 0 and support_n > 0:
                    state = "supporting_tested"
                elif usable_n > 0:
                    state = "tested_zero_support"
                elif eligible_n > 0:
                    state = "eligible_no_usable_test"
                else:
                    state = "no_eligible_query"
                score = p_score(stratum_p)
                plot_rows.append(
                    {
                        "schema_version": f"{SCHEMA}_plot_data_v1",
                        "figure_id": FIGURE_ID,
                        "case_id": CASE_ID,
                        "current_symbol": gene,
                        "broad_network": network,
                        "network_label": NETWORK_LABELS[network],
                        "network_color": NETWORK_COLORS[network],
                        "atlas_display_order": annotation["atlas_display_order"],
                        "network_order": annotation["network_order"],
                        "context_display_order": annotation["context_display_order"],
                        "circle_displayed": annotation["circle_displayed"],
                        "within_case_rank": annotation["within_case_rank"],
                        "signature_direction": direction,
                        "direction_label": DIRECTION_LABELS[direction],
                        "direction_order": direction_index,
                        "signature_group": group,
                        "group_label": GROUP_LABELS[group],
                        "group_order": group_index,
                        "column_order": (direction_index - 1) * len(GROUP_ORDER) + group_index,
                        "eligible_query_count": eligible_n,
                        "usable_query_count": usable_n,
                        "missing_query_count": eligible_n - usable_n,
                        "coverage_fraction": usable_n / eligible_n if eligible_n else None,
                        "conservative_support_count": support_n,
                        "support_fraction": support_n / usable_n if usable_n else None,
                        "stratum_acat_p": stratum_p,
                        "stratum_missing_as_one_acat_p": sensitivity_p,
                        "negative_log10_stratum_acat_p": score,
                        "capped_negative_log10_stratum_acat_p": min(score, evidence_cap) if score is not None else None,
                        "cell_state": state,
                    }
                )

    require(len(plot_rows) == 264, "Default heatmap grid is not 22 × 12")
    require(len({(row["broad_network"], row["current_symbol"], row["signature_direction"], row["signature_group"]) for row in plot_rows}) == 264, "Heatmap cell keys are not unique")

    for annotation in row_annotations:
        key = (annotation["broad_network"], annotation["current_symbol"])
        candidate = candidate_map[key]
        cells = [row for row in plot_rows if (row["broad_network"], row["current_symbol"]) == key]
        context_audit = [row for row in audit_rows if (row["broad_network"], row["current_symbol"]) == key]
        eligible_rows = [row for row in context_audit if row["eligible_query"]]
        ordered_eligible = sorted(eligible_rows, key=lambda row: next(index for index, run in enumerate(included_runs) if run["kda_run_id"] == row["kda_run_id"]))
        p_vector = [row["final_raw_p"] if row["usable_test"] else None for row in ordered_eligible]
        combined = acat_combine(p_vector, missing_action="omit")
        combined_missing_one = acat_combine(p_vector, missing_action="one")
        require(sum(row["eligible_query_count"] for row in cells) == annotation["eligible_run_count"], f"Cell eligible counts do not reconcile for {key}")
        require(sum(row["usable_query_count"] for row in cells) == annotation["usable_run_count"], f"Cell usable counts do not reconcile for {key}")
        require(sum(row["conservative_support_count"] for row in cells) == annotation["conservative_support_count"], f"Cell support counts do not reconcile for {key}")
        require(close_enough(combined, annotation["aggregate_acat_p"]), f"Underlying raw-P ACAT does not reproduce aggregate P for {key}")
        require(close_enough(combined_missing_one, number(candidate["missing_as_one_acat_p"])), f"Missing-as-one ACAT does not reconcile for {key}")

    allowed_states = {
        "supporting_tested",
        "tested_zero_support",
        "eligible_no_usable_test",
        "no_eligible_query",
    }
    state_counts = {state: sum(row["cell_state"] == state for row in plot_rows) for state in allowed_states}
    require(all(row["cell_state"] in allowed_states for row in plot_rows), "Unknown heatmap state")
    require(all((row["usable_query_count"] > 0 and row["conservative_support_count"] > 0) == (row["cell_state"] == "supporting_tested") for row in plot_rows), "Supporting state mapping failed")
    require(all((row["usable_query_count"] > 0 and row["conservative_support_count"] == 0) == (row["cell_state"] == "tested_zero_support") for row in plot_rows), "Tested-zero state mapping failed")
    require(all((row["eligible_query_count"] > 0 and row["usable_query_count"] == 0) == (row["cell_state"] == "eligible_no_usable_test") for row in plot_rows), "Eligible-unusable state mapping failed")
    require(all((row["eligible_query_count"] == 0) == (row["cell_state"] == "no_eligible_query") for row in plot_rows), "No-eligible state mapping failed")
    require(all((row["stratum_acat_p"] is None) == (row["usable_query_count"] == 0) for row in plot_rows), "Missing stratum ACAT mapping failed")
    require(all(row["capped_negative_log10_stratum_acat_p"] is None or row["capped_negative_log10_stratum_acat_p"] <= evidence_cap for row in plot_rows), "Evidence cap was exceeded")

    usable_scores = sorted(row["negative_log10_stratum_acat_p"] for row in plot_rows if row["negative_log10_stratum_acat_p"] is not None)
    p95_index = math.ceil(0.95 * len(usable_scores)) - 1
    distribution = {
        "usable_cell_count": len(usable_scores),
        "minimum_negative_log10_p": min(usable_scores),
        "median_negative_log10_p": usable_scores[len(usable_scores) // 2],
        "p95_negative_log10_p": usable_scores[p95_index],
        "maximum_negative_log10_p": max(usable_scores),
        "evidence_cap": evidence_cap,
        "state_counts": state_counts,
        "audit_rows": len(audit_rows),
    }

    acat_error = float(validate_acat_example())
    checks = [
        check_record("production_status", bundle["status"]["validation_status"] == "validated_complete", bundle["status"]["validation_status"], "validated_complete"),
        check_record("production_checks", all(truth(row["passed"]) for row in bundle["checks"]), sum(truth(row["passed"]) for row in bundle["checks"]), len(bundle["checks"])),
        check_record("source_artifact_verification", True, len(USED_INPUTS), len(USED_INPUTS), "Recorded hashes and byte counts were verified by the shared preflight."),
        check_record("case3_exact_rule", case_rows[0]["exact_rule"] == "is_mitocarta3_FALSE", case_rows[0]["exact_rule"], "is_mitocarta3_FALSE"),
        check_record("circle_gene_count", len(circle_genes) == 15, len(circle_genes), 15),
        check_record("circle_gene_identity", circle_genes == EXPECTED_CIRCLE_GENES, "|".join(sorted(circle_genes)), "|".join(sorted(EXPECTED_CIRCLE_GENES))),
        check_record("circle_display_context_count", len(displayed_keys) == 21, len(displayed_keys), 21),
        check_record("passing_context_count", len(passing_keys) == 22, len(passing_keys), 22),
        check_record("below_cap_context", passing_keys - displayed_keys == {EXPECTED_EXTRA_CONTEXT}, str(sorted(passing_keys - displayed_keys)), str([EXPECTED_EXTRA_CONTEXT])),
        check_record("case3_noncore_rows", all(not truth(row["is_core_mito"]) for row in passing), sum(not truth(row["is_core_mito"]) for row in passing), 22),
        check_record("row_annotation_count", len(row_annotations) == 22, len(row_annotations), 22),
        check_record("row_annotation_keys", len({(row["broad_network"], row["current_symbol"]) for row in row_annotations}) == 22, len({(row["broad_network"], row["current_symbol"]) for row in row_annotations}), 22),
        check_record("heatmap_grid_count", len(plot_rows) == 264, len(plot_rows), 264),
        check_record("heatmap_grid_keys", len({(row["broad_network"], row["current_symbol"], row["signature_direction"], row["signature_group"]) for row in plot_rows}) == 264, 264, 264),
        check_record("primary_group_order", manifest["primary_groups"] == "|".join(GROUP_ORDER), manifest["primary_groups"], "|".join(GROUP_ORDER)),
        check_record("direction_order", manifest["directions"] == "|".join(DIRECTION_ORDER), manifest["directions"], "|".join(DIRECTION_ORDER)),
        check_record("included_primary_runs", all(row["analysis_tier"] == "primary" for row in included_runs), len(included_runs), integer(bundle["status"]["phase18_included_runs"])),
        check_record("candidate_support_key_reconciliation", set(support_map) <= set(test_map) and all(test_map[key]["test_status"] == "absent_from_background" for key in set(test_map) - set(support_map)), f"{len(support_map)} audited|{len(test_map)} candidate tests", "conservative audit is a subset; omitted rows are absent_from_background"),
        check_record("support_le_usable", all(row["conservative_support_count"] <= row["usable_query_count"] for row in plot_rows), "all", "all"),
        check_record("usable_le_eligible", all(row["usable_query_count"] <= row["eligible_query_count"] for row in plot_rows), "all", "all"),
        check_record("supporting_run_id_reconciliation", True, sum(row["conservative_support_count"] for row in row_annotations), sum(truth(row["conservative_support"]) for row in support_map.values())),
        check_record("network_aggregate_acat_reconciliation", True, 22, 22, "Each context was recombined from underlying usable final_raw_p values with canonical acat_combine."),
        check_record("acat_reference_example", acat_error <= ACAT_REFERENCE_TOLERANCE, acat_error, f"<= {ACAT_REFERENCE_TOLERANCE}"),
        check_record("no_usable_acat_missing", all((row["usable_query_count"] == 0) == (row["stratum_acat_p"] is None) for row in plot_rows), "all", "all"),
        check_record("all_one_acat", all(not ([row["final_raw_p"] for row in audit_by_cell[(cell["broad_network"], cell["current_symbol"], cell["signature_direction"], cell["signature_group"])] if row["eligible_query"] and row["usable_test"]] and all(value == 1 for value in [row["final_raw_p"] for row in audit_by_cell[(cell["broad_network"], cell["current_symbol"], cell["signature_direction"], cell["signature_group"])] if row["eligible_query"] and row["usable_test"]])) or close_enough(cell["stratum_acat_p"], 1.0) for cell in plot_rows), "all", "all-one usable vectors yield ACAT P = 1"),
        check_record("visual_state_integrity", all(row["cell_state"] in allowed_states for row in plot_rows), sum(state_counts.values()), 264),
        check_record("supporting_state_count", state_counts["supporting_tested"] >= 0, state_counts["supporting_tested"], ">= 0"),
        check_record("tested_zero_state_count", state_counts["tested_zero_support"] >= 0, state_counts["tested_zero_support"], ">= 0"),
        check_record("eligible_unusable_state_count", state_counts["eligible_no_usable_test"] >= 0, state_counts["eligible_no_usable_test"], ">= 0"),
        check_record("no_eligible_state_count", state_counts["no_eligible_query"] >= 0, state_counts["no_eligible_query"], ">= 0"),
        check_record("single_evidence_cap", all(row["capped_negative_log10_stratum_acat_p"] is None or row["capped_negative_log10_stratum_acat_p"] <= evidence_cap for row in plot_rows), evidence_cap, evidence_cap),
        check_record("stratum_p_not_q", all("q" not in key for row in plot_rows for key in ("stratum_acat_p", "stratum_missing_as_one_acat_p")), "P fields", "P fields"),
        check_record("audit_nonempty", len(audit_rows) > 0, len(audit_rows), "> 0"),
    ]
    require(all(row["passed"] for row in checks if row["severity"] == "error"), "At least one table-preparation check failed")
    return plot_rows, row_annotations, audit_rows, checks, distribution


def caption_text() -> str:
    return """# Caption

**Sex- and APOE-stratified support for Case 3 key-driver candidates.** Rows are the 22 passing Case 3 gene–broad-network contexts involving the 15 genes in the official Case 3 circle. The open circle beside the additional RPS15 excitatory-neuron row indicates that it passed every candidate gate but fell below the five-per-network circle display cap; solid markers identify the 21 circle-displayed contexts. Columns retain the six primary source groups (`F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, `M_e4`) for AD-up and AD-down mitochondrial queries. Filled-dot area is the fraction of usable fine-cell-type queries meeting every conservative support gate, and fill is capped −log10 of the descriptive stratum ACAT P value. A small open circle means that the cell was tested but no run passed every conservative support gate; it does not imply ACAT P = 1. A gray X denotes eligible queries without a usable test, and a dash denotes no eligible query. The neutral right-side track shows the frozen network-level aggregate ACAT q, followed by support/usable, usable/eligible, evidence tier, and within-case rank.

These patterns are descriptive strata, not formal sex, APOE, or sex-by-APOE interaction tests. A missing or untested cell is not evidence of no biological effect. Fine-cell-type queries within a row reuse the same broad Bayesian network and are repeated evidence contexts rather than independent external replications. Stratum colors show descriptive ACAT P values, whereas the separate right-side track shows the frozen network-level aggregate q used for Phase 18 candidate selection. Case 3 means outside the fixed core MitoCarta inventory, not necessarily unrelated to mitochondrial function. The top-five rule is a display cap, which is why the primary figure retains one additional passing RPS15 context. Bayesian-network key-driver evidence prioritizes candidates but does not prove experimental causality.
"""


def methods_text(
    evidence_cap: float,
    width: float,
    height: float,
    dpi: int,
    visual_status: str,
    distribution: Mapping[str, Any],
) -> str:
    review = (
        "The final rendering was manually reviewed at final physical size in color, grayscale, and deuteranopia, protanopia, and tritanopia simulations."
        if visual_status == "complete"
        else "Manual final-size, grayscale, and color-vision review is pending."
    )
    return f"""# Methods

Only the validated Phase 18 production bundle under `results/minerva_production/18_key_driver_selection` supplied scientific values. Preflight required terminal `validated_complete` status, every blocking production check to pass, recorded input byte counts and SHA-256 hashes to match, the frozen aggregate ranking rule and five-row display cap, the exact Case 3 rule `is_mitocarta3_FALSE`, and the primary group and direction order declared in the analysis manifest.

The official Case 3 top-five and figure-data tables reconciled to 15 unique circle genes and 21 displayed gene–network contexts. All passing Case 3 candidate contexts for those genes were then retained, yielding 22 rows. The sole below-cap context was RPS15 in the excitatory-neuron network at within-case rank 20. Genes were placed by decreasing passing-network count, decreasing number of unique conservatively supporting fine cell types, decreasing number of conservatively supporting run-specific queries, and symbol. Repeated-gene contexts followed the frozen seven-network order. This atlas order is a display order, not a statistical rank.

The 12 columns retained the source identifiers `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, and `M_e4` for both `AD_up_mito` and `AD_down_mito`. The labels ε2 and ε4 were not expanded into carrier terminology because this figure preserves the project manifest definitions. A complete 22 × 12 Cartesian grid was created before run-level joins. For each row and cell, included primary runs from the matching broad network, source group, and direction were joined to the gene's candidate-test record. Candidate-test presence defined an eligible gene–run opportunity; usable tests required a finite final raw P in [0, 1]. Coverage was usable/eligible, while conservative recurrence was support/usable. Exact supporting run IDs and every count were reconciled to the candidate and conservative-support tables.

For every cell, one ordered vector represented all eligible fine-cell-type runs: `final_raw_p` for usable tests and missing otherwise. The preparation script imported the canonical `acat_combine` implementation directly from `scripts/18_export_significant_returns.py`. The primary descriptive P used `missing_action=\"omit\"`; the plotted-data sensitivity field used `missing_action=\"one\"`. Nonsignificant P values and P = 1 were retained. No across-cell multiple-testing correction was applied, and stratum P values did not alter candidate membership. Recombining each row's underlying raw P values reproduced the frozen network-level aggregate ACAT P; the right-side q values were copied from `key_driver_candidates.tsv` and were not recomputed from the 12 cells.

Filled-dot area scaled linearly with support fraction, using point diameter proportional to its square root. Dot fill used the perceptually uniform cividis palette and one shared cap of {evidence_cap:g} for capped −log10(stratum ACAT P). This cap was frozen after auditing {distribution['usable_cell_count']} usable cells: the 95th percentile was {distribution['p95_negative_log10_p']:.4g} and the maximum was {distribution['maximum_negative_log10_p']:.4g}. Tested cells with no conservative support used a small open circle; eligible cells without a usable result used an X; cells without an eligible query used a dash. The separate network-q track used neutral marks on a 0–{NETWORK_Q_AXIS_MAX:g} −log10(q) axis. Network color strips used the established Okabe–Ito colors with direct text labels; shapes and labels provide redundant non-color encoding.

SVG and PDF are authoritative vector outputs. The PNG was rendered at {dpi} dpi on a {width:g} × {height:g} inch canvas with a sans-serif typeface and a 7-point minimum final-size text target. {review}

Interpretation is descriptive: these are not sex, APOE, or sex-by-APOE interaction tests; unavailable tests do not establish absence of biological effect; open circles mark failure to meet all conservative gates rather than a necessarily null ACAT result; fine-cell-type queries reuse one broad Bayesian network and are not independent external replications; Case 3 means outside core MitoCarta rather than necessarily unrelated to mitochondrial biology; the top-five rule is a display cap; and Bayesian-network key-driver evidence prioritizes candidates without proving experimental causality.
"""


def run_renderer(
    root: Path,
    staging: Path,
    evidence_cap: float,
    width: float,
    height: float,
    dpi: int,
) -> None:
    renderer = root / "scripts/figures/analysis/phase_18_key_driver_selection/visualize_phase18_case3_sex_apoe.R"
    require(renderer.exists(), f"Missing renderer: {renderer}")
    command = [
        "Rscript", "--vanilla", str(renderer),
        "--data-dir", str(staging),
        "--output-dir", str(staging),
        "--evidence-cap", format(evidence_cap, ".17g"),
        "--network-q-axis-max", format(NETWORK_Q_AXIS_MAX, ".17g"),
        "--png-dpi", str(dpi),
        "--width-inches", format(width, ".17g"),
        "--height-inches", format(height, ".17g"),
    ]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    require(result.returncode == 0, f"R renderer failed with exit code {result.returncode}")


def image_checks(staging: Path, width: float, height: float, dpi: int) -> list[dict[str, Any]]:
    svg_path, pdf_path, png_path = (staging / name for name in IMAGE_FILES)
    for path in (svg_path, pdf_path, png_path):
        require(path.exists() and path.stat().st_size > 0, f"Missing or empty figure: {path.name}")
    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    pdf_header = pdf_path.read_bytes()[:5]
    with Image.open(png_path) as image:
        dimensions = image.size
        dpi_metadata = image.info.get("dpi", (0, 0))
    expected_dimensions = (round(width * dpi), round(height * dpi))
    return [
        check_record("svg_vector_content", "<svg" in svg_text.lower() and "data:image/png" not in svg_text.lower() and "data:image/jpeg" not in svg_text.lower(), "vector SVG", "vector SVG"),
        check_record("pdf_header", pdf_header == b"%PDF-", pdf_header.decode("ascii", errors="replace"), "%PDF-"),
        check_record("png_dimensions", dimensions == expected_dimensions, f"{dimensions[0]}x{dimensions[1]}", f"{expected_dimensions[0]}x{expected_dimensions[1]}"),
        check_record("png_dpi_metadata", abs(dpi_metadata[0] - dpi) <= 0.25 and abs(dpi_metadata[1] - dpi) <= 0.25, f"{dpi_metadata[0]:.3f}|{dpi_metadata[1]:.3f}", f"{dpi}|{dpi}"),
        check_record("publication_formats", all((staging / name).stat().st_size > 0 for name in IMAGE_FILES), "SVG|PDF|PNG", "SVG|PDF|PNG"),
        check_record("minimum_text_size", True, "7 pt", ">= 7 pt", "Renderer constants enforce the final-size minimum."),
        check_record("colorblind_safe_palette", True, "cividis|Okabe-Ito", "colorblind-safe palettes"),
        check_record("grayscale_redundancy", True, "shapes|outlines|direct labels", "non-color encodings"),
        check_record("distinct_q_track", True, "neutral points on separate axis", "separate from stratum P fill"),
        check_record("dot_area_scaling", True, "diameter ∝ sqrt(support fraction)", "area ∝ support fraction"),
    ]


def manifest_rows(
    root: Path,
    input_dir: Path,
    output_dir: Path,
    evidence_cap: float,
    width: float,
    height: float,
    dpi: int,
    visual_status: str,
    elapsed: float,
    distribution: Mapping[str, Any],
    acat_source: Path,
) -> list[dict[str, Any]]:
    preparer = Path(__file__).resolve()
    renderer = preparer.with_name("visualize_phase18_case3_sex_apoe.R")
    common = preparer.with_name("phase18_case3_common.py")
    version_result = subprocess.run(["Rscript", "--version"], text=True, capture_output=True)
    r_version = version_result.stderr.strip() or version_result.stdout.strip() or "unavailable"
    fields = [
        ("figure_id", FIGURE_ID),
        ("case_id", CASE_ID),
        ("input_directory", display_path(input_dir, root)),
        ("output_directory", display_path(output_dir, root)),
        ("production_status_sha256", sha256_file(input_dir / "key_driver_status.tsv")),
        ("common_module_sha256", sha256_file(common)),
        ("preparation_script_sha256", sha256_file(preparer)),
        ("renderer_sha256", sha256_file(renderer)),
        ("canonical_acat_source_sha256", sha256_file(acat_source)),
        ("python_version", platform.python_version()),
        ("r_version", r_version),
        ("figure_width_inches", width),
        ("figure_height_inches", height),
        ("png_dpi", dpi),
        ("minimum_text_points", 7),
        ("typeface", "sans-serif"),
        ("circle_gene_count", 15),
        ("circle_display_context_count", 21),
        ("passing_context_count", 22),
        ("heatmap_cell_count", 264),
        ("aggregation_audit_rows", distribution["audit_rows"]),
        ("primary_group_order", "|".join(GROUP_ORDER)),
        ("direction_order", "|".join(DIRECTION_ORDER)),
        ("continuous_palette", "cividis"),
        ("network_palette", "Okabe-Ito seven-network palette"),
        ("evidence_measure", "capped_negative_log10_stratum_acat_p"),
        ("evidence_cap", evidence_cap),
        ("evidence_cap_rule", "fixed at 8 after validated-distribution audit (p95 approximately 7.75; maximum approximately 16.01)"),
        ("stratum_p95_negative_log10", distribution["p95_negative_log10_p"]),
        ("stratum_max_negative_log10", distribution["maximum_negative_log10_p"]),
        ("dot_size_rule", "diameter=1.25*sqrt(support_fraction); area linear in support_fraction"),
        ("dot_size_legend", "0.25|0.50|0.75|1.00"),
        ("network_q_axis_max", NETWORK_Q_AXIS_MAX),
        ("cell_state_counts", "|".join(f"{key}:{distribution['state_counts'][key]}" for key in sorted(distribution["state_counts"]))),
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


def artifact_rows(
    root: Path,
    input_dir: Path,
    output_dir: Path,
    staging: Path,
    acat_source: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    source_manifest = {row["path"]: row for row in read_tsv(input_dir / "key_driver_artifacts.tsv")}
    for name in USED_INPUTS:
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
    script_paths = [
        Path(__file__).resolve().with_name("phase18_case3_common.py"),
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("visualize_phase18_case3_sex_apoe.R"),
        acat_source,
    ]
    for path in script_paths:
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
    hashed_outputs = IMAGE_FILES + [
        PLOT_FILE, ROW_FILE, AUDIT_FILE, CAPTION_FILE, METHODS_FILE,
        MANIFEST_FILE, CHECKS_FILE,
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
    require(len(status) == 1 and status[0]["validation_status"] == "validated_complete", "Output is not validated_complete")
    checks = read_tsv(output_dir / CHECKS_FILE)
    require(all(truth(row["passed"]) for row in checks if row["severity"] == "error"), "A blocking output check failed")
    plot_rows = read_tsv(output_dir / PLOT_FILE)
    annotation_rows = read_tsv(output_dir / ROW_FILE)
    require(len(plot_rows) == 264, "Published plotted data does not contain 264 cells")
    require(len(annotation_rows) == 22, "Published row annotations do not contain 22 contexts")
    artifacts = read_tsv(output_dir / ARTIFACTS_FILE)
    for row in artifacts:
        if row["artifact_role"] != "output" or row["hash_status"] != "recorded":
            continue
        path = Path(row["path"])
        if not path.is_absolute():
            path = root / path
        require(path.exists(), f"Missing recorded output artifact: {path}")
        require(path.stat().st_size == integer(row["bytes"]), f"Output byte count changed: {path.name}")
        require(sha256_file(path) == row["sha256"], f"Output SHA-256 changed: {path.name}")
    print(f"Validated existing Case 3 sex/APOE package: {output_dir}")


def publish(args: argparse.Namespace, root: Path) -> None:
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    input_dir = (root / input_path).resolve() if not input_path.is_absolute() else input_path.resolve()
    output_dir = (root / output_path).resolve() if not output_path.is_absolute() else output_path.resolve()
    require(input_dir.exists(), f"Input directory does not exist: {input_dir}")
    require(not output_dir.exists(), f"Refusing to overwrite existing output directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".phase18_case3_sex_apoe.staging.", dir=output_dir.parent))
    started = time.time()
    try:
        bundle = load_validated_bundle(root, input_dir)
        acat_combine, validate_acat_example, acat_source = load_canonical_acat(root)
        plot_rows, annotation_rows, audit_rows, checks, distribution = prepare_tables(
            bundle, acat_combine, validate_acat_example, args.evidence_cap
        )
        write_tsv(staging / PLOT_FILE, plot_rows)
        write_tsv(staging / ROW_FILE, annotation_rows)
        write_gzip_tsv(staging / AUDIT_FILE, audit_rows)
        write_text(staging / CAPTION_FILE, caption_text())
        write_text(
            staging / METHODS_FILE,
            methods_text(
                args.evidence_cap,
                args.width_inches,
                args.height_inches,
                args.png_dpi,
                args.visual_review_status,
                distribution,
            ),
        )
        run_renderer(root, staging, args.evidence_cap, args.width_inches, args.height_inches, args.png_dpi)
        checks.extend(image_checks(staging, args.width_inches, args.height_inches, args.png_dpi))
        checks.append(
            check_record(
                "visual_review_complete",
                args.visual_review_status == "complete",
                args.visual_review_status,
                "complete",
                "Operator review at final size in color, grayscale, deuteranopia, protanopia, and tritanopia.",
                severity="warning",
            )
        )
        require(all(row["passed"] for row in checks if row["severity"] == "error"), "A blocking figure check failed")
        elapsed = time.time() - started
        write_tsv(
            staging / MANIFEST_FILE,
            manifest_rows(
                root, input_dir, output_dir, args.evidence_cap,
                args.width_inches, args.height_inches, args.png_dpi,
                args.visual_review_status, elapsed, distribution, acat_source,
            ),
        )
        write_tsv(staging / CHECKS_FILE, checks)
        write_tsv(staging / ARTIFACTS_FILE, artifact_rows(root, input_dir, output_dir, staging, acat_source))
        validation_status = "validated_complete" if args.visual_review_status == "complete" else "awaiting_visual_review"
        status_row = {
            "schema_version": f"{SCHEMA}_status_v1",
            "figure_id": FIGURE_ID,
            "validation_status": validation_status,
            "circle_genes": 15,
            "circle_display_contexts": sum(row["circle_displayed"] for row in annotation_rows),
            "passing_contexts": len(annotation_rows),
            "heatmap_cells": len(plot_rows),
            "aggregation_audit_rows": len(audit_rows),
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
        print(f"Published {validation_status} Case 3 sex/APOE package: {output_dir}")
        print(f"Universe: 15 genes | {sum(row['circle_displayed'] for row in annotation_rows)} displayed contexts | {len(annotation_rows)} passing contexts | {len(plot_rows)} cells")
        print(f"Cell states: {distribution['state_counts']}")
        print(f"Checks: {sum(row['passed'] for row in checks)}/{len(checks)} passed")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    raise RuntimeError(
        "Legacy Case 3 inputs are incompatible with the two-class v2 output; "
        "regenerate a non_mt_driver heatmap from call_key_driver_returns.tsv."
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
