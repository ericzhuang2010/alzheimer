from __future__ import annotations

import gzip
import hashlib
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "minerva_production"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str)


def config() -> dict:
    return yaml.safe_load((ROOT / "config" / "phase19b_genetic_support.yml").read_text())


def test_historical_phase19_bundles_are_renamed_not_deleted() -> None:
    names = [
        "19_genetic_support_tier1",
        "19_genetic_support_tier2_regional",
        "19_genetic_support_tier2_recovery",
        "19_genetic_support_endophenotype_gwas_qtl_extension",
        "19_genetic_support_opc_rps15_public_recovery",
    ]
    for name in names:
        assert not (RESULTS / name).exists()
        deprecated = RESULTS / f"{name} (deprecated)"
        assert deprecated.is_dir()
        assert any(deprecated.iterdir())


def test_current_candidate_freeze_is_phase20_combo_scope() -> None:
    cfg = config()["analysis"]
    candidates = read_tsv(RESULTS / "19b_genetic_support_candidates" / "candidates.tsv")
    contexts = read_tsv(RESULTS / "19b_genetic_support_candidates" / "candidate_contexts.tsv")
    source = RESULTS / "20_sex_apoe_kda_combo" / "combo_key_drivers_by_category.tsv"
    assert len(candidates) == cfg["expected_genes"]
    assert candidates["gene"].nunique() == cfg["expected_genes"]
    assert candidates["mapping_status"].ne("symbol_mapping_failed").sum() == cfg["expected_mapped_genes"]
    assert len(contexts) == cfg["expected_contexts"]
    assert sha256(source) == "ba506a24d5fc925d732a7a9537b5c0201bf415b6848096068807db744e5498fd"


def test_phase19b_magma_contract() -> None:
    cfg = config()["analysis"]
    root = RESULTS / "19b_genetic_support_magma"
    result = read_tsv(root / "magma_candidate_results.tsv")
    status = read_tsv(root / "magma_status.tsv").iloc[0]
    assert len(result) == cfg["magma_candidate_tests"]
    assert result["gene"].nunique() == cfg["expected_genes"]
    assert result["trait_id"].nunique() == cfg["traits"]
    assert result["candidate_threshold"].astype(float).eq(cfg["magma_candidate_p"]).all()
    assert status["validation_status"] == "validated_complete"


def test_phase19b_qtl_and_coloc_contracts() -> None:
    cfg = config()["analysis"]
    qtl_root = RESULTS / "19b_genetic_support_qtl"
    coloc_root = RESULTS / "19b_genetic_support_coloc"
    coverage = read_tsv(qtl_root / "qtl_coverage.tsv")
    decisions = read_tsv(coloc_root / "coloc_route_decisions.tsv")
    evidence = read_tsv(coloc_root / "final_gene_evidence.tsv")

    expected_qtl = cfg["expected_followup_contexts"] * len(cfg["qtl_modalities"])
    assert len(coverage) == expected_qtl
    assert coverage["gene"].nunique() == cfg["expected_followup_genes"]
    assert coverage["sex_apoe_match"].eq("unavailable_public_source_not_stratified").all()
    assert len(decisions) == expected_qtl * cfg["traits"]
    assert decisions["valid_h0_h4_result"].str.upper().eq("FALSE").all()
    assert len(evidence) == cfg["expected_genes"]
    assert not evidence["gene_level_support_basis"].eq("regional_GWAS").any()

    with gzip.open(coloc_root / "colocalization.tsv.gz", "rt") as handle:
        lines = handle.readlines()
    assert len(lines) == 1
    assert "\th4\t" in lines[0]


def test_phase19b_compact_artifact_hashes() -> None:
    for stage in ("magma", "qtl", "coloc"):
        root = RESULTS / f"19b_genetic_support_{stage}"
        artifacts = read_tsv(root / f"{stage}_artifacts.tsv")
        for row in artifacts.itertuples(index=False):
            path = ROOT / row.path
            assert path.is_file()
            assert path.stat().st_size == int(row.bytes)
            assert sha256(path) == row.sha256
