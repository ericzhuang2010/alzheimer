#!/usr/bin/env python3
"""Read-only validator for the published or staged OPC RPS15 result bundle."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import re
from pathlib import Path
from typing import Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/phase19_opc_rps15_public_recovery.yml"
SCHEMA = "phase19_opc_rps15_public_recovery_v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def dir_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root.exists() else 0


def text_lines(path: Path) -> Iterable[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        yield from handle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    output = Path(args.output_root).resolve()
    require(output.is_dir(), f"Output directory is missing: {output}")

    with CONFIG_PATH.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    declared = sorted(config["outputs"]["declared_files"])
    observed = sorted(path.name for path in output.iterdir() if path.is_file())
    require(observed == declared, f"Exact 24-file contract failed: {observed}")
    require(len(observed) == 24, f"Expected 24 files, observed {len(observed)}")
    require(dir_bytes(output) <= 1024**3, "Result bundle exceeds the 1 GiB staging/final cap")

    status = read_tsv(output / "opc_rps15_status.tsv")
    require(len(status) == 1, "Status table must contain exactly one row")
    state = status[0]
    require(state["schema_version"] == SCHEMA, "Status schema drifted")
    require(state["validation_status"] == "validated_complete_opc_rps15_public_recovery", "Unexpected validation status")
    require(state["candidate_gene"] == "RPS15", "Candidate gene drifted")
    require(state["primary_candidate_id"] == "GS045" and state["secondary_candidate_id"] == "GS044", "Candidate IDs drifted")
    require(state["execution_backend"] == "direct" and state["use_minerva"] == "FALSE", "Execution was not local direct")
    require(state["author_data_required"] == "FALSE", "Author data unexpectedly required")
    require(state["automatic_full_archive_download"] == "FALSE", "Full archive download was enabled")
    require(state["full_archive_download_count"] == "0", "A full archive was downloaded")
    require(state["new_download_bytes"] == "0", "Initial public audit downloaded new source bytes")
    require(state["declared_output_files"] == "24", "Declared output count drifted")
    require(state["undeclared_output_files"] == "0", "Status reports undeclared outputs")
    require(state["blocking_check_failures"] == "0", "Status reports blocking failures")
    require(state["all_registered_routes_terminal"] == "TRUE", "A route is not terminal")
    require(state["baseline_phase19_hashes_unchanged"] == "TRUE", "Baseline hash validation failed")
    require(state["authoritative_path_contract_valid"] == "TRUE", "Path contract validation failed")

    artifacts = read_tsv(output / "opc_rps15_artifacts.tsv")
    expected_artifacts = set(declared) - {"opc_rps15_artifacts.tsv", "opc_rps15_status.tsv"}
    require({row["path"] for row in artifacts} == expected_artifacts, "Artifact path set drifted")
    require(len(artifacts) == 22, "Expected 22 hashed artifacts")
    for row in artifacts:
        path = output / row["path"]
        require(path.is_file(), f"Artifact missing: {row['path']}")
        require(path.stat().st_size == int(row["bytes"]), f"Artifact byte mismatch: {row['path']}")
        require(sha256(path) == row["sha256"], f"Artifact hash mismatch: {row['path']}")
        require(row["validation_state"] == "validated", f"Artifact is not validated: {row['path']}")
    require(
        sha256(output / "opc_rps15_artifacts.tsv") == state["artifact_manifest_sha256"],
        "Artifact manifest digest mismatch",
    )

    manifest = read_tsv(output / "opc_rps15_analysis_manifest.tsv")
    values = {row["field"]: row["value"] for row in manifest}
    require(values["target_lookup_at_freeze"] == "false", "Result-blind freeze flag drifted")
    require(values["automatic_full_archive_download"] == "false", "Frozen full-archive gate drifted")
    require(values["declared_output_files"] == "24", "Frozen output count drifted")
    scope = read_tsv(output / "opc_rps15_frozen_scope.tsv")
    require(len(scope) == 2 and {row["candidate_id"] for row in scope} == {"GS044", "GS045"}, "Frozen scope drifted")
    require(all(row["gene"] == "RPS15" and row["ensembl_gene_id"] == "ENSG00000115268" for row in scope), "Target identity drifted")
    require(all(row["locus_start"] == "438358" and row["locus_end"] == "2440495" for row in scope), "Locus drifted")
    require(all(row["gwas_accession"] == "GCST90027158" for row in scope), "GWAS accession drifted")

    routes = read_tsv(output / "opc_rps15_route_manifest.tsv")
    require(routes, "Frozen route manifest is empty")
    require(all(row["source_selection_state"] == "frozen_before_RPS15_lookup" for row in routes), "Route freeze state drifted")
    require({row["candidate_id"] for row in routes} == {"GS044", "GS045"}, "Route candidates drifted")
    audit = read_tsv(output / "opc_rps15_qtl_audit.tsv")
    require(len(audit) == 280, f"Expected 280 candidate-file audit rows, observed {len(audit)}")
    require({row["route_id"] for row in audit}.issubset({row["route_id"] for row in routes}), "Post-result route was introduced")
    require(all(row["qtl_source_id"] == "NG00184.v1" for row in audit), "Unexpected QTL source")

    acquisition = read_tsv(output / "opc_rps15_acquisition_decisions.tsv")
    require(len(acquisition) == len(routes), "Acquisition decisions do not cover every route")
    require(all(row["new_download_bytes"] == "0" for row in acquisition), "A route downloaded new source data")
    require(all(row["full_archive_download"] == "FALSE" for row in acquisition), "A route downloaded a full archive")
    assessability = read_tsv(output / "opc_rps15_assessability.tsv")
    require(len(assessability) == len(routes), "Assessability does not cover every route")
    require(all(row["terminal_state"] for row in assessability), "A route lacks a terminal state")

    qtl_fm = read_tsv(output / "opc_rps15_qtl_finemapping.tsv.gz")
    require(all(row["release_model_state"] == "PIP_and_credible_set_summary_not_complete_fitted_multisignal_model" for row in qtl_fm), "Released fine-mapping evidence was mislabeled")
    coloc = read_tsv(output / "opc_rps15_colocalization.tsv.gz")
    prior = read_tsv(output / "opc_rps15_prior_sensitivity.tsv.gz")
    require(len(coloc) == 0 and len(prior) == 0, "Primary coloc tables must be header-only without compatible model/LD")
    coloc_qc = read_tsv(output / "opc_rps15_colocalization_qc.tsv")
    require(len(coloc_qc) == len(routes), "Colocalization QC does not cover every route")
    require(all(row["coloc_run"] == "FALSE" for row in coloc_qc), "Colocalization ran without compatible inputs")
    require(all(row["pp_h4"] == "NA" for row in coloc_qc), "PIP or overlap was converted to H4")

    evidence = read_tsv(output / "opc_rps15_evidence_summary.tsv")
    require(len(evidence) == 2 and {row["candidate_id"] for row in evidence} == {"GS044", "GS045"}, "Evidence summary drifted")
    require(sum(row["gene_validated"] == "TRUE" for row in evidence) == int(state["newly_validated_genes"]), "Validated-gene count mismatch")
    checks = read_tsv(output / "opc_rps15_checks.tsv")
    source_checks = read_tsv(output / "opc_rps15_source_checks.tsv")
    require(checks and source_checks, "Check tables are empty")
    require(all(row["status"] == "pass" for row in checks + source_checks), "A blocking check is not pass")

    targeted_root = ROOT / config["paths"]["targeted_download_root"]
    work_parent = targeted_root.parent
    require(dir_bytes(targeted_root) == 0, "Targeted download directory is not empty")
    require(dir_bytes(work_parent) <= 20 * 1024**3, "Total new data/work footprint exceeds 20 GiB")
    require(dir_bytes(ROOT / config["paths"]["work_root"]) <= 10 * 1024**3, "Work directory exceeds 10 GiB")
    report = ROOT / config["paths"]["execution_report"]
    require(report.is_file(), "Execution report is missing")

    secret_patterns = [
        re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."),
        re.compile(r"authorization\s*:\s*bearer", re.IGNORECASE),
        re.compile(r"synapse_auth_token", re.IGNORECASE),
        re.compile(r"x-amz-(?:signature|credential)", re.IGNORECASE),
    ]
    for path in output.iterdir():
        if path.suffix not in {".tsv", ".gz"}:
            continue
        for line_number, line in enumerate(text_lines(path), start=1):
            require(
                not any(pattern.search(line) for pattern in secret_patterns),
                f"Credential-like text found in {path.name}:{line_number}",
            )

    print(
        "validated_complete",
        f"files={len(observed)}",
        f"artifacts={len(artifacts)}",
        f"routes={len(routes)}",
        f"audit_rows={len(audit)}",
        f"qtl_finemap_rows={len(qtl_fm)}",
        f"newly_validated_genes={state['newly_validated_genes']}",
        "credential_patterns=0",
    )


if __name__ == "__main__":
    main()
