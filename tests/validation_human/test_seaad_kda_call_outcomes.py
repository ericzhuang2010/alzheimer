from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_kda_call_outcomes.py"
SPEC = importlib.util.spec_from_file_location("seaad_kda_call_outcomes", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_frozen_kda_outcome_and_sequence_contract() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_plot_data(bundle)
    calls = plot.loc[plot["record_type"].eq("call")]
    cells = plot.loc[plot["record_type"].eq("outcome_cell")]
    stages = plot.loc[plot["record_type"].eq("selection_stage")]

    assert len(calls) == 42
    assert calls["kda_run_id"].is_unique
    assert calls["call_status"].value_counts().to_dict() == {
        "with_significant_return": 29,
        "without_significant_return": 13,
    }
    assert calls["significant_return_rows"].astype(int).sum() == 208
    assert len(cells) == 14
    assert not cells[["broad_network", "direction"]].duplicated().any()
    observed_outcomes = {
        (row.broad_network, row.direction): (
            int(row.with_return_calls), int(row.without_return_calls)
        )
        for row in cells.itertuples(index=False)
    }
    assert observed_outcomes == FIGURE.EXPECTED_OUTCOMES
    observed_stages = [
        (row.stage_id, int(row.stage_value), row.stage_label)
        for row in stages.sort_values("display_order").itertuples(index=False)
    ]
    assert observed_stages == FIGURE.SELECTION_STAGES
    assert bundle["candidate_units"] == 38_788
    assert bundle["selected_units"] == 13
    assert len(plot) == 67
    assert plot["record_id"].is_unique


def test_full_atomic_kda_outcomes_package(tmp_path: Path) -> None:
    output = tmp_path / "figure"
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
    assert int(status.loc[0, "completed_calls"]) == 42
    assert int(status.loc[0, "calls_with_returns"]) == 29
    assert int(status.loc[0, "significant_return_rows"]) == 208
    assert int(status.loc[0, "candidate_units"]) == 38_788
    assert int(status.loc[0, "selected_units"]) == 13

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(
        output / f"{FIGURE.FIGURE_ID}_artifacts.tsv", sep="\t", dtype=str
    )
    assert set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"]) == set(
        FIGURE.PAYLOAD_FILES
    )
    assert len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 2
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
    assert "KDA call outcomes" in svg
    assert "Dementia-up" in svg
    assert "Dementia-down" in svg
    assert "38,788" in svg
    assert "coverage ≥0.80" in svg

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
