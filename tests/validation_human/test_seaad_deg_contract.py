import math
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validation_human"))

from seaad_common import phase_dir  # noqa: E402


class SeaadContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "scripts/validation_human/seaad_deg_config.yml").open() as handle:
            cls.config = yaml.safe_load(handle)

    def test_structural_counts(self):
        counts = self.config["taxonomy"]["expected_supertype_counts"]
        self.assertEqual(sum(counts.values()), 129)
        self.assertEqual(129 * 6, self.config["expected_identity"]["fine_contrasts"])
        self.assertEqual(129 * 6 * 2, self.config["expected_identity"]["fine_directions"])

    def test_query_rules_are_distinct_and_frozen(self):
        rules = self.config["query_rules"]
        self.assertIn("abs(logFC) > log2(1.3)", rules["phase18_parity_query"])
        self.assertEqual(rules["fdr_only_query_sensitivity"], "FDR < 0.05")
        self.assertAlmostEqual(
            math.log2(self.config["thresholds"]["absolute_fold_change"]),
            0.37851162325372983,
        )

    def test_output_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "results" / "validation_human"
            self.assertEqual(phase_dir(root, "contract_test").parent, root.resolve())
            with self.assertRaises(ValueError):
                phase_dir(root, "../escape")


if __name__ == "__main__":
    unittest.main()
