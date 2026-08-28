# Phase 20 Relaxed Non-MT Key-Driver Thresholds

## Scope

Phase 20 will produce only non-MT key drivers. A driver must be classified in
the frozen Phase 18 evidence as:

~~~text
case3_not_core_mito
~~~

The two core-mitochondrial cases are excluded before aggregation, BH
correction, ranking, and output:

~~~text
case1_core_mito_in_query      -> exclude
case2_core_mito_not_in_query  -> exclude
case3_not_core_mito           -> retain
~~~

Each of the 42 sex/APOE × broad-cell categories therefore has one non-MT
driver list rather than separate MT and non-MT lists.

## What the earlier strict rule meant

The earlier rule was:

~~~text
coverage >= 0.80
strict Phase 18 support
category q <= 0.05
~~~

Its components meant:

- **Coverage ≥0.80:** the gene had to have usable explicit or implicit-null
  evidence in at least 80% of the included runs in that sex/APOE × broad-cell
  category. Coverage measures whether the gene was testable; it is not the
  percentage of runs in which the gene was significant.
- **Strict Phase 18 support:** at least one run had to contain at least two
  other mitochondrial query genes in the driver's network neighborhood, have
  fold enrichment greater than 1, and have run-level BH q≤0.05.
- **Category q≤0.05:** the gene's frozen run-level P values were combined with
  ACAT within one category, followed by BH correction across the assessable
  non-MT candidate genes in that category. The adjusted value had to be at
  most 0.05.

Applied to a non-MT-only candidate universe, that strict rule is projected to
produce:

~~~text
64 non-MT gene × category candidates
14 categories with at least one candidate
45 candidates in top-five displays
56 candidates in top-ten displays
~~~

## Selected relaxed Phase 20 rule

The main Phase 20 rule will be:

~~~text
candidate gene must be case3_not_core_mito

coverage_fraction >= 0.50

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.10

relaxed_category_acat_q <= 0.10

BH family:
    all assessable non-MT genes in the same
    signature_group + broad_network category
~~~

This is deliberately a relaxed, discovery-oriented definition. Every output
and figure must state that the main list uses 50% coverage and 10% FDR.

It is projected to produce:

~~~text
78 non-MT gene × category candidates
15 categories with at least one candidate
50 candidates in top-five displays
65 candidates in top-ten displays
~~~

Every passing candidate will be retained in the machine-readable candidate
file. The top-five and top-ten limits affect presentation only.

## Thresholds that can be relaxed

| Threshold or rule | Strict value | Relaxed Phase 20 value | Decision |
|---|---:|---:|---|
| Candidate universe | MT and non-MT | Non-MT only | Required: exclude every core-MT driver before BH and ranking. |
| Gene coverage | ≥0.80 | ≥0.50 | Relax. A gene must be usable in at least half of category runs. |
| Supporting-run q | ≤0.05 | ≤0.10 | Relax. One run can provide support at 10% run-level FDR. |
| Aggregated category q | ≤0.05 | ≤0.10 | Relax. This is the main increase in statistical yield. |
| Display cap | Top 5 | Top 10 plus all-candidate file | Relax. This changes presentation, not statistical selection. |
| Missing-value policy | Omit | Omit | Keep. Replacing missing values with P=1 would be stricter. |
| Stability requirement | Non-blocking label | Non-blocking label | Keep non-blocking. Instability changes the evidence label, not main eligibility. |

## Thresholds that should not be relaxed

| Threshold | Retained value | Reason |
|---|---:|---|
| Minimum supporting runs | ≥1 | Allowing zero would admit genes without any individually supported KDA run. |
| Other mitochondrial query genes in a supporting neighborhood | ≥2 | Reducing this to one could call a driver from a single neighboring target. |
| Supporting-run fold enrichment | >1 | A value at or below one is not enrichment. |
| Effective query genes per frozen KDA run | ≥10 | The frozen Phase 18 evidence contains these 161 runs. Lowering this is not a final-step reaggregation and would require new upstream KDA evidence. |

## Exploratory tier

For broader hypothesis generation, Phase 20 will also retain genes satisfying
the relaxed coverage and supporting-run gates with:

~~~text
0.10 < relaxed_category_acat_q <= 0.20
~~~

These are exploratory leads, not main Phase 20 key drivers. The projected
exploratory-inclusive yield is:

~~~text
94 non-MT gene × category units
17 categories with at least one unit
53 units in top-five displays
75 units in top-ten displays
~~~

## Interpretation boundary

The relaxed rule increases the number of non-MT candidates, but it cannot
create evidence in the 15 structural categories with no frozen Phase 18 runs.
It also does not prove that a driver differs statistically between sex/APOE
groups. It identifies drivers supported within a particular group and broad
cell type.
