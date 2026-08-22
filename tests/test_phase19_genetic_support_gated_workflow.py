from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/figures/analysis/phase_19_genetic_support/plot_genetic_support_gated_workflow.py"
)
SCRIPT_DIR = SCRIPT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("genetic_support_gated_workflow", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIGURE
SPEC.loader.exec_module(FIGURE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def test_default_output_contract() -> None:
    assert FIGURE.STEM == "genetic_support_gated_workflow"
    assert FIGURE.DEFAULT_OUTPUT_ROOT == (
        "results/figures/analysis/phase_19_genetic_support/gated_workflow"
    )
    assert len(FIGURE.OUTPUT_FILES) == 9


def test_source_contract_and_plot_data() -> None:
    paths = FIGURE.default_sources(ROOT)
    frames, derived = FIGURE.validate_sources(paths)
    assert derived["candidate_contexts"] == 47
    assert derived["unique_genes"] == 25
    assert derived["nuclear_contexts"] == 27
    assert derived["nuclear_genes"] == 19
    assert derived["mtdna_contexts"] == 20
    assert derived["mtdna_genes"] == 6
    assert derived["ad_routes"] == 54
    assert derived["csf_screens"] == 57
    assert derived["candidate_manifest_parity"]
    plot_data = FIGURE.derive_plot_data(derived)
    checks = FIGURE.build_science_checks(frames, derived, plot_data)
    assert checks["status"].eq("pass").all()
    assert set(plot_data.loc[plot_data["record_type"].eq("lane_heading"), "lane"]) == {
        "direct_summary",
        "nuclear_gated",
    }
    visible = "\n".join(
        plot_data[["title", "subtitle", "detail"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
    )
    assert "GCST90027158" in visible
    assert all(accession in visible for accession in FIGURE.CSF_ACCESSIONS)
    assert "NG00130.v2" in visible
    assert "NG00184.v1" in visible
    assert "DNA-to-gene link (QTL)" in visible
    assert "variant correlation (LD)" in visible
    assert "Probability both match" in visible
    assert "(PP.H4)" in visible
    assert "Matched ancestry" in visible
    assert "Public-data matches highlighted three genes" in visible
    assert "APOE  ·  COX7C  ·  SELENOW" in visible
    assert "Four gene–network pairs" in visible
    assert "Top network genes retained" in visible
    assert "Each completed step adds one layer of evidence" in visible
    assert "remaining steps guide future validation" in visible
    assert "Testing stops when a required step fails" not in visible
    assert "not changed by genetic results" not in visible
    assert "direct public-summary" not in visible.lower()
    assert "H0–H4" not in visible
    assert not any(value in visible for value in FIGURE.OMITTED_SAMPLE_COUNTS)


def test_full_package_in_temporary_directory(tmp_path: Path) -> None:
    output = tmp_path / "gated_workflow"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "font-cache")
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(SCRIPT),
            "--output-root",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    assert sorted(path.name for path in output.iterdir()) == sorted(FIGURE.OUTPUT_FILES)
    status = pd.read_csv(output / f"{FIGURE.STEM}_status.tsv", sep="\t")
    assert status.loc[0, "technical_status"] == "validated_complete"
    assert status.loc[0, "visual_review_status"] == "pending"
    assert int(status.loc[0, "candidate_contexts"]) == 47
    assert int(status.loc[0, "nuclear_genes"]) == 19
    assert int(status.loc[0, "mtdna_genes"]) == 6
    assert int(status.loc[0, "clinical_ad_routes"]) == 54
    assert int(status.loc[0, "csf_gene_trait_screens"]) == 57
    assert not bool(status.loc[0, "bellenguez_sample_counts_visible"])
    checks = pd.read_csv(output / f"{FIGURE.STEM}_checks.tsv", sep="\t")
    assert checks["status"].eq("pass").all()
    artifacts = pd.read_csv(
        output / f"{FIGURE.STEM}_artifacts.tsv", sep="\t", dtype=str
    )
    assert len(artifacts) == len(FIGURE.OUTPUT_FILES) - 2
    for row in artifacts.itertuples(index=False):
        assert digest(output / row.path) == row.sha256
    with Image.open(output / f"{FIGURE.STEM}.png") as image:
        assert image.size == FIGURE.EXPECTED_PNG_SIZE
        dpi = image.info.get("dpi")
        assert dpi and min(dpi) >= 449
    caption = (output / f"{FIGURE.STEM}_caption.md").read_text(encoding="utf-8")
    methods = (output / f"{FIGURE.STEM}_methods.md").read_text(encoding="utf-8")
    assert "two parallel evidence paths" in caption
    assert "arrows" in caption.lower() and "causal" in caption.lower()
    assert "intentionally not displayed" in methods
    plot_data = pd.read_csv(output / f"{FIGURE.STEM}_plot_data.tsv", sep="\t")
    visible = "\n".join(
        plot_data[["title", "subtitle", "detail"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
    )
    assert not any(value in visible for value in FIGURE.OMITTED_SAMPLE_COUNTS)
    assert "Public-data matches highlighted three genes" in visible
    assert "After steps 1–3" in visible
    assert "Dedicated mitochondrial data" in visible
    assert "remaining steps guide future validation" in visible
