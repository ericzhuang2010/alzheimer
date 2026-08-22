from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_fine_deg_landscape.py"
SPEC = importlib.util.spec_from_file_location("seaad_fine_deg_landscape", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_frozen_deg_landscape_contract() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_plot_data(bundle)
    cells = plot.loc[plot["record_type"].eq("heatmap_cell")]
    signed = plot.loc[plot["record_type"].eq("signed_group_total")]

    assert len(cells) == 774
    assert cells["supertype_id"].nunique() == 129
    assert cells["signature_group"].nunique() == 6
    assert not cells[["supertype_id", "signature_group"]].duplicated().any()
    assert cells["terminal_status"].value_counts().to_dict() == {
        "not_estimable": 514,
        "completed": 260,
    }
    assert bundle["total_fdr"] == 24_404
    assert bundle["total_parity"] == 22_192
    assert bundle["signal_contrasts"] == 74
    assert bundle["m_e33_parity"] == 21_795
    observed = {
        (row.signature_group, row.deg_direction): int(row.raw_count)
        for row in signed.itertuples(index=False)
    }
    assert observed == FIGURE.EXPECTED_SIGNED_TOTALS
    assert len(plot) == 785
    assert plot["record_id"].is_unique


def test_full_atomic_deg_landscape_package(tmp_path: Path) -> None:
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
    assert int(status.loc[0, "fine_contrasts"]) == 774
    assert int(status.loc[0, "completed_contrasts"]) == 260
    assert int(status.loc[0, "parity_hits"]) == 22_192

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
    assert "Fine-supertype DEG landscape" in svg
    assert "Dementia-down" in svg
    assert "98.2%" in svg

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
