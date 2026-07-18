# Tutorial: Understanding `data/processed/Vasculature_cells.rds`

This document explains the structure of the Seurat RDS file:

| File | Approximate size | What it is |
|---|---:|---|
| `data/processed/Vasculature_cells.rds` | ~139M on disk, ~689.9 Mb in R memory | A serialized R object containing a Seurat object for vascular cells |
| `scripts/inspect_rds_py8rds.py` | ~12K | A Python helper script that reads this RDS using `py8rds` and converts it to AnnData in memory |

The goal is to make the file understandable even if you have never used Seurat before.

## Very Short Summary

`data/processed/Vasculature_cells.rds` is a saved Seurat object. A Seurat object is a container for single-cell or single-nucleus RNA-seq data. It stores:

- A gene-by-cell count matrix.
- A normalized gene-by-cell expression matrix.
- Per-cell metadata.
- Cell identities, here the vascular cell subtype labels.
- A UMAP embedding for visualization.
- Some records of analysis commands and integration-related helper data.

This specific object contains:

| Item | Value |
|---|---:|
| Seurat object class | `Seurat` |
| Seurat object version | `3.1.5` |
| Project name | `SeuratProject` |
| Cells | 17,974 |
| Features/genes | 33,538 |
| Donor/sample IDs in `projid` | 423 |
| Assays | `RNA` |
| Active assay | `RNA` |
| Reductions | `umap` |
| Graphs | 0 |
| Neighbors | 0 |
| Images | 0 |
| Metadata columns | `projid`, `cell_type_high_resolution` |

The object is useful for expression analysis of vascular cells, but it does not by itself contain sex, APOE genotype, clinical diagnosis, chromosome positions, gene coordinates, or the original FASTQ/BAM files.

## What Is An RDS File?

An `.rds` file is an R serialization format. It is a saved R object. In R, you usually read it with:

```r
obj <- readRDS("data/processed/Vasculature_cells.rds")
```

The `.rds` extension does not tell you what kind of R object is inside. It could contain a vector, a data frame, a list, a model, or, in this case, a Seurat object.

For this file:

```text
class: Seurat
```

So the `.rds` file is just the storage wrapper. The important thing inside is the Seurat object.

## What Is A Seurat Object?

Seurat is an R toolkit for single-cell and single-nucleus RNA-seq analysis. A Seurat object is a structured container that keeps related pieces of an analysis together.

The most important mental model is:

```text
Seurat object
  assays       expression matrices, usually counts and normalized data
  meta.data    per-cell annotations
  reductions   embeddings such as PCA, UMAP, t-SNE
  graphs       nearest-neighbor graphs used for clustering
  commands     record of some Seurat commands that created or modified the object
  tools        extra analysis outputs used internally by some workflows
```

In Seurat, cells are usually columns in the expression matrix, and genes/features are rows.

That means the main count matrix in this object has shape:

```text
33,538 genes x 17,974 cells
```

This is different from AnnData/Scanpy, where the matrix is usually:

```text
17,974 cells x 33,538 genes
```

When converting from Seurat to AnnData, the matrix is transposed.

## What Is An S4 Object And What Are Slots?

R has a formal object system called S4. Seurat objects use this system.

Instead of storing fields like a Python dictionary:

```python
obj["assays"]
```

Seurat stores named fields called slots:

```r
obj@assays
obj@meta.data
obj@reductions
```

When you see a name such as `obj@assays`, read it as:

```text
the assays slot of the Seurat object
```

This object has the following top-level slots:

| Slot | Present here? | Beginner meaning |
|---|---:|---|
| `assays` | yes | Expression data containers. This object has one assay named `RNA`. |
| `meta.data` | yes | Table with one row per cell. |
| `active.assay` | yes | Which assay Seurat treats as the default. Here it is `RNA`. |
| `active.ident` | yes | The current cell identity labels. Here these are vascular cell types. |
| `graphs` | empty | Neighbor graphs used for clustering. None are stored here. |
| `neighbors` | empty | Neighbor search results. None are stored here. |
| `reductions` | yes | Dimensionality reductions. This object has UMAP. |
| `images` | empty | Spatial image data. None are stored here. |
| `project.name` | yes | A simple project label, `SeuratProject`. |
| `misc` | empty or not used | General extra storage. Not used meaningfully here. |
| `version` | yes | Seurat object version, `3.1.5`. |
| `commands` | yes | Records of Seurat commands. Here it records normalization. |
| `tools` | yes | Extra analysis data. Here it has `Integration` and `TransferData`. |

## Top-Level Object Structure

Actual values from this file:

```text
class: Seurat
version: 3.1.5
project.name: SeuratProject
active.assay: RNA
cells: 17,974
features/genes: 33,538
```

Top-level slot names:

```text
assays
meta.data
active.assay
active.ident
graphs
neighbors
reductions
images
project.name
misc
version
commands
tools
```

Important practical point:

The object contains enough information to inspect expression values and vascular cell subtype labels. It does not contain every piece of information needed for a full clinical or genotype-aware reanalysis.

## The `assays` Slot

The `assays` slot stores expression data.

This object has one assay:

```text
RNA
```

An assay is a container for matrices that all describe the same cells and genes, but at different stages of processing.

For this object:

```text
obj@assays$RNA
```

is the main RNA expression assay.

### RNA Assay Slots

The RNA assay contains these important internal slots:

| RNA assay slot | Value in this object | Beginner meaning |
|---|---|---|
| `counts` | `dgCMatrix`, 33,538 x 17,974, ~327.1 Mb in R memory | Raw count matrix. Usually integer UMI counts. |
| `data` | `dgCMatrix`, 33,538 x 17,974, ~327.1 Mb in R memory | Normalized expression matrix. Here it was made with `LogNormalize`. |
| `scale.data` | 0 x 0 | Empty. Scaled expression values are not stored. |
| `key` | `rna_` | Prefix Seurat can use for feature naming. Usually not critical for basic analysis. |
| `assay.orig` | empty | Original assay name, not meaningfully filled here. |
| `var.features` | length 0 | No variable feature list is stored. |
| `meta.features` | 33,538 x 0 | Gene-level metadata table exists in shape only, but has zero columns. |
| `misc` | `NULL` | No assay-specific miscellaneous data. |

### `counts`: Raw Expression Counts

The `counts` matrix has:

```text
class: dgCMatrix
shape: 33,538 genes x 17,974 cells
nonzero entries: 28,258,935
```

This is the matrix you would usually use when you want raw or near-raw expression counts.

Each row is a gene.
Each column is a cell.
Each value is the expression count for one gene in one cell.

Example interpretation:

```text
counts["MT-ND1", "GACTACAAGGCTCTTA-1-0"]
```

would mean:

```text
the raw count for gene MT-ND1 in cell GACTACAAGGCTCTTA-1-0
```

### `data`: Normalized Expression

The `data` matrix has:

```text
class: dgCMatrix
shape: 33,538 genes x 17,974 cells
nonzero entries: 28,258,935
```

This matrix stores normalized values. The stored command says it was made using:

```text
NormalizeData
normalization.method: LogNormalize
scale.factor: 10000
```

The usual meaning is:

1. For each cell, divide each gene count by the total counts in that cell.
2. Multiply by 10,000.
3. Apply a log transform.

In plain English:

```text
counts = raw observed expression
data = normalized expression, better for comparing expression across cells
```

### `scale.data`: Scaled Values

`scale.data` is empty:

```text
0 x 0
```

In some Seurat workflows, `scale.data` stores z-scored expression values after `ScaleData()`.

This object does not store those values. That means if a workflow requires scaled data, you would need to recompute it.

### Sparse Matrix: What Does `dgCMatrix` Mean?

Both `counts` and `data` are stored as `dgCMatrix`.

This is an R sparse matrix class from the Matrix package. It is used because single-cell RNA-seq matrices are mostly zeros.

Most genes are not detected in most individual cells. If we stored every zero explicitly, the file would be much larger.

A `dgCMatrix` stores only nonzero values. Internally it has pieces such as:

| Internal piece | Meaning |
|---|---|
| `Dim` | Matrix dimensions, here 33,538 x 17,974. |
| `Dimnames` | Row and column names, here gene names and cell barcodes. |
| `x` | The nonzero values. |
| `i` | Row indices for the nonzero values. |
| `p` | Column pointers showing where each cell column starts and ends. |

You usually do not need to work with `x`, `i`, and `p` directly. They explain why the matrix is compact.

## Genes And Cell Names

The matrix row names are gene or feature names.

The first 20 genes in this object are:

```text
MIR1302-2HG
FAM138A
OR4F5
AL627309.1
AL627309.3
AL627309.2
AL627309.4
AL732372.1
OR4F29
AC114498.1
OR4F16
AL669831.2
AL669831.5
FAM87B
LINC00115
FAM41C
AL645608.7
AL645608.3
AL645608.5
AL645608.1
```

The matrix column names are cell names or cell barcodes.

The first 10 cells are:

```text
GACTACAAGGCTCTTA-1-0
ACTGAGTTCACTTATC-2-0
CACAAACGTAAGGGAA-2-0
CGGTTAAAGGCTCAGA-2-0
TACCTTACATTAACCG-2-0
ACAGCCGTCAACGGGA-3-0
AGCATACTCGTTGACA-3-0
CAGCTAAAGGTAGCCA-3-0
CATGCCTCAGCTGCTG-3-0
CGACCTTAGCTGATAA-3-0
```

These cell names are important because they connect:

- expression matrix columns
- metadata rows
- UMAP rows
- cell identity labels

If cell names get changed or reordered incorrectly, the object becomes hard to interpret.

## The `meta.data` Slot

The `meta.data` slot is a table with one row per cell.

This object has 17,974 rows in metadata because it has 17,974 cells.

It has only two metadata columns:

```text
projid
cell_type_high_resolution
```

### `projid`

`projid` appears to identify the donor, participant, or sample associated with each cell.

This object has:

```text
423 unique projid values
```

This means the object contains cells from many biological samples or donors, not just one sample.

A single `projid` can have many cells. A cell-level object like this stores one row per cell, so the same `projid` appears repeatedly across cells from that donor/sample.

### `cell_type_high_resolution`

This column stores the vascular cell subtype label.

Counts in this object:

| Cell type | Cells |
|---|---:|
| `End` | 6,514 |
| `Per` | 5,308 |
| `Fib FLRT2` | 3,728 |
| `SMC` | 1,605 |
| `Fib SLC4A4` | 819 |

Likely meanings:

| Label | Likely cell type meaning |
|---|---|
| `End` | Endothelial cells |
| `Per` | Pericytes |
| `SMC` | Smooth muscle cells |
| `Fib FLRT2` | Fibroblast subtype marked by or associated with `FLRT2` |
| `Fib SLC4A4` | Fibroblast subtype marked by or associated with `SLC4A4` |

The exact biological naming should be checked against the paper or original metadata, but these are the practical labels in this file.

## The `active.ident` Slot

`active.ident` is Seurat's current identity label for each cell.

In many analyses, `active.ident` is what Seurat uses by default when grouping cells for plots or differential expression.

In this object, `active.ident` has the same five levels as `cell_type_high_resolution`:

```text
End
Fib FLRT2
Fib SLC4A4
Per
SMC
```

Counts:

| Active identity | Cells |
|---|---:|
| `End` | 6,514 |
| `Fib FLRT2` | 3,728 |
| `Fib SLC4A4` | 819 |
| `Per` | 5,308 |
| `SMC` | 1,605 |

Practical meaning:

If you ran a Seurat command that groups by the current identity, it would group cells by these vascular subtype labels.

## The `reductions` Slot

The `reductions` slot stores low-dimensional embeddings.

This object has one reduction:

```text
umap
```

The UMAP has:

```text
shape: 17,974 cells x 2 dimensions
key: UMAP_
assay.used: integrated
```

The two columns are usually UMAP dimension 1 and UMAP dimension 2.

Practical meaning:

Each cell has an `(x, y)` coordinate for plotting in two-dimensional UMAP space.

Important caveat:

The UMAP says:

```text
assay.used: integrated
```

but this object only stores an assay named:

```text
RNA
```

So the UMAP was probably computed earlier using an integrated assay or integrated workflow, but that full integrated assay is not stored in this RDS file.

That means:

- You can use the saved UMAP coordinates for visualization.
- You should not assume you can exactly reconstruct the original integration workflow from this object alone.
- If you want a new UMAP from raw counts or normalized data, you would need to recompute it.

Other UMAP-related slots are empty:

| UMAP component | Value |
|---|---|
| cell embeddings | 17,974 x 2 |
| feature loadings | 0 x 0 |
| projected feature loadings | 0 x 0 |
| standard deviations | length 0 |
| misc | length 0 |

This is normal for UMAP. UMAP usually stores cell coordinates, not gene loadings.

## Empty Slots: Graphs, Neighbors, Images

This object has:

```text
graphs: 0
neighbors: 0
images: 0
```

### Why Graphs Matter

Seurat often builds nearest-neighbor graphs before clustering.

Those graphs may have names like:

```text
RNA_nn
RNA_snn
integrated_snn
```

This object does not store any of them.

Practical implication:

If you want to rerun graph-based clustering from this object, you probably need to recompute PCA/neighbors/clusters.

### Why Neighbors Matter

The `neighbors` slot can store nearest-neighbor search results.

This object does not store them.

Practical implication:

UMAP coordinates are present, but the neighbor structure used to compute them is not.

### Why Images Matter

The `images` slot is used for spatial transcriptomics datasets.

This object is not storing spatial image data.

## The `commands` Slot

The `commands` slot records some Seurat commands that were run.

This object stores one command:

```text
NormalizeData.RNA
```

Stored command details:

```text
command name: NormalizeData.RNA
timestamp: 2021-01-13 13:24:38.301695
assay.used: RNA
call.string: NormalizeData(pbmc)
```

Stored parameters:

| Parameter | Value |
|---|---|
| `assay` | `RNA` |
| `normalization.method` | `LogNormalize` |
| `scale.factor` | 10000 |
| `margin` | 1 |
| `verbose` | TRUE |

Practical meaning:

The normalized `data` matrix was created from the `RNA` assay using Seurat's log-normalization workflow.

The command history is useful, but it is not a complete provenance record. It does not necessarily tell you every step that was ever run.

## The `tools` Slot

The `tools` slot stores extra analysis objects that do not fit neatly into assays, reductions, metadata, or graphs.

This object has:

| Tool item | Approximate R object size | Meaning |
|---|---:|---|
| `Integration` | ~18.1 Mb | Seurat integration-related data. |
| `TransferData` | ~10.4 Mb | Data related to label or data transfer. |

For a beginner, these are less important than `assays`, `meta.data`, and `reductions`.

Practical advice:

Start with:

```text
RNA counts
RNA normalized data
cell metadata
UMAP
```

Treat `tools` as internal analysis helper data unless you specifically need to reproduce an integration or transfer workflow.

## What Is Not Stored In This RDS

This part is important for project planning.

The object does not visibly store:

| Missing or not directly stored | Why it matters |
|---|---|
| Sex | Needed for sex-based comparisons. |
| APOE genotype | Needed for APOE-stratified analyses. |
| Clinical diagnosis | Needed for disease/control comparisons. |
| Age | Important covariate. |
| PMI | Important covariate for postmortem tissue. |
| Chromosome name per gene | Needed for chromosome-aware analysis. Use external annotation. |
| Gene coordinates | Needed for genomic interval analysis. Use external annotation. |
| Full integrated assay | UMAP references `integrated`, but only `RNA` is stored. |
| PCA reduction | Needed for many Seurat workflows; not stored here. |
| Neighbor graph | Needed for clustering; not stored here. |
| Original FASTQ/BAM files | Needed for alignment or read-level processing. |
| Differential expression results | Would need to be recomputed or found elsewhere. |

The key join variable for external sample-level metadata is probably:

```text
projid
```

That is where you would attach sex, APOE, diagnosis, age, PMI, and other donor-level information if you have a separate metadata table.

## Chromosome Names And Mitochondrial Genes

The RDS stores gene names as row names, but it does not store chromosome names.

For example, the object knows about a gene named:

```text
MT-ND1
```

but it does not store a table saying:

```text
MT-ND1 is on chrM
```

To map genes to chromosomes, use an external hg38 annotation file.

You already have a suitable annotation file:

| File | Approximate size | Use |
|---|---:|---|
| `/home/ericzhuang2010/.gcell_data/annotations/gencode.v44.basic.annotation.gtf.gz` | ~28 MiB | hg38/GRCh38 GENCODE annotation with gene names and chromosome names |

The mitochondrial protein-coding genes found in this RDS are:

```text
MT-ND1
MT-ND2
MT-CO1
MT-CO2
MT-ATP8
MT-ATP6
MT-CO3
MT-ND3
MT-ND4L
MT-ND4
MT-ND5
MT-ND6
MT-CYB
```

The hg38 GENCODE annotation contains more mitochondrial genes on `chrM`, including mitochondrial rRNA and tRNA genes. This RDS contains the 13 canonical mitochondrial protein-coding genes listed above.

## Counts Versus Normalized Data

This is one of the most common beginner confusions.

### Raw counts

Stored in:

```text
obj@assays$RNA@counts
```

Use when:

- You need raw expression counts.
- You are creating pseudobulk counts.
- You are using methods that expect counts.
- You want to recompute normalization yourself.

### Normalized data

Stored in:

```text
obj@assays$RNA@data
```

Use when:

- You want already-normalized expression values.
- You are making many expression plots.
- You are doing exploratory comparisons.

### Scaled data

Would be stored in:

```text
obj@assays$RNA@scale.data
```

But here it is empty.

Use only if:

- You recompute it.
- A downstream method specifically asks for scaled data.

## Seurat Orientation Versus AnnData Orientation

This matters if you use Python.

### In Seurat

Expression matrices are:

```text
genes x cells
```

For this object:

```text
33,538 x 17,974
```

### In AnnData

Expression matrices are:

```text
cells x genes
```

After conversion:

```text
17,974 x 33,538
```

So:

```text
Seurat rows    -> AnnData columns / adata.var
Seurat columns -> AnnData rows / adata.obs
```

## Python Inspection With `py8rds`

I installed `py8rds` in the project-local virtual environment:

| Path | Approximate size | Purpose |
|---|---:|---|
| `.venv` | ~409M | Python environment with `py8rds`, `anndata`, `scipy`, `pandas`, and `numpy` |
| `scripts/inspect_rds_py8rds.py` | ~12K | Inspection and optional AnnData conversion script |

Installed package versions:

```text
py8rds 1.1.1
anndata 0.13.1
scipy 1.18.0
pandas 3.0.3
numpy 2.5.1
```

The RDS is currently located at:

```text
data/processed/Vasculature_cells.rds
```

The script still accepts the old default path `data/Vasculature_cells.rds`; if that path is missing, it falls back to `data/processed/Vasculature_cells.rds`.

Run the inspector:

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
.venv/bin/python scripts/inspect_rds_py8rds.py data/processed/Vasculature_cells.rds
```

Expected high-level output:

```text
File: data/processed/Vasculature_cells.rds (138.1 MiB)
Top class: Seurat
Assays: ['RNA']
Metadata columns: ['projid', 'cell_type_high_resolution']
Reductions: ['umap']
AnnData shape: (17974, 33538)
AnnData obs columns: ['projid', 'cell_type_high_resolution', 'seurat_active_ident']
AnnData layers: ['counts', 'lognorm']
AnnData obsm keys: ['X_umap']
AnnData uns keys: ['seurat']
X type: csr_matrix
```

To write an AnnData file:

```bash
.venv/bin/python scripts/inspect_rds_py8rds.py data/processed/Vasculature_cells.rds --write-h5ad data/processed/Vasculature_cells.h5ad
```

The script defaults to using:

```text
assay: RNA
layer: counts
```

That means the AnnData object's `adata.X` contains raw counts by default. The script also stores raw counts in `adata.layers["counts"]` and normalized expression in `adata.layers["lognorm"]`.

To use normalized expression as `adata.X` instead:

```bash
.venv/bin/python scripts/inspect_rds_py8rds.py data/processed/Vasculature_cells.rds --layer data --write-h5ad data/processed/Vasculature_cells.normalized.h5ad
```

Even when `--layer data` is used, the script still stores both named layers by default:

```text
adata.layers["counts"]
adata.layers["lognorm"]
```

To reduce memory use and only keep the selected matrix in `adata.X`, use:

```bash
.venv/bin/python scripts/inspect_rds_py8rds.py data/processed/Vasculature_cells.rds --no-assay-layers
```

## How The RDS Maps To AnnData

When converted to AnnData, the conceptual mapping is:

| Seurat item | AnnData item | Meaning |
|---|---|---|
| selected `RNA` layer, default `RNA@counts` | `adata.X` | Main expression matrix, transposed to cells x genes. |
| `RNA@counts` | `adata.layers["counts"]` | Raw count matrix, also transposed to cells x genes. |
| `RNA@data` | `adata.layers["lognorm"]` | Log-normalized expression matrix. |
| `RNA@scale.data` | `adata.layers["scale_data"]` only if non-empty | Scaled data. It is empty in this RDS, so it is skipped. |
| `meta.data` | `adata.obs` | Cell metadata. |
| `active.ident` | `adata.obs["seurat_active_ident"]` | Seurat's active cell identity labels. |
| gene row names | `adata.var_names` | Gene names. |
| cell column names | `adata.obs_names` | Cell names. |
| `reductions$umap@cell.embeddings` | `adata.obsm["X_umap"]` | UMAP coordinates. |
| simple Seurat metadata | `adata.uns["seurat"]` | Project name, Seurat version, assay summaries, command summaries, tool names/classes, and conversion notes. |

For this object, the AnnData summary from the smoke test was:

```text
shape: 17,974 cells x 33,538 genes
obs columns: projid, cell_type_high_resolution, seurat_active_ident
layers: counts, lognorm
obsm keys: X_umap
uns keys: seurat
X type: csr_matrix
X nonzero entries: 28,258,935
```

`csr_matrix` is the Python sparse matrix equivalent used by SciPy. Like `dgCMatrix`, it avoids storing every zero explicitly.

## What The Current AnnData Conversion Includes And Does Not Include

The conversion is more complete than a one-matrix export, but it is still not a lossless Seurat-to-AnnData clone. AnnData and Seurat have different object models, so some Seurat internals are summarized rather than fully preserved.

### Included In The AnnData File

| RDS / Seurat content | AnnData location | Included detail |
|---|---|---|
| selected expression layer, default `RNA@counts` | `adata.X` | Main matrix for analysis. Shape becomes 17,974 cells x 33,538 genes. |
| raw counts `RNA@counts` | `adata.layers["counts"]` | Full sparse raw count matrix. |
| normalized expression `RNA@data` | `adata.layers["lognorm"]` | Full sparse log-normalized matrix from Seurat `LogNormalize`. |
| scaled expression `RNA@scale.data` | skipped here | The script would store it as `adata.layers["scale_data"]` if it were non-empty, but this RDS has `0 x 0` scaled data. |
| cell metadata `meta.data` | `adata.obs` | Includes `projid` and `cell_type_high_resolution`. |
| Seurat active identities `active.ident` | `adata.obs["seurat_active_ident"]` | Preserves the current Seurat cell identity labels. In this object they match the vascular subtype labels. |
| cell names/barcodes | `adata.obs_names` | Preserves cell identifiers such as `GACTACAAGGCTCTTA-1-0`. |
| gene names | `adata.var_names` | Preserves row names such as `MIR1302-2HG`. |
| UMAP cell embeddings | `adata.obsm["X_umap"]` | Preserves the 17,974 x 2 UMAP coordinates. |
| Seurat object class/version/project | `adata.uns["seurat"]` | Stores simple provenance fields such as class `Seurat`, version `3.1.5`, and project name. |
| Seurat command summaries | `adata.uns["seurat"]["commands"]` | Stores the `NormalizeData.RNA` command name, timestamp, assay, call string, and parameters. |
| Seurat assay summaries | `adata.uns["seurat"]["assay_summaries"]` | Stores layer dimensions, sparse nonzero counts, and which AnnData layer each Seurat layer maps to. |
| Seurat tool names/classes | `adata.uns["seurat"]["tools"]` | Stores that `Integration` and `TransferData` existed, plus their parsed classes. |

### Not Fully Included In The AnnData File

| RDS / Seurat content | Conversion status | Why |
|---|---|---|
| full Seurat S4 object internals | not preserved losslessly | AnnData is not a Seurat S4 object. It cannot store every R slot in the same executable form. |
| full `tools$Integration` contents | summarized only | These are Seurat-specific internal objects. The script stores names/classes, not the full internal data. |
| full `tools$TransferData` contents | summarized only | Same reason as `Integration`; the internal object is not directly useful in standard AnnData workflows. |
| `graphs` | not included | This RDS has no stored graphs. |
| `neighbors` | not included | This RDS has no stored neighbor objects. |
| `images` | not included | This RDS has no spatial image data. |
| PCA embeddings/loadings | not included | This RDS does not store PCA. |
| integrated assay matrix | not included | The UMAP says it used `integrated`, but the object only stores the `RNA` assay. |
| variable feature list | not included as a meaningful list | `RNA@var.features` has length 0 in this RDS. |
| gene-level metadata | effectively empty | `RNA@meta.features` has 33,538 rows but zero columns. |
| chromosome names and coordinates | not included | The RDS stores gene names only. Use the hg38 GENCODE GTF for chromosome mapping. |
| sex, APOE genotype, diagnosis, age, PMI | not included | These fields are not present in the RDS metadata. They need an external `projid`-level metadata table. |
| original FASTQ/BAM/read-level data | not included | The RDS is a processed expression object, not raw sequencing data. |

Practical takeaway:

```text
The AnnData conversion preserves the expression matrices, cell labels, UMAP, and useful provenance summaries.
It does not preserve the R/Seurat object as a fully reversible object.
```

## Suggested Beginner Workflow

If you want to understand the file before doing analysis, inspect in this order:

1. Cell metadata.
2. Cell type counts.
3. Donor/sample counts by `projid`.
4. Gene names.
5. Raw counts matrix.
6. Normalized data matrix.
7. UMAP coordinates.
8. External metadata joins by `projid`.
9. External gene annotation joins by gene name.

This order keeps you oriented:

```text
Who are the cells?
What labels do they have?
Which donors/samples do they come from?
What genes were measured?
What expression values are available?
What visualization coordinates are available?
What external metadata do I need?
```

## Common Questions About This File

### Are there multiple samples?

Yes.

There are 423 unique `projid` values. This strongly indicates cells from many donors or samples.

### Are there multiple cell types?

Yes.

There are five high-resolution vascular cell type labels:

```text
End
Per
Fib FLRT2
SMC
Fib SLC4A4
```

### Is chromosome name stored in the RDS?

No.

The RDS stores gene names, but not chromosome names or genomic coordinates.

Use the hg38 GENCODE GTF file to map gene names to chromosomes.

### Is sex stored in the RDS?

No.

There is no `sex` metadata column in this object.

### Is APOE genotype stored in the RDS?

No.

There is no `APOE` metadata column in this object.

### Can I do sex or APOE analysis with this object alone?

Not with this object alone.

You need an external donor/sample metadata table that maps `projid` to sex, APOE genotype, diagnosis, and other covariates.

### Can I use this for cell-type expression analysis?

Yes.

The object has expression matrices and vascular cell type labels.

### Can I exactly reproduce the original full Seurat workflow?

Probably not from this object alone.

The object has normalized RNA data and UMAP, but it does not store PCA, neighbor graphs, clustering graphs, or the full integrated assay referenced by the UMAP.

### Which matrix should I use for pseudobulk?

Usually use raw counts:

```text
RNA@counts
```

For pseudobulk, you usually aggregate counts by donor/sample and cell type, for example by:

```text
projid + cell_type_high_resolution
```

### Which matrix should I use for visualization?

Usually use normalized data:

```text
RNA@data
```

For UMAP coordinates, use:

```text
reductions$umap@cell.embeddings
```

or after Python conversion:

```text
adata.obsm["X_umap"]
```

## Practical Interpretation For Your Project

Your project is to extend the Yu sex/APOE Alzheimer paper.

For that goal, this RDS is useful as a vascular-cell expression object, but it is not the full project dataset by itself.

You can use it to:

- Study vascular cell subtypes.
- Extract raw counts for vascular cells.
- Extract normalized expression for vascular cells.
- Group cells by `projid`.
- Group cells by vascular subtype.
- Convert to AnnData for Python workflows.
- Attach chromosome information using hg38 GENCODE annotation.

You still need external metadata to:

- Identify sex.
- Identify APOE genotype.
- Identify disease status.
- Use covariates such as age and PMI.
- Recreate paper-level comparisons.

The most important linking field appears to be:

```text
projid
```

## Minimal R Access Pattern

If using R with `SeuratObject`, the important pieces are:

```r
library(SeuratObject)

obj <- readRDS("data/processed/Vasculature_cells.rds")

counts <- obj@assays$RNA@counts
norm_data <- obj@assays$RNA@data
cell_metadata <- obj@meta.data
cell_types <- obj@active.ident
umap <- obj@reductions$umap@cell.embeddings
```

Basic checks:

```r
dim(counts)
dim(norm_data)
head(rownames(counts))
head(colnames(counts))
head(cell_metadata)
table(cell_metadata$cell_type_high_resolution)
length(unique(cell_metadata$projid))
dim(umap)
```

## Minimal Python Access Pattern

Using the installed project environment:

```python
import py8rds

rds_path = "data/processed/Vasculature_cells.rds"

robj = py8rds.parse_rds(rds_path)
adata = py8rds.seurat2adata(robj, assay="RNA", layer="counts")

print(adata.shape)
print(adata.obs.head())
print(adata.var_names[:10])
```

The project script does a more careful version of this and manually preserves UMAP:

```bash
.venv/bin/python scripts/inspect_rds_py8rds.py
```

## Glossary

| Term | Meaning |
|---|---|
| RDS | R's serialized single-object file format. |
| Seurat | R package and object format for single-cell analysis. |
| Seurat object | Container holding expression matrices, metadata, reductions, and analysis outputs. |
| S4 slot | A named field inside an R S4 object, accessed with `@`. |
| Assay | A group of matrices for one measurement type, here RNA expression. |
| Feature | Usually a gene in RNA-seq data. |
| Cell barcode | Identifier for a single cell or nucleus. |
| `counts` | Raw expression count matrix. |
| `data` | Normalized expression matrix. |
| `scale.data` | Scaled expression matrix, empty here. |
| Metadata | Per-cell annotation table. |
| `projid` | Donor/sample/project identifier attached to each cell. |
| `active.ident` | Seurat's current grouping labels for cells. |
| UMAP | Two-dimensional embedding used for visualization. |
| `dgCMatrix` | Sparse matrix format in R. |
| `csr_matrix` | Sparse matrix format in Python/SciPy. |
| AnnData | Python object format used by Scanpy and many single-cell tools. |
| `adata.obs` | AnnData table with one row per cell. |
| `adata.var` | AnnData table with one row per gene. |
| `adata.X` | AnnData expression matrix. |
| `adata.obsm` | AnnData storage for multidimensional cell-level arrays such as UMAP. |

## Bottom Line

This file is a compact saved Seurat object for 17,974 vascular cells and 33,538 genes. It contains raw counts, log-normalized expression, vascular subtype labels, donor/sample IDs, and UMAP coordinates. It does not contain clinical or genotype metadata, chromosome annotations, or the full original integration/clustering workflow.

For most next steps, think of it as:

```text
expression matrix + cell metadata + UMAP
```

with `projid` as the likely bridge to external sample-level metadata and hg38 GENCODE as the bridge from gene names to chromosome locations.
