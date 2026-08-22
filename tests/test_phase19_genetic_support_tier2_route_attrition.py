from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/figures/analysis/phase_19_genetic_support"
    / "plot_genetic_support_tier2_route_attrition.py"
)
SPEC = importlib.util.spec_from_file_location(
    "genetic_support_tier2_route_attrition", SCRIPT
)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_default_output_contract() -> None:
    assert FIGURE.STEM == "genetic_support_tier2_route_attrition"
    assert FIGURE.DEFAULT_OUTPUT_ROOT == (
        "results/figures/analysis/phase_19_genetic_support/tier2_route_attrition"
    )
    assert FIGURE.OUTPUT_FILES == FIGURE.output_names(FIGURE.STEM)
    assert len(FIGURE.OUTPUT_FILES) == 9


def test_derivation_preserves_terminal_partition_and_posterior_boundary() -> None:
    source = (
        ROOT
        / "results/minerva_production/19_genetic_support_tier2_recovery"
    )
    frames = FIGURE.validate_inputs(source)
    plot_data, derived = FIGURE.derive_plot_data(frames)

    assert derived["route_count"] == 54
    assert derived["candidate_context_count"] == 27
    assert derived["unique_gene_count"] == 19
    assert derived["eqtl_route_count"] == 27
    assert derived["sqtl_route_count"] == 27
    assert derived["terminal_counts"] == FIGURE.EXPECTED_TERMINAL_COUNTS
    assert sum(derived["terminal_counts"].values()) == 54
    assert derived["valid_primary_h0_h4_results"] == 0
    assert derived["posterior_rows"] == 0
    assert derived["pp_h4_state"] == "unavailable"

    outcomes = plot_data.loc[plot_data["record_type"].eq("terminal_outcome")]
    assert list(outcomes.sort_values("display_order")["terminal_state"]) == (
        FIGURE.TERMINAL_ORDER
    )
    assert dict(zip(outcomes["terminal_state"], outcomes["route_count"])) == (
        FIGURE.EXPECTED_TERMINAL_COUNTS
    )
    boundary = plot_data.loc[plot_data["record_type"].eq("posterior_boundary")]
    assert len(boundary) == 1
    assert int(boundary.iloc[0]["route_count"]) == 0
    assert "unavailable" in str(boundary.iloc[0]["detail"]).lower()

    checks = FIGURE.build_science_checks(derived)
    assert checks["status"].eq("pass").all()
    assert "terminal_partition_total" in set(checks["check_id"])
    assert "valid_primary_h0_h4_results" in set(checks["check_id"])


def test_full_figure_package_in_temporary_directory(tmp_path: Path) -> None:
    output = tmp_path / "figure"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "fontcache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--input-root",
            str(
                ROOT
                / "results/minerva_production/19_genetic_support_tier2_recovery"
            ),
            "--output-root",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert sorted(path.name for path in output.iterdir()) == sorted(
        FIGURE.OUTPUT_FILES
    )
    status = pd.read_csv(
        output / f"{FIGURE.STEM}_status.tsv", sep="\t", low_memory=False
    )
    assert len(status) == 1
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "pending"
    assert int(status.loc[0, "route_count"]) == 54
    assert int(status.loc[0, "valid_primary_h0_h4_results"]) == 0
    assert status.loc[0, "pp_h4_state"] == "unavailable"

    checks = pd.read_csv(
        output / f"{FIGURE.STEM}_checks.tsv", sep="\t", low_memory=False
    )
    assert checks["status"].eq("pass").all()
    assert {
        "terminal_count__no_regional_gwas_signal",
        "terminal_count__no_regional_qtl_signal",
        "terminal_count__model_or_ld_incompatible",
        "terminal_count__not_assessable",
        "valid_primary_h0_h4_results",
        "qc_posterior_rows",
        "png_dimensions",
        "svg_editable_text",
    }.issubset(set(checks["check_id"]))

    plot_data = pd.read_csv(
        output / f"{FIGURE.STEM}_plot_data.tsv", sep="\t", low_memory=False
    )
    outcomes = plot_data.loc[plot_data["record_type"].eq("terminal_outcome")]
    assert dict(zip(outcomes["terminal_state"], outcomes["route_count"])) == (
        FIGURE.EXPECTED_TERMINAL_COUNTS
    )

    artifacts = pd.read_csv(
        output / f"{FIGURE.STEM}_artifacts.tsv", sep="\t", dtype=str
    )
    assert len(artifacts) == len(FIGURE.OUTPUT_FILES) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256

    with Image.open(output / f"{FIGURE.STEM}.png") as image:
        assert image.size == (5580, 2115)
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= 449
    svg = (output / f"{FIGURE.STEM}.svg").read_text(encoding="utf-8")
    assert "PP.H4 unavailable" in svg
    caption = (output / f"{FIGURE.STEM}_caption.md").read_text(encoding="utf-8")
    assert "not equal to zero" in caption
