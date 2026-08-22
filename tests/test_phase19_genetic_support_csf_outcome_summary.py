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
SCRIPT = (
    ROOT
    / "scripts/figures/analysis/phase_19_genetic_support/"
    "plot_genetic_support_csf_outcome_summary.py"
)
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("genetic_support_csf_outcome_summary", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def source_root() -> Path:
    return ROOT / FIGURE.DEFAULT_INPUT_ROOT


def test_default_package_contract() -> None:
    assert FIGURE.STEM == "genetic_support_csf_outcome_summary"
    assert FIGURE.DEFAULT_OUTPUT_ROOT == (
        "results/figures/analysis/phase_19_genetic_support/csf_outcome_summary"
    )
    assert FIGURE.output_names(FIGURE.STEM) == [
        "genetic_support_csf_outcome_summary.png",
        "genetic_support_csf_outcome_summary.pdf",
        "genetic_support_csf_outcome_summary.svg",
        "genetic_support_csf_outcome_summary_plot_data.tsv",
        "genetic_support_csf_outcome_summary_checks.tsv",
        "genetic_support_csf_outcome_summary_caption.md",
        "genetic_support_csf_outcome_summary_methods.md",
        "genetic_support_csf_outcome_summary_artifacts.tsv",
        "genetic_support_csf_outcome_summary_status.tsv",
    ]


def test_plot_data_preserves_gene_by_trait_scope_and_interpretation() -> None:
    frames = FIGURE.validate_inputs(source_root())
    plot_data, derived = FIGURE.derive_plot_data(frames)
    checks = FIGURE.science_checks(plot_data, derived, frames)

    assert derived["total_screens"] == 57
    assert derived["unique_genes"] == 19
    assert derived["trait_count"] == 3
    assert derived["positive_decisions"] == 3
    assert derived["no_signal_decisions"] == 54
    assert derived["positive_genes"] == ["APOE"]
    assert derived["newly_supported_unique_genes"] == 0
    assert checks["status"].eq("pass").all()

    tiles = plot_data.loc[plot_data["record_type"].eq("trait_tile")]
    assert tiles["trait_id"].tolist() == FIGURE.TRAIT_ORDER
    assert tiles["total_screens"].tolist() == [19, 19, 19]
    assert tiles["apoe_positive_decisions"].tolist() == [1, 1, 1]
    assert tiles["other_gene_no_signal_decisions"].tolist() == [18, 18, 18]
    assert tiles["primary_label"].eq("APOE").all()
    aggregate = plot_data.loc[plot_data["record_type"].eq("aggregate")].iloc[0]
    assert aggregate["apoe_positive_decisions"] == 3
    assert aggregate["other_gene_no_signal_decisions"] == 54
    assert aggregate["newly_supported_unique_genes"] == 0

    forbidden = {"regional_min_p", "magma_p", "minus_log10_p", "neg_log10_p"}
    assert forbidden.isdisjoint(plot_data.columns)
    visible = derived["visible_text"].lower()
    assert "one gene, not three genes" in visible
    assert "do not establish a molecular mechanism" in visible
    assert "phase 19" not in visible
    assert "phase19" not in visible


def test_underflowed_regional_p_values_do_not_affect_plot_data() -> None:
    frames = FIGURE.validate_inputs(source_root())
    baseline, baseline_derived = FIGURE.derive_plot_data(frames)
    altered = {key: value.copy(deep=True) for key, value in frames.items()}
    altered["gates"]["regional_min_p"] = 0.0
    altered["gates"]["magma_p"] = 0.0
    observed, observed_derived = FIGURE.derive_plot_data(altered)

    pd.testing.assert_frame_equal(baseline, observed)
    assert baseline_derived == observed_derived


def test_full_figure_package(tmp_path: Path) -> None:
    output = tmp_path / "csf_outcome_summary"
    sources = [source_root() / FIGURE.REQUIRED_FILES[key] for key in ("gates", "status", "checks")]
    source_hashes = {path: digest(path) for path in sources}
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "fontcache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--input-root",
            str(source_root()),
            "--output-root",
            str(output),
            "--visual-review-status",
            "pending",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert sorted(path.name for path in output.iterdir()) == sorted(
        FIGURE.output_names(FIGURE.STEM)
    )
    assert all(path.is_file() and path.stat().st_size > 0 for path in output.iterdir())
    assert {path: digest(path) for path in sources} == source_hashes

    checks = pd.read_csv(
        output / "genetic_support_csf_outcome_summary_checks.tsv", sep="\t"
    )
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(
        output / "genetic_support_csf_outcome_summary_artifacts.tsv",
        sep="\t",
        dtype=str,
    )
    assert len(artifacts) == 7
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256

    status = pd.read_csv(
        output / "genetic_support_csf_outcome_summary_status.tsv", sep="\t"
    )
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "pending"
    assert status.loc[0, "nuclear_gene_trait_screens"] == 57
    assert status.loc[0, "apoe_positive_gate_decisions"] == 3
    assert status.loc[0, "no_qualifying_signal_decisions"] == 54
    assert status.loc[0, "newly_supported_unique_genes"] == 0
    assert bool(status.loc[0, "underflow_safe_no_pvalue_geometry"])

    with Image.open(output / "genetic_support_csf_outcome_summary.png") as image:
        assert image.size == (5580, 2115)
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= 449
    svg = (output / "genetic_support_csf_outcome_summary.svg").read_text(
        encoding="utf-8"
    ).lower()
    assert "<svg" in svg
    assert "<text" in svg
    assert "phase 19" not in svg
    assert "phase19" not in svg
    assert "-log10" not in svg
    assert "pp.h4" not in svg
    assert (output / "genetic_support_csf_outcome_summary.pdf").read_bytes()[:5] == b"%PDF-"

