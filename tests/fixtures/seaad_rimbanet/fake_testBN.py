#!/usr/bin/env python3
"""Tiny test double for RIMBANet CLI contract tests; not a BN implementation."""

from __future__ import annotations

import sys
from pathlib import Path


def option(name: str, default=None):
    if name not in sys.argv:
        return default
    return sys.argv[sys.argv.index(name) + 1]


data_path = Path(option("-d"))
nodes = [line.split()[0] for line in data_path.read_text().splitlines() if line.strip()]

if option("-L") == "1":
    for parent in nodes:
        for child in nodes:
            if parent != child:
                print(f"{parent} -> {child} -1.0 0.1")
    raise SystemExit(0)

output = Path(option("-o"))
candidate = option("-c")
if candidate:
    edges = []
    for line in Path(candidate).read_text().splitlines():
        if "->" not in line:
            continue
        parent, rest = line.split("->", 1)
        child = rest.split()[0].split("[")[0].rstrip(";")
        if parent < child:
            edges.append((parent, child))
else:
    seed = int(option("-s", "0"))
    edges = [(nodes[i], nodes[i + 1]) for i in range(len(nodes) - 1)]
    if seed % 2 and len(nodes) > 2:
        edges.append((nodes[0], nodes[2]))

output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w") as handle:
    handle.write("digraph G {\n")
    for parent, child in edges:
        handle.write(f"{parent}->{child}\n")
    handle.write("}\n")
print("LIKELIHOOD -1.0")
