# Simple returned-only Phase 20 KDA aggregation

> **AUTHORITATIVE (2026-08-29).** This returned-only simple aggregation is the
> authoritative Phase 20 sex/APOE result. It supersedes the fine-cell
> coverage/support candidate selection
> (`results/minerva_production/20_sex_apoe_kda (deprecated)`) and the direct
> broad-cell analysis
> (`results/minerva_production/20_sex_apoe_kda_broad (deprecated)`).

This directory implements the requested exploratory rule over the frozen
Phase 20 set of **295 KDA calls**:

1. Retain only rows returned as significant by stock `call_key_drivers()`.
2. Use the returned within-call adjusted P value (`adjusted_p_value`) as the
   input q value.
3. If a gene has one returned row in the aggregation scope, copy that q value
   to `returned_run_q_acat_score` unchanged.
4. If a gene has two or more returned rows, equal-weight ACAT-combine those
   returned q values and store the result as `returned_run_q_acat_score`.
5. Do not apply another across-gene BH adjustment, because doing so would
   change singleton q values and violate step 3.

Two views are provided:

- `simple_global_gene_aggregates.tsv`: one row per gene across all included
  calls; this is the literal interpretation of "multiple calls".
- `simple_category_gene_aggregates.tsv`: one row per
  `signature_group + broad_network + gene`, preserving the Phase 20
  sex/APOE-by-broad-cell categories.

`simple_returned_call_rows.tsv.gz` contains the exact 2,494
stock returned rows and connects every row to both aggregate views.
`simple_category_summary.tsv` preserves all 42 structural categories.

## Interpretation warning

`returned_run_q_acat_score` is the canonical post-selected exploratory value.
`requested_final_q` is an identical alias included to match the requested
terminology. Neither is a formally FDR-controlled cross-call q value: the input rows were selected
for within-call significance, ACAT is being applied to adjusted values rather
than the complete raw-P family, and no final across-gene multiplicity
correction is performed. Use it for comparison and ranking, not confirmatory
error-rate claims.
