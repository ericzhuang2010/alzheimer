# SEA-AD Dataset Contents and Validation Notes

The two files are two representations of the same SEA-AD dataset—not two independent datasets.

| File | Contents |
|---|---|
| [SEAAD H5AD](/home/ericzhuang2010/VscodeProjects/alzheimer/data/SEAAD_A9_RNAseq_final-nuclei.2024-02-13.h5ad) | 35.3 GiB AnnData object containing expression, raw UMIs, metadata, annotations, embeddings, and neighbor graphs |
| [SEAAD metadata CSV](/home/ericzhuang2010/VscodeProjects/alzheimer/data/SEAAD_A9_RNAseq_final-nuclei_metadata.2024-02-13.csv) | 1.35 GiB export of the H5AD’s per-nucleus metadata; no gene-expression columns |

## Dataset contents

- Title embedded in the file: “DLPFC: Seattle Alzheimer’s Disease Atlas (SEA-AD).”
- Tissue: human dorsolateral prefrontal cortex, all cortical layers.
- 1,395,601 nuclei from 83 donors and 202 libraries.
- 36,601 genes on GRCh38.
- 7,989,685,110 stored expression entries.
- All nuclei have `Used in analysis = True`, indicating this is an already quality-controlled dataset.

Donor composition:

- 48 female and 35 male donors.
- Age at death available for 80 donors: 68–102 years, median 90.5.
- 80 aging/AD study donors plus 3 neurotypical reference donors.
- Cognitive status: 39 dementia, 41 no dementia, 3 reference.
- AD neuropathologic change: 39 high, 20 intermediate, 12 low, 9 not AD, 3 reference.
- APOE genotypes are included; the most common are `3/3` (45 donors) and `3/4` (17 donors).
- Detailed Braak, Thal, CERAD, CAA, Lewy body, LATE, vascular pathology, cognitive-score, PMI, education, race, and study metadata are present.

The cohort is predominantly recorded as White—77 of the 83 donors—which is relevant to how broadly validation results can be generalized.

## Cell types

There are three broad classes:

- Glutamatergic neurons: 660,751 nuclei, 47.3%.
- GABAergic neurons: 422,449 nuclei, 30.3%.
- Non-neuronal/non-neural cells: 312,401 nuclei, 22.4%.

Annotations include 24 subclasses and 131 finer supertypes. They cover:

- Excitatory populations such as L2/3 IT, L4 IT, L5 IT, L6 IT, L6 CT and L6b.
- Inhibitory populations such as Pvalb, Vip, Sst, Lamp5, Sncg and Chandelier.
- Oligodendrocytes, astrocytes, microglia/PVM, OPCs, endothelial cells and VLMCs.

The largest individual subclasses are L2/3 IT (341,960), oligodendrocytes (145,995), Pvalb (116,142), L5 IT (104,106), Vip (100,215), and astrocytes (87,444).

## Expression representation

The H5AD contains:

- `X`: natural-log normalized expression, specifically `ln(UMIs per 10,000 + 1)`.
- `layers["UMIs"]`: the corresponding raw UMI counts, stored as float32 but containing integer-valued counts.
- Median per nucleus: 19,221 UMIs and 5,652 detected genes.
- Median mitochondrial fraction: 0.13%.
- `obsm["X_scVI"]`: a 20-dimensional scVI latent representation.
- `obsm["X_umap"]`: two-dimensional UMAP coordinates.
- Precomputed cell-cell connectivity and distance graphs.

The gene index consists of unique gene symbols. The `gene_ids` column repeats those symbols rather than supplying Ensembl IDs, so gene harmonization with another dataset will need to be symbol-based or performed using an external annotation.

The file also includes Multiome/ATAC quality metrics for 86,187 nuclei, but it does not contain an ATAC peak-by-cell matrix. It is fundamentally an RNA expression object.

## Metadata CSV

The CSV has:

- 1,395,602 lines: one header plus exactly 1,395,601 nuclei.
- 133 columns.
- The exact same column names and ordering as `adata.obs` in the H5AD.
- Matching first and last nucleus identifiers, confirming alignment with the H5AD.

Its fields fall into four broad groups:

- Donor clinical and neuropathological information.
- Sample, library, chemistry, FACS, and sequencing information.
- Per-nucleus QC metrics.
- Cell class, subclass, supertype, and annotation confidence.

Therefore, you generally do not need to merge this CSV back into the H5AD—the metadata is already embedded there.

## Most important implication for validation

This is a strong independent human AD validation cohort, but the independent biological sample size is 83 donors, not 1.4 million nuclei. Validation should normally use donor-by-cell-type pseudobulk profiles from `layers["UMIs"]`, while modeling sex, age, study/chemistry, and pathology definition as appropriate. Avoid treating individual nuclei as independent replicates.
