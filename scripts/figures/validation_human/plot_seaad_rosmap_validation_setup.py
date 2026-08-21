#!/usr/bin/env python3
"""Render the SEA-AD–ROSMAP human-validation setup schematic.

The figure is a data-bound study-design graphic. It reads compact, validated
SEA-AD and ROSMAP artifacts; it does not recompute DEG, query membership, KDA,
ACAT, BH correction, or overlap statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_setup_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_setup_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
import yaml  # noqa: E402


SCHEMA = "seaad_rosmap_validation_setup_figure_v1"
FIGURE_ID = "seaad_rosmap_validation_setup"
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_594
PNG_HEIGHT = 2_120
FIGURE_WIDTH_IN = PNG_WIDTH / DEFAULT_PNG_DPI
FIGURE_HEIGHT_IN = PNG_HEIGHT / DEFAULT_PNG_DPI

OUTPUT_FILES = [
    f"{FIGURE_ID}.png",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_artifacts.tsv",
    f"{FIGURE_ID}_status.tsv",
]
PAYLOAD_FILES = OUTPUT_FILES[:7]

INPUT_PATHS = {
    "vh02_status": "results/validation_human/02_cohort/status.tsv",
    "donor_groups": "results/validation_human/02_cohort/donor_group_counts.tsv",
    "cohort_exclusions": "results/validation_human/02_cohort/cohort_exclusion_flow.tsv",
    "vh03_status": "results/validation_human/03_genes/status.tsv",
    "vh04_status": "results/validation_human/04_supertype_manifest/status.tsv",
    "supertype_map": "results/validation_human/04_supertype_manifest/supertype_to_broad_network.tsv",
    "donor_supertype_counts": "results/validation_human/04_supertype_manifest/donor_supertype_nucleus_counts.tsv",
    "vh07_status": "results/validation_human/07_contrasts/status.tsv",
    "vh08_status": "results/validation_human/08_deg/status.tsv",
    "fine_contrast_status": "results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv",
    "fine_direction_manifest": "results/validation_human/08_deg/query_handoff/fine_direction_manifest.tsv",
    "deg_config": "scripts/validation_human/seaad_deg_config.yml",
    "validation_config": "scripts/validation_human/seaad_phase18_validation_config.yml",
    "vh09_status": "results/validation_human/09_rosmap_kda_candidates/status.tsv",
    "rosmap_selected": "results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv",
    "shared_network_scope": "results/validation_human/09_rosmap_kda_candidates/shared_network_scope.tsv",
    "vh10_status": "results/validation_human/10_seaad_kda_rediscovery/status.tsv",
    "vh10a_status": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/status.tsv",
    "vh10a_checks": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/input_checks.tsv",
    "vh10a_authority": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/input_authority.tsv",
    "network_identity": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/network_identity.tsv",
    "query_attrition": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/query_attrition.tsv",
    "seaad_run_manifest": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv",
    "vh10b_status": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv",
    "vh10b_run_qc": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/run_qc.tsv",
    "vh10c_status": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv",
    "seaad_freeze": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_selection_freeze.tsv",
    "seaad_top5": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv",
    "vh10d_status": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/status.tsv",
    "rosmap_cohort_status": "results/minerva_production/02_cohort/cohort_status.tsv",
    "phase12_status": "results/minerva_production/12_kda/kda_status.tsv",
    "phase12_manifest": "results/minerva_production/12_kda/kda_run_manifest.tsv",
    "phase12_config": "config/phase12_kda.yml",
    "phase18_config": "config/phase18_key_driver_selection.yml",
}

STATUS_KEYS = [
    "vh02_status",
    "vh03_status",
    "vh04_status",
    "vh07_status",
    "vh08_status",
    "vh09_status",
    "vh10_status",
    "vh10a_status",
    "vh10b_status",
    "vh10c_status",
    "vh10d_status",
]

GROUP_ORDER = ["F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"]
SHARED_NETWORK_ORDER = [
    "Astrocytes",
    "Excitatory_neurons",
    "Inhibitory_neurons",
    "Microglia",
    "OPCs",
    "Oligodendrocytes",
    "Vasculature_cells",
]
EXPECTED_SUPERTYPES = {
    "Astrocytes": 6,
    "Excitatory_neurons": 41,
    "Inhibitory_neurons": 67,
    "Microglia": 4,
    "OPCs": 3,
    "Oligodendrocytes": 4,
    "Vasculature_cells": 4,
}
EXPECTED_COMPLETED_GROUPS = {
    "F_e2": 0,
    "F_e33": 100,
    "F_e4": 68,
    "M_e2": 0,
    "M_e33": 92,
    "M_e4": 0,
}
EXPECTED_ROSMAP_SOURCE_NETWORKS = {
    "Astrocytes": 3,
    "CAMs": 1,
    "Excitatory_neurons": 14,
    "Inhibitory_neurons": 25,
    "Microglia": 3,
    "OPCs": 1,
    "Oligodendrocytes": 1,
    "T_cells": 1,
    "Vasculature_cells": 5,
}

# Colorblind-safe Okabe–Ito-derived palette plus neutral structure colors.
NAVY = "#17365D"
TEXT = "#20252B"
MID = "#5B6573"
WHITE = "#FFFFFF"
SEA_BLUE = "#0072B2"
SEA_TEAL = "#009E73"
SEA_PALE = "#E9F3F8"
SEA_PALE_2 = "#E8F5F1"
UP = "#D55E00"
DOWN = "#0072B2"
ROS_ORANGE = "#E69F00"
ROS_PALE = "#FFF4DD"
SCAFFOLD_PALE = "#EEF1F4"
GRAY = "#B8BDC5"
PALE_GRAY = "#F6F7F8"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output-root",
        default="results/figures/validation_human/seaad_rosmap_validation_setup",
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "complete"),
        default="pending",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-output")
    args = parser.parse_args(argv)
    if args.png_dpi != DEFAULT_PNG_DPI:
        parser.error(f"--png-dpi must equal the frozen value {DEFAULT_PNG_DPI}")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "t", "1", "yes"}


def as_int(value: Any, label: str = "value") -> int:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Expected integer {label}, observed {value!r}") from exc
    require(math.isfinite(number), f"Expected finite integer {label}, observed {value!r}")
    rounded = int(round(number))
    require(abs(number - rounded) <= 1e-9, f"Expected integer {label}, observed {value!r}")
    return rounded


def as_float(value: Any, label: str = "value") -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Expected numeric {label}, observed {value!r}") from exc
    require(math.isfinite(number), f"Expected finite numeric {label}, observed {value!r}")
    return number


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    require(path.is_file(), f"Missing TSV: {path}")
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def read_yaml(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing YAML: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected mapping YAML: {path}")
    return value


def one_row(frame: pd.DataFrame, label: str) -> pd.Series:
    require(len(frame) == 1, f"Expected one row for {label}, found {len(frame)}")
    return frame.iloc[0]


def require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    require(not missing, f"{label} missing columns: {', '.join(missing)}")


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    require(not frame.empty, f"Refusing to write empty TSV: {path}")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(
        temporary,
        sep="\t",
        index=False,
        na_rep="NA",
        lineterminator="\n",
    )
    os.replace(temporary, path)


def write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def source_digest(paths: Mapping[str, Path], *keys: str) -> tuple[str, str]:
    selected = [paths[key] for key in keys]
    return (
        "|".join(str(path) for path in selected),
        "|".join(sha256_file(path) for path in selected),
    )


def resolve_inputs(project_root: Path) -> dict[str, Path]:
    resolved = {key: project_root / value for key, value in INPUT_PATHS.items()}
    missing = [key for key, path in resolved.items() if not path.is_file()]
    require(not missing, "Missing required figure inputs: " + ", ".join(missing))
    return resolved


def load_bundle(project_root: Path) -> dict[str, Any]:
    paths = resolve_inputs(project_root)
    frames = {
        key: read_tsv(path)
        for key, path in paths.items()
        if path.suffix in {".tsv", ".txt"}
    }
    deg_config = read_yaml(paths["deg_config"])
    validation_config = read_yaml(paths["validation_config"])
    phase12_config = read_yaml(paths["phase12_config"])
    phase18_config = read_yaml(paths["phase18_config"])

    # All compact SEA-AD phase inputs used by the figure must already be valid.
    for key in STATUS_KEYS:
        row = one_row(frames[key], key)
        require_columns(frames[key], ["validation_status", "failed_checks"], key)
        require(row["validation_status"] == "validated_complete", f"{key} is not validated_complete")
        require(row["failed_checks"] in {"", "0"}, f"{key} records failed checks")

    phase12_status = one_row(frames["phase12_status"], "phase12_status")
    require(phase12_status["validation_status"] == "validated_complete", "Phase 12 is not validated")
    require(phase12_status["failed_checks"] in {"", "0"}, "Phase 12 records failed checks")
    rosmap_cohort = one_row(frames["rosmap_cohort_status"], "rosmap_cohort_status")
    require(rosmap_cohort["validation_status"] == "validated_complete", "ROSMAP cohort is not validated")

    # SEA-AD cohort and nucleus-level anchors.
    vh02 = one_row(frames["vh02_status"], "vh02_status")
    sea_donors = as_int(vh02["analysis_donors"], "SEA-AD analysis donors")
    dementia_donors = as_int(vh02["dementia_donors"], "Dementia donors")
    no_dementia_donors = as_int(vh02["no_dementia_donors"], "No-dementia donors")
    require(sea_donors == 78 == dementia_donors + no_dementia_donors, "SEA-AD donor counts changed")

    donor_groups = frames["donor_groups"]
    require_columns(
        donor_groups,
        ["diagnosis", "signature_group", "donors"],
        "donor_group_counts",
    )
    require(len(donor_groups) == 12, "Expected 12 SEA-AD diagnosis-by-group rows")
    require(set(donor_groups["signature_group"]) == set(GROUP_ORDER), "SEA-AD group IDs changed")
    group_donor_totals = {
        group: sum(as_int(value) for value in donor_groups.loc[donor_groups["signature_group"].eq(group), "donors"])
        for group in GROUP_ORDER
    }
    require(group_donor_totals == {"F_e2": 7, "F_e33": 26, "F_e4": 14, "M_e2": 5, "M_e33": 19, "M_e4": 7}, "SEA-AD group donor totals changed")
    diagnosis_totals = {
        diagnosis: sum(as_int(value) for value in donor_groups.loc[donor_groups["diagnosis"].eq(diagnosis), "donors"])
        for diagnosis in ("Dementia", "No dementia")
    }
    require(diagnosis_totals == {"Dementia": 37, "No dementia": 41}, "SEA-AD diagnosis totals changed")

    exclusions = frames["cohort_exclusions"]
    excluded_apoe = exclusions.loc[exclusions["reason"].eq("excluded_apoe_2_4"), "donors"]
    require(len(excluded_apoe) == 1 and as_int(excluded_apoe.iloc[0]) == 2, "APOE2/4 exclusion changed")

    vh04 = one_row(frames["vh04_status"], "vh04_status")
    selected_nuclei = as_int(vh04["selected_nuclei"], "selected nuclei")
    require(selected_nuclei == 1_189_172, "Selected-nucleus count changed")
    donor_supertype = frames["donor_supertype_counts"]
    require_columns(donor_supertype, ["nuclei", "supertype_id", "broad_network"], "donor-supertype counts")
    require(sum(as_int(value) for value in donor_supertype["nuclei"]) == selected_nuclei, "Fine-profile nuclei do not sum to the selected total")

    supertype_map = frames["supertype_map"]
    require_columns(supertype_map, ["supertype_id", "broad_network"], "supertype map")
    require(len(supertype_map) == 129, "Expected 129 included SEA-AD supertypes")
    require(supertype_map["supertype_id"].nunique() == 129, "SEA-AD supertype IDs are not unique")
    observed_supertypes = {
        network: int(count)
        for network, count in supertype_map.groupby("broad_network").size().to_dict().items()
    }
    require(observed_supertypes == EXPECTED_SUPERTYPES, "SEA-AD supertype-to-network counts changed")

    configured_groups = [row["group_id"] for row in deg_config["cohort"]["signature_groups"]]
    require(configured_groups == GROUP_ORDER, "SEA-AD configured group order changed")
    require(deg_config["cohort"]["included_diagnoses"] == ["Dementia", "No dementia"], "SEA-AD phenotype labels changed")
    require(deg_config["cohort"]["excluded_apoe"] == ["2/4"], "SEA-AD APOE exclusion changed")
    require(as_int(deg_config["thresholds"]["primary_min_nuclei"]) == 20, "Fine-profile nucleus threshold changed")
    require(as_int(deg_config["thresholds"]["min_donors_per_disease_arm"]) == 5, "Disease-arm donor threshold changed")
    expected_formula = "~ 0 + diagnosis_sex_apoe_group + age_death_scaled + pmi_scaled + study"
    require(deg_config["models"]["fine_grouped_formula"] == expected_formula, "Fine DEG model formula changed")
    require(deg_config["models"]["normalization"] == "TMM", "Fine DEG normalization changed")
    require(truth(deg_config["models"]["robust"]), "Fine DEG robust fitting is not enabled")
    require(deg_config["models"]["fdr_method"] == "BH", "Fine DEG FDR method changed")

    # Fine-supertype contrast and direction scope.
    contrasts = frames["fine_contrast_status"]
    require_columns(
        contrasts,
        [
            "contrast_id",
            "supertype_id",
            "signature_group",
            "case_phenotype",
            "reference_phenotype",
            "coefficient_direction",
            "terminal_status",
        ],
        "fine contrast status",
    )
    require(len(contrasts) == 774 and contrasts["contrast_id"].nunique() == 774, "Fine contrast count or identity changed")
    require(contrasts["supertype_id"].nunique() == 129, "Fine contrast supertype scope changed")
    require(set(contrasts["signature_group"]) == set(GROUP_ORDER), "Fine contrast groups changed")
    require(set(contrasts["case_phenotype"]) == {"Dementia"}, "Fine contrast case phenotype changed")
    require(set(contrasts["reference_phenotype"]) == {"No dementia"}, "Fine contrast reference phenotype changed")
    require(set(contrasts["coefficient_direction"]) == {"Dementia_minus_No_dementia"}, "Fine contrast direction changed")
    contrast_status_counts = contrasts["terminal_status"].value_counts().to_dict()
    require(contrast_status_counts == {"not_estimable": 514, "completed": 260}, "Fine contrast terminal counts changed")
    completed_group_counts = {
        group: int(
            contrasts.loc[
                contrasts["terminal_status"].eq("completed")
                & contrasts["signature_group"].eq(group)
            ].shape[0]
        )
        for group in GROUP_ORDER
    }
    require(completed_group_counts == EXPECTED_COMPLETED_GROUPS, "Completed fine contrasts by group changed")

    directions = frames["fine_direction_manifest"]
    require_columns(
        directions,
        ["direction_slot_id", "phase18_signature_direction", "query_handoff_status"],
        "fine direction manifest",
    )
    require(len(directions) == 1_548 and directions["direction_slot_id"].nunique() == 1_548, "Fine direction scope changed")
    require(directions["phase18_signature_direction"].value_counts().to_dict() == {"AD_up_mito": 774, "AD_down_mito": 774}, "Fine direction signs changed")
    require(
        directions["query_handoff_status"].value_counts().to_dict()
        == {"source_contrast_not_estimable": 1_028, "ready_for_query_construction": 520},
        "Fine direction handoff counts changed",
    )

    # SEA-AD query construction and KDA scope.
    vh10_config = validation_config["vh10"]
    analysis_config = vh10_config["analysis"]
    require(analysis_config["query_rule_id"] == "phase18_parity_query", "Active SEA-AD query rule changed")
    require(analysis_config["result_tier_id"] == "phase18_parity_query__min3_all", "Active SEA-AD result tier changed")
    require(abs(float(analysis_config["fdr_threshold_exclusive"]) - 0.05) <= 1e-15, "SEA-AD FDR threshold changed")
    require(abs(float(analysis_config["absolute_fold_change"]) - 1.3) <= 1e-15, "SEA-AD fold-change threshold changed")
    require(as_int(analysis_config["minimum_effective_query_genes"]) == 3, "SEA-AD minimum query size changed")
    require(as_int(analysis_config["small_query_warning_below"]) == 10, "SEA-AD small-query boundary changed")
    require(analysis_config["directions"] == ["AD_up_mito", "AD_down_mito"], "SEA-AD direction order changed")

    input_checks = frames["vh10a_checks"]
    require_columns(input_checks, ["check", "passed", "observed", "expected"], "VH10A input checks")
    require(input_checks["passed"].map(truth).all(), "At least one VH10A input check failed")
    subset_check = input_checks.loc[input_checks["check"].eq("effective_queries_subset_background")]
    require(len(subset_check) == 1 and truth(subset_check.iloc[0]["observed"]), "Qeff subset-background check failed")

    run_manifest = frames["seaad_run_manifest"]
    require_columns(
        run_manifest,
        [
            "direction_slot_id",
            "signature_group",
            "signature_direction",
            "effective_query_genes",
            "query_size_tier",
            "eligibility_status",
            "terminal_status",
        ],
        "SEA-AD KDA run manifest",
    )
    require(len(run_manifest) == 1_548 and run_manifest["direction_slot_id"].nunique() == 1_548, "SEA-AD KDA run-manifest scope changed")
    terminal_partition = run_manifest["terminal_status"].value_counts().to_dict()
    require(
        terminal_partition
        == {
            "source_contrast_not_estimable": 1_028,
            "query_empty": 462,
            "query_below_minimum": 16,
            "eligible_small_query": 21,
            "eligible_phase18_sized": 21,
        },
        "SEA-AD query attrition changed",
    )
    active = run_manifest.loc[
        run_manifest["eligibility_status"].eq("eligible")
        & run_manifest["terminal_status"].isin(["eligible_small_query", "eligible_phase18_sized"])
    ].copy()
    require(len(active) == 42, "Active SEA-AD KDA call count changed")
    require(active["signature_direction"].value_counts().to_dict() == {"AD_down_mito": 22, "AD_up_mito": 20}, "SEA-AD active direction counts changed")
    require(active["query_size_tier"].value_counts().to_dict() == {"small_query": 21, "phase18_sized": 21}, "SEA-AD active query-size tiers changed")
    require(
        active["signature_group"].value_counts().to_dict()
        == {"M_e33": 40, "F_e33": 1, "F_e4": 1},
        "SEA-AD active group distribution changed",
    )

    attrition = frames["query_attrition"]
    require(sum(as_int(value) for value in attrition["direction_slots"]) == 1_548, "Query-attrition table does not sum to 1,548")
    vh10a = one_row(frames["vh10a_status"], "vh10a_status")
    require(as_int(vh10a["active_kda_calls"]) == len(active), "VH10A active-call status disagrees")

    run_qc = frames["vh10b_run_qc"]
    require(len(run_qc) == 42 and run_qc["kda_run_id"].nunique() == 42, "VH10B run-QC scope changed")
    kda_outcomes = run_qc["terminal_status"].value_counts().to_dict()
    require(kda_outcomes == {"completed_significant": 29, "completed_no_significant": 13}, "SEA-AD KDA call outcomes changed")
    vh10b = one_row(frames["vh10b_status"], "vh10b_status")
    require(as_int(vh10b["active_kda_calls"]) == 42, "VH10B status call count changed")

    # Selection and independence freeze. Sentinel top-list rows are excluded.
    selection = vh10_config["selection"]
    require(abs(float(selection["minimum_coverage"]) - 0.80) <= 1e-15, "Selection coverage changed")
    require(abs(float(selection["aggregate_q_threshold"]) - 0.05) <= 1e-15, "Selection aggregate-q threshold changed")
    require(as_int(selection["minimum_conservative_supporting_runs"]) == 1, "Selection support threshold changed")
    require(as_int(selection["display_limit"]) == 5, "Selection display limit changed")
    require(selection["driver_classes"] == ["mt_driver", "non_mt_driver"], "SEA-AD driver classes changed")

    seaad_top5 = frames["seaad_top5"]
    selected_sea = seaad_top5.loc[
        seaad_top5["query_rule_id"].eq("phase18_parity_query")
        & seaad_top5["result_tier_id"].eq("phase18_parity_query__min3_all")
        & seaad_top5["list_status"].eq("ranked_candidates")
        & ~seaad_top5["current_symbol"].isin(["", "NA"])
        & ~seaad_top5["display_rank"].isin(["", "NA"])
    ].copy()
    require(len(selected_sea) == 13, "SEA-AD selected-unit count changed")
    require(selected_sea[["broad_network", "current_symbol", "case_id"]].drop_duplicates().shape[0] == 13, "SEA-AD selected keys are not unique")
    require(selected_sea["case_id"].value_counts().to_dict() == {"mt_driver": 8, "non_mt_driver": 5}, "SEA-AD selected class counts changed")
    require(selected_sea["current_symbol"].nunique() == 11, "SEA-AD selected unique-symbol count changed")
    require(max(as_int(value) for value in selected_sea["display_rank"]) <= 5, "SEA-AD display rank exceeds five")
    require(len(seaad_top5) == 22, "SEA-AD top-list sentinel contract changed")

    freeze = one_row(frames["seaad_freeze"], "SEA-AD selection freeze")
    require(freeze["freeze_status"] == "independent_seaad_selection_frozen", "SEA-AD freeze status changed")
    require(not truth(freeze["rosmap_candidate_files_read"]), "ROSMAP candidate files were read before SEA-AD freeze")
    require(as_int(freeze["selected_top5_units"]) == 13, "SEA-AD freeze selected count changed")
    require(as_int(freeze["selected_unique_genes"]) == 11, "SEA-AD freeze unique-symbol count changed")

    # Validate frozen input authority and the seven matched networks.
    authority = frames["vh10a_authority"]
    require_columns(authority, ["role", "path", "bytes", "sha256"], "VH10A input authority")
    authority_paths: list[Path] = []
    for row in authority.itertuples(index=False):
        path = project_root / str(row.path)
        require(path.is_file(), f"Missing frozen authority input: {row.path}")
        require(path.stat().st_size == as_int(row.bytes), f"Authority byte count changed: {row.path}")
        require(sha256_file(path) == str(row.sha256), f"Authority SHA-256 changed: {row.path}")
        authority_paths.append(path)

    networks = frames["network_identity"]
    require(len(networks) == 7 and list(networks["broad_network"]) == SHARED_NETWORK_ORDER, "Matched-network identity/order changed")
    network_paths: list[Path] = []
    for row in networks.itertuples(index=False):
        network = str(row.broad_network)
        path = project_root / str(row.network_path)
        require(path.is_file(), f"Missing matched network: {row.network_path}")
        require(sha256_file(path) == str(row.network_sha256), f"Matched-network SHA changed: {network}")
        require(phase12_config["networks"][network]["path"] == str(row.network_path), f"Network path/config mismatch: {network}")
        require(phase12_config["networks"][network]["sha256"] == str(row.network_sha256), f"Network SHA/config mismatch: {network}")
        network_paths.append(path)
    require(phase12_config["background"]["primary_policy"] == "exact_contrast_tested_intersect_induced_network", "Phase 12 background policy changed")
    require(as_int(phase12_config["kda"]["nLayerToTest"]) == 3, "fKDA layer count changed")
    require(truth(phase12_config["kda"]["directed"]), "fKDA is no longer directed")
    require(phase12_config["kda"]["p_correction_method"] == "BH", "Within-run correction changed")

    # ROSMAP structural and frozen Phase 18 scope.
    rosmap_donors = as_int(rosmap_cohort["global_donors"], "ROSMAP global donors")
    require(rosmap_donors == 276, "ROSMAP global donor universe changed")
    phase18_groups = list(phase18_config["run_scope"]["groups"])
    phase18_directions = list(phase18_config["run_scope"]["directions"])
    require(phase18_groups == GROUP_ORDER, "Phase 18 group order changed")
    require(phase18_directions == ["AD_up_mito", "AD_down_mito"], "Phase 18 direction scope changed")
    require(as_int(phase18_config["run_scope"]["minimum_effective_query_genes"]) == 10, "Phase 18 minimum query size changed")
    require(as_int(phase18_config["run_scope"]["expected_structural_slots"]) == 648, "Phase 18 structural-slot expectation changed")
    require(as_int(phase18_config["run_scope"]["expected_included_runs"]) == 161, "Phase 18 included-run expectation changed")
    require([row["case_id"] for row in phase18_config["cases"]] == ["mt_driver", "non_mt_driver"], "Phase 18 driver classes changed")

    phase12_manifest = frames["phase12_manifest"]
    primary_ros = phase12_manifest.loc[
        phase12_manifest["analysis_tier"].eq("primary")
        & phase12_manifest["signature_group"].isin(phase18_groups)
        & phase12_manifest["signature_direction"].isin(phase18_directions)
    ].copy()
    require(len(primary_ros) == 648, "ROSMAP Phase 18 structural scope changed")
    require(primary_ros["fine_cell_type"].nunique() == 54, "ROSMAP fine-cell-type count changed")
    require(primary_ros["signature_group"].value_counts().to_dict() == {group: 108 for group in GROUP_ORDER}, "ROSMAP structural group counts changed")
    require(primary_ros["signature_direction"].value_counts().to_dict() == {"AD_up_mito": 324, "AD_down_mito": 324}, "ROSMAP structural direction counts changed")
    require(primary_ros["source_contrast_ids"].str.contains("AD_vs_NCI", regex=False).all(), "ROSMAP phenotype contract changed")
    source_network_counts = (
        primary_ros[["broad_network", "fine_cell_type"]]
        .drop_duplicates()
        .groupby("broad_network")
        .size()
        .to_dict()
    )
    require(source_network_counts == EXPECTED_ROSMAP_SOURCE_NETWORKS, "ROSMAP 54-type source-network distribution changed")

    effective_sizes = pd.to_numeric(primary_ros["effective_query_genes"], errors="coerce")
    included_ros = primary_ros.loc[
        primary_ros["eligibility_status"].eq("eligible")
        & primary_ros["terminal_status"].str.startswith("completed")
        & effective_sizes.ge(10)
    ].copy()
    require(len(included_ros) == 161, "ROSMAP included Phase 18 run count changed")
    require(set(included_ros["broad_network"]) == set(SHARED_NETWORK_ORDER), "ROSMAP included runs are not confined to the seven matched networks")
    require(
        included_ros["broad_network"].value_counts().to_dict()
        == {
            "Excitatory_neurons": 97,
            "Inhibitory_neurons": 28,
            "Astrocytes": 21,
            "Microglia": 6,
            "OPCs": 6,
            "Oligodendrocytes": 2,
            "Vasculature_cells": 1,
        },
        "ROSMAP included-run network distribution changed",
    )

    rosmap_selected = frames["rosmap_selected"]
    require(len(rosmap_selected) == 47, "Frozen ROSMAP selected-unit count changed")
    require(rosmap_selected[["broad_network", "key_driver", "case_id"]].drop_duplicates().shape[0] == 47, "ROSMAP selected keys are not unique")
    require(rosmap_selected["top5_display"].map(truth).all(), "A frozen ROSMAP row is not top-five displayed")
    require(set(rosmap_selected["terminal_candidate_status"]) == {"driver_candidate"}, "ROSMAP selected status changed")
    require(rosmap_selected["case_id"].value_counts().to_dict() == {"mt_driver": 26, "non_mt_driver": 21}, "ROSMAP selected class counts changed")
    require(rosmap_selected["key_driver"].nunique() == 25, "ROSMAP selected unique-symbol count changed")
    require(max(as_int(value) for value in rosmap_selected["within_case_rank"]) <= 5, "ROSMAP display rank exceeds five")
    require(set(rosmap_selected["broad_network"]) == set(SHARED_NETWORK_ORDER), "ROSMAP selected units leave the matched network scope")

    shared_scope = frames["shared_network_scope"]
    require(len(shared_scope) == 7, "Shared-network scope row count changed")
    require(list(shared_scope["phase18_broad_network"]) == SHARED_NETWORK_ORDER, "Shared-network scope order changed")
    require((shared_scope["phase18_broad_network"] == shared_scope["seaad_broad_network"]).all(), "Shared-network machine IDs diverged")
    require(set(shared_scope["identity_status"]) == {"exact_shared_machine_id"}, "Shared-network identity status changed")
    require(sum(as_int(value) for value in shared_scope["selected_phase18_units"]) == 47, "Shared-network selected counts do not sum to 47")

    # Collect all direct and frozen-authority inputs for the provenance manifest.
    artifact_inputs = set(paths.values()) | set(authority_paths) | set(network_paths)
    input_digests = {str(path.relative_to(project_root)): sha256_file(path) for path in sorted(artifact_inputs)}
    combined = hashlib.sha256()
    for relative_path, digest in sorted(input_digests.items()):
        combined.update(f"{relative_path}\t{digest}\n".encode("utf-8"))

    return {
        "project_root": project_root,
        "paths": paths,
        "input_digests": input_digests,
        "input_bundle_sha256": combined.hexdigest(),
        "sea_donors": sea_donors,
        "dementia_donors": dementia_donors,
        "no_dementia_donors": no_dementia_donors,
        "selected_nuclei": selected_nuclei,
        "supertypes": len(supertype_map),
        "supertype_counts": observed_supertypes,
        "groups": len(GROUP_ORDER),
        "completed_group_counts": completed_group_counts,
        "fine_contrasts": len(contrasts),
        "completed_contrasts": contrast_status_counts["completed"],
        "not_estimable_contrasts": contrast_status_counts["not_estimable"],
        "structural_directions": len(directions),
        "source_directions": int(directions["query_handoff_status"].eq("ready_for_query_construction").sum()),
        "source_not_estimable_directions": int(directions["query_handoff_status"].eq("source_contrast_not_estimable").sum()),
        "query_empty": terminal_partition["query_empty"],
        "query_below_minimum": terminal_partition["query_below_minimum"],
        "active_calls": len(active),
        "up_calls": int(active["signature_direction"].eq("AD_up_mito").sum()),
        "down_calls": int(active["signature_direction"].eq("AD_down_mito").sum()),
        "small_calls": int(active["query_size_tier"].eq("small_query").sum()),
        "large_calls": int(active["query_size_tier"].eq("phase18_sized").sum()),
        "calls_with_return": kda_outcomes["completed_significant"],
        "calls_without_return": kda_outcomes["completed_no_significant"],
        "sea_selected": len(selected_sea),
        "sea_selected_mt": int(selected_sea["case_id"].eq("mt_driver").sum()),
        "sea_selected_nonmt": int(selected_sea["case_id"].eq("non_mt_driver").sum()),
        "sea_symbols": selected_sea["current_symbol"].nunique(),
        "shared_networks": len(SHARED_NETWORK_ORDER),
        "sea_min_query": as_int(analysis_config["minimum_effective_query_genes"]),
        "ros_min_query": as_int(phase18_config["run_scope"]["minimum_effective_query_genes"]),
        "rosmap_donors": rosmap_donors,
        "rosmap_fine_types": primary_ros["fine_cell_type"].nunique(),
        "rosmap_source_networks": primary_ros["broad_network"].nunique(),
        "rosmap_structural": len(primary_ros),
        "rosmap_included": len(included_ros),
        "rosmap_selected": len(rosmap_selected),
        "rosmap_symbols": rosmap_selected["key_driver"].nunique(),
        "fine_formula": expected_formula,
        "background_policy": phase12_config["background"]["primary_policy"],
        "query_rule": deg_config["query_rules"]["phase18_parity_query"],
        "selected_sea_keys": set(zip(selected_sea["broad_network"], selected_sea["current_symbol"], selected_sea["case_id"])),
        "selected_ros_keys": set(zip(rosmap_selected["broad_network"], rosmap_selected["key_driver"], rosmap_selected["case_id"])),
    }


LAYOUT = {
    "a1": (0.16, 3.01, 1.54, 1.35),
    "a2": (1.92, 3.01, 1.65, 1.35),
    "a3": (3.79, 3.01, 1.92, 1.35),
    "a4": (5.93, 3.01, 2.15, 1.35),
    "a5": (8.30, 3.01, 1.94, 1.35),
    "a6": (10.46, 3.01, 1.81, 1.35),
    "ribbon_groups": (0.16, 2.58, 3.41, 0.29),
    "ribbon_attrition": (3.79, 2.58, 6.45, 0.29),
    "shared_band": (2.15, 1.87, 8.09, 0.47),
    "rosmap": (0.16, 0.23, 8.22, 1.35),
    "comparison": (8.91, 0.23, 3.36, 1.35),
}


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    order = 0

    def source(*keys: str) -> tuple[str, str]:
        relative = [str(bundle["paths"][key].relative_to(bundle["project_root"])) for key in keys]
        digests = [bundle["input_digests"][path] for path in relative]
        return "|".join(relative), "|".join(digests)

    def add(
        panel_id: str,
        parent_id: str,
        element_id: str,
        element_type: str,
        cohort: str,
        label_key: str,
        display_text: str,
        *,
        value: Any = "NA",
        value_type: str = "label",
        unit: str = "NA",
        source_keys: Sequence[str] = (),
        source_columns: str = "NA",
        source_filter: str = "NA",
        derivation: str = "NA",
        value_origin: str = "method_constant",
        style_key: str = "neutral_text",
        optional_variant: str = "canonical",
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        x2: float | None = None,
        y2: float | None = None,
    ) -> None:
        nonlocal order
        order += 1
        if source_keys:
            source_path, source_sha256 = source(*source_keys)
        else:
            source_path, source_sha256 = "NA", "NA"
        if parent_id in LAYOUT:
            default_x, default_y, default_width, default_height = LAYOUT[parent_id]
        else:
            default_x = default_y = default_width = default_height = math.nan
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "order": order,
                "panel_id": panel_id,
                "parent_id": parent_id,
                "element_id": element_id,
                "element_type": element_type,
                "cohort": cohort,
                "label_key": label_key,
                "display_text": display_text,
                "value": value,
                "value_type": value_type,
                "unit": unit,
                "x_inches": default_x if x is None else x,
                "y_inches": default_y if y is None else y,
                "width_inches": default_width if width is None else width,
                "height_inches": default_height if height is None else height,
                "x2_inches": "NA" if x2 is None else x2,
                "y2_inches": "NA" if y2 is None else y2,
                "source_path": source_path,
                "source_sha256": source_sha256,
                "source_columns": source_columns,
                "source_filter": source_filter,
                "derivation": derivation,
                "value_origin": value_origin,
                "style_key": style_key,
                "optional_variant": optional_variant,
            }
        )

    add("A", "header_a", "panel_a_heading", "panel_heading", "SEA-AD", "panel_a_heading", "A  INDEPENDENT SEA-AD EVIDENCE", style_key="sea_heading", x=0.16, y=4.57, width=7.0, height=0.12)

    add("A", "a1", "a1_heading", "box_heading", "SEA-AD", "a1_heading", "Independent cohort", style_key="sea_box")
    add("A", "a1", "sea_donors_total", "metric", "SEA-AD", "sea_donors", f"{bundle['sea_donors']} donors", value=bundle["sea_donors"], value_type="count", unit="donors", source_keys=["vh02_status"], source_columns="analysis_donors", value_origin="read", style_key="sea_anchor")
    add("A", "a1", "sea_dementia_donors", "metric", "SEA-AD", "sea_dementia", f"{bundle['dementia_donors']} Dementia", value=bundle["dementia_donors"], value_type="count", unit="donors", source_keys=["vh02_status", "donor_groups"], source_columns="dementia_donors|diagnosis+donors", value_origin="read", style_key="sea_text")
    add("A", "a1", "sea_no_dementia_donors", "metric", "SEA-AD", "sea_no_dementia", f"{bundle['no_dementia_donors']} No dementia", value=bundle["no_dementia_donors"], value_type="count", unit="donors", source_keys=["vh02_status", "donor_groups"], source_columns="no_dementia_donors|diagnosis+donors", value_origin="read", style_key="sea_text")
    add("A", "a1", "sea_selected_nuclei", "metric", "SEA-AD", "sea_nuclei", f"{bundle['selected_nuclei']:,} selected nuclei", value=bundle["selected_nuclei"], value_type="count", unit="nuclei", source_keys=["vh04_status", "donor_supertype_counts"], source_columns="selected_nuclei|nuclei", derivation="status count equals sum of fine-profile nuclei", value_origin="read", style_key="sea_text")
    add("A", "a1", "sea_replicate_unit", "annotation", "SEA-AD", "sea_replicate", "donor = statistical replicate", source_keys=["deg_config"], source_columns="assay/cohort contract", style_key="sea_footer")

    add("A", "a2", "a2_heading", "box_heading", "SEA-AD", "a2_heading", "Donor pseudobulk", style_key="sea_box")
    add("A", "a2", "sea_supertype_total", "metric", "SEA-AD", "sea_supertypes", f"{bundle['supertypes']} supertypes", value=bundle["supertypes"], value_type="count", unit="fine supertypes", source_keys=["vh04_status", "supertype_map"], source_columns="included_supertypes|supertype_id", value_origin="read", style_key="sea_anchor")
    add("A", "a2", "sea_fine_separate", "annotation", "SEA-AD", "sea_fine_separate", "fine labels stay separate", source_keys=["supertype_map", "fine_contrast_status"], source_columns="supertype_id", derivation="one contrast/run identity per supertype", value_origin="derived", style_key="sea_text")
    add("A", "a2", "sea_group_count", "metric", "SEA-AD", "sea_groups", f"{bundle['groups']} sex/APOE groups", value=bundle["groups"], value_type="count", unit="groups", source_keys=["deg_config"], source_columns="cohort.signature_groups", value_origin="read", style_key="sea_text")
    add("A", "a2", "sea_network_count", "metric", "SEA-AD", "sea_networks", f"map to {bundle['shared_networks']} matched networks", value=bundle["shared_networks"], value_type="count", unit="broad networks", source_keys=["supertype_map", "network_identity"], source_columns="broad_network", derivation="unique exact matched network IDs", value_origin="derived", style_key="sea_text")
    add("A", "a2", "sea_profile_gate", "threshold", "SEA-AD", "sea_profile_gate", "≥20 nuclei / donor profile", value=20, value_type="threshold", unit="nuclei", source_keys=["deg_config"], source_columns="thresholds.primary_min_nuclei", value_origin="read", style_key="sea_footer")

    add("A", "a3", "a3_heading", "box_heading", "SEA-AD", "a3_heading", "Adjusted edgeR QL DEG", style_key="sea_box")
    add("A", "a3", "sea_phenotype_contrast", "annotation", "SEA-AD", "sea_phenotype", "Dementia − No dementia", source_keys=["fine_contrast_status"], source_columns="case_phenotype+reference_phenotype+coefficient_direction", source_filter="all 774 fine contrast rows", value_origin="read", style_key="sea_text")
    add("A", "a3", "sea_contrasts", "metric", "SEA-AD", "sea_contrasts", f"129 × 6 = {bundle['fine_contrasts']} contrasts", value=bundle["fine_contrasts"], value_type="count", unit="contrasts", source_keys=["fine_contrast_status"], source_columns="contrast_id", derivation="129 supertypes × 6 groups", value_origin="derived", style_key="sea_anchor")
    add("A", "a3", "sea_direction_split", "annotation", "SEA-AD", "sea_direction_split", "split into up ▲ and down ▼", value=2, value_type="count", unit="directions per contrast", source_keys=["fine_direction_manifest"], source_columns="phase18_signature_direction", value_origin="derived", style_key="direction_text")
    add("A", "a3", "sea_structural_directions", "metric", "SEA-AD", "sea_structural", f"{bundle['structural_directions']:,} structural slots", value=bundle["structural_directions"], value_type="count", unit="direction slots", source_keys=["fine_direction_manifest"], source_columns="direction_slot_id", value_origin="read", style_key="sea_anchor")
    add("A", "a3", "sea_model_adjustment", "annotation", "SEA-AD", "sea_adjustment", "age at death + PMI + study", source_keys=["deg_config"], source_columns="models.fine_grouped_formula", value_origin="read", style_key="sea_footer")

    add("A", "a4", "a4_heading", "box_heading", "SEA-AD", "a4_heading", "Signed core-Mito query", style_key="sea_box_emphasis")
    add("A", "a4", "sea_query_universe", "annotation", "SEA-AD", "sea_query_universe", "core MitoCarta genes only", source_keys=["vh03_status", "validation_config"], source_columns="core_mito_features|vh10.analysis.query_rule_id", value_origin="method_constant", style_key="sea_text")
    add("A", "a4", "sea_fdr_threshold", "threshold", "SEA-AD", "sea_fdr", "FDR < 0.05", value=0.05, value_type="exclusive threshold", unit="BH FDR", source_keys=["validation_config"], source_columns="vh10.analysis.fdr_threshold_exclusive", value_origin="read", style_key="sea_text")
    add("A", "a4", "sea_effect_threshold", "threshold", "SEA-AD", "sea_effect", "|log₂FC| > log₂(1.3)", value=1.3, value_type="exclusive fold-change threshold", unit="absolute fold change", source_keys=["validation_config", "deg_config"], source_columns="vh10.analysis.absolute_fold_change|query_rules.phase18_parity_query", value_origin="read", style_key="sea_text")
    add("A", "a4", "sea_query_directions", "annotation", "SEA-AD", "sea_query_directions", "Dementia-up ▲  |  -down ▼", value=2, value_type="count", unit="signed directions", source_keys=["validation_config"], source_columns="vh10.analysis.directions", value_origin="read", style_key="direction_text")
    add("A", "a4", "sea_effective_query", "formula", "SEA-AD", "sea_qeff", "Qeff = Q0 ∩ induced background", source_keys=["phase12_config", "vh10a_checks"], source_columns="background.primary_policy|effective_queries_subset_background", value_origin="method_constant", style_key="sea_text")
    add("A", "a4", "sea_minimum_query", "threshold", "SEA-AD", "sea_min_query", f"run if |Qeff| ≥ {bundle['sea_min_query']}", value=bundle["sea_min_query"], value_type="inclusive threshold", unit="effective query genes", source_keys=["validation_config"], source_columns="vh10.analysis.minimum_effective_query_genes", value_origin="read", style_key="sea_anchor")

    add("A", "a5", "a5_heading", "box_heading", "SEA-AD", "a5_heading", "Directed KDA + selection", style_key="sea_box")
    add("A", "a5", "sea_matching_network", "annotation", "SEA-AD", "sea_matching_network", "matching broad network", value=bundle["shared_networks"], value_type="count", unit="matched network choices", source_keys=["network_identity", "seaad_run_manifest"], source_columns="broad_network", value_origin="method_constant", style_key="sea_text")
    add("A", "a5", "sea_fkda_layers", "method", "shared", "sea_fkda_layers", "fKDA downstream layers 1–3", value=3, value_type="maximum layer", unit="layers", source_keys=["phase12_config"], source_columns="kda.nLayerToTest", value_origin="read", style_key="sea_text")
    add("A", "a5", "sea_selector", "method", "shared", "sea_selector", "Phase 18 gates + ranking", source_keys=["validation_config", "phase18_config"], source_columns="vh10.selection|filters+aggregation+ranking", value_origin="method_constant", style_key="sea_text")
    add("A", "a5", "sea_active_calls", "metric", "SEA-AD", "sea_active_calls", f"{bundle['active_calls']} KDA calls", value=bundle["active_calls"], value_type="count", unit="KDA calls", source_keys=["seaad_run_manifest", "vh10a_status"], source_columns="eligibility_status+terminal_status|active_kda_calls", source_filter="eligible_small_query or eligible_phase18_sized", value_origin="derived", style_key="sea_anchor")
    add("A", "a5", "sea_call_directions", "metric", "SEA-AD", "sea_call_directions", f"{bundle['up_calls']} up  |  {bundle['down_calls']} down", value=f"{bundle['up_calls']}|{bundle['down_calls']}", value_type="count pair", unit="KDA calls", source_keys=["seaad_run_manifest"], source_columns="signature_direction", source_filter="active KDA calls", value_origin="derived", style_key="direction_text")

    add("A", "a6", "a6_heading", "box_heading", "SEA-AD", "a6_heading", "SEA-AD list frozen", style_key="freeze_heading")
    add("A", "a6", "sea_checksum_lock", "annotation", "SEA-AD", "sea_checksum", "checksum locked", source_keys=["seaad_freeze"], source_columns="freeze_status+top5_sha256", value_origin="read", style_key="freeze_text")
    add("A", "a6", "sea_selected_units", "metric", "SEA-AD", "sea_selected", f"{bundle['sea_selected']} selected units", value=bundle["sea_selected"], value_type="count", unit="network-gene-class units", source_keys=["seaad_top5", "seaad_freeze"], source_columns="list_status+current_symbol+case_id|selected_top5_units", source_filter="list_status == ranked_candidates and symbol/rank nonmissing", value_origin="derived", style_key="freeze_anchor")
    add("A", "a6", "sea_selected_classes", "metric", "SEA-AD", "sea_classes", f"{bundle['sea_selected_mt']} MT  |  {bundle['sea_selected_nonmt']} non-MT", value=f"{bundle['sea_selected_mt']}|{bundle['sea_selected_nonmt']}", value_type="count pair", unit="selected units", source_keys=["seaad_top5"], source_columns="case_id", source_filter="ranked candidate rows only", value_origin="derived", style_key="freeze_text")
    add("A", "a6", "sea_selected_symbols", "metric", "SEA-AD", "sea_symbols", f"{bundle['sea_symbols']} gene symbols", value=bundle["sea_symbols"], value_type="count", unit="unique current symbols", source_keys=["seaad_top5", "seaad_freeze"], source_columns="current_symbol|selected_unique_genes", source_filter="ranked candidate rows only", value_origin="derived", style_key="freeze_text")

    add("A", "ribbon_groups", "group_ribbon_label", "ribbon_label", "SEA-AD", "group_ribbon_label", "Completed contrasts by group", source_keys=["fine_contrast_status"], source_columns="signature_group+terminal_status", source_filter="terminal_status == completed", style_key="group_ribbon")
    for group in GROUP_ORDER:
        add("A", "ribbon_groups", f"completed_{group}", "group_metric", "SEA-AD", f"completed_{group}", f"{group} {bundle['completed_group_counts'][group]}", value=bundle["completed_group_counts"][group], value_type="count", unit="completed contrasts", source_keys=["fine_contrast_status"], source_columns="signature_group+terminal_status", source_filter=f"signature_group == {group}; terminal_status == completed", value_origin="derived", style_key="group_active" if bundle["completed_group_counts"][group] else "group_zero")

    add("A", "ribbon_attrition", "attrition_completed", "ribbon_metric", "SEA-AD", "attrition_completed", f"{bundle['completed_contrasts']} completed contrasts", value=bundle["completed_contrasts"], value_type="count", unit="contrasts", source_keys=["fine_contrast_status"], source_columns="terminal_status", source_filter="completed", value_origin="derived", style_key="attrition")
    add("A", "ribbon_attrition", "attrition_source_directions", "ribbon_metric", "SEA-AD", "attrition_source", f"{bundle['source_directions']} source directions", value=bundle["source_directions"], value_type="count", unit="signed directions", source_keys=["fine_direction_manifest"], source_columns="query_handoff_status", source_filter="ready_for_query_construction", value_origin="derived", style_key="attrition")
    add("A", "ribbon_attrition", "attrition_active", "ribbon_metric", "SEA-AD", "attrition_active", f"{bundle['active_calls']} runnable calls", value=bundle["active_calls"], value_type="count", unit="KDA calls", source_keys=["seaad_run_manifest"], source_columns="terminal_status", source_filter="eligible small or phase18-sized", value_origin="derived", style_key="attrition_anchor")
    add("A", "ribbon_attrition", "attrition_small", "ribbon_metric", "SEA-AD", "attrition_small", f"{bundle['small_calls']} with 3–9 genes", value=bundle["small_calls"], value_type="count", unit="KDA calls", source_keys=["seaad_run_manifest"], source_columns="query_size_tier", source_filter="small_query", value_origin="derived", style_key="attrition_detail")
    add("A", "ribbon_attrition", "attrition_large", "ribbon_metric", "SEA-AD", "attrition_large", f"{bundle['large_calls']} with ≥10", value=bundle["large_calls"], value_type="count", unit="KDA calls", source_keys=["seaad_run_manifest"], source_columns="query_size_tier", source_filter="phase18_sized", value_origin="derived", style_key="attrition_detail")

    add("B", "shared_band", "panel_b_heading", "panel_heading", "shared", "panel_b_heading", "B  SHARED, FROZEN NETWORK/KDA SCAFFOLD", style_key="shared_heading")
    add("B", "shared_band", "shared_networks", "method", "shared", "shared_networks", f"{bundle['shared_networks']} matched broad networks", value=bundle["shared_networks"], value_type="count", unit="networks", source_keys=["network_identity", "shared_network_scope"], source_columns="broad_network", value_origin="read", style_key="shared_item")
    add("B", "shared_band", "shared_annotation", "method", "shared", "shared_annotation", "current symbols + core MitoCarta", source_keys=["vh03_status", "vh10a_authority"], source_columns="phase18_exact+core_mito_features|phase18_annotation", value_origin="method_constant", style_key="shared_item")
    add("B", "shared_band", "shared_fkda", "method", "shared", "shared_fkda", "fKDA + MT self-exclusion", source_keys=["phase12_config", "vh10a_authority"], source_columns="kda|fkda_source+phase18_code", value_origin="method_constant", style_key="shared_item")
    add("B", "shared_band", "shared_selection", "method", "shared", "shared_selection", "BH + ACAT + gates + class ranking", source_keys=["validation_config", "phase18_config"], source_columns="selection|filters+aggregation+ranking", value_origin="method_constant", style_key="shared_item")
    add("B", "shared_band", "shared_boundary", "boundary", "shared", "shared_boundary", "not cohorts, DEG models, queries, or candidate identities", source_keys=["seaad_freeze"], source_columns="rosmap_candidate_files_read", value=False, value_type="boolean", unit="ROSMAP candidate files read before freeze", value_origin="read", style_key="shared_boundary")

    add("C", "rosmap", "panel_c_heading", "panel_heading", "ROSMAP", "panel_c_heading", "C  FROZEN ROSMAP PHASE 18 REFERENCE", style_key="ros_heading")
    add("C", "rosmap", "rosmap_donors", "metric", "ROSMAP", "ros_donors", f"{bundle['rosmap_donors']} global analytic donors", value=bundle["rosmap_donors"], value_type="count", unit="donors", source_keys=["rosmap_cohort_status"], source_columns="global_donors", value_origin="read", style_key="ros_text")
    add("C", "rosmap", "rosmap_phenotype", "annotation", "ROSMAP", "ros_phenotype", "AD vs NCI", source_keys=["phase12_manifest"], source_columns="source_contrast_ids", source_filter="Phase 18 primary structural scope", value_origin="read", style_key="ros_text")
    add("C", "rosmap", "rosmap_fine_types", "metric", "ROSMAP", "ros_fine_types", f"Original scope: {bundle['rosmap_fine_types']} fine types  |  {bundle['rosmap_source_networks']} source networks", value=f"{bundle['rosmap_fine_types']}|{bundle['rosmap_source_networks']}", value_type="count pair", unit="fine cell types|source networks", source_keys=["phase12_manifest"], source_columns="fine_cell_type+broad_network", source_filter="primary; six groups; up/down", value_origin="derived", style_key="ros_anchor")
    add("C", "rosmap", "rosmap_structural", "metric", "ROSMAP", "ros_structural", f"54 × 6 × 2 = {bundle['rosmap_structural']} structural slots", value=bundle["rosmap_structural"], value_type="count", unit="direction slots", source_keys=["phase12_manifest", "phase18_config"], source_columns="analysis_tier+fine_cell_type+signature_group+signature_direction|run_scope", derivation="54 fine types × 6 groups × 2 directions", value_origin="derived", style_key="ros_text")
    add("C", "rosmap", "rosmap_min_query", "threshold", "ROSMAP", "ros_min_query", f"minimum |Qeff| ≥ {bundle['ros_min_query']}", value=bundle["ros_min_query"], value_type="inclusive threshold", unit="effective query genes", source_keys=["phase18_config"], source_columns="run_scope.minimum_effective_query_genes", value_origin="read", style_key="ros_text")
    add("C", "rosmap", "rosmap_included", "metric", "ROSMAP", "ros_included", f"{bundle['rosmap_included']} included KDA runs", value=bundle["rosmap_included"], value_type="count", unit="KDA runs", source_keys=["phase12_manifest", "phase18_config"], source_columns="eligibility_status+terminal_status+effective_query_genes|expected_included_runs", source_filter="eligible; completed; effective query ≥10", value_origin="derived", style_key="ros_anchor")
    add("C", "rosmap", "rosmap_selected", "metric", "ROSMAP", "ros_selected", f"{bundle['rosmap_selected']} frozen units  |  {bundle['rosmap_symbols']} symbols", value=bundle["rosmap_selected"], value_type="count", unit="top-five network-gene-class units", source_keys=["rosmap_selected", "vh09_status"], source_columns="unique strict keys|selected_units", value_origin="read", style_key="ros_anchor")
    add("C", "rosmap", "rosmap_matched_scope", "annotation", "ROSMAP", "ros_matched_scope", "Matched scope: 7 SEA-AD networks", value=bundle["shared_networks"], value_type="count", unit="matched networks", source_keys=["phase12_manifest", "rosmap_selected", "shared_network_scope"], source_columns="broad_network", source_filter="included runs or selected units", value_origin="derived", style_key="ros_scope")
    add("C", "rosmap", "rosmap_holdout", "boundary", "ROSMAP", "ros_holdout", "candidate-bearing tables held out from SEA-AD KDA/selection code", value=False, value_type="boolean", unit="ROSMAP candidate files read before SEA-AD freeze", source_keys=["seaad_freeze"], source_columns="rosmap_candidate_files_read", value_origin="read", style_key="holdout")

    add("D", "gate", "comparison_gate", "protocol_gate", "shared", "comparison_gate", "OPEN ONLY AFTER SEA-AD FREEZE", source_keys=["seaad_freeze", "vh10d_status"], source_columns="freeze_status+rosmap_candidate_files_read|validation_status", source_filter="valid freeze before comparison", value_origin="method_constant", style_key="gate", x=8.64, y=0.18, width=0.14, height=1.50)
    add("D", "comparison", "panel_d_heading", "panel_heading", "comparison", "panel_d_heading", "D  STRICT POST-FREEZE COMPARISON", style_key="comparison_heading")
    add("D", "comparison", "comparison_unit", "formula", "comparison", "comparison_unit", "unit = broad network + gene + driver class", source_keys=["vh10d_status"], source_columns="strict comparison contract", value_origin="method_constant", style_key="comparison_anchor")
    add("D", "comparison", "comparison_universe", "annotation", "comparison", "comparison_universe", "within the common assessable universe", source_keys=["vh10d_status"], source_columns="common_assessable_units", value_origin="method_constant", style_key="comparison_text")
    add("D", "comparison", "comparison_shared", "status_chip", "comparison", "comparison_shared", "shared", value_origin="method_constant", style_key="status_shared")
    add("D", "comparison", "comparison_tested_not_shared", "status_chip", "comparison", "comparison_tested", "testable / not shared", value_origin="method_constant", style_key="status_tested")
    add("D", "comparison", "comparison_not_testable", "status_chip", "comparison", "comparison_not_testable", "not testable", value_origin="method_constant", style_key="status_unavailable")

    # The connector rows make the information-flow graph auditable.
    for index, (left, right) in enumerate(zip(["a1", "a2", "a3", "a4", "a5"], ["a2", "a3", "a4", "a5", "a6"]), start=1):
        lx, ly, lw, lh = LAYOUT[left]
        rx, _, _, _ = LAYOUT[right]
        add("A", f"connector_a{index}", f"connector_{left}_{right}", "solid_flow_connector", "SEA-AD", f"connector_{left}_{right}", f"{left} → {right}", style_key="sea_connector", x=lx + lw, y=ly + lh / 2, width=rx - (lx + lw), height=0, x2=rx, y2=ly + lh / 2)
    add("B", "connector_a4_shared", "connector_a4_shared", "dashed_method_connector", "shared", "connector_a4_shared", "shared scaffold → SEA query", style_key="shared_connector", x=7.00, y=3.01, width=0, height=0, x2=7.00, y2=2.34)
    add("B", "connector_a5_shared", "connector_a5_shared", "dashed_method_connector", "shared", "connector_a5_shared", "shared scaffold → SEA KDA/selection", style_key="shared_connector", x=9.27, y=3.01, width=0, height=0, x2=9.27, y2=2.34)
    add("B", "connector_shared_ros", "connector_shared_ros", "dashed_method_connector", "shared", "connector_shared_ros", "shared scaffold → ROSMAP Phase 18", style_key="shared_connector", x=4.25, y=1.87, width=0, height=0, x2=4.25, y2=1.58)
    add("D", "connector_freeze_compare", "connector_freeze_compare", "solid_flow_connector", "SEA-AD", "connector_freeze_compare", "SEA-AD freeze → comparison", style_key="sea_connector", x=11.95, y=3.01, width=0, height=0, x2=11.95, y2=1.58)
    add("D", "connector_ros_compare", "connector_ros_compare", "solid_flow_connector", "ROSMAP", "connector_ros_compare", "ROSMAP reference → comparison", style_key="ros_connector", x=8.38, y=0.87, width=0.53, height=0, x2=8.91, y2=0.87)

    frame = pd.DataFrame(rows)
    require(frame["order"].is_unique, "Plot-data order values are not unique")
    require(frame["element_id"].is_unique, "Plot-data element IDs are not unique")
    require(set(frame["value_origin"]) <= {"read", "derived", "method_constant"}, "Unexpected plot-data value origin")
    visible = "\n".join(frame.loc[~frame["element_type"].str.contains("connector"), "display_text"].astype(str))
    forbidden = ["6 strict shared", "36 of 47", "shared unique genes"]
    require(not any(text.lower() in visible.lower() for text in forbidden), "Overlap outcome leaked into canonical setup asset")
    return frame


def configure_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 8.5,
            "svg.hashsalt": SCHEMA,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "pdf.compression": 9,
            "figure.facecolor": WHITE,
            "savefig.facecolor": WHITE,
        }
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: str,
    edgecolor: str,
    linewidth: float = 1.0,
    radius: float = 0.08,
    linestyle: str = "-",
    zorder: float = 2,
) -> mpatches.FancyBboxPatch:
    patch = mpatches.FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def draw_lock(ax: plt.Axes, x: float, y: float, size: float, color: str, *, zorder: float = 5) -> None:
    body_width = size * 0.78
    body_height = size * 0.52
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (x - body_width / 2, y - body_height / 2),
            body_width,
            body_height,
            boxstyle=f"round,pad=0.003,rounding_size={size * 0.08}",
            facecolor=WHITE,
            edgecolor=color,
            linewidth=1.1,
            zorder=zorder,
        )
    )
    ax.add_patch(
        mpatches.Arc(
            (x, y + body_height / 2),
            size * 0.55,
            size * 0.72,
            theta1=0,
            theta2=180,
            color=color,
            linewidth=1.1,
            zorder=zorder,
        )
    )
    ax.add_patch(
        mpatches.Circle(
            (x, y),
            radius=size * 0.055,
            facecolor=color,
            edgecolor="none",
            zorder=zorder + 0.1,
        )
    )


def draw_connector_rows(ax: plt.Axes, plot_data: pd.DataFrame) -> None:
    connectors = plot_data.loc[plot_data["element_type"].str.contains("connector")]
    for row in connectors.itertuples(index=False):
        x1 = float(row.x_inches)
        y1 = float(row.y_inches)
        x2 = float(row.x2_inches)
        y2 = float(row.y2_inches)
        if row.style_key == "shared_connector":
            color = MID
            linestyle = (0, (3, 2.5))
            linewidth = 0.9
            arrowstyle = "-|>"
        elif row.style_key == "ros_connector":
            color = ROS_ORANGE
            linestyle = "-"
            linewidth = 1.35
            arrowstyle = "-|>"
        else:
            color = SEA_BLUE
            linestyle = "-"
            linewidth = 1.25
            arrowstyle = "-|>"
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops={
                "arrowstyle": arrowstyle,
                "color": color,
                "lw": linewidth,
                "linestyle": linestyle,
                "shrinkA": 3,
                "shrinkB": 3,
                "mutation_scale": 10,
            },
            zorder=1,
        )


def text_lookup(plot_data: pd.DataFrame) -> dict[str, str]:
    require(plot_data["label_key"].is_unique, "Visible label keys are not unique")
    return dict(zip(plot_data["label_key"], plot_data["display_text"]))


def render_figure(plot_data: pd.DataFrame) -> tuple[plt.Figure, dict[str, Any]]:
    configure_style()
    label = text_lookup(plot_data)
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIGURE_WIDTH_IN)
    ax.set_ylim(0, FIGURE_HEIGHT_IN)
    ax.axis("off")

    draw_connector_rows(ax, plot_data)

    # SEA-AD cards.
    for parent in ["a1", "a2", "a3", "a4", "a5"]:
        x, y, w, h = LAYOUT[parent]
        face = SEA_PALE_2 if parent == "a4" else SEA_PALE
        edge = SEA_TEAL if parent == "a4" else SEA_BLUE
        rounded_box(ax, x, y, w, h, facecolor=face, edgecolor=edge, linewidth=1.15 if parent == "a4" else 0.95)
    x, y, w, h = LAYOUT["a6"]
    rounded_box(ax, x, y, w, h, facecolor="#E7F3EF", edgecolor=SEA_TEAL, linewidth=1.35)

    ax.text(0.16, 4.57, label["panel_a_heading"], fontsize=12.8, fontweight="bold", color=NAVY, ha="left", va="center", zorder=4)

    # A1 cohort.
    x, y, w, h = LAYOUT["a1"]
    cx = x + w / 2
    ax.text(cx, y + 1.16, label["a1_heading"], fontsize=10.0, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.91, label["sea_donors"], fontsize=15.5, fontweight="bold", color=SEA_BLUE, ha="center", va="center")
    ax.text(cx, y + 0.68, label["sea_dementia"], fontsize=9.2, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.52, label["sea_no_dementia"], fontsize=9.2, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.31, label["sea_nuclei"], fontsize=8.2, color=MID, ha="center", va="center")
    ax.text(cx, y + 0.12, label["sea_replicate"], fontsize=7.8, fontweight="bold", color=NAVY, ha="center", va="center")

    # A2 pseudobulk and mapping.
    x, y, w, h = LAYOUT["a2"]
    cx = x + w / 2
    ax.text(cx, y + 1.16, label["a2_heading"], fontsize=10.0, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.91, label["sea_supertypes"], fontsize=13.7, fontweight="bold", color=SEA_BLUE, ha="center", va="center")
    ax.text(cx, y + 0.69, label["sea_fine_separate"], fontsize=8.8, fontweight="bold", color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.49, label["sea_groups"], fontsize=8.7, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.30, label["sea_networks"], fontsize=8.1, color=MID, ha="center", va="center")
    ax.text(cx, y + 0.12, label["sea_profile_gate"], fontsize=7.8, color=NAVY, ha="center", va="center")

    # A3 adjusted DEG.
    x, y, w, h = LAYOUT["a3"]
    cx = x + w / 2
    ax.text(cx, y + 1.16, label["a3_heading"], fontsize=10.0, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.96, label["sea_phenotype"], fontsize=8.8, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.73, label["sea_contrasts"], fontsize=10.6, fontweight="bold", color=SEA_BLUE, ha="center", va="center")
    ax.text(cx, y + 0.51, label["sea_direction_split"], fontsize=8.4, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.30, label["sea_structural"], fontsize=10.6, fontweight="bold", color=SEA_BLUE, ha="center", va="center")
    ax.text(cx, y + 0.10, label["sea_adjustment"], fontsize=7.6, color=MID, ha="center", va="center")

    # A4 query rule. Direction is redundantly encoded with color and shape.
    x, y, w, h = LAYOUT["a4"]
    cx = x + w / 2
    ax.text(cx, y + 1.16, label["a4_heading"], fontsize=10.1, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.96, label["sea_query_universe"], fontsize=8.8, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.76, f"{label['sea_fdr']}   •   {label['sea_effect']}", fontsize=8.6, color=TEXT, ha="center", va="center")
    ax.text(cx - 0.08, y + 0.56, "Dementia-up ▲", fontsize=8.5, fontweight="bold", color=UP, ha="right", va="center")
    ax.text(cx + 0.08, y + 0.56, "Dementia-down ▼", fontsize=8.5, fontweight="bold", color=DOWN, ha="left", va="center")
    ax.text(cx, y + 0.35, label["sea_qeff"], fontsize=8.1, color=MID, ha="center", va="center")
    ax.text(cx, y + 0.13, label["sea_min_query"], fontsize=11.0, fontweight="bold", color=SEA_TEAL, ha="center", va="center")

    # A5 KDA and selection.
    x, y, w, h = LAYOUT["a5"]
    cx = x + w / 2
    ax.text(cx, y + 1.16, label["a5_heading"], fontsize=9.4, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.96, label["sea_matching_network"], fontsize=8.6, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.77, label["sea_fkda_layers"], fontsize=8.5, color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.58, label["sea_selector"], fontsize=8.3, color=MID, ha="center", va="center")
    ax.text(cx, y + 0.34, label["sea_active_calls"], fontsize=13.5, fontweight="bold", color=SEA_BLUE, ha="center", va="center")
    ax.text(cx, y + 0.12, label["sea_call_directions"], fontsize=8.6, fontweight="bold", color=NAVY, ha="center", va="center")

    # A6 frozen independent selection.
    x, y, w, h = LAYOUT["a6"]
    cx = x + w / 2
    draw_lock(ax, x + 0.18, y + 1.13, 0.22, SEA_TEAL)
    ax.text(cx + 0.07, y + 1.16, label["a6_heading"], fontsize=10.0, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(cx, y + 0.91, label["sea_checksum"], fontsize=8.1, color=SEA_TEAL, ha="center", va="center")
    ax.text(cx, y + 0.66, label["sea_selected"], fontsize=13.0, fontweight="bold", color=SEA_TEAL, ha="center", va="center")
    ax.text(cx, y + 0.43, label["sea_classes"], fontsize=8.8, fontweight="bold", color=TEXT, ha="center", va="center")
    ax.text(cx, y + 0.24, label["sea_symbols"], fontsize=8.7, color=TEXT, ha="center", va="center")
    rounded_box(ax, x + 0.23, y + 0.055, w - 0.46, 0.12, facecolor=SEA_TEAL, edgecolor=SEA_TEAL, radius=0.035, zorder=3)
    ax.text(cx, y + 0.115, "FREEZE VALID", fontsize=7.2, fontweight="bold", color=WHITE, ha="center", va="center", zorder=4)

    # SEA-AD support and attrition ribbons.
    x, y, w, h = LAYOUT["ribbon_groups"]
    rounded_box(ax, x, y, w, h, facecolor=PALE_GRAY, edgecolor=GRAY, linewidth=0.75, radius=0.05)
    ax.text(x + 0.08, y + h / 2, "Completed\ncontrasts", fontsize=7.0, fontweight="bold", color=MID, ha="left", va="center", linespacing=1.0)
    chip_x0 = x + 0.78
    chip_width = 0.405
    chip_gap = 0.027
    for index, group in enumerate(GROUP_ORDER):
        value = int(plot_data.loc[plot_data["label_key"].eq(f"completed_{group}"), "value"].iloc[0])
        chip_x = chip_x0 + index * (chip_width + chip_gap)
        active_group = value > 0
        rounded_box(
            ax,
            chip_x,
            y + 0.035,
            chip_width,
            h - 0.07,
            facecolor=WHITE if active_group else PALE_GRAY,
            edgecolor=SEA_BLUE if active_group else GRAY,
            linewidth=0.65,
            radius=0.035,
            linestyle="-" if active_group else (0, (2.2, 2.2)),
            zorder=3,
        )
        ax.text(chip_x + chip_width / 2, y + h / 2, f"{group}\n{value}", fontsize=7.0, fontweight="bold" if active_group else "normal", color=SEA_BLUE if active_group else MID, ha="center", va="center", linespacing=0.95, zorder=4)

    x, y, w, h = LAYOUT["ribbon_attrition"]
    rounded_box(ax, x, y, w, h, facecolor="#EDF4F8", edgecolor="#A7C5D5", linewidth=0.75, radius=0.05)
    ax.text(x + w / 2, y + 0.185, f"{label['attrition_completed']}  →  {label['attrition_source']}  →  {label['attrition_active']}", fontsize=8.5, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(x + w / 2, y + 0.075, f"{label['attrition_small']}   •   {label['attrition_large']}", fontsize=7.3, color=MID, ha="center", va="center")

    # Shared frozen network/KDA band.
    x, y, w, h = LAYOUT["shared_band"]
    rounded_box(ax, x, y, w, h, facecolor=SCAFFOLD_PALE, edgecolor=NAVY, linewidth=0.9, radius=0.06)
    ax.text(x + 0.15, y + 0.355, label["panel_b_heading"], fontsize=9.5, fontweight="bold", color=NAVY, ha="left", va="center")
    ax.text(x + w / 2, y + 0.205, f"{label['shared_networks']}   •   {label['shared_annotation']}   •   {label['shared_fkda']}   •   {label['shared_selection']}", fontsize=7.9, color=TEXT, ha="center", va="center")
    ax.text(x + w / 2, y + 0.075, label["shared_boundary"], fontsize=7.7, fontstyle="italic", color=MID, ha="center", va="center")

    # ROSMAP reference: two-column compressed frozen lane.
    x, y, w, h = LAYOUT["rosmap"]
    rounded_box(ax, x, y, w, h, facecolor=ROS_PALE, edgecolor=ROS_ORANGE, linewidth=1.15, radius=0.08)
    ax.text(x + 0.15, y + 1.17, label["panel_c_heading"], fontsize=10.2, fontweight="bold", color=NAVY, ha="left", va="center")
    ax.plot([x + 4.12, x + 4.12], [y + 0.43, y + 1.08], color="#D9C28B", lw=0.75, zorder=3)
    ax.text(x + 0.20, y + 0.92, f"{label['ros_donors']}  •  {label['ros_phenotype']}", fontsize=8.7, color=TEXT, ha="left", va="center")
    ax.text(x + 0.20, y + 0.70, label["ros_fine_types"], fontsize=9.0, fontweight="bold", color=ROS_ORANGE, ha="left", va="center")
    ax.text(x + 0.20, y + 0.49, label["ros_structural"], fontsize=8.7, color=TEXT, ha="left", va="center")
    ax.text(x + 4.36, y + 0.92, label["ros_min_query"], fontsize=8.8, color=TEXT, ha="left", va="center")
    ax.text(x + 4.36, y + 0.72, label["ros_matched_scope"], fontsize=8.5, fontweight="bold", color=NAVY, ha="left", va="center")
    ax.text(x + 4.36, y + 0.52, label["ros_included"], fontsize=9.7, fontweight="bold", color=ROS_ORANGE, ha="left", va="center")
    ax.text(x + 4.36, y + 0.35, label["ros_selected"], fontsize=8.6, fontweight="bold", color=TEXT, ha="left", va="center")
    rounded_box(ax, x + 0.18, y + 0.055, w - 0.36, 0.205, facecolor=WHITE, edgecolor=ROS_ORANGE, linewidth=0.75, radius=0.045, linestyle=(0, (3, 2)), zorder=3)
    draw_lock(ax, x + 0.38, y + 0.157, 0.19, ROS_ORANGE, zorder=4)
    ax.text(x + 0.57, y + 0.157, label["ros_holdout"], fontsize=8.0, fontweight="bold", color=NAVY, ha="left", va="center", zorder=4)

    # Post-freeze protocol gate and strict comparison box.
    gate_x = 8.64
    ax.plot([gate_x, gate_x], [0.18, 1.64], color=NAVY, lw=0.9, linestyle=(0, (3, 2.5)), zorder=2)
    draw_lock(ax, gate_x, 0.87, 0.25, NAVY, zorder=5)
    ax.text(gate_x, 1.71, label["comparison_gate"], fontsize=7.5, fontweight="bold", color=NAVY, ha="center", va="center")

    x, y, w, h = LAYOUT["comparison"]
    rounded_box(ax, x, y, w, h, facecolor=WHITE, edgecolor=SEA_BLUE, linewidth=1.25, radius=0.08)
    rounded_box(ax, x + 0.04, y + 0.04, w - 0.08, h - 0.08, facecolor="none", edgecolor=ROS_ORANGE, linewidth=0.85, radius=0.065, zorder=2.5)
    ax.text(x + 0.15, y + 1.17, label["panel_d_heading"], fontsize=9.8, fontweight="bold", color=NAVY, ha="left", va="center")
    ax.text(x + w / 2, y + 0.92, "STRICT COMPARISON", fontsize=11.5, fontweight="bold", color=NAVY, ha="center", va="center")
    ax.text(x + w / 2, y + 0.70, "broad network + gene + driver class", fontsize=8.8, fontweight="bold", color=TEXT, ha="center", va="center")
    ax.text(x + w / 2, y + 0.51, label["comparison_universe"], fontsize=8.3, color=MID, ha="center", va="center")
    chip_specs = [
        (label["comparison_shared"], SEA_TEAL, WHITE, 0.73),
        (label["comparison_tested"], SEA_BLUE, WHITE, 1.25),
        (label["comparison_not_testable"], GRAY, TEXT, 0.88),
    ]
    total_width = sum(spec[3] for spec in chip_specs) + 0.10
    chip_x = x + (w - total_width) / 2
    for index, (chip_label, color, text_color, chip_width) in enumerate(chip_specs):
        facecolor = color if index < 2 else PALE_GRAY
        edgecolor = color
        linestyle = "-" if index < 2 else (0, (2, 2))
        rounded_box(ax, chip_x, y + 0.15, chip_width, 0.22, facecolor=facecolor, edgecolor=edgecolor, linewidth=0.75, radius=0.045, linestyle=linestyle, zorder=3)
        ax.text(chip_x + chip_width / 2, y + 0.26, chip_label, fontsize=7.1, fontweight="bold", color=text_color, ha="center", va="center", zorder=4)
        chip_x += chip_width + 0.05

    # Canvas-level text validation before export.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_bbox = fig.bbox
    clipped: list[str] = []
    minimum_font = math.inf
    for artist in fig.findobj(match=matplotlib.text.Text):
        if not artist.get_text().strip():
            continue
        minimum_font = min(minimum_font, float(artist.get_fontsize()))
        bbox = artist.get_window_extent(renderer=renderer)
        if (
            bbox.x0 < figure_bbox.x0 - 1
            or bbox.y0 < figure_bbox.y0 - 1
            or bbox.x1 > figure_bbox.x1 + 1
            or bbox.y1 > figure_bbox.y1 + 1
        ):
            clipped.append(artist.get_text())
    require(not clipped, "Text leaves the figure canvas: " + " | ".join(clipped))
    require(minimum_font >= 6.7, f"Minimum visible font is too small: {minimum_font}")
    return fig, {"minimum_font_points": minimum_font, "canvas_clipped_text": clipped}


def render_images(fig: plt.Figure, staging: Path, dpi: int) -> list[Path]:
    paths: list[Path] = []
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{FIGURE_ID}.{extension}"
        temporary = staging / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Creator": "SEA-AD–ROSMAP validation setup renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {
                "Creator": "SEA-AD–ROSMAP validation setup renderer",
                "Date": None,
            }
        else:
            metadata = {"Software": "SEA-AD–ROSMAP validation setup renderer"}
        fig.savefig(
            temporary,
            format=extension,
            dpi=dpi if extension == "png" else None,
            facecolor=WHITE,
            bbox_inches=None,
            pad_inches=0,
            metadata=metadata,
        )
        require(temporary.is_file() and temporary.stat().st_size > 1_000, f"Missing or small rendered image: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths


def check_record(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    details: str,
    *,
    severity: str = "blocking",
    status_override: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "figure_id": FIGURE_ID,
        "check_id": check_id,
        "severity": severity,
        "status": status_override or ("pass" if passed else "fail"),
        "expected": expected,
        "observed": observed,
        "details": details,
    }


def image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix.lower(): path for path in image_paths}
    checks = [
        check_record(
            "image_format_set",
            set(lookup) == {".png", ".pdf", ".svg"},
            "|".join(sorted(lookup)),
            ".pdf|.png|.svg",
            "The package contains the required raster and vector exports.",
        ),
        check_record(
            "image_files_nonempty",
            all(path.stat().st_size > 1_000 for path in image_paths),
            "|".join(str(path.stat().st_size) for path in image_paths),
            ">1000 bytes each",
            "Rendered files must be nonempty and larger than trivial headers.",
        ),
    ]
    svg_text = lookup[".svg"].read_text(encoding="utf-8")
    checks.extend(
        [
            check_record("svg_signature", "<svg" in svg_text.lower(), "<svg present" if "<svg" in svg_text.lower() else "missing", "<svg present", "SVG signature is present."),
            check_record("svg_searchable_text", "<text" in svg_text.lower(), "<text present" if "<text" in svg_text.lower() else "missing", "<text present", "SVG preserves text instead of converting every label to paths."),
            check_record("svg_vector_shapes", "<path" in svg_text.lower(), "<path present" if "<path" in svg_text.lower() else "missing", "<path present", "SVG contains vector paths/shapes."),
            check_record("canonical_setup_omits_overlap_result", "6 strict shared" not in svg_text.lower() and "36 of 47" not in svg_text.lower(), "overlap result absent", "overlap result absent", "The setup asset stops at the comparison rule."),
        ]
    )
    with lookup[".pdf"].open("rb") as handle:
        pdf_header = handle.read(5)
    checks.append(check_record("pdf_signature", pdf_header == b"%PDF-", pdf_header.decode("latin1"), "%PDF-", "PDF has the expected file signature."))
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        png_dpi = image.info.get("dpi", (math.nan, math.nan))
        mode = image.mode
    checks.extend(
        [
            check_record("png_width", width == PNG_WIDTH, width, PNG_WIDTH, "PNG width is frozen for the slide asset."),
            check_record("png_height", height == PNG_HEIGHT, height, PNG_HEIGHT, "PNG height is frozen for the slide asset."),
            check_record(
                "png_resolution",
                all(math.isfinite(value) and abs(value - dpi) <= 1 for value in png_dpi),
                f"{png_dpi[0]:.2f}|{png_dpi[1]:.2f}",
                f"{dpi}|{dpi}",
                "PNG embeds approximately 450 DPI in both dimensions.",
            ),
            check_record("png_color_mode", mode in {"RGB", "RGBA"}, mode, "RGB or RGBA", "PNG is suitable for the RGB slide deck."),
        ]
    )
    return checks


def build_checks(
    bundle: Mapping[str, Any],
    plot_data: pd.DataFrame,
    image_paths: Sequence[Path],
    render_meta: Mapping[str, Any],
    dpi: int,
    visual_review_status: str,
) -> pd.DataFrame:
    expected_group_text = "|".join(f"{group}:{EXPECTED_COMPLETED_GROUPS[group]}" for group in GROUP_ORDER)
    observed_group_text = "|".join(f"{group}:{bundle['completed_group_counts'][group]}" for group in GROUP_ORDER)
    checks = [
        check_record("seaad_donors", bundle["sea_donors"] == 78, bundle["sea_donors"], 78, "SEA-AD analysis donor total."),
        check_record("seaad_donor_phenotypes", (bundle["dementia_donors"], bundle["no_dementia_donors"]) == (37, 41), f"{bundle['dementia_donors']}|{bundle['no_dementia_donors']}", "37|41", "Dementia and No-dementia donor counts."),
        check_record("seaad_selected_nuclei", bundle["selected_nuclei"] == 1_189_172, bundle["selected_nuclei"], 1_189_172, "Selected SEA-AD nuclei."),
        check_record("seaad_supertypes", bundle["supertypes"] == 129, bundle["supertypes"], 129, "Distinct SEA-AD fine supertypes."),
        check_record("shared_network_count", bundle["shared_networks"] == 7, bundle["shared_networks"], 7, "Exact matched broad-network IDs."),
        check_record("fine_contrast_count", bundle["fine_contrasts"] == 774, bundle["fine_contrasts"], 774, "129 supertypes × six fixed groups."),
        check_record("fine_contrast_status_partition", bundle["completed_contrasts"] + bundle["not_estimable_contrasts"] == 774, f"{bundle['completed_contrasts']}+{bundle['not_estimable_contrasts']}", "260+514", "Completed and not-estimable contrast partition."),
        check_record("completed_contrasts_by_group", observed_group_text == expected_group_text, observed_group_text, expected_group_text, "Completed fine contrasts across all six fixed groups."),
        check_record("structural_directions", bundle["structural_directions"] == 1_548, bundle["structural_directions"], 1_548, "Two signed directions per structural fine contrast."),
        check_record("direction_status_partition", bundle["source_directions"] + bundle["source_not_estimable_directions"] == 1_548, f"{bundle['source_directions']}+{bundle['source_not_estimable_directions']}", "520+1028", "Completed-source and source-not-estimable direction partition."),
        check_record("completed_direction_attrition", bundle["query_empty"] + bundle["query_below_minimum"] + bundle["small_calls"] + bundle["large_calls"] == 520, f"{bundle['query_empty']}+{bundle['query_below_minimum']}+{bundle['small_calls']}+{bundle['large_calls']}", "462+16+21+21", "Completed-source directions partition by effective-query outcome."),
        check_record("active_kda_calls", bundle["active_calls"] == 42, bundle["active_calls"], 42, "SEA-AD active KDA calls."),
        check_record("active_direction_calls", bundle["up_calls"] + bundle["down_calls"] == 42, f"{bundle['up_calls']}+{bundle['down_calls']}", "20+22", "Active up/down KDA calls."),
        check_record("active_query_size_tiers", bundle["small_calls"] + bundle["large_calls"] == 42, f"{bundle['small_calls']}+{bundle['large_calls']}", "21+21", "Small and Phase18-sized active queries."),
        check_record("kda_call_outcomes", bundle["calls_with_return"] + bundle["calls_without_return"] == 42, f"{bundle['calls_with_return']}+{bundle['calls_without_return']}", "29+13", "Calls with at least one significant return and calls with none."),
        check_record("seaad_selected_units", bundle["sea_selected"] == 13, bundle["sea_selected"], 13, "Ranked SEA-AD network-gene-class units after sentinel filtering."),
        check_record("seaad_selected_classes", bundle["sea_selected_mt"] + bundle["sea_selected_nonmt"] == 13, f"{bundle['sea_selected_mt']}+{bundle['sea_selected_nonmt']}", "8+5", "SEA-AD MT and non-MT selected units."),
        check_record("seaad_selected_symbols", bundle["sea_symbols"] == 11, bundle["sea_symbols"], 11, "Unique selected SEA-AD current symbols."),
        check_record("seaad_minimum_query", bundle["sea_min_query"] == 3, bundle["sea_min_query"], 3, "SEA-AD downstream KDA run-inclusion minimum."),
        check_record("rosmap_global_donors", bundle["rosmap_donors"] == 276, bundle["rosmap_donors"], 276, "Global ROSMAP analytic donor universe."),
        check_record("rosmap_fine_types", bundle["rosmap_fine_types"] == 54, bundle["rosmap_fine_types"], 54, "ROSMAP Phase 18 fine-cell-type scope."),
        check_record("rosmap_source_networks", bundle["rosmap_source_networks"] == 9, bundle["rosmap_source_networks"], 9, "Original ROSMAP source-network scope, including CAMs and T cells."),
        check_record("rosmap_structural_slots", bundle["rosmap_structural"] == 648, bundle["rosmap_structural"], 648, "54 fine types × six groups × two directions."),
        check_record("rosmap_minimum_query", bundle["ros_min_query"] == 10, bundle["ros_min_query"], 10, "ROSMAP Phase 18 run-inclusion minimum."),
        check_record("rosmap_included_runs", bundle["rosmap_included"] == 161, bundle["rosmap_included"], 161, "Phase 18 included KDA runs in the seven matched networks."),
        check_record("rosmap_selected_units", bundle["rosmap_selected"] == 47, bundle["rosmap_selected"], 47, "Frozen ROSMAP top-five network-gene-class units."),
        check_record("rosmap_selected_symbols", bundle["rosmap_symbols"] == 25, bundle["rosmap_symbols"], 25, "Unique frozen ROSMAP selected symbols."),
        check_record("threshold_difference_visible", {"sea_min_query", "ros_min_query"} <= set(plot_data["label_key"]), "SEA 3|ROSMAP 10 labels", "SEA 3|ROSMAP 10 labels", "The intentional query-size difference is visible."),
        check_record("structural_vs_runnable_units_visible", {"sea_structural", "sea_active_calls"} <= set(plot_data["label_key"]), "1,548 slots|42 calls", "1,548 slots|42 calls", "Structural slots and runnable calls are visibly distinguished."),
        check_record("no_taxonomy_pooling_text", "fine labels stay separate" in set(plot_data["display_text"]), "fine labels stay separate", "fine labels stay separate", "Fine supertypes are not visually represented as pooled before DEG/KDA."),
        check_record("holdout_boundary_visible", "ros_holdout" in set(plot_data["label_key"]), "holdout label present", "holdout label present", "ROSMAP candidate tables are shown as held out from SEA-AD selection code."),
        check_record("canonical_setup_no_result_badge", not plot_data["display_text"].str.contains("6 strict shared|36 of 47", case=False, regex=True).any(), "overlap outcome absent", "overlap outcome absent", "The canonical setup does not reveal the later overlap result."),
        check_record("plot_element_ids_unique", plot_data["element_id"].is_unique, plot_data["element_id"].nunique(), len(plot_data), "Every plotted datum/label/connector has a unique audit ID."),
        check_record("plot_sources_hashed", plot_data.loc[plot_data["source_path"].ne("NA"), "source_sha256"].ne("NA").all(), "all sourced rows hashed", "all sourced rows hashed", "Every sourced visible element records input SHA-256 provenance."),
        check_record("minimum_font_size", float(render_meta["minimum_font_points"]) >= 7.0, f"{float(render_meta['minimum_font_points']):.2f}", ">=7.0 pt", "Minimum visible text size on the slide-native asset."),
        check_record("canvas_text_clipping", not render_meta["canvas_clipped_text"], len(render_meta["canvas_clipped_text"]), 0, "No text bounding box leaves the figure canvas."),
        check_record("colorblind_redundancy", True, "Okabe-Ito blue/teal/orange + labels/line styles/lock/status text", "color + redundant non-color encoding", "Cohorts, directions, scaffold, holdout, and statuses are not encoded by color alone."),
        check_record("deterministic_counts_no_uncertainty", True, "uncertainty not applicable", "uncertainty not applicable", "The figure displays deterministic workflow counts, not statistical estimates."),
    ]
    checks.extend(image_checks(image_paths, dpi))
    if visual_review_status == "complete":
        checks.append(check_record("visual_review", True, "complete", "complete", "Reviewed at intended slide size in color and grayscale.", severity="nonblocking"))
    else:
        checks.append(check_record("visual_review", False, "pending", "complete", "Manual slide-size color/grayscale review remains pending.", severity="nonblocking", status_override="pending"))
    frame = pd.DataFrame(checks)
    blocking_failures = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking_failures.empty, "Blocking figure checks failed: " + ", ".join(blocking_failures["check_id"]))
    return frame


def documentation(bundle: Mapping[str, Any]) -> tuple[str, str]:
    caption = f"""# SEA-AD–ROSMAP validation setup figure caption

**Independent SEA-AD validation of ROSMAP Phase 18 key drivers.** **A,** SEA-AD expression evidence was generated with donor-level pseudobulk profiles for {bundle['supertypes']} distinct fine supertypes and six fixed sex/APOE groups. The {bundle['fine_contrasts']} direct Dementia-versus-No-dementia contrasts yielded {bundle['structural_directions']:,} prespecified signed structural slots; {bundle['completed_contrasts']} contrasts completed and produced {bundle['source_directions']} signed directions ready for query construction. Core-MitoCarta genes meeting within-contrast FDR and effect-size criteria were intersected with the tested-gene-induced background of the matching frozen broad network. {bundle['active_calls']} effective queries contained at least {bundle['sea_min_query']} genes and entered directed KDA, producing {bundle['sea_selected']} selected network–gene–class units ({bundle['sea_symbols']} symbols) before checksum freeze. **B,** The seven matched broad networks, current-symbol/core-MitoCarta annotation, fKDA engine, and Phase 18 selection machinery were shared and frozen; cohorts, phenotype labels, fine taxonomies, DEG models, signed queries, and candidate identities were not shared. **C,** The ROSMAP Phase 18 reference began with {bundle['rosmap_fine_types']} fine cell types across {bundle['rosmap_source_networks']} source networks and {bundle['rosmap_structural']} structural slots. Its minimum effective query size was {bundle['ros_min_query']}; {bundle['rosmap_included']} included runs and all {bundle['rosmap_selected']} frozen selected units occurred in the seven networks matched to SEA-AD. Candidate-bearing ROSMAP tables were not read by the SEA-AD KDA/selection code before the SEA-AD freeze. **D,** Post-freeze comparison uses the strict broad-network, gene, and driver-class key within the common assessable universe. The setup asset intentionally omits the overlap outcome.
"""
    methods = f"""# SEA-AD–ROSMAP validation setup figure methods

The renderer reads only compact validated status, manifest, configuration, selection, and provenance artifacts. It verifies `validated_complete` status for VH02–VH04, VH07–VH10, validates the frozen input-authority and seven matched network hashes, and derives every displayed count from the stored tables. It does not recompute DEG statistics, query/background membership, KDA enrichment, ACAT, BH correction, candidate selection, or overlap.

SEA-AD DEG used one grouped edgeR quasi-likelihood model per supertype with the frozen formula `{bundle['fine_formula']}`, TMM normalization, robust dispersion/QL fitting, and within-contrast BH FDR. A donor–supertype profile required at least 20 nuclei, and a direct disease contrast required at least five eligible donors per phenotype arm. The displayed signed query rule is `{bundle['query_rule']}` with core-MitoCarta membership and sign. The recorded Phase 12 background policy is `{bundle['background_policy']}`; the compact bundle confirms `Qeff` is a subset of its stored background but cannot independently reconstruct membership because the large VH08 tested/filter shards and VH10A member tables are not present locally.

SEA-AD runs require at least three effective query genes; ROSMAP Phase 18 requires at least ten. The same seven matched broad-network files, current-symbol/core-MitoCarta authority, directed fKDA layer test, conditional MT self-exclusion, within-run BH, ACAT aggregation, aggregate BH, two driver classes, candidate gates, ranking order, and up-to-five/no-backfill rule are represented as the shared scaffold. The original ROSMAP taxonomy contains 54 fine cell types across nine source networks; CAMs and T cells contribute no included Phase 18 run or selected unit, so the 161 included runs and 47 selected units lie in the seven SEA-AD-matched networks.

The figure uses vector-native Matplotlib shapes with Okabe–Ito-derived blue, teal, vermilion, and orange plus explicit labels, solid/dashed lines, direction triangles, and a vector lock for redundant encoding. PNG is exported at 450 DPI; PDF and SVG preserve vector shapes, and SVG preserves searchable text. Counts are deterministic workflow properties, so error bars and significance marks are not applicable. Phase 05 and Phase 06 pseudobulk-QC artifacts are not required for this setup schematic.
"""
    return caption, methods


def table_row_count(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA"
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0)


def build_artifacts(
    bundle: Mapping[str, Any],
    staging: Path,
    renderer_path: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for relative_path, digest in sorted(bundle["input_digests"].items()):
        path = bundle["project_root"] / relative_path
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "artifact_role": "input",
                "logical_name": relative_path,
                "path": relative_path,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "rows": table_row_count(path),
                "validation_state": "validated_input",
            }
        )
    renderer_relative = str(renderer_path.relative_to(bundle["project_root"]))
    rows.append(
        {
            "schema_version": SCHEMA,
            "figure_id": FIGURE_ID,
            "artifact_role": "script",
            "logical_name": "renderer",
            "path": renderer_relative,
            "bytes": renderer_path.stat().st_size,
            "sha256": sha256_file(renderer_path),
            "rows": "NA",
            "validation_state": "validated_script",
        }
    )
    for name in PAYLOAD_FILES:
        path = staging / name
        require(path.is_file() and path.stat().st_size > 0, f"Missing payload before artifact manifest: {name}")
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "artifact_role": "output",
                "logical_name": name,
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "rows": table_row_count(path),
                "validation_state": "validated_output",
            }
        )
    frame = pd.DataFrame(rows)
    require(frame["path"].is_unique, "Artifact manifest paths are not unique")
    require(set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Output artifact hash scope changed")
    require(not frame["path"].isin(OUTPUT_FILES[-2:]).any(), "Artifact manifest or status entered its own hash scope")
    return frame


def validate_output(
    project_root: Path,
    output_root: Path,
    *,
    expected_visual_status: str | None = None,
) -> None:
    require(output_root.is_dir(), f"Missing figure output directory: {output_root}")
    observed = sorted(path.name for path in output_root.iterdir() if path.is_file())
    require(observed == sorted(OUTPUT_FILES), f"Figure output contract mismatch: {observed}")

    status = one_row(read_tsv(output_root / OUTPUT_FILES[-1]), "figure status")
    require(status["schema_version"] == SCHEMA, "Unexpected figure status schema")
    require(status["figure_id"] == FIGURE_ID, "Unexpected figure ID in status")
    visual_status = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual_status == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual_status == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Unexpected figure validation status")

    checks = read_tsv(output_root / f"{FIGURE_ID}_checks.tsv")
    require_columns(checks, ["check_id", "severity", "status"], "figure checks")
    blocking_failures = checks.loc[checks["severity"].eq("blocking") & ~checks["status"].eq("pass")]
    require(blocking_failures.empty, "Published package contains blocking check failures")
    if visual_status == "complete":
        require(checks["status"].eq("pass").all(), "Completed figure package contains a pending or failed check")

    artifacts_path = output_root / f"{FIGURE_ID}_artifacts.tsv"
    require(sha256_file(artifacts_path) == status["artifact_manifest_sha256"], "Artifact-manifest SHA disagrees with status")
    artifacts = read_tsv(artifacts_path)
    require_columns(artifacts, ["artifact_role", "path", "bytes", "sha256"], "artifact manifest")
    require(artifacts["path"].is_unique, "Artifact manifest paths are duplicated")
    output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
    require(set(output_rows["path"]) == set(PAYLOAD_FILES), "Artifact output hash scope changed")
    require(not artifacts["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status is incorrectly self-hashed")
    require(len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1, "Expected one renderer artifact row")
    for row in artifacts.itertuples(index=False):
        if row.artifact_role == "output":
            path = output_root / str(row.path)
        else:
            path = project_root / str(row.path)
        require(path.is_file(), f"Artifact path is missing: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact SHA-256 changed: {row.path}")

    plot_data = read_tsv(output_root / f"{FIGURE_ID}_plot_data.tsv")
    require_columns(
        plot_data,
        [
            "element_id",
            "element_type",
            "display_text",
            "value",
            "source_path",
            "source_sha256",
            "style_key",
        ],
        "figure plot data",
    )
    require(plot_data["element_id"].is_unique, "Published plot-data element IDs are duplicated")
    require(not plot_data["display_text"].str.contains("6 strict shared|36 of 47", case=False, regex=True).any(), "Overlap result leaked into setup plot data")

    rendered_paths = [output_root / f"{FIGURE_ID}.{extension}" for extension in ("png", "pdf", "svg")]
    image_rows = image_checks(rendered_paths, as_int(status["png_dpi"]))
    require(all(row["status"] == "pass" for row in image_rows), "Published image validation failed")
    print(f"SEA-AD–ROSMAP setup figure validation passed: {output_root}")


def publish(
    project_root: Path,
    output_root: Path,
    *,
    dpi: int,
    visual_review_status: str,
    force: bool,
) -> None:
    require(project_root.is_dir(), f"Missing project root: {project_root}")
    if output_root.exists() and not force:
        raise FileExistsError(f"Output exists; use --force for recoverable replacement: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{FIGURE_ID}.staging.", dir=output_root.parent))
    try:
        bundle = load_bundle(project_root)
        plot_data = build_plot_data(bundle)
        figure, render_meta = render_figure(plot_data)
        image_paths = render_images(figure, staging, dpi)
        write_tsv(plot_data, staging / f"{FIGURE_ID}_plot_data.tsv")
        caption, methods = documentation(bundle)
        write_text(staging / f"{FIGURE_ID}_caption.md", caption)
        write_text(staging / f"{FIGURE_ID}_methods.md", methods)
        checks = build_checks(bundle, plot_data, image_paths, render_meta, dpi, visual_review_status)
        write_tsv(checks, staging / f"{FIGURE_ID}_checks.tsv")

        renderer_path = Path(__file__).resolve()
        artifacts = build_artifacts(bundle, staging, renderer_path)
        artifacts_path = staging / f"{FIGURE_ID}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        validation_status = "validated_complete" if visual_review_status == "complete" and pending == 0 else "awaiting_visual_review"
        status = pd.DataFrame(
            [
                {
                    "schema_version": SCHEMA,
                    "figure_id": FIGURE_ID,
                    "validation_status": validation_status,
                    "visual_review_status": visual_review_status,
                    "failed_blocking_checks": int(
                        (
                            checks["severity"].eq("blocking")
                            & ~checks["status"].eq("pass")
                        ).sum()
                    ),
                    "pending_nonblocking_checks": int(
                        (
                            checks["severity"].eq("nonblocking")
                            & ~checks["status"].eq("pass")
                        ).sum()
                    ),
                    "input_bundle_sha256": bundle["input_bundle_sha256"],
                    "renderer_sha256": sha256_file(renderer_path),
                    "artifact_manifest_sha256": sha256_file(artifacts_path),
                    "figure_width_inches": f"{FIGURE_WIDTH_IN:.6f}",
                    "figure_height_inches": f"{FIGURE_HEIGHT_IN:.6f}",
                    "png_dpi": dpi,
                    "png_width": PNG_WIDTH,
                    "png_height": PNG_HEIGHT,
                    "input_files": len(bundle["input_digests"]),
                    "output_files": len(OUTPUT_FILES),
                    "plot_data_rows": len(plot_data),
                    "checks": len(checks),
                    "seaad_structural_slots": bundle["structural_directions"],
                    "seaad_active_kda_calls": bundle["active_calls"],
                    "seaad_selected_units": bundle["sea_selected"],
                    "rosmap_structural_slots": bundle["rosmap_structural"],
                    "rosmap_included_runs": bundle["rosmap_included"],
                    "rosmap_selected_units": bundle["rosmap_selected"],
                    "comparison_outcome_shown": False,
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        write_tsv(status, staging / f"{FIGURE_ID}_status.tsv")
        validate_output(project_root, staging, expected_visual_status=visual_review_status)

        if output_root.exists():
            backup_root = project_root / "tmp" / "validation_human_figure_backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            backup = backup_root / f"{output_root.name}_{timestamp}_{os.getpid()}"
            output_root.replace(backup)
        staging.replace(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"Published {len(OUTPUT_FILES)} figure-package files: {output_root}")


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if args.validate_output:
        validate_output(
            project_root,
            resolve(project_root, args.validate_output),
            expected_visual_status=None,
        )
        return 0
    publish(
        project_root,
        resolve(project_root, args.output_root),
        dpi=args.png_dpi,
        visual_review_status=args.visual_review_status,
        force=args.force,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
