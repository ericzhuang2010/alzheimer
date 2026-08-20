#!/usr/bin/env python3
"""VH05: resumably stream the raw SEA-AD UMI CSR matrix into broad pseudobulk."""

from __future__ import annotations

import os
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from seaad_common import (
    artifact_manifest,
    atomic_save_npz,
    atomic_write_tsv,
    checks_frame,
    load_config,
    parse_config_cli,
    phase_output_dir,
    repo_path,
    require_validated_status,
    sha256_array,
    sha256_file,
    sha256_strings,
    status_frame,
    utc_now,
)


def add_arguments(parser):
    parser.add_argument("--block-observations", type=int, default=None)
    parser.add_argument("--max-observations", type=int, default=None)
    parser.add_argument("--checkpoint-every-blocks", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--resume", action="store_true")


def save_checkpoint(
    path,
    counts,
    next_observation,
    source_umi_total,
    selected_source_umi_total,
    selected_nuclei_processed,
    blocks_completed,
    group_code_sha256,
    feature_order_sha256,
):
    atomic_save_npz(
        path,
        counts=counts,
        next_observation=np.asarray([next_observation], dtype=np.int64),
        source_umi_total=np.asarray([source_umi_total], dtype=np.int64),
        selected_source_umi_total=np.asarray([selected_source_umi_total], dtype=np.int64),
        selected_nuclei_processed=np.asarray([selected_nuclei_processed], dtype=np.int64),
        blocks_completed=np.asarray([blocks_completed], dtype=np.int64),
        group_code_sha256=np.asarray([group_code_sha256]),
        feature_order_sha256=np.asarray([feature_order_sha256]),
    )


def main() -> int:
    args = parse_config_cli("VH05: stream SEA-AD UMI pseudobulk", add_arguments)
    started_at = utc_now()
    start_wall = time.perf_counter()
    config, config_path, project_root, output_root = load_config(args.config)
    require_validated_status(output_root / "00_environment/status.tsv")
    require_validated_status(output_root / "03_genes/status.tsv")
    vh04_status = require_validated_status(output_root / "04_cell_manifest/status.tsv")

    output_dir = phase_output_dir(output_root, "05_pseudobulk", args.output_dir)
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint_latest.npz"
    status_path = output_dir / "status.tsv"

    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    group_codes = np.load(output_root / "04_cell_manifest/nucleus_to_group_code.npy")
    group_manifest = pd.read_csv(
        output_root / "04_cell_manifest/pseudobulk_group_manifest.tsv", sep="\t"
    ).sort_values("group_code")
    feature_order = pd.read_csv(output_root / "03_genes/feature_order.tsv", sep="\t")
    genes = feature_order["source_symbol"].astype(str).to_numpy()
    feature_order_sha256 = sha256_strings(genes)
    group_code_sha256 = sha256_array(group_codes)
    expected_group_sha = str(vh04_status.loc[0, "group_code_sha256"])
    if group_code_sha256 != expected_group_sha:
        raise ValueError("VH04 group-code checksum mismatch before streaming")

    block_observations = (
        args.block_observations
        if args.block_observations is not None
        else int(config["streaming"]["default_block_observations"])
    )
    checkpoint_every = (
        args.checkpoint_every_blocks
        if args.checkpoint_every_blocks is not None
        else int(config["streaming"]["checkpoint_every_blocks"])
    )
    if block_observations < 1 or checkpoint_every < 1:
        raise ValueError("Block and checkpoint intervals must be positive")

    with h5py.File(h5ad_path, "r") as h5:
        umi = h5[config["assay"]["umi_layer"]]
        n_observations, n_genes = (int(value) for value in umi.attrs["shape"])
        if group_codes.shape != (n_observations,):
            raise ValueError("VH04 group-code length does not match UMI rows")
        if len(genes) != n_genes:
            raise ValueError("VH03 feature order does not match UMI columns")
        n_groups = len(group_manifest)
        if group_manifest["group_code"].tolist() != list(range(n_groups)):
            raise ValueError("Pseudobulk group codes are not contiguous")

        target_observations = (
            n_observations
            if args.max_observations is None
            else min(int(args.max_observations), n_observations)
        )
        production_directory = output_dir == (output_root / "05_pseudobulk").resolve()
        production_run = production_directory and target_observations == n_observations

        if args.resume and production_run and status_path.exists():
            existing_status = pd.read_csv(status_path, sep="\t")
            if (
                len(existing_status) == 1
                and existing_status.loc[0, "validation_status"] == "validated_complete"
                and str(existing_status.loc[0, "config_sha256"])
                == sha256_file(config_path)
            ):
                print("VH05 is already validated_complete; no work repeated")
                return 0

        counts = np.zeros((n_groups, n_genes), dtype=np.int64)
        next_observation = 0
        source_umi_total = 0
        selected_source_umi_total = 0
        selected_nuclei_processed = 0
        blocks_completed = 0
        if args.resume and checkpoint_path.exists():
            with np.load(checkpoint_path, allow_pickle=False) as checkpoint:
                if str(checkpoint["group_code_sha256"][0]) != group_code_sha256:
                    raise ValueError("Checkpoint group-code checksum mismatch")
                if str(checkpoint["feature_order_sha256"][0]) != feature_order_sha256:
                    raise ValueError("Checkpoint feature-order checksum mismatch")
                counts = checkpoint["counts"].astype(np.int64, copy=False)
                next_observation = int(checkpoint["next_observation"][0])
                source_umi_total = int(checkpoint["source_umi_total"][0])
                selected_source_umi_total = int(checkpoint["selected_source_umi_total"][0])
                selected_nuclei_processed = int(checkpoint["selected_nuclei_processed"][0])
                blocks_completed = int(checkpoint["blocks_completed"][0])
            if counts.shape != (n_groups, n_genes):
                raise ValueError("Checkpoint count-matrix shape mismatch")
            if next_observation > target_observations:
                raise ValueError("Checkpoint is beyond requested observation limit")

        progress_rows = []
        existing_progress_path = output_dir / "block_progress.tsv"
        if args.resume and existing_progress_path.exists():
            existing_progress = pd.read_csv(existing_progress_path, sep="\t")
            progress_rows = existing_progress.to_dict("records")

        stream_start = time.perf_counter()
        while next_observation < target_observations:
            block_start_time = time.perf_counter()
            row_start = next_observation
            row_end = min(row_start + block_observations, target_observations)
            global_indptr = umi["indptr"][row_start : row_end + 1]
            nnz_start = int(global_indptr[0])
            nnz_end = int(global_indptr[-1])
            local_indptr = (global_indptr - nnz_start).astype(np.int32, copy=False)
            indices = umi["indices"][nnz_start:nnz_end].astype(np.int32, copy=False)
            raw_values = umi["data"][nnz_start:nnz_end]
            if not (
                np.all(np.isfinite(raw_values))
                and np.all(raw_values >= 0)
                and np.all(raw_values == np.floor(raw_values))
            ):
                raise ValueError(f"Invalid raw UMI value in rows {row_start}:{row_end}")
            if not (np.all(indices >= 0) and np.all(indices < n_genes)):
                raise ValueError(f"Invalid feature index in rows {row_start}:{row_end}")
            values = raw_values.astype(np.int64, copy=False)
            block_matrix = sparse.csr_matrix(
                (values, indices, local_indptr),
                shape=(row_end - row_start, n_genes),
                dtype=np.int64,
            )
            row_groups = group_codes[row_start:row_end]
            selected_local = np.flatnonzero(row_groups >= 0)
            selected_block_total = 0
            if selected_local.size:
                assignment = sparse.csr_matrix(
                    (
                        np.ones(selected_local.size, dtype=np.int8),
                        (
                            row_groups[selected_local].astype(np.int32, copy=False),
                            selected_local.astype(np.int32, copy=False),
                        ),
                    ),
                    shape=(n_groups, row_end - row_start),
                )
                aggregated = assignment @ block_matrix
                aggregated.sum_duplicates()
                aggregated_coo = aggregated.tocoo(copy=False)
                counts[aggregated_coo.row, aggregated_coo.col] += aggregated_coo.data
                selected_block_total = int(aggregated_coo.data.sum(dtype=np.int64))

            block_source_total = int(values.sum(dtype=np.int64))
            source_umi_total += block_source_total
            selected_source_umi_total += selected_block_total
            selected_nuclei_processed += int(selected_local.size)
            blocks_completed += 1
            next_observation = row_end
            block_seconds = time.perf_counter() - block_start_time
            progress_rows.append(
                {
                    "block": blocks_completed,
                    "row_start": row_start,
                    "row_end": row_end,
                    "observations": row_end - row_start,
                    "nnz": nnz_end - nnz_start,
                    "selected_nuclei": int(selected_local.size),
                    "source_umi_total": block_source_total,
                    "selected_source_umi_total": selected_block_total,
                    "block_seconds": block_seconds,
                    "observations_per_second": (row_end - row_start) / block_seconds,
                    "nnz_per_second": (nnz_end - nnz_start) / block_seconds,
                }
            )
            if blocks_completed % checkpoint_every == 0 or next_observation == target_observations:
                save_checkpoint(
                    checkpoint_path,
                    counts,
                    next_observation,
                    source_umi_total,
                    selected_source_umi_total,
                    selected_nuclei_processed,
                    blocks_completed,
                    group_code_sha256,
                    feature_order_sha256,
                )
                atomic_write_tsv(pd.DataFrame(progress_rows), existing_progress_path)
                print(
                    f"VH05 rows {next_observation}/{target_observations}; "
                    f"blocks {blocks_completed}; elapsed {(time.perf_counter()-stream_start)/60:.1f} min",
                    flush=True,
                )

    streaming_seconds = time.perf_counter() - stream_start
    output_start = time.perf_counter()
    processed_group_nuclei = np.bincount(
        group_codes[:target_observations][group_codes[:target_observations] >= 0],
        minlength=len(group_manifest),
    ).astype(np.int64)
    samples = group_manifest.copy()
    samples["nuclei_expected"] = samples["nuclei"].astype(np.int64)
    samples["nuclei_processed"] = processed_group_nuclei
    samples["library_size"] = counts.sum(axis=1, dtype=np.int64)
    samples["complete_profile"] = samples["nuclei_processed"].eq(samples["nuclei_expected"])

    counts_frame = pd.DataFrame(counts.T, columns=samples["pseudobulk_id"])
    counts_frame.insert(0, "gene", genes)
    counts_path = output_dir / "seaad_broad_pseudobulk_counts.tsv.gz"
    samples_path = output_dir / "seaad_broad_pseudobulk_samples.tsv"
    conservation_path = output_dir / "count_conservation.tsv"
    checks_path = output_dir / "pseudobulk_checks.tsv"
    artifacts_path = output_dir / "artifacts.tsv"
    atomic_write_tsv(counts_frame, counts_path)
    del counts_frame
    atomic_write_tsv(samples, samples_path)

    pseudobulk_total = int(counts.sum(dtype=np.int64))
    conservation = pd.DataFrame(
        [
            {"quantity": "source_umi_all_visited_rows", "value": source_umi_total},
            {"quantity": "source_umi_selected_nuclei", "value": selected_source_umi_total},
            {"quantity": "pseudobulk_umi_total", "value": pseudobulk_total},
            {"quantity": "selected_minus_pseudobulk", "value": selected_source_umi_total - pseudobulk_total},
        ]
    )
    atomic_write_tsv(conservation, conservation_path)

    full_rows_visited = next_observation == n_observations
    checks = [
        ("rows_visited_to_requested_limit", next_observation == target_observations, next_observation, target_observations, ""),
        ("selected_umi_conservation", selected_source_umi_total == pseudobulk_total, selected_source_umi_total - pseudobulk_total, 0, ""),
        ("counts_nonnegative", bool(np.all(counts >= 0)), int(counts.min()), ">=0", ""),
        ("group_code_checksum", group_code_sha256 == expected_group_sha, group_code_sha256, expected_group_sha, ""),
        ("feature_order_checksum", feature_order_sha256 == str(feature_order["feature_order_sha256"].iloc[0]), feature_order_sha256, str(feature_order["feature_order_sha256"].iloc[0]), ""),
        ("all_profiles_complete_if_production", (not production_run) or bool(samples["complete_profile"].all()), int(samples["complete_profile"].sum()), len(samples) if production_run else "not_applicable", ""),
        ("all_input_rows_visited_if_production", (not production_run) or full_rows_visited, next_observation, n_observations if production_run else "not_applicable", ""),
    ]
    checks_table = checks_frame(checks)
    atomic_write_tsv(checks_table, checks_path)
    artifacts = artifact_manifest(
        [counts_path, samples_path, existing_progress_path, checkpoint_path, conservation_path, checks_path],
        project_root,
    )
    atomic_write_tsv(artifacts, artifacts_path)

    output_seconds = time.perf_counter() - output_start
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    if failed:
        validation_status = "failed"
    elif production_run:
        validation_status = "validated_complete"
    else:
        validation_status = "smoke_complete"
    safety = float(config["streaming"]["benchmark_safety_multiplier"])
    projected_full_hours = (
        (streaming_seconds / max(1, target_observations - (0 if not args.resume else 0)))
        * n_observations
        * safety
        + output_seconds
    ) / 3600
    status = status_frame(
        "VH05",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        production_run=production_run,
        observations_processed=next_observation,
        observations_total=n_observations,
        selected_nuclei_processed=selected_nuclei_processed,
        blocks_completed=blocks_completed,
        source_umi_total=source_umi_total,
        selected_source_umi_total=selected_source_umi_total,
        pseudobulk_umi_total=pseudobulk_total,
        streaming_seconds=streaming_seconds,
        output_seconds=output_seconds,
        elapsed_seconds=time.perf_counter() - start_wall,
        projected_full_hours_conservative=projected_full_hours,
        block_observations=block_observations,
        feature_order_sha256=feature_order_sha256,
        group_code_sha256=group_code_sha256,
    )
    atomic_write_tsv(status, status_path)
    print(
        f"VH05 status: {validation_status}; streaming {streaming_seconds:.1f}s; "
        f"conservative full projection {projected_full_hours:.2f}h"
    )
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
