#!/usr/bin/env python3
"""Refresh the direct broad-cell section outline and its speaker notes."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT
    / "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx"
)
DEFAULT_OUTPUT = (
    ROOT
    / "tmp/presentations/slides40_44_notes/candidate.pptx"
)

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS}


NOTES_BY_SLIDE = {
    39: (
        "Teaching goal: Show whether SEA-AD excitatory-neuron genes returned from KDA calls recur across the six sex/APOE categories.\n"
        "Walk through: Rows are the three female groups followed by the three male groups. Columns contain all 27 distinct "
        "non-MitoCarta genes returned from KDA calls in the excitatory-neuron broad cell type. A colored tile means that the "
        "gene appears in that category. Its color gives the total number of categories containing that gene. No gene appears "
        "in more than one sex/APOE category.\n"
        "Scientific boundary: Category recurrence is a descriptive summary of returned KDA results. It is not an effect size, "
        "an independent replication count, or a sex-by-APOE interaction test.\n"
        "Transition: Move to Part 6, which tests selected findings at direct broad-cell resolution."
    ),
    40: (
        "Teaching goal: Introduce direct broad-cell validation and establish that both analysis resolutions use donors as the biological replicates.\n"
        "Walk through: Both workflows first combine RNA counts within each donor. The primary workflow creates one expression "
        "profile for each donor and fine cell type, then runs the AD-versus-NCI comparison separately for every fine cell type. "
        "The direct broad-cell workflow combines the contributing fine cell types within each donor before running one comparison "
        "for the broad cell class. This section explains that resolution difference, the ranked-gene pathway workflow, and the "
        "normalized enrichment score.\n"
        "Scientific boundary: Direct broad-cell analysis provides supporting evidence. Combining fine cell types can hide a "
        "subtype-specific result or create sensitivity to differences in fine-cell composition.\n"
        "Transition: Compare the fine-cell and direct broad-cell workflows side by side."
    ),
    41: (
        "Teaching goal: Distinguish the two workflows without implying that donor-level aggregation is unique to direct broad-cell analysis.\n"
        "Walk through: Fine-cell analysis produces one donor-level expression profile for each fine cell type. It tests each fine "
        "cell type separately and summarizes the resulting evidence by broad class afterward. Direct broad-cell analysis instead "
        "produces one donor-level profile for the whole broad class by combining its fine cell types before differential-expression "
        "testing. Both workflows therefore compare donors. They differ in the cell-type resolution retained before the comparison.\n"
        "Scientific boundary: Agreement supports a result across two resolutions. Disagreement can reflect fine-cell composition "
        "or opposing subtype-specific effects and does not by itself invalidate the fine-cell result.\n"
        "Transition: Follow the direct broad-cell pathway workflow from donor-level expression profiles to pathway testing."
    ),
    42: (
        "Teaching goal: Explain the direct broad-cell pathway workflow.\n"
        "Walk through: For each donor and broad cell class, the analysis combines counts from the contributing fine cell types into "
        "one expression profile. It then compares AD with NCI separately within each sex/APOE group and broad cell class. All tested "
        "genes are ordered from stronger AD-down evidence to stronger AD-up evidence. Gene set enrichment analysis, abbreviated "
        "GSEA, tests whether the genes in a pathway cluster toward either end of this ranked list.\n"
        "Scientific boundary: This ranked-gene pathway analysis uses all tested genes at direct broad-cell resolution. The fine-cell "
        "pathway analysis instead tests whether a thresholded DEG list contains more pathway genes than expected.\n"
        "Transition: Define the normalized enrichment score used to report the broad-cell pathway direction."
    ),
    43: (
        "Teaching goal: Define the normalized enrichment score before later findings use direct broad-cell pathway results.\n"
        "Walk through: NES means normalized enrichment score. It summarizes where the genes in one pathway occur in the ranked "
        "gene list while accounting for pathway size. A negative NES indicates an AD-down pathway direction. A positive NES "
        "indicates an AD-up pathway direction. A value near zero indicates no strong concentration at either end. An adjusted P "
        "value below 0.05 defines a significant pathway result.\n"
        "Scientific boundary: NES is a pathway-level ranking statistic. It is not a gene-level fold change or a DEG count, and it "
        "does not mean that every gene in the pathway changed significantly.\n"
        "Transition: Move to Part 7, the sensitivity analyses."
    ),
    44: (
        "Teaching goal: Introduce Part 7, which tests how selected analysis decisions affect the KDA results.\n"
        "Walk through: The sensitivity analyses examine donor support, the number of nuclei contributing to each profile, the DEG "
        "query definition, and the KDA decision rules. Each check changes one decision while keeping the rest of the workflow fixed. "
        "The first comparison raises the minimum donor requirement in each disease-status group from three to five.\n"
        "Scientific boundary: These analyses evaluate robustness to prespecified workflow decisions. The donor-threshold analysis "
        "concerns donors in each disease-status group, not the number of nuclei contributing to a donor-level profile.\n"
        "Transition: Begin with the numerical consequences of changing the donor threshold."
    ),
}

EXPECTED_TEXT = {
    39: "SEA-AD excitatory neurons: genes returned from KDA calls",
    40: "Direct broad-cell validation",
    41: "Fine-cell summaries and direct broad-cell analysis answer different questions",
    42: "How direct broad-cell pathway validation was done",
    43: "How to read the normalized enrichment score",
    44: "Sensitivity analyses",
}

SLIDE_TEXT_UPDATES = {
    40: {
        "TextBox 15": "Pathway workflow",
        "TextBox 18": "NES interpretation",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


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
        rel.get("Id"): rel.get("Target")
        for rel in relationships.xpath("./pr:Relationship", namespaces=NS)
    }
    result = []
    for slide_id in presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS):
        relationship_id = slide_id.get(f"{{{R_NS}}}id")
        result.append(resolve_part("ppt/presentation.xml", targets[relationship_id]))
    return result


def notes_part(parts: dict[str, bytes], slide_part: str) -> str:
    relationships = xml(parts[rels_path(slide_part)])
    for relationship in relationships.xpath("./pr:Relationship", namespaces=NS):
        if relationship.get("Type", "").endswith("/notesSlide"):
            return resolve_part(slide_part, relationship.get("Target"))
    raise RuntimeError(f"No notes relationship for {slide_part}")


def set_notes_body(root: etree._Element, value: str) -> None:
    bodies = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        placeholders = shape.xpath("./p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
        if placeholders and placeholders[0].get("type") == "body":
            bodies.append(shape)
    if len(bodies) != 1:
        raise RuntimeError(f"Expected one notes body, found {len(bodies)}")
    text_body = bodies[0].find(f"{{{P_NS}}}txBody")
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


def set_shape_text(root: etree._Element, shape_name: str, value: str) -> None:
    matches = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        names = shape.xpath("./p:nvSpPr/p:cNvPr/@name", namespaces=NS)
        if names and names[0] == shape_name:
            matches.append(shape)
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one shape named {shape_name!r}, found {len(matches)}"
        )
    text_nodes = matches[0].xpath(".//a:t", namespaces=NS)
    if not text_nodes:
        raise RuntimeError(f"Shape {shape_name!r} has no text nodes")
    text_nodes[0].text = value
    for node in text_nodes[1:]:
        node.text = ""


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if source == output:
        raise RuntimeError("Use a separate output file; do not overwrite the source directly")
    if not source.exists():
        raise FileNotFoundError(source)

    with ZipFile(source) as archive:
        parts = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    slides = visible_slide_parts(parts)
    if len(slides) != 153:
        raise RuntimeError(f"Expected 153 slides, found {len(slides)}")

    original_slide_xml = {number: parts[slides[number - 1]] for number in NOTES_BY_SLIDE}
    for number, expected in EXPECTED_TEXT.items():
        slide_root = xml(parts[slides[number - 1]])
        visible_text = " ".join(
            node.text or "" for node in slide_root.xpath(".//a:t", namespaces=NS)
        )
        if expected not in visible_text:
            raise RuntimeError(f"Slide {number} does not contain expected text: {expected}")

    for number, notes in NOTES_BY_SLIDE.items():
        part = notes_part(parts, slides[number - 1])
        root = copy.deepcopy(xml(parts[part]))
        set_notes_body(root, notes)
        parts[part] = xml_bytes(root)

    for number, updates in SLIDE_TEXT_UPDATES.items():
        part = slides[number - 1]
        root = copy.deepcopy(xml(parts[part]))
        for shape_name, value in updates.items():
            set_shape_text(root, shape_name, value)
        parts[part] = xml_bytes(root)

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)

    with ZipFile(output) as archive:
        candidate = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    candidate_slides = visible_slide_parts(candidate)
    if len(candidate_slides) != 153:
        raise RuntimeError("Candidate slide count changed")
    for number, original in original_slide_xml.items():
        if number not in SLIDE_TEXT_UPDATES and candidate[candidate_slides[number - 1]] != original:
            raise RuntimeError(f"Visible XML changed on slide {number}")
        part = notes_part(candidate, candidate_slides[number - 1])
        notes_text = " ".join(
            node.text or "" for node in xml(candidate[part]).xpath(".//a:t", namespaces=NS)
        )
        if "Teaching goal:" not in notes_text or "Transition:" not in notes_text:
            raise RuntimeError(f"Notes validation failed on slide {number}")

    slide40_text = " ".join(
        node.text or ""
        for node in xml(candidate[candidate_slides[39]]).xpath(".//a:t", namespaces=NS)
    )
    for expected in ("Pathway workflow", "NES interpretation"):
        if expected not in slide40_text:
            raise RuntimeError(f"Slide 40 lacks updated section item: {expected}")
    if "Validation summary" in slide40_text:
        raise RuntimeError("Slide 40 still contains the deleted validation-summary item")

    print(f"output={output}")
    print("updated_notes=39,40,41,42,43,44")
    print("updated_visible_slide=40")


if __name__ == "__main__":
    main()
