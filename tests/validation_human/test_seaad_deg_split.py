import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validation_human"))

from seaad_common import sha256_file  # noqa: E402


FINE_ROOT = ROOT / "results/validation_human/08_deg_fine"
BROAD_ROOT = ROOT / "results/validation_human/08_deg_broad"
OLD_ROOT = ROOT / "results/validation_human/08_deg"


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", keep_default_na=False)


class SeaadDegSplitTest(unittest.TestCase):
    def test_split_prefix_rewrite_is_exact(self):
        import importlib.util

        script = ROOT / "scripts/validation_human/08_split_deg_release.py"
        spec = importlib.util.spec_from_file_location("seaad_deg_split", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.tsv"
            path.write_text(
                "path\nresults/validation_human/08_deg/example.tsv\n",
                encoding="utf-8",
            )
            module.rewrite_prefix(
                path,
                "results/validation_human/08_deg/",
                "results/validation_human/08_deg_fine/",
            )
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "path\nresults/validation_human/08_deg_fine/example.tsv\n",
            )

    def validate_release(
        self,
        release_root: Path,
        status_schema: str,
        expected_scope: str,
    ):
        status = read_table(release_root / "status.tsv")
        checks = read_table(release_root / "deg_checks.tsv")
        artifacts = read_table(release_root / "artifacts.tsv")
        self.assertEqual(len(status), 1)
        self.assertEqual(status.loc[0, "schema_version"], status_schema)
        self.assertEqual(status.loc[0, "release_scope"], expected_scope)
        self.assertEqual(status.loc[0, "validation_status"], "validated_complete")
        self.assertTrue(checks["passed"].astype(bool).all())
        self.assertEqual(
            int(status.loc[0, "artifact_count"]), len(artifacts)
        )
        self.assertEqual(
            status.loc[0, "artifact_manifest_sha256"],
            sha256_file(release_root / "artifacts.tsv"),
        )
        code_paths = [
            ROOT / "scripts/validation_human/08_run_deg.R",
            ROOT / "scripts/validation_human/08_finalize_deg_release.py",
            ROOT / "scripts/validation_human/08_split_deg_release.py",
            ROOT / "scripts/validation_human/seaad_common.py",
        ]
        code_payload = "\n".join(
            f"{path.relative_to(ROOT)}={sha256_file(path)}"
            for path in code_paths
        )
        self.assertEqual(
            status.loc[0, "code_bundle_sha256"],
            hashlib.sha256(code_payload.encode()).hexdigest(),
        )
        self.assertTrue(artifacts["path"].is_unique)
        expected_prefix = str(release_root.relative_to(ROOT)) + "/"
        self.assertTrue(artifacts["path"].str.startswith(expected_prefix).all())

        declared = set(artifacts["path"])
        actual = {
            str(path.relative_to(ROOT))
            for path in release_root.rglob("*")
            if path.is_file() and path.name not in {"status.tsv", "artifacts.tsv"}
        }
        self.assertEqual(declared, actual)
        for row in artifacts.itertuples(index=False):
            path = ROOT / row.path
            self.assertEqual(path.stat().st_size, int(row.bytes))
            self.assertEqual(sha256_file(path), row.digest_value)

    def test_split_release_contracts(self):
        if not FINE_ROOT.exists() or not BROAD_ROOT.exists():
            self.skipTest("Production split has not been migrated yet")
        self.assertFalse(OLD_ROOT.exists())
        self.validate_release(
            FINE_ROOT, "seaad_deg_fine_status_v1", "fine"
        )
        self.validate_release(
            BROAD_ROOT, "seaad_deg_broad_status_v1", "broad"
        )

        fine_status = read_table(
            FINE_ROOT
            / "fine_supertype_phase18_parity"
            / "fine_contrast_status.tsv"
        )
        fine_summary = read_table(FINE_ROOT / "deg_summary.tsv")
        fine_query = read_table(
            FINE_ROOT / "query_handoff/fine_query_input_index.tsv"
        )
        self.assertEqual(len(fine_status), 774)
        self.assertEqual(
            int(fine_status["terminal_status"].eq("completed").sum()), 381
        )
        self.assertEqual(len(fine_summary), 774)
        self.assertEqual(len(fine_query), 381)

        pooled = read_table(
            BROAD_ROOT / "broad_pooled_anchor/contrast_status.tsv"
        )
        stratified = read_table(
            BROAD_ROOT / "broad_stratified_support/contrast_status.tsv"
        )
        broad_summary = read_table(BROAD_ROOT / "deg_summary.tsv")
        self.assertEqual(len(pooled), 7)
        self.assertEqual(
            int(pooled["terminal_status"].eq("completed").sum()), 7
        )
        self.assertEqual(len(stratified), 42)
        self.assertEqual(
            int(stratified["terminal_status"].eq("completed").sum()), 28
        )
        self.assertEqual(len(broad_summary), 49)

        parity_path = (
            ROOT
            / "results/validation_human/08_deg_split_payload_parity.tsv"
        )
        migration_status = read_table(
            ROOT
            / "results/validation_human/08_deg_split_migration_status.tsv"
        )
        parity = read_table(parity_path)
        self.assertEqual(len(migration_status), 1)
        self.assertEqual(
            migration_status.loc[0, "validation_status"],
            "validated_complete",
        )
        self.assertEqual(len(parity), 552)
        self.assertEqual(
            int(parity["artifact_class"].eq("tested_result").sum()), 416
        )
        self.assertEqual(int(parity["artifact_class"].eq("filter").sum()), 136)
        self.assertTrue(parity["sha256_match"].astype(bool).all())
        self.assertEqual(
            migration_status.loc[0, "parity_manifest_sha256"],
            sha256_file(parity_path),
        )

        old_prefix = "results/validation_human/08_deg/"
        for table in [fine_status, fine_query, pooled, stratified]:
            for column in [
                value
                for value in table.columns
                if value.endswith("_path") or value == "result_path"
            ]:
                self.assertFalse(
                    table[column].astype(str).str.contains(old_prefix).any()
                )


if __name__ == "__main__":
    unittest.main()
