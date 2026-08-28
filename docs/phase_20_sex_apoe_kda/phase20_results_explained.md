# Phase 20 ROSMAP Sex/APOE × Broad-Cell Non-MT KDA Results

## Release status

Phase 20 completed locally with validation status validated_complete and zero
failed checks. The machine-readable release is:

~~~text
results/minerva_production/20_sex_apoe_kda/
~~~

The independent output-contract test passed, including input hashes, Phase 18
parity, candidate yields, uniqueness, rank constraints, and the assertion that
every aggregate and candidate is a non-MT gene.

## Main result

The relaxed discovery rule produced:

- 78 non-MT gene × category candidates;
- candidates in 15 of the 27 analyzable categories;
- 50 candidates in compact top-five displays;
- 65 candidates in detailed top-ten displays; and
- 16 additional exploratory-only leads at 0.10 < category q ≤0.20.

The strict non-MT reference produced 64 candidates across 14 categories. Thus
64 of the 78 relaxed candidates also pass the strict reference, while 14 are
added by the relaxed thresholds.

All 42 structural categories remain in the category manifest. Fifteen have no
frozen Phase 18 runs and are explicitly marked not estimable; they are not
backfilled.

## Leading driver in each supported category

| Sex/APOE | Broad cell type | Top driver | Relaxed category q | Candidates |
|---|---|---:|---:|---:|
| F_e2 | Astrocytes | RPL11 | 1.69e-4 | 5 |
| F_e2 | Excitatory neurons | RPL11 | 5.40e-8 | 13 |
| F_e33 | Excitatory neurons | TMEM147 | 1.84e-3 | 6 |
| F_e33 | OPCs | RPS15 | 1.98e-6 | 3 |
| F_e4 | Astrocytes | RPL15 | 2.07e-2 | 1 |
| F_e4 | Excitatory neurons | RPL11 | 9.19e-8 | 9 |
| F_e4 | Inhibitory neurons | RPS15 | 3.81e-3 | 3 |
| M_e2 | Astrocytes | RPL11 | 2.08e-5 | 5 |
| M_e2 | Excitatory neurons | RPL11 | 1.50e-9 | 20 |
| M_e2 | Inhibitory neurons | RPS15 | 9.91e-3 | 4 |
| M_e2 | OPCs | RPS15 | 1.23e-12 | 5 |
| M_e2 | Oligodendrocytes | RPL11 | 7.85e-2 | 1 |
| M_e33 | Excitatory neurons | WDR82 | 1.50e-2 | 1 |
| M_e4 | Inhibitory neurons | RPS15 | 7.05e-3 | 1 |
| M_e4 | Microglia | RPL11 | 1.73e-2 | 1 |

M_e2 contributes 35 of the 78 candidate units, reflecting both stronger yield
and substantially greater frozen run coverage. Excitatory neurons contribute
49 candidate units. These imbalances are why list presence must not be
interpreted as a formal between-group difference.

## Recurring drivers

RPL11 and RPS15 each occur in seven supported categories. RPLP1 occurs in
four. ATG101, LAMTOR5, PSMB6, RPL15, RPLP2, RPS13, SELENOM, SELENOW, TMEM147,
and WDR82 each occur in three.

The stability labels among the 78 main candidates are:

| Evidence label | Candidate units |
|---|---:|
| recurrent_stable | 54 |
| localized_single_fine_type | 11 |
| strict_non_mt_reference | 10 |
| single_run_evidence | 3 |

The label strict_non_mt_reference in this table is used when the strict gate
passes but the result does not meet the recurrent-stable label. The separate
Boolean strict-reference column should be used to count all strict candidates.

## Primary files

- phase20_relaxed_candidates.tsv: all 78 main candidates.
- phase20_top10.tsv: detailed lists, plus explicit empty-list rows.
- phase20_top5_summary.tsv: compact presentation lists.
- phase20_driver_aggregates.tsv.gz: all 196,174 non-MT category-gene units.
- phase20_category_manifest.tsv: all 42 structural categories.
- phase20_strict_non_mt_reference_candidates.tsv: 64 strict candidates.
- phase20_exploratory_leads.tsv: 16 exploratory-only leads.
- phase20_checks.tsv and phase20_status.tsv: validation authority.
- phase20_artifacts.tsv: output sizes and SHA-256 hashes.

Five validated figure bundles are under:

~~~text
results/figures/analysis/phase_20_sex_apoe_kda/
~~~

## Interpretation boundary

These are within-category key-driver results. A driver appearing in one
sex/APOE list and not another is not evidence that its effect differs between
those groups. A formal comparison would require a separate balanced
heterogeneity analysis.
