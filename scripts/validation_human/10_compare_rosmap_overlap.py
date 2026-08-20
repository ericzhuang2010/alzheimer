#!/usr/bin/env python3
"""VH10D: unblind ROSMAP after SEA-AD freeze and calculate strict overlap."""

from __future__ import annotations

import importlib.util
import math
import os
import shutil
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml
from scipy.stats import hypergeom

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    repo_path,
    sha256_file,
    status_frame,
    utc_now,
    write_artifacts,
)


STRICT_KEY = ["broad_network", "gene", "case_id"]


def truth(value) -> bool:
    return str(value).strip().lower() in {"true", "t", "1", "yes"}


def load_phase18_module(path: Path):
    spec = importlib.util.spec_from_file_location("phase18_key_driver_selection", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Phase 18 module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_validated(directory: Path, project_root: Path) -> pd.DataFrame:
    status_path = directory / "status.tsv"
    artifacts_path = directory / "artifacts.tsv"
    if not status_path.exists() or not artifacts_path.exists():
        raise FileNotFoundError(f"Validated bundle is incomplete: {directory}")
    status = pd.read_csv(status_path, sep="\t", keep_default_na=False)
    if len(status) != 1 or status.loc[0, "validation_status"] != "validated_complete":
        raise ValueError(f"Bundle is not validated_complete: {directory}")
    artifacts = pd.read_csv(artifacts_path, sep="\t", keep_default_na=False)
    for row in artifacts.itertuples(index=False):
        path = repo_path(project_root, row.path)
        if path.stat().st_size != int(row.bytes) or sha256_file(path) != row.digest_value:
            raise ValueError(f"Bundle artifact mismatch: {path}")
    return status


def one_artifact(project_root: Path, by_role, role: str, phase18) -> Path:
    rows = by_role.get(role, [])
    if len(rows) != 1:
        raise ValueError(f"Expected one Phase 12 artifact for {role}")
    path = repo_path(project_root, rows[0]["path"])
    if sha256_file(path) != rows[0]["sha256"]:
        raise ValueError(f"Phase 12 artifact mismatch for {role}")
    return path


def reconstruct_phase18_universe(project_root: Path, cfg, phase18):
    phase18_config_path = repo_path(
        project_root, cfg["input_authority"]["phase18_config"]["path"]
    )
    with phase18_config_path.open() as handle:
        phase18_config = yaml.safe_load(handle)
    phase12_dir = repo_path(
        project_root, phase18_config["paths"]["phase12_directory"]
    )
    status = phase18.read_tsv(phase12_dir / "kda_status.tsv")
    if len(status) != 1 or status[0].get("validation_status") != "validated_complete":
        raise ValueError("Phase 12 is not validated_complete")
    phase12_checks = phase18.read_tsv(phase12_dir / "kda_checks.tsv")
    if not phase12_checks or not all(
        phase18.is_true(row.get("passed")) for row in phase12_checks
    ):
        raise ValueError("Phase 12 checks did not all pass")

    artifact_by_role = defaultdict(list)
    for row in phase18.iter_tsv(phase12_dir / "kda_artifacts.tsv"):
        artifact_by_role[row["artifact_role"]].append(row)
    annotation_path = one_artifact(
        project_root, artifact_by_role, "phase09_annotation", phase18
    )
    annotation, conflicts = phase18.load_annotation(annotation_path)
    if conflicts:
        raise ValueError(f"Conflicting Phase 09 annotations: {len(conflicts)}")

    groups = set(phase18_config["run_scope"]["groups"])
    directions = set(phase18_config["run_scope"]["directions"])
    structural = [
        row
        for row in phase18.iter_tsv(phase12_dir / "kda_run_manifest.tsv")
        if row["analysis_tier"] == phase18_config["run_scope"]["analysis_tier"]
        and row["signature_group"] in groups
        and row["signature_direction"] in directions
    ]
    if len(structural) != int(
        phase18_config["run_scope"]["expected_structural_slots"]
    ):
        raise ValueError("Phase 18 structural-run count mismatch")
    included = [
        row
        for row in structural
        if row["eligibility_status"] == "eligible"
        and row["terminal_status"].startswith("completed")
        and phase18.as_int(row["effective_query_genes"])
        >= int(phase18_config["run_scope"]["minimum_effective_query_genes"])
    ]
    if len(included) != int(phase18_config["run_scope"]["expected_included_runs"]):
        raise ValueError("Phase 18 included-run count mismatch")
    included_ids = {row["kda_run_id"] for row in included}

    signatures = defaultdict(set)
    for row in phase18.iter_tsv(phase12_dir / "kda_signature_members.tsv.gz"):
        if row["kda_run_id"] in included_ids and phase18.is_true(
            row.get("effective_member")
        ):
            signatures[row["kda_run_id"]].add(row["gene"])
    backgrounds = defaultdict(set)
    for row in phase18.iter_tsv(phase12_dir / "kda_background_members.tsv.gz"):
        if row["kda_run_id"] in included_ids:
            backgrounds[row["kda_run_id"]].add(row["gene"])
    for run in included:
        run_id = run["kda_run_id"]
        if len(signatures[run_id]) != phase18.as_int(run["effective_query_genes"]):
            raise ValueError(f"Phase 18 query-size mismatch: {run_id}")
        if len(backgrounds[run_id]) != phase18.as_int(
            run["effective_background_genes"]
        ):
            raise ValueError(f"Phase 18 background-size mismatch: {run_id}")

    network_order = list(phase18_config["networks"]["order"])
    full_edges = {
        network: phase18.load_network(
            one_artifact(
                project_root, artifact_by_role, f"network_{network}", phase18
            )
        )
        for network in network_order
    }
    published_rows = [
        row
        for row in phase18.iter_tsv(phase12_dir / "kda_results.tsv.gz")
        if row["kda_run_id"] in included_ids
    ]
    published_by_run = defaultdict(dict)
    for row in published_rows:
        published_by_run[row["kda_run_id"]][row["key_driver"]] = row

    explicit_by_run = {}
    for index, run in enumerate(included, start=1):
        run_id = run["kda_run_id"]
        explicit, _ = phase18.reconstruct_run(
            run,
            signatures[run_id],
            backgrounds[run_id],
            full_edges[run["broad_network"]],
            annotation,
        )
        phase18.validate_published_returns(
            run_id, published_by_run.get(run_id, {}), explicit
        )
        explicit_by_run[run_id] = explicit
        if index % 25 == 0 or index == len(included):
            print(
                f"VH10D Phase18 parity reconstructed_runs={index}/{len(included)}",
                flush=True,
            )

    runs_by_network = defaultdict(list)
    for run in included:
        runs_by_network[run["broad_network"]].append(run)
    network_genes = {
        network: sorted(
            set().union(*(backgrounds[run["kda_run_id"]] for run in runs))
        )
        for network, runs in runs_by_network.items()
    }
    aggregate_rows = []
    minimum_coverage = float(phase18_config["filters"]["minimum_coverage"])
    for network in network_order:
        if network not in runs_by_network:
            continue
        rows = phase18.aggregate_network(
            network,
            runs_by_network[network],
            network_genes[network],
            signatures,
            backgrounds,
            explicit_by_run,
            annotation,
            minimum_coverage,
        )
        for row in rows:
            row["missing_as_one_acat_p"] = None
            row["missing_as_one_acat_q"] = None
        aggregate_rows.extend(rows)

    return {
        "structural": structural,
        "included": included,
        "published_rows": published_rows,
        "aggregate_rows": aggregate_rows,
        "network_order": network_order,
    }


def key_set(frame: pd.DataFrame) -> set[tuple[str, str, str]]:
    return set(
        zip(
            frame["broad_network"].astype(str),
            frame["gene"].astype(str),
            frame["case_id"].astype(str),
        )
    )


def main() -> int:
    args = parse_config_cli("VH10D: compare frozen SEA-AD and ROSMAP candidates")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    cfg = config["vh10"]
    analysis = cfg["analysis"]
    phase_root = output_root / cfg["output_directory"]
    input_dir = phase_root / "10a_inputs"
    kda_dir = phase_root / "10b_kda"
    selection_dir = phase_root / "10c_seaad_selection"
    overlap_dir = phase_root / "10d_overlap"
    vh09_dir = output_root / config["vh09"]["output_directory"]

    require_validated(input_dir, project_root)
    require_validated(kda_dir, project_root)
    selection_status = require_validated(selection_dir, project_root)
    freeze = pd.read_csv(
        selection_dir / "seaad_selection_freeze.tsv",
        sep="\t",
        keep_default_na=False,
    )
    if (
        len(freeze) != 1
        or freeze.loc[0, "freeze_status"]
        != "independent_seaad_selection_frozen"
        or truth(freeze.loc[0, "rosmap_candidate_files_read"])
    ):
        raise ValueError("SEA-AD independent selection freeze is invalid")

    vh09_status = require_validated(vh09_dir, project_root)
    if int(vh09_status.loc[0, "selected_units"]) != 47:
        raise ValueError("VH09 selected-unit count is not 47")
    rosmap_selected = pd.read_csv(
        vh09_dir / "phase18_selected_candidate_units.tsv",
        sep="\t",
        keep_default_na=False,
    ).rename(columns={"key_driver": "gene"})
    rosmap_passing = pd.read_csv(
        vh09_dir / "phase18_passing_candidate_units.tsv",
        sep="\t",
        keep_default_na=False,
    ).rename(columns={"key_driver": "gene"})

    phase18_code_item = cfg["input_authority"]["phase18_code"]
    phase18_code = repo_path(project_root, phase18_code_item["path"])
    if sha256_file(phase18_code) != phase18_code_item["sha256"]:
        raise ValueError("Phase 18 code checksum mismatch")
    phase18 = load_phase18_module(phase18_code)
    replay = reconstruct_phase18_universe(project_root, cfg, phase18)
    aggregates = replay["aggregate_rows"]
    replay_passing = [
        row
        for row in aggregates
        if row["terminal_candidate_status"] == "driver_candidate"
    ]
    replay_top5 = pd.DataFrame(
        phase18.top5_rows(aggregates, replay["network_order"])
    )
    replay_selected = replay_top5.loc[
        replay_top5["list_status"].eq("ranked_candidates")
    ].copy()
    replay_selected = replay_selected.rename(columns={"current_symbol": "gene"})

    expected_selected_keys = {
        (
            row.broad_network,
            row.gene,
            row.case_id,
            int(float(row.within_case_rank)),
        )
        for row in rosmap_selected.itertuples(index=False)
    }
    replay_selected_keys = {
        (
            row.broad_network,
            row.gene,
            row.case_id,
            int(float(row.display_rank)),
        )
        for row in replay_selected.itertuples(index=False)
    }
    expected_passing_keys = key_set(rosmap_passing)
    replay_passing_frame = pd.DataFrame(
        [
            {
                "broad_network": row["broad_network"],
                "gene": row["current_symbol"],
                "case_id": row["case_id"],
            }
            for row in replay_passing
        ]
    )
    replay_passing_keys = key_set(replay_passing_frame)

    parity_checks = checks_frame(
        [
            ("phase18_structural_slots", len(replay["structural"]) == 648, len(replay["structural"]), 648, ""),
            ("phase18_included_runs", len(replay["included"]) == 161, len(replay["included"]), 161, ""),
            ("phase18_significant_returns", len(replay["published_rows"]) == 1641, len(replay["published_rows"]), 1641, ""),
            ("phase18_passing_units", len(replay_passing) == 78, len(replay_passing), 78, ""),
            ("phase18_selected_units", len(replay_selected) == 47, len(replay_selected), 47, ""),
            ("phase18_passing_keys_exact", replay_passing_keys == expected_passing_keys, len(replay_passing_keys.symmetric_difference(expected_passing_keys)), 0, ""),
            ("phase18_selected_keys_and_ranks_exact", replay_selected_keys == expected_selected_keys, len(replay_selected_keys.symmetric_difference(expected_selected_keys)), 0, ""),
            ("phase18_acat_regression", phase18.validate_acat_example() <= 1e-9, phase18.validate_acat_example(), "<=1e-9", ""),
        ]
    )
    if not parity_checks["passed"].all():
        failed = parity_checks.loc[~parity_checks["passed"], "check"].tolist()
        raise ValueError(f"Phase 18 conformance replay failed: {failed}")

    shared_networks = set(cfg["network_order"])
    phase18_universe_rows = []
    for row in aggregates:
        if row["broad_network"] not in shared_networks:
            continue
        public = phase18.public_row(row)
        public.pop("missing_as_one_acat_p", None)
        public.pop("missing_as_one_acat_q", None)
        public.pop("stability_assessable_repetitions", None)
        public.pop("stability_nominal_fraction", None)
        public.pop("stability_q_fraction", None)
        public.pop("stability_candidate_fraction", None)
        public.pop("stability_worst_rank", None)
        public["gene"] = public.pop("current_symbol")
        phase18_universe_rows.append(public)
    rosmap_universe = pd.DataFrame(phase18_universe_rows)
    seaad_universe = pd.read_csv(
        selection_dir / "seaad_candidate_summary.tsv.gz",
        sep="\t",
        keep_default_na=False,
        low_memory=False,
    ).rename(columns={"current_symbol": "gene"})
    seaad_top5 = pd.read_csv(
        selection_dir / "seaad_top5.tsv", sep="\t", keep_default_na=False
    )
    seaad_selected = seaad_top5.loc[
        seaad_top5["list_status"].eq("ranked_candidates")
    ].rename(columns={"current_symbol": "gene"})

    for frame in (rosmap_universe, seaad_universe):
        frame["coverage_fraction_numeric"] = pd.to_numeric(
            frame["coverage_fraction"], errors="coerce"
        )
        frame["aggregate_acat_p_numeric"] = pd.to_numeric(
            frame["aggregate_acat_p"], errors="coerce"
        )
    rosmap_assessable = rosmap_universe.loc[
        rosmap_universe["coverage_fraction_numeric"].ge(0.80)
        & rosmap_universe["aggregate_acat_p_numeric"].notna()
    ].copy()
    seaad_assessable = seaad_universe.loc[
        seaad_universe["coverage_fraction_numeric"].ge(0.80)
        & seaad_universe["aggregate_acat_p_numeric"].notna()
    ].copy()
    common_keys = key_set(rosmap_assessable).intersection(key_set(seaad_assessable))

    rosmap_selected_keys = key_set(rosmap_selected)
    seaad_selected_keys = key_set(seaad_selected)
    rosmap_candidate_keys = key_set(rosmap_passing)
    seaad_candidate_frame = seaad_universe.loc[
        seaad_universe["terminal_candidate_status"].eq("driver_candidate")
    ]
    seaad_candidate_keys = key_set(seaad_candidate_frame)
    seaad_rank = {
        (row.broad_network, row.gene, row.case_id): int(float(row.display_rank))
        for row in seaad_selected.itertuples(index=False)
    }
    rosmap_rank = {
        (row.broad_network, row.gene, row.case_id): int(float(row.within_case_rank))
        for row in rosmap_selected.itertuples(index=False)
    }

    overlap_rows = []
    selected_union = rosmap_selected_keys.union(seaad_selected_keys)
    for key in sorted(selected_union):
        in_common = key in common_keys
        rosmap_hit = key in rosmap_selected_keys
        seaad_hit = key in seaad_selected_keys
        if rosmap_hit:
            if not in_common:
                replication_status = "not_testable"
            elif seaad_hit:
                replication_status = "rediscovered_top5"
            elif key in seaad_candidate_keys:
                replication_status = "seaad_driver_candidate_not_top5"
            else:
                replication_status = "tested_not_selected"
        else:
            replication_status = "seaad_only_top5"
        overlap_rows.append(
            {
                "result_tier_id": analysis["result_tier_id"],
                "broad_network": key[0],
                "gene": key[1],
                "case_id": key[2],
                "in_common_assessable_universe": in_common,
                "rosmap_top5": rosmap_hit,
                "rosmap_rank": rosmap_rank.get(key),
                "seaad_top5": seaad_hit,
                "seaad_rank": seaad_rank.get(key),
                "seaad_driver_candidate": key in seaad_candidate_keys,
                "replication_status": replication_status,
            }
        )
    overlap = pd.DataFrame(overlap_rows)

    summary_rows = []
    for network in cfg["network_order"]:
        for case_id in cfg["selection"]["driver_classes"]:
            universe = {
                key
                for key in common_keys
                if key[0] == network and key[2] == case_id
            }
            rosmap_set = rosmap_selected_keys.intersection(universe)
            seaad_set = seaad_selected_keys.intersection(universe)
            shared = rosmap_set.intersection(seaad_set)
            union = rosmap_set.union(seaad_set)
            universe_n = len(universe)
            p_value = (
                float(
                    hypergeom.sf(
                        len(shared) - 1,
                        universe_n,
                        len(rosmap_set),
                        len(seaad_set),
                    )
                )
                if universe_n > 0 and rosmap_set and seaad_set
                else math.nan
            )
            summary_rows.append(
                {
                    "result_tier_id": analysis["result_tier_id"],
                    "broad_network": network,
                    "case_id": case_id,
                    "common_assessable_universe": universe_n,
                    "rosmap_selected_in_universe": len(rosmap_set),
                    "seaad_selected_in_universe": len(seaad_set),
                    "shared_selected_units": len(shared),
                    "seaad_precision": (
                        len(shared) / len(seaad_set) if seaad_set else math.nan
                    ),
                    "rosmap_recall_among_testable": (
                        len(shared) / len(rosmap_set) if rosmap_set else math.nan
                    ),
                    "jaccard_index": (
                        len(shared) / len(union) if union else math.nan
                    ),
                    "hypergeometric_overlap_p": p_value,
                    "shared_genes": "|".join(sorted(key[1] for key in shared)),
                    "rosmap_only_genes": "|".join(
                        sorted(key[1] for key in rosmap_set - shared)
                    ),
                    "seaad_only_genes": "|".join(
                        sorted(key[1] for key in seaad_set - shared)
                    ),
                    "list_status": (
                        "assessable" if universe_n else "not_testable_no_common_universe"
                    ),
                }
            )
    overlap_summary = pd.DataFrame(summary_rows)

    rosmap_gene_set = set(rosmap_selected["gene"])
    seaad_gene_set = set(seaad_selected["gene"])
    gene_rows = []
    for gene in sorted(rosmap_gene_set.union(seaad_gene_set)):
        gene_rows.append(
            {
                "gene": gene,
                "rosmap_top5_any_network_class": gene in rosmap_gene_set,
                "seaad_top5_any_network_class": gene in seaad_gene_set,
                "shared_gene": gene in rosmap_gene_set.intersection(seaad_gene_set),
                "rosmap_network_class_memberships": "|".join(
                    sorted(
                        f"{row.broad_network}:{row.case_id}"
                        for row in rosmap_selected.loc[
                            rosmap_selected["gene"].eq(gene)
                        ].itertuples(index=False)
                    )
                ),
                "seaad_network_class_memberships": "|".join(
                    sorted(
                        f"{row.broad_network}:{row.case_id}"
                        for row in seaad_selected.loc[
                            seaad_selected["gene"].eq(gene)
                        ].itertuples(index=False)
                    )
                ),
            }
        )
    gene_overlap = pd.DataFrame(gene_rows)

    rosmap_selected_testable = rosmap_selected_keys.intersection(common_keys)
    strict_shared = rosmap_selected_keys.intersection(seaad_selected_keys).intersection(
        common_keys
    )
    overlap_checks = checks_frame(
        [
            ("seaad_freeze_precedes_unblinding", not truth(freeze.loc[0, "rosmap_candidate_files_read"]), freeze.loc[0, "rosmap_candidate_files_read"], False, ""),
            ("one_active_result_tier", set(seaad_universe["result_tier_id"]) == {analysis["result_tier_id"]}, "|".join(sorted(set(seaad_universe["result_tier_id"]))), analysis["result_tier_id"], ""),
            ("strict_key_unique_rosmap_universe", not rosmap_universe.duplicated(STRICT_KEY).any(), len(rosmap_universe.drop_duplicates(STRICT_KEY)), len(rosmap_universe), ""),
            ("strict_key_unique_seaad_universe", not seaad_universe.duplicated(STRICT_KEY).any(), len(seaad_universe.drop_duplicates(STRICT_KEY)), len(seaad_universe), ""),
            ("rosmap_selected_count", len(rosmap_selected_keys) == 47, len(rosmap_selected_keys), 47, ""),
            ("seaad_selected_count_matches_freeze", len(seaad_selected_keys) == int(freeze.loc[0, "selected_top5_units"]), len(seaad_selected_keys), int(freeze.loc[0, "selected_top5_units"]), ""),
            ("summary_list_rows", len(overlap_summary) == len(cfg["network_order"]) * len(cfg["selection"]["driver_classes"]), len(overlap_summary), len(cfg["network_order"]) * len(cfg["selection"]["driver_classes"]), ""),
            ("no_sensitivity_overlap_tier", overlap_summary["result_tier_id"].nunique() == 1, overlap_summary["result_tier_id"].nunique(), 1, ""),
        ]
    )
    if not overlap_checks["passed"].all():
        failed = overlap_checks.loc[~overlap_checks["passed"], "check"].tolist()
        raise ValueError(f"VH10D overlap checks failed: {failed}")

    if overlap_dir.exists() and any(overlap_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty VH10D directory: {overlap_dir}")
    stage = phase_root / f".10d_overlap.tmp.{os.getpid()}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    paths = {
        "parity": stage / "phase18_selection_parity_checks.tsv",
        "universe": stage / "phase18_candidate_universe.tsv.gz",
        "overlap": stage / "rosmap_seaad_candidate_overlap.tsv",
        "summary": stage / "rosmap_seaad_overlap_summary.tsv",
        "gene": stage / "rosmap_seaad_gene_only_overlap.tsv",
        "checks": stage / "overlap_checks.tsv",
    }
    atomic_write_tsv(parity_checks, paths["parity"])
    atomic_write_tsv(rosmap_universe, paths["universe"])
    atomic_write_tsv(overlap, paths["overlap"])
    atomic_write_tsv(overlap_summary, paths["summary"])
    atomic_write_tsv(gene_overlap, paths["gene"])
    atomic_write_tsv(overlap_checks, paths["checks"])
    if overlap_dir.exists():
        overlap_dir.rmdir()
    os.replace(stage, overlap_dir)
    overlap_outputs = [overlap_dir / path.name for path in paths.values()]
    overlap_artifacts = write_artifacts(
        overlap_outputs, project_root, overlap_dir / "artifacts.tsv"
    )
    overlap_status = status_frame(
        "VH10D",
        "validated_complete",
        project_root,
        config_path,
        started,
        rosmap_selected_units=len(rosmap_selected_keys),
        seaad_selected_units=len(seaad_selected_keys),
        rosmap_testable_selected_units=len(rosmap_selected_testable),
        strict_shared_top5_units=len(strict_shared),
        common_assessable_units=len(common_keys),
        shared_unique_genes=len(rosmap_gene_set.intersection(seaad_gene_set)),
        artifact_count=len(overlap_artifacts),
    )
    atomic_write_tsv(overlap_status, overlap_dir / "status.tsv")

    root_checks = checks_frame(
        [
            ("vh10a_validated", True, "validated_complete", "validated_complete", ""),
            ("vh10b_validated", True, "validated_complete", "validated_complete", ""),
            ("vh10c_validated", True, "validated_complete", "validated_complete", ""),
            ("vh10d_validated", True, "validated_complete", "validated_complete", ""),
            ("phase18_parity_checks_pass", parity_checks["passed"].all(), int(parity_checks["passed"].sum()), len(parity_checks), ""),
            ("overlap_checks_pass", overlap_checks["passed"].all(), int(overlap_checks["passed"].sum()), len(overlap_checks), ""),
            ("no_deferred_sensitivity_executed", True, analysis["result_tier_id"], analysis["result_tier_id"], ""),
        ]
    )
    atomic_write_tsv(root_checks, phase_root / "checks.tsv")
    root_artifact_paths = [
        input_dir / "status.tsv",
        kda_dir / "status.tsv",
        selection_dir / "status.tsv",
        overlap_dir / "status.tsv",
        phase_root / "checks.tsv",
    ]
    root_artifacts = write_artifacts(
        root_artifact_paths, project_root, phase_root / "artifacts.tsv"
    )
    root_status = status_frame(
        "VH10",
        "validated_complete",
        project_root,
        config_path,
        started,
        active_result_tier=analysis["result_tier_id"],
        active_kda_calls=analysis["expected"]["active_kda_calls"],
        seaad_passing_candidate_units=int(
            selection_status.loc[0, "passing_candidate_units"]
        ),
        seaad_selected_top5_units=len(seaad_selected_keys),
        seaad_selected_unique_genes=len(seaad_gene_set),
        rosmap_testable_selected_units=len(rosmap_selected_testable),
        strict_shared_top5_units=len(strict_shared),
        shared_unique_genes=len(rosmap_gene_set.intersection(seaad_gene_set)),
        artifact_count=len(root_artifacts),
    )
    atomic_write_tsv(root_status, phase_root / "status.tsv")
    print(f"VH10D validated_complete: {overlap_dir}")
    print(f"VH10 validated_complete: {phase_root}")
    print(
        f"ROSMAP selected={len(rosmap_selected_keys)} testable={len(rosmap_selected_testable)} "
        f"SEA-AD selected={len(seaad_selected_keys)} strict_shared={len(strict_shared)} "
        f"shared_unique_genes={len(rosmap_gene_set.intersection(seaad_gene_set))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
