# Phase 20 Gene and Candidate Filtering Explained

The analysis has three main layers, but two corrections are essential:

1. There are **324 DEG comparisons**, not 648. Splitting each comparison into
   up- and downregulated mitochondrial signatures creates 648 planned KDA
   slots.
2. Phase 20 does **not** aggregate only genes returned as significant by
   `call_key_drivers()`. It uses reconstructed evidence for every assessable
   network gene.

```text
324 DEG comparisons
    ↓ split into up/down mitochondrial queries
648 planned directional KDA slots
    ↓ query-size and source-validity filters
295 actual call_key_drivers() calls
    ↓ require effective query ≥10 for Phase 18/20
161 included KDA runs
    ↓ reconstruct complete gene × run evidence
1,463,150 gene × run opportunities
    ↓ remove core-MT candidate drivers
1,343,593 non-MT gene × run rows
    ↓ group by gene + sex/APOE + broad network
196,174 gene × category units
    ↓ coverage ≥50%
182,538 units
    ↓ at least one supporting run
431 units
    ↓ category BH q≤0.10
78 candidate units = 37 distinct genes
```

The counting unit changes several times, so this is not one continuously
shrinking "number of genes."

## Step 1: DEG comparisons and mitochondrial queries

The DEG analysis performs:

```text
54 fine cell types × 6 sex/APOE groups = 324 AD-versus-NCI comparisons
```

One comparison produces one set of signed DEGs. It is then split into:

```text
AD_up_mito
AD_down_mito
```

Therefore:

```text
324 comparisons × 2 directions = 648 planned KDA slots
```

Up and down are not separate DEG model fits; they are the positive and
negative genes from the same comparison.

The full Phase 12 bundle also contains pooled groups and an `AD_both_mito`
direction, giving 1,782 planned analyses. Those additional analyses are
outside the Phase 18/20 funnel discussed here.

### DEG filters

A gene becomes a Phase 08 paper DEG only when:

```text
detected in ≥10% of AD or NCI nuclei
within-contrast BH FDR < 0.05
absolute log2 fold change > log2(1.3) ≈ 0.379
```

These are strict `<` and `>` thresholds.

Across all genes and contrasts:

```text
2,864,117 tested gene × comparison rows
118,297 paper-DEG memberships
    58,112 up
    60,185 down
```

KDA does not use all 118,297 DEG memberships. Its query is restricted to
`core_mito_protein`.

The fixed core-MT audit gives this mutually exclusive breakdown:

| Core-MT feature × comparison outcome | Count |
|---|---:|
| Contrast not estimable | 3,588 |
| Feature absent from expression matrix | 642 |
| Present but fails the 10% detection filter | 165,872 |
| Tested but fails both FDR and effect-size thresholds | 118,125 |
| Passes effect-size threshold but fails FDR | 49,423 |
| Passes FDR but fails effect-size threshold | 40,592 |
| Passes both: core-MT paper DEG | 9,262 |
| **Total** | **387,504** |

The 9,262 query memberships comprise:

```text
4,258 AD-up core-MT DEG memberships
5,004 AD-down core-MT DEG memberships
```

The provisional KDA query is therefore:

```text
paper DEG
∩ core_mito_protein
∩ requested up/down direction
```

The run-specific broad network is then restricted to genes tested in that DEG
contrast. Query genes absent from this induced network background are removed:

```text
9,262 provisional query memberships
−1,329 absent from effective network background
=7,933 effective-query memberships
```

Importantly, the manifest field `candidate_query_genes` means provisional
mitochondrial **query genes**. It does not mean candidate key-driver genes.

### How the 648 planned slots are filtered

| Slot outcome | Slots | Was KDA called? | Used by Phase 20? |
|---|---:|---|---|
| Source DEG contrast not estimable | 6 | No | No |
| No directional core-MT DEG | 229 | No | No |
| Provisional query nonempty, but effective query becomes zero | 17 | No | No |
| Effective query contains 1–2 genes | 101 | No; Phase 12 requires ≥3 | No |
| Effective query contains 3–9 genes | 134 | Yes | No; Phase 18/20 require ≥10 |
| Effective query contains ≥10 genes | 161 | Yes | Yes |
| **Total** | **648** | **295 calls** | **161 runs** |

#### What "source DEG contrast not estimable" means

A **source DEG contrast** is the upstream Phase 08 AD-versus-NCI comparison
for one fine cell type and one sex/APOE group. "Not estimable" means the
statistical model could not be fitted because a required input condition was
not met. It does **not** mean that the model ran successfully and found no
DEGs.

Seurat requires at least three cells in both the AD and NCI arms before the
MAST comparison can run. Three of the 324 planned source contrasts failed this
requirement:

| Fine cell type | Sex/APOE | AD cells (donors) | NCI cells (donors) | Reason |
|---|---|---:|---:|---|
| `Fib SLC4A4` | `M_e2` | 0 (0) | 11 (2) | The AD arm had no cells. |
| `CAMs` | `M_e2` | 45 (5) | 1 (1) | The NCI arm had fewer than three cells. |
| `Mic MKI67` | `M_e2` | 2 (2) | 9 (3) | The AD arm had fewer than three cells. |

Because no DEG model was fitted, these contrasts have no tested-gene results,
no qualifying `paper_deg` genes, and no up- or downregulated mitochondrial
query. Each unavailable contrast would otherwise create two directional KDA
slots (`AD_up_mito` and `AD_down_mito`), so:

```text
3 non-estimable DEG contrasts × 2 directions
= 6 source-not-estimable KDA slots
```

This also explains the 3,588 `Contrast not estimable` entries in the earlier
core-MT table:

```text
3 non-estimable contrasts × 1,196 core-MT feature records
= 3,588 unavailable feature × contrast opportunities
```

In general, a source contrast could also be non-estimable because required
covariates are unavailable or nonfinite, or because the model design is rank
deficient. Neither occurred among these three contrasts. This outcome is
different from `No directional core-MT DEG`: in that case the DEG comparison
did run, but no core-MT gene passed the FDR, effect-size, and direction filters
for that KDA slot.

Other coded possibilities—an empty induced network or a KDA computation
failure—had observed counts of zero.

This distinction is important:

```text
Phase 12 execution threshold: effective query ≥3
Phase 18/20 inclusion threshold: effective query ≥10
```

## Step 2: What `call_key_drivers()` actually tests

The mitochondrial DEGs are the **query**. Candidate key drivers are network
genes whose downstream neighborhoods are tested for enrichment of that query.

A candidate driver therefore:

- need not be a DEG;
- need not be mitochondrial;
- need not belong to the query; and
- is a network node, not a gene set.

Within one KDA call, the procedure:

1. Finds potential driver genes within three undirected network hops of the
   mitochondrial query.
2. Builds each candidate's directed downstream neighborhoods through layers
   1–3.
3. Calculates an upper-tail hypergeometric enrichment P value at each layer.
4. Retains the best layer for each candidate gene.
5. Applies BH correction across the explicitly tested candidate genes in that
   run.
6. Returns only genes with within-run BH q≤0.05.

The `global_key_driver` and related topology fields are annotations; they are
not Phase 20 selection gates.

### Actual call outcomes

| Scope | Calls | Calls with ≥1 returned driver | Calls returning none | Significant result rows |
|---|---:|---:|---:|---:|
| All executed slots | 295 | 221 | 74 | 2,494 |
| Query size 3–9, later excluded | 134 | 99 | 35 | 853 |
| Query size ≥10, used by Phase 20 | 161 | 122 | 39 | 1,641 |

Thus, 99 of the 134 small-query calls had significant results, but Phase 20
still excludes them because the query contained fewer than 10 genes.

Across the 161 included calls:

```text
95,557 explicit candidate-gene × run tests
    1,641 significant returned rows
   93,916 nonsignificant tested rows
```

The 95,557 explicit tests represent 6,149 distinct tested genes. The 1,641
significant rows represent 295 distinct returned gene symbols—coincidentally
the same number as the 295 executed calls.

## Step 3: Complete evidence, grouping, ACAT, and final filtering

This is the largest correction to the simple three-step model:

> Phase 20 does not begin with only the 1,641 returned rows.

Phase 18 reconstructs the complete pre-significance test family and then
evaluates every network gene across the relevant runs.

For each gene in each run, there are three broad possibilities:

| Gene state in one run | Statistical treatment |
|---|---|
| Explicitly tested | Use its frozen `final_raw_p` |
| In the run background but outside the explicit candidate family | Implicit zero overlap; use `P = 1` |
| Absent from the run background | Missing; omit from ACAT and lower coverage |

An explicit test is further labeled:

- `explicit_test`: positive query overlap; its P value may still be
  nonsignificant.
- `explicit_zero_overlap`: explicitly evaluated but zero overlap; `P = 1`.

Across all driver classes:

```text
95,557 explicit tests
1,204,225 implicit P=1 rows
163,368 missing rows
────────────────────────────
1,463,150 gene × run opportunities
```

Phase 20 then removes all core-MT candidate-driver rows:

```text
1,463,150 all-case rows
−119,557 core-MT rows
=1,343,593 non-MT gene × run rows
```

The retained non-MT evidence consists of:

| Non-MT run-level state | Rows | ACAT treatment |
|---|---:|---|
| Explicit positive-overlap test | 17,723 | Use raw P |
| Explicit zero-overlap test | 65,731 | Use `P = 1` |
| Implicit zero-overlap | 1,110,465 | Use `P = 1` |
| Absent from background | 149,674 | Missing/omit |
| **Total** | **1,343,593** | |
| **Usable explicit + implicit** | **1,193,919** | |

### Grouping is not by gene alone

The Phase 20 unit is:

```text
current_symbol + signature_group + broad_network
gene           + sex/APOE group  + broad cell type
```

Within this unit, Phase 20 combines:

- all included fine-cell-type runs belonging to the broad network; and
- both `AD_up_mito` and `AD_down_mito` runs.

It never combines different sex/APOE groups or different broad networks.

Therefore, one gene can produce multiple candidate units. The 1,343,593
run-level rows collapse to:

```text
196,174 non-MT gene × category units
11,319 distinct gene symbols
27 categories with at least one run
```

The remaining 15 of the 42 structural categories have no included runs and
are not estimable.

### Coverage

For one gene × category unit:

```text
coverage = usable runs / eligible runs
```

Usable means explicit evidence or implicit `P = 1`. Missing background rows
are not usable.

Coverage does not mean:

- percentage of significant runs;
- percentage of runs returning the gene; or
- recurrence across fine cell types.

Of the 196,174 units:

```text
8,352 have zero usable runs
5,284 have some evidence but coverage <0.50
13,636 total fail the relaxed coverage threshold
182,538 pass coverage ≥0.50
```

### What ACAT combines

ACAT combines the usable **raw run-level P values**, not run-level q values.

For example, suppose a gene-category unit has five eligible runs:

```text
explicit P=.001
explicit P=.40
implicit P=1
implicit P=1
absent=NA
```

Then:

```text
coverage = 4/5 = 0.80
ACAT combines [.001, .40, 1, 1]
NA is omitted
```

This produces `category_acat_p`.

Next, within each sex/APOE × broad-cell category, BH correction is applied to
the ACAT P values of every coverage-qualified non-MT gene. This produces:

```text
relaxed_category_acat_q
```

Therefore, "ACAT q value" is shorthand for two operations:

```text
run-level raw P values
    → ACAT
category-level raw P
    → BH across genes in the category
category-level q
```

### Supporting-run filter

ACAT significance alone is not enough. At least one individual run must
satisfy:

```text
other_query_overlap >= 2
final_fold_enrichment > 1
final_run_q <= 0.10
```

The non-MT support sub-funnel is:

```text
83,454 explicit tests
17,723 have positive query overlap
 3,502 have overlap ≥2
 3,468 also have fold enrichment >1
   775 also have run q≤0.10
```

Those 775 supporting gene × run events collapse to 432 gene × category
units. One unit fails 50% overall coverage, leaving 431 coverage-qualified
supported units.

The strict support definition uses run q≤0.05 and has 532 supporting gene ×
run events.

### Final relaxed candidate funnel

| Stage | Gene × category units | Distinct genes | Categories | Why units are lost |
|---|---:|---:|---:|---|
| Non-MT aggregate universe | 196,174 | 11,319 | 27 | Starting category-specific universe |
| Coverage ≥0.50 | 182,538 | 11,176 | 27 | 13,636 lack sufficient run availability |
| At least one relaxed supporting run | 431 | 227 | 24 | 182,107 lack an individually supported run |
| Category BH q≤0.10 | 78 | 37 | 15 | 353 supported units fail category FDR |

One subtle but important point: the table is displayed sequentially, but BH
is computed over **all 182,538 coverage-qualified units**, separately by
category. The BH denominator is not the 431 support-positive units. In this
dataset, all 78 units with category q≤0.10 also happen to have supporting-run
evidence.

The strict parallel funnel is:

```text
196,174 units
→166,086 with coverage ≥0.80
→279 with at least one strict supporting run
→64 strict candidates = 32 distinct genes
```

All 64 strict candidates are among the 78 relaxed candidates. The relaxed
thresholds add 14 candidate units.

An additional 16 units satisfy the relaxed coverage/support gates with:

```text
0.10 < category q <= 0.20
```

These are exploratory-only leads, not main candidates.

Finally, top-five/top-ten display limits and stability labels do not remove
candidates. They affect presentation and evidence labeling only.

## Implementation and audit authorities

- [Phase 08 DEG filtering](../../scripts/08_run_mast.R#L725)
- [Phase 12 query construction and KDA execution](../../scripts/12_run_kda.R#L285)
- [All-tested KDA guide](../phase_18_key_driver_selection/call_key_driver_returns_columns_explained.md)
- [Phase 20 methods](phase20_methods.md)
- [Phase 20 machine-readable filter funnel](../../results/minerva_production/20_sex_apoe_kda/phase20_filter_funnel.tsv)
