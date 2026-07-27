# Preliminary summary of mitochondrial results

**Status:** Preliminary figure-based summary  
**Prepared:** 2026-07-27

## Scope

This document summarizes the mitochondrial results currently shown in Figures 1A–1E and 3–6. It is intentionally descriptive and relies primarily on the information displayed in the SVG figures. It does not add new statistical tests, reanalyze the underlying data, or attempt a full biological interpretation.

The figures apply a mitochondrial-restricted analogue of the Yu analysis to AD-versus-NCI transcriptional results. Figure 1 summarizes mitochondrial-related differential-expression counts across fine cell types and sex–APOE strata. Figures 3–6 organize genes into shared, different, or opposite AD-response categories and examine Human MSigDB C2:CP pathway matches for high- and low-similarity score tails.

## Preliminary findings

### 1. Mitochondrial AD-associated transcriptional changes are widespread but heterogeneous

[Figure 1A](figure01/figure01A_mitochondrial_yu_analogue.svg) and [Figure 1B](figure01/figure01B_mitochondrial_yu_analogue.svg) show upregulated and downregulated mitochondrial-related DEG counts, respectively, for female and male APOE ε2, ε3/ε3, and ε4 groups.

- Altered mitochondrial-related genes occur across all major displayed cell classes, but the most continuous and visually prominent signal is in excitatory neurons and selected inhibitory neurons.
- Astrocytes, oligodendrocyte-lineage cells, immune cells, and vascular cells also show changes, although these are generally less continuous across fine cell types.
- The burden and direction of the response vary across sex–APOE strata. No single direction or stratum describes the entire figure.
- The downregulated panel has a higher legend maximum and broad blue coverage in several neuronal strata, suggesting that downregulated occurrences can be especially numerous. This is only a visual comparison: the up- and downregulated panels use separate color scales and should not be compared by color intensity alone.

### 2. Many APOE contrasts are driven by stratum-specific rather than uniformly shared responses

[Figure 1C](figure01/figure01C_mitochondrial_yu_analogue.svg) compares APOE groups within females, and [Figure 1D](figure01/figure01D_mitochondrial_yu_analogue.svg) makes the corresponding comparisons within males. Each pairwise comparison separates occurrences into:

- the same direction in both groups;
- the first group only;
- the second group only; and
- opposite directions.

Across both panels, the group-only rows are often more densely populated than the same-direction or opposite-direction rows. This is most visible across excitatory cell types, with more localized patterns in inhibitory and non-neuronal populations. At a preliminary level, the figures therefore indicate substantial APOE dependence in which mitochondrial-related AD responses reach the DEG threshold.

Opposite-direction occurrences are present but are less broadly distributed than the group-only categories. These plots consequently support heterogeneity across APOE strata more directly than they support a universal direction reversal.

### 3. Sex differences in the mitochondrial AD response depend on APOE background

[Figure 1E](figure01/figure01E_mitochondrial_yu_analogue.svg) compares females and males separately within APOE ε2, ε3/ε3, and ε4 groups.

- Female-only and male-only occurrences are widespread, particularly among excitatory neurons.
- Same-direction responses are also visible, but their distribution differs among the three APOE groups.
- Opposite-direction occurrences occur in each APOE background, with their cell-type distribution and apparent burden varying by genotype.
- Immune and vascular compartments show a more intermittent pattern, including cells for which a contrast was not estimable.

The direct figure-based conclusion is that sex-associated differences are not uniform across APOE groups. A formal sex-by-APOE or sex-by-diagnosis interaction cannot be inferred from these thresholded comparison categories alone.

### 4. Low-similarity genes repeatedly emphasize respiratory-chain biology

[Figure 3](figures03_to_06/figure03_mitochondrial_yu_analogue.svg) summarizes sex-shared and sex-divergent responses. [Figure 4](figures03_to_06/figure04_mitochondrial_yu_analogue.svg) and [Figure 5](figures03_to_06/figure05_mitochondrial_yu_analogue.svg) show the corresponding APOE ε2- and ε4-focused analyses.

In all three figures:

- the lowest-similarity lists contain multiple mitochondrially encoded respiratory-chain genes, including members of the `MT-ND`, `MT-CO`, and related groups;
- these low-similarity genes frequently accumulate occurrences in the Different columns and, for a subset of genes, the Opposite columns;
- the highest-similarity lists generally have fewer or lighter nonzero occurrence tiles; and
- the Bottom 200 score tails show strong pathway matches involving oxidative phosphorylation, the mitochondrial electron-transport chain, aerobic respiration, and curated Parkinson, Huntington, and Alzheimer disease pathways.

The Top 200 tails show a more varied set of mitochondrial processes, including TCA/Krebs-cycle, mitochondrial homeostasis, mitochondrial RNA/aminoacylation, and lipid or intermediary-metabolism terms. The displayed dot plots encode GeneRatio by point size and adjusted-P evidence by color; pathway names shown in the plots should therefore not all be assumed significant simply because they are displayed.

The recurrence of several neurodegeneration pathway labels should also be interpreted cautiously. These curated gene sets overlap substantially in respiratory-chain genes, so the repeated labels are consistent with one dominant mitochondrial respiration theme rather than necessarily representing several independent disease mechanisms.

### 5. APOE-stratified sex divergence retains a common mitochondrial core

[Figure 6](figures03_to_06/figure06_mitochondrial_yu_analogue.svg) compares sex divergence within APOE ε2, ε3/ε3, and ε4 backgrounds.

- The lowest-similarity gene lists in each APOE group again contain mitochondrially encoded respiratory-chain genes.
- The balance among Same, Different, and Opposite occurrences changes across APOE backgrounds, supporting genotype dependence in the pattern of sex divergence.
- The Bottom 200 sex-divergent tails from all three APOE groups match oxidative-phosphorylation/electron-transport and neurodegeneration-associated pathways.
- Additional pathway matches differ among APOE groups, including cellular-stress, cytoprotection, respiratory-complex, and metabolic terms.

Thus, the most stable cross-figure observation is a shared respiratory-chain component within a broader sex- and APOE-dependent pattern.

## Overall preliminary interpretation

Taken together, the current figures support three restrained conclusions:

1. Mitochondrial-related AD transcriptional responses are prominent in neuronal populations, especially excitatory neurons, while remaining detectable in several glial and other non-neuronal compartments.
2. The distribution and direction of these responses vary by sex and APOE group; many differences appear as threshold-level changes restricted to one stratum, while a smaller subset appears in opposite directions.
3. Genes in the most divergent score tails repeatedly point to oxidative phosphorylation and electron-transport-chain biology, even though the exact gene-level occurrence pattern differs across comparisons.

These results motivate more focused validation of respiratory-chain and oxidative-phosphorylation programs, but they do not yet establish causality, a formal statistical interaction, or replication outside the analyzed cohort.

## Interpretation limits

- Figure 1 cells report DEG counts or occurrences, not effect sizes or independent biological replicates.
- Counts depend on the number of tested assay features and available AD/NCI donors shown in the cells; white and gray cells can reflect zero counts or non-estimable contrasts rather than equivalent evidence.
- Separate panels use different color scales, so color intensity should only be interpreted within its own legend.
- “First group only,” “second group only,” and “opposite” describe thresholded AD-versus-NCI states. They are not substitutes for a direct interaction test.
- Figures 3–6 are relative similarity-rank and score-tail summaries. Low-tail membership prioritizes genes and pathways but does not, by itself, demonstrate significance for every individual gene.
- The figures use a mitochondrial-restricted gene universe, so the pathway results describe structure within mitochondrial biology rather than transcriptome-wide enrichment.

## Figure inventory

| Figure | Displayed analysis |
|---|---|
| [1A](figure01/figure01A_mitochondrial_yu_analogue.svg) | Mitochondrial-related genes upregulated in AD |
| [1B](figure01/figure01B_mitochondrial_yu_analogue.svg) | Mitochondrial-related genes downregulated in AD |
| [1C](figure01/figure01C_mitochondrial_yu_analogue.svg) | APOE comparisons within females |
| [1D](figure01/figure01D_mitochondrial_yu_analogue.svg) | APOE comparisons within males |
| [1E](figure01/figure01E_mitochondrial_yu_analogue.svg) | Sex-based comparisons within APOE groups |
| [3](figures03_to_06/figure03_mitochondrial_yu_analogue.svg) | Sex-shared and sex-divergent mitochondrial responses |
| [4](figures03_to_06/figure04_mitochondrial_yu_analogue.svg) | APOE ε2-shared and ε2-divergent mitochondrial responses |
| [5](figures03_to_06/figure05_mitochondrial_yu_analogue.svg) | APOE ε4-shared and ε4-divergent mitochondrial responses |
| [6](figures03_to_06/figure06_mitochondrial_yu_analogue.svg) | APOE-dependent sex divergence in mitochondrial responses |
