# Investigation of Sparse Positive Mitochondrial Similarity Scores

## Conclusion

I found no scoring, ranking, or gene-mapping bug. The scarcity of positive
mitochondrial similarity scores is a real consequence of the ternary score
definition combined with sparse, imbalanced mitochondrial DEG calls.

| Comparison | Eligible core-MT features | Positive scores | Plotted highest block: positive / zero / negative |
|---|---:|---:|---:|
| Female vs Male, all APOE | 700 | 3 (0.43%) | 3 / 11 / 11 |
| e2 vs e33 | 708 | 2 (0.28%) | 2 / 23 / 0 |
| e4 vs e33 | 686 | 7 (1.02%) | 7 / 18 / 0 |
| Female vs Male, e2 | 732 | 6 (0.82%) | 6 / 4 / 0 |
| Female vs Male, e33 | 705 | 8 (1.13%) | 8 / 2 / 0 |
| Female vs Male, e4 | 679 | 12 (1.77%) | 10 / 0 / 0 |

Thus, “highest similarity” currently means highest-ranked relative to the
other mitochondrial genes. It does not guarantee a positive score. This is
particularly noticeable in Figure 3, where 11 of the highest-ranked 25 scores
are still slightly negative.

## Why this happens

The Yu score implemented in
[`scripts/10_calculate_mitochondrial_similarity.R`](../../scripts/10_calculate_mitochondrial_similarity.R)
is:

\[
\text{score} =
\frac{\text{same-direction}
-0.5(\text{one-sided})
-\text{opposite-direction}}{N}
\]

Critically:

- `(0,0)`, nonsignificant in both groups, contributes zero—not positive
  similarity.
- A gene must be significantly changed in both groups in the same direction
  to receive positive evidence.
- Significance in only one group contributes `−0.5`.

Across eligible core-mitochondrial state pairs:

- 88.8–96.2% are `(0,0)`.
- Only 0.17–0.30% are significant in the same direction.
- 3.45–10.16% are significant in only one group.
- 0.13–0.86% are significant in opposite directions.

The negative one-sided component therefore greatly exceeds the positive
same-direction component.

The underlying DEG rates are also imbalanced:

- Female e33: 2.19% of tested mitochondrial states significant.
- Male e33: 2.64%.
- Female e4: 4.25%.
- Male e4: 2.63%.
- Female e2: 2.99%.
- Male e2: 9.71%.

The especially high Male-e2 DEG rate produces many one-sided comparisons,
which the Zhang–Yu metric correctly treats as divergence.

This pattern also exists in the inclusive `all_mito_related` universe, where
only 2–12 features per comparison have positive scores. It is therefore not
caused by restricting the figures to core MitoCarta genes.

## Checks performed

- Independently recomputed all 6,546 scoreable production scores from the
  702,000 underlying state-pair rows: maximum discrepancy was
  \(5\times10^{-16}\).
- Confirmed all 540 dimensions pair the intended sex/APOE contrasts.
- Confirmed every stored high tail is sorted by decreasing score and every
  low tail by increasing score.
- Confirmed Phase 11 retains 200/200 genes in every pathway query, with no
  duplicate-symbol collapse.
- Confirmed the figures retain every selected feature and all eight intended
  visible state-pair categories.
- Confirmed all 25 Phase 10 production checks and the four hand-calculated
  score tests pass.

The coverage filter does exclude a few positive scores, but appropriately:
the apparently strongest excluded values, such as `0.5`, are based on only
two paired tests when 26–27 are required. Including them would introduce
unstable high-score artifacts.

## Interpretation caveats

None of the primary core-mito scores—positive or negative—passes the Phase 10
gene-level directional BH FDR threshold. The significant results in the
low-tail pathway panels are pathway-level enrichment results, not significant
individual similarity scores.

The current Phase 10 inference is also more conservative than the incompletely
specified empirical-FDR procedure in
[`docs/yu_paper/Yu_sex_apoe.pdf`](../yu_paper/Yu_sex_apoe.pdf). This affects
significance, but not the observed scarcity or sign of the raw scores.

Yu’s own results place mitochondrial-function pathways among the
lowest-similarity APOE-e4 genes and identify MT-ND2 as strongly sex-divergent,
so the direction of the present mitochondrial-restricted result is
biologically consistent with the paper.

## Recommendation

Relabel the figure blocks as “Highest-ranked similarity (relative)” and add a
compact score-distribution summary. If the scientific question is shared
mitochondrial regulation below the DEG threshold, a continuous log-fold-change
concordance analysis would be a useful sensitivity analysis; changing the
ternary score itself would no longer be Yu-compatible.
