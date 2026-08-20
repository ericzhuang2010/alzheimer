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
the same broad-cell Bayesian networks and the same `call_key_drivers()`
algorithm recorded in the Phase 18 input inventory. This makes the key-driver
results comparable with Phase 18.

Consequently, VH10 is an **independent-cohort rediscovery on a shared frozen
network scaffold**. It is not a de novo SEA-AD network reconstruction. That
distinction must be stated in the final interpretation.

Phase 18 is the scientific authority for the comparison and selection rules.
The legacy Phase 12 directory is not used as a source of candidates or as an
analytical authority. Some technical assets originally used upstream of Phase
18 are still necessary: the exact broad-cell network files and `fKDA.R` source
whose paths and checksums were recorded by Phase 18. VH10 will copy those
identities and checksums into its own configuration and will fail if they do
not match.

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
tested-gene background and network. VH10 should retain that threshold for its
strict, Phase 18-compatible analysis.

The Phase 18 source signatures also used the DEG rule:

```text
within-contrast BH FDR < 0.05
AND abs(logFC) > log2(1.3)
```

Applying that rule to the completed VH08 primary results gives the following
query sizes **before** intersection with the corresponding network:

| Broad network | AD-up mitochondrial genes | AD-down mitochondrial genes | Strict status before network intersection |
|---|---:|---:|---|
| Astrocytes | 10 | 1 | Up is provisionally eligible |
| Excitatory neurons | 20 | 3 | Up is eligible; down is small |
| Inhibitory neurons | 5 | 0 | No strict direction |
| Microglia | 14 | 2 | Up is eligible; down is too small |
| OPCs | 0 | 0 | No strict direction |
| Oligodendrocytes | 9 | 2 | No strict direction |
| Vasculature cells | 2 | 1 | No strict direction |

Only three of the 14 primary directional slots have at least 10 genes before
network intersection: Astrocyte up, Excitatory-neuron up, and Microglia up.
Network intersection can only reduce those counts, so even these three are not
guaranteed to remain eligible.

This means VH10 must not promise 14 complete top-five lists, one for each of
seven networks and two driver classes. For a network with no eligible primary
direction, the correct result is `not_testable_no_eligible_primary_query`, not
an empty list interpreted as failure and not a top-five list filled with weak
genes.

For transparency, VH10 can also produce a prespecified exploratory branch:

- effective query size at least 10: strict Phase 18-compatible analysis;
- effective query size 3-9: small-query exploratory analysis;
- effective query size below 3: not estimable.

The exploratory branch must never be mixed into the headline overlap result.
An additional FDR-only query sensitivity could be considered later, but it
would not use the same DEG definition as the source KDA analysis and therefore
must be labeled separately.

## 6. Detailed process

### VH10A - Freeze inputs and build SEA-AD KDA queries

#### Inputs

| Input | Purpose |
|---|---|
| `results/validation_human/08_deg/status.tsv` | Require VH08 `validated_complete` |
| `results/validation_human/08_deg/seaad_primary_deg_complete.tsv.gz` | Seven pooled broad-cell DEG tables |
| `results/validation_human/08_deg/seaad_secondary_deg_complete.tsv.gz` | Twenty completed secondary DEG tables |
| `results/validation_human/08_deg/seaad_deg_contrast_manifest.tsv` | Preserve all 49 contrast slots and their eligibility status |
| Phase 18 gene annotation source | Apply the same MT versus non-MT driver definition |
| Phase 18 `key_driver_input_inventory.tsv` | Resolve and verify the exact network and `fKDA.R` checksums |
| Seven Phase 18-recorded broad-cell network files | Shared frozen network scaffold |
| `scripts/NetWeaver/fKDA.R` | Frozen `call_key_drivers()` implementation |

The VH09 selected candidates are deliberately **not** an input to VH10A,
VH10B, or VH10C.

#### Query construction

Within each completed SEA-AD contrast and matching broad network:

```text
background
    = genes with test_status == tested
      intersected with genes in the matching network

AD_up_mito query
    = background genes with is_mitocarta == TRUE,
      FDR < 0.05,
      abs(logFC) > log2(1.3),
      and logFC > 0

AD_down_mito query
    = background genes with is_mitocarta == TRUE,
      FDR < 0.05,
      abs(logFC) > log2(1.3),
      and logFC < 0
```

Gene matching uses `approved_symbol`. Duplicate approved symbols are resolved
deterministically before network intersection. Every query must be a subset of
its recorded background.

The run manifest contains the complete structural grid:

```text
49 contrast slots x 2 directions = 98 directional slots
```

Every slot receives a terminal eligibility status. Unavailable contrasts and
small or empty queries are not silently omitted.

#### VH10A outputs

- `seaad_kda_run_manifest.tsv`: all 98 directional slots, source status,
  pre-network and effective query sizes, and terminal eligibility;
- `seaad_kda_signature_members.tsv.gz`: exact query genes for every runnable
  slot;
- `seaad_kda_background_members.tsv.gz`: exact tested/network background for
  every runnable slot;
- input and checksum checks.

### VH10B - Run SEA-AD KDA and retain the complete test table

For every strict-eligible primary query, call `call_key_drivers()` using the
Phase 18-recorded settings:

| Parameter | Frozen value |
|---|---|
| Network layers tested | 1-3 |
| `nLayersToExpand` | 0 |
| Directed network | `TRUE` |
| `reduce.within.nlayer` | 2 |
| Run-level correction | BH |
| Run-level FDR threshold | 0.05 |
| Return overlap genes | `TRUE` |

The same operation is run separately for each eligible secondary query, but
those results go to the secondary-support branch.

`call_key_drivers()` returns only genes passing its run-level FDR filter. That
filtered table is not sufficient for Phase 18-compatible candidate selection.
VH10 must also reconstruct and save the complete pre-FDR candidate-test table,
as Phase 18 did. This retains significant tests, nonsignificant tests,
implicit-null evidence, genes absent from a run background, and runs that were
not estimable.

For an MT driver that is itself a member of the mitochondrial query, its
guaranteed self-overlap is removed before the final enrichment statistic is
calculated. The stored per-run evidence includes:

- best network layer;
- query overlap and neighborhood size;
- fold enrichment;
- raw hypergeometric p-value;
- within-run BH q-value; and
- conservative support, defined as at least two other query genes, fold
  enrichment greater than one, and run q-value at most 0.05.

Candidate class is fixed exactly as in current Phase 18:

- `mt_driver`: Phase 18 core-MitoCarta membership is true;
- `non_mt_driver`: Phase 18 core-MitoCarta membership is false or absent.

#### VH10B outputs

- `seaad_kda_candidate_tests.tsv.gz`: complete gene-by-run test table;
- `seaad_kda_significant_returns.tsv`: the subset returned by
  `call_key_drivers()`;
- `seaad_kda_secondary_candidate_tests.tsv.gz`: separate secondary evidence;
- run-level QC and reconstruction checks.

### VH10C - Select and freeze the independent SEA-AD top drivers

Only strict-eligible primary runs enter the headline selection.

For each `broad_network + key_driver + case_id` candidate unit:

1. combine usable run-level raw p-values across the eligible primary
   directions using the same ACAT procedure as Phase 18;
2. treat an implicit candidate test as p = 1 and omit genuinely missing tests;
3. calculate coverage as usable eligible primary runs divided by all eligible
   primary runs in that network;
4. apply BH correction to aggregate ACAT p-values within the broad network,
   across both driver classes;
5. require all three Phase 18 gates:
   - coverage at least 0.80;
   - at least one conservative supporting run;
   - aggregate ACAT q-value at most 0.05;
6. rank passing candidates separately within each
   `broad_network + case_id` list by:
   - smaller aggregate q-value;
   - smaller aggregate p-value;
   - alphabetical gene symbol;
7. retain ranks 1-5.

Five is a maximum, not a quota. No nonsignificant candidate is used to fill an
incomplete list.

Because SEA-AD has at most two primary directional runs in a network, and often
only one eligible direction, its aggregation has much less recurrence
information than ROSMAP Phase 18. VH10 applies the same gates for comparability,
but the report must show each list's eligible-run count and must not describe a
one-run selection as broadly recurrent evidence.

VH10C writes the SEA-AD top list and its SHA-256 checksum before any VH09
candidate file is read. This is the boundary that makes the later overlap
comparison an honest rediscovery analysis.

#### VH10C outputs

- `seaad_kda_candidate_summary.tsv`: one row per SEA-AD candidate unit;
- `seaad_kda_top5.tsv`: independently selected SEA-AD units, including explicit
  empty/not-testable list rows;
- `seaad_kda_secondary_support.tsv`: secondary evidence kept separate from
  selection;
- `seaad_kda_selection_freeze.tsv`: row counts, list counts, file checksum, and
  freeze timestamp.

### VH10D - Unblind the ROSMAP list and calculate overlap

Only after VH10C passes its freeze checks does VH10D read:

```text
results/validation_human/09_rosmap_kda_candidates/
    phase18_selected_candidate_units.tsv
```

The strict match key is:

```text
broad_network + key_driver + case_id
```

Network-specific matching is primary because a gene selected in astrocytes
and the same gene selected in excitatory neurons are different Phase 18
candidate units. An overlap of unique gene symbols that ignores network is
reported only as a secondary descriptive metric.

For each assessable broad-network and driver-class list, report:

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
| `not_testable` | No eligible SEA-AD query or the gene was outside the common testable background |

`not_testable` units are excluded from the replication denominator. They must
not be counted as negative replications. SEA-AD-only candidates are new
hypotheses; they are not failures of ROSMAP validation.

#### VH10D outputs

- `rosmap_seaad_candidate_overlap.tsv`: unit-level match and testability status;
- `rosmap_seaad_overlap_summary.tsv`: per-network/class and overall metrics;
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
```

The exact split can change during implementation, but discovery/freeze and
ROSMAP unblinding must remain separate executable stages.

### New results, when VH10 is executed

```text
results/validation_human/10_seaad_kda_rediscovery/
├── seaad_kda_run_manifest.tsv
├── seaad_kda_signature_members.tsv.gz
├── seaad_kda_background_members.tsv.gz
├── seaad_kda_candidate_tests.tsv.gz
├── seaad_kda_significant_returns.tsv
├── seaad_kda_candidate_summary.tsv
├── seaad_kda_top5.tsv
├── seaad_kda_secondary_candidate_tests.tsv.gz
├── seaad_kda_secondary_support.tsv
├── seaad_kda_selection_freeze.tsv
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
  and `10_seaad_kda_rediscovery` outputs listed above.
- **Changed:** no existing ROSMAP or SEA-AD result, script, or configuration.
- **Removed:** nothing.
- **Preserved read-only:** VH08 DEG outputs, VH09 frozen candidates, Phase 18
  outputs, Phase 18-recorded networks, and `fKDA.R`.

## 8. Completion criteria

VH10 is complete only when:

1. all 98 structural direction slots have a terminal eligibility status;
2. every runnable query is a subset of its recorded background;
3. all network and algorithm checksums match the frozen Phase 18 inventory;
4. the complete pre-FDR candidate-test table reproduces the significant
   `call_key_drivers()` subset;
5. candidate classes, self-exclusion, run-level BH, ACAT, aggregate BH, gates,
   ranks, and top-five flags reproduce hand-checked examples;
6. the independent SEA-AD list is checksum-frozen before VH09 is read;
7. overlap denominators include only common testable candidate units;
8. every ROSMAP selected unit is labeled rediscovered, tested but not selected,
   or not testable;
9. primary and secondary evidence remain separate; and
10. all blocking checks pass and `status.tsv` reports `validated_complete`.

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
> on the same frozen broad-cell network scaffold.

The denominator is not automatically 47. It is the number of the 47 frozen
ROSMAP units that could actually be tested in a network with an eligible
SEA-AD query. The report must present both that assessability denominator and
the overlap, otherwise limited SEA-AD DEG power could be mistaken for failed
biological replication.
