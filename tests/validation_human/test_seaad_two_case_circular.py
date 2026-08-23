from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_two_case_circular.py"
SPEC = importlib.util.spec_from_file_location("seaad_two_case_circular", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_plot_data_preserves_selection_and_testability() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot_data = FIGURE.build_plot_data(bundle)
    links = FIGURE.build_links(plot_data)

    assert bundle["query_rule_id"] == "fdr_only_query_sensitivity"
    assert (
        bundle["result_tier_id"]
        == "posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05"
    )
    assert bundle["minimum_coverage"] == 0.80
    assert bundle["aggregate_q_threshold"] == 0.05
    assert bundle["minimum_conservative_supporting_runs"] == 1
    assert bundle["selected_units"] == 11
    assert bundle["selected_symbols"] == 9
    assert bundle["selected_class_counts"] == {
        "mt_driver": 8,
        "non_mt_driver": 3,
    }
    assert len(plot_data) == 70
    assert plot_data.groupby("case_id").size().to_dict() == {
        "mt_driver": 35,
        "non_mt_driver": 35,
    }
    assert plot_data["slot_status"].value_counts().to_dict() == {
        "no_passing_candidate_slot": 30,
        "not_testable_no_included_runs_slot": 20,
        "ranked_candidate": 11,
        "unused_display_slot": 9,
    }

    occupied = plot_data.loc[plot_data["slot_status"].eq("ranked_candidate")]
    assert set(occupied.loc[occupied["case_id"].eq("mt_driver"), "current_symbol"]) == {
        "MT-ATP6",
        "MT-CO2",
        "MT-CO3",
        "MT-CYB",
        "MT-ND4",
        "MT-ND5",
    }
    assert set(
        occupied.loc[occupied["case_id"].eq("non_mt_driver"), "current_symbol"]
    ) == {"HGSNAT", "BEX3", "RPS27A"}
    assert occupied.loc[occupied["case_id"].eq("mt_driver"), "is_mtdna_gene"].all()
    assert set(
        occupied.loc[
            occupied["extended_reference_member"].fillna(False), "current_symbol"
        ]
    ) >= {"RPS27A"}
    assert occupied.loc[
        occupied["case_id"].eq("non_mt_driver")
        & occupied["extended_reference_member"].fillna(False),
        "current_symbol",
    ].tolist() == ["RPS27A"]

    assert len(links) == 2
    assert set(links["case_id"]) == {"mt_driver"}
    assert set(links["current_symbol"]) == {"MT-CO2", "MT-CYB"}
    assert set(
        links[
            ["anchor_broad_network", "target_broad_network"]
        ].itertuples(index=False, name=None)
    ) == {("Excitatory_neurons", "Inhibitory_neurons")}
    assert not links["link_rule"].str.contains("network_edge", case=False).any()


def test_recurrence_links_can_be_empty(tmp_path: Path) -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot_data = FIGURE.build_plot_data(bundle)
    occupied_indices = plot_data.index[
        plot_data["slot_status"].eq("ranked_candidate")
    ]
    plot_data.loc[occupied_indices, "current_symbol"] = [
        f"synthetic_unique_{index}" for index in range(len(occupied_indices))
    ]
    links = FIGURE.build_links(plot_data)

    assert links.empty
    assert list(links.columns) == [
        "schema_version",
        "figure_id",
        "case_id",
        "current_symbol",
        "selected_network_count_within_class",
        "anchor_broad_network",
        "target_broad_network",
        "anchor_sector_mid_degrees",
        "target_sector_mid_degrees",
        "anchor_negative_log10_acat_q",
        "target_negative_log10_acat_q",
        "link_rule",
    ]
    path = tmp_path / "empty_links.tsv"
    FIGURE.write_tsv(links, path, allow_empty=True)
    observed = pd.read_csv(path, sep="\t")
    assert observed.empty
    assert observed.columns.tolist() == links.columns.tolist()


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
    assert int(status.loc[0, "selected_units"]) == 11
    assert int(status.loc[0, "mt_units"]) == 8
    assert int(status.loc[0, "non_mt_units"]) == 3
    assert int(status.loc[0, "selected_unique_symbols"]) == 9
    assert status.loc[0, "query_rule_id"] == "fdr_only_query_sensitivity"
    assert status.loc[0, "contract_scope"] == "posthoc_exploratory_compact_display_only"

    checks = pd.read_csv(output / f"{FIGURE.FIGURE_ID}_checks.tsv", sep="\t")
    blocking = checks.loc[checks["severity"].eq("blocking")]
    assert blocking["status"].eq("pass").all()
    assert checks.loc[checks["check_id"].eq("visual_review"), "status"].tolist() == [
        "pending"
    ]

    artifacts = pd.read_csv(
        output / f"{FIGURE.FIGURE_ID}_artifacts.tsv", sep="\t", dtype=str
    )
    output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
    assert len(output_rows) == 11
    assert set(output_rows["path"]) == set(FIGURE.PAYLOAD_FILES)
    assert len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1
    assert f"{FIGURE.FIGURE_ID}_artifacts.tsv" not in set(artifacts["path"])
    assert f"{FIGURE.FIGURE_ID}_status.tsv" not in set(artifacts["path"])
    for row in artifacts.itertuples(index=False):
        path = output / row.path if row.artifact_role == "output" else ROOT / row.path
        assert path.stat().st_size == int(row.bytes)
        assert digest(path) == row.sha256

    for basename in ("seaad_mt_driver_circular", "seaad_non_mt_driver_circular"):
        image = Image.open(output / f"{basename}.png")
        assert image.size == (FIGURE.PNG_WIDTH, FIGURE.PNG_HEIGHT)
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= FIGURE.DEFAULT_PNG_DPI - 1
        assert (output / f"{basename}.pdf").read_bytes().startswith(b"%PDF")
        svg = (output / f"{basename}.svg").read_text(encoding="utf-8")
        assert "<path" in svg.lower()
        assert "<text" in svg.lower()
        assert "SEA-AD" in svg
        assert "Post-hoc exploratory" in svg
        assert "rediscover" not in svg.lower()
