# Data availability and download plan

Last checked: 2026-07-03.

No dataset files were downloaded while preparing these notes. Synapse sizes and folder contents below were checked from metadata only.

## Recommendation for reproducing Yu et al.

For reproducing the main analyses in [`Yu_sex_apoe.pdf`](Yu_sex_apoe.pdf), download the processed prefrontal-cortex 10x snRNA-seq data and the metadata. Do not download the full `syn52293417` tree unless there is a separate reason to reproduce raw-data processing or analyze other assays.

Minimum Synapse targets:

| Synapse ID | Purpose | Approximate size |
| --- | --- | ---: |
| `syn52293433` | Processed PFC 10x snRNA-seq expression objects | 130.91 GiB |
| `syn52293430` | Study metadata folder | 393.72 MiB total, with direct metadata files around 1.13 MiB |

The paper's Methods say it used Mathys et al. ROSMAP preprocessed read-count data from the prefrontal cortex, covering 2.3 million nuclei from 427 participants and 54 high-resolution cell types. The main analysis compares AD versus no cognitive impairment within sex and APOE genotype strata. It does not require raw FASTQs/BAMs, snATAC-seq, or multiome data.

## Processed expression files

Download `syn52293433`: `Gene Expression (snRNAseq - 10x) processed`.

This folder contains:

| Synapse ID | File | Notes |
| --- | --- | --- |
| `syn52392369` | `PFC427_raw_data.h5ad` | PFC 427-participant processed AnnData object; useful for Python/Scanpy workflows. |
| `syn52368912` | `Astrocytes.rds` | Seurat/R object. |
| `syn52368925` | `Excitatory_neurons_set1.rds` | Seurat/R object. |
| `syn52368950` | `Excitatory_neurons_set2.rds` | Seurat/R object. |
| `syn52368932` | `Excitatory_neurons_set3.rds` | Seurat/R object. |
| `syn52368905` | `Immune_cells.rds` | Seurat/R object. |
| `syn52368921` | `Inhibitory_neurons.rds` | Seurat/R object. |
| `syn52368910` | `OPCs.rds` | Seurat/R object. |
| `syn52368918` | `Oligodendrocytes.rds` | Seurat/R object. |
| `syn52368904` | `Vasculature_cells.rds` | Seurat/R object. |

The Yu paper used Seurat `FindMarkers`/MAST for cell-cluster-specific differential expression. For an R/Seurat reproduction, the `.rds` files are the most natural starting point. For a Python/Scanpy reproduction, start from `PFC427_raw_data.h5ad`. The `.h5ad` and `.rds` objects may be partly redundant, so the exact choice depends on the analysis stack.

## Metadata files

Download `syn52293430`: `Metadata`.

The likely minimum metadata files are:

| Synapse ID | File | Why it matters |
| --- | --- | --- |
| `syn52368902` | `MIT_ROSMAP_Multiomics_assay_snRNAseq_metadata` | snRNA-seq assay/sample metadata. |
| `syn52430346` | `MIT_ROSMAP_Multiomics_individual_metadata.csv` | Donor-level metadata, likely including diagnosis, sex, APOE, age, and related covariates. |
| `syn52430345` | `MIT_ROSMAP_Multiomics_biospecimen_metadata.csv` | Biospecimen/sample mapping metadata. |

The metadata must support the paper's filtering and covariates:

- Cognitive diagnosis group: NCI versus AD.
- APOE genotype: epsilon2/epsilon2 and epsilon2/epsilon3 as epsilon2 carriers, epsilon3/epsilon3 as the reference group, and epsilon3/epsilon4 plus epsilon4/epsilon4 as epsilon4 carriers.
- Sex.
- Post-mortem interval (PMI).
- Age at death.
- Total RNA counts / `nCount_RNA`, usually stored in the expression object metadata.
- Sample or donor IDs for joining expression objects to donor metadata.

The paper excluded MCI and other dementia samples, APOE epsilon2/epsilon4 samples, samples missing APOE genotype, samples missing PMI, and four samples with inconsistent reported sex versus sex-linked gene expression.

## Optional downloads

These are not required for the main PFC snRNA-seq reproduction, but may be useful depending on scope:

| Synapse ID / source | Purpose | Approximate size |
| --- | --- | ---: |
| `syn52383412` | Processed multi-region 10x snRNA-seq | 74.46 GiB |
| Wiley Supporting Information for Yu et al. | Tables S1-S6, Figure S1/S2, and published result tables | Small |
| MSigDB C2:CP gene sets | Pathway enrichment input used in the paper | Small |
| Prior MSBB/ROSMAP bulk RNA-seq DEG resources | Only needed to reproduce the validation comparison described in Section 2.5 | Varies |

## Data to skip for this reproduction

Skip these unless the goal expands beyond reproducing the paper's main processed PFC snRNA-seq analyses:

| Synapse ID | Folder | Size | Reason to skip |
| --- | --- | ---: | --- |
| `syn52293432` | Gene Expression (snRNAseq - 10x) raw | 7.38 TiB | Raw-data processing is not part of the described main analysis. |
| `syn52383413` | Gene Expression (snRNAseq - 10x) raw, multi-region | 5.70 TiB | Raw and multi-region. |
| `syn52558407` | Gene Expression (snRNAseq - Smart-seq2) | 180.84 GiB | The paper used the Mathys PFC snRNA-seq atlas, not Smart-seq2 as the main input. |
| `syn52564357` | Epigenetics | 1.36 TiB | snATAC-seq is not used in the main paper. |
| `syn52335508` | Multiome | 603.30 GiB | Multiome is not used in the main paper. |
| `syn66271521` | Multiregion Epigenetics (snATAC-seq) | 2.80 TiB | Not used in the main paper. |
| `syn66271522` | Multiregion Multiome | 1.64 TiB | Not used in the main paper. |

## Download commands

Do not run these commands until download approval is granted.

Install and configure the Synapse client:

```bash
pip install --upgrade synapseclient
synapse config
```

Alternatively, log in for one session with a personal access token:

```bash
synapse login -p "$MY_SYNAPSE_TOKEN"
```

Recommended folder-level downloads:

```bash
synapse get -r syn52293433 --downloadLocation /path/to/MIT_ROSMAP_processed_10x --manifest root
synapse get -r syn52293430 --downloadLocation /path/to/MIT_ROSMAP_metadata --manifest root
```

If you only want the most likely minimum files rather than the full processed and metadata folders:

```bash
synapse get syn52392369 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368912 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368925 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368950 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368932 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368905 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368921 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368910 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368918 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368904 --downloadLocation /path/to/MIT_ROSMAP_processed_10x
synapse get syn52368902 --downloadLocation /path/to/MIT_ROSMAP_metadata
synapse get syn52430346 --downloadLocation /path/to/MIT_ROSMAP_metadata
synapse get syn52430345 --downloadLocation /path/to/MIT_ROSMAP_metadata
```

At the time of checking, the `synapse` command-line client was not installed on this machine.

## Access requirements

The snRNA-seq data are publicly available for research use, but mostly through controlled access rather than unrestricted anonymous download.

You will likely need:

- A Synapse account.
- An approved Data Use Certificate / data use agreement for controlled human data.
- Possibly separate access to some ROSMAP clinical or phenotypic metadata through RADC, depending on what variables are needed.

In plain terms: the data can be obtained, but it probably cannot be downloaded instantly without account-level and controlled-access approval. For exploratory viewing, the UCSC Cell Browser / processed companion resources may be easier. For full raw counts plus linked donor metadata, use Synapse `syn52293417` and submit the required DUC.

## Dataset source

The Yu et al. paper did not generate a new snRNA-seq dataset. It reanalyzed the large Mathys et al. ROSMAP prefrontal cortex snRNA-seq atlas, which contains about 2.3 million nuclei from 427 ROSMAP participants.

Key access point:

| Field | Value |
| --- | --- |
| Portal | AD Knowledge Portal / Synapse |
| Study / folder | `MIT_ROSMAP_Multiomics` |
| Synapse ID | [`syn52293417`](https://www.synapse.org/Synapse:syn52293417) |

The AD Knowledge Portal release notes say the `MIT_ROSMAP_Multiomics` study provides single-nucleus RNA-seq, single-nucleus ATAC-seq, and multiome data from 427 prefrontal cortex samples, along with additional multi-region snRNA-seq data. A FunGen-AD resource page also identifies the primary data release as Synapse `syn52293417` and describes it as ROSMAP single-nucleus RNA-seq expression data from 427 donors generated by the MIT Kellis lab.

There is also a Mathys/MIT companion site. It says the complete human raw data are released through Synapse `syn52293417`, while the data and human metadata require access through Synapse with a Data Use Certificate, or DUC. The same site also links de-identified processed datasets, processed count matrices, cell-type tables, metadata files, and an interactive UCSC Cell Browser visualization.

## Full Synapse size context

`syn52293417` is a folder, not a single file. A recursive Synapse metadata enumeration reported:

- Recursive size: `21,824,858,191,529` bytes.
- Human-readable size: about `21.8 TB` decimal / `19.85 TiB`.
- Files seen in folder pages: about `14,163`.

Largest subfolders:

| Synapse ID | Folder | Size |
| --- | --- | ---: |
| `syn52564358` | Gene Expression | 13.46 TiB |
| `syn66271521` | Multiregion Epigenetics (snATAC-seq) | 2.80 TiB |
| `syn66271522` | Multiregion Multiome | 1.64 TiB |
| `syn52564357` | Epigenetics | 1.36 TiB |
| `syn52335508` | Multiome | 603.30 GiB |
| `syn52293430` | Metadata | 393.72 MiB |

Important Gene Expression subfolders:

| Synapse ID | Folder | Size |
| --- | --- | ---: |
| `syn52293432` | Gene Expression (snRNAseq - 10x) raw | 7.38 TiB |
| `syn52383413` | Gene Expression (snRNAseq - 10x) raw, multi-region | 5.70 TiB |
| `syn52558407` | Gene Expression (snRNAseq - Smart-seq2) | 180.84 GiB |
| `syn52293433` | Gene Expression (snRNAseq - 10x) processed | 130.91 GiB |
| `syn52383412` | Gene Expression (snRNAseq - 10x) processed, multi-region | 74.46 GiB |

The full download, after account/DUC approval and explicit download approval, would require a location with more than 20 TiB free:

```bash
synapse get -r syn52293417 --downloadLocation /path/with/25TB_free --manifest root
```

## Metadata method used

The size estimate was computed without downloading data by recursively querying Synapse folder metadata. The useful REST API field is `includeSumFileSizes`, documented in Synapse's [`EntityChildrenRequest`](https://rest-docs.synapse.org/rest/org/sagebionetworks/repo/model/EntityChildrenRequest.html) and [`EntityChildrenResponse`](https://rest-docs.synapse.org/rest/org/sagebionetworks/repo/model/EntityChildrenResponse.html).

Relevant Synapse documentation:

- [Synapse Python/command-line client installation](https://python-docs.synapse.org/en/stable/tutorials/installation/)
- [Synapse authentication](https://python-docs.synapse.org/en/stable/tutorials/authentication/)
- [Synapse command-line client](https://python-docs.synapse.org/en/stable/tutorials/command_line_client/)
- [Downloading data in bulk](https://python-docs.synapse.org/en/stable/tutorials/python/download_data_in_bulk/)
