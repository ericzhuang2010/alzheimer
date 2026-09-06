# Phase 20 Combined KDA Simple Aggregation Plan

**Status:** Implemented and validated on 2026-09-06.  
**Result directory:** `results/minerva_production/20_sex_apoe_kda_simple_aggr_combo/`

## Goal

Create one key-driver list for every:

```text
sex/APOE group x broad cell type
```

There are six sex/APOE groups and 54 fine cell types, giving:

```text
54 fine cell types x 6 sex/APOE groups = 324 input contrasts
```

## KDA query for each contrast

For each fine-cell-type/sex/APOE contrast:

1. Take its significant upregulated mitochondrial genes.
2. Take its significant downregulated mitochondrial genes.
3. Merge and deduplicate the two sets. Direction is not a separate analysis
   slot.
4. Intersect the merged set with the genes available in the assigned broad-cell
   network.
5. Call `call_key_drivers()` when the DEG contrast is eligible and at least the
   configured minimum number of genes remain.

The primary settings are:

```yaml
minimum_cells_per_deg_arm: 3
minimum_effective_query_genes: 3
```

Phase 12 already contains `AD_both_mito` calls made from the same union of up-
and downregulated mitochondrial genes. The implementation will reuse those
validated call results after confirming that their queries and thresholds
match this plan, avoiding duplicate KDA computation.

## Simple aggregation

Map each fine cell type to its broad cell type, then aggregate independently
for each:

```text
sex/APOE group + broad cell type + key-driver gene
```

Use the existing simple-aggregation rule:

- If a driver is returned by one contributing KDA call, retain that call's
  adjusted p-value.
- If a driver is returned by multiple contributing calls, combine their
  adjusted p-values with equal-weight ACAT.
- Rank drivers within each sex/APOE-by-broad-cell-type group by the resulting
  score, with gene symbol as the tie-breaker.

Only drivers returned by `call_key_drivers()` are included. No global ranking,
figures, presentation, pathway analysis, or external validation will be added.

## Main result

`combo_key_drivers_by_category.tsv` will contain one row per key driver and
sex/APOE-by-broad-cell-type group, including:

- sex/APOE group and broad cell type;
- key-driver gene;
- aggregation score and rank;
- singleton or ACAT aggregation method;
- number of contributing calls;
- contributing fine cell types and run IDs; and
- mitochondrial annotation for the driver.

`combo_category_summary.tsv` will include all expected sex/APOE-by-broad-cell-
type groups, including groups with no eligible KDA calls or no returned key
drivers.

## Sensitivity support

The two cutoffs will be configuration values rather than hardcoded values. For
all 324 contrasts, retain:

- cell counts for both DEG arms;
- merged-query size and effective-query size;
- eligibility/exclusion reason; and
- KDA status and number of returned drivers.

Also retain the combined query membership and unaggregated KDA result rows.
Later analyses can raise either cutoff, filter the saved baseline calls, and
rerun only the aggregation. For example:

```yaml
minimum_cells_per_deg_arm: 5
minimum_effective_query_genes: 10
```

Changing the DEG method, resampling cells, or lowering the thresholds below
the baseline would require upstream reruns and is outside this plan.

## Output files

```text
20_sex_apoe_kda_simple_aggr_combo/
├── combo_key_drivers_by_category.tsv
├── combo_category_summary.tsv
├── combo_run_manifest.tsv
├── combo_query_members.tsv.gz
└── combo_returned_call_rows.tsv.gz
```

## Implementation

1. Add one configuration file containing the two thresholds and input paths.
2. Add one script that validates/reuses the combined Phase 12 KDA calls,
   applies the selected thresholds, performs simple aggregation, and writes
   the five output files.
3. Check that all 324 input contrasts have an explicit status, retained calls
   meet both cutoffs, and ranks are unique within each final group.

The approved implementation and primary result generation are complete.
