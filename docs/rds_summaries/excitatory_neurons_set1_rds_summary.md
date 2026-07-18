# Excitatory Neurons Set 1 RDS: Concise Structure Summary

This document summarizes `Excitatory_neurons_set1.rds` from the completed Minerva inspection in `results/rds_structure_summaries.json`. It describes structure and dimensions; it does not contain the expression matrices.

## Overall dimensions

| Item | Value |
|---|---:|
| Seurat object | Seurat |
| Seurat object version | 3.2.3 |
| File size on disk | 5.6 GiB |
| Approximate size after loading in R | 28.5 GiB |
| Genes/features | 33,538 |
| Nuclei (called cells by Seurat) | 296,936 |
| Donors (`projid`) | 427 |
| Fine cell types | 1 |
| Observed donor × fine-cell-type combinations | 427 |
| Possible donor × fine-cell-type combinations | 427 |
| Donor × fine-cell-type coverage | 100.0% |
| Active assay | `RNA` |

Every nucleus has one nonmissing `projid` and one nonmissing `cell_type_high_resolution` value.

## Components inside the RDS

| Component | Dimensions | Biological coverage | Contents |
|---|---:|---:|---:|
| `RNA@counts` | 33,538 × 296,936 | 427 donors; 1 fine types | Raw UMI counts; 1,268,516,645 nonzero entries; 4,339,989,209 total UMIs |
| `RNA@data` | 33,538 × 296,936 | 427 donors; 1 fine types | Normalized expression; 1,268,516,645 nonzero entries |
| `RNA@scale.data` | Not populated | N/A | No scaled or z-scored expression layer |
| `RNA@meta.features` | 33,538 × 0 | Gene-level | Feature rows are present, but no feature-annotation columns are stored |
| `RNA@var.features` | Length 0 | Gene-level | No saved variable-feature list |
| `meta.data` | 296,936 × 2 | 427 donors; 1 fine types | Per-nucleus donor and fine-cell-type assignments |
| `active.ident` | Length 296,936 | Cell-level | Does not match fine-cell-type metadata |

## Fine-cell-type composition

| Fine cell type | Nuclei | Donors represented | Missing donor IDs |
|---|---:|---:|---:|
| `Exc L2-3 CBLN2 LINC02306` | 296,936 | 427 | 0 |
| **Total** | **296,936** | **427 unique** | **0** |

Donor counts overlap across rows because one donor can contribute nuclei to several fine cell types. The donor column must not be summed.

## Donor coverage across fine cell types

| Fine cell types represented for a donor | Number of donors |
|---|---:|
| 1 | 427 |
| **Total donors** | **427** |

### Nuclei per donor

| Minimum | First quartile | Median | Mean | Third quartile | Maximum |
|---|---:|---:|---:|---:|---:|
| 2 | 267.5 | 548 | 695.4 | 997.5 | 7,736 |

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

`Excitatory_neurons_set1.rds` contains raw and normalized RNA expression for 33,538 genes across 296,936 nuclei from 427 donors and 1 fine cell type(s). Donor-aware analyses should use `projid` as the biological replicate and `cell_type_high_resolution` as the cell-type label.
