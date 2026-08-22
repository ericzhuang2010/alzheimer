from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image
from pptx import Presentation


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/presentations/build_phase19_genetic_support_deck.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("phase19_deck_builder", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def slide_text(slide) -> str:
    return "\n".join(
        shape.text for shape in slide.shapes
        if getattr(shape, "has_text_frame", False)
    )


def test_five_slide_native_figures_are_separate_packages():
    builder = load_builder()
    assert len(builder.FIG) == 5
    assert len({path.parent for path in builder.FIG.values()}) == 5
    for path in builder.FIG.values():
        assert path.exists()
        with Image.open(path) as image:
            assert image.size == (5580, 2115)


def test_builds_and_validates_external_facing_genetic_support_deck(tmp_path):
    builder = load_builder()
    output = tmp_path / "human_genetic_support_for_key_drivers.pptx"
    assert builder.build_deck(output) == output.resolve()
    builder.validate_deck(output)

    presentation = Presentation(output)
    assert builder.EXPECTED_SLIDE_COUNT == 27
    assert len(presentation.slides) == builder.EXPECTED_SLIDE_COUNT
    assert presentation.slide_width == builder.SLIDE_W
    assert presentation.slide_height == builder.SLIDE_H
    assert all(
        slide.notes_slide.notes_text_frame.text.strip()
        for slide in presentation.slides
    )

    text = "\n".join(slide_text(slide) for slide in presentation.slides)
    for title in [
        "The presentation moves from the study design to results and next steps",
        "Study design and public data",
        "What the genetic evidence showed",
        "How to interpret the results and what to do next",
        "Supporting details",
    ]:
        assert title in text

    for dataset_label in [
        "GCST90027158",
        "GCST90726396",
        "GCST90726397",
        "GCST90726398",
        "NG00184.v1",
        "eQTL Catalogue r7",
        "FunGen-xQTL",
        "GENCODE v44",
        "HGNC",
    ]:
        assert dataset_label in text

    assert "Status: important follow-up remains" in text
    assert "The six mitochondrial genes were not found negative" in text
    assert "No shared-signal probability was available" in text
    assert "full_genetic_support_complete = FALSE" not in text
    assert "PP.H4 = 0" not in text
    assert "mtDNA genes were negative" not in text
    assert "Phase 18" not in text
    assert "Phase 19" not in text
