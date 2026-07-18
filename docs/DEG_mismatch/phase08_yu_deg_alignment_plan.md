# Plan to align Phase 08 DEG results with the Yu paper

## Objective

Revise Phase 08 so that its paper-replication branch performs the same 324 sex-by-APOE, AD-versus-NCI MAST comparisons reported in Yu et al. and validates the resulting DEG calls directly against Supplemental Table S1.

This is a replication change to the secondary single-nucleus MAST branch. Phase 07's donor-aware pseudobulk eligibility rules and its role as the project's primary inference remain unchanged.

## Reference artifacts

The external acceptance oracle is the `Table S1` sheet in:

- `docs/yu_paper/ALZ-22-e71463-s002.xlsx`
- SHA-256: `333898a4c1b89a484b56f51164bdc2fd553a43f7938fc1db2e19b1b8a7dc1ff0`

The supplemental figures are retained as supporting documentation:

- `docs/yu_paper/ALZ-22-e71463-s001.docx`
- SHA-256: `731176fd5947403bc72115be2c34fa55fc49dd7d697e7aadfa86ca67ac620aaf`

The DOCX contains the sex-marker quality-control figure and the scDesign3 power analysis, but no additional DEG filtering rule. Therefore, Table S1 and the paper's Methods define the DEG target.

## Baseline that this plan must improve

The detailed audit is in [phase08_vs_yu_degs.md](phase08_vs_yu_degs.md). The principal baseline measurements are:

| Measure | Current Phase 08 | Yu Table S1 comparison |
|---|---:|---:|
| Intended paper comparisons | 324 | 324 |
| Comparisons currently executed | 188 | — |
| Comparisons currently excluded by Phase 07 eligibility | 136 | — |
| DEG rows | 87,710 | 118,297 |
| Exact shared cell-type/contrast/gene calls | 78,773 | — |
| Recall across all Yu DEG rows | 66.59% | — |
| Precision across all current Phase 08 DEG rows | 89.81% | — |
| Recall when restricted to currently eligible comparisons | 87.19% | — |
| Shared-call log2FC direction agreement | 100% | — |
| Shared-call Pearson log2FC correlation | 0.9981 | — |

Of the 39,524 Yu calls absent from current Phase 08, 27,952 occur in comparisons that Phase 08 never ran. This makes the Phase 07 eligibility gate the first issue to remove. Remaining discrepancies must be investigated after all 324 comparisons are available.

Yu Table S1 contains one or more DEG rows for 277 comparisons. The other 47 comparisons have no reported DEGs; a completed comparison with zero qualifying genes is therefore a valid result, not a missing analysis.

## Target scientific behavior

### Population

For every fine cell type and each of the six paper strata, select all nuclei meeting all of these conditions:

1. `cohort_included == TRUE`;
2. the requested fine cell type;
3. the requested sex;
4. the requested APOE group (`e2`, `e33`, or `e4`);
5. diagnosis is `AD` or `NCI`.

Do not restrict these nuclei to donor-cell-type units that pass Phase 07's minimum-nuclei rule. Do not require at least five qualifying donors per diagnosis arm before running a Yu replication contrast. Those safeguards remain appropriate for primary pseudobulk inference but are not part of the paper's reported single-nucleus MAST analysis.

Record the observed cell and unique-donor counts for each diagnosis arm. A comparison should be marked `not_estimable`, with a machine-readable reason, only when the model truly cannot be fit—for example, an arm has zero cells or a required covariate is unavailable or rank-deficient. Low donor or cell counts alone should be reported as warnings rather than used as replication exclusion criteria.

### Model and DEG definition

For each of the 54 fine cell types and six strata (324 comparisons total), run the existing Seurat/MAST formulation with:

- comparison: AD versus NCI;
- assay/layer: normalized RNA `data` values;
- test: MAST;
- `logfc.threshold = 0`;
- `min.pct = 0.10`;
- latent variables: total RNA UMI count, age at death, and PMI;
- multiple-testing correction: Benjamini-Hochberg within each returned comparison;
- Yu DEG call: adjusted p-value `< 0.05` and `abs(avg_log2FC) > log2(1.3)`.

The Yu supplement's Bonferroni column may be emitted for diagnostic comparison, but it must not determine the paper-compatible DEG call. Do not change thresholds after viewing Table S1 in order to inflate overlap.

## Implementation work packages

### 1. Introduce a Yu-specific contrast manifest

Create a deterministic Phase 08 manifest containing exactly 54 fine cell types multiplied by six sex/APOE strata. Suggested artifact:

`results/minerva_production/08_mast_yu_replication_v2/yu_mast_contrast_manifest.tsv`

Each row should contain at least:

- source RDS and fine cell type;
- sex and APOE group;
- current internal contrast name;
- Yu contrast label (`F_e2x`, `F_e33x`, `F_e4x`, `M_e2x`, `M_e33x`, or `M_e4x`);
- AD/NCI cell and donor counts derived from the Phase 05 object's cohort-included metadata;
- modeling status and reason;
- a manifest schema version.

The manifest must not inherit the Phase 07 `primary_eligible` value. It may include Phase 07 eligibility as an informational column only.

### 2. Decouple Phase 08 modeling from Phase 07 eligibility

Modify `scripts/08_run_mast.R` so that:

1. the scientific input set is the Phase 05 normalized object, the frozen cohort/metadata provenance, the Phase 08 Yu manifest, and the Phase 08 parameters;
2. every estimable Yu manifest row is run, including rows Phase 07 labels ineligible;
3. cell selection comes directly from the normalized object's `cohort_included`, cell-type, sex, APOE, and diagnosis metadata;
4. counts in the Phase 08 output are recalculated from that selected population;
5. a completed model with no genes passing the Yu thresholds is written as a valid zero-DEG result;
6. Phase 07 pseudobulk results, if joined for method comparison, are treated as optional annotations and never control whether MAST executes.

Retain the existing comparison keys so downstream consumers can migrate without ambiguous remapping. Add an explicit field such as `analysis_population = yu_all_cohort_nuclei` to prevent old donor-screened and new replication results from being mixed.

### 3. Version schemas and resume validation

Change `scripts/run_one_rds.R` and Phase 08 status writers/readers to use a new schema, for example `mast_de_status_v2`.

The v2 resume validator should require hashes of the normalized RDS, code, parameters, cohort/metadata provenance, Yu manifest, and produced artifacts. It should no longer require Phase 07 pseudobulk sample or DE hashes for scientific validity. If optional pseudobulk annotations are included, hash and validate them separately as annotations.

This schema bump is necessary so existing v1 outputs cannot be incorrectly skipped as current after the population definition changes.

### 4. Preserve the current run and use a shadow output root

Do not overwrite the existing canonical Phase 08 artifacts during development. Preserve them as the donor-screened baseline and write the revised analysis to a versioned shadow directory, such as:

`results/minerva_production/08_mast_yu_replication_v2/`

Promote the revised branch only after the validation gates below pass. Promotion should be an explicit configuration or path change rather than an in-place rewrite of the baseline.

### 5. Add a reproducible Table S1 comparison utility

Add a read-only comparison script, suggested name `scripts/08_compare_yu_table_s1.R`, that:

1. verifies the supplemental XLSX checksum and sheet name;
2. maps the six Yu labels to the six internal contrasts explicitly;
3. normalizes gene and cell-type keys without silently collapsing duplicates;
4. compares exact `(cell type, contrast, gene symbol)` DEG keys;
5. checks direction and numerical agreement for log2FC, percentages, raw p-values, and BH-adjusted p-values;
6. assigns transparent mismatch reasons such as missing comparison, gene not returned by MAST, FDR failure, fold-change failure, both threshold failures, or current-only call;
7. writes machine-readable overall, by-contrast, by-cell-type, and row-level mismatch outputs.

Suggested outputs:

- `yu_table_s1_comparison_summary.tsv`;
- `yu_table_s1_comparison_by_contrast.tsv`;
- `yu_table_s1_comparison_by_cell_type.tsv`;
- `yu_table_s1_mismatches.tsv.gz`.

Table S1 is a validation target only. The script must not feed paper DEG labels back into model fitting or result filtering.

### 6. Run a small pilot before the full production rerun

Use the Vasculature source RDS as the pilot because it contains five fine cell types and therefore exercises all 30 sex/APOE comparisons while remaining smaller than the full dataset.

The pilot should establish that:

- all 30 manifest rows are attempted;
- Phase 07-ineligible rows are now modeled;
- output keys and status semantics are correct;
- completed zero-DEG contrasts are retained;
- resume validation detects a parameter, input, or manifest change;
- Table S1 comparison outputs are deterministic.

After the pilot passes, run the nine source RDS bundles. One job per source RDS may run in parallel, but two jobs must not write the same RDS-specific outputs concurrently.

### 7. Diagnose residual disagreement in a fixed order

Removing the eligibility gate is expected to recover most of the missing Yu calls, but it may not make all rows identical. Investigate residuals in this order:

1. confirm exact cell membership and AD/NCI labels for every comparison;
2. confirm the normalized `RNA` data layer is the same layer intended by the paper, and test whether re-running `LogNormalize` in Phase 05 changes the result;
3. confirm `nCount_RNA`, age, and PMI values, missing-data handling, capping, and scaling;
4. confirm the exact MAST feature universe after `min.pct = 0.10` and the universe used for BH adjustment;
5. confirm gene-symbol/Ensembl mapping and duplicated-symbol behavior;
6. record and, if available, reproduce the authors' exact Seurat and MAST versions.

The current environment uses Seurat 5.5.1 and MAST 1.28.0. The paper states Seurat v5 but does not provide enough version detail in the available material to guarantee bitwise-identical p-values. If exact reproduction remains impossible, report the remaining difference rather than introducing undocumented adjustments.

## Validation and acceptance gates

### Gate 1: structural coverage

- exactly 54 cell types and six contrast labels;
- exactly 324 unique cell-type/contrast status rows;
- no duplicate `(cell type, contrast, gene)` result keys;
- every row is either `validated_complete` or explicitly `not_estimable` with a reason;
- expected target: all 324 comparisons complete;
- zero-DEG results are distinguishable from failed or missing fits.

### Gate 2: scientific-method agreement

Use these as minimum method-equivalence targets, not as substitutes for the exact comparison:

- shared-call log2FC direction agreement at least 99.9%;
- shared-call Pearson log2FC correlation at least 0.995;
- median absolute shared-call log2FC difference at most 0.01;
- Table S1 DEG recall and precision each at least 95%;
- exact-call Jaccard index at least 90%.

These thresholds deliberately exceed the current eligible-scope baseline while allowing small software-version numerical differences.

### Gate 3: exact-reproduction target

The preferred final result is:

- exactly 118,297 Yu-compatible DEG keys;
- no Yu-only or Phase-08-only keys;
- identical directions;
- log2FC, percentage, p-value, and adjusted-p-value fields equal within predeclared numerical tolerances.

If Gate 2 passes but Gate 3 does not, the comparison report must identify the residual cause and quantify it before promotion. Do not describe the output as an exact reproduction unless Gate 3 passes.

## Tests to add

### Unit tests

- the six Yu-to-internal contrast mappings are one-to-one;
- the 54-by-6 manifest is complete and duplicate-free;
- cohort-included cell selection does not consult Phase 07 `primary_eligible`;
- diagnosis direction is consistently AD minus NCI;
- threshold boundary behavior uses strict `< 0.05` and strict `> log2(1.3)`;
- zero qualifying DEG rows still produce a completed status;
- mismatch-reason categories are mutually exclusive and exhaustive.

### Integration tests

- Vasculature produces 30 attempted comparisons;
- changing a Phase 08 input invalidates resume;
- changing only a Phase 07 result does not invalidate the Phase 08 scientific result when no optional annotation is embedded;
- the comparison utility reproduces fixed summary counts from a small fixture;
- an old v1 artifact cannot satisfy a v2 resume check.

### Regression checks

- Phase 07 pseudobulk results and eligibility manifests remain byte-for-byte unchanged;
- the original Phase 08 donor-screened output remains available as the audit baseline;
- the revised Phase 08 output contains provenance fields that make the two populations impossible to confuse.

## Downstream changes and reruns

After promotion, rerun or revalidate every consumer of Phase 08, particularly:

- Phase 09 mitochondrial pathway analysis;
- Phase 10 Yu-style similarity analysis;
- Phase 11 multiple-testing summaries;
- Phase 12 MAST-versus-pseudobulk sensitivity analysis;
- Phase 14 validation;
- Phase 15 and Yu-style figures.

Phase 10 needs special review. Its Yu-compatible branch should use the revised all-cohort Phase 08 results and should represent a tested but non-DEG state as zero rather than dropping the comparison dimension. The paper design implies 162 female-pair, 108 male-pair, and 108 cross-sex comparison dimensions; the current eligibility-gated branch has fewer. Phase 07 pseudobulk similarity outputs should remain a separate primary-analysis branch.

Update these documents when the code change is implemented:

- `docs/research_plans/mitochondria_sex_apoe_research_plan.md`;
- `docs/phase_08_explained.md`;
- `docs/DEG_mismatch/phase08_vs_yu_degs.md` with post-change measurements.

## Execution sequence

1. Freeze the current v1 output inventory and baseline comparison report.
2. Add the Yu-specific 324-row manifest and tests.
3. Refactor Phase 08 selection and dependency handling.
4. Add v2 schemas and resume validation.
5. Add the Table S1 comparison utility.
6. Run and validate the 30-comparison Vasculature pilot.
7. Resolve any population, normalization, covariate, feature-universe, or version discrepancy exposed by the pilot.
8. Run all nine source RDS bundles to the shadow output root.
9. Evaluate Gates 1 through 3 and publish the full mismatch report.
10. Promote the revised Phase 08 branch only after review, then rerun downstream phases.

## Completion criteria

This work is complete when the revised Phase 08 models all estimable Yu comparisons using all cohort-included nuclei, its output is independently compared with Table S1, the remaining differences are either eliminated or explicitly attributed, Phase 07 remains unchanged, and downstream artifacts have been regenerated from the promoted and provenance-versioned result.
