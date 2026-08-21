#!/usr/bin/env python3
"""Extract Phase 19 candidate rows from frozen public Tier 2 source files."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import re
import tarfile
from contextlib import contextmanager
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
QTL_COLUMNS = [
    "gene", "ensembl_gene_id", "qtl_type", "source_modality", "context",
    "cohort", "chromosome", "position", "variant_id", "ref", "alt", "pip",
    "conditional_effect", "credible_set_95", "credible_set_70", "credible_set_50",
    "non_ref_af", "qtl_distance_to_target", "signal_id", "source_archive",
    "source_member",
]
GWAS_COLUMNS = [
    "gene", "ensembl_gene_id", "chromosome", "window_start", "window_end",
    "variant_id", "position", "effect_allele", "other_allele",
    "effect_allele_frequency", "beta", "standard_error", "p_value", "odds_ratio",
    "n_cases", "n_controls", "source_accession",
]


@contextmanager
def deterministic_gzip_writer(path: Path):
    """Write text gzip with a stable header for reproducible SHA-256 values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                yield text


def tier1_genes_and_loci(config: dict) -> tuple[set[str], dict[str, list[dict]]]:
    manifest = ROOT / config["inputs"]["tier1_candidate_manifest"]
    with manifest.open(newline="") as handle:
        candidates = list(csv.DictReader(handle, delimiter="\t"))
    genes = {row["gene"] for row in candidates if row["is_mtdna_gene"].lower() != "true"}
    loci_path = ROOT / config["inputs"]["tier1_candidate_loci"]
    by_chromosome: dict[str, list[dict]] = {}
    with loci_path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["gene"] not in genes:
                continue
            row["window_start"] = int(row["window_start"])
            row["window_end"] = int(row["window_end"])
            by_chromosome.setdefault(row["chromosome"].removeprefix("chr"), []).append(row)
    return genes, by_chromosome


def parse_target_info(text: str) -> dict[str, str]:
    values = {}
    for item in text.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value
    return values


def extract_qtl(config: dict, genes: set[str], output: Path) -> int:
    qtl_dir = ROOT / config["inputs"]["niagads_qtl_dir"]
    archives = [
        source for source in config["alternative_sources"]
        if source["dataset_id"].endswith("finemapping_all")
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with deterministic_gzip_writer(output) as handle:
        writer = csv.DictWriter(handle, fieldnames=QTL_COLUMNS, delimiter="\t")
        writer.writeheader()
        for source in archives:
            archive = qtl_dir / source["filename"]
            if not archive.exists():
                raise FileNotFoundError(archive)
            modality = (
                "snuc-eQTL" if "snuc-eQTL" in source["filename"] else
                "sQTL" if ".sQTL." in source["filename"] else "eQTL"
            )
            qtl_type = "sQTL" if modality == "sQTL" else "eQTL"
            with tarfile.open(archive, "r") as tar:
                for member in tar:
                    if not member.isfile() or not member.name.endswith(".bed.gz"):
                        continue
                    raw = tar.extractfile(member)
                    if raw is None:
                        continue
                    cohort = member.name.split("/")[2]
                    with gzip.GzipFile(fileobj=raw) as compressed:
                        text = (line.decode("utf-8") for line in compressed)
                        reader = csv.DictReader(text, delimiter="\t")
                        if reader.fieldnames:
                            reader.fieldnames = [name.removeprefix("#") for name in reader.fieldnames]
                        for row in reader:
                            gene = row.get("target_gene_symbol", "")
                            if gene not in genes:
                                continue
                            info = parse_target_info(row.get("user_input", ""))
                            context = info.get("xQTL_context_id", "")
                            signal = info.get("event_ID", row.get("target", ""))
                            writer.writerow({
                                "gene": gene,
                                "ensembl_gene_id": row.get("target_ensembl_id", ""),
                                "qtl_type": qtl_type,
                                "source_modality": modality,
                                "context": context,
                                "cohort": cohort,
                                "chromosome": row.get("chrom", "").removeprefix("chr"),
                                "position": row.get("chromEnd", ""),
                                "variant_id": row.get("variant_id", ""),
                                "ref": row.get("ref", ""),
                                "alt": row.get("alt", ""),
                                "pip": row.get("PIP", ""),
                                "conditional_effect": row.get("conditional_effect", ""),
                                "credible_set_95": row.get("cs_95", ""),
                                "credible_set_70": row.get("cs_70", ""),
                                "credible_set_50": row.get("cs_50", ""),
                                "non_ref_af": row.get("non_ref_af", ""),
                                "qtl_distance_to_target": row.get("qtl_dist_to_target", ""),
                                "signal_id": signal,
                                "source_archive": source["filename"],
                                "source_member": member.name,
                            })
                            count += 1
    return count


def extract_gwas(config: dict, loci: dict[str, list[dict]], output: Path) -> int:
    gwas_dir = ROOT / config["inputs"]["gwas_catalog_dir"]
    source = next(x for x in config["alternative_sources"] if x["dataset_id"] == "Bellenguez2022_AD_GWAS")
    path = gwas_dir / source["filename"]
    if not path.exists():
        raise FileNotFoundError(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "rt", newline="") as input_handle, deterministic_gzip_writer(output) as output_handle:
        reader = csv.DictReader(input_handle, delimiter="\t")
        writer = csv.DictWriter(output_handle, fieldnames=GWAS_COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in reader:
            chromosome = row["chromosome"].removeprefix("chr")
            candidate_loci = loci.get(chromosome)
            if not candidate_loci:
                continue
            try:
                position = int(row["base_pair_location"])
            except (TypeError, ValueError):
                continue
            for locus in candidate_loci:
                if locus["window_start"] <= position <= locus["window_end"]:
                    writer.writerow({
                        "gene": locus["gene"],
                        "ensembl_gene_id": locus["ensembl_gene_id"],
                        "chromosome": chromosome,
                        "window_start": locus["window_start"],
                        "window_end": locus["window_end"],
                        "variant_id": row["variant_id"],
                        "position": position,
                        "effect_allele": row["effect_allele"],
                        "other_allele": row["other_allele"],
                        "effect_allele_frequency": row["effect_allele_frequency"],
                        "beta": row["beta"],
                        "standard_error": row["standard_error"],
                        "p_value": row["p_value"],
                        "odds_ratio": row["odds_ratio"],
                        "n_cases": row["n_cases"],
                        "n_controls": row["n_controls"],
                        "source_accession": source["accession"],
                    })
                    count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase19_genetic_support_tier2.yml")
    parser.add_argument("--qtl-only", action="store_true")
    parser.add_argument("--gwas-only", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / args.config).read_text())
    genes, loci = tier1_genes_and_loci(config)
    output_dir = ROOT / config["inputs"]["regional_inputs_dir"]
    if not args.gwas_only:
        count = extract_qtl(config, genes, output_dir / "ng00184_candidate_qtl_finemapping.tsv.gz")
        print(f"wrote {count} candidate QTL fine-mapping rows")
    if not args.qtl_only:
        count = extract_gwas(config, loci, output_dir / "bellenguez_candidate_gwas.tsv.gz")
        print(f"wrote {count} candidate-region GWAS rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
