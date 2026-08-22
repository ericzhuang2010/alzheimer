#!/usr/bin/env python3
"""Build the human-genetic-support presentation.

The deck follows ``phase19_presentation_slide_design.md`` and embeds the five
validated, slide-native genetic-support figures.  The main story is organized
into three sections with overview and divider slides; supporting slides retain
candidate lists, methods, dense matrices, and provenance caveats.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


REPO = Path(__file__).resolve().parents[2]
FIG_ROOT = REPO / "results/figures/analysis/phase_19_genetic_support"
RESULTS = REPO / "results/minerva_production"
DEFAULT_OUT = REPO / "docs/presentations/human_genetic_support_for_key_drivers.pptx"

FIG = {
    "workflow": FIG_ROOT / "gated_workflow/genetic_support_gated_workflow.png",
    "tier1": FIG_ROOT / "tier1_summary/genetic_support_tier1_slide_summary.png",
    "csf": FIG_ROOT / "csf_outcome_summary/genetic_support_csf_outcome_summary.png",
    "non_apoe": FIG_ROOT / "non_apoe_evidence/genetic_support_non_apoe_evidence_cards.png",
    "tier2": FIG_ROOT / "tier2_route_attrition/genetic_support_tier2_route_attrition.png",
}

AUX = {
    "tier1_matrix": RESULTS / "19_genetic_support_tier1/genetic_support_evidence_matrix.png",
    "tier1_loci": RESULTS / "19_genetic_support_tier1/genetic_support_locus_plots.pdf",
    "recovery_matrix": RESULTS / "19_genetic_support_tier2_recovery/recovery_evidence_matrix.png",
    "recovery_loci": RESULTS / "19_genetic_support_tier2_recovery/recovery_locus_plots.pdf",
    "csf_matrix": RESULTS / "19_genetic_support_endophenotype_gwas_qtl_extension/endophenotype_evidence_matrix.png",
}

SLIDE_W = Inches(13.333333)
SLIDE_H = Inches(7.5)

NAVY = RGBColor(15, 35, 61)
NAVY_2 = RGBColor(30, 59, 91)
BLUE = RGBColor(0, 114, 178)
SKY = RGBColor(86, 180, 233)
TEAL = RGBColor(0, 158, 115)
AMBER = RGBColor(230, 159, 0)
VERMILION = RGBColor(213, 94, 0)
PURPLE = RGBColor(126, 76, 154)
WHITE = RGBColor(255, 255, 255)
OFF_WHITE = RGBColor(247, 249, 252)
LIGHT = RGBColor(221, 229, 238)
MID = RGBColor(103, 116, 132)
DARK = RGBColor(47, 47, 47)
GRAY = RGBColor(77, 77, 77)
NO_SUPPORT = RGBColor(189, 189, 189)
PALE_BLUE = RGBColor(230, 242, 249)
PALE_GREEN = RGBColor(229, 244, 239)
PALE_AMBER = RGBColor(255, 246, 224)
PALE_RED = RGBColor(253, 235, 228)
PALE_GRAY = RGBColor(242, 244, 247)

FONT = "Arial"

MAIN_TITLES = [
    "Do genes highlighted by brain-cell networks also show inherited links to Alzheimer's disease?",
    "At a glance: APOE had strong evidence; most other genes need more study",
    "The presentation moves from the study design to results and next steps",
    "Study design and public data",
    "A gene can matter in diseased cells without changing inherited Alzheimer's risk",
    "We combined five kinds of public data, each with a different job",
    "Gene-activity datasets vary in cell type, sample size, and completeness",
    "A step-by-step design helps prevent overclaiming",
    "What the genetic evidence showed",
    "Only APOE had strong evidence in the first screen",
    "APOE was linked to Alzheimer's disease and all three spinal-fluid markers",
    "Four other genes showed hints, but none could be confirmed",
    "None of the 54 planned gene-activity comparisons reached the final test",
    "How to interpret the results and what to do next",
    "A missing result can mean three different things",
    "This study answers one focused question and leaves important gaps",
    "Next: finish the strongest open tests, then study more types of genetic effects",
    "The genetic evidence narrows the list but does not close the case",
]

APPENDIX_TITLES = [
    "Supporting details",
    "The original list: 25 genes in 47 gene–network settings",
    "Dataset details: what each source was used for",
    "Rules decided before looking at the results",
    "Full first-screen results for all 47 gene–network settings",
    "Four DNA regions had AD signals, but no candidate gene was confirmed by gene-activity data",
    "APOE evidence across Alzheimer's disease and three spinal-fluid markers",
    "RPS15 is promising, but the exact gene and cell setting remain uncertain",
    "Known file and documentation issues",
]

MAIN_NOTES = [
    "This study asked whether the key-driver genes from the network analysis also have evidence from inherited DNA differences. It did not rerank the original genes.",
    "The main result is concentrated in APOE. Two genes have early evidence, and RPS15 is an important follow-up candidate, but most genes need more study.",
    "The talk first explains the question and public datasets, then shows the results, and ends with limits and next steps.",
    "This section explains which genes were tested, which public datasets were used, and how each check was performed.",
    "Network analysis and genetics answer different questions. A gene can respond to disease or help maintain a disease state without carrying inherited risk.",
    "Each public dataset had one job: define the gene list, screen existing summaries, find Alzheimer-related DNA regions, study gene activity, or test spinal-fluid markers.",
    "Gene-activity studies differ in cell type, sample size, and available files. Brain-tissue results are useful fallbacks but do not prove a change in one exact cell type.",
    "The study used a fixed order of checks. A test stopped when an earlier requirement failed or when required data were missing.",
    "This section shows the first gene screen, the APOE result, evidence for four other genes, and why the later comparisons stopped.",
    "Only APOE had strong evidence in the first screen. The two COX7C rows came from one public result, not two independent studies; the RPS15 follow-up was separate.",
    "APOE is clearly linked to Alzheimer's disease and three spinal-fluid markers, but these data do not show exactly how APOE changes astrocytes.",
    "A strong DNA signal near a gene does not prove that the gene caused the signal. The four non-APOE genes therefore remain promising but unconfirmed.",
    "No final shared-signal comparison was completed because earlier checks failed or required gene-activity and reference data were unavailable.",
    "This section separates a true negative screen from an unfinished test or a mechanism that this study did not examine.",
    "A missing result can mean no strong signal was found, the test could not be completed, or the mechanism was outside the study design.",
    "The study mainly tested common DNA differences near nuclear genes. It was limited by small or mismatched cell datasets, incomplete files, and limited ancestry representation.",
    "The highest-value next step is to finish the APOE and RPS15 comparisons with complete gene-activity data and matched reference genetics.",
    "The genetic evidence helps prioritize the list, but it neither confirms nor rejects every network-derived gene.",
]

EXPECTED_TITLES = MAIN_TITLES + APPENDIX_TITLES
EXPECTED_SLIDE_COUNT = len(EXPECTED_TITLES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fill(shape, color: RGBColor, transparency: int = 0) -> None:
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if transparency:
        shape.fill.transparency = transparency


def stroke(shape, color: RGBColor, width: float = 1.0) -> None:
    shape.line.color.rgb = color
    shape.line.width = Pt(width)


def set_run(run, *, size: float, color: RGBColor, bold: bool = False,
            italic: bool = False) -> None:
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic


def add_rect(slide, x: float, y: float, w: float, h: float, *,
             color: RGBColor = WHITE, outline: RGBColor | None = LIGHT,
             radius: bool = True, transparency: int = 0,
             line_width: float = 1.0):
    kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(shape, color, transparency)
    if outline is None:
        shape.line.fill.background()
    else:
        stroke(shape, outline, line_width)
    return shape


def add_circle(slide, x: float, y: float, d: float, color: RGBColor,
               outline: RGBColor | None = None):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)
    )
    fill(shape, color)
    if outline is None:
        shape.line.fill.background()
    else:
        stroke(shape, outline)
    return shape


def add_text(slide, text: str, x: float, y: float, w: float, h: float, *,
             size: float = 16, color: RGBColor = DARK, bold: bool = False,
             italic: bool = False, align=PP_ALIGN.LEFT,
             valign=MSO_ANCHOR.TOP, margin: float = 0.03):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_before = p.space_after = Pt(0)
    p.line_spacing = 1.0
    run = p.add_run()
    run.text = text
    set_run(run, size=size, color=color, bold=bold, italic=italic)
    return box


def add_rich_text(slide, spans: list[tuple[str, dict]], x: float, y: float,
                  w: float, h: float, *, align=PP_ALIGN.LEFT,
                  valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.03)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_before = p.space_after = Pt(0)
    p.line_spacing = 1.0
    for text_value, style in spans:
        run = p.add_run()
        run.text = text_value
        set_run(
            run,
            size=style.get("size", 16),
            color=style.get("color", DARK),
            bold=style.get("bold", False),
            italic=style.get("italic", False),
        )
    return box


def add_bullets(slide, items: list[str], x: float, y: float, w: float, *,
                size: float = 15, accent: RGBColor = BLUE,
                color: RGBColor = DARK, line_h: float = 0.56) -> None:
    for index, item in enumerate(items):
        cy = y + index * line_h
        add_circle(slide, x, cy + 0.13, 0.09, accent)
        add_text(slide, item, x + 0.20, cy, w - 0.20, line_h,
                 size=size, color=color, valign=MSO_ANCHOR.MIDDLE)


def add_connector(slide, x1: float, y1: float, x2: float, y2: float,
                  color: RGBColor = BLUE, width: float = 2.0):
    shape = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    stroke(shape, color, width)
    shape.line.end_arrowhead = True
    return shape


def set_alt_text(shape, title: str, description: str) -> None:
    props = shape._element.xpath(".//p:cNvPr")
    if props:
        props[0].set("name", title)
        props[0].set("descr", description)


def add_picture_contain(slide, path: Path, x: float, y: float, w: float, h: float,
                        *, alt: str):
    with Image.open(path) as image:
        image_w, image_h = image.size
    scale = min(w / image_w, h / image_h)
    picture_w, picture_h = image_w * scale, image_h * scale
    picture_x = x + (w - picture_w) / 2
    picture_y = y + (h - picture_h) / 2
    picture = slide.shapes.add_picture(
        str(path), Inches(picture_x), Inches(picture_y),
        Inches(picture_w), Inches(picture_h)
    )
    set_alt_text(picture, alt, alt)
    return picture


def new_slide(prs: Presentation, *, bg: RGBColor = OFF_WHITE):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = bg
    return slide


def add_header(slide, kicker: str, title: str, page_no: int, *,
               accent: RGBColor = BLUE, subtitle: str | None = None) -> None:
    add_text(slide, kicker.upper(), 0.55, 0.18, 5.6, 0.24,
             size=9.5, color=accent, bold=True)
    title_size = 24.5 if len(title) < 70 else 22.0
    add_text(slide, title, 0.55, 0.44, 11.95, 0.56,
             size=title_size, color=NAVY, bold=True, valign=MSO_ANCHOR.MIDDLE)
    if subtitle:
        add_text(slide, subtitle, 0.57, 1.00, 11.65, 0.27,
                 size=10.7, color=MID)
    add_text(slide, f"{page_no:02d}", 12.42, 0.21, 0.36, 0.20,
             size=9, color=MID, bold=True, align=PP_ALIGN.RIGHT)


def add_source(slide, text_value: str) -> None:
    add_text(slide, text_value, 0.55, 7.25, 12.15, 0.14,
             size=6.8, color=MID)


def add_note(slide, note: str) -> None:
    slide.notes_slide.notes_text_frame.text = note


def add_ribbon(slide, text_value: str, *, y: float = 6.15,
               accent: RGBColor = BLUE, fill_color: RGBColor = NAVY) -> None:
    add_rect(slide, 0.55, y, 12.23, 0.55, color=fill_color,
             outline=None, radius=False)
    add_rect(slide, 0.55, y, 0.10, 0.55, color=accent,
             outline=None, radius=False)
    add_text(slide, text_value, 0.80, y + 0.10, 11.72, 0.31,
             size=12.0, color=WHITE, bold=True,
             valign=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


def add_figure_slide(prs: Presentation, *, page_no: int, title: str,
                     figure: Path, alt: str, source: str, note: str,
                     ribbon: str, accent: RGBColor = BLUE) -> None:
    slide = new_slide(prs, bg=WHITE)
    add_header(slide, "Main result", title, page_no, accent=accent)
    add_picture_contain(slide, figure, 0.55, 1.16, 12.23, 4.64, alt=alt)
    add_ribbon(slide, ribbon, y=6.12, accent=accent)
    add_source(slide, source)
    add_note(slide, note)


def render_pdf_page(pdf_path: Path, page: int, output_path: Path) -> None:
    command = [
        "gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pngalpha",
        "-r300", f"-dFirstPage={page}", f"-dLastPage={page}",
        f"-sOutputFile={output_path}", str(pdf_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Ghostscript did not create {output_path}")


def add_chip(slide, label: str, x: float, y: float, w: float, *,
             accent: RGBColor, bg: RGBColor) -> None:
    add_rect(slide, x, y, w, 0.64, color=bg, outline=accent,
             line_width=1.5)
    add_circle(slide, x + 0.18, y + 0.22, 0.18, accent)
    add_text(slide, label, x + 0.50, y + 0.16, w - 0.67, 0.30,
             size=13.0, color=NAVY, bold=True, valign=MSO_ANCHOR.MIDDLE)


def add_three_column_cards(slide, cards: list[tuple[str, str, str, RGBColor, RGBColor]],
                           *, y: float = 1.47, h: float = 4.83) -> None:
    card_w = 3.83
    for index, (number, title, body, accent, bg) in enumerate(cards):
        x = 0.70 + index * 4.10
        add_rect(slide, x, y, card_w, h, color=WHITE, outline=LIGHT)
        add_rect(slide, x, y, card_w, 0.80, color=bg, outline=None,
                 radius=False)
        add_text(slide, number, x + 0.22, y + 0.16, 0.45, 0.38,
                 size=16.0, color=accent, bold=True,
                 align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
        add_text(slide, title, x + 0.74, y + 0.13, card_w - 0.96, 0.46,
                 size=17.0, color=NAVY, bold=True,
                 valign=MSO_ANCHOR.MIDDLE)
        add_text(slide, body, x + 0.27, y + 1.12, card_w - 0.54, h - 1.40,
                 size=14.0, color=DARK)


def add_section_divider(prs: Presentation, *, marker: str, eyebrow: str,
                        title: str, subtitle: str, topics: list[str],
                        page_no: int, accent: RGBColor, note: str) -> None:
    """Add a dark narrative divider between presentation sections."""
    slide = new_slide(prs, bg=NAVY)
    add_rect(slide, 0, 0, 13.333, 7.5, color=NAVY, outline=None,
             radius=False)
    add_text(slide, eyebrow.upper(), 0.76, 0.63, 3.60, 0.28,
             size=11.0, color=accent, bold=True)
    add_rect(slide, 0.76, 1.28, 0.11, 2.26, color=accent,
             outline=None, radius=False)
    add_text(slide, title, 1.16, 1.36, 8.35, 1.50,
             size=32.0, color=WHITE, bold=True,
             valign=MSO_ANCHOR.MIDDLE)
    add_text(slide, subtitle, 1.18, 3.18, 7.90, 0.92,
             size=15.3, color=RGBColor(204, 219, 234))

    add_text(slide, marker, 9.55, 0.88, 2.52, 1.92,
             size=104.0 if len(marker) <= 2 else 82.0,
             color=NAVY_2, bold=True, align=PP_ALIGN.CENTER,
             valign=MSO_ANCHOR.MIDDLE)
    add_circle(slide, 11.63, 1.06, 0.56, accent)
    add_circle(slide, 10.98, 2.93, 0.28, SKY)
    add_rect(slide, 10.90, 2.12, 1.20, 0.035,
             color=RGBColor(105, 137, 169), outline=None, radius=False)
    add_rect(slide, 11.07, 2.14, 0.035, 0.91,
             color=RGBColor(105, 137, 169), outline=None, radius=False)

    add_text(slide, "IN THIS SECTION", 0.78, 4.67, 2.10, 0.25,
             size=9.8, color=SKY, bold=True)
    topic_x = [0.78, 4.20, 7.62]
    for index, topic in enumerate(topics[:3]):
        x = topic_x[index]
        add_rect(slide, x, 5.12, 3.10, 0.76,
                 color=NAVY_2, outline=accent)
        add_text(slide, topic, x + 0.18, 5.30, 2.74, 0.32,
                 size=11.4, color=WHITE, bold=True,
                 align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    add_text(slide, f"{page_no:02d}", 12.38, 0.34, 0.42, 0.22,
             size=9.0, color=RGBColor(145, 171, 197), bold=True,
             align=PP_ALIGN.RIGHT)
    add_note(slide, note)


def build_deck(output_path: Path = DEFAULT_OUT) -> Path:
    for path in [*FIG.values(), *AUX.values()]:
        if not path.exists():
            raise FileNotFoundError(path)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    prs.core_properties.title = "Inherited Genetic Evidence for Genes Highlighted by Cell Networks"
    prs.core_properties.subject = "Public-data study of 25 genes from 47 cell-network results"
    prs.core_properties.author = "Alzheimer project analysis team"
    prs.core_properties.keywords = "Alzheimer, genetics, QTL, APOE, key drivers"
    prs.core_properties.comments = (
        "Generated from validated genetic-support figures and minerva_production result bundles."
    )

    with tempfile.TemporaryDirectory(prefix="phase19_deck_assets_") as temp_dir:
        temp = Path(temp_dir)
        apoe_locus = temp / "apoe_tier1_locus_page1.png"
        recovery_loci = temp / "recovery_loci_page1.png"
        render_pdf_page(AUX["tier1_loci"], 1, apoe_locus)
        render_pdf_page(AUX["recovery_loci"], 1, recovery_loci)

        # 1 — title
        slide = new_slide(prs, bg=NAVY)
        add_rect(slide, 0, 0, 13.333, 7.5, color=NAVY, outline=None,
                 radius=False)
        add_text(slide, "GENES, NETWORKS, AND INHERITED RISK", 0.76, 0.67,
                 7.2, 0.28, size=11.5, color=SKY, bold=True)
        add_text(slide, "Do genes highlighted by brain-cell networks also show\ninherited links to Alzheimer's disease?",
                 0.76, 1.25, 8.25, 1.78, size=31.0, color=WHITE,
                 bold=True, valign=MSO_ANCHOR.MIDDLE)
        add_text(slide,
                 "A public-data study of 25 genes from 47 cell-network results",
                 0.78, 3.38, 7.75, 0.62, size=17.0,
                 color=RGBColor(210, 224, 239))
        add_rect(slide, 0.78, 4.30, 7.68, 0.06, color=BLUE,
                 outline=None, radius=False)
        add_text(slide,
                 "APOE had the strongest inherited DNA evidence; several other genes remain possible but unconfirmed.",
                 0.78, 4.65, 7.80, 0.75, size=14.5,
                 color=RGBColor(191, 210, 229))

        # Abstract network motif at right, deliberately non-biological.
        nodes = [
            (9.25, 1.05, 0.92, BLUE), (10.75, 1.54, 0.62, AMBER),
            (11.77, 0.90, 0.42, SKY), (9.55, 2.82, 0.50, PURPLE),
            (11.20, 3.06, 0.82, BLUE), (10.28, 4.56, 0.42, VERMILION),
            (11.77, 4.85, 0.62, TEAL),
        ]
        for x, y, diameter, color in nodes:
            add_circle(slide, x, y, diameter, color)
        for x1, y1, x2, y2 in [
            (9.72, 1.48, 11.04, 1.83), (11.06, 1.95, 11.56, 3.28),
            (9.80, 3.04, 11.43, 3.46), (10.02, 3.30, 10.47, 4.70),
            (11.53, 3.70, 12.06, 5.14), (10.66, 4.75, 11.98, 5.12),
        ]:
            add_connector(slide, x1, y1, x2, y2,
                          RGBColor(133, 164, 194), width=1.5)

        add_text(slide, "STUDY DESIGN  •  DATASETS  •  EVIDENCE  •  INTERPRETATION",
                 0.78, 6.35, 7.80, 0.25, size=10.0,
                 color=RGBColor(145, 171, 197), bold=True)
        add_text(slide, "Public-data update • 21 August 2026", 0.78, 7.03,
                 4.2, 0.18, size=8.5, color=RGBColor(145, 171, 197))
        add_note(slide, MAIN_NOTES[0])

        # 2 — executive overview
        slide = new_slide(prs)
        add_header(slide, "Executive overview", MAIN_TITLES[1], 2, accent=BLUE)
        overview_cards = [
            ("STARTING LIST", "25 genes", "47 gene-by-cell-network combinations", TEAL, PALE_GREEN),
            ("GENES TESTED", "19 nuclear", "6 mitochondrial genes need a different test", PURPLE, PALE_BLUE),
            ("STRONG EVIDENCE", "APOE", "Linked to Alzheimer's disease and 3 spinal-fluid markers", BLUE, PALE_BLUE),
            ("EARLY EVIDENCE", "COX7C + SELENOW", "Promising but incomplete public evidence", AMBER, PALE_AMBER),
            ("FOLLOW-UP PRIORITY", "RPS15", "Strong nearby DNA signal; gene link not confirmed", VERMILION, PALE_RED),
            ("FINAL COMPARISON", "0 completed", "Required gene-activity or reference data were missing", GRAY, PALE_GRAY),
        ]
        for index, (label, value, detail, accent, bg) in enumerate(overview_cards):
            row, col = divmod(index, 3)
            x = 0.70 + col * 4.10
            y = 1.38 + row * 2.23
            add_rect(slide, x, y, 3.83, 1.82, color=WHITE, outline=LIGHT)
            add_rect(slide, x, y, 0.11, 1.82, color=accent,
                     outline=None, radius=False)
            add_text(slide, label, x + 0.30, y + 0.20, 3.20, 0.22,
                     size=9.0, color=accent, bold=True)
            add_text(slide, value, x + 0.30, y + 0.58, 3.20, 0.46,
                     size=20.0 if len(value) < 15 else 16.5,
                     color=NAVY, bold=True, valign=MSO_ANCHOR.MIDDLE)
            add_text(slide, detail, x + 0.30, y + 1.18, 3.20, 0.42,
                     size=10.4, color=GRAY, valign=MSO_ANCHOR.MIDDLE)
        add_ribbon(slide,
                   "The genetic study adds a new layer of evidence; it does not replace the original network analysis.",
                   y=6.34, accent=BLUE)
        add_source(slide, "Source: consolidated genetic-support summary; formal Tier 1, recovery, and CSF status tables")
        add_note(slide, MAIN_NOTES[1])

        # 3 — presentation roadmap
        slide = new_slide(prs)
        add_header(slide, "Presentation roadmap", MAIN_TITLES[2], 3,
                   accent=TEAL)
        agenda_rows = [
            (
                "01", "Study design and public data", "Slides 04–08",
                "What the two analyses ask, which public datasets were used, and how each check worked.",
                TEAL, PALE_GREEN,
            ),
            (
                "02", "What the genetic evidence showed", "Slides 09–13",
                "The first gene screen, the APOE result, four other genes, and the reasons later tests stopped.",
                BLUE, PALE_BLUE,
            ),
            (
                "03", "How to read the results and what comes next", "Slides 14–18",
                "What a missing result means, what this study could not test, and the most useful next steps.",
                VERMILION, PALE_RED,
            ),
        ]
        for index, (number, title, slide_range, body, accent, bg) in enumerate(agenda_rows):
            y = 1.42 + index * 1.64
            add_rect(slide, 0.74, y, 11.86, 1.37, color=WHITE, outline=LIGHT)
            add_rect(slide, 0.74, y, 0.10, 1.37, color=accent,
                     outline=None, radius=False)
            add_circle(slide, 1.10, y + 0.34, 0.68, accent)
            add_text(slide, number, 1.10, y + 0.53, 0.68, 0.23,
                     size=11.5, color=WHITE, bold=True,
                     align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
            add_text(slide, title, 2.04, y + 0.21, 6.85, 0.36,
                     size=18.0, color=NAVY, bold=True)
            add_text(slide, slide_range, 9.70, y + 0.23, 2.38, 0.27,
                     size=10.2, color=accent, bold=True,
                     align=PP_ALIGN.RIGHT)
            add_text(slide, body, 2.05, y + 0.72, 9.90, 0.42,
                     size=11.4, color=GRAY)
        add_ribbon(slide,
                   "Exact cutoffs, full evidence tables, and file-quality checks are kept in the appendix on slides 19–27.",
                   y=6.50, accent=TEAL)
        add_note(slide, MAIN_NOTES[2])

        # 4 — section divider: study design and datasets
        add_section_divider(
            prs, marker="01", eyebrow="Section 01", title=MAIN_TITLES[3],
            subtitle="What was tested, which public resources were used, and how the evidence was checked step by step.",
            topics=["GWAS: DNA–trait links", "QTL: DNA–gene activity links", "CSF: spinal fluid"],
            page_no=4, accent=TEAL, note=MAIN_NOTES[3],
        )

        # 5 — complementary questions
        slide = new_slide(prs)
        add_header(slide, "Framing", MAIN_TITLES[4], 5, accent=TEAL)
        add_rect(slide, 0.73, 1.42, 4.95, 2.04, color=PALE_GREEN,
                 outline=TEAL, line_width=1.5)
        add_text(slide, "CELL-NETWORK ANALYSIS", 1.03, 1.72, 2.65, 0.26,
                 size=11.0, color=TEAL, bold=True)
        add_text(slide, "Which genes are central in diseased cells?", 1.03, 2.08,
                 4.28, 0.58, size=17.0, color=NAVY, bold=True)
        add_text(slide, "47 cell-network results  •  25 genes", 1.03, 2.78,
                 4.25, 0.32, size=15.5, color=GRAY, bold=True)

        add_connector(slide, 5.85, 2.44, 7.30, 2.44, color=BLUE, width=2.5)
        add_text(slide, "different\nquestions", 5.76, 2.69, 1.61, 0.62,
                 size=10.0, color=MID, bold=True, align=PP_ALIGN.CENTER)

        add_rect(slide, 7.45, 1.42, 5.13, 2.04, color=PALE_BLUE,
                 outline=BLUE, line_width=1.5)
        add_text(slide, "INHERITED-DNA ANALYSIS", 7.77, 1.72, 2.70, 0.26,
                 size=11.0, color=BLUE, bold=True)
        add_text(slide, "Which genes are linked to inherited AD risk?", 7.77, 2.08,
                 4.45, 0.58, size=17.0, color=NAVY, bold=True)
        add_text(slide, "19 nuclear genes tested  •  6 mitochondrial genes need a different test",
                 7.77, 2.78, 4.45, 0.48, size=12.5, color=GRAY, bold=True)

        add_bullets(slide, [
            "The network analysis finds genes at the center of disease-related activity in cells.",
            "The genetic analysis asks whether inherited DNA differences near a gene are linked to Alzheimer's disease or disease markers.",
            "A gene may help drive—or respond to—disease without being where inherited risk begins.",
        ], 1.02, 4.15, 11.25, size=16.0, accent=BLUE, line_h=0.69)
        add_ribbon(slide,
                   "A gene can matter in the disease process even when inherited DNA evidence is weak.",
                   y=6.42, accent=TEAL)
        add_source(slide, "Source: genetic-support consolidated summary §1.1; call_key_driver_returns.tsv")
        add_note(slide, MAIN_NOTES[4])

        # 6 — dataset portfolio
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Public datasets", MAIN_TITLES[5], 6,
                   accent=BLUE)
        data_layers = [
            (
                "Starting gene list",
                "Network-analysis list • GENCODE v44 • HGNC 2026-06-05",
                "Keep the same 47 settings / 25 genes; map 19 nuclear genes and flag 6 mitochondrial genes.",
                TEAL,
            ),
            (
                "Published summary lists",
                "FunGen-xQTL snapshot f6f63fc… • six public files (~8.74 MiB)",
                "Quickly check earlier Alzheimer's and gene-regulation results; these lists do not contain every study detail.",
                AMBER,
            ),
            (
                "Alzheimer's disease study",
                "Bellenguez 2022 • GCST90027158 • complete GRCh38 summary statistics",
                "Look for disease-linked DNA variants within ±1 Mb (one million DNA letters) of each nuclear gene.",
                BLUE,
            ),
            (
                "Brain gene-activity data",
                "NIAGADS NG00184.v1 • eQTL Catalogue r7",
                "Find DNA variants linked to RNA amount, RNA splicing, or protein amount in brain samples.",
                VERMILION,
            ),
            (
                "Spinal-fluid markers",
                "GCST90726396 / GCST90726397 / GCST90726398 • European N=18,948 each",
                "Test amyloid-β42, total tau, and p-tau181 across 19 genes × 3 markers = 57 checks.",
                PURPLE,
            ),
        ]
        col_x = [0.55, 2.55, 7.25]
        col_w = [2.00, 4.70, 5.53]
        for col, header in enumerate(["Data type", "Dataset / version", "What it tells us"]):
            add_rect(slide, col_x[col], 1.26, col_w[col], 0.50,
                     color=NAVY, outline=WHITE, radius=False)
            add_text(slide, header, col_x[col] + 0.13, 1.38,
                     col_w[col] - 0.26, 0.24, size=10.7,
                     color=WHITE, bold=True)
        for row_index, (layer, resource, role, accent) in enumerate(data_layers):
            y = 1.76 + row_index * 0.91
            bg = WHITE if row_index % 2 == 0 else PALE_GRAY
            for col, value in enumerate([layer, resource, role]):
                add_rect(slide, col_x[col], y, col_w[col], 0.91,
                         color=bg, outline=LIGHT, radius=False)
                add_text(slide, value, col_x[col] + 0.14, y + 0.10,
                         col_w[col] - 0.28, 0.67,
                         size=10.3 if col else 10.8,
                         color=NAVY if col == 0 else DARK,
                         bold=(col == 0), valign=MSO_ANCHOR.MIDDLE)
            add_rect(slide, 0.55, y, 0.07, 0.91, color=accent,
                     outline=None, radius=False)
        add_ribbon(slide,
                   "Summary data = group-level results, not individual records • CSF = fluid around the brain and spinal cord.",
                   y=6.45, accent=BLUE)
        add_source(slide, "Source: candidate, Tier 1, Tier 2, recovery, and CSF dataset registries and input inventories")
        add_note(slide, MAIN_NOTES[5])

        # 7 — QTL resource detail
        slide = new_slide(prs)
        add_header(slide, "Gene-activity data", MAIN_TITLES[6], 7,
                   accent=VERMILION)
        qtl_cards = [
            (
                "MICROGLIA", "Young 2019 • 104 samples",
                "eQTL (RNA amount): QTD000559\nsQTL (RNA splicing): QTD000563\n\nSame cell type",
                TEAL, PALE_GREEN,
            ),
            (
                "NEURON-LIKE CELLS", "Aygun 2021 • 73 samples",
                "eQTL (RNA amount): QTD000569\nsQTL (RNA splicing): QTD000573\n\nRelated neuron samples",
                BLUE, PALE_BLUE,
            ),
            (
                "MIXED BRAIN TISSUE", "Walker 2019 • 211 samples",
                "eQTL (RNA amount): QTD000579\nsQTL (RNA splicing): QTD000583\n\nUseful fallback—not exact-cell proof",
                AMBER, PALE_AMBER,
            ),
            (
                "BROADER BRAIN DATA", "NG00184.v1",
                "eQTL: RNA amount\nsQTL: RNA splicing\npQTL: protein amount\n\nWider coverage; full files and models often missing",
                VERMILION, PALE_RED,
            ),
        ]
        for index, (label, title, body, accent, bg) in enumerate(qtl_cards):
            x = 0.55 + index * 3.07
            add_rect(slide, x, 1.35, 2.82, 3.30, color=WHITE, outline=LIGHT)
            add_rect(slide, x, 1.35, 2.82, 0.62, color=bg,
                     outline=None, radius=False)
            add_text(slide, label, x + 0.16, 1.54, 2.50, 0.20,
                     size=8.4, color=accent, bold=True,
                     align=PP_ALIGN.CENTER)
            add_text(slide, title, x + 0.18, 2.16, 2.46, 0.43,
                     size=15.0, color=NAVY, bold=True,
                     align=PP_ALIGN.CENTER)
            add_text(slide, body, x + 0.22, 2.85, 2.38, 1.52,
                     size=10.4, color=DARK, align=PP_ALIGN.CENTER)

        add_rect(slide, 0.55, 4.91, 6.00, 1.04, color=WHITE, outline=BLUE)
        add_text(slide, "APOE PROTEIN FOLLOW-UP (pQTL)", 0.78, 5.10, 2.80, 0.20,
                 size=9.0, color=BLUE, bold=True)
        add_text(slide,
                 "NG00130.v2 • 3,506 European samples • spinal-fluid protein study used after APOE passed the earlier checks; the published file list is incomplete.",
                 0.78, 5.42, 5.45, 0.37, size=10.3, color=DARK)
        add_rect(slide, 6.78, 4.91, 6.00, 1.04, color=WHITE,
                 outline=VERMILION)
        add_text(slide, "RPS15 FOLLOW-UP", 7.01, 5.10, 2.30, 0.20,
                 size=9.0, color=VERMILION, bold=True)
        add_text(slide,
                 "Existing brain datasets were checked again; six positive setting rows came from three mixed-brain results repeated across two cell-network settings.",
                 7.01, 5.42, 5.45, 0.37, size=10.3, color=DARK)
        add_ribbon(slide,
                   "The full NG00184 files (~844 GB) were not downloaded; exact-cell studies were small, and matching DNA-reference data were often missing.",
                   y=6.32, accent=VERMILION)
        add_source(slide, "Source: recovery_dataset_registry.tsv; endophenotype_dataset_registry.tsv; targeted RPS15 audit")
        add_note(slide, MAIN_NOTES[6])

        # 8 — workflow figure
        add_figure_slide(
            prs, page_no=8, title=MAIN_TITLES[7], figure=FIG["workflow"],
            alt="Step-by-step workflow for checking public genetic evidence and comparing disease signals with gene-activity signals",
            source="Source: generated workflow package; analysis contracts, registries, and route manifests",
            note=MAIN_NOTES[7],
            ribbon="A comparison stopped when a required signal or dataset was missing. Arrows show steps—not cause and effect.",
            accent=BLUE,
        )

        # 9 — section divider: genetic evidence
        add_section_divider(
            prs, marker="02", eyebrow="Section 02", title=MAIN_TITLES[8],
            subtitle="We summarize all 47 gene–network settings, then focus on APOE and the other genes.",
            topics=["All 47 settings", "APOE + spinal fluid", "Other genes + stopped tests"],
            page_no=9, accent=BLUE, note=MAIN_NOTES[8],
        )

        # 10–13 — four result figures, full-width and untrimmed.
        add_figure_slide(
            prs, page_no=10, title=MAIN_TITLES[9], figure=FIG["tier1"],
            alt="First-screen scorecard for all 47 gene–network settings",
            source="Source: Tier 1 genetic_support_evidence_summary.tsv and genetic_support_status.tsv",
            note=MAIN_NOTES[9],
            ribbon="The extra RPS15 follow-up found limited evidence and was not included in these 47 first-screen results.",
            accent=BLUE,
        )
        add_figure_slide(
            prs, page_no=11, title=MAIN_TITLES[10], figure=FIG["csf"],
            alt="Spinal-fluid marker results showing APOE as the only positive gene across all three markers",
            source="Source: CSF endophenotype_gate_decisions.tsv and MAGMA candidate-gene results",
            note=MAIN_NOTES[10],
            ribbon="APOE's DNA signal is clear, but these data do not show exactly how APOE changes astrocytes.",
            accent=BLUE,
        )
        add_figure_slide(
            prs, page_no=12, title=MAIN_TITLES[11], figure=FIG["non_apoe"],
            alt="Evidence summaries for COX7C, SELENOW, RPS15, and ANKRD11",
            source="Source: generated non-APOE plot data; Tier 1, recovery, RPS15 audit, and CSF result bundles",
            note=MAIN_NOTES[11],
            ribbon="A strong DNA signal near a gene does not prove that the gene caused the signal.",
            accent=AMBER,
        )
        add_figure_slide(
            prs, page_no=13, title=MAIN_TITLES[12], figure=FIG["tier2"],
            alt="Reasons each of 54 planned gene-activity comparisons stopped before the final test",
            source="Source: Tier 2 recovery_route_decisions.tsv and header-only recovery_colocalization.tsv.gz",
            note=MAIN_NOTES[12],
            ribbon="These numbers show why each comparison stopped; zero completed tests does not mean zero shared signals.",
            accent=VERMILION,
        )

        # 14 — section divider: interpretation and next steps
        add_section_divider(
            prs, marker="03", eyebrow="Section 03", title=MAIN_TITLES[13],
            subtitle="A missing result can mean no signal, an unfinished test, or biology that this study did not examine.",
            topics=["No strong signal", "Test could not finish", "Not studied here"],
            page_no=14, accent=VERMILION, note=MAIN_NOTES[13],
        )

        # 15 — interpret negative evidence
        slide = new_slide(prs)
        add_header(slide, "Interpretation", MAIN_TITLES[14], 15,
                   accent=VERMILION)
        cards = [
            (
                "01", "No strong signal found",
                "15 of 19 nuclear genes had no nearby Alzheimer's-linked DNA signal at P < 5×10⁻⁸.\n\nAll 18 non-APOE genes failed the spinal-fluid marker checks.",
                NO_SUPPORT, PALE_GRAY,
            ),
            (
                "02", "The test could not finish",
                "Complete gene-activity files or matching DNA-reference data were missing.\n\nData from the exact cell type were small, unavailable, or did not match.",
                VERMILION, PALE_RED,
            ),
            (
                "03", "Not covered by this study",
                "Mitochondrial DNA, rare or large DNA changes, distant gene control, gene interactions, disease timing, and processes after RNA is made.",
                GRAY, WHITE,
            ),
        ]
        add_three_column_cards(slide, cards, y=1.42, h=4.75)
        add_ribbon(slide, "The six mitochondrial genes were not found negative—they need a different testing method.",
                   y=6.40, accent=VERMILION)
        add_source(slide, "Source: recovery_regional_gwas_summary.tsv; CSF gate decisions; Tier 1 mtDNA evidence states")
        add_note(slide, MAIN_NOTES[14])

        # 16 — explicit limitations
        slide = new_slide(prs)
        add_header(slide, "What this study could not answer", MAIN_TITLES[15], 16,
                   accent=VERMILION)
        limitations = [
            (
                "01", "No final signal comparison",
                "Zero final shared-signal tests were completed. Full gene-activity files and matching DNA-reference data were often unavailable.",
                VERMILION, PALE_RED,
            ),
            (
                "02", "Small or mixed samples",
                "Cell-focused gene-activity studies were small (N=73–211). Mixed brain tissue cannot prove a change in one exact cell type.",
                AMBER, PALE_AMBER,
            ),
            (
                "03", "Limited populations",
                "The main DNA studies were mostly European. Some brain data came from overlapping participants and were not fully independent.",
                BLUE, PALE_BLUE,
            ),
            (
                "04", "Other biology not tested",
                "Rare, large, mitochondrial, or distant DNA effects, gene interactions, disease timing, and laboratory experiments were outside this study.",
                GRAY, PALE_GRAY,
            ),
        ]
        for index, (number, title, body, accent, bg) in enumerate(limitations):
            row, col = divmod(index, 2)
            x = 0.68 + col * 6.12
            y = 1.40 + row * 2.33
            add_rect(slide, x, y, 5.83, 2.02, color=WHITE, outline=LIGHT)
            add_rect(slide, x, y, 0.10, 2.02, color=accent,
                     outline=None, radius=False)
            add_text(slide, number, x + 0.27, y + 0.22, 0.55, 0.30,
                     size=14.0, color=accent, bold=True,
                     align=PP_ALIGN.CENTER)
            add_text(slide, title, x + 0.96, y + 0.20, 4.48, 0.36,
                     size=16.5, color=NAVY, bold=True)
            add_text(slide, body, x + 0.96, y + 0.78, 4.45, 0.94,
                     size=11.6, color=DARK)
        add_ribbon(slide,
                   "Strongest conclusion: common inherited DNA variants located near nuclear genes in these public datasets.",
                   y=6.34, accent=VERMILION)
        add_source(slide, "Source: consolidated genetic-support summary §§5–6; route, QTL, ancestry, and provenance audits")
        add_note(slide, MAIN_NOTES[15])

        # 17 — roadmap
        slide = new_slide(prs)
        add_header(slide, "Next steps", MAIN_TITLES[16], 17, accent=TEAL)
        roadmap = [
            (
                "01", "Finish APOE and RPS15",
                "Complete gene-activity datasets\n+ matching DNA-reference data\n+ larger studies of exact cell types",
                VERMILION, PALE_RED,
            ),
            (
                "02", "Test more genetic effects",
                "Protein- and RNA-based gene tests\n+ rare DNA changes and interactions\n+ more traits and populations",
                BLUE, PALE_BLUE,
            ),
            (
                "03", "Use separate and lab checks",
                "Dedicated mitochondrial-DNA study\n+ repeat the network study in new data\n+ change gene activity in lab experiments",
                TEAL, PALE_GREEN,
            ),
        ]
        add_three_column_cards(slide, roadmap, y=1.50, h=4.55)
        for index in range(2):
            start_x = 4.58 + index * 4.10
            add_connector(slide, start_x, 3.83, start_x + 0.45, 3.83,
                          color=BLUE, width=2.0)
        add_ribbon(slide,
                   "Highest-value next step: collect the complete gene-activity and reference data needed for APOE and RPS15.",
                   y=6.37, accent=TEAL)
        add_source(slide, "Source: genetic-support consolidated summary §6.2; bundle-repair actions are detailed in the appendix")
        add_note(slide, MAIN_NOTES[16])

        # 18 — close
        slide = new_slide(prs, bg=NAVY)
        add_rect(slide, 0, 0, 13.333, 7.5, color=NAVY, outline=None,
                 radius=False)
        add_text(slide, "TAKE-HOME MESSAGE", 0.72, 0.50, 4.5, 0.26,
                 size=10.5, color=SKY, bold=True)
        add_text(slide, MAIN_TITLES[17], 0.72, 0.92, 11.8, 0.75,
                 size=29.0, color=WHITE, bold=True)
        takeaways = [
            ("01", "APOE", "Strong evidence from Alzheimer's and spinal-fluid studies.", BLUE),
            ("02", "COX7C + SELENOW", "Early evidence, but not enough for confirmation.", AMBER),
            ("03", "RPS15 + ANKRD11", "A follow-up priority and a nearby DNA-region signal, respectively.", VERMILION),
            ("04", "No new gene confirmed", "Results included negative checks, missing data, and biology not tested here.", TEAL),
        ]
        for index, (number, title, body, accent) in enumerate(takeaways):
            row = index // 2
            col = index % 2
            x = 0.72 + col * 6.10
            y = 2.05 + row * 1.62
            add_rect(slide, x, y, 5.72, 1.28, color=NAVY_2,
                     outline=accent, line_width=1.4)
            add_text(slide, number, x + 0.24, y + 0.19, 0.52, 0.36,
                     size=16.0, color=accent, bold=True,
                     align=PP_ALIGN.CENTER)
            add_text(slide, title, x + 0.92, y + 0.17, 4.50, 0.33,
                     size=17.0, color=WHITE, bold=True)
            add_text(slide, body, x + 0.92, y + 0.63, 4.48, 0.42,
                     size=12.0, color=RGBColor(207, 222, 237))
        add_rect(slide, 3.52, 5.76, 6.29, 0.73, color=WHITE,
                 outline=TEAL, line_width=1.6)
        add_text(slide, "Status: important follow-up remains", 3.76, 5.96,
                 5.81, 0.31, size=15.5, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide,
                 "This evidence adds to the network findings; it does not prove or reject them.",
                 2.15, 6.78, 9.03, 0.30, size=12.5,
                 color=RGBColor(173, 197, 220), align=PP_ALIGN.CENTER)
        add_text(slide, "18", 12.42, 0.32, 0.36, 0.20,
                 size=9, color=RGBColor(145, 171, 197), bold=True,
                 align=PP_ALIGN.RIGHT)
        add_note(slide, MAIN_NOTES[17])

        # 19 — appendix divider
        add_section_divider(
            prs, marker="A", eyebrow="Appendix", title=APPENDIX_TITLES[0],
            subtitle="The exact gene list, dataset versions, cutoffs, full result tables, and known file-quality issues.",
            topics=["Original gene list", "Data + rules", "Full results + file checks"],
            page_no=19, accent=SKY,
            note="The appendix keeps the technical details behind the main presentation for questions and follow-up discussion.",
        )

        # 20 — appendix candidate list
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • original gene list", APPENDIX_TITLES[1], 20,
                   accent=TEAL)
        headers = ["Cell network", "Mitochondria-related group (original order)", "Other driver group (original order)"]
        rows = [
            ("Astrocytes", "MT-CO2, MT-CO3, MT-ATP6, COX7C, COX4I1", "RPL11, RPLP1, RPL15, APOE, LAPTM4A"),
            ("Excitatory neurons", "MT-CO2, UQCR10, COX4I1, COX6B1, MT-CYB", "RPL11, RPS13, SELENOW, LAMTOR5, DYNLT1"),
            ("Inhibitory neurons", "MT-CO2, MT-CO3, MT-CYB, MT-ND5, COX7C", "RPS15, LAMTOR5, RPLP1, ATP6V1F, RPL38"),
            ("Microglia", "MT-CO2, MT-ND4", "RPL11"),
            ("OPCs", "MT-CO3, MT-CO2, MT-ND4", "RPS15, FTL, ANKRD11, NCOA1"),
            ("Oligodendrocytes", "MT-CO2, MT-ND4", "RPL11"),
            ("Vasculature cells", "MT-CO3, MT-CO2, MT-ATP6, MT-ND4", "None"),
        ]
        col_x = [0.55, 2.45, 7.55]
        col_w = [1.90, 5.10, 5.23]
        table_y = 1.30
        for col, header in enumerate(headers):
            add_rect(slide, col_x[col], table_y, col_w[col], 0.55,
                     color=NAVY, outline=WHITE, radius=False)
            add_text(slide, header, col_x[col] + 0.12, table_y + 0.13,
                     col_w[col] - 0.24, 0.26, size=11.0, color=WHITE,
                     bold=True, valign=MSO_ANCHOR.MIDDLE)
        for row_index, row in enumerate(rows):
            y = table_y + 0.55 + row_index * 0.69
            bg = WHITE if row_index % 2 == 0 else PALE_GRAY
            for col, value in enumerate(row):
                add_rect(slide, col_x[col], y, col_w[col], 0.69,
                         color=bg, outline=LIGHT, radius=False)
                add_text(slide, value, col_x[col] + 0.12, y + 0.10,
                         col_w[col] - 0.24, 0.47,
                         size=10.8 if col else 11.3, color=NAVY if col == 0 else DARK,
                         bold=(col == 0), valign=MSO_ANCHOR.MIDDLE)
        add_ribbon(slide,
                   "‘MT driver’ was a label in the original network analysis; COX7C and UQCR10 are nuclear genes. Six genes are encoded by mitochondrial DNA.",
                   y=6.83, accent=TEAL)
        add_note(slide, "This is the original top-five gene list from each cell network, shown in its original order.")

        # 21 — dataset inventory
        slide = new_slide(prs)
        add_header(slide, "Appendix • data inventory", APPENDIX_TITLES[2], 21,
                   accent=BLUE)
        inventory = [
            ("Starting gene list", "Original network study • GENCODE v44 • HGNC 2026-06-05", "Keep 47 settings; map gene names and DNA locations"),
            ("Published summaries", "FunGen-xQTL snapshot f6f63fc…", "Quick screen of earlier AD and gene-regulation results"),
            ("Alzheimer's disease", "Bellenguez • GCST90027158", "Check DNA within ±1 Mb of the 19 nuclear genes"),
            ("Brain gene activity", "NG00184.v1 • eQTL Catalogue r7", "Check DNA links to RNA amount, RNA splicing, and protein"),
            ("Spinal-fluid markers", "GCST90726396 / 397 / 398 • N=18,948 each", "Test amyloid-β42, total tau, and p-tau181"),
            ("Focused follow-up", "NG00130.v2 APOE protein QTL • local NG00184 RPS15", "Study the open APOE and RPS15 questions"),
        ]
        x_values = [0.55, 2.72, 7.44]
        widths = [2.17, 4.72, 5.34]
        for col, header in enumerate(["Data type", "Dataset / version", "What it tells us"]):
            add_rect(slide, x_values[col], 1.30, widths[col], 0.55,
                     color=NAVY, outline=WHITE, radius=False)
            add_text(slide, header, x_values[col] + 0.13, 1.43,
                     widths[col] - 0.26, 0.26, size=11.2,
                     color=WHITE, bold=True)
        for row_index, row in enumerate(inventory):
            y = 1.85 + row_index * 0.78
            bg = WHITE if row_index % 2 == 0 else PALE_GRAY
            for col, value in enumerate(row):
                add_rect(slide, x_values[col], y, widths[col], 0.78,
                         color=bg, outline=LIGHT, radius=False)
                add_text(slide, value, x_values[col] + 0.13, y + 0.10,
                         widths[col] - 0.26, 0.54,
                         size=11.1 if col else 11.5,
                         color=NAVY if col == 0 else DARK,
                         bold=(col == 0), valign=MSO_ANCHOR.MIDDLE)
        add_ribbon(slide,
                   "No individual-level genotypes or phenotypes were downloaded; Bellenguez case/control counts are omitted because published bundle fields conflict.",
                   y=6.78, accent=BLUE)
        add_note(slide, "This table records each public dataset, its version or accession, and the question it was used to answer.")

        # 22 — thresholds and states
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • decision rules", APPENDIX_TITLES[3], 22,
                   accent=VERMILION,
                   subtitle="A result passed only when its P value was below the listed cutoff; a smaller P value means stronger statistical evidence.")
        thresholds = [
            ("AD / trait link", "P < 5×10⁻⁸"),
            ("Gene-activity link", "P < 0.05 / N tested"),
            ("Spinal-fluid gene test", "P < 8.77193×10⁻⁴"),
            ("Model assumptions", "10⁻⁴ / 10⁻⁴ / 5×10⁻⁶"),
            ("Strong shared signal", "Estimated probability ≥ 0.80"),
        ]
        for index, (label, value) in enumerate(thresholds):
            x = 0.55 + index * 2.47
            width = 2.26
            add_rect(slide, x, 1.27, width, 1.04, color=PALE_BLUE,
                     outline=BLUE)
            add_text(slide, label.upper(), x + 0.13, 1.43, width - 0.26,
                     0.20, size=8.8, color=BLUE, bold=True,
                     align=PP_ALIGN.CENTER)
            add_text(slide, value, x + 0.13, 1.79, width - 0.26, 0.28,
                     size=12.2, color=NAVY, bold=True,
                     align=PP_ALIGN.CENTER)
        states = [
            ("No match in selected sources", "The quick public-data screen found no direct match; this is not proof of absence."),
            ("No nearby AD signal", "The full tested DNA region did not pass the Alzheimer's cutoff."),
            ("No gene-activity signal", "The gene was measured but did not pass its gene-activity cutoff."),
            ("Could not test", "A measurement, complete file, model, or dataset description was unavailable."),
            ("Inputs did not match", "Both signals existed, but the two datasets could not be compared correctly."),
            ("Mitochondrial DNA", "Mitochondrial genes need a separate testing method."),
        ]
        for index, (state, meaning) in enumerate(states):
            col = index % 2
            row = index // 2
            x = 0.62 + col * 6.18
            y = 2.70 + row * 1.15
            accent = VERMILION if state in {"Could not test", "Inputs did not match"} else GRAY
            add_rect(slide, x, y, 5.86, 0.96, color=WHITE,
                     outline=LIGHT)
            add_rect(slide, x, y, 0.09, 0.96, color=accent,
                     outline=None, radius=False)
            add_text(slide, state, x + 0.25, y + 0.15, 2.50, 0.27,
                     size=11.3, color=NAVY, bold=True)
            add_text(slide, meaning, x + 2.72, y + 0.12, 2.83, 0.54,
                     size=9.8, color=DARK)
        add_ribbon(slide,
                   "PIP, VCP, and CL are scores from the source studies. PP.H4 estimates whether the disease and gene-activity signals share a DNA variant.",
                   y=6.63, accent=VERMILION)
        add_note(slide, "These cutoffs and result categories were decided before the gene results were reviewed.")

        # 23 — Tier 1 matrix
        slide = new_slide(prs)
        add_header(slide, "Appendix • full Tier 1 audit", APPENDIX_TITLES[4], 23,
                   accent=BLUE)
        add_picture_contain(slide, AUX["tier1_matrix"], 0.55, 1.18, 4.22, 5.88,
                            alt="Full first-screen evidence matrix for 47 gene–network settings")
        # The published matrix carries an internal analysis-number title. Mask
        # only that title band while preserving the complete 47-row matrix.
        add_rect(slide, 0.55, 1.18, 4.22, 0.17, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "First-screen matrix: 47 settings", 0.73, 1.205,
                 3.86, 0.12, size=7.8, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_rect(slide, 5.04, 1.34, 7.72, 4.86, color=WHITE, outline=LIGHT)
        add_text(slide, "COUNTS ACROSS 47 SETTINGS", 5.37, 1.67, 3.95, 0.24,
                 size=10.0, color=BLUE, bold=True)
        count_cards = [
            ("1", "Strong", "APOE", BLUE, PALE_BLUE),
            ("0", "Moderate", "None", TEAL, PALE_GREEN),
            ("3", "Limited", "COX7C ×2; SELENOW ×1", AMBER, PALE_AMBER),
            ("23", "No direct match", "16 nuclear genes", NO_SUPPORT, PALE_GRAY),
            ("20", "Could not test", "6 mitochondrial genes", GRAY, WHITE),
        ]
        for index, (value, label, detail, accent, bg) in enumerate(count_cards):
            row = index // 3
            col = index % 3
            x = 5.34 + col * 2.35
            y = 2.08 + row * 1.38
            width = 2.08
            add_rect(slide, x, y, width, 1.12, color=bg, outline=accent)
            add_text(slide, value, x + 0.14, y + 0.15, 0.62, 0.48,
                     size=21.0, color=accent, bold=True,
                     valign=MSO_ANCHOR.MIDDLE)
            add_text(slide, label, x + 0.79, y + 0.15, 1.12, 0.28,
                     size=10.5, color=NAVY, bold=True)
            add_text(slide, detail, x + 0.79, y + 0.55, 1.12, 0.34,
                     size=8.7, color=GRAY)
        add_text(slide,
                 "COX7C's two limited settings come from one public result, not two independent confirmations. The extra RPS15 study is not included here.",
                 5.38, 5.06, 6.92, 0.70, size=12.0, color=DARK)
        add_ribbon(slide,
                   "No direct public match does not mean no genetic role • could not test is not a negative result.",
                   y=6.52, accent=BLUE)
        add_source(slide, "Source: Tier 1 genetic_support_evidence_matrix.png and genetic_support_evidence_summary.tsv")
        add_note(slide, "Appendix reference: the complete 47-row formal evidence audit, retained as a dense matrix for lookup.")

        # 24 — recovery matrix and loci
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • Tier 2 recovery detail", APPENDIX_TITLES[5], 24,
                   accent=VERMILION)
        add_picture_contain(slide, AUX["recovery_matrix"], 0.45, 1.16, 4.20, 5.72,
                            alt="Detailed comparison outcomes across nuclear gene–network settings")
        add_rect(slide, 0.45, 1.43, 4.20, 0.30, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "Detailed comparison outcomes", 0.70, 1.515,
                 3.70, 0.13, size=7.8, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_picture_contain(slide, recovery_loci, 4.86, 1.32, 7.94, 4.76,
                            alt="Four regional AD locus plots for ANKRD11, APOE, COX7C, and RPS15")
        add_rect(slide, 5.13, 6.12, 7.42, 0.68, color=PALE_RED,
                 outline=VERMILION)
        add_text(slide,
                 "A strong nearby DNA signal identifies a region—not necessarily the named gene. No shared-signal probability was available.",
                 5.37, 6.30, 6.94, 0.28, size=11.5, color=NAVY,
                 bold=True, align=PP_ALIGN.CENTER)
        add_source(slide, "Source: recovery_evidence_matrix.png; recovery_locus_plots.pdf; recovery_route_decisions.tsv")
        add_note(slide, "Appendix reference: regional AD signals at four candidate windows did not resolve candidate-gene shared-signal analyses.")

        # 25 — APOE locus + CSF matrix and MAGMA table
        slide = new_slide(prs)
        add_header(slide, "Appendix • APOE detail", APPENDIX_TITLES[6], 25,
                   accent=BLUE)
        add_picture_contain(slide, apoe_locus, 0.55, 1.23, 7.55, 3.60,
                            alt="Tier 1 APOE locus plot showing direct rs429358 entries")
        add_picture_contain(slide, AUX["csf_matrix"], 8.42, 1.18, 4.30, 5.76,
                            alt="Spinal-fluid marker evidence for 19 nuclear genes across three biomarkers")
        add_rect(slide, 8.42, 1.55, 4.30, 0.32, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "Spinal-fluid marker evidence", 8.66, 1.64,
                 3.82, 0.14, size=7.6, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        # The published matrix includes an internal workflow label in its raster
        # footer. Keep the scientific panel unchanged while masking that label
        # in the external-facing deck.
        add_rect(slide, 8.42, 6.40, 4.30, 0.22, color=WHITE,
                 outline=None, radius=False)
        add_rect(slide, 0.67, 5.00, 7.18, 1.60, color=WHITE, outline=LIGHT)
        add_text(slide, "MARKER", 0.91, 5.18, 1.47, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "STRONGEST NEARBY P", 2.54, 5.18, 1.55, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "GENE-LEVEL P", 4.26, 5.18, 1.68, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "GENE + NEARBY DNA", 6.10, 5.18, 1.45, 0.21,
                 size=9.2, color=BLUE, bold=True)
        magma_rows = [
            ("Amyloid-β42", "stored as 0*", "5.0×10⁻¹⁰", "2.3037×10⁻¹⁴"),
            ("Total tau", "5.4×10⁻¹⁶¹", "5.0×10⁻¹⁰", "1.2218×10⁻¹³"),
            ("p-tau181", "3.27×10⁻¹⁷⁴", "5.0×10⁻¹⁰", "5.0×10⁻¹⁰"),
        ]
        for index, row in enumerate(magma_rows):
            y = 5.52 + index * 0.31
            for col, (x, width) in enumerate([(0.91, 1.47), (2.54, 1.55), (4.26, 1.68), (6.10, 1.45)]):
                add_text(slide, row[col], x, y, width, 0.22,
                         size=9.2, color=NAVY if col == 0 else DARK,
                         bold=(col == 0), valign=MSO_ANCHOR.MIDDLE)
        add_text(slide,
                 "* The amyloid-β42 value was too small for normal storage; it does not literally mean zero, so its region plot is excluded.",
                 0.91, 6.52, 6.52, 0.20, size=7.7, color=VERMILION,
                 italic=True)
        add_source(slide, "Source: Tier 1 common_variant_evidence.tsv.gz and locus plot page 1; CSF gate and MAGMA result tables")
        add_note(slide, "Appendix reference: APOE direct rs429358 mapping and the three CSF regional-plus-gene-based gate results. The malformed Aβ42 locus rendering is deliberately excluded.")

        # 26 — RPS15 audit
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • targeted public-data audit", APPENDIX_TITLES[7], 26,
                   accent=VERMILION)
        metrics = [
            ("37", "planned comparisons", BLUE),
            ("31", "comparisons measured", BLUE),
            ("6", "positive setting rows", AMBER),
            ("3", "unique mixed-brain results", AMBER),
            ("0", "completed shared-signal tests", VERMILION),
        ]
        for index, (value, label, accent) in enumerate(metrics):
            x = 0.57 + index * 2.52
            add_rect(slide, x, 1.29, 2.27, 1.06, color=PALE_GRAY,
                     outline=accent)
            add_text(slide, value, x + 0.14, 1.46, 0.67, 0.44,
                     size=23.0, color=accent, bold=True)
            add_text(slide, label, x + 0.87, 1.48, 1.20, 0.42,
                     size=10.2, color=NAVY, bold=True)
        tracks = [
            ("MSBB BA36 RNA-amount QTL", "P = 2.41403×10⁻⁷", "Adjusted for many tests: 0.00209909"),
            ("ROSMAP DLPFC RNA-splicing QTL", "P = 3.86842×10⁻³⁰", "Adjusted: 1.26188×10⁻²⁶ • variant probability: 1.0"),
            ("ROSMAP posterior-cingulate RNA-splicing QTL", "P = 3.30886×10⁻⁷", "Adjusted: 0.000858045 • variant probability: 0.910283"),
        ]
        for index, (track, p_value, detail) in enumerate(tracks):
            y = 2.78 + index * 1.02
            add_rect(slide, 0.72, y, 8.14, 0.78, color=WHITE, outline=LIGHT)
            add_rect(slide, 0.72, y, 0.09, 0.78, color=AMBER,
                     outline=None, radius=False)
            add_text(slide, track, 1.01, y + 0.13, 2.84, 0.30,
                     size=12.5, color=NAVY, bold=True)
            add_text(slide, p_value, 3.95, y + 0.13, 2.03, 0.30,
                     size=11.6, color=DARK, bold=True)
            add_text(slide, detail, 6.05, y + 0.10, 2.53, 0.52,
                     size=8.5, color=GRAY)
        add_rect(slide, 9.22, 2.78, 3.40, 2.82, color=PALE_RED,
                 outline=VERMILION, line_width=1.5)
        add_text(slide, "WHAT THIS DOES NOT SHOW", 9.52, 3.08, 2.79, 0.24,
                 size=10.0, color=VERMILION, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide,
                 "The six positive rows are the same three mixed-brain results repeated across OPC and inhibitory-neuron settings.\n\nOPC = oligodendrocyte precursor cell. The exact cell and gene link remain unconfirmed.\n\nNo shared-signal probability was available.",
                 9.54, 3.43, 2.76, 1.90, size=11.4, color=NAVY,
                 bold=True, align=PP_ALIGN.CENTER)
        add_ribbon(slide,
                   "Follow-up result: RPS15 is promising, but the exact gene and cell setting are not confirmed.",
                   y=6.35, accent=VERMILION)
        add_source(slide, "Source: opc_rps15_evidence_summary.tsv and opc_rps15_qtl_audit.tsv")
        add_note(slide, "The RPS15 follow-up measured 31 of 37 planned comparisons; three mixed-brain results repeated across two settings, and no final shared-signal test was completed.")

        # 27 — provenance and reproducibility
        slide = new_slide(prs)
        add_header(slide, "Appendix • file-quality checks", APPENDIX_TITLES[8], 27,
                   accent=VERMILION)
        caveats = [
            ("Damaged empty-result files", "Two files meant to contain zero rows are damaged even though their recorded file hashes match."),
            ("APOE protein files missing from list", "The report says four NG00130.v2 files were checked, but the published file inventory does not list them."),
            ("Large raw files not in project folder", "Some large inputs were streamed or stored outside the published project folder."),
            ("Old computer paths remain", "The RPS15 report still includes /home/... file paths from the computer where it was run."),
            ("Sample counts disagree", "Two result files report different Bellenguez case and control counts."),
            ("Nine rows have the wrong QTL label", "Nine rows call a gene-expression QTL a splicing QTL; the dataset registry labels it correctly."),
        ]
        for index, (title, body) in enumerate(caveats):
            col = index % 2
            row = index // 2
            x = 0.64 + col * 6.18
            y = 1.28 + row * 1.50
            add_rect(slide, x, y, 5.84, 1.24, color=WHITE, outline=LIGHT)
            add_rect(slide, x, y, 0.10, 1.24, color=VERMILION,
                     outline=None, radius=False)
            add_text(slide, title, x + 0.30, y + 0.18, 2.12, 0.30,
                     size=12.4, color=NAVY, bold=True)
            add_text(slide, body, x + 2.52, y + 0.15, 3.02, 0.75,
                     size=9.8, color=DARK)
        add_rect(slide, 1.76, 5.95, 9.82, 0.70, color=NAVY,
                 outline=TEAL, line_width=1.4)
        add_text(slide,
                 "Repair plan: rebuild damaged files • publish complete file lists • fix labels and paths • reconcile sample counts",
                 2.02, 6.15, 9.30, 0.28, size=12.0, color=WHITE,
                 bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "Status: the data package still needs repair", 4.36, 6.82,
                 4.64, 0.23, size=12.0, color=VERMILION,
                 bold=True, align=PP_ALIGN.CENTER)
        add_source(slide, "Source: genetic-support consolidated summary §5.3 and bundle-integrity audit")
        add_note(slide, "Appendix reference: known provenance and integrity limitations that should be repaired before the bundle is considered fully complete.")

        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = output_path.with_name(f".{output_path.name}.tmp")
        prs.save(temporary_output)
        os.replace(temporary_output, output_path)

    validate_deck(output_path)
    return output_path


def _all_slide_text(slide) -> str:
    values: list[str] = []
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False):
            values.append(shape.text)
    return "\n".join(values)


def validate_deck(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 100_000:
        raise AssertionError(f"Deck is missing or unexpectedly small: {path}")

    prs = Presentation(path)
    if len(prs.slides) != EXPECTED_SLIDE_COUNT:
        raise AssertionError(
            f"Expected {EXPECTED_SLIDE_COUNT} slides, found {len(prs.slides)}"
        )
    if prs.slide_width != SLIDE_W or prs.slide_height != SLIDE_H:
        raise AssertionError("Deck is not 13.333333 × 7.5 inch widescreen")

    all_text: list[str] = []
    picture_alt: list[str] = []
    for index, (slide, expected_title) in enumerate(zip(prs.slides, EXPECTED_TITLES), start=1):
        slide_text = _all_slide_text(slide)
        all_text.append(slide_text)
        normalized_slide_text = " ".join(slide_text.split())
        normalized_title = " ".join(expected_title.split())
        if normalized_title not in normalized_slide_text:
            raise AssertionError(f"Slide {index} is missing expected title: {expected_title}")
        note_text = slide.notes_slide.notes_text_frame.text.strip()
        if not note_text:
            raise AssertionError(f"Slide {index} has no speaker note")
        all_text.append(note_text)
        for shape in slide.shapes:
            tolerance = Inches(0.02)
            if shape.left < -tolerance or shape.top < -tolerance:
                raise AssertionError(f"Slide {index} has a shape outside the top/left bound")
            if shape.left + shape.width > SLIDE_W + tolerance:
                raise AssertionError(f"Slide {index} has a shape beyond the right bound")
            if shape.top + shape.height > SLIDE_H + tolerance:
                raise AssertionError(f"Slide {index} has a shape beyond the bottom bound")
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                props = shape._element.xpath(".//p:cNvPr")
                description = props[0].get("descr", "") if props else ""
                if not description:
                    raise AssertionError(f"Slide {index} contains an image without alt text")
                picture_alt.append(description)

    joined_text = "\n".join(all_text)
    forbidden = [
        "PP.H4 = 0", "PP.H4=0", "mtDNA genes were negative",
        "mtDNA genes tested negative", "validated mechanism", "proved causal",
        "Phase 18", "Phase 19", "phase18", "phase19",
    ]
    for phrase in forbidden:
        if phrase.lower() in joined_text.lower():
            raise AssertionError(f"Forbidden presentation wording found: {phrase}")

    expected_alt_fragments = [
        "Step-by-step workflow",
        "First-screen scorecard",
        "Spinal-fluid marker results",
        "Evidence summaries for COX7C",
        "Reasons each of 54 planned",
    ]
    for fragment in expected_alt_fragments:
        if not any(fragment in alt for alt in picture_alt):
            raise AssertionError(f"Missing required figure alt text: {fragment}")

    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise AssertionError("PPTX ZIP integrity check failed")
        media_members = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        media_hashes = {
            hashlib.sha256(archive.read(name)).hexdigest() for name in media_members
        }
        for label, source in FIG.items():
            if sha256(source) not in media_hashes:
                raise AssertionError(f"Required source figure is not embedded byte-for-byte: {label}")
        slide_members = [
            name for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
        if len(slide_members) != EXPECTED_SLIDE_COUNT:
            raise AssertionError(
                "PPTX package does not contain exactly "
                f"{EXPECTED_SLIDE_COUNT} slide XML parts"
            )
        presentation_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        ).lower()
        for internal_label in ("phase 18", "phase 19", "phase18", "phase19"):
            if internal_label in presentation_xml:
                raise AssertionError(
                    f"Internal phase label remains in presentation XML: {internal_label}"
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help=f"Output PPTX path (default: {DEFAULT_OUT})")
    parser.add_argument("--validate-only", action="store_true",
                        help="Validate an existing --output without rebuilding it")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.validate_only:
        validate_deck(args.output.resolve())
        print(f"Validated: {args.output.resolve()}")
    else:
        path = build_deck(args.output)
        print(f"Built and validated: {path}")


if __name__ == "__main__":
    main()
