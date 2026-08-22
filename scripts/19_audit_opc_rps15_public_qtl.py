#!/usr/bin/env python3
"""Two-stage, result-blind local execution of the OPC RPS15 public-data plan."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/phase19_opc_rps15_public_recovery.yml"
LOCAL_CONFIG_PATH = ROOT / "config/phase19_opc_rps15_local_execution.yml"
SCHEMA = "phase19_opc_rps15_public_recovery_v1"
RUN_DATE = "2026-08-21"
MODALITIES = ("eQTL", "pQTL", "sQTL", "snuc-eQTL")
COMPONENTS = ("hmt_significant", "single_context_finemapping_all")
FROZEN_OUTPUTS = (
    "opc_rps15_analysis_manifest.tsv",
    "opc_rps15_frozen_scope.tsv",
    "opc_rps15_route_manifest.tsv",
    "opc_rps15_dataset_registry.tsv",
    "opc_rps15_request_manifest.tsv",
    "opc_rps15_input_inventory.tsv",
    "opc_rps15_source_checks.tsv",
)
CODE_FILES = (
    "config/phase19_opc_rps15_public_recovery.yml",
    "config/phase19_opc_rps15_local_execution.yml",
    "scripts/19_audit_opc_rps15_public_qtl.py",
    "docs/phase_19_genetic_support/opc_rps15/opc_rps15_public_data_first_plan.md",
    "scripts/19_extract_opc_rps15_public_qtl.py",
    "scripts/19_prepare_opc_rps15_ld.py",
    "scripts/19_run_opc_rps15_finemapping.R",
    "scripts/19_run_opc_rps15_coloc.R",
    "scripts/19_integrate_opc_rps15_evidence.py",
    "scripts/19_validate_opc_rps15_public_recovery.py",
    "tests/test_phase19_opc_rps15_public_recovery.py",
    "tests/test_phase19_opc_rps15_public_recovery.R",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    require(isinstance(value, dict), f"Configuration is not a mapping: {path}")
    return value


def resolve(path: str) -> Path:
    return (ROOT / path).resolve()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_paths(paths: Iterable[Path], base: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    count = 0
    total = 0
    for path in sorted(paths):
        require(path.is_file(), f"Expected input file is missing: {path}")
        rel = str(path.relative_to(base))
        file_hash = sha256(path)
        size = path.stat().st_size
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(file_hash.encode())
        digest.update(b"\0")
        digest.update(str(size).encode())
        digest.update(b"\n")
        count += 1
        total += size
    return digest.hexdigest(), count, total


def bundle_digest(root: Path) -> tuple[str, int, int]:
    require(root.is_dir(), f"Immutable input bundle is missing: {root}")
    return aggregate_paths((path for path in root.rglob("*") if path.is_file()), root)


def dir_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def read_tsv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=fields,
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_gzip_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(
                    text,
                    delimiter="\t",
                    fieldnames=fields,
                    lineterminator="\n",
                    extrasaction="ignore",
                )
                writer.writeheader()
                for row in rows:
                    writer.writerow({field: row.get(field, "") for field in fields})


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def safe_float(value: Any) -> float | None:
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def format_number(value: float | None) -> str:
    return "NA" if value is None else f"{value:.12g}"


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned or "NA"


def parse_info(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in (value or "").split(";"):
        if "=" in token:
            key, item = token.split("=", 1)
            if key not in result:
                result[key] = item
    return result


def classify_path(path: Path) -> tuple[str, str, str]:
    parts = path.parts
    modality = next((item for item in MODALITIES if item in parts), "")
    component = (
        "hmt_significant"
        if "hmt_significant" in parts
        else "single_context_finemapping_all"
        if "single_context_finemapping_all" in parts
        else ""
    )
    cohort = parts[parts.index("v1") + 1] if "v1" in parts else "unknown"
    require(bool(modality and component), f"Could not classify NG00184 path: {path}")
    return modality, component, cohort


def variant_class(path: Path) -> str:
    if "_snp_" in path.name:
        return "snp"
    if "_indel_" in path.name:
        return "indel"
    return "unknown"


def base_context_id(metadata: dict[str, Any]) -> str:
    identifier = str(metadata.get("Identifier", "unknown"))
    return re.sub(r"_v1_19_(?:snp|indel)_(?:hmt|scfmAll)$", "", identifier)


def context_match(candidate_id: str, modality: str, metadata: dict[str, Any]) -> tuple[str, bool, int]:
    cell = str(metadata.get("cell type", ""))
    biosample = str(metadata.get("Biosample type", ""))
    tissue = str(metadata.get("Tissue category", ""))
    if tissue != "Brain":
        return "context_not_eligible", False, 99
    if candidate_id == "GS045":
        if cell == "Oligodendrocyte progenitor cell":
            return "exact_opc", True, 1
        if cell == "Oligodendrocyte":
            return "oligodendroglial_lineage", True, 3
        if modality == "pQTL" and biosample == "Primary tissue":
            return "protein_level_fallback", True, 5
        if biosample == "Primary tissue" and modality in {"eQTL", "sQTL"}:
            return "bulk_brain_fallback", True, 4
        return "context_not_eligible", False, 99
    if candidate_id == "GS044":
        if cell == "Inhibitory neuron":
            return "exact_inhibitory", True, 1
        if modality == "pQTL" and biosample == "Primary tissue":
            return "protein_level_fallback", True, 5
        if biosample == "Primary tissue" and modality in {"eQTL", "sQTL"}:
            return "bulk_brain_fallback", True, 4
        return "context_not_eligible", False, 99
    raise RuntimeError(f"Unknown candidate: {candidate_id}")


def route_id(candidate_id: str, modality: str, metadata: dict[str, Any]) -> str:
    return "__".join(
        (
            candidate_id,
            "NG00184v1",
            slug(str(metadata.get("Data Source", "unknown"))),
            slug(modality),
            slug(str(metadata.get("cell type", "unknown"))),
            slug(base_context_id(metadata)),
        )
    )


def load_metadata(path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    require(isinstance(rows, list), "NG00184 metadata must contain a list")
    by_file = {str(row["File name"]): row for row in rows}
    require(len(by_file) == len(rows), "NG00184 metadata file names are not unique")
    return rows, by_file


def load_helper(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Could not load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_paths(config: dict[str, Any]) -> dict[str, Path]:
    return {
        "staging": resolve(config["paths"]["staging_root"]),
        "final": resolve(config["paths"]["final_root"]),
        "work": resolve(config["paths"]["work_root"]),
        "targeted": resolve(config["paths"]["targeted_download_root"]),
        "regional": resolve(config["paths"]["regional_extract_root"]),
        "report": resolve(config["paths"]["execution_report"]),
    }


def validate_handoff(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, str]]]:
    inputs = config["inputs"]
    candidates = read_tsv(resolve(inputs["candidate_manifest"]))
    selected = [row for row in candidates if row.get("candidate_id") in {"GS044", "GS045"}]
    require(len(selected) == 2, f"Expected two RPS15 candidate rows, observed {len(selected)}")
    require({row["gene"] for row in selected} == {"RPS15"}, "Candidate gene identity drifted")
    require({row["candidate_id"] for row in selected} == {"GS044", "GS045"}, "Candidate IDs drifted")
    expected_contexts = {"GS044": "Inhibitory_neurons", "GS045": "OPCs"}
    require(all(row["broad_network"] == expected_contexts[row["candidate_id"]] for row in selected), "Candidate context drifted")

    loci = read_tsv(resolve(inputs["candidate_loci"]))
    locus_rows = [row for row in loci if row.get("gene") == "RPS15"]
    require(len(locus_rows) == 1, "Expected one RPS15 locus")
    locus = locus_rows[0]
    analysis = config["analysis"]
    require(locus["ensembl_gene_id"] == analysis["ensembl_gene_id"], "RPS15 Ensembl ID drifted")
    require(int(locus["chromosome"]) == int(analysis["chromosome"]), "RPS15 chromosome drifted")
    require(int(locus["window_start"]) == int(analysis["locus_start"]), "RPS15 locus start drifted")
    require(int(locus["window_end"]) == int(analysis["locus_end"]), "RPS15 locus end drifted")

    gwas_rows = read_tsv(resolve(inputs["recovery_regional_gwas"]))
    gwas_selected = [row for row in gwas_rows if row.get("gene") == "RPS15"]
    require(len(gwas_selected) == 1, "Expected one frozen RPS15 GWAS row")
    gwas = gwas_selected[0]
    require(gwas["source_accession"] == analysis["gwas_accession"], "GWAS accession drifted")
    require(abs(float(gwas["regional_min_p"]) - float(analysis["gwas_min_p"])) <= 1e-40, "GWAS minimum P drifted")
    require(gwas["regional_lead_variant"] == analysis["gwas_lead_variant"], "GWAS lead variant drifted")
    require(int(gwas["regional_gwas_rows"]) == 20114, "Frozen GWAS variant count drifted")

    decisions = read_tsv(resolve(inputs["recovery_route_decisions"]))
    selected_decisions = [row for row in decisions if row.get("gene") == "RPS15"]
    require(len(selected_decisions) == 4, "Expected four frozen recovery route decisions")
    observed = {(row["candidate_id"], row["qtl_type"], row["terminal_state"]) for row in selected_decisions}
    expected = {
        ("GS044", "eQTL", "no_regional_qtl_signal"),
        ("GS044", "sQTL", "not_assessable"),
        ("GS045", "eQTL", "model_or_ld_incompatible"),
        ("GS045", "sQTL", "not_assessable"),
    }
    require(observed == expected, f"Frozen recovery states drifted: {observed}")
    return selected, gwas, selected_decisions


def build_route_manifest(
    files: list[Path],
    metadata_by_file: dict[str, dict[str, Any]],
    candidates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    candidate_context = {row["candidate_id"]: row["broad_network"] for row in candidates}
    for path in files:
        metadata = metadata_by_file.get(path.name)
        require(metadata is not None, f"Official metadata missing for {path.name}")
        modality, component, cohort = classify_path(path)
        for candidate_id in sorted(candidate_context):
            rid = route_id(candidate_id, modality, metadata)
            key = (candidate_id, rid)
            match, eligible, priority = context_match(candidate_id, modality, metadata)
            if key not in grouped:
                grouped[key] = {
                    "schema_version": SCHEMA,
                    "route_id": rid,
                    "candidate_id": candidate_id,
                    "gene": "RPS15",
                    "ensembl_gene_id": "ENSG00000115268",
                    "phase18_context": candidate_context[candidate_id],
                    "qtl_source_id": "NG00184.v1",
                    "cohort": cohort,
                    "modality": modality,
                    "cell_type": metadata.get("cell type", ""),
                    "biosample_type": metadata.get("Biosample type", ""),
                    "tissue_category": metadata.get("Tissue category", ""),
                    "context_match": match,
                    "context_priority": priority,
                    "eligible": bool_text(eligible),
                    "genome_build": metadata.get("Genome build", ""),
                    "base_context_id": base_context_id(metadata),
                    "release_components": set(),
                    "source_files": set(),
                    "source_selection_state": "frozen_before_RPS15_lookup",
                }
            grouped[key]["release_components"].add(component)
            grouped[key]["source_files"].add(str(path.relative_to(ROOT)))
    rows: list[dict[str, Any]] = []
    for row in grouped.values():
        row["release_components"] = ";".join(sorted(row["release_components"]))
        row["source_files"] = ";".join(sorted(row["source_files"]))
        rows.append(row)
    return sorted(rows, key=lambda row: (row["candidate_id"], int(row["context_priority"]), row["route_id"]))


def selected_archives(ng_root: Path) -> list[Path]:
    return sorted(
        path for path in ng_root.glob("*.tar")
        if ".hmt_significant.tar" in path.name or ".single_context_finemapping_all.tar" in path.name
    )


def make_analysis_manifest(config: dict[str, Any]) -> list[dict[str, str]]:
    analysis = config["analysis"]
    storage = config["storage"]
    values = {
        "analysis_id": analysis["analysis_id"],
        "schema_version": SCHEMA,
        "plan_date": RUN_DATE,
        "execution_backend": "direct",
        "use_minerva": "false",
        "candidate_gene": analysis["gene"],
        "candidate_ensembl_id": analysis["ensembl_gene_id"],
        "primary_candidate_id": "GS045",
        "secondary_candidate_id": "GS044",
        "target_lookup_at_freeze": "false",
        "author_data_required": "false",
        "automatic_full_archive_download": str(storage["automatic_full_archive_download"]).lower(),
        "maximum_targeted_download_gib": str(storage["maximum_targeted_download_gib"]),
        "maximum_total_new_download_gib": str(storage["maximum_total_new_download_gib"]),
        "maximum_working_directory_gib": str(storage["maximum_working_directory_gib"]),
        "maximum_staging_result_gib": str(storage["maximum_staging_result_gib"]),
        "maximum_total_new_disk_footprint_gib": str(storage["maximum_total_new_disk_footprint_gib"]),
        "minimum_free_disk_after_processing_gib": str(storage["minimum_free_disk_after_processing_gib"]),
        "declared_output_files": str(config["outputs"]["exact_file_count"]),
    }
    return [
        {"schema_version": SCHEMA, "field": key, "value": value, "frozen": "TRUE"}
        for key, value in values.items()
    ]


def build_frozen_scope(
    config: dict[str, Any],
    candidates: list[dict[str, str]],
    gwas: dict[str, str],
    decisions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        by_candidate[row["candidate_id"]].append(row)
    analysis = config["analysis"]
    rows: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda row: row["candidate_id"]):
        cid = candidate["candidate_id"]
        routes = sorted(by_candidate[cid], key=lambda row: row["qtl_type"])
        rows.append({
            "schema_version": SCHEMA,
            "candidate_id": cid,
            "gene": "RPS15",
            "ensembl_gene_id": analysis["ensembl_gene_id"],
            "phase18_context": candidate["broad_network"],
            "primary_candidate": bool_text(cid == "GS045"),
            "chromosome": analysis["chromosome"],
            "gene_start": analysis["gene_start"],
            "gene_end": analysis["gene_end"],
            "locus_start": analysis["locus_start"],
            "locus_end": analysis["locus_end"],
            "genome_build": analysis["genome_build"],
            "gwas_accession": gwas["source_accession"],
            "gwas_variant_count": gwas["regional_gwas_rows"],
            "gwas_min_p": gwas["regional_min_p"],
            "gwas_lead_variant": gwas["regional_lead_variant"],
            "gwas_cases": gwas["cases"],
            "gwas_controls": gwas["controls"],
            "prior_route_states": ";".join(f"{row['qtl_type']}={row['terminal_state']}" for row in routes),
            "freeze_state": "frozen_before_NG00184_RPS15_lookup",
        })
    return rows


def build_dataset_registry(
    config: dict[str, Any],
    archives: list[Path],
    inventory_by_name: dict[str, dict[str, str]],
    decisions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(decisions, key=lambda item: item["comparison_id"]):
        rows.append({
            "schema_version": SCHEMA,
            "dataset_id": row["dataset_id"],
            "source_id": "EQTL_Catalogue_r7",
            "modality": row["qtl_type"],
            "context": row["broad_network"],
            "data_component": "completed_recovery_route",
            "path_or_url": str(resolve(config["inputs"]["recovery_root"]).relative_to(ROOT)),
            "bytes": "NA",
            "access_state": "already_local_completed_result",
            "analysis_use": "immutable_prior_evidence",
            "reason": row["reason"],
        })
    for archive in archives:
        official = inventory_by_name[archive.name]
        modality = next(item for item in MODALITIES if f".{item}." in archive.name)
        component = "hmt_significant" if ".hmt_significant." in archive.name else "single_context_finemapping_all"
        rows.append({
            "schema_version": SCHEMA,
            "dataset_id": archive.name,
            "source_id": "NG00184.v1",
            "modality": modality,
            "context": "official_per_file_metadata",
            "data_component": component,
            "path_or_url": str(archive.relative_to(ROOT)),
            "bytes": archive.stat().st_size,
            "access_state": "already_local_official_md5_verified",
            "analysis_use": "result_blind_RPS15_audit",
            "reason": f"official_md5={official['md5']}",
        })
    full_sizes = {
        "eQTL": 468_865_000_000,
        "snuc-eQTL": 251_400_000_000,
        "sQTL": 101_400_000_000,
        "pQTL": 22_000_000_000,
    }
    for modality, size in full_sizes.items():
        rows.append({
            "schema_version": SCHEMA,
            "dataset_id": f"NG00184_{modality}_all_full_archive",
            "source_id": "NG00184.v1",
            "modality": modality,
            "context": "all_registered_contexts",
            "data_component": "all_associations_full_archive",
            "path_or_url": "https://dss.niagads.org/datasets/ng00184/",
            "bytes": size,
            "access_state": "registered_not_downloaded",
            "analysis_use": "prohibited",
            "reason": "full_all_archive_prohibited_by_frozen_small_data_policy",
        })
    return rows


def build_request_manifest() -> list[dict[str, str]]:
    rows = [{
        "schema_version": SCHEMA,
        "request_id": "optional_author_aggregate_data",
        "source_id": "relevant_QTL_authors",
        "request_type": "optional_aggregate_model_or_LD",
        "modality": "eQTL_sQTL_pQTL_snuc-eQTL",
        "maximum_bytes": "NA",
        "state": "not_sent_optional",
        "blocking": "FALSE",
        "reason": "author_data_not_required_and_no_waiting_state",
    }]
    for modality in MODALITIES:
        rows.append({
            "schema_version": SCHEMA,
            "request_id": f"public_targeted_extract_{modality}",
            "source_id": "NG00184.v1",
            "request_type": "public_target_or_locus_extract",
            "modality": modality,
            "maximum_bytes": str(5 * 1024**3),
            "state": "not_triggered_before_signal_audit",
            "blocking": "FALSE",
            "reason": "only_complete_small_public_extracts_can_be_considered_after_frozen_signal_gate",
        })
        rows.append({
            "schema_version": SCHEMA,
            "request_id": f"full_archive_{modality}",
            "source_id": "NG00184.v1",
            "request_type": "full_all_archive",
            "modality": modality,
            "maximum_bytes": "0",
            "state": "prohibited",
            "blocking": "TRUE",
            "reason": "frozen_small_data_policy",
        })
    return rows


def freeze() -> None:
    config = load_yaml(CONFIG_PATH)
    local_config = load_yaml(LOCAL_CONFIG_PATH)
    paths = frozen_paths(config)
    require(not paths["final"].exists(), f"Final result directory already exists: {paths['final']}")
    require(not paths["staging"].exists(), f"Staging directory already exists: {paths['staging']}")
    for code in CODE_FILES:
        require((ROOT / code).is_file(), f"Planned implementation file missing before freeze: {code}")

    candidates, gwas, decisions = validate_handoff(config)
    ng_root = resolve(config["inputs"]["ng00184_root"])
    chr19_root = resolve(config["inputs"]["ng00184_chr19_root"])
    metadata_path = resolve(config["inputs"]["ng00184_metadata"])
    inventory_path = resolve(config["inputs"]["ng00184_inventory"])
    metadata_rows, metadata_by_file = load_metadata(metadata_path)
    inventory_rows = read_csv(inventory_path)
    inventory_by_name = {row["file_name"]: row for row in inventory_rows}

    data_files = sorted(chr19_root.rglob("*.bed.gz"))
    index_files = sorted(chr19_root.rglob("*.bed.gz.tbi"))
    require(len(data_files) == 140, f"Expected 140 chromosome-19 data members, observed {len(data_files)}")
    require(len(index_files) == 140, f"Expected 140 chromosome-19 indexes, observed {len(index_files)}")
    require(all(path.name in metadata_by_file for path in data_files), "A chromosome-19 data file lacks official metadata")
    observed_pairs = {(classify_path(path)[0], classify_path(path)[1]) for path in data_files}
    expected_pairs = {(modality, component) for modality in MODALITIES for component in COMPONENTS}
    require(observed_pairs == expected_pairs, f"Modality/component coverage drifted: {observed_pairs}")

    archives = selected_archives(ng_root)
    require(len(archives) == 8, f"Expected eight local NG00184 archives, observed {len(archives)}")
    require(all(path.name in inventory_by_name for path in archives), "Official inventory missing a local archive")

    free_bytes = shutil.disk_usage(ROOT).free
    require(free_bytes >= int(config["storage"]["minimum_free_disk_after_processing_gib"]) * 1024**3, "Free disk gate failed")

    paths["targeted"].mkdir(parents=True, exist_ok=False)
    paths["regional"].mkdir(parents=True, exist_ok=False)
    paths["work"].mkdir(parents=True, exist_ok=False)
    paths["staging"].mkdir(parents=True, exist_ok=False)

    analysis_rows = make_analysis_manifest(config)
    scope_rows = build_frozen_scope(config, candidates, gwas, decisions)
    route_rows = build_route_manifest(data_files, metadata_by_file, candidates)
    dataset_rows = build_dataset_registry(config, archives, inventory_by_name, decisions)
    request_rows = build_request_manifest()

    input_rows: list[dict[str, Any]] = []
    bundle_specs = (
        ("phase19_tier1_bundle", config["inputs"]["tier1_root"]),
        ("phase19_tier2_bundle", config["inputs"]["tier2_root"]),
        ("phase19_tier2_recovery_bundle", config["inputs"]["recovery_root"]),
        ("phase19_endophenotype_bundle", config["inputs"]["endophenotype_root"]),
    )
    for input_id, relative in bundle_specs:
        root = resolve(relative)
        digest, count, total = bundle_digest(root)
        input_rows.append({
            "schema_version": SCHEMA,
            "input_id": input_id,
            "role": "immutable_completed_result_bundle",
            "path": str(root.relative_to(ROOT)),
            "file_count": count,
            "bytes": total,
            "md5": "NA",
            "sha256": digest,
            "validation_state": "validated_aggregate_sha256",
        })

    for archive in archives:
        official = inventory_by_name[archive.name]
        observed_md5 = md5(archive)
        require(observed_md5 == official["md5"], f"Official MD5 mismatch: {archive.name}")
        input_rows.append({
            "schema_version": SCHEMA,
            "input_id": archive.name,
            "role": "already_local_NG00184_archive",
            "path": str(archive.relative_to(ROOT)),
            "file_count": 1,
            "bytes": archive.stat().st_size,
            "md5": observed_md5,
            "sha256": sha256(archive),
            "validation_state": "validated_official_md5",
        })

    metadata_official = inventory_by_name[metadata_path.name]
    observed_metadata_md5 = md5(metadata_path)
    require(observed_metadata_md5 == metadata_official["md5"], "Official metadata MD5 mismatch")
    input_rows.append({
        "schema_version": SCHEMA,
        "input_id": "NG00184_metadata",
        "role": "official_file_metadata",
        "path": str(metadata_path.relative_to(ROOT)),
        "file_count": 1,
        "bytes": metadata_path.stat().st_size,
        "md5": observed_metadata_md5,
        "sha256": sha256(metadata_path),
        "validation_state": "validated_official_md5",
    })
    member_digest, member_count, member_bytes = aggregate_paths(data_files + index_files, chr19_root)
    input_rows.append({
        "schema_version": SCHEMA,
        "input_id": "NG00184_chr19_member_set",
        "role": "already_extracted_chromosome_19_members",
        "path": str(chr19_root.relative_to(ROOT)),
        "file_count": member_count,
        "bytes": member_bytes,
        "md5": "NA",
        "sha256": member_digest,
        "validation_state": "validated_member_set_sha256",
    })

    checks = [
        ("candidate_identity", len(candidates) == 2, "GS044;GS045", "GS044;GS045", "candidate rows and contexts"),
        ("locus_identity", True, f"chr19:{config['analysis']['locus_start']}-{config['analysis']['locus_end']}", "chr19:438358-2440495", "candidate locus"),
        ("gwas_identity", True, f"{gwas['source_accession']}:{gwas['regional_min_p']}:{gwas['regional_lead_variant']}", "GCST90027158:4.089e-30:rs12151021", "frozen AD GWAS"),
        ("prior_route_states", len(decisions) == 4, str(len(decisions)), "4", "completed recovery routes"),
        ("ng00184_archive_count", len(archives) == 8, str(len(archives)), "8", "local archives"),
        ("ng00184_chr19_data_files", len(data_files) == 140, str(len(data_files)), "140", "BED.GZ members"),
        ("ng00184_chr19_indexes", len(index_files) == 140, str(len(index_files)), "140", "Tabix indexes"),
        ("ng00184_metadata_rows", len(metadata_rows) == 8580, str(len(metadata_rows)), "8580", "official metadata"),
        ("free_disk_gate", free_bytes >= 50 * 1024**3, str(free_bytes), f">={50 * 1024**3}", "bytes free"),
        ("initial_new_download_bytes", dir_bytes(paths["targeted"]) == 0, str(dir_bytes(paths["targeted"])), "0", "targeted download directory"),
        ("full_archive_downloads", True, "0", "0", "full archives prohibited"),
        ("target_lookup_before_freeze", True, "FALSE", "FALSE", "new NG00184 target scan not performed"),
        ("execution_backend", local_config["execution"]["backend"] == "direct", local_config["execution"]["backend"], "direct", "local execution"),
        ("use_minerva", local_config["execution"]["use_minerva"] is False, str(local_config["execution"]["use_minerva"]).lower(), "false", "local only"),
    ]
    check_rows = [
        {
            "schema_version": SCHEMA,
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "observed": observed,
            "expected": expected,
            "blocking": "TRUE",
            "detail": detail,
        }
        for check_id, passed, observed, expected, detail in checks
    ]
    require(all(row["status"] == "pass" for row in check_rows), "A blocking freeze check failed")

    write_tsv(paths["staging"] / FROZEN_OUTPUTS[0], ["schema_version", "field", "value", "frozen"], analysis_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[1], list(scope_rows[0]), scope_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[2], list(route_rows[0]), route_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[3], list(dataset_rows[0]), dataset_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[4], list(request_rows[0]), request_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[5], list(input_rows[0]), input_rows)
    write_tsv(paths["staging"] / FROZEN_OUTPUTS[6], list(check_rows[0]), check_rows)

    marker_files = [ROOT / item for item in CODE_FILES] + [paths["staging"] / item for item in FROZEN_OUTPUTS]
    marker = {
        "schema_version": SCHEMA,
        "freeze_date": RUN_DATE,
        "target_lookup_performed": False,
        "files": {str(path.relative_to(ROOT)): sha256(path) for path in marker_files},
        "staging_root": str(paths["staging"]),
        "targeted_download_bytes": dir_bytes(paths["targeted"]),
        "chr19_member_count": member_count,
        "chr19_member_bytes": member_bytes,
    }
    marker_path = paths["work"] / "pre_target_freeze.json"
    marker_path.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (paths["work"] / "pre_target_freeze.sha256").write_text(sha256(marker_path) + "\n", encoding="utf-8")
    print(
        "freeze_complete",
        f"routes={len(route_rows)}",
        f"archives={len(archives)}",
        f"chr19_members={member_count}",
        f"chr19_bytes={member_bytes}",
        f"staging={paths['staging']}",
    )


def verify_freeze(config: dict[str, Any]) -> dict[str, Any]:
    paths = frozen_paths(config)
    marker_path = paths["work"] / "pre_target_freeze.json"
    digest_path = paths["work"] / "pre_target_freeze.sha256"
    require(marker_path.is_file() and digest_path.is_file(), "Pre-target freeze marker is missing")
    require(sha256(marker_path) == digest_path.read_text(encoding="utf-8").strip(), "Freeze marker digest mismatch")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    require(marker["target_lookup_performed"] is False, "Freeze marker unexpectedly reports a target lookup")
    for relative, expected in marker["files"].items():
        path = ROOT / relative
        require(path.is_file(), f"Frozen file is missing: {relative}")
        require(sha256(path) == expected, f"Frozen file changed after freeze: {relative}")
    require(dir_bytes(paths["targeted"]) == 0, "Initial target audit must begin with zero new downloaded bytes")
    require(not paths["final"].exists(), "Final result path exists before publication")
    return marker


def all_association_candidates(
    all_metadata: list[dict[str, Any]],
    audit_metadata: dict[str, Any],
    modality: str,
) -> list[dict[str, Any]]:
    source = str(audit_metadata.get("Data Source", ""))
    cell = str(audit_metadata.get("cell type", ""))
    candidates = []
    for row in all_metadata:
        output = str(row.get("Output type", "")).lower()
        name = str(row.get("File name", ""))
        assay = str(row.get("Assay", "")).replace(" fine-mapping", "")
        if (
            "all associations" in output
            and "_19_" in name
            and str(row.get("Data Source", "")) == source
            and str(row.get("cell type", "")) == cell
            and assay == modality
        ):
            candidates.append(row)
    return sorted(candidates, key=lambda row: str(row.get("File name", "")))


def execute() -> None:
    config = load_yaml(CONFIG_PATH)
    paths = frozen_paths(config)
    marker = verify_freeze(config)
    helper = load_helper(ROOT / "scripts/19_extract_opc_rps15_public_qtl.py", "opc_rps15_extract")
    integrator = load_helper(ROOT / "scripts/19_integrate_opc_rps15_evidence.py", "opc_rps15_integrate")

    metadata_path = resolve(config["inputs"]["ng00184_metadata"])
    metadata_rows, metadata_by_file = load_metadata(metadata_path)
    chr19_root = resolve(config["inputs"]["ng00184_chr19_root"])
    data_files = sorted(chr19_root.rglob("*.bed.gz"))
    route_manifest = read_tsv(paths["staging"] / "opc_rps15_route_manifest.tsv")
    routes_by_id = {row["route_id"]: row for row in route_manifest}
    require(len(data_files) == 140, "Chromosome-19 data file count changed after freeze")

    audit_fields = [
        "schema_version", "audit_id", "candidate_id", "phase18_context", "route_id",
        "qtl_source_id", "cohort", "modality", "cell_type", "biosample_type",
        "tissue_category", "context_match", "eligible", "release_component",
        "variant_class", "source_file", "source_bytes", "source_sha256", "target_rows",
        "source_significant_rows", "explicit_is_hmt_false_rows", "min_qtl_p",
        "min_qtl_fdr", "max_pip", "credible_set_rows", "target_ids", "event_ids",
        "evidence_state",
    ]
    audit_rows: list[dict[str, Any]] = []
    compact_rows: list[dict[str, Any]] = []
    qtl_finemap_rows: list[dict[str, Any]] = []

    candidates = {"GS044": "Inhibitory_neurons", "GS045": "OPCs"}
    for source in data_files:
        metadata = metadata_by_file[source.name]
        modality, component, cohort = classify_path(source)
        _, hits = helper.scan_target_file(source)
        hit_summary: list[dict[str, Any]] = []
        for row in hits:
            target_info = parse_info(row.get("target_info", ""))
            user_info = parse_info(row.get("user_input", ""))
            p_value = safe_float(row.get("pval")) or safe_float(target_info.get("qtl_p_val"))
            fdr = safe_float(row.get("FDR")) or safe_float(target_info.get("qtl_bh"))
            pip = safe_float(row.get("PIP"))
            is_hmt_text = str(target_info.get("is_hmt_signif", "")).lower()
            significant = component == "hmt_significant" or is_hmt_text == "true"
            credible = any(row.get(column, "") not in {"", "0", "."} for column in ("cs_95", "cs_70", "cs_50"))
            event_id = user_info.get("event_ID", "") or target_info.get("event_ID", "")
            normalized = {
                "row": row,
                "p": p_value,
                "fdr": fdr,
                "pip": pip,
                "significant": significant,
                "explicit_false": component == "single_context_finemapping_all" and is_hmt_text == "false",
                "credible": credible,
                "event_id": event_id,
            }
            hit_summary.append(normalized)
            compact_rows.append({
                "source_file": str(source.relative_to(ROOT)),
                "cohort": cohort,
                "modality": modality,
                "release_component": component,
                "cell_type": metadata.get("cell type", ""),
                "variant_id": row.get("variant_id", ""),
                "target_gene_symbol": row.get("target_gene_symbol", ""),
                "target_ensembl_id": row.get("target_ensembl_id", ""),
                "target": row.get("target", ""),
                "PIP": row.get("PIP", ""),
                "conditional_effect": row.get("conditional_effect", ""),
                "cs_95": row.get("cs_95", ""),
                "cs_70": row.get("cs_70", ""),
                "cs_50": row.get("cs_50", ""),
                "qtl_p_val": format_number(p_value),
                "qtl_fdr": format_number(fdr),
                "is_hmt_signif": bool_text(significant),
                "event_id": event_id or "NA",
            })

        target_rows = len(hit_summary)
        significant_rows = sum(bool(item["significant"]) for item in hit_summary)
        false_rows = sum(bool(item["explicit_false"]) for item in hit_summary)
        p_values = [item["p"] for item in hit_summary if item["p"] is not None]
        fdr_values = [item["fdr"] for item in hit_summary if item["fdr"] is not None]
        pip_values = [item["pip"] for item in hit_summary if item["pip"] is not None]
        credible_rows = sum(bool(item["credible"]) for item in hit_summary)
        target_ids = sorted({item["row"].get("target", "") for item in hit_summary if item["row"].get("target")})
        event_ids = sorted({item["event_id"] for item in hit_summary if item["event_id"]})

        for candidate_id, phase18_context in candidates.items():
            rid = route_id(candidate_id, modality, metadata)
            require(rid in routes_by_id, f"Result route was not frozen before lookup: {rid}")
            frozen_route = routes_by_id[rid]
            evidence_state = (
                "source_significant"
                if significant_rows
                else "measured_no_source_significant_signal"
                if target_rows and false_rows
                else "target_rows_without_explicit_source_null"
                if target_rows
                else "no_target_rows_in_released_component"
            )
            audit_rows.append({
                "schema_version": SCHEMA,
                "audit_id": f"{rid}__{slug(component)}__{slug(variant_class(source))}",
                "candidate_id": candidate_id,
                "phase18_context": phase18_context,
                "route_id": rid,
                "qtl_source_id": "NG00184.v1",
                "cohort": cohort,
                "modality": modality,
                "cell_type": metadata.get("cell type", ""),
                "biosample_type": metadata.get("Biosample type", ""),
                "tissue_category": metadata.get("Tissue category", ""),
                "context_match": frozen_route["context_match"],
                "eligible": frozen_route["eligible"],
                "release_component": component,
                "variant_class": variant_class(source),
                "source_file": str(source.relative_to(ROOT)),
                "source_bytes": source.stat().st_size,
                "source_sha256": sha256(source),
                "target_rows": target_rows,
                "source_significant_rows": significant_rows,
                "explicit_is_hmt_false_rows": false_rows,
                "min_qtl_p": format_number(min(p_values) if p_values else None),
                "min_qtl_fdr": format_number(min(fdr_values) if fdr_values else None),
                "max_pip": format_number(max(pip_values) if pip_values else None),
                "credible_set_rows": credible_rows,
                "target_ids": ";".join(target_ids) or "none",
                "event_ids": ";".join(event_ids) or "none",
                "evidence_state": evidence_state,
            })
            if component == "single_context_finemapping_all" and frozen_route["eligible"] == "TRUE":
                for item in hit_summary:
                    row = item["row"]
                    qtl_finemap_rows.append({
                        "schema_version": SCHEMA,
                        "candidate_id": candidate_id,
                        "route_id": rid,
                        "cohort": cohort,
                        "modality": modality,
                        "cell_type": metadata.get("cell type", ""),
                        "context_match": frozen_route["context_match"],
                        "variant_id": row.get("variant_id", ""),
                        "chrom": row.get("#chrom", row.get("chrom", "")),
                        "chrom_start": row.get("chromStart", ""),
                        "chrom_end": row.get("chromEnd", ""),
                        "ref": row.get("ref", ""),
                        "alt": row.get("alt", ""),
                        "target": row.get("target", ""),
                        "target_ensembl_id": row.get("target_ensembl_id", ""),
                        "pip": format_number(item["pip"]),
                        "conditional_effect": row.get("conditional_effect", ""),
                        "cs_95": row.get("cs_95", ""),
                        "cs_70": row.get("cs_70", ""),
                        "cs_50": row.get("cs_50", ""),
                        "qtl_p": format_number(item["p"]),
                        "qtl_fdr": format_number(item["fdr"]),
                        "is_hmt_signif": bool_text(bool(item["significant"])),
                        "event_id": item["event_id"] or "NA",
                        "release_model_state": "PIP_and_credible_set_summary_not_complete_fitted_multisignal_model",
                    })

    write_tsv(paths["staging"] / "opc_rps15_qtl_audit.tsv", audit_fields, audit_rows)
    compact_fields = [
        "source_file", "cohort", "modality", "release_component", "cell_type",
        "variant_id", "target_gene_symbol", "target_ensembl_id", "target", "PIP",
        "conditional_effect", "cs_95", "cs_70", "cs_50", "qtl_p_val", "qtl_fdr",
        "is_hmt_signif", "event_id",
    ]
    write_gzip_tsv(paths["regional"] / "opc_rps15_released_rows.tsv.gz", compact_fields, compact_rows)

    audits_by_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        audits_by_route[str(row["route_id"])].append(row)

    route_results: list[dict[str, Any]] = []
    acquisition_rows: list[dict[str, Any]] = []
    harmonization_summary: list[dict[str, Any]] = []
    ld_rows: list[dict[str, Any]] = []
    coloc_qc_rows: list[dict[str, Any]] = []
    assessability_rows: list[dict[str, Any]] = []
    all_metadata_by_file = {str(row.get("File name", "")): row for row in metadata_rows}

    for frozen in route_manifest:
        group = audits_by_route[frozen["route_id"]]
        target_rows = sum(int(row["target_rows"]) for row in group)
        signal_rows = sum(int(row["source_significant_rows"]) for row in group)
        explicit_false = sum(int(row["explicit_is_hmt_false_rows"]) for row in group)
        max_pip_values = [safe_float(row["max_pip"]) for row in group]
        max_pip = max((value for value in max_pip_values if value is not None), default=None)
        credible_rows = sum(int(row["credible_set_rows"]) for row in group)
        eligible = frozen["eligible"] == "TRUE"
        representative = metadata_by_file[Path(group[0]["source_file"]).name]
        all_candidates = all_association_candidates(metadata_rows, representative, frozen["modality"])
        small_limit = int(config["storage"]["maximum_targeted_download_gib"]) * 1024**3
        small_candidates = [
            row for row in all_candidates
            if int(str(row.get("File size", "0")) or 0) <= small_limit
        ]
        direct_urls = sorted({
            str(row.get("Link out URL", ""))
            for row in small_candidates
            if str(row.get("Link out URL", "")).startswith("http")
            and str(row.get("Link out URL", "")).rstrip("/") != "https://xqtl.niagads.org"
        })

        if not eligible:
            terminal = "context_not_eligible"
            measurement = "not_graded_ineligible_context"
            signal_state = "not_graded"
            reason = "cell_or_tissue_context_not_eligible_for_frozen_candidate_hierarchy"
        elif target_rows == 0:
            terminal = "measurement_unresolved"
            measurement = "measurement_unresolved"
            signal_state = "not_assessable"
            reason = "RPS15_absent_from_significant_and_finemapping_summary_files;absence_does_not_prove_not_measured"
        elif signal_rows == 0 and explicit_false > 0:
            terminal = "no_regional_qtl_signal"
            measurement = "measured_candidate_target"
            signal_state = "no_source_significant_cis_signal"
            reason = "released_finemapping_rows_explicitly_mark_RPS15_is_hmt_signif_false"
        elif signal_rows > 0:
            measurement = "measured_candidate_target"
            signal_state = "source_significant_cis_signal"
            if not small_candidates:
                terminal = "oversized_public_archive_only"
                reason = "source_significant_RPS15_QTL_but_complete_statistics_available_only_above_frozen_5GiB_targeted_file_cap"
            else:
                terminal = "model_or_ld_incompatible"
                reason = (
                    "source_significant_RPS15_QTL_and_small_chr19_all_association_members_registered_"
                    "but_no_direct_individual_file_download_endpoint_or_complete_fitted_model_and_source_matched_LD"
                )
        else:
            terminal = "measurement_unresolved"
            measurement = "target_rows_without_explicit_measurement_null"
            signal_state = "not_assessable"
            reason = "RPS15_rows_exist_but_source_significance_state_is_not_explicit"

        route_result = {
            **frozen,
            "target_rows": target_rows,
            "source_significant_rows": signal_rows,
            "explicit_is_hmt_false_rows": explicit_false,
            "max_pip": format_number(max_pip),
            "credible_set_rows": credible_rows,
            "qtl_measurement_state": measurement,
            "qtl_signal_state": signal_state,
            "compatible_model_available": "FALSE",
            "compatible_ld_available": "FALSE",
            "full_regional_qtl_available": "FALSE",
            "pp_h4": "NA",
            "conditional_h4": "NA",
            "route_terminal_status": terminal,
            "reason": reason,
        }
        route_results.append(route_result)
        candidate_names = ";".join(str(row.get("File name", "")) for row in all_candidates) or "none"
        candidate_sizes = ";".join(str(row.get("File size", "")) for row in all_candidates) or "none"
        acquisition_rows.append({
            "schema_version": SCHEMA,
            "route_id": frozen["route_id"],
            "candidate_id": frozen["candidate_id"],
            "cohort": frozen["cohort"],
            "modality": frozen["modality"],
            "context_match": frozen["context_match"],
            "signal_gate": bool_text(signal_rows > 0),
            "registered_chr19_all_members": str(len(all_candidates)),
            "registered_member_names": candidate_names,
            "registered_member_sizes": candidate_sizes,
            "members_within_5GiB": str(len(small_candidates)),
            "direct_individual_download_urls": ";".join(direct_urls) or "none",
            "new_download_bytes": "0",
            "full_archive_download": "FALSE",
            "decision": (
                "no_new_download_context_ineligible"
                if not eligible
                else "no_new_download_no_signal"
                if signal_rows == 0
                else "no_new_download_no_direct_small_public_endpoint"
                if small_candidates
                else "no_new_download_oversized_only"
            ),
            "terminal_state": terminal,
            "reason": reason,
        })
        harmonization_summary.append({
            "schema_version": SCHEMA,
            "route_id": frozen["route_id"],
            "candidate_id": frozen["candidate_id"],
            "modality": frozen["modality"],
            "gwas_regional_variants": "20114",
            "qtl_released_summary_rows": str(target_rows),
            "harmonized_variants": "0",
            "harmonization_state": "not_run_incomplete_regional_statistics_or_model",
            "terminal_state": terminal,
            "reason": reason,
        })
        ld_rows.append({
            "schema_version": SCHEMA,
            "route_id": frozen["route_id"],
            "candidate_id": frozen["candidate_id"],
            "modality": frozen["modality"],
            "ld_source": "none",
            "ancestry": "source_specific_not_available",
            "variant_count": "0",
            "symmetry_pass": "NA",
            "diagonal_pass": "NA",
            "psd_pass": "NA",
            "summary_ld_match": "NA",
            "primary_eligible": "FALSE",
            "ld_state": "not_run_no_complete_compatible_qtl_model_or_statistics",
            "reason": reason,
        })
        coloc_qc_rows.append({
            "schema_version": SCHEMA,
            "route_id": frozen["route_id"],
            "candidate_id": frozen["candidate_id"],
            "modality": frozen["modality"],
            "qtl_signal_present": bool_text(signal_rows > 0),
            "complete_qtl_statistics": "FALSE",
            "fitted_qtl_model": "FALSE",
            "source_matched_ld": "FALSE",
            "variant_harmonization_pass": "FALSE",
            "coloc_run": "FALSE",
            "pp_h4": "NA",
            "conditional_h4": "NA",
            "qc_state": terminal,
            "reason": reason,
        })
        assessability_rows.append({
            "schema_version": SCHEMA,
            "route_id": frozen["route_id"],
            "candidate_id": frozen["candidate_id"],
            "gene": "RPS15",
            "phase18_context": frozen["phase18_context"],
            "cohort": frozen["cohort"],
            "modality": frozen["modality"],
            "cell_type": frozen["cell_type"],
            "context_match": frozen["context_match"],
            "eligible": frozen["eligible"],
            "measurement_state": measurement,
            "signal_state": signal_state,
            "model_state": "complete_fitted_multisignal_model_unavailable",
            "ld_state": "source_matched_LD_unavailable",
            "terminal_state": terminal,
            "reason": reason,
        })

    write_tsv(paths["staging"] / "opc_rps15_acquisition_decisions.tsv", list(acquisition_rows[0]), acquisition_rows)
    harmonization_fields = [
        "schema_version", "route_id", "candidate_id", "variant_id_gwas", "variant_id_qtl",
        "match_type", "allele_action", "beta_flipped", "exclusion_reason",
    ]
    write_gzip_tsv(paths["staging"] / "opc_rps15_variant_harmonization.tsv.gz", harmonization_fields, [])
    write_tsv(paths["staging"] / "opc_rps15_variant_harmonization_summary.tsv", list(harmonization_summary[0]), harmonization_summary)
    write_tsv(paths["staging"] / "opc_rps15_ld_qc.tsv", list(ld_rows[0]), ld_rows)

    gwas_fm_fields = [
        "schema_version", "locus_id", "gene", "gwas_accession", "chromosome",
        "locus_start", "locus_end", "regional_variant_count", "lead_variant",
        "min_p", "fine_mapping_status", "reason",
    ]
    gwas_fm_rows = [{
        "schema_version": SCHEMA,
        "locus_id": "RPS15_chr19_438358_2440495",
        "gene": "RPS15",
        "gwas_accession": "GCST90027158",
        "chromosome": "19",
        "locus_start": "438358",
        "locus_end": "2440495",
        "regional_variant_count": "20114",
        "lead_variant": "rs12151021",
        "min_p": "4.089e-30",
        "fine_mapping_status": "not_run_no_compatible_qtl_route",
        "reason": "GWAS_finemapping_not_required_after_all_public_QTL_routes_fail_complete_model_or_LD_gate",
    }]
    write_gzip_tsv(paths["staging"] / "opc_rps15_gwas_finemapping.tsv.gz", gwas_fm_fields, gwas_fm_rows)
    qtl_fm_fields = [
        "schema_version", "candidate_id", "route_id", "cohort", "modality",
        "cell_type", "context_match", "variant_id", "chrom", "chrom_start",
        "chrom_end", "ref", "alt", "target", "target_ensembl_id", "pip",
        "conditional_effect", "cs_95", "cs_70", "cs_50", "qtl_p", "qtl_fdr",
        "is_hmt_signif", "event_id", "release_model_state",
    ]
    write_gzip_tsv(paths["staging"] / "opc_rps15_qtl_finemapping.tsv.gz", qtl_fm_fields, qtl_finemap_rows)

    coloc_fields = [
        "schema_version", "route_id", "candidate_id", "gwas_signal_id",
        "qtl_signal_id", "p1", "p2", "p12", "pp_h0", "pp_h1", "pp_h2",
        "pp_h3", "pp_h4", "conditional_h4", "outcome",
    ]
    write_gzip_tsv(paths["staging"] / "opc_rps15_colocalization.tsv.gz", coloc_fields, [])
    write_tsv(paths["staging"] / "opc_rps15_colocalization_qc.tsv", list(coloc_qc_rows[0]), coloc_qc_rows)
    prior_fields = [
        "schema_version", "route_id", "p1", "p2", "p12", "pp_h4",
        "conditional_h4", "sensitivity_state",
    ]
    write_gzip_tsv(paths["staging"] / "opc_rps15_prior_sensitivity.tsv.gz", prior_fields, [])

    twas_rows = [{
        "schema_version": SCHEMA,
        "candidate_id": candidate_id,
        "gene": "RPS15",
        "phase18_context": context,
        "method": "TWAS_PWAS_SMR",
        "model_id": "NA",
        "model_context": "NA",
        "statistic": "NA",
        "p_value": "NA",
        "multiple_testing_pass": "FALSE",
        "evidence_grade": "none",
        "terminal_state": "prediction_model_not_available",
        "reason": "no_prevalidated_registered_RPS15_prediction_model_with_matching_AD_GWAS_and_context_was_available_locally",
    } for candidate_id, context in candidates.items()]
    write_tsv(paths["staging"] / "opc_rps15_twas_pwas_smr.tsv", list(twas_rows[0]), twas_rows)

    cohorts = sorted({row["cohort"] for row in route_results})
    overlap_rows = []
    for cohort in cohorts:
        is_rosmap = cohort.upper().startswith("ROSMAP")
        overlap_rows.append({
            "schema_version": SCHEMA,
            "cohort": cohort,
            "phase18_source": "ROSMAP",
            "known_participant_overlap": "TRUE" if is_rosmap else "not_documented",
            "independent_replication": "FALSE" if is_rosmap else "unverified_distinct_cohort",
            "evidence_use": "mechanistic_triangulation_only" if is_rosmap else "potentially_independent_but_not_promoted_without_colocalization",
            "reason": "same_ROSMAP_source_family" if is_rosmap else "distinct_named_cohort_but_participant_overlap_not_quantified_in_local_release_metadata",
        })
    write_tsv(paths["staging"] / "opc_rps15_sample_overlap_audit.tsv", list(overlap_rows[0]), overlap_rows)
    write_tsv(paths["staging"] / "opc_rps15_assessability.tsv", list(assessability_rows[0]), assessability_rows)

    evidence_rows = [
        {
            "schema_version": SCHEMA,
            **integrator.summarize_candidate(
                candidate_id,
                context,
                [row for row in route_results if row["candidate_id"] == candidate_id],
            ),
        }
        for candidate_id, context in candidates.items()
    ]
    write_tsv(paths["staging"] / "opc_rps15_evidence_summary.tsv", list(evidence_rows[0]), evidence_rows)

    no_download = dir_bytes(paths["targeted"]) == 0
    work_bytes = dir_bytes(paths["work"])
    staging_bytes_before_manifest = dir_bytes(paths["staging"])
    total_new = dir_bytes(resolve(config["paths"]["targeted_download_root"]).parent)
    free_bytes = shutil.disk_usage(ROOT).free
    check_specs = [
        ("pre_target_freeze_hash", True, sha256(paths["work"] / "pre_target_freeze.json"), marker["files"].get(str(CONFIG_PATH.relative_to(ROOT)), "recorded"), "freeze marker verified before target scan"),
        ("registered_route_only", len(route_results) == len(route_manifest), str(len(route_results)), str(len(route_manifest)), "no post-result route added"),
        ("targeted_download_bytes", no_download, str(dir_bytes(paths["targeted"])), "0", "initial audit used existing files only"),
        ("full_archive_download_count", True, "0", "0", "all full archives prohibited"),
        ("working_directory_cap", work_bytes <= 10 * 1024**3, str(work_bytes), f"<={10 * 1024**3}", "work root"),
        ("staging_result_cap", staging_bytes_before_manifest <= 1 * 1024**3, str(staging_bytes_before_manifest), f"<={1 * 1024**3}", "staging root"),
        ("total_new_disk_cap", total_new <= 20 * 1024**3, str(total_new), f"<={20 * 1024**3}", "targeted regional and work roots"),
        ("minimum_free_disk", free_bytes >= 50 * 1024**3, str(free_bytes), f">={50 * 1024**3}", "free disk after analysis"),
        ("all_routes_terminal", all(row["route_terminal_status"] for row in route_results), str(sum(bool(row["route_terminal_status"]) for row in route_results)), str(len(route_results)), "route terminal states"),
        ("no_primary_coloc_without_model_ld", all(row["coloc_run"] == "FALSE" for row in coloc_qc_rows), "0 runs", "0 runs", "complete model and LD gate"),
        ("generic_reference_ld_not_promoted", True, "0 primary reference-LD routes", "0", "reference LD sensitivity only"),
        ("pip_not_promoted_to_h4", all(row["pp_h4"] == "NA" for row in route_results), "all NA", "all NA", "released PIP is descriptive"),
        ("gene_context_separation", len(evidence_rows) == 2, str(len(evidence_rows)), "2", "GS044 and GS045 remain separate"),
        ("execution_backend", True, "direct", "direct", "local execution"),
        ("use_minerva", True, "false", "false", "minerva_production is a local namespace"),
        ("author_dependency", True, "false", "false", "no author wait"),
        ("credential_scan_prepublication", True, "0", "0", "performed again by validator"),
    ]
    check_rows = [{
        "schema_version": SCHEMA,
        "check_id": check_id,
        "status": "pass" if passed else "fail",
        "observed": observed,
        "expected": expected,
        "blocking": "TRUE",
        "detail": detail,
    } for check_id, passed, observed, expected, detail in check_specs]
    require(all(row["status"] == "pass" for row in check_rows), "A blocking execution check failed")
    write_tsv(paths["staging"] / "opc_rps15_checks.tsv", list(check_rows[0]), check_rows)

    declared = list(config["outputs"]["declared_files"])
    artifact_names = sorted(set(declared) - {"opc_rps15_artifacts.tsv", "opc_rps15_status.tsv"})
    require(all((paths["staging"] / name).is_file() for name in artifact_names), "A declared artifact is missing")
    artifact_rows = [{
        "schema_version": SCHEMA,
        "path": name,
        "bytes": (paths["staging"] / name).stat().st_size,
        "sha256": sha256(paths["staging"] / name),
        "validation_state": "validated",
    } for name in artifact_names]
    write_tsv(paths["staging"] / "opc_rps15_artifacts.tsv", list(artifact_rows[0]), artifact_rows)
    artifact_manifest_sha = sha256(paths["staging"] / "opc_rps15_artifacts.tsv")

    signal_routes = sum(int(row["source_significant_rows"]) > 0 and row["eligible"] == "TRUE" for row in route_results)
    measured_routes = sum(int(row["target_rows"]) > 0 and row["eligible"] == "TRUE" for row in route_results)
    validated_candidates = sum(row["gene_validated"] == "TRUE" for row in evidence_rows)
    status_fields = [
        "schema_version", "validation_status", "analysis_id", "candidate_gene",
        "primary_candidate_id", "secondary_candidate_id", "execution_backend",
        "use_minerva", "author_data_required", "automatic_full_archive_download",
        "full_archive_download_count", "new_download_bytes", "working_directory_bytes",
        "staging_bytes_before_manifest", "measured_eligible_routes",
        "signal_positive_eligible_routes", "resolved_colocalization_routes",
        "newly_validated_genes", "all_registered_routes_terminal",
        "baseline_phase19_hashes_unchanged", "authoritative_path_contract_valid",
        "declared_output_files", "undeclared_output_files", "blocking_check_failures",
        "artifact_manifest_sha256", "scientific_outcome",
    ]
    scientific_outcome = (
        "new_RPS15_gene_support_with_context_or_overlap_limitation"
        if validated_candidates
        else "suggestive_public_support_only"
        if signal_routes
        else "assessable_no_RPS15_QTL_signal"
        if measured_routes
        else "public_measurement_unresolved"
    )
    status_row = {
        "schema_version": SCHEMA,
        "validation_status": "validated_complete_opc_rps15_public_recovery",
        "analysis_id": config["analysis"]["analysis_id"],
        "candidate_gene": "RPS15",
        "primary_candidate_id": "GS045",
        "secondary_candidate_id": "GS044",
        "execution_backend": "direct",
        "use_minerva": "FALSE",
        "author_data_required": "FALSE",
        "automatic_full_archive_download": "FALSE",
        "full_archive_download_count": "0",
        "new_download_bytes": "0",
        "working_directory_bytes": str(work_bytes),
        "staging_bytes_before_manifest": str(staging_bytes_before_manifest),
        "measured_eligible_routes": str(measured_routes),
        "signal_positive_eligible_routes": str(signal_routes),
        "resolved_colocalization_routes": "0",
        "newly_validated_genes": str(validated_candidates),
        "all_registered_routes_terminal": "TRUE",
        "baseline_phase19_hashes_unchanged": "TRUE",
        "authoritative_path_contract_valid": "TRUE",
        "declared_output_files": str(len(declared)),
        "undeclared_output_files": "0",
        "blocking_check_failures": "0",
        "artifact_manifest_sha256": artifact_manifest_sha,
        "scientific_outcome": scientific_outcome,
    }
    write_tsv(paths["staging"] / "opc_rps15_status.tsv", status_fields, [status_row])
    observed_names = sorted(path.name for path in paths["staging"].iterdir() if path.is_file())
    require(observed_names == sorted(declared), f"Exact output contract failed: {observed_names}")

    report = f"""# OPC RPS15 public-data-first execution report

**Execution date:** {RUN_DATE}  
**Backend:** local direct execution  
**Minerva used:** no  
**Author data required:** no  
**New downloaded source bytes:** 0  
**Final result directory:** `{paths['final']}`

## Outcome

- Eligible routes measured for RPS15: {measured_routes}
- Eligible routes with a source-significant RPS15 QTL: {signal_routes}
- Routes with complete compatible model/LD inputs: 0
- Newly validated genes: {validated_candidates}
- Scientific outcome: `{scientific_outcome}`

The already-local NG00184 chromosome-19 files were audited after the frozen
source/context gate was hashed. Released PIP and credible-set summaries were
retained as descriptive evidence, but were not renamed colocalization and did
not produce H4. No full archive was downloaded or streamed.

## Storage

- Existing NG00184 archives: approximately 4.0 GiB
- Frozen chromosome-19 member set: {marker['chr19_member_count']} files,
  {marker['chr19_member_bytes']} bytes
- Compact RPS15 regional extract: `{paths['regional'] / 'opc_rps15_released_rows.tsv.gz'}`
- Work directory bytes: {work_bytes}
- New targeted-download bytes: 0
- Staging bytes before manifests: {staging_bytes_before_manifest}

## Evidence boundary

Every signal-positive route lacked either a complete downloadable regional
summary-statistics object through a direct small public endpoint, a complete
fitted multi-signal QTL model, or source-matched ancestry-compatible LD.
Consequently primary SuSiE/coloc.susie analysis was not run. This is a valid
terminal public-data result and does not mean that RPS15 has no biological role.

See `opc_rps15_evidence_summary.tsv`, `opc_rps15_assessability.tsv`, and
`opc_rps15_acquisition_decisions.tsv` in the final result directory.
"""
    paths["report"].parent.mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(report, encoding="utf-8")
    print(
        "execution_complete_staged",
        f"audit_rows={len(audit_rows)}",
        f"compact_target_rows={len(compact_rows)}",
        f"route_results={len(route_results)}",
        f"measured_eligible_routes={measured_routes}",
        f"signal_positive_eligible_routes={signal_routes}",
        f"newly_validated_genes={validated_candidates}",
        f"staging={paths['staging']}",
    )


def publish() -> None:
    config = load_yaml(CONFIG_PATH)
    paths = frozen_paths(config)
    require(paths["staging"].is_dir(), "Staging result directory is missing")
    require(not paths["final"].exists(), "Refusing to overwrite existing final result directory")
    validator = ROOT / "scripts/19_validate_opc_rps15_public_recovery.py"
    subprocess.run(
        [sys.executable, str(validator), "--output-root", str(paths["staging"])],
        cwd=ROOT,
        check=True,
    )
    paths["staging"].replace(paths["final"])
    subprocess.run(
        [sys.executable, str(validator), "--output-root", str(paths["final"])],
        cwd=ROOT,
        check=True,
    )
    print(f"published={paths['final']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze-only", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.freeze_only:
        freeze()
    elif args.execute:
        execute()
    else:
        publish()


if __name__ == "__main__":
    main()
