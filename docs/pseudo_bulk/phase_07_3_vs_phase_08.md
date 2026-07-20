# Phase 07.3 versus Phase 08 Differential-Expression Analysis

Both Phase 07.3 and Phase 08 perform differential gene-expression analysis, but they use different statistical units and models.

| Feature | Phase 07.3 | Phase 08 |
|---|---|---|
| Role | Primary inference | Secondary, paper-comparable analysis |
| Method | edgeR quasi-likelihood | Seurat `FindMarkers` with MAST |
| Statistical observation | One donor-level pseudobulk sample | One nucleus |
| Expression input | Summed raw RNA counts | Phase 05 log-normalized nucleus-level expression |
| Donor correlation | Handled by using one sample per donor and fine cell type | No donor random effect; nuclei from the same donor are treated as separate observations |
| Contrasts per fine cell type | Up to 14 | Up to 6 |
| Covariates | Age at death and PMI | Total RNA count per nucleus, age at death, and PMI |
| Main interpretation | Evidence that an effect is reproducible across donors | Cell-level expression/detection pattern comparable with the Yu study |

## Contrasts tested

Both phases test the same six direct AD-versus-NCI comparisons:

```text
AD vs NCI in Female e2
AD vs NCI in Female e33
AD vs NCI in Female e4
AD vs NCI in Male e2
AD vs NCI in Male e33
AD vs NCI in Male e4
```

Phase 07.3 additionally tests:

```text
3 sex interactions
4 APOE interactions
1 global heterogeneity test
```

Therefore:

```text
Phase 07.3: up to 6 + 3 + 4 + 1 = 14 contrasts
Phase 08:   up to 6 direct contrasts only
```

Phase 08 records the other eight Phase 07 contrasts as `not_applicable`. This is intentional: Phase 08 reproduces the paper-style binary AD-versus-NCI MAST comparisons, while the interaction and omnibus hypotheses remain part of the primary pseudobulk analysis.

## Phase 07.3: donor-level pseudobulk edgeR

For one fine cell type, counts from all eligible nuclei belonging to the same donor are summed:

```text
one donor × one fine cell type = one pseudobulk sample
```

edgeR then models raw pseudobulk counts using a design equivalent to:

```r
~ 0 + diagnosis_sex_APOE_group + age_death_scaled + pmi_scaled
```

It performs:

1. Gene filtering with `filterByExpr`.
2. TMM normalization.
3. Dispersion estimation across donors.
4. Negative-binomial quasi-likelihood fitting.
5. Testing of every eligible contrast.

If the model contains 100 donor pseudobulk samples, its biological replication is approximately 100 donors—not the thousands of nuclei underlying them.

This is the project's primary analysis because the donor is the independent biological unit.

## Phase 08: nucleus-level MAST

Phase 08 uses the Phase 05 normalized Seurat object and selects individual nuclei from the same eligible donors used by the matching Phase 07 direct contrast.

It runs:

```text
Seurat FindMarkers
ident.1         = AD
ident.2         = NCI
test.use        = MAST
slot            = data
min.pct         = 0.10
logfc.threshold = 0
latent.vars     = nCount_RNA;age_death_scaled;pmi_scaled
```

MAST uses a hurdle model that considers:

- whether expression is detected in a nucleus; and
- the expression level among expressing nuclei.

A donor with 10,000 nuclei consequently contributes many more observations than a donor with 20 nuclei. Age and PMI are repeated on every nucleus from the donor, but this does not model the correlation among nuclei from the same donor.

Therefore, MAST can produce extremely small p-values because of the large number of nuclei, even when the number of independent donors is modest.

## Gene filtering differs

Phase 07.3:

- Uses `filterByExpr` on donor-level pseudobulk counts.
- Filters genes once for the fine-cell-type model.
- Normally tests every retained gene in every eligible contrast for that model.

Phase 08:

- Applies `min.pct = 0.10` separately for every AD-versus-NCI comparison.
- Requires a gene to be detected in at least 10% of AD or NCI nuclei.
- Can return different gene sets for different contrasts.
- Uses no fold-change prefilter.

Phase 08 defines `paper_deg = TRUE` when all three conditions hold:

```text
within-contrast FDR < 0.05
absolute log2 fold change > log2(1.3), approximately 0.379
detected in at least 10% of AD or NCI nuclei
```

## How to interpret the analyses together

Phase 07.3 answers:

> Is there evidence for an expression difference across independent donors?

Phase 08 answers:

> Is there a nucleus-level expression/detection difference using the paper's MAST procedure?

The strongest evidence is generally:

```text
same effect direction in both methods
+ convincing donor-level Phase 07 result
+ supportive Phase 08 result
```

If Phase 08 is significant but Phase 07.3 is not, the apparent signal may be influenced by:

- the very large nucleus count;
- donors contributing unequal numbers of nuclei;
- within-donor correlation;
- different gene-filtering rules; or
- a cell-detection pattern that is not strong across donors.

For this reason, the research plan treats Phase 07.3 as primary and Phase 08 as secondary. Phase 08 output directly includes:

- `pseudobulk_logFC`;
- `pseudobulk_fdr`; and
- `direction_concordant_with_pseudobulk`.

These columns are specifically provided to compare the two methods for the same gene, fine cell type, and direct AD-versus-NCI contrast.

## Practical interpretation table

| Phase 07.3 result | Phase 08 result | Suggested interpretation |
|---|---|---|
| Supported, same direction | Supported | Strongest cross-method evidence; donor-level and nucleus-level analyses agree. |
| Supported | Not supported | Donor-level effect may not meet the MAST detection/effect criteria, or method-specific filtering and modeling may differ. |
| Not supported | Supported | Treat cautiously; the large number of correlated nuclei may produce strong cell-level evidence without strong replication across donors. |
| Supported, opposite direction | Supported, opposite direction | Investigate immediately; verify contrast orientation, gene matching, donor/cell composition, filtering, and model diagnostics. |
| Not supported | Not supported | No evidence under either prespecified method, subject to power and eligibility limitations. |

Statistical significance should not be compared by asking which method has the smaller p-value. The methods use different observational units, likelihoods, filters, and covariates. Compare effect direction, effect magnitude, donor support, detection, rank, FDR within its declared scope, and model diagnostics.
