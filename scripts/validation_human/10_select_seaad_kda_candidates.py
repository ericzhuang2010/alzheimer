#!/usr/bin/env python3
"""VH10B/C: validate SEA-AD KDA calls and freeze independent top-driver lists."""

from __future__ import annotations

import importlib.util
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    git_revision,
    load_config,
    parse_config_cli,
    repo_path,
    sha256_file,
    sha256_strings,
    status_frame,
    utc_now,
    write_artifacts,
)


def truth(value) -> bool:
    return str(value).strip().lower() in {"true", "t", "1", "yes"}

def apply_seaad_candidate_threshold(
    rows, minimum_coverage, aggregate_q_threshold, minimum_support, phase18
):
    """Apply SEA-AD-specific aggregate gates without changing frozen ROSMAP."""
    for row in rows:
        q_value = row["aggregate_acat_q"]
        p_value = row["aggregate_acat_p"]
        q_valid = q_value is not None and not pd.isna(q_value)
        p_valid = p_value is not None and not pd.isna(p_value)
        q_pass = q_valid and q_value <= aggregate_q_threshold
        row["coverage_pass"] = row["coverage_fraction"] >= minimum_coverage
        row["aggregate_q_pass"] = q_pass
        if not row["coverage_pass"]:
            status = "insufficient_coverage"
        elif not p_valid or not q_valid:
            status = "not_testable"
        elif q_pass and row["conservative_support_count"] >= minimum_support:
            status = "driver_candidate"
        elif q_pass:
            status = "aggregate_only"
        elif p_value <= 0.05:
            status = "exploratory"
        else:
            status = "not_supported"
        row["terminal_candidate_status"] = status
    phase18.assign_candidate_ranks(rows)



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


def main() -> int:
    args = parse_config_cli("VH10B/C: reconstruct and select SEA-AD KDA candidates")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    cfg = config["vh10"]
    analysis = cfg["analysis"]
    selection = cfg["selection"]
    phase_root = output_root / cfg["output_directory"]
    input_dir = phase_root / "10a_inputs"
    kda_dir = phase_root / "10b_kda"
    selection_dir = phase_root / "10c_seaad_selection"

    input_status = require_validated(input_dir, project_root)
    expected_active_calls = int(input_status.loc[0, "active_kda_calls"])
    worker_path = kda_dir / "r_worker_status.tsv"
    r_qc_path = kda_dir / "r_run_qc.tsv"
    significant_path = kda_dir / "seaad_kda_significant_returns.tsv"
    for path in (worker_path, r_qc_path, significant_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing VH10B R output: {path}")
    worker = pd.read_csv(worker_path, sep="\t", keep_default_na=False)
    if (
        len(worker) != 1
        or worker.loc[0, "task_status"] != "worker_complete"
        or int(worker.loc[0, "failed_calls"]) != 0
    ):
        raise ValueError("VH10B R worker did not complete cleanly")
    if int(worker.loc[0, "active_kda_calls"]) != expected_active_calls:
        raise ValueError("VH10B R call count differs from the validated VH10A manifest")

    phase18_code_item = cfg["input_authority"]["phase18_code"]
    phase18_code = repo_path(project_root, phase18_code_item["path"])
    if sha256_file(phase18_code) != phase18_code_item["sha256"]:
        raise ValueError("Phase 18 selection-code checksum mismatch")
    phase18 = load_phase18_module(phase18_code)
    if phase18.validate_acat_example() > 1e-9:
        raise ValueError("Phase 18 ACAT regression example failed")

    manifest = pd.read_csv(
        input_dir / "seaad_kda_run_manifest.tsv", sep="\t", keep_default_na=False
    )
    active_states = {"eligible_small_query", "eligible_phase18_sized"}
    runs_frame = manifest.loc[manifest["terminal_status"].isin(active_states)].copy()
    if len(runs_frame) != expected_active_calls:
        raise ValueError("Active manifest run count mismatch")
    included_runs = runs_frame.to_dict("records")
    included_ids = set(runs_frame["kda_run_id"])

    signature_table = pd.read_csv(
        input_dir / "seaad_kda_signature_members.tsv.gz",
        sep="\t",
        keep_default_na=False,
    )
    background_table = pd.read_csv(
        input_dir / "seaad_kda_background_members.tsv.gz",
        sep="\t",
        keep_default_na=False,
    )
    signatures = defaultdict(set)
    for row in signature_table.itertuples(index=False):
        if row.kda_run_id in included_ids and truth(row.effective_member):
            signatures[row.kda_run_id].add(str(row.gene))
    backgrounds = defaultdict(set)
    for row in background_table.itertuples(index=False):
        if row.kda_run_id in included_ids:
            backgrounds[row.kda_run_id].add(str(row.gene))
    for run in included_runs:
        run_id = run["kda_run_id"]
        if len(signatures[run_id]) != phase18.as_int(run["effective_query_genes"]):
            raise ValueError(f"Signature size mismatch: {run_id}")
        if len(backgrounds[run_id]) != phase18.as_int(run["effective_background_genes"]):
            raise ValueError(f"Background size mismatch: {run_id}")
        if not signatures[run_id].issubset(backgrounds[run_id]):
            raise ValueError(f"Signature not contained in background: {run_id}")

    annotation_item = cfg["input_authority"]["phase18_annotation"]
    annotation_path = repo_path(project_root, annotation_item["path"])
    if sha256_file(annotation_path) != annotation_item["sha256"]:
        raise ValueError("Phase 18 annotation checksum mismatch")
    annotation, annotation_conflicts = phase18.load_annotation(annotation_path)
    if annotation_conflicts:
        raise ValueError(
            f"Conflicting Phase 18 annotations: {len(annotation_conflicts)}"
        )

    full_edges = {}
    for row in (
        runs_frame[["broad_network", "network_path", "network_sha256"]]
        .drop_duplicates()
        .itertuples(index=False)
    ):
        path = repo_path(project_root, row.network_path)
        if sha256_file(path) != row.network_sha256:
            raise ValueError(f"Network checksum mismatch: {row.broad_network}")
        full_edges[row.broad_network] = phase18.load_network(path)

    significant_rows = list(phase18.iter_tsv(significant_path))
    if len(
        {(row["kda_run_id"], row["key_driver"]) for row in significant_rows}
    ) != len(significant_rows):
        raise ValueError("R significant returns contain duplicate run/gene keys")
    published_by_run = defaultdict(dict)
    for row in significant_rows:
        if row["kda_run_id"] not in included_ids:
            raise ValueError(f"R returned an unknown run: {row['kda_run_id']}")
        published_by_run[row["kda_run_id"]][row["key_driver"]] = row

    explicit_by_run = {}
    reconstruction_rows = []
    for index, run in enumerate(included_runs, start=1):
        run_id = run["kda_run_id"]
        explicit, summary = phase18.reconstruct_run(
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
        reconstruction_rows.append(
            {
                "kda_run_id": run_id,
                "broad_network": run["broad_network"],
                "fine_cell_type": run["fine_cell_type"],
                "signature_group": run["signature_group"],
                "signature_direction": run["signature_direction"],
                "effective_query_genes": len(signatures[run_id]),
                "effective_background_genes": len(backgrounds[run_id]),
                "induced_edges": summary["induced_edges"],
                "explicit_candidates": summary["explicit_candidates"],
                "implicit_candidates": summary["implicit_candidates"],
                "layer_tests": summary["layer_tests"],
                "r_significant_returns": len(published_by_run.get(run_id, {})),
                "r_python_significant_parity": True,
            }
        )
        if index % 10 == 0 or index == len(included_runs):
            print(f"VH10C reconstructed_runs={index}/{len(included_runs)}", flush=True)

    runs_by_network = defaultdict(list)
    for run in included_runs:
        runs_by_network[run["broad_network"]].append(run)
    network_genes = {}
    for network, runs in runs_by_network.items():
        network_genes[network] = sorted(
            set().union(*(backgrounds[run["kda_run_id"]] for run in runs))
        )

    minimum_coverage = float(selection["minimum_coverage"])
    aggregate_q_threshold = float(selection["aggregate_q_threshold"])
    minimum_support = int(selection["minimum_conservative_supporting_runs"])
    aggregate_rows = []
    aggregates_by_network = {}
    for network in cfg["network_order"]:
        if network not in runs_by_network:
            aggregates_by_network[network] = []
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
        apply_seaad_candidate_threshold(
            rows,
            minimum_coverage,
            aggregate_q_threshold,
            minimum_support,
            phase18,
        )
        for row in rows:
            row["missing_as_one_acat_p"] = None
            row["missing_as_one_acat_q"] = None
            if row["terminal_candidate_status"] == "driver_candidate":
                row["evidence_tier"] = (
                    "single_run_network_evidence"
                    if row["eligible_run_count"] == 1
                    else "multi_run_network_evidence"
                )
            else:
                row["evidence_tier"] = "not_a_driver_candidate"
        aggregates_by_network[network] = rows
        aggregate_rows.extend(rows)

    aggregate_map = {
        (row["broad_network"], row["current_symbol"], row["case_id"]): row
        for row in aggregate_rows
    }
    candidate_summary_rows = []
    for row in aggregate_rows:
        public = phase18.public_row(row)
        public.pop("missing_as_one_acat_p", None)
        public.pop("missing_as_one_acat_q", None)
        public["query_rule_id"] = analysis["query_rule_id"]
        public["result_tier_id"] = analysis["result_tier_id"]
        candidate_summary_rows.append(public)
    candidate_summary = pd.DataFrame(candidate_summary_rows)
    if candidate_summary.duplicated(
        ["broad_network", "current_symbol", "case_id"]
    ).any():
        raise ValueError("SEA-AD candidate units are not unique")

    top5 = pd.DataFrame(
        phase18.top5_rows(aggregate_rows, list(cfg["network_order"]))
    )
    top5.insert(0, "result_tier_id", analysis["result_tier_id"])
    top5.insert(0, "query_rule_id", analysis["query_rule_id"])
    selected_rows = top5.loc[top5["list_status"].eq("ranked_candidates")].copy()
    list_status = (
        top5.groupby(
            ["query_rule_id", "result_tier_id", "broad_network", "case_id"],
            sort=False,
            dropna=False,
        )
        .agg(
            list_status=("list_status", "first"),
            total_passing_candidate_count=("total_passing_candidate_count", "max"),
            displayed_candidate_count=("displayed_candidate_count", "max"),
            output_rows=("case_id", "size"),
        )
        .reset_index()
    )

    call_return_rows = []
    significant_keys = {
        (row["kda_run_id"], row["key_driver"]) for row in significant_rows
    }
    case_counts = Counter(
        (row["broad_network"], row["case_id"])
        for row in aggregate_rows
        if row["terminal_candidate_status"] == "driver_candidate"
    )
    for run in included_runs:
        run_id = run["kda_run_id"]
        for symbol in sorted(explicit_by_run[run_id]):
            test = phase18.tested_gene_row(
                run,
                symbol,
                signatures,
                backgrounds,
                explicit_by_run,
                annotation,
            )
            case_id = test["case_id"]
            summary = phase18.public_row(
                aggregate_map[(run["broad_network"], symbol, case_id)]
            )
            summary.pop("missing_as_one_acat_p", None)
            summary.pop("missing_as_one_acat_q", None)
            output = {
                "schema_version": "seaad_kda_call_returns_v1",
                "query_rule_id": analysis["query_rule_id"],
                "result_tier_id": analysis["result_tier_id"],
                "kda_run_id": run_id,
                "fine_cell_type": run["fine_cell_type"],
                "broad_network": run["broad_network"],
                "signature_group": run["signature_group"],
                "signature_direction": run["signature_direction"],
                "effective_query_genes": run["effective_query_genes"],
                "effective_background_genes": run["effective_background_genes"],
                "key_driver": symbol,
                "tested_by_call_key_drivers": True,
                "significant_by_call_key_drivers": (
                    run_id,
                    symbol,
                )
                in significant_keys,
                "case_driver_candidate_count": case_counts[
                    (run["broad_network"], case_id)
                ],
                "case_displayed_candidate_count": min(
                    case_counts[(run["broad_network"], case_id)], 5
                ),
                **test,
                **summary,
            }
            call_return_rows.append(output)
    call_returns = pd.DataFrame(call_return_rows)

    test_fields = [
        "kda_run_id",
        "fine_cell_type",
        "broad_network",
        "signature_group",
        "signature_direction",
        "current_symbol",
        "case_id",
        "is_core_mito",
        "mitocarta_canonical_symbol",
        "query_member",
        "test_status",
        "usable_test",
        "explicit_family_member",
        "effective_query_size",
        "effective_background_size",
        "original_layer",
        "original_overlap_count",
        "original_neighborhood_size",
        "original_non_neighborhood_size",
        "original_signature_size",
        "original_fold_enrichment",
        "original_log_p",
        "original_raw_p",
        "original_run_q",
        "self_excluded",
        "final_layer",
        "final_overlap_count",
        "final_neighborhood_size",
        "final_non_neighborhood_size",
        "final_signature_size",
        "final_background_size",
        "final_fold_enrichment",
        "final_log_p",
        "final_raw_p",
        "final_run_q",
        "other_query_overlap",
        "support_overlap_pass",
        "support_fold_pass",
        "support_run_q_pass",
        "conservative_support",
    ]
    candidate_tests_path = kda_dir / "seaad_kda_candidate_tests.tsv.gz"
    candidate_test_count = phase18.write_tsv(
        candidate_tests_path,
        phase18.candidate_test_rows(
            included_runs,
            network_genes,
            signatures,
            backgrounds,
            explicit_by_run,
            annotation,
        ),
        test_fields,
        "seaad_kda_candidate_tests_v1",
    )

    reconstruction = pd.DataFrame(reconstruction_rows)
    r_qc = pd.read_csv(r_qc_path, sep="\t", keep_default_na=False)
    run_qc = r_qc.merge(
        reconstruction[
            [
                "kda_run_id",
                "explicit_candidates",
                "implicit_candidates",
                "layer_tests",
                "r_python_significant_parity",
            ]
        ],
        on="kda_run_id",
        how="left",
        validate="one_to_one",
    )
    reconstruction_checks = checks_frame(
        [
            ("r_worker_complete", True, worker.loc[0, "task_status"], "worker_complete", ""),
            ("active_call_count", len(included_runs) == expected_active_calls, len(included_runs), expected_active_calls, ""),
            ("all_r_calls_completed", r_qc["terminal_status"].str.startswith("completed_").all(), int(r_qc["terminal_status"].str.startswith("completed_").sum()), len(r_qc), ""),
            ("r_python_significant_parity", reconstruction["r_python_significant_parity"].all(), int(reconstruction["r_python_significant_parity"].sum()), len(reconstruction), ""),
            ("explicit_run_gene_keys_unique", not call_returns.duplicated(["kda_run_id", "key_driver"]).any(), len(call_returns.drop_duplicates(["kda_run_id", "key_driver"])), len(call_returns), ""),
            ("candidate_unit_keys_unique", not candidate_summary.duplicated(["broad_network", "current_symbol", "case_id"]).any(), len(candidate_summary.drop_duplicates(["broad_network", "current_symbol", "case_id"])), len(candidate_summary), ""),
            ("driver_classes_exact", sorted(candidate_summary["case_id"].unique()) == sorted(selection["driver_classes"]), "|".join(sorted(candidate_summary["case_id"].unique())), "|".join(sorted(selection["driver_classes"])), ""),
            ("top5_rank_cap", selected_rows.empty or pd.to_numeric(selected_rows["display_rank"]).le(selection["display_limit"]).all(), pd.to_numeric(selected_rows["display_rank"], errors="coerce").max() if not selected_rows.empty else 0, selection["display_limit"], ""),
            ("list_status_rows", len(list_status) == len(cfg["network_order"]) * len(selection["driver_classes"]), len(list_status), len(cfg["network_order"]) * len(selection["driver_classes"]), ""),
            ("no_optional_sensitivity_tier", set(candidate_summary["result_tier_id"]) == {analysis["result_tier_id"]}, "|".join(sorted(set(candidate_summary["result_tier_id"]))), analysis["result_tier_id"], ""),
            ("acat_regression", phase18.validate_acat_example() <= 1e-9, phase18.validate_acat_example(), "<=1e-9", ""),
        ]
    )
    if not reconstruction_checks["passed"].all():
        failed = reconstruction_checks.loc[
            ~reconstruction_checks["passed"], "check"
        ].tolist()
        raise ValueError(f"VH10B/C blocking checks failed: {failed}")

    call_returns_path = kda_dir / "seaad_kda_call_returns.tsv.gz"
    run_reconstruction_path = kda_dir / "run_reconstruction_checks.tsv"
    run_qc_path = kda_dir / "run_qc.tsv"
    atomic_write_tsv(call_returns, call_returns_path)
    atomic_write_tsv(reconstruction_checks, run_reconstruction_path)
    atomic_write_tsv(run_qc, run_qc_path)
    kda_outputs = [
        call_returns_path,
        significant_path,
        candidate_tests_path,
        run_reconstruction_path,
        run_qc_path,
        r_qc_path,
        worker_path,
    ]
    kda_artifacts = write_artifacts(
        kda_outputs, project_root, kda_dir / "artifacts.tsv"
    )
    kda_status = status_frame(
        "VH10B",
        "validated_complete",
        project_root,
        config_path,
        started,
        active_kda_calls=len(included_runs),
        completed_significant_calls=int(
            r_qc["terminal_status"].eq("completed_significant").sum()
        ),
        completed_no_significant_calls=int(
            r_qc["terminal_status"].eq("completed_no_significant").sum()
        ),
        significant_return_rows=len(significant_rows),
        explicit_call_return_rows=len(call_returns),
        candidate_test_rows=candidate_test_count,
        artifact_count=len(kda_artifacts),
    )
    atomic_write_tsv(kda_status, kda_dir / "status.tsv")

    if selection_dir.exists() and any(selection_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite nonempty VH10C directory: {selection_dir}"
        )
    stage = phase_root / f".10c_seaad_selection.tmp.{os.getpid()}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    candidate_path = stage / "seaad_candidate_summary.tsv.gz"
    top5_path = stage / "seaad_top5.tsv"
    list_status_path = stage / "seaad_list_status.tsv"
    freeze_path = stage / "seaad_selection_freeze.tsv"
    checks_path = stage / "selection_checks.tsv"
    atomic_write_tsv(candidate_summary, candidate_path)
    atomic_write_tsv(top5, top5_path)
    atomic_write_tsv(list_status, list_status_path)
    selected_key_values = sorted(
        f"{row.broad_network}\t{row.current_symbol}\t{row.case_id}\t{row.display_rank}"
        for row in selected_rows.itertuples(index=False)
    )
    freeze = pd.DataFrame(
        [
            {
                "schema_version": "seaad_kda_selection_freeze_v1",
                "query_rule_id": analysis["query_rule_id"],
                "result_tier_id": analysis["result_tier_id"],
                "minimum_coverage": minimum_coverage,
                "aggregate_q_threshold": aggregate_q_threshold,
                "minimum_conservative_supporting_runs": minimum_support,
                "candidate_units": len(candidate_summary),
                "passing_candidate_units": int(
                    candidate_summary["terminal_candidate_status"]
                    .eq("driver_candidate")
                    .sum()
                ),
                "selected_top5_units": len(selected_rows),
                "selected_unique_genes": selected_rows["current_symbol"].nunique(),
                "selected_keys_sha256": sha256_strings(selected_key_values),
                "candidate_summary_sha256": sha256_file(candidate_path),
                "top5_sha256": sha256_file(top5_path),
                "selection_code_path": str(
                    Path(__file__).resolve().relative_to(project_root)
                ),
                "selection_code_sha256": sha256_file(__file__),
                "phase18_authority_code_sha256": sha256_file(phase18_code),
                "config_sha256": sha256_file(config_path),
                "git_revision": git_revision(project_root),
                "rosmap_candidate_files_read": False,
                "freeze_status": "independent_seaad_selection_frozen",
                "freeze_timestamp_utc": utc_now(),
            }
        ]
    )
    driver_candidates = candidate_summary["terminal_candidate_status"].eq(
        "driver_candidate"
    )
    selection_checks = checks_frame(
        [
            ("candidate_units_unique", not candidate_summary.duplicated(["broad_network", "current_symbol", "case_id"]).any(), len(candidate_summary), len(candidate_summary), ""),
            ("selected_keys_unique", not selected_rows.duplicated(["broad_network", "current_symbol", "case_id"]).any(), len(selected_rows.drop_duplicates(["broad_network", "current_symbol", "case_id"])), len(selected_rows), ""),
            ("selected_are_driver_candidates", set(zip(selected_rows["broad_network"], selected_rows["current_symbol"], selected_rows["case_id"])).issubset(set(zip(candidate_summary.loc[driver_candidates, "broad_network"], candidate_summary.loc[driver_candidates, "current_symbol"], candidate_summary.loc[driver_candidates, "case_id"]))), True, True, ""),
            ("driver_candidates_meet_coverage", pd.to_numeric(candidate_summary.loc[driver_candidates, "coverage_fraction"], errors="coerce").ge(minimum_coverage).all(), True, True, ""),
            ("driver_candidates_meet_aggregate_q", pd.to_numeric(candidate_summary.loc[driver_candidates, "aggregate_acat_q"], errors="coerce").le(aggregate_q_threshold).all(), True, True, ""),
            ("driver_candidates_meet_conservative_support", pd.to_numeric(candidate_summary.loc[driver_candidates, "conservative_support_count"], errors="coerce").ge(minimum_support).all(), True, True, ""),
            ("top5_cap", selected_rows.groupby(["broad_network", "case_id"]).size().le(selection["display_limit"]).all(), int(selected_rows.groupby(["broad_network", "case_id"]).size().max()) if not selected_rows.empty else 0, selection["display_limit"], ""),
            ("rosmap_blinded_during_freeze", not truth(freeze.loc[0, "rosmap_candidate_files_read"]), freeze.loc[0, "rosmap_candidate_files_read"], False, ""),
            ("one_active_result_tier", candidate_summary["result_tier_id"].nunique() == 1, candidate_summary["result_tier_id"].nunique(), 1, ""),
        ]
    )
    if not selection_checks["passed"].all():
        failed = selection_checks.loc[~selection_checks["passed"], "check"].tolist()
        raise ValueError(f"VH10C selection checks failed: {failed}")
    atomic_write_tsv(freeze, freeze_path)
    atomic_write_tsv(selection_checks, checks_path)
    if selection_dir.exists():
        selection_dir.rmdir()
    os.replace(stage, selection_dir)
    selection_outputs = [
        selection_dir / candidate_path.name,
        selection_dir / top5_path.name,
        selection_dir / list_status_path.name,
        selection_dir / freeze_path.name,
        selection_dir / checks_path.name,
    ]
    selection_artifacts = write_artifacts(
        selection_outputs, project_root, selection_dir / "artifacts.tsv"
    )
    selection_status = status_frame(
        "VH10C",
        "validated_complete",
        project_root,
        config_path,
        started,
        minimum_coverage=minimum_coverage,
        aggregate_q_threshold=aggregate_q_threshold,
        minimum_conservative_supporting_runs=minimum_support,
        candidate_units=len(candidate_summary),
        passing_candidate_units=int(driver_candidates.sum()),
        selected_top5_units=len(selected_rows),
        selected_unique_genes=selected_rows["current_symbol"].nunique(),
        testable_networks=int(
            list_status["list_status"].ne("not_testable_no_included_runs").groupby(
                list_status["broad_network"]
            ).any().sum()
        ),
        artifact_count=len(selection_artifacts),
        freeze_sha256=sha256_file(selection_dir / freeze_path.name),
    )
    atomic_write_tsv(selection_status, selection_dir / "status.tsv")
    print(f"VH10B validated_complete: {kda_dir}")
    print(f"VH10C validated_complete: {selection_dir}")
    print(
        "candidate_units="
        f"{len(candidate_summary)} passing={int(candidate_summary['terminal_candidate_status'].eq('driver_candidate').sum())} "
        f"selected_top5={len(selected_rows)} unique_genes={selected_rows['current_symbol'].nunique()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
