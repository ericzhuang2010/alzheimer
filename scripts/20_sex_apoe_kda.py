#!/usr/bin/env python3
"""Run Phase 20 sex/APOE-by-broad-cell non-MT key-driver aggregation.

DEPRECATED (2026-08-29): this coverage/support/ACAT candidate-selection
branch is superseded by the returned-only simple aggregation
(``scripts/20_sex_apoe_kda_simple_aggr.py`` writing
``results/minerva_production/20_sex_apoe_kda_simple_aggr``), which keeps only
genes returned by ``call_key_drivers()`` and ACAT-combines within-call q
values when a gene has two or more returns. The release this script produced
was renamed to ``results/minerva_production/20_sex_apoe_kda (deprecated)``.
The script is retained for provenance only.

The program consumes a validated complete-evidence source reconstructed from
the already completed Phase 12 KDA calls at the configured effective-query
floor.  It does not regenerate differential-expression results or rerun KDA.
Core mitochondrial genes are excluded before category aggregation, BH
correction, ranking, and every Phase 20 result export.
"""

from __future__ import annotations

import argparse
import csv
import gc
import gzip
import hashlib
import math
import os
import shutil
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml
from scipy.stats import cauchy


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
NA_TEXT = "NA"
SCHEMA_ROOT = "phase20_sex_apoe_non_mt_kda_v2"


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def as_float(value: Any) -> float | None:
    if value in (None, "", NA_TEXT):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


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


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    if not path.is_file():
        fail(f"Required file does not exist: {path}")
    with open_text(path, "r") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_tsv(path: Path) -> list[dict[str, str]]:
    return list(iter_tsv(path))


def deterministic_gzip_text(path: Path):
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    import io

    return io.TextIOWrapper(compressed, encoding="utf-8", newline="")


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: Sequence[str],
    schema_version: str,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    connection = (
        deterministic_gzip_text(temporary)
        if path.suffix == ".gz"
        else temporary.open("w", newline="")
    )
    count = 0
    with connection as handle:
        names = ["schema_version", *[name for name in fields if name != "schema_version"]]
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = {name: display_value(row.get(name)) for name in names}
            output["schema_version"] = schema_version
            writer.writerow(output)
            count += 1
    temporary.replace(path)
    return count


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.tmp.{os.getpid()}"
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


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


@dataclass(slots=True)
class EvidenceAccumulator:
    eligible: int = 0
    usable: int = 0
    explicit: int = 0
    implicit: int = 0
    missing: int = 0
    interior_count: int = 0
    interior_stat_sum: float = 0.0
    zero_count: int = 0
    one_count: int = 0
    max_less_than_one: float | None = None
    log_score_sum: float = 0.0
    strict_support: int = 0
    relaxed_support: int = 0
    relaxed_folds: list[float] = field(default_factory=list)
    support_directions: set[str] = field(default_factory=set)

    def add(self, row: dict[str, str]) -> None:
        self.eligible += 1
        usable = is_true(row.get("usable_test"))
        if not usable:
            self.missing += 1
            return
        self.usable += 1
        if row.get("test_status", "").startswith("explicit"):
            self.explicit += 1
        else:
            self.implicit += 1
        p_value = as_float(row.get("final_raw_p"))
        if p_value is None or p_value < 0 or p_value > 1:
            fail(f"Invalid usable frozen P value for {row.get('kda_run_id')}/{row.get('current_symbol')}")
        if p_value == 0:
            self.zero_count += 1
            self.log_score_sum += 300.0
        elif p_value == 1:
            self.one_count += 1
        else:
            self.interior_count += 1
            self.interior_stat_sum += acat_statistic(p_value)
            self.log_score_sum += -math.log10(max(p_value, 1e-300))
            if self.max_less_than_one is None or p_value > self.max_less_than_one:
                self.max_less_than_one = p_value
        if is_true(row.get("conservative_support")):
            self.strict_support += 1
        overlap = as_float(row.get("other_query_overlap"))
        fold_value = as_float(row.get("final_fold_enrichment"))
        run_q = as_float(row.get("final_run_q"))
        relaxed = (
            overlap is not None
            and overlap >= 2
            and fold_value is not None
            and fold_value > 1
            and run_q is not None
            and run_q <= 0.10
        )
        if relaxed:
            self.relaxed_support += 1
            self.relaxed_folds.append(float(fold_value))
            self.support_directions.add(row["signature_direction"])

    @classmethod
    def merge(cls, parts: Iterable["EvidenceAccumulator"]) -> "EvidenceAccumulator":
        result = cls()
        for part in parts:
            result.eligible += part.eligible
            result.usable += part.usable
            result.explicit += part.explicit
            result.implicit += part.implicit
            result.missing += part.missing
            result.interior_count += part.interior_count
            result.interior_stat_sum += part.interior_stat_sum
            result.zero_count += part.zero_count
            result.one_count += part.one_count
            result.log_score_sum += part.log_score_sum
            result.strict_support += part.strict_support
            result.relaxed_support += part.relaxed_support
            result.relaxed_folds.extend(part.relaxed_folds)
            result.support_directions.update(part.support_directions)
            if part.max_less_than_one is not None and (
                result.max_less_than_one is None
                or part.max_less_than_one > result.max_less_than_one
            ):
                result.max_less_than_one = part.max_less_than_one
        return result

    def acat(self, missing_action: str = "omit", tolerance: float = 1e-300) -> float | None:
        if missing_action == "omit":
            total = self.usable
            ones = self.one_count
        elif missing_action == "one":
            total = self.eligible
            ones = self.one_count + self.missing
        else:
            fail(f"Unsupported ACAT missing action: {missing_action}")
        if total == 0:
            return None
        if self.zero_count == 0 and self.interior_count == 0:
            return 1.0
        statistic_sum = self.interior_stat_sum
        zero_value = tolerance
        if self.zero_count:
            statistic_sum += self.zero_count * acat_statistic(zero_value)
        if ones:
            maximum = self.max_less_than_one
            if maximum is None:
                maximum = zero_value
            one_replacement = maximum / 2.0 + 0.5
            statistic_sum += ones * acat_statistic(one_replacement)
        return float(cauchy.sf(statistic_sum / total))

    @property
    def coverage(self) -> float:
        return self.usable / self.eligible if self.eligible else 0.0

    @property
    def mean_log_score(self) -> float | None:
        return self.log_score_sum / self.usable if self.usable else None


@dataclass(slots=True)
class GeneUnit:
    total: EvidenceAccumulator = field(default_factory=EvidenceAccumulator)
    by_fine: dict[str, EvidenceAccumulator] = field(default_factory=dict)

    def add(self, row: dict[str, str]) -> None:
        self.total.add(row)
        fine = row["fine_cell_type"]
        self.by_fine.setdefault(fine, EvidenceAccumulator()).add(row)


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    observed: Any,
    expected: Any,
    passed: bool,
    severity: str = "error",
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "severity": severity,
            "observed": observed,
            "expected": expected,
            "passed": passed,
        }
    )


def validate_sources(
    source_dir: Path,
    config: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Path]:
    inputs = config["inputs"]
    sources = {
        "candidate_tests": source_dir / inputs["candidate_tests"],
        "run_manifest": source_dir / inputs["run_manifest"],
        "source_checks": source_dir / inputs["source_checks"],
        "source_status": source_dir / inputs["source_status"],
        "source_artifacts": source_dir / inputs["source_artifacts"],
    }
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        fail("Missing Phase 20 source inputs: " + ", ".join(missing))
    status = read_tsv(sources["source_status"])
    source_status = status[0].get("validation_status") if len(status) == 1 else "invalid"
    required = inputs["required_source_status"]
    add_check(checks, "source_validation_status", source_status, required, source_status == required)
    source_checks = read_tsv(sources["source_checks"])
    passed = bool(source_checks) and all(is_true(row.get("passed")) for row in source_checks)
    add_check(
        checks,
        "source_blocking_checks",
        sum(not is_true(row.get("passed")) for row in source_checks),
        0,
        passed,
    )
    artifacts = {
        row["path"]: row
        for row in iter_tsv(sources["source_artifacts"])
        if row.get("sha256") not in (None, "", NA_TEXT)
    }
    for name in ("candidate_tests", "run_manifest", "source_checks"):
        path = sources[name]
        recorded = artifacts.get(path.name, {}).get("sha256")
        observed = sha256_file(path)
        add_check(
            checks,
            f"source_recorded_hash_{name}",
            observed,
            recorded or "recorded source hash",
            recorded == observed,
        )
    return sources


def snapshot_inputs(
    sources: dict[str, Path],
    output_dir: Path,
    root: Path,
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    input_dir = output_dir / "00_inputs"
    snapshots = {
        "candidate_tests": input_dir / "phase20_source_candidate_tests.tsv.gz",
        "run_manifest": input_dir / "phase20_source_run_manifest.tsv",
        "source_checks": input_dir / "phase20_source_checks.tsv",
    }
    authority: list[dict[str, Any]] = []
    for role, destination in snapshots.items():
        source = sources[role]
        atomic_copy(source, destination)
        source_hash = sha256_file(source)
        snapshot_hash = sha256_file(destination)
        authority.append(
            {
                "input_role": role,
                "source_path": str(source.relative_to(root)),
                "snapshot_path": str(destination.relative_to(root)),
                "source_schema_version": next(iter_tsv(source)).get("schema_version", NA_TEXT),
                "source_validation_status": "validated_complete",
                "byte_size": source.stat().st_size,
                "sha256": source_hash,
                "copy_identity_pass": source_hash == snapshot_hash,
            }
        )
    return snapshots, authority


def included_runs(
    run_manifest: Path, inclusion_flag: str
) -> list[dict[str, str]]:
    return [row for row in iter_tsv(run_manifest) if is_true(row.get(inclusion_flag))]


def category_manifest(
    runs: list[dict[str, str]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    groups = config["scope"]["groups"]
    networks = config["scope"]["broad_networks"]
    labels = config["scope"]["group_labels"]
    by_category: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in runs:
        by_category[(row["signature_group"], row["broad_network"])].append(row)
    output: list[dict[str, Any]] = []
    for group in groups:
        for network in networks:
            rows = by_category.get((group, network), [])
            fine = sorted({row["fine_cell_type"] for row in rows})
            directions = sorted({row["signature_direction"] for row in rows})
            if not rows:
                status = "not_estimable_no_included_runs"
            elif len(rows) == 1:
                status = "single_run_evidence"
            elif len(fine) == 1:
                status = "localized_single_fine_type"
            else:
                status = "analyzable_multi_fine_type"
            output.append(
                {
                    "signature_group": group,
                    "sex": labels[group]["sex"],
                    "apoe_group": labels[group]["apoe_group"],
                    "broad_network": network,
                    "included_run_count": len(rows),
                    "fine_cell_type_count": len(fine),
                    "fine_cell_types": "|".join(fine),
                    "direction_count": len(directions),
                    "directions": "|".join(directions),
                    "category_status": status,
                    "strict_candidate_count": 0,
                    "relaxed_candidate_count": 0,
                    "exploratory_lead_count": 0,
                    "exploratory_inclusive_count": 0,
                }
            )
    return output


def scan_candidate_tests(
    path: Path,
    eligible_case: str,
) -> tuple[
    dict[tuple[str, str, str], GeneUnit],
    int,
    set[str],
    int,
    int,
]:
    units: dict[tuple[str, str, str], GeneUnit] = {}
    row_count = 0
    run_ids: set[str] = set()
    duplicate_keys = 0
    repeated_run_blocks = 0
    current_run: str | None = None
    closed_runs: set[str] = set()
    previous_key: tuple[str, str] | None = None
    for row in iter_tsv(path):
        row_count += 1
        run_id = row["kda_run_id"]
        key = (run_id, row["current_symbol"])
        duplicate_keys += int(key == previous_key)
        previous_key = key
        if run_id != current_run:
            if current_run is not None:
                closed_runs.add(current_run)
            repeated_run_blocks += int(run_id in closed_runs)
            current_run = run_id
        run_ids.add(run_id)
        if row["case_id"] != eligible_case:
            continue
        if is_true(row.get("is_core_mito")):
            fail(f"Core-MT row mislabeled as {eligible_case}: {row['current_symbol']}")
        key = (row["signature_group"], row["broad_network"], row["current_symbol"])
        units.setdefault(key, GeneUnit()).add(row)
        if row_count % 250000 == 0:
            print(f"candidate_test_rows_scanned={row_count}", flush=True)
    return units, row_count, run_ids, duplicate_keys, repeated_run_blocks


def phase18_status(p_value: float | None, q_value: float | None, coverage: float, support: int) -> str:
    if coverage < 0.80:
        return "insufficient_coverage"
    if p_value is None or q_value is None:
        return "not_testable"
    if q_value <= 0.05 and support >= 1:
        return "driver_candidate"
    if q_value <= 0.05:
        return "aggregate_only"
    if p_value <= 0.05:
        return "exploratory"
    return "not_supported"


def validate_phase18_parity(
    parity: dict[tuple[str, str, str], EvidenceAccumulator],
    archived_summary: Path,
    checks: list[dict[str, Any]],
) -> None:
    calculated: dict[tuple[str, str, str], dict[str, Any]] = {}
    by_network: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (network, gene, case_id), acc in parity.items():
        all_acat_p = acc.acat("omit")
        row = {
            "broad_network": network,
            "current_symbol": gene,
            "case_id": case_id,
            "eligible_run_count": acc.eligible,
            "usable_run_count": acc.usable,
            "explicit_run_count": acc.explicit,
            "implicit_run_count": acc.implicit,
            "missing_run_count": acc.missing,
            "coverage_fraction": acc.coverage,
            "conservative_support_count": acc.strict_support,
            "aggregate_acat_p": all_acat_p if acc.coverage >= 0.80 else None,
            "aggregate_acat_q": None,
            "within_case_rank": None,
            "top5_display": False,
            "_all_acat_p": all_acat_p,
        }
        calculated[(network, gene, case_id)] = row
        by_network[network].append(row)
    for rows in by_network.values():
        eligible = [row for row in rows if row["coverage_fraction"] >= 0.80]
        q_values = bh_adjust([row["_all_acat_p"] for row in eligible])
        for row, q_value in zip(eligible, q_values):
            row["aggregate_acat_q"] = q_value
        for row in rows:
            row["terminal_candidate_status"] = phase18_status(
                row["aggregate_acat_p"],
                row["aggregate_acat_q"],
                row["coverage_fraction"],
                row["conservative_support_count"],
            )
        by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if row["terminal_candidate_status"] == "driver_candidate":
                by_case[row["case_id"]].append(row)
        for case_rows in by_case.values():
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
    archived = {
        (row["broad_network"], row["current_symbol"], row["case_id"]): row
        for row in iter_tsv(archived_summary)
    }
    mismatches = 0
    fields_int = [
        "eligible_run_count",
        "usable_run_count",
        "explicit_run_count",
        "implicit_run_count",
        "missing_run_count",
        "conservative_support_count",
    ]
    for key, expected in archived.items():
        observed = calculated.get(key)
        if observed is None:
            mismatches += 1
            continue
        if any(int(expected[name]) != observed[name] for name in fields_int):
            mismatches += 1
            continue
        for name in ("coverage_fraction", "aggregate_acat_p", "aggregate_acat_q"):
            left = observed.get(name)
            right = as_float(expected.get(name))
            if left is None or right is None:
                equal = left is None and right is None
            else:
                equal = math.isclose(float(left), float(right), rel_tol=1e-11, abs_tol=1e-14)
            if not equal:
                mismatches += 1
                break
        else:
            expected_rank = None if expected["within_case_rank"] == NA_TEXT else int(expected["within_case_rank"])
            if (
                observed["terminal_candidate_status"] != expected["terminal_candidate_status"]
                or observed["within_case_rank"] != expected_rank
                or observed["top5_display"] != is_true(expected["top5_display"])
            ):
                mismatches += 1
    candidates = sum(
        row["terminal_candidate_status"] == "driver_candidate"
        for row in calculated.values()
    )
    top5 = sum(row["top5_display"] for row in calculated.values())
    add_check(checks, "phase18_parity_aggregate_rows", len(calculated), len(archived), len(calculated) == len(archived))
    add_check(checks, "phase18_parity_field_mismatches", mismatches, 0, mismatches == 0)
    add_check(checks, "phase18_parity_candidates", candidates, 109, candidates == 109)
    add_check(checks, "phase18_parity_top5_flags", top5, 63, top5 == 63)


def apply_q(
    rows: list[dict[str, Any]],
    coverage_threshold: float,
    p_field: str,
    q_field: str,
) -> None:
    eligible = [
        row
        for row in rows
        if row["coverage_fraction"] >= coverage_threshold and row[p_field] is not None
    ]
    adjusted = bh_adjust([row[p_field] for row in eligible])
    for row, q_value in zip(eligible, adjusted):
        row[q_field] = q_value


def sort_rank(
    rows: list[dict[str, Any]],
    flag: str,
    q_field: str,
    rank_field: str,
) -> None:
    candidates = [row for row in rows if row[flag]]
    candidates.sort(
        key=lambda row: (
            float(row[q_field]),
            float(row["category_acat_p"]),
            row["current_symbol"],
        )
    )
    for rank, row in enumerate(candidates, start=1):
        row[rank_field] = rank


def aggregate_phase20_units(
    units: dict[tuple[str, str, str], GeneUnit],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    labels = config["scope"]["group_labels"]
    coverage_thresholds = [float(value) for value in config["sensitivity"]["coverage_thresholds"]]
    by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for (group, network, gene), unit in units.items():
        acc = unit.total
        support_fine = sorted(
            fine for fine, fine_acc in unit.by_fine.items() if fine_acc.relaxed_support
        )
        row: dict[str, Any] = {
            "signature_group": group,
            "sex": labels[group]["sex"],
            "apoe_group": labels[group]["apoe_group"],
            "broad_network": network,
            "current_symbol": gene,
            "case_id": config["scope"]["eligible_case_id"],
            "is_core_mito": False,
            "eligible_run_count": acc.eligible,
            "usable_run_count": acc.usable,
            "explicit_run_count": acc.explicit,
            "implicit_run_count": acc.implicit,
            "missing_run_count": acc.missing,
            "coverage_numerator": acc.usable,
            "coverage_denominator": acc.eligible,
            "coverage_fraction": acc.coverage,
            "strict_coverage_pass": acc.coverage >= 0.80,
            "relaxed_coverage_pass": acc.coverage >= 0.50,
            "conservative_support_count": acc.strict_support,
            "relaxed_support_count": acc.relaxed_support,
            "conservative_support_pass": acc.strict_support >= 1,
            "relaxed_support_pass": acc.relaxed_support >= 1,
            "recurrence_fraction": acc.relaxed_support / acc.usable if acc.usable else 0.0,
            "supporting_fine_cell_type_count": len(support_fine),
            "supporting_fine_cell_types": "|".join(support_fine),
            "supporting_direction_count": len(acc.support_directions),
            "supporting_directions": "|".join(sorted(acc.support_directions)),
            "median_support_fold_enrichment": (
                statistics.median(acc.relaxed_folds) if acc.relaxed_folds else None
            ),
            "maximum_support_fold_enrichment": (
                max(acc.relaxed_folds) if acc.relaxed_folds else None
            ),
            "category_acat_p": acc.acat("omit"),
            "relaxed_category_acat_q": None,
            "strict_category_acat_q": None,
            "studywide_acat_q": None,
            "missing_as_one_acat_p": acc.acat("one"),
            "missing_as_one_acat_q": None,
            "mean_log_p_score": acc.mean_log_score,
            "strict_non_mt_reference": False,
            "relaxed_phase20_candidate": False,
            "exploratory_q20": False,
            "exploratory_inclusive": False,
            "terminal_candidate_status": None,
            "strict_rank": None,
            "relaxed_rank": None,
            "exploratory_inclusive_rank": None,
            "top5_summary": False,
            "top10_display": False,
            "stability_assessable_repetitions": 0,
            "stability_nominal_fraction": None,
            "stability_q_fraction": None,
            "stability_candidate_fraction": None,
            "stability_worst_rank": None,
            "evidence_label": None,
            "_unit": unit,
        }
        for threshold in coverage_thresholds:
            row[f"_coverage_q_{threshold:.2f}"] = None
        by_category[(group, network)].append(row)

    for rows in by_category.values():
        for threshold in coverage_thresholds:
            apply_q(
                rows,
                threshold,
                "category_acat_p",
                f"_coverage_q_{threshold:.2f}",
            )
        apply_q(rows, 0.50, "category_acat_p", "relaxed_category_acat_q")
        apply_q(rows, 0.80, "category_acat_p", "strict_category_acat_q")
        apply_q(rows, 0.50, "missing_as_one_acat_p", "missing_as_one_acat_q")

    all_rows = [
        row
        for key in sorted(by_category)
        for row in sorted(by_category[key], key=lambda item: item["current_symbol"])
    ]
    studywide = [
        row
        for row in all_rows
        if row["coverage_fraction"] >= 0.50 and row["category_acat_p"] is not None
    ]
    for row, q_value in zip(
        studywide, bh_adjust([row["category_acat_p"] for row in studywide])
    ):
        row["studywide_acat_q"] = q_value

    for rows in by_category.values():
        for row in rows:
            row["strict_non_mt_reference"] = (
                row["coverage_fraction"] >= 0.80
                and row["conservative_support_count"] >= 1
                and row["strict_category_acat_q"] is not None
                and row["strict_category_acat_q"] <= 0.05
            )
            row["relaxed_phase20_candidate"] = (
                row["coverage_fraction"] >= 0.50
                and row["relaxed_support_count"] >= 1
                and row["relaxed_category_acat_q"] is not None
                and row["relaxed_category_acat_q"] <= 0.10
            )
            row["exploratory_q20"] = (
                row["coverage_fraction"] >= 0.50
                and row["relaxed_support_count"] >= 1
                and row["relaxed_category_acat_q"] is not None
                and 0.10 < row["relaxed_category_acat_q"] <= 0.20
            )
            row["exploratory_inclusive"] = (
                row["relaxed_phase20_candidate"] or row["exploratory_q20"]
            )
            if row["coverage_fraction"] < 0.50:
                status = "insufficient_coverage"
            elif row["category_acat_p"] is None or row["relaxed_category_acat_q"] is None:
                status = "not_testable"
            elif row["relaxed_phase20_candidate"]:
                status = "driver_candidate"
            elif row["exploratory_q20"]:
                status = "exploratory_q20"
            elif row["relaxed_category_acat_q"] <= 0.10:
                status = "aggregate_only"
            elif row["category_acat_p"] <= 0.10:
                status = "nominal_only"
            else:
                status = "not_supported"
            row["terminal_candidate_status"] = status
        sort_rank(rows, "strict_non_mt_reference", "strict_category_acat_q", "strict_rank")
        sort_rank(rows, "relaxed_phase20_candidate", "relaxed_category_acat_q", "relaxed_rank")
        sort_rank(
            rows,
            "exploratory_inclusive",
            "relaxed_category_acat_q",
            "exploratory_inclusive_rank",
        )
        for row in rows:
            rank = row["relaxed_rank"]
            row["top5_summary"] = rank is not None and rank <= 5
            row["top10_display"] = rank is not None and rank <= 10
    return all_rows, by_category


def build_stability(
    by_category: dict[tuple[str, str], list[dict[str, Any]]],
    category_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    category_lookup = {
        (row["signature_group"], row["broad_network"]): row for row in category_rows
    }
    replicates: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for category, rows in by_category.items():
        candidates = [row for row in rows if row["relaxed_phase20_candidate"]]
        manifest = category_lookup[category]
        fine_types = [
            value for value in str(manifest["fine_cell_types"]).split("|") if value
        ]
        candidate_replicates: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if len(fine_types) >= 2:
            for omitted in fine_types:
                replicate_rows: list[dict[str, Any]] = []
                for row in rows:
                    unit: GeneUnit = row["_unit"]
                    acc = EvidenceAccumulator.merge(
                        fine_acc
                        for fine, fine_acc in unit.by_fine.items()
                        if fine != omitted
                    )
                    replicate_rows.append(
                        {
                            "current_symbol": row["current_symbol"],
                            "eligible_run_count": acc.eligible,
                            "usable_run_count": acc.usable,
                            "coverage_fraction": acc.coverage,
                            "aggregate_acat_p": acc.acat("omit"),
                            "aggregate_acat_q": None,
                            "relaxed_support_count": acc.relaxed_support,
                            "candidate": False,
                            "rank": None,
                        }
                    )
                apply_q(
                    replicate_rows,
                    0.50,
                    "aggregate_acat_p",
                    "aggregate_acat_q",
                )
                passing = []
                for item in replicate_rows:
                    item["candidate"] = (
                        item["coverage_fraction"] >= 0.50
                        and item["relaxed_support_count"] >= 1
                        and item["aggregate_acat_q"] is not None
                        and item["aggregate_acat_q"] <= 0.10
                    )
                    if item["candidate"]:
                        passing.append(item)
                passing.sort(
                    key=lambda item: (
                        float(item["aggregate_acat_q"]),
                        float(item["aggregate_acat_p"]),
                        item["current_symbol"],
                    )
                )
                for rank, item in enumerate(passing, start=1):
                    item["rank"] = rank
                replicate_by_gene = {
                    item["current_symbol"]: item for item in replicate_rows
                }
                for candidate in candidates:
                    item = replicate_by_gene[candidate["current_symbol"]]
                    assessable = (
                        item["coverage_fraction"] >= 0.50
                        and item["aggregate_acat_p"] is not None
                        and item["aggregate_acat_q"] is not None
                    )
                    output = {
                        "signature_group": category[0],
                        "broad_network": category[1],
                        "current_symbol": candidate["current_symbol"],
                        "omitted_fine_cell_type": omitted,
                        "remaining_eligible_run_count": item["eligible_run_count"],
                        "remaining_usable_run_count": item["usable_run_count"],
                        "coverage_fraction": item["coverage_fraction"],
                        "assessable": assessable,
                        "aggregate_acat_p": item["aggregate_acat_p"],
                        "aggregate_acat_q": item["aggregate_acat_q"],
                        "relaxed_support_count": item["relaxed_support_count"],
                        "nominal_p_pass": assessable and item["aggregate_acat_p"] <= 0.10,
                        "category_q_pass": assessable and item["aggregate_acat_q"] <= 0.10,
                        "candidate_retained": item["candidate"],
                        "replicate_rank": item["rank"],
                    }
                    replicates.append(output)
                    candidate_replicates[candidate["current_symbol"]].append(output)
        for candidate in candidates:
            observed = [
                row
                for row in candidate_replicates.get(candidate["current_symbol"], [])
                if row["assessable"]
            ]
            nominal_fraction = (
                sum(row["nominal_p_pass"] for row in observed) / len(observed)
                if observed
                else None
            )
            q_fraction = (
                sum(row["category_q_pass"] for row in observed) / len(observed)
                if observed
                else None
            )
            candidate_fraction = (
                sum(row["candidate_retained"] for row in observed) / len(observed)
                if observed
                else None
            )
            ranks = [
                int(row["replicate_rank"])
                for row in observed
                if row["replicate_rank"] is not None
            ]
            worst_rank = max(ranks) if ranks else None
            candidate["stability_assessable_repetitions"] = len(observed)
            candidate["stability_nominal_fraction"] = nominal_fraction
            candidate["stability_q_fraction"] = q_fraction
            candidate["stability_candidate_fraction"] = candidate_fraction
            candidate["stability_worst_rank"] = worst_rank
            if int(manifest["included_run_count"]) == 1:
                evidence_label = "single_run_evidence"
            elif int(manifest["fine_cell_type_count"]) == 1:
                evidence_label = "localized_single_fine_type"
            elif (
                candidate["supporting_fine_cell_type_count"] >= 2
                and nominal_fraction is not None
                and nominal_fraction >= 0.80
            ):
                evidence_label = "recurrent_stable"
            elif candidate["strict_non_mt_reference"]:
                evidence_label = "strict_non_mt_reference"
            else:
                evidence_label = "relaxed_phase20_candidate"
            candidate["evidence_label"] = evidence_label
            summaries.append(
                {
                    "signature_group": category[0],
                    "broad_network": category[1],
                    "current_symbol": candidate["current_symbol"],
                    "assessable_repetitions": len(observed),
                    "nominal_p_pass_fraction": nominal_fraction,
                    "aggregate_q_pass_fraction": q_fraction,
                    "candidate_retention_fraction": candidate_fraction,
                    "worst_rank": worst_rank,
                    "supporting_fine_cell_type_count": candidate[
                        "supporting_fine_cell_type_count"
                    ],
                    "evidence_label": evidence_label,
                }
            )
    return replicates, summaries


def update_category_counts(
    categories: list[dict[str, Any]],
    by_category: dict[tuple[str, str], list[dict[str, Any]]],
) -> None:
    for category in categories:
        rows = by_category.get(
            (category["signature_group"], category["broad_network"]), []
        )
        category["strict_candidate_count"] = sum(
            row["strict_non_mt_reference"] for row in rows
        )
        category["relaxed_candidate_count"] = sum(
            row["relaxed_phase20_candidate"] for row in rows
        )
        category["exploratory_lead_count"] = sum(row["exploratory_q20"] for row in rows)
        category["exploratory_inclusive_count"] = sum(
            row["exploratory_inclusive"] for row in rows
        )


def threshold_grid(
    by_category: dict[tuple[str, str], list[dict[str, Any]]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for coverage in [float(value) for value in config["sensitivity"]["coverage_thresholds"]]:
        q_field = f"_coverage_q_{coverage:.2f}"
        for support_q in [
            float(value) for value in config["sensitivity"]["support_run_q_thresholds"]
        ]:
            support_field = (
                "conservative_support_count" if support_q == 0.05 else "relaxed_support_count"
            )
            for category_q in [
                float(value) for value in config["sensitivity"]["category_q_thresholds"]
            ]:
                counts: list[int] = []
                for rows in by_category.values():
                    count = sum(
                        row["coverage_fraction"] >= coverage
                        and row[support_field] >= 1
                        and row[q_field] is not None
                        and row[q_field] <= category_q
                        for row in rows
                    )
                    if count:
                        counts.append(count)
                candidate_count = sum(counts)
                output.append(
                    {
                        "coverage_threshold": coverage,
                        "support_run_q_threshold": support_q,
                        "category_q_threshold": category_q,
                        "candidate_count": candidate_count,
                        "categories_with_candidate": len(counts),
                        "top5_display_count": sum(min(count, 5) for count in counts),
                        "top10_display_count": sum(min(count, 10) for count in counts),
                    }
                )
    return output


def sensitivity_rows(rows: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for row in rows:
        base = {
            "signature_group": row["signature_group"],
            "broad_network": row["broad_network"],
            "current_symbol": row["current_symbol"],
            "case_id": row["case_id"],
            "is_core_mito": row["is_core_mito"],
            "coverage_fraction": row["coverage_fraction"],
            "relaxed_support_count": row["relaxed_support_count"],
        }
        for threshold in (0.50, 0.80, 1.00):
            q_value = row[f"_coverage_q_{threshold:.2f}"]
            yield {
                **base,
                "sensitivity_id": f"coverage_{threshold:.2f}",
                "threshold": threshold,
                "aggregate_p": (
                    row["category_acat_p"]
                    if row["coverage_fraction"] >= threshold
                    else None
                ),
                "aggregate_q": q_value,
                "candidate_status": (
                    "driver_candidate"
                    if q_value is not None
                    and q_value <= 0.10
                    and row["relaxed_support_count"] >= 1
                    else "not_candidate"
                ),
            }
        yield {
            **base,
            "sensitivity_id": "missing_as_one",
            "threshold": 0.50,
            "aggregate_p": (
                row["missing_as_one_acat_p"]
                if row["coverage_fraction"] >= 0.50
                else None
            ),
            "aggregate_q": row["missing_as_one_acat_q"],
            "candidate_status": (
                "driver_candidate"
                if row["missing_as_one_acat_q"] is not None
                and row["missing_as_one_acat_q"] <= 0.10
                and row["relaxed_support_count"] >= 1
                else "not_candidate"
            ),
        }
        yield {
            **base,
            "sensitivity_id": "studywide_bh",
            "threshold": 0.10,
            "aggregate_p": row["category_acat_p"],
            "aggregate_q": row["studywide_acat_q"],
            "candidate_status": (
                "driver_candidate"
                if row["studywide_acat_q"] is not None
                and row["studywide_acat_q"] <= 0.10
                and row["relaxed_support_count"] >= 1
                else "not_candidate"
            ),
        }


def filter_funnel(
    categories: list[dict[str, Any]],
    by_category: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    scopes = [("overall", "ALL", "ALL", [row for rows in by_category.values() for row in rows])]
    for category in categories:
        key = (category["signature_group"], category["broad_network"])
        scopes.append(("category", key[0], key[1], by_category.get(key, [])))
    for scope, group, network, rows in scopes:
        stages = [
            ("input_non_mt_units", lambda row: True),
            ("coverage_at_least_0_50", lambda row: row["coverage_fraction"] >= 0.50),
            (
                "relaxed_run_support",
                lambda row: row["coverage_fraction"] >= 0.50
                and row["relaxed_support_count"] >= 1,
            ),
            ("category_q_at_most_0_10", lambda row: row["relaxed_phase20_candidate"]),
        ]
        previous = len(rows)
        for order, (stage, predicate) in enumerate(stages, start=1):
            retained = sum(predicate(row) for row in rows)
            output.append(
                {
                    "scope": scope,
                    "signature_group": group,
                    "broad_network": network,
                    "stage_order": order,
                    "stage_id": stage,
                    "input_count": previous,
                    "retained_count": retained,
                    "removed_at_stage": previous - retained,
                }
            )
            previous = retained
    return output


def display_rows(
    categories: list[dict[str, Any]],
    by_category: dict[tuple[str, str], list[dict[str, Any]]],
    limit: int,
    eligible_case: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for category in categories:
        key = (category["signature_group"], category["broad_network"])
        candidates = sorted(
            [
                row
                for row in by_category.get(key, [])
                if row["relaxed_phase20_candidate"]
            ],
            key=lambda row: int(row["relaxed_rank"]),
        )
        if candidates:
            for row in candidates[:limit]:
                output.append({**row, "list_status": "ranked_candidates"})
        else:
            status = (
                "not_estimable_no_included_runs"
                if int(category["included_run_count"]) == 0
                else "no_passing_candidate"
            )
            output.append(
                {
                    "signature_group": key[0],
                    "sex": category["sex"],
                    "apoe_group": category["apoe_group"],
                    "broad_network": key[1],
                    "current_symbol": None,
                    "case_id": eligible_case,
                    "is_core_mito": False,
                    "relaxed_rank": None,
                    "relaxed_category_acat_q": None,
                    "category_acat_p": None,
                    "strict_non_mt_reference": False,
                    "evidence_label": status,
                    "list_status": status,
                }
            )
    return output


def supporting_rows(
    candidate_tests: Path,
    candidate_keys: set[tuple[str, str, str]],
    eligible_case: str,
) -> Iterator[dict[str, Any]]:
    for row in iter_tsv(candidate_tests):
        key = (row["signature_group"], row["broad_network"], row["current_symbol"])
        if key not in candidate_keys or row["case_id"] != eligible_case:
            continue
        overlap = as_float(row.get("other_query_overlap"))
        fold_value = as_float(row.get("final_fold_enrichment"))
        run_q = as_float(row.get("final_run_q"))
        relaxed = (
            overlap is not None
            and overlap >= 2
            and fold_value is not None
            and fold_value > 1
            and run_q is not None
            and run_q <= 0.10
        )
        if not relaxed:
            continue
        yield {
            "signature_group": row["signature_group"],
            "broad_network": row["broad_network"],
            "current_symbol": row["current_symbol"],
            "case_id": row["case_id"],
            "is_core_mito": False,
            "kda_run_id": row["kda_run_id"],
            "fine_cell_type": row["fine_cell_type"],
            "signature_direction": row["signature_direction"],
            "test_status": row["test_status"],
            "other_query_overlap": row["other_query_overlap"],
            "final_fold_enrichment": row["final_fold_enrichment"],
            "final_raw_p": row["final_raw_p"],
            "final_run_q": row["final_run_q"],
            "strict_support": is_true(row.get("conservative_support")),
            "relaxed_support": True,
        }


def direction_summary(
    candidate_tests: Path,
    config: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    labels = config["scope"]["group_labels"]
    eligible_case = config["scope"]["eligible_case_id"]
    for direction in config["scope"]["directions"]:
        units: dict[tuple[str, str, str], EvidenceAccumulator] = {}
        for row in iter_tsv(candidate_tests):
            if row["case_id"] != eligible_case or row["signature_direction"] != direction:
                continue
            key = (row["signature_group"], row["broad_network"], row["current_symbol"])
            units.setdefault(key, EvidenceAccumulator()).add(row)
        by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for (group, network, gene), acc in units.items():
            by_category[(group, network)].append(
                {
                    "signature_group": group,
                    "sex": labels[group]["sex"],
                    "apoe_group": labels[group]["apoe_group"],
                    "broad_network": network,
                    "signature_direction": direction,
                    "current_symbol": gene,
                    "case_id": eligible_case,
                    "is_core_mito": False,
                    "eligible_run_count": acc.eligible,
                    "usable_run_count": acc.usable,
                    "coverage_fraction": acc.coverage,
                    "relaxed_support_count": acc.relaxed_support,
                    "direction_acat_p": acc.acat("omit"),
                    "direction_acat_q": None,
                    "direction_candidate": False,
                }
            )
        for rows in by_category.values():
            apply_q(rows, 0.50, "direction_acat_p", "direction_acat_q")
            for row in rows:
                row["direction_candidate"] = (
                    row["coverage_fraction"] >= 0.50
                    and row["relaxed_support_count"] >= 1
                    and row["direction_acat_q"] is not None
                    and row["direction_acat_q"] <= 0.10
                )
        for key in sorted(by_category):
            for row in sorted(by_category[key], key=lambda item: item["current_symbol"]):
                yield row
        del units
        gc.collect()


AUTHORITY_FIELDS = """
input_role source_path snapshot_path source_schema_version
source_validation_status byte_size sha256 copy_identity_pass
""".split()

CATEGORY_FIELDS = """
signature_group sex apoe_group broad_network included_run_count
fine_cell_type_count fine_cell_types direction_count directions category_status
strict_candidate_count relaxed_candidate_count exploratory_lead_count
exploratory_inclusive_count
""".split()

AGGREGATE_FIELDS = """
signature_group sex apoe_group broad_network current_symbol case_id is_core_mito
eligible_run_count usable_run_count explicit_run_count implicit_run_count
missing_run_count coverage_numerator coverage_denominator coverage_fraction
strict_coverage_pass relaxed_coverage_pass conservative_support_count
relaxed_support_count conservative_support_pass relaxed_support_pass
recurrence_fraction supporting_fine_cell_type_count supporting_fine_cell_types
supporting_direction_count supporting_directions median_support_fold_enrichment
maximum_support_fold_enrichment category_acat_p relaxed_category_acat_q
strict_category_acat_q studywide_acat_q missing_as_one_acat_p
missing_as_one_acat_q mean_log_p_score strict_non_mt_reference
relaxed_phase20_candidate exploratory_q20 exploratory_inclusive
terminal_candidate_status strict_rank relaxed_rank exploratory_inclusive_rank
top5_summary top10_display stability_assessable_repetitions
stability_nominal_fraction stability_q_fraction stability_candidate_fraction
stability_worst_rank evidence_label
""".split()

DISPLAY_FIELDS = [
    *AGGREGATE_FIELDS,
    "list_status",
]

SUPPORT_FIELDS = """
signature_group broad_network current_symbol case_id is_core_mito kda_run_id
fine_cell_type signature_direction test_status other_query_overlap
final_fold_enrichment final_raw_p final_run_q strict_support relaxed_support
""".split()

STABILITY_REPLICATE_FIELDS = """
signature_group broad_network current_symbol omitted_fine_cell_type
remaining_eligible_run_count remaining_usable_run_count coverage_fraction
assessable aggregate_acat_p aggregate_acat_q relaxed_support_count
nominal_p_pass category_q_pass candidate_retained replicate_rank
""".split()

STABILITY_SUMMARY_FIELDS = """
signature_group broad_network current_symbol assessable_repetitions
nominal_p_pass_fraction aggregate_q_pass_fraction candidate_retention_fraction
worst_rank supporting_fine_cell_type_count evidence_label
""".split()

SENSITIVITY_FIELDS = """
signature_group broad_network current_symbol case_id is_core_mito
coverage_fraction relaxed_support_count sensitivity_id threshold aggregate_p
aggregate_q candidate_status
""".split()

DIRECTION_FIELDS = """
signature_group sex apoe_group broad_network signature_direction current_symbol
case_id is_core_mito eligible_run_count usable_run_count coverage_fraction
relaxed_support_count direction_acat_p direction_acat_q direction_candidate
""".split()

GRID_FIELDS = """
coverage_threshold support_run_q_threshold category_q_threshold candidate_count
categories_with_candidate top5_display_count top10_display_count
""".split()

FUNNEL_FIELDS = """
scope signature_group broad_network stage_order stage_id input_count
retained_count removed_at_stage
""".split()

CHECK_FIELDS = "check_id severity observed expected passed".split()

ARTIFACT_FIELDS = """
artifact_order path rows bytes sha256 hash_status
""".split()

STATUS_FIELDS = """
analysis_id execution_stage task_mode source_validation_status included_runs
structural_categories analyzable_categories aggregate_rows strict_candidates
relaxed_candidates exploratory_leads relaxed_categories failed_checks
validation_status git_revision
""".split()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=root / "config/phase20_sex_apoe_kda.yml",
    )
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def run_phase20() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = project_path(root, args.config)
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    output_dir = project_path(
        root, args.output_dir or config["paths"]["output_directory"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    output_counts: dict[str, int | str] = {}

    source_dir = project_path(root, config["paths"]["source_directory"])
    sources = validate_sources(source_dir, config, checks)
    if any(
        row["severity"] == "error" and not row["passed"] for row in checks
    ):
        fail("Phase 20 source authority validation failed")
    snapshots, authority = snapshot_inputs(sources, output_dir, root)
    atomic_copy(config_path, output_dir / "phase20_config_snapshot.yml")
    authority_path = output_dir / "00_inputs/phase20_source_input_authority.tsv"
    output_counts[relative_or_absolute(authority_path, output_dir)] = write_tsv(
        authority_path,
        authority,
        AUTHORITY_FIELDS,
        f"{SCHEMA_ROOT}_input_authority_v1",
    )
    for row in authority:
        add_check(
            checks,
            f"input_snapshot_identity_{row['input_role']}",
            row["copy_identity_pass"],
            True,
            bool(row["copy_identity_pass"]),
        )

    expected = config["inputs"]
    runs = included_runs(
        snapshots["run_manifest"], expected["inclusion_flag"]
    )
    categories = category_manifest(runs, config)
    add_check(
        checks,
        "included_run_count",
        len(runs),
        int(expected["expected_included_runs"]),
        len(runs) == int(expected["expected_included_runs"]),
    )
    observed_query_floor = min(int(row["effective_query_genes"]) for row in runs)
    expected_query_floor = int(expected["minimum_effective_query_genes"])
    add_check(
        checks,
        "minimum_effective_query_genes",
        observed_query_floor,
        expected_query_floor,
        observed_query_floor == expected_query_floor,
    )
    add_check(
        checks,
        "structural_category_count",
        len(categories),
        int(config["scope"]["expected_structural_categories"]),
        len(categories) == int(config["scope"]["expected_structural_categories"]),
    )
    analyzable_count = sum(int(row["included_run_count"]) > 0 for row in categories)
    empty_count = sum(int(row["included_run_count"]) == 0 for row in categories)
    add_check(
        checks,
        "analyzable_category_count",
        analyzable_count,
        int(config["scope"]["expected_analyzable_categories"]),
        analyzable_count == int(config["scope"]["expected_analyzable_categories"]),
    )
    add_check(
        checks,
        "empty_category_count",
        empty_count,
        int(config["scope"]["expected_empty_categories"]),
        empty_count == int(config["scope"]["expected_empty_categories"]),
    )
    add_check(
        checks,
        "category_run_count_sum",
        sum(int(row["included_run_count"]) for row in categories),
        len(runs),
        sum(int(row["included_run_count"]) for row in categories) == len(runs),
    )

    (
        units,
        test_row_count,
        test_run_ids,
        duplicate_test_keys,
        repeated_run_blocks,
    ) = scan_candidate_tests(
        snapshots["candidate_tests"], config["scope"]["eligible_case_id"]
    )
    add_check(
        checks,
        "candidate_test_row_count",
        test_row_count,
        int(expected["expected_candidate_test_rows"]),
        test_row_count == int(expected["expected_candidate_test_rows"]),
    )
    included_ids = {row["kda_run_id"] for row in runs}
    add_check(
        checks,
        "candidate_test_run_set",
        len(test_run_ids),
        len(included_ids),
        test_run_ids == included_ids,
    )
    add_check(
        checks,
        "candidate_test_duplicate_run_gene_keys",
        duplicate_test_keys,
        0,
        duplicate_test_keys == 0,
    )
    add_check(
        checks,
        "candidate_test_repeated_run_blocks",
        repeated_run_blocks,
        0,
        repeated_run_blocks == 0,
    )
    gc.collect()
    print("source_evidence_scan_complete=TRUE", flush=True)

    aggregates, by_category = aggregate_phase20_units(units, config)
    stability_replicates, stability_summaries = build_stability(
        by_category, categories
    )
    update_category_counts(categories, by_category)
    grid = threshold_grid(by_category, config)
    funnel = filter_funnel(categories, by_category)

    relaxed = [row for row in aggregates if row["relaxed_phase20_candidate"]]
    strict = [row for row in aggregates if row["strict_non_mt_reference"]]
    exploratory = [row for row in aggregates if row["exploratory_q20"]]
    inclusive = [row for row in aggregates if row["exploratory_inclusive"]]
    relaxed.sort(
        key=lambda row: (
            config["scope"]["groups"].index(row["signature_group"]),
            config["scope"]["broad_networks"].index(row["broad_network"]),
            int(row["relaxed_rank"]),
        )
    )
    strict.sort(
        key=lambda row: (
            config["scope"]["groups"].index(row["signature_group"]),
            config["scope"]["broad_networks"].index(row["broad_network"]),
            int(row["strict_rank"]),
        )
    )
    exploratory.sort(
        key=lambda row: (
            config["scope"]["groups"].index(row["signature_group"]),
            config["scope"]["broad_networks"].index(row["broad_network"]),
            float(row["relaxed_category_acat_q"]),
            row["current_symbol"],
        )
    )
    eligible_case = config["scope"]["eligible_case_id"]
    top10 = display_rows(categories, by_category, 10, eligible_case)
    top5 = display_rows(categories, by_category, 5, eligible_case)
    expected_results = config["expected_results"]
    metrics = {
        "aggregate_rows": len(aggregates),
        "strict_candidates": len(strict),
        "strict_top5": sum(row["strict_rank"] is not None and row["strict_rank"] <= 5 for row in strict),
        "strict_top10": sum(row["strict_rank"] is not None and row["strict_rank"] <= 10 for row in strict),
        "strict_categories": len({(row["signature_group"], row["broad_network"]) for row in strict}),
        "relaxed_candidates": len(relaxed),
        "relaxed_top5": sum(row["top5_summary"] for row in relaxed),
        "relaxed_top10": sum(row["top10_display"] for row in relaxed),
        "relaxed_categories": len({(row["signature_group"], row["broad_network"]) for row in relaxed}),
        "exploratory_inclusive_candidates": len(inclusive),
        "exploratory_only_candidates": len(exploratory),
        "exploratory_inclusive_top5": sum(
            row["exploratory_inclusive_rank"] <= 5 for row in inclusive
        ),
        "exploratory_inclusive_top10": sum(
            row["exploratory_inclusive_rank"] <= 10 for row in inclusive
        ),
        "exploratory_inclusive_categories": len(
            {(row["signature_group"], row["broad_network"]) for row in inclusive}
        ),
    }
    for name, observed in metrics.items():
        if name == "aggregate_rows":
            target = int(expected["expected_aggregate_rows"])
        else:
            target = int(expected_results[name])
        add_check(checks, name, observed, target, observed == target)

    non_mt_pass = all(
        row["case_id"] == config["scope"]["eligible_case_id"]
        and row["is_core_mito"] is False
        for row in aggregates
    )
    add_check(checks, "non_mt_only_aggregate_rows", non_mt_pass, True, non_mt_pass)
    unique_keys = {
        (row["signature_group"], row["broad_network"], row["current_symbol"])
        for row in aggregates
    }
    add_check(
        checks,
        "aggregate_unit_uniqueness",
        len(unique_keys),
        len(aggregates),
        len(unique_keys) == len(aggregates),
    )
    category_run_counts = {
        (row["signature_group"], row["broad_network"]): int(row["included_run_count"])
        for row in categories
    }
    denominator_pass = all(
        row["eligible_run_count"]
        == category_run_counts[(row["signature_group"], row["broad_network"])]
        for row in aggregates
    )
    add_check(
        checks,
        "category_denominator_matches_manifest",
        denominator_pass,
        True,
        denominator_pass,
    )
    rank_pass = all(
        len(
            {
                row["relaxed_rank"]
                for row in rows
                if row["relaxed_phase20_candidate"]
            }
        )
        == sum(row["relaxed_phase20_candidate"] for row in rows)
        for rows in by_category.values()
    )
    add_check(checks, "candidate_ranks_unique", rank_pass, True, rank_pass)
    add_check(
        checks,
        "top10_display_cap",
        max(
            Counter(
                (row["signature_group"], row["broad_network"])
                for row in top10
                if row["current_symbol"] is not None
            ).values(),
            default=0,
        ),
        "<=10",
        all(
            value <= 10
            for value in Counter(
                (row["signature_group"], row["broad_network"])
                for row in top10
                if row["current_symbol"] is not None
            ).values()
        ),
    )

    category_path = output_dir / "phase20_category_manifest.tsv"
    output_counts[category_path.name] = write_tsv(
        category_path, categories, CATEGORY_FIELDS, f"{SCHEMA_ROOT}_category_manifest_v1"
    )
    aggregate_path = output_dir / "phase20_driver_aggregates.tsv.gz"
    output_counts[aggregate_path.name] = write_tsv(
        aggregate_path, aggregates, AGGREGATE_FIELDS, f"{SCHEMA_ROOT}_aggregates_v1"
    )
    for name, rows, schema in (
        ("phase20_relaxed_candidates.tsv", relaxed, "relaxed_candidates"),
        ("phase20_strict_non_mt_reference_candidates.tsv", strict, "strict_reference"),
        ("phase20_exploratory_leads.tsv", exploratory, "exploratory_leads"),
    ):
        path = output_dir / name
        output_counts[name] = write_tsv(
            path, rows, AGGREGATE_FIELDS, f"{SCHEMA_ROOT}_{schema}_v1"
        )
    top10_path = output_dir / "phase20_top10.tsv"
    output_counts[top10_path.name] = write_tsv(
        top10_path, top10, DISPLAY_FIELDS, f"{SCHEMA_ROOT}_top10_v1"
    )
    top5_path = output_dir / "phase20_top5_summary.tsv"
    output_counts[top5_path.name] = write_tsv(
        top5_path, top5, DISPLAY_FIELDS, f"{SCHEMA_ROOT}_top5_summary_v1"
    )
    support_path = output_dir / "phase20_conservative_support.tsv.gz"
    candidate_keys = {
        (row["signature_group"], row["broad_network"], row["current_symbol"])
        for row in relaxed
    }
    output_counts[support_path.name] = write_tsv(
        support_path,
        supporting_rows(
            snapshots["candidate_tests"], candidate_keys, eligible_case
        ),
        SUPPORT_FIELDS,
        f"{SCHEMA_ROOT}_support_v1",
    )
    expected_support_rows = sum(int(row["relaxed_support_count"]) for row in relaxed)
    add_check(
        checks,
        "support_export_row_count",
        output_counts[support_path.name],
        expected_support_rows,
        output_counts[support_path.name] == expected_support_rows,
    )
    stability_rep_path = output_dir / "phase20_stability_replicates.tsv.gz"
    output_counts[stability_rep_path.name] = write_tsv(
        stability_rep_path,
        stability_replicates,
        STABILITY_REPLICATE_FIELDS,
        f"{SCHEMA_ROOT}_stability_replicates_v1",
    )
    stability_summary_path = output_dir / "phase20_stability_summary.tsv"
    output_counts[stability_summary_path.name] = write_tsv(
        stability_summary_path,
        stability_summaries,
        STABILITY_SUMMARY_FIELDS,
        f"{SCHEMA_ROOT}_stability_summary_v1",
    )
    sensitivity_path = output_dir / "phase20_sensitivity_results.tsv.gz"
    output_counts[sensitivity_path.name] = write_tsv(
        sensitivity_path,
        sensitivity_rows(aggregates),
        SENSITIVITY_FIELDS,
        f"{SCHEMA_ROOT}_sensitivity_v1",
    )
    direction_path = output_dir / "phase20_direction_summary.tsv.gz"
    output_counts[direction_path.name] = write_tsv(
        direction_path,
        direction_summary(snapshots["candidate_tests"], config),
        DIRECTION_FIELDS,
        f"{SCHEMA_ROOT}_direction_summary_v1",
    )
    grid_path = output_dir / "phase20_threshold_grid.tsv"
    output_counts[grid_path.name] = write_tsv(
        grid_path, grid, GRID_FIELDS, f"{SCHEMA_ROOT}_threshold_grid_v1"
    )
    funnel_path = output_dir / "phase20_filter_funnel.tsv"
    output_counts[funnel_path.name] = write_tsv(
        funnel_path, funnel, FUNNEL_FIELDS, f"{SCHEMA_ROOT}_filter_funnel_v1"
    )

    checks_path = output_dir / "phase20_checks.tsv"
    output_counts[checks_path.name] = write_tsv(
        checks_path, checks, CHECK_FIELDS, f"{SCHEMA_ROOT}_checks_v1"
    )
    snapshot_counts = {
        "00_inputs/phase20_source_candidate_tests.tsv.gz": test_row_count,
        "00_inputs/phase20_source_run_manifest.tsv": sum(1 for _ in iter_tsv(snapshots["run_manifest"])),
        "00_inputs/phase20_source_checks.tsv": sum(1 for _ in iter_tsv(snapshots["source_checks"])),
        "00_inputs/phase20_source_input_authority.tsv": len(authority),
        "phase20_config_snapshot.yml": "NA",
    }
    all_counts = {**snapshot_counts, **output_counts}
    artifact_rows: list[dict[str, Any]] = []
    artifact_names = [
        "00_inputs/phase20_source_candidate_tests.tsv.gz",
        "00_inputs/phase20_source_run_manifest.tsv",
        "00_inputs/phase20_source_input_authority.tsv",
        "00_inputs/phase20_source_checks.tsv",
        "phase20_category_manifest.tsv",
        "phase20_driver_aggregates.tsv.gz",
        "phase20_relaxed_candidates.tsv",
        "phase20_strict_non_mt_reference_candidates.tsv",
        "phase20_exploratory_leads.tsv",
        "phase20_top10.tsv",
        "phase20_top5_summary.tsv",
        "phase20_conservative_support.tsv.gz",
        "phase20_stability_replicates.tsv.gz",
        "phase20_stability_summary.tsv",
        "phase20_sensitivity_results.tsv.gz",
        "phase20_direction_summary.tsv.gz",
        "phase20_threshold_grid.tsv",
        "phase20_filter_funnel.tsv",
        "phase20_checks.tsv",
        "phase20_config_snapshot.yml",
    ]
    for order, name in enumerate(artifact_names, start=1):
        path = output_dir / name
        artifact_rows.append(
            {
                "artifact_order": order,
                "path": name,
                "rows": all_counts.get(name, "NA"),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    artifacts_path = output_dir / "phase20_artifacts.tsv"
    write_tsv(
        artifacts_path,
        artifact_rows,
        ARTIFACT_FIELDS,
        f"{SCHEMA_ROOT}_artifacts_v1",
    )

    failed_checks = sum(
        row["severity"] == "error" and not row["passed"] for row in checks
    )
    validation_status = "validated_complete" if failed_checks == 0 else "validation_failed"
    status_row = {
        "analysis_id": config["analysis"]["analysis_id"],
        "execution_stage": config["analysis"]["execution_stage"],
        "task_mode": config["analysis"]["task_mode"],
        "source_validation_status": "validated_complete",
        "included_runs": len(runs),
        "structural_categories": len(categories),
        "analyzable_categories": analyzable_count,
        "aggregate_rows": len(aggregates),
        "strict_candidates": len(strict),
        "relaxed_candidates": len(relaxed),
        "exploratory_leads": len(exploratory),
        "relaxed_categories": metrics["relaxed_categories"],
        "failed_checks": failed_checks,
        "validation_status": validation_status,
        "git_revision": git_revision(root),
    }
    status_path = output_dir / "phase20_status.tsv"
    write_tsv(status_path, [status_row], STATUS_FIELDS, f"{SCHEMA_ROOT}_status_v1")

    print(f"wrote={output_dir}")
    print(f"aggregate_rows={len(aggregates)}")
    print(f"strict_candidates={len(strict)}")
    print(f"relaxed_candidates={len(relaxed)}")
    print(f"exploratory_leads={len(exploratory)}")
    print(f"relaxed_categories={metrics['relaxed_categories']}")
    print(f"validation_status={validation_status}")
    return 0 if validation_status == "validated_complete" else 1


if __name__ == "__main__":
    raise SystemExit(run_phase20())
