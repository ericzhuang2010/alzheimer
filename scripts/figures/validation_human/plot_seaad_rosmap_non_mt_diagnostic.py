#!/usr/bin/env python3
"""Render the validated slide-scale ROSMAP/SEA-AD non-MT diagnostic."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_non_mt_diagnostic_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_non_mt_diagnostic_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "seaad_rosmap_non_mt_diagnostic_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "hatch.linewidth": 0.9,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402
import pandas as pd  # noqa: E402


SCHEMA = "seaad_rosmap_non_mt_diagnostic_v1"
FIGURE_ID = "seaad_rosmap_non_mt_diagnostic"
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 5.3
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 2_385

ROSMAP = "#E69F00"
ROSMAP_PALE = "#F9E5B8"
SEAAD = "#009E73"
SEAAD_PALE = "#BFE8DC"
NAVY = "#0F233D"
GRAY = "#BDBDBD"
GRAY_PALE = "#F1F3F5"
MID = "#5E6670"
TEXT = "#20252B"
WHITE = "#FFFFFF"

INPUT_PATHS = {
    "phase12_status": "results/minerva_production/12_kda/kda_status.tsv",
    "phase12_artifacts": "results/minerva_production/12_kda/kda_artifacts.tsv",
    "phase12_checks": "results/minerva_production/12_kda/kda_checks.tsv",
    "phase12_results": "results/minerva_production/12_kda/kda_results.tsv.gz",
    "phase18_status": "results/minerva_production/18_key_driver_selection/archive/key_driver_status.tsv",
    "phase18_artifacts": "results/minerva_production/18_key_driver_selection/archive/key_driver_artifacts.tsv",
    "phase18_checks": "results/minerva_production/18_key_driver_selection/archive/key_driver_checks.tsv",
    "phase18_run_manifest": "results/minerva_production/18_key_driver_selection/archive/key_driver_run_manifest.tsv",
    "phase18_support": "results/minerva_production/18_key_driver_selection/archive/key_driver_conservative_support.tsv.gz",
    "phase18_gene_summary": "results/minerva_production/18_key_driver_selection/archive/key_driver_gene_case_summary.tsv.gz",
    "phase18_call_returns": "results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv",
    "vh09_status": "results/validation_human/09_rosmap_kda_candidates/status.tsv",
    "vh09_artifacts": "results/validation_human/09_rosmap_kda_candidates/artifacts.tsv",
    "vh09_checks": "results/validation_human/09_rosmap_kda_candidates/candidate_freeze_checks.tsv",
    "rosmap_selected": "results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv",
    "vh10a_status": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/status.tsv",
    "vh10a_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/artifacts.tsv",
    "vh10a_checks": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/input_checks.tsv",
    "seaad_run_manifest": "results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv",
    "vh10b_status": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/status.tsv",
    "vh10b_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/artifacts.tsv",
    "vh10b_checks": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/run_reconstruction_checks.tsv",
    "seaad_returns": "results/validation_human/10_seaad_kda_rediscovery/10b_kda/seaad_kda_significant_returns.tsv",
    "vh10d_status": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/status.tsv",
    "vh10d_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/artifacts.tsv",
    "vh10d_checks": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/overlap_checks.tsv",
    "unit_overlap": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv",
}

EXPECTED_INPUT_SHA256 = {
    "phase12_status": "ed1efb037d2d9e4c033e16d9b61f676b8ff530b9393c0bc3f1282d39efbd7c63",
    "phase12_artifacts": "0ed17d3929e3bbb6216cf0451049b44a329cfe8ac36223ca8c77f5c853d445d9",
    "phase12_checks": "e83f53eb341c0c7bd499a2d6ba66336707f20dfe88303c63225a8e63f26f4d53",
    "phase12_results": "079c5ec46435740d6a676c5676f637d49e4787c17f8490fbc398996a9b58ade1",
    "phase18_status": "91b2d997e9b15be1c06ceccff32a65b46f5f499e5ba607fe7990a99b826c9672",
    "phase18_artifacts": "4eda4b904e7476333b5f9a45562e8829fa2d24f730c632907ab15f07d941fb16",
    "phase18_checks": "463ed53c814a1c45a0981544cffaf56ddcb48d40848be8392bb2583acc86a34b",
    "phase18_run_manifest": "95a596d5e7a98dcfc7fe09f57f11156fa1a78534a36549a5e854d2ce79e43fc1",
    "phase18_support": "bce46031b589a353c98b4bd255fe8d6a4b71aa4dbe25336bedfb42025bf44f1a",
    "phase18_gene_summary": "a173e1338c8b48b2c524fec83778ba5057674fe486b6b04b33c44df2eaadfcae",
    "phase18_call_returns": "b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8",
    "vh09_status": "e5504ef3edb8264064d40b8307ded3f2277e9230e39f1029162aba4b11f52568",
    "vh09_artifacts": "9cb622cb3d1affc93eac21d598d51ada31b5f74a2355f477cce78c6cbe6f6ced",
    "vh09_checks": "74cacf128d42e62d63780a1e7f2658fec4dee0b701d5c8009c59e6df6614b8a8",
    "rosmap_selected": "e758720f7dcd80d1d6ef72fc7f95bfa20e3784931114e59c716a0e85b681d443",
    "vh10a_status": "d137ec39191340b2b956e1e91693ef694e45858064be4308f8bd5cde20283c81",
    "vh10a_artifacts": "e0d86a664eda5ea0f33fbb81800857bfafffa0ddc88970fce6f81416227202d5",
    "vh10a_checks": "db1a89653096468fb3520d5b33477f87a9e910321cd79d2e01526f252f514cfe",
    "seaad_run_manifest": "03197e2fb701d5d1c17c59339e3d16818222d946e795bdb70ce845e77896441d",
    "vh10b_status": "db308f382993c033b6126e996e860f8bcdb3a5d826e2aeea2daf54511e1d4e92",
    "vh10b_artifacts": "d3b012e7b9cf383bf489d259a2f3bcfbbd26f5682a2362efd9422f5d0e3d58c1",
    "vh10b_checks": "2e854d16fafd752ad9081c365f5690dcf5f626f67bde1b5a5bad1a06c0ba2a5d",
    "seaad_returns": "82ef26e9a2e7f22f81720b4c1a5076a40a7c924b8f5ee997bcde502b4585483b",
    "vh10d_status": "fd9370f145948f10358e90830e18b25fbf36b3c253c5b2ac22528cb7f74f9528",
    "vh10d_artifacts": "b349a71f5a5735188397a535c054f81af5c024278a6b21ee9c86b8491b2c2a57",
    "vh10d_checks": "a437d7122e0b83173aa49684127a00bd07da2a9b4df2bc1d0366fe478b3526d1",
    "unit_overlap": "68b839ef1dae967bc482d16667d94fe8fd2a8bb17290ea43b2a96767c4abbfa6",
}

OUTPUT_FILES = [
    f"{FIGURE_ID}.png",
    f"{FIGURE_ID}.pdf",
    f"{FIGURE_ID}.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_fate_summary.tsv",
    f"{FIGURE_ID}_reverse_lookup.tsv",
    f"{FIGURE_ID}_coverage_context.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_artifacts.tsv",
    f"{FIGURE_ID}_status.tsv",
]
PAYLOAD_FILES = OUTPUT_FILES[:-2]

UNAVAILABLE_GROUPS = {"F_e2", "M_e2", "M_e4"}
EXPECTED_NOT_TESTABLE = {
    ("OPCs", "RPS15"), ("OPCs", "FTL"),
    ("OPCs", "ANKRD11"), ("OPCs", "NCOA1"),
}
EXPECTED_ONE_RETURN = {
    ("Excitatory_neurons", "DYNLT1"),
    ("Inhibitory_neurons", "RPS15"),
    ("Inhibitory_neurons", "RPLP1"),
    ("Inhibitory_neurons", "RPL38"),
}
REVERSE_ORDER = [
    ("Excitatory_neurons", "HGSNAT"),
    ("Inhibitory_neurons", "BEX3"),
    ("Inhibitory_neurons", "RPS27A"),
    ("Inhibitory_neurons", "RPL30"),
    ("Oligodendrocytes", "KANSL1L"),
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output-root",
        default=f"results/figures/validation_human/{FIGURE_ID}",
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status", choices=("pending", "complete"), default="pending"
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-output")
    args = parser.parse_args(argv)
    if args.png_dpi != DEFAULT_PNG_DPI:
        parser.error(f"--png-dpi must equal {DEFAULT_PNG_DPI}")
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
    rounded = int(round(number))
    require(math.isfinite(number) and abs(number - rounded) < 1e-9, f"Expected integer {label}")
    return rounded


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_tsv(path: Path, **kwargs: Any) -> pd.DataFrame:
    require(path.is_file(), f"Missing table: {path}")
    return pd.read_csv(path, sep="\t", **kwargs)


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, sep="\t", index=False, lineterminator="\n")
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def one_row(frame: pd.DataFrame, label: str) -> pd.Series:
    require(len(frame) == 1, f"Expected one row in {label}, observed {len(frame)}")
    return frame.iloc[0]


def require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    require(not missing, f"Missing columns in {label}: {missing}")


def validate_registered(manifest: pd.DataFrame, registered_path: str, digest: str) -> None:
    require_columns(manifest, ["path"], "upstream artifact manifest")
    rows = manifest.loc[manifest["path"].eq(registered_path)]
    require(len(rows) == 1, f"Input is not uniquely registered: {registered_path}")
    row = rows.iloc[0]
    digest_column = "digest_value" if "digest_value" in manifest.columns else "sha256"
    require(str(row[digest_column]) == digest, f"Registered digest mismatch: {registered_path}")
    if "digest_algorithm" in manifest.columns:
        require(row["digest_algorithm"] == "sha256", f"Non-SHA256 registration: {registered_path}")
        require(row["digest_scope"] == "full_file", f"Non-full-file registration: {registered_path}")


def load_selected_support(path: Path, selected_keys: set[tuple[str, str]]) -> pd.DataFrame:
    columns = [
        "broad_network", "current_symbol", "case_id", "signature_group",
        "fine_cell_type", "signature_direction", "conservative_support",
    ]
    parts = []
    for chunk in pd.read_csv(path, sep="\t", usecols=columns, chunksize=200_000):
        keys = list(zip(chunk["broad_network"], chunk["current_symbol"]))
        mask = pd.Series([key in selected_keys for key in keys], index=chunk.index)
        mask &= chunk["conservative_support"].map(truth)
        parts.append(chunk.loc[mask].copy())
    frame = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=columns)
    require(not frame.empty, "No frozen ROSMAP support rows found")
    return frame


def load_reverse_aggregate(path: Path) -> pd.DataFrame:
    columns = [
        "broad_network", "key_driver", "case_id", "aggregate_acat_p",
        "aggregate_acat_q", "conservative_support_count",
        "terminal_candidate_status", "top5_display",
    ]
    frame = pd.read_csv(path, sep="\t", usecols=columns, low_memory=False)
    keys = set(REVERSE_ORDER[:-1])
    mask = pd.Series(
        [(network, gene) in keys for network, gene in zip(frame["broad_network"], frame["key_driver"])],
        index=frame.index,
    ) & frame["case_id"].eq("non_mt_driver")
    frame = frame.loc[mask].drop_duplicates().copy()
    require(len(frame) == 4, f"Expected four explicit reverse aggregate rows, observed {len(frame)}")
    return frame


def load_bundle(project_root: Path) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    digests = {}
    paths = {}
    for key, relative in INPUT_PATHS.items():
        path = project_root / relative
        digest = sha256_file(path)
        require(digest == EXPECTED_INPUT_SHA256[key], f"Frozen SHA-256 changed for {relative}")
        paths[key] = path
        digests[relative] = digest

    compact_keys = [
        key for key in INPUT_PATHS
        if key not in {"phase18_support", "phase18_gene_summary", "phase18_call_returns"}
    ]
    frames = {key: read_tsv(paths[key], dtype=str, keep_default_na=False) for key in compact_keys}

    phase12_status = one_row(frames["phase12_status"], "Phase 12 status")
    phase18_status = one_row(frames["phase18_status"], "Phase 18 status")
    require(phase12_status["validation_status"] == "validated_complete", "Phase 12 is not validated_complete")
    require(phase18_status["validation_status"] == "validated_complete", "Phase 18 is not validated_complete")
    require(as_int(phase12_status["failed_checks"]) == 0, "Phase 12 reports failed checks")
    require(as_int(phase18_status["failed_checks"]) == 0, "Phase 18 reports failed checks")
    for label in ("phase12_checks", "phase18_checks", "vh09_checks", "vh10a_checks", "vh10b_checks", "vh10d_checks"):
        require_columns(frames[label], ["passed"], label)
        require(frames[label]["passed"].map(truth).all(), f"Failed upstream check in {label}")
    for label in ("vh09_status", "vh10a_status", "vh10b_status", "vh10d_status"):
        row = one_row(frames[label], label)
        require(row["validation_status"] == "validated_complete", f"{label} is not validated_complete")
        require(str(row.get("failed_checks", "")).strip() == "", f"{label} reports failed checks")

    registrations = [
        ("phase12_artifacts", "results/minerva_production/12_kda/kda_checks.tsv", "phase12_checks"),
        ("phase12_artifacts", "results/minerva_production/12_kda/kda_results.tsv.gz", "phase12_results"),
        ("phase18_artifacts", "key_driver_checks.tsv", "phase18_checks"),
        ("phase18_artifacts", "key_driver_run_manifest.tsv", "phase18_run_manifest"),
        ("phase18_artifacts", "key_driver_conservative_support.tsv.gz", "phase18_support"),
        ("phase18_artifacts", "key_driver_gene_case_summary.tsv.gz", "phase18_gene_summary"),
        ("vh09_artifacts", INPUT_PATHS["vh09_checks"], "vh09_checks"),
        ("vh09_artifacts", INPUT_PATHS["rosmap_selected"], "rosmap_selected"),
        ("vh10a_artifacts", INPUT_PATHS["vh10a_checks"], "vh10a_checks"),
        ("vh10a_artifacts", INPUT_PATHS["seaad_run_manifest"], "seaad_run_manifest"),
        ("vh10b_artifacts", INPUT_PATHS["vh10b_checks"], "vh10b_checks"),
        ("vh10b_artifacts", INPUT_PATHS["seaad_returns"], "seaad_returns"),
        ("vh10d_artifacts", INPUT_PATHS["vh10d_checks"], "vh10d_checks"),
        ("vh10d_artifacts", INPUT_PATHS["unit_overlap"], "unit_overlap"),
    ]
    for manifest_key, registered_path, input_key in registrations:
        validate_registered(frames[manifest_key], registered_path, EXPECTED_INPUT_SHA256[input_key])

    selected = frames["rosmap_selected"].copy()
    require_columns(selected, ["broad_network", "key_driver", "case_id", "within_case_rank", "top5_display"], "ROSMAP selected")
    selected = selected.loc[selected["case_id"].eq("non_mt_driver") & selected["top5_display"].map(truth)].copy()
    require(len(selected) == 21, f"Expected 21 ROSMAP non-MT selected units, observed {len(selected)}")
    selected_keys = set(zip(selected["broad_network"], selected["key_driver"]))

    overlap = frames["unit_overlap"].copy()
    require_columns(overlap, ["broad_network", "gene", "case_id", "in_common_assessable_universe", "rosmap_top5", "seaad_top5", "seaad_driver_candidate", "replication_status"], "unit overlap")
    overlap = overlap.loc[overlap["case_id"].eq("non_mt_driver") & overlap["rosmap_top5"].map(truth)].copy()
    require(len(overlap) == 21, "ROSMAP non-MT overlap rows changed")
    require(set(zip(overlap["broad_network"], overlap["gene"])) == selected_keys, "Selected/overlap unit keys disagree")

    support = load_selected_support(paths["phase18_support"], selected_keys)
    reverse_aggregate = load_reverse_aggregate(paths["phase18_call_returns"])
    gene_summary = pd.read_csv(
        paths["phase18_gene_summary"], sep="\t",
        usecols=["broad_network", "current_symbol", "case_id", "aggregate_acat_p", "aggregate_acat_q", "conservative_support_count", "terminal_candidate_status", "top5_display"],
    )
    phase12_results = frames["phase12_results"].copy()
    seaad_returns = frames["seaad_returns"].copy()
    seaad_manifest = frames["seaad_run_manifest"].copy()
    phase18_manifest = frames["phase18_run_manifest"].copy()

    input_bundle_sha256 = sha256_strings(
        f"{path}\t{digest}" for path, digest in sorted(digests.items())
    )
    return {
        "project_root": project_root,
        "paths": paths,
        "frames": frames,
        "input_digests": digests,
        "input_bundle_sha256": input_bundle_sha256,
        "selected": selected,
        "selected_keys": selected_keys,
        "overlap": overlap,
        "support": support,
        "reverse_aggregate": reverse_aggregate,
        "gene_summary": gene_summary,
        "phase12_results": phase12_results,
        "seaad_returns": seaad_returns,
        "seaad_manifest": seaad_manifest,
        "phase18_manifest": phase18_manifest,
    }


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    selected = bundle["selected"]
    overlap = bundle["overlap"].set_index(["broad_network", "gene"])
    support = bundle["support"]
    seaad = bundle["seaad_returns"].copy()
    seaad["overlap_count"] = pd.to_numeric(seaad["overlap_count"], errors="coerce")
    seaad["fold_enrichment"] = pd.to_numeric(seaad["fold_enrichment"], errors="coerce")
    seaad["adjusted_p_value"] = pd.to_numeric(seaad["adjusted_p_value"], errors="coerce")
    qualifying = seaad.loc[
        seaad["adjusted_p_value"].le(0.05)
        & seaad["overlap_count"].ge(2)
        & seaad["fold_enrichment"].gt(1.0)
    ].copy()

    rows = []
    for row in selected.sort_values(["broad_network", "within_case_rank"]).itertuples(index=False):
        key = (row.broad_network, row.key_driver)
        trace = overlap.loc[key]
        ros_support = support.loc[
            support["broad_network"].eq(row.broad_network)
            & support["current_symbol"].eq(row.key_driver)
        ]
        groups = sorted(set(ros_support["signature_group"]))
        unavailable_groups = sorted(set(groups) & UNAVAILABLE_GROUPS)
        matched = qualifying.loc[
            qualifying["broad_network"].eq(row.broad_network)
            & qualifying["key_driver"].eq(row.key_driver)
        ]
        rows.append(
            {
                "schema_version": f"{SCHEMA}_plot_data",
                "figure_id": FIGURE_ID,
                "broad_network": row.broad_network,
                "gene": row.key_driver,
                "rosmap_within_class_rank": as_int(row.within_case_rank),
                "seaad_assessability": "assessable" if truth(trace["in_common_assessable_universe"]) else "not_testable_no_included_opc_run",
                "seaad_qualifying_return_count": len(matched),
                "seaad_supporting_runs": "|".join(sorted(set(matched["kda_run_id"]))) if len(matched) else "",
                "seaad_supporting_fine_types": "|".join(sorted(set(matched["fine_cell_type"]))) if len(matched) else "",
                "seaad_supporting_groups": "|".join(sorted(set(matched["signature_group"]))) if len(matched) else "",
                "seaad_final_driver_candidate": truth(trace["seaad_driver_candidate"]),
                "seaad_top5": truth(trace["seaad_top5"]),
                "replication_status": trace["replication_status"],
                "rosmap_support_groups": "|".join(groups),
                "rosmap_unavailable_in_seaad_support_groups": "|".join(unavailable_groups),
                "rosmap_has_unavailable_stratum_support": bool(unavailable_groups),
                "unavailable_support_is_exclusive": set(groups).issubset(UNAVAILABLE_GROUPS),
            }
        )
    frame = pd.DataFrame(rows)
    require(len(frame) == 21 and not frame.duplicated(["broad_network", "gene"]).any(), "Diagnostic unit rows changed")
    not_testable = set(zip(frame.loc[frame["seaad_assessability"].ne("assessable"), "broad_network"], frame.loc[frame["seaad_assessability"].ne("assessable"), "gene"]))
    one_return = set(zip(frame.loc[frame["seaad_qualifying_return_count"].eq(1), "broad_network"], frame.loc[frame["seaad_qualifying_return_count"].eq(1), "gene"]))
    require(not_testable == EXPECTED_NOT_TESTABLE, "Not-testable OPC identities changed")
    require(one_return == EXPECTED_ONE_RETURN, "One-return identities changed")
    require(frame["seaad_qualifying_return_count"].isin([0, 1]).all(), "Unexpected repeated SEA-AD matching support")
    require(frame["rosmap_has_unavailable_stratum_support"].sum() == 20, "Unavailable-stratum support count changed")
    require(not frame["seaad_final_driver_candidate"].any(), "A ROSMAP non-MT unit passed SEA-AD final selection")
    return frame


def build_fate_summary(plot_data: pd.DataFrame) -> pd.DataFrame:
    assessable = plot_data["seaad_assessability"].eq("assessable")
    rows = [
        ("rosmap_selected", "", 21, "ROSMAP selected non-MT network-gene units"),
        ("not_testable", "rosmap_selected", int((~assessable).sum()), "No included SEA-AD OPC run"),
        ("assessable", "rosmap_selected", int(assessable.sum()), "Matching SEA-AD broad network assessable"),
        ("no_qualifying_return", "assessable", int((assessable & plot_data["seaad_qualifying_return_count"].eq(0)).sum()), "No qualifying same-network SEA-AD run-level return"),
        ("one_qualifying_return", "assessable", int((assessable & plot_data["seaad_qualifying_return_count"].eq(1)).sum()), "Exactly one qualifying same-network SEA-AD return"),
        ("passed_final_selection", "one_qualifying_return", int(plot_data["seaad_final_driver_candidate"].sum()), "Passed final SEA-AD aggregate candidate selection"),
    ]
    frame = pd.DataFrame(
        [
            {"schema_version": f"{SCHEMA}_fate_summary", "figure_id": FIGURE_ID, "node_id": node, "parent_node_id": parent, "unit_count": count, "definition": definition}
            for node, parent, count, definition in rows
        ]
    )
    require(frame["unit_count"].astype(int).tolist() == [21, 4, 17, 13, 4, 0], "Fate counts changed")
    return frame


def build_reverse_lookup(bundle: Mapping[str, Any]) -> pd.DataFrame:
    aggregate = bundle["reverse_aggregate"].set_index(["broad_network", "key_driver"])
    gene_summary = bundle["gene_summary"]
    phase12 = bundle["phase12_results"].copy()
    phase12["signature_size"] = pd.to_numeric(phase12["signature_size"], errors="coerce")
    phase12["adjusted_p_value"] = pd.to_numeric(phase12["adjusted_p_value"], errors="coerce")
    rpl30_excluded = phase12.loc[
        phase12["analysis_tier"].eq("primary")
        & phase12["broad_network"].eq("Inhibitory_neurons")
        & phase12["key_driver"].eq("RPL30")
        & phase12["signature_size"].lt(10)
        & phase12["adjusted_p_value"].le(0.05)
    ]
    require(len(rpl30_excluded) == 2 and set(rpl30_excluded["signature_size"].astype(int)) == {3}, "RPL30 excluded size-3 return count changed")
    kansl_raw = phase12.loc[
        phase12["analysis_tier"].eq("primary")
        & phase12["broad_network"].eq("Oligodendrocytes")
        & phase12["key_driver"].eq("KANSL1L")
    ]
    require(kansl_raw.empty, "KANSL1L unexpectedly has a primary ROSMAP return")

    rows = []
    for order, (network, gene) in enumerate(REVERSE_ORDER, start=1):
        if (network, gene) in aggregate.index:
            row = aggregate.loc[(network, gene)]
            q_value = float(row["aggregate_acat_q"])
            p_value = float(row["aggregate_acat_p"])
            support_count = as_int(row["conservative_support_count"])
            terminal = row["terminal_candidate_status"]
        else:
            fallback = gene_summary.loc[
                gene_summary["broad_network"].eq(network)
                & gene_summary["current_symbol"].eq(gene)
                & gene_summary["case_id"].eq("case3_not_core_mito")
            ]
            fallback_row = one_row(fallback, f"ROSMAP fallback {network}/{gene}")
            q_value = float(fallback_row["aggregate_acat_q"])
            p_value = float(fallback_row["aggregate_acat_p"])
            support_count = as_int(fallback_row["conservative_support_count"])
            terminal = fallback_row["terminal_candidate_status"]

        if gene == "HGSNAT":
            outcome_id = "some_support_gate_not_passed"
            outcome = "Some run support; aggregate gate not passed"
        elif gene == "BEX3":
            outcome_id = "multiple_supports_gate_not_passed"
            outcome = "Multiple run supports; aggregate gate not passed"
        elif gene == "RPS27A":
            outcome_id = "support_present_gate_not_passed"
            outcome = "Run support present; aggregate gate not passed"
        elif gene == "RPL30":
            outcome_id = "excluded_size3_only"
            outcome = "Only 2 excluded size-3 returns; no included conservative support"
        else:
            outcome_id = "no_explicit_primary_return"
            outcome = "No explicit primary ROSMAP return; not selected"
        rows.append(
            {
                "schema_version": f"{SCHEMA}_reverse_lookup",
                "figure_id": FIGURE_ID,
                "display_order": order,
                "broad_network": network,
                "gene": gene,
                "rosmap_aggregate_p": p_value,
                "rosmap_aggregate_q": q_value,
                "rosmap_conservative_support_count": support_count,
                "rosmap_terminal_candidate_status": terminal,
                "excluded_size3_primary_return_count": len(rpl30_excluded) if gene == "RPL30" else 0,
                "explicit_primary_return_count": 0 if gene == "KANSL1L" else "NA",
                "outcome_id": outcome_id,
                "plain_language_outcome": outcome,
            }
        )
    frame = pd.DataFrame(rows)
    expected_q = {"HGSNAT": 0.6413643985648223, "BEX3": 0.1574575602307228, "RPS27A": 1.0, "RPL30": 1.0, "KANSL1L": 1.0}
    observed_q = frame.set_index("gene")["rosmap_aggregate_q"].astype(float).to_dict()
    require(all(math.isclose(observed_q[gene], value) for gene, value in expected_q.items()), "Reverse-lookup q values changed")
    require(not frame["rosmap_terminal_candidate_status"].isin({"driver_candidate"}).any(), "A reverse-lookup unit became a ROSMAP driver candidate")
    return frame


def build_coverage_context(bundle: Mapping[str, Any], plot_data: pd.DataFrame) -> pd.DataFrame:
    phase18 = bundle["phase18_manifest"]
    seaad = bundle["seaad_manifest"]
    rosmap_runs = int(phase18["phase18_included"].map(truth).sum())
    seaad_calls = int(seaad["eligibility_status"].eq("eligible").sum())
    seaad_m_e33 = int((seaad["eligibility_status"].eq("eligible") & seaad["signature_group"].eq("M_e33")).sum())
    rosmap_query_floor = int(
        pd.to_numeric(
            phase18.loc[phase18["phase18_included"].map(truth), "effective_query_genes"],
            errors="raise",
        ).min()
    )
    seaad_query_floor = int(
        pd.to_numeric(
            seaad.loc[seaad["eligibility_status"].eq("eligible"), "effective_query_genes"],
            errors="raise",
        ).min()
    )
    donor_limited_groups = set(
        seaad.loc[seaad["source_terminal_reason"].eq("disease_arm_below_5"), "signature_group"]
    )
    groups_with_eligible_calls = set(
        seaad.loc[seaad["eligibility_status"].eq("eligible"), "signature_group"]
    )
    unavailable = donor_limited_groups - groups_with_eligible_calls
    unavailable_support = int(plot_data["rosmap_has_unavailable_stratum_support"].sum())
    exclusive_support = int(plot_data["unavailable_support_is_exclusive"].sum())
    require(rosmap_runs == 161, "ROSMAP included-run count changed")
    require(seaad_calls == 42 and seaad_m_e33 == 40, "SEA-AD call/group counts changed")
    require(rosmap_query_floor == 10 and seaad_query_floor == 3, "KDA query-size floors changed")
    require(unavailable == UNAVAILABLE_GROUPS, "SEA-AD donor-limited strata changed")
    require(unavailable_support == 20, "Unavailable-stratum support count changed")
    frame = pd.DataFrame(
        [
            {
                "schema_version": f"{SCHEMA}_coverage_context",
                "figure_id": FIGURE_ID,
                "rosmap_included_runs": rosmap_runs,
                "rosmap_effective_query_floor": rosmap_query_floor,
                "seaad_kda_calls": seaad_calls,
                "seaad_m_e33_calls": seaad_m_e33,
                "seaad_effective_query_floor": seaad_query_floor,
                "seaad_other_group_calls": seaad_calls - seaad_m_e33,
                "seaad_donor_limited_groups": "|".join(sorted(unavailable)),
                "rosmap_selected_units": len(plot_data),
                "units_with_rosmap_support_in_donor_limited_group": unavailable_support,
                "units_supported_exclusively_in_donor_limited_groups": exclusive_support,
                "causal_guardrail": "unavailable-stratum support is not necessarily exclusive and does not make assessable units untestable",
            }
        ]
    )
    return frame


def _box(ax: Any, x: float, y: float, w: float, h: float, *, face: str, edge: str, linestyle: str = "solid", hatch: str | None = None, linewidth: float = 2.0, padding: float = 0.012) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad={padding},rounding_size=0.022",
        transform=ax.transAxes, facecolor=face, edgecolor=edge,
        linewidth=linewidth, linestyle=linestyle, hatch=hatch,
    )
    ax.add_patch(patch)
    return patch


def _connector(ax: Any, points: Sequence[tuple[float, float]], *, color: str = MID, linestyle: str = "solid", linewidth: float = 2.0) -> None:
    xs, ys = zip(*points)
    ax.plot(
        xs,
        ys,
        transform=ax.transAxes,
        color=color,
        linestyle=linestyle,
        linewidth=linewidth,
        solid_capstyle="butt",
        clip_on=False,
        zorder=0.5,
    )


def _node_text(ax: Any, x: float, y: float, text: str, *, size: float = 16, color: str = TEXT, weight: str = "normal", linespacing: float = 1.08) -> Any:
    return ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center", fontsize=size, color=color, weight=weight, linespacing=linespacing)


def draw_figure(plot_data: pd.DataFrame, fate: pd.DataFrame, reverse: pd.DataFrame, context: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    del plot_data
    counts = fate.set_index("node_id")["unit_count"].astype(int).to_dict()
    ctx = one_row(context, "coverage context")
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    ax_a = fig.add_axes([0.02, 0.235, 0.55, 0.735])
    ax_b = fig.add_axes([0.59, 0.235, 0.39, 0.735])
    ribbon = fig.add_axes([0.02, 0.020, 0.96, 0.190])
    for ax in (ax_a, ax_b, ribbon):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    owned_text: list[tuple[Any, Any, str]] = []
    table_left: list[Any] = []
    table_right: list[Any] = []
    panel_b_rows: list[tuple[str, Any]] = []
    ribbon_blocks: list[tuple[Any, list[Any], str]] = []

    def register(patch: Any, artists: Sequence[Any], label: str) -> None:
        owned_text.extend((patch, artist, label) for artist in artists)

    a_letter = ax_a.text(0.00, 0.99, "A", transform=ax_a.transAxes, ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    a_title = ax_a.text(0.07, 0.99, "ROSMAP → SEA-AD fate", transform=ax_a.transAxes, ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    ax_a.text(0.07, 0.895, "21 frozen non-MT network–gene units", transform=ax_a.transAxes, ha="left", va="top", fontsize=16, color=MID)

    source = _box(ax_a, 0.014, 0.31, 0.201, 0.28, face=ROSMAP_PALE, edge=ROSMAP, hatch="////")
    source_text = [
        _node_text(ax_a, 0.113, 0.50, str(counts["rosmap_selected"]), size=25, color=ROSMAP, weight="bold"),
        _node_text(ax_a, 0.113, 0.385, "selected\nnon-MT units", size=16, linespacing=1.0),
    ]
    register(source, source_text, "source")

    not_testable = _box(ax_a, 0.275, 0.52, 0.29, 0.30, face=WHITE, edge=MID, linestyle="dashed")
    not_testable_text = [
        _node_text(ax_a, 0.4225, 0.79, f"{counts['not_testable']} not testable", size=16, weight="bold"),
        _node_text(ax_a, 0.4225, 0.72, "all OPC", size=16, color=MID),
        _node_text(ax_a, 0.4225, 0.595, "RPS15 • FTL\nANKRD11\nNCOA1", size=16, color=MID, linespacing=0.95),
    ]
    register(not_testable, not_testable_text, "not_testable")

    assessable = _box(ax_a, 0.275, 0.235, 0.29, 0.24, face=SEAAD_PALE, edge=SEAAD)
    assessable_text = [
        _node_text(ax_a, 0.42, 0.435, str(counts["assessable"]), size=22, color=SEAAD, weight="bold"),
        _node_text(ax_a, 0.42, 0.345, "assessable", size=17, color=SEAAD, weight="bold"),
        _node_text(ax_a, 0.42, 0.275, "matching network", size=16),
    ]
    register(assessable, assessable_text, "assessable")

    right_stack_x = 0.635
    right_stack_center = 0.80
    no_return = _box(ax_a, right_stack_x, 0.58, 0.33, 0.20, face=GRAY_PALE, edge=GRAY)
    no_return_text = [
        _node_text(ax_a, right_stack_center, 0.74, str(counts["no_qualifying_return"]), size=22, color=MID, weight="bold"),
        _node_text(ax_a, right_stack_center, 0.635, "no qualifying\nrun return", size=16, color=MID, linespacing=1.0),
    ]
    register(no_return, no_return_text, "no_return")

    one_return = _box(ax_a, right_stack_x, 0.26, 0.33, 0.27, face=WHITE, edge=NAVY)
    one_return_text = [
        _node_text(ax_a, right_stack_center, 0.495, f"{counts['one_qualifying_return']} • one each", size=17, color=NAVY, weight="bold"),
        _node_text(ax_a, right_stack_center, 0.42, "Exc: DYNLT1", size=16),
        _node_text(ax_a, right_stack_center, 0.315, "Inh: RPS15 • RPLP1\nRPL38", size=16, linespacing=1.0),
    ]
    register(one_return, one_return_text, "one_return")

    terminal = _box(ax_a, right_stack_x, 0.02, 0.33, 0.14, face=NAVY, edge=NAVY)
    terminal_text = [
        _node_text(ax_a, right_stack_center, 0.09, f"{counts['passed_final_selection']} passed final\nselection", size=16, color=WHITE, weight="bold", linespacing=0.88)
    ]
    register(terminal, terminal_text, "terminal")

    _connector(ax_a, [(0.215, 0.45), (0.245, 0.45), (0.245, 0.685), (0.275, 0.685)])
    _connector(ax_a, [(0.245, 0.45), (0.245, 0.355), (0.275, 0.355)])
    _connector(ax_a, [(0.565, 0.355), (0.60, 0.355), (0.60, 0.68), (right_stack_x, 0.68)])
    _connector(ax_a, [(0.60, 0.355), (0.60, 0.395), (right_stack_x, 0.395)])
    _connector(ax_a, [(right_stack_center, 0.26), (right_stack_center, 0.16)], color=NAVY, linewidth=2.5)

    b_letter = ax_b.text(0.00, 0.99, "B", transform=ax_b.transAxes, ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    b_title = ax_b.text(0.10, 0.99, "SEA-AD → ROSMAP lookup", transform=ax_b.transAxes, ha="left", va="top", fontsize=20, weight="bold", color=TEXT)
    ax_b.text(0.10, 0.895, "five selected non-MT units", transform=ax_b.transAxes, ha="left", va="top", fontsize=16, color=MID)
    row_height = 0.145
    top = 0.80
    for index, row in enumerate(reverse.sort_values("display_order").itertuples(index=False)):
        y = top - index * 0.15 - row_height
        row_patch = _box(ax_b, 0.016, y, 0.955, row_height, face=WHITE if index % 2 == 0 else GRAY_PALE, edge="#D9DDE2", linewidth=1.2)
        divider_x = 0.30
        ax_b.plot([divider_x, divider_x], [y + 0.015, y + row_height - 0.015], transform=ax_b.transAxes, color="#D9DDE2", linewidth=1.2)
        network = row.broad_network.replace("Excitatory_neurons", "Excitatory").replace("Inhibitory_neurons", "Inhibitory").replace("Oligodendrocytes", "Oligo")
        left_artists = [
            _node_text(ax_b, 0.15, y + 0.105, network, size=16, color=MID),
            _node_text(ax_b, 0.15, y + 0.035, row.gene, size=16, color=TEXT, weight="bold"),
        ]
        if row.gene == "HGSNAT":
            line1, line2 = "Some run support • q=.641", "Aggregate gate not passed"
        elif row.gene == "BEX3":
            line1, line2 = "4 run supports • q=.157", "Aggregate gate not passed"
        elif row.gene == "RPS27A":
            line1, line2 = "Run support present • q=1", "Aggregate gate not passed"
        elif row.gene == "RPL30":
            line1, line2 = "2 size-3 returns • q=1", "Excluded; no support"
        else:
            line1, line2 = "No primary ROSMAP return", "Not selected"
        right_artists = [
            ax_b.text(0.315, y + 0.105, line1, transform=ax_b.transAxes, ha="left", va="center", fontsize=16, color=TEXT),
            ax_b.text(0.315, y + 0.035, line2, transform=ax_b.transAxes, ha="left", va="center", fontsize=16, color=MID),
        ]
        register(row_patch, left_artists + right_artists, f"table_{row.gene}")
        panel_b_rows.append((row.gene, row_patch))
        table_left.extend(left_artists)
        table_right.extend(right_artists)

    ribbon_specs = [
        (0.00, 0.24, ROSMAP_PALE, ROSMAP, "////", "ROSMAP", f"{as_int(ctx['rosmap_included_runs'])} included runs\nquery floor ≥{as_int(ctx['rosmap_effective_query_floor'])}"),
        (0.25, 0.29, SEAAD_PALE, SEAAD, None, "SEA-AD", f"{as_int(ctx['seaad_kda_calls'])} KDA calls • {as_int(ctx['seaad_m_e33_calls'])} M_e33\nquery floor ≥{as_int(ctx['seaad_effective_query_floor'])}"),
        (0.55, 0.45, GRAY_PALE, NAVY, None, "SEA-AD coverage context", f"{as_int(ctx['units_with_rosmap_support_in_donor_limited_group'])}/{as_int(ctx['rosmap_selected_units'])} ROSMAP units: support in ≥1 group\nF_e2 / M_e2 / M_e4: ≥1 arm had <5 donors\nSupport need not be exclusive; not a sole cause"),
    ]
    for x, width, face, edge, hatch, heading, body in ribbon_specs:
        patch = _box(ribbon, x, 0.00, width, 1.00, face=face, edge=edge, hatch=hatch, linewidth=1.6)
        is_context = heading == "SEA-AD coverage context"
        heading_artist = _node_text(ribbon, x + width / 2, 0.86 if is_context else 0.80, heading, size=16 if is_context else 18, color=edge, weight="bold")
        body_artist = _node_text(ribbon, x + width / 2, 0.44 if is_context else 0.40, body, size=16, color=MID if is_context else TEXT, weight="normal" if is_context else "bold", linespacing=0.86 if is_context else 1.0)
        artists = [heading_artist, body_artist]
        register(patch, artists, f"ribbon_{heading}")
        ribbon_blocks.append((patch, artists, heading))

    layout_registry = {
        "owned_text": owned_text,
        "title_boundary": (a_title, b_letter),
        "table_axis": ax_b,
        "table_divider_x": divider_x,
        "table_left": table_left,
        "table_right": table_right,
        "panel_a_axis": ax_a,
        "panel_a_boxes": [
            ("source", source),
            ("not_testable", not_testable),
            ("assessable", assessable),
            ("no_return", no_return),
            ("one_return", one_return),
            ("terminal", terminal),
        ],
        "panel_a_separation_pairs": [
            ("not_testable", not_testable, "assessable", assessable),
            ("no_return", no_return, "one_return", one_return),
            ("one_return", one_return, "terminal", terminal),
        ],
        "panel_b_rows": panel_b_rows,
        "ribbon_blocks": ribbon_blocks,
        "panel_letters": (a_letter, b_letter),
        "panel_titles": (a_title, b_title),
    }
    return fig, render_meta(fig, layout_registry)


def _bbox_contains(outer: Any, inner: Any, padding: float = 2.0) -> bool:
    return (
        inner.x0 >= outer.x0 + padding
        and inner.x1 <= outer.x1 - padding
        and inner.y0 >= outer.y0 + padding
        and inner.y1 <= outer.y1 - padding
    )


def _bbox_intersects(first: Any, second: Any, padding: float = 2.0) -> bool:
    return not (
        first.x1 + padding <= second.x0
        or second.x1 + padding <= first.x0
        or first.y1 + padding <= second.y0
        or second.y1 + padding <= first.y0
    )


def render_meta(fig: Any, layout_registry: Mapping[str, Any]) -> dict[str, Any]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    visible = list(fig.texts)
    for ax in fig.axes:
        visible.extend(ax.texts)
    visible = [artist for artist in visible if artist.get_visible() and artist.get_text()]
    minimum = min(float(artist.get_fontsize()) for artist in visible)
    clipped = []
    for artist in visible:
        bbox = artist.get_window_extent(renderer=renderer)
        if bbox.x0 < fig.bbox.x0 - 1 or bbox.y0 < fig.bbox.y0 - 1 or bbox.x1 > fig.bbox.x1 + 1 or bbox.y1 > fig.bbox.y1 + 1:
            clipped.append(artist.get_text())
    require(minimum >= 16.0, f"Minimum visible font is {minimum:.2f} pt")
    require(not clipped, "Text leaves canvas: " + " | ".join(clipped))

    box_violations = []
    for patch, artist, label in layout_registry["owned_text"]:
        if not _bbox_contains(
            patch.get_window_extent(renderer=renderer),
            artist.get_window_extent(renderer=renderer),
        ):
            box_violations.append(f"{label}:{artist.get_text()}")

    owned_groups: dict[str, list[Any]] = {}
    for _, artist, label in layout_registry["owned_text"]:
        owned_groups.setdefault(label, []).append(artist)
    owned_text_overlap_violations = []
    for label, artists in owned_groups.items():
        for index, first in enumerate(artists):
            for second in artists[index + 1 :]:
                if _bbox_intersects(
                    first.get_window_extent(renderer=renderer),
                    second.get_window_extent(renderer=renderer),
                    padding=1.0,
                ):
                    owned_text_overlap_violations.append(
                        f"{label}:{first.get_text()}|{second.get_text()}"
                    )

    a_title, b_letter = layout_registry["title_boundary"]
    title_violation = (
        a_title.get_window_extent(renderer=renderer).x1 + 8
        > b_letter.get_window_extent(renderer=renderer).x0
    )

    table_axis = layout_registry["table_axis"]
    divider_px = table_axis.transAxes.transform((layout_registry["table_divider_x"], 0))[0]
    table_column_violations = []
    for artist in layout_registry["table_left"]:
        if artist.get_window_extent(renderer=renderer).x1 > divider_px - 4:
            table_column_violations.append(f"left:{artist.get_text()}")
    for artist in layout_registry["table_right"]:
        if artist.get_window_extent(renderer=renderer).x0 < divider_px + 4:
            table_column_violations.append(f"right:{artist.get_text()}")

    panel_a_box_overlap_violations = []
    for first_label, first, second_label, second in layout_registry["panel_a_separation_pairs"]:
        if _bbox_intersects(
            first.get_window_extent(renderer=renderer),
            second.get_window_extent(renderer=renderer),
            padding=2.0,
        ):
            panel_a_box_overlap_violations.append(f"{first_label}|{second_label}")

    panel_a_boundary_violations = []
    panel_a_bbox = layout_registry["panel_a_axis"].get_window_extent(renderer=renderer)
    for label, patch in layout_registry["panel_a_boxes"]:
        if not _bbox_contains(
            panel_a_bbox,
            patch.get_window_extent(renderer=renderer),
            padding=1.0,
        ):
            panel_a_boundary_violations.append(label)

    panel_b_boundary_violations = []
    panel_b_bbox = table_axis.get_window_extent(renderer=renderer)
    for label, patch in layout_registry["panel_b_rows"]:
        if not _bbox_contains(
            panel_b_bbox,
            patch.get_window_extent(renderer=renderer),
            padding=1.0,
        ):
            panel_b_boundary_violations.append(label)

    ribbon_overlap_violations = []
    ribbon_blocks = layout_registry["ribbon_blocks"]
    for index, (_, first_artists, first_label) in enumerate(ribbon_blocks):
        for _, second_artists, second_label in ribbon_blocks[index + 1 :]:
            if any(
                _bbox_intersects(
                    first.get_window_extent(renderer=renderer),
                    second.get_window_extent(renderer=renderer),
                )
                for first in first_artists
                for second in second_artists
            ):
                ribbon_overlap_violations.append(f"{first_label}|{second_label}")

    internal = (
        box_violations
        + owned_text_overlap_violations
        + (["panel_title_boundary"] if title_violation else [])
        + table_column_violations
        + panel_a_box_overlap_violations
        + panel_a_boundary_violations
        + panel_b_boundary_violations
        + ribbon_overlap_violations
    )
    require(not internal, "Internal layout violations: " + " | ".join(internal))
    return {
        "minimum_font_points": minimum,
        "canvas_clipped_text": clipped,
        "visible_text_count": len(visible),
        "box_owned_text_violations": box_violations,
        "owned_text_overlap_violations": owned_text_overlap_violations,
        "title_boundary_violation": title_violation,
        "table_column_violations": table_column_violations,
        "panel_a_box_overlap_violations": panel_a_box_overlap_violations,
        "panel_a_boundary_violations": panel_a_boundary_violations,
        "panel_b_boundary_violations": panel_b_boundary_violations,
        "ribbon_overlap_violations": ribbon_overlap_violations,
        "internal_layout_violations": internal,
    }


def render_images(fig: Any, staging: Path, dpi: int) -> list[Path]:
    paths = []
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{FIGURE_ID}.{extension}"
        temporary = staging / f".{FIGURE_ID}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata = {"Title": "ROSMAP and SEA-AD non-MT diagnostic", "Creator": "Validation-human figure renderer", "CreationDate": None, "ModDate": None}
        elif extension == "svg":
            metadata = {"Title": "ROSMAP and SEA-AD non-MT diagnostic", "Creator": "Validation-human figure renderer", "Date": None}
        else:
            metadata = {"Software": "Validation-human figure renderer"}
        fig.savefig(temporary, format=extension, dpi=dpi if extension == "png" else None, facecolor=WHITE, bbox_inches=None, pad_inches=0, metadata=metadata)
        require(temporary.stat().st_size > 1000, f"Rendered file is too small: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths


def check_record(check_id: str, passed: bool, observed: Any, expected: Any, details: str, *, severity: str = "blocking", status: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA, "figure_id": FIGURE_ID,
        "check_id": check_id, "severity": severity,
        "status": status or ("pass" if passed else "fail"),
        "observed": observed, "expected": expected, "details": details,
    }


def image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    svg = lookup[".svg"].read_text(encoding="utf-8")
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        embedded = image.info.get("dpi", (math.nan, math.nan))
        mode = image.mode
    return [
        check_record("image_export_set", set(lookup) == {".png", ".pdf", ".svg"}, "|".join(sorted(lookup)), ".pdf|.png|.svg", "Three image formats."),
        check_record("image_exports_nonempty", all(path.stat().st_size > 1000 for path in image_paths), "all >1000", "all >1000", "Image exports are nontrivial."),
        check_record("svg_searchable_text", "<text" in svg.lower(), "present", "present", "SVG text remains searchable."),
        check_record("svg_vector_paths", "<path" in svg.lower(), "present", "present", "SVG contains vector geometry."),
        check_record("pdf_signature", lookup[".pdf"].read_bytes()[:5] == b"%PDF-", lookup[".pdf"].read_bytes()[:5].decode("latin1"), "%PDF-", "PDF signature."),
        check_record("png_dimensions", (width, height) == (PNG_WIDTH, PNG_HEIGHT), f"{width}x{height}", f"{PNG_WIDTH}x{PNG_HEIGHT}", "12 × 5.3 inch canvas."),
        check_record("png_resolution", all(math.isfinite(v) and abs(v - dpi) <= 1 for v in embedded), f"{embedded[0]:.2f}|{embedded[1]:.2f}", f"{dpi}|{dpi}", "Embedded PNG resolution."),
        check_record("png_color_mode", mode in {"RGB", "RGBA"}, mode, "RGB or RGBA", "Slide-compatible color mode."),
    ]


def build_checks(bundle: Mapping[str, Any], plot_data: pd.DataFrame, fate: pd.DataFrame, reverse: pd.DataFrame, context: pd.DataFrame, image_paths: Sequence[Path], meta: Mapping[str, Any], dpi: int, visual_review_status: str) -> pd.DataFrame:
    svg = next(path for path in image_paths if path.suffix == ".svg").read_text(encoding="utf-8")
    assessable = plot_data["seaad_assessability"].eq("assessable")
    ctx = one_row(context, "coverage context")
    checks = [
        check_record("upstream_statuses", True, "Phase12|Phase18|VH09|VH10A|VH10B|VH10D validated_complete", "all validated_complete", "Validated during loading."),
        check_record("frozen_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS), len(bundle["input_digests"]), len(INPUT_PATHS), "Every input matches frozen SHA-256."),
        check_record("plot_unit_count", len(plot_data) == 21, len(plot_data), 21, "Frozen ROSMAP non-MT selected units."),
        check_record("plot_keys_unique", not plot_data.duplicated(["broad_network", "gene"]).any(), "unique", "unique", "One trace row per network-gene unit."),
        check_record("assessability_split", int(assessable.sum()) == 17 and int((~assessable).sum()) == 4, f"{assessable.sum()}|{(~assessable).sum()}", "17|4", "Assessable versus not-testable split."),
        check_record("not_testable_all_opc", set(plot_data.loc[~assessable, "broad_network"]) == {"OPCs"}, "OPCs", "OPCs", "All four not-testable units are OPC."),
        check_record("support_split", int((assessable & plot_data["seaad_qualifying_return_count"].eq(0)).sum()) == 13 and int((assessable & plot_data["seaad_qualifying_return_count"].eq(1)).sum()) == 4, f"{(assessable & plot_data['seaad_qualifying_return_count'].eq(0)).sum()}|{(assessable & plot_data['seaad_qualifying_return_count'].eq(1)).sum()}", "13|4", "Qualifying SEA-AD support among assessable units."),
        check_record("one_return_identities", set(zip(plot_data.loc[plot_data["seaad_qualifying_return_count"].eq(1), "broad_network"], plot_data.loc[plot_data["seaad_qualifying_return_count"].eq(1), "gene"])) == EXPECTED_ONE_RETURN, "exact", "exact", "Four named one-return units."),
        check_record("final_selection_zero", not plot_data["seaad_final_driver_candidate"].map(truth).any(), 0, 0, "No ROSMAP non-MT unit passed SEA-AD aggregate selection."),
        check_record("fate_counts", fate["unit_count"].astype(int).tolist() == [21, 4, 17, 13, 4, 0], str(fate["unit_count"].astype(int).tolist()), "[21,4,17,13,4,0]", "Fate tree arithmetic."),
        check_record("reverse_rows", len(reverse) == 5 and reverse["gene"].tolist() == [gene for _, gene in REVERSE_ORDER], str(reverse["gene"].tolist()), str([gene for _, gene in REVERSE_ORDER]), "Five SEA-AD reverse lookups."),
        check_record("reverse_none_selected", not reverse["rosmap_terminal_candidate_status"].eq("driver_candidate").any(), "none", "none", "No reverse lookup passed ROSMAP final gates."),
        check_record("rpl30_excluded_returns", as_int(reverse.loc[reverse["gene"].eq("RPL30"), "excluded_size3_primary_return_count"].iloc[0]) == 2, reverse.loc[reverse["gene"].eq("RPL30"), "excluded_size3_primary_return_count"].iloc[0], 2, "RPL30 has only two primary size-3 returns excluded by the Phase 18 minimum-10 rule."),
        check_record("kansl1l_no_primary_return", reverse.loc[reverse["gene"].eq("KANSL1L"), "outcome_id"].iloc[0] == "no_explicit_primary_return", reverse.loc[reverse["gene"].eq("KANSL1L"), "outcome_id"].iloc[0], "no_explicit_primary_return", "KANSL1L has no explicit primary ROSMAP return."),
        check_record("run_context", as_int(ctx["rosmap_included_runs"]) == 161 and as_int(ctx["seaad_kda_calls"]) == 42 and as_int(ctx["seaad_m_e33_calls"]) == 40, f"{ctx['rosmap_included_runs']}|{ctx['seaad_kda_calls']}|{ctx['seaad_m_e33_calls']}", "161|42|40", "Frozen run counts."),
        check_record("query_size_floors", as_int(ctx["rosmap_effective_query_floor"]) == 10 and as_int(ctx["seaad_effective_query_floor"]) == 3, f"{ctx['rosmap_effective_query_floor']}|{ctx['seaad_effective_query_floor']}", "10|3", "Observed minimum effective query sizes among included ROSMAP and eligible SEA-AD runs."),
        check_record("donor_limited_groups", set(str(ctx["seaad_donor_limited_groups"]).split("|")) == UNAVAILABLE_GROUPS, ctx["seaad_donor_limited_groups"], "F_e2|M_e2|M_e4", "SEA-AD donor-limited strata."),
        check_record("unavailable_support_units", as_int(ctx["units_with_rosmap_support_in_donor_limited_group"]) == 20, ctx["units_with_rosmap_support_in_donor_limited_group"], 20, "ROSMAP support includes at least one unavailable SEA-AD stratum for 20 units."),
        check_record("causal_guardrail_visible", "Support need not be exclusive" in svg and "not a sole cause" in svg and "assessable" in svg, "present", "present", "Coverage context is not presented as exclusive or causal."),
        check_record("all_named_units_visible", all(gene in svg for gene in ["DYNLT1", "RPS15", "RPLP1", "RPL38", "ANKRD11", "FTL", "NCOA1"] + [gene for _, gene in REVERSE_ORDER]), "present", "present", "All diagnostic and reverse-lookup genes are searchable."),
        check_record("minimum_font_size", meta["minimum_font_points"] >= 16.0, meta["minimum_font_points"], ">=16", "Projection-scale typography."),
        check_record("canvas_text_clipping", not meta["canvas_clipped_text"], len(meta["canvas_clipped_text"]), 0, "No text leaves canvas."),
        check_record("box_owned_text_containment", not meta["box_owned_text_violations"], len(meta["box_owned_text_violations"]), 0, "Every node, table-row, and ribbon label remains inside its owning box."),
        check_record("box_owned_text_nonoverlap", not meta["owned_text_overlap_violations"], len(meta["owned_text_overlap_violations"]), 0, "Text elements sharing an owning box do not overlap."),
        check_record("panel_title_separation", not meta["title_boundary_violation"], int(meta["title_boundary_violation"]), 0, "Panel A title clears the Panel B label."),
        check_record("table_column_separation", not meta["table_column_violations"], len(meta["table_column_violations"]), 0, "Network/gene labels and outcomes remain on their assigned sides of the divider."),
        check_record("panel_a_box_boundary_separation", not meta["panel_a_box_overlap_violations"], len(meta["panel_a_box_overlap_violations"]), 0, "Adjacent Panel A box outlines remain separated."),
        check_record("panel_a_box_boundaries_visible", not meta["panel_a_boundary_violations"], len(meta["panel_a_boundary_violations"]), 0, "Every Panel A box outline remains inside the panel canvas."),
        check_record("panel_b_row_boundaries_visible", not meta["panel_b_boundary_violations"], len(meta["panel_b_boundary_violations"]), 0, "Every Panel B row outline remains inside the panel canvas."),
        check_record("ribbon_block_separation", not meta["ribbon_overlap_violations"], len(meta["ribbon_overlap_violations"]), 0, "The three coverage-ribbon blocks do not collide."),
        check_record("internal_layout_geometry", not meta["internal_layout_violations"], len(meta["internal_layout_violations"]), 0, "All registered internal layout guards pass."),
        check_record("no_vh05_vh06_inputs", not any("/05_" in path or "/06_" in path for path in bundle["input_digests"]), "none", "none", "No missing pseudobulk/QC inputs."),
    ]
    checks.extend(image_checks(image_paths, dpi))
    if visual_review_status == "complete":
        checks.extend([
            check_record("manual_color_review", True, "complete", "complete", "Reviewed at intended slide size in color.", severity="nonblocking"),
            check_record("manual_grayscale_review", True, "complete", "complete", "Reviewed in grayscale; redundant encodings remain clear.", severity="nonblocking"),
        ])
    else:
        checks.extend([
            check_record("manual_color_review", False, "pending", "complete", "Manual color review pending.", severity="nonblocking", status="pending"),
            check_record("manual_grayscale_review", False, "pending", "complete", "Manual grayscale review pending.", severity="nonblocking", status="pending"),
        ])
    frame = pd.DataFrame(checks)
    blocking = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking.empty, "Blocking checks failed: " + ", ".join(blocking["check_id"]))
    return frame


def documentation() -> tuple[str, str]:
    caption = """# ROSMAP–SEA-AD non-MT diagnostic: caption

**Why the frozen non-MT selected lists were disjoint.** Panel A traces the 21 frozen ROSMAP non-MT network–gene units into SEA-AD. Four OPC units were not testable because SEA-AD had no included OPC KDA run. Seventeen units were assessable in the matching broad network; 13 had no qualifying same-network SEA-AD run-level return and four had exactly one such return (Excitatory DYNLT1; Inhibitory RPS15, RPLP1, and RPL38). None passed final SEA-AD cross-run aggregate selection. Panel B reverses the comparison for the five SEA-AD non-MT selected units. HGSNAT, BEX3, and RPS27A had ROSMAP run evidence but did not pass the aggregate gate; RPL30 had only two primary size-3 returns excluded by the frozen ROSMAP minimum-query-size-10 rule and no included conservative support; KANSL1L had no explicit primary ROSMAP return. The coverage ribbon supplies context: ROSMAP had 161 included runs versus 42 SEA-AD calls, 40 of which were M_e33. Twenty of 21 ROSMAP units had support in at least one F_e2, M_e2, or M_e4 stratum that SEA-AD could not estimate because a disease arm had fewer than five independent donors. That support was not necessarily exclusive, the 17 units remain assessable, and the missing strata are not asserted to be the sole cause of zero final overlap. Not selected does not mean absent from the network or biologically disproved.
"""
    methods = f"""# ROSMAP–SEA-AD non-MT diagnostic: methods

The renderer reads validated Phase 12 KDA, archived Phase 18 selection, VH09 frozen ROSMAP units, and VH10A/VH10B/VH10D SEA-AD artifacts. It requires current `validated_complete` statuses, zero failed checks, registered artifact hashes where manifests are available, and frozen full-file SHA-256 values for every input. The diagnostic does not read VH05 or VH06.

ROSMAP non-MT units are exact `broad_network + gene` rows from the VH09 selected table. SEA-AD assessability and final-selection status come from the VH10D unit trace. A qualifying SEA-AD run-level return follows the frozen Phase 18 conservative-support gate: adjusted within-run q ≤ 0.05, overlap ≥ 2 query genes, and fold enrichment > 1 in the matching broad network. Phase 18 conservative-support rows provide ROSMAP support strata. The 20/21 context count means at least one conservative ROSMAP supporting run occurred in F_e2, M_e2, or M_e4; it does not require exclusive support in those strata. SEA-AD marks those three strata structurally unestimable because one disease arm contains fewer than five independent donors.

The reverse lookup uses the reclassified Phase 18 call-return audit for two-class aggregate q values. KANSL1L, absent from that explicit audit, is recovered from the registered Phase 18 gene-case summary. Phase 12 primary results verify the two Inhibitory RPL30 size-3 returns and the absence of an Oligodendrocyte KANSL1L primary return. The figure is titleless for slide composition, uses a 12 × 5.3 inch canvas with at least 16-point text, and exports searchable SVG, vector PDF, and a 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/{Path(__file__).name} \\
  --output-root results/figures/validation_human/{FIGURE_ID} \\
  --visual-review-status pending
```
"""
    return caption, methods


def table_rows(path: Path) -> int | str:
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0) if path.suffix == ".tsv" else "NA"


def build_artifacts(bundle: Mapping[str, Any], staging: Path, renderer: Path) -> pd.DataFrame:
    rows = []
    for relative, digest in sorted(bundle["input_digests"].items()):
        path = bundle["project_root"] / relative
        validation_state = "frozen_direct_sha256" if relative.endswith("call_key_driver_returns.tsv") else "validated_frozen_input"
        rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "input", "logical_name": relative, "path": relative, "bytes": path.stat().st_size, "sha256": digest, "rows": table_rows(path), "validation_state": validation_state})
    relative_renderer = str(renderer.relative_to(bundle["project_root"]))
    rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "script", "logical_name": "renderer", "path": relative_renderer, "bytes": renderer.stat().st_size, "sha256": sha256_file(renderer), "rows": "NA", "validation_state": "validated_script"})
    for name in PAYLOAD_FILES:
        path = staging / name
        require(path.is_file() and path.stat().st_size > 0, f"Missing payload: {name}")
        rows.append({"schema_version": SCHEMA, "figure_id": FIGURE_ID, "artifact_role": "output", "logical_name": name, "path": name, "bytes": path.stat().st_size, "sha256": sha256_file(path), "rows": table_rows(path), "validation_state": "validated_output"})
    frame = pd.DataFrame(rows)
    require(frame["path"].is_unique, "Artifact paths duplicated")
    require(set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Output artifact scope changed")
    require(not frame["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status entered hash scope")
    return frame


def validate_output(project_root: Path, output_root: Path, *, expected_visual_status: str | None = None) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(output_root.is_dir(), f"Missing output directory: {output_root}")
    require(sorted(path.name for path in output_root.iterdir() if path.is_file()) == sorted(OUTPUT_FILES), "Output package file set changed")
    status = one_row(read_tsv(output_root / f"{FIGURE_ID}_status.tsv", dtype=str, keep_default_na=False), "figure status")
    require(status["schema_version"] == SCHEMA and status["figure_id"] == FIGURE_ID, "Figure status identity changed")
    visual = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual == expected_visual_status, "Visual-review status changed")
    require(status["validation_status"] == ("validated_complete" if visual == "complete" else "awaiting_visual_review"), "Figure validation status changed")
    checks = read_tsv(output_root / f"{FIGURE_ID}_checks.tsv", dtype=str, keep_default_na=False)
    require(not ((checks["severity"] == "blocking") & (checks["status"] != "pass")).any(), "Published package has failed blocking checks")
    if visual == "complete":
        require(checks["status"].eq("pass").all(), "Completed package has incomplete checks")
    artifacts_path = output_root / f"{FIGURE_ID}_artifacts.tsv"
    require(sha256_file(artifacts_path) == status["artifact_manifest_sha256"], "Artifact-manifest SHA changed")
    artifacts = read_tsv(artifacts_path, dtype=str, keep_default_na=False)
    require(set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Artifact output scope changed")
    for row in artifacts.itertuples(index=False):
        path = output_root / row.path if row.artifact_role == "output" else project_root / row.path
        require(path.is_file(), f"Missing artifact: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact digest changed: {row.path}")
    require(all(row["status"] == "pass" for row in image_checks([output_root / f"{FIGURE_ID}.{ext}" for ext in ("png", "pdf", "svg")], as_int(status["png_dpi"]))), "Published image checks failed")
    print(f"Validated figure package: {output_root}")


def publish(project_root: Path, output_root: Path, *, dpi: int, visual_review_status: str, force: bool) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    if output_root.exists() and not force:
        raise FileExistsError(f"Output exists; use --force for recoverable replacement: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{FIGURE_ID}.staging.", dir=output_root.parent))
    try:
        bundle = load_bundle(project_root)
        plot_data = build_plot_data(bundle)
        fate = build_fate_summary(plot_data)
        reverse = build_reverse_lookup(bundle)
        context = build_coverage_context(bundle, plot_data)
        fig, meta = draw_figure(plot_data, fate, reverse, context)
        image_paths = render_images(fig, staging, dpi)
        write_tsv(plot_data, staging / f"{FIGURE_ID}_plot_data.tsv")
        write_tsv(fate, staging / f"{FIGURE_ID}_fate_summary.tsv")
        write_tsv(reverse, staging / f"{FIGURE_ID}_reverse_lookup.tsv")
        write_tsv(context, staging / f"{FIGURE_ID}_coverage_context.tsv")
        caption, methods = documentation()
        write_text(staging / f"{FIGURE_ID}_caption.md", caption)
        write_text(staging / f"{FIGURE_ID}_methods.md", methods)
        checks = build_checks(bundle, plot_data, fate, reverse, context, image_paths, meta, dpi, visual_review_status)
        write_tsv(checks, staging / f"{FIGURE_ID}_checks.tsv")
        renderer = Path(__file__).resolve()
        artifacts = build_artifacts(bundle, staging, renderer)
        artifacts_path = staging / f"{FIGURE_ID}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        status = pd.DataFrame([{
            "schema_version": SCHEMA, "figure_id": FIGURE_ID,
            "validation_status": "validated_complete" if visual_review_status == "complete" and pending == 0 else "awaiting_visual_review",
            "visual_review_status": visual_review_status,
            "failed_blocking_checks": int(((checks["severity"] == "blocking") & (checks["status"] != "pass")).sum()),
            "pending_nonblocking_checks": int(((checks["severity"] == "nonblocking") & (checks["status"] != "pass")).sum()),
            "input_bundle_sha256": bundle["input_bundle_sha256"],
            "renderer_sha256": sha256_file(renderer),
            "artifact_manifest_sha256": sha256_file(artifacts_path),
            "figure_width_inches": FIGURE_WIDTH_IN, "figure_height_inches": FIGURE_HEIGHT_IN,
            "png_dpi": dpi, "png_width": PNG_WIDTH, "png_height": PNG_HEIGHT,
            "input_files": len(bundle["input_digests"]), "output_files": len(OUTPUT_FILES),
            "plot_data_rows": len(plot_data), "reverse_lookup_rows": len(reverse),
            "contract_scope": "non_mt_evidence_fate_and_reverse_lookup",
            "completed_utc": datetime.now(timezone.utc).isoformat(),
        }])
        write_tsv(status, staging / f"{FIGURE_ID}_status.tsv")
        validate_output(project_root, staging, expected_visual_status=visual_review_status)
        if output_root.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            output_root.replace(output_root.parent / f".{output_root.name}.backup.{timestamp}.{os.getpid()}")
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
        validate_output(project_root, resolve(project_root, args.validate_output))
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
