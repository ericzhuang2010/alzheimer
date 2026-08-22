#!/usr/bin/env python3
"""Regression tests for the Phase 19 CSF endophenotype extension."""

from __future__ import annotations

import csv
import importlib.util
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/phase19_endophenotype_gwas_qtl_extension.yml"
RUNNER = ROOT / "scripts/19_run_endophenotype_extension.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("phase19_endophenotype_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_tsv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class EndophenotypeExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        cls.runner = load_runner()
        cls.output = ROOT / cls.config["outputs"]["root"]

    def test_frozen_design_counts_and_thresholds(self):
        analysis = self.config["analysis"]
        self.assertEqual(analysis["expected_candidate_contexts"], 47)
        self.assertEqual(analysis["expected_unique_genes"], 25)
        self.assertEqual(analysis["expected_nuclear_screens"], 57)
        self.assertEqual(analysis["expected_context_biomarker_rows"], 141)
        self.assertAlmostEqual(analysis["candidate_magma_p"], 0.05 / 57)
        self.assertEqual(len(self.config["biomarkers"]), 3)

    def test_candidate_and_region_freezes(self):
        candidates = read_tsv(ROOT / self.config["inputs"]["candidate_manifest"])
        regions = read_tsv(ROOT / self.config["inputs"]["recovery_regions"])
        self.assertEqual(len(candidates), 47)
        self.assertEqual(len({row["gene"] for row in candidates}), 25)
        self.assertEqual(len(regions), 19)
        self.assertEqual(
            {row["gene"] for row in regions},
            {row["gene"] for row in candidates if row["is_mtdna_gene"].lower() != "true"},
        )

    def test_declared_output_contract(self):
        self.assertEqual(len(self.runner.DECLARED_FILES), 36)
        self.assertEqual(len(set(self.runner.DECLARED_FILES)), 36)

    def test_published_output_if_present(self):
        if not self.output.exists():
            self.skipTest("Production extension has not been published yet")
        observed = sorted(path.name for path in self.output.iterdir() if path.is_file())
        self.assertEqual(observed, sorted(self.runner.DECLARED_FILES))
        status = read_tsv(self.output / "endophenotype_status.tsv")
        checks = read_tsv(self.output / "endophenotype_checks.tsv")
        self.assertEqual(len(status), 1)
        self.assertEqual(status[0]["technical_status"], "validated_complete")
        self.assertTrue(all(row["status"] == "pass" for row in checks))
        self.assertEqual(len(read_tsv(self.output / "endophenotype_gate_decisions.tsv")), 57)
        self.assertEqual(len(read_tsv(self.output / "endophenotype_context_biomarker_matrix.tsv")), 141)


    def test_atlas_route_classification_if_published(self):
        if not self.output.exists():
            self.skipTest("Production extension has not been published yet")
        routes = read_tsv(self.output / "endophenotype_route_manifest.tsv")
        atlas = [row for row in routes if row["qtl_source_id"] == "NG00184.v1"]
        self.assertEqual(len(atlas), 12)
        sqtl = [row for row in atlas if row["qtl_modality"] == "sQTL"]
        no_signal = [row for row in atlas if row["qtl_modality"] != "sQTL"]
        self.assertEqual(len(sqtl), 3)
        self.assertTrue(all(row["qtl_signal_state"] == "source_significant_cis_signal" for row in sqtl))
        self.assertTrue(all(row["route_terminal_status"] == "model_or_ld_incompatible" for row in sqtl))
        self.assertEqual(len(no_signal), 9)
        self.assertTrue(all(row["route_terminal_status"] == "no_regional_qtl_signal" for row in no_signal))

        inventory = read_tsv(self.output / "endophenotype_input_inventory.tsv")
        atlas_inputs = [row for row in inventory if row["source_id"] == "NG00184.v1"]
        self.assertEqual(len(atlas_inputs), 9)
        self.assertTrue(all(row["validation_state"].startswith("validated_official_md5_") for row in atlas_inputs))

    def test_magma_window_sensitivity_if_published(self):
        if not self.output.exists():
            self.skipTest("Production extension has not been published yet")
        rows = read_tsv(self.output / "endophenotype_magma_conditional.tsv")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["gene"] == "APOE" for row in rows))
        self.assertTrue(all(row["sensitivity_status"] == "tested_window_10kb" for row in rows))
        threshold = float(self.config["analysis"]["candidate_magma_p"])
        self.assertTrue(all(float(row["window_10kb_p"]) < threshold for row in rows))

    def test_no_new_biomarker_validation_if_published(self):
        if not self.output.exists():
            self.skipTest("Production extension has not been published yet")
        status = read_tsv(self.output / "endophenotype_status.tsv")
        matrix = read_tsv(self.output / "endophenotype_context_biomarker_matrix.tsv")
        self.assertEqual(status[0]["newly_biomarker_supported_unique_genes"], "0")
        self.assertTrue(all(row["newly_biomarker_supported"].lower() == "false" for row in matrix))

if __name__ == "__main__":
    unittest.main()
