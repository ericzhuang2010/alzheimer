# Phase 20: ROSMAP Sex/APOE × Broad Cell-Type Non-MT Key-Driver Aggregation Plan

**Status:** Executed locally; validated complete  
**Date:** 2026-08-27  
**Analysis name:** `phase20_sex_apoe_kda`  
**Cohort:** ROSMAP  

## 1. Objective

Identify non-MT key drivers separately for each of the 42 ROSMAP categories
defined by:

```text
6 sex/APOE groups × 7 broad cell types
```

The six sex/APOE groups are:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

The seven broad cell types/Bayesian networks are:

```text
Astrocytes
Excitatory_neurons
Inhibitory_neurons
Microglia
OPCs
Oligodendrocytes
Vasculature_cells
```

Phase 18 aggregated a gene across all included runs in the same broad cell
type, regardless of sex/APOE group. Phase 20 will retain the sex/APOE group in
the aggregation key.

The Phase 18 aggregation key was:

```text
broad_network + gene + driver_class
```

The Phase 20 aggregation key will be:

```text
signature_group + broad_network + non_mt_gene
```

Only genes classified by frozen Phase 18 as `case3_not_core_mito` are eligible
drivers. Core mitochondrial genes are excluded before Phase 20 aggregation,
multiple-testing correction, ranking, and output generation.

## 2. Scope decision: this is a reaggregation, not a new DEG or KDA analysis

Phase 20 will **not** regenerate DEG data and will **not** rerun KDA. Phase 12
is deprecated and will not be an input to the Phase 20 program.

The following Phase 18 quantities remain frozen and unchanged:

- the 161 included KDA runs and the minimum effective query size of 10 genes;
- the mitochondrial queries, tested-gene backgrounds, and Bayesian networks;
- the three directed network layers tested for each candidate;
- run-level hypergeometric P values and within-run BH-adjusted values;
- explicit tests, implicit zero-overlap tests, and absent-background status;
- the run-level overlap, fold-enrichment, raw-P, and within-run-q statistics
  needed to derive both strict and relaxed support flags;
- the frozen distinction between core-MT and non-MT candidate genes, used to
  exclude all core-MT drivers.

Only the final cross-run operations change:

1. select the Phase 18 run-level evidence belonging to one sex/APOE group and
   one broad network;
2. recompute the gene's eligible and usable run counts in that category;
3. recompute coverage and ACAT in that category;
4. recompute BH correction among non-MT genes within that category;
5. apply the relaxed Phase 20 coverage, support, and q gates;
6. rank one non-MT list within each sex/APOE group × broad network; and
7. recompute stability within the same category.

### Why Phase 20 must use the complete Phase 18 evidence table

The public Phase 18 file
`results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv`
contains 95,557 explicitly tested gene × run rows. It does not materialize the
implicit zero-overlap and absent-background opportunities as separate rows.
Those rows are necessary for category-specific coverage and ACAT.

Phase 18 already produced a validated complete opportunity table:

```text
results/minerva_production/18_key_driver_selection/archive/
  key_driver_candidate_tests.tsv.gz
```

It contains 1,463,150 data rows across all 161 included runs and records:

- `signature_group`;
- `broad_network` and `fine_cell_type`;
- `signature_direction`;
- gene and driver-class information;
- explicit, implicit-null, or absent-background test status;
- final raw P and run-level q values;
- conservative-support fields.

This complete frozen Phase 18 table makes Phase 20 a true last-step
reaggregation. The current explicit-only Phase 18 table will be used for
parity checks and presentation provenance, but not as the sole aggregation
input.

## 3. Input authority and Phase 20 input freeze

Phase 20 will read only frozen Phase 18 artifacts. At the beginning of the
Phase 20 execution, the required Phase 18 files will be copied byte-for-byte
into a Phase 20 input snapshot so that Phase 20 does not depend on a mutable or
archived location.

### Authoritative Phase 18 sources

```text
results/minerva_production/18_key_driver_selection/archive/
  key_driver_candidate_tests.tsv.gz
  key_driver_run_manifest.tsv
  key_driver_checks.tsv
  key_driver_status.tsv
  key_driver_artifacts.tsv

results/minerva_production/18_key_driver_selection/
  call_key_driver_returns.tsv
```

The complete opportunity table comes from the validated three-case Phase 18
archive. Phase 20 will apply this eligibility rule:

```text
case1_core_mito_in_query      -> exclude
case2_core_mito_not_in_query  -> exclude
case3_not_core_mito           -> retain as an eligible non-MT driver
```

No run-level P value, q value, or self-exclusion result will be recalculated
during this mapping. The original Phase 18 conservative-support Boolean will
be preserved as the strict reference. A separate relaxed-support Boolean will
be derived from the same frozen run statistics using run q≤0.10.

The frozen input snapshot may contain the excluded MT rows for byte-identical
provenance, but no MT row may enter a Phase 20 aggregate, BH family, ranked
list, candidate file, or figure.

### Frozen Phase 20 input location

```text
results/minerva_production/20_sex_apoe_kda/00_inputs/
  phase18_candidate_tests.tsv.gz
  phase18_run_manifest.tsv
  phase18_input_authority.tsv
  phase18_source_checks.tsv
```

`phase18_input_authority.tsv` will record, for every copied file:

```text
source_path
snapshot_path
source_schema_version
source_validation_status
byte_size
sha256
copy_identity_pass
```

The program must stop before analysis if the Phase 18 source status is not
`validated_complete`, any blocking source check failed, or a snapshot checksum
does not match its source.

## 4. Category feasibility under the frozen Phase 18 scope

All 42 structural categories will be retained in the Phase 20 category
manifest, including categories with no included runs.

The Phase 18 ≥10-gene run counts are:

| Sex/APOE group | Astrocytes | Excitatory | Inhibitory | Microglia | OPCs | Oligodendrocytes | Vasculature |
|---|---:|---:|---:|---:|---:|---:|---:|
| `F_e2` | 2 | 14 | 3 | 1 | 1 | 0 | 0 |
| `F_e33` | 2 | 15 | 2 | 0 | 1 | 0 | 0 |
| `F_e4` | 5 | 13 | 5 | 0 | 2 | 0 | 0 |
| `M_e2` | 5 | 25 | 14 | 2 | 2 | 2 | 1 |
| `M_e33` | 2 | 13 | 2 | 0 | 0 | 0 | 0 |
| `M_e4` | 5 | 17 | 2 | 3 | 0 | 0 | 0 |
| **Total** | **21** | **97** | **28** | **6** | **6** | **2** | **1** |

These counts sum to the 161 frozen Phase 18 runs. They imply:

- 27 categories have at least one included run;
- 15 categories have no included runs;
- categories with no runs will be labeled `not_estimable_no_included_runs`;
- a category with one run can produce only `single_run_evidence`, not a
  cross-run consensus claim;
- a category whose runs come from one fine cell type will be labeled
  `localized_single_fine_type` even if it passes the statistical candidate
  gates.

No failed or empty list will be filled with lower-ranked nonsignificant genes.

## 5. Preliminary threshold-yield audit and revised recommendation

Before fixing the Phase 20 thresholds, the complete frozen Phase 18 evidence
table was reaggregated by sex/APOE group × broad network under a prespecified
threshold grid. The calculation first passed the decisive parity check: when
`signature_group` was removed from the grouping key, it reproduced the current
Phase 18 totals of 78 passing candidate units and 47 displayed top-five units.

The mixed-driver parser first reproduced the Phase 18 totals of 78 passing
candidate units and 47 displayed units as an implementation parity check.
Phase 20 selection was then recalculated after removing every core-MT driver
and rebuilding BH families from non-MT genes only.

The resulting non-MT-only projections are:

| Analysis tier | Coverage | Supporting-run q | Non-MT category q | Passing non-MT candidate units | Top 5 displayed | Top 10 displayed | Categories with a non-MT candidate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict non-MT reference | 0.80 | 0.05 | 0.05 | 64 | 45 | 56 | 14 |
| Relaxed Phase 20 main | 0.50 | 0.10 | 0.10 | 78 | 50 | 65 | 15 |
| Broader exploratory | 0.50 | 0.10 | 0.20 | 94 | 53 | 75 | 17 |

The relaxed Phase 20 main analysis is therefore projected to return 78 non-MT
gene × category candidates across 15 of the 27 analyzable categories. The
strict non-MT reference remains available for comparison and is projected to
return 64 candidates across 14 categories.

The individual gates behave differently:

- lowering coverage from 0.80 to 0.50 adds only four candidate units and
  can make BH slightly harsher when used alone, but it is appropriate for the
  requested relaxed analysis and helps retain genes testable in only half of a
  sparse category's runs;
- relaxing the supporting-run q threshold from 0.05 to 0.10 adds little by
  itself, but makes the run-support definition consistent with the requested
  discovery-oriented analysis;
- raising category q from 0.05 to 0.10 is the most important direct threshold
  relaxation;
- category q≤0.20 reaches 17 non-MT categories, but that threshold is too permissive
  to use without an exploratory label;
- excluding MT drivers produces one non-MT hypothesis family and one ranked
  non-MT list per biological category.

### What each threshold means and what can be relaxed

| Threshold or rule | Phase 18 value | Relaxed Phase 20 value | Can it be relaxed? | Interpretation |
|---|---:|---:|---|---|
| Effective query genes per KDA run | At least 10 | Unchanged | Not within Phase 20 | Phase 20 uses frozen Phase 18 runs. Lowering this would require additional upstream KDA evidence, not just reaggregation. |
| Gene coverage across category runs | At least 0.80 | At least 0.50 | Yes | At 0.80, a gene must have usable explicit or implicit-null evidence in at least 80% of the category's runs. At 0.50, it must be usable in at least half. Coverage is test availability, not the fraction of significant runs. |
| Minimum supporting runs | At least 1 | At least 1 | No useful lower value | Zero would remove the requirement for any individually convincing KDA run. |
| Other mitochondrial query genes in a supporting neighborhood | At least 2 | At least 2 | Technically yes, to 1; not recommended | Keeping two targets avoids calling a gene a driver because of a single neighboring mitochondrial gene. |
| Supporting-run fold enrichment | Greater than 1 | Greater than 1 | No | A value at or below 1 is not enrichment. |
| Supporting-run BH q | At most 0.05 | At most 0.10 | Yes | This determines whether one individual KDA run counts as conservative support. |
| Aggregated category ACAT q | At most 0.05 | At most 0.10 | Yes; main relaxation | This is the FDR-adjusted significance of the gene after combining its evidence across runs in one sex/APOE × broad-cell category. |
| Candidate universe and BH family | MT and non-MT combined | Non-MT genes only | Yes | Core-MT drivers are excluded before BH. Each sex/APOE × broad-cell category has one non-MT hypothesis family. |
| Missing-value treatment | Omit missing | Omit missing | Already the more permissive main option | Replacing missing values with P=1 is stricter and remains a sensitivity analysis. |
| Display limit | Top 5 | Top 10 plus all-candidate files | Yes | This changes how many passing candidates are shown, not which genes pass. |
| Leave-one-fine-type stability | Evidence label | Evidence label | Already non-blocking | Instability does not remove a main relaxed candidate; it changes its evidence label. |

### Selected relaxed Phase 20 rule

The main Phase 20 key-driver candidate rule will be:

```text
coverage_fraction >= 0.50

at least one supporting run with:
    other_query_overlap >= 2
    final_fold_enrichment > 1
    final_run_q <= 0.10

category_acat_q <= 0.10
BH calculated among non-MT genes within:
    signature_group + broad_network
```

This is a relaxed, discovery-oriented key-driver definition. Every output and
figure will say that it uses 50% coverage and 10% FDR so it cannot be confused
with the stricter Phase 18 definition.

### Strict reference and broader exploratory flags

- `strict_non_mt_reference`: non-MT genes only, coverage≥0.80, original
  supporting-run q≤0.05, and non-MT category q≤0.05.
- `relaxed_phase20_candidate`: passes the selected main rule above.
- `exploratory_q20`: passes the relaxed coverage and run-support gates with
  0.10<relaxed category q≤0.20. It is not called a main key driver.

### Display limits

- store every passing relaxed Phase 20 candidate;
- use up to 10 non-MT candidates per category in the detailed Phase 20 tables
  and supplemental figures;
- retain a compact top-five table only for summary figures or slides.

The plan deliberately does not relax the two-target minimum, fold enrichment,
or minimum support count. Relaxing those would change the biological meaning
of “driver” more than it would address multiple-testing power.

## 6. Statistical analysis

### 6.1 Candidate unit and denominator

One Phase 20 candidate unit is:

```text
signature_group + broad_network + current_symbol
```

For a candidate unit, the eligible denominator is every one of the 161 frozen
Phase 18 runs whose `signature_group` and `broad_network` match that unit.
The candidate must be `case3_not_core_mito`; case 1 and case 2 genes are
removed before candidate units are formed.
Both `AD_up_mito` and `AD_down_mito` runs remain in the main aggregation,
as in Phase 18.

The seven broad networks are never combined. The six sex/APOE groups are never
combined in the Phase 20 main analysis.

### 6.2 Per-run evidence

Phase 20 will consume the following frozen values from the complete Phase 18
table:

```text
test_status
usable_test
final_raw_p
final_run_q
other_query_overlap
final_fold_enrichment
conservative_support
```

Their interpretation remains:

- explicit test: use its frozen `final_raw_p`;
- implicit zero-overlap test: use `P = 1`;
- absent from background: treat as missing;
- preserve `conservative_support` as the strict run-q≤0.05 flag;
- derive `relaxed_support` using overlap≥2, fold enrichment>1, and frozen
  run q≤0.10;
- do not filter to significant Phase 18 returns before aggregation.

### 6.3 Coverage and ACAT

For each candidate unit:

```text
coverage_fraction = usable_run_count / eligible_run_count
```

Use the relaxed Phase 20 coverage requirement:

```text
coverage_fraction >= 0.50
```

Combine usable frozen `final_raw_p` values with the same equal-weight ACAT
implementation used by Phase 18. The main missing-value action is `omit`.
Also calculate the Phase 18 `missing_as_one` sensitivity and the strict
coverage≥0.80 reference flag.

### 6.4 Multiple-testing correction

For the relaxed Phase 20 main analysis, apply BH to non-MT genes within each:

```text
signature_group + broad_network
```

This produces `relaxed_category_acat_q`. No MT gene is present in the BH
family.

For the strict non-MT reference, apply the stricter coverage, support, and
q thresholds to the same non-MT-only BH family:

```text
signature_group + broad_network
```

This produces `strict_category_acat_q`.

Also calculate a secondary `studywide_acat_q` across all assessable
non-MT gene × sex/APOE group × broad-network candidate units. The relaxed
non-MT category q is the main Phase 20 selection value; the strict non-MT q is
the reference; and the study-wide q is a robustness and prioritization field.

### 6.5 Candidate tiers

A gene is a main relaxed Phase 20 candidate when:

```text
coverage_fraction >= 0.50
relaxed_support_count >= 1
relaxed_category_acat_q <= 0.10
```

Also record whether it passes the stricter non-MT reference rule:

```text
coverage_fraction >= 0.80
conservative_support_count >= 1
strict_category_acat_q <= 0.05
```

A gene passing the relaxed coverage and support gates with
`0.10 < relaxed_category_acat_q <= 0.20` is an exploratory lead, not a main
Phase 20 key-driver candidate.

### 6.6 Ranking and detailed display

Rank passing candidates separately within:

```text
signature_group + broad_network
```

Sort by:

1. smaller `relaxed_category_acat_q`;
2. smaller `category_acat_p`; and
3. `current_symbol` alphabetically as the deterministic tie-breaker.

Retain up to ten relaxed non-MT candidates per category in the detailed Phase
20 output. Also create a compact top-five summary for figures and slides.
Phase 20 therefore contains exactly 42 structural category lists, including
lists marked not estimable or not supported. Rank by relaxed category q,
category ACAT P, and then gene symbol. The strict-reference flag remains
attached to each relaxed candidate.

## 7. Stability, sensitivity, and interpretation

### 7.1 Leave-one-fine-cell-type-out stability

For each passing candidate in a category with at least two included fine cell
types:

1. omit all runs from one fine cell type;
2. recompute coverage, ACAT, the complete category BH family, candidate
   status, and rank;
3. repeat for every fine cell type in the category; and
4. report nominal-P, category-q, candidate-retention, and worst-rank
   fractions.

Stability is not assessable when the category contains only one fine cell
type.

### 7.2 Prespecified sensitivities

Run the following without changing the main relaxed list:

- missing values replaced by `P = 1`;
- coverage thresholds 0.50, 0.80, and 1.00;
- `AD_up_mito` and `AD_down_mito` aggregated separately;
- category-level versus study-wide BH;
- Phase 18 degree-matched network null for displayed candidates, when the
  matching pool is sufficiently large.

### 7.3 Evidence labels

Use the following labels in tables and figures:

| Label | Definition |
|---|---|
| `recurrent_stable` | Relaxed Phase 20 gate passes, support spans at least two fine cell types, and leave-one-fine-type-out nominal pass fraction is at least 0.80. |
| `relaxed_phase20_candidate` | The non-MT-only 50%-coverage, relaxed-run-support, q≤0.10 main gate passes. |
| `strict_non_mt_reference` | The non-MT candidate also passes 80% coverage, strict run support, and non-MT category q≤0.05. |
| `exploratory_q20` | Relaxed coverage and support pass with 0.10 < relaxed category q ≤0.20; not called a main key driver. |
| `localized_single_fine_type` | Candidate gate passes but all included evidence comes from one fine cell type. |
| `single_run_evidence` | The category has one included run; the result is not described as aggregated consensus. |
| `not_supported` | Category is analyzable but the gene does not pass the candidate gate. |
| `not_estimable_no_included_runs` | The category has no frozen Phase 18 run. |

These are drivers identified *within* a sex/APOE category. A gene appearing in
one group's list but not another group's list is not, by itself, evidence of a
statistical difference between groups. Run counts and fine-cell-type coverage
are highly unequal. The report will therefore avoid “group-specific” claims
unless a separate balanced or formal heterogeneity analysis supports them.

## 8. New files and directories

Phase 20 will not overwrite Phase 18 or any earlier result.

### 8.1 Configuration

```text
config/phase20_sex_apoe_kda.yml
```

The config will freeze:

- the six group IDs and their sex/APOE labels;
- the seven broad networks and display order;
- the two directions;
- the case-3-only non-MT eligibility rule and explicit exclusion of cases 1
  and 2;
- coverage, support, ACAT, BH, tier, stability, and top-five/top-ten display
  thresholds;
- all Phase 18 input paths and expected checksums/counts;
- the Phase 20 machine-result and figure roots.

### 8.2 Analysis code

```text
scripts/20_sex_apoe_kda.py
```

This will be the single Phase 20 analysis entry point. It will read the frozen
Phase 18 opportunity table and perform only case mapping, category
aggregation, stability/sensitivity calculations, validation, and output
writing.

Figure code will be stored under:

```text
scripts/figures/analysis/phase_20_sex_apoe_kda/
```

### 8.3 Tests

```text
tests/test_phase20_sex_apoe_kda.py
```

If an R figure or table renderer is added, its output-contract test will be:

```text
tests/test_phase20_sex_apoe_kda.R
```

### 8.4 Machine-readable results

All Phase 20 analysis results will be stored under:

```text
results/minerva_production/20_sex_apoe_kda/
```

Planned structure:

```text
results/minerva_production/20_sex_apoe_kda/
├── 00_inputs/
│   ├── phase18_candidate_tests.tsv.gz
│   ├── phase18_run_manifest.tsv
│   ├── phase18_input_authority.tsv
│   └── phase18_source_checks.tsv
├── phase20_category_manifest.tsv
├── phase20_driver_aggregates.tsv.gz
├── phase20_relaxed_candidates.tsv
├── phase20_strict_non_mt_reference_candidates.tsv
├── phase20_exploratory_leads.tsv
├── phase20_top10.tsv
├── phase20_top5_summary.tsv
├── phase20_conservative_support.tsv.gz
├── phase20_stability_replicates.tsv.gz
├── phase20_stability_summary.tsv
├── phase20_sensitivity_results.tsv.gz
├── phase20_direction_summary.tsv.gz
├── phase20_threshold_grid.tsv
├── phase20_filter_funnel.tsv
├── phase20_checks.tsv
├── phase20_artifacts.tsv
├── phase20_status.tsv
└── phase20_config_snapshot.yml
```

File roles:

- `phase20_category_manifest.tsv`: exactly 42 rows, including empty and
  single-run categories;
- `phase20_driver_aggregates.tsv.gz`: one row per Phase 20 candidate unit;
- `phase20_relaxed_candidates.tsv`: every candidate passing the selected
  relaxed Phase 20 main gate;
- `phase20_strict_non_mt_reference_candidates.tsv`: the stricter non-MT-only
  subset retained for comparability;
- `phase20_exploratory_leads.tsv`: relaxed-support genes with
  0.10<relaxed category q≤0.20;
- `phase20_top10.tsv`: detailed ranked display, with at most ten relaxed
  non-MT candidates per category;
- `phase20_top5_summary.tsv`: compact presentation-only subset;
- `phase20_conservative_support.tsv.gz`: supporting run rows for passing
  candidates, retaining fine cell type, group, and direction;
- `phase20_threshold_grid.tsv`: candidate and category yields for every
  prespecified coverage, q, support, and BH-family combination;
- stability and sensitivity files: all recalculated alternative results;
- checks, artifacts, status, and config snapshot: reproducibility and release
  gates.

### 8.5 Figures

Final figure files and their plot-data/check manifests will be stored under:

```text
results/figures/analysis/phase_20_sex_apoe_kda/
```

Planned figure products:

1. a 6 × 7 category-coverage heatmap showing run and fine-cell-type counts;
2. a driver-by-category evidence heatmap using category q, recurrence, and
   evidence label;
3. compact top-five plus detailed top-ten non-MT relaxed-candidate panels for
   the 42 categories, with strict-reference candidates visibly marked;
4. recurrence plots showing which drivers recur across groups within a broad
   network; and
5. stability/sensitivity summaries for the displayed drivers.

Each final figure directory will include PNG, SVG, PDF, plot-data TSV,
caption, methods, checks, status, and artifact manifest where applicable.

### 8.6 Documentation

All Phase 20 documentation will remain under the user-created directory:

```text
docs/phase_20_sex_apoe_kda/
```

The final documentation set is:

```text
docs/phase_20_sex_apoe_kda/
  phase20_sex_apoe_kda_plan.md
  phase20_methods.md
  phase20_funnel_explained.md
  phase20_results_explained.md
  phase20_run_breakdown.md
```

The relaxed-threshold explanation and final methods are consolidated in
`phase20_methods.md` so that the analysis definitions, threshold rationale,
validated yields, and interpretation boundaries have one authority.

## 9. Validation and acceptance criteria

### 9.1 Input checks

- Phase 18 source status is `validated_complete`.
- All Phase 18 blocking checks pass.
- The input snapshot is byte-identical to its source.
- The complete evidence snapshot contains 1,463,150 data rows and 161 runs.
- All six sex/APOE groups and all seven broad networks are represented in the
  structural category manifest.
- Every frozen run maps to exactly one of the 42 categories.

### 9.2 Phase 18 parity test

Before accepting group-stratified results, run a validation-only Phase 18
parity harness with `signature_group` omitted from the grouping key. It must
reproduce the current Phase 18 broad-network results, including:

- eligible, usable, explicit, implicit, and missing run counts;
- coverage fractions;
- conservative-support counts;
- aggregate ACAT P and q values within numerical tolerance;
- candidate status;
- class-specific ranks and top-five flags.

This is the decisive proof that Phase 20 changes only the last aggregation
step. The parity harness may inspect MT rows in memory, but it writes no Phase
20 MT candidate or figure output. The Phase 20 production analysis begins only
after filtering to `case3_not_core_mito`.

### 9.3 Phase 20 output checks

- `phase20_category_manifest.tsv` has exactly 42 unique categories.
- The category run counts sum to 161.
- Exactly 27 categories are analyzable and 15 are marked not estimable under
  the frozen Phase 18 scope.
- The strict non-MT reference reproduces 64 candidate units, 45 top-five
  units, 56 top-ten units, and candidates in 14 categories.
- The selected relaxed non-MT Phase 20 threshold reproduces 78 candidate
  units, 50 top-five units, 65 top-ten units, and candidates in 15 categories.
- The exploratory non-MT q≤0.20 tier reproduces 94 units, 53 top-five units,
  75 top-ten units, and candidates in 17 categories.
- Every candidate, aggregate, rank, and figure row has
  `case_id == case3_not_core_mito` and `is_core_mito == FALSE`.
- No run contributes to a category with a different `signature_group` or
  `broad_network`.
- Every candidate unit is unique.
- Aggregate values are constant within their candidate unit.
- Each relaxed and strict-reference BH family contains all and only the
  assessable non-MT genes from one category.
- Candidate ranks are unique within each sex/APOE group × broad-network
  category.
- No detailed displayed list contains more than ten genes, and no compact
  summary list contains more than five genes.
- Empty and failed lists are not backfilled.
- Repeated execution produces byte-identical tabular outputs.

The release status will be `validated_complete` only after every blocking
check and the Phase 18 parity test pass.

## 10. Execution order

1. Add and freeze `config/phase20_sex_apoe_kda.yml`.
2. Snapshot and checksum the complete validated Phase 18 evidence into
   `results/minerva_production/20_sex_apoe_kda/00_inputs/`.
3. Implement the pure category reaggregation in
   `scripts/20_sex_apoe_kda.py`.
4. Pass the broad-network-only Phase 18 parity test.
5. Reproduce and save the prespecified threshold-yield grid.
6. Run the 42-category relaxed main, strict-reference, and exploratory
   aggregation.
7. Run stability and sensitivity analyses.
8. Write checks, artifact manifest, config snapshot, and release status.
9. Generate the Phase 20 figures and their figure-level checks.
10. Write the results explanation, run breakdown, and final methods document in
   `docs/phase_20_sex_apoe_kda/`.

## 11. Final interpretation boundary

Phase 20 will answer:

> Which frozen Phase 18 KDA drivers have aggregated evidence within each
> ROSMAP sex/APOE group and broad cell type?

It will not, by itself, prove that a driver differs significantly between two
sex/APOE groups. That stronger claim would require an additional balanced
heterogeneity analysis and should be planned separately if needed.
