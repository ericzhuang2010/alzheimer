# Phase 12 circular figure: recommended key-driver sort order

## Bottom line

For the key-driver genes in
`results/figures/analysis/phase12_kda/circular_figure/phase12_kda_circular.png`, the most
paper-faithful interpretation of the professor's comment is:

> Rank key drivers in descending order of the standardized **MeanOfLog** score
> across their KDA runs.

For key driver \(g\) across \(K\) runs, this score is

\[
S_g = \frac{1}{K}\sum_{r=1}^{K} -\log(p_{g,r}),
\qquad
S_g^{\mathrm{std}} = \frac{S_g}{\max_g S_g}.
\]

Genes with larger scores should appear first. Standardization changes the
reported scale but not the ordering.

This is almost certainly the "combined p-value and the mean of something" the
professor was recalling: it is the **mean of the negative log p-values**, not
the mean fold enrichment. With the same number of runs per gene, it gives the
same ordering as Fisher's sum-of-log-p statistic.

## Evidence from the related papers and code

The Wang multiscale-modeling paper reports a "KDP ranking score" in its
supplementary Table S4. The authors' released ranking script calculates several
ways to aggregate KDA p-values—ACAT, ProductOfRank, MeanOfLog, and
MeanOfLogLog—but explicitly orders the final results by `MeanOfLog`, decreasing.

- [Wang paper's released KDP ranking script](https://github.com/wange230/proteomics_networks/blob/main/codes/Baysian_network/KDA_analysis/PHG_protein_bnGlobalKDA_ranking.R)
- [NetWeaver implementation of `ensemble_rank`](https://github.com/mw201608/NetWeaver/blob/master/R/ensemble.rank.R)
- [NetWeaver ACAT implementation](https://github.com/mw201608/NetWeaver/blob/master/R/ACAT.R)
- Local related paper: [wang_multiscale_modeling.pdf](../related_papers/wang_multiscale_modeling.pdf)
- Local related paper: [mathys single-cell atlas reveals correlates.pdf](<../related_papers/mathys single-cell atlas reveals correlates.pdf>)

The Mathys paper also describes aggregating correlated p-values with Fisher's
sum-log method as the primary analysis and a Cauchy combination test as a
sensitivity analysis. That passage is about protein-complex aggregation rather
than key-driver ranking, so the Wang KDP script is the more direct precedent
for this figure.

## What the current figure does

The selection logic in
[`scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R`](../../scripts/figures/analysis/phease12_kda/visualize_phase12_kda_netweaver.R)
currently orders genes within each network by:

1. number of significant runs, descending;
2. minimum adjusted p-value, ascending;
3. maximum fold enrichment, descending;
4. gene symbol.

It then selects the top five genes per network. This is not the ranking method
used for the KDP ranking in the Wang paper.

## Recommended implementation

1. Construct a complete key-driver-by-run p-value matrix for each network.
2. For the main analysis, use the **primary directional** KDA runs
   (`analysis_tier == "primary"` and directions `AD_up_mito` or
   `AD_down_mito`).
3. Exclude secondary signature pools and `AD_both` from the main ranking,
   because they overlap with or are derived from the directional signatures.
4. Calculate each gene's `mean_of_log_score` from all relevant runs and
   standardize it within the comparison set.
5. Sort by `mean_of_log_score_standardized`, descending, and choose the top
   five genes per network for the circular plot.
6. Optionally report an ACAT combined p-value as a sensitivity result, but use
   MeanOfLog for the displayed order to match the published KDP workflow.
7. Keep mean fold enrichment as a descriptive annotation or a final tie-breaker
   only; it should not be the primary ranking score.

Suggested output fields are:

- `mean_of_log_score`
- `mean_of_log_score_standardized`
- `ranking_runs`
- optional `acat_combined_p`
- optional `mean_fold_enrichment`

## Important implementation caveat

Do **not** calculate this score directly from
`results/minerva_production/12_kda/kda_results.tsv`. That table contains only
significant KDA calls, so aggregating it would omit nonsignificant tests and
systematically favor genes based on which results survived filtering.

Likewise, `kda_key_driver_summary.tsv` contains only summaries such as the
minimum adjusted p-value and maximum fold enrichment; it does not contain the
complete p-value matrix required for MeanOfLog or a valid combined p-value.

The Phase 12 pipeline should first export or reconstruct the complete tested
candidate-by-run p-value matrix, including nonsignificant candidates. The
circular figure should be rerendered from that complete matrix. A ranking made
only from the significant-results table should be labeled an approximation and
should not be used as the final paper figure.

## Recommended wording for the method or figure notes

> Within each cell-type network, key drivers were ranked by the standardized
> mean negative log KDA p-value across the primary directional mitochondrial
> DEG signatures. Higher scores indicate stronger and more consistent evidence
> across KDA runs. Secondary and combined-direction signatures were excluded
> from the primary ranking to avoid double-counting overlapping signatures.
