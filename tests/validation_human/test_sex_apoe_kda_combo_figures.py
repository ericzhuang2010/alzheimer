from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/presentations/update_sex_apoe_kda_combo_slides.py"


def test_current_combo_figure_package(tmp_path: Path) -> None:
    output = tmp_path / "combo_figures"
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "font-cache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--figures-only",
            "--audit-root",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    status = pd.read_csv(output / "combo_figure_status.tsv", sep="\t").iloc[0]
    assert status["execution_status"] == "complete"
    assert (
        status["rosmap_non_mt_category_units"],
        status["rosmap_non_mt_genes"],
        status["rosmap_top5_entries"],
    ) == (381, 228, 123)
    assert (
        status["seaad_non_mt_category_units"],
        status["seaad_non_mt_genes"],
        status["seaad_top5_entries"],
    ) == (44, 43, 17)
    assert (status["figure_roles"], status["artifact_files"]) == (9, 36)

    artifacts = pd.read_csv(output / "combo_figure_artifacts.tsv", sep="\t")
    assert len(artifacts) == 36
    assert artifacts["path"].nunique() == 36
    assert all((ROOT / path).is_file() for path in artifacts["path"])
