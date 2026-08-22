#!/usr/bin/env python3
"""Render the frozen, gated human-genetic-support workflow for slides."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase19_slide_figure_common import (  # noqa: E402
    BLUE,
    CHARCOAL,
    DARK,
    EXPECTED_PNG_SIZE,
    GRAY,
    LIGHT,
    MID,
    NAVY,
    PALE,
    PALE_BLUE,
    PALE_GRAY,
    WHITE,
    add_text,
    make_checks,
    new_canvas,
    output_names,
    publish_package,
    render_triplet,
    require,
    rounded_box,
    sha256_file,
    truth,
    validate_blocking_checks,
    validate_source_status,
)

from matplotlib.patches import FancyArrowPatch  # noqa: E402


SCHEMA = "genetic_support_gated_workflow_v1"
STEM = "genetic_support_gated_workflow"
DEFAULT_OUTPUT_ROOT = (
    "results/figures/analysis/phase_19_genetic_support/gated_workflow"
)
OUTPUT_FILES = output_names(STEM)
PHASE18_SCHEMA = "phase18_call_key_driver_returns_v1"
TIER1_SCHEMA = "human_genetic_support_tier1_v1"
TIER2_SCHEMA = "human_genetic_support_tier2_coloc_v1"
RECOVERY_SCHEMA = "human_genetic_support_tier2_classical_coloc_recovery_v1"
ENDOPHENOTYPE_SCHEMA = "phase19_endophenotype_gwas_qtl_extension_v1"
RPS15_SCHEMA = "phase19_opc_rps15_public_recovery_v1"
FUNGEN_RELEASE = "f6f63fc319a417213cf1e86ec0eb14fcb53d2427"
PHASE18_SHA256 = "b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8"
CSF_ACCESSIONS = {
    "GCST90726396": "csf_abeta42",
    "GCST90726397": "csf_total_tau",
    "GCST90726398": "csf_ptau181",
}
RECOVERY_DATASETS = {
    "QTD000559",
    "QTD000563",
    "QTD000569",
    "QTD000573",
    "QTD000579",
    "QTD000583",
}
ROUTE_DECISION_RULE = (
    "frozen_gwas_gate_then_complete_qtl_model_then_ld_model_then_h0_h4"
)
OMITTED_SAMPLE_COUNTS = {"85934", "401577", "111326", "677663"}


@dataclass(frozen=True)
class SourcePaths:
    phase18_calls: Path
    tier1_manifest: Path
    tier1_candidates: Path
    tier1_registry: Path
    tier1_status: Path
    tier1_checks: Path
    tier2_routes: Path
    tier2_registry: Path
    tier2_status: Path
    tier2_checks: Path
    recovery_registry: Path
    recovery_decisions: Path
    recovery_status: Path
    recovery_checks: Path
    endophenotype_registry: Path
    endophenotype_decisions: Path
    endophenotype_status: Path
    endophenotype_checks: Path
    rps15_registry: Path
    rps15_status: Path
    rps15_checks: Path

    def as_list(self) -> list[Path]:
        return [Path(value) for value in vars(self).values()]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def default_sources(root: Path) -> SourcePaths:
    tier1 = root / "results/minerva_production/19_genetic_support_tier1"
    tier2 = root / "results/minerva_production/19_genetic_support_tier2_regional"
    recovery = root / "results/minerva_production/19_genetic_support_tier2_recovery"
    endophenotype = (
        root
        / "results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension"
    )
    rps15 = (
        root
        / "results/minerva_production/19_genetic_support_opc_rps15_public_recovery"
    )
    return SourcePaths(
        phase18_calls=(
            root
            / "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv"
        ),
        tier1_manifest=tier1 / "genetic_support_analysis_manifest.tsv",
        tier1_candidates=tier1 / "genetic_support_candidate_manifest.tsv",
        tier1_registry=tier1 / "genetic_support_dataset_registry.tsv",
        tier1_status=tier1 / "genetic_support_status.tsv",
        tier1_checks=tier1 / "genetic_support_checks.tsv",
        tier2_routes=tier2 / "tier2_candidate_route_manifest.tsv",
        tier2_registry=tier2 / "tier2_dataset_registry.tsv",
        tier2_status=tier2 / "tier2_status.tsv",
        tier2_checks=tier2 / "tier2_checks.tsv",
        recovery_registry=recovery / "recovery_dataset_registry.tsv",
        recovery_decisions=recovery / "recovery_route_decisions.tsv",
        recovery_status=recovery / "recovery_status.tsv",
        recovery_checks=recovery / "recovery_checks.tsv",
        endophenotype_registry=endophenotype / "endophenotype_dataset_registry.tsv",
        endophenotype_decisions=endophenotype / "endophenotype_gate_decisions.tsv",
        endophenotype_status=endophenotype / "endophenotype_status.tsv",
        endophenotype_checks=endophenotype / "endophenotype_checks.tsv",
        rps15_registry=rps15 / "opc_rps15_dataset_registry.tsv",
        rps15_status=rps15 / "opc_rps15_status.tsv",
        rps15_checks=rps15 / "opc_rps15_checks.tsv",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the frozen, gated human-genetic-support workflow."
    )
    parser.add_argument("--phase18-calls")
    parser.add_argument("--tier1-root")
    parser.add_argument("--tier2-root")
    parser.add_argument("--recovery-root")
    parser.add_argument("--endophenotype-root")
    parser.add_argument("--rps15-root")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--visual-review-status",
        choices=["pending", "complete"],
        default="pending",
    )
    return parser.parse_args()


def sources_from_args(root: Path, args: argparse.Namespace) -> SourcePaths:
    defaults = default_sources(root)
    phase18 = (
        resolve(root, args.phase18_calls)
        if args.phase18_calls
        else defaults.phase18_calls
    )
    tier1 = (
        resolve(root, args.tier1_root)
        if args.tier1_root
        else defaults.tier1_manifest.parent
    )
    tier2 = (
        resolve(root, args.tier2_root)
        if args.tier2_root
        else defaults.tier2_routes.parent
    )
    recovery = (
        resolve(root, args.recovery_root)
        if args.recovery_root
        else defaults.recovery_registry.parent
    )
    endophenotype = (
        resolve(root, args.endophenotype_root)
        if args.endophenotype_root
        else defaults.endophenotype_registry.parent
    )
    rps15 = (
        resolve(root, args.rps15_root)
        if args.rps15_root
        else defaults.rps15_registry.parent
    )
    return SourcePaths(
        phase18_calls=phase18,
        tier1_manifest=tier1 / "genetic_support_analysis_manifest.tsv",
        tier1_candidates=tier1 / "genetic_support_candidate_manifest.tsv",
        tier1_registry=tier1 / "genetic_support_dataset_registry.tsv",
        tier1_status=tier1 / "genetic_support_status.tsv",
        tier1_checks=tier1 / "genetic_support_checks.tsv",
        tier2_routes=tier2 / "tier2_candidate_route_manifest.tsv",
        tier2_registry=tier2 / "tier2_dataset_registry.tsv",
        tier2_status=tier2 / "tier2_status.tsv",
        tier2_checks=tier2 / "tier2_checks.tsv",
        recovery_registry=recovery / "recovery_dataset_registry.tsv",
        recovery_decisions=recovery / "recovery_route_decisions.tsv",
        recovery_status=recovery / "recovery_status.tsv",
        recovery_checks=recovery / "recovery_checks.tsv",
        endophenotype_registry=endophenotype / "endophenotype_dataset_registry.tsv",
        endophenotype_decisions=endophenotype / "endophenotype_gate_decisions.tsv",
        endophenotype_status=endophenotype / "endophenotype_status.tsv",
        endophenotype_checks=endophenotype / "endophenotype_checks.tsv",
        rps15_registry=rps15 / "opc_rps15_dataset_registry.tsv",
        rps15_status=rps15 / "opc_rps15_status.tsv",
        rps15_checks=rps15 / "opc_rps15_checks.tsv",
    )


def read_tsv(path: Path, *, schema: str, usecols: list[str] | None = None) -> pd.DataFrame:
    require(path.is_file(), f"Missing workflow source: {path}")
    frame = pd.read_csv(path, sep="\t", low_memory=False, usecols=usecols)
    require("schema_version" in frame.columns, f"Missing schema_version: {path}")
    observed = set(frame["schema_version"].dropna().astype(str))
    require(observed == {schema}, f"Unexpected schema {observed}: {path}")
    return frame


def validate_bundle_statuses(paths: SourcePaths) -> dict[str, str]:
    tier1 = validate_source_status(
        paths.tier1_status,
        status_column="technical_status",
        accepted={"validated_complete_tier1"},
    )
    tier2 = validate_source_status(
        paths.tier2_status,
        status_column="technical_status",
        accepted={"validated_complete_tier2"},
    )
    recovery = validate_source_status(
        paths.recovery_status,
        status_column="technical_status",
        accepted={"validated_complete_tier2_recovery"},
    )
    endophenotype = validate_source_status(
        paths.endophenotype_status,
        status_column="technical_status",
        accepted={"validated_complete"},
    )
    rps15 = validate_source_status(
        paths.rps15_status,
        status_column="validation_status",
        accepted={"validated_complete_opc_rps15_public_recovery"},
    )
    validate_blocking_checks(paths.tier1_checks)
    validate_blocking_checks(paths.tier2_checks)
    validate_blocking_checks(paths.recovery_checks)
    endophenotype_checks = pd.read_csv(paths.endophenotype_checks, sep="\t")
    require(
        "status" in endophenotype_checks.columns
        and endophenotype_checks["status"].astype(str).str.lower().eq("pass").all(),
        "An endophenotype source check failed",
    )
    validate_blocking_checks(paths.rps15_checks)
    return {
        "tier1": str(tier1.iloc[0]["technical_status"]),
        "tier2": str(tier2.iloc[0]["technical_status"]),
        "recovery": str(recovery.iloc[0]["technical_status"]),
        "endophenotype": str(endophenotype.iloc[0]["technical_status"]),
        "rps15": str(rps15.iloc[0]["validation_status"]),
    }


def validate_sources(
    paths: SourcePaths,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    statuses = validate_bundle_statuses(paths)
    phase18 = read_tsv(
        paths.phase18_calls,
        schema=PHASE18_SCHEMA,
        usecols=[
            "schema_version",
            "key_driver",
            "broad_network",
            "case_id",
            "is_mtdna_gene",
            "top5_display",
        ],
    )
    selected = phase18.loc[phase18["top5_display"].map(truth)].copy()
    key = ["key_driver", "broad_network", "case_id"]
    require(
        selected.groupby(key)["is_mtdna_gene"].nunique().max() == 1,
        "A frozen context has conflicting genome-origin labels",
    )
    selected = selected.drop_duplicates(key).rename(columns={"key_driver": "gene"})
    selected["is_mtdna_gene"] = selected["is_mtdna_gene"].map(truth)

    tier1_manifest = read_tsv(
        paths.tier1_manifest, schema=TIER1_SCHEMA
    )
    tier1_candidates = read_tsv(
        paths.tier1_candidates, schema=TIER1_SCHEMA
    )
    tier1_registry = read_tsv(paths.tier1_registry, schema=TIER1_SCHEMA)
    tier2_routes = read_tsv(paths.tier2_routes, schema=TIER2_SCHEMA)
    tier2_registry = read_tsv(paths.tier2_registry, schema=TIER2_SCHEMA)
    recovery_registry = read_tsv(paths.recovery_registry, schema=RECOVERY_SCHEMA)
    recovery_decisions = read_tsv(paths.recovery_decisions, schema=RECOVERY_SCHEMA)
    endophenotype_registry = read_tsv(
        paths.endophenotype_registry, schema=ENDOPHENOTYPE_SCHEMA
    )
    endophenotype_decisions = read_tsv(
        paths.endophenotype_decisions, schema=ENDOPHENOTYPE_SCHEMA
    )
    rps15_registry = read_tsv(paths.rps15_registry, schema=RPS15_SCHEMA)

    tier1_candidates = tier1_candidates.copy()
    tier1_candidates["is_mtdna_gene"] = tier1_candidates["is_mtdna_gene"].map(truth)
    phase18_units = set(
        selected[["gene", "broad_network", "case_id"]].itertuples(
            index=False, name=None
        )
    )
    tier1_units = set(
        tier1_candidates[["gene", "broad_network", "case_id"]].itertuples(
            index=False, name=None
        )
    )
    require(phase18_units == tier1_units, "Tier 1 candidate freeze differs from Phase 18")
    require(sha256_file(paths.phase18_calls) == PHASE18_SHA256, "Phase 18 hash changed")
    require(len(tier1_manifest) == 1, "Expected one Tier 1 analysis-manifest row")
    manifest_row = tier1_manifest.iloc[0]
    require(str(manifest_row["phase18_sha256"]) == PHASE18_SHA256, "Manifest hash mismatch")
    require(str(manifest_row["scope_rule"]) == "top5_display_TRUE_unique_key_driver_broad_network_case_id", "Unexpected freeze rule")

    nuclear = selected.loc[~selected["is_mtdna_gene"]]
    mtdna = selected.loc[selected["is_mtdna_gene"]]
    require(len(selected) == 47, "Expected 47 frozen candidate contexts")
    require(selected["gene"].nunique() == 25, "Expected 25 frozen genes")
    require(len(nuclear) == 27, "Expected 27 nuclear contexts")
    require(nuclear["gene"].nunique() == 19, "Expected 19 nuclear genes")
    require(len(mtdna) == 20, "Expected 20 mtDNA contexts")
    require(mtdna["gene"].nunique() == 6, "Expected six mtDNA genes")

    require(len(tier2_routes) == 54, "Expected 54 clinical-AD eQTL/sQTL routes")
    require(tier2_routes["route_id"].nunique() == 54, "Tier 2 route IDs are not unique")
    require(set(tier2_routes["qtl_type"]) == {"eQTL", "sQTL"}, "Unexpected Tier 2 QTL type")
    require(tier2_routes["candidate_id"].nunique() == 27, "Expected 27 nuclear route contexts")
    require(
        tier2_routes.groupby("candidate_id")["qtl_type"].nunique().eq(2).all(),
        "Each nuclear context must have one eQTL and one sQTL route",
    )
    require(len(recovery_decisions) == 54, "Expected 54 recovery decisions")
    require(
        set(recovery_decisions["decision_rule"].astype(str)) == {ROUTE_DECISION_RULE},
        "The frozen route-decision order changed",
    )

    require(len(endophenotype_decisions) == 57, "Expected 57 nuclear CSF screens")
    require(endophenotype_decisions["screen_id"].nunique() == 57, "CSF screen IDs are not unique")
    require(endophenotype_decisions["gene"].nunique() == 19, "Expected 19 CSF-screened genes")
    require(
        set(endophenotype_decisions["trait_id"].astype(str)) == set(CSF_ACCESSIONS.values()),
        "Unexpected CSF biomarker set",
    )

    required_tier1 = {"FunGen_AD_unified", "FunGen_xQTL", "FunGen_TWAS"}
    require(required_tier1 <= set(tier1_registry["dataset_id"]), "Missing FunGen registry row")
    fungen_rows = tier1_registry.loc[tier1_registry["dataset_id"].isin(required_tier1)]
    require(set(fungen_rows["version"].astype(str)) == {FUNGEN_RELEASE}, "FunGen release changed")

    bellenguez = tier2_registry.loc[tier2_registry["dataset_id"].eq("Bellenguez2022_AD_GWAS")]
    require(len(bellenguez) == 1, "Expected one Bellenguez registry row")
    require(str(bellenguez.iloc[0]["source_id"]) == "GCST90027158", "Bellenguez accession changed")
    require("NG00184.v1" in set(tier2_registry["source_id"].astype(str)), "NG00184 is unregistered")
    require("EQTL_Catalogue" in set(tier2_registry["dataset_id"].astype(str)), "eQTL Catalogue is unregistered")

    require(set(recovery_registry["dataset_id"]) == RECOVERY_DATASETS, "Recovery QTL dataset set changed")
    require(recovery_registry["selection_frozen_before_result"].map(truth).all(), "Recovery QTL selection was not frozen")

    endo_gwas = endophenotype_registry.loc[
        endophenotype_registry["source_id"].isin(CSF_ACCESSIONS)
    ]
    require(len(endo_gwas) == 3, "Expected three registered CSF GWAS")
    observed_traits = dict(zip(endo_gwas["source_id"], endo_gwas["trait_or_context"]))
    require(observed_traits == CSF_ACCESSIONS, "CSF accession/trait mapping changed")
    require(endo_gwas["selection_frozen_before_result"].map(truth).all(), "CSF GWAS selection was not frozen")
    require("NG00130.v2" in set(endophenotype_registry["source_id"]), "APOE CSF pQTL source is unregistered")
    require("NG00184.v1" in set(endophenotype_registry["source_id"]), "Endophenotype NG00184 source is unregistered")
    require("NG00184.v1" in set(rps15_registry["source_id"]), "RPS15 NG00184 audit source is unregistered")

    derived: dict[str, Any] = {
        "candidate_contexts": int(len(selected)),
        "unique_genes": int(selected["gene"].nunique()),
        "nuclear_contexts": int(len(nuclear)),
        "nuclear_genes": int(nuclear["gene"].nunique()),
        "mtdna_contexts": int(len(mtdna)),
        "mtdna_genes": int(mtdna["gene"].nunique()),
        "ad_routes": int(len(tier2_routes)),
        "csf_screens": int(len(endophenotype_decisions)),
        "source_statuses": statuses,
        "candidate_manifest_parity": phase18_units == tier1_units,
        "phase18_hash": sha256_file(paths.phase18_calls),
        "fungen_release": FUNGEN_RELEASE,
    }
    frames = {
        "selected": selected,
        "tier1_manifest": tier1_manifest,
        "tier1_candidates": tier1_candidates,
        "tier1_registry": tier1_registry,
        "tier2_routes": tier2_routes,
        "tier2_registry": tier2_registry,
        "recovery_registry": recovery_registry,
        "recovery_decisions": recovery_decisions,
        "endophenotype_registry": endophenotype_registry,
        "endophenotype_decisions": endophenotype_decisions,
        "rps15_registry": rps15_registry,
    }
    return frames, derived


def derive_plot_data(derived: dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "record_id": "freeze",
            "record_type": "scope",
            "lane": "shared",
            "display_order": 1,
            "title": "Starting gene list\n(chosen in advance)",
            "subtitle": "47 gene–network pairs\n25 unique genes",
            "detail": "Top network genes retained\nfor genetic follow-up",
            "source_note": "call_key_driver_returns.tsv",
            "style_key": "freeze_navy",
            "x": 0.025,
            "y": 0.410,
            "width": 0.165,
            "height": 0.350,
        },
        {
            "record_id": "tier1_lane",
            "record_type": "lane_heading",
            "lane": "direct_summary",
            "display_order": 1,
            "title": "LANE A  ·  LOOK UP RESULTS IN PUBLIC DATA",
            "subtitle": "All 47 gene–network pairs",
            "detail": "NA",
            "source_note": "genetic_support_dataset_registry.tsv",
            "style_key": "lane_blue",
            "x": 0.220,
            "y": 0.925,
            "width": 0.760,
            "height": 0.040,
        },
        {
            "record_id": "tier1_screen",
            "record_type": "analysis_step",
            "lane": "direct_summary",
            "display_order": 2,
            "title": "Search public FunGen results",
            "subtitle": "Likely AD variants  ·  effects on gene activity or splicing",
            "detail": "Pre-computed results from a fixed public data snapshot",
            "source_note": "FunGen_AD_unified / FunGen_xQTL / FunGen_TWAS",
            "style_key": "direct_blue",
            "x": 0.220,
            "y": 0.730,
            "width": 0.340,
            "height": 0.170,
        },
        {
            "record_id": "tier1_grade",
            "record_type": "analysis_step",
            "lane": "direct_summary",
            "display_order": 3,
            "title": "Public-data matches highlighted three genes",
            "subtitle": "APOE  ·  COX7C  ·  SELENOW",
            "detail": "Four gene–network pairs  ·  original source grades retained",
            "source_note": "Tier 1 evidence matrix",
            "style_key": "direct_output",
            "x": 0.610,
            "y": 0.730,
            "width": 0.370,
            "height": 0.170,
        },
        {
            "record_id": "nuclear_lane",
            "record_type": "lane_heading",
            "lane": "nuclear_gated",
            "display_order": 1,
            "title": "LANE B  ·  TEST WHETHER AD AND GENE ACTIVITY SHARE A DNA SIGNAL",
            "subtitle": "27 gene–network pairs  ·  19 non-mitochondrial genes",
            "detail": "NA",
            "source_note": "tier2_candidate_route_manifest.tsv",
            "style_key": "lane_navy",
            "x": 0.220,
            "y": 0.650,
            "width": 0.760,
            "height": 0.040,
        },
        {
            "record_id": "regional_gate",
            "record_type": "gate",
            "lane": "nuclear_gated",
            "display_order": 2,
            "title": "1  AD-linked DNA region",
            "subtitle": "Bellenguez AD  ·  GCST90027158",
            "detail": "Spinal-fluid biomarkers (CSF):\nGCST90726396  ·  GCST90726397\nGCST90726398",
            "source_note": "54 AD gene tests  ·  57 CSF screens",
            "style_key": "gate_white",
            "x": 0.220,
            "y": 0.315,
            "width": 0.185,
            "height": 0.300,
        },
        {
            "record_id": "qtl_gate",
            "record_type": "gate",
            "lane": "nuclear_gated",
            "display_order": 3,
            "title": "2  Variant affects the gene",
            "subtitle": "DNA-to-gene link (QTL)",
            "detail": "Activity (eQTL)  ·  splicing (sQTL)\nAPOE protein (pQTL; NG00130.v2)\nRPS15 check (NG00184.v1)",
            "source_note": "eQTL Catalogue r7",
            "style_key": "gate_white",
            "x": 0.425,
            "y": 0.315,
            "width": 0.195,
            "height": 0.300,
        },
        {
            "record_id": "compatibility_gate",
            "record_type": "gate",
            "lane": "nuclear_gated",
            "display_order": 4,
            "title": "3  Prepare matching data",
            "subtitle": "Matching variants + genome",
            "detail": "Complete statistical model\nMatched ancestry and\nvariant correlation (LD)",
            "source_note": "Every item is required",
            "style_key": "gate_white",
            "x": 0.640,
            "y": 0.315,
            "width": 0.175,
            "height": 0.300,
        },
        {
            "record_id": "primary_test",
            "record_type": "gate",
            "lane": "nuclear_gated",
            "display_order": 5,
            "title": "4  Shared DNA signal",
            "subtitle": "Probability both match",
            "detail": "(PP.H4)\nAfter steps 1–3",
            "source_note": "With compatible inputs",
            "style_key": "primary_blue",
            "x": 0.835,
            "y": 0.315,
            "width": 0.145,
            "height": 0.300,
        },
        {
            "record_id": "mtdna_scope",
            "record_type": "separate_scope",
            "lane": "mtdna",
            "display_order": 1,
            "title": "Mitochondrial genes",
            "subtitle": "20 pairs  ·  6 genes",
            "detail": "Dedicated mitochondrial data\ncan add validation",
            "source_note": "Future validation route",
            "style_key": "mtdna_outline",
            "x": 0.025,
            "y": 0.045,
            "width": 0.165,
            "height": 0.225,
        },
        {
            "record_id": "boundary",
            "record_type": "boundary",
            "lane": "shared",
            "display_order": 99,
            "title": "Each completed step adds one layer of evidence.",
            "subtitle": "Arrows show test order; remaining steps guide future validation.",
            "detail": "NA",
            "source_note": "recovery_route_decisions.tsv",
            "style_key": "boundary",
            "x": 0.220,
            "y": 0.045,
            "width": 0.760,
            "height": 0.180,
        },
    ]
    plot_data = pd.DataFrame(rows)
    plot_data.insert(0, "schema_version", SCHEMA)
    visible = "\n".join(
        plot_data[["title", "subtitle", "detail"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
    )
    require("GCST90027158" in visible, "Bellenguez accession is not visible")
    for accession in CSF_ACCESSIONS:
        require(accession in visible, f"CSF accession is not visible: {accession}")
    require(
        "each completed step adds one layer of evidence" in visible.lower(),
        "Evidence-layer message missing",
    )
    require(
        "remaining steps guide future validation" in visible.lower(),
        "Future-validation message missing",
    )
    require(not any(value in visible for value in OMITTED_SAMPLE_COUNTS), "Conflicting Bellenguez sample counts leaked into figure")
    require(int(derived["candidate_contexts"]) == 47, "Derived scope changed before plotting")
    return plot_data


def build_science_checks(
    frames: dict[str, pd.DataFrame],
    derived: dict[str, Any],
    plot_data: pd.DataFrame,
) -> pd.DataFrame:
    visible = "\n".join(
        plot_data[["title", "subtitle", "detail"]]
        .fillna("")
        .astype(str)
        .to_numpy()
        .ravel()
    )
    statuses = derived["source_statuses"]
    values = [
        ("candidate_contexts", 47, derived["candidate_contexts"], "Frozen gene × network contexts."),
        ("unique_genes", 25, derived["unique_genes"], "Frozen unique genes."),
        ("nuclear_contexts", 27, derived["nuclear_contexts"], "Contexts entering the nuclear path."),
        ("nuclear_genes", 19, derived["nuclear_genes"], "Genes entering the nuclear path."),
        ("mtdna_contexts", 20, derived["mtdna_contexts"], "Contexts requiring a separate mtDNA design."),
        ("mtdna_genes", 6, derived["mtdna_genes"], "Unique mtDNA genes."),
        ("phase18_sha256", PHASE18_SHA256, derived["phase18_hash"], "Frozen upstream identity."),
        ("candidate_manifest_parity", True, derived["candidate_manifest_parity"], "Phase 18 and Tier 1 scopes match."),
        ("clinical_ad_routes", 54, derived["ad_routes"], "Nuclear candidate-context × eQTL/sQTL routes."),
        ("recovery_decisions", 54, len(frames["recovery_decisions"]), "Every AD route has a frozen decision row."),
        ("csf_gene_trait_screens", 57, derived["csf_screens"], "Nineteen nuclear genes × three CSF traits."),
        ("tier1_status", "validated_complete_tier1", statuses["tier1"], "Tier 1 bundle status."),
        ("tier2_status", "validated_complete_tier2", statuses["tier2"], "Tier 2 regional bundle status."),
        ("recovery_status", "validated_complete_tier2_recovery", statuses["recovery"], "Recovery bundle status."),
        ("endophenotype_status", "validated_complete", statuses["endophenotype"], "Endophenotype bundle status."),
        ("rps15_status", "validated_complete_opc_rps15_public_recovery", statuses["rps15"], "RPS15 audit bundle status."),
        ("fungen_release", FUNGEN_RELEASE, derived["fungen_release"], "Pinned Tier 1 public release."),
        ("recovery_qtl_datasets", 6, frames["recovery_registry"]["dataset_id"].nunique(), "Frozen eQTL Catalogue recovery datasets."),
        ("bellenguez_accession_visible", True, "GCST90027158" in visible, "Clinical-AD dataset label."),
        ("all_csf_accessions_visible", True, all(value in visible for value in CSF_ACCESSIONS), "All three CSF GWAS labels."),
        ("bellenguez_sample_counts_omitted", True, not any(value in visible for value in OMITTED_SAMPLE_COUNTS), "Conflicting sample counts are intentionally omitted."),
        ("parallel_lanes", 2, plot_data.loc[plot_data["record_type"].eq("lane_heading"), "lane"].nunique(), "Direct-summary and nuclear gated paths."),
        (
            "evidence_layer_message_visible",
            True,
            "each completed step adds one layer of evidence" in visible.lower(),
            "The workflow emphasizes evidence accumulated at each completed step.",
        ),
        (
            "future_validation_message_visible",
            True,
            "remaining steps guide future validation" in visible.lower(),
            "The workflow presents incomplete steps as a future-validation map.",
        ),
    ]
    return make_checks(SCHEMA, values)


def arrow(axis: Any, start: tuple[float, float], end: tuple[float, float], *, color: str = NAVY, width: float = 1.35) -> None:
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=axis.transAxes,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=width,
            color=color,
            shrinkA=0,
            shrinkB=0,
            connectionstyle="arc3,rad=0",
            zorder=3,
        )
    )


def render_node(axis: Any, row: pd.Series) -> None:
    style = str(row["style_key"])
    face, edge, linewidth, hatch = WHITE, LIGHT, 1.1, None
    if style == "freeze_navy":
        face, edge, linewidth = NAVY, NAVY, 1.3
    elif style == "direct_blue":
        face, edge, linewidth = PALE_BLUE, BLUE, 1.3
    elif style == "direct_output":
        face, edge, linewidth = WHITE, BLUE, 1.3
    elif style == "primary_blue":
        face, edge, linewidth = PALE_BLUE, BLUE, 1.4
    elif style == "mtdna_outline":
        face, edge, linewidth = WHITE, CHARCOAL, 1.2
    elif style == "boundary":
        face, edge, linewidth = PALE_GRAY, GRAY, 0.9
    rounded_box(
        axis,
        float(row["x"]),
        float(row["y"]),
        float(row["width"]),
        float(row["height"]),
        face=face,
        edge=edge,
        linewidth=linewidth,
        radius=0.010,
        hatch=hatch,
        zorder=1,
    )
    x = float(row["x"])
    y = float(row["y"])
    width = float(row["width"])
    height = float(row["height"])
    if style == "freeze_navy":
        add_text(axis, x + 0.014, y + height - 0.038, str(row["title"]), size=10.0, color=WHITE, weight="bold", va="top", linespacing=1.0)
        add_text(axis, x + width / 2, y + 0.180, str(row["subtitle"]), size=12.0, color=WHITE, weight="bold", ha="center", linespacing=1.02)
        add_text(axis, x + width / 2, y + 0.096, str(row["detail"]), size=9.0, color=WHITE, ha="center", linespacing=1.05)
        add_text(axis, x + width / 2, y + 0.030, "List fixed in advance", size=9.0, color=LIGHT, ha="center")
        return
    if style == "boundary":
        add_text(axis, x + 0.018, y + 0.112, str(row["title"]), size=10.2, color=NAVY, weight="bold")
        add_text(axis, x + 0.018, y + 0.054, str(row["subtitle"]), size=9.0, color=DARK)
        return
    if style in {"direct_blue", "direct_output"}:
        add_text(axis, x + 0.013, y + height - 0.035, str(row["title"]), size=10.2, color=NAVY, weight="bold", va="top")
        add_text(axis, x + 0.013, y + height - 0.090, str(row["subtitle"]), size=9.0, color=DARK, va="top")
        add_text(axis, x + 0.013, y + 0.020, str(row["detail"]), size=9.0, color=MID, va="bottom")
        return
    if style == "mtdna_outline":
        add_text(axis, x + 0.013, y + height - 0.036, str(row["title"]), size=10.0, color=NAVY, weight="bold", va="top")
        add_text(axis, x + 0.013, y + 0.116, str(row["subtitle"]), size=9.2, color=DARK)
        add_text(axis, x + 0.013, y + 0.026, str(row["detail"]), size=9.0, color=MID, va="bottom", linespacing=1.08)
        return
    title_size = 10.0 if width >= 0.175 else 9.0
    add_text(axis, x + 0.011, y + height - 0.040, str(row["title"]), size=title_size, color=NAVY, weight="bold", va="top")
    add_text(axis, x + 0.011, y + height - 0.102, str(row["subtitle"]), size=9.0, color=DARK, va="top")
    detail_size = 9.0
    add_text(axis, x + 0.011, y + height - 0.145, str(row["detail"]), size=detail_size, color=MID, va="top", linespacing=1.12)
    add_text(axis, x + 0.011, y + 0.025, str(row["source_note"]), size=9.0, color=MID, va="bottom")


def render_figure(plot_data: pd.DataFrame, staging: Path) -> None:
    figure, axis = new_canvas()
    rows = plot_data.set_index("record_id")
    for record_id in ["tier1_lane", "nuclear_lane"]:
        row = rows.loc[record_id]
        add_text(axis, float(row["x"]), float(row["y"]) + 0.020, str(row["title"]), size=9.5, color=BLUE if record_id == "tier1_lane" else NAVY, weight="bold")
        add_text(axis, float(row["x"] + row["width"]), float(row["y"]) + 0.020, str(row["subtitle"]), size=9.0, color=MID, ha="right")

    for record_id in [
        "freeze",
        "tier1_screen",
        "tier1_grade",
        "regional_gate",
        "qtl_gate",
        "compatibility_gate",
        "primary_test",
        "mtdna_scope",
        "boundary",
    ]:
        render_node(axis, rows.loc[record_id])

    arrow(axis, (0.190, 0.650), (0.220, 0.815), color=BLUE)
    arrow(axis, (0.560, 0.815), (0.610, 0.815), color=BLUE)
    arrow(axis, (0.190, 0.525), (0.220, 0.465), color=NAVY)
    arrow(axis, (0.405, 0.465), (0.425, 0.465), color=NAVY)
    arrow(axis, (0.620, 0.465), (0.640, 0.465), color=NAVY)
    arrow(axis, (0.815, 0.465), (0.835, 0.465), color=NAVY)
    arrow(axis, (0.1075, 0.410), (0.1075, 0.270), color=CHARCOAL)

    add_text(axis, 0.202, 0.720, "A", size=9.0, color=BLUE, weight="bold", ha="center")
    add_text(axis, 0.202, 0.493, "B", size=9.0, color=NAVY, weight="bold", ha="center")
    add_text(axis, 0.1075, 0.330, "mtDNA", size=9.0, color=CHARCOAL, weight="bold", ha="center")
    render_triplet(figure, staging, STEM)


def caption_text() -> str:
    return """# Two-path workflow for human-genetic support

The frozen Phase 18 set contains 47 gene-by-network contexts representing 25
unique genes. It enters two parallel evidence paths. The direct-summary path
screens the public FunGen-xQTL release for precomputed AD fine-mapping, xQTL,
and TWAS evidence. The nuclear path evaluates regional clinical-AD or CSF
biomarker signals, candidate molecular-QTL signals, and allele/build/model/LD
compatibility before any primary multi-signal H0-H4 analysis. Nineteen nuclear
genes across 27 contexts generate 54 clinical-AD eQTL/sQTL routes and 57 CSF
gene-by-trait screens. Six mtDNA genes across 20 contexts have a dedicated
mitochondrial validation route. Each completed step contributes a layer of
evidence, while remaining inputs define clear future-validation work. Arrows
show analysis flow and do not imply a causal mechanism.
"""


def methods_text(paths: SourcePaths) -> str:
    return f"""# Figure methods

The candidate scope was reconstructed from `call_key_driver_returns.tsv` by
filtering `top5_display = TRUE` and deduplicating
`key_driver + broad_network + case_id`. Its SHA-256 was verified as
`{PHASE18_SHA256}` and its 47 contexts were required to match the Tier 1
candidate manifest exactly. Counts were validated as 25 unique genes, 27
nuclear contexts/19 genes, and 20 mtDNA contexts/6 genes.

The clinical-AD route count came from `tier2_candidate_route_manifest.tsv`
(27 nuclear candidate contexts multiplied by eQTL and sQTL routes). The 57 CSF
screens came from `endophenotype_gate_decisions.tsv` (19 nuclear genes by three
traits). Dataset names and accessions were read from the Tier 1, Tier 2,
recovery, endophenotype, and RPS15 dataset registries. The pinned FunGen release
was `{FUNGEN_RELEASE}`; the displayed GWAS accessions are `GCST90027158`,
`GCST90726396`, `GCST90726397`, and `GCST90726398`. The Bellenguez case/control
counts were intentionally not displayed because published bundle metadata are
inconsistent across two source tables.

All five result-bundle statuses and their blocking validation checks were
required to pass before rendering. The recovery decision rule was required to
be `{ROUTE_DECISION_RULE}`. This is a workflow schematic rather than an
attrition or causal diagram, so it contains no effect-size scale, uncertainty
interval, or significance encoding. Source root: `{paths.phase18_calls.parents[2]}`.
"""


def publish(
    paths: SourcePaths,
    output_root: Path,
    *,
    force: bool,
    visual_review_status: str,
) -> None:
    frames, derived = validate_sources(paths)
    plot_data = derive_plot_data(derived)
    science_checks = build_science_checks(frames, derived, plot_data)
    helper = SCRIPT_DIR / "phase19_slide_figure_common.py"
    scientific_sources = paths.as_list()
    publish_package(
        schema=SCHEMA,
        stem=STEM,
        output_root=output_root,
        source_paths=scientific_sources + [helper],
        renderer_path=Path(__file__).resolve(),
        plot_data=plot_data,
        science_checks=science_checks,
        caption=caption_text(),
        methods=methods_text(paths),
        render=lambda staging: render_figure(plot_data, staging),
        status_fields={
            "scientific_status": "descriptive_frozen_gated_workflow",
            "candidate_contexts": derived["candidate_contexts"],
            "unique_genes": derived["unique_genes"],
            "nuclear_contexts": derived["nuclear_contexts"],
            "nuclear_genes": derived["nuclear_genes"],
            "mtdna_contexts": derived["mtdna_contexts"],
            "mtdna_genes": derived["mtdna_genes"],
            "clinical_ad_routes": derived["ad_routes"],
            "csf_gene_trait_screens": derived["csf_screens"],
            "parallel_evidence_lanes": 2,
            "route_stop_rule_visible": True,
            "arrows_are_analysis_flow_not_causal": True,
            "bellenguez_sample_counts_visible": False,
            "scientific_source_files": len(scientific_sources),
        },
        force=force,
        visual_review_status=visual_review_status,
    )


def main() -> None:
    args = parse_args()
    root = repository_root()
    paths = sources_from_args(root, args)
    output_root = resolve(root, args.output_root)
    publish(
        paths,
        output_root,
        force=args.force,
        visual_review_status=args.visual_review_status,
    )


if __name__ == "__main__":
    main()
