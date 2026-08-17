from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/figures/analysis/phase_19_genetic_support/plot_genetic_support_slide_summary.py"
SPEC = importlib.util.spec_from_file_location("genetic_support_slide_summary", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_plot_data_preserves_scope_and_interpretive_categories() -> None:
    source = ROOT / "results/minerva_production/19_genetic_support"
    frames = FIGURE.validate_inputs(source)
    plot_data, derived = FIGURE.derive_plot_data(frames)
    assert derived["total_contexts"] == 47
    assert derived["unique_genes"] == 25
    assert derived["grade_counts"] == FIGURE.EXPECTED_GRADE_COUNTS
    cards = plot_data.loc[plot_data["record_type"].eq("candidate_card")]
    assert set(cards["gene"]) == {"APOE", "COX7C", "SELENOW"}
    displayed = set(plot_data.loc[plot_data["gene"].ne("NA"), "gene"])
    assert len(displayed) == 25
    assert set(derived["no_direct_genes"]) == FIGURE.EXPECTED_NO_DIRECT
    assert set(derived["not_assessable_genes"]) == FIGURE.EXPECTED_MTDNA
    assert "phase 19" not in derived["visible_text"].lower()
    assert "phase19" not in derived["visible_text"].lower()


def test_full_figure_package(tmp_path: Path) -> None:
    output = tmp_path / "figure"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"), str(SCRIPT),
            "--input-root", str(ROOT / "results/minerva_production/19_genetic_support"),
            "--output-root", str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE.OUTPUT_FILES)
    status = pd.read_csv(output / "genetic_support_slide_summary_status.tsv", sep="\t")
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert not bool(status.loc[0, "visible_internal_phase_label"])
    checks = pd.read_csv(output / "genetic_support_slide_summary_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(output / "genetic_support_slide_summary_artifacts.tsv", sep="\t", dtype=str)
    assert len(artifacts) == len(FIGURE.OUTPUT_FILES) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256
    image = Image.open(output / "genetic_support_slide_summary.png")
    assert image.size == (int(FIGURE.FIGURE_SIZE[0] * FIGURE.PNG_DPI), int(FIGURE.FIGURE_SIZE[1] * FIGURE.PNG_DPI))
    dpi = image.info.get("dpi")
    assert dpi and min(dpi) >= 449
    svg = (output / "genetic_support_slide_summary.svg").read_text(encoding="utf-8").lower()
    assert "phase 19" not in svg
    assert "phase19" not in svg
