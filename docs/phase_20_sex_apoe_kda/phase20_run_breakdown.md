# Phase 20 Canonical Run and Candidate Breakdown

The canonical fine-cell Phase 20 v2 release uses 295 validated Phase 12
primary runs with at least three effective query genes. They map uniquely to
42 structural sex/APOE × broad-cell categories. Thirty-eight categories
contain at least one included run and four contain none.

The 295 runs comprise the 161-run ≥10 subset used by the historical Phase 18
release plus 134 validated runs with 3–9 effective query genes. The historical
Phase 18 release and its ≥10 threshold remain unchanged.

The candidate counts below are copied from the canonical
`phase20_category_manifest.tsv`. “Exploratory-only” means a unit passing the
relaxed coverage and support gates with `0.10 < category q <= 0.20`; it is not
a main candidate.

| Sex/APOE | Broad cell type | Runs | Fine types | Category status | Relaxed | Strict | Exploratory-only |
|---|---|---:|---:|---|---:|---:|---:|
| F_e2 | Astrocytes | 6 | 3 | analyzable_multi_fine_type | 4 | 3 | 2 |
| F_e2 | Excitatory neurons | 20 | 12 | analyzable_multi_fine_type | 11 | 7 | 3 |
| F_e2 | Inhibitory neurons | 13 | 10 | analyzable_multi_fine_type | 0 | 0 | 0 |
| F_e2 | Microglia | 2 | 1 | localized_single_fine_type | 0 | 0 | 0 |
| F_e2 | OPCs | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| F_e2 | Oligodendrocytes | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| F_e2 | Vasculature | 0 | 0 | not_estimable_no_included_runs | 0 | 0 | 0 |
| F_e33 | Astrocytes | 5 | 3 | analyzable_multi_fine_type | 0 | 0 | 0 |
| F_e33 | Excitatory neurons | 23 | 14 | analyzable_multi_fine_type | 6 | 5 | 0 |
| F_e33 | Inhibitory neurons | 21 | 14 | analyzable_multi_fine_type | 0 | 0 | 0 |
| F_e33 | Microglia | 0 | 0 | not_estimable_no_included_runs | 0 | 0 | 0 |
| F_e33 | OPCs | 1 | 1 | single_run_evidence | 3 | 3 | 0 |
| F_e33 | Oligodendrocytes | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| F_e33 | Vasculature | 0 | 0 | not_estimable_no_included_runs | 0 | 0 | 0 |
| F_e4 | Astrocytes | 6 | 3 | analyzable_multi_fine_type | 1 | 1 | 0 |
| F_e4 | Excitatory neurons | 17 | 13 | analyzable_multi_fine_type | 9 | 6 | 0 |
| F_e4 | Inhibitory neurons | 15 | 12 | analyzable_multi_fine_type | 1 | 1 | 2 |
| F_e4 | Microglia | 3 | 2 | analyzable_multi_fine_type | 0 | 0 | 0 |
| F_e4 | OPCs | 2 | 1 | localized_single_fine_type | 0 | 0 | 2 |
| F_e4 | Oligodendrocytes | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| F_e4 | Vasculature | 3 | 2 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e2 | Astrocytes | 6 | 3 | analyzable_multi_fine_type | 5 | 4 | 0 |
| M_e2 | Excitatory neurons | 27 | 14 | analyzable_multi_fine_type | 20 | 17 | 3 |
| M_e2 | Inhibitory neurons | 19 | 10 | analyzable_multi_fine_type | 3 | 3 | 1 |
| M_e2 | Microglia | 2 | 1 | localized_single_fine_type | 0 | 0 | 0 |
| M_e2 | OPCs | 2 | 1 | localized_single_fine_type | 5 | 3 | 2 |
| M_e2 | Oligodendrocytes | 2 | 1 | localized_single_fine_type | 1 | 0 | 0 |
| M_e2 | Vasculature | 3 | 2 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e33 | Astrocytes | 5 | 3 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e33 | Excitatory neurons | 20 | 12 | analyzable_multi_fine_type | 1 | 1 | 0 |
| M_e33 | Inhibitory neurons | 13 | 9 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e33 | Microglia | 2 | 1 | localized_single_fine_type | 2 | 2 | 0 |
| M_e33 | OPCs | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| M_e33 | Oligodendrocytes | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| M_e33 | Vasculature | 1 | 1 | single_run_evidence | 0 | 0 | 0 |
| M_e4 | Astrocytes | 6 | 3 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e4 | Excitatory neurons | 26 | 13 | analyzable_multi_fine_type | 0 | 0 | 0 |
| M_e4 | Inhibitory neurons | 11 | 9 | analyzable_multi_fine_type | 1 | 1 | 0 |
| M_e4 | Microglia | 3 | 2 | analyzable_multi_fine_type | 1 | 1 | 0 |
| M_e4 | OPCs | 2 | 1 | localized_single_fine_type | 0 | 0 | 0 |
| M_e4 | Oligodendrocytes | 2 | 1 | localized_single_fine_type | 0 | 0 | 0 |
| M_e4 | Vasculature | 0 | 0 | not_estimable_no_included_runs | 0 | 0 | 0 |

Totals:

- included runs: 295;
- category-status counts: 22 `analyzable_multi_fine_type`, 8
  `localized_single_fine_type`, 8 `single_run_evidence`, and 4
  `not_estimable_no_included_runs`;
- relaxed candidates: 74 in 16 categories;
- strict candidates: 58 in 15 categories; and
- exploratory-only leads: 15.

The authoritative machine-readable table is:

```text
results/minerva_production/20_sex_apoe_kda/phase20_category_manifest.tsv
```
