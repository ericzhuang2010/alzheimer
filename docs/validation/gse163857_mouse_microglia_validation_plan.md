# GSE163857 Mouse Microglia Validation Plan

Date searched and metadata verified: August 19, 2026

## Purpose

This document describes how to use [GSE163857](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163857) as an external mouse validation dataset for the human ROSMAP sex × APOE × Alzheimer’s disease microglial findings in this repository.

GSE163857 should be used to validate **microglial** findings only. It cannot validate findings from neurons, astrocytes, oligodendrocytes, OPCs, or vascular cells.

## Executive summary: what to compare

GSE163857 is bulk RNA-seq of whole-brain, MACS-isolated CD11b-positive microglia from individual mice. It does **not** contain resolved microglial fine-cell types. Each of its 30 mouse columns is one average expression profile from all isolated microglia in one mouse.

The corresponding human ROSMAP populations are the three microglial fine-cell types in `Immune_cells.rds`:

- `Mic P2RY12`
- `Mic TPT1`
- `Mic MKI67`

The primary comparison should evaluate the mouse bulk result against each of these human fine-cell types separately. A combined donor-level human microglial pseudobulk across all three populations should be added as the closest bulk-to-bulk comparison.

Do **not** include `CAMs` or `T cells` in the primary comparison. They are separate immune populations and are not the intended target of the purified mouse-microglia experiment.

```text
GSE163857 mouse data
one bulk microglial profile per mouse
                 |
                 +--> Human Mic P2RY12 results
                 +--> Human Mic TPT1 results
                 +--> Human Mic MKI67 results
                 `--> Combined human microglial pseudobulk

Do not include CAMs or T cells in the primary comparison.
```

## Direct mouse-to-human comparison plan

| Mouse comparison in GSE163857 | Human ROSMAP comparison | Interpretation |
|---|---|---|
| Overall 5xFAD versus control, adjusted for sex and APOE | Overall AD versus NCI in each microglial fine type and in combined microglia | General disease-associated microglial concordance |
| Female APOE3: 5xFAD versus control | Female APOE3/3: AD versus NCI | Female APOE3 disease response |
| Male APOE3: 5xFAD versus control | Male APOE3/3: AD versus NCI | Male APOE3 disease response; the mouse estimate is especially weak because there is one control mouse |
| Female APOE4: 5xFAD versus control | Female APOE4 group: AD versus NCI | Female APOE4 disease response |
| Male APOE4: 5xFAD versus control | Male APOE4 group: AD versus NCI | Male APOE4 disease response |
| APOE4 versus APOE3 within female 5xFAD mice | APOE4 versus APOE3/3 within female AD donors, if estimable | APOE effect within disease |
| APOE4 versus APOE3 within male 5xFAD mice | APOE4 versus APOE3/3 within male AD donors, if estimable | APOE effect within disease |
| Sex-by-APOE interaction within 5xFAD mice | Sex-by-APOE pattern in human AD microglia | Whether the APOE effect differs by sex |

The mouse groups are homozygous APOE3/E3 and APOE4/E4. If the human APOE4 group includes heterozygous carriers, the comparison is a direction-of-effect validation rather than an exact genotype-dose replication.

## Validation endpoints

The cross-species comparison should emphasize:

1. Direction of differential expression for mapped one-to-one orthologs.
2. Effect-size concordance, with confidence intervals.
3. Enrichment of human microglial DEG signatures in ranked mouse results.
4. The four frozen mitochondrial programs used in this repository.
5. Results shared across human microglial fine types versus results localized to one fine type.

Raw expression magnitudes should not be compared directly between species. Mouse and human effects should be estimated separately and then compared using direction, standardized magnitude, gene-set enrichment, and rank concordance.

## 1. Dataset design

GSE163857 contains bulk RNA-seq profiles from mice carrying human APOE3 or APOE4 on either a targeted-replacement control background or a 5xFAD background. Both sexes are represented. The associated study is [Moser et al., 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8551075/).

The mouse experiment contains:

- 30 individual mice and 30 bulk RNA-seq libraries.
- 54,281 gene rows in the processed mouse matrix.
- Homozygous human APOE3/E3 or APOE4/E4 targeted replacement.
- Female and male mice.
- Non-5xFAD targeted-replacement controls and 5xFAD mice.
- Ages from 7.55 to 9 months.
- Whole-brain CD11b-positive cells isolated by magnetic sorting, or MACS.
- One reported sequencing batch for all mouse samples.

The mice were perfused before microglial isolation to reduce contamination from circulating blood cells. The paper reports strong microglial-marker expression and low neuronal and astrocytic marker expression in the isolated population.

### Genetic backgrounds

The APOE replacement and 5xFAD transgenes are separate genetic modifications:

```text
Human APOE targeted replacement
    supplies human APOE3 or APOE4

5xFAD transgenes
    supply the aggressive amyloid-disease background
```

The control mice express human APOE3 or APOE4 but do not carry the 5xFAD transgenes. The 5xFAD mice express the same human APOE alleles while also carrying mutant human `APP` and `PSEN1` transgenes that drive rapid amyloid pathology.

## 2. Why the mouse data have no fine-cell labels

Microglia were isolated first, and RNA from many isolated cells was then measured together. The resulting measurement is an average across all microglia collected from one mouse.

GSE163857 therefore cannot determine:

- Whether an effect originates from a `P2RY12`-like, `TPT1`-like, or proliferating `MKI67`-like state.
- The proportion of different microglial states in each mouse.
- Whether an observed bulk change reflects altered expression within cells, altered state composition, or both.

The human data retain this resolution. The [human immune-cell RDS summary](../rds_summaries/immune_cells_rds_summary.md) reports:

| Human fine-cell type | Nuclei | Donors represented |
|---|---:|---:|
| `Mic P2RY12` | 73,061 | 425 |
| `Mic TPT1` | 5,261 | 373 |
| `Mic MKI67` | 866 | 175 |

Because `Mic P2RY12` is much larger than the other populations, a combined human pseudobulk will be dominated by `Mic P2RY12`. Subtype-specific comparisons are therefore essential even if a combined pseudobulk is produced.

## 3. Human comparison analyses

### Analysis A: each microglial fine-cell type separately

Retain the existing donor-level analyses for:

- `Mic P2RY12`
- `Mic TPT1`
- `Mic MKI67`

For each fine-cell type, extract the same sex-, APOE-, and diagnosis-specific contrasts that can be matched to the mouse design. This identifies whether a mouse bulk signal is broadly reproduced or resembles one particular human microglial state.

### Analysis B: combined human-microglia pseudobulk

For each human donor:

1. Select nuclei labeled `Mic P2RY12`, `Mic TPT1`, or `Mic MKI67`.
2. Sum raw UMI counts across those nuclei gene by gene.
3. Keep one combined microglial count profile per donor.
4. Normalize and model the donor-level profiles using the same human covariate strategy used elsewhere in the repository.
5. Run the frozen sex-, APOE-, and diagnosis-specific contrasts.

Do not average already normalized cell-level expression values. Pseudobulk should begin by summing raw counts.

As a sensitivity analysis, calculate an equal-weight average of the three subtype-specific effect estimates or module scores. This prevents the much larger `Mic P2RY12` population from completely determining the combined result.

## 4. Mouse data download and reconstruction

### Processed count matrix

Download:

`GSE163857_Mouse_Microglia_counts.csv.gz`

The processed file contains gene-level Salmon/`tximport` expression estimates. Rows use versioned mouse Ensembl gene identifiers, and columns use sequencing filenames rather than simple animal identifiers.

“Processed” means the reads have already been quantified and summarized to genes. It does not mean the values are normalized or ready for differential-expression testing.

### Metadata table

Build one metadata row per count-matrix column with at least:

| Field | Example |
|---|---|
| `geo_accession` | `GSM4988799` |
| `count_column` | `F0_A9_S25_R1_001_merged.fastq.gz` |
| `animal_id` | `F0` |
| `sex` | Female |
| `apoe` | E3/E3 |
| `disease_background` | Control |
| `age_months` | 7.55 |
| `cell_source` | Whole-brain MACS CD11b-positive cells |
| `sequencing_batch` | Batch 1 |

The GEO MINiML/GSM records supply genotype, background, sex, cell source, and batch. Table S1 of the paper supplement supplies animal ages.

Verify that:

- All 30 count columns match exactly one metadata row.
- Every metadata row matches exactly one count column.
- There are no duplicated animal or library identifiers.
- Sex, APOE, disease background, and age are present for every mouse.
- Count-matrix order is explicitly aligned to metadata order.

## 5. Eight-group design and replicate counts

The nominal design is:

```text
2 sexes × 2 APOE genotypes × 2 disease backgrounds = 8 groups
```

The verified counts are:

| Sex | APOE | Background | Mice |
|---|---|---|---:|
| Female | E3/E3 | Control | 2 |
| Female | E3/E3 | 5xFAD | 5 |
| Female | E4/E4 | Control | 2 |
| Female | E4/E4 | 5xFAD | 5 |
| Male | E3/E3 | Control | **1** |
| Male | E3/E3 | 5xFAD | 7 |
| Male | E4/E4 | Control | 3 |
| Male | E4/E4 | 5xFAD | 5 |
| **Total** | | | **30** |

All eight cells are present, but the design is strongly unbalanced. In particular, the male E3/E3 control cell contains one mouse. A complete three-way interaction is algebraically estimable, but its uncertainty and sensitivity to individual mice will be substantial.

## 6. Mouse expression quality control

The biological replicate is the mouse, not an individual microglial cell or gene.

For each sample, inspect:

- Total estimated library counts.
- Number of detected genes.
- Mitochondrial read fraction as a QC measure.
- Sample-to-sample correlations.
- PCA and sample-distance plots.
- Outlier influence.

Confirm biological identity using:

- Microglial markers such as `P2ry12`, `Tmem119`, `Csf1r`, `Cx3cr1`, and `Aif1`.
- Low neuronal and astrocytic marker expression.
- `Xist` for female samples.
- `Kdm5d`, `Ddx3y`, and `Uty` for male samples.

Low-expression filtering should be fixed before testing. A reasonable starting rule is at least 10 estimated counts in at least three mice, followed by an explicit audit of mitochondrial-module coverage.

### Fractional count limitation

The processed matrix contains fractional Salmon/`tximport` count estimates. The original study used the complete Salmon/`tximport` output with DESeq2.

Options are:

- Use `edgeR`/`limma-voom` for a rapid analysis of the processed estimates.
- Round the estimates for DESeq2 only as a documented approximation.
- For publication-grade DESeq2 reproduction, download the SRA FASTQ files and rebuild the Salmon/`tximport` object with transcript-length offsets.

## 7. Recommended statistical hierarchy

The analyses should be prespecified and separated into primary, secondary, and exploratory tiers.

### Primary: sex-by-APOE within 5xFAD mice

The four 5xFAD groups have 5–7 mice each:

| 5xFAD group | Mice |
|---|---:|
| Female E3/E3 | 5 |
| Female E4/E4 | 5 |
| Male E3/E3 | 7 |
| Male E4/E4 | 5 |

Fit the FAD-only model:

```r
~ age + sex * APOE
```

This is the cleanest test of whether the APOE effect differs by sex in amyloid-model microglia.

### Secondary: overall 5xFAD effect

Fit an adjusted main-effect model across all mice:

```r
~ age + sex + APOE + disease
```

This estimates the average 5xFAD-versus-control microglial effect while adjusting for sex and APOE. It is more stable than eight separate disease contrasts, but it assumes the disease effect is reasonably similar across strata.

### Exploratory: complete three-way interaction

Fit:

```r
~ age + sex * APOE * disease
```

The three-way term asks whether the APOE modification of the 5xFAD effect differs by sex:

```text
Male:
  (E4 FAD - E4 control) - (E3 FAD - E3 control)

versus

Female:
  (E4 FAD - E4 control) - (E3 FAD - E3 control)
```

Because the male E3/E3 control cell has one mouse, this result must be labeled exploratory. Report effect sizes, confidence intervals, and leave-one-mouse-out sensitivity rather than relying on the interaction p-value alone.

### Gene-level outputs

For every prespecified contrast, save:

- Mouse Ensembl identifier and gene symbol.
- Mean normalized expression.
- Log2 fold change.
- Standard error and 95% confidence interval.
- Test statistic and raw p-value.
- Benjamini-Hochberg FDR.
- Model and contrast identifiers.

## 8. Mitochondrial module validation

Use the four frozen repository modules:

| Module | Human reference genes | Role |
|---|---:|---|
| mtDNA-encoded OXPHOS | 13 | Direct respiratory program |
| Nuclear-encoded structural OXPHOS | 86 | Direct respiratory program |
| Mitochondrial translation | 155 | Supporting maintenance program |
| MIB/MICOS inner membrane | 19 | Supporting membrane-organization program |

The frozen definitions are stored in [phase13_respiratory_modules.tsv](../../config/phase13_respiratory_modules.tsv) and explained in [four_respiratory_module_program.md](../deep_dive_research/four_respiratory_module_program.md).

### Ortholog mapping

1. Map every frozen human gene to a one-to-one mouse ortholog.
2. Match each mouse ortholog to the GRCm38/GENCODE M23 identifiers used by GSE163857.
3. Record missing, ambiguous, and filtered genes.
4. Freeze the admitted mouse gene lists before examining group differences.
5. Report module coverage explicitly.

### Two complementary module tests

**Ranked gene-set test:** Rank all genes by a signed differential-expression statistic and test whether a module is concentrated toward the positive or negative end.

**Mouse-level module score:** Normalize the mouse expression matrix, standardize admitted genes, calculate one module score per mouse, and fit the same primary, secondary, and exploratory models to those scores.

Mitochondrial read fraction remains a QC variable. It is not interchangeable with an OXPHOS module score.

## 9. Cross-species concordance analysis

For every matched contrast and microglial target, produce:

- Ortholog-level mouse and human log2 fold changes.
- Pearson and Spearman effect-size correlations where enough genes are available.
- Directional sign agreement.
- Overlap and enrichment of significant or top-ranked genes.
- Four-module direction, effect size, confidence interval, and FDR.
- Results for each human microglial fine type and combined microglia.

Example interpretation:

```text
Human female APOE4 Mic P2RY12:
AD versus NCI nuclear OXPHOS effect is negative.

Mouse female APOE4 microglia:
5xFAD versus control nuclear OXPHOS effect is negative.

Interpretation:
directionally concordant cross-species evidence for a female APOE4
microglial nuclear-OXPHOS response.
```

A matching direction with compatible uncertainty supports validation. Different p-values across species do not by themselves indicate disagreement.

## 10. Permitted and non-permitted conclusions

### Defensible conclusions

- The mouse bulk-microglial effect is directionally concordant with one or more human microglial fine-cell types.
- A frozen mitochondrial program changes in the same direction in human and mouse microglia.
- APOE and sex modify microglial expression within the replicated 5xFAD groups.
- The combined human microglial result resembles the average mouse-microglial result.

### Conclusions to avoid

- GSE163857 identifies the responsible microglial fine-cell state.
- The mouse bulk sample is equivalent to human `Mic P2RY12`, `Mic TPT1`, or `Mic MKI67`.
- GSE163857 validates neuronal, astrocytic, oligodendrocytic, or vascular findings.
- A non-significant three-way interaction proves that no interaction exists.
- Mouse 5xFAD pathology is identical to human late-onset AD.

## 11. Recommended deliverables

1. Audited 30-row mouse metadata table.
2. Eight-group replicate-count and age table.
3. Mouse QC report and PCA.
4. Primary FAD-only sex-by-APOE differential-expression results.
5. Secondary overall 5xFAD-versus-control results.
6. Exploratory three-way interaction with influence diagnostics.
7. Mouse ortholog and mitochondrial-module coverage manifest.
8. Four-module result table.
9. Mouse-versus-human microglial concordance table.
10. Forest plot of matched mitochondrial-module effects.
11. Fine-cell-type heatmap showing which human microglial population best matches the mouse bulk signal.

## Final recommendation

Use GSE163857 as an external validation dataset for microglial findings only. Compare its bulk mouse effects with the three human microglial fine-cell types separately and with a combined donor-level human microglial pseudobulk. Prioritize sex-by-APOE effects within the well-replicated 5xFAD groups, use the overall disease effect as secondary evidence, and label the complete three-way interaction exploratory because the control groups are sparse.
