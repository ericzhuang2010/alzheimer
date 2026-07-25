#!/usr/bin/env python3
"""Build an exploratory, pre-network mitochondrial regulator shortlist.

This analysis intentionally separates two questions:

1. Which mitochondrial genes carry the strongest AD/sex/APOE signal?
2. Which of those genes are plausible upstream control points rather than
   structural pathway readouts?

The output is a transparent nomination score, not a causal key-driver result.
Bayesian/coexpression network enrichment is still required before calling any
candidate a key driver.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator


COMPARISONS = (
    "female_vs_male_all_apoe",
    "e2_vs_e33_all_sexes",
    "e4_vs_e33_all_sexes",
    "female_vs_male_e2",
    "female_vs_male_e33",
    "female_vs_male_e4",
)

COMPARISON_FAMILY = {
    "female_vs_male_all_apoe": "sex_global",
    "e2_vs_e33_all_sexes": "apoe_contrast",
    "e4_vs_e33_all_sexes": "apoe_contrast",
    "female_vs_male_e2": "sex_within_apoe",
    "female_vs_male_e33": "sex_within_apoe",
    "female_vs_male_e4": "sex_within_apoe",
}

CONTROL_PROGRAM_PATTERNS = {
    "genome_expression": (
        "mtdna maintenance",
        "mtdna replication",
        "mtdna nucleoid",
        "mtdna repair",
        "mtdna modifications",
        "mtdna stability and decay",
        "mtrna metabolism",
        "transcription",
        "mtrna granules",
        "polycistronic mtrna processing",
        "mt-trna modifications",
        "mt-rrna modifications",
        "mt-mrna modifications",
        "mtrna stability and decay",
        "mitochondrial ribosome assembly",
        "translation factors",
    ),
    "proteostasis_import": (
        "protein import, sorting and homeostasis",
        "protein import and sorting",
        "protein homeostasis",
        "proteases",
        "chaperones",
        "preprotein cleavage",
        "tim22 carrier pathway",
        "tim23 presequence pathway",
        "import motor",
        "mia40",
        "tom",
        "sam",
        "oxa",
    ),
    "oxphos_assembly": (
        "oxphos assembly factors",
        "ci assembly factors",
        "cii assembly factors",
        "ciii assembly factors",
        "civ assembly factors",
        "cv assembly factors",
        "respirasome assembly",
    ),
    "dynamics_surveillance": (
        "fusion",
        "fission",
        "organelle contact sites",
        "intramitochondrial membrane interactions",
        "trafficking",
        "mitophagy",
        "autophagy",
        "micos complex",
    ),
}

SECONDARY_PROGRAM_PATTERNS = {
    "signaling_transport": (
        "signaling",
        "calcium homeostasis",
        "calcium cycle",
        "mitochondrial permeability transition pore",
        "immune response",
        "camp-pka signaling",
    ),
    "redox_stress": (
        "detoxification",
        "ros and glutathione metabolism",
        "iron homeostasis",
        "selenoproteins",
    ),
    "dynamics_effector": (
        "mitochondrial dynamics and surveillance",
        "apoptosis",
        "cristae formation",
    ),
}

CONTROL_NAME_HINTS = (
    "assembly factor",
    "chaperone",
    "elongation factor",
    "fission",
    "fusion",
    "initiation factor",
    "inhibitor",
    "inhibitory factor",
    "peptidase",
    "protease",
    "quality control",
    "regulator",
    "transcription factor",
    "translation factor",
    "translocase",
)

CONTROL_GENE_OVERRIDES = {"ATP5IF1"}

SCORE_SCHEMES = {
    "balanced": {
        "disease_signal": 0.35,
        "differential_context": 0.35,
        "pathway_support": 0.20,
        "data_quality": 0.10,
    },
    "deg_heavy": {
        "disease_signal": 0.55,
        "differential_context": 0.25,
        "pathway_support": 0.10,
        "data_quality": 0.10,
    },
    "context_heavy": {
        "disease_signal": 0.25,
        "differential_context": 0.50,
        "pathway_support": 0.15,
        "data_quality": 0.10,
    },
}


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(
        description="Prioritize mitochondrial regulator candidates before network KDA."
    )
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Defaults to "
            "<root>/docs/analysis/mt_pathway."
        ),
    )
    parser.add_argument("--shortlist-size", type=int, default=15)
    return parser.parse_args()


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="")
    return path.open("r", newline="")


def read_tsv(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "t", "yes"}


def as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def safe_log10_p(value: float | None) -> float:
    if value is None:
        return 0.0
    return -math.log10(max(value, 1e-300))


def first_nonempty(current: str, value: str) -> str:
    if current and current != "NA":
        return current
    return "" if value == "NA" else value


def mean_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.mean(values) if values else 0.0


def median_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.median(values) if values else 0.0


def percentile_map(values: dict[str, float]) -> dict[str, float]:
    """Return tie-aware empirical percentiles where larger values are better."""
    if not values:
        return {}
    grouped: dict[float, list[str]] = defaultdict(list)
    for key, value in values.items():
        grouped[value].append(key)
    ordered = sorted(grouped)
    n = len(values)
    out: dict[str, float] = {}
    position = 1
    for value in ordered:
        keys = grouped[value]
        end = position + len(keys) - 1
        midrank = (position + end) / 2
        percentile = 1.0 if n == 1 else (midrank - 1) / (n - 1)
        for key in keys:
            out[key] = percentile
        position = end + 1
    return out


def rank_map(values: dict[str, float]) -> dict[str, int]:
    ordered = sorted(values, key=lambda key: (-values[key], key))
    return {key: index for index, key in enumerate(ordered, start=1)}


def format_number(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return "NA"
        return f"{value:.6g}"
    if value is None:
        return "NA"
    return value


def write_tsv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: format_number(row.get(column)) for column in columns})


def collect_pathways(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    pathways: dict[str, set[str]] = defaultdict(set)
    hierarchies: dict[str, set[str]] = defaultdict(set)
    for row in read_tsv(path):
        genes = [gene.strip() for gene in row["genes"].split(",") if gene.strip()]
        for gene in genes:
            pathways[gene].add(row["pathway"])
            hierarchies[gene].add(row["hierarchy"])
    return pathways, hierarchies


def classify_role(
    gene: str,
    hgnc_name: str,
    genome_origin: str,
    pathways: set[str],
    hierarchies: set[str],
) -> tuple[str, list[str], list[str], bool]:
    searchable = {value.lower() for value in pathways | hierarchies}
    control_programs = []
    for program, patterns in CONTROL_PROGRAM_PATTERNS.items():
        if any(
            item == pattern or item.endswith(f" > {pattern}")
            for item in searchable
            for pattern in patterns
        ):
            control_programs.append(program)
    secondary_programs = []
    for program, patterns in SECONDARY_PROGRAM_PATTERNS.items():
        if any(
            item == pattern or item.endswith(f" > {pattern}")
            for item in searchable
            for pattern in patterns
        ):
            secondary_programs.append(program)

    name_lower = hgnc_name.lower()
    name_control_hint = any(pattern in name_lower for pattern in CONTROL_NAME_HINTS)
    structural_oxphos = any(
        item == "oxphos subunits" or item.endswith(" > oxphos subunits")
        for item in searchable
    )
    if genome_origin.lower() == "mtdna" or gene.startswith("MT-"):
        role = "mtDNA_structural_marker"
    elif gene in CONTROL_GENE_OVERRIDES or control_programs:
        role = "regulatory_control"
    elif structural_oxphos:
        role = "structural_oxphos"
    elif "redox_stress" in secondary_programs:
        role = "stress_defense"
    elif secondary_programs:
        role = "signaling_or_dynamics_effector"
    elif name_control_hint:
        role = "control_annotation_only"
    else:
        role = "metabolic_or_other"
    return (
        role,
        sorted(control_programs),
        sorted(secondary_programs),
        name_control_hint,
    )


def empty_gene_stats() -> dict[str, Any]:
    return {
        "hgnc_id": "",
        "hgnc_name": "",
        "ensembl_id_stable": "",
        "mito_tier": "",
        "genome_origin": "",
        "sub_mito_localization": "",
        "assay_eligible_context_ids": set(),
        "all_contexts_by_id": {},
        "deg_contexts_by_id": {},
        "assay_eligible_contexts": 0,
        "modeled_contexts": 0,
        "deg_contexts": 0,
        "deg_up_contexts": 0,
        "deg_down_contexts": 0,
        "deg_cell_types": set(),
        "deg_lineages": set(),
        "deg_strata": set(),
        "abs_effects": [],
        "min_deg_fdr": 1.0,
        "all_contexts": [],
        "contexts": [],
    }


def collect_deg_stats(path: Path) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(empty_gene_stats)
    for row in read_tsv(path):
        gene = row["symbol_hgnc_current"] or row["feature_id_original"]
        if not gene or gene == "NA":
            continue
        current = stats[gene]
        for field in (
            "hgnc_id",
            "hgnc_name",
            "ensembl_id_stable",
            "mito_tier",
            "genome_origin",
            "sub_mito_localization",
        ):
            current[field] = first_nonempty(current[field], row[field])
        context_id = row["contrast_id"]
        if as_bool(row["test_eligible"]):
            current["assay_eligible_context_ids"].add(context_id)
        log_fc = as_float(row["logFC"])
        fdr = as_float(row["fdr_bh_within_contrast"])
        is_deg = as_bool(row["paper_deg"])
        context = {
            "gene": gene,
            "contrast_id": context_id,
            "rds_id": row["rds_id"],
            "cell_type": row["cell_type_high_resolution"],
            "sex": row["sex"],
            "apoe_group": row["apoe_group"],
            "yu_stratum": row["yu_stratum"],
            "logFC": log_fc,
            "fdr": fdr,
            "paper_deg": is_deg,
            "cells_ad": row["cells_ad"],
            "cells_nci": row["cells_nci"],
            "donors_ad": row["donors_ad"],
            "donors_nci": row["donors_nci"],
        }
        if as_bool(row["phase08_row_present"]) and log_fc is not None:
            existing = current["all_contexts_by_id"].get(context_id)
            if existing is None or (
                is_deg,
                safe_log10_p(fdr),
                abs(log_fc),
            ) > (
                existing["paper_deg"],
                safe_log10_p(existing["fdr"]),
                abs(existing["logFC"] or 0.0),
            ):
                current["all_contexts_by_id"][context_id] = context
        if not is_deg:
            continue
        existing = current["deg_contexts_by_id"].get(context_id)
        if existing is None or (
            safe_log10_p(fdr),
            abs(log_fc or 0.0),
        ) > (
            safe_log10_p(existing["fdr"]),
            abs(existing["logFC"] or 0.0),
        ):
            current["deg_contexts_by_id"][context_id] = context

    for current in stats.values():
        all_contexts = list(current.pop("all_contexts_by_id").values())
        contexts = list(current.pop("deg_contexts_by_id").values())
        effects = [
            context["logFC"]
            for context in contexts
            if context["logFC"] is not None
        ]
        fdr_values = [
            context["fdr"]
            for context in contexts
            if context["fdr"] is not None
        ]
        current["assay_eligible_contexts"] = len(
            current.pop("assay_eligible_context_ids")
        )
        current["modeled_contexts"] = len(all_contexts)
        current["deg_contexts"] = len(contexts)
        current["deg_up_contexts"] = sum(effect > 0 for effect in effects)
        current["deg_down_contexts"] = sum(effect < 0 for effect in effects)
        current["deg_cell_types"] = {
            context["cell_type"] for context in contexts
        }
        current["deg_lineages"] = {context["rds_id"] for context in contexts}
        current["deg_strata"] = {context["yu_stratum"] for context in contexts}
        current["abs_effects"] = [abs(effect) for effect in effects]
        current["min_deg_fdr"] = min(fdr_values, default=1.0)
        current["all_contexts"] = all_contexts
        current["contexts"] = contexts
    return stats


def collect_similarity(
    results_path: Path, rank_path: Path
) -> tuple[
    set[str],
    dict[str, dict[str, dict[str, float]]],
    dict[str, dict[str, int]],
    dict[str, set[str]],
]:
    core_genes: set[str] = set()
    similarity: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for row in read_tsv(results_path):
        if not as_bool(row["in_core_mito"]):
            continue
        gene = row["symbol_hgnc_current"] or row["similarity_feature_id"]
        comparison = row["comparison_id"]
        core_genes.add(gene)
        similarity[gene][comparison] = {
            "score": as_float(row["similarity_score"]) or 0.0,
            "coverage": as_float(row["coverage_fraction"]) or 0.0,
            "fdr": as_float(row["directional_fdr_bh_core_mito"]) or 1.0,
            "eligible": 1.0 if as_bool(row["ranking_eligible"]) else 0.0,
        }

    low_tail_ranks: dict[str, dict[str, int]] = defaultdict(dict)
    panel_tail_comparisons: dict[str, set[str]] = defaultdict(set)
    for row in read_tsv(rank_path):
        if row["analysis_universe"] != "core_mito" or row["tail"] != "low_score":
            continue
        gene = row["symbol_hgnc_current"] or row["similarity_feature_id"]
        comparison = row["comparison_id"]
        requested_k = int(row["requested_k"])
        if requested_k == 200:
            low_tail_ranks[gene][comparison] = int(row["deterministic_rank"])
        elif requested_k in (10, 25):
            panel_tail_comparisons[gene].add(comparison)
    return core_genes, similarity, low_tail_ranks, panel_tail_comparisons


def collect_ora_support(
    path: Path,
) -> tuple[
    dict[str, dict[str, set[str]]],
    dict[str, dict[str, set[tuple[str, str]]]],
    dict[str, dict[str, float]],
]:
    query_support: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    pathway_support: dict[str, dict[str, set[tuple[str, str]]]] = defaultdict(
        lambda: defaultdict(set)
    )
    min_fdr: dict[str, dict[str, float]] = defaultdict(dict)
    for row in read_tsv(path):
        if (
            row["analysis_universe"] != "core_mito"
            or row["tail"] != "low_score"
            or not as_bool(row["tail_fdr_significant"])
        ):
            continue
        collection = row["pathway_collection"]
        comparison = row["comparison_id"]
        pathway = row["pathway_id"]
        fdr = as_float(row["tail_fdr_bh"])
        genes = [gene.strip() for gene in row["overlap_genes"].split(",") if gene.strip()]
        for gene in genes:
            query_support[collection][gene].add(comparison)
            pathway_support[collection][gene].add((comparison, pathway))
            previous = min_fdr[collection].get(gene, 1.0)
            if fdr is not None:
                min_fdr[collection][gene] = min(previous, fdr)
    return query_support, pathway_support, min_fdr


def build_candidate_rows(
    gene_stats: dict[str, dict[str, Any]],
    pathways: dict[str, set[str]],
    hierarchies: dict[str, set[str]],
    core_genes: set[str],
    similarity: dict[str, dict[str, dict[str, float]]],
    low_tail_ranks: dict[str, dict[str, int]],
    panel_tail_comparisons: dict[str, set[str]],
    ora_queries: dict[str, dict[str, set[str]]],
    ora_pathways: dict[str, dict[str, set[tuple[str, str]]]],
    ora_min_fdr: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    focused = "mitocarta_mitopathways_v3_0"
    primary = "msigdb_c2_cp_v2026_1"
    rows: list[dict[str, Any]] = []

    for gene in sorted(core_genes):
        stats = gene_stats.get(gene, empty_gene_stats())
        role, control_programs, secondary_programs, name_control_hint = classify_role(
            gene,
            stats["hgnc_name"],
            stats["genome_origin"],
            pathways.get(gene, set()),
            hierarchies.get(gene, set()),
        )
        comparison_details = similarity.get(gene, {})
        eligible_coverages = [
            values["coverage"]
            for values in comparison_details.values()
            if values["eligible"] == 1.0
        ]
        gene_low_ranks = low_tail_ranks.get(gene, {})
        low_comparisons = set(gene_low_ranks)
        low_families = {COMPARISON_FAMILY[item] for item in low_comparisons}
        rank_signal = sum(
            max(0.0, (201 - gene_low_ranks[comparison]) / 200)
            if comparison in gene_low_ranks
            else 0.0
            for comparison in COMPARISONS
        ) / len(COMPARISONS)
        low_scores = [
            comparison_details[comparison]["score"]
            for comparison in low_comparisons
            if comparison in comparison_details
        ]
        sim_fdr_values = [
            values["fdr"]
            for values in comparison_details.values()
            if values["eligible"] == 1.0
        ]
        top_context = None
        if stats["contexts"]:
            top_context = max(
                stats["contexts"],
                key=lambda item: (
                    safe_log10_p(item["fdr"]),
                    abs(item["logFC"] or 0.0),
                ),
            )

        rows.append(
            {
                "gene": gene,
                "hgnc_id": stats["hgnc_id"],
                "hgnc_name": stats["hgnc_name"],
                "ensembl_id_stable": stats["ensembl_id_stable"],
                "mito_tier": stats["mito_tier"],
                "genome_origin": stats["genome_origin"],
                "sub_mito_localization": stats["sub_mito_localization"],
                "role_class": role,
                "control_programs": ",".join(control_programs),
                "secondary_programs": ",".join(secondary_programs),
                "name_control_hint": name_control_hint,
                "mitocarta_pathway_count": len(pathways.get(gene, set())),
                "mitocarta_pathways": "; ".join(sorted(pathways.get(gene, set()))),
                "assay_eligible_contexts": stats["assay_eligible_contexts"],
                "modeled_contexts": stats["modeled_contexts"],
                "deg_contexts": stats["deg_contexts"],
                "deg_up_contexts": stats["deg_up_contexts"],
                "deg_down_contexts": stats["deg_down_contexts"],
                "deg_cell_types": len(stats["deg_cell_types"]),
                "deg_lineages": len(stats["deg_lineages"]),
                "deg_strata": len(stats["deg_strata"]),
                "median_abs_logFC_sig": median_or_zero(stats["abs_effects"]),
                "max_abs_logFC_sig": max(stats["abs_effects"], default=0.0),
                "min_deg_fdr": (
                    stats["min_deg_fdr"] if stats["deg_contexts"] else None
                ),
                "top_context_cell_type": top_context["cell_type"] if top_context else "",
                "top_context_stratum": top_context["yu_stratum"] if top_context else "",
                "top_context_logFC": top_context["logFC"] if top_context else None,
                "top_context_fdr": top_context["fdr"] if top_context else None,
                "low_tail_comparisons": len(low_comparisons),
                "low_tail_comparison_names": ",".join(
                    comparison
                    for comparison in COMPARISONS
                    if comparison in low_comparisons
                ),
                "low_tail_families": len(low_families),
                "low_tail_family_names": ",".join(sorted(low_families)),
                "mean_low_tail_rank": mean_or_zero(gene_low_ranks.values()),
                "low_tail_rank_signal": rank_signal,
                "mean_low_tail_similarity_score": mean_or_zero(low_scores),
                "panel_tail_comparisons": len(
                    panel_tail_comparisons.get(gene, set())
                ),
                "mean_similarity_coverage": mean_or_zero(eligible_coverages),
                "min_similarity_directional_fdr": (
                    min(sim_fdr_values) if sim_fdr_values else None
                ),
                "similarity_fdr_significant_comparisons": sum(
                    value <= 0.05 for value in sim_fdr_values
                ),
                "focused_ora_query_support": len(
                    ora_queries[focused].get(gene, set())
                ),
                "focused_ora_pathway_hits": len(
                    ora_pathways[focused].get(gene, set())
                ),
                "focused_ora_min_fdr": ora_min_fdr[focused].get(gene),
                "primary_ora_query_support": len(
                    ora_queries[primary].get(gene, set())
                ),
                "primary_ora_pathway_hits": len(
                    ora_pathways[primary].get(gene, set())
                ),
                "primary_ora_min_fdr": ora_min_fdr[primary].get(gene),
                "_all_contexts": stats["all_contexts"],
                "_contexts": stats["contexts"],
            }
        )

    metric_percentiles = {
        "deg_recurrence": percentile_map(
            {row["gene"]: math.log1p(row["deg_contexts"]) for row in rows}
        ),
        "cell_breadth": percentile_map(
            {row["gene"]: row["deg_cell_types"] for row in rows}
        ),
        "lineage_breadth": percentile_map(
            {row["gene"]: row["deg_lineages"] for row in rows}
        ),
        "effect": percentile_map(
            {row["gene"]: row["median_abs_logFC_sig"] for row in rows}
        ),
        "tested": percentile_map(
            {row["gene"]: row["modeled_contexts"] for row in rows}
        ),
    }

    for row in rows:
        gene = row["gene"]
        disease_signal = (
            0.30 * metric_percentiles["deg_recurrence"][gene]
            + 0.20 * metric_percentiles["cell_breadth"][gene]
            + 0.15 * metric_percentiles["lineage_breadth"][gene]
            + 0.15 * (row["deg_strata"] / 6)
            + 0.20 * metric_percentiles["effect"][gene]
        )
        differential_context = (
            0.40 * (row["low_tail_comparisons"] / 6)
            + 0.25 * (row["low_tail_families"] / 3)
            + 0.25 * row["low_tail_rank_signal"]
            + 0.10 * (row["panel_tail_comparisons"] / 6)
        )
        pathway_support = (
            0.55 * (row["focused_ora_query_support"] / 6)
            + 0.45 * (row["primary_ora_query_support"] / 6)
        )
        data_quality = (
            0.50 * metric_percentiles["tested"][gene]
            + 0.50 * row["mean_similarity_coverage"]
        )
        row["disease_signal_score"] = 100 * disease_signal
        row["differential_context_score"] = 100 * differential_context
        row["pathway_support_score"] = 100 * pathway_support
        row["data_quality_score"] = 100 * data_quality
        for scheme, weights in SCORE_SCHEMES.items():
            row[f"{scheme}_score"] = sum(
                weights[component]
                * {
                    "disease_signal": disease_signal,
                    "differential_context": differential_context,
                    "pathway_support": pathway_support,
                    "data_quality": data_quality,
                }[component]
                for component in weights
            ) * 100

    for scheme in SCORE_SCHEMES:
        global_ranks = rank_map(
            {row["gene"]: row[f"{scheme}_score"] for row in rows}
        )
        control_pool = {
            row["gene"]: row[f"{scheme}_score"]
            for row in rows
            if row["genome_origin"].lower() == "nuclear"
            and row["role_class"] == "regulatory_control"
        }
        control_ranks = rank_map(control_pool)
        for row in rows:
            row[f"{scheme}_global_rank"] = global_ranks[row["gene"]]
            row[f"{scheme}_control_rank"] = control_ranks.get(row["gene"])

    for row in rows:
        control_ranks = [
            row[f"{scheme}_control_rank"]
            for scheme in SCORE_SCHEMES
            if row[f"{scheme}_control_rank"] is not None
        ]
        row["median_control_rank"] = (
            statistics.median(control_ranks) if control_ranks else None
        )
        row["top20_control_schemes"] = sum(
            rank is not None and rank <= 20 for rank in control_ranks
        )
    return rows


def shortlist_candidates(
    rows: list[dict[str, Any]], shortlist_size: int
) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if row["genome_origin"].lower() == "nuclear"
        and row["role_class"] == "regulatory_control"
        and row["modeled_contexts"] >= 20
        and row["deg_contexts"] >= 5
        and row["deg_lineages"] >= 3
        and row["low_tail_comparisons"] >= 3
        and row["low_tail_families"] >= 2
        and row["mean_similarity_coverage"] >= 0.50
    ]
    eligible.sort(
        key=lambda row: (
            row["median_control_rank"],
            -row["balanced_score"],
            row["gene"],
        )
    )
    shortlist = eligible[:shortlist_size]
    for index, row in enumerate(shortlist, start=1):
        row["shortlist_rank"] = index
        row["priority_tier"] = "A" if index <= min(8, shortlist_size) else "B"
        row["rationale"] = (
            f"{row['control_programs'] or 'control annotation'}; "
            f"AD-vs-NCI DEG in {row['deg_contexts']} contexts across "
            f"{row['deg_cell_types']} cell types, {row['deg_lineages']} broad "
            f"lineages, and {row['deg_strata']}/6 strata; "
            f"bottom-200 divergent tail in {row['low_tail_comparisons']}/6 "
            f"comparisons spanning {row['low_tail_families']}/3 comparison families."
        )
    return shortlist


def sentinel_markers(rows: list[dict[str, Any]], size: int = 10) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if row["role_class"] in {"mtDNA_structural_marker", "structural_oxphos"}
        and row["deg_contexts"] > 0
    ]
    eligible.sort(key=lambda row: (-row["balanced_score"], row["gene"]))
    sentinels = eligible[:size]
    for index, row in enumerate(sentinels, start=1):
        row["sentinel_rank"] = index
    return sentinels


def build_context_rows(shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for candidate in shortlist:
        contexts = sorted(
            candidate["_contexts"],
            key=lambda item: (
                -(abs(item["logFC"] or 0.0)),
                item["fdr"] if item["fdr"] is not None else 1.0,
                item["cell_type"],
                item["yu_stratum"],
            ),
        )
        for context_rank, context in enumerate(contexts, start=1):
            out.append(
                {
                    "shortlist_rank": candidate["shortlist_rank"],
                    "priority_tier": candidate["priority_tier"],
                    "gene": candidate["gene"],
                    "context_effect_rank": context_rank,
                    **context,
                }
            )
    return out


def build_stratum_rows(shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for candidate in shortlist:
        all_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        significant_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for context in candidate["_all_contexts"]:
            all_grouped[context["yu_stratum"]].append(context)
        for context in candidate["_contexts"]:
            significant_grouped[context["yu_stratum"]].append(context)
        for stratum in ("F_e2x", "F_e33", "F_e4x", "M_e2x", "M_e33", "M_e4x"):
            all_contexts = all_grouped.get(stratum, [])
            significant_contexts = significant_grouped.get(stratum, [])
            all_effects = [
                context["logFC"]
                for context in all_contexts
                if context["logFC"] is not None
            ]
            significant_effects = [
                context["logFC"]
                for context in significant_contexts
                if context["logFC"] is not None
            ]
            out.append(
                {
                    "shortlist_rank": candidate["shortlist_rank"],
                    "priority_tier": candidate["priority_tier"],
                    "gene": candidate["gene"],
                    "yu_stratum": stratum,
                    "modeled_contexts": len(all_contexts),
                    "median_logFC_all": median_or_zero(all_effects),
                    "significant_contexts": len(significant_contexts),
                    "significant_cell_types": len(
                        {context["cell_type"] for context in significant_contexts}
                    ),
                    "median_logFC_sig": median_or_zero(significant_effects),
                    "median_abs_logFC_sig": median_or_zero(
                        abs(effect) for effect in significant_effects
                    ),
                    "up_contexts": sum(effect > 0 for effect in significant_effects),
                    "down_contexts": sum(effect < 0 for effect in significant_effects),
                }
            )
    return out


def build_lineage_rows(shortlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    lineages = sorted(
        {
            context["rds_id"]
            for candidate in shortlist
            for context in candidate["_all_contexts"]
        }
    )
    for candidate in shortlist:
        all_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        significant_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for context in candidate["_all_contexts"]:
            all_grouped[context["rds_id"]].append(context)
        for context in candidate["_contexts"]:
            significant_grouped[context["rds_id"]].append(context)
        for lineage in lineages:
            all_contexts = all_grouped.get(lineage, [])
            significant_contexts = significant_grouped.get(lineage, [])
            all_effects = [
                context["logFC"]
                for context in all_contexts
                if context["logFC"] is not None
            ]
            significant_effects = [
                context["logFC"]
                for context in significant_contexts
                if context["logFC"] is not None
            ]
            out.append(
                {
                    "shortlist_rank": candidate["shortlist_rank"],
                    "priority_tier": candidate["priority_tier"],
                    "gene": candidate["gene"],
                    "rds_id": lineage,
                    "modeled_contexts": len(all_contexts),
                    "median_logFC_all": median_or_zero(all_effects),
                    "significant_contexts": len(significant_contexts),
                    "significant_rate": (
                        len(significant_contexts) / len(all_contexts)
                        if all_contexts
                        else 0.0
                    ),
                    "median_logFC_sig": median_or_zero(significant_effects),
                    "up_contexts": sum(
                        effect > 0 for effect in significant_effects
                    ),
                    "down_contexts": sum(
                        effect < 0 for effect in significant_effects
                    ),
                }
            )
    return out


def candidate_columns() -> list[str]:
    base = [
        "gene",
        "hgnc_id",
        "hgnc_name",
        "ensembl_id_stable",
        "mito_tier",
        "genome_origin",
        "sub_mito_localization",
        "role_class",
        "control_programs",
        "secondary_programs",
        "name_control_hint",
        "mitocarta_pathway_count",
        "mitocarta_pathways",
        "assay_eligible_contexts",
        "modeled_contexts",
        "deg_contexts",
        "deg_up_contexts",
        "deg_down_contexts",
        "deg_cell_types",
        "deg_lineages",
        "deg_strata",
        "median_abs_logFC_sig",
        "max_abs_logFC_sig",
        "min_deg_fdr",
        "top_context_cell_type",
        "top_context_stratum",
        "top_context_logFC",
        "top_context_fdr",
        "low_tail_comparisons",
        "low_tail_comparison_names",
        "low_tail_families",
        "low_tail_family_names",
        "mean_low_tail_rank",
        "low_tail_rank_signal",
        "mean_low_tail_similarity_score",
        "panel_tail_comparisons",
        "mean_similarity_coverage",
        "min_similarity_directional_fdr",
        "similarity_fdr_significant_comparisons",
        "focused_ora_query_support",
        "focused_ora_pathway_hits",
        "focused_ora_min_fdr",
        "primary_ora_query_support",
        "primary_ora_pathway_hits",
        "primary_ora_min_fdr",
        "disease_signal_score",
        "differential_context_score",
        "pathway_support_score",
        "data_quality_score",
    ]
    for scheme in SCORE_SCHEMES:
        base.extend(
            (
                f"{scheme}_score",
                f"{scheme}_global_rank",
                f"{scheme}_control_rank",
            )
        )
    base.extend(("median_control_rank", "top20_control_schemes"))
    return base


def write_report(
    path: Path,
    rows: list[dict[str, Any]],
    shortlist: list[dict[str, Any]],
    sentinels: list[dict[str, Any]],
) -> None:
    no_similarity_hits = sum(
        row["similarity_fdr_significant_comparisons"] for row in rows
    )
    modeled_contexts = max(row["modeled_contexts"] for row in rows)
    assay_eligible_contexts = max(row["assay_eligible_contexts"] for row in rows)
    lines = [
        "# Pre-network mitochondrial regulator prioritization",
        "",
        "## Bottom line",
        "",
        "This is an evidence-integrated nomination analysis, not a causal key-driver "
        "analysis. The existing repository supports strong mitochondrial pathway "
        "divergence, but the local data do not include the cell-type Bayesian "
        "networks needed to establish network hubs.",
        "",
        "The analysis deliberately separates nuclear regulatory-control candidates "
        "from structural OXPHOS/mtDNA markers. Structural genes can be excellent "
        "experimental readouts without being plausible upstream regulators.",
        "",
        "## Preliminary perturbation shortlist",
        "",
    ]
    for row in shortlist:
        lines.append(
            f"- **{row['shortlist_rank']}. {row['gene']} (Tier "
            f"{row['priority_tier']})** — {row['rationale']} Balanced evidence "
            f"score {row['balanced_score']:.1f}/100; median control-gene rank "
            f"{row['median_control_rank']:.0f} across three weighting schemes."
        )
    lines.extend(
        [
            "",
            "## Sentinel/readout genes",
            "",
            "These genes carry strong mitochondrial phenotype signal but should "
            "not be called key regulators from these data alone:",
            "",
        ]
    )
    for row in sentinels[:6]:
        lines.append(
            f"- **{row['gene']}** — {row['deg_contexts']} significant AD-vs-NCI "
            f"contexts, {row['low_tail_comparisons']}/6 divergent tails, balanced "
            f"evidence score {row['balanced_score']:.1f}/100."
        )
    lines.extend(
        [
            "",
            "## Evidence used",
            "",
            "- Phase 09 MAST mitochondrial DEG recurrence, effect size, cell-type "
            "breadth, broad-lineage breadth, and sex/APOE stratum breadth.",
            "- Phase 10 bottom-200 similarity-tail recurrence and rank across six "
            "sex/APOE comparison definitions.",
            "- Phase 11 query-level support from FDR-significant MitoCarta and "
            "MSigDB pathway enrichments; redundant pathway counts are reported "
            "but are not treated as independent evidence.",
            "- MitoCarta pathway annotations and HGNC names to distinguish "
            "control processes from structural/pathway-effector roles.",
            "- Three transparent score weightings (balanced, DEG-heavy, and "
            "context-heavy) to expose ranking sensitivity.",
            "",
            "## Important limits",
            "",
            f"- Phase 08 supplied modeled statistics for up to "
            f"**{modeled_contexts}/{assay_eligible_contexts}** planned contexts; "
            "three male-e2 contrasts were not estimable.",
            f"- Gene-level Phase 10 directional FDR hits in this analysis: "
            f"**{no_similarity_hits}**. Similarity ranks are therefore descriptive; "
            "pathway-level coordination is stronger than single-gene evidence.",
            "- The six comparison definitions are nested, so 6/6 tail recurrence "
            "is robustness evidence, not six independent replications.",
            "- Current DEG evidence is MAST cell-level inference, not donor-level "
            "pseudobulk or formal AD-by-sex/APOE interaction testing.",
            "- MSigDB pathway hits are highly redundant, especially for OXPHOS "
            "and neurodegeneration collections.",
            "- No Bayesian-network KDA, coexpression centrality, AD GWAS, eQTL, "
            "or perturbation evidence is included in the score.",
            "",
            "## Required confirmation step",
            "",
            "Project pathway/contrast-specific DEG signatures onto the matching "
            "cell-type Bayesian networks, test directed neighborhoods by "
            "hypergeometric enrichment with BH correction, and retain candidates "
            "that are both locally supported here and significant network key "
            "drivers. Treat mtDNA/OXPHOS sentinels as downstream assay readouts.",
            "",
            "## Output files",
            "",
            "- `pre_network_candidate_scores.tsv`: all core-mito candidates and "
            "fully decomposed scores.",
            "- `pre_network_shortlist.tsv`: nuclear regulatory-control shortlist.",
            "- `pre_network_shortlist_contexts.tsv`: every significant context "
            "for shortlisted genes.",
            "- `pre_network_shortlist_strata.tsv`: sex/APOE stratum summaries.",
            "- `pre_network_shortlist_lineages.tsv`: normalized broad-lineage "
            "summaries.",
            "- `pre_network_sentinel_markers.tsv`: structural phenotype markers.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else root / "docs" / "analysis" / "mt_pathway"
    )

    inputs = {
        "deg": root
        / "results/minerva_production/09_annotate_genes/deg_mito_core.tsv.gz",
        "similarity": root
        / "results/minerva_production/10_similarity/"
        "mitochondrial_similarity_results.tsv.gz",
        "ranks": root
        / "results/minerva_production/10_similarity/"
        "mitochondrial_similarity_rank_sets.tsv",
        "ora": root
        / "results/minerva_production/11_pathway/"
        "similarity_tail_pathway_ora.tsv.gz",
        "pathways": root
        / "results/minerva_production/03_annotations/mitocarta_pathways.tsv",
    }
    missing = [str(path) for path in inputs.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    if args.shortlist_size < 1:
        raise ValueError("--shortlist-size must be positive")

    pathways, hierarchies = collect_pathways(inputs["pathways"])
    gene_stats = collect_deg_stats(inputs["deg"])
    core_genes, similarity, low_ranks, panel_comparisons = collect_similarity(
        inputs["similarity"], inputs["ranks"]
    )
    ora_queries, ora_pathways, ora_min_fdr = collect_ora_support(inputs["ora"])
    candidates = build_candidate_rows(
        gene_stats,
        pathways,
        hierarchies,
        core_genes,
        similarity,
        low_ranks,
        panel_comparisons,
        ora_queries,
        ora_pathways,
        ora_min_fdr,
    )
    shortlist = shortlist_candidates(candidates, args.shortlist_size)
    sentinels = sentinel_markers(candidates)
    context_rows = build_context_rows(shortlist)
    stratum_rows = build_stratum_rows(shortlist)
    lineage_rows = build_lineage_rows(shortlist)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_columns = candidate_columns()
    write_tsv(
        output_dir / "pre_network_candidate_scores.tsv",
        sorted(candidates, key=lambda row: (-row["balanced_score"], row["gene"])),
        all_columns,
    )
    write_tsv(
        output_dir / "pre_network_shortlist.tsv",
        shortlist,
        ["shortlist_rank", "priority_tier", "rationale", *all_columns],
    )
    write_tsv(
        output_dir / "pre_network_sentinel_markers.tsv",
        sentinels,
        ["sentinel_rank", *all_columns],
    )
    write_tsv(
        output_dir / "pre_network_shortlist_contexts.tsv",
        context_rows,
        [
            "shortlist_rank",
            "priority_tier",
            "gene",
            "context_effect_rank",
            "contrast_id",
            "rds_id",
            "cell_type",
            "sex",
            "apoe_group",
            "yu_stratum",
            "logFC",
            "fdr",
            "cells_ad",
            "cells_nci",
            "donors_ad",
            "donors_nci",
        ],
    )
    write_tsv(
        output_dir / "pre_network_shortlist_strata.tsv",
        stratum_rows,
        [
            "shortlist_rank",
            "priority_tier",
            "gene",
            "yu_stratum",
            "modeled_contexts",
            "median_logFC_all",
            "significant_contexts",
            "significant_cell_types",
            "median_logFC_sig",
            "median_abs_logFC_sig",
            "up_contexts",
            "down_contexts",
        ],
    )
    write_tsv(
        output_dir / "pre_network_shortlist_lineages.tsv",
        lineage_rows,
        [
            "shortlist_rank",
            "priority_tier",
            "gene",
            "rds_id",
            "modeled_contexts",
            "median_logFC_all",
            "significant_contexts",
            "significant_rate",
            "median_logFC_sig",
            "up_contexts",
            "down_contexts",
        ],
    )
    write_report(
        output_dir / "pre_network_prioritization_report.md",
        candidates,
        shortlist,
        sentinels,
    )
    print(
        f"Wrote {len(candidates)} candidate rows, {len(shortlist)} shortlisted "
        f"control genes, and {len(sentinels)} sentinel markers to {output_dir}"
    )


if __name__ == "__main__":
    main()
