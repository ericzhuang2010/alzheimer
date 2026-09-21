#!/usr/bin/env python3
"""Expand the direct broad-cell ES/NES explanation into three slides.

The script keeps the existing deck design, replaces visible slide 43 with an
editable running-score figure, and inserts two follow-up slides for the NES
formula and a worked ROSMAP example.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx"
BUILD = ROOT / "tmp/presentations/es_nes_explanation"
CANDIDATE = BUILD / "candidate.pptx"
EXPECTED_SOURCE_SHA256 = "4b200274ae7a412c2320ada6800960bb8dcb8c871e4cbf19ebcf12e322398624"

RANK_FILE = ROOT / "results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_ranked_genes.tsv.gz"
GSEA_FILE = ROOT / "results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_gsea.tsv.gz"
MODULE_FILE = ROOT / "config/phase13_respiratory_modules.tsv"
EXAMPLE_RANK_ID = "Excitatory_neurons::AD_vs_NCI__Female__e33"
EXAMPLE_PATHWAY_ID = "mtdna_oxphos_13"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS, "ct": CT_NS}


SLIDE44_TEXT = {
    "TextBox 1": "How the normalized enrichment score is calculated",
    "TextBox 2": "NES compares the observed enrichment score with random gene sets of the same size.",
    "TextBox 4": "Observed ES",
    "TextBox 6": "Same-size random sets",
    "TextBox 8": "Same direction",
    "TextBox 10": "Normalized score",
    "TextBox 12": "1. OBSERVED ES",
    "TextBox 13": "Use the real pathway genes",
    "TextBox 14": (
        "Calculate ES from the positions of the pathway genes in the ranked MitoCarta MT gene list."
    ),
    "TextBox 16": "2. NULL ES VALUES",
    "TextBox 17": "Use random sets of the same size",
    "TextBox 18": (
        "Repeat the ES calculation for random gene sets with the same number of genes. Keep null scores "
        "with the same sign as the observed ES."
    ),
    "TextBox 20": "3. NORMALIZE",
    "TextBox 21": "NES = ESₒᵦₛ ÷ mean(|ESₙᵤₗₗ|)",
    "TextBox 22": (
        "The null mean uses scores with the same sign as the observed ES. The NES keeps that sign."
    ),
    "TextBox 24": (
        "The NES sign gives direction. Adjusted P < 0.05 gives significance. NES alone does not define significance."
    ),
}


SLIDE45_TEXT = {
    "TextBox 1": "Worked example: female ε3/ε3 excitatory core MT genes",
    "TextBox 2": "ROSMAP direct broad-cell pathway result",
    "TextBox 4": "ROSMAP",
    "TextBox 6": "Direct broad-cell",
    "TextBox 8": "13 core MT genes",
    "TextBox 10": "Positive NES",
    "TextBox 12": "OBSERVED ES",
    "TextBox 13": "+0.9586",
    "TextBox 14": (
        "The running score reaches its largest distance from zero near the AD-up end of the ranking."
    ),
    "TextBox 16": "MEAN POSITIVE NULL ES",
    "TextBox 17": "0.3491",
    "TextBox 18": (
        "This normalization factor is implied by the reported ES divided by the reported NES."
    ),
    "TextBox 20": "NORMALIZED SCORE",
    "TextBox 21": "+2.746 ≈ +2.75",
    "TextBox 22": "NES = 0.9586 ÷ 0.3491. The positive sign gives the AD-up pathway direction.",
    "TextBox 24": (
        "Local BH-adjusted P = 2.73 × 10⁻¹². The pathway result is significant and AD-up; +2.75 is not a fold change."
    ),
}


NOTES42 = (
    "Teaching goal: Explain the direct broad-cell pathway workflow before introducing ES and NES.\n"
    "Walk through: For each donor and broad cell class, the analysis combines counts from the contributing fine cell types "
    "into one expression profile. It compares AD with NCI separately within each sex/APOE group and broad cell class. The "
    "analysis then ranks every tested MitoCarta MT gene using sign of log fold change multiplied by the square root of the "
    "edgeR F statistic. Positive scores indicate stronger AD-up evidence and appear first. Negative scores indicate stronger "
    "AD-down evidence and appear last. Gene set enrichment analysis, abbreviated GSEA, then tests whether one pathway's genes "
    "cluster toward either end of that ranking.\n"
    "Scientific boundary: This ranked-gene pathway analysis uses the tested MitoCarta MT genes at direct broad-cell resolution. "
    "The fine-cell pathway analysis instead tests overlap between a thresholded DEG list and a pathway.\n"
    "Transition: First calculate the running enrichment score, abbreviated ES."
)


NOTES43 = (
    "Teaching goal: Explain exactly how the running enrichment score is calculated using the real female epsilon-3 homozygous "
    "excitatory-neuron example.\n"
    "Walk through: The x-axis contains 1,134 tested MitoCarta MT genes ordered from strongest AD-up to strongest AD-down evidence. "
    "When the walk reaches a core MT gene, it adds the absolute value of that gene's rank score divided by the sum of the "
    "absolute rank scores for all 13 core MT genes. At every other tested gene, it subtracts one divided by 1,134 minus 13. "
    "The blue curve is the cumulative running score. The short orange marks show the positions of the 13 core MT genes. Twelve "
    "appear among the first 34 ranked genes; MT-ND6 appears at rank 239. The curve peaks at rank 34 with ES 0.9586.\n"
    "Scientific boundary: ES depends on both the positions and the rank-score magnitudes of pathway genes. It is not the fraction "
    "of pathway genes that are DEGs and it is not an expression fold change.\n"
    "Source: results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_ranked_genes.tsv.gz; "
    "config/phase13_respiratory_modules.tsv; scripts/lib/phase11_deg_pathway_common.R.\n"
    "Transition: Normalize the observed ES against same-size random gene sets."
)


NOTES44 = (
    "Teaching goal: Separate the NES calculation from the ES calculation and distinguish direction from significance.\n"
    "Walk through: The observed ES comes from the actual pathway genes. The analysis then calculates ES values for random gene "
    "sets that contain the same number of genes and come from the same ranked MitoCarta MT gene list. For a positive observed ES, "
    "the denominator is the mean magnitude of positive null ES values. For a negative observed ES, the denominator uses negative "
    "null ES values. NES equals the observed ES divided by this same-direction null mean. Normalization makes scores more comparable "
    "across pathways with different sizes.\n"
    "Scientific boundary: The sign of NES gives the pathway direction. The adjusted P value determines whether the result is "
    "statistically significant after multiple-testing correction. NES is not a fold change, DEG count, or percentage.\n"
    "Source: scripts/lib/phase11_deg_pathway_common.R runs fgseaMultilevel with exponent 1.\n"
    "Transition: Substitute the study values into the NES formula."
)


NOTES45 = (
    "Teaching goal: Work through the reported female epsilon-3 homozygous excitatory core MT result numerically.\n"
    "Walk through: The observed ES is 0.9585936. The reported NES is 2.7460272. Dividing ES by NES gives an implied positive-null "
    "normalization factor of 0.3490838. Substituting the rounded values gives 0.9586 divided by 0.3491, which equals 2.746 and rounds "
    "to 2.75. The positive sign indicates that the core MT genes cluster toward the AD-up end. The local Benjamini-Hochberg-adjusted "
    "P value is 2.73 times 10 to the minus 12, below 0.05, so the pathway result is significant.\n"
    "Scientific boundary: The value 2.75 is a normalized pathway-ranking score. It is not a 2.75-fold expression increase and does "
    "not mean that every core MT gene is individually significant.\n"
    "Source: results/minerva_production/11_pathway_deg_broad/broad_deg_pathway_gsea.tsv.gz.\n"
    "Transition: Move to Part 7, the sensitivity analyses."
)


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
    tx_body = shape.find(f"{{{P_NS}}}txBody")
    if tx_body is None:
        raise RuntimeError(f"Shape {name!r} has no text body")
    paragraphs = tx_body.findall(f"{{{A_NS}}}p")
    if not paragraphs:
        raise RuntimeError(f"Shape {name!r} has no paragraphs")
    template = paragraphs[0]
    p_pr = template.find(f"{{{A_NS}}}pPr")
    r_pr = template.find(f"{{{A_NS}}}r/{{{A_NS}}}rPr")
    end_pr = template.find(f"{{{A_NS}}}endParaRPr")
    for paragraph in paragraphs:
        tx_body.remove(paragraph)
    for line in value.splitlines() or [""]:
        paragraph = etree.SubElement(tx_body, f"{{{A_NS}}}p")
        if p_pr is not None:
            paragraph.append(copy.deepcopy(p_pr))
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        if r_pr is not None:
            run.append(copy.deepcopy(r_pr))
        text = etree.SubElement(run, f"{{{A_NS}}}t")
        text.text = line
        if end_pr is not None:
            paragraph.append(copy.deepcopy(end_pr))


def set_shape_geometry(
    root: etree._Element, name: str, x: int, y: int, cx: int, cy: int
) -> None:
    shape = shape_by_name(root, name)
    xfrm = shape.find("./p:spPr/a:xfrm", namespaces=NS)
    if xfrm is None:
        raise RuntimeError(f"Shape {name!r} lacks xfrm")
    off = xfrm.find("./a:off", namespaces=NS)
    ext = xfrm.find("./a:ext", namespaces=NS)
    if off is None or ext is None:
        raise RuntimeError(f"Shape {name!r} lacks geometry")
    off.set("x", str(x))
    off.set("y", str(y))
    ext.set("cx", str(cx))
    ext.set("cy", str(cy))


def set_shape_text_style(
    root: etree._Element,
    name: str,
    *,
    size: int | None = None,
    bold: bool | None = None,
    color: str | None = None,
    align: str | None = None,
    anchor: str | None = None,
) -> None:
    shape = shape_by_name(root, name)
    if size is not None or bold is not None or color is not None:
        for run_properties in shape.xpath(".//a:rPr", namespaces=NS):
            if size is not None:
                run_properties.set("sz", str(size))
            if bold is not None:
                run_properties.set("b", "1" if bold else "0")
            if color is not None:
                for fill in run_properties.xpath("./a:solidFill", namespaces=NS):
                    run_properties.remove(fill)
                solid = etree.Element(f"{{{A_NS}}}solidFill")
                etree.SubElement(solid, f"{{{A_NS}}}srgbClr", val=color)
                run_properties.insert(0, solid)
    if align is not None:
        for paragraph_properties in shape.xpath(".//a:pPr", namespaces=NS):
            paragraph_properties.set("algn", align)
    if anchor is not None:
        body = shape.find("./p:txBody/a:bodyPr", namespaces=NS)
        if body is not None:
            body.set("anchor", anchor)


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
        text = etree.SubElement(run, f"{{{A_NS}}}t")
        text.text = line
        etree.SubElement(paragraph, f"{{{A_NS}}}endParaRPr", lang="en-US", dirty="0")


def next_relationship_id(rels_root: etree._Element) -> str:
    numbers = []
    for relationship in rels_root.xpath("./pr:Relationship", namespaces=NS):
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


def clone_slide(
    parts: dict[str, bytes],
    source_slide_part: str,
    new_number: int,
    texts: dict[str, str],
    notes: str,
) -> str:
    source_rels_part = rels_path(source_slide_part)
    source_notes_part = relationship_target(parts, source_slide_part, "notesSlide")
    source_notes_rels_part = rels_path(source_notes_part)

    slide_root = copy.deepcopy(xml(parts[source_slide_part]))
    for name, value in texts.items():
        replace_shape_text(slide_root, name, value)
    slide_rels_root = copy.deepcopy(xml(parts[source_rels_part]))
    notes_root = copy.deepcopy(xml(parts[source_notes_part]))
    set_notes_body(notes_root, notes)
    notes_rels_root = copy.deepcopy(xml(parts[source_notes_rels_part]))

    new_slide_part = f"ppt/slides/slide{new_number}.xml"
    new_slide_rels_part = rels_path(new_slide_part)
    new_notes_part = f"ppt/notesSlides/notesSlide{new_number}.xml"
    new_notes_rels_part = rels_path(new_notes_part)

    for relationship in slide_rels_root.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/notesSlide"):
            relationship.set("Target", f"../notesSlides/notesSlide{new_number}.xml")
    for relationship in notes_rels_root.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/slide"):
            relationship.set("Target", f"../slides/slide{new_number}.xml")

    parts[new_slide_part] = xml_bytes(slide_root)
    parts[new_slide_rels_part] = xml_bytes(slide_rels_root)
    parts[new_notes_part] = xml_bytes(notes_root)
    parts[new_notes_rels_part] = xml_bytes(notes_rels_root)
    return new_slide_part


def make_textbox(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    text: str,
    *,
    size: int = 1100,
    bold: bool = False,
    color: str = "1F2730",
    align: str = "l",
    anchor: str = "t",
) -> etree._Element:
    shape = etree.Element(f"{{{P_NS}}}sp")
    nv = etree.SubElement(shape, f"{{{P_NS}}}nvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=name)
    cnv = etree.SubElement(nv, f"{{{P_NS}}}cNvSpPr")
    etree.SubElement(cnv, f"{{{A_NS}}}spLocks", noGrp="1")
    etree.SubElement(nv, f"{{{P_NS}}}nvPr")
    sp_pr = etree.SubElement(shape, f"{{{P_NS}}}spPr")
    xfrm = etree.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    etree.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    etree.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    geom = etree.SubElement(sp_pr, f"{{{A_NS}}}prstGeom", prst="rect")
    etree.SubElement(geom, f"{{{A_NS}}}avLst")
    etree.SubElement(sp_pr, f"{{{A_NS}}}noFill")
    tx_body = etree.SubElement(shape, f"{{{P_NS}}}txBody")
    etree.SubElement(
        tx_body,
        f"{{{A_NS}}}bodyPr",
        wrap="square",
        lIns="27432",
        tIns="13716",
        rIns="27432",
        bIns="13716",
        anchor=anchor,
    )
    etree.SubElement(tx_body, f"{{{A_NS}}}lstStyle")
    for line in text.splitlines() or [""]:
        paragraph = etree.SubElement(tx_body, f"{{{A_NS}}}p")
        p_pr = etree.SubElement(paragraph, f"{{{A_NS}}}pPr", algn=align)
        etree.SubElement(p_pr, f"{{{A_NS}}}buNone")
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        r_pr = etree.SubElement(run, f"{{{A_NS}}}rPr", sz=str(size), b="1" if bold else "0")
        solid = etree.SubElement(r_pr, f"{{{A_NS}}}solidFill")
        etree.SubElement(solid, f"{{{A_NS}}}srgbClr", val=color)
        etree.SubElement(r_pr, f"{{{A_NS}}}latin", typeface="Arial")
        etree.SubElement(r_pr, f"{{{A_NS}}}ea", typeface="Arial")
        etree.SubElement(r_pr, f"{{{A_NS}}}cs", typeface="Arial")
        node = etree.SubElement(run, f"{{{A_NS}}}t")
        node.text = line
        etree.SubElement(paragraph, f"{{{A_NS}}}endParaRPr", lang="en-US")
    return shape


def make_line(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    *,
    color: str,
    width: int = 12700,
    dash: str | None = None,
) -> etree._Element:
    shape = etree.Element(f"{{{P_NS}}}sp")
    nv = etree.SubElement(shape, f"{{{P_NS}}}nvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=name)
    etree.SubElement(nv, f"{{{P_NS}}}cNvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}nvPr")
    sp_pr = etree.SubElement(shape, f"{{{P_NS}}}spPr")
    xfrm = etree.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    etree.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    etree.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    geom = etree.SubElement(sp_pr, f"{{{A_NS}}}prstGeom", prst="line")
    etree.SubElement(geom, f"{{{A_NS}}}avLst")
    line = etree.SubElement(sp_pr, f"{{{A_NS}}}ln", w=str(width))
    solid = etree.SubElement(line, f"{{{A_NS}}}solidFill")
    etree.SubElement(solid, f"{{{A_NS}}}srgbClr", val=color)
    if dash:
        etree.SubElement(line, f"{{{A_NS}}}prstDash", val=dash)
    return shape


def make_ellipse(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    diameter: int,
    *,
    fill_color: str,
) -> etree._Element:
    shape = etree.Element(f"{{{P_NS}}}sp")
    nv = etree.SubElement(shape, f"{{{P_NS}}}nvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=name)
    etree.SubElement(nv, f"{{{P_NS}}}cNvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}nvPr")
    sp_pr = etree.SubElement(shape, f"{{{P_NS}}}spPr")
    xfrm = etree.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    etree.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    etree.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(diameter), cy=str(diameter))
    geom = etree.SubElement(sp_pr, f"{{{A_NS}}}prstGeom", prst="ellipse")
    etree.SubElement(geom, f"{{{A_NS}}}avLst")
    fill = etree.SubElement(sp_pr, f"{{{A_NS}}}solidFill")
    etree.SubElement(fill, f"{{{A_NS}}}srgbClr", val=fill_color)
    line = etree.SubElement(sp_pr, f"{{{A_NS}}}ln")
    etree.SubElement(line, f"{{{A_NS}}}noFill")
    return shape


def make_curve(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    values: list[float],
    *,
    color: str,
) -> etree._Element:
    shape = etree.Element(f"{{{P_NS}}}sp")
    nv = etree.SubElement(shape, f"{{{P_NS}}}nvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=name)
    etree.SubElement(nv, f"{{{P_NS}}}cNvSpPr")
    etree.SubElement(nv, f"{{{P_NS}}}nvPr")
    sp_pr = etree.SubElement(shape, f"{{{P_NS}}}spPr")
    xfrm = etree.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    etree.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    etree.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    custom = etree.SubElement(sp_pr, f"{{{A_NS}}}custGeom")
    for tag in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(custom, f"{{{A_NS}}}{tag}")
    etree.SubElement(custom, f"{{{A_NS}}}rect", l="l", t="t", r="r", b="b")
    paths = etree.SubElement(custom, f"{{{A_NS}}}pathLst")
    path = etree.SubElement(
        paths,
        f"{{{A_NS}}}path",
        w="1000000",
        h="1000000",
        fill="none",
        stroke="1",
        extrusionOk="0",
    )
    y_max = 1.02
    for index, value in enumerate(values):
        px = round(index * 1_000_000 / max(len(values) - 1, 1))
        py = round((y_max - max(0.0, min(y_max, value))) * 1_000_000 / y_max)
        command = etree.SubElement(
            path,
            f"{{{A_NS}}}{'moveTo' if index == 0 else 'lnTo'}",
        )
        etree.SubElement(command, f"{{{A_NS}}}pt", x=str(px), y=str(py))
    etree.SubElement(sp_pr, f"{{{A_NS}}}noFill")
    line = etree.SubElement(sp_pr, f"{{{A_NS}}}ln", w="33000", cap="rnd")
    solid = etree.SubElement(line, f"{{{A_NS}}}solidFill")
    etree.SubElement(solid, f"{{{A_NS}}}srgbClr", val=color)
    etree.SubElement(line, f"{{{A_NS}}}round")
    return shape


def load_example() -> dict[str, object]:
    ranks = pd.read_csv(RANK_FILE, sep="\t")
    ranks = ranks.loc[ranks["rank_id"].eq(EXAMPLE_RANK_ID)].sort_values("rank_position")
    modules = pd.read_csv(MODULE_FILE, sep="\t")
    pathway_genes = set(
        modules.loc[
            modules["module_id"].eq(EXAMPLE_PATHWAY_ID), "current_approved_symbol"
        ].astype(str)
    )
    hits = ranks["gene"].isin(pathway_genes).to_numpy()
    scores = ranks["rank_score"].astype(float).to_numpy()
    hit_weight = abs(scores[hits]).sum()
    miss_count = len(ranks) - int(hits.sum())
    running = []
    value = 0.0
    for is_hit, score in zip(hits, scores, strict=True):
        if is_hit:
            value += abs(float(score)) / hit_weight
        else:
            value -= 1.0 / miss_count
        running.append(value)

    results = pd.read_csv(GSEA_FILE, sep="\t")
    result = results.loc[
        results["rank_id"].eq(EXAMPLE_RANK_ID)
        & results["pathway_id"].eq(EXAMPLE_PATHWAY_ID)
    ].iloc[0]
    peak_index = max(range(len(running)), key=lambda index: abs(running[index]))
    if not math.isclose(
        running[peak_index], float(result["enrichment_score"]), rel_tol=0, abs_tol=1e-12
    ):
        raise RuntimeError("Calculated running score does not reproduce the reported ES")
    return {
        "n": len(ranks),
        "nh": int(hits.sum()),
        "running": running,
        "hit_positions": [int(value) for value in ranks.loc[hits, "rank_position"]],
        "peak_position": peak_index + 1,
        "es": float(result["enrichment_score"]),
        "nes": float(result["normalized_enrichment_score"]),
        "adjusted_p": float(result["local_fdr_bh"]),
    }


def build_es_slide(root: etree._Element, example: dict[str, object]) -> None:
    replace_shape_text(root, "TextBox 1", "How the enrichment score is calculated")
    replace_shape_text(
        root,
        "TextBox 2",
        (
            "GSEA walks through 1,134 tested MitoCarta MT genes ranked from strongest AD-up "
            "to strongest AD-down evidence."
        ),
    )

    sp_tree = root.find(".//p:spTree", namespaces=NS)
    if sp_tree is None:
        raise RuntimeError("Slide lacks p:spTree")
    keep = {
        "TextBox 1",
        "TextBox 2",
        "Rounded Rectangle 11",
        "TextBox 12",
        "TextBox 13",
        "TextBox 14",
        "TextBox 16",
        "TextBox 17",
        "TextBox 18",
        "Rounded Rectangle 19",
        "Rounded Rectangle 23",
        "TextBox 24",
    }
    for shape in list(sp_tree.xpath("./p:sp", namespaces=NS)):
        names = shape.xpath("./p:nvSpPr/p:cNvPr/@name", namespaces=NS)
        if names and names[0] not in keep:
            sp_tree.remove(shape)

    set_shape_geometry(root, "Rounded Rectangle 11", 658368, 1440000, 3420000, 4550000)
    set_shape_geometry(root, "Rounded Rectangle 19", 4270000, 1440000, 7420000, 4550000)
    set_shape_geometry(root, "Rounded Rectangle 23", 658368, 6173812, 10881360, 493776)
    set_shape_geometry(root, "TextBox 24", 896112, 6230110, 10405872, 237744)

    replace_shape_text(root, "TextBox 12", "RUNNING-SCORE RULES")
    replace_shape_text(root, "TextBox 13", "Pathway gene")
    replace_shape_text(root, "TextBox 14", "+ |rᵢ| ÷ Σpathway |rⱼ|")
    replace_shape_text(root, "TextBox 16", "Other tested gene")
    replace_shape_text(root, "TextBox 17", "− 1 ÷ (N − Nₕ)")
    replace_shape_text(
        root,
        "TextBox 18",
        (
            "rᵢ = signed rank score\n"
            "Σpathway |rⱼ| = total absolute score of the 13 pathway genes\n"
            "N = 1,134 tested genes; Nₕ = 13 pathway genes"
        ),
    )
    replace_shape_text(
        root,
        "TextBox 24",
        (
            "ES is the largest signed distance from zero. Here, ES = +0.9586 because core MT genes "
            "cluster near the AD-up end."
        ),
    )

    set_shape_geometry(root, "TextBox 12", 900000, 1740000, 2700000, 230000)
    set_shape_geometry(root, "TextBox 13", 900000, 2240000, 2700000, 300000)
    set_shape_geometry(root, "TextBox 14", 900000, 2570000, 2700000, 550000)
    set_shape_geometry(root, "TextBox 16", 900000, 3400000, 2700000, 300000)
    set_shape_geometry(root, "TextBox 17", 900000, 3730000, 2700000, 550000)
    set_shape_geometry(root, "TextBox 18", 900000, 4570000, 2700000, 920000)
    set_shape_text_style(root, "TextBox 12", size=940, bold=True, color="9E3A00", align="l")
    set_shape_text_style(root, "TextBox 13", size=1260, bold=True, color="0F233D", align="l")
    set_shape_text_style(root, "TextBox 14", size=1680, bold=True, color="9E3A00", align="l", anchor="ctr")
    set_shape_text_style(root, "TextBox 16", size=1260, bold=True, color="0F233D", align="l")
    set_shape_text_style(root, "TextBox 17", size=1680, bold=True, color="2F5597", align="l", anchor="ctr")
    set_shape_text_style(root, "TextBox 18", size=1100, bold=False, color="4E5A68", align="l", anchor="ctr")
    set_shape_text_style(root, "TextBox 24", size=1100, bold=True, color="7E4C9A", align="ctr")

    existing_ids = [
        int(value)
        for value in root.xpath(".//p:cNvPr/@id", namespaces=NS)
        if str(value).isdigit()
    ]
    shape_id = max(existing_ids, default=25) + 1
    chart_x, chart_y, chart_w, chart_h = 4700000, 2120000, 6260000, 2650000
    chart_bottom = chart_y + chart_h
    y_max = 1.02

    sp_tree.append(
        make_textbox(
            shape_id,
            "Chart title",
            4700000,
            1640000,
            6260000,
            300000,
            "Female ε3/ε3 excitatory core MT example",
            size=1260,
            bold=True,
            color="0F233D",
            align="ctr",
            anchor="ctr",
        )
    )
    shape_id += 1
    for label_value in (0.0, 0.5, 1.0):
        y = chart_y + round((y_max - label_value) / y_max * chart_h)
        sp_tree.append(
            make_line(
                shape_id,
                f"Gridline {label_value}",
                chart_x,
                y,
                chart_w,
                0,
                color="CBD5E1" if label_value else "7B8794",
                width=8000 if label_value else 15000,
                dash="dash" if label_value else None,
            )
        )
        shape_id += 1
        sp_tree.append(
            make_textbox(
                shape_id,
                f"Y label {label_value}",
                chart_x - 420000,
                y - 100000,
                360000,
                200000,
                f"{label_value:.1f}",
                size=860,
                color="4E5A68",
                align="r",
                anchor="ctr",
            )
        )
        shape_id += 1

    sp_tree.append(
        make_curve(
            shape_id,
            "Running enrichment score curve",
            chart_x,
            chart_y,
            chart_w,
            chart_h,
            list(example["running"]),
            color="2F5597",
        )
    )
    shape_id += 1

    n = int(example["n"])
    for position in example["hit_positions"]:
        x = chart_x + round((int(position) - 1) / (n - 1) * chart_w)
        sp_tree.append(
            make_line(
                shape_id,
                f"Core MT hit rank {position}",
                x,
                chart_bottom + 35000,
                0,
                180000,
                color="D55E00",
                width=18000,
            )
        )
        shape_id += 1

    peak_position = int(example["peak_position"])
    peak_value = float(example["es"])
    peak_x = chart_x + round((peak_position - 1) / (n - 1) * chart_w)
    peak_y = chart_y + round((y_max - peak_value) / y_max * chart_h)
    sp_tree.append(
        make_line(
            shape_id,
            "Peak guide",
            peak_x,
            peak_y,
            0,
            chart_bottom - peak_y,
            color="7E4C9A",
            width=11000,
            dash="dash",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_ellipse(
            shape_id,
            "Peak point",
            peak_x - 55000,
            peak_y - 55000,
            110000,
            fill_color="7E4C9A",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "Peak annotation",
            peak_x + 80000,
            peak_y + 100000,
            1400000,
            430000,
            "Peak ES = +0.9586\nat rank 34",
            size=930,
            bold=True,
            color="7E4C9A",
            align="l",
            anchor="ctr",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "AD-up label",
            chart_x,
            chart_bottom + 260000,
            1200000,
            250000,
            "AD-up",
            size=930,
            bold=True,
            color="2F5597",
            align="l",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "AD-down label",
            chart_x + chart_w - 1200000,
            chart_bottom + 260000,
            1200000,
            250000,
            "AD-down",
            size=930,
            bold=True,
            color="D55E00",
            align="r",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "Rank axis label",
            chart_x + 1100000,
            chart_bottom + 520000,
            chart_w - 2200000,
            300000,
            "Ranked tested MitoCarta MT genes",
            size=900,
            color="4E5A68",
            align="ctr",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "Running score label",
            chart_x - 20000,
            chart_y - 260000,
            1400000,
            230000,
            "Running score",
            size=900,
            color="4E5A68",
            align="l",
        )
    )
    shape_id += 1
    sp_tree.append(
        make_textbox(
            shape_id,
            "Hit rug legend",
            chart_x + chart_w - 2300000,
            chart_y - 260000,
            2300000,
            230000,
            "Orange marks = core MT genes",
            size=860,
            color="D55E00",
            align="r",
        )
    )


def update_package(
    parts: dict[str, bytes], new_slide_parts: list[str], insert_after_index: int
) -> None:
    presentation = xml(parts["ppt/presentation.xml"])
    presentation_rels = xml(parts["ppt/_rels/presentation.xml.rels"])
    content_types = xml(parts["[Content_Types].xml"])
    slide_ids = presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    if len(slide_ids) != 153:
        raise RuntimeError(f"Expected 153 source slides, found {len(slide_ids)}")
    slide_id_list = slide_ids[0].getparent()
    insert_at = slide_id_list.index(slide_ids[insert_after_index]) + 1
    next_slide_id = max(int(item.get("id")) for item in slide_ids) + 1

    for offset, slide_part in enumerate(new_slide_parts):
        relationship_id = next_relationship_id(presentation_rels)
        etree.SubElement(
            presentation_rels,
            f"{{{PR_NS}}}Relationship",
            Id=relationship_id,
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
            Target=f"slides/{PurePosixPath(slide_part).name}",
        )
        slide_id = etree.Element(f"{{{P_NS}}}sldId")
        slide_id.set("id", str(next_slide_id + offset))
        slide_id.set(f"{{{R_NS}}}id", relationship_id)
        slide_id_list.insert(insert_at + offset, slide_id)

        number = int(re.search(r"slide(\d+)\.xml$", slide_part).group(1))
        add_content_type_override(
            content_types,
            f"/{slide_part}",
            "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
        )
        add_content_type_override(
            content_types,
            f"/ppt/notesSlides/notesSlide{number}.xml",
            "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
        )

    parts["ppt/presentation.xml"] = xml_bytes(presentation)
    parts["ppt/_rels/presentation.xml.rels"] = xml_bytes(presentation_rels)
    parts["[Content_Types].xml"] = xml_bytes(content_types)

    app = parts.get("docProps/app.xml")
    if app:
        app_text = app.decode("utf-8")
        app_text, count = re.subn(
            r"(<Slides>)\d+(</Slides>)", r"\g<1>155\2", app_text, count=1
        )
        if count != 1:
            raise RuntimeError("Could not update slide count in docProps/app.xml")
        parts["docProps/app.xml"] = app_text.encode("utf-8")


def validate_candidate(path: Path) -> None:
    with ZipFile(path) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 155:
        raise RuntimeError(f"Expected 155 slides, found {len(visible)}")

    expected = {
        40: "Direct broad-cell validation",
        42: "How direct broad-cell pathway validation was done",
        43: "How the enrichment score is calculated",
        44: "How the normalized enrichment score is calculated",
        45: "Worked example: female ε3/ε3 excitatory core MT genes",
        46: "Sensitivity analyses",
    }
    for number, phrase in expected.items():
        root = xml(parts[visible[number - 1]])
        text = " ".join(root.xpath(".//a:t/text()", namespaces=NS))
        if phrase not in text:
            raise RuntimeError(f"Slide {number} lacks expected text: {phrase}")

    slide43 = xml(parts[visible[42]])
    names = set(slide43.xpath(".//p:cNvPr/@name", namespaces=NS))
    for name in (
        "Running enrichment score curve",
        "Peak annotation",
        "Hit rug legend",
    ):
        if name not in names:
            raise RuntimeError(f"Slide 43 lacks figure element: {name}")
    curve = shape_by_name(slide43, "Running enrichment score curve")
    if len(curve.xpath(".//a:path/a:lnTo", namespaces=NS)) != 1133:
        raise RuntimeError("Slide 43 curve does not contain all ranked-gene steps")

    required_phrases = {
        43: ["+ |rᵢ| ÷ Σpathway |rⱼ|", "− 1 ÷ (N − Nₕ)", "ES = +0.9586"],
        44: ["NES = ESₒᵦₛ ÷ mean(|ESₙᵤₗₗ|)", "Adjusted P < 0.05"],
        45: ["+2.746 ≈ +2.75", "2.73 × 10⁻¹²", "not a fold change"],
    }
    for number, phrases in required_phrases.items():
        root = xml(parts[visible[number - 1]])
        text = " ".join(root.xpath(".//a:t/text()", namespaces=NS))
        for phrase in phrases:
            if phrase not in text:
                raise RuntimeError(f"Slide {number} lacks: {phrase}")

    for number in (42, 43, 44, 45):
        note_part = relationship_target(parts, visible[number - 1], "notesSlide")
        note_text = " ".join(
            xml(parts[note_part]).xpath(".//a:t/text()", namespaces=NS)
        )
        if "Teaching goal:" not in note_text or "Transition:" not in note_text:
            raise RuntimeError(f"Slide {number} notes validation failed")


def make_candidate(source: Path, candidate: Path) -> None:
    with ZipFile(source) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    visible = visible_slide_parts(parts)
    if len(visible) != 153:
        raise RuntimeError(f"Expected 153 source slides, found {len(visible)}")

    example = load_example()
    if example["n"] != 1134 or example["nh"] != 13:
        raise RuntimeError(f"Unexpected example sizes: {example['n']}, {example['nh']}")

    original_slide43_part = visible[42]
    original_slide43_xml = parts[original_slide43_part]
    original_slide43_rels = parts[rels_path(original_slide43_part)]
    original_notes43_part = relationship_target(parts, original_slide43_part, "notesSlide")
    original_notes43_xml = parts[original_notes43_part]
    original_notes43_rels = parts[rels_path(original_notes43_part)]

    # Clone the unmodified three-card layout before converting slide 43 to the figure slide.
    clone_source_parts = dict(parts)
    clone_source_parts[original_slide43_part] = original_slide43_xml
    clone_source_parts[rels_path(original_slide43_part)] = original_slide43_rels
    clone_source_parts[original_notes43_part] = original_notes43_xml
    clone_source_parts[rels_path(original_notes43_part)] = original_notes43_rels
    slide44_part = clone_slide(
        clone_source_parts, original_slide43_part, 154, SLIDE44_TEXT, NOTES44
    )
    slide45_part = clone_slide(
        clone_source_parts, original_slide43_part, 155, SLIDE45_TEXT, NOTES45
    )
    for part_name in (
        slide44_part,
        rels_path(slide44_part),
        "ppt/notesSlides/notesSlide154.xml",
        rels_path("ppt/notesSlides/notesSlide154.xml"),
        slide45_part,
        rels_path(slide45_part),
        "ppt/notesSlides/notesSlide155.xml",
        rels_path("ppt/notesSlides/notesSlide155.xml"),
    ):
        parts[part_name] = clone_source_parts[part_name]

    slide43 = copy.deepcopy(xml(original_slide43_xml))
    build_es_slide(slide43, example)
    parts[original_slide43_part] = xml_bytes(slide43)
    notes42_part = relationship_target(parts, visible[41], "notesSlide")
    notes42 = xml(parts[notes42_part])
    set_notes_body(notes42, NOTES42)
    parts[notes42_part] = xml_bytes(notes42)
    notes43 = xml(parts[original_notes43_part])
    set_notes_body(notes43, NOTES43)
    parts[original_notes43_part] = xml_bytes(notes43)

    slide40 = xml(parts[visible[39]])
    replace_shape_text(slide40, "TextBox 18", "ES and NES calculation")
    parts[visible[39]] = xml_bytes(slide40)

    update_package(parts, [slide44_part, slide45_part], insert_after_index=42)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkstemp(prefix="es_nes_", suffix=".pptx", dir=candidate.parent)[1]
    )
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temporary.replace(candidate)
    finally:
        if temporary.exists():
            temporary.unlink()


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
    args = parse_args()
    source = args.source.resolve()
    candidate = args.candidate.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    current_hash = sha256(source)
    if source == DECK.resolve() and current_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            "The deck changed after inspection. "
            f"Expected {EXPECTED_SOURCE_SHA256}, found {current_hash}."
        )
    lock = source.with_name(f"~${source.name}")
    if lock.exists():
        raise RuntimeError(f"PowerPoint lock file exists: {lock}")

    make_candidate(source, candidate)
    validate_candidate(candidate)

    print(f"source_sha256={current_hash}")
    print(f"candidate={candidate}")
    print(f"candidate_sha256={sha256(candidate)}")
    print("slides=155")

    if args.install:
        if sha256(source) != current_hash:
            raise RuntimeError("The source deck changed before installation")
        backup = next_backup_path(source)
        shutil.copy2(source, backup)
        shutil.copy2(candidate, source)
        print(f"backup={backup}")
        print(f"installed={source}")
        print(f"installed_sha256={sha256(source)}")


if __name__ == "__main__":
    main()
