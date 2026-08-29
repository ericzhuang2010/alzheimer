#!/usr/bin/env python3
"""Build the Phase 20 fine-cell evidence source at the configured query floor.

The historical Phase 18 archive contains complete gene-by-run evidence only
for runs with at least ten effective query genes.  Phase 20 now uses the KDA
execution minimum (three genes), so this program reconstructs the complete
candidate-test universe directly from the validated Phase 12 bundle while
leaving the frozen Phase 18 release unchanged.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
NA_TEXT = "NA"
SCHEMA_ROOT = "phase20_sex_apoe_kda_source_v1"


def fail(message: str) -> None:
    raise RuntimeError(message)


def truth(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def display_value(value: Any) -> Any:
    if value is None:
        return NA_TEXT
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def project_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", newline="")
    return path.open(mode, newline="")


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path, "r") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_tsv(path: Path) -> list[dict[str, str]]:
    return list(iter_tsv(path))


def deterministic_gzip_text(path: Path):
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline="")


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: Sequence[str],
    schema_version: str,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    connection = (
        deterministic_gzip_text(temporary)
        if path.suffix == ".gz"
        else temporary.open("w", newline="")
    )
    count = 0
    with connection as handle:
        names = ["schema_version", *[name for name in fields if name != "schema_version"]]
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            record = {name: display_value(row.get(name)) for name in names}
            record["schema_version"] = schema_version
            writer.writerow(record)
            count += 1
    temporary.replace(path)
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_phase18_module(root: Path):
    path = root / "scripts" / "18_key_driver_selection.py"
    spec = importlib.util.spec_from_file_location("phase18_for_phase20_source", path)
    if spec is None or spec.loader is None:
        fail(f"Could not load Phase 18 implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    observed: Any,
    expected: Any,
    passed: bool,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "severity": "error",
            "observed": observed,
            "expected": expected,
            "passed": passed,
        }
    )


RUN_MANIFEST_FIELDS = """
kda_run_id analysis_tier fine_cell_type broad_network signature_group
signature_direction effective_query_genes effective_background_genes
eligibility_status terminal_status phase18_included phase18_exclusion_reason
phase20_included phase20_exclusion_reason
""".split()

CANDIDATE_TEST_FIELDS = """
kda_run_id fine_cell_type broad_network signature_group signature_direction
current_symbol case_id is_core_mito mitocarta_canonical_symbol query_member
test_status usable_test explicit_family_member effective_query_size
effective_background_size original_layer original_overlap_count
original_neighborhood_size original_non_neighborhood_size
original_signature_size original_fold_enrichment original_log_p original_raw_p
original_run_q self_excluded final_layer final_overlap_count
final_neighborhood_size final_non_neighborhood_size final_signature_size
final_background_size final_fold_enrichment final_log_p final_raw_p final_run_q
other_query_overlap support_overlap_pass support_fold_pass support_run_q_pass
conservative_support
""".split()

CHECK_FIELDS = "check_id severity observed expected passed".split()
ARTIFACT_FIELDS = "artifact_order path rows bytes sha256 hash_status".split()
STATUS_FIELDS = """
analysis_id source_phase minimum_effective_query_genes structural_run_slots
phase12_eligible_runs included_runs historical_phase18_included_runs
included_fine_cell_types included_categories reconstructed_runs
stock_significant_rows candidate_test_rows failed_checks validation_status
""".split()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=root / "config" / "phase20_sex_apoe_kda.yml",
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--minimum-query", type=int)
    return parser.parse_args()


def phase20_exclusion_reason(row: dict[str, str], minimum: int) -> str | None:
    if row["eligibility_status"] != "eligible":
        return row["eligibility_status"]
    if not row["terminal_status"].startswith("completed"):
        return row["terminal_status"]
    if int(row["effective_query_genes"]) < minimum:
        return f"effective_query_below_{minimum}"
    return None


def source_manifest(
    structural_runs: list[dict[str, str]], minimum: int
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in structural_runs:
        phase18_included = (
            row["eligibility_status"] == "eligible"
            and row["terminal_status"].startswith("completed")
            and int(row["effective_query_genes"]) >= 10
        )
        phase20_reason = phase20_exclusion_reason(row, minimum)
        output.append(
            {
                **row,
                "phase18_included": phase18_included,
                "phase18_exclusion_reason": (
                    None
                    if phase18_included
                    else phase20_exclusion_reason(row, 10)
                ),
                "phase20_included": phase20_reason is None,
                "phase20_exclusion_reason": phase20_reason,
            }
        )
    return output


def historical_non_mt_parity(
    historical_path: Path, current_path: Path
) -> tuple[int, int, int, int]:
    """Compare the historical >=10 non-MT rows within their original universe."""
    old_runs: set[str] = set()
    genes_by_network: dict[str, set[str]] = defaultdict(set)
    old_hash: dict[str, Any] = defaultdict(hashlib.sha256)
    new_hash: dict[str, Any] = defaultdict(hashlib.sha256)
    old_count: dict[str, int] = defaultdict(int)
    new_count: dict[str, int] = defaultdict(int)
    with gzip.open(historical_path, "rt", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = [
            name
            for name in (reader.fieldnames or [])
            if name not in {"schema_version", "case_id"}
        ]
        for row in reader:
            if row["case_id"] != "case3_not_core_mito":
                continue
            run_id = row["kda_run_id"]
            old_runs.add(run_id)
            genes_by_network[row["broad_network"]].add(row["current_symbol"])
            old_hash[run_id].update(
                ("\t".join(row[name] for name in fields) + "\n").encode()
            )
            old_count[run_id] += 1
    with gzip.open(current_path, "rt", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        current_fields = [
            name
            for name in (reader.fieldnames or [])
            if name not in {"schema_version", "case_id"}
        ]
        if current_fields != fields:
            fail("Historical and current candidate-test fields differ")
        for row in reader:
            run_id = row["kda_run_id"]
            if (
                run_id not in old_runs
                or row["case_id"] != "non_mt_driver"
                or row["current_symbol"]
                not in genes_by_network[row["broad_network"]]
            ):
                continue
            new_hash[run_id].update(
                ("\t".join(row[name] for name in fields) + "\n").encode()
            )
            new_count[run_id] += 1
    mismatches = sum(
        old_count[run_id] != new_count[run_id]
        or old_hash[run_id].digest() != new_hash[run_id].digest()
        for run_id in old_runs
    )
    return len(old_runs), sum(old_count.values()), sum(new_count.values()), mismatches


def run() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = project_path(root, args.config)
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    source_config = config["source"]
    minimum = int(
        args.minimum_query
        if args.minimum_query is not None
        else source_config["minimum_effective_query_genes"]
    )
    if minimum < 3:
        fail("The KDA execution contract requires at least three effective query genes")
    output_dir = project_path(
        root, args.output_dir or config["paths"]["source_directory"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    phase12_dir = project_path(root, config["paths"]["phase12_directory"])
    phase18_config_path = project_path(root, config["paths"]["phase18_config"])
    with phase18_config_path.open() as handle:
        phase18_config = yaml.safe_load(handle)
    phase18 = load_phase18_module(root)
    checks: list[dict[str, Any]] = []

    required = [
        "kda_run_manifest.tsv",
        "kda_signature_members.tsv.gz",
        "kda_background_members.tsv.gz",
        "kda_results.tsv.gz",
        "kda_checks.tsv",
        "kda_artifacts.tsv",
        "kda_status.tsv",
    ]
    missing = [name for name in required if not (phase12_dir / name).is_file()]
    if missing:
        fail("Missing Phase 12 files: " + ", ".join(missing))
    status = read_tsv(phase12_dir / "kda_status.tsv")
    phase12_complete = (
        len(status) == 1 and status[0].get("validation_status") == "validated_complete"
    )
    add_check(checks, "phase12_status", phase12_complete, True, phase12_complete)
    upstream_checks = read_tsv(phase12_dir / "kda_checks.tsv")
    upstream_failed = sum(not truth(row.get("passed")) for row in upstream_checks)
    add_check(checks, "phase12_failed_checks", upstream_failed, 0, upstream_failed == 0)

    artifact_by_role: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in iter_tsv(phase12_dir / "kda_artifacts.tsv"):
        artifact_by_role[row["artifact_role"]].append(row)
    annotation_path = phase18.one_upstream_artifact(
        root, artifact_by_role, "phase09_annotation"
    )
    annotation, conflicts = phase18.load_annotation(annotation_path)
    add_check(checks, "annotation_conflicts", len(conflicts), 0, not conflicts)

    groups = set(config["scope"]["groups"])
    directions = set(config["scope"]["directions"])
    structural_runs = [
        row
        for row in iter_tsv(phase12_dir / "kda_run_manifest.tsv")
        if row["analysis_tier"] == source_config["analysis_tier"]
        and row["signature_group"] in groups
        and row["signature_direction"] in directions
    ]
    manifest = source_manifest(structural_runs, minimum)
    included_runs = [row for row in manifest if truth(row["phase20_included"])]
    included_ids = {row["kda_run_id"] for row in included_runs}
    phase12_eligible = sum(row["eligibility_status"] == "eligible" for row in manifest)
    historical_included = sum(truth(row["phase18_included"]) for row in manifest)
    add_check(
        checks,
        "structural_run_slots",
        len(manifest),
        int(source_config["expected_structural_slots"]),
        len(manifest) == int(source_config["expected_structural_slots"]),
    )
    add_check(
        checks,
        "phase12_eligible_runs",
        phase12_eligible,
        int(source_config["expected_phase12_eligible"]),
        phase12_eligible == int(source_config["expected_phase12_eligible"]),
    )
    add_check(
        checks,
        "phase20_included_runs",
        len(included_runs),
        int(source_config["expected_included_runs"]),
        len(included_runs) == int(source_config["expected_included_runs"]),
    )
    add_check(
        checks,
        "minimum_included_query_size",
        min(int(row["effective_query_genes"]) for row in included_runs),
        minimum,
        min(int(row["effective_query_genes"]) for row in included_runs) == minimum,
    )
    add_check(
        checks,
        "historical_phase18_included_runs",
        historical_included,
        161,
        historical_included == 161,
    )

    signatures: dict[str, set[str]] = defaultdict(set)
    for row in iter_tsv(phase12_dir / "kda_signature_members.tsv.gz"):
        if row["kda_run_id"] in included_ids and truth(row.get("effective_member")):
            signatures[row["kda_run_id"]].add(sys.intern(row["gene"]))
    backgrounds: dict[str, set[str]] = defaultdict(set)
    for row in iter_tsv(phase12_dir / "kda_background_members.tsv.gz"):
        if row["kda_run_id"] in included_ids:
            backgrounds[row["kda_run_id"]].add(sys.intern(row["gene"]))
    membership_errors = 0
    for row in included_runs:
        run_id = row["kda_run_id"]
        membership_errors += int(
            len(signatures[run_id]) != int(row["effective_query_genes"])
            or len(backgrounds[run_id]) != int(row["effective_background_genes"])
            or not signatures[run_id].issubset(backgrounds[run_id])
        )
    add_check(checks, "query_background_membership_errors", membership_errors, 0, membership_errors == 0)

    networks = list(config["scope"]["broad_networks"])
    full_edges = {
        network: phase18.load_network(
            phase18.one_upstream_artifact(
                root, artifact_by_role, f"network_{network}"
            )
        )
        for network in networks
    }
    unexpected_networks = sorted(
        {row["broad_network"] for row in included_runs} - set(networks)
    )
    add_check(checks, "included_network_scope", "|".join(unexpected_networks), "none", not unexpected_networks)

    published_rows = [
        row
        for row in iter_tsv(phase12_dir / "kda_results.tsv.gz")
        if row["kda_run_id"] in included_ids
    ]
    published_by_run: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    duplicate_published = 0
    for row in published_rows:
        run_id = row["kda_run_id"]
        gene = row["key_driver"]
        duplicate_published += int(gene in published_by_run[run_id])
        published_by_run[run_id][gene] = row
    add_check(checks, "duplicate_stock_return_keys", duplicate_published, 0, duplicate_published == 0)

    explicit_by_run: dict[str, dict[str, dict[str, Any]]] = {}
    for index, row in enumerate(included_runs, start=1):
        run_id = row["kda_run_id"]
        explicit, _ = phase18.reconstruct_run(
            row,
            signatures[run_id],
            backgrounds[run_id],
            full_edges[row["broad_network"]],
            annotation,
        )
        phase18.validate_published_returns(
            run_id, published_by_run.get(run_id, {}), explicit
        )
        explicit_by_run[run_id] = explicit
        if index % 25 == 0 or index == len(included_runs):
            print(f"reconstructed_runs={index}/{len(included_runs)}", flush=True)
    add_check(checks, "reconstructed_runs", len(explicit_by_run), len(included_runs), len(explicit_by_run) == len(included_runs))

    runs_by_network: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in included_runs:
        runs_by_network[row["broad_network"]].append(row)
    network_genes = {
        network: sorted(
            set().union(
                *(backgrounds[row["kda_run_id"]] for row in runs)
            )
        )
        for network, runs in runs_by_network.items()
    }
    expected_candidate_rows = sum(
        len(network_genes[row["broad_network"]]) for row in included_runs
    )

    candidate_path = output_dir / source_config["candidate_tests"]
    candidate_rows = write_tsv(
        candidate_path,
        phase18.candidate_test_rows(
            included_runs,
            network_genes,
            signatures,
            backgrounds,
            explicit_by_run,
            annotation,
        ),
        CANDIDATE_TEST_FIELDS,
        f"{SCHEMA_ROOT}_candidate_tests_v1",
    )
    add_check(checks, "candidate_test_rows", candidate_rows, expected_candidate_rows, candidate_rows == expected_candidate_rows)
    historical_path = (
        project_path(root, config["paths"]["historical_phase18_archive"])
        / "key_driver_candidate_tests.tsv.gz"
    )
    historical_runs, historical_rows, matched_rows, parity_mismatches = (
        historical_non_mt_parity(historical_path, candidate_path)
    )
    add_check(checks, "historical_phase18_parity_runs", historical_runs, 161, historical_runs == 161)
    add_check(checks, "historical_phase18_parity_rows", matched_rows, historical_rows, matched_rows == historical_rows)
    add_check(checks, "historical_phase18_parity_mismatches", parity_mismatches, 0, parity_mismatches == 0)

    manifest_path = output_dir / source_config["run_manifest"]
    manifest_rows = write_tsv(
        manifest_path,
        manifest,
        RUN_MANIFEST_FIELDS,
        f"{SCHEMA_ROOT}_run_manifest_v1",
    )
    checks_path = output_dir / source_config["source_checks"]
    failed_checks = sum(not row["passed"] for row in checks)
    write_tsv(
        checks_path,
        checks,
        CHECK_FIELDS,
        f"{SCHEMA_ROOT}_checks_v1",
    )

    artifact_rows = []
    for order, (path, rows) in enumerate(
        ((candidate_path, candidate_rows), (manifest_path, manifest_rows), (checks_path, len(checks))),
        start=1,
    ):
        artifact_rows.append(
            {
                "artifact_order": order,
                "path": path.name,
                "rows": rows,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "hash_status": "recorded",
            }
        )
    write_tsv(
        output_dir / source_config["source_artifacts"],
        artifact_rows,
        ARTIFACT_FIELDS,
        f"{SCHEMA_ROOT}_artifacts_v1",
    )
    included_categories = {
        (row["signature_group"], row["broad_network"]) for row in included_runs
    }
    status_row = {
        "analysis_id": config["analysis"]["analysis_id"],
        "source_phase": "validated_phase12_reconstruction",
        "minimum_effective_query_genes": minimum,
        "structural_run_slots": len(manifest),
        "phase12_eligible_runs": phase12_eligible,
        "included_runs": len(included_runs),
        "historical_phase18_included_runs": historical_included,
        "included_fine_cell_types": len({row["fine_cell_type"] for row in included_runs}),
        "included_categories": len(included_categories),
        "reconstructed_runs": len(explicit_by_run),
        "stock_significant_rows": len(published_rows),
        "candidate_test_rows": candidate_rows,
        "failed_checks": failed_checks,
        "validation_status": "validated_complete" if failed_checks == 0 else "validation_failed",
    }
    write_tsv(
        output_dir / source_config["source_status"],
        [status_row],
        STATUS_FIELDS,
        f"{SCHEMA_ROOT}_status_v1",
    )
    print(f"wrote={output_dir}")
    print(f"minimum_effective_query_genes={minimum}")
    print(f"included_runs={len(included_runs)}")
    print(f"candidate_test_rows={candidate_rows}")
    print(f"validation_status={status_row['validation_status']}")
    return 0 if failed_checks == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
