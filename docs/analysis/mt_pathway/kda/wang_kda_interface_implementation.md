# Wang KDA maintained-interface implementation

## Scope

This document describes the project-maintained R interface around Wang's KDA
0.2 package: its architecture, scientific choices, input construction,
validation, caching, and tests.

For package installation, see
[wang_kda_package_installation.md](wang_kda_package_installation.md). For
commands used to run an analysis, see
[wang_kda_interface_usage.md](wang_kda_interface_usage.md).

## Source-code boundary

Wang's unmodified third-party package and reference PHG scripts remain under:

```text
archive/wang_kda_code/
```

They must not be edited to make the project analysis run. Project-maintained
code lives under:

```text
scripts/analysis/kda/
```

This separation keeps comparisons with the upstream Wang repository auditable.

## Implemented layout

```text
scripts/analysis/kda/
├── install_kda.R
├── prepare_kda_inputs.R
├── run_global_kda.R
├── run_signature_enrichment.R
├── run_kda_pipeline.R
├── run_global_kda_minerva.lsf
├── smoke_test_kda.R
└── lib/
    ├── cli.R
    ├── kda_io.R
    ├── kda_core.R
    ├── kda_enrichment.R
    └── kda_validation.R
```

Responsibilities:

- `install_kda.R` verifies and installs KDA 0.2.
- `prepare_kda_inputs.R` constructs queries, exact MAST backgrounds, query QC,
  and the run manifest.
- `run_global_kda.R` performs one global driver search for one broad network.
- `run_signature_enrichment.R` tests one biological query against cached
  driver neighborhoods.
- `run_kda_pipeline.R` orchestrates/resumes the two stages and serially
  combines completed enrichment results.
- `smoke_test_kda.R` tests package behavior, directionality, enrichment
  arithmetic, and validation failures.
- `lib/` contains reusable functions without command-line side effects.

## Scientific design

### Why the interface has two stages

The maintained default follows the design used in Wang's scripts:

1. discover structural/global driver candidates once for each broad
   cell-type Bayesian network;
2. extract each candidate's directed downstream neighborhood; and
3. test each fine-cell/sex/APOE mitochondrial DEG signature for enrichment in
   those neighborhoods using the matching measurable background.

Global KDA is expensive and depends on the network, not on a particular
contrast. It is therefore cached once per network checksum. Contrast-specific
enrichment is inexpensive and can reuse that cache.

### Stage A: global candidate discovery

For each broad network, the wrapper:

1. reads the headerless two-column edge list;
2. labels the columns `from` and `to`;
3. treats column 1 as upstream and column 2 as downstream;
4. validates the network as a DAG;
5. uses every network node as the KDA signature;
6. calls directed KDA with a six-layer search by default;
7. retains every candidate row returned by KDA, not just rows whose final
   `keydriver` flag equals one;
8. saves all three raw KDA return elements; and
9. extracts three-layer directed downstream neighborhoods by default.

The seed/driver is removed from its neighborhood before enrichment unless the
explicit compatibility option is enabled.

### Stage B: signature enrichment

For each biological run:

1. load the matching effective query and exact contrast background;
2. intersect each cached neighborhood with the background;
3. count effective-query overlap;
4. compute a one-sided hypergeometric P value;
5. compute fold enrichment;
6. apply BH correction across all candidate drivers within that signature;
7. retain overlap-gene membership and query-coverage diagnostics; and
8. report the Wang global `keydriver` flag separately.

For background size \(N\), query size \(K\), background-restricted
neighborhood size \(n\), and overlap \(k\):

```r
p_value <- phyper(
  q = k - 1,
  m = K,
  n = N - K,
  k = n,
  lower.tail = FALSE
)

fold_enrichment <- (k / n) / (K / N)
```

When `n` is zero, the interface returns `p_value = 1` and
`fold_enrichment = NA` rather than evaluating `0 / 0`.

## Phase 08/09 input construction

### Background definition

The background for one run is:

```text
genes returned/tested by MAST in that exact Phase 08 contrast
    ∩
nodes in the matching broad Bayesian network
```

It is not all assay genes, all network nodes, the annotation master's
`test_eligible` set, or a background borrowed from another contrast.

### Identifier policy

Network matching uses the original Phase 08 assay identifier:

```text
Phase 08 gene
    =
Phase 09 feature_id_original
```

The interface deliberately does not replace that key with
`symbol_hgnc_current`. These Bayesian networks were built from the assay
identifiers, and replacing them with current symbols reduces network coverage.
Current HGNC symbols and mapping status are retained as diagnostic annotation.

### Query definitions

The primary query universe is:

```text
mito_tier == core_mito_protein
```

The optional `all_mito_related` sensitivity universe adds:

```text
mito_extended
mtdna_noncoding
```

Within either universe, Phase 08 `paper_deg == TRUE` is the frozen DEG
definition. The three directions are:

- `all_mito`: both logFC signs;
- `AD_up_mito`: `logFC > 0`; and
- `AD_down_mito`: `logFC < 0`.

The Phase 08 paper DEG rule is:

```text
fdr_bh_within_contrast < 0.05
AND abs(logFC) > log2(1.3)
AND (pct_ad >= 0.10 OR pct_nci >= 0.10)
```

Input preparation trusts the frozen `paper_deg` field and records the rule in
the generated manifest.

### Fine-to-broad network mapping

The mapping is explicit and unknown values fail:

| Phase 08 input/fine type | Broad network |
|---|---|
| `astrocytes`, all `Ast*` | `Astrocytes` |
| `excitatory_set1/2/3`, all `Exc*` | `Excitatory_neurons` |
| `inhibitory`, all `Inh*` | `Inhibitory_neurons` |
| `opcs`, `OPC` | `OPCs` |
| `oligodendrocytes`, `Oli` | `Oligodendrocytes` |
| `vasculature`, `End`, `Fib FLRT2`, `Fib SLC4A4`, `Per`, or `SMC` | `Vasculature_cells` |
| `immune`, `CAMs` | `CAMs` |
| `immune`, `Mic MKI67`, `Mic P2RY12`, or `Mic TPT1` | `Microglia` |
| `immune`, `T cells` | `T_cells` |

### Small queries

Input preparation documents all 963 primary direction-specific candidate
runs. It does not abort the whole preparation when one query is too small.
Rows with fewer than three effective network-mapped genes receive:

```text
eligible = FALSE
skip_reason = effective_query_lt_3
```

The validated primary input set contains 494 eligible and 469 ineligible
rows. Runners reject an explicitly requested ineligible run; a full-manifest
pipeline skips it.

## KDA package functions and quirks

### `keydriverInSubnetwork()`

Global discovery calls:

```r
KDA::keydriverInSubnetwork(
  linkpairs,
  signature = all_network_nodes,
  background = NULL,
  directed = TRUE,
  nlayers = 6,
  enrichedNodes_percent_cut = -1,
  FET_pvalue_cut = 0.05,
  boost_hubs = TRUE,
  dynamic_search = TRUE,
  bonferroni_correction = TRUE,
  expanded_network_as_signature = FALSE
)
```

The `background` parameter in this package function is not a background gene
vector. The global wrapper therefore passes `NULL`; contrast backgrounds are
used only in the maintained external enrichment stage.

The function returns either `NULL` or an unnamed three-element list:

```text
[[1]] candidate-driver matrix
[[2]] cutoff/parameter matrix
[[3]] all-node downstream-count matrix
```

The matrices are character-coerced. The wrapper validates column names and
explicitly converts numeric fields. A `NULL` return after validating a network
with at least five nodes is represented as a legitimate empty candidate
result.

In all-node global mode, `fold_change_whole = 0` and `pvalue_whole = 1` are
package initialization placeholders and should not be interpreted
scientifically.

The parameter matrix's `cut_downstream` value can contain a semicolon-repeated
vector because of a KDA 0.2 package bug. It is preserved as raw text.

### `downStreamGenes()`

Neighborhood extraction calls:

```r
KDA::downStreamGenes(
  netpairs,
  seednodes,
  N = 3,
  directed = TRUE
)
```

Direction is column 1 to column 2. Successful results include the seed node.
A leaf or unknown seed returns `NULL`. The generic wrapper normalizes `NULL`
to an empty character vector and removes the seed by default.

Layer counts must be positive scalar integers. KDA 0.2 silently gives
unexpected behavior for values such as zero or `1.5`, so the maintained
interface rejects them before calling the package.

### Why `keyDriverAnalysis()` is not the default

KDA also exports a high-level `keyDriverAnalysis()` wrapper, but it:

- does not accept an actual background gene vector;
- mixes expansion/search direction choices;
- returns only internally selected drivers;
- character-coerces result columns; and
- has an output/visualization path that fails in the current environment.

The maintained workflow therefore calls the lower-level functions directly.

## Reusable in-memory API

The primary reusable function is:

```r
run_celltype_kda <- function(
  network,
  signatures,
  backgrounds,
  driver_search_layers = 6L,
  enrichment_layers = 3L,
  include_driver_in_neighborhood = FALSE,
  boost_hubs = TRUE,
  p_adjust_method = "BH",
  alpha = 0.05
)
```

It returns:

```r
list(
  run_manifest = ...,
  query_coverage = ...,
  global_drivers = ...,
  neighborhoods = ...,
  enrichment = ...,
  significant_drivers = ...,
  raw_kda = ...
)
```

The file-backed stage runners use the same core and enrichment functions.

## Input contracts

### Network

The network is a headerless TSV with exactly two fields per physical line:

```text
REGULATOR_X    GENE_Y
GENE_Y         TOMM7
```

The first field is upstream. The second is downstream.

### Membership files

Signature and background files are long-form TSVs:

```text
run_id    gene
RUN_A     TUFM
RUN_A     TOMM7
```

Shared membership files are filtered by `run_id`.

### Run manifest

Required columns are:

```text
run_id
network_id
network_path
fine_cell_type
sex
apoe_group
comparison
query_direction
signature_path
background_path
```

Prepared manifests additionally record contrast identity, query universe,
mitochondrial tiers, identifier policy, DEG rules, original/effective sizes,
eligibility, and unmapped query genes. Paths are repository-root-relative
unless absolute paths are supplied.

## Validation and safety

The interface fails on:

- KDA other than version 0.2 or missing required exports;
- wrong archive checksum;
- network rows with other than two fields;
- a header, missing identifiers, duplicate edges, self-edges, or cycles;
- ambiguous direction;
- duplicate or unsafe `run_id` values;
- a missing matching signature/background;
- a background that is not a network-node subset;
- an effective query with fewer than three genes;
- malformed KDA return objects or inconsistent downstream counts;
- zero, fractional, missing, or non-finite layer values; and
- incompatible or partial output directories unless `--force` is explicit.

Warnings cover small but valid queries, low coverage, no significant driver,
and candidate drivers absent from the contrast background.

Completed output reuse is keyed by input checksums and all relevant analysis
parameters. A compatible run is reused. An incompatible completed run fails
unless the user explicitly requests `--force` or chooses a new output
directory.

Per-run jobs do not concurrently modify shared combined tables. Combination is
a separate serial operation.

## Provenance

Run manifests record, as applicable:

- Git commit;
- R and KDA versions;
- the Wang paper/package version-label discrepancy;
- package-archive checksum;
- network, signature, background, and global-manifest checksums;
- direction, layer, hub, FET, correction, and driver-inclusion settings;
- original/effective query and background sizes;
- candidate/significant driver counts; and
- UTC start/end time, elapsed seconds, and completion status.

The exact raw KDA object is saved as `raw_kda.rds`. Separate raw driver,
parameter, and downstream-count TSVs keep all three return elements
inspectable without R.

## Verification status

The implementation has passed:

- syntax parsing for all maintained R files;
- exact KDA 0.2 version/export checks;
- directed-star recovery of `DRIVER1`;
- reversed-edge rejection of the same upstream interpretation;
- one-, two-, and three-layer reachability checks;
- default seed exclusion and compatibility inclusion;
- exact hypergeometric and fold-enrichment references;
- within-signature BH adjustment;
- malformed network/query/background/KDA failures;
- file-backed global and signature-enrichment execution;
- compatible-output resume and serial combination;
- strict reading of the real Bayesian networks; and
- complete Phase 08/09 input preparation in a disposable directory.

The validated `Mic P2RY12`, male, APOE e2 pilot input has:

| Quantity | Count |
|---|---:|
| Phase 08 tested genes | 4,337 |
| Microglia network-mapped background | 4,233 |
| Core all-direction query, original/effective | 88 / 87 |
| Core AD-up query, original/effective | 41 / 41 |
| Core AD-down query, original/effective | 47 / 46 |

`PIM1` is retained as the unmapped core query diagnostic.

Real-network global KDA and production enrichment have not yet been run by
this implementation task.

