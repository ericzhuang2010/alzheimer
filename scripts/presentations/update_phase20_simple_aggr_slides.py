#!/usr/bin/env python3
"""Surgically replace slides 8–10 with simple-aggregation results.

The updater edits only the XML for slides 8, 9, and 10, their speaker-note
XML, and the two PNG media parts used exclusively by slides 8 and 9. All
other slide parts are copied byte-for-byte from the input presentation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import posixpath
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from lxml import etree
from PIL import Image
from pptx import Presentation


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECK = ROOT / "docs" / "presentations" / "phase20_sex_apoe_kda_fine_broad.pptx"
RESULT_DIR = ROOT / "results" / "minerva_production" / "20_sex_apoe_kda_simple_aggr"
FIGURE_DIR = ROOT / "results" / "figures" / "analysis" / "phase_20_sex_apoe_simple_aggr"
RECURRENCE_PNG = (
    FIGURE_DIR
    / "driver_recurrence"
    / "phase20_simple_aggr_driver_recurrence.png"
)
TOP5_PNG = FIGURE_DIR / "top5_candidates" / "phase20_simple_aggr_top5_candidates.png"
RECURRENCE_DATA = (
    FIGURE_DIR
    / "driver_recurrence"
    / "phase20_simple_aggr_driver_recurrence_plot_data.tsv"
)
TOP5_DATA = (
    FIGURE_DIR / "top5_candidates" / "phase20_simple_aggr_top5_candidates_plot_data.tsv"
)
CATEGORY_DATA = RESULT_DIR / "simple_category_gene_aggregates.tsv"
AUDIT_PATH = (
    ROOT
    / "results"
    / "presentations"
    / "phase20_sex_apoe_kda_fine_broad"
    / "phase20_simple_aggr_slide_update_checks.tsv"
)

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EMU_PER_INCH = 914400
TRUE_VALUES = {"TRUE", "T", "1", "YES"}

SLIDE_PARTS = {
    8: "ppt/slides/slide8.xml",
    9: "ppt/slides/slide9.xml",
    10: "ppt/slides/slide10.xml",
}
NOTES_PARTS = {
    8: "ppt/notesSlides/notesSlide8.xml",
    9: "ppt/notesSlides/notesSlide9.xml",
    10: "ppt/notesSlides/notesSlide10.xml",
}
MEDIA_PARTS = {
    8: "ppt/media/image1.png",
    9: "ppt/media/image2.png",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit", type=Path, default=AUDIT_PATH)
    return parser.parse_args()


def truth(value: Any) -> bool:
    return str(value).strip().upper() in TRUE_VALUES


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def parse_xml(data: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=False)
    return etree.fromstring(data, parser=parser)


def serialize_xml(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def shape_by_name(root: etree._Element, name: str) -> etree._Element:
    matches: list[etree._Element] = []
    for shape in root.xpath(".//p:sp | .//p:pic", namespaces=NS):
        properties = shape.xpath(
            "./p:nvSpPr/p:cNvPr | ./p:nvPicPr/p:cNvPr", namespaces=NS
        )
        if properties and properties[0].get("name") == name:
            matches.append(shape)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one shape named {name!r}, found {len(matches)}")
    return matches[0]


def set_shape_text(root: etree._Element, shape_name: str, value: str) -> None:
    shape = shape_by_name(root, shape_name)
    text_nodes = shape.xpath(".//a:t", namespaces=NS)
    if len(text_nodes) != 1:
        raise RuntimeError(
            f"Expected one text node in {shape_name!r}, found {len(text_nodes)}"
        )
    text_nodes[0].text = value


def set_picture(
    root: etree._Element,
    *,
    old_name: str,
    new_alt_text: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    picture = shape_by_name(root, old_name)
    properties = picture.xpath("./p:nvPicPr/p:cNvPr", namespaces=NS)[0]
    properties.set("name", new_alt_text)
    properties.set("descr", new_alt_text)
    blips = picture.xpath("./p:blipFill/a:blip", namespaces=NS)
    if len(blips) != 1 or blips[0].get(f"{{{NS['r']}}}embed") != "rId3":
        raise RuntimeError("Target picture no longer uses the expected rId3 relationship")
    offsets = picture.xpath("./p:spPr/a:xfrm/a:off", namespaces=NS)
    extents = picture.xpath("./p:spPr/a:xfrm/a:ext", namespaces=NS)
    if len(offsets) != 1 or len(extents) != 1:
        raise RuntimeError("Target picture has an unexpected transform")
    offsets[0].set("x", str(round(x * EMU_PER_INCH)))
    offsets[0].set("y", str(round(y * EMU_PER_INCH)))
    extents[0].set("cx", str(round(width * EMU_PER_INCH)))
    extents[0].set("cy", str(round(height * EMU_PER_INCH)))


def set_shape_width(root: etree._Element, shape_name: str, width: float) -> None:
    shape = shape_by_name(root, shape_name)
    extents = shape.xpath("./p:spPr/a:xfrm/a:ext", namespaces=NS)
    if len(extents) != 1:
        raise RuntimeError(f"Unexpected transform for {shape_name}")
    extents[0].set("cx", str(round(width * EMU_PER_INCH)))


def set_notes(root: etree._Element, paragraphs: Iterable[str]) -> None:
    bodies = root.xpath(
        './/p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]', namespaces=NS
    )
    if len(bodies) != 1:
        raise RuntimeError("Expected one notes body placeholder")
    nodes = bodies[0].xpath(".//a:t", namespaces=NS)
    values = list(paragraphs)
    if len(nodes) != len(values):
        raise RuntimeError(
            f"Expected {len(values)} notes text nodes, found {len(nodes)}"
        )
    for node, value in zip(nodes, values, strict=True):
        node.text = value


def picture_geometry(path: Path, *, max_width: float, max_height: float) -> tuple[float, float]:
    with Image.open(path) as image:
        image_width, image_height = image.size
    scale = min(max_width / image_width, max_height / image_height)
    return image_width * scale, image_height * scale


def validate_inputs() -> dict[str, Any]:
    required = [
        RECURRENCE_PNG,
        TOP5_PNG,
        RECURRENCE_DATA,
        TOP5_DATA,
        CATEGORY_DATA,
        FIGURE_DIR / "driver_recurrence" / "phase20_simple_aggr_driver_recurrence_status.tsv",
        FIGURE_DIR / "top5_candidates" / "phase20_simple_aggr_top5_candidates_status.tsv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing simple-aggregation source(s): " + ", ".join(missing))

    for figure_id in ("driver_recurrence", "top5_candidates"):
        status_path = (
            FIGURE_DIR
            / figure_id
            / f"phase20_simple_aggr_{figure_id}_status.tsv"
        )
        status = read_tsv(status_path)
        if (
            len(status) != 1
            or status[0]["validation_status"] != "validated_complete"
            or int(status[0]["failed_checks"]) != 0
            or status[0]["scope"] != "non_mt_driver"
        ):
            raise RuntimeError(f"Figure source is not validated: {status_path}")

    categories = read_tsv(CATEGORY_DATA)
    non_mt = [
        row
        for row in categories
        if row["case_id"] == "non_mt_driver" and not truth(row["is_core_mito"])
    ]
    recurrence = read_tsv(RECURRENCE_DATA)
    top5 = read_tsv(TOP5_DATA)
    group_counts = Counter(row["signature_group"] for row in non_mt)
    network_counts = Counter(row["broad_network"] for row in non_mt)
    category_keys = {(row["signature_group"], row["broad_network"]) for row in non_mt}
    values = {
        "non_mt_category_units": len(non_mt),
        "non_mt_unique_genes": len({row["current_symbol"] for row in non_mt}),
        "non_mt_returned_rows": sum(int(row["returned_call_count"]) for row in non_mt),
        "non_mt_categories": len(category_keys),
        "top5_rows": len(top5),
        "top5_unique_genes": len({row["current_symbol"] for row in top5}),
        "group_counts": group_counts,
        "network_counts": network_counts,
        "recurrence": recurrence,
        "top5": top5,
    }
    expected = {
        "non_mt_category_units": 689,
        "non_mt_unique_genes": 433,
        "non_mt_returned_rows": 1033,
        "non_mt_categories": 32,
        "top5_rows": 149,
        "top5_unique_genes": 105,
    }
    for key, expected_value in expected.items():
        if values[key] != expected_value:
            raise RuntimeError(f"Source count drift for {key}: {values[key]} != {expected_value}")
    if len(recurrence) != 20 or recurrence[0]["current_symbol"] != "RPS15":
        raise RuntimeError("Recurrence source does not match the validated top-20 contract")
    return values


def media_uses(archive: zipfile.ZipFile) -> dict[str, list[int]]:
    uses: dict[str, list[int]] = {}
    for slide_number in range(1, 23):
        rel_path = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
        root = parse_xml(archive.read(rel_path))
        for relationship in root.xpath("./pr:Relationship", namespaces=NS):
            if relationship.get("Type", "").endswith("/image"):
                target = posixpath.normpath(
                    posixpath.join("ppt/slides", relationship.get("Target", ""))
                )
                uses.setdefault(target, []).append(slide_number)
    return uses


def replace_slide_xml(
    slide8: bytes, slide9: bytes, slide10: bytes, facts: dict[str, Any]
) -> dict[int, bytes]:
    recurrence = facts["recurrence"]
    first = recurrence[0]
    second = recurrence[1]

    root8 = parse_xml(slide8)
    set_shape_text(root8, "TextBox 2", "RPS15 recurs across 12 returned-only categories")
    set_shape_text(
        root8,
        "TextBox 3",
        "Returned-only recurrence is descriptive across sex/APOE × broad-cell categories.",
    )
    set_shape_text(root8, "TextBox 10", "Bar length = number of categories containing the gene.")
    set_shape_text(
        root8,
        "TextBox 12",
        "Fill = categories whose score combines ≥2 returned calls.",
    )
    set_shape_text(
        root8,
        "TextBox 14",
        f"{first['current_symbol']}: {first['category_count']} categories, "
        f"{first['sex_apoe_group_count']} groups, {first['broad_network_count']} networks; "
        f"ACAT in {first['acat_combined_category_count']}.",
    )
    set_shape_text(
        root8,
        "TextBox 16",
        f"{second['current_symbol']}: {second['category_count']} categories, "
        f"{second['sex_apoe_group_count']} groups, {second['broad_network_count']} networks; "
        f"ACAT in {second['acat_combined_category_count']}.",
    )
    set_shape_text(
        root8,
        "TextBox 18",
        "Top 20 by category count, best exploratory score, then symbol.",
    )
    set_shape_text(
        root8,
        "TextBox 20",
        "Fill shows calculation route—not evidence strength.",
    )
    recurrence_width, recurrence_height = picture_geometry(
        RECURRENCE_PNG, max_width=6.30, max_height=5.18
    )
    set_picture(
        root8,
        old_name=(
            "Fine-cell Phase 20 horizontal bar chart of the twenty most recurrent "
            "relaxed non-MT key drivers across supported categories"
        ),
        new_alt_text=(
            "Simple returned-only Phase 20 bar chart of the twenty non-MT genes "
            "appearing in the most sex/APOE by broad-cell categories"
        ),
        x=0.47 + (7.16 - recurrence_width) / 2,
        y=1.37,
        width=recurrence_width,
        height=recurrence_height,
    )

    root9 = parse_xml(slide9)
    set_shape_text(
        root9,
        "TextBox 2",
        "Top-five display: 149 non-MT entries across 32 categories",
    )
    top5_width, top5_height = picture_geometry(
        TOP5_PNG, max_width=12.10, max_height=6.55
    )
    set_picture(
        root9,
        old_name=(
            "Fine-cell Phase 20 tile chart of up to five relaxed non-MT key drivers "
            "per supported sex/APOE and broad-cell category"
        ),
        new_alt_text=(
            "Simple returned-only Phase 20 female and male panels showing up to five "
            "non-MT genes per sex/APOE by broad-cell category"
        ),
        x=(13.333333 - top5_width) / 2,
        y=0.88,
        width=top5_width,
        height=top5_height,
    )

    root10 = parse_xml(slide10)
    title = (
        f"Simple output: {facts['non_mt_category_units']} non-MT category units "
        f"represent {facts['non_mt_unique_genes']} genes"
    )
    set_shape_text(root10, "TextBox 2", title)
    metric_values = [
        ("TextBox 5", f"{facts['non_mt_returned_rows']:,}"),
        ("TextBox 6", "non-MT returned call rows"),
        ("TextBox 8", f"{facts['non_mt_category_units']:,}"),
        ("TextBox 9", "non-MT gene × category units"),
        ("TextBox 11", f"{facts['non_mt_unique_genes']:,}"),
        ("TextBox 12", "distinct gene symbols"),
        ("TextBox 14", str(facts["non_mt_categories"])),
        ("TextBox 15", "categories with non-MT returns"),
        ("TextBox 17", str(facts["top5_rows"])),
        ("TextBox 18", "top-five displayed rows"),
    ]
    for shape_name, value in metric_values:
        set_shape_text(root10, shape_name, value)

    set_shape_text(root10, "TextBox 21", "Where non-MT driver units occur")
    group_counts: Counter[str] = facts["group_counts"]
    group_order = ["M_e2", "F_e4", "M_e4", "F_e2", "M_e33", "F_e33"]
    group_text = "  •  ".join(f"{group} {group_counts[group]}" for group in group_order)
    set_shape_text(root10, "TextBox 23", group_text)
    network_counts: Counter[str] = facts["network_counts"]
    network_text = (
        f"Excitatory {network_counts['Excitatory_neurons']} • "
        f"Inhibitory {network_counts['Inhibitory_neurons']} • "
        f"Astrocytes {network_counts['Astrocytes']} • OPCs {network_counts['OPCs']}\n"
        f"Oligo {network_counts['Oligodendrocytes']} • "
        f"Microglia {network_counts['Microglia']} • "
        f"Vasculature {network_counts['Vasculature_cells']}"
    )
    set_shape_text(root10, "TextBox 25", network_text)
    set_shape_text(root10, "TextBox 28", "Most recurrent returned-only genes")

    genes = recurrence[:6]
    gene_shapes = ["TextBox 29", "TextBox 32", "TextBox 35", "TextBox 38", "TextBox 41", "TextBox 44"]
    bar_shapes = ["Rectangle 30", "Rectangle 33", "Rectangle 36", "Rectangle 39", "Rectangle 42", "Rectangle 45"]
    count_shapes = ["TextBox 31", "TextBox 34", "TextBox 37", "TextBox 40", "TextBox 43", "TextBox 46"]
    maximum = max(int(row["category_count"]) for row in genes)
    for row, gene_shape, bar_shape, count_shape in zip(
        genes, gene_shapes, bar_shapes, count_shapes, strict=True
    ):
        count = int(row["category_count"])
        set_shape_text(root10, gene_shape, row["current_symbol"])
        set_shape_width(root10, bar_shape, 2.62 * count / maximum)
        set_shape_text(root10, count_shape, str(count))
    set_shape_text(
        root10,
        "TextBox 47",
        "Counts are category presence—not independent replication or call counts.",
    )
    return {8: serialize_xml(root8), 9: serialize_xml(root9), 10: serialize_xml(root10)}


def replace_notes(notes_data: dict[int, bytes]) -> dict[int, bytes]:
    replacements = {
        8: [
            "Teaching goal: Interpret returned-only category recurrence without confusing category breadth, call count, and score construction.",
            "Walk through: Bar length counts each sex/APOE by broad-cell category once. Fill counts the subset whose score combines at least two returned calls. RPS15 appears in 12 categories and RPL11 in 10; their total returned-call counts are 28 and 29, respectively.",
            "Scientific boundary: Inputs were preselected stock-significant within-call q values. Fill shows the calculation route, not evidence strength. Recurrence is descriptive, not an independent replication or FDR-controlled significance test.",
            "Transition: The next slide shows which non-MT genes rank in the top five within each populated category.",
        ],
        9: [
            "Teaching goal: Interpret the non-MT top-five display after excluding mitochondrial candidate drivers and recalculating display ranks.",
            "Walk through: The figure contains 149 tiles across 32 categories. Blue means ACAT across at least two returned calls; orange means a one-call within-run BH q passthrough. Color identifies the calculation route, not an evidence tier.",
            "Scientific boundary: Top five is a display cap, not a significance threshold. The returned-only score is post-selected and has no final across-gene BH adjustment; categories without a non-MT return are omitted.",
            "Transition: The summary slide translates the displayed results into returned-row, category-unit, distinct-gene, and recurrence counts.",
        ],
        10: [
            "Teaching goal: Summarize the scale and distribution of the simple returned-only non-MT result set.",
            "Walk through: The 1,033 non-MT returned call rows form 689 gene-by-category units representing 433 genes across 32 populated categories. The lower panels show where those units occur and the genes with the broadest category presence.",
            "Scientific boundary: These descriptive counts condition on stock-significant returns and differ across categories with unequal opportunities. They do not use nonreturns, coverage, support gates, or a final FDR-controlled cross-gene family.",
            "Transition: Part II now returns to the direct broad-cell branch, where each eligible direction remains a separate KDA result.",
        ],
    }
    output: dict[int, bytes] = {}
    for slide_number, data in notes_data.items():
        root = parse_xml(data)
        set_notes(root, replacements[slide_number])
        output[slide_number] = serialize_xml(root)
    return output


def member_hashes(archive: zipfile.ZipFile) -> dict[str, str]:
    return {name: sha256_bytes(archive.read(name)) for name in archive.namelist()}


def write_package(
    input_path: Path,
    output_path: Path,
    replacements: dict[str, bytes],
) -> tuple[dict[str, str], dict[str, str]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_path, "r") as source:
        before = member_hashes(source)
        unknown = sorted(set(replacements) - set(source.namelist()))
        if unknown:
            raise RuntimeError(f"Replacement package members are absent: {unknown}")
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
        )
        os.close(file_descriptor)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w") as destination:
                destination.comment = source.comment
                for info in source.infolist():
                    destination.writestr(
                        info,
                        replacements.get(info.filename, source.read(info.filename)),
                    )
            temporary.replace(output_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    with zipfile.ZipFile(output_path, "r") as result:
        if result.testzip() is not None:
            raise RuntimeError("Updated PPTX failed ZIP integrity validation")
        after = member_hashes(result)
    return before, after


def slide_text(xml_data: bytes) -> str:
    root = parse_xml(xml_data)
    return "\n".join(root.xpath(".//a:t/text()", namespaces=NS))


def write_audit(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check_id", "observed", "expected", "passed"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    facts = validate_inputs()

    original_deck_hash = sha256_file(input_path)
    with zipfile.ZipFile(input_path, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Input PPTX failed ZIP integrity validation")
        slide_names = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
        if len(slide_names) != 22:
            raise RuntimeError(f"Expected the edited 22-slide deck, found {len(slide_names)}")
        uses = media_uses(archive)
        if uses.get(MEDIA_PARTS[8]) != [8] or uses.get(MEDIA_PARTS[9]) != [9]:
            raise RuntimeError("Slides 8 and 9 no longer exclusively own image1.png/image2.png")
        slide_data = {number: archive.read(path) for number, path in SLIDE_PARTS.items()}
        notes_data = {number: archive.read(path) for number, path in NOTES_PARTS.items()}

    allowed_old_titles = {
        8: {
            "RPL11 recurs across 7 supported categories",
            "RPS15 recurs across 12 returned-only categories",
        },
        9: {
            "Top-five lists retain up to five candidates per category",
            "Top-five display: 149 non-MT entries across 32 categories",
        },
        10: {
            "Fine-cell output: 74 candidate units represent 37 distinct genes",
            "Simple output: 689 non-MT category units represent 433 genes",
        },
    }
    for number, titles in allowed_old_titles.items():
        if not any(title in slide_text(slide_data[number]) for title in titles):
            raise RuntimeError(f"Slide {number} does not match the expected pre-update contract")

    updated_slides = replace_slide_xml(
        slide_data[8], slide_data[9], slide_data[10], facts
    )
    updated_notes = replace_notes(notes_data)
    replacements = {
        SLIDE_PARTS[number]: data for number, data in updated_slides.items()
    }
    replacements.update(
        {NOTES_PARTS[number]: data for number, data in updated_notes.items()}
    )
    replacements[MEDIA_PARTS[8]] = RECURRENCE_PNG.read_bytes()
    replacements[MEDIA_PARTS[9]] = TOP5_PNG.read_bytes()

    before, after = write_package(input_path, output_path, replacements)
    changed = {name for name in before if before[name] != after[name]}
    allowed_changed = set(replacements)
    non_target_slide_changes = sorted(
        name
        for name in changed
        if name.startswith("ppt/slides/slide")
        and name.endswith(".xml")
        and name not in set(SLIDE_PARTS.values())
    )
    with zipfile.ZipFile(output_path, "r") as archive:
        output_slide_count = sum(
            name.startswith("ppt/slides/slide") and name.endswith(".xml")
            for name in archive.namelist()
        )
        output_titles = {
            number: slide_text(archive.read(part))
            for number, part in SLIDE_PARTS.items()
        }
        image1_hash = sha256_bytes(archive.read(MEDIA_PARTS[8]))
        image2_hash = sha256_bytes(archive.read(MEDIA_PARTS[9]))
    presentation = Presentation(str(output_path))
    python_pptx_slide_count = len(presentation.slides)

    checks = [
        {
            "check_id": "slide_count",
            "observed": output_slide_count,
            "expected": 22,
            "passed": output_slide_count == 22,
        },
        {
            "check_id": "changed_members_within_authorized_scope",
            "observed": "|".join(sorted(changed)),
            "expected": "slides 8-10, their notes, and image1/image2 only",
            "passed": changed <= allowed_changed,
        },
        {
            "check_id": "non_target_slide_xml_unchanged",
            "observed": len(non_target_slide_changes),
            "expected": 0,
            "passed": not non_target_slide_changes,
        },
        {
            "check_id": "slide8_title",
            "observed": "RPS15 recurs across 12 returned-only categories"
            in output_titles[8],
            "expected": True,
            "passed": "RPS15 recurs across 12 returned-only categories"
            in output_titles[8],
        },
        {
            "check_id": "slide9_title",
            "observed": "Top-five display: 149 non-MT entries across 32 categories"
            in output_titles[9],
            "expected": True,
            "passed": "Top-five display: 149 non-MT entries across 32 categories"
            in output_titles[9],
        },
        {
            "check_id": "slide10_title",
            "observed": "Simple output: 689 non-MT category units represent 433 genes"
            in output_titles[10],
            "expected": True,
            "passed": "Simple output: 689 non-MT category units represent 433 genes"
            in output_titles[10],
        },
        {
            "check_id": "slide8_png_byte_exact",
            "observed": image1_hash,
            "expected": sha256_file(RECURRENCE_PNG),
            "passed": image1_hash == sha256_file(RECURRENCE_PNG),
        },
        {
            "check_id": "slide9_png_byte_exact",
            "observed": image2_hash,
            "expected": sha256_file(TOP5_PNG),
            "passed": image2_hash == sha256_file(TOP5_PNG),
        },
        {
            "check_id": "pptx_loads_with_python_pptx",
            "observed": python_pptx_slide_count,
            "expected": 22,
            "passed": python_pptx_slide_count == 22,
        },
    ]
    write_audit(args.audit.resolve(), checks)
    failed = [row["check_id"] for row in checks if not row["passed"]]
    if failed:
        raise RuntimeError("Slide update failed checks: " + ", ".join(failed))
    print(f"updated={output_path}")
    print("slides_replaced=8,9,10")
    print(f"other_slide_xml_changed={len(non_target_slide_changes)}")
    print(f"original_sha256={original_deck_hash}")
    print(f"updated_sha256={sha256_file(output_path)}")
    print(f"audit={args.audit.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
