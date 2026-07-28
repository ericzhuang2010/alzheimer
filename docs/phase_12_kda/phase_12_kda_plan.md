# Phase 12: Cell-Type-Specific Mitochondrial Key-Driver Analysis

## Status and phase boundary

This document defines the reviewable implementation and execution plan for
Phase 12. Phase 12 will project Phase 08 mitochondrial AD-versus-NCI DEG
signatures onto the matching directed Bayesian networks and use
NetWeaver-style key-driver analysis (KDA) to identify putative upstream
regulators.

Plan status: **draft for review; not approved for execution**.

Creating this document does not authorize or perform KDA. No Phase 08 or
Phase 09 data will be changed, no Bayesian network will be rebuilt, and no
Phase 12 result will be produced until this plan is reviewed and approved.

Local-pilot and Minerva-production outputs are separate:

```text
results/local_pilot/12_kda/
results/minerva_production/12_kda/
```

Pilot files must never be copied into, combined with, or promoted in place to
the production directory.

The required Phase 12 analysis has two levels:

- **Primary:** the six sex/APOE strata analyzed separately.
- **Secondary:** female, male, APOE ε2, APOE ε3/ε3, and APOE ε4 pooled
  signatures.

At both levels, every eligible group will be analyzed separately for every one
of the 54 Phase 08 fine cell types using exactly three signatures:

1. AD-up mitochondrial DEGs;
2. AD-down mitochondrial DEGs; and
3. the union of AD-up and AD-down mitochondrial DEGs.

The third signature is the complete bidirectional DEG set. It is therefore
not accompanied by a separate fourth signature called `all DEGs`; those two
definitions would be identical.

Phase 12 must **not**:

- refit MAST or change the Phase 08 DEG rule;
- interpret a pooled signature as a newly fitted pooled DE contrast;
- infer activation or inhibition from an unsigned Bayesian-network edge;
- merge the nine final networks into one network;
- use either pre-de-loop combined Bayesian-network file;
- use the old `BN.KDA.summary_stats.csv` results;
- select DEG thresholds or KDA parameters after inspecting driver results;
- silently omit an ineligible or empty run;
- label a network-enrichment result as proof of causality; or
- draw or publish final figures.

## High-level purpose

The primary scientific question is:

> Which upstream network genes have directed downstream neighborhoods enriched
> for the mitochondrial AD response in each fine cell type and sex/APOE
> stratum?

The secondary question is:

> Which candidate drivers recur when related stratum-specific signatures are
> summarized into sex-level or APOE-level pools?

Every reported driver will be described as a **putative key driver** or
**candidate upstream regulator**. Bayesian-network direction and KDA
enrichment provide network-based prioritization, not experimental proof of a
causal, activating, or inhibitory relationship.

## Relationship to preceding phases

Phase 12 inherits rather than reconstructs the following:

| Source | Frozen Phase 12 use |
|---|---|
| Phase 08 | Fine-cell-type, sex/APOE-stratified AD-versus-NCI MAST results and `paper_deg` calls |
| Phase 09 | Stable feature identity, current HGNC annotation, and mitochondrial-tier membership |
| Bayesian-network audit | Final de-looped, directed edge list and fine-to-broad network mapping |
| Local KDA source | NetWeaver-style `call_key_drivers()` implementation and documented defaults |

Phase 08 contains six AD-versus-NCI contrasts per fine cell type:

| `group_id` | Sex | APOE group | Phase 08 comparison |
|---|---|---|---|
| `F_e2` | Female | ε2 | Female ε2 AD minus Female ε2 NCI |
| `F_e33` | Female | ε3/ε3 | Female ε3/ε3 AD minus Female ε3/ε3 NCI |
| `F_e4` | Female | ε4 | Female ε4 AD minus Female ε4 NCI |
| `M_e2` | Male | ε2 | Male ε2 AD minus Male ε2 NCI |
| `M_e33` | Male | ε3/ε3 | Male ε3/ε3 AD minus Male ε3/ε3 NCI |
| `M_e4` | Male | ε4 | Male ε4 AD minus Male ε4 NCI |

The effect direction remains AD minus NCI throughout Phase 12. Positive
Phase 08 `logFC` means higher expression in AD; negative `logFC` means lower
expression in AD.

## Frozen scientific design

### Unit of analysis

One planned KDA run is uniquely defined by:

```text
fine cell type
× analysis level
× analysis group
× signature direction
× mitochondrial-universe profile
× KDA-parameter profile
```

The required analysis uses one mitochondrial-universe profile and one frozen
KDA-parameter profile. Sensitivity profiles, if approved later, must use
separate run identifiers and output directories.

### Primary analysis grid

For each of the 54 fine cell types, analyze the six Phase 08 strata
independently:

- `F_e2`;
- `F_e33`;
- `F_e4`;
- `M_e2`;
- `M_e33`; and
- `M_e4`.

For each stratum, construct:

- `AD_up_mito`;
- `AD_down_mito`; and
- `AD_both_mito`.

The complete planned primary grid is:

```text
54 fine cell types × 6 strata × 3 signatures = 972 planned runs
```

All 972 rows must appear in the Phase 12 run manifest. Phase 08 has 321
completed and three explicitly non-estimable fine-cell-type/stratum
comparisons, so nine primary direction rows are expected to be marked
`source_contrast_not_estimable` before query-size and network-coverage checks.
They must not be dropped.

### Secondary pooled analysis grid

For each fine cell type, construct five secondary groups:

| `group_id` | Required member strata |
|---|---|
| `female_pool` | `F_e2`, `F_e33`, `F_e4` |
| `male_pool` | `M_e2`, `M_e33`, `M_e4` |
| `e2_pool` | `F_e2`, `M_e2` |
| `e33_pool` | `F_e33`, `M_e33` |
| `e4_pool` | `F_e4`, `M_e4` |

For each pool, construct:

- `AD_up_mito`;
- `AD_down_mito`; and
- `AD_both_mito`.

The complete planned secondary grid is:

```text
54 fine cell types × 5 pools × 3 signatures = 810 planned runs
```

A pool is complete only when every required member contrast has terminal
status `validated_complete`. A missing or non-estimable member must not be
silently removed. The affected pooled rows receive
`source_pool_incomplete`.

Because the three known non-estimable Phase 08 contrasts are all `M_e2`,
the corresponding `male_pool` and `e2_pool` rows are expected to be
source-incomplete for those fine cell types. This creates 18 secondary
direction rows with `source_pool_incomplete` before query-size and
network-coverage checks.

The required Phase 12 manifest therefore contains:

```text
972 primary rows + 810 secondary rows = 1,782 planned runs
```

The number actually eligible for KDA will be smaller and must be determined
only by the prespecified source-status, query-size, and network-coverage rules.

### DEG definition

Phase 12 will trust the validated Phase 08 `paper_deg` field and independently
check that it reproduces:

```text
fdr_bh_within_contrast < 0.05
AND abs(logFC) > log2(1.3)
```

The Phase 08 `FindMarkers()` detection filter was:

```text
pct_ad >= 0.10 OR pct_nci >= 0.10
```

Phase 12 must not recalculate FDR across pooled groups or use a new DEG
threshold.

### Required mitochondrial universe

The required primary KDA universe is:

```text
analysis_profile = core_mito
mito_tier = core_mito_protein
```

Membership must come from the validated Phase 09 annotation master. Gene-name
prefixes and a newly downloaded mitochondrial list must not be used to rebuild
membership.

After the required analysis is complete, a separately labeled sensitivity
profile may be considered:

```text
analysis_profile = all_mito_related
mito_tier in {
  core_mito_protein,
  mtdna_noncoding,
  mito_extended
}
```

This sensitivity profile is outside the required 1,782-run count and must not
replace the `core_mito` result after viewing significance.

### Feature identity

The network-matching key will be the original Phase 08 assay identifier:

```text
network_gene_id = Phase 08 gene = Phase 09 feature_id_original
```

The current HGNC symbol, HGNC ID, Ensembl ID, mapping status, mitochondrial
tier, and original symbol will be retained as annotations. Current symbols
must not replace the matching key unless a documented network-identifier audit
shows that the network itself uses current symbols.

Duplicate query identifiers will be collapsed within a run. Ambiguous
one-to-many mappings are a blocking error, not an invitation to duplicate a
gene in the enrichment test.

### Primary signature construction

For one completed Phase 08 contrast and fine cell type, define:

```text
D_up   = unique core-mito genes with paper_deg = TRUE and logFC > 0
D_down = unique core-mito genes with paper_deg = TRUE and logFC < 0
D_both = union(D_up, D_down)
```

`D_up` and `D_down` must be disjoint for a single Phase 08 contrast.
`D_both` contains each gene once.

### Pooled signature construction

Pooled signatures are set unions of existing Phase 08 DEG calls. They are not
new differential-expression estimates.

For a pool with required member contrasts \(C_1,\ldots,C_j\):

```text
P_up   = union(D_up(C1), ..., D_up(Cj))
P_down = union(D_down(C1), ..., D_down(Cj))
P_both = union(P_up, P_down)
```

A gene that is AD-up in one member and AD-down in another is
`direction_discordant = TRUE`. It may occur in both `P_up` and `P_down`, and it
occurs once in `P_both`. This preserves the requested any-member pooling rule
without pretending the direction is consistent across the pool.

For every pooled gene, retain:

- all contributing member contrasts;
- direction in every contributing contrast;
- number of member contrasts in which it was tested;
- number in which it was a DEG;
- number with AD-up direction;
- number with AD-down direction; and
- the direction-discordance flag.

Consensus-direction pooling may be evaluated later as a sensitivity analysis,
but it is not part of the required grid.

### Fine-cell-type to Bayesian-network mapping

KDA signatures remain separate for all 54 fine cell types. The available final
Bayesian networks are broader than the Phase 08 fine-cell-type labels, so
related fine types reuse the appropriate audited broad network:

| Phase 08 fine type | Required final network |
|---|---|
| All `Ast*` types | `Astrocytes` |
| All `Exc*` types | `Excitatory_neurons` |
| All `Inh*` types | `Inhibitory_neurons` |
| `OPC` | `OPCs` |
| `Oli` | `Oligodendrocytes` |
| `End`, `Fib FLRT2`, `Fib SLC4A4`, `Per`, `SMC` | `Vasculature_cells` |
| `CAMs` | `CAMs` |
| `Mic MKI67`, `Mic P2RY12`, `Mic TPT1` | `Microglia` |
| `T cells` | `T_cells` |

This distinction must appear in every output:

```text
signature_scope = fine_cell_type
network_scope = broad_cell_class
```

Results from two fine cell types mapped to the same network remain different
KDA runs because their DEG signatures and backgrounds differ. They must not be
collapsed before KDA.

Only each network's final `result.links3.links.txt` file may be used. The first
column is upstream and the second is downstream. Each network must be
headerless, have exactly two nonempty columns, contain no self-edge or
duplicate edge, and pass a directed-acyclic-graph check.

As of 2026-07-27, all nine expected broad-cell-type
`result.links3.links.txt` files are present under
`data/bayesian_network/`. Their presence does not replace production
preflight: checksums, edge-list structure, direction, uniqueness, and
directed-acyclic-graph status must still be validated before KDA begins.

### Primary background construction

For each primary stratum run, begin with:

```text
genes returned by MAST in the exact Phase 08 contrast
∩
nodes in the matching final Bayesian network
```

To use the scalar `bg.size` argument consistently, the production adapter must
induce the run-specific network on those background genes, remove nodes left
without any retained edge, and then freeze:

```text
B_primary = nodes in the induced run-specific network
Q_primary = mitochondrial DEG signature ∩ B_primary
bg.size   = length(B_primary)
```

The plan deliberately does not pass a reduced scalar `bg.size` alongside an
unrestricted full network. The reviewed `call_key_drivers()` function counts
neighborhood nodes from the supplied network; using a smaller scalar without
restricting network membership would make the neighborhood and background
inconsistent.

This induced-network policy also means that a putative driver must have been
returned by MAST in that fine-cell-type/contrast context and remain connected
within the background-induced graph. The manifest must report how many full
network nodes and edges were removed.

### Pooled background construction

For a complete pool, use the intersection of member-specific tested sets:

```text
T_pool = intersection(
  genes returned by MAST in every required member contrast
)

B_pool = nodes in the matching network induced on T_pool
Q_pool = pooled mitochondrial DEG signature ∩ B_pool
bg.size = length(B_pool)
```

The intersection gives every background gene a documented opportunity to
become a DEG in every member contrast. It is intentionally more conservative
than using the union of tested sets.

For each pool, record:

- tested-gene count in each member contrast;
- tested-set intersection size;
- full network node and edge count;
- induced background node and edge count;
- original pooled signature size;
- effective network-mapped signature size; and
- genes removed at each filtering step.

A union-background pooled analysis may be considered later as a prespecified
sensitivity profile, but it must not be mixed with the required
intersection-background results.

### Query eligibility

Every planned run receives one explicit status.

| Condition | Required status |
|---|---|
| Source Phase 08 contrast is not estimable | `source_contrast_not_estimable` |
| At least one required pooled member is incomplete | `source_pool_incomplete` |
| No background-induced edges remain | `background_network_empty` |
| Fewer than three effective query genes remain | `effective_query_lt_3` |
| Inputs are valid and query has at least three genes | `eligible` |

An effective query of 3–9 genes is eligible but receives
`small_query_warning = TRUE`. Query size, not the presence of a significant
driver, determines eligibility.

### Frozen KDA engine and parameters

The requested reference implementation is:

```text
scripts/NetWeaver/fKDA.R
function: call_key_drivers()
```

Each eligible run will pass exactly one signature group so that its background
and network are unambiguous:

```r
signature_df <- data.frame(
  Var = effective_query,
  Group = run_id,
  stringsAsFactors = FALSE
)

result <- call_key_drivers(
  net = induced_network,
  signature.df = signature_df,
  nLayerToTest = 3,
  nLayersToExpand = 0,
  bg.size = length(effective_background),
  directed = TRUE,
  reduce.within.nlayer = 2,
  fdr = 0.05,
  p.correction.method = "BH",
  return.overlap = TRUE
)
```

The primary parameter profile is therefore:

| Parameter | Required value |
|---|---:|
| Network direction | upstream to downstream |
| `nLayerToTest` | 3 |
| `nLayersToExpand` | 0 |
| `directed` | `TRUE` |
| `reduce.within.nlayer` | 2 |
| `fdr` | 0.05 |
| `p.correction.method` | `BH` |
| `return.overlap` | `TRUE` |

The source file, adapter, configuration, and R session must be checksummed.
The source file must not be edited silently during a production run.

The repository also contains a separate maintained Wang KDA 0.2 two-stage
interface under `scripts/analysis/kda/`. That implementation must not be
silently substituted for `call_key_drivers()`. If it is used as an independent
validation profile, its outputs must be labeled with a different
`kda_engine`, parameter profile, run ID, and output directory.

### Statistical interpretation

Within one call, `call_key_drivers()`:

1. evaluates candidate directed neighborhoods up to three layers;
2. retains the best layer for a candidate driver;
3. computes a one-sided hypergeometric enrichment P value;
4. applies BH correction across candidate drivers in that signature; and
5. returns candidates passing adjusted P value `<= 0.05`.

The returned `adj.P.Value` controls multiplicity within one signature run. It
does not provide study-wide FDR control across 1,782 planned runs. Phase 12
will not claim study-wide significance from the within-run value.

Cross-run recurrence, number of cell types, number of groups, and consistency
of direction will be reported descriptively. A phase-wide correction cannot
be reconstructed correctly from a table that contains only significant
drivers, so no post hoc BH adjustment will be applied only to returned rows.

A `NULL` return is a valid outcome:

```text
terminal_status = validated_complete
result_status = no_significant_key_driver
```

It must not be treated as a failed or missing run.

### Optional sensitivity analyses

The following are prespecified candidates for later sensitivity analysis, not
part of the required execution:

- `all_mito_related` instead of `core_mito`;
- one- and two-layer neighborhood depths;
- the separately maintained Wang KDA 0.2 interface;
- pooled union-background instead of intersection-background;
- consensus-direction pools that exclude direction-discordant genes; and
- degree-matched random signatures for selected high-priority results.

No sensitivity profile should be started until the required design is
reviewed, implemented, and frozen.

## Inputs and dependencies

### Required Phase 08 inputs

From:

```text
results/minerva_production/08_mast/
```

Require:

- all nine `*.yu_mast_de.tsv.gz` result files;
- all nine `*.yu_mast_contrast_manifest.tsv` files;
- all nine `*.yu_mast_contrast_status.tsv` files;
- all nine `*.yu_mast_de_status.tsv` files; and
- the Phase 08 validation/check tables.

Preflight must verify:

- nine input families;
- 54 unique fine cell types;
- six planned contrasts per fine cell type;
- 324 contrast-status rows;
- 321 `validated_complete` and three `not_estimable` contrasts;
- no failed contrasts;
- AD as numerator and NCI as denominator throughout;
- unique `(fine cell type, contrast, gene)` keys; and
- exact reproduction of the stored `paper_deg` rule.

### Required Phase 09 inputs

From:

```text
results/minerva_production/09_annotate_genes/
```

Require:

- `gene_annotation_master.tsv.gz`;
- `annotation_status.tsv`;
- `annotation_artifacts.tsv`;
- `annotation_checks.tsv`; and
- the mitochondrial reference inventory.

Phase 09 must have `validation_status = validated_complete`, and every required
artifact checksum must match before input preparation begins.

### Required Bayesian-network inputs

Require the nine audited final edge lists:

```text
data/bayesian_network/Astrocytes/result.links3.links.txt
data/bayesian_network/CAMs/result.links3.links.txt
data/bayesian_network/Excitatory_neurons/result.links3.links.txt
data/bayesian_network/Inhibitory_neurons/result.links3.links.txt
data/bayesian_network/Microglia/result.links3.links.txt
data/bayesian_network/OPCs/result.links3.links.txt
data/bayesian_network/Oligodendrocytes/result.links3.links.txt
data/bayesian_network/T_cells/result.links3.links.txt
data/bayesian_network/Vasculature_cells/result.links3.links.txt
```

A frozen network manifest must record file path, SHA-256, edge count, node
count, source-to-target convention, duplicate count, self-edge count, and DAG
validation status.

### Required configuration

Implementation should add one frozen configuration file:

```text
config/phase12_kda.yml
```

It should contain:

- Phase 08 and Phase 09 input paths;
- nine network paths and expected checksums;
- the fine-to-broad network mapping;
- six primary group definitions;
- five pool definitions and required members;
- three signature definitions;
- mitochondrial-universe profiles;
- background policies;
- minimum query size and warning threshold;
- exact `call_key_drivers()` parameters;
- expected run-grid dimensions; and
- output path and schema versions.

Configuration must be read before outputs are created and copied or
checksummed into the final provenance bundle.

### Required software

The production environment must record:

- R version and platform;
- package versions used for I/O, checksums, and validation;
- checksum of `scripts/NetWeaver/fKDA.R`;
- Git revision;
- locale; and
- UTC start and finish times.

No package may be downloaded dynamically inside a production task.

## Construction workflow

### 1. Review and freeze decisions

Before implementation:

1. approve the three-signature design;
2. approve `core_mito` as the required universe;
3. approve strict complete-member pooling;
4. approve any-member union for pooled queries;
5. approve intersection backgrounds for pooled runs;
6. approve the induced-network use of `call_key_drivers()`; and
7. approve the frozen three-layer parameter profile.

No analysis begins until these decisions are reflected in configuration.

### 2. Validate all inherited inputs

Validate Phase 08, Phase 09, and all nine final networks against their status
files, schemas, expected dimensions, and checksums. Stop before creating
result files if any blocking check fails.

### 3. Build the complete run grid

Create all 1,782 planned rows before applying eligibility filters. Each row
must have a deterministic `run_id`, for example:

```text
Mic_P2RY12__primary__M_e2__AD_down_mito__core_mito
Mic_P2RY12__secondary__male_pool__AD_both_mito__core_mito
```

Required run-manifest fields include:

- `run_id`;
- `analysis_level`;
- `group_id`;
- `member_strata`;
- `fine_cell_type`;
- `network_id`;
- `signature_direction`;
- `analysis_profile`;
- source contrast IDs and statuses;
- background policy;
- KDA parameter-profile ID;
- eligibility;
- skip reason; and
- terminal status.

### 4. Construct primary signatures and backgrounds

For every fine cell type and stratum:

1. load the exact Phase 08 result rows;
2. validate `paper_deg`;
3. join Phase 09 mitochondrial annotations;
4. build `D_up`, `D_down`, and `D_both`;
5. build the exact tested-gene/network background;
6. induce the run-specific network;
7. intersect each query with the induced network nodes; and
8. store membership and loss diagnostics.

### 5. Construct pooled signatures and backgrounds

For every fine cell type and pool:

1. validate that all required member contrasts completed;
2. build the member-specific up and down sets;
3. form `P_up`, `P_down`, and `P_both`;
4. calculate per-gene contributing-member and direction metadata;
5. flag direction-discordant genes;
6. intersect tested genes across all required members;
7. induce the pooled background network;
8. intersect each pooled query with that network; and
9. store membership and loss diagnostics.

### 6. Apply eligibility rules

Assign one explicit eligibility status to every planned row. Do not submit
ineligible rows to KDA. Retain them in the run manifest and QC summaries.

### 7. Run a prespecified pilot after approval

After implementation and approval, first run:

- one sufficiently large Microglia signature;
- its up, down, and combined queries;
- one corresponding pooled query; and
- a small synthetic network with a known upstream driver.

The pilot must confirm direction, layer behavior, background arithmetic,
empty-result handling, output schemas, determinism, and resumability. Pilot
results are labeled `nonfinal_smoke_test` and cannot be merged into production
tables.

### 8. Run eligible primary signatures

Run the eligible primary manifest rows without altering the frozen inputs or
parameters. A `run_id` is a row identifier used in tables, not the name of a
permanent result directory. If scheduled tasks require per-run shards, those
shards must be written to disposable local or Minerva scratch space outside
the final `results/<environment>/12_kda/` directory.

### 9. Run eligible secondary signatures

Run secondary rows only after the primary grid and pooled-input audits pass.
Keep primary and secondary identifiers explicit in every output.

### 10. Combine and validate

After all eligible runs have one terminal status:

1. combine temporary task shards without dropping empty runs;
2. create the significant-driver table;
3. attach feature and network annotations;
4. create recurrence summaries;
5. write QC and provenance tables;
6. independently recompute enrichment arithmetic for sampled rows; and
7. atomically publish only the compact Phase 12 files listed below.

## Outputs and files created

Phase 12 follows the flat, phase-level output pattern used by the preceding
phases. It will not create `inputs/`, `runs/`, `combined/`, `qc/`, or
`provenance/` subdirectories, and it will not retain one directory per KDA
run.

The two output roots are:

```text
results/local_pilot/12_kda/
results/minerva_production/12_kda/
```

Each environment contains only this compact final bundle:

```text
results/<environment>/12_kda/
├── kda_run_manifest.tsv
├── kda_signature_members.tsv.gz
├── kda_background_members.tsv.gz
├── kda_results.tsv.gz
├── kda_key_driver_summary.tsv
├── kda_qc_summary.tsv
├── kda_checks.tsv
├── kda_artifacts.tsv
└── kda_status.tsv
```

File responsibilities:

| File | Purpose |
|---|---|
| `kda_run_manifest.tsv` | One row per planned `run_id`, including group definition, source contrasts, network, query/background sizes, eligibility, skip reason, result count, and terminal status |
| `kda_signature_members.tsv.gz` | Long-form effective and excluded mitochondrial query genes, including source-member and pooled-direction diagnostics |
| `kda_background_members.tsv.gz` | Long-form effective background membership needed to reproduce each enrichment test |
| `kda_results.tsv.gz` | All returned key-driver rows from all completed runs |
| `kda_key_driver_summary.tsv` | Compact significant-driver and cross-run recurrence summary for interpretation |
| `kda_qc_summary.tsv` | Query coverage, background/network reduction, small-query, pooled-discordance, and no-result summaries |
| `kda_checks.tsv` | Structural, scientific, numerical, and reproducibility validation checks |
| `kda_artifacts.tsv` | Input/output paths, sizes, schemas, SHA-256 values, configuration checksum, code checksum, and software provenance |
| `kda_status.tsv` | One phase-level terminal status row |

Information previously proposed as separate group, network, provenance, and
per-run files will instead be stored as columns in these tables. No additional
file may be added to a final Phase 12 directory unless it is required for
scientific interpretation or reproducibility and is added to this plan during
review.

### Local-pilot output

The local pilot publishes only to:

```text
results/local_pilot/12_kda/
```

It contains the five-fine-cell-type Vasculature pilot grid plus the synthetic
direction control. Its `kda_status.tsv` must report `nonfinal_smoke_test`. The
pilot validates code, schemas, background arithmetic, runtime, and empty-result
behavior; it is not a partial production result.

### Minerva-production output

The complete 1,782-row planned grid publishes only to:

```text
results/minerva_production/12_kda/
```

Minerva production must start from the frozen configuration and validated
Phase 08, Phase 09, and network inputs. It must not read KDA results or
membership tables from `results/local_pilot/12_kda/`. Temporary task shards
belong in Minerva scratch or another explicitly disposable working location,
not in the final production phase directory.

Production is complete only when the nine-file bundle is atomically
published, all artifact checksums match, and `kda_status.tsv` reports
`validated_complete`.

### KDA result schema

Each returned driver row should retain at least:

- schema version;
- run ID and KDA engine;
- analysis level and group ID;
- fine cell type and mapped network ID;
- signature direction and mitochondrial profile;
- source contrast IDs;
- query and background sizes;
- full and induced network sizes;
- `Signature`;
- `Keydriver`;
- `BestLayer`;
- `q`, `m`, `n`, and `k`;
- fold enrichment;
- `log.P.Value`;
- raw P value reconstructed as `exp(log.P.Value)`;
- `adj.P.Value`;
- `is.signature`, when returned;
- `is.root.node`;
- `global.Keydriver`;
- overlap-gene list;
- direction-discordance diagnostics for pooled queries; and
- run terminal status.

`global.Keydriver` is the function's within-run redundancy-reduction flag. It
must not be interpreted as globally significant across all cell types or
signatures.

## Code and configuration changes required before execution

### New files

| File | Required content |
|---|---|
| `config/phase12_kda.yml` | Frozen primary and pooled groups, three signatures, mitochondrial universe, network paths/checksums, fine-to-broad mapping, background rules, query thresholds, KDA parameters, expected pilot/production dimensions, output names, and schemas. |
| `scripts/12_run_kda.R` | One global Phase 12 entry point that validates Phase 08/09 and networks, builds the complete run grid, constructs signatures/backgrounds, runs `call_key_drivers()`, combines temporary shards, validates results, and atomically writes the flat nine-file bundle. |
| `tests/test_phase12_kda.R` | Deterministic tests for group membership, pooled unions, direction discordance, tested-set intersections, induced networks, query eligibility, run IDs, enrichment arithmetic, empty results, and output schemas. It writes only to a disposable temporary directory. |
| `docs/phase_12_kda/phase_12_kda_plan.md` | This implementation and execution plan. |

No separate prepare, run, combine, or validate executable is planned. Those
operations are functions inside `scripts/12_run_kda.R`, which keeps the public
command and final output contract small.

The planned internal functions are:

| Function | Responsibility |
|---|---|
| `parse_phase12_cli()` | Accept `--config`, `--execution-config`, and `--task-mode kda`. |
| `validate_phase08_bundle()` | Validate the nine production or one local-pilot Phase 08 families, statuses, contrast dimensions, DEG rule, and checksums. |
| `validate_phase09_bundle()` | Validate annotation status/artifacts and load the frozen feature-to-mitochondrial-tier mapping. |
| `read_validate_networks()` | Read the required final edge lists and check two-column structure, direction, uniqueness, self-edges, node counts, checksums, and DAG status. |
| `build_phase12_run_grid()` | Create all primary and secondary `run_id` rows before eligibility filtering. |
| `build_primary_signature()` | Construct one fine-cell/stratum up, down, or combined mitochondrial DEG set. |
| `build_pooled_signature()` | Construct one complete-member pooled set and retain member/direction-discordance diagnostics. |
| `build_effective_background()` | Construct the exact primary or pooled tested-gene background and induced network. |
| `run_one_key_driver_test()` | Call the frozen NetWeaver `call_key_drivers()` parameters for one eligible row and normalize `NULL` as a completed no-result outcome. |
| `combine_phase12_results()` | Combine temporary results by `run_id` into the manifest, result, summary, membership, and QC tables. |
| `validate_phase12_outputs()` | Run structural, scientific, numerical, environment-separation, and artifact checks. |
| `publish_phase12_bundle()` | Atomically publish only the nine approved files after all blocking checks pass. |

### Existing files changed

| File | Required change |
|---|---|
| `scripts/run_pipeline.R` | Register global task mode `kda` after `pathway`, resolve `project.phase12_kda_config`, add `kda` to the implemented global modes, pass no manifest row, and declare output schema `mitochondrial_kda_v1`. |
| `config/local_pilot.yml` | Add `project.phase12_kda_config: config/phase12_kda.yml` and enable `kda` after `pathway`. |
| `config/minerva_shared.yml` | Add `project.phase12_kda_config: config/phase12_kda.yml` and enable `kda` after `pathway`. |
| `scripts/NetWeaver/fKDA.R` | Correct the upper-tail hypergeometric boundary from `phyper(max(0, q - 1), ...)` to `phyper(q - 1, ...)`, so a candidate with zero signature overlap has P = 1 rather than being tested as though it had one overlap. Freeze and verify the corrected SHA-256 from `config/phase12_kda.yml`. |
| `renv.lock` | Change only if implementation requires a package that is not already pinned. |

The pipeline must reject `--rds-id` for `kda`. Phase 12 is one global task in
each environment. It may parallelize eligible `run_id` rows internally, but
temporary task shards remain outside the final phase directory and only one
process performs the final combination and publication.

### Files frozen after review or unchanged

- after the documented one-line statistical correction,
  `scripts/NetWeaver/fKDA.R` is frozen by checksum and remains the requested
  `call_key_drivers()` engine;
- all existing files under `scripts/analysis/kda/` remain unchanged and are
  not the primary Phase 12 engine;
- every Phase 00–11 scientific result and script remains unchanged;
- all nine final Bayesian-network edge lists remain unchanged; and
- no figure-generation script is added or run.

## Local pilot: run the 165-row Vasculature design

### Input

```text
results/local_pilot/08_mast/
results/local_pilot/09_annotate_genes/
data/bayesian_network/Vasculature_cells/result.links3.links.txt
config/local_pilot.yml
config/local_pilot_execution.yml
config/phase12_kda.yml
scripts/NetWeaver/fKDA.R
```

The local pilot uses all five Vasculature fine cell types, all six primary
strata, all five secondary pools, and all three signature directions:

```text
Primary:   5 fine cell types × 6 strata × 3 signatures = 90 rows
Secondary: 5 fine cell types × 5 pools  × 3 signatures = 75 rows
Total:                                                   165 rows
```

The known `Fib SLC4A4`, male-ε2 source contrast remains explicitly
non-estimable. Its three primary rows and the six affected `male_pool` and
`e2_pool` rows must remain in the manifest with source-status reasons.

### Output

```text
results/local_pilot/12_kda/
```

Only the flat nine-file bundle is published. No `runs/` or other subdirectory
is allowed. The pilot status is `nonfinal_smoke_test`.

### Preflight

Do not run these commands until the code and configuration listed above have
been implemented and reviewed.

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

test -r config/phase12_kda.yml
test -r scripts/12_run_kda.R
test -r scripts/NetWeaver/fKDA.R
test -r data/bayesian_network/Vasculature_cells/result.links3.links.txt
test -r results/local_pilot/08_mast/vasculature.yu_mast_de.tsv.gz
test -r results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv
test -r results/local_pilot/09_annotate_genes/gene_annotation_master.tsv.gz
test -r results/local_pilot/09_annotate_genes/annotation_status.tsv

Rscript -e '
stopifnot(
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("digest", quietly = TRUE)
)
de <- read.delim(
  "results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv")
ann <- read.delim(
  "results/local_pilot/09_annotate_genes/annotation_status.tsv")
stopifnot(
  de$validation_status == "validated_complete",
  ann$validation_status == "validated_complete"
)
cat("Local Phase 08/09 inputs are ready for the Phase 12 smoke test\n")
'
```

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase kda \
  --dry-run
```

Expected task graph: exactly one `global:kda` task using
`scripts/12_run_kda.R`, no RDS ID, and output schema
`mitochondrial_kda_v1`.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase kda
```

### Validate

```bash
Rscript -e '
library(data.table)
root <- "results/local_pilot/12_kda"
expected_files <- c(
  "kda_run_manifest.tsv",
  "kda_signature_members.tsv.gz",
  "kda_background_members.tsv.gz",
  "kda_results.tsv.gz",
  "kda_key_driver_summary.tsv",
  "kda_qc_summary.tsv",
  "kda_checks.tsv",
  "kda_artifacts.tsv",
  "kda_status.tsv"
)
status <- fread(file.path(root, "kda_status.tsv"))
manifest <- fread(file.path(root, "kda_run_manifest.tsv"))
checks <- fread(file.path(root, "kda_checks.tsv"))
artifacts <- fread(file.path(root, "kda_artifacts.tsv"))
entries <- list.files(root, full.names = TRUE)

stopifnot(
  setequal(list.files(root), expected_files),
  !any(dir.exists(entries)),
  status$schema_version == "mitochondrial_kda_status_v1",
  status$validation_status == "nonfinal_smoke_test",
  status$planned_runs == 165L,
  nrow(manifest) == 165L,
  sum(manifest$analysis_level == "primary") == 90L,
  sum(manifest$analysis_level == "secondary") == 75L,
  uniqueN(manifest$fine_cell_type) == 5L,
  setequal(unique(manifest$signature_direction),
           c("AD_up_mito", "AD_down_mito", "AD_both_mito")),
  identical(unique(manifest$network_id), "Vasculature_cells"),
  !anyDuplicated(manifest$run_id),
  !any(manifest$terminal_status == "failed"),
  all(checks$passed[checks$blocking]),
  all(artifacts$validation_status == "validated_complete")
)
cat("Local Phase 12 KDA smoke test validated successfully\n")
'
```

The local pilot is nonfinal. It validates the shared code path and
Vasculature subset, not the complete 54-fine-cell-type analysis.

## Minerva production: run all 1,782 planned rows

### Input

```text
results/minerva_production/08_mast/
results/minerva_production/09_annotate_genes/
data/bayesian_network/*/result.links3.links.txt
config/minerva_shared.yml
config/minerva_production_execution.yml
config/phase12_kda.yml
scripts/NetWeaver/fKDA.R
```

### Output

```text
results/minerva_production/12_kda/
```

Only the flat nine-file production bundle is published. The complete run
manifest contains 972 primary and 810 secondary planned rows.

### Production preflight

Run from the Minerva repository root on a compute node:

```bash
cd /sc/arion/work/zhuane01/alzheimer

test -r config/phase12_kda.yml
test -r scripts/12_run_kda.R
test -r scripts/NetWeaver/fKDA.R

Rscript -e '
library(data.table)
phase08 <- list.files(
  "results/minerva_production/08_mast",
  pattern = "[.]yu_mast_de_status[.]tsv$", full.names = TRUE)
stopifnot(length(phase08) == 9L)
de_status <- rbindlist(lapply(phase08, fread), fill = TRUE)
ann_status <- fread(
  "results/minerva_production/09_annotate_genes/annotation_status.tsv")
network_paths <- file.path(
  "data/bayesian_network",
  c("Astrocytes", "CAMs", "Excitatory_neurons", "Inhibitory_neurons",
    "Microglia", "OPCs", "Oligodendrocytes", "T_cells",
    "Vasculature_cells"),
  "result.links3.links.txt"
)
stopifnot(
  all(de_status$validation_status == "validated_complete"),
  ann_status$validation_status == "validated_complete",
  length(network_paths) == 9L,
  all(file.exists(network_paths)),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("digest", quietly = TRUE)
)
cat("Minerva Phase 08/09 and network inputs are ready for Phase 12\n")
'
```

The Phase 12 script performs the authoritative schema, checksum, network DAG,
run-grid, signature, background, and package checks.

### Minerva runtime setup

Use an initialized R environment on a compute node, not a login node:

```bash
cd /sc/arion/work/zhuane01/alzheimer

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript -e '
stopifnot(
  getRversion() >= "4.3.3",
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("digest", quietly = TRUE)
)
cat("Phase 12 packages are available\n")
'
```

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase kda \
  --dry-run
```

Expected task graph: exactly one `global:kda` task. Do not set `RDS_ID`, pass
`--rds-id`, or launch one task per RDS. Internal parallelism and scratch-shard
handling belong to `scripts/12_run_kda.R`.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase kda
```

To resume after interruption, rerun the same command. Compatible completed
runs are recognized from the frozen run manifest, code/config/input checksums,
and scratch-shard metadata. Do not use local-pilot outputs for resume.

### Validate production

```bash
Rscript -e '
library(data.table)
root <- "results/minerva_production/12_kda"
expected_files <- c(
  "kda_run_manifest.tsv",
  "kda_signature_members.tsv.gz",
  "kda_background_members.tsv.gz",
  "kda_results.tsv.gz",
  "kda_key_driver_summary.tsv",
  "kda_qc_summary.tsv",
  "kda_checks.tsv",
  "kda_artifacts.tsv",
  "kda_status.tsv"
)
status <- fread(file.path(root, "kda_status.tsv"))
manifest <- fread(file.path(root, "kda_run_manifest.tsv"))
checks <- fread(file.path(root, "kda_checks.tsv"))
artifacts <- fread(file.path(root, "kda_artifacts.tsv"))
entries <- list.files(root, full.names = TRUE)

stopifnot(
  setequal(list.files(root), expected_files),
  !any(dir.exists(entries)),
  status$schema_version == "mitochondrial_kda_status_v1",
  status$validation_status == "validated_complete",
  status$planned_runs == 1782L,
  nrow(manifest) == 1782L,
  sum(manifest$analysis_level == "primary") == 972L,
  sum(manifest$analysis_level == "secondary") == 810L,
  uniqueN(manifest$fine_cell_type) == 54L,
  uniqueN(manifest[group_id %chin% c(
    "F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4"), group_id]) == 6L,
  uniqueN(manifest[group_id %chin% c(
    "female_pool", "male_pool", "e2_pool", "e33_pool", "e4_pool"),
    group_id]) == 5L,
  setequal(unique(manifest$signature_direction),
           c("AD_up_mito", "AD_down_mito", "AD_both_mito")),
  uniqueN(manifest$network_id) == 9L,
  !anyDuplicated(manifest$run_id),
  !any(manifest$terminal_status == "failed"),
  all(checks$passed[checks$blocking]),
  all(artifacts$validation_status == "validated_complete")
)
cat("Minerva Phase 12 KDA production validated successfully\n")
'
```

### Required Minerva output check

- exactly the nine approved flat output files and no subdirectories;
- 54 fine cell types and nine mapped broad networks;
- 972 primary, 810 secondary, and 1,782 total manifest rows;
- all three signature directions represented for every planned group;
- every source-incomplete or query-ineligible run has an explicit reason;
- every eligible run has a completed terminal status, including explicit
  no-significant-driver outcomes;
- no failed run or duplicated run ID;
- all blocking checks and artifact checksums pass; and
- no local-pilot result or checksum appears in production provenance.

## Required scientific and provenance checks

### Input checks

- All required Phase 08 and Phase 09 files exist and match checksums.
- All inherited status files are validated.
- Exactly 54 fine cell types and six strata are represented.
- Exactly nine final Bayesian networks are present.
- Every fine cell type maps to exactly one approved network.
- Every network is a directed acyclic graph.
- Network direction is first column to second column.

### Run-grid checks

- Exactly 972 primary rows exist.
- Exactly 810 secondary rows exist.
- Exactly 1,782 total required rows exist.
- Every fine cell type has 18 primary and 15 secondary planned rows.
- Run IDs are unique and deterministic.
- No planned row is silently removed.

### Signature checks

- Every primary query gene is a Phase 08 `paper_deg`.
- Every required-profile query gene has the approved mitochondrial tier.
- Primary up and down sets are disjoint.
- `AD_both_mito` equals the exact union of up and down.
- Pooled members match the frozen membership table.
- Pooled direction-discordant genes are explicitly reported.
- No signature contains duplicate network identifiers.

### Background and network checks

- Every primary background comes from its exact Phase 08 contrast.
- Every pooled background is the tested-gene intersection across all members.
- Every effective background gene is a node in the matching induced network.
- Every effective query is a subset of its background.
- `bg.size` equals the exact effective background size.
- Every induced edge occurs in the matching final network.
- No induced network contains a self-edge, duplicate edge, or cycle.

### KDA numerical checks

- Primary parameters match the frozen configuration.
- Returned `BestLayer` is between 1 and 3.
- `q <= m`, `q <= k`, and all count columns are nonnegative.
- Reported fold enrichment is independently reproduced.
- `exp(log.P.Value)` is finite and within `[0, 1]`.
- Adjusted P values are finite and within `[0, 1]`.
- Every overlap item belongs to both the effective query and the tested
  driver neighborhood.
- A known synthetic upstream driver is recovered.
- Reversing synthetic edges removes or changes that upstream result.

### Empty and failed-run checks

- Ineligible rows have an explicit prespecified skip reason.
- Eligible `NULL` results are recorded as completed with no significant
  driver.
- Failed runs are distinct from ineligible and no-result runs.
- Every eligible row has exactly one terminal status.
- The final result and summary tables reconcile exactly with the run manifest
  and the temporary task shards at combination time.

### Provenance checks

- Every input and output artifact has a SHA-256.
- The KDA source and configuration checksums are recorded.
- Git revision, R environment, parameters, start time, and finish time are
  recorded.
- Compatible completed runs are resumable by checksum.
- An incompatible partial output is never silently reused or overwritten.

## Acceptance criteria

### Structural gate

- All 1,782 planned rows are present.
- Every eligible run is completed exactly once.
- Every ineligible run has one valid skip reason.
- Output schemas and artifact checksums pass.

### Scientific gate

- Primary and secondary groups match the approved definitions.
- Up, down, and combined signatures are constructed exactly.
- Every query and background uses the matching fine cell type and network.
- Pooled signatures remain labeled as set-union summaries.
- No result is interpreted as activation, inhibition, or proven causality.

### Reproducibility gate

- A clean rerun from frozen inputs reproduces membership and numeric outputs.
- Compatible output reuse is checksum-valid.
- Pilot and production directories and artifacts remain completely separate.
- An independent arithmetic audit passes for sampled driver rows.

## Interpretation and downstream handoff

The main scientific results will be the six stratum-specific analyses.
Secondary pools summarize recurrence across related strata but cannot replace
the primary results or erase direction discordance.

Driver prioritization after Phase 12 may consider:

- recurrence across related fine cell types;
- recurrence across sex/APOE groups;
- agreement between up, down, and combined signatures;
- global-key-driver flag;
- neighborhood size and query coverage;
- robustness across approved sensitivities;
- AD genetic or QTL support; and
- independent perturbation evidence.

These evidence layers are downstream interpretation tasks. They must remain
separate from the KDA enrichment statistic.

Phase 12 completion provides validated data tables, not final figures.

## Completion criteria

Phase 12 is complete only when:

1. this design has been reviewed and frozen in configuration;
2. all inherited inputs and nine final networks pass preflight;
3. the complete 1,782-row run grid is published;
4. all eligible primary and secondary runs have terminal outcomes;
5. all query, background, pooled-membership, QC, result, and provenance tables
   are published;
6. the scientific, numerical, structural, and reproducibility gates pass; and
7. `kda_status.tsv` reports `validated_complete`.

Until then, the phase remains `planned`, `implemented_not_run`, `pilot`, or
`production_incomplete`, as appropriate.

## Review checklist

Please review and approve or revise these decisions before implementation:

- [ ] Exactly three signatures: AD-up, AD-down, and their union.
- [ ] Six primary strata for every fine cell type.
- [ ] Five secondary pools for every fine cell type.
- [ ] Strict complete-member requirement for every pool.
- [ ] Any-member union rule for pooled DEG signatures.
- [ ] Explicit reporting of direction-discordant pooled genes.
- [ ] `core_mito_protein` as the required mitochondrial universe.
- [ ] Intersection of member tested-gene sets as the pooled background.
- [ ] Induced run-specific networks for consistent `bg.size` use.
- [ ] NetWeaver `call_key_drivers()` as the required KDA engine.
- [ ] Three directed layers and the other frozen KDA defaults.
- [ ] Minimum effective query size of three, with a warning below ten.
- [ ] Broad-network reuse across matching fine-cell-type signatures.
- [ ] Flat nine-file phase bundle with no permanent per-run directories.
- [ ] Local-pilot and Minerva-production outputs remain completely separate.
- [ ] Optional sensitivities remain outside the required production grid.
