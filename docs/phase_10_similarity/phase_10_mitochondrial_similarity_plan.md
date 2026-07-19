# Phase 10: Yu-Style Mitochondrial Similarity Scores

## Status and phase boundary

This document defines the new Phase 10. It follows the completed Phase 09
mitochondrial-gene annotation phase and replaces the scientific role of the
archived Phase 10 implementation without reusing its inputs or outputs.

The new phase is a data-production phase:

- read the validated, combined Phase 09 annotation bundle;
- select the mitochondrial gene tiers defined in Phase 09;
- convert the six Yu-compatible AD-versus-NCI DEG results to ternary states;
- calculate Yu-style similarity scores for the comparisons underlying Yu
  Figures 3, 4, 5, and 6;
- estimate permutation p-values and explicitly scoped FDR values;
- write complete state-pair, score, ranking, and quality-control tables for a
  later figure phase.

Phase 10 does **not** draw a figure, run pathway enrichment, refit MAST,
recalculate Phase 08 DEG calls, or change Phase 09 annotations.

The new output directory is:

```text
results/<environment>/10_similarity/
```

Do not reuse the archived `10_downstream/` directory. Archived Phase 09–15
scripts and results are historical references only and are explicit
non-inputs.

## High-level purpose

Yu et al. compared the direction of AD-associated expression changes between
sex or APOE strata. Each AD-versus-NCI result was represented as significant
up, not significant, or significant down. A gene received a high score when
its directional states agreed across paired strata and a low score when they
were opposite.

Phase 10 will reproduce that score structure for mitochondrial-related genes
identified in Phase 09. It will create the numerical inputs needed for later
figures analogous to:

- Yu Figure 3: Female-versus-Male similarity across all APOE groups;
- Yu Figure 4: APOE-e2-versus-e33 similarity across both sexes;
- Yu Figure 5: APOE-e4-versus-e33 similarity across both sexes;
- Yu Figure 6: Female-versus-Male similarity separately within e2, e33, and
  e4.

The later figure phase will decide visual design. Phase 10 only freezes and
validates the underlying numbers, ranks, selected tails, and heatmap-ready
states.

The companion explanation
[similarity_calculation_cross_celltypes_explained.md](similarity_calculation_cross_celltypes_explained.md)
is the authoritative description of how cell clusters enter Figures 3–6.
The central rule is that Phase 10 calculates **one cross-cell-type score per
gene and comparison** after concatenating matched DEG states across cell
clusters. It must not calculate one score per cell cluster and average those
scores, pool raw expression across clusters, or average fold changes across
clusters.

## Relationship to Yu and deliberate differences

### What remains the same

- The input to a similarity comparison is the direction of an AD-minus-NCI
  DEG result, not the magnitude of log fold change.
- The ternary states are `+1`, `0`, and `-1`.
- Concordant significant directions contribute `+1`.
- A significant state paired with a nonsignificant state contributes `-0.5`.
- Opposite significant directions contribute `-1`.
- A pair of nonsignificant states contributes `0`.
- Matched ternary states are concatenated across all cell clusters before the
  score is calculated.
- Scores are ranked from the most concordant to the most divergent.
- Permutation inference breaks the alignment of paired strata while
  preserving each gene's marginal state distribution.

### What changes

| Item | Yu analysis | New Phase 10 |
|---|---|---|
| Gene universe | Transcriptome-wide tested genes | Phase 09 mitochondrial tiers only |
| DEG source | Yu paper's analysis | Phase 08 Yu-compatible MAST states carried through Phase 09 |
| Gene identity | Published symbol | Exact Phase 09 assay feature, with stable HGNC/Ensembl annotations retained |
| Missing tests | Paper reports fixed nominal comparison counts | Filtered, unmeasured, and non-estimable tests remain missing and are excluded from the score denominator |
| Denominator | Fixed nominal `N` in the paper design | Observed paired-state count per gene, with an explicit coverage threshold for ranking |
| FDR family | Published transcriptome-wide family | Prespecified mitochondrial family within each comparison and analysis universe |
| Empirical p-value | Supplemental Table S2 includes zero values | Plus-one estimate; zero p-values are impossible |
| Products | Scores, plots, and enrichment in the paper | Validated data tables only; no plots and no enrichment |

These differences mean that the score formula is Yu-compatible, but the new
scores, p-values, FDR values, and top/bottom genes are not expected to equal
Yu Supplemental Table S2. The mitochondrial restriction and honest missing
state policy are scientific design changes, not implementation discrepancies.

## Frozen scientific definition

### Analysis unit and mitochondrial universes

The primary score unit is the exact Phase 09 assay feature:

```text
similarity_feature_id = feature_id_original
```

Phase 10 must not silently collapse two assay features that map to the same
HGNC symbol or stable Ensembl ID. It must verify that a repeated
`feature_id_original` has consistent HGNC, Ensembl, and mitochondrial-tier
annotations across RDS objects. An inconsistency is reported and makes the
feature ineligible until resolved.

Reference-only Phase 09 genes remain in the feature and eligibility outputs,
but cannot receive a similarity score because they have no measured DEG
state. Their status is `reference_only_not_scoreable`.

In this plan, `analysis_universe` is a named, prespecified set of Phase 09
features that are analyzed together for multiple-testing correction and
ranking. It does not mean all genes measured in the assay, and it is not the
set of cell types or strata used to calculate a feature's similarity score.
For a given `comparison_id`, the ranking-eligible features assigned to the
same `analysis_universe` form one BH FDR family and one ranking pool.

Two `analysis_universe` values are produced from the frozen Phase 09 tiers:

| Universe | Included Phase 09 tiers | Use |
|---|---|---|
| `core_mito` | `core_mito_protein` | Primary mitochondrial analysis |
| `all_mito_related` | `core_mito_protein`, `mtdna_noncoding`, and `mito_extended` | Inclusive secondary analysis |

`non_mito` is excluded. In the current local Phase 09 output, the conventional
mtDNA noncoding genes are reference-only; they will be retained in coverage
tables but will not be forced into a score.

The score itself is calculated once per feature and comparison. Universe
membership changes the FDR family and the ranks, not the score or its
permutation p-values. Because `core_mito` is a subset of
`all_mito_related`, an eligible core feature participates in both universes:
it has the same observed score and empirical p-values in each, but may have
different BH-adjusted FDR values and ranks because the two universes contain
different numbers and sets of features. Reference-only or otherwise
ineligible features remain visible in manifests and coverage summaries but do
not enter an FDR family or ranking pool.

### Ternary DEG states

Use the Phase 09 `deg_state` field exactly as written:

| Phase 09 `deg_state` / `tested_status` | Phase 10 state |
|---|---:|
| `significant_up` | `+1` |
| `tested_not_significant` | `0` |
| `significant_down` | `-1` |
| `present_but_filtered_min_pct` | Missing; excluded |
| `not_in_expression_matrix` | Missing; excluded |
| `contrast_not_estimable` | Missing; excluded |

Phase 10 must not reconstruct a DEG from `logFC`, raw p-value, or FDR. It must
not treat filtered, absent, reference-only, or non-estimable records as zero.
The continuous Phase 08 fields are carried into the state-pair output for
audit and later heatmap labeling only; they do not contribute to the score.

### Cross-cell-type aggregation rule

Each comparison pairs two vectors of ternary AD-versus-NCI states. A
dimension is identified by `rds_id` plus fine cell type and, when applicable,
sex or APOE group. Including `rds_id` prevents accidental collision of cell
type labels across source objects.

The Phase 08 MAST contrasts have already been run separately within each fine
cell cluster. Phase 10 combines only their ternary results. For each feature:

1. create the ordered first-stratum vector over all matched cell-cluster
   positions;
2. create the corresponding second-stratum vector in the identical position
   order;
3. compare states position by position;
4. pool the nine state-pair counts over the entire vector;
5. calculate the score once from those pooled counts.

The deterministic production position counts are:

| Yu analogue | Concatenated positions | Nominal `N` |
|---|---|---:|
| Figure 3 | 54 cell clusters × 3 APOE groups | 162 |
| Figure 4 | 54 cell clusters × 2 sexes | 108 |
| Figure 5 | 54 cell clusters × 2 sexes | 108 |
| Figure 6, e2 | 54 cell clusters | 54 |
| Figure 6, e33 | 54 cell clusters | 54 |
| Figure 6, e4 | 54 cell clusters | 54 |

For example, Figure 3 contains the Female-versus-Male state pair for every
`cell cluster × APOE group` position in one 162-position vector. Figure 4
contains the e2-versus-e33 pair for every `cell cluster × sex` position in one
108-position vector. The RDS objects are storage partitions containing the 54
fine cell clusters; they are not separate replicates and must not receive
separate scores that are combined afterward.

Every one of the 54 production clusters must occur in the dimension manifest,
even if an underlying contrast or gene state is unavailable. Thus, "all 54
clusters are used" means all nominal positions are constructed and audited.
Unavailable Phase 09 states remain explicit missing positions; they are not
silently converted to zero.

### Six Figure 3–6 comparison families

In this plan, `comparison_id` is the stable identifier for one prespecified
biological similarity question. It fixes which two subgroup-specific
AD-versus-NCI ternary state vectors are paired, which cell-type/stratum
positions form those vectors, and which Yu figure the comparison parallels.
It is not an individual gene, cell type, or Phase 08 AD-versus-NCI contrast.
For each `comparison_id`, every eligible gene receives one pooled
cross-cell-type similarity score and one set of permutation p-values. For
example, `female_vs_male_all_apoe` compares the female and male AD-versus-NCI
states at every `cell type x APOE group` position in one 162-position vector
per gene.

| `comparison_id` | Yu analogue | First state | Second state | Dimension key |
|---|---|---|---|---|
| `female_vs_male_all_apoe` | Figure 3 | Female | Male | `rds_id + cell_type + apoe_group` |
| `e2_vs_e33_all_sexes` | Figure 4 | e2 | e33 | `rds_id + cell_type + sex` |
| `e4_vs_e33_all_sexes` | Figure 5 | e4 | e33 | `rds_id + cell_type + sex` |
| `female_vs_male_e2` | Figure 6, e2 | Female e2 | Male e2 | `rds_id + cell_type` |
| `female_vs_male_e33` | Figure 6, e33 | Female e33 | Male e33 | `rds_id + cell_type` |
| `female_vs_male_e4` | Figure 6, e4 | Female e4 | Male e4 | `rds_id + cell_type` |

For every state, positive means higher expression in AD than NCI. The words
`first` and `second` only make the state-pair table deterministic; the
similarity score is symmetric.

With all 54 production fine cell types and all strata available, the nominal
maximum dimension counts are 162, 108, 108, 54, 54, and 54, respectively.
These are hard production design checks for the **planned dimension
manifest**, because Phase 09 contains all 324 planned contrasts. They are not
automatically the observed score denominator when Phase 09 reports a filtered,
unmeasured, or non-estimable state.

The four additional sex-specific APOE comparisons found in the archived
Phase 10 script are outside Figures 3–6 and are not part of this phase.

### Structural availability and score coverage

For each comparison:

- `nominal_dimensions` is 162, 108, 108, 54, 54, or 54 according to the
  comparison definition;
- `planned_dimensions` is the number of dimension pairs instantiated from the
  Phase 09 contrast design and must equal `nominal_dimensions` in production;
- `structurally_estimable_dimensions` is the number for which both underlying
  Phase 08 contrasts completed;
- `paired_tests` is the gene-specific number for which both ternary states
  are nonmissing;
- `missing_first`, `missing_second`, and `missing_both` preserve the reason a
  dimension was excluded;
- `coverage_fraction = paired_tests / structurally_estimable_dimensions`.

Also record:

```text
nominal_coverage_fraction = paired_tests / nominal_dimensions
complete_nominal_vector = paired_tests == nominal_dimensions
score_scope = complete_yu_vector | coverage_adjusted_cross_celltype | not_scoreable
```

`complete_yu_vector` means the score used every nominal position described in
the companion explanation. `coverage_adjusted_cross_celltype` still combines
states globally across all available cell-cluster positions, but it is not an
exact fixed-`N` reproduction and must be labeled as such in score and rank-set
outputs.

A score is numerically estimable when `paired_tests >= 1`, but a feature is
eligible for permutation inference, FDR, ranks, and top/bottom sets only when:

```text
required_paired_tests = max(3, ceiling(0.50 * structurally_estimable_dimensions))
paired_tests >= required_paired_tests
```

This default prevents a feature with one paired observation from receiving an
apparently extreme `+1` or `-1` rank. The threshold is frozen in
`config/phase10_similarity.yml`, written to every relevant output, and cannot
be changed after examining the Phase 10 rankings without declaring a new
sensitivity analysis.

If fewer than three dimensions are structurally estimable, scores may be
reported descriptively but no feature in that comparison is ranking-eligible.

### Similarity score

Let `S(a,b)` be the number of paired dimensions with first state `a` and
second state `b`, where `a,b` are in `{-1,0,+1}`. Let `N` be
`paired_tests`, including `(0,0)` pairs. Calculate:

```text
score = [
    S(+1,+1) + S(-1,-1)
  - 0.5 * {S(+1,0) + S(-1,0) + S(0,+1) + S(0,-1)}
  - {S(+1,-1) + S(-1,+1)}
] / N
```

The `(0,0)` count is included in `N` but contributes zero to the numerator.
The `S(a,b)` counts are pooled over the complete cross-cell-type vector before
this single division. Phase 10 must not calculate a score within each cell
cluster and then average or weight those cell-cluster scores.
Store all nine `S(a,b)` cells as well as:

- `same_direction_significant`;
- `one_sided_significant`;
- `opposite_direction_significant`;
- `both_not_significant`;
- `score_numerator`;
- `similarity_score`.

The score must be in `[-1,1]`. A high value means similar AD-associated
directional responses in the paired strata. A low value means different or
opposite responses. It is not a correlation and it does not encode effect-size
magnitude.

### Required hand-calculated tests

The implementation must write and validate at least these toy cases:

| First states | Second states | Expected score |
|---|---|---:|
| `+1,-1` | `+1,-1` | `+1.0` |
| `+1,-1` | `0,0` | `-0.5` |
| `+1,-1` | `-1,+1` | `-1.0` |
| `0,0` | `0,0` | `0.0` |

Missing values must be excluded before `N` is calculated, and a vector with
no paired states must return `score_status = not_scoreable`, not zero.

### Permutation inference

For each ranking-eligible feature and comparison:

1. retain the ordered, pooled cross-cell-type first-state vector over paired
   dimension IDs;
2. randomly permute the second-state vector over those same pooled dimension
   IDs;
3. recalculate the score;
4. repeat the procedure `B` times;
5. preserve `N` and both marginal state distributions in every permutation.

Use deterministic seeds derived from a frozen base seed, comparison ID,
feature ID, and execution profile. Identical inputs and configuration must
produce identical p-values on local and Minerva R installations.

Configuration defaults are:

| Execution | Permutations | Scientific status |
|---|---:|---|
| Local pilot | 100 | `nonfinal_smoke_test` |
| Minerva production | 10,000 | `validated_complete` when all gates pass |

The existing `pilot_limits.similarity_permutations: 100` is retained as the
local-only override. The production count and seed live in the dedicated
Phase 10 config.

Calculate plus-one empirical tails:

```text
p_high = (1 + count(null_score >= observed_score)) / (B + 1)
p_low  = (1 + count(null_score <= observed_score)) / (B + 1)
```

For a positive observed score, the directional p-value is `p_high`; for a
negative score it is `p_low`; for a zero score it is `1`. Also store the two
tail p-values and `min(1, 2 * min(p_high, p_low))` as a descriptive two-sided
p-value.

#### Inferential outputs and interpretation

Permutation inference does not replace or modify the observed similarity
score. The score reports the direction and degree of concordance: high scores
indicate unusually concordant AD-associated states, while low scores indicate
unusually divergent or opposite states. The permutation null distribution
provides the statistical evidence for deciding whether that observed score is
more extreme than expected by chance.

For every ranking-eligible feature and comparison, report:

- the observed `similarity_score`;
- `p_high`, measuring evidence for unusually high concordance;
- `p_low`, measuring evidence for unusually strong divergence;
- the sign-selected `directional_p`;
- the descriptive two-sided empirical p-value; and
- the BH-adjusted directional FDR within each applicable
  `comparison_id x analysis_universe` family.

The inferential result is therefore an FDR value for each eligible gene within
each specified similarity comparison and mitochondrial analysis universe, not
one FDR for the entire Phase 10 analysis. The score supplies the effect
direction and magnitude on the Zhang-Yu scale; the directional FDR supplies
the strength of statistical evidence. A low-score gene must not be described
as significantly divergent, and a high-score gene must not be described as
significantly concordant, unless its directional FDR passes the prespecified
threshold.

The plus-one rule is intentional. Yu Supplemental Table S2 contains empirical
p-values of zero, which cannot occur under this estimator. Phase 10 prioritizes
an explicit, reproducible finite-simulation estimator over reproducing that
undocumented edge behavior.

Apply Benjamini-Hochberg correction independently within each:

```text
comparison_id x analysis_universe
```

Only ranking-eligible features enter an FDR family. Report the family size.
There are six primary `core_mito` families and six inclusive
`all_mito_related` families. Do not describe these FDR values as
transcriptome-wide or as Yu's published FDR.

### Ranking and figure-ready selections

Within each `comparison_id x analysis_universe`, rank only eligible features.
Produce both:

- high-score rank: decreasing `similarity_score`;
- low-score rank: increasing `similarity_score`.

Use deterministic ordering for ties:

1. score;
2. greater `paired_tests`;
3. lexical `similarity_feature_id`.

Also store a tie-group rank based only on the score so later figures can show
that two deterministically ordered genes were statistically tied.

Create rank-set records for:

- top and bottom 25 for Figure 3 analogues;
- top and bottom 25 for Figure 4 analogues;
- top and bottom 25 for Figure 5 analogues;
- top and bottom 10 for each Figure 6 APOE panel;
- top and bottom 200 for later enrichment or supplementary analyses.

Phase 10 creates gene lists only. It does not run enrichment. Yu Figure 6's
caption/text is not fully consistent about the enrichment tail, so Phase 10
will preserve both high-score and low-score 200-gene sets and defer the visual
or enrichment choice to the later phase.

When an eligible universe is too small for two disjoint tails of the requested
size, set:

```text
selected_k = min(requested_k, floor(eligible_genes / 2))
```

Record the shortfall and keep top and bottom selections disjoint. Use
`high_score` and `low_score` as stored labels; do not claim that a low-score
tail is significantly divergent unless its directional FDR supports that
claim.

## Inputs and dependencies

### Required Phase 09 inputs

Phase 10 consumes only the validated combined Phase 09 bundle under:

```text
results/<environment>/09_annotate_genes/
```

| Input | Requirement and role |
|---|---|
| `annotation_status.tsv` | Schema `mitochondrial_annotation_status_v1`; must be `validated_complete` for production. |
| `annotation_artifacts.tsv` | Every declared Phase 09 artifact must exist and match its bytes, row count, checksum, and validation status. |
| `annotation_checks.tsv` | Every blocking Phase 09 check must pass. |
| `gene_annotation_master.tsv.gz` | Defines exact assay features, reference-only genes, stable identifiers, and mitochondrial tiers. |
| `deg_all_annotated.tsv.gz` | Supplies all six AD-versus-NCI ternary states and explicit unavailable-state reasons. |
| `mitochondrial_reference_inventory.tsv` | Reconciles the complete core, mtDNA, and extended mitochondrial inventories when declared by Phase 09. |

Required `deg_all_annotated.tsv.gz` fields include:

- `rds_id`, `contrast_id`, `cell_type_high_resolution`, `sex`, and
  `apoe_group`;
- `analysis_population`, `terminal_status`, and `tested_status`;
- `feature_id_original`, `reference_only_id`, and `reference_only`;
- `symbol_hgnc_current`, `hgnc_id`, and `ensembl_id_stable`;
- `mito_tier`, `genome_origin`, and `mapping_status`;
- `deg_state`, `paper_deg`, and `logFC`.

Phase 10 must validate the Phase 09 unique key before pairing:

```text
rds_id + contrast_id + feature_id_original/reference_only_id
```

### Observed local Phase 09 baseline

The current local input is an already validated baseline, not an expected
Phase 10 result:

| Property | Observed value |
|---|---:|
| Phase 09 annotated rows | 1,006,920 |
| Phase 09 master rows | 33,564 |
| Assay features | 33,538 |
| Reference-only rows | 26 |
| Assay `core_mito_protein` features | 1,194 |
| Assay `mito_extended` features | 80 |

Current local input checksums are:

| File | SHA-256 |
|---|---|
| `annotation_status.tsv` | `facbcce553e8bb238bd22245bee43368ea9cc3d4835cd98f7679f76f0b252b94` |
| `annotation_artifacts.tsv` | `1da652738dba43b180ade4aa3bb85bc7e122bb91e86862e0eecfa82d77a1e8d4` |
| `annotation_checks.tsv` | `81e9b5d371b2211d54473b98a6c0aa1e8d37f23d5010814a2cea8b967003aa21` |
| `gene_annotation_master.tsv.gz` | `2d16fc28d4e316f1d70df412ec902b975091628f214f8d41dc335c1d1450c99c` |
| `deg_all_annotated.tsv.gz` | `3415c8a217a8dfdebf7308a2f4f89b94249e46e13230c958e93e58cca29b876e` |

These hashes document the input used when this plan was written. The Phase 10
script must obtain authoritative hashes from the Phase 09 artifact manifest
and record the actual environment-specific values at run time.

### Local coverage preflight result

Applying the proposed pairing and 50%/minimum-three coverage rule to the
current local Vasculature Phase 09 states gives the following planning
baseline. It is not a frozen acceptance count because implementation checks
may expose input issues that must be corrected upstream.

| Comparison | Structurally estimable dimensions | Features with at least one pair | Required pairs | Currently ranking-eligible |
|---|---:|---:|---:|---:|
| `female_vs_male_all_apoe` | 14 | 621 | 7 | 355 |
| `e2_vs_e33_all_sexes` | 9 | 589 | 5 | 327 |
| `e4_vs_e33_all_sexes` | 10 | 601 | 5 | 377 |
| `female_vs_male_e2` | 4 | 501 | 3 | 237 |
| `female_vs_male_e33` | 5 | 529 | 3 | 356 |
| `female_vs_male_e4` | 5 | 574 | 3 | 370 |

This preflight demonstrates why coverage must accompany every score. It also
shows why requested 200-gene tails may need local capping to remain disjoint.

### Observed validated Minerva production result

The completed Minerva production bundle under
`results/minerva_production/10_similarity/` has
`validation_status = validated_complete`. Its feature manifest contains 1,300
`all_mito_related` features:

| Mitochondrial tier | Manifest features | Scoreable source features |
|---|---:|---:|
| `core_mito_protein` | 1,196 | 1,194 |
| `mito_extended` | 80 | 80 |
| `mtdna_noncoding` | 24 | 0 |
| **Total `all_mito_related`** | **1,300** | **1,274** |

The two non-scoreable core records and all 24 noncoding records are
reference-only features absent from the expression matrices. They remain in
the manifest for completeness but cannot enter a similarity ranking.

Applying the frozen paired-state coverage rule further reduces the
`all_mito_related` ranking universe separately for each comparison:

| Comparison | Ranking-eligible `all_mito_related` features |
|---|---:|
| `female_vs_male_all_apoe` | 766 |
| `e2_vs_e33_all_sexes` | 775 |
| `e4_vs_e33_all_sexes` | 751 |
| `female_vs_male_e2` | 798 |
| `female_vs_male_e33` | 770 |
| `female_vs_male_e4` | 743 |

Thus, the completed Phase 10 analysis contains 1,300 mitochondrial-related
manifest features, not approximately 2,000, and its comparison-specific
ranking pools contain 743–798 features. Downstream pathway enrichment of a
Phase 10 high- or low-score tail must use the corresponding
`comparison_id × analysis_universe` ranking-eligible set as its background,
not all measured transcriptome genes and not a nominal 2,000-gene set.

### Required configuration

Add:

```text
config/phase10_similarity.yml
```

It freezes at minimum:

- the three accepted mitochondrial tiers;
- primary and inclusive analysis universes;
- the six comparison definitions and state ordering;
- the deterministic all-cell-cluster position order and nominal dimension
  counts `162, 108, 108, 54, 54, 54`;
- the Yu score weights `+1`, `-0.5`, `-1`, and `0`;
- minimum three pairs and 50% structural coverage;
- local and production permutation counts;
- deterministic base seed;
- empirical p-value method;
- BH family definition;
- requested top/bottom set sizes;
- expected Phase 09 input and Phase 10 output schemas.

The project configs point to this file through:

```yaml
project:
  phase10_similarity_config: config/phase10_similarity.yml
```

### Explicit non-inputs

Phase 10 must not read:

- a normalized Seurat RDS;
- Phase 07 pseudobulk, contrast, or DEG outputs;
- Phase 08 files directly;
- Yu Supplemental Table S2 as a score or significance oracle;
- the Yu PDF as a run-time input;
- Reactome pathway GMT files directly;
- archived Phase 09–15 scripts or results;
- any pathway-enrichment result;
- any previously generated figure.

Phase 09 is the only scientific data boundary. Its provenance already links
the states back to Phase 08 and the frozen gene references.

The companion cross-cell-type explanation is a method specification and
review aid, not a run-time data input. Its aggregation rule is implemented and
tested through the Phase 10 comparison and dimension manifests.

## Construction workflow

### 1. Validate the Phase 09 bundle

- require a complete Phase 09 status;
- verify all artifact checksums and blocking checks;
- confirm all six Yu strata and every enabled RDS are represented;
- validate unique feature/contrast keys;
- validate allowed `tested_status` and `deg_state` values;
- fail if an assay feature has inconsistent stable identifiers or
  mitochondrial tiers across RDS objects.

### 2. Build the mitochondrial feature manifest

- select the three mitochondrial tiers;
- retain assay and reference-only entities;
- assign `similarity_feature_id` without many-to-one collapsing;
- attach primary/inclusive universe membership;
- preserve HGNC, Ensembl, symbol, genome-origin, and reference metadata;
- report mapping conflicts and score eligibility.

### 3. Build comparison and dimension manifests

- instantiate exactly the six frozen comparison families;
- enumerate every nominal dimension ID from the Phase 09 contrast grid in a
  deterministic cross-cell-type order;
- identify the first and second Phase 09 contrast for each dimension;
- mark structural status from both terminal contrast statuses;
- require production planned counts of `162, 108, 108, 54, 54, 54`;
- record planned, completed, non-estimable, and failed counts.

### 4. Build the complete state-pair table

- cross every mitochondrial feature with every planned comparison dimension;
- attach first and second DEG states without imputing unavailable tests;
- retain state-specific `tested_status`, missing reason, `logFC`, FDR, and DEG
  flag for audit;
- set `paired_for_score = TRUE` only when both ternary states exist.

### 5. Calculate score components and coverage

- pool all nine state-pair counts across the full cross-cell-type vector;
- calculate numerator, denominator, score, and coverage fields;
- assign `complete_yu_vector` or `coverage_adjusted_cross_celltype` scope;
- assign score and ranking eligibility statuses;
- reconcile the score with the state-pair table exactly.

### 6. Run deterministic permutation inference

- permute only eligible feature/comparison state vectors;
- preserve marginal state counts and paired dimension count;
- calculate high, low, directional, and descriptive two-sided p-values;
- store null diagnostics rather than every permutation draw;
- apply BH within each declared comparison/universe family.

### 7. Generate deterministic ranks and rank sets

- rank high and low scores for both universes;
- preserve score-tie groups and deterministic row order;
- generate requested 10-, 25-, and 200-gene tails;
- cap tails when necessary and record all shortfalls;
- never overlap high and low tails within one requested set.

### 8. Validate and atomically publish

- run structural, numerical, inference, ranking, and provenance checks;
- write every table to a temporary path before atomic rename;
- hash and inventory every final artifact;
- publish `similarity_status.tsv` last;
- never accept a partial bundle as resumable.

## Outputs and files created

Create the following under:

```text
results/<environment>/10_similarity/
```

| File | Contents |
|---|---|
| `mitochondrial_similarity_feature_manifest.tsv` | One row per unique mitochondrial assay or reference-only feature, identifiers, tier, universe membership, mapping consistency, and scoreability. |
| `similarity_comparison_manifest.tsv` | Exactly six rows defining figure analogue, first/second strata, cross-cell-type construction, nominal dimensions, thresholds, and expected selection sizes. |
| `similarity_dimension_manifest.tsv` | One row per planned comparison dimension with first/second Phase 09 contrasts and structural status. |
| `mitochondrial_similarity_state_pairs.tsv.gz` | Complete feature-by-comparison-by-dimension state pairs, missing reasons, source statuses, and audit statistics. This is the primary later heatmap input. |
| `mitochondrial_similarity_results.tsv.gz` | One global cross-cell-type row per feature and comparison with all nine pooled state counts, nominal/observed coverage, score scope, score, p-values, FDR values, ranks, eligibility, and gene annotations. |
| `mitochondrial_similarity_rank_sets.tsv` | Figure analogue, universe, high/low tail, requested and selected sizes, feature, score scope, score, rank, FDR, nominal/observed coverage, and deterministic order. |
| `similarity_permutation_diagnostics.tsv.gz` | Feature/comparison null count, seed key, null mean/SD/quantiles, tail exceedance counts, and p-values. |
| `similarity_toy_checks.tsv` | Hand-calculated vectors, observed result, expected result, and pass/fail status. |
| `similarity_qc_summary.tsv` | Counts by comparison, universe, tier, score status, coverage, score sign, FDR, and rank-set membership. |
| `similarity_checks.tsv` | One row per structural, numerical, inference, ranking, or provenance check. |
| `similarity_artifacts.tsv` | Artifact path, schema, bytes, rows, SHA-256, and validation status. |
| `similarity_status.tsv` | One global task summary, exact inputs/config/code hashes, permutation profile, and terminal validation state. |

Use versioned schemas:

```text
mitochondrial_similarity_feature_manifest_v1
similarity_comparison_manifest_v1
similarity_dimension_manifest_v1
mitochondrial_similarity_state_pairs_v1
mitochondrial_similarity_results_v1
mitochondrial_similarity_rank_sets_v1
similarity_permutation_diagnostics_v1
similarity_checks_v1
mitochondrial_similarity_status_v1
```

The output directory must contain no `.pdf`, `.png`, `.svg`, figure panel,
plot object, or enrichment table.

## Files added or changed during implementation

### New files

| File | Required content |
|---|---|
| `config/phase10_similarity.yml` | Frozen comparisons, universes, score weights, coverage rule, permutations, seeds, FDR families, schemas, and rank-set sizes. |
| `scripts/10_calculate_mitochondrial_similarity.R` | Global Phase 10 implementation, validations, deterministic permutations, atomic outputs, and status bundle. |
| `docs/phase_10_similarity/phase_10_mitochondrial_similarity_plan.md` | This implementation and execution plan. |

### Existing files changed

| File | Required change |
|---|---|
| `scripts/run_pipeline.R` | Register global task mode `similarity` after `annotate_genes`, use `config/phase10_similarity.yml`, pass no manifest row, and declare output schema `mitochondrial_similarity_v1`. |
| `config/local_pilot.yml` | Add `project.phase10_similarity_config` and enable `similarity` after `annotate_genes`; retain the existing local 100-permutation override. |
| `config/minerva_shared.yml` | Add `project.phase10_similarity_config` and enable `similarity` after `annotate_genes`. |
| `.gitignore` | If production tabular outputs are intended to be tracked, replace the stale `10_downstream` exception with the explicit `10_similarity` exception; otherwise leave result-ignore policy unchanged. |

The implementation should also add `similarity` to the pipeline's supported
global modes and make `--rds-id` invalid for this task.

### Files that remain unchanged

- all Phase 00–09 scientific scripts;
- `config/analysis_parameters.yml`;
- Phase 08 and Phase 09 scientific configs;
- all Phase 08 and Phase 09 results;
- normalized RDS files;
- frozen HGNC, GENCODE, MitoCarta, and Reactome reference files;
- everything under `archive/`;
- all existing figures.

## Local pilot: Vasculature

### Input

```text
results/local_pilot/09_annotate_genes/
config/local_pilot.yml
config/local_pilot_execution.yml
config/phase10_similarity.yml
```

The local run is one global task over the already combined Vasculature Phase
09 table. `RDS_ID` and `--rds-id` must not be set.

The local Phase 09 object contains five Vasculature fine cell types, so the
local score concatenates those five clusters using the same algorithm. It is a
software smoke test and is not a reproduction of the 54-cluster Figures 3–6.

### Output

```text
results/local_pilot/10_similarity/
```

The local profile uses 100 permutations and must be labeled
`nonfinal_smoke_test`. Its ranks and p-values are suitable for software/QC
validation, not final scientific claims.

### What changes

- a new `10_similarity/` result bundle is created;
- Phase 09 inputs are read and checksummed but not modified;
- no figure or pathway result is created.

### Preflight

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

test -r config/phase10_similarity.yml
test -r results/local_pilot/09_annotate_genes/annotation_status.tsv
test -r results/local_pilot/09_annotate_genes/annotation_artifacts.tsv
test -r results/local_pilot/09_annotate_genes/gene_annotation_master.tsv.gz
test -r results/local_pilot/09_annotate_genes/deg_all_annotated.tsv.gz

Rscript -e '
library(data.table)
root <- "results/local_pilot/09_annotate_genes"
status <- fread(file.path(root, "annotation_status.tsv"))
checks <- fread(file.path(root, "annotation_checks.tsv"))
artifacts <- fread(file.path(root, "annotation_artifacts.tsv"))
stopifnot(
  status$schema_version == "mitochondrial_annotation_status_v1",
  status$validation_status == "validated_complete",
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete")
)
cat("Local Phase 09 input is ready for Phase 10\n")
'
```

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase similarity \
  --dry-run
```

Expected task graph: exactly one `global:similarity` task using
`scripts/10_calculate_mitochondrial_similarity.R` and the Phase 10 config
checksum.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase similarity
```

### Validate

```bash
Rscript -e '
library(data.table)
root <- "results/local_pilot/10_similarity"
status <- fread(file.path(root, "similarity_status.tsv"))
checks <- fread(file.path(root, "similarity_checks.tsv"))
comparisons <- fread(file.path(root, "similarity_comparison_manifest.tsv"))
dimensions <- fread(file.path(root, "similarity_dimension_manifest.tsv"))
results <- fread(file.path(root, "mitochondrial_similarity_results.tsv.gz"))
rank_sets <- fread(file.path(root, "mitochondrial_similarity_rank_sets.tsv"))
toys <- fread(file.path(root, "similarity_toy_checks.tsv"))

expected <- c(
  "female_vs_male_all_apoe", "e2_vs_e33_all_sexes",
  "e4_vs_e33_all_sexes", "female_vs_male_e2",
  "female_vs_male_e33", "female_vs_male_e4"
)

stopifnot(
  status$schema_version == "mitochondrial_similarity_status_v1",
  status$validation_status == "nonfinal_smoke_test",
  status$permutations == 100L,
  setequal(comparisons$comparison_id, expected),
  nrow(comparisons) == 6L,
  all(checks$passed),
  all(toys$passed),
  !anyDuplicated(dimensions[, .(comparison_id, dimension_id)]),
  !anyDuplicated(results[, .(comparison_id, similarity_feature_id)]),
  all(results$similarity_score[results$score_status == "scoreable"] >= -1),
  all(results$similarity_score[results$score_status == "scoreable"] <= 1),
  all(rank_sets$selected_k <= rank_sets$requested_k)
)
cat("Local Phase 10 smoke test validated successfully\n")
'
```

Also require that no figure file exists:

```bash
if find results/local_pilot/10_similarity -type f \
  \( -name '*.pdf' -o -name '*.png' -o -name '*.svg' \) | grep -q .; then
  echo 'Unexpected figure artifact in Phase 10' >&2
  exit 1
fi
```

## Minerva production

### Input

```text
results/minerva_production/09_annotate_genes/
config/minerva_shared.yml
config/minerva_production_execution.yml
config/phase10_similarity.yml
```

Production must not start until the single global Phase 09 production bundle
covers all nine enabled RDS objects, 54 fine cell types, and 324 planned
AD-versus-NCI strata with no failed contrast.

All 54 fine cell types are concatenated into each applicable score vector.
There is one score row per gene and comparison, not one row per gene, cell
type, or RDS object.

### Output

```text
results/minerva_production/10_similarity/
```

### What changes

- one global, cross-RDS Phase 10 bundle is created;
- 10,000 permutations are used for every eligible feature/comparison;
- all upstream production results remain unchanged;
- no figure or enrichment output is produced.

### Phase 09 production preflight

Run on a Minerva compute node from the repository root:

```bash
cd /sc/arion/work/zhuane01/alzheimer

Rscript -e '
library(data.table)
root <- "results/minerva_production/09_annotate_genes"
status <- fread(file.path(root, "annotation_status.tsv"))
checks <- fread(file.path(root, "annotation_checks.tsv"))
artifacts <- fread(file.path(root, "annotation_artifacts.tsv"))
annotated <- fread(file.path(root, "deg_all_annotated.tsv.gz"),
                   select = c("rds_id", "cell_type_high_resolution",
                              "terminal_status"))
stopifnot(
  status$schema_version == "mitochondrial_annotation_status_v1",
  status$validation_status == "validated_complete",
  status$rds_sets == 9L,
  status$fine_cell_types == 54L,
  status$planned_contrasts == 324L,
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete"),
  uniqueN(annotated$rds_id) == 9L,
  uniqueN(annotated[, .(rds_id, cell_type_high_resolution)]) == 54L,
  !any(annotated$terminal_status == "failed")
)
cat("Minerva Phase 09 input is ready for Phase 10\n")
'
```

### Environment preflight

Phase 10 processes tables and does not fit MAST or link MKL. It does not
require `LD_PRELOAD`.

```bash
Rscript -e '
stopifnot(
  getRversion() >= "4.3.3",
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE),
  requireNamespace("digest", quietly = TRUE)
)
cat("Phase 10 packages are available\n")
'
```

### Dry run

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase similarity \
  --dry-run
```

Expected task graph: one `global:similarity` task. Do not set `RDS_ID`, do not
pass `--rds-id`, and do not launch one job per RDS. The score dimensions cross
RDS boundaries, so concurrent per-RDS writers would be scientifically wrong.

### Execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase similarity
```

### Validate production

```bash
Rscript -e '
library(data.table)
root <- "results/minerva_production/10_similarity"
status <- fread(file.path(root, "similarity_status.tsv"))
checks <- fread(file.path(root, "similarity_checks.tsv"))
artifacts <- fread(file.path(root, "similarity_artifacts.tsv"))
comparisons <- fread(file.path(root, "similarity_comparison_manifest.tsv"))
dimensions <- fread(file.path(root, "similarity_dimension_manifest.tsv"))
features <- fread(file.path(root, "mitochondrial_similarity_feature_manifest.tsv"))
pairs <- fread(file.path(root, "mitochondrial_similarity_state_pairs.tsv.gz"))
results <- fread(file.path(root, "mitochondrial_similarity_results.tsv.gz"))
rank_sets <- fread(file.path(root, "mitochondrial_similarity_rank_sets.tsv"))

expected <- c(
  "female_vs_male_all_apoe", "e2_vs_e33_all_sexes",
  "e4_vs_e33_all_sexes", "female_vs_male_e2",
  "female_vs_male_e33", "female_vs_male_e4"
)
expected_n <- setNames(c(162L, 108L, 108L, 54L, 54L, 54L), expected)
observed_n <- dimensions[, .N, by = comparison_id]
valid_states <- c(-1L, 0L, 1L)
scored <- results$score_status == "scoreable"
eligible <- results$ranking_eligible

stopifnot(
  status$schema_version == "mitochondrial_similarity_status_v1",
  status$validation_status == "validated_complete",
  status$permutations == 10000L,
  status$rds_sets == 9L,
  status$fine_cell_types == 54L,
  setequal(comparisons$comparison_id, expected),
  nrow(comparisons) == 6L,
  all(comparisons$nominal_dimensions ==
      unname(expected_n[comparisons$comparison_id])),
  all(observed_n$N == unname(expected_n[observed_n$comparison_id])),
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete"),
  !anyDuplicated(features$similarity_feature_id),
  !anyDuplicated(dimensions[, .(comparison_id, dimension_id)]),
  !anyDuplicated(pairs[, .(
    comparison_id, similarity_feature_id, dimension_id)]),
  !anyDuplicated(results[, .(comparison_id, similarity_feature_id)]),
  all(na.omit(pairs$first_state) %in% valid_states),
  all(na.omit(pairs$second_state) %in% valid_states),
  all(results$similarity_score[scored] >= -1),
  all(results$similarity_score[scored] <= 1),
  all(results$score_scope[scored] %in% c(
    "complete_yu_vector", "coverage_adjusted_cross_celltype")),
  all(results$complete_nominal_vector[scored] ==
      (results$paired_tests[scored] == results$nominal_dimensions[scored])),
  all(results$paired_tests[eligible] >= results$required_paired_tests[eligible]),
  all(results$directional_p[eligible] >= 1 / 10001),
  all(results$directional_p[eligible] <= 1),
  all(rank_sets$selected_k <= rank_sets$requested_k)
)
cat("Minerva Phase 10 production validated successfully\n")
'
```

## Required scientific and provenance checks

### Input and key checks

- Phase 09 status and all declared hashes validate;
- every enabled RDS and fine cell type appears exactly as declared upstream;
- exactly six comparison families exist;
- production planned dimension counts are exactly
  `162, 108, 108, 54, 54, 54` in comparison order;
- every one of the 54 fine cell types occurs in every applicable comparison
  vector;
- every dimension resolves to exactly one first and one second contrast;
- every feature/contrast/dimension state-pair key is unique;
- every `similarity_feature_id` maps consistently across RDS objects;
- no archived or direct Phase 08 path appears in the input manifest.

### State and missingness checks

- all nonmissing states are exactly `-1`, `0`, or `+1`;
- `significant_up`, `tested_not_significant`, and `significant_down` map to
  `+1`, `0`, and `-1` exactly;
- `present_but_filtered_min_pct`, `not_in_expression_matrix`, and
  `contrast_not_estimable` never become zero;
- `paired_for_score` is true if and only if both states are nonmissing;
- missing-state reasons reconcile to the Phase 09 source rows;
- reference-only genes have no score.

### Score checks

- the nine state-cell counts sum to `paired_tests`;
- aggregate same, one-sided, opposite, and `(0,0)` counts reconcile to the
  nine cells;
- the stored numerator and score exactly reproduce the frozen formula;
- each stored score is calculated once from pooled cross-cell-type counts;
- there are no per-cell-type or per-RDS similarity-score rows to average;
- every score is finite and in `[-1,1]`;
- zero paired tests yield `not_scoreable` and `NA`, never zero;
- all toy examples pass.

### Coverage checks

- planned and structurally estimable dimensions reconcile to the dimension
  manifest;
- nominal coverage uses `162`, `108`, or `54` as appropriate;
- `complete_yu_vector` is true if and only if observed and nominal `N` match;
- every incomplete score is labeled `coverage_adjusted_cross_celltype`;
- `coverage_fraction` uses the declared structural denominator;
- rank eligibility is exactly the frozen minimum-three/50% rule;
- every ineligible reason is explicit;
- local and production coverage distributions are written by comparison and
  mitochondrial tier.

### Permutation and FDR checks

- every permutation preserves paired `N` and both marginal state counts;
- the recorded seed key recreates an audited subset exactly;
- local uses 100 draws and is labeled nonfinal;
- production uses 10,000 draws;
- production empirical p-values are never below `1/10001` and never zero;
- BH is recalculated independently for each comparison/universe family;
- the recorded FDR family size equals the number of eligible members;
- no ineligible feature receives an FDR.

### Rank-set checks

- scores are ordered correctly in both directions;
- tie-group and deterministic ranks are both present;
- deterministic tie breaking is stable across reruns;
- top and bottom selections are disjoint;
- selected size is the requested size or the documented capped size;
- every rank-set row joins exactly once to the score and state-pair tables;
- no figure or enrichment artifact is present.

### Provenance checks

Record exact hashes for:

- Phase 10 script and scientific config;
- project, execution, and RDS manifest configs;
- all required Phase 09 inputs;
- every Phase 10 output artifact.

Also record R version, required package versions, execution stage, run ID,
permutation profile, base seed, start/end time, and host. Resume is permitted
only when code, configs, upstream hashes, schemas, row counts, and every
artifact hash match.

## Acceptance criteria

### Structural gate

- one global Phase 10 task;
- exactly six frozen comparison families;
- complete mitochondrial feature and dimension manifests;
- unique state-pair and result keys;
- one explicit score/ranking eligibility status per feature/comparison;
- a complete, hash-validated artifact bundle.

### Scientific gate

- only Phase 09 mitochondrial tiers are scored;
- Phase 09 ternary states are used without DEG recalculation;
- unavailable states remain missing;
- Yu's score weights and pooled-vector formula are reproduced exactly, and
  any non-nominal denominator is explicitly labeled coverage-adjusted;
- all score components and toy cases validate;
- coverage thresholds prevent low-information ranks;
- permutation and BH families are explicitly mitochondrial and reproducible.

### Figure-data gate

- all state pairs needed to reconstruct later Figure 3–6-style heatmaps are
  present;
- each similarity result is one system-level score pooled across all 54
  production cell clusters, never an average of cluster-level scores;
- high/low ranks exist for primary and inclusive universes;
- requested 10-, 25-, and 200-gene tail sets are present or have an explicit
  size shortfall;
- later phases do not need to reread Phase 08 or recompute a score;
- no figure or pathway enrichment is generated in Phase 10.

## Downstream handoff

A later figure phase should consume:

- `mitochondrial_similarity_results.tsv.gz` for scores, coverage, FDR, and
  annotations;
- `mitochondrial_similarity_state_pairs.tsv.gz` for heatmap cells and missing
  state display;
- `mitochondrial_similarity_rank_sets.tsv` for prespecified high/low panels;
- `similarity_comparison_manifest.tsv` for panel labels and ordering.

The figure phase must show or state coverage and must not replace missing
states with nonsignificant zeros. It may filter to `core_mito` for the primary
figure or use `all_mito_related` for an explicitly labeled inclusive figure.
It must not silently recalculate FDR after viewing candidate genes.

If a plotted gene has `score_scope = coverage_adjusted_cross_celltype`, the
later figure must report its observed and nominal `N`. Only
`complete_yu_vector` results may be described as using the complete fixed-`N`
Yu vector.

Any later pathway analysis must independently declare its pathway database,
gene identifier conversion, background universe, and multiple-testing family.
The Phase 09 Reactome files used to define the `mito_extended` tier are not a
pathway-enrichment input to Phase 10.

## Completion criteria

Phase 10 is complete when:

- implementation reads only a validated Phase 09 bundle and frozen Phase 10
  config;
- the local Vasculature smoke test passes with nonfinal status;
- the Minerva production task covers all nine RDS objects and 54 fine cell
  types;
- six score families, their state pairs, coverage, inference, ranks, and
  figure-ready tail sets validate;
- every output and input hash is recorded;
- no upstream result, archived file, figure, or enrichment result is changed
  or created.

## Implementation checklist

### Implement

- [ ] Add `config/phase10_similarity.yml`.
- [ ] Add `scripts/10_calculate_mitochondrial_similarity.R`.
- [ ] Validate Phase 09 status, checks, keys, schemas, and hashes.
- [ ] Build the mitochondrial feature manifest without many-to-one collapse.
- [ ] Build exactly six comparison and dimension manifests.
- [ ] Enforce the single pooled cross-cell-type score and nominal production
  vector sizes described in the companion explanation.
- [ ] Construct the complete state-pair grid with explicit missing reasons.
- [ ] Implement the Yu score and hand-calculated tests.
- [ ] Implement deterministic permutation inference and mitochondrial FDR.
- [ ] Build coverage-aware ranks and disjoint rank sets.
- [ ] Write all outputs atomically with schemas and hashes.

### Integrate

- [ ] Register global `similarity` after `annotate_genes` in
  `scripts/run_pipeline.R`.
- [ ] Add the Phase 10 config path and mode to local and Minerva configs.
- [ ] Confirm `--rds-id` is rejected for this global task.
- [ ] Update `.gitignore` only if the project intends to track the new
  production result directory.
- [ ] Keep all Phase 00–09 and archived files unchanged.

### Validate

- [ ] Run the local dry run and 100-permutation smoke test.
- [ ] Review missing-state and coverage distributions.
- [ ] Confirm the six preflight eligibility counts or explain any audited
  difference.
- [ ] Reproduce an audited permutation subset from stored seeds.
- [ ] Confirm no rank-set overlap and no figure artifacts.
- [ ] Promote identical code and common config hashes to Minerva.
- [ ] Run the single 10,000-permutation production task.
- [ ] Validate the complete production bundle before implementing figures.
