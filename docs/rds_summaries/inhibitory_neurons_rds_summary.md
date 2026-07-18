# Inhibitory Neurons RDS: Concise Structure Summary

This document summarizes `Inhibitory_neurons.rds` from the completed Minerva inspection in `results/rds_structure_summaries.json`. It describes structure and dimensions; it does not contain the expression matrices.

## Overall dimensions

| Item | Value |
|---|---:|
| Seurat object | Seurat |
| Seurat object version | 3.1.5 |
| File size on disk | 5.2 GiB |
| Approximate size after loading in R | 25.3 GiB |
| Genes/features | 33,538 |
| Nuclei (called cells by Seurat) | 329,699 |
| Donors (`projid`) | 423 |
| Fine cell types | 25 |
| Observed donor × fine-cell-type combinations | 10,034 |
| Possible donor × fine-cell-type combinations | 10,575 |
| Donor × fine-cell-type coverage | 94.9% |
| Active assay | `RNA` |

Every nucleus has one nonmissing `projid` and one nonmissing `cell_type_high_resolution` value.

## Components inside the RDS

| Component | Dimensions | Biological coverage | Contents |
|---|---:|---:|---:|
| `RNA@counts` | 33,538 × 329,699 | 423 donors; 25 fine types | Raw UMI counts; 1,103,903,106 nonzero entries; 3,306,978,739 total UMIs |
| `RNA@data` | 33,538 × 329,699 | 423 donors; 25 fine types | Normalized expression; 1,103,903,106 nonzero entries |
| `RNA@scale.data` | Not populated | N/A | No scaled or z-scored expression layer |
| `RNA@meta.features` | 33,538 × 0 | Gene-level | Feature rows are present, but no feature-annotation columns are stored |
| `RNA@var.features` | Length 0 | Gene-level | No saved variable-feature list |
| `meta.data` | 329,699 × 2 | 423 donors; 25 fine types | Per-nucleus donor and fine-cell-type assignments |
| `active.ident` | Length 329,699 | Cell-level | Matches fine-cell-type metadata |
| `reductions$umap` | 329,699 × 2 | Cell-level | Saved `umap` cell embedding; assay used: `integrated`, but that assay is not stored |

## Fine-cell-type composition

| Fine cell type | Nuclei | Donors represented | Missing donor IDs |
|---|---:|---:|---:|
| `Inh ALCAM TRPM3` | 10,897 | 404 | 0 |
| `Inh CUX2 MSR1` | 24,885 | 408 | 0 |
| `Inh ENOX2 SPHKAP` | 12,396 | 409 | 0 |
| `Inh FBN2 EPB41L4A` | 6,769 | 405 | 0 |
| `Inh GPC5 RIT2` | 4,788 | 401 | 0 |
| `Inh L1 PAX6 CA4` | 5,070 | 393 | 0 |
| `Inh L1-2 PAX6 SCGN` | 1,617 | 355 | 0 |
| `Inh L1-6 LAMP5 CA13` | 15,060 | 414 | 0 |
| `Inh L3-5 SST MAFB` | 23,294 | 411 | 0 |
| `Inh L5-6 PVALB STON2` | 5,286 | 390 | 0 |
| `Inh L5-6 SST TH` | 4,502 | 397 | 0 |
| `Inh L6 SST NPY` | 1,404 | 346 | 0 |
| `Inh LAMP5 NRG1 (Rosehip)` | 26,065 | 413 | 0 |
| `Inh LAMP5 RELN` | 8,813 | 387 | 0 |
| `Inh PTPRK FAM19A1` | 10,438 | 401 | 0 |
| `Inh PVALB CA8 (Chandelier)` | 14,644 | 413 | 0 |
| `Inh PVALB HTR4` | 42,032 | 415 | 0 |
| `Inh PVALB SULF1` | 21,231 | 410 | 0 |
| `Inh RYR3 TSHZ2` | 24,230 | 418 | 0 |
| `Inh SGCD PDE3A` | 4,030 | 393 | 0 |
| `Inh SORCS1 TTN` | 9,610 | 399 | 0 |
| `Inh VIP ABI3BP` | 14,448 | 418 | 0 |
| `Inh VIP CLSTN2` | 17,631 | 418 | 0 |
| `Inh VIP THSD7B` | 8,211 | 403 | 0 |
| `Inh VIP TSHZ2` | 12,348 | 413 | 0 |
| **Total** | **329,699** | **423 unique** | **0** |

Donor counts overlap across rows because one donor can contribute nuclei to several fine cell types. The donor column must not be summed.

## Donor coverage across fine cell types

| Fine cell types represented for a donor | Number of donors |
|---|---:|
| 1 | 3 |
| 2 | 2 |
| 6 | 1 |
| 9 | 1 |
| 11 | 2 |
| 12 | 1 |
| 13 | 3 |
| 15 | 1 |
| 16 | 1 |
| 17 | 3 |
| 18 | 5 |
| 19 | 5 |
| 20 | 7 |
| 21 | 6 |
| 22 | 12 |
| 23 | 21 |
| 24 | 66 |
| 25 | 283 |
| **Total donors** | **423** |

### Nuclei per donor

| Minimum | First quartile | Median | Mean | Third quartile | Maximum |
|---|---:|---:|---:|---:|---:|
| 1 | 366.5 | 683 | 779.4 | 1,054.5 | 2,826 |

## Expression layers and normalization

- `RNA@counts` contains raw UMI counts and should be used for donor-level pseudobulk count models.
- `RNA@data` is populated and contains normalized expression values.
- `RNA@scale.data` is not populated.

A populated `RNA@data` matrix is present, but no normalization command is retained in the object. The exact method and scale factor therefore cannot be proven from this RDS alone.

## Saved reductions and analysis helpers

| Component | Dimensions | Interpretation |
|---|---:|---:|
| `reductions$umap` | 329,699 × 2 | Saved `umap` cell embedding; assay used: `integrated`, but that assay is not stored |

| Tool component | Dimensions | Interpretation |
|---|---:|---:|
| `tools$Integration@anchors` | 8,581,054 × 5 | Internal Seurat integration anchor table; not donor/sample metadata |
| `tools$TransferData$weights.matrix` | 147,825 × 329,699 | Sparse transfer weights; 16,484,950 nonzero entries |

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

`Inhibitory_neurons.rds` contains raw and normalized RNA expression for 33,538 genes across 329,699 nuclei from 423 donors and 25 fine cell type(s). Donor-aware analyses should use `projid` as the biological replicate and `cell_type_high_resolution` as the cell-type label.
