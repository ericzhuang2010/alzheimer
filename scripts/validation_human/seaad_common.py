#!/usr/bin/env python3
"""Shared safety, HDF5, provenance, and atomic-output helpers for SEA-AD."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import h5py
import numpy as np
import pandas as pd
import yaml


STATUS_SCHEMA = "seaad_fine_phase_status_v2"


def parse_config_cli(description: str, add_arguments=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", required=True, help="Frozen SEA-AD YAML config")
    if add_arguments:
        add_arguments(parser)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(path: str | Path) -> tuple[dict[str, Any], Path, Path, Path]:
    config_path = Path(path).expanduser().resolve(strict=True)
    with config_path.open("rt", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    invocation_root = Path.cwd().resolve(strict=True)
    configured_root = Path(config.get("project_root", "."))
    project_root = (
        configured_root.resolve(strict=True)
        if configured_root.is_absolute()
        else (invocation_root / configured_root).resolve(strict=True)
    )
    output_rel = Path(config["output_root"])
    if output_rel.is_absolute() or ".." in output_rel.parts:
        raise ValueError("output_root must be a safe project-relative path")
    output_root = (project_root / output_rel).resolve(strict=False)
    required = (project_root / "results" / "validation_human").resolve(strict=False)
    if output_root != required:
        raise ValueError(f"output_root must resolve exactly to {required}")
    return config, config_path, project_root, output_root


def repo_path(project_root: Path, value: str | Path, must_exist: bool = True) -> Path:
    raw = Path(value)
    if ".." in raw.parts:
        raise ValueError(f"Repository path may not contain '..': {raw}")
    candidate = raw if raw.is_absolute() else project_root / raw
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {resolved}") from exc
    return resolved


def phase_dir(output_root: Path, name: str) -> Path:
    if not name or ".." in Path(name).parts or Path(name).is_absolute():
        raise ValueError(f"Unsafe phase directory: {name}")
    output_root.mkdir(parents=True, exist_ok=True)
    root = output_root.resolve(strict=True)
    candidate = (root / name).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Phase directory escapes validation root: {candidate}") from exc
    candidate.mkdir(parents=True, exist_ok=True)
    if candidate.is_symlink():
        raise ValueError(f"Phase directory may not be a symlink: {candidate}")
    return candidate


def sha256_file(path: str | Path, block_bytes: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(block_bytes):
            digest.update(block)
    return digest.hexdigest()


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8", errors="strict"))
        digest.update(bytes([10]))
    return digest.hexdigest()


def sha256_array(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode())
    digest.update(str(array.shape).encode())
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def sampled_dataset_digest(dataset: h5py.Dataset, sample_count: int = 4096) -> str:
    length = int(dataset.shape[0])
    if length == 0:
        return hashlib.sha256(b"empty").hexdigest()
    positions = np.unique(
        np.linspace(0, length - 1, min(sample_count, length), dtype=np.int64)
    )
    digest = hashlib.sha256()
    digest.update(str(dataset.shape).encode())
    digest.update(str(dataset.dtype).encode())
    for position in positions:
        digest.update(np.asarray(dataset[int(position)]).tobytes())
    return digest.hexdigest()


def decode_scalar(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, (bytes, np.bytes_)) else str(value)


def decode_strings(values: Any) -> np.ndarray:
    return np.asarray([decode_scalar(value) for value in np.asarray(values)], dtype=object)


def read_categorical_codes(h5: h5py.File, field: str):
    dataset = h5["obs"][field]
    reference = dataset.attrs.get("categories")
    if reference is None:
        return None
    return dataset[...], decode_strings(h5[reference][...])


def read_obs_values(h5: h5py.File, field: str) -> np.ndarray:
    encoded = read_categorical_codes(h5, field)
    if encoded is None:
        values = h5["obs"][field][...]
        return decode_strings(values) if values.dtype.kind in {"S", "O", "U"} else values
    codes, categories = encoded
    result = np.empty(codes.shape, dtype=object)
    valid = codes >= 0
    result[~valid] = None
    result[valid] = categories[codes[valid].astype(np.int64)]
    return result


def read_obs_slice(h5: h5py.File, field: str, start: int, end: int) -> np.ndarray:
    dataset = h5["obs"][field]
    reference = dataset.attrs.get("categories")
    values = dataset[start:end]
    if reference is None:
        return decode_strings(values) if values.dtype.kind in {"S", "O", "U"} else values
    categories = decode_strings(h5[reference][...])
    result = np.empty(values.shape, dtype=object)
    valid = values >= 0
    result[~valid] = None
    result[valid] = categories[values[valid].astype(np.int64)]
    return result


def categorical_inventory(h5: h5py.File, field: str) -> pd.DataFrame:
    values = read_obs_values(h5, field)
    canonical = np.asarray(["NA" if value is None else str(value) for value in values])
    levels, counts = np.unique(canonical, return_counts=True)
    return pd.DataFrame({"field": field, "level": levels, "n_observations": counts})


def _temporary(path: Path) -> Path:
    return path.with_name(f"{path.name}.tmp.{os.getpid()}")


def atomic_write_text(text: str, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(destination)
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, destination)


def atomic_copy(source: str | Path, destination: str | Path) -> None:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(target)
    shutil.copyfile(source, temporary)
    os.replace(temporary, target)


def atomic_write_tsv(frame: pd.DataFrame, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(destination)
    if destination.name.endswith(".gz"):
        with gzip.open(temporary, "wt", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, sep="	", index=False, na_rep="NA")
    else:
        frame.to_csv(temporary, sep="	", index=False, na_rep="NA")
    os.replace(temporary, destination)


def atomic_save_npy(value: np.ndarray, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(destination)
    with temporary.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    os.replace(temporary, destination)


def atomic_tar(paths: Sequence[Path], project_root: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(destination)
    with tarfile.open(temporary, "w:gz") as archive:
        for path in paths:
            archive.add(path, arcname=str(path.relative_to(project_root)), recursive=False)
    os.replace(temporary, destination)


def checks_frame(records: list[tuple[str, bool, Any, Any, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        records, columns=["check", "passed", "observed", "expected", "details"]
    )


def git_revision(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def git_status(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "status", "--porcelain=v1", "--untracked-files=all"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def status_frame(
    phase: str,
    state: str,
    project_root: Path,
    config_path: Path,
    started_at: str,
    failed: Iterable[str] = (),
    **fields: Any,
) -> pd.DataFrame:
    row = {
        "schema_version": STATUS_SCHEMA,
        "phase": phase,
        "validation_status": state,
        "failed_checks": ";".join(failed),
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "git_revision": git_revision(project_root),
        "config_sha256": sha256_file(config_path),
        "host": platform.node(),
    }
    row.update(fields)
    return pd.DataFrame([row])


def artifact_manifest(
    paths: Iterable[str | Path],
    project_root: Path,
    roles: dict[str, str] | None = None,
) -> pd.DataFrame:
    rows = []
    for item in paths:
        path = Path(item).resolve(strict=True)
        relative = str(path.relative_to(project_root))
        rows.append(
            {
                "artifact": path.name,
                "path": relative,
                "artifact_role": (roles or {}).get(relative, "result"),
                "bytes": path.stat().st_size,
                "digest_algorithm": "sha256",
                "digest_scope": "full_file",
                "digest_value": sha256_file(path),
            }
        )
    return pd.DataFrame(rows)


def write_artifacts(
    paths: Iterable[str | Path], project_root: Path, destination: Path
) -> pd.DataFrame:
    frame = artifact_manifest(paths, project_root)
    atomic_write_tsv(frame, destination)
    return frame


def require_phase(
    output_root: Path, phase_name: str, verify_artifacts: bool = True
) -> pd.DataFrame:
    directory = output_root / phase_name
    status_path = directory / "status.tsv"
    if not status_path.exists():
        raise FileNotFoundError(f"Missing predecessor status: {status_path}")
    status = pd.read_csv(status_path, sep="	", keep_default_na=False)
    if len(status) != 1 or status.loc[0, "validation_status"] != "validated_complete":
        raise ValueError(f"Predecessor is not validated_complete: {status_path}")
    if verify_artifacts:
        manifest_path = directory / "artifacts.tsv"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing predecessor artifact manifest: {manifest_path}")
        manifest = pd.read_csv(manifest_path, sep="	", keep_default_na=False)
        for row in manifest.itertuples(index=False):
            path = (output_root.parent.parent / row.path).resolve(strict=True)
            if (
                path.stat().st_size != int(row.bytes)
                or sha256_file(path) != row.digest_value
            ):
                raise ValueError(f"Predecessor artifact mismatch: {path}")
    return status


def structure_digest(
    umi: h5py.Group,
    normalization: str,
    obs_ids: np.ndarray,
    features: np.ndarray,
) -> tuple[str, dict[str, Any]]:
    indptr = umi["indptr"][...]
    payload = {
        "shape": tuple(int(value) for value in umi.attrs["shape"]),
        "nnz": int(umi["data"].shape[0]),
        "x_normalization": normalization,
        "obs_index_sha256": sha256_strings(obs_ids),
        "feature_order_sha256": sha256_strings(features),
        "umi_data_sample_sha256": sampled_dataset_digest(umi["data"]),
        "umi_indices_sample_sha256": sampled_dataset_digest(umi["indices"]),
        "umi_indptr_sha256": hashlib.sha256(indptr.tobytes()).hexdigest(),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return digest, payload


def bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().lower() in {"true", "t", "1", "yes"}
