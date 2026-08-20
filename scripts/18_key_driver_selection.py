#!/usr/bin/env python3
"""Run Phase 18 key-driver selection from validated upstream data.

This is the single Phase 18 entry point. It reads the validated Phase 12
bundle, the recorded Phase 09 annotation, and the recorded Bayesian networks;
reconstructs the complete pre-FDR ``call_key_drivers()`` test table in memory;
and writes only ``call_key_driver_returns.tsv``. It never reads another
Phase 18 result.

The output contains one row for every explicitly tested gene x included run,
not only the rows that passed the original within-run BH threshold. The
original Phase 12 significant return is retained as a Boolean flag and its
published values are copied when available.

Core mitochondrial genes are aggregated as ``mt_driver`` across all included
runs in their broad network. Non-core genes are aggregated as
``non_mt_driver``. MT query-member runs retain conditional self-exclusion.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math
import os
import random
import statistics
import subprocess
import sys
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
CASE_MT = "mt_driver"
CASE_NON_MT = "non_mt_driver"
CASE_ORDER = {CASE_MT: 1, CASE_NON_MT: 2}

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
    return CASE_MT if core else CASE_NON_MT


def requires_self_exclusion(
    symbol: str,
    query: set[str],
    annotation: dict[str, dict[str, Any]],
) -> bool:
    return bool(annotation.get(symbol, {}).get("is_core_mito", False)) and symbol in query


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
        self_excluded = requires_self_exclusion(candidate, query, annotation)
        if self_excluded:
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
            "self_excluded": self_excluded,
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
        case_id = CASE_MT if ann["is_core_mito"] else CASE_NON_MT
        case_runs = {case_id: list(network_runs)}
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
        for case_id in (CASE_MT, CASE_NON_MT):
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
                "self_excluded": bool(record and record.get("self_excluded", False)),
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
        for case_id in (CASE_MT, CASE_NON_MT):
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


GROUP_DETAILS = {
    "F_e2": ("Female", "e2"),
    "F_e33": ("Female", "e33"),
    "F_e4": ("Female", "e4"),
    "M_e2": ("Male", "e2"),
    "M_e33": ("Male", "e33"),
    "M_e4": ("Male", "e4"),
}

CASE_LABELS = {
    CASE_MT: "MT driver",
    CASE_NON_MT: "non-MT driver",
}

TEST_EVIDENCE_FIELDS = """
case_id is_core_mito mitocarta_canonical_symbol query_member test_status
usable_test explicit_family_member original_layer original_overlap_count
original_neighborhood_size original_non_neighborhood_size
original_signature_size original_fold_enrichment original_log_p original_raw_p
original_run_q self_excluded final_layer final_overlap_count
final_neighborhood_size final_non_neighborhood_size final_signature_size
final_background_size final_fold_enrichment final_log_p final_raw_p final_run_q
other_query_overlap support_overlap_pass support_fold_pass support_run_q_pass
conservative_support
""".split()

AGGREGATE_SUMMARY_FIELDS = """
mito_tier genome_origin is_mtdna_gene extended_reference_member mapping_status
phase03_mitocarta_match_type eligible_run_count usable_run_count
explicit_run_count implicit_run_count missing_run_count coverage_numerator
coverage_denominator coverage_fraction coverage_pass conservative_support_count
conservative_support_pass recurrence_fraction supporting_fine_cell_type_count
supporting_fine_cell_types supporting_group_count supporting_groups
supporting_direction_count supporting_directions median_support_fold_enrichment
maximum_support_fold_enrichment aggregate_acat_p aggregate_acat_q
aggregate_q_pass missing_as_one_acat_p missing_as_one_acat_q mean_log_p_score
terminal_candidate_status within_case_rank top5_display
stability_assessable_repetitions stability_nominal_fraction
stability_q_fraction stability_candidate_fraction stability_worst_rank
evidence_tier
""".split()

CALL_RETURN_OUTPUT_FIELDS = """
schema_version kda_run_id fine_cell_type broad_network signature_group sex
apoe_group signature_direction effective_query_genes effective_background_genes
run_terminal_status key_driver tested_by_call_key_drivers
significant_by_call_key_drivers
published_best_layer published_overlap_count published_neighborhood_size
published_non_neighborhood_size published_signature_size
published_fold_enrichment published_log_p_value published_raw_p_value
published_adjusted_p_value published_is_signature published_is_root_node
published_global_key_driver published_overlap_items case_order case_id case_label
is_core_mito mitocarta_canonical_symbol query_member test_status usable_test
explicit_family_member original_layer original_overlap_count
original_neighborhood_size original_non_neighborhood_size
original_signature_size original_fold_enrichment original_log_p original_raw_p
original_run_q self_excluded final_layer final_overlap_count
final_neighborhood_size final_non_neighborhood_size final_signature_size
final_background_size final_fold_enrichment final_log_p final_raw_p final_run_q
other_query_overlap support_overlap_pass support_fold_pass support_run_q_pass
conservative_support mito_tier genome_origin is_mtdna_gene
extended_reference_member mapping_status phase03_mitocarta_match_type
eligible_run_count usable_run_count explicit_run_count implicit_run_count
missing_run_count coverage_numerator coverage_denominator coverage_fraction
coverage_pass conservative_support_count conservative_support_pass
recurrence_fraction supporting_fine_cell_type_count supporting_fine_cell_types
supporting_group_count supporting_groups supporting_direction_count
supporting_directions median_support_fold_enrichment
maximum_support_fold_enrichment aggregate_acat_p aggregate_acat_q
aggregate_q_pass missing_as_one_acat_p missing_as_one_acat_q mean_log_p_score
terminal_candidate_status within_case_rank top5_display
stability_assessable_repetitions stability_nominal_fraction
stability_q_fraction stability_candidate_fraction stability_worst_rank
evidence_tier case_driver_candidate_count case_displayed_candidate_count
""".split()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=root / "config/phase18_key_driver_selection.yml",
        type=Path,
    )
    parser.add_argument("--phase12-dir", type=Path)
    parser.add_argument(
        "--output",
        default=root
        / "results/minerva_production/18_key_driver_selection"
        / "call_key_driver_returns.tsv",
        type=Path,
    )
    return parser.parse_args()


def one_upstream_artifact(
    root: Path,
    artifact_by_role: dict[str, list[dict[str, str]]],
    role: str,
) -> Path:
    rows = artifact_by_role.get(role, [])
    if len(rows) != 1:
        fail(f"Expected one Phase 12 artifact row for {role}")
    path = project_path(root, rows[0]["path"])
    if not path.exists():
        fail(f"Missing upstream artifact for {role}: {path}")
    if sha256_file(path) != rows[0]["sha256"]:
        fail(f"Upstream hash mismatch for {role}: {path}")
    return path


def tested_gene_row(
    run: dict[str, Any],
    symbol: str,
    signatures: dict[str, set[str]],
    backgrounds: dict[str, set[str]],
    explicit_by_run: dict[str, dict[str, dict[str, Any]]],
    annotation: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    run_id = run["kda_run_id"]
    evidence = evidence_for(
        symbol,
        run,
        signatures[run_id],
        backgrounds[run_id],
        explicit_by_run[run_id],
        annotation,
    )
    record = evidence["record"]
    if record is None:
        fail(f"Published driver lacks a reconstructed test: {run_id}/{symbol}")
    original = record["original"]
    final = record["final"]
    ann = annotation_fields(symbol, annotation)
    return {
        "case_id": evidence["case_id"],
        "is_core_mito": ann["is_core_mito"],
        "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
        "query_member": symbol in signatures[run_id],
        "test_status": evidence["test_status"],
        "usable_test": evidence["usable"],
        "explicit_family_member": symbol in explicit_by_run[run_id],
        "original_layer": original["layer"],
        "original_overlap_count": original["overlap"],
        "original_neighborhood_size": original["neighborhood"],
        "original_non_neighborhood_size": original["non_neighborhood"],
        "original_signature_size": original["signature_size"],
        "original_fold_enrichment": original["fold"],
        "original_log_p": original["log_p"],
        "original_raw_p": original["p"],
        "original_run_q": record["original_q"],
        "self_excluded": bool(record.get("self_excluded", False)),
        "final_layer": final["layer"],
        "final_overlap_count": final["overlap"],
        "final_neighborhood_size": final["neighborhood"],
        "final_non_neighborhood_size": final["non_neighborhood"],
        "final_signature_size": final["signature_size"],
        "final_background_size": final["background_size"],
        "final_fold_enrichment": final["fold"],
        "final_log_p": final["log_p"],
        "final_raw_p": evidence["p"],
        "final_run_q": evidence["q"],
        "other_query_overlap": evidence["other_overlap"],
        "support_overlap_pass": evidence["other_overlap"] is not None
        and evidence["other_overlap"] >= 2,
        "support_fold_pass": evidence["fold"] is not None
        and evidence["fold"] > 1.0,
        "support_run_q_pass": evidence["q"] is not None
        and evidence["q"] <= 0.05,
        "conservative_support": evidence["support"],
    }


def validate_published_returns(
    run_id: str,
    published: dict[str, dict[str, str]],
    explicit: dict[str, dict[str, Any]],
) -> None:
    reconstructed = {
        gene: record
        for gene, record in explicit.items()
        if record["original_q"] is not None and record["original_q"] <= 0.05
    }
    if set(published) != set(reconstructed):
        fail(f"Significant-gene reconstruction failed for {run_id}")
    for gene, expected in published.items():
        record = reconstructed[gene]
        original = record["original"]
        exact = (
            as_int(expected["best_layer"]) == original["layer"]
            and as_int(expected["overlap_count"]) == original["overlap"]
            and as_int(expected["neighborhood_size"]) == original["neighborhood"]
            and as_int(expected["non_neighborhood_size"])
            == original["non_neighborhood"]
            and as_int(expected["signature_size"]) == original["signature_size"]
        )
        numeric = (
            abs(as_float(expected["log_p_value"]) - original["log_p"]) <= 1e-8
            and abs(as_float(expected["adjusted_p_value"]) - record["original_q"])
            <= 1e-8
            and abs(as_float(expected["fold_enrichment"]) - original["fold"])
            <= 0.0100001
        )
        if not exact or not numeric:
            fail(f"Published-value reconstruction failed for {run_id}/{gene}")


def run_key_driver_selection() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = project_path(root, args.config)
    output_path = project_path(root, args.output)
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    phase12_dir = project_path(
        root, args.phase12_dir or config["paths"]["phase12_directory"]
    )

    required_phase12 = [
        "kda_run_manifest.tsv",
        "kda_signature_members.tsv.gz",
        "kda_background_members.tsv.gz",
        "kda_results.tsv.gz",
        "kda_checks.tsv",
        "kda_artifacts.tsv",
        "kda_status.tsv",
    ]
    missing = [name for name in required_phase12 if not (phase12_dir / name).exists()]
    if missing:
        fail(f"Missing Phase 12 files: {', '.join(missing)}")
    status = read_tsv(phase12_dir / "kda_status.tsv")
    if len(status) != 1 or status[0].get("validation_status") != "validated_complete":
        fail("Phase 12 is not validated_complete")
    checks = read_tsv(phase12_dir / "kda_checks.tsv")
    if not checks or not all(is_true(row.get("passed")) for row in checks):
        fail("At least one Phase 12 validation check failed")

    artifact_by_role: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in iter_tsv(phase12_dir / "kda_artifacts.tsv"):
        artifact_by_role[row["artifact_role"]].append(row)
    annotation_path = one_upstream_artifact(root, artifact_by_role, "phase09_annotation")
    annotation, conflicts = load_annotation(annotation_path)
    if conflicts:
        fail(f"Conflicting Phase 09 annotations for {len(conflicts)} genes")

    groups = set(config["run_scope"]["groups"])
    directions = set(config["run_scope"]["directions"])
    structural_runs = [
        row
        for row in iter_tsv(phase12_dir / "kda_run_manifest.tsv")
        if row["analysis_tier"] == config["run_scope"]["analysis_tier"]
        and row["signature_group"] in groups
        and row["signature_direction"] in directions
    ]
    if len(structural_runs) != as_int(config["run_scope"]["expected_structural_slots"]):
        fail(f"Expected 648 primary directional runs, found {len(structural_runs)}")
    if sum(row["eligibility_status"] == "eligible" for row in structural_runs) != as_int(
        config["run_scope"]["expected_phase12_eligible"]
    ):
        fail("Upstream eligible-run count changed")
    included_runs = [
        row
        for row in structural_runs
        if row["eligibility_status"] == "eligible"
        and row["terminal_status"].startswith("completed")
        and as_int(row["effective_query_genes"])
        >= as_int(config["run_scope"]["minimum_effective_query_genes"])
    ]
    if len(included_runs) != as_int(config["run_scope"]["expected_included_runs"]):
        fail(f"Expected 161 included runs, found {len(included_runs)}")
    included_ids = {row["kda_run_id"] for row in included_runs}

    signatures: dict[str, set[str]] = defaultdict(set)
    for row in iter_tsv(phase12_dir / "kda_signature_members.tsv.gz"):
        if row["kda_run_id"] in included_ids and is_true(row.get("effective_member")):
            signatures[row["kda_run_id"]].add(sys.intern(row["gene"]))
    backgrounds: dict[str, set[str]] = defaultdict(set)
    for row in iter_tsv(phase12_dir / "kda_background_members.tsv.gz"):
        if row["kda_run_id"] in included_ids:
            backgrounds[row["kda_run_id"]].add(sys.intern(row["gene"]))
    for run in included_runs:
        run_id = run["kda_run_id"]
        if len(signatures[run_id]) != as_int(run["effective_query_genes"]):
            fail(f"Query-size mismatch for {run_id}")
        if len(backgrounds[run_id]) != as_int(run["effective_background_genes"]):
            fail(f"Background-size mismatch for {run_id}")
        if not signatures[run_id].issubset(backgrounds[run_id]):
            fail(f"Query is not contained in the background for {run_id}")

    network_order = list(config["networks"]["order"])
    full_edges = {
        network: load_network(
            one_upstream_artifact(root, artifact_by_role, f"network_{network}")
        )
        for network in network_order
    }
    runs_by_network: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in included_runs:
        runs_by_network[run["broad_network"]].append(run)
    network_genes = {
        network: sorted(
            set().union(*(backgrounds[run["kda_run_id"]] for run in runs))
        )
        for network, runs in runs_by_network.items()
    }
    for network in network_order:
        network_genes.setdefault(network, [])

    published_rows = [
        row
        for row in iter_tsv(phase12_dir / "kda_results.tsv.gz")
        if row["kda_run_id"] in included_ids
    ]
    if len(published_rows) != 1641:
        fail(f"Expected 1,641 significant rows, found {len(published_rows)}")
    if len({(row["kda_run_id"], row["key_driver"]) for row in published_rows}) != 1641:
        fail("Significant returns contain duplicate run/gene keys")
    published_by_run: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in published_rows:
        published_by_run[row["kda_run_id"]][row["key_driver"]] = row

    explicit_by_run: dict[str, dict[str, dict[str, Any]]] = {}
    for index, run in enumerate(included_runs, start=1):
        run_id = run["kda_run_id"]
        explicit, _ = reconstruct_run(
            run,
            signatures[run_id],
            backgrounds[run_id],
            full_edges[run["broad_network"]],
            annotation,
        )
        validate_published_returns(
            run_id, published_by_run.get(run_id, {}), explicit
        )
        explicit_by_run[run_id] = explicit
        if index % 25 == 0 or index == len(included_runs):
            print(f"reconstructed_runs={index}/{len(included_runs)}", flush=True)

    minimum_coverage = float(config["filters"]["minimum_coverage"])
    aggregates_by_network: dict[str, list[dict[str, Any]]] = {}
    all_aggregates: list[dict[str, Any]] = []
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
    build_stability(
        aggregates_by_network,
        runs_by_network,
        network_genes,
        signatures,
        backgrounds,
        explicit_by_run,
        annotation,
        minimum_coverage,
    )
    summary_by_key = {
        (row["broad_network"], row["current_symbol"], row["case_id"]): row
        for row in all_aggregates
    }
    candidate_counts = Counter(
        (row["broad_network"], row["case_id"])
        for row in all_aggregates
        if row["terminal_candidate_status"] == "driver_candidate"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CALL_RETURN_OUTPUT_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        output_row_count = 0
        significant_row_count = 0
        for run in included_runs:
            run_id = run["kda_run_id"]
            sex, apoe_group = GROUP_DETAILS[run["signature_group"]]
            for symbol in sorted(explicit_by_run[run_id]):
                published = published_by_run.get(run_id, {}).get(symbol)
                significant = published is not None
                test = tested_gene_row(
                    run,
                    symbol,
                    signatures,
                    backgrounds,
                    explicit_by_run,
                    annotation,
                )
                case_id = test["case_id"]
                summary = summary_by_key[
                    (run["broad_network"], symbol, case_id)
                ]
                output = {
                    "schema_version": "phase18_call_key_driver_returns_v1",
                    "kda_run_id": run_id,
                    "fine_cell_type": run["fine_cell_type"],
                    "broad_network": run["broad_network"],
                    "signature_group": run["signature_group"],
                    "sex": sex,
                    "apoe_group": apoe_group,
                    "signature_direction": run["signature_direction"],
                    "effective_query_genes": run["effective_query_genes"],
                    "effective_background_genes": run["effective_background_genes"],
                    "run_terminal_status": run["terminal_status"],
                    "key_driver": symbol,
                    "tested_by_call_key_drivers": True,
                    "significant_by_call_key_drivers": significant,
                    "published_best_layer": (
                        published.get("best_layer") if published else None
                    ),
                    "published_overlap_count": (
                        published.get("overlap_count") if published else None
                    ),
                    "published_neighborhood_size": (
                        published.get("neighborhood_size") if published else None
                    ),
                    "published_non_neighborhood_size": (
                        published.get("non_neighborhood_size") if published else None
                    ),
                    "published_signature_size": (
                        published.get("signature_size") if published else None
                    ),
                    "published_fold_enrichment": (
                        published.get("fold_enrichment") if published else None
                    ),
                    "published_log_p_value": (
                        published.get("log_p_value") if published else None
                    ),
                    "published_raw_p_value": (
                        repr(math.exp(float(published["log_p_value"])))
                        if published
                        else None
                    ),
                    "published_adjusted_p_value": (
                        published.get("adjusted_p_value") if published else None
                    ),
                    "published_is_signature": (
                        published.get("is_signature") if published else None
                    ),
                    "published_is_root_node": (
                        published.get("is_root_node") if published else None
                    ),
                    "published_global_key_driver": (
                        published.get("global_key_driver") if published else None
                    ),
                    "published_overlap_items": (
                        published.get("overlap_items") if published else None
                    ),
                    "case_order": CASE_ORDER[case_id],
                    "case_label": CASE_LABELS[case_id],
                    "case_driver_candidate_count": candidate_counts[
                        (run["broad_network"], case_id)
                    ],
                    "case_displayed_candidate_count": min(
                        candidate_counts[(run["broad_network"], case_id)], 5
                    ),
                }
                output.update(
                    {field: test[field] for field in TEST_EVIDENCE_FIELDS}
                )
                output.update(
                    {field: summary[field] for field in AGGREGATE_SUMMARY_FIELDS}
                )
                writer.writerow(
                    {
                        field: display_value(output.get(field))
                        for field in CALL_RETURN_OUTPUT_FIELDS
                    }
                )
                output_row_count += 1
                significant_row_count += int(significant)
    temporary.replace(output_path)

    unique_tested_genes = set().union(
        *(set(rows) for rows in explicit_by_run.values())
    )
    runs_with_tests = {run_id for run_id, rows in explicit_by_run.items() if rows}
    print(f"wrote={output_path}")
    print(f"rows={output_row_count}")
    print(f"significant_rows={significant_row_count}")
    print(f"nonsignificant_rows={output_row_count - significant_row_count}")
    print(f"unique_tested_genes={len(unique_tested_genes)}")
    print(f"runs_with_tests={len(runs_with_tests)}")
    print(f"included_runs={len(included_runs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_key_driver_selection())
