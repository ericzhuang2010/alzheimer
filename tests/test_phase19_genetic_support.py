from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "19_run_genetic_support.py"
SPEC = importlib.util.spec_from_file_location("phase19_genetic_support", SCRIPT)
assert SPEC and SPEC.loader
PHASE19 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PHASE19)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_phase18_scope_is_frozen_to_all_25_genes_and_47_contexts() -> None:
    candidates = PHASE19.build_candidates(
        ROOT / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
    )
    assert len(candidates) == 47
    assert candidates["gene"].nunique() == 25
    assert candidates[["gene", "broad_network", "case_id"]].duplicated().sum() == 0
    assert set(PHASE19.MT_GENES).issubset(set(candidates["gene"]))


def test_grading_does_not_promote_filtered_absence_or_mtDNA_unassessability() -> None:
    assert PHASE19.candidate_grade("APOE")[0] == "strong"
    assert PHASE19.candidate_grade("COX7C")[0] == "weak"
    assert PHASE19.candidate_grade("SELENOW")[0] == "weak"
    assert PHASE19.candidate_grade("RPL11")[0] == "none_found"
    assert "not evidence" in PHASE19.candidate_grade("RPL11")[1]
    assert PHASE19.candidate_grade("MT-CO2")[0] == "not_assessable"


def test_published_tier1_bundle_contract_and_scientific_guards(tmp_path: Path) -> None:
    output = tmp_path / "tier1"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--config", str(ROOT / "config/phase19_genetic_support.yml"),
            "--execution-config", str(ROOT / "config/phase19_local_production_execution.yml"),
            "--task-mode", "genetic_support",
            "--output-root", str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    assert sorted(path.name for path in output.iterdir()) == sorted(PHASE19.OUTPUT_FILES)
    summary = pd.read_csv(output / "genetic_support_evidence_summary.tsv", sep="\t")
    assert len(summary) == 47
    assert summary["gene"].nunique() == 25
    assert summary["candidate_id"].is_unique
    assert set(summary["final_grade"]).issubset(PHASE19.GRADE_ORDER)
    coloc = pd.read_csv(output / "genetic_support_colocalization.tsv.gz", sep="\t")
    assert not coloc["classical_h0_h4_available"].astype(bool).any()
    assert coloc[["h0", "h1", "h2", "h3", "h4"]].isna().all().all()
    assessability = pd.read_csv(output / "genetic_support_assessability.tsv", sep="\t")
    assert len(assessability) == 47 * 4
    status = pd.read_csv(output / "genetic_support_status.tsv", sep="\t")
    assert status.loc[0, "technical_status"] == "validated_complete_tier1"
    assert not bool(status.loc[0, "full_phase19_complete"])
    artifacts = pd.read_csv(output / "genetic_support_artifacts.tsv", sep="\t", dtype=str)
    assert len(artifacts) == len(PHASE19.OUTPUT_FILES) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256
