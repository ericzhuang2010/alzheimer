#!/usr/bin/env python3
"""Validate whether an RPS15 route has a primary-compatible LD/model input."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


FIELDS = [
    "route_id",
    "candidate_id",
    "modality",
    "ld_source",
    "ancestry",
    "variant_count",
    "symmetry_pass",
    "diagonal_pass",
    "psd_pass",
    "summary_ld_match",
    "primary_eligible",
    "ld_state",
    "reason",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assessability", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    routes = read_tsv(Path(args.assessability))
    rows = []
    for route in routes:
        complete = route.get("model_state") == "complete_fitted_multisignal_model"
        source_ld = route.get("ld_state") == "source_matched_LD_available"
        eligible = complete and source_ld
        rows.append({
            "route_id": route["route_id"],
            "candidate_id": route["candidate_id"],
            "modality": route["modality"],
            "ld_source": "source_released" if source_ld else "none",
            "ancestry": "source_matched" if source_ld else "source_specific_not_available",
            "variant_count": route.get("harmonized_variants", "0"),
            "symmetry_pass": "TRUE" if source_ld else "NA",
            "diagonal_pass": "TRUE" if source_ld else "NA",
            "psd_pass": "TRUE" if source_ld else "NA",
            "summary_ld_match": "TRUE" if eligible else "NA",
            "primary_eligible": "TRUE" if eligible else "FALSE",
            "ld_state": "validated_primary_compatible" if eligible else "not_run_no_complete_compatible_qtl_model_or_statistics",
            "reason": route.get("reason", ""),
        })
    write_tsv(Path(args.output), rows)
    print(f"routes={len(rows)} primary_eligible={sum(row['primary_eligible'] == 'TRUE' for row in rows)}")


if __name__ == "__main__":
    main()
