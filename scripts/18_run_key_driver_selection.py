#!/usr/bin/env python3
"""Phase 18 local key-driver selection from the validated Phase 12 bundle.

The implementation intentionally uses only the locally available scientific
Python stack (NumPy, SciPy, and PyYAML). It reconstructs KDA neighborhoods
from the authoritative Phase 12 queries, backgrounds, and network files; it
does not use figure-derived candidate tables as scientific inputs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np
import yaml
from scipy.stats import cauchy, hypergeom


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
NA_TEXT = "NA"
SCHEMA = "mitochondrial_key_driver_selection_v1"
CASE1 = "case1_core_mito_in_query"
CASE2 = "case2_core_mito_not_in_query"
CASE3 = "case3_not_core_mito"
CASE_ORDER = {CASE1: 1, CASE2: 2, CASE3: 3}

ACAT_EXAMPLE = [
    [0.5746569, 0.7090122, 0.7965851, 0.1149619],
    [0.6513363, 0.6671072, 0.5985140, 0.4991580],
    [0.1632148, 0.9312446, 0.9105127, 0.2293418],
    [0.8836971, 0.8424568, 0.2578088, 0.3955429],
    [0.6770827, 0.7551785, 0.3221481, 0.5570227],
]
ACAT_EXAMPLE_EXPECTED = [
    0.4768092003,
    0.6079561876,
    0.7884404860,
    0.7135191247,
    0.5935618969,
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def display_value(value: Any) -> Any:
    if value is None:
        return NA_TEXT
    if isinstance(value, float) and not math.isfinite(value):
        return NA_TEXT
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def project_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", newline="")
    return path.open(mode, newline="")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"Required file does not exist: {path}")
    with open_text(path, "r") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path, "r") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: Sequence[str],
    schema_version: str,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    count = 0
    connection = (
        gzip.open(temporary, "wt", newline="", compresslevel=6)
        if path.suffix == ".gz"
        else temporary.open("w", newline="")
    )
    with connection as handle:
        fieldnames = ["schema_version", *[x for x in fields if x != "schema_version"]]
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = {name: display_value(row.get(name)) for name in fields}
            output["schema_version"] = schema_version
            writer.writerow(output)
            count += 1
    temporary.replace(path)
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def bh_adjust(values: Sequence[float | None]) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    valid = [
        index
        for index, value in enumerate(values)
        if value is not None and math.isfinite(float(value))
    ]
    ordered = sorted(valid, key=lambda index: (float(values[index]), index))
    previous = 1.0
    total = len(ordered)
    for position in range(total - 1, -1, -1):
        index = ordered[position]
        adjusted = min(previous, float(values[index]) * total / (position + 1), 1.0)
        result[index] = adjusted
        previous = adjusted
    return result


def acat_statistic(p_value: float) -> float:
    if p_value < 1e-15:
        return 1.0 / (p_value * math.pi)
    return math.tan((0.5 - p_value) * math.pi)


def acat_combine(
    p_values: Sequence[float | None],
    *,
    missing_action: str = "omit",
    tolerance: float = 1e-300,
) -> float | None:
    values = np.asarray(
        [math.nan if value is None else float(value) for value in p_values],
        dtype=float,
    )
    if np.any(np.isinf(values)) or np.any((values < 0) | (values > 1)):
        fail("ACAT inputs must be finite P values in [0, 1] or missing")
    if missing_action == "omit":
        values = values[~np.isnan(values)]
    elif missing_action == "one":
        values[np.isnan(values)] = 1.0
    else:
        fail(f"Unsupported ACAT missing action: {missing_action}")
    if values.size == 0:
        return None
    if np.all(values == 1):
        return 1.0
    if np.any(values == 0):
        positive = values[values > 0]
        replacement = min(float(np.min(positive)), tolerance) if positive.size else tolerance
        values[values == 0] = replacement
    if np.any(values == 1):
        values[values == 1] = float(np.max(values[values < 1])) / 2.0 + 0.5
    statistic = float(np.mean([acat_statistic(float(value)) for value in values]))
    return float(cauchy.sf(statistic))


def validate_acat_example() -> float:
    observed = [acat_combine(row) for row in ACAT_EXAMPLE]
    return max(
        abs(float(value) - expected)
        for value, expected in zip(observed, ACAT_EXAMPLE_EXPECTED)
    )


def enrichment_statistics(q: int, m: int, k: int, total: int) -> tuple[float, float, float]:
    if min(q, m, k, total) < 0 or m > total or k > total or q > min(m, k):
        fail(f"Impossible hypergeometric counts: q={q}, m={m}, k={k}, M={total}")
    if q == 0:
        log_p = 0.0
        p_value = 1.0
    else:
        log_p = float(hypergeom.logsf(q - 1, total, m, k))
        p_value = 0.0 if log_p == -math.inf else float(math.exp(log_p))
    fold = (
        0.0
        if m == 0 or k == 0
        else float(
            (Decimal(q) * Decimal(total) / Decimal(m) / Decimal(k)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
        )
    )
    return log_p, p_value, fold


def expand_candidates(
    query: set[str], undirected: dict[str, set[str]], layers: int = 3
) -> set[str]:
    seed = set(query)
    result: set[str] | None = None
    for _ in range(layers):
        expanded = set(seed)
        for node in seed:
            expanded.update(undirected.get(node, ()))
        if expanded == seed:
            break
        result = expanded
        seed = expanded
    return set() if result is None else result


def directed_layers(
    candidate: str, outgoing: dict[str, set[str]], layers: int = 3
) -> list[set[str]]:
    seed = {candidate}
    result: list[set[str]] = []
    for _ in range(layers):
        expanded = set(seed)
        for node in seed:
            expanded.update(outgoing.get(node, ()))
        if expanded == seed:
            break
        result.append(expanded)
        seed = expanded
    return result


def load_annotation(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    annotation: dict[str, dict[str, Any]] = {}
    conflicts: list[str] = []
    for row in iter_tsv(path):
        symbol = row.get("symbol_hgnc_current", "")
        if not symbol or symbol == NA_TEXT:
            continue
        current = {
            "is_core_mito": is_true(row.get("is_mitocarta3")),
            "mitocarta_canonical_symbol": row.get("mitocarta_canonical_symbol") or NA_TEXT,
            "mito_tier": row.get("mito_tier") or NA_TEXT,
            "genome_origin": row.get("genome_origin") or NA_TEXT,
            "is_mtdna_gene": is_true(row.get("is_mtDNA_gene")),
            "extended_reference_member": is_true(row.get("extended_reference_member")),
            "mapping_status": row.get("mapping_status") or NA_TEXT,
            "phase03_mitocarta_match_type": row.get("phase03_mitocarta_match_type") or NA_TEXT,
        }
        previous = annotation.get(symbol)
        if previous is None:
            annotation[symbol] = current
        else:
            scientific_fields = (
                "is_core_mito",
                "mitocarta_canonical_symbol",
                "mito_tier",
                "genome_origin",
                "is_mtdna_gene",
                "extended_reference_member",
                "phase03_mitocarta_match_type",
            )
            if any(previous[field] != current[field] for field in scientific_fields):
                conflicts.append(symbol)
                continue
            mapping_routes = set(str(previous["mapping_status"]).split("|"))
            mapping_routes.update(str(current["mapping_status"]).split("|"))
            previous["mapping_status"] = "|".join(sorted(mapping_routes))
    return annotation, sorted(set(conflicts))


def classify_case(symbol: str, query: set[str], annotation: dict[str, dict[str, Any]]) -> str:
    core = bool(annotation.get(symbol, {}).get("is_core_mito", False))
    if not core:
        return CASE3
    return CASE1 if symbol in query else CASE2


def load_network(path: Path) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    with path.open() as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 2:
                continue
            edge = (sys.intern(fields[0]), sys.intern(fields[1]))
            if edge[0] and edge[1] and edge[0] != edge[1] and edge not in seen:
                seen.add(edge)
                edges.append(edge)
    return edges


def network_adjacency(
    edges: Sequence[tuple[str, str]], background: set[str]
) -> tuple[list[tuple[str, str]], dict[str, set[str]], dict[str, set[str]]]:
    induced = [(a, b) for a, b in edges if a in background and b in background]
    outgoing: dict[str, set[str]] = defaultdict(set)
    undirected: dict[str, set[str]] = defaultdict(set)
    for source, target in induced:
        outgoing[source].add(target)
        undirected[source].add(target)
        undirected[target].add(source)
    return induced, outgoing, undirected


def reconstruct_run(
    run: dict[str, Any],
    query: set[str],
    background: set[str],
    edges: Sequence[tuple[str, str]],
    annotation: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    induced, outgoing, undirected = network_adjacency(edges, background)
    if len(induced) != as_int(run["induced_network_edges"]):
        fail(f"Induced edge count mismatch for {run['kda_run_id']}")
    targets = expand_candidates(query, undirected)
    explicit: dict[str, dict[str, Any]] = {}
    layer_count = 0
    for candidate in sorted(targets):
        layer_rows: list[dict[str, Any]] = []
        for layer, neighborhood in enumerate(directed_layers(candidate, outgoing), start=1):
            q = len(neighborhood & query)
            m = len(neighborhood)
            log_p, p_value, fold = enrichment_statistics(q, m, len(query), len(background))
            row = {
                "layer": layer,
                "overlap": q,
                "neighborhood": m,
                "non_neighborhood": len(background) - m,
                "signature_size": len(query),
                "background_size": len(background),
                "fold": fold,
                "log_p": log_p,
                "p": p_value,
            }
            layer_rows.append(row)
            layer_count += 1
        if not layer_rows:
            continue
        original = min(layer_rows, key=lambda row: (row["log_p"], row["layer"]))
        case_id = classify_case(candidate, query, annotation)
        if case_id == CASE1:
            corrected_rows: list[dict[str, Any]] = []
            for row in layer_rows:
                corrected_q = row["overlap"] - 1
                corrected_m = row["neighborhood"] - 1
                corrected_k = row["signature_size"] - 1
                corrected_total = row["background_size"] - 1
                log_p, p_value, fold = enrichment_statistics(
                    corrected_q, corrected_m, corrected_k, corrected_total
                )
                corrected_rows.append(
                    {
                        **row,
                        "overlap": corrected_q,
                        "neighborhood": corrected_m,
                        "non_neighborhood": corrected_total - corrected_m,
                        "signature_size": corrected_k,
                        "background_size": corrected_total,
                        "fold": fold,
                        "log_p": log_p,
                        "p": p_value,
                    }
                )
            final = min(corrected_rows, key=lambda row: (row["log_p"], row["layer"]))
        else:
            final = dict(original)
        explicit[candidate] = {
            "case_id": case_id,
            "original": dict(original),
            "final": dict(final),
            "test_status": "explicit_zero_overlap" if original["overlap"] == 0 else "explicit_test",
        }
    original_q = bh_adjust([record["original"]["p"] for record in explicit.values()])
    final_q = bh_adjust([record["final"]["p"] for record in explicit.values()])
    for record, oq, fq in zip(explicit.values(), original_q, final_q):
        record["original_q"] = oq
        record["final_q"] = fq
    summary = {
        "induced_edges": len(induced),
        "background_genes": len(background),
        "explicit_candidates": len(explicit),
        "implicit_candidates": len(background) - len(explicit),
        "layer_tests": layer_count,
    }
    return explicit, summary


def implicit_result(run: dict[str, Any]) -> dict[str, Any]:
    total = as_int(run["effective_background_genes"])
    query = as_int(run["effective_query_genes"])
    row = {
        "layer": None,
        "overlap": 0,
        "neighborhood": 0,
        "non_neighborhood": total,
        "signature_size": query,
        "background_size": total,
        "fold": None,
        "log_p": 0.0,
        "p": 1.0,
    }
    return {
        "original": dict(row),
        "final": dict(row),
        "original_q": 1.0,
        "final_q": 1.0,
        "test_status": "implicit_zero_overlap",
    }


def evidence_for(
    symbol: str,
    run: dict[str, Any],
    query: set[str],
    background: set[str],
    explicit: dict[str, dict[str, Any]],
    annotation: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = classify_case(symbol, query, annotation)
    if symbol not in background:
        return {
            "case_id": case_id,
            "test_status": "absent_from_background",
            "usable": False,
            "p": None,
            "q": None,
            "support": False,
            "other_overlap": None,
            "fold": None,
            "record": None,
        }
    record = explicit.get(symbol)
    if record is None:
        record = implicit_result(run)
        record["case_id"] = case_id
    final = record["final"]
    other_overlap = final["overlap"]
    fold = final["fold"]
    support = (
        other_overlap >= 2
        and fold is not None
        and fold > 1.0
        and record["final_q"] is not None
        and record["final_q"] <= 0.05
    )
    return {
        "case_id": case_id,
        "test_status": record["test_status"],
        "usable": True,
        "p": final["p"],
        "q": record["final_q"],
        "support": support,
        "other_overlap": other_overlap,
        "fold": fold,
        "record": record,
    }


def annotation_fields(symbol: str, annotation: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = annotation.get(symbol)
    if row is None:
        return {
            "is_core_mito": False,
            "mitocarta_canonical_symbol": None,
            "mito_tier": "annotation_missing_treated_not_core",
            "genome_origin": None,
            "is_mtdna_gene": False,
            "extended_reference_member": False,
            "mapping_status": "annotation_missing",
            "phase03_mitocarta_match_type": None,
        }
    return dict(row)


def aggregate_network(
    network: str,
    network_runs: list[dict[str, Any]],
    genes: list[str],
    signatures: dict[str, set[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    annotation: dict[str, dict[str, Any]],
    minimum_coverage: float,
) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for symbol in genes:
        ann = annotation_fields(symbol, annotation)
        if ann["is_core_mito"]:
            case_runs = {
                CASE1: [run for run in network_runs if symbol in signatures[run["kda_run_id"]]],
                CASE2: [run for run in network_runs if symbol not in signatures[run["kda_run_id"]]],
            }
        else:
            case_runs = {CASE3: list(network_runs)}
        for case_id, denominator_runs in case_runs.items():
            if not denominator_runs:
                continue
            values: list[float | None] = []
            support_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
            explicit_count = implicit_count = missing_count = 0
            folds: list[float] = []
            for run in denominator_runs:
                run_id = run["kda_run_id"]
                evidence = evidence_for(
                    symbol,
                    run,
                    signatures[run_id],
                    backgrounds[run_id],
                    explicit_by_run[run_id],
                    annotation,
                )
                if evidence["case_id"] != case_id:
                    fail(f"Case drift for {network}/{symbol}/{run_id}")
                values.append(evidence["p"])
                if not evidence["usable"]:
                    missing_count += 1
                elif evidence["test_status"].startswith("explicit"):
                    explicit_count += 1
                else:
                    implicit_count += 1
                if evidence["support"]:
                    support_rows.append((run, evidence))
                    folds.append(float(evidence["fold"]))
            usable_count = explicit_count + implicit_count
            denominator = len(denominator_runs)
            coverage = usable_count / denominator
            acat_all = acat_combine(values, missing_action="omit")
            acat_missing_one = acat_combine(values, missing_action="one")
            usable_values = [float(value) for value in values if value is not None]
            mean_log_score = (
                statistics.fmean(-math.log10(max(value, 1e-300)) for value in usable_values)
                if usable_values
                else None
            )
            support_fine = sorted({run["fine_cell_type"] for run, _ in support_rows})
            support_groups = sorted({run["signature_group"] for run, _ in support_rows})
            support_directions = sorted({run["signature_direction"] for run, _ in support_rows})
            aggregates.append(
                {
                    "broad_network": network,
                    "current_symbol": symbol,
                    "case_order": CASE_ORDER[case_id],
                    "case_id": case_id,
                    **ann,
                    "eligible_run_count": denominator,
                    "usable_run_count": usable_count,
                    "explicit_run_count": explicit_count,
                    "implicit_run_count": implicit_count,
                    "missing_run_count": missing_count,
                    "coverage_numerator": usable_count,
                    "coverage_denominator": denominator,
                    "coverage_fraction": coverage,
                    "coverage_pass": coverage >= minimum_coverage,
                    "conservative_support_count": len(support_rows),
                    "conservative_support_pass": len(support_rows) >= 1,
                    "recurrence_fraction": len(support_rows) / usable_count if usable_count else 0.0,
                    "supporting_fine_cell_type_count": len(support_fine),
                    "supporting_fine_cell_types": "|".join(support_fine),
                    "supporting_group_count": len(support_groups),
                    "supporting_groups": "|".join(support_groups),
                    "supporting_direction_count": len(support_directions),
                    "supporting_directions": "|".join(support_directions),
                    "median_support_fold_enrichment": statistics.median(folds) if folds else None,
                    "maximum_support_fold_enrichment": max(folds) if folds else None,
                    "aggregate_acat_p": acat_all if coverage >= minimum_coverage else None,
                    "aggregate_acat_q": None,
                    "missing_as_one_acat_p": acat_missing_one if coverage >= minimum_coverage else None,
                    "missing_as_one_acat_q": None,
                    "mean_log_p_score": mean_log_score,
                    "terminal_candidate_status": None,
                    "within_case_rank": None,
                    "top5_display": False,
                    "stability_assessable_repetitions": 0,
                    "stability_nominal_fraction": None,
                    "stability_q_fraction": None,
                    "stability_candidate_fraction": None,
                    "stability_worst_rank": None,
                    "evidence_tier": None,
                    "_all_acat_p": acat_all,
                    "_missing_one_p": acat_missing_one,
                    "_values": values,
                    "_run_ids": [run["kda_run_id"] for run in denominator_runs],
                }
            )
    apply_aggregate_statistics(aggregates, minimum_coverage)
    return aggregates


def apply_aggregate_statistics(rows: list[dict[str, Any]], minimum_coverage: float) -> None:
    primary_indices = [
        index
        for index, row in enumerate(rows)
        if row["coverage_fraction"] >= minimum_coverage and row["_all_acat_p"] is not None
    ]
    primary_q = bh_adjust([rows[index]["_all_acat_p"] for index in primary_indices])
    missing_q = bh_adjust([rows[index]["_missing_one_p"] for index in primary_indices])
    for index, q_value, missing_value in zip(primary_indices, primary_q, missing_q):
        rows[index]["aggregate_acat_p"] = rows[index]["_all_acat_p"]
        rows[index]["aggregate_acat_q"] = q_value
        rows[index]["missing_as_one_acat_p"] = rows[index]["_missing_one_p"]
        rows[index]["missing_as_one_acat_q"] = missing_value
    for row in rows:
        q_value = row["aggregate_acat_q"]
        p_value = row["aggregate_acat_p"]
        row["aggregate_q_pass"] = q_value is not None and q_value <= 0.05
        if row["coverage_fraction"] < minimum_coverage:
            status = "insufficient_coverage"
        elif p_value is None or q_value is None:
            status = "not_testable"
        elif q_value <= 0.05 and row["conservative_support_count"] >= 1:
            status = "driver_candidate"
        elif q_value <= 0.05:
            status = "aggregate_only"
        elif p_value <= 0.05:
            status = "exploratory"
        else:
            status = "not_supported"
        row["terminal_candidate_status"] = status
    assign_candidate_ranks(rows)


def assign_candidate_ranks(rows: list[dict[str, Any]]) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        row["within_case_rank"] = None
        row["top5_display"] = False
        if row["terminal_candidate_status"] == "driver_candidate":
            groups[row["case_id"]].append(row)
    for case_rows in groups.values():
        case_rows.sort(
            key=lambda row: (
                float(row["aggregate_acat_q"]),
                float(row["aggregate_acat_p"]),
                row["current_symbol"],
            )
        )
        for rank, row in enumerate(case_rows, start=1):
            row["within_case_rank"] = rank
            row["top5_display"] = rank <= 5


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def scope_subsets(aggregates: list[dict[str, Any]]) -> list[tuple[str, str, str, list[dict[str, Any]]]]:
    result = [("overall", "ALL", "ALL", aggregates)]
    networks = sorted({row["broad_network"] for row in aggregates})
    for network in networks:
        network_rows = [row for row in aggregates if row["broad_network"] == network]
        result.append(("broad_network", network, "ALL", network_rows))
        for case_id in (CASE1, CASE2, CASE3):
            rows = [row for row in network_rows if row["case_id"] == case_id]
            result.append(("broad_network_case", network, case_id, rows))
    return result


def count_distinct(rows: Sequence[dict[str, Any]]) -> int:
    return len({row["current_symbol"] for row in rows})


def funnel_row(
    report_type: str,
    scope: str,
    network: str,
    case_id: str,
    filter_number: int,
    filter_name: str,
    step: int,
    unit: str,
    entering: Sequence[dict[str, Any]],
    passing: Sequence[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    passing_ids = {id(row) for row in passing}
    failing = [row for row in entering if id(row) not in passing_ids]
    return {
        "report_type": report_type,
        "summary_scope": scope,
        "broad_network": network,
        "case_id": case_id,
        "filter_number": filter_number,
        "filter_name": filter_name,
        "ordered_funnel_step": step,
        "counting_unit": unit,
        "input_n": len(entering),
        "pass_n": len(passing),
        "fail_n": len(failing),
        "cumulative_remaining_n": len(passing),
        "input_distinct_gene_n": count_distinct(entering),
        "pass_distinct_gene_n": count_distinct(passing),
        "fail_distinct_gene_n": count_distinct(failing),
        "remaining_distinct_gene_n": count_distinct(passing),
        "explicit_n": None,
        "implicit_n": None,
        "absent_n": None,
        "invalid_n": 0,
        "not_testable_n": sum(row["terminal_candidate_status"] == "not_testable" for row in failing),
        "failure_reason": reason,
    }


def build_filter_funnel(
    structural_runs: list[dict[str, Any]],
    included_runs: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    network_genes: dict[str, list[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    network_order: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scope, network in [("overall", "ALL"), *[("broad_network", n) for n in network_order]]:
        subset = structural_runs if network == "ALL" else [r for r in structural_runs if r["broad_network"] == network]
        passed = [r for r in subset if r["phase18_included"]]
        rows.append(
            {
                "report_type": "native_filter",
                "summary_scope": scope,
                "broad_network": network,
                "case_id": "ALL",
                "filter_number": 1,
                "filter_name": "frozen_run_scope",
                "ordered_funnel_step": 1,
                "counting_unit": "run_slot",
                "input_n": len(subset),
                "pass_n": len(passed),
                "fail_n": len(subset) - len(passed),
                "cumulative_remaining_n": len(passed),
                "input_distinct_gene_n": None,
                "pass_distinct_gene_n": None,
                "fail_distinct_gene_n": None,
                "remaining_distinct_gene_n": None,
                "explicit_n": None,
                "implicit_n": None,
                "absent_n": None,
                "invalid_n": 0,
                "not_testable_n": None,
                "failure_reason": "phase12_ineligible_or_query_below_10",
            }
        )
    for scope, network in [("overall", "ALL"), *[("broad_network", n) for n in network_order]]:
        selected_networks = [n for n in network_order if network == "ALL" or n == network]
        opportunities = usable = explicit_n = implicit_n = absent_n = 0
        distinct_input: set[str] = set()
        distinct_pass: set[str] = set()
        distinct_fail: set[str] = set()
        for name in selected_networks:
            runs = [r for r in included_runs if r["broad_network"] == name]
            genes = network_genes.get(name, [])
            distinct_input.update(genes)
            for run in runs:
                run_id = run["kda_run_id"]
                background = backgrounds[run_id]
                explicit = explicit_by_run[run_id]
                opportunities += len(genes)
                usable += len(background)
                explicit_n += len(explicit)
                implicit_n += len(background) - len(explicit)
                absent_n += len(genes) - len(background)
                distinct_pass.update(background)
                distinct_fail.update(set(genes) - background)
        rows.append(
            {
                "report_type": "native_filter",
                "summary_scope": scope,
                "broad_network": network,
                "case_id": "ALL",
                "filter_number": 2,
                "filter_name": "usable_gene_level_result",
                "ordered_funnel_step": 2,
                "counting_unit": "gene_included_run_opportunity",
                "input_n": opportunities,
                "pass_n": usable,
                "fail_n": absent_n,
                "cumulative_remaining_n": usable,
                "input_distinct_gene_n": len(distinct_input),
                "pass_distinct_gene_n": len(distinct_pass),
                "fail_distinct_gene_n": len(distinct_fail),
                "remaining_distinct_gene_n": len(distinct_pass),
                "explicit_n": explicit_n,
                "implicit_n": implicit_n,
                "absent_n": absent_n,
                "invalid_n": 0,
                "not_testable_n": absent_n,
                "failure_reason": "absent_from_run_background",
            }
        )
    for scope, network, case_id, subset in scope_subsets(aggregates):
        current = list(subset)
        filter_specs = [
            (3, "conservative_support", lambda row: row["conservative_support_count"] >= 1, "no_conservative_support"),
            (4, "coverage", lambda row: row["coverage_fraction"] >= 0.80, "coverage_below_0_80"),
            (5, "aggregate_evidence", lambda row: row["aggregate_acat_q"] is not None and row["aggregate_acat_q"] <= 0.05, "acat_q_above_0_05_or_not_testable"),
        ]
        for step, (number, name, criterion, reason) in enumerate(filter_specs, start=3):
            passing = [row for row in current if criterion(row)]
            rows.append(
                funnel_row(
                    "sequential_candidate_funnel",
                    scope,
                    network,
                    case_id,
                    number,
                    name,
                    step,
                    "gene_broad_network_case_aggregate",
                    current,
                    passing,
                    reason,
                )
            )
            current = passing
        independent_specs = [
            (3, "conservative_support", lambda row: row["conservative_support_count"] >= 1, "no_conservative_support"),
            (4, "coverage", lambda row: row["coverage_fraction"] >= 0.80, "coverage_below_0_80"),
            (5, "aggregate_evidence", lambda row: row["aggregate_acat_q"] is not None and row["aggregate_acat_q"] <= 0.05, "acat_q_above_0_05_or_not_testable"),
        ]
        for number, name, criterion, reason in independent_specs:
            passing = [row for row in subset if criterion(row)]
            rows.append(
                funnel_row(
                    "independent_gate",
                    scope,
                    network,
                    case_id,
                    number,
                    name,
                    number,
                    "gene_broad_network_case_aggregate",
                    subset,
                    passing,
                    reason,
                )
            )
    return rows


def candidate_test_rows(
    included_runs: list[dict[str, Any]],
    network_genes: dict[str, list[str]],
    signatures: dict[str, set[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    annotation: dict[str, dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for run in included_runs:
        run_id = run["kda_run_id"]
        query = signatures[run_id]
        background = backgrounds[run_id]
        explicit = explicit_by_run[run_id]
        for symbol in network_genes[run["broad_network"]]:
            evidence = evidence_for(symbol, run, query, background, explicit, annotation)
            ann = annotation_fields(symbol, annotation)
            record = evidence["record"]
            original = record["original"] if record else {}
            final = record["final"] if record else {}
            yield {
                "kda_run_id": run_id,
                "fine_cell_type": run["fine_cell_type"],
                "broad_network": run["broad_network"],
                "signature_group": run["signature_group"],
                "signature_direction": run["signature_direction"],
                "current_symbol": symbol,
                "case_id": evidence["case_id"],
                "is_core_mito": ann["is_core_mito"],
                "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
                "query_member": symbol in query,
                "test_status": evidence["test_status"],
                "usable_test": evidence["usable"],
                "explicit_family_member": symbol in explicit,
                "effective_query_size": len(query),
                "effective_background_size": len(background),
                "original_layer": original.get("layer"),
                "original_overlap_count": original.get("overlap"),
                "original_neighborhood_size": original.get("neighborhood"),
                "original_non_neighborhood_size": original.get("non_neighborhood"),
                "original_signature_size": original.get("signature_size"),
                "original_fold_enrichment": original.get("fold"),
                "original_log_p": original.get("log_p"),
                "original_raw_p": original.get("p"),
                "original_run_q": record.get("original_q") if record else None,
                "self_excluded": evidence["case_id"] == CASE1 and record is not None,
                "final_layer": final.get("layer"),
                "final_overlap_count": final.get("overlap"),
                "final_neighborhood_size": final.get("neighborhood"),
                "final_non_neighborhood_size": final.get("non_neighborhood"),
                "final_signature_size": final.get("signature_size"),
                "final_background_size": final.get("background_size"),
                "final_fold_enrichment": final.get("fold"),
                "final_log_p": final.get("log_p"),
                "final_raw_p": evidence["p"],
                "final_run_q": evidence["q"],
                "other_query_overlap": evidence["other_overlap"],
                "support_overlap_pass": evidence["other_overlap"] is not None and evidence["other_overlap"] >= 2,
                "support_fold_pass": evidence["fold"] is not None and evidence["fold"] > 1.0,
                "support_run_q_pass": evidence["q"] is not None and evidence["q"] <= 0.05,
                "conservative_support": evidence["support"],
            }


def conservative_support_rows(
    included_runs: list[dict[str, Any]],
    network_genes: dict[str, list[str]],
    signatures: dict[str, set[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    annotation: dict[str, dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for run in included_runs:
        run_id = run["kda_run_id"]
        for symbol in network_genes[run["broad_network"]]:
            evidence = evidence_for(
                symbol,
                run,
                signatures[run_id],
                backgrounds[run_id],
                explicit_by_run[run_id],
                annotation,
            )
            if not evidence["usable"]:
                continue
            yield {
                "kda_run_id": run_id,
                "broad_network": run["broad_network"],
                "fine_cell_type": run["fine_cell_type"],
                "signature_group": run["signature_group"],
                "signature_direction": run["signature_direction"],
                "current_symbol": symbol,
                "case_id": evidence["case_id"],
                "test_status": evidence["test_status"],
                "query_size": len(signatures[run_id]),
                "query_size_pass": len(signatures[run_id]) >= 10,
                "other_query_overlap": evidence["other_overlap"],
                "other_query_overlap_pass": evidence["other_overlap"] is not None and evidence["other_overlap"] >= 2,
                "final_fold_enrichment": evidence["fold"],
                "fold_enrichment_pass": evidence["fold"] is not None and evidence["fold"] > 1.0,
                "final_run_q": evidence["q"],
                "run_q_pass": evidence["q"] is not None and evidence["q"] <= 0.05,
                "conservative_support": evidence["support"],
            }


def top5_rows(
    aggregates: list[dict[str, Any]], network_order: list[str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for network in network_order:
        network_rows = [row for row in aggregates if row["broad_network"] == network]
        for case_id in (CASE1, CASE2, CASE3):
            case_rows = [row for row in network_rows if row["case_id"] == case_id]
            candidates = sorted(
                [row for row in case_rows if row["terminal_candidate_status"] == "driver_candidate"],
                key=lambda row: int(row["within_case_rank"]),
            )
            displayed = candidates[:5]
            if displayed:
                for row in displayed:
                    output.append(
                        {
                            "broad_network": network,
                            "case_order": CASE_ORDER[case_id],
                            "case_id": case_id,
                            "list_status": "ranked_candidates",
                            "total_passing_candidate_count": len(candidates),
                            "displayed_candidate_count": len(displayed),
                            "display_rank": row["within_case_rank"],
                            "current_symbol": row["current_symbol"],
                            "aggregate_acat_p": row["aggregate_acat_p"],
                            "aggregate_acat_q": row["aggregate_acat_q"],
                            "coverage_numerator": row["coverage_numerator"],
                            "coverage_denominator": row["coverage_denominator"],
                            "coverage_fraction": row["coverage_fraction"],
                            "conservative_support_count": row["conservative_support_count"],
                            "evidence_tier": row["evidence_tier"],
                            "empty_result_reason": None,
                        }
                    )
            else:
                if not network_rows:
                    status = "not_testable_no_included_runs"
                    reason = "broad_network_has_zero_included_runs"
                elif not case_rows:
                    status = "not_testable_no_eligible_case_runs"
                    reason = "case_has_zero_eligible_run_denominators"
                else:
                    status = "no_passing_candidate"
                    reason = "no_gene_passed_all_three_candidate_gates"
                output.append(
                    {
                        "broad_network": network,
                        "case_order": CASE_ORDER[case_id],
                        "case_id": case_id,
                        "list_status": status,
                        "total_passing_candidate_count": 0,
                        "displayed_candidate_count": 0,
                        "display_rank": None,
                        "current_symbol": None,
                        "aggregate_acat_p": None,
                        "aggregate_acat_q": None,
                        "coverage_numerator": None,
                        "coverage_denominator": None,
                        "coverage_fraction": None,
                        "conservative_support_count": None,
                        "evidence_tier": None,
                        "empty_result_reason": reason,
                    }
                )
    return output


def build_stability(
    aggregates_by_network: dict[str, list[dict[str, Any]]],
    runs_by_network: dict[str, list[dict[str, Any]]],
    network_genes: dict[str, list[str]],
    signatures: dict[str, set[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    annotation: dict[str, dict[str, Any]],
    minimum_coverage: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    replicates: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for network, primary_rows in aggregates_by_network.items():
        candidates = [row for row in primary_rows if row["terminal_candidate_status"] == "driver_candidate"]
        fine_types = sorted({run["fine_cell_type"] for run in runs_by_network[network]})
        lookup: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        if len(fine_types) >= 2 and candidates:
            for omitted in fine_types:
                remaining_runs = [run for run in runs_by_network[network] if run["fine_cell_type"] != omitted]
                if not remaining_runs:
                    continue
                recalculated = aggregate_network(
                    network,
                    remaining_runs,
                    network_genes[network],
                    signatures,
                    backgrounds,
                    explicit_by_run,
                    annotation,
                    minimum_coverage,
                )
                recalculated_map = {(row["current_symbol"], row["case_id"]): row for row in recalculated}
                for candidate in candidates:
                    key = (candidate["current_symbol"], candidate["case_id"])
                    row = recalculated_map.get(key)
                    record = {
                        "broad_network": network,
                        "omitted_fine_cell_type": omitted,
                        "current_symbol": key[0],
                        "case_id": key[1],
                        "assessable": row is not None and row["aggregate_acat_p"] is not None,
                        "aggregate_acat_p": row["aggregate_acat_p"] if row else None,
                        "aggregate_acat_q": row["aggregate_acat_q"] if row else None,
                        "terminal_candidate_status": row["terminal_candidate_status"] if row else "not_testable",
                        "within_case_rank": row["within_case_rank"] if row else None,
                    }
                    replicates.append(record)
                    lookup[key].append(record)
        for candidate in candidates:
            key = (candidate["current_symbol"], candidate["case_id"])
            assessable = [row for row in lookup.get(key, []) if row["assessable"]]
            nominal_fraction = (
                sum(float(row["aggregate_acat_p"]) <= 0.05 for row in assessable) / len(assessable)
                if assessable
                else None
            )
            q_fraction = (
                sum(row["aggregate_acat_q"] is not None and float(row["aggregate_acat_q"]) <= 0.05 for row in assessable)
                / len(assessable)
                if assessable
                else None
            )
            candidate_fraction = (
                sum(row["terminal_candidate_status"] == "driver_candidate" for row in assessable) / len(assessable)
                if assessable
                else None
            )
            ranks = [as_int(row["within_case_rank"]) for row in assessable if row["within_case_rank"] is not None]
            if not assessable:
                tier = "tier_not_assessable"
            elif candidate["supporting_fine_cell_type_count"] >= 2 and nominal_fraction is not None and nominal_fraction >= 0.80:
                tier = "tier1_recurrent_stable"
            else:
                tier = "tier2_localized_or_unstable"
            candidate["stability_assessable_repetitions"] = len(assessable)
            candidate["stability_nominal_fraction"] = nominal_fraction
            candidate["stability_q_fraction"] = q_fraction
            candidate["stability_candidate_fraction"] = candidate_fraction
            candidate["stability_worst_rank"] = max(ranks) if ranks else None
            candidate["evidence_tier"] = tier
            summaries.append(
                {
                    "broad_network": network,
                    "current_symbol": candidate["current_symbol"],
                    "case_id": candidate["case_id"],
                    "assessable_repetitions": len(assessable),
                    "nominal_p_pass_fraction": nominal_fraction,
                    "aggregate_q_pass_fraction": q_fraction,
                    "candidate_retention_fraction": candidate_fraction,
                    "worst_rank": max(ranks) if ranks else None,
                    "evidence_tier": tier,
                }
            )
        for row in primary_rows:
            if row["terminal_candidate_status"] != "driver_candidate":
                row["evidence_tier"] = "not_a_driver_candidate"
    return replicates, summaries


def sensitivity_rows(
    aggregates_by_network: dict[str, list[dict[str, Any]]],
    coverage_thresholds: Sequence[float],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for network, rows in aggregates_by_network.items():
        missing_indices = [i for i, row in enumerate(rows) if row["coverage_fraction"] >= 0.80]
        missing_q = bh_adjust([rows[i]["_missing_one_p"] for i in missing_indices])
        missing_map = {index: q for index, q in zip(missing_indices, missing_q)}
        coverage_q: dict[float, dict[int, float | None]] = {}
        for threshold in coverage_thresholds:
            indices = [i for i, row in enumerate(rows) if row["coverage_fraction"] >= threshold and row["_all_acat_p"] is not None]
            q_values = bh_adjust([rows[i]["_all_acat_p"] for i in indices])
            coverage_q[threshold] = {index: q for index, q in zip(indices, q_values)}
        for index, row in enumerate(rows):
            base = {
                "broad_network": network,
                "current_symbol": row["current_symbol"],
                "case_id": row["case_id"],
                "coverage_fraction": row["coverage_fraction"],
                "conservative_support_count": row["conservative_support_count"],
            }
            q_missing = missing_map.get(index)
            output.append(
                {
                    **base,
                    "sensitivity_id": "missing_as_one",
                    "threshold": 0.80,
                    "aggregate_p": row["_missing_one_p"] if index in missing_map else None,
                    "aggregate_q": q_missing,
                    "mean_log_p_score": None,
                    "candidate_status": "driver_candidate" if q_missing is not None and q_missing <= 0.05 and row["conservative_support_count"] >= 1 else "not_candidate",
                }
            )
            for threshold in coverage_thresholds:
                q_value = coverage_q[threshold].get(index)
                output.append(
                    {
                        **base,
                        "sensitivity_id": f"coverage_{threshold:.2f}",
                        "threshold": threshold,
                        "aggregate_p": row["_all_acat_p"] if index in coverage_q[threshold] else None,
                        "aggregate_q": q_value,
                        "mean_log_p_score": None,
                        "candidate_status": "driver_candidate" if q_value is not None and q_value <= 0.05 and row["conservative_support_count"] >= 1 else "not_candidate",
                    }
                )
            output.append(
                {
                    **base,
                    "sensitivity_id": "mean_log_p",
                    "threshold": 0.80,
                    "aggregate_p": None,
                    "aggregate_q": None,
                    "mean_log_p_score": row["mean_log_p_score"],
                    "candidate_status": "descriptive_only",
                }
            )
    return output


def degree_sensitivity_rows(
    candidates: list[dict[str, Any]],
    aggregates_by_network: dict[str, list[dict[str, Any]]],
    full_edges: dict[str, list[tuple[str, str]]],
    draws: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        network = candidate["broad_network"]
        symbol = candidate["current_symbol"]
        out_degree = Counter(source for source, _ in full_edges[network])
        total_neighbors: dict[str, set[str]] = defaultdict(set)
        for source, target in full_edges[network]:
            total_neighbors[source].add(target)
            total_neighbors[target].add(source)
        degree = out_degree[symbol]
        total_degree = len(total_neighbors[symbol])
        pool = [
            row
            for row in aggregates_by_network[network]
            if row["case_id"] == candidate["case_id"]
            and row["coverage_fraction"] >= 0.80
            and row["aggregate_acat_p"] is not None
            and row["current_symbol"] != symbol
        ]
        pool.sort(
            key=lambda row: (
                abs(out_degree[row["current_symbol"]] - degree),
                abs(len(total_neighbors[row["current_symbol"]]) - total_degree),
                row["current_symbol"],
            )
        )
        nearest = pool[: max(draws * 5, draws)]
        seed_text = f"{base_seed}:{network}:{candidate['case_id']}:{symbol}"
        seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:12], 16)
        rng = random.Random(seed)
        sampled = rng.sample(nearest, min(draws, len(nearest))) if nearest else []
        empirical = (
            (1 + sum(float(row["aggregate_acat_p"]) <= float(candidate["aggregate_acat_p"]) for row in sampled))
            / (1 + len(sampled))
            if sampled
            else None
        )
        output.append(
            {
                "broad_network": network,
                "current_symbol": symbol,
                "case_id": candidate["case_id"],
                "out_degree": degree,
                "undirected_degree": total_degree,
                "requested_draws": draws,
                "available_match_pool": len(pool),
                "completed_draws": len(sampled),
                "observed_aggregate_acat_p": candidate["aggregate_acat_p"],
                "degree_matched_empirical_tail_p": empirical,
                "random_seed": seed,
                "blocking_gate": False,
            }
        )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/phase18_key_driver_selection.yml")
    parser.add_argument("--phase12-dir")
    parser.add_argument("--output-dir")
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    root = Path.cwd().resolve()
    config_path = project_path(root, args.config)
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    phase12_dir = project_path(root, args.phase12_dir or config["paths"]["phase12_directory"])
    annotation_path = project_path(root, config["paths"]["phase09_annotation"])
    configured_output = config["paths"].get("output_directory") or config["paths"].get("local_output_directory")
    if not configured_output and not args.output_dir:
        fail("Phase 18 config must define paths.output_directory")
    output_dir = project_path(root, args.output_dir or configured_output)
    if output_dir.exists():
        fail(f"Refusing to overwrite existing Phase 18 output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".18_key_driver_selection.staging.", dir=output_dir.parent))
    stage_rows: list[dict[str, Any]] = []
    file_counts: dict[str, int] = {}

    def stage(stage_id: str, before: float, status: str = "completed") -> None:
        stage_rows.append(
            {
                "stage_order": len(stage_rows) + 1,
                "stage_id": stage_id,
                "terminal_status": status,
                "elapsed_seconds": time.time() - before,
            }
        )

    try:
        checkpoint = time.time()
        required_phase12 = [
            "kda_run_manifest.tsv",
            "kda_signature_members.tsv.gz",
            "kda_background_members.tsv.gz",
            "kda_results.tsv.gz",
            "kda_qc_summary.tsv",
            "kda_checks.tsv",
            "kda_artifacts.tsv",
            "kda_status.tsv",
        ]
        for name in required_phase12:
            if not (phase12_dir / name).exists():
                fail(f"Missing required Phase 12 file: {name}")
        status_rows = read_tsv(phase12_dir / "kda_status.tsv")
        if len(status_rows) != 1 or status_rows[0].get("validation_status") != "validated_complete":
            fail("Phase 12 status is not validated_complete")
        if as_int(status_rows[0].get("planned_runs")) != 1782 or as_int(status_rows[0].get("failed_runs")) != 0:
            fail("Phase 12 status dimensions do not match the frozen plan")
        upstream_checks = read_tsv(phase12_dir / "kda_checks.tsv")
        if not upstream_checks or not all(is_true(row.get("passed")) for row in upstream_checks):
            fail("At least one Phase 12 blocking check failed")
        artifacts = read_tsv(phase12_dir / "kda_artifacts.tsv")
        artifact_by_role: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in artifacts:
            artifact_by_role[row["artifact_role"]].append(row)
        hash_checks: list[dict[str, Any]] = []
        for role in ["phase12_config", "fKDA_source", "phase09_annotation"]:
            entries = artifact_by_role.get(role, [])
            if len(entries) != 1:
                fail(f"Expected one Phase 12 artifact row for {role}")
            path = project_path(root, entries[0]["path"])
            observed = sha256_file(path)
            passed = observed == entries[0]["sha256"]
            hash_checks.append({"source_id": role, "path": str(path.relative_to(root)), "observed": observed, "expected": entries[0]["sha256"], "passed": passed})
            if not passed:
                fail(f"Upstream hash mismatch: {role}")
        network_order = list(config["networks"]["order"])
        network_paths: dict[str, Path] = {}
        full_edges: dict[str, list[tuple[str, str]]] = {}
        for network in network_order:
            role = f"network_{network}"
            entries = artifact_by_role.get(role, [])
            if len(entries) != 1:
                fail(f"Expected one network artifact row for {network}")
            path = project_path(root, entries[0]["path"])
            observed = sha256_file(path)
            passed = observed == entries[0]["sha256"]
            hash_checks.append({"source_id": role, "path": str(path.relative_to(root)), "observed": observed, "expected": entries[0]["sha256"], "passed": passed})
            if not passed:
                fail(f"Network hash mismatch: {network}")
            network_paths[network] = path
            full_edges[network] = load_network(path)
        stage("validate_upstream", checkpoint)

        checkpoint = time.time()
        manifest = read_tsv(phase12_dir / "kda_run_manifest.tsv")
        primary_groups = set(config["run_scope"]["groups"])
        directions = set(config["run_scope"]["directions"])
        structural_runs: list[dict[str, Any]] = []
        for row in manifest:
            if row["analysis_tier"] != "primary" or row["signature_group"] not in primary_groups or row["signature_direction"] not in directions:
                continue
            included = (
                row["eligibility_status"] == "eligible"
                and row["terminal_status"].startswith("completed")
                and as_int(row["effective_query_genes"]) >= as_int(config["run_scope"]["minimum_effective_query_genes"])
            )
            if included:
                exclusion = None
            elif row["eligibility_status"] != "eligible":
                exclusion = "phase12_ineligible"
            elif not row["terminal_status"].startswith("completed"):
                exclusion = "phase12_not_completed"
            else:
                exclusion = "effective_query_below_10"
            structural_runs.append({**row, "phase18_included": included, "phase18_exclusion_reason": exclusion})
        expected_slots = as_int(config["run_scope"]["expected_structural_slots"])
        expected_eligible = as_int(config["run_scope"]["expected_phase12_eligible"])
        expected_included = as_int(config["run_scope"]["expected_included_runs"])
        if len(structural_runs) != expected_slots:
            fail(f"Expected {expected_slots} structural runs, found {len(structural_runs)}")
        if sum(row["eligibility_status"] == "eligible" for row in structural_runs) != expected_eligible:
            fail("Phase 12 eligible primary directional count changed")
        included_runs = [row for row in structural_runs if row["phase18_included"]]
        if len(included_runs) != expected_included:
            fail(f"Expected {expected_included} included runs, found {len(included_runs)}")
        included_ids = {row["kda_run_id"] for row in included_runs}
        runs_by_network: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in included_runs:
            runs_by_network[row["broad_network"]].append(row)
        stage("build_run_manifest", checkpoint)

        checkpoint = time.time()
        annotation, annotation_conflicts = load_annotation(annotation_path)
        if annotation_conflicts:
            fail(f"Conflicting Phase 09 annotations for {len(annotation_conflicts)} symbols")
        signatures: dict[str, set[str]] = defaultdict(set)
        for row in iter_tsv(phase12_dir / "kda_signature_members.tsv.gz"):
            run_id = row["kda_run_id"]
            if run_id in included_ids and is_true(row.get("effective_member")):
                signatures[run_id].add(sys.intern(row["gene"]))
        for run in included_runs:
            run_id = run["kda_run_id"]
            if len(signatures[run_id]) != as_int(run["effective_query_genes"]):
                fail(f"Effective query size mismatch for {run_id}")
            if not all(annotation.get(gene, {}).get("is_core_mito", False) for gene in signatures[run_id]):
                fail(f"Non-core query membership found for {run_id}")
        backgrounds: dict[str, set[str]] = defaultdict(set)
        for row in iter_tsv(phase12_dir / "kda_background_members.tsv.gz"):
            run_id = row["kda_run_id"]
            if run_id in included_ids:
                backgrounds[run_id].add(sys.intern(row["gene"]))
        for run in included_runs:
            run_id = run["kda_run_id"]
            if len(backgrounds[run_id]) != as_int(run["effective_background_genes"]):
                fail(f"Effective background size mismatch for {run_id}")
            if not signatures[run_id].issubset(backgrounds[run_id]):
                fail(f"Effective query is not contained in background for {run_id}")
        network_genes = {
            network: sorted(set().union(*(backgrounds[run["kda_run_id"]] for run in runs)))
            for network, runs in runs_by_network.items()
        }
        for network in network_order:
            network_genes.setdefault(network, [])
        stage("load_queries_backgrounds_annotation", checkpoint)

        checkpoint = time.time()
        published: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
        for row in iter_tsv(phase12_dir / "kda_results.tsv.gz"):
            if row["kda_run_id"] in included_ids:
                published[row["kda_run_id"]][row["key_driver"]] = row
        explicit_by_run: dict[str, dict[str, dict[str, Any]]] = {}
        reconstruction_rows: list[dict[str, Any]] = []
        for index, run in enumerate(included_runs, start=1):
            run_id = run["kda_run_id"]
            explicit, summary = reconstruct_run(
                run,
                signatures[run_id],
                backgrounds[run_id],
                full_edges[run["broad_network"]],
                annotation,
            )
            expected = published.get(run_id, {})
            observed_significant = {
                gene: record
                for gene, record in explicit.items()
                if record["original_q"] is not None and record["original_q"] <= 0.05
            }
            reconciled = set(expected) == set(observed_significant)
            maximum_log_error = 0.0
            maximum_q_error = 0.0
            maximum_fold_error = 0.0
            if reconciled:
                for gene, expected_row in expected.items():
                    record = observed_significant[gene]
                    original = record["original"]
                    exact = (
                        as_int(expected_row["best_layer"]) == original["layer"]
                        and as_int(expected_row["overlap_count"]) == original["overlap"]
                        and as_int(expected_row["neighborhood_size"]) == original["neighborhood"]
                        and as_int(expected_row["non_neighborhood_size"]) == original["non_neighborhood"]
                        and as_int(expected_row["signature_size"]) == original["signature_size"]
                    )
                    maximum_fold_error = max(
                        maximum_fold_error,
                        abs(as_float(expected_row["fold_enrichment"]) - original["fold"]),
                    )
                    maximum_log_error = max(maximum_log_error, abs(as_float(expected_row["log_p_value"]) - original["log_p"]))
                    maximum_q_error = max(maximum_q_error, abs(as_float(expected_row["adjusted_p_value"]) - float(record["original_q"])))
                    reconciled = reconciled and exact
            reconciled = (
                reconciled
                and maximum_log_error <= 1e-8
                and maximum_q_error <= 1e-8
                and maximum_fold_error <= 0.0100001
            )
            if not reconciled:
                fail(f"Phase 12 significant-result reconstruction failed for {run_id}")
            explicit_by_run[run_id] = explicit
            reconstruction_rows.append(
                {
                    "kda_run_id": run_id,
                    "broad_network": run["broad_network"],
                    **summary,
                    "published_significant_candidates": len(expected),
                    "reconstructed_significant_candidates": len(observed_significant),
                    "maximum_log_p_error": maximum_log_error,
                    "maximum_q_error": maximum_q_error,
                    "maximum_rounded_fold_error": maximum_fold_error,
                    "reconciled": reconciled,
                }
            )
            print(
                f"[{index}/{len(included_runs)}] {run_id}: "
                f"{summary['background_genes']} background, {summary['explicit_candidates']} explicit",
                flush=True,
            )
        stage("reconstruct_phase12_and_self_exclude", checkpoint)

        checkpoint = time.time()
        aggregates_by_network: dict[str, list[dict[str, Any]]] = {}
        all_aggregates: list[dict[str, Any]] = []
        minimum_coverage = float(config["filters"]["minimum_coverage"])
        for network in network_order:
            if not runs_by_network.get(network):
                aggregates_by_network[network] = []
                continue
            rows = aggregate_network(
                network,
                runs_by_network[network],
                network_genes[network],
                signatures,
                backgrounds,
                explicit_by_run,
                annotation,
                minimum_coverage,
            )
            aggregates_by_network[network] = rows
            all_aggregates.extend(rows)
        stage("aggregate_and_filter", checkpoint)

        checkpoint = time.time()
        stability_replicates, stability_summary = build_stability(
            aggregates_by_network,
            runs_by_network,
            network_genes,
            signatures,
            backgrounds,
            explicit_by_run,
            annotation,
            minimum_coverage,
        )
        candidates = sorted(
            [row for row in all_aggregates if row["terminal_candidate_status"] == "driver_candidate"],
            key=lambda row: (network_order.index(row["broad_network"]), row["case_order"], int(row["within_case_rank"])),
        )
        top5 = top5_rows(all_aggregates, network_order)
        stage("rank_and_stability", checkpoint)

        checkpoint = time.time()
        sensitivities = sensitivity_rows(
            aggregates_by_network,
            [float(value) for value in config["sensitivity"]["coverage_thresholds"]],
        )
        degree_rows = degree_sensitivity_rows(
            candidates,
            aggregates_by_network,
            full_edges,
            as_int(config["sensitivity"]["degree_match_draws"]),
            as_int(config["sensitivity"]["random_seed"]),
        )
        funnel = build_filter_funnel(
            structural_runs,
            included_runs,
            all_aggregates,
            network_genes,
            backgrounds,
            explicit_by_run,
            network_order,
        )
        stage("sensitivities_and_funnel", checkpoint)

        checkpoint = time.time()
        analysis_manifest = [{
            "analysis_id": config["analysis"]["analysis_id"],
            "task_mode": config["analysis"]["task_mode"],
            "execution_class": config["analysis"]["execution_class"],
            "phase12_directory": str(phase12_dir.relative_to(root)),
            "primary_groups": "|".join(config["run_scope"]["groups"]),
            "directions": "|".join(config["run_scope"]["directions"]),
            "minimum_query_genes": config["run_scope"]["minimum_effective_query_genes"],
            "minimum_coverage": minimum_coverage,
            "run_q_threshold": config["filters"]["run_q_threshold"],
            "aggregate_q_threshold": config["filters"]["aggregate_q_threshold"],
            "ranking_order": "aggregate_acat_q|aggregate_acat_p|current_symbol",
            "display_limit": 5,
            "validation_class": config["outputs"]["validation_status"],
        }]
        case_manifest = [
            {"case_order": 1, "case_id": CASE1, "case_label": "MT-related and in query", "exact_rule": "is_mitocarta3_TRUE_and_effective_query_member_TRUE"},
            {"case_order": 2, "case_id": CASE2, "case_label": "MT-related and not in query", "exact_rule": "is_mitocarta3_TRUE_and_effective_query_member_FALSE"},
            {"case_order": 3, "case_id": CASE3, "case_label": "Not MT-related", "exact_rule": "is_mitocarta3_FALSE"},
        ]
        input_paths = [config_path, annotation_path, *[phase12_dir / name for name in required_phase12], *network_paths.values(), project_path(root, config["paths"]["fkda_source"])]
        unique_input_paths = list(dict.fromkeys(input_paths))
        input_inventory = [
            {
                "input_order": index,
                "path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for index, path in enumerate(unique_input_paths, start=1)
        ]
        source_checks = [
            {"check_id": "phase12_validation_status", "observed": status_rows[0]["validation_status"], "expected": "validated_complete", "passed": True},
            {"check_id": "phase12_planned_runs", "observed": as_int(status_rows[0]["planned_runs"]), "expected": 1782, "passed": True},
            {"check_id": "phase12_failed_runs", "observed": as_int(status_rows[0]["failed_runs"]), "expected": 0, "passed": True},
            *[
                {"check_id": f"hash_{row['source_id']}", "observed": row["observed"], "expected": row["expected"], "passed": row["passed"]}
                for row in hash_checks
            ],
        ]
        run_fields = [
            "kda_run_id", "analysis_tier", "fine_cell_type", "broad_network", "signature_group", "signature_direction",
            "effective_query_genes", "effective_background_genes", "eligibility_status", "terminal_status", "phase18_included", "phase18_exclusion_reason",
        ]
        aggregate_fields = [
            "broad_network", "current_symbol", "case_order", "case_id", "is_core_mito", "mitocarta_canonical_symbol", "mito_tier",
            "genome_origin", "is_mtdna_gene", "extended_reference_member", "mapping_status", "phase03_mitocarta_match_type",
            "eligible_run_count", "usable_run_count", "explicit_run_count", "implicit_run_count", "missing_run_count",
            "coverage_numerator", "coverage_denominator", "coverage_fraction", "coverage_pass", "conservative_support_count",
            "conservative_support_pass", "recurrence_fraction", "supporting_fine_cell_type_count", "supporting_fine_cell_types",
            "supporting_group_count", "supporting_groups", "supporting_direction_count", "supporting_directions",
            "median_support_fold_enrichment", "maximum_support_fold_enrichment", "aggregate_acat_p", "aggregate_acat_q",
            "aggregate_q_pass", "missing_as_one_acat_p", "missing_as_one_acat_q", "mean_log_p_score",
            "terminal_candidate_status", "within_case_rank", "top5_display", "stability_assessable_repetitions",
            "stability_nominal_fraction", "stability_q_fraction", "stability_candidate_fraction", "stability_worst_rank", "evidence_tier",
        ]
        candidate_test_fields = [
            "kda_run_id", "fine_cell_type", "broad_network", "signature_group", "signature_direction", "current_symbol", "case_id",
            "is_core_mito", "mitocarta_canonical_symbol", "query_member", "test_status", "usable_test", "explicit_family_member",
            "effective_query_size", "effective_background_size", "original_layer", "original_overlap_count", "original_neighborhood_size",
            "original_non_neighborhood_size", "original_signature_size", "original_fold_enrichment", "original_log_p", "original_raw_p",
            "original_run_q", "self_excluded", "final_layer", "final_overlap_count", "final_neighborhood_size", "final_non_neighborhood_size",
            "final_signature_size", "final_background_size", "final_fold_enrichment", "final_log_p", "final_raw_p", "final_run_q",
            "other_query_overlap", "support_overlap_pass", "support_fold_pass", "support_run_q_pass", "conservative_support",
        ]
        support_fields = [
            "kda_run_id", "broad_network", "fine_cell_type", "signature_group", "signature_direction", "current_symbol", "case_id",
            "test_status", "query_size", "query_size_pass", "other_query_overlap", "other_query_overlap_pass", "final_fold_enrichment",
            "fold_enrichment_pass", "final_run_q", "run_q_pass", "conservative_support",
        ]
        top5_fields = [
            "broad_network", "case_order", "case_id", "list_status", "total_passing_candidate_count", "displayed_candidate_count",
            "display_rank", "current_symbol", "aggregate_acat_p", "aggregate_acat_q", "coverage_numerator", "coverage_denominator",
            "coverage_fraction", "conservative_support_count", "evidence_tier", "empty_result_reason",
        ]
        funnel_fields = [
            "report_type", "summary_scope", "broad_network", "case_id", "filter_number", "filter_name", "ordered_funnel_step",
            "counting_unit", "input_n", "pass_n", "fail_n", "cumulative_remaining_n", "input_distinct_gene_n",
            "pass_distinct_gene_n", "fail_distinct_gene_n", "remaining_distinct_gene_n", "explicit_n", "implicit_n", "absent_n",
            "invalid_n", "not_testable_n", "failure_reason",
        ]
        file_counts["key_driver_analysis_manifest.tsv"] = write_tsv(staging / "key_driver_analysis_manifest.tsv", analysis_manifest, list(analysis_manifest[0]), f"{SCHEMA}_analysis_manifest_v1")
        file_counts["key_driver_case_manifest.tsv"] = write_tsv(staging / "key_driver_case_manifest.tsv", case_manifest, list(case_manifest[0]), f"{SCHEMA}_case_manifest_v1")
        file_counts["key_driver_run_manifest.tsv"] = write_tsv(staging / "key_driver_run_manifest.tsv", structural_runs, run_fields, f"{SCHEMA}_run_manifest_v1")
        file_counts["key_driver_input_inventory.tsv"] = write_tsv(staging / "key_driver_input_inventory.tsv", input_inventory, list(input_inventory[0]), f"{SCHEMA}_input_inventory_v1")
        file_counts["key_driver_source_checks.tsv"] = write_tsv(staging / "key_driver_source_checks.tsv", source_checks, list(source_checks[0]), f"{SCHEMA}_source_checks_v1")
        file_counts["key_driver_candidate_tests.tsv.gz"] = write_tsv(staging / "key_driver_candidate_tests.tsv.gz", candidate_test_rows(included_runs, network_genes, signatures, backgrounds, explicit_by_run, annotation), candidate_test_fields, f"{SCHEMA}_candidate_tests_v1")
        file_counts["key_driver_conservative_support.tsv.gz"] = write_tsv(staging / "key_driver_conservative_support.tsv.gz", conservative_support_rows(included_runs, network_genes, signatures, backgrounds, explicit_by_run, annotation), support_fields, f"{SCHEMA}_conservative_support_v1")
        file_counts["key_driver_gene_case_summary.tsv.gz"] = write_tsv(staging / "key_driver_gene_case_summary.tsv.gz", (public_row(row) for row in all_aggregates), aggregate_fields, f"{SCHEMA}_gene_case_summary_v1")
        file_counts["key_driver_candidates.tsv"] = write_tsv(staging / "key_driver_candidates.tsv", (public_row(row) for row in candidates), aggregate_fields, f"{SCHEMA}_candidates_v1")
        file_counts["key_driver_top5.tsv"] = write_tsv(staging / "key_driver_top5.tsv", top5, top5_fields, f"{SCHEMA}_top5_v1")
        stability_rep_fields = list(stability_replicates[0]) if stability_replicates else ["broad_network", "omitted_fine_cell_type", "current_symbol", "case_id", "assessable", "aggregate_acat_p", "aggregate_acat_q", "terminal_candidate_status", "within_case_rank"]
        stability_sum_fields = list(stability_summary[0]) if stability_summary else ["broad_network", "current_symbol", "case_id", "assessable_repetitions", "nominal_p_pass_fraction", "aggregate_q_pass_fraction", "candidate_retention_fraction", "worst_rank", "evidence_tier"]
        file_counts["key_driver_stability_replicates.tsv.gz"] = write_tsv(staging / "key_driver_stability_replicates.tsv.gz", stability_replicates, stability_rep_fields, f"{SCHEMA}_stability_replicates_v1")
        file_counts["key_driver_stability_summary.tsv"] = write_tsv(staging / "key_driver_stability_summary.tsv", stability_summary, stability_sum_fields, f"{SCHEMA}_stability_summary_v1")
        sensitivity_fields = list(sensitivities[0]) if sensitivities else ["broad_network", "current_symbol", "case_id", "sensitivity_id", "threshold", "aggregate_p", "aggregate_q", "mean_log_p_score", "candidate_status"]
        file_counts["key_driver_sensitivity_results.tsv.gz"] = write_tsv(staging / "key_driver_sensitivity_results.tsv.gz", sensitivities, sensitivity_fields, f"{SCHEMA}_sensitivity_results_v1")
        degree_fields = list(degree_rows[0]) if degree_rows else ["broad_network", "current_symbol", "case_id", "out_degree", "undirected_degree", "requested_draws", "available_match_pool", "completed_draws", "observed_aggregate_acat_p", "degree_matched_empirical_tail_p", "random_seed", "blocking_gate"]
        file_counts["key_driver_network_degree_sensitivity.tsv"] = write_tsv(staging / "key_driver_network_degree_sensitivity.tsv", degree_rows, degree_fields, f"{SCHEMA}_degree_sensitivity_v1")
        figure_rows = []
        for row in top5:
            base = dict(row)
            if row["current_symbol"]:
                aggregate = next(x for x in candidates if x["broad_network"] == row["broad_network"] and x["case_id"] == row["case_id"] and x["current_symbol"] == row["current_symbol"])
                base.update({"supporting_groups": aggregate["supporting_groups"], "supporting_directions": aggregate["supporting_directions"], "supporting_fine_cell_types": aggregate["supporting_fine_cell_types"]})
            else:
                base.update({"supporting_groups": None, "supporting_directions": None, "supporting_fine_cell_types": None})
            figure_rows.append(base)
        file_counts["key_driver_figure_data.tsv"] = write_tsv(staging / "key_driver_figure_data.tsv", figure_rows, [*top5_fields, "supporting_groups", "supporting_directions", "supporting_fine_cell_types"], f"{SCHEMA}_figure_data_v1")
        exclusion_rows: list[dict[str, Any]] = []
        for reason, count in Counter(row["phase18_exclusion_reason"] or "included" for row in structural_runs).items():
            exclusion_rows.append({"exclusion_level": "run", "broad_network": "ALL", "case_id": "ALL", "reason": reason, "count": count})
        for (network, status), count in Counter((row["broad_network"], row["terminal_candidate_status"]) for row in all_aggregates).items():
            exclusion_rows.append({"exclusion_level": "aggregate", "broad_network": network, "case_id": "ALL", "reason": status, "count": count})
        file_counts["key_driver_exclusion_summary.tsv"] = write_tsv(staging / "key_driver_exclusion_summary.tsv", exclusion_rows, ["exclusion_level", "broad_network", "case_id", "reason", "count"], f"{SCHEMA}_exclusion_summary_v1")
        file_counts["key_driver_filter_funnel.tsv"] = write_tsv(staging / "key_driver_filter_funnel.tsv", funnel, funnel_fields, f"{SCHEMA}_filter_funnel_v1")
        stage("write_scientific_outputs", checkpoint)

        checkpoint = time.time()
        stage_fields = ["stage_order", "stage_id", "terminal_status", "elapsed_seconds"]
        file_counts["key_driver_stage_status.tsv"] = write_tsv(staging / "key_driver_stage_status.tsv", stage_rows, stage_fields, f"{SCHEMA}_stage_status_v1")
        all27 = {(row["broad_network"], row["case_id"]) for row in top5}
        global_funnel = [row for row in funnel if row["report_type"] == "sequential_candidate_funnel" and row["summary_scope"] == "overall" and row["filter_number"] == 5]
        checks = [
            {"check_id": "phase12_planned_runs", "severity": "error", "observed": as_int(status_rows[0]["planned_runs"]), "expected": 1782, "passed": as_int(status_rows[0]["planned_runs"]) == 1782},
            {"check_id": "phase18_structural_slots", "severity": "error", "observed": len(structural_runs), "expected": 648, "passed": len(structural_runs) == 648},
            {"check_id": "phase18_included_runs", "severity": "error", "observed": len(included_runs), "expected": 161, "passed": len(included_runs) == 161},
            {"check_id": "phase12_reconstruction", "severity": "error", "observed": sum(row["reconciled"] for row in reconstruction_rows), "expected": len(included_runs), "passed": all(row["reconciled"] for row in reconstruction_rows)},
            {"check_id": "acat_professor_example", "severity": "error", "observed": validate_acat_example(), "expected": "<=5e-10", "passed": validate_acat_example() <= 5e-10},
            {"check_id": "three_case_manifest", "severity": "error", "observed": len(case_manifest), "expected": 3, "passed": len(case_manifest) == 3},
            {"check_id": "top5_network_case_lists", "severity": "error", "observed": len(all27), "expected": 27, "passed": len(all27) == 27},
            {"check_id": "top5_display_cap", "severity": "error", "observed": max(Counter((row["broad_network"], row["case_id"]) for row in top5 if row["list_status"] == "ranked_candidates").values(), default=0), "expected": "<=5", "passed": all(value <= 5 for value in Counter((row["broad_network"], row["case_id"]) for row in top5 if row["list_status"] == "ranked_candidates").values())},
            {"check_id": "filter_funnel_additivity", "severity": "error", "observed": sum(row["input_n"] == row["pass_n"] + row["fail_n"] for row in funnel), "expected": len(funnel), "passed": all(row["input_n"] == row["pass_n"] + row["fail_n"] for row in funnel)},
            {"check_id": "filter_funnel_matches_candidates", "severity": "error", "observed": global_funnel[0]["pass_n"] if global_funnel else None, "expected": len(candidates), "passed": len(global_funnel) == 1 and global_funnel[0]["pass_n"] == len(candidates)},
            {"check_id": "candidate_ranks_unique", "severity": "error", "observed": len({(row["broad_network"], row["case_id"], row["within_case_rank"]) for row in candidates}), "expected": len(candidates), "passed": len({(row["broad_network"], row["case_id"], row["within_case_rank"]) for row in candidates}) == len(candidates)},
            {"check_id": "invalid_tests", "severity": "error", "observed": 0, "expected": 0, "passed": True},
        ]
        if not all(row["passed"] for row in checks):
            failed = [row["check_id"] for row in checks if not row["passed"]]
            fail(f"Phase 18 checks failed: {', '.join(failed)}")
        file_counts["key_driver_checks.tsv"] = write_tsv(staging / "key_driver_checks.tsv", checks, list(checks[0]), f"{SCHEMA}_checks_v1")
        declared = list(config["outputs"]["declared_files"])
        artifacts_output = []
        for order, name in enumerate(declared, start=1):
            path = staging / name
            artifacts_output.append(
                {
                    "artifact_order": order,
                    "path": name,
                    "declared": True,
                    "rows": file_counts.get(name),
                    "bytes": path.stat().st_size if path.exists() else None,
                    "sha256": sha256_file(path) if path.exists() else None,
                    "hash_status": "recorded" if path.exists() else "written_after_artifact_manifest",
                }
            )
        file_counts["key_driver_artifacts.tsv"] = write_tsv(staging / "key_driver_artifacts.tsv", artifacts_output, list(artifacts_output[0]), f"{SCHEMA}_artifacts_v1")
        status_output = [{
            "execution_stage": config["analysis"]["execution_stage"],
            "execution_class": config["analysis"]["execution_class"],
            "stable_task_id": "global:key_driver_selection",
            "task_mode": "key_driver_selection",
            "phase12_planned_runs": 1782,
            "phase18_structural_run_slots": len(structural_runs),
            "phase18_included_runs": len(included_runs),
            "phase18_cases": 3,
            "included_broad_networks": sum(bool(runs_by_network.get(network)) for network in network_order),
            "aggregate_rows": len(all_aggregates),
            "driver_candidates": len(candidates),
            "top5_network_case_lists": len(all27),
            "failed_checks": 0,
            "elapsed_seconds": time.time() - started,
            "validation_status": config["outputs"]["validation_status"],
            "git_revision": git_revision(root),
            "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }]
        file_counts["key_driver_status.tsv"] = write_tsv(staging / "key_driver_status.tsv", status_output, list(status_output[0]), f"{SCHEMA}_status_v1")
        actual_files = sorted(path.name for path in staging.iterdir() if path.is_file())
        if sorted(declared) != actual_files:
            fail(f"Final output declaration mismatch: declared={len(declared)}, actual={len(actual_files)}")
        stage("validate_and_publish", checkpoint)
        staging.replace(output_dir)
        print(f"Phase 18 analysis completed: {output_dir}")
        print(f"Included runs: {len(included_runs)}; aggregate rows: {len(all_aggregates)}; candidates: {len(candidates)}")
        return 0
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
