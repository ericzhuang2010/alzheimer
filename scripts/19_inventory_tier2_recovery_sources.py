#!/usr/bin/env python3
"""Freeze Phase 19 Tier 2 recovery routes and their result-blind data requests."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def baseline_hashes(root: Path, artifact_path: Path, tier: str) -> list[dict[str, Any]]:
    rows = read_tsv(artifact_path)
    output: list[dict[str, Any]] = []
    failures: list[str] = []
    for row in rows:
        target = root / row["path"]
        observed = sha256(target) if target.exists() else ""
        status = "pass" if observed == row["sha256"] else "fail"
        if status == "fail":
            failures.append(row["path"])
        output.append(
            {
                "schema_version": SCHEMA,
                "tier": tier,
                "path": row["path"],
                "expected_sha256": row["sha256"],
                "observed_sha256": observed,
                "status": status,
            }
        )
    if failures:
        raise RuntimeError(f"{tier} baseline artifact mismatch: {', '.join(failures)}")
    return output


def minimum_gwas_p(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            try:
                p_value = float(row["p_value"])
            except (TypeError, ValueError):
                continue
            gene = row["gene"]
            current = result.get(gene)
            if current is None or p_value < current["min_p"]:
                result[gene] = {
                    "min_p": p_value,
                    "lead_variant": row["variant_id"],
                    "chromosome": row["chromosome"],
                    "window_start": row["window_start"],
                    "window_end": row["window_end"],
                }
    return result


def select_dataset(route: dict[str, str], datasets: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        dataset
        for dataset in datasets
        if dataset["qtl_type"] == route["qtl_type"]
        and route["broad_network"] in dataset["applies_to"]
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one frozen dataset for {route['route_id']}, found {len(matches)}"
        )
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="config/phase19_genetic_support_tier2_recovery.yml"
    )
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    analysis = config["analysis"]
    source_root = resolve(inputs["source_manifest_dir"])

    tier1_root = resolve(inputs["tier1_root"])
    tier2_root = resolve(inputs["tier2_root"])
    baseline = baseline_hashes(
        tier1_root, resolve(inputs["tier1_artifacts"]), "tier1"
    ) + baseline_hashes(tier2_root, resolve(inputs["tier2_artifacts"]), "tier2")
    write_tsv(
        source_root / "recovery_baseline_hashes.tsv",
        baseline,
        [
            "schema_version",
            "tier",
            "path",
            "expected_sha256",
            "observed_sha256",
            "status",
        ],
    )

    routes = read_tsv(resolve(inputs["tier2_route_manifest"]))
    if len(routes) != int(analysis["expected_base_routes"]):
        raise RuntimeError(f"Expected 54 routes, found {len(routes)}")
    if len({(row["candidate_id"], row["qtl_type"]) for row in routes}) != len(routes):
        raise RuntimeError("Recovery route keys are duplicated")

    gwas = minimum_gwas_p(resolve(inputs["candidate_gwas"]))
    threshold = float(analysis["gwas_signal_p"])
    request_rows: list[dict[str, Any]] = []
    recovery_routes: list[dict[str, Any]] = []
    datasets = config["qtl_datasets"]
    for route in routes:
        dataset = select_dataset(route, datasets)
        signal = gwas[route["gene"]]
        has_signal = signal["min_p"] < threshold
        comparison_id = f"REC-{route['route_id']}"
        route_row = dict(route)
        route_row.update(
            {
                "schema_version": SCHEMA,
                "comparison_id": comparison_id,
                "source_dataset_id": dataset["dataset_id"],
                "source_study_id": dataset["study_id"],
                "source_context": dataset["tissue_label"],
                "context_match_level": dataset["context_match_level"],
                "gwas_min_p": f"{signal['min_p']:.17g}",
                "gwas_lead_variant": signal["lead_variant"],
                "gwas_signal_present": str(has_signal).upper(),
                "decision_frozen_before_qtl_result": "TRUE",
            }
        )
        recovery_routes.append(route_row)
        request_rows.append(
            {
                "schema_version": SCHEMA,
                "comparison_id": comparison_id,
                "route_id": route["route_id"],
                "gene": route["gene"],
                "qtl_type": route["qtl_type"],
                "requested_context": route["broad_network"],
                "selected_dataset_id": dataset["dataset_id"],
                "context_match_level": dataset["context_match_level"],
                "gwas_signal_present": str(has_signal).upper(),
                "qtl_model_requested": str(has_signal).upper(),
                "ld_requested": str(has_signal).upper(),
                "requested_ld_chromosome": signal["chromosome"] if has_signal else "NA",
                "planned_action": (
                    "acquire_qtl_model_and_ld"
                    if has_signal
                    else "terminal_no_regional_gwas_signal"
                ),
                "selection_rule": "frozen_context_hierarchy_then_gwas_gate",
            }
        )

    route_fields = list(routes[0])
    route_fields[route_fields.index("schema_version")] = "schema_version"
    route_fields += [
        "comparison_id",
        "source_dataset_id",
        "source_study_id",
        "source_context",
        "context_match_level",
        "gwas_min_p",
        "gwas_lead_variant",
        "gwas_signal_present",
        "decision_frozen_before_qtl_result",
    ]
    write_tsv(source_root / "recovery_route_manifest.tsv", recovery_routes, route_fields)
    write_tsv(
        source_root / "recovery_request_manifest.tsv",
        request_rows,
        [
            "schema_version",
            "comparison_id",
            "route_id",
            "gene",
            "qtl_type",
            "requested_context",
            "selected_dataset_id",
            "context_match_level",
            "gwas_signal_present",
            "qtl_model_requested",
            "ld_requested",
            "requested_ld_chromosome",
            "planned_action",
            "selection_rule",
        ],
    )

    registry_rows: list[dict[str, Any]] = []
    for dataset in datasets:
        registry_rows.append(
            {
                "schema_version": SCHEMA,
                "study_id": dataset["study_id"],
                "dataset_id": dataset["dataset_id"],
                "study_label": dataset["study_label"],
                "sample_group": dataset["sample_group"],
                "tissue_label": dataset["tissue_label"],
                "qtl_type": dataset["qtl_type"],
                "quant_method": dataset["quant_method"],
                "sample_size": dataset["sample_size"],
                "source_class": dataset["source_class"],
                "context_match_level": dataset["context_match_level"],
                "genome_build": config["source_release"]["eqtl_catalogue_build"],
                "effect_allele": config["source_release"]["eqtl_catalogue_effect_allele"],
                "lbf_url": dataset["lbf_url"],
                "dense_url": dataset.get("dense_url", dataset.get("mapping_url", "NA")),
                "mapping_url": dataset.get("mapping_url", "NA"),
                "selection_frozen_before_result": "TRUE",
            }
        )
    write_tsv(
        source_root / "recovery_dataset_registry.tsv",
        registry_rows,
        list(registry_rows[0]),
    )
    print(
        f"Frozen {len(recovery_routes)} routes; "
        f"{sum(row['gwas_signal_present'] == 'TRUE' for row in recovery_routes)} "
        "require QTL-model/LD recovery"
    )


if __name__ == "__main__":
    main()
