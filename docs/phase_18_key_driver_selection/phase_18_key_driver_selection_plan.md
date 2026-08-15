# Phase 18: Data-Driven Selection of Phase 12 Mitochondrial Key-Driver Candidates

## Status and phase boundary

This document defines the scientific, implementation, execution, output, and
completion plan for Phase 18.

Plan status: **the frozen primary design was executed against the complete
validated Phase 12 inputs. After all Phase 18 checks passed, the user
explicitly authorized promotion on 2026-08-14. The official bundle is
<code>validated_complete</code>. It was computed locally, so its execution
stage is truthfully labeled <code>local_production_equivalent</code>; it does
not claim execution on Minerva hardware**.

Phase 18 is intentionally numbered after the currently documented Phase 15
work. Phase numbers 16 and 17 are treated as reserved and must not be reused,
even if earlier work assigned to them is no longer active.

Phase 18 asks:

> Which genes have statistically supported and sufficiently complete
> Phase 12 network evidence connecting them to AD-associated mitochondrial
> expression, after separating mitochondrial query membership from
> query-independent evidence?

Phase 18 is a reanalysis and selection phase. It does not rerun differential
expression, infer new Bayesian networks, or modify the validated Phase 12
bundle. It reads immutable Phase 12 and Phase 09 artifacts, reconstructs the
complete gene-by-run KDA evidence, applies a frozen three-case classification,
filters candidate drivers, and creates independent ranked lists within each
case.

The companion rationale is:

[Unified key-driver selection proposal](unified_key_driver_selection_proposal.md)

This implementation plan is authoritative if the companion proposal and this
plan differ. In particular, this plan freezes ranking by gene-level ACAT q
value within each case; breadth, recurrence, stability, and fold enrichment
are reported as annotations and evidence tiers rather than used ahead of the
q value in the rank.

### Short name

- Phase 18: **Key-driver selection**
- Machine task mode: <code>key_driver_selection</code>
- Stable task ID: <code>global:key_driver_selection</code>

### Output roots

~~~text
results/minerva_production/18_key_driver_selection/
~~~

This is the single official Phase 18 result root. The complete real-data run
was first validated in a local staging root and then moved here after explicit
user authorization. Promotion changed only path and provenance metadata; it
did not recompute or selectively replace scientific results.

## What Phase 18 will and will not do

### Phase 18 will

1. require a complete and independently validated Phase 12 production bundle;
2. verify the frozen Phase 12 configuration, fKDA source, network files,
   Phase 09 annotation, and all required artifact hashes;
3. retain only the six primary sex/APOE groups and the separate AD-up and
   AD-down mitochondrial queries;
4. preserve all 648 primary directional run slots in a Phase 18 run manifest,
   including explicit exclusion reasons;
5. use only validated runs with at least 10 effective query genes for primary
   driver selection;
6. begin from every gene present in at least one included run background,
   without a curated-gene gate;
7. assign every usable gene × run result to exactly one of three cases;
8. remove the guaranteed driver self-overlap from Case 1 and recompute its
   enrichment statistics;
9. reconstruct null and non-significant results so ACAT does not combine only
   favorable Phase 12 rows;
10. distinguish valid null tests with P = 1 from untestable results stored as
    missing;
11. apply run-level and aggregate-level Benjamini-Hochberg correction in
    prespecified families;
12. require coverage, conservative run support, and significant aggregate
    evidence before calling a driver candidate;
13. rank candidates independently within each broad network and each of the
    three cases;
14. display at most five passing candidates per network × case while
    publishing every candidate and noncandidate result;
15. publish an auditable filter funnel showing how many records enter, pass,
    and fail every filter at every scientifically meaningful reporting scope;
    and
16. publish complete provenance, sensitivity results, checks, and terminal
    statuses.

### Phase 18 will not

- change Phase 08 differential-expression results;
- change the Phase 09 MitoCarta annotation;
- alter Phase 12 queries, backgrounds, networks, directions, or source groups;
- write into <code>results/minerva_production/12_kda/</code>;
- combine the five secondary pooled groups with the six primary groups;
- combine AD-both results with separate AD-up and AD-down evidence;
- use the manually highlighted 14-gene list as an eligibility filter;
- use the existing 200 conservative genes as the candidate universe;
- select genes from only the significant Phase 12 result rows;
- use Phase 13, 14, or 15 results as inputs or ranking criteria;
- use literature support, druggability, or experimental convenience to
  determine primary membership or statistical rank;
- rank the three cases against one another;
- fill a top-five display position with a gene that failed the candidate gate;
- describe a network candidate as a proven causal regulator;
- infer mitochondrial function, ATP production, respiration, or therapeutic
  efficacy from RNA-network evidence; or
- overwrite an existing validated Phase 18 production bundle.

## Scientific question in plain language

Phase 12 tested whether the genes near or downstream of a candidate gene in an
inferred network contain more AD-associated mitochondrial genes than expected.
One Phase 12 run corresponds to:

~~~text
one fine cell type
× one sex/APOE analysis group
× one direction of AD change
× the matching broad network
~~~

The input mitochondrial genes are called the **query**. The gene whose
neighborhood is examined is called the **candidate driver**.

The Phase 18 problem is that these candidates do not all have the same
relationship to the query. A mitochondrial gene that is itself in the query
is different from a non-mitochondrial gene whose neighborhood reaches the
query. Phase 18 therefore separates three cases before filtering or ranking.

## Plain-language map of the workflow

~~~text
Validate the frozen Phase 12 and Phase 09 production artifacts
                              |
                              v
Build the 648-row primary AD-up/AD-down run manifest
                              |
                              v
Keep validated runs with effective query size >= 10
                              |
                              v
Reconstruct every gene-level KDA test, including valid P = 1 nulls
                              |
                              v
Assign Case 1, Case 2, or Case 3
           |                  |                  |
           v                  v                  v
   core MitoCarta       core MitoCarta      outside core
     and in query       and not in query       MitoCarta
           |
           v
Remove self-overlap and recompute Case 1 layer, P value, and fold enrichment
                              |
                              v
Recompute run-level q values and conservative supporting-run flags
                              |
                              v
Apply 80% coverage, ACAT, and aggregate FDR
                              |
                              v
Assign terminal candidate statuses and evidence annotations
                              |
                              v
Sort by ACAT q within each network and case; publish up to five
~~~

## Relationship to preceding phases

### Required Phase 12 dependency

Phase 18 depends directly on the validated Phase 12 production bundle:

~~~text
results/minerva_production/12_kda/
~~~

The current Phase 12 status reports:

| Field | Validated value |
|---|---:|
| Fine cell types | 54 |
| Broad networks | 9 |
| Planned runs | 1,782 |
| Phase 12 eligible runs | 1,021 |
| Skipped runs | 761 |
| Failed runs | 0 |
| Significant runs | 840 |
| Significant key-driver rows | 10,172 |
| Validation status | <code>validated_complete</code> |

These values are readiness checks, not Phase 18 scientific results. Phase 18
must independently validate the status row and all required hashes before
constructing any new test.

### Required Phase 09 annotation

The Phase 12 artifact manifest declares the required Phase 09 annotation:

~~~text
results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz
~~~

Phase 18 uses this file to determine:

- current gene symbol;
- Human MitoCarta3.0 membership;
- mtDNA versus nuclear genome origin;
- core, extended, and non-mitochondrial tier annotations; and
- identifier mapping status.

The Phase 09 file must match the SHA-256 recorded by Phase 12. Phase 18 must
not silently substitute a newer annotation.

### Relationship to Phases 13–15

Phases 13–15 do not supply scientific inputs to Phase 18. Their planning,
status, or results must not affect which Phase 18 genes are tested, selected,
or ranked.

### Existing figures are motivation, not authoritative inputs

The current Phase 12 circular, reduced circular, ACAT, and sex/APOE figure
tables motivated Phase 18. They are derived products and must not serve as
authoritative scientific inputs.

In particular, Phase 18 must not read:

~~~text
results/figures/analysis/phase12_kda/
~~~

to construct its primary candidate universe or statistical results. Those
files may be compared after production as nonblocking reconciliation checks.

## Frozen scientific design

### Analysis units

Phase 18 uses two connected units:

~~~text
run-level unit:
    one candidate gene × one included Phase 12 run

aggregate unit:
    one gene × one broad network × one case
~~~

The run-level unit supplies enrichment, P value, q value, overlap, and
supporting-run status. The aggregate unit supplies coverage, ACAT evidence,
candidate status, independent within-case rank, and top-five display status.

### Complete Phase 12 run grid

The complete Phase 12 grid contains:

~~~text
54 fine cell types
× 11 groups (6 primary + 5 secondary)
× 3 directions (AD-up, AD-down, and AD-both)
= 1,782 runs
~~~

The six primary groups are:

| Order | Group ID | Sex | APOE group |
|---:|---|---|---|
| 1 | <code>F_e2</code> | Female | e2 |
| 2 | <code>F_e33</code> | Female | e3/e3 |
| 3 | <code>F_e4</code> | Female | e4 |
| 4 | <code>M_e2</code> | Male | e2 |
| 5 | <code>M_e33</code> | Male | e3/e3 |
| 6 | <code>M_e4</code> | Male | e4 |

The five secondary pooled groups are:

| Order | Group ID | Members |
|---:|---|---|
| 1 | <code>female_pool</code> | <code>F_e2</code>, <code>F_e33</code>, <code>F_e4</code> |
| 2 | <code>male_pool</code> | <code>M_e2</code>, <code>M_e33</code>, <code>M_e4</code> |
| 3 | <code>e2_pool</code> | <code>F_e2</code>, <code>M_e2</code> |
| 4 | <code>e33_pool</code> | <code>F_e33</code>, <code>M_e33</code> |
| 5 | <code>e4_pool</code> | <code>F_e4</code>, <code>M_e4</code> |

### Primary Phase 18 run scope

Primary driver selection uses **only the six primary groups and only the
separate AD-up and AD-down mitochondrial queries**:

~~~text
54 fine cell types
× 6 primary groups
× 2 directions
= 648 primary directional run slots
~~~

All 648 slots appear in <code>key_driver_run_manifest.tsv</code>. A slot
becomes scientifically included only if:

1. Phase 12 marked the run eligible;
2. Phase 12 completed the run without failure;
3. all required sources and hashes validate;
4. the effective query contains at least 10 genes; and
5. the broad network and run background can be reconstructed exactly.

Under the currently frozen Phase 12 production bundle, Phase 18 preflight must
reproduce:

| Run category | Expected count |
|---|---:|
| Primary AD-up/AD-down slots | 648 |
| Phase 12 eligible within those slots | 295 |
| Included after effective query ≥10 | 161 |
| Excluded from primary Phase 18 selection | 487 |

The 161 included runs are distributed as:

| Broad network | Included runs |
|---|---:|
| Astrocytes | 21 |
| Excitatory neurons | 97 |
| Inhibitory neurons | 28 |
| Microglia | 6 |
| OPCs | 6 |
| Oligodendrocytes | 2 |
| Vasculature cells | 1 |
| CAMs | 0 |
| T cells | 0 |

The extreme imbalance is reported explicitly. Oligodendrocyte and vasculature
results cannot be described as broadly stable across many runs merely because
coverage is high.

The five secondary groups and AD-both are excluded from the primary analysis.
They are correlated summaries of evidence already represented by the primary
groups or separate directions. Phase 18 version 1 does not use them to select
or rank genes.

### Candidate universe

Phase 18 begins with every unique current gene symbol present in the effective
background of at least one of the 161 included runs.

It does not start from:

- the manually highlighted pool of 14 genes;
- the 200 genes with at least one prior conservative significant result;
- genes already displayed in a figure;
- genes with a significant Phase 12 result; or
- MitoCarta genes alone.

For each included run, the complete candidate matrix has one row for every
background gene. A gene with an explicit fKDA neighborhood test carries its
calculated result. Every remaining background gene carries an
<code>implicit_zero_overlap</code> result with P = 1. A gene absent from that
run's effective background has no test and is represented as missing only
when constructing cross-run matrices.

### Fixed three-case classification

For Phase 18, **MT-related** means membership in the fixed 1,136-gene Human
MitoCarta3.0 core inventory.

Every usable gene × run result receives exactly one case:

| Case ID | Plain name | Exact rule | Scientific interpretation |
|---|---|---|---|
| <code>case1_core_mito_in_query</code> | MT-related and in query | <code>is_mitocarta3 = TRUE</code> and effective query membership is TRUE | The altered mitochondrial gene must reach other altered mitochondrial genes after removing itself |
| <code>case2_core_mito_not_in_query</code> | MT-related and not in query | <code>is_mitocarta3 = TRUE</code> and effective query membership is FALSE | Query-independent evidence for a mitochondrial component or regulator |
| <code>case3_not_core_mito</code> | Not MT-related | <code>is_mitocarta3 = FALSE</code> | Evidence for a candidate outside the queried core mitochondrial inventory |

Because the query is restricted to core MitoCarta genes, a Case 3 gene cannot
be a query member.

Genes marked <code>mito_extended</code> but not in the 1,136-gene core
inventory belong to Case 3. Their extended annotation remains visible in
outputs; it does not create a fourth case.

A core MitoCarta gene can contribute one Case 1 aggregate from runs in which
it is in the query and a separate Case 2 aggregate from runs in which it is
not in the query. The two aggregates are never pooled.

### Gene identifier rules

The primary key is the Phase 09 current HGNC symbol. Phase 18 must:

1. normalize symbols only through the frozen Phase 09 mapping;
2. reject conflicting core-MitoCarta membership for the same current symbol;
3. preserve original and canonical identifiers for audit;
4. record unmapped or ambiguous symbols explicitly;
5. exclude ambiguous symbols from candidate status while retaining an audit
   row; and
6. never infer core membership from an <code>MT-</code> prefix alone.

Genome origin and an <code>MT-</code> prefix are annotations, not substitutes
for the three-case rule.

## Reconstruction of one gene-level KDA test

### Meaning of one test

One test is:

~~~text
one candidate gene × one included Phase 12 run
~~~

It asks whether the effective mitochondrial query is more concentrated in the
candidate's directed network neighborhood than expected in the complete
run-specific background.

For a candidate and one layer:

| Symbol | Meaning |
|---|---|
| M | Effective background size |
| k | Effective query size |
| m | Candidate neighborhood size |
| q | Query genes in the neighborhood |

The fold enrichment is:

~~~text
fold enrichment = (q / m) / (k / M)
~~~

The raw P value is the upper-tail hypergeometric probability of observing at
least q query genes in a neighborhood of size m, given k query genes in a
background of size M.

### Exact reconstruction of Phase 12

For every included run, Phase 18 must:

1. read the effective query from
   <code>kda_signature_members.tsv.gz</code>;
2. read the exact background from
   <code>kda_background_members.tsv.gz</code>;
3. restrict the declared broad network to edges whose two endpoints are in
   that background;
4. reproduce the induced-network edge and node counts in the Phase 12
   manifest;
5. identify explicit fKDA candidates by expanding undirected distance up to
   three layers from the query;
6. calculate directed candidate neighborhoods for layers 1, 2, and 3;
7. select the layer with the smallest raw P value, using the smaller layer as
   a deterministic tie-breaker;
8. add every other background gene as an implicit zero-overlap result with
   P = 1; and
9. reproduce all original Phase 12 significant rows before applying any
   Phase 18 correction.

Exact reproduction of the Phase 12 key, layer, overlap, neighborhood,
background, query, fold-enrichment, log-P, and adjusted-P fields is a blocking
check.

### Case 1 self-overlap correction

The frozen fKDA neighborhood includes the starting driver. For a Case 1
candidate, that driver is also in the query and automatically contributes one
overlap.

At every available layer, Phase 18 removes the driver once:

~~~text
M_self_excluded = M - 1
k_self_excluded = k - 1
m_self_excluded = m - 1
q_self_excluded = q - 1
~~~

Phase 18 then:

1. validates that every adjusted count is nonnegative and internally possible;
2. recalculates fold enrichment and the upper-tail hypergeometric P value;
3. assigns P = 1 when no remaining overlap or neighborhood evidence exists;
4. reselects the best layer using the self-excluded P values; and
5. preserves both original and self-excluded statistics.

Reselecting the layer is required because the original best layer may no
longer be best after self-overlap is removed.

Cases 2 and 3 retain their original layer and enrichment statistics after
Phase 12 reproduction succeeds.

### Explicit and implicit test statuses

| Test status | Meaning | P value carried forward |
|---|---|---:|
| <code>explicit_test</code> | fKDA evaluated at least one directed neighborhood | Calculated P value |
| <code>explicit_zero_overlap</code> | Explicit candidate with no query overlap | 1 |
| <code>implicit_zero_overlap</code> | Background gene outside the explicit candidate set | 1 |
| <code>absent_from_background</code> | No gene-level test was possible | Missing |
| <code>invalid_test</code> | Counts, identifiers, or computation failed validation | Missing and blocking if unexpected |

P = 1 means a usable test found no enrichment. Missing means no test was
possible. These states must never be collapsed.

### Run-level multiple-testing correction

After Case 1 P values are corrected, Phase 18 recomputes Benjamini-Hochberg
q values within each run across the **explicit fKDA candidate set**.

This preserves the Phase 12 candidate-testing family while updating all q
values affected by the Case 1 changes. Implicit zero-overlap background genes
retain P = 1 and q = 1; they do not enlarge the explicit run-level family.

The output stores:

- original Phase 12 P and q;
- reconstructed pre-correction P and q;
- Phase 18 self-excluded P and fold enrichment for Case 1;
- Phase 18 final run-level P and q used downstream; and
- the explicit-family size.

## Candidate filtering

Filtering determines whether a gene qualifies as a driver candidate. Sorting
occurs only after filtering.

### Filter 1: Frozen run scope

Use only:

- the six primary groups;
- AD-up and AD-down separately;
- Phase 12 eligible and completed runs;
- effective query size at least 10; and
- the matching broad network.

The 161 included runs are frozen before gene results are viewed.

### Filter 2: Usable gene-level result

Within each broad network, first take the union of genes found in at least one
included run background. Cross that union with the included runs for the same
network. Each resulting gene × run pair is one Filter 2 opportunity. This
makes absent-background results visible instead of silently dropping them.

A usable result requires:

1. an included run;
2. the gene in the effective background;
3. valid identifiers and network membership;
4. internally possible enrichment counts; and
5. a final raw P value in [0, 1].

An explicit or implicit P = 1 result is usable. An absent-background or invalid
result is missing.

### Filter 3: Conservative supporting run

One run is conservative support for a gene only when:

1. the effective query contains at least 10 genes;
2. the candidate reaches at least two **other** query genes;
3. final fold enrichment is greater than 1; and
4. the final run-level q value is at most 0.05.

For Case 1:

~~~text
other-query overlap = original q - 1
~~~

For Cases 2 and 3:

~~~text
other-query overlap = original q
~~~

Case 1 therefore needs an original overlap of at least three to retain at
least two other query genes.

A valid run that fails the conservative-support rule is not deleted. Its P
value remains an ACAT input.

### Filter 4: Coverage

Coverage is calculated for one gene × broad network × case:

~~~text
           eligible case-runs with a usable gene-level result
coverage = ─────────────────────────────────────────────────
                  all eligible runs for that case
~~~

The denominator is:

- Case 1: included network runs in which that core MitoCarta gene belongs to
  the effective query;
- Case 2: included network runs in which that core MitoCarta gene does not
  belong to the effective query; and
- Case 3: all included runs in that broad network.

The numerator counts explicit tests and implicit zero-overlap P = 1 results.
It does not count absent-background or invalid results.

Always publish the numerator, denominator, and fraction. A fraction based on
4/5 runs is not described as equally information-rich as 80/100.

Primary coverage must be at least 0.80. Coverage is evaluated before ACAT and
does not depend on significance.

### Filter 5: Aggregate evidence

For each coverage-qualified gene × broad network × case:

1. collect every usable final run-level P value;
2. retain significant, non-significant, and P = 1 results;
3. omit genuine missing values in the primary analysis;
4. combine the P values with the frozen ACAT implementation; and
5. apply Benjamini-Hochberg correction across all coverage-qualified
   gene × case aggregates within that broad network.

The aggregate correction family includes all three cases together within a
broad network. Sorting remains separate by case.

The ACAT implementation must:

- accept only finite P values in [0, 1];
- return 1 when all inputs equal 1;
- use the frozen numerical handling for exact 0 and 1 boundaries;
- reproduce the existing validated professor-example vector within tolerance;
- return the same value regardless of input order; and
- record the number of usable and missing inputs.

### Final candidate gate

A gene × broad network × case aggregate is a driver candidate only if:

| Component | Required value |
|---|---|
| Coverage | ≥0.80 |
| Conservative supporting runs | ≥1 |
| Gene-level ACAT q value | ≤0.05 |

Every aggregate receives one terminal status:

| Status | Rule |
|---|---|
| <code>driver_candidate</code> | All three gate components pass |
| <code>aggregate_only</code> | Coverage and ACAT q pass, but no conservative supporting run |
| <code>exploratory</code> | Coverage passes and raw ACAT P ≤0.05, but ACAT q >0.05 |
| <code>insufficient_coverage</code> | Coverage <0.80 |
| <code>not_supported</code> | Coverage passes but raw ACAT P >0.05 |
| <code>not_testable</code> | No usable aggregate can be calculated |

Only <code>driver_candidate</code> rows enter the primary ranked lists.

### Filter-count reporting contract

Phase 18 must make filter attrition directly visible. The word "gene" alone
is not a sufficient counting unit because Filters 1 and 2 operate below the
final gene × network × case level. The output must therefore report the
native unit used by each filter:

| Filter | Native counting unit | Required counts | Required scopes |
|---|---|---|---|
| Filter 1: frozen run scope | Run slot | All 648 primary directional slots; included slots; excluded slots; every exclusion reason | Overall and broad network; also tabulate group and direction |
| Filter 2: usable result | Gene × included-run opportunity | Total opportunities; usable explicit tests; usable implicit P = 1 results; absent-background results; invalid results | Overall and broad network; case where assignable |
| Filter 3: conservative support | Gene × broad-network × case aggregate | Aggregates with at least one conservative supporting run; aggregates with none | Overall, broad network, and broad network × case |
| Filter 4: coverage | Gene × broad-network × case aggregate | Aggregates with coverage ≥0.80; aggregates below 0.80 | Overall, broad network, and broad network × case |
| Filter 5: aggregate evidence | Gene × broad-network × case aggregate | Aggregates with ACAT q ≤0.05; aggregates above 0.05; not-testable aggregates | Overall, broad network, and broad network × case |

The authoritative candidate funnel uses a fixed, sequential order at the
aggregate level:

~~~text
all gene × broad-network × case aggregates with an eligible-run denominator
-> Filter 3: at least one conservative supporting run
-> Filter 4: coverage >= 0.80
-> Filter 5: ACAT q <= 0.05
-> driver candidates
~~~

For every sequential step, publish:

- number entering the step;
- number passing the step;
- number first removed at that step;
- number remaining after the step; and
- distinct current gene symbols represented by those rows.

The sequential aggregate counts must satisfy:

~~~text
entering = passing + first removed
next-step entering = previous-step passing
final remaining = number of driver-candidate aggregate rows
~~~

The primary count is the number of aggregate rows because the same gene may
legitimately appear in more than one network or in both Case 1 and Case 2.
Distinct-gene counts are also reported, but they are descriptive and must not
be added across networks or cases.

In addition to the sequential funnel, publish independent pass/fail counts
for the three final-gate components. These independent counts reveal overlap;
for example, one aggregate may fail both coverage and conservative support.
They therefore do not have to sum to the number removed by the sequential
funnel.

Filter 5 q values are always calculated in the full frozen broad-network BH
family defined above. Reporting Filter 3 before Filter 4 and Filter 5 in the
funnel does not change which rows enter ACAT or the multiple-testing family.
The funnel describes attrition; it does not redefine the statistics.

## Ranking and top-five selection

### Three independent rankings

Every broad network produces up to three independent ranked lists:

1. Case 1 only;
2. Case 2 only; and
3. Case 3 only.

There is no cross-case rank. A Case 1 gene ranked first and a Case 3 gene
ranked first are each first only within their own case and network.

### Frozen sort order

Within one broad network and one case, sort passing candidates by:

1. smaller gene-level ACAT q value;
2. smaller raw ACAT P value when q values tie; and
3. current gene symbol alphabetically as the final deterministic tie-breaker.

The rank is therefore, in ordinary circumstances, literally the ascending
ACAT q-value order. Fine-cell breadth, recurrence, fold enrichment, coverage,
and stability do not move a gene ahead of another gene with a smaller q value.

### Evidence annotations

The ranked table still reports:

- conservative supporting-run count;
- recurrence fraction;
- number of supporting fine cell types;
- supporting sex/APOE groups;
- supporting directions;
- median and maximum final fold enrichment;
- usable-run count and coverage;
- leave-one-fine-cell-type-out stability; and
- missing-data, coverage, aggregation, and network-degree sensitivities.

These fields explain the rank and its limitations. They are not combined into
an opaque weighted score.

### Evidence tiers

Evidence tiers are annotations, not sorting variables:

| Tier | Rule |
|---|---|
| <code>tier1_recurrent_stable</code> | Candidate; support in at least two fine cell types; nominal ACAT P ≤0.05 in at least 80% of assessable leave-one-fine-cell-type-out repetitions |
| <code>tier2_localized_or_unstable</code> | Candidate, but support is limited to one fine cell type or stability is below 80% |
| <code>tier_not_assessable</code> | Candidate in a network/case with too few distinct eligible fine cell types for the stability check |

### Top-five display rule

For each broad network × case:

- if more than five genes pass, mark ranks 1–5 for display;
- if fewer than five genes pass, display only the passing genes;
- if no gene passes, publish an explicit empty-result status; and
- never promote a noncandidate to fill a display slot.

The complete ranked table remains the authoritative result. Top five is a
display cap, not a statistical threshold.

### Top-five lookup contract

<code>key_driver_top5.tsv</code> must make the answer findable without
reconstructing ranks from another table. It covers all:

~~~text
9 declared broad networks × 3 cases = 27 network × case lists
~~~

Each list contains either:

- candidate rows with display ranks 1 through min(5, candidate count); or
- one explicit status row when no ranked gene can be shown.

Allowed list statuses are:

| List status | Meaning |
|---|---|
| <code>ranked_candidates</code> | At least one gene passed; the file contains its top one to five candidates |
| <code>no_passing_candidate</code> | The network × case was testable, but no gene passed all filters |
| <code>not_testable_no_included_runs</code> | The broad network had no included Phase 18 runs |
| <code>not_testable_no_eligible_case_runs</code> | Runs existed, but this case had no eligible-run denominator |

Every top-five row must include broad network, case order, case ID, list
status, total passing-candidate count, displayed-candidate count, display
rank, gene symbol, ACAT P, ACAT q, coverage numerator and denominator,
conservative-support count, and evidence tier. Rank and gene fields are
missing only for an explicit no-result status row.

There is no pooled top-five list across broad networks because the aggregate
q values are corrected within broad network. The interpretable lookup is the
top five within each broad network and each of the three cases.

## Stability and sensitivity analyses

### Leave one fine cell type out

Within every broad network, repeat aggregation after omitting each included
fine cell type in turn. Recompute:

- case-specific denominators;
- coverage;
- ACAT P values;
- the broad-network aggregate BH family; and
- candidate status.

For each gene, report:

- number of assessable omissions;
- fraction with nominal ACAT P ≤0.05;
- fraction with ACAT q ≤0.05;
- fraction retaining candidate status; and
- worst rank among repetitions.

Do not assign stability when fewer than two distinct fine cell types can be
omitted meaningfully.

### Missing-data sensitivity

Primary ACAT omits genuine missing values after the 80% coverage gate.

The conservative sensitivity replaces remaining missing values with P = 1.
Report whether candidate status and top-five membership persist.

### Coverage sensitivity

Repeat the aggregate analysis at:

- 0.50 coverage;
- 0.80 coverage, primary; and
- 1.00 coverage.

Do not choose the threshold that produces preferred genes.

### Alternative aggregation

Recalculate aggregate evidence with the existing mean-of-log-P method.
This result is a sensitivity analysis only. It cannot replace ACAT after
results are viewed.

### Network-degree sensitivity

Highly connected genes have more opportunities to reach query genes. The
hypergeometric test accounts for neighborhood size, but topology may still
favor hubs.

For each primary candidate, compare the observed aggregate evidence with
degree- and neighborhood-size-matched genes from the same broad network.
The configuration must freeze:

- matching variables and bins;
- number of random draws;
- replacement policy;
- random-number generator and seed; and
- empirical-tail calculation.

This is a nonblocking robustness annotation in Phase 18 version 1 unless a
later approved amendment defines it as a candidate gate.

### Secondary groups and AD-both

The five pooled secondary groups and AD-both do not enter Phase 18 version 1
selection, ranking, or FDR families. A future sensitivity extension requires
an approved plan amendment and must publish separate families without
changing the primary results.

## Multiple-testing families

Phase 18 has two levels of multiplicity:

### Run-level family

Within each included run, apply BH to the final P values for all explicit fKDA
candidates in that run. Case 1 changes require the entire explicit family to
be corrected again.

### Aggregate-level family

Within each broad network, apply BH to every coverage-qualified gene × case
ACAT P value. The three cases share this correction family but retain separate
ranks and displays.

Store both raw P and adjusted q values. A run-level q value and a gene-level
ACAT q value are different quantities and must have different column names.

## Inputs and dependencies

### Required Phase 12 files

Require the declared production artifacts:

| File | Phase 18 use |
|---|---|
| <code>kda_status.tsv</code> | Require <code>validated_complete</code>, 1,782 planned runs, zero failures, and expected identity |
| <code>kda_artifacts.tsv</code> | Resolve and verify Phase 12, Phase 09, fKDA, and network hashes |
| <code>kda_checks.tsv</code> | Require all blocking checks to pass |
| <code>kda_run_manifest.tsv</code> | Build the 648-slot Phase 18 scope and reproduce run counts |
| <code>kda_signature_members.tsv.gz</code> | Reconstruct every effective query |
| <code>kda_background_members.tsv.gz</code> | Reconstruct every exact effective background |
| <code>kda_results.tsv.gz</code> | Validate exact pre-correction reproduction of significant Phase 12 results |
| <code>kda_qc_summary.tsv</code> | Reconcile run eligibility and query/background diagnostics |

<code>kda_key_driver_summary.tsv</code> may be reconciled after computation
but does not define the candidate universe or Phase 18 ranks.

Only artifact-declared compressed membership and result files are scientific
inputs. Undeclared convenience copies are ignored.

### Required inherited files

Resolve through <code>kda_artifacts.tsv</code>:

- <code>config/phase12_kda.yml</code>;
- <code>scripts/NetWeaver/fKDA.R</code>;
- <code>results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz</code>;
- the Phase 09 status and checks; and
- all nine audited broad-network edge lists.

Every hash must match the value recorded by Phase 12.

### Required configuration and software

Implementation adds:

~~~text
config/phase18_key_driver_selection.yml
~~~

It freezes:

- Phase 12 input root and expected status identity;
- six primary groups and their order;
- AD-up and AD-down direction IDs;
- effective-query minimum of 10;
- three case IDs and order;
- fKDA layers and reconstruction rules;
- self-exclusion and layer-reselection rules;
- run-level BH family and q threshold;
- conservative supporting-run definition;
- coverage threshold and sensitivities;
- ACAT implementation and numerical tolerances;
- aggregate BH family and q threshold;
- candidate statuses;
- ranking and top-five rules;
- stability and topology sensitivities;
- output filenames and schema versions;
- local-pilot fixture;
- deterministic seeds; and
- scratch, staging, and final output paths.

The implementation should use the repository's frozen R environment. Any new
package or lockfile change is a plan deviation requiring approval.

### Explicit non-inputs

The Phase 18 scientific script must not read:

- Phase 12 figure-derived tables;
- the 14-gene curated pool;
- the prior 200-gene conservative summary;
- Phase 10 similarity or Phase 11 pathway ranking outputs;
- Phase 13, 14, or 15 results;
- literature-derived priority scores; or
- local-pilot outputs during production.

## Construction and analysis workflow

### Task 1: Freeze Phase 18 definitions

1. approve this plan;
2. assign Phase 18 permanently and reserve 16 and 17;
3. freeze the YAML configuration;
4. freeze case IDs, thresholds, families, sort order, and top-five rule;
5. freeze output schemas and random seeds; and
6. record code and plan hashes.

### Task 2: Validate inherited inputs

1. require Phase 12 <code>validated_complete</code>;
2. verify every required artifact path, size, and SHA-256;
3. verify Phase 09 identity and MitoCarta annotations;
4. validate all nine network hashes and direction convention;
5. reproduce 1,782 total Phase 12 rows and zero failures;
6. reproduce the 648 primary directional slots;
7. reproduce 295 Phase 12-eligible primary directional runs;
8. reproduce 161 runs with effective query size at least 10; and
9. stop before scientific computation if any blocking check fails.

### Task 3: Build the Phase 18 run and case manifests

1. publish all 648 structural run slots;
2. assign included or excluded status and one explicit reason;
3. record the seven-network included-run distribution;
4. create the three-row case manifest;
5. construct the frozen gene annotation lookup; and
6. calculate expected case denominators without using P values.

### Task 4: Reconstruct the complete candidate-test matrix

For each of the 161 included runs:

1. reconstruct query, background, and induced network;
2. calculate every explicit candidate at every available layer;
3. reproduce original Phase 12 significant results exactly;
4. append implicit zero-overlap P = 1 background genes;
5. assign one case to every usable row;
6. apply Case 1 self-exclusion at every layer;
7. reselect the Case 1 best layer;
8. recompute the explicit run-level BH family; and
9. checkpoint the validated run shard.

### Task 5: Assign conservative supporting-run status

1. apply the query-size rule;
2. count other-query overlap;
3. use final fold enrichment;
4. use final run-level q;
5. record every component Boolean; and
6. retain nonsupporting valid P values for aggregation.

### Task 6: Calculate coverage and aggregate evidence

1. build the complete network × gene × case manifest;
2. calculate eligible, usable, explicit, implicit, and missing counts;
3. apply the 0.80 coverage gate;
4. run primary ACAT on all usable P values;
5. apply aggregate BH within broad network;
6. assign every aggregate a terminal candidate status; and
7. publish native-unit, sequential, and independent-component filter counts
   overall and by broad network × case.

### Task 7: Rank and select top five

1. split candidates by broad network and case;
2. sort by ACAT q, raw ACAT P, then symbol;
3. assign independent within-case ranks;
4. flag ranks 1–5 for display;
5. leave unused display slots empty; and
6. represent all 27 declared network × case lists with ranked rows or an
   explicit no-result status; and
7. produce one figure-ready table from the authoritative ranked results.

### Task 8: Run stability and sensitivity analyses

1. leave one fine cell type out;
2. replace missing values with P = 1;
3. repeat coverage at 0.50 and 1.00;
4. compare mean-of-log-P aggregation;
5. run the frozen network-degree sensitivity; and
6. summarize status and top-five changes.

### Task 9: Validate and publish atomically

1. finish all structural, numerical, and scientific checks in scratch;
2. write every declared scientific output to staging;
3. write checks;
4. write the artifact manifest;
5. independently validate the staging bundle;
6. write the final status last; and
7. atomically publish the complete directory.

## Output and file contract

Final production root:

~~~text
results/minerva_production/18_key_driver_selection/
~~~

The final directory is flat and contains exactly 21 files:

| File | Required content |
|---|---|
| <code>key_driver_analysis_manifest.tsv</code> | One frozen Phase 18 definition, approvals, thresholds, methods, versions, and hashes |
| <code>key_driver_case_manifest.tsv</code> | Exactly three ordered case definitions |
| <code>key_driver_run_manifest.tsv</code> | Exactly 648 primary directional slots with inclusion and exclusion reasons |
| <code>key_driver_input_inventory.tsv</code> | Required Phase 12, Phase 09, fKDA, network, config, code, and lockfile identities |
| <code>key_driver_source_checks.tsv</code> | Upstream schemas, dimensions, keys, statuses, and hash validation |
| <code>key_driver_candidate_tests.tsv.gz</code> | Complete network-specific gene × included-run opportunity matrix, including usable P = 1 and missing-status rows, with original, reconstructed, self-excluded, and final test fields |
| <code>key_driver_conservative_support.tsv.gz</code> | All component decisions for conservative supporting runs |
| <code>key_driver_gene_case_summary.tsv.gz</code> | Every network × gene × case aggregate, including noncandidates |
| <code>key_driver_candidates.tsv</code> | All rows passing the final candidate gate |
| <code>key_driver_top5.tsv</code> | At most five passing genes per network × case plus explicit empty-result records |
| <code>key_driver_stability_replicates.tsv.gz</code> | Leave-one-fine-cell-type-out replicate results |
| <code>key_driver_stability_summary.tsv</code> | Stability counts, fractions, rank range, and evidence tier |
| <code>key_driver_sensitivity_results.tsv.gz</code> | Missing-value, coverage, and aggregation sensitivities |
| <code>key_driver_network_degree_sensitivity.tsv</code> | Degree-matched topology sensitivity for candidates |
| <code>key_driver_figure_data.tsv</code> | Figure-ready top-five and group-contribution data derived only from authoritative candidate tables |
| <code>key_driver_exclusion_summary.tsv</code> | Counts and reasons for run, test, aggregate, and candidate exclusions |
| <code>key_driver_filter_funnel.tsv</code> | Native-unit counts, sequential aggregate attrition, and independent gate pass/fail counts at the required overall, network, and network × case scopes |
| <code>key_driver_stage_status.tsv</code> | Stage dependencies, fingerprints, shard counts, elapsed times, and terminal states |
| <code>key_driver_checks.tsv</code> | Blocking and nonblocking checks |
| <code>key_driver_artifacts.tsv</code> | Every declared path, schema, row count, byte count, and SHA-256 |
| <code>key_driver_status.tsv</code> | One phase-level technical and scientific status row |

Every TSV begins with <code>schema_version</code>. Every final file is declared
in <code>key_driver_artifacts.tsv</code>. No scratch directory, temporary
shard, undeclared file, or figure image is permitted in the final production
root.

### Required aggregate fields

<code>key_driver_gene_case_summary.tsv.gz</code> must include at least:

- broad network, current symbol, and case ID;
- MitoCarta, mitochondrial tier, and genome-origin annotations;
- eligible, usable, explicit, implicit, and missing run counts;
- coverage numerator, denominator, and fraction;
- conservative support count and recurrence;
- supporting fine-cell-type, group, and direction breadth;
- median and maximum final fold enrichment;
- primary ACAT P and gene-level q;
- missing-as-one ACAT P and q;
- alternate-coverage and aggregation results;
- stability fields;
- candidate component Booleans;
- terminal candidate status;
- within-case rank;
- top-five display flag; and
- deterministic exclusion reason where applicable.

### Required top-five fields

<code>key_driver_top5.tsv</code> must include at least:

- broad network, ordered case ID, and list status;
- total passing-candidate and displayed-candidate counts;
- display rank and current gene symbol;
- primary ACAT P and gene-level q;
- coverage numerator, denominator, and fraction;
- conservative-support count;
- evidence tier; and
- deterministic empty-result reason when no gene is displayed.

The table must cover all 27 declared network × case combinations. A
combination with candidates has one row per displayed gene. A combination
without a displayed gene has exactly one explicit status row.

### Required filter-funnel fields

<code>key_driver_filter_funnel.tsv</code> must include at least:

- report type: <code>native_filter</code>,
  <code>sequential_candidate_funnel</code>, or
  <code>independent_gate</code>;
- summary scope: overall, broad network, or broad network × case;
- broad network and case ID, using an explicit <code>ALL</code> value when a
  dimension is summarized;
- filter number, filter name, ordered funnel step, and counting unit;
- input, pass, fail, and cumulative-remaining row counts;
- input, pass, fail, and remaining distinct-gene counts where meaningful;
- explicit, implicit, absent, invalid, and not-testable counts where
  applicable; and
- a deterministic reason code for every reported failure category.

For every compatible sequential row, input must equal pass plus fail. The
Filter 3–5 aggregate funnel must end at exactly the number of rows in
<code>key_driver_candidates.tsv</code>.

### Routine post-run lookups

After a validated Phase 18 run, answer the two routine questions as follows:

| Question | Authoritative file | Lookup |
|---|---|---|
| What are the top five genes? | <code>key_driver_top5.tsv</code> | Select one broad network and one of the three cases, then read nonmissing genes in ascending <code>display_rank</code> order |
| How many records did each filter remove? | <code>key_driver_filter_funnel.tsv</code> | Use <code>sequential_candidate_funnel</code> for additive Filter 3–5 attrition and <code>native_filter</code> for Filters 1–2 |
| How many aggregates fail each gate, including overlapping failures? | <code>key_driver_filter_funnel.tsv</code> | Use <code>independent_gate</code> and the desired overall, network, or network × case scope |
| Which individual genes passed or failed, and why? | <code>key_driver_gene_case_summary.tsv.gz</code> | Select the network, case, gene, terminal status, and component Boolean fields |

The production status is not <code>validated_complete</code> unless these
lookups reconcile with the detailed source tables.

### Required run-level fields

<code>key_driver_candidate_tests.tsv.gz</code> must include at least:

- run, fine-cell, broad-network, group, and direction IDs;
- current and original gene identifiers;
- three-case ID;
- effective query and background sizes;
- test status and explicit-family membership;
- original Phase 12 layer and counts;
- reconstructed pre-correction layer and counts;
- self-excluded Case 1 counts;
- final selected layer and counts;
- original, reconstructed, and final fold enrichment;
- original, reconstructed, and final raw P;
- original and final run-level q;
- query-membership and core-MitoCarta flags;
- conservative-support component Booleans; and
- provenance fields.

## Phase 18 end state

### Scientific and technical end state

Production is technically complete when:

~~~text
validation_status = validated_complete
phase12_planned_runs = 1782
phase18_structural_run_slots = 648
phase18_included_runs = 161
phase18_cases = 3
included_broad_networks = 7
failed_upstream_runs = 0
all_aggregate_rows_have_terminal_status = TRUE
all_candidate_rows_have_within_case_rank = TRUE
top_five_display_cap_respected = TRUE
network_case_top_five_lists_represented = 27
filter_funnel_complete = TRUE
filter_funnel_final_count_matches_candidates = TRUE
~~~

No positive driver candidate is required for technical completion.

### Source-controlled files added

| File | Purpose |
|---|---|
| <code>config/phase18_key_driver_selection.yml</code> | Frozen inputs, cases, filters, families, ACAT, ranking, sensitivities, outputs, and seeds |
| <code>scripts/18_run_key_driver_selection.R</code> | Package-independent R command-line entry point |
| <code>scripts/18_run_key_driver_selection.py</code> | Validation, test reconstruction, self-exclusion, aggregation, ranking, sensitivities, and atomic publication using the locally available scientific Python stack |
| <code>tests/test_phase18_key_driver_selection.R</code> | R entry point for Phase 18 tests and output validation |
| <code>tests/test_phase18_key_driver_selection.py</code> | Deterministic unit, gate, top-five, filter-funnel, gzip, artifact, and output-only tests |
| <code>docs/phase_18_key_driver_selection/phase_18_key_driver_selection_plan.md</code> | This Phase 18 contract |

The existing companion proposal remains in the same documentation directory.

### Existing source-controlled files modified

| File | Required change |
|---|---|
| <code>scripts/run_pipeline.R</code> | Register and dispatch global task <code>key_driver_selection</code> after KDA |
| <code>config/local_pilot.yml</code> | Add the Phase 18 config path and allow the pilot task |
| <code>config/minerva_shared.yml</code> | Add the Phase 18 config path and allow production execution |

No earlier phase plan, config, result, or status file is modified.

### Files deleted

None. Phase 18 does not delete or overwrite raw data, Phase 09, Phase 12,
figure outputs, or an existing validated Phase 18 bundle.

### Pipeline registration

~~~text
task_mode: key_driver_selection
scope: global
stable_task_id: global:key_driver_selection
output_schema: mitochondrial_key_driver_selection_v1
dependency: global:kda
~~~

Both environment YAML files add:

~~~yaml
project:
  phase18_key_driver_selection_config: config/phase18_key_driver_selection.yml

scope:
  allowed_task_modes:
    - key_driver_selection
~~~

The global task rejects <code>--rds-id</code>.

## Local validation

Synthetic local tests validate computation and contracts only. They do not
produce scientific results.

### Deterministic unit and synthetic checks

Use a deterministic synthetic fixture containing:

- at least two broad networks;
- at least three fine cell types in one network;
- all six primary group labels;
- AD-up and AD-down runs;
- one Case 1 candidate whose apparent result disappears after self-exclusion;
- one Case 1 candidate that remains supported after self-exclusion;
- one supported Case 2 candidate;
- one supported Case 3 candidate;
- explicit and implicit P = 1 results;
- an absent-background missing result;
- a coverage result just below 0.80 and one exactly at 0.80;
- a run with no conservative driver;
- a complete aggregate null;
- tied q values requiring deterministic tie-breaking; and
- fewer than five candidates in at least one network × case.

The pilot must verify:

- count subtraction and hypergeometric arithmetic;
- Case 1 layer reselection;
- exact three-case assignment;
- run-level and aggregate BH families;
- P = 1 versus missing handling;
- ACAT boundary and professor-example behavior;
- coverage denominators;
- candidate statuses;
- independent case ranks;
- top-five behavior and representation of all 27 network × case lists;
- native-unit filter counts and the complete Filter 3–5 aggregate funnel;
- sequential funnel identities and agreement with the candidate table;
- deterministic stability and sensitivity results;
- schemas and artifact hashes; and
- atomic publication.

Pilot status must be:

~~~text
validation_status = nonfinal_smoke_test
scientific_decision = not_applicable_pilot
~~~

### Completed local production-equivalent real-data execution

The user's explicit 2026-08-14 requests authorized one complete local run
against the immutable validated Phase 12 production inputs and, after all
checks passed, promotion of that bundle to the common production-results
root. This was not a reduced synthetic pilot: it reconstructed, aggregated,
filtered, and ranked the complete frozen Phase 18 scope. The storage location
is the production-results tree, while the execution metadata continues to say
that computation occurred locally rather than on Minerva hardware.

The local command is:

~~~bash
Rscript --vanilla scripts/18_run_key_driver_selection.R \
  --phase18-config config/phase18_key_driver_selection.yml \
  --phase12-dir results/minerva_production/12_kda \
  --output-dir results/minerva_production/18_key_driver_selection
~~~

The required terminal status is:

~~~text
execution_stage = local_production_equivalent
execution_class = real_phase12_data_local_production_equivalent
validation_status = validated_complete
~~~

The bundle is an official validated Phase 18 result. Its provenance must not
be described as a Minerva-hardware run unless a separate Minerva execution is
actually performed and validated.

## Minerva production

### Preflight

Before Phase 18 production:

1. approve and freeze this plan and the Phase 18 YAML;
2. require the Phase 12 production status to be
   <code>validated_complete</code>;
3. independently validate every required Phase 12 and inherited hash;
4. pass Phase 18 synthetic tests and the complete local real-data validation;
5. reproduce all frozen run-grid counts;
6. verify the one-task dry-run graph and dependency on
   <code>global:kda</code>;
7. freeze the Git revision, R environment, scientific fingerprint, and
   deterministic seeds; and
8. stop if an existing final Phase 18 directory is present.

### Command template

~~~bash
cd /sc/arion/work/zhuane01/alzheimer

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript tests/test_phase18_key_driver_selection.R

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase key_driver_selection \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase key_driver_selection

Rscript tests/test_phase18_key_driver_selection.R \
  --validate-output results/minerva_production/18_key_driver_selection
~~~

The output validator reads the frozen expected counts, execution labels, and
<code>validated_complete</code> status from the Phase 18 configuration; they
are not supplied as separate command-line overrides.

### Checkpointing and resume

Checkpoint production work by:

~~~text
stage
broad network
run ID
sensitivity type
leave-one-fine-cell-type-out replicate
~~~

The resume fingerprint includes:

- required Phase 12 output hashes;
- Phase 09 annotation hash;
- fKDA source hash;
- all network hashes;
- Phase 18 plan, YAML, and scientific-script hashes;
- ACAT implementation identity;
- pipeline and execution settings affecting computation;
- R environment lockfile; and
- randomization settings.

An incompatible fingerprint starts a new scratch tree. It must not reuse
scientific shards from another fingerprint.

### Atomic publication order

~~~text
build and checkpoint in scratch
-> finish all primary and sensitivity stages
-> write scientific files in staging
-> write checks
-> write artifact manifest
-> independently validate staging
-> write final status last
-> atomically rename staging to the final production directory
~~~

No partial result is published as final.

## Required blocking checks

### Upstream identity and scope

- Phase 12 status is <code>validated_complete</code>.
- All required Phase 12 and inherited artifact hashes match.
- The Phase 12 grid contains exactly 1,782 rows.
- The primary directional grid contains exactly 648 rows.
- Phase 12-eligible primary directional runs equal 295.
- Included effective-query-size-at-least-10 runs equal 161.
- Included network counts equal 21, 97, 28, 6, 6, 2, and 1 in the frozen
  network order.
- No secondary group or AD-both row enters primary computation.

### Query, background, network, and reconstruction

- Every included query and background reproduces Phase 12 membership.
- Every induced network reproduces the Phase 12 counts.
- Every background gene has exactly one explicit or implicit row per included
  run.
- No gene outside the background receives a P value.
- Every original significant Phase 12 result reproduces before correction.
- No duplicated run × gene key exists.

### Cases and self-exclusion

- Every usable row has exactly one case.
- Case 3 contains no effective query member.
- Case 1 count subtraction is exactly one in all four fields.
- No self-excluded count is negative or impossible.
- Case 1 best layers reproduce from the corrected layer table.
- Cases 2 and 3 preserve reconstructed original statistics.

### Multiplicity and filtering

- Run-level BH uses exactly the explicit candidate family.
- Implicit nulls retain P = 1 and q = 1.
- Conservative support reproduces from named component fields.
- Coverage numerators never exceed denominators.
- Coverage does not depend on P-value significance.
- ACAT uses all usable P values, including P = 1.
- Primary ACAT never converts missing values to P = 1.
- Aggregate BH families reproduce within broad network.
- Every candidate status reproduces from its three gate components.
- Filter 1 reports all 648 run slots as exactly included or excluded.
- Filter 2 test-status counts reconcile with the candidate-test matrix.
- Native filter counts retain their declared counting units.
- Every compatible sequential funnel row satisfies input = pass + fail.
- Every Filter 3–5 next-step input equals the preceding step's pass count.
- The final funnel count equals the candidate-table row count.
- Independent gate counts reproduce directly from aggregate component fields.

### Ranking and display

- Rankings are independent within each network × case.
- No cross-case rank exists.
- Rank order is ACAT q, raw ACAT P, then symbol.
- Every candidate has exactly one rank.
- No noncandidate has a primary candidate rank.
- No network × case displays more than five genes.
- No empty display slot is filled by a noncandidate.
- All 27 declared network × case lists have ranked rows or exactly one
  explicit no-result status row.
- Every displayed gene reproduces from the authoritative candidate rank.

### Stability, outputs, and provenance

- Every assessable leave-one-fine-cell-type-out result reproduces.
- Missingness, coverage, and aggregation sensitivities are complete.
- All declared files exist and no undeclared final file exists.
- Every table has the declared schema and unique keys.
- Every artifact hash validates.
- Pilot provenance is absent from production.
- Final status is written only after all blocking checks pass.

## Interpretation rules

### Allowed wording

For a passing Case 1 candidate:

> This core mitochondrial gene was itself part of the AD-associated
> mitochondrial query and retained enrichment for other query genes after its
> self-overlap was removed.

For a passing Case 2 candidate:

> This core mitochondrial gene was not part of the run-specific query and
> showed query-independent network enrichment for the AD-associated
> mitochondrial program.

For a passing Case 3 candidate:

> This gene lies outside the 1,136-gene core MitoCarta inventory and showed
> network evidence connecting it to the AD-associated mitochondrial program.

For top-five reporting:

> The gene ranked among the five smallest aggregate ACAT q values among
> passing candidates in its broad network and case.

### Prohibited wording

Do not state that Phase 18 proves:

- causal regulation;
- direct molecular interaction;
- disease mechanism;
- mitochondrial functional impairment;
- cell-type specificity based only on separate significance;
- therapeutic efficacy; or
- replication in an independent cohort.

### Negative and inconclusive results

A result in which no gene passes the final candidate gate is valid. Report:

- whether no gene passed because of aggregate evidence, conservative support,
  coverage, or testability;
- the number of exploratory and aggregate-only rows;
- networks with too few included runs for meaningful stability; and
- all sensitivity disagreements.

## Plain-language glossary

| Term | Meaning in Phase 18 |
|---|---|
| Run | One fine cell type × group × direction analysis using its matching broad network |
| Query | Core mitochondrial genes altered in AD for one run |
| Background | Genes that could be evaluated in the run-specific induced network |
| Candidate driver | A gene whose network neighborhood is tested for query enrichment |
| Explicit test | A candidate neighborhood evaluated by fKDA |
| Implicit zero-overlap | A background gene with no explicit query-neighborhood evidence, assigned P = 1 |
| Self-overlap | The automatic Case 1 overlap contributed by the driver itself |
| Fold enrichment | Query concentration in the neighborhood divided by query concentration in the full background |
| P value | Raw statistical evidence for one test |
| q value | P value adjusted for testing many candidates |
| Coverage | Usable tests divided by eligible case-runs |
| Conservative support | One run passing query-size, other-overlap, fold-enrichment, and run-level q requirements |
| ACAT | A method that combines run-level P values into one aggregate gene-level P value |
| Recurrence | Conservative supporting runs divided by usable tested runs |
| Fine-cell breadth | Number of distinct fine cell types with conservative support |
| Sensitivity analysis | A prespecified alternative analysis used to check robustness |

## Completion criteria

Phase 18 is complete only when:

1. the plan, configuration, cases, filters, families, and ranking are approved
   and frozen;
2. Phase 12 and every inherited dependency validate independently;
3. deterministic unit and integration tests pass;
4. the complete local real-data execution passes and its execution venue is
   recorded truthfully;
5. production reconstructs all required Phase 12 evidence;
6. all 648 structural slots and 161 included runs reconcile;
7. every aggregate has a terminal status;
8. every candidate has an independent within-case rank;
9. all 27 network × case top-five lists obey the display and empty-result
   rules;
10. native-unit, sequential, and independent-gate filter counts reconcile
    with their authoritative source tables;
11. all stability and sensitivity outputs are complete;
12. all output-only checks, schemas, hashes, and provenance pass; and
13. the final production bundle is published atomically.

Production completion is <code>validation_status = validated_complete</code>
whether Phase 18 identifies many candidates, few candidates, or no candidates.

## Implementation checklist

### Freeze

- [ ] Approve the permanent Phase 18 assignment and reserve Phases 16 and 17.
- [ ] Approve the six primary groups and two separate directions.
- [ ] Approve the effective-query minimum of 10.
- [ ] Approve the three cases and Case 1 self-exclusion.
- [ ] Approve run-level and aggregate BH families.
- [ ] Approve coverage ≥0.80 and candidate q ≤0.05.
- [ ] Approve the requirement for at least one conservative supporting run.
- [ ] Approve ACAT and its numerical boundary behavior.
- [ ] Approve sorting by ACAT q within case and the top-five cap.
- [ ] Approve the native-unit and sequential filter-count contract.
- [ ] Approve stability and sensitivity specifications.
- [ ] Freeze schemas, seeds, software, code revision, and hashes.

### Implement

- [ ] Add the Phase 18 YAML, scientific script, and tests.
- [ ] Register <code>global:key_driver_selection</code> after
  <code>global:kda</code>.
- [ ] Implement Phase 12 and Phase 09 preflight validation.
- [ ] Implement the 648-slot run manifest and 161-run inclusion checks.
- [ ] Implement exact query, background, and induced-network reconstruction.
- [ ] Implement complete explicit and implicit candidate-test matrices.
- [ ] Implement pre-correction Phase 12 reproduction.
- [ ] Implement Case 1 self-exclusion and layer reselection.
- [ ] Implement run-level BH, conservative support, and coverage.
- [ ] Implement ACAT, aggregate BH, and terminal statuses.
- [ ] Implement within-case ranks and top-five flags.
- [ ] Implement all-27-list top-five status reporting.
- [ ] Implement native-unit, sequential, and independent-gate filter counts.
- [ ] Implement stability, missingness, coverage, aggregation, and degree
  sensitivities.
- [ ] Implement checkpointing, atomic publication, and output-only validation.

### Validate and execute

- [ ] Pass deterministic synthetic tests locally.
- [x] Validate the complete local real-data execution and promote it with
  explicit user authorization.
- [ ] Reconfirm the frozen Phase 12 production identity.
- [ ] Inspect the one-task dry run.
- [ ] Execute or resume production from a compatible fingerprint.
- [ ] Validate all run, case, test, aggregate, and rank keys.
- [ ] Validate all top-five list statuses and filter-funnel identities.
- [ ] Verify every declared output, schema, row count, and hash.
- [ ] Publish <code>key_driver_status.tsv</code> last.

### Locked result review

- [ ] Review terminal statuses before viewing top-five figures.
- [ ] Keep the three cases separate in all tables and figures.
- [ ] Report ACAT q as the ranking variable.
- [ ] Report coverage numerator and denominator, not only the fraction.
- [ ] Report both sequential attrition and independent gate failures.
- [ ] Label every filter count with its counting unit.
- [ ] Report recurrence, breadth, fold enrichment, and stability as
  annotations.
- [ ] Label aggregate-only and exploratory rows accurately.
- [ ] Report networks with limited run or fine-cell breadth.
- [ ] Use only the allowed interpretation language.
- [ ] Record any requested deviation as a plan amendment before rerunning.
