#!/usr/bin/env python3
"""Finish Phase 19b genetic support (MAGMA, QTL audit, and coloc gate).

This script operates only on the frozen Phase 20 combo-KDA candidate set.  It
keeps three distinctions explicit:

* a regional GWAS hit is annotation, not gene-level support;
* a released QTL fine-mapping row is not a complete fitted multi-signal model;
* a route that cannot support a valid H0--H4 comparison is ``not_assessable``,
  never a negative colocalization result.

The three CSF MAGMA scans are reused from the checksum-validated historical
Phase 19 full-genome run because their GWAS sources, MAGMA version, LD panel,
and FUMA Ensembl-v110 gene definitions are unchanged.  Clinical AD is run
fresh with the same tested-gene definitions and official MAGMA reference.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import subprocess
import tarfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "phase19b_sex_apoe_kda_combo_v2"

QTL_COLUMNS = [
    "schema_version",
    "gene",
    "ensembl_gene_id",
    "source_modality",
    "cohort",
    "cell_type",
    "biosample_type",
    "tissue_category",
    "source_identifier",
    "variant_id",
    "chromosome",
    "chrom_start",
    "chrom_end",
    "ref",
    "alt",
    "target",
    "target_ensembl_id",
    "pip",
    "conditional_effect",
    "credible_set_95",
    "credible_set_70",
    "credible_set_50",
    "qtl_p",
    "qtl_fdr",
    "is_hmt_signif",
    "event_id",
    "source_archive",
    "source_member",
    "release_model_state",
]

COARSE_CELL_MATCH = {
    "Astrocytes": "astrocyte",
    "Excitatory_neurons": "excitatory neuron",
    "Inhibitory_neurons": "inhibitory neuron",
    "Microglia": "microglia",
    "Oligodendrocytes": "oligodendrocyte",
    "OPCs": "oligodendrocyte progenitor cell",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - source registry uses MD5.
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, na_rep="NA", lineterminator="\n")


@contextmanager
def deterministic_gzip_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                yield text


def write_empty_gzip_tsv(path: Path, columns: list[str]) -> None:
    with deterministic_gzip_writer(path) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()


def check(check_id: str, observed: Any, expected: Any, passed: bool) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA}_checks",
        "check_id": check_id,
        "observed": observed,
        "expected": expected,
        "passed": bool(passed),
    }


def finalize_stage(
    out_dir: Path,
    stage: str,
    checks: list[dict[str, Any]],
    status_fields: dict[str, Any],
    artifacts: Iterable[Path],
) -> None:
    checks_frame = pd.DataFrame(checks)
    checks_path = out_dir / f"{stage}_checks.tsv"
    status_path = out_dir / f"{stage}_status.tsv"
    artifacts_path = out_dir / f"{stage}_artifacts.tsv"
    write_tsv(checks_frame, checks_path)
    failed = int((~checks_frame["passed"].astype(bool)).sum())
    status = {
        "schema_version": f"{SCHEMA}_status",
        "stage": stage,
        "generated_at_utc": utc_now(),
        "failed_checks": failed,
        "validation_status": "validated_complete" if failed == 0 else "validation_failed",
    }
    status.update(status_fields)
    write_tsv(pd.DataFrame([status]), status_path)
    rows = []
    for path in list(artifacts) + [checks_path, status_path]:
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts",
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    write_tsv(pd.DataFrame(rows), artifacts_path)
    if failed:
        failed_ids = checks_frame.loc[~checks_frame["passed"].astype(bool), "check_id"].tolist()
        raise RuntimeError(f"{stage} failed checks: {', '.join(failed_ids)}")


def load_config(path: str) -> dict[str, Any]:
    config = yaml.safe_load(resolve(path).read_text(encoding="utf-8"))
    if not config["analysis"].get("definitions_frozen"):
        raise RuntimeError("Phase 19b definitions must be frozen before execution")
    return config


def load_inputs(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inputs = config["inputs"]
    candidates = pd.read_csv(resolve(inputs["candidates"]), sep="\t", dtype=str)
    loci = pd.read_csv(resolve(inputs["candidate_loci"]), sep="\t", dtype=str)
    contexts = pd.read_csv(resolve(inputs["candidate_contexts"]), sep="\t", dtype=str)
    return candidates, loci, contexts


def as_bool(value: Any) -> bool:
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES"}


def in_credible_set(value: Any) -> bool:
    return str(value).strip().upper() not in {"", ".", "0", "FALSE", "NA", "NAN", "NONE"}


def run_logged(command: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
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
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{tail}")


def make_tested_gene_location_file(legacy: pd.DataFrame, destination: Path) -> int:
    columns = ["gene_id", "chromosome", "start", "stop"]
    unique = legacy[columns].dropna().drop_duplicates().copy()
    conflicting = unique.groupby("gene_id").size()
    if int((conflicting > 1).sum()):
        raise RuntimeError("Historical MAGMA results contain conflicting gene coordinates")
    unique["gene_id"] = unique["gene_id"].astype(str).str.replace(r"\..*$", "", regex=True)
    unique["chromosome"] = unique["chromosome"].astype(str).str.replace(r"\.0$", "", regex=True)
    unique = unique.drop_duplicates("gene_id").sort_values(
        ["chromosome", "start", "gene_id"], key=lambda x: x.astype(str)
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    unique.to_csv(destination, sep="\t", header=False, index=False, lineterminator="\n")
    return len(unique)


def make_clinical_pvalue_file(source: Path, destination: Path) -> tuple[int, int]:
    accepted = 0
    rejected = 0
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "rt", newline="", encoding="utf-8") as input_handle, temporary.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        reader = csv.DictReader(input_handle, delimiter="\t")
        required = {"variant_id", "p_value"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"Clinical GWAS lacks columns {sorted(required)}")
        writer = csv.writer(output_handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["SNP", "P"])
        for row in reader:
            rsid = row["variant_id"]
            try:
                p_value = float(row["p_value"])
            except (TypeError, ValueError):
                rejected += 1
                continue
            if not rsid.startswith("rs") or not np.isfinite(p_value) or not 0 <= p_value <= 1:
                rejected += 1
                continue
            writer.writerow([rsid, row["p_value"]])
            accepted += 1
    temporary.replace(destination)
    return accepted, rejected


def parse_magma_genes(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=r"\s+", dtype={"GENE": str, "CHR": str})
    required = {"GENE", "CHR", "START", "STOP", "NSNPS", "ZSTAT", "P"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"Unexpected MAGMA output columns in {path}: {list(frame.columns)}")
    return frame.rename(
        columns={
            "GENE": "ensembl_gene_id",
            "CHR": "chromosome",
            "START": "start",
            "STOP": "stop",
            "NSNPS": "n_snps",
            "ZSTAT": "z_stat",
            "P": "p_value",
        }
    )


def stage_magma(config: dict[str, Any], force: bool = False) -> None:
    analysis = config["analysis"]
    inputs = config["inputs"]
    out_dir = resolve(config["outputs"]["magma"])
    work_dir = out_dir / "work"
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    candidates, loci, _ = load_inputs(config)
    legacy_path = resolve(inputs["legacy_csf_magma"])
    legacy_sha = sha256_file(legacy_path)
    if legacy_sha != inputs["legacy_csf_magma_sha256"]:
        raise RuntimeError(f"Historical CSF MAGMA SHA-256 changed: {legacy_sha}")
    legacy = pd.read_csv(legacy_path, sep="\t", dtype={"gene_id": str, "chromosome": str})
    legacy["gene_id"] = legacy["gene_id"].str.replace(r"\..*$", "", regex=True)

    gene_locations = work_dir / "fuma_v110_tested_gene_locations.tsv"
    tested_gene_count = make_tested_gene_location_file(legacy, gene_locations)

    binary = resolve(inputs["magma_binary"])
    reference = resolve(inputs["magma_reference_prefix"])
    required = [binary, gene_locations]
    required.extend(Path(f"{reference}.{suffix}") for suffix in ("bed", "bim", "fam"))
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Missing MAGMA inputs: {missing}")

    annotation_prefix = work_dir / "g1000_eur_fuma_v110_tested_genes"
    annotation_path = Path(f"{annotation_prefix}.genes.annot")
    annotation_log = work_dir / "magma_annotation.log"
    if force or not annotation_path.is_file():
        run_logged(
            [
                str(binary),
                "--annotate",
                "--snp-loc",
                f"{reference}.bim",
                "--gene-loc",
                str(gene_locations),
                "--out",
                str(annotation_prefix),
            ],
            annotation_log,
        )

    clinical_source = resolve(inputs["clinical_ad_gwas"])
    pvalue_path = work_dir / "clinical_ad_bellenguez2022.pval.tsv"
    pvalue_inventory = work_dir / "clinical_ad_pvalue_inventory.tsv"
    if force or not pvalue_path.is_file():
        accepted, rejected = make_clinical_pvalue_file(clinical_source, pvalue_path)
        write_tsv(
            pd.DataFrame(
                [
                    {
                        "schema_version": f"{SCHEMA}_magma_pvalue_inventory",
                        "accepted_rows": accepted,
                        "rejected_rows": rejected,
                        "pvalue_sha256": sha256_file(pvalue_path),
                    }
                ]
            ),
            pvalue_inventory,
        )
    else:
        accepted = max(sum(1 for _ in pvalue_path.open(encoding="utf-8")) - 1, 0)
        rejected = -1

    clinical_prefix = work_dir / "clinical_ad_bellenguez2022"
    clinical_out = Path(f"{clinical_prefix}.genes.out")
    clinical_log = work_dir / "clinical_ad_bellenguez2022.magma.log"
    if force or not clinical_out.is_file():
        run_logged(
            [
                str(binary),
                "--bfile",
                str(reference),
                "--pval",
                str(pvalue_path),
                f"N={int(inputs['clinical_ad_total_sample_size'])}",
                "duplicate=first",
                "--gene-annot",
                str(annotation_path),
                "--genes-only",
                "--out",
                str(clinical_prefix),
            ],
            clinical_log,
        )

    clinical = parse_magma_genes(clinical_out)
    clinical["ensembl_gene_id"] = clinical["ensembl_gene_id"].str.replace(r"\..*$", "", regex=True)
    clinical["trait_id"] = "clinical_ad"
    clinical["source_accession"] = inputs["clinical_ad_accession"]
    clinical["result_provenance"] = "fresh_magma_v1.10_phase19b"

    csf = legacy.rename(columns={"gene_id": "ensembl_gene_id"})[
        [
            "trait_id",
            "source_accession",
            "ensembl_gene_id",
            "chromosome",
            "start",
            "stop",
            "n_snps",
            "z_stat",
            "p_value",
        ]
    ].copy()
    csf["result_provenance"] = "reused_checksum_validated_phase19_full_genome_magma"
    all_results = pd.concat(
        [
            clinical[
                [
                    "trait_id",
                    "source_accession",
                    "ensembl_gene_id",
                    "chromosome",
                    "start",
                    "stop",
                    "n_snps",
                    "z_stat",
                    "p_value",
                    "result_provenance",
                ]
            ],
            csf,
        ],
        ignore_index=True,
    )
    all_results = all_results.sort_values(["trait_id", "ensembl_gene_id", "p_value"]).drop_duplicates(
        ["trait_id", "ensembl_gene_id"], keep="first"
    )

    candidate_loci = candidates[["candidate_id", "gene", "priority_tier", "mapping_status"]].merge(
        loci[["gene", "ensembl_gene_id", "chromosome", "start", "end"]], on="gene", how="left"
    )
    traits = pd.DataFrame(
        [
            ("clinical_ad", inputs["clinical_ad_accession"]),
            ("csf_abeta42", "GCST90726396"),
            ("csf_total_tau", "GCST90726397"),
            ("csf_ptau181", "GCST90726398"),
        ],
        columns=["trait_id", "source_accession"],
    )
    candidate_loci["_key"] = 1
    traits["_key"] = 1
    result = candidate_loci.merge(traits, on="_key").drop(columns="_key")
    result = result.merge(
        all_results.drop(columns="source_accession"),
        on=["trait_id", "ensembl_gene_id"],
        how="left",
        suffixes=("_candidate", "_magma"),
    )
    result["candidate_threshold"] = float(analysis["magma_candidate_p"])
    result["candidate_significant"] = result["p_value"].astype(float).le(result["candidate_threshold"])
    result["test_status"] = np.where(
        result["mapping_status"].eq("symbol_mapping_failed"),
        "not_assessable_symbol_mapping_failed",
        np.where(
            result["p_value"].notna(),
            "tested",
            "not_assessable_no_fuma_v110_reference_gene_model",
        ),
    )
    result.insert(0, "schema_version", f"{SCHEMA}_magma")
    output_columns = [
        "schema_version",
        "candidate_id",
        "gene",
        "priority_tier",
        "trait_id",
        "source_accession",
        "ensembl_gene_id",
        "chromosome_candidate",
        "start_candidate",
        "end",
        "chromosome_magma",
        "start_magma",
        "stop",
        "n_snps",
        "z_stat",
        "p_value",
        "candidate_threshold",
        "candidate_significant",
        "test_status",
        "result_provenance",
    ]
    result = result[output_columns].sort_values(["trait_id", "gene"])
    results_path = out_dir / "magma_candidate_results.tsv"
    write_tsv(result, results_path)

    sources = pd.DataFrame(
        [
            {
                "schema_version": f"{SCHEMA}_magma_sources",
                "source_id": "clinical_ad_bellenguez2022",
                "path": str(clinical_source.relative_to(ROOT)),
                "bytes": clinical_source.stat().st_size,
                "sha256": sha256_file(clinical_source),
                "provenance": "fresh_phase19b_magma_run",
            },
            {
                "schema_version": f"{SCHEMA}_magma_sources",
                "source_id": "three_csf_full_genome_magma_results",
                "path": str(legacy_path.relative_to(ROOT)),
                "bytes": legacy_path.stat().st_size,
                "sha256": legacy_sha,
                "provenance": "checksum_validated_historical_result_reuse",
            },
            {
                "schema_version": f"{SCHEMA}_magma_sources",
                "source_id": "magma_v1.10_mac",
                "path": str(binary.relative_to(ROOT)),
                "bytes": binary.stat().st_size,
                "sha256": sha256_file(binary),
                "provenance": "official_magma_distribution",
            },
            {
                "schema_version": f"{SCHEMA}_magma_sources",
                "source_id": "g1000_eur",
                "path": str(reference.relative_to(ROOT)) + ".bed/.bim/.fam",
                "bytes": sum(Path(f"{reference}.{x}").stat().st_size for x in ("bed", "bim", "fam")),
                "sha256": "see_individual_files_in_working_input_inventory",
                "provenance": "official_magma_distribution",
            },
        ]
    )
    sources_path = out_dir / "magma_sources.tsv"
    write_tsv(sources, sources_path)

    input_inventory = []
    for path in [binary, gene_locations, annotation_path, clinical_source, pvalue_path, clinical_out]:
        input_inventory.append(
            {
                "schema_version": f"{SCHEMA}_magma_input_inventory",
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    for suffix in ("bed", "bim", "fam", "synonyms"):
        path = Path(f"{reference}.{suffix}")
        if path.is_file():
            input_inventory.append(
                {
                    "schema_version": f"{SCHEMA}_magma_input_inventory",
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    inventory_path = out_dir / "magma_input_inventory.tsv"
    write_tsv(pd.DataFrame(input_inventory), inventory_path)

    expected_rows = int(analysis["expected_genes"]) * int(analysis["traits"])
    tested = int(result["p_value"].notna().sum())
    significant = int(result["candidate_significant"].sum())
    checks = [
        check("candidate_rows", len(result), expected_rows, len(result) == expected_rows),
        check("unique_candidates", result["gene"].nunique(), analysis["expected_genes"], result["gene"].nunique() == int(analysis["expected_genes"])),
        check("traits", result["trait_id"].nunique(), analysis["traits"], result["trait_id"].nunique() == int(analysis["traits"])),
        check("threshold", result["candidate_threshold"].nunique(), 1, result["candidate_threshold"].nunique() == 1),
        check("historical_csf_sha256", legacy_sha, inputs["legacy_csf_magma_sha256"], legacy_sha == inputs["legacy_csf_magma_sha256"]),
        check("tested_gene_definitions", tested_gene_count, ">=18000", tested_gene_count >= 18000),
        check("candidate_tests_completed", tested, ">=800", tested >= 800),
    ]
    artifacts = [results_path, sources_path, inventory_path]
    if pvalue_inventory.is_file():
        artifacts.append(pvalue_inventory)
    finalize_stage(
        out_dir,
        "magma",
        checks,
        {
            "candidate_rows": len(result),
            "tested_rows": tested,
            "not_assessable_rows": int(result["p_value"].isna().sum()),
            "candidate_significant_rows": significant,
            "candidate_significant_genes": int(result.loc[result["candidate_significant"], "gene"].nunique()),
            "candidate_threshold": analysis["magma_candidate_p"],
            "threshold_definition": "0.05/(228_candidates*4_traits)",
            "clinical_pvalue_rows": accepted,
            "clinical_rejected_rows": rejected,
        },
        artifacts,
    )
    print(f"MAGMA: rows={len(result)} tested={tested} significant={significant}")


def parse_target_info(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in str(text).split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value
    return values


def metadata_by_filename(path: Path) -> dict[str, dict[str, str]]:
    metadata = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    return {row["File name"]: row.to_dict() for _, row in metadata.iterrows()}


def qtl_gene_from_row(row: dict[str, str]) -> tuple[str, str]:
    info = parse_target_info(row.get("user_input", ""))
    symbol = row.get("target_gene_symbol", "") or info.get("target_gene_symbol", "")
    ensembl = (
        row.get("target_ensembl_id", "")
        or row.get("target", "")
        or info.get("target_ensembl_id", "")
        or info.get("target", "")
    )
    ensembl = str(ensembl).split(".")[0]
    return symbol, ensembl


def extract_qtl_rows(
    config: dict[str, Any],
    genes: set[str],
    ensembl_to_gene: dict[str, str],
    output_path: Path,
) -> tuple[int, pd.DataFrame, pd.DataFrame]:
    qtl_dir = resolve(config["inputs"]["niagads_qtl_dir"])
    metadata_path = resolve(config["inputs"]["niagads_metadata"])
    metadata_md5 = md5_file(metadata_path)
    if metadata_md5 != config["inputs"]["niagads_metadata_md5"]:
        raise RuntimeError(f"NG00184 metadata validation failed: md5={metadata_md5}")
    metadata = metadata_by_filename(metadata_path)
    extracted: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    for source in config["qtl_archives"]:
        archive = qtl_dir / source["filename"]
        if not archive.is_file():
            raise FileNotFoundError(archive)
        observed_md5 = md5_file(archive)
        if archive.stat().st_size != int(source["bytes"]) or observed_md5 != source["md5"]:
            raise RuntimeError(
                f"QTL archive validation failed for {archive}: bytes={archive.stat().st_size}, md5={observed_md5}"
            )
        member_count = 0
        data_member_count = 0
        with tarfile.open(archive, "r") as tar:
            for member in tar:
                member_count += 1
                if not member.isfile() or not member.name.endswith(".bed.gz"):
                    continue
                data_member_count += 1
                raw = tar.extractfile(member)
                if raw is None:
                    continue
                filename = Path(member.name).name
                meta = metadata.get(filename, {})
                with gzip.GzipFile(fileobj=raw) as compressed:
                    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
                    reader = csv.DictReader(text, delimiter="\t")
                    if reader.fieldnames:
                        reader.fieldnames = [name.removeprefix("#") for name in reader.fieldnames]
                    for row in reader:
                        symbol, ensembl = qtl_gene_from_row(row)
                        gene = symbol if symbol in genes else ensembl_to_gene.get(ensembl, "")
                        if gene not in genes:
                            continue
                        info = parse_target_info(row.get("user_input", ""))
                        target_info = parse_target_info(row.get("target_info", ""))
                        extracted.append(
                            {
                                "schema_version": f"{SCHEMA}_qtl_finemapping",
                                "gene": gene,
                                "ensembl_gene_id": ensembl,
                                "source_modality": source["modality"],
                                "cohort": meta.get("Data Source", member.name.split("/")[2] if "/" in member.name else ""),
                                "cell_type": meta.get("cell type", info.get("xQTL_context_id", "")),
                                "biosample_type": meta.get("Biosample type", ""),
                                "tissue_category": meta.get("Tissue category", ""),
                                "source_identifier": meta.get("Identifier", ""),
                                "variant_id": row.get("variant_id", ""),
                                "chromosome": row.get("chrom", "").removeprefix("chr"),
                                "chrom_start": row.get("chromStart", ""),
                                "chrom_end": row.get("chromEnd", ""),
                                "ref": row.get("ref", ""),
                                "alt": row.get("alt", ""),
                                "target": row.get("target", ""),
                                "target_ensembl_id": row.get("target_ensembl_id", ensembl),
                                "pip": row.get("PIP", row.get("pip", "")),
                                "conditional_effect": row.get("conditional_effect", ""),
                                "credible_set_95": row.get("cs_95", ""),
                                "credible_set_70": row.get("cs_70", ""),
                                "credible_set_50": row.get("cs_50", ""),
                                "qtl_p": row.get("qtl_p", "") or target_info.get("qtl_p_val", ""),
                                "qtl_fdr": row.get("qtl_fdr", "") or target_info.get("qtl_bh", ""),
                                "is_hmt_signif": row.get("is_hmt_signif", "") or target_info.get("is_hmt_signif", ""),
                                "event_id": info.get("event_ID", ""),
                                "source_archive": source["filename"],
                                "source_member": member.name,
                                "release_model_state": "PIP_and_credible_set_summary_not_complete_fitted_multisignal_model",
                            }
                        )
        source_rows.append(
            {
                "schema_version": f"{SCHEMA}_qtl_sources",
                "modality": source["modality"],
                "path": str(archive.relative_to(ROOT)),
                "bytes": archive.stat().st_size,
                "md5": observed_md5,
                "sha256": sha256_file(archive),
                "tar_members": member_count,
                "data_members": data_member_count,
                "validation_state": "validated",
            }
        )

    source_rows.append(
        {
            "schema_version": f"{SCHEMA}_qtl_sources",
            "modality": "metadata",
            "path": str(metadata_path.relative_to(ROOT)),
            "bytes": metadata_path.stat().st_size,
            "md5": metadata_md5,
            "sha256": sha256_file(metadata_path),
            "tar_members": np.nan,
            "data_members": np.nan,
            "validation_state": "validated",
        }
    )

    frame = pd.DataFrame(extracted, columns=QTL_COLUMNS)
    frame = frame.sort_values(["gene", "source_modality", "cohort", "cell_type", "variant_id"])
    with deterministic_gzip_writer(output_path) as handle:
        frame.to_csv(handle, sep="\t", index=False, na_rep="NA", lineterminator="\n")
    return len(frame), frame, pd.DataFrame(source_rows)


def numeric_summary(values: pd.Series, operation: str) -> float:
    numbers = pd.to_numeric(values, errors="coerce")
    if not numbers.notna().any():
        return np.nan
    return float(numbers.min() if operation == "min" else numbers.max())


def stage_qtl(config: dict[str, Any]) -> None:
    analysis = config["analysis"]
    out_dir = resolve(config["outputs"]["qtl"])
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates, loci, contexts = load_inputs(config)
    scope = set(config["analysis"]["qtl_scope"])
    followup = candidates.loc[candidates["priority_tier"].isin(scope)].copy()
    followup_genes = set(followup["gene"])
    scoped_contexts = contexts.loc[contexts["current_symbol"].isin(followup_genes)].copy()
    scoped_contexts = scoped_contexts.merge(
        followup[["candidate_id", "gene", "priority_tier"]],
        left_on="current_symbol",
        right_on="gene",
        how="left",
    )
    ensembl_to_gene = dict(
        zip(loci["ensembl_gene_id"].str.replace(r"\..*$", "", regex=True), loci["gene"])
    )

    qtl_path = out_dir / "qtl_finemapping.tsv.gz"
    extracted_count, qtl, sources = extract_qtl_rows(
        config, followup_genes, ensembl_to_gene, qtl_path
    )
    sources_path = out_dir / "qtl_sources.tsv"
    write_tsv(sources, sources_path)

    route_rows: list[dict[str, Any]] = []
    for index, context in scoped_contexts.sort_values(
        ["signature_group", "broad_network", "current_symbol"]
    ).reset_index(drop=True).iterrows():
        gene_rows = qtl.loc[qtl["gene"].eq(context["gene"])]
        for qtl_type in analysis["qtl_modalities"]:
            if qtl_type == "eQTL":
                exact_cell = COARSE_CELL_MATCH.get(context["broad_network"])
                exact = gene_rows.loc[
                    gene_rows["source_modality"].eq("snuc-eQTL")
                    & gene_rows["cell_type"].str.lower().eq(exact_cell or "__none__")
                ]
                if len(exact):
                    selected = exact
                    context_match = "exact_broad_lineage"
                else:
                    selected = gene_rows.loc[gene_rows["source_modality"].eq("eQTL")]
                    context_match = "bulk_brain_fallback" if len(selected) else "no_released_finemapping"
            else:
                selected = gene_rows.loc[gene_rows["source_modality"].eq("sQTL")]
                context_match = "bulk_brain_fallback" if len(selected) else "no_released_finemapping"

            hmt = selected["is_hmt_signif"].map(as_bool) if len(selected) else pd.Series(dtype=bool)
            signal_rows = int(hmt.sum())
            if not len(selected):
                evidence_state = "no_released_candidate_finemapping"
            elif signal_rows:
                evidence_state = "source_significant"
            else:
                evidence_state = "released_finemapping_no_source_significant_signal"
            route_rows.append(
                {
                    "schema_version": f"{SCHEMA}_qtl_coverage",
                    "route_id": f"QTL19B{index + 1:04d}_{qtl_type}",
                    "candidate_id": context["candidate_id"],
                    "gene": context["gene"],
                    "priority_tier": context["priority_tier"],
                    "signature_group": context["signature_group"],
                    "sex": context["sex"],
                    "apoe_group": context["apoe_group"],
                    "broad_network": context["broad_network"],
                    "qtl_type": qtl_type,
                    "context_match": context_match,
                    "sex_apoe_match": "unavailable_public_source_not_stratified",
                    "qtl_finemapping_rows": len(selected),
                    "source_significant_rows": signal_rows,
                    "credible_set_95_rows": int(selected["credible_set_95"].map(in_credible_set).sum()) if len(selected) else 0,
                    "min_qtl_p": numeric_summary(selected["qtl_p"], "min") if len(selected) else np.nan,
                    "min_qtl_fdr": numeric_summary(selected["qtl_fdr"], "min") if len(selected) else np.nan,
                    "max_pip": numeric_summary(selected["pip"], "max") if len(selected) else np.nan,
                    "qtl_signal": bool(signal_rows),
                    "evidence_state": evidence_state,
                }
            )
    coverage = pd.DataFrame(route_rows)
    coverage_path = out_dir / "qtl_coverage.tsv"
    write_tsv(coverage, coverage_path)

    archive_sources = sources.loc[sources["modality"].ne("metadata")]
    checks = [
        check("followup_genes", followup["gene"].nunique(), analysis["expected_followup_genes"], followup["gene"].nunique() == int(analysis["expected_followup_genes"])),
        check("followup_contexts", len(scoped_contexts), analysis["expected_followup_contexts"], len(scoped_contexts) == int(analysis["expected_followup_contexts"])),
        check("route_rows", len(coverage), int(analysis["expected_followup_contexts"]) * len(analysis["qtl_modalities"]), len(coverage) == int(analysis["expected_followup_contexts"]) * len(analysis["qtl_modalities"])),
        check("archives", len(archive_sources), len(config["qtl_archives"]), len(archive_sources) == len(config["qtl_archives"])),
        check("source_validation", int(sources["validation_state"].eq("validated").sum()), len(config["qtl_archives"]) + 1, sources["validation_state"].eq("validated").all()),
        check("extracted_rows", extracted_count, ">0", extracted_count > 0),
        check("sex_apoe_exact_routes", int(coverage["sex_apoe_match"].ne("unavailable_public_source_not_stratified").sum()), 0, coverage["sex_apoe_match"].eq("unavailable_public_source_not_stratified").all()),
    ]
    finalize_stage(
        out_dir,
        "qtl",
        checks,
        {
            "followup_genes": followup["gene"].nunique(),
            "followup_contexts": len(scoped_contexts),
            "routes": len(coverage),
            "extracted_finemapping_rows": extracted_count,
            "source_significant_routes": int(coverage["qtl_signal"].sum()),
            "source_significant_genes": int(coverage.loc[coverage["qtl_signal"], "gene"].nunique()),
            "exact_broad_lineage_routes": int(coverage["context_match"].eq("exact_broad_lineage").sum()),
            "bulk_brain_fallback_routes": int(coverage["context_match"].eq("bulk_brain_fallback").sum()),
            "no_released_finemapping_routes": int(coverage["context_match"].eq("no_released_finemapping").sum()),
        },
        [qtl_path, coverage_path, sources_path],
    )
    print(
        f"QTL: extracted={extracted_count} routes={len(coverage)} "
        f"signal_routes={int(coverage['qtl_signal'].sum())}"
    )


def stage_coloc(config: dict[str, Any]) -> None:
    analysis = config["analysis"]
    out_dir = resolve(config["outputs"]["coloc"])
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates, _, _ = load_inputs(config)
    tier1 = pd.read_csv(resolve(config["inputs"]["tier1_evidence"]), sep="\t", dtype=str)
    regional = pd.read_csv(resolve(config["inputs"]["regional_summary"]), sep="\t", dtype=str)
    magma = pd.read_csv(resolve(config["outputs"]["magma"]) / "magma_candidate_results.tsv", sep="\t", dtype=str)
    qtl = pd.read_csv(resolve(config["outputs"]["qtl"]) / "qtl_coverage.tsv", sep="\t", dtype=str)

    regional["genome_wide_significant"] = regional["genome_wide_significant"].map(as_bool)
    qtl["qtl_signal"] = qtl["qtl_signal"].map(as_bool)
    # pandas cannot cross-merge while retaining the gene key; explicitly merge
    # each gene's QTL routes to that gene's four GWAS traits.
    decisions = qtl.merge(
        regional[["trait", "gene", "regional_min_p", "genome_wide_significant", "regional_scan_status"]],
        on="gene",
        how="left",
    )
    decisions["eligible_for_coloc_model"] = decisions["qtl_signal"] & decisions[
        "genome_wide_significant"
    ]
    decisions["coloc_status"] = np.where(
        decisions["eligible_for_coloc_model"], "not_assessable", "not_run_signal_gate"
    )

    def route_reason(row: pd.Series) -> str:
        if row["eligible_for_coloc_model"]:
            return (
                "released_QTL_PIP_and_credible_set_rows_are_not_complete_fitted_multisignal_models;"
                "source_matched_LD_and_full_compatible_QTL_statistics_absent"
            )
        if not row["qtl_signal"] and not row["genome_wide_significant"]:
            return "no_source_significant_QTL_signal_and_no_regional_GWAS_signal"
        if not row["qtl_signal"]:
            return "no_source_significant_QTL_signal"
        return "no_regional_GWAS_signal"

    decisions["reason"] = decisions.apply(route_reason, axis=1)
    decisions["valid_h0_h4_result"] = False
    decisions["h4"] = np.nan
    decisions["conditional_h4"] = np.nan
    decisions["schema_version"] = f"{SCHEMA}_coloc_route_decisions"
    decisions = decisions[["schema_version"] + [column for column in decisions.columns if column != "schema_version"]]
    decisions_path = out_dir / "coloc_route_decisions.tsv"
    write_tsv(decisions, decisions_path)

    coloc_columns = [
        "schema_version",
        "route_id",
        "gene",
        "trait",
        "qtl_type",
        "h0",
        "h1",
        "h2",
        "h3",
        "h4",
        "conditional_h4",
        "method",
        "model_validation_state",
    ]
    coloc_path = out_dir / "colocalization.tsv.gz"
    write_empty_gzip_tsv(coloc_path, coloc_columns)

    gene_qtl = qtl.groupby("gene", as_index=False).agg(
        qtl_routes=("route_id", "size"),
        qtl_signal_routes=("qtl_signal", "sum"),
        qtl_exact_routes=("context_match", lambda values: int((values == "exact_broad_lineage").sum())),
    )
    magma["candidate_significant"] = magma["candidate_significant"].map(as_bool)
    gene_magma = magma.groupby("gene", as_index=False).agg(
        magma_tested_traits=("p_value", lambda values: int(values.notna().sum())),
        magma_significant_traits=("candidate_significant", "sum"),
        magma_min_p=("p_value", lambda values: pd.to_numeric(values, errors="coerce").min()),
    )
    tier1 = tier1[["gene", "grade"]].rename(columns={"grade": "tier1_grade"})
    evidence = candidates[["candidate_id", "gene", "priority_tier", "mapping_status"]].merge(
        tier1, on="gene", how="left"
    ).merge(gene_magma, on="gene", how="left").merge(gene_qtl, on="gene", how="left")
    for column in ["qtl_routes", "qtl_signal_routes", "qtl_exact_routes", "magma_significant_traits"]:
        evidence[column] = pd.to_numeric(evidence[column], errors="coerce").fillna(0).astype(int)
    evidence["qtl_scope_status"] = np.where(
        evidence["priority_tier"].isin(analysis["qtl_scope"]), "assessed_P1_P2", "not_run_preregistered_P3_stop"
    )
    evidence["valid_coloc_routes"] = 0
    evidence["final_gene_level_grade"] = evidence["tier1_grade"].fillna("none_found")
    upgrade = evidence["magma_significant_traits"].gt(0) & evidence["final_gene_level_grade"].eq("none_found")
    evidence.loc[upgrade, "final_gene_level_grade"] = "weak"
    evidence["gene_level_support_basis"] = np.where(
        evidence["tier1_grade"].isin(["strong", "moderate", "weak"]),
        "tier1_public_summary",
        np.where(evidence["magma_significant_traits"].gt(0), "corrected_MAGMA", "none_found"),
    )
    evidence["interpretation_note"] = (
        "QTL signal alone is annotation; no route had the complete compatible model inputs required for H0-H4 colocalization"
    )
    evidence.insert(0, "schema_version", f"{SCHEMA}_final_evidence")
    evidence_path = out_dir / "final_gene_evidence.tsv"
    write_tsv(evidence, evidence_path)

    qc = pd.DataFrame(
        [
            {
                "schema_version": f"{SCHEMA}_coloc_qc",
                "route_decisions": len(decisions),
                "eligible_signal_positive_routes": int(decisions["eligible_for_coloc_model"].sum()),
                "valid_h0_h4_results": int(decisions["valid_h0_h4_result"].sum()),
                "not_assessable_routes": int(decisions["coloc_status"].eq("not_assessable").sum()),
                "strong_h4_routes": 0,
                "source_model_limitation": "released_NG00184_finemapping_tables_are_summaries_not_complete_fitted_models",
                "ld_limitation": "source_matched_QTL_LD_or_complete_QTL_statistics_absent",
            }
        ]
    )
    qc_path = out_dir / "coloc_qc.tsv"
    write_tsv(qc, qc_path)

    expected_routes = int(analysis["expected_followup_contexts"]) * len(analysis["qtl_modalities"]) * int(analysis["traits"])
    checks = [
        check("route_decisions", len(decisions), expected_routes, len(decisions) == expected_routes),
        check("traits_per_qtl_route", len(decisions), len(qtl) * int(analysis["traits"]), len(decisions) == len(qtl) * int(analysis["traits"])),
        check("valid_h0_h4_results", int(decisions["valid_h0_h4_result"].sum()), 0, not decisions["valid_h0_h4_result"].any()),
        check("coloc_gzip_has_header", sum(1 for _ in gzip.open(coloc_path, "rt")), 1, sum(1 for _ in gzip.open(coloc_path, "rt")) == 1),
        check("final_evidence_genes", len(evidence), analysis["expected_genes"], len(evidence) == int(analysis["expected_genes"])),
        check("no_regional_only_gene_grade", int(evidence["gene_level_support_basis"].eq("regional_GWAS").sum()), 0, not evidence["gene_level_support_basis"].eq("regional_GWAS").any()),
    ]
    finalize_stage(
        out_dir,
        "coloc",
        checks,
        {
            "validation_status": "validated_complete_with_terminal_not_assessable_routes",
            "route_decisions": len(decisions),
            "eligible_signal_positive_routes": int(decisions["eligible_for_coloc_model"].sum()),
            "valid_h0_h4_results": 0,
            "not_assessable_routes": int(decisions["coloc_status"].eq("not_assessable").sum()),
            "supported_genes": int(evidence["final_gene_level_grade"].isin(["strong", "moderate", "weak"]).sum()),
        },
        [decisions_path, coloc_path, qc_path, evidence_path],
    )
    print(
        f"Coloc gate: decisions={len(decisions)} eligible={int(decisions['eligible_for_coloc_model'].sum())} "
        "valid_H0-H4=0"
    )


def stage_summary(config: dict[str, Any]) -> None:
    summary_path = resolve(config["outputs"]["summary"])
    candidates, _, contexts = load_inputs(config)
    tier1 = pd.read_csv(resolve(config["inputs"]["tier1_evidence"]), sep="\t", dtype=str)
    regional = pd.read_csv(resolve(config["inputs"]["regional_summary"]), sep="\t", dtype=str)
    magma = pd.read_csv(resolve(config["outputs"]["magma"]) / "magma_candidate_results.tsv", sep="\t", dtype=str)
    qtl = pd.read_csv(resolve(config["outputs"]["qtl"]) / "qtl_coverage.tsv", sep="\t", dtype=str)
    decisions = pd.read_csv(resolve(config["outputs"]["coloc"]) / "coloc_route_decisions.tsv", sep="\t", dtype=str)
    evidence = pd.read_csv(resolve(config["outputs"]["coloc"]) / "final_gene_evidence.tsv", sep="\t", dtype=str)

    magma_sig = magma.loc[magma["candidate_significant"].map(as_bool)].copy()
    qtl_sig = qtl.loc[qtl["qtl_signal"].map(as_bool)].copy()
    eligible = decisions.loc[decisions["eligible_for_coloc_model"].map(as_bool)].copy()
    grade_counts = tier1["grade"].value_counts().to_dict()
    final_counts = evidence["final_gene_level_grade"].value_counts().to_dict()
    regional_signal_genes = regional.loc[regional["genome_wide_significant"].map(as_bool), "gene"].nunique()
    magma_gene_text = ", ".join(sorted(magma_sig["gene"].unique())) or "none"

    lines = [
        "# Phase 19b genetic-support rerun results",
        "",
        f"**Completed:** {utc_now()[:10]}",
        "**Authoritative candidate source:** `results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv`",
        "**Scope:** 228 non-MT genes, 381 sex/APOE × broad-network contexts; QTL/coloc follow-up restricted a priori to P1+P2 (116 genes, 269 contexts).",
        "",
        "## Outcome",
        "",
        f"All six Phase 19b workstreams are terminal and validated. Tier 1 graded {grade_counts.get('strong', 0)} genes strong, {grade_counts.get('moderate', 0)} moderate, {grade_counts.get('weak', 0)} weak, and {grade_counts.get('none_found', 0)} none found. The combined gene-level result contains {final_counts.get('strong', 0)} strong, {final_counts.get('moderate', 0)} moderate, {final_counts.get('weak', 0)} weak, and {final_counts.get('none_found', 0)} none found.",
        "",
        f"The four GWAS regional scans found genome-wide-significant variants near {regional_signal_genes} unique genes. These are proximity annotations only and were not used as gene-level validation.",
        "",
        f"MAGMA tested {magma['p_value'].notna().sum()} of {len(magma)} candidate-trait rows. At the frozen family-wise threshold `0.05 / (228 × 4) = {float(config['analysis']['magma_candidate_p']):.8g}`, {len(magma_sig)} gene-trait rows ({magma_sig['gene'].nunique()} unique genes: {magma_gene_text}) passed. The three CSF full-genome scans were reused only after exact historical result checksum validation; clinical AD was run fresh with MAGMA v1.10 using the published total sample count (111,326 cases/proxy cases + 677,663 controls).",
        "",
        f"The public NG00184 fine-mapping audit yielded {len(qtl)} gene-context-modality routes, including {len(qtl_sig)} source-significant routes across {qtl_sig['gene'].nunique()} genes. Public QTL sources are broad-cell/bulk-brain and not sex/APOE-stratified, so they do not validate a sex/APOE-specific KDA effect.",
        "",
        f"The coloc gate considered {len(decisions)} QTL × GWAS-trait decisions; {len(eligible)} had both a regional GWAS signal and a source-significant QTL signal. None had a complete fitted multi-signal QTL model plus compatible source-matched LD/full statistics, so zero valid H0-H4 tests were produced. These routes are explicitly `not_assessable`, not negative colocalizations.",
        "",
        "## Gene-level interpretation",
        "",
        "A corrected MAGMA association is counted as weak gene-level statistical support. Regional GWAS proximity and QTL signal without a valid disease-QTL colocalization are annotation only. No Phase 19b gene receives strong colocalization support from the available public inputs.",
        "",
        "## Result bundles",
        "",
        "- `results/minerva_production/19b_genetic_support_candidates/` — frozen candidates and loci (WS0).",
        "- `results/minerva_production/19b_genetic_support_tier1/` — public summary screen (WS1).",
        "- `results/minerva_production/19b_genetic_support_regional/` — four complete regional GWAS scans (WS2).",
        "- `results/minerva_production/19b_genetic_support_magma/` — four-trait candidate MAGMA results and provenance (WS3).",
        "- `results/minerva_production/19b_genetic_support_qtl/` — P1/P2 QTL fine-mapping and coverage audit (WS4).",
        "- `results/minerva_production/19b_genetic_support_coloc/` — coloc gate decisions and final gene table (WS5).",
        "",
        "The five `19_genetic_support_* (deprecated)` bundles are immutable historical outputs for the earlier 25-gene Phase 18 freeze. They are retained for provenance and are not current inputs except for the explicitly checksum-validated CSF MAGMA result reuse documented above.",
        "",
    ]
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["magma", "qtl", "coloc", "summary", "all"])
    parser.add_argument("--config", default="config/phase19b_genetic_support.yml")
    parser.add_argument("--force", action="store_true", help="rebuild MAGMA intermediates")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.stage in {"magma", "all"}:
        stage_magma(config, force=args.force)
    if args.stage in {"qtl", "all"}:
        stage_qtl(config)
    if args.stage in {"coloc", "all"}:
        stage_coloc(config)
    if args.stage in {"summary", "all"}:
        stage_summary(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
