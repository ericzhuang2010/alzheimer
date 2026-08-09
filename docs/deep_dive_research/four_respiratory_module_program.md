# C1 respiratory and respiration-supporting gene modules

## Document status

The research plan names four modules, but their exact gene lists have not yet
been formally frozen. Only the 13-gene mitochondrial-DNA module is currently
unambiguous.

Based on the MitoCarta 3.0 data already in this project, the recommended working
definitions are:

| Module | Recommended reference size | Status |
|---|---:|---|
| 1. mtDNA-encoded OXPHOS | 13 | Unambiguous |
| 2. Nuclear-encoded OXPHOS structural genes | 86 | Recommended strict definition |
| 3. Mitochondrial translation | 155 | Recommended full MitoCarta definition |
| 4. MIB/MICOS and inner-membrane organization | 19 | Recommended custom union; not yet frozen |

“Reference size” means the number of genes in the original module definition.
Some genes may not be measured well enough in a particular cell type, so the
number that actually enters a statistical analysis may be smaller. The analysis
must report the original, measured, tested, and excluded genes for every cell
context.

## How the four modules were chosen

The four modules were not selected as four one-to-one matches for the three
candidate systems. They were selected through two connected routes:

1. **Core biological question:** which gene sets are needed to test whether AD
   changes mitochondrial respiratory expression, including the relationship
   between mitochondrial-DNA and nuclear-DNA signals?
2. **Earlier pathway and network clues:** which nearby mitochondrial processes
   could help connect the core respiratory result to the proposed candidate
   systems?

MitoCarta supplies curated genes after a biological process has been chosen.
It does not decide by itself that these are the four most important processes.
The process selection came from the central research question, earlier
Phase 11/12 observations, and the candidate hypotheses. This makes the current
set biologically motivated but partly hypothesis-driven.

The relationship is:

| Primary module | Main reason for choosing it | Relationship to C4–C6 |
|---|---|---|
| mtDNA-encoded OXPHOS | Directly measures the 13 respiratory components encoded by mitochondrial DNA; required for the core respiratory and mitonuclear questions | Shared mitochondrial outcome, not specific to one candidate |
| Nuclear-encoded OXPHOS | Measures the nuclear structural components of respiratory complexes I–V; required as the other half of the core respiratory and mitonuclear questions | Shared outcome for all candidates; its Complex V subset is especially relevant to `LAMTOR5–ATP5IF1` |
| Mitochondrial translation | Measures the machinery that makes mtDNA-encoded proteins | Directly related to the `APOE–TUFM` hypothesis because `TUFM` is a mitochondrial translation factor |
| MIB/MICOS and inner-membrane organization | Measures cristae and inner-membrane organization, the physical setting in which respiratory complexes operate | General respiration-supporting context; it is not a direct readout for one of C4–C6 |

Therefore, the four modules are best described as:

```text
Core respiratory measurements
├── mtDNA-encoded OXPHOS
└── nuclear-encoded OXPHOS

Broader respiration-supporting programs
├── mitochondrial translation
└── MIB/MICOS and inner-membrane organization
```

Only the first two directly measure OXPHOS machinery. The other two measure
processes that can support respiratory-chain production or organization.

## 1. mtDNA-encoded OXPHOS module: 13 genes

These genes are located in mitochondrial DNA rather than nuclear DNA.

### Complex I: 7 genes

```text
MT-ND1, MT-ND2, MT-ND3, MT-ND4, MT-ND4L, MT-ND5, MT-ND6
```

### Complex III: 1 gene

```text
MT-CYB
```

### Complex IV: 3 genes

```text
MT-CO1, MT-CO2, MT-CO3
```

### Complex V, or ATP synthase: 2 genes

```text
MT-ATP6, MT-ATP8
```

Complex II contains no mtDNA-encoded genes.

All 13 genes are measured in the existing datasets. This module is already
listed in [`analysis_parameters.yml`](../../config/analysis_parameters.yml).

## 2. Nuclear-encoded OXPHOS structural module: 86 genes

These genes are located in nuclear DNA, but their proteins become parts of
mitochondrial respiratory complexes I–V.

The recommended primary definition is the strict 86-gene list.

### Complex I: 37 genes

```text
NDUFA1, NDUFA2, NDUFA3, NDUFA5, NDUFA6, NDUFA7, NDUFA8,
NDUFA9, NDUFA10, NDUFA11, NDUFA12, NDUFA13, NDUFAB1,
NDUFB1, NDUFB2, NDUFB3, NDUFB4, NDUFB5, NDUFB6, NDUFB7,
NDUFB8, NDUFB9, NDUFB10, NDUFB11, NDUFC1, NDUFC2,
NDUFS1, NDUFS2, NDUFS3, NDUFS4, NDUFS5, NDUFS6, NDUFS7,
NDUFS8, NDUFV1, NDUFV2, NDUFV3
```

### Complex II: 4 genes

```text
SDHA, SDHB, SDHC, SDHD
```

### Complex III: 9 genes

```text
CYC1, UQCR10, UQCR11, UQCRB, UQCRC1, UQCRC2, UQCRFS1,
UQCRH, UQCRQ
```

### Complex IV: 18 genes

```text
COX4I1, COX4I2, COX5A, COX5B, COX6A1, COX6A2, COX6B1,
COX6B2, COX6C, COX7A1, COX7A2, COX7A2L, COX7B, COX7B2,
COX7C, COX8A, COX8C, NDUFA4
```

### Complex V: 18 genes

```text
ATP5F1A, ATP5F1B, ATP5F1C, ATP5F1D, ATP5F1E,
ATP5MC1, ATP5MC2, ATP5MC3, ATP5MD, ATP5ME, ATP5MF,
ATP5MG, ATP5MPL, ATP5PB, ATP5PD, ATP5PF, ATP5PO, DMAC2L
```

### Why 86 instead of 89?

The MitoCarta pathway named `OXPHOS subunits` contains 102 genes:

```text
13 mtDNA genes + 89 nuclear genes = 102 genes
```

However, three of the 89 nuclear genes are not strict structural components:

- `ATP5IF1` regulates or inhibits ATP synthase.
- `CYCS` carries electrons between complexes III and IV.
- `HCCS` helps produce mature cytochrome c.

Removing these three gives:

```text
89 − 3 = 86 strict nuclear OXPHOS structural genes
```

The 86-gene definition should be used for the primary C1 module. The broader
89-gene MitoCarta definition can be used as a sensitivity analysis.

This also keeps `ATP5IF1` out of the general module used to evaluate the
separate LAMTOR5–ATP5IF1 candidate hypothesis.

The complex-by-complex biology is explained in the
[OXPHOS pathway, complexes, and genes tutorial](oxphos_pathway_complexes_and_genes_tutorial.md).

## 3. Mitochondrial translation module: 155 genes

Mitochondrial translation is the machinery mitochondria use to make the
proteins encoded by mitochondrial DNA.

It includes:

- mitochondrial ribosome components;
- proteins that assemble the mitochondrial ribosome;
- translation initiation, elongation, and termination factors;
- enzymes that attach amino acids to mitochondrial transfer RNAs; and
- proteins that process and stabilize mitochondrial RNA.

The exact 155 MitoCarta genes are:

```text
AARS2, AURKAIP1, C12orf65, CARS2, CHCHD1, COA3, COX14,
DAP3, DARS2, DDX28, DHX30, EARS2, ERAL1, EXD2, FARS2,
FASTKD2, GADD45GIP1, GARS1, GATB, GATC, GFM1, GFM2,
GRSF1, GTPBP10, GUF1, HARS2, HEMK1, IARS2, KARS1, LARS2,
LRPPRC, MALSU1, MARS2, METAP1D, METTL17, MIEF1, MPV17L2,
MRM2, MRM3, MRPL1, MRPL10, MRPL11, MRPL12, MRPL13, MRPL14,
MRPL15, MRPL16, MRPL17, MRPL18, MRPL19, MRPL2, MRPL20,
MRPL21, MRPL22, MRPL23, MRPL24, MRPL27, MRPL28, MRPL3,
MRPL30, MRPL32, MRPL33, MRPL34, MRPL35, MRPL36, MRPL37,
MRPL38, MRPL39, MRPL4, MRPL40, MRPL41, MRPL42, MRPL43,
MRPL44, MRPL45, MRPL46, MRPL47, MRPL48, MRPL49, MRPL50,
MRPL51, MRPL52, MRPL53, MRPL54, MRPL55, MRPL57, MRPL58,
MRPL9, MRPS10, MRPS11, MRPS12, MRPS14, MRPS15, MRPS16,
MRPS17, MRPS18A, MRPS18B, MRPS18C, MRPS2, MRPS21, MRPS22,
MRPS23, MRPS24, MRPS25, MRPS26, MRPS27, MRPS28, MRPS30,
MRPS31, MRPS33, MRPS34, MRPS35, MRPS36, MRPS5, MRPS6,
MRPS7, MRPS9, MRRF, MTERF3, MTERF4, MTFMT, MTG1, MTG2,
MTIF2, MTIF3, MTRES1, MTRF1, MTRF1L, NARS2, NGRN, NOA1,
NSUN4, OXA1L, PARS2, PDF, PPA2, PTCD3, PUSL1, QRSL1,
RARS2, RBFA, RMND1, SARS2, SLIRP, TACO1, TARS2, TFB1M,
TIMM21, TRMT61B, TSFM, TUFM, VARS2, WARS2, YARS2, YBEY
```

### Important identifier problem

`MRPL13` is a mitochondrial ribosome gene and belongs in this module.

`RPL13` is a different gene belonging to the ordinary cytoplasmic ribosome. It
must not be included in this module.

The current repository contains a loose alias mapping that could confuse these
genes. They must be separated using their stable gene identifiers before
calculating the module score.

### TUFM and the candidate analysis

`TUFM` is one of the 155 translation genes.

For the general C1 translation module, keep `TUFM`.

When specifically testing the APOE–TUFM candidate system, calculate an
additional translation score with `TUFM` removed. Otherwise, a change in TUFM
could partly manufacture its own supporting module result.

## 4. MIB/MICOS and inner-membrane organization

This module is not yet uniquely defined.

MIB means the mitochondrial intermembrane-space bridging complex. It is not the
gene `MIB1`.

MitoCarta does not contain a pathway literally named “MIB.” It contains several
related gene sets.

### MICOS complex only: 7 genes

MICOS organizes junctions in the folded inner mitochondrial membrane.

```text
APOO, APOOL, CHCHD3, CHCHD6, IMMT, MICOS10, MICOS13
```

### Cristae formation: 11 genes

This contains the seven MICOS genes plus four additional inner-membrane genes:

```text
APOO, APOOL, ATP5MD, ATP5ME, ATP5MG, CHCHD3, CHCHD6,
IMMT, MICOS10, MICOS13, OPA1
```

### Intramitochondrial membrane interactions: 9 genes

These genes help link or organize mitochondrial membranes:

```text
ATAD3A, ATAD3B, CHCHD3, DNAJC11, MTX1, MTX2, MTX3,
SAMM50, SLC25A46
```

### Recommended broad module: 19 unique genes

To match the phrase “MIB/MICOS and inner-membrane organization,” the
recommended working definition is the union of the 11 cristae genes and the
9 membrane-interaction genes.

`CHCHD3` occurs in both lists, so the union contains 19 rather than 20 genes:

```text
APOO, APOOL, ATAD3A, ATAD3B, ATP5MD, ATP5ME, ATP5MG,
CHCHD3, CHCHD6, DNAJC11, IMMT, MICOS10, MICOS13,
MTX1, MTX2, MTX3, OPA1, SAMM50, SLC25A46
```

This 19-gene definition is a reasonable custom module, but it must be
explicitly approved and frozen before running C1.

### Relationship to the GABARAPL2–CHCHD2/PARK7 hypothesis

This MIB/MICOS module must not be treated as the candidate-specific
quality-control program for `GABARAPL2–CHCHD2`/`PARK7`.

In particular:

- `CHCHD2` is not one of the proposed 19 MIB/MICOS genes;
- `PARK7` is not one of the proposed 19 genes; and
- similar-looking `CHCHD` gene names do not establish membership in the same
  complex or program.

The C6 candidate test needs a separately frozen mitochondrial-quality-control
program with `CHCHD2` and `PARK7` removed from its score. The MIB/MICOS module
can provide broader membrane context, but it cannot substitute for that
candidate-specific readout.

## Primary modules versus candidate-specific readouts

The four modules above are used to study the main respiratory phenomenon.
Candidate testing asks a narrower question and therefore uses additional
target-excluded scores.

A **target-excluded score** is calculated after removing the named readout gene
from its biological program. This prevents one changing gene from creating
its own supporting module result.

| Candidate claim | Named partner/readout | Candidate-specific program | Relationship to the four primary modules |
|---|---|---|---|
| C4: `APOE–TUFM` | `TUFM` | Mitochondrial translation with `TUFM` removed | Directly derived from the 155-gene translation module |
| C5: `LAMTOR5–ATP5IF1` | `ATP5IF1` | ATP-synthase structural genes with `ATP5IF1` excluded | A focused Complex V subset of nuclear OXPHOS; `ATP5IF1` is already absent from the strict 86 structural genes |
| C6: `GABARAPL2–CHCHD2`/`PARK7` | `CHCHD2` primary; `PARK7` secondary | A separately frozen mitochondrial-quality-control program with `CHCHD2` and `PARK7` removed | Not one of the four primary modules; MIB/MICOS is not a replacement |

The complete organization is:

```text
Core biological phenomenon
├── mtDNA OXPHOS
├── nuclear OXPHOS
├── mitochondrial translation
└── MIB/MICOS and membrane organization

Candidate-specific phenotype checks
├── translation minus TUFM
├── ATP synthase minus ATP5IF1
└── quality control minus CHCHD2 and PARK7
```

Use the full translation module, including `TUFM`, for the general C1 analysis.
Use translation minus `TUFM` only for the C4 candidate test. Apply the same
separation between a general program and its candidate-specific
target-excluded score.

This design means:

- the core modules can be supported even if all three candidates fail;
- a candidate cannot rescue an unsupported core respiratory result;
- a candidate-specific module is supporting evidence for that candidate, not
  an independent replication; and
- the four primary modules must not be presented as four independent
  confirmations of the three candidate hypotheses.

## Gene-name translations to watch

Some gene names have changed. The frozen MitoCarta workbook and the count data
may use older names.

| Frozen or data name | Newer normalized name |
|---|---|
| `ATP5MD` | `ATP5MK` |
| `ATP5MPL` | `ATP5MJ` |
| `NDUFA4` | `COXFA4` |
| `C12orf65` | `MTRFR` |
| `MRPS36` | `KGD4` |
| `MINOS1` | `MICOS10` |
| `C19orf70` | `MICOS13` |

The final manifest should store both the source name and normalized name so
that genes are neither lost nor counted twice.

## Interpretation cautions

### The four modules are not four independent confirmations

The proposed 19-gene inner-membrane module shares `ATP5MD`, `ATP5ME`, and
`ATP5MG` with nuclear OXPHOS. This overlap must be reported. Evidence from
overlapping modules cannot be described as completely independent evidence.

### Only two modules directly describe OXPHOS machinery

The two direct OXPHOS modules are:

- mtDNA-encoded OXPHOS; and
- nuclear-encoded OXPHOS.

Mitochondrial translation and MIB/MICOS support respiratory biology, but they
are not themselves measurements of mitochondrial respiration.

Changes in RNA expression also do not prove that oxygen consumption or ATP
production changed. Those conclusions require functional measurements.

## Provenance and source warning

The frozen source workbook is
[`Human.MitoCarta3.0.xls`](../../data/reference/Human.MitoCarta3.0.xls).

The reliable normalized membership table is
[`pathway_membership_long.tsv.gz`](../../results/minerva_production/11_pathway/pathway_membership_long.tsv.gz).

Do not use the `gene_count` column in the older Phase 03 pathway table. That
table has a delimiter-parsing error that can make a comma-separated pathway
look like one gene.

Before C1 is run, copy the approved definitions into a versioned module
manifest and record:

- source symbol;
- normalized symbol;
- stable gene identifier;
- module membership;
- source annotation and version;
- inclusion or exclusion reason;
- measured/tested status in each cell context; and
- any overlap with another module.
