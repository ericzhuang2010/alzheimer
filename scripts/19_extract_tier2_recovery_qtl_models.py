#!/usr/bin/env python3
"""Extract complete released SuSiE model rows for frozen recovery genes."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def deterministic_gzip_writer(path: Path) -> tuple[io.TextIOWrapper, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline=""), raw


def write_gzip_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    temporary = path.with_suffix(path.suffix + ".tmp")
    handle, raw = deterministic_gzip_writer(temporary)
    count = 0
    try:
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=fields, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    finally:
        handle.close()
        raw.close()
    temporary.replace(path)
    return count


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=fields, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def unique_event_mapping(
    path: Path, wanted_genes: set[str]
) -> tuple[dict[str, str], list[dict[str, str]], list[str]]:
    event_to_gene: dict[str, str] = {}
    rows: dict[str, dict[str, str]] = {}
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        required = {"molecular_trait_id", "gene_id", "molecular_trait_object_id"}
        if not required.issubset(fields):
            raise RuntimeError(f"Missing sQTL mapping fields in {path}: {required - set(fields)}")
        for row in reader:
            gene = row["gene_id"].split(".")[0]
            if gene not in wanted_genes:
                continue
            trait = row["molecular_trait_id"]
            prior = event_to_gene.get(trait)
            if prior is not None and prior != gene:
                raise RuntimeError(f"Ambiguous event-to-gene mapping for {trait}")
            event_to_gene[trait] = gene
            if trait not in rows:
                rows[trait] = {field: row.get(field, "") for field in fields}
    return event_to_gene, [rows[key] for key in sorted(rows)], fields


def filtered_rows(path: Path, wanted_traits: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    kept: list[dict[str, str]] = []
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if "molecular_trait_id" not in fields:
            raise RuntimeError(f"No molecular_trait_id in {path}")
        for row in reader:
            if row["molecular_trait_id"] in wanted_traits:
                kept.append(row)
    return fields, kept


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="config/phase19_genetic_support_tier2_recovery.yml"
    )
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    route_path = resolve(inputs["source_manifest_dir"]) / "recovery_route_manifest.tsv"
    routes = [row for row in read_tsv(route_path) if row["gwas_signal_present"] == "TRUE"]
    by_dataset: dict[str, list[dict[str, str]]] = {}
    for row in routes:
        by_dataset.setdefault(row["source_dataset_id"], []).append(row)

    model_dir = resolve(inputs["released_qtl_models_dir"])
    regional_dir = resolve(inputs["regional_qtl_dir"])
    manifest_dir = resolve(inputs["source_manifest_dir"])
    summary_rows: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []

    for dataset in config["qtl_datasets"]:
        dataset_id = dataset["dataset_id"]
        selected = by_dataset.get(dataset_id, [])
        if not selected:
            continue
        genes = {row["ensembl_gene_id"].split(".")[0]: row["gene"] for row in selected}
        gene_traits: dict[str, set[str]] = {gene_id: set() for gene_id in genes}
        mapping_rows: list[dict[str, str]] = []
        mapping_fields: list[str] = []
        if dataset["qtl_type"] == "eQTL":
            gene_traits = {gene_id: {gene_id} for gene_id in genes}
        else:
            mapping_url = dataset.get("mapping_url")
            if not mapping_url:
                raise RuntimeError(f"No sQTL event mapping registered for {dataset_id}")
            mapping_path = regional_dir / Path(urlparse(mapping_url).path).name
            event_to_gene, mapping_rows, mapping_fields = unique_event_mapping(
                mapping_path, set(genes)
            )
            for trait, gene_id in event_to_gene.items():
                gene_traits[gene_id].add(trait)
            mapping_output = regional_dir / f"{dataset_id}.candidate_event_mapping.tsv.gz"
            write_gzip_tsv(mapping_output, mapping_rows, mapping_fields)
            artifact_rows.append(
                {
                    "schema_version": SCHEMA,
                    "dataset_id": dataset_id,
                    "role": "candidate_event_mapping",
                    "path": mapping_output.relative_to(ROOT).as_posix(),
                    "rows": len(mapping_rows),
                    "sha256": sha256(mapping_output),
                }
            )

        wanted_traits = set().union(*gene_traits.values())
        lbf_input = model_dir / Path(urlparse(dataset["lbf_url"]).path).name
        lbf_fields, lbf_rows = filtered_rows(lbf_input, wanted_traits)
        lbf_output = regional_dir / f"{dataset_id}.candidate_lbf.tsv.gz"
        write_gzip_tsv(lbf_output, lbf_rows, lbf_fields)
        artifact_rows.append(
            {
                "schema_version": SCHEMA,
                "dataset_id": dataset_id,
                "role": "candidate_released_susie_lbf",
                "path": lbf_output.relative_to(ROOT).as_posix(),
                "rows": len(lbf_rows),
                "sha256": sha256(lbf_output),
            }
        )

        credible_input = model_dir / Path(urlparse(dataset["credible_sets_url"]).path).name
        credible_fields, credible_rows = filtered_rows(credible_input, wanted_traits)
        credible_output = regional_dir / f"{dataset_id}.candidate_credible_sets.tsv.gz"
        write_gzip_tsv(credible_output, credible_rows, credible_fields)
        artifact_rows.append(
            {
                "schema_version": SCHEMA,
                "dataset_id": dataset_id,
                "role": "candidate_released_credible_sets",
                "path": credible_output.relative_to(ROOT).as_posix(),
                "rows": len(credible_rows),
                "sha256": sha256(credible_output),
            }
        )

        lbf_counts: dict[str, int] = {}
        variant_counts: dict[str, set[str]] = {}
        for row in lbf_rows:
            trait = row["molecular_trait_id"]
            lbf_counts[trait] = lbf_counts.get(trait, 0) + 1
            variant_counts.setdefault(trait, set()).add(row["variant"])
        credible_counts: dict[str, int] = {}
        for row in credible_rows:
            trait = row["molecular_trait_id"]
            credible_counts[trait] = credible_counts.get(trait, 0) + 1

        for gene_id, gene_symbol in sorted(genes.items()):
            traits = sorted(gene_traits[gene_id])
            traits_with_model = [trait for trait in traits if lbf_counts.get(trait, 0) > 0]
            variant_union: set[str] = set()
            for trait in traits:
                variant_union.update(variant_counts.get(trait, set()))
            summary_rows.append(
                {
                    "schema_version": SCHEMA,
                    "dataset_id": dataset_id,
                    "study_id": dataset["study_id"],
                    "qtl_type": dataset["qtl_type"],
                    "gene": gene_symbol,
                    "ensembl_gene_id": gene_id,
                    "mapped_molecular_traits": len(traits),
                    "traits_with_released_model": len(traits_with_model),
                    "molecular_trait_ids": ";".join(traits),
                    "model_lbf_rows": sum(lbf_counts.get(trait, 0) for trait in traits),
                    "unique_model_variants": len(variant_union),
                    "credible_set_rows": sum(credible_counts.get(trait, 0) for trait in traits),
                    "model_availability": (
                        "released_complete_lbf_model"
                        if traits_with_model
                        else "no_released_model_for_mapped_trait"
                    ),
                }
            )

    write_tsv(
        manifest_dir / "recovery_qtl_model_extraction_summary.tsv",
        summary_rows,
        [
            "schema_version", "dataset_id", "study_id", "qtl_type", "gene",
            "ensembl_gene_id", "mapped_molecular_traits", "traits_with_released_model",
            "molecular_trait_ids", "model_lbf_rows", "unique_model_variants",
            "credible_set_rows", "model_availability",
        ],
    )
    write_tsv(
        manifest_dir / "recovery_qtl_model_artifacts.tsv",
        artifact_rows,
        ["schema_version", "dataset_id", "role", "path", "rows", "sha256"],
    )
    print(
        f"Extracted {len(summary_rows)} dataset-gene model audits and "
        f"{len(artifact_rows)} deterministic artifacts"
    )


if __name__ == "__main__":
    main()
