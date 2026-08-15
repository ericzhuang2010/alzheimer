# Unified Selection of Phase 12 Key Drivers

**Phase:** 18 key-driver selection

**Status:** Revised analysis specification; strict case-separated testing still requires a rerun

**Prepared:** 2026-08-14

**Rewritten:** 2026-08-15

## Purpose

This document defines how Phase 12 key-driver analysis (KDA) results should be converted into Phase 18 candidate lists.

The central rule is simple: **analyze the three biological cases separately**. For each case, begin with its own gene × run results, apply the same five filters, combine evidence, correct for multiple testing, and rank genes. Do not pool evidence or false-discovery-rate calculations across cases.

## 1. Core concepts

| Term | Definition |
|---|---|
| **Core mitochondrial gene** | A gene in the fixed 1,136-gene Human MitoCarta3.0 core inventory. |
| **Extended mitochondrial annotation** | A broader project annotation, such as `mito_extended`. It is retained as descriptive information but does not change case assignment. A non-core gene remains in Case 3. |
| **Query** | The core MitoCarta genes altered in AD versus NCI for one fine cell type, sex/APOE group, and direction. The query changes from run to run. |
| **Run** | One fine cell type × one sex/APOE group × one direction, evaluated in the matching broad cell-type network. |
| **Network neighborhood** | The genes connected to or downstream of a candidate gene in the Bayesian network, using the neighborhood selected by KDA. |
| **Gene × run result** | One KDA enrichment test asking whether a candidate gene's neighborhood contains more query genes than expected. |
| **Eligible result** | A gene × run result that belongs to the case being analyzed and whose run passed Filter 1. |
| **Usable result** | An eligible result for which KDA produced a valid, interpretable P value. |
| **Supporting run** | A usable result that meets all conservative run-level criteria in Filter 3. |
| **Candidate unit** | One gene × broad network × case aggregate. This is the unit that receives a final status and rank. |
| **Driver candidate** | A candidate unit that passes coverage, combined-significance, and supporting-run requirements. It is statistical network evidence, not proof of causality. |

KDA uses four counts for each gene × run test:

- `N`: number of genes in the tested background;
- `K`: number of query genes in that background;
- `n`: number of genes in the candidate's network neighborhood; and
- `k`: number of query genes in that neighborhood.

The test reports a hypergeometric P value and fold enrichment:

```text
fold enrichment = (k / n) / (K / N)
```

A fold enrichment above 1 means that query genes are more concentrated in the neighborhood than expected.

## 2. Runs used for primary selection

Primary selection uses only:

- the six independent sex/APOE groups: `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, and `M_e4`;
- the separate `AD_up_mito` and `AD_down_mito` directions;
- validated runs with an original query size of at least 10 genes; and
- the broad network that matches the fine cell type.

It excludes pooled sex/APOE groups and the combined AD-both direction. Those analyses reuse information and should be reserved for sensitivity or descriptive summaries.

The maximum primary grid is:

```text
54 fine cell types × 6 sex/APOE groups × 2 directions = 648 possible runs
```

In the current validated data snapshot, 161 runs remain after the run-level requirements:

| Broad network | Included runs |
|---|---:|
| Astrocyte | 21 |
| Excitatory neuron | 97 |
| Inhibitory neuron | 28 |
| Microglia | 6 |
| Oligodendrocyte precursor cell | 6 |
| Oligodendrocyte | 2 |
| Vasculature | 1 |

These counts describe the current input. They should be recomputed whenever the validated run set changes.

## 3. Assign every gene × run opportunity to one case

Each opportunity receives exactly one case label before case-specific filtering or correction.

| Case | Assignment rule | Biological question |
|---|---|---|
| **Case 1: core mitochondrial and in query** | Gene is in the 1,136-gene core and is present in that run's query. | Does an AD-altered mitochondrial gene connect to other altered mitochondrial genes? |
| **Case 2: core mitochondrial and not in query** | Gene is in the core but absent from that run's query. | Does a mitochondrial gene outside this run's AD signature connect to the altered mitochondrial program? |
| **Case 3: not core mitochondrial** | Gene is outside the 1,136-gene core. | Does a non-core gene connect to, and potentially regulate, the altered mitochondrial program? |

Case membership can change by run for a core mitochondrial gene: it is in Case 1 when it belongs to the query and Case 2 otherwise. A non-core gene is always in Case 3.

After assignment, the analysis branches:

```text
validated runs
    |
    +-- Case 1 gene × run table --> filters --> ACAT --> Case 1 BH --> Case 1 ranks
    +-- Case 2 gene × run table --> filters --> ACAT --> Case 2 BH --> Case 2 ranks
    +-- Case 3 gene × run table --> filters --> ACAT --> Case 3 BH --> Case 3 ranks
```

No P values, q values, candidate lists, or ranks should be combined across these branches.

## 4. The five filters

The filters act at different levels. This distinction is important.

| Filter | Acts on | Purpose |
|---|---|---|
| **1. Run eligibility** | Run | Select the common, valid primary runs. |
| **2. Test validity** | Gene × run result | Decide whether an individual test is usable. |
| **3. Conservative support** | Gene × run result | Label convincing evidence from one run. It does not delete valid non-supporting results. |
| **4. Coverage** | Gene × network × case | Require enough usable results across eligible runs. |
| **5. Combined evidence** | Gene × network × case | Combine all usable P values and identify final candidates. |

### Filter 1: Select eligible runs

A run is included only if it satisfies all requirements in Section 2. This filter removes runs, not genes.

Runs removed here are not counted in any later coverage denominator.

### Filter 2: Require a valid gene × run test

An eligible result is usable when:

- the gene is in the run's tested background and matching broad network;
- the query, background, neighborhood, and overlap counts are logically valid; and
- a valid P value from 0 to 1 can be calculated.

Keep the difference between a null result and a missing test:

| Stored value | Meaning | Used by ACAT? | Counts as usable? |
|---|---|---:|---:|
| `P = 1` | The test was completed and found no enrichment. | Yes | Yes |
| `NA` | The test could not be performed or interpreted. | No | No |

#### Case 1 self-overlap correction

In Case 1, the candidate belongs to both the query and its own KDA neighborhood. That creates one guaranteed overlap. Remove that self-match before evaluating the gene:

```text
N_corrected = N - 1
K_corrected = K - 1
n_corrected = n - 1
k_corrected = k - 1
```

Then recompute the P value and fold enrichment. This asks whether the candidate reaches **other** query genes. If no enrichment remains, keep the valid result as `P = 1`; do not convert it to `NA`.

Cases 2 and 3 use the original counts because the candidate is not in the query.

After this correction, recalculate run-level Benjamini-Hochberg (BH) q values **separately within each run × case**. This keeps the three hypothesis families separate.

### Filter 3: Label conservative supporting runs

A usable gene × run result is a supporting run only when all four conditions hold:

1. the original run query contains at least 10 genes, as already required by Filter 1;
2. the candidate's neighborhood contains at least two other query genes;
3. fold enrichment is greater than 1; and
4. the case-specific run-level q value is at most 0.05.

For Case 1, use the self-corrected overlap, fold enrichment, P value, and q value. For Cases 2 and 3, use the original values.

A usable result that fails these criteria remains in the case table and still enters ACAT. Filter 3 adds a support label; it does not keep only significant results.

### Filter 4: Require at least 80% coverage

Filter 4 asks one question:

> Was this gene successfully tested in at least 80% of the runs where it should have been tested?

For one gene × broad network × case:

```text
coverage = number of usable results / number of eligible results
```

The denominator is case-specific:

- **Case 1:** included runs in that broad network where the core gene is in the query;
- **Case 2:** included runs in that broad network where the core gene is not in the query; and
- **Case 3:** all included runs in that broad network, because a non-core gene always belongs to Case 3.

Examples:

- 8 usable results out of 10 eligible results gives 80% coverage and passes.
- 7 usable results out of 10 gives 70% and fails.
- A valid `P = 1` result is usable and counts in the numerator.
- An `NA` result is eligible but not usable, so it lowers coverage.
- A run removed by Filter 1 is not eligible and is absent from both numerator and denominator.

If a gene has no eligible results for a case, that gene × network × case combination is not assessed.

### Filter 5: Require significant combined evidence

For each gene × broad network × case, combine **all usable P values** with the aggregated Cauchy association test (ACAT).

ACAT must include:

- significant P values;
- non-significant P values; and
- valid null values of `P = 1`.

Omit only `NA` values from the primary ACAT calculation. Exact boundary values should be handled with a numerically stable implementation without changing their interpretation.

Next, apply BH correction to the ACAT P values **separately within each broad network × case**. For example, Astrocyte Case 1, Astrocyte Case 2, and Astrocyte Case 3 are three different correction families.

A gene × broad network × case result is a final driver candidate when it has:

- coverage of at least 80%;
- aggregate ACAT q ≤ 0.05; and
- at least one conservative supporting run from Filter 3.

Suggested result labels are:

| Status | Rule |
|---|---|
| **Driver candidate** | Passes coverage, aggregate q, and supporting-run requirements. |
| **Exploratory signal** | Passes coverage and has raw ACAT P ≤ 0.05, but does not pass all final-candidate requirements. |
| **Not supported** | Has adequate coverage but does not meet either rule above. |
| **Insufficient coverage** | Coverage is below 80%. |
| **Not assessed** | No eligible results exist. |

## 5. Ranking candidates

Rank final candidates separately within each broad network × case by:

1. ascending aggregate ACAT q value;
2. ascending aggregate ACAT P value; and
3. gene symbol, alphabetically, as the deterministic tie-breaker.

Supporting-run count, recurrence, fine-cell-type breadth, and sex/APOE pattern should be reported as evidence annotations. They should not silently replace the prespecified statistical ranking.

“Top five” is a display limit, not a biological threshold. A circular figure may show the first five ranked candidates per broad cell type, but the complete table must retain every candidate.

## 6. Required outputs

Produce separate outputs for Cases 1, 2, and 3.

### Complete candidate table

At minimum, report:

- gene symbol and stable gene identifier;
- broad network and case;
- core and extended mitochondrial annotations;
- eligible, usable, and supporting-run counts;
- coverage;
- aggregate ACAT P and case-specific q values;
- fine-cell-type, sex/APOE, and direction breadth;
- final status and within-case rank; and
- the contributing run identifiers.

### Main figures

- one circular summary per case, showing at most five genes per broad cell type;
- one sex/APOE evidence figure for selected genes; and
- focused network figures showing how selected genes connect to query genes.

The figures summarize the complete tables; they do not define candidate status.

### Audit output

Retain a gene × run audit table containing case assignment, eligibility, usability, original values, Case 1 corrected values, support status, and exclusion reason. This makes every aggregate result traceable to its contributing tests.

## 7. Robustness checks

The primary result uses `NA` omission, 80% coverage, and ACAT. Test whether conclusions change under:

- treating missing eligible results as `P = 1`;
- coverage thresholds of 50%, 80%, and 100%;
- leave-one-fine-cell-type-out aggregation;
- degree-matched network nulls; and
- an alternative P-value combination method.

These checks assess stability. They should not replace the frozen primary rule after results are inspected.

## 8. Interpretation

The analysis can support statements such as:

- a gene's Bayesian-network neighborhood is enriched for an AD-associated mitochondrial query;
- the signal recurs across defined runs; or
- the signal is specific to a broad cell type, sex/APOE group, or direction.

It cannot by itself prove that the gene causes AD, directly regulates every connected gene, or is a therapeutic target. Bayesian-network direction and KDA enrichment are prioritization evidence that require biological validation.

## 9. Implementation note

Strict separation means that both run-level BH correction and aggregate BH correction use case-specific hypothesis families. Because this requirement changes the q values, existing Phase 18 candidate tables and figures should not be treated as compliant with this specification until the analysis is rerun and validated under the revised rule.
