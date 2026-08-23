from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_rosmap_top_driver_gene_venn.py"
SPEC = importlib.util.spec_from_file_location("seaad_rosmap_top_driver_gene_venn", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_successful_force_replacement_removes_backup(tmp_path: Path) -> None:
    output = tmp_path / FIGURE.FIGURE_ID
    output.mkdir()
    (output / "old.txt").write_text("old", encoding="utf-8")
    staging = tmp_path / f".{FIGURE.FIGURE_ID}.staging.test"
    staging.mkdir()
    (staging / "new.txt").write_text("new", encoding="utf-8")

    FIGURE.replace_output_package(staging, output)

    assert (output / "new.txt").read_text(encoding="utf-8") == "new"
    assert not list(tmp_path.glob(f".{FIGURE.FIGURE_ID}.backup.*"))


def test_frozen_gene_regions_and_geometry() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot_data = FIGURE.build_plot_data(bundle)
    summary = FIGURE.build_region_summary(bundle)

    assert len(bundle["rosmap"]) == 47
    assert len(bundle["seaad"]) == 11
    assert bundle["rosmap"]["key_driver"].nunique() == 25
    assert bundle["seaad"]["current_symbol"].nunique() == 9
    assert bundle["regions"] == FIGURE.EXPECTED_REGIONS

    assert len(plot_data) == 28
    assert not plot_data.duplicated(["case_id", "gene"]).any()
    counts = plot_data.groupby(["case_id", "region"]).size().to_dict()
    assert counts == {
        ("mt_driver", "common"): 6,
        ("mt_driver", "rosmap_only"): 4,
        ("non_mt_driver", "rosmap_only"): 15,
        ("non_mt_driver", "seaad_only"): 3,
    }

    assert len(summary) == 6
    assert not summary.duplicated(["case_id", "region"]).any()
    summary_counts = summary.set_index(["case_id", "region"])["region_count"].astype(int).to_dict()
    assert summary_counts == {
        ("mt_driver", "rosmap_only"): 4,
        ("mt_driver", "common"): 6,
        ("mt_driver", "seaad_only"): 0,
        ("non_mt_driver", "rosmap_only"): 15,
        ("non_mt_driver", "common"): 0,
        ("non_mt_driver", "seaad_only"): 3,
    }
    mt = summary.loc[summary["case_id"].eq("mt_driver")].iloc[0]
    non_mt = summary.loc[summary["case_id"].eq("non_mt_driver")].iloc[0]
    assert float(mt["center_distance"]) + float(mt["seaad_radius"]) <= float(mt["rosmap_radius"])
    assert float(non_mt["center_distance"]) >= float(non_mt["rosmap_radius"]) + float(non_mt["seaad_radius"])
    assert float(mt["rosmap_center_x"]) == 0.0
    assert float(mt["seaad_center_x"]) == 0.25
    assert float(non_mt["rosmap_center_x"]) == -1.55
    assert float(non_mt["seaad_center_x"]) == 1.25


def test_full_atomic_figure_package(tmp_path: Path) -> None:
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
    assert int(status.loc[0, "plot_data_rows"]) == 28
    assert int(status.loc[0, "rosmap_selected_units"]) == 47
    assert int(status.loc[0, "seaad_selected_units"]) == 11
    assert int(status.loc[0, "rosmap_unique_genes"]) == 25
    assert int(status.loc[0, "seaad_unique_genes"]) == 9

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_artifacts.tsv", sep="\t", dtype=str)
    output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
    assert len(output_rows) == 8
    assert set(output_rows["path"]) == set(FIGURE.PAYLOAD_FILES)
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
    assert not any(line != line.rstrip() for line in svg.splitlines())
    assert "<text" in svg.lower()
    assert "<path" in svg.lower()
    assert "Phase 18 core MitoCarta; not mtDNA-only" in svg
    assert "SEA-AD only: 0 (∅)" in svg
    assert "Common: 0 (∅)" in svg
    assert "SEA-AD OPC KDA unavailable" in svg
    assert "SEA-AD post-hoc exploratory" in svg
    for gene in FIGURE.build_plot_data(FIGURE.load_bundle(ROOT))["gene"]:
        assert gene in svg

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
