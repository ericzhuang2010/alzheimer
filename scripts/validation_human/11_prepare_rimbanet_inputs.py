#!/usr/bin/env python3
"""Validate discretized data and generate exact RIMBANet input contracts."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

from rimbanet_common import (
    configured_path,
    load_rimbanet_config,
    stage_dir,
    validate_network,
    write_stage_contract,
)
from seaad_common import atomic_copy, atomic_write_text, atomic_write_tsv


def read_discretized(path: Path):
    nodes, matrix, width = [], [], None
    with path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split("\t")
            width = width or len(fields)
            if len(fields) != width or len(fields) < 2:
                raise ValueError(f"Inconsistent row width at line {line_number}")
            if fields[0] in nodes:
                raise ValueError(f"Duplicate node {fields[0]}")
            states = [int(value) for value in fields[1:]]
            if any(value not in {0, 1, 2} for value in states):
                raise ValueError(f"Invalid state at line {line_number}")
            if set(states) != {0, 1, 2}:
                raise ValueError(f"Node {fields[0]} does not contain all three states")
            nodes.append(fields[0])
            matrix.append(states)
    if not nodes:
        raise ValueError("Discretized data is empty")
    return nodes, matrix, int(width - 1)


def node_xml(nodes: list[str], network: str) -> str:
    variables = []
    for node in nodes:
        variables.append(
            "<VARIABLE>\n"
            f"\t<NAME>{escape(node)}</NAME>\n"
            "\t<TYPE>discrete</TYPE>\n"
            "\t<VALUE>down</VALUE>\n"
            "\t<VALUE>no</VALUE>\n"
            "\t<VALUE>up</VALUE>\n"
            "</VARIABLE>"
        )
    return (
        '<?xml version="1.0"?>\n'
        "<!DOCTYPE BIF [\n"
        "\t<!ELEMENT BIF ( NETWORK )*>\n"
        "\t<!ELEMENT PROPERTY (#PCDATA)>\n"
        "\t<!ELEMENT TYPE (#PCDATA)>\n"
        "\t<!ELEMENT VALUE (#PCDATA)>\n"
        "\t<!ELEMENT NAME (#PCDATA)>\n"
        "\t<!ELEMENT NETWORK ( NAME, ( PROPERTY | VARIABLE | "
        "PROBABILITY | LIKELIHOOD)* )>\n"
        "\t<!ELEMENT VARIABLE ( NAME, TYPE, ( VALUE | PROPERTY )* )>\n"
        "\t<!ELEMENT PROBABILITY ( FOR | GIVEN | TABLE | ENTRY | "
        "DEFAULT | PROPERTY )*>\n"
        "\t<!ELEMENT PRIOR ( FOR | GIVEN | PROPERTY )*>\n"
        "\t<!ELEMENT FOR (#PCDATA)>\n"
        "\t<!ELEMENT GIVEN (#PCDATA)>\n"
        "\t<!ELEMENT TABLE (#PCDATA)>\n"
        "\t<!ELEMENT DEFAULT (TABLE)>\n"
        "\t<!ELEMENT ENTRY ( VALUE* , TABLE )>\n"
        "]>\n"
        f'<BIF>\n<NETWORK size="{len(nodes)}">\n'
        f"<NAME>{escape(network)} SEA-AD network</NAME>\n"
        "<!-- Variables -->\n"
        + "\n".join(variables)
        + "\n</NETWORK>\n</BIF>\n"
    )


def write_identity(size: int, path: Path) -> None:
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with temporary.open("wt", encoding="utf-8", newline="") as handle:
        for index in range(size):
            row = ["0"] * size
            row[index] = "1"
            handle.write(" ".join(row) + "\n")
    os.replace(temporary, path)


def generate_base_prior(
    binary: Path, node_path: Path, data_path: Path, samples: int, output: Path
) -> int:
    command = [
        str(binary),
        "-f",
        "0",
        "-b",
        node_path.name,
        "-d",
        data_path.name,
        "-t",
        "0",
        "-T",
        "0",
        "-D",
        str(samples),
        "-o",
        "base_prior_unused",
        "-r",
        "1",
        "-L",
        "1",
    ]
    temporary = output.with_name(f"{output.name}.tmp.{os.getpid()}")
    prior_rows = 0
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            command,
            cwd=data_path.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=stderr,
        )
        if process.stdout is None:
            process.kill()
            raise RuntimeError("RIMBANet base-prior stdout pipe is unavailable")
        try:
            with temporary.open("wt", encoding="utf-8", newline="") as handle:
                for line in process.stdout:
                    if ">" in line:
                        handle.write(line)
                        prior_rows += 1
        except BaseException:
            process.kill()
            process.wait()
            temporary.unlink(missing_ok=True)
            raise
        returncode = process.wait()
        stderr.seek(0)
        error_text = stderr.read()
    if returncode != 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"RIMBANet base-prior command failed ({returncode}): "
            f"{error_text[-2000:]}"
        )
    if not prior_rows:
        temporary.unlink(missing_ok=True)
        raise ValueError("RIMBANet produced no base-prior lines")
    os.replace(temporary, output)
    return prior_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--network", required=True)
    parser.add_argument("--binary")
    parser.add_argument(
        "--skip-base-prior",
        action="store_true",
        help="Fixture-only: validate/generate structural files without testBN",
    )
    args = parser.parse_args()
    config, config_path, project_root, output_root = load_rimbanet_config(args.config)
    network = validate_network(config, args.network)
    input_dir = stage_dir(output_root, "11e_inputs") / network
    input_dir.mkdir(parents=True, exist_ok=True)
    data_path = input_dir / "data.discretized.txt"
    if not data_path.exists():
        raise FileNotFoundError(data_path)
    nodes, _, sample_count = read_discretized(data_path)

    expression_sample = (
        stage_dir(output_root, "11b_expression", create=False)
        / network
        / "sample_manifest.tsv"
    )
    samples = pd.read_csv(expression_sample, sep="\t")
    if len(samples) != sample_count:
        raise ValueError("Discretized sample count differs from sample manifest")
    sample_copy = input_dir / "sample_manifest.tsv"
    atomic_copy(expression_sample, sample_copy)

    node_path = input_dir / "node.xml"
    banned_path = input_dir / "banned.txt"
    base_path = input_dir / "prior.base.txt"
    atomic_write_text(node_xml(nodes, network), node_path)
    write_identity(len(nodes), banned_path)

    binary = (
        Path(args.binary).resolve()
        if args.binary
        else configured_path(
            project_root, config["method"]["binary"], must_exist=False
        )
    )
    base_prior_rows = 0
    if not args.skip_base_prior:
        if not binary.exists():
            raise FileNotFoundError(binary)
        base_prior_rows = generate_base_prior(
            binary, node_path, data_path, sample_count, base_path
        )

    parameter_lines = [
        str(sample_count),
        str(len(nodes)),
        node_path.name,
        data_path.name,
        banned_path.name,
        "prior.txt",
        network,
        str(config["rimbanet"]["number_of_searches"]),
        config["rimbanet"]["output_directory"],
        config["rimbanet"]["output_prefix"],
    ]
    parameter_path = input_dir / "bn.param.txt"
    atomic_write_text("\n".join(parameter_lines) + "\n", parameter_path)
    nodes_path = input_dir / "nodes.tsv"
    atomic_write_tsv(
        pd.DataFrame(
            {
                "node_order": range(len(nodes)),
                "source_symbol": nodes,
            }
        ),
        nodes_path,
    )

    checks = [
        ("nodes_unique", len(nodes) == len(set(nodes)), len(set(nodes)), len(nodes), ""),
        ("sample_manifest_count", len(samples) == sample_count, len(samples), sample_count, ""),
        ("three_state_data", True, "0,1,2", "0,1,2", ""),
        ("node_xml_present", node_path.stat().st_size > 0, node_path.stat().st_size, ">0", ""),
        ("banned_rows", sum(1 for _ in banned_path.open()) == len(nodes), sum(1 for _ in banned_path.open()), len(nodes), ""),
        ("base_prior_present", args.skip_base_prior or base_path.exists(), base_path.exists(), not args.skip_base_prior, "skip is fixture-only"),
        (
            "base_prior_directed_rows",
            args.skip_base_prior or base_prior_rows == len(nodes) * (len(nodes) - 1),
            base_prior_rows,
            len(nodes) * (len(nodes) - 1),
            "all ordered non-self node pairs",
        ),
    ]
    failed = [name for name, passed, *_ in checks if not passed]
    state = (
        "fixture_validated"
        if args.skip_base_prior and not failed
        else "validated_complete"
        if not failed
        else "failed"
    )
    artifacts = [data_path, node_path, banned_path, parameter_path, nodes_path, sample_copy]
    if base_path.exists():
        artifacts.append(base_path)
    write_stage_contract(
        input_dir,
        "VH11E_INPUTS",
        state,
        config_path,
        project_root,
        checks,
        artifacts,
        network=network,
        nodes=len(nodes),
        samples=sample_count,
        base_prior_rows=base_prior_rows,
        binary=str(binary),
    )
    print(f"VH11E input status: {state}; network={network}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
