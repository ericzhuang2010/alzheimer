# Excitatory Neurons Set 2 RDS: Concise Structure Summary

This document summarizes `Excitatory_neurons_set2.rds` from the completed Minerva inspection in `results/rds_structure_summaries.json`. It describes structure and dimensions; it does not contain the expression matrices.

## Overall dimensions

| Item | Value |
|---|---:|
| Seurat object | Seurat |
| Seurat object version | 3.2.3 |
| File size on disk | 9.8 GiB |
| Approximate size after loading in R | 47.9 GiB |
| Genes/features | 33,538 |
| Nuclei (called cells by Seurat) | 421,529 |
| Donors (`projid`) | 425 |
| Fine cell types | 4 |
| Observed donor × fine-cell-type combinations | 1,679 |
| Possible donor × fine-cell-type combinations | 1,700 |
| Donor × fine-cell-type coverage | 98.8% |
| Active assay | `RNA` |

Every nucleus has one nonmissing `projid` and one nonmissing `cell_type_high_resolution` value.

## Components inside the RDS

| Component | Dimensions | Biological coverage | Contents |
|---|---:|---:|---:|
| `RNA@counts` | 33,538 × 421,529 | 425 donors; 4 fine types | Raw UMI counts; 2,134,899,444 nonzero entries; 8,200,910,010 total UMIs |
| `RNA@data` | 33,538 × 421,529 | 425 donors; 4 fine types | Normalized expression; 2,134,899,444 nonzero entries |
| `RNA@scale.data` | Not populated | N/A | No scaled or z-scored expression layer |
| `RNA@meta.features` | 33,538 × 0 | Gene-level | Feature rows are present, but no feature-annotation columns are stored |
| `RNA@var.features` | Length 0 | Gene-level | No saved variable-feature list |
| `meta.data` | 421,529 × 2 | 425 donors; 4 fine types | Per-nucleus donor and fine-cell-type assignments |
| `active.ident` | Length 421,529 | Cell-level | Does not match fine-cell-type metadata |

## Fine-cell-type composition

| Fine cell type | Nuclei | Donors represented | Missing donor IDs |
|---|---:|---:|---:|
| `Exc L3-4 RORB CUX2` | 184,784 | 423 | 0 |
| `Exc L3-5 RORB PLCH1` | 37,949 | 419 | 0 |
| `Exc L4-5 RORB GABRG1` | 79,361 | 416 | 0 |
| `Exc L4-5 RORB IL1RAPL2` | 119,435 | 421 | 0 |
| **Total** | **421,529** | **425 unique** | **0** |

Donor counts overlap across rows because one donor can contribute nuclei to several fine cell types. The donor column must not be summed.

## Donor coverage across fine cell types

| Fine cell types represented for a donor | Number of donors |
|---|---:|
| 1 | 3 |
| 2 | 5 |
| 3 | 2 |
| 4 | 415 |
| **Total donors** | **425** |

### Nuclei per donor

| Minimum | First quartile | Median | Mean | Third quartile | Maximum |
|---|---:|---:|---:|---:|---:|
| 1 | 477 | 853 | 991.8 | 1,222 | 3,875 |

## Expression layers and normalization

- `RNA@counts` contains raw UMI counts and should be used for donor-level pseudobulk count models.
- `RNA@data` is populated and contains normalized expression values.
- `RNA@scale.data` is not populated.

A populated `RNA@data` matrix is present, but no normalization command is retained in the object. The exact method and scale factor therefore cannot be proven from this RDS alone.

## Saved reductions and analysis helpers

No dimensionality reduction is stored. In particular, there is no saved PCA or UMAP.

No Seurat integration or transfer helper data are stored in `tools`.

- Graphs: none
- Neighbor objects: none
- Spatial images: none

## Metadata, identities, and sample information

The per-nucleus metadata contains exactly: `projid`, `cell_type_high_resolution`.

`active.ident` does **not** match `cell_type_high_resolution`; its recorded level(s) are `pbmc3k`. Use `cell_type_high_resolution` for cell-type grouping, or explicitly reset Seurat identities before an identity-based analysis.

The RDS does **not** contain `specimenID`, `sampleID`, `libraryID`, sequencing batch, or a barcode-to-specimen mapping. The available cell-level relationship is:

```text
nucleus barcode -> projid + fine cell type
```

It is not possible to assign nuclei to multiple specimens or libraries using this RDS alone. Do not join a one-to-many biospecimen table to nuclei using only `projid`.

Sex, diagnosis, APOE genotype, age, PMI, and `individualID` are also absent and must be joined from validated external donor metadata using `projid`.

## Mitochondrial feature coverage

All 13 canonical mtDNA-encoded protein genes are present.

## Important limitations

- The independent biological units are donors identified by `projid`; nuclei from one donor are not independent people.
- No specimen/library assignment or validated sequencing-batch covariate is stored.
- Clinical and genotype variables require an external donor-level join.
- No scaled expression, PCA, neighbor graph, or clustering graph is stored.
- The active Seurat identity is not the fine-cell-type annotation and should not be used without resetting it.

## Bottom line

`Excitatory_neurons_set2.rds` contains raw and normalized RNA expression for 33,538 genes across 421,529 nuclei from 425 donors and 4 fine cell type(s). Donor-aware analyses should use `projid` as the biological replicate and `cell_type_high_resolution` as the cell-type label.
