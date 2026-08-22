#!/usr/bin/env python3
"""Prepare and run the three preregistered Phase 19 MAGMA analyses locally."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_pvalue_file(source: Path, destination: Path) -> tuple[int, int]:
    """Write MAGMA's SNP/P format without loading a complete GWAS into memory."""
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    accepted = 0
    rejected = 0
    with gzip.open(source, "rt", newline="", encoding="utf-8") as input_handle, temporary.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        reader = csv.DictReader(input_handle, delimiter="\t")
        required = {"rsid", "p_value"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"Missing {required} in {source}")
        writer = csv.writer(output_handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["SNP", "P"])
        for row in reader:
            rsid = row["rsid"]
            try:
                p_value = float(row["p_value"])
            except (TypeError, ValueError):
                rejected += 1
                continue
            if not rsid.startswith("rs") or not 0 <= p_value <= 1:
                rejected += 1
                continue
            writer.writerow([rsid, row["p_value"]])
            accepted += 1
    temporary.replace(destination)
    return accepted, rejected


def run_logged(command: list[str], log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if completed.returncode:
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:])
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{tail}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase19_endophenotype_gwas_qtl_extension.yml")
    parser.add_argument("--force-pvalues", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    inputs = config["inputs"]
    binary = resolve(inputs["magma_binary"])
    reference = resolve(inputs["magma_reference_prefix"])
    gene_locations = resolve(inputs["magma_gene_locations"])
    work = resolve(inputs["work_dir"]) / "magma"
    work.mkdir(parents=True, exist_ok=True)

    required = [binary, gene_locations]
    required.extend(Path(str(reference) + f".{suffix}") for suffix in ("bed", "bim", "fam"))
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Missing MAGMA inputs: {missing}")

    annotation_prefix = work / "g1000_eur_official_ensembl_v110"
    annotation = Path(str(annotation_prefix) + ".genes.annot")
    if not annotation.exists():
        run_logged(
            [
                str(binary), "--annotate",
                "--snp-loc", str(reference) + ".bim",
                "--gene-loc", str(gene_locations),
                "--out", str(annotation_prefix),
            ],
            work / "annotation.log",
        )

    sensitivity_annotation_prefix = work / "g1000_eur_official_ensembl_v110_window10kb"
    sensitivity_annotation = Path(str(sensitivity_annotation_prefix) + ".genes.annot")
    if not sensitivity_annotation.exists():
        run_logged(
            [
                str(binary), "--annotate", "window=10,10",
                "--snp-loc", str(reference) + ".bim",
                "--gene-loc", str(gene_locations),
                "--out", str(sensitivity_annotation_prefix),
            ],
            work / "annotation.window10kb.log",
        )

    inventory_rows: list[dict[str, object]] = []
    for trait in config["biomarkers"]:
        trait_id = trait["trait_id"]
        source = resolve(trait["harmonized_file"])
        pvalue_file = work / f"{trait_id}.pval.tsv"
        if args.force_pvalues or not pvalue_file.exists():
            accepted, rejected = make_pvalue_file(source, pvalue_file)
        else:
            accepted = max(sum(1 for _ in pvalue_file.open(encoding="utf-8")) - 1, 0)
            rejected = -1
        output_prefix = work / trait_id
        run_logged(
            [
                str(binary),
                "--bfile", str(reference),
                "--pval", str(pvalue_file), f"N={trait['sample_size']}", "duplicate=first",
                "--gene-annot", str(annotation),
                "--genes-only",
                "--out", str(output_prefix),
            ],
            work / f"{trait_id}.magma.log",
        )
        genes_out = Path(str(output_prefix) + ".genes.out")
        sensitivity_output_prefix = work / f"{trait_id}.window10kb"
        run_logged(
            [
                str(binary),
                "--bfile", str(reference),
                "--pval", str(pvalue_file), f"N={trait['sample_size']}", "duplicate=first",
                "--gene-annot", str(sensitivity_annotation),
                "--genes-only",
                "--out", str(sensitivity_output_prefix),
            ],
            work / f"{trait_id}.window10kb.magma.log",
        )
        sensitivity_genes_out = Path(str(sensitivity_output_prefix) + ".genes.out")
        inventory_rows.append({
            "trait_id": trait_id,
            "pvalue_rows": accepted,
            "rejected_harmonized_rows": rejected,
            "pvalue_sha256": sha256(pvalue_file),
            "genes_out": str(genes_out.relative_to(ROOT)),
            "genes_out_sha256": sha256(genes_out),
            "window_10kb_genes_out": str(sensitivity_genes_out.relative_to(ROOT)),
            "window_10kb_genes_out_sha256": sha256(sensitivity_genes_out),
        })

    fields = list(inventory_rows[0])
    with (work / "magma_run_inventory.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(inventory_rows)
    print(f"Completed {len(inventory_rows)} MAGMA gene analyses in {work}")


if __name__ == "__main__":
    main()
