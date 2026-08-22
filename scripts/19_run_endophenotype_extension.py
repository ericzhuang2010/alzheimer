#!/usr/bin/env python3
"""Run the Phase 19 CSF endophenotype GWAS/QTL extension locally.

The runner is deliberately strict about the frozen candidate set, upstream
artifact hashes, source metadata, GWAS coverage, and the 36-file publication
contract.  Optional MAGMA and QTL/colocalization results are read from the
extension work/source-manifest directories; unavailable downstream inputs
remain explicit terminal scientific states.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import math
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "phase19_endophenotype_gwas_qtl_extension_v1"
GRADE_RANK = {"not_assessable": -1, "none_found": 0, "weak": 1, "moderate": 2, "strong": 3}
CHROMOSOME_LENGTHS_GRCH38 = {
    1: 248956422, 2: 242193529, 3: 198295559, 4: 190214555,
    5: 181538259, 6: 170805979, 7: 159345973, 8: 145138636,
    9: 138394717, 10: 133797422, 11: 135086622, 12: 133275309,
    13: 114364328, 14: 107043718, 15: 101991189, 16: 90338345,
    17: 83257441, 18: 80373285, 19: 58617616, 20: 64444167,
    21: 46709983, 22: 50818468,
}

DECLARED_FILES = [
    "endophenotype_analysis_manifest.tsv",
    "endophenotype_dataset_registry.tsv",
    "endophenotype_request_manifest.tsv",
    "endophenotype_input_inventory.tsv",
    "endophenotype_source_checks.tsv",
    "endophenotype_candidate_manifest.tsv",
    "endophenotype_biomarker_manifest.tsv",
    "endophenotype_screening_units.tsv",
    "endophenotype_gwas_qc.tsv",
    "endophenotype_regional_gwas_summary.tsv",
    "endophenotype_regional_gwas.tsv.gz",
    "endophenotype_magma_results.tsv",
    "endophenotype_magma_conditional.tsv",
    "endophenotype_gate_decisions.tsv",
    "endophenotype_qtl_coverage.tsv",
    "endophenotype_route_manifest.tsv",
    "endophenotype_sample_overlap_audit.tsv",
    "endophenotype_variant_harmonization.tsv.gz",
    "endophenotype_variant_harmonization_summary.tsv",
    "endophenotype_ld_qc.tsv",
    "endophenotype_gwas_finemapping.tsv.gz",
    "endophenotype_qtl_finemapping.tsv.gz",
    "endophenotype_colocalization.tsv.gz",
    "endophenotype_colocalization_qc.tsv",
    "endophenotype_prior_sensitivity.tsv.gz",
    "endophenotype_twas_pwas_followup.tsv",
    "endophenotype_assessability.tsv",
    "endophenotype_evidence_summary.tsv",
    "endophenotype_context_biomarker_matrix.tsv",
    "endophenotype_figure_data.tsv.gz",
    "endophenotype_evidence_matrix.pdf",
    "endophenotype_evidence_matrix.png",
    "endophenotype_locus_plots.pdf",
    "endophenotype_checks.tsv",
    "endophenotype_artifacts.tsv",
    "endophenotype_status.tsv",
]


def resolve(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def open_text(path: Path) -> Any:
    return gzip.open(path, "rt", newline="", encoding="utf-8") if path.suffix == ".gz" else path.open(newline="", encoding="utf-8")


def deterministic_gzip_text(path: Path) -> Any:
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return raw, compressed


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: normalize_cell(row.get(field, "NA")) for field in fields})
    temporary.replace(path)


def write_gzip_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    raw, compressed = deterministic_gzip_text(temporary)
    try:
        import io
        with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
            writer = csv.DictWriter(text, delimiter="\t", fieldnames=fields, lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: normalize_cell(row.get(field, "NA")) for field in fields})
    finally:
        if not raw.closed:
            raw.close()
    temporary.replace(path)


def normalize_cell(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "NA"
    return value


def safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def rows_in_file(path: Path) -> int | str:
    if path.suffix in {".pdf", ".png"}:
        return "NA"
    with open_text(path) as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def assert_unique(rows: list[dict[str, Any]], keys: tuple[str, ...], label: str) -> None:
    observed = [tuple(str(row.get(key, "")) for key in keys) for row in rows]
    if len(observed) != len(set(observed)):
        raise RuntimeError(f"Duplicate {label} keys for {keys}")


def verify_artifact_manifest(root: Path, manifest: Path, tier: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    for index, row in enumerate(read_tsv(manifest), start=1):
        target = root / row["path"]
        observed = sha256(target) if target.exists() else ""
        status = "pass" if observed == row["sha256"] else "fail"
        if status == "fail":
            failures.append(row["path"])
        checks.append({
            "schema_version": SCHEMA,
            "check_id": f"baseline_{tier}_{index:03d}",
            "source_id": tier,
            "role": "immutable_baseline_artifact",
            "path": str(target.relative_to(ROOT)),
            "expected": row["sha256"],
            "observed": observed,
            "status": status,
            "detail": "upstream_artifact_hash_reproduced",
        })
    if failures:
        raise RuntimeError(f"{tier} baseline mismatch: {', '.join(failures)}")
    return checks


def load_candidates(config: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]], list[str], list[str]]:
    candidates = read_tsv(resolve(config["inputs"]["candidate_manifest"]))
    if len(candidates) != int(config["analysis"]["expected_candidate_contexts"]):
        raise RuntimeError(f"Expected 47 candidate contexts, found {len(candidates)}")
    assert_unique(candidates, ("candidate_id",), "candidate")
    unique_genes = sorted({row["gene"] for row in candidates})
    if len(unique_genes) != int(config["analysis"]["expected_unique_genes"]):
        raise RuntimeError(f"Expected 25 genes, found {len(unique_genes)}")
    nuclear = sorted({row["gene"] for row in candidates if row["is_mtdna_gene"].lower() != "true"})
    mtdna = sorted(set(unique_genes) - set(nuclear))
    if (len(nuclear), len(mtdna)) != (19, 6):
        raise RuntimeError(f"Expected 19 nuclear and 6 mtDNA genes, found {len(nuclear)} and {len(mtdna)}")
    regions = read_tsv(resolve(config["inputs"]["recovery_regions"]))
    if len(regions) != 19:
        raise RuntimeError(f"Expected 19 frozen regions, found {len(regions)}")
    region_by_gene = {row["gene"]: row for row in regions}
    if set(region_by_gene) != set(nuclear):
        raise RuntimeError("Frozen recovery regions do not match the 19 nuclear genes")
    return candidates, region_by_gene, nuclear, mtdna


def verify_biomarkers(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for index, trait in enumerate(config["biomarkers"], start=1):
        raw = resolve(trait["raw_file"])
        metadata = resolve(trait["metadata_file"])
        harmonized = resolve(trait["harmonized_file"])
        meta = yaml.safe_load(metadata.read_text(encoding="utf-8"))
        descriptions = meta.get("trait_description", [])
        identity_ok = (
            meta.get("gwas_id") == trait["source_accession"]
            and trait["expected_trait_description"] in descriptions
            and meta.get("genome_assembly") == "GRCh38"
            and int(meta["samples"][0]["sample_size"]) == int(trait["sample_size"])
            and meta["samples"][0]["sample_ancestry_category"] == ["European"]
            and meta["samples"][0]["case_control_study"] is False
        )
        observed_md5 = md5(raw) if raw.exists() else ""
        raw_ok = observed_md5 == trait["expected_md5"]
        if not identity_ok or not raw_ok or not harmonized.exists():
            raise RuntimeError(f"GWAS source validation failed for {trait['source_accession']}")
        manifest.append({
            "schema_version": SCHEMA,
            "trait_id": trait["trait_id"],
            "trait_label": trait["trait_label"],
            "source_accession": trait["source_accession"],
            "trait_description": descriptions[0],
            "trait_type": "quantitative",
            "effect_scale": "standardized_linear_beta",
            "ancestry": "European",
            "sample_size": trait["sample_size"],
            "genome_build": meta["genome_assembly"],
            "coordinate_system": meta["coordinate_system"],
            "raw_file": str(raw.relative_to(ROOT)),
            "harmonized_file": str(harmonized.relative_to(ROOT)),
            "raw_md5": observed_md5,
            "source_url": trait["source_url"],
            "harmonized_url": trait["harmonized_url"],
            "identity_verified": True,
        })
        for role, path, url in [
            ("raw_complete_gwas", raw, trait["source_url"]),
            ("gwas_catalog_metadata", metadata, meta["gwas_catalog_api"]),
            ("harmonized_complete_gwas", harmonized, trait["harmonized_url"]),
            ("harmonized_tabix_index", Path(str(harmonized) + ".tbi"), trait["harmonized_url"] + ".tbi"),
        ]:
            inventory.append({
                "schema_version": SCHEMA,
                "source_id": trait["source_accession"],
                "role": role,
                "source_version": meta["date_metadata_last_modified"],
                "path": str(path.relative_to(ROOT)),
                "url": url,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "validation_state": "validated",
            })
        checks.append({
            "schema_version": SCHEMA,
            "check_id": f"gwas_source_{index:02d}",
            "source_id": trait["source_accession"],
            "role": "trait_identity_and_raw_checksum",
            "path": str(raw.relative_to(ROOT)),
            "expected": f"{trait['expected_trait_description']}|{trait['expected_md5']}",
            "observed": f"{descriptions[0]}|{observed_md5}",
            "status": "pass",
            "detail": "official_GWAS_Catalog_metadata_and_MD5_match",
        })
    return manifest, inventory, checks


def screening_units(
    candidates: list[dict[str, str]],
    regions: dict[str, dict[str, str]],
    biomarkers: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contexts_by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        contexts_by_gene[row["gene"]].append(row)
    gene_rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []
    for gene in sorted(contexts_by_gene):
        is_mtdna = contexts_by_gene[gene][0]["is_mtdna_gene"].lower() == "true"
        for trait in biomarkers:
            region = regions.get(gene, {})
            gene_rows.append({
                "schema_version": SCHEMA,
                "screen_id": f"{gene}__{trait['trait_id']}",
                "gene": gene,
                "ensembl_gene_id": region.get("ensembl_gene_id", "NA"),
                "trait_id": trait["trait_id"],
                "source_accession": trait["source_accession"],
                "is_mtdna_gene": is_mtdna,
                "chromosome": region.get("chromosome", "MT"),
                "window_start": region.get("window_start", "NA"),
                "window_end": region.get("window_end", "NA"),
                "analysis_scope": "not_applicable_mtdna" if is_mtdna else "nuclear_gwas_qtl",
                "frozen_before_result": True,
            })
            for context in sorted(contexts_by_gene[gene], key=lambda item: item["candidate_id"]):
                context_rows.append({
                    "schema_version": SCHEMA,
                    "candidate_id": context["candidate_id"],
                    "gene": gene,
                    "broad_network": context["broad_network"],
                    "trait_id": trait["trait_id"],
                    "is_mtdna_gene": is_mtdna,
                    "analysis_scope": "not_applicable_mtdna" if is_mtdna else "nuclear_gwas_qtl",
                })
    return gene_rows, context_rows


def scan_gwas(
    config: dict[str, Any],
    biomarkers: list[dict[str, Any]],
    units: list[dict[str, Any]],
    region_by_gene: dict[str, dict[str, str]],
    staging: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    analysis = config["analysis"]
    by_chromosome: dict[int, list[tuple[str, int, int, str]]] = defaultdict(list)
    for gene, region in region_by_gene.items():
        chrom = int(str(region["chromosome"]).replace("chr", ""))
        by_chromosome[chrom].append((gene, int(region["window_start"]), int(region["window_end"]), region["ensembl_gene_id"]))

    regional_path = staging / "endophenotype_regional_gwas.tsv.gz"
    raw, compressed = deterministic_gzip_text(regional_path)
    import io
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    regional_fields = [
        "schema_version", "trait_id", "source_accession", "gene", "ensembl_gene_id",
        "chromosome", "window_start", "window_end", "position", "effect_allele",
        "other_allele", "beta", "standard_error", "effect_allele_frequency",
        "p_value", "negative_log10_p", "source_variant_id", "canonical_variant_id",
    ]
    writer = csv.DictWriter(text, delimiter="\t", fieldnames=regional_fields, lineterminator="\n")
    writer.writeheader()

    all_summaries: list[dict[str, Any]] = []
    qc_rows: list[dict[str, Any]] = []
    try:
        for trait in biomarkers:
            raw_path = resolve(next(item["raw_file"] for item in config["biomarkers"] if item["trait_id"] == trait["trait_id"]))
            stats: dict[str, dict[str, Any]] = {
                gene: {"rows": 0, "finite_p": 0, "beta_se": 0, "min_p": math.inf,
                       "lead": "NA", "below_gws": 0, "below_1e6": 0, "below_1e5": 0}
                for gene in region_by_gene
            }
            chromosome_rows: Counter[int] = Counter()
            total_rows = 0
            valid_rows = 0
            invalid_rows = 0
            with raw_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                expected = {"chromosome", "base_pair_location", "effect_allele", "other_allele", "beta", "standard_error", "p_value"}
                if not expected.issubset(reader.fieldnames or []):
                    raise RuntimeError(f"Unexpected GWAS columns for {trait['trait_id']}: {reader.fieldnames}")
                for row in reader:
                    total_rows += 1
                    try:
                        chrom = int(str(row["chromosome"]).replace("chr", ""))
                        position = int(row["base_pair_location"])
                    except (TypeError, ValueError):
                        invalid_rows += 1
                        continue
                    if chrom not in CHROMOSOME_LENGTHS_GRCH38 or position < 1:
                        invalid_rows += 1
                        continue
                    p_value = safe_float(row["p_value"])
                    beta = safe_float(row["beta"])
                    standard_error = safe_float(row["standard_error"])
                    chromosome_rows[chrom] += 1
                    valid_rows += 1
                    for gene, start, end, ensembl_id in by_chromosome.get(chrom, []):
                        if not (start <= position <= end):
                            continue
                        state = stats[gene]
                        state["rows"] += 1
                        if p_value is not None and 0 <= p_value <= 1:
                            state["finite_p"] += 1
                            if p_value < state["min_p"]:
                                state["min_p"] = p_value
                                state["lead"] = f"{chrom}:{position}:{row['effect_allele']}:{row['other_allele']}"
                            state["below_gws"] += int(p_value < float(analysis["regional_signal_p"]))
                            state["below_1e6"] += int(p_value < float(analysis["descriptive_p_1"]))
                            state["below_1e5"] += int(p_value < float(analysis["descriptive_p_2"]))
                        if beta is not None and standard_error is not None and standard_error > 0:
                            state["beta_se"] += 1
                        if p_value is None or not (0 <= p_value <= 1):
                            neglog = "NA"
                        elif p_value == 0:
                            neglog = 323.3062153431158
                        else:
                            neglog = -math.log10(p_value)
                        writer.writerow({
                            "schema_version": SCHEMA,
                            "trait_id": trait["trait_id"],
                            "source_accession": trait["source_accession"],
                            "gene": gene,
                            "ensembl_gene_id": ensembl_id,
                            "chromosome": chrom,
                            "window_start": start,
                            "window_end": end,
                            "position": position,
                            "effect_allele": row["effect_allele"],
                            "other_allele": row["other_allele"],
                            "beta": row["beta"],
                            "standard_error": row["standard_error"],
                            "effect_allele_frequency": row.get("effect_allele_frequency", "NA"),
                            "p_value": row["p_value"],
                            "negative_log10_p": neglog,
                            "source_variant_id": state["lead"] if position and False else f"{chrom}:{position}",
                            "canonical_variant_id": f"{chrom}:{position}:{row['effect_allele']}:{row['other_allele']}",
                        })
            for gene in sorted(region_by_gene):
                region = region_by_gene[gene]
                state = stats[gene]
                chrom = int(str(region["chromosome"]).replace("chr", ""))
                width_mb = (int(region["window_end"]) - int(region["window_start"]) + 1) / 1_000_000
                density = state["rows"] / width_mb if width_mb > 0 else 0
                chromosome_density = chromosome_rows[chrom] / (CHROMOSOME_LENGTHS_GRCH38[chrom] / 1_000_000)
                relative_density = density / chromosome_density if chromosome_density else 0
                finite_fraction = state["finite_p"] / state["rows"] if state["rows"] else 0
                beta_se_fraction = state["beta_se"] / state["rows"] if state["rows"] else 0
                coverage_pass = (
                    density >= float(analysis["minimum_variant_density_per_mb"])
                    and relative_density >= float(analysis["minimum_relative_chromosome_density"])
                    and finite_fraction >= float(analysis["minimum_finite_p_fraction"])
                )
                model_eligible = coverage_pass and beta_se_fraction >= float(analysis["minimum_beta_se_fraction_for_model"])
                regional_signal = coverage_pass and state["below_gws"] > 0
                all_summaries.append({
                    "schema_version": SCHEMA,
                    "screen_id": f"{gene}__{trait['trait_id']}",
                    "gene": gene,
                    "ensembl_gene_id": region["ensembl_gene_id"],
                    "trait_id": trait["trait_id"],
                    "source_accession": trait["source_accession"],
                    "is_mtdna_gene": False,
                    "chromosome": chrom,
                    "window_start": region["window_start"],
                    "window_end": region["window_end"],
                    "regional_rows": state["rows"],
                    "regional_variant_density_per_mb": density,
                    "chromosome_variant_density_per_mb": chromosome_density,
                    "relative_density": relative_density,
                    "finite_p_fraction": finite_fraction,
                    "beta_se_complete_fraction": beta_se_fraction,
                    "coverage_pass": coverage_pass,
                    "model_input_eligible": model_eligible,
                    "regional_min_p": state["min_p"] if math.isfinite(state["min_p"]) else "NA",
                    "regional_lead_variant": state["lead"],
                    "variants_p_lt_5e8": state["below_gws"],
                    "variants_p_lt_1e6": state["below_1e6"],
                    "variants_p_lt_1e5": state["below_1e5"],
                    "regional_signal": regional_signal,
                    "regional_status": "regional_signal" if regional_signal else ("no_qualifying_gwas_signal" if coverage_pass else "not_assessable_low_gwas_coverage"),
                })
            qc_rows.append({
                "schema_version": SCHEMA,
                "trait_id": trait["trait_id"],
                "source_accession": trait["source_accession"],
                "total_source_rows": total_rows,
                "valid_autosomal_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "chromosomes_observed": len(chromosome_rows),
                "candidate_region_rows": sum(state["rows"] for state in stats.values()),
                "candidate_regions_passing_coverage": sum(
                    row["coverage_pass"] is True for row in all_summaries if row["trait_id"] == trait["trait_id"]
                ),
                "candidate_regions_with_gws_signal": sum(
                    row["regional_signal"] is True for row in all_summaries if row["trait_id"] == trait["trait_id"]
                ),
                "status": "pass" if invalid_rows / max(total_rows, 1) < 0.01 and len(chromosome_rows) == 22 else "fail",
            })
    finally:
        text.close()
        if not raw.closed:
            raw.close()

    for unit in units:
        if str(unit["is_mtdna_gene"]).upper() != "TRUE":
            continue
        all_summaries.append({
            "schema_version": SCHEMA,
            "screen_id": unit["screen_id"],
            "gene": unit["gene"],
            "ensembl_gene_id": "NA",
            "trait_id": unit["trait_id"],
            "source_accession": unit["source_accession"],
            "is_mtdna_gene": True,
            "chromosome": "MT",
            "window_start": "NA", "window_end": "NA", "regional_rows": 0,
            "regional_variant_density_per_mb": "NA", "chromosome_variant_density_per_mb": "NA",
            "relative_density": "NA", "finite_p_fraction": "NA", "beta_se_complete_fraction": "NA",
            "coverage_pass": False, "model_input_eligible": False, "regional_min_p": "NA",
            "regional_lead_variant": "NA", "variants_p_lt_5e8": 0, "variants_p_lt_1e6": 0,
            "variants_p_lt_1e5": 0, "regional_signal": False,
            "regional_status": "not_applicable_mtdna",
        })
    all_summaries.sort(key=lambda row: (row["trait_id"], row["gene"]))
    if len(all_summaries) != 75:
        raise RuntimeError(f"Expected 75 regional summaries, found {len(all_summaries)}")
    return all_summaries, qc_rows


def load_magma_results(config: dict[str, Any], biomarkers: list[dict[str, Any]], region_by_gene: dict[str, dict[str, str]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    work = resolve(config["inputs"]["work_dir"]) / "magma"
    all_rows: list[dict[str, Any]] = []
    candidate_map: dict[tuple[str, str], dict[str, Any]] = {}
    conditional: list[dict[str, Any]] = []
    candidate_ids = {row["ensembl_gene_id"]: gene for gene, row in region_by_gene.items()}
    threshold = float(config["analysis"]["candidate_magma_p"])
    for trait in biomarkers:
        path = work / f"{trait['trait_id']}.genes.out"
        parsed: list[dict[str, Any]] = []
        if path.exists():
            with path.open(encoding="utf-8") as handle:
                header = handle.readline().split()
                if "GENE" not in header or "P" not in header:
                    raise RuntimeError(f"Unexpected MAGMA columns in {path}: {header}")
                for line in handle:
                    values = line.split()
                    if len(values) == len(header):
                        parsed.append(dict(zip(header, values)))
        sensitivity_map: dict[str, float] = {}
        sensitivity_path = work / f"{trait['trait_id']}.window10kb.genes.out"
        if sensitivity_path.exists():
            with sensitivity_path.open(encoding="utf-8") as handle:
                sensitivity_header = handle.readline().split()
                if "GENE" not in sensitivity_header or "P" not in sensitivity_header:
                    raise RuntimeError(f"Unexpected MAGMA columns in {sensitivity_path}: {sensitivity_header}")
                for line in handle:
                    values = line.split()
                    if len(values) == len(sensitivity_header):
                        sensitivity_row = dict(zip(sensitivity_header, values))
                        sensitivity_gene_id = str(sensitivity_row.get("GENE", "")).split(".")[0]
                        sensitivity_p = safe_float(sensitivity_row.get("P"))
                        if sensitivity_p is not None:
                            sensitivity_map[sensitivity_gene_id] = sensitivity_p
        for row in parsed:
            gene_id = str(row.get("GENE", "")).split(".")[0]
            p_value = safe_float(row.get("P"))
            candidate_gene = candidate_ids.get(gene_id)
            output = {
                "schema_version": SCHEMA,
                "trait_id": trait["trait_id"],
                "source_accession": trait["source_accession"],
                "gene_id": gene_id,
                "gene": candidate_gene or "NA",
                "chromosome": row.get("CHR", "NA"),
                "start": row.get("START", "NA"),
                "stop": row.get("STOP", "NA"),
                "n_snps": row.get("NSNPS", "NA"),
                "z_stat": row.get("ZSTAT", "NA"),
                "p_value": p_value if p_value is not None else "NA",
                "phase18_candidate": candidate_gene is not None,
                "candidate_threshold": threshold,
                "candidate_significant": candidate_gene is not None and p_value is not None and p_value < threshold,
                "test_status": "tested_magma_v1.10",
                "method": "MAGMA_v1.10_SNP-wise_mean_gene_body",
            }
            all_rows.append(output)
            if candidate_gene:
                candidate_map[(candidate_gene, trait["trait_id"])] = output
        for gene, region in region_by_gene.items():
            key = (gene, trait["trait_id"])
            if key not in candidate_map:
                missing = {
                    "schema_version": SCHEMA, "trait_id": trait["trait_id"],
                    "source_accession": trait["source_accession"],
                    "gene_id": region["ensembl_gene_id"], "gene": gene,
                    "chromosome": region["chromosome"], "start": "NA", "stop": "NA",
                    "n_snps": "NA", "z_stat": "NA", "p_value": "NA",
                    "phase18_candidate": True, "candidate_threshold": threshold,
                    "candidate_significant": False,
                    "test_status": "not_assessable_magma_output_missing" if not path.exists() else "not_assessable_candidate_not_mapped",
                    "method": "MAGMA_v1.10_SNP-wise_mean_gene_body",
                }
                all_rows.append(missing)
                candidate_map[key] = missing
            if candidate_map[key]["candidate_significant"]:
                conditional.append({
                    "schema_version": SCHEMA, "trait_id": trait["trait_id"], "gene": gene,
                    "ensembl_gene_id": region["ensembl_gene_id"],
                    "unconditional_p": candidate_map[key]["p_value"],
                    "candidate_significant": True,
                    "window_10kb_p": sensitivity_map.get(region["ensembl_gene_id"], "NA"),
                    "window_10kb_significant": sensitivity_map.get(region["ensembl_gene_id"], 1.0) < threshold,
                    "sensitivity_status": "tested_window_10kb" if sensitivity_path.exists() else "not_assessable_output_missing",
                    "conditional_status": "not_assessable_no_preregistered_independent_variant_conditioning_model",
                    "conditional_p": "NA",
                    "regional_ambiguity": "unresolved",
                    "reason": "MAGMA_gene_test_available_but_SNP_level_conditional_model_not_released_or_run",
                })
    all_rows.sort(key=lambda row: (row["trait_id"], str(row["phase18_candidate"]) != "TRUE", row["gene_id"]))
    return all_rows, candidate_map, conditional


def gate_decisions(regional: list[dict[str, Any]], magma: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for row in regional:
        if row["is_mtdna_gene"] is True:
            continue
        mag = magma[(row["gene"], row["trait_id"])]
        regional_signal = row["regional_signal"] is True
        gene_signal = mag["candidate_significant"] is True
        if not row["coverage_pass"]:
            state = "not_assessable_gwas"
            next_action = "stop_low_gwas_coverage"
        elif regional_signal and gene_signal:
            state = "regional_and_gene_based_signal"
            next_action = "regional_qtl_colocalization_and_report_magma"
        elif regional_signal:
            state = "regional_signal_only"
            next_action = "regional_qtl_colocalization"
        elif gene_signal:
            state = "gene_based_signal_only"
            next_action = "twas_pwas_support_no_classical_coloc"
        else:
            state = "no_qualifying_gwas_signal"
            next_action = "terminal_no_signal_no_qtl_ld_acquisition"
        decisions.append({
            "schema_version": SCHEMA,
            "screen_id": row["screen_id"],
            "gene": row["gene"],
            "ensembl_gene_id": row["ensembl_gene_id"],
            "trait_id": row["trait_id"],
            "source_accession": row["source_accession"],
            "regional_coverage_pass": row["coverage_pass"],
            "regional_min_p": row["regional_min_p"],
            "regional_signal": regional_signal,
            "magma_test_status": mag["test_status"],
            "magma_p": mag["p_value"],
            "magma_signal": gene_signal,
            "gate_state": state,
            "next_action": next_action,
            "decision_frozen_before_qtl_result": True,
        })
    decisions.sort(key=lambda row: (row["trait_id"], row["gene"]))
    if len(decisions) != 57:
        raise RuntimeError(f"Expected 57 nuclear gate decisions, found {len(decisions)}")
    return decisions


def build_qtl_routes(config: dict[str, Any], candidates: list[dict[str, str]], decisions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    contexts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        if row["is_mtdna_gene"].lower() != "true":
            contexts[row["gene"]].append(row)
    optional_results = resolve(config["inputs"]["source_manifest_dir"]) / "endophenotype_route_results.tsv"
    result_by_route: dict[str, dict[str, str]] = {}
    if optional_results.exists():
        result_by_route = {row["route_id"]: row for row in read_tsv(optional_results)}
    routes: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    overlap: list[dict[str, Any]] = []
    for decision in decisions:
        if decision["gate_state"] not in {"regional_and_gene_based_signal", "regional_signal_only"}:
            continue
        gene = decision["gene"]
        trait_id = decision["trait_id"]
        registrations: list[tuple[str, str, str, str, str]] = [
            ("NG00130.v2", "pQTL", "CSF", "gene_level_csf_protein", "known_overlap_unquantified"),
            ("NG00184.v1", "pQTL", "brain_regions", "bulk_brain_fallback", "known_ROSMAP_and_other_cohort_overlap"),
        ]
        for context in contexts[gene]:
            network = context["broad_network"]
            registrations.extend([
                ("NG00184.v1", "eQTL", network, "exact_lineage_or_bulk_per_fileset", "known_ROSMAP_and_other_cohort_overlap"),
                ("NG00184.v1", "snuc-eQTL", network, "exact_or_lineage", "known_ROSMAP_and_other_cohort_overlap"),
                ("NG00184.v1", "sQTL", network, "exact_lineage_or_bulk_per_fileset", "known_ROSMAP_and_other_cohort_overlap"),
                ("scMetaBrain_2026", "eQTL", network, "exact_or_lineage", "possible_overlap"),
                ("PsychAD_snRNA_eQTL", "eQTL", network, "exact_or_lineage", "known_overlap_quantified"),
                ("EQTL_Catalogue_r7", "eQTL", network, "registered_exact_lineage_or_bulk", "source_specific"),
                ("EQTL_Catalogue_r7", "sQTL", network, "registered_exact_lineage_or_bulk", "source_specific"),
            ])
        for source_id, modality, context_label, match, overlap_state in sorted(set(registrations)):
            route_id = f"{gene}__{trait_id}__{source_id}__{modality}__{context_label}".replace("/", "_")
            imported = result_by_route.get(route_id, {})
            terminal = imported.get("route_terminal_status", "not_assessable")
            reason = imported.get("reason", "registered_source_coverage_or_complete_compatible_model_not_available_in_local_run")
            route = {
                "schema_version": SCHEMA,
                "route_id": route_id,
                "gene": gene,
                "ensembl_gene_id": decision["ensembl_gene_id"],
                "trait_id": trait_id,
                "source_accession": decision["source_accession"],
                "qtl_source_id": source_id,
                "qtl_modality": modality,
                "qtl_context": context_label,
                "context_match_level": match,
                "sample_overlap_state": overlap_state,
                "regional_gwas_signal": True,
                "qtl_measurement_state": imported.get("qtl_measurement_state", "inventory_unresolved"),
                "qtl_signal_state": imported.get("qtl_signal_state", "not_assessable"),
                "full_regional_qtl_available": imported.get("full_regional_qtl_available", "FALSE"),
                "compatible_model_or_ld_available": imported.get("compatible_model_or_ld_available", "FALSE"),
                "route_terminal_status": terminal,
                "coloc_outcome": imported.get("coloc_outcome", "NA"),
                "pp_h0": imported.get("pp_h0", "NA"), "pp_h1": imported.get("pp_h1", "NA"),
                "pp_h2": imported.get("pp_h2", "NA"), "pp_h3": imported.get("pp_h3", "NA"),
                "pp_h4": imported.get("pp_h4", "NA"),
                "conditional_h4": imported.get("conditional_h4", "NA"),
                "method": imported.get("method", "not_run"),
                "reason": reason,
                "selection_frozen_before_result": True,
            }
            routes.append(route)
            coverage.append({
                key: route[key] for key in [
                    "schema_version", "route_id", "gene", "ensembl_gene_id", "trait_id",
                    "qtl_source_id", "qtl_modality", "qtl_context", "context_match_level",
                    "sample_overlap_state", "qtl_measurement_state", "qtl_signal_state",
                    "full_regional_qtl_available", "compatible_model_or_ld_available", "reason",
                ]
            })
            overlap.append({
                "schema_version": SCHEMA, "route_id": route_id, "gene": gene,
                "trait_id": trait_id, "gwas_source": decision["source_accession"],
                "qtl_source": source_id,
                "phase18_vs_gwas": "possible_overlap_ROS_MAP_requires_cohort_list_audit",
                "phase18_vs_qtl": overlap_state,
                "gwas_vs_qtl": overlap_state,
                "independent_validation_permitted": overlap_state in {"no_known_overlap", "leave_overlap_out"},
                "interpretation": "mechanism_or_triangulation_only" if overlap_state not in {"no_known_overlap", "leave_overlap_out"} else "independent_validation_eligible",
            })
    routes.sort(key=lambda row: row["route_id"])
    coverage.sort(key=lambda row: row["route_id"])
    overlap.sort(key=lambda row: row["route_id"])
    return routes, coverage, overlap


def best_extension_grade(decision: dict[str, Any], routes: list[dict[str, Any]]) -> tuple[str, str, str]:
    matching = [route for route in routes if route["gene"] == decision["gene"] and route["trait_id"] == decision["trait_id"]]
    robust = [route for route in matching if route["coloc_outcome"] == "robust_shared_signal"]
    suggestive = [route for route in matching if route["coloc_outcome"] == "suggestive_shared_signal"]
    if robust:
        independent = any(route["sample_overlap_state"] in {"no_known_overlap", "leave_overlap_out"} for route in robust)
        grade = "strong" if independent else "moderate"
        return grade, "robust_shared_signal", robust[0]["route_id"]
    if suggestive:
        return "weak", "suggestive_shared_signal", suggestive[0]["route_id"]
    if decision["magma_signal"] is True:
        return "weak", "corrected_candidate_MAGMA", "NA"
    if decision["regional_signal"] is True:
        return "weak", "candidate_region_signal_without_gene_specific_colocalization", "NA"
    if decision["gate_state"] == "not_assessable_gwas":
        return "not_assessable", "low_or_invalid_GWAS_coverage", "NA"
    return "none_found", "assessable_no_qualifying_GWAS_signal", "NA"


def integrate_evidence(
    config: dict[str, Any],
    candidates: list[dict[str, str]],
    context_units: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    decision_map = {(row["gene"], row["trait_id"]): row for row in decisions}
    baseline_rows = read_tsv(resolve(config["inputs"]["recovery_evidence_summary"]))
    baseline = {row["candidate_id"]: row for row in baseline_rows}
    matrix: list[dict[str, Any]] = []
    for unit in context_units:
        base = baseline[unit["candidate_id"]]
        if unit["is_mtdna_gene"] is True:
            matrix.append({
                **unit,
                "gate_state": "not_applicable_mtdna",
                "regional_min_p": "NA", "regional_signal": False,
                "magma_p": "NA", "magma_signal": False,
                "extension_grade": "not_assessable",
                "extension_evidence_type": "not_applicable_mtdna",
                "best_route_id": "NA",
                "independence_class": "not_applicable",
                "baseline_grade": base["cumulative_phase19_grade"],
                "cumulative_phase19_grade": base["cumulative_phase19_grade"],
                "newly_biomarker_supported": False,
                "permitted_interpretation": "Nuclear endophenotype GWAS/QTL analysis is not applicable to mtDNA genes.",
            })
            continue
        decision = decision_map[(unit["gene"], unit["trait_id"])]
        grade, evidence_type, route_id = best_extension_grade(decision, routes)
        baseline_grade = base["cumulative_phase19_grade"]
        cumulative = baseline_grade if GRADE_RANK.get(baseline_grade, -1) >= GRADE_RANK[grade] else grade
        newly_supported = grade in {"strong", "moderate"} and baseline_grade not in {"strong", "moderate"}
        independence = "independent_eligible" if any(
            route["gene"] == unit["gene"] and route["trait_id"] == unit["trait_id"]
            and route["sample_overlap_state"] in {"no_known_overlap", "leave_overlap_out"}
            and route["coloc_outcome"] == "robust_shared_signal" for route in routes
        ) else "overlap_or_independence_unresolved"
        interpretation = {
            "strong": f"{unit['gene']} has strong biomarker-specific shared-signal support for {unit['trait_id']}.",
            "moderate": f"{unit['gene']} has biomarker-specific shared-signal support for {unit['trait_id']} with a context or independence limitation.",
            "weak": f"{unit['gene']} has candidate-level statistical support for {unit['trait_id']}, but the causal gene/shared molecular mechanism is not established.",
            "none_found": f"No qualifying {unit['trait_id']} GWAS signal was found for {unit['gene']} under the frozen gates.",
            "not_assessable": f"The {unit['trait_id']} genetic comparison for {unit['gene']} was not assessable.",
        }[grade]
        matrix.append({
            **unit,
            "gate_state": decision["gate_state"],
            "regional_min_p": decision["regional_min_p"],
            "regional_signal": decision["regional_signal"],
            "magma_p": decision["magma_p"],
            "magma_signal": decision["magma_signal"],
            "extension_grade": grade,
            "extension_evidence_type": evidence_type,
            "best_route_id": route_id,
            "independence_class": independence,
            "baseline_grade": baseline_grade,
            "cumulative_phase19_grade": cumulative,
            "newly_biomarker_supported": newly_supported,
            "permitted_interpretation": interpretation,
        })
    if len(matrix) != 141:
        raise RuntimeError(f"Expected 141 context-biomarker rows, found {len(matrix)}")
    assert_unique(matrix, ("candidate_id", "trait_id"), "context-biomarker")

    evidence: list[dict[str, Any]] = []
    for candidate in candidates:
        rows = [row for row in matrix if row["candidate_id"] == candidate["candidate_id"]]
        best = max(rows, key=lambda row: GRADE_RANK[row["extension_grade"]])
        evidence.append({
            "schema_version": SCHEMA,
            "candidate_id": candidate["candidate_id"],
            "gene": candidate["gene"],
            "broad_network": candidate["broad_network"],
            "is_mtdna_gene": candidate["is_mtdna_gene"],
            "baseline_grade": best["baseline_grade"],
            "best_extension_grade": best["extension_grade"],
            "best_extension_trait": best["trait_id"],
            "best_extension_evidence_type": best["extension_evidence_type"],
            "best_route_id": best["best_route_id"],
            "cumulative_phase19_grade": best["cumulative_phase19_grade"],
            "newly_biomarker_supported": any(row["newly_biomarker_supported"] is True for row in rows),
            "traits_with_regional_signal": ";".join(sorted(row["trait_id"] for row in rows if row["regional_signal"] is True)) or "none",
            "traits_with_magma_signal": ";".join(sorted(row["trait_id"] for row in rows if row["magma_signal"] is True)) or "none",
            "full_phase19_complete": False,
            "permitted_interpretation": best["permitted_interpretation"],
        })
    assessability: list[dict[str, Any]] = []
    for decision in decisions:
        assessability.append({
            "schema_version": SCHEMA, "unit_type": "gene_biomarker_screen",
            "unit_id": decision["screen_id"], "gene": decision["gene"],
            "trait_id": decision["trait_id"], "route_id": "NA",
            "terminal_status": decision["gate_state"], "reason": decision["next_action"],
        })
    for route in routes:
        assessability.append({
            "schema_version": SCHEMA, "unit_type": "qtl_route", "unit_id": route["route_id"],
            "gene": route["gene"], "trait_id": route["trait_id"], "route_id": route["route_id"],
            "terminal_status": route["route_terminal_status"], "reason": route["reason"],
        })
    return matrix, evidence, assessability


def write_empty_downstream(staging: Path, routes: list[dict[str, Any]], config: dict[str, Any]) -> None:
    harmonization_fields = [
        "schema_version", "route_id", "trait_id", "gene", "qtl_source_id", "variant_id",
        "gwas_effect_allele", "qtl_effect_allele", "alignment_state", "included", "exclusion_reason",
    ]
    source_manifest = resolve(config["inputs"]["source_manifest_dir"])
    route_lookup = {(route["trait_id"], route["qtl_source_id"]): route for route in routes}
    harmonization_rows: list[dict[str, Any]] = []
    matched_root = resolve(config["inputs"]["work_dir"]) / "coloc_sensitivity"
    for trait_id, source_id, accession in [
        (trait["trait_id"], "NG00130.v2", "GCST90424891") for trait in config["biomarkers"]
    ] + [
        (trait["trait_id"], "EQTL_Catalogue_r7", "QTD000579") for trait in config["biomarkers"]
    ]:
        route = route_lookup.get((trait_id, source_id))
        matched = matched_root / f"{trait_id}__{accession}.tsv"
        if route is None or not matched.exists():
            continue
        for row in read_tsv(matched):
            harmonization_rows.append({
                "schema_version": SCHEMA, "route_id": route["route_id"], "trait_id": trait_id,
                "gene": "APOE", "qtl_source_id": source_id, "variant_id": row["rsid"],
                "gwas_effect_allele": row["gwas_effect_allele"],
                "qtl_effect_allele": row["qtl_original_effect_allele"],
                "alignment_state": row["alignment_state"], "included": True, "exclusion_reason": "NA",
            })
    write_gzip_tsv(staging / "endophenotype_variant_harmonization.tsv.gz", harmonization_rows, harmonization_fields)

    audit_path = source_manifest / "endophenotype_harmonization_summary.tsv"
    audit_rows = read_tsv(audit_path) if audit_path.exists() else []
    audit_lookup = {
        (row["trait_id"], row["qtl_source_id"], row["qtl_accession"]): row for row in audit_rows
    }
    summary_rows: list[dict[str, Any]] = []
    for route in routes:
        accession = "GCST90424891" if route["qtl_source_id"] == "NG00130.v2" else (
            "QTD000579" if route["qtl_source_id"] == "EQTL_Catalogue_r7" and route["qtl_modality"] == "eQTL" else ""
        )
        audit = audit_lookup.get((route["trait_id"], route["qtl_source_id"], accession), {})
        gwas_count = safe_float(audit.get("gwas_variants"))
        qtl_count = safe_float(audit.get("qtl_variants"))
        common = safe_float(audit.get("included"))
        denominator = min(gwas_count, qtl_count) if gwas_count and qtl_count else None
        summary_rows.append({
            "schema_version": SCHEMA, "route_id": route["route_id"], "gene": route["gene"],
            "trait_id": route["trait_id"], "qtl_source_id": route["qtl_source_id"],
            "gwas_variants": audit.get("gwas_variants", "NA"),
            "qtl_variants": audit.get("qtl_variants", "NA"),
            "common_variants": audit.get("included", "NA"),
            "overlap_fraction_smaller_input": common / denominator if common is not None and denominator else "NA",
            "status": route["route_terminal_status"], "reason": route["reason"],
        })
    write_tsv(staging / "endophenotype_variant_harmonization_summary.tsv", summary_rows,
              ["schema_version", "route_id", "gene", "trait_id", "qtl_source_id", "gwas_variants", "qtl_variants", "common_variants", "overlap_fraction_smaller_input", "status", "reason"])
    ld_rows = [{
        "schema_version": SCHEMA, "route_id": route["route_id"], "gene": route["gene"],
        "trait_id": route["trait_id"], "ld_source": "NA", "ancestry": "NA", "variants": "NA",
        "symmetry_pass": "NA", "diagonal_pass": "NA", "psd_pass": "NA", "order_pass": "NA",
        "summary_ld_consistency_pass": "NA", "status": route["route_terminal_status"], "reason": route["reason"],
    } for route in routes]
    write_tsv(staging / "endophenotype_ld_qc.tsv", ld_rows,
              ["schema_version", "route_id", "gene", "trait_id", "ld_source", "ancestry", "variants", "symmetry_pass", "diagonal_pass", "psd_pass", "order_pass", "summary_ld_consistency_pass", "status", "reason"])
    fm_fields = ["schema_version", "route_id", "trait_id", "gene", "signal_id", "variant_id", "pip", "credible_set", "credible_set_coverage", "model_status"]
    write_gzip_tsv(staging / "endophenotype_gwas_finemapping.tsv.gz", [], fm_fields)
    write_gzip_tsv(staging / "endophenotype_qtl_finemapping.tsv.gz", [], fm_fields)
    coloc_fields = ["schema_version", "route_id", "gene", "trait_id", "qtl_source_id", "qtl_modality", "gwas_signal_id", "qtl_signal_id", "method", "p1", "p2", "p12", "pp_h0", "pp_h1", "pp_h2", "pp_h3", "pp_h4", "conditional_h4", "coloc_outcome"]
    coloc_rows = []
    for route in routes:
        if route["route_terminal_status"] not in {"precomputed_resolved", "custom_resolved"}:
            continue
        coloc_rows.append({
            "schema_version": SCHEMA, "route_id": route["route_id"], "gene": route["gene"],
            "trait_id": route["trait_id"], "qtl_source_id": route["qtl_source_id"],
            "qtl_modality": route["qtl_modality"], "gwas_signal_id": "source_model",
            "qtl_signal_id": "source_model", "method": route["method"], "p1": "NA", "p2": "NA", "p12": "NA",
            "pp_h0": route["pp_h0"], "pp_h1": route["pp_h1"], "pp_h2": route["pp_h2"],
            "pp_h3": route["pp_h3"], "pp_h4": route["pp_h4"], "conditional_h4": route["conditional_h4"],
            "coloc_outcome": route["coloc_outcome"],
        })
    write_gzip_tsv(staging / "endophenotype_colocalization.tsv.gz", coloc_rows, coloc_fields)
    qc_rows = [{
        "schema_version": SCHEMA, "route_id": route["route_id"], "gene": route["gene"],
        "trait_id": route["trait_id"], "route_terminal_status": route["route_terminal_status"],
        "model_converged": "NA", "posterior_sum": "NA", "prior_sensitivity_pass": "NA",
        "blocking_qc_pass": route["route_terminal_status"] in {"precomputed_resolved", "custom_resolved"},
        "reason": route["reason"],
    } for route in routes]
    write_tsv(staging / "endophenotype_colocalization_qc.tsv", qc_rows,
              ["schema_version", "route_id", "gene", "trait_id", "route_terminal_status", "model_converged", "posterior_sum", "prior_sensitivity_pass", "blocking_qc_pass", "reason"])
    sensitivity_path = source_manifest / "endophenotype_coloc_abf_sensitivity.tsv"
    sensitivity_rows: list[dict[str, Any]] = []
    if sensitivity_path.exists():
        for row in read_tsv(sensitivity_path):
            route = route_lookup.get((row["trait_id"], row["qtl_source_id"]))
            if route is None:
                continue
            sensitivity_rows.append({
                "schema_version": SCHEMA, "route_id": route["route_id"], "gene": route["gene"],
                "trait_id": row["trait_id"], "qtl_source_id": row["qtl_source_id"],
                "qtl_modality": route["qtl_modality"], "gwas_signal_id": "candidate_region_single_signal_assumption",
                "qtl_signal_id": row["qtl_accession"], "method": row["method"],
                "p1": 1e-4, "p2": 1e-4, "p12": row["p12"],
                "pp_h0": row["pp_h0"], "pp_h1": row["pp_h1"], "pp_h2": row["pp_h2"],
                "pp_h3": row["pp_h3"], "pp_h4": row["pp_h4"],
                "conditional_h4": row["conditional_h4"], "coloc_outcome": "not_graded_sensitivity_only",
            })
    write_gzip_tsv(staging / "endophenotype_prior_sensitivity.tsv.gz", sensitivity_rows, coloc_fields)


def run_plots(staging: Path) -> None:
    script = ROOT / "scripts" / "19_render_endophenotype_extension.R"
    subprocess.run(["Rscript", str(script), "--input-root", str(staging)], cwd=ROOT, check=True)


def make_checks(
    config: dict[str, Any], staging: Path, candidates: list[dict[str, str]], units: list[dict[str, Any]],
    decisions: list[dict[str, Any]], matrix: list[dict[str, Any]], routes: list[dict[str, Any]],
    baseline_checks: list[dict[str, Any]], source_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[tuple[str, Any, Any, bool, str]] = [
        ("candidate_context_count", 47, len(candidates), len(candidates) == 47, "frozen Phase 19 contexts"),
        ("unique_gene_count", 25, len({row['gene'] for row in candidates}), len({row['gene'] for row in candidates}) == 25, "frozen genes"),
        ("gene_biomarker_units", 75, len(units), len(units) == 75, "25 x 3"),
        ("nuclear_gate_decisions", 57, len(decisions), len(decisions) == 57, "19 x 3"),
        ("context_biomarker_rows", 141, len(matrix), len(matrix) == 141, "47 x 3"),
        ("mtdna_context_biomarker_rows", 60, sum(row['is_mtdna_gene'] is True for row in matrix), sum(row['is_mtdna_gene'] is True for row in matrix) == 60, "20 x 3"),
        ("all_gate_states_terminal", 57, sum(bool(row['gate_state']) for row in decisions), all(bool(row['gate_state']) for row in decisions), "no missing gate state"),
        ("all_qtl_routes_terminal", len(routes), sum(bool(row['route_terminal_status']) for row in routes), all(bool(row['route_terminal_status']) for row in routes), "zero routes is permitted"),
        ("baseline_hashes", "all_pass", sum(row['status'] == 'pass' for row in baseline_checks), all(row['status'] == 'pass' for row in baseline_checks), "all upstream files immutable"),
        ("gwas_source_checks", "all_pass", sum(row['status'] == 'pass' for row in source_checks), all(row['status'] == 'pass' for row in source_checks), "metadata and checksums"),
        ("candidate_magma_threshold", 0.05 / 57, float(config['analysis']['candidate_magma_p']), abs(float(config['analysis']['candidate_magma_p']) - 0.05 / 57) < 1e-15, "frozen Bonferroni"),
        ("gene_based_only_no_coloc", 0, sum(1 for decision in decisions if decision['gate_state'] == 'gene_based_signal_only' for route in routes if route['gene'] == decision['gene'] and route['trait_id'] == decision['trait_id']), not any(decision['gate_state'] == 'gene_based_signal_only' and any(route['gene'] == decision['gene'] and route['trait_id'] == decision['trait_id'] for route in routes) for decision in decisions), "MAGMA-only routes prohibited"),
        ("baseline_not_downgraded", "all", sum(GRADE_RANK.get(row['cumulative_phase19_grade'], -1) >= GRADE_RANK.get(row['baseline_grade'], -1) for row in matrix), all(GRADE_RANK.get(row['cumulative_phase19_grade'], -1) >= GRADE_RANK.get(row['baseline_grade'], -1) for row in matrix), "extension cannot downgrade"),
        ("execution_backend", "direct", config['execution']['backend'], config['execution']['backend'] == 'direct', "truthful local execution"),
    ]
    return [{
        "schema_version": SCHEMA, "check_id": check_id, "expected": expected,
        "observed": observed, "status": "pass" if passed else "fail", "detail": detail,
    } for check_id, expected, observed, passed, detail in checks]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase19_endophenotype_gwas_qtl_extension.yml")
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--execution-config", default=None)
    parser.add_argument("--task-mode", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--gate-only",
        action="store_true",
        help="Freeze the GWAS/MAGMA gate before any candidate-specific QTL acquisition.",
    )
    args = parser.parse_args()

    if args.task_mode not in {None, "genetic_support_endophenotype"}:
        raise RuntimeError(f"Unsupported --task-mode for endophenotype runner: {args.task_mode}")
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    if "biomarkers" not in config:
        configured = config.get("project", {}).get("phase19_endophenotype_gwas_qtl_extension_config")
        if not configured:
            raise RuntimeError(
                "project.phase19_endophenotype_gwas_qtl_extension_config is required in shared pipeline config"
            )
        config = yaml.safe_load(resolve(configured).read_text(encoding="utf-8"))
    output_root = resolve(args.output_root or config["outputs"]["root"])
    staging = Path(str(output_root) + ".staging")
    if output_root.exists() and not args.force:
        raise RuntimeError(f"Output exists: {output_root}; use --force for a deliberate replacement")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    baseline_checks: list[dict[str, Any]] = []
    for tier, root_key, manifest_key in [
        ("tier1", "tier1_root", "tier1_artifacts"),
        ("tier2", "tier2_root", "tier2_artifacts"),
        ("tier2_recovery", "recovery_root", "recovery_artifacts"),
    ]:
        baseline_checks.extend(verify_artifact_manifest(resolve(config["inputs"][root_key]), resolve(config["inputs"][manifest_key]), tier))

    candidates, region_by_gene, nuclear_genes, mtdna_genes = load_candidates(config)
    biomarker_manifest, source_inventory, gwas_source_checks = verify_biomarkers(config)
    units, context_units = screening_units(candidates, region_by_gene, biomarker_manifest)

    candidate_fields = ["schema_version", "candidate_id", "gene", "broad_network", "case_id", "case_label", "aggregate_acat_p", "aggregate_acat_q", "evidence_tier", "is_mtdna_gene", "requested_xqtl_context"]
    candidate_output = [{**row, "schema_version": SCHEMA} for row in candidates]
    write_tsv(staging / "endophenotype_candidate_manifest.tsv", candidate_output, candidate_fields)
    write_tsv(staging / "endophenotype_biomarker_manifest.tsv", biomarker_manifest, list(biomarker_manifest[0]))
    write_tsv(staging / "endophenotype_screening_units.tsv", units, list(units[0]))

    regional_summary, gwas_qc = scan_gwas(config, biomarker_manifest, units, region_by_gene, staging)
    write_tsv(staging / "endophenotype_gwas_qc.tsv", gwas_qc, list(gwas_qc[0]))
    write_tsv(staging / "endophenotype_regional_gwas_summary.tsv", regional_summary, list(regional_summary[0]))

    magma_rows, magma_map, magma_conditional = load_magma_results(config, biomarker_manifest, region_by_gene)
    write_tsv(staging / "endophenotype_magma_results.tsv", magma_rows, list(magma_rows[0]))
    conditional_fields = ["schema_version", "trait_id", "gene", "ensembl_gene_id", "unconditional_p", "candidate_significant", "window_10kb_p", "window_10kb_significant", "sensitivity_status", "conditional_status", "conditional_p", "regional_ambiguity", "reason"]
    write_tsv(staging / "endophenotype_magma_conditional.tsv", magma_conditional, conditional_fields)
    decisions = gate_decisions(regional_summary, magma_map)
    write_tsv(staging / "endophenotype_gate_decisions.tsv", decisions, list(decisions[0]))

    if args.gate_only:
        freeze_root = resolve(config["inputs"]["source_manifest_dir"])
        freeze_root.mkdir(parents=True, exist_ok=True)
        frozen_gate = freeze_root / "endophenotype_pre_qtl_gate_decisions.tsv"
        write_tsv(frozen_gate, decisions, list(decisions[0]))
        digest_path = freeze_root / "endophenotype_pre_qtl_gate_decisions.sha256"
        digest_path.write_text(f"{sha256(frozen_gate)}  {frozen_gate.name}\n", encoding="utf-8")
        signal_pairs = sum(row["regional_signal"] is True for row in decisions)
        magma_pairs = sum(row["magma_signal"] is True for row in decisions)
        print(f"Frozen 57 pre-QTL decisions at {frozen_gate}")
        print(f"Regional signal pairs: {signal_pairs}; MAGMA pairs: {magma_pairs}")
        return

    routes, qtl_coverage, overlap = build_qtl_routes(config, candidates, decisions)
    route_fields = ["schema_version", "route_id", "gene", "ensembl_gene_id", "trait_id", "source_accession", "qtl_source_id", "qtl_modality", "qtl_context", "context_match_level", "sample_overlap_state", "regional_gwas_signal", "qtl_measurement_state", "qtl_signal_state", "full_regional_qtl_available", "compatible_model_or_ld_available", "route_terminal_status", "coloc_outcome", "pp_h0", "pp_h1", "pp_h2", "pp_h3", "pp_h4", "conditional_h4", "method", "reason", "selection_frozen_before_result"]
    qtl_fields = ["schema_version", "route_id", "gene", "ensembl_gene_id", "trait_id", "qtl_source_id", "qtl_modality", "qtl_context", "context_match_level", "sample_overlap_state", "qtl_measurement_state", "qtl_signal_state", "full_regional_qtl_available", "compatible_model_or_ld_available", "reason"]
    overlap_fields = ["schema_version", "route_id", "gene", "trait_id", "gwas_source", "qtl_source", "phase18_vs_gwas", "phase18_vs_qtl", "gwas_vs_qtl", "independent_validation_permitted", "interpretation"]
    write_tsv(staging / "endophenotype_route_manifest.tsv", routes, route_fields)
    write_tsv(staging / "endophenotype_qtl_coverage.tsv", qtl_coverage, qtl_fields)
    write_tsv(staging / "endophenotype_sample_overlap_audit.tsv", overlap, overlap_fields)

    registry: list[dict[str, Any]] = []
    for trait in biomarker_manifest:
        registry.append({
            "schema_version": SCHEMA, "source_id": trait["source_accession"], "modality": "GWAS",
            "trait_or_context": trait["trait_id"], "ancestry": trait["ancestry"], "sample_size": trait["sample_size"],
            "genome_build": trait["genome_build"], "access_url": trait["source_url"],
            "full_statistics_access": "public_complete", "overlap_state": "possible_overlap_ROS_MAP",
            "selection_frozen_before_result": True,
        })
    for source in config["qtl_sources"]:
        registry.append({
            "schema_version": SCHEMA, "source_id": source["source_id"], "modality": source["modality"],
            "trait_or_context": source["context"], "ancestry": source["ancestry"], "sample_size": source["sample_size"],
            "genome_build": source["build"], "access_url": source["access_url"],
            "full_statistics_access": source["full_statistics_access"], "overlap_state": source["overlap_state"],
            "selection_frozen_before_result": True,
        })
    write_tsv(staging / "endophenotype_dataset_registry.tsv", registry, list(registry[0]))

    request_rows = [{
        "schema_version": SCHEMA, "request_id": f"gwas_{trait['trait_id']}",
        "source_id": trait["source_accession"], "role": "complete_endophenotype_GWAS",
        "requested": True, "obtained": True, "status": "validated",
        "reason": "official_GWAS_Catalog_file_obtained_after_article_Box_link_returned_404",
    } for trait in biomarker_manifest]
    request_rows.extend({
        "schema_version": SCHEMA, "request_id": route["route_id"], "source_id": route["qtl_source_id"],
        "role": f"{route['qtl_modality']}_coverage_model_and_LD", "requested": True,
        "obtained": route["route_terminal_status"] in {"precomputed_resolved", "custom_resolved"},
        "status": route["route_terminal_status"], "reason": route["reason"],
    } for route in routes)
    write_tsv(staging / "endophenotype_request_manifest.tsv", request_rows, list(request_rows[0]))

    for path, source_id, role, url in [
        (resolve(config["inputs"]["publication_supplement_8"]), "Timsina2026", "published_gene_prioritization_crosscheck", "https://www.nature.com/articles/s41467-026-71682-8"),
        (resolve(config["inputs"]["publication_supplement_9"]), "Timsina2026", "published_single_signal_coloc_crosscheck", "https://www.nature.com/articles/s41467-026-71682-8"),
        (resolve(config["inputs"]["magma_binary"]), "MAGMA_v1.10", "gene_based_test_binary", "https://vu.data.surf.nl/"),
        (resolve(config["inputs"]["magma_gene_locations"]), "FUMA_Ensembl_v110", "MAGMA_gene_locations_GRCh37", "https://fuma.ctglab.nl/downloadPage"),
    ]:
        source_inventory.append({
            "schema_version": SCHEMA, "source_id": source_id, "role": role,
            "source_version": "frozen_local", "path": str(path.relative_to(ROOT)), "url": url,
            "bytes": path.stat().st_size, "sha256": sha256(path), "validation_state": "validated",
        })
    for suffix in ["bed", "bim", "fam", "synonyms"]:
        path = Path(str(resolve(config["inputs"]["magma_reference_prefix"])) + f".{suffix}")
        if path.exists():
            source_inventory.append({
                "schema_version": SCHEMA, "source_id": "1000G_Phase3_EUR_FUMA", "role": f"MAGMA_LD_reference_{suffix}",
                "source_version": "MAGMA_official_2018_dbSNP151", "path": str(path.relative_to(ROOT)), "url": "https://cncr.nl/research/magma/",
                "bytes": path.stat().st_size, "sha256": sha256(path), "validation_state": "validated",
            })
    extension_data_root = resolve(config["inputs"]["source_manifest_dir"]).parent
    atlas_root = extension_data_root / "qtl_coverage" / "NG00184"
    atlas_catalog = extension_data_root / "inventory" / "NG00184.v1.csv"
    with atlas_catalog.open(newline="", encoding="utf-8-sig") as handle:
        atlas_rows = list(csv.DictReader(handle))
    atlas_by_name = {row["file_name"]: row for row in atlas_rows}
    atlas_names = [
        f"ADSP_FunGen_xQTL.v1.{modality}.{component}.tar"
        for modality in ("eQTL", "pQTL", "sQTL", "snuc-eQTL")
        for component in ("hmt_significant", "single_context_finemapping_all")
    ]
    atlas_names.append("ADSP_FunGen_xQTL.v1.metadata.json")
    for name in atlas_names:
        path = atlas_root / name
        record = atlas_by_name.get(name)
        if record is None or not path.exists():
            raise RuntimeError(f"Missing atlas inventory entry or local file: {name}")
        observed_md5 = md5(path)
        if observed_md5 != record["md5"].strip():
            raise RuntimeError(f"NG00184 checksum mismatch for {name}")
        source_inventory.append({
            "schema_version": SCHEMA, "source_id": "NG00184.v1",
            "role": "released_archive_or_metadata", "source_version": record["file_version_str"],
            "path": str(path.relative_to(ROOT)), "url": "https://dss.niagads.org/datasets/ng00184/",
            "bytes": path.stat().st_size, "sha256": sha256(path),
            "validation_state": f"validated_official_md5_{observed_md5}",
        })
    source_inventory.sort(key=lambda row: (row["source_id"], row["role"]))
    write_tsv(staging / "endophenotype_input_inventory.tsv", source_inventory, list(source_inventory[0]))
    source_checks = baseline_checks + gwas_source_checks
    write_tsv(staging / "endophenotype_source_checks.tsv", source_checks, list(source_checks[0]))

    write_empty_downstream(staging, routes, config)
    twas_rows = [{
        "schema_version": SCHEMA, "gene": decision["gene"], "trait_id": decision["trait_id"],
        "trigger_state": decision["gate_state"], "model_source": "NA", "model_context": "NA",
        "p_value": "NA", "corrected_significant": False,
        "terminal_status": "not_triggered" if decision["gate_state"] != "gene_based_signal_only" else "not_assessable_registered_prediction_model_not_available",
        "grade_contribution": "none", "reason": "TWAS_PWAS_is_conditional_support_and_no_eligible_validated_model_result_was_imported",
    } for decision in decisions]
    write_tsv(staging / "endophenotype_twas_pwas_followup.tsv", twas_rows, list(twas_rows[0]))

    matrix, evidence, assessability = integrate_evidence(config, candidates, context_units, decisions, routes)
    write_tsv(staging / "endophenotype_assessability.tsv", assessability, list(assessability[0]))
    write_tsv(staging / "endophenotype_evidence_summary.tsv", evidence, list(evidence[0]))
    write_tsv(staging / "endophenotype_context_biomarker_matrix.tsv", matrix, list(matrix[0]))
    figure_rows = [{
        "schema_version": SCHEMA, "candidate_id": row["candidate_id"], "gene": row["gene"],
        "broad_network": row["broad_network"], "trait_id": row["trait_id"],
        "extension_grade": row["extension_grade"], "gate_state": row["gate_state"],
        "regional_min_p": row["regional_min_p"], "regional_signal": row["regional_signal"],
        "magma_signal": row["magma_signal"], "newly_biomarker_supported": row["newly_biomarker_supported"],
    } for row in matrix]
    write_gzip_tsv(staging / "endophenotype_figure_data.tsv.gz", figure_rows, list(figure_rows[0]))

    analysis_manifest = [{
        "schema_version": SCHEMA, "analysis_id": config["analysis"]["analysis_id"],
        "genome_build": config["analysis"]["genome_build"], "execution_stage": config["execution"]["stage"],
        "execution_backend": config["execution"]["backend"], "publication_namespace": config["execution"]["publication_namespace"],
        "primary_traits": ";".join(row["trait_id"] for row in biomarker_manifest),
        "regional_signal_p": config["analysis"]["regional_signal_p"],
        "candidate_magma_p": config["analysis"]["candidate_magma_p"],
        "primary_coloc_method": "coloc.susie_when_complete_compatible_models_exist",
        "p12": config["analysis"]["primary_p12"], "strong_h4": config["analysis"]["strong_h4"],
        "strong_conditional_h4": config["analysis"]["strong_conditional_h4"],
        "candidate_selection_frozen": True, "qtl_selection_frozen_before_result": True,
        "full_phase19_complete": False,
    }]
    write_tsv(staging / "endophenotype_analysis_manifest.tsv", analysis_manifest, list(analysis_manifest[0]))

    run_plots(staging)
    checks = make_checks(config, staging, candidates, units, decisions, matrix, routes, baseline_checks, gwas_source_checks)
    write_tsv(staging / "endophenotype_checks.tsv", checks, list(checks[0]))
    if any(row["status"] != "pass" for row in checks):
        failed = [row["check_id"] for row in checks if row["status"] != "pass"]
        raise RuntimeError(f"Blocking checks failed: {failed}")

    pre_artifact_files = [name for name in DECLARED_FILES if name not in {"endophenotype_artifacts.tsv", "endophenotype_status.tsv"}]
    missing = [name for name in pre_artifact_files if not (staging / name).exists()]
    if missing:
        raise RuntimeError(f"Missing declared files before artifact freeze: {missing}")
    artifacts = [{
        "schema_version": SCHEMA, "path": name, "bytes": (staging / name).stat().st_size,
        "sha256": sha256(staging / name), "rows": rows_in_file(staging / name), "validation_state": "validated",
    } for name in pre_artifact_files]
    write_tsv(staging / "endophenotype_artifacts.tsv", artifacts, list(artifacts[0]))

    regional_signal_pairs = sum(row["regional_signal"] is True for row in decisions)
    gene_signal_pairs = sum(row["magma_signal"] is True for row in decisions)
    newly_supported_genes = len({row["gene"] for row in matrix if row["newly_biomarker_supported"] is True})
    status = [{
        "schema_version": SCHEMA,
        "validation_status": "validated_complete_endophenotype_gwas_qtl_extension",
        "run_id": "phase19_endophenotype_local_20260821",
        "execution_stage": config["execution"]["stage"], "execution_backend": config["execution"]["backend"],
        "publication_namespace": config["execution"]["publication_namespace"],
        "technical_status": "validated_complete", "scientific_status": "terminal_biomarker_specific_extension_complete",
        "baseline_phase19_hashes_unchanged": True, "full_phase19_complete": False,
        "unique_phase18_genes": 25, "nuclear_gene_biomarker_screens": 57,
        "terminal_nuclear_gate_decisions": 57, "regional_signal_pairs": regional_signal_pairs,
        "candidate_magma_signal_pairs": gene_signal_pairs, "generated_qtl_routes": len(routes),
        "terminal_qtl_routes": len(routes), "candidate_context_biomarker_rows": 141,
        "mtdna_context_biomarker_not_applicable_rows": 60,
        "newly_biomarker_supported_unique_genes": newly_supported_genes,
        "declared_output_files": 36, "undeclared_output_files": 0, "blocking_check_failures": 0,
        "artifact_manifest_sha256": sha256(staging / "endophenotype_artifacts.tsv"),
        "completed_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "next_required_action": "review_biomarker_specific_evidence_and_route_specific_data_limitations",
    }]
    write_tsv(staging / "endophenotype_status.tsv", status, list(status[0]))

    observed_files = sorted(path.name for path in staging.iterdir() if path.is_file())
    if observed_files != sorted(DECLARED_FILES):
        raise RuntimeError(f"Final file contract mismatch: {observed_files}")
    if output_root.exists():
        if not args.force:
            raise RuntimeError(f"Refusing to replace {output_root} without --force")
        shutil.rmtree(output_root)
    staging.replace(output_root)
    print(f"Published {len(DECLARED_FILES)} validated files to {output_root}")
    print(f"Regional signal pairs: {regional_signal_pairs}; MAGMA pairs: {gene_signal_pairs}; newly supported genes: {newly_supported_genes}")


if __name__ == "__main__":
    main()

