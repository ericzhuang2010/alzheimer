#!/usr/bin/env python3
"""Render a compact slide summary of CSF endophenotype gate outcomes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from phase19_slide_figure_common import (
    BLUE,
    DARK,
    GRAY,
    LIGHT,
    MID,
    NAVY,
    PALE,
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
    validate_source_status,
)
from matplotlib.patches import Rectangle


SCHEMA = "genetic_support_csf_outcome_summary_v1"
INPUT_SCHEMA = "phase19_endophenotype_gwas_qtl_extension_v1"
STEM = "genetic_support_csf_outcome_summary"
DEFAULT_INPUT_ROOT = (
    "results/minerva_production/"
    "19_genetic_support_endophenotype_gwas_qtl_extension"
)
DEFAULT_OUTPUT_ROOT = (
    "results/figures/analysis/phase_19_genetic_support/csf_outcome_summary"
)
REQUIRED_FILES = {
    "gates": "endophenotype_gate_decisions.tsv",
    "status": "endophenotype_status.tsv",
    "checks": "endophenotype_checks.tsv",
}
TRAIT_ORDER = ["csf_abeta42", "csf_total_tau", "csf_ptau181"]
TRAIT_LABELS = {
    "csf_abeta42": "Amyloid-β 42",
    "csf_total_tau": "Total tau",
    "csf_ptau181": "p-tau181",
}
EXPECTED_ACCESSIONS = {
    "csf_abeta42": "GCST90726396",
    "csf_total_tau": "GCST90726397",
    "csf_ptau181": "GCST90726398",
}
POSITIVE_STATE = "regional_and_gene_based_signal"
NO_SIGNAL_STATE = "no_qualifying_gwas_signal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    return parser.parse_args()


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def validate_inputs(input_root: Path) -> dict[str, pd.DataFrame]:
    paths = {key: input_root / name for key, name in REQUIRED_FILES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    require(not missing, "Missing CSF figure inputs: " + ", ".join(missing))

    gates = pd.read_csv(paths["gates"], sep="\t", low_memory=False)
    source_status = validate_source_status(
        paths["status"],
        status_column="validation_status",
        accepted={"validated_complete_endophenotype_gwas_qtl_extension"},
    )
    source_checks = pd.read_csv(paths["checks"], sep="\t", low_memory=False)

    for label, frame in {
        "gate decisions": gates,
        "source status": source_status,
        "source checks": source_checks,
    }.items():
        require("schema_version" in frame.columns, f"{label} lacks schema_version")
        require(
            set(frame["schema_version"].dropna().astype(str)) == {INPUT_SCHEMA},
            f"Unexpected schema in {label}",
        )

    required_gate_columns = {
        "screen_id",
        "gene",
        "trait_id",
        "source_accession",
        "regional_coverage_pass",
        "regional_signal",
        "magma_signal",
        "gate_state",
        "decision_frozen_before_qtl_result",
    }
    require(
        required_gate_columns.issubset(gates.columns),
        "Gate-decision table lacks required columns",
    )
    require(len(gates) == 57, "Expected 57 nuclear gene-by-trait screens")
    require(gates["screen_id"].nunique() == 57, "Screen IDs are not unique")
    require(gates["gene"].nunique() == 19, "Expected 19 nuclear genes")
    require(set(gates["trait_id"]) == set(TRAIT_ORDER), "Unexpected CSF traits")
    require(
        set(gates["gate_state"]) == {POSITIVE_STATE, NO_SIGNAL_STATE},
        "Unexpected CSF gate state",
    )
    require(
        gates["regional_coverage_pass"].map(truth).all(),
        "At least one nuclear screen lacks regional coverage",
    )
    require(
        gates["decision_frozen_before_qtl_result"].map(truth).all(),
        "A gate decision was not frozen before the QTL result",
    )

    positive = gates["gate_state"].eq(POSITIVE_STATE)
    both_signals = gates["regional_signal"].map(truth) & gates["magma_signal"].map(truth)
    require(positive.equals(both_signals), "Gate state disagrees with signal booleans")
    require(int(positive.sum()) == 3, "Expected three positive CSF gate decisions")
    require(set(gates.loc[positive, "gene"]) == {"APOE"}, "APOE must be the only positive gene")

    require(len(source_status) == 1, "Expected one source-status row")
    status = source_status.iloc[0]
    require(str(status["technical_status"]) == "validated_complete", "Source is not complete")
    require(int(status["blocking_check_failures"]) == 0, "Source has blocking failures")
    require(int(status["nuclear_gene_biomarker_screens"]) == 57, "Status screen count changed")
    require(int(status["regional_signal_pairs"]) == 3, "Status regional-signal count changed")
    require(int(status["candidate_magma_signal_pairs"]) == 3, "Status MAGMA count changed")
    require(
        int(status["newly_biomarker_supported_unique_genes"]) == 0,
        "Expected no newly biomarker-supported genes",
    )
    require("status" in source_checks.columns, "Source checks lack status")
    require(source_checks["status"].astype(str).str.lower().eq("pass").all(), "A source check failed")

    return {
        "gates": gates,
        "status": source_status,
        "checks": source_checks,
        "paths": pd.DataFrame({"key": list(paths), "path": [str(path) for path in paths.values()]}),
    }


def derive_plot_data(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, Any]]:
    gates = frames["gates"]
    source_status = frames["status"].iloc[0]
    rows: list[dict[str, Any]] = []

    for order, trait_id in enumerate(TRAIT_ORDER, 1):
        subset = gates.loc[gates["trait_id"].eq(trait_id)].copy()
        positive = subset.loc[subset["gate_state"].eq(POSITIVE_STATE)]
        no_signal = subset.loc[subset["gate_state"].eq(NO_SIGNAL_STATE)]
        accessions = set(subset["source_accession"].astype(str))
        require(len(subset) == 19, f"Expected 19 screens for {trait_id}")
        require(len(positive) == 1, f"Expected one positive decision for {trait_id}")
        require(positive.iloc[0]["gene"] == "APOE", f"Positive gene changed for {trait_id}")
        require(len(no_signal) == 18, f"Expected 18 no-signal decisions for {trait_id}")
        require(accessions == {EXPECTED_ACCESSIONS[trait_id]}, f"Accession changed for {trait_id}")
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "trait_tile",
                "display_order": order,
                "trait_id": trait_id,
                "trait_label": TRAIT_LABELS[trait_id],
                "source_accession": next(iter(accessions)),
                "total_screens": len(subset),
                "apoe_positive_decisions": len(positive),
                "other_gene_no_signal_decisions": len(no_signal),
                "newly_supported_unique_genes": 0,
                "primary_label": "APOE",
                "secondary_label": "Regional + gene-based signal",
                "tertiary_label": "Other nuclear genes: no qualifying signal",
                "style_key": "apoe_blue_vs_no_signal_gray",
                "source_rows": "endophenotype_gate_decisions.tsv",
            }
        )

    positive = gates.loc[gates["gate_state"].eq(POSITIVE_STATE)]
    no_signal = gates.loc[gates["gate_state"].eq(NO_SIGNAL_STATE)]
    newly_supported = int(source_status["newly_biomarker_supported_unique_genes"])
    rows.append(
        {
            "schema_version": SCHEMA,
            "record_type": "aggregate",
            "display_order": 4,
            "trait_id": "all_three_traits",
            "trait_label": "All CSF traits",
            "source_accession": "GCST90726396;GCST90726397;GCST90726398",
            "total_screens": len(gates),
            "apoe_positive_decisions": len(positive),
            "other_gene_no_signal_decisions": len(no_signal),
            "newly_supported_unique_genes": newly_supported,
            "primary_label": "Same gene across three traits: APOE",
            "secondary_label": "Three positive gate decisions; 54 without qualifying signal",
            "tertiary_label": "No molecular mechanism or colocalization established",
            "style_key": "aggregate_blue_gray",
            "source_rows": "endophenotype_gate_decisions.tsv;endophenotype_status.tsv",
        }
    )
    rows.append(
        {
            "schema_version": SCHEMA,
            "record_type": "interpretive_boundary",
            "display_order": 5,
            "trait_id": "not_applicable",
            "trait_label": "Interpretive boundary",
            "source_accession": "not_applicable",
            "total_screens": len(gates),
            "apoe_positive_decisions": len(positive),
            "other_gene_no_signal_decisions": len(no_signal),
            "newly_supported_unique_genes": newly_supported,
            "primary_label": "Three positive decisions represent one gene, not three genes",
            "secondary_label": "Regional + MAGMA gates do not establish a molecular mechanism or colocalization",
            "tertiary_label": "APOE was already supported before this extension",
            "style_key": "interpretive_boundary_navy",
            "source_rows": "endophenotype_gate_decisions.tsv;endophenotype_status.tsv",
        }
    )

    plot_data = pd.DataFrame(rows)
    derived = {
        "total_screens": len(gates),
        "unique_genes": gates["gene"].nunique(),
        "trait_count": gates["trait_id"].nunique(),
        "positive_decisions": len(positive),
        "no_signal_decisions": len(no_signal),
        "positive_genes": sorted(positive["gene"].unique()),
        "newly_supported_unique_genes": newly_supported,
        "visible_text": " ".join(
            plot_data[["trait_label", "primary_label", "secondary_label", "tertiary_label"]]
            .astype(str)
            .to_numpy()
            .ravel()
        ),
    }
    return plot_data, derived


def science_checks(plot_data: pd.DataFrame, derived: dict[str, Any], frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    gates = frames["gates"]
    per_trait_positive = "|".join(
        str(int((gates.loc[gates["trait_id"].eq(trait), "gate_state"] == POSITIVE_STATE).sum()))
        for trait in TRAIT_ORDER
    )
    per_trait_no_signal = "|".join(
        str(int((gates.loc[gates["trait_id"].eq(trait), "gate_state"] == NO_SIGNAL_STATE).sum()))
        for trait in TRAIT_ORDER
    )
    pvalue_columns = sorted(
        set(plot_data.columns) & {"regional_min_p", "magma_p", "minus_log10_p", "neg_log10_p"}
    )
    visible_lower = derived["visible_text"].lower()
    return make_checks(
        SCHEMA,
        [
            ("source_schema", INPUT_SCHEMA, gates.iloc[0]["schema_version"], "Validated endophenotype schema."),
            ("nuclear_gene_trait_screens", 57, derived["total_screens"], "Nineteen genes by three traits."),
            ("unique_nuclear_genes", 19, derived["unique_genes"], "Nuclear candidate count."),
            ("csf_traits", 3, derived["trait_count"], "CSF amyloid-beta 42, total tau, and p-tau181."),
            ("positive_gate_decisions", 3, derived["positive_decisions"], "One positive decision per CSF trait."),
            ("no_qualifying_signal_decisions", 54, derived["no_signal_decisions"], "Eighteen per CSF trait."),
            ("per_trait_positive_counts", "1|1|1", per_trait_positive, "Same positive count in each tile."),
            ("per_trait_no_signal_counts", "18|18|18", per_trait_no_signal, "Same no-signal count in each tile."),
            ("positive_gene_identity", "APOE", "|".join(derived["positive_genes"]), "All positive decisions are APOE."),
            ("newly_supported_unique_genes", 0, derived["newly_supported_unique_genes"], "APOE was supported previously."),
            ("pvalue_geometry_columns", "absent", "absent" if not pvalue_columns else "|".join(pvalue_columns), "No P value or -log10(P) enters plotted data."),
            ("mechanism_boundary_visible", "present", "present" if "do not establish a molecular mechanism" in visible_lower else "absent", "Gate evidence is not mechanistic colocalization."),
            ("internal_phase_label_visible", "absent", "absent" if "phase 19" not in visible_lower and "phase19" not in visible_lower else "present", "Artwork remains reusable."),
        ],
    )


def draw_unit_bar(axis: Any, x: float, y: float, width: float, height: float) -> None:
    gap = 0.0016
    unit_width = (width - gap * 18) / 19
    for index in range(19):
        axis.add_patch(
            Rectangle(
                (x + index * (unit_width + gap), y),
                unit_width,
                height,
                transform=axis.transAxes,
                facecolor=BLUE if index == 0 else GRAY,
                edgecolor=DARK,
                linewidth=0.35,
                zorder=3,
            )
        )


def render_figure(plot_data: pd.DataFrame) -> Any:
    figure, axis = new_canvas()
    panel_heading(axis, "A", "Trait-level gate decisions", 0.020, 0.955)
    panel_heading(axis, "B", "All 57 screens", 0.765, 0.955)

    tiles = plot_data.loc[plot_data["record_type"].eq("trait_tile")].sort_values("display_order")
    tile_x = [0.020, 0.266, 0.512]
    for x, row in zip(tile_x, tiles.itertuples(index=False), strict=True):
        rounded_box(axis, x, 0.205, 0.226, 0.680, face=PALE, edge=LIGHT, linewidth=1.2, radius=0.012)
        add_text(axis, x + 0.018, 0.825, row.trait_label, size=13.2, color=NAVY, weight="bold")
        add_text(axis, x + 0.018, 0.782, row.source_accession, size=9.0, color=MID)

        add_text(axis, x + 0.018, 0.665, str(row.apoe_positive_decisions), size=31.0, color=BLUE, weight="bold")
        add_text(axis, x + 0.065, 0.682, "APOE", size=15.0, color=NAVY, weight="bold")
        add_text(axis, x + 0.065, 0.632, "regional + gene-based signal", size=9.0, color=BLUE, weight="bold")

        draw_unit_bar(axis, x + 0.018, 0.515, 0.190, 0.052)
        add_text(axis, x + 0.018, 0.472, "1 APOE", size=9.0, color=BLUE, weight="bold")
        add_text(axis, x + 0.208, 0.472, "18 other genes", size=9.0, color=DARK, weight="bold", ha="right")

        add_text(axis, x + 0.018, 0.350, str(row.other_gene_no_signal_decisions), size=27.0, color=DARK, weight="bold")
        add_text(axis, x + 0.072, 0.365, "other nuclear genes", size=10.2, color=DARK, weight="bold")
        add_text(axis, x + 0.018, 0.287, "No qualifying regional + MAGMA signal", size=9.0, color=MID)

    aggregate = plot_data.loc[plot_data["record_type"].eq("aggregate")].iloc[0]
    rounded_box(axis, 0.765, 0.205, 0.215, 0.680, face=WHITE, edge=NAVY, linewidth=1.5, radius=0.012)
    add_text(axis, 0.785, 0.820, "3", size=33.0, color=BLUE, weight="bold")
    add_text(axis, 0.840, 0.835, "APOE-positive", size=12.0, color=NAVY, weight="bold")
    add_text(axis, 0.840, 0.790, "gate decisions", size=10.0, color=MID, weight="bold")
    add_text(axis, 0.785, 0.728, "Same gene in all three traits", size=9.2, color=BLUE, weight="bold")

    axis.add_patch(
        Rectangle(
            (0.785, 0.590), 0.174, 0.063,
            transform=axis.transAxes, facecolor=GRAY, edgecolor=DARK, linewidth=0.7, zorder=2,
        )
    )
    axis.add_patch(
        Rectangle(
            (0.785, 0.590), 0.174 * (3 / 57), 0.063,
            transform=axis.transAxes, facecolor=BLUE, edgecolor=DARK, linewidth=0.7, zorder=3,
        )
    )
    add_text(axis, 0.785, 0.555, "3", size=9.0, color=BLUE, weight="bold")
    add_text(axis, 0.959, 0.555, "54", size=9.0, color=DARK, weight="bold", ha="right")
    add_text(axis, 0.785, 0.472, str(aggregate.other_gene_no_signal_decisions), size=27.0, color=DARK, weight="bold")
    add_text(axis, 0.847, 0.485, "without qualifying", size=9.5, color=DARK, weight="bold")
    add_text(axis, 0.847, 0.445, "GWAS signal", size=9.5, color=DARK, weight="bold")

    rounded_box(axis, 0.785, 0.270, 0.174, 0.105, face=PALE_BLUE, edge=BLUE, linewidth=1.0, radius=0.009)
    add_text(axis, 0.805, 0.326, str(aggregate.newly_supported_unique_genes), size=25.0, color=BLUE, weight="bold")
    add_text(axis, 0.850, 0.337, "newly supported", size=9.2, color=NAVY, weight="bold")
    add_text(axis, 0.850, 0.298, "genes", size=9.2, color=NAVY, weight="bold")

    rounded_box(axis, 0.020, 0.030, 0.960, 0.120, face=NAVY, edge=NAVY, linewidth=1.0, radius=0.010)
    add_text(
        axis, 0.500, 0.104,
        "Three positive decisions = APOE across three traits, not three genes",
        size=12.0, color=WHITE, weight="bold", ha="center",
    )
    add_text(
        axis, 0.500, 0.063,
        "Regional + MAGMA gates do not establish a molecular mechanism or colocalization.",
        size=9.4, color="#DDE7F2", ha="center",
    )
    return figure


CAPTION = """# CSF endophenotype gate outcomes

Across amyloid-β 42, total tau, and p-tau181, APOE was the only nuclear
candidate to pass both the regional and corrected MAGMA gene-based gates. This
produced three positive gene-by-trait decisions, while the other 18 nuclear
genes produced 54 decisions without a qualifying signal. The three positive
decisions represent the same previously supported gene across three traits;
the extension added zero newly supported genes. These gates do not establish a
molecular mechanism or colocalization.
"""


METHODS = """# Figure methods

The figure reads the validated endophenotype `gate_decisions`, `status`, and
`checks` tables. Each of the 57 nuclear gene-by-trait screens is classified
from its stored `gate_state`, with the regional- and MAGMA-signal booleans used
to verify that classification. Counts are deterministic gate outcomes, so
uncertainty intervals and significance annotations are not applicable.

No P value is transformed or plotted. In particular, the stored APOE
amyloid-β 42 regional P value underflows to numerical zero, so the renderer
deliberately avoids `-log10(P)` geometry. Passing the regional and corrected
MAGMA gates is not relabeled as molecular-QTL colocalization or mechanistic
validation. Blue and gray are supplemented by direct labels and unit bars;
PDF and SVG are vector outputs and the PNG is exported at 450 DPI.
"""


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    input_root = resolve(root, args.input_root)
    output_root = resolve(root, args.output_root)
    frames = validate_inputs(input_root)
    plot_data, derived = derive_plot_data(frames)
    checks = science_checks(plot_data, derived, frames)
    source_paths = [input_root / REQUIRED_FILES[key] for key in ("gates", "status", "checks")]

    def render(staging: Path) -> None:
        render_triplet(render_figure(plot_data), staging, STEM)

    publish_package(
        schema=SCHEMA,
        stem=STEM,
        output_root=output_root,
        source_paths=source_paths,
        renderer_path=Path(__file__).resolve(),
        plot_data=plot_data,
        science_checks=checks,
        caption=CAPTION,
        methods=METHODS,
        render=render,
        status_fields={
            "scientific_status": "descriptive_csf_gate_summary",
            "nuclear_gene_trait_screens": derived["total_screens"],
            "apoe_positive_gate_decisions": derived["positive_decisions"],
            "no_qualifying_signal_decisions": derived["no_signal_decisions"],
            "newly_supported_unique_genes": derived["newly_supported_unique_genes"],
            "underflow_safe_no_pvalue_geometry": True,
            "visible_internal_phase_label": False,
        },
        force=args.force,
        visual_review_status=args.visual_review_status,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
