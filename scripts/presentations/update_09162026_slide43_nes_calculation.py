#!/usr/bin/env python3
"""Clarify the direct broad-cell GSEA ranking and NES calculation slides."""

from __future__ import annotations

import argparse
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
BUILD = ROOT / "tmp/presentations/slide43_nes_calculation"
CANDIDATE = BUILD / "candidate.pptx"
EXPECTED_SOURCE_SHA256 = "4addb21efff3be9b76397efb6e2fc96d8c19a73f5813114caa0cc0b64e4acc5b"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS}


SLIDE_TEXT_UPDATES = {
    42: {
        "TextBox 21": "Rank tested MitoCarta MT genes",
        "TextBox 22": "AD-up to AD-down",
        "TextBox 24": "Order genes from strongest AD-up to strongest AD-down evidence.",
    },
    43: {
        "TextBox 1": "How the normalized enrichment score is calculated",
        "TextBox 2": (
            "NES scales a pathway’s observed enrichment score against random gene sets of the same size."
        ),
        "TextBox 4": "MitoCarta MT genes",
        "TextBox 6": "Running score",
        "TextBox 8": "Random gene sets",
        "TextBox 10": "Direction",
        "TextBox 12": "1. RANK THE GENES",
        "TextBox 13": "AD-up to AD-down",
        "TextBox 14": (
            "Rank every tested MitoCarta MT gene by its signed AD-versus-NCI test statistic."
        ),
        "TextBox 16": "2. CALCULATE ES",
        "TextBox 17": "Walk down the ranking",
        "TextBox 18": (
            "The score rises at pathway genes and falls at other genes. ES is the largest distance from zero."
        ),
        "TextBox 20": "3. NORMALIZE ES",
        "TextBox 21": "Compare ES with chance",
        "TextBox 22": (
            "NES = ES ÷ mean(|null ES| in the same direction) from random gene sets of the same size."
        ),
        "TextBox 24": (
            "Study example: female ε3/ε3 excitatory core MT genes had ES = +0.96 and mean |null ES| ≈ 0.35. "
            "NES = +0.96 ÷ 0.35 = +2.75, an AD-up result. Adjusted P = 2.73 × 10⁻¹²."
        ),
    },
}


NOTES_BY_SLIDE = {
    42: (
        "Teaching goal: Explain the direct broad-cell pathway workflow before defining its score.\n"
        "Walk through: For each donor and broad cell class, the analysis combines counts from the contributing fine cell types "
        "into one expression profile. It compares AD with NCI separately within each sex/APOE group and broad cell class. The "
        "analysis then ranks every tested MitoCarta MT gene using a signed AD-versus-NCI test statistic. Positive scores, which "
        "indicate higher expression in AD, appear at the top. Negative scores, which indicate lower expression in AD, appear at "
        "the bottom. Gene set enrichment analysis, abbreviated GSEA, tests whether genes from one pathway collect near either end.\n"
        "Scientific boundary: This ranked-gene pathway analysis uses the tested MitoCarta MT genes at direct broad-cell resolution. "
        "The fine-cell pathway analysis instead tests whether a thresholded DEG list contains more pathway genes than expected.\n"
        "Transition: Calculate the enrichment score and then normalize it for pathway size."
    ),
    43: (
        "Teaching goal: Show how GSEA converts the ranked MitoCarta MT genes into a normalized enrichment score.\n"
        "Walk through: First, the analysis ranks every tested MitoCarta MT gene using sign of log fold change multiplied by the "
        "square root of the edgeR F statistic. This preserves direction: positive scores indicate AD-up and negative scores "
        "indicate AD-down. Second, GSEA walks from the top to the bottom of that ranking. Its running score increases when it "
        "encounters a gene in the pathway and decreases when it encounters another tested gene. The enrichment score, or ES, is "
        "the largest positive or negative distance of that running score from zero. Third, the analysis creates a null distribution "
        "from random gene sets with the same number of genes. It divides ES by the mean absolute null ES among null scores in the "
        "same direction. This produces NES and preserves the sign.\n"
        "Example: For the female epsilon-3 homozygous excitatory-neuron core MT pathway in ROSMAP, ES was 0.9586 and NES was "
        "2.7460. The implied mean positive null ES was approximately 0.3491, because 0.9586 divided by 0.3491 equals 2.7460. "
        "The local Benjamini-Hochberg-adjusted P value was 2.73 times 10 to the minus 12, so this was a significant AD-up result.\n"
        "Scientific boundary: NES is a pathway-level ranking statistic. It is not a fold change, a DEG count, or the percentage of "
        "pathway genes that increased. A large absolute NES indicates stronger concentration toward one end relative to random "
        "gene sets, while the adjusted P value determines statistical significance.\n"
        "Source: scripts/11_run_broad_deg_pathway_analysis.R defines the ranking statistic; "
        "scripts/lib/phase11_deg_pathway_common.R runs fgseaMultilevel; "
        "results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_gsea.tsv.gz contains the example.\n"
        "Transition: Move to Part 7, the sensitivity analyses."
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DECK)
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--install", action="store_true")
    return parser.parse_args()


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
        resolve_part(
            "ppt/presentation.xml",
            targets[slide_id.get(f"{{{R_NS}}}id")],
        )
        for slide_id in presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    ]


def notes_part(parts: dict[str, bytes], slide_part: str) -> str:
    relationships = xml(parts[rels_path(slide_part)])
    for relationship in relationships.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/notesSlide"):
            return resolve_part(slide_part, relationship.get("Target"))
    raise RuntimeError(f"No notes relationship for {slide_part}")


def set_shape_text(root: etree._Element, shape_name: str, value: str) -> None:
    matches = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        names = shape.xpath("./p:nvSpPr/p:cNvPr/@name", namespaces=NS)
        if names and names[0] == shape_name:
            matches.append(shape)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one shape named {shape_name!r}, found {len(matches)}")
    text_nodes = matches[0].xpath(".//a:t", namespaces=NS)
    if not text_nodes:
        raise RuntimeError(f"Shape {shape_name!r} has no text nodes")
    text_nodes[0].text = value
    for node in text_nodes[1:]:
        node.text = ""


def set_notes_body(root: etree._Element, value: str) -> None:
    matches = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        placeholders = shape.xpath("./p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
        if placeholders and placeholders[0].get("type") == "body":
            matches.append(shape)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one notes body, found {len(matches)}")
    text_body = matches[0].find(f"{{{P_NS}}}txBody")
    if text_body is None:
        raise RuntimeError("Notes body lacks p:txBody")
    for paragraph in list(text_body.findall(f"{{{A_NS}}}p")):
        text_body.remove(paragraph)
    for line in value.splitlines():
        paragraph = etree.SubElement(text_body, f"{{{A_NS}}}p")
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        etree.SubElement(run, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
        text = etree.SubElement(run, f"{{{A_NS}}}t")
        text.text = line
        etree.SubElement(paragraph, f"{{{A_NS}}}endParaRPr", lang="en-US", dirty="0")


def make_candidate(source: Path, candidate: Path) -> None:
    with ZipFile(source) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    slides = visible_slide_parts(parts)
    if len(slides) != 153:
        raise RuntimeError(f"Expected 153 slides, found {len(slides)}")

    for number, updates in SLIDE_TEXT_UPDATES.items():
        slide_part = slides[number - 1]
        root = copy.deepcopy(xml(parts[slide_part]))
        for shape_name, value in updates.items():
            set_shape_text(root, shape_name, value)
        parts[slide_part] = xml_bytes(root)

    for number, notes in NOTES_BY_SLIDE.items():
        part = notes_part(parts, slides[number - 1])
        root = copy.deepcopy(xml(parts[part]))
        set_notes_body(root, notes)
        parts[part] = xml_bytes(root)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkstemp(prefix="slide43_", suffix=".pptx", dir=candidate.parent)[1])
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temporary.replace(candidate)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_candidate(candidate: Path) -> None:
    with ZipFile(candidate) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    slides = visible_slide_parts(parts)
    if len(slides) != 153:
        raise RuntimeError("Candidate slide count changed")

    slide42 = " ".join(
        node.text or ""
        for node in xml(parts[slides[41]]).xpath(".//a:t", namespaces=NS)
    )
    slide43 = " ".join(
        node.text or ""
        for node in xml(parts[slides[42]]).xpath(".//a:t", namespaces=NS)
    )
    for phrase in (
        "Rank tested MitoCarta MT genes",
        "AD-up to AD-down",
    ):
        if phrase not in slide42:
            raise RuntimeError(f"Slide 42 lacks: {phrase}")
    for phrase in (
        "How the normalized enrichment score is calculated",
        "NES = ES ÷ mean(|null ES| in the same direction)",
        "NES = +0.96 ÷ 0.35 = +2.75",
        "Adjusted P = 2.73 × 10⁻¹²",
    ):
        if phrase not in slide43:
            raise RuntimeError(f"Slide 43 lacks: {phrase}")
    for number in NOTES_BY_SLIDE:
        part = notes_part(parts, slides[number - 1])
        notes = " ".join(
            node.text or "" for node in xml(parts[part]).xpath(".//a:t", namespaces=NS)
        )
        if "Teaching goal:" not in notes or "Transition:" not in notes:
            raise RuntimeError(f"Slide {number} notes validation failed")


def next_backup(source: Path) -> Path:
    used = set()
    for path in source.parent.glob(f"{source.stem} bak*.pptx"):
        match = re.search(r" bak(\d+)\.pptx$", path.name)
        if match:
            used.add(int(match.group(1)))
    number = 1
    while number in used:
        number += 1
    return source.with_name(f"{source.stem} bak{number}.pptx")


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    candidate = args.candidate.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    source_hash = sha256(source)
    if source == DECK.resolve() and source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"The deck changed after inspection: expected {EXPECTED_SOURCE_SHA256}, found {source_hash}"
        )
    make_candidate(source, candidate)
    validate_candidate(candidate)

    print(f"source_sha256={source_hash}")
    print(f"candidate={candidate}")
    print("updated_slides=42,43")

    if args.install:
        lock = source.with_name(f"~${source.name}")
        if lock.exists():
            raise RuntimeError(f"PowerPoint lock file exists: {lock}")
        if sha256(source) != source_hash:
            raise RuntimeError("The source deck changed before installation")
        backup = next_backup(source)
        shutil.copy2(source, backup)
        shutil.copy2(candidate, source)
        print(f"backup={backup}")
        print(f"installed_sha256={sha256(source)}")


if __name__ == "__main__":
    main()
