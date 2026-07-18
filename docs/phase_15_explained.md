# Phase 15 explained: final figures and their interpretation

## 1. What Phase 15 does

Phase 15 turns validated numerical results from earlier phases into a compact set of final PDF figures.

The most important point is:

> Phase 15 does not rerun differential-expression models, discover new genes, calculate new p-values, or change any upstream scientific result. It reads already-computed tables, selects and arranges values for plotting, writes figures, and records enough provenance to verify where every figure came from.

This is similar to making graphs for a laboratory report after all measurements and statistical tests have already been completed. The graph makes the result easier to see, but it does not replace the underlying data table.

Phase 15 is implemented by `scripts/15_make_figures.R` and is invoked through the `figures` mode of `scripts/run_pipeline.R`.

The final Minerva output is:

```text
results/minerva_production/15_figures/
```

The local-pilot output is:

```text
results/local_pilot/15_figures/
```

The same plotting code is used for both. Configuration changes determine whether the input is the small local pilot or the complete Minerva production analysis.

## 2. Where Phase 15 fits in the analysis

Phase 15 is the final presentation phase. It depends on Phase 14 validation and on results created throughout the project:

```text
Phase 02 cohort selection ---------------------> Figure 01
Phase 06 group coverage -----------------------> Figure 02
Phase 04 donor-level mitochondrial QC ---------> Figure 03
Phase 09 mitochondrial-fraction models --------> Figure 04
Phase 11 gene multiple-testing results --------> Figure 05
Phase 11 pathway multiple-testing results -----> Figure 06
Phase 09 mitonuclear summaries ----------------> Figure 07
Phase 11 similarity multiple-testing results --> Figure 08
Phase 12 sensitivity/robustness status --------> Figure 09
Phase 13 power simulations --------------------> Figure 10

Phase 14 validated_complete
                  |
                  v
        Phase 15 may render figures
```

Phase 15 refuses to start unless:

```text
results/<execution stage>/14_validation/validation_status.tsv
```

contains exactly one row with `validation_status = validated_complete`.

This requirement means that Phase 15 cannot silently turn an unvalidated collection of partial files into something that looks like a final result.

## 3. Essential vocabulary

### 3.1 Donor, nucleus, and pseudobulk

- A **donor** is one person.
- A **nucleus** is one measured nucleus from brain tissue. One donor can contribute many nuclei.
- A **pseudobulk sample** adds the UMI counts from all eligible nuclei belonging to one donor and one fine cell type.

Many nuclei from the same donor are not independent people. Therefore, the primary inferential unit is the donor. Phase 15 checks that no inferential figure reports the number of nuclei as if it were the independent sample size.

### 3.2 Broad and fine cell types

The project has nine source RDS objects, representing broad cell classes such as astrocytes, inhibitory neurons, and vasculature. Those objects contain 54 high-resolution, or **fine**, cell types. A figure can therefore contain many more than nine cell-type labels even though there are only nine RDS input objects.

### 3.3 Diagnosis

- `AD` means Alzheimer's disease.
- `NCI` means no cognitive impairment.

A direct contrast named, for example,

```text
AD_vs_NCI__Female__e33
```

compares female AD donors with female NCI donors in the APOE e33 group, within one fine cell type.

### 3.4 APOE groups

The frozen cohort mapping is:

- `e2`: APOE 22 or 23;
- `e33`: APOE 33; and
- `e4`: APOE 34 or 44.

APOE 24, the e2/e4 combination, is excluded before these groups are formed.

### 3.5 UMI count

A UMI, or unique molecular identifier, is a molecular tag used to count captured RNA molecules while reducing duplicate counting from repeated sequencing reads. One UMI count is treated as evidence for one captured RNA molecule. A UMI count is not the same as the raw number of sequencing reads.

### 3.6 mtDNA genes, MitoCarta genes, and OXPHOS

- The mitochondrial genome directly encodes 13 protein-coding genes. These have names such as `MT-ND1`, `MT-CO2`, and `MT-ATP6`.
- **MitoCarta** is a much larger curated inventory of proteins associated with mitochondria. Most MitoCarta genes are encoded in nuclear DNA.
- **OXPHOS**, oxidative phosphorylation, is the mitochondrial energy-production system. Its protein machinery includes both mtDNA-encoded and nuclear-encoded subunits.

### 3.7 Contrast

A contrast is a planned statistical comparison. Examples include:

- AD versus NCI within female e33 donors;
- the AD effect in females minus the AD effect in males; and
- a global test asking whether the AD effect differs anywhere among the six sex-APOE groups.

### 3.8 Effect size, confidence interval, p-value, and FDR

- An **effect size** tells how large and in what direction a difference is.
- A **95% confidence interval** shows the range of effect sizes reasonably compatible with the model and data under its assumptions.
- A **p-value** measures how surprising the observed test statistic would be under the test's null hypothesis.
- **FDR**, false discovery rate, is a multiple-testing adjustment. It is needed because thousands of tests create many opportunities for a small p-value to occur by chance.

An FDR below 0.05 is a threshold used by this project. It does not mean there is a 95% probability that a particular biological claim is true. It controls an expected error proportion across a declared family of tests.

## 4. Descriptive versus inferential figures

The ten PDFs do not all answer the same kind of question.

| Figure | Type | Main purpose |
|---|---|---|
| 01 | Descriptive | Show how the donor cohort was formed. |
| 02 | Descriptive | Show donor coverage in every diagnosis-sex-APOE-cell-type combination. |
| 03 | Descriptive | Summarize donor-level mitochondrial RNA percentages. |
| 04 | Inferential | Show adjusted mitochondrial-fraction model effects. |
| 05 | Inferential | Show selected mtDNA gene differential-expression effects. |
| 06 | Inferential | Show selected mitochondrial-pathway rank effects. |
| 07 | Descriptive | Summarize donor-level mtDNA:nuclear OXPHOS balance. |
| 08 | Inferential | Show similarity of significant-change patterns across sex or APOE comparisons. |
| 09 | Workflow/robustness summary | Show which sensitivity branches completed and how many result rows they made. |
| 10 | Simulation-based inference diagnostic | Show false-positive rate and power under simulated effects. |

A descriptive difference between two boxes or two colors is not automatically statistically significant. Figures 03 and 07, for example, do not adjust for age, PMI, sex, or APOE and do not display a p-value.

## 5. Exact Phase 15 workflow

Phase 15 performs the following operations.

1. It reads the analysis configuration and execution configuration.
2. It decides whether the run is `local_pilot` or `minerva_production`.
3. It requires Phase 14 to be `validated_complete`.
4. It identifies all required input tables.
5. It calculates SHA-256 checksums for every upstream input before plotting.
6. It reads the tables and verifies that all required columns exist.
7. It renders ten one-page PDF files. Each PDF is 14 by 8.5 inches.
8. It first writes each PDF to a temporary path and then renames it to the final path. This reduces the chance that a crash leaves a half-written PDF with a final-looking name.
9. It uses stage-neutral figure titles. The PDFs do not display the phase,
   execution stage, or output status in the top-right corner or title.
10. It writes a figure manifest connecting each PDF to its source table or tables.
    The manifest and status TSV retain the execution stage and output status so
    provenance is preserved without placing operational labels in the figures.
11. It calculates the upstream checksums again and verifies that no source file changed while the figures were being made.
12. It writes validation checks, artifact checksums, and the one-row Phase 15 status file.

If a scientific quantity cannot be estimated, Phase 15 can create a labeled `not_estimable` placeholder rather than silently omitting the planned figure. A plotting exception is different: it produces `render_status = failed` and makes the Phase 15 task fail.

## 6. Common graphical conventions

### 6.1 The dashed zero line

Figures 04, 05, 06, and 08 contain a vertical dashed line at zero.

- A point to the right has a positive effect or score.
- A point to the left has a negative effect or score.
- A point at zero has no estimated directional difference under that figure's definition.

The scientific meaning of “positive” is different in each figure, so the x-axis label must always be read.

### 6.2 Point ordering

For Figures 05, 06, and 08, Phase 15 sorts the source rows by FDR and then by absolute effect size, keeps only a fixed number, and plots the first selected row at the bottom. Therefore, the displayed list is a selected top set, and the strongest-ranked row is generally near the bottom rather than the top.

Figure 04 does not apply this top-row selection; it plots all finite model effects in source-table order.

### 6.3 Shortened labels

Long contrast, pathway, and comparison names are shortened with `...` so the plot can fit on one page. The shortening is only visual. The complete identifiers remain in the source TSV files. The source table, not a shortened PDF label, should be used when copying an identifier into a report.

### 6.4 Donor counts

The meaning of `n` depends on the figure:

- `n=37/45 donors` means 37 donors on the contrast numerator side and 45 on the denominator side.
- `n=208 donors` in Figure 04 means 208 donor-level samples entered the complete fine-cell-type model; it is not a 208-versus-208 comparison.
- `paired tests=6` in Figure 08 is the number of matched cell-type/stratum state comparisons for that gene; it is not six donors.
- `donors 37/45` in Figure 10 means the simulation reproduced an AD/NCI donor layout of 37 and 45.

## 7. Figure 01: `01_cohort_flow.pdf`

### 7.1 Question answered

How did the project move from all donors represented in the master nucleus metadata to the frozen analytic cohort?

### 7.2 Source

```text
results/minerva_production/02_cohort/cohort_exclusion_flow.tsv
```

### 7.3 How the figure is built

Each blue bar is the number of donors remaining after a cumulative filtering step. The number above the bar is the exact count. The x-axis label gives the rule applied at that step.

The production flow is:

| Step | Rule | Before | Excluded at this step | Remaining |
|---:|---|---:|---:|---:|
| 1 | Represented in master cell metadata | 427 | 0 | 427 |
| 2 | Retain NCI or AD | 427 | 137 | 290 |
| 3 | Exclude prespecified sex-discordant donors | 290 | 3 | 287 |
| 4 | Exclude APOE e2/e4 | 287 | 8 | 279 |
| 5 | Require an APOE genotype | 279 | 2 | 277 |
| 6 | Require PMI | 277 | 1 | 276 |
| 7 | Require age at death and valid sex | 276 | 0 | 276 |

### 7.4 How to interpret it

The bars show a cumulative total, not the number excluded. For example, the second bar's height of 290 means that 290 donors remain after restricting diagnosis to NCI or AD. The number excluded by that rule is 137.

“Require PMI” means that the donor must have a recorded postmortem interval: the time from death until the tissue was preserved or collected. PMI can affect RNA quality and measured expression, so it is later used as a covariate.

### 7.5 What it does not show

- It does not show nuclei counts.
- It does not show how many donors are available in each fine cell type.
- It does not prove that included and excluded donors are biologically equivalent.
- The initial 427 are donors represented in the available cell metadata, not every person ever enrolled in ROSMAP.

## 8. Figure 02: `02_group_coverage.pdf`

### 8.1 Question answered

How many donors are represented for each combination of fine cell type, diagnosis, sex, and APOE group?

### 8.2 Sources

The figure combines the nine Phase 06 files named:

```text
results/minerva_production/06_descriptive/<rds_id>_group_coverage.tsv
```

### 8.3 Layout

- Rows are the 54 fine cell types.
- Columns are the 12 diagnosis-sex-APOE groups:

  ```text
  2 diagnoses x 2 sexes x 3 APOE groups = 12 groups
  ```

- Columns are ordered by sex, then APOE, with AD and NCI adjacent within
  every matched sex/APOE pair:

  ```text
  Female e2:  AD, NCI
  Female e33: AD, NCI
  Female e4:  AD, NCI
  Male e2:    AD, NCI
  Male e33:   AD, NCI
  Male e4:    AD, NCI
  ```

- Every tile contains the exact number of donors.
- Pale blue means fewer donors; dark blue means more donors.

The production matrix has:

```text
54 fine cell types x 12 groups = 648 tiles
```

Tile counts range from 0 to 53 donors. The only zero tile is:

```text
Fib SLC4A4 | AD | Male | e2 = 0 donors
```

The e2 groups generally have fewer donors than e33 groups. For example, across fine cell types, female-AD-e2 coverage ranges from 3 to 8 donors, while female-AD-e33 ranges from 9 to 37.

### 8.4 How to interpret it

This is primarily a study-design and power map.

- Darker tiles indicate more donor replication.
- Very small tiles warn that estimates may be imprecise or that a planned contrast may be ineligible.
- A zero means that the exact group-cell-type combination cannot be compared.

The plot is not a gene-expression heat map. A dark tile does not mean high expression or strong disease biology; it only means more donors were represented.

### 8.5 Important counting rule

One donor can appear in many fine cell types. Therefore, tile counts must not be added to estimate the number of unique people. The same person may contribute an astrocyte pseudobulk, an oligodendrocyte pseudobulk, and multiple neuronal pseudobulks.

Coverage also is not identical to final contrast eligibility. Phase 07 requires a primary-eligible donor pseudobulk to contain at least 20 nuclei, and each required group needs at least five eligible donors. Consult the contrast manifest for the final eligibility decision.

## 9. Figure 03: `03_mitochondrial_summary.pdf`

### 9.1 Question answered

Within each fine cell type, what distribution of donor-level mitochondrial RNA percentages is observed in AD and NCI?

### 9.2 Sources

The figure combines the nine files:

```text
results/minerva_production/04_qc/<rds_id>_donor_celltype_qc.tsv
```

### 9.3 Quantity on the y-axis

For one donor and one fine cell type:

```text
aggregate percent mitochondrial
    = 100 x sum of UMI counts from the 13 mtDNA protein-coding genes
            -------------------------------------------------------
                    sum of all RNA UMI counts
```

Counts are first summed across all of that donor's cohort-included nuclei in the fine cell type. This is why the value is donor-level and “aggregate.” It is not the simple average of nucleus-level percentages.

### 9.4 Box-plot anatomy

There is one pale-blue box for each fine-cell-type/diagnosis combination.

- The thick line inside a box is the median.
- The bottom and top of the box are the 25th and 75th percentiles.
- The box therefore contains the middle 50% of donor values.
- The whiskers extend toward values within the usual 1.5-interquartile-range rule.
- Outlier points are hidden with `outline = FALSE` to keep the dense figure readable. They were not removed from the upstream table.
- The x-axis label includes the number of donors contributing to the box.

The production input contains 13,886 donor-fine-cell-type rows, 54 fine cell types, and 108 AD/NCI boxes. Box sizes range from 38 to 142 donors. Observed aggregate percentages range from 0% to approximately 14.09%.

### 9.5 How to interpret it

Compare the AD and NCI boxes for the same fine cell type. A higher AD median means the unadjusted donor-level mitochondrial fraction is descriptively higher in AD for that cell type.

However, Figure 03 is not an adjusted disease test. It does not account for age, PMI, sex, or APOE and shows no confidence interval for an AD-NCI effect. Use Figure 04 and its source model tables for inferential statements.

A high mitochondrial RNA percentage is also biologically ambiguous. It can reflect cell stress or RNA quality, but it can also reflect real cell-type metabolism. The figure alone cannot identify the cause.

## 10. Figure 04: `04_mitochondrial_fraction_effects.pdf`

### 10.1 Question answered

After adjusting for age at death and PMI, do donor-level mitochondrial RNA fractions differ for the planned AD, sex, and APOE contrasts within each fine cell type?

### 10.2 Sources

The figure combines:

```text
results/minerva_production/09_downstream/<rds_id>.mito_fraction_models.tsv
```

### 10.3 Model behind each point

For one donor and fine cell type, Phase 09 supplies two counts:

```text
mitochondrial count     = combined UMI count from 13 mtDNA genes
non-mitochondrial count = total UMI count - mitochondrial count
```

It fits a donor-level quasibinomial logistic model equivalent to:

```text
~ 0 + diagnosis-sex-APOE group + scaled age at death + scaled PMI
```

The quasibinomial method allows more donor-to-donor variability than a simple binomial model.

### 10.4 What is plotted

Phase 15 plots every row with a finite `effect_size`. In the current production output this is 386 points:

- 376 single-degree-of-freedom effects; and
- 10 multi-degree-of-freedom global heterogeneity effects.

The effect range is approximately -0.881 to 1.314.

For a single-degree-of-freedom test:

- the point is the log odds ratio;
- the horizontal line is the 95% confidence interval;
- zero means an odds ratio of one;
- a direct AD-versus-NCI point to the right means higher adjusted mitochondrial odds in AD; and
- a direct point to the left means lower adjusted mitochondrial odds in AD.

The odds ratio is:

```text
odds ratio = exp(log odds ratio)
```

An odds ratio is not a percentage-point difference. For example, an odds ratio of 1.5 means the odds are multiplied by 1.5; it does not mean the mitochondrial fraction rises by 50 percentage points.

For an interaction contrast, the sign describes a difference between AD effects. For example:

```text
(AD - NCI in Female e33) - (AD - NCI in Male e33)
```

A negative result means the modeled AD effect is more negative, or less positive, in female e33 than in male e33. It does not simply mean females have a lower mitochondrial percentage.

### 10.5 Global heterogeneity points require special care

The global test asks whether the six sex-APOE-specific AD effects are all equal. It has no single signed log odds ratio.

For these rows:

- `effect_type` is `maximum_absolute_log_odds_heterogeneity`;
- the point is the largest absolute component difference;
- the confidence interval is absent; and
- direction must be interpreted from the component contrasts, not from the positive x-position.

Although the shared x-axis says “Log odds ratio,” a multi-df global point is not a signed log odds ratio. Always check `contrast_kind` and `effect_type` in the TSV before describing one of those points.

### 10.6 Colors

- Red: `fdr_bh_mito_fraction_family < 0.05`.
- Blue: the Phase 09 mitochondrial-fraction family FDR is at least 0.05 or unavailable.

The production plot contains 10 red rows. All 10 are in `excitatory_set3`; nine are single-df contrasts and one is the global heterogeneity test. The remaining finite rows are blue.

### 10.7 Donor label

The label `n=<number> donors` is `model_donors`: the number of donor pseudobulks used to fit the complete fine-cell-type model. It is not the number on each side of a particular contrast. For side-specific counts, use the Phase 07 contrast manifest.

### 10.8 How to read one single-df row

1. Identify the fine cell type and contrast.
2. Confirm that `contrast_kind = single_df`.
3. Look at the point's sign and size.
4. Check whether its confidence interval crosses zero.
5. Use the color and exact TSV FDR, not only the raw p-value.
6. Read `model_donors`, and consult the contrast manifest for numerator/denominator donor counts.

The complete fraction-model explanation is in [phase_09_explained.md](phase_09_explained.md).

## 11. Figure 05: `05_mtdna_gene_effects.pdf`

### 11.1 Question answered

Which individual mtDNA protein-coding gene tests have the strongest FDR-ranked effects across the final pseudobulk and MAST results?

### 11.2 Source

```text
results/minerva_production/11_multiple_testing/gene_multiple_testing.tsv.gz
```

This Phase 11 file combines the Phase 07 pseudobulk and Phase 08 MAST branches and adds broader multiple-testing corrections.

### 11.3 Selection rule

Phase 15:

1. keeps rows marked as one of the 13 mtDNA protein-coding genes;
2. requires a finite `logFC`;
3. requires finite numerator and denominator donor counts from the contrast manifest;
4. sorts by `fdr_bh_mtdna_global`, with within-contrast FDR as a fallback if the global value is unavailable;
5. breaks ties by larger absolute log2 fold change; and
6. displays only the first 40 rows.

Therefore, this PDF is not a complete mtDNA result table. It is a 40-row overview. Absence from the PDF does not mean a gene was not tested.

### 11.4 Labels

Each label contains:

```text
method | fine cell type | gene | contrast | n=numerator/denominator donors
```

For example:

```text
mast | Oli | MT-ATP6 | AD_vs_NCI__Male__e2 | n=7/6 donors
```

means that the displayed row came from the MAST branch, concerns MT-ATP6 in oligodendrocytes, compares male-e2 AD with male-e2 NCI, and has 7 versus 6 eligible donors represented by the contrast.

### 11.5 X-axis

The x-axis is log2 fold change.

For a direct AD-versus-NCI contrast:

- `logFC > 0`: expression is estimated to be higher in AD;
- `logFC < 0`: expression is estimated to be lower in AD;
- `logFC = 1`: approximately a two-fold increase; and
- `logFC = -1`: approximately a two-fold decrease.

The fold-change conversion is:

```text
fold change = 2^(log2 fold change)
```

### 11.6 Colors

- Red: the plotted FDR is below 0.05.
- Blue: it is not below 0.05.

For mtDNA genes, the main plotted correction is performed separately within each method branch across all mtDNA gene tests, cell types, and contrasts. This is broader than a within-contrast correction. The current production top-40 points are red.

### 11.7 Pseudobulk and MAST are not interchangeable

- `pseudobulk` is the donor-level primary differential-expression branch.
- `mast` is the paper-comparability, nucleus-level secondary branch.

Both report a quantity called `logFC`, but their statistical models and observation structures differ. Compare direction and supporting evidence; do not treat their effect estimates as if they were repeated measurements from one model.

The PDF does not draw confidence intervals. A point far from zero can still be uncertain. Use the Phase 11 table and the original Phase 07 or Phase 08 results for exact p-values, FDRs, and diagnostics.

## 12. Figure 06: `06_pathway_effects.pdf`

### 12.1 Question answered

Which mitochondrial pathways show the strongest collective shift in gene-ranking scores?

### 12.2 Source

```text
results/minerva_production/11_multiple_testing/pathway_multiple_testing.tsv.gz
```

### 12.3 How pathway evidence is formed

Phase 09 first gives every tested gene a signed ranking score.

- In the pseudobulk branch, the sign comes from logFC and the magnitude is based on the edgeR quasi-likelihood statistic.
- In the MAST branch, the sign comes from logFC and the magnitude is based on the MAST p-value transformed to a signed normal-score scale.

For one pathway, Phase 09 compares the ranking scores of genes inside the pathway with scores of eligible tested genes outside the pathway. The plotted effect is:

```text
rank_mean_difference
    = mean rank score of pathway genes
      - mean rank score of complement genes
```

### 12.4 X-axis

- Positive: pathway genes tend to have more positive differential-expression evidence than the background complement.
- Negative: pathway genes tend to have more negative evidence.
- Zero: no mean ranked shift.

This number is not a log fold change and not an average expression level. The pseudobulk and MAST ranking scales are constructed differently, so their numerical effect sizes should not be compared as though they share one physical unit.

### 12.5 Selection and labels

Phase 15:

1. keeps `terminal_status = validated_complete`;
2. requires a finite `rank_mean_difference`;
3. requires resolved numerator/denominator donor counts;
4. sorts by Phase 11 global rank FDR and then absolute rank difference; and
5. displays the first 35 rows.

Each label shows:

```text
method | fine cell type | pathway | n=numerator/denominator donors
```

The current production top 35 contain both pseudobulk and MAST rows and are dominated by the `OXPHOS` and `OXPHOS subunits` pathway definitions.

### 12.6 Colors

- Red: `rank_fdr_bh_global_branch < 0.05`.
- Green: global branch rank FDR is at least 0.05.

The correction is performed across all eligible ranked-pathway tests, cell types, and contrasts separately for each method branch. The current production top-35 points are red.

### 12.7 What not to conclude

- A positive point does not mean every pathway gene increased.
- A negative point does not mean the pathway has stopped functioning.
- A pathway effect is not direct evidence of ATP production or mitochondrial health.
- The PDF shows the ranked-distribution test, not the separate over-representation-analysis odds ratio.
- No confidence interval is drawn in this summary PDF.

Use the Phase 11 table and the detailed pathway columns described in [phase_09_explained.md](phase_09_explained.md) for a complete interpretation.

## 13. Figure 07: `07_mitonuclear_balance.pdf`

### 13.1 Question answered

How does donor-level expression from mtDNA-encoded OXPHOS genes compare with expression from nuclear-encoded OXPHOS genes across fine cell types and diagnoses?

### 13.2 Sources

The figure combines:

```text
results/minerva_production/09_downstream/<rds_id>.mitonuclear_balance.tsv
```

### 13.3 Exact balance formula

For each primary-eligible donor pseudobulk and fine cell type:

```text
mt average = mtDNA OXPHOS UMI / number of measured mtDNA OXPHOS genes

nuclear average = nuclear OXPHOS UMI / number of measured nuclear OXPHOS genes

balance = log2((mt average + 0.5) / (nuclear average + 0.5))
```

The 0.5 values are pseudocounts that prevent division by zero and stabilize extremely small counts.

Dividing by measured gene count is important because the nuclear OXPHOS set is much larger than the 13 mtDNA protein-coding genes.

### 13.4 How to interpret the y-axis

- `balance = 0`: equal pseudocount-adjusted UMI per measured gene in the two sets.
- `balance = 1`: the mtDNA value is approximately twice the nuclear value.
- `balance = -1`: the mtDNA value is approximately half the nuclear value.
- A value of 6 corresponds to an approximate ratio of `2^6 = 64` on this normalized scale.

This is an RNA-expression balance, not a direct measurement of protein abundance, respiratory-chain assembly, ATP production, or mitochondrial function.

### 13.5 Box plots and production coverage

The box-plot anatomy is the same as Figure 03. Green boxes summarize donors, labels report donor counts, and outlier points are hidden but not removed from the source table.

The production input has:

- 8,269 primary-eligible donor-fine-cell-type rows;
- 54 fine cell types;
- 106 represented fine-cell-type/diagnosis boxes;
- 1 to 142 donors per box; and
- balance values from approximately 0.294 to 8.876.

Two possible diagnosis boxes are absent because no primary-eligible balance row exists for those combinations:

```text
Inh L1-2 PAX6 SCGN | AD
Inh L6 SST NPY     | NCI
```

### 13.6 How to use the figure

Compare AD and NCI boxes within the same fine cell type. Do not compare raw heights across unrelated cell types without considering cell-type biology and coverage.

This is descriptive. It does not adjust for age, PMI, sex, or APOE and does not test an AD contrast. A one-donor box is a single observed value, not a stable population distribution.

## 14. Figure 08: `08_similarity.pdf`

### 14.1 Question answered

For each MitoCarta gene, are the directions of significant AD-versus-NCI changes similar or different between two sex or APOE settings?

### 14.2 Source

```text
results/minerva_production/11_multiple_testing/similarity_multiple_testing.tsv.gz
```

Phase 10 creates the similarity results, and Phase 11 adds the broader FDR used for Figure 08.

### 14.3 From differential-expression rows to three states

For a gene in each matched cell-type/stratum dimension, Phase 10 converts the AD-versus-NCI result to one of three states:

```text
+1 = significant positive AD effect
 0 = not called significantly changed
-1 = significant negative AD effect
```

For pseudobulk, “significant” means within-contrast FDR below 0.05 and absolute fold change above 1.3. For MAST, it uses the Phase 08 `paper_deg` rule.

The analysis then pairs states across definitions such as:

```text
female versus male within e2
female versus male within e33
e4 versus e33 within females
```

### 14.4 Exact similarity score

For the paired state values:

- same nonzero direction contributes `+1`;
- one significant and one unchanged contributes `-0.5`;
- opposite significant directions contributes `-1`; and
- both unchanged contributes `0`.

The contributions are added and divided by the number of paired tests:

```text
similarity = (same direction - 0.5 x one-sided changes - opposite directions)
             ----------------------------------------------------------------
                              number of paired tests
```

The score must be between -1 and +1.

- `+1`: every paired significant change agrees in direction.
- `-1`: every paired significant change points in the opposite direction.
- `0`: neutral overall under this scoring rule.

A score of zero can arise because both sides are unchanged, or because positive and negative contributions cancel. The component columns in the source table distinguish these cases.

### 14.5 Paired tests are not donors

`paired tests=6` means that six matched cell-type/stratum state pairs contributed to that gene's score. It does not mean six donors.

The title reports `eligible source contrasts: 5-53 donors per side`. This is the minimum-to-maximum donor range across all eligible source contrasts, not a row-specific donor count. The contrast manifest supplies exact donor counts for a particular source contrast.

### 14.6 Empirical significance

Phase 10 repeatedly permutes the second state vector, calculates a null similarity score, and obtains a directional empirical p-value. Phase 11 applies BH correction across all similarity genes and comparisons separately within each method branch.

Colors are:

- Red: `empirical_fdr_bh_global_method_branch < 0.05`.
- Purple: global similarity FDR is at least 0.05.

### 14.7 Selection and current production result

Phase 15 first restricts to MitoCarta genes with finite scores, sorts by global FDR and then absolute score, and displays the first 35 rows.

In the current production PDF:

- all 35 displayed points are purple, so none of the displayed rows passes the global 0.05 threshold;
- the visible selected rows come from the MAST branch;
- most compare female with male within e2, with one displayed e33 example; and
- paired-test counts are very small, from 1 to 10.

Several scores equal +1 or -1 because a score based on one or two paired tests can easily be extreme. An extreme score with very small `paired_tests` is not automatically strong evidence. The FDR and pairing components are essential.

## 15. Figure 09: `09_sensitivity.pdf`

### 15.1 Question answered

Which planned sensitivity or robustness branches completed, which were blocked, and how many result rows did each branch produce?

### 15.2 Source

```text
results/minerva_production/12_sensitivity/sensitivity_robustness.tsv
```

### 15.3 What each bar means

The bar height is `result_rows`. It is the number of output comparison rows produced by that sensitivity branch.

It is not:

- an effect size;
- a robustness score;
- the number of significant discoveries;
- a success percentage; or
- the number of donors.

The label includes the sensitivity ID, terminal status, and repetitions completed when repetitions are applicable.

### 15.4 Colors

- Green: `validated_complete`.
- Orange: `not_estimable`.
- Purple: `blocked_missing_input`.
- Red: `failed`.

The production result has seven completed branches and four branches blocked by missing inputs:

| Sensitivity | Status | Result rows | Repetitions |
|---|---|---:|---:|
| `pseudobulk_vs_mast` | validated complete | 695,393 | 0 |
| `global_vs_within_contrast_fdr` | validated complete | 1,082,689 | 0 |
| `flagged_nuclei_exclusion` | validated complete | 373 | 0 |
| `nuclei_minimum_50` | validated complete | 229 | 0 |
| `alternative_age_pmi_encoding` | validated complete | 386 | 0 |
| `leave_one_donor_out` | validated complete | 386 | 43 |
| `donor_bootstrap` | validated complete | 386 | 1,000 |
| `validated_batch_covariate` | blocked missing input | 0 | 0 |
| `normalization_sctransform` | blocked missing input | 0 | 0 |
| `per_object_vs_results_only_harmonization` | blocked missing input | 0 | 0 |
| `alternative_external_mitochondrial_sets` | blocked missing input | 0 | 0 |

The first two bars dominate the y-axis because they contain hundreds of thousands to more than one million rows. This makes the smaller completed branches look nearly flat even though they contain hundreds of results. Read the numbers above the bars or the TSV rather than judging only visual bar height.

A blocked branch is not a negative biological result. It means the required alternative input was not available under the frozen production analysis.

## 16. Figure 10: `10_power.pdf`

### 16.1 Question answered

Under simulated effects and donor layouts resembling selected real contrasts, how often do two analysis methods reject the null hypothesis?

### 16.2 Source

```text
results/minerva_production/13_power/power_results.tsv.gz
```

### 16.3 What a simulation means

Phase 13 selects representative fine cell types, genes, and contrasts from real pseudobulk data, estimates count and detection characteristics, and repeatedly creates artificial datasets with known AD effects.

Because the true simulated effect is known, the analysis can ask:

- when the true effect is zero, how often is there a false positive? and
- when the true effect is nonzero, how often is the effect detected?

The production run uses:

```text
6 scenarios
x 2 method branches
x 6 simulated effect sizes
x 100 repetitions
= 7,200 simulated fits
```

The effect grid is:

```text
0, 0.25, 0.3785116, 0.5, 0.75, 1.0 log2 units
```

A log2 effect of 1 is a two-fold AD/NCI change. A log2 effect of 0.5 is approximately a 1.41-fold change.

### 16.4 Panels

There are six panels:

| Scenario | Fine cell type | Gene | AD/NCI donors | Role/contrast |
|---:|---|---|---:|---|
| 1 | Inh L5-6 SST TH | MT-ND6 | 5/8 | rare; Female e33 |
| 2 | Inh L5-6 SST TH | MT-CO3 | 5/8 | rare; Female e33 |
| 3 | Oli | MT-ND6 | 7/6 | abundant; Male e2 |
| 4 | Oli | MT-CO2 | 7/6 | abundant; Male e2 |
| 5 | Oli | MT-ND6 | 37/45 | abundant; Female e33 |
| 6 | Oli | MT-CO2 | 37/45 | abundant; Female e33 |

“Rare” means the selected eligible fine cell type had the fewest analytic nuclei among eligible types. “Abundant” means it had the most. The selected genes represent relatively low and high detection, and the selected contrasts include limiting and better-powered donor layouts.

### 16.5 Axes and lines

- The x-axis is the true simulated log2 AD effect.
- At x = 0, the y-value is the false-positive rate.
- At x > 0, the y-value is power.
- The dashed horizontal line is the target power of 0.80.
- Blue is `pseudobulk_edgeR_known_dispersion`.
- Red is `paper_like_mast_hurdle`.

The blue method fits donor-level pseudobulk counts with edgeR using the scenario's estimated donor dispersion.

The red method is a simplified paper-like hurdle benchmark, not the complete production MAST implementation. It combines a detection-proportion test with a model of positive nucleus values. It treats large numbers of nucleus-level observations as the evidence base and does not implement donor clustering in the same way as pseudobulk.

### 16.6 How to read power correctly

At a nonzero effect, a higher curve means more simulations detected the planted effect. Larger donor groups generally give greater power. For example, the 37/45-donor oligodendrocyte pseudobulk scenarios reach the 0.80 target around a log2 effect of 0.5, while several 5/8- or 7/6-donor pseudobulk scenarios do not reach 0.80 anywhere in the tested grid.

However, power is meaningful only if the method controls false positives when the true effect is zero.

The nominal false-positive target is 0.05. Production zero-effect rates are:

| Scenario | Pseudobulk edgeR | Paper-like hurdle |
|---:|---:|---:|
| 1 | 0.01 | 0.06 |
| 2 | 0.06 | 0.46 |
| 3 | 0.03 | 0.61 |
| 4 | 0.03 | 0.83 |
| 5 | 0.00 | 0.50 |
| 6 | 0.03 | 0.76 |

Except for scenario 1, the red method has severely inflated false-positive rates. Therefore, its high red “power” values must not be celebrated as superior detection. A method that calls many null simulations significant will also appear to detect many nonzero simulations. The figure is showing an anti-conservative benchmark in those scenarios.

The dashed 0.80 line is a power target for nonzero effects. It is not a desired false-positive rate at x = 0. At zero, a well-calibrated point should be near 0.05, far below the dashed line.

### 16.7 Monte Carlo uncertainty

Each point is based on only 100 repetitions. A plotted value such as 0.80 means 80 of 100 simulations rejected the null. Repeating the entire experiment would not produce exactly the same proportion. The source table contains a Monte Carlo standard error.

These are representative scenarios, not a promise of identical power for all 54 cell types, every gene, or every contrast.

## 17. The four supporting TSV files

Phase 15 produces four machine-readable files in addition to the ten PDFs.

### 17.1 `figure_manifest.tsv`

There is one row per planned figure.

| Column | Meaning |
|---|---|
| `schema_version` | Table format version, currently `figure_manifest_v1`. |
| `execution_stage` | `local_pilot` or `minerva_production`. |
| `output_status` | `nonfinal_smoke_test` for pilot or `final` for production. |
| `figure_id` | Stable figure name without `.pdf`. |
| `title` | Human-readable figure title. |
| `path` | Project-relative PDF path. |
| `render_status` | `validated_complete`, `not_estimable`, or `failed`. |
| `message` | Empty on success; reason for not-estimable or failed output otherwise. |
| `source_paths` | Semicolon-separated upstream table paths used for the figure. |
| `inferential` | Whether the plot presents a statistical inference or simulation-based inferential diagnostic. |
| `donor_counts_displayed` | Whether donor-based sample-size information is displayed. |
| `sample_size_unit` | `donor`, `donor_or_result_row`, or `simulated_donor`. |
| `bytes` | PDF file size in bytes. |
| `sha256` | SHA-256 checksum of the PDF. |

This is the best starting point for answering, “Which table produced this figure?”

### 17.2 `figure_checks.tsv`

There is one row per validation check.

| Column | Meaning |
|---|---|
| `schema_version` | `figure_checks_v1`. |
| `check` | Stable check name. |
| `passed` | `TRUE` or `FALSE`. |
| `observed` | What Phase 15 actually found. |
| `expected` | Required value or condition. |

The ten checks verify:

1. Phase 14 was validated;
2. every planned figure has a manifest row;
3. every figure has a terminal status;
4. all expected PDF files exist;
5. all PDFs are nonempty;
6. all PDF checksums are recorded;
7. inferential figures display donor information;
8. nuclei are not presented as the inferential sample-size unit;
9. execution-stage and output-status fields in the manifest match the configured scope; and
10. upstream input files remained unchanged while plotting.

### 17.3 `figure_artifacts.tsv`

This is the file inventory for the ten PDFs plus `figure_manifest.tsv` and `figure_checks.tsv`.

| Column | Meaning |
|---|---|
| `schema_version` | `figure_artifacts_v1`. |
| `artifact` | Basename of the artifact. |
| `path` | Project-relative path. |
| `bytes` | File size. |
| `sha256` | File checksum. |
| `records` | Row count for TSV artifacts; `NA` for PDFs. |
| `validation_status` | Overall Phase 15 validation status assigned to the artifact. |

`figure_artifacts.tsv` does not list itself or `figure_status.tsv`, because it is created before the final status is written.

### 17.4 `figure_status.tsv`

This file has exactly one row summarizing the task.

| Column | Meaning |
|---|---|
| `schema_version` | `figures_status_v1`. |
| `execution_stage` | Pilot or production stage. |
| `execution_phase` | Legacy numeric execution-scope label stored by the execution config. It is not Scientific Phase 15. |
| `backend` | Execution backend, such as `direct`. |
| `run_id` | Identifier for the configured run. |
| `stable_task_id` | `global:figures`. |
| `source_rds` | Semicolon-separated RDS IDs represented by the input tables. |
| `scientific_script` | Plotting script path. |
| `scientific_code_bundle_sha256` | Checksum of the plotting script. |
| `scientific_config_sha256` | Checksum of the scientific analysis configuration. |
| `rds_manifest_sha256` | Checksum of the RDS manifest. |
| `upstream_input_bundle_sha256` | Combined checksum identity for all figure inputs. |
| `output_status` | `final` or `nonfinal_smoke_test`. |
| `planned_figures` | Number of figures expected. |
| `rendered_figures` | Number rendered successfully. |
| `not_estimable_figures` | Number replaced by explicit not-estimable pages. |
| `failed_figures` | Number that failed during rendering. |
| `inferential_figures` | Number classified as inferential. |
| `inferential_figures_with_donor_counts` | Inferential figures satisfying the donor-count display rule. |
| `peak_ram_gib` | Approximate peak memory used by Phase 15. |
| `elapsed_seconds` | Task runtime. |
| `validation_status` | `validated_complete` or `failed`. |
| `failed_checks` | Semicolon-separated failed check names; empty on success. |
| `git_revision` | Git revision recorded at execution time. |
| `timestamp_utc` | Completion time in UTC. |

## 18. Current Minerva production snapshot

The checked production status reports:

```text
planned figures:                         10
rendered figures:                        10
not-estimable figures:                    0
failed figures:                           0
inferential figures:                      5
inferential figures with donor counts:    5
validation status:       validated_complete
peak RAM:                     about 6.26 GiB
elapsed time:                about 59.5 sec
```

All ten rows in `figure_checks.tsv` pass. The source RDS list contains all nine production RDS IDs.

“Rendered successfully” means that the PDF exists, is nonempty, has a checksum, and passed the Phase 15 bookkeeping checks. It does not mean every point in the PDF is statistically significant or biologically correct. Scientific interpretation still depends on the upstream model, assumptions, FDR family, donor coverage, and diagnostics.

## 19. How to inspect a result responsibly

Use this order:

1. Check `figure_manifest.tsv` or `figure_status.tsv` for the execution stage and
   output status. The PDFs intentionally use stage-neutral titles and do not
   display a stage stamp. Do not present a local-pilot figure as a final result.
2. Identify whether the figure is descriptive or inferential.
3. Read the x- and y-axis units.
4. Read donor counts and note small or unbalanced groups.
5. For a colored inferential point, identify the exact FDR family described above.
6. Locate the complete row in the source TSV. Do not rely on a shortened PDF label.
7. Check the relevant upstream status and diagnostic files.
8. Compare pseudobulk and MAST as separate branches.
9. Distinguish “not significant” from “no biological effect.” Limited donor coverage can produce low power.
10. Do not infer mechanism or causality from an association plot alone.

## 20. Running Phase 15

### 20.1 Local pilot

```bash
Rscript scripts/run_pipeline.R \
  --config config/local_pilot.yml \
  --execution-config config/local_pilot_execution.yml \
  --phase figures
```

Expected output:

```text
results/local_pilot/15_figures/
```

The pilot PDFs use the same stage-neutral titles as production. Their
`figure_manifest.tsv` and `figure_status.tsv` records must be labeled
`local_pilot` and `nonfinal_smoke_test`.

### 20.2 Minerva production

After the Minerva shell environment has been initialized as documented in the research plan:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase figures
```

Expected output:

```text
results/minerva_production/15_figures/
```

The final check is:

```bash
Rscript -e '
status <- read.delim(
  "results/minerva_production/15_figures/figure_status.tsv",
  check.names = FALSE
)
print(status[, c(
  "planned_figures", "rendered_figures", "not_estimable_figures",
  "failed_figures", "inferential_figures",
  "inferential_figures_with_donor_counts", "validation_status"
)])
stopifnot(
  nrow(status) == 1L,
  status$validation_status == "validated_complete",
  status$failed_figures == 0L,
  status$rendered_figures + status$not_estimable_figures == status$planned_figures,
  status$inferential_figures_with_donor_counts == status$inferential_figures
)
'
```

## 21. Short summary

Phase 15 is a validated rendering and provenance layer over results from Phases 02 through 13. Its ten figures cover cohort construction, donor coverage, mitochondrial fractions, mtDNA genes, pathways, mitonuclear balance, cross-group similarity, robustness execution, and simulated power. The PDFs are useful summaries, but the source TSV files remain the authoritative place for exact identifiers, model fields, FDR values, diagnostics, and complete result sets.
