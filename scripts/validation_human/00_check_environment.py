#!/usr/bin/env python3
"""VH00: freeze configuration and verify local SEA-AD dependencies."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

import h5py
import pandas as pd

from seaad_common import (
    atomic_copy,
    atomic_write_tsv,
    checks_frame,
    load_config,
    package_version,
    parse_config_cli,
    phase_output_dir,
    repo_path,
    sha256_file,
    status_frame,
    utc_now,
)


def main() -> int:
    args = parse_config_cli("VH00: check SEA-AD validation environment")
    started_at = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    output_dir = phase_output_dir(output_root, "00_environment")

    required_python = ["h5py", "numpy", "scipy", "pandas", "PyYAML"]
    environment_rows = [
        {"component": "python", "version": platform.python_version(), "path": sys.executable},
        {"component": "platform", "version": platform.platform(), "path": platform.node()},
    ]
    checks = []
    for package in required_python:
        version = package_version(package)
        passed = version != "missing"
        checks.append((f"python_package_{package}", passed, version, "installed", ""))
        environment_rows.append(
            {"component": f"python:{package}", "version": version, "path": ""}
        )

    rscript = shutil.which("Rscript")
    checks.append(("Rscript_available", rscript is not None, rscript or "missing", "installed", ""))
    r_packages = ["edgeR", "limma", "Matrix", "data.table", "yaml", "digest"]
    if rscript:
        expression = (
            'pkgs <- c("edgeR","limma","Matrix","data.table","yaml","digest");'
            'for (p in pkgs) cat(p, if (requireNamespace(p, quietly=TRUE)) '
            'as.character(packageVersion(p)) else "missing", "\n", sep="\t")'
        )
        result = subprocess.run(
            [rscript, "-e", expression], check=False, capture_output=True, text=True
        )
        observed = {}
        for line in result.stdout.splitlines():
            pieces = line.split("\t")
            if len(pieces) >= 2:
                observed[pieces[0]] = pieces[1]
        for package in r_packages:
            version = observed.get(package, "missing")
            checks.append((f"r_package_{package}", version != "missing", version, "installed", result.stderr.strip()))
            environment_rows.append(
                {"component": f"R:{package}", "version": version, "path": rscript}
            )
        version_result = subprocess.run(
            [rscript, "--version"], check=False, capture_output=True, text=True
        )
        environment_rows.append(
            {
                "component": "R",
                "version": (version_result.stderr or version_result.stdout).strip(),
                "path": rscript,
            }
        )
    else:
        for package in r_packages:
            checks.append((f"r_package_{package}", False, "not_checked", "installed", "Rscript missing"))

    input_paths = {
        "h5ad": repo_path(project_root, config["inputs"]["h5ad"], must_exist=False),
        "metadata_csv": repo_path(project_root, config["inputs"]["metadata_csv"], must_exist=False),
    }
    for name, path in input_paths.items():
        checks.append((f"input_{name}_exists", path.is_file(), str(path), "readable file", ""))
        if path.is_file():
            checks.append((f"input_{name}_readable", path.stat().st_size > 0, path.stat().st_size, ">0 bytes", ""))

    reference_paths = {}
    for name, value in config["references"].items():
        path = repo_path(project_root, value, must_exist=False)
        reference_paths[name] = path
        checks.append((f"reference_{name}_exists", path.is_file(), str(path), "readable file", ""))

    h5ad_readable = False
    if input_paths["h5ad"].is_file():
        try:
            with h5py.File(input_paths["h5ad"], "r") as h5:
                h5ad_readable = "layers/UMIs" in h5 and "obs" in h5 and "var" in h5
        except OSError:
            h5ad_readable = False
    checks.append(("h5ad_openable", h5ad_readable, h5ad_readable, True, ""))

    checks.append(
        (
            "isolated_output_root",
            output_root == (project_root / "results/validation_human").resolve(),
            str(output_root),
            str((project_root / "results/validation_human").resolve()),
            "",
        )
    )

    script_root = (project_root / "scripts" / "validation_human").resolve(strict=True)
    code_paths = sorted(
        path for path in script_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    checks.append((
        "isolated_code_manifest_nonempty", len(code_paths) >= 12,
        len(code_paths), ">=12 files", ""
    ))
    code_manifest = pd.DataFrame([
        {
            "path": str(path.relative_to(project_root)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in code_paths
    ])
    environment = pd.DataFrame(environment_rows)
    checks_table = checks_frame(checks)
    environment_path = output_dir / "environment.tsv"
    snapshot_path = output_dir / "config_snapshot.yml"
    checks_path = output_dir / "environment_checks.tsv"
    code_manifest_path = output_dir / "code_manifest.tsv"
    status_path = output_dir / "status.tsv"
    atomic_write_tsv(environment, environment_path)
    atomic_copy(config_path, snapshot_path)
    atomic_write_tsv(checks_table, checks_path)
    atomic_write_tsv(code_manifest, code_manifest_path)

    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    validation_status = "validated_complete" if not failed else "failed"
    status = status_frame(
        "VH00",
        validation_status,
        project_root,
        config_path,
        started_at,
        failed,
        h5ad_bytes=input_paths["h5ad"].stat().st_size if input_paths["h5ad"].exists() else 0,
        metadata_csv_bytes=input_paths["metadata_csv"].stat().st_size if input_paths["metadata_csv"].exists() else 0,
        checks_passed=int(checks_table["passed"].sum()),
        checks_total=len(checks_table),
        code_files=len(code_manifest),
        code_manifest_sha256=sha256_file(code_manifest_path),
    )
    atomic_write_tsv(status, status_path)
    print(f"VH00 status: {validation_status}")
    print(f"Output: {output_dir}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
