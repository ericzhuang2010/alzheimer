#!/usr/bin/env python3
"""VH00: freeze environment, config, namespace, storage, and code provenance."""

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
    atomic_tar,
    atomic_write_text,
    atomic_write_tsv,
    checks_frame,
    git_status,
    load_config,
    package_version,
    parse_config_cli,
    phase_dir,
    repo_path,
    sha256_file,
    status_frame,
    utc_now,
    write_artifacts,
)


def main() -> int:
    args = parse_config_cli("VH00: freeze SEA-AD validation environment")
    started = utc_now()
    config, config_path, project_root, output_root = load_config(args.config)
    output_dir = phase_dir(output_root, "00_environment")
    expected = config["expected_identity"]

    python_packages = ["h5py", "numpy", "scipy", "pandas", "PyYAML"]
    r_packages = ["edgeR", "limma", "Matrix", "data.table", "yaml", "digest"]
    environment_rows = [
        {"component": "python", "version": platform.python_version(), "path": sys.executable},
        {"component": "platform", "version": platform.platform(), "path": platform.node()},
    ]
    checks = []
    for package in python_packages:
        version = package_version(package)
        checks.append((f"python_package_{package}", version != "missing", version, "installed", ""))
        environment_rows.append({"component": f"python:{package}", "version": version, "path": ""})

    rscript = shutil.which("Rscript")
    checks.append(("Rscript_available", rscript is not None, rscript or "missing", "installed", ""))
    if rscript:
        expression = (
            'pkgs <- c("edgeR","limma","Matrix","data.table","yaml","digest");'
            'for (p in pkgs) cat(p, "\t", if(requireNamespace(p,quietly=TRUE)) '
            'as.character(packageVersion(p)) else "missing", "\n", sep="")'
        )
        result = subprocess.run([rscript, "-e", expression], capture_output=True, text=True)
        observed = {}
        for line in result.stdout.splitlines():
            pieces = line.split("\t")
            if len(pieces) == 2:
                observed[pieces[0]] = pieces[1]
        for package in r_packages:
            version = observed.get(package, "missing")
            checks.append((f"r_package_{package}", version != "missing", version, "installed", result.stderr.strip()))
            environment_rows.append({"component": f"R:{package}", "version": version, "path": rscript})

    inputs = {
        "h5ad": repo_path(project_root, config["inputs"]["h5ad"], must_exist=False),
        "metadata_csv": repo_path(project_root, config["inputs"]["metadata_csv"], must_exist=False),
    }
    for name, path in inputs.items():
        checks.append((f"input_{name}_exists", path.is_file(), str(path), "readable file", ""))
    if inputs["h5ad"].is_file():
        checks.append(("h5ad_bytes", inputs["h5ad"].stat().st_size == expected["h5ad_bytes"], inputs["h5ad"].stat().st_size, expected["h5ad_bytes"], ""))
    if inputs["metadata_csv"].is_file():
        checks.append(("metadata_csv_bytes", inputs["metadata_csv"].stat().st_size == expected["metadata_csv_bytes"], inputs["metadata_csv"].stat().st_size, expected["metadata_csv_bytes"], ""))

    h5ad_openable = False
    if inputs["h5ad"].is_file():
        try:
            with h5py.File(inputs["h5ad"], "r") as h5:
                h5ad_openable = all(key in h5 for key in ["obs", "var", "layers/UMIs"])
        except OSError:
            pass
    checks.append(("h5ad_openable", h5ad_openable, h5ad_openable, True, ""))

    reference_rows = []
    for name, value in config["references"].items():
        path = repo_path(project_root, value, must_exist=False)
        exists = path.is_file()
        observed_hash = sha256_file(path) if exists else ""
        expected_hash = config["expected_reference_sha256"][name]
        checks.append((f"reference_{name}_identity", exists and observed_hash == expected_hash, observed_hash or "missing", expected_hash, str(path)))
        if exists:
            reference_rows.append({"reference": name, "path": str(path.relative_to(project_root)), "bytes": path.stat().st_size, "sha256": observed_hash})

    supertype_total = sum(config["taxonomy"]["expected_supertype_counts"].values())
    group_total = len(config["cohort"]["signature_groups"])
    checks.extend([
        ("structural_supertypes", supertype_total == 129, supertype_total, 129, ""),
        ("structural_fine_contrasts", supertype_total * group_total == expected["fine_contrasts"], supertype_total * group_total, expected["fine_contrasts"], ""),
        ("structural_fine_directions", supertype_total * group_total * 2 == expected["fine_directions"], supertype_total * group_total * 2, expected["fine_directions"], ""),
        ("isolated_output_root", output_root == (project_root / "results/validation_human").resolve(), str(output_root), str((project_root / "results/validation_human").resolve()), ""),
    ])

    disk = shutil.disk_usage(project_root)
    checks.append(("minimum_free_storage", disk.free >= int(config["storage"]["minimum_free_bytes"]), disk.free, config["storage"]["minimum_free_bytes"], ""))

    code_paths = sorted(
        [p for p in (project_root / "scripts/validation_human").rglob("*") if p.is_file()]
        + [p for p in (project_root / "tests/validation_human").rglob("*") if p.is_file()]
        + [project_root / "docs/validation_human/seaad_deg_processing_plan.md"]
    )
    code_manifest = pd.DataFrame([
        {"path": str(path.relative_to(project_root)), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in code_paths
    ])
    checks.append(("implementation_file_count", len(code_paths) >= 13, len(code_paths), ">=13", ""))

    initial_git_status = git_status(project_root)
    tracked_diff = subprocess.run(
        ["git", "-C", str(project_root), "diff", "--binary", "HEAD", "--", ".gitignore", "scripts/validation_human", "tests/validation_human", "docs/validation_human/seaad_deg_processing_plan.md"],
        capture_output=True,
        text=True,
    ).stdout

    paths = {
        "config": output_dir / "config_snapshot.yml",
        "environment": output_dir / "environment.tsv",
        "checks": output_dir / "environment_checks.tsv",
        "storage": output_dir / "storage_policy.tsv",
        "planned": output_dir / "planned_artifacts.tsv",
        "references": output_dir / "reference_identity.tsv",
        "code_manifest": output_dir / "code_manifest.tsv",
        "code_snapshot": output_dir / "code_snapshot.tar.gz",
        "git_status": output_dir / "git_status_initial.txt",
        "git_diff": output_dir / "dirty_diff.patch",
        "artifacts": output_dir / "artifacts.tsv",
        "status": output_dir / "status.tsv",
    }
    atomic_copy(config_path, paths["config"])
    atomic_write_tsv(pd.DataFrame(environment_rows), paths["environment"])
    storage = pd.DataFrame([
        {"artifact_class": value, "local_treatment": "retained_or_archived_with_hash", "git_treatment": "ignored"}
        for value in config["storage"]["large_artifact_classes"]
    ] + [
        {"artifact_class": "compact_contracts_manifests_checks", "local_treatment": "retained", "git_treatment": "tracked"}
    ])
    atomic_write_tsv(storage, paths["storage"])
    planned = pd.DataFrame([
        {"phase": f"VH{index:02d}", "directory": name, "storage_root": str(output_root.relative_to(project_root))}
        for index, name in enumerate(["00_environment", "01_audit", "02_cohort", "03_genes", "04_supertype_manifest", "05_pseudobulk", "06_pseudobulk_qc", "07_contrasts", "08_deg"])
    ])
    atomic_write_tsv(planned, paths["planned"])
    atomic_write_tsv(pd.DataFrame(reference_rows), paths["references"])
    atomic_write_tsv(code_manifest, paths["code_manifest"])
    atomic_tar(code_paths, project_root, paths["code_snapshot"])
    atomic_write_text(initial_git_status, paths["git_status"])
    atomic_write_text(tracked_diff, paths["git_diff"])

    checks_table = checks_frame(checks)
    atomic_write_tsv(checks_table, paths["checks"])
    failed = checks_table.loc[~checks_table["passed"], "check"].tolist()
    state = "validated_complete" if not failed else (
        "blocked_missing_input" if any(name.startswith("input_") for name in failed) else "failed"
    )
    declared = [paths[key] for key in ["config", "environment", "checks", "storage", "planned", "references", "code_manifest", "code_snapshot", "git_status", "git_diff"]]
    write_artifacts(declared, project_root, paths["artifacts"])
    status = status_frame(
        "VH00", state, project_root, config_path, started, failed,
        free_bytes=disk.free,
        safety_reserve_bytes=config["storage"]["safety_reserve_bytes"],
        code_files=len(code_paths),
        dirty_tree=bool(initial_git_status.strip()),
        h5ad_bytes=inputs["h5ad"].stat().st_size if inputs["h5ad"].exists() else 0,
        metadata_csv_bytes=inputs["metadata_csv"].stat().st_size if inputs["metadata_csv"].exists() else 0,
    )
    atomic_write_tsv(status, paths["status"])
    print(f"VH00 status: {state}; free disk: {disk.free / 2**30:.1f} GiB")
    return 0 if state == "validated_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
