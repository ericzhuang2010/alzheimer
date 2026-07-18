# Phase 2: Annotate Mitochondrial Genes

## Purpose of this phase

The **mitochondrial annotation phase is not another differential-expression test**. It is a data-integration step in which we attach biological information to every gene in the differential-expression results.

Conceptually:

```text
All-gene MAST results
        +
Gene identifiers from the snRNA-seq dataset
        +
A curated mitochondrial gene database
        ->
Annotated all-gene DEG table
```

For example, before annotation you may have:

| Gene | Cell cluster | Contrast | log2FC | Adjusted p value |
|---|---|---|---:|---:|
| MT-ND2 | Exc L5 ET | F_e4x AD vs NCI | -0.45 | 0.012 |
| NDUFS1 | Exc L5 ET | F_e4x AD vs NCI | -0.19 | 0.11 |
| CLU | Exc L5 ET | F_e4x AD vs NCI | -0.31 | 0.020 |

After annotation, the table would tell us that:

- **MT-ND2** is encoded by mitochondrial DNA and belongs to respiratory-chain Complex I.
- **NDUFS1** is encoded by nuclear DNA, but its protein functions inside mitochondria as part of Complex I.
- **CLU** may be biologically related to cellular stress and Alzheimer disease, but it is not automatically classified as a core mitochondrial protein.

The original paper identified mitochondrial signals, especially MT-ND2 and oxidative-phosphorylation/electron-transport pathways, but it did not construct a comprehensive mitochondrial annotation system. The supplemental document contains only the sex-marker QC and power-analysis figures, not a mitochondrial annotation table. Therefore, this annotation must be built as part of the new study.

---

## 1. Required input data

Four main inputs are needed.

### Input 1: The complete gene list from the snRNA-seq dataset

Obtain the exact list of features used in the Seurat object or count matrix.

Ideally, for every feature, retain:

| Required field | Example |
|---|---|
| Original feature ID | `ENSG00000198840.2` |
| Ensembl gene ID | `ENSG00000198840` |
| Original gene symbol | `MT-ND3` |
| Gene biotype | Protein-coding, rRNA, tRNA, pseudogene, lncRNA |
| Chromosome | MT, 1, 2, X, etc. |
| Genome assembly | GRCh37 or GRCh38 |
| Gene annotation release | Ensembl or GENCODE version used to build the matrix |

This feature table is important even when a gene never appears in a DEG result. It lets us distinguish among the following situations:

- The gene was not present in the expression matrix.
- The gene was present but failed the expression filter.
- The gene was tested but was not significant.
- The gene was tested and was significant.

Those situations are biologically and statistically different.

### Input 2: Complete MAST results

Use the complete results from all six contrasts in every cell cluster, not only significant DEG lists.

The six primary contrasts are:

1. `F_e2x_AD vs F_e2x_NCI`
2. `F_e33_AD vs F_e33_NCI`
3. `F_e4x_AD vs F_e4x_NCI`
4. `M_e2x_AD vs M_e2x_NCI`
5. `M_e33_AD vs M_e33_NCI`
6. `M_e4x_AD vs M_e4x_NCI`

Applied across 54 cell clusters, this gives up to:

```text
6 contrasts x 54 clusters = 324 DEG analyses
```

Each DEG-result row should ideally contain:

| Field | Meaning |
|---|---|
| `gene_id` | Original gene identifier |
| `gene_symbol` | Original symbol |
| `cell_cluster` | Example: `Exc L5 ET` |
| `contrast` | Example: `F_e4x_AD_vs_NCI` |
| `avg_log2FC` | Direction and size of the AD effect |
| `p_value` | Raw MAST p value |
| `p_adj_BH` | Benjamini-Hochberg adjusted p value |
| `pct_AD` | Percentage of AD nuclei expressing the gene |
| `pct_NCI` | Percentage of NCI nuclei expressing the gene |
| `n_AD_cells` | Number of AD nuclei |
| `n_NCI_cells` | Number of NCI nuclei |

The contrast orientation must be fixed so that:

```text
ident.1 = AD
ident.2 = NCI
```

Then:

- Positive log2FC means higher expression in AD.
- Negative log2FC means lower expression in AD.

### Input 3: A curated mitochondrial protein inventory

Use **Human MitoCarta3.0** as the primary reference for mitochondrial proteins.

MitoCarta3.0 contains a curated inventory of human genes whose protein products have strong evidence of mitochondrial localization. It also supplies sub-mitochondrial compartment information and membership in a hierarchical set of mitochondrial pathways.

This should be the foundation of the study's **core mitochondrial protein set**.

### Input 4: Gene-name and identifier references

Use:

- **HGNC** for approved human gene symbols, previous symbols, aliases, and stable HGNC IDs.
- **Ensembl** for stable gene IDs, chromosome, biotype, and genomic location.

Ensembl IDs are preferable for matching because gene symbols can change over time or have aliases.

---

## 2. Define what counts as a mitochondrial gene

This definition should be frozen before examining the DEG results. Otherwise, it becomes too easy to selectively include genes that support an expected story.

Use three separate annotation tiers.

### Tier 1: Core mitochondrial protein genes

Definition:

> A gene included in Human MitoCarta3.0.

This includes both:

- Mitochondrial-DNA-encoded proteins, such as `MT-ND2`.
- Nuclear-DNA-encoded mitochondrial proteins, such as `NDUFS1`, `TFAM`, `TOMM20`, and `PINK1`.

This should be the primary mitochondrial gene set for the study.

### Tier 2: Mitochondrial-DNA noncoding genes

The human mitochondrial genome contains 37 conventional genes:

- 13 protein-coding genes
- 22 mitochondrial tRNA genes
- 2 mitochondrial rRNA genes

Because MitoCarta is primarily a protein inventory, the non-protein-coding mitochondrial genes should be tracked separately.

Examples:

| Type | Examples |
|---|---|
| Mitochondrial rRNA | `MT-RNR1`, `MT-RNR2` |
| Mitochondrial tRNA | `MT-TL1`, `MT-TS1`, `MT-TF` |

These genes may be absent or poorly represented in a single-nucleus dataset. Check whether each is present and tested rather than assuming that it was measured.

### Tier 3: Extended mitochondrial-associated genes

Some genes influence mitochondrial biology even though their proteins are not permanent mitochondrial residents.

Examples include genes involved indirectly in:

- Cellular responses to mitochondrial stress
- Transcriptional regulation of mitochondrial biogenesis
- Inflammatory responses to mitochondrial damage
- Mitochondria-endoplasmic-reticulum communication
- Cell-death signaling
- Metabolic signaling upstream of mitochondria

These genes can be collected from GO, Reactome, MSigDB, or other curated resources, but they should be labeled as:

```text
mitochondrial_associated_extended
```

rather than:

```text
core_mitochondrial
```

This distinction prevents the mitochondrial gene set from becoming so broad that nearly any metabolic or stress-related gene is called mitochondrial.

### Recommended classification

| Annotation | Definition | Main use |
|---|---|---|
| `core_mito_protein` | MitoCarta3.0 member | Primary gene-level analysis |
| `mtDNA_noncoding` | Mitochondrial tRNA or rRNA | Separate exploratory analysis |
| `mito_extended` | Indirect mitochondrial-process gene | Secondary or sensitivity analysis |
| `non_mito` | None of the above | Transcriptome background |

---

## 3. Do not identify mitochondrial genes using only the `MT-` prefix

Using the `MT-` prefix alone would miss most mitochondrial proteins.

| Gene | Has `MT-` prefix? | Mitochondrial? | Explanation |
|---|---:|---:|---|
| `MT-ND2` | Yes | Yes | mtDNA-encoded Complex I subunit |
| `NDUFS1` | No | Yes | Nuclear-encoded Complex I subunit |
| `TFAM` | No | Yes | Nuclear-encoded mtDNA maintenance and transcription protein |
| `TOMM20` | No | Yes | Nuclear-encoded mitochondrial protein-import protein |
| `PINK1` | No | Yes | Nuclear-encoded mitochondrial quality-control protein |

The reverse error can also occur: a gene can look mitochondrial because of its name but not be encoded by mitochondrial DNA.

For example:

- `MT-RNR2` is a true mitochondrial-DNA rRNA gene.
- `MTRNR2L8` is a separate nuclear gene and should not be classified as an mtDNA gene.

Therefore, classify genes using curated identifiers and database annotations, not name patterns.

---

## 4. Build a master gene-identifier crosswalk

Before adding mitochondrial information, map every dataset feature to reliable identifiers.

Recommended workflow:

```text
Original dataset feature
        ->
Original Ensembl ID and symbol
        ->
Ensembl stable gene ID
        ->
Current approved HGNC symbol and HGNC ID
        ->
MitoCarta and MitoPathways membership
```

### Keep original and current identifiers

Do not overwrite the original identifiers.

For each gene, retain:

| Field | Example |
|---|---|
| `feature_id_original` | `ENSG00000198840.2` |
| `ensembl_id_versioned` | `ENSG00000198840.2` |
| `ensembl_id_stable` | `ENSG00000198840` |
| `symbol_original` | Symbol used in the ROSMAP matrix |
| `symbol_hgnc_current` | Current approved symbol |
| `hgnc_id` | Stable HGNC identifier |
| `previous_symbols` | Previous approved symbols |
| `mapping_status` | Exact, alias, unmapped, or ambiguous |

If an Ensembl ID has a version suffix, such as:

```text
ENSG00000198840.2
```

retain the full versioned ID and also create:

```text
ENSG00000198840
```

for database matching.

### Handle mapping problems explicitly

Possible mapping outcomes include:

| Mapping status | Meaning |
|---|---|
| `exact_ensembl_match` | Ensembl ID maps directly |
| `exact_symbol_match` | Current symbol maps directly |
| `previous_symbol_match` | An old symbol maps to a current approved symbol |
| `alias_match` | An alias maps to an approved symbol |
| `one_to_many` | One feature maps to several records |
| `many_to_one` | Several dataset features map to one gene |
| `unmapped` | No reliable mapping |

Ambiguous mappings should be flagged for manual review rather than silently resolved.

---

## 5. Build the mitochondrial annotation master table

Once the identifiers are standardized, construct one row per unique gene.

Recommended fields:

| Annotation field | What it tells us |
|---|---|
| `is_mitocarta3` | Whether the gene is in MitoCarta3.0 |
| `is_mtDNA_gene` | Whether the locus is physically on mitochondrial DNA |
| `mito_tier` | Core protein, mtDNA noncoding, extended, or non-mito |
| `genome_origin` | `mtDNA` or `nuclear` |
| `gene_class` | Protein-coding, rRNA, tRNA, pseudogene, etc. |
| `mito_compartment` | Matrix, inner membrane, intermembrane space, outer membrane |
| `mitopathway_level1` | Broad mitochondrial process |
| `mitopathway_level2` | More specific process |
| `mitopathway_level3` | Most specific pathway |
| `oxphos_complex` | I, II, III, IV, V, or none |
| `oxphos_role` | Structural subunit, assembly factor, electron carrier, etc. |
| `mitochondrial_process` | Mitophagy, dynamics, import, translation, mtDNA maintenance, etc. |
| `annotation_source` | MitoCarta, HGNC, Ensembl, etc. |
| `annotation_version` | Exact database version |
| `annotation_date` | Date downloaded |

### Suggested broad mitochondrial pathway categories

#### 1. Oxidative phosphorylation

- Complex I
- Complex II
- Complex III
- Complex IV
- Complex V
- Respiratory-chain assembly
- Respirasome organization

#### 2. Mitochondrial central dogma

- mtDNA replication
- mtDNA repair
- Mitochondrial transcription
- RNA processing
- Mitochondrial ribosome
- Mitochondrial translation
- Mitochondrial tRNA modification

#### 3. Mitochondrial metabolism

- TCA cycle
- Pyruvate metabolism
- Fatty-acid oxidation
- Amino-acid metabolism
- One-carbon metabolism
- Coenzyme Q metabolism
- Heme metabolism
- Iron-sulfur cluster synthesis

#### 4. Protein import and homeostasis

- TOM complex
- TIM complexes
- Preprotein processing
- Chaperones
- Mitochondrial proteases

#### 5. Mitochondrial dynamics and quality control

- Fission
- Fusion
- Mitophagy
- Organelle trafficking
- Cristae organization
- Apoptosis

#### 6. Signaling and stress

- Calcium handling
- Reactive oxygen species detoxification
- Mitochondrial stress responses

The exact hierarchy and labels should be imported directly from the chosen MitoPathways release rather than typed manually into the final data files.

---

## 6. Allow genes to belong to more than one pathway

Do not force every gene into only one mitochondrial category.

Examples:

- **SDHA** can be classified as a Complex II subunit, an oxidative-phosphorylation gene, and a TCA-cycle gene.
- **TFAM** can be classified under mtDNA replication, mitochondrial nucleoid organization, and mitochondrial transcription.

Produce two annotation tables.

### Table A: One row per gene

Suggested filename:

```text
gene_annotation_master.tsv
```

This contains identity information and broad categories.

### Table B: One row per gene-pathway pair

Suggested filename:

```text
mitochondrial_pathway_membership_long.tsv
```

Example:

| Gene | Pathway |
|---|---|
| SDHA | OXPHOS > Complex II > Complex II subunits |
| SDHA | Metabolism > TCA cycle |
| TFAM | mtDNA maintenance > mtDNA replication |
| TFAM | mtDNA maintenance > mitochondrial nucleoid |
| TFAM | mtRNA metabolism > transcription |

The long format is safer and easier to use in pathway enrichment.

---

## 7. Join the annotation to the MAST results

After building the master annotation, perform a left join onto every all-gene DEG table.

Conceptually:

```text
MAST results
LEFT JOIN
gene_annotation_master
USING stable gene ID
```

A final row might look like:

| Field | Example |
|---|---|
| Gene | MT-ND2 |
| Cluster | Exc L5 ET |
| Contrast | F_e4x AD vs NCI |
| log2FC | -0.45 |
| Raw p value | 0.0008 |
| BH-adjusted p value | 0.012 |
| MitoCarta | Yes |
| Genome origin | mtDNA |
| Compartment | Inner membrane |
| Broad pathway | OXPHOS |
| Detailed pathway | Complex I subunits |
| DEG status | Significant down |

Do not filter to mitochondrial genes until after this join. Keep the complete transcriptome because all tested genes will be needed as a statistical background in later pathway analyses.

---

## 8. Record whether each gene was actually tested

The original paper used:

```text
min.pct = 0.1
```

A gene was included only if it was expressed in at least 10 percent of cells in either the AD or NCI group for that particular cluster and contrast.

Therefore, absence from a result table does not necessarily mean that a gene did not change. It may mean that the gene was never tested.

Assign every gene-cluster-contrast combination one of the following states:

| `tested_status` | Meaning |
|---|---|
| `not_in_expression_matrix` | Gene was never measured |
| `present_but_filtered_min_pct` | Present but failed the 10 percent expression threshold |
| `tested_not_significant` | Tested but did not pass significance criteria |
| `significant_up` | Significantly higher in AD |
| `significant_down` | Significantly lower in AD |
| `mapping_unresolved` | Gene identity could not be resolved reliably |

### Example

Suppose `PINK1` does not appear in the microglial MAST result table.

An incorrect conclusion would be:

> PINK1 is unchanged in microglia.

The correct explanation might be:

> PINK1 was detected in fewer than 10 percent of microglial nuclei and was not tested.

That distinction must be preserved.

---

## 9. Keep continuous statistics and categorical DEG states

For every gene, retain:

- log2 fold change
- raw p value
- BH-adjusted p value
- percentage of cells expressing the gene
- categorical DEG state

A categorical state can follow the paper's ternary system:

```text
+1 = significantly upregulated
 0 = no significant differential expression
-1 = significantly downregulated
```

However, continuous values must also be preserved.

Example:

| Gene | log2FC | FDR | DEG state |
|---|---:|---:|---:|
| Gene A | -0.80 | 0.001 | -1 |
| Gene B | -0.39 | 0.042 | -1 |
| Gene C | -0.37 | 0.061 | 0 |

Genes A and B receive the same categorical label, but Gene A has a much larger estimated effect. Gene C narrowly misses the cutoff but may still contribute to a coordinated pathway signal.

Therefore, the next pathway phase should use the complete ranked statistics as well as the significant DEG categories.

### Applying the paper's fold-change threshold

The paper used:

```text
adjusted p value < 0.05
absolute fold change > 1.3
```

If the result column is log2 fold change, a 1.3-fold cutoff corresponds to approximately:

```text
abs(log2FC) > log2(1.3) = approximately 0.379
```

Verify whether the exported Seurat column is ordinary fold change, natural-log fold change, or log2 fold change before applying this threshold.

---

## 10. Example of a final annotated table

The numerical values below are hypothetical.

| Gene | Cluster | Contrast | log2FC | FDR | Core mitochondrial? | Origin | Pathway | Detailed category | DEG status |
|---|---|---|---:|---:|---|---|---|---|---|
| MT-ND2 | Exc L5 ET | F_e4x AD vs NCI | -0.45 | 0.012 | Yes | mtDNA | OXPHOS | Complex I subunit | Significant down |
| NDUFS1 | Exc L5 ET | F_e4x AD vs NCI | -0.20 | 0.090 | Yes | Nuclear | OXPHOS | Complex I subunit | Tested, not significant |
| NUBPL | Exc L5 ET | F_e4x AD vs NCI | -0.28 | 0.040 | Yes | Nuclear | OXPHOS | Complex I assembly | Significant down |
| TFAM | Exc L5 ET | F_e4x AD vs NCI | +0.14 | 0.220 | Yes | Nuclear | Central dogma | mtDNA maintenance | Tested, not significant |
| TOMM20 | Exc L5 ET | F_e4x AD vs NCI | -0.10 | 0.410 | Yes | Nuclear | Protein import | TOM complex | Tested, not significant |
| MTRNR2L8 | Exc L5 ET | F_e4x AD vs NCI | -0.33 | 0.018 | No, not core | Nuclear | None in core set | MT-RNR2-like nuclear gene | Significant down |
| CLU | Exc L5 ET | F_e4x AD vs NCI | -0.31 | 0.020 | No, not core | Nuclear | Possibly extended | Stress-related or indirect | Significant down |

This allows more precise conclusions.

Instead of saying:

> Several mitochondrial-looking genes are downregulated.

we could say:

> In female APOE e4 excitatory neurons, several nuclear- and mtDNA-encoded Complex I genes show negative AD-associated fold changes, including both structural subunits and an assembly factor.

---

## 11. Annotation quality-control checks

Before using the annotated table, generate a formal QC report.

### Identifier-mapping checks

Report:

- Total number of unique dataset features
- Number mapped by Ensembl ID
- Number mapped only by symbol or alias
- Number unmapped
- Number with ambiguous mappings
- Number of duplicate gene mappings

Example:

| Mapping result | Number |
|---|---:|
| Exact Ensembl match | 18,200 |
| Exact HGNC-symbol match | 700 |
| Previous-symbol match | 40 |
| Ambiguous | 12 |
| Unmapped | 85 |

### Mitochondrial coverage checks

Report:

- Number of MitoCarta genes present in the count matrix
- Number absent from the count matrix
- Number tested in each cluster and contrast
- Number filtered by `min.pct`
- Number significantly upregulated
- Number significantly downregulated
- Number of mtDNA protein genes detected
- Number of mtDNA rRNA and tRNA genes detected

Example:

| Cell cluster | Contrast | Core mito genes present | Tested | Significant up | Significant down |
|---|---|---:|---:|---:|---:|
| Exc L5 ET | F_e4x | 980 | 830 | 21 | 47 |
| Ast GRM3 | F_e4x | 960 | 710 | 35 | 22 |
| Mic P2RY12 | F_e4x | 925 | 630 | 18 | 11 |

These numbers help determine whether differences between cell types reflect biology or simply differences in gene detectability.

### Positive-control checks

Confirm that well-known mitochondrial genes map correctly:

| Gene | Expected annotation |
|---|---|
| MT-ND2 | mtDNA, Complex I |
| NDUFS1 | Nuclear, Complex I |
| SDHA | Nuclear, Complex II and TCA cycle |
| COX5A | Nuclear, Complex IV |
| ATP5F1A | Nuclear, Complex V |
| TFAM | mtDNA maintenance and transcription |
| TOMM20 | Protein import, outer membrane |
| PINK1 | Mitochondrial quality control and mitophagy |

### Negative-control checks

Confirm that genes are not classified as core mitochondrial merely because:

- Their symbol begins with `MT`.
- Their name contains the word mitochondrial.
- They are associated with metabolic stress.
- They are mentioned in an Alzheimer disease paper alongside mitochondrial genes.

---

## 12. P-value bookkeeping

The paper reports using Benjamini-Hochberg correction for DEG analysis.

In the analysis output, retain distinct columns such as:

```text
p_value_MAST
p_adj_Seurat
p_adj_BH
```

Calculate the BH-adjusted value explicitly from the raw MAST p values if necessary:

```r
result$p_adj_BH <- p.adjust(result$p_val, method = "BH")
```

The correction family should normally be all genes tested within one:

```text
cell cluster x DEG contrast
```

unless the authors' released code documents a different family.

This bookkeeping does not change whether a gene is mitochondrial, but it affects whether an annotated mitochondrial gene is classified as statistically significant.

---

## 13. Recommended output files

At the end of this phase, create the following files.

### `gene_annotation_master.tsv`

One row per unique dataset feature, containing:

- Original and standardized IDs
- HGNC symbol
- Chromosome and biotype
- Core or extended mitochondrial classification
- Genome origin
- Mitochondrial compartment
- Broad pathway information
- Annotation source and version

### `mitochondrial_pathway_membership_long.tsv`

One row per gene-pathway pair, used for pathway analysis.

### `deg_all_annotated.tsv.gz`

All MAST results for all genes, cell clusters, and contrasts, with mitochondrial annotations attached.

### `deg_mito_core.tsv.gz`

A convenient subset containing only core MitoCarta genes. This must be derived from the complete annotated table, not produced independently.

### `mtDNA_noncoding_results.tsv.gz`

Separate results for mitochondrial rRNAs and tRNAs.

### `mitochondrial_gene_sets.gmt`

Gene sets formatted for enrichment analysis.

### `mitochondrial_annotation_qc.tsv`

Mapping, coverage, and annotation statistics.

### Optional human-readable QC report

```text
mitochondrial_annotation_qc_report.md
```

This report should summarize mapping success, mitochondrial coverage, testability, and unresolved identifiers.

---

## 14. What this phase answers

The annotation phase answers:

- Is this gene a core mitochondrial gene?
- Is it encoded by mtDNA or nuclear DNA?
- What mitochondrial compartment is its protein located in?
- Which mitochondrial pathway or respiratory complex does it belong to?
- Was it measured and tested in this particular cell cluster and contrast?
- Was it upregulated, downregulated, or not significant?

It does **not yet** answer:

- Is Complex I collectively altered?
- Is oxidative phosphorylation significantly enriched?
- Does the mitochondrial response differ statistically between females and males?
- Does APOE e4 modify the mitochondrial AD response?
- Which mitochondrial genes are the strongest candidates?

Those questions belong to the pathway, interaction, cross-cell-type, and prioritization phases.

---

## 15. Final decisions to freeze before implementation

Use the following specification:

1. Use **MitoCarta3.0** as the primary definition of core mitochondrial protein genes.
2. Use **MitoPathways3.0** as the primary mitochondrial pathway hierarchy.
3. Analyze mitochondrial rRNA and tRNA genes as a separate group.
4. Keep indirect mitochondrial-associated genes in a separate extended tier.
5. Use Ensembl stable gene IDs as the preferred matching key.
6. Preserve original gene IDs and symbols from the ROSMAP matrix.
7. Annotate every available gene, not only significant DEGs.
8. Distinguish unmeasured, filtered, tested-not-significant, significant-up, and significant-down states.
9. Allow genes to belong to multiple mitochondrial pathways.
10. Record the version and download date of every reference database.
11. Retain complete continuous DEG statistics in addition to categorical DEG states.
12. Keep the complete transcriptome as the background for later pathway testing.

The concrete product of this phase is:

> One comprehensive, all-gene DEG table in which every row has reliable mitochondrial identity, pathway, compartment, genome-origin, mapping-status, and test-status information.

That annotated table becomes the input for the next phase: **testing mitochondrial pathways**.

---

## Actionable checklist

### Before annotation

- [ ] Export the complete feature list from the Seurat object.
- [ ] Export complete MAST results for all 324 cluster-contrast analyses.
- [ ] Confirm that AD is `ident.1` and NCI is `ident.2`.
- [ ] Record the genome assembly and GENCODE or Ensembl annotation version.
- [ ] Download and freeze the selected MitoCarta3.0 and MitoPathways3.0 files.
- [ ] Download or generate an HGNC and Ensembl identifier crosswalk.

### Build identifiers

- [ ] Remove Ensembl version suffixes into a separate stable-ID column.
- [ ] Preserve the original versioned IDs.
- [ ] Map original symbols to current HGNC symbols.
- [ ] Flag aliases, previous symbols, duplicate mappings, and unresolved mappings.

### Add mitochondrial annotations

- [ ] Mark MitoCarta3.0 membership.
- [ ] Mark mtDNA location separately.
- [ ] Add protein-coding, rRNA, tRNA, and other gene classes.
- [ ] Add mitochondrial compartment.
- [ ] Add MitoPathways levels 1, 2, and 3.
- [ ] Add respiratory-chain complex and gene role.
- [ ] Add core, mtDNA-noncoding, extended, or non-mito tier.

### Join with DEG results

- [ ] Join by stable Ensembl ID whenever possible.
- [ ] Verify that the number of DEG rows does not change unexpectedly after the join.
- [ ] Add tested-status and DEG-state columns.
- [ ] Retain raw p values, BH-adjusted p values, log2FC, and expression percentages.

### Validate

- [ ] Check known mitochondrial positive controls.
- [ ] Check non-mitochondrial negative controls.
- [ ] Review `MTRNR2L*` genes separately from `MT-RNR2`.
- [ ] Report mitochondrial coverage by cluster and contrast.
- [ ] Manually inspect all ambiguous gene mappings.

### Save final products

- [ ] Save the master gene annotation table.
- [ ] Save the long gene-to-pathway table.
- [ ] Save the complete annotated DEG table.
- [ ] Save core-mitochondrial and mtDNA-noncoding subsets.
- [ ] Save the mitochondrial gene-set GMT file.
- [ ] Save the annotation QC table and human-readable report.
