#!/usr/bin/env python3
"""Extract full candidate-gene regions from official tabix-indexed eQTL files."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
from pathlib import Path
from typing import Any

import pysam
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"
FIELDS = [
    "molecular_trait_id", "chromosome", "position", "ref", "alt", "variant",
    "ma_samples", "maf", "pvalue", "beta", "se", "type", "ac", "an", "r2",
    "molecular_trait_object_id", "gene_id", "median_tpm", "rsid",
]


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


def write_gzip(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    raw = temporary.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    try:
        writer = csv.DictWriter(text, delimiter="\t", fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    finally:
        text.close()
        raw.close()
    temporary.replace(path)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="config/phase19_genetic_support_tier2_recovery.yml"
    )
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    manifest_dir = resolve(inputs["source_manifest_dir"])
    regional_dir = resolve(inputs["regional_qtl_dir"])
    inventory_dir = resolve(inputs["inventory_dir"])
    routes = [
        row
        for row in read_tsv(manifest_dir / "recovery_route_manifest.tsv")
        if row["gwas_signal_present"] == "TRUE" and row["qtl_type"] == "eQTL"
    ]
    by_dataset: dict[str, list[dict[str, str]]] = {}
    for row in routes:
        by_dataset.setdefault(row["source_dataset_id"], []).append(row)

    summary: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    alpha = float(config["analysis"]["qtl_bonferroni_alpha"])
    dataset_by_id = {row["dataset_id"]: row for row in config["qtl_datasets"]}

    for dataset_id, dataset_routes in sorted(by_dataset.items()):
        dataset = dataset_by_id[dataset_id]
        url = dataset.get("dense_url")
        if not url:
            raise RuntimeError(f"No indexed dense eQTL URL registered for {dataset_id}")
        index_path = inventory_dir / f"{Path(url).name}.tbi"
        if not index_path.exists():
            raise RuntimeError(f"Pinned local tabix index is missing: {index_path}")
        tabix = pysam.TabixFile(url, index=str(index_path))
        kept_by_gene: dict[str, dict[str, dict[str, str]]] = {}
        route_by_gene: dict[str, dict[str, str]] = {}
        for route in dataset_routes:
            gene_id = route["ensembl_gene_id"].split(".")[0]
            route_by_gene[gene_id] = route
            kept_by_gene.setdefault(gene_id, {})
        for gene_id, route in sorted(route_by_gene.items()):
            chromosome = route["chromosome"].removeprefix("chr")
            start = int(route["window_start"])
            end = int(route["window_end"])
            try:
                iterator = tabix.fetch(chromosome, start - 1, end)
            except ValueError as error:
                raise RuntimeError(
                    f"Tabix fetch failed for {dataset_id} {chromosome}:{start}-{end}"
                ) from error
            for line in iterator:
                values = line.split("\t")
                if len(values) != len(FIELDS):
                    raise RuntimeError(
                        f"Unexpected {dataset_id} dense row width {len(values)} != {len(FIELDS)}"
                    )
                row = dict(zip(FIELDS, values))
                if row["molecular_trait_id"].split(".")[0] != gene_id:
                    continue
                position = int(row["position"])
                if not start <= position <= end:
                    raise RuntimeError("Tabix returned a row outside the frozen region")
                kept_by_gene[gene_id][row["variant"]] = row
        tabix.close()

        combined: list[dict[str, str]] = []
        for gene_id in sorted(kept_by_gene):
            rows = sorted(
                kept_by_gene[gene_id].values(),
                key=lambda row: (int(row["chromosome"]), int(row["position"]), row["variant"]),
            )
            combined.extend(rows)
            p_values = [
                float(row["pvalue"])
                for row in rows
                if row["pvalue"] not in {"", "NA", "nan"}
            ]
            threshold = alpha / len(p_values) if p_values else float("nan")
            min_p = min(p_values) if p_values else float("nan")
            route = route_by_gene[gene_id]
            summary.append(
                {
                    "schema_version": SCHEMA,
                    "dataset_id": dataset_id,
                    "study_id": dataset["study_id"],
                    "gene": route["gene"],
                    "ensembl_gene_id": gene_id,
                    "qtl_type": "eQTL",
                    "chromosome": route["chromosome"],
                    "window_start": route["window_start"],
                    "window_end": route["window_end"],
                    "dense_statistics_rows": len(rows),
                    "unique_variants": len({row["variant"] for row in rows}),
                    "minimum_p_value": f"{min_p:.17g}" if p_values else "NA",
                    "bonferroni_tests": len(p_values),
                    "bonferroni_alpha": f"{alpha:.17g}",
                    "bonferroni_threshold": f"{threshold:.17g}" if p_values else "NA",
                    "regional_qtl_signal": (
                        str(min_p <= threshold).upper() if p_values else "NA"
                    ),
                    "coverage_state": (
                        "complete_indexed_candidate_gene_region"
                        if p_values
                        else "gene_not_present_in_indexed_dense_source"
                    ),
                    "source_url": url,
                }
            )
        output = regional_dir / f"{dataset_id}.candidate_dense_eqtl.tsv.gz"
        write_gzip(output, combined)
        artifacts.append(
            {
                "schema_version": SCHEMA,
                "dataset_id": dataset_id,
                "role": "indexed_dense_candidate_eqtl_statistics",
                "source_url": url,
                "path": output.relative_to(ROOT).as_posix(),
                "rows": len(combined),
                "sha256": sha256(output),
            }
        )
        artifacts.append(
            {
                "schema_version": SCHEMA,
                "dataset_id": dataset_id,
                "role": "official_dense_eqtl_tabix_index",
                "source_url": f"{url}.tbi",
                "path": index_path.relative_to(ROOT).as_posix(),
                "rows": "NA",
                "sha256": sha256(index_path),
            }
        )

    write_tsv(
        manifest_dir / "recovery_dense_qtl_extraction_summary.tsv",
        summary,
        [
            "schema_version", "dataset_id", "study_id", "gene", "ensembl_gene_id",
            "qtl_type", "chromosome", "window_start", "window_end",
            "dense_statistics_rows", "unique_variants", "minimum_p_value",
            "bonferroni_tests", "bonferroni_alpha", "bonferroni_threshold",
            "regional_qtl_signal", "coverage_state", "source_url",
        ],
    )
    write_tsv(
        manifest_dir / "recovery_dense_qtl_artifacts.tsv",
        artifacts,
        ["schema_version", "dataset_id", "role", "source_url", "path", "rows", "sha256"],
    )
    print(f"Extracted {len(summary)} dense dataset-gene regions into {len(artifacts)} files")


if __name__ == "__main__":
    main()
