#!/usr/bin/env python3
"""Extract and audit APOE QTL routes after the immutable endophenotype gate."""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "phase19_endophenotype_gwas_qtl_extension_v1"
APOE_ID = "ENSG00000130203"
APOE_PROTEINS = OrderedDict([
    ("GCST90424891", "Apolipoprotein E"),
    ("GCST90425531", "Apolipoprotein E (isoform E3)"),
    ("GCST90425532", "Apolipoprotein E (isoform E4)"),
    ("GCST90426314", "Apolipoprotein E (isoform E2)"),
])


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def finite(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def read_gwas(path: Path, start: int, end: int) -> dict[str, dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {}
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["chromosome"] not in {"19", "chr19"}:
                continue
            position = int(row["base_pair_location"])
            if position < start or position > end:
                continue
            rsid = row.get("rsid", "")
            beta = finite(row.get("beta", ""))
            se = finite(row.get("standard_error", ""))
            if not rsid.startswith("rs") or beta is None or se is None or se <= 0 or rsid in variants:
                continue
            variants[rsid] = {
                "rsid": rsid,
                "position": position,
                "effect_allele": row["effect_allele"].upper(),
                "other_allele": row["other_allele"].upper(),
                "beta": beta,
                "se": se,
            }
    return variants


def read_pqtl(path: Path, start: int, end: int) -> tuple[dict[str, dict[str, Any]], float]:
    variants: dict[str, dict[str, Any]] = {}
    minimum_p = 1.0
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["chromosome"] not in {"19", "chr19"}:
                continue
            position = int(row["base_pair_location"])
            if position < start or position > end:
                continue
            rsid = row.get("rs_id", "")
            beta = finite(row.get("beta", ""))
            se = finite(row.get("standard_error", ""))
            neglog = finite(row.get("neg_log_10_p_value", ""))
            sample_size = finite(row.get("n", ""))
            if not rsid.startswith("rs") or beta is None or se is None or se <= 0 or rsid in variants:
                continue
            p_value = 10 ** (-neglog) if neglog is not None and neglog < 323 else (0.0 if neglog is not None else 1.0)
            minimum_p = min(minimum_p, p_value)
            variants[rsid] = {
                "rsid": rsid,
                "position": position,
                "effect_allele": row["effect_allele"].upper(),
                "other_allele": row["other_allele"].upper(),
                "beta": beta,
                "se": se,
                "n": sample_size,
                "p_value": p_value,
            }
    return variants, minimum_p


def read_eqtl(path: Path, start: int, end: int) -> tuple[dict[str, dict[str, Any]], float]:
    variants: dict[str, dict[str, Any]] = {}
    minimum_p = 1.0
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["gene_id"].split(".")[0] != APOE_ID:
                continue
            position = int(row["position"])
            if position < start or position > end:
                continue
            rsid = row["rsid"]
            beta = finite(row["beta"])
            se = finite(row["se"])
            p_value = finite(row["pvalue"])
            if not rsid.startswith("rs") or beta is None or se is None or se <= 0 or rsid in variants:
                continue
            if p_value is not None:
                minimum_p = min(minimum_p, p_value)
            variants[rsid] = {
                "rsid": rsid,
                "position": position,
                "effect_allele": row["alt"].upper(),
                "other_allele": row["ref"].upper(),
                "beta": beta,
                "se": se,
                "n": 211,
                "p_value": p_value,
            }
    return variants, minimum_p


def harmonize(gwas: dict[str, dict[str, Any]], qtl: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    counts = {"gwas_variants": len(gwas), "qtl_variants": len(qtl), "shared_rsids": 0, "included": 0, "swapped": 0, "palindromic_excluded": 0, "allele_mismatch": 0}
    for rsid in sorted(set(gwas) & set(qtl)):
        counts["shared_rsids"] += 1
        g = gwas[rsid]
        q = qtl[rsid]
        if {g["effect_allele"], g["other_allele"]} in ({"A", "T"}, {"C", "G"}):
            counts["palindromic_excluded"] += 1
            continue
        if g["effect_allele"] == q["effect_allele"] and g["other_allele"] == q["other_allele"]:
            q_beta = q["beta"]
            state = "direct"
        elif g["effect_allele"] == q["other_allele"] and g["other_allele"] == q["effect_allele"]:
            q_beta = -q["beta"]
            state = "swapped"
            counts["swapped"] += 1
        else:
            counts["allele_mismatch"] += 1
            continue
        rows.append({
            "rsid": rsid,
            "position": g["position"],
            "gwas_effect_allele": g["effect_allele"],
            "gwas_other_allele": g["other_allele"],
            "qtl_original_effect_allele": q["effect_allele"],
            "alignment_state": state,
            "gwas_beta": g["beta"],
            "gwas_se": g["se"],
            "qtl_beta": q_beta,
            "qtl_se": q["se"],
            "qtl_n": q.get("n", "NA"),
        })
    counts["included"] = len(rows)
    return rows, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase19_endophenotype_gwas_qtl_extension.yml")
    args = parser.parse_args()
    config = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    source_manifest = resolve(config["inputs"]["source_manifest_dir"])
    work = resolve(config["inputs"]["work_dir"]) / "coloc_sensitivity"
    work.mkdir(parents=True, exist_ok=True)

    gate = read_tsv(source_manifest / "endophenotype_pre_qtl_gate_decisions.tsv")
    positive = [row for row in gate if row["regional_signal"] == "TRUE"]
    if {(row["gene"], row["trait_id"]) for row in positive} != {
        ("APOE", "csf_abeta42"), ("APOE", "csf_total_tau"), ("APOE", "csf_ptau181")
    }:
        raise RuntimeError("Frozen gate-positive set drifted; expected APOE for all three biomarkers")

    region = next(row for row in read_tsv(resolve(config["inputs"]["recovery_regions"])) if row["gene"] == "APOE")
    start, end = int(region["window_start"]), int(region["window_end"])
    biomarker_by_id = {row["trait_id"]: row for row in config["biomarkers"]}
    gwas = {
        trait_id: read_gwas(resolve(trait["harmonized_file"]), start, end)
        for trait_id, trait in biomarker_by_id.items()
    }

    pqtl_root = resolve(config["inputs"]["qtl_regional_dir"]) / "NG00130_APOE"
    pqtl: dict[str, dict[str, dict[str, Any]]] = {}
    pqtl_min: dict[str, float] = {}
    for accession in APOE_PROTEINS:
        path = pqtl_root / f"{accession}.tsv.gz"
        if not path.exists():
            raise RuntimeError(f"Missing gate-authorized pQTL file: {path}")
        pqtl[accession], pqtl_min[accession] = read_pqtl(path, start, end)

    eqtl_path = ROOT / "data/reference/phase19_genetic_support/tier2_recovery/regional_qtl/QTD000579.candidate_dense_eqtl.tsv.gz"
    eqtl, eqtl_min = read_eqtl(eqtl_path, start, end)

    manifest_rows: list[dict[str, Any]] = []
    harmonization_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    for accession, label in APOE_PROTEINS.items():
        inventory_rows.append({
            "schema_version": SCHEMA, "qtl_source_id": "NG00130.v2", "qtl_accession": accession,
            "molecular_trait": label, "candidate_gene": "APOE", "measurement_state": "measured",
            "regional_variants": len(pqtl[accession]), "regional_min_p": pqtl_min[accession],
            "source_signal_rule": "source_reported_genome_wide_p_lt_5e-8",
            "source_signal": pqtl_min[accession] < 5e-8,
            "full_regional_statistics": True, "released_multisignal_model": False,
            "qtl_ancestry_matched_ld": False,
        })
        for trait_id in biomarker_by_id:
            rows, counts = harmonize(gwas[trait_id], pqtl[accession])
            matched_path = work / f"{trait_id}__{accession}.tsv"
            write_tsv(matched_path, rows, list(rows[0]) if rows else ["rsid"])
            qtl_n_values = [float(row["qtl_n"]) for row in rows if str(row["qtl_n"]) != "NA"]
            manifest_rows.append({
                "trait_id": trait_id, "qtl_source_id": "NG00130.v2",
                "molecular_trait": label, "qtl_accession": accession, "qtl_context": "CSF",
                "matched_file": str(matched_path), "gwas_n": biomarker_by_id[trait_id]["sample_size"],
                "qtl_n": int(round(sorted(qtl_n_values)[len(qtl_n_values) // 2])) if qtl_n_values else 3506,
            })
            harmonization_rows.append({"schema_version": SCHEMA, "trait_id": trait_id, "qtl_source_id": "NG00130.v2", "qtl_accession": accession, **counts})

    inventory_rows.append({
        "schema_version": SCHEMA, "qtl_source_id": "EQTL_Catalogue_r7", "qtl_accession": "QTD000579",
        "molecular_trait": "APOE expression", "candidate_gene": "APOE", "measurement_state": "measured",
        "regional_variants": len(eqtl), "regional_min_p": eqtl_min,
        "source_signal_rule": "release_global_q_value_le_0.05_threshold_p_4.339524e-6",
        "source_signal": eqtl_min <= 4.33952438812706e-6,
        "full_regional_statistics": True, "released_multisignal_model": False,
        "qtl_ancestry_matched_ld": False,
    })
    for trait_id in biomarker_by_id:
        rows, counts = harmonize(gwas[trait_id], eqtl)
        matched_path = work / f"{trait_id}__QTD000579.tsv"
        write_tsv(matched_path, rows, list(rows[0]) if rows else ["rsid"])
        manifest_rows.append({
            "trait_id": trait_id, "qtl_source_id": "EQTL_Catalogue_r7",
            "molecular_trait": "APOE expression", "qtl_accession": "QTD000579",
            "qtl_context": "bulk neocortex fallback", "matched_file": str(matched_path),
            "gwas_n": biomarker_by_id[trait_id]["sample_size"], "qtl_n": 211,
        })
        harmonization_rows.append({"schema_version": SCHEMA, "trait_id": trait_id, "qtl_source_id": "EQTL_Catalogue_r7", "qtl_accession": "QTD000579", **counts})

    manifest_path = work / "coloc_abf_manifest.tsv"
    write_tsv(manifest_path, manifest_rows, list(manifest_rows[0]))
    sensitivity_path = source_manifest / "endophenotype_coloc_abf_sensitivity.tsv"
    subprocess.run([
        "Rscript", str(ROOT / "scripts/19_run_endophenotype_coloc_sensitivity.R"),
        "--manifest", str(manifest_path), "--output", str(sensitivity_path),
    ], cwd=ROOT, check=True)

    sensitivity = read_tsv(sensitivity_path)
    primary = {
        (row["trait_id"], row["qtl_source_id"], row["qtl_accession"]): row
        for row in sensitivity if abs(float(row["p12"]) - 5e-6) < 1e-12
    }
    route_rows: list[dict[str, Any]] = []
    for trait_id in biomarker_by_id:
        for source_id, modality, context, accession in [
            ("NG00130.v2", "pQTL", "CSF", "GCST90424891"),
            ("EQTL_Catalogue_r7", "eQTL", "Astrocytes", "QTD000579"),
        ]:
            result = primary.get((trait_id, source_id, accession), {})
            route_rows.append({
                "route_id": f"APOE__{trait_id}__{source_id}__{modality}__{context}",
                "qtl_source_id": source_id,
                "qtl_measurement_state": "measured_candidate_trait",
                "qtl_signal_state": "source_significant_cis_signal",
                "full_regional_qtl_available": "TRUE",
                "compatible_model_or_ld_available": "FALSE",
                "route_terminal_status": "model_or_ld_incompatible",
                "coloc_outcome": "NA",
                "pp_h0": result.get("pp_h0", "NA"), "pp_h1": result.get("pp_h1", "NA"),
                "pp_h2": result.get("pp_h2", "NA"), "pp_h3": result.get("pp_h3", "NA"),
                "pp_h4": result.get("pp_h4", "NA"), "conditional_h4": result.get("conditional_h4", "NA"),
                "method": "coloc.abf_single_signal_sensitivity_only",
                "reason": "single_signal_sensitivity_completed_but_primary_multisignal_route_lacks_released_QTL_model_or_QTL_ancestry_matched_LD",
            })
        route_rows.extend([
            {
                "route_id": f"APOE__{trait_id}__EQTL_Catalogue_r7__sQTL__Astrocytes",
                "qtl_source_id": "EQTL_Catalogue_r7", "qtl_measurement_state": "measurement_unresolved",
                "qtl_signal_state": "not_assessable", "full_regional_qtl_available": "FALSE",
                "compatible_model_or_ld_available": "FALSE", "route_terminal_status": "not_assessable",
                "coloc_outcome": "NA", "method": "not_run",
                "reason": "target_gene_splicing_event_absent_from_conditionally_detected_release_and_measurement_status_unresolved",
            },
            {
                "route_id": f"APOE__{trait_id}__scMetaBrain_2026__eQTL__Astrocytes",
                "qtl_source_id": "scMetaBrain_2026", "qtl_measurement_state": "published_resource_no_candidate_complete_model_imported",
                "qtl_signal_state": "not_assessable", "full_regional_qtl_available": "FALSE",
                "compatible_model_or_ld_available": "FALSE", "route_terminal_status": "not_assessable",
                "coloc_outcome": "NA", "method": "not_run",
                "reason": "candidate_level_complete_statistics_and_compatible_released_model_not_available_in_public_local_inventory",
            },
            {
                "route_id": f"APOE__{trait_id}__PsychAD_snRNA_eQTL__eQTL__Astrocytes",
                "qtl_source_id": "PsychAD_snRNA_eQTL", "qtl_measurement_state": "resource_exists_controlled_or_request_access",
                "qtl_signal_state": "not_assessable", "full_regional_qtl_available": "FALSE",
                "compatible_model_or_ld_available": "FALSE", "route_terminal_status": "not_assessable",
                "coloc_outcome": "NA", "method": "not_run",
                "reason": "full_candidate_statistics_not_publicly_downloadable_and_ROSMAP_overlap_prevents_independent_validation",
            },
        ])

    existing_path = source_manifest / "endophenotype_route_results.tsv"
    if existing_path.exists():
        route_rows.extend(row for row in read_tsv(existing_path) if row.get("qtl_source_id") == "NG00184.v1")
    route_fields = sorted({key for row in route_rows for key in row})
    write_tsv(existing_path, route_rows, route_fields)
    write_tsv(source_manifest / "endophenotype_qtl_candidate_inventory.tsv", inventory_rows, list(inventory_rows[0]))
    write_tsv(source_manifest / "endophenotype_harmonization_summary.tsv", harmonization_rows, list(harmonization_rows[0]))
    print(f"Prepared {len(manifest_rows)} APOE sensitivity comparisons and {len(route_rows)} route results")


if __name__ == "__main__":
    main()
