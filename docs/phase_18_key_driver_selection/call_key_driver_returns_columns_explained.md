# Phase 18 `call_key_driver_returns.tsv`: Column Guide

## Row unit

One row is one explicitly tested candidate gene in one included
`call_key_drivers()` run:

```text
kda_run_id + key_driver
```

The current table contains 95,557 rows from all 161 included calls. It includes
93,916 nonsignificant rows and the original 1,641 significant rows.

The function's internal workflow tests candidates, keeps each gene's best
layer, applies BH correction within the run, and normally returns only rows
with adjusted P value at most 0.05. Phase 18 reconstructs and records the table
before that last significance filter.

## How to identify significance

| Column | Meaning |
|---|---|
| `tested_by_call_key_drivers` | `TRUE` for every row because every row is an explicit candidate test. |
| `significant_by_call_key_drivers` | `TRUE` when the original within-run BH-adjusted P value was at most 0.05. This selects the original 1,641-row subset. |
| `original_run_q` | Reconstructed BH-adjusted P value before Phase 18 self-overlap correction. |
| `final_run_q` | BH-adjusted P value after conditional self-overlap correction. Use this for Phase 18 support assessment. |

The `published_*` columns are populated only when
`significant_by_call_key_drivers = TRUE`, because Phase 12 published only those
rows. Nonsignificant rows use `NA` in the `published_*` columns but have complete
values in the reconstructed `original_*` and `final_*` columns.

## Column groups

### 1. Schema, run, and gene identity

`schema_version`, `kda_run_id`, `fine_cell_type`, `broad_network`,
`signature_group`, `sex`, `apoe_group`, `signature_direction`,
`effective_query_genes`, `effective_background_genes`, `run_terminal_status`,
and `key_driver` identify the test and its biological context.

`run_terminal_status` can be `completed_significant` or
`completed_no_significant`. Both types of completed calls contain tested rows.

### 2. Original Phase 12 publication fields

`published_best_layer`, `published_overlap_count`,
`published_neighborhood_size`, `published_non_neighborhood_size`,
`published_signature_size`, `published_fold_enrichment`,
`published_log_p_value`, `published_raw_p_value`,
`published_adjusted_p_value`, `published_is_signature`,
`published_is_root_node`, `published_global_key_driver`, and
`published_overlap_items` preserve the original Phase 12 output when one
exists.

These fields are provenance fields. Use the reconstructed fields below for
Phase 18 analysis.

### 3. Driver class and mitochondrial annotation

`case_order`, `case_id`, and `case_label` assign either `mt_driver` or
`non_mt_driver`. The historical `case_*` names are retained for compatibility;
they now describe two driver classes, not three cases.

`is_core_mito`, `mitocarta_canonical_symbol`, `mito_tier`, `genome_origin`,
`is_mtdna_gene`, `extended_reference_member`, `mapping_status`, and
`phase03_mitocarta_match_type` describe mitochondrial membership and symbol
mapping.

### 4. Reconstructed original test

`query_member`, `test_status`, `usable_test`, and `explicit_family_member`
describe how the gene was tested. In this table every row is explicit and
usable. `test_status` distinguishes ordinary tests from explicit tests whose
best layer had zero query overlap.

The `original_*` columns contain the best-layer statistics before Phase 18
self-overlap correction:

- `original_layer`
- `original_overlap_count`
- `original_neighborhood_size`
- `original_non_neighborhood_size`
- `original_signature_size`
- `original_fold_enrichment`
- `original_log_p`
- `original_raw_p`
- `original_run_q`

`original_run_q` is BH adjusted across all explicit candidates in that run.

### 5. Phase 18 conditional self-overlap correction

`self_excluded = TRUE` only when the tested gene is an MT driver and belongs
to that run's query. One guaranteed self-overlap is removed, then the
hypergeometric statistics, best layer, and within-run BH values are recomputed.

The corrected result is stored in `final_layer`, `final_overlap_count`,
`final_neighborhood_size`, `final_non_neighborhood_size`,
`final_signature_size`, `final_background_size`, `final_fold_enrichment`,
`final_log_p`, `final_raw_p`, and `final_run_q`.

When `self_excluded = FALSE`, the final values equal the original values.

### 6. Conservative run support

`other_query_overlap`, `support_overlap_pass`, `support_fold_pass`,
`support_run_q_pass`, and `conservative_support` evaluate whether the corrected
run has at least two other query genes, fold enrichment greater than 1, and
final within-run q value at most 0.05.

`conservative_support` is true only when all three conditions pass.

### 7. Cross-run coverage and recurrence

`eligible_run_count`, `usable_run_count`, `explicit_run_count`,
`implicit_run_count`, `missing_run_count`, `coverage_numerator`,
`coverage_denominator`, `coverage_fraction`, and `coverage_pass` summarize the
gene across every included run in its broad network.

The aggregate calculation includes explicit tests from this table, implicit
background tests as P = 1, and omits runs where the gene is absent from the
background.

`conservative_support_count`, `conservative_support_pass`,
`recurrence_fraction`, the `supporting_*` columns, and support fold-enrichment
summaries describe where conservative evidence occurred.

### 8. Aggregated significance

`aggregate_acat_p` combines usable final run-level P values with ACAT.
`aggregate_acat_q` is its BH-adjusted value within the broad network across MT
and non-MT driver records. `aggregate_q_pass` indicates q at most 0.05.

`missing_as_one_acat_p` and `missing_as_one_acat_q` are sensitivity results
that replace missing run evidence with P = 1. `mean_log_p_score` is descriptive.

### 9. Candidate status, rank, and stability

`terminal_candidate_status` records the final selection outcome.
`within_case_rank` ranks driver candidates within broad network and driver
class. `top5_display` identifies the first five for figures.

The `stability_*` fields summarize leave-one-fine-cell-type-out analysis, and
`evidence_tier` gives the descriptive stability tier.

`case_driver_candidate_count` and `case_displayed_candidate_count` give the
number of passing and displayed candidates in that row's broad-network driver
class.

## Common selections

```text
Original significant subset:
    significant_by_call_key_drivers == TRUE

Final Phase 18 candidates:
    terminal_candidate_status == "driver_candidate"

Top-five figure records after deduplicating by broad network, gene, and class:
    top5_display == TRUE
```
