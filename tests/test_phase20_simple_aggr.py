#!/usr/bin/env python3
"""Deterministic unit and output checks for the simple returned-only KDA view."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase20_simple_aggr",
    ROOT / "scripts" / "20_sex_apoe_kda_simple_aggr.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load simple Phase 20 aggregation implementation")
SIMPLE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SIMPLE
SPEC.loader.exec_module(SIMPLE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unit_tests() -> None:
    require(math.isclose(SIMPLE.acat_combine([0.01]), 0.01, abs_tol=1e-15), "Singleton ACAT drifted")
    require(
        math.isclose(
            SIMPLE.acat_combine([0.01, 0.02]),
            0.01333430842986355,
            rel_tol=0,
            abs_tol=1e-15,
        ),
        "Two-value ACAT fixture drifted",
    )
    require(
        math.isclose(SIMPLE.acat_combine([0.02, 0.02]), 0.02, rel_tol=0, abs_tol=1e-15),
        "Repeated-value ACAT fixture drifted",
    )
    require(
        SIMPLE.acat_combine([0.01, 0.02, 0.03])
        == SIMPLE.acat_combine([0.03, 0.01, 0.02]),
        "ACAT must be permutation invariant",
    )
    print("Simple Phase 20 aggregation unit tests passed")


def validate_output(output: Path) -> None:
    global_rows = SIMPLE.read_tsv(output / "simple_global_gene_aggregates.tsv")
    category_rows = SIMPLE.read_tsv(output / "simple_category_gene_aggregates.tsv")
    details = SIMPLE.read_tsv(output / "simple_returned_call_rows.tsv.gz")
    categories = SIMPLE.read_tsv(output / "simple_category_summary.tsv")
    checks = SIMPLE.read_tsv(output / "simple_checks.tsv")
    status = SIMPLE.read_tsv(output / "simple_status.tsv")

    require(len(global_rows) == 615, f"Unexpected global row count: {len(global_rows)}")
    require(len(category_rows) == 1298, f"Unexpected category row count: {len(category_rows)}")
    require(len(details) == 2494, f"Unexpected detail count: {len(details)}")
    require(len(categories) == 42, f"Unexpected structural category count: {len(categories)}")
    require(len(status) == 1, "Status must have exactly one row")
    require(status[0]["execution_status"] == "complete", "Execution status is not complete")
    require(status[0]["failed_check_count"] == "0", "Status reports failed checks")
    require(
        status[0]["interpretation_status"] == "exploratory_post_selected_not_fdr_controlled",
        "Interpretation label drifted",
    )
    require(
        all(SIMPLE.is_true(row["passed"]) for row in checks),
        f"Failed built-in checks: {[row['check_id'] for row in checks if not SIMPLE.is_true(row['passed'])]}",
    )

    require(len({row["current_symbol"] for row in global_rows}) == len(global_rows), "Duplicate global gene")
    require(
        len(
            {
                (row["signature_group"], row["broad_network"], row["current_symbol"])
                for row in category_rows
            }
        )
        == len(category_rows),
        "Duplicate category-gene unit",
    )
    require(
        len({(row["kda_run_id"], row["current_symbol"]) for row in details}) == len(details),
        "Duplicate returned run-gene key",
    )
    require(
        all(0 < float(row["returned_within_call_q"]) <= 0.05 + 1e-12 for row in details),
        "A detail row violates the stock significance filter",
    )

    detail_by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    detail_by_category_gene: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in details:
        detail_by_gene[row["current_symbol"]].append(row)
        detail_by_category_gene[
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        ].append(row)

    require(sum(len(rows) for rows in detail_by_gene.values()) == 2494, "Global detail conservation failed")
    require(
        sum(len(rows) for rows in detail_by_category_gene.values()) == 2494,
        "Category detail conservation failed",
    )

    def check_aggregates(
        aggregates: list[dict[str, str]],
        source: dict[object, list[dict[str, str]]],
        key_function,
    ) -> None:
        for aggregate in aggregates:
            key = key_function(aggregate)
            input_rows = source[key]
            values = [float(row["returned_within_call_q"]) for row in input_rows]
            observed = float(aggregate["returned_run_q_acat_score"])
            alias = float(aggregate["requested_final_q"])
            require(observed == alias, f"Requested alias differs for {key}")
            require(int(aggregate["returned_call_count"]) == len(values), f"Return count differs for {key}")
            if len(values) == 1:
                expected = values[0]
                require(
                    aggregate["final_value_method"] == "singleton_within_call_q_passthrough",
                    f"Singleton method differs for {key}",
                )
                require(aggregate["acat_of_returned_within_call_q"] == "NA", f"Singleton ACAT should be NA for {key}")
            else:
                expected = SIMPLE.acat_combine(values)
                require(
                    aggregate["final_value_method"] == "acat_of_returned_within_call_q_values",
                    f"Recurrent method differs for {key}",
                )
            require(math.isclose(observed, expected, rel_tol=0, abs_tol=1e-15), f"Score differs for {key}")
            require(not SIMPLE.is_true(aggregate["formal_fdr_controlled_q"]), f"Formal-q flag differs for {key}")
            require(aggregate["input_statistic"] == "stock_within_call_bh_q", f"Input label differs for {key}")
            require(
                aggregate["inferential_status"] == "exploratory_postselection",
                f"Inferential label differs for {key}",
            )
            require(aggregate["multiple_testing_after_acat"] == "none", f"Multiplicity label differs for {key}")
            require(
                not SIMPLE.is_true(aggregate["additional_across_gene_bh_applied"]),
                f"Unexpected BH flag for {key}",
            )

    check_aggregates(global_rows, detail_by_gene, lambda row: row["current_symbol"])
    check_aggregates(
        category_rows,
        detail_by_category_gene,
        lambda row: (row["signature_group"], row["broad_network"], row["current_symbol"]),
    )

    require(sum(int(row["returned_call_count"]) == 1 for row in global_rows) == 363, "Global singleton count drifted")
    require(sum(int(row["returned_call_count"]) >= 2 for row in global_rows) == 252, "Global recurrent count drifted")
    require(sum(int(row["returned_call_count"]) == 1 for row in category_rows) == 892, "Category singleton count drifted")
    require(sum(int(row["returned_call_count"]) >= 2 for row in category_rows) == 406, "Category recurrent count drifted")
    require(sum(int(row["returned_call_count"]) for row in global_rows) == 2494, "Global occurrence sum drifted")
    require(sum(int(row["returned_call_count"]) for row in category_rows) == 2494, "Category occurrence sum drifted")

    global_order = sorted(
        global_rows,
        key=lambda row: (float(row["returned_run_q_acat_score"]), row["current_symbol"]),
    )
    require([int(row["rank"]) for row in global_order] == list(range(1, 616)), "Global ranks drifted")
    category_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in category_rows:
        category_groups[(row["signature_group"], row["broad_network"])].append(row)
    for key, rows in category_groups.items():
        ordered = sorted(
            rows,
            key=lambda row: (float(row["returned_run_q_acat_score"]), row["current_symbol"]),
        )
        require(
            [int(row["rank"]) for row in ordered] == list(range(1, len(rows) + 1)),
            f"Category ranks drifted for {key}",
        )
    print("Simple Phase 20 aggregation output checks passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/minerva_production/20_sex_apoe_kda_simple_aggr",
    )
    args = parser.parse_args()
    unit_tests()
    validate_output(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
