#!/usr/bin/env python3
"""Deterministic unit and output-contract tests for Phase 20."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase20_sex_apoe_kda",
    ROOT / "scripts" / "20_sex_apoe_kda.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load Phase 20 implementation")
PHASE20 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PHASE20
SPEC.loader.exec_module(PHASE20)


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def fixture_row(p_value: str, *, usable: bool = True) -> dict[str, str]:
    return {
        "kda_run_id": "fixture",
        "current_symbol": "GENE",
        "usable_test": "TRUE" if usable else "FALSE",
        "test_status": "explicit_test" if usable else "absent_from_background",
        "final_raw_p": p_value if usable else "NA",
        "final_run_q": "0.04" if usable else "NA",
        "final_fold_enrichment": "2",
        "other_query_overlap": "2",
        "conservative_support": "TRUE" if usable else "FALSE",
        "signature_direction": "AD_up_mito",
    }


def unit_tests() -> None:
    observed = PHASE20.bh_adjust([0.01, 0.04, None, 0.02])
    expected = [0.03, 0.04, None, 0.03]
    assert_true(
        all(
            (left is None and right is None)
            or (
                left is not None
                and right is not None
                and abs(left - right) <= 1e-15
            )
            for left, right in zip(observed, expected)
        ),
        f"BH fixture failed: {observed}",
    )
    phase18_examples = [
        (
            [0.5746569, 0.7090122, 0.7965851, 0.1149619],
            0.4768092003,
        ),
        (
            [0.6513363, 0.6671072, 0.5985140, 0.4991580],
            0.6079561876,
        ),
        (
            [0.1632148, 0.9312446, 0.9105127, 0.2293418],
            0.7884404860,
        ),
    ]
    for p_values, target in phase18_examples:
        acc = PHASE20.EvidenceAccumulator()
        for p_value in p_values:
            acc.add(fixture_row(str(p_value)))
        assert_true(
            math.isclose(acc.acat("omit"), target, rel_tol=0, abs_tol=5e-10),
            f"ACAT fixture failed for {p_values}: {acc.acat('omit')}",
        )
    acc = PHASE20.EvidenceAccumulator()
    acc.add(fixture_row("1"))
    acc.add(fixture_row("NA", usable=False))
    assert_true(acc.acat("omit") == 1.0, "All-null omit ACAT failed")
    assert_true(acc.acat("one") == 1.0, "All-null missing-as-one ACAT failed")
    left = PHASE20.EvidenceAccumulator()
    right = PHASE20.EvidenceAccumulator()
    left.add(fixture_row("0.01"))
    right.add(fixture_row("0.5"))
    merged = PHASE20.EvidenceAccumulator.merge([left, right])
    direct = PHASE20.EvidenceAccumulator()
    direct.add(fixture_row("0.01"))
    direct.add(fixture_row("0.5"))
    assert_true(
        math.isclose(merged.acat("omit"), direct.acat("omit"), rel_tol=0, abs_tol=1e-15),
        "Accumulator merge changed ACAT",
    )
    print("Phase 20 deterministic unit tests passed")


def validate_output(output: Path) -> None:
    status = PHASE20.read_tsv(output / "phase20_status.tsv")
    assert_true(len(status) == 1, "Phase 20 status must contain one row")
    assert_true(
        status[0]["validation_status"] == "validated_complete",
        f"Phase 20 status is {status[0]['validation_status']}",
    )
    checks = PHASE20.read_tsv(output / "phase20_checks.tsv")
    failed = [
        row
        for row in checks
        if row["severity"] == "error" and not PHASE20.is_true(row["passed"])
    ]
    assert_true(not failed, f"Phase 20 has failed checks: {failed}")
    categories = PHASE20.read_tsv(output / "phase20_category_manifest.tsv")
    assert_true(len(categories) == 42, "Category manifest must contain 42 rows")
    assert_true(
        len(
            {
                (row["signature_group"], row["broad_network"])
                for row in categories
            }
        )
        == 42,
        "Category manifest keys are duplicated",
    )
    assert_true(
        sum(int(row["included_run_count"]) for row in categories) == 161,
        "Category run counts do not sum to 161",
    )
    aggregates = PHASE20.iter_tsv(output / "phase20_driver_aggregates.tsv.gz")
    aggregate_count = 0
    keys: set[tuple[str, str, str]] = set()
    for row in aggregates:
        aggregate_count += 1
        assert_true(
            row["case_id"] == "case3_not_core_mito"
            and not PHASE20.is_true(row["is_core_mito"]),
            "An MT driver entered the aggregate output",
        )
        keys.add(
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        )
    assert_true(len(keys) == aggregate_count, "Aggregate keys are duplicated")
    relaxed = PHASE20.read_tsv(output / "phase20_relaxed_candidates.tsv")
    strict = PHASE20.read_tsv(
        output / "phase20_strict_non_mt_reference_candidates.tsv"
    )
    exploratory = PHASE20.read_tsv(output / "phase20_exploratory_leads.tsv")
    assert_true(len(relaxed) == 78, "Relaxed candidate count changed")
    assert_true(len(strict) == 64, "Strict-reference candidate count changed")
    assert_true(len(exploratory) == 16, "Exploratory-only lead count changed")
    assert_true(
        all(
            row["case_id"] == "case3_not_core_mito"
            and not PHASE20.is_true(row["is_core_mito"])
            for row in relaxed + strict + exploratory
        ),
        "An MT driver entered a candidate output",
    )
    artifacts = PHASE20.read_tsv(output / "phase20_artifacts.tsv")
    for row in artifacts:
        path = output / row["path"]
        assert_true(path.is_file(), f"Missing declared artifact: {path}")
        assert_true(
            PHASE20.sha256_file(path) == row["sha256"],
            f"Artifact hash mismatch: {path}",
        )
    print(f"Phase 20 output validation passed: {output}")


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
