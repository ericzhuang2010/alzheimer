#!/usr/bin/env python3
"""Integrity tests for the Phase 12 KDA network-figure artifacts."""

from __future__ import annotations

import hashlib
import math
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "figures" / "analysis" / "phease12_kda"
sys.path.insert(0, str(SCRIPT_DIR))

from phase12_kda_network_figure_common import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    SEX_REVERSAL_SPECS,
    WANG_PANEL_SPECS,
    node_area,
    read_tsv,
    validate_acat_example,
)


class Phase12KdaNetworkFigureTests(unittest.TestCase):
    output_dir = DEFAULT_OUTPUT_DIR

    def test_acat_implementation_matches_professor_example(self) -> None:
        self.assertLessEqual(validate_acat_example(), 5e-10)

    def test_connectivity_points_use_acat(self) -> None:
        row = read_tsv(self.output_dir / "phase12_kda_connectivity_evidence_points.tsv")[0]
        self.assertIn("acat_combined_p", row)
        self.assertIn("acat_negative_log10_p", row)
        self.assertEqual(row["acat_input_p_value"], "raw_p_value")
        self.assertEqual(row["acat_na_action"], "na.to1")
        self.assertNotIn("mean_of_log_score", row)
        self.assertNotIn("mean_of_log_score_standardized", row)

    def test_common_data_checks_pass(self) -> None:
        rows = read_tsv(self.output_dir / "phase12_kda_network_data_checks.tsv")
        self.assertGreaterEqual(len(rows), 7)
        failures = [row["check_id"] for row in rows if row["passed"] != "TRUE"]
        self.assertEqual(failures, [])

    def test_complex_v_definition_is_fixed(self) -> None:
        rows = read_tsv(self.output_dir / "phase12_kda_complex_v_genes.tsv")
        self.assertEqual(len(rows), 26)
        self.assertIn("ATP5F1A", {row["gene"] for row in rows})
        self.assertIn("ATP5PF", {row["gene"] for row in rows})

    def test_selected_convergence_counts(self) -> None:
        rows = read_tsv(self.output_dir / "phase12_kda_atp_convergence_pairs.tsv")
        observed = {
            (row["broad_network"], row["driver"], row["complex_v_target"]): int(row["qualifying_calls"])
            for row in rows
        }
        expected = {
            ("Astrocytes", "APOE", "ATP5PB"): 2,
            ("Excitatory_neurons", "GABARAPL2", "ATP5MC3"): 15,
            ("Excitatory_neurons", "LAMTOR5", "ATP5IF1"): 12,
            ("Excitatory_neurons", "RPL11", "ATP5PF"): 14,
            ("Inhibitory_neurons", "RPS15", "ATP5PF"): 6,
            ("OPCs", "FTL", "ATP5IF1"): 1,
            ("OPCs", "ANKRD11", "ATP5IF1"): 1,
        }
        for key, value in expected.items():
            self.assertEqual(observed.get(key), value, key)

    def test_wang_panels_have_expected_neighborhood_sizes_and_paths(self) -> None:
        nodes = read_tsv(self.output_dir / "phase12_kda_wang_subnetworks_nodes.tsv")
        counts: dict[str, int] = {}
        for row in nodes:
            counts[row["panel"]] = counts.get(row["panel"], 0) + 1
        self.assertEqual(counts, {"A": 19, "B": 27, "C": 45})
        paths = {
            (row["driver"], row["target"]): row["path"]
            for row in read_tsv(self.output_dir / "phase12_kda_wang_subnetworks_paths.tsv")
        }
        self.assertEqual(paths[("APOE", "ATP5F1A")], "APOE;LDHB;ATP5F1A")
        self.assertEqual(paths[("LAMTOR5", "ATP5MC2")], "LAMTOR5;POP7;ATP5MC2")
        self.assertEqual(paths[("GABARAPL2", "PARK7")], "GABARAPL2;MAGEF1;SNAPC5;PARK7")

    def test_paired_panels_share_coordinates(self) -> None:
        rows = read_tsv(self.output_dir / "phase12_kda_sex_reversal_networks_nodes.tsv")
        coordinates: dict[tuple[str, str], set[tuple[str, str]]] = {}
        for row in rows:
            key = (row["comparison_row"], row["gene"])
            coordinates.setdefault(key, set()).add((row["x"], row["y"]))
        self.assertTrue(coordinates)
        self.assertTrue(all(len(values) == 1 for values in coordinates.values()))
        expected_panels = len(SEX_REVERSAL_SPECS) * 2
        self.assertEqual(len({row["panel"] for row in rows}), expected_panels)

    def test_all_planned_outputs_exist_and_are_nonempty(self) -> None:
        basenames = [
            "phase12_kda_wang_subnetworks",
            "phase12_kda_sex_reversal_networks",
            "phase12_kda_atp_convergence",
            "phase12_kda_connectivity_evidence",
        ]
        for basename in basenames:
            for suffix in ("pdf", "svg", "png"):
                path = self.output_dir / f"{basename}.{suffix}"
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 1000, path)

    def test_specs_remain_prespecified(self) -> None:
        self.assertEqual(
            [(spec["panel"], spec["driver"]) for spec in WANG_PANEL_SPECS],
            [("A", "APOE"), ("B", "LAMTOR5"), ("C", "GABARAPL2")],
        )

    def test_node_diameter_scales_linearly_with_degree(self) -> None:
        diameters = [math.sqrt(node_area(degree)) for degree in range(1, 17)]
        self.assertEqual(diameters, [float(value) for value in range(8, 24)])
        self.assertGreater(node_area(16) / node_area(1), 8.0)

    def test_generation_log_hashes_match_files(self) -> None:
        rows = read_tsv(self.output_dir / "phase12_kda_network_figures_generation_log.tsv")
        self.assertGreaterEqual(len(rows), 29)
        for row in rows:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, row["sha256"], path)

    def test_pngs_are_300_dpi_scale(self) -> None:
        for basename in (
            "phase12_kda_wang_subnetworks",
            "phase12_kda_sex_reversal_networks",
            "phase12_kda_atp_convergence",
            "phase12_kda_connectivity_evidence",
        ):
            path = self.output_dir / f"{basename}.png"
            with path.open("rb") as handle:
                self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")
                handle.read(8)
                width, height = struct.unpack(">II", handle.read(8))
            self.assertGreaterEqual(width, 3000, path)
            self.assertGreaterEqual(height, 1500, path)

    def test_auditable_tables_store_visual_encodings(self) -> None:
        node = read_tsv(self.output_dir / "phase12_kda_wang_subnetworks_nodes.tsv")[0]
        edge = read_tsv(self.output_dir / "phase12_kda_wang_subnetworks_edges.tsv")[0]
        for field in ("logFC", "total_degree", "node_size_area", "display_label", "is_complex_v", "x", "y"):
            self.assertIn(field, node)
        for field in ("broad_network", "highlight_path", "edge_style", "line_width"):
            self.assertIn(field, edge)


if __name__ == "__main__":
    unittest.main()
