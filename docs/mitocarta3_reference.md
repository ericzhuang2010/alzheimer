# Human MitoCarta3.0 reference

Last checked: 2026-07-11.

## What Human MitoCarta3.0 is

[Human MitoCarta3.0](https://www.broadinstitute.org/mitocarta/mitocarta30-inventory-mammalian-mitochondrial-proteins-and-pathways) is a curated reference inventory of 1,136 human genes whose encoded proteins have strong support for mitochondrial localization. It is a gene and protein annotation resource, not an expression dataset, disease cohort, or measurement of mitochondrial activity.

The inventory combines experimental and computational evidence, including mitochondrial proteomics, GFP localization, proximity labeling, mitochondrial targeting-sequence prediction, homology, protein-domain evidence, coexpression, and manual literature review. Its annotations include:

- Official gene symbols, descriptions, synonyms, and identifiers.
- Evidence and integrated scores supporting mitochondrial localization.
- Protein detection across 14 tissues.
- Sub-mitochondrial localization, such as matrix, inner mitochondrial membrane, intermembrane space, and outer mitochondrial membrane.
- Membership in 149 manually curated, hierarchical `MitoPathways`.

The 1,136-gene inventory includes both nuclear-encoded and mitochondrial-DNA-encoded protein genes. Because the mitochondrial genome encodes 13 proteins, the inventory contains approximately 1,123 nuclear-encoded genes plus those 13 mtDNA-encoded genes.

MitoCarta is intended to describe the mitochondrial proteome. It is more specific than a broad list of every gene that regulates, interacts with, or responds to mitochondria, and it does not by itself establish that a protein is active in a particular brain cell type.

## Official source and downloads

The resource is maintained by the Broad Institute and is freely available from its MitoCarta site:

- [MitoCarta3.0 project and download page](https://www.broadinstitute.org/mitocarta/mitocarta30-inventory-mammalian-mitochondrial-proteins-and-pathways)
- [Human MitoCarta3.0 inventory spreadsheet](https://personal.broadinstitute.org/scalvo/MitoCarta3.0/Human.MitoCarta3.0.xls)
- [Human MitoPathways3.0 gene sets](https://personal.broadinstitute.org/scalvo/MitoCarta3.0/Human.MitoPathways3.0.gmx)
- [MitoCarta3.0 column documentation](https://www.broadinstitute.org/mitocarta30-documentation)
- [MitoCarta3.0 publication](https://doi.org/10.1093/nar/gkaa1011)

The Excel workbook is the primary source for this project because it contains the human inventory, localization evidence, sub-mitochondrial compartments, pathway assignments, and genome-wide localization scores. The GMX file is a convenient alternative when only pathway gene sets are needed for tools such as GSEA.

## Download step in this project

Phase C of [`mitochondria_sex_apoe_research_plan.md`](mitochondria_sex_apoe_research_plan.md#10-phase-c-freeze-mitochondrial-gene-and-pathway-annotations) downloads and freezes the official spreadsheet before disease-effect testing:

```bash
mkdir -p data/reference
wget -O data/reference/Human.MitoCarta3.0.xls \
  https://personal.broadinstitute.org/scalvo/MitoCarta3.0/Human.MitoCarta3.0.xls
```

The downloaded source should remain unchanged. Record its source URL, download date, file size, and checksum in the annotation manifest. For example:

```bash
sha256sum data/reference/Human.MitoCarta3.0.xls
```

The plan then calls the annotation-building script:

```bash
Rscript scripts/03_build_mito_annotations.R \
  --config config/local_pilot.yml \
  --features results/local_pilot/01_audit/Vasculature_cells.features.tsv.gz
```

That script is planned to create analysis-ready gene, pathway, alias, and provenance tables from the frozen workbook. The research plan downloads the Excel workbook directly and derives its pathway table locally; downloading the separate GMX file is therefore optional, although it can be retained as a cross-check.

## How it is used in the Alzheimer analysis

The project uses MitoCarta for two related purposes:

1. Define the set of nuclear-encoded mitochondrial genes measurable in each Seurat object.
2. Define mitochondrial pathway gene sets for pathway-level testing, including OXPHOS complexes, mitochondrial translation, mtDNA maintenance, protein import, mitophagy, dynamics, reactive-oxygen-species defense, and mitochondrial metabolism.

The workflow should intersect MitoCarta gene symbols with each Seurat object's row names and report matched, unmatched, duplicated, and alias-resolved symbols. A MitoCarta gene that is absent or insufficiently expressed in an object must not be treated as tested.

The 13 mtDNA-encoded protein genes are analyzed as a separate prespecified family. They should therefore be removed from the nuclear-encoded MitoCarta set when constructing mutually exclusive gene categories, while remaining available in analyses of the complete mitochondrial proteome. This avoids double-counting the same genes.

MitoCarta annotations identify mitochondrial genes and pathways, but RNA abundance does not directly measure respiration, ATP production, membrane potential, mtDNA copy number, heteroplasmy, or other mitochondrial functions. Results should consequently be described as mitochondrial gene-expression or pathway-expression changes rather than direct changes in mitochondrial function.

## Recommended provenance checks

Before analysis, verify that:

- The inventory contains 1,136 unique expected human entries after documented identifier handling.
- All 13 canonical mtDNA protein genes are accounted for.
- The nuclear-only and mtDNA-only sets do not overlap.
- MitoPathway membership is preserved as a many-to-many relationship because one gene may belong to multiple pathways.
- Gene-symbol aliases and duplicates are resolved reproducibly without silently discarding entries.
- The original workbook checksum and all derived-file checksums are recorded.
- The same frozen annotation files are used in all three execution phases.
