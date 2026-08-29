# Phase 20 Broad-Cell Sex/APOE Direct KDA Plan and Execution Report (No ACAT)

**Status:** Executed; local-production release is `validated_complete`  
**Date:** 2026-08-28  
**Analysis ID:** `phase20_sex_apoe_kda_broad_v1`  
**Cohort:** ROSMAP

## Decision summary

This is a new, parallel Phase 20 branch that runs key-driver analysis (KDA)
directly from the donor-level broad-cell DEG results produced in Phase 08. It
does not overwrite or alter the existing fine-cell Phase 20 analysis.

The biological result grid contains:

```text
7 broad cell types × 6 sex/APOE groups = 42 broad-cell DEG contrasts
```

Each estimable contrast produces one signed DEG result, which is separated
into an upregulated and a downregulated mitochondrial query. Therefore, the
exact structural KDA counting is:

```text
42 broad-cell DEG contrasts
× 2 query directions (AD_up_mito and AD_down_mito)
= 84 planned directional KDA slots
```

The 42 combinations are the biological categories. They are not automatically
42 successful KDA calls. A directional slot is executed only when its source
DEG contrast is estimable and at least three mitochondrial query genes remain
after network mapping.

No ACAT aggregation is needed or permitted in this branch. Each eligible
broad-cell direction already supplies one query to its matching broad-cell
network. Its within-run KDA P value and BH q-value are the direct statistical
evidence.

The frozen Phase 08 data produced three executable relaxed-primary directional
calls:

| Broad cell type | Sex/APOE group | Direction | Effective query genes |
|---|---|---|---:|
| Astrocytes | `F_e4` | `AD_down_mito` | 13 |
| Astrocytes | `M_e33` | `AD_down_mito` | 3 |
| OPCs | `F_e4` | `AD_down_mito` | 4 |

All 42 categories and all 84 directional slots are retained in the manifests.
A skipped slot is a documented result of the filtering funnel; it is not
silently dropped or filled with top-ranked genes.

### Executed local-production result

The local-production run completed all three eligible relaxed-primary calls with no
KDA failures:

| Broad cell type | Group | Direction | Query genes | Explicit candidate tests | Relaxed candidates (`q <= 0.10`) | Strict reference (`q <= 0.05`) | Terminal status |
|---|---|---|---:|---:|---:|---:|---|
| Astrocytes | `F_e4` | `AD_down_mito` | 13 | 160 | 2 | 2 | `completed_significant` |
| Astrocytes | `M_e33` | `AD_down_mito` | 3 | 80 | 0 | 0 | `completed_no_significant` |
| OPCs | `F_e4` | `AD_down_mito` | 4 | 137 | 10 | 7 | `completed_significant` |
| **Total** | | | | **377** | **12** | **9** | **3 completed, 0 failed** |

The 12 relaxed-primary non-core-MT candidate genes are:

| Broad-cell category and direction | Candidate genes in within-run rank order |
|---|---|
| Astrocytes, `F_e4`, `AD_down_mito` | `ELL2`, `SLC44A3` |
| OPCs, `F_e4`, `AD_down_mito` | `CAMK2D`, `RAPGEF4`, `RAB3IP`, `FOXN3`, `AC092691.1`, `FAM13A`, `NCOA1`, `FGF14`, `GRID1`, `DENND1A` |

The first two Astrocyte candidates and the first seven OPC candidates also
pass the strict-reference q-value threshold. Astrocytes `M_e33` was a valid
completed empty result. These are direct direction-specific KDA results; no
ACAT or other cross-run aggregation was applied.

All 31 blocking local-production checks passed. An independent second execution
also passed output validation and was byte-identical across all 21 declared
files, including the deterministically compressed tables.

## 1. Objective

For every broad-cell type and sex/APOE group, test whether a non-core-MT
network gene has a directed downstream neighborhood enriched for the broad-cell
mitochondrial AD-versus-NCI DEG signature.

The six sex/APOE groups are:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

The seven broad cell types and matching Bayesian networks are:

```text
Astrocytes
Excitatory_neurons
Inhibitory_neurons
Microglia
OPCs
Oligodendrocytes
Vasculature_cells
```

This branch answers a direct broad-cell question. It does not combine
fine-cell KDA evidence and does not replace the existing Phase 20 analysis.

## 2. Relationship to the existing Phase 20 branch

The two Phase 20 analyses use different upstream evidence and have different
statistical units:

| Feature | Existing fine-cell Phase 20 | New direct broad-cell branch |
|---|---|---|
| DEG source | Fine-cell contrasts | Donor-level broad-cell contrasts |
| Evidence in one category | Multiple fine-cell/direction KDA runs | At most one KDA run per direction |
| Cross-run coverage | Required | Not applicable |
| ACAT | Combines run-level P values | Not used |
| Category ACAT q | Final aggregate statistic | Does not exist |
| Fine-type recurrence/support | Used | Not applicable |
| Leave-one-fine-type-out stability | Used | Not applicable |
| Direct result unit | Gene x category after aggregation | Gene x category x direction |

The current fine-cell Phase 20 result remains frozen under:

```text
results/minerva_production/20_sex_apoe_kda/
```

The broad-direct result uses a separate namespace:

```text
results/minerva_production/20_sex_apoe_kda_broad/
```

The two results may later be compared descriptively as triangulation. Their P
values and q-values must not be pooled, and agreement or disagreement is not a
formal validation test.

## 3. Definitions and counting units

### Broad-cell DEG contrast

One AD-versus-NCI edgeR comparison for one broad cell type and one sex/APOE
group. There are 42 structural contrasts.

### Directional KDA slot or run

One possible KDA test defined by:

```text
broad_cell_type + group_id + signature_direction
```

There are 84 planned directional slots in the relaxed-primary manifest. A slot
becomes an executed KDA run only after all source, background, and query-size
gates pass.

Even if the implementation sends the up and down signatures to
`call_key_drivers()` together as two `Group` labels, the function tests and
BH-corrects each group separately. Statistically, they remain two runs.

### Query gene

A query gene is a broad-cell DEG that:

- passes the prespecified DEG tier;
- is annotated `core_mito_protein`;
- has the requested AD-up or AD-down direction; and
- is present in the effective network background.

The query genes are the mitochondrial targets whose network enrichment is
tested. They are not candidate drivers.

### Candidate driver gene

Yes, a candidate is a **gene**. It is a network gene whose directed downstream
neighborhood is tested for enrichment of the mitochondrial query genes. A
candidate driver:

- does not have to be a DEG;
- does not have to be mitochondrial;
- does not have to belong to the query; and
- is not called a passing key driver until it satisfies the final KDA gates.

The formal candidate unit in this branch is:

```text
broad_cell_type + group_id + signature_direction + analysis_gene_symbol
```

`analysis_gene_symbol` is the Phase 08 `mapped_gene`: the current HGNC symbol
when available, otherwise the original feature/network symbol. The output
column is retained as `current_symbol` for compatibility with the inherited
KDA engine, so `mapping_status` must be used to distinguish current mappings
from original-symbol fallbacks.

Up- and down-direction evidence remains separate. If the same gene passes in
both directions, it has two inferential rows rather than one combined q-value.

## 4. Frozen Phase 08 broad-DEG authority

### Required input files

The broad branch reads the validated production release under:

```text
results/minerva_production/08_deg_broad/
```

Required files are:

```text
broad_deg_status.tsv
broad_deg_checks.tsv
broad_deg_artifacts.tsv
broad_deg_contrast_status.tsv
broad_deg_model_diagnostics.tsv
broad_deg_results.tsv.gz
broad_core_mito_kda_query_handoff.tsv.gz
broad_deg_filter_funnel.tsv
00_inputs/broad_deg_contrast_manifest.tsv
00_inputs/phase08_broad_deg_config_snapshot.yml
```

The Phase 09 annotation authority and the seven network files configured in
`config/phase12_kda.yml` are also required. The new branch must record path,
byte size, and SHA-256 for every source, config, network, and scientific code
file.

Execution must stop before KDA if:

- the Phase 08 status is not `validated_complete`;
- a blocking Phase 08 check failed;
- an expected source or network checksum differs;
- the 42-row contrast manifest is incomplete or duplicated; or
- the gene annotation cannot classify every candidate as core-MT or
  non-core-MT.

### Current source audit

The validated Phase 08 release contains:

| Source outcome | Broad-cell contrasts |
|---|---:|
| `validated_complete` | 40 |
| `not_estimable` | 2 |
| Failed | 0 |
| **Total** | **42** |

The two non-estimable contrasts are:

| Broad cell type | Group | Eligible AD donors | Eligible NCI donors | Reason |
|---|---|---:|---:|---|
| Vasculature_cells | `F_e2` | 3 | 10 | Fewer than five eligible donors in the AD arm |
| Vasculature_cells | `M_e2` | 4 | 3 | Fewer than five eligible donors in both arms |

These are unavailable source models, not successful DEG comparisons with zero
DEGs. Each unavailable contrast accounts for two source-not-estimable KDA
slots.

## 5. Prespecified query tier

The primary query uses the Phase 08 **relaxed** DEG tier, which was already
declared as the recommended broad-cell KDA handoff:

```text
within-contrast DEG BH q <= 0.10
and abs(logFC) >= log2(1.2)
and mito_tier == core_mito_protein
```

Direction is determined by the sign of `logFC`:

```text
logFC > 0 -> AD_up_mito
logFC < 0 -> AD_down_mito
```

The strict and exploratory DEG tiers are sensitivity analyses, not sources to
mix into the relaxed-primary run or use as category-specific fallbacks:

| Query tier | DEG rule | Role |
|---|---|---|
| Strict | q `< 0.05` and `abs(logFC) > log2(1.3)` | Reference sensitivity |
| Relaxed | q `<= 0.10` and `abs(logFC) >= log2(1.2)` | Primary |
| Exploratory | q `<= 0.20`, no fold-change gate | Hypothesis-generating sensitivity |

The tier is applied uniformly. A sparse category cannot switch from relaxed to
exploratory after its query size is observed.

## 6. Tested universe, network background, and effective query

For each source-complete broad-cell contrast:

1. Read all rows for that broad cell and group from
   `broad_deg_results.tsv.gz`, not only significant DEGs.
2. Define `tested_genes` as the unique Phase 08 `mapped_gene` values retained
   by the broad edgeR model's `filterByExpr` analysis. `mapped_gene` uses the
   current HGNC symbol when available and otherwise keeps the original feature
   symbol.
3. Read the matching frozen broad Bayesian network and verify its checksum and
   directed-acyclic-graph status.
4. Induce the network by retaining only edges for which both endpoints belong
   to `tested_genes`.
5. Define the effective background as the unique endpoints of the retained
   edges.
6. Build the provisional query from unique `mapped_gene` values in the
   direction-specific handoff rows with `signature_tier == "relaxed"` and
   `mito_tier == "core_mito_protein"`.
7. Define the effective query as:

```text
effective_query = unique(provisional_query intersect effective_background)
```

Gene-symbol mappings must be deduplicated for set membership. Mapping
collisions and every query gene removed by network mapping must be recorded.
The KDA `bg.size` is the number of genes in the effective background.

This construction matches the established Phase 12 policy:

```text
exact contrast-tested genes intersect induced matching network
```

It prevents an untested expression gene or an out-of-background query gene
from contributing to the enrichment test.

## 7. Directional eligibility and the observed funnel

The minimum executable effective query size is retained at three genes. This
was prespecified in the Phase 08 broad-DEG plan and must not be lowered to
manufacture a result.

The existing fine-cell Phase 18/20 branch later required at least ten query
genes before cross-run aggregation. That downstream inclusion gate is not
inherited by this new direct-broad branch: Phase 08 prespecified three as the
broad-KDA estimability minimum. The ten-gene boundary is retained below as an
evidence-strength label and sensitivity, so the difference remains visible.

Each primary directional slot receives exactly one eligibility status:

```text
source_contrast_not_estimable
no_provisional_query
effective_query_empty_after_background
effective_query_below_minimum
eligible
```

An eligible execution then receives one terminal status:

```text
completed_significant
completed_no_significant
completed_no_testable_candidates
failed
```

A completed call with no selected driver is a valid empty KDA result, not a
failure.

### Observed query-tier funnel

The following production reconstruction uses the completed Phase 08 broad
release, its exact tested-gene sets, and the frozen seven Bayesian networks:

| Query tier | Source not estimable | No provisional query | Query lost after background | Effective query 1-2 | Effective query 3-9 | Effective query >=10 | Executable at >=3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict | 4 | 66 | 3 | 9 | 2 | 0 | 2 |
| Relaxed primary | 4 | 61 | 4 | 12 | 2 | 1 | 3 |
| Exploratory | 4 | 54 | 3 | 16 | 4 | 3 | 7 |

Every row sums to 84 directional slots. The production program must recompute
these counts from frozen inputs and fail validation if the frozen-input audit
does not reproduce them.

For the relaxed primary tier, the detailed funnel is:

```text
84 planned directional slots
- 4 source-not-estimable slots
= 80 source-complete slots
- 61 with no relaxed core-MT DEG in that direction
= 19 nonempty provisional queries
- 4 that lose every query gene during tested-network mapping
= 15 nonempty effective queries
- 12 with only 1-2 effective query genes
= 3 executable KDA runs
```

The three-gene rule allows all three calls to execute. Their evidence strength
must still distinguish:

```text
small_query_3_9: 3-9 effective genes
phase18_sized_query_ge10: >=10 effective genes
```

Two current calls are `small_query_3_9`; only Astrocytes `F_e4` AD-down has at
least ten effective query genes. Query size is an evidence label and a
prespecified sensitivity boundary, not a reason to hide executed results.

## 8. Direct KDA computation

Use the frozen KDA engine in `scripts/NetWeaver/fKDA.R` with the established
settings:

```text
nLayerToTest = 3
nLayersToExpand = 0
directed = TRUE
reduce.within.nlayer = 2
fdr = 0.05 for stock-fKDA parity output
p.correction.method = BH
return.overlap = TRUE
```

Within one eligible direction, KDA:

1. identifies candidate network genes reachable around the effective query;
2. evaluates each candidate's directed downstream neighborhoods at layers
   one through three;
3. calculates an upper-tail hypergeometric enrichment P value at each layer;
4. retains the best layer and raw P value for each candidate gene; and
5. performs multiple-testing correction across the candidate genes in that
   directional run.

The implementation must preserve the complete pre-FDR candidate-test table.
Stock `call_key_drivers()` normally returns only candidates passing its FDR
cutoff, which is insufficient for reproducing a non-core-MT-only BH family or a
relaxed q threshold.

The broad implementation must therefore either expose the complete internal
test table or reconstruct it with parity-tested code. On a shared test fixture,
raw P values, best layers, overlaps, fold enrichments, and stock significant
returns must reproduce the frozen fKDA implementation exactly.

## 9. Non-MT driver family and direct q-values

The mitochondrial genes define the **query**, but final driver candidates are
restricted to **non-core-MT genes**.

For each eligible directional run:

1. compute and retain raw KDA P values for every explicitly tested candidate;
2. annotate every candidate with the frozen Phase 09 mitochondrial tier;
3. exclude all `core_mito_protein` candidates from the final inferential
   family;
4. apply BH across all remaining explicitly tested non-core-MT candidates; and
5. store the result as `non_mt_run_q`.

The filter occurs before BH and before overlap, enrichment, q-value, or ranking
selection. BH must never be recomputed only among stock significant returns.

Also preserve for audit:

```text
original_run_q
stock_fkda_q05_return
```

`original_run_q` is the stock fKDA BH value across all explicitly tested
candidates, including MT candidates. It is retained for engine parity and is
not the final non-core-MT inferential q-value.

The schema name `non_mt_run_q` uses “non-MT” as shorthand for “not annotated
`core_mito_protein`.” It does not exclude the broader `mito_extended` tier;
for example, the selected candidate `NCOA1` is `mito_extended`.

## 10. No ACAT or cross-run aggregation

This branch must not calculate:

- eligible-run or usable-run coverage;
- implicit cross-run `P = 1` rows;
- ACAT P values;
- ACAT q-values;
- supporting-run counts or recurrence gates;
- leave-one-fine-type-out stability; or
- any aggregate obtained by combining up- and down-direction P values.

There is no cross-run evidence to combine within a broad-cell direction. The
direct `non_mt_run_q` is the main q-value.

The 42-category summary may display up and down results side by side. It may
also contain a clearly labeled descriptive union of gene symbols, but it must
retain both direction-specific q-values and must not label the minimum of them
as a corrected category q-value.

## 11. Candidate gates, evidence tiers, and ranking

### Relaxed-primary candidate

A candidate unit passes the discovery-oriented main rule when:

```text
the directional run is eligible and completed
candidate is not core_mito_protein
query_overlap >= 2
fold_enrichment > 1
non_mt_run_q <= 0.10
```

### Strict direct-KDA reference

Attach a strict-reference flag when the same candidate satisfies:

```text
query_overlap >= 2
fold_enrichment > 1
non_mt_run_q <= 0.05
```

The query tier and driver q threshold are different filtering axes. The
strict-reference flag above uses the relaxed-primary query with a stricter KDA
q threshold. A KDA rerun using the strict DEG query is a separate sensitivity
analysis and must be labeled as such.

`is_root_node`, best layer, out-degree, undirected degree, and query-size tier
are reported annotations. Stock fKDA's `global_key_driver` is defined only for
its q <= 0.05 returned set and is therefore retained as the explicitly named
`stock_global_key_driver`; it is `NA` for candidates outside that stock return.
These annotations are not additional candidate gates.

Rank passing genes separately within:

```text
broad_cell_type + group_id + signature_direction
```

Use this deterministic order:

1. smaller `non_mt_run_q`;
2. smaller raw KDA P value;
3. larger query overlap;
4. larger fold enrichment; and
5. analysis gene symbol alphabetically.

Retain every passing candidate. A top-ten table is a detailed display subset,
and a top-five table is a compact presentation subset. Empty lists are never
backfilled with nonsignificant genes.

## 12. Sensitivity analyses

The following are prespecified and remain separate from the relaxed primary
result:

- repeat KDA with the strict DEG query tier;
- repeat KDA with the exploratory DEG query tier;
- compare candidate q thresholds of 0.05 and 0.10;
- flag results from effective queries of 3-9 versus at least 10 genes; and
- optionally calculate a study-wide BH q across all explicit non-core-MT
  gene-by-direction hypotheses as a robustness field, not a selection
  replacement and not ACAT.

An `AD_both_mito` query would answer a different, direction-agnostic question.
It is excluded from the primary branch. If later enabled, it must be a
separately labeled sensitivity and cannot replace or be merged with the signed
results.

No sensitivity tier may be substituted into an empty primary category.

## 13. Implemented code and output files

### Configuration and code

```text
config/phase20_sex_apoe_kda_broad.yml
scripts/20_sex_apoe_kda_broad.py
scripts/20_sex_apoe_kda_broad_fkda_parity.R
tests/test_phase20_sex_apoe_kda_broad.py
```

The Python production program reuses the complete-evidence reconstruction in
`scripts/18_key_driver_selection.py`. The R parity helper calls the frozen
stock `fKDA.R` implementation so stock q <= 0.05 returns can be checked against
the reconstructed complete candidate table. The branch writes only to its own
output directory; it does not alter the Phase 12, Phase 18, or fine-cell Phase
20 releases.

### Output layout

```text
results/minerva_production/20_sex_apoe_kda_broad/
|-- 00_inputs/
|   |-- phase08_broad_input_authority.tsv
|   |-- phase08_broad_config_snapshot.yml
|   |-- phase20_broad_kda_config_snapshot.yml
|   `-- network_input_authority.tsv
|-- phase20_broad_category_manifest.tsv
|-- phase20_broad_direction_manifest.tsv
|-- phase20_broad_signature_members.tsv.gz
|-- phase20_broad_background_members.tsv.gz
|-- phase20_broad_symbol_mapping_collisions.tsv.gz
|-- phase20_broad_all_candidate_tests.tsv.gz
|-- phase20_broad_stock_fkda_returns.tsv
|-- phase20_broad_non_mt_candidates.tsv
|-- phase20_broad_strict_reference.tsv
|-- phase20_broad_top10.tsv
|-- phase20_broad_top5_summary.tsv
|-- phase20_broad_category_summary.tsv
|-- phase20_broad_query_tier_sensitivity.tsv.gz
|-- phase20_broad_filter_funnel.tsv
|-- phase20_broad_checks.tsv
|-- phase20_broad_artifacts.tsv
`-- phase20_broad_status.tsv
```

File requirements:

- `phase20_broad_category_manifest.tsv` has exactly 42 rows, including source
  failures and categories with no eligible direction;
- `phase20_broad_direction_manifest.tsv` has exactly 84 relaxed-primary rows;
- the signature file preserves provisional membership and network-exclusion
  reasons, while the background file preserves every included effective-
  background member;
- the symbol-collision file preserves all source-gene identities behind every
  many-to-one `mapped_gene` collapse;
- the all-candidate table contains every explicit test needed to reproduce
  both BH families;
- the candidate file contains all passing non-core-MT direction-specific genes;
- the category summary presents complete direction-specific candidate/q-value
  lists as well as top-five displays, without creating an aggregate q-value;
- sensitivity results carry their query tier and cannot be confused with the
  relaxed primary result.

## 14. Validation and acceptance criteria

### Input and scope checks

- Phase 08 broad status is `validated_complete`, with every blocking check
  passing.
- The source manifest contains exactly 42 unique broad-cell/group contrasts.
- Exactly 40 source contrasts are complete, two are not estimable, and none
  failed for the frozen input release.
- The primary direction manifest contains exactly 84 unique slots.
- The seven network paths and SHA-256 values match the frozen config, and all
  seven networks are valid DAGs.

### Query and funnel checks

- The relaxed handoff contains 65 core-MT memberships: 20 AD-up and 45
  AD-down.
- Every effective query gene belongs to both its provisional query and its
  effective background.
- Every effective background is exactly the endpoint set of the induced
  network.
- The relaxed-primary 84-slot funnel reproduces `4 + 61 + 4 + 12 + 2 + 1` for
  source-not-estimable, no-query, lost-query, size 1-2, size 3-9, and size
  at least 10, respectively.
- Exactly three relaxed-primary direction slots are executable at the
  prespecified minimum of three genes, with effective query sizes 13, 3, and
  4 for the declared category/direction combinations.

### KDA and candidate checks

- Candidate test keys are unique by directional run and gene.
- Stored hypergeometric P values, best layers, overlaps, and fold enrichments
  reproduce the parity-tested fKDA engine.
- `original_run_q` reproduces stock fKDA BH and significant returns.
- `non_mt_run_q` reproduces BH over all and only explicitly tested non-core-MT
  candidates in one directional run.
- No core-MT gene enters a final candidate, rank, or figure table.
- No candidate is selected without overlap of at least two, fold enrichment
  greater than one, and the declared q threshold.
- A completed empty result remains present and is not marked failed.
- No ACAT, coverage, cross-run support, or leave-one-fine-type-out operation is
  present in the production path or output schema.
- There are zero KDA computation failures for a `validated_complete` release.
- Repeated execution with unchanged inputs produces deterministically ordered,
  byte-identical tabular outputs.

The release status is `validated_complete` only after all blocking checks
pass.

## 15. Executed sequence

1. Froze the broad-KDA config, Phase 08 and Phase 09 input authorities,
   network hashes, and scientific-code hashes.
2. Built the 42-row category manifest and 84-row relaxed-primary direction
   manifest.
3. Reconstructed tested-gene-induced backgrounds and effective queries, with
   an independent NetworkX DAG and induced-edge check for every network.
4. Reproduced the frozen relaxed-primary funnel exactly.
5. Parity-tested complete pre-FDR fKDA evidence capture against stock fKDA.
6. Executed all three eligible primary directional runs and retained exact
   terminal statuses for every ineligible slot.
7. Removed core-MT candidates before rebuilding complete within-run
   non-core-MT BH families, then applied candidate gates and deterministic
   ranks.
8. Ran the separately labeled strict and exploratory query sensitivities.
9. Wrote the 42-category side-by-side summary without ACAT aggregation.
10. Passed all 31 blocking local-production checks and published the release as
    `validated_complete`.

The executable entry points are:

```bash
python3 tests/test_phase20_sex_apoe_kda_broad.py
python3 scripts/20_sex_apoe_kda_broad.py
python3 tests/test_phase20_sex_apoe_kda_broad.py \
  --validate-output results/minerva_production/20_sex_apoe_kda_broad
```

## 16. Interpretation boundaries

This direct branch can identify non-core-MT network drivers supported by a
signed broad-cell mitochondrial DEG query. It cannot establish biological
causality.

The broad-cell DEG is a marginal broad-population effect. It may reflect both
within-fine-type expression changes and changes in the mixture of fine cell
types inside a broad cell population.

A gene found in one sex/APOE category but not another is not, by itself,
evidence that its key-driver effect differs statistically between those
groups. That claim would require a formal heterogeneity or interaction test.

Most importantly, a category with no executable KDA direction is **not** a
category with proven absence of key drivers. It means the source contrast was
not estimable or too few relaxed core-MT DEG genes survived the network and
minimum-query filters. Under the current frozen inputs, only three of the 84
directional slots can be executed without changing the prespecified rules.
