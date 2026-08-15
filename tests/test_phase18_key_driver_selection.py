#!/usr/bin/env python3
"""Deterministic unit and output-contract tests for Phase 18."""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase18_key_driver_selection",
    ROOT / "scripts" / "18_export_significant_returns.py",
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
    assert_true(
        declared == ["key_driver_significant_returns.tsv"],
        "Phase 18 must declare only the significant-return table",
    )
    path = output / declared[0] if output.is_dir() else output
    assert_true(path.is_file(), f"Missing Phase 18 output: {path}")

    rows = read(path)
    assert_true(len(rows) == 1641, "Significant-return row count changed")
    assert_true(
        set(rows[0]) == set(PHASE18.SIGNIFICANT_OUTPUT_FIELDS),
        "Significant-return columns do not match the schema",
    )
    assert_true(
        len(rows[0]) == len(PHASE18.SIGNIFICANT_OUTPUT_FIELDS) == 103,
        "Significant-return column count changed",
    )

    row_keys = {(row["kda_run_id"], row["key_driver"]) for row in rows}
    assert_true(len(row_keys) == len(rows), "Run-by-gene rows are duplicated")
    assert_true(len({row["kda_run_id"] for row in rows}) == 122, "Nonempty run count changed")
    assert_true(len({row["key_driver"] for row in rows}) == 295, "Returned-gene count changed")
    assert_true(
        {row["case_id"] for row in rows} == {PHASE18.CASE1, PHASE18.CASE2, PHASE18.CASE3},
        "The three Phase 18 cases are not all represented",
    )
    assert_true(
        all(PHASE18.is_true(row["returned_by_call_key_drivers"]) for row in rows),
        "The output contains a gene not returned by call_key_drivers",
    )
    assert_true(
        all(float(row["published_adjusted_p_value"]) <= 0.05 for row in rows),
        "The output contains a nonsignificant returned gene",
    )
    assert_true(
        all(int(row["effective_query_genes"]) >= 10 for row in rows),
        "The output contains a run with fewer than 10 effective query genes",
    )
    assert_true(
        all(row["run_terminal_status"] == "completed_significant" for row in rows),
        "The output contains a non-significant run status",
    )
    print(f"Phase 18 significant-return validation passed: {path}")


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
