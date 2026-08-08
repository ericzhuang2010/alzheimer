# Oxidative phosphorylation (OXPHOS): pathway, complexes, and human genes

Last verified: 2026-08-08  
Species: *Homo sapiens*

## Purpose and scope

Oxidative phosphorylation, abbreviated **OXPHOS**, is the process by which
mitochondria convert energy carried by NADH and other reduced metabolites into
an electrochemical proton gradient and then into ATP. It requires respiratory
Complexes I-IV, the mobile electron carriers coenzyme Q and cytochrome *c*, and
ATP synthase (Complex V).

This tutorial answers four questions:

1. What happens to electrons and protons during OXPHOS?
2. What does each of Complexes I-V do?
3. Which human genes encode the physical subunits of each complex, and which
   are encoded by nuclear DNA versus mitochondrial DNA (mtDNA)?
4. Which additional genes help assemble each complex?

The boundary around “genes involved” matters. A **structural-subunit gene**
encodes a protein present in the mature complex. An **assembly-factor gene**
encodes a protein that builds, matures, inserts cofactors into, or stabilizes a
complex but is generally not a permanent stoichiometric subunit. A third group
provides mobile carriers, cofactors, mitochondrial translation, metabolite
transport, and quality control. Calling all three groups “subunits” obscures
their very different biological roles.

The complex assignments and assembly-factor lists below use the project-frozen
[Human MitoCarta3.0 workbook](../../data/reference/Human.MitoCarta3.0.xls) and
its derived [MitoPathways table](../../results/minerva_production/03_annotations/mitocarta_pathways.tsv)
as the operational reference. MitoCarta3.0 is a curated inventory of 1,136
human genes with strong evidence for mitochondrial localization and includes a
hierarchical OXPHOS annotation [1,2]. Mechanistic descriptions are checked
against Reactome and primary structural studies [3-9].

## The pathway in one picture

```text
                         INTERMEMBRANE SPACE
                    H+       H+       H+
                    ^        ^        ^
                    |        |        |
NADH -> Complex I --+--> Q -> Complex III -> cytochrome c -> Complex IV -> O2
                          ^                                      |
succinate -> Complex II --+                                      +-> H2O
                          ^
      ETFDH, GPD2, DHODH, SQOR, and other Q-linked dehydrogenases

======================= INNER MITOCHONDRIAL MEMBRANE ========================

                    proton-motive force
INTERMEMBRANE SPACE H+ --------------------> Complex V ----> H+ MATRIX
                                                    |
                                               ADP + Pi -> ATP

                                  MATRIX
```

The sequence is therefore not simply “Complex I to Complex V.” Complexes I and
II are alternative entry points into the **coenzyme Q pool**. Complex III
passes electrons from reduced coenzyme Q to **cytochrome c**. Complex IV passes
them to oxygen, the terminal electron acceptor. Complex V does not receive
electrons; it uses the proton-motive force created mainly by Complexes I, III,
and IV [3].

## Executive summary of the five complexes

| Complex | Common name | Main reaction or job | Approximate H+ contribution per electron pair | mtDNA-encoded structural genes | Nuclear structural-gene inventory | MitoCarta assembly factors |
|---|---|---|---:|---:|---:|---:|
| I | NADH:ubiquinone oxidoreductase | NADH -> coenzyme Q | 4 pumped | 7 | 37 | 22 |
| II | Succinate dehydrogenase | Succinate -> coenzyme Q; also part of the TCA cycle | 0 pumped | 0 | 4 | 4 |
| III | Ubiquinol:cytochrome *c* oxidoreductase, or cytochrome `bc1` | Coenzyme Q -> cytochrome *c* | 4 released/translocated through the Q cycle | 1 | 9 | 6 |
| IV | Cytochrome *c* oxidase | Cytochrome *c* -> O2 -> H2O | 2 pumped; matrix protons are also consumed to make water | 3 | 18-gene isoform-inclusive inventory | 30 |
| V | `F1Fo` ATP synthase | Proton return -> ATP synthesis | H+ flows back into the matrix | 2 | 18 current structural genes | 5 |

Important counting qualifications:

- **Complex I:** 44 different genes encode its subunit types. `NDUFAB1` occurs
  twice in the mature mammalian complex, so a particle has 45 protein chains
  even though it is encoded by 44 distinct genes [6].
- **Complex III:** ten distinct genes encode each protomer. Cleavage of the
  `UQCRFS1` targeting sequence creates a peptide that remains bound, producing
  the traditional count of 11 polypeptides per protomer [7]. Complex III is an
  obligate dimer, conventionally written `CIII2`.
- **Complex IV:** one mature mammalian enzyme has 14 subunit types: three mtDNA
  core subunits and 11 nuclear subunits. The human gene inventory is larger
  because several nuclear subunit positions have tissue- or condition-specific
  paralogs. `COX7A2L` is also dual-annotated as a Complex IV-associated subunit
  and a supercomplex-assembly factor.
- **Complex V:** the structural list contains 20 current genes, but the enzyme
  contains multiple copies of some products, including three alpha, three beta,
  and multiple c-ring subunits. `ATP5IF1` is a bound regulator/inhibitor rather
  than a constitutive part of the rotary motor; MitoCarta nevertheless includes
  it in its operational “CV subunits” set.

## The two genomes that build OXPHOS

Human mtDNA is a 16,569-base-pair circular genome. It encodes 13 OXPHOS
proteins, 22 tRNAs, and two rRNAs; the standard human mtDNA reference is
NC_012920.1 [4]. All other OXPHOS subunits and all curated assembly factors are
nuclear encoded.

| Complex | mtDNA-encoded protein genes |
|---|---|
| I | `MT-ND1`, `MT-ND2`, `MT-ND3`, `MT-ND4`, `MT-ND4L`, `MT-ND5`, `MT-ND6` |
| II | None |
| III | `MT-CYB` |
| IV | `MT-CO1`, `MT-CO2`, `MT-CO3` |
| V | `MT-ATP6`, `MT-ATP8` |

This division creates a **mitonuclear coordination problem**:

- Nuclear OXPHOS transcripts are made in the nucleus, translated on cytosolic
  ribosomes, and their proteins are imported into mitochondria.
- mtDNA OXPHOS transcripts are made and translated inside mitochondria using
  nuclear-encoded transcription, RNA-processing, and mitochondrial-ribosome
  machinery.
- Subunits from both sources must appear in the correct amounts, acquire their
  cofactors, and assemble in the inner membrane.
- Failure in mtDNA replication, mitochondrial translation, protein import, or
  complex assembly can therefore impair OXPHOS even when the structural genes
  themselves are unchanged.

Complex II is the only one of the five complexes whose structural proteins are
entirely nuclear encoded. It is consequently a useful biological comparator
when studying nuclear-versus-mtDNA coordination.

## From electrons to ATP: the chemistry step by step

### 1. Reduced cofactors deliver electrons

Catabolism produces NADH and reduced flavins. NADH donates a pair of electrons
to Complex I. Succinate oxidation reduces the covalently bound FAD in Complex
II, and those electrons enter the same coenzyme Q pool. Fatty-acid oxidation
can feed the Q pool through electron-transfer flavoprotein and `ETFDH`; other
enzymes such as `GPD2`, `DHODH`, `SQOR`, and `PRODH` also reduce coenzyme Q.

### 2. Complexes I, III, and IV build a proton-motive force

The inner mitochondrial membrane is highly impermeable to ions. Moving protons
from the matrix to the intermembrane space stores energy as:

- a voltage difference, or membrane potential (`delta psi`); and
- a pH difference (`delta pH`).

Together these are the **proton-motive force**. For a pair of electrons that
enters at NADH, the conventional tally is approximately 10 pumped protons:
four at Complex I, four through Complex III's Q cycle, and two at Complex IV.
Electrons that enter through Complex II bypass the four-proton contribution of
Complex I, giving approximately six pumped protons per pair. Complex II is part
of electron transport but is not a proton pump [3,5].

### 3. Complex V converts the gradient into ATP

Protons return to the matrix through the membrane `Fo` sector of ATP synthase.
This rotates the c ring and central stalk. Rotation forces the three catalytic
beta subunits in the matrix-facing `F1` head through conformations that bind
ADP and inorganic phosphate, synthesize ATP, and release ATP [8]. Electron flow
and ATP synthesis are therefore coupled indirectly through the proton-motive
force.

### 4. ATP and its substrates must cross the membrane

The core complexes do not by themselves deliver ATP to the cytosol. Important
supporting transporters include:

- `SLC25A3`, the mitochondrial phosphate carrier;
- `SLC25A4`, `SLC25A5`, `SLC25A6`, and `SLC25A31`, tissue-dependent ADP/ATP
  carrier genes; and
- `VDAC1`, `VDAC2`, and `VDAC3`, outer-membrane channels.

These proteins are functionally necessary for cellular ATP exchange but are
not Complex V structural subunits.

## Complex I: NADH:ubiquinone oxidoreductase

### What Complex I does

Complex I oxidizes matrix NADH, transfers two electrons through FMN and a chain
of iron-sulfur clusters to coenzyme Q, and couples that reaction to pumping
approximately four protons from the matrix to the intermembrane space [5]. It
has an L shape:

- the **N module** accepts electrons from NADH;
- the **Q module** reduces coenzyme Q; and
- the membrane **P module** performs proton translocation.

Fourteen core subunits contain the conserved catalytic machinery. Thirty
additional accessory, or supernumerary, subunit types surround and stabilize
that core. The 44 distinct subunit genes produce 45 chains because there are
two copies of `NDUFAB1` [6].

### Complex I structural genes

| Genome/role | Genes |
|---|---|
| mtDNA-encoded membrane-core subunits (7) | `MT-ND1`, `MT-ND2`, `MT-ND3`, `MT-ND4`, `MT-ND4L`, `MT-ND5`, `MT-ND6` |
| Nuclear-encoded catalytic core (7) | `NDUFV1`, `NDUFV2`, `NDUFS1`, `NDUFS2`, `NDUFS3`, `NDUFS7`, `NDUFS8` |
| Nuclear-encoded accessory subunits (30) | `NDUFV3`; `NDUFS4`, `NDUFS5`, `NDUFS6`; `NDUFA1`, `NDUFA2`, `NDUFA3`, `NDUFA5`, `NDUFA6`, `NDUFA7`, `NDUFA8`, `NDUFA9`, `NDUFA10`, `NDUFA11`, `NDUFA12`, `NDUFA13`, `NDUFAB1`; `NDUFB1`-`NDUFB11`; `NDUFC1`, `NDUFC2` |

The gene `NDUFA4` is intentionally absent. Despite its historical name, it is
now assigned to Complex IV, not Complex I [9].

### Complex I assembly factors

MitoCarta3.0 assigns 22 genes to Complex I assembly:

```text
ACAD9, AIFM1, COA1, DMAC1, DMAC2, ECSIT, FOXRED1, LYRM2,
NDUFAF1, NDUFAF2, NDUFAF3, NDUFAF4, NDUFAF5, NDUFAF6,
NDUFAF7, NDUFAF8, NUBPL, TIMMDC1, TMEM126A, TMEM126B,
TMEM186, TMEM70
```

These proteins have different jobs. For example, the `NDUFAF` proteins support
module-specific assembly and maturation; `NUBPL` supports iron-sulfur-cluster
delivery; and the `ACAD9`-`ECSIT`-`NDUFAF1` machinery participates in membrane
arm assembly. An assembly factor can be essential for Complex I abundance
without being present in the mature holoenzyme.

## Complex II: succinate dehydrogenase

### What Complex II does

Complex II is shared by two pathways:

1. In the TCA cycle, it oxidizes succinate to fumarate.
2. In the respiratory chain, it transfers the resulting electrons through FAD
   and iron-sulfur centers to coenzyme Q.

Complex II does **not** pump protons. Electrons entering here consequently
support less ATP synthesis than electrons entering through Complex I.

### Complex II structural genes

All four are nuclear encoded:

| Gene | Principal role |
|---|---|
| `SDHA` | Matrix-facing flavoprotein; binds succinate and FAD |
| `SDHB` | Iron-sulfur subunit; transfers electrons toward coenzyme Q |
| `SDHC` | Membrane anchor and part of the coenzyme Q/heme region |
| `SDHD` | Membrane anchor and part of the coenzyme Q/heme region |

There are no mtDNA-encoded Complex II structural subunits.

### Complex II assembly factors

```text
SDHAF1, SDHAF2, SDHAF3, SDHAF4
```

`SDHAF2` is especially important for covalent FAD attachment to `SDHA`;
`SDHAF1` and `SDHAF3` support maturation of the iron-sulfur subunit; and
`SDHAF4` supports late assembly/stability.

## Complex III: ubiquinol:cytochrome c oxidoreductase

### What Complex III does

Complex III accepts electrons from ubiquinol (`QH2`) and transfers them one at
a time to cytochrome *c*. Its **Q cycle** couples the two-electron chemistry of
coenzyme Q to the one-electron chemistry of cytochrome *c* and contributes
approximately four protons to the intermembrane side per electron pair.

Mammalian Complex III is an obligate dimer (`CIII2`). Each protomer is encoded
by ten genes, but the cleaved targeting peptide of `UQCRFS1` remains bound as
an additional polypeptide, which explains the classical “11-subunit” count
[7].

### Complex III structural genes

| Genome/role | Genes |
|---|---|
| mtDNA encoded (1) | `MT-CYB` |
| Nuclear encoded (9) | `CYC1`, `UQCRFS1`, `UQCRC1`, `UQCRC2`, `UQCRH`, `UQCRB`, `UQCRQ`, `UQCR10`, `UQCR11` |
| Direct catalytic/redox-center subunits | `MT-CYB`, `CYC1`, `UQCRFS1` |

`MT-CYB` contains the two b hemes and the quinone-binding sites. `UQCRFS1`
contains the Rieske `2Fe-2S` center, and `CYC1` contains heme c1. The remaining
subunits organize and stabilize the enzyme.

### Complex III assembly and quality-control factors

```text
BCS1L, LYRM7, TTC19, UQCC1, UQCC2, UQCC3
```

`UQCC1`-`UQCC3` support early `MT-CYB`-centered assembly, `BCS1L` and `LYRM7`
support incorporation/maturation of `UQCRFS1`, and `TTC19` has a post-assembly
quality-control role. The literature continues to identify additional
Complex III-associated factors, so this is explicitly the frozen MitoCarta3.0
set rather than a claim that no other factor exists.

## Complex IV: cytochrome c oxidase

### What Complex IV does

Complex IV accepts electrons from reduced cytochrome *c* and transfers four
electrons to one oxygen molecule, forming two water molecules. It pumps protons
and also consumes matrix protons in water formation. Because oxygen is reduced
only here, Complex IV is the terminal oxidase of the chain.

The catalytic core is mtDNA encoded:

- `MT-CO1` contains heme a, heme a3, and the CuB catalytic center;
- `MT-CO2` contains the CuA center that accepts electrons from cytochrome *c*;
  and
- `MT-CO3` helps organize the membrane core and proton-transfer environment.

### Complex IV structural-gene inventory

MitoCarta's human gene inventory contains 21 genes because several of the 11
nuclear subunit positions have alternative isoforms.

| Genome/role | Genes |
|---|---|
| mtDNA-encoded catalytic core (3) | `MT-CO1`, `MT-CO2`, `MT-CO3` |
| Nuclear subunit families (18 genes) | `COX4I1`, `COX4I2`; `COX5A`, `COX5B`; `COX6A1`, `COX6A2`; `COX6B1`, `COX6B2`; `COX6C`; `COX7A1`, `COX7A2`, `COX7A2L`; `COX7B`, `COX7B2`; `COX7C`; `COX8A`, `COX8C`; `NDUFA4` |

Do not interpret all 21 genes as 21 simultaneous subunits in one enzyme.
Paralogs such as `COX4I1`/`COX4I2`, `COX6A1`/`COX6A2`, and
`COX6B1`/`COX6B2` can occupy corresponding positions in tissue- or
condition-dependent ways. `NDUFA4` is the recognized 14th Complex IV subunit
[9]. `COX7A2L`, also called SCAF1 in the literature, has a context-dependent
role in respiratory supercomplex organization and is dual-classified by
MitoCarta.

### Complex IV assembly factors

MitoCarta3.0 assigns 30 genes to Complex IV assembly:

```text
CEP89, CMC1, CMC2, COA1, COA3, COA4, COA5, COA6, COA7, COA8,
COX10, COX11, COX14, COX15, COX16, COX17, COX18, COX19, COX20,
HIGD1A, PET100, PET117, PNKD, SCO1, SCO2, SMIM20, SURF1, TACO1,
TIMM21, TMEM177
```

Useful functional groupings include:

- **Heme a synthesis:** `COX10`, `COX15`.
- **Copper delivery and metal-center maturation:** `COX11`, `COX17`,
  `COX19`, `SCO1`, `SCO2`, and `COA6`.
- **Synthesis, insertion, or stabilization of mtDNA core subunits:** `TACO1`,
  `COA3`, `COX14`, `COX18`, and `COX20`.
- **Late assembly and stabilization:** factors including `SURF1`, `PET100`,
  `PET117`, and several `COA` proteins.

Because Complex IV needs heme a, copper, mitochondrial translation, and membrane
insertion, a defect in any of those supporting systems can appear as Complex IV
deficiency even if all structural genes are intact.

## Complex V: F1Fo ATP synthase

### What Complex V does

Complex V is a rotary molecular motor. Its membrane `Fo` sector conducts
protons and turns a c ring. The attached central stalk rotates within the
matrix-facing `F1` catalytic head. Three beta subunits cycle through distinct
conformations, synthesizing three ATP molecules per full rotation [8].

Complex V can run in reverse and hydrolyze ATP to pump protons when the
proton-motive force collapses. The regulatory protein `ATP5IF1` suppresses
wasteful reverse ATP hydrolysis under appropriate conditions.

### Current Complex V structural genes

| Sector/role | Genome | Current genes |
|---|---|---|
| `F1` alpha3-beta3 catalytic head | Nuclear | `ATP5F1A`, `ATP5F1B` |
| `F1` central rotor/stalk | Nuclear | `ATP5F1C`, `ATP5F1D`, `ATP5F1E` |
| c-ring rotor | Nuclear | `ATP5MC1`, `ATP5MC2`, `ATP5MC3` |
| Proton-channel core | mtDNA | `MT-ATP6`, `MT-ATP8` |
| Peripheral stator | Nuclear | `ATP5PB`, `ATP5PD`, `ATP5PF`, `ATP5PO` |
| Mitochondrial membrane/dimerization subunits | Nuclear | `ATP5ME`, `ATP5MF`, `ATP5MG`, `ATP5MJ`, `ATP5MK` |
| Coupling/proton-conductance subunit s, or factor B | Nuclear | `DMAC2L` |

There are 20 current structural genes in this table: 18 nuclear and two mtDNA.
Gene count is not protein-copy count. For example, `ATP5MC1`, `ATP5MC2`, and
`ATP5MC3` encode closely related c-subunit forms that contribute to a
multi-copy c ring.

### Complex V symbol updates and regulator

| Current symbol | Symbol in the frozen MitoCarta3.0 table | Other common name | Interpretation |
|---|---|---|---|
| `ATP5MJ` | `ATP5MPL` | 6.8PL, subunit j | Structural membrane subunit |
| `ATP5MK` | `ATP5MD` | DAPIT, `USMG5`, subunit k | Structural membrane/dimerization subunit |
| `ATP5IF1` | `ATP5IF1` | IF1 | Reversible ATPase inhibitor/regulator, not a constitutive rotary-motor subunit |

NCBI records `ATP5MPL` as an alias of current `ATP5MJ` and `ATP5MD` as an alias
of current `ATP5MK` [10,11]. The frozen MitoCarta “CV subunits” set contains 21
genes because it includes `ATP5IF1` in addition to the 20 structural genes.
This tutorial preserves that distinction so analyses can reproduce the project
annotation without misdescribing IF1's role.

### Complex V assembly factors

```text
ATPAF1, ATPAF2, ATPSCKMT, FMC1, TMEM70
```

`ATPAF1` and `ATPAF2` support assembly of the `F1` alpha and beta subunits;
`TMEM70` is important for ATP synthase biogenesis and oligomerization;
`ATPSCKMT` supports post-translational maturation of the c subunit; and `FMC1`
supports Complex V stability/assembly.

## The mobile carriers between complexes

### Coenzyme Q, or ubiquinone

Coenzyme Q is a lipid-soluble small molecule, not a protein encoded by one
“CoQ gene.” It diffuses within the inner membrane. Complexes I and II and
several other dehydrogenases reduce `Q` to `QH2`; Complex III oxidizes `QH2`.

MitoCarta's coenzyme Q metabolism set is:

```text
COQ2, COQ3, COQ4, COQ5, COQ6, COQ7, COQ8A, COQ8B, COQ9,
COQ10A, COQ10B, PDSS1, PDSS2
```

These genes synthesize, modify, organize, or handle the coenzyme Q pool. They
are not structural subunits of Complexes I-III.

### Cytochrome c

`CYCS` is the nuclear gene encoding cytochrome *c*, the small soluble protein
that carries one electron at a time from Complex III to Complex IV on the
intermembrane-space side of the inner membrane. `HCCS` encodes holocytochrome
*c* synthase, which attaches heme to apocytochrome *c*.

MitoCarta groups `CYCS` and `HCCS` under its “Cytochrome C” pathway and also
includes them in the 102-gene operational “OXPHOS subunits” collection. For
mechanistic interpretation, `CYCS` is a mobile carrier and `HCCS` is its
maturation enzyme; neither is a numbered I-V complex subunit.

## Respiratory supercomplexes

Complexes can form higher-order assemblies. The best-known mammalian
**respirasome** contains Complex I, a Complex III dimer, and one or more copies
of Complex IV. Supercomplexes can stabilize components and organize the inner
membrane, but they do not turn the chain into a sealed wire: coenzyme Q and
cytochrome *c* remain mobile carriers.

MitoCarta's focused respirasome-assembly set is:

```text
COX7A2L, HIGD1A, HIGD2A, RAB5IF
```

Some of these genes also have complex-specific annotations. For example,
`COX7A2L` is included in the Complex IV subunit inventory, and `HIGD1A` is in
the Complex IV assembly set. Gene sets must therefore be stored as many-to-many
annotations rather than forcing every gene into exactly one category.

## A reproducible gene-set accounting for this project

Using the frozen MitoCarta3.0-derived table:

| Operational set | Gene count | Interpretation |
|---|---:|---|
| Complex I subunits | 44 | 7 mtDNA + 37 nuclear; 44 gene types, 45 physical chains because `NDUFAB1` is duplicated |
| Complex II subunits | 4 | All nuclear |
| Complex III subunits | 10 | 1 mtDNA + 9 nuclear; 11 traditional polypeptides because a `UQCRFS1` cleavage peptide remains bound |
| Complex IV subunit genes | 21 | 3 mtDNA + 18 nuclear; isoform-inclusive, not 21 simultaneous chains |
| Complex V subunit/regulator set | 21 | 2 mtDNA + 18 current nuclear structural genes + `ATP5IF1` |
| Cytochrome C | 2 | `CYCS`, `HCCS` |
| OXPHOS subunits | 102 | Union of the five complex sets plus `CYCS` and `HCCS` |
| OXPHOS assembly factors | 68 | Complex-specific and supercomplex assembly annotations; may overlap other sets |

The five complex lists contain 100 entries in the frozen representation. After
recognizing `ATP5IF1` as a regulator, 99 complex-assigned gene entries remain;
the isoform and dual-role caveats for Complex IV still apply. The full 102-gene
MitoCarta operational set is valuable for reproducible enrichment analysis,
but its label should not be interpreted as “102 permanent structural
proteins.”

## Complete complex-by-complex gene checklist

The following compact lists are useful for manual review or code validation.
They use current symbols for Complex V and otherwise reproduce the MitoCarta3.0
complex assignments.

### Structural or complex-associated subunit genes

```text
Complex I — mtDNA (7)
MT-ND1, MT-ND2, MT-ND3, MT-ND4, MT-ND4L, MT-ND5, MT-ND6

Complex I — nuclear (37)
NDUFA1, NDUFA2, NDUFA3, NDUFA5, NDUFA6, NDUFA7, NDUFA8,
NDUFA9, NDUFA10, NDUFA11, NDUFA12, NDUFA13, NDUFAB1,
NDUFB1, NDUFB2, NDUFB3, NDUFB4, NDUFB5, NDUFB6, NDUFB7,
NDUFB8, NDUFB9, NDUFB10, NDUFB11, NDUFC1, NDUFC2,
NDUFS1, NDUFS2, NDUFS3, NDUFS4, NDUFS5, NDUFS6, NDUFS7,
NDUFS8, NDUFV1, NDUFV2, NDUFV3

Complex II — nuclear (4)
SDHA, SDHB, SDHC, SDHD

Complex III — mtDNA (1)
MT-CYB

Complex III — nuclear (9)
CYC1, UQCR10, UQCR11, UQCRB, UQCRC1, UQCRC2, UQCRFS1,
UQCRH, UQCRQ

Complex IV — mtDNA (3)
MT-CO1, MT-CO2, MT-CO3

Complex IV — nuclear, isoform-inclusive (18)
COX4I1, COX4I2, COX5A, COX5B, COX6A1, COX6A2, COX6B1,
COX6B2, COX6C, COX7A1, COX7A2, COX7A2L, COX7B, COX7B2,
COX7C, COX8A, COX8C, NDUFA4

Complex V — mtDNA (2)
MT-ATP6, MT-ATP8

Complex V — nuclear structural genes, current symbols (18)
ATP5F1A, ATP5F1B, ATP5F1C, ATP5F1D, ATP5F1E,
ATP5MC1, ATP5MC2, ATP5MC3, ATP5ME, ATP5MF, ATP5MG,
ATP5MJ, ATP5MK, ATP5PB, ATP5PD, ATP5PF, ATP5PO, DMAC2L

Complex V regulator
ATP5IF1
```

### Assembly-factor genes

```text
Complex I assembly (22)
ACAD9, AIFM1, COA1, DMAC1, DMAC2, ECSIT, FOXRED1, LYRM2,
NDUFAF1, NDUFAF2, NDUFAF3, NDUFAF4, NDUFAF5, NDUFAF6,
NDUFAF7, NDUFAF8, NUBPL, TIMMDC1, TMEM126A, TMEM126B,
TMEM186, TMEM70

Complex II assembly (4)
SDHAF1, SDHAF2, SDHAF3, SDHAF4

Complex III assembly/quality control (6)
BCS1L, LYRM7, TTC19, UQCC1, UQCC2, UQCC3

Complex IV assembly (30)
CEP89, CMC1, CMC2, COA1, COA3, COA4, COA5, COA6, COA7,
COA8, COX10, COX11, COX14, COX15, COX16, COX17, COX18,
COX19, COX20, HIGD1A, PET100, PET117, PNKD, SCO1, SCO2,
SMIM20, SURF1, TACO1, TIMM21, TMEM177

Complex V assembly (5)
ATPAF1, ATPAF2, ATPSCKMT, FMC1, TMEM70

Respirasome assembly (4)
COX7A2L, HIGD1A, HIGD2A, RAB5IF
```

`COA1` is annotated to both Complex I and IV assembly, while `TMEM70` is
annotated to both Complex I and V assembly. `COX7A2L` and `HIGD1A` likewise
cross the boundary between a numbered complex and respirasome organization.
The MitoCarta global OXPHOS-assembly set has 68 unique genes, not the simple sum
of every row above, because these memberships overlap.

## Genes that support OXPHOS without belonging to one complex

Many nuclear genes are necessary for OXPHOS but should not be assigned as a
subunit or a complex-specific assembly factor. Major examples include:

| Supporting process | Illustrative genes |
|---|---|
| mtDNA replication and maintenance | `POLG`, `POLG2`, `TWNK`, `SSBP1`, `TFAM`, `RNASEH1`, `MGME1` |
| Mitochondrial transcription | `POLRMT`, `TFAM`, `TFB2M`, `TEFM` |
| mtRNA processing and stability | `LRPPRC`, `SLIRP`, `FASTKD2`, `FASTKD5`, `GRSF1`, `PNPT1` |
| Mitochondrial translation | `MRPL*`, `MRPS*`, `TUFM`, `TSFM`, `GFM1`, mitochondrial aminoacyl-tRNA synthetases |
| Inner-membrane insertion | `OXA1L`, `TIMM21` |
| Iron-sulfur-cluster biogenesis | `NFS1`, `ISCU`, `FXN`, `LYRM4`, `HSCB`, `HSPA9`, `ISCA1`, `ISCA2`, `IBA57`, `NUBPL` |
| Coenzyme Q metabolism | `PDSS1`, `PDSS2`, `COQ2`, `COQ3`, `COQ4`, `COQ5`, `COQ6`, `COQ7`, `COQ8A`, `COQ8B`, `COQ9`, `COQ10A`, `COQ10B` |
| Heme and copper handling | `COX10`, `COX15`, `COX17`, `SCO1`, `SCO2`, `ABCB7`, `FECH` |
| Protein import and proteostasis | `TOMM*`, `TIMM*`, `LONP1`, `CLPP`, `AFG3L2`, `YME1L1` |

The wildcard notation here indicates gene families for orientation, not a
ready-made statistical gene set. A reproducible analysis should expand every
family to explicit approved symbols from a frozen annotation release.

## How to interpret OXPHOS RNA data correctly

OXPHOS is a biochemical flux, whereas RNA sequencing measures transcript
abundance. More OXPHOS RNA does not necessarily mean more respiration, and less
RNA does not necessarily mean less ATP. Between RNA and respiratory flux lie:

- translation and protein import;
- mtDNA copy number and heteroplasmy;
- complex assembly and cofactor insertion;
- protein turnover and supercomplex organization;
- substrate, ADP, phosphate, coenzyme Q, and oxygen availability;
- membrane potential, proton leak, and uncoupling; and
- the number, mass, and health of mitochondria per cell.

For single-cell or single-nucleus Alzheimer transcriptomics, use the following
interpretive rules:

1. **Separate genome origin.** Score nuclear and mtDNA OXPHOS genes separately
   before combining them. Opposite directions can reveal mitonuclear
   discordance, technical differences, or compensatory biology.
2. **Separate structural subunits from assembly factors.** A fall in an
   assembly factor is not the same observation as a fall in a catalytic
   subunit, although both may impair the same complex.
3. **Treat Complex II as a special comparator.** It is nuclear only, belongs to
   both the TCA cycle and respiratory chain, and does not pump protons.
4. **Do not equate mitochondrial-read fraction with OXPHOS activity.** A high
   fraction can reflect stress, membrane damage, cytoplasmic RNA loss, or cell
   quality. In single-nucleus RNA-seq, mtRNA recovery also differs fundamentally
   from whole-cell RNA-seq.
5. **Track detectability.** A gene absent from a nucleus-level assay was not
   necessarily biologically absent. Report the tested/measured denominator for
   every complex and cell type.
6. **Resolve symbols and aliases before enrichment.** In this project,
   `ATP5MPL` -> `ATP5MJ` and `ATP5MD` -> `ATP5MK` must be handled explicitly.
7. **Avoid functional overstatement.** Prefer “Complex I transcript abundance
   was lower” over “Complex I activity was impaired” unless activity was
   measured directly.

## Measurements that can validate a transcriptomic hypothesis

| Question | More direct measurement |
|---|---|
| Is basal or maximal respiration altered? | Oxygen-consumption respirometry with controlled substrates, ADP, uncouplers, and inhibitors |
| Which complex has lower enzymatic activity? | Spectrophotometric or polarographic complex-specific enzyme assays |
| Are intact complexes or supercomplexes reduced? | Blue-native PAGE, in-gel activity, complexome profiling, or native mass spectrometry |
| Is ATP production altered? | Mitochondrial ATP synthesis rate with matched substrate and ADP conditions |
| Is the proton-motive force altered? | Membrane-potential and pH-gradient probes with appropriate controls |
| Is mtDNA biology altered? | mtDNA copy number, heteroplasmy, transcription, and mitochondrial translation assays |
| Are proteins concordant with RNA? | Targeted proteomics or immunoblotting for nuclear- and mtDNA-encoded subunits |

No single assay captures the entire pathway. For example, oxygen consumption
can change because of ATP demand, proton leak, substrate delivery, or electron
transport capacity. A strong validation design combines flux, complex
abundance/activity, and mitonuclear measurements.

## Common misconceptions

### “All five complexes pump protons.”

False. Complexes I, III, and IV build the gradient. Complex II transfers
electrons without pumping protons. Complex V normally lets protons flow back to
the matrix while making ATP.

### “Complex V is the final electron-transfer complex.”

False. Oxygen receives electrons at Complex IV. Complex V is powered by the
proton gradient and does not accept electrons from Complex IV.

### “The mitochondrial genome encodes mitochondria.”

Misleading. mtDNA encodes only 13 OXPHOS proteins plus mitochondrial rRNAs and
tRNAs. The nucleus encodes the large majority of mitochondrial proteins,
including most OXPHOS subunits and all curated assembly factors.

### “Every gene with an `MT-` prefix is an OXPHOS protein.”

False. Human mtDNA also encodes rRNAs and tRNAs. Conversely, most mitochondrial
proteins are nuclear encoded and do not have an `MT-` prefix.

### “All `NDUFA` genes are Complex I.”

Almost, but `NDUFA4` is the famous exception: it is a Complex IV subunit [9].
`NDUFAF1`-`NDUFAF8` are assembly factors, not mature Complex I subunits.

### “A pathway score measures ATP production.”

False. An RNA-derived pathway score summarizes measured transcripts. It does
not directly measure electron flux, oxygen reduction, proton pumping, membrane
potential, or ATP synthesis.

## One-minute memory aid

- **I:** NADH enters; 7 mtDNA + 37 nuclear subunit genes; pumps 4 H+.
- **II:** succinate/TCA entry; 4 nuclear genes; pumps 0 H+.
- **Q:** lipid-soluble two-electron carrier linking I/II and other enzymes to
  III.
- **III:** Q cycle; 1 mtDNA + 9 nuclear genes; contributes 4 H+; passes one
  electron at a time to cytochrome *c*.
- **Cytochrome c:** soluble carrier encoded by nuclear `CYCS`.
- **IV:** reduces O2 to H2O; 3 mtDNA core genes; pumps 2 H+ per electron pair.
- **V:** 2 mtDNA + 18 nuclear structural genes; lets H+ return and makes ATP.
- **Only mtDNA protein genes:** 7 `MT-ND`, 1 `MT-CYB`, 3 `MT-CO`, and 2
  `MT-ATP` genes.

## References and authoritative resources

1. Rath S, et al. MitoCarta3.0: an updated mitochondrial proteome now with
   sub-organelle localization and pathway annotations. *Nucleic Acids
   Research*. 2021. [doi:10.1093/nar/gkaa1011](https://doi.org/10.1093/nar/gkaa1011)
2. Broad Institute.
   [MitoCarta3.0 project, inventory, and downloads](https://www.broadinstitute.org/mitocarta/mitocarta30-inventory-mammalian-mitochondrial-proteins-and-pathways)
   and [MitoCarta3.0 documentation](https://www.broadinstitute.org/mitocarta30-documentation).
3. Reactome.
   [Respiratory electron transport, Homo sapiens (R-HSA-611105)](https://reactome.org/content/detail/R-HSA-611105).
4. NCBI RefSeq.
   [Homo sapiens mitochondrion, complete genome (NC_012920.1)](https://www.ncbi.nlm.nih.gov/nuccore/NC_012920.1).
5. Jones AJY, et al. Respiratory Complex I in *Bos taurus* and *Paracoccus
   denitrificans* pumps four protons for every NADH oxidized. *Journal of
   Biological Chemistry*. 2017.
   [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5377811/)
6. Bridges HR, et al. Subunit NDUFV3 is present in two distinct isoforms in
   mammalian Complex I. *Biochimica et Biophysica Acta*. 2017. The article
   explains the 44 distinct subunits/45 chains distinction and duplicated
   `NDUFAB1`.
   [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5293009/)
7. Iwata S, et al. Complete structure of the 11-subunit bovine mitochondrial
   cytochrome `bc1` complex. *Science*. 1998.
   [PubMed](https://pubmed.ncbi.nlm.nih.gov/9651245/)
8. Reactome.
   [Formation of ATP by chemiosmotic coupling, Homo sapiens (R-HSA-163210)](https://reactome.org/content/detail/R-HSA-163210).
9. Balsa E, et al. `NDUFA4` is a subunit of Complex IV of the mammalian electron
   transport chain. *Cell Metabolism*. 2012.
   [Article](https://www.sciencedirect.com/science/article/pii/S1550413112002938)
10. NCBI Gene.
    [`ATP5MJ`, current symbol; `ATP5MPL` alias](https://www.ncbi.nlm.nih.gov/gene/9556).
11. NCBI Gene.
    [`ATP5MK`, current symbol; `ATP5MD`/`USMG5` aliases](https://www.ncbi.nlm.nih.gov/gene/84833).

## Versioning note

Gene membership and nomenclature evolve as structures improve and gene symbols
are revised. For project analyses, preserve the frozen MitoCarta3.0 source and
record any symbol normalization separately. For biological interpretation,
state the annotation release, distinguish subunits from factors and carriers,
and document exceptions such as `NDUFA4`, `ATP5MJ`, `ATP5MK`, `ATP5IF1`, and
`COX7A2L`.
