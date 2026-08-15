#!/usr/bin/env python3
"""Legacy helpers for the former Case 3 deep-dive figures.

The former Case 3 maps to ``non_mt_driver``, but this module depends on the
retired multi-file Phase 18 bundle and must not be used for current v2 output.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import math
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


CASE_ID = "non_mt_driver"
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
EXPECTED_CIRCLE_GENES = {
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
EXPECTED_EXTRA_CONTEXT = ("Excitatory_neurons", "RPS15")

REQUIRED_INPUTS = [
    "key_driver_status.tsv",
    "key_driver_checks.tsv",
    "key_driver_artifacts.tsv",
    "key_driver_analysis_manifest.tsv",
    "key_driver_case_manifest.tsv",
    "key_driver_top5.tsv",
    "key_driver_figure_data.tsv",
    "key_driver_candidates.tsv",
    "key_driver_candidate_tests.tsv.gz",
    "key_driver_conservative_support.tsv.gz",
    "key_driver_stability_summary.tsv",
    "key_driver_stability_replicates.tsv.gz",
    "key_driver_network_degree_sensitivity.tsv",
    "key_driver_run_manifest.tsv",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes"}


def integer(value: Any) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Expected integer-like value, observed {value!r}") from error


def number(value: Any) -> float | None:
    if value is None or str(value).strip() in {"", "NA", "NaN", "nan", "None"}:
        return None
    try:
        output = float(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Expected numeric value, observed {value!r}") from error
    require(math.isfinite(output), f"Expected finite numeric value, observed {value!r}")
    return output


def token_set(value: Any) -> set[str]:
    if value is None or str(value).strip() in {"", "NA"}:
        return set()
    return {token for token in str(value).split("|") if token}


def sorted_tokens(values: Iterable[str]) -> str:
    return "|".join(sorted(set(values)))


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
        "case_id",
        "atlas_display_order",
        "current_symbol",
        "network_order",
        "broad_network",
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
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if math.isnan(value):
            return "NA"
        return format(value, ".17g")
    return value


def write_tsv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    require(bool(rows), f"Refusing to write empty table: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    columns = ordered_columns(rows)
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean_value(row.get(column)) for column in columns})
    temporary.replace(path)


def write_text(path: Path, text: str) -> None:
    require(bool(text.strip()), f"Refusing to write empty text artifact: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def load_validated_bundle(root: Path, input_dir: Path) -> dict[str, Any]:
    paths = {name: input_dir / name for name in REQUIRED_INPUTS}
    missing = [name for name, path in paths.items() if not path.exists()]
    require(not missing, f"Missing Phase 18 inputs: {', '.join(missing)}")

    status = read_tsv(paths["key_driver_status.tsv"])
    checks = read_tsv(paths["key_driver_checks.tsv"])
    artifacts = read_tsv(paths["key_driver_artifacts.tsv"])
    analysis = read_tsv(paths["key_driver_analysis_manifest.tsv"])
    cases = read_tsv(paths["key_driver_case_manifest.tsv"])

    require_columns(status, ["validation_status", "failed_checks"], "key_driver_status.tsv")
    require(len(status) == 1, "Phase 18 status must contain exactly one row")
    require(status[0]["validation_status"] == "validated_complete", "Phase 18 is not validated_complete")
    require(integer(status[0]["failed_checks"]) == 0, "Phase 18 reports failed checks")
    require_columns(checks, ["check_id", "severity", "passed"], "key_driver_checks.tsv")
    require(all(truth(row["passed"]) for row in checks), "At least one Phase 18 check failed")
    require_columns(artifacts, ["path", "bytes", "sha256", "hash_status"], "key_driver_artifacts.tsv")
    artifact_map = {row["path"]: row for row in artifacts}
    require(len(artifact_map) == len(artifacts), "Duplicate paths in key_driver_artifacts.tsv")
    for name, path in paths.items():
        record = artifact_map.get(name)
        require(record is not None, f"No artifact record for {name}")
        if record["hash_status"] == "recorded":
            require(integer(record["bytes"]) == path.stat().st_size, f"Artifact byte count changed: {name}")
            require(record["sha256"] == sha256_file(path), f"Artifact SHA-256 changed: {name}")
        else:
            require(
                name in {"key_driver_artifacts.tsv", "key_driver_status.tsv"}
                and record["hash_status"] == "written_after_artifact_manifest",
                f"Unexpected unrecorded artifact state for {name}",
            )

    require_columns(
        analysis,
        ["primary_groups", "directions", "minimum_coverage", "aggregate_q_threshold", "ranking_order", "display_limit", "validation_class"],
        "key_driver_analysis_manifest.tsv",
    )
    require(len(analysis) == 1, "Analysis manifest must contain exactly one row")
    manifest = analysis[0]
    require(manifest["validation_class"] == "validated_complete", "Analysis manifest is not validated_complete")
    require(manifest["ranking_order"] == "aggregate_acat_q|aggregate_acat_p|current_symbol", "Phase 18 ranking rule drifted")
    require(integer(manifest["display_limit"]) == 5, "Phase 18 display limit drifted")
    require(abs(float(manifest["minimum_coverage"]) - 0.8) <= 1e-12, "Minimum coverage drifted")
    require(abs(float(manifest["aggregate_q_threshold"]) - 0.05) <= 1e-12, "Aggregate q threshold drifted")

    require_columns(cases, ["case_order", "case_id"], "key_driver_case_manifest.tsv")
    ordered_cases = [row["case_id"] for row in sorted(cases, key=lambda row: integer(row["case_order"]))]
    require(ordered_cases == ["mt_driver", CASE_ID], "Driver-class manifest drifted")

    return {
        "root": root,
        "input_dir": input_dir,
        "paths": paths,
        "status": status[0],
        "checks": checks,
        "artifacts": artifacts,
        "analysis": manifest,
        "cases": cases,
    }
