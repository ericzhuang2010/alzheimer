# SEA-AD Fine-Supertype Pseudobulk DEG Processing Plan

**Status:** implemented and executed locally; VH00–VH08 validated complete on 2026-08-20  
**Workload:** Advanced  
**Date:** 2026-08-20  
**Primary endpoint:** 129 SEA-AD `Supertype`s × 6 sex/APOE groups = 774 signed DEG contrasts and 1,548 structural downstream direction slots  
**Implementation root:** `scripts/validation_human/`  
**Result root:** `results/validation_human/`

This is the canonical replacement for the retired broad-cell protocol. It assumes that no prior `scripts/validation_human/` implementation or `results/validation_human/` output can be reused. VH00–VH08 will be implemented and executed again from the raw inputs and frozen references.

### Local execution outcome (2026-08-20)

- All phase statuses from VH00 through VH08 are `validated_complete`; Minerva was not required.
- VH05 streamed all 1,395,601 source nuclei and completed in 13.1 minutes, producing 129 fine-supertype and seven independently aggregated broad-network pseudobulk shards.
- VH06 independently reloaded the shards and reproduced the exact selected total of 31,867,743,351 UMIs and exact fine-to-direct-broad reconciliation.
- VH07 froze 774 fine contrast slots (260 eligible), seven eligible pooled broad contrasts, and 42 stratified broad slots (20 eligible).
- VH08 completed 260 fine, seven pooled broad, and 20 stratified broad DEG results. It released all 1,548 structural fine direction slots, of which 520 are query-ready because they derive from completed fine contrasts.
- The final release contains 287 full DEG result files and remains isolated under `results/validation_human/`; implementation and contract tests remain isolated under `scripts/validation_human/` and `tests/validation_human/`.
- During execution, two implementation-only issues were corrected without changing the frozen analysis contract: R YAML parsing now handles 64-bit identity totals, and sparse non-estimable contexts use explicit grouped indicator columns so one-level factors remain auditable.

The Advanced design is structurally closest to ROSMAP Phase 18: both cross fine cell labels with the same six sex/APOE groups and derive two signed query directions from each DEG contrast. It is not a one-to-one cell-taxonomy replication. ROSMAP has 54 fine types; SEA-AD has 129 included supertypes, and their labels are not directly interchangeable.

## A. Study Intent Summary

### Research question

Can donor-aware SEA-AD differential expression produce fine-cell, sex/APOE-stratified mitochondrial signatures suitable for an independent Phase 18-style key-driver analysis?

### Primary analysis unit and comparison

- Biological replicate: donor.
- Expression unit: raw UMI pseudobulk for one `donor × Supertype`.
- Primary comparison: `Dementia - No dementia` within each sex/APOE group.
- Fine-cell resolution: 129 included SEA-AD supertypes mapped one-to-one to one of seven frozen broad networks.
- Statistical result: one signed, two-sided DEG contrast for each `Supertype × sex/APOE group`.
- Downstream directions: `AD_up_mito` and `AD_down_mito`, derived from the sign of that one contrast rather than fitted as separate tests.

### Headline endpoint

```text
129 included supertypes × 6 sex/APOE groups = 774 structural DEG contrasts
774 signed contrasts × 2 directions          = 1,548 structural direction slots
```

`1,548` is a structural planning count, not a promise of 1,548 runnable KDA queries. Every contrast and direction remains in a complete manifest, but sparsity, donor support, design rank, DEG evidence, gene mapping, MitoCarta membership, network coverage, and the downstream query-size gate reduce the number that can be analyzed.

### Supporting endpoints

- Seven pooled broad-network contrasts provide a higher-power biological anchor.
- Forty-two broad-network × sex/APOE contrasts provide a direct bridge to the prior broad-cell design.
- These supporting tiers remain statistically and operationally separate from the 774-contrast fine primary tier. They do not enter its run denominators, FDR families, or later KDA aggregation.

### Interpretation boundary

The endpoint is a validated genome-wide DEG release plus a prespecified directional query handoff. DEG evidence alone does not establish a key driver, a causal mechanism, or replication of a ROSMAP candidate. Network/KDA selection and ROSMAP overlap begin only after VH08 is complete and require revised downstream plans.

## B. Best-Fit Study Pattern

This is an observational, independent-cohort, donor-pseudobulk validation study with multi-resolution evidence.

The design uses nuclei to estimate cell-type-specific donor expression, while treating the donor as the independent statistical unit. It does not treat 1.4 million nuclei as independent human samples. The headline analysis is fine-supertype and stratified; broad-cell analyses are anchors rather than substitutes for the fine primary tier.

Robust edgeR quasi-likelihood is retained as the primary DEG engine because it:

- models raw donor-level count data;
- supports the existing SEA-AD covariate structure and small-group quasi-likelihood testing;
- preserves continuity with the executed historical SEA-AD workflow; and
- avoids changing both cell resolution and the statistical engine in the same protocol revision.

The plan estimates associations with cognitive status. Separate sex/APOE-stratified estimates are not interaction tests, and they must not be described as causal sex or APOE effects.

## C. Four Workload Configurations

| Configuration | DEG tiers | Structural contrasts | Direction slots | Intended use |
|---|---|---:|---:|---|
| Lite | Seven pooled broad-network anchors | 7 | 14 | Fast cohort-level validation |
| Standard | Lite plus 42 broad-network × group contrasts | 49 | 98 | Reproduce the former broad design |
| **Advanced — selected** | 774 fine primary plus the 49 broad support contrasts | 823 total; 774 headline | 1,646 total; **1,548 headline** | Phase 18-shaped SEA-AD discovery and broad anchoring |
| Publication+ | Advanced plus 24 subclass × 6 sensitivity contrasts | 967 | 1,934 | Multi-resolution sensitivity and publication package |

Only the Advanced configuration is authorized by this plan. Publication+ components are listed so the extension boundary is clear; they are not silently enabled.

## D. Recommended Primary Plan

### Analysis tiers

| Tier ID | Resolution and comparison | Contrasts | Directions | Role |
|---|---|---:|---:|---|
| `fine_supertype_phase18_parity` | 129 supertypes × 6 within-group Dementia contrasts | 774 | 1,548 | Headline primary |
| `broad_pooled_anchor` | 7 broad networks, pooled Dementia contrast | 7 | 14 | Higher-power anchor |
| `broad_stratified_support` | 7 broad networks × 6 within-group contrasts | 42 | 84 | Supportive bridge |
| `subclass_stratified_sensitivity` | 24 subclasses × 6 within-group contrasts | 144 | 288 | Disabled unless Publication+ is approved |

The word `primary` always refers to `fine_supertype_phase18_parity` in the rebuilt workflow. Broad pooled results are anchors, not the primary KDA input.

The headline and FDR-only query rules are two downstream interpretations of the same fine DEG results. They do not create additional DEG models, contrasts, or structural direction slots.

### Frozen fine-cell inventory

The raw SEA-AD taxonomy has 131 relevant supertypes. Exactly `Monocyte` and `Lymphocyte` are excluded from the Microglia-PVM lineage, leaving 129.

| Broad network | SEA-AD inclusion rule | Included supertypes | Fine primary directions |
|---|---|---:|---:|
| `Astrocytes` | `Subclass == Astrocyte` | 6 | 72 |
| `Excitatory_neurons` | `Class == Neuronal: Glutamatergic` | 41 | 492 |
| `Inhibitory_neurons` | `Class == Neuronal: GABAergic` | 67 | 804 |
| `Microglia` | `Subclass == Microglia-PVM`, excluding `Monocyte` and `Lymphocyte` | 4 | 48 |
| `OPCs` | `Subclass == OPC` | 3 | 36 |
| `Oligodendrocytes` | `Subclass == Oligodendrocyte` | 4 | 48 |
| `Vasculature_cells` | `Subclass` in `Endothelial`, `VLMC` | 4 | 48 |
| **Total** |  | **129** | **1,548** |

The `Supertype -> Subclass -> Class -> broad_network` mapping must be materialized and checksum-frozen. Filename-safe IDs must be assigned separately from scientific labels because labels can contain spaces, punctuation, and `/`. Scientific labels must never be inferred back from filenames.

### Frozen groups and phenotype

The six structural groups are:

```text
F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
```

APOE definitions are:

```text
e2  = 2/2 or 2/3
e33 = 3/3
e4  = 3/4 or 4/4
2/4 = excluded
```

The phenotype is `Dementia` versus `No dementia`. `No dementia` must not be renamed `NCI`; it is not guaranteed to match the ROSMAP NCI definition.

Historical metadata counts to reproduce from the restored input are:

| Group | Dementia donors | No-dementia donors | Globally capable of meeting 5/arm? |
|---|---:|---:|---|
| `F_e2` | 1 | 6 | No |
| `F_e33` | 13 | 13 | Yes |
| `F_e4` | 9 | 5 | Yes |
| `M_e2` | 1 | 4 | No |
| `M_e33` | 9 | 10 | Yes |
| `M_e4` | 4 | 3 | No |

Thus 387 of 774 fine contrasts are structurally incapable of meeting the five-donor-per-arm rule before considering cell-type sparsity. Only `F_e33`, `F_e4`, and `M_e33` can be estimable in this cohort.

### Pre-DEG feasibility expectation

A metadata-only preflight audit of the exact historical snapshot predicted 260 supertype/group contrasts passing the 20-nucleus and 5-donor-per-arm support gates. VH04–VH07 must recompute this result; it is an expected reproducibility assertion, not an input used to force eligibility.

`Pooled-support labels` below is a descriptive sparsity check: the number of supertypes with at least five 20-nucleus donor profiles in each phenotype when sex/APOE is ignored. This plan does not fit a pooled fine-supertype tier.

| Broad network | Included labels | Pooled-support labels | Support-passing stratified contrasts | Maximum directions before later gates |
|---|---:|---:|---:|---:|
| Astrocytes | 6 | 6 | 10 | 20 |
| Excitatory neurons | 41 | 35 | 88 | 176 |
| Inhibitory neurons | 67 | 64 | 142 | 284 |
| Microglia | 4 | 1 | 3 | 6 |
| OPCs | 3 | 2 | 3 | 6 |
| Oligodendrocytes | 4 | 4 | 9 | 18 |
| Vasculature | 4 | 3 | 5 | 10 |
| **Total** | **129** | **115** | **260** | **520** |

The expected support-passing contrasts by group are `F_e33 = 100`, `F_e4 = 68`, and `M_e33 = 92`. Full-rank, coefficient, residual-degree-of-freedom, fit, DEG, and downstream query gates can reduce the count further.

The broad-support replay has its own historical expectation: all seven pooled anchors are eligible, while 20 of 42 broad stratified contrasts are eligible and 22 are `not_estimable`. The expected 20 are all seven `F_e33`, all seven `M_e33`, and six `F_e4` contrasts; Vasculature `F_e4` lacks the required profile support. VH06/VH07 must recompute these values rather than insert them.

## E. Data Strategy and Example Dataset Directions

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

### Raw SEA-AD input

The raw input files are currently absent and must be restored from the authoritative source or a verified backup. This plan does not invent an acquisition URL. No expression phase may begin until VH00/VH01 establish file identity.

Expected configured paths:

```text
data/seaad/SEAAD_A9_RNAseq_final-nuclei.2024-02-13.h5ad
data/seaad/SEAAD_A9_RNAseq_final-nuclei_metadata.2024-02-13.csv
```

Historical identity assertions for the exact 2024 snapshot are:

| Property | Expected value | Identity type |
|---|---|---|
| H5AD bytes | 37,938,782,321 | Exact size |
| Observations | 1,395,601 | Exact shape |
| Features | 36,601 | Exact shape |
| UMI CSR stored entries | 7,989,685,110 | Exact `nnz` |
| H5AD structure digest | `9e63f9281b9150c8dd8b32cfae58b823dae5472be8ae746dfecd1f79514e32a6` | Historical sampled/structural digest, not a full-file SHA-256 |
| Observation-order digest | `76a28a761003c4a538cad107cc2f92f0e76ae27cfe56076b7fe72d4de2fdc3ba` | SHA-256 of ordered observation identity |
| Feature-order digest | `7dcafda20108ee578e451c410238e1b659478f02ca7a50bde24bd618b9ba972d` | SHA-256 of ordered feature identity |
| Metadata CSV bytes | 1,444,844,786 | Exact size |
| Metadata CSV SHA-256 | `9ef1c9e1180d4404ce814283a25e3b2f0da05ab152af305990a1e3f2f682f3fc` | Full-file SHA-256 |
| Metadata columns | 133 | Exact schema count |

The artifact schema must store `digest_algorithm`, `digest_scope`, and `digest_value` separately. The historical H5AD structure digest must never be mislabeled as a full SHA-256. A full H5AD checksum should be computed once during input restoration when practical and then frozen.

### Expression and metadata source

- Use only `layers["UMIs"]` as the expression input.
- Do not use normalized `X`, scVI coordinates, UMAP coordinates, or neighbor graphs for DEG.
- Require `Used in analysis == True`.
- Require `method == 10Xv3.1` for the primary analysis.
- Use `Supertype`, `Subclass`, and `Class` only through the frozen taxonomy mapping.
- Use H5AD `obs` as the canonical computational metadata because it is row-aligned to the UMI matrix; do not merge the CSV back into it.
- Use the CSV as an independent mirror check. It must have identical ordered row identity and exact canonicalized values for every model- or selection-critical field.

### Reference layer

Freeze and checksum these configured references before mapping:

```text
data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
data/reference/hgnc/hgnc_complete_set_2026-06-05.txt
data/reference/Human.MitoCarta3.0.xls
results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz
```

The GENCODE and HGNC snapshots support gene annotation. The current Phase 18 gene annotation defines the downstream current-symbol and core-MitoCarta membership used for query construction. A disagreement that changes query membership is blocking and must not be silently resolved.

### Data and artifact retention

Before any large output is created, VH00 must freeze a storage policy:

| Artifact class | Local treatment | Git treatment |
|---|---|---|
| Raw H5AD/CSV | Read-only under `data/seaad/` | Ignored; checksum-frozen |
| Per-observation group-code arrays and full nucleus-selection table | Local computational/audit handoff | Ignored; manifest and checksums tracked |
| Transaction checkpoints/deltas | Local temporary or restart store | Ignored |
| Per-supertype count shards | Local reproducibility bundle; archive after validation | Ignored; manifest and checksums tracked |
| Large edgeR objects | Retain only when needed for replay; archive with hashes | Ignored |
| Config, code, statuses, manifests, checks, compact QC | Repository records | Tracked |
| Compact directional query-input tables and release indexes | Repository/release records | Tracked when size permits |
| Full tested DEG shards | Local or external release bundle | Track only through checksums unless a versioned large-file store is explicitly configured |

The current broad unignore rule for `results/validation_human` is not a sufficient large-artifact policy. The implementation must add explicit ignore rules before execution, not after multi-gigabyte artifacts are produced.

## F. Core Analysis Modules and Method Choices

### 1. Donor-aware pseudobulk

Raw UMIs are summed to `donor × Supertype`. Nucleus counts inform profile eligibility but never become replicate weights that inflate the biological sample size.

The complete structural sample grid contains:

```text
78 donors × 129 supertypes = 10,062 donor-supertype profiles
```

Zero-nucleus and low-nucleus profiles remain in the sample manifest. Only profiles with at least 20 selected nuclei enter the primary DEG models. A 50-nucleus flag is retained for sensitivity summaries without changing primary eligibility.

### 2. Cohort and covariates

The expected cohort is 78 donors:

```text
83 source donors
- 3 neurotypical reference donors
- 2 APOE 2/4 donors
= 78 analysis donors: 37 Dementia and 41 No dementia
```

Age at death and PMI are scaled once using the frozen 78-donor cohort, not separately within cell types or groups. Source values and derived values are retained together. Required clinical fields must be invariant within donor.

The primary cohort uses no covariate imputation. A donor missing a required field is excluded with the source value and reason preserved before any cell-type eligibility decision.

### 3. Primary fine model

For each supertype, use all donor profiles with at least 20 nuclei and fit one model:

```text
~ 0 + diagnosis_sex_apoe_group
    + age_death_scaled
    + pmi_scaled
    + study
```

Each eligible contrast is:

```text
+1 × Dementia__sex__apoe - 1 × No_dementia__sex__apoe
```

Unused factor levels may be removed deterministically. The primary formula may not be adaptively simplified to rescue a contrast. Missing coefficients, incomplete covariates, rank deficiency, or nonpositive residual degrees of freedom produce an explicit `not_estimable` result.

### 4. Broad support models

The pooled broad anchor uses:

```text
~ diagnosis + sex + apoe_group + age_death_scaled + pmi_scaled + study
```

The broad stratified support tier uses the grouped fine-model formula. It is fitted to independently aggregated donor × broad-network profiles, not by pooling fine-model p-values.

### 5. Filtering, normalization, and testing

For each supertype:

1. Build one `DGEList` from all profiles passing the 20-nucleus gate.
2. Freeze one gene universe using `filterByExpr(y0, group = metadata$diagnosis)`.
3. Subset with `keep.lib.sizes = FALSE`.
4. Apply `calcNormFactors(method = "TMM")`.
5. Apply robust dispersion estimation.
6. Fit with `glmQLFit(..., robust = TRUE)`.
7. Test only prespecified eligible contrast vectors with `glmQLFTest`.
8. Recompute BH FDR across all tested genes separately within each completed contrast.

For each broad network, share the counts, frozen filter universe, library-size recalculation, and TMM factors across the two broad tiers. Then run `estimateDisp(..., design = pooled_design, robust = TRUE)` and `glmQLFit` for the pooled model, and run a separate `estimateDisp(..., design = grouped_design, robust = TRUE)` and `glmQLFit` for the grouped model. Each contrast is tested only from its matching design/fit.

The shared filter is computed once per cell context, not separately for each group contrast. Dispersion is estimated from all eligible profiles in that context, not from an isolated 5-versus-5 subset, but it is always estimated against the model-specific design matrix.

### 6. Effect and multiplicity contract

- Positive `logFC` means higher expression in Dementia.
- Report `logFC`, logCPM/abundance, QL statistic, raw p-value, and within-contrast BH FDR for every tested feature.
- Do not correct across the 774 contrasts for the primary Phase 18-style query rule.
- Report both `FDR < 0.05` counts and the stricter headline query-source count.
- The prespecified headline rule is:

```text
FDR < 0.05 AND abs(logFC) > log2(1.3)
```

The value `1.3` is inherited from the Yu/ROSMAP Phase 08 `paper_deg` convention and therefore from the DEG signatures used by Phase 12 and Phase 18. It was not estimated from SEA-AD and is not a universal mitochondrial effect threshold. On the log2 scale, `log2(1.3) = 0.3785`; the rule retains expression ratios above 1.3 or below `1 / 1.3 = 0.7692`.

This effect gate is applied after the ordinary QL test against zero and only when defining the headline Phase 18-parity query source. It does not filter model fitting, BH correction, or the genome-wide DEG release. Every tested feature remains available with its continuous effect and uncertainty evidence. The primary protocol does not use `glmTreat`.

A prespecified, separately labeled `fdr_only_query_sensitivity` uses:

```text
FDR < 0.05
```

It reuses the same completed DEG contrasts and changes no fit, tested universe, structural slot, or FDR calculation. It may show whether the 1.3-fold gate materially limits downstream query size, but it cannot replace, be pooled with, or be used to tune the headline `phase18_parity_query` rule.

Both query branches use the same `logFC` sign for direction and, in VH10, the same current-symbol mapping, core-MitoCarta restriction, induced-network background, minimum-effective-query rule, KDA engine, aggregation, correction, and ranking. The presence or absence of the 1.3-fold gate is their only difference.

Within-contrast BH supports inference inside each prespecified contrast. Any global statement spanning all 774 contrasts requires a separately labeled cross-contrast multiplicity analysis; it cannot be inferred from a count of within-contrast discoveries alone.

### 7. Complete result representation

Materializing a 36,601-feature table for every structural contrast would create up to 28,329,174 repeated rows before compression. Instead:

- write one 36,601-feature filter/testability table per supertype or broad context;
- write model-native tested rows for each completed contrast;
- keep non-estimable contrasts in the contrast manifest without fabricated gene rows; and
- provide stable keys that reconstruct the complete feature state deterministically.

For a completed contrast, features outside the frozen universe are `filtered`, not nonsignificant. For a non-estimable contrast, statistics are absent, not set to zero or one.

### 8. Directional query handoff

VH08 expands the 774 fine contrast rows into exactly 1,548 structural direction rows and exposes every field needed for later query construction:

- source contrast and terminal status;
- tested/filtered feature state;
- `logFC`, FDR, and effect direction;
- source, approved, and frozen current symbols;
- mapping status; and
- frozen Phase 18 core-MitoCarta annotation as a provenance field.

VH08 summarizes directional counts under both named rules—`phase18_parity_query` and `fdr_only_query_sensitivity`—but it does not freeze an authoritative mitochondrial query-member set. VH10 must reconstruct membership from the checksum-frozen DEG and annotation rows and run the two branches independently. At that boundary, feature-to-symbol duplicates use set semantics: a current symbol enters a direction if any mapped source feature passes that direction's exact rule. Differing feature-level DEG values do not cause a block. Ambiguous current-symbol identity or conflicting core-MitoCarta annotation that could change membership is blocking.

Network induction, effective query size, the minimum-three runnable gate, KDA, ACAT, candidate selection, and ROSMAP overlap remain downstream work. VH08 must not label a DEG direction as runnable.

### 9. Prohibited post-result changes

The primary result may not be enlarged after inspection by:

- lowering the 20-nucleus or 5-donor thresholds;
- dropping `study`, age, or PMI adaptively;
- filtering genes separately within each small contrast;
- changing the primary estimator to nucleus-level testing;
- adding a post hoc 10%-nucleus detection rule copied from ROSMAP;
- switching to `glmTreat`;
- replacing the headline FDR/effect rule, adding further thresholds, or using the prespecified FDR-only sensitivity to tune the headline rule; or
- pooling fine, broad, or sensitivity tiers in one downstream denominator.

Any unlisted change requires a dated protocol amendment and a separately labeled sensitivity tier. The already prespecified `fdr_only_query_sensitivity` is the sole effect-threshold sensitivity authorized here.

## G. Validation and Extension Layers

### Blocking internal validation

The clean rebuild must establish:

1. exact raw-input identity and schema;
2. exact donor cohort and frozen covariates;
3. exact observation and feature ordering;
4. exactly 129 included supertypes and exactly two excluded immune labels;
5. one and only one broad-network assignment for every selected supertype;
6. exact raw-UMI conservation;
7. exact equality between fine-count rollup and a separately coded direct broad aggregation;
8. a complete 774-row fine contrast manifest;
9. a complete 1,548-row fine direction manifest;
10. explicit status and reason fields for every unavailable analysis; and
11. replayable per-contrast BH and sampled model results.

Historical exact-snapshot expectations are 1,189,172 selected nuclei, 31,867,743,351 selected UMIs, and 37,297,743,646 UMIs across all visited observations. These must be recomputed. A mismatch is investigated rather than overwritten or waved through.

### Supporting evidence layers

- `broad_pooled_anchor` assesses higher-powered direction and magnitude at the network level.
- `broad_stratified_support` checks whether broad group-specific effects tell a compatible story.
- `fdr_only_query_sensitivity` measures how much the inherited 1.3-fold gate changes query size and downstream conclusions while remaining separate from the headline `phase18_parity_query` branch.
- The 50-nucleus flag supports a stricter profile-coverage sensitivity without redefining the main cohort.
- The 24-subclass grid is a disabled Publication+ sensitivity that may be derived from fine counts without rereading the H5AD.
- Formal sex/APOE interaction models, alternate pathology endpoints, and alternate assay chemistries are future amendments rather than implicit rescue analyses.

Fine-to-broad concordance is descriptive because the fine and broad estimates use overlapping data. It is not independent replication.

### Downstream extension

The revised [VH09 candidate-freeze plan](vh09_phase18_candidate_freeze.md) freezes ROSMAP candidate units without crossing them to SEA-AD contrasts. The revised [VH10 KDA plan](vh10_seaad_kda_rediscovery_and_overlap.md) consumes the fine primary manifest, preserves the 1,548-slot structural grid, and runs `phase18_parity_query` and `fdr_only_query_sensitivity` independently. Neither branch may be obtained by filtering or reranking the other branch's winners.

> **Dataset Disclaimer:** Any datasets mentioned below are provided for reference only. Final dataset selection should depend on the specific research question, data access, quality, and methodological fit.

## H. Step-by-Step Workflow

### Common execution contract

VH00–VH08 are a new implementation. A historical script or result may be inspected as design history, but it is not a predecessor artifact and may not be copied into a `validated_complete` phase.

Every executable must:

- accept a single frozen config through `--config`;
- provide `--help` and reject unknown arguments;
- validate predecessor status and artifact checksums before analysis;
- write only under its configured phase directory in `results/validation_human/`;
- canonicalize output paths and reject symlink or `..` escapes;
- use deterministic ordering, stable IDs, and recorded software versions;
- write outputs atomically;
- write task-local status/artifact records when operating as a worker; the phase's sole finalizer writes the one-row phase `status.tsv` and complete phase `artifacts.tsv`; and
- exit nonzero when a blocking gate fails.

The new implementation is planned as:

```text
scripts/validation_human/
├── README.md
├── seaad_deg_config.yml
├── seaad_common.py
├── 00_check_environment.py
├── 01_audit_inputs.py
├── 02_build_donor_cohort.py
├── 03_harmonize_genes.py
├── 04_build_supertype_manifest.py
├── 05_stream_pseudobulk.py
├── 06_validate_pseudobulk.R
├── 07_build_contrast_manifests.R
├── 08_run_deg.R
└── 08_finalize_deg_release.py

tests/validation_human/
└── test_seaad_deg_contract.py
```

The planned result tree is:

```text
results/validation_human/
├── 00_environment/
├── 01_audit/
├── 02_cohort/
├── 03_genes/
├── 04_supertype_manifest/
├── 05_pseudobulk/
├── 06_pseudobulk_qc/
├── 07_contrasts/
└── 08_deg/
    ├── fine_supertype_phase18_parity/
    ├── broad_pooled_anchor/
    ├── broad_stratified_support/
    ├── filters/
    ├── model_objects/
    └── query_handoff/
```

The exact filenames below are part of the proposed interface and should be frozen in VH00 before code execution.

### VH00 — Environment, configuration, namespace, and storage freeze

**Goal:** create the machine-readable scientific contract and ensure that the rebuild can run without writing outside its namespace.

**Inputs:** repository state, raw/reference paths, the decisions in this plan, Python/R environments, and local storage capacity.

**Implementation:**

- Create the script tree, README, config, shared path/status/checksum helpers, and contract tests.
- Pin Python packages needed for HDF5 and sparse streaming, including `h5py`, NumPy, SciPy, pandas, and PyYAML.
- Pin R, edgeR, limma, Matrix, data.table, yaml, and digest through the repository environment.
- Freeze all scientific thresholds, formulas, tier names, group order, taxonomy rules, expected structural counts, random seed, and output paths, including the two immutable query-rule IDs and their exact predicates.
- Freeze a storage class for every planned artifact and add large-artifact ignore rules before running VH01.
- Record git revision and dirty-state details; a dirty tree is allowed only if the exact diff is archived in provenance.
- Benchmark free disk and require a configured safety reserve. Restoration of the two raw inputs alone requires about 36.7 GiB.

**Principal outputs:**

```text
results/validation_human/00_environment/config_snapshot.yml
results/validation_human/00_environment/environment.tsv
results/validation_human/00_environment/environment_checks.tsv
results/validation_human/00_environment/storage_policy.tsv
results/validation_human/00_environment/planned_artifacts.tsv
results/validation_human/00_environment/artifacts.tsv
results/validation_human/00_environment/status.tsv
```

**Blocking gate:** required software is available, all paths are safe, storage policy is explicit, structural constants equal 129/774/1,548, and raw inputs are either present or the phase terminates as `blocked_missing_input` without creating downstream outputs.

### VH01 — Restore and audit raw inputs

**Goal:** establish the identity, structure, and semantic integrity of the H5AD and matching metadata CSV without treating historical results as evidence.

**Inputs:** validated VH00 config, restored H5AD/CSV, and no prior validation output.

**Implementation:**

- Verify exact file sizes, dimensions, object encodings, required fields, and recorded digests.
- Verify `X` and `layers/UMIs` have identical `1,395,601 × 36,601` shapes and compatible CSR row structure.
- Confirm that sampled UMI values are finite, nonnegative, integer-valued counts despite their storage dtype.
- Confirm the CSV has 1,395,601 data rows and 133 columns, with matching ordered observation identifiers and compatible headers.
- Canonically serialize and compare all rows for donor, phenotype, sex, APOE, age, PMI, study, neuropathology, assay method, `Used in analysis`, `Class`, `Subclass`, and `Supertype`; record field-wise checksums and mismatch counts.
- Inventory `Class`, `Subclass`, `Supertype`, donor, assay, phenotype, sex, APOE, age, PMI, study, and pathology fields.
- Verify unique source feature rows and record that the embedded gene ID field does not substitute for external stable identifiers.
- Compute a full H5AD checksum if feasible; otherwise retain the historical structure digest with its truthful scope and add deterministic sampled-content checks.

**Principal outputs:**

```text
results/validation_human/01_audit/input_identity.tsv
results/validation_human/01_audit/h5ad_structure.tsv
results/validation_human/01_audit/obs_schema.tsv
results/validation_human/01_audit/category_inventory.tsv
results/validation_human/01_audit/gene_inventory_raw.tsv
results/validation_human/01_audit/csv_h5ad_alignment.tsv
results/validation_human/01_audit/critical_metadata_field_checksums.tsv
results/validation_human/01_audit/observation_order_checksum.tsv
results/validation_human/01_audit/audit_checks.tsv
results/validation_human/01_audit/artifacts.tsv
results/validation_human/01_audit/status.tsv
```

**Blocking gate:** all exact-snapshot identity assertions pass, required metadata and the raw UMI layer exist, and H5AD/CSV observation identity agrees. A different source release requires a protocol amendment, not adjusted expected values.

### VH02 — Rebuild the authoritative donor cohort

**Goal:** create one verified donor row and freeze all analysis covariates and group labels.

**Inputs:** the checksum-validated H5AD `obs` fields reread from the raw input, VH01 identity/schema status, and VH00 cohort rules. VH01 intentionally does not materialize a second full observation table.

**Implementation:**

- Verify every clinical field used by the model is invariant within donor.
- Start from all 83 source donors.
- Exclude three neurotypical reference donors and two APOE `2/4` donors.
- Require the two analysis phenotype levels and complete finite model covariates.
- Derive sex, APOE group, the six `signature_group` labels, and source-preserving exclusion reasons.
- Scale age at death and PMI once across the included 78 donors and freeze the center/scale constants.
- Tabulate diagnosis × sex × APOE, study, and cognitive-pathology composition.

**Principal outputs:**

```text
results/validation_human/02_cohort/donor_metadata_all.tsv
results/validation_human/02_cohort/donor_cohort_primary.tsv
results/validation_human/02_cohort/cohort_exclusion_flow.tsv
results/validation_human/02_cohort/donor_group_counts.tsv
results/validation_human/02_cohort/covariate_scaling.tsv
results/validation_human/02_cohort/cognitive_pathology_crosstab.tsv
results/validation_human/02_cohort/donor_invariance_checks.tsv
results/validation_human/02_cohort/artifacts.tsv
results/validation_human/02_cohort/status.tsv
```

**Blocking gate:** the exact snapshot yields 78 included donors, 37 Dementia and 41 No dementia, with the 12 arm counts in Section D and no incomplete model covariate.

### VH03 — Harmonize genes and freeze feature identity

**Goal:** preserve the H5AD matrix row identity while adding auditable stable/current symbols and mitochondrial annotations.

**Inputs:** VH01 feature inventory and checksum-frozen GENCODE, HGNC, MitoCarta, and Phase 18 annotation references.

**Implementation:**

- Preserve all 36,601 source features in exact H5AD order; do not merge or drop rows before pseudobulk.
- Attach GENCODE identifiers and approved HGNC symbols only when mapping is unambiguous.
- Record exact, approved, alias, ambiguous, and unresolved mapping states.
- Freeze a `current_symbol_for_kda` and Phase 18 core-MitoCarta field for downstream set construction.
- Keep source symbol, approved symbol, current symbol, Ensembl ID, mapping method, and ambiguity reason as separate fields.
- Produce deterministic feature and reference checksums.

**Principal outputs:**

```text
results/validation_human/03_genes/gene_annotation_master.tsv
results/validation_human/03_genes/gene_aliases_used.tsv
results/validation_human/03_genes/gene_mapping_ambiguities.tsv
results/validation_human/03_genes/feature_order.tsv
results/validation_human/03_genes/reference_identity.tsv
results/validation_human/03_genes/gene_checks.tsv
results/validation_human/03_genes/artifacts.tsv
results/validation_human/03_genes/status.tsv
```

**Blocking gate:** exactly 36,601 unique source feature rows remain in the frozen matrix order, the feature digest matches VH01, and no ambiguous mapping is silently collapsed.

### VH04 — Freeze taxonomy, nucleus selection, and group codes

**Goal:** assign selected nuclei to fine and broad pseudobulk groups with an explicit, reproducible taxonomy contract.

**Inputs:** the checksum-validated ordered H5AD `obs` fields reread from the raw input, VH01 identity/schema status, VH02 donors, VH03 feature status, and frozen taxonomy rules. Observation-order validation is repeated before assigning group codes.

**Implementation:**

- Require `Used in analysis == True`, `method == 10Xv3.1`, and donor membership in VH02.
- Inventory all 131 raw relevant supertypes.
- Exclude exactly `Monocyte` and `Lymphocyte`; retain exactly 129 supertypes.
- Build and freeze `supertype_to_broad_network.tsv`, including scientific labels and stable safe IDs.
- Assign each selected observation a fine donor-supertype code and, independently from the fine rollup, a direct donor-broad code.
- Assign every excluded observation a negative code and one explicit exclusion reason.
- Write the complete 78 × 129 donor-supertype profile grid, including zero-nucleus cells.
- Tabulate primary and 50-nucleus sensitivity eligibility without fitting a model.
- Recompute the metadata-only 260 support-passing contrast expectation.

**Principal outputs:**

```text
results/validation_human/04_supertype_manifest/supertype_inventory.tsv
results/validation_human/04_supertype_manifest/supertype_to_broad_network.tsv
results/validation_human/04_supertype_manifest/supertype_safe_ids.tsv
results/validation_human/04_supertype_manifest/nucleus_to_supertype_group_code.npy
results/validation_human/04_supertype_manifest/nucleus_to_direct_broad_group_code.npy
results/validation_human/04_supertype_manifest/nucleus_selection.tsv.gz
results/validation_human/04_supertype_manifest/donor_supertype_nucleus_counts.tsv
results/validation_human/04_supertype_manifest/nucleus_exclusion_summary.tsv
results/validation_human/04_supertype_manifest/support_preflight.tsv
results/validation_human/04_supertype_manifest/cell_manifest_checks.tsv
results/validation_human/04_supertype_manifest/artifacts.tsv
results/validation_human/04_supertype_manifest/status.tsv
```

**Blocking gate:** selected observations partition into exactly one included supertype and broad network; there are 129 included labels with the 6/41/67/4/3/4/4 distribution; all group arrays match the VH01 observation order; and the exact snapshot reproduces 1,189,172 selected nuclei. The 260 support count must be reproduced or a discrepancy must be resolved before DEG fitting.

### VH05 — Stream fine and direct-broad pseudobulk counts

**Goal:** aggregate all raw UMIs exactly once without loading or densifying the nucleus × gene matrix.

**Inputs:** H5AD `layers/UMIs` CSR arrays, VH03 feature order, and both VH04 group-code arrays.

**Implementation:**

1. Stream bounded consecutive observation blocks from the UMI CSR layer.
2. Exhaustively verify finite, nonnegative, integer-valued counts and valid feature indices.
3. Aggregate each block into donor-supertype and independently coded donor-broad accumulators.
4. Track all-source, selected-source, fine-pseudobulk, and direct-broad UMI totals.
5. Use either immutable block-delta shards followed by deterministic reduction or an in-memory `int64` accumulator with atomic snapshot replacement.
6. Never use a mutable memmap plus only a row counter as a resumability contract; a crash between data flush and ledger update could double-apply a block.
7. Reduce to 129 per-supertype count shards with a stable sample order and a separately generated broad bundle.
8. Sum fine shards through the frozen mapping and require cell-by-cell equality with direct broad counts for every gene and donor.

The maximum fine accumulator is 10,062 × 36,601 = 368,279,262 `int64` values, about 2.74 GiB before copies. Final R jobs must read one bounded shard at a time rather than the full matrix.

**Principal outputs:**

```text
results/validation_human/05_pseudobulk/fine_counts/<supertype_id>.counts.tsv.gz
results/validation_human/05_pseudobulk/fine_samples/<supertype_id>.samples.tsv
results/validation_human/05_pseudobulk/direct_broad_counts/<broad_network>.counts.tsv.gz
results/validation_human/05_pseudobulk/pseudobulk_shard_manifest.tsv
results/validation_human/05_pseudobulk/block_ledger.tsv
results/validation_human/05_pseudobulk/checkpoints/
results/validation_human/05_pseudobulk/count_conservation.tsv
results/validation_human/05_pseudobulk/fine_broad_reconciliation.tsv
results/validation_human/05_pseudobulk/pseudobulk_checks.tsv
results/validation_human/05_pseudobulk/artifacts.tsv
results/validation_human/05_pseudobulk/status.tsv
```

**Blocking gate:** every observation is visited once; all output counts are finite nonnegative integers; source and pseudobulk UMI totals are exact; fine rollup equals direct broad aggregation gene-by-donor; feature/sample checksums agree; and the exact snapshot reproduces 31,867,743,351 selected UMIs.

### VH06 — Validate pseudobulk profiles and model inputs

**Goal:** independently validate count shards, clinical joins, profile eligibility, and model-ready metadata without creating one monolithic R object.

**Inputs:** VH05 fine and broad shards, VH04 nucleus counts, VH03 features, and VH02 donor metadata.

**Implementation:**

- Reload every shard and verify feature and sample order by checksum.
- Join donors by stable ID, never row order.
- Recompute nucleus counts, library sizes, detected features, and mitochondrial fractions.
- Retain every structural profile and label `primary_profile_eligible = nuclei >= 20`.
- Retain `sensitivity_profile_eligible = nuclei >= 50` separately.
- Ensure all model-entering profiles have nonzero libraries and complete finite covariates.
- Produce per-supertype and per-broad-context QC summaries suitable for bounded R jobs.
- Recheck UMI conservation and fine/direct-broad reconciliation independently in R.

**Principal outputs:**

```text
results/validation_human/06_pseudobulk_qc/profile_manifest.tsv.gz
results/validation_human/06_pseudobulk_qc/profile_eligibility.tsv
results/validation_human/06_pseudobulk_qc/library_qc.tsv.gz
results/validation_human/06_pseudobulk_qc/supertype_qc_summary.tsv
results/validation_human/06_pseudobulk_qc/broad_qc_summary.tsv
results/validation_human/06_pseudobulk_qc/count_conservation_recheck.tsv
results/validation_human/06_pseudobulk_qc/fine_broad_reconciliation_recheck.tsv
results/validation_human/06_pseudobulk_qc/pseudobulk_qc_checks.tsv
results/validation_human/06_pseudobulk_qc/artifacts.tsv
results/validation_human/06_pseudobulk_qc/status.tsv
```

**Blocking gate:** all 129 fine shards and seven broad bundles reload; all joins and counts reconcile; every model-entering profile passes the 20-nucleus, nonzero-library, and covariate checks; and excluded/ineligible profiles remain explicit.

### VH07 — Declare all contrasts, directions, and model designs

**Goal:** freeze the complete analysis grid and decide model estimability without looking at gene-level DEG results.

**Inputs:** VH06 profile/QC manifests, VH02 covariates, and frozen formulas and thresholds.

**Implementation:**

- Create exactly 774 fine contrast rows in deterministic broad-network, supertype, and group order.
- Create exactly 1,548 fine direction rows by crossing each contrast with `Dementia_up` and `Dementia_down`.
- Create separate 7-row broad pooled and 42-row broad stratified contrast manifests and their 14/84 direction rows.
- For each context, construct the exact model matrix after deterministic unused-level removal.
- Record design columns, rank, sample count, residual degrees of freedom, required coefficient names, and complete contrast vectors.
- Require at least five eligible donors in each disease arm for every direct Dementia contrast, including each pooled broad anchor and every stratified fine or broad contrast.
- Separate `support_status`, `eligibility_status`, and later `terminal_status`.
- Preserve a deterministic non-estimability reason for every unavailable slot.

Minimum fine contrast identity fields are:

```text
contrast_slot
contrast_id
deg_tier
supertype_id
supertype_label
broad_network
signature_group
sex
apoe_group
case_phenotype
reference_phenotype
coefficient_direction
n_case_donors
n_reference_donors
formula_id
design_id
contrast_vector_id
support_status
eligibility_status
ineligibility_reason
```

VH08 appends `terminal_status`, tested/filtered feature counts, result/filter shard paths, and their SHA-256 values without changing the VH07 identity fields.

Minimum fine direction identity fields are:

```text
direction_slot
direction_slot_id
contrast_id
deg_tier
supertype_id
supertype_label
broad_network
signature_group
deg_direction
phase18_signature_direction
source_eligibility_status
```

The VH08 version also carries source terminal status, tested-feature count, result/filter artifact IDs, and checksums. A downstream `kda_run_id` is deliberately absent; VH10 creates it only after query and network construction.

Use `Dementia_up`/`Dementia_down` as truthful DEG directions and map them explicitly to `AD_up_mito`/`AD_down_mito` for Phase 18 compatibility.

**Principal outputs:**

```text
results/validation_human/07_contrasts/fine_contrast_manifest.tsv
results/validation_human/07_contrasts/fine_direction_manifest.tsv
results/validation_human/07_contrasts/broad_pooled_contrast_manifest.tsv
results/validation_human/07_contrasts/broad_pooled_direction_manifest.tsv
results/validation_human/07_contrasts/broad_stratified_contrast_manifest.tsv
results/validation_human/07_contrasts/broad_stratified_direction_manifest.tsv
results/validation_human/07_contrasts/design_columns.tsv.gz
results/validation_human/07_contrasts/design_rank_checks.tsv
results/validation_human/07_contrasts/contrast_vectors.tsv.gz
results/validation_human/07_contrasts/donor_counts_by_required_group.tsv
results/validation_human/07_contrasts/contrast_checks.tsv
results/validation_human/07_contrasts/artifacts.tsv
results/validation_human/07_contrasts/status.tsv
```

**Blocking gate:** all tier counts are exact; every row has an eligibility decision and reason; no group is silently omitted; every eligible model is full rank with positive residual degrees of freedom; required coefficients exist; and the metadata-only support result reproduces 260 fine contrasts before design gates.

For the exact historical snapshot, the same gate also requires seven eligible pooled broad anchors and the explained 20-eligible/22-not-estimable split across the 42 broad stratified contrasts.

### VH08 — Fit robust edgeR models and publish the DEG release

**Goal:** fit every eligible analysis, retain complete status information, validate statistics, and produce a fine directional handoff without performing KDA.

**Inputs:** validated VH03 gene annotations, VH05 count shards, VH06 profile manifests, and all VH07 design/contrast artifacts.

**Fine-tier fitting:**

1. Process one supertype at a time in stable ID order or as a checksum-recorded task array.
2. Load only that supertype's count and sample shard.
3. Build the shared `filterByExpr` universe and fit the one robust QL group model.
4. Test all and only VH07-eligible group contrasts.
5. Compute BH FDR independently within each completed contrast.
6. Write filter state, tested results, design/normalization diagnostics, and a completion record atomically.
7. Continue collecting diagnostic results if another context fails, but do not mark VH08 complete while an eligible contrast has terminal status `failed`.

If no feature survives the frozen `filterByExpr` rule, all otherwise design-eligible contrasts for that context receive terminal `not_estimable` with reason `no_genes_after_filterByExpr`; this is distinct from an unexpected fit failure. A fitted contrast with zero significant genes is still `completed`.

If a task array is used, each supertype writes only to its own task directory and task-status file. The finalizer is the sole writer of shared indexes, aggregate checks, and the phase status; concurrent workers must never append to a shared TSV.

**Broad-tier fitting:**

- Fit the pooled and grouped broad models from the direct broad pseudobulks.
- Use one frozen filter universe and TMM normalization per broad network, then estimate dispersion and fit separately against the pooled and grouped design matrices.
- Write broad outputs under their separate tier directories.
- Never combine broad and fine p-values or use broad results to decide which fine tests to retain.

**Finalization:**

- Verify tested rows have unique source feature keys and finite statistics.
- Verify BH by recomputing it from all raw p-values in sampled and full small fixtures.
- Add result/filter paths and SHA-256 values to every completed contrast record.
- Preserve all non-estimable and failed slots without gene-statistic fabrication.
- Expand/validate the complete fine direction manifest.
- Summarize directional DEG and mapping counts separately under `phase18_parity_query` and `fdr_only_query_sensitivity`, without freezing authoritative query membership.
- Write a compact index rather than binding every result shard into one in-memory table.
- Sample-replay edgeR fits from retained objects or deterministic fit inputs.

**Principal fine outputs:**

```text
results/validation_human/08_deg/fine_supertype_phase18_parity/filters/<supertype_id>.filter.tsv.gz
results/validation_human/08_deg/fine_supertype_phase18_parity/tested/<contrast_id>.tsv.gz
results/validation_human/08_deg/fine_supertype_phase18_parity/diagnostics/<supertype_id>.tsv
results/validation_human/08_deg/fine_supertype_phase18_parity/fine_contrast_status.tsv
results/validation_human/08_deg/fine_supertype_phase18_parity/fine_result_index.tsv
```

Each tested result row contains at least:

```text
contrast_id, feature_index, source_symbol, ensembl_id, approved_symbol,
current_symbol_for_kda, is_core_mito_phase18, phase18_annotation_status,
logFC, logCPM, F, PValue, FDR, test_status, effect_direction,
mapping_status
```

**Principal broad outputs:**

```text
results/validation_human/08_deg/filters/broad/<broad_network>.filter.tsv.gz
results/validation_human/08_deg/broad_pooled_anchor/tested/<contrast_id>.tsv.gz
results/validation_human/08_deg/broad_pooled_anchor/diagnostics/<broad_network>.tsv
results/validation_human/08_deg/broad_pooled_anchor/contrast_status.tsv
results/validation_human/08_deg/broad_pooled_anchor/result_index.tsv
results/validation_human/08_deg/broad_stratified_support/tested/<contrast_id>.tsv.gz
results/validation_human/08_deg/broad_stratified_support/diagnostics/<broad_network>.tsv
results/validation_human/08_deg/broad_stratified_support/contrast_status.tsv
results/validation_human/08_deg/broad_stratified_support/result_index.tsv
```

The one broad filter table per network is shared by the pooled and stratified broad models, so its checksum must appear in both tier indexes.

**Directional handoff and release outputs:**

```text
results/validation_human/08_deg/query_handoff/fine_direction_manifest.tsv
results/validation_human/08_deg/query_handoff/fine_query_input_index.tsv
results/validation_human/08_deg/query_handoff/fine_direction_deg_summary.tsv
results/validation_human/08_deg/deg_summary.tsv
results/validation_human/08_deg/model_diagnostics.tsv.gz
results/validation_human/08_deg/deg_checks.tsv
results/validation_human/08_deg/artifacts.tsv
results/validation_human/08_deg/status.tsv
```

`fine_direction_deg_summary.tsv` contains one row per direction, not a duplicated structural grid. At minimum it records `fdr_significant_tested_feature_count`, `phase18_parity_tested_feature_count`, and `effect_gate_excluded_tested_feature_count`. These are pre-symbol-deduplication, pre-MitoCarta, and pre-network summaries; authoritative query sizes are added only by VH10.

When fit objects are retained, their frozen path pattern is `results/validation_human/08_deg/model_objects/<deg_tier>/<context_id>.edgeR.rds`. They are ignored by Git and represented in `artifacts.tsv` by path, byte size, SHA-256, and restore/archive location. Deterministic fit inputs remain the required replay path if objects are not retained.

The final direction manifest retains exactly 1,548 fine rows. Each row carries its source contrast status and one of:

- `ready_for_query_construction`;
- `source_contrast_not_estimable`; or
- `source_contrast_failed`.

A completed direction remains `ready_for_query_construction` even when either prespecified summary count is zero. It is not reclassified as a failed or non-estimable DEG contrast. VH10 later reconstructs authoritative mitochondrial membership and determines network-effective query eligibility independently for each query rule.

**Blocking gate:** every design-eligible contrast is either completed or has the recognized post-design reason `no_genes_after_filterByExpr`; no contrast is `failed`; every structural contrast/direction has a terminal record; all statistical, sign, FDR, mapping, checksum, and shard-replay checks pass; tier boundaries are intact; and `status.tsv` is `validated_complete`.

### Status semantics

These concepts must remain separate:

| Field/concept | Allowed meaning |
|---|---|
| `structural` | Slot exists in the complete prespecified grid |
| `support_pass` | Nucleus and donor-arm thresholds pass |
| `eligible` | Support, covariate, coefficient, rank, and residual-df gates pass |
| `not_estimable` | A prespecified scientific, design, or empty-tested-universe gate fails; exact reason required |
| `completed` | The eligible fit and all result validation completed |
| `failed` | Unexpected software or numerical failure; never interpreted biologically |
| `ready_for_query_construction` | Source DEG contrast completed, including zero qualifying genes |
| `runnable` | Reserved for VH10 after network induction and the effective-query-size gate |

Recommended non-estimability reasons include `disease_arm_below_5`, `no_profiles_above_nucleus_gate`, `incomplete_or_nonfinite_covariate`, `missing_required_coefficient`, `design_rank_deficient`, `nonpositive_residual_df`, and `no_genes_after_filterByExpr`.

### Phase dependency graph

```text
VH00 environment/config/storage
  ↓
VH01 input identity and schema
  ├──→ VH03 gene/reference harmonization
  ↓
VH02 donor cohort
  ↓
VH04 taxonomy and nucleus group codes ← VH03 feature gate
  ↓
VH05 streamed fine + direct-broad pseudobulk
  ↓
VH06 pseudobulk and profile validation
  ↓
VH07 complete tiered contrast/direction registry
  ↓
VH08 bounded edgeR fitting + validated DEG/query handoff
  ↓
Revised VH09/VH10 candidate freeze and KDA
```

## I. Validation Evidence Hierarchy

Evidence is interpreted from strongest technical prerequisite to later biological extension:

1. **Raw-input identity:** exact file, schema, observation, feature, and UMI-layer evidence.
2. **Cohort validity:** one row per donor, frozen phenotype/groups/covariates, and transparent exclusions.
3. **Taxonomy validity:** a complete fine inventory and one-to-one mapping into the seven network contexts.
4. **Count validity:** exhaustive integer checks, exact UMI conservation, and exact fine/direct-broad reconciliation.
5. **Design validity:** donor support, full rank, positive residual degrees of freedom, and prespecified coefficient vectors.
6. **DEG validity:** robust QL estimates, effect sizes, within-contrast FDR, tested/filtered separation, and replay checks.
7. **Within-cohort resolution support:** compatible broad-anchor and fine effects, interpreted as overlapping rather than independent evidence.
8. **Directional handoff:** frozen, signed, mapped pre-network query candidates with complete assessability accounting.
9. **Future external/network validation:** KDA rediscovery and ROSMAP overlap under the current Phase 18 selection core.

Structural slots, non-estimable contrasts, failed fits, filtered genes, and zero-query directions are different states. None may be collapsed into a biological null.

## J. Figure and Deliverable Plan

### Minimum QC figures

| Figure | Purpose | Required stratification |
|---|---|---|
| Cohort flow and arm-count panel | Show exclusions and the three globally feasible groups | Diagnosis, sex, APOE |
| Supertype support heatmap | Show which fine contrasts can be estimated | 129 supertypes × 6 groups, faceted by broad network |
| Profile QC distributions | Show nuclei, library size, detected genes, and mitochondrial fraction | Broad network and supertype |
| Pseudobulk reconciliation panel | Demonstrate exact fine-rollup/direct-broad agreement | Counts and checksum gates |
| Model QC panels | Assess composition, normalization, and dispersion | Completed supertype models |
| Analysis attrition waterfall | Separate structural, support-pass, eligible, completed, query-ready, and later runnable counts | Tier and direction |
| DEG-yield heatmap | Show FDR and FDR+effect counts | Supertype, group, direction |
| Fine/broad effect concordance | Compare related resolution estimates without claiming independence | Broad network and group |

MDS/PCA plots must be generated from pseudobulk expression and labeled by diagnosis, group, study, donor, and library size where legible. They are diagnostic; they may not trigger post hoc donor deletion without a documented amendment.

### Core table deliverables

- input and reference identity manifests;
- donor cohort and exclusion flow;
- complete supertype and safe-ID mapping;
- pseudobulk sample/shard manifests;
- fine and broad count-conservation checks;
- 774-row fine contrast manifest;
- 1,548-row fine direction manifest;
- design/rank/coefficient audit;
- per-context filter tables and per-contrast tested results;
- contrast/direction status tables;
- compact DEG and query summaries; and
- full code/config/input/output checksum provenance.

Figures should use colorblind-safe palettes and distinguish `not_estimable`, `failed`, zero-DEG, and completed-positive states visually rather than treating missing values as zero.

## K. Verified Reference Layer or Search Strategy

### Local design-history references

- The retired broad-cell DEG plan in repository history: reusable engineering and donor-model decisions only; it is not a live input or predecessor.
- [SEA-AD dataset contents](seaad_dataset_contents.md): raw object and metadata inventory expectations.
- [SEA-AD–ROSMAP cell-type mapping](seaad_rosmap_cell_type_mapping.md): taxonomy context and the warning against forced one-to-one fine-label matching.
- [VH09 Phase 18 candidate freeze](vh09_phase18_candidate_freeze.md): revised 47-unit ROSMAP discovery freeze with no SEA-AD candidate cross-product.
- [VH10 KDA rediscovery plan](vh10_seaad_kda_rediscovery_and_overlap.md): revised fine-supertype KDA and independent ROSMAP overlap contract.
- `docs/related_papers/yu_paper/code/mathys_DEG_analysis_subcluster_sex-cogdx_apoe-cogdx.Rmd` and `config/analysis_parameters.yml`: executable provenance for the inherited absolute 1.3-fold Yu/ROSMAP threshold.
- `config/phase18_key_driver_selection.yml`, `scripts/18_key_driver_selection.py`, `config/phase12_kda.yml`, `scripts/12_run_kda.R`, and `scripts/NetWeaver/fKDA.R`: downstream executable authorities and technical assets; they are read-only during DEG.

The deprecated plan and deleted historical outputs may supply expected replay values, but they are not valid predecessors. The clean pipeline must derive every analytical artifact again.

### Method and literature verification

Before a manuscript or public protocol is issued:

- verify edgeR, `filterByExpr`, TMM, and robust QL descriptions against the version-matched Bioconductor documentation and primary method papers;
- verify the SEA-AD dataset description against its authoritative release page/publication;
- record title, DOI or stable URL, software version, and access date; and
- avoid inserting an accession, download URL, cohort claim, or cell-label equivalence that has not been verified.

This plan does not require a new dataset search. If the raw files cannot be restored with the expected identity, work stops at VH00/VH01 until an authoritative replacement release is selected and the protocol is amended.

## L. Self-Critical Risk Review

| Risk | Consequence | Prespecified mitigation or decision rule |
|---|---|---|
| Fine stratification is sparse | Most structural slots may be non-estimable | Preserve all 774/1,548 slots; never lower support thresholds after seeing yield |
| Three groups are globally underpowered | `F_e2`, `M_e2`, and `M_e4` cannot reach 5 donors/arm | Record `disease_arm_below_5`; do not call them negative evidence |
| Small eligible groups yield unstable effects | Inflated uncertainty and few query genes | Report donor counts and confidence/effect information; retain broad anchor; use min-3 KDA only downstream with small-query flags |
| Full grouped design can be rank deficient | A nominally supported contrast cannot be fit | Mark `not_estimable`; do not drop covariates adaptively |
| Study may be confounded with phenotype/group | Coefficients can be non-identifiable or sensitive | Retain `study`, inspect design rank/distribution, and limit causal interpretation |
| SEA-AD and ROSMAP fine labels differ | Apparent fine-cell replication can be overstated | Compare through canonical broad networks; describe supertype recurrence without claiming one-to-one taxonomy |
| `No dementia` differs from ROSMAP NCI | Cross-cohort effect attenuation or mismatch | Preserve the phenotype name and describe the comparison explicitly |
| Gene symbols are ambiguous or duplicated | Query membership can change | Preserve feature identity, freeze mappings, use explicit any-pass set semantics, block identity/class conflicts |
| 774 within-contrast tests create many opportunities | Selective reporting and survivorship bias | Freeze all slots before DEG, show full attrition, and do not report only successful supertypes |
| Fine and broad tiers share donors and nuclei | Concordance is not independent replication | Treat broad results as anchors/support, never as independent evidence or pooled denominator |
| A monolithic count/result object exceeds practical memory | Crashes, copies, or corrupted recovery | Stream once, shard by supertype, fit bounded jobs, and use transactional checkpoints |
| Current `.gitignore` can admit bulky outputs | Multi-gigabyte artifacts can enter Git | Freeze explicit artifact classes and ignore rules in VH00 |
| Raw inputs are absent | Rebuild cannot start | Restore and authenticate them; do not reconstruct fine counts from broad derivatives |
| Historical expected counts are mistaken for inputs | A changed release can be forced to look identical | Recompute every count; stop and amend on unexplained mismatch |
| Up/down are mistaken for separate tests | DEG multiplicity and slot counts are misreported | State that 774 prespecified contrast slots yield 1,548 signed partitions everywhere |
| Empty directions prompt threshold relaxation | Post hoc bias | Keep zero-query directions valid and preserve frozen FDR/effect rules |
| FDR-only sensitivity is mistaken for the main analysis | Small effects can inflate queries and weaken Phase 18 comparability | Label both branches everywhere, run them independently, and never replace or tune the headline rule from the sensitivity result |
| Stratified estimates are described as interactions | Unsupported effect-modification claims | Require a separate formal interaction model and amendment for interaction inference |

### Definition of done

The rebuilt DEG endpoint is complete only when:

1. VH00–VH08 have `validated_complete` status from newly executed code;
2. all raw/reference identities and predecessor checksums are recorded;
3. the exact donor, taxonomy, observation, feature, and UMI conservation gates pass;
4. fine counts reconcile exactly with direct broad counts;
5. all 774 fine contrasts and all 1,548 fine directions are present exactly once;
6. broad pooled and broad stratified tiers are complete and separate;
7. every unavailable slot has a deterministic reason and no fabricated statistics;
8. every design-eligible contrast either completed successfully with validated BH FDR/coefficient direction or has the recognized empty-tested-universe status;
9. tested/filtered feature state is reconstructable for every completed contrast;
10. query handoff tables contain checksum-frozen DEG inputs only and claim neither authoritative query membership nor KDA eligibility;
11. compact release artifacts and bulky restore locations/checksums are both documented;
12. no raw input or unrelated ROSMAP result/code file was modified;
13. the inherited 1.3-fold provenance and the separate FDR-only sensitivity are frozen explicitly, without removing any tested DEG row; and
14. VH09/VH10 broad-only input assumptions are explicitly revised before downstream execution.

Until all 14 conditions pass, the endpoint remains incomplete regardless of how many DEG or KDA-ready signatures were observed.
