#!/usr/bin/env python3
"""Validate the pinned Linux runtime required for SEA-AD RIMBANet."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import yaml

from rimbanet_common import (
    configured_path,
    load_rimbanet_config,
    provenance_path,
    safe_project_path,
    stage_dir,
    write_stage_contract,
)
from seaad_common import atomic_write_tsv, sha256_file


COMMANDS = [
    "bash",
    "bc",
    "bcftools",
    "gzip",
    "perl",
    "plink2",
    "python",
    "Rscript",
]
R_PACKAGES = ["data.table", "digest", "edgeR", "MatrixEQTL", "yaml", "cit"]
PYTHON_PACKAGES = ["h5py", "networkx", "numpy", "pandas", "scipy", "yaml"]


def command_version(command: str) -> str:
    executable = shutil.which(command)
    if not executable:
        return "missing"
    attempts = [[executable, "--version"], [executable, "-v"]]
    for args in attempts:
        result = subprocess.run(args, text=True, capture_output=True)
        text = (result.stdout or result.stderr).strip()
        if text:
            return text.splitlines()[0][:300]
    return "present_version_unavailable"


def r_package_version(package: str) -> str:
    code = (
        f'if (!requireNamespace("{package}", quietly=TRUE)) '
        f'quit(status=2); cat(as.character(packageVersion("{package}")))'
    )
    # The repository .Rprofile activates renv. Production runs inside the
    # pinned image must inspect its R library instead of the bound host one.
    result = subprocess.run(
        ["Rscript", "--vanilla", "-e", code], text=True, capture_output=True
    )
    return result.stdout.strip() if result.returncode == 0 else "missing"


def python_package_version(package: str) -> str:
    distribution = "PyYAML" if package == "yaml" else package
    code = (
        "import importlib.metadata, importlib.util; "
        f"assert importlib.util.find_spec({package!r}) is not None; "
        f"print(importlib.metadata.version({distribution!r}))"
    )
    result = subprocess.run(["python", "-c", code], text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "missing"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--execution-config", default="config/seaad_rimbanet_execution.yml"
    )
    args = parser.parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    output = stage_dir(output_root, "11a_environment")
    execution_path = safe_project_path(project_root, args.execution_config)
    execution = yaml.safe_load(execution_path.read_text(encoding="utf-8"))

    rows = []
    checks = []
    storage_root = configured_path(
        project_root, execution["paths"]["storage_root"], must_exist=False
    )
    execution_output_root = configured_path(
        project_root,
        execution["paths"]["generated_output_root"],
        must_exist=False,
    )
    try:
        output_in_scratch = output_root.is_relative_to(storage_root)
    except AttributeError:
        output_in_scratch = storage_root == output_root or storage_root in output_root.parents
    checks.extend(
        [
            (
                "scratch_storage_available",
                storage_root.is_dir() and os.access(storage_root, os.W_OK),
                str(storage_root),
                "existing writable directory",
                "scratch is disposable and must be rehydrated after a purge",
            ),
            (
                "scientific_execution_output_roots_match",
                output_root == execution_output_root,
                str(output_root),
                str(execution_output_root),
                "",
            ),
            (
                "generated_outputs_are_in_scratch",
                output_in_scratch,
                str(output_root),
                f"below {storage_root}",
                "do not fall back to the work allocation",
            ),
        ]
    )
    for command in COMMANDS:
        version = command_version(command)
        rows.append({"component": command, "version": version})
        checks.append(
            (f"command_{command}", version != "missing", version, "present", "")
        )
    runtime_binary = shutil.which("testBN")
    runtime_binary_sha = (
        sha256_file(Path(runtime_binary)) if runtime_binary is not None else "missing"
    )
    rows.append({"component": "testBN", "version": runtime_binary_sha})
    checks.append(
        (
            "command_testBN",
            runtime_binary is not None,
            runtime_binary_sha,
            "present with recorded SHA-256",
            "",
        )
    )

    if shutil.which("Rscript"):
        for package in R_PACKAGES:
            version = r_package_version(package)
            rows.append({"component": f"R:{package}", "version": version})
            checks.append(
                (f"r_package_{package}", version != "missing", version, "present", "")
            )
    else:
        for package in R_PACKAGES:
            rows.append({"component": f"R:{package}", "version": "missing"})
            checks.append(
                (f"r_package_{package}", False, "missing", "present", "")
            )

    if shutil.which("python"):
        for package in PYTHON_PACKAGES:
            version = python_package_version(package)
            rows.append({"component": f"python:{package}", "version": version})
            checks.append(
                (
                    f"python_package_{package}",
                    version != "missing",
                    version,
                    "present",
                    "",
                )
            )

    system = platform.system()
    machine = platform.machine()
    linux_x86 = system == "Linux" and machine in {"x86_64", "AMD64"}
    checks.append(
        (
            "production_architecture",
            linux_x86,
            f"{system}_{machine}",
            "Linux_x86_64",
            "macOS may orchestrate, but cannot run the legacy ELF binary",
        )
    )

    source_root = configured_path(
        project_root, config["method"]["external_checkout"], must_exist=False
    )
    commit = "missing"
    if source_root.exists():
        result = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
    checks.append(
        (
            "rimbanet_commit",
            commit == config["method"]["source_commit"],
            commit,
            config["method"]["source_commit"],
            "",
        )
    )

    binary = configured_path(
        project_root, config["method"]["binary"], must_exist=False
    )
    binary_sha = sha256_file(binary) if binary.exists() else "missing"
    executable = binary.exists() and binary.is_file()
    checks.append(
        (
            "rimbanet_binary_present",
            executable,
            binary_sha,
            "present with frozen checksum",
            provenance_path(binary, project_root),
        )
    )

    image_raw = Path(execution["runtime"]["image"])
    image = (
        image_raw
        if image_raw.is_absolute()
        else (project_root / image_raw).resolve(strict=False)
    )
    image_frozen = (
        image.exists()
        and execution["runtime"]["image_sha256"] != "TO_BE_FROZEN"
        and sha256_file(image) == execution["runtime"]["image_sha256"]
    )
    checks.append(
        (
            "container_image_frozen",
            image_frozen,
            image.exists(),
            True,
            str(image),
        )
    )

    versions = output / "environment_versions.tsv"
    atomic_write_tsv(pd.DataFrame(rows), versions)
    failed = [name for name, passed, *_ in checks if not passed]
    state = "validated_complete" if not failed else "blocked_runtime_incomplete"
    write_stage_contract(
        output,
        "VH11_ENV",
        state,
        config_path,
        project_root,
        checks,
        [versions, execution_path] + ([binary] if binary.exists() else []),
        failed_checks=";".join(failed),
        rimbanet_binary_sha256=binary_sha,
        container_image=str(image),
    )
    print(f"VH11 environment status: {state}; failed={len(failed)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
