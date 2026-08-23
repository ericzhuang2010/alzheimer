#!/usr/bin/env python3
"""VH10A: freeze SEA-AD DEG inputs and construct ≥3-gene KDA queries."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pandas as pd
import yaml

from seaad_common import (
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    repo_path,
    require_phase,
    sha256_file,
    sha256_strings,
    status_frame,
    utc_now,
    write_artifacts,
)


def truth(value) -> bool:
    return str(value).strip().lower() in {"true", "t", "1", "yes"}


def read_network(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        sep="\t",
        header=None,
        usecols=[0, 1],
        names=["source", "target"],
        dtype=str,
        keep_default_na=False,
    )
    frame = frame.loc[
        frame["source"].ne("")
        & frame["target"].ne("")
        & frame["source"].ne(frame["target"])
    ].drop_duplicates()
    return frame.reset_index(drop=True)


def main() -> int:
    args = parse_config_cli("VH10A: construct SEA-AD KDA queries")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    cfg = config["vh10"]
    analysis = cfg["analysis"]
    expected = analysis["expected"]

    require_phase(output_root, "08_deg")
    authority_paths = {}
    authority_rows = []
    for role, item in cfg["input_authority"].items():
        path = repo_path(project_root, item["path"])
        observed = sha256_file(path)
        if observed != item["sha256"]:
            raise ValueError(f"VH10 authority checksum mismatch for {role}: {path}")
        authority_paths[role] = path
        authority_rows.append(
            {
                "role": role,
                "path": str(path.relative_to(project_root)),
                "bytes": path.stat().st_size,
                "sha256": observed,
            }
        )

    with authority_paths["phase12_config"].open() as handle:
        phase12 = yaml.safe_load(handle)
    network_order = list(cfg["network_order"])
    network_frames = {}
    network_rows = []
    for network in network_order:
        net_cfg = phase12["networks"].get(network)
        if net_cfg is None:
            raise ValueError(f"Missing Phase 12 network configuration: {network}")
        path = repo_path(project_root, net_cfg["path"])
        observed = sha256_file(path)
        if observed != net_cfg["sha256"]:
            raise ValueError(f"Network checksum mismatch: {network}")
        frame = read_network(path)
        if frame.empty:
            raise ValueError(f"Network has no usable edges: {network}")
        network_frames[network] = frame
        network_rows.append(
            {
                "broad_network": network,
                "network_path": str(path.relative_to(project_root)),
                "network_sha256": observed,
                "full_network_edges": len(frame),
                "full_network_nodes": len(
                    set(frame["source"]).union(frame["target"])
                ),
            }
        )

    phase18_annotation = pd.read_csv(
        authority_paths["phase18_annotation"],
        sep="\t",
        usecols=["symbol_hgnc_current", "is_mitocarta3"],
        keep_default_na=False,
        low_memory=False,
    )
    phase18_annotation = phase18_annotation.loc[
        phase18_annotation["symbol_hgnc_current"].ne("")
        & phase18_annotation["symbol_hgnc_current"].ne("NA")
    ].copy()
    phase18_annotation["core"] = phase18_annotation["is_mitocarta3"].map(truth)
    conflict = (
        phase18_annotation.groupby("symbol_hgnc_current")["core"]
        .nunique()
        .gt(1)
    )
    if conflict.any():
        raise ValueError(
            f"Conflicting Phase 18 core-Mito annotation for {int(conflict.sum())} symbols"
        )
    phase18_core = (
        phase18_annotation.drop_duplicates("symbol_hgnc_current")
        .set_index("symbol_hgnc_current")["core"]
        .to_dict()
    )

    seaad_annotation = pd.read_csv(
        authority_paths["seaad_annotation"],
        sep="\t",
        usecols=[
            "current_symbol_for_kda",
            "is_core_mito_phase18",
            "phase18_hgnc_identity_conflict",
            "phase18_mitocarta_conflict",
        ],
        keep_default_na=False,
    )
    seaad_annotation = seaad_annotation.loc[
        seaad_annotation["current_symbol_for_kda"].ne("")
        & seaad_annotation["current_symbol_for_kda"].ne("NA")
    ].copy()
    if seaad_annotation["phase18_hgnc_identity_conflict"].map(truth).any():
        raise ValueError("SEA-AD annotation contains Phase 18 HGNC identity conflicts")
    if seaad_annotation["phase18_mitocarta_conflict"].map(truth).any():
        raise ValueError("SEA-AD annotation contains Phase 18 MitoCarta conflicts")
    seaad_annotation["core"] = seaad_annotation["is_core_mito_phase18"].map(truth)
    shared_annotation = seaad_annotation.loc[
        seaad_annotation["current_symbol_for_kda"].isin(phase18_core)
    ]
    annotation_disagreement = shared_annotation.loc[
        shared_annotation.apply(
            lambda row: bool(row["core"])
            != bool(phase18_core[row["current_symbol_for_kda"]]),
            axis=1,
        )
    ]
    if not annotation_disagreement.empty:
        raise ValueError(
            f"SEA-AD/Phase 18 core-Mito disagreement for {len(annotation_disagreement)} features"
        )

    direction = pd.read_csv(
        authority_paths["direction_manifest"], sep="\t", keep_default_na=False
    )
    query_index = pd.read_csv(
        authority_paths["query_input_index"], sep="\t", keep_default_na=False
    )
    if not direction["direction_slot_id"].is_unique:
        raise ValueError("Direction slot IDs are not unique")
    if not query_index["contrast_id"].is_unique:
        raise ValueError("Fine query input contrast IDs are not unique")
    index_by_contrast = query_index.set_index("contrast_id", drop=False)

    fdr_cut = float(analysis["fdr_threshold_exclusive"])
    minimum = int(analysis["minimum_effective_query_genes"])
    warning_below = int(analysis["small_query_warning_below"])
    caches = {}
    result_hash_checks = 0

    for contrast_id, source in index_by_contrast.iterrows():
        result_path = repo_path(project_root, source["result_path"])
        if result_path.stat().st_size != int(source["result_bytes"]):
            raise ValueError(f"DEG result byte mismatch: {result_path}")
        if sha256_file(result_path) != source["result_sha256"]:
            raise ValueError(f"DEG result checksum mismatch: {result_path}")
        result_hash_checks += 1
        table = pd.read_csv(result_path, sep="\t", low_memory=False)
        tested = table.loc[
            table["test_status"].eq("tested")
            & table["current_symbol_for_kda"].notna()
            & table["current_symbol_for_kda"].astype(str).ne("")
        ].copy()
        tested_symbols = set(tested["current_symbol_for_kda"].astype(str))
        network = str(source["broad_network"])
        full = network_frames[network]
        induced = full.loc[
            full["source"].isin(tested_symbols)
            & full["target"].isin(tested_symbols)
        ]
        background = set(induced["source"]).union(induced["target"])
        core_mask = tested["is_core_mito_phase18"].map(truth)
        query_members = tested.loc[core_mask & tested["FDR"].lt(fdr_cut)]
        up = set(
            query_members.loc[
                query_members["logFC"].gt(0), "current_symbol_for_kda"
            ].astype(str)
        )
        down = set(
            query_members.loc[
                query_members["logFC"].lt(0), "current_symbol_for_kda"
            ].astype(str)
        )
        if any(not phase18_core.get(symbol, False) for symbol in up.union(down)):
            raise ValueError(f"Query contains a non-core Phase 18 symbol: {contrast_id}")
        caches[contrast_id] = {
            "result_path": result_path,
            "result_sha256": source["result_sha256"],
            "tested": tested_symbols,
            "induced_edges": len(induced),
            "background": background,
            "AD_up_mito": up,
            "AD_down_mito": down,
        }

    manifest_rows = []
    signature_rows = []
    background_rows = []
    for row in direction.itertuples(index=False):
        record = {
            "schema_version": "seaad_kda_run_manifest_v1",
            "direction_slot": row.direction_slot,
            "direction_slot_id": row.direction_slot_id,
            "contrast_id": row.contrast_id,
            "query_rule_id": analysis["query_rule_id"],
            "result_tier_id": analysis["result_tier_id"],
            "supertype_id": row.supertype_id,
            "fine_cell_type": row.supertype_label,
            "broad_network": row.broad_network,
            "signature_group": row.signature_group,
            "signature_direction": row.phase18_signature_direction,
            "source_terminal_status": row.source_terminal_status,
            "source_terminal_reason": row.terminal_reason,
            "kda_run_id": "",
            "candidate_query_genes": pd.NA,
            "effective_query_genes": pd.NA,
            "exact_tested_genes": pd.NA,
            "induced_network_edges": pd.NA,
            "effective_background_genes": pd.NA,
            "query_size_tier": "not_applicable",
            "eligibility_status": row.query_handoff_status,
            "terminal_status": row.query_handoff_status,
            "result_path": row.result_path,
            "result_sha256": row.result_sha256,
            "network_path": "",
            "network_sha256": "",
            "effective_query_sha256": "",
            "effective_background_sha256": "",
        }
        if row.source_terminal_status == "completed":
            cached = caches.get(row.contrast_id)
            if cached is None:
                raise ValueError(f"Completed direction lacks query input: {row.contrast_id}")
            source_query = cached[row.phase18_signature_direction]
            background = cached["background"]
            effective = source_query.intersection(background)
            if not effective:
                terminal = "query_empty"
                tier = "empty"
            elif len(effective) < minimum:
                terminal = "query_below_minimum"
                tier = "below_minimum"
            elif len(effective) < warning_below:
                terminal = "eligible_small_query"
                tier = "small_query"
            else:
                terminal = "eligible_phase18_sized"
                tier = "phase18_sized"
            net_row = next(
                item for item in network_rows
                if item["broad_network"] == row.broad_network
            )
            record.update(
                {
                    "candidate_query_genes": len(source_query),
                    "effective_query_genes": len(effective),
                    "exact_tested_genes": len(cached["tested"]),
                    "induced_network_edges": cached["induced_edges"],
                    "effective_background_genes": len(background),
                    "query_size_tier": tier,
                    "eligibility_status": (
                        "eligible"
                        if terminal in {"eligible_small_query", "eligible_phase18_sized"}
                        else "not_eligible"
                    ),
                    "terminal_status": terminal,
                    "network_path": net_row["network_path"],
                    "network_sha256": net_row["network_sha256"],
                    "effective_query_sha256": sha256_strings(sorted(effective)),
                    "effective_background_sha256": sha256_strings(sorted(background)),
                }
            )
            if terminal in {"eligible_small_query", "eligible_phase18_sized"}:
                run_id = (
                    f"seaad__{row.supertype_id}__{row.signature_group}"
                    f"__{row.phase18_signature_direction}"
                )
                record["kda_run_id"] = run_id
                for symbol in sorted(source_query):
                    signature_rows.append(
                        {
                            "schema_version": "seaad_kda_signature_members_v1",
                            "kda_run_id": run_id,
                            "gene": symbol,
                            "effective_member": symbol in effective,
                            "exclusion_reason": (
                                "" if symbol in effective else "not_in_effective_background"
                            ),
                        }
                    )
                for symbol in sorted(background):
                    background_rows.append(
                        {
                            "schema_version": "seaad_kda_background_members_v1",
                            "kda_run_id": run_id,
                            "gene": symbol,
                        }
                    )
        manifest_rows.append(record)

    manifest = pd.DataFrame(manifest_rows)
    signatures = pd.DataFrame(signature_rows)
    backgrounds = pd.DataFrame(background_rows)
    eligible_states = {"eligible_small_query", "eligible_phase18_sized"}
    eligible = manifest.loc[manifest["terminal_status"].isin(eligible_states)].copy()
    active_by_network = (
        eligible.groupby(["broad_network", "signature_direction"])
        .size()
        .rename("active_calls")
        .reset_index()
    )
    network_identity = pd.DataFrame(network_rows).merge(
        eligible.groupby("broad_network").size().rename("active_kda_calls"),
        left_on="broad_network",
        right_index=True,
        how="left",
    )
    network_identity["active_kda_calls"] = (
        network_identity["active_kda_calls"].fillna(0).astype(int)
    )
    attrition = (
        manifest.groupby(
            ["source_terminal_status", "terminal_status", "query_size_tier"],
            dropna=False,
        )
        .size()
        .rename("direction_slots")
        .reset_index()
    )
    completed_source_directions = int(
        manifest["source_terminal_status"].eq("completed").sum()
    )
    checks = checks_frame(
        [
            ("structural_direction_slots", len(manifest) == expected["structural_direction_slots"], len(manifest), expected["structural_direction_slots"], ""),
            ("direction_slot_ids_unique", manifest["direction_slot_id"].is_unique, manifest["direction_slot_id"].nunique(), len(manifest), ""),
            ("one_active_query_rule", manifest["query_rule_id"].nunique() == 1, manifest["query_rule_id"].nunique(), 1, ""),
            ("completed_source_direction_reconciliation", completed_source_directions == 2 * len(query_index), completed_source_directions, 2 * len(query_index), "two signed directions per completed DEG contrast"),
            ("active_call_tier_reconciliation", len(eligible) == int(eligible["query_size_tier"].isin(["small_query", "phase18_sized"]).sum()), len(eligible), int(eligible["query_size_tier"].isin(["small_query", "phase18_sized"]).sum()), ""),
            ("active_call_direction_reconciliation", len(eligible) == int(eligible["signature_direction"].isin(analysis["directions"]).sum()), len(eligible), int(eligible["signature_direction"].isin(analysis["directions"]).sum()), ""),
            ("effective_queries_subset_background", all(set(signatures.loc[(signatures["kda_run_id"] == run_id) & signatures["effective_member"].map(truth), "gene"]).issubset(set(backgrounds.loc[backgrounds["kda_run_id"] == run_id, "gene"])) for run_id in eligible["kda_run_id"]), True, True, ""),
            ("eligible_run_ids_unique", eligible["kda_run_id"].is_unique, eligible["kda_run_id"].nunique(), len(eligible), ""),
            ("result_hash_checks", result_hash_checks == len(query_index), result_hash_checks, len(query_index), ""),
            ("seaad_phase18_annotation_agreement", annotation_disagreement.empty, len(annotation_disagreement), 0, ""),
        ]
    )
    if not checks["passed"].all():
        failed = checks.loc[~checks["passed"], "check"].tolist()
        raise ValueError(f"VH10A blocking checks failed: {failed}")

    root_dir = output_root / cfg["output_directory"]
    root_dir.mkdir(parents=True, exist_ok=True)
    final_dir = root_dir / "10a_inputs"
    if final_dir.exists() and any(final_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty VH10A directory: {final_dir}")
    stage = root_dir / f".10a_inputs.tmp.{os.getpid()}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    paths = {
        "manifest": stage / "seaad_kda_run_manifest.tsv",
        "signatures": stage / "seaad_kda_signature_members.tsv.gz",
        "backgrounds": stage / "seaad_kda_background_members.tsv.gz",
        "attrition": stage / "query_attrition.tsv",
        "networks": stage / "network_identity.tsv",
        "authority": stage / "input_authority.tsv",
        "checks": stage / "input_checks.tsv",
    }
    atomic_write_tsv(manifest, paths["manifest"])
    atomic_write_tsv(signatures, paths["signatures"])
    atomic_write_tsv(backgrounds, paths["backgrounds"])
    atomic_write_tsv(attrition, paths["attrition"])
    atomic_write_tsv(network_identity, paths["networks"])
    atomic_write_tsv(pd.DataFrame(authority_rows), paths["authority"])
    atomic_write_tsv(checks, paths["checks"])
    if final_dir.exists():
        final_dir.rmdir()
    os.replace(stage, final_dir)
    final_outputs = [final_dir / item.name for item in paths.values()]
    artifacts = write_artifacts(final_outputs, project_root, final_dir / "artifacts.tsv")
    status = status_frame(
        "VH10A",
        "validated_complete",
        project_root,
        config_path,
        started,
        structural_direction_slots=len(manifest),
        completed_source_directions=int(manifest["source_terminal_status"].eq("completed").sum()),
        active_kda_calls=len(eligible),
        small_query_calls=int(eligible["query_size_tier"].eq("small_query").sum()),
        phase18_sized_calls=int(eligible["query_size_tier"].eq("phase18_sized").sum()),
        active_query_members=int(signatures["effective_member"].map(truth).sum()),
        active_background_members=len(backgrounds),
        artifact_count=len(artifacts),
    )
    atomic_write_tsv(status, final_dir / "status.tsv")
    print(f"VH10A validated_complete: {final_dir}")
    print(f"active_kda_calls={len(eligible)} small={int(eligible['query_size_tier'].eq('small_query').sum())} phase18_sized={int(eligible['query_size_tier'].eq('phase18_sized').sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
