#!/usr/bin/env python3
"""Update the GSE143758 assessment DOCX with the cortex/PFC fit boundary.

The edit is deliberately surgical: it changes text in existing paragraphs and
table cells while retaining the package structure, styles, image, hyperlinks,
headers, and footer. Publication is atomic and guarded by the approved source
hash or by an idempotent already-updated contract.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile


REPO = Path(__file__).resolve().parents[2]
DEFAULT_DOCX = REPO / "docs/validation_mouse/GSE143758_dataset_does_not_work.docx"
ORIGINAL_SHA256 = "7b3509535985ac1ae5fb258f938f02a9717443972c2ff282520907dbbda6583c"
INTERMEDIATE_SHA256 = "d01c33d62c2af9ed4f965cc7db63dfe8e94a3add3ebb3790da6874858acfd1eb"
FINAL_SHA256 = "5bfdc1563178dba3aa33cb54e1b325728189890ffef02afc8350041311c6934d"
IMAGE_SHA256 = "9d0a24e0c437c21b77ddc1de0cccab62a2dc69cc3e95e8b7dfa2c30205944707"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DC = "{http://purl.org/dc/elements/1.1/}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
XML_DECL = b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_namespaces(xml: bytes) -> None:
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(xml), events=("start-ns",)):
        if prefix == "xml":
            continue
        try:
            ET.register_namespace(prefix or "", uri)
        except ValueError:
            # ElementTree reserves generated ns* prefixes; Word does not rely
            # on a particular prefix spelling for those namespaces.
            continue


def parse_xml(xml: bytes) -> ET.Element:
    register_namespaces(xml)
    return ET.fromstring(xml)


def serialize_xml(root: ET.Element) -> bytes:
    return XML_DECL + ET.tostring(root, encoding="utf-8")


def visible_text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.iter(f"{W}t"))


def set_paragraph_text(paragraph: ET.Element, value: str) -> None:
    text_nodes = list(paragraph.iter(f"{W}t"))
    if not text_nodes:
        raise AssertionError("Target paragraph has no Word text nodes")
    text_nodes[0].text = value
    for node in text_nodes[1:]:
        node.text = ""


def find_paragraph(root: ET.Element, expected: str) -> ET.Element:
    matches = [
        paragraph
        for paragraph in root.iter(f"{W}p")
        if visible_text(paragraph) == expected
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one paragraph matching {expected!r}; found {len(matches)}"
        )
    return matches[0]


def row_cells(row: ET.Element) -> list[ET.Element]:
    return row.findall(f"./{W}tc")


def row_values(row: ET.Element) -> tuple[str, ...]:
    return tuple(visible_text(cell) for cell in row_cells(row))


def find_row(root: ET.Element, expected: tuple[str, ...]) -> ET.Element:
    matches = [row for row in root.iter(f"{W}tr") if row_values(row) == expected]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one table row matching {expected!r}; found {len(matches)}"
        )
    return matches[0]


def set_cell_text(cell: ET.Element, value: str) -> None:
    paragraphs = cell.findall(f"./{W}p")
    if len(paragraphs) != 1:
        raise AssertionError(
            f"Expected a one-paragraph cell, found {len(paragraphs)} paragraphs"
        )
    set_paragraph_text(paragraphs[0], value)


def update_document_xml(xml: bytes) -> bytes:
    root = parse_xml(xml)

    paragraph_replacements = {
        "Dataset design, sample counts, biological findings, and appropriate use":
            "Dataset design, regional fit, sample counts, and appropriate use",
        "A clear guide to why GEO lists 37 samples while the main comparison contains 8 independent mice":
            "Why a primarily hippocampal study cannot provide broad PFC APOE-by-sex validation",
        "Use GSE143758 as a disease and cell-state validation dataset, not as the APOE or sex dataset.":
            "Use GSE143758 as an auxiliary disease and cell-state reference, not as a region-matched PFC, APOE, or sex-validation dataset.",
        '"We used GSE143758 as an independent mouse 5xFAD-versus-WT snRNA-seq reference to assess disease-direction and cell-type concordance. Because the study lacks human APOE isoform groups and contains only one female mouse per disease condition, it was not used to estimate APOE or sex interactions."':
            '“We used GSE143758 as an auxiliary mouse reference for 5xFAD disease direction and cross-region cell-state concordance. Because its broad cell-type data are hippocampal, its cortex/PFC subset is small and astrocyte-only, human APOE isoform groups are absent, and female replication is insufficient, we did not use it for direct PFC, APOE, or sex-interaction validation.”',
        "GSE143758 is scientifically valuable, but the correct sample size depends on the question. The entire GEO series has 37 sample records. The main seven-month disease comparison has 8 independent mice and 10 sample/library preparations. Its tens of thousands of nuclei provide detailed cell-level measurements, not tens of thousands of independent biological replicates. For your broader Alzheimer validation project, use GSE143758 for 5xFAD disease effects, cell-type localization, astrocyte states, and age progression; use separate APOE- and sex-appropriate datasets for those factors.":
            "GSE143758 is scientifically valuable, but the correct sample size depends on the question. The entire GEO series has 37 sample records. The main seven-month disease comparison has 8 independent mice and 10 sample/library preparations. Its tens of thousands of nuclei provide detailed cell-level measurements, not tens of thousands of independent biological replicates. For a human PFC validation project, use GSE143758 only as auxiliary 5xFAD disease, astrocyte-state, age, or cross-region support; use separate cortex/PFC-, APOE-, and sex-appropriate datasets for the primary validation questions.",
    }
    for old, new in paragraph_replacements.items():
        set_paragraph_text(find_paragraph(root, old), new)

    bottom_line_tables = []
    for table in root.iter(f"{W}tbl"):
        cells = list(table.iter(f"{W}tc"))
        if not cells:
            continue
        paragraphs = cells[0].findall(f"./{W}p")
        if paragraphs and visible_text(paragraphs[0]) == "Bottom line":
            bottom_line_tables.append((table, cells[0], paragraphs))
    if len(bottom_line_tables) != 1:
        raise AssertionError(
            f"Expected one Bottom line callout; found {len(bottom_line_tables)}"
        )
    _, _, paragraphs = bottom_line_tables[0]
    if len(paragraphs) != 2:
        raise AssertionError("Bottom line callout structure changed")
    expected_bottom = (
        "GSE143758 is a valuable 5xFAD-versus-WT mouse-brain snRNA-seq "
        "resource, especially for disease-associated astrocytes, age progression, "
        "and broad cell-type localization at seven months. It is not a human "
        "APOE3-versus-APOE4 dataset, and its female sample size is far too small "
        "for a reliable sex comparison."
    )
    if visible_text(paragraphs[1]) != expected_bottom:
        raise AssertionError("Bottom line body changed before the regional update")
    set_paragraph_text(
        paragraphs[1],
        "GSE143758 is a valuable 5xFAD-versus-WT snRNA-seq resource, but it is "
        "not a suitable primary dataset for a human prefrontal-cortex (PFC) "
        "APOE-by-sex validation study. Its broad all-cell atlas and age-course "
        "data are hippocampal. The only cortex/PFC component is an astrocyte-focused "
        "subset of four male mice across two ages—one WT and one 5xFAD mouse per "
        "age—and those mice also contributed hippocampus. The study also lacks "
        "human APOE isoform groups and has only one reported female mouse per genotype.",
    )

    primary_row = find_row(
        root,
        (
            "Primary tissue",
            "Hippocampus; smaller validation components also include prefrontal cortex",
        ),
    )
    set_cell_text(
        row_cells(primary_row)[1],
        "Main all-cell atlas and age course: hippocampus. A smaller astrocyte-only "
        "cortex/PFC subset contains four male mice across 7 and 10 months.",
    )

    fit_row = find_row(
        root,
        (
            "Multiple brain cell types",
            "Yes at 7 months",
            "The all-nuclei atlas includes neurons, glia, and vascular/stromal populations.",
        ),
    )
    for cell, value in zip(
        row_cells(fit_row),
        (
            "Region-matched broad cell types",
            "No",
            "Broad cell-type coverage is available in hippocampus, not PFC; the "
            "cortex/PFC subset is astrocyte-only.",
        ),
    ):
        set_cell_text(cell, value)

    component_row = find_row(
        root,
        (
            "Cortex validation",
            "Male prefrontal cortex at seven and ten months",
            "Cortex specimens from mice also used for hippocampus",
            "Tests whether the astrocyte state is restricted to hippocampus.",
        ),
    )
    component_values = (
        "Cortex validation",
        "Male cortex/PFC at 7 and 10 months (PFC per paper)",
        "4 mice total: 1 WT + 1 5xFAD per age; the same mice also contributed hippocampus",
        "Descriptive cross-region astrocyte-state check; not independent or all-cell PFC validation",
    )
    for cell, value in zip(row_cells(component_row), component_values):
        set_cell_text(cell, value)

    answer_row = find_row(
        root,
        (
            "Does the signal occur in both hippocampus and cortex?",
            "Descriptive validation",
            "The cortex component is useful, but some regions come from the same "
            "mice and should not be counted as independent animals.",
        ),
    )
    answer_values = (
        "Does an astrocyte signal occur in both hippocampus and cortex/PFC?",
        "Descriptive only",
        "The cortex/PFC subset has one mouse per genotype at each age and reuses "
        "hippocampus-profiled mice; it is neither an independent cohort nor a broad-cell comparison.",
    )
    for cell, value in zip(row_cells(answer_row), answer_values):
        set_cell_text(cell, value)

    return serialize_xml(root)


def update_section_headings(xml: bytes) -> bytes:
    root = parse_xml(xml)
    replacements = {
        "2. How well does it match the APOE-by-sex validation goal?":
            "2. How well does it match the APOE-by-sex and cortex/PFC validation goal?",
        "12. Practical recommendation for an APOE-and-sex Alzheimer project":
            "12. Practical recommendation for an APOE, sex, and cortex/PFC Alzheimer project",
    }
    for old, new in replacements.items():
        set_paragraph_text(find_paragraph(root, old), new)
    return serialize_xml(root)


def update_core_xml(xml: bytes) -> bytes:
    root = parse_xml(xml)
    subject = root.find(f"{DC}subject")
    keywords = root.find(f"{CP}keywords")
    description = root.find(f"{DC}description")
    if subject is None or keywords is None or description is None:
        raise AssertionError("DOCX core properties are incomplete")
    if subject.text != "Dataset design, sample counts, biological findings, and appropriate use":
        raise AssertionError("DOCX core subject changed before regional update")
    subject.text = "Dataset design, regional fit, sample counts, biological findings, and appropriate use"
    keywords.text = (
        "GSE143758, 5xFAD, snRNA-seq, Alzheimer disease, astrocytes, GEO, "
        "sample size, hippocampus, prefrontal cortex, PFC"
    )
    description.text = "Prepared as a standalone research guide with regional-fit assessment."
    return serialize_xml(root)


NEW_REQUIRED = (
    "Why a primarily hippocampal study cannot provide broad PFC APOE-by-sex validation",
    "not a suitable primary dataset for a human prefrontal-cortex (PFC) APOE-by-sex validation study",
    "Region-matched broad cell types",
    "cortex/PFC subset is astrocyte-only",
    "4 mice total: 1 WT + 1 5xFAD per age",
    "Descriptive cross-region astrocyte-state check",
    "not as a region-matched PFC, APOE, or sex-validation dataset",
    "direct PFC, APOE, or sex-interaction validation",
    "use separate cortex/PFC-, APOE-, and sex-appropriate datasets",
    "APOE-by-sex and cortex/PFC validation goal",
    "APOE, sex, and cortex/PFC Alzheimer project",
)


def validate_updated_package(path: Path, baseline: dict[str, bytes] | None = None) -> None:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise AssertionError("DOCX ZIP integrity check failed")
        names = archive.namelist()
        parts = {name: archive.read(name) for name in names}
    if len(names) != 20:
        raise AssertionError(f"Expected 20 DOCX parts, found {len(names)}")
    if "word/document.xml" not in parts or "docProps/core.xml" not in parts:
        raise AssertionError("DOCX is missing required XML parts")
    if "word/media/image1.png" not in parts:
        raise AssertionError("DOCX embedded hierarchy image is missing")
    if sha256_bytes(parts["word/media/image1.png"]) != IMAGE_SHA256:
        raise AssertionError("DOCX embedded image changed")

    root = parse_xml(parts["word/document.xml"])
    body = root.find(f"{W}body")
    if body is None:
        raise AssertionError("DOCX document body is missing")
    direct_paragraphs = body.findall(f"./{W}p")
    direct_tables = body.findall(f"./{W}tbl")
    if len(body) != 103 or len(direct_paragraphs) != 87 or len(direct_tables) != 15:
        raise AssertionError(
            "DOCX top-level paragraph/table structure changed unexpectedly"
        )
    text = " ".join(" ".join(visible_text(body).split()).split())
    for phrase in NEW_REQUIRED:
        if phrase.lower() not in text.lower():
            raise AssertionError(f"Updated DOCX is missing required phrase: {phrase}")

    if baseline is not None:
        if set(parts) != set(baseline):
            raise AssertionError("DOCX package member set changed")
        allowed = {"word/document.xml", "docProps/core.xml"}
        for name in parts:
            if name not in allowed and parts[name] != baseline[name]:
                raise AssertionError(f"Unexpected DOCX package change: {name}")


def update_docx(path: Path) -> str:
    path = path.resolve()
    current_hash = sha256(path)
    if current_hash == FINAL_SHA256:
        validate_updated_package(path)
        print(f"Already updated and validated: {path}")
        return current_hash
    if current_hash not in {ORIGINAL_SHA256, INTERMEDIATE_SHA256}:
        raise AssertionError(
            "DOCX does not match the approved original, intermediate, or final revision"
        )

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        baseline = {info.filename: archive.read(info.filename) for info in infos}
    updated = dict(baseline)
    if current_hash == ORIGINAL_SHA256:
        document_xml = update_document_xml(baseline["word/document.xml"])
        updated["docProps/core.xml"] = update_core_xml(baseline["docProps/core.xml"])
    else:
        document_xml = baseline["word/document.xml"]
    updated["word/document.xml"] = update_section_headings(document_xml)

    with tempfile.NamedTemporaryFile(
        prefix=f".{path.stem}.", suffix=".tmp.docx", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for info in infos:
                archive.writestr(info, updated[info.filename])
        validate_updated_package(temporary, baseline=baseline)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    validate_updated_package(path, baseline=baseline)
    result = sha256(path)
    if result != FINAL_SHA256:
        raise AssertionError(
            f"Updated DOCX hash changed: expected {FINAL_SHA256}, observed {result}"
        )
    print(f"Updated and validated: {path}")
    print(f"SHA-256: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_updated_package(args.docx.resolve())
        print(f"Validated: {args.docx.resolve()}")
    else:
        update_docx(args.docx)


if __name__ == "__main__":
    main()
