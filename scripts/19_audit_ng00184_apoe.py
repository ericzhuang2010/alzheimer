#!/usr/bin/env python3
"""Audit released NG00184 APOE xQTL evidence after the frozen GWAS gate."""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension"
QTL_ROOT = BASE / "qtl_regional/NG00184"
METADATA = BASE / "qtl_coverage/NG00184/ADSP_FunGen_xQTL.v1.metadata.json"
MANIFEST_ROOT = BASE / "source_manifest"
GATE = MANIFEST_ROOT / "endophenotype_pre_qtl_gate_decisions.tsv"
AUDIT = MANIFEST_ROOT / "endophenotype_ng00184_apoe_audit.tsv"
ROUTES = MANIFEST_ROOT / "endophenotype_route_results.tsv"
SCHEMA = "phase19_endophenotype_v1"

MODALITIES = ("eQTL", "pQTL", "sQTL", "snuc-eQTL")
TRAIT_IDS = ("csf_abeta42", "csf_total_tau", "csf_ptau181")
ROUTE_CONTEXT = {
    "pQTL": "brain_regions",
    "eQTL": "Astrocytes",
    "snuc-eQTL": "Astrocytes",
    "sQTL": "Astrocytes",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def safe_float(value: Any) -> float | None:
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def classify(path: Path) -> tuple[str, str, str]:
    parts = path.parts
    modality = next((value for value in MODALITIES if value in parts), "")
    component = (
        "hmt_significant"
        if "hmt_significant" in parts
        else "single_context_finemapping_all"
        if "single_context_finemapping_all" in parts
        else ""
    )
    cohort = parts[parts.index("v1") + 1] if "v1" in parts else "unknown"
    if not modality or not component:
        raise RuntimeError(f"Cannot classify released file: {path}")
    return modality, component, cohort


def load_metadata() -> dict[str, dict[str, Any]]:
    with METADATA.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    return {row["File name"]: row for row in rows}


def route_context_eligible(modality: str, metadata: dict[str, Any]) -> bool:
    cell_type = str(metadata.get("cell type", "")).lower()
    biosample_type = str(metadata.get("Biosample type", "")).lower()
    tissue_category = str(metadata.get("Tissue category", "")).lower()
    if modality == "snuc-eQTL":
        return cell_type == "astrocyte"
    if modality == "eQTL":
        return cell_type == "astrocyte" or (tissue_category == "brain" and biosample_type == "primary tissue")
    return tissue_category == "brain" and biosample_type == "primary tissue"


def info_value(value: str, key: str) -> str:
    match = re.search(rf"(?:^|;){re.escape(key)}=([^;]*)", value or "")
    return match.group(1) if match else ""


def scan_file(path: Path, metadata_by_file: dict[str, dict[str, Any]]) -> dict[str, Any]:
    modality, component, cohort = classify(path)
    official = metadata_by_file.get(path.name)
    if official is None:
        raise RuntimeError(f"Official metadata missing for released file: {path.name}")
    eligible = route_context_eligible(modality, official)
    apoe_rows = 0
    significant_rows = 0
    min_p: float | None = None
    min_fdr: float | None = None
    max_pip: float | None = None
    credible_set_rows = 0
    targets: set[str] = set()
    contexts: set[str] = set()
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"target_gene_symbol", "target_ensembl_id", "target", "target_info"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"Unexpected NG00184 schema in {path}: {reader.fieldnames}")
        for row in reader:
            if row.get("target_gene_symbol") != "APOE" and not row.get("target_ensembl_id", "").startswith("ENSG00000130203"):
                continue
            apoe_rows += 1
            targets.add(row.get("target", ""))
            context_id = info_value(row.get("target_info", ""), "xQTL_context_id")
            if context_id:
                contexts.add(context_id)
            p_value = safe_float(row.get("pval"))
            fdr = safe_float(row.get("FDR"))
            pip = safe_float(row.get("PIP"))
            if p_value is not None:
                min_p = p_value if min_p is None else min(min_p, p_value)
            if fdr is not None:
                min_fdr = fdr if min_fdr is None else min(min_fdr, fdr)
            if pip is not None:
                max_pip = pip if max_pip is None else max(max_pip, pip)
            if any(row.get(column, "") not in {"", "0", "."} for column in ("cs_95", "cs_70", "cs_50")):
                credible_set_rows += 1
            is_hmt_signif = info_value(row.get("target_info", ""), "is_hmt_signif").lower() == "true"
            if component == "hmt_significant" or is_hmt_signif:
                significant_rows += 1
    return {
        "schema_version": SCHEMA,
        "qtl_source_id": "NG00184.v1",
        "qtl_modality": modality,
        "cohort": cohort,
        "context_cell_type": official.get("cell type", "NA"),
        "biosample_type": official.get("Biosample type", "NA"),
        "tissue_category": official.get("Tissue category", "NA"),
        "route_context_eligible": eligible,
        "release_component": component,
        "released_file": str(path.relative_to(ROOT)),
        "apoe_rows": apoe_rows,
        "apoe_source_significant_rows": significant_rows,
        "min_p": min_p if min_p is not None else "NA",
        "min_fdr": min_fdr if min_fdr is not None else "NA",
        "max_pip": max_pip if max_pip is not None else "NA",
        "credible_set_rows": credible_set_rows,
        "target_ids": ";".join(sorted(value for value in targets if value)) or "none",
        "context_ids": ";".join(sorted(contexts)) or "none",
        "evidence_state": (
            "source_significant"
            if significant_rows
            else "measured_no_source_significant_signal"
            if apoe_rows
            else "no_apoe_rows"
        ),
    }


def build_route_result(modality: str, trait_id: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    hmt_rows = sum(int(row["apoe_rows"]) for row in rows if row["release_component"] == "hmt_significant")
    fm_rows = sum(int(row["apoe_rows"]) for row in rows if row["release_component"] == "single_context_finemapping_all")
    significant_rows = sum(int(row["apoe_source_significant_rows"]) for row in rows)
    cohorts = sorted({str(row["cohort"]) for row in rows if int(row["apoe_rows"])})
    context_ids: set[str] = set()
    for row in rows:
        if int(row["apoe_rows"]) and row["context_ids"] != "none":
            context_ids.update(str(row["context_ids"]).split(";"))
    if significant_rows:
        measurement = "measured_candidate_trait"
        signal = "source_significant_cis_signal"
        terminal = "model_or_ld_incompatible"
        reason = (
            f"NG00184_APOE_signal_present_hmt_rows={hmt_rows}_finemap_rows={fm_rows};"
            "released_finemapping_contains_PIP_and_credible_set_membership_but_not_a_complete_"
            "multisignal_model_or_ancestry_matched_LD_required_for_primary_colocalization"
        )
    elif fm_rows:
        measurement = "measured_candidate_trait"
        signal = "no_source_significant_cis_signal"
        terminal = "no_regional_qtl_signal"
        reason = (
            f"NG00184_APOE_measured_in_{','.join(cohorts)}_with_finemap_rows={fm_rows}_but_"
            f"hmt_significant_rows={hmt_rows}_and_all_released_APOE_rows_are_is_hmt_signif_false"
        )
    else:
        measurement = "measurement_unresolved"
        signal = "not_assessable"
        terminal = "not_assessable"
        reason = "NG00184_selected_released_files_contain_no_APOE_rows_for_this_modality_or_registered_context"
    context = ROUTE_CONTEXT[modality]
    return {
        "coloc_outcome": "NA",
        "compatible_model_or_ld_available": "FALSE",
        "conditional_h4": "",
        "full_regional_qtl_available": "FALSE",
        "method": "released_hmt_and_PIP_credible_set_audit_no_primary_coloc",
        "pp_h0": "",
        "pp_h1": "",
        "pp_h2": "",
        "pp_h3": "",
        "pp_h4": "",
        "qtl_measurement_state": measurement,
        "qtl_signal_state": signal,
        "qtl_source_id": "NG00184.v1",
        "reason": reason + (f";contexts={','.join(sorted(context_ids))}" if context_ids else ""),
        "route_id": f"APOE__{trait_id}__NG00184.v1__{modality}__{context}",
        "route_terminal_status": terminal,
    }


def main() -> None:
    frozen = read_tsv(GATE)
    positives = {
        (row["gene"], row["trait_id"])
        for row in frozen
        if row["gate_state"] in {"regional_and_gene_based_signal", "regional_signal_only"}
    }
    expected = {("APOE", trait_id) for trait_id in TRAIT_IDS}
    if positives != expected:
        raise RuntimeError(f"Frozen positive set changed: expected {expected}, observed {positives}")

    metadata_by_file = load_metadata()
    files = sorted(path for path in QTL_ROOT.rglob("*.bed.gz") if not path.name.endswith(".tbi"))
    if not files:
        raise RuntimeError(f"No extracted NG00184 chromosome files found under {QTL_ROOT}")
    audit_rows = [scan_file(path, metadata_by_file) for path in files]
    observed_components = {
        (row["qtl_modality"], row["release_component"])
        for row in audit_rows
    }
    expected_components = {
        (modality, component)
        for modality in MODALITIES
        for component in ("hmt_significant", "single_context_finemapping_all")
    }
    missing = expected_components - observed_components
    if missing:
        raise RuntimeError(f"NG00184 extraction incomplete; missing modality/components: {sorted(missing)}")

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit_fields = list(audit_rows[0])
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=audit_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit_rows)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        if row["route_context_eligible"] is True:
            grouped[str(row["qtl_modality"])].append(row)
    additions = [
        build_route_result(modality, trait_id, grouped[modality])
        for trait_id in TRAIT_IDS
        for modality in MODALITIES
    ]

    existing = read_tsv(ROUTES) if ROUTES.exists() else []
    keep = [row for row in existing if row.get("qtl_source_id") != "NG00184.v1"]
    combined = sorted(keep + additions, key=lambda row: row["route_id"])
    route_fields = list(combined[0])
    temporary = ROUTES.with_suffix(".tsv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=route_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(combined)
    temporary.replace(ROUTES)

    by_modality = {
        modality: {
            "hmt_rows": sum(int(row["apoe_rows"]) for row in grouped[modality] if row["release_component"] == "hmt_significant"),
            "finemap_rows": sum(int(row["apoe_rows"]) for row in grouped[modality] if row["release_component"] == "single_context_finemapping_all"),
        }
        for modality in MODALITIES
    }
    print(f"Audited {len(files)} released chromosome-19 files; APOE summary: {by_modality}")
    print(f"Wrote {AUDIT.relative_to(ROOT)} and {len(additions)} NG00184 route results")


if __name__ == "__main__":
    main()
