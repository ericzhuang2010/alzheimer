from __future__ import annotations

import hashlib
import importlib.util
import math
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_rosmap_non_mt_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("seaad_rosmap_non_mt_diagnostic", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_frozen_non_mt_fate_and_context() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_plot_data(bundle)
    fate = FIGURE.build_fate_summary(plot)
    context = FIGURE.build_coverage_context(bundle, plot)

    assert len(plot) == 21
    assert not plot.duplicated(["broad_network", "gene"]).any()
    assessable = plot["seaad_assessability"].eq("assessable")
    assert int(assessable.sum()) == 17
    assert int((~assessable).sum()) == 4
    assert set(
        zip(
            plot.loc[~assessable, "broad_network"],
            plot.loc[~assessable, "gene"],
        )
    ) == FIGURE.EXPECTED_NOT_TESTABLE
    assert int((assessable & plot["seaad_qualifying_return_count"].eq(0)).sum()) == 13
    assert int((assessable & plot["seaad_qualifying_return_count"].eq(1)).sum()) == 4
    assert set(
        zip(
            plot.loc[plot["seaad_qualifying_return_count"].eq(1), "broad_network"],
            plot.loc[plot["seaad_qualifying_return_count"].eq(1), "gene"],
        )
    ) == FIGURE.EXPECTED_ONE_RETURN
    assert not plot["seaad_final_driver_candidate"].map(FIGURE.truth).any()
    assert int(plot["rosmap_has_unavailable_stratum_support"].sum()) == 20

    assert fate["unit_count"].astype(int).tolist() == [21, 4, 17, 13, 4, 0]
    row = context.iloc[0]
    assert (
        int(row["rosmap_included_runs"]),
        int(row["seaad_kda_calls"]),
        int(row["seaad_m_e33_calls"]),
    ) == (161, 42, 40)
    assert (
        int(row["rosmap_effective_query_floor"]),
        int(row["seaad_effective_query_floor"]),
    ) == (10, 3)
    assert set(row["seaad_donor_limited_groups"].split("|")) == FIGURE.UNAVAILABLE_GROUPS
    assert int(row["units_with_rosmap_support_in_donor_limited_group"]) == 20


def test_frozen_reverse_lookup() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    reverse = FIGURE.build_reverse_lookup(bundle)

    assert reverse["gene"].tolist() == [gene for _, gene in FIGURE.REVERSE_ORDER]
    assert reverse.set_index("gene")["rosmap_conservative_support_count"].astype(int).to_dict() == {
        "HGSNAT": 1,
        "BEX3": 4,
        "RPS27A": 2,
        "RPL30": 0,
        "KANSL1L": 0,
    }
    expected_q = {
        "HGSNAT": 0.6413643985648223,
        "BEX3": 0.1574575602307228,
        "RPS27A": 1.0,
        "RPL30": 1.0,
        "KANSL1L": 1.0,
    }
    observed_q = reverse.set_index("gene")["rosmap_aggregate_q"].astype(float).to_dict()
    assert all(math.isclose(observed_q[gene], value) for gene, value in expected_q.items())
    assert int(
        reverse.loc[
            reverse["gene"].eq("RPL30"), "excluded_size3_primary_return_count"
        ].iloc[0]
    ) == 2
    assert reverse.loc[reverse["gene"].eq("KANSL1L"), "outcome_id"].iloc[0] == "no_explicit_primary_return"
    assert not reverse["rosmap_terminal_candidate_status"].eq("driver_candidate").any()


def test_full_atomic_package(tmp_path: Path) -> None:
    output = tmp_path / FIGURE.FIGURE_ID
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "font-cache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--project-root",
            str(ROOT),
            "--output-root",
            str(output),
            "--visual-review-status",
            "complete",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE.OUTPUT_FILES)
    status = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_status.tsv", sep="\t")
    assert status.loc[0, "validation_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "complete"
    assert int(status.loc[0, "failed_blocking_checks"]) == 0
    assert int(status.loc[0, "pending_nonblocking_checks"]) == 0
    assert int(status.loc[0, "input_files"]) == len(FIGURE.INPUT_PATHS)
    assert int(status.loc[0, "output_files"]) == len(FIGURE.OUTPUT_FILES)
    assert int(status.loc[0, "plot_data_rows"]) == 21
    assert int(status.loc[0, "reverse_lookup_rows"]) == 5
    assert float(status.loc[0, "figure_width_inches"]) == 12.0
    assert float(status.loc[0, "figure_height_inches"]) == 5.3

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    assert float(
        checks.loc[checks["check_id"].eq("minimum_font_size"), "observed"].iloc[0]
    ) >= 16.0
    geometry_checks = {
        "box_owned_text_containment",
        "box_owned_text_nonoverlap",
        "panel_title_separation",
        "table_column_separation",
        "panel_a_box_boundary_separation",
        "panel_a_box_boundaries_visible",
        "panel_b_row_boundaries_visible",
        "ribbon_block_separation",
        "internal_layout_geometry",
    }
    assert geometry_checks.issubset(set(checks["check_id"]))
    assert {"manual_color_review", "manual_grayscale_review"}.issubset(
        set(checks["check_id"])
    )

    artifacts = pd.read_csv(
        output / f"{FIGURE.FIGURE_ID}_artifacts.tsv", sep="\t", dtype=str
    )
    assert set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"]) == set(
        FIGURE.PAYLOAD_FILES
    )
    assert len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1
    assert not artifacts["path"].isin(FIGURE.OUTPUT_FILES[-2:]).any()
    for row in artifacts.itertuples(index=False):
        path = output / row.path if row.artifact_role == "output" else ROOT / row.path
        assert path.stat().st_size == int(row.bytes)
        assert digest(path) == row.sha256

    image = Image.open(output / f"{FIGURE.FIGURE_ID}.png")
    assert image.size == (FIGURE.PNG_WIDTH, FIGURE.PNG_HEIGHT)
    dpi = image.info.get("dpi")
    assert dpi and min(dpi) >= FIGURE.DEFAULT_PNG_DPI - 1
    assert (output / f"{FIGURE.FIGURE_ID}.pdf").read_bytes().startswith(b"%PDF")
    svg = (output / f"{FIGURE.FIGURE_ID}.svg").read_text(encoding="utf-8")
    assert "<text" in svg.lower()
    assert "<path" in svg.lower()
    assert all(
        gene in svg
        for gene in [
            "DYNLT1",
            "RPS15",
            "RPLP1",
            "RPL38",
            "ANKRD11",
            "FTL",
            "NCOA1",
            "HGSNAT",
            "BEX3",
            "RPS27A",
            "RPL30",
            "KANSL1L",
        ]
    )
    assert "q=.641" in svg
    assert "q=.157" in svg
    assert "≥1 arm had &lt;5 donors" in svg
    assert "Support need not be exclusive; not a sole cause" in svg

    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--project-root",
            str(ROOT),
            "--validate-output",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
