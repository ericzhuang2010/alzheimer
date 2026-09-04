#!/usr/bin/env python3
"""Submit one SEA-AD RIMBANet network as a validated Minerva LSF array."""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import subprocess
from pathlib import Path

import yaml


def read_yaml(path: Path) -> dict:
    with path.open("rt", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def resolve_config_path(project_root: Path, value: str | Path) -> Path:
    raw = Path(value).expanduser()
    if ".." in raw.parts:
        raise ValueError(f"Configured path may not contain '..': {raw}")
    return (raw if raw.is_absolute() else project_root / raw).resolve(strict=False)


def generated_output_root(project_root: Path, scientific: dict) -> Path:
    value = scientific.get("storage", {}).get(
        "generated_output_root", scientific["output_root"]
    )
    return resolve_config_path(project_root, value)


def require_pilot_gate(project_root: Path, scientific: dict, network: str) -> None:
    pilot = str(scientific["cohort"]["pilot_network"])
    if network == pilot:
        return
    status_path = (
        generated_output_root(project_root, scientific)
        / scientific["phase_directory"]
        / "11h_release_qc"
        / pilot
        / "status.tsv"
    )
    if not status_path.is_file():
        raise RuntimeError(
            f"Pilot gate is missing: {status_path}. Submit {pilot} first."
        )
    with status_path.open("rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 1 or rows[0].get("state") != "validated_complete":
        state = rows[0].get("state", "invalid") if rows else "missing"
        raise RuntimeError(f"Pilot gate has not passed: {status_path} state={state}")
    gate_path = (
        generated_output_root(project_root, scientific)
        / scientific["phase_directory"]
        / "11f_runs/pilot_gate.tsv"
    )
    if not gate_path.is_file():
        raise RuntimeError(f"Final pilot gate is missing: {gate_path}")
    with gate_path.open("rt", encoding="utf-8", newline="") as handle:
        gate_rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(gate_rows) != 1 or gate_rows[0].get("state") != "passed":
        state = gate_rows[0].get("state", "invalid") if gate_rows else "missing"
        raise RuntimeError(f"Final pilot gate has not passed: {gate_path} state={state}")


def build_bsub_command(
    *,
    project_root: Path,
    config_path: Path,
    image_path: Path,
    storage_root: Path,
    log_root: Path,
    network: str,
    lsf: dict,
    project: str,
) -> list[str]:
    start = int(lsf["task_start"])
    end = int(lsf["task_end"])
    concurrency = int(lsf["array_concurrency"])
    cores = int(lsf["cores_per_task"])
    memory = int(lsf["memory_mb_per_task"])
    network_log_root = log_root / network
    environment = ",".join(
        [
            "all",
            f"PROJECT_ROOT={project_root}",
            f"CONFIG={config_path}",
            f"NETWORK={network}",
            f"RIMBANET_IMAGE={image_path}",
            f"RIMBANET_STORAGE_ROOT={storage_root}",
        ]
    )
    return [
        "bsub",
        "-P",
        project,
        "-q",
        str(lsf["queue"]),
        "-n",
        str(cores),
        "-R",
        "span[hosts=1]",
        "-R",
        f"rusage[mem={memory}]",
        "-M",
        str(memory),
        "-W",
        str(lsf["walltime"]),
        "-J",
        f"seaad_{network}[{start}-{end}]%{concurrency}",
        "-o",
        str(network_log_root / "%J.%I.out"),
        "-e",
        str(network_log_root / "%J.%I.err"),
        "-env",
        environment,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/seaad_rimbanet.yml")
    parser.add_argument(
        "--execution-config", default="config/seaad_rimbanet_execution.yml"
    )
    parser.add_argument("--network", required=True)
    parser.add_argument(
        "--lsf-project",
        help="Minerva allocation/project; overrides execution config",
    )
    parser.add_argument("--image", help="SIF path; overrides execution config")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print bsub command without submitting"
    )
    args = parser.parse_args()

    project_root = Path.cwd().resolve(strict=True)
    config_path = Path(args.config).expanduser().resolve(strict=True)
    execution_path = Path(args.execution_config).expanduser().resolve(strict=True)
    scientific = read_yaml(config_path)
    execution = read_yaml(execution_path)
    if scientific.get("schema_version") != "seaad_rimbanet_config_v1":
        raise ValueError("Unsupported scientific config schema")
    if execution.get("schema_version") != "seaad_rimbanet_execution_v1":
        raise ValueError("Unsupported execution config schema")
    networks = [str(value) for value in scientific["networks"]]
    if args.network not in networks:
        raise ValueError(f"Unknown network {args.network!r}; expected {networks}")
    if not bool(execution["lsf_production"]["enabled"]):
        raise RuntimeError("LSF production is disabled in the execution config")
    require_pilot_gate(project_root, scientific, args.network)

    project = args.lsf_project or str(execution["lsf_production"]["project"])
    if not project or project == "TO_BE_CONFIGURED":
        raise ValueError("Provide the Minerva allocation with --lsf-project")
    image_value = args.image or str(execution["runtime"]["image"])
    image_path = Path(image_value).expanduser()
    if not image_path.is_absolute():
        image_path = project_root / image_path
    image_path = image_path.resolve(strict=True)

    storage_root = resolve_config_path(
        project_root, execution["paths"]["storage_root"]
    )
    if not storage_root.is_dir() or not os.access(storage_root, os.W_OK):
        raise FileNotFoundError(
            f"Minerva scratch storage root is missing or not writable: {storage_root}"
        )
    configured_generated_root = resolve_config_path(
        project_root, execution["paths"]["generated_output_root"]
    )
    scientific_generated_root = generated_output_root(project_root, scientific)
    if configured_generated_root != scientific_generated_root:
        raise ValueError(
            "Scientific and execution generated_output_root values do not match: "
            f"{scientific_generated_root} != {configured_generated_root}"
        )
    log_root = resolve_config_path(project_root, execution["paths"]["log_root"])
    for label, path in [
        ("container image", image_path),
        ("generated output root", configured_generated_root),
        ("log root", log_root),
    ]:
        if not path.is_relative_to(storage_root):
            raise ValueError(
                f"{label} must be below Minerva scratch storage root: "
                f"{path} is not below {storage_root}"
            )
    (log_root / args.network).mkdir(parents=True, exist_ok=True)
    job_script = (
        project_root
        / "scripts/validation_human/11_submit_rimbanet_minerva.lsf"
    )
    if not job_script.is_file():
        raise FileNotFoundError(job_script)
    command = build_bsub_command(
        project_root=project_root,
        config_path=config_path,
        image_path=image_path,
        storage_root=storage_root,
        log_root=log_root,
        network=args.network,
        lsf=execution["lsf_production"],
        project=project,
    )
    print(shlex.join(command) + f" < {shlex.quote(str(job_script))}")
    if args.dry_run:
        return 0
    if not shutil_which("bsub"):
        raise RuntimeError("bsub is not available; run this command on Minerva")
    with job_script.open("rb") as handle:
        result = subprocess.run(command, stdin=handle, cwd=project_root, check=False)
    return result.returncode


def shutil_which(command: str) -> str | None:
    """Small local wrapper kept separate for deterministic tests."""
    from shutil import which

    return which(command)


if __name__ == "__main__":
    raise SystemExit(main())
