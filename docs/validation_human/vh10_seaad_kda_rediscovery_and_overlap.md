# VH10 SEA-AD Key-Driver Rediscovery and ROSMAP Overlap

**Status:** proposed; not yet implemented or executed  
**Planned code root:** `scripts/validation_human/`  
**Planned result root:** `results/validation_human/10_seaad_kda_rediscovery/`  
**ROSMAP reference:** Phase 18 candidates frozen by VH09

## 1. The short answer

Yes. The central purpose of VH10 should be:

1. use the SEA-AD DEG signatures to produce an independent set of top key
   drivers;
2. freeze that SEA-AD set before looking at the ROSMAP selected genes; and
3. measure how much the SEA-AD set overlaps the ROSMAP Phase 18 set.

```text
SEA-AD VH08 DEGs
        |
        v
SEA-AD KDA on the frozen broad-cell networks
        |
        v
SEA-AD candidate selection and top-five lists
        |
        v
freeze and checksum the SEA-AD lists
        |
        +------------------------------+
                                       |
VH09 frozen ROSMAP Phase 18 lists -----+--> overlap analysis
```

The ROSMAP selected list must not be used to generate or rank the SEA-AD
candidates. It is opened only after the SEA-AD top lists have been written and
checksum-frozen.

## 2. Why VH10 should not begin by scoring the 47 ROSMAP units

VH09 froze 47 ROSMAP Phase 18 candidate units, representing 25 unique genes.
A candidate unit is:

```text
broad_network + key_driver + case_id
```

Testing only those 47 units in SEA-AD would be a targeted validation analysis.
It could tell us whether a known ROSMAP candidate has SEA-AD support, but it
could not produce an independent SEA-AD top list because the search was
restricted to the ROSMAP winners.

VH10 therefore searches all assessable key drivers in each SEA-AD broad-cell
network first. A targeted analysis of the 47 frozen units can be retained as a
later sensitivity phase, but it is not the primary VH10 analysis.

## 3. What is independent and what is shared

The SEA-AD evidence is independent at the human cohort and expression-data
level:

- SEA-AD donors, counts, pseudobulk profiles, and DEGs come from VH00-VH08;
- no ROSMAP DEG or selected-gene identity enters SEA-AD candidate discovery;
- the SEA-AD list is frozen before the ROSMAP comparison.

The network scaffold is deliberately shared. VH10 applies SEA-AD signatures to
the same broad-cell Bayesian networks with the same frozen `fKDA.R` engine and
the same current Phase 18 v2 selection core. This makes the key-driver results
comparable with Phase 18.

Consequently, VH10 is an **independent-cohort rediscovery on a shared frozen
network scaffold**. It is not a de novo SEA-AD network reconstruction. That
distinction must be stated in the final interpretation.

The current, two-class Phase 18 v2 analysis is the scientific authority for the
comparison and selection rules. VH10 freezes these current files directly:

- `config/phase18_key_driver_selection.yml`;
- `scripts/18_key_driver_selection.py`; and
- `docs/phase_18_key_driver_selection/key_driver_selection_process.md`.

Their SHA-256 values are already frozen by VH09. The Phase 18 archive is not a
selection authority: in particular, its historical three-case manifest is
obsolete because current Phase 18 has only `mt_driver` and `non_mt_driver`.
The archived input inventory may be used only to corroborate the exact network,
Phase 09 annotation, and `fKDA.R` identities and checksums.

Before the SEA-AD lists are frozen, the Phase 18 process document is a
checksum-only conformance artifact because its explanatory final section names
the selected genes. VH10A-VH10C may parse the current configuration and code,
but they must not parse a candidate-bearing Phase 18 result or documentation
table. No Phase 18 identity may be used to form, score, gate, or rank a SEA-AD
candidate.

The legacy Phase 12 directory is not used as a source of candidates. Some
technical assets originally used upstream of Phase 18 are nevertheless
necessary: the exact broad-cell network files, the Phase 09 annotation, and
the upstream `fKDA.R` engine whose saved returns current Phase 18 reconstructs.
VH10 copies their identities and checksums into its own configuration and fails
if they do not match.

### Phase 18 selection-conformance contract

VH10 is a cohort adapter around the current Phase 18 v2 decision procedure,
not a new key-driver selector. Except for
`minimum_effective_query_genes = 3` instead of 10, it must preserve all
selection-bearing behavior:

| Component | Behavior frozen from current Phase 18 |
|---|---|
| Query universe | Core-MitoCarta protein genes and separate `AD_up_mito`/`AD_down_mito` directions |
| Run evidence | Same induced-network background, explicit candidate family, directed layer tests, best-layer rule, hypergeometric statistic, and within-run BH family |
| Self-exclusion | Same conditional correction for an MT driver that belongs to its query, including best-layer reselection and final within-run BH |
| Driver classes | Exactly `mt_driver` and `non_mt_driver`; query membership never creates a class |
| Cross-run evidence | Same union-of-backgrounds candidate universe, explicit/implicit/missing states, equal-weight ACAT implementation, and coverage denominator |
| Candidate decision | Same 0.80 coverage, one conservative-supporting-run, and aggregate-q-at-most-0.05 gates |
| Aggregate correction | Same BH family within each broad network across both driver classes |
| Ranking | Same aggregate q, aggregate p, alphabetical-symbol order and maximum of five without backfilling |

SEA-AD necessarily has different donors, DEG values, tested-gene sets, and run
identities. Its primary grid also has one pooled broad-cell contrast per
network rather than Phase 18's fine-cell-type by sex/APOE grid. Those are
cohort-input differences, not permission to change the selection mathematics
or thresholds. Any additional statistical departure requires a protocol
amendment and a separately labeled analysis.

## 4. Primary versus secondary SEA-AD evidence

The headline SEA-AD top lists use the seven pooled primary VH08 contrasts:

```text
Dementia versus No dementia, once in each broad cell population
```

Each contrast creates an `AD_up_mito` and an `AD_down_mito` query, so the
primary grid has 14 directional slots.

The 42 sex/APOE secondary contrast slots create 84 additional directional
slots. Only 20 secondary contrasts were estimable in VH08; the other 22, or 44
directional slots, remain explicitly `not_estimable`.

Secondary contrasts are not pooled with the primary contrast when selecting
the headline SEA-AD top drivers. They are subsets of the same donor cohort and
therefore are not independent of the pooled analysis. Their KDA results are
reported as supportive or exploratory evidence after the primary lists are
frozen.

## 5. Important limitation: SEA-AD may not produce lists for all seven networks

Phase 18 required at least 10 effective query genes after intersection with the
tested-gene background and network. That cutoff would leave most SEA-AD
directions untested. VH10 therefore uses a lower minimum of **three effective
query genes**, matching the original Phase 12 KDA run-eligibility rule. Queries
with 3-9 effective genes are runnable and enter the primary SEA-AD analysis,
but are flagged `small_query` because their enrichment estimates can be
unstable. Effective query size must be shown with every result and top list.
Three is also the smallest query that lets an in-query MT driver satisfy the
later conservative-support rule using two other query genes after its
guaranteed self-overlap is removed.

This is a prespecified departure from the Phase 18 run-scope rule, not a claim
that a three-gene query is equivalent to a ten-gene query. Results restricted
to queries with at least 10 effective genes are reported separately as a
Phase 18-sized sensitivity analysis whenever that subset is assessable.

The shared statistical part of the source-signature DEG rule is:

```text
within-contrast BH FDR < 0.05
AND abs(logFC) > log2(1.3)
```

ROSMAP Phase 18 inherited one additional upstream `paper_deg` condition from
Phase 08: detection in at least 10% of AD or NCI nuclei. SEA-AD VH08 does not
contain directly comparable per-nucleus detection fractions; it prespecifies
its tested universe with edgeR `filterByExpr` instead. VH10 therefore uses the
VH08 tested-gene status plus the shared FDR/effect rule and does not invent a
post hoc 10% analog. This is a cohort-specific query-input difference, not a
change to the Phase 18 key-driver selection engine.

Applying that rule and then the exact induced-network background gives these
planning counts:

| Broad network | AD-up before network | Effective AD-up | AD-down before network | Effective AD-down | Post-intersection status |
|---|---:|---:|---:|---:|---|
| Astrocytes | 10 | 9 | 1 | 0 | Up is `small_query` |
| Excitatory neurons | 20 | 12 | 3 | 1 | Up is `phase18_sized` |
| Inhibitory neurons | 5 | 5 | 0 | 0 | Up is `small_query` |
| Microglia | 14 | 10 | 2 | 0 | Up is `phase18_sized` |
| OPCs | 0 | 0 | 0 | 0 | No eligible direction |
| Oligodendrocytes | 9 | 8 | 2 | 2 | Up is `small_query` |
| Vasculature cells | 2 | 2 | 1 | 0 | No eligible direction |

These values were cross-checked by joining `approved_symbol` to the frozen
Phase 18 core-MitoCarta annotation and inducing each frozen network on the
corresponding tested-gene set. VH10 must reproduce them as blocking input-QC
assertions rather than treating them as hard-coded analytical inputs.

Five of the 14 primary directional slots are therefore runnable at the
three-gene minimum: Astrocyte up, Excitatory-neuron up, Inhibitory-neuron up,
Microglia up, and Oligodendrocyte up. Only Excitatory-neuron up and Microglia up
meet the Phase 18 ten-gene cutoff after network intersection. Lowering the
minimum from 10 to 3 adds three runnable primary queries while leaving all
down-direction primary queries below the minimum.

This means VH10 must not promise 14 complete top-five lists, one for each of
seven networks and two driver classes. For a network with no eligible primary
direction, preserve the Phase 18 list status
`not_testable_no_included_runs`. A testable list with no gene passing all three
gates is `no_passing_candidate`; it is not an empty list interpreted as failure
and is never filled with weak genes. The Phase 18
`not_testable_no_eligible_case_runs` status is retained for the defensive case
where an included network has no record for one driver class.

The effective post-intersection query-size tiers are therefore:

- effective query size at least 10: eligible and labeled `phase18_sized`;
- effective query size 3-9: eligible and labeled `small_query`;
- effective query size below 3: `not_estimable`.

Both eligible query-size tiers are tested. They feed two explicitly named
analysis tiers: `primary_min3` includes all eligible queries, whereas
`phase18_sized_sensitivity` includes only `phase18_sized` queries. The report
must show whether each primary selection or overlap depends on a small query
and must never pool the two analysis tiers. VH10 does not add an FDR-only or
effect-size-relaxed query branch; either would be another departure from Phase
18 and would require a separate protocol amendment.

## 6. Detailed process

### VH10A - Freeze inputs and build SEA-AD KDA queries

#### Inputs

| Input | Purpose |
|---|---|
| `results/validation_human/08_deg/status.tsv` | Require VH08 `validated_complete` |
| `results/validation_human/08_deg/seaad_primary_deg_complete.tsv.gz` | Seven pooled broad-cell DEG tables |
| `results/validation_human/08_deg/seaad_secondary_deg_complete.tsv.gz` | Twenty completed secondary DEG tables |
| `results/validation_human/08_deg/seaad_deg_contrast_manifest.tsv` | Preserve all 49 contrast slots and their eligibility status |
| `results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz` | Apply the exact Phase 18 core-MitoCarta and driver-class definition |
| `config/phase18_key_driver_selection.yml` | Freeze current two-class selection constants |
| `scripts/18_key_driver_selection.py` | Freeze current reconstruction, self-exclusion, ACAT, BH, and ranking behavior |
| `docs/phase_18_key_driver_selection/key_driver_selection_process.md` | Checksum-only conformance artifact before the SEA-AD freeze; never parse its candidate-bearing list |
| Archived Phase 18 `key_driver_input_inventory.tsv` | Corroborate only the network, Phase 09 annotation, and `fKDA.R` paths and checksums, not current selection semantics |
| Seven Phase 18-recorded broad-cell network files | Shared frozen network scaffold |
| `scripts/NetWeaver/fKDA.R` | Frozen `call_key_drivers()` implementation |

The canonical Phase 18 return table and the VH09 selected/passing candidate
tables are deliberately **not** inputs to VH10A, VH10B, or VH10C.

#### Query construction

Within each completed SEA-AD contrast and matching broad network:

```text
tested_symbols
    = unique nonmissing approved symbols from rows with test_status == tested

induced_network
    = frozen network edges whose source and target are both in tested_symbols

background
    = unique source and target nodes in induced_network

candidate AD_up_mito query before network intersection
    = unique tested symbols with Phase 18 is_core_mito == TRUE,
      FDR < 0.05,
      abs(logFC) > log2(1.3),
      and logFC > 0

candidate AD_down_mito query before network intersection
    = unique tested symbols with Phase 18 is_core_mito == TRUE,
      FDR < 0.05,
      abs(logFC) > log2(1.3),
      and logFC < 0

effective directional query
    = candidate directional query intersected with background
```

Gene matching maps SEA-AD `approved_symbol` to the frozen Phase 18 current
symbol and excludes missing symbols. The Phase 18 `is_mitocarta3` value defines
`is_core_mito`; the VH08 `is_mitocarta` field is a QC cross-check rather than an
independent query definition. Any annotation disagreement that changes query
membership is blocking.

Duplicate source rows use set semantics, matching the Phase 18 query builder:
a tested symbol is recorded once, and a directional query contains the symbol
if any mapped source row passes that exact directional DEG rule. Conflicting
source-feature logFC, FDR, or direction values do not override those any-pass
set semantics. Only conflicting frozen gene-identity or class annotations that
could change the current-symbol mapping or `is_core_mito` assignment are
blocking rather than silently resolved.
Every effective query must be a subset of its recorded induced-network
background.

The run manifest contains the complete structural grid:

```text
49 contrast slots x 2 directions = 98 directional slots
```

Every slot receives a terminal eligibility status. Unavailable contrasts and
small or empty queries are not silently omitted. Every eligible slot is also
assigned `phase18_sized` or `small_query` from its effective post-intersection
query size. Only eligible, successfully completed runs enter selection.
Both `completed_significant` and `completed_no_significant` runs are included;
run-level significance is not an inclusion criterion.
Ineligible, failed, and non-estimable slots remain manifest/QC records and
never enter an ACAT vector, `eligible_run_count`, or coverage denominator.

#### VH10A outputs

- `seaad_kda_run_manifest.tsv`: all 98 directional slots, source status,
  pre-network and effective query sizes, query-size tier, and terminal
  eligibility;
- `seaad_kda_signature_members.tsv.gz`: exact query genes for every runnable
  slot;
- `seaad_kda_background_members.tsv.gz`: exact tested/network background for
  every runnable slot;
- input and checksum checks.

### VH10B - Run SEA-AD KDA and retain the complete test table

For every eligible primary query with at least three effective genes, call
`call_key_drivers()` using the Phase 18-recorded settings:

| Parameter | Frozen value |
|---|---|
| Network input | Run-specific induced network from VH10A |
| `nLayerToTest` | 3 |
| `nLayersToExpand` | 0 |
| `bg.size` | Number of genes in the induced-network background |
| `directed` | `TRUE` |
| `reduce.within.nlayer` | 2 |
| `fdr` | 0.05 |
| `p.correction.method` | BH |
| `return.overlap` | `TRUE` |

The same operation is run separately for each eligible secondary query, but
those results go to the secondary-support branch.

#### Exact Phase 18 run reconstruction

VH10 must reuse the selection-bearing Phase 18 helpers directly or extract them
into a shared module used by both phases. It must not introduce an independent
ACAT, BH, enrichment, self-exclusion, or ranking implementation. Any shared-
module refactor must leave the current Phase 18 unit and canonical-output tests
unchanged and passing.

`call_key_drivers()` returns only genes passing its original run-level FDR
filter. Phase 18 selection reconstructs all explicit tests before using the
results, and VH10 must use the same reconstruction:

1. Starting from the effective query, form the explicit candidate family from
   genes reached within three undirected layers of the query in the induced
   network.
2. For each candidate with an evaluable neighborhood, test cumulative directed
   downstream neighborhoods at layers 1, 2, and 3.
3. At each layer, calculate the same upper-tail hypergeometric p-value from
   overlap `q`, neighborhood size `m`, query size `k`, and background size `M`.
   Calculate fold enrichment with the same two-decimal rounding behavior.
4. Select the layer with the smallest log p-value, breaking an exact tie in
   favor of the lower layer.
5. Apply BH across every explicit candidate in that run, including
   nonsignificant and explicit zero-overlap tests. The reconstructed original
   q-value-at-most-0.05 subset and its published fields must reproduce the
   `call_key_drivers()` return exactly.

Original `call_key_drivers()` significance, query/root flags, and
`global.Keydriver` are provenance fields, not selection gates.

For a candidate that is both a core-MitoCarta driver and a member of the run's
query, apply the exact Phase 18 self-exclusion at every tested layer: subtract
one from `q`, `m`, `k`, and `M`; recompute the hypergeometric p-value and fold
enrichment; and reselect the best layer. The final best layer may therefore
differ from the original best layer. After all conditional corrections,
recompute BH across the same complete explicit-candidate family using the final
raw p-values.

The stored evidence retains original and final layers, counts, raw p-values,
and within-run q-values. Candidate selection uses the final raw p-value.
Conservative support uses the final result and is true only when there are at
least two other query genes, final fold enrichment is strictly greater than
one after Phase 18's rounding, and final run q-value is at most 0.05.

The current canonical Phase 18 `call_key_driver_returns.tsv` persists explicit
tests only; implicit and missing states are constructed in memory during
aggregation. VH10 preserves that explicit call-return table and additionally
writes a richer aggregation evidence matrix with these states:

- `explicit_test` or `explicit_zero_overlap`: in the explicit family, using its
  final raw p-value and final run q-value;
- `implicit_zero_overlap`: in the run background but outside the explicit
  family, usable with p = q = 1; and
- `absent_from_background`: part of the network-level candidate universe but
  absent from this run background, unusable and missing rather than p = 1.

Non-estimable structural slots have no synthetic evidence rows and do not enter
aggregation.

Candidate class is fixed exactly as in current Phase 18:

- `mt_driver`: Phase 18 core-MitoCarta membership is true;
- `non_mt_driver`: Phase 18 core-MitoCarta membership is false or absent.

Query membership changes only whether self-exclusion is required; it never
creates a third driver class.

#### VH10B outputs

- `seaad_kda_call_returns.tsv.gz`: all explicit pre-FDR gene-by-run tests in the
  current Phase 18 call-return model;
- `seaad_kda_candidate_tests.tsv.gz`: richer gene-by-run aggregation evidence
  matrix containing explicit, implicit, and missing states;
- `seaad_kda_significant_returns.tsv`: the subset returned by
  `call_key_drivers()`;
- `seaad_kda_secondary_candidate_tests.tsv.gz`: separate secondary evidence;
- run-level QC and reconstruction checks.

### VH10C - Select and freeze the independent SEA-AD top drivers

All eligible primary runs, including those labeled `small_query`, enter the
`primary_min3` selection. Candidate summaries and top lists retain each
contributing run's effective query size and a flag indicating whether the
result depends on any 3-9-gene query. The same aggregation and selection are
also calculated for `phase18_sized_sensitivity` using only `phase18_sized`
runs when at least one such run is available. The sensitivity tier recomputes
its candidate universe, denominators, ACAT values, BH correction, candidate
decisions, ranks, and top-five lists from that run subset; it is not obtained
by filtering or reranking the `primary_min3` winners.

Within each analysis tier and broad network:

1. define the aggregate candidate universe as the union of the effective
   backgrounds from all included runs in that network;
2. assign each gene its one fixed `mt_driver` or `non_mt_driver` class, making
   the candidate-unit key `broad_network + key_driver + case_id`;
3. create one equal-weight run vector for every candidate: use the final raw
   p-value for an explicit test, p = 1 for an implicit test, and missing for a
   gene absent from the run background;
4. calculate coverage as explicit plus implicit usable runs divided by all
   included runs in that network;
5. only for candidates with coverage at least 0.80, combine the usable final
   raw p-values with the exact Phase 18 `acat_combine()` implementation and its
   boundary handling; primary ACAT omits missing values;
6. within the broad network, apply BH jointly to all and only
   coverage-qualified candidate units with a reportable ACAT p-value, across
   both driver classes and before filtering on conservative support;
7. require all three Phase 18 gates:
   - coverage at least 0.80;
   - at least one conservative supporting run;
   - aggregate ACAT q-value at most 0.05;
8. label only units passing all three gates as `driver_candidate`; and
9. rank passing candidates separately within each
   `broad_network + case_id` list by:
   - smaller aggregate q-value;
   - smaller aggregate p-value;
   - alphabetical gene symbol;
10. retain ranks 1-5.

The Phase 18 missing-as-one ACAT and q-value are retained as sensitivity fields
only. They do not replace the primary missing-omission rule and do not gate
candidate selection. VH10 preserves the Phase 18 terminal candidate-status
semantics; in particular, `aggregate_only` and `exploratory` are not
`driver_candidate` results and cannot enter a top-five list.

Five is a maximum, not a quota. No nonsignificant candidate is used to fill an
incomplete list.

Because SEA-AD has at most two primary directional runs in a network, and often
only one eligible direction, its aggregation has much less recurrence
information than ROSMAP Phase 18. VH10 applies the same gates for comparability,
but the report must show each list's eligible-run count and must not describe a
one-run selection as broadly recurrent evidence.

Phase 18 leave-one-fine-cell-type-out stability is descriptive and is not a
candidate gate. It is not assessable for SEA-AD's one pooled broad-cell primary
contrast per network. VH10 records `tier_not_assessable` rather than replacing
it with a new stability rule or allowing secondary contrasts to affect primary
selection.

VH10C writes the primary SEA-AD top list, the Phase 18-sized sensitivity list,
and their SHA-256 checksums before any VH09 candidate file is read. This is the
boundary that makes the later overlap comparison an honest rediscovery
analysis.

#### VH10C outputs

- `seaad_kda_candidate_summary.tsv`: one row per SEA-AD candidate unit and
  analysis tier;
- `seaad_kda_top5.tsv`: independently selected SEA-AD units for the primary and
  Phase 18-sized sensitivity tiers, including explicit empty/not-testable list
  rows and never pooling tiers;
- `seaad_kda_secondary_support.tsv`: secondary evidence kept separate from
  selection;
- `seaad_kda_selection_freeze.tsv`: row counts, list counts, file checksum, and
  freeze timestamp.

### VH10D - Unblind the ROSMAP list and calculate overlap

Only after VH10C passes its freeze checks does VH10D run the full Phase 18
compatibility gate. With the minimum restored to 10 and the frozen ROSMAP
Phase 18 inputs, the shared selection core must:

- pass `tests/test_phase18_key_driver_selection.py`;
- reproduce the exact keys and all selection-bearing original/final fields of
  the 95,557 canonical explicit gene-by-run rows from 161 included runs,
  including the exact 1,641 original significant returns;
- reconstruct all 47,590 gene-by-network units in the union-of-backgrounds
  aggregate universe, including implicit-only units, and apply aggregate BH to
  the exact coverage-qualified subset of that full universe;
- reproduce the 10,433 candidate units represented by at least one explicit
  canonical call-return row, with exact coverage, aggregate p/q, terminal
  status, rank, and top-five fields under a deterministic projection checksum;
  and
- reproduce the 78 `driver_candidate` units, 47 top-five units, and their exact
  candidate keys and ranks, not only their counts.

This compatibility run produces checks, checksums, and the membership/coverage
artifact needed to define the overlap universe. It cannot feed a Phase 18 gene
identity, p-value, status, or rank back into the already frozen SEA-AD
selection. A mismatch is blocking and prevents overlap analysis.
The post-freeze gate may read the frozen Phase 12 run and background-membership
artifacts solely to reconstruct the Phase 18 aggregate universe and validate
current Phase 18 behavior.

After that gate passes, VH10D reads:

```text
results/validation_human/09_rosmap_kda_candidates/
    phase18_selected_candidate_units.tsv
```

The strict match key is:

```text
broad_network + key_driver + case_id
```

For overlap testing, define the universe separately for every analysis tier,
broad network, and driver class. First intersect the full SEA-AD
union-of-backgrounds candidate universe with the reconstructed 47,590-unit
Phase 18 union-of-backgrounds universe on the strict key. Then retain only
units with coverage of at least 0.80 and a reportable primary ACAT p-value in
both analyses. This coverage-qualified intersection is the common assessable
universe `U`. The 10,433 explicitly represented Phase 18 units are not used as
a shortcut for `U`, because that would omit implicit-only p = 1 records that
participated in the Phase 18 aggregate BH family.

Every ROSMAP and SEA-AD selected-set size, intersection, Jaccard denominator,
and hypergeometric population/sample count is restricted to `U`. The
reconstructed Phase 18 universe membership and coverage fields are saved and
checksummed after the SEA-AD freeze.

Network-specific matching is primary because a gene selected in astrocytes
and the same gene selected in excitatory neurons are different Phase 18
candidate units. An overlap of unique gene symbols that ignores network is
reported only as a secondary descriptive metric.

For each analysis tier and assessable broad-network and driver-class list,
report:

- number selected by ROSMAP Phase 18 within the common testable universe;
- number selected independently by SEA-AD;
- exact candidate-unit intersection count;
- SEA-AD precision: intersection divided by SEA-AD selected units;
- ROSMAP recall: intersection divided by testable ROSMAP selected units;
- Jaccard index;
- hypergeometric overlap p-value using the common assessable candidate universe;
- the identities and ranks of shared, ROSMAP-only, and SEA-AD-only units.

Each frozen ROSMAP candidate unit receives one of these statuses:

| Status | Meaning |
|---|---|
| `rediscovered_top5` | Selected in both Phase 18 and the SEA-AD top list |
| `seaad_driver_candidate_not_top5` | Passed SEA-AD candidate gates but ranked below five |
| `tested_not_selected` | Was testable in SEA-AD but failed one or more selection gates |
| `not_testable` | No included SEA-AD run or the unit was outside coverage-qualified common universe `U` |

`not_testable` units are excluded from the replication denominator. They must
not be counted as negative replications. SEA-AD-only candidates are new
hypotheses; they are not failures of ROSMAP validation.

#### VH10D outputs

- `phase18_selection_parity_checks.tsv`: current-v2 unit, output-contract,
  count, candidate-key, and rank parity checks;
- `phase18_candidate_universe.tsv.gz`: reconstructed full Phase 18
  union-of-backgrounds membership and coverage fields used to define `U`;
- `rosmap_seaad_candidate_overlap.tsv`: unit-level match and testability status,
  separated by analysis tier;
- `rosmap_seaad_overlap_summary.tsv`: per-tier, per-network/class, and overall
  metrics;
- `rosmap_seaad_gene_only_overlap.tsv`: secondary network-agnostic comparison;
- final checks, artifact checksums, and `status.tsv`.

## 7. Proposed repository end state

### New code, when VH10 is implemented

```text
scripts/validation_human/
├── seaad_kda_validation_config.yml
├── 10_prepare_seaad_kda_inputs.R
├── 10_run_seaad_kda.R
└── 10_select_and_compare_kda_candidates.py

tests/
└── test_vh10_phase18_selection_parity.py
```

The exact split can change during implementation, but discovery/freeze and
ROSMAP unblinding must remain separate executable stages. The parity test must
exercise the same shared selection core used for SEA-AD; testing the untouched
Phase 18 script alone is necessary but not sufficient.

### New results, when VH10 is executed

```text
results/validation_human/10_seaad_kda_rediscovery/
├── seaad_kda_run_manifest.tsv
├── seaad_kda_signature_members.tsv.gz
├── seaad_kda_background_members.tsv.gz
├── seaad_kda_call_returns.tsv.gz
├── seaad_kda_candidate_tests.tsv.gz
├── seaad_kda_significant_returns.tsv
├── seaad_kda_candidate_summary.tsv
├── seaad_kda_top5.tsv
├── seaad_kda_secondary_candidate_tests.tsv.gz
├── seaad_kda_secondary_support.tsv
├── seaad_kda_selection_freeze.tsv
├── phase18_selection_parity_checks.tsv
├── phase18_candidate_universe.tsv.gz
├── rosmap_seaad_candidate_overlap.tsv
├── rosmap_seaad_overlap_summary.tsv
├── rosmap_seaad_gene_only_overlap.tsv
├── checks.tsv
├── artifacts.tsv
└── status.tsv
```

There is no `model_objects/` directory in this proposal. KDA uses fixed network
files and table-based enrichment tests rather than fitted edgeR model objects.

### Added, changed, removed, and preserved

- **Added now:** this process document only.
- **Added during implementation:** the isolated VH10 scripts, configuration,
  parity test, and `10_seaad_kda_rediscovery` outputs listed above.
- **Changed:** no existing ROSMAP or SEA-AD result, script, or configuration.
- **Removed:** nothing.
- **Preserved read-only:** VH08 DEG outputs, VH09 frozen candidates, current
  Phase 18 v2 authority files and outputs, Phase 18-recorded networks, the
  Phase 09 annotation, and `fKDA.R`.

## 8. Completion criteria

VH10 is complete only when:

1. all 98 structural direction slots have a terminal eligibility status, and
   no ineligible or non-estimable slot enters a selection denominator;
2. queries use the frozen Phase 18 core-MitoCarta definition, backgrounds are
   the endpoints of networks induced on tested symbols, and every effective
   query is a subset of its recorded background;
3. the runnable minimum is three effective query genes and every 3-9-gene query
   is labeled `small_query`;
4. the current Phase 18 v2 configuration, implementation, and process-document
   checksums match the VH09-frozen values, all network/annotation/`fKDA.R`
   checksums match, and no archived three-case rule is used;
5. the explicit family, directed-layer statistics, best-layer choice, original
   within-run BH, and significant-return fields reproduce
   `call_key_drivers()` exactly;
6. conditional self-exclusion, final best-layer reselection, final within-run
   BH, explicit/implicit/missing evidence states, and conservative-support
   flags reproduce Phase 18 fixtures;
7. the union-of-backgrounds universe, coverage denominator, equal-weight ACAT,
   aggregate BH family, candidate statuses, ranks, and top-five flags use the
   shared Phase 18 selection core;
8. `primary_min3` and `phase18_sized_sensitivity` are recomputed independently,
   reported separately, and never pooled or derived by filtering winners;
9. primary and secondary evidence remain separate;
10. the independent SEA-AD lists are checksum-frozen before any Phase 18
    candidate-bearing result table is parsed or used;
11. the post-freeze Phase 18 compatibility gate reproduces the current
    canonical explicit-row fields, the full 47,590-unit aggregate/BH universe,
    and the 10,433 explicitly represented units' aggregate p/q, statuses, keys,
    and ranks exactly;
12. overlap denominators and hypergeometric counts use only the frozen,
    coverage-qualified common universe `U` reconstructed from both full
    union-of-backgrounds universes;
13. every ROSMAP selected unit is labeled rediscovered, tested but not selected,
    or not testable; and
14. all blocking checks pass and `status.tsv` reports `validated_complete`.

## 9. Expected execution environment

VH10 works from compact DEG tables and small broad-cell network edge lists. It
does not read the 1.4-million-nucleus H5AD and is expected to run locally. No
VH10 step is currently expected to require Minerva. Exact local and Minerva
commands should be added when the scripts exist; inventing commands before the
interfaces are implemented would make this document unreliable.

## 10. Interpretation of the final result

The most defensible final statement will have this form:

> SEA-AD independently rediscovered *k* of the *n* ROSMAP Phase 18 candidate
> units that were testable in SEA-AD, using independent SEA-AD DEG signatures
> with at least three effective genes on the same frozen broad-cell network
> scaffold.

If any selected or rediscovered unit depends on a 3-9-gene query, the report
must state that the primary SEA-AD minimum was lower than Phase 18's ten-gene
run-scope cutoff and present the Phase 18-sized sensitivity result alongside
the primary result.

The denominator is not automatically 47. It is the number of the 47 frozen
ROSMAP units that could actually be tested in a network with an eligible
SEA-AD query. The report must present both that assessability denominator and
the overlap, otherwise limited SEA-AD DEG power could be mistaken for failed
biological replication.
