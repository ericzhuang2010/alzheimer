#!/usr/bin/env python3
"""Deterministic evidence integration for the OPC RPS15 public-data audit."""

from __future__ import annotations

from typing import Any


POSITIVE_TERMINALS = {"resolved_public_colocalization"}
SIGNAL_TERMINALS = {"model_or_ld_incompatible", "oversized_public_archive_only"}
NULL_TERMINALS = {"no_regional_qtl_signal"}
UNRESOLVED_TERMINALS = {"measurement_unresolved", "not_assessable_local_resource_gate"}


def as_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def as_float(value: Any) -> float | None:
    try:
        result = float(str(value))
    except (TypeError, ValueError):
        return None
    return result if result == result else None


def summarize_candidate(
    candidate_id: str,
    context: str,
    routes: list[dict[str, Any]],
) -> dict[str, str]:
    eligible = [row for row in routes if str(row.get("eligible", "")).upper() == "TRUE"]
    exact_or_lineage = [
        row for row in eligible
        if row.get("context_match") in {"exact_opc", "oligodendroglial_lineage", "exact_inhibitory", "neuronal_lineage"}
    ]
    resolved = [row for row in eligible if row.get("route_terminal_status") in POSITIVE_TERMINALS]
    signal_limited = [row for row in eligible if row.get("route_terminal_status") in SIGNAL_TERMINALS]
    null_routes = [row for row in eligible if row.get("route_terminal_status") in NULL_TERMINALS]
    unresolved = [row for row in eligible if row.get("route_terminal_status") in UNRESOLVED_TERMINALS]
    exact_signal = [row for row in exact_or_lineage if as_int(row.get("source_significant_rows")) > 0]

    if resolved:
        max_h4 = max((as_float(row.get("pp_h4")) or 0.0) for row in resolved)
        gene_grade = "strong" if max_h4 >= 0.80 else "moderate"
        gene_state = "new_RPS15_gene_support_with_context_or_overlap_limitation"
        validated = "TRUE"
    elif signal_limited:
        max_h4 = None
        gene_grade = "weak"
        gene_state = "suggestive_public_support_only"
        validated = "FALSE"
    elif null_routes and not unresolved:
        max_h4 = None
        gene_grade = "none"
        gene_state = "assessable_no_RPS15_QTL_signal"
        validated = "FALSE"
    else:
        max_h4 = None
        gene_grade = "not_assessable"
        gene_state = "public_measurement_unresolved"
        validated = "FALSE"

    if resolved and any(row in exact_or_lineage for row in resolved):
        context_grade = gene_grade
        context_validated = "TRUE"
    elif exact_signal:
        context_grade = "weak"
        context_validated = "FALSE"
    else:
        context_grade = "not_validated"
        context_validated = "FALSE"

    cohorts = sorted({
        str(row.get("cohort", ""))
        for row in eligible
        if as_int(row.get("target_rows")) > 0 and row.get("cohort")
    })
    signals = sorted({
        str(row.get("route_id", ""))
        for row in eligible
        if as_int(row.get("source_significant_rows")) > 0
    })
    reasons = sorted({
        str(row.get("reason", ""))
        for row in eligible
        if row.get("reason")
    })

    return {
        "candidate_id": candidate_id,
        "gene": "RPS15",
        "context": context,
        "eligible_routes": str(len(eligible)),
        "measured_routes": str(sum(as_int(row.get("target_rows")) > 0 for row in eligible)),
        "signal_positive_routes": str(sum(as_int(row.get("source_significant_rows")) > 0 for row in eligible)),
        "resolved_colocalization_routes": str(len(resolved)),
        "gene_evidence_grade": gene_grade,
        "gene_outcome": gene_state,
        "gene_validated": validated,
        "context_evidence_grade": context_grade,
        "context_validated": context_validated,
        "maximum_pp_h4": "NA" if max_h4 is None else f"{max_h4:.12g}",
        "observed_cohorts": ";".join(cohorts) or "none",
        "signal_route_ids": ";".join(signals) or "none",
        "independence_state": "source_specific_overlap_audit_required",
        "reason": ";".join(reasons) or "no_eligible_route_result",
    }
