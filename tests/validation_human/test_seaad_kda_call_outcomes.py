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


def test_active_posthoc_kda_outcome_and_sequence_contract() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_plot_data(bundle)
    calls = plot.loc[plot["record_type"].eq("call")]
    cells = plot.loc[plot["record_type"].eq("outcome_cell")]
    stages = plot.loc[plot["record_type"].eq("selection_stage")]

    assert len(calls) == 42
    assert calls["kda_run_id"].is_unique
    assert calls["call_status"].value_counts().to_dict() == {
        "with_significant_return": 27,
        "without_significant_return": 15,
    }
    assert calls["significant_return_rows"].astype(int).sum() == 201
    assert len(cells) == 14
    assert not cells[["broad_network", "direction"]].duplicated().any()
    observed_outcomes = {
        (row.broad_network, row.direction): (
            int(row.with_return_calls), int(row.without_return_calls)
        )
        for row in cells.itertuples(index=False)
    }
    assert observed_outcomes == {
        ("Astrocytes", "up"): (0, 1),
        ("Astrocytes", "down"): (0, 0),
        ("Excitatory_neurons", "up"): (4, 6),
        ("Excitatory_neurons", "down"): (10, 0),
        ("Inhibitory_neurons", "up"): (3, 3),
        ("Inhibitory_neurons", "down"): (8, 2),
        ("Microglia", "up"): (0, 1),
        ("Microglia", "down"): (0, 0),
        ("OPCs", "up"): (0, 0),
        ("OPCs", "down"): (0, 0),
        ("Oligodendrocytes", "up"): (1, 1),
        ("Oligodendrocytes", "down"): (1, 1),
        ("Vasculature_cells", "up"): (0, 0),
        ("Vasculature_cells", "down"): (0, 0),
    }
    observed_stages = [
        (row.stage_id, int(row.stage_value), row.stage_label)
        for row in stages.sort_values("display_order").itertuples(index=False)
    ]
    assert observed_stages == [
        ("completed_calls", 42, "completed KDA calls"),
        ("calls_with_return", 27, "calls with ≥1 significant return"),
        ("significant_rows", 201, "significant return rows"),
        ("aggregate_candidates", 38_788, "aggregate candidate units"),
        ("passing_units", 11, "units passed all gates"),
    ]
    assert bundle["analysis_role"] == "posthoc_exploratory"
    assert bundle["query_rule_id"] == "fdr_only_query_sensitivity"
    assert bundle["active_query_rule"] == "FDR < 0.05"
    assert bundle["donor_minimum"] == 3
    assert bundle["minimum_coverage"] == 0.80
    assert bundle["aggregate_q_threshold"] == 0.05
    assert bundle["group_calls"] == {"M_e33": 40, "F_e4": 1, "F_e33": 1}
    assert bundle["candidate_units"] == 38_788
    assert bundle["passing_units"] == 11
    assert bundle["selected_units"] == 11
    assert bundle["selected_unique_genes"] == 9
    assert len(plot) == 67
    assert plot["record_id"].is_unique
    assert set(plot["analysis_role"]) == {"posthoc_exploratory"}
    assert set(plot["query_rule_id"]) == {"fdr_only_query_sensitivity"}
    assert set(plot["minimum_coverage"].astype(float)) == {0.80}
    assert set(plot["aggregate_q_threshold"].astype(float)) == {0.05}
    assert not plot["rosmap_candidate_files_read"].astype(bool).any()


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
    assert float(status.loc[0, "minimum_coverage"]) == 0.80
    assert float(status.loc[0, "aggregate_q_threshold"]) == 0.05
    assert int(status.loc[0, "completed_calls"]) == 42
    assert int(status.loc[0, "calls_with_returns"]) == 27
    assert int(status.loc[0, "calls_without_returns"]) == 15
    assert int(status.loc[0, "significant_return_rows"]) == 201
    assert int(status.loc[0, "candidate_units"]) == 38_788
    assert int(status.loc[0, "passing_units"]) == 11
    assert int(status.loc[0, "selected_units"]) == 11
    assert int(status.loc[0, "selected_unique_genes"]) == 9

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
    assert "KDA call outcomes" in svg
    assert "Dementia-up" in svg
    assert "Dementia-down" in svg
    assert "38,788" in svg
    assert "POST-HOC EXPLORATORY" in svg
    assert "coverage ≥0.80" in svg
    assert "network BH q≤0.05" in svg

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
