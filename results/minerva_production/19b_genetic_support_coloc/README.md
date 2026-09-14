# Phase 19b colocalization gate and final gene table

This validated WS5 bundle enumerates 2,152 QTL-by-GWAS-trait decisions. Forty-
seven routes have both a source-significant QTL signal and regional GWAS
signal. All 47 are terminally `not_assessable`: the released QTL fine-mapping
tables contain PIP/credible-set summaries rather than complete fitted
multi-signal models, and compatible source-matched LD/full QTL statistics are
absent.

`colocalization.tsv.gz` is a valid header-only gzip file because no valid H0-H4
test was possible. This is not a negative colocalization result.
`final_gene_evidence.tsv` keeps Tier 1 and corrected MAGMA gene-level support
separate from regional and QTL annotations.
