# Phase 18 `key_driver_significant_returns.tsv`: Column Guide

> **Superseded 2026-08-15.** This guide documents the former 1,641-row
> significant-only export. The current canonical output is
> [`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv),
> which contains all 95,557 explicit tested gene × run rows.

## Purpose and row meaning

This document explains every column in:

```text
results/minerva_production/18_key_driver_selection/key_driver_significant_returns.tsv
```

The table contains the significant genes returned by the Phase 12
`call_key_drivers()` calls that are included in Phase 18. Its row unit is:

> one significant key-driver gene returned in one KDA run

The pair `kda_run_id + key_driver` is therefore unique. A run can return many
genes, and a gene can occur in many runs.

The current table has:

| Quantity | Value |
|---|---:|
| Data rows | 1,641 |
| Columns | 103 |
| Included `call_key_drivers()` calls | 161 |
| Calls with at least one significant return | 122 |
| Included calls with no significant return, and therefore no row in this table | 39 |
| Unique returned genes | 295 |
| Distinct `broad_network + key_driver + case_id` summaries represented | 389 |
| Distinct driver-candidate summaries represented | 78 |
| Distinct top-five summaries represented | 47 |

This is a significant-return table, not a complete run manifest or a complete
gene-by-run testing matrix. The 39 included calls with no significant gene do
not appear. Genes tested but not returned by Phase 12 also do not receive an
individual row. However, reconstructed nonsignificant and implicit results
from all 161 included calls are used internally when the aggregate columns are
calculated.

## The three levels of information in one row

Each row combines three related levels of information:

1. **Run-level published result:** what Phase 12 `call_key_drivers()` returned
   for this gene in this exact run. These columns start with `published_`.
2. **Run-level reconstructed evidence:** an independent reconstruction of the
   same test, followed by self-exclusion for MT drivers in runs where they are
   query members. These are the
   `original_*`, `final_*`, and run-support columns.
3. **Gene-level aggregate evidence:** evidence for the gene across all
   included runs in the same broad network and driver class. These include
   coverage, ACAT, ranking, and stability columns.

The aggregate columns are repeated on every matching run-level row. For
example, all rows with the same `broad_network + key_driver + case_id` have the
same `aggregate_acat_q`, `within_case_rank`, and stability values. Deduplicate
on those three fields before counting aggregate candidates.

## Statistical notation used below

For a candidate driver at one cumulative directed-network layer:

| Symbol | Meaning |
|---|---|
| `q` | Number of query genes in the driver's selected neighborhood |
| `m` | Number of background genes in that neighborhood |
| `k` | Total query size in the run |
| `M` | Total effective background size in the run |
| `n` | Background genes outside the neighborhood, `M - m` |

The one-sided upper-tail hypergeometric P value is
`P(X >= q)`. Fold enrichment is:

```text
(q / m) / (k / M) = q * M / (m * k)
```

Layers are cumulative. Layer 1 contains the driver and genes reachable within
one directed edge; layers 2 and 3 extend this to at most two and three directed
edges. The selected layer is the layer with the smallest raw P value, with the
smaller layer winning an exact tie.

## Values, delimiters, and missing data

- Boolean values are written as `TRUE` or `FALSE`.
- `NA` means that a value is unavailable or not applicable.
- Empty supporting-set fields mean that no run passed the conservative-support
  definition.
- `published_overlap_items` uses semicolons (`;`) between genes.
- Aggregate supporting-set fields use vertical bars (`|`) between values.
- P values and q values are on the ordinary 0–1 scale unless the column name
  explicitly contains `log`.
- All `*_log_p*` columns use the natural logarithm, `ln(P)`, not `-log10(P)`.
  More-negative values indicate smaller P values.

## A. Schema, run, and row identity: columns 1–13

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 1 | `schema_version` | text | Schema identifier for this table. The current value is `phase18_significant_kda_returns_v2`. |
| 2 | `kda_run_id` | text | Unique Phase 12 KDA run identifier. It encodes the primary tier, fine cell type, sex/APOE group, and mitochondrial signature direction. Use this column to join back to Phase 12 run-level files. |
| 3 | `fine_cell_type` | text | Fine-grained cell type whose AD-versus-NCI mitochondrial query and induced broad-cell-type network were used in this run. |
| 4 | `broad_network` | text | Broad cell-type Bayesian network used by the run, such as `Astrocytes`, `Excitatory_neurons`, or `Microglia`. Aggregate evidence and ranks are computed separately within each broad network. |
| 5 | `signature_group` | category | Sex/APOE stratum that generated the query: `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, or `M_e4`. `F` and `M` denote female and male; `e33` denotes APOE ε3/ε3. |
| 6 | `sex` | category | Human-readable sex parsed from `signature_group`: `Female` or `Male`. |
| 7 | `apoe_group` | category | APOE category parsed from `signature_group`: `e2`, `e33`, or `e4`. |
| 8 | `signature_direction` | category | Direction of the mitochondrial AD-versus-NCI query: `AD_up_mito` contains mitochondrial genes upregulated in AD; `AD_down_mito` contains mitochondrial genes downregulated in AD. |
| 9 | `effective_query_genes` | integer | Number of query genes remaining after intersection with the usable run background. Phase 18 includes only runs with at least 10 effective query genes. This is `k` for the uncorrected test. |
| 10 | `effective_background_genes` | integer | Number of genes in the run-specific effective background after the network and expression-universe restrictions. This is `M` for the uncorrected test. |
| 11 | `run_terminal_status` | category | Terminal status inherited from the Phase 12 run manifest. Every row in the current significant-return table is `completed_significant`; completed calls with no returned gene have no row here. |
| 12 | `key_driver` | gene symbol | Current gene symbol of the candidate whose directed downstream neighborhood was enriched for the query in this run. “Driver” here is a network-enrichment result, not proof of biological causality. |
| 13 | `returned_by_call_key_drivers` | Boolean | Confirms that this row came from the significant output of Phase 12 `call_key_drivers()`. It is `TRUE` for every row in this table. |

## B. Published Phase 12 `call_key_drivers()` result: columns 14–26

These fields preserve the original significant result. They are not altered
by the Phase 18 conditional self-exclusion procedure.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 14 | `published_best_layer` | integer 1–3 | Cumulative directed-network layer selected by Phase 12 because it gave the smallest original raw hypergeometric P value for this driver. |
| 15 | `published_overlap_count` | integer | Original overlap `q`: number of effective query genes in the selected published neighborhood. If the driver is itself a query gene, this count can include the driver. |
| 16 | `published_neighborhood_size` | integer | Original neighborhood size `m`, including the driver itself and all background genes reachable within the selected cumulative layer. |
| 17 | `published_non_neighborhood_size` | integer | Original count `n = M - m`: effective-background genes outside the selected neighborhood. |
| 18 | `published_signature_size` | integer | Original effective query size `k`. It normally equals `effective_query_genes`. |
| 19 | `published_fold_enrichment` | numeric | Original fold enrichment, `(q/m)/(k/M)`, as returned by Phase 12. Values above 1 indicate enrichment; the implementation reports a rounded value. |
| 20 | `published_log_p_value` | numeric | Natural logarithm of the original unadjusted upper-tail hypergeometric P value. More-negative values mean stronger evidence. |
| 21 | `published_raw_p_value` | numeric 0–1 | Original unadjusted P value reconstructed as `exp(published_log_p_value)`. It is included for convenience because Phase 12 stored the logged value. |
| 22 | `published_adjusted_p_value` | numeric 0–1 | Original Benjamini–Hochberg q value across the explicitly tested candidate genes in this run. Every row satisfies `<= 0.05`, because Phase 12 returned only significant genes. |
| 23 | `published_is_signature` | Boolean or `NA` | Phase 12 indicator for whether the driver itself belonged to the effective query. It can be `NA` in a small upstream edge case. Prefer the reconstructed `query_member` column when an explicit Boolean is needed. |
| 24 | `published_is_root_node` | Boolean | Whether the driver had no incoming edge in the run-specific induced directed network. This describes network topology; it is not a significance or aggregate-selection filter. |
| 25 | `published_global_key_driver` | Boolean | NetWeaver within-run redundancy flag. `TRUE` means this significant driver was not within the configured two downstream layers of another significant driver in the same run. It does not mean “global across the study.” |
| 26 | `published_overlap_items` | semicolon-separated genes | Query genes contained in the original selected neighborhood. For an MT driver that is a query member, this original list can include the driver itself; the table does not provide a separate corrected overlap-gene list. |

## C. Driver class and reconstructed-test identity: columns 27–35

The two driver classes are mutually exclusive:

| Driver class | Rule | Interpretation |
|---|---|---|
| MT driver | Core mitochondrial gene | Uses all included runs in the broad network. Self-overlap is removed only in runs where the gene is a query member. |
| non-MT driver | Not a core mitochondrial gene | Uses all included runs in the broad network. Query membership is false because the query contains core mitochondrial genes. |

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 27 | `case_order` | integer | Stable display order: `1` for MT driver and `2` for non-MT driver. The column retains its historical name, but it now orders two driver classes. |
| 28 | `case_id` | category | Machine-readable driver class: `mt_driver` or `non_mt_driver`. The column name is retained for compatibility with downstream code. |
| 29 | `case_label` | text | Human-readable driver-class label: `MT driver` or `non-MT driver`. |
| 30 | `is_core_mito` | Boolean | Whether Phase 09 marks the gene as a core MitoCarta gene (`is_mitocarta3`). This field alone determines the driver class. Missing annotation is conservatively treated as non-MT. |
| 31 | `mitocarta_canonical_symbol` | gene symbol or `NA` | Canonical MitoCarta symbol assigned by Phase 09. It is usually `NA` for genes not matched to MitoCarta. |
| 32 | `query_member` | Boolean | Independently reconstructed indicator that the driver is an effective query gene in this exact run. Unlike `published_is_signature`, this field is always explicit. |
| 33 | `test_status` | category | How the gene's run-level result was represented during reconstruction. Every current exported row is `explicit_test`. In the complete internal matrix, `explicit_zero_overlap`, `implicit_zero_overlap`, and `absent_from_background` can also occur. |
| 34 | `usable_test` | Boolean | Whether this gene/run opportunity contributes a usable P value to aggregation. It is `TRUE` for every exported significant row. In the complete internal matrix it is false when the gene is absent from that run's background. |
| 35 | `explicit_family_member` | Boolean | Whether the gene belonged to the explicit candidate family tested by the reconstructed KDA call. Explicit candidates are network-proximal to the query and have a directed neighborhood to test. It is `TRUE` for every published row. |

## D. Original and final reconstructed run evidence: columns 36–60

`original_*` independently reconstructs the Phase 12 result. When an MT driver
is a query member, the driver appears in both its own neighborhood and the
query, producing a guaranteed overlap. Phase 18 removes that one gene at every
layer:

```text
q_final = q_original - 1
m_final = m_original - 1
k_final = k_original - 1
M_final = M_original - 1
```

Phase 18 then recomputes P values and fold enrichment and selects the best
layer again. Therefore, the final layer can differ from the original layer.
MT-driver runs where the gene is not in the query and all non-MT-driver runs
require no self-exclusion, so their final evidence equals their original
evidence.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 36 | `original_layer` | integer 1–3 | Best cumulative layer from the independently reconstructed original test. It is validated against `published_best_layer`. |
| 37 | `original_overlap_count` | integer | Reconstructed original overlap `q`, including the driver when it is a query member. |
| 38 | `original_neighborhood_size` | integer | Reconstructed original neighborhood size `m`, including the driver. |
| 39 | `original_non_neighborhood_size` | integer | Reconstructed original outside-neighborhood count `M - m`. |
| 40 | `original_signature_size` | integer | Reconstructed original effective query size `k`. |
| 41 | `original_fold_enrichment` | numeric | Reconstructed original fold enrichment at `original_layer`. It is checked against the published value, allowing for upstream rounding. |
| 42 | `original_log_p` | numeric | Natural logarithm of the reconstructed original raw hypergeometric P value. |
| 43 | `original_raw_p` | numeric 0–1 | Reconstructed original raw hypergeometric P value. |
| 44 | `original_run_q` | numeric 0–1 | Benjamini–Hochberg q value obtained from the original raw P values across all explicit candidates reconstructed for this run. It is validated against `published_adjusted_p_value`. |
| 45 | `self_excluded` | Boolean | `TRUE` exactly when `case_id = mt_driver` and `query_member = TRUE`. It records that the driver's guaranteed self-overlap was removed before calculating final evidence. |
| 46 | `final_layer` | integer 1–3 | Best layer after conditional self-exclusion and re-selection. It equals `original_layer` when `self_excluded = FALSE`. |
| 47 | `final_overlap_count` | integer | Final query overlap `q`. When self-exclusion was applied, this counts other query genes and excludes the driver. |
| 48 | `final_neighborhood_size` | integer | Final neighborhood size `m`. When self-exclusion was applied, the driver is removed from the selected neighborhood count. |
| 49 | `final_non_neighborhood_size` | integer | Final number of background genes outside the selected neighborhood, `M_final - m_final`. |
| 50 | `final_signature_size` | integer | Final query size `k`. It is one smaller than the original query size when `self_excluded = TRUE` and unchanged otherwise. |
| 51 | `final_background_size` | integer | Final background size `M`. It is one smaller than the original background when `self_excluded = TRUE` and unchanged otherwise. |
| 52 | `final_fold_enrichment` | numeric | Fold enrichment recomputed from the final counts at `final_layer`. This is the fold value used by Phase 18's conservative-support rule. |
| 53 | `final_log_p` | numeric | Natural logarithm of the final unadjusted hypergeometric P value. |
| 54 | `final_raw_p` | numeric 0–1 | Final unadjusted P value used as this run's input to gene-level ACAT aggregation. |
| 55 | `final_run_q` | numeric 0–1 | Benjamini–Hochberg q value after replacing every explicit candidate's original P value with its final P value in this run. MT query members use corrected P values; all other candidates retain their original P values. |
| 56 | `other_query_overlap` | integer | Number of query genes other than the driver captured by the final neighborhood. It is the same numeric value as `final_overlap_count`; the name emphasizes the self-excluded MT-driver interpretation. |
| 57 | `support_overlap_pass` | Boolean | Whether `other_query_overlap >= 2`. This prevents a run from counting as conservative support based on only one other query gene. |
| 58 | `support_fold_pass` | Boolean | Whether `final_fold_enrichment > 1`. The threshold is strict; exactly 1 does not pass. |
| 59 | `support_run_q_pass` | Boolean | Whether `final_run_q <= 0.05`. |
| 60 | `conservative_support` | Boolean | Whether all three run-level support conditions pass simultaneously: at least two other query genes, fold enrichment above 1, and final within-run q value at most 0.05. |

## E. Gene annotation: columns 61–66

These annotations come from the validated Phase 09 gene-annotation table and
are repeated for the same gene.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 61 | `mito_tier` | category | Phase 09 mitochondrial classification. Values in this file include `core_mito_protein`, `mito_extended`, `non_mito`, and `annotation_missing_treated_not_core`. Only the core flag determines MT versus non-MT driver class. |
| 62 | `genome_origin` | category or `NA` | Genomic origin from Phase 09, principally `nuclear` or `mtDNA`. |
| 63 | `is_mtdna_gene` | Boolean | Whether the gene is encoded by mitochondrial DNA. This is distinct from `is_core_mito`; most core mitochondrial proteins are nuclear encoded. |
| 64 | `extended_reference_member` | Boolean | Whether the gene belongs to the broader Phase 09 mitochondrial-reference collection. This is descriptive and is not the core-mitochondrial case gate. |
| 65 | `mapping_status` | category | Phase 09 identifier-mapping status. Current rows are primarily `mapped_ensembl`; missing annotation is labeled `annotation_missing`. Multiple compatible routes can be joined with `|`. |
| 66 | `phase03_mitocarta_match_type` | category or `NA` | How the gene matched the earlier MitoCarta reference, such as `canonical`, `unique_synonym`, or `unmatched`. |

## F. Cross-run coverage and recurrence: columns 67–86

These columns summarize one `broad_network + key_driver + case_id` record and
are repeated on all matching run-level rows.

For both driver classes, the denominator contains all included runs in the
broad network. For an MT driver, query membership changes whether an
individual run is self-corrected; it no longer splits the denominator.

Within that denominator, an **explicit** run directly tested the gene. An
**implicit** run contained the gene in its background but not in the explicit
candidate family; it contributes a valid null P value of 1. A **missing** run
did not contain the gene in its background and contributes no primary P value.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 67 | `eligible_run_count` | integer | Number of included runs in the broad network. It is fixed by network for both driver classes: 21 Astrocyte, 97 Excitatory-neuron, 28 Inhibitory-neuron, 6 Microglia, 6 OPC, 2 Oligodendrocyte, or 1 Vasculature run. |
| 68 | `usable_run_count` | integer | Denominator runs providing a usable P value: `explicit_run_count + implicit_run_count`. |
| 69 | `explicit_run_count` | integer | Runs in which the gene was explicitly tested as a KDA candidate. These runs can have any P value; they are not limited to the significant rows exported in this table. |
| 70 | `implicit_run_count` | integer | Runs in which the gene was present in the background but outside the explicit candidate family. Each contributes P = 1, so it supplies null rather than missing evidence. |
| 71 | `missing_run_count` | integer | Included broad-network runs in which the gene was absent from the effective background. These contribute missing values to primary ACAT. `eligible_run_count = usable_run_count + missing_run_count`. |
| 72 | `coverage_numerator` | integer | Number of usable runs; identical to `usable_run_count`. |
| 73 | `coverage_denominator` | integer | Number of included runs in the broad network; identical to `eligible_run_count`. |
| 74 | `coverage_fraction` | numeric 0–1 | `coverage_numerator / coverage_denominator`. It measures how completely the gene can be evaluated across its broad-network runs. |
| 75 | `coverage_pass` | Boolean | Whether `coverage_fraction >= 0.80`, the primary Phase 18 coverage gate. |
| 76 | `conservative_support_count` | integer | Number of usable runs satisfying `conservative_support = TRUE` for this gene/network/driver-class record. |
| 77 | `conservative_support_pass` | Boolean | Whether at least one run provides conservative support. |
| 78 | `recurrence_fraction` | numeric 0–1 | `conservative_support_count / usable_run_count`. The denominator is usable runs, not all eligible runs. |
| 79 | `supporting_fine_cell_type_count` | integer | Number of distinct fine cell types among conservative-support runs. |
| 80 | `supporting_fine_cell_types` | `|`-separated text | Sorted fine cell types contributing conservative support. Empty when there is no support. |
| 81 | `supporting_group_count` | integer | Number of distinct sex/APOE `signature_group` values among conservative-support runs. |
| 82 | `supporting_groups` | `|`-separated text | Sorted supporting sex/APOE groups. Empty when there is no support. |
| 83 | `supporting_direction_count` | integer | Number of mitochondrial query directions represented among support runs: 0, 1, or 2. |
| 84 | `supporting_directions` | `|`-separated category list | Supporting directions, `AD_up_mito`, `AD_down_mito`, or both. Empty when there is no support. |
| 85 | `median_support_fold_enrichment` | numeric or `NA` | Median `final_fold_enrichment` across conservative-support runs only. It is `NA` when no run supplies conservative support. |
| 86 | `maximum_support_fold_enrichment` | numeric or `NA` | Maximum `final_fold_enrichment` across conservative-support runs only. It is `NA` when no run supplies conservative support. |

## G. Aggregate significance, candidate status, and rank: columns 87–95

Primary ACAT combines the `final_raw_p` values across the broad-network run
denominator with equal weight. Explicit nonsignificant results are included,
implicit results contribute P = 1, and background-absent runs are omitted.
Aggregate values are reported only when coverage is at least 0.80.

Aggregate Benjamini–Hochberg correction is performed separately within each
broad network, across all assessable gene × driver-class aggregate records in
that network. It is not performed separately for each driver class.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 87 | `aggregate_acat_p` | numeric 0–1 or `NA` | Primary equal-weight ACAT P value combining usable final run-level P values while omitting missing runs. It is `NA` when the 80% coverage gate fails. |
| 88 | `aggregate_acat_q` | numeric 0–1 or `NA` | Benjamini–Hochberg-adjusted primary ACAT P value within the broad-network family described above. |
| 89 | `aggregate_q_pass` | Boolean | Whether `aggregate_acat_q <= 0.05`. |
| 90 | `missing_as_one_acat_p` | numeric 0–1 or `NA` | Conservative sensitivity ACAT result in which background-absent runs are assigned P = 1 instead of omitted. It uses the same 80% reporting gate. |
| 91 | `missing_as_one_acat_q` | numeric 0–1 or `NA` | Benjamini–Hochberg-adjusted version of `missing_as_one_acat_p`, using the same assessable broad-network family as the primary analysis. This is a sensitivity field, not the primary candidate gate. |
| 92 | `mean_log_p_score` | nonnegative numeric or `NA` | Descriptive mean of `-log10(final_raw_p)` across usable runs, with P values floored at `1e-300`. Implicit P = 1 contributes zero; missing runs are omitted. Larger values mean stronger average evidence. This is a score, not a P value. |
| 93 | `terminal_candidate_status` | category | Final aggregate classification. `driver_candidate`: coverage passes, aggregate q <= 0.05, and at least one conservative-support run. `aggregate_only`: aggregate q passes but no conservative-support run. `exploratory`: raw aggregate P <= 0.05 but q > 0.05. `not_supported`: raw aggregate P > 0.05. `insufficient_coverage`: coverage < 0.80. `not_testable`: no reportable aggregate P/q despite passing the preceding coverage check. The current table contains `driver_candidate`, `exploratory`, `not_supported`, and `insufficient_coverage`. |
| 94 | `within_case_rank` | positive integer or `NA` | Rank assigned only to `driver_candidate` records, separately within `broad_network + case_id`. Ordering is increasing `aggregate_acat_q`, then increasing `aggregate_acat_p`, then alphabetical gene symbol. Noncandidates are `NA`. |
| 95 | `top5_display` | Boolean | Whether the record is a driver candidate with `within_case_rank <= 5`. This selects at most five genes per represented broad-network/driver-class combination. Deduplicate aggregate keys before counting displayed genes. |

The three actual candidate gates are therefore:

1. `coverage_fraction >= 0.80`;
2. `conservative_support_count >= 1`; and
3. `aggregate_acat_q <= 0.05`.

The three conditions inside `conservative_support` are run-level support
requirements, not three additional aggregate gates.

## H. Stability and list-size context: columns 96–103

Stability is evaluated only for primary `driver_candidate` records. Within a
broad network, Phase 18 omits one fine cell type at a time, recomputes all
gene/driver-class aggregates and broad-network multiple-testing correction, and then
checks the candidate again.

| No. | Column | Type | Detailed meaning |
|---:|---|---|---|
| 96 | `stability_assessable_repetitions` | integer | Number of leave-one-fine-cell-type-out repetitions in which this candidate retained a reportable aggregate P value. It can be smaller than the number of fine cell types if removing one leaves the gene/driver-class combination unassessable. Noncandidates have 0. |
| 97 | `stability_nominal_fraction` | numeric 0–1 or `NA` | Fraction of assessable repetitions with `aggregate_acat_p <= 0.05`. This uses the nominal aggregate P value, not the adjusted q value. |
| 98 | `stability_q_fraction` | numeric 0–1 or `NA` | Fraction of assessable repetitions with recalculated `aggregate_acat_q <= 0.05`. |
| 99 | `stability_candidate_fraction` | numeric 0–1 or `NA` | Fraction of assessable repetitions in which the full recalculated status remains `driver_candidate`, including coverage, support, and aggregate-q requirements. |
| 100 | `stability_worst_rank` | positive integer or `NA` | Largest, and therefore numerically worst, candidate rank among assessable repetitions where the gene still received a candidate rank. Repetitions in which the gene lost candidate status have no rank and are reflected in `stability_candidate_fraction`, not directly in this field. |
| 101 | `evidence_tier` | category | Compact evidence label. `tier1_recurrent_stable`: driver candidate supported by at least two fine cell types and with `stability_nominal_fraction >= 0.80`. `tier2_localized_or_unstable`: assessable candidate not meeting that rule. `tier_not_assessable`: candidate with no assessable stability repetition. `not_a_driver_candidate`: aggregate did not receive candidate status. |
| 102 | `case_driver_candidate_count` | integer | Total number of driver-candidate genes in this row's `broad_network + case_id`, calculated from the complete aggregate universe. The historical column name is retained, but `case_id` now means driver class. |
| 103 | `case_displayed_candidate_count` | integer 0–5 | Number selected for display in this row's broad-network/driver-class list: `min(case_driver_candidate_count, 5)`. It counts distinct aggregate genes, not run-level rows. The current file contains only values 1–5. |

## Recommended use

### Examine individual significant calls

Use the run identity fields together with `published_*` or `final_*` fields.
When `self_excluded = TRUE`, use `final_*`; the published fields retain the
uncorrected self-overlap.

### Make one row per aggregate gene

Before analyzing candidate counts, ACAT values, ranks, or stability, keep one
row per:

```text
broad_network + key_driver + case_id
```

Do not treat the repeated aggregate values on multiple significant run rows as
independent observations.

### Select the Phase 18 candidates or top five

After deduplication:

```text
terminal_candidate_status == "driver_candidate"
```

selects all candidates, and:

```text
top5_display == TRUE
```

selects the display list.

### Study sex/APOE or direction-specific support

Use the individual rows and their `sex`, `apoe_group`, and
`signature_direction` fields for call-level patterns. Use `supporting_groups`
and `supporting_directions` when the question concerns only runs that pass the
conservative-support definition.

## Interpretation cautions

- A row means that the gene's downstream network neighborhood was enriched for
  the mitochondrial query in one run. It does not establish causal regulation
  or experimental directionality.
- All rows were significant under the original Phase 12 within-run test, but a
  row's gene need not become a Phase 18 `driver_candidate`. Phase 18 also uses
  coverage, recurrence, conditional MT self-correction, and cross-run aggregation.
- `published_global_key_driver` is a redundancy-reduction flag within one run;
  it is unrelated to `terminal_candidate_status` or cross-cell-type breadth.
- Row counts are not gene counts. The same aggregate candidate can appear in
  several run-level rows.
- `top5_display` is a presentation flag, not a separate statistical test.
