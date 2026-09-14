# ROSMAP Sex/APOE Broad KDA: Findings, Mitochondrial Programs, and Supplemental SEA-AD Support

- **Analysis date:** 2026-09-12
- **Status:** exploratory synthesis for candidate prioritization, not confirmatory inference
- **Discovery cohort:** ROSMAP
- **Supplemental cross-cohort support:** SEA-AD; useful but not required for retaining a ROSMAP finding
- **Interpretive guide:** [AD/APOE/sex key-driver analysis guide](AD_APOE_Sex_Key_Driver_Analysis_Guide.md)

## Start here: how to read this report

### The biological question

Every cell needs mitochondria to help make usable energy. Most mitochondrial proteins are encoded by genes in the **cell nucleus**, but 13 important energy-system proteins are encoded by the mitochondrion’s own small genome, called **mtDNA**. These two genomes must work together.

This study asks:

> In Alzheimer’s disease, do mitochondrial gene changes differ by sex, APOE genotype, and brain-cell type, and which non-mitochondrial network genes are associated with those changes?

The project therefore has two linked goals: identify candidate Alzheimer’s drivers that recur broadly, and identify patterns that may differ by sex, APOE, or cell type. A driver recurring in a different SEA-AD context can support the first goal even though it does not confirm sex/APOE specificity.

ROSMAP is the main discovery dataset. SEA-AD is a much smaller, unevenly sampled dataset used to look for optional cross-cohort support. A ROSMAP finding is **not rejected** merely because SEA-AD cannot evaluate it or does not select the same key driver.

### Group names used throughout

- `F` means female and `M` means male.
- `e2` means an APOE ε2-containing group.
- `e33` means APOE ε3/ε3.
- `e4` means an APOE ε4-containing group.
- Therefore, `F_e33` means female APOE ε3/ε3, and `M_e4` means male APOE ε4.

These labels describe the groups that were analyzed separately. A result seen in one group is **not automatically specific to that group**. Proving specificity requires a direct statistical comparison between groups.

### Key terms in simple language

- **AD and NCI:** AD means Alzheimer’s disease. NCI means no cognitive impairment and is the ROSMAP comparison group.
- **APOE:** a gene with common forms called ε2, ε3, and ε4. These forms are associated with different population-level Alzheimer’s risks, but they do not determine a person’s outcome.
- **ROSMAP and SEA-AD:** two studies of human brain tissue. ROSMAP is the discovery cohort here; SEA-AD provides a smaller and incomplete opportunity for additional support.
- **Donor:** a person who contributed tissue. Thousands of cell nuclei from one donor are not thousands of independent people.
- **Fine and broad cell type:** a fine type is a specific cell subtype. Related fine types are grouped into broad classes such as excitatory neurons, inhibitory neurons, astrocytes, microglia, oligodendrocytes, OPCs, and vascular cells.
- **Gene expression:** how much RNA a cell makes from a gene. It is a measure of gene activity, not a direct measurement of protein amount or cell function.
- **DEG:** a differentially expressed gene. Here it means a gene whose RNA level differs between Alzheimer’s disease and the comparison group.
- **Up or down:** “up” means more RNA in Alzheimer’s disease; “down” means less.
- **log2FC:** log2 fold change, a way to report the size and direction of an expression difference. Positive values mean up and negative values mean down.
- `paper_deg`**:** this report’s stricter ROSMAP DEG label, requiring both an adjusted P value below 0.05 and an expression change larger than the stored effect-size threshold.
- **mtDNA:** mitochondrial DNA, the small genome inside mitochondria.
- **ATP:** a molecule cells use as spendable chemical energy.
- **OXPHOS:** oxidative phosphorylation, the linked protein complexes mitochondria use to make most cellular ATP.
- **mtDNA OXPHOS genes:** the 13 OXPHOS genes encoded inside mitochondrial DNA.
- **Nuclear OXPHOS genes:** OXPHOS genes encoded in the nucleus and imported into mitochondria.
- **Mitochondrial translation:** the machinery that builds proteins inside mitochondria.
- **MitoCarta:** a reference list of genes connected to mitochondria. **Core-MitoCarta** refers to the mitochondrial query definition used in this analysis.
- **Non-MT:** not classified as a core mitochondrial gene in the stored analysis. A non-MT driver can still affect or be associated with mitochondria.
- **KDA:** key-driver analysis. It searches a gene network for genes whose nearby network neighborhoods contain unusually many query DEGs.
- **Candidate driver:** a gene prioritized by KDA. It is a map-based candidate, not proof that the gene causes the DEG changes.
- **Neighborhood overlap:** mitochondrial DEGs found near a candidate driver in the inferred network. They are not experimentally proven targets.
- **Call:** one KDA analysis for one fine cell type and one sex/APOE group.
- **Category:** several related fine-cell calls combined into one sex/APOE × broad-cell group.
- **Enrichment:** more genes from a defined program or pathway appeared than expected under a statistical comparison.
- **ORA:** over-representation analysis, one way to test enrichment in a gene list.
- **P value:** a measure of how surprising a result would be under a specified chance model. It is not the probability that the biological claim is true.
- **FDR or BH-adjusted P value:** a statistical value corrected for testing several hypotheses. Smaller values provide stronger evidence against chance, but they do not prove causation.
- **Pseudobulk:** adding cell-level counts within each donor before testing. This helps keep the person, rather than each nucleus, as the independent unit.
- **Aβ and tau:** amyloid-beta and tau, proteins that can form abnormal accumulations in Alzheimer’s disease.
- **Not evaluable:** SEA-AD lacked a usable comparison. This is neutral and does not count against the ROSMAP finding.
- **Tested but not returned:** the gene was available to SEA-AD KDA, but KDA did not select it. In this small cohort, that means no added driver-level support in that test—not proof that the ROSMAP driver is wrong.
- **Cross-context support:** the same driver, pathway, or mitochondrial program appears in SEA-AD even if sex, APOE group, or cell type differs. This is weaker than an exact match but still informative.



### A useful mental picture

Think of the gene network as a road map:

1. Mitochondrial DEGs are the marked destinations.
2. KDA looks for intersections located near more marked destinations than expected.
3. Those intersections become candidate key drivers.
4. The map suggests where to investigate, but it does not show that changing an intersection will control traffic.



### Recommended reading order

Readers who mainly want the biology can read the quick answer and Findings 1–17. Sections 1–3 explain evidence and methods. Sections 8–11 explain genetics, next analyses, and limitations. Appendix A contains the complete recurrence inventory.

## Quick answer in plain language

The clearest result is that the mitochondrial changes differ across the analyzed sex/APOE and cell-type groups. ROSMAP provides the primary evidence for the candidate drivers. SEA-AD is treated as bonus evidence rather than a pass/fail gate.

1. **The strongest supplemental cross-cohort support is a mitochondrial program, not a driver gene.** Female ε3/ε3 excitatory neurons showed increased mtDNA OXPHOS RNA in both ROSMAP and SEA-AD.
2. **Male ε3/ε3 inhibitory neurons showed an important mismatch.** mtDNA OXPHOS genes increased, while many nuclear-encoded mitochondrial-support genes decreased. This pattern also appeared in both datasets.
3. **Many ROSMAP candidate drivers belong to the ordinary cytosolic ribosome.** `RPL11` and `RPS15` are leading examples. Their network neighborhoods connect cytosolic protein production to mitochondrial OXPHOS changes.
4. **A second candidate system links lysosomes, autophagy, nutrient sensing, and mitochondria.** `LAMTOR5` is the strongest representative.
5. **Several narrower candidates suggest testable mechanisms.** These include `WDR82`, `SELENOM`, `SELENOW`, `PGK1`, and the OPC pair `FTL`/`ANKRD11`.
6. **Exact same-context driver matching is absent, but broader support is present.** Of 72 directly testable ROSMAP driver-category units, zero were selected again in the exact same sex/APOE and broad-cell category. However, `LAGE3`, `MIPOL1`, and `PAPOLA` recur in different contexts, and several mitochondrial programs recur. These relaxed matches count as partial support. The lack of an exact match does not remove a candidate supported by strong ROSMAP recurrence, a coherent network neighborhood, pathway evidence, genetics, or prior experiments.

The data do **not** establish causal regulation, a sex/APOE interaction, improved or impaired ATP production, or donor-independent replication. Each finding below explains separately what was observed, why it is interesting, what supports it, and what still needs to be tested.

## 1. Evidence levels used in this document


| Level                                | Meaning in this analysis                                                                                                                                                                     |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Strong ROSMAP discovery evidence** | A non-MT driver recurs across eligible calls or categories, has a coherent mitochondrial neighborhood, and survives relevant internal checks. This evidence does not require SEA-AD support. |
| **Exact-context SEA-AD support**     | The same driver appears in the same sex/APOE and broad-cell category. This is the strongest cross-cohort driver match, but it is not required.                                               |
| **Context-relaxed SEA-AD support**   | The same driver appears in another sex/APOE or cell context, or a related driver/pathway appears. This is partial cross-cohort support rather than failure.                                  |
| **Cross-cohort program support**     | A mitochondrial DEG program recurs with a compatible direction, even if the selected driver differs.                                                                                         |
| **Orthogonal support**               | Human genetics or experimental literature supports the gene or pathway, but not necessarily the inferred cell context or KDA edge.                                                           |
| **Preliminary hypothesis**           | A narrow or technically sensitive KDA pattern needs stronger internal robustness or mechanistic evidence. Lack of SEA-AD support alone does not place a finding in this level.               |


No current candidate reaches a confirmatory “causal driver” level.

### Novelty labels used below

**Novelty and evidence strength are different.** A highly novel finding may be uncertain, while a less novel finding may have strong evidence.

- **Low novelty:** the main relationship is already well established; this analysis mainly confirms it.
- **Moderate novelty:** the general biology is known, but the exact cell type, sex/APOE context, direction, or network connection adds something new.
- **High novelty:** no direct prior report of the exact relationship was identified in the focused literature reviewed for this report.

These labels are provisional as of September 2026. The literature review was focused rather than systematic, so “high novelty” means “no direct report identified,” not “definitely never reported.”

## 2. Inputs and analysis safeguards



### 2.1 ROSMAP discovery inputs

Primary artifacts:

- [category summary](../../../results/minerva_production/20_sex_apoe_kda_combo/combo_category_summary.tsv)
- [gene-by-category driver table](../../../results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv)
- [run manifest](../../../results/minerva_production/20_sex_apoe_kda_combo/combo_run_manifest.tsv)
- [effective mitochondrial query members](../../../results/minerva_production/20_sex_apoe_kda_combo/combo_query_members.tsv.gz)
- [within-call returned KDA rows and exact overlap genes](../../../results/minerva_production/20_sex_apoe_kda_combo/combo_returned_call_rows.tsv.gz)
- [source MAST DEG results](../../../results/minerva_production/08_mast/)
- [exact KDA background members](../../../results/minerva_production/12_rosmap_sex_apoe_mito_kda_runs/kda_background_members.tsv.gz)

The contrasts are AD versus NCI **within** each fine cell type and one of six groups: `F_e2`, `F_e33`, `F_e4`, `M_e2`, `M_e33`, and `M_e4`.

ROSMAP `paper_deg` is defined in the stored output as within-contrast BH FDR `< 0.05` and `|log2FC| > log2(1.3)`. The KDA query contains effective core-MitoCarta DEGs; consequently, the mere presence of mitochondrial biology is expected. The informative outputs are the program, direction, context, and non-MT network neighborhood.

The `is_core_mito` and non-MT counts below initially preserve the stored Phase 09 labels. A separate HGNC–MitoCarta identity audit is reported in Section 4.1 because synonym-only cross-gene matches affect this field.

### 2.2 Targeted mitochondrial-program analysis

Four frozen gene sets from [phase13_respiratory_modules.tsv](../../../config/phase13_respiratory_modules.tsv) were evaluated in each eligible KDA call:

- 13 mtDNA-encoded OXPHOS genes;
- 86 nuclear-encoded structural OXPHOS genes;
- 155 mitochondrial-translation genes;
- 19 MICOS/inner-membrane genes.

For each call, the effective core-MitoCarta DEG query was compared with that call’s exact background restricted to core-MitoCarta genes using a one-sided hypergeometric test. Benjamini–Hochberg correction was applied across the four programs within that call. This is a targeted exploratory reanalysis of frozen modules, not a preregistered test.

“Occurrences” below are gene-by-call observations. They are not independent donors or unique genes.

### 2.3 Exploratory pathway analysis of non-MT drivers

Unique non-MT drivers were tested against the local [MSigDB C2 canonical pathways v2026.1 collection](../../../data/reference/msigdb/c2.cp.v2026.1.Hs.symbols.gmt):

- hit list: 228 unique ROSMAP non-MT drivers;
- background: 11,478 non-MitoCarta genes in the union of exact eligible KDA backgrounds;
- eligible pathways: 1,953 sets containing 15–500 background genes;
- statistic: one-sided hypergeometric test with BH across eligible pathways.

Cell-network analyses used the corresponding network-specific background. These enrichments are descriptive because KDA selection depends on network degree/topology, and ribosomal, ubiquitin, and heat-shock genes can be highly connected.

### 2.4 SEA-AD supplemental-support definitions

SEA-AD inputs:

- [category summary](../../../results/validation_human/12_sex_apoe_kda_combo/simple_category_summary.tsv)
- [category-gene aggregates](../../../results/validation_human/12_sex_apoe_kda_combo/simple_category_gene_aggregates.tsv)
- [significant within-call returns](../../../results/validation_human/12_sex_apoe_kda_combo/10b_kda/seaad_kda_significant_returns.tsv)
- [run manifest](../../../results/validation_human/12_sex_apoe_kda_combo/10a_inputs/seaad_kda_run_manifest.tsv)
- [query members](../../../results/validation_human/12_sex_apoe_kda_combo/10a_inputs/seaad_kda_signature_members.tsv.gz)
- [background members](../../../results/validation_human/12_sex_apoe_kda_combo/10a_inputs/seaad_kda_background_members.tsv.gz)
- [source DEG results](../../../results/validation_human/08_deg_fine/fine_supertype_phase18_parity/tested/)

SEA-AD was analyzed as a **graded support system**, not a required validation gate:

1. **Exact-context driver support:** the same gene, sex/APOE group, and broad network. This is strongest but most difficult to observe.
2. **Partially matched driver support:** the same gene with either the sex/APOE group or a related cell lineage retained.
3. **Any-context driver support:** the same gene appears elsewhere in SEA-AD.
4. **Pathway or mitochondrial-program support:** related genes or the same biological program recur even when the key-driver ranking changes.
5. **No added SEA-AD support:** the comparison is unavailable or returns a different result. Given SEA-AD’s size and imbalance, this is not by itself a reason to discard a ROSMAP finding.

SEA-AD uses dementia versus no-dementia labels, cohort-specific networks, and an FDR-only sensitivity query rather than the ROSMAP FDR-plus-effect threshold. It has only 22 active KDA calls, with 20 in `M_e33`. These differences greatly limit exact matching across sex, APOE, and cell type.

The practical rule in this report is:

> Retain a biologically coherent ROSMAP candidate on the strength of its ROSMAP KDA recurrence, exact mitochondrial neighborhood, pathway coherence, genetics, literature, and internal robustness. Use SEA-AD to increase confidence when support appears, but do not require it for inclusion.

For the **general Alzheimer’s-driver goal**, same-gene recurrence in a different sex/APOE or cell context is meaningful because it suggests that the candidate is not limited to one subgroup. For the **sex/APOE-specific goal**, that same recurrence cannot confirm specificity. The document keeps these two interpretations separate.

For program support, only effective KDA query members were compared. Within each sex/APOE × broad-network category, a gene was called fixed-up or fixed-down when all contributing fine-type queries agreed and “mixed” otherwise; cohorts were then intersected by current gene symbol. Driver testability required the driver to occur in at least one exact SEA-AD background for the matching category.

That testability rule applies only to the **strict exact-context calculation**. The relaxed recurrence analysis compares driver genes across all available SEA-AD contexts and separately considers pathway/program convergence.

Separately, cross-cohort effective-query overlap was tested by one-sided hypergeometric analysis against the operational-symbol intersection of the two cohorts’ category-specific core-MitoCarta backgrounds, with BH correction across the five jointly active categories. An identity-conflict-exclusion sensitivity was also run. This overlap test is distinct from within-cohort enrichment of a mitochondrial program.

## 3. ROSMAP KDA landscape



### 3.1 Coverage and attrition

- 324 structural fine-cell × sex/APOE contrasts were represented.
- 194 calls passed the stored query/eligibility thresholds.
- 164/194 eligible calls returned at least one significant driver.
- The 1,833 returned rows comprise 1,210 core-MitoCarta and 623 non-MT call returns.
- Category aggregation produced 840 rows: 459 mitochondrial and 381 non-MT.
- The 381 non-MT units represent 228 genes in 29 sex/APOE × broad-network categories.

Effective-query size was highly variable: median 16.5 genes, range 3–258, with 65/194 calls containing fewer than ten genes. It is also a major opportunity confounder. For example, `M_e2` excitatory neurons produced 131 non-MT returns across 14 eligible calls (9.36 per call), but the median effective-query size across `M_e2` calls was 85 genes versus 16, 11.5, 19, 9, and 21 in `F_e2`, `F_e33`, `F_e4`, `M_e33`, and `M_e4`. Raw driver yield must therefore not be interpreted as stronger biology without query-size and topology adjustment.

Among the intended 42 combinations of six strata and seven broad networks:

- 34 returned at least one driver of either class;
- 29 returned a non-MT driver;
- 4 had eligible calls but no returned driver;
- 4 had no eligible call.

The non-MT category units were concentrated in neurons:


| Broad network      | Non-MT category units | Unique non-MT genes | Within-call non-MT returns |
| ------------------ | --------------------- | ------------------- | -------------------------- |
| Excitatory neurons | 153                   | 84                  | 347                        |
| Inhibitory neurons | 146                   | 110                 | 192                        |
| Astrocytes         | 32                    | 21                  | 32                         |
| OPCs               | 21                    | 18                  | 21                         |
| Oligodendrocytes   | 18                    | 18                  | 18                         |
| Vasculature        | 6                     | 5                   | 7                          |
| Microglia          | 5                     | 5                   | 6                          |


Sparse glial/vascular results should not be compared with neuronal recurrence counts without accounting for the very different number of eligible fine-cell calls.

### 3.2 Leading recurrent non-MT drivers


| Driver      | Category units | Supporting calls | Strata | Broad networks | Interpretation                                                      |
| ----------- | -------------- | ---------------- | ------ | -------------- | ------------------------------------------------------------------- |
| `RPS15`     | 11             | 22               | 6      | 4              | Most recurrent representative of a larger ribosomal module          |
| `RPL11`     | 10             | 24               | 6      | 4              | Ribosomal-stress candidate with a broad nuclear-OXPHOS neighborhood |
| `RPLP1`     | 8              | 12               | 5      | 2              | Additional ribosomal-module support                                 |
| `SELENOM`   | 7              | 12               | 6      | 2              | Translation/redox-calcium candidate                                 |
| `RPL15`     | 7              | 9                | 4      | 3              | Additional ribosomal-module support                                 |
| `LAMTOR5`   | 6              | 17               | 4      | 2              | Lysosomal nutrient sensing linked to OXPHOS                         |
| `SELENOW`   | 6              | 16               | 4      | 2              | Redox/proteostasis candidate with direct tau literature             |
| `GABARAPL2` | 5              | 13               | 4      | 2              | Autophagy-related reinforcement of the lysosomal axis               |
| `GAPDH`     | 5              | 12               | 4      | 3              | Glycolytic/stress coupling; high-connectivity caveat                |
| `RPS13`     | 5              | 12               | 5      | 2              | Additional ribosomal-module support                                 |
| `WDR82`     | 4              | 18               | 4      | 1              | Narrow excitatory mtDNA-up neighborhood                             |


Recurrence across fine-cell types does not create independent replication because the same donors can contribute nuclei to multiple calls.

## 4. Mitochondrial programs define the main sex/APOE-stratified result



### 4.1 Overall targeted program results


| Program                   | ROSMAP query occurrences, up/down | ROSMAP significant calls | SEA-AD query occurrences, up/down | SEA-AD significant calls |
| ------------------------- | --------------------------------- | ------------------------ | --------------------------------- | ------------------------ |
| mtDNA OXPHOS              | 732, 540/192                      | 99/194                   | 32, 32/0                          | 4/22                     |
| Nuclear structural OXPHOS | 1,172, 430/742                    | 33/194                   | 35, 2/33                          | 0/22                     |
| Mitochondrial translation | 906, 375/531                      | 0/194                    | 67, 19/48                         | 0/22                     |
| MICOS/inner membrane      | 103, 31/72                        | 0/194                    | 4, 0/4                            | 0/22                     |


The translation and MICOS counts represent a diffuse DEG burden but **not** enrichment relative to the core-MitoCarta background under this test.

**MitoCarta identity sensitivity.** In the stored [Phase 09 annotation](../../../results/minerva_production/09_annotate_genes/gene_annotation_master.tsv.gz), 59 current HGNC symbols are flagged through a `unique_synonym` match to a different MitoCarta canonical symbol. Five occur among returned drivers: `ACP1`, `PSAP`, `RNH1`, `RPL13`, and `RPS12`. In particular, cytosolic `RPL13` and `RPS12` were matched to the distinct mitochondrial genes `MRPL13` and `MRPS12`. The official 228-gene/381-unit non-MT counts above preserve the stored classification.

The same collision family is inherited by the operational SEA-AD mapping; the SEA-AD annotation records explicit HGNC/MitoCarta conflict fields, and 64/919 fine-cell FDR-only mitochondrial-query occurrences have an identity conflict. The identity-resolved cross-cohort sensitivity below excludes these symbols.

As a post hoc program-level sensitivity check, removing all 59 identity-conflict symbols from both the ROSMAP core-MitoCarta queries and backgrounds changed the significant-call counts only from 99 to 98 for mtDNA OXPHOS and left nuclear OXPHOS at 33; translation and MICOS remained zero. This supports the broad program result, but it does **not** repair the KDA rankings because the original network tests used the uncorrected queries. Stable-ID remapping and KDA reruns are required before publication.

### 4.2 ROSMAP direction by stratum


| Stratum | mtDNA OXPHOS occurrences, up/down; significant calls | Nuclear OXPHOS occurrences, up/down; significant calls | Reading                                  |
| ------- | ---------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| `F_e2`  | 128, 127/1; 20                                       | 243, 239/4; 9                                          | Coordinated mtDNA and nuclear OXPHOS up  |
| `F_e33` | 217, 217/0; 29                                       | 89, 76/13; 4                                           | Strong mtDNA-up with mostly nuclear-up   |
| `F_e4`  | 64, 26/38; 10                                        | 216, 10/206; 6                                         | Predominantly nuclear-OXPHOS down        |
| `M_e2`  | 132, 13/119; 13                                      | 467, 63/404; 10                                        | Broad mtDNA and nuclear OXPHOS down      |
| `M_e33` | 81, 70/11; 12                                        | 68, 8/60; 1                                            | mtDNA-up/nuclear-down discordance        |
| `M_e4`  | 110, 87/23; 15                                       | 89, 34/55; 3                                           | Weaker mtDNA-up/nuclear-down discordance |


This is the most important sex/APOE-related pattern, but it remains **stratum-resolved**, not proof that the AD effect differs statistically between strata. A donor-level disease × sex/APOE interaction on frozen program scores is required.

### Finding 1: female APOE ε3/ε3 cells show a strong mtDNA OXPHOS increase

**Provisional novelty: Moderate.** Increased mitochondrial transcription in Alzheimer’s disease is not new, but this female ε3/ε3 excitatory-neuron pattern and its cross-cohort support add a less-established context.

#### Plain-language takeaway

Female APOE ε3/ε3 cells repeatedly had higher RNA from the mitochondrial genome’s energy-making genes in Alzheimer’s disease. The excitatory-neuron part of this pattern was also seen in SEA-AD, making it the clearest cross-cohort result.

#### What ROSMAP showed

Across the eligible `F_e33` fine-cell calls:

- mtDNA OXPHOS genes appeared 217 times as DEGs;
- all 217 occurrences were AD-up and none were AD-down;
- 29 calls had statistically significant enrichment of mtDNA OXPHOS genes; and
- nuclear OXPHOS also leaned up, with 76 up and 13 down occurrences.

The number 217 does **not** mean that there are 217 different mtDNA OXPHOS genes. The human mitochondrial genome has only 13 OXPHOS protein-coding genes. An occurrence is counted again whenever the same gene appears in another eligible fine-cell call. The result therefore means that a small mitochondrial gene set repeatedly appeared across cells.

#### What SEA-AD added

Only one matching female ε3/ε3 excitatory-neuron call was evaluable in SEA-AD, so the added support is strong in direction but narrow in coverage.

Nine mtDNA genes appeared in both the ROSMAP category and the SEA-AD query: `MT-ATP6`, `MT-CO1`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND1`, `MT-ND2`, `MT-ND4`, and `MT-ND5`. All nine were AD-up in both datasets. They made up 9 of the 10 genes in the SEA-AD query.

The cross-dataset overlap remained significant after correcting for multiple tests (`BH = 0.00505`). A sensitivity analysis that removed genes with unresolved mitochondrial name conflicts produced nearly the same result (`BH = 0.00441`). Within the SEA-AD call itself, mtDNA OXPHOS enrichment was extremely strong (`BH = 5.00 × 10^-16`). The first two values test cross-cohort overlap; the last value tests enrichment within SEA-AD, so they should not be treated as the same statistic.

#### Why this may matter

Excitatory neurons use large amounts of energy to send signals. A coordinated increase in mtDNA OXPHOS RNA could mean that diseased neurons are trying to compensate for inefficient mitochondria. It could also be a stress response, a change in mitochondrial RNA processing, or a difference in which nuclei survived and were captured.

More RNA does not automatically mean better mitochondria. A damaged engine may receive more repair instructions without producing more power.

#### Prior research

Single-cell Alzheimer’s studies show that disease responses differ across cell types and sexes ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5); [Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). APOE ε4 astrocyte experiments also connect APOE state to mitochondrial dysfunction ([Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). This prior work makes the result reasonable to investigate, but it does not independently prove this exact female ε3/ε3 pattern.

#### What is not proven

- The result does not identify what caused the mtDNA increase.
- Separate subgroup tests do not prove that the pattern is unique to females or to ε3/ε3.
- One SEA-AD call does not show replication across every excitatory-neuron subtype.
- RNA abundance does not measure respiratory-complex assembly, oxygen use, membrane potential, or ATP production.
- SEA-AD reproduced the mitochondrial program but did not add exact driver-level support for `WDR82` or a ribosomal gene. This does not reject those ROSMAP candidates.



#### Best next evidence

Show each shared gene’s effect for each donor, then fit a model with direct disease × sex × APOE interaction terms. Follow this with OXPHOS protein, respiratory-complex assembly, and oxygen-consumption measurements in female ε3/ε3 neuronal models.

### Finding 2: male APOE ε3/ε3 cells show a mtDNA-up, nuclear-OXPHOS-down mismatch

**Provisional novelty: High.** The concept of mitonuclear imbalance is known, but no prior report of this cross-cohort male ε3/ε3 inhibitory-neuron pattern was identified.

#### Plain-language takeaway

In male APOE ε3/ε3 cells, the mitochondrial genome and the nuclear genome often moved in opposite directions. mtDNA OXPHOS RNA mostly increased, while nuclear OXPHOS RNA mostly decreased. The inhibitory-neuron part of this mismatch also appeared in SEA-AD.

#### What ROSMAP showed

Across the eligible `M_e33` calls:

- mtDNA OXPHOS had 81 DEG occurrences: 70 up and 11 down;
- 12 calls had significant mtDNA OXPHOS enrichment;
- nuclear OXPHOS had 68 occurrences: 8 up and 60 down; and
- one call had significant nuclear OXPHOS enrichment, in the down direction.

The opposite directions are important because OXPHOS complexes contain matching parts made from both genomes. The cell must produce and assemble both sets of parts in the correct amounts.

#### What SEA-AD added

In the matched male ε3/ε3 inhibitory-neuron comparison, ROSMAP and SEA-AD shared 22 mitochondrial query genes. Nineteen had the same fixed AD direction in both datasets; only three had opposite directions.

The concordant genes included nine mtDNA OXPHOS genes that were all up: `MT-ATP6`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND1`, `MT-ND2`, `MT-ND3`, `MT-ND4`, and `MT-ND4L`.

Examples of concordant nuclear or maintenance genes that were down include:

- OXPHOS or energy transport: `UQCRFS1` and `SLC25A5`;
- mitochondrial protein import: `TIMM13` and `TIMM17A`;
- mitochondrial ribosome: `MRPL16` and `MRPS34`; and
- mitochondrial maintenance: `ENDOG` and `MTCH1`.

The cross-cohort overlap was significant after multiple-test correction (`BH = 0.0417`). Removing unresolved mitochondrial identity-conflict genes left 21 shared genes and a similar result (`BH = 0.0486`). The three discordant genes were `HIBCH`, `ISCU`, and `TMEM126B`.

#### Why this may matter

This pattern is called a **mitonuclear mismatch**. Imagine a factory increasing instructions for one group of machine parts while decreasing instructions for matching parts, delivery systems, and assembly tools. That could lead to compensation, unassembled components, or mitochondrial stress.

The mismatch is more informative than an isolated change in one gene because several related nuclear systems point in the same direction.

#### Prior research

Mitonuclear coordination is necessary for respiratory-complex assembly. Cell-resolved Alzheimer’s studies also show that sex and cell class influence disease-associated transcription ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5); [Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). The current result adds a specific subgroup and cell context; the earlier studies do not prove this exact mismatch.

#### What is not proven

- The RNA data do not show that OXPHOS protein complexes are physically unbalanced.
- They do not show lower ATP, altered oxygen consumption, or higher oxidative stress.
- Separate subgroup tests do not prove a male- or ε3/ε3-specific interaction.
- SEA-AD adds support for the DEG program but not for the exact ROSMAP driver genes in this context. Exact driver matching is not required to retain the ROSMAP finding.



#### Best next evidence

Measure mtDNA-encoded and nuclear-encoded OXPHOS proteins in the same samples, test respiratory-complex assembly, and compare oxygen consumption across groups. A donor-aware interaction model is required before calling the mismatch sex- or APOE-specific.

### Finding 3: female APOE ε2 cells show coordinated increases from both genomes

**Provisional novelty: High.** No direct prior report of this coordinated female ε2 mtDNA-and-nuclear OXPHOS increase was identified.

#### Plain-language takeaway

Female APOE ε2 cells showed a different pattern from Finding 2: both mtDNA and nuclear OXPHOS genes were overwhelmingly increased. At the RNA level, the two genomes appeared coordinated rather than opposed.

#### What ROSMAP showed

Across eligible `F_e2` calls:

- mtDNA OXPHOS had 128 occurrences: 127 up and 1 down;
- 20 calls had significant mtDNA OXPHOS enrichment;
- nuclear OXPHOS had 243 occurrences: 239 up and 4 down; and
- 9 calls had significant nuclear OXPHOS enrichment.

This is one of the strongest same-direction patterns in ROSMAP. Both the mitochondrial instructions and the nuclear instructions for energy-making machinery mostly increased.

#### Why this may matter

APOE ε2 is associated with lower Alzheimer’s risk than APOE ε4 at the population level ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075)). A coordinated mitochondrial response could be protective, compensatory, or simply a different disease state. It is therefore an interesting mechanism to test.

However, “coordinated” describes RNA direction only. It does not mean that the matching proteins were made in the right amounts, assembled correctly, or produced more ATP.

#### Supplemental SEA-AD evidence

No matching `F_e2` category was active in the current SEA-AD export. This is **not evaluable** and is neutral: it does not reduce the standing of the ROSMAP result.

#### Prior research

Human genetics strongly supports different Alzheimer’s risks across APOE alleles ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075)). Experimental literature also links APOE state to mitochondrial and metabolic changes ([Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). These sources motivate the hypothesis but do not show that coordinated OXPHOS transcription explains ε2-associated protection.

#### What is not proven

- The result does not prove a protective mechanism.
- It does not prove a female × ε2 interaction.
- Repeated occurrences across related cell calls are not independent biological replications.
- SEA-AD supplies no additional evidence for this group because it lacks the required data; this is not evidence against the finding.



#### Best next evidence

Directly compare female ε2 with female ε3/ε3 and female ε4 using donor-pseudobulk interaction models. Then measure respiratory proteins, ATP production, and stress tolerance in APOE-isogenic female neuronal and glial models.

### Finding 4: female APOE ε4 cells show a strong nuclear-OXPHOS decrease

**Provisional novelty: Moderate.** APOE ε4-related mitochondrial problems are well studied, but the strongly nuclear-sided decrease in this female, cell-resolved ROSMAP context is a more specific extension.

#### Plain-language takeaway

Female APOE ε4 cells showed lower RNA for many nuclear-encoded OXPHOS genes. Unlike Findings 1 and 3, this group did not show a coordinated increase across both genomes.

#### What ROSMAP showed

Across eligible `F_e4` calls:

- mtDNA OXPHOS had 64 occurrences: 26 up and 38 down;
- 10 calls had significant mtDNA OXPHOS enrichment;
- nuclear OXPHOS had 216 occurrences: only 10 up and 206 down; and
- 6 calls had significant nuclear OXPHOS enrichment.

The nuclear side is the clearest part of the result: about 95% of its occurrences were AD-down. The mtDNA side was more mixed, so it should not be described as a uniform decrease of all mitochondrial genes.

#### Why this may matter

The nucleus encodes most OXPHOS proteins. A broad decrease in those instructions could reflect lower respiratory investment, cell stress, altered cell state, or a response to disease. It could also make it harder for cells to match any mtDNA-encoded components that remain stable or increase.

Because APOE ε4 is the strongest common genetic risk factor for late-onset Alzheimer’s disease ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075)), this nuclear-side reduction is a high-priority hypothesis. The risk association alone does not show that this RNA pattern is the reason for that risk.

#### Supplemental SEA-AD evidence

SEA-AD had one active female ε4 astrocyte call, but its query contained only five genes. Only `NDUFS8` and `MRPS6` overlapped the ROSMAP category, and the cross-cohort overlap did not exceed chance after correction (`BH = 0.819`). This supplies little positive support, but the comparison is too small to treat as meaningful contradictory evidence.

#### Prior research

APOE ε4 models show altered mitochondrial and mitophagy-related phenotypes ([Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4); [Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). Single-cell studies also report strong glial disease responses ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5); [Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). This literature supports follow-up but does not independently replicate the observed nuclear-OXPHOS decrease.

#### What is not proven

- The analysis does not show reduced respiration or ATP production.
- It does not prove that the decrease is unique to women or ε4 carriers.
- The mtDNA pattern is mixed.
- The only active SEA-AD comparison was too small to add meaningful support or contradiction.



#### Best next evidence

Show the result separately for each broad and fine cell type, then test disease × sex × ε4 interactions at the donor level. Protein-level respiratory-complex measurements would determine whether the RNA decrease reaches the machinery itself.

### Finding 5: male APOE ε2 cells show broad decreases across both OXPHOS genomes

**Provisional novelty: High.** This broad male ε2 decrease is unexpected relative to the usual protective framing of ε2, and no direct prior report was identified. SEA-AD coverage is absent, but cross-cohort validation is not required for this discovery label.

#### Plain-language takeaway

Male APOE ε2 had the broadest downward OXPHOS pattern in ROSMAP. Both mtDNA-encoded and nuclear-encoded OXPHOS genes were mostly lower in Alzheimer’s disease.

#### What ROSMAP showed

Across eligible `M_e2` calls:

- mtDNA OXPHOS had 132 occurrences: 13 up and 119 down;
- 13 calls had significant mtDNA OXPHOS enrichment;
- nuclear OXPHOS had 467 occurrences: 63 up and 404 down; and
- 10 calls had significant nuclear OXPHOS enrichment.

About 90% of mtDNA OXPHOS occurrences and 87% of nuclear OXPHOS occurrences were down. This differs from the mitonuclear mismatch in Finding 2 because both sides of the system move mainly in the same downward direction.

#### Why this may matter

The result could indicate a broad reduction in mitochondrial gene programs, a shift in cell state, or selective vulnerability. It is especially interesting because APOE ε2 is often described as protective. A population-level protective allele can still be associated with an unfavorable-looking molecular pattern in one subgroup, disease stage, or surviving-cell population.

#### Important query-size warning

The median eligible mitochondrial query in `M_e2` contained 85 genes, while the median across all eligible calls was 16.5. A larger query naturally touches more network neighborhoods and can cause more candidate drivers to be returned.

This issue strongly confounds the very high KDA return count in `M_e2`. It does not automatically erase the DEG direction pattern, but the number of key drivers in this group should not be presented as stronger biological evidence.

#### Supplemental SEA-AD evidence

No matching male ε2 category was active in the current SEA-AD export. SEA-AD therefore adds no evidence in either direction.

#### Prior research

APOE alleles differ strongly in Alzheimer’s risk ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075)), and sex and cell type can shape disease-associated gene expression ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5); [Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). No cited study establishes this exact male ε2 decrease, so it remains a discovery result.

#### What is not proven

- The RNA decrease does not prove loss of mitochondrial function.
- It does not prove that APOE ε2 caused the pattern.
- It does not establish a male × ε2 interaction.
- Large DEG queries may amplify the apparent number of KDA drivers.



#### Best next evidence

Repeat KDA with query sizes matched across groups, and directly model sex/APOE interactions using donor-level summaries. If the decrease persists, test respiratory proteins and function in male ε2 models.

### Finding 6: male APOE ε4 cells show a weaker possible mitonuclear mismatch

**Provisional novelty: Moderate.** APOE ε4 mitochondrial dysfunction is established, while the mtDNA-up/nuclear-down pattern observed in the male ε4 stratum is a less-established subgroup hypothesis.

#### Plain-language takeaway

Male APOE ε4 cells showed mostly increased mtDNA OXPHOS RNA but mostly decreased nuclear OXPHOS RNA. This resembles Finding 2, although the direction split is weaker.

#### What ROSMAP showed

Across eligible `M_e4` calls:

- mtDNA OXPHOS had 110 occurrences: 87 up and 23 down;
- 15 calls had significant mtDNA OXPHOS enrichment;
- nuclear OXPHOS had 89 occurrences: 34 up and 55 down; and
- 3 calls had significant nuclear OXPHOS enrichment.

The mtDNA-up tendency is clear. The nuclear side is less one-sided than in `M_e33`, so this should be called a **possible weaker mismatch**, not a fully established one.

#### Why this may matter

If confirmed, the pattern would suggest that increasing mitochondrial-genome RNA without a matching nuclear response is not limited to male ε3/ε3 cells. Comparing the strength of the pattern between male ε3/ε3 and male ε4 could help separate a general disease response from an APOE-dependent response.

#### Supplemental SEA-AD evidence

No male ε4 category was active in the current SEA-AD export, so SEA-AD adds no evidence in either direction.

#### Prior research

APOE ε4 and altered mitochondrial biology are well-supported parts of Alzheimer’s research ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075); [Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). That general evidence makes the question important but does not validate this subgroup-specific result.

#### What is not proven

- The nuclear decrease is not strong enough to claim a definite mismatch.
- SEA-AD does not cover this group; that missing support is neutral rather than a failed result.
- The analysis does not prove a male × ε4 interaction.
- RNA directions do not demonstrate OXPHOS function.



#### Best next evidence

Define a mitonuclear balance score before analysis, compare male ε4 directly with male ε3/ε3 and female ε4, and validate the score at protein and respiratory-function levels.

## 5. Main ROSMAP driver findings



### Finding 7: a cytosolic-ribosome module repeatedly connects to mitochondrial OXPHOS

**Provisional novelty: Moderate.** Ribosome dysfunction in Alzheimer’s disease is established, but the recurrent KDA connection between cytosolic ribosomal genes and nuclear OXPHOS neighborhoods is a newer network-level extension.

#### Plain-language takeaway

Many of the most recurrent non-mitochondrial candidate drivers are parts of the **cytosolic ribosome**, the molecular machine that builds most proteins in the cell. `RPS15` and `RPL11` are the leading examples. Their network neighborhoods repeatedly contain nuclear OXPHOS genes, suggesting a connection between general protein production and mitochondrial energy machinery.

This is a **module-level** finding. It is more reasonable to say that the ribosome system is prioritized than to claim that 20 ribosomal proteins are 20 independent mitochondrial controllers.

#### What ROSMAP showed

- Twenty KEGG ribosome genes comprise 70/381 non-MT category units (`18.4%`) and 133/623 non-MT within-call returns (`21.3%`).
- They occur in 19/29 categories containing non-MT drivers.
- Against the non-MT KDA background, KEGG ribosome enrichment was 20/228 drivers versus 71/11,478 background genes: raw `P = 3.65 × 10^-18`, BH `= 3.56 × 10^-15`.
- `RPS15` and `RPL11` lead the recurrence landscape, followed by `RPLP1`, `RPL15`, `RPS13`, and other large/small subunit genes.

The enrichment comparison is useful because it asks whether ribosome genes are more common in the 228-driver list than in the available network background. They are: 20/228 driver genes (`8.8%`) versus 71/11,478 background genes (`0.62%`). The very small BH-adjusted P value means that this over-representation is difficult to explain by random selection alone under the test.

#### A closer look at `RPL11`

- `RPL11` was returned in 24 calls across 10 categories, all six strata, and four broad networks.
- Its exact KDA neighborhoods contain 253 overlap occurrences representing 37 mitochondrial query genes.
- Nuclear structural OXPHOS contributes 151/253 occurrences, with 100 AD-down and 51 AD-up.
- Recurrent overlaps include `COX7C` (20 occurrences), `UQCRQ` (15), `NDUFS5` (15), `NDUFA1` (15), `ATP5PF` (14), `NDUFB9` (13), and `NDUFB3` (13).
- Nuclear-OXPHOS enrichment was significant in 16/24 supporting queries.
- `RPL11` itself met the ROSMAP `paper_deg` definition in 12/24 supporting calls. Thus, its network nomination is not simply a restatement of driver differential expression.

`RPL11` is a component of the large ribosomal subunit. It was prioritized across many sex/APOE groups and cell classes, so it is not a subgroup-specific result. Its neighborhood is dominated by nuclear genes that encode OXPHOS parts, including repeated links to `COX7C`, `UQCRQ`, `NDUFS5`, `NDUFA1`, `ATP5PF`, `NDUFB9`, and `NDUFB3`.

`RPS15`, a small-subunit protein, was returned in 22 calls across 11 categories and was the most broadly recurrent representative. Together, `RPL11`, `RPS15`, and related genes make the repeated module more convincing than any one ribosomal candidate alone.

#### Why this may matter

Human AD tissue has shown early impairment of ribosome function, lower protein-synthesis capacity, and RNA oxidation ([Ding et al., 2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005)). `RPL11` can also signal ribosomal stress through MDM2–p53 in experimental systems ([Zhang et al., 2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003)). These studies support a translation/proteostasis mechanism, but do not establish the ROSMAP `RPL11`–OXPHOS network relationship.

One interpretation is that stress in ordinary cellular protein production is coupled to reduced production or maintenance of mitochondrial energy proteins. Another possibility is technical: ribosomal genes are abundant, highly connected, and easy for network methods to prioritize.

#### Supplemental SEA-AD evidence

No cytosolic ribosomal driver was returned in SEA-AD. `RPL11` was present in the matching background for the sole `F_e33` excitatory call and all 10 `M_e33` excitatory calls but was not returned. SEA-AD therefore adds no driver-level support in those contexts. Because SEA-AD is small and uses different networks and thresholds, this does not remove the strongly recurrent ROSMAP ribosomal module.

#### What is not proven

- KDA does not prove that a ribosomal protein regulates the neighboring OXPHOS genes.
- Recurrence across fine-cell calls is not independent replication because the calls can contain nuclei from the same donors.
- High network connectivity may help ribosomal genes appear as drivers.
- SEA-AD did not add cross-cohort driver support for the module, but such support is optional in this discovery analysis.



#### Best next evidence

Repeat KDA with degree-matched random networks and after excluding cytosolic-ribosome nodes. Then perturb `RPL11` or `RPS15` in relevant cell models and measure protein synthesis, OXPHOS proteins, cellular stress, and respiration.

### Finding 8: `LAMTOR5` links lysosomal nutrient sensing to OXPHOS

**Provisional novelty: High.** Lysosome–mTOR–mitochondria communication is known, but no direct human Alzheimer’s report of the specific neuronal `LAMTOR5`–OXPHOS network relationship was identified.

#### Plain-language takeaway

`LAMTOR5` is part of a nutrient-sensing system on lysosomes, the cell’s recycling compartments. Its ROSMAP network neighborhoods repeatedly contained decreased nuclear OXPHOS genes. This suggests a possible bridge between nutrient sensing, cellular cleanup, and mitochondrial energy production.

#### What ROSMAP showed

- `LAMTOR5` was returned in 17 neuronal calls across six categories and four strata.
- The strongest category scores were `M_e2` inhibitory (`7.11 × 10^-5`, three calls) and `M_e2` excitatory (`1.35 × 10^-4`, five calls). These are exploratory aggregation scores, not final q-values.
- Its KDA neighborhoods contain 87 mitochondrial overlap occurrences; 39 are nuclear structural OXPHOS and 30/39 are AD-down.
- Frequent overlaps include `ATP5IF1` (13), `CHCHD10` (12), `ATP5MC2` (11), `NDUFA6` (7), `NDUFB6` (5), `TMEM11` (5), and `MRPL4` (5).
- Nuclear-OXPHOS enrichment was significant in 14/17 supporting queries.
- `LAMTOR5` itself was a `paper_deg` in 11/17 calls: consistently up in the five `F_e2` excitatory calls and down in the strongest `M_e2` excitatory/inhibitory calls. This direction contrast is hypothesis-generating until directly tested.

The axis is reinforced by other ROSMAP non-MT drivers:

- `GABARAPL2`: 13 calls and five categories, with recurrent `CHCHD2`, `ATP5MC3`, `PARK7`, and mitochondrial-ribosome overlaps;
- `ATG101`: six calls and three categories, with `MRPS34`, `UQCRFS1`, `CLPP`, and `PINK1`;
- `ATP6AP2`: six calls and three categories, linking V-ATPase biology to OXPHOS/import genes.

The changing direction of `LAMTOR5` itself is important. It was up in female ε2 excitatory calls but down in the strongest male ε2 calls. That pattern may reflect real sex/APOE biology, but it may also arise because the groups were tested separately. A direct interaction test is needed.

#### Why this may matter and what prior research says

LAMTOR5 is a Ragulator component linking amino-acid sensing to lysosomal mTORC1 ([Bar-Peled et al., 2012](https://doi.org/10.1016/j.cell.2012.07.032)). mTORC1 can coordinate translation with nuclear-encoded mitochondrial proteins and oxidative capacity ([Morita et al., 2013](https://doi.org/10.1016/j.cmet.2013.10.001)). Aβ oligomers disrupt a neuronal lysosome-to-mitochondria nutrient-signaling pathway in a tau-dependent manner, although LAMTOR5 was not manipulated in that study ([Norambuena et al., 2018](https://doi.org/10.15252/embj.2018100241)). Experimental LAMTOR5 loss can impair V-ATPase assembly and lysosomal acidification, but that evidence comes from myeloid/SLE models rather than AD neurons ([Zhang et al., 2024](https://doi.org/10.1002/advs.202400446)).

In simple terms, these studies show that LAMTOR5 sits in the right biological place to connect food sensing, lysosome function, protein production, and mitochondria. They do **not** show that LAMTOR5 causes the ROSMAP OXPHOS pattern.

#### Supplemental SEA-AD evidence

SEA-AD had no active call in a matching `LAMTOR5` discovery category. Exact-context support is therefore **not evaluable** and does not count against the candidate. The ROSMAP recurrence, neighborhood coherence, and mechanistic literature remain the basis for retaining `LAMTOR5`.

#### What is not proven

- `LAMTOR5` has not been shown to control these OXPHOS genes in Alzheimer’s neurons.
- The male ε2 calls had unusually large queries, which can increase KDA returns.
- The reported aggregate scores rank candidates but are not final multiple-testing-corrected q-values.
- The supporting literature spans other systems and does not replicate the human cell context.



#### Best next evidence

Perturb `LAMTOR5` in APOE-isogenic neurons, especially female and male ε2 models. Measure lysosomal acidity, mTORC1 activity, autophagic flow, nuclear OXPHOS proteins, and respiration in the same experiment.

### Finding 9: `WDR82` is linked to a narrow excitatory-neuron mtDNA-up module

**Provisional novelty: High.** WDR82 has appeared in Alzheimer’s expression studies, but no direct prior mechanism connecting it to this four-gene neuronal mtDNA module was identified.

#### Plain-language takeaway

`WDR82` was prioritized only in excitatory neurons. Almost every mitochondrial gene in its exact KDA neighborhood came from a four-gene mtDNA group that was increased in Alzheimer’s disease. This is a focused and interesting signal, but the four genes are produced from the same long mitochondrial RNA, so they are not four independent pieces of evidence.

#### What ROSMAP showed

- `WDR82` was returned only in excitatory neurons, in 18 calls across `F_e2` (2), `F_e33` (11), `M_e33` (2), and `M_e4` (3).
- Every supporting query had significant mtDNA-OXPHOS enrichment (`18/18`).
- These queries contained 172 mtDNA-OXPHOS occurrences, all AD-up.
- The exact `WDR82` KDA overlap is much narrower: 68/70 occurrences are `MT-ND1`, `MT-ND3`, `MT-ND4L`, or `MT-ND5`; the other two are `PIM1`.
- `WDR82` itself was not a ROSMAP `paper_deg` in any supporting call. It had within-contrast FDR `< 0.05` in 13/18 calls, but its effect remained below the stored effect-size threshold; 17/18 logFC values were small and positive.

The final point prevents a common misunderstanding: a gene can be nominated by KDA even when it is not a strong DEG. KDA uses network location. In this case, `WDR82` sits near a repeated mtDNA-up query pattern.

#### Why this may matter and what prior research says

Bulk hippocampal reanalysis has reported increased WDR82 and hub status in AD ([Zhu et al., 2015](https://doi.org/10.3892/mmr.2015.4271)), and a later internally split classifier also included WDR82 ([Xu et al., 2024](https://doi.org/10.1038/s41598-024-61363-1)). Neither result provides cell-resolved external validation or a mechanism. Established WDR82 biology instead centers on SETD1A/B–COMPASS recruitment and RNA polymerase II-linked H3K4 trimethylation ([Lee and Skalnik, 2008](https://doi.org/10.1128/MCB.01356-07)). No direct evidence was found that WDR82 binds mtDNA or selectively regulates neuronal mtDNA transcription.

The four mtDNA genes arise from the same mitochondrial heavy-strand polycistronic transcript and are therefore not four independent regulatory observations ([Mercer et al., 2011](https://doi.org/10.1016/j.cell.2011.06.051)). A polycistronic transcript is one long RNA that is later cut into several separate gene products. The neighborhood could therefore reflect total mitochondrial RNA abundance, network wiring, or a real transcriptional coupling mechanism.

#### Supplemental SEA-AD evidence

WDR82 was present in the corresponding SEA background for `1/1 F_e33` and `10/10 M_e33` excitatory calls but was not returned. SEA-AD strongly supports the `F_e33` mtDNA-up program but adds no driver-level support for WDR82 in those calls. This is a caution about transferability, not a reason to discard the ROSMAP candidate.

#### What is not proven

- There is no direct evidence that WDR82 binds mtDNA or controls mitochondrial transcription.
- The four neighboring mtDNA genes are biologically linked through one long starting transcript.
- Small changes in WDR82 itself did not pass the stored effect-size threshold.
- SEA-AD had an opportunity to return WDR82 in matching networks but did not; this limits added cross-cohort confidence without invalidating the ROSMAP result.



#### Best next evidence

Repeat KDA without mtDNA-encoded query genes, control for mitochondrial read fraction and RNA-quality variables, and use degree-matched network controls. Then perturb WDR82 in excitatory neurons and measure mtRNA, mtDNA copy number, H3K4me3, and respiration.

### Finding 10: `SELENOM` links ER redox biology to mitochondrial protein production

**Provisional novelty: High.** SELENOM has prior redox and experimental Alzheimer’s biology, but its specific connection to a decreased mitochondrial-translation neighborhood appears to be a new hypothesis.

#### Plain-language takeaway

`SELENOM` is a selenium-containing protein that helps control oxidation and calcium inside the endoplasmic reticulum, or ER. The ER is a cellular compartment that folds and processes many proteins. In ROSMAP, `SELENOM` repeatedly sat near decreased genes used to build proteins inside mitochondria.

#### What ROSMAP showed

- `SELENOM` was returned in 12 calls across seven categories and all six sex/APOE strata.
- Ten of the 12 calls were excitatory-neuron calls and two were inhibitory-neuron calls.
- `SELENOM` itself met the report’s DEG threshold in 10/12 calls.
- Its exact KDA neighborhoods contained 51 mitochondrial overlap occurrences.
- Mitochondrial-translation genes contributed 27/51 occurrences, including `MRPS34`, `TUFM`, `MRPS7`, `CLPP`, and `MRPS26`.
- Twenty-two of those 27 translation occurrences were AD-down.
- Nuclear-OXPHOS enrichment was significant in 11/12 supporting queries.

This is not evidence that `SELENOM` is part of the mitochondrial ribosome. Instead, the network connects an ER redox/calcium protein to a mitochondrial protein-production pattern.

#### Why this may matter and what prior research says

Cells must coordinate calcium and oxidation across the ER and mitochondria. Disturbing that coordination can affect energy production and stress responses. SELENOM is an ER-lumen thioredoxin-like oxidoreductase, meaning that it helps control reversible oxidation reactions inside the ER ([Ferguson et al., 2006](https://doi.org/10.1074/jbc.M511386200)).

Experimental studies connect SELENOM to neuronal redox/calcium regulation and report effects on Aβ aggregation, mitochondrial swelling, secretase activity, and tau phosphorylation in cells or transgenic animals ([Yim et al., 2009](https://doi.org/10.3892/ijmm_00000211); [experimental Aβ/ROS study](https://doi.org/10.3390/ijms14034385)). These experiments make the candidate plausible, but they are not validation in human Alzheimer’s neurons.

#### Supplemental SEA-AD evidence

`SELENOM` was present in the network background for all 10 matching male ε3/ε3 excitatory SEA-AD calls but was not returned as a key driver. SEA-AD therefore adds no exact driver-level support in that context, but the recurrent ROSMAP result remains eligible for follow-up.

#### What is not proven

- No direct `SELENOM` interaction with `TUFM` or the `MRPS` proteins was identified.
- KDA does not show that SELENOM controls mitochondrial translation.
- The result recurs across groups and should not be called sex- or APOE-specific.
- SEA-AD did not add driver-level support; this is a limitation of external support, not a rejection criterion.
- The local genetic screen found no direct human-genetic support for `SELENOM`.



#### Best next evidence

Perturb `SELENOM` in excitatory neurons and jointly measure ER calcium, redox state, mitochondrial translation, OXPHOS proteins, and respiration. Rescue with normal SELENOM would help distinguish a specific mechanism from general cell stress.

### Finding 11: `SELENOW` connects redox and protein-quality control to respiration

**Provisional novelty: Moderate.** SELENOW already has experimental links to respiration and tau clearance; the human neuronal KDA neighborhood and its cell contexts are the newer parts.

#### Plain-language takeaway

`SELENOW` is another selenium-containing protein, but it should not be treated as the same mechanism as `SELENOM`. Its ROSMAP neighborhood was broader and included respiratory, mitochondrial-ribosome, protein-quality-control, and membrane-related genes.

#### What ROSMAP showed

- `SELENOW` was returned in 16 excitatory- or inhibitory-neuron calls.
- Those calls covered six categories and four sex/APOE strata.
- `SELENOW` itself met the report’s DEG threshold in 10/16 calls.
- Its exact neighborhood contained 123 mitochondrial overlap occurrences.
- Recurrent genes included `PRELID1`, `CHCHD10`, `NDUFB11`, `COA3`, `SLC25A4`, `CYC1`, `MRPS34`, `MRPL34`, and `CLPP`.
- Nuclear-OXPHOS enrichment was significant in 13/16 supporting queries.

The gene list spans several jobs. `NDUFB11`, `COA3`, and `CYC1` support respiration; `MRPS34` and `MRPL34` help mitochondrial protein production; `CLPP` helps remove damaged mitochondrial proteins; and `SLC25A4` transports energy-related molecules across the mitochondrial inner membrane.

#### Why this may matter and what prior research says

Redox balance means keeping oxidizing and reducing chemistry within a range the cell can tolerate. Mitochondria both depend on and influence that balance. Loss of SELENOW altered redox state and mitochondrial respiration in macrophages ([Misra et al., 2023](https://doi.org/10.1016/j.redox.2022.102571)). In a 3×Tg-AD mouse model, SELENOW overexpression promoted tau clearance and improved tau-related phenotypes ([Ren et al., 2024](https://doi.org/10.1038/s42003-024-06572-0)).

These experiments are unusually relevant to mitochondrial and Alzheimer’s biology, but one was performed in immune cells and the other in mice. Neither proves the human neuronal network relationship.

#### SEA-AD and genetic support

`SELENOW` was present but not returned in all 10 matching male ε3/ε3 excitatory calls and all 8 matching inhibitory calls. SEA-AD therefore provides no exact driver-level support for `SELENOW`. However, it returned a different selenium-related gene, `SECISBP2`, once in male ε3/ε3 inhibitory neurons. Under the relaxed framework, this is weak pathway-theme support rather than exact gene support.

The local genetic screen gives `SELENOW` weak support through membership in a public transcriptome-wide association study list. It does not establish causality.

#### What is not proven

- `SELENOW` has not been shown to control the listed mitochondrial neighbors in human neurons.
- The prior studies do not reproduce the exact cell, sex, or APOE contexts.
- SEA-AD adds only weak selenium-theme support, not same-gene support; this does not remove `SELENOW` from the ROSMAP candidate list.
- `SELENOW` and `SELENOM` should not be combined into one mechanism merely because both use selenium.



#### Best next evidence

Perturb `SELENOW` in excitatory and inhibitory neurons, then measure tau clearance, redox state, mitochondrial protein quality, and respiration together. Compare normal SELENOW with a redox-inactive version to test whether its redox function is required.

### Finding 12: `PGK1` links astrocyte glycolysis and hypoxia signaling to mitochondrial quality control

**Provisional novelty: Moderate.** Astrocyte glycolysis and BNIP3/BNIP3L-related mitophagy already have supporting literature, including ROSMAP-related work; the focused KDA neighborhood is an extension rather than a wholly new pathway.

#### Plain-language takeaway

Astrocytes are support cells that help supply and regulate energy for neurons. `PGK1`, a gene used in glycolysis, was linked to three genes involved in low-oxygen stress and removal of damaged mitochondria. Glycolysis makes some energy from sugar outside mitochondria; **mitophagy** is the cell’s process for recycling damaged mitochondria.

#### What ROSMAP showed

- `PGK1` was returned in one astrocyte call each in `F_e33`, `F_e4`, and `M_e4`.
- The exploratory category scores were `0.0472`, `0.00927`, and `0.0164`, respectively.
- Its exact mitochondrial overlaps were only `FAM162A` (3), `BNIP3` (3), and `BNIP3L` (2)—a focused hypoxia/mitophagy neighborhood rather than an OXPHOS module.
- PGK1 was AD-up and met `paper_deg` in the `F_e33` (`logFC = 1.06`) and `M_e4` (`0.95`) calls, but not `F_e4` (`0.03`).

The narrow neighborhood helps define a specific hypothesis. `FAM162A`, `BNIP3`, and `BNIP3L` respond to low-oxygen stress and can participate in mitochondrial quality control. The result suggests a shift between sugar breakdown and mitochondrial cleanup, not broad regulation of every OXPHOS gene.

The `PGK1` direction was not consistent across all three categories: it was clearly up in two but barely changed in female ε4. The category scores are useful for ranking candidates, but they are exploratory scores rather than final q-values.

#### Why this may matter and what prior research says

A multiregion human AD study reported correlated glial glycolysis modules containing `PGK1` and the mitophagy regulator `BNIP3L`, with astrocyte glycolytic remodeling related to pathology ([Mathys et al., 2024](https://doi.org/10.1038/s41586-024-07606-7)). That study uses ROSMAP samples, not SEA-AD, so it is supporting discovery-cohort context rather than fully independent validation; donor overlap with the present ROSMAP analysis should be checked.

APOE4 astrocyte models show altered mitochondrial dynamics/mitophagy ([Schmukler et al., 2020](https://doi.org/10.1038/s41419-020-02776-4)) and lysosomal cholesterol-dependent impairment of mitochondrial clearance and respiration ([Lee et al., 2023](https://doi.org/10.1016/j.celrep.2023.113183)). These studies make the PGK1–BNIP3/BNIP3L hypothesis plausible, but they do not demonstrate that PGK1 controls this pathway in the ROSMAP categories.

#### Supplemental SEA-AD evidence

PGK1 was present but not returned in the sole active `F_e4` astrocyte network. That query had only five genes; only `NDUFS8` (up/up) and `MRPS6` (ROSMAP mixed, SEA up) overlapped the ROSMAP category. SEA-AD adds little support for PGK1, but this single small query is not treated as contradictory evidence.

#### What is not proven

- The network does not prove that PGK1 activates `BNIP3` or `BNIP3L`.
- Increased glycolysis can be adaptive or harmful; its direction alone does not reveal the consequence.
- Mathys et al. 2024 uses ROSMAP, so it is not an independent SEA-AD validation.
- The same candidate appeared in several groups and should not be labeled sex- or APOE-specific.



#### Best next evidence

Perturb PGK1 in astrocytes and measure glycolytic rate, mitochondrial damage, mitophagic flow, and respiration. Test whether blocking or rescuing `BNIP3`/`BNIP3L` changes the PGK1 effect.

### Finding 13: an OPC `FTL`/`ANKRD11` module links iron handling, GPX4, and autophagy

**Provisional novelty: High.** OPC vulnerability to iron-dependent damage is known, but no direct prior report of this `FTL`/`ANKRD11`–GPX4–OXPHOS network module in human Alzheimer’s OPCs was identified.

#### Plain-language takeaway

Oligodendrocyte precursor cells, or **OPCs**, can mature into cells that make the insulating myelin around nerve fibers. In two ROSMAP groups, the candidates `FTL` and `ANKRD11` shared a network neighborhood containing iron-storage genes, the protective enzyme `GPX4`, OXPHOS genes, and mitochondrial-cleanup genes.

This suggests an iron/autophagy hypothesis. It does **not** prove ferroptosis, a form of cell death caused by iron-dependent damage to membrane fats.

#### What ROSMAP showed

- `FTL` and `ANKRD11` both recur in the single ROSMAP OPC fine type in `F_e33` and `M_e2`, alongside `RPS15`.
- Their neighborhoods are nearly identical: `FTH1`, `GPX4`, `COX5B`, and `UQCR10` occur in both strata; `FIS1`, `PARK7`, `ATP5IF1`, `PHB2`, and additional OXPHOS genes occur in `M_e2`.
- Both mtDNA and nuclear OXPHOS programs were significantly enriched in both supporting queries.
- `FTL` was a `paper_deg` in both calls but changed in opposite directions (`F_e33` up, `M_e2` down). `ANKRD11` met the effect threshold only in `M_e2`.

`FTL` and `FTH1` form ferritin, a protein complex that safely stores iron. `GPX4` helps prevent damaging oxidation of membrane fats. `FIS1`, `PARK7`, and `PHB2` are connected to mitochondrial stress or quality control. Their co-occurrence gives the module a biological theme, although the opposite `FTL` directions warn against a single simple interpretation.

#### What pathway analysis added

Over-representation analysis, or ORA, asks whether genes from a known pathway appear more often in the driver list than expected. Exploratory OPC-driver ORA found:

- selective autophagy BH `= 9.00 × 10^-5`;
- autophagy BH `= 6.76 × 10^-4`;
- mitophagy BH `= 0.00233`;
- iron uptake/transport BH `= 0.00968`.

These terms are not independent and are driven partly by generic ubiquitin/tubulin genes: selective autophagy contains `MAP1LC3B`, `TUBA1A`, `TUBB2B`, `UBB`, and `UBC`, while the iron term contains `FTL`, `UBB`, and `UBC`. Therefore, the data support an **iron/autophagy hypothesis**, not a ferroptosis conclusion.

#### Why this may matter and what prior research says

OPCs are experimentally vulnerable to iron-dependent lipid peroxidation when GPX4 protection is impaired ([OPC ferroptosis study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8941078/)), and oxytosis/ferroptosis transcriptomic signatures have been reported in AD datasets ([2025 BMC Biology study](https://doi.org/10.1186/s12915-025-02235-6)). Direct evidence for ferroptosis in human AD OPCs remains lacking.

#### Supplemental SEA-AD evidence

SEA-AD had no active OPC category, so this finding is not evaluable there and receives no SEA-AD penalty. Because ROSMAP contains only one OPC fine type and the two driver neighborhoods are nearly identical, `FTL` and `ANKRD11` should be treated as representatives of one module rather than independent ROSMAP recurrences.

#### What is not proven

No direct `ANKRD11`–ferritin/GPX4 mechanism was identified in prior work. Increased ferritin or GPX4 can also be compensatory and anti-ferroptotic; a ferroptosis claim requires labile iron, oxidized-lipid or lipid-ROS measurements, GPX4 activity loss, and pharmacological rescue.

#### Best next evidence

Measure free iron, oxidized lipids, lipid reactive oxygen species, GPX4 activity, and OPC survival in the same experiment. A ferroptosis inhibitor should rescue the phenotype before the mechanism is called ferroptosis. `ANKRD11` and `FTL` perturbations should be tested separately because the current network cannot show which one is functionally upstream.

## 6. Secondary but potentially useful findings



### Finding 14: `PLCG2` is genetically important but its KDA neighborhood is fragile

**Provisional novelty: High, but with low network confidence.** PLCG2’s Alzheimer’s genetics are established, whereas the female inhibitory-neuron `PLCG2`–`MT-CO1` connection appears new and is supported by only one repeated overlap gene.

#### Plain-language takeaway

`PLCG2` encodes a signaling enzyme and has strong human-genetic connections to Alzheimer’s disease. KDA selected it in six female inhibitory-neuron calls, but every exact mitochondrial overlap was the same single gene, `MT-CO1`. This makes `PLCG2` interesting for follow-up but weak as a network mechanism.

#### What ROSMAP showed

- `PLCG2` was detected only under current thresholds in female inhibitory categories: `F_e2` (one call), `F_e33` (four), and `F_e4` (one).
- Every KDA overlap is the single gene `MT-CO1`; five were AD-up and one AD-down.
- The full supporting queries contain 41 mtDNA-OXPHOS occurrences (36 up, 5 down), and mtDNA-OXPHOS enrichment was significant in all six calls.
- PLCG2 itself was not a DEG in any supporting call.

KDA can select a driver that is not itself a DEG because it asks about network position. Here, however, the position is supported by only one exact mitochondrial neighbor. Repeating `MT-CO1` across calls is not equivalent to seeing a broad and varied mitochondrial neighborhood.

#### Why this may matter and what prior research says

The local [phase19b genetic screen](../../../results/minerva_production/19b_genetic_support_tier1/fungen_gene_evidence.tsv) gives `PLCG2` strong gene-level Alzheimer’s support. The AD-protective P522R variant has weak hypermorphic activity, meaning that it slightly increases a PLCG2 function rather than eliminating it ([2019 primary study](https://doi.org/10.1186/s13195-019-0469-0)).

PLCG2 has historically been studied mainly in microglia and dentate granule cells. A [2026 Nature Genetics study](https://doi.org/10.1038/s41588-026-02709-5) reports neuron-intrinsic PLCG2 effects on synapses, Aβ, and tau. This strengthens the reason to examine neurons, but it does not validate a `PLCG2`–`MT-CO1` regulatory edge.

#### Supplemental SEA-AD evidence

No female inhibitory-neuron category was active in SEA-AD, so exact-context support is not evaluable. This is neutral; `PLCG2` is retained because of its ROSMAP signal and strong independent genetics, while its narrow `MT-CO1` neighborhood remains the main concern.

#### What is not proven

- Strong genetics for the gene does not validate this cell context or network edge.
- One repeated overlap gene is technically fragile.
- The unexpected inhibitory-neuron signal could be affected by ambient RNA, mixed-cell droplets, cell labels, or network connectivity.
- Detection only in the analyzed female groups does not prove a female interaction.



#### Best next evidence

First confirm that `PLCG2` RNA and protein truly occur in the inhibitory-neuron subtypes using spatial or in situ methods. Then perturb PLCG2 in validated neuronal models and measure `MT-CO1`, the other mtDNA transcripts, synaptic phenotypes, and respiration.

### Finding 15: astrocyte `APOE` is context-dependent, not an ε4-only driver

**Provisional novelty: Moderate.** Astrocyte APOE biology is well established; the different KDA neighborhoods and opposite disease directions across the three sex/genotype contexts are the newer observations.

#### Plain-language takeaway

The `APOE` gene itself was selected as an astrocyte candidate in three different genotype groups. It increased in one group and decreased in two. This shows why an APOE-labeled analysis should not automatically be described as an APOE ε4 mechanism.

#### What ROSMAP showed

APOE was returned in one astrocyte call in each of `F_e2`, `M_e2`, and `M_e4`, with exact overlaps including `TUFM`, `LDHB`, `CHCHD10`, `ATP5PB`, and `ATP5F1A`. APOE itself was a `paper_deg` in all three calls but was AD-up in `F_e2` (`logFC = 0.79`) and AD-down in `M_e2` (`-0.51`) and `M_e4` (`-1.25`).

The neighboring genes span mitochondrial protein production (`TUFM`), energy metabolism (`LDHB`), mitochondrial structure or stress (`CHCHD10`), and ATP synthase (`ATP5PB`, `ATP5F1A`). This is a varied mitochondrial neighborhood rather than one single pathway.

#### Why this may matter

Astrocytes are a major source of APOE in the brain. The opposite disease directions could indicate that APOE expression responds differently by sex/genotype context. They could also reflect cell-state or sampling differences. A direct interaction test is required to separate those explanations.

Human genetics strongly establishes `APOE` as an Alzheimer’s risk gene ([Belloy et al., 2019](https://doi.org/10.1016/j.neuron.2019.03.075)). That evidence validates the importance of the gene but does not validate these exact astrocyte network relationships or direction differences.

#### Supplemental SEA-AD evidence

None of the three matching categories was active in SEA-AD, so exact-context support is not evaluable there. This does not count against the ROSMAP result.

#### What is not proven

- KDA does not show that APOE regulates the neighboring mitochondrial genes.
- The three calls are too few to define a shared module.
- Opposite within-group directions do not by themselves establish a sex or genotype interaction.
- Finding APOE in ε2 and ε4 groups means this cannot be called an ε4-only result.



#### Best next evidence

Fit a direct disease × sex × APOE model for astrocyte APOE and its mitochondrial neighbors. In APOE-isogenic astrocytes, change APOE expression or allele state and measure the neighboring proteins, lipid handling, and mitochondrial function.

### Finding 16: female APOE ε4 vascular cells show a small heat-shock module

**Provisional novelty: Moderate.** Heat-shock responses and vascular stress in Alzheimer’s disease are not new, but their concentration in the small female ε4 vascular result is a context-specific observation.

#### Plain-language takeaway

Three of the five non-mitochondrial candidates found in female APOE ε4 vascular calls were stress-response genes. This suggests a heat-shock or protein-protection response in cells associated with blood vessels, but the evidence comes from only two eligible calls.

#### What ROSMAP and pathway analysis showed

The five unique non-MT vascular drivers include `HSPH1`, `HSPA1A`, and `PTGES3` in `F_e4`. Network-specific ORA supports HSF1 activation (BH `= 4.07 × 10^-4`) and cellular response to heat stress (BH `= 0.00383`).

`HSPA1A` and `HSPH1` help other proteins fold or recover from stress. `PTGES3` also acts as a protein chaperone in addition to its other functions. HSF1 is a regulator that turns on many heat-shock genes. “Heat shock” in a pathway name does not require literal high temperature; many forms of cell stress can activate the same protective machinery.

#### Why this may matter

Vascular cells help maintain blood flow and the blood–brain barrier. A stress-response module could point to protein damage or vascular strain in this subgroup. Because only three stress genes drive the pathway result, it is better treated as a focused clue than a broad program.

#### Supplemental SEA-AD evidence

SEA-AD had no active vascular category, so this result is not evaluable there. The candidate remains a low-confidence ROSMAP lead because of its small internal call count, not because SEA-AD is missing.

#### What is not proven

- Only two female ε4 vascular calls were eligible.
- Three related genes drive the enrichment, and pathway terms overlap.
- The analysis does not show what type of stress triggered the genes.
- It does not establish a female × ε4 interaction.



#### Best next evidence

Confirm the module in donor-level vascular-cell data and test disease × sex × ε4 interactions. Spatial protein measurements near brain vessels could determine whether HSF1 targets increase in the same cells and locations as vascular Alzheimer’s pathology.

## 7. Supplemental SEA-AD support in detail



### 7.1 Why exact matching is narrow and uneven

SEA-AD contains 22 active KDA calls:

- `F_e33` excitatory: 1;
- `F_e4` astrocyte: 1;
- `M_e33` excitatory: 10;
- `M_e33` inhibitory: 8;
- `M_e33` oligodendrocyte: 2.

Twenty of 22 calls are `M_e33`; 20 calls returned drivers and two `M_e33` excitatory calls were empty. The output contains 44 non-MT gene-by-category units representing 43 genes.

This uneven coverage is why “not evaluated” and “did not reproduce” must remain separate. SEA-AD gives almost no information about ε2 or male ε4 categories and provides only one female ε4 astrocyte call. Even a tested-but-not-returned gene supplies only limited counterevidence because the networks, phenotype labels, thresholds, and sample sizes differ.

Accordingly, exact same-context matching is reported for transparency but is not an inclusion requirement. Same-gene recurrence in another context and pathway/program agreement are counted as weaker forms of cross-cohort support.

### 7.2 Strongest program-level matches


| Matched category        | Shared effective query genes and direction                                                                                                                                                                                                                                                              | Interpretation                                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `F_e33` excitatory      | Nine shared mtDNA genes, all up in both cohorts: `MT-ATP6`, `MT-CO1`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND1`, `MT-ND2`, `MT-ND4`, `MT-ND5`. These are 9/10 genes in the sole SEA query; SEA program BH `= 5.00 × 10^-16`.                                                                               | **Strongest, but narrow, cross-cohort program evidence.** SEA-AD adds program support even though it selects different drivers.                                                   |
| `M_e33` inhibitory      | 22 shared genes; 19 fixed-direction concordant and 3 discordant. Concordant mtDNA-up: `MT-ATP6`, `MT-CO2`, `MT-CO3`, `MT-CYB`, `MT-ND1`, `MT-ND2`, `MT-ND3`, `MT-ND4`, `MT-ND4L`. Concordant nuclear/maintenance-down: `UQCRFS1`, `SLC25A5`, `TIMM13`, `TIMM17A`, `MRPL16`, `MRPS34`, `ENDOG`, `MTCH1`. | **Moderate-to-strong mitonuclear-program concordance**, concentrated in a subset of SEA inhibitory types. Driver identity differs, which is acceptable for program-level support. |
| `M_e33` excitatory      | 35 shared genes: 17 concordant, 7 discordant, and 11 with mixed direction across ROSMAP fine types. SEA has a clean mtDNA-up call, while ROSMAP mtDNA direction varies by fine type.                                                                                                                    | **Partial support only.** Aggregation would hide heterogeneity.                                                                                                                   |
| `F_e4` astrocyte        | Two shared genes: `NDUFS8` up/up and `MRPS6` mixed/up.                                                                                                                                                                                                                                                  | **Little added support.** The SEA query contains only five genes, so this is not treated as rejection.                                                                            |
| `M_e33` oligodendrocyte | Only `HSPD1`, ROSMAP down and SEA up.                                                                                                                                                                                                                                                                   | **No positive directional support in this one-gene comparison.** This does not address the broader ROSMAP findings.                                                               |


The three discordant `M_e33` inhibitory genes were `HIBCH` (ROSMAP down/SEA up), `ISCU` (up/down), and `TMEM126B` (up/down).

The cross-cohort overlap test was significant for `F_e33` excitatory neurons: 9 genes were shared versus 3.83 expected by chance (raw `P = 0.00101`, BH `= 0.00505`). It was also significant for `M_e33` inhibitory neurons: 22 genes were shared versus 15.17 expected (raw `P = 0.0167`, BH `= 0.0417`).

The `F_e4` astrocyte, `M_e33` excitatory, and `M_e33` oligodendrocyte overlaps did not exceed chance after correction (BH `= 0.819`, `0.971`, and `0.819`). Excluding identity-conflict symbols preserved both supported categories (`F_e33` excitatory: 9 shared, BH `= 0.00441`; `M_e33` inhibitory: 21 shared, BH `= 0.0486`). The SEA `5.00 × 10^-16` value in the table is instead within-call enrichment of mtDNA genes in the `F_e33` query.

### Finding 17: SEA-AD provides program and cross-context support despite no exact driver matches

**Provisional novelty: Moderate and analytical rather than mechanistic.** This is a new comparison of these ROSMAP and SEA-AD outputs, but it evaluates reproducibility rather than proposing a new biological mechanism.

#### Plain-language takeaway

The strongest cross-cohort agreement is at the level of mitochondrial gene programs described in Findings 1 and 2. None of the directly testable non-mitochondrial ROSMAP driver-category results was selected again in the exact same SEA-AD sex/APOE and broad-cell context.

Three driver genes appeared somewhere in both studies, but in different contexts. Under the relaxed framework, these count as partial cross-cohort support rather than failures.

#### What the exact comparison showed

Of 83 ROSMAP non-MT driver-category units located in a category that SEA-AD could structurally test, 72 had the driver gene present in at least one matching SEA-AD network background. This distinction matters: a gene absent from the network could never be selected, while a gene present in the background was genuinely available to KDA.

None of the 72 available units was returned in the exact same sex/APOE and broad-cell category. Across 12,941 intersected non-MT gene-category opportunities, the analysis observed 0 exact matches and expected only 0.173 by chance (`P = 1`, one-sided hypergeometric). Because even the chance expectation was much lower than one, zero matches is not evidence of active disagreement. It means only that SEA-AD supplies no support at the strictest tier.

If mitochondrial drivers are retained, 13 exact units appear. However, 11/13 SEA-AD rows are mitochondrial genes that also belong to the query itself. That query/self signal does not replace the stricter non-MT driver test.

#### Three genes provide context-relaxed support

Only three non-MT genes recur anywhere in both driver lists:

- `LAGE3`: ROSMAP `F_e2`, `F_e4`, and `M_e2` excitatory; SEA `M_e33` inhibitory (two calls; exploratory aggregate score `0.00702`). Its SEA neighborhoods include `TIMM10`, `POLDIP2`, `ATP5MC1`, `UQCR11`, and `PET100`. This is **weak-to-moderate any-context support** because both the group and neuron class differ, but the SEA neighborhood is mitochondrial.
- `MIPOL1`: ROSMAP `F_e4` and `M_e33` inhibitory; SEA `M_e33` excitatory (two calls; score `0.02595`). This is **moderate partial-context support** because the male ε3/ε3 stratum matches even though the broad neuronal class differs.
- `PAPOLA`: ROSMAP `F_e4` OPC; SEA `M_e33` oligodendrocyte (one call; score `0.03836`). This is **weak lineage-level support** because OPCs and oligodendrocytes are related, while sex/APOE and exact cell context differ.

These recurrences do not establish that a driver acts identically across groups. They do show that the same genes can be prioritized by two independent cohort-specific networks. `LAGE3` has the clearest mitochondrial SEA neighborhood, while `MIPOL1` has the closest sex/APOE match.

Globally, 3/43 SEA-AD non-MT driver genes overlapped the 228 ROSMAP genes, versus 1.02 expected in the 6,836-gene intersected network universe (odds ratio `3.15`, one-sided `P = 0.0812`). This is suggestive but not statistically significant gene-level convergence.

The odds ratio says that overlap was about three times the random expectation, but the P value remained above the conventional 0.05 threshold. With only three genes, random variation is still a plausible explanation.

#### Why programs can agree when drivers do not

Different genes can connect to the same biological program. In addition, ROSMAP and SEA-AD use different cohort-specific networks, disease definitions, available fine-cell types, and query thresholds. SEA-AD also has only 22 active calls, 20 of which are male ε3/ε3. These factors can change the top-ranked network gene even when mtDNA or OXPHOS DEGs point in a similar direction.

SEA-specific thematic candidates include `U2AF2`, whose `M_e33` excitatory neighborhood contains the mitochondrial RNA genes `TBRG4` and `FASTK`, and `SECISBP2`, noted above. They may explain program convergence despite different driver rankings.

#### What is not proven

- Zero exact matches does not disprove every ROSMAP driver.
- Most ROSMAP sex/APOE and cell categories had no SEA-AD opportunity.
- `LAGE3`, `MIPOL1`, and `PAPOLA` receive partial cross-context support but are not confirmed in their original contexts.
- The global three-gene overlap did not meet the 0.05 significance threshold.
- Similar mitochondrial programs do not prove a shared upstream cause.



#### Best next evidence

Freeze each ROSMAP driver-associated mitochondrial gene set before looking at another cohort, then test the full signed set across both matched and related cell contexts. Rebuild or harmonize networks using stable gene IDs and comparable thresholds. A larger cohort with balanced sex/APOE groups would strengthen exact matching, but exact matching is not required to retain the current ROSMAP candidates.

## 8. Orthogonal human-genetic evidence

The local [phase19b first-pass screen](../../../results/minerva_production/19b_genetic_support_tier1/fungen_gene_evidence.tsv) provides gene-level, not cell-mechanism-level, evidence:

- **Strong:** `APOE`, `PLCG2`;
- **Weak:** `SELENOW` through public TWAS-list membership;
- **None found in that registered source:** `RPL11`, `RPS15`, `WDR82`, `SELENOM`, `LAMTOR5`, `PGK1`, `FTL`, `ANKRD11`, and `LAGE3`.

“None found” is not evidence that no genetic association exists. A focused [RPS15 public-data recovery](../../../results/minerva_production/19_genetic_support_opc_rps15_public_recovery/opc_rps15_status.tsv) found suggestive QTL signals but no resolved colocalization and no newly validated gene.

The genetics therefore strengthens `PLCG2` and expectedly `APOE`, modestly supports `SELENOW`, and does not independently validate the main ribosomal or LAMTOR5 network mechanisms.

## 9. Evidence-based candidate priorities


| Priority | Candidate/theme                        | Why retain it                                                                                             | Main reason not to overclaim                                                                     |
| -------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1        | `RPL11`/`RPS15` ribosomal module       | Highest recurrence, strong driver-list pathway enrichment, and coherent RPL11 nuclear-OXPHOS neighborhood | Network-degree bias and shared-donor dependence                                                  |
| 2        | `LAMTOR5` lysosome–mTOR–OXPHOS         | Recurrent, coherent OXPHOS neighborhood, direct driver DEG support, strong mechanistic literature         | Exploratory aggregation scores, large `M_e2` queries, and no direct causal experiment            |
| 3        | `WDR82` mtDNA-up module                | Exceptional 18/18 program coherence and precise excitatory pattern                                        | Narrow polycistronic four-mtDNA-gene neighborhood and no established mechanism                   |
| 4        | `SELENOM` and `SELENOW` separately     | Recurrent, driver DEG support, distinct mitochondrial neighborhoods; strong tau literature for SELENOW    | Experimental literature does not establish the inferred human neuronal network edges             |
| 5        | `PGK1`–`BNIP3/BNIP3L` astrocyte module | Exact focused neighborhood, driver DEG in two calls, human glial-program and APOE4-mitophagy context      | Only three calls, inconsistent PGK1 direction, and possible ROSMAP donor overlap with prior work |
| 6        | OPC `FTL`/`ANKRD11` module             | Repeated iron/GPX4/OXPHOS neighborhood and exploratory autophagy/mitophagy ORA                            | One OPC fine type, nearly identical neighborhoods, and no direct ferroptosis measurement         |
| 7        | `PLCG2` inhibitory mtDNA signal        | Strong gene-level genetics and relevant AD literature                                                     | Single-gene `MT-CO1` overlap, no driver DEG, and unexpected cell context                         |


The relaxed SEA-AD framework adds three secondary cross-cohort leads:

- `LAGE3`, because it recurs across cohorts and its SEA-AD neighborhood is strongly mitochondrial;
- `MIPOL1`, because the male ε3/ε3 group recurs across cohorts even though the neuronal class changes; and
- `PAPOLA`, because it recurs across the related OPC–oligodendrocyte lineage despite different sex/APOE groups.

These three genes are not promoted above the primary ROSMAP candidates because the global cross-cohort gene overlap remains nonsignificant (`P = 0.0812`) and the contexts differ. Their recurrence is still useful for the general Alzheimer’s-driver goal.

For a main paper narrative, the recurrent ROSMAP KDA drivers and their mitochondrial neighborhoods can serve as the central discovery results. SEA-AD program and cross-context matches should be presented as supplemental confidence-building evidence, not as a filter that determines which ROSMAP candidates may be discussed.

## 10. Artifacts needed to support or refute each claim



### 10.1 Essential statistical artifacts

1. **Donor-level pseudobulk or mixed-model DEG table** for every shortlisted fine type, with donor counts, effect sizes, confidence intervals, and disease × sex/APOE interaction terms.
2. **Program-level interaction heatmap** showing signed effect size for the four frozen programs by broad cell type and stratum, with interaction FDR separate from color.
3. **Leave-one-donor-out and threshold-sensitivity results** for each candidate-associated mitochondrial gene set.
4. **Full-test category aggregation** using all eligible driver tests or a null procedure that reproduces return-based selection; do not treat current returned-only ACAT scores as q-values.



### 10.2 Network robustness artifacts

1. Degree- and expression-matched null neighborhoods for ribosomal genes, WDR82, PLCG2, and heat-shock genes.
2. Edge-direction and confidence summaries rather than overlap alone.
3. KDA sensitivity after removing mtDNA genes, high-mitochondrial-read nuclei, and ubiquitous ribosomal/stress genes.
4. A driver-by-overlap-gene matrix with DEG direction, respiratory complex, and fine-cell support.



### 10.3 Optional cross-cohort support artifacts

1. Freeze each ROSMAP driver-associated mitochondrial gene set before testing SEA-AD.
2. Evaluate signed set-level effects in both matching and biologically related SEA subtypes, including calls whose query did not pass KDA size thresholds.
3. Report “not evaluable,” “no added support,” “any-context recurrence,” “partial-context recurrence,” “program concordance,” and “exact-context driver support” separately.
4. Harmonize AD/NCI versus dementia/no-dementia phenotypes and DEG thresholds where possible.
5. Do not remove a ROSMAP candidate solely because SEA-AD lacks coverage or returns a different driver.



### 10.4 Mechanistic follow-up

- `RPL11`/`RPS15`: perturbation with protein-synthesis, integrated-stress, p53, OXPHOS, and respiration readouts.
- `LAMTOR5`: lysosomal pH, V-ATPase assembly, mTORC1 localization, mitophagy flux, and respiration.
- `WDR82`: nuclear versus mitochondrial transcription, H3K4me3, mtDNA copy number, and mtRNA stability.
- `SELENOM`/`SELENOW`: separate perturbations measuring selenium dependence, redox/calcium, proteostasis, tau, and the exact KDA mitochondrial genes.
- `PGK1`: astrocyte glycolytic flux, lactate, hypoxia signaling, BNIP3/BNIP3L-dependent mitophagy, and APOE-genotype interaction.
- `FTL`/`ANKRD11`: OPC iron pool, ferritin turnover, lipid peroxidation, GPX4 activity, maturation, and mitochondrial function.
- `PLCG2`: cell-identity validation followed by neuron/microglia-specific perturbation and MT-CO1/respiration assays.

This evidence ladder follows the precedent of moving from human network prioritization to context-specific perturbation used in prior sex-specific AD KDA work ([Guo et al., 2023](https://doi.org/10.1186/s13024-023-00624-5)).

## 11. Limitations that materially affect interpretation

1. **Upstream donor independence is not established.** The stored ROSMAP MAST specification lists nucleus-level observations with `nCount_RNA`, age at death, and PMI covariates, but no donor term. Treating nuclei as independent can produce anticonservative P values; donor pseudobulk or a donor-aware mixed model is required.
2. **Current category scores are exploratory.** Recurrent rows use equal-weight ACAT of already returned within-call adjusted P values; singletons pass through the within-call value. Nonreturned tests are omitted and no final across-gene BH is applied. Within each call, the best of up to three neighborhood layers is selected before BH, without a separate layer-selection correction.
3. **Stratum-specific significance is not a modifier test.** A result present in women and absent in men does not prove a sex difference, nor does detection in ε4 prove an APOE4 interaction.
4. **KDA is observational network association.** “Key driver” does not establish causal regulation, and `overlap_items` are neighborhood signature genes rather than experimentally verified targets.
5. **Mitochondrial enrichment is partly designed in.** Core-MitoCarta DEGs define the query. Only subprogram, direction, context, and non-MT linkage add biological specificity.
6. **Both operational MitoCarta mappings contain cross-gene synonym conflicts.** The targeted ROSMAP program pattern is nearly unchanged after excluding flagged symbols, but driver calls in both cohorts must be rerun from stable-ID-corrected mitochondrial queries; `RPL13` must not be conflated with `MRPL13`.
7. **Network topology can favor ubiquitous genes.** Ribosomal proteins, heat-shock proteins, GAPDH, ubiquitin genes, and other hubs require degree-matched sensitivity analyses.
8. **SEA-AD opportunity is highly incomplete.** Only five categories are active, 20/22 calls are `M_e33`, networks are cohort-specific, and the query threshold differs from ROSMAP. Consequently, absent or nonmatching SEA-AD results cannot serve as a general rejection criterion for ROSMAP candidates.
9. **mtRNA signals are QC-sensitive.** The WDR82 and PLCG2 findings especially require checks for mitochondrial read fraction, RNA quality, ambient RNA, doublets, and altered cell-state composition.
10. **Pathway ORA is exploratory.** The background is network-aware at the gene-list level but does not model node degree, gene correlation, or repeated selection across related networks.
11. **Literature is supporting context, not validation.** Studies in cell lines, mice, or the same discovery resource cannot independently establish the proposed ROSMAP mechanism.



## 12. Conclusions

The most defensible study-level narrative is:

> AD-associated mitochondrial transcription differs across sex/APOE strata, with coordinated OXPHOS upregulation in female ε2/ε3 contexts, nuclear-OXPHOS repression in female ε4, broad mtDNA/nuclear repression in male ε2, and mtDNA-up/nuclear-down discordance in male ε3/ε4 contexts. Non-mitochondrial KDA candidates connect these programs primarily to cytosolic ribosome/translation and lysosome–autophagy–nutrient sensing.

ROSMAP is sufficient to nominate the driver genes below as discovery-stage, testable mechanisms:

- recurrent module representatives: `RPL11`, `RPS15`, `LAMTOR5`;
- focused novel candidates: `WDR82`, `SELENOM`, `SELENOW`, `PGK1`;
- context-specific secondary modules: OPC `FTL`/`ANKRD11`, inhibitory `PLCG2`, astrocyte `APOE`, and F_e4 vascular heat shock.

SEA-AD adds strong program-level support for `F_e33` excitatory mtDNA upregulation and `M_e33` inhibitory mitonuclear discordance. It also adds context-relaxed gene support for `LAGE3`, `MIPOL1`, and `PAPOLA`. The absence of an exact same-context non-MT driver match is reported transparently but does not invalidate or remove the ROSMAP candidates.

The immediate priorities are donor-aware interaction testing, network-robustness analyses, and mechanistic experiments. Additional cross-cohort testing is valuable but optional. Those analyses will determine whether the current patterns reflect genuine sex/APOE modification or thresholded recurrence within related postmortem data.

## Focused literature

1. Guo L et al. Sex specific molecular networks and key drivers of Alzheimer’s disease. *Molecular Neurodegeneration* (2023). [doi:10.1186/s13024-023-00624-5](https://doi.org/10.1186/s13024-023-00624-5)
2. Mathys H et al. Single-cell multiregion dissection of Alzheimer’s disease. *Nature* (2024). [doi:10.1038/s41586-024-07606-7](https://doi.org/10.1038/s41586-024-07606-7)
3. Ding Q et al. Ribosome dysfunction is an early event in Alzheimer’s disease. *Journal of Neuroscience* (2005). [doi:10.1523/JNEUROSCI.3040-05.2005](https://doi.org/10.1523/JNEUROSCI.3040-05.2005)
4. Zhang Y et al. Ribosomal protein L11 negatively regulates oncoprotein MDM2 and mediates a p53-dependent ribosomal-stress checkpoint pathway. *Molecular and Cellular Biology* (2003). [doi:10.1128/MCB.23.23.8902-8912.2003](https://doi.org/10.1128/MCB.23.23.8902-8912.2003)
5. Bar-Peled L et al. Ragulator is a GEF for the Rag GTPases that signal amino acid levels to mTORC1. *Cell* (2012). [doi:10.1016/j.cell.2012.07.032](https://doi.org/10.1016/j.cell.2012.07.032)
6. Morita M et al. mTORC1 controls mitochondrial activity and biogenesis through 4E-BP-dependent translational regulation. *Cell Metabolism* (2013). [doi:10.1016/j.cmet.2013.10.001](https://doi.org/10.1016/j.cmet.2013.10.001)
7. Norambuena A et al. A novel lysosome-to-mitochondria signaling pathway disrupted by amyloid-β oligomers. *EMBO Journal* (2018). [doi:10.15252/embj.2018100241](https://doi.org/10.15252/embj.2018100241)
8. Ren X et al. Selenoprotein W modulates tau homeostasis in an Alzheimer’s disease mouse model. *Communications Biology* (2024). [doi:10.1038/s42003-024-06572-0](https://doi.org/10.1038/s42003-024-06572-0)
9. Lee H et al. ApoE4-dependent lysosomal cholesterol accumulation impairs mitochondrial homeostasis and oxidative phosphorylation in human astrocytes. *Cell Reports* (2023). [doi:10.1016/j.celrep.2023.113183](https://doi.org/10.1016/j.celrep.2023.113183)
10. Magno L et al. Alzheimer’s disease phospholipase C-gamma-2 protective variant is a functional hypermorph. *Alzheimer’s Research & Therapy* (2019). [doi:10.1186/s13195-019-0469-0](https://doi.org/10.1186/s13195-019-0469-0)
11. Squair JW et al. Confronting false discoveries in single-cell differential expression. *Nature Communications* (2021). [doi:10.1038/s41467-021-25960-2](https://doi.org/10.1038/s41467-021-25960-2)
12. Belloy ME et al. APOE in Alzheimer’s disease: a genetic, molecular and therapeutic review. *Neuron* (2019). [doi:10.1016/j.neuron.2019.03.075](https://doi.org/10.1016/j.neuron.2019.03.075)



## Appendix A. Complete ROSMAP non-MT recurrence inventory

The original category-occurrence inventory is retained below as a reference. It should be read together with the eligibility and non-independence caveats above.

### A.1 Analysis scope

- Cohort: ROSMAP only.
- Source: `results/minerva_production/20_sex_apoe_kda_combo/combo_key_drivers_by_category.tsv`.
- Category: one of six sex/APOE groups crossed with one of seven broad cell types, giving 42 possible categories.
- Analysis unit: one non-mitochondrial key-driver gene in one category.
- Mitochondrial key drivers (`is_core_mito = TRUE`) are excluded.
- A gene is counted at most once in a category.
- Fine-cell identities and fine-cell-level recurrence are not used in this section.

These appendix counts preserve the stored mitochondrial annotation and should be revised after the stable-ID correction described in Section 4.1.

After these restrictions, the aggregated table contains 381 gene × category records representing 228 unique non-mitochondrial key-driver genes. Twenty-nine of the 42 possible categories contain at least one such record.

### A.2 Distribution of key-driver occurrence across categories

For every key-driver gene, its occurrence count is the number of distinct sex/APOE × broad-cell categories in which it appears. The distribution is:


| Number of categories containing the gene | Number of genes | Percentage of 228 genes | Gene × category records contributed |
| ---------------------------------------- | --------------- | ----------------------- | ----------------------------------- |
| 1                                        | 158             | 69.3%                   | 158                                 |
| 2                                        | 34              | 14.9%                   | 68                                  |
| 3                                        | 19              | 8.3%                    | 57                                  |
| 4                                        | 7               | 3.1%                    | 28                                  |
| 5                                        | 3               | 1.3%                    | 15                                  |
| 6                                        | 2               | 0.9%                    | 12                                  |
| 7                                        | 2               | 0.9%                    | 14                                  |
| 8                                        | 1               | 0.4%                    | 8                                   |
| 9                                        | 0               | 0.0%                    | 0                                   |
| 10                                       | 1               | 0.4%                    | 10                                  |
| 11                                       | 1               | 0.4%                    | 11                                  |
| 12–42                                    | 0               | 0.0%                    | 0                                   |
| **Total**                                | **228**         | **100.0%**              | **381**                             |




### Summary

- 158 genes (69.3%) occur in exactly one category.
- 70 genes (30.7%) occur in at least two categories.
- 36 genes (15.8%) occur in at least three categories.
- 192 genes (84.2%) occur in no more than two categories.
- The broadest key driver occurs in 11 of the 42 possible categories.

The distribution is strongly right-skewed: most key drivers are restricted to one observed category, while a small group recurs across several categories.

This is a descriptive occurrence distribution, not yet evidence that the 158 single-category genes are biologically category-specific. Thirteen of the 42 structural categories do not contribute a non-mitochondrial aggregated driver record, and the categories differ in KDA opportunity. Later specificity analyses should distinguish a tested absence from a category in which a driver could not have been evaluated.

### A.3 Key drivers occurring in more than one category

Seventy of the 228 non-mitochondrial key-driver genes occur in at least two of the 42 sex/APOE × broad-cell categories. Together, these 70 genes account for 223 of the 381 gene × category records.


| Gene      | Number of categories | Categories                                                                                                                                                                                                                                                   |
| --------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ACAT2     | 2                    | F_e33 × Inhibitory neurons M_e2 × Inhibitory neurons                                                                                                                                                                                                         |
| ANKRD11   | 2                    | F_e33 × OPCs M_e2 × OPCs                                                                                                                                                                                                                                     |
| APOE      | 3                    | F_e2 × Astrocytes M_e2 × Astrocytes M_e4 × Astrocytes                                                                                                                                                                                                        |
| ATG101    | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| ATP6AP2   | 3                    | F_e2 × Inhibitory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                                                                                                               |
| ATP6V0B   | 2                    | F_e2 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                                          |
| ATP6V1F   | 3                    | F_e4 × Inhibitory neurons M_e2 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                |
| B3GAT3    | 2                    | M_e33 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                                         |
| BEX1      | 2                    | M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                                                                                                                                         |
| BEX3      | 3                    | F_e4 × Inhibitory neurons M_e2 × OPCs M_e33 × Excitatory neurons                                                                                                                                                                                             |
| BTF3      | 3                    | F_e2 × Excitatory neurons F_e33 × Inhibitory neurons M_e2 × Excitatory neurons                                                                                                                                                                               |
| CCDC85B   | 2                    | F_e4 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                                          |
| CHORDC1   | 2                    | M_e33 × Inhibitory neurons M_e33 × Microglia                                                                                                                                                                                                                 |
| CUTA      | 2                    | F_e33 × Excitatory neurons M_e2 × Inhibitory neurons                                                                                                                                                                                                         |
| DYNLL1    | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| DYNLT1    | 3                    | F_e33 × Excitatory neurons F_e4 × Inhibitory neurons M_e2 × Excitatory neurons                                                                                                                                                                               |
| EDF1      | 2                    | F_e33 × Excitatory neurons F_e33 × Inhibitory neurons                                                                                                                                                                                                        |
| FAU       | 2                    | F_e2 × Astrocytes M_e2 × Inhibitory neurons                                                                                                                                                                                                                  |
| FTL       | 2                    | F_e33 × OPCs M_e2 × OPCs                                                                                                                                                                                                                                     |
| GABARAPL2 | 5                    | F_e2 × Excitatory neurons F_e2 × Inhibitory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                                                           |
| GALNT2    | 2                    | F_e33 × Inhibitory neurons M_e2 × Inhibitory neurons                                                                                                                                                                                                         |
| GAPDH     | 5                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons M_e2 × OPCs M_e33 × Inhibitory neurons                                                                                                                                         |
| GATAD1    | 3                    | F_e2 × Inhibitory neurons F_e33 × Inhibitory neurons M_e2 × Inhibitory neurons                                                                                                                                                                               |
| GNG3      | 2                    | F_e2 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                                          |
| HSPA1A    | 3                    | F_e4 × Inhibitory neurons F_e4 × Vasculature M_e33 × Inhibitory neurons                                                                                                                                                                                      |
| HSPH1     | 2                    | F_e4 × Vasculature M_e33 × Microglia                                                                                                                                                                                                                         |
| KTN1      | 2                    | F_e33 × Inhibitory neurons M_e2 × Inhibitory neurons                                                                                                                                                                                                         |
| LAGE3     | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| LAMTOR5   | 6                    | F_e2 × Excitatory neurons F_e33 × Inhibitory neurons F_e4 × Excitatory neurons F_e4 × Inhibitory neurons M_e2 × Excitatory neurons M_e2 × Inhibitory neurons                                                                                                 |
| LAPTM4A   | 2                    | M_e2 × Astrocytes M_e4 × Astrocytes                                                                                                                                                                                                                          |
| MAGEF1    | 3                    | F_e4 × Excitatory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                                                                                                               |
| MAP1LC3A  | 2                    | M_e33 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                                         |
| METTL21A  | 2                    | F_e4 × Inhibitory neurons M_e33 × Inhibitory neurons                                                                                                                                                                                                         |
| MIPOL1    | 2                    | F_e4 × Inhibitory neurons M_e33 × Inhibitory neurons                                                                                                                                                                                                         |
| MT3       | 2                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons                                                                                                                                                                                                          |
| PCBP4     | 3                    | F_e4 × Inhibitory neurons M_e33 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                               |
| PER3      | 2                    | F_e33 × Inhibitory neurons F_e4 × Inhibitory neurons                                                                                                                                                                                                         |
| PGAM1     | 4                    | M_e2 × Inhibitory neurons M_e33 × Excitatory neurons M_e4 × Excitatory neurons M_e4 × Inhibitory neurons                                                                                                                                                     |
| PGK1      | 3                    | F_e33 × Astrocytes F_e4 × Astrocytes M_e4 × Astrocytes                                                                                                                                                                                                       |
| PLCG2     | 3                    | F_e2 × Inhibitory neurons F_e33 × Inhibitory neurons F_e4 × Inhibitory neurons                                                                                                                                                                               |
| PRDX1     | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| PSMB6     | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| RABAC1    | 4                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                                                                                     |
| RPL11     | 10                   | F_e2 × Astrocytes F_e2 × Excitatory neurons F_e33 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Astrocytes M_e2 × Excitatory neurons M_e2 × Oligodendrocytes M_e33 × Excitatory neurons M_e4 × Astrocytes M_e4 × Microglia                           |
| RPL15     | 7                    | F_e2 × Astrocytes F_e2 × Inhibitory neurons F_e4 × Astrocytes F_e4 × Excitatory neurons M_e2 × Astrocytes M_e2 × Excitatory neurons M_e33 × Excitatory neurons                                                                                               |
| RPL29     | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| RPL36     | 2                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons                                                                                                                                                                                                         |
| RPL36AL   | 4                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                     |
| RPL6      | 3                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                |
| RPLP1     | 8                    | F_e2 × Astrocytes F_e2 × Inhibitory neurons F_e4 × Inhibitory neurons M_e2 × Astrocytes M_e2 × Inhibitory neurons M_e33 × Inhibitory neurons M_e4 × Astrocytes M_e4 × Inhibitory neurons                                                                     |
| RPLP2     | 4                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                     |
| RPS13     | 5                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons M_e33 × Inhibitory neurons M_e4 × Excitatory neurons                                                                                                                           |
| RPS15     | 11                   | F_e2 × Astrocytes F_e2 × Excitatory neurons F_e2 × Inhibitory neurons F_e33 × Excitatory neurons F_e33 × OPCs F_e4 × Inhibitory neurons M_e2 × Excitatory neurons M_e2 × Inhibitory neurons M_e2 × OPCs M_e33 × Inhibitory neurons M_e4 × Inhibitory neurons |
| RPS25     | 2                    | M_e33 × Inhibitory neurons M_e4 × Astrocytes                                                                                                                                                                                                                 |
| RPS4X     | 2                    | F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                                          |
| SELENOM   | 7                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons F_e4 × Excitatory neurons F_e4 × Inhibitory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons M_e4 × Inhibitory neurons                                                                      |
| SELENOW   | 6                    | F_e2 × Excitatory neurons F_e4 × Excitatory neurons F_e4 × Inhibitory neurons M_e2 × Excitatory neurons M_e33 × Excitatory neurons M_e33 × Inhibitory neurons                                                                                                |
| SPATS2L   | 2                    | F_e4 × Vasculature M_e33 × Vasculature                                                                                                                                                                                                                       |
| SRSF7     | 2                    | F_e33 × Excitatory neurons F_e33 × Inhibitory neurons                                                                                                                                                                                                        |
| SSR2      | 2                    | F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                                          |
| SYN1      | 4                    | F_e2 × Inhibitory neurons F_e33 × Inhibitory neurons F_e4 × Inhibitory neurons M_e2 × Inhibitory neurons                                                                                                                                                     |
| TMEM147   | 4                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons F_e4 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                     |
| TPI1      | 2                    | F_e2 × Excitatory neurons M_e2 × Excitatory neurons                                                                                                                                                                                                          |
| TRERF1    | 2                    | F_e33 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                                         |
| TTC8      | 2                    | F_e4 × Excitatory neurons M_e4 × Excitatory neurons                                                                                                                                                                                                          |
| TUBA1A    | 2                    | F_e33 × Inhibitory neurons M_e33 × OPCs                                                                                                                                                                                                                      |
| UBB       | 2                    | M_e33 × Inhibitory neurons M_e33 × OPCs                                                                                                                                                                                                                      |
| UBC       | 2                    | F_e4 × Excitatory neurons M_e33 × OPCs                                                                                                                                                                                                                       |
| WDR82     | 4                    | F_e2 × Excitatory neurons F_e33 × Excitatory neurons M_e33 × Excitatory neurons M_e4 × Excitatory neurons                                                                                                                                                    |
| ZNF280D   | 2                    | F_e4 × Inhibitory neurons M_e4 × Inhibitory neurons                                                                                                                                                                                                          |
