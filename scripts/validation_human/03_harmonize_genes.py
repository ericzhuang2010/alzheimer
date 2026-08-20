#!/usr/bin/env python3
"""VH03: preserve SEA-AD feature identity and freeze current/mitochondrial mapping."""

from __future__ import annotations

import gzip
import io
import re
import subprocess
from collections import defaultdict

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_dir,
    repo_path,
    require_phase,
    sha256_file,
    sha256_strings,
    status_frame,
    utc_now,
    write_artifacts,
)


ATTRIBUTE = re.compile(r'([A-Za-z0-9_]+) "([^"]*)"')


def split_aliases(value):
    if value is None or pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def read_gencode(path):
    records = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip(chr(10)).split(chr(9))
            if len(fields) != 9 or fields[2] != "gene":
                continue
            attrs = dict(ATTRIBUTE.findall(fields[8]))
            symbol = attrs.get("gene_name")
            gene_id = attrs.get("gene_id", "").split(".")[0]
            if symbol and gene_id:
                records[symbol].add((gene_id, fields[0], attrs.get("gene_type", "")))
    return records


def read_mitocarta(path):
    expression = (
        'x<-readxl::read_excel(commandArgs(TRUE)[1],sheet="A Human MitoCarta3.0");'
        'x<-x[,c("Symbol","Synonyms")];'
        'write.table(x,file="",sep="\t",row.names=FALSE,quote=FALSE,na="")'
    )
    result = subprocess.run(
        ["Rscript", "-e", expression, str(path)],
        capture_output=True, text=True, check=True,
    )
    frame = pd.read_csv(io.StringIO(result.stdout), sep="	", dtype=str, keep_default_na=False)
    canonical = set(frame["Symbol"])
    alias_targets = defaultdict(set)
    for row in frame.itertuples(index=False):
        for alias in split_aliases(row.Synonyms):
            alias_targets[alias].add(row.Symbol)
    aliases = {alias: next(iter(values)) for alias, values in alias_targets.items() if len(values) == 1}
    return canonical, aliases


def bool_text(value):
    return str(value).strip().upper() == "TRUE"


def main() -> int:
    args = parse_config_cli("VH03: harmonize SEA-AD genes")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    vh01 = require_phase(output_root, "01_audit")
    output_dir = phase_dir(output_root, "03_genes")
    raw = pd.read_csv(output_root / "01_audit/gene_inventory_raw.tsv", sep="	", dtype=str)
    raw["feature_index"] = raw["feature_index"].astype(int)
    expected = config["expected_identity"]

    hgnc_path = repo_path(project_root, config["references"]["hgnc_complete_set"])
    gencode_path = repo_path(project_root, config["references"]["gencode_gtf"])
    mitocarta_path = repo_path(project_root, config["references"]["mitocarta_workbook"])
    phase18_path = repo_path(project_root, config["references"]["phase18_gene_annotation"])

    hgnc = pd.read_csv(hgnc_path, sep="	", dtype=str, low_memory=False)
    hgnc = hgnc.loc[hgnc["status"].eq("Approved")].copy()
    hgnc_exact = hgnc.drop_duplicates("symbol").set_index("symbol")
    alias_targets = defaultdict(set)
    for row in hgnc.itertuples(index=False):
        for column in ["alias_symbol", "prev_symbol"]:
            for alias in split_aliases(getattr(row, column)):
                alias_targets[alias].add(row.symbol)
    unique_hgnc_alias = {alias: next(iter(values)) for alias, values in alias_targets.items() if len(values) == 1}
    ambiguous_hgnc_alias = {alias: sorted(values) for alias, values in alias_targets.items() if len(values) > 1}

    gencode = read_gencode(gencode_path)
    mito_symbols, mito_aliases = read_mitocarta(mitocarta_path)
    phase18_columns = [
        "feature_id_original", "symbol_original", "symbol_hgnc_current",
        "hgnc_id", "ensembl_id_stable", "mapping_status", "chromosome",
        "gene_type", "is_mitocarta3", "is_mtDNA_gene",
    ]
    phase18 = pd.read_csv(phase18_path, sep="	", usecols=phase18_columns, dtype=str)
    phase18_by_source = {}
    phase18_conflicts = []
    for source, group in phase18.groupby("symbol_original", sort=False):
        current = sorted(set(group["symbol_hgnc_current"].dropna()))
        core = sorted(set(group["is_mitocarta3"].dropna()))
        mtdna = sorted(set(group["is_mtDNA_gene"].dropna()))
        stable = sorted(set(group["ensembl_id_stable"].dropna()))
        chromosome = sorted(set(group["chromosome"].dropna()))
        gene_type = sorted(set(group["gene_type"].dropna()))
        hgnc_ids = sorted(set(group["hgnc_id"].dropna()))
        if len(current) > 1 or len(core) > 1 or len(mtdna) > 1:
            phase18_conflicts.append({
                "source_symbol": source,
                "ambiguity_type": "phase18_identity_or_core_conflict",
                "candidate_symbols": "|".join(current),
                "candidate_core_values": "|".join(core),
            })
        phase18_by_source[source] = {
            "current": current[0] if len(current) == 1 else None,
            "core": bool_text(core[0]) if len(core) == 1 else None,
            "mtdna": bool_text(mtdna[0]) if len(mtdna) == 1 else None,
            "stable": stable[0] if len(stable) == 1 else None,
            "chromosome": chromosome[0] if len(chromosome) == 1 else None,
            "gene_type": gene_type[0] if len(gene_type) == 1 else None,
            "hgnc_id": hgnc_ids[0] if len(hgnc_ids) == 1 else None,
        }

    annotations = []
    aliases_used = []
    ambiguities = list(phase18_conflicts)
    for record in raw.itertuples(index=False):
        source = record.source_symbol
        approved = None
        hgnc_method = "unresolved"
        if source in hgnc_exact.index:
            approved = source
            hgnc_method = "exact"
        elif source in unique_hgnc_alias:
            approved = unique_hgnc_alias[source]
            hgnc_method = "unique_alias"
            aliases_used.append({"source_symbol": source, "approved_symbol": approved, "alias_source": "HGNC"})
        elif source in ambiguous_hgnc_alias:
            hgnc_method = "ambiguous_alias"
            ambiguities.append({
                "source_symbol": source,
                "ambiguity_type": "HGNC_alias",
                "candidate_symbols": "|".join(ambiguous_hgnc_alias[source]),
                "candidate_core_values": "",
            })

        phase = phase18_by_source.get(source)
        phase_current = phase["current"] if phase else None
        current = phase_current or approved
        mapping_status = "phase18_exact" if phase_current else (
            hgnc_method if approved else "unresolved"
        )
        identity_conflict = bool(phase_current and approved and phase_current != approved)
        if identity_conflict:
            ambiguities.append({
                "source_symbol": source,
                "ambiguity_type": "phase18_hgnc_disagreement",
                "candidate_symbols": f"{phase_current}|{approved}",
                "candidate_core_values": "",
            })

        gencode_symbol = current or approved or source
        gencode_candidates = sorted(gencode.get(gencode_symbol, set()))
        stable = phase["stable"] if phase and phase["stable"] else None
        chromosome = phase["chromosome"] if phase and phase["chromosome"] else None
        gene_type = phase["gene_type"] if phase and phase["gene_type"] else None
        gencode_method = "phase18"
        if not stable:
            if len(gencode_candidates) == 1:
                stable, chromosome, gene_type = gencode_candidates[0]
                gencode_method = "unique_symbol"
            elif len(gencode_candidates) > 1:
                gencode_method = "ambiguous_symbol"
                ambiguities.append({
                    "source_symbol": source,
                    "ambiguity_type": "GENCODE_symbol",
                    "candidate_symbols": "|".join(item[0] for item in gencode_candidates),
                    "candidate_core_values": "",
                })
            else:
                gencode_method = "unresolved"

        mito_current = None
        if current in mito_symbols:
            mito_current = current
        elif source in mito_symbols:
            mito_current = source
        elif source in mito_aliases:
            mito_current = mito_aliases[source]
        reference_core = mito_current is not None
        if phase and phase["core"] is not None:
            core = phase["core"]
            annotation_status = "phase18_exact"
            core_disagreement = core != reference_core
        else:
            core = reference_core
            annotation_status = "mitocarta_reference_fallback"
            core_disagreement = False
        if core_disagreement:
            ambiguities.append({
                "source_symbol": source,
                "ambiguity_type": "phase18_mitocarta_disagreement",
                "candidate_symbols": current or "",
                "candidate_core_values": f"phase18={core}|workbook={reference_core}",
            })

        hgnc_id = phase["hgnc_id"] if phase and phase["hgnc_id"] else (
            hgnc_exact.loc[approved, "hgnc_id"] if approved in hgnc_exact.index else None
        )
        annotations.append({
            "feature_index": int(record.feature_index),
            "source_symbol": source,
            "embedded_gene_id": record.embedded_gene_id,
            "approved_symbol": approved,
            "current_symbol_for_kda": current,
            "hgnc_id": hgnc_id,
            "ensembl_id": stable,
            "chromosome": chromosome,
            "gene_type": gene_type,
            "mapping_status": mapping_status,
            "hgnc_mapping_method": hgnc_method,
            "gencode_mapping_method": gencode_method,
            "phase18_annotation_status": annotation_status,
            "mitocarta_canonical_symbol": mito_current,
            "is_core_mito_phase18": bool(core),
            "is_mtdna_gene": bool(phase["mtdna"]) if phase and phase["mtdna"] is not None else bool(chromosome == "chrM"),
            "phase18_hgnc_identity_conflict": identity_conflict,
            "phase18_mitocarta_conflict": core_disagreement,
        })

    annotation = pd.DataFrame(annotations).sort_values("feature_index")
    aliases = pd.DataFrame(aliases_used, columns=["source_symbol", "approved_symbol", "alias_source"])
    ambiguity = pd.DataFrame(ambiguities, columns=["source_symbol", "ambiguity_type", "candidate_symbols", "candidate_core_values"])
    feature_sha = sha256_strings(annotation["source_symbol"])
    feature_order = annotation[["feature_index", "source_symbol"]].copy()
    feature_order["feature_order_sha256"] = feature_sha
    references = pd.DataFrame([
        {"reference": name, "path": config["references"][name], "bytes": repo_path(project_root, value).stat().st_size, "sha256": sha256_file(repo_path(project_root, value))}
        for name, value in config["references"].items()
    ])

    query_blocking = annotation["phase18_hgnc_identity_conflict"] | annotation["phase18_mitocarta_conflict"]
    checks = [
        ("feature_count", len(annotation) == expected["features"], len(annotation), expected["features"], ""),
        ("feature_indices_contiguous", annotation["feature_index"].tolist() == list(range(expected["features"])), f"{annotation['feature_index'].min()}..{annotation['feature_index'].max()}", f"0..{expected['features']-1}", ""),
        ("source_symbols_unique", annotation["source_symbol"].is_unique, annotation["source_symbol"].nunique(), expected["features"], ""),
        ("matrix_order_preserved", feature_sha == str(vh01.loc[0, "feature_order_sha256"]), feature_sha, str(vh01.loc[0, "feature_order_sha256"]), ""),
        ("reference_hashes_frozen", all(references.set_index("reference").loc[name, "sha256"] == config["expected_reference_sha256"][name] for name in config["references"]), True, True, ""),
        ("phase18_internal_conflicts", len(phase18_conflicts) == 0, len(phase18_conflicts), 0, ""),
        ("query_membership_conflicts", int(query_blocking.sum()) == 0, int(query_blocking.sum()), 0, ""),
        ("core_mito_annotation_nonempty", int(annotation["is_core_mito_phase18"].sum()) > 0, int(annotation["is_core_mito_phase18"].sum()), ">0", ""),
        ("mtdna_gene_count", int(annotation["is_mtdna_gene"].sum()) == 13, int(annotation["is_mtdna_gene"].sum()), 13, "Phase 18 mtDNA flag among SEA-AD source features"),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "master": output_dir / "gene_annotation_master.tsv",
        "aliases": output_dir / "gene_aliases_used.tsv",
        "ambiguity": output_dir / "gene_mapping_ambiguities.tsv",
        "order": output_dir / "feature_order.tsv",
        "references": output_dir / "reference_identity.tsv",
        "checks": output_dir / "gene_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    for frame, key in [(annotation, "master"), (aliases, "aliases"), (ambiguity, "ambiguity"), (feature_order, "order"), (references, "references"), (checks_table, "checks")]:
        atomic_write_tsv(frame, paths[key])
    write_artifacts([paths[key] for key in ["master", "aliases", "ambiguity", "order", "references", "checks"]], project_root, paths["artifacts"])
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH03", state, project_root, config_path, started, failed,
        features=len(annotation), current_symbols=int(annotation["current_symbol_for_kda"].notna().sum()),
        phase18_exact=int(annotation["phase18_annotation_status"].eq("phase18_exact").sum()),
        mitocarta_fallback=int(annotation["phase18_annotation_status"].eq("mitocarta_reference_fallback").sum()),
        core_mito_features=int(annotation["is_core_mito_phase18"].sum()),
        feature_order_sha256=feature_sha,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH03 status: {state}; current symbols={annotation['current_symbol_for_kda'].notna().sum()}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
