#!/usr/bin/env python3
"""Append effective-query-size sensitivity slides to the 2026-09-16 deck."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_phase11_seaad_simple_aggr_part2 as ui  # noqa: E402


DEFAULT_DECK = (
    ROOT / "docs/presentations/09162026/sex_apoe_kda_fine_broad_09162026.pptx"
)
ROS_DIR = ROOT / "results/minerva_production/22_harmonized_broad_kda_combo"
SEA_DIR = ROOT / "results/validation_human/14_harmonized_broad_kda_combo"
AUDIT_DIR = ROOT / "results/presentations/09162026_query_size_sensitivity"

THRESHOLDS = (3, 5, 10, 20, 30)
EXPECTED_INPUT_SLIDES = 27
EXPECTED_OUTPUT_SLIDES = 30
TABLE_TITLE = "Query-size sensitivity — numerical comparison"
EFFECTS_TITLE = "Query-size sensitivity — cohort effects"
INTERPRETATION_TITLE = "Query-size sensitivity — validation interpretation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--audit-dir", type=Path, default=AUDIT_DIR)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def truth(value: str) -> bool:
    return value.strip().upper() in {"TRUE", "T", "1", "YES"}


def as_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def slide_text(slide) -> str:
    return "\n".join(
        shape.text
        for shape in slide.shapes
        if getattr(shape, "has_text_frame", False)
    )


def slide_signature(slide) -> tuple[Any, ...]:
    shapes = tuple(
        (
            shape.name,
            str(shape.shape_type),
            int(shape.left),
            int(shape.top),
            int(shape.width),
            int(shape.height),
            shape.text if getattr(shape, "has_text_frame", False) else "",
        )
        for shape in slide.shapes
    )
    notes_frame = slide.notes_slide.notes_text_frame
    notes = notes_frame.text if notes_frame is not None else ""
    return shapes, notes


def load_cohort_facts(cohort: str, directory: Path) -> dict[int, dict[str, Any]]:
    status = read_tsv(directory / "status.tsv")
    if (
        len(status) != 1
        or status[0]["validation_status"] != "validated_complete"
        or int(status[0]["failed_checks"]) != 0
    ):
        raise RuntimeError(f"{cohort} KDA release is not validated complete")

    manifest = read_tsv(directory / "run_manifest.tsv")
    returns = read_tsv(directory / "significant_returns.tsv")
    if len(manifest) != 42:
        raise RuntimeError(f"Expected 42 {cohort} structural contrasts")
    source_estimable = sum(
        row["source_terminal_status"] == "completed" for row in manifest
    )

    result: dict[int, dict[str, Any]] = {}
    for threshold in THRESHOLDS:
        retained_rows = [
            row
            for row in manifest
            if row["source_terminal_status"] == "completed"
            and as_int(row["effective_query_genes"]) is not None
            and int(row["effective_query_genes"]) >= threshold
        ]
        retained_ids = {row["kda_run_id"] for row in retained_rows}
        if any(not truth(row["execute_kda"]) for row in retained_rows):
            raise RuntimeError(
                f"{cohort} threshold {threshold} retains a run not executed at the current floor"
            )
        retained_returns = [
            row for row in returns if row["kda_run_id"] in retained_ids
        ]
        raw_genes = {row["key_driver"] for row in retained_returns}
        non_mt_rows = [
            row
            for row in retained_returns
            if not row["key_driver"].startswith("MT-")
        ]
        non_mt_genes = {row["key_driver"] for row in non_mt_rows}
        result[threshold] = {
            "source_estimable_contrasts": source_estimable,
            "query_passing_contrasts": len(retained_rows),
            "kda_runs": len(retained_rows),
            "significant_driver_rows": len(retained_returns),
            "unique_raw_driver_genes": len(raw_genes),
            "non_mt_driver_rows": len(non_mt_rows),
            "unique_non_mt_drivers": len(non_mt_genes),
            "retained_strata": "|".join(
                sorted(
                    f"{row['broad_cell_type']} × {row['group_id']}"
                    for row in retained_rows
                )
            ),
        }
    return result


def load_facts() -> dict[str, dict[int, dict[str, Any]]]:
    required = [
        DEFAULT_DECK,
        ROS_DIR / "status.tsv",
        ROS_DIR / "run_manifest.tsv",
        ROS_DIR / "significant_returns.tsv",
        SEA_DIR / "status.tsv",
        SEA_DIR / "run_manifest.tsv",
        SEA_DIR / "significant_returns.tsv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing query-sensitivity input(s): " + ", ".join(missing))

    facts = {
        "rosmap": load_cohort_facts("ROSMAP", ROS_DIR),
        "seaad": load_cohort_facts("SEA-AD", SEA_DIR),
    }
    expected = {
        "rosmap": {
            3: (42, 3, 39, 33),
            5: (42, 2, 30, 24),
            10: (42, 1, 26, 20),
            20: (42, 1, 26, 20),
            30: (42, 1, 26, 20),
        },
        "seaad": {
            3: (28, 5, 24, 18),
            5: (28, 5, 24, 18),
            10: (28, 3, 8, 3),
            20: (28, 3, 8, 3),
            30: (28, 2, 7, 3),
        },
    }
    for cohort, threshold_rows in expected.items():
        for threshold, expected_values in threshold_rows.items():
            observed = facts[cohort][threshold]
            actual = (
                observed["source_estimable_contrasts"],
                observed["kda_runs"],
                observed["significant_driver_rows"],
                observed["unique_non_mt_drivers"],
            )
            if actual != expected_values:
                raise RuntimeError(
                    f"Query sensitivity source drift for {cohort} threshold "
                    f"{threshold}: {actual} != {expected_values}"
                )
    return facts


def append_table(
    prs: Presentation,
    facts: dict[str, dict[int, dict[str, Any]]],
) -> None:
    slide = ui.new_slide(prs)
    ui.add_title_block(
        slide,
        TABLE_TITLE,
        "Minimum effective genes after network mapping; donor minimum held at 3 per disease arm.",
    )
    rows = []
    for cohort_key, cohort_label in (("rosmap", "ROSMAP"), ("seaad", "SEA-AD")):
        for threshold in THRESHOLDS:
            values = facts[cohort_key][threshold]
            rows.append(
                [
                    cohort_label,
                    str(threshold),
                    str(values["source_estimable_contrasts"]),
                    str(values["query_passing_contrasts"]),
                    str(values["kda_runs"]),
                    str(values["significant_driver_rows"]),
                    str(values["unique_non_mt_drivers"]),
                ]
            )
    ui.add_table(
        slide,
        [
            "Cohort",
            "Minimum query genes",
            "Source-estimable contrasts",
            "Query-passing contrasts",
            "KDA runs",
            "Significant KD rows",
            "Unique non-MT KDs",
        ],
        rows,
        0.59,
        1.50,
        [1.20, 1.45, 1.95, 1.90, 1.15, 2.18, 2.32],
        row_h=0.43,
        header_h=0.69,
        font_size=9.2,
    )
    ui.add_text(
        slide,
        "One merged up/down query is used per contrast, so query-passing contrasts and KDA runs are identical here.",
        0.70, 6.66, 11.95, 0.26,
        size=9.4, color=ui.GRAY, bold=True, align=PP_ALIGN.CENTER,
    )
    ui.add_text(
        slide,
        "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
        0.72, 7.08, 11.90, 0.16,
        size=6.7, color=ui.MID, align=PP_ALIGN.CENTER,
    )
    ui.add_notes(
        slide,
        goal="Show how increasing the minimum effective query size changes KDA availability and returned drivers.",
        walkthrough="ROSMAP contracts from three calls and 39 returned rows at three genes to one call and 26 rows at ten or more genes. SEA-AD is unchanged at five genes, contracts to three calls and eight rows at ten or twenty genes, and retains two calls and seven rows at thirty genes.",
        boundary="The donor minimum remains three per disease arm. This exact gating sensitivity drops existing calls; it does not refit DEG models or rerun KDA for retained calls. Significant rows are raw returns, while the final column excludes MT-* genes and deduplicates within cohort.",
        transition="Next, identify the specific calls responsible for the step changes.",
    )


def append_cohort_effects(prs: Presentation) -> None:
    slide = ui.new_slide(prs)
    ui.add_title_block(
        slide,
        EFFECTS_TITLE,
        "Only seven current KDA calls determine the entire threshold response.",
    )

    ui.add_rect(slide, 0.55, 1.43, 5.96, 4.98, color=ui.PALE_RED, outline=ui.VERMILION)
    ui.add_panel_title(slide, "ROSMAP", 0.88, 1.72, 5.30, accent=ui.VERMILION)
    ui.add_bullets(
        slide,
        [
            "Current executed query sizes: 3, 8, and 78 genes.",
            "Minimum 5 removes OPCs × F_e4: 9 driver rows.",
            "Minimum 10 also removes Astrocytes × F_e4: 4 more rows; thresholds 20 and 30 make no further change.",
            "At ≥10, only the low-support Vasculature × M_e2 call remains: 26 rows and 20 unique non-MT drivers.",
        ],
        0.90, 2.35, 5.17,
        size=11.7, accent=ui.VERMILION, line_h=0.75,
    )
    ui.add_rect(slide, 0.90, 5.58, 5.28, 0.54, color=ui.WHITE, outline=ui.VERMILION)
    ui.add_text(
        slide,
        "A higher query floor increases domination by the low-donor vasculature result.",
        1.08, 5.72, 4.92, 0.25,
        size=9.9, color=ui.VERMILION_TEXT, bold=True, align=PP_ALIGN.CENTER,
    )

    ui.add_rect(slide, 6.82, 1.43, 5.96, 4.98, color=ui.PALE_GREEN, outline=ui.TEAL)
    ui.add_panel_title(slide, "SEA-AD", 7.15, 1.72, 5.30, accent=ui.TEAL)
    ui.add_bullets(
        slide,
        [
            "Current executed query sizes: 5, 9, 21, 43, and 45 genes.",
            "Minimum 5 changes nothing.",
            "Minimum 10 removes Microglia × M_e33 and Astrocytes × F_e4: 24 → 8 rows and 18 → 3 unique non-MT drivers.",
            "Minimum 20 changes nothing further; minimum 30 removes Oligodendrocytes × M_e33, whose sole return is MT-*.",
        ],
        7.17, 2.35, 5.17,
        size=11.7, accent=ui.TEAL, line_h=0.75,
    )
    ui.add_rect(slide, 7.17, 5.58, 5.28, 0.54, color=ui.WHITE, outline=ui.TEAL)
    ui.add_text(
        slide,
        "The non-MT driver count reaches 3 at minimum 10 and stays there through 30.",
        7.35, 5.72, 4.92, 0.25,
        size=9.9, color=ui.TEAL_TEXT, bold=True, align=PP_ALIGN.CENTER,
    )
    ui.add_text(
        slide,
        "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
        0.72, 7.08, 11.90, 0.16,
        size=6.7, color=ui.MID, align=PP_ALIGN.CENTER,
    )
    ui.add_notes(
        slide,
        goal="Explain which KDA calls drive the query-threshold sensitivity result.",
        walkthrough="ROSMAP loses the three-gene OPC call at five and the eight-gene astrocyte call at ten, leaving only the 78-gene low-donor vasculature call. SEA-AD is unchanged at five; at ten it loses its five-gene microglia and nine-gene astrocyte calls, and at thirty it additionally loses the 21-gene oligodendrocyte call.",
        boundary="Returned MT-* genes are shown only when explaining raw row changes; they are not treated as eligible key drivers.",
        transition="Finish with the consequences for matched-stratum validation and the least disruptive threshold.",
    )


def append_interpretation(prs: Presentation) -> None:
    slide = ui.new_slide(prs)
    ui.add_title_block(
        slide,
        INTERPRETATION_TITLE,
        "The query floor changes assessability, but it does not create cross-cohort driver validation.",
    )
    ui.add_rect(slide, 0.72, 1.45, 11.90, 3.86, color=ui.WHITE, outline=ui.LIGHT)
    ui.add_text(
        slide, "VALIDATION CONSEQUENCES", 1.05, 1.76, 3.20, 0.26,
        size=10.2, color=ui.BLUE, bold=True,
    )
    ui.add_bullets(
        slide,
        [
            "Cross-cohort non-MT driver overlap remains zero at every tested threshold.",
            "At minimum 3 or 5, Astrocytes × F_e4 remains the only exact shared executed stratum, with no shared drivers.",
            "At minimum 10, 20, or 30, no exact stratum is executed in both cohorts; validation is unavailable rather than negative.",
            "Thresholds ≥10 reduce validation assessability and make ROSMAP increasingly dominated by the low-support Vasculature × M_e2 call.",
        ],
        1.05, 2.20, 10.95,
        size=14.0, accent=ui.BLUE, line_h=0.72,
    )
    ui.add_rect(slide, 0.72, 5.62, 11.90, 0.85, color=ui.PALE_GOLD, outline=ui.GOLD)
    ui.add_text(
        slide,
        "Least disruptive sensitivity reference: minimum 5 effective query genes",
        1.00, 5.84, 11.34, 0.28,
        size=15.0, color=ui.GOLD_TEXT, bold=True, align=PP_ALIGN.CENTER,
    )
    ui.add_text(
        slide,
        "It removes the smallest ROSMAP query while preserving every SEA-AD run and the only matched cross-cohort stratum.",
        1.00, 6.16, 11.34, 0.20,
        size=9.4, color=ui.GOLD_TEXT, align=PP_ALIGN.CENTER,
    )
    ui.add_text(
        slide,
        "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
        0.72, 7.08, 11.90, 0.16,
        size=6.7, color=ui.MID, align=PP_ALIGN.CENTER,
    )
    ui.add_notes(
        slide,
        goal="State the validation impact and identify the least disruptive query-size sensitivity threshold.",
        walkthrough="Non-mitochondrial driver overlap is zero at every threshold. The shared Astrocytes F_e4 stratum remains available at thresholds three and five but disappears from both cohorts at ten. Threshold five is the only stricter floor that preserves all SEA-AD calls and the shared stratum.",
        boundary="Absence of a matched executed stratum at thresholds ten or higher is an unavailable validation comparison, not negative evidence. The five-gene threshold is a sensitivity reference, not a new confirmatory rule.",
        transition="Continue with the next planned sensitivity test.",
    )


def validate_deck(
    path: Path,
    preserved: tuple[tuple[Any, ...], ...],
) -> list[dict[str, Any]]:
    prs = Presentation(str(path))
    checks: list[dict[str, Any]] = []

    def add(check_id: str, observed: Any, expected: Any, passed: bool) -> None:
        checks.append(
            {
                "schema_version": "query_size_sensitivity_deck_checks_v1",
                "check_id": check_id,
                "observed": observed,
                "expected": expected,
                "passed": str(bool(passed)).upper(),
            }
        )

    add(
        "slide_count",
        len(prs.slides),
        EXPECTED_OUTPUT_SLIDES,
        len(prs.slides) == EXPECTED_OUTPUT_SLIDES,
    )
    actual_preserved = tuple(
        slide_signature(slide) for slide in list(prs.slides)[:EXPECTED_INPUT_SLIDES]
    )
    add(
        "existing_slides_preserved",
        actual_preserved == preserved,
        True,
        actual_preserved == preserved,
    )
    all_new_text = "\n".join(
        slide_text(slide) for slide in list(prs.slides)[EXPECTED_INPUT_SLIDES:]
    )
    required = [
        TABLE_TITLE,
        EFFECTS_TITLE,
        INTERPRETATION_TITLE,
        "Minimum query genes",
        "Source-estimable contrasts",
        "Unique non-MT KDs",
        "Current executed query sizes: 3, 8, and 78 genes.",
        "Current executed query sizes: 5, 9, 21, 43, and 45 genes.",
        "Cross-cohort non-MT driver overlap remains zero at every tested threshold.",
        "Least disruptive sensitivity reference: minimum 5 effective query genes",
    ]
    missing = [text for text in required if text not in all_new_text]
    add("required_content_present", missing, [], not missing)
    add(
        "admissible_wording_absent",
        "admissible" in all_new_text.lower(),
        False,
        "admissible" not in all_new_text.lower(),
    )

    notes_ok = 0
    in_bounds = 0
    for slide in list(prs.slides)[EXPECTED_INPUT_SLIDES:]:
        notes_frame = slide.notes_slide.notes_text_frame
        notes = notes_frame.text if notes_frame is not None else ""
        if all(
            marker in notes
            for marker in (
                "Teaching goal:",
                "Walk through:",
                "Scientific boundary:",
                "Transition:",
            )
        ):
            notes_ok += 1
        bounded = all(
            shape.left >= 0
            and shape.top >= 0
            and shape.left + shape.width <= prs.slide_width + 10
            and shape.top + shape.height <= prs.slide_height + 10
            for shape in slide.shapes
        )
        if bounded:
            in_bounds += 1
    add("structured_notes", notes_ok, 3, notes_ok == 3)
    add("new_shapes_in_bounds", in_bounds, 3, in_bounds == 3)

    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
    add("pptx_zip_integrity", bad_member, None, bad_member is None)
    return checks


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    audit_dir = args.audit_dir.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    facts = load_facts()
    source_hash = sha256(input_path)
    prs = Presentation(str(input_path))
    if len(prs.slides) != EXPECTED_INPUT_SLIDES:
        raise RuntimeError(
            f"Expected {EXPECTED_INPUT_SLIDES}-slide input deck, found {len(prs.slides)}; "
            "refusing to append duplicate or misplaced slides"
        )
    if "Donor-threshold sensitivity — key findings" not in slide_text(prs.slides[-1]):
        raise RuntimeError("The expected donor-threshold findings slide is not last")

    preserved = tuple(slide_signature(slide) for slide in prs.slides)
    ui.set_notes_body_template(prs.slides[0].notes_slide.notes_placeholder._element)
    append_table(prs, facts)
    append_cohort_effects(prs)
    append_interpretation(prs)
    if len(prs.slides) != EXPECTED_OUTPUT_SLIDES:
        raise RuntimeError("The three query-size sensitivity slides were not appended")

    old_comments = prs.core_properties.comments or ""
    addition = "Query-size sensitivity added 2026-09-11."
    if addition not in old_comments:
        prs.core_properties.comments = f"{old_comments} {addition}".strip()

    audit_dir.mkdir(parents=True, exist_ok=True)
    backup = audit_dir / f"source_before_append_{source_hash[:12]}.pptx"
    if backup.exists():
        if sha256(backup) != source_hash:
            raise RuntimeError(f"Existing backup hash mismatch: {backup}")
    else:
        shutil.copy2(input_path, backup)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(descriptor)
    temporary = Path(temp_name)
    try:
        prs.save(str(temporary))
        checks = validate_deck(temporary, preserved)
        failed = [row["check_id"] for row in checks if row["passed"] != "TRUE"]
        if failed:
            raise RuntimeError("Deck validation failed: " + ", ".join(failed))
        temporary.replace(output_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    output_hash = sha256(output_path)
    write_tsv(
        audit_dir / "checks.tsv",
        checks,
        ["schema_version", "check_id", "observed", "expected", "passed"],
    )
    sensitivity_rows = []
    for cohort in ("rosmap", "seaad"):
        for threshold in THRESHOLDS:
            sensitivity_rows.append(
                {
                    "schema_version": "broad_kda_query_size_sensitivity_v1",
                    "cohort": cohort,
                    "minimum_effective_query_genes": threshold,
                    **facts[cohort][threshold],
                }
            )
    write_tsv(
        audit_dir / "sensitivity_summary.tsv",
        sensitivity_rows,
        [
            "schema_version",
            "cohort",
            "minimum_effective_query_genes",
            "source_estimable_contrasts",
            "query_passing_contrasts",
            "kda_runs",
            "significant_driver_rows",
            "unique_raw_driver_genes",
            "non_mt_driver_rows",
            "unique_non_mt_drivers",
            "retained_strata",
        ],
    )
    write_tsv(
        audit_dir / "status.tsv",
        [
            {
                "schema_version": "query_size_sensitivity_deck_status_v1",
                "validation_status": "validated_complete",
                "failed_checks": 0,
                "input_sha256": source_hash,
                "output_sha256": output_hash,
                "slide_count": EXPECTED_OUTPUT_SLIDES,
                "backup_path": str(backup.relative_to(ROOT)),
                "output_path": str(output_path.relative_to(ROOT)),
            }
        ],
        [
            "schema_version",
            "validation_status",
            "failed_checks",
            "input_sha256",
            "output_sha256",
            "slide_count",
            "backup_path",
            "output_path",
        ],
    )
    print(f"output={output_path}")
    print(f"slides={EXPECTED_OUTPUT_SLIDES}")
    print(f"sha256={output_hash}")
    print(f"backup={backup}")
    print(f"audit={audit_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
