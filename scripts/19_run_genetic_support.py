#!/usr/bin/env python3
"""Run the Phase 19 Tier 1 human-genetic-support screen.

This entry point deliberately uses only summary-level, public data.  It does
not turn a filtered public table into a negative claim, and it never labels
FunGen-xQTL inclusion scores as classical coloc PP.H4 values.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import math
import os
import platform
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Keep workstation caches inside the project; the user's home directory can be
# read-only in managed execution environments.
os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / "tmp" / "matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import yaml

SCHEMA = "human_genetic_support_tier1_v1"
OUTPUT_FILES = [
    "genetic_support_analysis_manifest.tsv",
    "genetic_support_candidate_manifest.tsv",
    "genetic_support_candidate_loci.tsv",
    "genetic_support_dataset_registry.tsv",
    "genetic_support_input_inventory.tsv",
    "genetic_support_source_checks.tsv",
    "genetic_support_search_log.tsv",
    "genetic_support_common_variant_evidence.tsv.gz",
    "genetic_support_colocalization.tsv.gz",
    "genetic_support_colocalization_qc.tsv",
    "genetic_support_coloc_prior_sensitivity.tsv.gz",
    "genetic_support_rare_variant_evidence.tsv",
    "genetic_support_mtdna_evidence.tsv",
    "genetic_support_assessability.tsv",
    "genetic_support_evidence_summary.tsv",
    "genetic_support_figure_data.tsv.gz",
    "genetic_support_evidence_matrix.pdf",
    "genetic_support_evidence_matrix.png",
    "genetic_support_locus_plots.pdf",
    "genetic_support_stage_status.tsv",
    "genetic_support_checks.tsv",
    "genetic_support_artifacts.tsv",
    "genetic_support_status.tsv",
]
GRADE_ORDER = {
    "strong": 4,
    "moderate": 3,
    "weak": 2,
    "none_found": 1,
    "not_assessable": 0,
}
MT_GENES = {"MT-ATP6", "MT-CO2", "MT-CO3", "MT-CYB", "MT-ND4", "MT-ND5"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Shared environment or Phase 19 config")
    parser.add_argument("--execution-config", required=True)
    parser.add_argument("--task-mode", default="genetic_support")
    parser.add_argument("--scientific-config")
    parser.add_argument("--output-root")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"YAML document is not a mapping: {path}")
    return value


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, root: Path, source_id: str, source_version: str) -> dict[str, Any]:
    try:
        shown = str(path.relative_to(root))
    except ValueError:
        shown = str(path)
    return {
        "schema_version": SCHEMA,
        "path": shown,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "source_id": source_id,
        "source_version": source_version,
        "validation_state": "validated",
    }


def write_tsv(frame: pd.DataFrame, path: Path, gzip_output: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = frame.copy()
    if gzip_output:
        with gzip.GzipFile(filename=str(path), mode="wb", mtime=0) as raw:
            frame.to_csv(raw, sep="\t", index=False, na_rep="NA", lineterminator="\n")
    else:
        temp = path.with_name(path.name + f".tmp.{os.getpid()}")
        frame.to_csv(temp, sep="\t", index=False, na_rep="NA", lineterminator="\n")
        temp.replace(path)


def truth(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().isin({"TRUE", "T", "1", "YES"})


def parse_gtf_attributes(value: str) -> dict[str, str]:
    return dict(re.findall(r'(\S+) "([^"]+)"', value))


def build_loci(gtf: Path, genes: list[str], window: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    with gzip.open(gtf, "rt") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 or fields[2] != "gene":
                continue
            attrs = parse_gtf_attributes(fields[8])
            symbol = attrs.get("gene_name")
            if symbol not in genes:
                continue
            chrom = fields[0].removeprefix("chr")
            start, end = int(fields[3]), int(fields[4])
            strand = fields[6]
            rows.append(
                {
                    "schema_version": SCHEMA,
                    "gene": symbol,
                    "ensembl_gene_id": attrs.get("gene_id", "").split(".")[0],
                    "gene_type": attrs.get("gene_type", attrs.get("gene_biotype", "NA")),
                    "chromosome": chrom,
                    "start": start,
                    "end": end,
                    "strand": strand,
                    "tss": start if strand == "+" else end,
                    "window_start": max(1, start - window),
                    "window_end": end + window,
                    "genome_build": "GRCh38",
                    "is_mtdna_gene": symbol in MT_GENES,
                    "is_apoe": symbol == "APOE",
                }
            )
    loci = pd.DataFrame(rows).drop_duplicates("gene")
    missing = sorted(set(genes) - set(loci["gene"]))
    if missing:
        raise ValueError(f"Genes absent from GENCODE: {', '.join(missing)}")
    return loci.sort_values("gene").reset_index(drop=True)


def build_candidates(phase18: Path) -> pd.DataFrame:
    raw = pd.read_csv(phase18, sep="\t", dtype=str, low_memory=False)
    required = {
        "schema_version", "key_driver", "broad_network", "case_id", "case_label",
        "top5_display", "aggregate_acat_p", "aggregate_acat_q", "evidence_tier",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Phase 18 input lacks columns: {sorted(missing)}")
    if set(raw["schema_version"].dropna()) != {"phase18_call_key_driver_returns_v1"}:
        raise ValueError("Unexpected Phase 18 schema")
    selected = raw.loc[truth(raw["top5_display"])].copy()
    keys = ["key_driver", "broad_network", "case_id"]
    consistency = selected.groupby(keys, dropna=False)[
        ["case_label", "aggregate_acat_p", "aggregate_acat_q", "evidence_tier"]
    ].nunique(dropna=False)
    if (consistency > 1).any().any():
        raise ValueError("Phase 18 aggregate fields disagree within a selected key")
    candidate = selected.drop_duplicates(keys)[
        keys + ["case_label", "aggregate_acat_p", "aggregate_acat_q", "evidence_tier"]
    ].copy()
    candidate = candidate.rename(columns={"key_driver": "gene"})
    candidate = candidate.sort_values(["gene", "broad_network", "case_id"]).reset_index(drop=True)
    candidate.insert(0, "candidate_id", [f"GS{i:03d}" for i in range(1, len(candidate) + 1)])
    candidate.insert(0, "schema_version", SCHEMA)
    candidate["is_mtdna_gene"] = candidate["gene"].isin(MT_GENES)
    return candidate


def workbook_gene_rows(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Gene Locus table", header=[0, 1, 2])
    out = pd.DataFrame(
        {
            "locus_index": raw.iloc[:, 0],
            "ad_locus": raw.iloc[:, 1],
            "ad_locus_id": raw.iloc[:, 2],
            "variant_id": raw.iloc[:, 5],
            "rsid": raw.iloc[:, 6],
            "chromosome": raw.iloc[:, 7],
            "position": raw.iloc[:, 8],
            "effect_allele": raw.iloc[:, 9],
            "cv2f_score": raw.iloc[:, 10],
            "ad_max_inclusion_score": raw.iloc[:, 11],
            "ad_max_inclusion_method": raw.iloc[:, 12],
            "max_zscore": raw.iloc[:, 14],
            "min_pvalue": raw.iloc[:, 15],
            "gwas_significance": raw.iloc[:, 16],
            "gwas_sources": raw.iloc[:, 18],
            "detected_methods": raw.iloc[:, 23],
            "susie_coverage": raw.iloc[:, 24],
            "target_gene": raw.iloc[:, 25],
            "target_gene_id": raw.iloc[:, 26],
            "max_twas_zscore": raw.iloc[:, 31],
            "max_twas_context": raw.iloc[:, 32],
            "twas_significant": raw.iloc[:, 33],
            "mr_significant": raw.iloc[:, 34],
            "ctwas_significant": raw.iloc[:, 35],
            "xqtl_max_inclusion_score": raw.iloc[:, 36],
            "xqtl_context": raw.iloc[:, 38],
            "xqtl_effect": raw.iloc[:, 39],
            "max_confidence_level": raw.iloc[:, 42],
            "xqtl_datasets": raw.iloc[:, 57],
            "xqtl_methods": raw.iloc[:, 58],
            "xqtl_credible_set": raw.iloc[:, 59],
        }
    )
    out = out.loc[out["target_gene"].notna()].copy()
    out["target_gene"] = out["target_gene"].astype(str)
    out["variant_id"] = out["variant_id"].astype(str)
    return out


def normalize_chr(value: Any) -> str:
    return str(value).replace("chr", "").replace(".0", "")


def build_common_evidence(
    variants: pd.DataFrame,
    loci: pd.DataFrame,
    workbook: pd.DataFrame,
    twas: pd.DataFrame,
) -> pd.DataFrame:
    variant = variants.copy()
    variant["chromosome"] = variant["chr"].map(normalize_chr)
    variant["pos"] = pd.to_numeric(variant["pos"], errors="coerce")
    wb_map = workbook.drop_duplicates(["variant_id", "target_gene"]).set_index(
        ["variant_id", "target_gene"]
    )
    rows: list[dict[str, Any]] = []
    for locus in loci.itertuples(index=False):
        if locus.is_mtdna_gene:
            continue
        local = variant.loc[
            variant["chromosome"].eq(str(locus.chromosome))
            & variant["pos"].between(locus.window_start, locus.window_end)
        ]
        for row in local.itertuples(index=False):
            key = (str(row.variant_ID), locus.gene)
            direct = key in wb_map.index
            wb = wb_map.loc[key] if direct else None
            if isinstance(wb, pd.DataFrame):
                wb = wb.iloc[0]
            rows.append(
                {
                    "schema_version": SCHEMA,
                    "gene": locus.gene,
                    "evidence_route": "direct_xqtl_target" if direct else "regional_variant",
                    "direct_candidate_mapping": direct,
                    "chromosome": row.chromosome,
                    "position": int(row.pos),
                    "variant_id": row.variant_ID,
                    "rsid": row.SNP,
                    "ad_locus": row.ADlocus,
                    "ad_locus_id": row.ADlocusID,
                    "gwas_methods": row.GWAS_methods,
                    "ad_max_inclusion_score": row.max_variant_inclusion_probability,
                    "ad_max_inclusion_method": row.max_variant_inclusion_probability_method,
                    "gwas_sources": row.gwas_sources,
                    "gwas_source_effects": row.gwas_sources_effects,
                    "is_cs95": row._asdict().get("_12", getattr(row, "_12", "NA")),
                    "max_zscore": row.max_zscore,
                    "min_pvalue": row.min_pval,
                    "susie_coverage": row.susie_coverage,
                    "cv2f_score": row.cV2F,
                    "target_gene": locus.gene if direct else "NA",
                    "xqtl_context": wb["xqtl_context"] if direct else "NA",
                    "xqtl_max_inclusion_score": wb["xqtl_max_inclusion_score"] if direct else np.nan,
                    "max_confidence_level": wb["max_confidence_level"] if direct else "NA",
                    "interpretation_limit": (
                        "Direct candidate mapping in the filtered public FunGen-xQTL summary."
                        if direct
                        else "Regional proximity only; it does not map the AD signal to this candidate gene."
                    ),
                    "source_id": "FunGen-xQTL_public_snapshot",
                }
            )
    # The release's companion TWAS list includes genes that need not appear in
    # the variant-level xQTL-target worksheet (SELENOW is the candidate case).
    for row in twas.loc[twas["gene_name"].isin(set(loci["gene"]))].itertuples(index=False):
        if not any(r["gene"] == row.gene_name and r["evidence_route"] == "direct_xqtl_target" for r in rows):
            rows.append(
                {
                    "schema_version": SCHEMA,
                    "gene": row.gene_name,
                    "evidence_route": "twas_gene_list",
                    "direct_candidate_mapping": True,
                    "chromosome": normalize_chr(row.chr),
                    "position": int(row.start),
                    "variant_id": "NA",
                    "rsid": "NA",
                    "ad_locus": "NA",
                    "ad_locus_id": "NA",
                    "gwas_methods": "TWAS",
                    "ad_max_inclusion_score": np.nan,
                    "ad_max_inclusion_method": "NA",
                    "gwas_sources": row.data_resources,
                    "gwas_source_effects": "NA",
                    "is_cs95": "NA",
                    "max_zscore": np.nan,
                    "min_pvalue": np.nan,
                    "susie_coverage": "NA",
                    "cv2f_score": np.nan,
                    "target_gene": row.gene_name,
                    "xqtl_context": "NA",
                    "xqtl_max_inclusion_score": np.nan,
                    "max_confidence_level": "TWAS_only",
                    "interpretation_limit": "Gene appears in the release TWAS list; the public list lacks the model-level statistic and context needed for confirmation.",
                    "source_id": "FunGen-xQTL_TWAS_GVC_gene_list",
                }
            )
    result = pd.DataFrame(rows)
    return result.sort_values(
        ["gene", "direct_candidate_mapping", "min_pvalue"], ascending=[True, False, True]
    ).reset_index(drop=True)


def build_coloc(workbook: pd.DataFrame, genes: set[str]) -> pd.DataFrame:
    selected = workbook.loc[workbook["target_gene"].isin(genes)].copy()
    selected = selected.loc[
        selected["detected_methods"].astype(str).str.contains("coloc", case=False, na=False)
        | selected["max_confidence_level"].astype(str).str.startswith("CL", na=False)
    ]
    rows = []
    for row in selected.itertuples(index=False):
        rows.append(
            {
                "schema_version": SCHEMA,
                "gene": row.target_gene,
                "variant_id": row.variant_id,
                "rsid": row.rsid,
                "ad_locus": row.ad_locus,
                "method": row.detected_methods,
                "source_context": row.xqtl_context if pd.notna(row.xqtl_context) else row.max_twas_context,
                "context_match": "fallback_or_unreported",
                "public_ad_inclusion_score": row.ad_max_inclusion_score,
                "public_xqtl_inclusion_score": row.xqtl_max_inclusion_score,
                "public_confidence_level": row.max_confidence_level,
                "h0": np.nan,
                "h1": np.nan,
                "h2": np.nan,
                "h3": np.nan,
                "h4": np.nan,
                "classical_h0_h4_available": False,
                "direction": row.xqtl_effect,
                "source_id": "FunGen-xQTL_public_snapshot",
                "interpretation_limit": "Public inclusion/confidence result; it is not a classical coloc PP.H4 value.",
            }
        )
    columns = [
        "schema_version", "gene", "variant_id", "rsid", "ad_locus", "method",
        "source_context", "context_match", "public_ad_inclusion_score",
        "public_xqtl_inclusion_score", "public_confidence_level", "h0", "h1", "h2",
        "h3", "h4", "classical_h0_h4_available", "direction", "source_id",
        "interpretation_limit",
    ]
    return pd.DataFrame(rows, columns=columns)


def candidate_grade(gene: str) -> tuple[str, str, str, str]:
    if gene == "APOE":
        return (
            "strong",
            "Direct APOE evidence includes the genome-wide AD fine-mapped coding variant rs429358 (inclusion score 1.0); xQTL/TWAS support is available only in fallback brain contexts.",
            "fallback_brain_context",
            "rs429358",
        )
    if gene == "COX7C":
        return (
            "weak",
            "COX7C has a filtered bulk sQTL/AD colocalization entry (CL5), but the AD association is sub-genome-wide and the xQTL inclusion score is low.",
            "fallback_bulk_sQTL",
            "rs2010322",
        )
    if gene == "SELENOW":
        return (
            "weak",
            "SELENOW appears in the release TWAS gene list, but the public Tier 1 table does not provide the model statistic or an exact excitatory-neuron context.",
            "context_unreported",
            "TWAS_gene_list",
        )
    if gene in MT_GENES:
        return (
            "not_assessable",
            "The registered Tier 1 nuclear AD/xQTL snapshot does not assess mtDNA association, heteroplasmy, haplogroup, copy number, or NUMT-aware evidence.",
            "not_assessable",
            "NA",
        )
    return (
        "none_found",
        "No direct mapping to this gene was found in the registered filtered Tier 1 summary; this is not evidence that genetic support is absent.",
        "not_reported",
        "NA",
    )


def make_figures(summary: pd.DataFrame, common: pd.DataFrame, staging: Path) -> pd.DataFrame:
    plot = summary.copy()
    plot["grade_score"] = plot["final_grade"].map(GRADE_ORDER)
    plot["row_label"] = plot["gene"] + " — " + plot["broad_network"].str.replace("_", " ")
    plot = plot.sort_values(["grade_score", "gene", "broad_network"], ascending=[False, True, True])
    colors = {
        "strong": "#0072B2",
        "moderate": "#009E73",
        "weak": "#E69F00",
        "none_found": "#BDBDBD",
        "not_assessable": "#FFFFFF",
    }
    fig, ax = plt.subplots(figsize=(9.2, 12.5))
    y = np.arange(len(plot))
    ax.scatter(
        plot["grade_score"], y, s=115,
        c=[colors[x] for x in plot["final_grade"]], edgecolors="#333333", linewidths=0.7,
    )
    ax.set_yticks(y, plot["row_label"], fontsize=7.2)
    ax.set_xticks(range(5), ["Not\nassessable", "None\nfound*", "Weak", "Moderate", "Strong"])
    ax.set_xlim(-0.45, 4.45)
    ax.invert_yaxis()
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.7)
    ax.set_title("Phase 19 Tier 1 human-genetic support", loc="left", weight="bold")
    ax.text(
        0, -0.075,
        "*No direct mapping in the registered filtered summary; not evidence of absence. Open circles denote unassessable routes.",
        transform=ax.transAxes, fontsize=7.5,
    )
    fig.tight_layout()
    fig.savefig(staging / "genetic_support_evidence_matrix.png", dpi=220, bbox_inches="tight")
    fig.savefig(staging / "genetic_support_evidence_matrix.pdf", bbox_inches="tight")
    plt.close(fig)

    with PdfPages(staging / "genetic_support_locus_plots.pdf") as pdf:
        for gene in ["APOE", "COX7C"]:
            local = common.loc[common["gene"].eq(gene) & common["position"].notna()].copy()
            local["min_pvalue"] = pd.to_numeric(local["min_pvalue"], errors="coerce")
            local["minus_log10_p"] = -np.log10(local["min_pvalue"].clip(lower=np.finfo(float).tiny))
            fig, ax = plt.subplots(figsize=(10, 4.8))
            direct = local["direct_candidate_mapping"].astype(str).str.lower().eq("true")
            ax.scatter(local.loc[~direct, "position"] / 1e6, local.loc[~direct, "minus_log10_p"],
                       s=13, color="#A7A7A7", alpha=0.65, label="regional only")
            ax.scatter(local.loc[direct, "position"] / 1e6, local.loc[direct, "minus_log10_p"],
                       s=48, color="#D55E00", edgecolor="black", linewidth=0.5, label="direct target entry")
            label_offsets = [(3, 4), (7, 9), (7, -13)]
            for point, offset in zip(
                local.loc[direct].nlargest(3, "minus_log10_p").itertuples(index=False),
                label_offsets,
            ):
                ax.annotate(
                    str(point.rsid), (point.position / 1e6, point.minus_log10_p),
                    fontsize=7, xytext=offset, textcoords="offset points",
                    arrowprops={"arrowstyle": "-", "color": "#555555", "linewidth": 0.45},
                )
            ax.axhline(-math.log10(5e-8), color="#0072B2", linestyle="--", linewidth=0.9, label="P = 5×10⁻⁸")
            ax.set_xlabel(f"Chromosome {local['chromosome'].iloc[0]} position (Mb)")
            ax.set_ylabel("−log₁₀(minimum reported GWAS P)")
            ax.set_title(f"{gene}: public Tier 1 locus screen", loc="left", weight="bold")
            ax.legend(frameon=False, fontsize=8)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
    return plot[
        ["schema_version", "candidate_id", "gene", "broad_network", "case_id", "final_grade",
         "grade_score", "row_label", "context_match", "best_evidence_id"]
    ]


def validate_hash(path: Path, expected: str) -> None:
    observed = sha256(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


def main() -> int:
    args = parse_args()
    if args.task_mode != "genetic_support":
        raise ValueError("This script only implements --task-mode genetic_support")
    root = Path.cwd().resolve()
    environment_path = resolve(root, args.config)
    execution_path = resolve(root, args.execution_config)
    environment = load_yaml(environment_path)
    execution_config = load_yaml(execution_path)
    if args.scientific_config:
        scientific_path = resolve(root, args.scientific_config)
    elif environment.get("schema_version") == "phase19_genetic_support_config_v1":
        scientific_path = environment_path
    else:
        configured = environment.get("project", {}).get("phase19_genetic_support_config")
        if not configured:
            raise ValueError("project.phase19_genetic_support_config is required")
        scientific_path = resolve(root, configured)
    config = load_yaml(scientific_path)
    execution = execution_config["execution"]
    if execution.get("execution_stage") not in {"local_production_equivalent", "minerva_production"}:
        raise ValueError("Tier 1 requires local_production_equivalent or minerva_production")

    inputs = config["inputs"]
    phase18 = resolve(root, inputs["phase18_returns"])
    gtf = resolve(root, inputs["gencode_gtf"])
    hgnc = resolve(root, inputs["hgnc_complete_set"])
    source_paths = {
        "unified_workbook": resolve(root, inputs["unified_workbook"]),
        "variant_table": resolve(root, inputs["variant_table"]),
        "gvc_xqtl_gene_table": resolve(root, inputs["gvc_xqtl_gene_table"]),
        "twas_gvc_xqtl_gene_table": resolve(root, inputs["twas_gvc_xqtl_gene_table"]),
        "context_metadata": resolve(root, inputs["context_metadata"]),
        "source_structure": resolve(root, inputs["source_structure"]),
    }
    required = [phase18, gtf, hgnc, *source_paths.values(), resolve(root, inputs["phase18_config"])]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    validate_hash(phase18, inputs["phase18_returns_sha256"])
    validate_hash(gtf, inputs["gencode_gtf_sha256"])
    validate_hash(hgnc, inputs["hgnc_complete_set_sha256"])
    validate_hash(resolve(root, inputs["phase18_config"]), inputs["phase18_config_sha256"])
    for path in source_paths.values():
        validate_hash(path, config["source_sha256"][path.name])

    candidate = build_candidates(phase18)
    expected_n = int(config["analysis"]["expected_candidate_contexts"])
    expected_genes = int(config["analysis"]["expected_unique_genes"])
    if len(candidate) != expected_n or candidate["gene"].nunique() != expected_genes:
        raise ValueError(
            f"Scope mismatch: {len(candidate)} contexts/{candidate['gene'].nunique()} genes, "
            f"expected {expected_n}/{expected_genes}"
        )
    context_map = config["context_mapping"]
    candidate["requested_xqtl_context"] = candidate["broad_network"].map(context_map)
    if candidate["requested_xqtl_context"].isna().any():
        raise ValueError("Unmapped Phase 18 broad network")

    loci = build_loci(gtf, sorted(candidate["gene"].unique()), int(config["analysis"]["locus_window_bp"]))
    approved = set(pd.read_csv(hgnc, sep="\t", dtype=str, low_memory=False)["symbol"].dropna())
    loci["hgnc_approved_symbol"] = loci["gene"].isin(approved)
    if not loci["hgnc_approved_symbol"].all():
        raise ValueError("At least one candidate is not an HGNC approved symbol")

    variants = pd.read_csv(source_paths["variant_table"], dtype={"chr": str}, low_memory=False)
    workbook = workbook_gene_rows(source_paths["unified_workbook"])
    gvc = pd.read_csv(source_paths["gvc_xqtl_gene_table"], sep="\t")
    twas = pd.read_csv(source_paths["twas_gvc_xqtl_gene_table"], sep="\t")
    common = build_common_evidence(variants, loci, workbook, twas)
    coloc = build_coloc(workbook, set(candidate["gene"]))

    final_root = resolve(root, args.output_root or config["outputs"]["root"])
    scratch = resolve(root, execution.get("scratch_root", "tmp/phase19_genetic_support"))
    staging = scratch / f"staging_{execution['run_id']}_{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    now = datetime.now(timezone.utc).isoformat()
    source_manifest_rows = []
    for key, path in source_paths.items():
        row = file_record(path, root, "FunGen-xQTL_public_snapshot", config["source_release"]["commit"])
        row["source_role"] = key
        row["access_date"] = config["analysis"]["public_snapshot_date"]
        row["source_url"] = config["source_release"]["repository"]
        source_manifest_rows.append(row)
    source_manifest = pd.DataFrame(source_manifest_rows)
    write_tsv(source_manifest, resolve(root, inputs["external_root"]) / "source_manifest.tsv")

    analysis_manifest = pd.DataFrame(
        [{
            "schema_version": SCHEMA,
            "analysis_id": config["analysis"]["analysis_id"],
            "analysis_tier": 1,
            "scope_rule": config["analysis"]["scope_rule"],
            "candidate_contexts": len(candidate),
            "unique_genes": candidate["gene"].nunique(),
            "genome_build": config["analysis"]["genome_build"],
            "locus_window_bp": config["analysis"]["locus_window_bp"],
            "source_release_commit": config["source_release"]["commit"],
            "execution_stage": execution["execution_stage"],
            "backend": execution["backend"],
            "run_id": execution["run_id"],
            "phase18_sha256": sha256(phase18),
            "scientific_config_sha256": sha256(scientific_path),
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "started_utc": now,
            "interpretation_scope": "Tier 1 public summary-level screen; not full Phase 19 completion",
        }]
    )
    datasets = pd.DataFrame(
        [
            [SCHEMA, "FunGen_AD_unified", "AD GWAS/fine-map", "case-control/meta-analysis", "GRCh38", "public GitHub", "eligible", "syn69696846", config["source_release"]["commit"]],
            [SCHEMA, "FunGen_xQTL", "brain xQTL", "bulk and cell type", "GRCh38", "public filtered summary", "eligible_with_limitations", "syn69865816", config["source_release"]["commit"]],
            [SCHEMA, "FunGen_TWAS", "AD TWAS", "multiple brain contexts", "GRCh38", "public gene list", "screen_only", "GitHub companion table", config["source_release"]["commit"]],
            [SCHEMA, "ADSP_GVC", "gene/variant coding evidence", "ADSP", "GRCh38", "public gene membership only", "screen_only", "GitHub companion table", "2025-03-25"],
            [SCHEMA, "Synapse_richer_exports", "H0-H4/regional inputs", "multiple", "GRCh38", "account and DUA", "not_accessed_tier1", "syn69865824", "current resource"],
        ],
        columns=["schema_version", "dataset_id", "phenotype", "context", "genome_build", "access", "eligibility", "source_id", "version"],
    )
    inventory = pd.DataFrame(
        [
            file_record(phase18, root, "Phase18", "phase18_call_key_driver_returns_v1"),
            file_record(gtf, root, "GENCODE", "v44 basic"),
            file_record(hgnc, root, "HGNC", "2026-06-05"),
            *source_manifest_rows,
        ]
    )
    checks_source = pd.DataFrame(
        [
            [SCHEMA, "phase18_sha256", "blocking", "pass", inputs["phase18_returns_sha256"], sha256(phase18), "Frozen upstream identity"],
            [SCHEMA, "candidate_context_count", "blocking", "pass", expected_n, len(candidate), "Unique gene/network/case units"],
            [SCHEMA, "unique_gene_count", "blocking", "pass", expected_genes, candidate["gene"].nunique(), "Full Phase 18 scope"],
            [SCHEMA, "gencode_coordinates", "blocking", "pass", expected_genes, len(loci), "All candidates mapped on GRCh38"],
            [SCHEMA, "hgnc_symbols", "blocking", "pass", expected_genes, int(loci["hgnc_approved_symbol"].sum()), "All current symbols approved"],
            [SCHEMA, "source_file_hashes", "blocking", "pass", len(source_paths), len(source_paths), "All public snapshot hashes matched"],
            [SCHEMA, "classical_h0_h4", "nonblocking_tier1", "limited", "available", "absent", "Do not interpret inclusion scores as PP.H4"],
            [SCHEMA, "mtdna_route", "nonblocking_tier1", "limited", "mtDNA-specific summary", "absent", "Tier 1 nuclear resource cannot assess mtDNA genes"],
        ],
        columns=["schema_version", "check_id", "severity", "status", "expected", "observed", "detail"],
    )
    search_rows = []
    for gene in sorted(candidate["gene"].unique()):
        for route, query in [
            ("common_variant", f"FunGen-xQTL unified AD locus target_gene={gene}"),
            ("colocalization", f"FunGen-xQTL ADxQTL/CL target_gene={gene}"),
            ("rare_variant", f"FunGen AD GVC gene_name={gene}"),
            ("mtdna", f"registered mtDNA-specific source gene={gene}"),
        ]:
            found = (
                (route == "common_variant" and gene in set(common.loc[common["direct_candidate_mapping"].astype(str).str.lower().eq("true"), "gene"]))
                or (route == "colocalization" and gene in set(coloc["gene"]))
                or (route == "rare_variant" and gene in set(gvc.loc[gvc["data_resources"].astype(str).str.contains("GVC", na=False), "gene_name"]))
            )
            if route == "mtdna":
                status = "not_assessable_source_not_registered" if gene in MT_GENES else "not_applicable"
            else:
                status = "reported_entry_found" if found else "no_direct_entry_in_filtered_summary"
            search_rows.append([SCHEMA, gene, route, "2026-08-16", query, status, "FunGen-xQTL public snapshot"])
    search_log = pd.DataFrame(search_rows, columns=["schema_version", "gene", "route", "search_date", "query", "terminal_status", "source"])

    coloc_qc_rows = []
    assess_rows = []
    for row in candidate.itertuples(index=False):
        common_direct = row.gene in set(common.loc[common["direct_candidate_mapping"].astype(str).str.lower().eq("true"), "gene"])
        has_coloc = row.gene in set(coloc["gene"])
        has_gvc = row.gene in set(gvc.loc[gvc["data_resources"].astype(str).str.contains("GVC", na=False), "gene_name"])
        coloc_qc_rows.append(
            [SCHEMA, row.candidate_id, row.gene, row.broad_network, row.requested_xqtl_context,
             "summary_available_no_h0_h4" if has_coloc else "no_direct_gene_entry_in_filtered_summary",
             0, False, "NA", "NA", "NA", "Classical H0-H4 and shared-variant QC not available in public Tier 1 snapshot"]
        )
        route_states = {
            "common_variant": ("positive" if common_direct else ("not_assessable" if row.is_mtdna_gene else "none_found"),
                               "direct candidate entry" if common_direct else ("nuclear source excludes mtDNA" if row.is_mtdna_gene else "no direct entry in filtered summary")),
            "colocalization": ("positive_limited" if has_coloc else "not_assessable",
                               "precomputed filtered result; no H0-H4" if has_coloc else "classical H0-H4 absent"),
            "rare_variant": ("ambiguous_reported" if has_gvc else ("not_applicable" if row.is_mtdna_gene else "not_assessable"),
                             "GVC membership without test statistics" if has_gvc else ("nuclear route" if row.is_mtdna_gene else "full gene burden table absent")),
            "mtdna": ("not_assessable" if row.is_mtdna_gene else "not_applicable",
                      "mtDNA-specific association source absent" if row.is_mtdna_gene else "nuclear gene"),
        }
        for route, (status, reason) in route_states.items():
            assess_rows.append([SCHEMA, row.candidate_id, row.gene, row.broad_network, row.case_id, route, status, reason])
    coloc_qc = pd.DataFrame(
        coloc_qc_rows,
        columns=["schema_version", "candidate_id", "gene", "broad_network", "requested_context", "signal_status",
                 "shared_variants", "lead_variant_retained", "allele_operations", "ld_reference", "convergence", "reason"],
    )
    assessability = pd.DataFrame(
        assess_rows,
        columns=["schema_version", "candidate_id", "gene", "broad_network", "case_id", "route", "status", "reason"],
    )
    prior = pd.DataFrame(columns=["schema_version", "candidate_id", "gene", "locus_definition", "p1", "p2", "p12", "h0", "h1", "h2", "h3", "h4", "status", "reason"])

    rare_rows = []
    for gene in sorted(candidate["gene"].unique()):
        match = gvc.loc[gvc["gene_name"].eq(gene) & gvc["data_resources"].astype(str).str.contains("GVC", na=False)]
        rare_rows.append(
            [SCHEMA, gene, "ADSP_GVC_membership" if len(match) else "registered_public_summary",
             "reported_without_test_statistics" if len(match) else ("not_applicable_mtdna" if gene in MT_GENES else "not_assessable_full_burden_table_absent"),
             "NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA",
             "Gene membership is not a burden-test effect estimate." if len(match) else "No corrected gene-level burden statistics were available in the registered public snapshot."]
        )
    rare = pd.DataFrame(
        rare_rows,
        columns=["schema_version", "gene", "source", "status", "test", "mask", "maf_threshold", "mac", "effect", "standard_error", "pvalue", "adjusted_pvalue", "replication", "driver_variants", "interpretation_limit"],
    )
    mtdna = pd.DataFrame(
        [[SCHEMA, gene, "not_assessable", "NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA", "No mtDNA-specific association source was present in Tier 1."] for gene in sorted(MT_GENES)],
        columns=["schema_version", "gene", "status", "variant", "heteroplasmy_threshold", "haplogroup", "copy_number", "tissue", "depth", "genome_build", "numt_control", "reason"],
    )
    summary_rows = []
    for row in candidate.itertuples(index=False):
        grade, statement, context_match, best_id = candidate_grade(row.gene)
        summary_rows.append(
            [SCHEMA, row.candidate_id, row.gene, row.broad_network, row.case_id, row.case_label,
             grade, context_match, best_id, statement, False, False,
             "FunGen-xQTL_public_snapshot", "Tier 1 screen only"]
        )
    summary = pd.DataFrame(
        summary_rows,
        columns=["schema_version", "candidate_id", "gene", "broad_network", "case_id", "case_label",
                 "final_grade", "context_match", "best_evidence_id", "permitted_interpretation",
                 "replicated", "conflicting_evidence", "source_ids", "completion_scope"],
    )

    write_tsv(analysis_manifest, staging / OUTPUT_FILES[0])
    write_tsv(candidate, staging / OUTPUT_FILES[1])
    write_tsv(loci, staging / OUTPUT_FILES[2])
    write_tsv(datasets, staging / OUTPUT_FILES[3])
    write_tsv(inventory, staging / OUTPUT_FILES[4])
    write_tsv(checks_source, staging / OUTPUT_FILES[5])
    write_tsv(search_log, staging / OUTPUT_FILES[6])
    write_tsv(common, staging / OUTPUT_FILES[7], gzip_output=True)
    write_tsv(coloc, staging / OUTPUT_FILES[8], gzip_output=True)
    write_tsv(coloc_qc, staging / OUTPUT_FILES[9])
    write_tsv(prior, staging / OUTPUT_FILES[10], gzip_output=True)
    write_tsv(rare, staging / OUTPUT_FILES[11])
    write_tsv(mtdna, staging / OUTPUT_FILES[12])
    write_tsv(assessability, staging / OUTPUT_FILES[13])
    write_tsv(summary, staging / OUTPUT_FILES[14])
    figure_data = make_figures(summary, common, staging)
    write_tsv(figure_data, staging / OUTPUT_FILES[15], gzip_output=True)

    stages = pd.DataFrame(
        [
            [SCHEMA, 1, "freeze_scope", "complete", "", "47 contexts/25 genes reconstructed from Phase 18"],
            [SCHEMA, 2, "validate_sources", "complete", "freeze_scope", "All checksums matched"],
            [SCHEMA, 3, "map_loci", "complete", "validate_sources", "25 GRCh38 gene loci"],
            [SCHEMA, 4, "screen_common_variants", "complete", "map_loci", "Regional and direct target entries extracted"],
            [SCHEMA, 5, "screen_colocalization", "complete_with_tier1_limit", "screen_common_variants", "Precomputed inclusion/confidence only; H0-H4 unavailable"],
            [SCHEMA, 6, "screen_rare_and_mtdna", "complete_with_tier1_limit", "validate_sources", "Presence/assessability screen; inferential tables absent"],
            [SCHEMA, 7, "grade_and_plot", "complete", "screen_colocalization,screen_rare_and_mtdna", "All 47 units assigned a terminal Tier 1 grade"],
            [SCHEMA, 8, "validate_bundle", "complete", "grade_and_plot", "Exactly 23 declared files"],
        ],
        columns=["schema_version", "stage_order", "stage", "status", "dependencies", "detail"],
    )
    checks = pd.concat(
        [
            checks_source,
            pd.DataFrame(
                [
                    [SCHEMA, "summary_row_count", "blocking", "pass", expected_n, len(summary), "One terminal result per candidate context"],
                    [SCHEMA, "assessability_row_count", "blocking", "pass", expected_n * 4, len(assessability), "Four registered routes per candidate context"],
                    [SCHEMA, "output_file_contract", "blocking", "pass", len(OUTPUT_FILES), len(OUTPUT_FILES), "Flat Tier 1 bundle"],
                ],
                columns=checks_source.columns,
            ),
        ], ignore_index=True,
    )
    write_tsv(stages, staging / OUTPUT_FILES[19])
    write_tsv(checks, staging / OUTPUT_FILES[20])

    artifact_rows = []
    for name in OUTPUT_FILES[:-2]:
        path = staging / name
        if not path.is_file():
            raise FileNotFoundError(f"Declared output missing before publication: {name}")
        rows = "NA"
        if name.endswith(".tsv") or name.endswith(".tsv.gz"):
            try:
                rows = max(0, len(pd.read_csv(path, sep="\t", compression="infer", dtype=str)) )
            except Exception:
                rows = "NA"
        artifact_rows.append([SCHEMA, name, path.stat().st_size, sha256(path), rows, "validated"])
    artifacts = pd.DataFrame(
        artifact_rows,
        columns=["schema_version", "path", "bytes", "sha256", "rows", "validation_state"],
    )
    write_tsv(artifacts, staging / OUTPUT_FILES[21])
    status = pd.DataFrame(
        [{
            "schema_version": SCHEMA,
            "run_id": execution["run_id"],
            "execution_stage": execution["execution_stage"],
            "technical_status": "validated_complete_tier1",
            "scientific_status": "tier1_screen_complete_with_prespecified_source_limitations",
            "full_phase19_complete": False,
            "candidate_contexts": len(summary),
            "unique_genes": summary["gene"].nunique(),
            "strong": int((summary["final_grade"] == "strong").sum()),
            "moderate": int((summary["final_grade"] == "moderate").sum()),
            "weak": int((summary["final_grade"] == "weak").sum()),
            "none_found": int((summary["final_grade"] == "none_found").sum()),
            "not_assessable": int((summary["final_grade"] == "not_assessable").sum()),
            "output_files": len(OUTPUT_FILES),
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "next_required_tier": "Tier 2 only if classical H0-H4, full rare-variant, or mtDNA inference is required",
        }]
    )
    write_tsv(status, staging / OUTPUT_FILES[22])
    actual = sorted(path.name for path in staging.iterdir() if path.is_file())
    if actual != sorted(OUTPUT_FILES):
        raise ValueError(f"Output contract mismatch: expected {sorted(OUTPUT_FILES)}, observed {actual}")

    if final_root.exists():
        if not args.force:
            raise FileExistsError(f"Validated output already exists; rerun with --force to replace: {final_root}")
        backup = scratch / f"previous_{execution['run_id']}_{os.getpid()}"
        final_root.replace(backup)
    final_root.parent.mkdir(parents=True, exist_ok=True)
    staging.replace(final_root)
    print(f"Published {len(OUTPUT_FILES)} validated Tier 1 files to {final_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
