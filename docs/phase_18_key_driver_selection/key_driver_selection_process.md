# Phase 18 Key-Driver Selection Process

## Goal

Select up to five genes for each broad network and each of the two driver
classes:

- `mt_driver`: core mitochondrial genes
- `non_mt_driver`: genes outside the core mitochondrial set

The historical column name `case_id` stores these two driver classes. Query
membership does not create another case.

## Starting table

Start with
[`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv).

The table contains 95,557 rows from 161 included `call_key_drivers()` calls.
One row is one explicitly tested gene in one run:

```text
kda_run_id + key_driver
```

Both significant and nonsignificant tests are present. Do not begin by
filtering to `significant_by_call_key_drivers = TRUE`; doing so would discard
valid negative evidence used by the cross-run analysis.

## Columns used during selection

The run-level correction, conservative-support assessment, ACAT aggregation,
and multiple-testing correction have already been calculated in the TSV. The
selection process reads the following columns; it does not recalculate them.
The run-level columns explain and audit the evidence. The aggregate-gate and
ranking columns are the fields directly used to extract the final top-five
lists.

Because each gene has one fixed `case_id`, “per gene × broad network” is
equivalent to “per candidate unit.” The class remains in the stored key so the
two driver classes can be grouped and ranked separately.

### Identity and grouping columns

| Column | Level | Explanation |
|---|---|---|
| `kda_run_id` | Per run | Identifies one KDA call. A run corresponds to one fine cell type, sex/APOE group, and mitochondrial direction. |
| `key_driver` | Per gene | Gene tested as a possible network driver. It can occur in many run rows and broad networks. |
| `broad_network` | Per run and candidate unit | Broad cell-type Bayesian network used for the run. Cross-run evidence is never combined across broad networks. |
| `case_id` | Per gene | Fixed driver class: `mt_driver` or `non_mt_driver`. A gene has only one class, even when it occurs in multiple broad networks. |

### Final run-level evidence columns

| Column | Level | Explanation |
|---|---|---|
| `self_excluded` | Per gene × run | `TRUE` when the gene is an MT driver and belongs to that run's query. Its guaranteed self-overlap was removed before calculating the final statistics. |
| `final_raw_p` | Per gene × run | Unadjusted hypergeometric enrichment P value for the gene's final best network layer in this one run. For a self-excluded row, it is calculated after removing the gene from the overlap, neighborhood, query, and background. Otherwise it equals `original_raw_p`. |
| `final_run_q` | Per gene × run; corrected within the run | BH-adjusted value obtained from all `final_raw_p` values for explicitly tested genes in the same `kda_run_id`. It measures significance within one KDA call, not across runs. |
| `other_query_overlap` | Per gene × run | Number of query genes in the final neighborhood after any required self-exclusion. |
| `final_fold_enrichment` | Per gene × run | Enrichment of query genes in the final neighborhood relative to the run background. |
| `conservative_support` | Per gene × run | `TRUE` when `other_query_overlap >= 2`, `final_fold_enrichment > 1`, and `final_run_q <= 0.05` for this gene in this run. |

`final_raw_p` and `final_run_q` have different roles:

```text
final_raw_p
    = evidence for one gene in one run before within-run correction

final_run_q
    = the same run-level evidence after correcting for all genes tested
      in that call
```

### Cross-run aggregation and candidate-gate columns

| Column | Level | Explanation |
|---|---|---|
| `eligible_run_count` | Per broad network | Number of included runs in the broad network. It is fixed for every gene and both driver classes within that network. |
| `usable_run_count` | Per gene × broad network | Number of eligible runs in that network where the gene had usable explicit or implicit-null evidence. |
| `coverage_fraction` | Per gene × broad network | `usable_run_count / eligible_run_count` for that gene in that network. It must be at least 0.80. |
| `conservative_support_count` | Per gene × broad network | Number of runs in that network where `conservative_support = TRUE` for the gene. At least one is required. |
| `aggregate_acat_p` | Per gene × broad network | ACAT P value combining that gene's usable `final_raw_p` evidence across runs in the network. Implicit-null tests contribute `P = 1`; missing tests are omitted. |
| `aggregate_acat_q` | Per gene × broad network; corrected within the broad network | BH-adjusted `aggregate_acat_p`. The correction family contains all assessable gene records from both driver classes in the same broad network. It must be at most 0.05. |
| `terminal_candidate_status` | Per gene × broad network | Final decision for that gene in that network. `driver_candidate` means its coverage, support, and aggregate-q gates all passed. |

The two q-value columns operate at different levels:

```text
final_run_q       = within one KDA run
aggregate_acat_q  = across runs and then across candidate genes
```

### Ranking and display columns

| Column | Level | Explanation |
|---|---|---|
| `within_case_rank` | Per gene × broad network; ranked within broad network × driver class | Rank of the gene relative to other passing candidates in the same `broad_network + case_id` list. |
| `top5_display` | Per gene × broad network | `TRUE` when the gene's `within_case_rank` is 1–5 in its broad-network driver-class list. |

## Selection overview

```text
95,557 explicit gene × run rows
        ↓
one gene × broad network × driver-class record
        ↓
apply coverage, support, and aggregate-q gates
        ↓
rank passing genes within broad network × driver class
        ↓
retain ranks 1–5
```

## Step 1: Create one record per candidate unit

The selection unit is:

```text
broad_network + key_driver + case_id
```

Each gene belongs to exactly one driver class, so a gene can have only one
candidate unit—and therefore at most one `driver_candidate` decision—within a
given broad network. Its many gene × run rows are evidence contributing to
that single decision; they are not separate driver candidates.

The same gene can still be a driver candidate in more than one broad network.
For example, a gene selected in both astrocytes and excitatory neurons has two
candidate units because the broad networks differ.

The TSV has multiple rows for a gene when it was explicitly tested in multiple
runs. Its cross-run aggregate fields are repeated and are constant within the
candidate unit. Deduplicate the table to one row per candidate unit, retaining:

- `coverage_fraction`
- `conservative_support_count`
- `aggregate_acat_p`
- `aggregate_acat_q`
- `terminal_candidate_status`
- `within_case_rank`
- `top5_display`

## Step 2: Apply the three candidate gates

A gene becomes a `driver_candidate` only when all three gates pass:

| Gate | Required value |
|---|---|
| Coverage | `coverage_fraction >= 0.80` |
| Conservative support | `conservative_support_count >= 1` |
| Aggregated significance | `aggregate_acat_q <= 0.05` |

The equivalent stored rule is:

```text
terminal_candidate_status == "driver_candidate"
```

Failing genes are not eligible for the top-five lists. A strong rank cannot
rescue a gene that failed one of these gates.

## Step 3: Rank separately within each list

Make a separate ranked list for every:

```text
broad_network + case_id
```

Sort the passing driver candidates by:

1. smaller `aggregate_acat_q`;
2. smaller `aggregate_acat_p`; and
3. alphabetical `key_driver` as the deterministic tie-breaker.

Assign ranks beginning at 1. The stored rank is `within_case_rank`.

## Step 4: Retain up to five genes

For each broad-network × driver-class list, retain:

```text
within_case_rank <= 5
```

The equivalent stored flag is:

```text
top5_display = TRUE
```

Five is the maximum, not a requirement to fill every list. If only two genes
pass all three gates, the list contains two genes. Nonsignificant or otherwise
failing genes are not used as backfills.

## Compact selection logic

```text
1. Deduplicate by broad_network + key_driver + case_id.
2. Keep terminal_candidate_status == "driver_candidate".
3. Group by broad_network + case_id.
4. Sort by aggregate_acat_q, aggregate_acat_p, key_driver.
5. Keep ranks 1 through 5.
```

## Current selected lists

| Broad network | Driver class | Passing candidates | Displayed | Selected genes in rank order |
|---|---|---:|---:|---|
| Astrocytes | MT driver | 6 | 5 | MT-CO2, MT-CO3, MT-ATP6, COX7C, COX4I1 |
| Astrocytes | non-MT driver | 5 | 5 | RPL11, RPLP1, RPL15, APOE, LAPTM4A |
| Excitatory neurons | MT driver | 13 | 5 | MT-CO2, UQCR10, COX4I1, COX6B1, MT-CYB |
| Excitatory neurons | non-MT driver | 21 | 5 | RPL11, RPS13, SELENOW, LAMTOR5, DYNLT1 |
| Inhibitory neurons | MT driver | 11 | 5 | MT-CO2, MT-CO3, MT-CYB, MT-ND5, COX7C |
| Inhibitory neurons | non-MT driver | 5 | 5 | RPS15, LAMTOR5, RPLP1, ATP6V1F, RPL38 |
| Microglia | MT driver | 2 | 2 | MT-CO2, MT-ND4 |
| Microglia | non-MT driver | 1 | 1 | RPL11 |
| OPCs | MT driver | 3 | 3 | MT-CO3, MT-CO2, MT-ND4 |
| OPCs | non-MT driver | 4 | 4 | RPS15, FTL, ANKRD11, NCOA1 |
| Oligodendrocytes | MT driver | 2 | 2 | MT-CO2, MT-ND4 |
| Oligodendrocytes | non-MT driver | 1 | 1 | RPL11 |
| Vasculature cells | MT driver | 4 | 4 | MT-CO3, MT-CO2, MT-ATP6, MT-ND4 |
| Vasculature cells | non-MT driver | 0 | 0 | None |

Across all lists, 78 candidate units pass the three gates and 47 are retained
for the top-five displays.

## Interpretation

A selected gene has sufficient run coverage, at least one conservatively
supporting run, and significant cross-run ACAT evidence after broad-network
multiple-testing correction. Selection supports prioritization as a
network-associated driver; it does not by itself establish causal regulation.
