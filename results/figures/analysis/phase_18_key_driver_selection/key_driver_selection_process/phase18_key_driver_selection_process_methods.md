# Phase 18 key-driver selection-process figure methods

The renderer reads `call_key_driver_returns.tsv`, verifies the `phase18_call_key_driver_returns_v1` schema, and validates one unique row per `kda_run_id + key_driver`. It deduplicates repeated aggregate fields to one `broad_network + key_driver + case_id` record and verifies that the fields are constant within that unit.

The displayed gate sequence is calculated from the stored `coverage_fraction >= 0.80`, `conservative_support_count >= 1`, and `aggregate_acat_q <= 0.05` fields. The intersection is required to match `terminal_candidate_status = driver_candidate`. Passing candidates are ordered within each broad-network × driver-class list by ascending `aggregate_acat_q`, ascending `aggregate_acat_p`, and gene symbol. Stored `within_case_rank` and `top5_display` values are checked against this ordering. The renderer does not recompute KDA enrichment, run-level P values, ACAT P values, or BH corrections.

Counts are deterministic properties of the saved table, so uncertainty intervals and significance annotations are not applicable. Okabe–Ito blue and orange identify the two driver classes and are supplemented by explicit class labels and exact counts. PDF and SVG are vector outputs; PNG is exported at 450 DPI.
