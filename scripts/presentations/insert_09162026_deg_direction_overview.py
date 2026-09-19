#!/usr/bin/env python3
"""Refresh the ROSMAP OXPHOS-direction slide in the reviewed deck.

The figure summarizes mtDNA-encoded and nuclear-DNA-encoded structural OXPHOS
gene direction across the six sex/APOE groups. Counts are derived from the
effective Phase 20 mitochondrial DEG lists used for subsequent KDA. The slide
is located by title because it now belongs inside the pathway-analysis section.
All other slides and the reviewed ordering are preserved.
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

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "deg_direction_overview_mpl")
)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
PRESENTATION_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(PRESENTATION_SCRIPTS))
import update_phase11_seaad_simple_aggr_part2 as ui  # noqa: E402

SKILL_SCRIPTS = ROOT / ".agents/skills/scientific-visualization/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from figure_export import save_publication_figure  # noqa: E402
from style_presets import apply_publication_style  # noqa: E402


DEFAULT_DECK = (
    ROOT
    / "docs"
    / "presentations"
    / "09162026"
    / "09162026_sex_apoe_kda_fine_broad.pptx"
)
AUDIT_ROOT = ROOT / "results" / "presentations" / "09162026_deg_direction"
QUERY_PATH = (
    ROOT
    / "results"
    / "minerva_production"
    / "20_sex_apoe_kda_combo"
    / "combo_query_members.tsv.gz"
)
MODULE_PATH = ROOT / "config" / "phase13_respiratory_modules.tsv"

EXPECTED_SLIDE_COUNTS = {49, 50, 52, 157, 158, 159}
NEW_TITLE = "OXPHOS gene directions vary across sex/APOE groups"
LEGACY_TITLE = "Mitochondrial energy-gene directions vary across sex/APOE groups"
SUBTITLE = (
    "OXPHOS (oxidative phosphorylation) is the mitochondrial process that makes "
    "most cellular ATP."
)
DENOMINATOR_TEXT = (
    "% = share of gene-by-fine-cell DEG occurrences in the dominant direction; "
    "a gene can recur across comparisons."
)
GROUP_ORDER = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
GROUP_LABELS = [
    "Female\nε2",
    "Female\nε3/ε3",
    "Female\nε4",
    "Male\nε2",
    "Male\nε3/ε3",
    "Male\nε4",
]
MODULES = {
    "Mitochondrial DNA": "mtdna_oxphos_13",
    "Nuclear DNA": "nuclear_oxphos_structural_86",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-root", type=Path, default=AUDIT_ROOT)
    parser.add_argument(
        "--figure-only",
        action="store_true",
        help="Render and validate figure artifacts without modifying the deck.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().isin({"TRUE", "T", "1", "YES"})


def prepare_plot_data() -> pd.DataFrame:
    for path in (QUERY_PATH, MODULE_PATH):
        if not path.is_file():
            raise FileNotFoundError(path)

    queries = pd.read_csv(QUERY_PATH, sep="\t", low_memory=False)
    modules = pd.read_csv(MODULE_PATH, sep="\t")
    queries = queries.loc[
        truth(queries["effective_member"])
        & truth(queries["included_at_thresholds"])
    ].copy()
    queries["up"] = truth(queries["in_upregulated_query"])
    queries["down"] = truth(queries["in_downregulated_query"])

    rows: list[dict[str, Any]] = []
    for label, module_id in MODULES.items():
        genes = set(
            modules.loc[
                modules["module_id"].eq(module_id), "current_approved_symbol"
            ]
        )
        subset = queries.loc[queries["gene"].isin(genes)]
        counts = (
            subset.groupby("signature_group")[["up", "down"]]
            .sum()
            .reindex(GROUP_ORDER)
        )
        if counts.isna().any().any():
            raise RuntimeError(f"Missing group counts for {module_id}")
        for group in GROUP_ORDER:
            up = int(counts.loc[group, "up"])
            down = int(counts.loc[group, "down"])
            total = up + down
            if total == 0:
                raise RuntimeError(f"No directional observations for {module_id} {group}")
            if up >= down:
                dominant_direction = "higher_in_ad"
                dominant_count = up
                signed_percent = 100.0 * up / total
            else:
                dominant_direction = "lower_in_ad"
                dominant_count = down
                signed_percent = -100.0 * down / total
            rows.append(
                {
                    "signature_group": group,
                    "group_label": GROUP_LABELS[GROUP_ORDER.index(group)].replace(
                        "\n", " "
                    ),
                    "gene_source": label,
                    "module_id": module_id,
                    "up_count": up,
                    "down_count": down,
                    "total_appearances": total,
                    "dominant_direction": dominant_direction,
                    "dominant_percent": abs(signed_percent),
                    "signed_dominant_percent": signed_percent,
                    "dominant_count": dominant_count,
                }
            )

    frame = pd.DataFrame(rows)
    expected = {
        ("F_e2", "Mitochondrial DNA"): (127, 1),
        ("F_e33", "Mitochondrial DNA"): (217, 0),
        ("F_e4", "Mitochondrial DNA"): (26, 38),
        ("M_e2", "Mitochondrial DNA"): (13, 119),
        ("M_e33", "Mitochondrial DNA"): (70, 11),
        ("M_e4", "Mitochondrial DNA"): (87, 23),
        ("F_e2", "Nuclear DNA"): (239, 4),
        ("F_e33", "Nuclear DNA"): (76, 13),
        ("F_e4", "Nuclear DNA"): (10, 206),
        ("M_e2", "Nuclear DNA"): (63, 404),
        ("M_e33", "Nuclear DNA"): (8, 60),
        ("M_e4", "Nuclear DNA"): (34, 55),
    }
    observed = {
        (row.signature_group, row.gene_source): (row.up_count, row.down_count)
        for row in frame.itertuples()
    }
    if observed != expected:
        raise RuntimeError(f"Directional counts changed: {observed!r}")
    return frame


def render_figure(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style("presentation")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "axes.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(12.0, 4.25), constrained_layout=False)
    fig.subplots_adjust(left=0.105, right=0.985, top=0.82, bottom=0.22)
    positions = np.arange(len(GROUP_ORDER), dtype=float)
    width = 0.34
    colors = {"Mitochondrial DNA": "#0072B2", "Nuclear DNA": "#D55E00"}
    hatches = {"Mitochondrial DNA": "", "Nuclear DNA": "///"}

    for offset, source in ((-width / 2, "Mitochondrial DNA"), (width / 2, "Nuclear DNA")):
        subset = (
            frame.loc[frame["gene_source"].eq(source)]
            .set_index("signature_group")
            .reindex(GROUP_ORDER)
        )
        values = subset["signed_dominant_percent"].to_numpy(dtype=float)
        bars = ax.bar(
            positions + offset,
            values,
            width=width * 0.90,
            color=colors[source],
            edgecolor="#FFFFFF" if source == "Mitochondrial DNA" else "#5A3A2A",
            linewidth=0.9,
            hatch=hatches[source],
            zorder=3,
        )
        for bar, value in zip(bars, values, strict=True):
            y = value - 8.5 if value > 0 else value + 8.5
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y,
                f"{abs(value):.0f}%",
                ha="center",
                va="center",
                fontsize=11.5,
                fontweight="bold",
                color="white",
                zorder=4,
            )

    ax.axhline(0, color="#4B5563", linewidth=1.2, zorder=2)
    ax.axvline(2.5, color="#D1D5DB", linewidth=1.1, zorder=1)
    ax.set_xlim(-0.65, 5.65)
    ax.set_ylim(-112, 112)
    ax.set_xticks(positions)
    ax.set_xticklabels(GROUP_LABELS, fontsize=12.0, fontweight="bold")
    for index, tick in enumerate(ax.get_xticklabels()):
        if index in {1, 4}:
            tick.set_color("#5B3A87")
    ax.set_yticks([-100, -50, 0, 50, 100])
    ax.set_yticklabels(
        ["100% lower", "50% lower", "0", "50% higher", "100% higher"],
        fontsize=10.2,
    )
    ax.set_ylabel("Share of OXPHOS gene occurrences", fontsize=12.0)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    legend = ax.legend(
        handles=[
            Patch(
                facecolor=colors["Mitochondrial DNA"],
                edgecolor="white",
                label="13 OXPHOS genes encoded by mitochondrial DNA",
            ),
            Patch(
                facecolor=colors["Nuclear DNA"],
                edgecolor="#5A3A2A",
                hatch=hatches["Nuclear DNA"],
                label="86 structural OXPHOS genes encoded by nuclear DNA",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=2,
        frameon=False,
        fontsize=11.0,
        handlelength=1.7,
        columnspacing=2.4,
    )
    for text_item in legend.get_texts():
        text_item.set_color("#1F2937")

    base = output_dir / "rosmap_deg_direction_by_sex_apoe"
    saved = save_publication_figure(
        fig,
        base,
        formats=["png", "svg", "pdf"],
        dpi=350,
        bbox_inches="tight",
        pad_inches=0.05,
    )
    plt.close(fig)
    paths = {path.suffix.lstrip("."): path for path in saved}
    data_path = base.with_name(base.name + "_plot_data.tsv")
    frame.to_csv(data_path, sep="\t", index=False, lineterminator="\n")
    paths["data"] = data_path
    for role, path in paths.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty {role} artifact: {path}")
    return paths


def slide_title(slide) -> str:
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False) and shape.text.strip():
            return " ".join(shape.text.split())
    return ""


def slide_fingerprint(slide) -> tuple[Any, ...]:
    notes = slide.notes_slide.notes_text_frame
    return (
        tuple(
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
        ),
        notes.text if notes is not None else "",
    )


def build_slide(prs: Presentation, figure_path: Path):
    slide = ui.new_slide(prs)
    ui.add_title_block(
        slide,
        NEW_TITLE,
        SUBTITLE,
    )
    ui.add_text(
        slide,
        DENOMINATOR_TEXT,
        0.72,
        1.18,
        11.90,
        0.30,
        size=10.8,
        color=ui.MID,
        align=PP_ALIGN.CENTER,
    )
    ui.add_picture_contain(
        slide,
        figure_path,
        0.67,
        1.25,
        12.00,
        4.88,
        alt=(
            "Diverging paired bar chart of dominant Alzheimer’s disease direction "
            "for the 13 mitochondrial-DNA-encoded OXPHOS genes and 86 "
            "nuclear-DNA-encoded structural OXPHOS genes across female and male "
            "APOE epsilon-2, epsilon-3 homozygous, and epsilon-4 groups."
        ),
    )
    ui.add_rect(slide, 0.72, 6.18, 11.90, 0.70, color=ui.PALE_GRAY, outline=None)
    ui.add_text(
        slide,
        "Key contrast",
        1.02,
        6.39,
        1.22,
        0.25,
        size=12.0,
        color=ui.PURPLE,
        bold=True,
    )
    ui.add_text(
        slide,
        "Female ε3/ε3: both OXPHOS sets mostly rise; male ε3/ε3: mitochondrial-encoded genes rise while nuclear-encoded genes fall.",
        2.35,
        6.34,
        9.82,
        0.34,
        size=13.8,
        color=ui.DARK,
        valign=MSO_ANCHOR.MIDDLE,
    )
    ui.add_notes(
        slide,
        goal="Give an overall view of OXPHOS DEG direction across sex/APOE groups.",
        walkthrough=(
            "OXPHOS, or oxidative phosphorylation, is the mitochondrial process "
            "that produces most cellular ATP. Blue bars summarize the 13 OXPHOS "
            "genes encoded by mitochondrial DNA, and striped orange bars summarize "
            "86 structural OXPHOS genes encoded by nuclear DNA. The denominator is "
            "the number of gene-by-fine-cell occurrences from the eligible DEG "
            "lists for that sex/APOE group and gene set. The same gene can therefore "
            "be counted again in another fine-cell comparison. Each bar reports the "
            "percentage of those occurrences in whichever direction was more common: "
            "above zero for more RNA in Alzheimer’s disease and below zero for less. "
            "Female epsilon-2 is strongly "
            "up in both gene groups. Female epsilon-3 homozygous is also up in both, "
            "with a complete mitochondrial-DNA direction. Female epsilon-4 and male "
            "epsilon-2 are mostly down. Male epsilon-3 homozygous shows the clearest "
            "split between the two genomes, while male epsilon-4 shows a weaker split."
        ),
        boundary=(
            "The percentages are not percent expression change, percent of cells or "
            "donors, percent of unique genes, an effect size, pathway enrichment, "
            "OXPHOS activity, or a direct statistical interaction between disease, "
            "sex, and APOE."
        ),
        transition=(
            "Focus first on the female epsilon-3 homozygous mitochondrial increase."
        ),
    )
    return slide


def set_shape_text(slide, shape_name: str, value: str) -> None:
    matches = [shape for shape in slide.shapes if shape.name == shape_name]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one shape named {shape_name!r}, found {len(matches)}"
        )
    frame = matches[0].text_frame
    first = frame.paragraphs[0]
    if first.runs:
        first.runs[0].text = value
        for run in first.runs[1:]:
            run.text = ""
    else:
        first.add_run().text = value
    for paragraph in list(frame.paragraphs[1:]):
        paragraph._element.getparent().remove(paragraph._element)


def sync_existing_slide(slide, figure_path: Path) -> None:
    """Apply reviewed terminology, denominator text, and regenerated chart."""
    set_shape_text(slide, "TextBox 1", NEW_TITLE)
    set_shape_text(
        slide,
        "TextBox 2",
        SUBTITLE,
    )
    set_shape_text(
        slide,
        "TextBox 6",
        "Female ε3/ε3: both OXPHOS sets mostly rise; male ε3/ε3: mitochondrial-encoded genes rise while nuclear-encoded genes fall.",
    )
    for shape in list(slide.shapes):
        if shape.shape_type == 13:
            shape._element.getparent().remove(shape._element)
    ui.add_picture_contain(
        slide,
        figure_path,
        0.67,
        1.25,
        12.00,
        4.88,
        alt=(
            "Diverging paired bar chart of dominant Alzheimer’s disease direction "
            "for the 13 mitochondrial-DNA-encoded OXPHOS genes and 86 "
            "nuclear-DNA-encoded structural OXPHOS genes across female and male "
            "APOE epsilon-2, epsilon-3 homozygous, and epsilon-4 groups."
        ),
    )
    denominator_shapes = [
        shape
        for shape in slide.shapes
        if getattr(shape, "has_text_frame", False)
        and "gene-by-fine-cell DEG occurrences" in shape.text
    ]
    if not denominator_shapes:
        ui.add_text(
            slide,
            DENOMINATOR_TEXT,
            0.72,
            1.18,
            11.90,
            0.30,
            size=10.8,
            color=ui.MID,
            align=PP_ALIGN.CENTER,
        )
    elif len(denominator_shapes) == 1:
        set_shape_text(slide, denominator_shapes[0].name, DENOMINATOR_TEXT)
    else:
        raise RuntimeError("Multiple denominator definitions found on slide 4")
    removed_footer = (
        "Descriptive summary of separately analyzed groups—not a direct test that "
        "sex/APOE changes the AD effect."
    )
    for shape in list(slide.shapes):
        if (
            getattr(shape, "has_text_frame", False)
            and " ".join(shape.text.split()) == " ".join(removed_footer.split())
        ):
            shape._element.getparent().remove(shape._element)


def validate_deck(
    prs: Presentation, preserved: tuple[Any, ...], overview_index: int
) -> None:
    if len(prs.slides) not in EXPECTED_SLIDE_COUNTS:
        raise RuntimeError("Unexpected output slide count")
    if slide_title(prs.slides[overview_index]) != NEW_TITLE:
        raise RuntimeError("OXPHOS direction slide was not found at the reviewed position")
    after_existing = tuple(
        slide_fingerprint(slide)
        for index, slide in enumerate(prs.slides)
        if index != overview_index
    )
    if after_existing != preserved:
        raise RuntimeError("An existing slide changed during insertion")
    slide = prs.slides[overview_index]
    visible_text = "\n".join(
        shape.text
        for shape in slide.shapes
        if getattr(shape, "has_text_frame", False)
    )
    if SUBTITLE not in visible_text:
        raise RuntimeError("OXPHOS definition is missing from the overview slide")
    if DENOMINATOR_TEXT not in visible_text:
        raise RuntimeError("Percentage denominator is missing from the overview slide")
    if "energy gene" in visible_text.lower() or "energy-gene" in visible_text.lower():
        raise RuntimeError("Vague energy-gene terminology remains on the overview slide")
    if "Descriptive summary of separately analyzed groups" in visible_text:
        raise RuntimeError("The removed bottom disclaimer was restored")
    notes = slide.notes_slide.notes_text_frame
    if notes is None or not notes.text.strip():
        raise RuntimeError("The overview slide is missing speaker notes")
    for shape in slide.shapes:
        if (
            shape.left < 0
            or shape.top < 0
            or shape.left + shape.width > prs.slide_width + 10
            or shape.top + shape.height > prs.slide_height + 10
        ):
            raise RuntimeError(f"Out-of-bounds shape: {shape.name}")


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_root = args.audit_root.resolve()
    frame = prepare_plot_data()
    artifacts = render_figure(frame, audit_root / "figures")
    if args.figure_only:
        print(f"Rendered figure: {artifacts['png']}")
        return 0
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    input_hash = sha256(input_path)
    prs = Presentation(input_path)
    titles = [slide_title(slide) for slide in prs.slides]
    overview_indices = [
        index
        for index, title in enumerate(titles)
        if title in {NEW_TITLE, LEGACY_TITLE}
    ]
    if len(prs.slides) not in EXPECTED_SLIDE_COUNTS or len(overview_indices) != 1:
        raise RuntimeError(
            f"Unexpected deck state: {len(prs.slides)} slides and "
            f"{sum(title in {NEW_TITLE, LEGACY_TITLE} for title in titles)} overview slides"
        )
    overview_index = overview_indices[0]
    preserved = tuple(
        slide_fingerprint(slide)
        for index, slide in enumerate(prs.slides)
        if index != overview_index
    )
    sync_existing_slide(prs.slides[overview_index], artifacts["png"])
    action = "Updated"
    validate_deck(prs, preserved, overview_index)

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
        validate_deck(reopened, preserved, overview_index)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print(f"Updated deck: {output_path}")
    print(f"{action} slide: {overview_index + 1}")
    print(f"Figure: {artifacts['png']}")
    print(f"Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
