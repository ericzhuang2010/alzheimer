# Phase 20 Methods and Threshold Rationale

## Analysis scope and source authority

Phase 20 aggregates key-driver evidence across fine-cell KDA calls for the 42
categories defined by six sex/APOE groups and seven broad cell types. It does
not rerun differential expression, refit a network, or rerun the original
Phase 12 KDA calls.

The current source is a validated reconstruction from the completed Phase 12
bundle. It uses the Phase 12 run manifest, query and background memberships,
stock KDA results, broad-cell networks, and mitochondrial annotation to
reconstruct the complete candidate-test family for every completed primary
call with at least three effective query genes. The source status records:

```text
648 structural directional slots
295 completed Phase 12 calls included in Phase 20
41 included fine cell types
38 sex/APOE × broad-cell categories with at least one run
2,494 stock significant result rows
2,623,910 reconstructed gene × run rows
0 failed source checks
```

The validated source files are copied into:

```text
results/minerva_production/20_sex_apoe_kda/00_inputs/
```

The source and copied-file SHA-256 hashes must match before aggregation. The
canonical release status is `validated_complete`.

### The historical Phase 18 release remains frozen

Phase 18 historically required at least 10 effective query genes and contains
161 runs. Phase 20 does **not** modify or overwrite that archive. Instead, the
Phase 20 source reconstruction uses the Phase 12 execution floor of three and
therefore adds 134 already-completed Phase 12 calls with query sizes 3–9:

```text
134 calls with 3–9 effective query genes
+161 calls with at least 10 effective query genes
=295 current Phase 20 runs
```

As an audit, the reconstruction was restricted to the original Phase 18
non-MT gene universe. All 1,343,593 historical non-MT rows across the 161
historical runs matched, with zero parity mismatches. That parity check is
deliberately limited to the historical gene universe; the current 295-run
source uses the broader network-gene union induced by all 295 runs.

## What is a run?

One **run** is one upstream KDA call, not one donor, sample, or gene. A primary
run is defined by:

```text
fine cell type × sex/APOE group × signature direction
```

The two directions are `AD_up_mito` and `AD_down_mito`, and each run uses the
Bayesian network for its corresponding broad cell type. Several fine-cell
runs and both directions can therefore contribute to one Phase 20 category.

The structural universe is:

```text
54 fine cell types × 6 sex/APOE groups × 2 directions
=648 planned run slots
```

The source manifest includes 295 runs: 147 `AD_up_mito` and 148
`AD_down_mito`. The other 353 slots were not called because the source
contrast was unavailable or the effective query contained fewer than three
genes. The 295 included runs contain 7,787 effective query-gene memberships.

The 295 runs map to 38 of the 42 structural categories. Four categories have
no included run and are explicitly recorded as not estimable:

```text
F_e2  × Vasculature_cells
F_e33 × Microglia
F_e33 × Vasculature_cells
M_e4  × Vasculature_cells
```

## Why the current run floor is three

Three effective query genes is the Phase 12 KDA execution contract. It is the
lowest threshold for which completed Phase 12 KDA evidence exists. Phase 20
therefore includes all 295 validated calls at that floor; it cannot include
the 101 slots with only one or two effective query genes because KDA was not
called for them.

The historical threshold of 10 was a later Phase 18 inclusion rule, not the
Phase 12 call threshold. Keeping it as the Phase 20 gate would discard 134
completed calls, including 99 calls with at least one stock significant
return. The historical ≥10 subset is retained as a frozen audit reference,
not as the current Phase 20 inclusion rule.

The configuration history explains where 10 came from. Phase 12 set
`minimum_effective_query_genes: 3` and separately marked queries below 10 with
`small_query_warning = TRUE`; Phase 18 then used that warning boundary as a
conservative inclusion floor. The caution is reasonable because enrichment
from a very small query can be more sensitive to one gene and produces less
information, but 10 is not required by `call_key_drivers()`. No project record
establishes 10 as an empirically calibrated optimum, so current Phase 20 keeps
the small-query caution while including every validated completed call at the
actual execution floor of three.

Including 3–9-gene queries does not relax the downstream support definition:
a supporting neighborhood must still contain at least two *other* query genes,
have fold enrichment greater than one, and pass a within-run q threshold.

## What is a candidate?

The mitochondrial DEGs are the **query**. A potential key-driver candidate is
a gene in the relevant network whose directed downstream neighborhood is
tested for enrichment of that query. A candidate driver therefore:

- is a gene;
- need not be a DEG;
- need not be mitochondrial;
- need not belong to the query; and
- is a network node, not a gene set.

There are two useful counting units:

1. A **candidate-gene × run test** is one gene evaluated in one KDA run.
2. A **Phase 20 candidate unit** is one gene in one sex/APOE × broad-cell
   category:

```text
current_symbol + signature_group + broad_network
gene symbol    + sex/APOE group  + broad cell type
```

The same gene can therefore be a passing candidate in several categories.
Candidate-unit counts are not counts of unique gene symbols.

## Complete reconstructed run evidence

Phase 20 does not start with only the 2,494 genes returned as significant by
the stock Phase 12 calls. It reconstructs the complete pre-significance test
family and represents every relevant network gene in every included run.

The complete source has 2,623,910 gene × run rows:

| Driver class | Rows | Phase 20 use |
|---|---:|---|
| Non-core-mitochondrial driver | 2,411,256 | Retain |
| Core-mitochondrial driver | 212,654 | Exclude before aggregation and BH |
| **Total** | **2,623,910** | |

The retained class is encoded as `case_id = non_mt_driver` with
`is_core_mito = FALSE`. These fields replace the historical Phase 18 case
labels in the reconstructed source.

The retained non-MT evidence has four mutually exclusive states:

| Run-level state | Rows | ACAT treatment |
|---|---:|---|
| Explicit positive-overlap test | 19,740 | Use reconstructed `final_raw_p` |
| Explicit zero-overlap test | 74,787 | Use `P = 1` |
| Implicit zero-overlap gene in the run background | 2,029,764 | Use `P = 1` |
| Gene absent from the run background | 286,965 | Missing; omit from primary ACAT |
| **Total non-MT rows** | **2,411,256** | |
| **Usable explicit + implicit rows** | **2,124,291** | |

`final_run_q` is the BH-adjusted value within the reconstructed candidate
family for one run after the Phase 18-compatible self-exclusion procedure.
The 2,494 stock result rows describe the original significant returns; they
are a validation target, not the Phase 20 aggregation universe.

## Cross-run aggregation

For a gene × category unit, the eligible denominator is every included run
with the same `signature_group` and `broad_network`. Evidence is combined
across the fine cell types and across both directions within that category.
Different sex/APOE groups and different broad networks are never combined.

Coverage is:

```text
coverage_fraction = usable_run_count / eligible_run_count
```

Coverage measures run-level availability for that gene. It is not the
fraction of significant runs, the fraction of runs that returned the gene,
or recurrence across fine cell types.

Equal-weight ACAT combines the usable **raw** `final_raw_p` values. Explicit
and implicit zero-overlap evidence contributes `P = 1`; background absence is
omitted. The implementation preserves the Phase 18/NetWeaver boundary
behavior for `P = 0` and `P = 1`.

ACAT yields `category_acat_p`. BH correction is then applied separately
within each sex/APOE × broad-cell category:

- the relaxed BH family contains every non-MT gene with coverage ≥0.50;
- the strict BH family contains every non-MT gene with coverage ≥0.80; and
- supporting-run status is **not** used to shrink either BH family.

Thus, “ACAT q” is shorthand for two operations:

```text
run-level raw P values → ACAT category P
category P values      → BH across coverage-qualified genes in that category
```

## Candidate tiers

### Relaxed Phase 20 main tier

A gene × category unit is a main candidate only if all four gates pass:

```text
coverage_fraction >= 0.50

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.10

relaxed_category_acat_q <= 0.10
```

The support gate requires an individually interpretable KDA event, while the
category q gate evaluates the aggregate evidence after correction across the
complete coverage-qualified category family.

### Strict non-MT reference tier

The strict reference uses the same 295-run source and non-MT-only candidate
universe. It requires:

```text
coverage_fraction >= 0.80

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.05

strict_category_acat_q <= 0.05
```

This is a stricter Phase 20 comparison tier. It must not be confused with the
frozen Phase 18 ≥10-run archive; both current tiers use the 295-run min-3
source.

### Exploratory-only tier

An exploratory-only lead passes the relaxed coverage and support gates but
has:

```text
0.10 < relaxed_category_acat_q <= 0.20
```

These units are not main candidates. “Exploratory inclusive” means relaxed
main candidates plus exploratory-only leads.

## Threshold choices and rationale

| Component | Strict reference | Relaxed main | Rationale |
|---|---:|---:|---|
| Source run floor | ≥3 effective query genes | ≥3 | Includes every completed, validated Phase 12 call; no KDA evidence exists below three. |
| Candidate universe | Non-MT only | Non-MT only | Core-MT candidate drivers are outside the stated Phase 20 target and are removed before BH. |
| Gene coverage | ≥0.80 | ≥0.50 | The main tier allows missing background membership but requires usable evidence in at least half of the category's runs. |
| Other query genes in a supporting neighborhood | ≥2 | ≥2 | Prevents a call based on only one neighboring query target. |
| Supporting-run fold enrichment | >1 | >1 | A value at or below one is not enrichment. |
| Supporting-run q | ≤0.05 | ≤0.10 | At least one reconstructed run must provide BH-adjusted support. |
| Aggregated category q | ≤0.05 | ≤0.10 | The main tier is discovery-oriented while retaining category-level FDR control. |
| Primary missing-value action | Omit | Omit | Replacing missing values with `P = 1` is a stricter sensitivity analysis. |
| Stability | Non-blocking label | Non-blocking label | Stability changes the evidence label, not candidate eligibility. |

## Validated current results

The aggregate table contains 259,548 non-MT gene × category units representing
11,474 distinct gene symbols across 38 analyzable categories.

| Analysis tier | Candidate units | Distinct genes | Categories with a candidate | Top-five units | Top-ten units |
|---|---:|---:|---:|---:|---:|
| Strict non-MT reference | 58 | 30 | 15 | 43 | 51 |
| Relaxed Phase 20 main | 74 | 37 | 16 | 48 | 63 |
| Exploratory inclusive | 89 | 47 | 17 | 54 | 72 |

The exploratory-inclusive total is 74 main candidates plus 15
exploratory-only units. Those 15 exploratory-only units represent 14 distinct
genes in seven categories. All 58 strict units are among the 74 relaxed main
candidates.

Passing candidates are ranked within category by category q, ACAT P, and gene
symbol. Top-five and top-ten outputs are presentation subsets; they do not
remove a candidate from the machine-readable main list.

## Stability and sensitivity

For categories containing at least two fine cell types, each fine type is
omitted in turn and the complete coverage, ACAT, BH, support, candidate, and
rank calculations are repeated. Single-fine-type and single-run categories
are labeled explicitly rather than given an artificial cross-fine-type
stability estimate.

Prespecified sensitivities include coverage thresholds 0.50, 0.80, and 1.00;
missing values replaced with `P = 1`; study-wide BH; direction-separated
aggregation; support q thresholds 0.05 and 0.10; and category q thresholds
0.05, 0.10, and 0.20.

## Interpretation boundaries

- A candidate is within-category network-enrichment evidence for a gene, not
  a statistically tested difference between sex/APOE groups.
- A key-driver result does not by itself establish biological causality.
- Up- and down-query evidence is combined in the primary category result;
  direction-separated output is a sensitivity analysis.
- The 134 query-size 3–9 calls are valid completed Phase 12 calls, but their
  smaller queries should remain visible when interpreting localized evidence.
- A category with no included run is not estimable; it is not evidence that
  the category has no biological driver.

## Validation and executable authorities

The release is `validated_complete` only when all blocking checks pass,
including source hash identity, 295 unique included runs, a minimum included
query size of three, 42 structural and 38 analyzable categories, 2,623,910
source rows, 259,548 unique aggregate units, the candidate yields above,
complete non-MT-only BH families, and no MT row in any aggregate or candidate
table. The current release has zero failed checks.

Executable authorities:

```text
config/phase20_sex_apoe_kda.yml
scripts/20_prepare_sex_apoe_kda_source.py
scripts/20_sex_apoe_kda.py
tests/test_phase20_sex_apoe_kda.py
scripts/figures/analysis/phase_20_sex_apoe_kda/render_phase20_summary_figures.py
```
