# Mitochondrial module tiers and expansion plan

## Short answer

Yes, there are other mitochondrial pathways that are worth studying. However, they should not all be added to the main Claim 1 test as if they answer the same question.

A **module** is a predefined group of genes that perform a related biological job. For example, the nuclear OXPHOS module contains nuclear-DNA genes that help build the mitochondrial respiratory-chain complexes.

The clearest approach is to divide the modules into three levels:

1. **Core Claim 1 modules** test the main respiratory claim.
2. **Candidate-specific modules** test the three network-nominated systems in C4, C5, and C6.
3. **Secondary modules** explore additional mitochondrial mechanisms without changing the original claim.

This separation is important. It prevents an interesting result from a newly added pathway from being used to rescue a failed test of the original respiratory claim.

## Recommended module structure

| Level | Module | Reference gene count | Main purpose |
|---|---|---:|---|
| Core C1 | mtDNA OXPHOS | 13 | Test mitochondrial-DNA respiratory genes |
| Core C1 | Nuclear OXPHOS | 86 | Test nuclear-DNA respiratory-complex structural genes |
| Candidate C4 | Mitochondrial translation | 155; 154 after removing `TUFM` | Test the `APOE–TUFM` hypothesis |
| Candidate C5 | ATP synthase/Complex V | 21; 20 after removing `ATP5IF1` | Test the `LAMTOR5–ATP5IF1` hypothesis |
| Candidate C6 | Mitophagy | 14; 13 after removing `PARK7` | Test the `GABARAPL2–CHCHD2/PARK7` hypothesis |
| Secondary | ROS and glutathione metabolism | 27 | Test mitochondrial oxidative-stress defense |
| Secondary | Protein import and sorting | 48 | Test whether moving proteins into mitochondria is disrupted |
| Secondary | Mitochondrial chaperones | 16 | Test mitochondrial protein folding and stress responses |
| Secondary | OXPHOS assembly factors | 68 | Test construction of respiratory complexes |
| Secondary | MIB/MICOS and inner-membrane organization | 19 | Test mitochondrial cristae and inner-membrane structure |

The gene counts above come from the normalized local MitoCarta3.0 membership table:

```text
results/minerva_production/11_pathway/pathway_membership_long.tsv.gz
```

## A recommended correction to the current four-module description

The four modules in the current plan do not all have the same job.

- The 13 mtDNA OXPHOS genes and 86 nuclear OXPHOS genes directly test the respiratory part of Claim 1.
- Mitochondrial translation is especially relevant to the C4 `APOE–TUFM` system.
- MIB/MICOS provides supporting evidence about mitochondrial membrane structure. It is not a direct test of C6.

Mitochondrial translation and MIB/MICOS should not be deleted. Instead, their roles should be labelled more precisely.

A Claim 1 result supported only by mitochondrial translation should be described as a **mitochondrial-translation change**. A result supported only by MIB/MICOS should be described as an **inner-membrane-organization change**. Neither result alone is enough to claim that the respiratory chain changed.

## Level 1: the core Claim 1 modules

### 1. mtDNA OXPHOS

This module contains the 13 protein-coding respiratory genes carried by mitochondrial DNA.

Its job is to answer:

> Does sex or APOE change the AD-associated expression pattern of mtDNA-encoded respiratory genes?

### 2. Nuclear OXPHOS

This module contains 86 nuclear-DNA genes that encode structural parts of respiratory complexes I–V.

Its job is to answer:

> Does sex or APOE change the AD-associated expression pattern of nuclear-encoded respiratory-complex genes?

These are the two modules that most directly support respiratory wording in Claim 1.

## Level 2: modules for the three candidate systems

### C4: `APOE–TUFM`

Use the mitochondrial-translation module.

`TUFM` helps mitochondria make proteins. Therefore, mitochondrial translation is the local biological program predicted by this candidate system.

When testing whether `TUFM` agrees with the wider translation program, remove `TUFM` from the module score:

```text
TUFM expression
        compared with
translation score calculated from the other 154 genes
```

This is called a **target-excluded score**. It prevents `TUFM` from creating its own supporting result.

### C5: `LAMTOR5–ATP5IF1`

Use the Complex V, or ATP-synthase, module.

The local MitoCarta Complex V subunit set contains 21 genes. It includes:

- `ATP5IF1`, the named readout;
- `MT-ATP6` and `MT-ATP8`, which are encoded by mitochondrial DNA;
- 18 nuclear structural ATP-synthase genes.

Remove `ATP5IF1` when testing the candidate system. This leaves 20 genes.

The recommended analysis is:

- use the 18 nuclear structural genes as the primary candidate-module score;
- use all 20 target-excluded genes as a sensitivity check.

This keeps the main score consistent with the separation between nuclear and mtDNA respiratory expression.

### C6: `GABARAPL2–CHCHD2/PARK7`

Use the MitoCarta mitophagy module.

**Mitophagy** is the process by which a cell identifies and removes damaged mitochondria. It is a reasonable local program for this candidate system because `GABARAPL2` is related to autophagy and `PARK7` is included in the MitoCarta mitophagy set.

The module contains 14 genes. Remove `PARK7` when calculating the candidate score, leaving 13 genes.

`CHCHD2` is not a member of the MitoCarta mitophagy set. Therefore:

- test `CHCHD2` separately as the required named readout;
- test `PARK7` separately as a secondary readout;
- compare them with the 13-gene target-excluded mitophagy score.

Experimental work in Alzheimer models has shown that changing mitophagy can affect amyloid, tau, and cognitive outcomes. This supports studying mitophagy, but it does not prove that the same mechanism occurs in these human RNA data ([Fang et al., 2019](https://doi.org/10.1038/s41593-018-0332-9)).

## Level 3: the best secondary modules

### 1. ROS and glutathione metabolism

**ROS**, or reactive oxygen species, are chemically reactive molecules that can damage cells when they become excessive. Glutathione is part of the cell's antioxidant defense.

This 27-gene module is a strong secondary choice because the existing Phase 11 analysis found:

- 11 upward and 44 downward female-ε4 occurrences;
- formal enrichment in the within-ε4 low-similarity tail;
- fold enrichment of 2.20;
- FDR of 0.037.

This was the clearest formal non-OXPHOS secondary pathway result in Phase 11.

### 2. Protein import and sorting

Most mitochondrial proteins are made outside mitochondria and must be moved into the organelle. This 48-gene module tests whether that transport machinery changes.

Phase 11 found:

- female ε4: 8 upward and 46 downward occurrences;
- male ε2: 46 upward and 58 downward occurrences.

These are descriptive results, not yet formal donor-level module tests.

### 3. Mitochondrial chaperones

Chaperones help other proteins fold correctly and protect them during stress.

This 16-gene module is worth testing because female ε4 had 37 significant chaperone occurrences, all downward. However, `HSPD1` contributed heavily to the pattern. The analysis must therefore check whether the result remains after removing `HSPD1`.

### 4. OXPHOS assembly factors

Structural OXPHOS genes are parts of respiratory complexes. Assembly factors help build those complexes but are not usually permanent parts of the completed structures.

The 68 assembly-factor genes should be tested separately from the 86 structural genes. A change in assembly factors could indicate disturbed construction or maintenance even when the structural genes show a weaker result.

### 5. MIB/MICOS and inner-membrane organization

This 19-gene module tests mitochondrial cristae and inner-membrane organization.

It should be secondary because:

- it is not the direct local module predicted for C6;
- it overlaps nuclear OXPHOS through `ATP5MD`, `ATP5ME`, and `ATP5MG`;
- an apparent agreement with nuclear OXPHOS is therefore not completely independent.

As a sensitivity analysis, remove those three overlapping genes and recalculate a 16-gene score.

## Valid modules to save for later exploration

| Module | Local MitoCarta gene count | Why it is not an immediate priority |
|---|---:|---|
| mtRNA metabolism | 76 | Relevant to mitonuclear biology, but not required for C1 or C4–C6 |
| Fatty-acid oxidation | 44 | Biologically relevant to APOE and metabolism, but current local evidence is limited |
| TCA cycle | 20 | Current results mainly suggest relative stability rather than coordinated change |
| Mitochondrial fission | 15 | Interesting for quality control, but narrower and currently less supported than mitophagy |
| Mitochondrial fusion | 9 | Same reason as fission; useful as a later quality-control follow-up |
| Cardiolipin synthesis | 16 | Relevant to inner-membrane biology, but not currently a leading local signal |
| Iron homeostasis | 5 | Potentially relevant to `FTL` and OPC biology, but the module is very small |
| Calcium cycle | 9 | Biologically plausible but not currently a leading Phase 11 result |

These pathways should not be discarded. They should be kept in an exploratory catalogue and tested later if the core or candidate results point toward them.

## Why not test every mitochondrial pathway as a primary result?

MitoCarta3.0 contains 149 hierarchical mitochondrial pathways covering seven broad areas of mitochondrial biology ([Rath et al., 2021](https://academic.oup.com/nar/article/49/D1/D1541/5974091)).

Testing all 149 pathways across seven sex/APOE comparisons and three broad cell classes would create:

```text
149 pathways × 7 comparisons × 3 cell classes = 3,129 tests
```

This causes two problems:

1. With thousands of tests, some pathways can look interesting by chance.
2. Many MitoCarta pathways overlap or are nested inside one another. For example, mitophagy is contained within a broader autophagy pathway. A result in both sets is not automatically two independent discoveries.

A whole-catalogue analysis can still be useful for discovery. It should be labelled exploratory, corrected across the complete catalogue, and followed by confirmation in another dataset.

## Rules for adding a module

A new module should enter the written plan only when all of the following are true:

1. It has one understandable biological job.
2. Its genes come from a curated source such as MitoCarta, not from whichever genes happen to be significant in the new analysis.
3. It either directly tests a planned candidate or has clear support from the existing Phase 11 evidence.
4. Enough of its genes are measured: normally at least 70% of the frozen list and at least 5 genes.
5. Its overlap with the other modules is measured and reported.
6. The exact genes, contrasts, cell contexts, and direction rules are written down before examining Phase 13 effects.
7. Its tests belong to a declared multiple-testing group.

When testing a candidate system, also remove its named readout from the corresponding module score. A candidate should not be allowed to provide both the question and most of its own supporting evidence.

## Statistical organization

Use separate testing groups for the different levels.

### Core C1 family

```text
2 core modules × 7 modifier comparisons × 3 broad cell classes
= 42 tests
```

Correct these 42 tests together. This family determines whether the direct respiratory part of C1 is supported.

### Candidate-module family

Put the prewritten C4, C5, and C6 module tests into one candidate-module family. Do not create a separate easy correction for each candidate.

The named-gene tests for `TUFM`, `ATP5IF1`, `CHCHD2`, and `PARK7` should form a separate candidate-gene family.

### Secondary-module family

Put ROS/glutathione, import, chaperone, assembly-factor, and MIB/MICOS tests into one secondary family. These results can extend the biological story, but they cannot rescue a failed core C1 result.

## Important interpretation rule

Phase 11 helped select several of these pathways, and Phase 13 will use the same ROSMAP donors with a stronger donor-level method. Therefore, Phase 13 is an **internal hypothesis test**, not independent replication.

Independent replication still requires another group of donors, such as an appropriately matched SEA-AD analysis. Protein measurements can add support from a different type of measurement, but protein data from the same ROSMAP donors are not an independent cohort.

## Final recommendation

Before running Phase 13:

1. Keep mtDNA OXPHOS and nuclear OXPHOS as the two direct C1 respiratory modules.
2. Freeze three target-excluded candidate modules:
   - translation without `TUFM`;
   - ATP synthase without `ATP5IF1`;
   - mitophagy without `PARK7`.
3. Freeze a secondary panel containing:
   - ROS/glutathione metabolism;
   - protein import and sorting;
   - mitochondrial chaperones;
   - OXPHOS assembly factors;
   - MIB/MICOS and inner-membrane organization.
4. Keep the remaining mitochondrial pathways in an exploratory catalogue.
5. Save the exact genes and module roles in a machine-readable manifest before viewing Phase 13 effects.

The number of candidate systems described as supported must equal the number that pass their own donor-level and network-validation requirements. A result from one module must not be used to compensate for a failed required module in another candidate system.

## Related project documents

- [Four respiratory module/program guide](four_respiratory_module_program.md)
- [Deep-dive next-steps plan](deep_dive_next_steps_plan.md)
- [Beginner guide to the core claims and candidate systems](beginner_guide_to_core_claims_and_three_candidate_systems.md)
- [Phase 11 mitochondrial pathway discussion](../analysis/mt_pathway/phase11_pathway_discussion.md)
