# Unified Selection of Phase 12 Key Drivers

**Phase:** 18 key-driver selection

**Status:** Current implemented workflow

**Rewritten:** 2026-08-15

## Purpose

Phase 18 starts with the complete explicit test table in
[`call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv).
One row means that one gene received an enrichment test in one included KDA
run. Significant and nonsignificant tests are both retained.

The analysis follows one linear sequence:

```text
161 included KDA calls
-> reconstruct and record every explicit gene × run test
-> assign MT versus non-MT class and correct MT query-member runs
-> label conservative supporting runs
-> calculate coverage and aggregate P values
-> apply three candidate gates
-> rank and assess stability
```

## Step 1: Start with all explicit tested rows

The current starting table contains:

| Quantity | Value |
|---|---:|
| Included KDA calls | 161 |
| Calls with at least one significant returned gene | 122 |
| Included calls with no significant returned gene | 39 |
| All explicit tested `gene × run` rows | 95,557 |
| Nonsignificant tested rows | 93,916 |
| Significant tested rows | 1,641 |
| Unique tested genes | 6,149 |

The unique row key is:

```text
kda_run_id + key_driver
```

A run tests many genes, and a gene can be tested in several runs. Thus,
95,557 rows does not mean 95,557 distinct genes.

Every row satisfies:

```text
tested_by_call_key_drivers = TRUE
```

`significant_by_call_key_drivers = TRUE` identifies the original 1,641 rows
that passed within-run BH adjustment. The `published_*` columns are populated
only for those rows. Reconstructed test columns are populated for every row.

## Step 2: Define the included runs

One primary run is:

```text
fine cell type × sex/APOE group × mitochondrial direction
```

The full primary grid is:

```text
54 fine cell types × 6 sex/APOE groups × 2 directions = 648 runs
```

The six groups are `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, and
`M_e4`. The directions are `AD_up_mito` and `AD_down_mito`.

The query for a run is the set of core mitochondrial genes that are
upregulated or downregulated in AD versus NCI for that fine cell type and
sex/APOE group. The run uses the Bayesian network for the matching broad cell
type.

A run is included only when:

1. it belongs to the primary six-group, two-direction scope;
2. its source contrast and network inputs were validated;
3. the Phase 12 KDA call completed; and
4. its effective query has at least 10 genes.

This leaves 161 runs:

| Broad network | Runs |
|---|---:|
| Astrocytes | 21 |
| Excitatory neurons | 97 |
| Inhibitory neurons | 28 |
| Microglia | 6 |
| OPCs | 6 |
| Oligodendrocytes | 2 |
| Vasculature cells | 1 |
| **Total** | **161** |

Excluded runs are not used later and are not counted in coverage denominators.

## Step 3: Reconstruct complete gene × run evidence

Phase 18 rebuilds each included KDA call from its query, background, and
directed Bayesian network before the within-run significance filter is applied.

For every explicit candidate, cumulative directed layers 1–3 are tested. The
layer with the smallest raw hypergeometric P value is retained. The
The reconstructed significant subset and its layers, overlap counts, fold
enrichments, and adjusted P values must reproduce the 1,641 published rows.

Phase 18 then represents every relevant gene × run opportunity as:

| Type | Meaning | Value used later | Usable? |
|---|---|---:|---:|
| **Explicit** | Gene received a direct KDA enrichment test | Its reconstructed P value, significant or not | Yes |
| **Implicit null** | Gene was in the background but outside the explicit candidate family | `P = 1` | Yes |
| **Missing** | Gene was absent from the run background | `NA` | No |

`P = 1` is valid null evidence and must be retained. `NA` means that the gene
could not be tested.

For one tested layer:

- `q` is the number of query genes in the neighborhood;
- `m` is the number of background genes in the neighborhood;
- `k` is the total effective query size; and
- `M` is the total effective background size.

Fold enrichment is:

```text
(q / m) / (k / M)
```

The raw P value is the upper-tail hypergeometric probability of observing at
least `q` query genes in a neighborhood of size `m`.

## Step 4: Assign two driver classes and correct MT query-member runs

Each gene × run opportunity receives one driver class:

| Driver class | Assignment | Main question |
|---|---|---|
| **MT driver** | Core mitochondrial gene | Does a mitochondrial gene connect to the altered mitochondrial program across all included runs? |
| **non-MT driver** | Not a core mitochondrial gene | Does a non-core gene connect to the altered mitochondrial program? |

Query membership no longer creates separate cases. An MT driver uses all
included runs in its broad network. Its test is self-corrected only in runs
where the gene belongs to the query.

### Conditional self-overlap correction for MT drivers

When an MT driver belongs to a run's query, it also belongs to its own
neighborhood. This creates one guaranteed overlap. Phase 18 removes that gene
at every layer:

```text
q_final = q_original - 1
m_final = m_original - 1
k_final = k_original - 1
M_final = M_original - 1
```

P value and fold enrichment are recalculated, and the best layer is selected
again. The corrected layer can differ from the published layer.

An MT-driver run where the gene is not in the query needs no correction.
Non-MT drivers cannot be query members and also need no correction.

After correction, BH q values are recomputed across the complete explicit
candidate family within each KDA run. This is one correction family per run.

## Step 5: Label conservative supporting runs

A usable gene × run result is a conservative supporting run when all three
conditions hold:

1. the final neighborhood contains at least two other query genes;
2. final fold enrichment is greater than 1; and
3. final within-run q value is at most 0.05.

The minimum query size of 10 was already enforced when runs were selected. It
is not a fourth support condition.

A usable result that fails the support rule is not deleted. Its final P value
still contributes to cross-run aggregation.

## Step 6: Build one gene × broad-network × driver-class aggregate

The candidate unit is:

```text
broad_network + key_driver + case_id
```

The retained `case_id` column now stores the driver class: `mt_driver` or
`non_mt_driver`.

Both driver classes use all included runs in their broad network:

| Driver class | Eligible runs |
|---|---|
| **MT driver** | All included runs in the broad network; apply self-exclusion only when the gene is a query member |
| **non-MT driver** | All included runs in the broad network |

Coverage is:

```text
coverage_fraction = usable_run_count / eligible_run_count
```

Explicit and implicit-null results count as usable. Missing results do not.

For every candidate unit, Phase 18 also records:

- conservative-support count and recurrence fraction;
- supporting fine cell types;
- supporting sex/APOE groups and directions; and
- median and maximum fold enrichment among supporting runs.

### Combine run-level P values

All usable `final_raw_p` values are combined with equal-weight ACAT:

- significant and nonsignificant explicit P values are included;
- implicit-null values of `P = 1` are included; and
- missing values are omitted.

The primary ACAT result is reported only when coverage is at least 80%.

ACAT P values are BH adjusted within each broad network across all assessable
`gene × driver class` aggregate records in that network. The two classes
remain distinct candidate records and are ranked separately later; only the
broad-network multiple-testing family spans both classes.

As a sensitivity result, `missing_as_one_acat_p/q` repeats aggregation after
replacing missing values with `P = 1`. It is not used by the primary candidate
rule.

## Step 7: Apply the three candidate gates

A candidate unit is a `driver_candidate` only when all three gates pass:

| Gate | Rule |
|---|---|
| **Coverage** | `coverage_fraction >= 0.80` |
| **Conservative support** | `conservative_support_count >= 1` |
| **Combined significance** | `aggregate_acat_q <= 0.05` |

The three conditions defining a conservative supporting run belong inside the
support gate. They are not three additional aggregate gates.

Other statuses are:

| Status | Meaning |
|---|---|
| `aggregate_only` | Aggregate q passes, but no run passes conservative support |
| `exploratory` | Coverage passes and raw ACAT P is at most 0.05, but aggregate q does not pass |
| `not_supported` | Coverage passes and raw ACAT P is above 0.05 |
| `insufficient_coverage` | Coverage is below 0.80 |
| `not_testable` | No reportable aggregate result remains |

## Step 8: Rank candidates and assess stability

Only driver candidates are ranked. Ranking is separate within:

```text
broad_network + case_id
```

The order is:

1. smaller `aggregate_acat_q`;
2. smaller `aggregate_acat_p`; and
3. alphabetical gene symbol as the tie-breaker.

`top5_display = TRUE` marks ranks 1–5. Top five is a display limit, not another
biological or statistical threshold.

### Stability

For every driver candidate, Phase 18 removes one fine cell type at a time and
repeats aggregation, correction, candidate assignment, and ranking.

The stability fields report the fractions of assessable repetitions that:

- retain nominal ACAT P at most 0.05;
- retain aggregate q at most 0.05; and
- retain full driver-candidate status.

The evidence tier is:

| Tier | Rule |
|---|---|
| `tier1_recurrent_stable` | Support from at least two fine cell types and nominal significance in at least 80% of assessable repetitions |
| `tier2_localized_or_unstable` | Assessable candidate not meeting Tier 1 |
| `tier_not_assessable` | Candidate with no assessable repetition |
| `not_a_driver_candidate` | Aggregate is not a driver candidate |

Stability is descriptive. It is not a fourth candidate gate.

## Reading the final table

The output is an explicit tested `gene × run` table. Aggregate fields are
repeated when a gene was tested in several runs. Before counting or plotting
candidates, keep one row per:

```text
broad_network + key_driver + case_id
```

Then use:

| Selection | Rule |
|---|---|
| All candidates | `terminal_candidate_status == "driver_candidate"` |
| Figure display list | `top5_display == TRUE` |

The current deduplicated results are:

| Result | Candidate units |
|---|---:|
| All driver candidates | 78 |
| MT driver | 41 |
| non-MT driver | 37 |
| Top-five display records across all represented lists | 47 |

The table contains 104 columns. `tested_by_call_key_drivers` is true for every
row; `significant_by_call_key_drivers` selects the original significant subset.
They are described in
[`call_key_driver_returns_columns_explained.md`](call_key_driver_returns_columns_explained.md).

## Figures after selection

Figures summarize the selected candidates; they do not determine candidate
status.

1. For the two circular figures, deduplicate candidate units and use
   `top5_display`.
2. For sex/APOE or direction evidence, use the individual tested rows and
   distinguish significant from nonsignificant evidence explicitly.
3. For connectivity figures, reconstruct each selected driver's directed
   neighborhood from the Bayesian network and selected layer.

## Interpretation

A Phase 18 driver candidate has adequate broad-network run coverage, at least
one conservative supporting run, and significant combined network-enrichment
evidence.

This supports prioritizing the gene as a possible network-associated regulator
of the AD-related mitochondrial expression program. It does not prove
causality, experimental edge direction, direct regulation of every query gene,
or therapeutic value.

## Reproducibility

The table is generated by
[`18_export_significant_returns.py`](../../scripts/18_export_significant_returns.py)
using
[`phase18_key_driver_selection.yml`](../../config/phase18_key_driver_selection.yml).

The script reads validated Phase 12 results, Phase 09 annotation, and the
Bayesian-network artifacts recorded by Phase 12. It reconstructs complete
explicit test evidence and writes the annotated 95,557-row table.
