from __future__ import annotations

import importlib.util
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/presentations/update_gse143758_docx_region_context.py"
SPEC = importlib.util.spec_from_file_location("gse143758_docx_updater", SCRIPT)
assert SPEC and SPEC.loader
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


def test_updated_docx_package_and_regional_contract() -> None:
    path = updater.DEFAULT_DOCX
    assert updater.sha256(path) == updater.FINAL_SHA256
    updater.validate_updated_package(path)
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
        text = updater.visible_text(updater.parse_xml(document_xml))
        assert len(archive.namelist()) == 20
        assert updater.sha256_bytes(archive.read("word/media/image1.png")) == (
            updater.IMAGE_SHA256
        )

    for phrase in updater.NEW_REQUIRED:
        assert phrase.lower() in text.lower()

    for stale in (
        "Multiple brain cell typesYes at 7 months",
        "Use GSE143758 as a disease and cell-state validation dataset, not as the APOE or sex dataset.",
        "not used to estimate APOE or sex interactions",
    ):
        assert stale.lower() not in text.lower()


def test_deck_and_docx_use_the_same_approved_source_hash() -> None:
    deck_script = REPO / "scripts/presentations/build_gse143758_mouse_validation_limitations_deck.py"
    deck_spec = importlib.util.spec_from_file_location("gse143758_deck", deck_script)
    assert deck_spec and deck_spec.loader
    deck = importlib.util.module_from_spec(deck_spec)
    deck_spec.loader.exec_module(deck)
    assert updater.FINAL_SHA256 == deck.SOURCE_DOC_SHA256
    assert updater.sha256(updater.DEFAULT_DOCX) == deck.SOURCE_DOC_SHA256
