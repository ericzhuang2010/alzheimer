# Phase 20 Methods and Threshold Rationale

## Analysis scope

Phase 20 reaggregates frozen Phase 18 key-driver analysis (KDA) evidence for
the 42 categories defined by six sex/APOE groups and seven broad cell types.
It does not regenerate differential-expression data or rerun KDA.

Here, one **run** is one upstream KDA call, not one donor or sample. Within the
Phase 20 primary scope, a run is defined by one fine cell type, one sex/APOE
group, and one mitochondrial AD-versus-NCI signature direction
(`AD_up_mito` or `AD_down_mito`). It uses the Bayesian network for the
corresponding broad cell type. Several runs can therefore contribute to the
same sex/APOE × broad-cell category because that category can contain multiple
fine cell types and both signature directions.

Phase 20 uses exactly 161 unique, frozen Phase 18 runs that passed the Phase 18
inclusion rules, including at least 10 effective query genes: 86
`AD_up_mito` runs and 75 `AD_down_mito` runs. They map to 27 of the 42
sex/APOE × broad-cell categories; the other 15 categories have no included
run. The full run manifest contains 648 planned run slots (54 fine cell types
× 6 sex/APOE groups × 2 directions), but only the 161 rows with
`phase18_included = TRUE` enter Phase 20.

The frozen input contains 1,463,150 gene-run opportunities from those 161
included runs. It is copied byte-for-byte into:

~~~text
results/minerva_production/20_sex_apoe_kda/00_inputs/
~~~

The source and snapshot SHA-256 hashes must match before analysis begins.

## Analysis unit and non-MT eligibility

Phase 20 retains only genes classified in the frozen Phase 18 evidence as
non-core-mitochondrial:

~~~text
case1_core_mito_in_query      -> exclude
case2_core_mito_not_in_query  -> exclude
case3_not_core_mito           -> retain
~~~

Eligible rows must therefore have:

~~~text
case_id = case3_not_core_mito
is_core_mito = FALSE
~~~

The two core-mitochondrial cases are removed before aggregation, BH
correction, ranking, candidate selection, and figure output. Each of the 42
structural categories consequently has one non-MT list or status record rather
than separate MT and non-MT lists. In the 15 categories with no included run,
that list is empty and the category is not estimable.

A **candidate** is a gene evaluated as a possible network key driver: the
gene's directed network neighborhood is tested for enrichment of a run's
mitochondrial query genes. The Phase 20 analysis and counting unit is not a
gene alone. One candidate unit is:

~~~text
current_symbol + signature_group + broad_network
gene symbol    + sex/APOE group  + broad cell type
~~~

Thus, `current_symbol` identifies the gene. A unit that meets a tier's gates
is a passing candidate. The same gene is counted as a separate passing
candidate each time it passes in a different sex/APOE × broad-cell category.
Candidate counts therefore mean gene × category units, not unique gene
symbols.

## Frozen run evidence and cross-run aggregation

For a gene × category unit, the eligible denominator contains every included
run with the same `signature_group` and `broad_network`. Run-level evidence is
handled as follows:

- an explicit frozen test contributes its `final_raw_p`;
- an implicit zero-overlap test contributes `P = 1`; and
- a gene absent from the run background is missing and is omitted from the
  primary aggregation.

Equal-weight ACAT combines the usable P values within the category. The
implementation reproduces the Phase 18 boundary behavior for `P = 0` and
`P = 1`. No run-level P value, q value, query, background, network, or
self-exclusion result is recalculated.

Coverage is:

~~~text
coverage_fraction = usable_run_count / eligible_run_count
~~~

Coverage measures whether the gene has usable test evidence, not the fraction
of runs in which it is significant.

`final_run_q` is the frozen BH-adjusted value within one KDA run. After ACAT,
category-level BH correction is rebuilt separately within each sex/APOE ×
broad-cell category. For each tier, the BH family contains every non-MT gene
that meets that tier's coverage threshold; it is not restricted to genes with
an individually significant run.

## Candidate tiers

### Relaxed Phase 20 main tier

A gene × category unit is a relaxed main candidate only when it meets all of
the following requirements:

~~~text
coverage_fraction >= 0.50

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.10

relaxed_category_acat_q <= 0.10
~~~

This is deliberately a discovery-oriented definition. Tables and figures
must identify the main list as using 50% run coverage and 10% run-level and
category-level FDR thresholds.

### Strict non-MT reference tier

The strict reference uses the same non-MT-only candidate universe and
requires:

~~~text
coverage_fraction >= 0.80

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.05

strict_category_acat_q <= 0.05
~~~

The frozen Phase 18 `conservative_support` flag supplies the strict
supporting-run definition. The strict category BH family contains all non-MT
genes meeting 80% coverage in that category.

### Exploratory-only tier

For broader hypothesis generation, an exploratory-only lead must pass the
relaxed coverage and supporting-run gates but have:

~~~text
0.10 < relaxed_category_acat_q <= 0.20
~~~

These units are retained as exploratory leads, not main Phase 20 candidates.
There are 16 such exploratory-only units. The exploratory-inclusive count
combines the 78 relaxed main candidates with these leads, for 94 units total.

## Threshold choices and rationale

The strict reference and relaxed main tier differ only where a relaxation was
prespecified:

| Component | Strict non-MT reference | Relaxed Phase 20 main | Rationale |
|---|---:|---:|---|
| Candidate universe | Non-MT only | Non-MT only | Fixed Phase 20 scope; core-MT genes are excluded before BH and ranking. |
| Gene coverage | ≥0.80 | ≥0.50 | The relaxed tier requires usable evidence in at least half of the category's runs. |
| Supporting-run q | ≤0.05 | ≤0.10 | One individual run must still provide BH-adjusted support. |
| Aggregated category q | ≤0.05 | ≤0.10 | This is the main discovery-oriented increase in yield. |
| Primary missing-value action | Omit | Omit | Replacing missing values with `P = 1` is evaluated only as a stricter sensitivity analysis. |
| Stability requirement | Non-blocking label | Non-blocking label | Instability changes the evidence label, not main eligibility. |

The following biological and upstream-analysis boundaries are not relaxed:

| Boundary | Retained value | Reason |
|---|---:|---|
| Minimum supporting runs | ≥1 | Allowing zero would admit genes without any individually supported KDA run. |
| Other mitochondrial query genes in a supporting neighborhood | ≥2 | Reducing this to one could call a driver from a single neighboring target. |
| Supporting-run fold enrichment | >1 | A value at or below one is not enrichment. |
| Effective query genes per frozen KDA run | ≥10 | Lowering this would require new upstream KDA evidence rather than a final-step reaggregation. |

## Validated threshold yields, ranking, and display

The executed, validated outputs contain:

| Analysis tier | Candidate units | Categories with a candidate | Top-five units | Top-ten units |
|---|---:|---:|---:|---:|
| Strict non-MT reference | 64 | 14 | 45 | 56 |
| Relaxed Phase 20 main | 78 | 15 | 50 | 65 |
| Exploratory inclusive | 94 | 17 | 53 | 75 |

All counts are non-MT gene × category units. The 78 relaxed main candidate
units represent 37 distinct gene symbols.

Passing candidates are ranked within each sex/APOE × broad-cell category by
relaxed category q, ACAT P, and gene symbol. Every passing candidate is
retained in the machine-readable candidate file; top-five and top-ten files
are presentation subsets and do not change statistical selection.

## Stability and sensitivity

For categories with at least two fine cell types, each fine type is omitted in
turn. Coverage, ACAT, the complete non-MT BH family, support, candidate status,
and rank are recalculated. Single-fine-type categories are labeled rather than
given an artificial cross-fine-type stability estimate.

Prespecified sensitivity outputs include coverage thresholds 0.50, 0.80, and
1.00; missing values replaced by `P = 1`; study-wide BH;
direction-separated aggregation; strict and relaxed supporting-run
definitions; and category q thresholds 0.05, 0.10, and 0.20.

## Interpretation boundaries

The relaxed rule can increase candidate yield only where frozen Phase 18 run
evidence exists; it cannot create evidence in the 15 structural categories
with no included run. A candidate identifies within-category network evidence
for one gene, not a statistically tested difference between sex/APOE groups.
The key-driver label is a statistical network-enrichment result and does not
by itself establish biological causality.

## Validation and executable authorities

The validation-only parity harness aggregates the complete three-case table
without sex/APOE in the key and reproduces all 49,618 archived Phase 18
aggregate rows, 109 candidate units, and 63 top-five flags. The production
path then filters to non-MT case 3.

The release is `validated_complete` only when all blocking checks pass,
including:

- 42 unique structural categories and 161 total included runs;
- 27 analyzable and 15 zero-run categories;
- the strict, relaxed, and exploratory yields shown above;
- unique category-gene units and unique within-category ranks;
- complete non-MT-only BH families; and
- no MT row in any Phase 20 aggregate, candidate, rank, or figure table.

The executable authorities are:

~~~text
config/phase20_sex_apoe_kda.yml
scripts/20_sex_apoe_kda.py
tests/test_phase20_sex_apoe_kda.py
scripts/figures/analysis/phase_20_sex_apoe_kda/render_phase20_summary_figures.R
~~~
