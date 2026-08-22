from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/figures/analysis/phase_19_genetic_support"
SCRIPT = SCRIPT_DIR / "plot_genetic_support_non_apoe_evidence_cards.py"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("phase19_non_apoe_evidence_cards", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def source_roots() -> tuple[Path, Path, Path, Path]:
    base = ROOT / "results/minerva_production"
    return (
        base / "19_genetic_support_tier1",
        base / "19_genetic_support_tier2_recovery",
        base / "19_genetic_support_opc_rps15_public_recovery",
        base / "19_genetic_support_endophenotype_gwas_qtl_extension",
    )


def test_plot_data_preserves_candidate_evidence_boundaries() -> None:
    frames, _ = FIGURE.load_sources(*source_roots())
    plot_data, derived = FIGURE.derive_plot_data(frames)
    assert list(plot_data.sort_values("display_order")["gene"]) == FIGURE.CARD_ORDER
    assert dict(zip(plot_data["gene"], plot_data["tier1_grade"])) == {
        "COX7C": "weak",
        "SELENOW": "weak",
        "RPS15": "none_found",
        "ANKRD11": "none_found",
    }
    assert set(plot_data.loc[plot_data["regional_signal"], "gene"]) == {
        "COX7C",
        "RPS15",
        "ANKRD11",
    }
    assert plot_data["csf_traits_passed"].sum() == 0
    assert derived["rps15_totals"] == {
        "eligible": 37,
        "measured": 31,
        "positive_rows": 6,
        "resolved": 0,
    }
    assert derived["rps15_unique_tracks"] == 3
    assert "PP.H4 unavailable" in derived["visible_text"]
    assert "PP.H4 = 0" not in derived["visible_text"]
    assert "causal" not in derived["visible_text"].lower()


def test_full_figure_package(tmp_path: Path) -> None:
    tier1, recovery, rps15, endophenotype = source_roots()
    output = tmp_path / "non_apoe_evidence"
    environment = os.environ.copy()
    environment["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--tier1-root",
            str(tier1),
            "--recovery-root",
            str(recovery),
            "--rps15-root",
            str(rps15),
            "--endophenotype-root",
            str(endophenotype),
            "--output-root",
            str(output),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    expected = FIGURE.output_names(FIGURE.STEM)
    assert sorted(path.name for path in output.iterdir()) == sorted(expected)
    status = pd.read_csv(output / f"{FIGURE.STEM}_status.tsv", sep="\t")
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "pending"
    checks = pd.read_csv(output / f"{FIGURE.STEM}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(
        output / f"{FIGURE.STEM}_artifacts.tsv",
        sep="\t",
        dtype=str,
    )
    assert len(artifacts) == len(expected) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256
    with Image.open(output / f"{FIGURE.STEM}.png") as image:
        assert image.size == (5580, 2115)
        assert min(image.info["dpi"]) >= 449
    svg = (output / f"{FIGURE.STEM}.svg").read_text(encoding="utf-8")
    assert "<text" in svg
    assert "PP.H4 = 0" not in svg

