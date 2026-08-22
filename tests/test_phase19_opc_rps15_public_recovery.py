from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load(ROOT / "scripts/19_audit_opc_rps15_public_qtl.py", "opc_rps15_runner_test")
INTEGRATOR = load(ROOT / "scripts/19_integrate_opc_rps15_evidence.py", "opc_rps15_integrator_test")


class ContextRulesTest(unittest.TestCase):
    def test_exact_opc(self):
        metadata = {"cell type": "Oligodendrocyte progenitor cell", "Biosample type": "Primary cell", "Tissue category": "Brain"}
        self.assertEqual(RUNNER.context_match("GS045", "snuc-eQTL", metadata), ("exact_opc", True, 1))

    def test_opc_lineage(self):
        metadata = {"cell type": "Oligodendrocyte", "Biosample type": "Primary cell", "Tissue category": "Brain"}
        self.assertEqual(RUNNER.context_match("GS045", "eQTL", metadata), ("oligodendroglial_lineage", True, 3))

    def test_exact_inhibitory(self):
        metadata = {"cell type": "Inhibitory neuron", "Biosample type": "Primary cell", "Tissue category": "Brain"}
        self.assertEqual(RUNNER.context_match("GS044", "snuc-eQTL", metadata), ("exact_inhibitory", True, 1))

    def test_bulk_not_context_specific(self):
        metadata = {"cell type": "Parietal cortex", "Biosample type": "Primary tissue", "Tissue category": "Brain"}
        self.assertEqual(RUNNER.context_match("GS045", "eQTL", metadata), ("bulk_brain_fallback", True, 4))

    def test_microglia_ineligible_for_opc(self):
        metadata = {"cell type": "Microglia", "Biosample type": "Primary cell", "Tissue category": "Brain"}
        self.assertEqual(RUNNER.context_match("GS045", "eQTL", metadata), ("context_not_eligible", False, 99))


class EvidenceIntegrationTest(unittest.TestCase):
    def test_pip_only_signal_is_weak_not_validated(self):
        rows = [{
            "eligible": "TRUE",
            "context_match": "exact_opc",
            "route_terminal_status": "model_or_ld_incompatible",
            "source_significant_rows": "2",
            "target_rows": "5",
            "cohort": "ROSMAP_CUIMC1",
            "route_id": "r1",
            "reason": "no complete model",
        }]
        result = INTEGRATOR.summarize_candidate("GS045", "OPCs", rows)
        self.assertEqual(result["gene_evidence_grade"], "weak")
        self.assertEqual(result["gene_validated"], "FALSE")
        self.assertEqual(result["context_validated"], "FALSE")
        self.assertEqual(result["maximum_pp_h4"], "NA")

    def test_explicit_null_is_no_support(self):
        rows = [{
            "eligible": "TRUE",
            "context_match": "exact_inhibitory",
            "route_terminal_status": "no_regional_qtl_signal",
            "source_significant_rows": "0",
            "target_rows": "3",
            "cohort": "ROSMAP_CUIMC1",
            "route_id": "r2",
            "reason": "explicit null",
        }]
        result = INTEGRATOR.summarize_candidate("GS044", "Inhibitory_neurons", rows)
        self.assertEqual(result["gene_evidence_grade"], "none")
        self.assertEqual(result["gene_validated"], "FALSE")


class ContractTest(unittest.TestCase):
    def test_declared_files_and_storage(self):
        config = yaml.safe_load((ROOT / "config/phase19_opc_rps15_public_recovery.yml").read_text())
        self.assertEqual(config["outputs"]["exact_file_count"], 24)
        self.assertEqual(len(config["outputs"]["declared_files"]), 24)
        self.assertFalse(config["storage"]["automatic_full_archive_download"])
        self.assertFalse(config["storage"]["allow_full_all_archives"])
        self.assertEqual(config["storage"]["maximum_targeted_download_gib"], 5)
        self.assertEqual(config["storage"]["maximum_total_new_download_gib"], 10)
        self.assertEqual(config["storage"]["maximum_total_new_disk_footprint_gib"], 20)

    def test_planned_implementation_files_exist(self):
        for relative in RUNNER.CODE_FILES:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_published_bundle_if_present(self):
        output = ROOT / "results/minerva_production/19_genetic_support_opc_rps15_public_recovery"
        if not output.exists():
            self.skipTest("Published bundle not created yet")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/19_validate_opc_rps15_public_recovery.py"), "--output-root", str(output)],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    unittest.main()
