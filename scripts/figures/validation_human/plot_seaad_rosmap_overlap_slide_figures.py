#!/usr/bin/env python3
"""Render validated slide-scale ROSMAP/SEA-AD overlap figures.

This renderer publishes two independent, atomic figure packages:

* ``seaad_rosmap_strict_overlap_ranks``: the primary, network-aware overlap
  scorecard and paired MT selection ranks; and
* ``seaad_rosmap_top_driver_gene_overlap_slide``: the secondary,
  network-collapsed gene-level Euler/Venn view.

The script only reads compact, validated VH09/VH10C/VH10D artifacts.  It does
not read VH05/VH06, rerun selection, or alter the existing detailed Venn
package.
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


MPL_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_overlap_slides_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
FONT_CACHE = Path(tempfile.gettempdir()) / "seaad_rosmap_overlap_slides_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "seaad_rosmap_overlap_slide_figures_v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "hatch.linewidth": 1.0,
    }
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402
import pandas as pd  # noqa: E402


SCHEMA = "seaad_rosmap_overlap_slide_figure_v1"
STRICT_ID = "seaad_rosmap_strict_overlap_ranks"
GENE_ID = "seaad_rosmap_top_driver_gene_overlap_slide"
FIGURE_IDS = (STRICT_ID, GENE_ID)
FIGURE_WIDTH_IN = 12.0
FIGURE_HEIGHT_IN = 5.3
DEFAULT_PNG_DPI = 450
PNG_WIDTH = 5_400
PNG_HEIGHT = 2_385
QUERY_RULE = "phase18_parity_query"
RESULT_TIER = "phase18_parity_query__min3_all"
CLASS_ORDER = ("mt_driver", "non_mt_driver")

# Deck-wide, colorblind-safe cohort encoding.  Every meaning also has a
# redundant outline, hatch, line style, symbol, or direct label.
ROSMAP = "#E69F00"
ROSMAP_PALE = "#F9E5B8"
SEAAD = "#009E73"
SEAAD_PALE = "#BFE8DC"
SHARED = "#0F233D"
UNMATCHED = "#A9A9A9"
UNMATCHED_TEXT = "#666666"
TEXT = "#20252B"
MID = "#5E6670"
PANEL_BG = "#F6F7F8"
WHITE = "#FFFFFF"

INPUT_PATHS = {
    "vh09_status": "results/validation_human/09_rosmap_kda_candidates/status.tsv",
    "vh09_artifacts": "results/validation_human/09_rosmap_kda_candidates/artifacts.tsv",
    "vh09_checks": "results/validation_human/09_rosmap_kda_candidates/candidate_freeze_checks.tsv",
    "rosmap_selected": "results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv",
    "vh10c_status": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/status.tsv",
    "vh10c_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/artifacts.tsv",
    "vh10c_checks": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/selection_checks.tsv",
    "seaad_top5": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv",
    "seaad_freeze": "results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_selection_freeze.tsv",
    "vh10d_status": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/status.tsv",
    "vh10d_artifacts": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/artifacts.tsv",
    "vh10d_checks": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/overlap_checks.tsv",
    "unit_overlap": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv",
    "overlap_summary": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_overlap_summary.tsv",
    "gene_overlap": "results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_gene_only_overlap.tsv",
}

EXPECTED_INPUT_SHA256 = {
    "vh09_status": "e5504ef3edb8264064d40b8307ded3f2277e9230e39f1029162aba4b11f52568",
    "vh09_artifacts": "9cb622cb3d1affc93eac21d598d51ada31b5f74a2355f477cce78c6cbe6f6ced",
    "vh09_checks": "74cacf128d42e62d63780a1e7f2658fec4dee0b701d5c8009c59e6df6614b8a8",
    "rosmap_selected": "e758720f7dcd80d1d6ef72fc7f95bfa20e3784931114e59c716a0e85b681d443",
    "vh10c_status": "c12e21e961c670d69b04789b149fece950c036c68187c75588e19838f91a7023",
    "vh10c_artifacts": "2fe7d1af68e3e4971e19516706d496118719d3422cf198ef010e1000b83b52c1",
    "vh10c_checks": "eda96be41bc9af33257ba447ed623c29e0ffcf521ce1fd77df6b5cd0fff5ae97",
    "seaad_top5": "18b4cdd6cbadbf4ef741cdf54cf2dd992017035786726d701a5d818acc3937ac",
    "seaad_freeze": "33bef167577c0abd8b0ee26861f33ee8f3a26ed22537f449d35cc3d884e52168",
    "vh10d_status": "fd9370f145948f10358e90830e18b25fbf36b3c253c5b2ac22528cb7f74f9528",
    "vh10d_artifacts": "b349a71f5a5735188397a535c054f81af5c024278a6b21ee9c86b8491b2c2a57",
    "vh10d_checks": "a437d7122e0b83173aa49684127a00bd07da2a9b4df2bc1d0366fe478b3526d1",
    "unit_overlap": "68b839ef1dae967bc482d16667d94fe8fd2a8bb17290ea43b2a96767c4abbfa6",
    "overlap_summary": "bde46e5821e0639f29c46f8aa480fb50d7b355fc02a93e128ded862af9ad1ade",
    "gene_overlap": "8b71aef2aa561ef33e1ad679a96dc2fc48c674a76a89c09a4ac3cfb735341e16",
}

EXPECTED_STRICT = {
    "Excitatory_neurons": {
        "MT-CO2": (1, 1),
        "MT-CYB": (5, 2),
        "UQCR10": (2, None),
        "COX4I1": (3, None),
        "COX6B1": (4, None),
        "MT-ND4": (None, 3),
        "MT-ATP6": (None, 4),
    },
    "Inhibitory_neurons": {
        "MT-CO2": (1, 1),
        "MT-CO3": (2, 3),
        "MT-CYB": (3, 4),
        "MT-ND5": (4, 2),
        "COX7C": (5, None),
    },
}

EXPECTED_REGIONS = {
    "mt_driver": {
        "rosmap_only": {"COX4I1", "COX6B1", "COX7C", "UQCR10"},
        "common": {"MT-ATP6", "MT-CO2", "MT-CO3", "MT-CYB", "MT-ND4", "MT-ND5"},
        "seaad_only": set(),
    },
    "non_mt_driver": {
        "rosmap_only": {
            "ANKRD11", "APOE", "ATP6V1F", "DYNLT1", "FTL", "LAMTOR5",
            "LAPTM4A", "NCOA1", "RPL11", "RPL15", "RPL38", "RPLP1",
            "RPS13", "RPS15", "SELENOW",
        },
        "common": set(),
        "seaad_only": {"BEX3", "HGSNAT", "KANSL1L", "RPL30", "RPS27A"},
    },
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--figure", choices=("all", "strict", "gene"), default="all")
    parser.add_argument(
        "--output-base", default="results/figures/validation_human",
        help="Parent directory; each package is written beneath its figure ID.",
    )
    parser.add_argument("--png-dpi", type=int, default=DEFAULT_PNG_DPI)
    parser.add_argument(
        "--visual-review-status", choices=("pending", "complete"), default="pending"
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--validate-output",
        help="Validate one existing package directory; its basename must be a figure ID.",
    )
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
    rounded = int(round(number))
    require(math.isfinite(number) and abs(number - rounded) < 1e-9, f"Expected integer {label}")
    return rounded


def as_rank(value: Any) -> int | None:
    text = str(value).strip()
    return None if text in {"", "NA", "nan"} else as_int(text, "rank")


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


def read_tsv(path: Path) -> pd.DataFrame:
    require(path.is_file(), f"Missing TSV: {path}")
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


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


def validate_source_artifact(manifest: pd.DataFrame, relative: str, digest: str) -> None:
    require_columns(
        manifest, ["path", "digest_algorithm", "digest_scope", "digest_value"],
        "source artifact manifest",
    )
    rows = manifest.loc[manifest["path"].eq(relative)]
    require(len(rows) == 1, f"Input is not uniquely registered: {relative}")
    row = rows.iloc[0]
    require(row["digest_algorithm"] == "sha256", f"Non-SHA256 registration: {relative}")
    require(row["digest_scope"] == "full_file", f"Non-full-file registration: {relative}")
    require(row["digest_value"] == digest, f"Registered digest mismatch: {relative}")


def _memberships(frame: pd.DataFrame, gene_column: str) -> dict[tuple[str, str], str]:
    answer: dict[tuple[str, str], str] = {}
    for (case_id, gene), group in frame.groupby(["case_id", gene_column], sort=True):
        answer[(case_id, gene)] = "|".join(sorted(set(group["broad_network"])))
    return answer


def load_bundle(project_root: Path) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    frames: dict[str, pd.DataFrame] = {}
    digests: dict[str, str] = {}
    for key, relative in INPUT_PATHS.items():
        path = project_root / relative
        digest = sha256_file(path)
        require(digest == EXPECTED_INPUT_SHA256[key], f"Frozen SHA-256 changed for {relative}")
        frames[key] = read_tsv(path)
        digests[relative] = digest

    for label, status_key in (("VH09", "vh09_status"), ("VH10C", "vh10c_status"), ("VH10D", "vh10d_status")):
        row = one_row(frames[status_key], f"{label} status")
        require(row["validation_status"] == "validated_complete", f"{label} is not validated_complete")
        require(str(row.get("failed_checks", "")).strip() == "", f"{label} reports failed checks")
    for checks_key in ("vh09_checks", "vh10c_checks", "vh10d_checks"):
        require_columns(frames[checks_key], ["passed"], checks_key)
        require(frames[checks_key]["passed"].map(truth).all(), f"Failed upstream check in {checks_key}")

    registrations = {
        "vh09_checks": "vh09_artifacts",
        "rosmap_selected": "vh09_artifacts",
        "vh10c_checks": "vh10c_artifacts",
        "seaad_top5": "vh10c_artifacts",
        "seaad_freeze": "vh10c_artifacts",
        "vh10d_checks": "vh10d_artifacts",
        "unit_overlap": "vh10d_artifacts",
        "overlap_summary": "vh10d_artifacts",
        "gene_overlap": "vh10d_artifacts",
    }
    for key, manifest_key in registrations.items():
        validate_source_artifact(frames[manifest_key], INPUT_PATHS[key], digests[INPUT_PATHS[key]])

    vh09 = one_row(frames["vh09_status"], "VH09 status")
    vh10c = one_row(frames["vh10c_status"], "VH10C status")
    vh10d = one_row(frames["vh10d_status"], "VH10D status")
    require(as_int(vh09["selected_units"]) == 47, "ROSMAP selected-unit count changed")
    require(as_int(vh09["selected_unique_genes"]) == 25, "ROSMAP unique-gene count changed")
    require(as_int(vh10c["selected_top5_units"]) == 13, "SEA-AD selected-unit count changed")
    require(as_int(vh10c["selected_unique_genes"]) == 11, "SEA-AD unique-gene count changed")
    require(as_int(vh10d["rosmap_testable_selected_units"]) == 36, "ROSMAP testable count changed")
    require(as_int(vh10d["strict_shared_top5_units"]) == 6, "Strict shared-unit count changed")

    freeze = one_row(frames["seaad_freeze"], "SEA-AD freeze")
    require(not truth(freeze["rosmap_candidate_files_read"]), "SEA-AD freeze was not ROSMAP blind")
    require(freeze["query_rule_id"] == QUERY_RULE, "SEA-AD query rule changed")
    require(freeze["result_tier_id"] == RESULT_TIER, "SEA-AD result tier changed")

    rosmap = frames["rosmap_selected"].copy()
    require_columns(rosmap, ["broad_network", "key_driver", "case_id", "within_case_rank", "top5_display"], "ROSMAP selected units")
    require(rosmap["top5_display"].map(truth).all() and len(rosmap) == 47, "ROSMAP top-display rows changed")
    seaad_all = frames["seaad_top5"].copy()
    require_columns(seaad_all, ["query_rule_id", "result_tier_id", "broad_network", "case_id", "list_status", "display_rank", "current_symbol"], "SEA-AD top list")
    require(set(seaad_all["query_rule_id"]) == {QUERY_RULE}, "SEA-AD query rule changed")
    require(set(seaad_all["result_tier_id"]) == {RESULT_TIER}, "SEA-AD result tier changed")
    seaad = seaad_all.loc[seaad_all["list_status"].eq("ranked_candidates")].copy()
    require(len(seaad) == 13 and ~seaad["current_symbol"].isin({"", "NA"}).any(), "SEA-AD ranked rows changed")

    unit = frames["unit_overlap"].copy()
    require_columns(unit, ["result_tier_id", "broad_network", "gene", "case_id", "in_common_assessable_universe", "rosmap_top5", "rosmap_rank", "seaad_top5", "seaad_rank", "replication_status"], "unit overlap")
    require(set(unit["result_tier_id"]) == {RESULT_TIER}, "Unit-overlap tier changed")
    require(not unit.duplicated(["broad_network", "gene", "case_id"]).any(), "Unit-overlap keys duplicated")
    summary = frames["overlap_summary"].copy()
    require_columns(summary, ["result_tier_id", "broad_network", "case_id", "rosmap_selected_in_universe", "seaad_selected_in_universe", "shared_selected_units", "jaccard_index", "hypergeometric_overlap_p", "list_status"], "overlap summary")
    require(set(summary["result_tier_id"]) == {RESULT_TIER}, "Overlap-summary tier changed")
    require(not summary.duplicated(["broad_network", "case_id"]).any(), "Overlap-summary keys duplicated")

    rosmap_sets = {case: set(rosmap.loc[rosmap["case_id"].eq(case), "key_driver"]) for case in CLASS_ORDER}
    seaad_sets = {case: set(seaad.loc[seaad["case_id"].eq(case), "current_symbol"]) for case in CLASS_ORDER}
    require({case: len(rosmap_sets[case]) for case in CLASS_ORDER} == {"mt_driver": 10, "non_mt_driver": 15}, "ROSMAP class-gene counts changed")
    require({case: len(seaad_sets[case]) for case in CLASS_ORDER} == {"mt_driver": 6, "non_mt_driver": 5}, "SEA-AD class-gene counts changed")
    regions = {
        case: {
            "rosmap_only": rosmap_sets[case] - seaad_sets[case],
            "common": rosmap_sets[case] & seaad_sets[case],
            "seaad_only": seaad_sets[case] - rosmap_sets[case],
        }
        for case in CLASS_ORDER
    }
    require(regions == EXPECTED_REGIONS, "Frozen gene-level regions changed")

    gene = frames["gene_overlap"]
    require_columns(gene, ["gene", "rosmap_top5_any_network_class", "seaad_top5_any_network_class", "shared_gene"], "gene-only overlap")
    require(set(gene.loc[gene["shared_gene"].map(truth), "gene"]) == regions["mt_driver"]["common"], "Gene-only shared set changed")

    input_bundle_sha256 = sha256_strings(
        f"{path}\t{digest}" for path, digest in sorted(digests.items())
    )
    return {
        "project_root": project_root,
        "frames": frames,
        "input_digests": digests,
        "input_bundle_sha256": input_bundle_sha256,
        "rosmap": rosmap,
        "seaad": seaad,
        "unit": unit,
        "summary": summary,
        "regions": regions,
        "rosmap_memberships": _memberships(rosmap, "key_driver"),
        "seaad_memberships": _memberships(seaad, "current_symbol"),
    }


def build_strict_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    unit = bundle["unit"]
    keep = (
        unit["case_id"].eq("mt_driver")
        & unit["broad_network"].isin(EXPECTED_STRICT)
        & (unit["rosmap_top5"].map(truth) | unit["seaad_top5"].map(truth))
    )
    rows = []
    for row in unit.loc[keep].itertuples(index=False):
        rosmap_rank = as_rank(row.rosmap_rank)
        seaad_rank = as_rank(row.seaad_rank)
        pair_status = (
            "strict_shared" if truth(row.rosmap_top5) and truth(row.seaad_top5)
            else "rosmap_only" if truth(row.rosmap_top5) else "seaad_only"
        )
        rows.append(
            {
                "schema_version": "seaad_rosmap_strict_overlap_ranks_plot_data_v1",
                "figure_id": STRICT_ID,
                "broad_network": row.broad_network,
                "network_label": row.broad_network.replace("_", " "),
                "gene": row.gene,
                "case_id": row.case_id,
                "rosmap_selected": truth(row.rosmap_top5),
                "rosmap_rank": "NA" if rosmap_rank is None else rosmap_rank,
                "seaad_selected": truth(row.seaad_top5),
                "seaad_rank": "NA" if seaad_rank is None else seaad_rank,
                "pair_status": pair_status,
                "replication_status": row.replication_status,
            }
        )
    frame = pd.DataFrame(rows).sort_values(
        ["broad_network", "rosmap_selected", "rosmap_rank", "seaad_rank", "gene"],
        ascending=[True, False, True, True, True],
    ).reset_index(drop=True)
    require(len(frame) == 12, f"Expected 12 paired-rank rows, observed {len(frame)}")
    require(not frame.duplicated(["broad_network", "gene"]).any(), "Paired-rank keys duplicated")
    observed = {
        network: {
            row.gene: (as_rank(row.rosmap_rank), as_rank(row.seaad_rank))
            for row in frame.loc[frame["broad_network"].eq(network)].itertuples(index=False)
        }
        for network in EXPECTED_STRICT
    }
    require(observed == EXPECTED_STRICT, "Frozen paired ranks changed")
    return frame


def build_strict_scorecard(bundle: Mapping[str, Any]) -> pd.DataFrame:
    unit = bundle["unit"]
    rows = []
    for case in CLASS_ORDER:
        subset = unit.loc[unit["case_id"].eq(case)]
        rosmap_testable = int((subset["rosmap_top5"].map(truth) & subset["in_common_assessable_universe"].map(truth)).sum())
        seaad_selected = int(subset["seaad_top5"].map(truth).sum())
        shared = int((subset["rosmap_top5"].map(truth) & subset["seaad_top5"].map(truth)).sum())
        rows.append(
            {
                "schema_version": "seaad_rosmap_strict_overlap_ranks_scorecard_v1",
                "figure_id": STRICT_ID,
                "case_id": case,
                "case_label": "MT driver class" if case == "mt_driver" else "Non-MT driver class",
                "rosmap_testable_selected_units": rosmap_testable,
                "seaad_selected_units": seaad_selected,
                "strict_shared_units": shared,
            }
        )
    frame = pd.DataFrame(rows)
    observed = frame.set_index("case_id")[["rosmap_testable_selected_units", "seaad_selected_units", "strict_shared_units"]].astype(int).apply(tuple, axis=1).to_dict()
    require(observed == {"mt_driver": (19, 8, 6), "non_mt_driver": (17, 5, 0)}, "Strict scorecard changed")
    return frame


def build_strict_facet_summary(bundle: Mapping[str, Any]) -> pd.DataFrame:
    summary = bundle["summary"]
    subset = summary.loc[
        summary["case_id"].eq("mt_driver")
        & summary["broad_network"].isin(EXPECTED_STRICT)
    ].copy()
    require(len(subset) == 2, "Expected two neuronal MT summary rows")
    rows = []
    for row in subset.sort_values("broad_network").itertuples(index=False):
        rows.append(
            {
                "schema_version": "seaad_rosmap_strict_overlap_ranks_facet_summary_v1",
                "figure_id": STRICT_ID,
                "broad_network": row.broad_network,
                "network_label": row.broad_network.replace("_", " "),
                "common_assessable_universe": as_int(row.common_assessable_universe),
                "rosmap_selected_in_universe": as_int(row.rosmap_selected_in_universe),
                "seaad_selected_in_universe": as_int(row.seaad_selected_in_universe),
                "shared_selected_units": as_int(row.shared_selected_units),
                "jaccard_index": float(row.jaccard_index),
                "nominal_hypergeometric_p": float(row.hypergeometric_overlap_p),
            }
        )
    frame = pd.DataFrame(rows)
    by_network = frame.set_index("broad_network")
    require(as_int(by_network.loc["Excitatory_neurons", "shared_selected_units"]) == 2, "Excitatory shared count changed")
    require(math.isclose(float(by_network.loc["Excitatory_neurons", "jaccard_index"]), 2 / 7), "Excitatory Jaccard changed")
    require(math.isclose(float(by_network.loc["Excitatory_neurons", "nominal_hypergeometric_p"]), 0.0002330906712655181), "Excitatory nominal p changed")
    require(as_int(by_network.loc["Inhibitory_neurons", "shared_selected_units"]) == 4, "Inhibitory shared count changed")
    require(math.isclose(float(by_network.loc["Inhibitory_neurons", "jaccard_index"]), 0.8), "Inhibitory Jaccard changed")
    require(math.isclose(float(by_network.loc["Inhibitory_neurons", "nominal_hypergeometric_p"]), 1.2245720731665745e-09), "Inhibitory nominal p changed")
    return frame


def build_gene_plot_data(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows = []
    for case in CLASS_ORDER:
        for region in ("rosmap_only", "common", "seaad_only"):
            for order, gene in enumerate(sorted(bundle["regions"][case][region]), start=1):
                rows.append(
                    {
                        "schema_version": "seaad_rosmap_top_driver_gene_overlap_slide_plot_data_v1",
                        "figure_id": GENE_ID,
                        "case_id": case,
                        "case_label": "MT driver class" if case == "mt_driver" else "Non-MT driver class",
                        "gene": gene,
                        "region": region,
                        "region_order": order,
                        "rosmap_selected": region in {"rosmap_only", "common"},
                        "seaad_selected": region in {"seaad_only", "common"},
                        "rosmap_networks": bundle["rosmap_memberships"].get((case, gene), ""),
                        "seaad_networks": bundle["seaad_memberships"].get((case, gene), ""),
                        "opcs_not_testable_guardrail": case == "non_mt_driver" and gene in {"ANKRD11", "FTL", "NCOA1"},
                        "gene_level_only_common": case == "mt_driver" and gene in {"MT-ATP6", "MT-ND4"},
                    }
                )
    frame = pd.DataFrame(rows)
    require(len(frame) == 30 and not frame.duplicated(["case_id", "gene"]).any(), "Gene-level plot rows changed")
    return frame


def build_gene_region_summary(bundle: Mapping[str, Any]) -> pd.DataFrame:
    rows = []
    geometry = {
        "mt_driver": {"rosmap_center_x": -0.10, "seaad_center_x": 0.20, "rosmap_radius": 1.25, "seaad_radius": 0.93, "geometry": "nested_containment"},
        "non_mt_driver": {"rosmap_center_x": -1.55, "seaad_center_x": 1.75, "rosmap_radius": 1.42, "seaad_radius": 0.82, "geometry": "disjoint"},
    }
    for case in CLASS_ORDER:
        regions = bundle["regions"][case]
        for region in ("rosmap_only", "common", "seaad_only"):
            row = {
                "schema_version": "seaad_rosmap_top_driver_gene_overlap_slide_region_summary_v1",
                "figure_id": GENE_ID,
                "case_id": case,
                "region": region,
                "region_count": len(regions[region]),
                "region_genes": "|".join(sorted(regions[region])),
                "rosmap_unique_genes": len(regions["rosmap_only"] | regions["common"]),
                "seaad_unique_genes": len(regions["seaad_only"] | regions["common"]),
            }
            row.update(geometry[case])
            row["center_distance"] = abs(row["seaad_center_x"] - row["rosmap_center_x"])
            row["geometry_margin"] = (
                row["rosmap_radius"] - row["seaad_radius"] - row["center_distance"]
                if case == "mt_driver"
                else row["center_distance"] - row["rosmap_radius"] - row["seaad_radius"]
            )
            rows.append(row)
    frame = pd.DataFrame(rows)
    require(len(frame) == 6, "Gene-level region-summary row count changed")
    require((frame["geometry_margin"].astype(float) >= 0).all(), "Euler geometry violates set relationship")
    return frame


def _scorecard_cell(ax: Any, x: float, y: float, width: float, height: float, label: str, value: int, color: str, *, hatch: str | None = None) -> None:
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.01,rounding_size=0.025",
        transform=ax.transAxes,
        facecolor=WHITE,
        edgecolor=color,
        linewidth=2.0,
        hatch=hatch,
    )
    ax.add_patch(patch)
    divider = x + 0.78 * width
    ax.plot([divider, divider], [y + 0.04 * height, y + 0.96 * height], transform=ax.transAxes, color=color, linewidth=1.3, alpha=0.65)
    ax.text(x + 0.39 * width, y + height / 2, label, transform=ax.transAxes, ha="center", va="center", fontsize=16, color=MID)
    ax.text(x + 0.89 * width, y + height / 2, str(value), transform=ax.transAxes, ha="center", va="center", fontsize=21, weight="bold", color=color)


def _draw_scorecard(ax: Any, scorecard: pd.DataFrame) -> None:
    ax.axis("off")
    positions = {"mt_driver": 0.53, "non_mt_driver": 0.08}
    for row in scorecard.itertuples(index=False):
        y = positions[row.case_id]
        ax.add_patch(FancyBboxPatch((0.005, y), 0.985, 0.34, boxstyle="round,pad=0.012,rounding_size=0.025", transform=ax.transAxes, facecolor=PANEL_BG, edgecolor="#D9DDE2", linewidth=1.0))
        row_label = "MT" if row.case_id == "mt_driver" else "non-MT"
        ax.text(0.025, y + 0.17, row_label, transform=ax.transAxes, ha="left", va="center", fontsize=18, weight="bold", color=TEXT)
        _scorecard_cell(ax, 0.150, y + 0.035, 0.270, 0.27, "ROSMAP testable", as_int(row.rosmap_testable_selected_units), ROSMAP, hatch="////")
        _scorecard_cell(ax, 0.435, y + 0.035, 0.250, 0.27, "SEA-AD selected", as_int(row.seaad_selected_units), SEAAD)
        _scorecard_cell(
            ax, 0.700, y + 0.035, 0.270, 0.27, "Strict shared",
            as_int(row.strict_shared_units), SHARED,
        )


def _format_p(network: str) -> str:
    return "2.33 × 10⁻⁴" if network == "Excitatory_neurons" else "1.22 × 10⁻⁹"


def _draw_slope_facet(ax: Any, network: str, plot_data: pd.DataFrame, facet_summary: pd.DataFrame) -> None:
    subset = plot_data.loc[plot_data["broad_network"].eq(network)].copy()
    summary = one_row(facet_summary.loc[facet_summary["broad_network"].eq(network)], network)
    ax.set_xlim(-0.43, 1.43)
    ax.set_ylim(7.25, -0.25)
    ax.axis("off")
    ax.text(0.5, 1.025, network.replace("_", " "), transform=ax.transAxes, ha="center", va="bottom", fontsize=20, weight="bold", color=TEXT)
    ax.text(0.16, 0.93, "ROSMAP rank", transform=ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=ROSMAP)
    ax.text(0.84, 0.93, "SEA-AD rank", transform=ax.transAxes, ha="center", va="bottom", fontsize=16, weight="bold", color=SEAAD)
    ax.plot([0, 0], [0.85, 5.15], color=ROSMAP, linewidth=2.2, linestyle=(0, (5, 3)), zorder=0)
    ax.plot([1, 1], [0.85, 5.15], color=SEAAD, linewidth=2.2, zorder=0)

    for row in subset.itertuples(index=False):
        left = as_rank(row.rosmap_rank)
        right = as_rank(row.seaad_rank)
        shared = row.pair_status == "strict_shared"
        if shared:
            ax.plot([0, 1], [left, right], color=SHARED, linewidth=3.2, solid_capstyle="round", zorder=2)
        if left is not None:
            color = SHARED if shared else UNMATCHED
            if shared:
                ax.scatter([0], [left], s=95, facecolor=WHITE, edgecolor=ROSMAP, linewidth=2.3, zorder=4, marker="o")
            else:
                ax.scatter([0], [left], s=95, color=UNMATCHED, linewidth=2.3, zorder=4, marker="x")
            ax.text(-0.055, left, f"{left}  {row.gene}", ha="right", va="center", fontsize=16, weight="bold" if shared else "normal", color=color, zorder=5)
        if right is not None:
            color = SHARED if shared else UNMATCHED_TEXT
            ax.scatter([1], [right], s=95, facecolor=WHITE if shared else UNMATCHED, edgecolor=SEAAD if shared else UNMATCHED, linewidth=2.3, zorder=4, marker="o" if shared else "s")
            ax.text(1.055, right, f"{row.gene}  {right}", ha="left", va="center", fontsize=16, weight="bold" if shared else "normal", color=color, zorder=5)

    ax.text(
        0.5, 6.35,
        f"Shared {as_int(summary['shared_selected_units'])}  •  Jaccard {float(summary['jaccard_index']):.3f}\nnominal p = {_format_p(network)}",
        ha="center", va="center", fontsize=16, linespacing=1.15, color=TEXT,
    )


def draw_strict_figure(bundle: Mapping[str, Any], plot_data: pd.DataFrame, scorecard: pd.DataFrame, facet_summary: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.25, 3.75), left=0.025, right=0.975, bottom=0.105, top=0.985, wspace=0.28, hspace=0.25)
    score_ax = fig.add_subplot(grid[0, :])
    _draw_scorecard(score_ax, scorecard)
    for ax, network in zip((fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])), EXPECTED_STRICT):
        _draw_slope_facet(ax, network, plot_data, facet_summary)
    fig.text(0.5, 0.025, "6 strict units = 4 unique symbols  •  strict unit: network + gene + class  •  selection rank, not effect size", ha="center", va="center", fontsize=16, color=MID)
    return fig, _render_meta(fig, minimum_required=16.0)


def _gene_grid(ax: Any, genes: Sequence[str], xs: Sequence[float], ys: Sequence[float], *, daggers: set[str] | None = None, starred: set[str] | None = None) -> None:
    positions = [(x, y) for y in ys for x in xs]
    require(len(positions) >= len(genes), "Insufficient gene-label positions")
    daggers = daggers or set()
    starred = starred or set()
    for gene, (x, y) in zip(genes, positions):
        label = f"{gene}†" if gene in daggers else f"{gene}*" if gene in starred else gene
        ax.text(x, y, label, ha="center", va="center", fontsize=16, color=TEXT, zorder=8)


def _draw_mt_gene_panel(ax: Any, regions: Mapping[str, set[str]]) -> None:
    rosmap_only = sorted(regions["rosmap_only"])
    ax.add_patch(Circle((-0.10, 0), 1.25, facecolor=ROSMAP_PALE, edgecolor=ROSMAP, linewidth=2.3, hatch="////", zorder=1))
    ax.add_patch(Circle((0.20, 0), 0.93, facecolor=SEAAD_PALE, edgecolor=SEAAD, linewidth=2.6, zorder=2))
    ax.text(-0.82, 1.36, "ROSMAP • 10", ha="center", va="center", fontsize=17, weight="bold", color=ROSMAP)
    ax.text(0.64, 0.99, "SEA-AD • 6", ha="center", va="center", fontsize=17, weight="bold", color=SEAAD)
    ax.text(0.20, 0.54, "Common • 6", ha="center", va="center", fontsize=17, weight="bold", color=SHARED)
    _gene_grid(ax, sorted(regions["common"]), (0.20,), (0.26, 0.06, -0.14, -0.34, -0.54, -0.74), starred={"MT-ATP6", "MT-ND4"})
    ax.annotate(
        f"ROSMAP only • {len(rosmap_only)}\n{rosmap_only[0]}   {rosmap_only[1]}\n{rosmap_only[2]}   {rosmap_only[3]}",
        xy=(-1.14, 0.0), xycoords="data", xytext=(-2.05, 0.0), textcoords="data",
        ha="center", va="center", fontsize=16, color=TEXT,
        bbox={"boxstyle": "round,pad=0.32", "facecolor": WHITE, "edgecolor": ROSMAP, "linewidth": 2.0, "hatch": "////"},
        arrowprops={"arrowstyle": "-", "color": ROSMAP, "linewidth": 2.0}, zorder=9,
    )
    ax.text(0.22, -1.30, "SEA-AD only: 0 (∅)", ha="center", va="center", fontsize=16, color=MID)
    ax.set_xlim(-3.15, 2.30)
    ax.set_ylim(-1.55, 1.55)


def _draw_non_mt_gene_panel(ax: Any, regions: Mapping[str, set[str]]) -> None:
    ax.add_patch(Circle((-1.55, 0), 1.42, facecolor=ROSMAP_PALE, edgecolor=ROSMAP, linewidth=2.3, hatch="////", zorder=1))
    ax.add_patch(Circle((1.75, 0), 0.82, facecolor=SEAAD_PALE, edgecolor=SEAAD, linewidth=2.6, zorder=2))
    ax.text(-1.55, 1.53, "ROSMAP only • 15", ha="center", va="center", fontsize=17, weight="bold", color=ROSMAP)
    ax.text(1.75, 0.98, "SEA-AD only • 5", ha="center", va="center", fontsize=17, weight="bold", color=SEAAD)
    _gene_grid(
        ax, sorted(regions["rosmap_only"]),
        (-2.15, -0.95), (0.93, 0.67, 0.41, 0.15, -0.11, -0.37, -0.63, -0.89),
        daggers={"ANKRD11", "FTL", "NCOA1"},
    )
    _gene_grid(ax, sorted(regions["seaad_only"]), (1.75,), (0.37, 0.12, -0.13, -0.38, -0.63))
    ax.text(0.42, 1.43, "Common:\n0 (∅)", ha="center", va="center", fontsize=17, linespacing=1.0, weight="bold", color=SHARED)
    ax.set_xlim(-3.15, 2.80)
    ax.set_ylim(-1.55, 1.70)


def draw_gene_figure(bundle: Mapping[str, Any], plot_data: pd.DataFrame, region_summary: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    del plot_data, region_summary  # validated tables; labels are drawn from bundle regions
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), facecolor=WHITE)
    fig.subplots_adjust(left=0.02, right=0.985, bottom=0.19, top=0.91, wspace=0.04)
    for index, (ax, case) in enumerate(zip(axes, CLASS_ORDER)):
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.text(0.0, 1.04, "AB"[index], transform=ax.transAxes, ha="left", va="bottom", fontsize=20, weight="bold", color=TEXT)
        ax.set_title("MT driver class" if case == "mt_driver" else "Non-MT driver class", fontsize=20, weight="bold", color=TEXT, pad=8)
        if case == "mt_driver":
            _draw_mt_gene_panel(ax, bundle["regions"][case])
        else:
            _draw_non_mt_gene_panel(ax, bundle["regions"][case])
    fig.text(0.5, 0.125, "Descriptive gene-level view; network identity collapsed  •  no gene-level overlap p value", ha="center", va="center", fontsize=16, weight="bold", color=SHARED)
    fig.text(0.5, 0.050, "* MT-ATP6 and MT-ND4 are common only after networks are collapsed  •  † SEA-AD OPC KDA unavailable", ha="center", va="center", fontsize=16, color=MID)
    return fig, _render_meta(fig, minimum_required=16.0)


def _render_meta(fig: Any, *, minimum_required: float) -> dict[str, Any]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    visible = list(fig.texts)
    for ax in fig.axes:
        visible.extend(ax.texts)
        for title in (ax.title, ax._left_title, ax._right_title):
            if title.get_visible() and title.get_text() and title not in visible:
                visible.append(title)
    visible = [artist for artist in visible if artist.get_visible() and artist.get_text()]
    minimum = min(float(artist.get_fontsize()) for artist in visible)
    clipped = []
    for artist in visible:
        bbox = artist.get_window_extent(renderer=renderer)
        if bbox.x0 < fig.bbox.x0 - 1 or bbox.y0 < fig.bbox.y0 - 1 or bbox.x1 > fig.bbox.x1 + 1 or bbox.y1 > fig.bbox.y1 + 1:
            clipped.append(artist.get_text())
    require(minimum >= minimum_required, f"Minimum visible font is {minimum:.2f} pt")
    require(not clipped, "Text leaves canvas: " + " | ".join(clipped))
    return {"minimum_font_points": minimum, "canvas_clipped_text": clipped, "visible_text_count": len(visible)}


def _output_files(figure_id: str) -> list[str]:
    extra = (
        [f"{figure_id}_scorecard.tsv", f"{figure_id}_facet_summary.tsv"]
        if figure_id == STRICT_ID else [f"{figure_id}_region_summary.tsv"]
    )
    return [
        f"{figure_id}.png", f"{figure_id}.pdf", f"{figure_id}.svg",
        f"{figure_id}_plot_data.tsv", *extra,
        f"{figure_id}_caption.md", f"{figure_id}_methods.md",
        f"{figure_id}_checks.tsv", f"{figure_id}_artifacts.tsv", f"{figure_id}_status.tsv",
    ]


def _payload_files(figure_id: str) -> list[str]:
    return _output_files(figure_id)[:-2]


def render_images(fig: Any, staging: Path, figure_id: str, dpi: int) -> list[Path]:
    paths = []
    title = "Strict ROSMAP and SEA-AD key-driver overlap" if figure_id == STRICT_ID else "Gene-level ROSMAP and SEA-AD key-driver overlap"
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{figure_id}.{extension}"
        temporary = staging / f".{figure_id}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata = {"Title": title, "Creator": "Validation-human slide figure renderer", "CreationDate": None, "ModDate": None}
        elif extension == "svg":
            metadata = {"Title": title, "Creator": "Validation-human slide figure renderer", "Date": None}
        else:
            metadata = {"Software": "Validation-human slide figure renderer"}
        fig.savefig(temporary, format=extension, dpi=dpi if extension == "png" else None, facecolor=WHITE, bbox_inches=None, pad_inches=0, metadata=metadata)
        require(temporary.stat().st_size > 1000, f"Rendered file is too small: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    plt.close(fig)
    return paths


def check_record(figure_id: str, check_id: str, passed: bool, observed: Any, expected: Any, details: str, *, severity: str = "blocking", status: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "figure_id": figure_id,
        "check_id": check_id,
        "severity": severity,
        "status": status or ("pass" if passed else "fail"),
        "observed": observed,
        "expected": expected,
        "details": details,
    }


def image_checks(figure_id: str, image_paths: Sequence[Path], dpi: int) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    svg = lookup[".svg"].read_text(encoding="utf-8")
    with Image.open(lookup[".png"]) as image:
        width, height = image.size
        embedded = image.info.get("dpi", (math.nan, math.nan))
        mode = image.mode
    return [
        check_record(figure_id, "image_export_set", set(lookup) == {".png", ".pdf", ".svg"}, "|".join(sorted(lookup)), ".pdf|.png|.svg", "Three slide and vector formats."),
        check_record(figure_id, "image_exports_nonempty", all(path.stat().st_size > 1000 for path in image_paths), "all >1000", "all >1000", "Exports are nontrivial."),
        check_record(figure_id, "svg_searchable_text", "<text" in svg.lower(), "present", "present", "SVG text remains searchable."),
        check_record(figure_id, "svg_vector_paths", "<path" in svg.lower(), "present", "present", "SVG preserves vector geometry."),
        check_record(figure_id, "pdf_signature", lookup[".pdf"].read_bytes()[:5] == b"%PDF-", lookup[".pdf"].read_bytes()[:5].decode("latin1"), "%PDF-", "PDF signature."),
        check_record(figure_id, "png_dimensions", (width, height) == (PNG_WIDTH, PNG_HEIGHT), f"{width}x{height}", f"{PNG_WIDTH}x{PNG_HEIGHT}", "Frozen 12 × 5.3 inch slide asset."),
        check_record(figure_id, "png_resolution", all(math.isfinite(v) and abs(v - dpi) <= 1 for v in embedded), f"{embedded[0]:.2f}|{embedded[1]:.2f}", f"{dpi}|{dpi}", "Embedded PNG DPI."),
        check_record(figure_id, "png_color_mode", mode in {"RGB", "RGBA"}, mode, "RGB or RGBA", "PowerPoint-compatible color mode."),
    ]


def build_checks(figure_id: str, bundle: Mapping[str, Any], tables: Mapping[str, pd.DataFrame], image_paths: Sequence[Path], render_meta: Mapping[str, Any], dpi: int, visual_review_status: str) -> pd.DataFrame:
    svg = next(path for path in image_paths if path.suffix == ".svg").read_text(encoding="utf-8")
    checks = [
        check_record(figure_id, "upstream_phases_complete", True, "VH09|VH10C|VH10D validated_complete", "VH09|VH10C|VH10D validated_complete", "Validated during loading."),
        check_record(figure_id, "frozen_input_hashes", len(bundle["input_digests"]) == len(INPUT_PATHS), len(bundle["input_digests"]), len(INPUT_PATHS), "Every compact input matches frozen SHA-256."),
        check_record(figure_id, "seaad_blinded_freeze", True, "rosmap_candidate_files_read=False", "False", "SEA-AD list was frozen before candidate-bearing ROSMAP files were opened."),
        check_record(figure_id, "minimum_font_size", render_meta["minimum_font_points"] >= 16.0, render_meta["minimum_font_points"], ">=16", "Projection-scale typography."),
        check_record(figure_id, "canvas_text_clipping", not render_meta["canvas_clipped_text"], len(render_meta["canvas_clipped_text"]), 0, "No text leaves the canvas."),
        check_record(figure_id, "no_vh05_vh06_inputs", not any("/05_" in path or "/06_" in path for path in bundle["input_digests"]), "none", "none", "Figure does not require missing pseudobulk/QC phases."),
    ]
    if figure_id == STRICT_ID:
        plot = tables["plot_data"]
        score = tables["scorecard"]
        facets = tables["facet_summary"]
        shared = plot.loc[plot["pair_status"].eq("strict_shared")]
        checks.extend(
            [
                check_record(figure_id, "paired_rank_rows", len(plot) == 12, len(plot), 12, "Full Excitatory/Inhibitory MT top-list union."),
                check_record(figure_id, "paired_rank_keys_unique", not plot.duplicated(["broad_network", "gene"]).any(), "unique", "unique", "Endpoint keys."),
                check_record(figure_id, "strict_shared_units", len(shared) == 6, len(shared), 6, "Same-network, same-class shared units."),
                check_record(figure_id, "strict_unique_symbols", shared["gene"].nunique() == 4, shared["gene"].nunique(), 4, "Six units resolve to four symbols."),
                check_record(figure_id, "scorecard_counts", score[["rosmap_testable_selected_units", "seaad_selected_units", "strict_shared_units"]].astype(int).values.tolist() == [[19, 8, 6], [17, 5, 0]], str(score[["rosmap_testable_selected_units", "seaad_selected_units", "strict_shared_units"]].astype(int).values.tolist()), "[[19,8,6],[17,5,0]]", "Class-level endpoint scorecard."),
                check_record(figure_id, "facet_statistics", facets["shared_selected_units"].astype(int).tolist() == [2, 4], str(facets["shared_selected_units"].astype(int).tolist()), "[2,4]", "Excitatory and Inhibitory strict overlaps."),
                check_record(figure_id, "svg_all_endpoint_genes", all(gene in svg for gene in plot["gene"]), sum(gene in svg for gene in plot["gene"]), len(plot), "All paired-rank endpoint genes remain searchable."),
                check_record(figure_id, "svg_nominal_p_guardrail", "nominal p = 2.33 × 10⁻⁴" in svg and "nominal p = 1.22 × 10⁻⁹" in svg, "present", "present", "Both per-list p values are explicitly nominal."),
                check_record(figure_id, "strict_definition_visible", "strict unit: network + gene + class" in svg, "present", "present", "Primary unit definition is visible."),
            ]
        )
    else:
        plot = tables["plot_data"]
        summary = tables["region_summary"]
        counts = {(row.case_id, row.region): as_int(row.region_count) for row in summary.itertuples(index=False)}
        expected = {("mt_driver", "rosmap_only"): 4, ("mt_driver", "common"): 6, ("mt_driver", "seaad_only"): 0, ("non_mt_driver", "rosmap_only"): 15, ("non_mt_driver", "common"): 0, ("non_mt_driver", "seaad_only"): 5}
        checks.extend(
            [
                check_record(figure_id, "gene_rows", len(plot) == 30, len(plot), 30, "Unique class-gene symbols."),
                check_record(figure_id, "gene_keys_unique", not plot.duplicated(["case_id", "gene"]).any(), "unique", "unique", "One row per class and symbol."),
                check_record(figure_id, "region_counts", counts == expected, str(counts), str(expected), "Frozen MT containment and non-MT disjoint regions."),
                check_record(figure_id, "region_geometry", (summary["geometry_margin"].astype(float) >= 0).all(), summary["geometry_margin"].astype(float).min(), ">=0", "Nested MT and disjoint non-MT geometry."),
                check_record(figure_id, "svg_all_gene_labels", all(gene in svg for gene in plot["gene"]), sum(gene in svg for gene in plot["gene"]), len(plot), "All region genes remain searchable."),
                check_record(figure_id, "svg_empty_regions", "SEA-AD only: 0 (∅)" in svg and "Common:" in svg and "0 (∅)" in svg, "both present", "both present", "Zero regions are explicit."),
                check_record(figure_id, "network_collapse_guardrail", "network identity collapsed" in svg and "common only after networks are collapsed" in svg, "present", "present", "Secondary endpoint cannot be mistaken for strict overlap."),
                check_record(figure_id, "opcs_guardrail", "SEA-AD OPC KDA unavailable" in svg and plot["opcs_not_testable_guardrail"].map(truth).sum() == 3, f"visible|{plot['opcs_not_testable_guardrail'].map(truth).sum()}", "visible|3", "ROSMAP OPC-only genes are not treated as negative tests."),
                check_record(figure_id, "no_gene_level_p_value", "nominal p =" not in svg, "absent", "absent", "No gene-level inferential overlap statistic."),
            ]
        )
    checks.extend(image_checks(figure_id, image_paths, dpi))
    if visual_review_status == "complete":
        checks.extend(
            [
                check_record(figure_id, "manual_color_review", True, "complete", "complete", "Reviewed at intended slide size in color.", severity="nonblocking"),
                check_record(figure_id, "manual_grayscale_review", True, "complete", "complete", "Reviewed in grayscale; redundant encodings remain interpretable.", severity="nonblocking"),
            ]
        )
    else:
        checks.extend(
            [
                check_record(figure_id, "manual_color_review", False, "pending", "complete", "Manual color review remains pending.", severity="nonblocking", status="pending"),
                check_record(figure_id, "manual_grayscale_review", False, "pending", "complete", "Manual grayscale review remains pending.", severity="nonblocking", status="pending"),
            ]
        )
    frame = pd.DataFrame(checks)
    blocking = frame.loc[frame["severity"].eq("blocking") & ~frame["status"].eq("pass")]
    require(blocking.empty, "Blocking checks failed: " + ", ".join(blocking["check_id"]))
    return frame


def documentation(figure_id: str) -> tuple[str, str]:
    if figure_id == STRICT_ID:
        caption = """# Strict ROSMAP–SEA-AD overlap and paired ranks: caption

**Strict network-aware rediscovery of selected top key drivers.** The scorecard compares ROSMAP selected units that were testable in SEA-AD with independently selected SEA-AD units, using the primary unit `broad network + gene + driver class`. Nineteen ROSMAP MT units were testable, eight SEA-AD MT units were selected, and six strict MT units were shared; the corresponding non-MT counts were 17, five, and zero. The paired-rank facets display the complete ROSMAP and SEA-AD MT top lists in the two networks with strict overlap. Navy connectors mark the six strict units: MT-CO2 and MT-CYB in Excitatory neurons, and MT-CO2, MT-CO3, MT-CYB, and MT-ND5 in Inhibitory neurons. Gray endpoints are unmatched selected units, not omitted data. The per-list hypergeometric p values are nominal and unadjusted. Ranks describe the frozen selection order, not expression effect size, causal direction, or agreement in DEG direction.
"""
        methods = f"""# Strict ROSMAP–SEA-AD overlap and paired ranks: methods

The renderer reads validated VH09 ROSMAP selected units, the independently frozen VH10C SEA-AD list, and the VH10D strict overlap and summary tables. Upstream statuses, checks, registered full-file SHA-256 values, blind-freeze flag, `{QUERY_RULE}`, and `{RESULT_TIER}` are required before rendering. ROSMAP scorecard denominators include only selected units in the common assessable universe. A strict shared unit must match broad network, current gene symbol, and exact driver class. The slopegraphs retain the complete MT selected-list union for Excitatory and Inhibitory neurons; unmatched cohort endpoints are drawn in gray and strict matches use navy connectors. Jaccard indices and nominal per-list hypergeometric p values are read from VH10D rather than recomputed. The 12 × 5.3 inch asset uses at least 16-point text and is exported as searchable SVG, vector PDF, and 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/{Path(__file__).name} \\
  --figure strict \\
  --output-base results/figures/validation_human \\
  --visual-review-status pending
```
"""
    else:
        caption = """# ROSMAP–SEA-AD top-driver gene overlap slide: caption

**Descriptive gene-level overlap after broad-network identity is collapsed.** Within the MT driver class, all six unique SEA-AD genes occurred somewhere in the ten-gene ROSMAP set, leaving four ROSMAP-only genes and no SEA-AD-only gene. MT-ATP6 and MT-ND4 become common only after network identity is removed; neither is a strict same-network rediscovery. The non-MT sets were disjoint: 15 ROSMAP-only genes and five SEA-AD-only genes. Daggers identify ANKRD11, FTL, and NCOA1, which were selected only in ROSMAP OPC; SEA-AD had no included OPC KDA run, so they are not tested-negative results. Counts are unique symbols within class, not network–gene units. This secondary descriptive view has no gene-level overlap p value; the primary endpoint remains strict broad-network + gene + driver-class overlap within the common assessable universe.
"""
        methods = f"""# ROSMAP–SEA-AD top-driver gene overlap slide: methods

The renderer reads validated VH09 ROSMAP selected units and the independently frozen VH10C SEA-AD top lists, using compact VH10D overlap artifacts as cross-checks. Upstream statuses, checks, registered full-file SHA-256 values, blind-freeze flag, `{QUERY_RULE}`, and `{RESULT_TIER}` are required. Symbols are split by exact driver class and deduplicated across broad networks. MT geometry is nested because the SEA-AD set is contained in the ROSMAP set; non-MT geometry is disjoint because the intersection is empty. ROSMAP uses an orange hatched outline, SEA-AD uses a teal solid fill, and every region is directly labeled. The visible footer states that network identity is collapsed and distinguishes the two gene-level-only common symbols. The 12 × 5.3 inch asset uses at least 16-point text and is exported as searchable SVG, vector PDF, and 5400 × 2385 PNG at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/{Path(__file__).name} \\
  --figure gene \\
  --output-base results/figures/validation_human \\
  --visual-review-status pending
```
"""
    return caption, methods


def table_rows(path: Path) -> int | str:
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0) if path.suffix == ".tsv" else "NA"


def build_artifacts(figure_id: str, bundle: Mapping[str, Any], staging: Path, renderer: Path) -> pd.DataFrame:
    rows = []
    for relative, digest in sorted(bundle["input_digests"].items()):
        path = bundle["project_root"] / relative
        rows.append({"schema_version": SCHEMA, "figure_id": figure_id, "artifact_role": "input", "logical_name": relative, "path": relative, "bytes": path.stat().st_size, "sha256": digest, "rows": table_rows(path), "validation_state": "validated_frozen_input"})
    relative_renderer = str(renderer.relative_to(bundle["project_root"]))
    rows.append({"schema_version": SCHEMA, "figure_id": figure_id, "artifact_role": "script", "logical_name": "renderer", "path": relative_renderer, "bytes": renderer.stat().st_size, "sha256": sha256_file(renderer), "rows": "NA", "validation_state": "validated_script"})
    for name in _payload_files(figure_id):
        path = staging / name
        require(path.is_file() and path.stat().st_size > 0, f"Missing payload: {name}")
        rows.append({"schema_version": SCHEMA, "figure_id": figure_id, "artifact_role": "output", "logical_name": name, "path": name, "bytes": path.stat().st_size, "sha256": sha256_file(path), "rows": table_rows(path), "validation_state": "validated_output"})
    frame = pd.DataFrame(rows)
    require(frame["path"].is_unique, "Artifact paths duplicated")
    require(set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(_payload_files(figure_id)), "Output artifact scope changed")
    require(not frame["path"].isin(_output_files(figure_id)[-2:]).any(), "Manifest/status entered hash scope")
    return frame


def validate_output(project_root: Path, output_root: Path, *, expected_visual_status: str | None = None, figure_id: str | None = None) -> None:
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    figure_id = figure_id or output_root.name
    require(figure_id in FIGURE_IDS, f"Unknown figure package: {figure_id}")
    require(output_root.is_dir(), f"Missing output directory: {output_root}")
    require(sorted(path.name for path in output_root.iterdir() if path.is_file()) == sorted(_output_files(figure_id)), "Output package file set changed")
    status = one_row(read_tsv(output_root / f"{figure_id}_status.tsv"), "figure status")
    require(status["schema_version"] == SCHEMA and status["figure_id"] == figure_id, "Figure status identity changed")
    visual = status["visual_review_status"]
    if expected_visual_status is not None:
        require(visual == expected_visual_status, "Visual-review status changed")
    expected_validation = "validated_complete" if visual == "complete" else "awaiting_visual_review"
    require(status["validation_status"] == expected_validation, "Figure validation status changed")
    checks = read_tsv(output_root / f"{figure_id}_checks.tsv")
    require(not ((checks["severity"] == "blocking") & (checks["status"] != "pass")).any(), "Published package has failed blocking checks")
    if visual == "complete":
        require(checks["status"].eq("pass").all(), "Completed package has incomplete checks")
    artifacts_path = output_root / f"{figure_id}_artifacts.tsv"
    require(sha256_file(artifacts_path) == status["artifact_manifest_sha256"], "Artifact-manifest SHA changed")
    artifacts = read_tsv(artifacts_path)
    require(set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"]) == set(_payload_files(figure_id)), "Artifact output scope changed")
    for row in artifacts.itertuples(index=False):
        path = output_root / row.path if row.artifact_role == "output" else project_root / row.path
        require(path.is_file(), f"Missing artifact: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact digest changed: {row.path}")
    require(all(row["status"] == "pass" for row in image_checks(figure_id, [output_root / f"{figure_id}.{ext}" for ext in ("png", "pdf", "svg")], as_int(status["png_dpi"]))), "Published image checks failed")
    print(f"Validated figure package: {output_root}")


def publish_one(project_root: Path, output_root: Path, figure_id: str, *, dpi: int, visual_review_status: str, force: bool, bundle: Mapping[str, Any]) -> None:
    output_root = Path(output_root).resolve()
    if output_root.exists() and not force:
        raise FileExistsError(f"Output exists; use --force for recoverable replacement: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{figure_id}.staging.", dir=output_root.parent))
    try:
        if figure_id == STRICT_ID:
            tables = {
                "plot_data": build_strict_plot_data(bundle),
                "scorecard": build_strict_scorecard(bundle),
                "facet_summary": build_strict_facet_summary(bundle),
            }
            fig, render_meta = draw_strict_figure(bundle, tables["plot_data"], tables["scorecard"], tables["facet_summary"])
        else:
            tables = {
                "plot_data": build_gene_plot_data(bundle),
                "region_summary": build_gene_region_summary(bundle),
            }
            fig, render_meta = draw_gene_figure(bundle, tables["plot_data"], tables["region_summary"])
        image_paths = render_images(fig, staging, figure_id, dpi)
        for logical_name, frame in tables.items():
            write_tsv(frame, staging / f"{figure_id}_{logical_name}.tsv")
        caption, methods = documentation(figure_id)
        write_text(staging / f"{figure_id}_caption.md", caption)
        write_text(staging / f"{figure_id}_methods.md", methods)
        checks = build_checks(figure_id, bundle, tables, image_paths, render_meta, dpi, visual_review_status)
        write_tsv(checks, staging / f"{figure_id}_checks.tsv")
        renderer = Path(__file__).resolve()
        artifacts = build_artifacts(figure_id, bundle, staging, renderer)
        artifacts_path = staging / f"{figure_id}_artifacts.tsv"
        write_tsv(artifacts, artifacts_path)
        pending = int((checks["status"] != "pass").sum())
        status = pd.DataFrame(
            [
                {
                    "schema_version": SCHEMA,
                    "figure_id": figure_id,
                    "validation_status": "validated_complete" if visual_review_status == "complete" and pending == 0 else "awaiting_visual_review",
                    "visual_review_status": visual_review_status,
                    "failed_blocking_checks": int(((checks["severity"] == "blocking") & (checks["status"] != "pass")).sum()),
                    "pending_nonblocking_checks": int(((checks["severity"] == "nonblocking") & (checks["status"] != "pass")).sum()),
                    "input_bundle_sha256": bundle["input_bundle_sha256"],
                    "renderer_sha256": sha256_file(renderer),
                    "artifact_manifest_sha256": sha256_file(artifacts_path),
                    "figure_width_inches": FIGURE_WIDTH_IN,
                    "figure_height_inches": FIGURE_HEIGHT_IN,
                    "png_dpi": dpi,
                    "png_width": PNG_WIDTH,
                    "png_height": PNG_HEIGHT,
                    "input_files": len(bundle["input_digests"]),
                    "output_files": len(_output_files(figure_id)),
                    "plot_data_rows": len(tables["plot_data"]),
                    "contract_scope": "strict_network_gene_class_primary" if figure_id == STRICT_ID else "gene_level_network_collapsed_secondary",
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        write_tsv(status, staging / f"{figure_id}_status.tsv")
        validate_output(project_root, staging, expected_visual_status=visual_review_status, figure_id=figure_id)
        if output_root.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            output_root.replace(output_root.parent / f".{output_root.name}.backup.{timestamp}.{os.getpid()}")
        staging.replace(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"Published {len(_output_files(figure_id))} package files: {output_root}")


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if args.validate_output:
        validate_output(project_root, resolve(project_root, args.validate_output))
        return 0
    output_base = resolve(project_root, args.output_base)
    selections = FIGURE_IDS if args.figure == "all" else (STRICT_ID if args.figure == "strict" else GENE_ID,)
    bundle = load_bundle(project_root)
    for figure_id in selections:
        publish_one(project_root, output_base / figure_id, figure_id, dpi=args.png_dpi, visual_review_status=args.visual_review_status, force=args.force, bundle=bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
