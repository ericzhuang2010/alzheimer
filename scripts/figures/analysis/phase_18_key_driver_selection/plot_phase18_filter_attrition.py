#!/usr/bin/env python3
"""Render and validate the Phase 18 five-filter attrition figure package.

The renderer consumes only the validated Phase 18 production bundle. It
reshapes saved filter decisions and exact counts; it never recomputes KDA,
ACAT, coverage, q values, or candidate status.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable, Iterator, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "phase18_filter_attrition_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "phase18_filter_attrition_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
from PIL import Image  # noqa: E402


SCHEMA = "phase18_filter_attrition_figure_v1"
FIGURE_ID = "phase18_filter_attrition"
FIGURE_WIDTH_IN = 7.2
FIGURE_HEIGHT_IN = 6.0
DEFAULT_PNG_DPI = 360

CASE_ORDER = [
    "case1_core_mito_in_query",
    "case2_core_mito_not_in_query",
    "case3_not_core_mito",
]
CASE_META = {
    "case1_core_mito_in_query": {
        "order": 1,
        "panel": "B",
        "short": "Case 1",
        "title": "MT-related and in query",
        "subtitle": "self-overlap removed",
        "color": "#0072B2",
    },
    "case2_core_mito_not_in_query": {
        "order": 2,
        "panel": "C",
        "short": "Case 2",
        "title": "MT-related and not in query",
        "subtitle": "query-independent mitochondrial gene",
        "color": "#009E73",
    },
    "case3_not_core_mito": {
        "order": 3,
        "panel": "D",
        "short": "Case 3",
        "title": "Outside core MitoCarta",
        "subtitle": "not one of the 1,136 core genes",
        "color": "#CC79A7",
    },
}

EXPECTED_FILTER1 = {"input": 648, "pass": 161, "fail": 487}
EXPECTED_FILTER2 = {
    "case1_core_mito_in_query": (7073, 7073, 0),
    "case2_core_mito_not_in_query": (112484, 98790, 13694),
    "case3_not_core_mito": (1343593, 1193919, 149674),
}
EXPECTED_DISTINCT = {
    "case1_core_mito_in_query": {"input": 877, 3: 47, 4: 47, 5: 27},
    "case2_core_mito_not_in_query": {"input": 902, 3: 34, 4: 33, 5: 18},
    "case3_not_core_mito": {"input": 11319, 3: 150, 4: 143, 5: 30},
}
EXPECTED_AGGREGATES = {
    "case1_core_mito_in_query": {"input": 2046, 3: 77, 4: 77, 5: 49},
    "case2_core_mito_not_in_query": {"input": 3625, 3: 43, 4: 42, 5: 23},
    "case3_not_core_mito": {"input": 43947, 3: 172, 4: 164, 5: 37},
}

DECLARED_OUTPUTS = [
    "phase18_filter_attrition.svg",
    "phase18_filter_attrition.pdf",
    "phase18_filter_attrition.png",
    "phase18_filter_attrition_plot_data.tsv",
    "phase18_filter_attrition_membership.tsv.gz",
    "phase18_filter_attrition_caption.md",
    "phase18_filter_attrition_methods.md",
    "phase18_filter_attrition_sources.tsv",
    "phase18_filter_attrition_checks.tsv",
    "phase18_filter_attrition_status.tsv",
]

REQUIRED_INPUTS = [
    "key_driver_status.tsv",
    "key_driver_artifacts.tsv",
    "key_driver_case_manifest.tsv",
    "key_driver_filter_funnel.tsv",
    "key_driver_candidate_tests.tsv.gz",
    "key_driver_gene_case_summary.tsv.gz",
    "key_driver_candidates.tsv",
]

FILTER_LABELS = {
    3: "conservative_support",
    4: "coverage",
    5: "aggregate_evidence",
}

LIGHT_REMOVED = "#E6E6E6"
MID_GRAY = "#7A7A7A"
DARK = "#262626"
LIGHT_LINE = "#BDBDBD"
SHARED_BLUE = "#56B4E9"


def configure_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 7,
            "axes.titlesize": 8.5,
            "axes.labelsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 0.9,
            "patch.linewidth": 0.7,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "svg.hashsalt": "phase18_filter_attrition_v1",
            "svg.fonttype": "none",
            "pdf.compression": 9,
            "pdf.fonttype": 42,
        }
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default="results/minerva_production/18_key_driver_selection",
    )
    parser.add_argument(
        "--output-dir",
        default="results/figures/analysis/phase_18_key_driver_selection/filter_attrition",
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    parser.add_argument(
        "--validate-output",
        help="Validate an existing output directory and exit without rendering.",
    )
    args = parser.parse_args(argv)
    if not 300 <= args.png_dpi <= 600:
        parser.error("--png-dpi must be between 300 and 600")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or value in ("TRUE", "True", "true", "1", 1)


def integer(value: Any) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Expected integer-like value, observed {value!r}") from error


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tsv_rows(path: Path) -> Iterator[dict[str, str]]:
    require(path.exists(), f"Missing TSV input: {path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_tsv(path: Path) -> list[dict[str, str]]:
    return list(tsv_rows(path))


def require_columns(
    rows: Sequence[Mapping[str, Any]], columns: Sequence[str], label: str
) -> None:
    require(bool(rows), f"{label} is empty")
    missing = [column for column in columns if column not in rows[0]]
    require(not missing, f"{label} missing columns: {', '.join(missing)}")


def ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = [
        "schema_version",
        "figure_id",
        "record_type",
        "panel_id",
        "case_order",
        "case_id",
    ]
    observed: list[str] = []
    for row in rows:
        for key in row:
            if key not in observed:
                observed.append(key)
    return [column for column in preferred if column in observed] + [
        column for column in observed if column not in preferred
    ]


def clean_value(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, float) and not math.isfinite(value):
        return "NA"
    return value


def write_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty table: {path}")
    columns = ordered_columns(rows)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean_value(row.get(column)) for column in columns})
    os.replace(temporary, path)


def write_tsv_gz(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty compressed table: {path}")
    columns = ordered_columns(rows)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("wb") as binary:
        with gzip.GzipFile(fileobj=binary, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=columns,
                    delimiter="\t",
                    lineterminator="\n",
                    extrasaction="ignore",
                )
                writer.writeheader()
                for row in rows:
                    writer.writerow(
                        {column: clean_value(row.get(column)) for column in columns}
                    )
    os.replace(temporary, path)


def write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def display_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(resolved)


def lighten(hex_color: str, fraction: float = 0.82) -> tuple[float, float, float]:
    red, green, blue = matplotlib.colors.to_rgb(hex_color)
    return (
        red + (1 - red) * fraction,
        green + (1 - green) * fraction,
        blue + (1 - blue) * fraction,
    )


def check_record(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    detail: str = "",
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "figure_id": FIGURE_ID,
        "check_id": check_id,
        "blocking": "TRUE" if blocking else "FALSE",
        "passed": "TRUE" if passed else "FALSE",
        "observed": observed,
        "expected": expected,
        "detail": detail,
    }


def load_bundle(root: Path, input_dir: Path) -> dict[str, Any]:
    paths = {name: input_dir / name for name in REQUIRED_INPUTS}
    for path in paths.values():
        require(path.exists(), f"Missing Phase 18 input: {path}")

    status = read_tsv(paths["key_driver_status.tsv"])
    require_columns(
        status,
        [
            "execution_stage",
            "validation_status",
            "phase18_structural_run_slots",
            "phase18_included_runs",
            "driver_candidates",
        ],
        "Phase 18 status",
    )
    require(len(status) == 1, "Phase 18 status must have exactly one row")
    require(
        status[0]["validation_status"] == "validated_complete",
        "Phase 18 production bundle is not validated_complete",
    )

    artifacts = read_tsv(paths["key_driver_artifacts.tsv"])
    require_columns(
        artifacts,
        ["path", "bytes", "sha256", "hash_status"],
        "Phase 18 artifact manifest",
    )
    artifact_lookup = {row["path"]: row for row in artifacts}
    hashed_input_names = [
        "key_driver_case_manifest.tsv",
        "key_driver_filter_funnel.tsv",
        "key_driver_candidate_tests.tsv.gz",
        "key_driver_gene_case_summary.tsv.gz",
        "key_driver_candidates.tsv",
    ]
    for name in hashed_input_names:
        require(name in artifact_lookup, f"Artifact manifest does not declare {name}")
        record = artifact_lookup[name]
        require(record["hash_status"] == "recorded", f"Artifact hash not recorded: {name}")
        require(integer(record["bytes"]) == paths[name].stat().st_size, f"Artifact bytes changed: {name}")
        require(record["sha256"] == sha256_file(paths[name]), f"Artifact hash changed: {name}")

    case_rows = read_tsv(paths["key_driver_case_manifest.tsv"])
    require_columns(case_rows, ["case_order", "case_id", "case_label"], "Case manifest")
    observed_case_order = [
        row["case_id"] for row in sorted(case_rows, key=lambda row: integer(row["case_order"]))
    ]
    require(observed_case_order == CASE_ORDER, "Phase 18 case order changed")

    funnel = read_tsv(paths["key_driver_filter_funnel.tsv"])
    require_columns(
        funnel,
        [
            "report_type",
            "summary_scope",
            "broad_network",
            "case_id",
            "filter_number",
            "filter_name",
            "counting_unit",
            "input_n",
            "pass_n",
            "fail_n",
            "cumulative_remaining_n",
        ],
        "Filter funnel",
    )

    filter1_rows = [
        row
        for row in funnel
        if row["report_type"] == "native_filter"
        and row["summary_scope"] == "overall"
        and row["filter_number"] == "1"
    ]
    require(len(filter1_rows) == 1, "Missing overall native Filter 1 row")
    filter1 = filter1_rows[0]
    observed_filter1 = {
        "input": integer(filter1["input_n"]),
        "pass": integer(filter1["pass_n"]),
        "fail": integer(filter1["fail_n"]),
    }
    require(observed_filter1 == EXPECTED_FILTER1, "Filter 1 checkpoint changed")

    filter2_overall_rows = [
        row
        for row in funnel
        if row["report_type"] == "native_filter"
        and row["summary_scope"] == "overall"
        and row["filter_number"] == "2"
    ]
    require(len(filter2_overall_rows) == 1, "Missing overall native Filter 2 row")
    filter2_overall = filter2_overall_rows[0]

    filter2 = {
        case: {
            "opportunities": 0,
            "usable": 0,
            "unavailable": 0,
            "explicit": 0,
            "implicit": 0,
            "absent": 0,
            "invalid": 0,
        }
        for case in CASE_ORDER
    }
    for row in tsv_rows(paths["key_driver_candidate_tests.tsv.gz"]):
        case = row["case_id"]
        require(case in filter2, f"Unexpected candidate-test case: {case}")
        summary = filter2[case]
        summary["opportunities"] += 1
        if truth(row["usable_test"]):
            summary["usable"] += 1
        else:
            summary["unavailable"] += 1
        status_id = row["test_status"]
        if status_id in {"explicit_test", "explicit_zero_overlap"}:
            summary["explicit"] += 1
        elif status_id == "implicit_zero_overlap":
            summary["implicit"] += 1
        elif status_id == "absent_from_background":
            summary["absent"] += 1
        elif status_id == "invalid_test":
            summary["invalid"] += 1
        else:
            raise RuntimeError(f"Unexpected Filter 2 test status: {status_id}")

    for case, expected in EXPECTED_FILTER2.items():
        observed = filter2[case]
        require(
            (observed["opportunities"], observed["usable"], observed["unavailable"])
            == expected,
            f"Filter 2 checkpoint changed for {case}",
        )
        require(
            observed["opportunities"] == observed["usable"] + observed["unavailable"],
            f"Filter 2 is not additive for {case}",
        )
        require(
            observed["usable"] == observed["explicit"] + observed["implicit"],
            f"Filter 2 usable components do not reconcile for {case}",
        )
        require(
            observed["unavailable"] == observed["absent"] + observed["invalid"],
            f"Filter 2 unavailable components do not reconcile for {case}",
        )

    total_filter2 = {
        key: sum(filter2[case][key] for case in CASE_ORDER)
        for key in filter2[CASE_ORDER[0]]
    }
    require(
        total_filter2["opportunities"] == integer(filter2_overall["input_n"]),
        "Case-specific Filter 2 opportunities do not match overall funnel",
    )
    require(
        total_filter2["usable"] == integer(filter2_overall["pass_n"]),
        "Case-specific Filter 2 usable count does not match overall funnel",
    )
    require(
        total_filter2["unavailable"] == integer(filter2_overall["fail_n"]),
        "Case-specific Filter 2 unavailable count does not match overall funnel",
    )
    require(total_filter2["invalid"] == 0, "Filter 2 contains invalid tests")

    sequential = [
        row
        for row in funnel
        if row["report_type"] == "sequential_candidate_funnel"
        and row["summary_scope"] == "broad_network_case"
    ]
    require(bool(sequential), "No broad-network × case sequential funnel rows")
    for row in sequential:
        require(row["case_id"] in CASE_ORDER, "Unexpected sequential case")
        require(integer(row["filter_number"]) in (3, 4, 5), "Unexpected sequential filter")
        require(
            integer(row["input_n"]) == integer(row["pass_n"]) + integer(row["fail_n"]),
            f"Nonadditive sequential row: {row}",
        )

    grouped_sequential: dict[tuple[str, str], dict[int, dict[str, str]]] = {}
    for row in sequential:
        key = (row["broad_network"], row["case_id"])
        grouped_sequential.setdefault(key, {})[integer(row["filter_number"])] = row
    for key, stages in grouped_sequential.items():
        require(set(stages) == {3, 4, 5}, f"Incomplete sequential funnel for {key}")
        require(integer(stages[4]["input_n"]) == integer(stages[3]["pass_n"]), f"Filter 3→4 mismatch for {key}")
        require(integer(stages[5]["input_n"]) == integer(stages[4]["pass_n"]), f"Filter 4→5 mismatch for {key}")

    funnel_aggregates = {
        case: {
            "input": sum(
                integer(row["input_n"])
                for row in sequential
                if row["case_id"] == case and row["filter_number"] == "3"
            ),
            **{
                filter_number: sum(
                    integer(row["pass_n"])
                    for row in sequential
                    if row["case_id"] == case
                    and row["filter_number"] == str(filter_number)
                )
                for filter_number in (3, 4, 5)
            },
        }
        for case in CASE_ORDER
    }
    require(funnel_aggregates == EXPECTED_AGGREGATES, "Aggregate funnel checkpoints changed")

    distinct_sets = {
        case: {"input": set(), 3: set(), 4: set(), 5: set()}
        for case in CASE_ORDER
    }
    summary_aggregates = {
        case: {"input": 0, 3: 0, 4: 0, 5: 0}
        for case in CASE_ORDER
    }
    membership: list[dict[str, Any]] = []
    final_keys: set[tuple[str, str, str]] = set()
    for row in tsv_rows(paths["key_driver_gene_case_summary.tsv.gz"]):
        case = row["case_id"]
        require(case in distinct_sets, f"Unexpected gene-summary case: {case}")
        gene = row["current_symbol"]
        network = row["broad_network"]
        support = truth(row["conservative_support_pass"])
        coverage = truth(row["coverage_pass"])
        aggregate_q = truth(row["aggregate_q_pass"])
        summary_aggregates[case]["input"] += 1
        distinct_sets[case]["input"].add(gene)
        if support:
            summary_aggregates[case][3] += 1
            distinct_sets[case][3].add(gene)
        if support and coverage:
            summary_aggregates[case][4] += 1
            distinct_sets[case][4].add(gene)
        if support and coverage and aggregate_q:
            summary_aggregates[case][5] += 1
            distinct_sets[case][5].add(gene)
            final_keys.add((network, case, gene))

        if not support:
            first_failed_filter: int | None = 3
            first_failed_reason = "no_conservative_support"
        elif not coverage:
            first_failed_filter = 4
            first_failed_reason = "coverage_below_0_80"
        elif not aggregate_q:
            first_failed_filter = 5
            first_failed_reason = "acat_q_above_0_05_or_not_testable"
        else:
            first_failed_filter = None
            first_failed_reason = "passed_all_filters"
        membership.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "record_type": "gene_network_case_membership",
                "case_order": CASE_META[case]["order"],
                "case_id": case,
                "broad_network": network,
                "current_symbol": gene,
                "conservative_support_pass": "TRUE" if support else "FALSE",
                "coverage_pass": "TRUE" if coverage else "FALSE",
                "aggregate_q_pass": "TRUE" if aggregate_q else "FALSE",
                "first_failed_filter": first_failed_filter,
                "first_failed_reason": first_failed_reason,
                "terminal_candidate_status": row["terminal_candidate_status"],
            }
        )

    require(len(membership) == 49618, "Gene-summary aggregate row count changed")
    require(summary_aggregates == EXPECTED_AGGREGATES, "Summary and funnel aggregate counts differ")
    distinct_counts = {
        case: {stage: len(genes) for stage, genes in stages.items()}
        for case, stages in distinct_sets.items()
    }
    require(distinct_counts == EXPECTED_DISTINCT, "Distinct-gene checkpoints changed")

    candidate_rows = read_tsv(paths["key_driver_candidates.tsv"])
    require_columns(
        candidate_rows,
        ["broad_network", "case_id", "current_symbol", "terminal_candidate_status"],
        "Candidate table",
    )
    candidate_keys = {
        (row["broad_network"], row["case_id"], row["current_symbol"])
        for row in candidate_rows
    }
    require(len(candidate_rows) == 109, "Candidate row count changed")
    require(candidate_keys == final_keys, "Final filter membership differs from candidate table")
    require(
        all(row["terminal_candidate_status"] == "driver_candidate" for row in candidate_rows),
        "Candidate table contains a noncandidate row",
    )
    final_union = set().union(*(distinct_sets[case][5] for case in CASE_ORDER))
    require(len(final_union) == 57, "Final all-case unique-gene union changed")

    plotted_rows: list[dict[str, Any]] = [
        {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "record_type": "native_filter",
            "panel_id": "A",
            "case_order": None,
            "case_id": "ALL",
            "case_label": "Shared by all cases",
            "filter_number": 1,
            "filter_name": "frozen_run_scope",
            "counting_unit": "run_slot",
            "input_n": EXPECTED_FILTER1["input"],
            "pass_n": EXPECTED_FILTER1["pass"],
            "first_removed_n": EXPECTED_FILTER1["fail"],
            "remaining_n": EXPECTED_FILTER1["pass"],
            "conditional_retained_fraction": EXPECTED_FILTER1["pass"] / EXPECTED_FILTER1["input"],
            "distinct_gene_input_n": None,
            "distinct_gene_first_removed_n": None,
            "distinct_gene_remaining_n": None,
            "source_file": "key_driver_filter_funnel.tsv",
            "source_report_type": "native_filter",
            "source_summary_scope": "overall",
            "derivation_rule": "read authoritative overall Filter 1 row",
        }
    ]
    for case in CASE_ORDER:
        meta = CASE_META[case]
        f2 = filter2[case]
        plotted_rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "record_type": "native_filter",
                "panel_id": meta["panel"],
                "case_order": meta["order"],
                "case_id": case,
                "case_label": f"{meta['short']}: {meta['title']}",
                "filter_number": 2,
                "filter_name": "usable_gene_level_result",
                "counting_unit": "gene_included_run_opportunity",
                "input_n": f2["opportunities"],
                "pass_n": f2["usable"],
                "first_removed_n": f2["unavailable"],
                "remaining_n": f2["usable"],
                "conditional_retained_fraction": f2["usable"] / f2["opportunities"],
                "distinct_gene_input_n": None,
                "distinct_gene_first_removed_n": None,
                "distinct_gene_remaining_n": None,
                "source_file": "key_driver_candidate_tests.tsv.gz",
                "source_report_type": "candidate_test_rows",
                "source_summary_scope": "case",
                "derivation_rule": "count usable_test within case; unavailable is absent or invalid",
            }
        )
        plotted_rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "record_type": "aggregate_universe",
                "panel_id": meta["panel"],
                "case_order": meta["order"],
                "case_id": case,
                "case_label": f"{meta['short']}: {meta['title']}",
                "filter_number": "pre_3",
                "filter_name": "eligible_case_aggregate_universe",
                "counting_unit": "gene_broad_network_case_aggregate",
                "input_n": EXPECTED_AGGREGATES[case]["input"],
                "pass_n": EXPECTED_AGGREGATES[case]["input"],
                "first_removed_n": None,
                "remaining_n": EXPECTED_AGGREGATES[case]["input"],
                "conditional_retained_fraction": None,
                "distinct_gene_input_n": EXPECTED_DISTINCT[case]["input"],
                "distinct_gene_first_removed_n": None,
                "distinct_gene_remaining_n": EXPECTED_DISTINCT[case]["input"],
                "source_file": "key_driver_gene_case_summary.tsv.gz",
                "source_report_type": "aggregate_rows",
                "source_summary_scope": "case_any_network",
                "derivation_rule": "distinct symbol counted once per case; aggregate counted once per network and case",
            }
        )
        previous_aggregate = EXPECTED_AGGREGATES[case]["input"]
        previous_distinct = EXPECTED_DISTINCT[case]["input"]
        for filter_number in (3, 4, 5):
            remaining_aggregate = EXPECTED_AGGREGATES[case][filter_number]
            remaining_distinct = EXPECTED_DISTINCT[case][filter_number]
            plotted_rows.append(
                {
                    "schema_version": SCHEMA,
                    "figure_id": FIGURE_ID,
                    "record_type": "sequential_candidate_funnel",
                    "panel_id": meta["panel"],
                    "case_order": meta["order"],
                    "case_id": case,
                    "case_label": f"{meta['short']}: {meta['title']}",
                    "filter_number": filter_number,
                    "filter_name": FILTER_LABELS[filter_number],
                    "counting_unit": "gene_broad_network_case_aggregate",
                    "input_n": previous_aggregate,
                    "pass_n": remaining_aggregate,
                    "first_removed_n": previous_aggregate - remaining_aggregate,
                    "remaining_n": remaining_aggregate,
                    "conditional_retained_fraction": remaining_distinct / previous_distinct,
                    "distinct_gene_input_n": previous_distinct,
                    "distinct_gene_first_removed_n": previous_distinct - remaining_distinct,
                    "distinct_gene_remaining_n": remaining_distinct,
                    "source_file": "key_driver_filter_funnel.tsv|key_driver_gene_case_summary.tsv.gz",
                    "source_report_type": "sequential_candidate_funnel|aggregate_rows",
                    "source_summary_scope": "broad_network_case|case_any_network",
                    "derivation_rule": "aggregate counts summed across networks; distinct gene remains if any network passes",
                }
            )
            previous_aggregate = remaining_aggregate
            previous_distinct = remaining_distinct

    require(len(plotted_rows) == 16, "Unexpected plotted-data row count")

    return {
        "root": root,
        "input_dir": input_dir,
        "paths": paths,
        "status": status[0],
        "filter1": observed_filter1,
        "filter2": filter2,
        "filter2_total": total_filter2,
        "aggregates": summary_aggregates,
        "distinct": distinct_counts,
        "membership": membership,
        "plotted_rows": plotted_rows,
        "final_union_n": len(final_union),
        "source_hashes_verified": len(hashed_input_names),
    }


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: Any,
    edgecolor: str = DARK,
    hatch: str | None = None,
    linewidth: float = 0.75,
    radius: float = 0.015,
    zorder: int = 1,
) -> mpatches.FancyBboxPatch:
    box = mpatches.FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.004,rounding_size={radius}",
        transform=ax.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        hatch=hatch,
        zorder=zorder,
    )
    ax.add_patch(box)
    return box


def arrow(ax: plt.Axes, x1: float, x2: float, y: float = 0.51) -> None:
    ax.annotate(
        "",
        xy=(x2, y),
        xytext=(x1, y),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops={"arrowstyle": "-|>", "lw": 0.7, "color": MID_GRAY},
        zorder=0,
    )


def render_panel_a(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.text(0.0, 1.01, "A", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.text(
        0.035,
        1.01,
        "Shared run scope and the three counting units",
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight="bold",
        va="bottom",
    )

    boxes = [
        ("Filter 1", "Common runs", "648 → 161 kept", "run slots"),
        ("Filter 2", "Usable result", "valid P or P = 1", "gene × run"),
        ("Filter 3", "Support", "≥1 conservative run", "gene × network × case"),
        ("Filter 4", "Coverage", "≥80% usable", "gene × network × case"),
        ("Filter 5", "Combined evidence", "ACAT q ≤ 0.05", "gene × network × case"),
    ]
    xs = [0.015, 0.205, 0.395, 0.585, 0.775]
    width = 0.16
    for index, ((number, title, rule, unit), x) in enumerate(zip(boxes, xs)):
        face = lighten(SHARED_BLUE, 0.78) if index < 2 else "#F5F5F5"
        rounded_box(ax, x, 0.23, width, 0.60, facecolor=face, edgecolor="#4D4D4D")
        ax.text(x + 0.012, 0.74, number, transform=ax.transAxes, fontsize=7, fontweight="bold", va="top")
        ax.text(x + 0.012, 0.57, title, transform=ax.transAxes, fontsize=7, fontweight="bold", va="top")
        ax.text(x + 0.012, 0.43, rule, transform=ax.transAxes, fontsize=7, va="top")
        ax.text(x + 0.012, 0.27, unit, transform=ax.transAxes, fontsize=7, color="#555555", va="bottom")
        if index < len(boxes) - 1:
            arrow(ax, x + width + 0.005, xs[index + 1] - 0.005, y=0.55)

    boundary_x = 0.38
    ax.plot([boundary_x, boundary_x], [0.08, 0.91], transform=ax.transAxes, color="#666666", lw=0.75, ls="--")
    ax.text(
        boundary_x,
        0.06,
        "aggregation boundary",
        transform=ax.transAxes,
        fontsize=7,
        color="#555555",
        ha="center",
        va="top",
    )


def format_count(value: int) -> str:
    return f"{value:,}"


def render_case_panel(ax: plt.Axes, case: str, bundle: Mapping[str, Any]) -> None:
    ax.set_axis_off()
    meta = CASE_META[case]
    color = str(meta["color"])
    ax.text(0.0, 1.01, meta["panel"], transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.plot([0.034, 0.047], [1.045, 1.045], transform=ax.transAxes, color=color, lw=4, solid_capstyle="butt", clip_on=False)
    ax.text(0.052, 1.01, f"{meta['short']} — {meta['title']}", transform=ax.transAxes, fontsize=8.3, fontweight="bold", va="bottom")
    ax.text(0.99, 1.01, f"({meta['subtitle']})", transform=ax.transAxes, fontsize=7, color="#555555", ha="right", va="bottom")

    filter2 = bundle["filter2"][case]
    opportunities = filter2["opportunities"]
    usable = filter2["usable"]
    unavailable = filter2["unavailable"]
    usable_fraction = usable / opportunities

    bar_x, bar_y, bar_width, bar_height = 0.018, 0.73, 0.964, 0.105
    ax.add_patch(
        mpatches.Rectangle(
            (bar_x, bar_y),
            bar_width * usable_fraction,
            bar_height,
            transform=ax.transAxes,
            facecolor=lighten(color, 0.25),
            edgecolor=DARK,
            linewidth=0.65,
        )
    )
    if unavailable:
        ax.add_patch(
            mpatches.Rectangle(
                (bar_x + bar_width * usable_fraction, bar_y),
                bar_width * (1 - usable_fraction),
                bar_height,
                transform=ax.transAxes,
                facecolor=LIGHT_REMOVED,
                edgecolor=DARK,
                linewidth=0.65,
                hatch="////",
            )
        )
    ax.add_patch(
        mpatches.Rectangle(
            (bar_x, bar_y),
            bar_width,
            bar_height,
            transform=ax.transAxes,
            facecolor="none",
            edgecolor=DARK,
            linewidth=0.7,
        )
    )
    ax.text(
        bar_x + 0.01,
        bar_y + bar_height / 2,
        f"Filter 2 • {format_count(usable)} / {format_count(opportunities)} usable gene × run results "
        f"({100 * usable_fraction:.1f}%) • {format_count(unavailable)} unavailable",
        transform=ax.transAxes,
        fontsize=7,
        fontweight="bold",
        va="center",
    )
    stage_x = [0.15, 0.365, 0.58, 0.795]
    stage_width = 0.19
    headers = [
        "Entering Filter 3",
        "After Filter 3\n≥1 conservative run",
        "After Filter 4\n≥80% coverage",
        "After Filter 5\nACAT q ≤ 0.05",
    ]
    genes = [
        bundle["distinct"][case]["input"],
        bundle["distinct"][case][3],
        bundle["distinct"][case][4],
        bundle["distinct"][case][5],
    ]
    aggregates = [
        bundle["aggregates"][case]["input"],
        bundle["aggregates"][case][3],
        bundle["aggregates"][case][4],
        bundle["aggregates"][case][5],
    ]

    ax.text(0.015, 0.48, "Genes remaining", transform=ax.transAxes, fontsize=7, fontweight="bold", va="center")
    ax.text(0.015, 0.33, "Network results", transform=ax.transAxes, fontsize=7, color="#4A4A4A", va="center")
    ax.text(0.015, 0.18, "First removed", transform=ax.transAxes, fontsize=7, color="#4A4A4A", va="center")
    ax.text(0.015, 0.035, "Stage retention", transform=ax.transAxes, fontsize=7, color="#4A4A4A", va="center")

    for index, x in enumerate(stage_x):
        ax.text(
            x + stage_width / 2,
            0.62,
            headers[index],
            transform=ax.transAxes,
            fontsize=7,
            fontweight="bold",
            ha="center",
            va="center",
            linespacing=1.1,
        )
        rounded_box(
            ax,
            x,
            0.39,
            stage_width,
            0.17,
            facecolor=lighten(color, 0.82 if index == 0 else 0.68),
            edgecolor=color,
            linewidth=0.9,
            radius=0.012,
        )
        ax.text(
            x + stage_width / 2,
            0.48,
            f"{format_count(genes[index])} genes",
            transform=ax.transAxes,
            fontsize=7.1,
            fontweight="bold",
            ha="center",
            va="center",
            color=DARK,
        )
        ax.text(
            x + stage_width / 2,
            0.33,
            f"{format_count(aggregates[index])} network results",
            transform=ax.transAxes,
            fontsize=7,
            ha="center",
            va="center",
            color="#4A4A4A",
        )

        if index == 0:
            ax.text(
                x + stage_width / 2,
                0.18,
                "—",
                transform=ax.transAxes,
                fontsize=7,
                ha="center",
                va="center",
                color="#555555",
            )
            ax.text(
                x + stage_width / 2,
                0.035,
                "—",
                transform=ax.transAxes,
                fontsize=7,
                ha="center",
                va="center",
                color="#555555",
            )
        else:
            removed_genes = genes[index - 1] - genes[index]
            removed_aggregates = aggregates[index - 1] - aggregates[index]
            retained_percent = 100 * genes[index] / genes[index - 1]
            ax.text(
                x + stage_width / 2,
                0.20,
                f"{format_count(removed_genes)} genes\n{format_count(removed_aggregates)} results",
                transform=ax.transAxes,
                fontsize=7,
                ha="center",
                va="center",
                color="#4A4A4A",
                bbox={"boxstyle": "round,pad=0.16", "facecolor": LIGHT_REMOVED, "edgecolor": "#707070", "hatch": "////", "linewidth": 0.55},
            )
            ax.text(
                x + stage_width / 2,
                0.035,
                f"{retained_percent:.1f}%",
                transform=ax.transAxes,
                fontsize=7,
                fontweight="bold",
                ha="center",
                va="center",
            )

        if index < 3:
            arrow(ax, x + stage_width + 0.004, stage_x[index + 1] - 0.004, y=0.475)


def render_figure(bundle: Mapping[str, Any]) -> plt.Figure:
    configure_style()
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor="white")
    fig.text(
        0.025,
        0.975,
        "Phase 18 key-driver attrition across five filters",
        fontsize=11,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.025,
        0.944,
        "Exact validated counts • three cases remain separate • native counting unit shown at every stage",
        fontsize=7,
        color="#4A4A4A",
        ha="left",
        va="top",
    )
    grid = fig.add_gridspec(
        4,
        1,
        left=0.025,
        right=0.99,
        bottom=0.09,
        top=0.90,
        hspace=0.18,
        height_ratios=[0.9, 1.0, 1.0, 1.0],
    )
    axes = [fig.add_subplot(grid[index, 0]) for index in range(4)]
    render_panel_a(axes[0])
    for ax, case in zip(axes[1:], CASE_ORDER):
        render_case_panel(ax, case, bundle)
    fig.text(
        0.025,
        0.018,
        "Large type: distinct genes retained in ≥1 broad network. Smaller type: gene–network–case results.\n"
        "Filter 2 counts gene × run opportunities. Counts are exact; no formal case comparison was performed.",
        fontsize=7,
        color="#404040",
        ha="left",
        va="bottom",
    )
    return fig


def render_triplet(fig: plt.Figure, directory: Path, dpi: int) -> list[Path]:
    paths: list[Path] = []
    for extension in ("svg", "pdf", "png"):
        final = directory / f"{FIGURE_ID}.{extension}"
        temporary = directory / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Creator": "Phase 18 filter-attrition renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {"Creator": "Phase 18 filter-attrition renderer", "Date": None}
        else:
            metadata = {"Software": "Phase 18 filter-attrition renderer"}
        fig.savefig(
            temporary,
            format=extension,
            dpi=dpi if extension == "png" else None,
            facecolor="white",
            metadata=metadata,
        )
        require(temporary.exists() and temporary.stat().st_size > 0, f"Empty image: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths


CAPTION = """# Phase 18 filter-attrition figure caption

**Phase 18 attrition across five key-driver filters.** **A,** The shared run-scope gate retained 161 of 648 primary sex/APOE-direction run slots that were validated and contained at least 10 effective query genes. The schematic marks the change from run slots, to gene × run results, to gene × broad-network × case results. **B–D,** Attrition is shown separately for Case 1 (core MitoCarta gene in the run query), Case 2 (core MitoCarta gene not in the run query), and Case 3 (gene outside the 1,136-gene core MitoCarta inventory). Filter 2 counts usable and unavailable gene × run results; valid zero-overlap results with P = 1 are usable. After aggregation, large labels give distinct symbols remaining in at least one broad network, and smaller labels give gene × broad-network × case results. Filters 3–5 require at least one conservative supporting run, at least 80% usable-run coverage, and ACAT q ≤ 0.05, respectively. Case 1 removes the driver's guaranteed self-overlap before enrichment is evaluated. Counts are exact and descriptive; no formal comparison among cases was performed.
"""

METHODS = """# Phase 18 filter-attrition figure methods

The renderer read the validated Phase 18 production status, artifact manifest, case manifest, filter funnel, complete candidate-test matrix, gene-case summary, and final candidate table. Recorded Phase 18 hashes and byte counts were verified before plotting. It did not rerun KDA, alter self-overlap corrections, recompute coverage, combine P values, adjust q values, or select candidates.

Filter 1 uses the authoritative overall native-filter run-slot row. Filter 2 was summarized by case from all 1,463,150 gene × included-run opportunities; explicit tests and valid explicit or implicit zero-overlap results count as usable, while absent-background and invalid results count as unavailable. Filters 3–5 use the authoritative sequential gene × broad-network × case funnel. Distinct-gene counts were derived within each case by retaining a symbol when at least one broad-network aggregate remained after the relevant sequential gate. Distinct counts were never summed across networks, and all-case unique genes were calculated by set union.

Counts are deterministic properties of the validated bundle, so uncertainty intervals and hypothesis tests are not applicable. Okabe–Ito case colors are supplemented by panel labels, exact text, outlines, and hatched removal boxes. SVG and PDF are vector outputs; the PNG is exported at the recorded resolution.
"""


def image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    checks: list[dict[str, Any]] = []
    checks.append(
        check_record(
            "vector_and_raster_outputs",
            set(lookup) == {".svg", ".pdf", ".png"},
            "|".join(sorted(lookup)),
            ".pdf|.png|.svg",
        )
    )
    checks.append(
        check_record(
            "image_outputs_nonempty",
            all(path.stat().st_size > 0 for path in image_paths),
            sum(path.stat().st_size > 0 for path in image_paths),
            3,
        )
    )
    svg_text = lookup[".svg"].read_text(encoding="utf-8")
    checks.append(check_record("svg_is_vector", "<svg" in svg_text, "<svg present", "<svg present"))
    checks.append(check_record("svg_text_preserved", "<text" in svg_text, "<text present", "<text present"))
    with lookup[".pdf"].open("rb") as handle:
        pdf_header = handle.read(5)
    checks.append(check_record("pdf_signature", pdf_header == b"%PDF-", pdf_header.decode("latin1"), "%PDF-"))
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        png_dpi = image.info.get("dpi", (math.nan, math.nan))
    expected_width = round(FIGURE_WIDTH_IN * dpi)
    expected_height = round(FIGURE_HEIGHT_IN * dpi)
    checks.append(check_record("png_width", width == expected_width, width, expected_width))
    checks.append(check_record("png_height", height == expected_height, height, expected_height))
    dpi_ok = all(math.isfinite(value) and abs(value - dpi) <= 1 for value in png_dpi)
    checks.append(check_record("png_resolution", dpi_ok, f"{png_dpi[0]:.2f}|{png_dpi[1]:.2f}", f"{dpi}|{dpi}"))
    return checks


def build_checks(
    bundle: Mapping[str, Any],
    image_paths: Sequence[Path],
    png_dpi: int,
    visual_review_status: str,
) -> list[dict[str, Any]]:
    filter2 = bundle["filter2_total"]
    aggregate_totals = {
        stage: sum(bundle["aggregates"][case][stage] for case in CASE_ORDER)
        for stage in ("input", 3, 4, 5)
    }
    final_union = bundle["final_union_n"]
    checks = [
        check_record("production_status", bundle["status"]["validation_status"] == "validated_complete", bundle["status"]["validation_status"], "validated_complete"),
        check_record("execution_stage_recorded", bool(bundle["status"]["execution_stage"]), bundle["status"]["execution_stage"], "nonempty"),
        check_record("three_ordered_cases", list(bundle["distinct"]) == CASE_ORDER, "|".join(bundle["distinct"]), "|".join(CASE_ORDER)),
        check_record("source_artifact_hashes", bundle["source_hashes_verified"] == 5, bundle["source_hashes_verified"], 5),
        check_record("filter1_additive", bundle["filter1"]["input"] == bundle["filter1"]["pass"] + bundle["filter1"]["fail"], f"{bundle['filter1']['input']}={bundle['filter1']['pass']}+{bundle['filter1']['fail']}", "648=161+487"),
        check_record("filter2_opportunities", filter2["opportunities"] == 1463150, filter2["opportunities"], 1463150),
        check_record("filter2_usable", filter2["usable"] == 1299782, filter2["usable"], 1299782),
        check_record("filter2_unavailable", filter2["unavailable"] == 163368, filter2["unavailable"], 163368),
        check_record("filter2_invalid", filter2["invalid"] == 0, filter2["invalid"], 0),
        check_record("aggregate_input", aggregate_totals["input"] == 49618, aggregate_totals["input"], 49618),
        check_record("filter3_aggregate_survivors", aggregate_totals[3] == 292, aggregate_totals[3], 292),
        check_record("filter4_aggregate_survivors", aggregate_totals[4] == 283, aggregate_totals[4], 283),
        check_record("filter5_candidate_aggregates", aggregate_totals[5] == 109, aggregate_totals[5], 109),
        check_record("case1_final_distinct_genes", bundle["distinct"][CASE_ORDER[0]][5] == 27, bundle["distinct"][CASE_ORDER[0]][5], 27),
        check_record("case2_final_distinct_genes", bundle["distinct"][CASE_ORDER[1]][5] == 18, bundle["distinct"][CASE_ORDER[1]][5], 18),
        check_record("case3_final_distinct_genes", bundle["distinct"][CASE_ORDER[2]][5] == 30, bundle["distinct"][CASE_ORDER[2]][5], 30),
        check_record("all_case_unique_gene_union", final_union == 57, final_union, 57),
        check_record("membership_rows", len(bundle["membership"]) == 49618, len(bundle["membership"]), 49618),
        check_record("plotted_data_rows", len(bundle["plotted_rows"]) == 16, len(bundle["plotted_rows"]), 16),
        check_record("colorblind_safe_palette", True, "Okabe-Ito blue|green|purple", "colorblind-safe categorical palette"),
        check_record("grayscale_redundancy", True, "labels|outlines|hatching", "non-color encodings present"),
        check_record("minimum_text_size", True, "7 pt", ">=7 pt", "All rendered text is at least 7 pt at the 183 mm final width."),
        check_record("no_uncertainty_bars", True, "not applicable to exact counts", "not applicable"),
        check_record("no_significance_stars", True, "none", "none"),
        check_record("visual_review_complete", visual_review_status == "complete", visual_review_status, "complete", "Manual review of clipping, grayscale redundancy, and label readability.", blocking=False),
    ]
    checks.extend(image_checks(image_paths, png_dpi))
    return checks


def build_source_rows(
    root: Path,
    final_output_dir: Path,
    staging: Path,
    source_paths: Sequence[tuple[str, Path]],
    output_paths: Sequence[Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record_type, path in source_paths:
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "record_type": record_type,
                "artifact_id": path.name,
                "path": display_path(path, root),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    for path in output_paths:
        logical = final_output_dir / path.relative_to(staging)
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "record_type": "output",
                "artifact_id": path.name,
                "path": display_path(logical, root),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def validate_output(
    root: Path,
    directory: Path,
    expected_visual_status: str | None = None,
) -> None:
    require(directory.exists() and directory.is_dir(), f"Missing output directory: {directory}")
    actual = sorted(path.name for path in directory.iterdir() if path.is_file())
    require(actual == sorted(DECLARED_OUTPUTS), f"Output declaration mismatch: {actual}")

    status = read_tsv(directory / f"{FIGURE_ID}_status.tsv")
    require(len(status) == 1, "Figure status must contain one row")
    visual_status = status[0]["visual_review_status"]
    if expected_visual_status is not None:
        require(visual_status == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual_status == "complete" else "awaiting_visual_review"
    require(status[0]["validation_status"] == expected_validation, "Unexpected figure validation status")

    checks = read_tsv(directory / f"{FIGURE_ID}_checks.tsv")
    require(bool(checks), "Figure checks are empty")
    blocking_failures = [row["check_id"] for row in checks if truth(row["blocking"]) and not truth(row["passed"])]
    require(not blocking_failures, f"Blocking figure checks failed: {', '.join(blocking_failures)}")
    if visual_status == "complete":
        require(all(truth(row["passed"]) for row in checks), "A completed figure check is not passed")

    source_rows = read_tsv(directory / f"{FIGURE_ID}_sources.tsv")
    require(bool(source_rows), "Figure source manifest is empty")
    for row in source_rows:
        if row["record_type"] == "output":
            path = directory / row["artifact_id"]
        else:
            candidate = Path(row["path"])
            path = candidate if candidate.is_absolute() else root / candidate
        require(path.exists(), f"Recorded artifact is missing: {path}")
        require(integer(row["bytes"]) == path.stat().st_size, f"Recorded bytes changed: {path}")
        require(row["sha256"] == sha256_file(path), f"Recorded hash changed: {path}")

    plot_rows = read_tsv(directory / f"{FIGURE_ID}_plot_data.tsv")
    require(len(plot_rows) == 16, "Plotted-data row count changed")
    membership_rows = sum(1 for _ in tsv_rows(directory / f"{FIGURE_ID}_membership.tsv.gz"))
    require(membership_rows == 49618, "Membership row count changed")
    with (directory / f"{FIGURE_ID}_membership.tsv.gz").open("rb") as handle:
        require(handle.read(2) == b"\x1f\x8b", "Membership table is not gzip-compressed")

    image_check_rows = image_checks(
        [directory / f"{FIGURE_ID}.{extension}" for extension in ("svg", "pdf", "png")],
        integer(status[0]["png_dpi"]),
    )
    failures = [row["check_id"] for row in image_check_rows if not truth(row["passed"])]
    require(not failures, f"Output image checks failed: {', '.join(failures)}")
    print(f"Phase 18 filter-attrition output validation passed: {directory}")


def publish(
    root: Path,
    input_dir: Path,
    output_dir: Path,
    png_dpi: int,
    visual_review_status: str,
) -> None:
    require(not output_dir.exists(), f"Refusing to overwrite existing output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".phase18_filter_attrition.staging.", dir=output_dir.parent)
    )
    try:
        bundle = load_bundle(root, input_dir)
        figure = render_figure(bundle)
        image_paths = render_triplet(figure, staging, png_dpi)

        plotted_path = staging / f"{FIGURE_ID}_plot_data.tsv"
        membership_path = staging / f"{FIGURE_ID}_membership.tsv.gz"
        caption_path = staging / f"{FIGURE_ID}_caption.md"
        methods_path = staging / f"{FIGURE_ID}_methods.md"
        write_tsv(plotted_path, bundle["plotted_rows"])
        write_tsv_gz(membership_path, bundle["membership"])
        write_text(caption_path, CAPTION)
        write_text(methods_path, METHODS)

        renderer_path = Path(__file__).resolve()
        plan_path = root / "docs/figures/analysis/phase_18_key_driver_selection/phase18_filter_attrition_figure_plan.md"
        source_paths = [
            ("renderer", renderer_path),
            ("figure_plan", plan_path),
            *[("production_input", bundle["paths"][name]) for name in REQUIRED_INPUTS],
        ]
        primary_outputs = [
            *image_paths,
            plotted_path,
            membership_path,
            caption_path,
            methods_path,
        ]
        source_rows = build_source_rows(root, output_dir, staging, source_paths, primary_outputs)
        sources_path = staging / f"{FIGURE_ID}_sources.tsv"
        write_tsv(sources_path, source_rows)

        checks = build_checks(bundle, image_paths, png_dpi, visual_review_status)
        checks_path = staging / f"{FIGURE_ID}_checks.tsv"
        write_tsv(checks_path, checks)
        blocking_failed = sum(
            truth(row["blocking"]) and not truth(row["passed"]) for row in checks
        )
        nonblocking_pending = sum(
            not truth(row["blocking"]) and not truth(row["passed"]) for row in checks
        )
        require(blocking_failed == 0, "A blocking figure-package check failed")
        validation_status = (
            "validated_complete"
            if visual_review_status == "complete" and nonblocking_pending == 0
            else "awaiting_visual_review"
        )
        status_row = {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "execution_stage": bundle["status"]["execution_stage"],
            "input_validation_status": bundle["status"]["validation_status"],
            "input_status_sha256": sha256_file(bundle["paths"]["key_driver_status.tsv"]),
            "renderer_sha256": sha256_file(renderer_path),
            "figure_width_inches": FIGURE_WIDTH_IN,
            "figure_height_inches": FIGURE_HEIGHT_IN,
            "png_dpi": png_dpi,
            "plotted_rows": len(bundle["plotted_rows"]),
            "membership_rows": len(bundle["membership"]),
            "image_artifacts": len(image_paths),
            "declared_outputs": len(DECLARED_OUTPUTS),
            "checks": len(checks),
            "failed_blocking_checks": blocking_failed,
            "pending_nonblocking_checks": nonblocking_pending,
            "visual_review_status": visual_review_status,
            "validation_status": validation_status,
        }
        status_path = staging / f"{FIGURE_ID}_status.tsv"
        write_tsv(status_path, [status_row])

        validate_output(root, staging, visual_review_status)
        staging.replace(output_dir)
        print(f"Phase 18 filter-attrition figure published: {output_dir}")
        print("Distinct genes after Filter 5: Case 1 = 27; Case 2 = 18; Case 3 = 30")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd().resolve()
    if args.validate_output:
        validate_output(root, (root / args.validate_output).resolve())
        return 0
    input_dir = (root / args.input_dir).resolve()
    output_dir = (root / args.output_dir).resolve()
    publish(
        root,
        input_dir,
        output_dir,
        args.png_dpi,
        args.visual_review_status,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
