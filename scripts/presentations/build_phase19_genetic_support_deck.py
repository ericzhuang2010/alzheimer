#!/usr/bin/env python3
"""Build the Phase 19 human-genetic-support presentation.

The deck follows ``phase19_presentation_slide_design.md`` and embeds the five
validated, slide-native Phase 19 figures.  The main story is ten slides; eight
appendix slides preserve candidate lists, methods, dense matrices, and
provenance caveats for discussion.
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
    "Human genetic support for network-derived key drivers",
    "The genetic analysis asks a narrower question than the network analysis",
    "A frozen, gated design prevents overinterpretation",
    "Only APOE achieved strong formal support",
    "APOE has convergent AD and CSF biomarker evidence",
    "Non-APOE signals remain suggestive, regional, or unresolved",
    "All 54 Tier 2 routes stopped before a valid shared-signal analysis",
    "No support has three non-equivalent meanings",
    "The next work should resolve key loci, then broaden mechanisms",
    "Human genetics narrows the candidate landscape without closing it",
]

APPENDIX_TITLES = [
    "The frozen candidate set contains 47 contexts across seven networks",
    "Each dataset answers a different part of the genetic-support question",
    "Frozen thresholds preserve distinct terminal-state meanings",
    "The full Tier 1 matrix preserves every candidate-context result",
    "Regional AD loci were detected, but no route reached a valid H0–H4 result",
    "APOE direct AD evidence converges with all three CSF traits",
    "RPS15 remains the highest-priority unresolved non-APOE candidate",
    "The published bundle is auditable but not yet fully complete",
]

MAIN_NOTES = [
    "This analysis tested whether network-derived key drivers also have inherited human-genetic support; it did not retest or rerank the upstream network analysis.",
    "The two phases provide complementary evidence and should not be expected to return identical rankings.",
    "The design was intentionally conservative and distinguishes a measured negative from missing or incompatible inputs.",
    "Formal support is concentrated in one gene; most other rows are either unsupported by this screen or not testable with the chosen data. COX7C's two weak rows derive from one source record, and the supplemental RPS15 audit was not integrated into the formal 47-row grade.",
    "APOE is strongly supported as an AD gene, but this analysis does not establish that the association acts through the exact astrocyte mechanism nominated by the network analysis.",
    "Significant regional association alone does not identify which gene mediates the locus.",
    "The main bottleneck was upstream evidence and input completeness, not a series of completed colocalizations favoring distinct signals.",
    "Current negative evidence lowers confidence in a simple common cis-germline mechanism; it does not refute a downstream or state-specific functional role.",
    "The immediate scientific opportunity is resolving APOE and RPS15 with complete, signal-aware molecular-QTL packages.",
    "This is a disciplined genetic annotation of the network-derived list, not broad genetic validation or rejection of the network drivers.",
]


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
    add_header(slide, "Human genetics • main result", title, page_no, accent=accent)
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


def build_deck(output_path: Path = DEFAULT_OUT) -> Path:
    for path in [*FIG.values(), *AUX.values()]:
        if not path.exists():
            raise FileNotFoundError(path)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    prs.core_properties.title = "Human Genetic Support for Network-Derived Key Drivers"
    prs.core_properties.subject = "Public-data genetic-support assessment of 25 network-derived candidates"
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
        add_text(slide, "HUMAN GENETIC SUPPORT", 0.76, 0.67,
                 7.2, 0.28, size=11.5, color=SKY, bold=True)
        add_text(slide, "Human genetic support\nfor network-derived key drivers",
                 0.76, 1.25, 8.25, 1.78, size=34.0, color=WHITE,
                 bold=True, valign=MSO_ANCHOR.MIDDLE)
        add_text(slide,
                 "Public-data evaluation of 25 genes across 47 gene-by-network contexts",
                 0.78, 3.38, 7.75, 0.62, size=17.0,
                 color=RGBColor(210, 224, 239))
        add_rect(slide, 0.78, 4.30, 7.68, 0.06, color=BLUE,
                 outline=None, radius=False)
        add_text(slide,
                 "Inherited support is concentrated in APOE; several non-APOE loci remain suggestive or unresolved.",
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

        add_chip(slide, "APOE — strong", 0.78, 6.15, 3.30,
                 accent=BLUE, bg=PALE_BLUE)
        add_chip(slide, "COX7C / SELENOW — weak", 4.32, 6.15, 4.05,
                 accent=AMBER, bg=PALE_AMBER)
        add_chip(slide, "RPS15 — promising, unresolved", 8.62, 6.15, 4.00,
                 accent=VERMILION, bg=PALE_RED)
        add_text(slide, "Public-data update • 21 August 2026", 0.78, 7.03,
                 4.2, 0.18, size=8.5, color=RGBColor(145, 171, 197))
        add_note(slide, MAIN_NOTES[0])

        # 2 — complementary questions
        slide = new_slide(prs)
        add_header(slide, "Framing", MAIN_TITLES[1], 2, accent=TEAL)
        add_rect(slide, 0.73, 1.42, 4.95, 2.04, color=PALE_GREEN,
                 outline=TEAL, line_width=1.5)
        add_text(slide, "NETWORK ANALYSIS", 1.03, 1.72, 2.10, 0.26,
                 size=11.0, color=TEAL, bold=True)
        add_text(slide, "Network-associated key drivers", 1.03, 2.08,
                 4.28, 0.40, size=18.5, color=NAVY, bold=True)
        add_text(slide, "47 contexts  •  25 unique genes", 1.03, 2.78,
                 4.25, 0.32, size=15.5, color=GRAY, bold=True)

        add_connector(slide, 5.85, 2.44, 7.30, 2.44, color=BLUE, width=2.5)
        add_text(slide, "complementary\nevidence", 5.76, 2.69, 1.61, 0.62,
                 size=10.0, color=MID, bold=True, align=PP_ALIGN.CENTER)

        add_rect(slide, 7.45, 1.42, 5.13, 2.04, color=PALE_BLUE,
                 outline=BLUE, line_width=1.5)
        add_text(slide, "GENETIC ANALYSIS", 7.77, 1.72, 2.10, 0.26,
                 size=11.0, color=BLUE, bold=True)
        add_text(slide, "Inherited human-genetic support", 7.77, 2.08,
                 4.45, 0.40, size=18.5, color=NAVY, bold=True)
        add_text(slide, "19 nuclear genes tested  •  6 mtDNA genes need a separate design",
                 7.77, 2.78, 4.45, 0.48, size=12.5, color=GRAY, bold=True)

        add_bullets(slide, [
            "The network analysis identifies genes central to disease-associated network modules.",
            "The genetic analysis asks whether AD or endophenotype associations map to a candidate—and share a QTL signal when compatible inputs exist.",
            "Biological network importance need not imply inherited susceptibility.",
        ], 1.02, 4.15, 11.25, size=16.0, accent=BLUE, line_h=0.69)
        add_ribbon(slide,
                   "Genetic evidence annotates the frozen candidate set; it does not rerank the network analysis.",
                   y=6.42, accent=TEAL)
        add_source(slide, "Source: genetic-support consolidated summary §1.1; call_key_driver_returns.tsv")
        add_note(slide, MAIN_NOTES[1])

        # 3–7 — all five newly generated figures, full-width and untrimmed.
        add_figure_slide(
            prs, page_no=3, title=MAIN_TITLES[2], figure=FIG["workflow"],
            alt="Parallel genetic-support workflow: direct public-summary screening and gated nuclear regional-QTL analysis",
            source="Source: generated workflow package; analysis contracts, registries, and route manifests",
            note=MAIN_NOTES[2],
            ribbon="A route stops at the first failed requirement; arrows describe analysis flow, not a causal mechanism.",
            accent=BLUE,
        )
        add_figure_slide(
            prs, page_no=4, title=MAIN_TITLES[3], figure=FIG["tier1"],
            alt="Formal Tier 1 scorecard for all 47 candidate-context rows",
            source="Source: Tier 1 genetic_support_evidence_summary.tsv and genetic_support_status.tsv",
            note=MAIN_NOTES[3],
            ribbon="Supplemental RPS15 audit: weak/suggestive; not integrated into the formal 47-row grade.",
            accent=BLUE,
        )
        add_figure_slide(
            prs, page_no=5, title=MAIN_TITLES[4], figure=FIG["csf"],
            alt="CSF trait-level gate decisions showing APOE as the only positive gene across all three traits",
            source="Source: CSF endophenotype_gate_decisions.tsv and MAGMA candidate-gene results",
            note=MAIN_NOTES[4],
            ribbon="Direct AD evidence: rs429358, inclusion 1.0, P ≈ 1.88×10⁻¹⁵⁵ • exact astrocyte mechanism remains unresolved.",
            accent=BLUE,
        )
        add_figure_slide(
            prs, page_no=6, title=MAIN_TITLES[5], figure=FIG["non_apoe"],
            alt="Evidence cards for COX7C, SELENOW, RPS15, and ANKRD11",
            source="Source: generated non-APOE plot data; Tier 1, recovery, RPS15 audit, and CSF result bundles",
            note=MAIN_NOTES[5],
            ribbon="Regional P values are locus evidence—not candidate-gene assignment or cross-gene effect-size ranks.",
            accent=AMBER,
        )
        add_figure_slide(
            prs, page_no=7, title=MAIN_TITLES[6], figure=FIG["tier2"],
            alt="Mutually exclusive terminal outcomes across 54 prespecified Tier 2 eQTL and sQTL routes",
            source="Source: Tier 2 recovery_route_decisions.tsv and header-only recovery_colocalization.tsv.gz",
            note=MAIN_NOTES[6],
            ribbon="The 42 / 4 / 2 / 6 states are terminal categories; zero valid analyses means PP.H4 is unavailable.",
            accent=VERMILION,
        )

        # 8 — interpret negative evidence
        slide = new_slide(prs)
        add_header(slide, "Interpretation", MAIN_TITLES[7], 8, accent=VERMILION)
        cards = [
            (
                "01", "Signal-negative",
                "15 of 19 nuclear genes lacked a clinical-AD regional signal at P < 5×10⁻⁸.\n\nAll 18 non-APOE nuclear genes failed the CSF gates.",
                NO_SUPPORT, PALE_GRAY,
            ),
            (
                "02", "Technically unresolved",
                "Complete candidate-QTL models, variant order, or source-matched LD were missing.\n\nExact-cell QTL data were sparse, unavailable, or context-mismatched.",
                VERMILION, PALE_RED,
            ),
            (
                "03", "Outside this design",
                "mtDNA, rare/structural variation, trans regulation, interactions, disease stage, progression, resilience, and post-transcriptional mechanisms.",
                GRAY, WHITE,
            ),
        ]
        add_three_column_cards(slide, cards, y=1.42, h=4.75)
        add_ribbon(slide, "The six mtDNA genes were not tested negatively.",
                   y=6.40, accent=VERMILION)
        add_source(slide, "Source: recovery_regional_gwas_summary.tsv; CSF gate decisions; Tier 1 mtDNA evidence states")
        add_note(slide, MAIN_NOTES[7])

        # 9 — roadmap
        slide = new_slide(prs)
        add_header(slide, "Next steps", MAIN_TITLES[8], 9, accent=TEAL)
        roadmap = [
            (
                "01", "Resolve APOE and RPS15",
                "Complete signal-aware QTL models\n+ source-matched LD\n+ larger exact-cell eQTL / sQTL",
                VERMILION, PALE_RED,
            ),
            (
                "02", "Broaden nuclear mechanisms",
                "Candidate-frozen pQTL / PWAS / TWAS\n+ rare variants and interactions\n+ more phenotypes and ancestries",
                BLUE, PALE_BLUE,
            ),
            (
                "03", "Separate and validate",
                "Dedicated mtDNA analysis\n+ independent network replication\n+ perturbation and rescue",
                TEAL, PALE_GREEN,
            ),
        ]
        add_three_column_cards(slide, roadmap, y=1.50, h=4.55)
        for index in range(2):
            start_x = 4.58 + index * 4.10
            add_connector(slide, start_x, 3.83, start_x + 0.45, 3.83,
                          color=BLUE, width=2.0)
        add_ribbon(slide,
                   "Highest-value next step: complete, matched molecular-QTL packages for APOE and RPS15.",
                   y=6.37, accent=TEAL)
        add_source(slide, "Source: genetic-support consolidated summary §6.2; bundle-repair actions are detailed in the appendix")
        add_note(slide, MAIN_NOTES[8])

        # 10 — close
        slide = new_slide(prs, bg=NAVY)
        add_rect(slide, 0, 0, 13.333, 7.5, color=NAVY, outline=None,
                 radius=False)
        add_text(slide, "HUMAN GENETICS • TAKE-HOME", 0.72, 0.50, 4.5, 0.26,
                 size=10.5, color=SKY, bold=True)
        add_text(slide, MAIN_TITLES[9], 0.72, 0.92, 11.8, 0.75,
                 size=29.0, color=WHITE, bold=True)
        takeaways = [
            ("01", "APOE", "Strong, convergent gene-level support.", BLUE),
            ("02", "COX7C + SELENOW", "Weak/suggestive summary evidence.", AMBER),
            ("03", "RPS15 + ANKRD11", "Highest-priority unresolved; locus-only, respectively.", VERMILION),
            ("04", "No new validated gene", "Outcomes mix tested negatives, unavailable inputs, and out-of-design mechanisms.", TEAL),
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
        add_text(slide, "full_genetic_support_complete = FALSE", 3.76, 5.96,
                 5.81, 0.31, size=15.5, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide,
                 "Disciplined genetic annotation—not broad validation or rejection of network drivers.",
                 2.15, 6.78, 9.03, 0.30, size=12.5,
                 color=RGBColor(173, 197, 220), align=PP_ALIGN.CENTER)
        add_text(slide, "10", 12.42, 0.32, 0.36, 0.20,
                 size=9, color=RGBColor(145, 171, 197), bold=True,
                 align=PP_ALIGN.RIGHT)
        add_note(slide, MAIN_NOTES[9])

        # 11 — appendix candidate list
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • candidate freeze", APPENDIX_TITLES[0], 11,
                   accent=TEAL)
        headers = ["Broad network", "MT-driver class (rank order)", "Non-MT-driver class (rank order)"]
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
                   "‘MT driver’ is an upstream signature class; COX7C and UQCR10 are nuclear genes. Six listed genes are encoded by mtDNA.",
                   y=6.83, accent=TEAL)
        add_note(slide, "Appendix reference: the exact frozen upstream top-five display set, retained without genetic reranking.")

        # 12 — dataset inventory
        slide = new_slide(prs)
        add_header(slide, "Appendix • data inventory", APPENDIX_TITLES[1], 12,
                   accent=BLUE)
        inventory = [
            ("Candidate freeze", "Upstream KDA • GENCODE v44 • HGNC 2026-06-05", "Fix 47 contexts; map symbols and GRCh38 intervals"),
            ("Direct summary", "FunGen-xQTL snapshot f6f63fc…", "AD fine mapping, xQTL, TWAS/GVC membership screen"),
            ("Clinical AD", "Bellenguez • GCST90027158", "Complete ±1 Mb nuclear candidate regions"),
            ("Brain QTL", "NG00184.v1 • eQTL Catalogue r7", "eQTL/sQTL coverage, signal, models, and context fallback"),
            ("CSF traits", "GCST90726396 / 397 / 398 • N=18,948 each", "Aβ42, total tau, and p-tau181 regional + MAGMA gates"),
            ("Targeted audits", "NG00130.v2 APOE pQTL • local NG00184 RPS15", "Follow up APOE mechanism and unresolved RPS15 routes"),
        ]
        x_values = [0.55, 2.72, 7.44]
        widths = [2.17, 4.72, 5.34]
        for col, header in enumerate(["Layer", "Dataset / version", "Why it was used"]):
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
        add_note(slide, "Appendix reference: versions, accessions, and the specific analytical role of each public source.")

        # 13 — thresholds and states
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • frozen decision rules", APPENDIX_TITLES[2], 13,
                   accent=VERMILION)
        thresholds = [
            ("GWAS", "P < 5×10⁻⁸"),
            ("Dense QTL", "P < 0.05 / N tested"),
            ("CSF MAGMA", "P < 8.77193×10⁻⁴"),
            ("Coloc priors", "10⁻⁴ / 10⁻⁴ / 5×10⁻⁶"),
            ("Strong shared signal", "H4 and conditional H4 ≥ 0.80"),
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
            ("none_found", "No direct support in the registered screen; not proof of absence."),
            ("no_regional_gwas_signal", "Complete tested region failed the frozen GWAS gate."),
            ("no_regional_qtl_signal", "Gene was measured but failed its prespecified QTL gate."),
            ("not_assessable", "Measurement, complete statistics, model, or release metadata unavailable."),
            ("model_or_ld_incompatible", "Both signals existed, but the shared-signal model could not run."),
            ("not_applicable_mtdna", "Nuclear GWAS/QTL framework is not applicable to mtDNA."),
        ]
        for index, (state, meaning) in enumerate(states):
            col = index % 2
            row = index // 2
            x = 0.62 + col * 6.18
            y = 2.70 + row * 1.15
            accent = VERMILION if "incompatible" in state or "assessable" in state else GRAY
            add_rect(slide, x, y, 5.86, 0.96, color=WHITE,
                     outline=LIGHT)
            add_rect(slide, x, y, 0.09, 0.96, color=accent,
                     outline=None, radius=False)
            add_text(slide, state, x + 0.25, y + 0.15, 2.50, 0.27,
                     size=11.3, color=NAVY, bold=True)
            add_text(slide, meaning, x + 2.72, y + 0.12, 2.83, 0.54,
                     size=9.8, color=DARK)
        add_ribbon(slide,
                   "PIP, credible-set membership, inclusion scores, VCP, and CL labels retain their source meanings; none is renamed PP.H4.",
                   y=6.63, accent=VERMILION)
        add_note(slide, "Appendix reference: frozen gates and mutually distinct terminal states used throughout the genetic-support analysis.")

        # 14 — Tier 1 matrix
        slide = new_slide(prs)
        add_header(slide, "Appendix • full Tier 1 audit", APPENDIX_TITLES[3], 14,
                   accent=BLUE)
        add_picture_contain(slide, AUX["tier1_matrix"], 0.55, 1.18, 4.22, 5.88,
                            alt="Full Tier 1 evidence matrix for 47 network-derived candidate contexts")
        # The published matrix carries an internal analysis-number title. Mask
        # only that title band while preserving the complete 47-row matrix.
        add_rect(slide, 0.55, 1.18, 4.22, 0.17, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "Tier 1 candidate-context matrix", 0.73, 1.205,
                 3.86, 0.12, size=7.8, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_rect(slide, 5.04, 1.34, 7.72, 4.86, color=WHITE, outline=LIGHT)
        add_text(slide, "FORMAL CONTEXT-LEVEL COUNTS", 5.37, 1.67, 3.95, 0.24,
                 size=10.0, color=BLUE, bold=True)
        count_cards = [
            ("1", "Strong", "APOE", BLUE, PALE_BLUE),
            ("0", "Moderate", "None", TEAL, PALE_GREEN),
            ("3", "Weak", "COX7C ×2; SELENOW ×1", AMBER, PALE_AMBER),
            ("23", "No direct mapping", "16 nuclear genes", NO_SUPPORT, PALE_GRAY),
            ("20", "Not assessable", "6 mtDNA genes", GRAY, WHITE),
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
                 "COX7C's two weak contexts derive from one public source record; they are not independent replications. RPS15 remains outside this formal grade.",
                 5.38, 5.06, 6.92, 0.70, size=12.0, color=DARK)
        add_ribbon(slide,
                   "No direct mapping ≠ no genetic role • not assessable ≠ a negative result.",
                   y=6.52, accent=BLUE)
        add_source(slide, "Source: Tier 1 genetic_support_evidence_matrix.png and genetic_support_evidence_summary.tsv")
        add_note(slide, "Appendix reference: the complete 47-row formal evidence audit, retained as a dense matrix for lookup.")

        # 15 — recovery matrix and loci
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • Tier 2 recovery detail", APPENDIX_TITLES[4], 15,
                   accent=VERMILION)
        add_picture_contain(slide, AUX["recovery_matrix"], 0.45, 1.16, 4.20, 5.72,
                            alt="Tier 2 recovery evidence matrix across nuclear candidate contexts")
        add_rect(slide, 0.45, 1.43, 4.20, 0.30, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "Tier 2 recovery matrix", 0.70, 1.515,
                 3.70, 0.13, size=7.8, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        add_picture_contain(slide, recovery_loci, 4.86, 1.32, 7.94, 4.76,
                            alt="Four regional AD locus plots for ANKRD11, APOE, COX7C, and RPS15")
        add_rect(slide, 5.13, 6.12, 7.42, 0.68, color=PALE_RED,
                 outline=VERMILION)
        add_text(slide,
                 "Regional significance is locus evidence only. All positive routes have PP.H4 unavailable.",
                 5.37, 6.30, 6.94, 0.28, size=11.5, color=NAVY,
                 bold=True, align=PP_ALIGN.CENTER)
        add_source(slide, "Source: recovery_evidence_matrix.png; recovery_locus_plots.pdf; recovery_route_decisions.tsv")
        add_note(slide, "Appendix reference: regional AD signals at four candidate windows did not resolve candidate-gene shared-signal analyses.")

        # 16 — APOE locus + CSF matrix and MAGMA table
        slide = new_slide(prs)
        add_header(slide, "Appendix • APOE detail", APPENDIX_TITLES[5], 16,
                   accent=BLUE)
        add_picture_contain(slide, apoe_locus, 0.55, 1.23, 7.55, 3.60,
                            alt="Tier 1 APOE locus plot showing direct rs429358 entries")
        add_picture_contain(slide, AUX["csf_matrix"], 8.42, 1.18, 4.30, 5.76,
                            alt="CSF evidence matrix for 19 nuclear candidates across three biomarkers")
        add_rect(slide, 8.42, 1.55, 4.30, 0.32, color=WHITE,
                 outline=None, radius=False)
        add_text(slide, "CSF endophenotype genetic evidence", 8.66, 1.64,
                 3.82, 0.14, size=7.6, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        # The published matrix includes an internal workflow label in its raster
        # footer. Keep the scientific panel unchanged while masking that label
        # in the external-facing deck.
        add_rect(slide, 8.42, 6.40, 4.30, 0.22, color=WHITE,
                 outline=None, radius=False)
        add_rect(slide, 0.67, 5.00, 7.18, 1.60, color=WHITE, outline=LIGHT)
        add_text(slide, "CSF TRAIT", 0.91, 5.18, 1.47, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "REGIONAL MIN P", 2.54, 5.18, 1.55, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "MAGMA GENE BODY", 4.26, 5.18, 1.68, 0.21,
                 size=9.2, color=BLUE, bold=True)
        add_text(slide, "MAGMA ±10 KB", 6.10, 5.18, 1.45, 0.21,
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
                 "* Numerical underflow in the stored regional minimum; do not use the current Aβ42 locus rendering.",
                 0.91, 6.52, 6.52, 0.20, size=7.7, color=VERMILION,
                 italic=True)
        add_source(slide, "Source: Tier 1 common_variant_evidence.tsv.gz and locus plot page 1; CSF gate and MAGMA result tables")
        add_note(slide, "Appendix reference: APOE direct rs429358 mapping and the three CSF regional-plus-gene-based gate results. The malformed Aβ42 locus rendering is deliberately excluded.")

        # 17 — RPS15 audit
        slide = new_slide(prs, bg=WHITE)
        add_header(slide, "Appendix • targeted public-data audit", APPENDIX_TITLES[6], 17,
                   accent=VERMILION)
        metrics = [
            ("37", "eligible routes", BLUE),
            ("31", "measured routes", BLUE),
            ("6", "positive context rows", AMBER),
            ("3", "distinct bulk tracks", AMBER),
            ("0", "resolved H0–H4 analyses", VERMILION),
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
            ("MSBB BA36 eQTL", "P = 2.41403×10⁻⁷", "FDR = 0.00209909"),
            ("ROSMAP DLPFC sQTL", "P = 3.86842×10⁻³⁰", "FDR = 1.26188×10⁻²⁶ • max PIP = 1.0"),
            ("ROSMAP posterior-cingulate sQTL", "P = 3.30886×10⁻⁷", "FDR = 0.000858045 • max PIP = 0.910283"),
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
            add_text(slide, detail, 6.05, y + 0.13, 2.53, 0.38,
                     size=9.8, color=GRAY)
        add_rect(slide, 9.22, 2.78, 3.40, 2.82, color=PALE_RED,
                 outline=VERMILION, line_width=1.5)
        add_text(slide, "INTERPRETIVE BOUNDARY", 9.52, 3.08, 2.79, 0.24,
                 size=10.0, color=VERMILION, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide,
                 "The six positive rows are the same three bulk tracks repeated across OPC and inhibitory-neuron contexts.\n\nExact contexts and gene-level shared signal remain unresolved.\n\nPP.H4 is unavailable.",
                 9.54, 3.55, 2.76, 1.67, size=12.1, color=NAVY,
                 bold=True, align=PP_ALIGN.CENTER)
        add_ribbon(slide,
                   "Supplemental outcome: weak/suggestive public support only; RPS15 and its exact contexts are not validated.",
                   y=6.35, accent=VERMILION)
        add_source(slide, "Source: opc_rps15_evidence_summary.tsv and opc_rps15_qtl_audit.tsv")
        add_note(slide, "Appendix reference: the RPS15 audit measured 31 of 37 eligible routes; three bulk-brain tracks recur across two candidate contexts, with no resolved primary H0–H4 analysis.")

        # 18 — provenance and reproducibility
        slide = new_slide(prs)
        add_header(slide, "Appendix • reproducibility", APPENDIX_TITLES[7], 18,
                   accent=VERMILION)
        caveats = [
            ("Malformed empty outputs", "Two declared zero-row Tier 2 gzip files are truncated despite matching the manifest hashes."),
            ("APOE pQTL inventory gap", "The report states four NG00130.v2 files were checksum-verified; the published inventory does not enumerate them."),
            ("Raw sources not in checkout", "Large downloaded inputs were streamed or retained outside the repository publication bundle."),
            ("Nonportable paths", "The RPS15 report retains absolute /home/... paths from its execution environment."),
            ("GWAS metadata conflict", "Bellenguez case/control counts disagree between the recovery manifest and regional summaries."),
            ("QTD000579 mislabeled", "Nine sensitivity rows call Walker neocortex eQTL an sQTL; the registry and route manifest identify it correctly."),
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
                 "Repair path: regenerate malformed files • publish checksums/inventories • fix labels/paths • reconcile metadata",
                 2.02, 6.15, 9.30, 0.28, size=12.0, color=WHITE,
                 bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "full_genetic_support_complete = FALSE", 4.92, 6.82,
                 3.52, 0.23, size=12.0, color=VERMILION,
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
    if len(prs.slides) != 18:
        raise AssertionError(f"Expected 18 slides, found {len(prs.slides)}")
    if prs.slide_width != SLIDE_W or prs.slide_height != SLIDE_H:
        raise AssertionError("Deck is not 13.333333 × 7.5 inch widescreen")

    expected_titles = MAIN_TITLES + APPENDIX_TITLES
    all_text: list[str] = []
    picture_alt: list[str] = []
    for index, (slide, expected_title) in enumerate(zip(prs.slides, expected_titles), start=1):
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
        "Parallel genetic-support workflow",
        "Formal Tier 1 scorecard",
        "CSF trait-level gate decisions",
        "Evidence cards for COX7C",
        "Mutually exclusive terminal outcomes",
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
        if len(slide_members) != 18:
            raise AssertionError("PPTX package does not contain exactly 18 slide XML parts")
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
