# Phase 01 audit explained

## Purpose of Phase 01

Phase 01 is a read-only structural and scientific-integrity audit of every
Seurat RDS input. It establishes what is actually inside each object before any
cohort filtering, mitochondrial QC, normalization, pseudobulk aggregation, or
differential-expression analysis is attempted.

The phase answers five foundational questions:

1. Can the serialized object be loaded with the promoted R/Seurat environment?
2. Does it contain a usable sparse raw-count matrix with valid feature and cell
   identifiers?
3. Are donor and fine-cell-type annotations complete and consistent with the
   independent master cell-metadata table?
4. Are the prespecified 13 mtDNA protein-coding genes present?
5. What feature-, cell-type-, and donor-level inventories should later phases
   use without reopening every large RDS merely to rediscover its structure?

This is an audit, not a transformation. The script never saves the Seurat
object and does not change its assays, layers, metadata, reductions, graphs, or
commands. All files written by Phase 01 are summaries or provenance records.

The production artifacts described here are under:

```text
results/minerva_production/01_audit/
```

## Scope and unit of work

Phase 01 has RDS scope. The controller creates one stable task for each enabled
manifest row:

```text
audit:astrocytes
audit:excitatory_set1
audit:excitatory_set2
audit:excitatory_set3
audit:immune
audit:inhibitory
audit:opcs
audit:oligodendrocytes
audit:vasculature
```

Each task runs in a separate R process and reads one Seurat object. This limits
the lifetime of the memory used for a large object and prevents one failed RDS
from corrupting another object's output. The Minerva execution configuration
has `fail_fast: false`, so the controller can record one failed object and
continue auditing the remaining objects.

The filenames use the source RDS basename, whereas task IDs use the shorter
manifest `rds_id`. For example:

```text
source RDS:       data/processed/Excitatory_neurons_set1.rds
rds_id:           excitatory_set1
stable task ID:   audit:excitatory_set1
output prefix:    Excitatory_neurons_set1
```

## Inputs

Each audit task uses the following inputs.

### Source Seurat RDS

The manifest identifies the RDS to read. The object must inherit from the
Seurat class and contain the configured assay, currently `RNA`.

### Minerva RDS manifest

`config/minerva_rds_manifest.tsv` supplies:

- the stable manifest row and `rds_id`;
- the project-relative RDS path;
- expected disk and peak-memory estimates;
- optionally pinned feature, nucleus, donor, and fine-cell-type counts;
- whether the row is enabled.

A numeric expected count is a strict assertion and must equal the observed
count. An `NA` expected count means the value was not pinned before the first
production read. It does not disable the other integrity checks; it only means
that the corresponding count is discovered and recorded rather than compared
with a prior number.

### Shared analysis configuration

`config/analysis_parameters.yml` supplies the assay name, donor-ID width, and
the prespecified 13 mtDNA protein-coding gene symbols.

### Master cell metadata

`data/processed/cell.meta.data.tsv` is read using only four columns:

- `barcode`;
- `projid`;
- `cell_type_high_resolution`;
- `cell_type_broad`.

Only rows whose barcodes occur in the current RDS are retained. Phase 01 then
checks the object's donor and fine-cell-type annotations against this
independent table by barcode, not by row position.

### Execution configuration

`config/minerva_production_execution.yml` supplies provenance labels such as
execution stage/phase, backend, and run ID. These fields describe how the task
ran; they do not change the scientific audit checks.

## Detailed processing sequence

### 1. Validate command-line and manifest selection

The scientific script requires exactly one of `--manifest-row` or `--rds-id`.
The selection must identify one enabled manifest record, and the selected input
RDS must exist.

The normal controller invokes `scripts/run_one_rds.R`, which in turn launches
`scripts/01_audit_seurat_inputs.R` for the selected manifest row and captures
its log and controller-level exit status.

### 2. Initialize Seurat safely

The audit requires `yaml`, `Matrix`, `RcppAnnoy`, `Seurat`, `SeuratObject`, and
`data.table`.

It explicitly loads `RcppAnnoy` before Seurat. This order is required on the
Minerva environment because lazy S4 method resolution while reading an older
serialized Seurat object can otherwise trigger the `AnnoyAngular` Rcpp module
loading failure.

### 3. Read and identify the object

The script uses `readRDS()` and requires the result to inherit from `Seurat`.
It records both:

- the version stored in the serialized object's `object@version`; and
- the current Seurat and SeuratObject package versions used for the audit.

These versions are not expected to be identical. The production objects were
created with older Seurat object versions but were audited using Seurat 5.5.1
and SeuratObject 5.4.0.

### 4. Locate the raw counts and optional normalized layer

The configured assay is currently `RNA`. The script requires that assay and
retrieves its `counts` layer using the Seurat 5 layer interface, with a legacy
slot-access fallback for older objects.

The raw counts layer is mandatory. The `data` layer is inspected but is not
used as a substitute for later uniform normalization. `normalized_data_present`
only records whether such a layer already exists.

### 5. Audit the raw count matrix

The script records the matrix class and dimensions and verifies that raw counts
are:

- stored as a sparse Matrix object;
- finite;
- nonnegative;
- integer-valued within numerical tolerance.

It calculates the number of stored nonzero entries, total raw counts, total
counts per feature, and the number of nuclei detecting each feature.

The audit does not densify the full expression matrix. For a sparse matrix it
uses the sparse value and row-index slots plus sparse row/column sums. This is
important for objects with hundreds of thousands of nuclei.

### 6. Audit feature and barcode identifiers

The feature names are the raw-count matrix row names; cell barcodes are its
column names. Phase 01 requires:

- nonempty, nonmissing feature names;
- unique feature names;
- unique cell barcodes;
- object-metadata row names in exactly the same order as count-matrix columns.

An object with ambiguous features or misordered cell metadata cannot safely
proceed because later joins and gene-level summaries would be unreliable.

### 7. Audit object-level donor and cell-type metadata

The Seurat object must contain:

- `projid`;
- `cell_type_high_resolution`.

`projid` is normalized to an eight-character string. Numeric IDs shorter than
eight characters receive leading zeroes. Blank strings and textual missing
values become missing IDs.

The fine cell-type strings are trimmed and blanks become missing. Phase 01
requires every nucleus to have both a donor ID and fine cell type. It counts
the distinct represented donors and fine cell types and compares these counts
with any numeric expectations pinned in the manifest.

### 8. Compare the object with master metadata

Master metadata is filtered by barcode and reordered with `match()` to the RDS
column order. The audit then checks:

- every RDS barcode occurs in the master table;
- a barcode is not duplicated in the matching master subset;
- normalized donor IDs agree for every barcode;
- fine cell types agree for every barcode.

The broad cell-type labels found in the master table are recorded as an
additional scope check. For example, all Astrocytes RDS barcodes map to the
master broad type `Astrocytes`.

### 9. Confirm mtDNA protein-coding features

The RDS feature names are intersected with the 13-gene list declared in the
scientific configuration:

```text
MT-ATP6, MT-ATP8, MT-CO1, MT-CO2, MT-CO3, MT-CYB,
MT-ND1, MT-ND2, MT-ND3, MT-ND4, MT-ND4L, MT-ND5, MT-ND6
```

All 13 must be present. Phase 01 checks feature presence only; Phase 03 later
adds GENCODE and MitoCarta annotations, and Phase 04 calculates per-nucleus
mitochondrial QC values.

### 10. Inventory existing Seurat structure

For reproducibility, the audit records:

- all assays and the default assay;
- the class and layers of the audited assay;
- reductions;
- graphs;
- saved Seurat commands;
- whether any saved command name contains `NormalizeData`.

An existing `data` layer can be present even when no saved NormalizeData
command is available. Therefore, `normalized_data_present` and
`normalize_command_present` answer different questions: the first concerns the
current layer; the second concerns retained command provenance.

### 11. Build feature, cell-type, and donor inventories

The scientific task constructs three reusable long-form summaries:

- one row per feature;
- one row per fine cell type;
- one row per represented donor.

For donor summaries, all raw counts across the donor's nuclei are aggregated.
XIST and UTY counts are also aggregated and converted to counts per million of
all donor raw counts. These are sex-linked expression QC signals, not a
standalone reassignment of donor sex.

### 12. Validate, write atomically, and report status

The task evaluates 21 checks. It writes a semicolon-delimited list of any
failed check names into both the audit summary and status file. If no check
fails, the status is `validated_complete`; otherwise it is `failed` and the
script exits nonzero.

Each individual output is written to a temporary file and then renamed, so a
single final TSV cannot be observed half-written. The files are written near
the end of the task, with the scientific status written last. If a process is
interrupted between file renames, an incomplete bundle is still possible;
therefore downstream phases must require a readable `validated_complete`
status rather than relying only on the presence of one data file.

## The 21 required validation checks

The checks are embedded in the audit process; there is no separate
`annotation_checks`-style file in Phase 01.

| Check | Required condition |
| --- | --- |
| `seurat_object` | Loaded object inherits from Seurat. |
| `feature_count` | Observed features equal the pinned manifest value, or the expectation is unpinned. |
| `nucleus_count` | Observed nuclei equal the pinned manifest value, or the expectation is unpinned. |
| `counts_sparse` | Raw counts inherit from `sparseMatrix`. |
| `counts_finite` | Every stored raw-count value is finite. |
| `counts_nonnegative` | Every raw count is at least zero. |
| `counts_integer_valued` | Every raw count is integer-valued within tolerance. |
| `feature_names_nonempty` | No feature name is missing or empty. |
| `feature_names_unique` | Feature names have no duplicates. |
| `barcodes_unique` | Cell barcodes have no duplicates. |
| `metadata_rownames_match` | Seurat metadata row names exactly equal count-matrix column names in order. |
| `required_object_metadata` | Both `projid` and `cell_type_high_resolution` exist. |
| `donor_ids_complete` | Every nucleus has a normalized donor ID. |
| `donor_count` | Distinct donors equal the pinned expectation, or the expectation is unpinned. |
| `cell_types_complete` | Every nucleus has a nonblank fine cell type. |
| `cell_type_count` | Distinct fine cell types equal the pinned expectation, or the expectation is unpinned. |
| `mtdna_protein_genes` | All 13 prespecified mtDNA protein genes occur in the feature names. |
| `master_barcode_coverage` | Every RDS barcode matches one master-metadata row. |
| `master_barcodes_unique` | No matched master barcode is duplicated. |
| `master_projid_agreement` | Object and master donor IDs agree for every barcode. |
| `master_cell_type_agreement` | Object and master fine cell types agree for every barcode. |

The `.audit.tsv` file stores the overall result and failed-check names, but it
does not contain one row per check or the individual observed/expected values.
The relevant observed and expected object counts and mismatch totals are stored
as dedicated columns in the same audit row.

## Output bundles and row counts

Every RDS produces the same five suffixes. The inspected production directory
contains 9 x 5 = 45 files.

| Output prefix / `rds_id` | Audit rows | Feature rows | Cell-type rows | Donor rows | Status rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Astrocytes` / `astrocytes` | 1 | 33,538 | 3 | 427 | 1 |
| `Excitatory_neurons_set1` / `excitatory_set1` | 1 | 33,538 | 1 | 427 | 1 |
| `Excitatory_neurons_set2` / `excitatory_set2` | 1 | 33,538 | 4 | 425 | 1 |
| `Excitatory_neurons_set3` / `excitatory_set3` | 1 | 33,538 | 9 | 426 | 1 |
| `Immune_cells` / `immune` | 1 | 33,538 | 5 | 426 | 1 |
| `Inhibitory_neurons` / `inhibitory` | 1 | 33,538 | 25 | 423 | 1 |
| `OPCs` / `opcs` | 1 | 33,538 | 1 | 427 | 1 |
| `Oligodendrocytes` / `oligodendrocytes` | 1 | 33,538 | 1 | 427 | 1 |
| `Vasculature_cells` / `vasculature` | 1 | 33,538 | 5 | 423 | 1 |

The donor counts are per RDS. They must not be summed to estimate unique study
participants because the same donor can contribute multiple broad cell types.
Likewise, donors within the rows of a `.cell_types.tsv` file overlap and must
not be summed.

## `*.audit.tsv`: one row per audited RDS

Examples include `Astrocytes.audit.tsv` and
`Excitatory_neurons_set1.audit.tsv`. Each file contains exactly one wide row
describing the source object, its raw-count assay, observed dimensions,
metadata agreement, Seurat structure, and final scientific validation result.

### Identity and provenance columns

| Column | Meaning |
| --- | --- |
| `schema_version` | Audit-row schema, currently `rds_audit_v1`. |
| `rds_id` | Stable short identifier from the manifest. |
| `stable_task_id` | Stable task key, `audit:<rds_id>`. |
| `source_rds` | Project-relative path of the audited object. |
| `source_rds_bytes` | Source file size in bytes. |
| `source_rds_sha256` | SHA-256 of the exact RDS read by the task. This identifies content, not merely its filename. |

### Seurat object and assay columns

| Column | Meaning |
| --- | --- |
| `object_class` | Serialized object's R classes, semicolon-separated if more than one. |
| `object_version` | Version recorded inside `object@version`; this describes the serialized object format/history. |
| `seurat_version` | Installed Seurat package used to run the audit. |
| `seurat_object_version` | Installed SeuratObject package used to run the audit. |
| `assays` | All assay names in the object, semicolon-separated. |
| `default_assay` | Object's default assay when read. |
| `audited_assay` | Assay selected by the analysis configuration; currently `RNA`. |
| `assay_class` | R class of the audited assay. |
| `layers` | Layers/legacy slots exposed by the audited assay, semicolon-separated. |

### Raw-count and normalized-layer columns

| Column | Meaning |
| --- | --- |
| `raw_counts_class` | R matrix class of the raw counts, `dgCMatrix` in all inspected objects. |
| `raw_counts_sparse` | Whether raw counts inherit from a sparse Matrix class. |
| `raw_counts_integer_valued` | Whether all stored values are integer-valued within tolerance. |
| `raw_counts_nonnegative` | Whether all stored values are finite and at least zero. |
| `raw_counts_nnz` | Number of stored entries in the sparse raw-count matrix; for these canonical sparse matrices this represents nonzero gene-by-nucleus entries. |
| `raw_counts_total` | Sum of every raw UMI/count value in the object. |
| `normalized_data_present` | Whether an `RNA` data layer could be retrieved. It does not certify a common normalization method. |
| `normalized_data_dimensions` | Feature-by-nucleus dimensions of the existing data layer, written as `rowsxcolumns`; missing if no layer exists. |

`counts_finite` is enforced as a validation check but is not a separate audit
column. A nonfinite value also makes `raw_counts_nonnegative` false.

### Observed and expected dimension columns

| Column | Meaning |
| --- | --- |
| `features` | Number of raw-count matrix rows. |
| `nuclei` | Number of raw-count matrix columns. Each column is treated as one nucleus/cell barcode. |
| `donors` | Number of distinct nonmissing normalized `projid` values in this RDS. |
| `fine_cell_types` | Number of distinct nonmissing high-resolution cell types in this RDS. |
| `expected_features` | Manifest-pinned feature count, or `NA` if discovery was allowed. |
| `expected_nuclei` | Manifest-pinned nucleus count, or `NA`. |
| `expected_donors` | Manifest-pinned donor count, or `NA`. |
| `expected_fine_cell_types` | Manifest-pinned fine-cell-type count, or `NA`. |

An unpinned `NA` expectation does not mean the observed value is missing. The
observed count remains in `features`, `nuclei`, `donors`, or `fine_cell_types`.

### Metadata-agreement columns

| Column | Meaning |
| --- | --- |
| `metadata_fields` | All Seurat object metadata column names, semicolon-separated. |
| `master_metadata_rows_matched` | RDS barcodes with a matched master-metadata row. This must equal `nuclei`. |
| `master_metadata_missing_barcodes` | RDS barcodes absent from master metadata; required to be zero. |
| `master_metadata_duplicate_barcodes` | Duplicate matching barcode rows in master metadata; required to be zero. |
| `master_projid_mismatches` | Barcodes whose normalized object donor ID and master donor ID disagree or are unusable; required to be zero. |
| `master_cell_type_mismatches` | Barcodes whose object and master fine cell type disagree or are unusable; required to be zero. |
| `master_broad_cell_types` | Broad cell-type labels found in master metadata for this RDS, semicolon-separated. |

### Mitochondrial and retained-object-structure columns

| Column | Meaning |
| --- | --- |
| `mtdna_protein_genes_observed` | Number of the 13 expected mtDNA protein-coding symbols present. |
| `mtdna_protein_genes_missing` | Semicolon-separated missing symbols. An empty on-disk field is commonly read by R as `NA`. |
| `reductions` | Saved dimensional reductions such as `umap`, semicolon-separated. |
| `graphs` | Saved graph names, semicolon-separated; blank if none. |
| `commands` | Names of saved Seurat command records, semicolon-separated; blank if none. |
| `normalize_command_present` | Whether a saved command name contains `NormalizeData`. This does not indicate whether a data layer exists. |

### Result columns

| Column | Meaning |
| --- | --- |
| `validation_status` | `validated_complete` when all 21 checks pass; otherwise `failed`. |
| `failed_checks` | Semicolon-separated failed check names. Empty when all checks pass and often read back as `NA`. |

## `*.features.tsv.gz`: one row per original RDS feature

Examples include `Astrocytes.features.tsv.gz` and
`Inhibitory_neurons.features.tsv.gz`. These are gzip-compressed TSV files, not
R objects. Each inspected file has 33,538 rows in the exact raw-count feature
order.

| Column | Meaning |
| --- | --- |
| `feature_index` | One-based row position in the audited raw-count matrix. This preserves source order. |
| `feature` | Original matrix row name, normally a gene symbol in these objects. |
| `total_raw_counts` | Sum of raw counts for this feature across all nuclei in the RDS. |
| `nuclei_detected` | Number of nuclei with a stored/nonzero raw count for the feature. |
| `is_mtdna_protein_gene` | Whether the exact feature symbol belongs to the prespecified 13-gene mtDNA protein set. |

A feature with `total_raw_counts = 0` and `nuclei_detected = 0` is present in
the matrix vocabulary but not expressed in that RDS. Presence and expression
are therefore distinct. Phase 03 uses these files to construct the per-RDS
tested-gene universe without loading the large RDS again.

The number of positive-count features ranged from 27,516 in Vasculature to
31,147 in Excitatory set 2. Every file contains exactly 13 rows with
`is_mtdna_protein_gene = TRUE`.

## `*.cell_types.tsv`: one row per fine cell type in one RDS

Examples include `Astrocytes.cell_types.tsv` and
`Inhibitory_neurons.cell_types.tsv`. Rows summarize the object metadata without
altering any cell labels.

| Column | Meaning |
| --- | --- |
| `fine_cell_type` | Exact high-resolution cell-type label from the object. |
| `nuclei` | Number of nuclei assigned to that fine cell type in this RDS. |
| `donors` | Distinct nonmissing donors represented in that fine cell type. |
| `missing_donor_ids` | Nuclei in that fine cell type without a donor ID; required to be zero in a valid audit. |

Within one file, the `nuclei` values sum to the RDS nucleus count. The `donors`
values do not sum to the RDS donor count because a donor can contribute nuclei
to several fine cell types.

Across the nine files there are 54 fine-cell-type rows: 3 astrocyte, 14
excitatory across three files, 5 immune, 25 inhibitory, 1 OPC, 1
oligodendrocyte, and 5 vasculature types. The three excitatory files contain 1,
4, and 9 types respectively.

## `*.donors.tsv`: one row per represented donor in one RDS

Examples include `Astrocytes.donors.tsv` and `OPCs.donors.tsv`. A donor appears
once per RDS in which that donor has at least one nucleus. The same person can
therefore appear in several donor files.

| Column | Meaning |
| --- | --- |
| `schema_version` | Donor-inventory schema, currently `rds_donor_inventory_v1`. |
| `rds_id` | Stable RDS identifier. |
| `source_rds` | Project-relative source object path. |
| `projid` | Eight-character normalized donor/project ID. Read this column as text to preserve leading zeroes. |
| `nuclei` | Number of this donor's nuclei in this RDS. |
| `fine_cell_types` | Number of distinct fine cell types represented for this donor within this RDS. |
| `raw_counts` | Sum of all genes' raw counts across all nuclei from this donor in this RDS. |
| `xist_counts` | XIST raw counts summed across the donor's nuclei. |
| `uty_counts` | UTY raw counts summed across the donor's nuclei. |
| `xist_cpm` | `1,000,000 * xist_counts / raw_counts`; missing only if total raw counts are zero. |
| `uty_cpm` | `1,000,000 * uty_counts / raw_counts`; missing only if total raw counts are zero. |

XIST is an X-linked transcript commonly enriched in cells with an inactive X
chromosome; UTY is Y-linked. These aggregates can flag potential discrepancies
between reported sex and sex-linked expression, but zeros can arise from
dropout, limited depth, or cell-type biology. They must not be interpreted as a
definitive sex call in isolation.

Summing `nuclei` over a donor file reproduces the corresponding RDS nucleus
count. Summing `raw_counts` reproduces the RDS `raw_counts_total`.

## `*.audit_status.tsv`: one scientific task-status row per RDS

This one-row file records how the scientific audit ran. It is distinct from the
wide `.audit.tsv`: the audit file describes the Seurat object, while the status
file describes execution and reproducibility.

| Column | Meaning |
| --- | --- |
| `execution_phase` | Legacy numeric execution label from the execution configuration; production currently records `2`. It is not Scientific Phase 02. |
| `backend` | Execution backend, currently `direct`. |
| `run_id` | Configured run identifier. |
| `stable_task_id` | Stable audit task key. |
| `source_rds` | Project-relative source object path. |
| `scientific_script` | Script that generated the scientific artifacts. |
| `scientific_code_bundle_sha256` | SHA-256 of that script. |
| `scientific_config_sha256` | SHA-256 of the complete shared analysis configuration used by the run. |
| `manifest_sha256` | SHA-256 of the RDS manifest used for selection and expectations. |
| `peak_ram_gib` | Peak resident memory reported from the scientific R process. |
| `elapsed_seconds` | Scientific task wall-clock duration. |
| `validation_status` | Scientific validation outcome. |
| `failed_checks` | Semicolon-separated failed scientific checks; empty/`NA` after a successful audit. |
| `git_revision` | Repository commit visible to the scientific process. |
| `timestamp_utc` | Scientific completion time in UTC. |

When Phase 01 is launched through `run_pipeline.R`, a second controller status
is written outside this directory under:

```text
results/minerva_production/status/audit__<rds_id>.tsv
```

That wrapper-level row additionally records the child exit code and log path.
Logs are under the configured `results/minerva_production/logs/` directory.
Downstream verification can use both the scientific status and controller
status, but the `01_audit/*.audit_status.tsv` file is the authoritative
scientific status bundled with these outputs.

## Observed Minerva production results

| `rds_id` | Features | Nuclei | Donors | Fine types | Positive-count features | Peak RAM GiB | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `astrocytes` | 33,538 | 149,558 | 427 | 3 | 29,880 | 22.38 | 90.6 |
| `excitatory_set1` | 33,538 | 296,936 | 427 | 1 | 30,876 | 71.52 | 280.4 |
| `excitatory_set2` | 33,538 | 421,529 | 425 | 4 | 31,147 | 144.02 | 479.1 |
| `excitatory_set3` | 33,538 | 324,765 | 426 | 9 | 31,030 | 75.33 | 288.6 |
| `immune` | 33,538 | 83,889 | 426 | 5 | 28,834 | 9.04 | 42.6 |
| `inhibitory` | 33,538 | 329,699 | 423 | 25 | 30,838 | 67.42 | 268.7 |
| `opcs` | 33,538 | 90,502 | 427 | 1 | 29,573 | 16.04 | 62.2 |
| `oligodendrocytes` | 33,538 | 645,142 | 427 | 1 | 30,177 | 68.00 | 470.4 |
| `vasculature` | 33,538 | 17,974 | 423 | 5 | 27,516 | 2.71 | 19.7 |

The sum of the nine RDS nucleus counts is 2,359,994. This is a sum of object
columns; Phase 01 does not itself prove cross-object barcode uniqueness.

All nine inspected audits have `validation_status = validated_complete` and an
empty `failed_checks` field. Specifically:

- every object is a Seurat object with one `RNA` assay;
- all raw count matrices are sparse `dgCMatrix` objects;
- all raw counts are finite, nonnegative, and integer-valued;
- every object has 33,538 unique features and unique barcodes;
- all donor IDs and fine cell types are complete;
- every RDS barcode has one matching master-metadata record;
- there are zero donor-ID mismatches and zero fine-cell-type mismatches;
- all 13 mtDNA protein-coding genes are present in every object;
- every object has an existing `counts;data` layer pair;
- existing reductions vary by object, and no saved graphs were reported;
- normalized data are present in all objects, but only Immune, OPCs, and
  Vasculature retain a saved command whose name contains `NormalizeData`.

The presence of normalized data does not make the objects analytically uniform.
Later normalization still starts from the validated raw counts so that all
objects follow the same promoted method.

## How later phases use these files

- Phase 02 uses the donor inventories and audited metadata agreement to build
  the authoritative clinical cohort and per-RDS donor intersections.
- Phase 03 consumes the compressed feature inventories to map the complete
  per-RDS feature universe to GENCODE and MitoCarta.
- Phase 04 uses the audit dimensions and checksums to validate mitochondrial QC
  against the exact source RDS.
- Later validation uses the stable task IDs, script/config/manifest checksums,
  source checksums, and terminal statuses to determine whether results came
  from the promoted inputs and code.

No downstream phase should treat the existence of a `.features.tsv.gz` or
`.donors.tsv` file alone as proof of a successful audit. It should also require
the matching audit summary and scientific status to be readable and
`validated_complete`.
