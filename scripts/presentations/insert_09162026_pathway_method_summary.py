#!/usr/bin/env python3
"""Insert a pathway-analysis method and coverage summary after slide 5.

The reviewed deck already contains two focused pathway slides. This updater
adds one bridge slide before them, refreshes their terminology from "program"
to "pathway", and preserves every other slide visual.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import insert_09162026_pathway_overview as pathway_slides  # noqa: E402
import update_phase11_seaad_simple_aggr_part2 as ui  # noqa: E402


DEFAULT_DECK = (
    ROOT
    / "docs"
    / "presentations"
    / "09162026"
    / "09162026_sex_apoe_kda_fine_broad.pptx"
)
RESULTS_PATH = (
    ROOT
    / "results"
    / "minerva_production"
    / "11_pathway_deg_fine"
    / "fine_deg_pathway_significant_results.tsv.gz"
)
AUDIT_ROOT = ROOT / "results" / "presentations" / "09162026_pathway_method_summary"

INSERT_INDEX = 5
INPUT_SLIDES = 158
OUTPUT_SLIDES = 159
SECTION_TITLE = "Pathway analysis"
METHOD_TITLE = "How the pathway analysis was done"
OLD_LIST_TITLE = "Four mitochondrial gene programs anchor the pathway analysis"
LIST_TITLE = pathway_slides.LIST_TITLE
OVERLAP_TITLE = pathway_slides.OVERLAP_TITLE
NEXT_TITLE = pathway_slides.NEXT_TITLE

EXPECTED_STATS = {
    "mitocarta_broad_46": {
        "pathways_tested": 46,
        "pathways_significant": 12,
        "local_results": 517,
        "global_results": 436,
    },
    "mitocarta_complete_149": {
        "pathways_tested": 149,
        "pathways_significant": 18,
        "local_results": 735,
        "global_results": 591,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-root", type=Path, default=AUDIT_ROOT)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def slide_title(slide) -> str:
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False) and shape.text.strip():
            return " ".join(shape.text.split())
    return ""


def visual_fingerprint(slide) -> tuple[Any, ...]:
    return tuple(
        (
            int(shape.shape_type),
            shape.name,
            int(shape.left),
            int(shape.top),
            int(shape.width),
            int(shape.height),
            shape.text if getattr(shape, "has_text_frame", False) else "",
        )
        for shape in slide.shapes
    )


def load_and_validate_stats() -> dict[str, dict[str, int]]:
    if not RESULTS_PATH.is_file():
        raise FileNotFoundError(RESULTS_PATH)
    frame = pd.read_csv(RESULTS_PATH, sep="\t", low_memory=False)
    observed: dict[str, dict[str, int]] = {}
    for collection, expected in EXPECTED_STATS.items():
        selected = frame.loc[frame["pathway_collection"].eq(collection)]
        observed[collection] = {
            "pathways_tested": expected["pathways_tested"],
            "pathways_significant": int(selected["pathway_id"].nunique()),
            "local_results": int(len(selected)),
            "global_results": int(selected["global_fdr_significant"].sum()),
        }
    if observed != EXPECTED_STATS:
        raise RuntimeError(f"Pathway summary statistics changed: {observed!r}")
    return observed


def add_step_card(
    slide,
    *,
    number: str,
    title: str,
    body: str,
    x: float,
    background,
    accent,
) -> None:
    ui.add_rect(slide, x, 1.48, 3.58, 2.14, color=background, outline=None)
    ui.add_circle(slide, x + 0.24, 1.70, 0.48, accent)
    ui.add_text(
        slide,
        number,
        x + 0.24,
        1.78,
        0.48,
        0.24,
        size=14.5,
        color=ui.WHITE,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )
    ui.add_text(
        slide,
        title,
        x + 0.84,
        1.72,
        2.42,
        0.35,
        size=15.5,
        color=ui.NAVY,
        bold=True,
        valign=MSO_ANCHOR.MIDDLE,
    )
    ui.add_text(
        slide,
        body,
        x + 0.28,
        2.30,
        3.02,
        1.05,
        size=11.6,
        color=ui.DARK,
        valign=MSO_ANCHOR.MIDDLE,
    )


def add_result_card(
    slide,
    *,
    x: float,
    headline: str,
    label: str,
    background,
    accent,
) -> None:
    ui.add_rect(slide, x, 3.99, 5.71, 1.42, color=background, outline=None)
    ui.add_text(
        slide,
        headline,
        x + 0.28,
        4.20,
        1.45,
        0.44,
        size=23.0,
        color=ui.readable_accent(accent),
        bold=True,
        font=ui.FONT_HEAD,
        valign=MSO_ANCHOR.MIDDLE,
    )
    ui.add_text(
        slide,
        label,
        x + 1.78,
        4.12,
        3.57,
        0.56,
        size=13.2,
        color=ui.NAVY,
        bold=True,
        valign=MSO_ANCHOR.MIDDLE,
    )


def build_method_slide(slide, stats: dict[str, dict[str, int]]) -> None:
    ui.add_title_block(
        slide,
        METHOD_TITLE,
        "MitoCarta is a curated catalog of mitochondrial genes and pathways, consists of 3 categories of pathways.\n"
        "each fine-cell sex/APOE contrast was tested separately.",
    )
    slide.shapes[-1].height = Inches(0.60)
    add_step_card(
        slide,
        number="1",
        title="Create three DEG lists",
        body=(
            "For each contrast:\n"
            "• all mitochondrial DEGs\n"
            "• up-regulated in AD\n"
            "• down-regulated in AD"
        ),
        x=2.77,
        background=ui.PALE_SKY,
        accent=ui.BLUE,
    )
    ui.add_text(slide, "→", 6.43, 2.22, 0.35, 0.40, size=23, color=ui.MID, bold=True)
    add_step_card(
        slide,
        number="2",
        title="Test each pathway",
        body=(
            "Ask whether the DEG list contains more genes from that pathway than "
            "expected among genes detectable in the same contrast."
        ),
        x=6.87,
        background=ui.PALE_GREEN,
        accent=ui.TEAL,
    )
    add_result_card(
        slide,
        x=0.72,
        headline="12 of 46",
        label="Level 1& 2 MitoCarta pathways had at least one significant result",
        background=ui.PALE_SKY,
        accent=ui.BLUE,
    )
    add_result_card(
        slide,
        x=6.61,
        headline="18 of 149",
        label="complete MitoCarta pathways had at least one significant result",
        background=ui.PALE_GREEN,
        accent=ui.TEAL,
    )

    ui.add_text(
        slide,
        "Significant result = greater-than-expected pathway overlap after multiple-test correction (false-discovery rate < 5%).",
        0.80,
        5.60,
        11.60,
        0.30,
        size=8.8,
        color=ui.GRAY,
    )
    ui.add_rect(slide, 0.77, 5.99, 11.60, 0.75, color=ui.PALE_GRAY, outline=None)
    ui.add_text(
        slide,
        "Main pattern",
        0.82,
        6.27,
        1.30,
        0.25,
        size=11.8,
        color=ui.PURPLE,
        bold=True,
    )
    ui.add_text(
        slide,
        "Most significant results were overlapping OXPHOS pathways; non-OXPHOS signals were fewer and more localized.",
        2.17,
        6.19,
        9.55,
        0.38,
        size=12.3,
        color=ui.DARK,
        valign=MSO_ANCHOR.MIDDLE,
    )
    ui.add_notes(
        slide,
        goal="Explain how the pathway analysis was performed and show its full scope.",
        walkthrough=(
            "This analysis organized the pathways into three collections. "
            "The first contains four focused pathway definitions used repeatedly in "
            "the later findings. The second contains 46 Level 1 and Level 2 MitoCarta "
            "categories. The third contains all 149 MitoCarta pathways, including 103 "
            "more detailed Level 3 categories. For each estimable fine-cell sex/APOE "
            "contrast, the analysis created three mitochondrial DEG lists: all "
            "significant DEGs, genes up-regulated in AD, and genes down-regulated in "
            "AD. It then tested whether each list contained more genes from a pathway "
            "than expected among genes detectable in that contrast. A significant "
            "result means that this overlap remained significant after "
            "Benjamini-Hochberg correction across the pathways in the same collection "
            "for that DEG list, with a false-discovery rate below 5 percent. Twelve of the 46 "
            "Level 1 and Level 2 categories and 18 of the 149 complete pathways had at "
            "least one significant result. Most significant results involved "
            "overlapping OXPHOS pathways."
        ),
        boundary=(
            "The three collections are an analysis organization, not three independent "
            "parts of MitoCarta. The complete 149-pathway collection contains the 46 "
            "Level 1 and Level 2 categories, so the collections overlap. At least one "
            "significant result means enrichment in at least one fine-cell, sex/APOE, "
            "and DEG-direction list. It does not mean significance in every group or "
            "prove altered pathway activity."
        ),
        transition="Focus next on four pathways used repeatedly in the later findings.",
    )


def validate_deck(prs: Presentation, preserved: tuple[Any, ...]) -> None:
    if len(prs.slides) != OUTPUT_SLIDES:
        raise RuntimeError(f"Expected {OUTPUT_SLIDES} slides, found {len(prs.slides)}")
    expected = (SECTION_TITLE, METHOD_TITLE, LIST_TITLE, OVERLAP_TITLE, NEXT_TITLE)
    observed = tuple(slide_title(prs.slides[index]) for index in range(4, 9))
    if observed != expected:
        raise RuntimeError(f"Unexpected pathway-section order: {observed!r}")
    retained = tuple(
        visual_fingerprint(slide)
        for index, slide in enumerate(prs.slides)
        if index not in {INSERT_INDEX, INSERT_INDEX + 1, INSERT_INDEX + 2}
    )
    if retained != preserved:
        raise RuntimeError("A retained slide changed during pathway-summary insertion")
    for index, required in (
        (INSERT_INDEX, ["three DEG lists", "12 of 46", "18 of 149", "Significant result =", "Main pattern"]),
        (INSERT_INDEX + 1, ["Four mitochondrial pathways", "Two related questions"]),
        (INSERT_INDEX + 2, ["unique DEG genes", "three pathways"]),
    ):
        slide = prs.slides[index]
        visible = "\n".join(
            shape.text
            for shape in slide.shapes
            if getattr(shape, "has_text_frame", False)
        )
        for item in required:
            if item not in visible:
                raise RuntimeError(f"Missing {item!r} from slide {index + 1}")
        notes = slide.notes_slide.notes_text_frame
        if notes is None or not notes.text.strip():
            raise RuntimeError(f"Missing speaker notes on slide {index + 1}")
        for shape in slide.shapes:
            if (
                shape.left < 0
                or shape.top < 0
                or shape.left + shape.width > prs.slide_width + 10
                or shape.top + shape.height > prs.slide_height + 10
            ):
                raise RuntimeError(
                    f"Out-of-bounds shape on slide {index + 1}: {shape.name}"
                )


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_root = args.audit_root.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    stats = load_and_validate_stats()
    overlap = pathway_slides.prepare_overlap_data()
    artifacts = pathway_slides.render_overlap_figure(overlap, audit_root / "figures")
    input_hash = sha256(input_path)
    prs = Presentation(input_path)
    titles = [slide_title(slide) for slide in prs.slides]
    ui.set_notes_body_template(prs.slides[0].notes_slide.notes_placeholder._element)

    if (
        len(prs.slides) == INPUT_SLIDES
        and titles[4] == SECTION_TITLE
        and titles[5] in {OLD_LIST_TITLE, LIST_TITLE}
        and titles[6] == OVERLAP_TITLE
        and titles[7] == NEXT_TITLE
    ):
        preserved = tuple(
            visual_fingerprint(slide)
            for index, slide in enumerate(prs.slides)
            if index not in {INSERT_INDEX, INSERT_INDEX + 1}
        )
        method_slide = ui.new_slide(prs)
        build_method_slide(method_slide, stats)
        slide_ids = prs.slides._sldIdLst
        method_id = slide_ids[-1]
        slide_ids.remove(method_id)
        slide_ids.insert(INSERT_INDEX, method_id)
        action = "Inserted"
    elif (
        len(prs.slides) == OUTPUT_SLIDES
        and titles[4] == SECTION_TITLE
        and titles[5] == METHOD_TITLE
        and titles[6] in {OLD_LIST_TITLE, LIST_TITLE}
        and titles[7] == OVERLAP_TITLE
        and titles[8] == NEXT_TITLE
    ):
        preserved = tuple(
            visual_fingerprint(slide)
            for index, slide in enumerate(prs.slides)
            if index not in {INSERT_INDEX, INSERT_INDEX + 1, INSERT_INDEX + 2}
        )
        pathway_slides.clear_slide(prs.slides[INSERT_INDEX])
        build_method_slide(prs.slides[INSERT_INDEX], stats)
        action = "Updated"
    else:
        raise RuntimeError(
            f"Unexpected deck state: {len(prs.slides)} slides; slides 5-9 are "
            f"{titles[4:9]!r}"
        )

    pathway_slides.clear_slide(prs.slides[INSERT_INDEX + 1])
    pathway_slides.clear_slide(prs.slides[INSERT_INDEX + 2])
    pathway_slides.build_program_list_slide(prs.slides[INSERT_INDEX + 1])
    pathway_slides.build_overlap_slide(
        prs.slides[INSERT_INDEX + 2], artifacts["png"]
    )
    validate_deck(prs, preserved)

    audit_root.mkdir(parents=True, exist_ok=True)
    backup_dir = audit_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"input_deck_{input_hash[:12]}.pptx"
    if not backup_path.exists():
        shutil.copy2(input_path, backup_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=output_path.stem + ".", suffix=".pptx", dir=output_path.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        prs.save(temp_path)
        reopened = Presentation(temp_path)
        validate_deck(reopened, preserved)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print(f"{action} pathway method summary as slide 6: {output_path}")
    print(f"Slides: {len(prs.slides)}")
    print(f"Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
