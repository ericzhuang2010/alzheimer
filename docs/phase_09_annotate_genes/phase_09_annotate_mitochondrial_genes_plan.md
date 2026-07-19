# Phase 09: Annotate Mitochondrial Genes

## Status and replacement decision

This document defines the new Phase 09. It follows the Yu-compatible Phase 08
MAST analysis and replaces the previously archived Phase 09 mitochondrial
fraction implementation.

The replacement is an annotation and data-integration phase:

- read the complete Phase 08 `*.yu_mast_*` v2 result bundles;
- join every assayed feature to frozen gene-identifier and mitochondrial
  references;
- preserve all Phase 08 statistics without refitting a model or recalculating
  a p-value;
- distinguish tested genes from genes filtered by `min.pct`, genes absent from
  an RDS, and contrasts that were not estimable;
- attach frozen gene identifiers, mitochondrial tiers, genome origin, and
  available MitoCarta localization metadata.

The new output directory is:

```text
results/<environment>/09_annotate_genes/
```

Do not reuse the archived `09_downstream/` directory or any archived Phase
09–15 script. Phases 00–08 remain unchanged. In particular, Phase 09 must not
modify a normalized RDS, rerun MAST, change the Yu DEG rule, or alter a Phase
08 artifact.

## High-level purpose

Phase 09 answers biological identity and testability questions for genes in the
Phase 08 design:

- Is the feature mapped to a stable Ensembl gene and an approved HGNC symbol?
- Is it a MitoCarta3.0 core mitochondrial protein gene?
- Is it one of the 13 mtDNA protein-coding genes or one of the 24 conventional
  mtDNA noncoding genes?
- Is the encoded protein assigned to a MitoCarta compartment?
- Was the feature measured in this RDS?
- For this fine-cell-type/contrast combination, was it tested, filtered by
  `min.pct`, significant, or not evaluable?

This phase does not construct pathway memberships or gene sets, test pathway
enrichment, compare sexes or APOE groups, prioritize candidates, or perform
another multiple-testing correction.

## Frozen scientific decisions

### Primary mitochondrial tiers

| Tier | Definition | Primary use |
|---|---|---|
| `core_mito_protein` | Canonical Human MitoCarta3.0 member | Primary mitochondrial gene analysis |
| `mtdna_noncoding` | GENCODE GRCh38 `chrM` gene with type `Mt_rRNA` or `Mt_tRNA` | Separate exploratory analysis |
| `mito_extended` | Member of a separately frozen, predeclared extended mitochondrial reference | Secondary/sensitivity analysis only |
| `non_mito` | None of the above, but only when the extended reference was enabled and evaluated | Transcriptome background |

If no extended reference has been frozen, Phase 09 must not silently call every
non-MitoCarta nuclear gene `non_mito`. It must instead set:

```text
extended_annotation_status = not_configured
mito_tier = not_core_or_mtdna_extended_not_evaluated
```

The core and mtDNA-noncoding tiers remain fully valid when the optional
extended tier is disabled.

### Stable identifier policy

The exact Seurat feature is the row identity used to join Phase 08 to Phase 03.
Stable identifiers enrich that row; they do not replace it.

Retain:

- `feature_id_original`: the exact assay feature from Phase 03/08;
- `ensembl_id_versioned` when the original feature is a versioned Ensembl ID;
- `ensembl_id_stable` with a version suffix removed;
- `symbol_original`;
- `symbol_hgnc_current`;
- `hgnc_id`;
- previous symbols and aliases;
- an explicit mapping status and mapping evidence.

Mapping precedence must be deterministic:

1. unique stable Ensembl ID match;
2. unique current HGNC-symbol match;
3. unique previous-symbol match;
4. unique alias match;
5. otherwise `ambiguous` or `unmapped`.

Never select one record from a one-to-many mapping by row order.

### DEG and direction policy

Phase 09 copies, rather than reconstructs, the Phase 08 fields:

- `logFC`;
- `pct_ad` and `pct_nci`;
- `p_value`;
- `p_val_adj_bonferroni`;
- `fdr_bh_within_contrast`;
- `paper_effect_threshold_log2`;
- `paper_deg`.

The direction remains AD minus NCI:

```text
paper_deg = TRUE and logFC > 0  -> significant_up
paper_deg = TRUE and logFC < 0  -> significant_down
paper_deg = FALSE               -> tested_not_significant
```

Phase 09 must validate that `paper_deg` agrees with the stored Phase 08 rule,
but it must not recompute BH over a mitochondrial subset.

## Inputs and dependencies

### Required Phase 03 inputs

| Input | Role |
|---|---|
| `results/<environment>/03_annotations/annotation_status.tsv` | Must be `validated_complete` and records the frozen reference hashes. |
| `results/<environment>/03_annotations/annotation_manifest.tsv` | Artifact paths, versions, bytes, and SHA-256 values. |
| `results/<environment>/03_annotations/tested_gene_universe.tsv` | One row per `(rds_id, feature)` with counts, GENCODE mapping, MitoCarta mapping, chromosome, gene type, and assay eligibility. |
| `results/<environment>/03_annotations/gencode_gene_annotation.tsv` | GENCODE 44 stable gene ID, symbol, chromosome, and biotype records. |
| `results/<environment>/03_annotations/gene_alias_mapping.tsv` | Existing MitoCarta canonical/synonym mappings and ambiguity flags. |
| `results/<environment>/03_annotations/mitocarta_measured_genes.tsv` | Complete 1,136-gene MitoCarta inventory by RDS, including measured/tested status. |
| `data/reference/gencode/gencode.v44.basic.annotation.gtf.gz` | Frozen GRCh38/GENCODE 44 source, checksum `3e52f82c63f8fd860bf632ccde10441c05751f4c342ad08c0a98e9e2700171a5`. |
| `data/reference/Human.MitoCarta3.0.xls` | Frozen MitoCarta3.0 inventory and localization source, checksum `e6ada0ae8dcd5447a5efb6f77c69a1c10b1ffa66521540a1e81b92c61e5505f2`. |

The current local Phase 03 universe contains 33,538 Vasculature features:
22,595 have a GENCODE mapping, 1,194 assay features map to MitoCarta aliases or
canonical symbols, and 27,516 have positive raw counts. The MitoCarta reference
contains 1,136 canonical genes; 1,134 are measured and 1,088 have positive raw
counts in the local Vasculature object.

### Required HGNC snapshot

The archived HGNC complete-set TSV has been downloaded and validated locally:

| Property | Frozen value |
|---|---|
| Local path | `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt` |
| HGNC archive release | `2026-06-05` monthly complete set |
| Source URL | `https://storage.googleapis.com/public-download-files/hgnc/archive/archive/monthly/tsv/hgnc_complete_set_2026-06-05.txt` |
| Size | 16,739,920 bytes |
| Data rows | 44,997, plus one header row |
| Columns | 54 |
| Unique HGNC IDs | 44,997 |
| SHA-256 | `f3051e4aa6fac82166e1c26638d0077a95b0f66ab62a03e18bb35eb613e40a90` |

The validated snapshot contains all required fields. Phase 09 must retain at
minimum:

- `hgnc_id`;
- approved `symbol`;
- `name`;
- `status`;
- `locus_type`;
- `prev_symbol`;
- `alias_symbol`;
- Ensembl gene ID.

Do not replace this file with the unversioned live HGNC complete set during
implementation or execution. Record the exact path, release date, source URL,
byte count, SHA-256 value, and required columns in `config/phase09_annotation.yml`
and the Phase 09 provenance outputs. HGNC documents archived complete sets on
the [official archive page](https://hgnc.genenames.org/download/archive/).

Because `data/` is ignored by Git, the snapshot must be transferred to the
same relative path on Minerva independently of code deployment and verified
against the frozen SHA-256 before Phase 09 runs.

The HGNC file is an identifier reference only. It must not change an exact
assay feature or a Phase 08 statistic.

### Frozen Reactome V97 extended-tier input

The extended tier has been selected, downloaded, and validated locally. It is
a prespecified four-pathway Reactome V97 panel containing 157 HGNC-normalized
genes: 77 MitoCarta core genes and 80 extended-only genes.

Require:

```text
data/reference/mitochondrial_extended/ReactomePathways.v97.gmt.zip
data/reference/mitochondrial_extended/ReactomePathways.v97.gmt
data/reference/mitochondrial_extended/mitochondrial_extended_gene_sets.gmt
data/reference/mitochondrial_extended/mitochondrial_extended_manifest.tsv
```

The derived GMT contains exactly:

- `R-HSA-1592230`: Mitochondrial biogenesis;
- `R-HSA-5205647`: Mitophagy;
- `R-HSA-9840373`: Cellular response to mitochondrial stress;
- `R-HSA-9841251`: Mitochondrial unfolded protein response.

Frozen reference checksums are:

| Artifact | SHA-256 |
|---|---|
| `ReactomePathways.v97.gmt.zip` | `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4` |
| `ReactomePathways.v97.gmt` | `89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b` |
| `mitochondrial_extended_gene_sets.gmt` | `f4d8b6c7a74894929028805e5e3cf81523968f8eecc380ac52b47038c5f9b847` |
| `mitochondrial_extended_manifest.tsv` | `8d77d6782872d6d19eb98a6297c92dda686dfba719199c6c0b6346d4127fb4ec` |

The manifest uses schema `mitochondrial_extended_manifest_v1` and has
`validation_status = validated_complete`. Phase 09 must configure
`extended_tier_enabled: true` and fail if any required file, stable ID,
count, or checksum differs. It must not silently fall back to a disabled tier.

### Required Phase 08 inputs

For every enabled RDS:

| File pattern | Requirement |
|---|---|
| `08_mast/<rds_id>.yu_mast_de.tsv.gz` | Complete returned-gene table using `yu_mast_de_results_v2`. |
| `08_mast/<rds_id>.yu_mast_contrast_manifest.tsv` | Six planned Yu strata per fine cell type. |
| `08_mast/<rds_id>.yu_mast_contrast_status.tsv` | Every planned contrast has a terminal status. |
| `08_mast/<rds_id>.yu_mast_de_status.tsv` | Must use `yu_mast_de_status_v2` and be `validated_complete`. |
| `08_mast/<rds_id>.yu_mast_de_artifacts.tsv` | Every declared file exists and matches bytes/checksum/status. |
| `results/<environment>/status/mast__<rds_id>.tsv` | Controller must have exit code zero and `validated_complete`. |

`not_estimable` contrast rows are allowed and retained. A Phase 08
`failed` contrast or failed task blocks Phase 09.

### Required configuration

Add a dedicated:

```text
config/phase09_annotation.yml
```

It must contain:

- output schema versions;
- GENCODE, MitoCarta, and HGNC paths and hashes;
- extended-tier enablement and paths;
- identifier mapping precedence;
- mtDNA chromosome and gene-type rules;
- allowed tested-status and mapping-status values;
- positive and negative controls.

Do not add these fields to `config/analysis_parameters.yml`. Phase 08 records
the checksum of that file, so unrelated Phase 09 additions would make a valid
Phase 08 resume appear stale.

Add the Phase 09 config path to `config/local_pilot.yml` and
`config/minerva_shared.yml`.

### Explicit non-inputs

Phase 09 must not read:

- a Phase 05 normalized RDS;
- Phase 06 descriptive tables;
- any Phase 07 pseudobulk or eligibility artifact;
- Yu supplemental tables;
- archived Phase 09–15 code or results;
- `results/figures/`.

The exact feature inventory comes from Phase 03, and every continuous DEG
statistic comes from Phase 08.

## Exact annotation construction

### Master feature/reference universe

Build the master universe separately for each RDS as the union of:

1. every `(rds_id, feature)` in `tested_gene_universe.tsv`;
2. every canonical MitoCarta gene not measured in that RDS;
3. all 37 conventional GENCODE `chrM` genes, including absent mtDNA rRNAs and
   tRNAs;
4. extended-tier reference genes when enabled.

Use a stable key such as:

```text
rds_id + feature_id_original + reference_only_id
```

Assay features and reference-only genes must remain distinguishable.
Many-to-one feature mappings must not be collapsed in the complete
transcriptome output.

### Mitochondrial classification

Apply this precedence:

1. MitoCarta canonical member -> `core_mito_protein`;
2. GENCODE `chrM` and `Mt_rRNA`/`Mt_tRNA` -> `mtdna_noncoding`;
3. frozen extended reference member -> `mito_extended`;
4. otherwise `non_mito`, but only when the extended reference was evaluated;
5. otherwise `not_core_or_mtdna_extended_not_evaluated`.

Record `genome_origin = mtDNA` only for a locus physically on `chrM`. Nuclear
MitoCarta genes must have `genome_origin = nuclear`.

Do not use an `MT-` prefix as the classification rule. In particular,
`MTRNR2L*` genes are nuclear and must not be conflated with `MT-RNR2`.

### Full contrast grid

For each RDS, cross its master feature/reference universe with only the
Phase 08 contrast-manifest rows belonging to that RDS. Join returned Phase 08
rows by:

```text
rds_id + contrast_id + gene/feature_id_original
```

Production is expected to be approximately 10.9 million grid rows with the
current 33,538-feature objects and 324 planned contrasts. The exact expected
row count must be calculated from the input manifests rather than hard-coded.

### Tested status and DEG state

Testing and identifier mapping are orthogonal. Keep `mapping_status` separate
from `tested_status` so an unresolved symbol can still be known to have been
tested by MAST.

Assign `tested_status` in this order:

| Status | Rule |
|---|---|
| `contrast_not_estimable` | Phase 08 contrast terminal status is `not_estimable`. |
| `not_in_expression_matrix` | Reference-only gene has no assay feature in that RDS. |
| `present_but_filtered_min_pct` | Contrast completed, feature is present, but no Phase 08 result row exists. |
| `tested_not_significant` | Phase 08 result exists and `paper_deg = FALSE`. |
| `significant_up` | `paper_deg = TRUE` and `logFC > 0`. |
| `significant_down` | `paper_deg = TRUE` and `logFC < 0`. |

Set the ternary `deg_state` to `+1`, `0`, or `-1` only for returned/tested
genes. It must be `NA` for filtered, unmeasured, and not-estimable rows. A
filtered gene must never be represented as a tested zero.

## Outputs and files created

Write all Phase 09 products under:

```text
results/<environment>/09_annotate_genes/
```

| File | Contents |
|---|---|
| `gene_annotation_master.tsv.gz` | One row per RDS assay feature plus reference-only mitochondrial records; original/current identifiers, mapping evidence, biotype, chromosome, tiers, origin, and available MitoCarta localization metadata. |
| `mitochondrial_reference_inventory.tsv` | Canonical MitoCarta and mtDNA reference genes by RDS with measured, mapped, and test-eligible states. |
| `deg_all_annotated.tsv.gz` | Complete feature/reference-by-contrast grid with Phase 08 statistics where tested and explicit testability states elsewhere. |
| `deg_mito_core.tsv.gz` | Derived subset of `deg_all_annotated` for `core_mito_protein`. |
| `mtdna_noncoding_results.tsv.gz` | Derived subset for the 22 mt-tRNAs and two mt-rRNAs, including absent/filtered states. |
| `unresolved_gene_mappings.tsv` | Ambiguous, one-to-many, many-to-one, and unmapped records for review. |
| `annotation_qc_summary.tsv` | Global/RDS mapping and mitochondrial coverage totals. |
| `annotation_qc_by_contrast.tsv` | Present, tested, filtered, significant-up/down, and non-estimable counts by RDS, cell type, and contrast. |
| `annotation_checks.tsv` | Structural, row-preservation, mapping, numerical, reference, and positive/negative-control checks. |
| `annotation_artifacts.tsv` | Paths, bytes, rows, SHA-256 values, schema versions, and validation status for every output. |
| `annotation_status.tsv` | One task summary with input/code/config hashes, row totals, and terminal status. |
| `mitochondrial_annotation_qc_report.md` | Human-readable summary generated from the QC tables; no hand-edited scientific conclusions. |

Recommended schemas:

```text
gene_annotation_master_v1
mitochondrial_reference_inventory_v1
annotated_yu_mast_results_v1
mitochondrial_annotation_checks_v1
mitochondrial_annotation_artifacts_v1
mitochondrial_annotation_status_v1
```

## Files changed or added before execution

| File | Required change |
|---|---|
| `scripts/09_annotate_mitochondrial_genes.R` | New global, read-only annotation task; validates Phase 03/08 inputs, constructs identifier mappings, mitochondrial tiers, localization fields, and test states, and writes atomic outputs. |
| `config/phase09_annotation.yml` | New Phase 09-only reference, mapping, tier, and schema configuration. |
| `config/local_pilot.yml` | Add the Phase 09 config path and allow `annotate_genes` after `mast`. |
| `config/minerva_shared.yml` | Add the same config path and task mode. |
| `scripts/run_pipeline.R` | Register global mode `annotate_genes`, script `scripts/09_annotate_mitochondrial_genes.R`, and output schema `mitochondrial_annotation_status_v1`. |
| `.gitignore` | Add the new production `09_annotate_genes/` exception if validated production results are intended to be tracked; do not reactivate archived `09_downstream/` paths. |
| `data/reference/hgnc/hgnc_complete_set_2026-06-05.txt` | Already downloaded and validated locally; existing frozen HGNC identifier input. Do not modify or redownload during implementation. |
| Phase 09 provenance outputs | Record the HGNC source URL, release date, path, bytes, SHA-256, required columns, and validation result. No separate sidecar manifest is required if these fields are recorded in the Phase 09 config, checks, status, and artifact tables. |
| `docs/minerva/cmd_to_run_09_annotate_genes.txt` | Optional operational command copy after implementation is validated locally. |

Do not modify:

- `scripts/08_run_mast.R`;
- `scripts/08_compare_yu_table_s1.R`;
- `scripts/run_one_rds.R`;
- `config/analysis_parameters.yml`;
- any Phase 00–08 result;
- anything under `archive/` or `results/figures/`.

No new R package is required if HGNC is stored as TSV and the implementation
uses the existing `data.table`, `readxl`, and `yaml` dependencies.

## Atomicity and resume behavior

The global task must write to a temporary staging directory under the target
output root. Publish final files only after all checks pass.

On rerun:

1. validate the existing `annotation_status.tsv` and artifact manifest;
2. compare script, Phase 09 config, HGNC, GENCODE, MitoCarta, Phase 03, Phase
   08, and RDS-manifest hashes;
3. skip only when every hash, byte count, schema, and validation state matches;
4. otherwise rebuild the complete output atomically.

No two Phase 09 instances may write the same environment output concurrently.

## Local pilot: Vasculature

### Input

The local pilot reads:

- one validated Phase 03 Vasculature annotation bundle;
- one validated Phase 08 Vasculature v2 bundle;
- 33,538 measured assay features;
- five fine cell types and 30 planned Yu contrasts;
- the frozen GENCODE, MitoCarta, and HGNC references.

The current Phase 08 pilot has 157,308 returned rows, 29 completed contrasts,
one not-estimable contrast, and 645 Yu-compatible DEGs.

### Output

One global `annotate_genes` task writes the complete local bundle under:

```text
results/local_pilot/09_annotate_genes/
```

The full grid is expected to contain approximately one million rows. Its exact
size is computed from the master universe and 30 contrast rows.

### Local preflight

Run from the repository root after the script/config/reference files listed
above have been implemented:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer

test -r data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
test -r data/reference/Human.MitoCarta3.0.xls
test -r data/reference/hgnc/hgnc_complete_set_2026-06-05.txt
printf '%s  %s\n' \
  'f3051e4aa6fac82166e1c26638d0077a95b0f66ab62a03e18bb35eb613e40a90' \
  'data/reference/hgnc/hgnc_complete_set_2026-06-05.txt' | \
  sha256sum --check --strict
test -r config/phase09_annotation.yml
test -r results/local_pilot/03_annotations/annotation_status.tsv
test -r results/local_pilot/03_annotations/tested_gene_universe.tsv
test -r results/local_pilot/08_mast/vasculature.yu_mast_de.tsv.gz
test -r results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv

Rscript -e '
phase03 <- read.delim(
  "results/local_pilot/03_annotations/annotation_status.tsv",
  check.names = FALSE)
phase08 <- read.delim(
  "results/local_pilot/08_mast/vasculature.yu_mast_de_status.tsv",
  check.names = FALSE)
contrasts <- read.delim(
  "results/local_pilot/08_mast/vasculature.yu_mast_contrast_status.tsv",
  check.names = FALSE)
stopifnot(
  phase03$validation_status == "validated_complete",
  phase08$schema_version == "yu_mast_de_status_v2",
  phase08$validation_status == "validated_complete",
  nrow(contrasts) == 30L,
  !any(contrasts$terminal_status == "failed")
)
'
```

### Local execute

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase annotate_genes \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase annotate_genes
```

Expected dry-run result: exactly one `global:annotate_genes` task,
`script_exists = TRUE`, and output schema
`mitochondrial_annotation_status_v1`. Do not pass `--rds-id` because Phase 09
is a global aggregation task.

### Local validation

```bash
Rscript -e '
library(data.table)
root <- "results/local_pilot/09_annotate_genes"
status <- fread(file.path(root, "annotation_status.tsv"))
checks <- fread(file.path(root, "annotation_checks.tsv"))
artifacts <- fread(file.path(root, "annotation_artifacts.tsv"))
master <- fread(file.path(root, "gene_annotation_master.tsv.gz"))
annotated <- fread(file.path(root, "deg_all_annotated.tsv.gz"))
phase08 <- fread(
  "results/local_pilot/08_mast/vasculature.yu_mast_de.tsv.gz")

stopifnot(
  status$schema_version == "mitochondrial_annotation_status_v1",
  status$validation_status == "validated_complete",
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete"),
  uniqueN(master[rds_id == "vasculature" & !reference_only, feature_id_original])
    == 33538L,
  nrow(annotated[tested_status %chin% c(
    "tested_not_significant", "significant_up", "significant_down")])
    == nrow(phase08),
  !anyDuplicated(annotated[, .(
    rds_id, contrast_id, feature_id_original, reference_only_id)]),
  all(annotated$tested_status %chin% c(
    "contrast_not_estimable", "not_in_expression_matrix",
    "present_but_filtered_min_pct", "tested_not_significant",
    "significant_up", "significant_down"))
)
'
```

The implementation should add checks for exact p-value/logFC preservation and
artifact SHA-256 values; the example above is a concise operator check.

## Minerva production

### Input

Production requires:

- one validated Phase 03 bundle covering all nine enabled RDS IDs;
- nine validated Phase 08 v2 bundles;
- 54 fine cell types and 324 contrast-status rows;
- zero failed Phase 08 contrasts;
- the identical frozen Phase 09 references and config promoted from local.

Do not start Phase 09 while any Phase 08 RDS job is still running.

### Output

One production bundle is written under:

```text
results/minerva_production/09_annotate_genes/
```

Expected scale with the current feature sets is approximately 10.9 million
annotated grid rows, plus the master, subset, QC, status, and artifact
tables.

### Minerva Phase 08 completeness preflight

Run on a compute node:

```bash
cd /sc/arion/work/zhuane01/alzheimer

Rscript -e '
status_root <- "results/minerva_production/08_mast"
scientific_files <- list.files(
  status_root,
  pattern = "[.]yu_mast_de_status[.]tsv$",
  full.names = TRUE)
contrast_files <- list.files(
  status_root,
  pattern = "[.]yu_mast_contrast_status[.]tsv$",
  full.names = TRUE)
artifact_files <- list.files(
  status_root,
  pattern = "[.]yu_mast_de_artifacts[.]tsv$",
  full.names = TRUE)

stopifnot(
  length(scientific_files) == 9L,
  length(contrast_files) == 9L,
  length(artifact_files) == 9L)

scientific <- do.call(rbind, lapply(
  scientific_files, read.delim, check.names = FALSE))
contrasts <- do.call(rbind, lapply(
  contrast_files, read.delim, check.names = FALSE))
artifacts <- do.call(rbind, lapply(
  artifact_files, read.delim, check.names = FALSE))

stopifnot(
  all(scientific$schema_version == "yu_mast_de_status_v2"),
  all(scientific$validation_status == "validated_complete"),
  nrow(contrasts) == 324L,
  length(unique(contrasts$cell_type_high_resolution)) == 54L,
  !any(contrasts$terminal_status == "failed"),
  all(contrasts$terminal_status %in% c(
    "validated_complete", "not_estimable")),
  all(artifacts$validation_status == "validated_complete")
)
cat("All Phase 08 production inputs are ready for Phase 09\n")
'
```

### Minerva environment preflight

Phase 09 is a table-integration task and does not fit MAST or edgeR. It does
not require the MKL `LD_PRELOAD` workaround.

```bash
Rscript -e '
stopifnot(
  getRversion() >= "4.3.3",
  requireNamespace("data.table", quietly = TRUE),
  requireNamespace("readxl", quietly = TRUE),
  requireNamespace("yaml", quietly = TRUE)
)
cat("Phase 09 packages are available\n")
'

test -r config/phase09_annotation.yml
test -r data/reference/Human.MitoCarta3.0.xls
test -r data/reference/gencode/gencode.v44.basic.annotation.gtf.gz
test -r data/reference/hgnc/hgnc_complete_set_2026-06-05.txt
printf '%s  %s\n' \
  'f3051e4aa6fac82166e1c26638d0077a95b0f66ab62a03e18bb35eb613e40a90' \
  'data/reference/hgnc/hgnc_complete_set_2026-06-05.txt' | \
  sha256sum --check --strict
```

If the HGNC file is not yet present on Minerva, copy this exact local snapshot
to the path above before running the preflight. The Phase 09 config preflight
implemented by the script must also verify the dated HGNC file, its required
columns, and every configured SHA-256 value.

### Minerva execute

Run one production instance on a compute node. A 192-GiB node is conservative
for constructing and sorting the approximately 10.9-million-row grid.

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase annotate_genes \
  --dry-run

Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase annotate_genes
```

Expected dry-run result: one `global:annotate_genes` task. Do not use
`RDS_ID` and do not launch one job per RDS; the production output is a single
cross-RDS table and concurrent writers are prohibited.

### Minerva production validation

```bash
Rscript -e '
library(data.table)
root <- "results/minerva_production/09_annotate_genes"
status <- fread(file.path(root, "annotation_status.tsv"))
checks <- fread(file.path(root, "annotation_checks.tsv"))
artifacts <- fread(file.path(root, "annotation_artifacts.tsv"))
master <- fread(file.path(root, "gene_annotation_master.tsv.gz"))
annotated <- fread(file.path(root, "deg_all_annotated.tsv.gz"))

stopifnot(
  status$schema_version == "mitochondrial_annotation_status_v1",
  status$validation_status == "validated_complete",
  status$rds_sets == 9L,
  status$fine_cell_types == 54L,
  status$planned_contrasts == 324L,
  all(checks$passed),
  all(artifacts$validation_status == "validated_complete"),
  uniqueN(master$rds_id) == 9L,
  !anyDuplicated(annotated[, .(
    rds_id, contrast_id, feature_id_original, reference_only_id)]),
  all(annotated$tested_status %chin% c(
    "contrast_not_estimable", "not_in_expression_matrix",
    "present_but_filtered_min_pct", "tested_not_significant",
    "significant_up", "significant_down"))
)
cat("Phase 09 Minerva production validated successfully\n")
'
```

## Required scientific and provenance checks

### Row and key checks

- every enabled RDS appears in Phase 03, Phase 08, and Phase 09;
- every Phase 08 result key joins exactly once;
- no Phase 08 returned row is lost or duplicated;
- the full grid row count equals the calculated universe-by-contrast count;
- `deg_mito_core.tsv.gz` and `mtdna_noncoding_results.tsv.gz` are exact
  subsets of `deg_all_annotated.tsv.gz`;
- reference-only records cannot collide with assay-feature keys.

### Numerical preservation checks

For every returned Phase 08 row, Phase 09 values must be identical for:

- `logFC`;
- `pct_ad` and `pct_nci`;
- `p_value`;
- `p_val_adj_bonferroni`;
- `fdr_bh_within_contrast`;
- `paper_effect_threshold_log2`;
- `paper_deg`;
- cell and donor counts.

No p-value or FDR column may be recalculated in this phase.

### Identifier mapping checks

Report by RDS:

- exact stable-Ensembl matches;
- exact current-symbol matches;
- previous-symbol matches;
- alias matches;
- ambiguous one-to-many mappings;
- many-to-one feature mappings;
- unmapped features;
- MitoCarta canonical versus synonym mappings.

All ambiguous mappings must appear in `unresolved_gene_mappings.tsv`.

### Mitochondrial coverage checks

Report by RDS and contrast:

- 1,136 canonical MitoCarta reference genes;
- measured and unmeasured core genes;
- present, filtered, and tested core genes;
- significant-up and significant-down core genes;
- all 13 mtDNA protein-coding genes;
- all 22 mt-tRNAs and two mt-rRNAs, including absent records;
- genome-origin counts;
- available MitoCarta localization coverage.

### Positive controls

At minimum:

| Gene | Required result |
|---|---|
| `MT-ND2` | `chrM`, mtDNA origin, and MitoCarta core |
| `NDUFS1` | nuclear origin and MitoCarta core |
| `SDHA` | nuclear origin and MitoCarta core |
| `COX5A` | nuclear origin and MitoCarta core |
| `ATP5F1A` | nuclear origin and MitoCarta core |
| `TFAM` | nuclear origin and MitoCarta core |
| `TOMM20` | nuclear origin, MitoCarta core, and outer-membrane localization when available in the inventory |
| `PINK1` | nuclear origin and MitoCarta core |

### Negative controls

- `MTRNR2L8` must not be mtDNA;
- a symbol beginning with `MT` is insufficient for MitoCarta membership;
- an Alzheimer/stress gene is not core mitochondrial without a MitoCarta
  mapping;
- an ambiguous alias must not be silently promoted to core.

## Acceptance criteria

### Structural gate

- one validated global task;
- one master row per assay feature plus explicit reference-only rows;
- complete 30-row local or 324-row production contrast coverage;
- one explicit tested status per grid row;
- unique keys and complete artifact manifest.

### Annotation gate

- all Phase 08 rows preserved exactly;
- all 1,136 MitoCarta genes represented for every RDS;
- all 37 conventional mtDNA genes represented for every RDS;
- all mapping ambiguities reported;
- positive and negative controls pass;
- no `MT-` prefix-only classification;
- extended tier is either checksummed and evaluated or explicitly
  `not_configured`.

### Provenance gate

- code, Phase 09 config, pipeline config, manifest, Phase 03, Phase 08,
  GENCODE, MitoCarta, HGNC, and optional extended-reference hashes recorded;
- every output has bytes, rows, SHA-256, schema, and validation state;
- temporary/partial outputs are not accepted;
- reruns skip only a complete hash-identical bundle.

## Downstream handoff

Downstream analyses should consume `deg_all_annotated.tsv.gz` together with
`tested_status` and the continuous Phase 08 statistics, not only `deg_state`.
They must never treat `present_but_filtered_min_pct`,
`not_in_expression_matrix`, or `contrast_not_estimable` as a tested zero.

Phase 09 does not provide pathway memberships or enrichment-ready gene sets.
Any later pathway-analysis phase must declare, freeze, parse, and validate its
own pathway reference inputs.

## Completion criteria

Phase 09 is complete when:

- the implementation reads only validated, checksummed Phase 03/08 and frozen
  reference inputs;
- the local Vasculature bundle passes all checks;
- Minerva covers nine RDS IDs, 54 fine cell types, and 324 planned contrasts;
- every Phase 08 row is preserved exactly once;
- feature mapping, mitochondrial tier, genome origin, available localization,
  tested status, and DEG state are explicit;
- all output hashes and schemas validate;
- Phases 00–08 and archived Phase 09–15 materials remain unchanged.

## Implementation checklist

### Freeze references

- [x] Select, download, and validate the dated HGNC `2026-06-05` archived
  complete-set TSV locally.
- [x] Record the HGNC URL, release, bytes, row/column counts, required columns,
  and SHA-256 in this plan.
- [ ] Add the frozen HGNC metadata and required-column validation to
  `config/phase09_annotation.yml` and the Phase 09 provenance outputs.
- [ ] Transfer the identical HGNC snapshot to Minerva and verify its SHA-256.
- [x] Freeze and validate the Reactome V97 four-pathway extended-tier gene
  sets and manifest locally before looking at annotated DEG results.
- [ ] Confirm the existing GENCODE and MitoCarta hashes.

### Implement

- [ ] Add `config/phase09_annotation.yml`.
- [ ] Add `scripts/09_annotate_mitochondrial_genes.R`.
- [ ] Build deterministic HGNC/Ensembl mapping with ambiguity reporting.
- [ ] Build the per-RDS feature/reference universe.
- [ ] Construct and join the complete contrast grid.
- [ ] Preserve Phase 08 continuous statistics exactly.
- [ ] Write all outputs atomically.
- [ ] Add status, checks, artifact hashes, and hash-aware resume.

### Integrate

- [ ] Register `annotate_genes` in `scripts/run_pipeline.R`.
- [ ] Enable it after `mast` in local and Minerva configs.
- [ ] Add the new production output rule to `.gitignore` if appropriate.
- [ ] Keep `analysis_parameters.yml` and Phase 08 files unchanged.

### Validate

- [ ] Run and validate the local Vasculature pilot.
- [ ] Review every ambiguous mapping.
- [ ] Confirm positive and negative controls.
- [ ] Promote identical code/config/reference hashes to Minerva.
- [ ] Run only after all nine Phase 08 tasks validate.
- [ ] Validate the complete production bundle before pathway analysis.
