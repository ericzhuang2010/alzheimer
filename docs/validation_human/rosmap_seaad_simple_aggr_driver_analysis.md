# ROSMAP × SEA-AD key-driver overlap after simple aggregation

**Date:** 2026-08-29
**Scope:** Fine-cell sex/APOE groups only, after the returned-only non-MT simple aggregation — the results presented in `docs/presentations/phase20_sex_apoe_kda_fine_broad.pptx`.

**Sources:**

- ROSMAP: `results/minerva_production/20_sex_apoe_kda_simple_aggr/simple_category_gene_aggregates.tsv` (689 non-MT gene × category units, 433 genes)
- SEA-AD: `results/validation_human/11_sex_apoe_kda_simple_aggr/simple_category_gene_aggregates.tsv` (96 units, 91 genes)

Both tables were filtered to `case_id = non_mt_driver` and `is_core_mito = FALSE`, and display ranks were recomputed within each `signature_group × broad_network` category by `returned_run_q_acat_score`, then gene symbol — the same rule the deck's figures use.

## Category-matched overlap (same sex/APOE group × broad cell type — the deck's counting unit)

8 of SEA-AD's 96 units land on the identical gene and category in ROSMAP:

| Category | Gene | SEA-AD q (rank) | ROSMAP q (rank) |
|---|---|---|---|
| F_e33 · Excitatory | **WDR82** | 0.028 (#1) | 0.000097 (#5, 11 calls) |
| F_e33 · Excitatory | DMTF1 | 0.045 (#2) | 0.043 (#42) |
| F_e33 · Excitatory | TPP2 | 0.048 (#3) | 0.048 (#48) |
| M_e33 · Excitatory | **TTC8** | 0.0076 (#3, ACAT of 4 calls) | 0.020 (#24) |
| M_e33 · Inhibitory | RPL30 | 0.0008 (#3) | 0.048 (#27) |
| M_e33 · Inhibitory | **RPS15** | 0.020 (#9) | 0.036 (#20) |
| M_e33 · Inhibitory | PAFAH1B1 | 0.027 (#19) | 0.046 (#26) |
| M_e33 · Inhibitory | PIP5K1A | 0.027 (#20) | 0.049 (#30) |

Notable points:

- **WDR82 is the cleanest replication story.** It is SEA-AD's #1 gene in F_e33 excitatory neurons, and ROSMAP has it at rank 5 in the *same* category (from 11 returned calls) — so it appears as a tile on **both** cohorts' top-five figures in the deck. It is also on both recurrence charts.
- **All three SEA-AD F_e33 excitatory genes (WDR82, DMTF1, TPP2) match ROSMAP** — that entire (small) female category replicates at the gene level.
- **RPS15**, the headline recurrent gene of the ROSMAP part (12 categories, deck slide 9), re-emerges in SEA-AD in M_e33 inhibitory neurons, though it just misses the SEA-AD recurrence top-20 display.

## Gene-level overlap (any category)

35 of SEA-AD's 91 non-MT genes (38%) appear somewhere among ROSMAP's 433:

B3GALNT1, BABAM2, BEX3, BRD1, CEP57, CSTF2, DHDDS, DIDO1, DMTF1, DYNLT1, EVA1C, GATAD1, HGSNAT, HSPA1A, LIFR-AS1, METTL26, NDFIP2, PAFAH1B1, PHTF2, PIP5K1A, POLR3F, RFLNA, RFTN2, RPL21, RPL30, RPL38, RPS15, RPS27A, SELENOM, SMIM19, STXBP5, TARBP1, TPP2, TTC8, WDR82.

Of these, four sit on **both recurrence figures** in the deck: **BEX3, DYNLT1, SELENOM, TTC8** (SEA-AD's top recurrent gene HGSNAT is in ROSMAP too, but in different categories, so it is not a category match).

## Sex/APOE-resolved analysis

SEA-AD can only test two groups: F_e33 (3 genes) and M_e33 (88 genes). F_e4 had one active call but zero non-MT returns, and the remaining groups had no active call, so sex/APOE-level validation is effectively an M_e33 comparison plus a tiny F_e33 slice.

### F_e33: perfect but tiny

All 3 SEA-AD F_e33 genes (WDR82, DMTF1, TPP2) match ROSMAP's F_e33 excitatory category exactly — same group, same network. With n = 3 this is anecdotal, but it is a 100% category-level replication of the only female SEA-AD category.

### M_e33: gene overlap is real, but it is not group-specific

Of SEA-AD's 88 M_e33 genes, 32 appear anywhere in ROSMAP — yet only 8 of them in ROSMAP's own M_e33 group. Overlap counts of the 32 genes against each ROSMAP group gene set (hypergeometric enrichment P against the 433-gene ROSMAP background, descriptive only):

| ROSMAP group | Group size | Overlap with SEA-AD M_e33 | P(X ≥ k) |
|---|---|---|---|
| M_e2 | 121 | **14** | 0.03 |
| F_e33 | 85 | 10 | 0.07 |
| F_e4 | 125 | 9 | 0.61 |
| M_e4 | 123 | 9 | 0.59 |
| **M_e33 (matching group)** | 93 | 8 | 0.38 |
| F_e2 | 94 | 7 | 0.57 |

The matching group is near the bottom: ROSMAP M_e2 shares the most genes with SEA-AD M_e33. There is also no detectable e33-specificity (16 of the genes sit in ROSMAP's e33 union vs 23 in the non-e33 union) and no strong sex fidelity — among the 32 shared M_e33 genes, ROSMAP shows 14 as male-only, 11 as female-only, and 7 in both sexes:

- ROSMAP male-only (14): BABAM2, BRD1, EVA1C, **HGSNAT**, METTL26, NDFIP2, PAFAH1B1, PIP5K1A, RFLNA, RFTN2, RPL30, RPL38, RPS27A, **TARBP1**
- ROSMAP female-only (11): B3GALNT1, CEP57, CSTF2, DHDDS, DIDO1, GATAD1, LIFR-AS1, PHTF2, POLR3F, SMIM19, STXBP5
- ROSMAP both sexes (7): BEX3, DYNLT1, HSPA1A, RPL21, RPS15, SELENOM, TTC8

### Cell-type context replicates better than sex/APOE context

Pairing every SEA-AD unit with every ROSMAP unit of the same gene gives 84 pairs: 62% share the broad cell type (vs ≈41% expected from random pairing of the two network distributions), but only 13% share the sex/APOE group. Cross-cohort convergence is therefore mostly a gene-in-cell-type phenomenon; the sex/APOE stratum in which a gene returns is largely not preserved. Examples: CSTF2, DHDDS, DIDO1, POLR3F, B3GALNT1, and SMIM19 are excitatory-neuron drivers in both cohorts but flip from ROSMAP F_e33 to SEA-AD M_e33.

### Gene-level stories

- **HGSNAT** (SEA-AD's top recurrent gene): male-consistent across cohorts and APOE strata — ROSMAP has it only in M_e2 and M_e4 excitatory neurons; SEA-AD adds M_e33 (excitatory and inhibitory). It never appears in a female category in either cohort.
- **TARBP1 and RPS27A** are similarly male-only in both cohorts.
- **WDR82** is excitatory-only in all four of its ROSMAP groups (F_e2, F_e33, M_e33, M_e4) and in SEA-AD F_e33 — a cell-type-faithful driver whose strongest shared stratum is F_e33.
- **RPS15, SELENOM, TTC8, BEX3, DYNLT1** are ROSMAP pan-group recurrent genes (5–12 categories) that also return in SEA-AD; their reappearance is expected from breadth rather than stratum-specific replication.

## Caveats

- SEA-AD has only 4 return-bearing categories (F_e33 excitatory; M_e33 excitatory, inhibitory, oligodendrocytes) and 40 of its 42 active calls are M_e33, so category-matched overlap is only *possible* in those four categories, and the group-resolved comparison is effectively powered only for M_e33.
- The hypergeometric values use the 433 ROSMAP non-MT genes as a rough background; they are descriptive context, not calibrated tests.
- Both scores are exploratory, post-selected, returned-only values (singleton within-call BH q passthrough or equal-weight ACAT of returned q values) with no across-gene FDR control. Matched genes are descriptive convergence, not formal replication tests.
