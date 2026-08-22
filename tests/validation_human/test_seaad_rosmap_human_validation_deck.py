from __future__ import annotations

import csv
import importlib.util
import zipfile
from pathlib import Path

from pptx import Presentation


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/presentations/build_seaad_rosmap_human_validation_deck.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("seaad_human_validation_deck", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def slide_text(slide) -> str:
    return "\n".join(
        shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False)
    )


def test_derived_values_preserve_scientific_denominators():
    builder = load_builder()
    metrics = builder.derive_metrics()
    assert metrics["donors"] == 78
    assert metrics["supertypes"] == 129
    assert metrics["planned_directions"] == 1548
    assert metrics["completed_directions"] == 520
    assert metrics["kda_calls"] == 42
    assert metrics["selected_units"] == 13
    assert metrics["selected_genes"] == 11
    assert metrics["rosmap_units"] == 47
    assert metrics["rosmap_testable"] == 36
    assert metrics["strict_units"] == 6
    assert metrics["strict_genes"] == 4
    assert metrics["strict_gene_symbols"] == ["MT-CO2", "MT-CO3", "MT-CYB", "MT-ND5"]
    assert metrics["non_mt_rosmap_units"] == 21
    assert metrics["non_mt_testable"] == 17


def test_builds_validated_deck_with_notes_alt_text_and_reports(tmp_path):
    builder = load_builder()
    output = tmp_path / "seaad_rosmap_human_validation.pptx"
    report = tmp_path / "report"
    result = builder.build_deck(
        output, report, visual_review_status="complete"
    )
    assert result == output.resolve()
    builder.validate_deck(output)

    presentation = Presentation(output)
    assert len(presentation.slides) == 15
    assert presentation.slide_width == builder.SLIDE_W
    assert presentation.slide_height == builder.SLIDE_H
    assert len(builder.MAIN_TITLES) == 9
    assert len(builder.APPENDIX_TITLES) == 6

    for slide in presentation.slides:
        note = slide.notes_slide.notes_text_frame.text
        assert len(note.split()) >= builder.MIN_NOTE_WORDS
        assert all(heading in note for heading in builder.NOTE_HEADINGS)

    text = "\n".join(
        slide_text(slide) + "\n" + slide.notes_slide.notes_text_frame.text
        for slide in presentation.slides
    )
    for required in [
        "13 SEA-AD selected units",
        "same-network MT matches",
        "Only 42 directions produced mitochondrial gene sets large enough for KDA",
        "Six ROSMAP units reappear in the same neuronal network and driver class",
        "Zero non-MT overlap does not mean the biology is absent",
        "Mitochondrial genes define the query",
    ]:
        assert required in text
    for forbidden in [
        "84 calls",
        "six unique strict genes",
        "failed replication",
        "1,548 KDA calls",
    ]:
        assert forbidden.lower() not in text.lower()

    pictures = [
        shape
        for slide in presentation.slides
        for shape in slide.shapes
        if shape.shape_type == 13
    ]
    assert len(pictures) == 8
    assert all(
        shape._element.xpath(".//p:cNvPr")[0].get("descr", "")
        for shape in pictures
    )
    slide8_pictures = [
        shape for shape in presentation.slides[7].shapes if shape.shape_type == 13
    ]
    assert len(slide8_pictures) == 1
    assert (
        builder.hashlib.sha256(slide8_pictures[0].image.blob).hexdigest()
        == builder.sha256(builder.FIG["non_mt_diagnostic"])
    )
    assert "Non-MT diagnostic" in slide8_pictures[0]._element.xpath(
        ".//p:cNvPr"
    )[0].get("descr", "")

    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        embedded = {
            builder.hashlib.sha256(archive.read(name)).hexdigest()
            for name in media
        }
        assert {builder.sha256(path) for path in builder.FIG.values()} <= embedded

    status = read_tsv(report / "seaad_rosmap_human_validation_status.tsv")
    assert len(status) == 1
    assert status[0]["validation_status"] == "validated_complete"
    assert status[0]["visual_review_status"] == "complete"
    assert status[0]["main_slides"] == "9"
    assert status[0]["appendix_slides"] == "6"
    assert status[0]["total_slides"] == "15"

    checks = read_tsv(report / "seaad_rosmap_human_validation_checks.tsv")
    assert len(checks) == 14
    assert all(row["passed"] == "True" for row in checks)
    assert any(
        row["check_id"] == "slide8_non_mt_diagnostic_identity"
        for row in checks
    )
    inventory = read_tsv(report / "seaad_rosmap_human_validation_slide_inventory.tsv")
    assert len(inventory) == 15
    assert [row["section"] for row in inventory].count("main") == 9
    assert [row["section"] for row in inventory].count("appendix") == 6


def test_canonical_circles_are_the_only_circle_inputs():
    builder = load_builder()
    expected_parent = (
        REPO / "results/figures/validation_human/seaad_two_case_circular"
    )
    assert builder.FIG["mt_circle"].parent == expected_parent
    assert builder.FIG["non_mt_circle"].parent == expected_parent
    assert "circular_slide" not in str(builder.FIG["mt_circle"])
    assert "summary_slide" not in str(builder.FIG["non_mt_circle"])
