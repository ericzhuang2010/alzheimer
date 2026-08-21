#!/usr/bin/env python3
"""Acquire and verify the frozen public Phase 19 Tier 2 source files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=destination.name + ".", suffix=".part", dir=destination.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "phase19-tier2/1.0"})
        with urllib.request.urlopen(request) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=8 * 1024 * 1024)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def verify_source(source: dict, directory: Path, acquire: bool) -> dict:
    filename = source.get("filename")
    if not filename:
        return {**source, "path": "", "state": "registered_deferred", "sha256": ""}
    path = directory / filename
    if not path.exists() and acquire:
        download(source["url"], path)
    if not path.exists():
        return {**source, "path": str(path), "state": "missing", "sha256": ""}
    expected_bytes = source.get("bytes")
    if expected_bytes is not None and path.stat().st_size != int(expected_bytes):
        raise RuntimeError(f"byte-count mismatch for {path}")
    expected_md5 = source.get("md5")
    observed_md5 = digest(path, "md5") if expected_md5 else ""
    if expected_md5 and observed_md5 != expected_md5:
        raise RuntimeError(f"MD5 mismatch for {path}")
    return {
        **source,
        "path": str(path),
        "state": "verified",
        "observed_md5": observed_md5,
        "sha256": digest(path, "sha256"),
        "observed_bytes": path.stat().st_size,
    }


def candidate_genes(config: dict) -> list[str]:
    path = ROOT / config["inputs"]["tier1_candidate_manifest"]
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return sorted({row["gene"] for row in rows if row["is_mtdna_gene"].lower() != "true"})


def query_genes(config: dict, acquire: bool) -> list[dict]:
    directory = ROOT / config["inputs"]["niagads_gene_queries_dir"]
    template = config["alternative_completion"]["qtl_gene_query_url_template"]
    records = []
    for gene in candidate_genes(config):
        path = directory / f"{gene}.tsv"
        url = template.replace("{gene}", gene)
        if not path.exists() and acquire:
            download(url, path)
        records.append({
            "dataset_id": f"NG00184_gene_{gene}",
            "accession": "NG00184.portal",
            "filename": path.name,
            "url": url,
            "role": "significant-only candidate-gene coverage screen",
            "path": str(path),
            "state": "verified" if path.exists() else "missing",
            "observed_bytes": path.stat().st_size if path.exists() else "",
            "sha256": digest(path, "sha256") if path.exists() else "",
        })
    return records


def write_manifest(records: list[dict], destination: Path) -> None:
    columns = [
        "dataset_id", "accession", "file_id", "filename", "url", "role", "path",
        "state", "bytes", "observed_bytes", "md5", "observed_md5", "sha256",
        "retrieved_utc",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with destination.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({**record, "retrieved_utc": stamp})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase19_genetic_support_tier2.yml")
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--skip-gene-queries", action="store_true")
    parser.add_argument("--gene-queries-only", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / args.config).read_text())
    qtl_dir = ROOT / config["inputs"]["niagads_qtl_dir"]
    gwas_dir = ROOT / config["inputs"]["gwas_catalog_dir"]
    records = []
    if not args.gene_queries_only:
        for source in config["alternative_sources"]:
            directory = gwas_dir if source["dataset_id"].startswith("Bellenguez2022") else qtl_dir
            records.append(verify_source(source, directory, args.acquire))
    if not args.skip_gene_queries:
        records.extend(query_genes(config, args.acquire))
    manifest = ROOT / config["inputs"]["external_root"] / "alternative_source_manifest.tsv"
    write_manifest(records, manifest)
    failures = [record for record in records if record.get("state") == "missing"]
    print(f"wrote {len(records)} source records to {manifest}")
    if failures:
        print(f"missing {len(failures)} required/acquired files", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
