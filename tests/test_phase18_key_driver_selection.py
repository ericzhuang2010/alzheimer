#!/usr/bin/env python3
"""Deterministic unit and output-contract tests for Phase 18."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase18_key_driver_selection",
    ROOT / "scripts" / "18_run_key_driver_selection.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load Phase 18 implementation")
PHASE18 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PHASE18)


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def read(path: Path) -> list[dict[str, str]]:
    return PHASE18.read_tsv(path)


def unit_tests() -> None:
    assert_true(PHASE18.validate_acat_example() <= 5e-10, "ACAT example failed")
    observed = PHASE18.bh_adjust([0.01, 0.04, None, 0.02])
    expected = [0.03, 0.04, None, 0.03]
    assert_true(
        all(
            (left is None and right is None)
            or (left is not None and right is not None and abs(left - right) <= 1e-15)
            for left, right in zip(observed, expected)
        ),
        f"BH fixture failed: {observed}",
    )
    assert_true(PHASE18.acat_combine([1.0, 1.0]) == 1.0, "All-null ACAT failed")
    assert_true(PHASE18.acat_combine([None, None]) is None, "All-missing ACAT failed")
    assert_true(
        PHASE18.classify_case("A", {"A"}, {"A": {"is_core_mito": True}}) == PHASE18.CASE1,
        "Case 1 fixture failed",
    )
    assert_true(
        PHASE18.classify_case("A", set(), {"A": {"is_core_mito": True}}) == PHASE18.CASE2,
        "Case 2 fixture failed",
    )
    assert_true(
        PHASE18.classify_case("B", {"A"}, {"B": {"is_core_mito": False}}) == PHASE18.CASE3,
        "Case 3 fixture failed",
    )
    log_p, p_value, fold = PHASE18.enrichment_statistics(0, 5, 10, 100)
    assert_true(log_p == 0 and p_value == 1 and fold == 0, "Zero-overlap fixture failed")
    adjusted = PHASE18.enrichment_statistics(2, 8, 9, 99)
    assert_true(
        all(math.isfinite(value) for value in adjusted),
        "Self-excluded hypergeometric fixture failed",
    )
    outgoing = {"D": {"A"}, "A": {"B"}, "B": {"C"}}
    layers = PHASE18.directed_layers("D", outgoing)
    assert_true([len(layer) for layer in layers] == [2, 3, 4], "Directed cumulative layers failed")
    print("Phase 18 deterministic unit tests passed")


def validate_output(output: Path) -> None:
    config = PHASE18.yaml.safe_load((ROOT / "config" / "phase18_key_driver_selection.yml").read_text())
    declared = list(config["outputs"]["declared_files"])
    actual = sorted(path.name for path in output.iterdir() if path.is_file())
    assert_true(len(declared) == 21, "Phase 18 must declare exactly 21 outputs")
    assert_true(sorted(declared) == actual, "Output files do not match the declaration")
    for name in declared:
        if name.endswith(".gz"):
            with (output / name).open("rb") as handle:
                assert_true(handle.read(2) == b"\x1f\x8b", f"Declared gzip file is not compressed: {name}")

    status = read(output / "key_driver_status.tsv")
    assert_true(len(status) == 1, "Status must contain one row")
    assert_true(
        status[0]["validation_status"] == config["outputs"]["validation_status"],
        "Status does not match the configured validation status",
    )
    assert_true(
        status[0]["execution_stage"] == config["analysis"]["execution_stage"],
        "Status does not match the configured execution stage",
    )
    assert_true(
        status[0]["execution_class"] == config["analysis"]["execution_class"],
        "Status does not match the configured execution class",
    )
    assert_true(int(status[0]["phase12_planned_runs"]) == 1782, "Phase 12 run count changed")
    assert_true(int(status[0]["phase18_structural_run_slots"]) == 648, "Structural run count changed")
    assert_true(int(status[0]["phase18_included_runs"]) == 161, "Included run count changed")

    checks = read(output / "key_driver_checks.tsv")
    assert_true(checks and all(PHASE18.is_true(row["passed"]) for row in checks), "A blocking check failed")

    case_manifest = read(output / "key_driver_case_manifest.tsv")
    assert_true([row["case_id"] for row in case_manifest] == [PHASE18.CASE1, PHASE18.CASE2, PHASE18.CASE3], "Case order changed")

    runs = read(output / "key_driver_run_manifest.tsv")
    assert_true(len(runs) == 648, "Run manifest must contain 648 rows")
    assert_true(sum(PHASE18.is_true(row["phase18_included"]) for row in runs) == 161, "Run manifest included count changed")

    candidates = read(output / "key_driver_candidates.tsv")
    candidate_keys = set()
    for row in candidates:
        assert_true(row["terminal_candidate_status"] == "driver_candidate", "Noncandidate in candidate table")
        assert_true(float(row["coverage_fraction"]) >= 0.80, "Candidate failed coverage")
        assert_true(int(row["conservative_support_count"]) >= 1, "Candidate failed support")
        assert_true(float(row["aggregate_acat_q"]) <= 0.05, "Candidate failed aggregate q")
        key = (row["broad_network"], row["case_id"], int(row["within_case_rank"]))
        assert_true(key not in candidate_keys, "Candidate ranks are duplicated")
        candidate_keys.add(key)

    top5 = read(output / "key_driver_top5.tsv")
    combinations = {(row["broad_network"], row["case_id"]) for row in top5}
    assert_true(len(combinations) == 27, "Top-five table does not represent all 27 lists")
    displayed_counts = Counter(
        (row["broad_network"], row["case_id"])
        for row in top5
        if row["list_status"] == "ranked_candidates"
    )
    assert_true(all(count <= 5 for count in displayed_counts.values()), "A top-five list exceeds five genes")
    for row in top5:
        if row["list_status"] == "ranked_candidates":
            assert_true(row["current_symbol"] not in {"", "NA"}, "Ranked row lacks a gene")
            assert_true(1 <= int(row["display_rank"]) <= 5, "Display rank is outside 1-5")
        else:
            assert_true(row["current_symbol"] in {"", "NA"}, "Empty-status row contains a gene")

    funnel = read(output / "key_driver_filter_funnel.tsv")
    for row in funnel:
        assert_true(
            int(row["input_n"]) == int(row["pass_n"]) + int(row["fail_n"]),
            f"Funnel row is not additive: {row}",
        )
    final = [
        row
        for row in funnel
        if row["report_type"] == "sequential_candidate_funnel"
        and row["summary_scope"] == "overall"
        and row["filter_number"] == "5"
    ]
    assert_true(len(final) == 1, "Missing global final funnel row")
    assert_true(int(final[0]["pass_n"]) == len(candidates), "Funnel does not end at candidate count")

    artifacts = read(output / "key_driver_artifacts.tsv")
    assert_true(len(artifacts) == 21, "Artifact manifest must declare all 21 files")
    assert_true({row["path"] for row in artifacts} == set(declared), "Artifact paths differ from declaration")
    for row in artifacts:
        if row["hash_status"] == "recorded":
            path = output / row["path"]
            assert_true(int(row["bytes"]) == path.stat().st_size, f"Artifact byte count changed: {path.name}")
            assert_true(row["sha256"] == PHASE18.sha256_file(path), f"Artifact hash changed: {path.name}")
        else:
            assert_true(
                row["path"] in {"key_driver_artifacts.tsv", "key_driver_status.tsv"},
                f"Unexpected unhashed artifact: {row['path']}",
            )
    print(f"Phase 18 output validation passed: {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-output")
    args = parser.parse_args()
    unit_tests()
    if args.validate_output:
        validate_output(Path(args.validate_output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
