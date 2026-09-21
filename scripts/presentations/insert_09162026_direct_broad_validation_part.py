#!/usr/bin/env python3
"""Insert a direct broad-cell validation section after visible slide 39."""

from __future__ import annotations

import copy
import hashlib
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx"
BUILD = ROOT / "tmp/presentations/direct_broad_validation_part"
CANDIDATE = BUILD / "09162026_sex_apoe_kda_fine_broad_direct_broad_validation.pptx"
EXPECTED_SOURCE_SHA256 = "953f6e4e1e3556b962cbb10cc1f0e029bd4d248382dc1185189b3884107a23d6"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PR_NS, "ct": CT_NS}


NEW_SLIDES = [
    {
        "source": 40,
        "texts": {
            "TextBox 1": "PART 6",
            "TextBox 3": "Direct broad-cell validation",
            "TextBox 4": (
                "A secondary analysis tests whether fine-cell findings persist when cells are "
                "combined into broad classes."
            ),
            "TextBox 6": "IN THIS PART",
            "TextBox 8": "1",
            "TextBox 9": "Analysis resolution",
            "TextBox 11": "2",
            "TextBox 12": "Broad-cell comparison",
            "TextBox 14": "3",
            "TextBox 15": "NES interpretation",
            "TextBox 17": "4",
            "TextBox 18": "Validation summary",
            "TextBox 20": (
                "Direct broad-cell analysis is supporting evidence; fine-cell analysis remains "
                "the primary resolution."
            ),
        },
        "notes": (
            "Teaching goal: Introduce direct broad-cell validation as a secondary analysis with a "
            "different biological resolution.\n"
            "Walk through: The primary findings test each fine cell type and then summarize results "
            "by broad class. Direct broad-cell analysis instead combines cells within a broad class "
            "before testing. This section explains the comparison, the ranked-gene pathway method, "
            "the normalized enrichment score, and the main validation conclusions.\n"
            "Scientific boundary: Direct broad-cell analysis is not a replacement for the fine-cell "
            "analysis. It cannot identify which fine cell type produces a broad-class signal.\n"
            "Transition: First, distinguish the two analysis resolutions."
        ),
    },
    {
        "source": 67,
        "texts": {
            "TextBox 1": "Fine-cell summaries and direct broad-cell analysis answer different questions",
            "TextBox 2": "The order of aggregation and testing changes the biological resolution.",
            "TextBox 4": "Fine-cell primary",
            "TextBox 6": "Direct broad secondary",
            "TextBox 8": "Same AD-versus-NCI contrast",
            "TextBox 10": "Different resolution",
            "TextBox 12": "FINE-CELL ANALYSIS",
            "TextBox 13": "Test each fine cell type",
            "TextBox 14": (
                "Run AD-versus-NCI DEG analysis separately within each fine cell type, sex, and APOE group. "
                "Summarize results later by broad class."
            ),
            "TextBox 16": "DIRECT BROAD-CELL ANALYSIS",
            "TextBox 17": "Combine cells before testing",
            "TextBox 18": (
                "Within each donor, combine cells belonging to one broad class, then compare AD with NCI "
                "within one sex/APOE group."
            ),
            "TextBox 20": "WHY BOTH ARE USEFUL",
            "TextBox 21": "Resolution check",
            "TextBox 22": (
                "Agreement strengthens a finding. Disagreement means that the result depends on cell resolution."
            ),
            "TextBox 24": (
                "Fine-cell analysis retains subtype localization. Direct broad-cell analysis retains donor-level "
                "structure but mixes fine cell types."
            ),
        },
        "notes": (
            "Teaching goal: Explain why the fine-cell and direct broad-cell analyses are related but not interchangeable.\n"
            "Walk through: In the primary workflow, AD-versus-NCI differential expression is tested separately "
            "for each fine cell type, sex, and APOE group. Those fine-cell results can later be summarized within a "
            "broad class. In the secondary workflow, cells from the same broad class are first combined within each "
            "donor, and one AD-versus-NCI comparison is made for that broad class and sex/APOE group.\n"
            "Scientific boundary: Direct broad-cell analysis preserves donor-level replication but mixes the fine "
            "cell types inside a broad class. Agreement supports robustness across resolutions; disagreement does not "
            "invalidate the fine-cell result, but it limits how broadly the result should be stated.\n"
            "Transition: Next, show how the direct broad-cell pathway analysis was performed."
        ),
    },
    {
        "source": 21,
        "texts": {
            "TextBox 2": "How direct broad-cell pathway validation was done",
            "TextBox 6": "1",
            "TextBox 7": "Combine cells by donor",
            "TextBox 8": "one broad class within each donor",
            "TextBox 10": "Pool cells from one broad class within each donor.",
            "TextBox 13": "2",
            "TextBox 14": "Compare AD with NCI",
            "TextBox 15": "sex/APOE group × broad class",
            "TextBox 17": "Run one differential-expression comparison for each group and broad cell class.",
            "TextBox 20": "3",
            "TextBox 21": "Rank the tested genes",
            "TextBox 22": "AD-down → AD-up",
            "TextBox 24": "Order genes from strongest AD-down to strongest AD-up evidence.",
            "TextBox 27": "4",
            "TextBox 28": "Test each pathway",
            "TextBox 29": "ranked-gene pathway analysis",
            "TextBox 31": "Ask whether pathway genes concentrate toward one end of the ranked list.",
        },
        "notes": (
            "Teaching goal: Explain the direct broad-cell pathway workflow before presenting its results.\n"
            "Walk through: For each donor, cells assigned to the same broad class were combined to create one donor-level "
            "expression profile. AD and NCI were compared separately within each sex/APOE group and broad cell class. "
            "All tested genes were then ranked from the strongest AD-down evidence to the strongest AD-up evidence. "
            "Gene set enrichment analysis, abbreviated GSEA, asks whether the genes in a pathway cluster near either "
            "end of that ranked list.\n"
            "Scientific boundary: This is a ranked-gene pathway analysis at broad-cell resolution. It is different from "
            "the fine-cell over-representation analysis based on DEG lists.\n"
            "Transition: The next slide defines the normalized enrichment score used to report the pathway direction."
        ),
    },
    {
        "source": 67,
        "texts": {
            "TextBox 1": "How to read the normalized enrichment score",
            "TextBox 2": "NES summarizes the pathway-level direction in ranked-gene analysis.",
            "TextBox 4": "Pathway-level",
            "TextBox 6": "Ranked genes",
            "TextBox 8": "Direction",
            "TextBox 10": "Significance",
            "TextBox 12": "NEGATIVE NES",
            "TextBox 13": "AD-down direction",
            "TextBox 14": (
                "Pathway genes tend to appear near the lower-expression-in-AD end of the ranked list."
            ),
            "TextBox 16": "NES NEAR ZERO",
            "TextBox 17": "No clear direction",
            "TextBox 18": "Pathway genes are not strongly concentrated at either end of the ranked list.",
            "TextBox 20": "POSITIVE NES",
            "TextBox 21": "AD-up direction",
            "TextBox 22": (
                "Pathway genes tend to appear near the higher-expression-in-AD end of the ranked list."
            ),
            "TextBox 24": (
                "Adjusted P < 0.05 defines a significant pathway result. NES is not a fold change or a count of DEGs, "
                "and it does not mean every pathway gene changed significantly."
            ),
        },
        "notes": (
            "Teaching goal: Define NES before it appears in any direct broad-cell result.\n"
            "Walk through: NES means normalized enrichment score. It summarizes whether genes in one pathway tend to "
            "occur near the AD-down or AD-up end of the ranked list while accounting for pathway size. A negative NES "
            "indicates an AD-down pathway direction, a positive NES indicates an AD-up pathway direction, and a value "
            "near zero indicates little concentration at either end. An adjusted P value below 0.05 defines a significant "
            "pathway result.\n"
            "Scientific boundary: NES is a pathway-level ranking statistic. It is not a gene-level fold change, a DEG "
            "count, or evidence that every gene in the pathway changed significantly.\n"
            "Transition: Use this definition to interpret which fine-cell findings are supported at broad-cell resolution."
        ),
    },
    {
        "source": 70,
        "texts": {
            "TextBox 1": "Direct broad-cell validation strengthens some findings and limits others",
            "TextBox 2": "Broad-cell results are secondary evidence because fine-cell analysis is the primary resolution.",
            "TextBox 4": "STRENGTHENS",
            "TextBox 5": "Female ε3/ε3 core MT increase",
            "TextBox 6": (
                "The excitatory-neuron AD-up result appears in ROSMAP and SEA-AD and survives the ROSMAP composition adjustment."
            ),
            "TextBox 8": "QUALIFIES",
            "TextBox 9": "Male ε3/ε3 mismatch",
            "TextBox 10": (
                "ROSMAP and SEA-AD agree before composition adjustment, but the ROSMAP broad-cell result loses significance after adjustment."
            ),
            "TextBox 12": "DISAGREES",
            "TextBox 13": "Female ε4 and male ε4",
            "TextBox 14": (
                "Female ε4 reverses direction at broad resolution. Male ε4 differs between ROSMAP and SEA-AD."
            ),
            "TextBox 16": "Coverage and interpretation",
            "TextBox 17": (
                "Female ε2 and male ε2 have incomplete SEA-AD broad-cell coverage. Agreement strengthens a claim; "
                "disagreement keeps it resolution-specific."
            ),
        },
        "notes": (
            "Teaching goal: Summarize what the direct broad-cell analysis adds before returning to sensitivity analyses.\n"
            "Walk through: The strongest broad-cell validation is the female epsilon-3 homozygous excitatory-neuron core "
            "MT AD-up result: ROSMAP NES 2.75 with adjusted P 2.73 × 10^-12, composition-adjusted ROSMAP NES 2.70 with "
            "adjusted P 1.86 × 10^-12, and SEA-AD NES 3.12 with adjusted P 1.94 × 10^-17. For male epsilon-3 homozygous "
            "inhibitory neurons, the core MT AD-up and nuclear-encoded OXPHOS AD-down pattern agrees across cohorts before "
            "composition adjustment, but the adjusted ROSMAP results are not significant. Female epsilon-4 reverses direction "
            "at broad resolution, and male epsilon-4 differs between cohorts. Female epsilon-2 and male epsilon-2 have "
            "incomplete SEA-AD broad-cell coverage.\n"
            "Scientific boundary: Across 112 pathway and category pairs tested in both cohorts, 60 have the same NES sign. "
            "Among 32 pairs significant in both cohorts, 23 agree in direction and 9 differ. Broad-cell evidence therefore "
            "strengthens selected findings but does not provide uniform validation.\n"
            "Transition: Part 7 examines additional sensitivity analyses."
        ),
    },
]


SLIDE15_NOTES = (
    "Teaching goal: Explain the two-stage pathway analysis and summarize how many pathways had at least one significant result.\n"
    "Walk through: Each estimable fine-cell sex/APOE contrast was analyzed separately. For each contrast, the analysis "
    "created three mitochondrial DEG lists: all DEGs, genes upregulated in AD, and genes downregulated in AD. It then "
    "tested each pathway using the enrichment and significance definition on the previous slide. Twelve of the 46 Level 1 "
    "and Level 2 pathways and 18 of the 149 complete pathways had at least one significant result across the tested contrasts "
    "and DEG lists. Most significant results involved overlapping OXPHOS pathways. Non-OXPHOS signals were fewer and more "
    "localized. The next slide defines a separate descriptive overlap percentage used to summarize four recurring pathway "
    "sets across sex/APOE groups.\n"
    "Scientific boundary: The complete 149-pathway collection contains the 46 Level 1 and Level 2 pathways, so the two "
    "reported scopes overlap. At least one significant result means enrichment in at least one fine-cell, sex/APOE, and DEG "
    "direction list. It does not mean significance in every group or prove altered pathway activity.\n"
    "Transition: Next, define the descriptive pathway-overlap percentage before reading the heatmap."
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def xml(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def rels_path(part: str) -> str:
    p = PurePosixPath(part)
    return str(p.parent / "_rels" / f"{p.name}.rels")


def resolve_part(base_part: str, target: str) -> str:
    base = PurePosixPath(base_part).parent
    pieces: list[str] = []
    for item in (base / target).parts:
        if item == "..":
            pieces.pop()
        elif item != ".":
            pieces.append(item)
    return "/".join(pieces)


def relationship_target(parts: dict[str, bytes], part: str, suffix: str) -> str:
    root = xml(parts[rels_path(part)])
    for rel in root.xpath("./pr:Relationship", namespaces=NS):
        if rel.get("Type", "").endswith(f"/{suffix}"):
            return resolve_part(part, rel.get("Target"))
    raise RuntimeError(f"No {suffix} relationship for {part}")


def set_shape_text(root: etree._Element, shape_name: str, value: str) -> None:
    found = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        names = shape.xpath("./p:nvSpPr/p:cNvPr/@name", namespaces=NS)
        if names and names[0] == shape_name:
            found.append(shape)
    if len(found) != 1:
        raise RuntimeError(f"Expected one shape named {shape_name!r}, found {len(found)}")
    text_nodes = found[0].xpath(".//a:t", namespaces=NS)
    if not text_nodes:
        raise RuntimeError(f"Shape {shape_name!r} has no text nodes")
    text_nodes[0].text = value
    for node in text_nodes[1:]:
        node.text = ""


def set_notes_body(root: etree._Element, value: str) -> None:
    body_shapes = []
    for shape in root.xpath(".//p:sp", namespaces=NS):
        placeholders = shape.xpath("./p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
        if placeholders and placeholders[0].get("type") == "body":
            body_shapes.append(shape)
    if len(body_shapes) != 1:
        raise RuntimeError(f"Expected one notes body placeholder, found {len(body_shapes)}")
    tx_body = body_shapes[0].find(f"{{{P_NS}}}txBody")
    if tx_body is None:
        raise RuntimeError("Notes body lacks txBody")
    for paragraph in list(tx_body.findall(f"{{{A_NS}}}p")):
        tx_body.remove(paragraph)
    for line in value.splitlines():
        paragraph = etree.SubElement(tx_body, f"{{{A_NS}}}p")
        run = etree.SubElement(paragraph, f"{{{A_NS}}}r")
        etree.SubElement(run, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
        text = etree.SubElement(run, f"{{{A_NS}}}t")
        text.text = line
        etree.SubElement(paragraph, f"{{{A_NS}}}endParaRPr", lang="en-US", dirty="0")


def visible_slide_parts(parts: dict[str, bytes]) -> list[str]:
    presentation = xml(parts["ppt/presentation.xml"])
    rels = xml(parts["ppt/_rels/presentation.xml.rels"])
    targets = {
        rel.get("Id"): rel.get("Target")
        for rel in rels.xpath("./pr:Relationship", namespaces=NS)
    }
    result = []
    for slide_id in presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS):
        rid = slide_id.get(f"{{{R_NS}}}id")
        result.append(resolve_part("ppt/presentation.xml", targets[rid]))
    return result


def next_relationship_id(rels_root: etree._Element) -> str:
    nums = []
    for rel in rels_root.xpath("./pr:Relationship", namespaces=NS):
        match = re.fullmatch(r"rId(\d+)", rel.get("Id", ""))
        if match:
            nums.append(int(match.group(1)))
    return f"rId{max(nums, default=0) + 1}"


def add_content_type_override(root: etree._Element, part_name: str, content_type: str) -> None:
    existing = root.xpath(f'./ct:Override[@PartName="{part_name}"]', namespaces=NS)
    if existing:
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
        set_shape_text(slide_root, name, value)

    slide_rels_root = copy.deepcopy(xml(parts[source_rels_part]))
    notes_root = copy.deepcopy(xml(parts[source_notes_part]))
    set_notes_body(notes_root, notes)
    notes_rels_root = copy.deepcopy(xml(parts[source_notes_rels_part]))

    new_slide_part = f"ppt/slides/slide{new_number}.xml"
    new_slide_rels_part = rels_path(new_slide_part)
    new_notes_part = f"ppt/notesSlides/notesSlide{new_number}.xml"
    new_notes_rels_part = rels_path(new_notes_part)

    for rel in slide_rels_root.xpath("./pr:Relationship", namespaces=NS):
        if rel.get("Type", "").endswith("/notesSlide"):
            rel.set("Target", f"../notesSlides/notesSlide{new_number}.xml")
    for rel in notes_rels_root.xpath("./pr:Relationship", namespaces=NS):
        if rel.get("Type", "").endswith("/slide"):
            rel.set("Target", f"../slides/slide{new_number}.xml")

    parts[new_slide_part] = xml_bytes(slide_root)
    parts[new_slide_rels_part] = xml_bytes(slide_rels_root)
    parts[new_notes_part] = xml_bytes(notes_root)
    parts[new_notes_rels_part] = xml_bytes(notes_rels_root)
    return new_slide_part


def update_existing(parts: dict[str, bytes], visible_parts: list[str]) -> None:
    slide15 = xml(parts[visible_parts[14]])
    set_shape_text(
        slide15,
        "TextBox 32",
        "Counts show whether each pathway had at least one significant result across the tested fine-cell contrasts and DEG lists.",
    )
    parts[visible_parts[14]] = xml_bytes(slide15)
    notes15_part = relationship_target(parts, visible_parts[14], "notesSlide")
    notes15 = xml(parts[notes15_part])
    set_notes_body(notes15, SLIDE15_NOTES)
    parts[notes15_part] = xml_bytes(notes15)

    slide40 = xml(parts[visible_parts[39]])
    set_shape_text(slide40, "TextBox 1", "PART 7")
    parts[visible_parts[39]] = xml_bytes(slide40)

    slide46 = xml(parts[visible_parts[45]])
    set_shape_text(slide46, "TextBox 1", "PART 8")
    parts[visible_parts[45]] = xml_bytes(slide46)
    notes46_part = relationship_target(parts, visible_parts[45], "notesSlide")
    notes46 = xml(parts[notes46_part])
    all_text = "\n".join(t.text or "" for t in notes46.xpath(".//a:t", namespaces=NS))
    all_text = all_text.replace("Part 7", "Part 8")
    set_notes_body(notes46, all_text)
    parts[notes46_part] = xml_bytes(notes46)


def update_package(parts: dict[str, bytes], new_slide_parts: list[str]) -> None:
    presentation = xml(parts["ppt/presentation.xml"])
    presentation_rels = xml(parts["ppt/_rels/presentation.xml.rels"])
    content_types = xml(parts["[Content_Types].xml"])

    slide_ids = presentation.xpath(".//p:sldIdLst/p:sldId", namespaces=NS)
    if len(slide_ids) != 149:
        raise RuntimeError(f"Expected 149 source slides, found {len(slide_ids)}")
    slide_id_list = slide_ids[0].getparent()
    insert_at = slide_id_list.index(slide_ids[38]) + 1
    next_slide_id = max(int(item.get("id")) for item in slide_ids) + 1

    for offset, slide_part in enumerate(new_slide_parts):
        rid = next_relationship_id(presentation_rels)
        etree.SubElement(
            presentation_rels,
            f"{{{PR_NS}}}Relationship",
            Id=rid,
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
            Target=f"slides/{PurePosixPath(slide_part).name}",
        )
        slide_id = etree.Element(f"{{{P_NS}}}sldId")
        slide_id.set("id", str(next_slide_id + offset))
        slide_id.set(f"{{{R_NS}}}id", rid)
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
        app_text, count = re.subn(r"(<Slides>)\d+(</Slides>)", r"\g<1>154\2", app_text, count=1)
        if count != 1:
            raise RuntimeError("Could not update slide count in docProps/app.xml")
        parts["docProps/app.xml"] = app_text.encode("utf-8")


def validate_candidate(path: Path) -> None:
    with ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    visible = visible_slide_parts(parts)
    if len(visible) != 154:
        raise RuntimeError(f"Expected 154 final slides, found {len(visible)}")

    expected = {
        15: "How the pathway analysis was done",
        40: "Direct broad-cell validation",
        41: "Fine-cell summaries and direct broad-cell analysis answer different questions",
        42: "How direct broad-cell pathway validation was done",
        43: "How to read the normalized enrichment score",
        44: "Direct broad-cell validation strengthens some findings and limits others",
        45: "Sensitivity analyses",
        51: "Findings and discussions",
    }
    for number, phrase in expected.items():
        root = xml(parts[visible[number - 1]])
        text = " ".join(t.text or "" for t in root.xpath(".//a:t", namespaces=NS))
        if phrase not in text:
            raise RuntimeError(f"Final slide {number} lacks expected text: {phrase}")

    slide15 = xml(parts[visible[14]])
    slide15_text = " ".join(t.text or "" for t in slide15.xpath(".//a:t", namespaces=NS))
    notes15_part = relationship_target(parts, visible[14], "notesSlide")
    notes15_text = " ".join(t.text or "" for t in xml(parts[notes15_part]).xpath(".//a:t", namespaces=NS))
    if "NES" in slide15_text or "normalized enrichment score" in notes15_text.lower():
        raise RuntimeError("NES remains on slide 15 or in its notes")

    for number in range(40, 45):
        notes_part = relationship_target(parts, visible[number - 1], "notesSlide")
        note_text = " ".join(t.text or "" for t in xml(parts[notes_part]).xpath(".//a:t", namespaces=NS))
        if "Teaching goal:" not in note_text:
            raise RuntimeError(f"New slide {number} lacks speaker notes")


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

    BUILD.mkdir(parents=True, exist_ok=True)
    with ZipFile(DECK) as archive:
        parts = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}

    visible = visible_slide_parts(parts)
    if len(visible) != 149:
        raise RuntimeError(f"Expected 149 source slides, found {len(visible)}")
    update_existing(parts, visible)

    existing_numbers = [
        int(match.group(1))
        for name in parts
        if (match := re.fullmatch(r"ppt/slides/slide(\d+)\.xml", name))
    ]
    next_number = max(existing_numbers) + 1
    new_slide_parts = []
    for offset, spec in enumerate(NEW_SLIDES):
        source_part = visible[spec["source"] - 1]
        new_slide_parts.append(
            clone_slide(
                parts,
                source_part,
                next_number + offset,
                spec["texts"],
                spec["notes"],
            )
        )

    update_package(parts, new_slide_parts)

    temp_path = Path(tempfile.mkstemp(prefix="direct_broad_", suffix=".pptx", dir=BUILD)[1])
    try:
        with ZipFile(temp_path, "w", ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        temp_path.replace(CANDIDATE)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    validate_candidate(CANDIDATE)

    if sha256(DECK) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("The source deck changed before installation")
    backups = sorted(DECK.parent.glob(f"{DECK.stem} bak*.pptx"))
    used = {
        int(match.group(1))
        for path in backups
        if (match := re.search(r" bak(\d+)\.pptx$", path.name))
    }
    backup_number = 1
    while backup_number in used:
        backup_number += 1
    backup = DECK.with_name(f"{DECK.stem} bak{backup_number}.pptx")
    shutil.copy2(DECK, backup)
    shutil.copy2(CANDIDATE, DECK)

    print(f"source_before_sha256={current_hash}")
    print(f"source_after_sha256={sha256(DECK)}")
    print(f"backup={backup}")
    print(f"candidate={CANDIDATE}")
    print("slides=154")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
