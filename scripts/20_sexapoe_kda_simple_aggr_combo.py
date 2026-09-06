#!/usr/bin/env python3
"""Build direction-combined Phase 20 KDA simple aggregates.

The Phase 12 primary ``AD_both_mito`` calls already contain the deduplicated
union of each contrast's up- and downregulated mitochondrial DEG queries. This
script validates and reuses those calls, applies configurable cell and query
floors, then aggregates returned drivers within sex/APOE-by-broad-cell-type
categories using singleton pass-through or equal-weight ACAT.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import math
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml
from scipy.stats import cauchy


NA_TEXT = "NA"
TRUE_VALUES = {"TRUE", "T", "1", "YES"}
SCHEMA_ROOT = "phase20_sexapoe_kda_simple_aggr_combo_v1"


def fail(message: str) -> None:
    raise RuntimeError(message)


def is_true(value: Any) -> bool:
    return str(value).upper() in TRUE_VALUES


def as_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Invalid integer for {label}: {value!r}") from error


def as_float(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Invalid number for {label}: {value!r}") from error
    if not math.isfinite(result):
        fail(f"Non-finite number for {label}: {value!r}")
    return result


def display_value(value: Any) -> Any:
    if value is None or value == "":
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
        names = ["schema_version", *fields]
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


def acat_statistic(value: float) -> float:
    if value < 1e-15:
        return 1.0 / (value * math.pi)
    return math.tan((0.5 - value) * math.pi)


def acat_combine(values: Sequence[float], tolerance: float = 1e-300) -> float:
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
        replacement = maximum / 2.0 + 0.5
        work = [replacement if value == 1 else value for value in work]
    statistic = statistics.fmean(acat_statistic(value) for value in work)
    return float(cauchy.sf(statistic))


def require_fields(rows: Sequence[dict[str, str]], fields: Sequence[str], label: str) -> None:
    if not rows:
        fail(f"{label} is empty")
    missing = [field for field in fields if field not in rows[0]]
    if missing:
        fail(f"{label} is missing fields: {missing}")


def load_annotations(path: Path) -> dict[str, dict[str, Any]]:
    annotations: dict[str, dict[str, Any]] = {}
    for row in iter_tsv(path):
        current = row.get("symbol_hgnc_current", "")
        symbol = current if current and current != NA_TEXT else row.get("symbol_original", "")
        if not symbol or symbol == NA_TEXT:
            continue
        annotation = {
            "is_core_mito": is_true(row.get("is_mitocarta3")),
            "mito_tier": row.get("mito_tier") or NA_TEXT,
            "genome_origin": row.get("genome_origin") or NA_TEXT,
        }
        previous = annotations.get(symbol)
        if previous is None:
            annotations[symbol] = annotation
        elif previous != annotation:
            fail(f"Conflicting mitochondrial annotation for {symbol}")
    return annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/phase20_sexapoe_kda_simple_aggr_combo.yml",
    )
    parser.add_argument("--minimum-cells-per-deg-arm", type=int)
    parser.add_argument("--minimum-effective-query-genes", type=int)
    parser.add_argument("--output")
    return parser.parse_args()


RUN_MANIFEST_FIELDS = """
contrast_index kda_run_id source_contrast_id fine_cell_type broad_cell_type
signature_group sex apoe_group query_mode cells_ad cells_nci donors_ad donors_nci
phase08_terminal_status minimum_cells_per_deg_arm passes_cell_floor
candidate_query_genes effective_query_genes minimum_effective_query_genes
passes_query_floor phase12_eligibility_status phase12_terminal_status
phase12_returned_driver_count included_at_thresholds exclusion_reason
""".split()

QUERY_FIELDS = """
kda_run_id source_contrast_id fine_cell_type broad_cell_type signature_group sex
apoe_group gene in_upregulated_query in_downregulated_query source_directions
effective_member exclusion_reason included_at_thresholds
""".split()

RETURNED_FIELDS = """
kda_run_id source_contrast_id fine_cell_type broad_cell_type signature_group sex
apoe_group query_mode key_driver is_core_mito mito_tier genome_origin best_layer
overlap_count neighborhood_size non_neighborhood_size signature_size
fold_enrichment log_p_value raw_p_value within_call_adjusted_p_value is_signature
is_root_node global_key_driver overlap_items
""".split()

AGGREGATE_FIELDS = """
signature_group sex apoe_group broad_cell_type key_driver is_core_mito mito_tier
genome_origin contributing_call_count contributing_fine_cell_type_count
contributing_fine_cell_types contributing_run_ids
minimum_within_call_adjusted_p_value median_within_call_adjusted_p_value
maximum_within_call_adjusted_p_value simple_aggregation_score aggregation_method
rank
""".split()

CATEGORY_FIELDS = """
signature_group sex apoe_group broad_cell_type structural_contrast_count
source_deg_valid_count cell_floor_pass_count query_floor_pass_count
included_kda_call_count calls_with_returned_drivers returned_call_row_count
key_driver_count singleton_key_driver_count recurrent_key_driver_count
minimum_simple_aggregation_score category_status
""".split()


def build_aggregate(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        fail("Cannot aggregate an empty group")
    genes = {row["key_driver"] for row in rows}
    categories = {(row["signature_group"], row["broad_cell_type"]) for row in rows}
    if len(genes) != 1 or len(categories) != 1:
        fail("Aggregation group contains multiple genes or categories")
    q_values = [float(row["within_call_adjusted_p_value"]) for row in rows]
    run_ids = [str(row["kda_run_id"]) for row in rows]
    if len(run_ids) != len(set(run_ids)):
        fail(f"Duplicate contributing call for {next(iter(genes))}")
    if len(q_values) == 1:
        score = q_values[0]
        method = "singleton_within_call_adjusted_p_passthrough"
    else:
        score = acat_combine(q_values)
        method = "equal_weight_acat"
    first = rows[0]
    if any(row["is_core_mito"] != first["is_core_mito"] for row in rows):
        fail(f"Mitochondrial annotation drift for {first['key_driver']}")
    fine_types = sorted({str(row["fine_cell_type"]) for row in rows})
    return {
        "signature_group": first["signature_group"],
        "sex": first["sex"],
        "apoe_group": first["apoe_group"],
        "broad_cell_type": first["broad_cell_type"],
        "key_driver": first["key_driver"],
        "is_core_mito": first["is_core_mito"],
        "mito_tier": first["mito_tier"],
        "genome_origin": first["genome_origin"],
        "contributing_call_count": len(rows),
        "contributing_fine_cell_type_count": len(fine_types),
        "contributing_fine_cell_types": "|".join(fine_types),
        "contributing_run_ids": "|".join(sorted(run_ids)),
        "minimum_within_call_adjusted_p_value": min(q_values),
        "median_within_call_adjusted_p_value": statistics.median(q_values),
        "maximum_within_call_adjusted_p_value": max(q_values),
        "simple_aggregation_score": score,
        "aggregation_method": method,
        "rank": None,
    }


def run() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = project_path(root, args.config)
    with config_path.open() as handle:
        config = yaml.safe_load(handle)

    paths = config["paths"]
    minimum_cells = (
        args.minimum_cells_per_deg_arm
        if args.minimum_cells_per_deg_arm is not None
        else as_int(config["thresholds"]["minimum_cells_per_deg_arm"], "cell floor")
    )
    minimum_query = (
        args.minimum_effective_query_genes
        if args.minimum_effective_query_genes is not None
        else as_int(
            config["thresholds"]["minimum_effective_query_genes"], "query floor"
        )
    )
    if minimum_cells < 3:
        fail("minimum_cells_per_deg_arm below 3 requires a Phase 08 rerun")
    if minimum_query < 3:
        fail("minimum_effective_query_genes below 3 requires new KDA calls")

    output_dir = project_path(root, args.output or paths["output_directory"])
    phase12_manifest_path = project_path(root, paths["phase12_run_manifest"])
    phase12_query_path = project_path(root, paths["phase12_query_members"])
    phase12_results_path = project_path(root, paths["phase12_results"])
    annotation_path = project_path(root, paths["gene_annotation"])

    group_rows = config["scope"]["groups"]
    groups = [row["group_id"] for row in group_rows]
    labels = {row["group_id"]: row for row in group_rows}
    broad_types = list(config["scope"]["broad_cell_types"])
    expected = config["expected_source"]

    phase08_pattern = paths["phase08_status_glob"]
    phase08_paths = sorted(root.glob(phase08_pattern))
    if not phase08_paths:
        fail(f"No Phase 08 status files match: {phase08_pattern}")
    phase08_rows: list[dict[str, str]] = []
    for path in phase08_paths:
        phase08_rows.extend(read_tsv(path))
    require_fields(
        phase08_rows,
        [
            "contrast_id",
            "cell_type_high_resolution",
            "sex",
            "apoe_group",
            "terminal_status",
            "cells_ad",
            "cells_nci",
            "donors_ad",
            "donors_nci",
        ],
        "Phase 08 contrast status",
    )
    phase08_lookup = {row["contrast_id"]: row for row in phase08_rows}
    if len(phase08_lookup) != len(phase08_rows):
        fail("Duplicate Phase 08 contrast_id")

    phase12_rows = read_tsv(phase12_manifest_path)
    require_fields(
        phase12_rows,
        [
            "kda_run_id",
            "analysis_tier",
            "fine_cell_type",
            "broad_network",
            "signature_group",
            "source_contrast_ids",
            "source_terminal_statuses",
            "signature_direction",
            "candidate_query_genes",
            "effective_query_genes",
            "eligibility_status",
            "terminal_status",
            "significant_key_drivers",
        ],
        "Phase 12 run manifest",
    )
    primary = [row for row in phase12_rows if row["analysis_tier"] == "primary"]
    direction_lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in primary:
        key = (row["fine_cell_type"], row["signature_group"], row["signature_direction"])
        if key in direction_lookup:
            fail(f"Duplicate primary Phase 12 slot: {key}")
        direction_lookup[key] = row
    combined = [row for row in primary if row["signature_direction"] == "AD_both_mito"]
    combined_ids = {row["kda_run_id"] for row in combined}
    if len(combined_ids) != len(combined):
        fail("Duplicate Phase 12 combined kda_run_id")

    expected_structural = as_int(expected["structural_contrasts"], "expected contrasts")
    if len(combined) != expected_structural:
        fail(f"Expected {expected_structural} combined slots; observed {len(combined)}")
    if len(phase08_lookup) != expected_structural:
        fail(f"Expected {expected_structural} Phase 08 rows; observed {len(phase08_lookup)}")
    if set(row["signature_group"] for row in combined) != set(groups):
        fail("Phase 12 combined signature groups do not match config")
    if set(row["broad_network"] for row in combined) != set(broad_types):
        fail("Phase 12 combined broad-cell networks do not match config")

    annotations = load_annotations(annotation_path)
    result_rows_by_run: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_result_keys: set[tuple[str, str]] = set()
    for row in iter_tsv(phase12_results_path):
        if row["kda_run_id"] not in combined_ids:
            continue
        key = (row["kda_run_id"], row["key_driver"])
        if key in seen_result_keys:
            fail(f"Duplicate Phase 12 returned run/gene key: {key}")
        seen_result_keys.add(key)
        if row["signature_direction"] != "AD_both_mito":
            fail(f"Unexpected result direction for {row['kda_run_id']}")
        q_value = as_float(row["adjusted_p_value"], f"adjusted P for {key}")
        if q_value <= 0 or q_value > 0.05 + 1e-12:
            fail(f"Invalid returned adjusted P for {key}: {q_value}")
        result_rows_by_run[row["kda_run_id"]].append(row)

    raw_returned_count = sum(len(rows) for rows in result_rows_by_run.values())
    expected_returned = as_int(expected["phase12_combined_returned_rows"], "returned rows")
    if raw_returned_count != expected_returned:
        fail(f"Expected {expected_returned} combined returned rows; observed {raw_returned_count}")
    completed_count = sum(row["terminal_status"].startswith("completed") for row in combined)
    significant_count = sum(row["terminal_status"] == "completed_significant" for row in combined)
    if completed_count != as_int(expected["phase12_combined_completed_calls"], "completed calls"):
        fail(f"Unexpected combined completed-call count: {completed_count}")
    if significant_count != as_int(expected["phase12_combined_significant_calls"], "significant calls"):
        fail(f"Unexpected combined significant-call count: {significant_count}")

    manifest_rows: list[dict[str, Any]] = []
    manifest_by_run: dict[str, dict[str, Any]] = {}
    for source in combined:
        group = source["signature_group"]
        if group not in labels:
            fail(f"Unknown signature group: {group}")
        contrast_id = source["source_contrast_ids"]
        phase08 = phase08_lookup.get(contrast_id)
        if phase08 is None:
            fail(f"Missing Phase 08 status for {contrast_id}")
        if phase08["cell_type_high_resolution"] != source["fine_cell_type"]:
            fail(f"Fine-cell metadata mismatch for {contrast_id}")
        if (
            phase08["sex"] != labels[group]["sex"]
            or phase08["apoe_group"] != labels[group]["apoe_group"]
        ):
            fail(f"Sex/APOE metadata mismatch for {contrast_id}")
        if phase08["terminal_status"] != source["source_terminal_statuses"]:
            fail(f"Phase 08/12 terminal-status mismatch for {contrast_id}")

        cells_ad = as_int(phase08["cells_ad"], f"AD cells for {contrast_id}")
        cells_nci = as_int(phase08["cells_nci"], f"NCI cells for {contrast_id}")
        donors_ad = as_int(phase08["donors_ad"], f"AD donors for {contrast_id}")
        donors_nci = as_int(phase08["donors_nci"], f"NCI donors for {contrast_id}")
        candidate_size = as_int(source["candidate_query_genes"], f"candidate size for {contrast_id}")
        effective_size = as_int(source["effective_query_genes"], f"effective size for {contrast_id}")
        returned_count = len(result_rows_by_run[source["kda_run_id"]])
        if returned_count != as_int(
            source["significant_key_drivers"], f"returned drivers for {contrast_id}"
        ):
            fail(f"Manifest/result returned-driver mismatch for {source['kda_run_id']}")

        source_valid = phase08["terminal_status"] == "validated_complete"
        passes_cell = cells_ad >= minimum_cells and cells_nci >= minimum_cells
        passes_query = effective_size >= minimum_query
        phase12_completed = source["terminal_status"].startswith("completed")
        included = source_valid and passes_cell and passes_query and phase12_completed
        if included:
            reason = ""
        elif not passes_cell:
            reason = "minimum_cells_per_deg_arm_not_met"
        elif not source_valid:
            reason = "source_deg_not_validated"
        elif not passes_query:
            reason = "minimum_effective_query_genes_not_met"
        else:
            reason = "validated_phase12_call_not_available"

        output = {
            "kda_run_id": source["kda_run_id"],
            "source_contrast_id": contrast_id,
            "fine_cell_type": source["fine_cell_type"],
            "broad_cell_type": source["broad_network"],
            "signature_group": group,
            "sex": labels[group]["sex"],
            "apoe_group": labels[group]["apoe_group"],
            "query_mode": "AD_both_mito",
            "cells_ad": cells_ad,
            "cells_nci": cells_nci,
            "donors_ad": donors_ad,
            "donors_nci": donors_nci,
            "phase08_terminal_status": phase08["terminal_status"],
            "minimum_cells_per_deg_arm": minimum_cells,
            "passes_cell_floor": passes_cell,
            "candidate_query_genes": candidate_size,
            "effective_query_genes": effective_size,
            "minimum_effective_query_genes": minimum_query,
            "passes_query_floor": passes_query,
            "phase12_eligibility_status": source["eligibility_status"],
            "phase12_terminal_status": source["terminal_status"],
            "phase12_returned_driver_count": returned_count,
            "included_at_thresholds": included,
            "exclusion_reason": reason,
        }
        manifest_rows.append(output)
        manifest_by_run[source["kda_run_id"]] = output

    valid_count = sum(row["phase08_terminal_status"] == "validated_complete" for row in manifest_rows)
    if valid_count != as_int(expected["phase08_valid_contrasts"], "valid Phase 08 contrasts"):
        fail(f"Unexpected valid Phase 08 contrast count: {valid_count}")

    member_rows_by_run: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    primary_ids = {row["kda_run_id"] for row in primary}
    for row in iter_tsv(phase12_query_path):
        run_id = row["kda_run_id"]
        if run_id not in primary_ids:
            continue
        if row["gene"] in member_rows_by_run[run_id]:
            fail(f"Duplicate Phase 12 query member: {(run_id, row['gene'])}")
        member_rows_by_run[run_id][row["gene"]] = row

    query_rows: list[dict[str, Any]] = []
    for source in combined:
        fine = source["fine_cell_type"]
        group = source["signature_group"]
        up = direction_lookup.get((fine, group, "AD_up_mito"))
        down = direction_lookup.get((fine, group, "AD_down_mito"))
        if up is None or down is None:
            fail(f"Missing up/down source slot for {(fine, group)}")
        if any(
            item["source_contrast_ids"] != source["source_contrast_ids"]
            or item["broad_network"] != source["broad_network"]
            for item in (up, down)
        ):
            fail(f"Up/down/combined metadata mismatch for {(fine, group)}")
        up_members = member_rows_by_run[up["kda_run_id"]]
        down_members = member_rows_by_run[down["kda_run_id"]]
        both_members = member_rows_by_run[source["kda_run_id"]]
        if set(both_members) != set(up_members) | set(down_members):
            fail(f"Combined query is not the up/down union for {(fine, group)}")
        if len(both_members) != as_int(source["candidate_query_genes"], "candidate count"):
            fail(f"Combined candidate-query count mismatch for {(fine, group)}")
        both_effective = {gene for gene, row in both_members.items() if is_true(row["effective_member"])}
        up_effective = {gene for gene, row in up_members.items() if is_true(row["effective_member"])}
        down_effective = {gene for gene, row in down_members.items() if is_true(row["effective_member"])}
        if both_effective != up_effective | down_effective:
            fail(f"Combined effective query is not the up/down union for {(fine, group)}")
        if len(both_effective) != as_int(source["effective_query_genes"], "effective count"):
            fail(f"Combined effective-query count mismatch for {(fine, group)}")
        manifest = manifest_by_run[source["kda_run_id"]]
        for gene, member in sorted(both_members.items()):
            in_up = gene in up_members
            in_down = gene in down_members
            directions = "|".join(
                direction
                for direction, present in (
                    ("AD_up_mito", in_up),
                    ("AD_down_mito", in_down),
                )
                if present
            )
            query_rows.append(
                {
                    "kda_run_id": source["kda_run_id"],
                    "source_contrast_id": source["source_contrast_ids"],
                    "fine_cell_type": fine,
                    "broad_cell_type": source["broad_network"],
                    "signature_group": group,
                    "sex": labels[group]["sex"],
                    "apoe_group": labels[group]["apoe_group"],
                    "gene": gene,
                    "in_upregulated_query": in_up,
                    "in_downregulated_query": in_down,
                    "source_directions": directions,
                    "effective_member": is_true(member["effective_member"]),
                    "exclusion_reason": member.get("exclusion_reason", ""),
                    "included_at_thresholds": manifest["included_at_thresholds"],
                }
            )

    included_ids = {
        row["kda_run_id"] for row in manifest_rows if row["included_at_thresholds"]
    }
    returned_rows: list[dict[str, Any]] = []
    missing_annotations: set[str] = set()
    for source in combined:
        run_id = source["kda_run_id"]
        if run_id not in included_ids:
            continue
        manifest = manifest_by_run[run_id]
        for row in result_rows_by_run[run_id]:
            if any(
                row[field] != source[source_field]
                for field, source_field in (
                    ("fine_cell_type", "fine_cell_type"),
                    ("broad_network", "broad_network"),
                    ("signature_group", "signature_group"),
                )
            ):
                fail(f"Phase 12 result metadata mismatch for {run_id}")
            gene = row["key_driver"]
            annotation = annotations.get(gene)
            if annotation is None:
                missing_annotations.add(gene)
                annotation = {
                    "is_core_mito": False,
                    "mito_tier": "annotation_missing",
                    "genome_origin": NA_TEXT,
                }
            log_p = as_float(row["log_p_value"], f"log P for {(run_id, gene)}")
            returned_rows.append(
                {
                    "kda_run_id": run_id,
                    "source_contrast_id": manifest["source_contrast_id"],
                    "fine_cell_type": source["fine_cell_type"],
                    "broad_cell_type": source["broad_network"],
                    "signature_group": source["signature_group"],
                    "sex": manifest["sex"],
                    "apoe_group": manifest["apoe_group"],
                    "query_mode": "AD_both_mito",
                    "key_driver": gene,
                    "is_core_mito": annotation["is_core_mito"],
                    "mito_tier": annotation["mito_tier"],
                    "genome_origin": annotation["genome_origin"],
                    "best_layer": as_int(row["best_layer"], "best layer"),
                    "overlap_count": as_int(row["overlap_count"], "overlap count"),
                    "neighborhood_size": as_int(row["neighborhood_size"], "neighborhood size"),
                    "non_neighborhood_size": as_int(
                        row["non_neighborhood_size"], "non-neighborhood size"
                    ),
                    "signature_size": as_int(row["signature_size"], "signature size"),
                    "fold_enrichment": as_float(row["fold_enrichment"], "fold enrichment"),
                    "log_p_value": log_p,
                    "raw_p_value": math.exp(log_p),
                    "within_call_adjusted_p_value": as_float(
                        row["adjusted_p_value"], "adjusted P"
                    ),
                    "is_signature": is_true(row["is_signature"]),
                    "is_root_node": is_true(row["is_root_node"]),
                    "global_key_driver": is_true(row["global_key_driver"]),
                    "overlap_items": row["overlap_items"],
                }
            )
    if missing_annotations:
        fail(f"Missing annotations for returned drivers: {sorted(missing_annotations)}")

    by_category_gene: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in returned_rows:
        by_category_gene[
            (row["signature_group"], row["broad_cell_type"], row["key_driver"])
        ].append(row)
    aggregate_rows = [build_aggregate(rows) for rows in by_category_gene.values()]
    aggregate_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in aggregate_rows:
        aggregate_by_category[(row["signature_group"], row["broad_cell_type"])].append(row)
    for rows in aggregate_by_category.values():
        rows.sort(key=lambda row: (row["simple_aggregation_score"], row["key_driver"]))
        for rank, row in enumerate(rows, start=1):
            row["rank"] = rank

    slots_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    returns_by_category: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        slots_by_category[(row["signature_group"], row["broad_cell_type"])].append(row)
    for row in returned_rows:
        returns_by_category[(row["signature_group"], row["broad_cell_type"])].append(row)

    category_rows: list[dict[str, Any]] = []
    for group in groups:
        for broad_type in broad_types:
            key = (group, broad_type)
            slots = slots_by_category.get(key, [])
            returns = returns_by_category.get(key, [])
            drivers = aggregate_by_category.get(key, [])
            included_calls = [row for row in slots if row["included_at_thresholds"]]
            if drivers:
                status = "key_drivers_returned"
            elif included_calls:
                status = "eligible_calls_no_key_drivers_returned"
            else:
                status = "no_eligible_kda_calls"
            category_rows.append(
                {
                    "signature_group": group,
                    "sex": labels[group]["sex"],
                    "apoe_group": labels[group]["apoe_group"],
                    "broad_cell_type": broad_type,
                    "structural_contrast_count": len(slots),
                    "source_deg_valid_count": sum(
                        row["phase08_terminal_status"] == "validated_complete" for row in slots
                    ),
                    "cell_floor_pass_count": sum(row["passes_cell_floor"] for row in slots),
                    "query_floor_pass_count": sum(row["passes_query_floor"] for row in slots),
                    "included_kda_call_count": len(included_calls),
                    "calls_with_returned_drivers": sum(
                        row["phase12_returned_driver_count"] > 0 for row in included_calls
                    ),
                    "returned_call_row_count": len(returns),
                    "key_driver_count": len(drivers),
                    "singleton_key_driver_count": sum(
                        row["contributing_call_count"] == 1 for row in drivers
                    ),
                    "recurrent_key_driver_count": sum(
                        row["contributing_call_count"] >= 2 for row in drivers
                    ),
                    "minimum_simple_aggregation_score": min(
                        (row["simple_aggregation_score"] for row in drivers), default=None
                    ),
                    "category_status": status,
                }
            )

    expected_categories = as_int(expected["structural_categories"], "categories")
    if len(category_rows) != expected_categories:
        fail(f"Expected {expected_categories} structural categories; observed {len(category_rows)}")
    if sum(row["structural_contrast_count"] for row in category_rows) != len(manifest_rows):
        fail("Structural contrasts are not conserved across category summary")
    if sum(row["returned_call_row_count"] for row in category_rows) != len(returned_rows):
        fail("Returned rows are not conserved across category summary")
    if sum(row["key_driver_count"] for row in category_rows) != len(aggregate_rows):
        fail("Aggregated drivers are not conserved across category summary")
    if any(row["rank"] is None for row in aggregate_rows):
        fail("An aggregate row is missing its within-category rank")
    for key, rows in aggregate_by_category.items():
        ranks = sorted(int(row["rank"]) for row in rows)
        if ranks != list(range(1, len(rows) + 1)):
            fail(f"Non-unique or incomplete ranks for category {key}")
    fixture = acat_combine([0.5746569, 0.7090122, 0.7965851, 0.1149619])
    if abs(fixture - 0.4768092003) > 5e-10:
        fail("ACAT implementation failed the repository reference fixture")

    group_index = {group: index for index, group in enumerate(groups)}
    broad_index = {name: index for index, name in enumerate(broad_types)}
    manifest_rows.sort(
        key=lambda row: (
            group_index[row["signature_group"]],
            broad_index[row["broad_cell_type"]],
            row["fine_cell_type"],
        )
    )
    for index, row in enumerate(manifest_rows, start=1):
        row["contrast_index"] = index
    run_order = {row["kda_run_id"]: row["contrast_index"] for row in manifest_rows}
    query_rows.sort(key=lambda row: (run_order[row["kda_run_id"]], row["gene"]))
    returned_rows.sort(
        key=lambda row: (
            group_index[row["signature_group"]],
            broad_index[row["broad_cell_type"]],
            row["fine_cell_type"],
            row["key_driver"],
        )
    )
    aggregate_rows.sort(
        key=lambda row: (
            group_index[row["signature_group"]],
            broad_index[row["broad_cell_type"]],
            int(row["rank"]),
        )
    )

    outputs = (
        (
            output_dir / "combo_run_manifest.tsv",
            manifest_rows,
            RUN_MANIFEST_FIELDS,
            f"{SCHEMA_ROOT}_run_manifest",
        ),
        (
            output_dir / "combo_query_members.tsv.gz",
            query_rows,
            QUERY_FIELDS,
            f"{SCHEMA_ROOT}_query_members",
        ),
        (
            output_dir / "combo_returned_call_rows.tsv.gz",
            returned_rows,
            RETURNED_FIELDS,
            f"{SCHEMA_ROOT}_returned_call_rows",
        ),
        (
            output_dir / "combo_key_drivers_by_category.tsv",
            aggregate_rows,
            AGGREGATE_FIELDS,
            f"{SCHEMA_ROOT}_key_drivers_by_category",
        ),
        (
            output_dir / "combo_category_summary.tsv",
            category_rows,
            CATEGORY_FIELDS,
            f"{SCHEMA_ROOT}_category_summary",
        ),
    )
    counts: dict[str, int] = {}
    for path, rows, fields, schema in outputs:
        counts[path.name] = write_tsv(path, rows, fields, schema)

    print(f"minimum_cells_per_deg_arm\t{minimum_cells}")
    print(f"minimum_effective_query_genes\t{minimum_query}")
    print(f"included_kda_calls\t{len(included_ids)}")
    print(f"calls_with_returned_drivers\t{sum(bool(result_rows_by_run[run_id]) for run_id in included_ids)}")
    for name, count in counts.items():
        print(f"{name}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
