#!/usr/bin/env python3
"""Insert the gene-ranking-score explanation after slide 42 and refresh notes."""

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
BUILD = ROOT / "tmp/presentations/rank_score_slide"
CANDIDATE = BUILD / "candidate.pptx"
EXPECTED_SOURCE_SHA256 = "8338806a2af3395c12565772eb34ed74fdfd9043caa329d50be8b72dbb02e202"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS, "ct": CT_NS}


SLIDE43_TEXT = {
    "TextBox 1": "Gene-ranking score for direct broad-cell GSEA",
    "TextBox 2": (
        "Every tested MitoCarta MT gene receives a signed score before pathway testing."
    ),
    "TextBox 4": "AD-up if positive",
    "TextBox 6": "AD-down if negative",
    "TextBox 8": "Strength from F",
    "TextBox 10": "Study-specific rule",
    "TextBox 12": "STUDY RANKING RULE",
    "TextBox 13": "rank score = sign(logFC) × √F",
    "TextBox 14": (
        "logFC is AD versus NCI. Its sign sets the direction. √F sets the score magnitude."
    ),
    "TextBox 16": "WHY USE √F?",
    "TextBox 17": "F measures statistical evidence",
    "TextBox 18": (
        "F comes from the edgeR quasi-likelihood test. For this one-degree-of-freedom "
        "contrast, √F gives a t-like scale and preserves the ordering set by F."
    ),
    "TextBox 20": "WHY NOT logFC ALONE?",
    "TextBox 21": "Large estimates can be noisy",
    "TextBox 22": (
        "Gene A: logFC +2.0, F = 0.25, score +0.5. Gene B: logFC +0.5, "
        "F = 16, score +4.0. Stronger statistical support places Gene B higher."
    ),
    "TextBox 24": (
        "This is the study's ranking rule for targeted MitoCarta GSEA. "
        "GSEA does not require one universal ranking formula."
    ),
}


NOTES42 = (
    "Teaching goal: Explain the four stages of direct broad-cell pathway validation.\n"
    "Walk through: First, the analysis combines cells from one broad class within each donor. Second, it compares AD with "
    "NCI separately within each sex/APOE group and broad cell class. Third, it orders all tested MitoCarta MT genes from "
    "stronger AD-up evidence to stronger AD-down evidence. Fourth, ranked-gene pathway analysis asks whether the genes in "
    "one pathway concentrate toward either end of that ranking.\n"
    "Scientific boundary: This workflow analyzes donor-level broad-cell expression profiles. It ranks every tested MitoCarta "
    "MT gene rather than filtering to significant DEGs first. The fine-cell pathway analysis uses a different method based "
    "on overlap between a thresholded DEG list and a pathway.\n"
    "Transition: The next slide defines the signed score used to rank the tested MitoCarta MT genes."
)


NOTES43 = (
    "Teaching goal: Define the study-specific score used to rank genes before calculating pathway enrichment.\n"
    "Walk through: Within each broad cell, sex, and APOE comparison, the analysis assigns every tested MitoCarta MT gene "
    "the score sign of log fold change multiplied by the square root of the edgeR quasi-likelihood F statistic. The log fold "
    "change compares AD with NCI. Its sign supplies direction: positive means AD-up and negative means AD-down. The F statistic "
    "is nonnegative and measures the strength of evidence for an AD-versus-NCI difference after accounting for variability. "
    "For this one-degree-of-freedom contrast, the square root of F gives a t-like scale while preserving the ordering based on F. "
    "The analysis sorts scores from largest positive to most negative and does not filter to significant DEGs before GSEA.\n"
    "Why not logFC alone: Raw log fold change describes estimated effect size but not uncertainty. Low expression or donor "
    "variability can produce a large but unstable estimate. The illustrative example on the slide shows that a gene with logFC "
    "plus 2.0 and F 0.25 receives score plus 0.5, while a gene with logFC plus 0.5 and F 16 receives score plus 4.0. The "
    "better-supported gene ranks higher.\n"
    "Scientific boundary: This is the study's ranking rule for targeted MitoCarta preranked GSEA. GSEA does not require one "
    "universal ranking statistic. The example values are illustrative and are not observed study genes. In the implementation, "
    "tiny negative F values caused only by numerical precision are clamped to zero.\n"
    "Source: scripts/11_run_broad_deg_pathway_analysis.R computes rank_score = sign(logFC) × sqrt(max(F, 0)); "
    "scripts/08_run_broad_pseudobulk_de.R produces logFC and F with edgeR glmQLFTest.\n"
    "Transition: Use this ranked list to calculate the running enrichment score."
)


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


def set_shape_text_style(
    root: etree._Element,
    name: str,
    *,
    size: int | None = None,
    bold: bool | None = None,
) -> None:
    shape = shape_by_name(root, name)
    for properties in shape.xpath(".//a:rPr", namespaces=NS):
        if size is not None:
            properties.set("sz", str(size))
        if bold is not None:
            properties.set("b", "1" if bold else "0")


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


def clone_rank_slide(
    parts: dict[str, bytes], source_slide_part: str, new_number: int
) -> str:
    source_rels_part = rels_path(source_slide_part)
    source_notes_part = relationship_target(parts, source_slide_part, "notesSlide")
    source_notes_rels_part = rels_path(source_notes_part)

    slide = copy.deepcopy(xml(parts[source_slide_part]))
    for name, value in SLIDE43_TEXT.items():
        replace_shape_text(slide, name, value)
    set_shape_text_style(slide, "TextBox 13", size=1900, bold=True)
    set_shape_text_style(slide, "TextBox 22", size=1140)

    slide_rels = copy.deepcopy(xml(parts[source_rels_part]))
    notes = copy.deepcopy(xml(parts[source_notes_part]))
    set_notes_body(notes, NOTES43)
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


def insert_slide_after_42(parts: dict[str, bytes], slide_part: str) -> None:
    presentation = xml(parts["ppt/presentation.xml"])
    relationships = xml(parts["ppt/_rels/presentation.xml.rels"])
    content_types = xml(parts["[Content_Types].xml"])
    slide_ids = presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    if len(slide_ids) != 155:
        raise RuntimeError(f"Expected 155 source slides, found {len(slide_ids)}")

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
    slide_id_list.insert(slide_id_list.index(slide_ids[41]) + 1, slide_id)

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
        text, count = re.subn(r"(<Slides>)\d+(</Slides>)", r"\g<1>156\2", text, count=1)
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
    if len(visible) != 155:
        raise RuntimeError(f"Expected 155 source slides, found {len(visible)}")
    slide42_part = visible[41]
    slide42_sha = hashlib.sha256(parts[slide42_part]).hexdigest()

    new_slide_part = clone_rank_slide(parts, visible[43], 156)

    notes42_part = relationship_target(parts, slide42_part, "notesSlide")
    notes42 = xml(parts[notes42_part])
    set_notes_body(notes42, NOTES42)
    parts[notes42_part] = xml_bytes(notes42)

    insert_slide_after_42(parts, new_slide_part)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkstemp(prefix="rank_score_", suffix=".pptx", dir=candidate.parent)[1]
    )
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temporary.replace(candidate)
    finally:
        if temporary.exists():
            temporary.unlink()
    return slide42_sha


def slide_text(parts: dict[str, bytes], part: str) -> str:
    return " ".join(xml(parts[part]).xpath(".//a:t/text()", namespaces=NS))


def validate_candidate(path: Path, slide42_sha: str) -> None:
    with ZipFile(path) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 156:
        raise RuntimeError(f"Expected 156 slides, found {len(visible)}")
    if hashlib.sha256(parts[visible[41]]).hexdigest() != slide42_sha:
        raise RuntimeError("Slide 42 content changed; only its notes may be updated")

    expected = {
        42: "How direct broad-cell pathway validation was done",
        43: "Gene-ranking score for direct broad-cell GSEA",
        44: "How the enrichment score is calculated",
        45: "How the normalized enrichment score is calculated",
        46: "Worked example: female ε3/ε3 excitatory core MT genes",
        47: "Sensitivity analyses",
    }
    for number, phrase in expected.items():
        if phrase not in slide_text(parts, visible[number - 1]):
            raise RuntimeError(f"Slide {number} lacks expected text: {phrase}")

    text43 = slide_text(parts, visible[42])
    for phrase in (
        "rank score = sign(logFC) × √F",
        "F measures statistical evidence",
        "WHY NOT logFC ALONE?",
        "Gene B: logFC +0.5",
    ):
        if phrase not in text43:
            raise RuntimeError(f"Slide 43 lacks: {phrase}")

    for number in (42, 43):
        notes_part = relationship_target(parts, visible[number - 1], "notesSlide")
        notes_text = " ".join(xml(parts[notes_part]).xpath(".//a:t/text()", namespaces=NS))
        if "Teaching goal:" not in notes_text or "Transition:" not in notes_text:
            raise RuntimeError(f"Slide {number} notes validation failed")
    notes43_part = relationship_target(parts, visible[42], "notesSlide")
    notes43 = " ".join(xml(parts[notes43_part]).xpath(".//a:t/text()", namespaces=NS))
    if "example values are illustrative" not in notes43:
        raise RuntimeError("Slide 43 notes do not identify the example as illustrative")


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

    slide42_sha = make_candidate(DECK, CANDIDATE)
    validate_candidate(CANDIDATE, slide42_sha)
    if sha256(DECK) != current_hash:
        raise RuntimeError("The source deck changed before installation")

    backup = next_backup_path(DECK)
    shutil.copy2(DECK, backup)
    shutil.copy2(CANDIDATE, DECK)
    print(f"source_sha256={current_hash}")
    print(f"candidate={CANDIDATE}")
    print(f"candidate_sha256={sha256(CANDIDATE)}")
    print("slides=156")
    print(f"backup={backup}")
    print(f"installed={DECK}")


if __name__ == "__main__":
    main()
