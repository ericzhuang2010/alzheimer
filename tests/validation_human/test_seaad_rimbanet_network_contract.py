from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import networkx as nx


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "scripts/validation_human"
sys.path.insert(0, str(SCRIPT_DIR))

path = SCRIPT_DIR / "11_validate_publish_seaad_networks.py"
spec = importlib.util.spec_from_file_location("validate_publish", path)
validate_publish = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validate_publish)


def test_verified_legacy_consensus_thresholds():
    counts = Counter(
        {
            ("A", "B"): 200,
            ("B", "A"): 100,
            ("C", "D"): 150,
            ("D", "C"): 150,
            ("E", "F"): 149,
            ("F", "E"): 151,
            ("G", "H"): 149,
            ("H", "G"): 149,
        }
    )
    selected = validate_publish.selected_edges(counts, 1000, 0.15, 0.30)
    assert ("A", "B") in selected
    assert ("B", "A") not in selected
    assert {("C", "D"), ("D", "C")}.issubset(selected)
    assert ("F", "E") in selected
    assert ("E", "F") not in selected
    assert ("G", "H") not in selected
    assert ("H", "G") not in selected


def test_final_network_contract_example():
    graph = nx.DiGraph(
        [
            ("ROOT", "A"),
            ("ROOT", "B"),
            ("A", "C"),
            ("B", "C"),
        ]
    )
    assert nx.is_directed_acyclic_graph(graph)
    assert nx.number_of_selfloops(graph) == 0
    assert max(dict(graph.in_degree()).values()) <= 3
    assert not any(graph.has_edge(v, u) for u, v in graph.edges())


def test_jaccard_empty_and_nonempty():
    assert validate_publish.jaccard(set(), set()) == 1.0
    assert validate_publish.jaccard({("A", "B")}, {("A", "B")}) == 1.0
    assert validate_publish.jaccard({("A", "B")}, {("B", "A")}) == 0.0
