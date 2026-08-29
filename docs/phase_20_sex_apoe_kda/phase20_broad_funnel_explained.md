# Phase 20 Broad-Cell KDA Gene and Candidate Filtering Explained

The broad-cell analysis has three main layers, with three essential
clarifications:

1. There are **42 broad-cell DEG contrasts**, not 42 automatic KDA calls.
   Splitting each contrast into up- and downregulated mitochondrial queries
   creates 84 possible directional KDA slots.
2. Only three relaxed-primary slots contain at least three effective query
   genes, so only three primary KDA calls are executed.
3. This is a direct broad-cell analysis. It does **not** group genes across
   runs and does not use ACAT, coverage, recurrence, or a category-level q
   value.

```text
42 planned structural broad-cell DEG contrasts
    ↓ predeclare up/down slots for every structural contrast
84 planned directional KDA slots
    ↓ source validity, query presence, network mapping, and query size ≥3
3 executed relaxed-primary KDA runs
    ↓ reconstruct complete pre-FDR candidate evidence
377 explicit gene × directional-run tests
    ↓ remove 15 core-MT candidate-driver tests before final BH
362 non-core-MT tests
    ↓ require query overlap ≥2
15 tests
    ↓ require fold enrichment >1
15 tests
    ↓ require within-run non-core-MT BH q≤0.10
12 relaxed candidate rows = 12 distinct genes
    ↳ 9 also pass the q≤0.05 strict-reference rule
```

The counting unit changes from contrasts, to directional slots, to query-gene
memberships, and then to candidate-gene × directional-run tests. This is not
one continuously shrinking count of unique genes.

## Step 1: Broad-cell DEG contrasts and mitochondrial queries

The donor-level broad-cell DEG analysis performs:

```text
7 broad cell types × 6 sex/APOE groups
= 42 planned AD-versus-NCI contrasts
```

Phase 08 fits one joint edgeR model per broad cell type and tests up to six
sex/APOE-specific AD-versus-NCI contrasts within that model. One estimable
contrast test produces one signed result. Positive and negative `logFC` values
are then separated into:

```text
AD_up_mito
AD_down_mito
```

Up and down are therefore not separate DEG models or contrast tests. They are
two query directions derived from the same signed contrast result:

```text
42 structural contrasts × 2 directions = 84 directional KDA slots
```

### Source-model and contrast filters

The broad DEG models use donors, not nuclei, as the biological replicates. A
donor-by-broad-cell sample must contain at least 20 nuclei, and a sex/APOE
contrast requires at least five eligible AD donors and five eligible NCI
donors. Within each broad-cell edgeR model, `filterByExpr()` removes genes with
insufficient expression before testing.

The validated Phase 08 broad release contains:

| Source outcome | Broad-cell contrasts |
|---|---:|
| Completed and validated | 40 |
| Not estimable | 2 |
| Failed | 0 |
| **Total** | **42** |

The two unavailable source contrasts are:

| Broad cell type | Group | Eligible AD donors | Eligible NCI donors | Reason |
|---|---|---:|---:|---|
| Vasculature_cells | `F_e2` | 3 | 10 | AD has fewer than five eligible donors |
| Vasculature_cells | `M_e2` | 4 | 3 | Both arms have fewer than five eligible donors |

`not_estimable` means the stratum-specific contrast was not tested and no
contrast result was produced because the donor gate failed. It does not imply
that the shared broad-cell model failed to fit: the Vasculature model was
fitted, but these two contrast tests were skipped. It also does not mean that a
completed contrast found zero DEGs. Each unavailable contrast accounts for two
unavailable KDA slots:

```text
2 unavailable contrasts × 2 directions
= 4 source-contrast-not-estimable KDA slots
```

### Relaxed-primary DEG and query filters

Phase 08 retained 786,242 tested gene × contrast rows across the 40 completed
contrasts. A gene becomes a relaxed DEG membership when it satisfies:

```text
within-contrast DEG BH q ≤ 0.10
and abs(logFC) ≥ log2(1.2) ≈ 0.263
```

The relaxed tier contains:

```text
2,336 DEG memberships
    983 AD-up
  1,353 AD-down
```

KDA does not use all 2,336 memberships. Its provisional query is restricted to
core mitochondrial proteins and the requested direction:

```text
relaxed DEG
∩ mito_tier == core_mito_protein
∩ requested sign of logFC
```

This leaves:

```text
65 provisional query-gene memberships
    20 AD_up_mito
    45 AD_down_mito
```

A query gene is a mitochondrial DEG used as the target set for network
enrichment. It is not a candidate key-driver gene.

## Step 2: Network mapping and directional-run eligibility

For each source-complete broad-cell contrast, the matching Bayesian network is
restricted to the genes actually tested in that contrast:

```text
induced edges = network edges whose two endpoints are tested genes
effective background = unique endpoints of those induced edges
effective query = provisional query ∩ effective background
```

This prevents an untested expression gene or an out-of-background query gene
from entering the enrichment test.

### Query-gene membership funnel

Across the relaxed-primary tier:

```text
65 provisional query memberships
−30 absent from their tested-gene-induced network backgrounds
=35 effective query memberships
```

The 30 removed memberships are gene-level losses. They are not the same as the
four directional slots that lose their entire query: some other slots retain
part of their provisional query.

### The 84-slot outcome partition

Every relaxed-primary directional slot receives exactly one mutually exclusive
outcome:

| Directional-slot outcome | Slots | Provisional memberships | Effective memberships | Was KDA called? |
|---|---:|---:|---:|---|
| Source DEG contrast not estimable | 4 | 0 | 0 | No |
| No provisional relaxed core-MT query | 61 | 0 | 0 | No |
| Query becomes empty after network mapping | 4 | 7 | 0 | No |
| Effective query contains 1–2 genes | 12 | 29 | 15 | No |
| Effective query contains at least 3 genes | 3 | 29 | 20 | Yes |
| **Total** | **84** | **65** | **35** | **3 calls** |

Equivalently, the slot funnel can be read sequentially:

```text
84 planned directional slots
− 4 source-not-estimable slots
=80 source-complete slots
−61 with no relaxed core-MT DEG in that direction
=19 nonempty provisional queries
− 4 that lose every query gene during network mapping
=15 nonempty effective queries
−12 with only 1–2 effective query genes
= 3 executable KDA runs
```

The `directional_query_slots` rows in
`phase20_broad_filter_funnel.tsv` are outcome bins over the same 84 slots. Its
generic `passing_units` column should not be read as a sequential survivor
count.

### The three executable primary runs

| Broad cell type | Group | Direction | Provisional query | Effective query | Query-size label |
|---|---|---|---:|---:|---|
| Astrocytes | `F_e4` | `AD_down_mito` | 18 | 13 | `phase18_sized_query_ge10` |
| Astrocytes | `M_e33` | `AD_down_mito` | 5 | 3 | `small_query_3_9` |
| OPCs | `F_e4` | `AD_down_mito` | 6 | 4 | `small_query_3_9` |

Their effective query genes are:

- Astrocytes `F_e4`: `ACOT7`, `AHCYL1`, `ETHE1`, `FDPS`, `GBF1`, `GLDC`,
  `LAP3`, `PNPLA8`, `POLG`, `SLC25A28`, `SLC25A37`, `SMIM20`, `YME1L1`.
- Astrocytes `M_e33`: `MALSU1`, `RARS2`, `SLC25A37`.
- OPCs `F_e4`: `BCL2L1`, `GLDC`, `HAP1`, `ME3`.

All three executable relaxed-primary queries are AD-down queries. A query of
three or four genes is allowed in this direct broad branch because the
prespecified minimum is three. Canonical fine-cell Phase 20 v2 now uses the
same ≥3 KDA execution floor. The ≥10 boundary belongs only to the frozen
historical Phase 18 release; it is retained here as an evidence-strength label,
not as a current fine-cell or direct-broad Phase 20 inclusion rule.

### What each ineligible status means

- `source_contrast_not_estimable`: the upstream donor-level DEG comparison was
  unavailable.
- `no_provisional_query`: the DEG model ran, but no relaxed core-MT DEG passed
  the requested up/down rule.
- `effective_query_empty_after_background`: provisional query genes existed,
  but none belonged to the tested-gene-induced network background.
- `effective_query_below_minimum`: one or two query genes survived, fewer than
  the prespecified minimum of three.

None of these statuses means that key drivers were tested and proven absent.

## Step 3: What direct `call_key_drivers()` testing does

The mitochondrial DEGs are the query. A candidate driver is a network gene
whose directed downstream neighborhood is tested for enrichment of that query.
A candidate driver:

- need not be a DEG;
- need not be mitochondrial;
- need not belong to the query; and
- is one gene, not a gene set.

Within one eligible directional run, KDA:

1. finds potential candidates within three undirected network hops of the
   query;
2. constructs each candidate's directed downstream neighborhoods through
   layers 1–3;
3. calculates an upper-tail hypergeometric enrichment P value at each layer;
4. retains the best layer and raw P value for each explicitly tested gene; and
5. applies BH correction across the explicitly tested candidate genes in that
   run.

Stock fKDA normally returns only genes with its original within-run BH q≤0.05.
That returned subset is too narrow for a complete relaxed-q or non-core-MT
analysis. The broad implementation therefore reconstructs every explicit
pre-FDR candidate test and checks the stock returned rows for exact parity.

### Complete test families by primary run

| Primary directional run | Effective background | All explicit tests | Core-MT tests | Non-core-MT BH family | Stock q≤0.05 returns |
|---|---:|---:|---:|---:|---:|
| Astrocytes `F_e4`, down | 7,828 | 160 | 9 | 151 | 2 |
| Astrocytes `M_e33`, down | 7,828 | 80 | 2 | 78 | 0 |
| OPCs `F_e4`, down | 7,817 | 137 | 4 | 133 | 9 |
| **Total** | **23,473** | **377** | **15** | **362** | **11** |

The 11 stock returns are a parity and audit result, not the input to the final
candidate funnel. Background genes outside the explicit candidate family are
also not assigned implicit `P = 1` rows here, because this direct branch does
not perform cross-run coverage or ACAT aggregation.

The 23,473 effective-background gene × run opportunities are not the starting
denominator for candidate selection. fKDA explicitly tests 377 potential
drivers that are reachable around the query and have directed downstream
layers; the remaining 23,096 background opportunities are outside that
explicit family and outside the within-run BH denominators.

## Step 4: Non-core-MT BH and final candidate gates

The query genes are core-MT, but final driver candidates must be
**non-core-MT**. The analysis first removes all explicitly tested candidates
annotated `core_mito_protein`, then recomputes BH separately within each
directional run:

```text
Astrocytes F_e4 down: 151 raw P values → one 151-gene BH family
Astrocytes M_e33 down: 78 raw P values → one 78-gene BH family
OPCs F_e4 down:        133 raw P values → one 133-gene BH family
```

The resulting field is `non_mt_run_q`. Here, “non-MT” in the schema means
“not `core_mito_protein`.” It does not exclude every mitochondria-associated
gene; `mito_extended` genes remain eligible.

After those full BH families have been computed, a relaxed-primary candidate
must satisfy all of:

```text
candidate is not core_mito_protein
query_overlap ≥ 2
fold_enrichment > 1
non_mt_run_q ≤ 0.10
```

The strict direct-reference flag uses the same relaxed-primary query and the
same overlap/enrichment rules, but requires:

```text
non_mt_run_q ≤ 0.05
```

The exact per-run candidate funnel is:

| Primary directional run | Non-core-MT tests | Overlap ≥2 | Also FE >1 | Also q≤0.10 | Also q≤0.05 |
|---|---:|---:|---:|---:|---:|
| Astrocytes `F_e4`, down | 151 | 4 | 4 | 2 | 2 |
| Astrocytes `M_e33`, down | 78 | 1 | 1 | 0 | 0 |
| OPCs `F_e4`, down | 133 | 10 | 10 | 10 | 7 |
| **Total** | **362** | **15** | **15** | **12** | **9** |

The table is displayed as a sequential selection funnel, but the q values are
not recomputed among the 15 overlap-positive rows. BH is computed first over
all 151, 78, or 133 non-core-MT explicit candidates in the corresponding run.
Filtering to overlap, fold enrichment, and q thresholds happens afterward.

The threshold boundaries are exact:

- overlap is inclusive: `query_overlap >= 2`;
- fold enrichment is exclusive: `fold_enrichment > 1`;
- relaxed q is inclusive: `non_mt_run_q <= 0.10`; and
- strict-reference q is inclusive: `non_mt_run_q <= 0.05`.

`original_run_q` is different: it is stock fKDA BH across all explicit genes,
including core-MT candidates. Of the 11 primary stock returns, `GLDC` and
`ME3` are core-MT query genes in the OPC run and are excluded as final drivers.
The other nine pass the strict non-core-MT reference. Relaxing the final
non-core-MT q threshold to 0.10 adds `FGF14`, `GRID1`, and `DENND1A`.

## Final primary candidates

The final inferential unit is:

```text
broad cell type + sex/APOE group + query direction + analysis gene symbol
```

The 12 relaxed candidate rows happen to represent 12 distinct genes in this
release. In general, the same gene could create multiple rows if it passed in
more than one category or direction.

| Broad-cell category and query direction | Relaxed-primary candidates in rank order | Strict subset |
|---|---|---|
| Astrocytes, `F_e4`, `AD_down_mito` | `ELL2`, `SLC44A3` | Both |
| Astrocytes, `M_e33`, `AD_down_mito` | None | None |
| OPCs, `F_e4`, `AD_down_mito` | `CAMK2D`, `RAPGEF4`, `RAB3IP`, `FOXN3`, `AC092691.1`, `FAM13A`, `NCOA1`, `FGF14`, `GRID1`, `DENND1A` | First seven |

`NCOA1` is annotated `mito_extended`, illustrating that the final rule removes
core-MT candidates rather than every gene with a mitochondrial association.

`AD_down_mito` describes the direction of the mitochondrial DEG query. It does
not assert that a candidate driver gene is itself downregulated or even a DEG.

### Category-level accounting

The 42 structural broad-cell × sex/APOE categories end in these mutually
exclusive states:

| Category outcome | Categories | Meaning |
|---|---:|---|
| Source contrast not estimable | 2 | No stratum-specific contrast result, hence neither direction can run |
| No eligible primary direction | 37 | DEG source exists, but neither relaxed direction reaches query size 3 |
| Completed with no selected candidate | 1 | Astrocytes `M_e33`; KDA ran successfully and returned an empty final set |
| Completed with at least one candidate | 2 | Astrocytes `F_e4` and OPCs `F_e4` |
| **Total** | **42** | |

A completed empty result is valid, not a computation failure. All three
eligible primary calls completed, and the release has zero failed KDA runs.

## Query-tier sensitivities

Strict and exploratory DEG-query tiers are rerun separately. They are never
used to fill an empty relaxed-primary slot:

| Query tier | Source unavailable | No provisional query | Lost after background | Effective 1–2 | Effective 3–9 | Effective ≥10 | Executable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict | 4 | 66 | 3 | 9 | 2 | 0 | 2 |
| Relaxed primary | 4 | 61 | 4 | 12 | 2 | 1 | 3 |
| Exploratory | 4 | 54 | 3 | 16 | 4 | 3 | 7 |

Every tier row partitions 84 directional slots. The three tiers have different
query definitions. They are alternative nested query sets, so their counts
must not be added together:

| Query tier | DEG rule | Provisional core-MT memberships |
|---|---|---:|
| Strict | q `< 0.05` and `abs(logFC) > log2(1.3)` | 43 |
| Relaxed primary | q `<= 0.10` and `abs(logFC) >= log2(1.2)` | 65 |
| Exploratory | q `<= 0.20`, no fold-change cutoff | 141 |

Two uses of “strict” must not be confused:

- **Strict query sensitivity** rebuilds KDA queries using the strict DEG tier.
- **Strict direct reference** keeps the relaxed-primary query and changes the
  final driver threshold from q≤0.10 to q≤0.05.

Sensitivity results remain labeled by their query tier and are not added to
the 12 relaxed-primary candidates.

## Why there is no ACAT stage

The fine-cell Phase 20 analysis has multiple fine-cell/direction KDA runs to
combine within a broad category. This direct broad analysis instead has at
most one KDA run for one broad-cell category and one query direction.

Therefore this branch does not calculate:

- implicit cross-run `P = 1` evidence rows;
- usable-run coverage;
- ACAT P values or category ACAT q values;
- supporting-run counts or fine-type recurrence;
- leave-one-fine-type-out stability; or
- any combined up/down q value.

The direct `non_mt_run_q` is the final q value for one gene in one broad-cell ×
sex/APOE × direction run. Up and down remain separate. The category summary's
union of gene names is descriptive only and has no combined inferential q
value.

## Complete list of ways the funnel can narrow

| Stage | Why the count can decrease | Observed primary loss |
|---|---|---:|
| Source DEG contrast | Fewer than five eligible donors in either arm makes the stratum-specific contrast not estimable | 2 contrasts, producing 4 slots |
| Shared model or contrast execution | Invalid covariates, a rank-deficient shared model, or a contrast-test error would be a failure rather than `not_estimable` | 0 failed contrasts |
| Relaxed DEG query | No core-MT DEG passes q, fold-change, and direction rules | 61 slots |
| Network mapping | Every provisional query gene is absent from the tested-gene-induced background | 4 slots; 30 memberships lost overall |
| Query-size gate | Only 1–2 effective query genes remain | 12 slots |
| Candidate class | Explicit candidate is `core_mito_protein` | 15 of 377 tests |
| Query overlap | Candidate's best-layer neighborhood contains fewer than two query genes | 347 of 362 non-core-MT tests |
| Fold enrichment | Enrichment is not strictly greater than one | 0 of the 15 overlap-qualified tests |
| Within-run FDR | Full-family `non_mt_run_q` exceeds 0.10 | 3 of the 15 overlap/enrichment-qualified tests |

The following fields do not remove relaxed-primary candidates:

- `stock_global_key_driver`, root-node status, and graph degree;
- small-query versus at-least-ten query labels;
- top-five or top-ten display limits; and
- results from the strict or exploratory query-tier sensitivities.

## Interpretation boundaries

- No provisional query means no relaxed core-MT DEG passed the specified rule;
  it does not necessarily mean there were no DEGs of any kind.
- A query lost during network mapping reflects tested-network coverage, not
  evidence that the mitochondrial signal is biologically absent.
- A query below three genes is insufficient for the prespecified KDA call; it
  is not a tested negative result.
- A completed run with no candidate means no explicitly tested non-core-MT gene
  passed all overlap, enrichment, and full-family q gates.
- A gene passing in one sex/APOE category but not another is not a formal test
  of heterogeneity between those categories.
- A key-driver result is a network-enrichment association, not proof of
  biological causality.

## Implementation and audit authorities

The installed local-production release is `validated_complete`: all 31
blocking checks pass, and no primary KDA call failed.

- [Broad KDA plan and execution report](phase20_sex_apoe_kda_broad_plan.md)
- [Broad KDA configuration](../../config/phase20_sex_apoe_kda_broad.yml)
- [Broad KDA implementation](../../scripts/20_sex_apoe_kda_broad.py)
- [Phase 08 broad DEG status](../../results/minerva_production/08_deg_broad/broad_deg_status.tsv)
- [Phase 08 broad DEG filter funnel](../../results/minerva_production/08_deg_broad/broad_deg_filter_funnel.tsv)
- [Broad KDA direction manifest](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_direction_manifest.tsv)
- [Broad KDA complete candidate tests](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_all_candidate_tests.tsv.gz)
- [Broad KDA machine-readable filter funnel](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_filter_funnel.tsv)
- [Broad KDA final candidates](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_non_mt_candidates.tsv)
- [Broad KDA validation checks](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_checks.tsv)
- [Broad KDA release status](../../results/minerva_production/20_sex_apoe_kda_broad/phase20_broad_status.tsv)
