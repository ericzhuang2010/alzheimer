#!/usr/bin/env python3
"""Plot Section 2 mitochondrial and OXPHOS directional DEG burden.

The script reads the evidence table from:

    docs/analysis/phase11_phase12_joint_mitochondrial_discussion.md

It produces publication-oriented SVG, PDF, and PNG files plus the exact
plotted values as a TSV. AD-down percentages are displayed to the left of
zero, but the exported percentages remain nonnegative rates.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

FIGURE_CACHE_ROOT = Path(tempfile.gettempdir()) / "alzheimer_figure_cache"
(FIGURE_CACHE_ROOT / "matplotlib").mkdir(parents=True, exist_ok=True)
(FIGURE_CACHE_ROOT / "xdg").mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(FIGURE_CACHE_ROOT / "matplotlib"),
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    str(FIGURE_CACHE_ROOT / "xdg"),
)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import transforms
    from matplotlib.patches import Patch
    from matplotlib.patches import Rectangle
    from matplotlib.text import Text
    from matplotlib.ticker import FuncFormatter
except ImportError as exc:
    raise SystemExit(
        "This script requires matplotlib. Install it in the active Python "
        "environment before rerunning."
    ) from exc


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[3]
DEFAULT_SOURCE = (
    PROJECT_ROOT
    / "docs"
    / "analysis"
    / "phase11_phase12_joint_mitochondrial_discussion.md"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results" / "figures" / "analysis"
DEFAULT_BASENAME = "section02_mitochondrial_oxphos_directional_burden"

COLOR_UP = "#D55E00"
COLOR_DOWN = "#0072B2"
COLOR_TEXT = "#202020"
COLOR_MUTED = "#5A5A5A"
COLOR_GRID = "#D8D8D8"
COLOR_SHADE = "#F5F5F5"

EXPECTED_HEADER = [
    "Stratum",
    "Mitochondrial DEG occurrences / tested",
    "AD up / down",
    "OXPHOS occurrences / tested",
    "OXPHOS up / down",
]

STRATUM_ORDER = [
    "Female ε2",
    "Male ε2",
    "Female ε3/ε3",
    "Male ε3/ε3",
    "Female ε4",
    "Male ε4",
]

Y_POSITIONS = {
    "Female ε2": 7.0,
    "Male ε2": 6.0,
    "Female ε3/ε3": 4.0,
    "Male ε3/ε3": 3.0,
    "Female ε4": 1.0,
    "Male ε4": 0.0,
}


@dataclass(frozen=True)
class TableRow:
    stratum: str
    sex: str
    apoe_group: str
    mitochondrial_significant: int
    mitochondrial_tested: int
    mitochondrial_up: int
    mitochondrial_down: int
    oxphos_significant: int
    oxphos_tested: int
    oxphos_up: int
    oxphos_down: int


@dataclass(frozen=True)
class PlotRow:
    stratum: str
    sex: str
    apoe_group: str
    gene_set: str
    significant_occurrences: int
    tested_occurrences: int
    ad_up_occurrences: int
    ad_down_occurrences: int
    ad_up_pct_tested: float
    ad_down_pct_tested: float
    significant_pct_tested: float
    ad_up_pct_significant: float


@dataclass(frozen=True)
class DirectionAnnotation:
    """A directional count label and the bar that constrains its placement."""

    text: Text
    bar: Rectangle
    direction: str
    endpoint: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the Section 2 diverging-bar figure from the joint "
            "mitochondrial discussion table."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Markdown source containing the Section 2 evidence table.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for rendered figures and companion files.",
    )
    parser.add_argument(
        "--basename",
        default=DEFAULT_BASENAME,
        help="Output filename stem.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG resolution in dots per inch (default: 300).",
    )
    return parser.parse_args()


def absolute_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def parse_integer_pair(value: str, field_name: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*([\d,]+)\s*/\s*([\d,]+)\s*", value)
    if match is None:
        raise ValueError(f"Could not parse {field_name!r} value: {value!r}")
    return tuple(int(item.replace(",", "")) for item in match.groups())


def section_two_lines(source_text: str) -> list[str]:
    lines = source_text.splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("## 2. AD-associated OXPHOS direction")
        ),
        None,
    )
    if start is None:
        raise ValueError("Could not find the Section 2 heading in the source")
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("## 3.")
        ),
        len(lines),
    )
    return lines[start:end]


def markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_section_two_table(source_path: Path) -> list[TableRow]:
    if not source_path.is_file():
        raise FileNotFoundError(f"Source Markdown does not exist: {source_path}")
    section_lines = section_two_lines(source_path.read_text(encoding="utf-8"))
    header_index = next(
        (
            index
            for index, line in enumerate(section_lines)
            if line.startswith("| Stratum | Mitochondrial DEG occurrences")
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Could not find the Section 2 evidence table")
    header = markdown_cells(section_lines[header_index])
    if header != EXPECTED_HEADER:
        raise ValueError(
            "Unexpected Section 2 table header.\n"
            f"Observed: {header}\nExpected: {EXPECTED_HEADER}"
        )

    rows: list[TableRow] = []
    for line in section_lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        cells = markdown_cells(line)
        if len(cells) != len(EXPECTED_HEADER):
            raise ValueError(f"Unexpected table row: {line}")
        stratum = cells[0]
        mitochondrial_significant, mitochondrial_tested = parse_integer_pair(
            cells[1], "Mitochondrial DEG occurrences / tested"
        )
        mitochondrial_up, mitochondrial_down = parse_integer_pair(
            cells[2], "AD up / down"
        )
        oxphos_significant, oxphos_tested = parse_integer_pair(
            cells[3], "OXPHOS occurrences / tested"
        )
        oxphos_up, oxphos_down = parse_integer_pair(
            cells[4], "OXPHOS up / down"
        )
        if mitochondrial_up + mitochondrial_down != mitochondrial_significant:
            raise ValueError(
                f"Mitochondrial counts do not reconcile for {stratum}"
            )
        if oxphos_up + oxphos_down != oxphos_significant:
            raise ValueError(f"OXPHOS counts do not reconcile for {stratum}")
        if stratum.startswith("Female "):
            sex = "Female"
        elif stratum.startswith("Male "):
            sex = "Male"
        else:
            raise ValueError(f"Unexpected stratum sex label: {stratum}")
        apoe_group = stratum.removeprefix(f"{sex} ")
        rows.append(
            TableRow(
                stratum=stratum,
                sex=sex,
                apoe_group=apoe_group,
                mitochondrial_significant=mitochondrial_significant,
                mitochondrial_tested=mitochondrial_tested,
                mitochondrial_up=mitochondrial_up,
                mitochondrial_down=mitochondrial_down,
                oxphos_significant=oxphos_significant,
                oxphos_tested=oxphos_tested,
                oxphos_up=oxphos_up,
                oxphos_down=oxphos_down,
            )
        )

    observed_strata = [row.stratum for row in rows]
    if set(observed_strata) != set(STRATUM_ORDER) or len(rows) != 6:
        raise ValueError(
            "Expected exactly the six sex/APOE strata.\n"
            f"Observed: {observed_strata}"
        )
    rows_by_stratum = {row.stratum: row for row in rows}
    return [rows_by_stratum[stratum] for stratum in STRATUM_ORDER]


def as_plot_rows(table_rows: Iterable[TableRow]) -> list[PlotRow]:
    output: list[PlotRow] = []
    for row in table_rows:
        for gene_set, significant, tested, up, down in (
            (
                "All mitochondrial genes",
                row.mitochondrial_significant,
                row.mitochondrial_tested,
                row.mitochondrial_up,
                row.mitochondrial_down,
            ),
            (
                "OXPHOS subunits",
                row.oxphos_significant,
                row.oxphos_tested,
                row.oxphos_up,
                row.oxphos_down,
            ),
        ):
            if tested <= 0 or significant <= 0:
                raise ValueError(
                    f"Nonpositive denominator or significant count for "
                    f"{row.stratum}, {gene_set}"
                )
            output.append(
                PlotRow(
                    stratum=row.stratum,
                    sex=row.sex,
                    apoe_group=row.apoe_group,
                    gene_set=gene_set,
                    significant_occurrences=significant,
                    tested_occurrences=tested,
                    ad_up_occurrences=up,
                    ad_down_occurrences=down,
                    ad_up_pct_tested=100.0 * up / tested,
                    ad_down_pct_tested=100.0 * down / tested,
                    significant_pct_tested=100.0 * significant / tested,
                    ad_up_pct_significant=100.0 * up / significant,
                )
            )
    return output


def atomic_write_tsv(rows: list[PlotRow], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.tmp.{os.getpid()}"
    )
    fieldnames = list(PlotRow.__dataclass_fields__)
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for row in rows:
                record = {
                    field: getattr(row, field)
                    for field in fieldnames
                }
                for field in (
                    "ad_up_pct_tested",
                    "ad_down_pct_tested",
                    "significant_pct_tested",
                    "ad_up_pct_significant",
                ):
                    record[field] = f"{record[field]:.6f}"
                writer.writerow(record)
        if temporary.stat().st_size <= 0:
            raise RuntimeError(f"Generated empty TSV: {temporary}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_text(text: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.tmp.{os.getpid()}"
    )
    try:
        temporary.write_text(text, encoding="utf-8")
        if temporary.stat().st_size <= 0:
            raise RuntimeError(f"Generated empty text file: {temporary}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def annotate_direction(
    ax: plt.Axes,
    bar: Rectangle,
    y: float,
    count: int,
    percent: float,
    direction: str,
) -> DirectionAnnotation:
    signed_endpoint = percent if direction == "up" else -percent
    label = f"{count:,} ({percent:.2f}%)"
    horizontal_alignment = "left" if direction == "up" else "right"
    text = ax.text(
        signed_endpoint,
        y,
        label,
        ha=horizontal_alignment,
        va="center",
        fontsize=9.6,
        color=COLOR_TEXT,
        fontweight="normal",
        clip_on=False,
        zorder=5,
    )
    return DirectionAnnotation(
        text=text,
        bar=bar,
        direction=direction,
        endpoint=signed_endpoint,
    )


def place_direction_annotations(
    fig: plt.Figure,
    annotations: list[DirectionAnnotation],
) -> None:
    """Place labels inside bars only when a padded rendered fit is possible."""

    # Work in physical points so the whitespace is preserved in every output
    # format. Candidate labels are first inset into their bars; labels that do
    # not fit with the required padding are moved fully outside instead.
    inside_inset_points = 5.0
    outside_offset_points = 4.5
    minimum_horizontal_padding_points = 3.5
    minimum_vertical_padding_points = 2.0
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for annotation in annotations:
        direction_sign = 1 if annotation.direction == "up" else -1
        annotation.text.set_position(
            (annotation.endpoint, annotation.text.get_position()[1])
        )
        annotation.text.set_ha("right" if direction_sign > 0 else "left")
        annotation.text.set_color("white")
        annotation.text.set_fontweight("bold")
        annotation.text.set_transform(
            annotation.text.axes.transData
            + transforms.ScaledTranslation(
                -direction_sign * inside_inset_points / 72.0,
                0,
                fig.dpi_scale_trans,
            )
        )

        text_bounds = annotation.text.get_window_extent(renderer=renderer)
        bar_bounds = annotation.bar.get_window_extent(renderer=renderer)
        horizontal_padding = minimum_horizontal_padding_points * fig.dpi / 72.0
        vertical_padding = minimum_vertical_padding_points * fig.dpi / 72.0
        fits_inside = (
            text_bounds.x0 >= bar_bounds.x0 + horizontal_padding
            and text_bounds.x1 <= bar_bounds.x1 - horizontal_padding
            and text_bounds.y0 >= bar_bounds.y0 + vertical_padding
            and text_bounds.y1 <= bar_bounds.y1 - vertical_padding
        )
        if fits_inside:
            continue

        annotation.text.set_ha("left" if direction_sign > 0 else "right")
        annotation.text.set_color(COLOR_TEXT)
        annotation.text.set_fontweight("normal")
        annotation.text.set_transform(
            annotation.text.axes.transData
            + transforms.ScaledTranslation(
                direction_sign * outside_offset_points / 72.0,
                0,
                fig.dpi_scale_trans,
            )
        )

    fig.canvas.draw()


def validate_layout(
    fig: plt.Figure,
    axes: Iterable[plt.Axes],
    legend: matplotlib.legend.Legend,
    annotations: list[DirectionAnnotation],
) -> None:
    """Fail loudly if the rendered typography violates key clearances."""

    renderer = fig.canvas.get_renderer()
    legend_bounds = legend.get_window_extent(renderer=renderer)
    clearance_pixels = 5.0 * fig.dpi / 72.0
    for ax in axes:
        title_bounds = ax.title.get_window_extent(renderer=renderer)
        if title_bounds.y1 + clearance_pixels > legend_bounds.y0:
            raise RuntimeError(
                f"Panel title {ax.get_title()!r} is too close to the legend"
            )

    for annotation in annotations:
        text_bounds = annotation.text.get_window_extent(renderer=renderer)
        bar_bounds = annotation.bar.get_window_extent(renderer=renderer)
        horizontal_padding = 3.0 * fig.dpi / 72.0
        vertical_padding = 1.5 * fig.dpi / 72.0
        if annotation.text.get_color() == "white":
            has_padding = (
                text_bounds.x0 >= bar_bounds.x0 + horizontal_padding
                and text_bounds.x1 <= bar_bounds.x1 - horizontal_padding
                and text_bounds.y0 >= bar_bounds.y0 + vertical_padding
                and text_bounds.y1 <= bar_bounds.y1 - vertical_padding
            )
        elif annotation.direction == "up":
            has_padding = text_bounds.x0 >= bar_bounds.x1 + horizontal_padding
        else:
            has_padding = text_bounds.x1 <= bar_bounds.x0 - horizontal_padding
        if not has_padding:
            raise RuntimeError(
                f"Bar label {annotation.text.get_text()!r} lacks boundary padding"
            )


def draw_panel(
    ax: plt.Axes,
    rows: list[PlotRow],
    title: str,
    show_y_labels: bool,
) -> list[DirectionAnnotation]:
    rows_by_stratum = {row.stratum: row for row in rows}
    ordered = [rows_by_stratum[stratum] for stratum in STRATUM_ORDER]
    y_values = [Y_POSITIONS[row.stratum] for row in ordered]
    up_values = [row.ad_up_pct_tested for row in ordered]
    down_values = [-row.ad_down_pct_tested for row in ordered]

    for low, high in ((5.55, 7.45), (-0.45, 1.45)):
        ax.axhspan(low, high, color=COLOR_SHADE, zorder=0)
    for separator in (5.0, 2.0):
        ax.axhline(separator, color="#E5E5E5", linewidth=0.8, zorder=1)

    down_bars = ax.barh(
        y_values,
        down_values,
        height=0.64,
        color=COLOR_DOWN,
        edgecolor="white",
        linewidth=0.7,
        zorder=3,
    )
    up_bars = ax.barh(
        y_values,
        up_values,
        height=0.64,
        color=COLOR_UP,
        edgecolor="white",
        linewidth=0.7,
        zorder=3,
    )

    annotations: list[DirectionAnnotation] = []
    for row, y, down_bar, up_bar in zip(
        ordered,
        y_values,
        down_bars.patches,
        up_bars.patches,
    ):
        annotations.append(
            annotate_direction(
                ax,
                down_bar,
                y,
                row.ad_down_occurrences,
                row.ad_down_pct_tested,
                "down",
            )
        )
        annotations.append(
            annotate_direction(
                ax,
                up_bar,
                y,
                row.ad_up_occurrences,
                row.ad_up_pct_tested,
                "up",
            )
        )
        ax.text(
            19.35,
            y + 0.13,
            f"{row.significant_pct_tested:.2f}%",
            ha="right",
            va="center",
            fontsize=9.7,
            fontweight="bold",
            color=COLOR_TEXT,
            zorder=5,
        )
        ax.text(
            19.35,
            y - 0.18,
            f"{row.tested_occurrences:,} tested",
            ha="right",
            va="center",
            fontsize=8.2,
            color=COLOR_MUTED,
            zorder=5,
        )

    ax.axvline(0, color="#333333", linewidth=1.1, zorder=4)
    ax.axvline(16.75, color="#DFDFDF", linewidth=0.8, zorder=2)
    ax.set_xlim(-20, 20)
    ax.set_ylim(-0.75, 8.15)
    ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
    ax.xaxis.set_major_formatter(
        FuncFormatter(
            lambda value, _position: (
                "0" if abs(value) < 1e-9 else f"{abs(value):.0f}%"
            )
        )
    )
    ax.grid(axis="x", color=COLOR_GRID, linewidth=0.7, alpha=0.85, zorder=0)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="x", labelsize=9.5, colors=COLOR_MUTED, length=0)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_yticks(y_values)
    if show_y_labels:
        ax.set_yticklabels(
            [row.stratum for row in ordered],
            fontsize=11.0,
            color=COLOR_TEXT,
        )
    else:
        ax.tick_params(axis="y", labelleft=False)

    ax.set_title(
        title,
        loc="left",
        fontsize=14.0,
        fontweight="bold",
        color=COLOR_TEXT,
        pad=18,
    )
    ax.text(
        -19.4,
        7.85,
        "← AD-down",
        ha="left",
        va="center",
        fontsize=9.6,
        fontweight="bold",
        color=COLOR_DOWN,
    )
    ax.text(
        12.8,
        7.85,
        "AD-up →",
        ha="right",
        va="center",
        fontsize=9.6,
        fontweight="bold",
        color=COLOR_UP,
    )
    ax.text(
        19.35,
        7.87,
        "Total DEG\nrate / tested",
        ha="right",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color=COLOR_MUTED,
        linespacing=1.0,
    )

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#A8A8A8")
    ax.spines["bottom"].set_linewidth(0.8)
    return annotations


def make_figure(plot_rows: list[PlotRow]) -> plt.Figure:
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.unicode_minus": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(15.2, 8.8),
        sharey=True,
        gridspec_kw={"wspace": 0.07},
    )
    mitochondrial_rows = [
        row for row in plot_rows if row.gene_set == "All mitochondrial genes"
    ]
    oxphos_rows = [
        row for row in plot_rows if row.gene_set == "OXPHOS subunits"
    ]

    annotations = draw_panel(
        axes[0],
        mitochondrial_rows,
        "All mitochondrial genes",
        show_y_labels=True,
    )
    annotations.extend(
        draw_panel(
            axes[1],
            oxphos_rows,
            "OXPHOS subunits",
            show_y_labels=False,
        )
    )

    fig.suptitle(
        "Direction and burden of AD-associated mitochondrial transcription",
        x=0.5,
        y=0.972,
        fontsize=18,
        fontweight="bold",
        color=COLOR_TEXT,
    )
    fig.text(
        0.5,
        0.925,
        "AD versus no cognitive impairment, stratified by sex and APOE genotype",
        ha="center",
        va="center",
        fontsize=12.0,
        color=COLOR_MUTED,
    )
    legend = fig.legend(
        handles=[
            Patch(facecolor=COLOR_DOWN, edgecolor="none", label="AD-down"),
            Patch(facecolor=COLOR_UP, edgecolor="none", label="AD-up"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.878),
        ncol=2,
        frameon=False,
        handlelength=1.5,
        columnspacing=2.0,
        fontsize=10.8,
    )
    fig.text(
        0.5,
        0.105,
        "Significant gene–fine-cell-type occurrences (% of all tested occurrences)",
        ha="center",
        va="center",
        fontsize=11.5,
        color=COLOR_TEXT,
    )
    fig.text(
        0.5,
        0.058,
        (
            "Bar labels are occurrence count (percentage tested). Total DEG "
            "rate is the combined AD-up and AD-down percentage."
        ),
        ha="center",
        va="center",
        fontsize=9.2,
        color=COLOR_MUTED,
    )
    fig.text(
        0.5,
        0.028,
        (
            "Occurrences can repeat a gene across fine cell types and are not "
            "unique genes or donors; strata are descriptive, not formal "
            "interaction tests."
        ),
        ha="center",
        va="center",
        fontsize=9.2,
        color=COLOR_MUTED,
    )
    fig.subplots_adjust(
        left=0.12,
        right=0.985,
        top=0.77,
        bottom=0.16,
        wspace=0.07,
    )
    place_direction_annotations(fig, annotations)
    validate_layout(fig, axes, legend, annotations)
    return fig


def atomic_save_figure(
    fig: plt.Figure,
    destination: Path,
    file_format: str,
    dpi: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.stem}.tmp.{os.getpid()}.{file_format}"
    )
    save_kwargs = {
        "format": file_format,
        "facecolor": "white",
    }
    if file_format == "png":
        save_kwargs["dpi"] = dpi
    try:
        fig.savefig(temporary, **save_kwargs)
        if temporary.stat().st_size <= 0:
            raise RuntimeError(f"Generated empty figure: {temporary}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def caption_text(source_path: Path) -> str:
    try:
        source_relative = source_path.relative_to(PROJECT_ROOT)
    except ValueError:
        source_relative = source_path
    return (
        "# Figure caption\n\n"
        "**Direction and burden of AD-associated mitochondrial transcription "
        "by sex/APOE stratum.** The left panel shows all mitochondrial genes "
        "and the right panel shows OXPHOS subunits. Bars represent significant "
        "gene–fine-cell-type occurrences as a percentage of all occurrences "
        "tested in the corresponding stratum; AD-down values are displayed "
        "to the left and AD-up values to the right. Bar labels report the raw "
        "occurrence count and percentage tested. The right-hand annotation "
        "reports the combined DEG rate and denominator. An occurrence is not "
        "a unique gene or donor because the same gene can be significant in "
        "multiple fine cell types. The sex/APOE differences are descriptive "
        "and do not constitute formal interaction tests.\n\n"
        f"**Source:** `{source_relative}`, Section 2.\n"
    )


def main() -> int:
    args = parse_args()
    if args.dpi <= 0:
        raise ValueError("--dpi must be positive")
    source_path = absolute_path(args.source).resolve()
    output_root = absolute_path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    print(f"Reading Section 2 table: {source_path}")
    table_rows = parse_section_two_table(source_path)
    plot_rows = as_plot_rows(table_rows)
    if len(plot_rows) != 12:
        raise RuntimeError(f"Expected 12 plotted rows; observed {len(plot_rows)}")

    data_path = output_root / f"{args.basename}_plotted_data.tsv"
    caption_path = output_root / f"{args.basename}_caption.md"
    atomic_write_tsv(plot_rows, data_path)
    atomic_write_text(caption_text(source_path), caption_path)

    print("Rendering figure")
    figure = make_figure(plot_rows)
    generated: list[Path] = []
    try:
        for file_format in ("svg", "pdf", "png"):
            destination = output_root / f"{args.basename}.{file_format}"
            atomic_save_figure(figure, destination, file_format, args.dpi)
            generated.append(destination)
    finally:
        plt.close(figure)

    generated.extend((data_path, caption_path))
    for path in generated:
        print(f"Wrote {path} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
