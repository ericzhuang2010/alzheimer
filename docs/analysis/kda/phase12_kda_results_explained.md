# From Phase 12 KDA tables to the NetWeaver circular figure

## Purpose of this document

This document explains, from beginning to end:

1. what Phase 12 analyzed;
2. what data Phase 12 produced;
3. the format and meaning of every Phase 12 output file;
4. which files were used for the NetWeaver circular figure;
5. every selection, denominator, transformation, and plotting operation used
   to make the figure; and
6. how to interpret the figure scientifically.

The validated Phase 12 production bundle is:

```text
results/minerva_production/12_kda/
```

The figure-generation code is:

```text
scripts/figures/visualize_phase12_kda_netweaver.R
```

The generated files are:

```text
results/figures/phase12_kda/
├── phase12_kda_netweaver.svg
├── phase12_kda_netweaver.png
└── phase12_kda_netweaver_plotted_data.tsv
```

The SVG and PNG contain the same figure. The SVG is an editable vector image.
The PNG is a 3600 by 3600 pixel, 300-dpi raster image. The plotted-data TSV is
the audit table connecting each displayed sector to its source values and
derived plotting values.

## 1. What Phase 12 analyzed

### 1.1 Scientific question

Phase 12 asks whether a cell-type-specific mitochondrial AD-versus-NCI gene
signature is enriched in the downstream neighborhood of particular genes in a
cell-type-matched Bayesian network.

Informally, for each analysis, Phase 12 asks:

> In this fine cell type and sex/APOE group, are mitochondrial genes that are
> altered in AD unusually concentrated downstream of a candidate network
> driver?

If the answer is statistically significant after within-run multiple-testing
correction, NetWeaver reports that candidate as a potential key driver for
that run.

This is a network-neighborhood enrichment analysis. It is not a differential
expression test, and it is not direct experimental evidence of causality.

### 1.2 Fine cell types and broad networks

Phase 12 contains 54 fine cell types mapped to nine broad Bayesian networks:

```text
Astrocytes
CAMs
Excitatory_neurons
Inhibitory_neurons
Microglia
OPCs
Oligodendrocytes
T_cells
Vasculature_cells
```

The production run had eligible KDA analyses in seven of these networks.
CAMs and T cells had no eligible KDA run because their effective
mitochondrial queries did not satisfy the input requirements. Therefore,
those two networks have planned manifest rows but no reported key-driver
rows.

This is an eligibility outcome, not evidence that CAMs and T cells have no
biological key drivers.

### 1.3 Primary groups

The primary analysis uses six sex/APOE groups:

| `signature_group` | Sex | APOE group |
|---|---|---|
| `F_e2` | Female | e2 |
| `F_e33` | Female | e33 |
| `F_e4` | Female | e4 |
| `M_e2` | Male | e2 |
| `M_e33` | Male | e33 |
| `M_e4` | Male | e4 |

For each fine cell type, each group is tested with three mitochondrial
signature directions:

| `signature_direction` | Meaning |
|---|---|
| `AD_up_mito` | Mitochondrial genes higher in AD than NCI |
| `AD_down_mito` | Mitochondrial genes lower in AD than NCI |
| `AD_both_mito` | Union of the AD-up and AD-down mitochondrial genes |

The primary grid therefore contains:

```text
54 fine cell types × 6 groups × 3 directions = 972 planned runs
```

### 1.4 Secondary pools

The secondary analysis uses five prespecified pools:

| `signature_group` | Source groups |
|---|---|
| `female_pool` | `F_e2`, `F_e33`, `F_e4` |
| `male_pool` | `M_e2`, `M_e33`, `M_e4` |
| `e2_pool` | `F_e2`, `M_e2` |
| `e33_pool` | `F_e33`, `M_e33` |
| `e4_pool` | `F_e4`, `M_e4` |

Each pool is also analyzed in the three signature directions:

```text
54 fine cell types × 5 pools × 3 directions = 810 planned runs
```

These pools are set-union summaries over related primary groups. They are not
independent biological replications, because the pools overlap and reuse
primary-group information.

### 1.5 Complete analysis grid

Together, Phase 12 planned:

```text
972 primary runs + 810 secondary runs = 1,782 planned runs
```

The validated production status reports:

| Quantity | Value |
|---|---:|
| Fine cell types | 54 |
| Broad networks | 9 |
| Planned runs | 1,782 |
| Eligible runs | 1,021 |
| Skipped runs | 761 |
| Failed runs | 0 |
| Runs with at least one significant driver | 840 |
| Significant key-driver result rows | 10,172 |
| Failed validation checks | 0 |
| Validation status | `validated_complete` |

### 1.6 How the query and background are constructed

For one planned run, Phase 12 constructs the inputs in this order:

1. Select the Phase 08 AD-versus-NCI result for the matching fine cell type
   and primary group, or the set of results that defines a secondary pool.
2. Use the validated Phase 09 gene annotations to restrict the signature to
   the configured mitochondrial universe, `core_mito_protein`.
3. Build one of the three candidate signatures: AD-up, AD-down, or their
   union.
4. Identify the exact genes tested in every required source contrast. For a
   secondary pool, the tested-gene set is the intersection of its source
   groups.
5. Restrict the matching broad Bayesian network to edges whose two endpoints
   are in that exact tested-gene set. This is the run-specific induced
   network.
6. Define the effective background as the unique nodes appearing in that
   induced network.
7. Intersect the candidate mitochondrial signature with the effective
   background. This produces the effective query.
8. Mark the run eligible only if its sources are validated, the induced
   network is nonempty, and the effective query contains at least three
   genes.

Consequently, two runs that use the same broad network may still have
different induced networks, backgrounds, and effective mitochondrial
queries.

### 1.7 What NetWeaver tests in one eligible run

The frozen Phase 12 configuration uses:

```text
maximum neighborhood layer:       3
signature expansion layers:       0
directed network:                 TRUE
global-driver reduction distance: 2
significance cutoff:              BH-adjusted P <= 0.05
overlap genes returned:           TRUE
```

For a candidate driver and a particular network layer, define:

| Symbol | Phase 12 column | Meaning |
|---|---|---|
| \(M\) | `neighborhood_size + non_neighborhood_size` | Effective background size |
| \(m\) | `neighborhood_size` | Number of genes in the driver's directed neighborhood |
| \(k\) | `signature_size` | Number of effective mitochondrial query genes |
| \(q\) | `overlap_count` | Query genes in the driver's neighborhood |

The fold enrichment is:

```text
fold_enrichment = (q / m) / (k / M)
                = q × M / (m × k)
```

NetWeaver calculates an upper-tail hypergeometric P value for observing at
least \(q\) query genes in a neighborhood of size \(m\), given \(k\) query
genes in a background of size \(M\). It evaluates neighborhood layers up to
three and retains the best layer for each candidate driver. It then applies
Benjamini-Hochberg correction across the candidate drivers tested in that
run. Only drivers with adjusted P values at or below 0.05 are returned.

For example, the first result row for `RPL13` has:

```text
q = 2
m = 18
n = 6,925
M = m + n = 6,943
k = 6
```

Its fold enrichment is:

```text
2 × 6,943 / (18 × 6) = 128.574...
```

which is stored, after the NetWeaver rounding convention, as `128.57`.

## 2. General Phase 12 file format

Every Phase 12 output is a tab-separated text table.

- Files ending in `.tsv` are plain text.
- Files ending in `.tsv.gz` are the same tab-separated format compressed with
  gzip.
- The first line is a header.
- Each later line is one data row.
- Every table has a `schema_version` column.
- Logical values are written as `TRUE` or `FALSE`.
- Missing values, when present, are represented as `NA`.
- Multiple identifiers stored in one field are separated with semicolons.
- The stable join key for run-level tables is `kda_run_id`.

Small tables can be read in base R:

```r
phase12_dir <- "results/minerva_production/12_kda"

manifest <- read.delim(
  file.path(phase12_dir, "kda_run_manifest.tsv"),
  sep = "\t",
  quote = "",
  check.names = FALSE
)

results <- read.delim(
  gzfile(file.path(phase12_dir, "kda_results.tsv.gz")),
  sep = "\t",
  quote = "",
  check.names = FALSE
)
```

The background-membership table has more than 12.5 million rows. It should
usually be filtered or processed with a streaming or high-performance table
reader rather than loaded unnecessarily into a small-memory R session.

## 3. The nine files produced by Phase 12

The production directory contains exactly nine files:

| File | Compression | Data rows | Approximate size | Grain |
|---|---|---:|---:|---|
| `kda_run_manifest.tsv` | None | 1,782 | 590 KB | One row per planned KDA run |
| `kda_signature_members.tsv.gz` | gzip | 53,022 | 249 KB | One candidate signature gene per run |
| `kda_background_members.tsv.gz` | gzip | 12,506,736 | 46 MB | One background gene per run |
| `kda_results.tsv.gz` | gzip | 10,172 | 329 KB | One significant driver per run |
| `kda_key_driver_summary.tsv` | None | 889 | 87 KB | One broad-network–driver pair |
| `kda_qc_summary.tsv` | None | 108 | 12 KB | One tier–network–fine-cell-type group |
| `kda_checks.tsv` | None | 11 | 778 bytes | One validation check |
| `kda_artifacts.tsv` | None | 38 | 6.8 KB | One input/output artifact |
| `kda_status.tsv` | None | 1 | 3.0 KB | One production-run status record |

The row counts above exclude the header.

### 3.1 `kda_run_manifest.tsv`

Schema:

```text
mitochondrial_kda_run_manifest_v1
```

This is the backbone of the Phase 12 output. It contains all 1,782 planned
runs, including eligible runs, skipped runs, runs with no significant driver,
and runs with significant drivers.

It is the correct file to use when a denominator must include zero-result or
skipped analyses. Using only `kda_results.tsv.gz` would silently discard those
runs.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `kda_run_id` | Unique, stable identifier for one planned KDA analysis |
| `analysis_tier` | `primary` or `secondary` |
| `fine_cell_type` | Fine cell type used to obtain the signature and network mapping |
| `broad_network` | Broad Bayesian network used for KDA |
| `signature_group` | Primary sex/APOE group or secondary pool |
| `source_groups` | Semicolon-separated primary groups contributing to the signature |
| `source_contrast_ids` | Semicolon-separated Phase 08 contrast identifiers |
| `source_terminal_statuses` | Validation status of the contributing Phase 08 contrasts |
| `signature_direction` | `AD_up_mito`, `AD_down_mito`, or `AD_both_mito` |
| `candidate_query_genes` | Mitochondrial signature size before intersection with the effective network background |
| `effective_query_genes` | Signature genes present in the run-specific background |
| `exact_tested_genes` | Genes tested in the required source contrast, or their intersection for a pool |
| `induced_network_edges` | Edges remaining after restricting the matched broad network to exact tested genes |
| `effective_background_genes` | Unique nodes in the induced network |
| `eligibility_status` | `eligible` or a reason that KDA could not be run |
| `terminal_status` | Completed, skipped, or failed status for the run |
| `significant_key_drivers` | Number of significant result rows returned for this run |
| `elapsed_seconds` | Time spent in the KDA call |
| `message` | Error message when a KDA error occurred; empty for normal runs |

The production bundle contains the following important terminal outcomes:

- `completed_significant`: eligible and at least one driver passed the cutoff;
- `completed_no_significant`: eligible but no driver passed the cutoff;
- `skipped_effective_query_below_minimum`: fewer than three effective query
  genes;
- `skipped_source_contrast_not_validated`: at least one required source
  contrast was unavailable or nonfinal; and
- `failed`: the KDA computation itself failed.

There were zero failed runs in production.

### 3.2 `kda_signature_members.tsv.gz`

Schema:

```text
mitochondrial_kda_signature_members_v1
```

This is a long-form audit table of the candidate mitochondrial signatures.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `kda_run_id` | Run to which the candidate gene belongs |
| `gene` | Candidate mitochondrial signature gene |
| `effective_member` | Whether the gene is in the run-specific effective background |
| `exclusion_reason` | Empty for effective genes; otherwise why the candidate was excluded |

In this production configuration, the usual exclusion reason is:

```text
not_in_effective_background
```

To reconstruct the exact query used for one run, retain rows with:

```r
effective_member == TRUE
```

### 3.3 `kda_background_members.tsv.gz`

Schema:

```text
mitochondrial_kda_background_members_v1
```

This is the largest Phase 12 table. It records every gene in every
run-specific effective network background.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `kda_run_id` | Run whose background contains the gene |
| `gene` | A unique node in the run-specific induced network |

This table supports exact reproduction of enrichment denominators and
independent checks that signatures and returned key drivers belong to the
correct background.

### 3.4 `kda_results.tsv.gz`

Schema:

```text
mitochondrial_kda_results_v1
```

This is the detailed scientific result table. It contains only significant
key-driver calls returned by completed KDA runs. It does not contain explicit
zero rows for eligible runs with no significant driver and does not contain
skipped runs.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `kda_run_id` | Run in which the driver was significant |
| `analysis_tier` | `primary` or `secondary` |
| `fine_cell_type` | Fine cell type for the run |
| `broad_network` | Broad network for the run |
| `signature_group` | Primary group or secondary pool |
| `signature_direction` | AD-up, AD-down, or combined signature |
| `key_driver` | Candidate gene whose neighborhood was enriched |
| `best_layer` | Network-neighborhood layer, from 1 to 3, giving the retained result |
| `overlap_count` | Number \(q\) of effective query genes in the neighborhood |
| `neighborhood_size` | Number \(m\) of background genes in the neighborhood |
| `non_neighborhood_size` | Number \(n = M-m\) of background genes outside the neighborhood |
| `signature_size` | Number \(k\) of effective query genes |
| `fold_enrichment` | \((q/m)/(k/M)\), rounded by the KDA implementation |
| `log_p_value` | Natural logarithm of the unadjusted upper-tail hypergeometric P value |
| `adjusted_p_value` | Benjamini-Hochberg-adjusted P value within the run |
| `is_signature` | Whether the driver itself is in the effective query; this may be `NA` in a single-result edge case |
| `is_root_node` | Whether the driver has no incoming edge in the run-specific directed network |
| `global_key_driver` | NetWeaver's within-run reduction flag |
| `overlap_items` | Semicolon-separated query genes covered by the driver's neighborhood |

In directed mode, `global_key_driver = TRUE` means that the reported driver
was not downstream, within the configured two-layer reduction window, of
another significant driver in that same run. If only one driver is
significant in a run, NetWeaver marks it as global.

This flag does not mean that the driver is global across cell types, networks,
sexes, APOE groups, or the whole study.

### 3.5 `kda_key_driver_summary.tsv`

Schema:

```text
mitochondrial_kda_key_driver_summary_v1
```

This is a compact recurrence summary derived from
`kda_results.tsv.gz`. It is the primary source of the values displayed in the
circular figure.

Only significant key-driver rows are summarized. A candidate driver that was
tested but never passed the within-run adjusted-P-value threshold does not
appear in this table.

The grain is one `broad_network`–`key_driver` pair:

```r
key_driver_summary <- results[, .(
  significant_runs = uniqueN(kda_run_id),
  fine_cell_types = uniqueN(fine_cell_type),
  primary_runs = uniqueN(kda_run_id[analysis_tier == "primary"]),
  secondary_runs = uniqueN(kda_run_id[analysis_tier == "secondary"]),
  global_calls = sum(global_key_driver %in% TRUE, na.rm = TRUE),
  minimum_adjusted_p_value = min(adjusted_p_value, na.rm = TRUE),
  maximum_fold_enrichment = max(fold_enrichment, na.rm = TRUE)
), by = .(broad_network, key_driver)]
```

The same gene can therefore appear more than once if it is significant in
more than one broad network.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `broad_network` | Broad network in which the driver was reported |
| `key_driver` | Driver gene |
| `significant_runs` | Number of distinct `kda_run_id` values in which this driver was significant in this broad network |
| `fine_cell_types` | Number of distinct fine cell types represented among those significant runs |
| `primary_runs` | Number of distinct significant runs for individual sex/APOE groups |
| `secondary_runs` | Number of distinct significant runs for pooled groups such as `female_pool`, `male_pool`, or `e4_pool` |
| `global_calls` | Number of significant result rows in which `global_key_driver` is `TRUE` |
| `minimum_adjusted_p_value` | Smallest adjusted P value observed across the summarized runs |
| `maximum_fold_enrichment` | Largest fold enrichment observed across the summarized runs |

By construction:

```text
significant_runs = primary_runs + secondary_runs
```

This summary collapses across:

- fine cell types;
- sex/APOE primary groups;
- secondary pools; and
- AD-up, AD-down, and combined signature directions.

For example, the production summary contains approximately the following row:

```text
broad_network:               Astrocytes
key_driver:                  RPL13
significant_runs:            21
fine_cell_types:             3
primary_runs:                8
secondary_runs:              13
global_calls:                19
minimum_adjusted_p_value:    9.76e-06
maximum_fold_enrichment:     128.57
```

This means that `RPL13` was reported as a significant key driver in 21
Astrocytes-network runs spanning three fine astrocyte cell types. Eight calls
were from primary sex/APOE analyses, 13 were from secondary pooled analyses,
and 19 of the 21 calls had `global_key_driver = TRUE`. The smallest adjusted P
value observed across those calls was approximately \(9.76 \times 10^{-6}\),
and the largest fold enrichment was 128.57.

This file is a descriptive recurrence summary, not a new statistical test or
meta-analysis:

- `minimum_adjusted_p_value` is the best individual adjusted P value rather
  than a combined P value.
- `maximum_fold_enrichment` is the largest individual enrichment.
- The minimum P value and maximum fold enrichment may come from different
  runs.
- Primary and pooled secondary calls are not independent replications because
  pooled analyses reuse information from their member groups.
- A high `significant_runs` value indicates recurrence across configured
  analyses, not the same number of independent biological replications.

It is useful for a study overview, but `kda_results.tsv.gz` is required to
identify the particular run, group, signature direction, fine cell type,
best layer, and overlap genes underlying each summarized call.

### 3.6 `kda_qc_summary.tsv`

Schema:

```text
mitochondrial_kda_qc_summary_v1
```

The grain is one `analysis_tier`–`broad_network`–`fine_cell_type`
combination. There are two rows per fine cell type, one primary and one
secondary.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `analysis_tier` | Primary or secondary |
| `broad_network` | Broad network |
| `fine_cell_type` | Fine cell type |
| `planned_runs` | Number of planned runs in the group |
| `eligible_runs` | Runs that passed input eligibility |
| `skipped_runs` | Runs skipped for an explicit reason |
| `failed_runs` | Runs whose KDA computation failed |
| `significant_runs` | Runs with at least one significant driver |
| `no_significant_runs` | Eligible runs with no significant driver |
| `candidate_query_genes` | Sum of candidate signature sizes across the grouped runs |
| `effective_query_genes` | Sum of effective signature sizes across the grouped runs |
| `significant_key_drivers` | Total detailed result rows across the grouped runs |
| `elapsed_seconds` | Total KDA runtime across the grouped runs |

The candidate and effective query fields in this file are sums over runs, not
counts of unique genes.

### 3.7 `kda_checks.tsv`

Schema:

```text
mitochondrial_kda_checks_v1
```

This table records the structural and scientific validation gates that had to
pass before the output bundle could be published.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `check_id` | Stable validation-check name |
| `severity` | Validation severity |
| `observed` | Observed value |
| `expected` | Required value |
| `passed` | Whether observed equals expected |

The 11 production checks cover fine-cell and network counts, primary and
secondary grid sizes, run-ID uniqueness, source representation, KDA failures,
mitochondrial signature membership, effective-query background membership,
and network acyclicity. All 11 passed.

### 3.8 `kda_artifacts.tsv`

Schema:

```text
mitochondrial_kda_artifacts_v1
```

This is the provenance and integrity inventory.

| Column | Meaning |
|---|---|
| `schema_version` | Table schema identifier |
| `artifact_role` | Role of the input or output |
| `path` | Project-relative artifact path |
| `sha256` | SHA-256 checksum |
| `bytes` | File size in bytes |

It records the Phase 12 configuration, KDA source, Phase 08 and Phase 09
inputs, nine networks, and the hashable Phase 12 output artifacts. It permits
detection of an input or output file that has changed after production.

### 3.9 `kda_status.tsv`

Schema:

```text
mitochondrial_kda_status_v1
```

This is one phase-level status and provenance row.

The columns fall into four groups:

1. **Execution identity:** `execution_stage`, `execution_phase`, `backend`,
   `execution_run_id`, `stable_task_id`, and `task_mode`.
2. **Code/configuration provenance:** script paths, SHA-256 hashes for the
   scientific script, scientific configuration, pipeline configuration,
   execution configuration, Phase 08/09 inputs, KDA source, and networks.
3. **Run totals and resources:** fine-cell count, network count, planned,
   eligible, skipped, failed, and significant runs, result-row count, failed
   checks, peak RAM, and elapsed time.
4. **Terminal provenance:** `validation_status`, `git_revision`, and
   `timestamp_utc`.

The figure script requires:

```text
validation_status == validated_complete
```

before it will plot the production data.

