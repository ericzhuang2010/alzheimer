#!/usr/bin/env python3
"""Normalize the frozen ENCODE proximal TF-target network to current symbols."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import os
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path


RELEASE = "ENCODE_2012_Gerstein_filtered_proximal_TIP"
RELATION = "proximal_filtered"
OUTPUT_COLUMNS = ("parent", "child", "source", "release")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_aliases(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def gencode_genes(path: Path) -> tuple[set[str], dict[str, set[str]]]:
    symbols: set[str] = set()
    stable_to_symbols: dict[str, set[str]] = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 or fields[2] != "gene":
                continue
            attributes: dict[str, str] = {}
            for item in fields[8].rstrip(";").split("; "):
                key, separator, value = item.partition(" ")
                if separator:
                    attributes[key] = value.strip('"')
            gene_id = attributes.get("gene_id", "").split(".", 1)[0]
            symbol = attributes.get("gene_name", "")
            if gene_id and symbol:
                symbols.add(symbol)
                stable_to_symbols[gene_id].add(symbol)
    return symbols, stable_to_symbols


def hgnc_symbol_maps(
    path: Path,
    gencode_symbols: set[str],
    gencode_stable_to_symbols: dict[str, set[str]],
) -> tuple[dict[str, str], dict[str, str], set[str]]:
    approved: dict[str, str] = {}
    candidate_aliases: dict[str, set[str]] = defaultdict(set)
    current_symbols: set[str] = set()
    with path.open("rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"symbol", "status", "alias_symbol", "prev_symbol", "ensembl_gene_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"HGNC table lacks columns: {sorted(required)}")
        for row in reader:
            if row["status"] != "Approved":
                continue
            symbol = row["symbol"].strip()
            ensembl_ids = split_aliases(row.get("ensembl_gene_id"))
            linked_by_ensembl = any(
                symbol in gencode_stable_to_symbols.get(ensembl_id.split(".", 1)[0], set())
                for ensembl_id in ensembl_ids
            )
            if not linked_by_ensembl and symbol not in gencode_symbols:
                continue
            approved[symbol] = symbol
            current_symbols.add(symbol)
            for alias in split_aliases(row.get("prev_symbol")):
                candidate_aliases[alias].add(symbol)
            for alias in split_aliases(row.get("alias_symbol")):
                candidate_aliases[alias].add(symbol)
    unique_aliases = {
        alias: next(iter(symbols))
        for alias, symbols in candidate_aliases.items()
        if len(symbols) == 1 and alias not in approved
    }
    return approved, unique_aliases, current_symbols


def resolve_symbol(
    symbol: str,
    approved: dict[str, str],
    unique_aliases: dict[str, str],
    gencode_symbols: set[str],
) -> tuple[str | None, str]:
    if symbol in approved:
        return approved[symbol], "HGNC_approved_exact"
    if symbol in unique_aliases:
        return unique_aliases[symbol], "HGNC_unique_previous_or_alias"
    if symbol in gencode_symbols:
        return symbol, "GENCODE_v44_exact"
    return None, "unresolved"


def read_source(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split()
            if len(fields) != 3 or fields[1] != RELATION:
                raise ValueError(f"Unexpected ENCODE row {line_number}: {line.rstrip()}")
            rows.append((fields[0], fields[2]))
    if not rows:
        raise ValueError("ENCODE source is empty")
    if len(rows) != len(set(rows)):
        raise ValueError("ENCODE source contains duplicate TF-target pairs")
    return rows


def deterministic_gzip_stored(payload: bytes) -> bytes:
    """Return a valid gzip stream without zlib-version-dependent compression."""
    output = bytearray(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff")
    if not payload:
        output.extend(b"\x01\x00\x00\xff\xff")
    else:
        for offset in range(0, len(payload), 65535):
            block = payload[offset : offset + 65535]
            final = offset + len(block) == len(payload)
            output.append(1 if final else 0)
            output.extend(struct.pack("<HH", len(block), len(block) ^ 0xFFFF))
            output.extend(block)
    output.extend(struct.pack("<II", zlib.crc32(payload), len(payload) & 0xFFFFFFFF))
    return bytes(output)


def atomic_write_gzip_tsv(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    text = io.StringIO(newline="")
    writer = csv.writer(text, delimiter="\t", lineterminator="\n")
    writer.writerow(OUTPUT_COLUMNS)
    for parent, child in rows:
        writer.writerow((parent, child, "ENCODE", RELEASE))
    temporary.write_bytes(deterministic_gzip_stored(text.getvalue().encode("utf-8")))
    os.replace(temporary, path)


def atomic_write_tsv(path: Path, columns: tuple[str, ...], rows: list[tuple[object, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--source", type=Path, required=True)
    argument_parser.add_argument("--source-sha256", required=True)
    argument_parser.add_argument("--gencode", type=Path, required=True)
    argument_parser.add_argument("--hgnc", type=Path, required=True)
    argument_parser.add_argument("--output", type=Path, required=True)
    argument_parser.add_argument("--summary", type=Path, required=True)
    argument_parser.add_argument("--rejections", type=Path, required=True)
    args = argument_parser.parse_args()

    observed_source_sha256 = sha256_file(args.source)
    if observed_source_sha256 != args.source_sha256:
        raise ValueError(
            "ENCODE source SHA-256 mismatch: "
            f"expected={args.source_sha256}; observed={observed_source_sha256}"
        )

    source_rows = read_source(args.source)
    gencode_symbols, gencode_stable_to_symbols = gencode_genes(args.gencode)
    approved, unique_aliases, _ = hgnc_symbol_maps(
        args.hgnc, gencode_symbols, gencode_stable_to_symbols
    )

    mapping_counts: Counter[str] = Counter()
    accepted: set[tuple[str, str]] = set()
    rejections: list[tuple[object, ...]] = []
    mapped_before_deduplication = 0
    self_loops = 0
    for input_parent, input_child in source_rows:
        parent, parent_method = resolve_symbol(
            input_parent, approved, unique_aliases, gencode_symbols
        )
        child, child_method = resolve_symbol(
            input_child, approved, unique_aliases, gencode_symbols
        )
        mapping_counts[f"parent_{parent_method}"] += 1
        mapping_counts[f"child_{child_method}"] += 1
        if parent is None or child is None:
            reason = "unresolved_parent" if parent is None else "unresolved_child"
            if parent is None and child is None:
                reason = "unresolved_parent_and_child"
            rejections.append((input_parent, input_child, reason, parent_method, child_method))
            continue
        if parent == child:
            self_loops += 1
            rejections.append((input_parent, input_child, "self_loop", parent_method, child_method))
            continue
        mapped_before_deduplication += 1
        accepted.add((parent, child))

    accepted_rows = sorted(accepted)
    rejection_rows = sorted(rejections)
    atomic_write_gzip_tsv(args.output, accepted_rows)
    atomic_write_tsv(
        args.rejections,
        ("input_parent", "input_child", "reason", "parent_mapping", "child_mapping"),
        rejection_rows,
    )

    summary_values: list[tuple[object, ...]] = [
        ("release", RELEASE),
        ("source_sha256", observed_source_sha256),
        ("source_rows", len(source_rows)),
        ("source_unique_tfs", len({parent for parent, _ in source_rows})),
        ("source_unique_targets", len({child for _, child in source_rows})),
        ("mapped_rows_before_deduplication", mapped_before_deduplication),
        ("rejected_rows", len(rejection_rows)),
        ("self_loops_excluded", self_loops),
        ("duplicate_mapped_edges_collapsed", mapped_before_deduplication - len(accepted_rows)),
        ("final_edges", len(accepted_rows)),
        ("final_unique_tfs", len({parent for parent, _ in accepted_rows})),
        ("final_unique_targets", len({child for _, child in accepted_rows})),
    ]
    summary_values.extend(sorted(mapping_counts.items()))
    atomic_write_tsv(args.summary, ("metric", "value"), summary_values)

    output_sha256 = sha256_file(args.output)
    print(f"release={RELEASE}")
    print(f"source_rows={len(source_rows)}")
    print(f"final_edges={len(accepted_rows)}")
    print(f"rejected_rows={len(rejection_rows)}")
    print(f"output_sha256={output_sha256}")
    print("encode_tf_target_status=completed_for_review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
