#!/usr/bin/env python3
"""Contract tests for the executed VH09/VH10 SEA-AD KDA validation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
VH09 = ROOT / "results/validation_human/09_rosmap_kda_candidates"
VH10 = ROOT / "results/validation_human/10_seaad_kda_rediscovery"


def load_phase18():
    path = ROOT / "scripts/18_key_driver_selection.py"
    spec = importlib.util.spec_from_file_location("phase18_test_authority", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Phase 18 authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Phase18HelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase18 = load_phase18()

    def test_acat_reference(self):
        self.assertLessEqual(self.phase18.validate_acat_example(), 1e-9)

    def test_bh_reference(self):
        observed = self.phase18.bh_adjust([0.01, 0.04, 0.03, 1.0, None])
        expected = [0.04, 0.05333333333333334, 0.05333333333333334, 1.0, None]
        for left, right in zip(observed, expected):
            if right is None:
                self.assertIsNone(left)
            else:
                self.assertAlmostEqual(left, right, places=14)


class ExecutedBundleTests(unittest.TestCase):
    def test_vh09_freeze_contract(self):
        status = pd.read_csv(VH09 / "status.tsv", sep="\t", keep_default_na=False)
        self.assertEqual(status.loc[0, "validation_status"], "validated_complete")
        self.assertEqual(int(status.loc[0, "selected_units"]), 47)
        self.assertEqual(int(status.loc[0, "passing_units"]), 78)
        self.assertEqual(int(status.loc[0, "selected_unique_genes"]), 25)

    def test_vh10_amended_tier_only(self):
        status = pd.read_csv(VH10 / "status.tsv", sep="\t", keep_default_na=False)
        self.assertEqual(status.loc[0, "validation_status"], "validated_complete")
        self.assertEqual(
            status.loc[0, "active_result_tier"],
            "posthoc_exploratory__fdr_only__donor3__query3__coverage50__q10",
        )
        self.assertEqual(int(status.loc[0, "active_kda_calls"]), 42)

        candidates = pd.read_csv(
            VH10 / "10c_seaad_selection/seaad_candidate_summary.tsv.gz",
            sep="\t",
            keep_default_na=False,
            low_memory=False,
        )
        self.assertEqual(
            set(candidates["result_tier_id"]),
            {"posthoc_exploratory__fdr_only__donor3__query3__coverage50__q10"},
        )
        self.assertNotIn("missing_as_one_acat_p", candidates.columns)
        self.assertNotIn("missing_as_one_acat_q", candidates.columns)

    def test_kda_and_selection_contract(self):
        run_qc = pd.read_csv(
            VH10 / "10b_kda/run_qc.tsv", sep="\t", keep_default_na=False
        )
        self.assertEqual(len(run_qc), 42)
        self.assertTrue(run_qc["terminal_status"].str.startswith("completed_").all())
        self.assertTrue(run_qc["r_python_significant_parity"].astype(bool).all())

        selection_status = pd.read_csv(
            VH10 / "10c_seaad_selection/status.tsv", sep="\t", keep_default_na=False
        )
        self.assertEqual(float(selection_status.loc[0, "minimum_coverage"]), 0.50)
        self.assertEqual(float(selection_status.loc[0, "aggregate_q_threshold"]), 0.10)
        self.assertEqual(int(selection_status.loc[0, "passing_candidate_units"]), 14)
        top5 = pd.read_csv(
            VH10 / "10c_seaad_selection/seaad_top5.tsv",
            sep="\t",
            keep_default_na=False,
        )
        selected = top5.loc[top5["list_status"].eq("ranked_candidates")].copy()
        self.assertEqual(len(selected), 14)
        self.assertFalse(
            selected.duplicated(["broad_network", "current_symbol", "case_id"]).any()
        )
        self.assertTrue(pd.to_numeric(selected["display_rank"]).le(5).all())

    def test_phase18_and_overlap_checks(self):
        for name in (
            "phase18_selection_parity_checks.tsv",
            "overlap_checks.tsv",
        ):
            checks = pd.read_csv(
                VH10 / "10d_overlap" / name,
                sep="\t",
                keep_default_na=False,
            )
            self.assertTrue(checks["passed"].astype(bool).all(), name)
        status = pd.read_csv(
            VH10 / "10d_overlap/status.tsv", sep="\t", keep_default_na=False
        )
        self.assertEqual(int(status.loc[0, "rosmap_selected_units"]), 47)
        self.assertEqual(int(status.loc[0, "rosmap_testable_selected_units"]), 36)
        self.assertEqual(int(status.loc[0, "strict_shared_top5_units"]), 6)


if __name__ == "__main__":
    unittest.main()
