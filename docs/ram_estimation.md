# RAM Estimation for Cell-Level Seurat Analysis

## Purpose

This document estimates the memory needed to process the local Seurat RDS files without pseudobulk aggregation. It covers three different memory situations:

1. Loading an RDS object into R.
2. Running Seurat `NormalizeData`.
3. Running genome-wide cell-level differential expression with MAST.

These operations do not have the same memory requirements. The compressed RDS size on disk is not a reliable estimate of the amount of RAM required after loading or during analysis.

## Local Machine Resources

The local machine had the following resources when checked:

| Resource | Measured amount |
| --- | ---: |
| Total physical RAM | ~15 GiB |
| RAM available during inspection | ~11 GiB |
| Total swap | ~4.0 GiB |
| Swap available during inspection | ~3.4 GiB |
| Available disk space | ~393 GB |

Disk space is sufficient for the four current RDS files and ordinary result tables. RAM is the limiting resource.

Swap should be treated as an emergency buffer rather than normal working memory. Heavy swap use can make R extremely slow and does not guarantee that an operation will finish.

## Measured RDS Memory

Each object was loaded independently in a fresh R process. R's `object.size()` was used to measure the complete Seurat object and its principal RNA matrices.

| Local RDS file | Estimated disk size | RAM after loading | Raw `counts` matrix | Existing `data` matrix | `scale.data` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/processed/Vasculature_cells.rds` | ~139 MB | **0.67 GiB** | 0.32 GiB | 0.32 GiB | Empty |
| `data/processed/Immune_cells.rds` | ~616 MB | **3.12 GiB** | 1.50 GiB | 1.50 GiB | Empty |
| `data/processed/OPCs.rds` | ~1.2 GB | **5.75 GiB** | 2.81 GiB | 2.81 GiB | Empty |
| `data/processed/Astrocytes.rds` | ~1.6 GB | **8.16 GiB** | 3.98 GiB | 3.98 GiB | Empty |

All four objects already contain both:

- A populated sparse raw-count matrix.
- A populated sparse `data` matrix with the same nonzero structure.

The four complete objects would occupy at least approximately **17.7 GiB** if loaded simultaneously, before temporary calculations or R overhead. Loading them together is therefore impossible on a machine with 15 GiB total RAM.

## Why Analysis Needs More RAM Than Loading

R commonly uses copy-on-modify behavior. A Seurat operation can temporarily retain the original matrix while constructing a replacement matrix. Memory may therefore include:

- The original Seurat object.
- Raw counts.
- The existing normalized `data` matrix.
- A newly generated normalized matrix.
- Temporary sparse-matrix arrays.
- Subsetted Seurat objects.
- Statistical-model and result objects.
- R package and interpreter overhead.

An operation can fail even when the loaded object itself fits into RAM.

## Estimated `NormalizeData` Requirements

The following are planning ranges rather than measured peaks. Exact use depends on the Seurat version, sparse-matrix implementation, number of temporary copies, and whether the existing `data` matrix is replaced in place.

| RDS file | RAM after loading | Estimated `NormalizeData` peak | Assessment on current machine |
| --- | ---: | ---: | --- |
| Vasculature | 0.67 GiB | ~2-4 GiB | Expected to be safe |
| Immune cells | 3.12 GiB | ~8-12 GiB | Possible but tight |
| OPCs | 5.75 GiB | ~12-16 GiB | High risk of swap or failure |
| Astrocytes | 8.16 GiB | ~18-24 GiB | Expected to exceed available RAM |

These estimates assume that sparse matrices remain sparse. Accidental dense conversion would require much more memory.

## Estimated Cell-Level MAST Requirements

Genome-wide cell-level MAST analysis can use substantially more memory than normalization. The exact peak is difficult to predict because it depends on:

- Number of nuclei in the selected cell type and sex-APOE group.
- Number of genes passing `min.pct` and other filters.
- Whether an intermediate representation becomes dense.
- Number and type of covariates.
- Whether the full Seurat object remains in memory while a subset is analyzed.
- Internal copies created by Seurat and MAST.

Conservative planning ranges are:

| RDS file | Estimated genome-wide MAST working RAM | Suggested installed RAM |
| --- | ---: | ---: |
| Vasculature | ~8-16 GiB | At least 16 GiB; 32 GiB preferred |
| Immune cells | ~24-48 GiB | At least 32 GiB; 64 GiB safer |
| OPCs | ~24-48 GiB | At least 32 GiB; 64 GiB safer |
| Astrocytes | ~48-64+ GiB | At least 64 GiB |

These ranges describe genome-wide cell-level work on large populations. Paper-like testing should be performed one fine cell type and one sex-APOE group at a time, which may substantially reduce the actual requirement.

Restricting `FindMarkers` to the 13 mtDNA-encoded protein genes or approximately 1,136 MitoCarta genes can reduce model memory relative to testing all 33,538 measured genes. Genome-wide tests are still needed when producing unbiased genome-wide rankings for pathway enrichment.

## Dense-Matrix Hazard

The expression matrices are stored efficiently as sparse `dgCMatrix` objects. A dense double-precision matrix requires eight bytes for every gene-cell combination, including zeros.

The approximate size of one dense full expression matrix is:

| RDS file | Genes | Nuclei | One dense matrix |
| --- | ---: | ---: | ---: |
| Vasculature | 33,538 | 17,974 | ~4.5 GiB |
| Immune cells | 33,538 | 83,889 | ~21.0 GiB |
| OPCs | 33,538 | 90,502 | ~22.6 GiB |
| Astrocytes | 33,538 | 149,558 | ~37.4 GiB |

One accidental dense conversion can exceed local RAM before accounting for the original Seurat object. Multiple dense working copies can require two or three times these amounts.

Avoid operations such as:

```r
full_dense_matrix <- as.matrix(object@assays$RNA@counts)
```

Do not run `ScaleData` over every gene in a large object:

```r
# Do not do this on a large complete object.
object <- ScaleData(object, features = rownames(object))
```

`scale.data` is generally dense. Scaling all 33,538 genes could create a matrix close to the dense sizes shown above.

## What Is Practical on the Current Machine?

### Vasculature

The approximately 139 MB Vasculature RDS uses approximately 0.67 GiB after loading. It is the safest object for testing normalization, metadata joining, mitochondrial feature selection, and a small MAST workflow.

Expected status:

- Loading: safe.
- `NormalizeData`: safe.
- MAST after fine-cell-type and sex-APOE subsetting: likely practical.
- Full genome-wide operations without subsetting: possible but should still be monitored.

### Immune cells

The approximately 616 MB Immune RDS uses approximately 3.12 GiB after loading.

Expected status:

- Loading: safe.
- `NormalizeData`: likely possible but close enough to the limit to require monitoring.
- MAST on the complete object: unsafe.
- MAST on one fine cell type and one sex-APOE group: potentially practical.

### OPCs

The approximately 1.2 GB OPC RDS uses approximately 5.75 GiB after loading.

Expected status:

- Loading: possible.
- `NormalizeData`: high risk because a replacement matrix can push memory above available RAM.
- Complete-object genome-wide MAST: unsafe.
- Aggressive donor/group subsetting before MAST: potentially possible, but the subsetting step itself can temporarily copy large matrices.

### Astrocytes

The approximately 1.6 GB Astrocytes RDS uses approximately 8.16 GiB after loading.

Expected status:

- Loading: possible but leaves little working memory.
- `NormalizeData`: likely to exceed local RAM.
- Complete-object MAST: unsafe.
- Fine-cell-type and sex-APOE subsetting may become practical only if the original object can be removed before modeling without creating an excessive temporary copy.

## Memory-Conscious Workflow Without Pseudobulk

If following the paper's cell-level MAST approach, use this execution pattern:

1. Process exactly one RDS at a time.
2. Start a fresh R process for every large analysis unit.
3. Load the source RDS.
4. Immediately subset to one `cell_type_high_resolution` and one sex-APOE group.
5. Retain only required metadata and assays.
6. Remove the original full object.
7. Run `gc()` before differential expression.
8. Run MAST on the subset.
9. Save only the compact result table.
10. Terminate R before processing the next contrast.

Conceptually:

```r
object <- readRDS(input_rds)

small_object <- subset(
  object,
  subset = cell_type_high_resolution == target_cell_type &
    sex == target_sex &
    apoe_group == target_apoe_group
)

rm(object)
gc()

result <- FindMarkers(
  small_object,
  ident.1 = "AD",
  ident.2 = "NCI",
  group.by = "diagnosis",
  test.use = "MAST",
  features = tested_genes,
  min.pct = 0.10,
  logfc.threshold = 0,
  latent.vars = c("nCount_RNA", "age_death_numeric", "pmi")
)
```

Subsetting can temporarily require both the source and subset objects. Monitor the peak rather than assuming only the final subset size matters.

## Monitoring Actual Peak RAM

Run each analysis through `/usr/bin/time`:

```bash
/usr/bin/time -v Rscript scripts/example_analysis.R
```

Review these fields in the output:

```text
Maximum resident set size
Elapsed wall clock time
Major page faults
Exit status
```

`Maximum resident set size` is reported in KiB on Linux. Divide by 1,048,576 to estimate GiB.

Also monitor current memory in another terminal:

```bash
watch -n 2 free -h
```

Stop increasing workload if swap usage rises continuously or the machine becomes unresponsive.

## Ways to Reduce RAM

Use these measures in roughly this order:

1. Process one file, cell type, and sex-APOE group at a time.
2. Restrict MAST to prespecified mitochondrial genes when genome-wide results are not required.
3. Remove reductions, graphs, tools, commands, unused assays, and unnecessary metadata from the working subset.
4. Keep expression matrices sparse.
5. Avoid full-object scaling and reclustering because cell annotations already exist.
6. Save result tables rather than many normalized copies of complete objects.
7. Use an on-disk representation such as BPCells or HDF5 for larger future inputs.
8. Use donor-level pseudobulk raw counts for the primary analysis when scientifically appropriate.

Pseudobulk does not eliminate the need to load an RDS at least once, but it reduces the large cell-level matrix to a much smaller donor-level matrix early in the workflow.

## Recommended Hardware

For processing one RDS at a time:

| Planned work | Recommended RAM |
| --- | ---: |
| Vasculature pilot and small mitochondrial MAST subsets | 16 GiB minimum; 32 GiB comfortable |
| Immune or OPC cell-level analysis | 32 GiB minimum; 64 GiB safer |
| Astrocyte genome-wide cell-level MAST | 64 GiB minimum |
| Full scaling, reclustering, or multiple large objects | 96-128 GiB may be needed |

The 15 GiB local machine is adequate for a Vasculature pilot and carefully subsetted analyses. It is not adequate for straightforward normalization and genome-wide cell-level analysis of all large objects.

## Decision Summary

| Question | Answer |
| --- | --- |
| Can all four RDS files be loaded together? | No; they require at least ~17.7 GiB before analysis. |
| Can Vasculature be processed locally? | Yes. |
| Can Immune cells be normalized locally? | Probably, but memory should be monitored. |
| Can OPCs be normalized locally? | It is high risk with 15 GiB total RAM. |
| Can Astrocytes be normalized locally? | It is likely to exceed available RAM. |
| Can full genome-wide MAST be run on large objects locally? | Not safely without strong subsetting or more RAM. |
| Does restricting analysis to mitochondrial genes help? | Yes, especially during MAST, although the full Seurat object must still be loaded initially. |
| Is disk space the immediate problem? | No; RAM is the immediate constraint. |

## Bottom Line

The compressed RDS sizes substantially underestimate working memory. The local objects occupy approximately 0.67-8.16 GiB each after loading, and normalization or MAST may require several additional copies or dense intermediate matrices. On the current 15 GiB machine, Vasculature is safe, Immune cells are manageable with care, OPCs are high risk, and Astrocytes are too large for straightforward normalization or genome-wide cell-level MAST. Process one narrowly subsetted analysis at a time, preserve sparse matrices, monitor peak memory, and avoid full-object scaling or dense conversion.
