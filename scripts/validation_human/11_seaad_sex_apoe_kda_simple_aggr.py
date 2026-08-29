#!/usr/bin/env python3
"""Build the returned-only, non-core-MT SEA-AD KDA aggregation.

The upstream SEA-AD KDA calls are already complete.  This script consumes the
validated significant rows returned by ``call_key_drivers()`` for the relaxed
SEA-AD tier and applies the requested exploratory rule:

* retain only returned non-core-MitoCarta key drivers;
* pass a singleton's within-call BH q value through unchanged;
* equal-weight ACAT-combine the returned within-call q values when a gene is
  returned by two or more calls in the aggregation scope;
* do not add implicit rows or apply another across-gene BH correction.

Both a global gene view and a sex/APOE-by-broad-network gene view are written.
The derived score is post-selected and is not a formally FDR-controlled q.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import math
import os
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
FALSE_VALUES = {"FALSE", "F", "0", "NO"}
NA_TEXT = "NA"
ACTIVE_STATES = {"eligible_small_query", "eligible_phase18_sized"}
GROUPS = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
GROUP_LABELS = {
    "F_e2": {"sex": "Female", "apoe_group": "e2"},
    "F_e33": {"sex": "Female", "apoe_group": "e33"},
    "F_e4": {"sex": "Female", "apoe_group": "e4"},
    "M_e2": {"sex": "Male", "apoe_group": "e2"},
    "M_e33": {"sex": "Male", "apoe_group": "e33"},
    "M_e4": {"sex": "Male", "apoe_group": "e4"},
}
SCHEMA_ROOT = "seaad_simple_returned_only_non_core_mt_acat_v1"
ANALYSIS_ID = "seaad_simple_returned_only_non_core_mt_acat_v1"


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).strip().upper() in TRUE_VALUES


def as_optional_bool(value: Any) -> bool | None:
    if value in (None, "", NA_TEXT):
        return None
    normalized = str(value).strip().upper()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    fail(f"Invalid logical value: {value}")


def as_float(value: Any) -> float | None:
    if value in (None, "", NA_TEXT):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def display_value(value: Any) -> Any:
    if value is None:
        return NA_TEXT
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return repr(value) if math.isfinite(value) else NA_TEXT
    return value


def project_path(root: Path, value: str | Path, *, must_exist: bool = True) -> Path:
    raw = Path(value)
    if ".." in raw.parts:
        fail(f"Repository path may not contain '..': {raw}")
    candidate = raw if raw.is_absolute() else root / raw
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        fail(f"Path escapes the project root: {resolved}")
        raise AssertionError from exc
    return resolved


def open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", newline="")
    return path.open(mode, newline="")


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    if not path.is_file():
        fail(f"Required file does not exist: {path}")
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
        names = ["schema_version", *[field for field in fields if field != "schema_version"]]
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = {field: display_value(row.get(field)) for field in names}
            output["schema_version"] = schema_version
            writer.writerow(output)
            count += 1
    temporary.replace(path)
    return count


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def load_phase18_module(path: Path):
    spec = importlib.util.spec_from_file_location("phase18_seaad_simple_authority", path)
    if spec is None or spec.loader is None:
        fail(f"Could not load the frozen Phase 18 module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    observed: Any,
    expected: Any,
    passed: bool,
    message: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "observed": observed,
            "expected": expected,
            "passed": passed,
            "severity": "error",
            "message": message,
        }
    )


def require_validated_bundle(
    root: Path,
    directory: Path,
    checks: list[dict[str, Any]],
    prefix: str,
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    status_path = directory / "status.tsv"
    artifacts_path = directory / "artifacts.tsv"
    status_rows = read_tsv(status_path)
    if len(status_rows) != 1:
        fail(f"Expected one status row in {status_path}")
    status = status_rows[0]
    add_check(
        checks,
        f"{prefix}_validated_status",
        status.get("validation_status"),
        "validated_complete",
        status.get("validation_status") == "validated_complete",
        f"The upstream {prefix} bundle must be validated_complete",
    )
    artifacts = read_tsv(artifacts_path)
    artifact_lookup = {row["artifact"]: row for row in artifacts}
    # Compact checkouts may omit registered reconstruction tables that this
    # returned-only derivative does not consume. Required inputs are verified
    # individually below against their registered bytes and SHA-256 values.
    add_check(
        checks,
        f"{prefix}_artifact_registry_keys",
        len(artifact_lookup),
        len(artifacts),
        len(artifact_lookup) == len(artifacts),
        f"The upstream {prefix} artifact registry must have unique names",
    )
    return status, artifact_lookup


def summarize_unit(
    rows: Sequence[dict[str, Any]],
    *,
    scope: str,
    phase18: Any,
    query_rule_id: str,
    result_tier_id: str,
    signature_group: str = "ALL",
    broad_network: str = "ALL",
) -> dict[str, Any]:
    if not rows:
        fail("Cannot summarize an empty returned-row unit")
    ordered = sorted(rows, key=lambda row: str(row["kda_run_id"]))
    genes = {str(row["current_symbol"]) for row in ordered}
    if len(genes) != 1:
        fail(f"Aggregate unit contains multiple genes: {sorted(genes)}")
    gene = next(iter(genes))
    if any(bool(row["is_core_mito"]) for row in ordered):
        fail(f"Core-MitoCarta gene reached the non-MT aggregation: {gene}")
    q_values = [float(row["returned_within_call_q"]) for row in ordered]
    run_ids = [str(row["kda_run_id"]) for row in ordered]
    if len(set(run_ids)) != len(run_ids):
        fail(f"Duplicate returned run for {scope}/{signature_group}/{broad_network}/{gene}")
    if len(q_values) == 1:
        final_value = q_values[0]
        acat_value = None
        method = "singleton_within_call_q_passthrough"
    else:
        acat_value = phase18.acat_combine(q_values, missing_action="omit")
        if acat_value is None:
            fail(f"ACAT unexpectedly returned missing for {gene}")
        final_value = float(acat_value)
        method = "acat_of_returned_within_call_q_values"
    ann = ordered[0]
    if signature_group == "ALL":
        sex = "ALL"
        apoe_group = "ALL"
    else:
        sex = GROUP_LABELS[signature_group]["sex"]
        apoe_group = GROUP_LABELS[signature_group]["apoe_group"]
    return {
        "cohort": "SEAAD",
        "analysis_scope": scope,
        "query_rule_id": query_rule_id,
        "result_tier_id": result_tier_id,
        "signature_group": signature_group,
        "sex": sex,
        "apoe_group": apoe_group,
        "broad_network": broad_network,
        "current_symbol": gene,
        "case_id": "non_mt_driver",
        "is_core_mito": False,
        "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
        "mito_tier": ann["mito_tier"],
        "genome_origin": ann["genome_origin"],
        "returned_call_count": len(ordered),
        "returned_fine_cell_type_count": len({row["fine_cell_type"] for row in ordered}),
        "returned_fine_cell_types": "|".join(sorted({row["fine_cell_type"] for row in ordered})),
        "returned_signature_group_count": len({row["signature_group"] for row in ordered}),
        "returned_signature_groups": "|".join(sorted({row["signature_group"] for row in ordered})),
        "returned_broad_network_count": len({row["broad_network"] for row in ordered}),
        "returned_broad_networks": "|".join(sorted({row["broad_network"] for row in ordered})),
        "returned_direction_count": len({row["signature_direction"] for row in ordered}),
        "returned_directions": "|".join(sorted({row["signature_direction"] for row in ordered})),
        "minimum_returned_within_call_q": min(q_values),
        "median_returned_within_call_q": statistics.median(q_values),
        "maximum_returned_within_call_q": max(q_values),
        "acat_of_returned_within_call_q": acat_value,
        "returned_run_q_acat_score": final_value,
        "requested_final_q": final_value,
        "final_value_method": method,
        "input_statistic": "stock_within_call_bh_q",
        "inferential_status": "exploratory_postselection",
        "multiple_testing_after_acat": "none",
        "additional_across_gene_bh_applied": False,
        "formal_fdr_controlled_q": False,
        "returned_run_ids": "|".join(run_ids),
        "rank": None,
    }


def assign_ranks(rows: list[dict[str, Any]], key_fields: Sequence[str]) -> None:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row[field]) for field in key_fields)
        groups[key].append(row)
    for members in groups.values():
        members.sort(
            key=lambda row: (
                float(row["returned_run_q_acat_score"]),
                str(row["current_symbol"]),
            )
        )
        for rank, row in enumerate(members, start=1):
            row["rank"] = rank


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="scripts/validation_human/seaad_phase18_validation_config.yml",
    )
    parser.add_argument(
        "--phase-root",
        default="results/validation_human/10_seaad_kda_rediscovery",
    )
    parser.add_argument(
        "--output",
        default="results/validation_human/11_sex_apoe_kda_simple_aggr",
    )
    return parser.parse_args()


AGGREGATE_FIELDS = """
cohort analysis_scope query_rule_id result_tier_id signature_group sex
apoe_group broad_network current_symbol case_id is_core_mito
mitocarta_canonical_symbol mito_tier genome_origin returned_call_count
returned_fine_cell_type_count returned_fine_cell_types
returned_signature_group_count returned_signature_groups
returned_broad_network_count returned_broad_networks returned_direction_count
returned_directions minimum_returned_within_call_q median_returned_within_call_q
maximum_returned_within_call_q acat_of_returned_within_call_q
returned_run_q_acat_score requested_final_q final_value_method input_statistic
inferential_status multiple_testing_after_acat additional_across_gene_bh_applied
formal_fdr_controlled_q returned_run_ids rank
""".split()

DETAIL_FIELDS = """
cohort kda_run_id query_rule_id result_tier_id fine_cell_type broad_network
signature_group sex apoe_group signature_direction current_symbol case_id
is_core_mito mitocarta_canonical_symbol mito_tier genome_origin best_layer
overlap_count neighborhood_size non_neighborhood_size signature_size
fold_enrichment returned_log_p returned_raw_p returned_within_call_q
is_signature is_root_node global_key_driver overlap_items
global_returned_call_count global_returned_run_q_acat_score
global_requested_final_q global_rank category_returned_call_count
category_returned_run_q_acat_score category_requested_final_q category_rank
""".split()

CATEGORY_FIELDS = """
signature_group sex apoe_group broad_network aggregation_status
included_call_count completed_significant_call_count completed_empty_call_count
all_class_stock_returned_row_count mt_excluded_returned_row_count
non_mt_retained_returned_row_count non_mt_returned_gene_count
non_mt_singleton_gene_unit_count non_mt_recurrent_gene_unit_count
minimum_requested_final_q
""".split()

CHECK_FIELDS = "check_id observed expected passed severity message".split()
STATUS_FIELDS = """
analysis_id cohort execution_status interpretation_status source_kda_execution
git_revision query_rule_id result_tier_id included_run_count
completed_significant_call_count completed_empty_call_count
all_class_stock_returned_row_count mt_excluded_returned_row_count
non_mt_retained_returned_row_count non_mt_unique_returned_gene_count
global_singleton_gene_count global_recurrent_gene_count
global_aggregate_row_count category_gene_unit_count
category_singleton_unit_count category_recurrent_unit_count
structural_category_count active_category_count return_bearing_category_count
failed_check_count output_directory
""".split()

ARTIFACT_FIELDS = "role path bytes sha256".split()


def run() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    config_path = project_path(root, args.config)
    phase_root = project_path(root, args.phase_root)
    output_dir = project_path(root, args.output, must_exist=False)
    input_dir = phase_root / "10a_inputs"
    kda_dir = phase_root / "10b_kda"
    manifest_path = input_dir / "seaad_kda_run_manifest.tsv"
    stock_path = kda_dir / "seaad_kda_significant_returns.tsv"
    run_qc_path = kda_dir / "run_qc.tsv"

    with config_path.open("rt", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    cfg = config["vh10"]
    analysis = cfg["analysis"]
    query_rule_id = str(analysis["query_rule_id"])
    result_tier_id = str(analysis["result_tier_id"])
    networks = list(cfg["network_order"])

    checks: list[dict[str, Any]] = []
    input_status, input_artifacts = require_validated_bundle(
        root, input_dir, checks, "vh10a"
    )
    kda_status, kda_artifacts = require_validated_bundle(
        root, kda_dir, checks, "vh10b"
    )
    config_sha = sha256_file(config_path)
    config_matches = (
        input_status.get("config_sha256") == config_sha
        and kda_status.get("config_sha256") == config_sha
    )
    add_check(
        checks,
        "frozen_config_identity",
        f"{input_status.get('config_sha256')}|{kda_status.get('config_sha256')}",
        config_sha,
        config_matches,
        "Both upstream stages must record the exact current SEA-AD config",
    )
    for path, lookup, label in (
        (manifest_path, input_artifacts, "manifest"),
        (stock_path, kda_artifacts, "significant_returns"),
        (run_qc_path, kda_artifacts, "run_qc"),
    ):
        row = lookup.get(path.name)
        matches = (
            row is not None
            and int(row["bytes"]) == path.stat().st_size
            and row["digest_value"] == sha256_file(path)
        )
        add_check(
            checks,
            f"registered_{label}_identity",
            sha256_file(path),
            row["digest_value"] if row is not None else "registered artifact",
            matches,
            f"The {label} input must match its validated upstream registration",
        )

    phase18_item = cfg["input_authority"]["phase18_code"]
    phase18_path = project_path(root, phase18_item["path"])
    phase18_match = sha256_file(phase18_path) == phase18_item["sha256"]
    add_check(
        checks,
        "phase18_acat_code_identity",
        sha256_file(phase18_path),
        phase18_item["sha256"],
        phase18_match,
        "Use the frozen repository ACAT implementation",
    )
    phase18 = load_phase18_module(phase18_path)

    annotation_item = cfg["input_authority"]["phase18_annotation"]
    annotation_path = project_path(root, annotation_item["path"])
    annotation_match = sha256_file(annotation_path) == annotation_item["sha256"]
    add_check(
        checks,
        "phase18_annotation_identity",
        sha256_file(annotation_path),
        annotation_item["sha256"],
        annotation_match,
        "Use the frozen Phase 18 driver-class annotation",
    )
    annotations, annotation_conflicts = phase18.load_annotation(annotation_path)
    add_check(
        checks,
        "annotation_conflicts",
        len(annotation_conflicts),
        0,
        not annotation_conflicts,
        "A gene must have one unambiguous core-MitoCarta classification",
    )

    manifest_rows = read_tsv(manifest_path)
    active_rows = [row for row in manifest_rows if row["terminal_status"] in ACTIVE_STATES]
    active_lookup = {row["kda_run_id"]: row for row in active_rows}
    expected_active = int(input_status["active_kda_calls"])
    add_check(
        checks,
        "active_run_count",
        len(active_rows),
        expected_active,
        len(active_rows) == expected_active == 42 and len(active_lookup) == len(active_rows),
        "Use all 42 validated relaxed-tier SEA-AD KDA calls exactly once",
    )
    contract_count = sum(
        row["query_rule_id"] == query_rule_id
        and row["result_tier_id"] == result_tier_id
        and row["signature_group"] in GROUPS
        and row["broad_network"] in networks
        and row["signature_direction"] in analysis["directions"]
        and bool(row["kda_run_id"])
        for row in active_rows
    )
    add_check(
        checks,
        "active_run_contract",
        contract_count,
        len(active_rows),
        contract_count == len(active_rows),
        "Every active call must belong to the frozen exploratory tier and scope",
    )
    structural_groups = sorted({row["signature_group"] for row in manifest_rows})
    structural_networks = sorted({row["broad_network"] for row in manifest_rows})
    add_check(
        checks,
        "structural_scope",
        f"{len(structural_groups)} groups x {len(structural_networks)} networks",
        "6 groups x 7 networks",
        structural_groups == sorted(GROUPS) and structural_networks == sorted(networks),
        "Preserve the complete sex/APOE-by-broad-network structural grid",
    )

    run_qc_rows = read_tsv(run_qc_path)
    run_qc_lookup = {row["kda_run_id"]: row for row in run_qc_rows}
    completed_significant = sum(
        row["terminal_status"] == "completed_significant" for row in run_qc_rows
    )
    completed_empty = sum(
        row["terminal_status"] == "completed_no_significant" for row in run_qc_rows
    )
    run_qc_complete = (
        set(run_qc_lookup) == set(active_lookup)
        and completed_significant == int(kda_status["completed_significant_calls"])
        and completed_empty == int(kda_status["completed_no_significant_calls"])
        and completed_significant + completed_empty == len(active_rows)
    )
    add_check(
        checks,
        "run_qc_completion",
        f"{completed_significant} significant|{completed_empty} empty",
        "27 significant|15 empty",
        run_qc_complete and completed_significant == 27 and completed_empty == 15,
        "Every active call must have completed successfully",
    )
    qc_metadata_mismatches = 0
    for run_id, qc in run_qc_lookup.items():
        run = active_lookup.get(run_id)
        if run is None or any(
            qc[field] != run[field]
            for field in (
                "fine_cell_type",
                "broad_network",
                "signature_group",
                "signature_direction",
            )
        ):
            qc_metadata_mismatches += 1
    add_check(
        checks,
        "run_qc_manifest_metadata",
        qc_metadata_mismatches,
        0,
        qc_metadata_mismatches == 0,
        "Run-QC metadata must match the active run manifest",
    )

    all_returned_rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    invalid_significant_rows = 0
    metadata_mismatches = 0
    annotation_missing = 0
    for row in iter_tsv(stock_path):
        run_id = row["kda_run_id"]
        gene = row["key_driver"]
        key = (run_id, gene)
        if key in seen_keys:
            fail(f"Duplicate stock returned key: {key}")
        seen_keys.add(key)
        run = active_lookup.get(run_id)
        if run is None:
            fail(f"Stock return belongs to an inactive or unknown call: {run_id}")
        if any(
            row[field] != run[field]
            for field in (
                "fine_cell_type",
                "broad_network",
                "signature_group",
                "signature_direction",
            )
        ):
            metadata_mismatches += 1
        within_q = as_float(row.get("adjusted_p_value"))
        log_p = as_float(row.get("log_p_value"))
        if within_q is None or within_q <= 0 or within_q > 0.05 + 1e-12:
            invalid_significant_rows += 1
        if log_p is None or log_p > 1e-12:
            invalid_significant_rows += 1
        ann = annotations.get(gene)
        if ann is None:
            annotation_missing += 1
            continue
        label = GROUP_LABELS[row["signature_group"]]
        all_returned_rows.append(
            {
                "cohort": "SEAAD",
                "kda_run_id": run_id,
                "query_rule_id": query_rule_id,
                "result_tier_id": result_tier_id,
                "fine_cell_type": row["fine_cell_type"],
                "broad_network": row["broad_network"],
                "signature_group": row["signature_group"],
                "sex": label["sex"],
                "apoe_group": label["apoe_group"],
                "signature_direction": row["signature_direction"],
                "current_symbol": gene,
                "case_id": "mt_driver" if ann["is_core_mito"] else "non_mt_driver",
                "is_core_mito": bool(ann["is_core_mito"]),
                "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
                "mito_tier": ann["mito_tier"],
                "genome_origin": ann["genome_origin"],
                "best_layer": int(row["best_layer"]),
                "overlap_count": int(row["overlap_count"]),
                "neighborhood_size": int(row["neighborhood_size"]),
                "non_neighborhood_size": int(row["non_neighborhood_size"]),
                "signature_size": int(row["signature_size"]),
                "fold_enrichment": float(row["fold_enrichment"]),
                "returned_log_p": float(log_p) if log_p is not None else None,
                "returned_raw_p": math.exp(float(log_p)) if log_p is not None else None,
                "returned_within_call_q": float(within_q) if within_q is not None else None,
                "is_signature": as_optional_bool(row["is_signature"]),
                "is_root_node": as_optional_bool(row["is_root_node"]),
                "global_key_driver": as_optional_bool(row["global_key_driver"]),
                "overlap_items": row["overlap_items"] or NA_TEXT,
            }
        )

    expected_returns = int(kda_status["significant_return_rows"])
    add_check(
        checks,
        "stock_returned_row_count",
        len(all_returned_rows),
        expected_returns,
        len(all_returned_rows) == expected_returns == 201,
        "Use every stock significant return from the 42 active calls",
    )
    add_check(
        checks,
        "stock_returned_unique_keys",
        len(seen_keys),
        expected_returns,
        len(seen_keys) == expected_returns,
        "Each active call and returned gene must occur at most once",
    )
    add_check(
        checks,
        "stock_significance_filter",
        invalid_significant_rows,
        0,
        invalid_significant_rows == 0,
        "Every stock return must have finite within-call q in (0, 0.05] and valid log P",
    )
    add_check(
        checks,
        "stock_manifest_metadata",
        metadata_mismatches,
        0,
        metadata_mismatches == 0,
        "Every stock result must match its manifest metadata",
    )
    add_check(
        checks,
        "returned_gene_annotation",
        annotation_missing,
        0,
        annotation_missing == 0,
        "Every returned gene must have a frozen Phase 18 class annotation",
    )
    stock_counts_by_run = Counter(row["kda_run_id"] for row in all_returned_rows)
    per_run_return_mismatches = sum(
        stock_counts_by_run[run_id] != int(qc["significant_key_drivers"])
        for run_id, qc in run_qc_lookup.items()
    )
    add_check(
        checks,
        "per_run_return_count_parity",
        per_run_return_mismatches,
        0,
        per_run_return_mismatches == 0,
        "Each call's stock row count must match its validated run-QC count",
    )
    parity_failures = sum(
        not is_true(row["r_python_significant_parity"]) for row in run_qc_rows
    )
    add_check(
        checks,
        "r_python_significant_parity",
        parity_failures,
        0,
        parity_failures == 0,
        "Every stock R return set must match the independent Python reconstruction",
    )

    mt_rows = [row for row in all_returned_rows if row["is_core_mito"]]
    returned_rows = [row for row in all_returned_rows if not row["is_core_mito"]]
    add_check(
        checks,
        "non_mt_filter_conservation",
        f"{len(returned_rows)} retained + {len(mt_rows)} excluded",
        "121 retained + 80 excluded",
        len(returned_rows) == 121
        and len(mt_rows) == 80
        and len(returned_rows) + len(mt_rows) == len(all_returned_rows),
        "Filter the 201 stock returns exactly by frozen core-MitoCarta membership",
    )
    add_check(
        checks,
        "non_mt_detail_only",
        sum(row["is_core_mito"] or row["case_id"] != "non_mt_driver" for row in returned_rows),
        0,
        all(not row["is_core_mito"] and row["case_id"] == "non_mt_driver" for row in returned_rows),
        "No core-MitoCarta key driver may enter the requested output",
    )
    retained_signature_missing = sum(
        row["is_signature"] is None for row in returned_rows
    )
    add_check(
        checks,
        "retained_signature_missingness",
        retained_signature_missing,
        2,
        retained_signature_missing == 2,
        "Preserve source is_signature=NA values instead of coercing them to FALSE",
    )

    by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_category_gene: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in returned_rows:
        by_gene[row["current_symbol"]].append(row)
        by_category_gene[
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        ].append(row)

    global_rows = [
        summarize_unit(
            rows,
            scope="all_relaxed_seaad_calls",
            phase18=phase18,
            query_rule_id=query_rule_id,
            result_tier_id=result_tier_id,
        )
        for _, rows in sorted(by_gene.items())
    ]
    assign_ranks(global_rows, [])
    category_rows = [
        summarize_unit(
            rows,
            scope="signature_group_by_broad_network",
            phase18=phase18,
            query_rule_id=query_rule_id,
            result_tier_id=result_tier_id,
            signature_group=group,
            broad_network=network,
        )
        for (group, network, _), rows in sorted(by_category_gene.items())
    ]
    assign_ranks(category_rows, ["signature_group", "broad_network"])

    global_lookup = {row["current_symbol"]: row for row in global_rows}
    category_lookup = {
        (row["signature_group"], row["broad_network"], row["current_symbol"]): row
        for row in category_rows
    }
    detail_rows: list[dict[str, Any]] = []
    for row in sorted(
        returned_rows,
        key=lambda item: (
            GROUPS.index(item["signature_group"]),
            networks.index(item["broad_network"]),
            item["current_symbol"],
            item["kda_run_id"],
        ),
    ):
        global_row = global_lookup[row["current_symbol"]]
        category_row = category_lookup[
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        ]
        detail_rows.append(
            {
                **row,
                "global_returned_call_count": global_row["returned_call_count"],
                "global_returned_run_q_acat_score": global_row["returned_run_q_acat_score"],
                "global_requested_final_q": global_row["requested_final_q"],
                "global_rank": global_row["rank"],
                "category_returned_call_count": category_row["returned_call_count"],
                "category_returned_run_q_acat_score": category_row["returned_run_q_acat_score"],
                "category_requested_final_q": category_row["requested_final_q"],
                "category_rank": category_row["rank"],
            }
        )

    calls_by_category = Counter(
        (row["signature_group"], row["broad_network"]) for row in active_rows
    )
    significant_calls_by_category = Counter(
        (active_lookup[row["kda_run_id"]]["signature_group"], active_lookup[row["kda_run_id"]]["broad_network"])
        for row in run_qc_rows
        if row["terminal_status"] == "completed_significant"
    )
    all_returns_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    non_mt_returns_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    units_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in all_returned_rows:
        all_returns_by_category[(row["signature_group"], row["broad_network"])].append(row)
    for row in returned_rows:
        non_mt_returns_by_category[(row["signature_group"], row["broad_network"])].append(row)
    for row in category_rows:
        units_by_category[(row["signature_group"], row["broad_network"])].append(row)

    category_summary: list[dict[str, Any]] = []
    for group in GROUPS:
        for network in networks:
            key = (group, network)
            calls = calls_by_category[key]
            all_returns = all_returns_by_category.get(key, [])
            non_mt_returns = non_mt_returns_by_category.get(key, [])
            units = units_by_category.get(key, [])
            if units:
                aggregation_status = "non_mt_returns_aggregated"
            elif calls:
                aggregation_status = "active_calls_no_non_mt_returns"
            else:
                aggregation_status = "no_active_kda_call"
            q_values = [float(row["requested_final_q"]) for row in units]
            significant_calls = significant_calls_by_category[key]
            category_summary.append(
                {
                    "signature_group": group,
                    "sex": GROUP_LABELS[group]["sex"],
                    "apoe_group": GROUP_LABELS[group]["apoe_group"],
                    "broad_network": network,
                    "aggregation_status": aggregation_status,
                    "included_call_count": calls,
                    "completed_significant_call_count": significant_calls,
                    "completed_empty_call_count": calls - significant_calls,
                    "all_class_stock_returned_row_count": len(all_returns),
                    "mt_excluded_returned_row_count": sum(row["is_core_mito"] for row in all_returns),
                    "non_mt_retained_returned_row_count": len(non_mt_returns),
                    "non_mt_returned_gene_count": len({row["current_symbol"] for row in non_mt_returns}),
                    "non_mt_singleton_gene_unit_count": sum(row["returned_call_count"] == 1 for row in units),
                    "non_mt_recurrent_gene_unit_count": sum(row["returned_call_count"] >= 2 for row in units),
                    "minimum_requested_final_q": min(q_values) if q_values else None,
                }
            )

    fixture = phase18.acat_combine(
        [0.5746569, 0.7090122, 0.7965851, 0.1149619], missing_action="omit"
    )
    add_check(
        checks,
        "acat_reference_fixture",
        fixture,
        0.4768092003,
        fixture is not None and abs(float(fixture) - 0.4768092003) <= 5e-10,
        "ACAT must reproduce the repository reference fixture",
    )
    repeated_fixture = phase18.acat_combine([0.01, 0.01], missing_action="omit")
    permutation_a = phase18.acat_combine([1e-20, 0.01, 0.04], missing_action="omit")
    permutation_b = phase18.acat_combine([0.04, 1e-20, 0.01], missing_action="omit")
    add_check(
        checks,
        "acat_invariants",
        f"repeat={repeated_fixture}|permutation_delta={abs(float(permutation_a)-float(permutation_b))}",
        "repeat=0.01|permutation_delta<=1e-15",
        repeated_fixture is not None
        and abs(float(repeated_fixture) - 0.01) <= 1e-15
        and abs(float(permutation_a) - float(permutation_b)) <= 1e-15,
        "Equal-weight ACAT must be stable for repeated values and input permutation",
    )
    add_check(
        checks,
        "global_non_mt_gene_counts",
        f"{len(global_rows)} total|{sum(row['returned_call_count'] == 1 for row in global_rows)} singleton|{sum(row['returned_call_count'] >= 2 for row in global_rows)} recurrent",
        "91 total|71 singleton|20 recurrent",
        len(global_rows) == 91
        and sum(row["returned_call_count"] == 1 for row in global_rows) == 71
        and sum(row["returned_call_count"] >= 2 for row in global_rows) == 20,
        "Global output must contain every retained non-MT gene exactly once",
    )
    add_check(
        checks,
        "category_non_mt_gene_counts",
        f"{len(category_rows)} total|{sum(row['returned_call_count'] == 1 for row in category_rows)} singleton|{sum(row['returned_call_count'] >= 2 for row in category_rows)} recurrent",
        "96 total|80 singleton|16 recurrent",
        len(category_rows) == 96
        and sum(row["returned_call_count"] == 1 for row in category_rows) == 80
        and sum(row["returned_call_count"] >= 2 for row in category_rows) == 16,
        "Category output must contain every retained group-network-gene unit",
    )
    conservation_ok = (
        sum(int(row["returned_call_count"]) for row in global_rows) == len(returned_rows)
        and sum(int(row["returned_call_count"]) for row in category_rows) == len(returned_rows)
    )
    add_check(
        checks,
        "returned_row_conservation",
        f"global={sum(int(row['returned_call_count']) for row in global_rows)}|category={sum(int(row['returned_call_count']) for row in category_rows)}",
        len(returned_rows),
        conservation_ok,
        "Both aggregation views must conserve the 121 retained returned rows",
    )
    singleton_mismatches = sum(
        row["returned_call_count"] == 1
        and (
            row["acat_of_returned_within_call_q"] is not None
            or float(row["requested_final_q"]) != float(row["minimum_returned_within_call_q"])
        )
        for row in [*global_rows, *category_rows]
    )
    recurrent_mismatches = sum(
        row["returned_call_count"] >= 2
        and (
            row["acat_of_returned_within_call_q"] is None
            or abs(float(row["requested_final_q"]) - float(row["acat_of_returned_within_call_q"])) > 1e-15
        )
        for row in [*global_rows, *category_rows]
    )
    add_check(
        checks,
        "singleton_passthrough",
        singleton_mismatches,
        0,
        singleton_mismatches == 0,
        "Every singleton score must equal its one returned within-call q",
    )
    add_check(
        checks,
        "recurrent_acat_assignment",
        recurrent_mismatches,
        0,
        recurrent_mismatches == 0,
        "Every recurrent score must equal the ACAT of only its returned q values",
    )
    invalid_scores = sum(
        not math.isfinite(float(row["requested_final_q"]))
        or not 0 <= float(row["requested_final_q"]) <= 1
        or float(row["requested_final_q"]) != float(row["returned_run_q_acat_score"])
        or row["case_id"] != "non_mt_driver"
        or row["is_core_mito"]
        or row["additional_across_gene_bh_applied"]
        or row["formal_fdr_controlled_q"]
        for row in [*global_rows, *category_rows]
    )
    add_check(
        checks,
        "output_score_contract",
        invalid_scores,
        0,
        invalid_scores == 0,
        "Every score must be finite, non-MT, alias-identical, and explicitly non-FDR-controlled",
    )
    global_ranks = sorted(int(row["rank"]) for row in global_rows)
    category_rank_ok = all(
        sorted(int(row["rank"]) for row in category_rows if row["signature_group"] == group and row["broad_network"] == network)
        == list(range(1, 1 + sum(row["signature_group"] == group and row["broad_network"] == network for row in category_rows)))
        for group in GROUPS
        for network in networks
    )
    add_check(
        checks,
        "rank_contiguity",
        f"global={len(global_ranks)}|category_groups_ok={category_rank_ok}",
        "global 1..91|all category ranks contiguous",
        global_ranks == list(range(1, 92)) and category_rank_ok,
        "Ranks must be contiguous after the non-MT filter",
    )
    active_category_count = sum(row["included_call_count"] > 0 for row in category_summary)
    return_category_count = sum(row["non_mt_retained_returned_row_count"] > 0 for row in category_summary)
    active_no_return_count = sum(
        row["included_call_count"] > 0 and row["all_class_stock_returned_row_count"] == 0
        for row in category_summary
    )
    add_check(
        checks,
        "structural_category_summary",
        f"{len(category_summary)} structural|{active_category_count} active|{return_category_count} returned|{active_no_return_count} active-empty",
        "42 structural|6 active|4 returned|2 active-empty",
        len(category_summary) == 42
        and active_category_count == 6
        and return_category_count == 4
        and active_no_return_count == 2,
        "Preserve all structural categories, including zero-call and completed-empty categories",
    )

    failed_checks = [row for row in checks if not row["passed"]]
    if failed_checks:
        fail(f"SEA-AD simple aggregation failed checks: {[row['check_id'] for row in failed_checks]}")

    global_rows.sort(key=lambda row: int(row["rank"]))
    category_rows.sort(
        key=lambda row: (
            GROUPS.index(row["signature_group"]),
            networks.index(row["broad_network"]),
            int(row["rank"]),
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    global_path = output_dir / "simple_global_gene_aggregates.tsv"
    category_path = output_dir / "simple_category_gene_aggregates.tsv"
    detail_path = output_dir / "simple_returned_call_rows.tsv.gz"
    category_summary_path = output_dir / "simple_category_summary.tsv"
    checks_path = output_dir / "simple_checks.tsv"
    status_path = output_dir / "simple_status.tsv"
    methods_path = output_dir / "README.md"
    artifacts_path = output_dir / "simple_artifacts.tsv"

    output_counts = {
        global_path.name: write_tsv(
            global_path,
            global_rows,
            AGGREGATE_FIELDS,
            f"{SCHEMA_ROOT}_global_gene_aggregates_v1",
        ),
        category_path.name: write_tsv(
            category_path,
            category_rows,
            AGGREGATE_FIELDS,
            f"{SCHEMA_ROOT}_category_gene_aggregates_v1",
        ),
        detail_path.name: write_tsv(
            detail_path,
            detail_rows,
            DETAIL_FIELDS,
            f"{SCHEMA_ROOT}_returned_call_rows_v1",
        ),
        category_summary_path.name: write_tsv(
            category_summary_path,
            category_summary,
            CATEGORY_FIELDS,
            f"{SCHEMA_ROOT}_category_summary_v1",
        ),
        checks_path.name: write_tsv(
            checks_path,
            checks,
            CHECK_FIELDS,
            f"{SCHEMA_ROOT}_checks_v1",
        ),
    }

    status_row = {
        "analysis_id": ANALYSIS_ID,
        "cohort": "SEAAD",
        "execution_status": "complete",
        "interpretation_status": "exploratory_post_selected_not_fdr_controlled",
        "source_kda_execution": "reused_validated_complete_vh10b_calls_no_rerun",
        "git_revision": git_revision(root),
        "query_rule_id": query_rule_id,
        "result_tier_id": result_tier_id,
        "included_run_count": len(active_rows),
        "completed_significant_call_count": completed_significant,
        "completed_empty_call_count": completed_empty,
        "all_class_stock_returned_row_count": len(all_returned_rows),
        "mt_excluded_returned_row_count": len(mt_rows),
        "non_mt_retained_returned_row_count": len(returned_rows),
        "non_mt_unique_returned_gene_count": len(global_rows),
        "global_singleton_gene_count": sum(row["returned_call_count"] == 1 for row in global_rows),
        "global_recurrent_gene_count": sum(row["returned_call_count"] >= 2 for row in global_rows),
        "global_aggregate_row_count": len(global_rows),
        "category_gene_unit_count": len(category_rows),
        "category_singleton_unit_count": sum(row["returned_call_count"] == 1 for row in category_rows),
        "category_recurrent_unit_count": sum(row["returned_call_count"] >= 2 for row in category_rows),
        "structural_category_count": len(category_summary),
        "active_category_count": active_category_count,
        "return_bearing_category_count": return_category_count,
        "failed_check_count": 0,
        "output_directory": str(output_dir),
    }
    output_counts[status_path.name] = write_tsv(
        status_path,
        [status_row],
        STATUS_FIELDS,
        f"{SCHEMA_ROOT}_status_v1",
    )

    methods = f"""# SEA-AD simple returned-only non-MT KDA aggregation

This directory applies the requested exploratory aggregation to the already
validated **{len(active_rows)} SEA-AD KDA calls**. The upstream calls were not
rerun: VH10B is `validated_complete`, and its exact registered set of
**{len(all_returned_rows)} significant `call_key_drivers()` rows** was reused.

The source tier is already relaxed upstream: donor support is at least 3 per
disease arm, the mitochondrial DEG query uses within-contrast FDR below 0.05
without a fold-change cutoff, and an effective KDA query requires at least 3
genes. Its frozen identifiers are `{query_rule_id}` and `{result_tier_id}`.

The requested returned-only rule is:

1. Start only with genes returned as significant by `call_key_drivers()`;
   their `adjusted_p_value` values are within-call BH q values at q <= 0.05.
2. Exclude core-MitoCarta drivers before aggregation. Here "non-MT" follows
   the project definition `is_mitocarta3=FALSE` (more precisely, non-core-MT),
   not merely "not encoded by mtDNA".
3. If a gene has one returned row in the aggregation scope, copy that q value
   unchanged.
4. If it has two or more returned rows, equal-weight ACAT-combine only those
   returned q values.
5. Do not add P=1 rows for unreturned calls and do not apply another
   across-gene BH adjustment.

Of the {len(all_returned_rows)} source rows, {len(mt_rows)} core-MT rows were
excluded and {len(returned_rows)} non-MT rows were retained. The retained rows
represent {len(global_rows)} unique genes: {sum(row['returned_call_count'] == 1 for row in global_rows)}
singletons and {sum(row['returned_call_count'] >= 2 for row in global_rows)} recurrent genes globally.

Two aggregate views are provided:

- `simple_global_gene_aggregates.tsv`: one row per retained gene across all 42
  available calls.
- `simple_category_gene_aggregates.tsv`: one row per
  sex/APOE group + broad network + retained gene. Fine supertype and direction
  remain provenance/recurrence dimensions.

`simple_returned_call_rows.tsv.gz` contains the exact {len(returned_rows)}
retained non-MT returned rows and links each to both aggregate views.
`simple_category_summary.tsv` preserves all 42 structural sex/APOE-by-network
categories, including categories without an active KDA call or without a
significant return.

## Interpretation warning

`returned_run_q_acat_score` is the canonical value and `requested_final_q` is
an identical compatibility alias. Neither is a formally FDR-controlled
cross-call q value: the inputs were selected for within-call significance,
ACAT is applied to adjusted values rather than a complete raw-P family, and no
final across-gene multiplicity correction is made. Use this output for
exploratory comparison and ranking, not confirmatory error-rate claims.

The global view reflects the available active-call distribution rather than a
balanced six-group design: 40 of the 42 active calls are in `M_e33`. Use the
sex/APOE-by-network category view when comparing category-specific candidates.
Ranks are consecutive after sorting by score and then gene symbol; genes with
identical scores have equal numerical evidence even though the lexical
tie-break gives them different display ranks.
"""
    atomic_write_text(methods_path, methods)
    output_counts[methods_path.name] = 1

    artifact_rows: list[dict[str, Any]] = []
    for role, path in (
        ("script", Path(__file__).resolve()),
        ("input_config", config_path),
        ("input_vh10a_status", input_dir / "status.tsv"),
        ("input_vh10a_artifacts", input_dir / "artifacts.tsv"),
        ("input_run_manifest", manifest_path),
        ("input_vh10b_status", kda_dir / "status.tsv"),
        ("input_vh10b_artifacts", kda_dir / "artifacts.tsv"),
        ("input_run_qc", run_qc_path),
        ("input_stock_significant_returns", stock_path),
        ("input_phase18_acat_code", phase18_path),
        ("input_phase18_annotation", annotation_path),
        ("output_global_aggregates", global_path),
        ("output_category_aggregates", category_path),
        ("output_returned_rows", detail_path),
        ("output_category_summary", category_summary_path),
        ("output_checks", checks_path),
        ("output_status", status_path),
        ("output_methods", methods_path),
    ):
        artifact_rows.append(
            {
                "role": role,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    output_counts[artifacts_path.name] = write_tsv(
        artifacts_path,
        artifact_rows,
        ARTIFACT_FIELDS,
        f"{SCHEMA_ROOT}_artifacts_v1",
    )

    for name, count in sorted(output_counts.items()):
        print(f"{name}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
