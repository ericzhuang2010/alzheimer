# Phase 20 Methods

## Analysis scope

Phase 20 reaggregates frozen Phase 18 KDA evidence for each combination of six
sex/APOE groups and seven broad cell types. It does not regenerate DEG data
and does not rerun KDA.

The frozen input contains 1,463,150 gene-run opportunities from 161 validated
Phase 18 runs. It is copied byte-for-byte into:

~~~text
results/minerva_production/20_sex_apoe_kda/00_inputs/
~~~

The source and snapshot SHA-256 hashes must match before analysis begins.

## Non-MT restriction

Only rows with:

~~~text
case_id = case3_not_core_mito
is_core_mito = FALSE
~~~

are eligible. Case 1 and case 2 core-mitochondrial rows are removed before
aggregation, BH correction, ranking, candidate selection, and figure output.
The Phase 20 aggregate key is:

~~~text
signature_group + broad_network + current_symbol
~~~

## Frozen run evidence

Explicit frozen tests contribute final_raw_p. Implicit zero-overlap tests
contribute P=1. Genes absent from a run background are treated as missing.
Equal-weight ACAT combines usable P values within a category. The
implementation reproduces the Phase 18 boundary behavior for P=0 and P=1.

Coverage is:

~~~text
usable_run_count / eligible_run_count
~~~

It measures test availability, not the fraction of significant runs.

## Candidate definitions

The relaxed main candidate requires:

~~~text
coverage_fraction >= 0.50

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.10

relaxed_category_acat_q <= 0.10
~~~

BH is rebuilt across every coverage-eligible non-MT gene within one
sex/APOE × broad-cell category.

The strict non-MT reference requires coverage≥0.80, at least one frozen
conservative supporting run at run q≤0.05, and strict non-MT category q≤0.05.
The exploratory-only tier uses the relaxed coverage and support gates with
0.10 < relaxed category q≤0.20.

Passing candidates are ranked within category by relaxed category q, ACAT P,
and gene symbol. Every passing candidate is retained; top-five and top-ten
files are presentation subsets only.

## Stability and sensitivity

For categories with at least two fine cell types, each fine type is omitted in
turn. Coverage, ACAT, the complete non-MT BH family, support, candidate status,
and rank are recalculated. Single-fine-type categories are labeled rather than
given an artificial cross-fine-type stability estimate.

Prespecified sensitivity outputs include coverage thresholds 0.50, 0.80, and
1.00; missing values replaced by P=1; study-wide BH; direction-separated
aggregation; strict and relaxed supporting-run definitions; and category q
thresholds 0.05, 0.10, and 0.20.

## Validation

The validation-only parity harness aggregates the complete three-case table
without sex/APOE in the key and reproduces all 49,618 archived Phase 18
aggregate rows, 109 candidates, and 63 top-five flags. The production path
then filters to non-MT case 3.

The release is validated_complete only when all blocking checks pass,
including:

- 42 unique structural categories and 161 total included runs;
- 27 analyzable and 15 zero-run categories;
- expected strict, relaxed, and exploratory yields;
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
