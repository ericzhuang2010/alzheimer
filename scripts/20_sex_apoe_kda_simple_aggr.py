#!/usr/bin/env python3
"""Build the requested returned-only Phase 20 KDA aggregation.

This intentionally exploratory analysis uses only rows returned as significant
by the stock Phase 12 ``call_key_drivers()`` calls included in Phase 20.  The
returned within-call adjusted P values are treated as the input values:

* one returned call: pass the within-call q value through unchanged;
* two or more returned calls: combine the returned q values with equal-weight
  ACAT.

No additional across-gene BH adjustment is applied because that would violate
the requested singleton pass-through rule.  The canonical derived field is
``returned_run_q_acat_score``. ``requested_final_q`` is retained as an
identical user-requested alias, but is not a formally FDR-controlled q value.
The script writes both a literal all-call gene view and a Phase 20
sex/APOE-by-broad-network category view.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import math
import os
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml
from scipy.stats import cauchy


TRUE_VALUES = {"TRUE", "T", "1", "YES"}
NA_TEXT = "NA"
SCHEMA_ROOT = "phase20_simple_returned_only_acat_v1"
ANALYSIS_ID = "phase20_simple_returned_only_acat_v1"


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def as_float(value: Any) -> float | None:
    if value in (None, "", NA_TEXT):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def display_value(value: Any) -> Any:
    if value is None:
        return NA_TEXT
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return repr(value) if math.isfinite(value) else NA_TEXT
    return value


def project_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", newline="")
    return path.open(mode, newline="")


def iter_tsv(path: Path) -> Iterator[dict[str, str]]:
    if not path.is_file():
        fail(f"Required file does not exist: {path}")
    with open_text(path, "r") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_tsv(path: Path) -> list[dict[str, str]]:
    return list(iter_tsv(path))


def deterministic_gzip_text(path: Path):
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline="")


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: Sequence[str],
    schema_version: str,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp.{os.getpid()}"
    connection = (
        deterministic_gzip_text(temporary)
        if path.suffix == ".gz"
        else temporary.open("w", newline="")
    )
    count = 0
    with connection as handle:
        names = ["schema_version", *[field for field in fields if field != "schema_version"]]
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            output = {field: display_value(row.get(field)) for field in names}
            output["schema_version"] = schema_version
            writer.writerow(output)
            count += 1
    temporary.replace(path)
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def acat_statistic(value: float) -> float:
    if value < 1e-15:
        return 1.0 / (value * math.pi)
    return math.tan((0.5 - value) * math.pi)


def acat_combine(values: Sequence[float], tolerance: float = 1e-300) -> float:
    """NetWeaver-compatible equal-weight ACAT used elsewhere in Phase 20."""

    if not values:
        fail("ACAT requires at least one value")
    work = [float(value) for value in values]
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in work):
        fail("ACAT inputs must be finite values in [0, 1]")
    if all(value == 1 for value in work):
        return 1.0
    positive = [value for value in work if value > 0]
    zero_replacement = min(min(positive), tolerance) if positive else tolerance
    work = [zero_replacement if value == 0 else value for value in work]
    if any(value == 1 for value in work):
        maximum = max(value for value in work if value < 1)
        one_replacement = maximum / 2.0 + 0.5
        work = [one_replacement if value == 1 else value for value in work]
    statistic = statistics.fmean(acat_statistic(value) for value in work)
    return float(cauchy.sf(statistic))


def load_annotations(path: Path) -> dict[str, dict[str, Any]]:
    annotations: dict[str, dict[str, Any]] = {}
    for row in iter_tsv(path):
        current_symbol = row.get("symbol_hgnc_current", "")
        symbol = (
            current_symbol
            if current_symbol and current_symbol != NA_TEXT
            else row.get("symbol_original", "")
        )
        if not symbol or symbol == NA_TEXT:
            continue
        current = {
            "is_core_mito": is_true(row.get("is_mitocarta3")),
            "mitocarta_canonical_symbol": row.get("mitocarta_canonical_symbol") or NA_TEXT,
            "mito_tier": row.get("mito_tier") or NA_TEXT,
            "genome_origin": row.get("genome_origin") or NA_TEXT,
        }
        previous = annotations.get(symbol)
        if previous is None:
            annotations[symbol] = current
        elif previous["is_core_mito"] != current["is_core_mito"]:
            fail(f"Conflicting core-MitoCarta annotation for {symbol}")
    return annotations


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    observed: Any,
    expected: Any,
    passed: bool,
    message: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "observed": observed,
            "expected": expected,
            "passed": passed,
            "severity": "error",
            "message": message,
        }
    )


def summarize_unit(
    rows: Sequence[dict[str, Any]],
    *,
    scope: str,
    signature_group: str = "ALL",
    broad_network: str = "ALL",
    labels: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not rows:
        fail("Cannot summarize an empty returned-row unit")
    genes = {str(row["current_symbol"]) for row in rows}
    if len(genes) != 1:
        fail(f"Aggregate unit contains multiple genes: {sorted(genes)}")
    gene = next(iter(genes))
    q_values = [float(row["returned_within_call_q"]) for row in rows]
    run_ids = [str(row["kda_run_id"]) for row in rows]
    if len(set(run_ids)) != len(run_ids):
        fail(f"Duplicate returned run for {scope}/{signature_group}/{broad_network}/{gene}")
    if len(q_values) == 1:
        final_value = q_values[0]
        acat_value = None
        method = "singleton_within_call_q_passthrough"
    else:
        final_value = acat_combine(q_values)
        acat_value = final_value
        method = "acat_of_returned_within_call_q_values"
    ann = rows[0]
    if any(bool(row["is_core_mito"]) != bool(ann["is_core_mito"]) for row in rows):
        fail(f"Driver-class drift for {gene}")
    sex = labels.get(signature_group, {}).get("sex", "ALL") if labels else "ALL"
    apoe = labels.get(signature_group, {}).get("apoe_group", "ALL") if labels else "ALL"
    return {
        "analysis_scope": scope,
        "signature_group": signature_group,
        "sex": sex,
        "apoe_group": apoe,
        "broad_network": broad_network,
        "current_symbol": gene,
        "case_id": "mt_driver" if ann["is_core_mito"] else "non_mt_driver",
        "is_core_mito": bool(ann["is_core_mito"]),
        "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
        "mito_tier": ann["mito_tier"],
        "genome_origin": ann["genome_origin"],
        "returned_call_count": len(rows),
        "returned_fine_cell_type_count": len({row["fine_cell_type"] for row in rows}),
        "returned_fine_cell_types": "|".join(sorted({row["fine_cell_type"] for row in rows})),
        "returned_signature_group_count": len({row["signature_group"] for row in rows}),
        "returned_signature_groups": "|".join(sorted({row["signature_group"] for row in rows})),
        "returned_broad_network_count": len({row["broad_network"] for row in rows}),
        "returned_broad_networks": "|".join(sorted({row["broad_network"] for row in rows})),
        "returned_direction_count": len({row["signature_direction"] for row in rows}),
        "returned_directions": "|".join(sorted({row["signature_direction"] for row in rows})),
        "minimum_returned_within_call_q": min(q_values),
        "median_returned_within_call_q": statistics.median(q_values),
        "maximum_returned_within_call_q": max(q_values),
        "acat_of_returned_within_call_q": acat_value,
        "returned_run_q_acat_score": final_value,
        "requested_final_q": final_value,
        "final_value_method": method,
        "input_statistic": "stock_within_call_bh_q",
        "inferential_status": "exploratory_postselection",
        "multiple_testing_after_acat": "none",
        "additional_across_gene_bh_applied": False,
        "formal_fdr_controlled_q": False,
        "returned_run_ids": "|".join(sorted(run_ids)),
        "rank": None,
    }


def assign_ranks(rows: list[dict[str, Any]], key_fields: Sequence[str]) -> None:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row[field]) for field in key_fields)
        groups[key].append(row)
    for members in groups.values():
        members.sort(
            key=lambda row: (
                float(row["returned_run_q_acat_score"]),
                str(row["current_symbol"]),
            )
        )
        for rank, row in enumerate(members, start=1):
            row["rank"] = rank


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/phase20_sex_apoe_kda.yml",
        help="Frozen Phase 20 configuration used to define groups and networks",
    )
    parser.add_argument(
        "--run-manifest",
        default=(
            "results/minerva_production/20_sex_apoe_kda/00_inputs/"
            "phase20_source_run_manifest.tsv"
        ),
    )
    parser.add_argument(
        "--stock-results",
        default="results/minerva_production/12_kda/kda_results.tsv.gz",
    )
    parser.add_argument(
        "--annotation",
        default="results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz",
    )
    parser.add_argument(
        "--output",
        default=(
            "results/minerva_production/20_sex_apoe_kda_simple_aggr"
        ),
    )
    return parser.parse_args()


AGGREGATE_FIELDS = """
analysis_scope signature_group sex apoe_group broad_network current_symbol
case_id is_core_mito mitocarta_canonical_symbol mito_tier genome_origin
returned_call_count returned_fine_cell_type_count returned_fine_cell_types
returned_signature_group_count returned_signature_groups
returned_broad_network_count returned_broad_networks returned_direction_count
returned_directions minimum_returned_within_call_q
median_returned_within_call_q maximum_returned_within_call_q
acat_of_returned_within_call_q returned_run_q_acat_score requested_final_q final_value_method
input_statistic inferential_status multiple_testing_after_acat
additional_across_gene_bh_applied formal_fdr_controlled_q returned_run_ids rank
""".split()

DETAIL_FIELDS = """
kda_run_id analysis_tier fine_cell_type broad_network signature_group sex
apoe_group signature_direction current_symbol case_id is_core_mito
mitocarta_canonical_symbol best_layer overlap_count neighborhood_size
signature_size fold_enrichment returned_log_p returned_raw_p
returned_within_call_q global_returned_call_count global_returned_run_q_acat_score
global_requested_final_q global_rank category_returned_call_count
category_returned_run_q_acat_score category_requested_final_q category_rank
""".split()

CATEGORY_FIELDS = """
signature_group sex apoe_group broad_network included_call_count
stock_returned_row_count all_class_returned_gene_count mt_returned_gene_count
non_mt_returned_gene_count singleton_gene_unit_count recurrent_gene_unit_count
minimum_requested_final_q
""".split()

CHECK_FIELDS = "check_id observed expected passed severity message".split()
STATUS_FIELDS = """
analysis_id execution_status interpretation_status git_revision
included_run_count stock_returned_row_count unique_returned_gene_count
global_singleton_gene_count global_recurrent_gene_count global_aggregate_row_count
category_gene_unit_count category_singleton_unit_count category_recurrent_unit_count
structural_category_count analyzable_category_count failed_check_count output_directory
""".split()

ARTIFACT_FIELDS = "role path bytes sha256".split()


def run() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = project_path(root, args.config)
    manifest_path = project_path(root, args.run_manifest)
    stock_path = project_path(root, args.stock_results)
    annotation_path = project_path(root, args.annotation)
    output_dir = project_path(root, args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    groups = list(config["scope"]["groups"])
    networks = list(config["scope"]["broad_networks"])
    labels = dict(config["scope"]["group_labels"])

    checks: list[dict[str, Any]] = []
    manifest_rows = read_tsv(manifest_path)
    included_runs = [row for row in manifest_rows if is_true(row.get("phase20_included"))]
    run_lookup = {row["kda_run_id"]: row for row in included_runs}
    add_check(
        checks,
        "included_run_count",
        len(included_runs),
        295,
        len(included_runs) == 295 and len(run_lookup) == 295,
        "Use the frozen 295-call Phase 20 source scope",
    )
    add_check(
        checks,
        "included_run_contract",
        sum(
            row["eligibility_status"] == "eligible"
            and row["terminal_status"].startswith("completed")
            and row["signature_group"] in groups
            and row["broad_network"] in networks
            for row in included_runs
        ),
        len(included_runs),
        all(
            row["eligibility_status"] == "eligible"
            and row["terminal_status"].startswith("completed")
            and row["signature_group"] in groups
            and row["broad_network"] in networks
            for row in included_runs
        ),
        "Every included call must satisfy the frozen Phase 20 scope",
    )

    annotations = load_annotations(annotation_path)
    returned_rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    stock_rows_in_scope = 0
    invalid_significant_rows = 0
    metadata_mismatches = 0
    annotation_missing = 0
    for row in iter_tsv(stock_path):
        run_id = row["kda_run_id"]
        if run_id not in run_lookup:
            continue
        stock_rows_in_scope += 1
        key = (run_id, row["key_driver"])
        if key in seen_keys:
            fail(f"Duplicate stock returned key: {key}")
        seen_keys.add(key)
        run = run_lookup[run_id]
        if any(
            row[field] != run[field]
            for field in (
                "fine_cell_type",
                "broad_network",
                "signature_group",
                "signature_direction",
            )
        ):
            metadata_mismatches += 1
        within_q = as_float(row.get("adjusted_p_value"))
        log_p = as_float(row.get("log_p_value"))
        if within_q is None or within_q <= 0 or within_q > 0.05 + 1e-12:
            invalid_significant_rows += 1
        if log_p is None or log_p > 1e-12:
            fail(f"Invalid stock log P for {key}: {row.get('log_p_value')}")
        raw_p = math.exp(float(log_p))
        symbol = row["key_driver"]
        ann = annotations.get(symbol)
        if ann is None:
            annotation_missing += 1
            ann = {
                "is_core_mito": False,
                "mitocarta_canonical_symbol": NA_TEXT,
                "mito_tier": "annotation_missing_treated_non_mt",
                "genome_origin": NA_TEXT,
            }
        label = labels[row["signature_group"]]
        returned_rows.append(
            {
                "kda_run_id": run_id,
                "analysis_tier": row["analysis_tier"],
                "fine_cell_type": row["fine_cell_type"],
                "broad_network": row["broad_network"],
                "signature_group": row["signature_group"],
                "sex": label["sex"],
                "apoe_group": label["apoe_group"],
                "signature_direction": row["signature_direction"],
                "current_symbol": symbol,
                "case_id": "mt_driver" if ann["is_core_mito"] else "non_mt_driver",
                "is_core_mito": ann["is_core_mito"],
                "mitocarta_canonical_symbol": ann["mitocarta_canonical_symbol"],
                "mito_tier": ann["mito_tier"],
                "genome_origin": ann["genome_origin"],
                "best_layer": int(row["best_layer"]),
                "overlap_count": int(row["overlap_count"]),
                "neighborhood_size": int(row["neighborhood_size"]),
                "signature_size": int(row["signature_size"]),
                "fold_enrichment": float(row["fold_enrichment"]),
                "returned_log_p": float(log_p),
                "returned_raw_p": raw_p,
                "returned_within_call_q": float(within_q),
            }
        )

    add_check(
        checks,
        "stock_returned_row_count",
        stock_rows_in_scope,
        2494,
        stock_rows_in_scope == 2494 and len(returned_rows) == 2494,
        "Use every stock significant return from the 295 included calls",
    )
    add_check(
        checks,
        "stock_returned_unique_keys",
        len(seen_keys),
        len(returned_rows),
        len(seen_keys) == len(returned_rows),
        "Each run and gene must occur at most once",
    )
    add_check(
        checks,
        "stock_significance_filter",
        invalid_significant_rows,
        0,
        invalid_significant_rows == 0,
        "Every stock input row must have within-call q <= 0.05",
    )
    add_check(
        checks,
        "stock_manifest_metadata",
        metadata_mismatches,
        0,
        metadata_mismatches == 0,
        "Stock result metadata must match the frozen run manifest",
    )
    add_check(
        checks,
        "returned_gene_annotation",
        annotation_missing,
        0,
        annotation_missing == 0,
        "Every returned gene should have recorded mitochondrial annotation",
    )

    by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_category_gene: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in returned_rows:
        by_gene[row["current_symbol"]].append(row)
        by_category_gene[
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        ].append(row)

    global_rows = [
        summarize_unit(rows, scope="all_phase20_calls")
        for _, rows in sorted(by_gene.items())
    ]
    assign_ranks(global_rows, [])
    category_rows = [
        summarize_unit(
            rows,
            scope="signature_group_by_broad_network",
            signature_group=group,
            broad_network=network,
            labels=labels,
        )
        for (group, network, _), rows in sorted(by_category_gene.items())
    ]
    assign_ranks(category_rows, ["signature_group", "broad_network"])

    global_lookup = {row["current_symbol"]: row for row in global_rows}
    category_lookup = {
        (row["signature_group"], row["broad_network"], row["current_symbol"]): row
        for row in category_rows
    }
    detail_rows: list[dict[str, Any]] = []
    for row in sorted(
        returned_rows,
        key=lambda item: (
            item["signature_group"],
            item["broad_network"],
            item["current_symbol"],
            item["kda_run_id"],
        ),
    ):
        global_row = global_lookup[row["current_symbol"]]
        category_row = category_lookup[
            (row["signature_group"], row["broad_network"], row["current_symbol"])
        ]
        detail_rows.append(
            {
                **row,
                "global_returned_call_count": global_row["returned_call_count"],
                "global_returned_run_q_acat_score": global_row[
                    "returned_run_q_acat_score"
                ],
                "global_requested_final_q": global_row["requested_final_q"],
                "global_rank": global_row["rank"],
                "category_returned_call_count": category_row["returned_call_count"],
                "category_returned_run_q_acat_score": category_row[
                    "returned_run_q_acat_score"
                ],
                "category_requested_final_q": category_row["requested_final_q"],
                "category_rank": category_row["rank"],
            }
        )

    calls_by_category = Counter(
        (row["signature_group"], row["broad_network"]) for row in included_runs
    )
    returns_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    units_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in returned_rows:
        returns_by_category[(row["signature_group"], row["broad_network"])].append(row)
    for row in category_rows:
        units_by_category[(row["signature_group"], row["broad_network"])].append(row)
    category_summary: list[dict[str, Any]] = []
    for group in groups:
        for network in networks:
            key = (group, network)
            returns = returns_by_category.get(key, [])
            units = units_by_category.get(key, [])
            q_values = [float(row["returned_run_q_acat_score"]) for row in units]
            category_summary.append(
                {
                    "signature_group": group,
                    "sex": labels[group]["sex"],
                    "apoe_group": labels[group]["apoe_group"],
                    "broad_network": network,
                    "included_call_count": calls_by_category[key],
                    "stock_returned_row_count": len(returns),
                    "all_class_returned_gene_count": len({row["current_symbol"] for row in returns}),
                    "mt_returned_gene_count": len(
                        {row["current_symbol"] for row in returns if row["is_core_mito"]}
                    ),
                    "non_mt_returned_gene_count": len(
                        {row["current_symbol"] for row in returns if not row["is_core_mito"]}
                    ),
                    "singleton_gene_unit_count": sum(
                        int(row["returned_call_count"]) == 1 for row in units
                    ),
                    "recurrent_gene_unit_count": sum(
                        int(row["returned_call_count"]) >= 2 for row in units
                    ),
                    "minimum_requested_final_q": min(q_values) if q_values else None,
                }
            )

    acat_fixture = acat_combine([0.5746569, 0.7090122, 0.7965851, 0.1149619])
    add_check(
        checks,
        "acat_reference_fixture",
        acat_fixture,
        0.4768092003,
        abs(acat_fixture - 0.4768092003) <= 5e-10,
        "ACAT must reproduce the repository reference fixture",
    )
    add_check(
        checks,
        "global_gene_count",
        len(global_rows),
        615,
        len(global_rows) == 615,
        "Literal global output must contain every distinct returned gene",
    )
    add_check(
        checks,
        "global_singleton_count",
        sum(row["returned_call_count"] == 1 for row in global_rows),
        363,
        sum(row["returned_call_count"] == 1 for row in global_rows) == 363,
        "Singleton genes must pass their one within-call q through",
    )
    add_check(
        checks,
        "global_recurrent_count",
        sum(row["returned_call_count"] >= 2 for row in global_rows),
        252,
        sum(row["returned_call_count"] >= 2 for row in global_rows) == 252,
        "Recurrent genes must use ACAT",
    )
    add_check(
        checks,
        "category_gene_unit_count",
        len(category_rows),
        1298,
        len(category_rows) == 1298,
        "Category output must contain every returned gene-category unit",
    )
    add_check(
        checks,
        "category_singleton_count",
        sum(row["returned_call_count"] == 1 for row in category_rows),
        892,
        sum(row["returned_call_count"] == 1 for row in category_rows) == 892,
        "Category singleton units must pass through their q",
    )
    add_check(
        checks,
        "category_recurrent_count",
        sum(row["returned_call_count"] >= 2 for row in category_rows),
        406,
        sum(row["returned_call_count"] >= 2 for row in category_rows) == 406,
        "Category recurrent units must use ACAT",
    )
    singleton_mismatches = sum(
        row["returned_call_count"] == 1
        and abs(
            float(row["returned_run_q_acat_score"])
            - float(row["minimum_returned_within_call_q"])
        )
        > 1e-15
        for row in [*global_rows, *category_rows]
    )
    recurrent_mismatches = sum(
        row["returned_call_count"] >= 2
        and (
            row["acat_of_returned_within_call_q"] is None
            or abs(
                float(row["returned_run_q_acat_score"])
                - float(row["acat_of_returned_within_call_q"])
            )
            > 1e-15
        )
        for row in [*global_rows, *category_rows]
    )
    add_check(
        checks,
        "singleton_passthrough",
        singleton_mismatches,
        0,
        singleton_mismatches == 0,
        "Every singleton final value must equal its one returned q",
    )
    add_check(
        checks,
        "recurrent_acat_assignment",
        recurrent_mismatches,
        0,
        recurrent_mismatches == 0,
        "Every recurrent final value must equal its returned-q ACAT value",
    )
    invalid_final = sum(
        not 0 <= float(row["returned_run_q_acat_score"]) <= 1
        for row in [*global_rows, *category_rows]
    )
    add_check(
        checks,
        "final_value_bounds",
        invalid_final,
        0,
        invalid_final == 0,
        "Every requested final value must lie in [0, 1]",
    )
    add_check(
        checks,
        "structural_category_count",
        len(category_summary),
        42,
        len(category_summary) == 42,
        "Preserve all six-by-seven Phase 20 structural categories",
    )

    global_rows.sort(key=lambda row: int(row["rank"]))
    category_rows.sort(
        key=lambda row: (
            groups.index(row["signature_group"]),
            networks.index(row["broad_network"]),
            int(row["rank"]),
        )
    )

    global_path = output_dir / "simple_global_gene_aggregates.tsv"
    category_path = output_dir / "simple_category_gene_aggregates.tsv"
    detail_path = output_dir / "simple_returned_call_rows.tsv.gz"
    category_summary_path = output_dir / "simple_category_summary.tsv"
    checks_path = output_dir / "simple_checks.tsv"
    status_path = output_dir / "simple_status.tsv"
    artifacts_path = output_dir / "simple_artifacts.tsv"
    methods_path = output_dir / "README.md"

    output_counts = {
        global_path.name: write_tsv(
            global_path,
            global_rows,
            AGGREGATE_FIELDS,
            f"{SCHEMA_ROOT}_global_gene_aggregates_v1",
        ),
        category_path.name: write_tsv(
            category_path,
            category_rows,
            AGGREGATE_FIELDS,
            f"{SCHEMA_ROOT}_category_gene_aggregates_v1",
        ),
        detail_path.name: write_tsv(
            detail_path,
            detail_rows,
            DETAIL_FIELDS,
            f"{SCHEMA_ROOT}_returned_call_rows_v1",
        ),
        category_summary_path.name: write_tsv(
            category_summary_path,
            category_summary,
            CATEGORY_FIELDS,
            f"{SCHEMA_ROOT}_category_summary_v1",
        ),
    }

    failed_checks = [row for row in checks if not row["passed"]]
    output_counts[checks_path.name] = write_tsv(
        checks_path,
        checks,
        CHECK_FIELDS,
        f"{SCHEMA_ROOT}_checks_v1",
    )
    status_row = {
        "analysis_id": ANALYSIS_ID,
        "execution_status": "complete" if not failed_checks else "failed_checks",
        "interpretation_status": "exploratory_post_selected_not_fdr_controlled",
        "git_revision": git_revision(root),
        "included_run_count": len(included_runs),
        "stock_returned_row_count": len(returned_rows),
        "unique_returned_gene_count": len(global_rows),
        "global_singleton_gene_count": sum(
            row["returned_call_count"] == 1 for row in global_rows
        ),
        "global_recurrent_gene_count": sum(
            row["returned_call_count"] >= 2 for row in global_rows
        ),
        "global_aggregate_row_count": len(global_rows),
        "category_gene_unit_count": len(category_rows),
        "category_singleton_unit_count": sum(
            row["returned_call_count"] == 1 for row in category_rows
        ),
        "category_recurrent_unit_count": sum(
            row["returned_call_count"] >= 2 for row in category_rows
        ),
        "structural_category_count": len(category_summary),
        "analyzable_category_count": sum(row["included_call_count"] > 0 for row in category_summary),
        "failed_check_count": len(failed_checks),
        "output_directory": str(output_dir),
    }
    output_counts[status_path.name] = write_tsv(
        status_path,
        [status_row],
        STATUS_FIELDS,
        f"{SCHEMA_ROOT}_status_v1",
    )

    methods = f"""# Simple returned-only Phase 20 KDA aggregation

This directory implements the requested exploratory rule over the frozen
Phase 20 set of **{len(included_runs)} KDA calls**:

1. Retain only rows returned as significant by stock `call_key_drivers()`.
2. Use the returned within-call adjusted P value (`adjusted_p_value`) as the
   input q value.
3. If a gene has one returned row in the aggregation scope, copy that q value
   to `returned_run_q_acat_score` unchanged.
4. If a gene has two or more returned rows, equal-weight ACAT-combine those
   returned q values and store the result as `returned_run_q_acat_score`.
5. Do not apply another across-gene BH adjustment, because doing so would
   change singleton q values and violate step 3.

Two views are provided:

- `simple_global_gene_aggregates.tsv`: one row per gene across all included
  calls; this is the literal interpretation of "multiple calls".
- `simple_category_gene_aggregates.tsv`: one row per
  `signature_group + broad_network + gene`, preserving the Phase 20
  sex/APOE-by-broad-cell categories.

`simple_returned_call_rows.tsv.gz` contains the exact {len(returned_rows):,}
stock returned rows and connects every row to both aggregate views.
`simple_category_summary.tsv` preserves all 42 structural categories.

## Interpretation warning

`returned_run_q_acat_score` is the canonical post-selected exploratory value.
`requested_final_q` is an identical alias included to match the requested
terminology. Neither is a formally FDR-controlled cross-call q value: the input rows were selected
for within-call significance, ACAT is being applied to adjusted values rather
than the complete raw-P family, and no final across-gene multiplicity
correction is performed. Use it for comparison and ranking, not confirmatory
error-rate claims.
"""
    temporary_methods = methods_path.parent / f".{methods_path.name}.tmp.{os.getpid()}"
    temporary_methods.write_text(methods)
    temporary_methods.replace(methods_path)
    output_counts[methods_path.name] = 1

    artifact_rows: list[dict[str, Any]] = []
    for role, path in (
        ("script", Path(__file__).resolve()),
        ("input_config", config_path),
        ("input_run_manifest", manifest_path),
        ("input_stock_results", stock_path),
        ("input_annotation", annotation_path),
        ("output_global_aggregates", global_path),
        ("output_category_aggregates", category_path),
        ("output_returned_rows", detail_path),
        ("output_category_summary", category_summary_path),
        ("output_checks", checks_path),
        ("output_status", status_path),
        ("output_methods", methods_path),
    ):
        artifact_rows.append(
            {
                "role": role,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    output_counts[artifacts_path.name] = write_tsv(
        artifacts_path,
        artifact_rows,
        ARTIFACT_FIELDS,
        f"{SCHEMA_ROOT}_artifacts_v1",
    )

    for name, count in sorted(output_counts.items()):
        print(f"{name}\t{count}")
    if failed_checks:
        fail(f"Simple aggregation failed checks: {[row['check_id'] for row in failed_checks]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
