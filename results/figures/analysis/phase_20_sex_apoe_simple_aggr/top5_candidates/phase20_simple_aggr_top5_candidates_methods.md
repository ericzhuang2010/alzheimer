# Methods

The renderer reads the validated `simple_category_gene_aggregates.tsv` table from `results/minerva_production/20_sex_apoe_kda_simple_aggr` and verifies its registered SHA-256 hash, source completion status, and source checks. Rows are restricted to `case_id = non_mt_driver` and `is_core_mito = FALSE` before figure-specific ordering. No KDA or ACAT calculation is rerun. The stored all-class rank is not reused: non-MT rows are ordered within each `signature_group × broad_network` category by `returned_run_q_acat_score`, then gene symbol, and assigned a new display rank.

The score is the requested exploratory returned-only value: a singleton stock within-call BH q is passed through unchanged, whereas two or more returned q values are combined by equal-weight ACAT. It is post-selected and is not a formally FDR-controlled cross-call q value; the figures are descriptive rankings of stock-significant returns.

For the top-five display, ranks 1–5 after non-MT filtering are retained without backfilling or an additional significance threshold. This leaves 149 plotted gene-category rows across 32 categories. The word “candidates” names the requested display and does not imply a new confirmatory error-rate claim.
