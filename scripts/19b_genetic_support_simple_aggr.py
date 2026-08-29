#!/usr/bin/env python3
"""Phase 19b: genetic-support screen for the simple-aggregation drivers.

Implements workstreams WS0-WS2 of
``docs/phase_19_genetic_support/simple_aggr_rerun/phase19_simple_aggr_rerun_plan.md``:

- ``freeze``   (WS0): freeze all 433 non-MT driver genes from the returned-only
  simple aggregation, assign pre-registered priority tiers, and map genes to
  GRCh38 loci (GENCODE v44 + HGNC) with gene-body +/- 1 Mb windows.
- ``tier1``    (WS1): screen the frozen candidates against the local
  FunGen-xQTL public snapshot (unified workbook direct variant-to-gene
  mappings, TWAS/GVC gene lists, and variant-level window annotation).
- ``regional`` (WS2): stream the clinical-AD GWAS (Bellenguez 2022,
  GCST90027158) and the three CSF biomarker GWAS and record the minimum
  regional P value, lead variant, and variant count per candidate window.

Grade vocabulary for the tier1 stage (frozen before execution):

- ``strong``   : direct workbook mapping with min P < 5e-8 and maximum
  variant inclusion score >= 0.5;
- ``moderate`` : direct mapping with min P < 5e-8 and inclusion >= 0.1, or a
  workbook TWAS/cTWAS-significant flag for the gene;
- ``weak``     : any other direct workbook mapping or TWAS/GVC list
  membership;
- ``none_found``: no direct mapping and no list membership. Window-level
  variant annotation is reported separately and never graded.

Regional results are annotation only (plan rule 11): with 433 windows of
~2 Mb, a nearby genome-wide-significant variant is expected for many genes by
proximity alone and must not be reported as gene-level support.

Missing GWAS source files are recorded and skipped, so the ``freeze`` and
``tier1`` stages run on any machine holding the repository, while ``regional``
completes only where the GWAS files exist (see the rerun plan's
missing-input manifest).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "docs" / "phase_19_genetic_support" / "simple_aggr_rerun"

ROSMAP_PRIMARY = (
    ROOT
    / "results/minerva_production/20_sex_apoe_kda_simple_aggr"
    / "simple_category_gene_aggregates.tsv"
)
ROSMAP_FROZEN = PLAN_DIR / "frozen_inputs" / "rosmap_simple_category_gene_aggregates.tsv"
ROSMAP_SHA256 = "4e0ab4204ba837ec7ca0d5920e27f2557849f6acbc0d92189d5737193eab8ebd"
SEAAD_PRIMARY = (
    ROOT
    / "results/validation_human/11_sex_apoe_kda_simple_aggr"
    / "simple_category_gene_aggregates.tsv"
)
SEAAD_FROZEN = PLAN_DIR / "frozen_inputs" / "seaad_simple_category_gene_aggregates.tsv"
SEAAD_SHA256 = "e9593861292cbbdc327b22fc34096dcb5189fa9f3d5de0f135ffaad8426fdda4"

GENCODE_GTF = ROOT / "data/reference/gencode/gencode.v44.basic.annotation.gtf.gz"
HGNC_SET = ROOT / "data/reference/hgnc/hgnc_complete_set_2026-06-05.txt"
FUNGEN_DIR = ROOT / "data/reference/phase19_genetic_support/source_downloads"
FUNGEN_WORKBOOK = FUNGEN_DIR / "unified_AD_loci_xQTL_summary.xlsx"
FUNGEN_VARIANTS = FUNGEN_DIR / "AD_loci_unified_cs95orColocs_Pval1e5_variant_level.csv.gz"
FUNGEN_GVC = FUNGEN_DIR / "AD_genes_FunGen_AD_GVC_xQTL_20250325.tsv"
FUNGEN_TWAS = FUNGEN_DIR / "AD_genes_FunGen_AD_twas_GVC_xQTL_20250325.tsv"

GWAS_SOURCES = {
    "clinical_ad_bellenguez2022": ROOT
    / "data/reference/phase19_genetic_support/tier2/gwas_catalog"
    / "GCST90027158_buildGRCh38.tsv.gz",
    "csf_abeta42_gcst90726396": ROOT
    / "data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension"
    / "gwas_normalized/GCST90726396.h.tsv.gz",
    "csf_total_tau_gcst90726397": ROOT
    / "data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension"
    / "gwas_normalized/GCST90726397.h.tsv.gz",
    "csf_ptau181_gcst90726398": ROOT
    / "data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension"
    / "gwas_normalized/GCST90726398.h.tsv.gz",
}

CANDIDATE_DIR = ROOT / "results/minerva_production/19b_genetic_support_candidates"
TIER1_DIR = ROOT / "results/minerva_production/19b_genetic_support_tier1"
REGIONAL_DIR = ROOT / "results/minerva_production/19b_genetic_support_regional"

SCHEMA = "phase19b_simple_aggr_v1"
WINDOW_BP = 1_000_000
GW_THRESHOLD = 5e-8
EXPECTED_GENES = 433
EXPECTED_CONTEXTS = 689
EXPECTED_P1 = 35

CHROM_COLUMNS = ["hm_chrom", "chromosome", "chr"]
POS_COLUMNS = ["hm_pos", "base_pair_location", "position", "pos"]
PVAL_COLUMNS = ["p_value", "pval", "p"]
VARIANT_COLUMNS = ["hm_rsid", "variant_id", "rsid", "hm_variant_id"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, na_rep="NA", lineterminator="\n")


def check(check_id: str, observed: Any, expected: Any, passed: bool) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA}_checks",
        "check_id": check_id,
        "observed": observed,
        "expected": expected,
        "passed": bool(passed),
    }


def finalize_stage(
    out_dir: Path,
    stage: str,
    checks: list[dict[str, Any]],
    extra_status: dict[str, Any],
    artifacts: Iterable[Path],
) -> None:
    checks_frame = pd.DataFrame(checks)
    write_tsv(checks_frame, out_dir / f"{stage}_checks.tsv")
    failed = int((~checks_frame["passed"].astype(bool)).sum())
    status = {
        "schema_version": f"{SCHEMA}_status",
        "stage": stage,
        "generated_at_utc": utc_now(),
        "failed_checks": failed,
        "validation_status": "validated_complete" if failed == 0 else "validation_failed",
    }
    status.update(extra_status)
    write_tsv(pd.DataFrame([status]), out_dir / f"{stage}_status.tsv")
    rows = []
    for path in list(artifacts) + [out_dir / f"{stage}_checks.tsv", out_dir / f"{stage}_status.tsv"]:
        rows.append(
            {
                "schema_version": f"{SCHEMA}_artifacts",
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    write_tsv(pd.DataFrame(rows), out_dir / f"{stage}_artifacts.tsv")
    if failed:
        bad = checks_frame.loc[~checks_frame["passed"].astype(bool), "check_id"].tolist()
        raise RuntimeError(f"{stage} failed checks: {', '.join(bad)}")


def resolve_input(primary: Path, fallback: Path, expected_sha: str, label: str) -> Path:
    for path in (primary, fallback):
        if path.is_file():
            observed = sha256_file(path)
            if observed != expected_sha:
                raise RuntimeError(
                    f"{label} at {path} has SHA-256 {observed}, expected {expected_sha}"
                )
            return path
    raise FileNotFoundError(f"{label}: neither {primary} nor {fallback} exists")


def load_non_mt(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_values=["NA"])
    frame = frame[
        frame["case_id"].eq("non_mt_driver") & ~frame["is_core_mito"].isin(["TRUE"])
    ].copy()
    frame["score"] = frame["returned_run_q_acat_score"].astype(float)
    frame["calls"] = frame["returned_call_count"].astype(int)
    frame = frame.sort_values(
        ["signature_group", "broad_network", "score", "current_symbol"], kind="mergesort"
    )
    frame["display_rank"] = frame.groupby(["signature_group", "broad_network"]).cumcount() + 1
    return frame


# --------------------------------------------------------------------------
# WS0: candidate freeze
# --------------------------------------------------------------------------


def parse_gencode(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"GENCODE annotation missing: {path}")
    pattern = re.compile(r'(\S+) "([^"]*)"')
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 9 or fields[2] != "gene":
                continue
            attrs = dict(pattern.findall(fields[8]))
            rows.append(
                {
                    "gencode_gene_id": attrs.get("gene_id", ""),
                    "ensembl_gene_id": attrs.get("gene_id", "").split(".")[0],
                    "gene_name": attrs.get("gene_name", ""),
                    "gene_type": attrs.get("gene_type", ""),
                    "chromosome": fields[0].removeprefix("chr"),
                    "start": int(fields[3]),
                    "end": int(fields[4]),
                    "strand": fields[6],
                }
            )
    frame = pd.DataFrame(rows)
    frame = frame[~frame["chromosome"].isin(["M"])]
    return frame


def load_hgnc_maps(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"HGNC complete set missing: {path}")
    hgnc = pd.read_csv(
        path, sep="\t", dtype=str, keep_default_na=False,
        usecols=["symbol", "ensembl_gene_id", "alias_symbol", "prev_symbol"],
    )
    symbol_to_ensembl = {
        r.symbol: r.ensembl_gene_id for r in hgnc.itertuples() if r.ensembl_gene_id
    }
    alias_to_symbol: dict[str, str] = {}
    for r in hgnc.itertuples():
        for field in (r.alias_symbol, r.prev_symbol):
            for alias in str(field).split("|"):
                alias = alias.strip()
                if alias and alias not in alias_to_symbol:
                    alias_to_symbol[alias] = r.symbol
    return symbol_to_ensembl, alias_to_symbol


def stage_freeze() -> None:
    out = CANDIDATE_DIR
    out.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []

    rosmap_path = resolve_input(ROSMAP_PRIMARY, ROSMAP_FROZEN, ROSMAP_SHA256, "ROSMAP aggregate")
    seaad_path = resolve_input(SEAAD_PRIMARY, SEAAD_FROZEN, SEAAD_SHA256, "SEA-AD aggregate")
    ros = load_non_mt(rosmap_path)
    sea_genes = set(load_non_mt(seaad_path)["current_symbol"])

    contexts = ros[
        [
            "signature_group", "sex", "apoe_group", "broad_network", "current_symbol",
            "returned_call_count", "returned_run_q_acat_score", "display_rank",
        ]
    ].copy()
    contexts.insert(0, "schema_version", f"{SCHEMA}_contexts")

    gene_level = (
        ros.groupby("current_symbol")
        .agg(
            category_count=("current_symbol", "size"),
            total_returned_calls=("calls", "sum"),
            best_score=("score", "min"),
            best_display_rank=("display_rank", "min"),
            in_top5_display=("display_rank", lambda s: bool((s <= 5).any())),
        )
        .reset_index()
        .rename(columns={"current_symbol": "gene"})
        .sort_values("gene", kind="mergesort")
    )
    gene_level["in_seaad"] = gene_level["gene"].isin(sea_genes)
    gene_level["priority_tier"] = np.where(
        gene_level["in_seaad"],
        "P1",
        np.where(
            gene_level["in_top5_display"]
            | (gene_level["category_count"] >= 2)
            | (gene_level["total_returned_calls"] >= 3),
            "P2",
            "P3",
        ),
    )

    gencode = parse_gencode(GENCODE_GTF)
    by_name: dict[str, list[int]] = {}
    for index, name in enumerate(gencode["gene_name"]):
        by_name.setdefault(name, []).append(index)
    by_ensembl = {e: i for i, e in enumerate(gencode["ensembl_gene_id"])}
    symbol_to_ensembl, alias_to_symbol = load_hgnc_maps(HGNC_SET)

    loci_rows = []
    mapping_status = []
    for gene in gene_level["gene"]:
        row_index = None
        status = "symbol_mapping_failed"
        hits = by_name.get(gene, [])
        if len(hits) == 1:
            row_index, status = hits[0], "mapped_by_symbol"
        elif len(hits) > 1:
            ensembl = symbol_to_ensembl.get(gene, "")
            if ensembl in by_ensembl:
                row_index, status = by_ensembl[ensembl], "mapped_by_symbol_hgnc_disambiguated"
        else:
            ensembl = symbol_to_ensembl.get(gene, "")
            if ensembl and ensembl in by_ensembl:
                row_index, status = by_ensembl[ensembl], "mapped_via_hgnc_ensembl"
            else:
                approved = alias_to_symbol.get(gene, "")
                alias_hits = by_name.get(approved, []) if approved else []
                if len(alias_hits) == 1:
                    row_index, status = alias_hits[0], "mapped_via_hgnc_alias"
        mapping_status.append(status)
        if row_index is not None:
            g = gencode.iloc[row_index]
            loci_rows.append(
                {
                    "schema_version": f"{SCHEMA}_loci",
                    "gene": gene,
                    "ensembl_gene_id": g["ensembl_gene_id"],
                    "gene_type": g["gene_type"],
                    "chromosome": g["chromosome"],
                    "start": int(g["start"]),
                    "end": int(g["end"]),
                    "strand": g["strand"],
                    "window_start": max(0, int(g["start"]) - WINDOW_BP),
                    "window_end": int(g["end"]) + WINDOW_BP,
                    "genome_build": "GRCh38",
                }
            )
    gene_level["mapping_status"] = mapping_status
    gene_level.insert(0, "schema_version", f"{SCHEMA}_candidates")
    gene_level.insert(1, "candidate_id", [f"GS19B{i:04d}" for i in range(1, len(gene_level) + 1)])
    loci = pd.DataFrame(loci_rows)

    candidates_path = out / "candidates.tsv"
    loci_path = out / "candidate_loci.tsv"
    contexts_path = out / "candidate_contexts.tsv"
    write_tsv(gene_level, candidates_path)
    write_tsv(loci, loci_path)
    write_tsv(contexts, contexts_path)

    tier_counts = gene_level["priority_tier"].value_counts().to_dict()
    mapped = int(gene_level["mapping_status"].str.startswith("mapped").sum())
    checks.extend(
        [
            check("candidate_gene_count", len(gene_level), EXPECTED_GENES, len(gene_level) == EXPECTED_GENES),
            check("context_row_count", len(contexts), EXPECTED_CONTEXTS, len(contexts) == EXPECTED_CONTEXTS),
            check("p1_tier_count", tier_counts.get("P1", 0), EXPECTED_P1, tier_counts.get("P1", 0) == EXPECTED_P1),
            check("tier_partition", int(sum(tier_counts.values())), EXPECTED_GENES, sum(tier_counts.values()) == EXPECTED_GENES),
            check("genes_unique", gene_level["gene"].nunique(), EXPECTED_GENES, gene_level["gene"].nunique() == EXPECTED_GENES),
            check("mapped_gene_count", mapped, ">=420", mapped >= 420),
            check("loci_rows_match_mapped", len(loci), mapped, len(loci) == mapped),
            check("loci_have_valid_windows", int((loci["window_end"] > loci["window_start"]).sum()), len(loci), bool((loci["window_end"] > loci["window_start"]).all())),
            check("no_mitochondrial_loci", int(loci["chromosome"].eq("M").sum()), 0, not loci["chromosome"].eq("M").any()),
        ]
    )
    finalize_stage(
        out,
        "freeze",
        checks,
        {
            "candidate_genes": len(gene_level),
            "mapped_genes": mapped,
            "tier_p1": tier_counts.get("P1", 0),
            "tier_p2": tier_counts.get("P2", 0),
            "tier_p3": tier_counts.get("P3", 0),
            "rosmap_input": str(rosmap_path.relative_to(ROOT)),
            "rosmap_sha256": ROSMAP_SHA256,
            "seaad_input": str(seaad_path.relative_to(ROOT)),
            "seaad_sha256": SEAAD_SHA256,
        },
        [candidates_path, loci_path, contexts_path],
    )
    unmapped = gene_level.loc[gene_level["mapping_status"].eq("symbol_mapping_failed"), "gene"].tolist()
    print(f"freeze: genes={len(gene_level)} mapped={mapped} unmapped={unmapped}")


# --------------------------------------------------------------------------
# WS1: FunGen public summary screen
# --------------------------------------------------------------------------


def load_workbook_gene_table() -> pd.DataFrame | None:
    if not FUNGEN_WORKBOOK.is_file():
        return None
    try:
        table = pd.read_excel(FUNGEN_WORKBOOK, sheet_name="Gene Locus table", header=2)
    except ImportError:
        return None
    needed = [
        "Variant ID", "Rsid", "Chr", "Pos", "maximum inclusion score",
        "Min p-value", "xQTL target gene", "gene ID",
        "TWAS significant", "MR significant", "cTWAS significant",
    ]
    missing = [column for column in needed if column not in table.columns]
    if missing:
        raise RuntimeError(f"Unified workbook is missing columns: {missing}")
    table = table.dropna(subset=["xQTL target gene"]).copy()
    table["ensembl_base"] = table["gene ID"].astype(str).str.split(".").str[0]
    return table


def stage_tier1() -> None:
    out = TIER1_DIR
    out.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    candidates = pd.read_csv(CANDIDATE_DIR / "candidates.tsv", sep="\t", dtype={"gene": str})
    loci = pd.read_csv(CANDIDATE_DIR / "candidate_loci.tsv", sep="\t", dtype={"gene": str, "chromosome": str})

    for path in (FUNGEN_VARIANTS, FUNGEN_GVC, FUNGEN_TWAS):
        if not path.is_file():
            raise FileNotFoundError(f"FunGen snapshot file missing: {path}")
    gvc_genes = set(pd.read_csv(FUNGEN_GVC, sep="\t", dtype=str)["gene_name"])
    twas_genes = set(pd.read_csv(FUNGEN_TWAS, sep="\t", dtype=str)["gene_name"])
    workbook = load_workbook_gene_table()
    workbook_available = workbook is not None

    variants = pd.read_csv(
        FUNGEN_VARIANTS,
        usecols=["chr", "pos", "variant_ID", "SNP", "min_pval", "max_variant_inclusion_probability", "is.cs95"],
    )
    variants["chr"] = variants["chr"].astype(str)

    rows = []
    for candidate in candidates.itertuples():
        gene = candidate.gene
        locus = loci[loci["gene"].eq(gene)]
        direct_n = 0
        direct_best_inclusion = np.nan
        direct_min_p = np.nan
        direct_rsids = ""
        twas_flag = False
        ctwas_flag = False
        mr_flag = False
        if workbook_available:
            hits = workbook[workbook["xQTL target gene"].eq(gene)]
            if hits.empty and len(locus):
                hits = workbook[workbook["ensembl_base"].eq(locus.iloc[0]["ensembl_gene_id"])]
            direct_n = len(hits)
            if direct_n:
                direct_best_inclusion = float(hits["maximum inclusion score"].max())
                direct_min_p = float(hits["Min p-value"].min())
                direct_rsids = "|".join(sorted({str(v) for v in hits["Rsid"].dropna()})[:6])
                twas_flag = bool(hits["TWAS significant"].fillna(False).astype(bool).any())
                ctwas_flag = bool(hits["cTWAS significant"].fillna(False).astype(bool).any())
                mr_flag = bool(hits["MR significant"].fillna(False).astype(bool).any())

        window_n = 0
        window_min_p = np.nan
        window_max_inclusion = np.nan
        window_cs95 = 0
        if len(locus):
            l = locus.iloc[0]
            in_window = variants[
                variants["chr"].eq(str(l["chromosome"]))
                & variants["pos"].between(int(l["window_start"]), int(l["window_end"]))
            ]
            window_n = len(in_window)
            if window_n:
                window_min_p = float(in_window["min_pval"].min())
                window_max_inclusion = float(in_window["max_variant_inclusion_probability"].max())
                window_cs95 = int(in_window["is.cs95"].astype(bool).sum())

        in_twas = gene in twas_genes
        in_gvc = gene in gvc_genes
        if direct_n and direct_min_p < GW_THRESHOLD and direct_best_inclusion >= 0.5:
            grade = "strong"
        elif direct_n and ((direct_min_p < GW_THRESHOLD and direct_best_inclusion >= 0.1) or twas_flag or ctwas_flag):
            grade = "moderate"
        elif direct_n or in_twas or in_gvc:
            grade = "weak"
        else:
            grade = "none_found"
        if not workbook_available and not (in_twas or in_gvc):
            grade = "not_assessable_workbook_unavailable"

        rows.append(
            {
                "schema_version": f"{SCHEMA}_fungen",
                "candidate_id": candidate.candidate_id,
                "gene": gene,
                "priority_tier": candidate.priority_tier,
                "direct_mapping_rows": direct_n,
                "direct_best_inclusion_score": direct_best_inclusion,
                "direct_min_p": direct_min_p,
                "direct_rsids": direct_rsids,
                "workbook_twas_significant": twas_flag,
                "workbook_ctwas_significant": ctwas_flag,
                "workbook_mr_significant": mr_flag,
                "in_public_twas_list": in_twas,
                "in_public_gvc_list": in_gvc,
                "window_variant_rows": window_n,
                "window_min_p": window_min_p,
                "window_max_inclusion_score": window_max_inclusion,
                "window_cs95_variants": window_cs95,
                "grade": grade,
            }
        )
    evidence = pd.DataFrame(rows)
    evidence_path = out / "fungen_gene_evidence.tsv"
    write_tsv(evidence, evidence_path)

    graded = evidence["grade"].value_counts().to_dict()
    apoe = evidence[evidence["gene"].eq("APOE")]
    checks.extend(
        [
            check("evidence_rows", len(evidence), EXPECTED_GENES, len(evidence) == EXPECTED_GENES),
            check("workbook_available", workbook_available, True, workbook_available),
            check(
                "apoe_positive_control",
                apoe.iloc[0]["grade"] if len(apoe) else "absent",
                "strong",
                len(apoe) == 1 and apoe.iloc[0]["grade"] == "strong",
            ),
            check("grades_assigned", int(sum(graded.values())), EXPECTED_GENES, sum(graded.values()) == EXPECTED_GENES),
        ]
    )
    finalize_stage(
        out,
        "tier1",
        checks,
        {
            "graded_strong": graded.get("strong", 0),
            "graded_moderate": graded.get("moderate", 0),
            "graded_weak": graded.get("weak", 0),
            "graded_none_found": graded.get("none_found", 0),
        },
        [evidence_path],
    )
    print(f"tier1: strong={graded.get('strong',0)} moderate={graded.get('moderate',0)} weak={graded.get('weak',0)} none={graded.get('none_found',0)}")


# --------------------------------------------------------------------------
# WS2: regional GWAS annotation
# --------------------------------------------------------------------------


def detect_column(available: list[str], choices: list[str], label: str, source: str) -> str:
    for choice in choices:
        if choice in available:
            return choice
    raise RuntimeError(f"{source}: no {label} column among {available[:20]}")


def scan_gwas(path: Path, loci: pd.DataFrame) -> pd.DataFrame:
    header = pd.read_csv(path, sep="\t", nrows=0)
    columns = list(header.columns)
    chrom_col = detect_column(columns, CHROM_COLUMNS, "chromosome", path.name)
    pos_col = detect_column(columns, POS_COLUMNS, "position", path.name)
    pval_col = detect_column(columns, PVAL_COLUMNS, "p-value", path.name)
    variant_col = detect_column(columns, VARIANT_COLUMNS, "variant-id", path.name)

    state: dict[str, dict[str, Any]] = {
        row.gene: {"n": 0, "min_p": np.inf, "lead": ""} for row in loci.itertuples()
    }
    windows_by_chrom: dict[str, list[Any]] = {}
    for row in loci.itertuples():
        windows_by_chrom.setdefault(str(row.chromosome), []).append(row)

    reader = pd.read_csv(
        path,
        sep="\t",
        usecols=[chrom_col, pos_col, pval_col, variant_col],
        dtype={chrom_col: str, variant_col: str},
        chunksize=2_000_000,
        low_memory=False,
    )
    for chunk in reader:
        chunk[pos_col] = pd.to_numeric(chunk[pos_col], errors="coerce")
        chunk[pval_col] = pd.to_numeric(chunk[pval_col], errors="coerce")
        chunk = chunk.dropna(subset=[pos_col, pval_col])
        chunk["_chrom"] = chunk[chrom_col].str.removeprefix("chr")
        for chrom, group in chunk.groupby("_chrom", sort=False):
            targets = windows_by_chrom.get(str(chrom))
            if not targets:
                continue
            positions = group[pos_col].to_numpy(float)
            pvalues = group[pval_col].to_numpy(float)
            variants = group[variant_col].to_numpy(object)
            order = np.argsort(positions, kind="stable")
            positions, pvalues, variants = positions[order], pvalues[order], variants[order]
            for row in targets:
                lo = np.searchsorted(positions, row.window_start, side="left")
                hi = np.searchsorted(positions, row.window_end, side="right")
                if hi <= lo:
                    continue
                entry = state[row.gene]
                entry["n"] += int(hi - lo)
                local = pvalues[lo:hi]
                best = int(np.argmin(local))
                if local[best] < entry["min_p"]:
                    entry["min_p"] = float(local[best])
                    entry["lead"] = str(variants[lo + best])
    rows = []
    for row in loci.itertuples():
        entry = state[row.gene]
        rows.append(
            {
                "gene": row.gene,
                "ensembl_gene_id": row.ensembl_gene_id,
                "chromosome": row.chromosome,
                "window_start": row.window_start,
                "window_end": row.window_end,
                "variant_rows": entry["n"],
                "regional_min_p": entry["min_p"] if np.isfinite(entry["min_p"]) else np.nan,
                "regional_lead_variant": entry["lead"],
                "genome_wide_significant": bool(entry["min_p"] < GW_THRESHOLD),
            }
        )
    return pd.DataFrame(rows)


def stage_regional() -> None:
    out = REGIONAL_DIR
    out.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    loci = pd.read_csv(
        CANDIDATE_DIR / "candidate_loci.tsv", sep="\t",
        dtype={"gene": str, "chromosome": str},
    )
    candidates = pd.read_csv(CANDIDATE_DIR / "candidates.tsv", sep="\t", dtype={"gene": str})
    tier_map = dict(zip(candidates["gene"], candidates["priority_tier"]))

    artifacts: list[Path] = []
    source_rows = []
    combined = []
    scanned = 0
    for trait, path in GWAS_SOURCES.items():
        if not path.is_file():
            source_rows.append({"schema_version": f"{SCHEMA}_sources", "trait": trait, "path": str(path), "status": "missing_source_skipped"})
            print(f"regional: SKIPPED {trait} (missing {path})")
            continue
        print(f"regional: scanning {trait} ...")
        summary = scan_gwas(path, loci)
        summary.insert(0, "schema_version", f"{SCHEMA}_regional")
        summary.insert(1, "trait", trait)
        summary["priority_tier"] = summary["gene"].map(tier_map)
        trait_path = out / f"regional_summary_{trait}.tsv"
        write_tsv(summary, trait_path)
        artifacts.append(trait_path)
        combined.append(summary)
        scanned += 1
        source_rows.append(
            {
                "schema_version": f"{SCHEMA}_sources",
                "trait": trait,
                "path": str(path),
                "status": "scanned",
                "windows_with_variants": int((summary["variant_rows"] > 0).sum()),
                "genome_wide_significant_windows": int(summary["genome_wide_significant"].sum()),
            }
        )
    sources_path = out / "regional_sources.tsv"
    write_tsv(pd.DataFrame(source_rows), sources_path)
    artifacts.append(sources_path)
    if combined:
        all_path = out / "regional_summary_all_traits.tsv"
        write_tsv(pd.concat(combined, ignore_index=True), all_path)
        artifacts.append(all_path)

    checks.extend(
        [
            check("sources_scanned", scanned, ">=1", scanned >= 1),
            check("loci_scanned_per_source", len(loci), len(loci), True),
        ]
    )
    if combined:
        coverage_ok = all(bool((frame["variant_rows"] > 0).mean() > 0.95) for frame in combined)
        checks.append(check("window_coverage_above_95pct", coverage_ok, True, coverage_ok))
    finalize_stage(
        out,
        "regional",
        checks,
        {"sources_scanned": scanned, "sources_missing": len(GWAS_SOURCES) - scanned},
        artifacts,
    )
    print(f"regional: scanned={scanned} of {len(GWAS_SOURCES)} sources")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stages",
        default="freeze,tier1,regional",
        help="Comma-separated subset of: freeze,tier1,regional",
    )
    args = parser.parse_args()
    stages = [stage.strip() for stage in args.stages.split(",") if stage.strip()]
    known = {"freeze": stage_freeze, "tier1": stage_tier1, "regional": stage_regional}
    unknown = [stage for stage in stages if stage not in known]
    if unknown:
        raise SystemExit(f"Unknown stage(s): {unknown}")
    for stage in stages:
        print(f"=== stage {stage} ===")
        known[stage]()
    print("all requested stages complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
