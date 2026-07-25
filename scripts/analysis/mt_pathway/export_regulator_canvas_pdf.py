#!/usr/bin/env python3
"""Render the mitochondrial regulator Canvas analysis as a print-ready PDF.

Run without modifying the project environment:

    uv run --with reportlab python \
      scripts/analysis/mt_pathway/export_regulator_canvas_pdf.py
"""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#52606D")
BLUE = colors.HexColor("#2E79B5")
BLUE_LIGHT = colors.HexColor("#DCEBF7")
GREEN = colors.HexColor("#1F8A65")
GREEN_LIGHT = colors.HexColor("#DCEFE9")
RED = colors.HexColor("#C04848")
RED_LIGHT = colors.HexColor("#F5DEDE")
AMBER = colors.HexColor("#A66B14")
AMBER_LIGHT = colors.HexColor("#F7ECD8")
BORDER = colors.HexColor("#CBD2D9")
SURFACE = colors.HexColor("#F5F7FA")
WHITE = colors.white

COMPARISONS = (
    ("female_vs_male_all_apoe", "Sex: F vs M (all APOE)"),
    ("e2_vs_e33_all_sexes", "APOE: e2 vs e33"),
    ("e4_vs_e33_all_sexes", "APOE: e4 vs e33"),
    ("female_vs_male_e2", "Sex within e2"),
    ("female_vs_male_e33", "Sex within e33"),
    ("female_vs_male_e4", "Sex within e4"),
)

STRATA = ("F_e2x", "F_e33", "F_e4x", "M_e2x", "M_e33", "M_e4x")
HEATMAP_GENES = ("ATP5IF1", "TUFM", "HSPD1", "TOMM7", "FKBP8")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--output",
        type=Path,
        default=root
        / "docs"
        / "analysis"
        / "mt_pathway"
        / "mitochondrial_regulator_prioritization.pdf",
    )
    return parser.parse_args()


def build_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            textColor=INK,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=MUTED,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontSize=8.7,
            leading=12.5,
            textColor=INK,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=7.1,
            leading=9.5,
            textColor=MUTED,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["BodyText"],
            fontSize=7,
            leading=8.5,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CellSmall",
            parent=styles["BodyText"],
            fontSize=6.3,
            leading=7.6,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CenterCell",
            parent=styles["Cell"],
            alignment=1,
        )
    )
    return styles


class ScoreBars(Flowable):
    def __init__(self, rows: list[dict[str, str]], width: int = 690, height: int = 245):
        super().__init__()
        self.rows = rows
        self.width = width
        self.height = height

    def draw(self) -> None:
        canvas = self.canv
        label_width = 78
        chart_width = self.width - 125
        row_height = (self.height - 25) / len(self.rows)
        for tick in (0, 25, 50, 75, 100):
            x = label_width + chart_width * tick / 100
            canvas.setStrokeColor(colors.HexColor("#E4E7EB"))
            canvas.line(x, 15, x, self.height - 8)
            canvas.setFillColor(MUTED)
            canvas.setFont("Helvetica", 6.5)
            canvas.drawCentredString(x, 3, str(tick))
        for index, row in enumerate(self.rows):
            y = self.height - 20 - (index + 1) * row_height + 4
            score = float(row["balanced_score"])
            canvas.setFillColor(INK)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawRightString(label_width - 6, y + 3, row["gene"])
            canvas.setFillColor(BLUE_LIGHT)
            canvas.roundRect(label_width, y, chart_width, 9, 2, fill=1, stroke=0)
            canvas.setFillColor(BLUE)
            canvas.roundRect(
                label_width,
                y,
                chart_width * score / 100,
                9,
                2,
                fill=1,
                stroke=0,
            )
            canvas.setFillColor(INK)
            canvas.setFont("Helvetica", 7)
            canvas.drawString(label_width + chart_width + 5, y + 2.5, f"{score:.1f}")
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawCentredString(
            label_width + chart_width / 2,
            -7,
            "Integrated evidence score (0-100)",
        )


class EffectHeatmap(Flowable):
    def __init__(self, data: dict[str, list[float]], width: int = 690, height: int = 150):
        super().__init__()
        self.data = data
        self.width = width
        self.height = height

    @staticmethod
    def fill(value: float):
        if abs(value) < 0.05:
            return SURFACE
        base = GREEN if value > 0 else RED
        alpha = 0.18 + 0.55 * min(abs(value) / 0.9, 1)
        return colors.Color(
            1 - (1 - base.red) * alpha,
            1 - (1 - base.green) * alpha,
            1 - (1 - base.blue) * alpha,
        )

    def draw(self) -> None:
        canvas = self.canv
        labels = ("F-e2", "F-e33", "F-e4", "M-e2", "M-e33", "M-e4")
        label_width = 80
        cell_width = (self.width - label_width) / 6
        row_height = 21
        top = self.height - 24
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica-Bold", 7)
        for index, label in enumerate(labels):
            canvas.drawCentredString(
                label_width + index * cell_width + cell_width / 2,
                top + 8,
                label,
            )
        for row_index, gene in enumerate(HEATMAP_GENES):
            y = top - (row_index + 1) * row_height
            canvas.setFillColor(INK)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawRightString(label_width - 6, y + 6, gene)
            for column_index, value in enumerate(self.data[gene]):
                x = label_width + column_index * cell_width
                canvas.setFillColor(self.fill(value))
                canvas.setStrokeColor(WHITE)
                canvas.rect(x, y, cell_width - 1, row_height - 1, fill=1, stroke=1)
                canvas.setFillColor(INK)
                canvas.setFont(
                    "Helvetica-Bold" if abs(value) >= 0.3 else "Helvetica",
                    7,
                )
                canvas.drawCentredString(
                    x + (cell_width - 1) / 2,
                    y + 6,
                    f"{value:+.2f}",
                )
        canvas.setFillColor(GREEN_LIGHT)
        canvas.rect(label_width, 0, 11, 8, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(label_width + 15, 1, "AD higher")
        canvas.setFillColor(RED_LIGHT)
        canvas.rect(label_width + 70, 0, 11, 8, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.drawString(label_width + 85, 1, "AD lower")


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def pathway_summary(root: Path) -> list[list[object]]:
    rows = []
    path = (
        root
        / "results"
        / "minerva_production"
        / "11_pathway"
        / "similarity_tail_pathway_ora.tsv.gz"
    )
    with gzip.open(path, "rt", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if (
                row["analysis_universe"] == "core_mito"
                and row["tail"] == "low_score"
                and row["test_status"] == "tested"
            ):
                rows.append(row)
    summary = []
    for comparison, label in COMPARISONS:
        focused = [
            row
            for row in rows
            if row["comparison_id"] == comparison
            and row["pathway_collection"] == "mitocarta_mitopathways_v3_0"
        ]
        primary = [
            row
            for row in rows
            if row["comparison_id"] == comparison
            and row["pathway_collection"] == "msigdb_c2_cp_v2026_1"
        ]
        top = min(focused, key=lambda row: float(row["tail_fdr_bh"]))
        summary.append(
            [
                label,
                sum(row["tail_fdr_significant"].lower() == "true" for row in focused),
                top["pathway_name"],
                float(top["tail_fdr_bh"]),
                float(top["fold_enrichment"]),
                sum(row["tail_fdr_significant"].lower() == "true" for row in primary),
            ]
        )
    return summary


def render(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    output = args.output.resolve()
    data_dir = root / "docs" / "analysis" / "mt_pathway"
    candidates = load_tsv(data_dir / "pre_network_shortlist.tsv")
    strata_rows = load_tsv(data_dir / "pre_network_shortlist_strata.tsv")
    pathways = pathway_summary(root)
    styles = build_styles()

    def paragraph(text: str, style: str = "BodyCustom"):
        return Paragraph(text, styles[style])

    def callout(
        title: str,
        body: str,
        background=AMBER_LIGHT,
        border=AMBER,
    ):
        table = Table(
            [[paragraph(f"<b>{title}</b><br/>{body}")]],
            colWidths=[9.65 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), background),
                    ("BOX", (0, 0), (-1, -1), 0.8, border),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return table

    def footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(
            document.leftMargin,
            0.42 * inch,
            landscape(letter)[0] - document.rightMargin,
            0.42 * inch,
        )
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(
            document.leftMargin,
            0.25 * inch,
            "Mitochondrial regulator prioritization | Canvas PDF | July 25, 2026",
        )
        canvas.drawRightString(
            landscape(letter)[0] - document.rightMargin,
            0.25 * inch,
            f"Page {document.page}",
        )
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=landscape(letter),
        leftMargin=0.46 * inch,
        rightMargin=0.46 * inch,
        topMargin=0.42 * inch,
        bottomMargin=0.55 * inch,
        title="Mitochondrial regulator prioritization",
        author="ROSMAP mitochondrial analysis project",
    )
    story = [
        paragraph("MITOCHONDRIAL ANALYSIS | PRE-NETWORK NOMINATION", "Small"),
        paragraph("Mitochondrial regulator prioritization", "TitleCustom"),
        paragraph(
            "A first-pass ranking from mitochondrial DEGs, cross-stratum "
            "similarity tails, pathway enrichment, and curated mitochondrial "
            "control roles.",
            "Subtitle",
        ),
        callout(
            "Interpretation boundary",
            "The current data nominate regulators; they do not establish key "
            "drivers. A key-driver call requires directed neighborhood enrichment "
            "in the lab's cell-type Bayesian networks.",
        ),
        Spacer(1, 9),
    ]
    summary = Table(
        [
            [
                paragraph("<b>1,195</b><br/>core-mito candidates", "CenterCell"),
                paragraph("<b>321 / 324</b><br/>modeled AD-NCI contexts", "CenterCell"),
                paragraph("<b>0</b><br/>gene-level similarity FDR hits", "CenterCell"),
                paragraph("<b>6 / 6</b><br/>OXPHOS-enriched comparisons", "CenterCell"),
            ]
        ],
        colWidths=[2.4 * inch] * 4,
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story += [
        summary,
        Spacer(1, 12),
        paragraph("Local evidence score by regulatory-control candidate", "Section"),
        paragraph(
            "Scores integrate DEG recurrence/effect, cross-context divergence, "
            "pathway-query support, and data coverage. They are ranks, not "
            "probabilities or p-values.",
            "Small",
        ),
        ScoreBars(candidates[:10]),
        paragraph(
            "Source: Phase 09 DEGs + Phase 10 low-similarity ranks + Phase 11 "
            "ORA; production validated July 23, 2026.",
            "Small",
        ),
        PageBreak(),
    ]
    insights = (
        (
            "ATP5IF1",
            "Strongest strict local candidate: 34 significant contexts, 8/9 broad "
            "lineages, all six divergent tails, and membership in every significant "
            "focused OXPHOS query.",
        ),
        (
            "TUFM | TOMM7 | FKBP8",
            "Mechanistically diverse bridge from the OXPHOS phenotype to translation, "
            "PINK1/Parkin entry, and receptor-mediated mitophagy.",
        ),
        (
            "HSPD1",
            "All 22 significant female-APOE4 contexts are down; median log2FC "
            "across all 54 modeled clusters is -0.89.",
        ),
        (
            "Shared reversal",
            "Top candidates tend to be higher in female-APOE2 AD but lower in "
            "female-APOE4 and/or male-APOE2 AD.",
        ),
    )
    insight_table = Table(
        [
            [paragraph(f"<b>{label}</b>", "Cell"), paragraph(text, "Cell")]
            for label, text in insights
        ],
        colWidths=[1.75 * inch, 7.9 * inch],
    )
    insight_table.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 2, BLUE),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, SURFACE]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story += [
        paragraph("What stands out", "Section"),
        insight_table,
        PageBreak(),
        paragraph("Candidate-level evidence", "Section"),
    ]

    headers = (
        "Rank",
        "Gene",
        "Score",
        "DE contexts",
        "Lineages",
        "Strata",
        "Low tails",
        "Control program / role",
    )
    candidate_rows = []
    for row in candidates:
        role = row["control_programs"].replace("_", " ") or row["hgnc_name"]
        candidate_rows.append(
            [
                row["shortlist_rank"],
                row["gene"],
                f"{float(row['balanced_score']):.1f}",
                row["deg_contexts"],
                f"{row['deg_lineages']}/9",
                f"{row['deg_strata']}/6",
                f"{row['low_tail_comparisons']}/6",
                paragraph(role, "CellSmall"),
            ]
        )
    candidate_table = Table(
        [list(headers)] + candidate_rows,
        colWidths=[
            0.55 * inch,
            1.0 * inch,
            0.6 * inch,
            0.8 * inch,
            0.7 * inch,
            0.6 * inch,
            0.7 * inch,
            4.65 * inch,
        ],
        repeatRows=1,
    )
    candidate_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SURFACE]),
                ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 1), (6, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    effects = {}
    for gene in HEATMAP_GENES:
        by_stratum = {
            row["yu_stratum"]: float(row["median_logFC_all"])
            for row in strata_rows
            if row["gene"] == gene
        }
        effects[gene] = [by_stratum[stratum] for stratum in STRATA]
    story += [
        candidate_table,
        PageBreak(),
        paragraph("Median AD-NCI effect by sex/APOE stratum", "Section"),
        paragraph(
            "Cells show median log2 fold-change across every modeled fine "
            "cell type; positive values indicate AD higher than NCI.",
            "Small",
        ),
        EffectHeatmap(effects),
        paragraph(
            "Source: Phase 09 MAST, all modeled fine-cell contexts; "
            "ROSMAP postmortem cohort.",
            "Small",
        ),
        Spacer(1, 8),
        callout(
            "Validation contrast",
            "<b>Start with female APOE4 excitatory neurons and astrocytes</b> "
            "(26 AD, 11 NCI donors). Use female APOE2 as the reversal arm "
            "(8 AD, 17 NCI). Treat male APOE2 as replication because it has "
            "only 7 AD and 6 NCI donors.",
            BLUE_LIGHT,
            BLUE,
        ),
        PageBreak(),
        paragraph("Pathway phenotype is consistent and downstream-heavy", "Section"),
        paragraph(
            "Every low-similarity comparison enriches MitoCarta OXPHOS subunits. "
            "This validates the phenotype but explains why structural ETC genes "
            "dominate naive rankings."
        ),
    ]

    pathway_headers = (
        "Comparison",
        "Sig. MitoPathways",
        "Top focused pathway",
        "Top FDR",
        "Fold",
        "Sig. C2:CP",
    )
    pathway_rows = [
        [
            paragraph(row[0], "Cell"),
            row[1],
            paragraph(row[2], "Cell"),
            f"{row[3]:.1e}",
            f"{row[4]:.2f}x",
            row[5],
        ]
        for row in pathways
    ]
    pathway_table = Table(
        [[paragraph(f"<b>{header}</b>", "CellSmall") for header in pathway_headers]]
        + pathway_rows,
        colWidths=[
            2.4 * inch,
            1.0 * inch,
            3.0 * inch,
            0.85 * inch,
            0.7 * inch,
            0.85 * inch,
        ],
        repeatRows=1,
    )
    pathway_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SURFACE]),
                ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story += [
        pathway_table,
        paragraph(
            "Source: Phase 11 core_mito bottom-200 ORA; MitoCarta 3.0 and "
            "MSigDB C2:CP 2026.1.",
            "Small",
        ),
        Spacer(1, 12),
        paragraph("Recommended first experimental panel", "Section"),
    ]
    experiments = (
        (
            "Primary perturbation screen",
            "ATP5IF1 | TUFM | TOMM7 | FKBP8 | HSPD1",
            "Best combination of local recurrence, control-point biology, "
            "cross-stratum divergence, and external disease evidence.",
        ),
        (
            "Paired cristae mechanism",
            "CHCHD2 | CHCHD10",
            "Both are locally strong in all six tails; perturb together because "
            "functional redundancy may mask single-gene effects.",
        ),
        (
            "Canonical pathway controls",
            "PINK1 | PHB2",
            "Lower local rank but established mitophagy anchors for TOMM7/FKBP8 "
            "perturbations.",
        ),
        (
            "Molecular readouts",
            "MT-ND2 | COX4I1 | COX5B | ATP5F1E",
            "Strong downstream phenotype markers; measure them without calling "
            "them upstream drivers.",
        ),
    )
    experiment_table = Table(
        [
            [
                paragraph(f"<b>{label}</b>", "Cell"),
                paragraph(f"<b>{genes}</b><br/>{reason}", "Cell"),
            ]
            for label, genes, reason in experiments
        ],
        colWidths=[2.0 * inch, 7.65 * inch],
    )
    experiment_table.setStyle(
        TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLUE_LIGHT, WHITE]),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story += [
        experiment_table,
        Spacer(1, 7),
        paragraph(
            "<b>Suggested readouts:</b> basal/maximal OCR, ATP, membrane "
            "potential, mitochondrial ROS, mitophagy flux, cristae morphology, "
            "and transcript/protein levels for MT-ND2 plus representative "
            "Complex I/IV/V subunits."
        ),
        PageBreak(),
        paragraph("External evidence that changes priority", "Section"),
    ]
    external = (
        (
            "ATP5IF1",
            "A 2026 human-brain study reports hippocampal loss of protective IF1 "
            "in sporadic AD.",
            "https://doi.org/10.3390/ijms27062816",
        ),
        (
            "TUFM",
            "Loss links mitochondrial ROS to BACE1/A-beta, apoptosis, and tau "
            "phosphorylation.",
            "https://doi.org/10.1096/fj.202002461r",
        ),
        (
            "FKBP8",
            "A 2024 study connects phospho-tau to impaired FKBP8-mediated "
            "mitophagy.",
            "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0307358",
        ),
        (
            "TOMM7",
            "A genome-wide screen identifies TOMM7 as required for PINK1 "
            "stabilization and Parkin recruitment.",
            "https://pubmed.ncbi.nlm.nih.gov/24270810/",
        ),
        (
            "HSPD1",
            "Human AD mtUPR data support disease involvement; the local "
            "female-e4 direction suggests loss of compensation.",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5977398/",
        ),
    )
    for gene, text, url in external:
        story.append(
            paragraph(
                f'<b>{gene}:</b> {text} '
                f'<link href="{url}" color="#2E79B5">Source</link>'
            )
        )
    story += [Spacer(1, 9), paragraph("Decision gate for key driver", "Section")]
    gates = (
        "Map the 54 fine clusters to each available cell-type Bayesian network.",
        "Project pathway- and contrast-specific mitochondrial DEG signatures.",
        "Test directed 1-3 hop neighborhoods and BH-correct across candidate hubs.",
        "Require replication in coexpression modules and donor-level pseudobulk.",
        "Add AD GWAS/eQTL/TWAS evidence as an orthogonal score, not a substitute "
        "for KDA.",
    )
    for index, gate in enumerate(gates, start=1):
        story.append(paragraph(f"<b>{index}.</b> {gate}"))
    story += [
        callout(
            "Keep the label strict",
            'Until this gate is passed, use "candidate regulator" or '
            '"pre-network priority," not "key driver."',
        ),
        Spacer(1, 10),
        paragraph("Reproducible sources", "Section"),
        paragraph(
            "<b>Canvas:</b> mitochondrial-regulator-prioritization.canvas.tsx",
            "Small",
        ),
        paragraph(
            "<b>Script:</b> "
            "scripts/analysis/mt_pathway/prioritize_mitochondrial_regulators.py",
            "Small",
        ),
        paragraph(
            "<b>Score tables:</b> docs/analysis/mt_pathway/",
            "Small",
        ),
    ]
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


def main() -> None:
    render(parse_args())


if __name__ == "__main__":
    main()
