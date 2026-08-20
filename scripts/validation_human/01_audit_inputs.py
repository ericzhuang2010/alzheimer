#!/usr/bin/env python3
"""VH01: authenticate and semantically audit the SEA-AD H5AD/CSV pair."""

from __future__ import annotations

import hashlib
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from seaad_common import (
    atomic_write_tsv,
    categorical_inventory,
    checks_frame,
    decode_scalar,
    decode_strings,
    load_config,
    parse_config_cli,
    phase_dir,
    read_obs_slice,
    repo_path,
    require_phase,
    sha256_file,
    sha256_strings,
    status_frame,
    structure_digest,
    utc_now,
    write_artifacts,
)


def canonical_strings(values, kind: str) -> np.ndarray:
    if kind == "bool":
        return np.asarray([
            "<NA>" if value is None or str(value).strip() == "" else
            ("TRUE" if str(value).strip().lower() in {"true", "t", "1"} else "FALSE")
            for value in values
        ], dtype=object)
    if kind == "numeric":
        numeric = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
        return np.asarray([
            "<NA>" if not np.isfinite(value) else format(float(value), ".17g")
            for value in numeric
        ], dtype=object)
    return np.asarray([
        "<NA>" if value is None or str(value) in {"", "nan", "NA"} else str(value)
        for value in values
    ], dtype=object)


def main() -> int:
    args = parse_config_cli("VH01: audit SEA-AD raw inputs")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_phase(output_root, "00_environment")
    output_dir = phase_dir(output_root, "01_audit")
    expected = config["expected_identity"]
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    csv_path = repo_path(project_root, config["inputs"]["metadata_csv"])

    checks = []
    structure_rows = []
    schema_rows = []
    category_frames = []
    critical_fields = [
        config["cohort"]["donor_field"],
        config["cohort"]["neurotypical_reference_field"],
        config["cohort"]["diagnosis_field"],
        config["cohort"]["sex_field"],
        config["cohort"]["apoe_field"],
        config["cohort"]["age_field"],
        config["cohort"]["pmi_field"],
        config["cohort"]["study_field"],
        config["cohort"]["pathology_field"],
        config["assay"]["method_field"],
        config["assay"]["used_field"],
        "Class", "Subclass", "Supertype",
    ]

    csv_sha = sha256_file(csv_path)
    full_h5ad_sha = sha256_file(h5ad_path) if config["streaming"]["full_h5ad_sha256"] else ""
    with h5py.File(h5ad_path, "r") as h5:
        x = h5["X"]
        umi = h5[config["assay"]["umi_layer"]]
        x_shape = tuple(int(value) for value in x.attrs["shape"])
        umi_shape = tuple(int(value) for value in umi.attrs["shape"])
        n_obs, n_features = umi_shape
        nnz = int(umi["data"].shape[0])
        normalization = decode_scalar(h5["uns/X_normalization"][()])
        checks.extend([
            ("h5ad_bytes", h5ad_path.stat().st_size == expected["h5ad_bytes"], h5ad_path.stat().st_size, expected["h5ad_bytes"], ""),
            ("metadata_csv_bytes", csv_path.stat().st_size == expected["metadata_csv_bytes"], csv_path.stat().st_size, expected["metadata_csv_bytes"], ""),
            ("metadata_csv_sha256", csv_sha == expected["metadata_csv_sha256"], csv_sha, expected["metadata_csv_sha256"], ""),
            ("observation_count", n_obs == expected["observations"], n_obs, expected["observations"], ""),
            ("feature_count", n_features == expected["features"], n_features, expected["features"], ""),
            ("umi_nnz", nnz == expected["umi_nnz"], nnz, expected["umi_nnz"], ""),
            ("X_UMI_shape_equal", x_shape == umi_shape, str((x_shape, umi_shape)), "equal", ""),
            ("X_encoding_csr", decode_scalar(x.attrs.get("encoding-type", "")) == "csr_matrix", decode_scalar(x.attrs.get("encoding-type", "")), "csr_matrix", ""),
            ("UMI_encoding_csr", decode_scalar(umi.attrs.get("encoding-type", "")) == "csr_matrix", decode_scalar(umi.attrs.get("encoding-type", "")), "csr_matrix", ""),
        ])
        for object_name in ["X", config["assay"]["umi_layer"]]:
            group = h5[object_name]
            for member in ["data", "indices", "indptr"]:
                dataset = group[member]
                structure_rows.append({
                    "object": object_name,
                    "member": member,
                    "shape": "x".join(map(str, dataset.shape)),
                    "dtype": str(dataset.dtype),
                    "compression": dataset.compression or "none",
                    "chunks": "x".join(map(str, dataset.chunks or ())),
                })

        x_indptr = x["indptr"][...]
        umi_indptr = umi["indptr"][...]
        checks.append(("X_UMI_indptr_equal", np.array_equal(x_indptr, umi_indptr), np.array_equal(x_indptr, umi_indptr), True, "full comparison"))
        positions = np.unique(np.linspace(0, nnz - 1, 4096, dtype=np.int64))
        x_indices = x["indices"][positions]
        umi_indices = umi["indices"][positions]
        raw_values = umi["data"][positions]
        checks.extend([
            ("X_UMI_indices_sample_equal", np.array_equal(x_indices, umi_indices), np.array_equal(x_indices, umi_indices), True, "4096 deterministic entries"),
            ("UMI_sample_integer_nonnegative", bool(np.all(np.isfinite(raw_values)) and np.all(raw_values >= 0) and np.all(raw_values == np.floor(raw_values))), True, True, "4096 deterministic entries"),
            ("UMI_sample_indices_in_range", bool(np.all((umi_indices >= 0) & (umi_indices < n_features))), True, True, ""),
        ])

        obs = h5["obs"]
        obs_index_name = decode_scalar(obs.attrs["_index"])
        obs_ids = decode_strings(obs[obs_index_name][...])
        var = h5["var"]
        var_index_name = decode_scalar(var.attrs["_index"])
        features = decode_strings(var[var_index_name][...])
        embedded_ids = decode_strings(var["gene_ids"][...])
        observation_sha = sha256_strings(obs_ids)
        feature_sha = sha256_strings(features)
        struct_sha, struct_payload = structure_digest(umi, normalization, obs_ids, features)
        checks.extend([
            ("observation_ids_unique", len(np.unique(obs_ids)) == n_obs, len(np.unique(obs_ids)), n_obs, ""),
            ("source_features_unique", len(np.unique(features)) == n_features, len(np.unique(features)), n_features, ""),
            ("embedded_gene_ids_equal_symbols", np.array_equal(features, embedded_ids), np.array_equal(features, embedded_ids), True, "embedded field is not treated as stable Ensembl identity"),
            ("observation_order_digest", observation_sha == expected["observation_order_sha256"], observation_sha, expected["observation_order_sha256"], ""),
            ("feature_order_digest", feature_sha == expected["feature_order_sha256"], feature_sha, expected["feature_order_sha256"], ""),
            ("historical_structure_digest", struct_sha == expected["h5ad_structure_digest"], struct_sha, expected["h5ad_structure_digest"], "historical sampled/structural digest"),
        ])

        column_order = [decode_scalar(value) for value in obs.attrs["column-order"]]
        csv_header = pd.read_csv(csv_path, nrows=0).columns.tolist()
        checks.extend([
            ("csv_column_count", len(csv_header) == expected["csv_columns"], len(csv_header), expected["csv_columns"], ""),
            ("csv_h5ad_header_equal", csv_header == [obs_index_name] + column_order, csv_header == [obs_index_name] + column_order, True, ""),
        ])
        for field in column_order:
            dataset = obs.get(field)
            schema_rows.append({
                "field": field,
                "required": field in critical_fields,
                "object_present": dataset is not None,
                "encoding": "categorical" if dataset is not None and dataset.attrs.get("categories") is not None else "array",
                "dtype": str(dataset.dtype) if dataset is not None else "",
            })
        for field in critical_fields:
            present = field in obs
            checks.append((f"required_obs_field:{field}", present, present, True, ""))
            if present:
                category_frames.append(categorical_inventory(h5, field))

        usecols = [obs_index_name] + critical_fields
        h5_digests = {field: hashlib.sha256() for field in usecols}
        csv_digests = {field: hashlib.sha256() for field in usecols}
        mismatches = {field: 0 for field in usecols}
        rows_seen = 0
        chunk_rows = int(config["streaming"]["csv_chunk_rows"])
        for chunk in pd.read_csv(csv_path, usecols=usecols, dtype=str, keep_default_na=False, chunksize=chunk_rows):
            start = rows_seen
            end = start + len(chunk)
            for field in usecols:
                if field == obs_index_name:
                    h5_values = obs_ids[start:end]
                    kind = "string"
                else:
                    dataset = obs[field]
                    h5_values = read_obs_slice(h5, field, start, end)
                    kind = "bool" if dataset.dtype.kind == "b" else (
                        "numeric" if dataset.attrs.get("categories") is None and dataset.dtype.kind in "fiu" else "string"
                    )
                left = canonical_strings(h5_values, kind)
                right = canonical_strings(chunk[field].to_numpy(), kind)
                mismatches[field] += int(np.sum(left != right))
                h5_digests[field].update(("\n".join(left.tolist()) + "\n").encode())
                csv_digests[field].update(("\n".join(right.tolist()) + "\n").encode())
            rows_seen = end

    checks.extend([
        ("csv_row_count", rows_seen == expected["observations"], rows_seen, expected["observations"], ""),
        ("critical_metadata_exact_alignment", sum(mismatches.values()) == 0, sum(mismatches.values()), 0, ""),
    ])
    field_checksums = pd.DataFrame([
        {
            "field": field,
            "rows_compared": rows_seen,
            "mismatch_count": mismatches[field],
            "h5ad_canonical_sha256": h5_digests[field].hexdigest(),
            "csv_canonical_sha256": csv_digests[field].hexdigest(),
            "checksums_equal": h5_digests[field].hexdigest() == csv_digests[field].hexdigest(),
        }
        for field in usecols
    ])

    input_identity = pd.DataFrame([
        {"input": "h5ad", "path": str(h5ad_path.relative_to(project_root)), "bytes": h5ad_path.stat().st_size, "digest_algorithm": "sha256", "digest_scope": "full_file", "digest_value": full_h5ad_sha},
        {"input": "h5ad", "path": str(h5ad_path.relative_to(project_root)), "bytes": h5ad_path.stat().st_size, "digest_algorithm": "sha256", "digest_scope": "historical_sampled_structure", "digest_value": struct_sha},
        {"input": "metadata_csv", "path": str(csv_path.relative_to(project_root)), "bytes": csv_path.stat().st_size, "digest_algorithm": "sha256", "digest_scope": "full_file", "digest_value": csv_sha},
    ])
    genes = pd.DataFrame({
        "feature_index": np.arange(len(features), dtype=np.int64),
        "source_symbol": features,
        "embedded_gene_id": embedded_ids,
    })
    alignment = field_checksums[["field", "rows_compared", "mismatch_count", "checksums_equal"]].copy()
    structure = pd.DataFrame(structure_rows)
    structure["historical_structure_digest"] = struct_sha
    schema = pd.DataFrame(schema_rows)
    categories = pd.concat(category_frames, ignore_index=True)
    checks_table = checks_frame(checks)

    paths = {
        "identity": output_dir / "input_identity.tsv",
        "structure": output_dir / "h5ad_structure.tsv",
        "schema": output_dir / "obs_schema.tsv",
        "categories": output_dir / "category_inventory.tsv",
        "genes": output_dir / "gene_inventory_raw.tsv",
        "alignment": output_dir / "csv_h5ad_alignment.tsv",
        "field_checksums": output_dir / "critical_metadata_field_checksums.tsv",
        "obs_checksum": output_dir / "observation_order_checksum.tsv",
        "checks": output_dir / "audit_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(input_identity, paths["identity"])
    atomic_write_tsv(structure, paths["structure"])
    atomic_write_tsv(schema, paths["schema"])
    atomic_write_tsv(categories, paths["categories"])
    atomic_write_tsv(genes, paths["genes"])
    atomic_write_tsv(alignment, paths["alignment"])
    atomic_write_tsv(field_checksums, paths["field_checksums"])
    atomic_write_tsv(pd.DataFrame([{"observations": n_obs, "observation_order_sha256": observation_sha}]), paths["obs_checksum"])
    atomic_write_tsv(checks_table, paths["checks"])
    declared = [paths[key] for key in ["identity", "structure", "schema", "categories", "genes", "alignment", "field_checksums", "obs_checksum", "checks"]]
    write_artifacts(declared, project_root, paths["artifacts"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH01", state, project_root, config_path, started, failed,
        observations=n_obs, features=n_features, umi_nnz=nnz,
        metadata_csv_rows=rows_seen, h5ad_full_sha256=full_h5ad_sha,
        h5ad_structure_digest=struct_sha,
        observation_order_sha256=observation_sha,
        feature_order_sha256=feature_sha,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH01 status: {state}; compared {rows_seen} CSV/H5AD rows")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
