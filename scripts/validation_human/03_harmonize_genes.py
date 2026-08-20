#!/usr/bin/env python3
"""VH03: preserve SEA-AD feature order and attach HGNC/GENCODE/MitoCarta IDs."""

from __future__ import annotations

import gzip
import re
from collections import defaultdict

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_output_dir,
    repo_path,
    require_validated_status,
    sha256_strings,
    status_frame,
    utc_now,
)


GTF_ATTRIBUTE = re.compile(r'(\w+) "([^"]+)"')


def split_aliases(value) -> list[str]:
    if pd.isna(value):
        return []
    return [piece.strip() for piece in str(value).split("|") if piece.strip()]


def read_gencode_genes(path):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 or fields[2] != "gene":
                continue
            attributes = dict(GTF_ATTRIBUTE.findall(fields[8]))
            if "gene_id" in attributes and "gene_name" in attributes:
                rows.append(
                    {
                        "chromosome": fields[0],
                        "gencode_gene_id": re.sub(r"\.\d+$", "", attributes["gene_id"]),
                        "gencode_gene_name": attributes["gene_name"],
                        "gene_type": attributes.get("gene_type", ""),
                    }
                )
    return pd.DataFrame(rows).drop_duplicates()


def main() -> int:
    args = parse_config_cli("VH03: harmonize SEA-AD genes")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_validated_status(output_root / "01_audit/status.tsv")
    output_dir = phase_output_dir(output_root, "03_genes")
    expected_genes = int(config["expected"]["genes"])

    raw = pd.read_csv(output_root / "01_audit/gene_inventory_raw.tsv", sep="\t", dtype=str)
    raw["feature_index"] = pd.to_numeric(raw["feature_index"]).astype(int)
    raw = raw.sort_values("feature_index").reset_index(drop=True)
    raw = raw.rename(columns={"gene": "source_symbol"})

    hgnc_path = repo_path(project_root, config["references"]["hgnc_complete_set"])
    hgnc = pd.read_csv(hgnc_path, sep="\t", dtype=str, low_memory=False)
    hgnc = hgnc.loc[hgnc["status"].eq("Approved")].copy()
    exact = hgnc.drop_duplicates("symbol").set_index("symbol")

    alias_targets = defaultdict(set)
    for row in hgnc.itertuples(index=False):
        for column in ["alias_symbol", "prev_symbol"]:
            for alias in split_aliases(getattr(row, column)):
                alias_targets[alias].add(row.symbol)
    unique_alias = {
        alias: next(iter(targets))
        for alias, targets in alias_targets.items()
        if len(targets) == 1
    }
    ambiguous_alias = {
        alias: sorted(targets)
        for alias, targets in alias_targets.items()
        if len(targets) > 1
    }

    gencode = read_gencode_genes(repo_path(project_root, config["references"]["gencode_gtf"]))
    gencode_groups = {
        symbol: group
        for symbol, group in gencode.groupby("gencode_gene_name", sort=False)
    }

    mitocarta = pd.read_csv(
        repo_path(project_root, config["references"]["mitocarta_genes"]),
        sep="\t",
        usecols=["canonical_symbol"],
        dtype=str,
    )
    mitocarta_symbols = set(mitocarta["canonical_symbol"].dropna().unique())
    mito_aliases = pd.read_csv(
        repo_path(project_root, config["references"]["mitocarta_aliases"]),
        sep="\t",
        dtype=str,
    )
    mito_aliases = mito_aliases.loc[
        mito_aliases["canonical_targets"].astype(int).eq(1),
        ["alias", "canonical_symbol"],
    ].drop_duplicates("alias")
    mito_alias_map = dict(zip(mito_aliases["alias"], mito_aliases["canonical_symbol"]))

    annotation_rows = []
    alias_rows = []
    ambiguity_rows = []
    for record in raw.itertuples(index=False):
        source = record.source_symbol
        approved = None
        hgnc_match = "unresolved"
        if source in exact.index:
            approved = source
            hgnc_match = "exact"
        elif source in unique_alias:
            approved = unique_alias[source]
            hgnc_match = "alias"
            alias_rows.append(
                {
                    "source_symbol": source,
                    "approved_symbol": approved,
                    "alias_type": "HGNC_alias_or_previous",
                }
            )
        elif source in ambiguous_alias:
            hgnc_match = "ambiguous_alias"
            ambiguity_rows.append(
                {
                    "source_symbol": source,
                    "ambiguity_type": "HGNC_alias",
                    "candidate_symbols": "|".join(ambiguous_alias[source]),
                }
            )

        hgnc_id = exact.loc[approved, "hgnc_id"] if approved in exact.index else None
        mapping_symbol = approved or source
        gencode_group = gencode_groups.get(mapping_symbol)
        gencode_id = None
        chromosome = None
        gene_type = None
        gencode_match = "unresolved"
        if gencode_group is not None:
            unique_ids = gencode_group["gencode_gene_id"].dropna().unique()
            if len(unique_ids) == 1:
                selected = gencode_group.iloc[0]
                gencode_id = selected["gencode_gene_id"]
                chromosome = selected["chromosome"]
                gene_type = selected["gene_type"]
                gencode_match = "approved_symbol" if approved else "source_symbol"
            else:
                gencode_match = "ambiguous_symbol"
                ambiguity_rows.append(
                    {
                        "source_symbol": source,
                        "ambiguity_type": "GENCODE_symbol",
                        "candidate_symbols": "|".join(sorted(unique_ids)),
                    }
                )

        mito_symbol = None
        if mapping_symbol in mitocarta_symbols:
            mito_symbol = mapping_symbol
        elif source in mitocarta_symbols:
            mito_symbol = source
        elif source in mito_alias_map:
            mito_symbol = mito_alias_map[source]
        is_mitocarta = mito_symbol in mitocarta_symbols if mito_symbol else False
        is_mtdna_protein = chromosome == "chrM" and gene_type == "protein_coding"

        annotation_rows.append(
            {
                "feature_index": int(record.feature_index),
                "source_symbol": source,
                "source_gene_ids": record.gene_ids,
                "approved_symbol": approved,
                "hgnc_id": hgnc_id,
                "hgnc_match_type": hgnc_match,
                "gencode_gene_id": gencode_id,
                "gencode_gene_name": mapping_symbol if gencode_id else None,
                "chromosome": chromosome,
                "gene_type": gene_type,
                "gencode_match_type": gencode_match,
                "mitocarta_symbol": mito_symbol,
                "is_mitocarta": bool(is_mitocarta),
                "is_mtdna_protein_coding": bool(is_mtdna_protein),
            }
        )

    annotation = pd.DataFrame(annotation_rows).sort_values("feature_index")
    feature_checksum = sha256_strings(annotation["source_symbol"])
    feature_order = annotation[["feature_index", "source_symbol"]].copy()
    feature_order["feature_order_sha256"] = feature_checksum
    aliases_used = pd.DataFrame(
        alias_rows,
        columns=["source_symbol", "approved_symbol", "alias_type"],
    )
    ambiguities = pd.DataFrame(
        ambiguity_rows,
        columns=["source_symbol", "ambiguity_type", "candidate_symbols"],
    )

    checks = [
        ("feature_count", len(annotation) == expected_genes, len(annotation), expected_genes, ""),
        ("source_symbols_unique", annotation["source_symbol"].is_unique, annotation["source_symbol"].nunique(), expected_genes, ""),
        ("feature_indices_contiguous", annotation["feature_index"].tolist() == list(range(expected_genes)), str((annotation["feature_index"].min(), annotation["feature_index"].max())), f"0..{expected_genes-1}", ""),
        ("feature_order_checksum_nonempty", len(feature_checksum) == 64, feature_checksum, "SHA-256", ""),
        ("matrix_identity_preserved", annotation["source_symbol"].tolist() == raw["source_symbol"].tolist(), True, True, ""),
        ("mtdna_protein_gene_count", int(annotation["is_mtdna_protein_coding"].sum()) == 13, int(annotation["is_mtdna_protein_coding"].sum()), 13, ""),
        ("mitocarta_reference_nonempty", int(annotation["is_mitocarta"].sum()) > 0, int(annotation["is_mitocarta"].sum()), ">0", ""),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "master": output_dir / "gene_annotation_master.tsv",
        "aliases": output_dir / "gene_aliases_used.tsv",
        "ambiguities": output_dir / "gene_mapping_ambiguities.tsv",
        "order": output_dir / "feature_order.tsv",
        "checks": output_dir / "gene_checks.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(annotation, paths["master"])
    atomic_write_tsv(aliases_used, paths["aliases"])
    atomic_write_tsv(ambiguities, paths["ambiguities"])
    atomic_write_tsv(feature_order, paths["order"])
    atomic_write_tsv(checks_table, paths["checks"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH03",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        features=len(annotation),
        approved_exact=int(annotation["hgnc_match_type"].eq("exact").sum()),
        approved_alias=int(annotation["hgnc_match_type"].eq("alias").sum()),
        ambiguous_mappings=len(ambiguities),
        mitocarta_features=int(annotation["is_mitocarta"].sum()),
        mtdna_protein_features=int(annotation["is_mtdna_protein_coding"].sum()),
        feature_order_sha256=feature_checksum,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH03 status: {validation_status}; feature checksum: {feature_checksum}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
