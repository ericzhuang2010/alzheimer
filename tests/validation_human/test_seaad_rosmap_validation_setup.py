from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_rosmap_validation_setup.py"
SPEC = importlib.util.spec_from_file_location("seaad_rosmap_validation_setup", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_plot_data_preserves_setup_scope_and_holdout_boundary() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot_data = FIGURE.build_plot_data(bundle)

    assert bundle["sea_donors"] == 78
    assert bundle["supertypes"] == 129
    assert bundle["fine_contrasts"] == 774
    assert bundle["structural_directions"] == 1_548
    assert bundle["source_directions"] == 762
    assert bundle["active_calls"] == 42
    assert bundle["sea_selected"] == 11
    assert bundle["sea_symbols"] == 9
    assert bundle["minimum_donors_per_arm"] == 3
    assert bundle["query_rule"] == "FDR < 0.05"

    # The original ROSMAP scope spans nine source networks; the included and
    # selected comparison scope lies in the seven networks matched to SEA-AD.
    assert bundle["rosmap_fine_types"] == 54
    assert bundle["rosmap_source_networks"] == 9
    assert bundle["shared_networks"] == 7
    assert bundle["rosmap_structural"] == 648
    assert bundle["rosmap_included"] == 161
    assert bundle["rosmap_selected"] == 47

    assert plot_data["element_id"].is_unique
    visible = "\n".join(plot_data["display_text"].astype(str))
    assert "Original scope: 54 fine types  |  9 source networks" in visible
    assert "Matched scope: 7 SEA-AD networks" in visible
    assert "ROSMAP candidate files not read by SEA-AD selection code" in visible
    assert "COMPARE AFTER NEW SEA-AD LIST FREEZE" in visible
    assert "no fold-change cutoff" in visible
    assert "SEA-AD POST-HOC EXPLORATORY RERUN" in visible
    assert "fine labels stay separate" in visible
    assert "1,548 structural slots" in visible
    assert "42 KDA calls" in visible
    assert not plot_data["display_text"].str.contains(
        "6 strict shared|36 of 47", case=False, regex=True
    ).any()


def test_full_figure_package(tmp_path: Path) -> None:
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
    assert int(status.loc[0, "png_width"]) == FIGURE.PNG_WIDTH
    assert int(status.loc[0, "png_height"]) == FIGURE.PNG_HEIGHT
    assert not bool(status.loc[0, "comparison_outcome_shown"])

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()

    artifacts = pd.read_csv(
        output / f"{FIGURE.FIGURE_ID}_artifacts.tsv", sep="\t", dtype=str
    )
    output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
    assert len(output_rows) == 7
    assert set(output_rows["path"]) == set(FIGURE.PAYLOAD_FILES)
    assert len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1
    assert f"{FIGURE.FIGURE_ID}_artifacts.tsv" not in set(artifacts["path"])
    assert f"{FIGURE.FIGURE_ID}_status.tsv" not in set(artifacts["path"])
    for row in artifacts.itertuples(index=False):
        path = output / row.path if row.artifact_role == "output" else ROOT / row.path
        assert path.stat().st_size == int(row.bytes)
        assert digest(path) == row.sha256

    image = Image.open(output / f"{FIGURE.FIGURE_ID}.png")
    assert image.size == (FIGURE.PNG_WIDTH, FIGURE.PNG_HEIGHT)
    dpi = image.info.get("dpi")
    assert dpi and min(dpi) >= FIGURE.DEFAULT_PNG_DPI - 1

    pdf = (output / f"{FIGURE.FIGURE_ID}.pdf").read_bytes()
    assert pdf.startswith(b"%PDF")
    svg = (output / f"{FIGURE.FIGURE_ID}.svg").read_text(encoding="utf-8")
    assert "<path" in svg.lower()
    assert "SEA-AD POST-HOC EXPLORATORY RERUN" in svg
    assert "COMPARE AFTER NEW SEA-AD LIST FREEZE" in svg
    assert "no fold-change cutoff" in svg
    assert "6 strict shared" not in svg
