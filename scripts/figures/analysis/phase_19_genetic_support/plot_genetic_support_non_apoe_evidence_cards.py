#!/usr/bin/env python3
"""Render four evidence-boundary cards for non-APOE Phase 19 candidates."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from phase19_slide_figure_common import (
    AMBER,
    CHARCOAL,
    DARK,
    LIGHT,
    MID,
    NAVY,
    PALE_AMBER,
    PALE_GRAY,
    PALE_VERMILLION,
    VERMILLION,
    WHITE,
    add_text,
    make_checks,
    new_canvas,
    output_names,
    publish_package,
    render_triplet,
    require,
    rounded_box,
    truth,
    validate_blocking_checks,
    validate_source_status,
)


SCHEMA = "genetic_support_non_apoe_evidence_cards_v1"
STEM = "genetic_support_non_apoe_evidence_cards"
DEFAULT_OUTPUT_ROOT = (
    "results/figures/analysis/phase_19_genetic_support/non_apoe_evidence"
)
CARD_ORDER = ["COX7C", "SELENOW", "RPS15", "ANKRD11"]
EXPECTED_ROUTE_STATES = {
    "COX7C": {"no_regional_qtl_signal": 2, "not_assessable": 2},
    "SELENOW": {"no_regional_gwas_signal": 2},
    "RPS15": {
        "no_regional_qtl_signal": 1,
        "model_or_ld_incompatible": 1,
        "not_assessable": 2,
    },
    "ANKRD11": {"no_regional_qtl_signal": 1, "not_assessable": 1},
}
EXPECTED_REGIONAL_P = {
    "COX7C": 8.579e-14,
    "SELENOW": 6.410e-5,
    "RPS15": 4.089e-30,
    "ANKRD11": 1.283e-11,
}
EXPECTED_LEADS = {
    "COX7C": "rs62375397",
    "SELENOW": "rs17206581",
    "RPS15": "rs12151021",
    "ANKRD11": "rs56407236",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier1-root",
        default="results/minerva_production/19_genetic_support_tier1",
    )
    parser.add_argument(
        "--recovery-root",
        default="results/minerva_production/19_genetic_support_tier2_recovery",
    )
    parser.add_argument(
        "--rps15-root",
        default=(
            "results/minerva_production/"
            "19_genetic_support_opc_rps15_public_recovery"
        ),
    )
    parser.add_argument(
        "--endophenotype-root",
        default=(
            "results/minerva_production/"
            "19_genetic_support_endophenotype_gwas_qtl_extension"
        ),
    )
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    return parser.parse_args(argv)


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def format_sci(value: float, digits: int = 3) -> str:
    """Return a slide-readable scientific-notation string using Unicode."""

    mantissa, exponent = f"{float(value):.{digits}e}".split("e")
    superscript = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return f"{mantissa} × 10{str(int(exponent)).translate(superscript)}"


def _read(path: Path, expected_schema: str) -> pd.DataFrame:
    require(path.is_file(), f"Missing source table: {path}")
    frame = pd.read_csv(path, sep="\t", low_memory=False)
    require("schema_version" in frame.columns, f"Missing schema_version: {path}")
    require(
        set(frame["schema_version"].dropna().astype(str)) == {expected_schema},
        f"Unexpected source schema: {path}",
    )
    return frame


def load_sources(
    tier1_root: Path,
    recovery_root: Path,
    rps15_root: Path,
    endophenotype_root: Path,
) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    paths = {
        "tier1_summary": tier1_root / "genetic_support_evidence_summary.tsv",
        "tier1_common": tier1_root / "genetic_support_common_variant_evidence.tsv.gz",
        "tier1_status": tier1_root / "genetic_support_status.tsv",
        "tier1_checks": tier1_root / "genetic_support_checks.tsv",
        "regional_gwas": recovery_root / "recovery_regional_gwas_summary.tsv",
        "regional_qtl": recovery_root / "recovery_regional_qtl_summary.tsv",
        "routes": recovery_root / "recovery_route_decisions.tsv",
        "recovery_status": recovery_root / "recovery_status.tsv",
        "recovery_checks": recovery_root / "recovery_checks.tsv",
        "rps15_summary": rps15_root / "opc_rps15_evidence_summary.tsv",
        "rps15_status": rps15_root / "opc_rps15_status.tsv",
        "rps15_checks": rps15_root / "opc_rps15_checks.tsv",
        "endo_gates": endophenotype_root / "endophenotype_gate_decisions.tsv",
        "endo_status": endophenotype_root / "endophenotype_status.tsv",
        "endo_checks": endophenotype_root / "endophenotype_checks.tsv",
    }
    for path in paths.values():
        require(path.is_file(), f"Missing figure input: {path}")

    validate_source_status(
        paths["tier1_status"],
        status_column="technical_status",
        accepted={"validated_complete_tier1"},
    )
    validate_blocking_checks(paths["tier1_checks"])
    validate_source_status(
        paths["recovery_status"],
        status_column="validation_status",
        accepted={"validated_complete_tier2_classical_coloc_recovery"},
    )
    validate_blocking_checks(paths["recovery_checks"])
    validate_source_status(
        paths["rps15_status"],
        status_column="validation_status",
        accepted={"validated_complete_opc_rps15_public_recovery"},
    )
    validate_blocking_checks(paths["rps15_checks"])
    validate_source_status(
        paths["endo_status"],
        status_column="validation_status",
        accepted={"validated_complete_endophenotype_gwas_qtl_extension"},
    )
    validate_blocking_checks(paths["endo_checks"])

    frames = {
        "tier1_summary": _read(paths["tier1_summary"], "human_genetic_support_tier1_v1"),
        "tier1_common": _read(paths["tier1_common"], "human_genetic_support_tier1_v1"),
        "regional_gwas": _read(
            paths["regional_gwas"],
            "human_genetic_support_tier2_classical_coloc_recovery_v1",
        ),
        "regional_qtl": _read(
            paths["regional_qtl"],
            "human_genetic_support_tier2_classical_coloc_recovery_v1",
        ),
        "routes": _read(
            paths["routes"],
            "human_genetic_support_tier2_classical_coloc_recovery_v1",
        ),
        "rps15_summary": _read(
            paths["rps15_summary"],
            "phase19_opc_rps15_public_recovery_v1",
        ),
        "endo_gates": _read(
            paths["endo_gates"],
            "phase19_endophenotype_gwas_qtl_extension_v1",
        ),
    }
    return frames, list(paths.values())


def _one(frame: pd.DataFrame, message: str) -> pd.Series:
    require(len(frame) == 1, f"{message}: expected 1 row, observed {len(frame)}")
    return frame.iloc[0]


def derive_plot_data(
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    tier1 = frames["tier1_summary"]
    common = frames["tier1_common"]
    gwas = frames["regional_gwas"]
    qtl = frames["regional_qtl"]
    routes = frames["routes"]
    rps = frames["rps15_summary"]
    endo = frames["endo_gates"]

    require(set(CARD_ORDER) <= set(tier1["gene"]), "A card gene is absent from Tier 1")
    require(gwas["gene"].is_unique, "Regional GWAS table is not one row per gene")
    require(routes["route_id"].is_unique, "Recovery route IDs are not unique")

    direct_cox = _one(
        common.loc[
            common["gene"].eq("COX7C")
            & common["rsid"].eq("rs2010322")
            & common["direct_candidate_mapping"].map(truth)
        ],
        "COX7C direct summary entry",
    )
    selenow_twas = _one(
        common.loc[
            common["gene"].eq("SELENOW")
            & common["evidence_route"].eq("twas_gene_list")
            & common["direct_candidate_mapping"].map(truth)
        ],
        "SELENOW TWAS-list entry",
    )
    selenow_wightman = common.loc[
        common["gene"].eq("SELENOW")
        & common["evidence_route"].eq("regional_variant")
        & common["gwas_sources"].astype(str).str.contains("Wightman")
    ]
    require(len(selenow_wightman) > 0, "SELENOW Wightman proximity rows are absent")
    selenow_wightman_min = float(selenow_wightman["min_pvalue"].min())

    gwas_rows: dict[str, pd.Series] = {}
    for gene in CARD_ORDER:
        row = _one(gwas.loc[gwas["gene"].eq(gene)], f"{gene} regional GWAS")
        require(
            math.isclose(
                float(row["regional_min_p"]),
                EXPECTED_REGIONAL_P[gene],
                rel_tol=1e-9,
            ),
            f"{gene} regional minimum P changed",
        )
        require(str(row["regional_lead_variant"]) == EXPECTED_LEADS[gene], f"{gene} lead changed")
        gwas_rows[gene] = row

    qtl_rows = {
        "cox_aygun": _one(
            qtl.loc[qtl["gene"].eq("COX7C") & qtl["dataset_id"].eq("QTD000569")],
            "COX7C Aygun eQTL",
        ),
        "cox_walker": _one(
            qtl.loc[qtl["gene"].eq("COX7C") & qtl["dataset_id"].eq("QTD000579")],
            "COX7C Walker eQTL",
        ),
        "rps_walker": _one(
            qtl.loc[qtl["gene"].eq("RPS15") & qtl["dataset_id"].eq("QTD000579")],
            "RPS15 Walker eQTL",
        ),
        "ank_walker": _one(
            qtl.loc[qtl["gene"].eq("ANKRD11") & qtl["dataset_id"].eq("QTD000579")],
            "ANKRD11 Walker eQTL",
        ),
    }
    require(
        not truth(qtl_rows["cox_aygun"]["dense_regional_qtl_signal"])
        and not truth(qtl_rows["cox_walker"]["dense_regional_qtl_signal"]),
        "COX7C dense eQTL gate unexpectedly passed",
    )
    require(
        truth(qtl_rows["rps_walker"]["dense_regional_qtl_signal"]),
        "RPS15 Walker eQTL gate no longer passes",
    )
    require(
        not truth(qtl_rows["ank_walker"]["dense_regional_qtl_signal"]),
        "ANKRD11 Walker eQTL gate unexpectedly passed",
    )

    route_states: dict[str, dict[str, int]] = {}
    for gene in CARD_ORDER:
        observed = {
            str(key): int(value)
            for key, value in routes.loc[routes["gene"].eq(gene), "terminal_state"]
            .value_counts()
            .to_dict()
            .items()
        }
        require(observed == EXPECTED_ROUTE_STATES[gene], f"{gene} route-state counts changed")
        route_states[gene] = observed

    require(len(rps) == 2 and set(rps["context"]) == {"Inhibitory_neurons", "OPCs"}, "RPS15 contexts changed")
    require(rps["gene_evidence_grade"].eq("weak").all(), "RPS15 supplemental grade changed")
    require(rps["gene_outcome"].eq("suggestive_public_support_only").all(), "RPS15 outcome changed")
    require(not rps["gene_validated"].map(truth).any(), "RPS15 unexpectedly gene-validated")
    require(not rps["context_validated"].map(truth).any(), "RPS15 unexpectedly context-validated")
    require(rps["maximum_pp_h4"].isna().all(), "RPS15 PP.H4 should remain unavailable")
    rps_totals = {
        "eligible": int(rps["eligible_routes"].sum()),
        "measured": int(rps["measured_routes"].sum()),
        "positive_rows": int(rps["signal_positive_routes"].sum()),
        "resolved": int(rps["resolved_colocalization_routes"].sum()),
    }
    require(rps_totals == {"eligible": 37, "measured": 31, "positive_rows": 6, "resolved": 0}, "RPS15 route totals changed")
    track_suffixes: set[str] = set()
    for value in rps["signal_route_ids"]:
        for route_id in str(value).split(";"):
            track_suffixes.add(route_id.split("__", 1)[1])
    require(len(track_suffixes) == 3, "RPS15 positive rows no longer reduce to three source tracks")

    csf_pass_counts: dict[str, int] = {}
    for gene in CARD_ORDER:
        subset = endo.loc[endo["gene"].eq(gene)]
        require(len(subset) == 3 and subset["trait_id"].nunique() == 3, f"{gene} CSF screens changed")
        passed = int(subset["gate_state"].eq("regional_and_gene_based_signal").sum())
        require(passed == 0, f"{gene} unexpectedly passed a CSF gate")
        csf_pass_counts[gene] = passed

    cards = [
        {
            "gene": "COX7C",
            "status_label": "WEAK / INCOMPLETE",
            "style_key": "weak_amber",
            "evidence_text": (
                "One published bulk-brain summary record: AD + RNA splicing\n"
                f"Within 1 Mb (Bellenguez): smallest P {format_sci(gwas_rows['COX7C']['regional_min_p'])}\n"
                f"Lead variant {gwas_rows['COX7C']['regional_lead_variant']}"
            ),
            "boundary_text": (
                "One evidence record is repeated in two network settings.\n"
                "The expression test did not pass.\n"
                "The splicing shared-variant test was incomplete."
            ),
            "footer_text": "Initial: weak · 2 network settings     Spinal-fluid: 0/3",
            "qtl_p": float(qtl_rows["cox_walker"]["dense_minimum_p_value"]),
            "qtl_threshold": float(qtl_rows["cox_walker"]["dense_bonferroni_threshold"]),
        },
        {
            "gene": "SELENOW",
            "status_label": "WEAK GENE-LIST EVIDENCE",
            "style_key": "weak_amber",
            "evidence_text": (
                "Published list based on predicted expression includes SELENOW\n"
                f"Bellenguez: smallest P {format_sci(gwas_rows['SELENOW']['regional_min_p'])}\n"
                f"Significance cutoff {format_sci(5e-8, 0)}: not passed"
            ),
            "boundary_text": (
                "No score, independent confirmation, or exact excitatory-neuron match.\n"
                "Wightman variants were only nearby.\n"
                "No expression or splicing follow-up started."
            ),
            "footer_text": "Initial: weak · 1 network setting     Spinal-fluid: 0/3",
            "qtl_p": float("nan"),
            "qtl_threshold": float("nan"),
        },
        {
            "gene": "RPS15",
            "status_label": "TOP FOLLOW-UP; INCOMPLETE",
            "style_key": "unresolved_vermillion",
            "evidence_text": (
                f"Within 1 Mb (Bellenguez): smallest P {format_sci(gwas_rows['RPS15']['regional_min_p'])}\n"
                f"Lead variant {gwas_rows['RPS15']['regional_lead_variant']}\n"
                f"Walker neocortex expression: P {format_sci(qtl_rows['rps_walker']['dense_minimum_p_value'])}\n"
                f"Corrected cutoff {format_sci(qtl_rows['rps_walker']['dense_bonferroni_threshold'])}: passed"
            ),
            "boundary_text": (
                "Expression-prediction data and matching variant correlations were missing.\n"
                "Three bulk-brain tracks had signals, but the gene and cell setting\n"
                "and a shared variant remain untested."
            ),
            "footer_text": "Follow-up: 31/37 measured · 3 tracks     Spinal-fluid: 0/3",
            "qtl_p": float(qtl_rows["rps_walker"]["dense_minimum_p_value"]),
            "qtl_threshold": float(qtl_rows["rps_walker"]["dense_bonferroni_threshold"]),
        },
        {
            "gene": "ANKRD11",
            "status_label": "AD SIGNAL NEARBY ONLY",
            "style_key": "regional_only_gray",
            "evidence_text": (
                f"Within 1 Mb (Bellenguez): smallest P {format_sci(gwas_rows['ANKRD11']['regional_min_p'])}\n"
                f"Lead variant {gwas_rows['ANKRD11']['regional_lead_variant']}\n"
                f"Walker brain expression: P {format_sci(qtl_rows['ank_walker']['dense_minimum_p_value'])}\n"
                f"Corrected cutoff {format_sci(qtl_rows['ank_walker']['dense_bonferroni_threshold'])}: not passed"
            ),
            "boundary_text": (
                "We could not confirm whether splicing data were available.\n"
                "The shared-variant test could not be run.\n"
                "A nearby AD signal does not prove ANKRD11 is the affected gene."
            ),
            "footer_text": "Initial: none found · 1 network setting     Spinal-fluid: 0/3",
            "qtl_p": float(qtl_rows["ank_walker"]["dense_minimum_p_value"]),
            "qtl_threshold": float(qtl_rows["ank_walker"]["dense_bonferroni_threshold"]),
        },
    ]

    rows: list[dict[str, Any]] = []
    for display_order, card in enumerate(cards, 1):
        gene = str(card["gene"])
        tier1_rows = tier1.loc[tier1["gene"].eq(gene)]
        grades = sorted(set(tier1_rows["final_grade"].astype(str)))
        require(len(grades) == 1, f"{gene} has mixed Tier 1 grades")
        state_text = ";".join(
            f"{state}:{count}" for state, count in sorted(route_states[gene].items())
        )
        rows.append(
            {
                "schema_version": SCHEMA,
                "record_type": "candidate_card",
                "display_order": display_order,
                "gene": gene,
                "status_label": card["status_label"],
                "style_key": card["style_key"],
                "tier1_grade": grades[0],
                "tier1_contexts": len(tier1_rows),
                "regional_min_p": float(gwas_rows[gene]["regional_min_p"]),
                "regional_lead_variant": str(gwas_rows[gene]["regional_lead_variant"]),
                "regional_signal": truth(gwas_rows[gene]["regional_gwas_signal"]),
                "qtl_min_p": card["qtl_p"],
                "qtl_threshold": card["qtl_threshold"],
                "terminal_state_summary": state_text,
                "csf_traits_passed": csf_pass_counts[gene],
                "evidence_text": card["evidence_text"],
                "boundary_text": card["boundary_text"],
                "footer_text": card["footer_text"],
                "source_rows": (
                    "genetic_support_evidence_summary.tsv|"
                    "genetic_support_common_variant_evidence.tsv.gz|"
                    "recovery_regional_gwas_summary.tsv|"
                    "recovery_regional_qtl_summary.tsv|"
                    "recovery_route_decisions.tsv|"
                    "opc_rps15_evidence_summary.tsv|"
                    "endophenotype_gate_decisions.tsv"
                ),
            }
        )
    plot_data = pd.DataFrame(rows)
    visible_text = "\n".join(
        plot_data[["gene", "status_label", "evidence_text", "boundary_text", "footer_text"]]
        .astype(str)
        .to_numpy()
        .ravel()
    )
    require("PP.H4" not in visible_text, "Specialist posterior shorthand leaked into the cards")
    require("shared-variant test" in visible_text, "Shared-signal analysis lacks a plain-language explanation")
    require("causal" not in visible_text.lower(), "Causal language leaked into the cards")
    derived = {
        "direct_cox_rsid": str(direct_cox["rsid"]),
        "selenow_twas_target": str(selenow_twas["target_gene"]),
        "selenow_wightman_min_p": selenow_wightman_min,
        "rps15_totals": rps_totals,
        "rps15_unique_tracks": len(track_suffixes),
        "route_states": route_states,
        "visible_text": visible_text,
    }
    return plot_data, derived


def render_figure(plot_data: pd.DataFrame, staging: Path) -> None:
    figure, axis = new_canvas()
    geometry = [
        (0.015, 0.522, 0.477, 0.462),
        (0.508, 0.522, 0.477, 0.462),
        (0.015, 0.045, 0.477, 0.462),
        (0.508, 0.045, 0.477, 0.462),
    ]
    styles = {
        "weak_amber": (PALE_AMBER, AMBER, AMBER),
        "unresolved_vermillion": (PALE_VERMILLION, VERMILLION, VERMILLION),
        "regional_only_gray": (PALE_GRAY, CHARCOAL, VERMILLION),
    }
    cards = plot_data.sort_values("display_order")
    for row, (x, y, width, height) in zip(cards.itertuples(index=False), geometry):
        face, edge, accent = styles[row.style_key]
        evidence_lines = str(row.evidence_text).count("\n") + 1
        boundary_lines = str(row.boundary_text).count("\n") + 1
        rounded_box(
            axis,
            x,
            y,
            width,
            height,
            face=WHITE,
            edge=edge,
            linewidth=1.25,
            radius=0.012,
        )
        rounded_box(
            axis,
            x + 0.001,
            y + height - 0.091,
            width - 0.002,
            0.087,
            face=face,
            edge=edge,
            linewidth=0.0,
            radius=0.010,
        )
        add_text(axis, x + 0.020, y + height - 0.046, row.gene, size=16.5, color=NAVY, weight="bold")
        add_text(
            axis,
            x + width - 0.018,
            y + height - 0.046,
            row.status_label,
            size=9.0,
            color=accent,
            weight="bold",
            ha="right",
        )
        add_text(axis, x + 0.022, y + height - 0.125, "WHAT THE DATA SHOW", size=9.0, color=accent, weight="bold")
        add_text(
            axis,
            x + 0.022,
            y + height - 0.194,
            row.evidence_text,
            size=8.1 if evidence_lines >= 4 else 8.5,
            color=DARK,
            weight="bold",
            va="center",
            linespacing=1.14,
        )
        axis.plot(
            [x + 0.022, x + width - 0.022],
            [y + height - 0.253, y + height - 0.253],
            transform=axis.transAxes,
            color=LIGHT,
            linewidth=0.8,
            zorder=3,
        )
        add_text(axis, x + 0.022, y + height - 0.282, "WHAT THIS DOES NOT PROVE", size=9.0, color=MID, weight="bold")
        add_text(
            axis,
            x + 0.022,
            y + height - 0.351,
            row.boundary_text,
            size=7.9 if boundary_lines >= 3 else 8.2,
            color=DARK,
            va="center",
            linespacing=1.12,
        )
        rounded_box(
            axis,
            x + 0.020,
            y + 0.017,
            width - 0.040,
            0.052,
            face=PALE_GRAY,
            edge=LIGHT,
            linewidth=0.7,
            radius=0.007,
        )
        add_text(
            axis,
            x + width / 2,
            y + 0.043,
            row.footer_text,
            size=9.0,
            color=MID,
            weight="bold",
            ha="center",
        )
    render_triplet(figure, staging, STEM)


def build_checks(plot_data: pd.DataFrame, derived: dict[str, Any]) -> pd.DataFrame:
    regional_flags = {
        row.gene: bool(row.regional_signal) for row in plot_data.itertuples(index=False)
    }
    values = [
        ("card_count", 4, len(plot_data), "Four equal candidate cards."),
        ("card_gene_order", "|".join(CARD_ORDER), "|".join(plot_data.sort_values("display_order")["gene"]), "Frozen card order."),
        ("cox7c_direct_entry", "rs2010322", derived["direct_cox_rsid"], "Tier 1 direct summary record."),
        ("selenow_twas_target", "SELENOW", derived["selenow_twas_target"], "Tier 1 TWAS-list membership."),
        ("rps15_eligible_routes", 37, derived["rps15_totals"]["eligible"], "Sum across two frozen contexts."),
        ("rps15_measured_routes", 31, derived["rps15_totals"]["measured"], "Sum across two frozen contexts."),
        ("rps15_positive_context_rows", 6, derived["rps15_totals"]["positive_rows"], "Three source tracks repeated across two contexts."),
        ("rps15_unique_source_tracks", 3, derived["rps15_unique_tracks"], "Deduplicated after removing candidate prefix."),
        ("rps15_resolved_h0_h4", 0, derived["rps15_totals"]["resolved"], "PP.H4 remains unavailable."),
        ("regional_signal_genes", "ANKRD11|COX7C|RPS15", "|".join(sorted(gene for gene, value in regional_flags.items() if value)), "Bellenguez frozen gate among the four cards."),
        ("csf_passed_traits", 0, int(plot_data["csf_traits_passed"].sum()), "All four genes have zero qualifying CSF gates."),
        ("posterior_shorthand_visible", "absent", "absent" if "PP.H4" not in derived["visible_text"] else "present", "Posterior shorthand is replaced by a shared-variant explanation."),
        ("shared_variant_explanation", "present", "present" if "shared-variant test" in derived["visible_text"] else "absent", "Shared-signal analysis is described in plain language."),
        ("causal_claim", "absent", "absent" if "causal" not in derived["visible_text"].lower() else "present", "Regional signal is not candidate-gene causality."),
    ]
    return make_checks(SCHEMA, values)


CAPTION = """# Non-APOE evidence remains suggestive, regional, or unresolved

Four equal cards summarize the strongest non-APOE observations without using
regional P values as comparable effect sizes. COX7C has one weak bulk-brain
AD–sQTL summary record represented in two network contexts. SELENOW has public
TWAS-list membership but lacks model statistics and exact-context support.
RPS15 combines a highly significant AD region with one passing bulk-neocortex
eQTL gate and three supplemental bulk-brain tracks, but the required model and
source-matched LD are incomplete. ANKRD11 has regional locus evidence only.
None of these four genes passed a CSF follow-up gate, and no primary H0–H4
result was resolved.
"""


METHODS = """# Figure methods

Tier 1 grades and candidate contexts were read from
`genetic_support_evidence_summary.tsv`; direct FunGen summary records were
checked in `genetic_support_common_variant_evidence.tsv.gz`. Bellenguez regional
minimum P values and lead variants came from
`recovery_regional_gwas_summary.tsv`. Candidate eQTL measurements and frozen
Bonferroni gates came from `recovery_regional_qtl_summary.tsv`, while route
limitations came from `recovery_route_decisions.tsv`. The targeted RPS15 counts
were read from `opc_rps15_evidence_summary.tsv`; its six positive context rows
were deduplicated to three source tracks after removing the candidate-context
prefix. CSF counts came from `endophenotype_gate_decisions.tsv`.

The cards are deliberately equal in size because P values from different
sources and tests are not comparable effect sizes. Values are deterministic
source summaries, so no error bars or significance annotations are applicable.
Color, direct text labels, borders, and card headings provide redundant
encoding. “PP.H4 unavailable” means no valid primary posterior was produced; it
does not mean PP.H4 was estimated as zero. Regional association is described as
locus evidence and not as assignment of the candidate gene.
"""


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repository = Path.cwd().resolve()
    tier1_root = resolve(repository, args.tier1_root)
    recovery_root = resolve(repository, args.recovery_root)
    rps15_root = resolve(repository, args.rps15_root)
    endophenotype_root = resolve(repository, args.endophenotype_root)
    output_root = resolve(repository, args.output_root)
    frames, sources = load_sources(
        tier1_root,
        recovery_root,
        rps15_root,
        endophenotype_root,
    )
    plot_data, derived = derive_plot_data(frames)
    checks = build_checks(plot_data, derived)
    publish_package(
        schema=SCHEMA,
        stem=STEM,
        output_root=output_root,
        source_paths=sources,
        renderer_path=Path(__file__).resolve(),
        plot_data=plot_data,
        science_checks=checks,
        caption=CAPTION,
        methods=METHODS,
        render=lambda staging: render_figure(plot_data, staging),
        status_fields={
            "scientific_status": "descriptive_candidate_evidence_boundaries",
            "candidate_cards": len(plot_data),
            "primary_h0_h4_results": 0,
            "new_csf_supported_genes": 0,
        },
        force=args.force,
        visual_review_status=args.visual_review_status,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
