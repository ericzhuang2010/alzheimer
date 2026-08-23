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


def test_active_fdr_only_deg_landscape_contract() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_plot_data(bundle)
    cells = plot.loc[plot["record_type"].eq("heatmap_cell")]
    signed = plot.loc[plot["record_type"].eq("signed_group_total")]

    assert len(cells) == 774
    assert cells["supertype_id"].nunique() == 129
    assert cells["signature_group"].nunique() == 6
    assert not cells[["supertype_id", "signature_group"]].duplicated().any()
    assert cells["terminal_status"].value_counts().to_dict() == {
        "not_estimable": 393,
        "completed": 381,
    }
    assert bundle["analysis_role"] == "posthoc_exploratory"
    assert bundle["query_rule_id"] == "fdr_only_query_sensitivity"
    assert bundle["active_query_rule"] == "FDR < 0.05"
    assert bundle["donor_minimum"] == 3
    assert bundle["total_active"] == 24_423
    assert bundle["total_reference"] == 22_211
    assert bundle["signal_contrasts"] == 85
    assert bundle["dominant_group"] == "M_e33"
    assert bundle["dominant_group_hits"] == 24_005
    assert bundle["plotted_groups"] == ["F_e33", "F_e4", "M_e33", "M_e4"]
    observed = {
        (row.signature_group, row.deg_direction): int(row.raw_count)
        for row in signed.itertuples(index=False)
    }
    assert observed == {
        ("F_e33", "Dementia_down"): 8,
        ("F_e33", "Dementia_up"): 258,
        ("F_e4", "Dementia_down"): 34,
        ("F_e4", "Dementia_up"): 112,
        ("M_e33", "Dementia_down"): 14_472,
        ("M_e33", "Dementia_up"): 9_533,
        ("M_e4", "Dementia_down"): 0,
        ("M_e4", "Dementia_up"): 6,
    }
    assert len(plot) == 787
    assert plot["record_id"].is_unique
    assert set(plot["analysis_role"]) == {"posthoc_exploratory"}
    assert set(plot["query_rule_id"]) == {"fdr_only_query_sensitivity"}
    assert set(plot["donor_minimum_per_arm"].astype(int)) == {3}


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
            "pending",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE.OUTPUT_FILES)
    status = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_status.tsv", sep="\t")
    assert status.loc[0, "validation_status"] == "awaiting_visual_review"
    assert status.loc[0, "visual_review_status"] == "pending"
    assert int(status.loc[0, "failed_blocking_checks"]) == 0
    assert int(status.loc[0, "pending_nonblocking_checks"]) == 1
    assert status.loc[0, "analysis_role"] == "posthoc_exploratory"
    assert status.loc[0, "query_rule_id"] == "fdr_only_query_sensitivity"
    assert int(status.loc[0, "donor_minimum_per_arm"]) == 3
    assert int(status.loc[0, "fine_contrasts"]) == 774
    assert int(status.loc[0, "completed_contrasts"]) == 381
    assert int(status.loc[0, "not_estimable_contrasts"]) == 393
    assert int(status.loc[0, "active_fdr_only_hits"]) == 24_423
    assert int(status.loc[0, "phase18_reference_hits"]) == 22_211
    assert int(status.loc[0, "active_signal_contrasts"]) == 85
    assert status.loc[0, "plotted_groups"] == "F_e33|F_e4|M_e33|M_e4"

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    assert not (
        checks["severity"].eq("blocking") & ~checks["status"].eq("pass")
    ).any()
    assert checks.set_index("check_id").loc["visual_review", "status"] == "pending"
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
    assert "M_e4" in svg
    assert "POST-HOC EXPLORATORY" in svg
    assert "FDR-only active" in svg
    assert "98.3%" in svg

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
