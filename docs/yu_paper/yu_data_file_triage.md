# Yu Sex/APOE Data File Triage

This note summarizes which files from `files_in_data_directory.txt` are likely needed to extend `docs/Yu_sex_apoe.pdf`, and how the files relate to the analysis code in `AD_scRNAseq_companion-master`.

Estimated sizes come from `files_in_data_directory.txt`. They are rounded binary sizes (`GiB`, `MiB`, `KiB`) for storage planning.

## Main Recommendation

For a Yu-style extension, the key ingredients are processed PFC snRNA-seq expression data plus cell and donor metadata. The Yu paper used the Mathys ROSMAP prefrontal cortex snRNA-seq dataset with 2.3 million nuclei from 427 participants, 54 high-resolution cell types, and AD versus NCI differential expression tests inside six sex-APOE strata using Seurat `FindMarkers` with MAST.

The companion code is useful as a template, especially:

| Companion file | Estimated size | Why it matters |
| --- | ---: | --- |
| `AD_scRNAseq_companion-master/scripts/00_qc_normalization_cluster.Rmd` | Not listed in data inventory | Shows how the older tutorial builds a Seurat object from count matrix and metadata files. |
| `AD_scRNAseq_companion-master/scripts/Section_F_DEG_pipeline.Rmd` | Not listed in data inventory | Shows the `FindMarkers(..., test.use = "MAST")` pattern for cluster-specific DEG analysis. |

However, the companion repo targets older 2019 Mathys ROSMAP tutorial filenames, while the inventory points to the newer MIT_ROSMAP 427-donor processed release. Treat the companion code as method scaffolding rather than an exact filename match.

## Best Keep Set

Choose one primary route rather than keeping every representation of the same data.

| Route | Files | Estimated total size | Use when |
| --- | --- | ---: | --- |
| R/Seurat route | See cell-type `.rds` table below | ~34.9 GiB | Best match for Seurat/MAST differential expression like Yu. |
| Matrix route | See matrix-route table below | ~7.7 GiB | Leaner route if you want to rebuild objects yourself. |
| Python route | `Raw/PFC427_raw_data.h5ad` | ~85.3 GiB | Use if extending in Scanpy/Python. |

Do not copy both `Raw/PFC427_raw_data.h5ad` (~85.3 GiB) and all of the cell-type `.rds` objects (~34.9 GiB) unless storage is not a concern. They are likely alternative processed representations of the same broad dataset.

## R/Seurat Route

These are the most natural files if you want to adapt the Yu-style Seurat/MAST analysis.

| File | Estimated size | Recommendation |
| --- | ---: | --- |
| `Astrocytes.rds` | ~1.6 GiB | Keep. |
| `Excitatory_neurons_set1.rds` | ~5.7 GiB | Keep. |
| `Excitatory_neurons_set2.rds` | ~9.8 GiB | Keep. |
| `Excitatory_neurons_set3.rds` | ~5.8 GiB | Keep. |
| `Immune_cells.rds` | ~616 MiB | Keep. |
| `Inhibitory_neurons.rds` | ~5.2 GiB | Keep. |
| `OPCs.rds` | ~1.1 GiB | Keep. |
| `Oligodendrocytes.rds` | ~5.0 GiB | Keep. |
| `Vasculature_cells.rds` | ~138 MiB | Keep. |

Estimated total: ~34.9 GiB.

## Matrix Route

These files are likely the leanest reproducible starting point if you want to reconstruct objects yourself.

| File | Estimated size | Recommendation |
| --- | ---: | --- |
| `counts.hdf5` | ~7.7 GiB | Keep. Main expression matrix. |
| `cell.meta.data.tsv.gz` | ~28.6 MiB | Keep. Likely cell metadata; may or may not include all donor fields. |
| `Raw/genes.tsv` | ~1.9 MiB | Keep. Gene annotation. |
| `Raw/genes.cellranger_3.1.0.tsv` | ~1.9 MiB | Keep. Alternate Cell Ranger gene annotation. |
| `read_counts.R` | ~3.5 KiB | Keep. Likely documents how to read `counts.hdf5`. |

Estimated total: ~7.7 GiB.

## Python Route

| File | Estimated size | Recommendation |
| --- | ---: | --- |
| `Raw/PFC427_raw_data.h5ad` | ~85.3 GiB | Keep only if using Python/Scanpy or if this object is easier to inspect than the Seurat objects. |

## Maybe Useful

Keep these only if the extension uses pseudobulk summaries, sample-level analysis, or QC visualization.

| File | Estimated size | Recommendation |
| --- | ---: | --- |
| `pseudo_bulk/major_cell_type.raw.counts.RDS` | ~123 MiB | Maybe keep for pseudobulk count analyses. |
| `pseudo_bulk/major_cell_type.normalized.RDS` | ~336 MiB | Maybe keep for pseudobulk normalized analyses. |
| `pseudo_bulk/major_cell_type.meta.embeds.RDS` | ~177 KiB | Maybe keep if using the provided pseudobulk embeddings. |
| `pseudo_bulk/major_cell_type.clustering.png` | ~2.1 MiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.dist.normalized.png` | ~1.1 MiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.dist.raw.png` | ~973 KiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.lib.sizes.png` | ~171 KiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.mds.png` | ~450 KiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.tsne.png` | ~270 KiB | Optional QC/reference plot. |
| `pseudo_bulk/major_cell_type.voom.png` | ~118 KiB | Optional QC/reference plot. |

Estimated total for the core pseudobulk `.RDS` files: ~459 MiB.

Estimated total for listed pseudobulk plots: ~5.1 MiB.

## Use Carefully

These are probably not suitable for reproducing Yu's main sex-stratified analysis because sex has already been adjusted out.

| File | Estimated size | Recommendation |
| --- | ---: | --- |
| `pseudo_bulk/major_cell_type.normalized.PMI_age_sex_adjusted.RDS` | ~693 MiB | Use carefully; sex adjustment may remove the signal of interest. |
| `pseudo_bulk/major_cell_type.normalized.PMI_age_sex_adjusted.merged_by_sample.RDS` | ~369 MiB | Use carefully; sex adjustment may remove the signal of interest. |

Estimated total: ~1.0 GiB.

## Likely Skip

These files are old, coarser, diagnostic, or provenance-only for this project.

| File | Estimated size | Reason to skip |
| --- | ---: | --- |
| `SYNAPSE_METADATA_MANIFEST.tsv` | ~4.0 KiB | Useful for provenance, not analysis. |
| `pseudo_bulk/old/broad_cell_type.clustering.png` | ~2.2 MiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.dist.normalized.png` | ~861 KiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.dist.raw.png` | ~810 KiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.lib.sizes.png` | ~100 KiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.mds.png` | ~73 KiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.meta.embeds.RDS` | ~184 KiB | Old broad-cell-type embedding. |
| `pseudo_bulk/old/broad_cell_type.normalized.RDS` | ~406 MiB | Old broad-cell-type normalized pseudobulk object. |
| `pseudo_bulk/old/broad_cell_type.raw.counts.RDS` | ~158 MiB | Old broad-cell-type raw pseudobulk object. |
| `pseudo_bulk/old/broad_cell_type.tsne.png` | ~59 KiB | Old broad-cell-type diagnostic output. |
| `pseudo_bulk/old/broad_cell_type.voom.png` | ~124 KiB | Old broad-cell-type diagnostic output. |

Estimated total for listed old `broad_cell_type` files: ~568 MiB.

## Important Metadata Gap

The inventory may not include all donor-level metadata that Yu's analysis needs:

| Needed field | Estimated size | Why it matters |
| --- | ---: | --- |
| Donor or sample ID | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Joins expression/cell metadata to donor metadata. |
| Sex | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Required for female versus male strata. |
| APOE genotype | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Required for epsilon2, epsilon3/epsilon3, and epsilon4 strata. |
| Cognitive diagnosis or `cogdx` | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Required to compare AD versus NCI. |
| PMI | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Used as a covariate in Yu. |
| Age at death | Unknown; may be in `cell.meta.data.tsv.gz` (~28.6 MiB) | Used as a covariate in Yu. |
| `nCount_RNA` or total RNA counts | Unknown; likely in expression object or `cell.meta.data.tsv.gz` (~28.6 MiB) | Used as a covariate in Yu. |
| High-resolution cell type labels | Unknown; likely in expression object or `cell.meta.data.tsv.gz` (~28.6 MiB) | Required for 54-cell-type cluster-specific tests. |

The `/sc/...` paths in `files_in_data_directory.txt` were not mounted on this machine during inspection, so the header of `cell.meta.data.tsv.gz` could not be checked here.

On the system where the data exists, inspect the metadata columns with:

```bash
zcat cell.meta.data.tsv.gz | head -n 1 | tr '\t' '\n' | grep -Ei 'proj|individual|cell|type|sex|apoe|cogdx|pmi|age|ncount'
```

If those fields are absent, download or request the donor-level MIT_ROSMAP metadata files noted in `docs/data_availability.md`.

## Practical Starting Point

If using R/Seurat, start with the cell-type `.rds` route (~34.9 GiB) plus whatever donor metadata is needed. If using Python/Scanpy, start with `Raw/PFC427_raw_data.h5ad` (~85.3 GiB) plus donor metadata. If trying to minimize storage, start with `counts.hdf5` plus `cell.meta.data.tsv.gz`, gene TSVs, and `read_counts.R` (~7.7 GiB total), then verify that the metadata contains sex, APOE, diagnosis, PMI, age, and cell-type labels.
