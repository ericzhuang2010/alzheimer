#!/usr/bin/env python3
"""Validate and freeze the Phase 21 ROSMAP minimum-three broad DEG subrelease."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "config" / "phase21_rosmap_broad_deg_min3.yml"
DEFAULT_OUTPUT = ROOT / "results" / "minerva_production" / "21_harmonized_broad_kda_inputs" / "00_source_deg_min3"
PHASE08 = ROOT / "results" / "minerva_production" / "08_deg_broad"
TRUE_VALUES = {"true", "t", "1", "yes"}
PRIMARY_NUMERIC_TOLERANCES = {
    "logFC": 1e-8,
    "logCPM": 1e-10,
    "F": 1e-7,
    "p_value": 1e-6,
    "fdr_bh_within_contrast": 1e-6,
    "detection_rate_required_groups": 1e-12,
    "donors_ad": 0.0,
    "donors_nci": 0.0,
    "nuclei_ad": 0.0,
    "nuclei_nci": 0.0,
    "model_samples": 0.0,
    "model_donors": 0.0,
}
DERIVED_DISPLAY_COLUMNS = ["standard_error", "ci95_low", "ci95_high"]
INFERENCE_IDENTITY_COLUMNS = [
    "direction",
    "strict_deg",
    "relaxed_deg",
    "exploratory_deg",
    "is_mitocarta3",
    "mito_tier",
    "symbol_hgnc_current",
]
IDENTITY_REGRESSION_COLUMNS = [
    "gene",
    "contrast_id",
    "broad_cell_type",
    "group_id",
    "sex",
    "apoe_group",
    "numerator",
    "denominator",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def truth(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        fail(f"Required file is missing: {path}")
    return pd.read_csv(path, sep="\t", keep_default_na=False, low_memory=False)


def atomic_tsv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, sep="\t", index=False, na_rep="NA")
    os.replace(temporary, path)


def atomic_copy(source: Path, target: Path) -> None:
    temporary = target.with_name(f".{target.name}.tmp.{os.getpid()}")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def git_revision() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def support_columns(frame: pd.DataFrame) -> pd.DataFrame:
    answer = frame.copy()
    minimum = answer[["donors_ad", "donors_nci"]].min(axis=1).astype(int)
    low = answer["contrast_id"].isin(
        [
            "Vasculature_cells::AD_vs_NCI__Female__e2",
            "Vasculature_cells::AD_vs_NCI__Male__e2",
        ]
    )
    confirmatory = minimum.ge(10)
    answer["exploratory_min3_support"] = low
    answer["confirmatory_support"] = confirmatory
    answer["support_tier"] = "standard_nonconfirmatory_support"
    answer.loc[confirmatory, "support_tier"] = "confirmatory_support"
    answer.loc[low, "support_tier"] = "exploratory_min3_support"
    return answer


def main() -> int:
    args = parse_args()
    config_path = args.config.resolve(strict=True)
    output = args.output.resolve(strict=True)
    if output != DEFAULT_OUTPUT.resolve():
        fail("Phase 21 source output must use the frozen repository path")

    wrapper_products = [
        "config_snapshot.yml",
        "input_authority.tsv",
        "contrast_manifest.tsv",
        "contrast_status.tsv",
        "model_diagnostics.tsv",
        "phase08_regression_checks.tsv",
        "checks.tsv",
        "artifacts.tsv",
        "status.tsv",
    ]
    existing = [name for name in wrapper_products if (output / name).exists()]
    if (existing or (output / "by_contrast").exists()) and not args.refresh:
        fail(f"Refusing to overwrite Phase 21 source wrapper products: {existing}")
    if args.refresh and (set(existing) != set(wrapper_products) or not (output / "by_contrast").is_dir()):
        fail("Cannot refresh an incomplete Phase 21 source wrapper")

    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    with (ROOT / "config" / "phase08_broad_deg.yml").open(encoding="utf-8") as handle:
        old_config = yaml.safe_load(handle)

    raw_status = read_tsv(output / "broad_deg_status.tsv")
    raw_checks = read_tsv(output / "broad_deg_checks.tsv")
    raw_contrasts = read_tsv(output / "broad_deg_contrast_status.tsv")
    raw_manifest = read_tsv(output / "00_inputs" / "broad_deg_contrast_manifest.tsv")
    raw_diagnostics = read_tsv(output / "broad_deg_model_diagnostics.tsv")
    old_status = read_tsv(PHASE08 / "broad_deg_status.tsv")
    old_contrasts = read_tsv(PHASE08 / "broad_deg_contrast_status.tsv")

    new_analysis = dict(config["analysis"])
    old_analysis = dict(old_config["analysis"])
    for field in ["analysis_id", "title", "minimum_donors_per_arm"]:
        new_analysis.pop(field, None)
        old_analysis.pop(field, None)
    config_science_match = (
        new_analysis == old_analysis
        and config["thresholds"] == old_config["thresholds"]
        and config["composition_sensitivity"] == old_config["composition_sensitivity"]
        and config["inputs"] == old_config["inputs"]
        and config["schemas"] == old_config["schemas"]
        and int(config["analysis"]["minimum_donors_per_arm"]) == 3
        and int(config["analysis"]["minimum_nuclei_primary"]) == 20
        and int(config["analysis"]["confirmatory_donors_per_arm"]) == 10
    )

    complete = raw_contrasts["terminal_status"].eq("validated_complete")
    old_complete = old_contrasts["terminal_status"].eq("validated_complete")
    shared_ids = sorted(old_contrasts.loc[old_complete, "contrast_id"].tolist())
    regression_rows: list[dict[str, Any]] = []
    for contrast_id in shared_ids:
        old_row = old_contrasts.loc[old_contrasts["contrast_id"].eq(contrast_id)].iloc[0]
        new_row = raw_contrasts.loc[raw_contrasts["contrast_id"].eq(contrast_id)].iloc[0]
        filename = f"{old_row['broad_cell_type']}__{old_row['group_id']}.broad_deg.tsv.gz"
        old_result = read_tsv(PHASE08 / "05_by_contrast" / filename)
        new_result = read_tsv(output / "05_by_contrast" / filename)
        required = (
            IDENTITY_REGRESSION_COLUMNS
            + list(PRIMARY_NUMERIC_TOLERANCES)
            + DERIVED_DISPLAY_COLUMNS
            + INFERENCE_IDENTITY_COLUMNS
        )
        missing = [column for column in required if column not in old_result or column not in new_result]
        if missing:
            fail(f"Regression columns missing for {contrast_id}: {missing}")
        old_result = old_result.sort_values("gene").reset_index(drop=True)
        new_result = new_result.sort_values("gene").reset_index(drop=True)
        identity_match = len(old_result) == len(new_result)
        if identity_match:
            identity_match = all(
                old_result[column].astype(str).equals(new_result[column].astype(str))
                for column in IDENTITY_REGRESSION_COLUMNS
            )
        primary_deltas: dict[str, float] = {}
        numeric_match = identity_match
        if identity_match and len(old_result):
            for column, tolerance in PRIMARY_NUMERIC_TOLERANCES.items():
                old_values = pd.to_numeric(old_result[column], errors="coerce")
                new_values = pd.to_numeric(new_result[column], errors="coerce")
                same_na = old_values.isna().equals(new_values.isna())
                finite = old_values.notna() & new_values.notna()
                delta = float((old_values[finite] - new_values[finite]).abs().max()) if finite.any() else 0.0
                primary_deltas[column] = delta
                numeric_match = numeric_match and same_na and delta <= tolerance
        inference_match = identity_match and all(
            old_result[column].astype(str).equals(new_result[column].astype(str))
            for column in INFERENCE_IDENTITY_COLUMNS
        )
        derived_deltas: dict[str, float] = {}
        if identity_match and len(old_result):
            for column in DERIVED_DISPLAY_COLUMNS:
                old_values = pd.to_numeric(old_result[column], errors="coerce")
                new_values = pd.to_numeric(new_result[column], errors="coerce")
                finite = old_values.notna() & new_values.notna()
                derived_deltas[column] = (
                    float((old_values[finite] - new_values[finite]).abs().max())
                    if finite.any() else 0.0
                )
        regression_rows.append(
            {
                "schema_version": "phase21_phase08_regression_checks_v1",
                "contrast_id": contrast_id,
                "old_result_path": relative(PHASE08 / "05_by_contrast" / filename),
                "new_result_path": relative(output / "05_by_contrast" / filename),
                "old_rows": len(old_result),
                "new_rows": len(new_result),
                "gene_and_coefficient_identity_match": identity_match,
                "inference_and_annotation_identity_match": inference_match,
                "maximum_logfc_absolute_delta": primary_deltas.get("logFC", float("nan")),
                "maximum_logcpm_absolute_delta": primary_deltas.get("logCPM", float("nan")),
                "maximum_f_absolute_delta": primary_deltas.get("F", float("nan")),
                "maximum_p_value_absolute_delta": primary_deltas.get("p_value", float("nan")),
                "maximum_within_fdr_absolute_delta": primary_deltas.get("fdr_bh_within_contrast", float("nan")),
                "maximum_detection_rate_absolute_delta": primary_deltas.get("detection_rate_required_groups", float("nan")),
                "maximum_derived_standard_error_absolute_delta": derived_deltas.get("standard_error", float("nan")),
                "maximum_derived_ci_absolute_delta": max(
                    derived_deltas.get("ci95_low", 0.0), derived_deltas.get("ci95_high", 0.0)
                ),
                "cross_platform_tolerance_profile": "logFC=1e-8;logCPM=1e-10;F=1e-7;p=1e-6;withinFDR=1e-6;detection=1e-12;counts=exact",
                "passed": identity_match and inference_match and numeric_match,
            }
        )
    regression = pd.DataFrame(regression_rows)

    contrast_status = support_columns(raw_contrasts)
    manifest = support_columns(raw_manifest)
    expected_low = {
        "Vasculature_cells::AD_vs_NCI__Female__e2": (3, 10),
        "Vasculature_cells::AD_vs_NCI__Male__e2": (4, 3),
    }
    observed_low = {
        row.contrast_id: (int(row.donors_ad), int(row.donors_nci))
        for row in contrast_status.loc[contrast_status["exploratory_min3_support"]].itertuples(index=False)
    }

    checks_data = [
        ("phase08_reference_validated", len(old_status) == 1 and old_status.iloc[0]["validation_status"] == "validated_complete", old_status.iloc[0]["validation_status"], "validated_complete"),
        ("minimum3_release_validated", len(raw_status) == 1 and raw_status.iloc[0]["validation_status"] == "validated_complete", raw_status.iloc[0]["validation_status"], "validated_complete"),
        ("minimum3_release_checks_passed", raw_checks["passed"].map(truth).all(), int((~raw_checks["passed"].map(truth)).sum()), 0),
        ("scientific_configuration_frozen_except_identity_and_donor_gate", config_science_match, config_science_match, True),
        ("structural_contrast_count", len(raw_contrasts) == 42, len(raw_contrasts), 42),
        ("completed_contrast_count", int(complete.sum()) == 42, int(complete.sum()), 42),
        ("not_estimable_contrast_count", int(raw_contrasts["terminal_status"].eq("not_estimable").sum()) == 0, int(raw_contrasts["terminal_status"].eq("not_estimable").sum()), 0),
        ("shared_phase08_contrast_count", len(shared_ids) == 40, len(shared_ids), 40),
        ("shared_phase08_cross_platform_numerical_regression", len(regression) == 40 and regression["passed"].map(truth).all(), int(regression["passed"].map(truth).sum()), 40),
        ("new_low_support_contrast_counts", observed_low == expected_low, str(observed_low), str(expected_low)),
        ("exactly_two_exploratory_min3_support", int(contrast_status["exploratory_min3_support"].sum()) == 2, int(contrast_status["exploratory_min3_support"].sum()), 2),
        ("confirmatory_threshold_frozen_at_10", (contrast_status["confirmatory_support"] == contrast_status[["donors_ad", "donors_nci"]].min(axis=1).ge(10)).all(), 10, 10),
        ("model_diagnostic_count", len(raw_diagnostics) == 7, len(raw_diagnostics), 7),
        ("coefficient_direction", set(raw_manifest["numerator"]) == {"AD"} and set(raw_manifest["denominator"]) == {"NCI"}, "AD_minus_NCI", "AD_minus_NCI"),
    ]
    checks = pd.DataFrame(
        [
            {
                "schema_version": "phase21_rosmap_broad_deg_min3_checks_v1",
                "check": name,
                "passed": bool(passed),
                "observed": observed,
                "expected": expected,
            }
            for name, passed, observed, expected in checks_data
        ]
    )
    failed = checks.loc[~checks["passed"], "check"].tolist()
    if failed:
        fail(f"Blocking Phase 21 minimum-three checks failed: {', '.join(failed)}")

    by_contrast = output / "by_contrast"
    if not args.refresh:
        by_contrast.mkdir()
        for source in sorted((output / "05_by_contrast").glob("*.broad_deg.tsv.gz")):
            atomic_copy(source, by_contrast / source.name)
    if len(list(by_contrast.glob("*.broad_deg.tsv.gz"))) != 42:
        fail("Phase 21 by_contrast alias does not contain 42 result sets")

    atomic_copy(config_path, output / "config_snapshot.yml")
    atomic_tsv(manifest, output / "contrast_manifest.tsv")
    atomic_tsv(contrast_status, output / "contrast_status.tsv")
    atomic_tsv(raw_diagnostics, output / "model_diagnostics.tsv")
    atomic_tsv(regression, output / "phase08_regression_checks.tsv")
    atomic_tsv(checks, output / "checks.tsv")

    authority_paths: list[tuple[str, Path]] = [
        ("phase21_deg_configuration", config_path),
        ("phase08_deg_configuration_reference", ROOT / "config" / "phase08_broad_deg.yml"),
        ("phase08_deg_status_reference", PHASE08 / "broad_deg_status.tsv"),
        ("phase08_contrast_status_reference", PHASE08 / "broad_deg_contrast_status.tsv"),
        ("phase08_combined_results_reference", PHASE08 / "broad_deg_results.tsv.gz"),
        ("rosmap_gene_annotation", ROOT / config["profiles"]["phase21_min3"]["annotation_master"]),
        ("rosmap_gene_annotation_status", ROOT / config["profiles"]["phase21_min3"]["annotation_status"]),
        ("broad_deg_model_script", ROOT / "scripts" / "08_run_broad_pseudobulk_de.R"),
        ("broad_deg_sensitivity_script", ROOT / "scripts" / "08_run_broad_deg_composition_sensitivity.R"),
        ("broad_deg_finalize_script", ROOT / "scripts" / "08_finalize_broad_deg.R"),
        ("broad_deg_validate_script", ROOT / "scripts" / "08_validate_broad_deg.R"),
        ("broad_deg_helper", ROOT / "scripts" / "lib" / "phase08_broad_deg_common.R"),
        ("phase21_wrapper_script", Path(__file__).resolve()),
        ("harmonized_kda_configuration", ROOT / "config" / "harmonized_broad_kda.yml"),
        ("harmonized_kda_prepare_script", ROOT / "scripts" / "analysis" / "kda" / "prepare_harmonized_broad_kda_inputs.py"),
        ("harmonized_kda_run_script", ROOT / "scripts" / "analysis" / "kda" / "run_harmonized_broad_kda.R"),
        ("fkda_source", ROOT / "scripts" / "NetWeaver" / "fKDA.R"),
        ("phase08_pseudobulk_status", PHASE08 / "02_broad_pseudobulk" / "broad_pseudobulk_stage_status.tsv"),
    ]
    for bundle in sorted((PHASE08 / "02_broad_pseudobulk").glob("*.broad_pseudobulk_counts.rds")):
        authority_paths.append((f"phase08_pseudobulk::{bundle.stem}", bundle))
    for result in sorted((PHASE08 / "05_by_contrast").glob("*.broad_deg.tsv.gz")):
        authority_paths.append((f"phase08_result_reference::{result.name}", result))
    authority = pd.DataFrame(
        [
            {
                "schema_version": "phase21_rosmap_broad_deg_min3_input_authority_v1",
                "role": role,
                "path": relative(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for role, path in authority_paths
        ]
    )
    atomic_tsv(authority, output / "input_authority.tsv")

    artifact_files = sorted(
        path for path in output.rglob("*")
        if path.is_file() and path.name not in {"artifacts.tsv", "status.tsv"}
    )
    artifacts = pd.DataFrame(
        [
            {
                "schema_version": "phase21_rosmap_broad_deg_min3_artifacts_v1",
                "artifact_order": index,
                "path": relative(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for index, path in enumerate(artifact_files, start=1)
        ]
    )
    atomic_tsv(artifacts, output / "artifacts.tsv")
    status = pd.DataFrame(
        [
            {
                "schema_version": "phase21_rosmap_broad_deg_min3_status_v1",
                "phase": "Phase21_source_deg_min3",
                "cohort": "rosmap",
                "validation_status": "validated_complete",
                "failed_checks": 0,
                "structural_contrasts": 42,
                "completed_contrasts": 42,
                "not_estimable_contrasts": 0,
                "phase08_regression_contrasts": 40,
                "phase08_regression_passed": int(regression["passed"].map(truth).sum()),
                "exploratory_min3_support_contrasts": 2,
                "confirmatory_support_contrasts": int(contrast_status["confirmatory_support"].sum()),
                "minimum_nuclei_per_donor_broad_profile": 20,
                "minimum_donors_per_arm": 3,
                "confirmatory_donors_per_arm": 10,
                "config_sha256": sha256_file(config_path),
                "git_revision": git_revision(),
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    atomic_tsv(status, output / "status.tsv")
    print(f"Phase21 source validated_complete: {relative(output)}")
    print("Contrasts completed: 42; Phase08 regressions passed: 40; exploratory_min3_support: 2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
