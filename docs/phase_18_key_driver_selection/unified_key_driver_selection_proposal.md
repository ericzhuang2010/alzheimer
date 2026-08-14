# Proposal: A Consistent, Data-Driven Way to Select Phase 12 Key Drivers

**Status:** Revised proposal; not yet implemented
**Prepared:** 2026-08-14

## Executive recommendation

Phase 12 should begin with **all genes that were tested** and process them in three steps:

1. Divide every gene × run result into one of three mutually exclusive cases.
2. Apply prespecified filters to decide which genes qualify as driver candidates.
3. Sort the remaining candidates using the same transparent evidence measures.

The three cases are:

1. The driver is one of the 1,136 MitoCarta core genes **and is in that run's mitochondrial query**.
2. The driver is one of the 1,136 MitoCarta core genes **and is not in that run's mitochondrial query**.
3. The driver is **not** one of the 1,136 MitoCarta core genes.

These cases should be analyzed and displayed separately. They answer different biological questions and should not compete in one undifferentiated “top five genes” list.

## Definitions used in this proposal

### What “MT-related” means

For this proposal, **MT-related gene** means a gene in the fixed 1,136-gene Human MitoCarta3.0 core inventory.

The inventory contains:

- 13 genes encoded by mitochondrial DNA; and
- approximately 1,123 mitochondrial genes encoded by nuclear DNA.

The 13 mitochondrial-DNA-encoded protein genes are:

MT-ATP6, MT-ATP8, MT-CO1, MT-CO2, MT-CO3, MT-CYB, MT-ND1, MT-ND2, MT-ND3, MT-ND4, MT-ND4L, MT-ND5, and MT-ND6.

Some project annotations use a broader category called <code>mito_extended</code>. Those genes are outside the 1,136-gene core inventory, so they belong to Case 3 under the definition above. Their extended mitochondrial annotation should still be retained as an additional label.

### What the query is

A **query** is the smaller set of MitoCarta core genes that changed in AD versus NCI in one particular analysis.

Each run represents one:

- fine cell type;
- sex/APOE analysis group;
- direction of AD change; and
- matching broad cell network.

Phase 12 contains six primary sex/APOE groups:

| Primary group ID | Sex | APOE group |
|---|---|---|
| <code>F_e2</code> | Female | APOE e2 |
| <code>F_e33</code> | Female | APOE e3/e3 |
| <code>F_e4</code> | Female | APOE e4 |
| <code>M_e2</code> | Male | APOE e2 |
| <code>M_e33</code> | Male | APOE e3/e3 |
| <code>M_e4</code> | Male | APOE e4 |

It also contains five secondary pooled groups:

| Secondary group ID | Samples combined |
|---|---|
| <code>female_pool</code> | All three female APOE groups |
| <code>male_pool</code> | All three male APOE groups |
| <code>e2_pool</code> | Female and male APOE e2 groups |
| <code>e33_pool</code> | Female and male APOE e3/e3 groups |
| <code>e4_pool</code> | Female and male APOE e4 groups |

The complete Phase 12 production grid has 1,782 runs:

~~~text
54 fine cell types
× 11 analysis groups (6 primary + 5 secondary)
× 3 directions (AD-up, AD-down, and AD-both)
= 1,782 runs
~~~

The proposed primary driver selection uses only the six primary groups and the separate AD-up and AD-down directions. The five secondary pooled groups and AD-both runs remain available for sensitivity or descriptive analyses, but they are not mixed into the primary ranking.

The query therefore changes between runs. The 1,136-gene MitoCarta inventory is fixed, but membership in a particular run's query is not fixed.

### What a candidate driver is

KDA, or **key driver analysis**, asks whether a candidate gene's network neighborhood contains more query genes than expected by chance.

A **network neighborhood** is the set of genes connected to or downstream of the candidate in the inferred gene network.

“Candidate driver” means that the gene has passed the statistical and reproducibility filters defined below. It does not prove that the gene causes Alzheimer's disease or mitochondrial dysfunction.

## Step 1: Divide every result into three cases

Every gene × run result should receive exactly one case label.

| Case | Exact rule | Question answered | Interpretation |
|---|---|---|---|
| **Case 1: MT-related and in query** | <code>in_core_mito = yes</code> and <code>driver_in_query = yes</code> | Does an AD-altered mitochondrial gene connect to other AD-altered mitochondrial genes? | The candidate is part of the input signature, so its own contribution must be removed before judging downstream evidence. |
| **Case 2: MT-related and not in query** | <code>in_core_mito = yes</code> and <code>driver_in_query = no</code> | Does a mitochondrial gene that was not selected into this run's AD query connect to the altered mitochondrial program? | Query-independent evidence for a mitochondrial component or regulator. |
| **Case 3: not MT-related** | <code>in_core_mito = no</code> | Does a gene outside the 1,136-gene MitoCarta core set connect to the altered mitochondrial program? | Best case for discovering candidate regulators outside the queried mitochondrial program. |

Because every Phase 12 query is drawn from the 1,136 MitoCarta genes, a Case 3 gene cannot be in the query. Therefore, Case 3 does not need a second query-membership subdivision.

### Why Case 1 needs special handling

The Phase 12 fKDA method includes the candidate driver itself in the tested neighborhood. If the candidate is also in the query, it automatically contributes one overlap to its own enrichment result. This is called **self-overlap**.

For example:

~~~text
The query contains 10 genes.
The candidate is one of those 10 genes.
The candidate reaches 1 other query gene.

Reported overlap = 1 candidate itself + 1 other query gene = 2.
Independent downstream overlap = 1 other query gene.
~~~

The reported overlap of two can look stronger than the independent downstream evidence of one. In the validated Phase 12 results, 5,349 of 10,172 result rows, or 52.6%, have a driver that is also in the query. This is therefore a major feature of the data, not a rare edge case.

Case 1 results should not be discarded automatically. A query-member gene may genuinely connect to several other altered mitochondrial genes. Instead, recompute its enrichment after removing the driver's guaranteed self-contribution.

For a Case 1 row, subtract the driver once from:

- the total background size;
- the query size;
- the neighborhood size; and
- the query–neighborhood overlap.

Then recompute the enrichment P value using the remaining genes. This **self-excluded P value** asks whether the driver reaches other query genes, rather than rewarding the driver for matching itself.

For Cases 2 and 3, no subtraction is needed because the driver is not in the query.

## Step 2: Filter genes to obtain driver candidates

Filtering and sorting serve different purposes:

- **Filtering** defines the minimum evidence required to call a gene a candidate.
- **Sorting** orders candidates that have already passed those minimum requirements.

The filters should be defined before inspecting the resulting ranks.

### Filter 1: Use a common set of Phase 12 runs

For primary driver selection, use **only the six primary sex/APOE groups and only the separate AD-up and AD-down mitochondrial queries**.

This gives a maximum starting set of 648 runs before the query-size and other quality filters are applied:

~~~text
54 fine cell types
× 6 primary sex/APOE groups
× 2 directions (AD-up and AD-down)
= 648 possible primary-selection runs
~~~

Specifically, include only:

- primary Phase 12 analyses only;
- the six primary sex/APOE groups: <code>F_e2</code>, <code>F_e33</code>, <code>F_e4</code>, <code>M_e2</code>, <code>M_e33</code>, and <code>M_e4</code>;
- AD-up and AD-down mitochondrial queries;
- validated runs with an effective query size of at least 10 genes; and
- the matching broad cell network.

Explicitly exclude from primary candidate selection:

- the five secondary pooled groups: <code>female_pool</code>, <code>male_pool</code>, <code>e2_pool</code>, <code>e33_pool</code>, and <code>e4_pool</code>; and
- the combined AD-both query direction.

The secondary groups reuse samples from the six primary groups, and AD-both reuses information from the separate directional queries. Including them together in the primary ACAT calculation would count related evidence more than once. Analyze them separately as sensitivity or descriptive results.

### Filter 2: Require a valid, interpretable test

Filter 2 is a **data-validity filter**, not a significance filter. It asks whether a gene × run result is trustworthy enough to use in the later candidate-selection calculations.

#### 2A. Confirm that the driver was testable in the run

The driver must be present in the run's tested gene background. This means that the gene was sufficiently represented in the corresponding fine cell type and sex/APOE comparison to be included in the analysis.

If a driver was not measured or could not be tested, store its result as missing, or <code>NA</code>. Do not replace an unperformed test with P = 1, because P = 1 means that a valid test was performed and found no enrichment.

#### 2B. Confirm that the network test was constructed correctly

The candidate must exist in the matching broad cell network, and its downstream neighborhood must have been constructed successfully.

A valid neighborhood with no query-gene overlap is still a valid null result. Retain it with P = 1. It is different from a missing test:

| Situation | Stored value | Meaning |
|---|---|---|
| Test completed but found no enrichment | P = 1 | Valid evidence against enrichment in that run |
| Test could not be performed | <code>NA</code> | No evidence was generated |

#### 2C. Confirm that the run passed quality checks

The query, background, network, and enrichment calculation must be internally valid. At minimum:

- query genes must map correctly to the tested background;
- network genes must use valid and consistent identifiers;
- the query, neighborhood, overlap, and background counts must be logically consistent;
- the run must satisfy the Phase 12 validation checks; and
- the raw enrichment P value must be a valid number between 0 and 1.

A failed or malformed result should be stored as untestable and must not enter ACAT.

#### 2D. Remove the guaranteed self-overlap from Case 1

In Case 1, the driver belongs to the query and the Phase 12 fKDA method includes the driver in its own neighborhood. The original enrichment result therefore contains one guaranteed overlap.

Remove the driver once from all four enrichment counts:

~~~text
self-excluded background size   = original background size − 1
self-excluded query size        = original query size − 1
self-excluded neighborhood size = original neighborhood size − 1
self-excluded overlap count     = original overlap count − 1
~~~

Then recalculate both the enrichment P value and fold enrichment from the self-excluded counts.

For example:

~~~text
Original overlap:
1 driver itself + 2 other query genes = 3

Self-excluded overlap:
2 other query genes
~~~

For Cases 2 and 3, use the original counts and ordinary P value because the driver is not in the query.

If removing the Case 1 driver leaves no remaining neighborhood genes or no overlap with the remaining query, retain the result as a valid null test with P = 1 rather than marking it missing.

#### 2E. Recalculate run-level q values

After all Case 1 P values have been replaced with their self-excluded P values, apply Benjamini-Hochberg multiple-testing correction again across all tested drivers within each run.

The q values must be recalculated because each q value depends on:

- all P values in the run;
- the number of genes tested; and
- the relative ordering of the P values.

The existing run-level q values are no longer valid after the Case 1 P values change.

The resulting **q value** is the multiple-testing-adjusted P value. It controls the expected fraction of false discoveries among the reported genes.

#### Output of Filter 2

Filter 2 does not require statistical significance. Valid non-significant P values must remain in the data because ACAT needs favorable, weak, and null evidence.

After Filter 2, every gene × run result has one of these outcomes:

| Filter 2 outcome | Value carried forward |
|---|---|
| Valid Case 1 test | Self-excluded P value and self-excluded fold enrichment |
| Valid Case 2 or Case 3 test | Original P value and fold enrichment |
| Valid test with no enrichment | P = 1 |
| Invalid or untestable result | <code>NA</code> |

Statistical support is evaluated later under Filters 3 and 5.

### Filter 3: Define conservative run-level support

Filter 3 asks whether **one individual run provides convincing support for a driver**. It does not produce the final driver list; evidence is combined across runs later under Filter 5.

A run counts as conservative support only when all four conditions below are satisfied.

#### 3A. The effective query contains at least 10 genes

The query is the set of mitochondrial genes altered in AD for that fine cell type × sex/APOE group × direction.

Very small queries produce unstable enrichment results. For example, if a query contains only three genes, reaching one gene represents one-third of the entire query and can produce an apparently impressive result from very little information.

Requiring at least 10 query genes removes the smallest and most fragile tests. Filter 1 already applies this threshold to the primary run set; repeating it here ensures that no smaller-query sensitivity run can accidentally count as conservative support.

#### 3B. The driver reaches at least two other query genes

The driver's network neighborhood must contain at least two query genes other than the driver itself.

Apply the rule as follows:

- Case 1: subtract the driver's self-overlap. The original reported overlap must be at least three to leave two other query genes.
- Case 2: use the reported overlap directly because the driver is not in the query.
- Case 3: also use the reported overlap directly because the driver cannot be in the core mitochondrial query.

Case 1 passing example:

~~~text
Reported overlap       = 3
                       = driver itself + 2 other query genes
Self-excluded overlap = 2
Result passes the overlap requirement.
~~~

Case 1 failing example:

~~~text
Reported overlap       = 2
                       = driver itself + 1 other query gene
Self-excluded overlap = 1
Result fails the overlap requirement.
~~~

Requiring two other query genes prevents a candidate from receiving conservative support from only one network connection and avoids giving Case 1 an easier threshold.

#### 3C. Fold enrichment is greater than 1

Fold enrichment compares the proportion of query genes inside the driver's neighborhood with the proportion of query genes in the complete tested background:

~~~text
                  query genes in neighborhood / neighborhood size
fold enrichment = ────────────────────────────────────────────────
                       total query genes / background size
~~~

Interpret fold enrichment as follows:

- Fold enrichment = 1 means no enrichment.
- Fold enrichment > 1 means query genes are more concentrated around the driver than expected.
- Fold enrichment < 1 means query genes are less concentrated around the driver than expected.

For Case 1, calculate fold enrichment using the self-excluded counts from Filter 2. This condition ensures that a statistically significant result represents enrichment in the intended direction.

#### 3D. The run-level q value is no greater than 0.05

Each run tests many candidate drivers, so some genes will have small raw P values by chance. The Benjamini-Hochberg q value corrects for these multiple tests.

Requiring q ≤ 0.05 means that the run-level result remains significant after accounting for the number of candidate drivers tested. For Case 1, use the recalculated q value based on the self-excluded P values.

#### Output of Filter 3

For every valid gene × run result:

~~~text
All four conditions pass → conservative supporting run
Any condition fails      → not a conservative supporting run
~~~

The supporting runs are used to calculate:

- number of conservative supporting runs;
- recurrence across tested runs;
- fine-cell-type breadth; and
- whether the gene has at least one conservative supporting run, as required by Filter 5.

A valid run that fails Filter 3 is **not deleted**. Its P value still enters the later ACAT calculation. Keeping favorable, weak, and null evidence prevents the combined analysis from using only significant results.

### Filter 4: Require adequate coverage across runs

Filter 4 asks whether a gene was evaluated often enough for its combined ACAT result to be trustworthy. It is a **data-completeness filter**, not a significance filter.

#### 4A. What one gene-level test means

A **test** is one KDA enrichment calculation for one candidate gene in one Phase 12 run:

~~~text
one candidate gene × one Phase 12 run = one gene-level KDA test
~~~

For example:

~~~text
Run:       astrocyte subtype × Female APOE e4 × AD-up query
Candidate: RPL11
Question:  Are AD-up mitochondrial query genes unusually concentrated
           in RPL11's downstream network neighborhood?
~~~

For each candidate, KDA uses:

- background size: number of genes in the run's tested background;
- query size: number of AD-associated mitochondrial query genes;
- neighborhood size: number of genes in the candidate's directed network neighborhood; and
- overlap count: number of query genes in that neighborhood.

KDA evaluates directed neighborhoods up to three network layers and retains the best layer for the candidate. It reports fold enrichment, a raw hypergeometric P value, and a run-level Benjamini-Hochberg-adjusted q value.

#### 4B. What counts as a usable test result

A gene has a usable test result when:

1. the run passed Filter 1 and the Phase 12 run-level quality checks;
2. the gene is present in that run's tested background;
3. the gene and network identifiers are valid;
4. the neighborhood, query, overlap, and background counts are internally possible; and
5. a P value between 0 and 1 can be assigned.

A usable result can be significant, non-significant, or completely null.

Example of a usable enriched test:

~~~text
Background genes:              7,000
Query genes:                      20
Neighborhood genes:               50
Query genes in neighborhood:        4
~~~

KDA can calculate an enrichment P value from these counts, so this is a usable test.

If a gene is present in the tested background but has no usable query overlap, the complete Phase 12 candidate table records an implicit zero-overlap result:

~~~text
candidate_test_status = implicit_zero_overlap
P value = 1
~~~

This is also a usable test. It is valid evidence that the gene did not show enrichment in that run.

#### 4C. When no usable gene-level test exists

**Gene absent from the tested background:** The gene was not testable in that fine cell type and contrast or was absent from the run-specific induced network. No gene-level P value can be calculated, so store <code>NA</code>.

**Entire run ineligible:** The run may have an insufficient query, an unvalidated source contrast, an empty induced network, or another failed run-level quality check. Such a run is excluded before coverage is calculated and is not part of the denominator.

**Malformed or failed calculation:** Examples include an overlap larger than the query or neighborhood, a neighborhood larger than the background, duplicated gene/run records, an invalid P value, or a computation failure. Store the result as <code>NA</code>. The validated Phase 12 production report had zero failed runs, but the revised workflow should still check for these conditions.

#### 4D. Calculate coverage

For each gene, broad network, and case, calculate:

~~~text
           eligible runs with a usable gene-level result
coverage = ─────────────────────────────────────────────
              eligible runs for that network and case
~~~

For example:

~~~text
Eligible runs: 100
Usable tests:   85
Coverage:       85 / 100 = 0.85
~~~

This gene passes the proposed 80% coverage threshold. A gene with one very small P value but usable results in only 40 of 100 eligible runs has 40% coverage and fails.

The denominator is gene- and case-specific:

- Case 1 includes runs in which that MitoCarta gene is in the query.
- Case 2 includes runs in which that MitoCarta gene is not in the query.
- Case 3 includes all otherwise eligible runs because a non-MitoCarta gene cannot enter the core mitochondrial query.

A MitoCarta gene can therefore have one Case 1 aggregate and a separate Case 2 aggregate. Do not pool evidence from the two cases.

Always report the numerator and denominator as well as the fraction. For example, 4/5 and 80/100 both equal 80%, but the second estimate is based on substantially more information.

#### 4E. Distinguish P = 1 from missing data

| Situation | Count in coverage denominator? | Count in coverage numerator? | Value supplied to primary ACAT |
|---|---:|---:|---|
| Run excluded by Filter 1 | No | No | Not included |
| Eligible run; gene has an explicit KDA result | Yes | Yes | Calculated P value |
| Eligible run; gene has an implicit zero-overlap result | Yes | Yes | P = 1 |
| Eligible run; gene is absent from the tested background | Yes | No | <code>NA</code> |
| Eligible run; gene-level calculation fails | Yes | No | <code>NA</code> |

The essential distinction is:

~~~text
P = 1 → the gene was evaluated and showed no enrichment
NA    → the gene could not be evaluated
~~~

For example:

~~~text
100 eligible runs
80 usable P values, including 20 values equal to 1
20 untestable values recorded as NA

Coverage = 80 / 100 = 0.80
~~~

The gene passes coverage, and all 80 usable P values—including the P = 1 results—enter the primary ACAT calculation.

#### 4F. Apply the threshold and sensitivity analyses

Require coverage of at least 0.80 for the primary analysis. Passing means that the gene has sufficiently complete testing across its relevant runs; it does not mean that the gene is significant or recurrent.

After a gene passes the 80% gate:

1. combine all usable P values with ACAT, including P = 1 results; and
2. omit genuine <code>NA</code> values from the primary ACAT calculation.

This avoids treating technical inability to evaluate a gene as biological evidence against it. As a conservative sensitivity analysis, replace the remaining <code>NA</code> values with P = 1 and repeat ACAT. A gene that remains strong under both approaches is less dependent on missing-data handling.

The 80% threshold is a prespecified compromise, not a biological constant. Repeat the analysis at coverage thresholds of 0.50, 0.80, and 1.00 to show whether conclusions depend strongly on this choice; retain 0.80 as the primary threshold.

### Filter 5: Require significant combined evidence

For every broad network × gene × case:

1. Combine all valid tested run-level P values with ACAT.
2. Include non-significant P values as well as significant ones.
3. Do not combine only the favorable runs.
4. Apply Benjamini-Hochberg correction to the resulting gene-level ACAT P values across all tested gene × case combinations within that broad network.

ACAT, the **aggregated Cauchy association test**, produces one combined P value from a gene's evidence across runs.

A gene becomes a Phase 12 driver candidate only if all of the following are true:

- coverage is at least 0.80;
- the gene has at least one conservative supporting run; and
- the gene-level ACAT q value is no greater than 0.05.

The same hard filters apply to all three cases. The only special operation is removing self-overlap before testing Case 1.

### Candidate status after filtering

| Status | Rule |
|---|---|
| **Driver candidate** | Coverage ≥ 0.80, at least one conservative run, and ACAT q ≤ 0.05 |
| **Exploratory signal** | Coverage ≥ 0.80 and raw ACAT P ≤ 0.05, but ACAT q > 0.05 |
| **Insufficient coverage** | Coverage < 0.80 |
| **Not supported** | Adequate coverage but no conservative run or raw ACAT P > 0.05 |

Exploratory signals should remain in the supplementary table but should not be displayed as selected drivers in the main figure.

## Step 3: Sort the remaining driver candidates

Sorting must occur **within each of the three cases**. The workflow should produce three independent ranked lists for every broad network:

1. a Case 1 ranking containing only MT-related drivers that are in the query;
2. a Case 2 ranking containing only MT-related drivers that are not in the query; and
3. a Case 3 ranking containing only drivers outside the 1,136-gene MitoCarta core set.

There must be no single combined rank across Cases 1, 2, and 3.

Do not compare a Case 1 query-member mitochondrial gene directly with a Case 3 non-MitoCarta gene for one shared rank. The two genes answer different questions.

### Measures used for sorting

For every candidate, calculate:

- **ACAT q value:** overall statistical evidence after multiple-testing correction;
- **fine-cell-type breadth:** number of distinct fine cell types with conservative support;
- **recurrence:** conservative supporting runs divided by tested runs;
- **leave-one-fine-cell-type-out stability:** whether the combined result remains when each fine cell type is removed in turn;
- **median fold enrichment:** typical magnitude of enrichment across supporting runs, using the self-excluded fold enrichment for Case 1; and
- **coverage:** completeness of testing across eligible runs.

The leave-one-fine-cell-type-out check identifies genes whose combined evidence is driven almost entirely by one subtype.

### Evidence tiers

Assign an evidence tier before sorting:

| Tier | Rule | Meaning |
|---|---|---|
| **Tier 1: recurrent and stable** | Candidate filter passed; conservative support in at least two fine cell types; nominal ACAT P ≤ 0.05 in at least 80% of leave-one-fine-cell-type-out repeats | Strongest repeated evidence |
| **Tier 2: significant but localized** | Candidate filter passed, but support occurs in only one fine cell type or fails the stability requirement | Statistically supported but context-specific |

If a network contains too few eligible fine cell types to evaluate breadth or leave-one-out stability, mark stability as **not assessable** rather than treating it as failure.

### Exact sorting order

Within each broad network, apply the following sorting order independently to Case 1, Case 2, and Case 3 candidates:

1. Tier 1 before Tier 2.
2. Smaller gene-level ACAT q value.
3. Greater fine-cell-type breadth.
4. Higher recurrence.
5. Larger median fold enrichment.
6. Higher coverage.
7. Gene symbol alphabetically as the final deterministic tie-breaker.

This is a **lexicographic ranking**: apply the first rule, use the second rule only to order genes within the same tier, then continue down the list. It is not a weighted score. Readers can therefore see exactly why one gene ranks above another.

### The “top five” rule

“Top five” should be a display limit only, not a candidate-selection criterion.

- If more than five genes pass, display the first five and publish all candidates in the supplementary table.
- If fewer than five genes pass, display only the genes that passed.
- If no gene passes, state that no gene met the prespecified criteria.

Never fill an empty position with a gene that failed the candidate filters.

## Recommended outputs

### Main summary figure

Show separate sections or panels for:

- **Case 1:** MT-related, query-member candidates evaluated with self-excluded enrichment;
- **Case 2:** MT-related, query-independent candidates; and
- **Case 3:** candidates outside the 1,136-gene MitoCarta core set.

Case 3 should be the primary panel for claims about regulators outside the queried mitochondrial program. Case 2 provides mitochondrial regulator or component candidates. Case 1 describes mitochondrial genes that are themselves altered in AD but also reach other altered mitochondrial genes after self-overlap is removed.

Use a separate annotation to show whether a gene is mtDNA encoded, nuclear encoded, or labeled <code>mito_extended</code>. Genome origin is useful biological information but does not replace the three-case classification.

### Sex/APOE heatmap

Use the same candidates selected by the three-case workflow. The heatmap should show which sex/APOE runs contribute to each candidate's overall result.

Do not select a new heatmap gene list from the manually curated set of 14 genes.

### Complete supplementary table

The master table should contain at least:

| Column | Purpose |
|---|---|
| Broad network, fine cell type, group, direction, and gene | Identifies the result |
| <code>in_core_mito</code> | Identifies membership in the 1,136-gene MitoCarta core set |
| <code>driver_in_query</code> | Distinguishes Case 1 from Case 2 |
| Three-case label | Makes the analysis branch explicit |
| Genome origin and extended mitochondrial annotation | Preserves additional biological information |
| Original and self-excluded overlap counts | Makes the Case 1 correction visible |
| Original and self-excluded P values | Shows the impact of removing self-overlap |
| Recomputed run-level q value | Reports multiple-testing-adjusted run evidence |
| Eligible runs, tested runs, and coverage | Shows data completeness |
| Conservative-support count and recurrence | Shows repeated run-level support |
| Fine-cell-type breadth | Shows whether evidence spans subtypes |
| ACAT P value and gene-level q value | Reports aggregate evidence |
| Leave-one-fine-cell-type-out stability | Identifies subtype-driven results |
| Median fold enrichment | Reports evidence magnitude, not only significance |
| Candidate status, evidence tier, and final rank | Makes selection reproducible |

## Robustness checks

### Network-hub sensitivity

Highly connected genes have more opportunities to reach query genes. The enrichment calculation accounts for neighborhood size, but additional degree-matched permutations should test whether highly ranked genes remain unusual compared with genes having similar network connectivity.

A **degree-matched permutation** compares a candidate with randomized genes or queries having similar numbers of network connections.

### Missing-data sensitivity

Compare:

- primary ACAT with true missing values omitted after the 80% coverage gate; and
- conservative ACAT with missing values replaced by P = 1.

Candidates that pass under both approaches are less sensitive to missing tests.

### Coverage sensitivity

Repeat the ranking at coverage thresholds of 0.50, 0.80, and 1.00. The 0.80 analysis remains primary; the alternatives show whether rankings depend strongly on the chosen threshold.

### Alternative aggregation

Compare ACAT with the existing mean-of-log-P method. This is a sensitivity check, not an opportunity to choose whichever method gives the preferred genes.

## Plain-language statistical glossary

| Term | Meaning |
|---|---|
| **P value** | How surprising the result would be if there were no enrichment. Smaller values indicate stronger evidence but do not prove causality. |
| **q value/FDR-adjusted P value** | A P value corrected because many genes were tested. It limits the expected proportion of false discoveries among selected genes. |
| **ACAT** | A method that combines several run-level P values into one overall P value for a gene. |
| **Fold enrichment** | How concentrated query genes are in a driver's neighborhood compared with the full background. It describes magnitude, whereas the P value describes statistical evidence. |
| **Coverage** | The fraction of eligible runs in which a gene was actually tested. |
| **Recurrence** | The fraction of tested runs that provide conservative significant support. |
| **Fine-cell-type breadth** | The number of different fine cell types providing conservative support. |
| **Self-overlap** | The guaranteed overlap created when the candidate driver is itself in the query and is included in its tested neighborhood. |
| **Multiple-testing correction** | An adjustment that reduces false-positive findings when many genes are examined. |
| **Sensitivity analysis** | Repeating the analysis under a reasonable alternative rule to determine whether conclusions are stable. |

## Minimum implementation requirements

The revised workflow is complete when:

1. all tested genes enter the initial analysis;
2. every result receives exactly one of the three case labels;
3. Case 1 enrichment is recomputed after removing self-overlap;
4. run-level multiple-testing correction is recomputed after changing the P values;
5. the same conservative support, coverage, and aggregate significance filters are applied to all cases;
6. candidates are sorted separately by broad network and case;
7. the ranking follows the documented tier and tie-breaking order;
8. “top five” is used only as a display cap;
9. the circular and sex/APOE figures use the same selected candidates; and
10. a complete table documents every inclusion, exclusion, and rank.

## Claims the analysis can and cannot support

This analysis can identify genes with statistically supported and reproducible network connections to AD-associated mitochondrial expression.

It cannot establish that a selected gene causes Alzheimer's disease, directly regulates mitochondria, or is a therapeutic target. Those conclusions require independent datasets and functional experiments.

## Recommended decision

Adopt the three-case workflow as the Phase 12 standard:

1. classify every tested result;
2. remove Case 1 self-overlap and apply common candidate filters; and
3. sort the surviving candidates separately within each broad network and case.

Keep biological literature as an interpretation and experimental-prioritization layer after the data-driven selection is complete.
