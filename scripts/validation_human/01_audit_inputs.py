#!/usr/bin/env python3
"""VH01: structural and semantic audit of SEA-AD H5AD and metadata CSV."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from seaad_common import (
    artifact_manifest,
    atomic_write_tsv,
    categorical_count_table,
    checks_frame,
    decode_scalar,
    decode_strings,
    load_config,
    parse_config_cli,
    phase_output_dir,
    repo_path,
    require_validated_status,
    sampled_dataset_digest,
    sha256_strings,
    status_frame,
    utc_now,
)


def scan_csv(path: Path) -> dict:
    digest = hashlib.sha256()
    line_count = 0
    first = None
    second = None
    last = None
    with path.open("rb") as handle:
        for line in handle:
            digest.update(line)
            line_count += 1
            if first is None:
                first = line
            elif second is None:
                second = line
            last = line
    if first is None or second is None or last is None:
        raise ValueError("Metadata CSV does not contain a header and data rows")
    header = next(csv.reader([first.decode("utf-8-sig").rstrip("\r\n")]))
    first_row = next(csv.reader([second.decode("utf-8").rstrip("\r\n")]))
    last_row = next(csv.reader([last.decode("utf-8").rstrip("\r\n")]))
    return {
        "line_count": line_count,
        "header": header,
        "first_id": first_row[0],
        "last_id": last_row[0],
        "sha256": digest.hexdigest(),
    }


def main() -> int:
    args = parse_config_cli("VH01: audit SEA-AD H5AD and CSV")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    require_validated_status(output_root / "00_environment/status.tsv")
    output_dir = phase_output_dir(output_root, "01_audit")
    h5ad_path = repo_path(project_root, config["inputs"]["h5ad"])
    csv_path = repo_path(project_root, config["inputs"]["metadata_csv"])
    expected = config["expected"]

    checks = []
    structure_rows = []
    schema_rows = []
    category_tables = []
    csv_info = scan_csv(csv_path)

    with h5py.File(h5ad_path, "r") as h5:
        x = h5["X"]
        umi = h5[config["assay"]["umi_layer"]]
        x_shape = tuple(int(value) for value in x.attrs["shape"])
        umi_shape = tuple(int(value) for value in umi.attrs["shape"])
        n_obs, n_genes = umi_shape
        checks.extend(
            [
                ("observation_count", n_obs == expected["observations"], n_obs, expected["observations"], ""),
                ("gene_count", n_genes == expected["genes"], n_genes, expected["genes"], ""),
                ("X_encoding", decode_scalar(x.attrs.get("encoding-type", "")) == "csr_matrix", decode_scalar(x.attrs.get("encoding-type", "")), "csr_matrix", ""),
                ("UMI_encoding", decode_scalar(umi.attrs.get("encoding-type", "")) == "csr_matrix", decode_scalar(umi.attrs.get("encoding-type", "")), "csr_matrix", ""),
                ("X_UMI_shape_equal", x_shape == umi_shape, str((x_shape, umi_shape)), "equal", ""),
            ]
        )
        normalization = decode_scalar(h5["uns/X_normalization"][()])
        checks.append(("X_normalization", normalization == "ln(UP10K+1)", normalization, "ln(UP10K+1)", ""))

        for object_name in ["X", config["assay"]["umi_layer"]]:
            group = h5[object_name]
            for member in ["data", "indices", "indptr"]:
                dataset = group[member]
                structure_rows.append(
                    {
                        "object": object_name,
                        "member": member,
                        "shape": "x".join(map(str, dataset.shape)),
                        "dtype": str(dataset.dtype),
                        "compression": dataset.compression or "none",
                        "chunks": "x".join(map(str, dataset.chunks or ())),
                    }
                )

        x_indptr = x["indptr"][...]
        umi_indptr = umi["indptr"][...]
        indptr_equal = np.array_equal(x_indptr, umi_indptr)
        checks.append(("X_UMI_indptr_equal", indptr_equal, indptr_equal, True, "full indptr comparison"))

        nnz = int(umi["data"].shape[0])
        sample_positions = np.unique(np.linspace(0, nnz - 1, 4096, dtype=np.int64))
        x_indices_sample = x["indices"][sample_positions]
        umi_indices_sample = umi["indices"][sample_positions]
        indices_equal = np.array_equal(x_indices_sample, umi_indices_sample)
        checks.append(("X_UMI_indices_sample_equal", indices_equal, indices_equal, True, "4096 deterministic positions"))
        umi_values = umi["data"][sample_positions]
        integer_raw = bool(np.all(np.isfinite(umi_values)) and np.all(umi_values >= 0) and np.all(umi_values == np.floor(umi_values)))
        checks.append(("UMI_sample_nonnegative_integer", integer_raw, integer_raw, True, "4096 deterministic positions"))
        valid_indices = bool(np.all(umi_indices_sample >= 0) and np.all(umi_indices_sample < n_genes))
        checks.append(("UMI_sample_indices_in_range", valid_indices, valid_indices, True, ""))

        obs = h5["obs"]
        obs_index_name = decode_scalar(obs.attrs["_index"])
        obs_index = decode_strings(obs[obs_index_name][...])
        var = h5["var"]
        var_index_name = decode_scalar(var.attrs["_index"])
        genes = decode_strings(var[var_index_name][...])
        gene_ids = decode_strings(var["gene_ids"][...])
        checks.extend(
            [
                ("unique_observation_ids", len(np.unique(obs_index)) == n_obs, len(np.unique(obs_index)), n_obs, ""),
                ("unique_gene_symbols", len(np.unique(genes)) == n_genes, len(np.unique(genes)), n_genes, ""),
                ("gene_ids_duplicate_symbols", np.array_equal(genes, gene_ids), bool(np.array_equal(genes, gene_ids)), True, ""),
            ]
        )

        column_order = [decode_scalar(value) for value in obs.attrs["column-order"]]
        checks.extend(
            [
                ("csv_column_count", len(csv_info["header"]) == expected["csv_columns"], len(csv_info["header"]), expected["csv_columns"], ""),
                ("csv_row_count", csv_info["line_count"] - 1 == n_obs, csv_info["line_count"] - 1, n_obs, ""),
                ("csv_h5ad_header_equal", csv_info["header"] == [obs_index_name] + column_order, bool(csv_info["header"] == [obs_index_name] + column_order), True, ""),
                ("csv_h5ad_first_id_equal", csv_info["first_id"] == obs_index[0], csv_info["first_id"], obs_index[0], ""),
                ("csv_h5ad_last_id_equal", csv_info["last_id"] == obs_index[-1], csv_info["last_id"], obs_index[-1], ""),
            ]
        )

        required_fields = [
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
            "Class",
            "Subclass",
            "Supertype",
        ]
        for field in column_order:
            h5_object = obs.get(field)
            schema_rows.append(
                {
                    "field": field,
                    "required": field in required_fields,
                    "encoded_object_present": h5_object is not None,
                    "encoding": "categorical" if h5_object is not None and "categories" in h5_object.attrs else ("array" if h5_object is not None else "path-escaped-column"),
                    "dtype": str(h5_object.dtype) if isinstance(h5_object, h5py.Dataset) else "",
                }
            )
        for field in required_fields:
            present = field in obs
            checks.append((f"required_obs_field_{field}", present, present, True, ""))
            if present:
                category_tables.append(categorical_count_table(h5, field))

        structure_digest_payload = {
            "shape": umi_shape,
            "nnz": nnz,
            "x_normalization": normalization,
            "obs_index_sha256": sha256_strings(obs_index),
            "feature_order_sha256": sha256_strings(genes),
            "umi_data_sample_sha256": sampled_dataset_digest(umi["data"]),
            "umi_indices_sample_sha256": sampled_dataset_digest(umi["indices"]),
            "umi_indptr_sha256": hashlib.sha256(umi_indptr.tobytes()).hexdigest(),
        }
        structure_digest = hashlib.sha256(
            json.dumps(structure_digest_payload, sort_keys=True).encode()
        ).hexdigest()

    gene_inventory = pd.DataFrame(
        {
            "feature_index": np.arange(len(genes), dtype=np.int64),
            "gene": genes,
            "gene_ids": gene_ids,
        }
    )
    csv_alignment = pd.DataFrame(
        [
            {
                "csv_columns": len(csv_info["header"]),
                "csv_data_rows": csv_info["line_count"] - 1,
                "first_nucleus_id": csv_info["first_id"],
                "last_nucleus_id": csv_info["last_id"],
                "csv_sha256": csv_info["sha256"],
                "h5ad_structure_digest": structure_digest,
            }
        ]
    )
    structure = pd.DataFrame(structure_rows)
    schema = pd.DataFrame(schema_rows)
    categories = pd.concat(category_tables, ignore_index=True)
    checks_table = checks_frame(checks)

    paths = {
        "structure": output_dir / "h5ad_structure.tsv",
        "schema": output_dir / "obs_schema.tsv",
        "categories": output_dir / "category_inventory.tsv",
        "genes": output_dir / "gene_inventory_raw.tsv",
        "alignment": output_dir / "csv_h5ad_alignment.tsv",
        "checks": output_dir / "audit_checks.tsv",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_write_tsv(structure, paths["structure"])
    atomic_write_tsv(schema, paths["schema"])
    atomic_write_tsv(categories, paths["categories"])
    atomic_write_tsv(gene_inventory, paths["genes"])
    atomic_write_tsv(csv_alignment, paths["alignment"])
    atomic_write_tsv(checks_table, paths["checks"])

    artifacts = artifact_manifest(
        [paths[key] for key in ["structure", "schema", "categories", "genes", "alignment", "checks"]],
        project_root,
    )
    input_records = pd.DataFrame(
        [
            {
                "artifact": h5ad_path.name,
                "path": str(h5ad_path.relative_to(project_root)),
                "bytes": h5ad_path.stat().st_size,
                "sha256": f"sampled_structure:{structure_digest}",
            },
            {
                "artifact": csv_path.name,
                "path": str(csv_path.relative_to(project_root)),
                "bytes": csv_path.stat().st_size,
                "sha256": csv_info["sha256"],
            },
        ]
    )
    artifacts = pd.concat([input_records, artifacts], ignore_index=True)
    atomic_write_tsv(artifacts, paths["artifacts"])

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH01",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        observations=n_obs,
        genes=n_genes,
        umi_nnz=nnz,
        csv_rows=csv_info["line_count"] - 1,
        h5ad_structure_digest=structure_digest,
        feature_order_sha256=sha256_strings(genes),
        observation_order_sha256=sha256_strings(obs_index),
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH01 status: {validation_status}")
    print(f"Observations: {n_obs}; genes: {n_genes}; UMI nnz: {nnz}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
