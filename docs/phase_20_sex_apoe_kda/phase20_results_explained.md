# Phase 20 ROSMAP Sex/APOE × Broad-Cell Non-MT KDA Results

## Release status and analysis scope

The canonical fine-cell Phase 20 v2 release completed locally with
`validation_status == validated_complete` and zero failed checks:

```text
results/minerva_production/20_sex_apoe_kda/
```

This release reaggregates complete KDA evidence reconstructed from the
validated Phase 12 primary runs at the KDA execution minimum of **three
effective query genes**. It includes 295 fine-cell × sex/APOE × direction
runs, not only the 161 runs with at least ten query genes that were included
in the historical Phase 18 release.

The historical Phase 18 release is unchanged. Its ≥10-gene, 161-run subset is
retained only as a frozen historical comparison and passed an exact parity
check within its original non-MT evidence universe.

The Phase 20 output contract also verifies input hashes, source validation,
run and category counts, candidate yields, uniqueness, rank constraints, and
that every aggregate and candidate is a non-core-MT gene.

## From runs to candidates

The canonical source and aggregation counts are:

```text
648 structural fine-cell × group × direction slots
  −6 source-unavailable directional slots (from 3 contrasts)
  −347 source slots below the 3-gene KDA execution minimum
= 295 included KDA runs at effective query size ≥3
  → 2,623,910 complete gene × run opportunity rows
  → 259,548 non-MT gene × category aggregate units
  → 233,368 pass coverage ≥0.50
  → 500 also have at least one relaxed supporting run
  → 74 also pass within-category ACAT q ≤0.10
```

Among the 295 included runs, 221 had at least one Phase 12 significant return
and 74 had none. An empty returned list is not a failed run: its complete
candidate-test opportunities still enter the reconstructed evidence table.

## Main result

The relaxed discovery rule produced:

- 74 non-MT gene × category candidates, representing 37 distinct genes;
- candidates in 16 of the 38 analyzable categories;
- 48 candidate rows in compact top-five displays;
- 63 candidate rows in detailed top-ten displays; and
- 15 additional exploratory-only rows at `0.10 < category q <= 0.20`.

The strict non-MT reference produced 58 candidates, representing 30 distinct
genes, across 15 categories. All 58 are among the 74 relaxed candidates; the
relaxed rule adds 16 candidate units. The exploratory-inclusive tier contains
89 units across 17 categories: the 74 main candidates plus the 15
exploratory-only leads.

All 42 structural categories remain in the category manifest. Thirty-eight
contain at least one included run and four are explicitly marked
`not_estimable_no_included_runs`; empty categories are not backfilled.

## Leading driver in each supported category

| Sex/APOE | Broad cell type | Top driver | Relaxed category q | Candidates |
|---|---|---:|---:|---:|
| F_e2 | Astrocytes | RPL11 | 5.00e-4 | 4 |
| F_e2 | Excitatory neurons | RPL11 | 7.74e-8 | 11 |
| F_e33 | Excitatory neurons | TMEM147 | 2.66e-3 | 6 |
| F_e33 | OPCs | RPS15 | 1.98e-6 | 3 |
| F_e4 | Astrocytes | RPL15 | 2.49e-2 | 1 |
| F_e4 | Excitatory neurons | RPL11 | 1.20e-7 | 9 |
| F_e4 | Inhibitory neurons | RPS15 | 1.14e-2 | 1 |
| M_e2 | Astrocytes | RPL11 | 2.08e-5 | 5 |
| M_e2 | Excitatory neurons | RPL11 | 1.62e-9 | 20 |
| M_e2 | Inhibitory neurons | RPS15 | 1.29e-2 | 3 |
| M_e2 | OPCs | RPS15 | 1.23e-12 | 5 |
| M_e2 | Oligodendrocytes | RPL11 | 7.85e-2 | 1 |
| M_e33 | Excitatory neurons | WDR82 | 2.32e-2 | 1 |
| M_e33 | Microglia | HSPH1 | 8.56e-3 | 2 |
| M_e4 | Inhibitory neurons | RPS15 | 3.49e-2 | 1 |
| M_e4 | Microglia | RPL11 | 1.73e-2 | 1 |

`M_e2` contributes 34 of the 74 candidate units. Excitatory neurons
contribute 47. These yields reflect highly unequal run and fine-cell-type
coverage, so list presence must not be interpreted as a formal between-group
difference.

## Recurring drivers and evidence labels

RPL11 occurs in seven supported categories and RPS15 in six. ATG101, LAMTOR5,
PSMB6, RPL15, RPLP1, RPLP2, RPS13, SELENOW, TMEM147, and WDR82 each occur in
three.

The primary evidence labels among the 74 main candidate units are:

| Evidence label | Candidate units |
|---|---:|
| `recurrent_stable` | 51 |
| `localized_single_fine_type` | 8 |
| `strict_non_mt_reference` | 9 |
| `relaxed_phase20_candidate` | 3 |
| `single_run_evidence` | 3 |

The label `strict_non_mt_reference` is assigned only when the strict gate
passes but a higher-priority recurrence/stability label does not. Use the
separate Boolean `strict_non_mt_reference` column to count all 58 strict
candidates.

## Primary files

- `phase20_relaxed_candidates.tsv`: all 74 main candidate units.
- `phase20_top10.tsv`: 63 displayed candidates plus explicit empty-list rows.
- `phase20_top5_summary.tsv`: 48 displayed candidates plus explicit
  empty-list rows.
- `phase20_driver_aggregates.tsv.gz`: all 259,548 non-MT gene × category
  aggregate units.
- `phase20_category_manifest.tsv`: all 42 structural categories.
- `phase20_strict_non_mt_reference_candidates.tsv`: 58 strict candidates.
- `phase20_exploratory_leads.tsv`: 15 exploratory-only leads.
- `phase20_filter_funnel.tsv`: exact overall and per-category reductions.
- `phase20_checks.tsv` and `phase20_status.tsv`: validation authority.
- `phase20_artifacts.tsv`: output sizes and SHA-256 hashes.

The snapshotted source evidence under `00_inputs/` contains 2,623,910
gene × run opportunity rows and the 648-slot run manifest used to determine
the 295 included runs.

## Interpretation boundary

These are within-category key-driver results. A driver appearing in one
sex/APOE list and not another is not evidence that its effect differs between
those groups. A formal comparison would require a separate balanced
heterogeneity analysis.
