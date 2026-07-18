# OPCs RDS: Concise Structure Summary

This document summarizes `OPCs.rds` from the completed Minerva inspection in `results/rds_structure_summaries.json`. It describes structure and dimensions; it does not contain the expression matrices.

## Overall dimensions

| Item | Value |
|---|---:|
| Seurat object | Seurat |
| Seurat object version | 3.1.5 |
| File size on disk | 1.1 GiB |
| Approximate size after loading in R | 5.7 GiB |
| Genes/features | 33,538 |
| Nuclei (called cells by Seurat) | 90,502 |
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
| `RNA@counts` | 33,538 × 90,502 | 427 donors; 1 fine types | Raw UMI counts; 250,265,679 nonzero entries; 638,596,880 total UMIs |
| `RNA@data` | 33,538 × 90,502 | 427 donors; 1 fine types | Normalized expression; 250,265,679 nonzero entries |
| `RNA@scale.data` | Not populated | N/A | No scaled or z-scored expression layer |
| `RNA@meta.features` | 33,538 × 0 | Gene-level | Feature rows are present, but no feature-annotation columns are stored |
| `RNA@var.features` | Length 0 | Gene-level | No saved variable-feature list |
| `meta.data` | 90,502 × 2 | 427 donors; 1 fine types | Per-nucleus donor and fine-cell-type assignments |
| `active.ident` | Length 90,502 | Cell-level | Matches fine-cell-type metadata |
| `reductions$umap` | 90,502 × 2 | Cell-level | Saved `umap` cell embedding; assay used: `integrated`, but that assay is not stored |

## Fine-cell-type composition

| Fine cell type | Nuclei | Donors represented | Missing donor IDs |
|---|---:|---:|---:|
| `OPC` | 90,502 | 427 | 0 |
| **Total** | **90,502** | **427 unique** | **0** |

Donor counts overlap across rows because one donor can contribute nuclei to several fine cell types. The donor column must not be summed.

## Donor coverage across fine cell types

| Fine cell types represented for a donor | Number of donors |
|---|---:|
| 1 | 427 |
| **Total donors** | **427** |

### Nuclei per donor

| Minimum | First quartile | Median | Mean | Third quartile | Maximum |
|---|---:|---:|---:|---:|---:|
| 5 | 124.5 | 184 | 211.9 | 263.5 | 946 |

## Expression layers and normalization

- `RNA@counts` contains raw UMI counts and should be used for donor-level pseudobulk count models.
- `RNA@data` is populated and contains normalized expression values.
- `RNA@scale.data` is not populated.

The object retains `NormalizeData.RNA`: method `LogNormalize`, scale factor 10,000, recorded at `2021-01-14 10:32:44.386816`.

For gene *i* in nucleus *j*, the stored LogNormalize transformation is:

\[
\ln\left(1 + \frac{\mathrm{UMI}_{ij}}{\mathrm{total\ UMIs\ in\ nucleus\ }j} \times 10{,}000\right)
\]

## Saved reductions and analysis helpers

| Component | Dimensions | Interpretation |
|---|---:|---:|
| `reductions$umap` | 90,502 × 2 | Saved `umap` cell embedding; assay used: `integrated`, but that assay is not stored |

| Tool component | Dimensions | Interpretation |
|---|---:|---:|
| `tools$Integration@anchors` | 1,858,048 × 5 | Internal Seurat integration anchor table; not donor/sample metadata |
| `tools$TransferData$weights.matrix` | 2,745 × 90,502 | Sparse transfer weights; 4,525,100 nonzero entries |

- Graphs: none
- Neighbor objects: none
- Spatial images: none

## Metadata, identities, and sample information

The per-nucleus metadata contains exactly: `projid`, `cell_type_high_resolution`.

`active.ident` matches `cell_type_high_resolution`, so Seurat's active grouping is the fine-cell-type label.

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
- A saved embedding references an `integrated` assay that is absent; the embedding can be plotted, but the original integration cannot be reconstructed from this RDS alone.

## Bottom line

`OPCs.rds` contains raw and normalized RNA expression for 33,538 genes across 90,502 nuclei from 427 donors and 1 fine cell type(s). Donor-aware analyses should use `projid` as the biological replicate and `cell_type_high_resolution` as the cell-type label.
