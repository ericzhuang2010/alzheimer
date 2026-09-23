#!/usr/bin/env python3
"""Insert an ES-versus-NES concept slide after visible slide 44."""

from __future__ import annotations

import copy
import hashlib
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

from insert_09162026_es_concept_slide import (
    A_NS,
    CT_NS,
    NS,
    P_NS,
    PR_NS,
    R_NS,
    add_content_type_override,
    next_backup_path,
    next_relationship_id,
    relationship_target,
    rels_path,
    replace_note_line,
    replace_shape_text,
    resolve_part,
    sha256,
    slide_text,
    visible_slide_parts,
    xml,
    xml_bytes,
)


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx"
BUILD = ROOT / "tmp/presentations/nes_concept_slide"
CANDIDATE = BUILD / "candidate.pptx"
EXPECTED_SOURCE_SHA256 = "db24a6eb9f689c7e7839c4a04c4786e70c78b6772bcd2c2ce0161baaa3d91adf"


SLIDE45_TEXT = {
    "TextBox 1": "How NES differs from ES",
    "TextBox 2": "NES rescales the raw ES against random gene sets of the same size.",
    "TextBox 12": "RAW ES",
    "TextBox 13": "Observed pathway concentration",
    "TextBox 14": (
        "ES shows where the pathway genes cluster. Its sign gives the AD-up or AD-down direction."
    ),
    "TextBox 16": "NORMALIZATION",
    "TextBox 17": "Compare with same-size random gene sets",
    "TextBox 18": (
        "Calculate ES for random gene sets with the same number of genes. Use random ES values "
        "in the same direction."
    ),
    "TextBox 20": "NES",
    "TextBox 21": "Normalized enrichment strength",
    "TextBox 22": (
        "Divide the observed ES by the expected same-direction ES magnitude. NES keeps the ES sign "
        "and supports comparisons across pathways."
    ),
    "TextBox 24": (
        "Example: ES +0.9586 ÷ mean positive null ES 0.3491 = NES +2.75. "
        "NES is not a fold change. Adjusted P determines significance."
    ),
}


NOTES45 = (
    "Teaching goal: Distinguish the raw enrichment score from the normalized enrichment score.\n"
    "Walk through: ES describes where one pathway's genes concentrate in the ranked list. Its sign gives the AD-up or "
    "AD-down direction, but its raw magnitude depends partly on pathway size and the distribution of rank scores. To calculate "
    "NES, the analysis calculates ES values for random gene sets containing the same number of genes. For a positive observed "
    "ES, normalization uses the mean magnitude of positive random ES values. For a negative observed ES, it uses negative random "
    "ES values. Dividing the observed ES by that same-direction null magnitude produces NES and preserves the original direction.\n"
    "Example: In the female epsilon-3 homozygous excitatory core MT result, the observed ES is 0.9586. The mean positive null ES "
    "magnitude implied by the reported result is 0.3491. Dividing 0.9586 by 0.3491 gives NES 2.746, which rounds to positive 2.75. "
    "This means the observed positive concentration is about 2.75 times the typical positive enrichment magnitude from random "
    "gene sets of the same size.\n"
    "Scientific boundary: NES is a normalized pathway-ranking score. It is not a fold change, DEG count, or percentage. NES alone "
    "does not establish statistical significance. The adjusted P value determines whether the pathway result is significant after "
    "multiple-testing correction. Comparisons across separate cohorts or ranking procedures still require caution.\n"
    "Sources: Bioconductor fgsea documentation; scripts/lib/phase11_deg_pathway_common.R; "
    "results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_gsea.tsv.gz.\n"
    "Transition: The next slide shows how the running score produces the raw ES in a study example."
)


OLD_GOAL44 = (
    "Teaching goal: Explain what the standard weighted GSEA enrichment score means before showing how it is calculated."
)
NEW_GOAL44 = (
    "Teaching goal: Explain what the standard weighted GSEA enrichment score means for one pathway."
)
OLD_TRANSITION44 = (
    "Transition: The next slide shows how the running score produces the ES in a study example."
)
NEW_TRANSITION44 = "Transition: The next slide explains how NES rescales the raw ES."


def set_notes_body(root: etree._Element, value: str) -> None:
    body_shapes = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        placeholders = shape.xpath("./p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
        if placeholders and placeholders[0].get("type") == "body":
            body_shapes.append(shape)
    if len(body_shapes) != 1:
        raise RuntimeError(f"Expected one notes body, found {len(body_shapes)}")
    text_body = body_shapes[0].find(f"{{{P_NS}}}txBody")
    if text_body is None:
        raise RuntimeError("Notes body lacks p:txBody")
    for paragraph in list(text_body.findall(f"{{{A_NS}}}p")):
        text_body.remove(paragraph)
    for line in value.splitlines():
        paragraph = etree.SubElement(text_body, f"{{{A_NS}}}p")
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        etree.SubElement(run, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
        node = etree.SubElement(run, f"{{{A_NS}}}t")
        node.text = line
        etree.SubElement(paragraph, f"{{{A_NS}}}endParaRPr", lang="en-US", dirty="0")


def clone_nes_concept_slide(
    parts: dict[str, bytes], source_slide_part: str, new_number: int
) -> str:
    source_rels_part = rels_path(source_slide_part)
    source_notes_part = relationship_target(parts, source_slide_part, "notesSlide")
    source_notes_rels_part = rels_path(source_notes_part)

    slide = copy.deepcopy(xml(parts[source_slide_part]))
    for name, value in SLIDE45_TEXT.items():
        replace_shape_text(slide, name, value)
    slide_rels = copy.deepcopy(xml(parts[source_rels_part]))
    notes = copy.deepcopy(xml(parts[source_notes_part]))
    set_notes_body(notes, NOTES45)
    notes_rels = copy.deepcopy(xml(parts[source_notes_rels_part]))

    new_slide_part = f"ppt/slides/slide{new_number}.xml"
    new_notes_part = f"ppt/notesSlides/notesSlide{new_number}.xml"
    for relationship in slide_rels.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/notesSlide"):
            relationship.set("Target", f"../notesSlides/notesSlide{new_number}.xml")
    for relationship in notes_rels.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/slide"):
            relationship.set("Target", f"../slides/slide{new_number}.xml")

    parts[new_slide_part] = xml_bytes(slide)
    parts[rels_path(new_slide_part)] = xml_bytes(slide_rels)
    parts[new_notes_part] = xml_bytes(notes)
    parts[rels_path(new_notes_part)] = xml_bytes(notes_rels)
    return new_slide_part


def insert_slide_after_44(parts: dict[str, bytes], slide_part: str) -> None:
    presentation = xml(parts["ppt/presentation.xml"])
    relationships = xml(parts["ppt/_rels/presentation.xml.rels"])
    content_types = xml(parts["[Content_Types].xml"])
    slide_ids = presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    if len(slide_ids) != 157:
        raise RuntimeError(f"Expected 157 source slides, found {len(slide_ids)}")

    relationship_id = next_relationship_id(relationships)
    etree.SubElement(
        relationships,
        f"{{{PR_NS}}}Relationship",
        Id=relationship_id,
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
        Target=f"slides/{PurePosixPath(slide_part).name}",
    )
    slide_id = etree.Element(f"{{{P_NS}}}sldId")
    slide_id.set("id", str(max(int(item.get("id")) for item in slide_ids) + 1))
    slide_id.set(f"{{{R_NS}}}id", relationship_id)
    slide_id_list = slide_ids[0].getparent()
    slide_id_list.insert(slide_id_list.index(slide_ids[43]) + 1, slide_id)

    add_content_type_override(
        content_types,
        f"/{slide_part}",
        "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
    )
    number = int(re.search(r"slide(\d+)\.xml$", slide_part).group(1))
    add_content_type_override(
        content_types,
        f"/ppt/notesSlides/notesSlide{number}.xml",
        "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
    )
    parts["ppt/presentation.xml"] = xml_bytes(presentation)
    parts["ppt/_rels/presentation.xml.rels"] = xml_bytes(relationships)
    parts["[Content_Types].xml"] = xml_bytes(content_types)

    app = parts.get("docProps/app.xml")
    if app:
        text = app.decode("utf-8")
        text, count = re.subn(r"(<Slides>)\d+(</Slides>)", r"\g<1>158\2", text, count=1)
        if count != 1:
            raise RuntimeError("Could not update slide count in docProps/app.xml")
        parts["docProps/app.xml"] = text.encode("utf-8")


def make_candidate(source: Path, candidate: Path) -> str:
    with ZipFile(source) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 157:
        raise RuntimeError(f"Expected 157 source slides, found {len(visible)}")
    slide44_part = visible[43]
    slide44_sha = hashlib.sha256(parts[slide44_part]).hexdigest()

    new_slide_part = clone_nes_concept_slide(parts, slide44_part, 158)

    notes44_part = relationship_target(parts, slide44_part, "notesSlide")
    notes44 = xml(parts[notes44_part])
    replace_note_line(notes44, OLD_GOAL44, NEW_GOAL44)
    replace_note_line(notes44, OLD_TRANSITION44, NEW_TRANSITION44)
    parts[notes44_part] = xml_bytes(notes44)

    insert_slide_after_44(parts, new_slide_part)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkstemp(prefix="nes_concept_", suffix=".pptx", dir=candidate.parent)[1]
    )
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temporary.replace(candidate)
    finally:
        if temporary.exists():
            temporary.unlink()
    return slide44_sha


def validate_candidate(path: Path, slide44_sha: str) -> None:
    with ZipFile(path) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 158:
        raise RuntimeError(f"Expected 158 slides, found {len(visible)}")
    if hashlib.sha256(parts[visible[43]]).hexdigest() != slide44_sha:
        raise RuntimeError("Slide 44 content changed; only its notes may be updated")

    expected = {
        44: "Standard weighted GSEA enrichment score for pathway",
        45: "How NES differs from ES",
        46: "How the enrichment score is calculated",
        47: "How the normalized enrichment score is calculated",
        48: "Worked example: female ε3/ε3 excitatory core MT genes",
        49: "Sensitivity analyses",
    }
    for number, phrase in expected.items():
        if phrase not in slide_text(parts, visible[number - 1]):
            raise RuntimeError(f"Slide {number} lacks expected text: {phrase}")

    text45 = slide_text(parts, visible[44])
    for phrase in (
        "RAW ES",
        "same-size random gene sets",
        "Normalized enrichment strength",
        "NES +2.75",
        "Adjusted P determines significance",
    ):
        if phrase not in text45:
            raise RuntimeError(f"Slide 45 lacks: {phrase}")

    for number in (44, 45):
        notes_part = relationship_target(parts, visible[number - 1], "notesSlide")
        notes_text = " ".join(xml(parts[notes_part]).xpath(".//a:t/text()", namespaces=NS))
        if "Teaching goal:" not in notes_text or "Transition:" not in notes_text:
            raise RuntimeError(f"Slide {number} notes validation failed")


def main() -> None:
    if not DECK.exists():
        raise FileNotFoundError(DECK)
    current_hash = sha256(DECK)
    if current_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            "The deck changed after inspection. "
            f"Expected {EXPECTED_SOURCE_SHA256}, found {current_hash}."
        )
    lock = DECK.with_name(f"~${DECK.name}")
    if lock.exists():
        raise RuntimeError(f"PowerPoint lock file exists: {lock}")

    slide44_sha = make_candidate(DECK, CANDIDATE)
    validate_candidate(CANDIDATE, slide44_sha)
    if sha256(DECK) != current_hash:
        raise RuntimeError("The source deck changed before installation")

    backup = next_backup_path(DECK)
    shutil.copy2(DECK, backup)
    shutil.copy2(CANDIDATE, DECK)
    print(f"source_sha256={current_hash}")
    print(f"candidate={CANDIDATE}")
    print(f"candidate_sha256={sha256(CANDIDATE)}")
    print("slides=158")
    print(f"backup={backup}")
    print(f"installed={DECK}")


if __name__ == "__main__":
    main()
