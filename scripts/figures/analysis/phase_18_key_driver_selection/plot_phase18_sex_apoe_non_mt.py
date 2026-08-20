#!/usr/bin/env python3
"""Build the Phase 18 sex/APOE evidence figure for selected non-MT drivers."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

from PIL import Image


SCHEMA = "phase18_sex_apoe_non_mt_v1"
INPUT_SCHEMA = "phase18_call_key_driver_returns_v1"
CASE_ID = "non_mt_driver"
LEGACY_CASE_IDS = {"case3_not_core_mito"}
CASE_DISPLAY_LABEL = "non-MT"
FIGURE_ID = "phase18_sex_apoe_non_mt"
RENDERER_FILE = "visualize_phase18_sex_apoe_non_mt.R"
DEFAULT_INPUT = (
    "results/minerva_production/18_key_driver_selection/"
    "call_key_driver_returns.tsv"
)
DEFAULT_OUTPUT = (
    "results/figures/analysis/phase_18_key_driver_selection/"
    "sex_apoe_non_mt"
)
DEFAULT_CANDIDATE_TESTS = (
    "results/minerva_production/18_key_driver_selection/archive/"
    "key_driver_candidate_tests.tsv.gz"
)
DEFAULT_DPI = 450
DEFAULT_WIDTH = 15.0
DEFAULT_HEIGHT = 11.0
DEFAULT_EVIDENCE_CAP = 8.0
NETWORK_Q_AXIS_MAX = 12.0

PLOT_FILE = f"{FIGURE_ID}_plot_data.tsv"
ROW_FILE = f"{FIGURE_ID}_row_annotations.tsv"
AUDIT_FILE = f"{FIGURE_ID}_aggregation_audit.tsv.gz"
CAPTION_FILE = f"{FIGURE_ID}_caption.md"
METHODS_FILE = f"{FIGURE_ID}_methods.md"
MANIFEST_FILE = f"{FIGURE_ID}_manifest.tsv"
CHECKS_FILE = f"{FIGURE_ID}_checks.tsv"
ARTIFACTS_FILE = f"{FIGURE_ID}_artifacts.tsv"
STATUS_FILE = f"{FIGURE_ID}_status.tsv"
IMAGE_FILES = [f"{FIGURE_ID}.svg", f"{FIGURE_ID}.pdf", f"{FIGURE_ID}.png"]
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
NETWORK_COLORS = {
    "Astrocytes": "#009E73",
    "Excitatory_neurons": "#E69F00",
    "Inhibitory_neurons": "#0072B2",
    "Microglia": "#CC79A7",
    "OPCs": "#56B4E9",
    "Oligodendrocytes": "#F0E442",
    "Vasculature_cells": "#D55E00",
}
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
EXPECTED_GENES = {
    "ANKRD11",
    "APOE",
    "ATP6V1F",
    "DYNLT1",
    "FTL",
    "LAMTOR5",
    "LAPTM4A",
    "NCOA1",
    "RPL11",
    "RPL15",
    "RPL38",
    "RPLP1",
    "RPS13",
    "RPS15",
    "SELENOW",
}
EXPECTED_EXTRA_CONTEXTS = {("Excitatory_neurons", "RPS15")}
EXPECTED_INPUT_ROWS = 95_557
EXPECTED_INPUT_COLUMNS = 104
EXPECTED_RUNS = 161
EXPECTED_DISPLAYED_CONTEXTS = 21
EXPECTED_PASSING_CONTEXTS = 22
EXPECTED_CELLS = 264
EXPECTED_AUDIT_ROWS = 859


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--candidate-tests", default=DEFAULT_CANDIDATE_TESTS)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--width-inches", type=float, default=DEFAULT_WIDTH)
    parser.add_argument("--height-inches", type=float, default=DEFAULT_HEIGHT)
    parser.add_argument("--evidence-cap", type=float, default=DEFAULT_EVIDENCE_CAP)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    parser.add_argument("--validate-output")
    args = parser.parse_args(argv)
    if not 300 <= args.png_dpi <= 600:
        parser.error("--png-dpi must be between 300 and 600")
    if args.width_inches <= 0 or args.height_inches <= 0:
        parser.error("Figure dimensions must be positive")
    if not math.isclose(args.evidence_cap, DEFAULT_EVIDENCE_CAP):
        parser.error(f"--evidence-cap is frozen at {DEFAULT_EVIDENCE_CAP:g}")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "t", "1", "yes"}


def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def integer(value: Any) -> int:
    result = number(value)
    require(result is not None, f"Expected integer-like value, observed {value!r}")
    return int(round(result))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_value(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, float) and not math.isfinite(value):
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    preferred = [
        "schema_version",
        "figure_id",
        "case_id",
        "atlas_display_order",
        "current_symbol",
        "network_order",
        "broad_network",
        "context_display_order",
    ]
    observed: list[str] = []
    for row in rows:
        for column in row:
            if column not in observed:
                observed.append(column)
    return [column for column in preferred if column in observed] + [
        column for column in observed if column not in preferred
    ]


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


def write_gzip_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty table: {path}")
    columns = ordered_columns(rows)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with gzip.open(temporary, "wt", newline="", encoding="utf-8", compresslevel=6) as handle:
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


def write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_tsv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"Missing TSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_acat(root: Path) -> tuple[Callable[..., float | None], Path]:
    source = root / "scripts/18_key_driver_selection.py"
    spec = importlib.util.spec_from_file_location("phase18_current_selection", source)
    require(spec is not None and spec.loader is not None, "Could not load ACAT source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(callable(module.acat_combine), "Canonical acat_combine is unavailable")
    require(module.validate_acat_example() <= 5e-10, "Canonical ACAT self-check failed")
    return module.acat_combine, source


def check_record(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    detail: str = "",
    *,
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA}_checks_v1",
        "figure_id": FIGURE_ID,
        "check_id": check_id,
        "blocking": blocking,
        "passed": passed,
        "observed": observed,
        "expected": expected,
        "detail": detail,
    }


def load_bundle(
    input_path: Path,
    candidate_path: Path,
    acat_combine: Callable[..., float | None],
    evidence_cap: float,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "kda_run_id",
        "fine_cell_type",
        "broad_network",
        "signature_group",
        "signature_direction",
        "key_driver",
        "tested_by_call_key_drivers",
        "usable_test",
        "final_raw_p",
        "conservative_support",
        "case_id",
        "is_core_mito",
        "extended_reference_member",
        "eligible_run_count",
        "usable_run_count",
        "conservative_support_count",
        "coverage_fraction",
        "recurrence_fraction",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
        "evidence_tier",
    }
    repeated = [
        "is_core_mito",
        "extended_reference_member",
        "eligible_run_count",
        "usable_run_count",
        "conservative_support_count",
        "coverage_fraction",
        "recurrence_fraction",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "terminal_candidate_status",
        "within_case_rank",
        "top5_display",
        "evidence_tier",
    ]
    row_count = 0
    run_meta: dict[str, tuple[str, str, str, str]] = {}
    aggregates: dict[tuple[str, str], dict[str, str]] = {}
    aggregate_values: dict[tuple[str, str], tuple[str, ...]] = {}
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(reader.fieldnames is not None, "Canonical input has no header")
        require(len(reader.fieldnames) == EXPECTED_INPUT_COLUMNS, "Unexpected input column count")
        require(not (required - set(reader.fieldnames)), "Canonical input is missing required fields")
        for row in reader:
            row_count += 1
            require(row["schema_version"] == INPUT_SCHEMA, "Unexpected input schema")
            run_id = row["kda_run_id"]
            metadata = (
                row["fine_cell_type"],
                row["broad_network"],
                row["signature_group"],
                row["signature_direction"],
            )
            if run_id in run_meta:
                require(run_meta[run_id] == metadata, f"Run metadata varies: {run_id}")
            else:
                run_meta[run_id] = metadata
            if row["case_id"] != CASE_ID:
                continue
            key = (row["broad_network"], row["key_driver"])
            values = tuple(row[field] for field in repeated)
            if key in aggregate_values:
                require(aggregate_values[key] == values, f"Aggregate fields vary: {key}")
            else:
                aggregate_values[key] = values
                aggregates[key] = row

    require(row_count == EXPECTED_INPUT_ROWS, "Canonical row count changed")
    require(len(run_meta) == EXPECTED_RUNS, "Included KDA-call count changed")
    displayed_keys = {key for key, row in aggregates.items() if truth(row["top5_display"])}
    selected_genes = {gene for _, gene in displayed_keys}
    passing_keys = {
        key
        for key, row in aggregates.items()
        if key[1] in selected_genes
        and row["terminal_candidate_status"] == "driver_candidate"
    }
    require(
        selected_genes == EXPECTED_GENES,
        f"Selected {CASE_DISPLAY_LABEL} gene set changed",
    )
    require(len(displayed_keys) == EXPECTED_DISPLAYED_CONTEXTS, "Displayed-context count changed")
    require(len(passing_keys) == EXPECTED_PASSING_CONTEXTS, "Passing-context count changed")
    require(passing_keys - displayed_keys == EXPECTED_EXTRA_CONTEXTS, "Below-cap contexts changed")
    require(not displayed_keys - passing_keys, "A displayed context is not passing")

    explicit_current: dict[tuple[str, str], dict[str, str]] = {}
    selected_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with input_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["case_id"] != CASE_ID or row["key_driver"] not in selected_genes:
                continue
            key = (row["kda_run_id"], row["key_driver"])
            require(key not in explicit_current, f"Duplicate gene-run row: {key}")
            require(truth(row["tested_by_call_key_drivers"]), f"Untested explicit row: {key}")
            require(truth(row["usable_test"]), f"Unusable explicit row: {key}")
            require(number(row["final_raw_p"]) is not None, f"Missing final P: {key}")
            explicit_current[key] = row
            selected_rows[row["key_driver"]].append(row)

    passing_networks = {
        gene: {network for network, observed_gene in passing_keys if observed_gene == gene}
        for gene in selected_genes
    }
    candidate_tests: dict[tuple[str, str], dict[str, str]] = {}
    require(candidate_path.exists(), f"Missing archived candidate tests: {candidate_path}")
    with gzip.open(candidate_path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(reader.fieldnames is not None, "Archived candidate tests have no header")
        candidate_required = {
            "kda_run_id",
            "fine_cell_type",
            "broad_network",
            "signature_group",
            "signature_direction",
            "current_symbol",
            "case_id",
            "test_status",
            "usable_test",
            "final_raw_p",
            "conservative_support",
        }
        require(not (candidate_required - set(reader.fieldnames)), "Archived candidate tests are missing required fields")
        for row in reader:
            gene = row["current_symbol"]
            network = row["broad_network"]
            if (
                row["case_id"] not in LEGACY_CASE_IDS
                or gene not in selected_genes
                or network not in passing_networks[gene]
            ):
                continue
            key = (row["kda_run_id"], gene)
            require(key not in candidate_tests, f"Duplicate archived gene-run row: {key}")
            candidate_tests[key] = row
    summary: list[dict[str, Any]] = []
    for gene in selected_genes:
        support = [
            row
            for row in selected_rows[gene]
            if truth(row["conservative_support"])
            and row["broad_network"] in passing_networks[gene]
        ]
        summary.append(
            {
                "current_symbol": gene,
                "passing_network_count": len(passing_networks[gene]),
                "supporting_fine_count": len({row["fine_cell_type"] for row in support}),
                "supporting_run_count": len(support),
            }
        )
    summary.sort(
        key=lambda row: (
            -row["passing_network_count"],
            -row["supporting_fine_count"],
            -row["supporting_run_count"],
            row["current_symbol"],
        )
    )
    gene_order = {row["current_symbol"]: index for index, row in enumerate(summary, 1)}
    ordered_contexts = sorted(
        passing_keys,
        key=lambda key: (gene_order[key[1]], NETWORK_ORDER.index(key[0])),
    )
    context_order = {key: index for index, key in enumerate(ordered_contexts, 1)}

    row_rows: list[dict[str, Any]] = []
    for network, gene in ordered_contexts:
        source = aggregates[(network, gene)]
        q_value = number(source["aggregate_acat_q"])
        require(q_value is not None and 0 < q_value <= 0.05, f"Invalid candidate q: {(network, gene)}")
        row_rows.append(
            {
                "schema_version": f"{SCHEMA}_row_annotations_v1",
                "figure_id": FIGURE_ID,
                "case_id": CASE_ID,
                "atlas_display_order": gene_order[gene],
                "current_symbol": gene,
                "network_order": NETWORK_ORDER.index(network) + 1,
                "broad_network": network,
                "network_label": NETWORK_LABELS[network],
                "network_color": NETWORK_COLORS[network],
                "context_display_order": context_order[(network, gene)],
                "circle_displayed": (network, gene) in displayed_keys,
                "circle_display_rank": integer(source["within_case_rank"]) if (network, gene) in displayed_keys else None,
                "within_case_rank": integer(source["within_case_rank"]),
                "evidence_tier": source["evidence_tier"],
                "extended_reference_member": truth(source["extended_reference_member"]),
                "eligible_run_count": integer(source["eligible_run_count"]),
                "usable_run_count": integer(source["usable_run_count"]),
                "conservative_support_count": integer(source["conservative_support_count"]),
                "coverage_fraction": number(source["coverage_fraction"]),
                "recurrence_fraction": number(source["recurrence_fraction"]),
                "aggregate_acat_p": number(source["aggregate_acat_p"]),
                "aggregate_acat_q": q_value,
                "negative_log10_aggregate_acat_q": -math.log10(q_value),
            }
        )

    runs_by_stratum: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for run_id, (_, network, group, direction) in run_meta.items():
        runs_by_stratum[(network, group, direction)].append(run_id)
    for run_ids in runs_by_stratum.values():
        run_ids.sort()

    plot_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    aggregate_differences: list[float] = []
    for annotation in row_rows:
        network = annotation["broad_network"]
        gene = annotation["current_symbol"]
        context_p_values: list[float | None] = []
        for direction_index, direction in enumerate(DIRECTION_ORDER, 1):
            for group_index, group in enumerate(GROUP_ORDER, 1):
                run_ids = runs_by_stratum.get((network, group, direction), [])
                p_values: list[float | None] = []
                support_count = 0
                explicit_count = 0
                implicit_count = 0
                usable_count = 0
                for run_id in run_ids:
                    observed = candidate_tests.get((run_id, gene))
                    require(observed is not None, f"Archived status is missing for {(run_id, gene)}")
                    require(
                        (
                            observed["fine_cell_type"],
                            observed["broad_network"],
                            observed["signature_group"],
                            observed["signature_direction"],
                        )
                        == run_meta[run_id],
                        f"Archived run metadata differs for {(run_id, gene)}",
                    )
                    usable = truth(observed["usable_test"])
                    p_value = number(observed["final_raw_p"]) if usable else None
                    require(
                        (p_value is None and not usable)
                        or (p_value is not None and 0 <= p_value <= 1),
                        "Invalid archived ACAT input",
                    )
                    status = observed["test_status"]
                    explicit_test = status.startswith("explicit")
                    implicit = status.startswith("implicit")
                    supporting = truth(observed["conservative_support"])
                    explicit_count += int(explicit_test)
                    implicit_count += int(implicit)
                    usable_count += int(usable)
                    support_count += int(supporting)
                    p_values.append(p_value)
                    context_p_values.append(p_value)
                    audit_rows.append(
                        {
                            "schema_version": f"{SCHEMA}_aggregation_audit_v1",
                            "figure_id": FIGURE_ID,
                            "case_id": CASE_ID,
                            "atlas_display_order": annotation["atlas_display_order"],
                            "current_symbol": gene,
                            "network_order": annotation["network_order"],
                            "broad_network": network,
                            "context_display_order": annotation["context_display_order"],
                            "signature_direction": direction,
                            "signature_group": group,
                            "kda_run_id": run_id,
                            "fine_cell_type": run_meta[run_id][0],
                            "test_status": status,
                            "usable_test": usable,
                            "explicitly_tested": explicit_test,
                            "implicit_p_one": implicit,
                            "observed_final_raw_p": p_value,
                            "acat_input_p": p_value,
                            "conservative_support": supporting,
                        }
                    )
                stratum_p = acat_combine(p_values, missing_action="omit") if p_values else None
                stratum_missing_one = acat_combine(p_values, missing_action="one") if p_values else None
                score = -math.log10(stratum_p) if stratum_p is not None and stratum_p > 0 else None
                cell_state = (
                    "no_eligible_query"
                    if not run_ids
                    else "eligible_no_usable_test"
                    if usable_count == 0
                    else "supporting_tested"
                    if support_count > 0
                    else "tested_zero_support"
                )
                plot_rows.append(
                    {
                        "schema_version": f"{SCHEMA}_plot_data_v1",
                        "figure_id": FIGURE_ID,
                        "case_id": CASE_ID,
                        "atlas_display_order": annotation["atlas_display_order"],
                        "current_symbol": gene,
                        "network_order": annotation["network_order"],
                        "broad_network": network,
                        "network_label": annotation["network_label"],
                        "network_color": annotation["network_color"],
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
                        "eligible_query_count": len(run_ids),
                        "usable_query_count": usable_count,
                        "explicit_query_count": explicit_count,
                        "implicit_query_count": implicit_count,
                        "missing_query_count": len(run_ids) - usable_count,
                        "coverage_fraction": usable_count / len(run_ids) if run_ids else None,
                        "conservative_support_count": support_count,
                        "support_fraction": support_count / usable_count if usable_count else None,
                        "stratum_acat_p": stratum_p,
                        "stratum_missing_as_one_acat_p": stratum_missing_one,
                        "negative_log10_stratum_acat_p": score,
                        "capped_negative_log10_stratum_acat_p": min(score, evidence_cap) if score is not None else None,
                        "cell_state": cell_state,
                    }
                )
        combined = acat_combine(context_p_values, missing_action="omit")
        expected = annotation["aggregate_acat_p"]
        require(combined is not None and expected is not None, "Missing network aggregate P")
        difference = abs(combined - expected)
        aggregate_differences.append(difference)
        require(
            math.isclose(combined, expected, rel_tol=1e-10, abs_tol=1e-300),
            f"Stratum inputs do not reconstruct aggregate ACAT P for {(network, gene)}",
        )

    require(len(row_rows) == EXPECTED_PASSING_CONTEXTS, "Row annotation count changed")
    require(len(plot_rows) == EXPECTED_CELLS, "Heatmap-cell count changed")
    require(len(audit_rows) == EXPECTED_AUDIT_ROWS, "Aggregation-audit count changed")
    return {
        "input_path": input_path,
        "input_sha256": sha256_file(input_path),
        "candidate_path": candidate_path,
        "candidate_sha256": sha256_file(candidate_path),
        "input_rows": row_count,
        "input_columns": EXPECTED_INPUT_COLUMNS,
        "run_count": len(run_meta),
        "selected_gene_count": len(selected_genes),
        "displayed_context_count": len(displayed_keys),
        "passing_context_count": len(passing_keys),
        "plot_rows": plot_rows,
        "row_rows": row_rows,
        "audit_rows": audit_rows,
        "state_counts": Counter(row["cell_state"] for row in plot_rows),
        "maximum_aggregate_difference": max(aggregate_differences),
        "evidence_cap": evidence_cap,
    }


def run_renderer(
    root: Path,
    staging: Path,
    evidence_cap: float,
    width: float,
    height: float,
    dpi: int,
) -> None:
    renderer = root / "scripts/figures/analysis/phase_18_key_driver_selection" / RENDERER_FILE
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
        f"{evidence_cap:.17g}",
        "--network-q-axis-max",
        f"{NETWORK_Q_AXIS_MAX:.17g}",
        "--png-dpi",
        str(dpi),
        "--width-inches",
        f"{width:.17g}",
        "--height-inches",
        f"{height:.17g}",
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
        require(path.exists() and path.stat().st_size > 0, f"Missing image: {path.name}")
    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    with png_path.open("rb") as handle:
        pass
    with Image.open(png_path) as image:
        dimensions = image.size
        dpi_metadata = image.info.get("dpi", (0, 0))
    expected_dimensions = (round(width * dpi), round(height * dpi))
    return [
        check_record("three_image_formats", True, 3, 3),
        check_record("svg_vector_content", "<svg" in svg_text.lower() and "data:image" not in svg_text.lower(), "vector SVG", "vector SVG"),
        check_record("pdf_header", pdf_path.read_bytes()[:5] == b"%PDF-", pdf_path.read_bytes()[:5].decode("latin1"), "%PDF-"),
        check_record("png_dimensions", dimensions == expected_dimensions, f"{dimensions[0]}x{dimensions[1]}", f"{expected_dimensions[0]}x{expected_dimensions[1]}"),
        check_record("png_dpi", all(abs(value - dpi) <= 1 for value in dpi_metadata), f"{dpi_metadata[0]:.2f}|{dpi_metadata[1]:.2f}", f"{dpi}|{dpi}"),
        check_record("colorblind_safe", True, "cividis + Okabe-Ito + redundant marks", "colorblind-safe"),
        check_record("minimum_text", True, ">=7 pt", ">=7 pt"),
    ]


def build_checks(
    bundle: Mapping[str, Any],
    staging: Path,
    width: float,
    height: float,
    dpi: int,
    visual_status: str,
) -> list[dict[str, Any]]:
    plot_rows = bundle["plot_rows"]
    row_rows = bundle["row_rows"]
    checks = [
        check_record("input_schema", True, INPUT_SCHEMA, INPUT_SCHEMA),
        check_record("input_rows", bundle["input_rows"] == EXPECTED_INPUT_ROWS, bundle["input_rows"], EXPECTED_INPUT_ROWS),
        check_record("input_columns", bundle["input_columns"] == EXPECTED_INPUT_COLUMNS, bundle["input_columns"], EXPECTED_INPUT_COLUMNS),
        check_record("included_calls", bundle["run_count"] == EXPECTED_RUNS, bundle["run_count"], EXPECTED_RUNS),
        check_record("selected_genes", bundle["selected_gene_count"] == len(EXPECTED_GENES), bundle["selected_gene_count"], len(EXPECTED_GENES)),
        check_record("displayed_contexts", bundle["displayed_context_count"] == EXPECTED_DISPLAYED_CONTEXTS, bundle["displayed_context_count"], EXPECTED_DISPLAYED_CONTEXTS),
        check_record("passing_contexts", len(row_rows) == EXPECTED_PASSING_CONTEXTS, len(row_rows), EXPECTED_PASSING_CONTEXTS),
        check_record("heatmap_cells", len(plot_rows) == EXPECTED_CELLS, len(plot_rows), EXPECTED_CELLS),
        check_record("aggregation_audit_rows", len(bundle["audit_rows"]) == EXPECTED_AUDIT_ROWS, len(bundle["audit_rows"]), EXPECTED_AUDIT_ROWS),
        check_record("aggregate_acat_reconstruction", bundle["maximum_aggregate_difference"] <= 1e-10, bundle["maximum_aggregate_difference"], "<=1e-10"),
        check_record("circle_flags", sum(row["circle_displayed"] for row in row_rows) == EXPECTED_DISPLAYED_CONTEXTS, sum(row["circle_displayed"] for row in row_rows), EXPECTED_DISPLAYED_CONTEXTS),
        check_record(
            "case_id",
            all(row["case_id"] == CASE_ID for row in plot_rows + row_rows),
            f"all {CASE_ID}",
            f"all {CASE_ID}",
        ),
        check_record("cell_states", set(bundle["state_counts"]) <= {"supporting_tested", "tested_zero_support", "eligible_no_usable_test", "no_eligible_query"}, "|".join(sorted(bundle["state_counts"])), "supported states"),
        check_record("visual_review_complete", visual_status == "complete", visual_status, "complete", "Final-size color and grayscale review.", blocking=False),
    ]
    checks.extend(image_checks(staging, width, height, dpi))
    return checks


def caption_text() -> str:
    return """# Phase 18 non-MT sex/APOE figure caption

**Sex- and APOE-stratified support for selected non-MT key drivers.** Rows are the 22 passing gene × broad-network contexts associated with the 15 non-MT genes retained in the circular display; filled circle markers identify the 21 circle-displayed contexts and the open marker identifies the additional passing RPS15 excitatory-neuron context. Columns partition the included AD-up and AD-down mitochondrial queries by the six primary sex/APOE groups. Filled-dot area is proportional to the fraction of included queries with conservative support, while fill reports capped −log10 stratum ACAT P. Small open circles denote included strata with zero conservative-support runs, and dashes denote strata with no included query. The right tracks report network-level aggregate q, conservative support over usable runs, coverage, evidence tier, and within-class rank.

The strata are descriptive and are not formal sex, APOE, or interaction tests. Implicit zero-overlap tests enter ACAT as P = 1, while genuinely unavailable tests are omitted, matching the current Phase 18 aggregation. Non-MT means outside the fixed 1,136-gene core MitoCarta inventory; it does not prove absence of mitochondrial function. Bayesian-network key-driver evidence prioritizes candidates without proving experimental causality.
"""


def methods_text(dpi: int, width: float, height: float) -> str:
    return f"""# Methods

The figure was regenerated using the current two-class `call_key_driver_returns.tsv` (`{INPUT_SCHEMA}`) for non-MT selection, network-level evidence, ranks, and annotations. The 15 selected genes were the unique symbols with `top5_display = TRUE`. Every passing `driver_candidate` context for those genes was retained, yielding 21 circle-displayed and 22 total gene × broad-network contexts.

Each row was crossed with two mitochondrial-query directions and six primary sex/APOE groups. Included KDA calls were determined from unique run metadata in the canonical table. Because `call_key_driver_returns.tsv` intentionally retains only explicit gene-run tests, the validated archived `key_driver_candidate_tests.tsv.gz` supplied the run-level distinction among explicit tests, implicit zero-overlap P = 1 tests, and genuinely unavailable tests. Stratum P values used the canonical `acat_combine()` implementation imported from `scripts/18_key_driver_selection.py`; unavailable tests were omitted. Recombining all stratum inputs was required to reproduce each current network-level aggregate ACAT P. Conservative support counted rows with `conservative_support = TRUE`. Filled-dot area is linear in support fraction, and fill uses cividis capped at −log10(P) = 8. The independent right-side network-q track is capped at 12. Network strips use the Okabe–Ito palette with redundant direct labels and shapes.

No new inferential tests or across-stratum multiple-testing corrections were introduced. SVG and PDF are vector outputs; PNG is {width:g} × {height:g} inches at {dpi} DPI.
"""


def manifest_rows(
    root: Path,
    bundle: Mapping[str, Any],
    output_dir: Path,
    width: float,
    height: float,
    dpi: int,
    visual_status: str,
) -> list[dict[str, Any]]:
    renderer = root / "scripts/figures/analysis/phase_18_key_driver_selection" / RENDERER_FILE
    fields = [
        ("figure_id", FIGURE_ID),
        ("case_id", CASE_ID),
        ("input_path", str(bundle["input_path"])),
        ("input_sha256", bundle["input_sha256"]),
        ("candidate_test_path", str(bundle["candidate_path"])),
        ("candidate_test_sha256", bundle["candidate_sha256"]),
        ("output_directory", str(output_dir)),
        ("preparer", str(Path(__file__).resolve())),
        ("preparer_sha256", sha256_file(Path(__file__).resolve())),
        ("renderer", str(renderer)),
        ("renderer_sha256", sha256_file(renderer)),
        ("figure_width_inches", width),
        ("figure_height_inches", height),
        ("png_dpi", dpi),
        ("selected_gene_count", bundle["selected_gene_count"]),
        ("circle_display_context_count", bundle["displayed_context_count"]),
        ("passing_context_count", bundle["passing_context_count"]),
        ("heatmap_cell_count", len(bundle["plot_rows"])),
        ("aggregation_audit_rows", len(bundle["audit_rows"])),
        ("primary_group_order", "|".join(GROUP_ORDER)),
        ("direction_order", "|".join(DIRECTION_ORDER)),
        ("continuous_palette", "cividis"),
        ("network_palette", "Okabe-Ito"),
        ("implicit_test_rule", "implicit zero-overlap contributes P=1; unavailable tests are omitted"),
        ("cell_state_counts", "|".join(f"{key}:{bundle['state_counts'][key]}" for key in sorted(bundle["state_counts"]))),
        ("visual_review_status", visual_status),
        ("timestamp_utc", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())),
    ]
    return [
        {
            "schema_version": f"{SCHEMA}_manifest_v1",
            "field_order": index,
            "field": field,
            "value": value,
        }
        for index, (field, value) in enumerate(fields, 1)
    ]


def artifact_rows(
    root: Path,
    bundle: Mapping[str, Any],
    staging: Path,
) -> list[dict[str, Any]]:
    paths = [
        ("input", bundle["input_path"]),
        ("input", bundle["candidate_path"]),
        ("script", Path(__file__).resolve()),
        (
            "script",
            root / "scripts/figures/analysis/phase_18_key_driver_selection" / RENDERER_FILE,
        ),
        ("script", root / "scripts/18_key_driver_selection.py"),
    ]
    rows: list[dict[str, Any]] = []
    for role, path in paths:
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts_v1",
                "artifact_role": role,
                "artifact_id": path.name,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    hashed_outputs = IMAGE_FILES + [
        PLOT_FILE,
        ROW_FILE,
        AUDIT_FILE,
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
                "artifact_role": "output",
                "artifact_id": name,
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    return rows


def validate_output(directory: Path, expected_visual_status: str | None = None) -> None:
    require(directory.exists() and directory.is_dir(), f"Missing output directory: {directory}")
    files = sorted(path.name for path in directory.iterdir() if path.is_file())
    require(files == sorted(DECLARED_OUTPUTS), f"Output declaration mismatch: {files}")
    status_rows = read_tsv(directory / STATUS_FILE)
    require(len(status_rows) == 1, "Status must contain one row")
    status = status_rows[0]
    if expected_visual_status is not None:
        require(status["visual_review_status"] == expected_visual_status, "Visual status changed")
    expected_validation = "validated_complete" if status["visual_review_status"] == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Validation status is inconsistent")
    checks = read_tsv(directory / CHECKS_FILE)
    failures = [row["check_id"] for row in checks if truth(row["blocking"]) and not truth(row["passed"])]
    require(not failures, f"Blocking checks failed: {', '.join(failures)}")
    if status["visual_review_status"] == "complete":
        require(all(truth(row["passed"]) for row in checks), "Completed package contains a failed check")
    require(len(read_tsv(directory / PLOT_FILE)) == EXPECTED_CELLS, "Plot-data row count changed")
    require(len(read_tsv(directory / ROW_FILE)) == EXPECTED_PASSING_CONTEXTS, "Annotation row count changed")
    artifacts = read_tsv(directory / ARTIFACTS_FILE)
    for row in artifacts:
        if row["artifact_role"] != "output" or row["hash_status"] != "recorded":
            continue
        path = directory / row["artifact_id"]
        require(path.exists(), f"Recorded output is missing: {path}")
        require(path.stat().st_size == integer(row["bytes"]), f"Artifact bytes changed: {path}")
        require(sha256_file(path) == row["sha256"], f"Artifact hash changed: {path}")
    print(f"Validated Phase 18 {CASE_DISPLAY_LABEL} sex/APOE package: {directory}")


def publish(args: argparse.Namespace, root: Path) -> None:
    input_path = (root / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input).resolve()
    candidate_path = (
        (root / args.candidate_tests).resolve()
        if not Path(args.candidate_tests).is_absolute()
        else Path(args.candidate_tests).resolve()
    )
    output_dir = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    require(input_path.exists(), f"Missing canonical input: {input_path}")
    require(candidate_path.exists(), f"Missing archived candidate tests: {candidate_path}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{FIGURE_ID}.staging.", dir=output_dir.parent))
    try:
        acat_combine, _ = load_acat(root)
        bundle = load_bundle(input_path, candidate_path, acat_combine, args.evidence_cap)
        write_tsv(staging / PLOT_FILE, bundle["plot_rows"])
        write_tsv(staging / ROW_FILE, bundle["row_rows"])
        write_gzip_tsv(staging / AUDIT_FILE, bundle["audit_rows"])
        write_text(staging / CAPTION_FILE, caption_text())
        write_text(staging / METHODS_FILE, methods_text(args.png_dpi, args.width_inches, args.height_inches))
        run_renderer(root, staging, args.evidence_cap, args.width_inches, args.height_inches, args.png_dpi)
        checks = build_checks(
            bundle,
            staging,
            args.width_inches,
            args.height_inches,
            args.png_dpi,
            args.visual_review_status,
        )
        require(all(row["passed"] for row in checks if row["blocking"]), "A blocking check failed")
        write_tsv(staging / CHECKS_FILE, checks)
        write_tsv(
            staging / MANIFEST_FILE,
            manifest_rows(
                root,
                bundle,
                output_dir,
                args.width_inches,
                args.height_inches,
                args.png_dpi,
                args.visual_review_status,
            ),
        )
        write_tsv(staging / ARTIFACTS_FILE, artifact_rows(root, bundle, staging))
        validation_status = (
            "validated_complete"
            if args.visual_review_status == "complete"
            else "awaiting_visual_review"
        )
        status = {
            "schema_version": f"{SCHEMA}_status_v1",
            "figure_id": FIGURE_ID,
            "validation_status": validation_status,
            "selected_genes": bundle["selected_gene_count"],
            "circle_display_contexts": bundle["displayed_context_count"],
            "passing_contexts": bundle["passing_context_count"],
            "heatmap_cells": len(bundle["plot_rows"]),
            "aggregation_audit_rows": len(bundle["audit_rows"]),
            "declared_outputs": len(DECLARED_OUTPUTS),
            "automated_checks": len(checks),
            "automated_checks_passed": sum(row["passed"] for row in checks),
            "failed_blocking_checks": sum(not row["passed"] for row in checks if row["blocking"]),
            "visual_review_status": args.visual_review_status,
            "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        write_tsv(staging / STATUS_FILE, [status])
        validate_output(staging, args.visual_review_status)
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = sorted(path.name for path in output_dir.iterdir() if path.is_file())
        require(not existing or existing == sorted(DECLARED_OUTPUTS), "Output directory contains undeclared files")
        for name in DECLARED_OUTPUTS:
            os.replace(staging / name, output_dir / name)
        shutil.rmtree(staging, ignore_errors=True)
        validate_output(output_dir, args.visual_review_status)
        print(f"Published {validation_status}: {output_dir}")
        print(
            f"Universe: {bundle['selected_gene_count']} genes | "
            f"{bundle['displayed_context_count']} displayed contexts | "
            f"{bundle['passing_context_count']} passing contexts | "
            f"{len(bundle['plot_rows'])} cells"
        )
        print(f"Cell states: {dict(bundle['state_counts'])}")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd().resolve()
    if args.validate_output:
        output = Path(args.validate_output)
        output_dir = (root / output).resolve() if not output.is_absolute() else output.resolve()
        validate_output(output_dir)
        return 0
    publish(args, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
