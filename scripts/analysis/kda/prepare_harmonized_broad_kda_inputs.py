#!/usr/bin/env python3
"""Freeze direct-broad mitochondrial KDA inputs for ROSMAP or SEA-AD."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "config" / "harmonized_broad_kda.yml"
TRUE_VALUES = {"true", "t", "1", "yes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cohort", required=True, choices=("rosmap", "seaad"))
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def truth(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_members(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(set(values)):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def repo_path(value: str | Path, must_exist: bool = True) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        fail(f"Path must be repository-relative without '..': {raw}")
    path = (ROOT / raw).resolve(strict=must_exist)
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Path escapes repository: {path}") from exc
    return path


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_revision() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def deterministic_tsv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    if path.name.endswith(".gz"):
        with temporary.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as handle:
                    frame.to_csv(handle, sep="\t", index=False, na_rep="NA")
    else:
        frame.to_csv(temporary, sep="\t", index=False, na_rep="NA")
    os.replace(temporary, path)


def read_tsv(path: Path, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", keep_default_na=False, low_memory=False, **kwargs)


def add_authority(rows: list[dict[str, Any]], role: str, path: Path) -> str:
    observed = sha256_file(path)
    rows.append(
        {
            "schema_version": "harmonized_broad_kda_input_authority_v1",
            "role": role,
            "path": relative(path),
            "bytes": path.stat().st_size,
            "sha256": observed,
        }
    )
    return observed


def read_network(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_csv(
        path,
        sep="\t",
        header=None,
        usecols=[0, 1],
        names=["source", "target"],
        dtype=str,
        keep_default_na=False,
    )
    raw_rows = len(raw)
    usable = raw.loc[
        raw["source"].ne("")
        & raw["target"].ne("")
        & raw["source"].ne(raw["target"])
    ].copy()
    self_edges = raw_rows - len(raw.loc[raw["source"].ne("") & raw["target"].ne("") & raw["source"].ne(raw["target"])])
    before_dedup = len(usable)
    usable = usable.drop_duplicates().reset_index(drop=True)
    graph = nx.DiGraph()
    graph.add_edges_from(usable.itertuples(index=False, name=None))
    metrics = {
        "raw_edges": raw_rows,
        "usable_edges": len(usable),
        "duplicate_edges_removed": before_dedup - len(usable),
        "blank_or_self_edges_removed": self_edges,
        "nodes": graph.number_of_nodes(),
        "is_directed_acyclic_graph": nx.is_directed_acyclic_graph(graph),
        "weak_components": nx.number_weakly_connected_components(graph),
    }
    if usable.empty:
        fail(f"Network contains no usable edges: {path}")
    return usable, metrics


def annotation_identity(
    path: Path, symbol_col: str, core_col: str, cohort: str
) -> tuple[pd.DataFrame, dict[str, bool], set[str]]:
    frame = read_tsv(path, usecols=[symbol_col, core_col])
    frame[symbol_col] = frame[symbol_col].astype(str).str.strip()
    frame = frame.loc[frame[symbol_col].ne("") & frame[symbol_col].ne("NA")].copy()
    frame["core"] = frame[core_col].map(truth)
    rows: list[dict[str, Any]] = []
    identity: dict[str, bool] = {}
    conflicts: set[str] = set()
    for symbol, group in frame.groupby(symbol_col, sort=True):
        flags = sorted(set(bool(x) for x in group["core"]))
        conflict = len(flags) != 1
        if conflict:
            conflicts.add(symbol)
        else:
            identity[symbol] = flags[0]
        rows.append(
            {
                "schema_version": "harmonized_broad_kda_core_mito_identity_v1",
                "cohort": cohort,
                "gene": symbol,
                "source_rows": len(group),
                "is_core_mito": flags[0] if not conflict else pd.NA,
                "identity_conflict": conflict,
                "kda_eligible_identity": not conflict,
            }
        )
    return pd.DataFrame(rows), identity, conflicts


def source_contrasts(
    cohort: str, cfg: dict[str, Any], status: pd.DataFrame
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if cohort == "rosmap":
        for row in status.itertuples(index=False):
            complete = row.terminal_status == "validated_complete"
            result_path = repo_path(
                Path(cfg["result_directory"])
                / f"{row.broad_cell_type}__{row.group_id}.broad_deg.tsv.gz",
                must_exist=complete,
            )
            output.append(
                {
                    "contrast_slot": int(row.manifest_row),
                    "contrast_id": row.contrast_id,
                    "broad_cell_type": row.broad_cell_type,
                    "group_id": row.group_id,
                    "sex": row.sex,
                    "apoe_group": row.apoe_group,
                    "n_case_donors": int(row.donors_ad),
                    "n_reference_donors": int(row.donors_nci),
                    "source_terminal_status": "completed" if complete else "source_not_estimable",
                    "source_terminal_reason": "" if complete else str(row.message or "not_estimable"),
                    "tested_feature_count": int(row.genes_returned) if complete else 0,
                    "result_path": result_path if complete else None,
                    "registered_result_sha256": "",
                }
            )
    else:
        for row in status.itertuples(index=False):
            complete = row.terminal_status == "completed"
            result_path = repo_path(row.result_path, must_exist=True) if complete else None
            output.append(
                {
                    "contrast_slot": int(row.contrast_slot),
                    "contrast_id": row.contrast_id,
                    "broad_cell_type": row.broad_network,
                    "group_id": row.signature_group,
                    "sex": row.sex,
                    "apoe_group": row.apoe_group,
                    "n_case_donors": int(row.n_case_donors),
                    "n_reference_donors": int(row.n_reference_donors),
                    "source_terminal_status": "completed" if complete else "source_not_estimable",
                    "source_terminal_reason": "" if complete else str(row.terminal_reason),
                    "tested_feature_count": int(row.tested_feature_count) if complete else 0,
                    "result_path": result_path,
                    "registered_result_sha256": str(row.result_sha256) if complete else "",
                }
            )
    return sorted(output, key=lambda row: row["contrast_slot"])


def main() -> int:
    args = parse_args()
    started = utc_now()
    config_path = args.config.resolve(strict=True)
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    cfg = config["cohorts"][args.cohort]
    scope = config["scope"]
    query_cfg = config["query"]
    output_dir = repo_path(cfg["input_directory"], must_exist=False)
    if output_dir.exists() and any(output_dir.iterdir()):
        fail(f"Refusing to overwrite nonempty input release: {output_dir}")

    authority: list[dict[str, Any]] = []
    add_authority(authority, "configuration", config_path)
    add_authority(authority, "prepare_script", repo_path(config["implementation"]["prepare_script"]))
    add_authority(authority, "run_script", repo_path(config["implementation"]["run_script"]))
    fkda_path = repo_path(config["kda"]["source"])
    fkda_hash = add_authority(authority, "fkda_source", fkda_path)
    if fkda_hash != config["kda"]["source_sha256"]:
        fail("fKDA source checksum differs from the frozen configuration")
    source_status_path = repo_path(cfg["source_status"])
    contrast_status_path = repo_path(cfg["contrast_status"])
    add_authority(authority, "source_status", source_status_path)
    add_authority(authority, "contrast_status", contrast_status_path)
    annotation_path = repo_path(cfg["annotation"])
    add_authority(authority, "gene_annotation", annotation_path)
    network_config_path = repo_path(cfg["network_config"])
    add_authority(authority, "network_config", network_config_path)
    if cfg.get("combined_results"):
        add_authority(authority, "combined_deg_release", repo_path(cfg["combined_results"]))
    if cfg.get("network_release_manifest"):
        add_authority(authority, "network_release_manifest", repo_path(cfg["network_release_manifest"]))

    source_status = read_tsv(source_status_path)
    if len(source_status) != 1 or source_status.iloc[0]["validation_status"] != "validated_complete":
        fail(f"{args.cohort} source release is not validated_complete")
    status = read_tsv(contrast_status_path)
    contrasts = source_contrasts(args.cohort, cfg, status)
    expected_cells = list(scope["broad_cell_types"])
    expected_groups = [item["group_id"] for item in scope["groups"]]
    expected_pairs = {(cell, group) for cell in expected_cells for group in expected_groups}
    observed_pairs = {(row["broad_cell_type"], row["group_id"]) for row in contrasts}

    annotation_table, core_identity, identity_conflicts = annotation_identity(
        annotation_path,
        cfg["annotation_columns"]["symbol"],
        cfg["annotation_columns"]["core_mito"],
        args.cohort,
    )

    network_frames: dict[str, pd.DataFrame] = {}
    network_rows: list[dict[str, Any]] = []
    network_hash_matches = True
    network_dags = True
    for cell in expected_cells:
        item = cfg["networks"][cell]
        path = repo_path(item["path"])
        observed_hash = add_authority(authority, f"network::{cell}", path)
        frame, metrics = read_network(path)
        hash_match = observed_hash == item["sha256"]
        network_hash_matches = network_hash_matches and hash_match
        network_dags = network_dags and bool(metrics["is_directed_acyclic_graph"])
        network_frames[cell] = frame
        network_rows.append(
            {
                "schema_version": "harmonized_broad_kda_network_identity_v1",
                "cohort": args.cohort,
                "broad_cell_type": cell,
                "network_path": relative(path),
                "network_sha256": observed_hash,
                "configured_sha256": item["sha256"],
                "checksum_match": hash_match,
                "release_mode": item["release_mode"],
                "exploratory": item["release_mode"] == "encode_only_exploratory",
                **metrics,
            }
        )

    columns = cfg["result_columns"]
    caches: dict[str, dict[str, Any]] = {}
    result_annotation_disagreements = 0
    result_hash_matches = True
    donor_gate_pass = True
    result_authority_rows = 0
    for contrast in contrasts:
        if contrast["source_terminal_status"] != "completed":
            continue
        result_path = contrast["result_path"]
        assert isinstance(result_path, Path)
        observed_hash = add_authority(authority, f"source_result::{contrast['contrast_id']}", result_path)
        result_authority_rows += 1
        registered_hash = contrast["registered_result_sha256"]
        if registered_hash and registered_hash != observed_hash:
            result_hash_matches = False
        contrast["result_sha256"] = observed_hash
        donor_gate_pass = donor_gate_pass and min(
            contrast["n_case_donors"], contrast["n_reference_donors"]
        ) >= int(cfg["minimum_donors_per_arm"])
        table = read_tsv(
            result_path,
            usecols=[columns["symbol"], columns["core_mito"], columns["fdr"], columns["logfc"]],
        )
        symbol = table[columns["symbol"]].astype(str).str.strip()
        valid = symbol.ne("") & symbol.ne("NA") & symbol.ne("nan")
        table = table.loc[valid].copy()
        table["gene"] = symbol.loc[valid]
        table["result_core"] = table[columns["core_mito"]].map(truth)
        table["identity_core"] = table["gene"].map(core_identity)
        disagreement = table["identity_core"].notna() & table["result_core"].ne(table["identity_core"])
        result_annotation_disagreements += int(disagreement.sum())
        tested = set(table["gene"])
        network = network_frames[contrast["broad_cell_type"]]
        induced = network.loc[
            network["source"].isin(tested) & network["target"].isin(tested)
        ].copy()
        background = set(induced["source"]).union(induced["target"])
        fdr = pd.to_numeric(table[columns["fdr"]], errors="coerce")
        logfc = pd.to_numeric(table[columns["logfc"]], errors="coerce")
        primary = (
            table["result_core"]
            & table["identity_core"].eq(True)
            & ~table["gene"].isin(identity_conflicts)
            & fdr.lt(float(query_cfg["fdr_threshold_exclusive"]))
        )
        up = set(table.loc[primary & logfc.gt(0), "gene"])
        down = set(table.loc[primary & logfc.lt(0), "gene"])
        caches[contrast["contrast_id"]] = {
            "tested": tested,
            "background": background,
            "induced_edges": len(induced),
            "up": up,
            "down": down,
            "both": up.union(down),
            "result_rows": len(table),
        }

    contrast_rows: list[dict[str, Any]] = []
    query_manifest_rows: list[dict[str, Any]] = []
    query_member_rows: list[dict[str, Any]] = []
    background_rows: list[dict[str, Any]] = []
    minimum = int(query_cfg["minimum_effective_query_genes"])
    warning = int(query_cfg["small_query_warning_below"])
    network_by_cell = {row["broad_cell_type"]: row for row in network_rows}
    query_slot = 0
    for contrast in contrasts:
        result_path = contrast.get("result_path")
        contrast_rows.append(
            {
                "schema_version": "harmonized_broad_kda_contrast_manifest_v1",
                "cohort": args.cohort,
                "contrast_slot": contrast["contrast_slot"],
                "contrast_id": contrast["contrast_id"],
                "broad_cell_type": contrast["broad_cell_type"],
                "group_id": contrast["group_id"],
                "sex": contrast["sex"],
                "apoe_group": contrast["apoe_group"],
                "case_phenotype": cfg["case_phenotype"],
                "reference_phenotype": cfg["reference_phenotype"],
                "coefficient_direction": cfg["coefficient_direction"],
                "n_case_donors": contrast["n_case_donors"],
                "n_reference_donors": contrast["n_reference_donors"],
                "minimum_donors_per_arm": cfg["minimum_donors_per_arm"],
                "source_terminal_status": contrast["source_terminal_status"],
                "source_terminal_reason": contrast["source_terminal_reason"],
                "tested_feature_count": contrast["tested_feature_count"],
                "result_path": relative(result_path) if isinstance(result_path, Path) else "",
                "result_sha256": contrast.get("result_sha256", ""),
            }
        )
        for query_mode in scope["query_modes"]:
            query_slot += 1
            mode = query_mode["name"]
            run_id = f"{args.cohort}__{contrast['broad_cell_type']}__{contrast['group_id']}__{mode}"
            network_meta = network_by_cell[contrast["broad_cell_type"]]
            candidate: set[str] = set()
            effective: set[str] = set()
            background: set[str] = set()
            tested_count: Any = pd.NA
            induced_edges: Any = pd.NA
            terminal = "source_not_estimable"
            if contrast["source_terminal_status"] == "completed":
                cache = caches[contrast["contrast_id"]]
                candidate = cache["both"]
                background = cache["background"]
                effective = candidate.intersection(background)
                tested_count = len(cache["tested"])
                induced_edges = cache["induced_edges"]
                if not candidate:
                    terminal = "query_empty"
                elif not effective:
                    terminal = "effective_query_empty"
                elif len(effective) < minimum:
                    terminal = "effective_query_below_minimum"
                else:
                    terminal = "eligible_small_query" if len(effective) < warning else "eligible"
            execute = terminal in {"eligible_small_query", "eligible"}
            if execute:
                for gene in sorted(candidate):
                    query_member_rows.append(
                        {
                            "schema_version": "harmonized_broad_kda_query_members_v1",
                            "cohort": args.cohort,
                            "kda_run_id": run_id,
                            "gene": gene,
                            "in_upregulated_query": gene in cache["up"],
                            "in_downregulated_query": gene in cache["down"],
                            "effective_member": gene in effective,
                            "exclusion_reason": "" if gene in effective else "not_in_effective_background",
                        }
                    )
                for gene in sorted(background):
                    background_rows.append(
                        {
                            "schema_version": "harmonized_broad_kda_background_members_v1",
                            "cohort": args.cohort,
                            "kda_run_id": run_id,
                            "gene": gene,
                        }
                    )
            query_manifest_rows.append(
                {
                    "schema_version": "harmonized_broad_kda_query_manifest_v1",
                    "cohort": args.cohort,
                    "query_slot": query_slot,
                    "query_slot_id": f"{contrast['contrast_id']}::{mode}",
                    "kda_run_id": run_id,
                    "contrast_id": contrast["contrast_id"],
                    "broad_cell_type": contrast["broad_cell_type"],
                    "group_id": contrast["group_id"],
                    "sex": contrast["sex"],
                    "apoe_group": contrast["apoe_group"],
                    "case_phenotype": cfg["case_phenotype"],
                    "reference_phenotype": cfg["reference_phenotype"],
                    "coefficient_direction": cfg["coefficient_direction"],
                    "native_query_mode": cfg["native_query_mode"],
                    "query_mode": mode,
                    "n_case_donors": contrast["n_case_donors"],
                    "n_reference_donors": contrast["n_reference_donors"],
                    "source_terminal_status": contrast["source_terminal_status"],
                    "source_terminal_reason": contrast["source_terminal_reason"],
                    "candidate_query_genes": len(candidate) if contrast["source_terminal_status"] == "completed" else pd.NA,
                    "effective_query_genes": len(effective) if contrast["source_terminal_status"] == "completed" else pd.NA,
                    "exact_tested_genes": tested_count,
                    "effective_background_genes": len(background) if contrast["source_terminal_status"] == "completed" else pd.NA,
                    "induced_network_edges": induced_edges,
                    "query_sha256": sha256_members(effective) if execute else "",
                    "background_sha256": sha256_members(background) if execute else "",
                    "network_path": network_meta["network_path"],
                    "network_sha256": network_meta["network_sha256"],
                    "network_release_mode": network_meta["release_mode"],
                    "exploratory_network": network_meta["exploratory"],
                    "terminal_status": terminal,
                    "execute_kda": execute,
                }
            )

    contrast_frame = pd.DataFrame(contrast_rows)
    query_manifest = pd.DataFrame(query_manifest_rows)
    query_members = pd.DataFrame(query_member_rows, columns=[
        "schema_version", "cohort", "kda_run_id", "gene", "in_upregulated_query",
        "in_downregulated_query", "effective_member", "exclusion_reason"
    ])
    background_members = pd.DataFrame(background_rows, columns=[
        "schema_version", "cohort", "kda_run_id", "gene"
    ])
    attrition = (
        query_manifest.groupby(
            ["source_terminal_status", "terminal_status", "network_release_mode", "exploratory_network"],
            dropna=False,
        )
        .size()
        .rename("query_slots")
        .reset_index()
    )
    attrition.insert(0, "schema_version", "harmonized_broad_kda_query_attrition_v1")
    attrition.insert(1, "cohort", args.cohort)

    completed = int(contrast_frame["source_terminal_status"].eq("completed").sum())
    not_estimable = len(contrast_frame) - completed
    eligible_calls = int(query_manifest["execute_kda"].map(truth).sum())
    checks_data = [
        ("source_release_validated", True, "validated_complete", "validated_complete"),
        ("structural_contrast_count", len(contrast_frame) == 42, len(contrast_frame), 42),
        ("structural_pair_universe", observed_pairs == expected_pairs, len(observed_pairs), len(expected_pairs)),
        ("completed_contrast_count", completed == int(cfg["expected_completed_contrasts"]), completed, cfg["expected_completed_contrasts"]),
        ("not_estimable_contrast_count", not_estimable == int(cfg["expected_not_estimable_contrasts"]), not_estimable, cfg["expected_not_estimable_contrasts"]),
        ("structural_query_count", len(query_manifest) == 42, len(query_manifest), 42),
        ("query_ids_unique", query_manifest["query_slot_id"].is_unique, query_manifest["query_slot_id"].nunique(), len(query_manifest)),
        ("run_ids_unique", query_manifest["kda_run_id"].is_unique, query_manifest["kda_run_id"].nunique(), len(query_manifest)),
        ("completed_source_query_count", int(query_manifest["source_terminal_status"].eq("completed").sum()) == completed, int(query_manifest["source_terminal_status"].eq("completed").sum()), completed),
        ("source_result_authority_count", result_authority_rows == completed, result_authority_rows, completed),
        ("source_result_hashes_match", result_hash_matches, result_hash_matches, True),
        ("donor_eligibility_gate", donor_gate_pass, donor_gate_pass, True),
        ("network_count", len(network_rows) == 7, len(network_rows), 7),
        ("network_hashes_match", network_hash_matches, network_hash_matches, True),
        ("networks_are_directed_acyclic", network_dags, network_dags, True),
        ("annotation_result_agreement", result_annotation_disagreements == 0, result_annotation_disagreements, 0),
        ("query_members_are_signed_union", query_members.empty or (
            query_members["in_upregulated_query"].map(truth)
            | query_members["in_downregulated_query"].map(truth)
        ).all(), True, True),
        ("query_member_keys_unique", not query_members.duplicated(["kda_run_id", "gene"]).any(),
         int(query_members.duplicated(["kda_run_id", "gene"]).sum()), 0),
        ("effective_queries_in_background", all(
            set(query_members.loc[(query_members["kda_run_id"] == run_id) & query_members["effective_member"].map(truth), "gene"]).issubset(
                set(background_members.loc[background_members["kda_run_id"] == run_id, "gene"])
            ) for run_id in query_manifest.loc[query_manifest["execute_kda"].map(truth), "kda_run_id"]
        ), True, True),
        ("seaad_vasculature_exploratory", args.cohort != "seaad" or query_manifest.loc[query_manifest["broad_cell_type"].eq("Vasculature_cells"), "exploratory_network"].map(truth).all(), True, True),
    ]
    checks = pd.DataFrame(
        [
            {
                "schema_version": "harmonized_broad_kda_input_checks_v1",
                "cohort": args.cohort,
                "check": name,
                "passed": passed,
                "observed": observed,
                "expected": expected,
            }
            for name, passed, observed, expected in checks_data
        ]
    )
    failed = checks.loc[~checks["passed"].map(truth), "check"].tolist()
    if failed:
        fail(f"Blocking input checks failed: {failed}")

    if output_dir.exists():
        output_dir.rmdir()
    stage = output_dir.with_name(f".{output_dir.name}.tmp.{os.getpid()}")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    products = {
        "input_authority.tsv": pd.DataFrame(authority).sort_values(["role", "path"]),
        "contrast_manifest.tsv": contrast_frame,
        "query_manifest.tsv": query_manifest,
        "core_mito_identity.tsv": annotation_table,
        "network_identity.tsv": pd.DataFrame(network_rows),
        "query_attrition.tsv": attrition,
        "query_members.tsv.gz": query_members,
        "background_members.tsv.gz": background_members,
        "checks.tsv": checks,
    }
    for name, frame in products.items():
        deterministic_tsv(frame, stage / name)
    artifact_rows = []
    for order, name in enumerate(products, start=1):
        staged = stage / name
        artifact_rows.append(
            {
                "schema_version": "harmonized_broad_kda_input_artifacts_v1",
                "artifact_order": order,
                "path": relative(output_dir / name),
                "rows": len(products[name]),
                "bytes": staged.stat().st_size,
                "sha256": sha256_file(staged),
            }
        )
    deterministic_tsv(pd.DataFrame(artifact_rows), stage / "artifacts.tsv")
    status_frame = pd.DataFrame(
        [
            {
                "schema_version": "harmonized_broad_kda_input_status_v1",
                "phase": cfg["input_phase"],
                "cohort": args.cohort,
                "validation_status": "validated_complete",
                "failed_checks": 0,
                "structural_contrasts": len(contrast_frame),
                "completed_source_contrasts": completed,
                "source_not_estimable_contrasts": not_estimable,
                "structural_query_slots": len(query_manifest),
                "eligible_kda_calls": eligible_calls,
                "small_query_calls": int(query_manifest["terminal_status"].eq("eligible_small_query").sum()),
                "source_query_members": int(query_manifest["candidate_query_genes"].fillna(0).sum()),
                "effective_query_members": int(query_manifest["effective_query_genes"].fillna(0).sum()),
                "core_identity_conflicts_blocked": len(identity_conflicts),
                "config_sha256": sha256_file(config_path),
                "fkda_source_sha256": fkda_hash,
                "git_revision": git_revision(),
                "started_at_utc": started,
                "completed_at_utc": utc_now(),
            }
        ]
    )
    deterministic_tsv(status_frame, stage / "status.tsv")
    os.replace(stage, output_dir)
    print(
        f"{cfg['input_phase']} validated_complete: {relative(output_dir)}; "
        f"completed_contrasts={completed}; eligible_kda_calls={eligible_calls}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
