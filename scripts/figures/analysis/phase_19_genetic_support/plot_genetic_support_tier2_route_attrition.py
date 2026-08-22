#!/usr/bin/env python3
"""Render the Tier 2 terminal-route outcome figure for presentation slides."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase19_slide_figure_common import (  # noqa: E402
    CHARCOAL,
    DARK,
    GRAY,
    LIGHT,
    MID,
    NAVY,
    PALE,
    PALE_VERMILLION,
    VERMILLION,
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
    validate_blocking_checks,
    validate_source_status,
)

import matplotlib  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402


SCHEMA = "genetic_support_tier2_route_attrition_v1"
INPUT_SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"
STEM = "genetic_support_tier2_route_attrition"
DEFAULT_INPUT_ROOT = (
    "results/minerva_production/19_genetic_support_tier2_recovery"
)
DEFAULT_OUTPUT_ROOT = (
    "results/figures/analysis/phase_19_genetic_support/tier2_route_attrition"
)
OUTPUT_FILES = output_names(STEM)
REQUIRED_INPUTS = [
    "recovery_route_decisions.tsv",
    "recovery_status.tsv",
    "recovery_checks.tsv",
    "recovery_colocalization_qc.tsv",
    "recovery_colocalization.tsv.gz",
]

TERMINAL_ORDER = [
    "no_regional_gwas_signal",
    "no_regional_qtl_signal",
    "model_or_ld_incompatible",
    "not_assessable",
]
EXPECTED_TERMINAL_COUNTS = {
    "no_regional_gwas_signal": 42,
    "no_regional_qtl_signal": 4,
    "model_or_ld_incompatible": 2,
    "not_assessable": 6,
}
TERMINAL_LABELS = {
    "no_regional_gwas_signal": "No strong nearby\nAD variant signal",
    "no_regional_qtl_signal": "No strong gene-\nexpression signal",
    "model_or_ld_incompatible": "Required inputs\nunavailable",
    "not_assessable": "Could not assess",
}
TERMINAL_DETAILS = {
    "no_regional_gwas_signal": "Nearby AD-signal\ncutoff not passed",
    "no_regional_qtl_signal": "Expression-signal\ncutoff not passed",
    "model_or_ld_incompatible": "Prediction method or\nvariant correlations missing",
    "not_assessable": "Splicing-data status\nunresolved",
}
STYLE_KEYS = {
    "no_regional_gwas_signal": "signal_negative_gray",
    "no_regional_qtl_signal": "qtl_negative_blue_gray",
    "model_or_ld_incompatible": "input_limited_vermillion",
    "not_assessable": "not_assessable_open",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the validated Tier 2 terminal-route slide figure."
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


def _require_schema(frame: pd.DataFrame, label: str, *, allow_empty: bool = False) -> None:
    _require_columns(frame, {"schema_version"}, label)
    if frame.empty:
        require(allow_empty, f"{label} must not be empty")
        return
    observed = set(frame["schema_version"].dropna().astype(str))
    require(observed == {INPUT_SCHEMA}, f"Unexpected schema in {label}: {observed}")


def validate_inputs(input_root: Path) -> dict[str, pd.DataFrame]:
    """Load the recovery bundle and enforce the source-analysis contract."""

    paths = {name: input_root / name for name in REQUIRED_INPUTS}
    missing = [name for name, path in paths.items() if not path.is_file()]
    require(not missing, "Missing figure inputs: " + ", ".join(missing))

    routes = pd.read_csv(paths[REQUIRED_INPUTS[0]], sep="\t", low_memory=False)
    status = validate_source_status(
        paths[REQUIRED_INPUTS[1]],
        status_column="technical_status",
        accepted={"validated_complete_tier2_recovery"},
    )
    source_checks = validate_blocking_checks(paths[REQUIRED_INPUTS[2]])
    qc = pd.read_csv(paths[REQUIRED_INPUTS[3]], sep="\t", low_memory=False)
    coloc = pd.read_csv(paths[REQUIRED_INPUTS[4]], sep="\t", low_memory=False)

    frames = {
        "routes": routes,
        "status": status,
        "source_checks": source_checks,
        "qc": qc,
        "coloc": coloc,
    }
    for label, frame in frames.items():
        _require_schema(frame, label, allow_empty=label == "coloc")

    _require_columns(
        routes,
        {
            "route_id",
            "candidate_id",
            "gene",
            "broad_network",
            "qtl_type",
            "terminal_state",
            "reason",
        },
        "routes",
    )
    _require_columns(
        status,
        {
            "nuclear_recovery_routes",
            "terminal_recovery_routes",
            "precomputed_resolved_routes",
            "custom_resolved_routes",
            "no_regional_gwas_signal_routes",
            "no_regional_qtl_signal_routes",
            "model_or_ld_incompatible_routes",
            "not_assessable_routes",
            "blocking_check_failures",
        },
        "status",
    )
    _require_columns(
        qc,
        {"route_id", "posterior_rows", "terminal_state", "qc_state"},
        "colocalization QC",
    )
    _require_columns(
        coloc,
        {
            "route_id",
            "PP.H0.abf",
            "PP.H1.abf",
            "PP.H2.abf",
            "PP.H3.abf",
            "PP.H4.abf",
        },
        "colocalization results",
    )

    require(len(routes) == 54, f"Expected 54 recovery routes; found {len(routes)}")
    require(routes["route_id"].nunique() == 54, "Recovery route IDs are not unique")
    observed_states = set(routes["terminal_state"].astype(str))
    require(
        observed_states == set(TERMINAL_ORDER),
        f"Unexpected terminal-state set: {observed_states}",
    )
    observed_counts = routes["terminal_state"].value_counts().to_dict()
    require(
        all(int(observed_counts.get(key, 0)) == value for key, value in EXPECTED_TERMINAL_COUNTS.items()),
        f"Unexpected terminal-state counts: {observed_counts}",
    )
    qtl_counts = routes["qtl_type"].value_counts().to_dict()
    require(qtl_counts == {"eQTL": 27, "sQTL": 27}, f"Unexpected QTL counts: {qtl_counts}")
    require(routes["candidate_id"].nunique() == 27, "Expected 27 nuclear candidate contexts")
    require(routes["gene"].nunique() == 19, "Expected 19 unique nuclear genes")
    for candidate_id, group in routes.groupby("candidate_id", sort=False):
        require(len(group) == 2, f"Expected two routes for {candidate_id}")
        require(
            set(group["qtl_type"].astype(str)) == {"eQTL", "sQTL"},
            f"Expected paired eQTL/sQTL routes for {candidate_id}",
        )

    require(len(qc) == 54, f"Expected 54 colocalization-QC rows; found {len(qc)}")
    require(qc["route_id"].nunique() == 54, "QC route IDs are not unique")
    require(
        set(qc["route_id"].astype(str)) == set(routes["route_id"].astype(str)),
        "Route and QC route IDs differ",
    )
    qc_states = qc.set_index("route_id")["terminal_state"].astype(str).sort_index()
    route_states = routes.set_index("route_id")["terminal_state"].astype(str).sort_index()
    require(qc_states.equals(route_states), "Route and QC terminal states differ")
    posterior_rows = pd.to_numeric(qc["posterior_rows"], errors="raise")
    require(bool(posterior_rows.eq(0).all()), "A QC route contains posterior rows")
    require(coloc.empty, "Primary colocalization output must be header-only")

    source_status = status.iloc[0]
    status_expectations = {
        "nuclear_recovery_routes": 54,
        "terminal_recovery_routes": 54,
        "precomputed_resolved_routes": 0,
        "custom_resolved_routes": 0,
        "no_regional_gwas_signal_routes": 42,
        "no_regional_qtl_signal_routes": 4,
        "model_or_ld_incompatible_routes": 2,
        "not_assessable_routes": 6,
        "blocking_check_failures": 0,
    }
    for field, expected in status_expectations.items():
        observed = int(source_status[field])
        require(observed == expected, f"Status mismatch for {field}: {observed}")
    return frames


def derive_plot_data(
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aggregate route-level terminal states into the plotted categories."""

    routes = frames["routes"]
    counts = routes["terminal_state"].value_counts().to_dict()
    rows: list[dict[str, Any]] = []
    for order, state in enumerate(TERMINAL_ORDER, start=1):
        count = int(counts.get(state, 0))
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "terminal_outcome",
                "display_order": order,
                "terminal_state": state,
                "display_label": TERMINAL_LABELS[state].replace("\n", " "),
                "route_count": count,
                "share": count / len(routes),
                "detail": TERMINAL_DETAILS[state],
                "style_key": STYLE_KEYS[state],
                "source_field": "recovery_route_decisions.tsv:terminal_state",
            }
        )
    rows.append(
        {
            "schema_version": SCHEMA,
            "record_type": "posterior_boundary",
            "display_order": 1,
            "terminal_state": "valid_primary_h0_h4",
            "display_label": "Completed shared-variant tests",
            "route_count": 0,
            "share": 0.0,
            "detail": "Shared-variant probability unavailable; no test reached calculation",
            "style_key": "posterior_unavailable_vermillion",
            "source_field": "recovery_colocalization.tsv.gz:data_rows",
        }
    )
    plot_data = pd.DataFrame(rows)
    derived = {
        "route_count": len(routes),
        "candidate_context_count": routes["candidate_id"].nunique(),
        "unique_gene_count": routes["gene"].nunique(),
        "eqtl_route_count": int(routes["qtl_type"].eq("eQTL").sum()),
        "sqtl_route_count": int(routes["qtl_type"].eq("sQTL").sum()),
        "terminal_counts": {
            state: int(counts.get(state, 0)) for state in TERMINAL_ORDER
        },
        "valid_primary_h0_h4_results": len(frames["coloc"]),
        "posterior_rows": int(
            pd.to_numeric(frames["qc"]["posterior_rows"], errors="raise").sum()
        ),
        "pp_h4_state": "unavailable",
    }
    require(
        sum(derived["terminal_counts"].values()) == derived["route_count"],
        "Terminal states do not partition the route set",
    )
    return plot_data, derived


def build_science_checks(derived: dict[str, Any]) -> pd.DataFrame:
    values: list[tuple[str, Any, Any, str]] = [
        ("route_count", 54, derived["route_count"], "Prespecified nuclear QTL routes."),
        (
            "candidate_context_count",
            27,
            derived["candidate_context_count"],
            "Nuclear gene-by-network contexts represented by paired routes.",
        ),
        ("unique_gene_count", 19, derived["unique_gene_count"], "Unique nuclear genes."),
        ("eqtl_route_count", 27, derived["eqtl_route_count"], "One eQTL route per context."),
        ("sqtl_route_count", 27, derived["sqtl_route_count"], "One sQTL route per context."),
    ]
    for state in TERMINAL_ORDER:
        values.append(
            (
                f"terminal_count__{state}",
                EXPECTED_TERMINAL_COUNTS[state],
                derived["terminal_counts"][state],
                "Mutually exclusive terminal-route count.",
            )
        )
    values.extend(
        [
            (
                "terminal_partition_total",
                54,
                sum(derived["terminal_counts"].values()),
                "Terminal categories partition all routes and are not sequential losses.",
            ),
            (
                "valid_primary_h0_h4_results",
                0,
                derived["valid_primary_h0_h4_results"],
                "The primary colocalization result table is header-only.",
            ),
            (
                "qc_posterior_rows",
                0,
                derived["posterior_rows"],
                "No QC route reached posterior estimation.",
            ),
            (
                "pp_h4_state",
                "unavailable",
                derived["pp_h4_state"],
                "No posterior estimate may be interpreted as PP.H4 equal to zero.",
            ),
        ]
    )
    return make_checks(SCHEMA, values)


def render_figure(plot_data: pd.DataFrame, derived: dict[str, Any]):
    figure, axis = new_canvas()
    # The presentation style requests tight bounding boxes and constrained
    # layout. This full-canvas composition needs exact slide-native pixels.
    figure.set_layout_engine(None)
    matplotlib.rcParams["savefig.bbox"] = None
    matplotlib.rcParams["savefig.pad_inches"] = 0.0

    rounded_box(axis, 0.014, 0.075, 0.716, 0.86, face=WHITE, edge=LIGHT, linewidth=1.0)
    panel_heading(
        axis,
        "A",
        "Why 54 planned gene tests stopped",
        0.032,
        0.892,
    )
    add_text(
        axis,
        0.056,
        0.817,
        "27 gene–network pairs  •  27 expression tests  •  27 splicing tests",
        size=10.2,
        color=MID,
    )

    outcomes = plot_data.loc[plot_data["record_type"].eq("terminal_outcome")].sort_values(
        "display_order"
    )
    bar_x, bar_y, bar_width, bar_height = 0.055, 0.565, 0.635, 0.135
    faces = {
        "no_regional_gwas_signal": GRAY,
        "no_regional_qtl_signal": LIGHT,
        "model_or_ld_incompatible": VERMILLION,
        "not_assessable": WHITE,
    }
    text_colors = {
        "no_regional_gwas_signal": DARK,
        "no_regional_qtl_signal": DARK,
        "model_or_ld_incompatible": WHITE,
        "not_assessable": DARK,
    }
    offset = 0.0
    for row in outcomes.itertuples(index=False):
        width = bar_width * float(row.route_count) / derived["route_count"]
        hatch = "////" if row.terminal_state == "not_assessable" else None
        axis.add_patch(
            Rectangle(
                (bar_x + offset, bar_y),
                width,
                bar_height,
                transform=axis.transAxes,
                facecolor=faces[row.terminal_state],
                edgecolor=CHARCOAL,
                linewidth=1.0,
                hatch=hatch,
                zorder=2,
            )
        )
        center = bar_x + offset + width / 2
        if row.terminal_state == "no_regional_gwas_signal":
            add_text(
                axis,
                center,
                bar_y + bar_height / 2,
                "42   No strong AD variant signal near the gene",
                size=11.2,
                color=text_colors[row.terminal_state],
                weight="bold",
                ha="center",
            )
        else:
            add_text(
                axis,
                center,
                bar_y + bar_height / 2,
                str(int(row.route_count)),
                size=11.0,
                color=text_colors[row.terminal_state],
                weight="bold",
                ha="center",
            )
        offset += width

    card_x = [0.032, 0.205, 0.378, 0.551]
    card_width = 0.157
    for x, row in zip(card_x, outcomes.itertuples(index=False), strict=True):
        state = row.terminal_state
        face = PALE_VERMILLION if state == "model_or_ld_incompatible" else PALE
        hatch = "////" if state == "not_assessable" else None
        rounded_box(
            axis,
            x,
            0.215,
            card_width,
            0.25,
            face=face,
            edge=VERMILLION if state == "model_or_ld_incompatible" else LIGHT,
            linewidth=1.0,
            hatch=hatch,
        )
        add_text(
            axis,
            x + 0.012,
            0.417,
            str(int(row.route_count)),
            size=16.0,
            color=VERMILLION if state == "model_or_ld_incompatible" else NAVY,
            weight="bold",
        )
        add_text(
            axis,
            x + 0.012,
            0.335,
            TERMINAL_LABELS[state],
            size=9.0,
            color=DARK,
            weight="bold",
            va="center",
            linespacing=1.02,
        )
        add_text(
            axis,
            x + 0.012,
            0.265,
            TERMINAL_DETAILS[state],
            size=9.0,
            color=MID,
            va="center",
            linespacing=1.08,
        )

    rounded_box(
        axis,
        0.752,
        0.075,
        0.234,
        0.86,
        face=PALE_VERMILLION,
        edge=VERMILLION,
        linewidth=1.2,
    )
    panel_heading(axis, "B", "Same variant?", 0.773, 0.892)
    add_text(
        axis,
        0.869,
        0.665,
        "0",
        size=48.0,
        color=VERMILLION,
        weight="bold",
        ha="center",
    )
    add_text(
        axis,
        0.869,
        0.535,
        "completed tests",
        size=13.0,
        color=DARK,
        weight="bold",
        ha="center",
        linespacing=1.08,
    )
    axis.plot(
        [0.785, 0.953],
        [0.420, 0.420],
        transform=axis.transAxes,
        color=VERMILLION,
        linewidth=1.0,
        alpha=0.65,
    )
    add_text(
        axis,
        0.869,
        0.337,
        "Probability not calculated",
        size=13.2,
        color=VERMILLION,
        weight="bold",
        ha="center",
    )
    add_text(
        axis,
        0.869,
        0.240,
        "No test had all\nrequired inputs",
        size=9.5,
        color=MID,
        ha="center",
        linespacing=1.12,
    )

    add_text(
        axis,
        0.032,
        0.115,
        "Each test appears in one category—not a sequence of losses.",
        size=9.0,
        color=NAVY,
        weight="bold",
    )
    add_text(
        axis,
        0.707,
        0.115,
        "A test stops at its first missing requirement.",
        size=9.0,
        color=MID,
        ha="right",
    )
    return figure


CAPTION = """
**All planned tests stopped before the shared-variant analysis.** The 54 tests
comprise one expression test and one splicing test for each of 27 gene–network
pairs. The reasons were: 42 lacked a strong AD variant signal near the gene,
four lacked a strong gene-expression signal, two lacked the required prediction
method or matching variant-correlation data, and six had unresolved splicing
measurements. No test had all required inputs, so the probability that the AD
and gene-activity signals share one variant was unavailable, not zero. Each
test appears in exactly one category; the counts are not sequential losses.
"""


METHODS = """
Terminal-state counts were derived directly from `terminal_state` in
`recovery_route_decisions.tsv`. The route table was required to contain 54
unique route IDs spanning 27 nuclear candidate contexts, with exactly one eQTL
and one sQTL route per context. Counts were validated against
`recovery_status.tsv`; all blocking checks in `recovery_checks.tsv` were
required to pass. Route IDs and terminal states were matched one-to-one to the
54 rows in `recovery_colocalization_qc.tsv`, whose `posterior_rows` values were
required to be zero. `recovery_colocalization.tsv.gz` was required to retain its
declared H0-H4 columns while containing zero data rows. The graphic is a
terminal-outcome stacked bar—not a sequential attrition funnel—and was exported
at 12.4 × 4.7 inches as 450-DPI PNG plus editable PDF and SVG.
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
            "route_count": derived["route_count"],
            "candidate_context_count": derived["candidate_context_count"],
            "unique_gene_count": derived["unique_gene_count"],
            "eqtl_route_count": derived["eqtl_route_count"],
            "sqtl_route_count": derived["sqtl_route_count"],
            "no_regional_gwas_signal_routes": derived["terminal_counts"][
                "no_regional_gwas_signal"
            ],
            "no_regional_qtl_signal_routes": derived["terminal_counts"][
                "no_regional_qtl_signal"
            ],
            "model_or_ld_incompatible_routes": derived["terminal_counts"][
                "model_or_ld_incompatible"
            ],
            "not_assessable_routes": derived["terminal_counts"]["not_assessable"],
            "valid_primary_h0_h4_results": derived["valid_primary_h0_h4_results"],
            "pp_h4_state": derived["pp_h4_state"],
            "terminal_categories_mutually_exclusive": True,
        },
        force=args.force,
        visual_review_status=args.visual_review_status,
    )


if __name__ == "__main__":
    main()
