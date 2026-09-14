# Phase 11: Broad-cell DEG mitochondrial pathway and program analysis

## Status

**Implemented, executed, and validated on 2026-09-14.**

The production output directory will be:

```text
results/minerva_production/11_pathway_deg_broad/
```

This will be a sibling analysis to:

```text
results/minerva_production/11_pathway_similarity/
results/minerva_production/11_pathway_deg_fine/
```

The new analysis will not overwrite the broad-cell DEG release, the fine-cell
pathway release, KDA results, or Phase 11 similarity results.

### Execution outcome

- The production bundle contains all 25 required files and is
  `validated_complete`.
- All 53 blocking checks passed.
- Resume is now bound to 70 exact upstream files, including all 42 physical
  broad-DEG slices. The status also binds the complete 23-row, path-exact
  output artifact manifest, so changed inputs or omitted outputs cannot be
  accepted as a valid cached release.
- The 42 planned contrasts remain explicit: 40 are estimable and two are
  non-estimable.
- Primary GSEA contains 8,358 status rows, of which 6,228 were testable and
  213 passed local BH FDR. Within the primary broad-46 collection, 64 passed
  local BH FDR and 44 also passed study-wide BH FDR.
- ORA contains 75,222 status rows, of which 7,664 were testable. No strict or
  relaxed ORA result passed local BH FDR. Six exploratory legacy-module rows
  passed local BH FDR, so they remain hypothesis-generating evidence only.
- Composition GSEA contains 8,358 status rows and 4,308 testable rows. Among
  37 locally significant broad-46 signals in cell classes where composition
  adjustment was applicable, all 37 retained their NES sign and 26 retained
  local BH significance.
- A second isolated production run reproduced all 23 checksummed scientific
  artifacts byte-for-byte. Re-running the normal pipeline command safely
  resumed from the hash-valid release.
- Broad-versus-fine rows are now `not_comparable` whenever either resolution
  is untestable; significance categories are assigned only when both
  resolutions can be tested.

## 1. Main objective

Run a reproducible mitochondrial pathway and program analysis for the ROSMAP
donor-level broad-cell DEG contrasts in:

```text
results/minerva_production/08_deg_broad/
```

The structural design is:

```text
7 broad cell types × 6 sex/APOE groups = 42 planned AD-versus-NCI contrasts
```

The seven broad cell types are:

1. Astrocytes;
2. Excitatory neurons;
3. Inhibitory neurons;
4. Microglia;
5. OPCs;
6. Oligodendrocytes; and
7. Vasculature cells.

The six groups are:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

Of the 42 planned contrasts, 40 are `validated_complete`. Two vasculature
contrasts are explicitly `not_estimable` because they have fewer than five
eligible donors in at least one diagnosis arm:

- `Vasculature_cells::AD_vs_NCI__Female__e2`;
- `Vasculature_cells::AD_vs_NCI__Male__e2`.

The analysis will answer:

1. Which mitochondrial programs show coordinated AD-associated expression
   shifts within each broad cell type and sex/APOE group?
2. Is each program shifted toward higher or lower expression in AD?
3. Which pathway findings survive a strict thresholded-DEG analysis?
4. Which conclusions are visible only under the relaxed or exploratory DEG
   tiers?
5. Which broad-cell pathway findings are robust to fine-cell-composition
   adjustment?
6. Which broad-cell findings agree descriptively with the earlier fine-cell
   pathway analysis?

These are stratified AD-versus-NCI analyses. They are not formal
disease-by-sex or disease-by-APOE interaction tests.

## 2. Key scientific decision: ranked GSEA is primary

### 2.1 Why strict ORA alone is not sufficient

The broad-cell DEG release contains complete edgeR results for 40 estimable
contrasts, but strict mitochondrial DEG lists are sparse:

| Prespecified tier | Core-mito DEG rows | Contrasts with at least one |
|---|---:|---:|
| Strict | 43 | 13 |
| Relaxed | 65 | 14 |
| Exploratory | 141 | 18 |

Under the strict tier, only six completed contrasts have at least three
combined mitochondrial DEGs. One has at least three AD-up genes and five have
at least three AD-down genes. An ORA-only analysis would therefore leave most
broad-cell contrasts unavailable for pathway testing.

The primary analysis will instead use preranked gene-set enrichment analysis
(GSEA) over every tested core-mitochondrial gene. GSEA can detect a coordinated
pathway shift even when few individual genes cross a DEG threshold.

### 2.2 Analysis hierarchy

The evidence hierarchy will be:

1. **Primary:** preranked GSEA using all tested core-mitochondrial genes;
2. **Thresholded companion:** ORA using strict DEGs;
3. **Threshold sensitivity:** ORA using the frozen relaxed and exploratory
   tiers, kept in separate statistical families;
4. **Composition sensitivity:** preranked GSEA from the composition-adjusted
   broad-cell models; and
5. **Resolution comparison:** descriptive comparison with the strict fine-cell
   ORA release.

The analysis must not choose whichever tier gives the smallest P value.
Strict, relaxed, and exploratory results have different evidential roles.

## 3. Broad-cell DEG authority

### 3.1 Primary model

The broad-cell release used donor-level pseudobulk counts and edgeR
quasi-likelihood models. The donor, not the nucleus, is the biological
replicate.

For each broad cell type, the primary model estimated:

```text
AD − NCI
```

within each sex/APOE group while adjusting for age at death and PMI.

This broad-cell estimand is marginal: it may reflect both expression changes
within constituent fine cell types and changes in their proportions.

### 3.2 Required primary inputs

The implementation must validate and checksum:

```text
results/minerva_production/08_deg_broad/broad_deg_status.tsv
results/minerva_production/08_deg_broad/broad_deg_checks.tsv
results/minerva_production/08_deg_broad/broad_deg_artifacts.tsv
results/minerva_production/08_deg_broad/broad_deg_contrast_status.tsv
results/minerva_production/08_deg_broad/broad_deg_model_diagnostics.tsv
results/minerva_production/08_deg_broad/broad_deg_filter_funnel.tsv
results/minerva_production/08_deg_broad/broad_deg_results.tsv.gz
results/minerva_production/08_deg_broad/00_inputs/broad_deg_contrast_manifest.tsv
results/minerva_production/08_deg_broad/00_inputs/phase08_broad_deg_config_snapshot.yml
results/minerva_production/08_deg_broad/05_by_contrast/*.broad_deg.tsv.gz
results/minerva_production/09_annotate_genes/annotation_status.tsv
results/minerva_production/09_annotate_genes/annotation_checks.tsv
results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz
```

Current validated expectations are:

- 42 structural contrasts;
- 40 completed and two non-estimable contrasts;
- 786,242 tested gene rows;
- 41,520 tested `core_mito_protein` rows;
- 1,136 unique current core-mito symbols across the release;
- 1,636 strict DEGs across all genes, including 43 core-mito DEGs;
- 2,336 relaxed DEGs across all genes, including 65 core-mito DEGs; and
- 4,113 exploratory DEGs across all genes, including 141 core-mito DEGs.

All 31 blocking rows in `broad_deg_checks.tsv` must pass. Every required source
file must match its record in `broad_deg_artifacts.tsv`. The 42 physical
contrast files must reconcile exactly to the combined result and include two
header-only files for the unavailable contrasts. The Phase 09 annotation
status and checks must pass, and the annotation-master checksum must match the
checksum recorded by the broad DEG release.

### 3.3 Required composition-sensitivity inputs

Use:

```text
results/minerva_production/08_deg_broad/04_sensitivity/broad_deg_composition_adjusted.tsv.gz
results/minerva_production/08_deg_broad/04_sensitivity/broad_deg_sensitivity_contrast_status.tsv
results/minerva_production/08_deg_broad/04_sensitivity/broad_deg_sensitivity_summary.tsv
results/minerva_production/08_deg_broad/04_sensitivity/broad_deg_sensitivity_checks.tsv
```

The composition branch contains:

- 28 `validated_complete` contrast models;
- 12 `not_applicable` contrasts for OPCs and oligodendrocytes, which each
  contain only one included fine cell type; and
- the same two non-estimable vasculature contrasts.

The 28 completed sensitivity contrasts contain 28,476 tested core-mito rows.
Gene annotations must join exactly from the primary broad-cell result by
`broad_cell_type + gene`; the current release has no missing joins or duplicate
mapping keys.

## 4. Gene identity and statistical universes

### 4.1 Mitochondrial universe

The required release is mitochondrial-program focused. Use:

```text
mito_tier == core_mito_protein
```

Whole-transcriptome Hallmark, GO, Reactome, KEGG, inflammatory, synaptic, and
other non-mitochondrial pathways are outside this release. They require the
whole tested transcriptome as their background and should be implemented as a
separate future profile.

### 4.2 Gene identity

The enrichment unit is:

```text
symbol_hgnc_current
```

For the current primary broad-cell release:

- all tested core-mito rows have a current symbol;
- there are no duplicate `contrast_id + symbol_hgnc_current` keys; and
- there are no missing core-mito symbol mappings.

The implementation must still retain mapping checks and fail if these
properties change. It must never silently use a whole-genome background or
drop a duplicated symbol without recording the collapse.

### 4.3 Per-contrast tested universe

For each estimable contrast, the universe is every unique
`symbol_hgnc_current` in `broad_deg_results.tsv.gz` with:

```text
mito_tier == core_mito_protein
```

The broad result contains only genes retained by edgeR for that broad-cell
model, so these are the genes that could have contributed to the statistical
result. `filterByExpr` was applied once per broad-cell model, so the tested
universe is shared across the six strata within a broad cell type:

| Broad cell type | Tested core-mito symbols |
|---|---:|
| Astrocytes | 1,084 |
| Excitatory neurons | 1,134 |
| Inhibitory neurons | 1,113 |
| Microglia | 1,033 |
| OPCs | 1,070 |
| Oligodendrocytes | 1,104 |
| Vasculature cells | 573 |

The two non-estimable contrasts receive explicit unavailable rank and
background records. They are not represented as zero-DEG contrasts.

## 5. Pathway and program collections

Use the same three prespecified collections as the fine-cell pathway analysis.

### 5.1 Legacy four-module benchmark

Read:

```text
config/phase13_respiratory_modules.tsv
```

The four modules are:

1. 13 mtDNA-encoded OXPHOS genes;
2. 86 nuclear-encoded structural OXPHOS genes;
3. 155 mitochondrial-translation genes; and
4. 19 MIB/MICOS inner-membrane genes.

This is a compatibility benchmark, not the comprehensive discovery
collection.

### 5.2 Broad MitoCarta collection

Use the 46 MitoCarta3.0 programs at hierarchy depths 1 and 2:

- seven top-level mitochondrial systems; and
- 39 level-2 programs.

This is the primary expanded collection.

### 5.3 Complete MitoCarta collection

Use all 149 MitoCarta3.0 MitoPathways as a prespecified supplemental
collection. Parent and child terms supported by the same genes must be treated
as one biological theme during interpretation.

### 5.4 Reference authority and reconciliation

The authoritative source is:

```text
data/reference/Human.MitoCarta3.0.xls
```

Use sheet `C MitoPathways` and verify source SHA-256:

```text
e6ada0ae8dcd5447a5efb6f77c69a1c10b1ffa66521540a1e81b92c61e5505f2
```

Reconcile the normalized reference exactly against:

```text
results/minerva_production/11_pathway_similarity/pathway_reference_manifest.tsv
results/minerva_production/11_pathway_similarity/pathway_membership_long.tsv.gz
results/minerva_production/11_pathway_deg_fine/fine_deg_pathway_program_manifest.tsv
```

Expected MitoCarta properties are:

- 149 pathways;
- 3,904 pathway-gene memberships;
- 1,035 unique symbols;
- seven depth-1 pathways;
- 39 depth-2 pathways; and
- 103 depth-3 pathways.

No P value, DEG query, or selected finding from either existing Phase 11
analysis is an input to the new broad-cell test.

## 6. Primary preranked GSEA

### 6.1 Rank statistic

For every completed contrast, rank all tested core-mito symbols by:

```r
F_for_rank <- pmax(F, 0)
rank_score <- sign(logFC) * sqrt(F_for_rank)
```

Here, `F` is the one-degree-of-freedom edgeR quasi-likelihood F statistic.
This ranking combines direction with strength of evidence:

- a large positive score means stronger evidence for higher expression in AD;
- a large negative score means stronger evidence for lower expression in AD.

Do not rank by log fold change alone. Low-count genes can have unstable fold
changes, whereas the edgeR test statistic incorporates uncertainty.

An edgeR F statistic is theoretically nonnegative. The frozen release contained
one numerical underflow artifact (`SDHD`, inhibitory neurons, female APOE
ε2): `F = -6.64 × 10^-10` with `p = 1`. The implementation preserves the raw
`F`, records the correction, and clamps only finite values in
`[-1 × 10^-8, 0)` to zero for ranking. Any value below `-1 × 10^-8` is a
blocking failure.

The rank builder must:

- require finite `logFC`, `F`, and rank scores;
- record every tiny-negative-F clamp and reject materially negative values;
- use one current symbol once per contrast;
- retain the original edgeR fields;
- sort ties deterministically by `logFC`, then symbol;
- record rank size and pathway coverage; and
- preserve unavailable records for the two non-estimable contrasts.

### 6.2 GSEA engine

Use a frozen `fgsea` version and `fgseaMultilevel` with:

- a deterministic seed derived from `contrast_id`;
- one worker for byte-stable execution;
- `eps = 0`;
- a frozen `sampleSize`;
- minimum pathway size of five genes after intersection;
- pathway size strictly smaller than the rank universe; and
- at least 30% of the source pathway represented in the rank universe.

For the 149 MitoCarta collection, run each eligible pathway once. Copy the same
raw enrichment score, normalized enrichment score, P value, and leading edge
for the matching broad-46 record, then calculate collection-specific FDR.
This prevents stochastic differences for an identical pathway tested in two
collections.

The legacy four modules are run as a separate collection.

### 6.3 GSEA outputs and interpretation

Retain:

- enrichment score and normalized enrichment score (`NES`);
- nominal P value;
- local and study-wide BH FDR;
- leading-edge genes and count;
- pathway/rank intersection size;
- source-reference coverage;
- rank size;
- positive/negative direction; and
- explicit testability status.

Interpretation:

- positive `NES` means pathway genes tend toward the AD-up end of the rank;
- negative `NES` means pathway genes tend toward the AD-down end;
- `NES` is a coordinated expression pattern, not direct pathway activity; and
- a single leading-edge gene is labeled lower confidence.

The full primary GSEA grid contains:

```text
42 contrasts × 199 program definitions = 8,358 records
```

This includes tested, not-testable, and non-estimable records.

## 7. Thresholded ORA companion

### 7.1 Frozen DEG tiers

Use the flags already stored in `broad_deg_results.tsv.gz`.

| Tier | Frozen rule | Role |
|---|---|---|
| Strict | within-contrast BH `< 0.05` and `abs(logFC) > log2(1.3)` | Confirmatory thresholded companion |
| Relaxed | within-contrast BH `<= 0.10` and `abs(logFC) >= log2(1.2)` | Prespecified sensitivity |
| Exploratory | within-contrast BH `<= 0.20`, no fold-change cutoff | Hypothesis generation only |

The implementation must independently reproduce every stored tier flag before
using it.

### 7.2 ORA query definitions

For each tier and structural contrast, construct:

1. `AD_any_mito`: AD-up and AD-down core-mito DEGs combined;
2. `AD_up_mito`: core-mito DEGs with `direction == AD_up`;
3. `AD_down_mito`: core-mito DEGs with `direction == AD_down`.

This creates:

```text
42 contrasts × 3 DEG tiers × 3 query modes = 378 query definitions
```

Observed query-size expectations among the 40 completed contrasts are:

| Tier | Combined with n≥3 | AD-up with n≥3 | AD-down with n≥3 |
|---|---:|---:|---:|
| Strict | 6 | 1 | 5 |
| Relaxed | 7 | 1 | 6 |
| Exploratory | 10 | 5 | 7 |

Empty, one-gene, two-gene, and non-estimable queries remain explicit records.

### 7.3 ORA calculation

For each
`contrast × tier × query_mode × pathway_collection × pathway`, define:

- `N`: unique tested core-mito background genes;
- `n`: unique core-mito DEG query genes;
- `M`: tested background genes in the pathway; and
- `k`: query genes in the pathway.

Calculate:

```r
p_value <- phyper(
  q = k - 1L,
  m = M,
  n = N - M,
  k = n,
  lower.tail = FALSE
)
```

Also retain the complete 2 × 2 table, overlap genes, fold enrichment, pathway
hit rate, pathway hierarchy, and source order.

For broad-46 and complete-149 pathways, require:

- `n >= 3`;
- `M >= 5`;
- `M < N`; and
- reference coverage of at least 30%.

Otherwise, write a precise not-testable reason. Zero-overlap pathways that meet
all gates remain tested with `p = 1`.

The legacy four-module profile keeps the same four-test compatibility rule as
the fine-cell release, with stricter pathway-size checks reported only as
sensitivity labels.

The complete ORA grid contains:

```text
378 query definitions × 199 program definitions = 75,222 records
```

## 8. Multiple-testing correction

### 8.1 Primary GSEA

Apply local BH independently within:

```text
contrast × pathway collection
```

Also calculate study-wide BH within:

```text
pathway collection
```

Primary GSEA significance is local BH FDR `< 0.05`. The global value is a
stricter sensitivity result.

### 8.2 Thresholded ORA

Apply local BH independently within:

```text
contrast × DEG tier × query mode × pathway collection
```

Apply study-wide BH within:

```text
DEG tier × query mode × pathway collection
```

The strict, relaxed, and exploratory tiers must never share an FDR family.
Likewise, the legacy-4, broad-46, and complete-149 collections remain separate
families.

Only strict ORA local FDR `< 0.05` is a confirmatory thresholded result.
Relaxed and exploratory q-values are sensitivity and hypothesis-generating
evidence, respectively.

## 9. Composition-adjusted GSEA sensitivity

Run the same rank-based GSEA rules on the composition-adjusted model results.

Create a 42-row composition rank manifest:

- 28 completed and testable ranks;
- 12 `not_applicable_single_fine_type` records; and
- two `contrast_not_estimable` records.

For OPCs and oligodendrocytes, `not_applicable` is not a failure: each broad
class contains only one included fine type, so there is no within-broad
fine-type mixture to adjust.

Use the same signed `sqrt(F)` rank statistic, pathway testability rules, seeds,
and FDR families as primary GSEA, but keep all composition P values and q-values
in a separate statistical profile.

The composition GSEA table also contains:

```text
42 contrasts × 199 program definitions = 8,358 records
```

Compare primary and composition profiles using:

- NES sign concordance;
- NES difference and absolute difference;
- leading-edge overlap;
- local-FDR status in each model;
- whether the primary signal survives composition adjustment; and
- the existing whole-transcriptome logFC concordance from
  `broad_deg_sensitivity_summary.tsv`.

Do not require composition ORA in the first release. Its strict core-mito
queries contain only ten genes across six contrasts, leaving only two combined
and two AD-down queries with at least three genes. Ranked GSEA is the more
informative composition sensitivity.

## 10. Broad-cell and sex/APOE summaries

Create summaries by:

- broad cell type across the six sex/APOE strata;
- sex/APOE stratum across the seven broad cell types;
- pathway and hierarchy;
- GSEA direction;
- ORA direction;
- DEG tier; and
- primary versus composition-adjusted profile.

For GSEA, report:

- number of structurally available contrasts;
- number of testable pathways;
- number with positive and negative NES;
- number significant locally and globally;
- median and range of NES;
- leading-edge gene union and recurrence; and
- whether the signal is confined to one broad cell type or stratum.

For ORA, report:

- number of testable queries;
- number significantly enriched;
- number enriched among AD-up and AD-down genes;
- median and range of fold enrichment;
- overlap-gene union and recurrence; and
- strict/relaxed/exploratory support status.

Broad cell types and sex/APOE strata share donors. Recurrence is descriptive
and must not be called independent replication.

## 11. Broad-versus-fine resolution comparison

Use the validated fine-cell result:

```text
results/minerva_production/11_pathway_deg_fine/fine_deg_pathway_ora.tsv.gz
```

Restrict comparison to:

- the seven broad classes present in both releases;
- the strict DEG tier;
- matching sex/APOE group;
- matching query mode;
- matching pathway collection; and
- matching pathway.

For each broad-cell strict ORA record, report:

- whether the broad-cell query was testable and significant;
- number of corresponding fine-cell queries tested;
- number of corresponding fine-cell queries significant;
- directional agreement;
- broad and fine overlap-gene unions; and
- one of:
  `concordant_support`, `broad_only`, `fine_only`, `neither`,
  or `not_comparable`.

This is triangulation across resolution and statistical method:

- broad DEGs use donor-level edgeR pseudobulk;
- fine DEGs use fine-cell MAST results;
- broad effects may include fine-type-composition changes; and
- fine-cell tests are not independent validations.

Do not pool P values or q-values across the two releases.

## 12. Redundancy reduction

Reuse the same MitoCarta hierarchy and gene-set Jaccard rules as the fine-cell
release.

Write all 11,026 pairwise comparisons among the 149 complete MitoCarta
pathways, including:

- pathway sizes;
- shared genes;
- Jaccard similarity;
- parent-child or ancestor-descendant relationship;
- shared top-level system; and
- a redundancy-candidate flag.

When interpreting results, report one representative biological theme when
parent and child terms are driven by the same leading-edge or overlap genes.

## 13. Required output bundle

Write under:

```text
results/minerva_production/11_pathway_deg_broad/
```

Required files:

```text
broad_deg_pathway_status.tsv
broad_deg_pathway_checks.tsv
broad_deg_pathway_artifacts.tsv
broad_deg_pathway_reference_manifest.tsv
broad_deg_pathway_program_manifest.tsv
broad_deg_pathway_contrast_manifest.tsv
broad_deg_pathway_rank_manifest.tsv
broad_deg_pathway_ranked_genes.tsv.gz
broad_deg_pathway_gsea.tsv.gz
broad_deg_pathway_significant_gsea.tsv.gz
broad_deg_pathway_background_manifest.tsv
broad_deg_pathway_background_genes.tsv.gz
broad_deg_pathway_ora_query_manifest.tsv
broad_deg_pathway_ora_query_genes.tsv.gz
broad_deg_pathway_ora.tsv.gz
broad_deg_pathway_significant_ora.tsv.gz
broad_deg_pathway_composition_rank_manifest.tsv
broad_deg_pathway_composition_ranked_genes.tsv.gz
broad_deg_pathway_composition_gsea.tsv.gz
broad_deg_pathway_composition_concordance.tsv
broad_deg_pathway_broad_cell_summary.tsv
broad_deg_pathway_sex_apoe_summary.tsv
broad_deg_pathway_broad_vs_fine_concordance.tsv.gz
broad_deg_pathway_redundancy_map.tsv.gz
README.md
```

The full GSEA and ORA tables are authoritative. Significant-only files are
convenience subsets and must never replace the complete status grids.

No figure, PowerPoint slide, PDF, or manually selected pathway list belongs in
the production data bundle.

## 14. Planned implementation files

Add:

```text
config/phase11_pathway_deg_broad.yml
scripts/lib/phase11_deg_pathway_common.R
scripts/11_run_broad_deg_pathway_analysis.R
tests/test_phase11_pathway_deg_broad.R
```

Update:

```text
scripts/run_pipeline.R
config/minerva_shared.yml
renv.lock
.gitignore
```

Register one global task mode:

```text
pathway_deg_broad
```

Place it after `pathway_deg_fine` and before KDA in the pipeline registry. One
global task is sufficient because the complete broad-cell DEG table is only
about 67 MB compressed and the enrichment grid is small.

Create the common helper by copying only the validated pure
reference-normalization, ORA, FDR, and redundancy functions from:

```text
scripts/11_run_fine_deg_pathway_analysis.R
```

The broad script will source the new helper library. It must not source the
entire fine analysis entry point because that would import unrelated CLI and
production-run state. Add parity tests showing that the copied pure functions
reproduce the frozen fine-cell toy calculations and reference normalization.
Do not refactor or regenerate the validated fine-cell release as part of the
first broad-cell implementation.

Add and freeze the `fgsea` package version in `renv.lock`. The implementation
must stop with a clear dependency error rather than installing software during
the production run.

## 15. Construction workflow

1. Validate Phase 08 broad status, checks, schemas, and required artifact
   hashes.
2. Validate all 42 structural contrasts and retain the two unavailable rows.
3. Reproduce strict, relaxed, and exploratory DEG flags.
4. Normalize and reconcile the legacy and MitoCarta program collections.
5. Build 40 primary rank vectors and two unavailable rank records.
6. Run primary GSEA and calculate local and study-wide FDR.
7. Build exact tested core-mito backgrounds.
8. Build 378 thresholded ORA query records across all tiers and directions.
9. Run the strict, relaxed, and exploratory ORA profiles with separate FDR
   families.
10. Build composition-adjusted ranks and run the separate GSEA sensitivity.
11. Build broad-cell, sex/APOE, and hierarchy-aware summaries.
12. Compare strict broad ORA descriptively with matching fine-cell ORA.
13. Run numerical, provenance, reproducibility, and reconciliation checks.
14. Write all files to a process-specific staging directory.
15. Hash every artifact and publish the status file last.

## 16. Validation requirements

### 16.1 Structural checks

- exactly seven broad cell types;
- exactly six sex/APOE strata;
- exactly 42 planned contrasts;
- exactly 40 completed and two non-estimable contrasts;
- exactly 42 primary rank records;
- exactly 378 ORA query records;
- exactly four legacy, 46 broad, and 149 complete pathway definitions;
- exactly 8,358 primary GSEA rows;
- exactly 75,222 ORA rows;
- exactly 8,358 composition GSEA rows; and
- unique keys in every manifest and statistical table.

### 16.2 Input and gene-identity checks

- all required broad DEG artifacts match their declared hashes and byte sizes;
- the 42 physical contrast slices reconstruct the 786,242-row combined table;
- stored DEG-tier flags reproduce from q-values, logFC, and frozen thresholds;
- all primary background/rank genes are tested `core_mito_protein` genes;
- tested core-mito background sizes are exactly
  1,084/1,134/1,113/1,033/1,070/1,104/573 in the frozen broad-cell order;
- all symbols are current, nonmissing, and unique within contrast;
- every ORA query is a subset of its exact background;
- every GSEA pathway is intersected only with the exact matching rank universe;
- non-estimable contrasts contain no fabricated ranks or queries; and
- MitoCarta normalization matches the frozen 149-pathway authority.

### 16.3 GSEA numerical checks

- rank score equals `sign(logFC) * sqrt(max(F, 0))`, with the frozen
  `1 × 10^-8` negative-F tolerance;
- exactly one primary core-mito F statistic is clamped and no materially
  negative F statistic is accepted;
- every rank score is finite;
- rank order is deterministic;
- positive and negative NES labels match the NES sign;
- leading-edge genes belong to the tested rank and pathway;
- broad-46 raw statistics exactly match the same pathways in complete-149;
- repeated seeded runs reproduce a frozen audit subset;
- an independent full rerun is byte-identical; and
- local and global BH values reproduce independently.

### 16.4 ORA numerical checks

- contingency cells are nonnegative and sum to `N`;
- `k <= n`, `k <= M`, and `n <= N`;
- P values reproduce the frozen hypergeometric formula;
- zero-overlap tests have `p = 1`;
- an audited subset matches one-sided Fisher exact tests;
- BH values reproduce independently within every declared family; and
- known toy examples pass.

### 16.5 Sensitivity and resolution checks

- composition statuses reconcile to 28 complete, 12 not applicable, and two
  non-estimable;
- all 28 composition result sets join exactly to gene annotations;
- composition q-values remain separate from primary q-values;
- the broad-versus-fine comparison uses only the seven shared broad classes;
- matching requires exact group, direction, collection, and pathway; and
- no P values are pooled across models or resolutions.

## 17. Execution plan

First run unit tests and a dry run:

```bash
Rscript tests/test_phase11_pathway_deg_broad.R

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway_deg_broad \
  --dry-run
```

Expected graph:

```text
one global:pathway_deg_broad task
```

Then execute:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway_deg_broad
```

The workload is locally feasible. It contains only 75,222 ORA records and
16,716 primary-plus-composition GSEA status records. Runtime should be measured
rather than promised, but memory should remain modest relative to the existing
broad-cell DEG pipeline.

After execution:

1. run the output-bundle validator;
2. repeat the pipeline command to confirm safe hash-valid resume;
3. perform a byte-identical independent rerun in a temporary directory;
4. inspect sparse-query and pathway-coverage attrition; and
5. review leading findings only after every blocking check passes.

## 18. Explicit non-inputs

The required analysis must not use:

- KDA-returned driver genes;
- deprecated direct broad-cell KDA outputs;
- SEA-AD results;
- fine-cell P values to alter broad-cell significance;
- manually selected pathways from the analysis document or presentation;
- Phase 10 similarity scores or rank tails; or
- a whole-genome background for mitochondrial-only ORA.

The broad-versus-fine table is a descriptive downstream comparison only.

## 19. Interpretation rules

Permitted statements include:

- “This mitochondrial program was coordinately shifted toward higher
  expression in AD in female APOE ε3/ε3 astrocytes.”
- “The strict DEG ORA supported the same program identified by ranked GSEA.”
- “The pathway direction remained concordant after composition adjustment.”
- “Fine-cell and broad-cell analyses showed descriptive agreement for this
  theme.”

Do not claim:

- that GSEA or ORA proves pathway activity or respiratory function;
- that a pathway is controlled by a KDA driver;
- that significance in one stratum and not another proves an interaction;
- that relaxed or exploratory ORA is confirmatory;
- that repeated broad-cell findings are independent donor replications; or
- that multiple overlapping parent/child terms are separate mechanisms.

The broad-cell primary model is donor-level and generally more appropriate for
donor-level inference than nucleus-level MAST. However, formal claims of
sex/APOE specificity still require direct interaction models.

## 20. Acceptance criteria

The phase is complete when:

- the validated bundle exists under
  `results/minerva_production/11_pathway_deg_broad/`;
- every one of the 42 contrasts has an explicit status;
- all tested core-mito ranks reconcile to the broad DEG release;
- primary GSEA is complete for all eligible contrasts;
- strict, relaxed, and exploratory ORA remain separate and reproducible;
- composition sensitivity is explicit;
- broad-versus-fine comparison is descriptive and key-exact;
- pathway redundancy is explicit;
- all input and output artifacts are checksummed;
- status is `validated_complete`; and
- no upstream or fine-cell result is modified.

## 21. Implementation checklist

### Freeze

- [x] Freeze GSEA rank statistic, engine version, seed, and precision settings.
- [x] Freeze strict, relaxed, and exploratory ORA roles.
- [x] Freeze exact GSEA and ORA FDR families.
- [x] Freeze the legacy-4, broad-46, and complete-149 program collections.
- [x] Freeze composition and broad-versus-fine comparison rules.
- [x] Freeze output schemas and expected structural counts.

### Implement

- [x] Add the scientific configuration.
- [x] Add the broad-cell pathway script.
- [x] Add and lock the `fgsea` dependency.
- [x] Add automated GSEA, ORA, and failure-state tests.
- [x] Register the global `pathway_deg_broad` task.
- [x] Build complete rank, background, and query manifests.
- [x] Implement primary and composition GSEA.
- [x] Implement all three ORA tiers and query directions.
- [x] Implement pathway redundancy and resolution-concordance summaries.
- [x] Write atomic status, checks, and artifact manifests.

### Validate and run

- [x] Run unit and deterministic-reproducibility tests.
- [x] Review mapping and pathway-coverage attrition.
- [x] Run the pipeline dry run.
- [x] Execute the production task.
- [x] Validate every output hash and numerical check.
- [x] Confirm safe resume and byte-identical independent reproduction.
- [x] Prepare an initial interpretation summary; detailed finding
  prioritization remains a downstream analysis task.
