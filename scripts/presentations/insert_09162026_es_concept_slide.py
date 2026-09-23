#!/usr/bin/env python3
"""Insert a conceptual weighted-GSEA ES slide after visible slide 43."""

from __future__ import annotations

import copy
import hashlib
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx"
BUILD = ROOT / "tmp/presentations/es_concept_slide"
CANDIDATE = BUILD / "candidate.pptx"
EXPECTED_SOURCE_SHA256 = "e6415f8db9587813e387d4e192060e5ff4b31c235d4c0068babf0ccfbda0860f"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS, "ct": CT_NS}


SLIDE44_TEXT = {
    "TextBox 1": "Standard weighted GSEA enrichment score",
    "TextBox 2": "ES indicates where one pathway's genes concentrate in the ranked gene list.",
    "TextBox 12": "LARGE POSITIVE ES",
    "TextBox 13": "Pathway genes cluster near the AD-up end",
    "TextBox 14": (
        "A larger positive value means stronger concentration near the top of the ranked list."
    ),
    "TextBox 16": "ES NEAR ZERO",
    "TextBox 17": "No clear concentration",
    "TextBox 18": (
        "Pathway genes are spread through the ranked list instead of accumulating at either end."
    ),
    "TextBox 20": "LARGE NEGATIVE ES",
    "TextBox 21": "Pathway genes cluster near the AD-down end",
    "TextBox 22": (
        "A more negative value means stronger concentration near the bottom of the ranked list."
    ),
    "TextBox 24": (
        "This is the standard weighted GSEA ES. The sign gives direction. Values farther from zero "
        "mean stronger concentration, not statistical significance."
    ),
}


NOTES44 = (
    "Teaching goal: Explain what the standard weighted GSEA enrichment score means before showing how it is calculated.\n"
    "Walk through: GSEA starts at the AD-up end of the ranked MitoCarta MT gene list and moves toward the AD-down end. "
    "When it encounters a gene from the pathway, the running score increases. Pathway genes with stronger absolute rank "
    "scores have more influence because this analysis uses standard weighted GSEA. Other tested genes decrease the running "
    "score evenly. The enrichment score, abbreviated ES, is the most extreme point reached by that running score. A large "
    "positive ES means pathway genes cluster near the AD-up end. An ES near zero means the pathway genes are dispersed through "
    "the ranked list. A large negative ES means pathway genes cluster near the AD-down end.\n"
    "Scientific boundary: The ES sign gives direction, and distance from zero describes concentration within that ranked list. "
    "The raw ES is not a fold change and does not by itself establish statistical significance. Its magnitude also depends on "
    "pathway size and the rank-score distribution, so the later normalized enrichment score supports comparisons across pathways.\n"
    "Method: The analysis uses fgseaMultilevel with scoreType set to std and gseaParam set to 1, the standard weighted GSEA ES.\n"
    "Sources: Subramanian et al., PNAS 2005, doi:10.1073/pnas.0506580102; Bioconductor fgsea documentation; "
    "scripts/lib/phase11_deg_pathway_common.R; config/phase11_pathway_deg_broad.yml.\n"
    "Transition: The next slide shows how the running score produces the ES in a study example."
)


OLD_TRANSITION43 = "Transition: The next slide uses this ranked list to calculate the running enrichment score."
NEW_TRANSITION43 = "Transition: The next slide explains what the standard weighted GSEA enrichment score means."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xml(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def rels_path(part: str) -> str:
    path = PurePosixPath(part)
    return str(path.parent / "_rels" / f"{path.name}.rels")


def resolve_part(base_part: str, target: str) -> str:
    result: list[str] = []
    for item in (PurePosixPath(base_part).parent / target).parts:
        if item == "..":
            result.pop()
        elif item != ".":
            result.append(item)
    return "/".join(result)


def visible_slide_parts(parts: dict[str, bytes]) -> list[str]:
    presentation = xml(parts["ppt/presentation.xml"])
    relationships = xml(parts["ppt/_rels/presentation.xml.rels"])
    targets = {
        relationship.get("Id"): relationship.get("Target")
        for relationship in relationships.xpath("./pr:Relationship", namespaces=NS)
    }
    return [
        resolve_part("ppt/presentation.xml", targets[item.get(f"{{{R_NS}}}id")])
        for item in presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    ]


def relationship_target(parts: dict[str, bytes], part: str, suffix: str) -> str:
    relationships = xml(parts[rels_path(part)])
    for relationship in relationships.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith(f"/{suffix}"):
            return resolve_part(part, relationship.get("Target"))
    raise RuntimeError(f"No {suffix} relationship for {part}")


def shape_by_name(root: etree._Element, name: str) -> etree._Element:
    matches = root.xpath(
        f'.//p:sp[p:nvSpPr/p:cNvPr/@name="{name}"]', namespaces=NS
    )
    if len(matches) != 1:
        raise RuntimeError(f"Expected one shape named {name!r}, found {len(matches)}")
    return matches[0]


def replace_shape_text(root: etree._Element, name: str, value: str) -> None:
    shape = shape_by_name(root, name)
    text_body = shape.find(f"{{{P_NS}}}txBody")
    if text_body is None:
        raise RuntimeError(f"Shape {name!r} has no text body")
    paragraphs = text_body.findall(f"{{{A_NS}}}p")
    if not paragraphs:
        raise RuntimeError(f"Shape {name!r} has no paragraphs")
    template = paragraphs[0]
    paragraph_properties = template.find(f"{{{A_NS}}}pPr")
    run_properties = template.find(f"{{{A_NS}}}r/{{{A_NS}}}rPr")
    end_properties = template.find(f"{{{A_NS}}}endParaRPr")
    for paragraph in paragraphs:
        text_body.remove(paragraph)
    for line in value.splitlines() or [""]:
        paragraph = etree.SubElement(text_body, f"{{{A_NS}}}p")
        if paragraph_properties is not None:
            paragraph.append(copy.deepcopy(paragraph_properties))
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        if run_properties is not None:
            run.append(copy.deepcopy(run_properties))
        node = etree.SubElement(run, f"{{{A_NS}}}t")
        node.text = line
        if end_properties is not None:
            paragraph.append(copy.deepcopy(end_properties))


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


def replace_note_line(root: etree._Element, old: str, new: str) -> None:
    matches = [node for node in root.xpath(".//a:t", namespaces=NS) if node.text == old]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one notes line {old!r}, found {len(matches)}")
    matches[0].text = new


def next_relationship_id(root: etree._Element) -> str:
    numbers = []
    for relationship in root.xpath("./pr:Relationship", namespaces=NS):
        match = re.fullmatch(r"rId(\d+)", relationship.get("Id", ""))
        if match:
            numbers.append(int(match.group(1)))
    return f"rId{max(numbers, default=0) + 1}"


def add_content_type_override(
    root: etree._Element, part_name: str, content_type: str
) -> None:
    if root.xpath(f'./ct:Override[@PartName="{part_name}"]', namespaces=NS):
        return
    etree.SubElement(
        root,
        f"{{{CT_NS}}}Override",
        PartName=part_name,
        ContentType=content_type,
    )


def clone_es_concept_slide(
    parts: dict[str, bytes], source_slide_part: str, new_number: int
) -> str:
    source_rels_part = rels_path(source_slide_part)
    source_notes_part = relationship_target(parts, source_slide_part, "notesSlide")
    source_notes_rels_part = rels_path(source_notes_part)

    slide = copy.deepcopy(xml(parts[source_slide_part]))
    for name, value in SLIDE44_TEXT.items():
        replace_shape_text(slide, name, value)
    slide_rels = copy.deepcopy(xml(parts[source_rels_part]))
    notes = copy.deepcopy(xml(parts[source_notes_part]))
    set_notes_body(notes, NOTES44)
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


def insert_slide_after_43(parts: dict[str, bytes], slide_part: str) -> None:
    presentation = xml(parts["ppt/presentation.xml"])
    relationships = xml(parts["ppt/_rels/presentation.xml.rels"])
    content_types = xml(parts["[Content_Types].xml"])
    slide_ids = presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    if len(slide_ids) != 156:
        raise RuntimeError(f"Expected 156 source slides, found {len(slide_ids)}")

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
    slide_id_list.insert(slide_id_list.index(slide_ids[42]) + 1, slide_id)

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
        text, count = re.subn(r"(<Slides>)\d+(</Slides>)", r"\g<1>157\2", text, count=1)
        if count != 1:
            raise RuntimeError("Could not update slide count in docProps/app.xml")
        parts["docProps/app.xml"] = text.encode("utf-8")


def slide_text(parts: dict[str, bytes], part: str) -> str:
    return " ".join(xml(parts[part]).xpath(".//a:t/text()", namespaces=NS))


def make_candidate(source: Path, candidate: Path) -> tuple[str, str]:
    with ZipFile(source) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 156:
        raise RuntimeError(f"Expected 156 source slides, found {len(visible)}")
    slide43_part = visible[42]
    slide43_sha = hashlib.sha256(parts[slide43_part]).hexdigest()

    new_slide_part = clone_es_concept_slide(parts, slide43_part, 157)

    notes43_part = relationship_target(parts, slide43_part, "notesSlide")
    notes43 = xml(parts[notes43_part])
    replace_note_line(notes43, OLD_TRANSITION43, NEW_TRANSITION43)
    parts[notes43_part] = xml_bytes(notes43)

    insert_slide_after_43(parts, new_slide_part)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkstemp(prefix="es_concept_", suffix=".pptx", dir=candidate.parent)[1]
    )
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temporary.replace(candidate)
    finally:
        if temporary.exists():
            temporary.unlink()
    return slide43_sha, new_slide_part


def validate_candidate(path: Path, slide43_sha: str) -> None:
    with ZipFile(path) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 157:
        raise RuntimeError(f"Expected 157 slides, found {len(visible)}")
    if hashlib.sha256(parts[visible[42]]).hexdigest() != slide43_sha:
        raise RuntimeError("Slide 43 content changed; only its notes may be updated")

    expected = {
        43: "direct broad-cell GSEA",
        44: "Standard weighted GSEA enrichment score",
        45: "How the enrichment score is calculated",
        46: "How the normalized enrichment score is calculated",
        47: "Worked example: female ε3/ε3 excitatory core MT genes",
        48: "Sensitivity analyses",
    }
    for number, phrase in expected.items():
        if phrase not in slide_text(parts, visible[number - 1]):
            raise RuntimeError(f"Slide {number} lacks expected text: {phrase}")

    text44 = slide_text(parts, visible[43])
    for phrase in (
        "LARGE POSITIVE ES",
        "ES NEAR ZERO",
        "LARGE NEGATIVE ES",
        "not statistical significance",
    ):
        if phrase not in text44:
            raise RuntimeError(f"Slide 44 lacks: {phrase}")
    if any(token in text44 for token in ("P_hit", "P_miss", "N − N", "Σpathway")):
        raise RuntimeError("Slide 44 unexpectedly contains an ES formula")

    for number in (43, 44):
        notes_part = relationship_target(parts, visible[number - 1], "notesSlide")
        notes_text = " ".join(xml(parts[notes_part]).xpath(".//a:t/text()", namespaces=NS))
        if "Teaching goal:" not in notes_text or "Transition:" not in notes_text:
            raise RuntimeError(f"Slide {number} notes validation failed")
    notes44_part = relationship_target(parts, visible[43], "notesSlide")
    notes44 = " ".join(xml(parts[notes44_part]).xpath(".//a:t/text()", namespaces=NS))
    if "standard weighted GSEA" not in notes44 or "gseaParam set to 1" not in notes44:
        raise RuntimeError("Slide 44 notes lack the method definition")


def next_backup_path(deck: Path) -> Path:
    used = {
        int(match.group(1))
        for path in deck.parent.glob(f"{deck.stem} bak*.pptx")
        if (match := re.search(r" bak(\d+)\.pptx$", path.name))
    }
    number = 1
    while number in used:
        number += 1
    return deck.with_name(f"{deck.stem} bak{number}.pptx")


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

    slide43_sha, _ = make_candidate(DECK, CANDIDATE)
    validate_candidate(CANDIDATE, slide43_sha)
    if sha256(DECK) != current_hash:
        raise RuntimeError("The source deck changed before installation")

    backup = next_backup_path(DECK)
    shutil.copy2(DECK, backup)
    shutil.copy2(CANDIDATE, DECK)
    print(f"source_sha256={current_hash}")
    print(f"candidate={CANDIDATE}")
    print(f"candidate_sha256={sha256(CANDIDATE)}")
    print("slides=157")
    print(f"backup={backup}")
    print(f"installed={DECK}")


if __name__ == "__main__":
    main()
