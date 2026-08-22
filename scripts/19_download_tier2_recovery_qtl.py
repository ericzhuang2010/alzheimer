#!/usr/bin/env python3
"""Download and checksum the frozen public inputs for Tier 2 recovery."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import subprocess
from typing import Any
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def download(url: str, path: Path, expected_bytes: int | None, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if force and path.exists():
        path.unlink()
    if path.exists() and not force:
        if expected_bytes is None or path.stat().st_size == expected_bytes:
            return
    subprocess.run(
        ["wget", "-c", "-O", str(path), url],
        check=True,
        cwd=ROOT,
        env={**os.environ, "LC_ALL": "C"},
    )
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise RuntimeError(
            f"Byte-count mismatch for {path}: {path.stat().st_size} != {expected_bytes}"
        )


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "schema_version",
        "source_id",
        "source_version",
        "role",
        "url",
        "path",
        "expected_bytes",
        "observed_bytes",
        "expected_md5",
        "observed_md5",
        "sha256",
        "validation_state",
    ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def record(
    source_id: str,
    version: str,
    role: str,
    url: str,
    path: Path,
    expected_bytes: int | None = None,
    expected_md5: str | None = None,
) -> dict[str, Any]:
    observed_bytes = path.stat().st_size if path.exists() else 0
    observed_md5 = digest(path, "md5") if path.exists() and expected_md5 else "NA"
    valid = path.exists()
    if expected_bytes is not None:
        valid = valid and observed_bytes == expected_bytes
    if expected_md5:
        valid = valid and observed_md5 == expected_md5
    return {
        "schema_version": SCHEMA,
        "source_id": source_id,
        "source_version": version,
        "role": role,
        "url": url,
        "path": path.relative_to(ROOT).as_posix(),
        "expected_bytes": expected_bytes if expected_bytes is not None else "NA",
        "observed_bytes": observed_bytes,
        "expected_md5": expected_md5 or "NA",
        "observed_md5": observed_md5,
        "sha256": digest(path, "sha256") if path.exists() else "NA",
        "validation_state": "validated" if valid else "failed",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="config/phase19_genetic_support_tier2_recovery.yml"
    )
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--qtl-only", action="store_true")
    parser.add_argument("--ld-only", action="store_true")
    parser.add_argument("--skip-ld", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    release = config["source_release"]
    inventory_dir = resolve(inputs["inventory_dir"])
    model_dir = resolve(inputs["released_qtl_models_dir"])
    qtl_dir = resolve(inputs["regional_qtl_dir"])
    ld_dir = resolve(inputs["ld_source_dir"])
    manifest_path = resolve(inputs["source_manifest_dir"]) / "recovery_source_manifest.tsv"
    rows: list[dict[str, Any]] = []

    do_metadata = not args.qtl_only and not args.ld_only
    do_qtl = not args.metadata_only and not args.ld_only
    do_ld = not args.metadata_only and not args.qtl_only and not args.skip_ld

    if do_metadata:
        commit = release["eqtl_catalogue_metadata_commit"]
        metadata = {
            "dataset_metadata_r7.tsv": (
                f"https://raw.githubusercontent.com/eQTL-Catalogue/"
                f"eQTL-Catalogue-resources/{commit}/data_tables/dataset_metadata_r7.tsv"
            ),
            "tabix_ftp_paths.tsv": (
                f"https://raw.githubusercontent.com/eQTL-Catalogue/"
                f"eQTL-Catalogue-resources/{commit}/tabix/tabix_ftp_paths.tsv"
            ),
            "Columns.md": (
                f"https://raw.githubusercontent.com/eQTL-Catalogue/"
                f"eQTL-Catalogue-resources/{commit}/tabix/Columns.md"
            ),
        }
        for filename, url in metadata.items():
            path = inventory_dir / filename
            download(url, path, None, args.force)
            rows.append(record("EQTL_Catalogue", commit, "metadata", url, path))

        public_url = "https://st1.niagads.org/portal/v1/fileset_public/NG00067"
        public_path = inventory_dir / "niagads_ng00067_public.json"
        download(public_url, public_path, None, args.force)
        rows.append(record("NG00067", "v21_portal", "public_file_registry", public_url, public_path))

    if do_qtl:
        for dataset in config["qtl_datasets"]:
            dataset_id = dataset["dataset_id"]
            lbf_url = dataset["lbf_url"]
            lbf_path = model_dir / Path(urlparse(lbf_url).path).name
            download(lbf_url, lbf_path, int(dataset["lbf_bytes"]), args.force)
            rows.append(
                record(
                    dataset_id,
                    release["eqtl_catalogue_metadata_release"],
                    "released_susie_log_bayes_factors",
                    lbf_url,
                    lbf_path,
                    int(dataset["lbf_bytes"]),
                )
            )
            credible_url = dataset["credible_sets_url"]
            credible_path = model_dir / Path(urlparse(credible_url).path).name
            download(credible_url, credible_path, None, args.force)
            rows.append(
                record(
                    dataset_id,
                    release["eqtl_catalogue_metadata_release"],
                    "released_susie_credible_sets",
                    credible_url,
                    credible_path,
                )
            )
            if dataset.get("mapping_url"):
                mapping_url = dataset["mapping_url"]
                mapping_path = qtl_dir / Path(urlparse(mapping_url).path).name
                download(mapping_url, mapping_path, int(dataset["mapping_bytes"]), args.force)
                rows.append(
                    record(
                        dataset_id,
                        release["eqtl_catalogue_metadata_release"],
                        "splicing_event_gene_mapping_statistics",
                        mapping_url,
                        mapping_path,
                        int(dataset["mapping_bytes"]),
                    )
                )

    if do_ld:
        for source in config["ld_sources"]:
            path = ld_dir / source["filename"]
            download(source["url"], path, int(source["bytes"]), args.force)
            rows.append(
                record(
                    release["niagads_panel"],
                    release["niagads_accession"],
                    f"ancestry_matched_ld_chr{source['chromosome']}",
                    source["url"],
                    path,
                    int(source["bytes"]),
                    source["md5"],
                )
            )

    existing: list[dict[str, Any]] = []
    if manifest_path.exists():
        with manifest_path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle, delimiter="\t"))
    merged = {(row["source_id"], row["role"], row["path"]): row for row in existing}
    merged.update({(row["source_id"], row["role"], row["path"]): row for row in rows})
    final_rows = [merged[key] for key in sorted(merged)]
    write_manifest(manifest_path, final_rows)
    failures = [row["path"] for row in rows if row["validation_state"] != "validated"]
    if failures:
        raise RuntimeError(f"Source validation failed: {', '.join(failures)}")
    print(f"Validated {len(rows)} source files; manifest has {len(final_rows)} records")


if __name__ == "__main__":
    main()
