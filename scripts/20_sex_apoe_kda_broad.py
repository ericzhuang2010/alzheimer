#!/usr/bin/env python3
"""Execute direct broad-cell sex/APOE KDA without cross-run aggregation.

DEPRECATED (2026-08-29): the direct broad-cell branch is superseded by the
returned-only simple aggregation
(``scripts/20_sex_apoe_kda_simple_aggr.py`` writing
``results/minerva_production/20_sex_apoe_kda_simple_aggr``). The release this
script produced was renamed to
``results/minerva_production/20_sex_apoe_kda_broad (deprecated)``. The script
is retained for provenance only.

The analysis consumes the validated Phase 08 donor-level broad-cell DEG
release. Each broad-cell x sex/APOE contrast is split into AD-up and AD-down
core-MitoCarta queries. Eligible directional queries are tested directly in
their matching Bayesian network. The complete pre-FDR fKDA test family is
reconstructed with the parity-tested Phase 18 engine, core-MT candidate genes
are removed, and BH is rebuilt across all explicit non-MT candidates within
each directional run.

No coverage calculation, implicit cross-run null, ACAT, recurrence gate, or
leave-one-fine-type-out analysis is performed in this module.
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
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import networkx as nx
import scipy
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "phase20_sex_apoe_kda_broad.yml"
NA_TEXT = "NA"
TRUE_VALUES = {"TRUE", "T", "1", "YES"}

CATEGORY_SCHEMA = "phase20_broad_category_manifest_v1"
DIRECTION_SCHEMA = "phase20_broad_direction_manifest_v1"
SIGNATURE_SCHEMA = "phase20_broad_signature_members_v1"
BACKGROUND_SCHEMA = "phase20_broad_background_members_v1"
COLLISION_SCHEMA = "phase20_broad_symbol_mapping_collisions_v1"
TEST_SCHEMA = "phase20_broad_candidate_tests_v1"
STOCK_SCHEMA = "phase20_broad_stock_fkda_returns_v1"
CANDIDATE_SCHEMA = "phase20_broad_non_mt_candidates_v1"
SUMMARY_SCHEMA = "phase20_broad_category_summary_v1"
FUNNEL_SCHEMA = "phase20_broad_filter_funnel_v1"
CHECK_SCHEMA = "phase20_broad_checks_v1"
ARTIFACT_SCHEMA = "phase20_broad_artifacts_v1"
STATUS_SCHEMA = "phase20_broad_status_v1"
INPUT_SCHEMA = "phase20_broad_input_authority_v1"
NETWORK_SCHEMA = "phase20_broad_network_authority_v1"

PRIMARY_MANIFEST_FIELDS = [
    "analysis_id",
    "manifest_row",
    "category_id",
    "kda_run_id",
    "query_tier",
    "contrast_id",
    "broad_cell_type",
    "group_id",
    "sex",
    "apoe_group",
    "signature_direction",
    "source_terminal_status",
    "source_message",
    "donors_ad",
    "donors_nci",
    "provisional_query_rows",
    "provisional_query_genes",
    "effective_query_genes",
    "query_genes_lost_from_background",
    "source_result_rows",
    "exact_tested_genes",
    "mapped_symbol_collision_count",
    "mapped_symbol_collapsed_rows",
    "full_network_edges",
    "induced_network_edges",
    "effective_background_genes",
    "query_size_tier",
    "eligibility_status",
    "terminal_status",
    "explicit_candidate_tests",
    "non_mt_candidate_family_size",
    "stock_significant_returns",
    "relaxed_non_mt_candidates",
    "strict_non_mt_candidates",
    "message",
]

TEST_FIELDS = [
    "analysis_id",
    "query_tier",
    "kda_run_id",
    "category_id",
    "contrast_id",
    "broad_cell_type",
    "group_id",
    "sex",
    "apoe_group",
    "signature_direction",
    "query_size_tier",
    "effective_query_genes",
    "effective_background_genes",
    "current_symbol",
    "is_core_mito",
    "mito_tier",
    "genome_origin",
    "is_mtdna_gene",
    "mapping_status",
    "query_member",
    "self_excluded_in_phase18_engine",
    "best_layer",
    "query_overlap",
    "neighborhood_size",
    "non_neighborhood_size",
    "signature_size",
    "fold_enrichment",
    "log_p_value",
    "raw_p_value",
    "original_run_q",
    "non_mt_run_q",
    "stock_fkda_q05_return",
    "is_root_node",
    "out_degree",
    "undirected_degree",
    "stock_is_signature",
    "stock_is_root_node",
    "stock_global_key_driver",
    "overlap_items",
    "overlap_gate_pass",
    "fold_enrichment_gate_pass",
    "relaxed_q_gate_pass",
    "strict_q_gate_pass",
    "relaxed_primary_candidate",
    "strict_direct_reference",
]

CANDIDATE_FIELDS = TEST_FIELDS + [
    "direction_rank",
    "top10_display",
    "top5_display",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bh_adjust(values: Sequence[float | None]) -> list[float | None]:
    """Benjamini-Hochberg adjustment with stable input-order tie handling."""
    adjusted: list[float | None] = [None] * len(values)
    valid = [
        index
        for index, value in enumerate(values)
        if value is not None and math.isfinite(float(value))
    ]
    ordered = sorted(valid, key=lambda index: (float(values[index]), index))
    previous = 1.0
    total = len(ordered)
    for position in range(total - 1, -1, -1):
        index = ordered[position]
        value = min(previous, float(values[index]) * total / (position + 1), 1.0)
        adjusted[index] = value
        previous = value
    return adjusted


def display_value(value: Any) -> Any:
    if value is None:
        return NA_TEXT
    if isinstance(value, float) and not math.isfinite(value):
        return NA_TEXT
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", newline="")
    return path.open(mode, newline="")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"Required TSV does not exist: {path}")
    with open_text(path, "r") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    if not path.is_file():
        fail(f"Required TSV does not exist: {path}")
    with open_text(path, "r") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def deterministic_text_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    if path.suffix != ".gz":
        return temporary, temporary.open("w", newline="")
    raw = temporary.open("wb")
    compressed = gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0
    )
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    return temporary, text


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: Sequence[str],
    schema_version: str,
) -> int:
    temporary, handle = deterministic_text_writer(path)
    count = 0
    fieldnames = ["schema_version", *[field for field in fields if field != "schema_version"]]
    try:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = {field: display_value(row.get(field)) for field in fields}
            output["schema_version"] = schema_version
            writer.writerow(output)
            count += 1
    finally:
        handle.close()
    temporary.replace(path)
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def safe_id(*parts: Any) -> str:
    text = "__".join(str(part) for part in parts)
    return "".join(character if character.isalnum() else "_" for character in text)


def load_python_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        fail(f"Could not load Python module: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def add_check(
    rows: list[dict[str, Any]],
    check_id: str,
    observed: Any,
    expected: Any,
    passed: bool,
    detail: str = "",
    severity: str = "error",
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "severity": severity,
            "observed": observed,
            "expected": expected,
            "passed": bool(passed),
            "detail": detail,
        }
    )


def require_equal(observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        fail(f"{label}: expected {expected!r}, observed {observed!r}")


def annotation_row(symbol: str, annotation: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = annotation.get(symbol)
    if row is None:
        fail(f"Network candidate lacks frozen Phase 09 annotation: {symbol}")
    return row


def load_complete_annotation(
    path: Path, phase18: Any
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load Phase 09 using the same current-symbol/fallback policy as Phase 08."""
    annotation: dict[str, dict[str, Any]] = {}
    conflicts: list[str] = []
    scientific_fields = (
        "is_core_mito",
        "mitocarta_canonical_symbol",
        "mito_tier",
        "genome_origin",
        "is_mtdna_gene",
        "extended_reference_member",
        "phase03_mitocarta_match_type",
    )
    for row in iter_tsv(path):
        if phase18.is_true(row.get("reference_only")):
            continue
        current_symbol = row.get("symbol_hgnc_current", "")
        mapped = (
            current_symbol
            if current_symbol and current_symbol != NA_TEXT
            else row.get("feature_id_original", "")
        )
        if not mapped or mapped == NA_TEXT:
            continue
        entry = {
            "is_core_mito": phase18.is_true(row.get("is_mitocarta3")),
            "mitocarta_canonical_symbol": row.get("mitocarta_canonical_symbol") or NA_TEXT,
            "mito_tier": row.get("mito_tier") or NA_TEXT,
            "genome_origin": row.get("genome_origin") or NA_TEXT,
            "is_mtdna_gene": phase18.is_true(row.get("is_mtDNA_gene")),
            "extended_reference_member": phase18.is_true(
                row.get("extended_reference_member")
            ),
            "mapping_status": row.get("mapping_status") or NA_TEXT,
            "phase03_mitocarta_match_type": row.get("phase03_mitocarta_match_type")
            or NA_TEXT,
        }
        previous = annotation.get(mapped)
        if previous is None:
            annotation[mapped] = entry
            continue
        if any(previous[field] != entry[field] for field in scientific_fields):
            conflicts.append(mapped)
            continue
        mapping_routes = set(str(previous["mapping_status"]).split("|"))
        mapping_routes.update(str(entry["mapping_status"]).split("|"))
        previous["mapping_status"] = "|".join(sorted(mapping_routes))
    return annotation, sorted(set(conflicts))


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    require_equal(
        config.get("schema_version"),
        "phase20_sex_apoe_kda_broad_config_v1",
        "Broad KDA config schema",
    )
    require_equal(config["analysis"]["aggregation_method"], "none", "Aggregation method")
    return config


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir")
    return parser.parse_args(argv)


def validate_frozen_inputs(
    config: dict[str, Any], config_path: Path
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    phase08 = project_path(config["paths"]["phase08_broad_directory"])
    paths: dict[str, Path] = {
        "phase08_directory": phase08,
        "phase09_annotation": project_path(config["paths"]["phase09_annotation"]),
        "phase09_status": project_path(config["paths"]["phase09_status"]),
        "phase09_checks": project_path(config["paths"]["phase09_checks"]),
        "phase12_config": project_path(config["paths"]["phase12_config"]),
        "fkda_source": project_path(config["paths"]["fkda_source"]),
        "complete_evidence_engine": project_path(
            config["paths"]["complete_evidence_engine"]
        ),
        "fkda_parity_helper": project_path(config["paths"]["fkda_parity_helper"]),
        "analysis_config": config_path,
        "analysis_script": Path(__file__).resolve(),
    }
    for name, path in paths.items():
        if name == "phase08_directory":
            if not path.is_dir():
                fail(f"Required Phase 08 directory is missing: {path}")
        elif not path.is_file():
            fail(f"Required input is missing ({name}): {path}")

    authority: list[dict[str, Any]] = []
    for relative, expected in config["frozen_inputs"]["files"].items():
        path = phase08 / relative
        if not path.is_file():
            fail(f"Frozen Phase 08 input is missing: {path}")
        observed = sha256_file(path)
        if observed != str(expected):
            fail(f"Frozen Phase 08 checksum changed: {relative}")
        authority.append(
            {
                "artifact_role": "phase08_broad_input",
                "source_path": relative_path(path),
                "expected_sha256": expected,
                "observed_sha256": observed,
                "bytes": path.stat().st_size,
                "checksum_pass": True,
            }
        )

    extra_hashes = {
        "phase09_annotation": "phase09_annotation_sha256",
        "phase09_status": "phase09_status_sha256",
        "phase09_checks": "phase09_checks_sha256",
        "phase12_config": "phase12_config_sha256",
        "fkda_source": "fkda_source_sha256",
        "complete_evidence_engine": "complete_evidence_engine_sha256",
        "fkda_parity_helper": "fkda_parity_helper_sha256",
    }
    for role, config_key in extra_hashes.items():
        path = paths[role]
        expected = str(config["frozen_inputs"][config_key])
        observed = sha256_file(path)
        if observed != expected:
            fail(f"Frozen checksum changed for {role}: {observed} != {expected}")
        authority.append(
            {
                "artifact_role": role,
                "source_path": relative_path(path),
                "expected_sha256": expected,
                "observed_sha256": observed,
                "bytes": path.stat().st_size,
                "checksum_pass": True,
            }
        )

    for role in ("analysis_config", "analysis_script"):
        path = paths[role]
        observed = sha256_file(path)
        authority.append(
            {
                "artifact_role": role,
                "source_path": relative_path(path),
                "expected_sha256": observed,
                "observed_sha256": observed,
                "bytes": path.stat().st_size,
                "checksum_pass": True,
            }
        )
    authority.sort(key=lambda row: (row["artifact_role"], row["source_path"]))
    return paths, authority


def validate_source_release(
    config: dict[str, Any], phase08: Path, phase09_status_path: Path,
    phase09_checks_path: Path
) -> tuple[dict[str, str], list[dict[str, str]], list[dict[str, str]]]:
    status_rows = read_tsv(phase08 / "broad_deg_status.tsv")
    if len(status_rows) != 1:
        fail("Phase 08 broad status must contain exactly one row")
    status = status_rows[0]
    require_equal(
        status.get("validation_status"),
        config["frozen_inputs"]["required_phase08_status"],
        "Phase 08 broad validation status",
    )
    checks = read_tsv(phase08 / "broad_deg_checks.tsv")
    failed = [row for row in checks if not is_true(row.get("passed"))]
    if failed:
        fail(f"Phase 08 broad release has failed checks: {[row['check'] for row in failed]}")
    phase09_status = read_tsv(phase09_status_path)
    if len(phase09_status) != 1:
        fail("Phase 09 annotation status must contain exactly one row")
    require_equal(
        phase09_status[0].get("validation_status"),
        config["frozen_inputs"]["required_phase09_status"],
        "Phase 09 annotation validation status",
    )
    phase09_checks = read_tsv(phase09_checks_path)
    phase09_failed = [row for row in phase09_checks if not is_true(row.get("passed"))]
    if phase09_failed:
        fail(
            "Phase 09 annotation release has failed checks: "
            f"{[row.get('check', row.get('check_id')) for row in phase09_failed]}"
        )
    contrast_status = read_tsv(phase08 / "broad_deg_contrast_status.tsv")
    require_equal(len(contrast_status), config["scope"]["expected_categories"], "Contrast statuses")
    return status, checks, contrast_status


def load_categories(
    config: dict[str, Any], phase08: Path, contrast_status: list[dict[str, str]]
) -> list[dict[str, Any]]:
    manifest = read_tsv(phase08 / "00_inputs" / "broad_deg_contrast_manifest.tsv")
    require_equal(len(manifest), config["scope"]["expected_categories"], "Category manifest rows")
    status_by_key = {
        (row["broad_cell_type"], row["group_id"]): row for row in contrast_status
    }
    if len(status_by_key) != len(contrast_status):
        fail("Contrast-status keys are duplicated")
    groups = list(config["scope"]["groups"])
    networks = list(config["scope"]["broad_networks"])
    categories: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in sorted(manifest, key=lambda value: as_int(value["manifest_row"])):
        key = (row["broad_cell_type"], row["group_id"])
        if key in seen:
            fail(f"Duplicate category key: {key}")
        seen.add(key)
        if key[0] not in networks or key[1] not in groups:
            fail(f"Category outside frozen scope: {key}")
        source = status_by_key.get(key)
        if source is None:
            fail(f"Category has no terminal source status: {key}")
        categories.append(
            {
                **row,
                "category_id": f"{row['broad_cell_type']}::{row['group_id']}",
                "source_terminal_status": source["terminal_status"],
                "source_message": source.get("message", ""),
                "source_genes_returned": source.get("genes_returned", "0"),
            }
        )
    expected_keys = {(network, group) for network in networks for group in groups}
    require_equal(seen, expected_keys, "Frozen 42-category grid")
    return categories


def load_tested_gene_sets(
    phase08: Path,
) -> tuple[
    dict[tuple[str, str], set[str]],
    dict[tuple[str, str], int],
    dict[tuple[str, str], dict[str, set[str]]],
]:
    tested: dict[tuple[str, str], set[str]] = defaultdict(set)
    result_rows: dict[tuple[str, str], int] = Counter()
    symbol_sources: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for row in iter_tsv(phase08 / "broad_deg_results.tsv.gz"):
        key = (row["broad_cell_type"], row["group_id"])
        symbol = row.get("mapped_gene", "")
        if not symbol or symbol == NA_TEXT:
            fail(f"Tested DEG row lacks mapped_gene for {key}/{row.get('gene')}")
        tested[key].add(symbol)
        result_rows[key] += 1
        symbol_sources[key][symbol].add(row.get("gene", symbol))
    return dict(tested), dict(result_rows), dict(symbol_sources)


def load_query_sets(
    config: dict[str, Any], phase08: Path
) -> tuple[
    dict[tuple[str, str, str, str], set[str]],
    dict[tuple[str, str, str, str], int],
]:
    queries: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    input_rows: dict[tuple[str, str, str, str], int] = Counter()
    seen: set[tuple[str, str, str, str, str]] = set()
    allowed_tiers = set(config["scope"]["query_tiers"])
    allowed_directions = set(config["scope"]["directions"])
    for row in iter_tsv(phase08 / "broad_core_mito_kda_query_handoff.tsv.gz"):
        tier = row["signature_tier"]
        direction = row["signature_direction"]
        if tier not in allowed_tiers or direction not in allowed_directions:
            fail(f"Unexpected handoff tier/direction: {tier}/{direction}")
        if row.get("mito_tier") != "core_mito_protein":
            fail("Broad KDA handoff contains a non-core-MT query member")
        symbol = row.get("mapped_gene", "")
        if not symbol or symbol == NA_TEXT:
            fail("Broad KDA handoff contains an unmapped query member")
        key = (tier, row["broad_cell_type"], row["group_id"], direction)
        member_key = (*key, symbol)
        if member_key in seen:
            fail(f"Duplicate query membership: {member_key}")
        seen.add(member_key)
        queries[key].add(symbol)
        input_rows[key] += 1
    return dict(queries), dict(input_rows)


def load_networks(
    config: dict[str, Any], phase12_config_path: Path, phase18: Any
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    with phase12_config_path.open() as handle:
        phase12 = yaml.safe_load(handle)
    require_equal(phase12.get("schema_version"), "phase12_kda_config_v1", "Phase 12 config schema")
    network_data: dict[str, dict[str, Any]] = {}
    authority: list[dict[str, Any]] = []
    for name in config["scope"]["broad_networks"]:
        entry = phase12["networks"].get(name)
        if entry is None:
            fail(f"Broad network is not configured in Phase 12: {name}")
        path = project_path(entry["path"])
        observed_hash = sha256_file(path)
        expected_hash = str(entry["sha256"])
        if observed_hash != expected_hash:
            fail(f"Network checksum changed for {name}")
        edges = phase18.load_network(path)
        graph = nx.DiGraph()
        graph.add_edges_from(edges)
        dag = nx.is_directed_acyclic_graph(graph)
        if not dag:
            fail(f"Configured Bayesian network is not a DAG: {name}")
        network_data[name] = {"path": path, "edges": edges, "graph": graph}
        authority.append(
            {
                "network": name,
                "source_path": relative_path(path),
                "expected_sha256": expected_hash,
                "observed_sha256": observed_hash,
                "bytes": path.stat().st_size,
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "is_dag": dag,
            }
        )
    return network_data, authority


def classify_query_size(size: int, minimum: int, phase18_sized: int) -> str:
    if size == 0:
        return "empty"
    if size < minimum:
        return "below_minimum"
    if size < phase18_sized:
        return "small_query_3_9"
    return "phase18_sized_query_ge10"


def build_slot_manifests(
    config: dict[str, Any],
    categories: list[dict[str, Any]],
    tested: dict[tuple[str, str], set[str]],
    result_rows: dict[tuple[str, str], int],
    symbol_sources: dict[tuple[str, str], dict[str, set[str]]],
    queries: dict[tuple[str, str, str, str], set[str]],
    query_input_rows: dict[tuple[str, str, str, str], int],
    network_data: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, tuple[set[str], set[str], list[tuple[str, str]]]],
    int,
]:
    minimum = as_int(config["eligibility"]["minimum_effective_query_genes"])
    phase18_sized = as_int(config["eligibility"]["phase18_sized_query_genes"])
    manifests: dict[str, list[dict[str, Any]]] = {}
    run_context: dict[str, tuple[set[str], set[str], list[tuple[str, str]]]] = {}
    networkx_disagreements = 0
    for tier in config["scope"]["query_tiers"]:
        slots: list[dict[str, Any]] = []
        for category in categories:
            broad = category["broad_cell_type"]
            group = category["group_id"]
            category_key = (broad, group)
            source_complete = category["source_terminal_status"] == "validated_complete"
            tested_genes = tested.get(category_key, set()) if source_complete else set()
            collision_count = sum(
                len(source_genes) > 1
                for source_genes in symbol_sources.get(category_key, {}).values()
            )
            full_edges = network_data[broad]["edges"]
            induced = [
                (source, target)
                for source, target in full_edges
                if source in tested_genes and target in tested_genes
            ]
            background = {gene for edge in induced for gene in edge}
            nx_edges = set(network_data[broad]["graph"].subgraph(tested_genes).edges())
            if nx_edges != set(induced):
                networkx_disagreements += 1
            for direction in config["scope"]["directions"]:
                query_key = (tier, broad, group, direction)
                provisional = set(queries.get(query_key, set()))
                effective = provisional & background
                run_id = safe_id("broad", tier, broad, group, direction)
                if not source_complete:
                    eligibility = "source_contrast_not_estimable"
                elif not induced:
                    eligibility = "no_induced_network_edges"
                elif not provisional:
                    eligibility = "no_provisional_query"
                elif not effective:
                    eligibility = "effective_query_empty_after_background"
                elif len(effective) < minimum:
                    eligibility = "effective_query_below_minimum"
                else:
                    eligibility = "eligible"
                terminal = "pending" if eligibility == "eligible" else f"skipped_{eligibility}"
                slot = {
                    "analysis_id": config["analysis"]["analysis_id"],
                    "manifest_row": as_int(category["manifest_row"]),
                    "category_id": category["category_id"],
                    "kda_run_id": run_id,
                    "query_tier": tier,
                    "contrast_id": category["contrast_id"],
                    "broad_cell_type": broad,
                    "group_id": group,
                    "sex": category["sex"],
                    "apoe_group": category["apoe_group"],
                    "signature_direction": direction,
                    "source_terminal_status": category["source_terminal_status"],
                    "source_message": category["source_message"],
                    "donors_ad": as_int(category["donors_ad"]),
                    "donors_nci": as_int(category["donors_nci"]),
                    "provisional_query_rows": query_input_rows.get(query_key, 0),
                    "provisional_query_genes": len(provisional),
                    "effective_query_genes": len(effective),
                    "query_genes_lost_from_background": len(provisional - background),
                    "source_result_rows": result_rows.get(category_key, 0),
                    "exact_tested_genes": len(tested_genes),
                    "mapped_symbol_collision_count": collision_count,
                    "mapped_symbol_collapsed_rows": max(
                        result_rows.get(category_key, 0) - len(tested_genes), 0
                    ),
                    "full_network_edges": len(full_edges),
                    "induced_network_edges": len(induced),
                    "effective_background_genes": len(background),
                    "query_size_tier": classify_query_size(len(effective), minimum, phase18_sized),
                    "eligibility_status": eligibility,
                    "terminal_status": terminal,
                    "explicit_candidate_tests": 0,
                    "non_mt_candidate_family_size": 0,
                    "stock_significant_returns": 0,
                    "relaxed_non_mt_candidates": 0,
                    "strict_non_mt_candidates": 0,
                    "message": "",
                }
                slots.append(slot)
                run_context[run_id] = (effective, background, induced)
        require_equal(
            len(slots),
            config["scope"]["expected_direction_slots_per_tier"],
            f"{tier} directional slots",
        )
        manifests[tier] = slots
    return manifests, run_context, networkx_disagreements


def slot_funnel_counts(
    slots: list[dict[str, Any]], minimum: int, phase18_sized: int
) -> dict[str, int]:
    counts = Counter()
    for slot in slots:
        eligibility = slot["eligibility_status"]
        size = as_int(slot["effective_query_genes"])
        if eligibility == "source_contrast_not_estimable":
            counts["source_contrast_not_estimable"] += 1
        elif eligibility == "no_provisional_query":
            counts["no_provisional_query"] += 1
        elif eligibility == "effective_query_empty_after_background":
            counts["effective_query_empty_after_background"] += 1
        elif eligibility == "effective_query_below_minimum" and 0 < size < minimum:
            counts["effective_query_size_1_2"] += 1
        elif eligibility == "eligible" and minimum <= size < phase18_sized:
            counts["effective_query_size_3_9"] += 1
        elif eligibility == "eligible" and size >= phase18_sized:
            counts["effective_query_size_ge10"] += 1
        else:
            counts[f"unexpected:{eligibility}:{size}"] += 1
    return dict(counts)


def validate_expected_funnels(
    config: dict[str, Any], manifests: dict[str, list[dict[str, Any]]]
) -> None:
    minimum = as_int(config["eligibility"]["minimum_effective_query_genes"])
    phase18_sized = as_int(config["eligibility"]["phase18_sized_query_genes"])
    for tier, expected in config["expected_sensitivity_funnel"].items():
        observed = slot_funnel_counts(manifests[tier], minimum, phase18_sized)
        unexpected = {key: value for key, value in observed.items() if key.startswith("unexpected:")}
        if unexpected:
            fail(f"Unexpected {tier} slot outcomes: {unexpected}")
        for key, value in expected.items():
            require_equal(observed.get(key, 0), as_int(value), f"{tier} funnel {key}")
        require_equal(sum(observed.values()), 84, f"{tier} funnel total")


def run_stock_fkda(
    paths: dict[str, Path],
    run_id: str,
    induced_edges: list[tuple[str, str]],
    query: set[str],
    background_size: int,
    n_layers: int,
    temp_parent: Path,
) -> list[dict[str, str]]:
    if not induced_edges or not query:
        return []
    with tempfile.TemporaryDirectory(prefix=f"fkda_{safe_id(run_id)}_", dir=temp_parent) as temp:
        temp_path = Path(temp)
        network_path = temp_path / "network.tsv"
        signature_path = temp_path / "signature.tsv"
        output_path = temp_path / "returns.tsv"
        with network_path.open("w", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["from", "to"])
            writer.writerows(induced_edges)
        with signature_path.open("w", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["Var", "Group"])
            for gene in sorted(query):
                writer.writerow([gene, run_id])
        result = subprocess.run(
            [
                "Rscript",
                "--vanilla",
                str(paths["fkda_parity_helper"]),
                str(paths["fkda_source"]),
                str(network_path),
                str(signature_path),
                str(background_size),
                str(n_layers),
                str(output_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            fail(
                f"Stock fKDA failed for {run_id}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
        return read_tsv(output_path)


def attach_original_overlap_items(
    phase18: Any,
    run_id: str,
    explicit: dict[str, dict[str, Any]],
    query: set[str],
    background: set[str],
    induced_edges: list[tuple[str, str]],
    n_layers: int,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Attach complete best-layer query membership to every explicit test."""
    _, outgoing, undirected = phase18.network_adjacency(induced_edges, background)
    for gene, record in explicit.items():
        layers = phase18.directed_layers(gene, outgoing, n_layers)
        layer_index = as_int(record["original"]["layer"]) - 1
        if layer_index < 0 or layer_index >= len(layers):
            fail(f"Best layer is unavailable for {run_id}/{gene}")
        overlap_items = sorted(layers[layer_index] & query)
        if len(overlap_items) != as_int(record["original"]["overlap"]):
            fail(f"Best-layer overlap membership drift for {run_id}/{gene}")
        record["original_overlap_items"] = overlap_items
    return outgoing, undirected


def validate_stock_parity(
    run_id: str,
    explicit: dict[str, dict[str, Any]],
    stock_rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    expected = {
        gene: record
        for gene, record in explicit.items()
        if record["original_q"] is not None and record["original_q"] <= 0.05
    }
    stock = {row["Keydriver"]: row for row in stock_rows}
    if len(stock) != len(stock_rows):
        fail(f"Stock fKDA returned duplicate genes for {run_id}")
    if set(stock) != set(expected):
        missing = sorted(set(expected) - set(stock))
        extra = sorted(set(stock) - set(expected))
        fail(f"Stock fKDA parity failed for {run_id}; missing={missing}, extra={extra}")
    for gene, row in stock.items():
        record = expected[gene]
        original = record["original"]
        exact = (
            as_int(row["BestLayer"]) == original["layer"]
            and as_int(row["q"]) == original["overlap"]
            and as_int(row["m"]) == original["neighborhood"]
            and as_int(row["n"]) == original["non_neighborhood"]
            and as_int(row["k"]) == original["signature_size"]
        )
        numeric = (
            abs(as_float(row["log.P.Value"]) - original["log_p"]) <= 1e-8
            and abs(as_float(row["adj.P.Value"]) - record["original_q"]) <= 1e-8
            and abs(as_float(row["FE"]) - original["fold"]) <= 0.0100001
        )
        stock_overlap_items = sorted(
            item
            for item in str(row.get("Overlap.Items", "")).replace(",", ";").split(";")
            if item and item != NA_TEXT
        )
        overlap_items_match = stock_overlap_items == record["original_overlap_items"]
        if not exact or not numeric or not overlap_items_match:
            fail(f"Stock fKDA numeric parity failed for {run_id}/{gene}")
    return stock


def candidate_annotation_fields(
    symbol: str, annotation: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    row = annotation_row(symbol, annotation)
    return {
        "is_core_mito": bool(row["is_core_mito"]),
        "mito_tier": row.get("mito_tier"),
        "genome_origin": row.get("genome_origin"),
        "is_mtdna_gene": bool(row.get("is_mtdna_gene", False)),
        "mapping_status": row.get("mapping_status"),
    }


def normalize_stock_return(
    slot: dict[str, Any], row: dict[str, str], explicit: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    gene = row["Keydriver"]
    record = explicit[gene]
    return {
        "analysis_id": slot["analysis_id"],
        "query_tier": slot["query_tier"],
        "kda_run_id": slot["kda_run_id"],
        "category_id": slot["category_id"],
        "contrast_id": slot["contrast_id"],
        "broad_cell_type": slot["broad_cell_type"],
        "group_id": slot["group_id"],
        "sex": slot["sex"],
        "apoe_group": slot["apoe_group"],
        "signature_direction": slot["signature_direction"],
        "current_symbol": gene,
        "best_layer": as_int(row["BestLayer"]),
        "query_overlap": as_int(row["q"]),
        "neighborhood_size": as_int(row["m"]),
        "non_neighborhood_size": as_int(row["n"]),
        "signature_size": as_int(row["k"]),
        "fold_enrichment": as_float(row["FE"]),
        "log_p_value": as_float(row["log.P.Value"]),
        "raw_p_value": record["original"]["p"],
        "original_run_q": as_float(row["adj.P.Value"]),
        "is_signature": row.get("is.signature", NA_TEXT),
        "is_root_node": row.get("is.root.node", NA_TEXT),
        "global_key_driver": row.get("global.Keydriver", NA_TEXT),
        "overlap_items": row.get("Overlap.Items", ""),
    }


def execute_slot(
    config: dict[str, Any],
    paths: dict[str, Path],
    phase18: Any,
    annotation: dict[str, dict[str, Any]],
    network_edges: list[tuple[str, str]],
    slot: dict[str, Any],
    query: set[str],
    background: set[str],
    induced_edges: list[tuple[str, str]],
    temp_parent: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if slot["eligibility_status"] != "eligible":
        return [], [], slot
    if query == background:
        fail(f"Effective query equals the complete background for {slot['kda_run_id']}")
    if not query.issubset(background):
        fail(f"Effective query is outside the background for {slot['kda_run_id']}")
    missing_annotation = sorted(background - set(annotation))
    if missing_annotation:
        fail(
            f"Background genes lack Phase 09 annotation for {slot['kda_run_id']}: "
            f"{missing_annotation[:10]}"
        )
    explicit, summary = phase18.reconstruct_run(
        slot, query, background, network_edges, annotation
    )
    n_layers = as_int(config["kda"]["nLayerToTest"])
    outgoing, undirected = attach_original_overlap_items(
        phase18,
        slot["kda_run_id"],
        explicit,
        query,
        background,
        induced_edges,
        n_layers,
    )
    stock_rows: list[dict[str, str]] = []
    stock_by_gene: dict[str, dict[str, str]] = {}
    if explicit:
        stock_rows = run_stock_fkda(
            paths,
            slot["kda_run_id"],
            induced_edges,
            query,
            len(background),
            n_layers,
            temp_parent,
        )
        stock_by_gene = validate_stock_parity(slot["kda_run_id"], explicit, stock_rows)

    non_mt_genes = [
        gene
        for gene in explicit
        if not bool(annotation_row(gene, annotation)["is_core_mito"])
    ]
    non_mt_adjusted = bh_adjust(
        [explicit[gene]["original"]["p"] for gene in non_mt_genes]
    )
    non_mt_q = dict(zip(non_mt_genes, non_mt_adjusted))
    overlap_minimum = as_int(config["candidate_filters"]["minimum_query_overlap"])
    fold_minimum = float(config["candidate_filters"]["minimum_fold_enrichment_exclusive"])
    relaxed_q = float(config["candidate_filters"]["relaxed_non_mt_run_q"])
    strict_q = float(config["candidate_filters"]["strict_non_mt_run_q"])
    target_nodes = {target for _, target in induced_edges}

    test_rows: list[dict[str, Any]] = []
    stock_normalized: list[dict[str, Any]] = []
    for stock_row in stock_rows:
        stock_normalized.append(normalize_stock_return(slot, stock_row, explicit))
    for gene, record in explicit.items():
        original = record["original"]
        ann = candidate_annotation_fields(gene, annotation)
        q_value = non_mt_q.get(gene)
        overlap_pass = original["overlap"] >= overlap_minimum
        fold_pass = original["fold"] is not None and original["fold"] > fold_minimum
        relaxed_q_pass = q_value is not None and q_value <= relaxed_q
        strict_q_pass = q_value is not None and q_value <= strict_q
        stock = stock_by_gene.get(gene, {})
        row = {
            "analysis_id": slot["analysis_id"],
            "query_tier": slot["query_tier"],
            "kda_run_id": slot["kda_run_id"],
            "category_id": slot["category_id"],
            "contrast_id": slot["contrast_id"],
            "broad_cell_type": slot["broad_cell_type"],
            "group_id": slot["group_id"],
            "sex": slot["sex"],
            "apoe_group": slot["apoe_group"],
            "signature_direction": slot["signature_direction"],
            "query_size_tier": slot["query_size_tier"],
            "effective_query_genes": len(query),
            "effective_background_genes": len(background),
            "current_symbol": gene,
            **ann,
            "query_member": gene in query,
            "self_excluded_in_phase18_engine": bool(record["self_excluded"]),
            "best_layer": original["layer"],
            "query_overlap": original["overlap"],
            "neighborhood_size": original["neighborhood"],
            "non_neighborhood_size": original["non_neighborhood"],
            "signature_size": original["signature_size"],
            "fold_enrichment": original["fold"],
            "log_p_value": original["log_p"],
            "raw_p_value": original["p"],
            "original_run_q": record["original_q"],
            "non_mt_run_q": q_value,
            "stock_fkda_q05_return": gene in stock_by_gene,
            "is_root_node": gene not in target_nodes,
            "out_degree": len(outgoing.get(gene, set())),
            "undirected_degree": len(undirected.get(gene, set())),
            "stock_is_signature": stock.get("is.signature"),
            "stock_is_root_node": stock.get("is.root.node"),
            "stock_global_key_driver": stock.get("global.Keydriver"),
            "overlap_items": ";".join(record["original_overlap_items"]),
            "overlap_gate_pass": overlap_pass,
            "fold_enrichment_gate_pass": fold_pass,
            "relaxed_q_gate_pass": relaxed_q_pass,
            "strict_q_gate_pass": strict_q_pass,
            "relaxed_primary_candidate": (
                not ann["is_core_mito"] and overlap_pass and fold_pass and relaxed_q_pass
            ),
            "strict_direct_reference": (
                not ann["is_core_mito"] and overlap_pass and fold_pass and strict_q_pass
            ),
        }
        test_rows.append(row)

    slot["explicit_candidate_tests"] = len(test_rows)
    slot["non_mt_candidate_family_size"] = len(non_mt_genes)
    slot["stock_significant_returns"] = len(stock_rows)
    slot["stock_parity_checked"] = True
    slot["stock_parity_rows_validated"] = len(stock_rows)
    slot["relaxed_non_mt_candidates"] = sum(
        bool(row["relaxed_primary_candidate"]) for row in test_rows
    )
    slot["strict_non_mt_candidates"] = sum(
        bool(row["strict_direct_reference"]) for row in test_rows
    )
    if not explicit:
        slot["terminal_status"] = "completed_no_testable_candidates"
    elif stock_rows:
        slot["terminal_status"] = "completed_significant"
    else:
        slot["terminal_status"] = "completed_no_significant"
    if summary["explicit_candidates"] != len(test_rows):
        fail(f"Explicit-candidate summary drift for {slot['kda_run_id']}")
    return test_rows, stock_normalized, slot


def execute_all_tiers(
    config: dict[str, Any],
    paths: dict[str, Path],
    phase18: Any,
    annotation: dict[str, dict[str, Any]],
    network_data: dict[str, dict[str, Any]],
    manifests: dict[str, list[dict[str, Any]]],
    run_context: dict[str, tuple[set[str], set[str], list[tuple[str, str]]]],
    temp_parent: Path,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    tests_by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stock_by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tier in config["scope"]["query_tiers"]:
        for index, slot in enumerate(manifests[tier]):
            if slot["eligibility_status"] != "eligible":
                continue
            query, background, induced = run_context[slot["kda_run_id"]]
            try:
                tests, stock, updated = execute_slot(
                    config,
                    paths,
                    phase18,
                    annotation,
                    network_data[slot["broad_cell_type"]]["edges"],
                    slot,
                    query,
                    background,
                    induced,
                    temp_parent,
                )
            except Exception as error:
                slot["terminal_status"] = "failed"
                slot["message"] = str(error)
                raise
            manifests[tier][index] = updated
            tests_by_tier[tier].extend(tests)
            stock_by_tier[tier].extend(stock)
            print(
                f"{tier}: {slot['kda_run_id']} -> {slot['terminal_status']} "
                f"({len(query)} query, {len(tests)} tests, "
                f"{slot['relaxed_non_mt_candidates']} relaxed candidates)",
                flush=True,
            )
    return dict(tests_by_tier), dict(stock_by_tier)


def rank_primary_candidates(
    config: dict[str, Any], primary_tests: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in primary_tests:
        if row["relaxed_primary_candidate"]:
            key = (row["broad_cell_type"], row["group_id"], row["signature_direction"])
            groups[key].append(dict(row))
    ranked: list[dict[str, Any]] = []
    top10 = as_int(config["candidate_filters"]["top10_limit"])
    top5 = as_int(config["candidate_filters"]["top5_limit"])
    for key in sorted(groups):
        rows = groups[key]
        rows.sort(
            key=lambda row: (
                float(row["non_mt_run_q"]),
                float(row["raw_p_value"]),
                -as_int(row["query_overlap"]),
                -float(row["fold_enrichment"]),
                row["current_symbol"],
            )
        )
        for rank, row in enumerate(rows, start=1):
            row["direction_rank"] = rank
            row["top10_display"] = rank <= top10
            row["top5_display"] = rank <= top5
            ranked.append(row)
    return ranked


def build_signature_rows(
    primary_slots: list[dict[str, Any]],
    queries: dict[tuple[str, str, str, str], set[str]],
    run_context: dict[str, tuple[set[str], set[str], list[tuple[str, str]]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot in primary_slots:
        key = (
            slot["query_tier"],
            slot["broad_cell_type"],
            slot["group_id"],
            slot["signature_direction"],
        )
        provisional = queries.get(key, set())
        effective, _, _ = run_context[slot["kda_run_id"]]
        for gene in sorted(provisional):
            member = gene in effective
            rows.append(
                {
                    "analysis_id": slot["analysis_id"],
                    "kda_run_id": slot["kda_run_id"],
                    "category_id": slot["category_id"],
                    "broad_cell_type": slot["broad_cell_type"],
                    "group_id": slot["group_id"],
                    "signature_direction": slot["signature_direction"],
                    "gene": gene,
                    "effective_member": member,
                    "exclusion_reason": "" if member else "not_in_effective_background",
                }
            )
    return rows


def build_background_rows(
    primary_slots: list[dict[str, Any]],
    run_context: dict[str, tuple[set[str], set[str], list[tuple[str, str]]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot in primary_slots:
        _, background, _ = run_context[slot["kda_run_id"]]
        for gene in sorted(background):
            rows.append(
                {
                    "analysis_id": slot["analysis_id"],
                    "kda_run_id": slot["kda_run_id"],
                    "category_id": slot["category_id"],
                    "broad_cell_type": slot["broad_cell_type"],
                    "group_id": slot["group_id"],
                    "signature_direction": slot["signature_direction"],
                    "gene": gene,
                }
            )
    return rows


def build_mapping_collision_rows(
    config: dict[str, Any],
    categories: list[dict[str, Any]],
    symbol_sources: dict[tuple[str, str], dict[str, set[str]]],
) -> list[dict[str, Any]]:
    """Preserve every many-to-one source-gene mapping used for DEG sets."""
    rows: list[dict[str, Any]] = []
    for category in categories:
        key = (category["broad_cell_type"], category["group_id"])
        for mapped_gene, source_genes in sorted(symbol_sources.get(key, {}).items()):
            if len(source_genes) <= 1:
                continue
            ordered_sources = sorted(source_genes)
            rows.append(
                {
                    "analysis_id": config["analysis"]["analysis_id"],
                    "category_id": category["category_id"],
                    "contrast_id": category["contrast_id"],
                    "broad_cell_type": category["broad_cell_type"],
                    "group_id": category["group_id"],
                    "mapped_gene": mapped_gene,
                    "source_gene_count": len(ordered_sources),
                    "collapsed_rows": len(ordered_sources) - 1,
                    "source_genes": ";".join(ordered_sources),
                }
            )
    return rows


def build_category_outputs(
    categories: list[dict[str, Any]],
    primary_slots: list[dict[str, Any]],
    ranked_candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    slots_by_category: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for slot in primary_slots:
        slots_by_category[slot["category_id"]][slot["signature_direction"]] = slot
    candidates_by_category_direction: dict[
        tuple[str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in ranked_candidates:
        candidates_by_category_direction[
            (row["category_id"], row["signature_direction"])
        ].append(row)

    manifest_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for category in categories:
        category_id = category["category_id"]
        direction_slots = slots_by_category[category_id]
        up = direction_slots["AD_up_mito"]
        down = direction_slots["AD_down_mito"]
        total_candidates = up["relaxed_non_mt_candidates"] + down["relaxed_non_mt_candidates"]
        eligible_directions = sum(
            slot["eligibility_status"] == "eligible" for slot in (up, down)
        )
        failed_directions = sum(slot["terminal_status"] == "failed" for slot in (up, down))
        if category["source_terminal_status"] != "validated_complete":
            category_status = "source_contrast_not_estimable"
        elif eligible_directions == 0:
            category_status = "no_eligible_direction"
        elif failed_directions:
            category_status = "kda_failed"
        elif total_candidates:
            category_status = "completed_with_candidate"
        else:
            category_status = "completed_no_selected_candidate"
        common = {
            "analysis_id": up["analysis_id"],
            "manifest_row": as_int(category["manifest_row"]),
            "category_id": category_id,
            "contrast_id": category["contrast_id"],
            "broad_cell_type": category["broad_cell_type"],
            "group_id": category["group_id"],
            "sex": category["sex"],
            "apoe_group": category["apoe_group"],
            "source_terminal_status": category["source_terminal_status"],
            "source_message": category["source_message"],
            "donors_ad": as_int(category["donors_ad"]),
            "donors_nci": as_int(category["donors_nci"]),
            "up_eligibility_status": up["eligibility_status"],
            "up_effective_query_genes": up["effective_query_genes"],
            "up_terminal_status": up["terminal_status"],
            "up_relaxed_candidates": up["relaxed_non_mt_candidates"],
            "down_eligibility_status": down["eligibility_status"],
            "down_effective_query_genes": down["effective_query_genes"],
            "down_terminal_status": down["terminal_status"],
            "down_relaxed_candidates": down["relaxed_non_mt_candidates"],
            "eligible_direction_count": eligible_directions,
            "completed_direction_count": sum(
                slot["terminal_status"].startswith("completed") for slot in (up, down)
            ),
            "failed_direction_count": failed_directions,
            "relaxed_candidate_rows": total_candidates,
            "category_status": category_status,
        }
        manifest_rows.append(common)
        up_candidates = candidates_by_category_direction.get((category_id, "AD_up_mito"), [])
        down_candidates = candidates_by_category_direction.get((category_id, "AD_down_mito"), [])
        summary_rows.append(
            {
                **common,
                "up_top5_genes": ";".join(
                    row["current_symbol"] for row in up_candidates if row["top5_display"]
                ),
                "up_top5_non_mt_run_q": ";".join(
                    str(row["non_mt_run_q"]) for row in up_candidates if row["top5_display"]
                ),
                "up_all_candidate_genes": ";".join(
                    row["current_symbol"] for row in up_candidates
                ),
                "up_all_non_mt_run_q": ";".join(
                    str(row["non_mt_run_q"]) for row in up_candidates
                ),
                "down_top5_genes": ";".join(
                    row["current_symbol"] for row in down_candidates if row["top5_display"]
                ),
                "down_top5_non_mt_run_q": ";".join(
                    str(row["non_mt_run_q"])
                    for row in down_candidates
                    if row["top5_display"]
                ),
                "down_all_candidate_genes": ";".join(
                    row["current_symbol"] for row in down_candidates
                ),
                "down_all_non_mt_run_q": ";".join(
                    str(row["non_mt_run_q"]) for row in down_candidates
                ),
                "descriptive_union_genes": ";".join(
                    sorted(
                        {
                            row["current_symbol"]
                            for row in [*up_candidates, *down_candidates]
                        }
                    )
                ),
                "inferential_note": "directions_retained_separately_no_combined_q",
            }
        )
    return manifest_rows, summary_rows


def build_funnel_rows(
    config: dict[str, Any],
    manifests: dict[str, list[dict[str, Any]]],
    primary_tests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    minimum = as_int(config["eligibility"]["minimum_effective_query_genes"])
    phase18_sized = as_int(config["eligibility"]["phase18_sized_query_genes"])
    outcome_order = [
        "source_contrast_not_estimable",
        "no_provisional_query",
        "effective_query_empty_after_background",
        "effective_query_size_1_2",
        "effective_query_size_3_9",
        "effective_query_size_ge10",
    ]
    for tier in config["scope"]["query_tiers"]:
        counts = slot_funnel_counts(manifests[tier], minimum, phase18_sized)
        for order, outcome in enumerate(outcome_order, start=1):
            rows.append(
                {
                    "funnel_scope": "directional_query_slots",
                    "query_tier": tier,
                    "stage_order": order,
                    "stage": outcome,
                    "input_units": 84,
                    "passing_units": counts.get(outcome, 0),
                    "removed_units": 84 - counts.get(outcome, 0),
                    "counting_unit": "directional_kda_slot",
                }
            )

    candidate_steps: list[tuple[str, Any]] = [
        ("all_explicit_candidates", lambda row: True),
        ("non_core_mt_candidates", lambda row: not row["is_core_mito"]),
        (
            "query_overlap_ge2",
            lambda row: not row["is_core_mito"] and row["overlap_gate_pass"],
        ),
        (
            "fold_enrichment_gt1",
            lambda row: not row["is_core_mito"]
            and row["overlap_gate_pass"]
            and row["fold_enrichment_gate_pass"],
        ),
        (
            "non_mt_run_q_le0_10",
            lambda row: row["relaxed_primary_candidate"],
        ),
    ]
    previous = list(primary_tests)
    for order, (stage, criterion) in enumerate(candidate_steps, start=1):
        if order == 1:
            passing = [row for row in primary_tests if criterion(row)]
            input_count = len(primary_tests)
        else:
            passing = [row for row in previous if criterion(row)]
            input_count = len(previous)
        rows.append(
            {
                "funnel_scope": "primary_candidate_selection",
                "query_tier": config["analysis"]["primary_query_tier"],
                "stage_order": order,
                "stage": stage,
                "input_units": input_count,
                "passing_units": len(passing),
                "removed_units": input_count - len(passing),
                "counting_unit": "gene_directional_run_test",
            }
        )
        previous = passing
    strict = [row for row in primary_tests if row["strict_direct_reference"]]
    rows.append(
        {
            "funnel_scope": "independent_reference_gate",
            "query_tier": config["analysis"]["primary_query_tier"],
            "stage_order": 1,
            "stage": "non_mt_run_q_le0_05_with_overlap_and_fe",
            "input_units": len(primary_tests),
            "passing_units": len(strict),
            "removed_units": len(primary_tests) - len(strict),
            "counting_unit": "gene_directional_run_test",
        }
    )
    return rows


def build_checks(
    config: dict[str, Any],
    source_status: dict[str, str],
    source_checks: list[dict[str, str]],
    categories: list[dict[str, Any]],
    manifests: dict[str, list[dict[str, Any]]],
    network_authority: list[dict[str, Any]],
    networkx_disagreements: int,
    queries: dict[tuple[str, str, str, str], set[str]],
    run_context: dict[str, tuple[set[str], set[str], list[tuple[str, str]]]],
    tests_by_tier: dict[str, list[dict[str, Any]]],
    ranked_candidates: list[dict[str, Any]],
    mapping_collision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    primary_tier = config["analysis"]["primary_query_tier"]
    primary_slots = manifests[primary_tier]
    primary_tests = tests_by_tier.get(primary_tier, [])
    add_check(
        checks,
        "phase08_status_validated",
        source_status.get("validation_status"),
        "validated_complete",
        source_status.get("validation_status") == "validated_complete",
    )
    add_check(
        checks,
        "phase08_checks_pass",
        sum(not is_true(row["passed"]) for row in source_checks),
        0,
        all(is_true(row["passed"]) for row in source_checks),
    )
    add_check(checks, "category_count", len(categories), 42, len(categories) == 42)
    category_keys = {(row["broad_cell_type"], row["group_id"]) for row in categories}
    add_check(
        checks,
        "category_keys_unique",
        len(category_keys),
        42,
        len(category_keys) == len(categories) == 42,
    )
    complete_sources = sum(
        row["source_terminal_status"] == "validated_complete" for row in categories
    )
    not_estimable_sources = sum(
        row["source_terminal_status"] == "not_estimable" for row in categories
    )
    add_check(checks, "source_complete_contrasts", complete_sources, 40, complete_sources == 40)
    add_check(
        checks,
        "source_not_estimable_contrasts",
        not_estimable_sources,
        2,
        not_estimable_sources == 2,
    )
    add_check(
        checks,
        "primary_direction_slot_count",
        len(primary_slots),
        84,
        len(primary_slots) == 84,
    )
    add_check(
        checks,
        "primary_direction_ids_unique",
        len({row["kda_run_id"] for row in primary_slots}),
        84,
        len({row["kda_run_id"] for row in primary_slots}) == 84,
    )
    add_check(
        checks,
        "network_count",
        len(network_authority),
        7,
        len(network_authority) == 7,
    )
    add_check(
        checks,
        "networks_are_dags",
        sum(bool(row["is_dag"]) for row in network_authority),
        7,
        all(bool(row["is_dag"]) for row in network_authority),
    )
    add_check(
        checks,
        "networkx_induction_agreement",
        networkx_disagreements,
        0,
        networkx_disagreements == 0,
    )
    relaxed_members = sum(
        len(value) for key, value in queries.items() if key[0] == primary_tier
    )
    relaxed_up = sum(
        len(value)
        for key, value in queries.items()
        if key[0] == primary_tier and key[3] == "AD_up_mito"
    )
    relaxed_down = sum(
        len(value)
        for key, value in queries.items()
        if key[0] == primary_tier and key[3] == "AD_down_mito"
    )
    add_check(checks, "relaxed_query_memberships", relaxed_members, 65, relaxed_members == 65)
    add_check(checks, "relaxed_up_memberships", relaxed_up, 20, relaxed_up == 20)
    add_check(checks, "relaxed_down_memberships", relaxed_down, 45, relaxed_down == 45)
    expected_collision_keys = as_int(
        config["expected_primary"]["mapped_symbol_collision_keys"]
    )
    observed_collapsed_rows = sum(
        as_int(row["collapsed_rows"]) for row in mapping_collision_rows
    )
    expected_collapsed_rows = as_int(
        config["expected_primary"]["mapped_symbol_collapsed_rows"]
    )
    add_check(
        checks,
        "mapped_symbol_collision_keys",
        len(mapping_collision_rows),
        expected_collision_keys,
        len(mapping_collision_rows) == expected_collision_keys,
    )
    add_check(
        checks,
        "mapped_symbol_collapsed_rows",
        observed_collapsed_rows,
        expected_collapsed_rows,
        observed_collapsed_rows == expected_collapsed_rows,
    )

    expected_outcomes = config["expected_primary"]["slot_outcomes"]
    observed_outcomes = Counter(row["eligibility_status"] for row in primary_slots)
    for outcome, expected in expected_outcomes.items():
        observed = observed_outcomes.get(outcome, 0)
        add_check(
            checks,
            f"primary_slot_outcome_{outcome}",
            observed,
            as_int(expected),
            observed == as_int(expected),
        )
    eligible = [row for row in primary_slots if row["eligibility_status"] == "eligible"]
    observed_eligible = {
        (
            row["broad_cell_type"],
            row["group_id"],
            row["signature_direction"],
            as_int(row["effective_query_genes"]),
        )
        for row in eligible
    }
    expected_eligible = {
        (
            row["broad_cell_type"],
            row["group_id"],
            row["signature_direction"],
            as_int(row["effective_query_genes"]),
        )
        for row in config["expected_primary"]["eligible_runs"]
    }
    add_check(
        checks,
        "primary_eligible_runs_exact",
        ";".join("|".join(map(str, row)) for row in sorted(observed_eligible)),
        ";".join("|".join(map(str, row)) for row in sorted(expected_eligible)),
        observed_eligible == expected_eligible,
    )
    query_subset_failures = sum(
        not query.issubset(background)
        for query, background, _ in run_context.values()
    )
    add_check(
        checks,
        "effective_queries_subset_background",
        query_subset_failures,
        0,
        query_subset_failures == 0,
    )
    test_keys = {(row["kda_run_id"], row["current_symbol"]) for row in primary_tests}
    add_check(
        checks,
        "primary_candidate_test_keys_unique",
        len(test_keys),
        len(primary_tests),
        len(test_keys) == len(primary_tests),
    )
    stock_parity_failures = sum(
        is_true(row["stock_fkda_q05_return"])
        != (as_float(row["original_run_q"]) <= 0.05)
        for row in primary_tests
    )
    add_check(
        checks,
        "stock_fkda_return_parity",
        stock_parity_failures,
        0,
        stock_parity_failures == 0,
    )
    non_mt_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary_tests:
        if not row["is_core_mito"]:
            non_mt_groups[row["kda_run_id"]].append(row)
    bh_failures = 0
    for rows in non_mt_groups.values():
        ordered = sorted(rows, key=lambda value: value["current_symbol"])
        expected_q = bh_adjust([as_float(row["raw_p_value"]) for row in ordered])
        for row, expected in zip(ordered, expected_q):
            observed = as_float(row["non_mt_run_q"])
            if expected is None or not math.isclose(observed, expected, rel_tol=0, abs_tol=1e-12):
                bh_failures += 1
    add_check(checks, "non_mt_run_q_values_valid", bh_failures, 0, bh_failures == 0)
    mt_candidate_leaks = sum(row["is_core_mito"] for row in ranked_candidates)
    add_check(checks, "no_core_mt_candidate_leakage", mt_candidate_leaks, 0, mt_candidate_leaks == 0)
    gate_failures = sum(
        not (
            row["overlap_gate_pass"]
            and row["fold_enrichment_gate_pass"]
            and row["relaxed_q_gate_pass"]
        )
        for row in ranked_candidates
    )
    add_check(checks, "all_candidate_gates_pass", gate_failures, 0, gate_failures == 0)
    failed_runs = sum(
        row["terminal_status"] == "failed"
        for tier in manifests.values()
        for row in tier
    )
    add_check(checks, "zero_kda_failures", failed_runs, 0, failed_runs == 0)
    eligible_slots = [
        row
        for tier in manifests.values()
        for row in tier
        if row["eligibility_status"] == "eligible"
    ]
    parity_checked = sum(bool(row.get("stock_parity_checked")) for row in eligible_slots)
    parity_rows = sum(as_int(row.get("stock_parity_rows_validated")) for row in eligible_slots)
    add_check(
        checks,
        "stock_fkda_full_numeric_parity",
        f"{parity_checked} calls; {parity_rows} returned rows",
        f"{len(eligible_slots)} calls; fail-closed numeric comparison",
        parity_checked == len(eligible_slots),
        "All returned rows were compared on key, best layer, counts, log P, BH q, "
        "fold enrichment, and overlap membership during execution.",
    )
    banned = ("acat", "coverage", "supporting_run", "leave_one_fine")
    output_fields = {field.lower() for field in [*PRIMARY_MANIFEST_FIELDS, *TEST_FIELDS]}
    banned_fields = sorted(field for field in output_fields if any(word in field for word in banned))
    add_check(
        checks,
        "no_cross_run_aggregation_fields",
        ";".join(banned_fields),
        "",
        not banned_fields,
    )
    return checks


def write_analysis_outputs(
    config: dict[str, Any],
    config_path: Path,
    output_dir: Path,
    paths: dict[str, Path],
    input_authority: list[dict[str, Any]],
    network_authority: list[dict[str, Any]],
    source_status: dict[str, str],
    categories: list[dict[str, Any]],
    manifests: dict[str, list[dict[str, Any]]],
    signature_rows: list[dict[str, Any]],
    background_rows: list[dict[str, Any]],
    mapping_collision_rows: list[dict[str, Any]],
    tests_by_tier: dict[str, list[dict[str, Any]]],
    stock_by_tier: dict[str, list[dict[str, Any]]],
    ranked_candidates: list[dict[str, Any]],
    category_manifest: list[dict[str, Any]],
    category_summary: list[dict[str, Any]],
    funnel_rows: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> Path:
    if output_dir.exists():
        fail(f"Output directory already exists; refusing to overwrite: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging.", dir=output_dir.parent)
    )
    primary_tier = config["analysis"]["primary_query_tier"]
    primary_tests = sorted(
        tests_by_tier.get(primary_tier, []),
        key=lambda row: (row["kda_run_id"], row["current_symbol"]),
    )
    sensitivity_tests = sorted(
        [row for tier in config["scope"]["query_tiers"] for row in tests_by_tier.get(tier, [])],
        key=lambda row: (
            list(config["scope"]["query_tiers"]).index(row["query_tier"]),
            row["kda_run_id"],
            row["current_symbol"],
        ),
    )
    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda row: (
            row["broad_cell_type"],
            row["group_id"],
            row["signature_direction"],
            as_int(row["direction_rank"]),
        ),
    )
    strict_candidates = [row for row in ranked_candidates if row["strict_direct_reference"]]
    top10 = [row for row in ranked_candidates if row["top10_display"]]
    top5 = [row for row in ranked_candidates if row["top5_display"]]
    stock_primary = sorted(
        stock_by_tier.get(primary_tier, []),
        key=lambda row: (row["kda_run_id"], row["current_symbol"]),
    )

    category_fields = [
        "analysis_id",
        "manifest_row",
        "category_id",
        "contrast_id",
        "broad_cell_type",
        "group_id",
        "sex",
        "apoe_group",
        "source_terminal_status",
        "source_message",
        "donors_ad",
        "donors_nci",
        "up_eligibility_status",
        "up_effective_query_genes",
        "up_terminal_status",
        "up_relaxed_candidates",
        "down_eligibility_status",
        "down_effective_query_genes",
        "down_terminal_status",
        "down_relaxed_candidates",
        "eligible_direction_count",
        "completed_direction_count",
        "failed_direction_count",
        "relaxed_candidate_rows",
        "category_status",
    ]
    summary_fields = category_fields + [
        "up_top5_genes",
        "up_top5_non_mt_run_q",
        "up_all_candidate_genes",
        "up_all_non_mt_run_q",
        "down_top5_genes",
        "down_top5_non_mt_run_q",
        "down_all_candidate_genes",
        "down_all_non_mt_run_q",
        "descriptive_union_genes",
        "inferential_note",
    ]
    stock_fields = [
        "analysis_id",
        "query_tier",
        "kda_run_id",
        "category_id",
        "contrast_id",
        "broad_cell_type",
        "group_id",
        "sex",
        "apoe_group",
        "signature_direction",
        "current_symbol",
        "best_layer",
        "query_overlap",
        "neighborhood_size",
        "non_neighborhood_size",
        "signature_size",
        "fold_enrichment",
        "log_p_value",
        "raw_p_value",
        "original_run_q",
        "is_signature",
        "is_root_node",
        "global_key_driver",
        "overlap_items",
    ]
    try:
        inputs = staging / "00_inputs"
        inputs.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            paths["phase08_directory"] / "00_inputs" / "phase08_broad_deg_config_snapshot.yml",
            inputs / "phase08_broad_config_snapshot.yml",
        )
        shutil.copyfile(config_path, inputs / "phase20_broad_kda_config_snapshot.yml")
        write_tsv(
            inputs / "phase08_broad_input_authority.tsv",
            input_authority,
            [
                "artifact_role",
                "source_path",
                "expected_sha256",
                "observed_sha256",
                "bytes",
                "checksum_pass",
            ],
            INPUT_SCHEMA,
        )
        write_tsv(
            inputs / "network_input_authority.tsv",
            network_authority,
            [
                "network",
                "source_path",
                "expected_sha256",
                "observed_sha256",
                "bytes",
                "nodes",
                "edges",
                "is_dag",
            ],
            NETWORK_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_category_manifest.tsv",
            category_manifest,
            category_fields,
            CATEGORY_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_direction_manifest.tsv",
            manifests[primary_tier],
            PRIMARY_MANIFEST_FIELDS,
            DIRECTION_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_signature_members.tsv.gz",
            signature_rows,
            [
                "analysis_id",
                "kda_run_id",
                "category_id",
                "broad_cell_type",
                "group_id",
                "signature_direction",
                "gene",
                "effective_member",
                "exclusion_reason",
            ],
            SIGNATURE_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_background_members.tsv.gz",
            background_rows,
            [
                "analysis_id",
                "kda_run_id",
                "category_id",
                "broad_cell_type",
                "group_id",
                "signature_direction",
                "gene",
            ],
            BACKGROUND_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_symbol_mapping_collisions.tsv.gz",
            mapping_collision_rows,
            [
                "analysis_id",
                "category_id",
                "contrast_id",
                "broad_cell_type",
                "group_id",
                "mapped_gene",
                "source_gene_count",
                "collapsed_rows",
                "source_genes",
            ],
            COLLISION_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_all_candidate_tests.tsv.gz",
            primary_tests,
            TEST_FIELDS,
            TEST_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_stock_fkda_returns.tsv",
            stock_primary,
            stock_fields,
            STOCK_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_non_mt_candidates.tsv",
            ranked_candidates,
            CANDIDATE_FIELDS,
            CANDIDATE_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_strict_reference.tsv",
            strict_candidates,
            CANDIDATE_FIELDS,
            CANDIDATE_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_top10.tsv",
            top10,
            CANDIDATE_FIELDS,
            CANDIDATE_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_top5_summary.tsv",
            top5,
            CANDIDATE_FIELDS,
            CANDIDATE_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_category_summary.tsv",
            category_summary,
            summary_fields,
            SUMMARY_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_query_tier_sensitivity.tsv.gz",
            sensitivity_tests,
            TEST_FIELDS,
            TEST_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_filter_funnel.tsv",
            funnel_rows,
            [
                "funnel_scope",
                "query_tier",
                "stage_order",
                "stage",
                "input_units",
                "passing_units",
                "removed_units",
                "counting_unit",
            ],
            FUNNEL_SCHEMA,
        )
        write_tsv(
            staging / "phase20_broad_checks.tsv",
            checks,
            ["check_id", "severity", "observed", "expected", "passed", "detail"],
            CHECK_SCHEMA,
        )

        declared = list(config["outputs"]["declared_files"])
        artifact_exclusions = {
            "phase20_broad_artifacts.tsv",
            "phase20_broad_status.tsv",
        }
        artifacts: list[dict[str, Any]] = []
        for name in declared:
            if name in artifact_exclusions:
                continue
            path = staging / name
            if not path.is_file():
                fail(f"Declared output was not written: {name}")
            artifacts.append(
                {
                    "artifact_role": "phase20_broad_output",
                    "path": name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        write_tsv(
            staging / "phase20_broad_artifacts.tsv",
            artifacts,
            ["artifact_role", "path", "bytes", "sha256"],
            ARTIFACT_SCHEMA,
        )

        executable_by_tier = {
            tier: sum(slot["eligibility_status"] == "eligible" for slot in slots)
            for tier, slots in manifests.items()
        }
        status = {
            "analysis_id": config["analysis"]["analysis_id"],
            "task_mode": config["analysis"]["task_mode"],
            "execution_stage": config["analysis"]["execution_stage"],
            "primary_query_tier": primary_tier,
            "aggregation_method": "none",
            "structural_categories": len(categories),
            "primary_direction_slots": len(manifests[primary_tier]),
            "source_complete_contrasts": sum(
                row["source_terminal_status"] == "validated_complete" for row in categories
            ),
            "source_not_estimable_contrasts": sum(
                row["source_terminal_status"] == "not_estimable" for row in categories
            ),
            "primary_executable_runs": executable_by_tier.get(primary_tier, 0),
            "primary_completed_runs": sum(
                row["terminal_status"].startswith("completed") for row in manifests[primary_tier]
            ),
            "primary_failed_runs": sum(
                row["terminal_status"] == "failed" for row in manifests[primary_tier]
            ),
            "primary_explicit_candidate_tests": len(primary_tests),
            "primary_stock_significant_returns": len(stock_primary),
            "relaxed_non_mt_candidates": len(ranked_candidates),
            "strict_non_mt_candidates": len(strict_candidates),
            "strict_query_executable_runs": executable_by_tier.get("strict", 0),
            "relaxed_query_executable_runs": executable_by_tier.get("relaxed", 0),
            "exploratory_query_executable_runs": executable_by_tier.get("exploratory", 0),
            "blocking_checks": sum(row["severity"] == "error" for row in checks),
            "failed_checks": sum(
                row["severity"] == "error" and not bool(row["passed"]) for row in checks
            ),
            "scientific_config_sha256": sha256_file(config_path),
            "scientific_script_sha256": sha256_file(Path(__file__).resolve()),
            "complete_evidence_engine_sha256": sha256_file(paths["complete_evidence_engine"]),
            "fkda_source_sha256": sha256_file(paths["fkda_source"]),
            "fkda_parity_helper_sha256": sha256_file(paths["fkda_parity_helper"]),
            "python_version": sys.version.split()[0],
            "networkx_version": nx.__version__,
            "scipy_version": scipy.__version__,
            "source_release_timestamp_utc": source_status.get("timestamp_utc"),
            "git_revision": git_revision(),
            "validation_status": config["outputs"]["validation_status"],
        }
        status_fields = list(status)
        write_tsv(
            staging / "phase20_broad_status.tsv",
            [status],
            status_fields,
            STATUS_SCHEMA,
        )
        for name in declared:
            if not (staging / name).is_file():
                fail(f"Final declared output is missing: {name}")
        failed_checks = [
            row
            for row in checks
            if row["severity"] == "error" and not bool(row["passed"])
        ]
        if failed_checks:
            fail(f"Blocking validation checks failed: {[row['check_id'] for row in failed_checks]}")
        staging.replace(output_dir)
        return output_dir
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def execute_analysis(config_path: Path, output_override: Path | None = None) -> Path:
    config_path = project_path(config_path)
    config = load_config(config_path)
    output_dir = (
        output_override.resolve()
        if output_override is not None
        else project_path(config["paths"]["output_directory"])
    )
    paths, input_authority = validate_frozen_inputs(config, config_path)
    source_status, source_checks, contrast_status = validate_source_release(
        config,
        paths["phase08_directory"],
        paths["phase09_status"],
        paths["phase09_checks"],
    )
    phase18 = load_python_module(
        paths["complete_evidence_engine"], "phase18_complete_evidence_for_broad_kda"
    )
    annotation, annotation_conflicts = load_complete_annotation(
        paths["phase09_annotation"], phase18
    )
    if annotation_conflicts:
        fail(f"Phase 09 current-symbol annotation conflicts: {annotation_conflicts[:10]}")
    categories = load_categories(config, paths["phase08_directory"], contrast_status)
    tested, result_rows, symbol_sources = load_tested_gene_sets(paths["phase08_directory"])
    queries, query_input_rows = load_query_sets(config, paths["phase08_directory"])
    network_data, network_authority = load_networks(config, paths["phase12_config"], phase18)
    manifests, run_context, networkx_disagreements = build_slot_manifests(
        config,
        categories,
        tested,
        result_rows,
        symbol_sources,
        queries,
        query_input_rows,
        network_data,
    )
    validate_expected_funnels(config, manifests)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="phase20_broad_kda_runtime_", dir=output_dir.parent
    ) as runtime_temp:
        tests_by_tier, stock_by_tier = execute_all_tiers(
            config,
            paths,
            phase18,
            annotation,
            network_data,
            manifests,
            run_context,
            Path(runtime_temp),
        )
    primary_tier = config["analysis"]["primary_query_tier"]
    primary_slots = manifests[primary_tier]
    ranked_candidates = rank_primary_candidates(
        config, tests_by_tier.get(primary_tier, [])
    )
    signature_rows = build_signature_rows(primary_slots, queries, run_context)
    background_rows = build_background_rows(primary_slots, run_context)
    mapping_collision_rows = build_mapping_collision_rows(
        config, categories, symbol_sources
    )
    category_manifest, category_summary = build_category_outputs(
        categories, primary_slots, ranked_candidates
    )
    funnel_rows = build_funnel_rows(
        config, manifests, tests_by_tier.get(primary_tier, [])
    )
    checks = build_checks(
        config,
        source_status,
        source_checks,
        categories,
        manifests,
        network_authority,
        networkx_disagreements,
        queries,
        run_context,
        tests_by_tier,
        ranked_candidates,
        mapping_collision_rows,
    )
    return write_analysis_outputs(
        config,
        config_path,
        output_dir,
        paths,
        input_authority,
        network_authority,
        source_status,
        categories,
        manifests,
        signature_rows,
        background_rows,
        mapping_collision_rows,
        tests_by_tier,
        stock_by_tier,
        ranked_candidates,
        category_manifest,
        category_summary,
        funnel_rows,
        checks,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = execute_analysis(
        Path(args.config), Path(args.output_dir) if args.output_dir else None
    )
    status = read_tsv(output / "phase20_broad_status.tsv")[0]
    print(
        "Phase 20 broad direct KDA complete: "
        f"{status['primary_executable_runs']} primary calls, "
        f"{status['primary_explicit_candidate_tests']} explicit tests, "
        f"{status['relaxed_non_mt_candidates']} relaxed non-MT candidates; "
        f"status={status['validation_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
