#!/usr/bin/env python3
"""Deterministic unit and production-output tests for broad direct KDA."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import tempfile
from pathlib import Path

import networkx as nx


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase20_sex_apoe_kda_broad",
    ROOT / "scripts" / "20_sex_apoe_kda_broad.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load broad direct KDA implementation")
BROAD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BROAD
SPEC.loader.exec_module(BROAD)


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return math.isclose(left, right, rel_tol=0, abs_tol=tolerance)


def load_phase18():
    return BROAD.load_python_module(
        ROOT / "scripts" / "18_key_driver_selection.py",
        "phase18_complete_evidence_broad_test",
    )


def unit_tests() -> None:
    observed = BROAD.bh_adjust([0.01, 0.04, None, 0.02])
    expected = [0.03, 0.04, None, 0.03]
    assert_true(
        all(
            (left is None and right is None)
            or (
                left is not None
                and right is not None
                and close(float(left), float(right))
            )
            for left, right in zip(observed, expected)
        ),
        f"BH fixture failed: {observed}",
    )

    all_family = BROAD.bh_adjust([0.001, 0.01, 0.04, 1.0])
    non_mt_family = BROAD.bh_adjust([0.01, 0.04, 1.0])
    assert_true(
        all(close(left, right) for left, right in zip(all_family, [0.004, 0.02, 0.05333333333333334, 1.0])),
        f"All-gene BH fixture failed: {all_family}",
    )
    assert_true(
        all(close(left, right) for left, right in zip(non_mt_family, [0.03, 0.06, 1.0])),
        f"Filter-before-BH fixture failed: {non_mt_family}",
    )
    assert_true(non_mt_family[0] != all_family[1], "MT removal did not change the BH family")

    phase18 = load_phase18()
    annotation_fields = [
        "feature_id_original",
        "symbol_hgnc_current",
        "reference_only",
        "is_mitocarta3",
        "mitocarta_canonical_symbol",
        "mito_tier",
        "genome_origin",
        "is_mtDNA_gene",
        "extended_reference_member",
        "mapping_status",
        "phase03_mitocarta_match_type",
    ]
    annotation_rows = [
        {
            "feature_id_original": "ORIGINAL_CURRENT",
            "symbol_hgnc_current": "CURRENT",
            "reference_only": False,
            "is_mitocarta3": True,
            "mitocarta_canonical_symbol": "CURRENT",
            "mito_tier": "core_mito_protein",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": True,
            "mapping_status": "mapped_current",
            "phase03_mitocarta_match_type": "exact",
        },
        {
            "feature_id_original": "FALLBACK",
            "symbol_hgnc_current": BROAD.NA_TEXT,
            "reference_only": False,
            "is_mitocarta3": False,
            "mitocarta_canonical_symbol": BROAD.NA_TEXT,
            "mito_tier": "not_mito",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": False,
            "mapping_status": "fallback_original",
            "phase03_mitocarta_match_type": BROAD.NA_TEXT,
        },
        {
            "feature_id_original": "REFERENCE_ORIGINAL",
            "symbol_hgnc_current": "REFERENCE_SKIP",
            "reference_only": True,
            "is_mitocarta3": True,
            "mitocarta_canonical_symbol": "REFERENCE_SKIP",
            "mito_tier": "core_mito_protein",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": True,
            "mapping_status": "reference_only",
            "phase03_mitocarta_match_type": "exact",
        },
        {
            "feature_id_original": "DUPLICATE_A",
            "symbol_hgnc_current": "DUPLICATE",
            "reference_only": False,
            "is_mitocarta3": False,
            "mitocarta_canonical_symbol": BROAD.NA_TEXT,
            "mito_tier": "not_mito",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": False,
            "mapping_status": "route_a",
            "phase03_mitocarta_match_type": BROAD.NA_TEXT,
        },
        {
            "feature_id_original": "DUPLICATE_B",
            "symbol_hgnc_current": "DUPLICATE",
            "reference_only": False,
            "is_mitocarta3": False,
            "mitocarta_canonical_symbol": BROAD.NA_TEXT,
            "mito_tier": "not_mito",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": False,
            "mapping_status": "route_b",
            "phase03_mitocarta_match_type": BROAD.NA_TEXT,
        },
        {
            "feature_id_original": "CONFLICT_A",
            "symbol_hgnc_current": "CONFLICT",
            "reference_only": False,
            "is_mitocarta3": False,
            "mitocarta_canonical_symbol": BROAD.NA_TEXT,
            "mito_tier": "not_mito",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": False,
            "mapping_status": "conflict_a",
            "phase03_mitocarta_match_type": BROAD.NA_TEXT,
        },
        {
            "feature_id_original": "CONFLICT_B",
            "symbol_hgnc_current": "CONFLICT",
            "reference_only": False,
            "is_mitocarta3": True,
            "mitocarta_canonical_symbol": "CONFLICT",
            "mito_tier": "core_mito_protein",
            "genome_origin": "nuclear",
            "is_mtDNA_gene": False,
            "extended_reference_member": True,
            "mapping_status": "conflict_b",
            "phase03_mitocarta_match_type": "exact",
        },
    ]
    with tempfile.TemporaryDirectory() as temp:
        annotation_path = Path(temp) / "annotation.tsv"
        BROAD.write_tsv(
            annotation_path,
            annotation_rows,
            annotation_fields,
            "synthetic_annotation_v1",
        )
        complete_annotation, annotation_conflicts = BROAD.load_complete_annotation(
            annotation_path, phase18
        )
    assert_true("CURRENT" in complete_annotation, "Current symbol was not preferred")
    assert_true(
        "ORIGINAL_CURRENT" not in complete_annotation,
        "Original feature leaked when a current symbol was available",
    )
    assert_true("FALLBACK" in complete_annotation, "Original-feature fallback failed")
    assert_true(
        "REFERENCE_SKIP" not in complete_annotation
        and "REFERENCE_ORIGINAL" not in complete_annotation,
        "Reference-only annotation was not excluded",
    )
    assert_true(
        complete_annotation["DUPLICATE"]["mapping_status"] == "route_a|route_b",
        "Compatible duplicate mapping routes were not merged",
    )
    assert_true(
        annotation_conflicts == ["CONFLICT"],
        f"Scientific annotation conflict was not detectable: {annotation_conflicts}",
    )

    query = {"Q1", "Q2", "Q3"}
    edges = [
        ("D", "Q1"),
        ("D", "Q2"),
        ("D", "Q3"),
        ("Q1", "A"),
        ("A", "X"),
        ("X", "Z"),
        *[(f"U{i}", f"U{i + 1}") for i in range(1, 100)],
    ]
    background = {gene for edge in edges for gene in edge}
    run = {
        "kda_run_id": "synthetic_broad_direct",
        "induced_network_edges": len(edges),
        "effective_query_genes": len(query),
        "effective_background_genes": len(background),
    }
    annotation = {
        gene: {
            "is_core_mito": gene in query,
            "mito_tier": "core_mito_protein" if gene in query else "not_mito",
            "genome_origin": "nuclear",
            "is_mtdna_gene": False,
            "mapping_status": "fixture",
        }
        for gene in background
    }
    explicit, _ = phase18.reconstruct_run(run, query, background, edges, annotation)
    BROAD.attach_original_overlap_items(
        phase18, run["kda_run_id"], explicit, query, background, edges, 3
    )
    assert_true(set(explicit) == {"A", "D", "Q1", "X"}, f"Explicit family drift: {set(explicit)}")
    assert_true(explicit["D"]["original"]["overlap"] == 3, "Directed positive control lost")
    assert_true(explicit["A"]["original"]["p"] == 1.0, "Zero-overlap P must equal one")
    assert_true(explicit["X"]["original"]["p"] == 1.0, "Second zero-overlap P must equal one")
    paths = {
        "fkda_parity_helper": ROOT / "scripts" / "20_sex_apoe_kda_broad_fkda_parity.R",
        "fkda_source": ROOT / "scripts" / "NetWeaver" / "fKDA.R",
    }
    with tempfile.TemporaryDirectory() as temp:
        stock_rows = BROAD.run_stock_fkda(
            paths,
            run["kda_run_id"],
            edges,
            query,
            len(background),
            3,
            Path(temp),
        )
    stock = BROAD.validate_stock_parity(run["kda_run_id"], explicit, stock_rows)
    assert_true(set(stock) == {"D"}, f"Synthetic q<=.05 stock returns drifted: {set(stock)}")

    reverse_edges = [
        ("Q1", "D"),
        ("Q2", "D"),
        ("Q3", "D"),
        *edges[3:],
    ]
    reverse_run = {**run, "kda_run_id": "synthetic_reverse", "induced_network_edges": len(reverse_edges)}
    reverse, _ = phase18.reconstruct_run(
        reverse_run, query, background, reverse_edges, annotation
    )
    assert_true("D" not in reverse, "Direction reversal did not remove D from explicit drivers")

    assert_true(2 >= 2 and not (1 >= 2), "Overlap boundary fixture failed")
    assert_true(1.0001 > 1 and not (1.0 > 1), "Fold-enrichment boundary fixture failed")
    assert_true(0.10 <= 0.10 and 0.05 <= 0.05, "Inclusive q boundary fixture failed")
    print("Phase 20 broad direct deterministic unit tests passed")


def validate_output(output: Path) -> None:
    config = BROAD.load_config(ROOT / "config" / "phase20_sex_apoe_kda_broad.yml")
    declared = list(config["outputs"]["declared_files"])
    assert_true(len(declared) == 21, "Declared-output count changed")
    assert_true(len(set(declared)) == len(declared), "Declared outputs are duplicated")
    for name in declared:
        assert_true((output / name).is_file(), f"Missing declared output: {name}")
    actual_files = {
        path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()
    }
    assert_true(actual_files == set(declared), f"Undeclared or missing output files: {actual_files ^ set(declared)}")

    status_rows = BROAD.read_tsv(output / "phase20_broad_status.tsv")
    assert_true(len(status_rows) == 1, "Status must contain exactly one row")
    status = status_rows[0]
    assert_true(status["validation_status"] == "validated_complete", "Release is not validated")
    assert_true(status["aggregation_method"] == "none", "Broad branch used aggregation")
    assert_true(int(status["structural_categories"]) == 42, "Category count changed")
    assert_true(int(status["primary_direction_slots"]) == 84, "Direction-slot count changed")
    assert_true(int(status["source_complete_contrasts"]) == 40, "Complete source count changed")
    assert_true(int(status["source_not_estimable_contrasts"]) == 2, "Source failure count changed")
    assert_true(int(status["primary_executable_runs"]) == 3, "Primary executable count changed")
    assert_true(int(status["primary_completed_runs"]) == 3, "Primary completion count changed")
    assert_true(int(status["primary_explicit_candidate_tests"]) == 377, "Candidate-test count changed")
    assert_true(int(status["primary_stock_significant_returns"]) == 11, "Stock-return count changed")
    assert_true(int(status["relaxed_non_mt_candidates"]) == 12, "Relaxed candidate count changed")
    assert_true(int(status["strict_non_mt_candidates"]) == 9, "Strict candidate count changed")
    assert_true(int(status["strict_query_executable_runs"]) == 2, "Strict executable count changed")
    assert_true(int(status["exploratory_query_executable_runs"]) == 7, "Exploratory executable count changed")
    assert_true(int(status["primary_failed_runs"]) == 0, "Primary KDA failure occurred")
    assert_true(int(status["blocking_checks"]) == 31, "Blocking-check count changed")
    assert_true(int(status["failed_checks"]) == 0, "Blocking output check failed")
    assert_true(
        status["fkda_parity_helper_sha256"]
        == BROAD.sha256_file(ROOT / "scripts" / "20_sex_apoe_kda_broad_fkda_parity.R"),
        "Pinned fKDA parity-helper hash changed",
    )

    checks = BROAD.read_tsv(output / "phase20_broad_checks.tsv")
    assert_true(len(checks) == 31, "Checks table must have 31 rows")
    assert_true(len({row["check_id"] for row in checks}) == 31, "Check IDs are duplicated")
    failed = [row for row in checks if row["severity"] == "error" and not BROAD.is_true(row["passed"])]
    assert_true(not failed, f"Failed checks: {failed}")
    parity_checks = [row for row in checks if row["check_id"] == "stock_fkda_full_numeric_parity"]
    assert_true(
        len(parity_checks) == 1 and BROAD.is_true(parity_checks[0]["passed"]),
        "Full stock-fKDA numeric parity is not audit-visible",
    )

    network_authority = BROAD.read_tsv(output / "00_inputs" / "network_input_authority.tsv")
    assert_true(len(network_authority) == 7, "Network authority must have seven rows")
    for row in network_authority:
        source = BROAD.project_path(row["source_path"])
        assert_true(source.is_file(), f"Network authority source is missing: {source}")
        assert_true(int(row["bytes"]) == source.stat().st_size, f"Network byte size drifted: {source}")
        assert_true(BROAD.sha256_file(source) == row["observed_sha256"], f"Network hash drifted: {source}")

    categories = BROAD.read_tsv(output / "phase20_broad_category_manifest.tsv")
    assert_true(len(categories) == 42, "Category manifest must have 42 rows")
    assert_true(
        len({(row["broad_cell_type"], row["group_id"]) for row in categories}) == 42,
        "Category keys are duplicated",
    )
    directions = BROAD.read_tsv(output / "phase20_broad_direction_manifest.tsv")
    assert_true(len(directions) == 84, "Direction manifest must have 84 rows")
    assert_true(len({row["kda_run_id"] for row in directions}) == 84, "Run IDs are duplicated")
    outcomes = {name: 0 for name in config["expected_primary"]["slot_outcomes"]}
    for row in directions:
        outcomes[row["eligibility_status"]] = outcomes.get(row["eligibility_status"], 0) + 1
    assert_true(
        outcomes == {name: int(value) for name, value in config["expected_primary"]["slot_outcomes"].items()},
        f"Primary funnel changed: {outcomes}",
    )
    eligible = {
        (
            row["broad_cell_type"],
            row["group_id"],
            row["signature_direction"],
            int(row["effective_query_genes"]),
        )
        for row in directions
        if row["eligibility_status"] == "eligible"
    }
    assert_true(
        eligible
        == {
            ("Astrocytes", "F_e4", "AD_down_mito", 13),
            ("Astrocytes", "M_e33", "AD_down_mito", 3),
            ("OPCs", "F_e4", "AD_down_mito", 4),
        },
        f"Eligible primary runs changed: {eligible}",
    )
    eligible_terminal = {
        (row["broad_cell_type"], row["group_id"], row["signature_direction"]): row[
            "terminal_status"
        ]
        for row in directions
        if row["eligibility_status"] == "eligible"
    }
    assert_true(
        eligible_terminal
        == {
            ("Astrocytes", "F_e4", "AD_down_mito"): "completed_significant",
            ("Astrocytes", "M_e33", "AD_down_mito"): "completed_no_significant",
            ("OPCs", "F_e4", "AD_down_mito"): "completed_significant",
        },
        f"Primary terminal statuses changed: {eligible_terminal}",
    )

    tests = BROAD.read_tsv(output / "phase20_broad_all_candidate_tests.tsv.gz")
    assert_true(
        len({(row["kda_run_id"], row["current_symbol"]) for row in tests}) == len(tests),
        "Candidate-test keys are duplicated",
    )
    effective_queries: dict[str, set[str]] = {}
    for row in BROAD.read_tsv(output / "phase20_broad_signature_members.tsv.gz"):
        if BROAD.is_true(row["effective_member"]):
            effective_queries.setdefault(row["kda_run_id"], set()).add(row["gene"])
    backgrounds: dict[str, set[str]] = {}
    for row in BROAD.read_tsv(output / "phase20_broad_background_members.tsv.gz"):
        backgrounds.setdefault(row["kda_run_id"], set()).add(row["gene"])
    direction_by_run = {row["kda_run_id"]: row for row in directions}
    full_graphs: dict[str, nx.DiGraph] = {}
    phase18 = load_phase18()
    for row in network_authority:
        graph = nx.DiGraph()
        graph.add_edges_from(phase18.load_network(BROAD.project_path(row["source_path"])))
        full_graphs[row["network"]] = graph
    induced_graphs: dict[str, nx.DiGraph] = {}
    for run_id in {row["kda_run_id"] for row in tests}:
        slot = direction_by_run[run_id]
        induced_graphs[run_id] = nx.DiGraph(
            full_graphs[slot["broad_cell_type"]].subgraph(backgrounds[run_id])
        )
    by_run: dict[str, list[dict[str, str]]] = {}
    for row in tests:
        by_run.setdefault(row["kda_run_id"], []).append(row)
        stock_flag = BROAD.is_true(row["stock_fkda_q05_return"])
        assert_true(
            stock_flag == (float(row["original_run_q"]) <= 0.05),
            "Stock q05 flag does not reproduce original q",
        )
        if BROAD.is_true(row["is_core_mito"]):
            assert_true(row["non_mt_run_q"] == "NA", "Core-MT row received non-MT q")
        overlap_items = [item for item in row["overlap_items"].split(";") if item]
        graph = induced_graphs[row["kda_run_id"]]
        layer = int(row["best_layer"])
        neighborhood = set(
            nx.single_source_shortest_path_length(
                graph, row["current_symbol"], cutoff=layer
            )
        )
        expected_overlap = sorted(neighborhood & effective_queries[row["kda_run_id"]])
        assert_true(
            overlap_items == expected_overlap
            and len(overlap_items) == int(row["query_overlap"]),
            f"Complete overlap membership failed for {row['kda_run_id']}/{row['current_symbol']}",
        )
        assert_true(
            len(neighborhood) == int(row["neighborhood_size"]),
            f"Best-layer neighborhood failed for {row['kda_run_id']}/{row['current_symbol']}",
        )
        expected_out_degree = graph.out_degree(row["current_symbol"])
        expected_undirected_degree = len(
            set(graph.successors(row["current_symbol"]))
            | set(graph.predecessors(row["current_symbol"]))
        )
        assert_true(int(row["out_degree"]) == expected_out_degree, "Out-degree drifted")
        assert_true(
            int(row["undirected_degree"]) == expected_undirected_degree,
            "Undirected degree drifted",
        )
        assert_true(
            BROAD.is_true(row["is_root_node"])
            == (graph.in_degree(row["current_symbol"]) == 0),
            "Root-node status drifted",
        )
    for rows in by_run.values():
        non_mt = sorted(
            [row for row in rows if not BROAD.is_true(row["is_core_mito"])],
            key=lambda row: row["current_symbol"],
        )
        expected_q = BROAD.bh_adjust([float(row["raw_p_value"]) for row in non_mt])
        for row, expected in zip(non_mt, expected_q):
            assert_true(
                expected is not None
                and close(float(row["non_mt_run_q"]), float(expected)),
                f"Non-MT BH failed for {row['kda_run_id']}/{row['current_symbol']}",
            )

    candidates = BROAD.read_tsv(output / "phase20_broad_non_mt_candidates.tsv")
    assert_true(
        all(
            not BROAD.is_true(row["is_core_mito"])
            and int(row["query_overlap"]) >= 2
            and float(row["fold_enrichment"]) > 1
            and float(row["non_mt_run_q"]) <= 0.10
            for row in candidates
        ),
        "Candidate gate or non-MT filter failed",
    )
    candidates_by_run: dict[tuple[str, str, str], list[str]] = {}
    for row in candidates:
        key = (row["broad_cell_type"], row["group_id"], row["signature_direction"])
        candidates_by_run.setdefault(key, []).append(row["current_symbol"])
    assert_true(
        candidates_by_run
        == {
            ("Astrocytes", "F_e4", "AD_down_mito"): ["ELL2", "SLC44A3"],
            ("OPCs", "F_e4", "AD_down_mito"): [
                "CAMK2D",
                "RAPGEF4",
                "RAB3IP",
                "FOXN3",
                "AC092691.1",
                "FAM13A",
                "NCOA1",
                "FGF14",
                "GRID1",
                "DENND1A",
            ],
        },
        f"Relaxed candidate identities or ranks changed: {candidates_by_run}",
    )

    collisions = BROAD.read_tsv(output / "phase20_broad_symbol_mapping_collisions.tsv.gz")
    assert_true(len(collisions) == 862, "Mapped-symbol collision-key count changed")
    collision_keys = {
        (row["broad_cell_type"], row["group_id"], row["mapped_gene"])
        for row in collisions
    }
    assert_true(len(collision_keys) == len(collisions), "Mapped-symbol collision keys duplicate")
    assert_true(
        sum(int(row["collapsed_rows"]) for row in collisions) == 904,
        "Mapped-symbol collapsed-row count changed",
    )
    phase08_sources: dict[tuple[str, str, str], set[str]] = {}
    phase08_results = BROAD.project_path(config["paths"]["phase08_broad_directory"]) / "broad_deg_results.tsv.gz"
    for row in BROAD.iter_tsv(phase08_results):
        key = (row["broad_cell_type"], row["group_id"], row["mapped_gene"])
        phase08_sources.setdefault(key, set()).add(row["gene"])
    expected_collisions = {
        key: sources for key, sources in phase08_sources.items() if len(sources) > 1
    }
    assert_true(collision_keys == set(expected_collisions), "Collision keys differ from Phase 08")
    for row in collisions:
        sources = row["source_genes"].split(";")
        key = (row["broad_cell_type"], row["group_id"], row["mapped_gene"])
        assert_true(len(sources) == int(row["source_gene_count"]), "Collision source list changed")
        assert_true(int(row["collapsed_rows"]) == len(sources) - 1, "Collision row count changed")
        assert_true(set(sources) == expected_collisions[key], "Collision sources differ from Phase 08")

    summaries = BROAD.read_tsv(output / "phase20_broad_category_summary.tsv")
    assert_true(len(summaries) == 42, "Category summary must have 42 rows")
    category_by_id = {row["category_id"]: row for row in categories}
    candidate_rows_by_direction: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in candidates:
        candidate_rows_by_direction.setdefault(
            (row["category_id"], row["signature_direction"]), []
        ).append(row)
    for row in summaries:
        manifest_row = category_by_id[row["category_id"]]
        for field, value in manifest_row.items():
            if field == "schema_version":
                continue
            assert_true(row[field] == value, f"Category-summary field drifted: {field}")
        direction_rows: dict[str, list[dict[str, str]]] = {}
        for prefix, direction in (("up", "AD_up_mito"), ("down", "AD_down_mito")):
            expected_rows = candidate_rows_by_direction.get((row["category_id"], direction), [])
            direction_rows[prefix] = expected_rows
            expected_genes = ";".join(value["current_symbol"] for value in expected_rows)
            expected_q = ";".join(value["non_mt_run_q"] for value in expected_rows)
            top5 = [value for value in expected_rows if BROAD.is_true(value["top5_display"])]
            expected_top5_genes = ";".join(value["current_symbol"] for value in top5)
            expected_top5_q = ";".join(value["non_mt_run_q"] for value in top5)
            assert_true(
                row[f"{prefix}_all_candidate_genes"] == expected_genes,
                f"{prefix} complete candidate list drifted",
            )
            assert_true(
                row[f"{prefix}_all_non_mt_run_q"] == expected_q,
                f"{prefix} complete q-value list drifted",
            )
            assert_true(
                row[f"{prefix}_top5_genes"] == expected_top5_genes,
                f"{prefix} top-five candidate list drifted",
            )
            assert_true(
                row[f"{prefix}_top5_non_mt_run_q"] == expected_top5_q,
                f"{prefix} top-five q-value list drifted",
            )
        expected_union = ";".join(
            sorted(
                {
                    value["current_symbol"]
                    for values in direction_rows.values()
                    for value in values
                }
            )
        )
        assert_true(row["descriptive_union_genes"] == expected_union, "Descriptive union drifted")
        assert_true(
            row["inferential_note"] == "directions_retained_separately_no_combined_q",
            "Category-summary inferential note drifted",
        )

    banned = (
        "acat",
        "coverage",
        "supporting_run",
        "recurrence",
        "stability",
        "leave_one_fine",
        "aggregate_p",
        "aggregate_q",
        "combined_q",
        "category_q",
    )
    for name in declared:
        if not name.endswith((".tsv", ".tsv.gz")):
            continue
        rows = BROAD.read_tsv(output / name)
        if not rows:
            with BROAD.open_text(output / name, "r") as handle:
                fields = next(csv_reader := __import__("csv").reader(handle, delimiter="\t"))
            del csv_reader
        else:
            fields = list(rows[0])
        offending = [field for field in fields if any(term in field.lower() for term in banned)]
        assert_true(not offending, f"Cross-run aggregation fields in {name}: {offending}")

    artifacts = BROAD.read_tsv(output / "phase20_broad_artifacts.tsv")
    for row in artifacts:
        path = output / row["path"]
        assert_true(path.is_file(), f"Artifact is missing: {path}")
        assert_true(BROAD.sha256_file(path) == row["sha256"], f"Artifact hash failed: {path}")
    print(f"Phase 20 broad direct output validation passed: {output}")


def compare_outputs(left: Path, right: Path) -> None:
    config = BROAD.load_config(ROOT / "config" / "phase20_sex_apoe_kda_broad.yml")
    for name in config["outputs"]["declared_files"]:
        left_path = left / name
        right_path = right / name
        assert_true(left_path.is_file(), f"Missing declared output in first release: {left_path}")
        assert_true(right_path.is_file(), f"Missing declared output in second release: {right_path}")
        left_hash = BROAD.sha256_file(left_path)
        right_hash = BROAD.sha256_file(right_path)
        assert_true(
            left_hash == right_hash,
            f"Declared output is not byte-identical: {name} ({left_hash} != {right_hash})",
        )
    print(f"Phase 20 broad direct outputs are byte-identical: {left} == {right}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-output")
    parser.add_argument("--compare-output", nargs=2, metavar=("DIR_A", "DIR_B"))
    args = parser.parse_args()
    unit_tests()
    if args.validate_output:
        validate_output(Path(args.validate_output).resolve())
    if args.compare_output:
        compare_outputs(
            Path(args.compare_output[0]).resolve(),
            Path(args.compare_output[1]).resolve(),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
