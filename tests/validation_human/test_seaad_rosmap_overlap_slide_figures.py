from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/figures/validation_human/plot_seaad_rosmap_overlap_slide_figures.py"
SPEC = importlib.util.spec_from_file_location("seaad_rosmap_overlap_slide_figures", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_frozen_strict_overlap_data() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_strict_plot_data(bundle)
    scorecard = FIGURE.build_strict_scorecard(bundle)
    facets = FIGURE.build_strict_facet_summary(bundle)

    assert len(plot) == 12
    assert not plot.duplicated(["broad_network", "gene"]).any()
    assert plot["pair_status"].value_counts().to_dict() == {
        "strict_shared": 6,
        "rosmap_only": 4,
        "seaad_only": 2,
    }
    assert plot.loc[plot["pair_status"].eq("strict_shared"), "gene"].nunique() == 4
    assert scorecard.set_index("case_id")[
        ["rosmap_testable_selected_units", "seaad_selected_units", "strict_shared_units"]
    ].astype(int).apply(tuple, axis=1).to_dict() == {
        "mt_driver": (19, 8, 6),
        "non_mt_driver": (17, 5, 0),
    }
    assert facets.set_index("broad_network")["shared_selected_units"].astype(int).to_dict() == {
        "Excitatory_neurons": 2,
        "Inhibitory_neurons": 4,
    }
    assert facets.set_index("broad_network")["jaccard_index"].astype(float).round(3).to_dict() == {
        "Excitatory_neurons": 0.286,
        "Inhibitory_neurons": 0.800,
    }


def test_frozen_gene_level_regions_and_geometry() -> None:
    bundle = FIGURE.load_bundle(ROOT)
    plot = FIGURE.build_gene_plot_data(bundle)
    summary = FIGURE.build_gene_region_summary(bundle)

    assert len(plot) == 30
    assert not plot.duplicated(["case_id", "gene"]).any()
    assert plot.groupby(["case_id", "region"]).size().to_dict() == {
        ("mt_driver", "common"): 6,
        ("mt_driver", "rosmap_only"): 4,
        ("non_mt_driver", "rosmap_only"): 15,
        ("non_mt_driver", "seaad_only"): 5,
    }
    counts = summary.set_index(["case_id", "region"])["region_count"].astype(int).to_dict()
    assert counts == {
        ("mt_driver", "rosmap_only"): 4,
        ("mt_driver", "common"): 6,
        ("mt_driver", "seaad_only"): 0,
        ("non_mt_driver", "rosmap_only"): 15,
        ("non_mt_driver", "common"): 0,
        ("non_mt_driver", "seaad_only"): 5,
    }
    assert (summary["geometry_margin"].astype(float) >= 0).all()
    assert int(plot["opcs_not_testable_guardrail"].map(FIGURE.truth).sum()) == 3
    assert int(plot["gene_level_only_common"].map(FIGURE.truth).sum()) == 2


def test_full_atomic_packages(tmp_path: Path) -> None:
    output_base = tmp_path / "figures"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "font-cache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--project-root",
            str(ROOT),
            "--figure",
            "all",
            "--output-base",
            str(output_base),
            "--visual-review-status",
            "complete",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    bundle = FIGURE.load_bundle(ROOT)
    expected_rows = {FIGURE.STRICT_ID: 12, FIGURE.GENE_ID: 30}
    for figure_id in FIGURE.FIGURE_IDS:
        output = output_base / figure_id
        assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE._output_files(figure_id))
        status = pd.read_csv(output / f"{figure_id}_status.tsv", sep="\t")
        assert status.loc[0, "validation_status"] == "validated_complete"
        assert status.loc[0, "visual_review_status"] == "complete"
        assert int(status.loc[0, "failed_blocking_checks"]) == 0
        assert int(status.loc[0, "pending_nonblocking_checks"]) == 0
        assert int(status.loc[0, "plot_data_rows"]) == expected_rows[figure_id]
        assert float(status.loc[0, "figure_width_inches"]) == 12.0
        assert float(status.loc[0, "figure_height_inches"]) == 5.3

        checks = pd.read_csv(output / f"{figure_id}_checks.tsv", sep="\t")
        assert checks["status"].eq("pass").all()
        assert float(checks.loc[checks["check_id"].eq("minimum_font_size"), "observed"].iloc[0]) >= 16.0
        assert {"manual_color_review", "manual_grayscale_review"}.issubset(set(checks["check_id"]))

        artifacts = pd.read_csv(output / f"{figure_id}_artifacts.tsv", sep="\t", dtype=str)
        output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
        assert set(output_rows["path"]) == set(FIGURE._payload_files(figure_id))
        assert len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1
        assert not artifacts["path"].isin(FIGURE._output_files(figure_id)[-2:]).any()
        for row in artifacts.itertuples(index=False):
            path = output / row.path if row.artifact_role == "output" else ROOT / row.path
            assert path.stat().st_size == int(row.bytes)
            assert digest(path) == row.sha256

        image = Image.open(output / f"{figure_id}.png")
        assert image.size == (FIGURE.PNG_WIDTH, FIGURE.PNG_HEIGHT)
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= FIGURE.DEFAULT_PNG_DPI - 1
        assert (output / f"{figure_id}.pdf").read_bytes().startswith(b"%PDF")
        svg = (output / f"{figure_id}.svg").read_text(encoding="utf-8")
        assert "<text" in svg.lower()
        assert "<path" in svg.lower()

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

    strict_svg = (output_base / FIGURE.STRICT_ID / f"{FIGURE.STRICT_ID}.svg").read_text(encoding="utf-8")
    strict_plot = FIGURE.build_strict_plot_data(bundle)
    assert all(gene in strict_svg for gene in strict_plot["gene"])
    assert "nominal p = 2.33 × 10⁻⁴" in strict_svg
    assert "nominal p = 1.22 × 10⁻⁹" in strict_svg
    assert "6 strict units = 4 unique symbols" in strict_svg

    gene_svg = (output_base / FIGURE.GENE_ID / f"{FIGURE.GENE_ID}.svg").read_text(encoding="utf-8")
    gene_plot = FIGURE.build_gene_plot_data(bundle)
    assert all(gene in gene_svg for gene in gene_plot["gene"])
    assert "network identity collapsed" in gene_svg
    assert "SEA-AD OPC KDA unavailable" in gene_svg
    assert "nominal p =" not in gene_svg
