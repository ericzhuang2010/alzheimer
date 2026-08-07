## **Methods and analysis workflow**

| Stage | What the authors did | Main tools and parameters |
| ----- | ----- | ----- |
| **1\. Data source** | Reused the Mathys et al. ROSMAP dataset containing approximately **2.3 million nuclei from prefrontal cortex tissue of 427 donors** spanning no impairment, mild cognitive impairment, Alzheimer’s disease, and other dementias. They used the original study’s **preprocessed count matrix and cell annotations**, including 54 fine-grained cell types grouped into 12 broad classes. | ROSMAP cohort; previously processed snRNA-seq counts and annotations |
| **2\. Sample selection and QC** | Restricted the analysis to donors with either **no cognitive impairment (NCI)** or **Alzheimer’s disease (AD)**. They checked reported sex using the sex-linked genes **XIST** and **UTY**, excluding four discordant samples. They also excluded APOE ε2/ε4 donors, samples without APOE genotype, and one sample missing postmortem interval. | Expression-based sex verification using XIST and UTY |
| **3\. Sex–APOE stratification** | Divided the final 276 donors into six groups: female or male combined with APOE ε2 carrier, ε3/ε3, or ε4 carrier status. The final dataset contained **142 NCI and 134 AD donors**. | ε2 carriers: ε2/ε2 or ε2/ε3; ε4 carriers: ε3/ε4 or ε4/ε4 |
| **4\. Cell-type-specific differential expression** | Within every one of the 54 cell clusters and each sex–APOE subgroup, compared AD with NCI expression. | **Seurat v5 `FindMarkers`**, with figure captions specifying the **MAST** test; genes expressed in at least 10% of cells; covariates: total RNA counts, age at death, and postmortem interval |
| **5\. Multiple-testing and DEG filtering** | Corrected gene-level tests for multiple comparisons and retained genes that passed both statistical and effect-size thresholds. | Benjamini–Hochberg correction; adjusted *p* \< 0.05; absolute fold change \> 1.3 |
| **6\. Pathway enrichment** | Tested whether DEG sets or similarity-ranked gene sets were enriched for canonical biological pathways. | **GOtest v1.0.9**; **MSigDB C2:CP canonical pathways**; hypergeometric test; all measured genes as background; BH-adjusted *p* \< 0.05 |
| **7\. Power analysis** | Simulated single-cell datasets to estimate how unequal subgroup sizes affected DEG-detection power, concentrating on microglia and the relatively small APOE ε2 groups. | **scDesign3**; 100 simulations per condition; power measured as the fraction of simulated true DEGs detected at 5% FDR |
| **8\. Cross-group similarity analysis** | Developed a new statistic—the **Zhang–Yu similarity measure**—to rank genes according to whether their AD-associated changes were concordant or divergent across sexes or APOE genotypes. | Custom ternary similarity score; 10,000 permutations; empirical FDR |
| **9\. Independent validation** | Compared sex-specific genes from the single-nucleus analysis with an independent bulk RNA-seq study of the parahippocampal gyrus from the Mount Sinai Brain Bank. | Adjusted DEG thresholds to address unequal female/male power; overlap assessed with **Fisher’s exact test** |

### **1\. Dataset and cohort construction**

The original ROSMAP data included 427 donors, but the main comparisons used only AD and NCI cases. Cell annotations covered excitatory and inhibitory neuronal subtypes, astrocytes, oligodendrocytes, oligodendrocyte precursor cells, microglia, macrophages, T cells, and several vascular cell populations. Because the authors started with preprocessed counts and existing cell labels, they did **not** repeat read alignment, count generation, dimensionality reduction, clustering, or cell-type annotation.

Sex was checked by comparing metadata with expression of **XIST**, which is generally associated with female cells, and **UTY**, which is Y-linked. Four discordant donors were removed. The six final groups ranged from 13 male APOE ε2 carriers to 82 donors in each of the female and male ε3/ε3 groups, illustrating the substantial imbalance in subgroup sizes. Nearly all 276 donors were self-reported White.

### **2\. Differential-expression analysis**

The core analysis consisted of **324 AD-versus-NCI contrasts**: six sex–APOE groups multiplied by 54 cell clusters. For example, female ε4-carrier AD nuclei were compared with female ε4-carrier NCI nuclei separately within each cell type.

#### **What the 324 contrasts compare**

The 324 “pairs” are pairs of sample groups, not 324 one-to-one matched donor pairs. For each cell type, the authors repeated these six comparisons:

| Contrast | AD group | NCI group |
| --- | --- | --- |
| 1 | Female APOE ε2-carrier AD nuclei | Female APOE ε2-carrier NCI nuclei |
| 2 | Female APOE ε3/ε3 AD nuclei | Female APOE ε3/ε3 NCI nuclei |
| 3 | Female APOE ε4-carrier AD nuclei | Female APOE ε4-carrier NCI nuclei |
| 4 | Male APOE ε2-carrier AD nuclei | Male APOE ε2-carrier NCI nuclei |
| 5 | Male APOE ε3/ε3 AD nuclei | Male APOE ε3/ε3 NCI nuclei |
| 6 | Male APOE ε4-carrier AD nuclei | Male APOE ε4-carrier NCI nuclei |

The same six contrasts were evaluated separately in each of the 54 cell types:

```text
54 cell types × 6 sex–APOE-specific AD-versus-NCI contrasts = 324 contrasts
```

For a particular cell type, sex, and APOE group, the two sets were:

```text
Set 1: nuclei from all eligible AD donors in that cell type and sex–APOE group
Set 2: nuclei from all eligible NCI donors in that cell type and sex–APOE group
```

For example, the astrocyte/female/ε4 contrast compared astrocyte nuclei from female ε4-carrier AD donors with astrocyte nuclei from female ε4-carrier NCI donors. The AD and NCI donors were not matched one to one. Each contrast tested whether gene expression differed between the two groups while accounting for total RNA count, age at death, and postmortem interval.

The authors used **Seurat version 5’s `FindMarkers` function**; the figure methods specify **MAST** as the differential-expression test. The apparent distinction is that Seurat served as the analysis framework and MAST as the statistical test selected within it. Genes had to be detected in at least 10% of cells in either comparison group. Total transcript counts per nucleus (`nCount_RNA`), age at death, and postmortem interval were included as covariates. Sequencing batch was evaluated but not included because the authors reported that it explained little gene-expression variance.

#### **What MAST adjustment means**

For each gene within one cell-type and sex–APOE contrast, the model can be summarized conceptually as:

```text
gene expression ~ AD-versus-NCI diagnosis + total RNA count + age at death + PMI
```

The diagnosis term is the effect of interest. “Adjusted” means that the estimated AD-versus-NCI difference accounts statistically for the other variables:

- Total RNA count (`nCount_RNA`) controls for differences in sequencing depth or the total number of transcripts detected in each nucleus.
- Age at death controls for expression differences associated with donor age.
- Postmortem interval (PMI) controls for the time between death and tissue collection or preservation, which can affect RNA quality and expression measurements.

MAST is designed for sparse single-cell data and uses a two-part, or hurdle, model. It considers both whether a gene is detected in a nucleus and how strongly it is expressed when detected. A positive AD effect indicates higher expression in AD after covariate adjustment; a negative effect indicates lower expression in AD after adjustment.

Covariate adjustment does not match individual AD donors to NCI donors and does not by itself account for correlation among nuclei from the same donor.

A gene was called differentially expressed when:

BH-adjusted p\<0.05and∣fold change∣\>1.3.

One detail not explicitly described in the main methods is a donor-level random effect or pseudobulk aggregation; the listed model covariates were RNA count, age, and postmortem interval.

### **3\. Pathway analysis**

For functional interpretation, the authors used the R package **GOtest 1.0.9** to perform over-representation analysis against the **C2:CP canonical pathway collection from MSigDB**. They used a hypergeometric test, treated all genes in the analyzed dataset as the background universe, and applied Benjamini–Hochberg correction. Pathways with adjusted *p* values below 0.05 were considered significant.

Despite its name, GOtest was not limited to Gene Ontology terms here; the paper specifically reports testing the MSigDB canonical pathway collection.

### **4\. Simulation-based power analysis**

Because the sex–APOE strata had unequal donor counts, the authors used **scDesign3** to estimate the resulting differences in power. They fitted scDesign3 to ROSMAP microglial expression data so the simulations reproduced characteristics such as gene-specific expression distributions, mean–variance relationships, zero inflation, and experimental covariates.

They then generated synthetic datasets with known AD-versus-NCI fold changes, designated a random subset of genes as truly differential, repeated the differential-expression analysis, and calculated the percentage of true DEGs recovered at a 5% FDR. Each condition was repeated **100 times**.

This analysis showed an important methodological limitation: the study had reasonable power for large expression changes but limited power for small or moderate effects, particularly in smaller groups such as male APOE ε2 carriers.

### **5\. Zhang–Yu similarity measure**

The major new computational method in the paper is the **Zhang–Yu similarity measure**. It was designed to summarize whether a gene’s AD-associated changes were similar or different across many cell types and subgroup comparisons.

For each AD-versus-NCI test, a gene was converted to a ternary state:

* **\+1:** significantly upregulated  
* **0:** not significantly changed  
* **−1:** significantly downregulated

The score can be summarized as:

Nconcordant changes−0.5(change in only one group)−opposite-direction changes.

Thus, the score rewards two groups changing in the same direction, gives a partial penalty when only one group changes, and gives the strongest penalty when the groups change in opposite directions. Scores range from **−1**, indicating maximum divergence, to **\+1**, indicating maximum concordance. The metric uses the direction and significance category of the DEG result, not the exact fold-change magnitude.

The authors applied it to three principal comparisons:

1. Female versus male AD responses across the three APOE groups and 54 cell clusters.  
2. APOE ε2 carriers versus ε3/ε3 across both sexes and 54 clusters.  
3. APOE ε4 carriers versus ε3/ε3 across both sexes and 54 clusters.

Genes were ranked from most concordant to most divergent. Statistical significance was evaluated using **10,000 permutations** of the ternary states, followed by empirical FDR estimation at 0.05.

### **6\. Independent validation**

For external validation, the authors used previously generated **bulk RNA-seq data from the parahippocampal gyrus** in the Mount Sinai Brain Bank. They compared female-specific and male-specific AD signatures from that study with genes identified as sex-dependent by the Zhang–Yu measure.

Because the bulk dataset had substantially more female DEGs, the female significance threshold was progressively tightened to make the female and male DEG-set sizes more comparable. Enrichment of overlapping sex-specific genes was then evaluated using **Fisher’s exact test**. This was a useful cross-cohort check, although it involved bulk tissue from a different brain region rather than an independent single-nucleus replication.

## **Software and resources explicitly named**

The principal computational tools were:

* **Seurat v5** — data handling and cluster-specific `FindMarkers` analysis.  
* **MAST** — differential-expression testing within Seurat.  
* **GOtest v1.0.9** — pathway over-representation analysis.  
* **MSigDB C2:CP** — canonical pathway gene sets.  
* **scDesign3** — realistic single-cell simulation and power analysis.  
* **Custom Zhang–Yu similarity code** — concordance/divergence ranking and permutation testing.  
* **Benjamini–Hochberg correction**, hypergeometric tests, empirical FDR, and Fisher’s exact tests — statistical procedures.

The main article text does not report a specific R version or identify a public code repository for the custom similarity implementation.

## **Bottom-line methodological summary**

The study is best understood as a **large, stratified computational reanalysis** rather than a new single-cell experiment. Its strongest methodological features are the fine cell-type resolution, explicit sex-by-APOE stratification, pathway analysis, simulation-based examination of power, and a custom metric for integrating hundreds of differential-expression contrasts. The major constraints are unequal subgroup sizes, limited ancestry diversity, reliance on existing preprocessing and annotations, and validation in bulk tissue rather than an independent single-nucleus cohort.


