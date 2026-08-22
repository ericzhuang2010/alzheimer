#!/usr/bin/env python3
"""Extract sparse ancestry-matched LD blocks for the four GWAS-signal loci."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
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
        writer = csv.DictWriter(
            handle, delimiter="\t", fieldnames=fields, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def deterministic_writer(path: Path) -> tuple[io.TextIOWrapper, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline=""), raw


def checksum(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def allele_key(position: int, allele1: str, allele2: str) -> tuple[int, str, str]:
    first, second = sorted((allele1.upper(), allele2.upper()))
    return position, first, second


def canonical(chromosome: str, position: int, ref: str, alt: str) -> str:
    return f"chr{chromosome}_{position}_{ref.upper()}_{alt.upper()}"


def load_gwas_by_locus(
    path: Path, loci: list[dict[str, Any]]
) -> dict[str, dict[tuple[int, str, str], dict[str, str]]]:
    lookup: dict[str, dict[tuple[int, str, str], dict[str, str]]] = {
        locus["locus_id"]: {} for locus in loci
    }
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            chromosome = row["chromosome"].removeprefix("chr")
            position = int(row["position"])
            for locus in loci:
                if (
                    chromosome == locus["chromosome"]
                    and locus["window_start"] <= position <= locus["window_end"]
                    and row["gene"] == locus["gene"]
                ):
                    key = allele_key(
                        position, row["effect_allele"], row["other_allele"]
                    )
                    previous = lookup[locus["locus_id"]].get(key)
                    if previous is None or float(row["p_value"]) < float(previous["p_value"]):
                        lookup[locus["locus_id"]][key] = row
    return lookup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="config/phase19_genetic_support_tier2_recovery.yml"
    )
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    route_path = resolve(inputs["source_manifest_dir"]) / "recovery_route_manifest.tsv"
    signal_routes = [
        row for row in read_tsv(route_path) if row["gwas_signal_present"] == "TRUE"
    ]
    unique: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in signal_routes:
        key = (row["gene"], row["chromosome"], row["window_start"], row["window_end"])
        if key not in unique:
            unique[key] = {
                "schema_version": SCHEMA,
                "locus_id": f"{row['gene']}_chr{row['chromosome']}_{row['window_start']}_{row['window_end']}",
                "gene": row["gene"],
                "ensembl_gene_id": row["ensembl_gene_id"],
                "chromosome": row["chromosome"].removeprefix("chr"),
                "window_start": int(row["window_start"]),
                "window_end": int(row["window_end"]),
            }
    loci = sorted(unique.values(), key=lambda x: (int(x["chromosome"]), x["window_start"]))
    gwas = load_gwas_by_locus(resolve(inputs["candidate_gwas"]), loci)
    block_dir = resolve(inputs["ld_candidate_blocks_dir"])
    source_dir = resolve(inputs["ld_source_dir"])
    manifest_dir = resolve(inputs["source_manifest_dir"])
    summary: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []

    source_by_chromosome = {
        str(source["chromosome"]): source for source in config["ld_sources"]
    }
    qtl_summary_path = manifest_dir / "recovery_qtl_model_extraction_summary.tsv"
    if qtl_summary_path.exists():
        qtl_rows = read_tsv(qtl_summary_path)
        qtl_signal_genes = {
            row["gene"]
            for row in qtl_rows
            if int(row["credible_set_rows"]) > 0
        }
        required_genes = {locus["gene"] for locus in loci}
        if not required_genes.intersection(qtl_signal_genes):
            for locus in loci:
                summary.append(
                    {
                        "schema_version": SCHEMA,
                        "locus_id": locus["locus_id"],
                        "gene": locus["gene"],
                        "chromosome": locus["chromosome"],
                        "window_start": locus["window_start"],
                        "window_end": locus["window_end"],
                        "source_panel": config["source_release"]["niagads_panel"],
                        "source_sample_size": config["source_release"]["niagads_panel_sample_size"],
                        "source_build": config["source_release"]["niagads_panel_build"],
                        "source_retention_rule": "within_5Mb_and_abs_R_gt_0.2",
                        "candidate_gwas_variants": len(gwas[locus["locus_id"]]),
                        "ld_observed_variants": 0,
                        "ld_observed_edges": 0,
                        "missing_pair_policy": "not_applicable_after_qtl_model_gate",
                        "extraction_state": "not_required_after_qtl_model_gate",
                        "reason": "no_released_qtl_susie_signal_model_and_no_qtl_ancestry_matched_ld_for_dense_signals",
                    }
                )
            summary_fields = [
                "schema_version", "locus_id", "gene", "chromosome", "window_start",
                "window_end", "source_panel", "source_sample_size", "source_build",
                "source_retention_rule", "candidate_gwas_variants", "ld_observed_variants",
                "ld_observed_edges", "missing_pair_policy", "extraction_state", "reason",
            ]
            write_tsv(manifest_dir / "recovery_ld_extraction_summary.tsv", summary, summary_fields)
            write_tsv(
                manifest_dir / "recovery_ld_block_artifacts.tsv", [],
                ["schema_version", "locus_id", "role", "path", "rows", "sha256"],
            )
            print("Skipped LD extraction after the compatible QTL model/LD gate")
            return
    for chromosome in sorted({locus["chromosome"] for locus in loci}, key=int):
        source = source_by_chromosome[chromosome]
        source_path = source_dir / source["filename"]
        if source_path.stat().st_size != int(source["bytes"]):
            raise RuntimeError(f"Incomplete LD source: {source_path}")
        chromosome_loci = [locus for locus in loci if locus["chromosome"] == chromosome]
        outputs: dict[str, dict[str, Any]] = {}
        for locus in chromosome_loci:
            edge_path = block_dir / f"{locus['locus_id']}.ld_edges.tsv.gz"
            temporary = edge_path.with_suffix(edge_path.suffix + ".tmp")
            handle, raw = deterministic_writer(temporary)
            fields = [
                "variant1", "variant2", "chromosome", "position1", "position2",
                "ref1", "alt1", "ref2", "alt2", "r", "r2",
            ]
            writer = csv.DictWriter(
                handle, delimiter="\t", fieldnames=fields, lineterminator="\n"
            )
            writer.writeheader()
            outputs[locus["locus_id"]] = {
                "locus": locus,
                "path": edge_path,
                "temporary": temporary,
                "handle": handle,
                "raw": raw,
                "writer": writer,
                "edges": 0,
                "variants": {},
            }

        with gzip.open(source_path, "rt", encoding="utf-8") as handle:
            header = next(handle).strip().lstrip("#").split()
            expected = [
                "CHR", "POS1", "RSID1", "REF:ALT1", "POS2", "RSID2",
                "REF:ALT2", "R", "Rsq", "D", "Dprime",
            ]
            if header != expected:
                raise RuntimeError(f"Unexpected LD header in {source_path}: {header}")
            for line_number, line in enumerate(handle, start=2):
                values = line.split()
                if len(values) != 11:
                    raise RuntimeError(
                        f"Malformed LD row {line_number} in {source_path}: {len(values)} fields"
                    )
                row_chromosome, pos1_text, _rsid1, alleles1, pos2_text, _rsid2, alleles2, r, r2, _d, _dprime = values
                row_chromosome = row_chromosome.removeprefix("chr")
                if row_chromosome != chromosome:
                    raise RuntimeError(f"Chromosome drift in {source_path}: {row_chromosome}")
                pos1, pos2 = int(pos1_text), int(pos2_text)
                ref1, alt1 = alleles1.split(":", 1)
                ref2, alt2 = alleles2.split(":", 1)
                key1 = allele_key(pos1, ref1, alt1)
                key2 = allele_key(pos2, ref2, alt2)
                for output in outputs.values():
                    locus = output["locus"]
                    if not (
                        locus["window_start"] <= pos1 <= locus["window_end"]
                        and locus["window_start"] <= pos2 <= locus["window_end"]
                    ):
                        continue
                    locus_gwas = gwas[locus["locus_id"]]
                    if key1 not in locus_gwas or key2 not in locus_gwas:
                        continue
                    variant1 = canonical(chromosome, pos1, ref1, alt1)
                    variant2 = canonical(chromosome, pos2, ref2, alt2)
                    output["writer"].writerow(
                        {
                            "variant1": variant1,
                            "variant2": variant2,
                            "chromosome": chromosome,
                            "position1": pos1,
                            "position2": pos2,
                            "ref1": ref1,
                            "alt1": alt1,
                            "ref2": ref2,
                            "alt2": alt2,
                            "r": r,
                            "r2": r2,
                        }
                    )
                    output["edges"] += 1
                    output["variants"][variant1] = (pos1, ref1, alt1, key1)
                    output["variants"][variant2] = (pos2, ref2, alt2, key2)

        for output in outputs.values():
            output["handle"].close()
            output["raw"].close()
            output["temporary"].replace(output["path"])
            locus = output["locus"]
            variant_path = block_dir / f"{locus['locus_id']}.variant_map.tsv.gz"
            variant_rows: list[dict[str, Any]] = []
            for variant, (position, ref, alt, key) in sorted(
                output["variants"].items(), key=lambda item: (item[1][0], item[0])
            ):
                gwas_row = gwas[locus["locus_id"]][key]
                beta = float(gwas_row["beta"])
                effect = gwas_row["effect_allele"].upper()
                other = gwas_row["other_allele"].upper()
                if effect == alt.upper() and other == ref.upper():
                    beta_ld_alt = beta
                    alignment = "effect_is_ld_alt"
                elif effect == ref.upper() and other == alt.upper():
                    beta_ld_alt = -beta
                    alignment = "effect_is_ld_ref_beta_flipped"
                else:
                    raise RuntimeError(f"Allele matching error for {variant}")
                variant_rows.append(
                    {
                        "variant": variant,
                        "chromosome": locus["chromosome"],
                        "position": position,
                        "ld_ref": ref,
                        "ld_alt": alt,
                        "gwas_variant_id": gwas_row["variant_id"],
                        "gwas_effect_allele": effect,
                        "gwas_other_allele": other,
                        "gwas_beta_original": gwas_row["beta"],
                        "gwas_beta_ld_alt": f"{beta_ld_alt:.17g}",
                        "gwas_standard_error": gwas_row["standard_error"],
                        "gwas_p_value": gwas_row["p_value"],
                        "alignment": alignment,
                    }
                )
            variant_fields = [
                "variant", "chromosome", "position", "ld_ref", "ld_alt",
                "gwas_variant_id", "gwas_effect_allele", "gwas_other_allele",
                "gwas_beta_original", "gwas_beta_ld_alt", "gwas_standard_error",
                "gwas_p_value", "alignment",
            ]
            temporary = variant_path.with_suffix(variant_path.suffix + ".tmp")
            writer_handle, writer_raw = deterministic_writer(temporary)
            writer = csv.DictWriter(
                writer_handle, delimiter="\t", fieldnames=variant_fields, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(variant_rows)
            writer_handle.close()
            writer_raw.close()
            temporary.replace(variant_path)
            summary.append(
                {
                    "schema_version": SCHEMA,
                    "locus_id": locus["locus_id"],
                    "gene": locus["gene"],
                    "chromosome": locus["chromosome"],
                    "window_start": locus["window_start"],
                    "window_end": locus["window_end"],
                    "source_panel": config["source_release"]["niagads_panel"],
                    "source_sample_size": config["source_release"]["niagads_panel_sample_size"],
                    "source_build": config["source_release"]["niagads_panel_build"],
                    "source_retention_rule": "within_5Mb_and_abs_R_gt_0.2",
                    "candidate_gwas_variants": len(gwas[locus["locus_id"]]),
                    "ld_observed_variants": len(variant_rows),
                    "ld_observed_edges": output["edges"],
                    "missing_pair_policy": "zero_from_published_abs_R_gt_0.2_sparse_release",
                    "extraction_state": "prepared_after_qtl_signal_gate",
                    "reason": "ancestry_matched_candidate_block_extracted",
                }
            )
            for role, path, rows in (
                ("candidate_ld_edges", output["path"], output["edges"]),
                ("candidate_ld_variant_map", variant_path, len(variant_rows)),
            ):
                artifacts.append(
                    {
                        "schema_version": SCHEMA,
                        "locus_id": locus["locus_id"],
                        "role": role,
                        "path": path.relative_to(ROOT).as_posix(),
                        "rows": rows,
                        "sha256": checksum(path),
                    }
                )

    write_tsv(
        manifest_dir / "recovery_ld_extraction_summary.tsv",
        summary,
        [
            "schema_version", "locus_id", "gene", "chromosome", "window_start",
            "window_end", "source_panel", "source_sample_size", "source_build",
            "source_retention_rule", "candidate_gwas_variants", "ld_observed_variants",
            "ld_observed_edges", "missing_pair_policy", "extraction_state", "reason",
        ],
    )
    write_tsv(
        manifest_dir / "recovery_ld_block_artifacts.tsv",
        artifacts,
        ["schema_version", "locus_id", "role", "path", "rows", "sha256"],
    )
    print(f"Prepared {len(summary)} sparse LD blocks from {len(source_by_chromosome)} registered sources")


if __name__ == "__main__":
    main()
