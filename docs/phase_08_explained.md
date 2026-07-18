# Analyzing Phase 08 MAST Results

## Purpose

Phase 08 performs the secondary, paper-comparable cell-level differential-expression analysis using MAST. Within each eligible high-resolution cell type and sex-APOE group, it compares Alzheimer disease (`AD`) nuclei with no cognitive impairment (`NCI`) nuclei.

- A positive `logFC` means that expression is higher in AD than NCI.
- A negative `logFC` means that expression is lower in AD than NCI.
- Phase 08 writes one row per tested gene and contrast, not only significant genes.

Because multiple nuclei can come from the same donor, Phase 08 is a secondary paper-comparable analysis. The donor-aware Phase 07 pseudobulk analysis remains the primary differential-expression analysis.

## Phase 08 DEG definition

The `paper_deg` column identifies genes that pass the paper-style reporting rule. A gene has `paper_deg == TRUE` when all the following conditions hold:

1. `fdr_bh_within_contrast < 0.05`;
2. `abs(logFC) > log2(1.3)`, approximately `0.3785`; and
3. the gene is detected in at least 10% of AD or NCI nuclei (`pct_ad >= 0.10` or `pct_nci >= 0.10`).

The Benjamini-Hochberg FDR is calculated separately within each fine-cell-type and sex-APOE AD-versus-NCI contrast.

## Output locations

Minerva production writes one result bundle per RDS under:

```text
results/minerva_production/08_mast/
```

The main gene-level result file is:

```text
results/minerva_production/08_mast/<rds_id>.mast_de.tsv.gz
```

Examples include:

```text
results/minerva_production/08_mast/astrocytes.mast_de.tsv.gz
results/minerva_production/08_mast/inhibitory.mast_de.tsv.gz
results/minerva_production/08_mast/vasculature.mast_de.tsv.gz
```

Each RDS also produces:

- `<rds_id>.mast_model_diagnostics.tsv`: model diagnostics;
- `<rds_id>.mast_contrast_status.tsv`: terminal status and sample sizes for every planned contrast;
- `<rds_id>.mast_de_checks.tsv`: validation checks;
- `<rds_id>.mast_de_artifacts.tsv`: artifact sizes and checksums; and
- `<rds_id>.mast_de_status.tsv`: overall scientific completion status and summary counts.

The main `.mast_de.tsv.gz` file is written atomically after the entire RDS task finishes. While an RDS is running, its log reports individual MAST fits, but its final gene table might not exist yet. A partial log does not mean the RDS task completed successfully.

## Important result columns

| Column | Meaning |
|---|---|
| `rds_id` | Broad source RDS identifier. |
| `cell_type_high_resolution` | Fine cell type analyzed. |
| `contrast_name` | Sex-APOE-specific AD-versus-NCI comparison. |
| `gene` | Tested gene symbol. |
| `logFC` | AD-versus-NCI log2 fold change; positive is higher in AD. |
| `pct_ad` | Fraction of AD nuclei in which the gene is detected. |
| `pct_nci` | Fraction of NCI nuclei in which the gene is detected. |
| `p_value` | Raw MAST p-value. |
| `fdr_bh_within_contrast` | Benjamini-Hochberg-adjusted p-value within the contrast. |
| `paper_deg` | Whether the gene passes the complete Phase 08 DEG rule. |
| `cells_ad`, `cells_nci` | Numbers of nuclei in the two sets being compared. |
| `donors_ad`, `donors_nci` | Numbers of represented donors in the two sets. |

## Detailed row definition for the compressed gene table

### The unit represented by one row

The unit of a `*.mast_de.tsv.gz` row is:

```text
one RDS + one fine cell type + one eligible sex-APOE AD-versus-NCI contrast + one tested gene
```

The unique scientific key is:

```text
cell_type_high_resolution + contrast_id + gene
```

The RDS is embedded in `contrast_id`. Phase 08 validation requires this key to
be unique.

A row is not a nucleus, a donor, a gene summarized across all cell types, or
necessarily a significant DEG. For example:

```text
cell_type_high_resolution = Ast CHI3L1
contrast_name              = AD_vs_NCI__Female__e33
gene                       = NTRK2
```

means that NTRK2 was tested by comparing AD nuclei with NCI nuclei among female
APOE-e33 donors, restricted to the `Ast CHI3L1` fine cell type in the
Astrocytes RDS.

The same gene can have many rows because it can be tested in six sex-APOE
groups, multiple fine cell types, and multiple RDS files. The number of rows is
therefore the number of gene tests, not the number of unique gene symbols.
Likewise, counting `paper_deg == TRUE` counts significant
gene-by-cell-type-by-contrast results, not unique DEGs.

### Which contrasts and genes produce rows

Phase 07 defines 14 contrast rows for each fine cell type:

- six paper-matched AD-versus-NCI comparisons: Female and Male crossed with
  APOE groups `e2`, `e33`, and `e4`;
- three sex-interaction contrasts;
- four APOE-interaction contrasts; and
- one global sex-APOE heterogeneity test.

Phase 08 fits only the six paper-matched comparisons. Interaction and omnibus
rows are primary pseudobulk tests; Phase 08 records them as `not_applicable` in
`mast_contrast_status.tsv` and writes no gene rows for them.

A paper comparison is eligible only if both its AD and NCI side contain at
least five primary-eligible donors. Ineligible comparisons are documented in
`mast_contrast_status.tsv` but do not appear in `mast_de.tsv.gz`.

For an eligible comparison, Phase 08 selects cohort-included nuclei from the
required fine cell type and eligible Phase 07 donors. The observed nucleus and
donor counts must agree with the Phase 07 sample and contrast manifests, and
the MAST covariates must be complete.

Seurat `FindMarkers` is then called with:

```text
ident.1         = AD
ident.2         = NCI
test.use        = MAST
slot            = data
min.pct         = 0.10
logfc.threshold = 0
latent.vars     = nCount_RNA;age_death_scaled;pmi_scaled
```

A gene receives a row if Seurat returns it after the detection filter: it must
be detected in at least 10% of AD or at least 10% of NCI nuclei. There is no
fold-change prefilter. A gene failing this detection rule has no row; a gene
with `paper_deg == FALSE` has a row because it was tested but failed at least
one DEG criterion.

Results are appended contrast by contrast. Thousands of consecutive rows can
therefore have the same contrast. The first screenful is not evidence that the
file contains only one comparison. Tabulate `cell_type_high_resolution` and
`contrast_name` to see all result blocks.

## Complete 25-column dictionary

### Artifact and input identity

| Column | Meaning |
|---|---|
| `schema_version` | Result schema, currently `mast_de_results_v1`. |
| `rds_id` | Stable source-object identifier, such as `astrocytes` or `vasculature`. |
| `source_rds` | Project-relative original Seurat RDS path. This is provenance; the model uses the normalized RDS. |
| `normalized_rds` | Project-relative Phase 05 normalized Seurat object used by MAST. Expression comes from its RNA `data` layer. |

### Fine-cell-type and contrast identity

| Column | Meaning |
|---|---|
| `cell_type_high_resolution` | Exact fine cell type used for this comparison. |
| `manifest_row` | Row number in the **Phase 07 contrast manifest**, not in `config/minerva_rds_manifest.tsv`. It links back to required groups, eligibility, and sample counts. |
| `contrast_id` | Globally unique identifier, normally `<rds_id>::<sanitized_cell_type>::<contrast_name>`. Use this for joins rather than `contrast_name` alone. |
| `contrast_family` | Contrast class. Phase 08 result rows use `AD_vs_NCI`. |
| `contrast_name` | Human-readable comparison such as `AD_vs_NCI__Female__e33`. It encodes AD as numerator, NCI as denominator, sex, and APOE group. |

AD is always `ident.1` and NCI is `ident.2`. This orientation determines the
fold-change sign.

### Gene-level statistics

| Column | Meaning |
|---|---|
| `gene` | Feature/gene symbol returned from the normalized RNA assay by `FindMarkers`. |
| `logFC` | Seurat's descriptive average log2 fold change for AD versus NCI. Positive means higher average normalized expression in AD; negative means higher in NCI. It is not itself the MAST p-value and is not necessarily the fitted MAST coefficient. |
| `pct_ad` | Fraction from 0 to 1 of selected AD nuclei with detected/nonzero expression. This is Seurat `pct.1`. |
| `pct_nci` | Fraction from 0 to 1 of selected NCI nuclei with detected/nonzero expression. This is Seurat `pct.2`. |
| `p_value` | Unadjusted p-value returned by the Seurat MAST test for the AD-versus-NCI group effect after adjustment for the listed latent variables. |
| `fdr_bh_within_contrast` | Benjamini-Hochberg adjustment across all genes returned for this one fine-cell-type/sex-APOE contrast. It does not adjust across other contrasts or cell types. |
| `paper_effect_threshold_log2` | Fixed `log2(1.3)` effect threshold, approximately 0.3785116. It is repeated for provenance and is not estimated from the row. |
| `paper_deg` | `TRUE` when FDR is below 0.05, absolute `logFC` exceeds the threshold, and detection is at least 10% in AD or NCI; otherwise `FALSE`. |

MAST is a hurdle-model analysis, combining information about detected versus
undetected expression with continuous expression among expressing nuclei.
`logFC` is Seurat's average-expression summary, whereas `p_value` is
model-based evidence. They are related but are not the same calculation.

The FDR is local to one contrast. Phase 11 adds and audits broader
multiple-testing families. A Phase 08 within-contrast FDR below 0.05 does not
control FDR across all 54 cell types and six sex-APOE comparisons.

### Nucleus, donor, and covariate context

| Column | Meaning |
|---|---|
| `cells_ad` | AD nuclei used in the contrast, repeated on every gene row in that contrast. |
| `cells_nci` | NCI nuclei used in the contrast, also repeated. |
| `donors_ad` | Distinct represented AD donors. This is contrast-level, not gene-specific. |
| `donors_nci` | Distinct represented NCI donors. |
| `latent_vars` | Semicolon-separated MAST covariates; production uses `nCount_RNA;age_death_scaled;pmi_scaled`. |

The covariates are per-nucleus RNA depth, scaled donor age at death, and scaled
donor postmortem interval. Age and PMI repeat across nuclei from one donor.
The model does not include a donor random effect. Very large cell counts can
therefore yield much smaller MAST p-values than the donor-aware pseudobulk
analysis, even when donor counts are modest. Phase 08 is secondary; Phase 07 is
the primary inference.

### Phase 07 pseudobulk comparison columns

| Column | Meaning |
|---|---|
| `pseudobulk_logFC` | Phase 07 donor-aware pseudobulk log2 fold change for the same gene, fine cell type, and contrast name. Missing when no pseudobulk gene row matched, often because method-specific filtering differed. |
| `pseudobulk_fdr` | Matching Phase 07 within-contrast pseudobulk FDR. Missing for a nonoverlapping gene. |
| `direction_concordant_with_pseudobulk` | `TRUE` if MAST and pseudobulk `logFC` signs agree, `FALSE` if they differ, and `NA` when no pseudobulk result matched. Sign agreement does not require either method to be significant. |

The script reads the pseudobulk raw p-value during matching, but it does not
write a `pseudobulk_p_value` column. Only pseudobulk logFC and FDR are stored.
An `NA` concordance value means unavailable for comparison, not discordant.

## Worked production-row example

An inspected Astrocytes row reports:

```text
fine cell type:      Ast CHI3L1
contrast:            AD_vs_NCI__Female__e33
gene:                NTRK2
logFC:               0.738
pct_ad / pct_nci:    0.980 / 0.926
MAST FDR:            2.74e-135
AD / NCI nuclei:     1,828 / 3,032
AD / NCI donors:     11 / 17
pseudobulk logFC:    0.690
pseudobulk FDR:      0.336
direction agreement: TRUE
paper_deg:           TRUE
```

NTRK2 was detected in 98.0% of selected AD nuclei and 92.6% of NCI nuclei.
Its average normalized expression was higher in AD; `2^0.738` is approximately
a 1.67-fold descriptive difference. It passes the cell-level Phase 08 rule.

The donor-aware effect has the same direction and similar magnitude, but its
pseudobulk FDR is 0.336. Phase 07 therefore does not call it significant in
that contrast. This is a concrete example of why an extremely small cell-level
MAST FDR is not equivalent to strong donor-level replication.

## Current production row counts

Across the nine inspected validated bundles:

- the contrast manifest contains 756 rows, 14 for each of 54 fine cell types;
- 324 rows are paper-matched AD-versus-NCI comparisons;
- 188 paper comparisons were eligible and completed;
- 136 paper comparisons were ineligible;
- 432 interaction/omnibus rows were correctly marked not applicable;
- no eligible MAST contrast failed;
- the compressed result files contain 1,729,179 tested gene rows; and
- 87,710 rows have `paper_deg == TRUE`.

The 87,710 value is a count of gene-cell-type-contrast calls, not unique genes.

The canonical Vasculature compressed file contains 14,958 rows:

| Fine cell type | Contrast | Rows |
|---|---|---:|
| `End` | `AD_vs_NCI__Female__e33` | 4,847 |
| `Per` | `AD_vs_NCI__Female__e33` | 4,883 |
| `End` | `AD_vs_NCI__Male__e33` | 5,228 |

Other Vasculature paper comparisons were ineligible, so they have no gene rows.
This is why the canonical file contains only the e33 APOE label.

The directory also contains `vasculature.mast_de.tsv`, but that uncompressed
filename is not written or declared by the Phase 08 script or artifact
manifest. Treat `vasculature.mast_de.tsv.gz` as canonical; a manually
decompressed or subset TSV can be incomplete or stale.

## Reconciling the number of rows in every compressed result

A decompressed TSV contains one header plus one line for every tested
gene-cell-type-contrast result:

```text
physical lines = 1 header + sum of tested genes across fitted combinations
```

The tested-gene count can differ between combinations because the 10%
detection filter is recalculated using that comparison's AD and NCI nuclei.
Genes overlap heavily across combinations, so these subtotals must not be
added to estimate unique genes.

### Vasculature 14,959-line example

The uncompressed `vasculature.mast_de.tsv` has 14,959 physical lines:

- one header line;
- 4,847 End/Female/e33 gene tests;
- 5,228 End/Male/e33 gene tests; and
- 4,883 Per/Female/e33 gene tests.

Thus, `1 + 4,847 + 5,228 + 4,883 = 14,959`. The scientific
table has 14,958 data rows. It contains 6,279 unique gene symbols because
genes tested in more than one fitted combination appear more than once.
All 14,958 scientific keys are unique, so the count is not caused by
duplicated rows.

The current uncompressed file and the decompressed canonical
`vasculature.mast_de.tsv.gz` have the same SHA-256, so their current
contents are byte-for-byte identical. The GZIP remains the declared pipeline
artifact.

Only three Vasculature paper comparisons passed the minimum-five-donors-per-
side eligibility rule. Twenty-seven other paper comparisons were ineligible,
and 40 interaction/omnibus rows were not applicable to Phase 08 MAST.

### File-level reconciliation

| Broad RDS | Fine types represented | Fitted combinations | Data rows | Decompressed physical lines |
|---|---:|---:|---:|---:|
| `astrocytes` | 3 | 15 | 109,882 | 109,883 |
| `excitatory_set1` | 1 | 6 | 63,334 | 63,335 |
| `excitatory_set2` | 4 | 24 | 277,197 | 277,198 |
| `excitatory_set3` | 8 | 40 | 413,884 | 413,885 |
| `immune` | 2 | 7 | 34,930 | 34,931 |
| `inhibitory` | 22 | 81 | 731,987 | 731,988 |
| `oligodendrocytes` | 1 | 6 | 34,285 | 34,286 |
| `opcs` | 1 | 6 | 48,722 | 48,723 |
| `vasculature` | 2 | 3 | 14,958 | 14,959 |

The detailed tables below list every combination that actually contributes
rows. A missing fine-cell-type/contrast combination had no fitted eligible
paper comparison and therefore contributes zero rows.

### Astrocytes (`astrocytes`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Ast CHI3L1` | `AD_vs_NCI__Female__e33` | 8,502 |
| `Ast CHI3L1` | `AD_vs_NCI__Female__e4` | 8,463 |
| `Ast CHI3L1` | `AD_vs_NCI__Male__e33` | 8,511 |
| `Ast CHI3L1` | `AD_vs_NCI__Male__e4` | 7,163 |
| `Ast DPP10` | `AD_vs_NCI__Female__e2` | 6,410 |
| `Ast DPP10` | `AD_vs_NCI__Female__e33` | 6,655 |
| `Ast DPP10` | `AD_vs_NCI__Female__e4` | 7,029 |
| `Ast DPP10` | `AD_vs_NCI__Male__e33` | 6,562 |
| `Ast DPP10` | `AD_vs_NCI__Male__e4` | 6,878 |
| `Ast GRM3` | `AD_vs_NCI__Female__e2` | 7,470 |
| `Ast GRM3` | `AD_vs_NCI__Female__e33` | 7,333 |
| `Ast GRM3` | `AD_vs_NCI__Female__e4` | 8,368 |
| `Ast GRM3` | `AD_vs_NCI__Male__e2` | 6,983 |
| `Ast GRM3` | `AD_vs_NCI__Male__e33` | 6,799 |
| `Ast GRM3` | `AD_vs_NCI__Male__e4` | 6,756 |
| **File subtotal** | **15 fitted combinations** | **109,882** |

### Excitatory neurons set 1 (`excitatory_set1`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Female__e2` | 10,468 |
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Female__e33` | 10,586 |
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Female__e4` | 10,682 |
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Male__e2` | 10,846 |
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Male__e33` | 10,427 |
| `Exc L2-3 CBLN2 LINC02306` | `AD_vs_NCI__Male__e4` | 10,325 |
| **File subtotal** | **6 fitted combinations** | **63,334** |

### Excitatory neurons set 2 (`excitatory_set2`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Female__e2` | 11,871 |
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Female__e33` | 12,076 |
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Female__e4` | 12,373 |
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Male__e2` | 12,118 |
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Male__e33` | 11,784 |
| `Exc L3-4 RORB CUX2` | `AD_vs_NCI__Male__e4` | 11,792 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Female__e2` | 12,232 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Female__e33` | 11,709 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Female__e4` | 11,828 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Male__e2` | 11,620 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Male__e33` | 11,202 |
| `Exc L3-5 RORB PLCH1` | `AD_vs_NCI__Male__e4` | 11,250 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Female__e2` | 11,080 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Female__e33` | 10,995 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Female__e4` | 10,995 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Male__e2` | 10,791 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Male__e33` | 10,407 |
| `Exc L4-5 RORB GABRG1` | `AD_vs_NCI__Male__e4` | 10,463 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Female__e2` | 11,874 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Female__e33` | 11,857 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Female__e4` | 11,934 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Male__e2` | 11,811 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Male__e33` | 11,543 |
| `Exc L4-5 RORB IL1RAPL2` | `AD_vs_NCI__Male__e4` | 11,592 |
| **File subtotal** | **24 fitted combinations** | **277,197** |

### Excitatory neurons set 3 (`excitatory_set3`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Exc L5-6 RORB LINC02196` | `AD_vs_NCI__Female__e2` | 11,950 |
| `Exc L5-6 RORB LINC02196` | `AD_vs_NCI__Female__e33` | 11,855 |
| `Exc L5-6 RORB LINC02196` | `AD_vs_NCI__Female__e4` | 12,199 |
| `Exc L5-6 RORB LINC02196` | `AD_vs_NCI__Male__e33` | 11,521 |
| `Exc L5-6 RORB LINC02196` | `AD_vs_NCI__Male__e4` | 11,585 |
| `Exc L5/6 IT Car3` | `AD_vs_NCI__Female__e2` | 12,656 |
| `Exc L5/6 IT Car3` | `AD_vs_NCI__Female__e33` | 12,230 |
| `Exc L5/6 IT Car3` | `AD_vs_NCI__Female__e4` | 12,546 |
| `Exc L5/6 IT Car3` | `AD_vs_NCI__Male__e33` | 11,688 |
| `Exc L5/6 IT Car3` | `AD_vs_NCI__Male__e4` | 12,258 |
| `Exc L5/6 NP` | `AD_vs_NCI__Female__e2` | 11,354 |
| `Exc L5/6 NP` | `AD_vs_NCI__Female__e33` | 11,003 |
| `Exc L5/6 NP` | `AD_vs_NCI__Female__e4` | 11,465 |
| `Exc L5/6 NP` | `AD_vs_NCI__Male__e33` | 10,964 |
| `Exc L5/6 NP` | `AD_vs_NCI__Male__e4` | 10,872 |
| `Exc L6 CT` | `AD_vs_NCI__Female__e2` | 10,945 |
| `Exc L6 CT` | `AD_vs_NCI__Female__e33` | 11,032 |
| `Exc L6 CT` | `AD_vs_NCI__Female__e4` | 11,337 |
| `Exc L6 CT` | `AD_vs_NCI__Male__e33` | 10,719 |
| `Exc L6 CT` | `AD_vs_NCI__Male__e4` | 11,220 |
| `Exc L6 THEMIS NFIA` | `AD_vs_NCI__Female__e2` | 12,416 |
| `Exc L6 THEMIS NFIA` | `AD_vs_NCI__Female__e33` | 12,341 |
| `Exc L6 THEMIS NFIA` | `AD_vs_NCI__Female__e4` | 12,778 |
| `Exc L6 THEMIS NFIA` | `AD_vs_NCI__Male__e33` | 12,109 |
| `Exc L6 THEMIS NFIA` | `AD_vs_NCI__Male__e4` | 12,327 |
| `Exc L6b` | `AD_vs_NCI__Female__e2` | 12,740 |
| `Exc L6b` | `AD_vs_NCI__Female__e33` | 12,153 |
| `Exc L6b` | `AD_vs_NCI__Female__e4` | 12,798 |
| `Exc L6b` | `AD_vs_NCI__Male__e33` | 11,767 |
| `Exc L6b` | `AD_vs_NCI__Male__e4` | 12,442 |
| `Exc NRGN` | `AD_vs_NCI__Female__e2` | 4,906 |
| `Exc NRGN` | `AD_vs_NCI__Female__e33` | 4,457 |
| `Exc NRGN` | `AD_vs_NCI__Female__e4` | 4,553 |
| `Exc NRGN` | `AD_vs_NCI__Male__e2` | 5,131 |
| `Exc NRGN` | `AD_vs_NCI__Male__e33` | 4,578 |
| `Exc NRGN` | `AD_vs_NCI__Male__e4` | 6,294 |
| `Exc RELN CHD7` | `AD_vs_NCI__Female__e33` | 7,534 |
| `Exc RELN CHD7` | `AD_vs_NCI__Female__e4` | 8,651 |
| `Exc RELN CHD7` | `AD_vs_NCI__Male__e33` | 5,574 |
| `Exc RELN CHD7` | `AD_vs_NCI__Male__e4` | 6,936 |
| **File subtotal** | **40 fitted combinations** | **413,884** |

Fine cell types with no eligible fitted Phase 08 comparison and therefore no rows: `Exc L5 ET`.

### Immune cells (`immune`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Mic P2RY12` | `AD_vs_NCI__Female__e2` | 4,639 |
| `Mic P2RY12` | `AD_vs_NCI__Female__e33` | 5,146 |
| `Mic P2RY12` | `AD_vs_NCI__Female__e4` | 5,385 |
| `Mic P2RY12` | `AD_vs_NCI__Male__e2` | 4,328 |
| `Mic P2RY12` | `AD_vs_NCI__Male__e33` | 4,716 |
| `Mic P2RY12` | `AD_vs_NCI__Male__e4` | 4,967 |
| `Mic TPT1` | `AD_vs_NCI__Female__e33` | 5,749 |
| **File subtotal** | **7 fitted combinations** | **34,930** |

Fine cell types with no eligible fitted Phase 08 comparison and therefore no rows: `CAMs`, `Mic MKI67`, `T cells`.

### Inhibitory neurons (`inhibitory`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Inh ALCAM TRPM3` | `AD_vs_NCI__Female__e33` | 10,493 |
| `Inh ALCAM TRPM3` | `AD_vs_NCI__Female__e4` | 10,121 |
| `Inh ALCAM TRPM3` | `AD_vs_NCI__Male__e33` | 10,065 |
| `Inh ALCAM TRPM3` | `AD_vs_NCI__Male__e4` | 10,048 |
| `Inh CUX2 MSR1` | `AD_vs_NCI__Female__e33` | 7,379 |
| `Inh CUX2 MSR1` | `AD_vs_NCI__Female__e4` | 7,625 |
| `Inh CUX2 MSR1` | `AD_vs_NCI__Male__e33` | 7,840 |
| `Inh CUX2 MSR1` | `AD_vs_NCI__Male__e4` | 6,712 |
| `Inh ENOX2 SPHKAP` | `AD_vs_NCI__Female__e33` | 8,598 |
| `Inh ENOX2 SPHKAP` | `AD_vs_NCI__Female__e4` | 8,830 |
| `Inh ENOX2 SPHKAP` | `AD_vs_NCI__Male__e33` | 8,776 |
| `Inh ENOX2 SPHKAP` | `AD_vs_NCI__Male__e4` | 8,233 |
| `Inh FBN2 EPB41L4A` | `AD_vs_NCI__Female__e33` | 10,293 |
| `Inh FBN2 EPB41L4A` | `AD_vs_NCI__Female__e4` | 10,611 |
| `Inh FBN2 EPB41L4A` | `AD_vs_NCI__Male__e33` | 10,154 |
| `Inh GPC5 RIT2` | `AD_vs_NCI__Female__e33` | 10,077 |
| `Inh GPC5 RIT2` | `AD_vs_NCI__Male__e33` | 9,520 |
| `Inh L1 PAX6 CA4` | `AD_vs_NCI__Female__e33` | 8,533 |
| `Inh L1 PAX6 CA4` | `AD_vs_NCI__Male__e33` | 8,518 |
| `Inh L1-6 LAMP5 CA13` | `AD_vs_NCI__Female__e33` | 10,252 |
| `Inh L1-6 LAMP5 CA13` | `AD_vs_NCI__Female__e4` | 10,485 |
| `Inh L1-6 LAMP5 CA13` | `AD_vs_NCI__Male__e33` | 10,247 |
| `Inh L1-6 LAMP5 CA13` | `AD_vs_NCI__Male__e4` | 9,919 |
| `Inh L3-5 SST MAFB` | `AD_vs_NCI__Female__e33` | 7,642 |
| `Inh L3-5 SST MAFB` | `AD_vs_NCI__Female__e4` | 7,621 |
| `Inh L3-5 SST MAFB` | `AD_vs_NCI__Male__e33` | 7,992 |
| `Inh L3-5 SST MAFB` | `AD_vs_NCI__Male__e4` | 6,764 |
| `Inh L5-6 PVALB STON2` | `AD_vs_NCI__Female__e33` | 10,304 |
| `Inh L5-6 PVALB STON2` | `AD_vs_NCI__Male__e33` | 10,369 |
| `Inh L5-6 SST TH` | `AD_vs_NCI__Female__e33` | 9,661 |
| `Inh LAMP5 NRG1 (Rosehip)` | `AD_vs_NCI__Female__e2` | 9,568 |
| `Inh LAMP5 NRG1 (Rosehip)` | `AD_vs_NCI__Female__e33` | 9,589 |
| `Inh LAMP5 NRG1 (Rosehip)` | `AD_vs_NCI__Female__e4` | 9,200 |
| `Inh LAMP5 NRG1 (Rosehip)` | `AD_vs_NCI__Male__e33` | 9,527 |
| `Inh LAMP5 NRG1 (Rosehip)` | `AD_vs_NCI__Male__e4` | 8,999 |
| `Inh LAMP5 RELN` | `AD_vs_NCI__Female__e33` | 8,086 |
| `Inh LAMP5 RELN` | `AD_vs_NCI__Female__e4` | 7,363 |
| `Inh LAMP5 RELN` | `AD_vs_NCI__Male__e33` | 8,415 |
| `Inh PTPRK FAM19A1` | `AD_vs_NCI__Female__e33` | 7,918 |
| `Inh PTPRK FAM19A1` | `AD_vs_NCI__Female__e4` | 7,576 |
| `Inh PTPRK FAM19A1` | `AD_vs_NCI__Male__e33` | 8,155 |
| `Inh PTPRK FAM19A1` | `AD_vs_NCI__Male__e4` | 7,292 |
| `Inh PVALB CA8 (Chandelier)` | `AD_vs_NCI__Female__e33` | 8,985 |
| `Inh PVALB CA8 (Chandelier)` | `AD_vs_NCI__Female__e4` | 8,739 |
| `Inh PVALB CA8 (Chandelier)` | `AD_vs_NCI__Male__e33` | 8,693 |
| `Inh PVALB CA8 (Chandelier)` | `AD_vs_NCI__Male__e4` | 8,428 |
| `Inh PVALB HTR4` | `AD_vs_NCI__Female__e2` | 10,678 |
| `Inh PVALB HTR4` | `AD_vs_NCI__Female__e33` | 10,314 |
| `Inh PVALB HTR4` | `AD_vs_NCI__Female__e4` | 10,320 |
| `Inh PVALB HTR4` | `AD_vs_NCI__Male__e33` | 10,288 |
| `Inh PVALB HTR4` | `AD_vs_NCI__Male__e4` | 10,117 |
| `Inh PVALB SULF1` | `AD_vs_NCI__Female__e2` | 10,192 |
| `Inh PVALB SULF1` | `AD_vs_NCI__Female__e33` | 10,072 |
| `Inh PVALB SULF1` | `AD_vs_NCI__Female__e4` | 10,149 |
| `Inh PVALB SULF1` | `AD_vs_NCI__Male__e33` | 9,961 |
| `Inh PVALB SULF1` | `AD_vs_NCI__Male__e4` | 9,877 |
| `Inh RYR3 TSHZ2` | `AD_vs_NCI__Female__e2` | 8,098 |
| `Inh RYR3 TSHZ2` | `AD_vs_NCI__Female__e33` | 8,532 |
| `Inh RYR3 TSHZ2` | `AD_vs_NCI__Female__e4` | 8,599 |
| `Inh RYR3 TSHZ2` | `AD_vs_NCI__Male__e33` | 8,261 |
| `Inh RYR3 TSHZ2` | `AD_vs_NCI__Male__e4` | 7,692 |
| `Inh SORCS1 TTN` | `AD_vs_NCI__Female__e33` | 7,677 |
| `Inh SORCS1 TTN` | `AD_vs_NCI__Male__e33` | 7,863 |
| `Inh SORCS1 TTN` | `AD_vs_NCI__Male__e4` | 7,517 |
| `Inh VIP ABI3BP` | `AD_vs_NCI__Female__e33` | 9,917 |
| `Inh VIP ABI3BP` | `AD_vs_NCI__Female__e4` | 9,998 |
| `Inh VIP ABI3BP` | `AD_vs_NCI__Male__e33` | 9,715 |
| `Inh VIP ABI3BP` | `AD_vs_NCI__Male__e4` | 9,416 |
| `Inh VIP CLSTN2` | `AD_vs_NCI__Female__e2` | 9,706 |
| `Inh VIP CLSTN2` | `AD_vs_NCI__Female__e33` | 9,415 |
| `Inh VIP CLSTN2` | `AD_vs_NCI__Female__e4` | 9,356 |
| `Inh VIP CLSTN2` | `AD_vs_NCI__Male__e33` | 9,000 |
| `Inh VIP CLSTN2` | `AD_vs_NCI__Male__e4` | 9,074 |
| `Inh VIP THSD7B` | `AD_vs_NCI__Female__e33` | 8,888 |
| `Inh VIP THSD7B` | `AD_vs_NCI__Female__e4` | 9,166 |
| `Inh VIP THSD7B` | `AD_vs_NCI__Male__e33` | 9,167 |
| `Inh VIP THSD7B` | `AD_vs_NCI__Male__e4` | 8,971 |
| `Inh VIP TSHZ2` | `AD_vs_NCI__Female__e33` | 8,644 |
| `Inh VIP TSHZ2` | `AD_vs_NCI__Female__e4` | 8,796 |
| `Inh VIP TSHZ2` | `AD_vs_NCI__Male__e33` | 8,518 |
| `Inh VIP TSHZ2` | `AD_vs_NCI__Male__e4` | 7,818 |
| **File subtotal** | **81 fitted combinations** | **731,987** |

Fine cell types with no eligible fitted Phase 08 comparison and therefore no rows: `Inh L1-2 PAX6 SCGN`, `Inh L6 SST NPY`, `Inh SGCD PDE3A`.

### Oligodendrocytes (`oligodendrocytes`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `Oli` | `AD_vs_NCI__Female__e2` | 6,274 |
| `Oli` | `AD_vs_NCI__Female__e33` | 5,712 |
| `Oli` | `AD_vs_NCI__Female__e4` | 6,054 |
| `Oli` | `AD_vs_NCI__Male__e2` | 5,054 |
| `Oli` | `AD_vs_NCI__Male__e33` | 5,547 |
| `Oli` | `AD_vs_NCI__Male__e4` | 5,644 |
| **File subtotal** | **6 fitted combinations** | **34,285** |

### OPCs (`opcs`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `OPC` | `AD_vs_NCI__Female__e2` | 8,808 |
| `OPC` | `AD_vs_NCI__Female__e33` | 8,084 |
| `OPC` | `AD_vs_NCI__Female__e4` | 8,624 |
| `OPC` | `AD_vs_NCI__Male__e2` | 7,648 |
| `OPC` | `AD_vs_NCI__Male__e33` | 7,652 |
| `OPC` | `AD_vs_NCI__Male__e4` | 7,906 |
| **File subtotal** | **6 fitted combinations** | **48,722** |

### Vasculature (`vasculature`)

| Fine cell type | Contrast | Tested genes / result rows |
|---|---|---:|
| `End` | `AD_vs_NCI__Female__e33` | 4,847 |
| `End` | `AD_vs_NCI__Male__e33` | 5,228 |
| `Per` | `AD_vs_NCI__Female__e33` | 4,883 |
| **File subtotal** | **3 fitted combinations** | **14,958** |

Fine cell types with no eligible fitted Phase 08 comparison and therefore no rows: `Fib FLRT2`, `Fib SLC4A4`, `SMC`.


## Display all Phase 08 DEGs on Minerva

From the Minerva project root, run:

```bash
cd /sc/arion/work/zhuane01/alzheimer

Rscript -e '
files <- list.files(
  "results/minerva_production/08_mast",
  pattern = "[.]mast_de[.]tsv[.]gz$",
  full.names = TRUE
)

stopifnot(length(files) > 0L)

results <- do.call(
  rbind,
  lapply(files, function(path) read.delim(gzfile(path)))
)

degs <- results[results$paper_deg %in% TRUE, ]

degs <- degs[
  order(
    degs$rds_id,
    degs$cell_type_high_resolution,
    degs$contrast_name,
    degs$fdr_bh_within_contrast,
    -abs(degs$logFC)
  ),
  c(
    "rds_id",
    "cell_type_high_resolution",
    "contrast_name",
    "gene",
    "logFC",
    "pct_ad",
    "pct_nci",
    "p_value",
    "fdr_bh_within_contrast",
    "cells_ad",
    "cells_nci",
    "donors_ad",
    "donors_nci"
  )
]

print(degs, row.names = FALSE)
cat("\nTotal Phase 08 DEG rows:", nrow(degs), "\n")
'
```

This command reads every completed RDS result file. If Phase 08 is still running, its output represents only RDS tasks whose final `.mast_de.tsv.gz` files already exist.

## Inspect only Astrocyte DEGs

```bash
cd /sc/arion/work/zhuane01/alzheimer

Rscript -e '
x <- read.delim(gzfile(
  "results/minerva_production/08_mast/astrocytes.mast_de.tsv.gz"
))
x <- x[x$paper_deg %in% TRUE, ]
x <- x[order(x$fdr_bh_within_contrast), ]
print(x[, c(
  "cell_type_high_resolution",
  "contrast_name",
  "gene",
  "logFC",
  "pct_ad",
  "pct_nci",
  "fdr_bh_within_contrast"
)], row.names = FALSE)
'
```

## Interpretation cautions

- A DEG row describes one gene in one fine-cell-type and sex-APOE contrast. The same gene can appear in multiple rows.
- A small cell-level MAST FDR is not equivalent to donor-level evidence because nuclei from the same donor are not independent biological replicates.
- Interpret Phase 08 alongside the primary Phase 07 pseudobulk results in `results/minerva_production/07_pseudobulk_de/`.
- Compare methods using effect direction, effect magnitude, rank, FDR, and donor counts; do not conclude that MAST is stronger merely because it calls more genes.
- Before interpreting an RDS, confirm that its `.mast_de_status.tsv` reports `validated_complete`, its contrast-status file contains no `failed` rows, and all rows in its check table pass.
