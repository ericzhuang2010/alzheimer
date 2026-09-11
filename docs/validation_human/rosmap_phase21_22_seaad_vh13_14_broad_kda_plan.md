# ROSMAP Phase 21-22 and SEA-AD VH13-VH14 broad-cell KDA plan

**Status:** revised and planned, not executed  
**Plan revised:** 2026-09-10  
**Scope:** separate non-overwriting ROSMAP and SEA-AD broad KDA generation tracks  
**Primary biological replicate:** donor  
**KDA strata:** sex/APOE group within broad cell class  
**ROSMAP contrast eligibility:** at least 3 donors per AD/NCI arm  
**SEA-AD contrast eligibility:** unchanged at 3 donors per Dementia/No-dementia arm

## 1. Objective

Build two independent direct-broad KDA releases. ROSMAP first creates a new,
non-overwriting donor-level broad-cell differential-expression source release
with a 3-donor-per-arm minimum; SEA-AD continues to use its existing broad DEG
release with the unchanged 3-donor minimum. Each cohort then uses one merged
up/down mitochondrial DEG query per contrast, the same KDA algorithm and gates,
and its own broad-cell Bayesian networks.

The KDA result unit is:

```text
driver gene
+ sex/APOE group
+ broad cell class
```

This analysis will not overwrite or redefine VH00-VH12, ROSMAP Phase 08/20, or
the 2026-09-16 presentation. The existing ROSMAP Phase 08 release remains the
five-donor reference release and is read-only. ROSMAP generation writes only
beneath `results/minerva_production/`; SEA-AD generation writes only beneath
`results/validation_human/`. Cross-cohort overlap analysis, figures, summaries,
and slides are outside this plan.

## 2. Why add a broad-cell primary layer

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

The current fine analysis creates a separate disease contrast for each of 129
SEA-AD supertypes and then sends each fine-supertype mitochondrial query into a
broad-cell network. Returned drivers are aggregated back to broad categories
after KDA. With only 78 SEA-AD donors, this produces substantial fine-profile
attrition and many empty mitochondrial queries.

The proposed primary layer aligns all three resolutions:

```text
donor x broad-cell raw-count pseudobulk
    -> broad-cell disease contrast within sex/APOE
    -> deduplicated union of significant up- and downregulated mitochondrial DEGs
    -> matching broad-cell Bayesian network
    -> one KDA result per cohort x group x broad cell
```

Fine-supertype VH12 results remain a secondary localization/sensitivity layer.
They are not pooled with the new broad results.

## 3. Frozen scientific design

### 3.1 Broad-cell taxonomy

Use the seven existing network-aligned classes, with exact machine labels:

1. `Astrocytes`
2. `Excitatory_neurons`
3. `Inhibitory_neurons`
4. `Microglia`
5. `OPCs`
6. `Oligodendrocytes`
7. `Vasculature_cells`

No new crosswalk is required for the primary layer because both cohorts already
have donor-level results at these seven resolutions.

The SEA-AD vasculature network is `encode_only_exploratory`, whereas the other
six SEA-AD networks are full-integrative RIMBANet releases. Preserve that flag
in every vasculature input and result row.

### 3.2 Sex/APOE groups

Preserve the six frozen groups:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

SEA-AD can support the broad disease contrast in all seven broad classes for
`F_e33`, `F_e4`, `M_e33`, and `M_e4`. It cannot support `F_e2` or `M_e2`
because each group has only one Dementia donor in the entire cohort. Those
groups must remain `source_not_estimable`, regardless of nucleus count or
broad-cell aggregation.

### 3.3 Pseudobulk and differential-expression unit

- Sum raw counts within each `donor x broad cell` profile; never aggregate
  normalized expression.
- Require at least 20 nuclei for an eligible donor-broad profile.
- Require at least 3 eligible donors in both disease arms for the new ROSMAP
  source release. This replaces the 5-donor eligibility rule only in the new
  Phase 21 derivative; it does not alter the existing Phase 08 release.
- Preserve the existing SEA-AD threshold of at least 3 eligible donors in both
  disease arms.
- Refit the seven ROSMAP donor-level broad edgeR quasi-likelihood models from
  the frozen Phase 08 broad pseudobulk count bundles and test the complete
  42-contrast family. Do not splice two new tests into the old 40-contrast
  release and do not use nucleus-level MAST.
- Use the existing SEA-AD donor-level broad edgeR quasi-likelihood fits rather
  than rerunning SEA-AD DEG.
- Preserve the cohort-appropriate disease labels and covariates. ROSMAP uses
  `AD - NCI`; SEA-AD uses `Dementia - No dementia` and retains its study term.
- Preserve these native phenotype definitions in every manifest.

At the 3-donor threshold, the expected independent source universes are 42
completed broad contrasts for ROSMAP and 28 completed broad contrasts for
SEA-AD. The two newly eligible ROSMAP contrasts are:

```text
Vasculature_cells x F_e2: AD=3, NCI=10 donors
Vasculature_cells x M_e2: AD=4, NCI=3 donors
```

Both must be labeled `exploratory_min3_support`; neither satisfies the frozen
10-donor-per-arm confirmatory-support threshold. The other 40 ROSMAP contrasts
retain their recorded donor counts and support labels. KDA is never called for
a source contrast that its applicable upstream release marked non-estimable.

### 3.4 Primary merged mitochondrial query rule

Apply the same rule independently to the full broad DEG result tables from each
cohort:

1. gene belongs to the frozen core mitochondrial protein set;
2. within-contrast BH FDR is strictly below `0.05`;
3. no fold-change cutoff in the primary harmonized query;
4. take the deduplicated union of genes with positive and negative disease
   coefficients and label the single query `AD_both_mito`;
5. retain `in_upregulated_query` and `in_downregulated_query` as gene-level
   provenance fields, but never create direction-specific KDA calls;
6. intersect with the corresponding cohort-specific network and exact tested
   gene background; and
7. require at least 3 effective mapped query genes for KDA.

For SEA-AD, positive and negative `Dementia - No dementia` coefficients are
merged into the same `AD_both_mito` query. For ROSMAP, positive and negative
`AD - NCI` coefficients are merged in the same way. Preserve the native
coefficient and phenotype labels and each query member's source sign.

ROSMAP Phase 21 and SEA-AD VH13 must independently freeze and validate their
cohort-specific core-mito identities. Any within-cohort symbol conflict is
written to an exception table and blocks the affected gene; it is never
resolved silently.

### 3.5 KDA configuration

Use the validated `scripts/NetWeaver/fKDA.R` implementation and freeze its hash.
Match the current VH12 settings:

```text
nLayerToTest: 3
nLayersToExpand: 0
directed: true
reduce_within_nlayer: 2
within-call p correction: BH
within-call driver FDR: 0.05
return_overlap: true
```

Each broad category produces at most one KDA call. There is no separate up or
down call and no post-KDA combination of directional results. Do not
ACAT-combine post-selected q values across fine supertypes in the primary broad
analysis. Top-five ranking is a display rule only and never a selection or
validation rule.

## 4. Local data-sufficiency audit

### 4.1 Conclusion

The repository on this machine contains enough data and final network releases
to execute the planned workflow without downloading external data and without
rereading the original large single-nucleus objects.

The frozen ROSMAP Phase 08 donor-by-broad-cell raw-count pseudobulk bundles are
present for all seven broad classes. They are sufficient to refit the same
edgeR models, rebuild the contrast manifest with a 3-donor minimum, and test all
42 structural contrasts in a new Phase 21 source subrelease. The existing
five-donor Phase 08 DEG release remains a read-only comparison authority.

It contains enough biological replication for 28 of 42 SEA-AD broad contrasts:
all seven broad classes in `F_e33`, `F_e4`, `M_e33`, and `M_e4`. It does not
contain enough independent SEA-AD donors for disease inference in `F_e2` or
`M_e2`. This is a cohort limitation, not a missing-file limitation.

### 4.2 Reusable local inputs

| Required input | Local authority | Audit result |
|---|---|---|
| ROSMAP frozen broad pseudobulk counts | `results/minerva_production/08_deg_broad/02_broad_pseudobulk/` | Present for all seven broad classes; this is the count authority for the new minimum-3 Phase 21 DEG subrelease |
| ROSMAP Phase 08 broad edgeR reference | `results/minerva_production/08_deg_broad/broad_deg_results.tsv.gz`, `05_by_contrast/`, and `broad_deg_contrast_status.tsv` | Present and validated with 40/42 completed contrasts; read-only regression reference, not the scientific source for the new ROSMAP KDA |
| SEA-AD direct broad raw-count pseudobulks | `results/validation_human/05_pseudobulk/direct_broad_counts/` | Present for all seven broad classes; direct and fine-rollup counts previously reconciled exactly |
| SEA-AD broad donor-level edgeR results | `results/validation_human/08_deg/broad_stratified_support/` | Present; all 28 eligible contrasts completed and compressed result files pass gzip checks |
| ROSMAP gene/mitochondrial annotations | `results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz` plus annotations embedded in the broad result | Present and gzip-valid |
| SEA-AD gene/mitochondrial annotations | `results/validation_human/03_genes/gene_annotation_master.tsv` | Present |
| ROSMAP broad Bayesian networks | `data/bayesian_network/<broad>/result.links3.links.txt` | Present for all seven required broad classes |
| SEA-AD broad Bayesian networks | `data/bayesian_network_seaad/<broad>/result.links3.links.txt` | Present for all seven classes with release manifest and hashes |
| KDA implementation | `scripts/NetWeaver/fKDA.R` | Present; same validated implementation used by prior phases |
| Prior KDA preparation/execution logic | `scripts/validation_human/10_prepare_seaad_kda_inputs.py`, `10_run_seaad_kda.R`, and Phase 18 selection code | Present; reusable as implementation patterns, not as result evidence |

Observed local sizes are modest for the proposed rerun: approximately 143 MB
for the seven frozen ROSMAP broad pseudobulk bundles, 598 MB for the Phase 08
ROSMAP broad DEG reference release, 21 MB for SEA-AD direct broad counts, 30 MB
for SEA-AD broad DEG results, 1.2 MB for the existing ROSMAP network directory,
and 12 MB for the SEA-AD network release. The proposed KDA universe is at most
42 merged-query slots per cohort before query and network-mapping attrition.

### 4.3 Files not required

The following are not required to execute the new broad KDA validation because
validated downstream authorities are already local:

- original large ROSMAP RDS files;
- original SEA-AD H5AD expression objects;
- SEA-AD genotype/eQTL controlled inputs;
- RIMBANet per-search scratch outputs; and
- prior VH10-VH12 KDA returns as scientific evidence.

VH10-VH12 outputs may be read only for schema and reconstruction checks.

## 5. Non-overwriting phase layout

All new scripts and configs must use explicit output roots and fail if their
target contains an incompatible completed run. ROSMAP generation and SEA-AD
generation are separate tracks with separate manifests, status files, and
artifact registries. No phase reads the other cohort's KDA release.

```text
results/minerva_production/
  21_harmonized_broad_kda_inputs/
    00_source_deg_min3/
  22_harmonized_broad_kda_combo/

results/validation_human/
  13_harmonized_broad_kda_inputs/
  14_harmonized_broad_kda_combo/

docs/validation_human/
  rosmap_phase21_22_seaad_vh13_14_broad_kda_plan.md
```

No new script may write beneath existing ROSMAP Phase 00-20 or SEA-AD VH00-VH12
directories.

## 6. ROSMAP production phases

### Phase 21: ROSMAP minimum-3 broad DEG and query input freeze

**Output:** `results/minerva_production/21_harmonized_broad_kda_inputs/`

Phase 21 has two dependency-ordered stages. First, it creates a complete
minimum-3 ROSMAP broad DEG subrelease beneath `00_source_deg_min3/` by refitting
the seven broad edgeR models from the frozen Phase 08 broad pseudobulk count
bundles. Second, it freezes the merged KDA queries from that new source. It does
not rebuild pseudobulk, modify Phase 08, splice new rows into Phase 08, or use
the fine-MAST Phase 20 KDA returns as broad KDA evidence.

Tasks:

1. Freeze SHA-256 identities for the seven Phase 08 broad pseudobulk count
   bundles and their validation status, ROSMAP annotation, the read-only Phase
   08 DEG reference, seven ROSMAP broad networks, fKDA source, configuration,
   and all new scripts.
2. Create a dedicated Phase 21 ROSMAP DEG configuration derived from the Phase
   08 production configuration. Change only the run/output identities and
   `minimum_donors_per_arm` from 5 to 3; preserve the 20-nucleus donor-profile
   minimum, 10-donor confirmatory threshold, model formula, covariates,
   `filterByExpr`, TMM normalization, robust edgeR QL fitting, coefficient
   direction, tested-gene universe, and within-contrast BH correction.
3. Rebuild the 42-row ROSMAP contrast manifest from the frozen pseudobulk
   metadata using the 3-donor rule, then refit all seven broad-cell models and
   test all 42 contrasts. Publish a complete derivative DEG release; do not
   combine 40 Phase 08 files with two new files.
4. Validate that all 42 contrasts completed and that the newly admitted
   vasculature `F_e2` and `M_e2` rows have the expected 3/10 and 4/3 AD/NCI
   donor counts, respectively.
5. Regression-check the 40 contrasts shared with Phase 08: require identical
   gene keys, coefficient directions, tested-gene membership, and numerical
   results within a frozen machine-precision tolerance. Any unexplained change
   blocks Phase 21.
6. Mark the two newly eligible contrasts and every derived query/KDA row as
   `exploratory_min3_support`; preserve the existing confirmatory-support flag
   for every contrast.
7. Build the exact 42-row ROSMAP merged-query universe from the new Phase 21
   DEG subrelease only.
8. Extract one deduplicated FDR-only `AD_both_mito` query from each completed
   broad DEG contrast.
9. Intersect each query with its exact tested-gene and ROSMAP-network
   background.
10. Record every source/query attrition state, deterministic membership hash,
    and KDA execution decision.

Required products:

```text
00_source_deg_min3/config_snapshot.yml
00_source_deg_min3/input_authority.tsv
00_source_deg_min3/contrast_manifest.tsv
00_source_deg_min3/contrast_status.tsv
00_source_deg_min3/model_diagnostics.tsv
00_source_deg_min3/broad_deg_results.tsv.gz
00_source_deg_min3/by_contrast/*.broad_deg.tsv.gz
00_source_deg_min3/phase08_regression_checks.tsv
00_source_deg_min3/checks.tsv
00_source_deg_min3/artifacts.tsv
00_source_deg_min3/status.tsv
input_authority.tsv
contrast_manifest.tsv
query_manifest.tsv
core_mito_identity.tsv
network_identity.tsv
query_attrition.tsv
query_members.tsv.gz
background_members.tsv.gz
checks.tsv
artifacts.tsv
status.tsv
```

Blocking gates:

- the new Phase 21 ROSMAP minimum-3 DEG subrelease reports
  `validated_complete`;
- all 42 ROSMAP broad contrasts complete, including the two expected newly
  eligible vasculature contrasts;
- the 40 shared contrasts pass the frozen Phase 08 regression comparison;
- the two newly eligible contrasts retain `exploratory_min3_support` through
  all downstream tables;
- all seven network files parse and match frozen identities;
- every merged query is the exact deduplicated union of its positive- and
  negative-coefficient qualifying genes;
- every eligible query/background is reconstructible; and
- no prior ROSMAP result is modified.

### Phase 22: ROSMAP harmonized direct-broad KDA release

**Output:** `results/minerva_production/22_harmonized_broad_kda_combo/`

Tasks:

1. Execute only Phase 21-eligible merged-query calls against the matching ROSMAP
   broad networks.
2. Preserve source contrast, donor counts, query and background identities,
   source-sign membership, network identity, and result identity for every call.
3. Retain completed calls with zero significant key drivers as completed null
   calls.
4. Record all non-executed source/query slots explicitly.
5. Reconstruct every returned q value from registered per-call results.
6. Freeze all within-call BH-significant drivers as the ROSMAP discovery
   release; top-five rows are display-only derivatives.

Required products:

```text
run_manifest.tsv
call_returns.tsv.gz
candidate_tests.tsv.gz
significant_returns.tsv
rosmap_broad_driver_units.tsv
run_reconstruction_checks.tsv
run_qc.tsv
checks.tsv
artifacts.tsv
status.tsv
```

Phase 22 supersedes no existing ROSMAP result. It is an additional direct-broad
release with a harmonized query rule. The absent/deprecated Phase 20 direct
broad result is not treated as an input authority.

## 7. SEA-AD validation phases

### VH13: SEA-AD broad-query input freeze

**Output:** `results/validation_human/13_harmonized_broad_kda_inputs/`

Tasks:

1. Freeze SHA-256 identities for the SEA-AD broad DEG release, annotation,
   seven SEA-AD broad networks and release modes, fKDA source, configuration,
   and new scripts.
2. Validate the upstream statuses, compressed files, schemas, unique IDs,
   donor counts, coefficient directions, and gene identities.
3. Build the exact 42-row SEA-AD broad contrast and merged-query universe,
   retaining all non-estimable slots.
4. Extract one deduplicated FDR-only `AD_both_mito` query from each completed
   broad DEG file; never start from a prefiltered DEG list.
5. Intersect queries with the exact tested-gene and SEA-AD-network backgrounds.
6. Record every source/query attrition state, network release mode,
   deterministic membership hash, and KDA execution decision.

Required products:

```text
input_authority.tsv
contrast_manifest.tsv
query_manifest.tsv
core_mito_identity.tsv
network_identity.tsv
query_attrition.tsv
query_members.tsv.gz
background_members.tsv.gz
checks.tsv
artifacts.tsv
status.tsv
```

Blocking gates:

- the SEA-AD DEG release reports `validated_complete`;
- all 28 completed and 14 non-estimable broad contrasts reconcile;
- all seven network files match frozen identities and parse as two-column edge
  lists;
- every merged query is the exact deduplicated union of its positive- and
  negative-coefficient qualifying genes;
- every eligible query and background is reconstructible from frozen inputs;
- vasculature retains its `encode_only_exploratory` flag; and
- no prior SEA-AD result is modified.

### VH14: SEA-AD harmonized direct-broad KDA release

**Output:** `results/validation_human/14_harmonized_broad_kda_combo/`

Tasks:

1. Execute only VH13-eligible merged-query calls against the matching SEA-AD broad
   networks.
2. Preserve source contrast, donor counts, query members, background members,
   source-sign membership, network release mode, and result identity for every call.
3. Retain completed calls with zero significant key drivers as completed null
   calls; do not discard them from the KDA release audit.
4. Record non-executed source/query slots explicitly.
5. Reconstruct every returned q value from the registered result files.
6. Freeze all within-call BH-significant drivers as the SEA-AD broad KDA
   release; top-five rows are display-only derivatives.
7. Flag all vasculature calls as exploratory in every output.

VH14 must retain the distinction among:

```text
source contrast not estimable
source estimable but query empty
effective mapped query below 3
completed KDA with no significant driver
completed KDA with significant driver(s)
```

Only the last two states constitute executed KDA evidence.

Required products mirror the Phase 22 release schema with SEA-AD-specific IDs,
network modes, driver units, checks, artifacts, and status.

## 8. Scientific and interpretive boundaries

- The donor, not the nucleus, is the independent biological replicate.
- Use at least three donors per AD/NCI arm for the new ROSMAP Phase 21 source
  release. Keep at least three donors per Dementia/No-dementia arm for the
  existing SEA-AD source release. Report exact donor counts.
- Treat all inference derived from a ROSMAP arm with 3 or 4 donors as
  exploratory low-replication evidence, even when the DEG or KDA FDR threshold
  is passed. Do not relabel it as confirmatory validation.
- Lowering only the ROSMAP threshold does not expand the matched cross-cohort
  validation universe: SEA-AD `F_e2` and `M_e2` remain non-estimable because
  each has one Dementia donor.
- Keep `AD versus NCI` and `Dementia versus No dementia` as their native,
  cohort-specific phenotype labels.
- Broad pseudobulk can mix within-subtype expression changes with shifts in
  fine-subtype composition; record this limitation with each release.
- Opposing effects among fine subtypes can cancel after broad aggregation.
- A skipped or undersized query is not a completed negative KDA result.
- Top-five tables are display derivatives; they must not define the KDA release.
- Returned-only ACAT values from earlier phases are exploratory and are not
  reused as broad KDA q values.

## 9. Completion criteria

ROSMAP Phase 21-22 and SEA-AD VH13-VH14 are complete only when:

1. the ROSMAP minimum-3 source subrelease completes all 42 contrasts, passes
   the 40-contrast Phase 08 regression check, and reports
   `validated_complete` with no failed checks;
2. all other new status files report `validated_complete` with no failed
   checks;
3. all input, query, background, network, code, and output identities are
   checksum-frozen;
4. every one of the 42 structural merged-query slots per cohort has exactly one
   terminal state;
5. the two minimum-3 ROSMAP vasculature contrasts and all derived rows retain
   the `exploratory_min3_support` flag;
6. completed zero-return calls remain explicitly registered;
7. every returned driver q value reconstructs from the per-call result;
8. every SEA-AD vasculature row retains its exploratory network flag;
9. the two cohort releases have no cross-cohort result dependency; and
10. no pre-existing result, figure, document, configuration, or presentation is
   overwritten.

## 10. Expected scope after source eligibility

Before mitochondrial DEG and network mapping attrition:

```text
ROSMAP structural broad contrasts:     42
ROSMAP completed broad contrasts:      42
ROSMAP completed merged-query slots:    42
SEA-AD structural broad contrasts:     42
SEA-AD completed broad contrasts:      28
SEA-AD completed merged-query slots:    28
Primary full-integrative SEA-AD slots: 24  # six networks x four supported groups
Exploratory vasculature slots:           4  # one network x four supported groups
```

The actual KDA-call counts will be smaller and are intentionally not predicted
in advance. ROSMAP Phase 21 and SEA-AD VH13 will determine their denominators
independently from the frozen FDR-only merged broad DEG queries and exact
network intersections.
