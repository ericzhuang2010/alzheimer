#!/usr/bin/env python3
"""Build the Phase 18 sex/APOE evidence figure for selected MT drivers."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import plot_phase18_sex_apoe_non_mt as workflow


def configure_mt_workflow() -> None:
    """Configure the shared sex/APOE evidence-map workflow for MT drivers."""
    workflow.SCHEMA = "phase18_sex_apoe_mt_v1"
    workflow.CASE_ID = "mt_driver"
    workflow.LEGACY_CASE_IDS = {
        "case1_core_mito_in_query",
        "case2_core_mito_not_in_query",
    }
    workflow.CASE_DISPLAY_LABEL = "MT"
    workflow.FIGURE_ID = "phase18_sex_apoe_mt"
    workflow.RENDERER_FILE = "visualize_phase18_sex_apoe_mt.R"
    workflow.DEFAULT_OUTPUT = (
        "results/figures/analysis/phase_18_key_driver_selection/sex_apoe_mt"
    )
    workflow.DEFAULT_HEIGHT = 15.0
    workflow.DEFAULT_EVIDENCE_CAP = 16.0
    workflow.NETWORK_Q_AXIS_MAX = 21.0

    workflow.PLOT_FILE = f"{workflow.FIGURE_ID}_plot_data.tsv"
    workflow.ROW_FILE = f"{workflow.FIGURE_ID}_row_annotations.tsv"
    workflow.AUDIT_FILE = f"{workflow.FIGURE_ID}_aggregation_audit.tsv.gz"
    workflow.CAPTION_FILE = f"{workflow.FIGURE_ID}_caption.md"
    workflow.METHODS_FILE = f"{workflow.FIGURE_ID}_methods.md"
    workflow.MANIFEST_FILE = f"{workflow.FIGURE_ID}_manifest.tsv"
    workflow.CHECKS_FILE = f"{workflow.FIGURE_ID}_checks.tsv"
    workflow.ARTIFACTS_FILE = f"{workflow.FIGURE_ID}_artifacts.tsv"
    workflow.STATUS_FILE = f"{workflow.FIGURE_ID}_status.tsv"
    workflow.IMAGE_FILES = [
        f"{workflow.FIGURE_ID}.svg",
        f"{workflow.FIGURE_ID}.pdf",
        f"{workflow.FIGURE_ID}.png",
    ]
    workflow.DECLARED_OUTPUTS = workflow.IMAGE_FILES + [
        workflow.PLOT_FILE,
        workflow.ROW_FILE,
        workflow.AUDIT_FILE,
        workflow.CAPTION_FILE,
        workflow.METHODS_FILE,
        workflow.MANIFEST_FILE,
        workflow.CHECKS_FILE,
        workflow.ARTIFACTS_FILE,
        workflow.STATUS_FILE,
    ]

    workflow.EXPECTED_GENES = {
        "COX4I1",
        "COX6B1",
        "COX7C",
        "MT-ATP6",
        "MT-CO2",
        "MT-CO3",
        "MT-CYB",
        "MT-ND4",
        "MT-ND5",
        "UQCR10",
    }
    workflow.EXPECTED_EXTRA_CONTEXTS = {
        ("Excitatory_neurons", "COX7C"),
        ("Excitatory_neurons", "MT-ATP6"),
        ("Excitatory_neurons", "MT-ND4"),
        ("Inhibitory_neurons", "COX4I1"),
    }
    workflow.EXPECTED_DISPLAYED_CONTEXTS = 26
    workflow.EXPECTED_PASSING_CONTEXTS = 30
    workflow.EXPECTED_CELLS = 360
    workflow.EXPECTED_AUDIT_ROWS = 1_087

    # Functions in the imported workflow record the preparer through module __file__.
    workflow.__file__ = str(Path(__file__).resolve())
    workflow.caption_text = caption_text
    workflow.methods_text = methods_text


def caption_text() -> str:
    return """# Phase 18 MT sex/APOE figure caption

**Sex- and APOE-stratified support for selected MT key drivers.** Rows are the 30 passing gene × broad-network contexts associated with the 10 MT genes retained in the circular display. Filled circle markers identify the 26 circle-displayed contexts; open markers identify four additional passing contexts below the display cap: COX7C, MT-ATP6, and MT-ND4 in excitatory neurons and COX4I1 in inhibitory neurons. Columns partition the included AD-up and AD-down mitochondrial queries by the six primary sex/APOE groups. Filled-dot area is proportional to the fraction of usable queries with conservative support, while fill reports capped −log10 stratum ACAT P. Small open circles denote included strata with zero conservative-support runs, and dashes denote strata with no included query. The right tracks report network-level aggregate q, conservative support over usable runs, coverage, evidence tier, and within-class rank.

The strata are descriptive and are not formal sex, APOE, or interaction tests. Implicit zero-overlap tests enter ACAT as P = 1, while genuinely unavailable tests are omitted, matching the current Phase 18 aggregation. MT means membership in the fixed 1,136-gene core MitoCarta inventory. Bayesian-network key-driver evidence prioritizes candidates without proving experimental causality.
"""


def methods_text(dpi: int, width: float, height: float) -> str:
    return f"""# Methods

The figure was regenerated using the current two-class `call_key_driver_returns.tsv` (`{workflow.INPUT_SCHEMA}`) for MT selection, network-level evidence, ranks, and annotations. The 10 selected genes were the unique symbols with `top5_display = TRUE`. Every passing `driver_candidate` context for those genes was retained, yielding 26 circle-displayed and 30 total gene × broad-network contexts.

Each row was crossed with two mitochondrial-query directions and six primary sex/APOE groups. Included KDA calls were determined from unique run metadata in the canonical table. Because `call_key_driver_returns.tsv` intentionally retains explicit gene-run tests, the validated archived `key_driver_candidate_tests.tsv.gz` supplied the run-level distinction among explicit tests, implicit zero-overlap P = 1 tests, and genuinely unavailable tests. Records from the former query-MT and non-query-MT subclasses were combined because both now belong to the unified MT-driver class. Their gene-run keys were required to be unique. Stratum P values used the canonical `acat_combine()` implementation imported from `scripts/18_export_significant_returns.py`; unavailable tests were omitted. Recombining all stratum inputs was required to reproduce each current network-level aggregate ACAT P. Conservative support counted rows with `conservative_support = TRUE`. Filled-dot area is linear in support fraction, and fill uses cividis capped at −log10(P) = 16. The independent right-side network-q track is capped at 21. Network strips use the Okabe–Ito palette with redundant direct labels and shapes.

No new inferential tests or across-stratum multiple-testing corrections were introduced. SVG and PDF are vector outputs; PNG is {width:g} × {height:g} inches at {dpi} DPI.
"""


def main(argv: Sequence[str] | None = None) -> int:
    configure_mt_workflow()
    return workflow.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
