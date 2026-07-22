# Pseudobulk Analysis Guide for the Alzheimer Mitochondria Project

## 1. What Pseudobulk Analysis Means

Single-nucleus RNA sequencing produces one expression profile for every nucleus. However, the nuclei are not the independent biological samples in this project. The independent samples are the human donors identified by `projid`.

Pseudobulk analysis combines the raw gene counts from nuclei belonging to the same donor and cell type. It creates one expression profile for each:

```text
projid x cell_type_high_resolution
```

For example, if donor `11409232` contributed 300 `Ast GRM3` nuclei, the raw counts for each gene are summed over those 300 nuclei:

```text
                         MT-ND1   MT-ND2   APOE   ...
11409232, Ast GRM3          420      310    900
another donor, Ast GRM3     275      190    650
third donor, Ast GRM3       510      440   1100
```

The result resembles a bulk RNA-seq count matrix, which explains the name *pseudobulk*. It remains cell-type-specific because astrocytes, immune cells, OPCs, and vascular subtypes are aggregated separately.

## 2. Why Donor-Level Aggregation Is Important

Nuclei from one donor share the same genetics, sex, APOE genotype, diagnosis, age, tissue collection, and many technical conditions. They are correlated observations rather than independent people.

This distinction is crucial:

```text
Incorrect interpretation:
10,000 nuclei = 10,000 independent biological samples

Correct interpretation:
10,000 nuclei from 40 donors = 40 independent biological samples
```

Treating all nuclei as independent can underestimate biological variability and produce overly small p-values. Pseudobulk preserves the donor as the unit of statistical inference while still allowing separate analyses for each fine cell type.

For this project, donor-aware pseudobulk should provide the primary differential-expression evidence. Cell-level MAST can be retained as a secondary analysis for comparison with Yu et al.

## 3. Are Raw Counts Required?

Yes. Standard pseudobulk differential-expression analysis requires the **raw UMI counts** stored in the Seurat `RNA` assay's `counts` slot or layer.

Raw counts in this context are the integer gene-by-cell values produced before cell-level normalization. They are not the same thing as raw sequencing files. Pseudobulk does **not** require:

- FASTQ files.
- BAM or CRAM files.
- Read alignment.
- Re-running Cell Ranger.
- A dense gene-by-cell matrix.

The required expression input is:

```r
counts <- GetAssayData(object, assay = "RNA", slot = "counts")
```

For the older Seurat object representation used by the local RDS files, the same matrix is stored at:

```r
counts <- object@assays$RNA@counts
```

The count matrix should be sparse, nonnegative, and integer-valued.

## 4. Verified Local Data

The four local Seurat objects were inspected directly. Every object contains a valid sparse `dgCMatrix` raw-count matrix. All nonzero values are finite, nonnegative integers.

| Local RDS file | Estimated disk size | Genes | Nuclei | Donors | Fine cell types | Raw counts |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `data/processed/Vasculature_cells.rds` | ~139 MB | 33,538 | 17,974 | 423 | 5 | Valid |
| `data/processed/Immune_cells.rds` | ~616 MB | 33,538 | 83,889 | 426 | 5 | Valid |
| `data/processed/OPCs.rds` | ~1.2 GB | 33,538 | 90,502 | 427 | 1 | Valid |
| `data/processed/Astrocytes.rds` | ~1.6 GB | 33,538 | 149,558 | 427 | 3 | Valid |

Together, these objects provide:

- 341,923 nuclei.
- 14 high-resolution cell types.
- Up to 427 donors.
- The same 33,538-gene feature space in every object.
- All 13 canonical mitochondrial protein-coding genes.
- `MT-ND2`, the principal mitochondrial candidate highlighted by Yu et al.

Each RDS contains these two essential cell-level metadata columns:

```text
projid
cell_type_high_resolution
```

The supporting metadata are also available locally:

| Local file | Estimated size | Pseudobulk role |
| --- | ---: | --- |
| `data/processed/dataset_707_basic_02-08-2022.clean.txt` | ~2.7 MB | Checksum-frozen Yu clinical source supplying diagnosis, sex, APOE genotype, exact uncensored age at death, and PMI. |
| `data/processed/cell.meta.data.tsv` | ~168 MB | Supplies master cell barcodes, RNA counts, detected features, clusters, and fine/broad cell types. |

The clinical file has already been checked against the 427 donor IDs in the cell metadata. After normalizing `projid` to an eight-character string, all 427 donors match. Its SHA-256 is `76a71814b43c9fa3e84b9bbb119dddc3fd4b08743948f75ca38400e9bcb7425e`.

## 5. Is the Local Data Sufficient?

### Sufficient for the current pilot

The local repository contains enough data to perform a complete donor-level pseudobulk pilot for:

- Astrocytes.
- Immune cells.
- OPCs.
- Vascular cells.
- Fourteen fine cell types in total.
- AD-versus-NCI comparisons within the six sex-APOE groups used by Yu et al.
- Diagnosis-by-sex and diagnosis-by-APOE interaction tests.
- Mitochondrial gene and pathway analysis.

With six paper-matched AD-versus-NCI contrasts and 14 fine cell types, the current data support at most 84 cell-type-specific contrasts. Some will be ineligible if too few donors remain after minimum-cell filtering.

### Not sufficient for all 54 fine cell types

The full Yu-style analysis requires five additional cell-class RDS inputs:

- Three excitatory-neuron RDS sets, approximately 21.3 GB combined.
- Inhibitory neurons, approximately 5.2 GB.
- Oligodendrocytes, approximately 5.0 GB.

These missing inputs total approximately 31.5 GB. Until they are added locally, the project can analyze 14 rather than all 54 fine cell types.

The local data also do not currently provide an obvious sequencing-batch field in the four RDS metadata tables. Batch metadata would be useful for a sensitivity analysis, but it is not required to construct pseudobulk counts.

## 6. Pseudobulk Versus Seurat `NormalizeData`

These are two different workflows with different inputs.

### Pseudobulk differential expression

```text
raw cell-level counts
    -> sum counts by projid and fine cell type
    -> donor-by-gene pseudobulk count matrix
    -> edgeR/DESeq2 library normalization
    -> donor-level statistical model
```

Do not sum Seurat `NormalizeData` values. edgeR and DESeq2 expect raw pseudobulk counts and perform their own library-size normalization.

### Seurat cell-level analysis

```text
raw cell-level counts
    -> Seurat NormalizeData
    -> normalized cell-level expression
    -> MAST, plots, or exploratory cell-level scores
```

`NormalizeData` remains appropriate for:

- Paper-comparable MAST testing.
- Violin and feature plots.
- Cell-level mitochondrial expression visualization.
- Exploratory module scores.

The two branches can coexist:

| Analysis branch | Input | Main purpose |
| --- | --- | --- |
| Pseudobulk edgeR/DESeq2 | Raw counts summed by donor and cell type | Primary donor-aware inference |
| Seurat MAST | Cell-level `NormalizeData` expression | Comparison with Yu et al. |
| Seurat plots and scores | Cell-level `NormalizeData` expression | Visualization and exploration |

## 7. Required Inputs for Each Pseudobulk Sample

Every pseudobulk column should have:

- A normalized eight-character `projid`.
- One `cell_type_high_resolution` value.
- Number of contributing nuclei.
- Total raw UMI count.
- Diagnosis: NCI or AD.
- Sex: female or male.
- Original APOE genotype and derived APOE group.
- Age-at-death covariate.
- PMI covariate.
- Batch, if it becomes available and is suitable for modeling.

Normalize `projid` before joining clinical data:

```r
normalize_projid <- function(x) {
  stringr::str_pad(as.character(x), width = 8, side = "left", pad = "0")
}
```

Never rely on row order when joining donor metadata. Match using the normalized `projid` key and require exactly one clinical record per donor.

## 8. Memory-Conscious Local Workflow

The local machine has approximately:

- 15 GiB total RAM.
- Approximately 11 GiB available during inspection.
- 4 GiB swap.
- Approximately 393 GB available disk space.

Disk space is adequate for the four current inputs. RAM is the main constraint. The approximately 1.6 GB Astrocytes RDS occupied approximately 8.2 GB after being loaded into R.

Use these rules:

1. Run exactly one RDS per fresh `Rscript` process.
2. Start with the approximately 139 MB Vasculature object.
3. Extract only raw counts and the two required metadata columns.
4. Remove the full Seurat object and run `gc()` before aggregation.
5. Keep all matrices sparse.
6. Never call `as.matrix()` on a full gene-by-cell matrix.
7. Do not run full-object `ScaleData` over all genes.
8. Save the compact pseudobulk counts and sample metadata, then exit R.
9. Process the next RDS in a new process.
10. Monitor peak memory with `/usr/bin/time -v`.

A safe extraction pattern is:

```r
suppressPackageStartupMessages(library(Matrix))

object <- readRDS(input_rds)
counts <- object@assays$RNA@counts
cell_metadata <- object@meta.data[, c(
  "projid",
  "cell_type_high_resolution"
), drop = FALSE]

stopifnot(identical(colnames(counts), rownames(cell_metadata)))

rm(object)
gc()
```

Removing the complete Seurat object releases stored reductions, normalized data, tools, commands, and other material that is not needed for pseudobulk construction. The raw sparse counts and minimal metadata remain available.

## 9. Constructing Pseudobulk Counts Efficiently

The basic operation is to sum raw counts for all nuclei sharing a donor and fine cell type.

### Step 1: Create the aggregation group

```r
cell_metadata$projid <- normalize_projid(cell_metadata$projid)

aggregation_group <- interaction(
  cell_metadata$projid,
  cell_metadata$cell_type_high_resolution,
  sep = "__",
  drop = TRUE
)
```

### Step 2: Create a sparse cell-to-group matrix

```r
group_matrix <- Matrix::sparse.model.matrix(
  ~ 0 + aggregation_group
)
colnames(group_matrix) <- levels(aggregation_group)
```

This matrix has one row per nucleus and one column per donor-cell-type combination. Each row has one nonzero value indicating its pseudobulk group.

### Step 3: Sum counts with sparse matrix multiplication

```r
pseudobulk_counts <- counts %*% group_matrix
```

The dimensions change from:

```text
genes x nuclei
```

to:

```text
genes x donor-cell-type samples
```

### Step 4: Count contributing nuclei

```r
nuclei_per_sample <- as.integer(table(aggregation_group))
names(nuclei_per_sample) <- levels(aggregation_group)
```

### Step 5: Build sample metadata

For each pseudobulk column, create one metadata row containing its `projid`, fine cell type, nuclei count, total UMI count, and joined clinical variables.

Always verify:

```r
stopifnot(ncol(pseudobulk_counts) == nrow(pseudobulk_metadata))
stopifnot(identical(colnames(pseudobulk_counts), rownames(pseudobulk_metadata)))
stopifnot(!anyDuplicated(rownames(pseudobulk_metadata)))
```

## 10. Minimum Cell and Donor Requirements

A donor with only a few nuclei in a fine cell type may have an unstable pseudobulk profile. Use prespecified eligibility rules rather than choosing thresholds after seeing p-values.

Recommended initial rules:

- Primary threshold: at least 20 nuclei per donor and fine cell type.
- Sensitivity threshold: at least 50 nuclei per donor and fine cell type.
- Minimum for formal comparison: at least five eligible donors in both NCI and AD.
- Prefer at least ten donors per side when available.

The male APOE epsilon2 group begins with only 6 NCI and 7 AD donors. Some fine cell types will therefore be descriptive only after minimum-cell filtering.

For every contrast, report:

- Number of NCI and AD donors.
- Number of contributing nuclei.
- Median nuclei per donor.
- Number of genes passing expression filters.
- Any donors removed by eligibility rules.

## 11. Differential-Expression Model

For each fine cell type, analyze the pseudobulk raw-count matrix with edgeR, DESeq2, or a similarly justified count-based method. edgeR quasi-likelihood is a reasonable primary choice.

Create a combined group representing diagnosis, sex, and APOE:

```r
pseudobulk_metadata$group <- interaction(
  pseudobulk_metadata$diagnosis,
  pseudobulk_metadata$sex,
  pseudobulk_metadata$apoe_group,
  sep = "_",
  drop = TRUE
)
```

An edgeR-style workflow is:

```r
library(edgeR)

y <- DGEList(counts = pseudobulk_counts)

keep <- filterByExpr(
  y,
  group = pseudobulk_metadata$group
)
y <- y[keep, , keep.lib.sizes = FALSE]

y <- calcNormFactors(y, method = "TMM")

design <- model.matrix(
  ~ 0 + group + age_scaled + pmi_scaled,
  data = pseudobulk_metadata
)

y <- estimateDisp(y, design, robust = TRUE)
fit <- glmQLFit(y, design, robust = TRUE)
```

The six paper-matched AD-versus-NCI contrasts are:

1. Female APOE epsilon2: AD versus NCI.
2. Female APOE epsilon3/epsilon3: AD versus NCI.
3. Female APOE epsilon4: AD versus NCI.
4. Male APOE epsilon2: AD versus NCI.
5. Male APOE epsilon3/epsilon3: AD versus NCI.
6. Male APOE epsilon4: AD versus NCI.

The model should also directly test interaction contrasts when claiming that AD effects differ by sex or APOE. Significance in one group and nonsignificance in another is not itself evidence that the two groups differ.

## 12. Mitochondrial Analysis After Aggregation

The pseudobulk matrix contains the same 33,538 genes as the source object before gene filtering. It can support several mitochondrial analyses:

### mtDNA-encoded genes

Analyze the 13 measured mitochondrial protein-coding genes, including `MT-ND2`, while reporting donor-level detection and count coverage.

### Nuclear-encoded mitochondrial genes

Intersect the measured genes with Human MitoCarta3.0. MitoCarta is not needed to construct pseudobulk counts, but it is needed to define the broader mitochondrial gene and pathway sets.

### Pathway analysis

Use genome-wide signed differential-expression statistics to test:

- OXPHOS complexes I-V.
- Electron transport and respirasome assembly.
- Mitochondrial translation and ribosome.
- mtDNA maintenance and transcription.
- Mitophagy, fusion, and fission.
- Reactive oxygen species pathways.
- Mitochondrial protein import and stress responses.

### Mitochondrial read fraction

Analyze mitochondrial UMI fraction as a separate donor-level outcome. Do not treat it as interchangeable with OXPHOS or mitochondrial pathway expression.

## 13. Suggested Output Files

The following outputs do not yet exist. Their sizes are planning estimates and will vary with compression and filtering:

| Planned output file | Estimated size | Contents |
| --- | ---: | --- |
| `results/pseudobulk/Vasculature_cells_pseudobulk.rds` | ~20-200 MB | Raw pseudobulk counts and sample metadata for 5 fine cell types. |
| `results/pseudobulk/Immune_cells_pseudobulk.rds` | ~50-500 MB | Raw pseudobulk counts and sample metadata for 5 fine cell types. |
| `results/pseudobulk/OPCs_pseudobulk.rds` | ~20-200 MB | Raw pseudobulk counts and sample metadata for OPCs. |
| `results/pseudobulk/Astrocytes_pseudobulk.rds` | ~30-300 MB | Raw pseudobulk counts and sample metadata for 3 fine cell types. |
| `results/pseudobulk/pseudobulk_sample_metadata.tsv` | ~0.1-5 MB | Donor-cell-type sample metadata and eligibility fields. |
| `results/de/pseudobulk_de_results.tsv.gz` | ~10-500 MB | Complete gene-level effects and statistics for all estimable contrasts. |
| `results/pathways/mitochondrial_pathway_results.tsv` | ~0.1-20 MB | MitoCarta and other mitochondrial pathway tests. |

Keep raw pseudobulk counts unchanged after creation. Save filtered count matrices or normalized expression under different filenames so they cannot be confused with the raw aggregated counts.

## 14. Advantages and Limitations

### Advantages

- Uses donors as independent biological replicates.
- Reduces pseudoreplication and false-positive risk.
- Retains fine-cell-type specificity.
- Supports diagnosis, sex, APOE, age, PMI, batch, and interaction terms.
- Uses established bulk RNA-seq statistical methods.
- Produces much smaller matrices after aggregation.
- Avoids the need to save another full normalized Seurat object for the primary analysis.

### Limitations

- Summarizes expression within each donor and cell type.
- Does not model cell-to-cell variability within a donor.
- Cannot directly detect subpopulations hidden within a fine cell type.
- Requires enough nuclei and donors for every tested cell type.
- Rare cell types and the male APOE epsilon2 group may remain underpowered.
- Still requires loading each source RDS at least once unless an on-disk conversion is introduced.

Pseudobulk and cell-level methods answer related but different questions. Agreement between donor-level pseudobulk and paper-comparable MAST is stronger evidence than either method alone.

## 15. Practical Checklist

Before aggregation:

- Confirm `RNA@counts` exists.
- Confirm counts are sparse, nonnegative, and integer-valued.
- Confirm count columns exactly match metadata rows.
- Normalize `projid` to eight characters.
- Confirm fine cell-type labels are present.
- Confirm every retained donor joins to one clinical record.

After aggregation:

- Confirm total counts are conserved across aggregation.
- Confirm one column exists per donor-cell-type combination.
- Confirm nuclei counts per pseudobulk sample.
- Remove or flag samples below the prespecified nucleus threshold.
- Confirm clinical metadata are complete.
- Confirm NCI and AD donor counts before fitting each contrast.
- Save raw pseudobulk counts before filtering or normalization.

Before reporting results:

- Treat donor count, not nucleus count, as sample size.
- Report effect sizes and confidence intervals.
- Apply the declared multiple-testing correction.
- Test interactions directly for sex or APOE differences.
- Verify that top effects are not driven by one donor.
- Compare important findings with MAST and sensitivity analyses.
- Describe RNA-expression changes as evidence about mitochondrial programs, not direct proof of altered mitochondrial function.

## Bottom Line

The local repository already contains the raw UMI counts and metadata required for donor-level pseudobulk analysis of 341,923 nuclei across 14 fine cell types. Construct each pseudobulk matrix by summing sparse raw counts within `projid` and `cell_type_high_resolution`, join the donor clinical metadata, and use edgeR or DESeq2 for donor-level normalization and statistical testing. Seurat `NormalizeData` should be used separately for MAST and cell-level visualization, not as the input to pseudobulk count models. The current data are sufficient for a meaningful four-cell-class pilot but not yet for the complete 54-cell-type analysis.
