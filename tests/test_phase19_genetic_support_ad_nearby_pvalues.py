from __future__ import annotations

import hashlib
import importlib.util
import math
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/figures/analysis/phase_19_genetic_support"
    / "plot_genetic_support_ad_nearby_pvalues.py"
)
SPEC = importlib.util.spec_from_file_location("genetic_support_ad_nearby_pvalues", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_default_output_is_a_separate_subdirectory() -> None:
    assert FIGURE.DEFAULT_OUTPUT_ROOT == (
        "results/figures/analysis/phase_19_genetic_support/ad_nearby_pvalues"
    )
    assert FIGURE.OUTPUT_FILES == [
        "genetic_support_ad_nearby_pvalues.png",
        "genetic_support_ad_nearby_pvalues.pdf",
        "genetic_support_ad_nearby_pvalues.svg",
        "genetic_support_ad_nearby_pvalues_plot_data.tsv",
        "genetic_support_ad_nearby_pvalues_checks.tsv",
        "genetic_support_ad_nearby_pvalues_caption.md",
        "genetic_support_ad_nearby_pvalues_methods.md",
        "genetic_support_ad_nearby_pvalues_artifacts.tsv",
        "genetic_support_ad_nearby_pvalues_status.tsv",
    ]


def test_plot_data_shows_all_exact_source_p_values_once() -> None:
    source = ROOT / FIGURE.DEFAULT_INPUT_ROOT
    frames = FIGURE.validate_inputs(source)
    plot_data, derived = FIGURE.derive_plot_data(frames)

    assert len(plot_data) == 19
    assert plot_data["gene"].nunique() == 19
    assert derived["below_cutoff_count"] == 4
    assert derived["at_or_above_cutoff_count"] == 15
    assert set(derived["below_cutoff_genes"]) == FIGURE.EXPECTED_BELOW_CUTOFF_GENES
    assert plot_data.set_index("gene")["regional_min_p_source"].to_dict() == FIGURE.EXPECTED_RAW_P
    assert plot_data["source_accession"].eq("GCST90027158").all()

    apoe = plot_data.set_index("gene").loc["APOE"]
    assert apoe["regional_min_p_source"] == "0"
    assert "underflow" in apoe["regional_min_p_display"]
    assert pd.isna(apoe["minus_log10_p"])
    assert apoe["minus_log10_display"] == "beyond range*"

    rps15 = plot_data.set_index("gene").loc["RPS15"]
    assert math.isclose(float(rps15["minus_log10_p"]), -math.log10(4.089e-30))
    assert rps15["regional_min_p_display"] == "4.089 × 10⁻³⁰"
    at_or_above = plot_data.loc[~plot_data["below_cutoff"]]
    assert at_or_above["minus_log10_p"].notna().all()
    assert (pd.to_numeric(at_or_above["minus_log10_p"]) < FIGURE.CUTOFF_MINUS_LOG10).all()
    assert set(plot_data["cutoff_class"]) == {
        "Below conservative cutoff",
        "At or above conservative cutoff",
    }


def test_threshold_explanation_and_interpretation_boundary_are_plain_language() -> None:
    visible = "\n".join([FIGURE.CAPTION, FIGURE.METHODS])
    plain = " ".join(visible.split())
    assert "0.05 / 1,000,000" in plain
    assert "does not by itself identify that gene as causal" in plain
    assert "P value is not literally zero" in plain
    assert "conservative screening cutoff" in plain
    assert "priorities for validation" in plain
    assert "gene-activity and shared-variant validation" in plain
    assert "one evidence layer for prioritizing validation" in plain
    assert "Filled blue diamonds" in plain
    assert "open gray circles and dotted lines" in plain
    assert "did not pass" not in plain.lower()
    assert "non-passing" not in plain.lower()
    assert "lack of evidence" not in plain.lower()


def test_science_checks_pass() -> None:
    source = ROOT / FIGURE.DEFAULT_INPUT_ROOT
    frames = FIGURE.validate_inputs(source)
    _, derived = FIGURE.derive_plot_data(frames)
    checks = FIGURE.build_science_checks(derived)
    assert checks["status"].eq("pass").all()
    assert set(checks["check_id"]) >= {
        "unique_gene_count",
        "below_cutoff_count",
        "at_or_above_cutoff_count",
        "underflow_gene",
        "exact_p_fingerprint",
    }


def test_full_figure_package(tmp_path: Path) -> None:
    output = tmp_path / "figure"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--input-root",
            str(ROOT / FIGURE.DEFAULT_INPUT_ROOT),
            "--output-root",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE.OUTPUT_FILES)
    status = pd.read_csv(output / "genetic_support_ad_nearby_pvalues_status.tsv", sep="\t")
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "pending"
    assert int(status.loc[0, "unique_gene_count"]) == 19
    assert int(status.loc[0, "below_cutoff_count"]) == 4
    assert int(status.loc[0, "at_or_above_cutoff_count"]) == 15
    assert not bool(status.loc[0, "cutoff_class_is_total_evidence_conclusion"])
    assert bool(status.loc[0, "apoe_numeric_underflow"])
    assert not bool(status.loc[0, "nearby_signal_assigns_gene"])
    assert not bool(status.loc[0, "visible_internal_phase_label"])

    plot_data = pd.read_csv(
        output / "genetic_support_ad_nearby_pvalues_plot_data.tsv",
        sep="\t",
        dtype={"regional_min_p_source": "string"},
    )
    assert len(plot_data) == 19
    assert int((plot_data["display_group"] == "fifteen_values_at_or_above_cutoff").sum()) == 15
    checks = pd.read_csv(output / "genetic_support_ad_nearby_pvalues_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()

    artifacts = pd.read_csv(
        output / "genetic_support_ad_nearby_pvalues_artifacts.tsv",
        sep="\t",
        dtype=str,
    )
    assert len(artifacts) == len(FIGURE.OUTPUT_FILES) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256

    with Image.open(output / "genetic_support_ad_nearby_pvalues.png") as image:
        assert image.size == (5580, 2115)
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= 449
    svg = (output / "genetic_support_ad_nearby_pvalues.svg").read_text(encoding="utf-8").lower()
    assert "phase 19" not in svg
    assert "phase19" not in svg
    assert "all 19 exact values" in svg
    assert "15 additional regions" in svg
    assert "four priority regions below cutoff" in svg
    assert "how the results guide validation" in svg
    assert "priorities for matched" in svg
    assert "gene-activity and shared-variant analyses" in svg
    assert "why a conservative cutoff?" in svg
    assert "a screening cutoff is not a verdict" not in svg
    assert "did not pass" not in svg
    assert "non-passing" not in svg
