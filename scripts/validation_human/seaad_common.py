#!/usr/bin/env python3
"""Shared safety, HDF5, provenance, and atomic-output helpers for SEA-AD."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import yaml


SCHEMA_VERSION = "seaad_validation_common_v1"


def parse_config_cli(description: str, extra_arguments=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", required=True, help="SEA-AD YAML configuration")
    if extra_arguments:
        extra_arguments(parser)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_revision(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--verify", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def load_config(config_path: str | Path) -> tuple[dict[str, Any], Path, Path, Path]:
    config_file = Path(config_path).expanduser().resolve(strict=True)
    with config_file.open("rt", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    invocation_root = Path.cwd().resolve(strict=True)
    raw_root = Path(config.get("project_root", "."))
    project_root = (
        raw_root.resolve(strict=True)
        if raw_root.is_absolute()
        else (invocation_root / raw_root).resolve(strict=True)
    )
    output_rel = Path(config["output_root"])
    if ".." in output_rel.parts:
        raise ValueError("Configured output_root may not contain '..'")
    output_root = (
        output_rel.resolve(strict=False)
        if output_rel.is_absolute()
        else (project_root / output_rel).resolve(strict=False)
    )
    required_root = (project_root / "results" / "validation_human").resolve(strict=False)
    if output_root != required_root:
        raise ValueError(
            f"output_root must resolve exactly to {required_root}, not {output_root}"
        )
    return config, config_file, project_root, output_root


def repo_path(project_root: Path, value: str | Path, must_exist: bool = True) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else project_root / raw
    return path.resolve(strict=must_exist)


def isolated_output_path(
    output_root: Path, relative_or_absolute: str | Path, create: bool = False
) -> Path:
    raw = Path(relative_or_absolute)
    if ".." in raw.parts:
        raise ValueError(f"Output path may not contain '..': {raw}")
    candidate = (
        raw.resolve(strict=False)
        if raw.is_absolute()
        else (output_root / raw).resolve(strict=False)
    )
    try:
        candidate.relative_to(output_root)
    except ValueError as exc:
        raise ValueError(
            f"Refusing output outside isolated root {output_root}: {candidate}"
        ) from exc
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def phase_output_dir(
    output_root: Path, phase_directory: str, override: str | None = None
) -> Path:
    if override is None:
        return isolated_output_path(output_root, phase_directory, create=True)
    raw = Path(override)
    if raw.is_absolute():
        return isolated_output_path(output_root, raw, create=True)
    project_root = output_root.parent.parent
    candidate = project_root / raw
    return isolated_output_path(output_root, candidate, create=True)


def sha256_file(path: str | Path, block_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(block_bytes)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8", errors="strict"))
        digest.update(b"\n")
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode())
    digest.update(str(contiguous.shape).encode())
    digest.update(memoryview(contiguous).cast("B"))
    return digest.hexdigest()


def _temporary_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.tmp.{os.getpid()}")


def atomic_write_text(text: str, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temporary, destination)


def atomic_write_bytes(data: bytes, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    with temporary.open("wb") as handle:
        handle.write(data)
    os.replace(temporary, destination)


def atomic_copy(source: str | Path, destination: str | Path) -> None:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(target)
    shutil.copyfile(source, temporary)
    os.replace(temporary, target)


def atomic_write_tsv(frame: pd.DataFrame, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    if destination.name.endswith(".gz"):
        with gzip.open(temporary, "wt", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, sep="\t", index=False, na_rep="NA")
    else:
        frame.to_csv(temporary, sep="\t", index=False, na_rep="NA")
    os.replace(temporary, destination)


def atomic_save_npy(array: np.ndarray, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    with temporary.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)
    os.replace(temporary, destination)


def atomic_save_npz(path: str | Path, **arrays: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, destination)


def decode_scalar(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return str(value)


def decode_strings(values: Any) -> np.ndarray:
    array = np.asarray(values)
    return np.asarray([decode_scalar(value) for value in array], dtype=object)


def read_categorical_codes(
    h5: h5py.File, obs_field: str
) -> tuple[np.ndarray, np.ndarray] | None:
    dataset = h5["obs"][obs_field]
    reference = dataset.attrs.get("categories")
    if reference is None:
        return None
    categories = decode_strings(h5[reference][...])
    return dataset[...], categories


def read_obs_values(h5: h5py.File, obs_field: str) -> np.ndarray:
    encoded = read_categorical_codes(h5, obs_field)
    if encoded is None:
        values = h5["obs"][obs_field][...]
        if values.dtype.kind in {"S", "O", "U"}:
            return decode_strings(values)
        return values
    codes, categories = encoded
    result = np.empty(codes.shape, dtype=object)
    valid = codes >= 0
    result[~valid] = None
    result[valid] = categories[codes[valid].astype(np.int64)]
    return result


def categorical_count_table(
    h5: h5py.File, obs_field: str
) -> pd.DataFrame:
    encoded = read_categorical_codes(h5, obs_field)
    if encoded is None:
        values = read_obs_values(h5, obs_field)
        unique, counts = np.unique(values, return_counts=True)
        labels = [decode_scalar(value) for value in unique]
    else:
        codes, categories = encoded
        unique, counts = np.unique(codes, return_counts=True)
        labels = [
            "NA" if int(code) < 0 else str(categories[int(code)])
            for code in unique
        ]
    return pd.DataFrame(
        {"field": obs_field, "level": labels, "n_observations": counts.astype(np.int64)}
    )


def require_validated_status(path: str | Path, allowed=("validated_complete",)) -> pd.DataFrame:
    status_path = Path(path)
    if not status_path.exists():
        raise FileNotFoundError(f"Required upstream status is missing: {status_path}")
    frame = pd.read_csv(status_path, sep="\t")
    if frame.shape[0] != 1 or "validation_status" not in frame.columns:
        raise ValueError(f"Malformed upstream status: {status_path}")
    observed = str(frame.loc[0, "validation_status"])
    if observed not in set(allowed):
        raise ValueError(f"Upstream status is {observed}, not one of {allowed}: {status_path}")
    return frame


def status_frame(
    phase: str,
    validation_status: str,
    project_root: Path,
    config_path: Path,
    started_at: str,
    failed_checks: Iterable[str] = (),
    **fields: Any,
) -> pd.DataFrame:
    row = {
        "schema_version": "seaad_phase_status_v1",
        "phase": phase,
        "validation_status": validation_status,
        "failed_checks": ";".join(failed_checks),
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "git_revision": git_revision(project_root),
        "config_sha256": sha256_file(config_path),
        "host": platform.node(),
    }
    row.update(fields)
    return pd.DataFrame([row])


def checks_frame(records: list[tuple[str, bool, Any, Any, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        records,
        columns=["check", "passed", "observed", "expected", "details"],
    )


def artifact_manifest(paths: Iterable[str | Path], project_root: Path) -> pd.DataFrame:
    records = []
    for item in paths:
        path = Path(item)
        records.append(
            {
                "artifact": path.name,
                "path": str(path.resolve(strict=True).relative_to(project_root)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return pd.DataFrame(records)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def sampled_dataset_digest(dataset: h5py.Dataset, sample_count: int = 4096) -> str:
    length = int(dataset.shape[0])
    if length == 0:
        return hashlib.sha256(b"empty").hexdigest()
    indices = np.unique(np.linspace(0, length - 1, min(sample_count, length), dtype=np.int64))
    digest = hashlib.sha256()
    digest.update(str(dataset.shape).encode())
    digest.update(str(dataset.dtype).encode())
    for index in indices:
        value = np.asarray(dataset[int(index)])
        digest.update(value.tobytes())
    return digest.hexdigest()


def human_bytes(value: int) -> str:
    amount = float(value)
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return str(value)
