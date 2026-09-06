#!/usr/bin/env python3
"""Shared contracts for the SEA-AD RIMBANet construction stages."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from seaad_common import (
    atomic_write_text,
    atomic_write_tsv,
    checks_frame,
    load_config,
    sha256_file,
    utc_now,
)


PHASE = "11_seaad_rimbanet"
EDGE_RE = re.compile(r"^\s*([^\s;]+)\s*->\s*([^\s;]+)")
NODE_RE = re.compile(r"^\s*[^\s;]+\s*;\s*$")


def parser(description: str, *, network: bool = False) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--config", required=True)
    if network:
        result.add_argument("--network", required=True)
    return result


def load_rimbanet_config(path: str | Path):
    config, config_path, project_root, repository_output_root = load_config(path)
    if config.get("schema_version") != "seaad_rimbanet_config_v1":
        raise ValueError("Unsupported SEA-AD RIMBANet config schema")
    phase_name = config.get("phase_directory")
    if phase_name != PHASE:
        raise ValueError(f"phase_directory must be {PHASE}")
    output_value = config.get("storage", {}).get("generated_output_root")
    output_root = (
        configured_path(project_root, output_value, must_exist=False)
        if output_value
        else repository_output_root
    )
    return config, config_path, project_root, output_root


def configured_path(
    project_root: Path, value: str | Path, *, must_exist: bool = True
) -> Path:
    """Resolve a trusted config path, including an absolute Minerva scratch path."""
    raw = Path(value)
    if ".." in raw.parts:
        raise ValueError(f"Configured path may not contain '..': {raw}")
    candidate = raw if raw.is_absolute() else project_root / raw
    return candidate.resolve(strict=must_exist)


def provenance_path(path: Path, project_root: Path) -> str:
    """Use repository-relative provenance when possible, otherwise an absolute path."""
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(project_root))
    except ValueError:
        return str(resolved)


def safe_project_path(
    project_root: Path, value: str | Path, *, must_exist: bool = True
) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"Expected safe project-relative path, got {raw}")
    path = (project_root / raw).resolve(strict=must_exist)
    path.relative_to(project_root)
    return path


def stage_dir(output_root: Path, name: str, *, create: bool = True) -> Path:
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"Unsafe stage name: {name}")
    root = (output_root / PHASE).resolve(strict=False)
    path = (root / name).resolve(strict=False)
    path.relative_to(root)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def validate_network(config: dict, network: str) -> str:
    networks = [str(value) for value in config["networks"]]
    if network not in networks:
        raise ValueError(f"Unknown network {network!r}; expected one of {networks}")
    return network


def atomic_write_json(value, path: Path) -> None:
    atomic_write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", path)


def write_stage_contract(
    directory: Path,
    stage: str,
    state: str,
    config_path: Path,
    project_root: Path,
    checks: list[tuple[str, bool, object, object, str]],
    artifacts: Iterable[Path],
    **details,
) -> None:
    checks_table = checks_frame(checks)
    atomic_write_tsv(checks_table, directory / "checks.tsv")
    artifact_rows = []
    for path in sorted(set(Path(item) for item in artifacts)):
        if not path.exists() or not path.is_file():
            continue
        artifact_rows.append(
            {
                "path": provenance_path(path, project_root),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    atomic_write_tsv(pd.DataFrame(artifact_rows), directory / "artifacts.tsv")
    status = {
        "schema_version": "seaad_rimbanet_stage_status_v1",
        "stage": stage,
        "state": state,
        "timestamp_utc": utc_now(),
        "config_path": str(config_path.relative_to(project_root)),
        "config_sha256": sha256_file(config_path),
        **details,
    }
    atomic_write_tsv(pd.DataFrame([status]), directory / "status.tsv")


def parse_edge_file(path: Path) -> list[tuple[str, str]]:
    opener = gzip.open if path.name.endswith(".gz") else open
    edges: list[tuple[str, str]] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if (
                not stripped
                or stripped in {"{", "}"}
                or stripped.startswith("#")
                or stripped.startswith("digraph")
            ):
                continue
            match = EDGE_RE.match(stripped)
            if match:
                edges.append((match.group(1), match.group(2)))
                continue
            if NODE_RE.fullmatch(stripped):
                # RIMBANet emits DOT-style declarations for isolated nodes.
                # They are valid network records but are not directed edges.
                continue
            fields = stripped.rstrip(";").split("\t")
            if len(fields) >= 2 and fields[0] and fields[1]:
                edges.append((fields[0], fields[1]))
                continue
            raise ValueError(f"Unparseable edge at {path}:{line_number}: {stripped}")
    return edges


def write_headerless_edges(edges: Iterable[tuple[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        for parent, child in edges:
            handle.write(f"{parent}\t{child}\n")
    os.replace(temporary, path)
