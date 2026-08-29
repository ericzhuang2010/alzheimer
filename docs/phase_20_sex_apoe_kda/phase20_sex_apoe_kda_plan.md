# Phase 20: ROSMAP Sex/APOE × Broad Cell-Type Non-MT Key-Driver Aggregation Plan

**Status:** Executed locally; validated complete

**Date:** 2026-08-28

**Analysis name:** `phase20_sex_apoe_kda_v2`

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

Only genes classified in the canonical source as `non_mt_driver` are eligible
drivers. Core mitochondrial genes (`mt_driver`) are excluded before Phase 20
aggregation, multiple-testing correction, ranking, and output generation.

## 2. Scope decision: validated Phase 12 evidence at the three-gene KDA floor

Phase 20 does **not** regenerate DEG data and does **not** rerun the stock
`call_key_drivers()` calls. The canonical v2 release reconstructs the complete
gene-by-run evidence universe from the already validated Phase 12 primary KDA
bundle at its execution minimum of three effective query genes, then performs
the sex/APOE × broad-network reaggregation.

This change distinguishes two releases that must not be conflated:

- **Canonical fine-cell Phase 20 v2:** 295 validated Phase 12 primary runs
  with effective query size ≥3. This is the source for all current Phase 20
  candidates, tables, counts, and figures.
- **Historical Phase 18:** 161 runs with effective query size ≥10. That
  release, threshold, archive, and published results remain frozen and
  unchanged. Its overlapping 161-run non-MT evidence is used only for an
  exact historical parity check.

The complete Phase 20 source preserves the validated Phase 12 query,
tested-gene background, network, self-exclusion, overlap, fold-enrichment,
raw-P, and call-specific BH-q semantics. Phase 20 then:

1. assigns each included run to one sex/APOE group and one broad network;
2. forms explicit, implicit-zero-overlap, and absent-background opportunities;
3. removes core-MT driver genes;
4. recomputes eligible and usable run counts for each non-MT gene in each
   category;
5. combines usable raw P values with ACAT;
6. recomputes BH correction among coverage-eligible non-MT genes within the
   category;
7. applies the relaxed, strict-reference, and exploratory gates; and
8. ranks candidates and recomputes stability within that category.

### Why the complete evidence source is necessary

`kda_results.tsv.gz` contains only Phase 12 returned rows. Across the 295
included runs, it contains 2,494 significant return rows: 221 runs have at
least one return and 74 have none. It does not materialize every implicit
zero-overlap or absent-background opportunity required for coverage and ACAT.

The validated Phase 20 source reconstruction therefore writes:

```text
results/minerva_production/20_sex_apoe_kda_source/
  phase20_source_candidate_tests.tsv.gz
  phase20_source_run_manifest.tsv
  phase20_source_checks.tsv
  phase20_source_status.tsv
  phase20_source_artifacts.tsv
```

The complete table contains 2,623,910 gene × run opportunities across all
295 included runs: 2,411,256 non-MT-driver rows and 212,654 core-MT-driver
rows. Test statuses are 2,202,083 implicit zero-overlap, 313,290 absent from
background, 82,502 explicit zero-overlap, and 26,035 explicit tests. Core-MT
rows are retained in the source only for provenance; none enters a Phase 20
aggregate, BH family, ranked list, candidate file, or figure.

## 3. Input authority and Phase 20 input freeze

The authoritative upstream analysis is the validated Phase 12 bundle:

```text
results/minerva_production/12_kda/
  kda_run_manifest.tsv
  kda_signature_members.tsv.gz
  kda_background_members.tsv.gz
  kda_results.tsv.gz
  kda_checks.tsv
  kda_status.tsv
  kda_artifacts.tsv
```

The source-building program also reads the frozen Phase 09 annotation and
seven network artifacts recorded by Phase 12. The historical Phase 18 archive
is read only for parity over its original ≥10-gene, 161-run non-MT subset; it
is never rewritten or substituted for the canonical ≥3 Phase 20 source.

At Phase 20 execution, the validated source files are copied byte-for-byte to:

```text
results/minerva_production/20_sex_apoe_kda/00_inputs/
  phase20_source_candidate_tests.tsv.gz
  phase20_source_run_manifest.tsv
  phase20_source_input_authority.tsv
  phase20_source_checks.tsv
```

`phase20_source_input_authority.tsv` records source and snapshot paths, source
schema and validation status, byte size, SHA-256, and copy-identity status.
The aggregation stops if source validation fails, a blocking source check
fails, a snapshot differs from its recorded source, or the configured
three-gene inclusion floor is not reproduced.

## 4. Category feasibility under the canonical Phase 20 scope

The structural source contains:

```text
54 fine cell types × 6 sex/APOE groups × 2 directions = 648 slots
```

Of these, 295 are validated and meet effective query size ≥3. The remaining
353 comprise six source-unavailable directional slots from three contrasts and
347 slots below the three-gene KDA execution minimum. The included 295 consist
of 161 runs with
effective query size ≥10 and 134 with size 3–9.

The canonical ≥3 run counts are:

| Sex/APOE group | Astrocytes | Excitatory | Inhibitory | Microglia | OPCs | Oligodendrocytes | Vasculature |
|---|---:|---:|---:|---:|---:|---:|---:|
| `F_e2` | 6 | 20 | 13 | 2 | 1 | 1 | 0 |
| `F_e33` | 5 | 23 | 21 | 0 | 1 | 1 | 0 |
| `F_e4` | 6 | 17 | 15 | 3 | 2 | 1 | 3 |
| `M_e2` | 6 | 27 | 19 | 2 | 2 | 2 | 3 |
| `M_e33` | 5 | 20 | 13 | 2 | 1 | 1 | 1 |
| `M_e4` | 6 | 26 | 11 | 3 | 2 | 2 | 0 |
| **Total** | **34** | **133** | **92** | **12** | **9** | **8** | **7** |

These counts sum to 295 and yield 38 categories with at least one run and four
`not_estimable_no_included_runs` categories. The category-status breakdown is
22 multi-fine-type, eight localized single-fine-type, eight single-run, and
four empty categories. A single-run category is not described as cross-run
consensus, and empty or unsupported lists are never backfilled.

The 161-run historical Phase 18 breakdown remains valid for that frozen
release only. Expanding canonical Phase 20 to 295 does not revise or overwrite
Phase 18.

## 5. Frozen threshold yields and final recommendation

The prespecified threshold grid was recomputed from the canonical 295-run
source after excluding core-MT drivers and rebuilding each within-category BH
family from coverage-eligible non-MT genes. The validated yields are:

| Analysis tier | Coverage | Supporting-run q | Non-MT category q | Passing non-MT candidate units | Top 5 displayed | Top 10 displayed | Categories with a non-MT candidate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict non-MT reference | 0.80 | 0.05 | 0.05 | 58 | 43 | 51 | 15 |
| Relaxed Phase 20 main | 0.50 | 0.10 | 0.10 | 74 | 48 | 63 | 16 |
| Broader exploratory, inclusive | 0.50 | 0.10 | 0.20 | 89 | 54 | 72 | 17 |

The main release therefore contains 74 non-MT gene × category candidates
across 16 of the 38 analyzable categories. The strict non-MT reference contains
58 candidates across 15 categories. The q≤0.20 exploratory-inclusive tier has
89 units, of which 15 are exploratory-only leads outside the main list.

The exact main-selection funnel is:

```text
259,548 non-MT gene × category aggregate units
  → 233,368 with coverage ≥0.50               (26,180 removed)
  → 500 with at least one relaxed supporting run (232,868 removed)
  → 74 with within-category ACAT q ≤0.10      (426 removed)
```

The individual gates behave differently:

- at category q≤0.05, lowering coverage from 0.80 to 0.50 changes the yield
  from 58 to 63 candidates while retaining 15 supported categories;
- changing the supporting-run q threshold from 0.05 to 0.10 does not change
  any candidate yield in the frozen grid, although q≤0.10 remains the declared
  relaxed support definition;
- at coverage≥0.50, raising category q from 0.05 to 0.10 changes the yield
  from 63 to 74 and adds one supported category;
- category q≤0.20 reaches 89 inclusive units and 17 categories, but remains
  exploratory rather than part of the main list;
- excluding MT drivers produces one non-MT hypothesis family and one ranked
  non-MT list per biological category.

### What each threshold means and what can be relaxed

| Threshold or rule | Historical Phase 18 value | Canonical Phase 20 value | Can it be relaxed? | Interpretation |
|---|---:|---:|---|---|
| Effective query genes per KDA run | At least 10 | At least 3 | Not below 3 | Phase 20 v2 uses validated Phase 12 runs at the KDA execution contract of ≥3. The historical Phase 18 ≥10 release remains unchanged. |
| Gene coverage across category runs | At least 0.80 | At least 0.50 | Yes | At 0.80, a gene must have usable explicit or implicit-null evidence in at least 80% of the category's runs. At 0.50, it must be usable in at least half. Coverage is test availability, not the fraction of significant runs. |
| Minimum supporting runs | At least 1 | At least 1 | No useful lower value | Zero would remove the requirement for any individually convincing KDA run. |
| Other mitochondrial query genes in a supporting neighborhood | At least 2 | At least 2 | Technically yes, to 1; not recommended | Keeping two targets avoids calling a gene a driver because of a single neighboring mitochondrial gene. |
| Supporting-run fold enrichment | Greater than 1 | Greater than 1 | No | A value at or below 1 is not enrichment. |
| Supporting-run BH q | At most 0.05 | At most 0.10 | Yes | This determines whether one individual KDA run counts as conservative support. |
| Aggregated category ACAT q | At most 0.05 | At most 0.10 | Yes; main relaxation | This is the FDR-adjusted significance of the gene after combining its evidence across runs in one sex/APOE × broad-cell category. |
| Candidate universe and BH family | Historical mixed-driver family | Non-MT genes only | Yes | Core-MT drivers are excluded before Phase 20 BH. Each sex/APOE × broad-cell category has one non-MT hypothesis family. |
| Missing-value treatment | Omit missing | Omit missing | Already the more permissive main option | Replacing missing values with P=1 is stricter and remains a sensitivity analysis. |
| Display limit | Top 5 | Top 10 plus all-candidate files | Yes | This changes how many passing candidates are shown, not which genes pass. |
| Leave-one-fine-type stability | Evidence label | Evidence label | Already non-blocking | Instability does not remove a main relaxed candidate; it changes its evidence label. |

### Selected relaxed Phase 20 rule

The frozen main Phase 20 key-driver candidate rule is:

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
figure states that it uses 50% coverage and 10% FDR. The minimum effective
query size is separately fixed at three; it is not one of these downstream
candidate relaxations.

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

For a candidate unit, the eligible denominator is every one of the 295
canonical Phase 20 runs whose `signature_group` and `broad_network` match that
unit. The candidate must have `case_id == non_mt_driver`; `mt_driver` genes are
removed before candidate units are formed.
Both `AD_up_mito` and `AD_down_mito` runs remain in the main aggregation,
as in the historical implementation.

The seven broad networks are never combined. The six sex/APOE groups are never
combined in the Phase 20 main analysis.

### 6.2 Per-run evidence

Phase 20 consumes the following values from the validated complete Phase 20
source reconstructed from Phase 12:

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
- derive `relaxed_support` using overlap≥2, fold enrichment>1, and validated
  run q≤0.10;
- do not filter to significant Phase 12 returns before aggregation.

### 6.3 Coverage and ACAT

For each candidate unit:

```text
coverage_fraction = usable_run_count / eligible_run_count
```

Use the relaxed Phase 20 coverage requirement:

```text
coverage_fraction >= 0.50
```

Combine usable validated `final_raw_p` values with the same equal-weight ACAT
implementation used by Phase 18. The main missing-value action is `omit`.
Also calculate the `missing_as_one` sensitivity and the strict
coverage≥0.80 reference flag.

### 6.4 Multiple-testing correction

For the relaxed Phase 20 main analysis, apply BH to the non-MT genes passing
coverage≥0.50 within each:

```text
signature_group + broad_network
```

This produces `relaxed_category_acat_q`. No MT gene is present in the BH
family.

For the strict non-MT reference, rebuild BH among the non-MT genes passing
coverage≥0.80 within the same category key:

```text
signature_group + broad_network
```

This produces `strict_category_acat_q`. Thus the relaxed and strict q values
use the same biological category but different coverage-eligible hypothesis
families; the support gate is applied after those q values are calculated.

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
| `not_estimable_no_included_runs` | The category has no canonical Phase 20 run meeting the ≥3 effective-query rule. |

These are drivers identified *within* a sex/APOE category. A gene appearing in
one group's list but not another group's list is not, by itself, evidence of a
statistical difference between groups. Run counts and fine-cell-type coverage
are highly unequal. The report will therefore avoid “group-specific” claims
unless a separate balanced or formal heterogeneity analysis supports them.

## 8. New files and directories

Phase 20 does not overwrite Phase 12, the historical Phase 18 release, or any
earlier result.

### 8.1 Configuration

```text
config/phase20_sex_apoe_kda.yml
```

The config freezes:

- the six group IDs and their sex/APOE labels;
- the seven broad networks and display order;
- the two directions;
- the `non_mt_driver` eligibility rule and explicit exclusion of `mt_driver`;
- coverage, support, ACAT, BH, tier, stability, and top-five/top-ten display
  thresholds;
- Phase 12, Phase 20 source, and historical Phase 18 parity paths plus expected
  counts;
- the Phase 20 machine-result and figure roots.

### 8.2 Analysis code

```text
scripts/20_sex_apoe_kda.py
```

`scripts/20_prepare_sex_apoe_kda_source.py` reconstructs and validates the
complete ≥3 source from the Phase 12 bundle. `scripts/20_sex_apoe_kda.py`
snapshots that source and performs non-MT filtering, category aggregation,
stability/sensitivity calculations, validation, and output writing.

Figure code is stored under:

```text
scripts/figures/analysis/phase_20_sex_apoe_kda/render_phase20_summary_figures.py
```

### 8.3 Tests

```text
tests/test_phase20_sex_apoe_kda.py
```

### 8.4 Machine-readable results

All Phase 20 analysis results are stored under:

```text
results/minerva_production/20_sex_apoe_kda/
```

Validated structure:

```text
results/minerva_production/20_sex_apoe_kda/
├── 00_inputs/
│   ├── phase20_source_candidate_tests.tsv.gz
│   ├── phase20_source_run_manifest.tsv
│   ├── phase20_source_input_authority.tsv
│   └── phase20_source_checks.tsv
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
  prespecified coverage, supporting-run-q, and category-q combination;
- stability and sensitivity files: all recalculated alternatives, including
  the study-wide BH sensitivity analysis;
- checks, artifacts, status, and config snapshot: reproducibility and release
  gates.

### 8.5 Figures

Final figure files and their plot-data/check manifests are stored under:

```text
results/figures/analysis/phase_20_sex_apoe_kda/
```

Figure products:

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

For current counts, the machine-readable status, checks, category manifest,
threshold grid, and filter funnel in the canonical result directory are the
release authority. `phase20_results_explained.md` and
`phase20_run_breakdown.md` summarize those v2 tables.

## 9. Validation and acceptance criteria

### 9.1 Input checks

- Phase 12 source status is `validated_complete` and its blocking checks pass.
- The reconstructed Phase 20 source status is `validated_complete` with zero
  blocking failures.
- The input snapshot is byte-identical to its source.
- The structural source manifest contains 648 slots, exactly 295 included runs,
  and a minimum included effective query size of three.
- The complete evidence snapshot contains 2,623,910 gene × run rows.
- All six sex/APOE groups and all seven broad networks are represented in the
  structural category manifest.
- Every included run maps to exactly one of the 42 categories.

### 9.2 Historical Phase 18 parity guard

The source reconstruction leaves the historical Phase 18 release unchanged
and compares the overlapping ≥10-gene subset against its frozen non-MT evidence
universe. The validated guard reports:

- 161 historical Phase 18 runs;
- 1,343,593 historical non-MT evidence rows matched;
- zero parity mismatches; and
- no writes to the Phase 18 archive or published release.

This parity guard applies only to the historical overlap. The additional 134
Phase 20 runs with 3–9 effective query genes are validated against Phase 12 and
are not retroactively added to Phase 18.

### 9.3 Phase 20 output checks

- `phase20_category_manifest.tsv` has exactly 42 unique categories.
- The category run counts sum to 295.
- Exactly 38 categories are analyzable and four are marked not estimable under
  the canonical ≥3 scope.
- `phase20_driver_aggregates.tsv.gz` contains 259,548 unique non-MT units.
- The strict non-MT reference reproduces 58 candidate units, 43 top-five
  units, 51 top-ten units, and candidates in 15 categories.
- The selected relaxed non-MT Phase 20 threshold reproduces 74 candidate
  units, 48 top-five units, 63 top-ten units, and candidates in 16 categories.
- The exploratory-inclusive non-MT q≤0.20 tier reproduces 89 units, 54
  top-five units, 72 top-ten units, and candidates in 17 categories; exactly
  15 units are exploratory-only.
- Every candidate, aggregate, and rank row has
  `case_id == non_mt_driver` and `is_core_mito == FALSE`; every figure bundle
  declares and validates non-MT scope, while only plot-data schemas that carry
  row-level gene evidence include those two fields.
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

The release status is `validated_complete`; all blocking checks and the
historical Phase 18 parity guard passed.

## 10. Execution order

1. Freeze the v2 config with the three-gene source floor and expected counts.
2. Reconstruct complete evidence for the 295 eligible Phase 12 runs.
3. Validate Phase 12 provenance and exact historical Phase 18 overlap parity.
4. Snapshot and checksum the complete Phase 20 source into `00_inputs/`.
5. Run the 42-category relaxed main, strict-reference, and exploratory
   aggregation.
6. Run stability, sensitivity, threshold-grid, and direction summaries.
7. Write checks, artifact manifest, config snapshot, and release status.
8. Generate figures and synchronize the result documentation.

## 11. Final interpretation boundary

Phase 20 answers:

> Which non-MT drivers from the validated Phase 12 ≥3 KDA evidence have
> aggregated evidence within each
> ROSMAP sex/APOE group and broad cell type?

It will not, by itself, prove that a driver differs significantly between two
sex/APOE groups. That stronger claim would require an additional balanced
heterogeneity analysis and should be planned separately if needed.
