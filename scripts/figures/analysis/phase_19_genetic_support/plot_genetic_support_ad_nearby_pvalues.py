#!/usr/bin/env python3
"""Render the Bellenguez nearby-AD P values for the 19 nuclear genes."""

from __future__ import annotations

import argparse
from decimal import Decimal
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase19_slide_figure_common import (  # noqa: E402
    AMBER,
    BLUE,
    CHARCOAL,
    DARK,
    LIGHT,
    MID,
    NAVY,
    PALE,
    PALE_AMBER,
    PALE_BLUE,
    WHITE,
    add_text,
    make_checks,
    new_canvas,
    output_names,
    panel_heading,
    publish_package,
    render_triplet,
    require,
    rounded_box,
    truth,
    validate_blocking_checks,
    validate_source_status,
)

import matplotlib  # noqa: E402


SCHEMA = "genetic_support_ad_nearby_pvalues_v1"
INPUT_SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"
STEM = "genetic_support_ad_nearby_pvalues"
DEFAULT_INPUT_ROOT = (
    "results/minerva_production/19_genetic_support_tier2_recovery"
)
DEFAULT_OUTPUT_ROOT = (
    "results/figures/analysis/phase_19_genetic_support/ad_nearby_pvalues"
)
OUTPUT_FILES = output_names(STEM)
REQUIRED_INPUTS = [
    "recovery_regional_gwas_summary.tsv",
    "recovery_status.tsv",
    "recovery_checks.tsv",
]

GWAS_CUTOFF = 5e-8
CUTOFF_MINUS_LOG10 = -math.log10(GWAS_CUTOFF)
SOURCE_ACCESSION = "GCST90027158"
EXPECTED_BELOW_CUTOFF_GENES = {"ANKRD11", "APOE", "COX7C", "RPS15"}
EXPECTED_RAW_P = {
    "ANKRD11": "1.283e-11",
    "APOE": "0",
    "ATP6V1F": "4e-05",
    "COX4I1": "2.929e-06",
    "COX6B1": "3.932e-05",
    "COX7C": "8.579e-14",
    "DYNLT1": "6.079e-05",
    "FTL": "5.711e-06",
    "LAMTOR5": "6.605e-05",
    "LAPTM4A": "5.651e-06",
    "NCOA1": "1.213e-05",
    "RPL11": "8.157e-06",
    "RPL15": "2.677e-05",
    "RPL38": "1.05e-05",
    "RPLP1": "0.0002931",
    "RPS13": "8.997e-05",
    "RPS15": "4.089e-30",
    "SELENOW": "6.41e-05",
    "UQCR10": "1.248e-05",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render exact nearby Bellenguez AD P values for 19 genes."
    )
    parser.add_argument("--input-root", default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    return parser.parse_args()


def _require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    require(not missing, f"{label} is missing columns: {', '.join(missing)}")


def _superscript(integer: int) -> str:
    table = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(integer).translate(table)


def format_exact_p(raw_value: str) -> str:
    """Format the source value without inventing extra numerical precision."""

    value = Decimal(str(raw_value))
    if value.is_zero():
        return "underflow* (source stored 0)"
    exponent = value.adjusted()
    mantissa = value.scaleb(-exponent).normalize()
    mantissa_text = format(mantissa, "f").rstrip("0").rstrip(".")
    return f"{mantissa_text} × 10{_superscript(exponent)}"


def validate_inputs(input_root: Path) -> dict[str, pd.DataFrame]:
    """Load and validate the authoritative recovery summary and run status."""

    paths = {name: input_root / name for name in REQUIRED_INPUTS}
    missing = [name for name, path in paths.items() if not path.is_file()]
    require(not missing, "Missing figure inputs: " + ", ".join(missing))

    regional = pd.read_csv(
        paths[REQUIRED_INPUTS[0]],
        sep="\t",
        dtype={"regional_min_p": "string"},
        low_memory=False,
    )
    status = validate_source_status(
        paths[REQUIRED_INPUTS[1]],
        status_column="technical_status",
        accepted={"validated_complete_tier2_recovery"},
    )
    source_checks = validate_blocking_checks(paths[REQUIRED_INPUTS[2]])

    for label, frame in {
        "regional summary": regional,
        "status": status,
        "source checks": source_checks,
    }.items():
        _require_columns(frame, {"schema_version"}, label)
        observed = set(frame["schema_version"].dropna().astype(str))
        require(observed == {INPUT_SCHEMA}, f"Unexpected schema in {label}: {observed}")

    _require_columns(
        regional,
        {
            "gene",
            "ensembl_gene_id",
            "window_start",
            "window_end",
            "regional_min_p",
            "regional_lead_variant",
            "regional_gwas_signal",
            "source_accession",
        },
        "regional summary",
    )
    require(len(regional) == 19, f"Expected 19 regional rows; found {len(regional)}")
    require(regional["gene"].nunique() == 19, "Expected one regional row per gene")
    require(
        set(regional["source_accession"].astype(str)) == {SOURCE_ACCESSION},
        "Regional rows do not all use the frozen Bellenguez accession",
    )
    require(
        regional["regional_min_p"].notna().all(),
        "A regional minimum P value is missing",
    )
    require(
        set(regional.set_index("gene")["regional_min_p"].astype(str).to_dict().items())
        == set(EXPECTED_RAW_P.items()),
        "Frozen regional minimum P values changed",
    )
    return {"regional": regional, "status": status, "source_checks": source_checks}


def derive_plot_data(
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Derive exactly one display row per unique nuclear gene."""

    regional = frames["regional"].copy()
    rows: list[dict[str, Any]] = []
    for gene, group in regional.groupby("gene", sort=True):
        require(len(group) == 1, f"Expected exactly one recovery row for {gene}")
        source = group.iloc[0]
        raw_p = str(source["regional_min_p"])
        numeric_p = float(Decimal(raw_p))
        source_below_cutoff = truth(source["regional_gwas_signal"])
        if numeric_p > 0:
            computed_below_cutoff = numeric_p < GWAS_CUTOFF
            require(
                computed_below_cutoff == source_below_cutoff,
                f"Source cutoff flag disagrees with P value for {gene}",
            )
            minus_log10_p: float | Any = -math.log10(numeric_p)
            minus_log10_display = f"{minus_log10_p:.2f}"
        else:
            require(gene == "APOE", "Only APOE may have a zero source P value")
            require(
                source_below_cutoff,
                "The APOE underflow row must be classified below the source cutoff",
            )
            minus_log10_p = pd.NA
            minus_log10_display = "beyond range*"
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "gene_region",
                "gene": gene,
                "ensembl_gene_id": str(source["ensembl_gene_id"]),
                "window_start": int(source["window_start"]),
                "window_end": int(source["window_end"]),
                "regional_lead_variant": str(source["regional_lead_variant"]),
                "regional_min_p_source": raw_p,
                "regional_min_p_display": format_exact_p(raw_p),
                "minus_log10_p": minus_log10_p,
                "minus_log10_display": minus_log10_display,
                "cutoff_p": GWAS_CUTOFF,
                "cutoff_minus_log10": CUTOFF_MINUS_LOG10,
                "below_cutoff": source_below_cutoff,
                "cutoff_class": (
                    "Below conservative cutoff"
                    if source_below_cutoff
                    else "At or above conservative cutoff"
                ),
                "style_key": (
                    "below_cutoff_filled_blue_diamond"
                    if source_below_cutoff
                    else "at_or_above_cutoff_open_gray_circle"
                ),
                "source_accession": str(source["source_accession"]),
                "source_table": "recovery_regional_gwas_summary.tsv",
            }
        )

    plot_data = pd.DataFrame(rows)
    plot_data["display_group"] = plot_data["below_cutoff"].map(
        {
            True: "four_values_below_cutoff",
            False: "fifteen_values_at_or_above_cutoff",
        }
    )
    sort_value = pd.to_numeric(plot_data["minus_log10_p"], errors="coerce")
    plot_data["sort_minus_log10_p"] = sort_value.fillna(math.inf)
    plot_data = plot_data.sort_values(
        ["below_cutoff", "sort_minus_log10_p", "gene"],
        ascending=[True, False, True],
        kind="stable",
    ).reset_index(drop=True)
    plot_data["display_order"] = range(1, len(plot_data) + 1)

    below_cutoff = plot_data.loc[plot_data["below_cutoff"]]
    at_or_above_cutoff = plot_data.loc[~plot_data["below_cutoff"]]
    derived = {
        "source_row_count": len(regional),
        "unique_gene_count": plot_data["gene"].nunique(),
        "below_cutoff_count": len(below_cutoff),
        "at_or_above_cutoff_count": len(at_or_above_cutoff),
        "below_cutoff_genes": sorted(below_cutoff["gene"].tolist()),
        "at_or_above_cutoff_genes": sorted(at_or_above_cutoff["gene"].tolist()),
        "underflow_count": int(plot_data["minus_log10_p"].isna().sum()),
        "underflow_genes": sorted(
            plot_data.loc[plot_data["minus_log10_p"].isna(), "gene"].tolist()
        ),
        "source_accessions": sorted(plot_data["source_accession"].unique()),
        "exact_p_fingerprint": "|".join(
            f"{gene}:{EXPECTED_RAW_P[gene]}" for gene in sorted(EXPECTED_RAW_P)
        ),
    }
    return plot_data, derived


def build_science_checks(derived: dict[str, Any]) -> pd.DataFrame:
    return make_checks(
        SCHEMA,
        [
            ("source_row_count", 19, derived["source_row_count"], "Recovery summary rows."),
            ("unique_gene_count", 19, derived["unique_gene_count"], "One row per nuclear gene."),
            (
                "below_cutoff_count",
                4,
                derived["below_cutoff_count"],
                "Regional minimum P values below the conservative cutoff.",
            ),
            (
                "at_or_above_cutoff_count",
                15,
                derived["at_or_above_cutoff_count"],
                "Regional minimum P values at or above the conservative cutoff.",
            ),
            (
                "below_cutoff_gene_set",
                "|".join(sorted(EXPECTED_BELOW_CUTOFF_GENES)),
                "|".join(derived["below_cutoff_genes"]),
                "Genes whose regional minimum is below P = 5e-8.",
            ),
            ("underflow_count", 1, derived["underflow_count"], "Numerically underflowed P values."),
            ("underflow_gene", "APOE", "|".join(derived["underflow_genes"]), "APOE is explicitly labeled as underflow."),
            ("source_accession", SOURCE_ACCESSION, "|".join(derived["source_accessions"]), "Frozen Bellenguez GWAS accession."),
            (
                "exact_p_fingerprint",
                "|".join(f"{gene}:{EXPECTED_RAW_P[gene]}" for gene in sorted(EXPECTED_RAW_P)),
                derived["exact_p_fingerprint"],
                "All exact source P strings are retained.",
            ),
        ],
    )


def render_figure(plot_data: pd.DataFrame, derived: dict[str, Any]):
    figure, axis = new_canvas()
    figure.set_layout_engine(None)
    matplotlib.rcParams["savefig.bbox"] = None
    matplotlib.rcParams["savefig.pad_inches"] = 0.0

    # Main panel: retain all 15 additional exact values alongside the four
    # priority regions in panel B.
    rounded_box(axis, 0.014, 0.055, 0.645, 0.89, face=WHITE, edge=LIGHT, linewidth=1.0)
    panel_heading(axis, "A", "All 19 exact values • 15 additional regions", 0.032, 0.906)
    add_text(
        axis,
        0.057,
        0.852,
        "Smallest Bellenguez AD P value within each gene's nearby region",
        size=9.7,
        color=MID,
    )
    add_text(axis, 0.136, 0.797, "Gene", size=8.2, color=NAVY, weight="bold", ha="right")
    add_text(
        axis,
        0.317,
        0.797,
        "−log₁₀(P)   →   smaller P",
        size=8.2,
        color=NAVY,
        weight="bold",
        ha="center",
    )
    add_text(axis, 0.507, 0.797, "Exact regional P", size=8.2, color=NAVY, weight="bold")

    x_min, x_max = 3.2, 7.45
    plot_x0, plot_x1 = 0.155, 0.485

    def map_x(value: float) -> float:
        return plot_x0 + (value - x_min) / (x_max - x_min) * (plot_x1 - plot_x0)

    row_top, row_bottom = 0.744, 0.135
    at_or_above_cutoff = plot_data.loc[~plot_data["below_cutoff"]].sort_values(
        ["sort_minus_log10_p", "gene"], ascending=[False, True], kind="stable"
    )
    row_step = (row_top - row_bottom) / (len(at_or_above_cutoff) - 1)

    for tick in [4.0, 5.0, 6.0, 7.0]:
        x = map_x(tick)
        axis.plot([x, x], [row_bottom - 0.018, row_top + 0.018], transform=axis.transAxes, color=LIGHT, linewidth=0.65, zorder=1)
        add_text(axis, x, 0.773, f"{tick:.0f}", size=7.3, color=MID, ha="center")

    cutoff_x = map_x(CUTOFF_MINUS_LOG10)
    axis.plot(
        [cutoff_x, cutoff_x],
        [row_bottom - 0.023, row_top + 0.027],
        transform=axis.transAxes,
        color=AMBER,
        linewidth=1.5,
        linestyle=(0, (4, 3)),
        zorder=2,
    )
    add_text(
        axis,
        cutoff_x,
        0.773,
        "7.30 conservative cutoff",
        size=7.3,
        color=AMBER,
        weight="bold",
        ha="center",
    )

    for index, row in enumerate(at_or_above_cutoff.itertuples(index=False)):
        y = row_top - index * row_step
        value = float(row.minus_log10_p)
        x = map_x(value)
        if index % 2 == 0:
            axis.add_patch(
                matplotlib.patches.Rectangle(
                    (0.025, y - row_step * 0.42),
                    0.622,
                    row_step * 0.84,
                    transform=axis.transAxes,
                    facecolor=PALE,
                    edgecolor="none",
                    zorder=0,
                )
            )
        add_text(axis, 0.136, y, row.gene, size=8.0, color=DARK, weight="bold", ha="right")
        axis.plot(
            [plot_x0, x],
            [y, y],
            transform=axis.transAxes,
            color=CHARCOAL,
            linewidth=1.0,
            linestyle=(0, (2, 2)),
            zorder=2,
        )
        axis.scatter(
            [x],
            [y],
            transform=axis.transAxes,
            s=34,
            marker="o",
            facecolors=WHITE,
            edgecolors=CHARCOAL,
            linewidths=1.2,
            zorder=4,
        )
        add_text(axis, 0.507, y, row.regional_min_p_display, size=7.8, color=DARK)

    add_text(
        axis,
        0.036,
        0.085,
        "○ 15 additional values at/above cutoff   •   Exact minima retained for transparent follow-up",
        size=8.1,
        color=MID,
    )

    # Compact callout: the four regional minima below the cutoff.
    rounded_box(axis, 0.680, 0.595, 0.305, 0.35, face=PALE_BLUE, edge=BLUE, linewidth=1.1)
    panel_heading(axis, "B", "Four priority regions below cutoff", 0.699, 0.907)
    add_text(axis, 0.702, 0.852, "Gene", size=7.5, color=NAVY, weight="bold")
    add_text(axis, 0.790, 0.852, "Exact regional P", size=7.5, color=NAVY, weight="bold")
    add_text(axis, 0.963, 0.852, "−log₁₀", size=7.5, color=NAVY, weight="bold", ha="right")

    below_cutoff = plot_data.loc[plot_data["below_cutoff"]].sort_values(
        ["sort_minus_log10_p", "gene"], ascending=[False, True], kind="stable"
    )
    below_cutoff_ys = [0.800, 0.747, 0.694, 0.641]
    for y, row in zip(
        below_cutoff_ys, below_cutoff.itertuples(index=False), strict=True
    ):
        axis.scatter(
            [0.705],
            [y],
            transform=axis.transAxes,
            s=31,
            marker="D",
            facecolors=BLUE,
            edgecolors=NAVY,
            linewidths=0.7,
            zorder=4,
        )
        add_text(axis, 0.718, y, row.gene, size=8.0, color=DARK, weight="bold")
        p_label = "underflow* (stored 0)" if row.gene == "APOE" else row.regional_min_p_display
        add_text(axis, 0.790, y, p_label, size=6.9, color=DARK)
        add_text(axis, 0.963, y, row.minus_log10_display, size=7.3, color=DARK, ha="right")

    add_text(
        axis,
        0.700,
        0.612,
        "*APOE was too small for the file's number format; P is not literally zero.",
        size=6.7,
        color=MID,
    )

    # Plain-language threshold rationale.
    rounded_box(axis, 0.680, 0.315, 0.305, 0.253, face=PALE_AMBER, edge=AMBER, linewidth=1.0)
    panel_heading(axis, "C", "Why a conservative cutoff?", 0.699, 0.533)
    add_text(
        axis,
        0.701,
        0.478,
        "A genome-wide study checks millions of DNA variants.",
        size=8.1,
        color=DARK,
    )
    add_text(axis, 0.701, 0.433, "0.05  ÷  about 1,000,000 independent tests", size=8.2, color=MID)
    add_text(axis, 0.701, 0.386, "≈  5 × 10⁻⁸", size=13.0, color=AMBER, weight="bold")
    add_text(
        axis,
        0.701,
        0.343,
        "This greatly reduces chance findings.\nIt is a screening rule, not a magic boundary.",
        size=6.9,
        color=DARK,
        va="center",
        linespacing=1.08,
    )

    # Future-validation guidance.
    rounded_box(axis, 0.680, 0.055, 0.305, 0.235, face=WHITE, edge=LIGHT, linewidth=1.0)
    panel_heading(axis, "D", "How the results guide validation", 0.699, 0.256)
    add_text(
        axis,
        0.701,
        0.205,
        "All 19 exact P values remain available for comparison.",
        size=7.1,
        color=DARK,
    )
    add_text(
        axis,
        0.701,
        0.145,
        "The four below-cutoff regions are priorities for matched\ngene-activity and shared-variant analyses.",
        size=6.7,
        color=NAVY,
        weight="bold",
        va="center",
        linespacing=1.08,
    )
    add_text(
        axis,
        0.701,
        0.085,
        "Nearby = 1 Mb on each side. Gene-level validation can test\nwhich gene or DNA “switch” is responsible.",
        size=6.3,
        color=MID,
        va="center",
        linespacing=1.08,
    )
    return figure


CAPTION = """
**Four regions are priorities for validation, with all 19 exact P values
shown.**
For each of the 19 nuclear genes, the smallest Alzheimer’s disease association
P value in the recovery table is shown. Four values are below the conventional
genome-wide cutoff of `P = 5 × 10⁻⁸`, prioritizing those regions for
gene-activity and shared-variant validation; the 15 additional values are shown
at or above the cutoff.
Horizontal position is `−log₁₀(P)`, so a point farther right represents a
smaller P value. APOE’s regional minimum was stored as zero because it
underflowed the source number representation; a P value is not literally zero.
The conservative screening cutoff is approximately `0.05 / 1,000,000`, reflecting the
roughly one million independent common-variant comparisons in a genome-wide
study. The cutoff is one evidence layer for prioritizing validation. A signal
inside a gene’s nearby region does not by itself identify that gene as causal.
"""


METHODS = """
Values were read from the validated
`recovery_regional_gwas_summary.tsv` table for Bellenguez GWAS Catalog accession
`GCST90027158`. The source table was required to contain exactly one row for
each of 19 unique nuclear genes, and its run status and blocking checks were
required to pass. The exact source strings were retained for the displayed P
labels. For positive P values, `−log₁₀(P)` was computed directly and the source
regional-signal flag was checked against the frozen `P < 5e-8` rule. APOE’s
stored zero was treated only as numerical underflow: no finite `−log₁₀(P)` was
calculated or substituted. Filled blue diamonds identify the four values below
the cutoff; open gray circles and dotted lines identify the 15 values at or
above it, providing redundant shape and line-style encoding in addition to
color. These screening-cutoff positions guide follow-up without serving as
total-evidence ratings. Candidate windows extend 1 Mb on either side of the
gene span. The graphic was exported at
12.4 × 4.7 inches as a 450-DPI PNG plus editable PDF and SVG.
"""


def main() -> None:
    args = parse_args()
    input_root = Path(args.input_root).resolve()
    output_root = Path(args.output_root).resolve()
    frames = validate_inputs(input_root)
    plot_data, derived = derive_plot_data(frames)
    science_checks = build_science_checks(derived)
    source_paths = [input_root / name for name in REQUIRED_INPUTS]

    publish_package(
        schema=SCHEMA,
        stem=STEM,
        output_root=output_root,
        source_paths=source_paths,
        renderer_path=Path(__file__).resolve(),
        plot_data=plot_data,
        science_checks=science_checks,
        caption=CAPTION,
        methods=METHODS,
        render=lambda staging: render_triplet(
            render_figure(plot_data, derived), staging, STEM
        ),
        status_fields={
            "source_schema_version": INPUT_SCHEMA,
            "source_accession": SOURCE_ACCESSION,
            "unique_gene_count": derived["unique_gene_count"],
            "cutoff_p": GWAS_CUTOFF,
            "cutoff_minus_log10": CUTOFF_MINUS_LOG10,
            "below_cutoff_count": derived["below_cutoff_count"],
            "at_or_above_cutoff_count": derived["at_or_above_cutoff_count"],
            "cutoff_class_is_total_evidence_conclusion": False,
            "apoe_numeric_underflow": True,
            "nearby_signal_assigns_gene": False,
            "visible_internal_phase_label": False,
        },
        force=args.force,
        visual_review_status=args.visual_review_status,
    )


if __name__ == "__main__":
    main()
