#!/usr/bin/env python3
"""Validate a published Phase 19 endophenotype extension without modifying it."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension"
RUNNER = ROOT / "scripts/19_run_endophenotype_extension.py"


def load_declared_files() -> list[str]:
    spec = importlib.util.spec_from_file_location("phase19_endophenotype_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return list(module.DECLARED_FILES)


def read_tsv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_lines(path: Path) -> Iterator[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        yield from handle


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output_root).resolve()
    require(output.is_dir(), f"Published output does not exist: {output}")

    declared = sorted(load_declared_files())
    observed = sorted(path.name for path in output.iterdir() if path.is_file())
    require(observed == declared, f"Exact 36-file contract failed: {observed}")
    require(len(observed) == 36, f"Expected 36 files, observed {len(observed)}")

    status = read_tsv(output / "endophenotype_status.tsv")
    checks = read_tsv(output / "endophenotype_checks.tsv")
    artifacts = read_tsv(output / "endophenotype_artifacts.tsv")
    require(len(status) == 1, "Status table must contain exactly one row")
    require(status[0]["validation_status"] == "validated_complete_endophenotype_gwas_qtl_extension", "Unexpected validation status")
    require(status[0]["execution_backend"] == "direct", "Execution backend must be direct")
    require(status[0]["declared_output_files"] == "36", "Status file-count declaration drifted")
    require(status[0]["blocking_check_failures"] == "0", "Published status reports a blocking failure")
    require(all(row["status"] == "pass" for row in checks), "A published blocking check is not pass")
    require(
        sha256(output / "endophenotype_artifacts.tsv") == status[0]["artifact_manifest_sha256"],
        "Artifact-manifest digest does not match status",
    )

    expected_artifact_names = set(declared) - {"endophenotype_artifacts.tsv", "endophenotype_status.tsv"}
    require({row["path"] for row in artifacts} == expected_artifact_names, "Artifact manifest path set drifted")
    for row in artifacts:
        path = output / row["path"]
        require(path.stat().st_size == int(row["bytes"]), f"Byte count mismatch: {row['path']}")
        require(sha256(path) == row["sha256"], f"SHA-256 mismatch: {row['path']}")
        require(row["validation_state"] == "validated", f"Artifact is not validated: {row['path']}")

    candidates = read_tsv(output / "endophenotype_candidate_manifest.tsv")
    biomarkers = read_tsv(output / "endophenotype_biomarker_manifest.tsv")
    units = read_tsv(output / "endophenotype_screening_units.tsv")
    regional = read_tsv(output / "endophenotype_regional_gwas_summary.tsv")
    gates = read_tsv(output / "endophenotype_gate_decisions.tsv")
    matrix = read_tsv(output / "endophenotype_context_biomarker_matrix.tsv")
    routes = read_tsv(output / "endophenotype_route_manifest.tsv")
    conditional = read_tsv(output / "endophenotype_magma_conditional.tsv")
    inventory = read_tsv(output / "endophenotype_input_inventory.tsv")

    require(len(candidates) == 47 and len({row["gene"] for row in candidates}) == 25, "Candidate freeze drifted")
    require(len(biomarkers) == 3, "Biomarker count drifted")
    require(len(units) == 75 and len(regional) == 75, "Gene-biomarker row count drifted")
    require(len(gates) == 57, "Nuclear gate count drifted")
    require(len(matrix) == 141, "Context-biomarker matrix count drifted")
    require(all(row["route_terminal_status"] for row in routes), "A QTL route lacks a terminal state")
    require(len(conditional) == 3 and all(row["sensitivity_status"] == "tested_window_10kb" for row in conditional), "MAGMA sensitivity audit drifted")
    require(status[0]["newly_biomarker_supported_unique_genes"] == "0", "Unexpected newly supported gene count")

    atlas_routes = [row for row in routes if row["qtl_source_id"] == "NG00184.v1"]
    atlas_inputs = [row for row in inventory if row["source_id"] == "NG00184.v1"]
    require(len(atlas_routes) == 12, "Expected 12 NG00184 route results")
    require(len(atlas_inputs) == 9, "Expected eight NG00184 archives plus metadata")
    require(all(row["validation_state"].startswith("validated_official_md5_") for row in atlas_inputs), "Atlas MD5 validation missing")

    secret_patterns = [
        re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."),
        re.compile(r"authorization\s*:\s*bearer", re.IGNORECASE),
        re.compile(r"synapse_auth_token", re.IGNORECASE),
        re.compile(r"x-amz-(?:signature|credential)", re.IGNORECASE),
    ]
    text_paths = [path for path in output.iterdir() if path.suffix in {".tsv", ".gz"}]
    for path in text_paths:
        for line_number, line in enumerate(text_lines(path), start=1):
            require(
                not any(pattern.search(line) for pattern in secret_patterns),
                f"Credential-like text found in {path.name}:{line_number}",
            )

    print(
        "validated_complete:",
        f"files={len(observed)}",
        f"artifacts={len(artifacts)}",
        f"gates={len(gates)}",
        f"routes={len(routes)}",
        f"matrix_rows={len(matrix)}",
        "credential_patterns=0",
    )


if __name__ == "__main__":
    main()
