#!/usr/bin/env python3
"""VH05: stream raw UMIs into fine-supertype and independently coded broad counts."""

from __future__ import annotations

import os
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from seaad_common import (
    atomic_save_npy,
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_dir,
    repo_path,
    require_phase,
    sha256_array,
    sha256_file,
    sha256_strings,
    status_frame,
    utc_now,
    write_artifacts,
)


def add_arguments(parser):
    parser.add_argument("--block-observations", type=int)
    parser.add_argument("--checkpoint-every-blocks", type=int)
    parser.add_argument("--resume", action="store_true")


def save_snapshot(directory, row_end, fine_counts, broad_counts, metadata):
    fine_path = directory / f"fine_counts_{row_end:07d}.npy"
    broad_path = directory / f"broad_counts_{row_end:07d}.npy"
    marker_path = directory / f"snapshot_{row_end:07d}.tsv"
    atomic_save_npy(fine_counts, fine_path)
    atomic_save_npy(broad_counts, broad_path)
    row = dict(metadata)
    row.update({
        "row_end": row_end,
        "fine_path": fine_path.name,
        "broad_path": broad_path.name,
        "fine_bytes": fine_path.stat().st_size,
        "broad_bytes": broad_path.stat().st_size,
        "fine_sha256": sha256_file(fine_path),
        "broad_sha256": sha256_file(broad_path),
    })
    atomic_write_tsv(pd.DataFrame([row]), marker_path)


def load_latest_snapshot(directory, expected):
    markers = sorted(directory.glob("snapshot_*.tsv"))
    for marker in reversed(markers):
        metadata = pd.read_csv(marker, sep="	").iloc[0].to_dict()
        fine_path = directory / metadata["fine_path"]
        broad_path = directory / metadata["broad_path"]
        if not fine_path.exists() or not broad_path.exists():
            continue
        for key, value in expected.items():
            if str(metadata[key]) != str(value):
                raise ValueError(f"Checkpoint metadata mismatch for {key}")
        if (
            fine_path.stat().st_size != int(metadata["fine_bytes"])
            or broad_path.stat().st_size != int(metadata["broad_bytes"])
            or sha256_file(fine_path) != metadata["fine_sha256"]
            or sha256_file(broad_path) != metadata["broad_sha256"]
        ):
            raise ValueError(f"Checkpoint file identity mismatch: {marker}")
        return metadata, np.load(fine_path), np.load(broad_path)
    return None


def add_sparse_aggregation(target, group_codes, block_matrix):
    selected_rows = np.flatnonzero(group_codes >= 0)
    if selected_rows.size == 0:
        return 0
    assignment = sparse.csr_matrix(
        (
            np.ones(selected_rows.size, dtype=np.int8),
            (group_codes[selected_rows].astype(np.int32), selected_rows.astype(np.int32)),
        ),
        shape=(target.shape[0], block_matrix.shape[0]),
    )
    aggregated = assignment @ block_matrix
    aggregated.sum_duplicates()
    coo = aggregated.tocoo(copy=False)
    target[coo.row, coo.col] += coo.data
    return int(coo.data.sum(dtype=np.int64))


def main() -> int:
    args = parse_config_cli("VH05: stream SEA-AD fine/direct-broad pseudobulk", add_arguments)
    started = utc_now()
    wall_start = time.perf_counter()
    config, config_path, project_root, output_root = load_config(args.config)
    require_phase(output_root, "03_genes")
    vh04 = require_phase(output_root, "04_supertype_manifest")
    output_dir = phase_dir(output_root, "05_pseudobulk")
    checkpoint_dir = output_dir / "checkpoints"
    fine_count_dir = output_dir / "fine_counts"
    fine_sample_dir = output_dir / "fine_samples"
    broad_count_dir = output_dir / "direct_broad_counts"
    for directory in [checkpoint_dir, fine_count_dir, fine_sample_dir, broad_count_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    expected = config["expected_identity"]
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    fine_codes = np.load(output_root / "04_supertype_manifest/nucleus_to_supertype_group_code.npy")
    broad_codes = np.load(output_root / "04_supertype_manifest/nucleus_to_direct_broad_group_code.npy")
    profiles = pd.read_csv(output_root / "04_supertype_manifest/donor_supertype_nucleus_counts.tsv", sep="	", dtype={"donor_id": str})
    broad_profiles = pd.read_csv(output_root / "04_supertype_manifest/donor_direct_broad_nucleus_counts.tsv", sep="	", dtype={"donor_id": str})
    mapping = pd.read_csv(output_root / "04_supertype_manifest/supertype_to_broad_network.tsv", sep="	")
    feature_order = pd.read_csv(output_root / "03_genes/feature_order.tsv", sep="	")
    feature_order = feature_order.sort_values("feature_index")
    genes = feature_order["source_symbol"].astype(str).to_numpy()
    feature_sha = sha256_strings(genes)
    fine_code_sha = sha256_array(fine_codes)
    broad_code_sha = sha256_array(broad_codes)
    if fine_code_sha != str(vh04.loc[0, "fine_group_code_sha256"]):
        raise ValueError("Fine group-code checksum differs from VH04")
    if broad_code_sha != str(vh04.loc[0, "direct_broad_group_code_sha256"]):
        raise ValueError("Broad group-code checksum differs from VH04")

    block_size = args.block_observations or int(config["streaming"]["block_observations"])
    checkpoint_every = args.checkpoint_every_blocks or int(config["streaming"]["checkpoint_every_blocks"])
    if block_size < 1 or checkpoint_every < 1:
        raise ValueError("Streaming and checkpoint block sizes must be positive")

    n_fine_groups = expected["fine_profiles"]
    n_broad_groups = len(broad_profiles)
    with h5py.File(h5ad_path, "r") as h5:
        umi = h5[config["assay"]["umi_layer"]]
        n_obs, n_features = [int(value) for value in umi.attrs["shape"]]
        if len(fine_codes) != n_obs or len(broad_codes) != n_obs or len(genes) != n_features:
            raise ValueError("Group-code or feature dimensions do not match H5AD")

        fine_counts = np.zeros((n_fine_groups, n_features), dtype=np.int64)
        direct_broad_counts = np.zeros((n_broad_groups, n_features), dtype=np.int64)
        next_observation = 0
        source_total = 0
        selected_total = 0
        selected_nuclei_processed = 0
        blocks_completed = 0
        ledger_rows = []
        snapshot_expected = {
            "fine_group_code_sha256": fine_code_sha,
            "direct_broad_group_code_sha256": broad_code_sha,
            "feature_order_sha256": feature_sha,
            "config_sha256": sha256_file(config_path),
        }
        if args.resume:
            loaded = load_latest_snapshot(checkpoint_dir, snapshot_expected)
            if loaded:
                metadata, fine_counts, direct_broad_counts = loaded
                next_observation = int(metadata["row_end"])
                source_total = int(metadata["source_umi_total"])
                selected_total = int(metadata["selected_umi_total"])
                selected_nuclei_processed = int(metadata["selected_nuclei_processed"])
                blocks_completed = int(metadata["blocks_completed"])
                ledger_path = output_dir / "block_ledger.tsv"
                if ledger_path.exists():
                    ledger_rows = pd.read_csv(ledger_path, sep="	").loc[
                        lambda x: x["row_end"] <= next_observation
                    ].to_dict("records")

        stream_start = time.perf_counter()
        while next_observation < n_obs:
            block_start = time.perf_counter()
            row_start = next_observation
            row_end = min(row_start + block_size, n_obs)
            global_indptr = umi["indptr"][row_start:row_end + 1]
            nnz_start = int(global_indptr[0])
            nnz_end = int(global_indptr[-1])
            local_indptr = (global_indptr - nnz_start).astype(np.int64, copy=False)
            indices = umi["indices"][nnz_start:nnz_end].astype(np.int32, copy=False)
            raw = umi["data"][nnz_start:nnz_end]
            if not (
                np.all(np.isfinite(raw))
                and np.all(raw >= 0)
                and np.all(raw == np.floor(raw))
                and np.all(indices >= 0)
                and np.all(indices < n_features)
            ):
                raise ValueError(f"Invalid UMI CSR content in observations {row_start}:{row_end}")
            values = raw.astype(np.int64, copy=False)
            block = sparse.csr_matrix(
                (values, indices, local_indptr),
                shape=(row_end - row_start, n_features),
                dtype=np.int64,
            )
            fine_block_total = add_sparse_aggregation(
                fine_counts, fine_codes[row_start:row_end], block
            )
            broad_block_total = add_sparse_aggregation(
                direct_broad_counts, broad_codes[row_start:row_end], block
            )
            if fine_block_total != broad_block_total:
                raise ValueError(f"Fine/direct-broad block totals differ at {row_start}:{row_end}")
            block_source_total = int(values.sum(dtype=np.int64))
            source_total += block_source_total
            selected_total += fine_block_total
            selected_in_block = int(np.sum(fine_codes[row_start:row_end] >= 0))
            selected_nuclei_processed += selected_in_block
            blocks_completed += 1
            next_observation = row_end
            seconds = time.perf_counter() - block_start
            ledger_rows.append({
                "block": blocks_completed,
                "row_start": row_start,
                "row_end": row_end,
                "observations": row_end - row_start,
                "nnz": nnz_end - nnz_start,
                "selected_nuclei": selected_in_block,
                "source_umi_total": block_source_total,
                "selected_umi_total": fine_block_total,
                "block_seconds": seconds,
                "committed": True,
            })
            if blocks_completed % 100 == 0 or row_end == n_obs:
                print(f"VH05 rows {row_end}/{n_obs}; blocks={blocks_completed}; elapsed={(time.perf_counter()-stream_start)/60:.1f} min", flush=True)
            if blocks_completed % checkpoint_every == 0 or row_end == n_obs:
                metadata = dict(snapshot_expected)
                metadata.update({
                    "source_umi_total": source_total,
                    "selected_umi_total": selected_total,
                    "selected_nuclei_processed": selected_nuclei_processed,
                    "blocks_completed": blocks_completed,
                })
                save_snapshot(checkpoint_dir, row_end, fine_counts, direct_broad_counts, metadata)
                atomic_write_tsv(pd.DataFrame(ledger_rows), output_dir / "block_ledger.tsv")

    streaming_seconds = time.perf_counter() - stream_start
    n_donors = profiles["donor_id"].nunique()
    n_supertypes = len(mapping)
    broad_order = config["taxonomy"]["broad_network_order"]
    rolled_broad = np.zeros_like(direct_broad_counts)
    for row in mapping.itertuples(index=False):
        fine_rows = np.arange(n_donors, dtype=np.int64) * n_supertypes + int(row.supertype_index)
        broad_rows = np.arange(n_donors, dtype=np.int64) * len(broad_order) + int(row.broad_network_index)
        rolled_broad[broad_rows] += fine_counts[fine_rows]
    reconcile_equal = np.array_equal(rolled_broad, direct_broad_counts)
    mismatch_cells = int(np.count_nonzero(rolled_broad != direct_broad_counts))
    reconciliation_rows = []
    for network_index, network in enumerate(broad_order):
        rows = np.arange(n_donors, dtype=np.int64) * len(broad_order) + network_index
        reconciliation_rows.append({
            "broad_network": network,
            "fine_rollup_umi_total": int(rolled_broad[rows].sum(dtype=np.int64)),
            "direct_broad_umi_total": int(direct_broad_counts[rows].sum(dtype=np.int64)),
            "mismatched_gene_donor_cells": int(np.count_nonzero(rolled_broad[rows] != direct_broad_counts[rows])),
            "exact_equal": bool(np.array_equal(rolled_broad[rows], direct_broad_counts[rows])),
        })

    shard_rows = []
    declared_shards = []
    feature_index = np.arange(n_features, dtype=np.int64)
    for row in mapping.sort_values("supertype_index").itertuples(index=False):
        group_rows = np.arange(n_donors, dtype=np.int64) * n_supertypes + int(row.supertype_index)
        sample = profiles.loc[profiles["supertype_id"].eq(row.supertype_id)].sort_values("donor_id").copy()
        if sample["fine_group_code"].tolist() != group_rows.tolist():
            raise ValueError(f"Unexpected sample order for {row.supertype_id}")
        sample.insert(0, "sample_order", np.arange(n_donors, dtype=int))
        sample_path = fine_sample_dir / f"{row.supertype_id}.samples.tsv"
        counts_path = fine_count_dir / f"{row.supertype_id}.counts.tsv.gz"
        count_frame = pd.DataFrame(fine_counts[group_rows].T, columns=sample["pseudobulk_id"])
        count_frame.insert(0, "source_symbol", genes)
        count_frame.insert(0, "feature_index", feature_index)
        atomic_write_tsv(count_frame, counts_path)
        atomic_write_tsv(sample, sample_path)
        declared_shards.extend([counts_path, sample_path])
        shard_rows.append({
            "shard_type": "fine_supertype",
            "context_id": row.supertype_id,
            "scientific_label": row.supertype_label,
            "broad_network": row.broad_network,
            "counts_path": str(counts_path.relative_to(project_root)),
            "samples_path": str(sample_path.relative_to(project_root)),
            "features": n_features,
            "samples": n_donors,
            "counts_bytes": counts_path.stat().st_size,
            "counts_sha256": sha256_file(counts_path),
            "samples_sha256": sha256_file(sample_path),
        })
        del count_frame

    for network_index, network in enumerate(broad_order):
        group_rows = np.arange(n_donors, dtype=np.int64) * len(broad_order) + network_index
        sample = broad_profiles.loc[broad_profiles["broad_network"].eq(network)].sort_values("donor_id").copy()
        sample.insert(0, "sample_order", np.arange(n_donors, dtype=int))
        sample = sample.merge(
            profiles.drop_duplicates("donor_id")[[
                "donor_id", "diagnosis", "sex", "apoe_group", "signature_group",
                "age_death", "pmi", "study", "age_death_scaled", "pmi_scaled",
            ]],
            on="donor_id", how="left", validate="one_to_one",
        )
        sample["primary_profile_eligible"] = sample["nuclei"] >= config["thresholds"]["primary_min_nuclei"]
        sample["sensitivity_profile_eligible"] = sample["nuclei"] >= config["thresholds"]["sensitivity_min_nuclei"]
        sample_path = broad_count_dir / f"{network}.samples.tsv"
        counts_path = broad_count_dir / f"{network}.counts.tsv.gz"
        count_frame = pd.DataFrame(direct_broad_counts[group_rows].T, columns=sample["pseudobulk_id"])
        count_frame.insert(0, "source_symbol", genes)
        count_frame.insert(0, "feature_index", feature_index)
        atomic_write_tsv(count_frame, counts_path)
        atomic_write_tsv(sample, sample_path)
        declared_shards.extend([counts_path, sample_path])
        shard_rows.append({
            "shard_type": "direct_broad",
            "context_id": network,
            "scientific_label": network,
            "broad_network": network,
            "counts_path": str(counts_path.relative_to(project_root)),
            "samples_path": str(sample_path.relative_to(project_root)),
            "features": n_features,
            "samples": n_donors,
            "counts_bytes": counts_path.stat().st_size,
            "counts_sha256": sha256_file(counts_path),
            "samples_sha256": sha256_file(sample_path),
        })
        del count_frame

    fine_total = int(fine_counts.sum(dtype=np.int64))
    broad_total = int(direct_broad_counts.sum(dtype=np.int64))
    processed_fine_nuclei = np.bincount(fine_codes[fine_codes >= 0], minlength=n_fine_groups)
    expected_fine_nuclei = profiles.sort_values("fine_group_code")["nuclei"].to_numpy()
    conservation = pd.DataFrame([
        {"quantity": "source_umi_all_visited_rows", "value": source_total, "expected": expected["all_visited_umis"]},
        {"quantity": "source_umi_selected_nuclei", "value": selected_total, "expected": expected["selected_umis"]},
        {"quantity": "fine_pseudobulk_umi_total", "value": fine_total, "expected": expected["selected_umis"]},
        {"quantity": "direct_broad_pseudobulk_umi_total", "value": broad_total, "expected": expected["selected_umis"]},
    ])
    checks = [
        ("all_observations_visited_once", next_observation == expected["observations"], next_observation, expected["observations"], ""),
        ("all_source_umi_total", source_total == expected["all_visited_umis"], source_total, expected["all_visited_umis"], ""),
        ("selected_nuclei_processed", selected_nuclei_processed == expected["selected_nuclei"], selected_nuclei_processed, expected["selected_nuclei"], ""),
        ("selected_umi_total", selected_total == expected["selected_umis"], selected_total, expected["selected_umis"], ""),
        ("fine_umi_conservation", fine_total == selected_total, fine_total, selected_total, ""),
        ("direct_broad_umi_conservation", broad_total == selected_total, broad_total, selected_total, ""),
        ("fine_direct_broad_exact_reconciliation", reconcile_equal, mismatch_cells, 0, ""),
        ("fine_counts_nonnegative", bool(np.all(fine_counts >= 0)), int(fine_counts.min()), ">=0", ""),
        ("broad_counts_nonnegative", bool(np.all(direct_broad_counts >= 0)), int(direct_broad_counts.min()), ">=0", ""),
        ("profile_nucleus_reconciliation", np.array_equal(processed_fine_nuclei, expected_fine_nuclei), int(np.count_nonzero(processed_fine_nuclei != expected_fine_nuclei)), 0, ""),
        ("fine_shard_count", sum(row["shard_type"] == "fine_supertype" for row in shard_rows) == 129, sum(row["shard_type"] == "fine_supertype" for row in shard_rows), 129, ""),
        ("broad_shard_count", sum(row["shard_type"] == "direct_broad" for row in shard_rows) == 7, sum(row["shard_type"] == "direct_broad" for row in shard_rows), 7, ""),
    ]
    checks_table = checks_frame(checks)
    paths = {
        "manifest": output_dir / "pseudobulk_shard_manifest.tsv",
        "ledger": output_dir / "block_ledger.tsv",
        "conservation": output_dir / "count_conservation.tsv",
        "reconciliation": output_dir / "fine_broad_reconciliation.tsv",
        "checks": output_dir / "pseudobulk_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(pd.DataFrame(shard_rows), paths["manifest"])
    atomic_write_tsv(pd.DataFrame(ledger_rows), paths["ledger"])
    atomic_write_tsv(conservation, paths["conservation"])
    atomic_write_tsv(pd.DataFrame(reconciliation_rows), paths["reconciliation"])
    atomic_write_tsv(checks_table, paths["checks"])
    declared = declared_shards + [paths[key] for key in ["manifest", "ledger", "conservation", "reconciliation", "checks"]]
    write_artifacts(declared, project_root, paths["artifacts"])
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH05", state, project_root, config_path, started, failed,
        observations_visited=next_observation,
        selected_nuclei=selected_nuclei_processed,
        source_umi_total=source_total,
        selected_umi_total=selected_total,
        fine_pseudobulk_umi_total=fine_total,
        direct_broad_umi_total=broad_total,
        blocks_completed=blocks_completed,
        streaming_seconds=streaming_seconds,
        elapsed_seconds=time.perf_counter() - wall_start,
        fine_group_code_sha256=fine_code_sha,
        direct_broad_group_code_sha256=broad_code_sha,
        feature_order_sha256=feature_sha,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH05 status: {state}; streaming={streaming_seconds/60:.1f} min; total={(time.perf_counter()-wall_start)/60:.1f} min")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
