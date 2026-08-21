#!/usr/bin/env python3
"""Render frozen SEA-AD MT and non-MT key-driver circular figures.

The renderer consumes the compact, independently frozen VH10C display
contract.  It does not read ROSMAP candidate identities, VH10D overlap
results, or the unavailable full SEA-AD candidate-summary table, and it does
not recompute KDA, ACAT, BH correction, candidate gates, or ranks.
"""

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


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_two_case_circular_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_two_case_circular_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "seaad_two_case_circular_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches as mpatches  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from PIL import Image  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402


SCHEMA = "seaad_two_case_circular_figure_v1"
PLOT_SCHEMA = "seaad_two_case_circular_plot_data_v1"
LINK_SCHEMA = "seaad_two_case_circular_links_v1"
FIGURE_ID = "seaad_two_case_circular"
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 3_240
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 7.2
EVIDENCE_CAP = 15.0
TOP_PER_NETWORK = 5

CLASS_ORDER = ["mt_driver", "non_mt_driver"]
CLASS_LABELS = {"mt_driver": "MT drivers", "non_mt_driver": "Non-MT drivers"}
CLASS_BASENAMES = {
    "mt_driver": "seaad_mt_driver_circular",
    "non_mt_driver": "seaad_non_mt_driver_circular",
}
NETWORK_ORDER = [
    "Astrocytes",
    "Excitatory_neurons",
    "Inhibitory_neurons",
    "Microglia",
    "OPCs",
    "Oligodendrocytes",
    "Vasculature_cells",
]
NETWORK_LABELS = {
    "Astrocytes": "Astrocytes",
    "Excitatory_neurons": "Excitatory neurons",
    "Inhibitory_neurons": "Inhibitory neurons",
    "Microglia": "Microglia",
    "OPCs": "OPCs",
    "Oligodendrocytes": "Oligodendrocytes",
    "Vasculature_cells": "Vasculature",
}
NETWORK_COLORS = {
    "Astrocytes": "#009E73",
    "Excitatory_neurons": "#E69F00",
    "Inhibitory_neurons": "#0072B2",
    "Microglia": "#CC79A7",
    "OPCs": "#56B4E9",
    "Oligodendrocytes": "#F0E442",
    "Vasculature_cells": "#D55E00",
}

NAVY = "#344E73"
TEXT = "#202020"
MID = "#5F6770"
WHITE = "#FFFFFF"
RANKED_TRACK = "#F1F3F5"
UNUSED_TRACK = "#E2E5E9"
NO_PASS_TRACK = "#C7CDD4"
NO_PASS_EDGE = "#747D87"
NOT_TESTABLE_TRACK = "#959FAA"
NOT_TESTABLE_EDGE = "#545E69"
REFERENCE = "#CBD0D5"
LINK = "#666666"

OUTPUT_FILES = [
    "seaad_mt_driver_circular.png",
    "seaad_mt_driver_circular.pdf",
    "seaad_mt_driver_circular.svg",
    "seaad_non_mt_driver_circular.png",
    "seaad_non_mt_driver_circular.pdf",
    "seaad_non_mt_driver_circular.svg",
    f"{FIGURE_ID}_plot_data.tsv",
    f"{FIGURE_ID}_links.tsv",
    f"{FIGURE_ID}_caption.md",
    f"{FIGURE_ID}_methods.md",
    f"{FIGURE_ID}_checks.tsv",
    f"{FIGURE_ID}_artifacts.tsv",
    f"{FIGURE_ID}_status.tsv",
]
PAYLOAD_FILES = OUTPUT_FILES[:-2]

INPUT_PATHS = {
    "vh10c_status": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/status.tsv"
    ),
    "seaad_top5": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/seaad_top5.tsv"
    ),
    "seaad_list_status": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/seaad_list_status.tsv"
    ),
    "selection_checks": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/selection_checks.tsv"
    ),
    "selection_freeze": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/seaad_selection_freeze.tsv"
    ),
    "selection_artifacts": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10c_seaad_selection/artifacts.tsv"
    ),
    "run_manifest": (
        "results/validation_human/10_seaad_kda_rediscovery/"
        "10a_inputs/seaad_kda_run_manifest.tsv"
    ),
    "validation_config": "scripts/validation_human/seaad_phase18_validation_config.yml",
    "phase18_annotation": (
        "results/minerva_production/09_annotate_genes/"
        "gene_annotation_master.tsv.gz"
    ),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output-root",
        default="results/figures/validation_human/seaad_two_case_circular",
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


def is_missing(value: Any) -> bool:
    return str(value).strip() in {"", "NA", "None", "nan"}


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


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8", errors="strict"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_tsv(path: Path, **kwargs: Any) -> pd.DataFrame:
    require(path.is_file(), f"Missing TSV: {path}")
    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        **kwargs,
    )


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


def resolve_inputs(project_root: Path) -> dict[str, Path]:
    paths = {key: project_root / value for key, value in INPUT_PATHS.items()}
    missing = [key for key, path in paths.items() if not path.is_file()]
    require(not missing, "Missing required figure inputs: " + ", ".join(missing))
    return paths


def _validate_registered_compact_files(
    paths: Mapping[str, Path], artifacts: pd.DataFrame
) -> None:
    require_columns(
        artifacts,
        [
            "artifact",
            "path",
            "artifact_role",
            "bytes",
            "digest_algorithm",
            "digest_scope",
            "digest_value",
        ],
        "VH10C artifacts",
    )
    require(artifacts["artifact"].is_unique, "VH10C artifact names are duplicated")
    by_name = artifacts.set_index("artifact", drop=False)
    required = {
        "seaad_top5.tsv": paths["seaad_top5"],
        "seaad_list_status.tsv": paths["seaad_list_status"],
        "seaad_selection_freeze.tsv": paths["selection_freeze"],
        "selection_checks.tsv": paths["selection_checks"],
    }
    for name, path in required.items():
        require(name in by_name.index, f"VH10C artifact registry omits {name}")
        row = by_name.loc[name]
        require(row["artifact_role"] == "result", f"Unexpected VH10C role for {name}")
        require(row["digest_algorithm"] == "sha256", f"Unexpected digest for {name}")
        require(row["digest_scope"] == "full_file", f"Unexpected digest scope for {name}")
        require(path.stat().st_size == as_int(row["bytes"], f"{name} bytes"), f"VH10C byte count changed: {name}")
        require(sha256_file(path) == row["digest_value"], f"VH10C SHA-256 changed: {name}")


def _selected_annotation(
    annotation_path: Path, selected_symbols: set[str]
) -> pd.DataFrame:
    columns = [
        "symbol_hgnc_current",
        "is_mitocarta3",
        "is_mtDNA_gene",
        "extended_reference_member",
        "mito_tier",
    ]
    annotation = read_tsv(annotation_path, usecols=columns)
    annotation = annotation.loc[annotation["symbol_hgnc_current"].isin(selected_symbols)].copy()
    require(set(annotation["symbol_hgnc_current"]) == selected_symbols, "Selected symbols are missing Phase 18 annotation")
    scientific = columns[1:]
    for symbol, group in annotation.groupby("symbol_hgnc_current", sort=False):
        require(
            len(group[scientific].drop_duplicates()) == 1,
            f"Conflicting Phase 18 marker annotation for {symbol}",
        )
    return annotation.drop_duplicates("symbol_hgnc_current").reset_index(drop=True)


def load_bundle(project_root: Path) -> dict[str, Any]:
    """Load and validate the compact frozen SEA-AD display contract."""

    project_root = Path(project_root).resolve()
    paths = resolve_inputs(project_root)
    status = read_tsv(paths["vh10c_status"])
    top5 = read_tsv(paths["seaad_top5"])
    list_status = read_tsv(paths["seaad_list_status"])
    selection_checks = read_tsv(paths["selection_checks"])
    freeze = read_tsv(paths["selection_freeze"])
    artifacts = read_tsv(paths["selection_artifacts"])
    run_manifest = read_tsv(paths["run_manifest"])
    config = read_yaml(paths["validation_config"])

    status_row = one_row(status, "VH10C status")
    require_columns(
        status,
        [
            "phase",
            "validation_status",
            "failed_checks",
            "config_sha256",
            "candidate_units",
            "passing_candidate_units",
            "selected_top5_units",
            "selected_unique_genes",
            "testable_networks",
            "freeze_sha256",
        ],
        "VH10C status",
    )
    require(status_row["phase"] == "VH10C", "Unexpected VH10C phase label")
    require(status_row["validation_status"] == "validated_complete", "VH10C is not validated_complete")
    require(status_row["failed_checks"] in {"", "0"}, "VH10C records failed checks")

    require_columns(selection_checks, ["check", "passed"], "selection checks")
    require(len(selection_checks) > 0, "Selection checks are empty")
    require(selection_checks["passed"].map(truth).all(), "At least one VH10C selection check failed")

    freeze_row = one_row(freeze, "SEA-AD selection freeze")
    require_columns(
        freeze,
        [
            "schema_version",
            "query_rule_id",
            "result_tier_id",
            "candidate_units",
            "passing_candidate_units",
            "selected_top5_units",
            "selected_unique_genes",
            "selected_keys_sha256",
            "top5_sha256",
            "config_sha256",
            "rosmap_candidate_files_read",
            "freeze_status",
        ],
        "selection freeze",
    )
    require(freeze_row["schema_version"] == "seaad_kda_selection_freeze_v1", "Unexpected SEA-AD freeze schema")
    require(not truth(freeze_row["rosmap_candidate_files_read"]), "ROSMAP candidates were read before SEA-AD freeze")
    require(freeze_row["freeze_status"] == "independent_seaad_selection_frozen", "SEA-AD selection is not independently frozen")
    require(sha256_file(paths["selection_freeze"]) == status_row["freeze_sha256"], "VH10C freeze hash disagrees with status")
    require(sha256_file(paths["seaad_top5"]) == freeze_row["top5_sha256"], "SEA-AD top-five hash disagrees with freeze")
    require(sha256_file(paths["validation_config"]) == freeze_row["config_sha256"], "Validation-config hash disagrees with freeze")
    require(status_row["config_sha256"] == freeze_row["config_sha256"], "VH10C status/config hash mismatch")
    _validate_registered_compact_files(paths, artifacts)

    vh10 = config.get("vh10", {})
    analysis = vh10.get("analysis", {})
    selection = vh10.get("selection", {})
    network_order = list(vh10.get("network_order", []))
    query_rule_id = str(analysis.get("query_rule_id", ""))
    result_tier_id = str(analysis.get("result_tier_id", ""))
    driver_classes = list(selection.get("driver_classes", []))
    display_limit = as_int(selection.get("display_limit"), "display limit")
    require(network_order == NETWORK_ORDER, "SEA-AD network order changed")
    require(driver_classes == CLASS_ORDER, "SEA-AD driver-class order changed")
    require(display_limit == TOP_PER_NETWORK, "SEA-AD display limit changed")
    require(as_float(selection.get("minimum_coverage")) == 0.80, "SEA-AD coverage gate changed")
    require(as_float(selection.get("aggregate_q_threshold")) == 0.05, "SEA-AD aggregate-q gate changed")
    require(as_int(selection.get("minimum_conservative_supporting_runs")) == 1, "SEA-AD conservative-support gate changed")
    require(query_rule_id == "phase18_parity_query", "SEA-AD query rule changed")
    require(result_tier_id == "phase18_parity_query__min3_all", "SEA-AD result tier changed")
    require(freeze_row["query_rule_id"] == query_rule_id, "Freeze query rule differs from config")
    require(freeze_row["result_tier_id"] == result_tier_id, "Freeze result tier differs from config")

    top_columns = [
        "query_rule_id",
        "result_tier_id",
        "broad_network",
        "case_order",
        "case_id",
        "list_status",
        "total_passing_candidate_count",
        "displayed_candidate_count",
        "display_rank",
        "current_symbol",
        "aggregate_acat_p",
        "aggregate_acat_q",
        "coverage_numerator",
        "coverage_denominator",
        "coverage_fraction",
        "conservative_support_count",
        "evidence_tier",
        "empty_result_reason",
    ]
    require_columns(top5, top_columns, "SEA-AD top five")
    require(len(top5) == 22, f"Expected 22 SEA-AD top-list rows, found {len(top5)}")
    require(set(top5["query_rule_id"]) == {query_rule_id}, "Top-list query rule changed")
    require(set(top5["result_tier_id"]) == {result_tier_id}, "Top-list result tier changed")
    require(set(top5["broad_network"]) == set(NETWORK_ORDER), "Top-list network scope changed")
    require(set(top5["case_id"]) == set(CLASS_ORDER), "Top-list driver classes changed")
    require(
        (top5["case_order"].map(as_int) == top5["case_id"].map({"mt_driver": 1, "non_mt_driver": 2})).all(),
        "Top-list case order changed",
    )

    ranked = top5.loc[top5["list_status"].eq("ranked_candidates")].copy()
    sentinels = top5.loc[~top5["list_status"].eq("ranked_candidates")].copy()
    require(len(ranked) == 13 and len(sentinels) == 9, "SEA-AD ranked/sentinel row partition changed")
    require((~ranked["current_symbol"].map(is_missing)).all(), "A ranked SEA-AD row lacks a symbol")
    require(sentinels["current_symbol"].map(is_missing).all(), "An empty-list sentinel contains a symbol")
    require((ranked["coverage_fraction"].map(as_float) >= 0.80).all(), "A ranked row fails coverage")
    require((ranked["conservative_support_count"].map(as_int) >= 1).all(), "A ranked row lacks conservative support")
    require((ranked["aggregate_acat_q"].map(as_float) <= 0.05).all(), "A ranked row fails aggregate q")
    require((ranked["aggregate_acat_q"].map(as_float) > 0).all(), "A ranked row has nonpositive aggregate q")
    require(not ranked.duplicated(["broad_network", "current_symbol", "case_id"]).any(), "Selected SEA-AD keys are duplicated")

    for (network, case_id), group in ranked.groupby(["broad_network", "case_id"], sort=False):
        group = group.copy()
        ranks = sorted(group["display_rank"].map(as_int).tolist())
        require(ranks == list(range(1, len(group) + 1)), f"Noncontinuous ranks for {network}/{case_id}")
        total = {as_int(value) for value in group["total_passing_candidate_count"]}
        displayed = {as_int(value) for value in group["displayed_candidate_count"]}
        require(total == {len(group)} == displayed, f"SEA-AD list is backfilled or truncated: {network}/{case_id}")
        ordered = group.assign(
            _q=group["aggregate_acat_q"].map(as_float),
            _p=group["aggregate_acat_p"].map(as_float),
        ).sort_values(
            ["_q", "_p", "current_symbol"],
            kind="mergesort",
        )
        require(
            ordered["display_rank"].map(as_int).tolist() == list(range(1, len(group) + 1)),
            f"Stored SEA-AD order differs from q/P/symbol order: {network}/{case_id}",
        )

    selected_key_values = sorted(
        f"{row.broad_network}\t{row.current_symbol}\t{row.case_id}\t{row.display_rank}"
        for row in ranked.itertuples(index=False)
    )
    require(
        sha256_strings(selected_key_values) == freeze_row["selected_keys_sha256"],
        "SEA-AD selected-key hash disagrees with freeze",
    )

    list_columns = [
        "query_rule_id",
        "result_tier_id",
        "broad_network",
        "case_id",
        "list_status",
        "total_passing_candidate_count",
        "displayed_candidate_count",
        "output_rows",
    ]
    require_columns(list_status, list_columns, "SEA-AD list status")
    require(len(list_status) == 14, f"Expected 14 SEA-AD lists, found {len(list_status)}")
    require(not list_status.duplicated(["broad_network", "case_id"]).any(), "SEA-AD list statuses are duplicated")
    expected_keys = {(network, case_id) for network in NETWORK_ORDER for case_id in CLASS_ORDER}
    require(set(zip(list_status["broad_network"], list_status["case_id"])) == expected_keys, "SEA-AD list grid changed")
    status_counts = list_status["list_status"].value_counts().to_dict()
    require(
        status_counts == {
            "ranked_candidates": 5,
            "no_passing_candidate": 5,
            "not_testable_no_included_runs": 4,
        },
        f"SEA-AD list-status partition changed: {status_counts}",
    )
    for row in list_status.itertuples(index=False):
        group = top5.loc[
            top5["broad_network"].eq(row.broad_network)
            & top5["case_id"].eq(row.case_id)
        ]
        require(len(group) == as_int(row.output_rows), f"Top-list row count differs for {row.broad_network}/{row.case_id}")
        require(set(group["list_status"]) == {row.list_status}, f"Top/list status mismatch for {row.broad_network}/{row.case_id}")
        require(
            max(group["displayed_candidate_count"].map(as_int)) == as_int(row.displayed_candidate_count),
            f"Displayed count mismatch for {row.broad_network}/{row.case_id}",
        )

    require_columns(run_manifest, ["broad_network", "terminal_status"], "SEA-AD run manifest")
    require(len(run_manifest) == 1_548, "SEA-AD structural run-manifest size changed")
    active_states = {"eligible_small_query", "eligible_phase18_sized"}
    active_runs = run_manifest.loc[run_manifest["terminal_status"].isin(active_states)].copy()
    require(len(active_runs) == 42, "SEA-AD included KDA-run count changed")
    active_by_network = {
        network: int((active_runs["broad_network"] == network).sum())
        for network in NETWORK_ORDER
    }
    require(
        active_by_network
        == {
            "Astrocytes": 1,
            "Excitatory_neurons": 20,
            "Inhibitory_neurons": 16,
            "Microglia": 1,
            "OPCs": 0,
            "Oligodendrocytes": 4,
            "Vasculature_cells": 0,
        },
        f"SEA-AD included-run counts by network changed: {active_by_network}",
    )
    for row in list_status.itertuples(index=False):
        unavailable = row.list_status == "not_testable_no_included_runs"
        require(unavailable == (active_by_network[row.broad_network] == 0), f"List testability disagrees with run manifest: {row.broad_network}/{row.case_id}")

    require(as_int(status_row["candidate_units"]) == 38_788, "VH10C candidate-unit count changed")
    require(as_int(status_row["passing_candidate_units"]) == 13, "VH10C passing count changed")
    require(as_int(status_row["selected_top5_units"]) == 13, "VH10C selected count changed")
    require(as_int(status_row["selected_unique_genes"]) == 11, "VH10C selected-symbol count changed")
    require(as_int(status_row["testable_networks"]) == 5, "VH10C testable-network count changed")
    for field, expected in (
        ("candidate_units", 38_788),
        ("passing_candidate_units", 13),
        ("selected_top5_units", 13),
        ("selected_unique_genes", 11),
    ):
        require(as_int(freeze_row[field]) == expected, f"Freeze {field} changed")

    annotation_item = vh10.get("input_authority", {}).get("phase18_annotation", {})
    annotation_relative = str(annotation_item.get("path", ""))
    require(annotation_relative == INPUT_PATHS["phase18_annotation"], "Phase 18 annotation path changed")
    require(sha256_file(paths["phase18_annotation"]) == annotation_item.get("sha256"), "Phase 18 annotation hash changed")
    selected_symbols = set(ranked["current_symbol"])
    annotation = _selected_annotation(paths["phase18_annotation"], selected_symbols)
    annotation_map = annotation.set_index("symbol_hgnc_current")
    for row in ranked.itertuples(index=False):
        ann = annotation_map.loc[row.current_symbol]
        is_core = truth(ann["is_mitocarta3"])
        require(is_core == (row.case_id == "mt_driver"), f"Driver class disagrees with annotation: {row.current_symbol}")
    mt_symbols = ranked.loc[ranked["case_id"].eq("mt_driver"), "current_symbol"]
    require(all(truth(annotation_map.loc[symbol, "is_mtDNA_gene"]) for symbol in mt_symbols), "Not every selected MT unit is mtDNA encoded")
    non_mt_symbols = ranked.loc[ranked["case_id"].eq("non_mt_driver"), "current_symbol"]
    extended_non_mt = {
        symbol
        for symbol in non_mt_symbols
        if truth(annotation_map.loc[symbol, "extended_reference_member"])
    }
    require(extended_non_mt == {"RPS27A"}, f"Extended non-MT marker set changed: {extended_non_mt}")

    mt_count = int((ranked["case_id"] == "mt_driver").sum())
    non_mt_count = int((ranked["case_id"] == "non_mt_driver").sum())
    require((mt_count, non_mt_count) == (8, 5), "SEA-AD selected class counts changed")
    require(ranked["current_symbol"].nunique() == 11, "SEA-AD unique selected-symbol count changed")

    input_digests = {
        str(path.relative_to(project_root)): sha256_file(path)
        for path in paths.values()
    }
    bundle_digest = hashlib.sha256()
    for relative, digest in sorted(input_digests.items()):
        bundle_digest.update(f"{relative}\t{digest}\n".encode("utf-8"))

    return {
        "project_root": project_root,
        "paths": paths,
        "input_digests": input_digests,
        "input_bundle_sha256": bundle_digest.hexdigest(),
        "status": status,
        "top5": top5,
        "ranked": ranked,
        "list_status": list_status,
        "selection_checks": selection_checks,
        "freeze": freeze,
        "run_manifest": run_manifest,
        "annotation": annotation,
        "config": config,
        "query_rule_id": query_rule_id,
        "result_tier_id": result_tier_id,
        "network_order": network_order,
        "driver_classes": driver_classes,
        "display_limit": display_limit,
        "active_runs_by_network": active_by_network,
        "selected_units": len(ranked),
        "selected_mt_units": mt_count,
        "selected_non_mt_units": non_mt_count,
        "selected_class_counts": {
            "mt_driver": mt_count,
            "non_mt_driver": non_mt_count,
        },
        "selected_symbols": ranked["current_symbol"].nunique(),
        "candidate_summary_present": (
            project_root
            / "results/validation_human/10_seaad_kda_rediscovery/"
            "10c_seaad_selection/seaad_candidate_summary.tsv.gz"
        ).is_file(),
    }


def _geometry() -> pd.DataFrame:
    network_gap = 6.0
    slot_gap = 1.0
    slots = len(NETWORK_ORDER) * TOP_PER_NETWORK
    total_gap = len(NETWORK_ORDER) * network_gap + (slots - len(NETWORK_ORDER)) * slot_gap
    slot_width = (360.0 - total_gap) / slots
    cursor = 90.0
    rows: list[dict[str, Any]] = []
    for network_index, network in enumerate(NETWORK_ORDER, start=1):
        for rank in range(1, TOP_PER_NETWORK + 1):
            start = cursor
            end = start - slot_width
            rows.append(
                {
                    "broad_network": network,
                    "network_display_order": network_index,
                    "slot_rank": rank,
                    "sector_start_degrees": start,
                    "sector_end_degrees": end,
                    "sector_mid_degrees": (start + end) / 2.0,
                }
            )
            cursor = end - (slot_gap if rank < TOP_PER_NETWORK else network_gap)
    geometry = pd.DataFrame(rows)
    require(len(geometry) == 35, "Circular geometry must contain 35 slots")
    require(abs(slot_width - 8.285714285714286) < 1e-12, "Circular slot width changed")
    return geometry


def build_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    """Build the exact 70-row, fixed-slot plotting table."""

    top5 = bundle["top5"]
    list_status = bundle["list_status"].set_index(["broad_network", "case_id"])
    annotations = bundle["annotation"].set_index("symbol_hgnc_current")
    geometry = _geometry()
    top5_relative = str(bundle["paths"]["seaad_top5"].relative_to(bundle["project_root"]))
    annotation_relative = str(bundle["paths"]["phase18_annotation"].relative_to(bundle["project_root"]))
    top5_sha = bundle["input_digests"][top5_relative]
    annotation_sha = bundle["input_digests"][annotation_relative]
    rows: list[dict[str, Any]] = []

    for class_index, case_id in enumerate(CLASS_ORDER, start=1):
        for geometry_row in geometry.itertuples(index=False):
            list_row = list_status.loc[(geometry_row.broad_network, case_id)]
            matches = top5.loc[
                top5["broad_network"].eq(geometry_row.broad_network)
                & top5["case_id"].eq(case_id)
                & top5["list_status"].eq("ranked_candidates")
                & top5["display_rank"].map(
                    lambda value: not is_missing(value) and as_int(value) == geometry_row.slot_rank
                )
            ]
            require(len(matches) <= 1, "Duplicate candidate at one circular slot")
            occupied = len(matches) == 1
            if occupied:
                selected = matches.iloc[0]
                symbol = selected["current_symbol"]
                ann = annotations.loc[symbol]
                q_value = as_float(selected["aggregate_acat_q"])
                score = -math.log10(max(q_value, float.fromhex("0x1.0p-1022")))
                capped_score = min(score, EVIDENCE_CAP)
                slot_status = "ranked_candidate"
            else:
                selected = None
                symbol = None
                ann = None
                score = None
                capped_score = None
                if list_row["list_status"] == "ranked_candidates":
                    slot_status = "unused_display_slot"
                elif list_row["list_status"] == "no_passing_candidate":
                    slot_status = "no_passing_candidate_slot"
                elif list_row["list_status"] == "not_testable_no_included_runs":
                    slot_status = "not_testable_no_included_runs_slot"
                else:
                    raise RuntimeError(f"Unsupported SEA-AD list status: {list_row['list_status']}")

            style = {
                "ranked_candidate": (RANKED_TRACK, "#FFFFFF", "solid", ""),
                "unused_display_slot": (UNUSED_TRACK, "#FFFFFF", "solid", ""),
                "no_passing_candidate_slot": (NO_PASS_TRACK, NO_PASS_EDGE, "solid", ""),
                "not_testable_no_included_runs_slot": (
                    NOT_TESTABLE_TRACK,
                    NOT_TESTABLE_EDGE,
                    "dashed",
                    "xx",
                ),
            }[slot_status]
            rows.append(
                {
                    "schema_version": PLOT_SCHEMA,
                    "figure_id": FIGURE_ID,
                    "class_order": class_index,
                    "case_id": case_id,
                    "case_label": CLASS_LABELS[case_id],
                    "query_rule_id": bundle["query_rule_id"],
                    "result_tier_id": bundle["result_tier_id"],
                    "broad_network": geometry_row.broad_network,
                    "network_display_order": geometry_row.network_display_order,
                    "display_network": NETWORK_LABELS[geometry_row.broad_network],
                    "network_color": NETWORK_COLORS[geometry_row.broad_network],
                    "network_included_run_count": bundle["active_runs_by_network"][geometry_row.broad_network],
                    "slot_rank": geometry_row.slot_rank,
                    "slot_status": slot_status,
                    "list_status": list_row["list_status"],
                    "total_passing_candidate_count": as_int(list_row["total_passing_candidate_count"]),
                    "displayed_candidate_count": as_int(list_row["displayed_candidate_count"]),
                    "current_symbol": symbol,
                    "display_rank": as_int(selected["display_rank"]) if occupied else None,
                    "is_core_mito": truth(ann["is_mitocarta3"]) if occupied else None,
                    "is_mtdna_gene": truth(ann["is_mtDNA_gene"]) if occupied else None,
                    "extended_reference_member": truth(ann["extended_reference_member"]) if occupied else None,
                    "mito_tier": ann["mito_tier"] if occupied else None,
                    "coverage_numerator": as_int(selected["coverage_numerator"]) if occupied else None,
                    "coverage_denominator": as_int(selected["coverage_denominator"]) if occupied else None,
                    "coverage_fraction": as_float(selected["coverage_fraction"]) if occupied else None,
                    "conservative_support_count": as_int(selected["conservative_support_count"]) if occupied else None,
                    "aggregate_acat_p": as_float(selected["aggregate_acat_p"]) if occupied else None,
                    "aggregate_acat_q": as_float(selected["aggregate_acat_q"]) if occupied else None,
                    "negative_log10_acat_q": score,
                    "capped_negative_log10_acat_q": capped_score,
                    "display_score": capped_score / EVIDENCE_CAP if occupied else None,
                    "evidence_tier": selected["evidence_tier"] if occupied else None,
                    "selected_network_count_within_class": None,
                    "sector_start_degrees": geometry_row.sector_start_degrees,
                    "sector_end_degrees": geometry_row.sector_end_degrees,
                    "sector_mid_degrees": geometry_row.sector_mid_degrees,
                    "slot_facecolor": style[0],
                    "slot_edgecolor": style[1],
                    "slot_linestyle": style[2],
                    "slot_hatch": style[3],
                    "source_top5_path": top5_relative,
                    "source_top5_sha256": top5_sha,
                    "source_annotation_path": annotation_relative,
                    "source_annotation_sha256": annotation_sha,
                }
            )

    plot_data = pd.DataFrame(rows)
    occupied = plot_data["slot_status"].eq("ranked_candidate")
    recurrence = (
        plot_data.loc[occupied]
        .groupby(["case_id", "current_symbol"], sort=False)
        .size()
        .to_dict()
    )
    plot_data.loc[occupied, "selected_network_count_within_class"] = [
        recurrence[(row.case_id, row.current_symbol)]
        for row in plot_data.loc[occupied].itertuples(index=False)
    ]
    require(len(plot_data) == 70, "Fixed circular plot data must contain 70 slots")
    require(plot_data.groupby("case_id").size().to_dict() == {"mt_driver": 35, "non_mt_driver": 35}, "Each driver class must contain 35 slots")
    expected_states = {
        "ranked_candidate": 13,
        "unused_display_slot": 12,
        "no_passing_candidate_slot": 25,
        "not_testable_no_included_runs_slot": 20,
    }
    require(plot_data["slot_status"].value_counts().to_dict() == expected_states, "Fixed-slot state counts changed")
    return plot_data


def build_links(plot_data: pd.DataFrame) -> pd.DataFrame:
    """Build highest-evidence-to-other recurrence links within each class."""

    occupied = plot_data.loc[plot_data["slot_status"].eq("ranked_candidate")].copy()
    rows: list[dict[str, Any]] = []
    for (case_id, symbol), group in occupied.groupby(["case_id", "current_symbol"], sort=True):
        if len(group) <= 1:
            continue
        group = group.sort_values(
            ["negative_log10_acat_q", "network_display_order", "slot_rank"],
            ascending=[False, True, True],
            kind="mergesort",
        )
        anchor = group.iloc[0]
        for _, target in group.iloc[1:].iterrows():
            rows.append(
                {
                    "schema_version": LINK_SCHEMA,
                    "figure_id": FIGURE_ID,
                    "case_id": case_id,
                    "current_symbol": symbol,
                    "selected_network_count_within_class": len(group),
                    "anchor_broad_network": anchor["broad_network"],
                    "target_broad_network": target["broad_network"],
                    "anchor_sector_mid_degrees": anchor["sector_mid_degrees"],
                    "target_sector_mid_degrees": target["sector_mid_degrees"],
                    "anchor_negative_log10_acat_q": anchor["negative_log10_acat_q"],
                    "target_negative_log10_acat_q": target["negative_log10_acat_q"],
                    "link_rule": "highest_uncapped_evidence_to_each_other_occurrence",
                }
            )
    links = pd.DataFrame(
        rows,
        columns=[
            "schema_version",
            "figure_id",
            "case_id",
            "current_symbol",
            "selected_network_count_within_class",
            "anchor_broad_network",
            "target_broad_network",
            "anchor_sector_mid_degrees",
            "target_sector_mid_degrees",
            "anchor_negative_log10_acat_q",
            "target_negative_log10_acat_q",
            "link_rule",
        ],
    )
    require(len(links) == 2, f"Expected two SEA-AD recurrence links, found {len(links)}")
    require(set(links["case_id"]) == {"mt_driver"}, "Non-MT recurrence link unexpectedly present")
    require(set(links["current_symbol"]) == {"MT-CO2", "MT-CYB"}, "SEA-AD recurrence genes changed")
    return links


def _annular_sector(
    ax: plt.Axes,
    start_degrees: float,
    end_degrees: float,
    inner_radius: float,
    outer_radius: float,
    *,
    facecolor: str,
    edgecolor: str,
    linewidth: float = 0.6,
    linestyle: str | tuple[Any, ...] = "solid",
    hatch: str = "",
    zorder: float = 2,
) -> mpatches.Wedge:
    wedge = mpatches.Wedge(
        (0, 0),
        outer_radius,
        end_degrees,
        start_degrees,
        width=outer_radius - inner_radius,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        hatch=hatch or None,
        joinstyle="miter",
        zorder=zorder,
    )
    ax.add_patch(wedge)
    return wedge


def _circle(ax: plt.Axes, radius: float, *, color: str, linewidth: float, linestyle: Any = "solid") -> None:
    ax.add_patch(
        mpatches.Circle(
            (0, 0),
            radius,
            fill=False,
            edgecolor=color,
            linewidth=linewidth,
            linestyle=linestyle,
            zorder=1.5,
        )
    )


def _upright_rotation(angle: float) -> float:
    rotation = (angle - 90.0) % 360.0
    if 90.0 < rotation < 270.0:
        rotation += 180.0
    if rotation > 180.0:
        rotation -= 360.0
    return rotation


def _polar_xy(radius: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return radius * math.cos(radians), radius * math.sin(radians)


def _draw_link(ax: plt.Axes, angle1: float, angle2: float) -> None:
    start = _polar_xy(0.61, angle1)
    end = _polar_xy(0.61, angle2)
    path = MplPath(
        [start, (0.0, 0.0), end],
        [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3],
    )
    ax.add_patch(
        mpatches.PathPatch(
            path,
            facecolor="none",
            edgecolor=LINK,
            linewidth=0.8,
            alpha=0.28,
            zorder=2.2,
        )
    )


def _draw_legend(fig: plt.Figure, case_id: str) -> None:
    ax = fig.add_axes([0.62, 0.09, 0.36, 0.79])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    key_x = 0.04
    text_x = 0.20
    ax.text(key_x, 0.95, "Legend", fontsize=12.0, fontweight="bold", color=TEXT, ha="left", va="center")
    ax.add_patch(mpatches.Rectangle((key_x, 0.84), 0.11, 0.045, facecolor=NETWORK_COLORS["Astrocytes"], edgecolor="none"))
    ax.text(text_x, 0.862, "Broad-network band", fontsize=9.0, color=TEXT, ha="left", va="center")
    ax.add_patch(mpatches.Rectangle((key_x, 0.75), 0.11, 0.045, facecolor=NAVY, edgecolor="none"))
    ax.text(text_x, 0.772, "Capped −log10(ACAT q)", fontsize=9.0, color=TEXT, ha="left", va="center")
    ax.plot([key_x, key_x + 0.11], [0.68, 0.68], color=LINK, lw=1.1, alpha=0.55)
    ax.text(text_x, 0.68, "Same gene across networks", fontsize=9.0, color=TEXT, ha="left", va="center")
    if case_id == "mt_driver":
        ax.scatter([key_x + 0.055], [0.59], s=19, marker="o", color="#666666", zorder=3)
        marker_text = "mtDNA-encoded gene"
    else:
        ax.scatter([key_x + 0.055], [0.59], s=37, marker="D", facecolors="none", edgecolors="#555555", linewidths=1.0, zorder=3)
        marker_text = "Extended mitochondrial reference"
    ax.text(text_x, 0.59, marker_text, fontsize=9.0, color=TEXT, ha="left", va="center")

    ax.text(key_x, 0.49, "Empty-list states", fontsize=9.3, fontweight="bold", color=TEXT, ha="left", va="center")
    ax.add_patch(mpatches.Rectangle((key_x, 0.405), 0.11, 0.045, facecolor=NO_PASS_TRACK, edgecolor=NO_PASS_EDGE, linewidth=0.8))
    ax.text(text_x, 0.427, "Testable; no passing candidate", fontsize=8.6, color=TEXT, ha="left", va="center")
    ax.add_patch(
        mpatches.Rectangle(
            (key_x, 0.315),
            0.11,
            0.045,
            facecolor=NOT_TESTABLE_TRACK,
            edgecolor=NOT_TESTABLE_EDGE,
            linewidth=0.8,
            linestyle=(0, (3, 2)),
            hatch="xx",
        )
    )
    ax.text(text_x, 0.337, "No included KDA run", fontsize=8.6, color=TEXT, ha="left", va="center")
    ax.add_patch(mpatches.Rectangle((key_x, 0.225), 0.11, 0.045, facecolor=UNUSED_TRACK, edgecolor="#FFFFFF", linewidth=0.8))
    ax.text(text_x, 0.247, "Unused rank; no backfill", fontsize=8.6, color=TEXT, ha="left", va="center")

    ax.text(key_x, 0.13, "Common evidence scale: 0–15", fontsize=8.9, color=MID, ha="left", va="center")
    ax.text(key_x, 0.065, "Curves show recurrence, not network edges", fontsize=8.0, color=MID, ha="left", va="center")


def _draw_circle_figure(
    plot_data: pd.DataFrame, links: pd.DataFrame, case_id: str
) -> tuple[plt.Figure, dict[str, Any]]:
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    ax = fig.add_axes([0.005, 0.055, 0.595, 0.835])
    ax.set_xlim(-1.68, 1.68)
    ax.set_ylim(-1.68, 1.68)
    ax.set_aspect("equal")
    ax.axis("off")
    class_slots = plot_data.loc[plot_data["case_id"].eq(case_id)].sort_values(
        ["network_display_order", "slot_rank"]
    )
    class_links = links.loc[links["case_id"].eq(case_id)]

    score_inner = 0.62
    score_height = 0.32
    for row in class_slots.itertuples(index=False):
        _annular_sector(
            ax,
            row.sector_start_degrees,
            row.sector_end_degrees,
            score_inner,
            score_inner + score_height,
            facecolor=row.slot_facecolor,
            edgecolor=row.slot_edgecolor,
            linewidth=0.62 if row.slot_status.startswith("not_testable") else 0.55,
            linestyle=(0, (3, 2)) if row.slot_status.startswith("not_testable") else "solid",
            hatch=row.slot_hatch,
            zorder=2,
        )
    for value in (5.0, 10.0, EVIDENCE_CAP):
        fraction = min(value / EVIDENCE_CAP, 1.0)
        _circle(
            ax,
            score_inner + score_height * fraction,
            color="#AEB6BF" if fraction == 1 else REFERENCE,
            linewidth=0.62 if fraction == 1 else 0.42,
            linestyle="solid" if fraction == 1 else (0, (2, 4)),
        )

    for row in class_links.itertuples(index=False):
        _draw_link(ax, row.anchor_sector_mid_degrees, row.target_sector_mid_degrees)

    occupied = class_slots.loc[class_slots["slot_status"].eq("ranked_candidate")]
    for row in occupied.itertuples(index=False):
        _annular_sector(
            ax,
            row.sector_start_degrees,
            row.sector_end_degrees,
            score_inner,
            score_inner + score_height * row.display_score,
            facecolor=NAVY,
            edgecolor=WHITE,
            linewidth=0.55,
            zorder=3,
        )

    for row in class_slots.itertuples(index=False):
        edge = "#8E7D00" if row.broad_network == "Oligodendrocytes" else WHITE
        _annular_sector(
            ax,
            row.sector_start_degrees,
            row.sector_end_degrees,
            0.98,
            1.07,
            facecolor=row.network_color,
            edgecolor=edge,
            linewidth=0.72 if edge == WHITE else 0.62,
            zorder=4,
        )

    label_radii = {1: 1.12, 2: 1.23, 3: 1.34, 4: 1.23, 5: 1.12}
    for row in occupied.itertuples(index=False):
        angle = row.sector_mid_degrees
        x, y = _polar_xy(label_radii[row.slot_rank], angle)
        ax.text(
            x,
            y,
            row.current_symbol,
            fontsize=7.4,
            color="#666666" if row.is_mtdna_gene else TEXT,
            ha="center",
            va="center",
            rotation=_upright_rotation(angle),
            rotation_mode="anchor",
            zorder=6,
        )
        marker_x, marker_y = _polar_xy(1.092, angle)
        if case_id == "mt_driver" and row.is_mtdna_gene:
            ax.scatter([marker_x], [marker_y], s=8, marker="o", color="#666666", zorder=6)
        if case_id == "non_mt_driver" and row.extended_reference_member:
            ax.scatter(
                [marker_x],
                [marker_y],
                s=18,
                marker="D",
                facecolors="none",
                edgecolors="#555555",
                linewidths=0.8,
                zorder=6,
            )

    for network in NETWORK_ORDER:
        group = class_slots.loc[class_slots["broad_network"].eq(network)].sort_values("slot_rank")
        block_mid = (
            float(group.iloc[0]["sector_start_degrees"])
            + float(group.iloc[-1]["sector_end_degrees"])
        ) / 2.0
        x, y = _polar_xy(1.51, block_mid)
        ax.text(
            x,
            y,
            NETWORK_LABELS[network],
            fontsize=9.4,
            fontweight="bold",
            color=TEXT,
            ha="center",
            va="center",
            rotation=_upright_rotation(block_mid),
            rotation_mode="anchor",
            zorder=6,
        )
        list_state = str(group.iloc[0]["list_status"])
        if list_state in {"no_passing_candidate", "not_testable_no_included_runs"}:
            label = "No passing\ncandidate" if list_state == "no_passing_candidate" else "No included\nKDA run"
            x, y = _polar_xy(1.22, block_mid)
            ax.text(
                x,
                y,
                label,
                fontsize=7.0,
                fontstyle="italic",
                color="#555E68",
                ha="center",
                va="center",
                rotation=_upright_rotation(block_mid),
                rotation_mode="anchor",
                linespacing=0.95,
                zorder=6,
            )

    fig.text(
        0.30,
        0.955,
        f"SEA-AD • {CLASS_LABELS[case_id]}",
        fontsize=13.0,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
    )
    fig.text(
        0.30,
        0.915,
        "Up to five passing candidates per network, ranked by aggregate ACAT q",
        fontsize=8.2,
        color=MID,
        ha="center",
        va="center",
    )
    fig.text(
        0.30,
        0.028,
        "Center links mark repeated selected genes across networks; they are not network edges",
        fontsize=7.2,
        color=MID,
        ha="center",
        va="center",
    )
    _draw_legend(fig, case_id)

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
    require(minimum_font >= 7.0, f"Minimum visible font is too small: {minimum_font}")
    return fig, {"minimum_font_points": minimum_font, "canvas_clipped_text": clipped}


def _render_class_images(
    plot_data: pd.DataFrame,
    links: pd.DataFrame,
    case_id: str,
    staging: Path,
    dpi: int,
) -> tuple[list[Path], dict[str, Any]]:
    fig, render_meta = _draw_circle_figure(plot_data, links, case_id)
    basename = CLASS_BASENAMES[case_id]
    paths: list[Path] = []
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{basename}.{extension}"
        temporary = staging / f".{basename}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Title": f"SEA-AD {CLASS_LABELS[case_id]} circular figure",
                "Creator": "SEA-AD two-case circular renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {
                "Title": f"SEA-AD {CLASS_LABELS[case_id]} circular figure",
                "Creator": "SEA-AD two-case circular renderer",
                "Date": None,
            }
        else:
            metadata = {"Software": "SEA-AD two-case circular renderer"}
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
    return paths, render_meta


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


def _image_checks(image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    lookup = {path.name: path for path in image_paths}
    expected_names = set(OUTPUT_FILES[:6])
    checks.append(
        check_record(
            "image_file_set",
            set(lookup) == expected_names,
            "|".join(sorted(lookup)),
            "|".join(sorted(expected_names)),
            "Both driver classes have PNG, PDF, and SVG exports.",
        )
    )
    checks.append(
        check_record(
            "image_files_nonempty",
            all(path.stat().st_size > 1_000 for path in image_paths),
            "|".join(str(path.stat().st_size) for path in image_paths),
            ">1000 bytes each",
            "Rendered files are nontrivial.",
        )
    )
    for case_id in CLASS_ORDER:
        basename = CLASS_BASENAMES[case_id]
        svg_path = lookup[f"{basename}.svg"]
        pdf_path = lookup[f"{basename}.pdf"]
        png_path = lookup[f"{basename}.png"]
        svg_text = svg_path.read_text(encoding="utf-8")
        lower = svg_text.lower()
        checks.extend(
            [
                check_record(f"{case_id}_svg_signature", "<svg" in lower, "present" if "<svg" in lower else "missing", "present", "SVG signature is present."),
                check_record(f"{case_id}_svg_searchable_text", "<text" in lower, "present" if "<text" in lower else "missing", "present", "SVG preserves searchable text."),
                check_record(f"{case_id}_svg_vector_shapes", "<path" in lower, "present" if "<path" in lower else "missing", "present", "SVG preserves vector paths."),
            ]
        )
        with pdf_path.open("rb") as handle:
            header = handle.read(5)
        checks.append(check_record(f"{case_id}_pdf_signature", header == b"%PDF-", header.decode("latin1"), "%PDF-", "PDF signature is valid."))
        with Image.open(png_path) as image:
            width, height = image.size
            embedded_dpi = image.info.get("dpi", (math.nan, math.nan))
            mode = image.mode
        checks.extend(
            [
                check_record(f"{case_id}_png_width", width == PNG_WIDTH, width, PNG_WIDTH, "PNG width is frozen."),
                check_record(f"{case_id}_png_height", height == PNG_HEIGHT, height, PNG_HEIGHT, "PNG height is frozen."),
                check_record(
                    f"{case_id}_png_resolution",
                    all(math.isfinite(value) and abs(value - dpi) <= 1 for value in embedded_dpi),
                    f"{embedded_dpi[0]:.2f}|{embedded_dpi[1]:.2f}",
                    f"{dpi}|{dpi}",
                    "PNG embeds approximately 450 DPI.",
                ),
                check_record(f"{case_id}_png_color_mode", mode in {"RGB", "RGBA"}, mode, "RGB or RGBA", "PNG is suitable for slides."),
            ]
        )
    return checks


def build_checks(
    bundle: Mapping[str, Any],
    plot_data: pd.DataFrame,
    links: pd.DataFrame,
    image_paths: Sequence[Path],
    render_meta: Mapping[str, Mapping[str, Any]],
    dpi: int,
    visual_review_status: str,
) -> pd.DataFrame:
    state_counts = plot_data["slot_status"].value_counts().to_dict()
    occupied = plot_data.loc[plot_data["slot_status"].eq("ranked_candidate")]
    checks = [
        check_record("vh10c_validated", True, "validated_complete", "validated_complete", "VH10C completion was validated during input loading."),
        check_record("compact_input_hashes", True, len(bundle["input_digests"]), len(INPUT_PATHS), "All compact inputs and the annotation reference are SHA-256 bound."),
        check_record("rosmap_blinded_freeze", not truth(bundle["freeze"].iloc[0]["rosmap_candidate_files_read"]), bundle["freeze"].iloc[0]["rosmap_candidate_files_read"], False, "SEA-AD selection was frozen without ROSMAP candidates."),
        check_record("network_class_lists", len(bundle["list_status"]) == 14, len(bundle["list_status"]), 14, "Seven networks × two driver classes."),
        check_record("top_list_rows", len(bundle["top5"]) == 22, len(bundle["top5"]), 22, "Thirteen ranked rows and nine sentinels."),
        check_record("ranked_units", len(occupied) == 13, len(occupied), 13, "All frozen SEA-AD selected units are displayed."),
        check_record("ranked_class_units", occupied.groupby("case_id").size().to_dict() == {"mt_driver": 8, "non_mt_driver": 5}, str(occupied.groupby("case_id").size().to_dict()), "mt_driver:8|non_mt_driver:5", "Frozen class partition."),
        check_record("ranked_unique_symbols", occupied["current_symbol"].nunique() == 11, occupied["current_symbol"].nunique(), 11, "Unique displayed symbols."),
        check_record("fixed_plot_rows", len(plot_data) == 70, len(plot_data), 70, "Two classes × seven networks × five slots."),
        check_record("ranked_slot_count", state_counts.get("ranked_candidate") == 13, state_counts.get("ranked_candidate"), 13, "Ranked circular slots."),
        check_record("unused_slot_count", state_counts.get("unused_display_slot") == 12, state_counts.get("unused_display_slot"), 12, "Unused ranks after short passing lists."),
        check_record("no_passing_slot_count", state_counts.get("no_passing_candidate_slot") == 25, state_counts.get("no_passing_candidate_slot"), 25, "Testable empty lists."),
        check_record("not_testable_slot_count", state_counts.get("not_testable_no_included_runs_slot") == 20, state_counts.get("not_testable_no_included_runs_slot"), 20, "Unavailable network/class lists."),
        check_record("included_runs", sum(bundle["active_runs_by_network"].values()) == 42, sum(bundle["active_runs_by_network"].values()), 42, "Included SEA-AD KDA runs."),
        check_record("recurrence_links", len(links) == 2, len(links), 2, "MT-CO2 and MT-CYB recurrence links."),
        check_record("non_mt_recurrence_links", int((links["case_id"] == "non_mt_driver").sum()) == 0, int((links["case_id"] == "non_mt_driver").sum()), 0, "The five non-MT symbols are unique."),
        check_record("mt_core_and_mtdna", occupied.loc[occupied["case_id"].eq("mt_driver"), ["is_core_mito", "is_mtdna_gene"]].map(truth).all().all(), "all true", "all true", "All displayed MT units are core MitoCarta and mtDNA encoded."),
        check_record("non_mt_outside_core", (~occupied.loc[occupied["case_id"].eq("non_mt_driver"), "is_core_mito"].map(truth)).all(), "all false", "all false", "All displayed non-MT units are outside core MitoCarta."),
        check_record("extended_non_mt_marker", set(occupied.loc[occupied["case_id"].eq("non_mt_driver") & occupied["extended_reference_member"].map(truth), "current_symbol"]) == {"RPS27A"}, "|".join(sorted(set(occupied.loc[occupied["case_id"].eq("non_mt_driver") & occupied["extended_reference_member"].map(truth), "current_symbol"]))), "RPS27A", "Only RPS27A carries the non-MT extended-reference diamond."),
        check_record("evidence_cap", EVIDENCE_CAP == 15, EVIDENCE_CAP, 15, "Both figures share the Phase 18 display cap."),
        check_record("single_capped_unit", int((occupied["negative_log10_acat_q"] > EVIDENCE_CAP).sum()) == 1, int((occupied["negative_log10_acat_q"] > EVIDENCE_CAP).sum()), 1, "Only excitatory MT-CO2 is capped."),
        check_record("no_candidate_summary_read", "seaad_candidate_summary.tsv.gz" not in bundle["input_digests"], "not read", "not read", "The missing full candidate table is outside the compact display contract."),
        check_record("no_overlap_inputs", not any("09_rosmap_kda_candidates" in path or "10d_overlap" in path for path in bundle["input_digests"]), "none", "none", "No ROSMAP candidate or overlap result enters the figures."),
        check_record("empty_state_redundancy", set(plot_data.loc[plot_data["slot_status"].str.contains("no_passing|not_testable"), ["slot_facecolor", "slot_edgecolor", "slot_linestyle", "slot_hatch"]].drop_duplicates()["slot_linestyle"]) == {"solid", "dashed"}, "solid|dashed + distinct fill/hatch + labels", "solid|dashed + distinct fill/hatch + labels", "No-passing and unavailable states differ by more than color."),
        check_record("minimum_font_size", min(meta["minimum_font_points"] for meta in render_meta.values()) >= 7.0, f"{min(meta['minimum_font_points'] for meta in render_meta.values()):.2f}", ">=7.0 pt", "Minimum visible text size."),
        check_record("canvas_text_clipping", sum(len(meta["canvas_clipped_text"]) for meta in render_meta.values()) == 0, sum(len(meta["canvas_clipped_text"]) for meta in render_meta.values()), 0, "No text leaves either canvas."),
    ]
    checks.extend(_image_checks(image_paths, dpi))
    if visual_review_status == "complete":
        checks.append(check_record("visual_review", True, "complete", "complete", "Reviewed at intended slide size in color and grayscale.", severity="nonblocking"))
    else:
        checks.append(check_record("visual_review", False, "pending", "complete", "Manual slide-size color/grayscale review remains pending.", severity="nonblocking", status_override="pending"))
    frame = pd.DataFrame(checks)
    blocking = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking.empty, "Blocking figure checks failed: " + ", ".join(blocking["check_id"]))
    return frame


def documentation(bundle: Mapping[str, Any]) -> tuple[str, str]:
    caption = """# SEA-AD two-class circular figures: caption

**SEA-AD MT and non-MT key-driver candidates across broad brain-cell networks.** Each circle shows one independently frozen SEA-AD driver class. Within each broad network, up to five genes passing the 80% coverage, conservative-support, and aggregate ACAT q ≤ 0.05 gates are displayed in rank order. Navy bar height is −log10(aggregate ACAT q) on a common scale capped at 15. Outer colors denote broad networks. Center curves connect repeated displayed genes across networks and are not network edges. Dots mark mtDNA-encoded MT genes; diamonds mark non-MT genes in the extended mitochondrial reference. Solid gray slots mark testable lists with no passing candidate, whereas dashed/crossed slots mark networks with no included KDA run. Failing genes were not used as backfills.
"""
    methods = f"""# SEA-AD two-class circular figures: methods

The renderer reads the compact validated VH10C selection contract: `status.tsv`, `seaad_top5.tsv`, `seaad_list_status.tsv`, `selection_checks.tsv`, `seaad_selection_freeze.tsv`, and their artifact registry. It verifies the registered SHA-256 values, `validated_complete` status, zero failed selection checks, `rosmap_candidate_files_read = False`, the frozen query/result tier, all candidate gates and stored ranks, and the 14-list testability grid against the 1,548-row SEA-AD KDA run manifest. The registered full `seaad_candidate_summary.tsv.gz` is not present and is not read; the renderer displays the already-frozen top lists and does not claim to rerank all 38,788 candidate units.

Candidate annotations are joined from the checksum-frozen Phase 18 annotation authority only to encode core-MitoCarta class, mtDNA dots, and extended-reference diamonds. No VH09 ROSMAP candidate table or VH10D overlap result is read. The selected set contains {bundle['selected_mt_units']} MT and {bundle['selected_non_mt_units']} non-MT network–gene units ({bundle['selected_symbols']} unique symbols). MT-CO2 and MT-CYB recur across excitatory and inhibitory networks; recurrence curves connect the highest-uncapped-evidence occurrence to the other occurrence and are not Bayesian-network edges.

Both figures use the Phase 18 seven-network order, colorblind-aware palette, 35 fixed slots, clockwise geometry, 6° network gaps, 1° slot gaps, and common evidence cap of 15. Testable/no-passing lists use a solid medium-light gray track and direct label. Lists with no included KDA run use a darker dashed, cross-hatched track and direct label. Thus unavailable evidence is not represented as a negative biological result. SVG and PDF are vector exports; SVG preserves searchable text. PNG review copies are 5400 × 3240 at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_two_case_circular.py \\
  --output-root results/figures/validation_human/seaad_two_case_circular \\
  --visual-review-status pending
```
"""
    return caption, methods


def table_row_count(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA"
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0)


def build_artifacts(
    bundle: Mapping[str, Any], staging: Path, renderer_path: Path
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for relative, digest in sorted(bundle["input_digests"].items()):
        path = bundle["project_root"] / relative
        rows.append(
            {
                "schema_version": SCHEMA,
                "figure_id": FIGURE_ID,
                "artifact_role": "input",
                "logical_name": relative,
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "rows": table_row_count(path),
                "validation_state": "validated_compact_input",
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
    require(set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(PAYLOAD_FILES), "Output artifact scope changed")
    require(not frame["path"].isin(OUTPUT_FILES[-2:]).any(), "Artifact manifest or status entered its own hash scope")
    return frame


def validate_output(
    project_root: Path,
    output_root: Path,
    *,
    expected_visual_status: str | None = None,
) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(output_root.is_dir(), f"Missing figure output directory: {output_root}")
    observed = sorted(path.name for path in output_root.iterdir() if path.is_file())
    require(observed == sorted(OUTPUT_FILES), f"Figure output contract mismatch: {observed}")

    status = one_row(read_tsv(output_root / f"{FIGURE_ID}_status.tsv"), "figure status")
    require(status["schema_version"] == SCHEMA, "Unexpected figure status schema")
    require(status["figure_id"] == FIGURE_ID, "Unexpected figure ID")
    visual_status = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual_status == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual_status == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Unexpected validation status")

    checks = read_tsv(output_root / f"{FIGURE_ID}_checks.tsv")
    require_columns(checks, ["check_id", "severity", "status"], "figure checks")
    blocking = checks.loc[checks["severity"].eq("blocking") & ~checks["status"].eq("pass")]
    require(blocking.empty, "Published package contains blocking check failures")
    if visual_status == "complete":
        require(checks["status"].eq("pass").all(), "Completed package contains a pending or failed check")

    artifacts_path = output_root / f"{FIGURE_ID}_artifacts.tsv"
    require(sha256_file(artifacts_path) == status["artifact_manifest_sha256"], "Artifact-manifest SHA disagrees with status")
    artifacts = read_tsv(artifacts_path)
    require_columns(artifacts, ["artifact_role", "path", "bytes", "sha256"], "artifact manifest")
    require(artifacts["path"].is_unique, "Artifact manifest paths are duplicated")
    output_rows = artifacts.loc[artifacts["artifact_role"].eq("output")]
    require(set(output_rows["path"]) == set(PAYLOAD_FILES), "Artifact output scope changed")
    require(not artifacts["path"].isin(OUTPUT_FILES[-2:]).any(), "Manifest/status is self-hashed")
    require(len(artifacts.loc[artifacts["artifact_role"].eq("script")]) == 1, "Expected one renderer artifact")
    for row in artifacts.itertuples(index=False):
        path = output_root / str(row.path) if row.artifact_role == "output" else project_root / str(row.path)
        require(path.is_file(), f"Artifact path is missing: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact SHA-256 changed: {row.path}")

    plot_data = read_tsv(output_root / f"{FIGURE_ID}_plot_data.tsv")
    require(len(plot_data) == 70, "Published plot table does not contain 70 slots")
    require(plot_data["slot_status"].value_counts().to_dict() == {
        "ranked_candidate": 13,
        "unused_display_slot": 12,
        "no_passing_candidate_slot": 25,
        "not_testable_no_included_runs_slot": 20,
    }, "Published slot-state partition changed")
    links = read_tsv(output_root / f"{FIGURE_ID}_links.tsv")
    require(len(links) == 2 and set(links["current_symbol"]) == {"MT-CO2", "MT-CYB"}, "Published recurrence table changed")
    image_paths = [output_root / name for name in OUTPUT_FILES[:6]]
    image_checks = _image_checks(image_paths, as_int(status["png_dpi"]))
    require(all(row["status"] == "pass" for row in image_checks), "Published image validation failed")
    print(f"SEA-AD two-case circular figure validation passed: {output_root}")


def publish(
    project_root: Path,
    output_root: Path,
    *,
    dpi: int,
    visual_review_status: str,
    force: bool,
) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    require(project_root.is_dir(), f"Missing project root: {project_root}")
    if output_root.exists() and not force:
        raise FileExistsError(f"Output exists; use --force for recoverable replacement: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{FIGURE_ID}.staging.", dir=output_root.parent))
    try:
        bundle = load_bundle(project_root)
        plot_data = build_plot_data(bundle)
        links = build_links(plot_data)
        image_paths: list[Path] = []
        render_meta: dict[str, Mapping[str, Any]] = {}
        for case_id in CLASS_ORDER:
            paths, meta = _render_class_images(plot_data, links, case_id, staging, dpi)
            image_paths.extend(paths)
            render_meta[case_id] = meta
        write_tsv(plot_data, staging / f"{FIGURE_ID}_plot_data.tsv")
        write_tsv(links, staging / f"{FIGURE_ID}_links.tsv")
        caption, methods = documentation(bundle)
        write_text(staging / f"{FIGURE_ID}_caption.md", caption)
        write_text(staging / f"{FIGURE_ID}_methods.md", methods)
        checks = build_checks(
            bundle,
            plot_data,
            links,
            image_paths,
            render_meta,
            dpi,
            visual_review_status,
        )
        write_tsv(checks, staging / f"{FIGURE_ID}_checks.tsv")

        renderer_path = Path(__file__).resolve()
        artifacts = build_artifacts(bundle, staging, renderer_path)
        artifacts_path = staging / f"{FIGURE_ID}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        validation_status = (
            "validated_complete"
            if visual_review_status == "complete" and pending == 0
            else "awaiting_visual_review"
        )
        status = pd.DataFrame(
            [
                {
                    "schema_version": SCHEMA,
                    "figure_id": FIGURE_ID,
                    "validation_status": validation_status,
                    "visual_review_status": visual_review_status,
                    "failed_blocking_checks": int((checks["severity"].eq("blocking") & ~checks["status"].eq("pass")).sum()),
                    "pending_nonblocking_checks": int((checks["severity"].eq("nonblocking") & ~checks["status"].eq("pass")).sum()),
                    "input_bundle_sha256": bundle["input_bundle_sha256"],
                    "renderer_sha256": sha256_file(renderer_path),
                    "artifact_manifest_sha256": sha256_file(artifacts_path),
                    "figure_width_inches": f"{FIGURE_WIDTH_IN:.1f}",
                    "figure_height_inches": f"{FIGURE_HEIGHT_IN:.1f}",
                    "png_dpi": dpi,
                    "png_width": PNG_WIDTH,
                    "png_height": PNG_HEIGHT,
                    "input_files": len(bundle["input_digests"]),
                    "output_files": len(OUTPUT_FILES),
                    "plot_data_rows": len(plot_data),
                    "link_rows": len(links),
                    "checks": len(checks),
                    "selected_units": bundle["selected_units"],
                    "mt_units": bundle["selected_mt_units"],
                    "non_mt_units": bundle["selected_non_mt_units"],
                    "selected_mt_units": bundle["selected_mt_units"],
                    "selected_non_mt_units": bundle["selected_non_mt_units"],
                    "selected_unique_symbols": bundle["selected_symbols"],
                    "candidate_summary_read": False,
                    "rosmap_candidate_files_read": False,
                    "contract_scope": "compact_frozen_display_only",
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        write_tsv(status, staging / f"{FIGURE_ID}_status.tsv")
        validate_output(
            project_root,
            staging,
            expected_visual_status=visual_review_status,
        )

        if output_root.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            backup = output_root.parent / f".{output_root.name}.backup.{timestamp}.{os.getpid()}"
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
