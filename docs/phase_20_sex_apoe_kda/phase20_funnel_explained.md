# Phase 20 Gene and Candidate Filtering Explained

## The full picture

The fine-cell analysis starts with 324 DEG comparisons, creates 648 potential
directional KDA slots, and includes all 295 KDA calls that Phase 12 actually
completed at its minimum effective query size of three.

Two distinctions prevent common counting mistakes:

1. There are **324 DEG comparisons**, not 648. Up and down are two query
   directions derived from each comparison.
2. Phase 20 does **not** aggregate only the 2,494 significant rows returned by
   the stock KDA calls. It reconstructs complete gene × run evidence.

The current validated funnel is:

```text
324 fine-cell × sex/APOE DEG comparisons
    ↓ split each contrast into up/down mitochondrial queries
648 planned directional KDA slots
    ↓ 6 source-unavailable slots; 347 effective queries below 3
295 completed Phase 12 KDA calls
    = 147 AD-up + 148 AD-down
    ↓ reconstruct every relevant network gene in every run
2,623,910 all-driver gene × run rows
    ↓ exclude 212,654 core-MT candidate-driver rows
2,411,256 non-MT gene × run rows
    ↓ group by gene + sex/APOE + broad network
259,548 non-MT gene × category units
    ↓ coverage ≥0.50
233,368 units
    ↓ at least one relaxed supporting run
500 units
    ↓ within-category ACAT P followed by BH q≤0.10
74 relaxed candidate units
    = 37 distinct genes in 16 categories
```

The counting unit changes from comparisons, to run slots, to gene × run rows,
to gene × category units. This is not one continuously shrinking count of
unique genes.

## Step 1: From DEG contrasts to 295 KDA runs

### 1.1 The 648 structural slots

The upstream primary DEG design is:

```text
54 fine cell types × 6 sex/APOE groups
=324 AD-versus-NCI comparisons
```

Each fitted comparison produces signed DEG results. Core-mitochondrial DEGs
are separated into:

```text
AD_up_mito
AD_down_mito
```

Therefore:

```text
324 comparisons × 2 directions = 648 planned KDA slots
```

Up and down are not separate DEG model fits.

### 1.2 Filters that form an effective KDA query

The Phase 08 paper-DEG gates are applied upstream:

```text
detected in at least 10% of AD or NCI nuclei
within-contrast BH FDR < 0.05
absolute log2 fold change > log2(1.3)
```

For one directional slot, the provisional KDA query is:

```text
paper DEG
∩ core_mito_protein
∩ requested up/down direction
```

The run-specific broad-cell network is then restricted to genes tested in the
source DEG contrast. Any provisional query gene absent from that induced
background is removed. The number remaining is
`effective_query_genes`.

The current source manifest records the final effective-query count. It does
not split an effective count of zero into “no directional core-MT DEG” versus
“provisional query removed by background restriction.” Both mechanisms can
produce zero.

### 1.3 Exact slot outcomes

| Source/run outcome | Slots | Phase 12 KDA called? | Current Phase 20? | Frozen Phase 18? |
|---|---:|---|---|---|
| Source contrast not validated | 6 | No | No | No |
| Source valid; effective query = 0 | 246 | No | No | No |
| Effective query = 1–2 | 101 | No | No | No |
| Effective query = 3–9 | 134 | Yes | Yes | No |
| Effective query ≥10 | 161 | Yes | Yes | Yes |
| **Total** | **648** | **295 calls** | **295 runs** | **161 runs** |

The 295 included runs contain 7,787 effective query-gene memberships. The 101
one- or two-gene slots contain the remaining 146 nonzero memberships below the
execution floor.

### What “source DEG contrast not validated” means

This status means that no validated upstream AD-versus-NCI DEG result exists
for that fine-cell × sex/APOE contrast. It does **not** mean that a model ran
successfully and found zero DEGs. Without a validated contrast, Phase 12 has
no tested-gene universe and cannot construct either directional query.

The six affected directional slots are the up and down slots for three
`M_e2` source contrasts:

```text
CAMs
Fib SLC4A4
Mic MKI67
```

The Phase 20 source manifest records this source-level status but not the
finer model-fitting reason. That distinction matters: a source-unavailable
slot is different from a source-valid slot whose effective query is zero.

### 1.4 Why Phase 20 uses ≥3 instead of the historical ≥10 gate

Three is the KDA execution contract used by Phase 12. It is the lowest query
size for which completed KDA evidence exists. The current Phase 20 source
therefore includes every validated completed call:

```text
134 calls with query size 3–9
+161 calls with query size ≥10
=295 calls
```

The historical Phase 18 release applied a later ≥10 inclusion rule and remains
frozen at 161 runs. It is preserved as an audit reference; it is not rewritten
and it is no longer the Phase 20 run gate.

In the Phase 12 configuration, 10 was the `small_query_warning_below`
boundary, whereas three was the executable eligibility minimum. Phase 18 used
the warning boundary as a conservative filter. Smaller queries warrant extra
caution because one gene has greater leverage and the enrichment test carries
less information, but there is no `call_key_drivers()` requirement—and no
documented project calibration—showing that 10 is the uniquely correct cutoff.
Phase 20 therefore retains the warning label for 3–9-gene runs instead of
discarding their completed evidence.

The added 134 calls are not hypothetical reruns. They were already completed
in Phase 12. Of them, 99 returned at least one stock significant driver and 35
returned none.

### 1.5 Outcomes of the 295 completed calls

| Query-size stratum | Calls | Calls with ≥1 stock return | Calls returning none | Stock significant rows |
|---|---:|---:|---:|---:|
| 3–9 | 134 | 99 | 35 | 853 |
| ≥10 | 161 | 122 | 39 | 1,641 |
| **All included calls** | **295** | **221** | **74** | **2,494** |

A call that returned no stock-significant driver is still included in Phase
20. Its reconstructed nonsignificant, implicit-P=1, and missing evidence
remains part of the category denominator and aggregation.

There are 147 included `AD_up_mito` calls and 148 included
`AD_down_mito` calls. They arise from 41 fine cell types and map to 38 of the
42 structural sex/APOE × broad-cell categories.

Four categories have no included run:

```text
F_e2  × Vasculature_cells
F_e33 × Microglia
F_e33 × Vasculature_cells
M_e4  × Vasculature_cells
```

These categories are **not estimable**. They are not categories in which a
tested analysis found no driver.

## Step 2: What KDA tests and why the stock return is not the funnel input

The mitochondrial DEGs are the query. Candidate key drivers are network genes
whose downstream neighborhoods are tested for enrichment of that query.

A candidate driver:

- is a gene;
- need not be a DEG;
- need not be mitochondrial;
- need not be a query member; and
- is a network node, not a gene set.

Within a KDA call, the procedure identifies potential drivers near the query,
constructs directed downstream neighborhoods through layers 1–3, evaluates
upper-tail hypergeometric enrichment, retains the best layer, and applies BH
within the explicit candidate family.

The stock Phase 12 output returns only genes significant under the original
within-run rule. That is why the stock table has 2,494 rows. Phase 20 instead
uses a deterministic reconstruction of the complete test family:

- stock returns validate the reconstruction;
- all explicit tests are retained, including nonsignificant tests;
- network genes outside the explicit family are represented as implicit
  zero-overlap evidence; and
- genes absent from a run's induced background are represented as missing.

The reconstruction also applies the Phase 18-compatible self-exclusion rule
and rebuilds the final within-run BH values. Downstream support uses
`final_raw_p`, `final_run_q`, and `other_query_overlap`, not merely whether
the gene appeared in the 2,494-row stock return table.

The reconstructed source was checked against the frozen Phase 18 non-MT
universe: 1,343,593 historical rows across 161 historical runs matched with
zero mismatches. The frozen Phase 18 archive itself was not changed.

## Step 3: Complete gene × run evidence

The reconstruction contains:

| Candidate-driver class | Gene × run rows | Action |
|---|---:|---|
| Non-core-mitochondrial | 2,411,256 | Retain |
| Core-mitochondrial | 212,654 | Remove before aggregation and BH |
| **Total** | **2,623,910** | |

The retained rows are encoded as `case_id = non_mt_driver` and
`is_core_mito = FALSE`.

The retained non-MT rows have four states:

| Non-MT state in one run | Rows | Usable? | ACAT value |
|---|---:|---|---|
| Explicit positive-overlap test | 19,740 | Yes | Reconstructed raw P |
| Explicit zero-overlap test | 74,787 | Yes | 1 |
| Implicit zero-overlap, in background | 2,029,764 | Yes | 1 |
| Absent from run background | 286,965 | No | Missing/omit |
| **Total** | **2,411,256** | | |
| **Usable total** | **2,124,291** | | |

“Implicit” does not mean unknown. It means the gene was in the run background
but outside the explicit candidate neighborhood family, so its query overlap
is zero and its P value is one. “Absent” means the gene was not assessable in
that run and is the only primary missing state.

## Step 4: Grouping into gene × category units

The Phase 20 analysis unit is:

```text
current_symbol + signature_group + broad_network
gene           + sex/APOE group  + broad cell type
```

Within a unit, Phase 20 combines every included fine-cell run and both query
directions that belong to that category. It never combines different
sex/APOE groups or different broad networks.

The 2,411,256 non-MT run rows collapse to:

```text
259,548 non-MT gene × category units
11,474 distinct gene symbols
38 categories with at least one run
```

One gene can form several candidate units by appearing in several categories.
Thus, 74 final units does not mean 74 unique genes.

## Step 5: Coverage

For one gene × category unit:

```text
coverage = usable runs / eligible runs
```

The denominator is every included run in that category. The numerator counts
explicit and implicit evidence; background-absent rows are not usable.

Coverage does **not** mean:

- percentage of significant runs;
- percentage of runs that returned the gene; or
- recurrence across fine cell types.

The relaxed coverage funnel is:

| Coverage state | Gene × category units |
|---|---:|
| Zero usable runs | 14,266 |
| Some usable evidence but coverage <0.50 | 11,914 |
| Coverage ≥0.50 | 233,368 |
| **Total** | **259,548** |

Thus, 26,180 units fail relaxed coverage. The 233,368 passing units represent
11,232 distinct genes across all 38 analyzable categories.

The strict reference requires coverage ≥0.80:

```text
259,548 total units
→216,218 strict-coverage units
```

## Step 6: Supporting-run evidence

Category-wide evidence is not sufficient by itself. A relaxed candidate must
have at least one individual run satisfying:

```text
other_query_overlap >= 2
final_fold_enrichment > 1
final_run_q <= 0.10
```

The progressive non-MT run-event funnel is:

| Run-level gate | Remaining gene × run events |
|---|---:|
| Explicit candidate-family members | 94,527 |
| Positive query overlap | 19,740 |
| Other-query overlap ≥2 | 3,613 |
| Also fold enrichment >1 | 3,579 |
| Also final run q≤0.10 | 864 |

The 864 relaxed support events collapse to 501 gene × category units. One of
those units fails 50% coverage, leaving:

```text
500 coverage-qualified supported units
265 distinct genes
30 categories
```

Displayed as a sequential aggregate funnel:

```text
233,368 coverage-qualified units
−232,868 with no relaxed supporting run
=500 supported units
```

The strict support rule changes the run q threshold to ≤0.05. It yields 593
supporting gene × run events, which collapse to 345 units; 332 of those units
also pass strict 80% coverage.

## Step 7: ACAT and category-level BH

For each gene × category unit, ACAT combines the usable **raw**
`final_raw_p` values:

- explicit raw P values are retained;
- explicit and implicit zero-overlap rows contribute `P = 1`; and
- background-absent rows are omitted.

For example:

```text
five eligible runs:
    explicit P=.001
    explicit P=.40
    implicit P=1
    implicit P=1
    absent=NA

coverage = 4/5 = 0.80
ACAT combines [.001, .40, 1, 1]
NA is omitted
```

ACAT produces a category-level raw P. BH then corrects those P values across
genes **separately within each sex/APOE × broad-cell category**.

The relaxed BH family contains all 233,368 units with coverage ≥0.50. The
strict BH family contains all 216,218 units with coverage ≥0.80. Support is
not used to shrink either BH family.

Therefore, “ACAT q” means:

```text
run-level raw P values
    → ACAT category P
category P values
    → BH across all coverage-qualified genes in that category
category q
```

The funnel is often displayed as coverage → support → q for readability, but
the q values are calculated using the complete coverage-qualified families,
not only the 500 relaxed or 332 strict support-positive units.

## Step 8: Final candidate gates and current yields

### Relaxed Phase 20 main funnel

| Stage | Gene × category units | Distinct genes | Categories | Removed at this stage |
|---|---:|---:|---:|---:|
| Non-MT aggregate universe | 259,548 | 11,474 | 38 | — |
| Coverage ≥0.50 | 233,368 | 11,232 | 38 | 26,180 |
| Also ≥1 relaxed supporting run | 500 | 265 | 30 | 232,868 |
| Also category q≤0.10 | 74 | 37 | 16 | 426 |

The final 74 are **candidate units**, meaning gene × sex/APOE × broad-cell
combinations. They represent 37 unique gene symbols.

### Strict non-MT reference funnel

```text
259,548 aggregate units
→216,218 with coverage ≥0.80
→332 with at least one strict supporting run
→58 with strict category q≤0.05
```

The 58 strict units represent 30 distinct genes in 15 categories. All 58 are
also among the 74 relaxed main candidates.

The strict reference uses the same current 295-run source. It is not the same
thing as rerunning or changing the historical Phase 18 ≥10 release.

### Exploratory leads and display subsets

Fifteen additional units pass relaxed coverage and support but have:

```text
0.10 < relaxed category q <= 0.20
```

They represent 14 distinct genes in seven categories and are labeled
exploratory-only. Combining them with the 74 main candidates gives:

```text
89 exploratory-inclusive units
47 distinct genes
17 categories
```

Top-five and top-ten limits are display rules, not statistical filters:

| Tier | All units | Top-five units | Top-ten units |
|---|---:|---:|---:|
| Strict reference | 58 | 43 | 51 |
| Relaxed main | 74 | 48 | 63 |
| Exploratory inclusive | 89 | 54 | 72 |

Stability labels also do not remove main candidates. They describe how the
result behaves when one fine cell type is omitted and the full aggregation
and BH calculation is repeated.

## Interpretation cautions

- A KDA candidate is a gene, but a Phase 20 candidate count is a gene ×
  category count.
- A significant stock return is not required in every run; complete evidence,
  including P=1 and missing states, enters aggregation.
- Coverage measures assessability, not recurrence or significance.
- The primary analysis combines up and down directions within a category;
  direction-separated results are a sensitivity analysis.
- A candidate supports within-category network enrichment. It does not test a
  difference between sex/APOE groups and does not establish causality.
- The 3–9-query calls are completed validated Phase 12 calls, but their smaller
  queries should be considered when interpreting localized evidence.
- “Not estimable” means no included run, not evidence of no biological driver.

## Machine-readable authorities

- [Source run manifest](../../results/minerva_production/20_sex_apoe_kda/00_inputs/phase20_source_run_manifest.tsv)
- [Source validation checks](../../results/minerva_production/20_sex_apoe_kda/00_inputs/phase20_source_checks.tsv)
- [Phase 20 status](../../results/minerva_production/20_sex_apoe_kda/phase20_status.tsv)
- [Phase 20 category manifest](../../results/minerva_production/20_sex_apoe_kda/phase20_category_manifest.tsv)
- [Phase 20 filter funnel](../../results/minerva_production/20_sex_apoe_kda/phase20_filter_funnel.tsv)
- [Phase 20 checks](../../results/minerva_production/20_sex_apoe_kda/phase20_checks.tsv)
- [Phase 20 methods](phase20_methods.md)
