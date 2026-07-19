# Phase 11: Yu-Style Mitochondrial Pathway Data for Figures 3–6

## Status and phase boundary

This document defines the implementation plan for the new Phase 11. It follows
the validated Phase 10 mitochondrial-similarity phase and prepares the pathway
enrichment tables and panel-ready data needed for later mitochondrial
analogues of Yu Figures 3, 4, 5, and 6.

Phase 11 is one global data-production task. It will:

- validate the complete Phase 10 bundle;
- freeze and validate the pathway references used for enrichment;
- use the stored Phase 10 top- and bottom-score mitochondrial gene sets;
- perform one-sided hypergeometric overrepresentation analysis (ORA);
- apply explicitly scoped Benjamini–Hochberg correction;
- prepare long-form similarity-count data for later `A` panels;
- prepare complete pathway-enrichment data for later `B` panels; and
- write complete query, enrichment, panel-data, QC, provenance, and status
  tables.

The output directory is:

```text
results/<environment>/11_pathway/
```

Phase 11 must **not** refit MAST, reconstruct Phase 09 DEG states, recalculate
Phase 10 similarity scores or ranks, or select new score tails after looking at
pathway results.

Phase 11 also must **not** draw, assemble, or export any figure. The separate
[Phase 11 Figures 3–6 generation guide](../figures/phase_11_mitochondrial_figures_3_to_6_guide.md)
defines how the validated Phase 10 and Phase 11 data are converted into visual
panels after this phase is complete.

The broader cell-cluster-specific pathway atlas described in
[mitochondrial_pathways_explained.md](mitochondrial_pathways_explained.md) is
scientifically valuable, but it is not required to reproduce Yu Figures 3–6.
The following analyses are therefore deferred to a later phase:

- 324 cell-cluster-by-sex/APOE AD-versus-NCI pathway tests;
- ranked gene-set enrichment of continuous MAST statistics;
- direct upregulated-versus-downregulated DEG ORA within each cell cluster;
- nuclear-only, mtDNA-only, and cell-cluster pathway matrices; and
- formal pathway interaction tests across sex and APOE groups.

This boundary keeps Phase 11 aligned with its data responsibility: provide all
validated inputs required for later cross-cell-type Yu-style figures while
restricting the ranked genes and statistical backgrounds to
mitochondrial-related genes.

## High-level purpose

Yu et al. ranked transcriptome-wide genes by the Zhang–Yu similarity measure.
Their Figures 3–5 displayed the top and bottom 25 genes in panel A and pathway
enrichment of the top and bottom 200 genes in panel B. Figure 6 displayed the
top and bottom 10 genes separately within APOE e2, e33, and e4, then showed
pathway enrichment of the genes with the greatest sex divergence.

Phase 10 has already performed the mitochondrial-restricted ranking. Phase 11
will use those frozen rankings to prepare data for:

- Figure 3 analogue: Female-versus-Male across all APOE groups;
- Figure 4 analogue: APOE e2-versus-e33 across both sexes;
- Figure 5 analogue: APOE e4-versus-e33 across both sexes; and
- Figure 6 analogue: Female-versus-Male separately within e2, e33, and e4.

The primary downstream data profile uses the Phase 10 `core_mito` universe.
The inclusive `all_mito_related` universe is a prespecified sensitivity
profile, not a replacement chosen after viewing results.

The pathway analysis has two frozen collections:

1. Human MSigDB C2:CP canonical pathways for the closest feasible Yu
   comparison.
2. MitoCarta3.0 MitoPathways for a focused mitochondrial interpretation.

The later Figure 3–6 analogues will use C2:CP for their `B`-panel data, matching
the collection class reported by Yu. Phase 11 also writes complete
MitoPathways results as a focused companion dataset.

## Relationship to Yu and deliberate differences

### What remains the same

- Similarity panel genes are selected from stored Zhang–Yu score ranks.
- Figures 3–5 use top and bottom 25 genes in panel A.
- Figure 6 uses top and bottom 10 genes within each APOE group in panel A.
- Pathway analysis uses 200-gene rank tails.
- ORA is a one-sided hypergeometric test for overrepresentation.
- P values are adjusted by the Benjamini–Hochberg method.
- C2:CP canonical pathways supply the primary downstream pathway collection.
- Gene ratio, overlap count, and adjusted P value are retained for later
  pathway panels.

### What changes

| Item | Yu analysis | New Phase 11 |
|---|---|---|
| Ranked gene universe | Transcriptome-wide | Phase 10 `core_mito` primary; `all_mito_related` sensitivity |
| Ranking source | Yu transcriptome-wide similarity analysis | Frozen Phase 10 mitochondrial similarity output |
| Background | Reported as all genes in the dataset | Comparison- and universe-specific Phase 10 ranking-eligible mitochondrial genes |
| Query size | Nominal top or bottom 200 | Actual stored Phase 10 `selected_k`; never assumed to equal 200 |
| Missing tests | Not detailed in figure captions | Already handled by Phase 10 coverage eligibility and retained in panel metadata |
| Pathway release | Not reported in the paper | Human MSigDB C2:CP v2026.1.Hs, frozen by checksum before execution |
| Mitochondrial pathway source | No dedicated MitoPathways analysis | MitoCarta3.0 MitoPathways companion analysis |
| Figure 6 enrichment tail | Caption and text use different wording | Stored `low_score` 200-gene tail is primary because Results section 3.5 explicitly says bottom 200 |
| Feature identity | Published gene symbols | Exact Phase 10 feature in panel A; unique current HGNC symbol in ORA |
| No significant pathways | Only enriched pathways are displayed | Phase 11 records an explicit no-significant-pathway status for downstream display |

These are Yu-style mitochondrial analogues, not exact reproductions of the
published transcriptome-wide figures. In particular, changing both the ranked
gene pool and its statistical background changes the null hypothesis and the
resulting P values.

Because Yu did not report an MSigDB release, exact recovery of the paper's
pathway set is not possible from the paper alone. Phase 11 freezes Human MSigDB
v2026.1.Hs for reproducibility and records this difference in every status and
downstream-panel manifest.

## Frozen scientific definition

### Primary and sensitivity analysis universes

Phase 11 inherits the two Phase 10 analysis universes without redefining them:

| `analysis_universe` | Included Phase 09 tiers | Phase 11 role |
|---|---|---|
| `core_mito` | `core_mito_protein` | Required primary downstream data profile |
| `all_mito_related` | `core_mito_protein`, `mtdna_noncoding`, `mito_extended` | Prespecified inclusive sensitivity |

Only rows with `ranking_eligible = TRUE` in the matching Phase 10
`comparison_id` enter an ORA background. A reference-only or
coverage-ineligible feature remains in Phase 10 provenance but does not enter
the Phase 11 query or background.

Universe membership must come from Phase 10. Phase 11 must not rebuild it from
MitoCarta, Reactome, gene-name prefixes, or a new annotation rule.

### Downstream comparison and tail mapping

| Output panel | `comparison_id` | Panel A rank set | Panel B primary query |
|---|---|---:|---|
| Figure 3A | `female_vs_male_all_apoe` | high and low 25 | — |
| Figure 3B | `female_vs_male_all_apoe` | — | high and low 200 |
| Figure 4A | `e2_vs_e33_all_sexes` | high and low 25 | — |
| Figure 4B | `e2_vs_e33_all_sexes` | — | high and low 200 |
| Figure 5A | `e4_vs_e33_all_sexes` | high and low 25 | — |
| Figure 5B | `e4_vs_e33_all_sexes` | — | high and low 200 |
| Figure 6A, e2 | `female_vs_male_e2` | high and low 10 | — |
| Figure 6A, e33 | `female_vs_male_e33` | high and low 10 | — |
| Figure 6A, e4 | `female_vs_male_e4` | high and low 10 | — |
| Figure 6B | three within-APOE comparisons | — | low 200 from e2, e33, and e4 |

Phase 11 will run ORA for both high- and low-score 200-gene tails for all six
comparisons and both analysis universes. This preserves the complete Phase 10
handoff and permits supplemental analyses. The required Figure 6B uses only
the three `low_score` results.

Use `high_score` and `low_score` in data files. Figure labels may add
`highest relative concordance` and `greatest relative divergence`, but a gene
or pathway must not be called significantly concordant or divergent solely
because it occurs in a rank tail.

### Feature identity for similarity data and gene identity for ORA

Panel A retains the exact Phase 10 feature identity:

```text
panel_feature_id = similarity_feature_id
```

The downstream gene symbol is a label only. If two selected features share a
symbol, the panel-ready data must provide a disambiguated label containing the
feature ID.

Pathway databases are HGNC-symbol gene sets, so the ORA unit is:

```text
pathway_gene_id = symbol_hgnc_current
```

For every query and background:

- discard no row merely because it lacks a pathway membership;
- require a nonmissing current HGNC symbol for ORA admission;
- count each admitted HGNC symbol once;
- report features lost during symbol mapping;
- collapse a repeated symbol within one tail to one query gene; and
- fail if the same symbol is represented by different features in both high
  and low tails of one comparison/universe, because its gene-level tail is
  ambiguous.

The current validated Minerva Phase 10 bundle has no duplicate eligible HGNC
symbols, no within-tail duplicate symbols, and no symbol appearing in both
200-gene tails. Phase 11 must still enforce these checks rather than relying on
that observation.

### Frozen pathway collection 1: MSigDB C2:CP

The required Yu-comparability reference is:

```text
data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt
```

The frozen reference properties are:

| Property | Required value |
|---|---|
| Species | Human |
| Identifier namespace | HGNC gene symbols |
| MSigDB release | `2026.1.Hs` |
| Collection | `C2:CP` canonical pathways |
| Expected source pathways | 4,115 |
| SHA-256 | `af1b31c091f5d296438f6ca20fba0286ca31fd8ae84efd6317675e6579968093` |

The file must be obtained from the official
[MSigDB Human collections page](https://www.gsea-msigdb.org/gsea/msigdb/collections.jsp).
MSigDB registration is required for the download. Do not download a pathway
reference dynamically during a pipeline run, and do not redistribute the file
unless its terms permit that use.

For each GMT record, retain the source pathway name, description/URL field,
all unique symbols, source set size, and deterministic source order. Empty
names, duplicate pathway names, empty gene sets, or duplicate symbols within a
set are blocking validation errors after normalization.

### Frozen pathway collection 2: MitoCarta3.0 MitoPathways

The focused reference is the existing frozen workbook:

```text
data/reference/Human.MitoCarta3.0.xls
```

Required properties are:

| Property | Required value |
|---|---|
| Workbook SHA-256 | `e6ada0ae8dcd5447a5efb6f77c69a1c10b1ffa66521540a1e81b92c61e5505f2` |
| Sheet | `C MitoPathways` |
| Nonblank pathways | 149 |
| Unique pathway names | 149 |
| Gene-pathway memberships | 3,904 |
| Unique member symbols | 1,035 |
| Source pathway-size range | 1–461 |

Phase 11 must parse the comma-delimited `Genes` field directly from the
workbook, trim symbols, remove within-pathway duplicates, and discard five
blank spacer rows. It must retain the complete hierarchy string and derive:

- `hierarchy_depth`;
- `level_1`, `level_2`, and `level_3_or_deeper` labels when present;
- parent pathway; and
- broad-versus-detailed pathway status.

The existing Phase 03 files
`results/<environment>/03_annotations/mitocarta_pathways.tsv` and
`mitocarta_pathways.gmt` are explicit non-inputs. Their known parser defect
treated the comma-delimited MitoPathway gene field as pipe-delimited, producing
incorrect `gene_count` values and invalid GMT membership. Phase 11 therefore
builds and validates its own normalized MitoPathways reference table from the
frozen source workbook without changing Phase 03 outputs.

### Query construction

For each `comparison_id × analysis_universe × tail`, read the stored Phase 10
rank-set rows with:

```text
requested_k = 200
tail in {high_score, low_score}
```

The query is the set of unique, successfully mapped current HGNC symbols among
those rows. Store separately:

- `requested_k` from Phase 10;
- `selected_k` from Phase 10;
- `rank_set_feature_rows` read from the file;
- `mapped_unique_query_genes` used as `n`;
- unmapped feature count and IDs;
- duplicate-symbol collapse count; and
- exact query-gene list and source feature list.

Phase 11 must not fill a Phase 10 tail shortfall, pull the next ranked gene,
drop a selected gene because it is not in any pathway, or replace one tail
with the other after viewing enrichment.

### Background construction

For each `comparison_id × analysis_universe`, the ORA background is the set of
unique current HGNC symbols among Phase 10 rows that are:

```text
ranking_eligible == TRUE
and members of the requested Phase 10 analysis_universe
```

The background is independent of pathway membership. A mitochondrial gene
that belongs to no C2:CP or MitoPathways set remains part of `N`.

The query must be a subset of its background. The script must fail if any
mapped query symbol is absent from the matching background.

This background answers:

> Within mitochondrial genes eligible for this Zhang–Yu comparison, is a
> pathway unusually common in the selected score tail?

It does not answer whether the pathway is enriched relative to the complete
transcriptome. That transcriptome-wide question is outside the Phase 11
figure goal because Phase 10 did not rank transcriptome-wide genes.

### Pathway coverage and eligibility

For a pathway and one query/background pair, define:

```text
source_pathway_size = unique source symbols in the pathway
background_pathway_size = M = source symbols present in the ORA background
background_size = N
reference_coverage = M / source_pathway_size
```

Every source pathway receives a result row, including pathways that are not
testable. Eligibility is frozen by collection:

| Collection | Testability rule |
|---|---|
| `msigdb_c2_cp_v2026_1` | `M >= 5` and `M < N` |
| `mitocarta_mitopathways_v3_0` | `M >= 5`, `M < N`, and `reference_coverage >= 0.30` |

Pathways with 5–9 background genes are labeled `small_pathway_lower_confidence`.
Pathways with at least 10 are labeled `standard_pathway_size`. Both may be
tested, but the size label must remain in the output and focused figure data.

An ineligible pathway has `test_status = not_testable`, an explicit reason,
and `NA` P/FDR values. It must not enter a BH family. `Not testable` and `not
significant` must never be conflated.

### Overrepresentation test

For one eligible pathway and one query, let:

- `N` be the number of unique background genes;
- `n` be the number of unique query genes admitted to that background;
- `M` be the number of background genes in the pathway; and
- `k` be the number of query genes in the pathway.

Calculate the one-sided hypergeometric probability of observing at least `k`
pathway genes:

```r
p_value <- phyper(
  q = k - 1L,
  m = M,
  n = N - M,
  k = n,
  lower.tail = FALSE
)
```

Store the complete 2 × 2 table:

| | In pathway | Not in pathway |
|---|---:|---:|
| Query tail | `k` | `n - k` |
| Background outside query | `M - k` | `N - M - n + k` |

Also calculate:

```text
gene_ratio = k / n
background_ratio = M / N
fold_enrichment = (k / n) / (M / N)
pathway_hit_rate = k / M
```

`gene_ratio` is the x-axis value in the `B` panels. It is not a fold change,
pathway activity score, or fraction of the pathway detected. A zero overlap
has `p_value = 1`, `gene_ratio = 0`, and `fold_enrichment = 0`.

The implementation must reproduce prespecified hand-calculated ORA examples
and cross-check an audited subset with `fisher.test(..., alternative =
"greater")`.

### Multiple-testing correction

The primary BH family is:

```text
comparison_id
× analysis_universe
× pathway_collection
× tail
```

Only eligible pathways enter that family. Store:

- raw hypergeometric `p_value`;
- `tail_fdr_bh`, the primary within-query adjusted value;
- `tail_fdr_family_size`; and
- `tail_fdr_significant = tail_fdr_bh < 0.05`.

As a stricter sensitivity analysis, calculate `global_fdr_bh` across all
eligible Phase 11 ORA rows within each:

```text
analysis_universe × pathway_collection
```

The downstream primary pathway status is `tail_fdr_bh < 0.05`, matching the
per-gene-list interpretation of Yu's enrichment analyses. The global FDR is
reported as a sensitivity result and must not replace the primary FDR after
results are seen.

Phase 11 does not cap or select displayed pathway names. It writes all
testable and not-testable pathways, their deterministic statistical order, and
an explicit count of primary-FDR-significant pathways per query. The separate
figure guide owns any later display cap, empty-panel text, layout, or visual
ordering.

### Similarity panel-data preparation

The panel-A-ready table must use the exact rank-set records stored by Phase 10:

- `requested_k = 25` for Figures 3–5;
- `requested_k = 10` for each Figure 6 APOE comparison;
- both `high_score` and `low_score` tails; and
- Phase 10 `selection_order` within each tail.

Join each selected feature to the nine stored Phase 10 state-pair counts:

```text
S_pos1_pos1
S_neg1_neg1
S_pos1_0
S_neg1_0
S_0_pos1
S_0_neg1
S_pos1_neg1
S_neg1_pos1
S_0_0
```

Store the occurrence count and
`occurrence_fraction = occurrence_count / paired_tests`. The data phase does
not decide which quantity will be used as a visual fill.

For every selected feature, retain:

- `similarity_score`;
- the universe-specific Phase 10 `directional_fdr_bh`;
- `paired_tests / nominal_dimensions`;
- `score_scope`; and
- mitochondrial tier and genome origin.

Phase 11 must verify the nine counts against
`mitochondrial_similarity_state_pairs.tsv.gz`. Missing states remain excluded
from counts and denominators. A zero state-pair count means no observed pair
had that state; it is not imputation of missing values to `(0,0)`.

### Downstream panel profiles

Prepare stable profile labels so the later figure task does not need to infer
scientific choices:

```text
primary_yu_mito:
  analysis_universe = core_mito
  pathway_collection = msigdb_c2_cp_v2026_1

focused_mitopathways:
  analysis_universe = core_mito
  pathway_collection = mitocarta_mitopathways_v3_0

inclusive_yu_sensitivity:
  analysis_universe = all_mito_related
  pathway_collection = msigdb_c2_cp_v2026_1
```

For Figures 3–5, mark both high- and low-score 200-gene queries as required
panel-B data. For Figure 6, mark only the three low-score 200-gene queries as
required primary panel-B data while retaining both tails in the complete ORA
table. Record actual query size, background size, release, universe, and FDR
family in the panel-profile manifest.

## Inputs and dependencies

### Required Phase 10 inputs

Phase 11 consumes the validated bundle under:

```text
results/<environment>/10_similarity/
```

| Input | Requirement and role |
|---|---|
| `similarity_status.tsv` | Schema `mitochondrial_similarity_status_v1`; production must be `validated_complete`. |
| `similarity_checks.tsv` | Every blocking Phase 10 check must pass. |
| `similarity_artifacts.tsv` | Every declared artifact must exist and match path, bytes, rows, checksum, and validation status. |
| `similarity_comparison_manifest.tsv` | Supplies exactly six comparison definitions, Yu analogues, dimensions, and panel sizes. |
| `mitochondrial_similarity_feature_manifest.tsv` | Supplies feature identity and universe membership checks. |
| `mitochondrial_similarity_results.tsv.gz` | Supplies eligibility backgrounds, scores, FDR, coverage, annotations, and nine state-pair counts. |
| `mitochondrial_similarity_rank_sets.tsv` | Supplies exact 10-, 25-, and 200-gene high/low selections and order. |
| `mitochondrial_similarity_state_pairs.tsv.gz` | Audits similarity-category counts and missing-state handling. |

The Phase 10 unique result key is:

```text
comparison_id + similarity_feature_id
```

The Phase 10 rank-set key is:

```text
rank_set_id + selection_order
```

Phase 11 must validate both before any query or figure construction.

### Observed validated Minerva Phase 10 baseline

The current production input has:

| Property | Observed value |
|---|---:|
| Validation status | `validated_complete` |
| RDS sets | 9 |
| Fine cell types | 54 |
| Comparison families | 6 |
| Mitochondrial manifest features | 1,300 |
| Phase 10 result rows | 7,800 |
| Phase 10 rank-set rows | 5,220 |
| Production permutations | 10,000 |

The comparison-specific ORA background sizes are:

| Comparison | `core_mito` | `all_mito_related` |
|---|---:|---:|
| `female_vs_male_all_apoe` | 700 | 766 |
| `e2_vs_e33_all_sexes` | 708 | 775 |
| `e4_vs_e33_all_sexes` | 686 | 751 |
| `female_vs_male_e2` | 732 | 798 |
| `female_vs_male_e33` | 705 | 770 |
| `female_vs_male_e4` | 679 | 743 |

Every production high/low 200-gene rank set contains exactly 200 features with
no size shortfall. These observed values are preflight baselines, not values to
hard-code in the algorithm.

Current production input checksums are:

| File | SHA-256 |
|---|---|
| `similarity_status.tsv` | `b0f5b6bba7ab3fd3305c266432d17564ee96cf01b0d801bd33198ad82133bdb9` |
| `similarity_checks.tsv` | `65cffd89628f72c8bb98ef1786737b86b9aeee8639d5f0e301718a8e036ac826` |
| `similarity_artifacts.tsv` | `b48a4a080825d11000d6ae0ef0c0353aae30b6956a166ee770b363b7aa003b15` |
| `similarity_comparison_manifest.tsv` | `4de8cc2557ead673c36369ecd6b184fcb3c0cdbff015dacd2736760d526a2ae3` |
| `mitochondrial_similarity_results.tsv.gz` | `31d677d35beeb528841e8113d34644d401b5cddff1c5c3a772bc2ad085dc073a` |
| `mitochondrial_similarity_rank_sets.tsv` | `04fecc29c5e4bc3ddb926e5be625e2b2e38d6cbae419da6663f172981f30ed53` |

These hashes document the repository state when this plan was written. The
Phase 11 script must validate the authoritative runtime values through the
Phase 10 artifact manifest and record the actual hashes used.

### Observed local Phase 10 baseline

The local Vasculature Phase 10 bundle is a validated software smoke test with
five fine cell types and 100 permutations. Its core-mitochondrial 200-tail
selections are capped to remain disjoint:

| Comparison | Core eligible genes | Selected per high/low 200 tail |
|---|---:|---:|
| `female_vs_male_all_apoe` | 306 | 153 |
| `e2_vs_e33_all_sexes` | 284 | 142 |
| `e4_vs_e33_all_sexes` | 324 | 162 |
| `female_vs_male_e2` | 201 | 100 |
| `female_vs_male_e33` | 307 | 153 |
| `female_vs_male_e4` | 321 | 160 |

Phase 11 must use these actual local sizes in `n` and label all local figures
`nonfinal_smoke_test`. The local output is not a 54-cell-type scientific
result.

### Required pathway-reference inputs

```text
data/reference/Human.MitoCarta3.0.xls
data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt
```

Both frozen references are present. The official MSigDB C2:CP file has
SHA-256 `af1b31c091f5d296438f6ca20fba0286ca31fd8ae84efd6317675e6579968093`
and contains 4,115 unique pathway records with no malformed records or
duplicate pathway names. The Phase 11 script must still enforce these values
and all MitoCarta normalization invariants before every run.

### Required configuration

Add:

```text
config/phase11_pathway.yml
```

It freezes at minimum:

- primary and sensitivity Phase 10 analysis universes;
- the six comparison IDs and Figure 3–6 panel mapping;
- rank-set sizes 10, 25, and 200;
- Figure 6 primary low-score-tail decision;
- C2:CP v2026.1.Hs path, expected set count, and SHA-256;
- MitoCarta3.0 path, sheet, checksum, and expected pathway invariants;
- symbol-normalization and duplicate policy;
- pathway testability thresholds;
- one-sided hypergeometric formula;
- primary and global BH families and `0.05` threshold;
- deterministic statistical ordering and downstream panel-profile flags;
- expected Phase 10 input schemas; and
- expected Phase 11 output schemas.

The project configs point to this file through:

```yaml
project:
  phase11_pathway_config: config/phase11_pathway.yml
```

### Required software

The implementation can use the packages already represented in the project
environment:

- `data.table` for tables;
- `yaml` for configuration;
- `digest` for deterministic provenance hashes;
- `readxl` for the frozen MitoCarta workbook.

The hypergeometric test uses base R `phyper`; GOtest is not required to
reproduce the stated statistic. If a new package is added, update and validate
`renv.lock` before production rather than installing it dynamically on a
compute node.

### Explicit non-inputs

Phase 11 must not read:

- normalized Seurat RDS files;
- Phase 07 pseudobulk results;
- Phase 08 MAST files directly;
- Phase 09 annotation files directly;
- Yu Supplemental Table S2 as a rank or significance oracle;
- the Yu PDF as a runtime data source;
- a previous enrichment result or figure;
- the known-defective Phase 03 `mitocarta_pathways.tsv` or GMT;
- the Phase 09 four-pathway Reactome V97 extended-tier GMT as a test
  collection; or
- any dynamically downloaded pathway database.

The Yu paper and explanatory documents are method specifications and review
references only.

## Construction workflow

### 1. Validate Phase 10

- require the expected status schema and terminal status;
- verify every Phase 10 artifact checksum, byte count, row count, and schema;
- require every blocking Phase 10 check to pass;
- require exactly six comparison IDs;
- validate result, rank-set, and state-pair keys;
- verify that every rank-set record joins exactly once to its result; and
- require the configured universe-specific FDR column and eligibility fields.

### 2. Normalize and validate pathway references

- parse the frozen C2:CP symbol GMT;
- parse MitoCarta sheet `C MitoPathways` with comma-delimited genes;
- discard only documented blank rows;
- deduplicate within-set symbols without changing source order;
- create a long collection/pathway/symbol membership table;
- derive MitoPathways hierarchy fields;
- require the frozen reference counts and checksums; and
- publish a Phase 11 reference manifest before running ORA.

### 3. Build background manifests

- filter Phase 10 results to `ranking_eligible = TRUE`;
- assign membership in each inherited analysis universe;
- map features to unique current HGNC symbols;
- enumerate one background per comparison and universe;
- record all admitted and excluded features with reasons; and
- reconcile observed background sizes to Phase 10 eligibility counts.

### 4. Build query manifests and query-gene tables

- read all stored high/low rank sets with `requested_k = 200`;
- create 24 query IDs: six comparisons × two universes × two tails;
- retain actual `selected_k`, feature IDs, ranks, scores, FDR, and coverage;
- map to unique query symbols;
- require every query to be a subset of its matching background; and
- flag the nine query IDs used in the required primary `B` panels.

### 5. Construct the complete ORA grid

- cross each of the 24 queries with all 4,115 C2:CP pathways and all 149
  MitoPathways;
- calculate `N`, `n`, `M`, `k`, coverage, and the complete contingency cells;
- assign testability and small-pathway status;
- calculate one-sided hypergeometric P values for eligible rows;
- retain explicit not-testable rows; and
- store overlap genes and source Phase 10 features deterministically.

With the frozen reference counts, production should contain:

```text
24 queries × (4,115 C2:CP + 149 MitoPathways)
= 102,336 complete ORA rows
```

### 6. Apply multiple-testing correction

- calculate primary BH FDR independently within each query and collection;
- record exact family sizes;
- calculate the prespecified collection/universe global FDR sensitivity;
- leave ineligible rows without P or FDR values; and
- verify BH values by recalculation from stored raw P values.

### 7. Build similarity panel data

- select stored 25- or 10-gene tails for both universes;
- join the nine Phase 10 state-pair counts;
- reconcile counts against the state-pair table;
- reshape to long panel-ready data;
- retain occurrence count and occurrence fraction; and
- preserve Phase 10 ordering, score, FDR, scope, and coverage annotations.

### 8. Build pathway panel data

- identify the nine required primary panel-B query families;
- retain all pathways with statistical order and primary/global significance;
- record an explicit zero-significant-pathway status per query;
- build focused core-MitoPathways panel data; and
- build inclusive-universe sensitivity panel data without changing the
  primary selection.

### 9. Validate and atomically publish

- run reference, query, ORA, FDR, panel-data, and provenance checks;
- write every table to a process-specific temporary path;
- hash and inventory every final artifact;
- publish `pathway_status.tsv` last; and
- do not treat a partial directory as resumable.

## Outputs and files created

Create the following under:

```text
results/<environment>/11_pathway/
```

| File | Contents |
|---|---|
| `pathway_reference_manifest.tsv` | Collection names, releases, source paths/URLs, checksums, source and normalized set/member counts, identifier namespace, and validation. |
| `pathway_membership_long.tsv.gz` | One row per collection/pathway/current source symbol with source order and MitoPathways hierarchy fields. |
| `pathway_background_manifest.tsv` | One row per comparison/universe background with feature and unique-symbol counts, exclusions, and input hashes. |
| `pathway_background_genes.tsv.gz` | Exact admitted feature-to-symbol records for every comparison/universe background. |
| `pathway_query_manifest.tsv` | Exactly 24 high/low 200-tail query definitions with requested, selected, mapped, and excluded sizes and figure-use flags. |
| `pathway_query_genes.tsv.gz` | Exact Phase 10 feature, symbol, rank, score, FDR, and coverage rows entering every query. |
| `similarity_tail_pathway_ora.tsv.gz` | Complete 102,336-row production ORA grid with coverage, testability, contingency cells, ratios, P values, local/global FDR, overlaps, and deterministic statistical order. |
| `similarity_panel_data.tsv.gz` | Long selected-feature-by-state-pair table with counts, fractions, rank order, score, FDR, and coverage for downstream panel A. |
| `pathway_panel_data.tsv.gz` | All pathway rows for the required downstream profiles with statistical order and explicit significant/empty-query status; no visual cap is applied. |
| `downstream_panel_manifest.tsv` | Figure analogue, panel, profile, comparison, universe, pathway collection, required tail/query, expected row counts, and data-source keys. |
| `pathway_toy_checks.tsv` | Hand-calculated ORA and count-reshape examples with expected and observed results. |
| `pathway_qc_summary.tsv` | Counts by collection, query, universe, tail, testability, pathway size, significance, mapping, and downstream profile. |
| `pathway_checks.tsv` | One row per blocking or informational reference, key, mapping, ORA, FDR, panel-data, or provenance check. |
| `pathway_artifacts.tsv` | Artifact path, schema, bytes, rows, SHA-256, and validation status. |
| `pathway_status.tsv` | One global task record with exact input/config/code/reference hashes, counts, software versions, timing, and terminal state. |

The Phase 11 output directory must contain no `.pdf`, `.png`, `.svg`,
plot object, or assembled figure. Those artifacts belong to the separate
figure-generation workflow documented under `docs/figures`.

Use versioned schemas:

```text
pathway_reference_manifest_v1
pathway_membership_long_v1
pathway_background_manifest_v1
pathway_query_manifest_v1
similarity_tail_pathway_ora_v1
mitochondrial_similarity_panel_data_v1
mitochondrial_pathway_panel_data_v1
downstream_panel_manifest_v1
pathway_checks_v1
pathway_artifacts_v1
mitochondrial_pathway_status_v1
```

## Files added or changed during implementation

### New files

| File | Required content |
|---|---|
| `config/phase11_pathway.yml` | Frozen universes, references, checksums, queries, ORA/testability rules, FDR families, downstream profiles, and schemas. |
| `scripts/11_prepare_mitochondrial_pathway_data.R` | Global Phase 11 reference parsing, query/background construction, ORA, validation, panel-ready tables, atomic outputs, and status bundle. |
| `data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt` | User-obtained frozen official C2:CP symbol GMT; treatment in version control must follow MSigDB terms. |
| `docs/phase_11_pathway/phase_11_mitochondrial_pathway_data_plan.md` | This implementation and execution plan. |
| `docs/figures/phase_11_mitochondrial_figures_3_to_6_guide.md` | Separate downstream instructions for rendering Figures 3–6 from validated Phase 10 and Phase 11 data. |

### Existing files changed

| File | Required change |
|---|---|
| `scripts/run_pipeline.R` | Register global task mode `pathway` after `similarity`, resolve `project.phase11_pathway_config`, pass no manifest row, and declare output schema `mitochondrial_pathway_data_v1`. |
| `config/local_pilot.yml` | Add `project.phase11_pathway_config` and enable `pathway` after `similarity`. |
| `config/minerva_shared.yml` | Add `project.phase11_pathway_config` and enable `pathway` after `similarity`. |
| `renv.lock` | Change only if implementation introduces a package not already pinned. |
| `.gitignore` | Add an explicit `11_pathway` result exception only if the project intends to track generated tables. Respect MSigDB redistribution terms separately. |

The pipeline must reject `--rds-id` for `pathway`. Phase 11 is one global task
because its scores and queries already combine cell types and RDS partitions.

### Files that remain unchanged

- every Phase 00–10 scientific script and config;
- all Phase 00–10 result bundles;
- normalized RDS files;
- the frozen MitoCarta workbook;
- the known-defective Phase 03 pathway artifacts;
- the Phase 09 Reactome extended-tier reference;
- Yu paper and supplemental files; and
- all previously generated figures.

## Local pilot: Vasculature smoke test

### Input

```text
results/local_pilot/10_similarity/
config/local_pilot.yml
config/local_pilot_execution.yml
config/phase11_pathway.yml
data/reference/Human.MitoCarta3.0.xls
data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt
```

The local task reads the five-cell-type Vasculature similarity bundle. It
tests the complete Phase 11 data-preparation path, but it is not a scientific
54-cell-type result.

### Output

```text
results/local_pilot/11_pathway/
```

### What changes

- one new local Phase 11 bundle is created;
- Phase 10 and reference inputs are read and checksummed but not modified;
- local query sizes use the stored capped Phase 10 tails;
- panel-ready tables are labeled `nonfinal_smoke_test`; and
- no figure is created.

### Preflight

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

test -r config/phase11_pathway.yml
test -r data/reference/Human.MitoCarta3.0.xls
test -r data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt
test -r results/local_pilot/10_similarity/similarity_status.tsv
test -r results/local_pilot/10_similarity/similarity_artifacts.tsv
test -r results/local_pilot/10_similarity/mitochondrial_similarity_results.tsv.gz
test -r results/local_pilot/10_similarity/mitochondrial_similarity_rank_sets.tsv

Rscript -e '
library(data.table)
root <- "results/local_pilot/10_similarity"
status <- fread(file.path(root, "similarity_status.tsv"))
checks <- fread(file.path(root, "similarity_checks.tsv"))
artifacts <- fread(file.path(root, "similarity_artifacts.tsv"))
stopifnot(
  status$schema_version == "mitochondrial_similarity_status_v1",
  status$validation_status == "nonfinal_smoke_test",
  status$comparison_families == 6L,
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete")
)
cat("Local Phase 10 input is ready for the Phase 11 smoke test\n")
'
```

The Phase 11 script performs the authoritative configured checksum and
reference-count checks. A readable but wrong MSigDB release must fail.

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pathway \
  --dry-run
```

Expected graph: exactly one `global:pathway` task using
`scripts/11_prepare_mitochondrial_pathway_data.R` and the Phase 11 config
checksum.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase pathway
```

### Validate

```bash
Rscript -e '
library(data.table)
root <- "results/local_pilot/11_pathway"
status <- fread(file.path(root, "pathway_status.tsv"))
checks <- fread(file.path(root, "pathway_checks.tsv"))
refs <- fread(file.path(root, "pathway_reference_manifest.tsv"))
queries <- fread(file.path(root, "pathway_query_manifest.tsv"))
ora <- fread(file.path(root, "similarity_tail_pathway_ora.tsv.gz"))
similarity_data <- fread(file.path(root, "similarity_panel_data.tsv.gz"))
pathway_data <- fread(file.path(root, "pathway_panel_data.tsv.gz"))
panels <- fread(file.path(root, "downstream_panel_manifest.tsv"))
toys <- fread(file.path(root, "pathway_toy_checks.tsv"))

expected_collections <- c(
  "msigdb_c2_cp_v2026_1",
  "mitocarta_mitopathways_v3_0"
)
stopifnot(
  status$schema_version == "mitochondrial_pathway_status_v1",
  status$validation_status == "nonfinal_smoke_test",
  nrow(queries) == 24L,
  setequal(refs$pathway_collection, expected_collections),
  all(checks$passed[checks$blocking]),
  all(toys$passed),
  !anyDuplicated(queries$query_id),
  !anyDuplicated(ora[, .(query_id, pathway_collection, pathway_id)]),
  all(ora$query_size <= ora$background_size),
  all(ora$overlap_count <= ora$query_size),
  all(ora$overlap_count <= ora$background_pathway_size),
  nrow(similarity_data) > 0L,
  nrow(pathway_data) > 0L,
  all(panels$execution_label == "nonfinal_smoke_test"),
  !any(grepl("[.](pdf|png|svg)$", list.files(root, recursive = TRUE)))
)
cat("Local Phase 11 smoke test validated successfully\n")
'
```

## Minerva production

### Input

```text
results/minerva_production/10_similarity/
config/minerva_shared.yml
config/minerva_production_execution.yml
config/phase11_pathway.yml
data/reference/Human.MitoCarta3.0.xls
data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt
```

Production must not start until the MSigDB file and checksum are frozen and
the complete Phase 10 bundle remains `validated_complete`.

### Output

```text
results/minerva_production/11_pathway/
```

### What changes

- one global Phase 11 production bundle is created;
- 24 frozen 200-tail queries are tested against two pathway collections;
- similarity and pathway panel-ready tables are created;
- focused and inclusive sensitivity tables are created;
- no figure artifact is created; and
- no upstream result or reference is modified.

### Phase 10 production preflight

Run from the Minerva repository root on a compute node:

```bash
cd /sc/arion/work/zhuane01/alzheimer

Rscript -e '
library(data.table)
root <- "results/minerva_production/10_similarity"
status <- fread(file.path(root, "similarity_status.tsv"))
checks <- fread(file.path(root, "similarity_checks.tsv"))
artifacts <- fread(file.path(root, "similarity_artifacts.tsv"))
comparisons <- fread(file.path(root, "similarity_comparison_manifest.tsv"))
rank_sets <- fread(file.path(root, "mitochondrial_similarity_rank_sets.tsv"))

expected <- c(
  "female_vs_male_all_apoe", "e2_vs_e33_all_sexes",
  "e4_vs_e33_all_sexes", "female_vs_male_e2",
  "female_vs_male_e33", "female_vs_male_e4"
)
tails200 <- unique(rank_sets[requested_k == 200L, .(
  comparison_id, analysis_universe, tail, selected_k, size_shortfall
)])

stopifnot(
  status$schema_version == "mitochondrial_similarity_status_v1",
  status$validation_status == "validated_complete",
  status$rds_sets == 9L,
  status$fine_cell_types == 54L,
  status$comparison_families == 6L,
  status$permutations == 10000L,
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete"),
  setequal(comparisons$comparison_id, expected),
  nrow(tails200) == 24L,
  all(tails200$selected_k == 200L),
  all(tails200$size_shortfall == 0L)
)
cat("Minerva Phase 10 input is ready for Phase 11\n")
'
```

### Reference and environment preflight

```bash
test -r data/reference/Human.MitoCarta3.0.xls
test -r data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt

Rscript -e '
stopifnot(
  getRversion() >= "4.3.3",
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("digest", quietly = TRUE),
  requireNamespace("readxl", quietly = TRUE)
)
cat("Phase 11 packages are available\n")
'
```

Do not copy an unverified reference into Minerva after the local run. The local
and production pathway-reference hashes must be identical.

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway \
  --dry-run
```

Expected graph: one `global:pathway` task. Do not set `RDS_ID`, pass
`--rds-id`, or launch one job per RDS.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway
```

### Validate production

```bash
Rscript -e '
library(data.table)
root <- "results/minerva_production/11_pathway"
status <- fread(file.path(root, "pathway_status.tsv"))
checks <- fread(file.path(root, "pathway_checks.tsv"))
artifacts <- fread(file.path(root, "pathway_artifacts.tsv"))
refs <- fread(file.path(root, "pathway_reference_manifest.tsv"))
backgrounds <- fread(file.path(root, "pathway_background_manifest.tsv"))
queries <- fread(file.path(root, "pathway_query_manifest.tsv"))
ora <- fread(file.path(root, "similarity_tail_pathway_ora.tsv.gz"))
similarity_data <- fread(file.path(root, "similarity_panel_data.tsv.gz"))
pathway_data <- fread(file.path(root, "pathway_panel_data.tsv.gz"))
panels <- fread(file.path(root, "downstream_panel_manifest.tsv"))
toys <- fread(file.path(root, "pathway_toy_checks.tsv"))

expected_collections <- c(
  msigdb_c2_cp_v2026_1 = 4115L,
  mitocarta_mitopathways_v3_0 = 149L
)
testable <- ora$test_status == "tested"

stopifnot(
  status$schema_version == "mitochondrial_pathway_status_v1",
  status$validation_status == "validated_complete",
  status$comparison_families == 6L,
  status$query_families == 24L,
  status$ora_rows == 102336L,
  nrow(refs) == 2L,
  all(refs$source_pathways ==
      unname(expected_collections[refs$pathway_collection])),
  nrow(backgrounds) == 12L,
  nrow(queries) == 24L,
  all(queries$selected_k == 200L),
  all(queries$mapped_unique_query_genes <= queries$selected_k),
  nrow(ora) == 102336L,
  !anyDuplicated(ora[, .(query_id, pathway_collection, pathway_id)]),
  all(ora$query_size <= ora$background_size),
  all(ora$overlap_count <= ora$query_size),
  all(ora$overlap_count <= ora$background_pathway_size),
  all(ora$p_value[testable] >= 0 & ora$p_value[testable] <= 1),
  all(ora$tail_fdr_bh[testable] >= 0 & ora$tail_fdr_bh[testable] <= 1),
  all(is.na(ora$p_value[!testable])),
  all(is.na(ora$tail_fdr_bh[!testable])),
  all(checks$passed[checks$blocking]),
  all(artifacts$validation_status == "validated_complete"),
  all(toys$passed),
  all(similarity_data$occurrence_count >= 0),
  all(similarity_data$occurrence_fraction >= 0 &
      similarity_data$occurrence_fraction <= 1),
  nrow(pathway_data) > 0L,
  all(panels$execution_label == "validated_complete"),
  !any(grepl("[.](pdf|png|svg)$", list.files(root, recursive = TRUE)))
)
cat("Minerva Phase 11 production validated successfully\n")
'
```

## Required scientific and provenance checks

### Input and reference checks

- every required Phase 10 input matches its artifact record;
- the Phase 10 status and all blocking checks pass;
- exactly six frozen comparisons and two inherited universes exist;
- C2:CP path, release, symbol namespace, checksum, and 4,115-set count match;
- MitoCarta workbook checksum and sheet match;
- the normalized MitoPathways collection contains 149 pathways, 3,904
  memberships, and 1,035 unique symbols;
- the five blank workbook rows do not become pathways;
- all pathway IDs are unique within collection;
- all within-pathway members are unique and nonempty; and
- no defective Phase 03 pathway file appears in the input manifest.

### Query and background checks

- exactly 12 comparison/universe backgrounds exist;
- exactly 24 comparison/universe/tail queries exist;
- every query comes from a stored Phase 10 `requested_k = 200` rank set;
- rank-set row count equals stored `selected_k` before symbol mapping;
- every mapped query is a subset of its background;
- background genes are unique current HGNC symbols;
- no query gene is dropped merely for having no pathway membership;
- all mapping losses and duplicate collapses are explicit;
- no symbol appears ambiguously in both tails; and
- production tail sizes are 200 unless Phase 10 itself records a documented
  shortfall.

### ORA numerical checks

- all contingency cells are nonnegative integers;
- `k <= n`, `k <= M`, `n <= N`, and `M < N` for tested rows;
- contingency cells sum exactly to `N`;
- stored P values reproduce the frozen `phyper` expression;
- zero-overlap pathways have P value 1;
- gene ratio, background ratio, fold enrichment, and hit rate reproduce their
  stored counts;
- overlap genes equal the set intersection of query and pathway membership;
- an audited subset matches one-sided Fisher exact tests; and
- every toy case passes.

### Coverage and testability checks

- source and background pathway sizes reconcile to membership tables;
- C2:CP and MitoPathways apply their configured eligibility rules exactly;
- 5–9-member tested sets carry the lower-confidence label;
- not-testable rows have explicit reasons and no inferential values;
- reference coverage is present for every pathway/query row; and
- pathway absence is never represented as a significant negative result.

### FDR checks

- BH is recalculated independently for every query and collection;
- stored family size equals the number of eligible pathway rows;
- ineligible rows never enter a family;
- primary downstream significance uses `tail_fdr_bh < 0.05`;
- global FDR is calculated only in the frozen universe/collection family; and
- panel-profile flags never switch between local and global FDR after
  inspection.

### Downstream-data checks

- Figure 3–5 panel-A data has 25 high and 25 low features per universe;
- each Figure 6 panel-A dataset has 10 high and 10 low features;
- every selected feature follows stored Phase 10 `selection_order`;
- nine state-pair counts sum to `paired_tests`;
- count cells reconcile to the Phase 10 state-pair table;
- missing states are never converted to zero states;
- occurrence fractions use `paired_tests`, not nominal dimensions;
- required panel-B query flags follow the frozen downstream mapping;
- the Figure 6B profile flags the three low-score 200 tails;
- every query records its primary-significant count, including zero;
- panel-ready tables contain actual `n`, `N`, reference release, FDR scope,
  and coverage fields; and
- no PDF, PNG, SVG, plot object, or assembled figure exists in the Phase 11
  output bundle.

### Provenance checks

Record exact hashes for:

- Phase 11 script and scientific config;
- project, execution, and RDS manifest configs;
- MitoCarta and MSigDB source references;
- every required Phase 10 input; and
- every Phase 11 table.

Also record R and package versions, execution stage, run ID, task ID, start/end
time, host, Git revision, peak memory, and elapsed time. Resume is allowed only
when code, config, input, reference, schema, row/page count, and output hashes
all match.

## Acceptance criteria

### Structural gate

- one global Phase 11 task;
- two frozen, hash-validated pathway collections;
- 12 backgrounds and 24 high/low tail queries;
- unique reference, query, ORA, similarity-panel, pathway-panel, and manifest
  keys;
- a complete atomic artifact bundle; and
- no direct dependency on Phase 08 or Phase 09.

### Scientific gate

- Phase 10 ranks and selections are consumed without recalculation;
- the primary universe is `core_mito` and the inclusive universe is labeled
  sensitivity;
- actual mapped query sizes and comparison-specific eligible backgrounds are
  used;
- ORA counts unique current HGNC symbols;
- C2:CP provides the Yu-comparability analysis;
- MitoPathways is correctly re-parsed from the frozen workbook;
- pathway coverage and testability are explicit;
- one-sided hypergeometric P values and BH families reproduce the frozen
  specification; and
- Figure 6 tail ambiguity is resolved prospectively in favor of `low_score`.

### Downstream-data gate

- panel-ready data exists for all Figure 3–6 analogues;
- similarity data contains the required score-tail features and nine state-pair
  values;
- Figures 3–5 profiles flag high- and low-200-tail ORA;
- the Figure 6 profile flags low-200-tail ORA for e2, e33, and e4;
- panel-ready values join exactly to the complete ORA and Phase 10 records;
- queries with no significant pathways are explicit;
- no non-mitochondrial Phase 10 feature enters a primary query/background; and
- no visual artifact is created by Phase 11.

### Reproducibility gate

- local smoke test passes with nonfinal labeling;
- production uses the same script, scientific config, MitoCarta hash, and
  MSigDB hash;
- rerunning identical inputs reproduces all tabular values and deterministic
  statistical order;
- all artifacts and inputs are checksummed; and
- `pathway_status.tsv` is published only after all blocking checks pass.

## Downstream handoff

The complete Phase 11 bundle supports manuscript interpretation and later
pathway analyses without rereading Phase 08 or recomputing similarity.

Later work should consume:

- `similarity_tail_pathway_ora.tsv.gz` for complete enrichment results;
- `pathway_query_genes.tsv.gz` for exact tail membership and drivers;
- `similarity_panel_data.tsv.gz` for panel A values;
- `pathway_panel_data.tsv.gz` for panel B values;
- `downstream_panel_manifest.tsv` for panel definitions and source keys; and
- `pathway_reference_manifest.tsv` for pathway release and provenance.

Figure generation must follow the separate
[Phase 11 Figures 3–6 generation guide](../figures/phase_11_mitochondrial_figures_3_to_6_guide.md)
and write outside `11_pathway/`.

The later 324-test mitochondrial pathway atlas must be implemented as a
separate phase with its own Phase 08/09 input boundary, continuous ranking
statistic, contrast-specific tested-gene backgrounds, FDR families, and
cell-cluster outputs. It must not append those tests into the Phase 11 ORA
families.

## Completion criteria

Phase 11 is complete when:

- the MSigDB reference is present, frozen, and validated;
- the script reads only validated Phase 10 outputs and declared references;
- MitoPathways are correctly normalized from the source workbook;
- local smoke-test outputs pass with nonfinal status;
- Minerva production creates 24 queries and 102,336 complete ORA rows;
- primary and global FDR values validate;
- all Figure 3–6 panel data reconcile to their source tables;
- every input and output is inventoried and hashed; and
- no upstream file is modified; and
- no figure artifact is created.

## Implementation checklist

### Freeze references and decisions

- [x] Obtain `c2.cp.v2026.1.Hs.symbols.gmt` from official MSigDB.
- [x] Record its SHA-256 and verify 4,115 unique C2:CP pathways.
- [x] Confirm the frozen MitoCarta workbook checksum.
- [x] Confirm 149 nonblank MitoPathways and 3,904 memberships.
- [x] Freeze the Figure 6 low-score-tail decision.
- [x] Freeze pathway eligibility, FDR, and downstream profile rules.

### Implement

- [ ] Add `config/phase11_pathway.yml`.
- [ ] Add `scripts/11_prepare_mitochondrial_pathway_data.R`.
- [ ] Validate Phase 10 status, schemas, keys, checks, and hashes.
- [ ] Parse and normalize both pathway collections.
- [ ] Build 12 backgrounds and 24 query manifests.
- [ ] Implement symbol mapping and ambiguity checks.
- [ ] Implement the complete ORA grid and toy tests.
- [ ] Implement local and global BH correction.
- [ ] Build similarity and pathway panel-ready tables.
- [ ] Build the downstream panel manifest.
- [ ] Write all tables atomically with schemas and hashes.

### Integrate

- [ ] Register global `pathway` after `similarity` in `scripts/run_pipeline.R`.
- [ ] Add the Phase 11 config path and task mode to local and Minerva configs.
- [ ] Reject per-RDS execution for the global task.
- [ ] Update `renv.lock` only if a new dependency is required.
- [ ] Update ignore/tracking policy without redistributing restricted
  reference data.
- [ ] Keep all Phase 00–10 code and results unchanged.

### Validate

- [ ] Run the local dry run and Vasculature smoke test.
- [ ] Review reference normalization and symbol-mapping reports.
- [ ] Verify local capped tail sizes are used as actual `n`.
- [ ] Cross-check audited ORA rows with one-sided Fisher tests.
- [ ] Confirm all FDR families and statistical ordering reproduce exactly.
- [ ] Confirm local panel-ready tables carry nonfinal labels.
- [ ] Confirm no figure artifact exists under local `11_pathway/`.
- [ ] Promote identical code, config, and reference hashes to Minerva.
- [ ] Run the single production Phase 11 task.
- [ ] Validate 102,336 ORA rows and all downstream panel-ready tables.
- [ ] Review focused MitoPathways and inclusive sensitivity outputs without
  replacing the primary prespecified data profile.
