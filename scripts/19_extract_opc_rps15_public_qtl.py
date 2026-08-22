#!/usr/bin/env python3
"""Stream compact RPS15 rows from already-local NG00184 chromosome files."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
from pathlib import Path
from typing import Any, Iterable


TARGET_SYMBOL = "RPS15"
TARGET_ENSEMBL = "ENSG00000115268"


def parse_info(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in (value or "").split(";"):
        if "=" in token:
            key, item = token.split("=", 1)
            if key not in result:
                result[key] = item
    return result


def safe_float(value: Any) -> float | None:
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def is_target(row: dict[str, str], symbol: str = TARGET_SYMBOL, ensembl: str = TARGET_ENSEMBL) -> bool:
    return row.get("target_gene_symbol", "") == symbol or row.get("target_ensembl_id", "").split(".")[0] == ensembl


def scan_target_file(
    path: Path,
    symbol: str = TARGET_SYMBOL,
    ensembl: str = TARGET_ENSEMBL,
) -> tuple[list[str], list[dict[str, str]]]:
    hits: list[dict[str, str]] = []
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = list(reader.fieldnames or [])
        required = {"variant_id", "target_gene_symbol", "target_ensembl_id", "target", "target_info"}
        missing = required - set(fields)
        if missing:
            raise RuntimeError(f"Unexpected NG00184 schema in {path}: missing {sorted(missing)}")
        for row in reader:
            if is_target(row, symbol, ensembl):
                hits.append(row)
    return fields, hits


def write_gzip_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, delimiter="\t", fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--symbol", default=TARGET_SYMBOL)
    parser.add_argument("--ensembl", default=TARGET_ENSEMBL)
    args = parser.parse_args()

    root = Path(args.input_root).resolve()
    output = Path(args.output).resolve()
    files = sorted(root.rglob("*.bed.gz"))
    if not files:
        raise RuntimeError(f"No BED.GZ files found under {root}")

    output_fields = ["source_file"]
    output_rows: list[dict[str, str]] = []
    union: list[str] = []
    for source in files:
        fields, hits = scan_target_file(source, args.symbol, args.ensembl)
        for field in fields:
            if field not in union:
                union.append(field)
        for row in hits:
            output_rows.append({"source_file": str(source), **row})
    output_fields.extend(union)
    write_gzip_tsv(output, output_fields, output_rows)
    print(f"files={len(files)} target_rows={len(output_rows)} output={output}")


if __name__ == "__main__":
    main()
