# Phase 03 annotation results explained

## What Phase 03 does in the pipeline

Phase 03 freezes the biological annotation contract used by later phases. Its
question is not whether a gene differs between AD and NCI. Its question is:
**for every feature in every input RDS, what gene does it represent, does it
belong to a prespecified mitochondrial definition, is it present in that RDS,
and does it have any usable raw counts?**

Freezing matters because reference releases, gene symbols, aliases, and feature
sets can change. If each later phase reconstructed these definitions
independently, one phase could silently call a feature mitochondrial while
another did not. Phase 03 creates one versioned, checksummed, reviewable mapping
layer for all downstream work.

It is one global task, with stable task ID **global:annotations**. It combines
all enabled Phase 01 feature inventories and writes per-RDS mappings. It is not
one statistical task per broad or fine cell type.

### What it deliberately does not do

Phase 03 does not modify a Seurat object, normalize counts, remove nuclei or
donors, calculate per-nucleus mitochondrial percentages, compare AD with NCI,
fit a model, or calculate p-values and FDRs. It reads the feature summaries
created by Phase 01 instead of reopening the large RDS files.

It can tell that a feature exists and has nonzero counts somewhere in an RDS.
It cannot tell whether that feature is sufficiently expressed in a particular
fine cell type, donor set, or sex-APOE contrast. Those stricter decisions occur
later.

### Inputs

Phase 03 combines:

1. **GENCODE v44 basic hg38/GRCh38 GTF.** This supplies gene IDs, symbols,
   chromosomes, and biotypes. Its project-relative path is
   **data/reference/gencode/gencode.v44.basic.annotation.gtf.gz**.
2. **Human MitoCarta 3.0.** The spreadsheet
   **data/reference/Human.MitoCarta3.0.xls** supplies 1,136 canonical
   mitochondrial genes, synonyms, descriptions, sub-mitochondrial locations,
   pathway assignments, pathway hierarchy, and pathway members.
3. **The enabled RDS manifest.** This defines the objects in scope and the
   stable **rds_id** for each object.
4. **Phase 01 feature inventories.** Each compressed feature file supplies the
   original feature name, RDS-wide total raw counts, and number of nuclei in
   which that feature was detected.
5. **The shared scientific configuration.** This declares reference versions,
   expected SHA-256 values, spreadsheet sheets, and the 13 prespecified
   mtDNA-encoded protein genes.
6. **The execution configuration.** This contributes provenance such as run ID,
   execution stage, and backend; it does not change scientific matching rules.

Local pilot and Minerva production use the same references and mapping code.
Minerva nevertheless needs its own Phase 03 run to create mappings for all nine
production feature inventories.

### Detailed processing sequence

#### 1. Verify immutable references

Before mapping, the script runs an integrity test on the compressed GENCODE
file, calculates the SHA-256 of both external references, and requires those
hashes to equal the configured values. It also verifies that the expected
MitoCarta columns and sheets exist.

A checksum mismatch is a hard failure. The task will not silently continue with
a different GENCODE or MitoCarta release.

#### 2. Parse GENCODE at gene level

A GTF contains genes, transcripts, exons, and other records. Phase 03 reads the
compressed GTF in chunks and retains only records whose feature type is
**gene**. It extracts:

- chromosome or contig;
- Ensembl **gene_id**, after removing a trailing version suffix;
- **gene_name**;
- **gene_type**.

It removes duplicate records, sorts the table, and flags gene symbols occurring
in more than one gene record. The resulting compact lookup prevents later
phases from repeatedly parsing the full GTF.

#### 3. Read the MitoCarta inventory

The MitoCarta **Symbol** column is treated as the canonical mitochondrial gene
symbol. Phase 03 retains the Human Gene ID, description, synonyms,
sub-mitochondrial localization, and pathway annotation for every one of the
1,136 inventory genes.

It verifies that canonical symbols are unique. This is a reference-level check,
not an expression check.

#### 4. Build and audit the alias dictionary

For every canonical MitoCarta symbol, the script creates rows for the canonical
name and its supplied synonyms. It counts how many canonical targets each alias
has.

Matching rules are conservative:

- an exact canonical-symbol match takes priority;
- a synonym is used only if it maps to exactly one canonical symbol;
- an alias mapping to multiple canonical symbols is flagged as ambiguous and is
  not used automatically;
- unmatched features remain explicit instead of being silently dropped.

The alias output also records in how many RDS inventories an alias is present
and in how many it was selected as the actual mapping.

#### 5. Read every Phase 01 feature inventory

The script maps each **.features.tsv.gz** filename to exactly one enabled
manifest row. It requires at least **feature**, **total_raw_counts**, and
**nuclei_detected**.

It adds the stable RDS ID and source file, then stacks all inventories. The same
feature in nine RDS files therefore has nine rows. This preserves the fact that
a gene can be present or expressed in one object but absent or all-zero in
another.

The inspected Minerva output contains 33,538 rows from each of nine objects:
9 x 33,538 = 301,842 per-RDS feature rows.

#### 6. Map each feature to GENCODE

Mapping proceeds in priority order:

1. exact match of the RDS feature to GENCODE **gene_name**;
2. if no symbol match exists, match as an Ensembl gene ID after removing an
   optional version suffix;
3. otherwise mark the feature **unmatched**.

A successful row receives GENCODE gene ID, name, chromosome, biotype, and match
method.

One implementation detail matters: the current symbol lookup retains the first
GENCODE record for a repeated gene name. Repeated names are flagged in
**gencode_gene_annotation.tsv**, but all repeated names are not excluded from
mapping. Consult the duplicate flag when a repeated symbol's exact genomic
identity matters.

#### 7. Map each feature to MitoCarta

MitoCarta mapping is separate from GENCODE mapping. Each feature is first
compared with the 1,136 canonical symbols. Only if no canonical match exists is
it compared with the unambiguous alias dictionary.

The feature receives a canonical MitoCarta symbol, a match type of
**canonical**, **unique_synonym**, or **unmatched**, and an **is_mitocarta**
flag. Ambiguous aliases are not guessed.

#### 8. Identify the 13 mtDNA protein-coding genes

The 13-gene list is prespecified in the analysis configuration. Phase 03 makes
the complete RDS-by-13 grid, so every expected gene has a row for every RDS.
If a gene is absent, the row remains present with **measured = FALSE**.

GENCODE chromosome and gene ID are carried into the table. Validation can
therefore confirm both that all 13 features are measured and that they have
chromosome annotations.

#### 9. Define measured and preliminary test eligibility

These labels are intentionally narrow:

- **measured** means a matching feature exists in that RDS;
- **test_eligible** means its RDS-wide total raw count is finite and greater
  than zero;
- an ineligible feature receives
  **zero_or_nonfinite_raw_counts** as its reason.

This is only a broad candidate universe. A Phase 03 **tested** value does not
mean the gene was tested in every fine cell type or contrast. Phase 07 applies
edgeR's donor- and design-aware expression filtering, while MAST applies its
own comparison-specific requirements.

#### 10. Build the RDS-by-MitoCarta coverage grid

The script constructs every combination of RDS ID and all 1,136 canonical
MitoCarta genes, then joins observed feature mappings to it. This ensures that
unmatched genes are represented explicitly.

If multiple features map to one canonical gene, their feature names and match
types are retained in semicolon-separated form. A gene is measured if any
feature maps to it and preliminary-tested if any mapped feature has positive,
finite raw counts.

This design supports statements such as “1,134 of 1,136 MitoCarta genes were
measured” without confusing absence from the reference with absence from the
RDS.

#### 11. Build MitoCarta pathway artifacts

The task is intended to create:

- a TSV with pathway, hierarchy, member genes, and gene count;
- a standards-compatible GMT representation of the same pathways.

The inspected implementation has a known defect here: it applies a
pipe-delimited synonym parser to the comma-delimited MitoCarta pathway gene
field. Consequently, current **gene_count** values are wrong and the GMT is not
standards-compliant. This does not affect the GENCODE mapping or the 1,136-gene
MitoCarta inventory, but the pathway artifacts should be fixed and regenerated
before external reuse. The file-specific sections below describe the impact.

#### 12. Write files atomically

Each table is written to a process-specific temporary file and renamed to its
final path only after the write completes. This reduces the risk of a partial
final file after an interruption.

Phase 03 is a relatively small global task and has no per-RDS resume mode. If it
fails, the global annotation task is rerun.

#### 13. Validate and record provenance

The validation table checks reference integrity, checksums, nonempty GENCODE
parsing, MitoCarta inventory size and symbol uniqueness, expected pathway row
count, the expected feature inventories, all 13 mtDNA genes and chromosome
annotations, and a nonempty tested-gene universe.

The artifact manifest records path, bytes, SHA-256, row count, version, source
URL where applicable, and validation status. The task status records scientific
script and configuration checksums, reference and RDS-manifest checksums,
execution labels, Git revision, memory, elapsed time, and final status.

The existing checks validate broad record counts but not the number of genes in
each pathway or the GMT field structure. That gap explains why the pathway
defect can coexist with a **validated_complete** Phase 03 status.

### Downstream use

Phase 03 prevents later phases from redefining mitochondrial membership:

- Phase 04 uses **mtDNA_protein_genes.tsv** and
  **mitocarta_measured_genes.tsv** for mitochondrial QC calculations.
- Phase 06 uses those tables for descriptive mitochondrial summaries.
- Phase 09 uses **mitocarta_pathways.tsv** and
  **tested_gene_universe.tsv** for pathway analysis and its tested background.
- Phase 10 uses **tested_gene_universe.tsv** for cross-method similarity work.
- Phase 11 uses **tested_gene_universe.tsv** when defining and auditing
  multiple-testing families.

The result is an explicit contract connecting each original RDS feature to its
GENCODE identity, MitoCarta identity, mtDNA status, measured status, and broad
eligibility status, with enough provenance to reproduce and audit the mapping.

Phase 03 builds the annotation layer used by later phases. It connects the
features found in each Seurat object to GENCODE genes, the Human MitoCarta 3.0
inventory, mitochondrial pathways, and the 13 protein-coding genes in the
mitochondrial genome. It also records provenance and validation information.

The files described below are in:

```text
results/minerva_production/03_annotations/
```

The row counts in this document describe the inspected Minerva production
outputs. They can change if the inputs or annotation-building code are changed
and Phase 03 is rerun.

## `gencode_gene_annotation.tsv`

This is a compact gene-level table parsed from the GENCODE v44 basic hg38 GTF.
There is one row per GENCODE gene record: 62,700 rows in the inspected output.

| Column | Meaning |
| --- | --- |
| `chromosome` | Chromosome or contig assigned by GENCODE. |
| `gene_id` | Stable GENCODE/Ensembl gene identifier. |
| `gene_name` | Human-readable gene symbol from the GTF. |
| `gene_type` | GENCODE gene biotype, such as `protein_coding`, `lncRNA`, or `processed_pseudogene`. |
| `duplicate_gene_name` | `TRUE` when the same gene symbol occurs in more than one GENCODE gene record; such symbols cannot always be mapped to one gene ID unambiguously. |

In the inspected file, 60,885 rows have a unique gene name and 1,815 have a
duplicated name. The most common gene types are 20,046 protein-coding genes,
18,866 lncRNAs, and 10,146 processed pseudogenes.

## `gene_alias_mapping.tsv`

This table documents how MitoCarta canonical symbols and synonyms were mapped
to feature names in the nine Seurat objects. There is one row per
alias-to-canonical-symbol pair: 4,608 rows in the inspected output.

| Column | Meaning |
| --- | --- |
| `alias` | Candidate feature name used for matching. It may be the canonical MitoCarta symbol or one of its synonyms. |
| `canonical_symbol` | Canonical Human MitoCarta 3.0 gene symbol represented by the alias. |
| `alias_type` | Whether the alias is a `canonical` symbol or a `synonym`. |
| `canonical_targets` | Number of different canonical MitoCarta symbols associated with this alias. A value greater than one makes the alias ambiguous. |
| `duplicate_alias` | `TRUE` if the alias maps to more than one canonical symbol. Ambiguous aliases are not safe for automatic synonym matching. |
| `feature_present_rds` | Number of RDS feature inventories containing this exact alias. |
| `selected_mapping_rds` | Number of RDS files in which this alias was actually selected as the mapping to the canonical gene. |

The file contains 1,136 canonical-symbol rows and 3,472 synonym rows. There are
4,469 unambiguous rows and 139 ambiguous rows. In these data, the nine RDS
objects have the same feature vocabulary, so `feature_present_rds` is normally
zero or nine. Seventy-seven unique synonyms were selected in all nine objects.

## `mitocarta_measured_genes.tsv`

This is the per-RDS MitoCarta coverage table. Each row represents one of the
1,136 Human MitoCarta 3.0 genes in one RDS file. Nine RDS files multiplied by
1,136 genes gives 10,224 rows.

| Column | Meaning |
| --- | --- |
| `rds_id` | Stable identifier of the source Seurat object. |
| `canonical_symbol` | Canonical Human MitoCarta 3.0 gene symbol. |
| `human_gene_id` | Human gene identifier supplied by MitoCarta. |
| `description` | MitoCarta gene description. |
| `synonyms` | Alternative gene symbols supplied by MitoCarta. |
| `sub_mito_localization` | Reported sub-mitochondrial localization, when available. |
| `mito_pathways` | MitoCarta pathway assignments for the gene. |
| `duplicate_canonical_symbol` | Whether the canonical symbol is duplicated in the source MitoCarta inventory. |
| `mapped_feature` | Feature name in this RDS selected to represent the MitoCarta gene; missing if no safe match was found. |
| `match_type` | How `mapped_feature` was obtained: canonical-symbol match, unique-synonym match, both, or unmatched. |
| `tested` | Whether the mapped feature has positive total raw counts across this RDS and is eligible for later testing at this preliminary stage. This does not mean every later contrast tested the gene. |
| `measured` | Whether a matching feature exists in the RDS feature inventory. |

Each inspected RDS has 1,134 measured MitoCarta genes. The number marked
`tested` ranges from 1,088 to 1,104. `GPX1` and `RP11_469A15.2` were unmatched
in all nine objects. Across all RDS-gene rows, the mapping categories are 9,549
canonical, 504 canonical plus unique synonym, 153 unique synonym, and 18
unmatched.

## `mtDNA_protein_genes.tsv`

This table tracks the 13 protein-coding genes encoded by mitochondrial DNA in
each RDS file. It has 9 x 13 = 117 rows. All 13 genes are measured and have
positive total raw counts in every inspected RDS.

| Column | Meaning |
| --- | --- |
| `rds_id` | Source Seurat-object identifier. |
| `feature` | mtDNA protein-coding gene symbol. |
| `measured` | Whether that feature is present in the object. |
| `tested` | Whether it has positive total raw counts and passes this Phase 03 preliminary eligibility check. |
| `total_raw_counts` | Sum of raw counts for the gene across all nuclei in the RDS. |
| `nuclei_detected` | Number of nuclei with a nonzero raw count for the gene. This is a per-gene count and must not be summed across genes to estimate unique nuclei. |
| `chromosome` | GENCODE chromosome assignment, expected to be mitochondrial. |
| `gencode_gene_id` | Matching GENCODE gene identifier. |

The 13 genes are `MT-ATP6`, `MT-ATP8`, `MT-CO1`, `MT-CO2`, `MT-CO3`,
`MT-CYB`, `MT-ND1`, `MT-ND2`, `MT-ND3`, `MT-ND4`, `MT-ND4L`, `MT-ND5`, and
`MT-ND6`.

## `tested_gene_universe.tsv`

This is the full per-RDS feature universe used to define which genes can enter
later statistical analyses. There is one row for every original feature in
every RDS: 33,538 features per object and 301,842 rows across nine objects.

| Column | Meaning |
| --- | --- |
| `feature_index` | Original row position of the feature in the RDS assay. |
| `feature` | Original feature name. |
| `total_raw_counts` | Total raw counts for the feature across the RDS. |
| `nuclei_detected` | Number of nuclei with a nonzero count for the feature. |
| `is_mtdna_protein_gene` | Whether the feature is one of the 13 mtDNA protein-coding genes. |
| `rds_id` | Source Seurat-object identifier. |
| `source_feature_file` | Phase 01 feature-inventory file used to create the row. |
| `gencode_gene_id` | Matched GENCODE gene ID, if available and unambiguous. |
| `gencode_gene_name` | Matched GENCODE symbol. |
| `chromosome` | Matched GENCODE chromosome or contig. |
| `gene_type` | Matched GENCODE gene biotype. |
| `gencode_match_type` | How the feature was matched to GENCODE, or `unmatched`. |
| `mitocarta_symbol` | Canonical MitoCarta symbol when the feature maps safely to a MitoCarta gene. |
| `mitocarta_match_type` | Canonical, unique-synonym, or unmatched MitoCarta matching method. |
| `is_mitocarta` | Whether the feature maps to the MitoCarta inventory. |
| `test_eligible` | Whether the feature has positive, finite total raw counts across the RDS. This is an initial universe check; Phase 07 applies additional expression filtering such as edgeR `filterByExpr`. |
| `test_exclusion_reason` | Reason a feature is not initially eligible, such as zero or nonfinite total raw counts. |

The inspected table has 269,871 initially eligible rows and 31,971 excluded for
zero or nonfinite total raw counts. GENCODE matching found 203,355 symbol
matches and 98,487 unmatched rows. MitoCarta matching found 10,053 canonical
matches, 693 unique-synonym matches, and 291,096 unmatched rows.

## `mitocarta_pathways.tsv`

This table is intended to provide one row per MitoCarta pathway.

| Column | Meaning |
| --- | --- |
| `pathway` | MitoCarta pathway name. |
| `hierarchy` | Parent category or hierarchy description. |
| `genes` | Genes assigned to the pathway. |
| `gene_count` | Intended number of genes in `genes`. |

Important current limitation: the inspected Phase 03 builder parsed the source
MitoCarta `Genes` field as if it were pipe-delimited, but that field is
comma-delimited. Consequently, 149 valid pathway rows incorrectly report
`gene_count = 1`, even though the actual pathway sizes range from 1 to 461. The
source spreadsheet also contributed five blank trailing rows, which appear as
missing pathway/hierarchy rows with `gene_count = 0`.

For reference, parsing the source field correctly gives 461 genes for
`Metabolism`, 231 for `Mitochondrial central dogma`, 169 for `OXPHOS`, and 155
for `Translation`.

Phase 09 currently splits the `genes` field on commas and discards blank rows,
so its pathway memberships are likely correct despite the incorrect Phase 03
`gene_count` values. The Phase 03 table should nevertheless be corrected before
it is treated as a finalized general-purpose annotation artifact.

## `mitocarta_pathways.gmt`

This is intended to be the same MitoCarta pathway collection in standard GMT
format. A valid GMT row has:

```text
pathway_name<TAB>description<TAB>gene_1<TAB>gene_2<TAB>...
```

The current file is not standards-compliant: each row stores the entire
comma-separated gene list in one third field rather than one tab-delimited
field per gene. It also contains five trailing `NA<TAB>NA` lines from the blank
spreadsheet rows. Do not use this GMT file in external pathway tools until the
Phase 03 export is fixed and regenerated. The pipeline's Phase 09 code reads
`mitocarta_pathways.tsv`, not this GMT file.

## `annotation_checks.tsv`

This is a machine-readable validation checklist. Each row is one Phase 03
check; there were 11 checks in the inspected output.

| Column | Meaning |
| --- | --- |
| `schema_version` | Version of the validation-table schema. |
| `check` | Stable name of the validation rule. |
| `passed` | Whether the observed value satisfied the rule. |
| `observed` | Value calculated from the current inputs or outputs. |
| `expected` | Required value or condition. |

The checks cover GENCODE gzip integrity, source checksums and gene records;
MitoCarta checksum, 1,136-gene inventory, unique symbols, and 154 source
pathway spreadsheet rows; all nine RDS feature inventories; all 13 mtDNA genes
and their chromosomes per RDS; and a nonempty tested-gene universe.

All current checks passed. However, the checks count source pathway rows but do
not validate the number of genes in each pathway or the structure of the GMT
file. That is why the pathway-export problem was not detected by validation.

## `annotation_manifest.tsv`

This is the provenance and integrity manifest for Phase 03 inputs and derived
artifacts. Each row identifies one tracked file.

| Column | Meaning |
| --- | --- |
| `schema_version` | Manifest schema version. |
| `artifact` | Stable name of the source or derived artifact. |
| `path` | Project-relative file path. |
| `bytes` | File size in bytes. |
| `sha256` | SHA-256 checksum used to detect changes. |
| `records` | Number of data records in the artifact. |
| `source_version` | External annotation version or pipeline analysis version. |
| `source_url` | Original source URL when the artifact came from an external resource. |
| `validation_status` | Whether the artifact passed its declared validation. |

The first two records describe the external GENCODE and MitoCarta sources. The
remaining records describe files derived by analysis version `0.1.0`. The
manifest does not list itself or `annotation_status.tsv`.

## `annotation_status.tsv`

This is the one-row completion record for the global Phase 03 annotation task.
It supports reproducibility, task tracking, and later promotion validation.

| Column | Meaning |
| --- | --- |
| `schema_version` | Status-record schema version. |
| `execution_phase` | Execution-stage label recorded when this artifact was produced. |
| `backend` | Execution backend, such as direct execution. |
| `run_id` | Identifier for this pipeline invocation. |
| `stable_task_id` | Stable task key; for this phase it is `global:annotations`. |
| `task_mode` | Pipeline mode, `annotations`. |
| `scientific_script` | Script responsible for the scientific output. |
| `scientific_code_bundle_sha256` | Checksum representing the scientific code bundle. |
| `scientific_config_sha256` | Checksum of the recorded scientific configuration. |
| `manifest_sha256` | Checksum of the input RDS manifest, not of `annotation_manifest.tsv`. |
| `gencode_sha256` | Checksum of the GENCODE source file. |
| `mitocarta_sha256` | Checksum of the MitoCarta source file. |
| `rds_feature_sets` | Number of RDS feature inventories processed. |
| `tested_gene_rows` | Number of rows written to the full tested-gene universe. |
| `mitocarta_rows` | Number of canonical genes in the source MitoCarta inventory. |
| `pathway_rows` | Number of source spreadsheet pathway rows counted, including the five blank trailing rows in the inspected source. |
| `peak_ram_gib` | Peak memory use recorded for the task. |
| `elapsed_seconds` | Wall-clock run time. |
| `validation_status` | Overall task result. |
| `failed_checks` | Semicolon-separated failed validation rules, empty when none failed. |
| `git_revision` | Git revision associated with the run. |
| `timestamp_utc` | Completion time in UTC. |

The inspected task processed nine feature sets, wrote 301,842 tested-universe
rows, recorded 1,136 MitoCarta genes and 154 source pathway spreadsheet rows,
used approximately 1.27 GiB peak RAM, ran for approximately 26 seconds, and was
marked `validated_complete`.

## Interpretation summary

The GENCODE annotation, per-feature tested universe, MitoCarta gene mapping,
and mtDNA gene tables are internally coherent. The main actionable problem is
the pathway export: `mitocarta_pathways.tsv` has incorrect `gene_count` values
and retained blank rows, while `mitocarta_pathways.gmt` is malformed. Those two
artifacts and their validation checks should be corrected and regenerated
before Phase 03 is considered completely finalized for external reuse.
