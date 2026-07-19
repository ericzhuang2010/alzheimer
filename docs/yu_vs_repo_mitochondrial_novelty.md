# Were the repository's mitochondrial genes already studied by Yu et al.?

## Short answer

Partly—but the repository is not simply repeating a roughly 1,000-gene analysis from Yu et al.

Yu et al. tested genes transcriptome-wide. Therefore, MitoCarta genes that passed their expression filter were already included in their differential-expression tests. However, the paper did not define or systematically analyze the approximately 1,000 MitoCarta genes as a mitochondrial family.

## The central clarification: this is not only a pathway analysis

The repository studies mitochondrial biology at four distinct levels.

### 1. Individual mitochondrial genes

The repository examines individual gene-level differential-expression results for:

- the 13 protein-coding genes encoded by mitochondrial DNA, such as `MT-ND2`; and
- approximately 1,000 measured MitoCarta genes, most of which are encoded by nuclear DNA.

The MitoCarta genes are therefore not used only to construct pathways. Each eligible gene can have its own effect size, p-value, within-contrast FDR, mitochondrial-family FDR, cell type, sex–APOE stratum, and differential-expression classification.

### 2. Mitochondrial pathways

Groups of related MitoCarta genes are also analyzed together. Examples include:

- oxidative phosphorylation;
- electron-transport-chain complexes I–V;
- mitochondrial translation;
- mitochondrial protein import;
- mitophagy; and
- mitochondrial metabolism and stress responses.

This asks whether many genes participating in the same mitochondrial process shift together, even when not every individual gene is significant.

### 3. Mitochondrial RNA fraction

The repository separately asks whether the proportion

```text
mitochondrial RNA counts / total RNA counts
```

differs between AD and NCI or across sex–APOE groups. This is a donor-level proportion outcome and is not interchangeable with pathway activity. A higher mitochondrial fraction could reflect mitochondrial transcription, loss of other RNA, cellular stress, tissue quality, or a mixture of these factors.

### 4. Mitonuclear balance

The repository compares expression from:

```text
mtDNA-encoded OXPHOS genes
              versus
nuclear-encoded OXPHOS genes
```

This asks whether the mitochondrial and nuclear genomes coordinate their mitochondrial programs or show evidence of imbalance.

## What Yu et al. did

In [Yu_sex_apoe.pdf](Yu_sex_apoe.pdf), the authors:

- Started with the genome-wide expression matrix.
- Used MAST separately within six sex–APOE groups and 54 cell types.
- Tested genes expressed in at least 10% of AD or NCI nuclei.
- Defined DEGs using BH FDR `< 0.05` and absolute fold change `> 1.3`.
- Used all resulting DEGs in Figure 1, not only mitochondrial genes.
- Performed general MSigDB canonical-pathway enrichment.
- Highlighted mitochondrial findings such as `MT-ND2`, oxidative phosphorylation, and the electron-transport chain.

The local paper PDF never names “MitoCarta.” Thus, mitochondrial biology appeared as a result of a broad transcriptome-wide analysis, rather than as a prespecified MitoCarta investigation.

## What this repository does

The repository still performs differential expression on all adequately expressed genes—not only MitoCarta genes. The 33,538 features are the starting assay rows; Phase 08 MAST tests approximately 4,328–12,798 genes per eligible contrast after expression filtering.

The complete workflow is:

```text
33,538 assayed features
        ↓
Test all adequately expressed genes
using donor-level edgeR and nucleus-level MAST
        ↓
Identify prespecified mitochondrial genes
        ├── 13 mtDNA genes
        └── approximately 1,000 measured MitoCarta genes
        ↓
Analyze individual mitochondrial genes
        ↓
Analyze 154 mitochondrial pathways
        ↓
Analyze mitochondrial RNA fraction
        ↓
Analyze mtDNA-versus-nuclear OXPHOS balance
        ↓
Test whether the effects differ by sex, APOE, and cell type
```

The generated Yu-style figure contains 990 canonical MitoCarta genes because not every one of the 1,136 inventory genes is mapped and tested in the eligible Phase 08 contrasts. See the [figure checks](../results/figures/figure01/figure01_mitochondrial_yu_analogue_checks.tsv).

## What is actually new?

| Analysis | Yu et al. | This repository |
|---|:---:|:---:|
| Same ROSMAP snRNA-seq dataset | Yes | Yes |
| Genome-wide differential expression | Yes | Yes |
| Individual MitoCarta genes present in the initial gene tests | Yes, when they passed the expression filter | Yes, when they pass the relevant filter |
| Individual MitoCarta results treated as a prespecified mitochondrial family | No | Yes |
| Dedicated MitoCarta pathway hierarchy | No | Yes |
| The 13 mtDNA protein genes treated as their own testing family | No | Yes |
| Mitochondrial RNA-fraction models | No | Yes |
| Mitonuclear OXPHOS balance | No | Yes |
| Donor-level pseudobulk edgeR | No | Yes; primary method |
| Nucleus-level MAST | Yes | Yes; secondary paper-comparison method |
| Formal AD-by-sex and AD-by-APOE interaction tests | Not the primary approach | Yes |
| Global mitochondrial multiple-testing correction | No | Yes |
| Pseudobulk–MAST comparison, sensitivity analyses, donor gates, and power analysis | No | Yes |

The main additions are:

1. **A systematic MitoCarta analysis.**  
   Instead of noticing a few mitochondrial genes afterward, the repository evaluates a frozen set of 1,136 mitochondrial-localized genes and 154 mitochondrial pathways.

2. **Donor-aware inference.**  
   Yu’s MAST analysis treats nuclei as observations. This repository’s primary edgeR analysis aggregates nuclei into one sample per donor and cell type, making the donor the biological replicate. See [Phase 07.3 versus Phase 08](phase_07_3_vs_phase_08.md).

3. **Formal interaction tests.**  
   The repository directly asks whether the AD effect differs by sex or APOE group. “Significant in females but not significant in males” alone does not prove a sex difference; a direct interaction test is stronger.

4. **Mitochondrial-specific multiple-testing families.**  
   Phase 11 corrects all mtDNA or MitoCarta tests across cell types and contrasts, not merely within one comparison. See [Phase 11 explained](phase_11_explained.md).

5. **Additional mitochondrial outcomes.**  
   The project separately investigates mitochondrial RNA fraction, nuclear- versus mtDNA-encoded OXPHOS expression, respiratory complexes, and mitonuclear balance.

## The two studies ask different questions

Yu et al. asked a broad transcriptomic question:

> Which genes and pathways show different AD responses across sex, APOE, and cell type?

This repository asks a focused extension:

> Within those transcriptomic differences, exactly how is mitochondrial biology altered—including individual genes, pathways, mitochondrial RNA abundance, and coordination between mitochondrial and nuclear genomes—and are those conclusions reproducible across donors?

The strongest extension is therefore not simply filtering the Yu result table to mitochondrial genes. It is the combination of donor-aware pseudobulk analysis, formal interaction tests, individual mtDNA and MitoCarta testing families, mitochondrial pathways, RNA-fraction modeling, mitonuclear balance, and mitochondrial-specific global FDR correction.

The new Yu-style MitoCarta figure shows only one part of this larger analysis: individual MitoCarta DEG patterns from the paper-comparable Phase 08 MAST branch. It is a gene-level summary, not a mitochondrial-pathway analysis.

## Important limitation

The novelty is in the biological focus and statistical analysis—not in new samples or previously unmeasured genes. This remains a reanalysis of the Yu/Mathys ROSMAP dataset, so it is not independent validation.

Also, the new Yu-style MitoCarta figure is primarily a focused reorganization of the Phase 08 MAST results. The stronger methodological extension comes from the donor-level pseudobulk, interaction, pathway, mitochondrial-fraction, global-correction, and sensitivity analyses.

The most accurate description is:

> This repository is a systematic, donor-aware mitochondrial extension of Yu et al., rather than the discovery of an entirely new set of genes.
