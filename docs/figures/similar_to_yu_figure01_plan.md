# Plan for a mitochondrial version of Yu et al. Figure 1

## 1. Recommendation

Create a figure similar to Figure 1 in `docs/Yu_sex_apoe.pdf`, but restrict the displayed genes to the approximately 1,000 mitochondrial-related genes defined by MitoCarta.

This should be one of the most informative figures in the project because it connects our mitochondrial focus directly to the sex-APOE-cell-type differential-expression design used by Yu et al.

The proposed title is:

```text
MitoCarta AD differential-expression landscape across sex, APOE, and cell type
```

## 2. Required differential-expression source: Phase 08 MAST

The DEG calls for this figure must come from the **MAST differential-expression analysis produced in Phase 08**.

The source files are:

```text
results/minerva_production/08_mast/*.mast_de.tsv.gz
```

This choice is important because:

1. Yu et al. Figure 1 used MAST.
2. Phase 08 uses Seurat `FindMarkers` with `test.use = "MAST"`.
3. Phase 08 already produces the paper-comparable `paper_deg` flag.
4. Using Phase 08 makes the new figure directly comparable with the original paper.

The primary figure must **not mix pseudobulk and MAST DEG calls**. Pseudobulk results can be examined separately as a sensitivity analysis, but they are not the DEG source for this Yu-style figure.

All of the following must come from the Phase 08 MAST rows:

- gene tested status;
- log2 fold change and its direction;
- within-contrast p-value and FDR;
- `paper_deg` status;
- cell type;
- sex-APOE contrast; and
- MAST model and contrast status.

## 3. Mitochondrial gene definition

Restrict the Phase 08 results to genes marked:

```text
is_mitocarta = TRUE
```

The MitoCarta mapping should come from the frozen Phase 03 annotations:

```text
results/minerva_production/03_annotations/tested_gene_universe.tsv
```

The frozen MitoCarta source contains 1,136 canonical entries. The assay can contain a slightly different number of mapped feature names because aliases or multiple assay identifiers can map to the same canonical MitoCarta entry.

The main analysis unit should be the tested assay gene or feature used by Phase 08. If several assay feature names map to the same canonical MitoCarta gene, the implementation must document whether they are retained as distinct tested features or collapsed. It must not silently count the same canonical gene twice.

The 13 mtDNA protein-coding genes are a smaller subset of MitoCarta. They may be marked with a symbol or label, but the planned figure is intended to cover the full measured MitoCarta set.

## 4. DEG definition

For direct comparability with Yu et al., define a DEG using the Phase 08 `paper_deg` rule:

```text
within-contrast BH FDR < 0.05
AND
absolute fold change > 1.3
```

Because Phase 08 stores log2 fold change, the effect threshold is:

```text
absolute log2 fold change > log2(1.3)
                           approximately 0.3785
```

In practice, the figure-generation code should use the existing Phase 08 column:

```text
paper_deg = TRUE
```

rather than independently reconstructing the rule. The code should nevertheless validate that every `paper_deg = TRUE` row satisfies the expected FDR, fold-change, and detection criteria.

The direction is determined from the Phase 08 MAST log2 fold change:

```text
paper_deg = TRUE and logFC > 0  -> upregulated in AD
paper_deg = TRUE and logFC < 0  -> downregulated in AD
paper_deg = FALSE               -> not called differentially expressed
```

The figure must not recalculate BH FDR only among the MitoCarta subset. Doing that would create a different testing family from Yu et al. and from the existing Phase 08 `paper_deg` definition.

## 5. Optional Phase 11 overlay

Phase 11 provides a more stringent study-wide MitoCarta correction:

```text
fdr_bh_mitocarta_global < 0.05
```

If the production Phase 11 outputs are available, a small border, dot, or asterisk may identify Phase 08 MAST rows that also survive the Phase 11 MitoCarta-global correction.

This overlay must remain secondary:

- tile membership and DEG counts come from Phase 08 `paper_deg`;
- Phase 11 must not redefine which genes enter the Yu-comparable DEG counts; and
- the caption must explain the difference between within-contrast Phase 08 evidence and study-wide Phase 11 evidence.

## 6. Proposed figure panels

### Panel A: upregulated MitoCarta genes

Use the same general layout as Yu et al. Figure 1A.

- Rows: the six sex-APOE groups.
- Columns: the 54 fine cell types.
- Tile value: number of tested MitoCarta genes significantly upregulated in AD according to Phase 08 MAST.
- Suggested color: white to red.

The six rows are:

```text
Female e2
Female e33
Female e4
Male e2
Male e33
Male e4
```

Each row represents an AD-versus-NCI contrast within that sex-APOE group.

### Panel B: downregulated MitoCarta genes

Use the same layout as Panel A.

- Rows: the six sex-APOE groups.
- Columns: the 54 fine cell types.
- Tile value: number of tested MitoCarta genes significantly downregulated in AD according to Phase 08 MAST.
- Suggested color: white to blue.

Panels A and B should use related, clearly labeled scales. If the maximum upregulated and downregulated counts differ greatly, either use separate scales and state that fact or use a shared maximum to support direct visual comparison.

### Panel C: APOE comparisons within females

Compare the Phase 08 MAST AD-versus-NCI calls between female APOE groups:

```text
Female e2 versus Female e33
Female e4 versus Female e33
Female e2 versus Female e4
```

For each fine cell type, classify MitoCarta genes as:

- significant in both with the same direction;
- unique to the first APOE group;
- unique to the second APOE group;
- significant in both with opposite directions; or
- not called in either group.

The main displayed categories should match the Yu et al. common, unique, and opposite framework. The `not called in either` category should be retained in the companion table even if it is omitted from the plotted heat map.

### Panel D: APOE comparisons within males

Repeat Panel C for male APOE groups:

```text
Male e2 versus Male e33
Male e4 versus Male e33
Male e2 versus Male e4
```

Use exactly the same category definitions, ordering, and colors as Panel C.

### Panel E: female-versus-male comparisons within APOE groups

Compare Phase 08 MAST AD-versus-NCI calls between females and males within each APOE group:

```text
Female e2 versus Male e2
Female e33 versus Male e33
Female e4 versus Male e4
```

For each fine cell type, classify MitoCarta genes as:

- significant in both sexes with the same direction;
- significant only in females;
- significant only in males;
- significant in both with opposite directions; or
- not called in either sex.

This panel provides the most direct view of sex-dependent mitochondrial transcriptional responses.

## 7. Counts and denominators

Each tile should report both the DEG count and the number of eligible MitoCarta genes tested in that contrast.

The recommended annotation is:

```text
DEG count / tested MitoCarta genes
```

For example:

```text
42 / 917
```

An optional second line or companion table should report:

```text
100 x DEG count / tested MitoCarta genes
```

Using only raw counts can be misleading because the number of MitoCarta genes passing the Phase 08 detection filter can differ across cell types and contrasts. Forty DEGs out of 500 tested genes represent a different proportion from forty DEGs out of 1,100 tested genes.

For Panels C-E, pairwise classifications must use only the intersection of MitoCarta genes tested in both contrasts. Otherwise a gene could appear unique merely because it was not tested in the comparison group.

The companion table must record:

- genes tested in the first contrast;
- genes tested in the second contrast;
- genes in the tested intersection; and
- genes excluded from comparison because they were not jointly testable.

## 8. Ineligible and missing contrasts

If a Phase 08 contrast was not fitted or was ineligible, its tile must be visually distinct from a true zero.

Recommended display:

- light grey tile;
- label `NE` for not estimable; and
- a companion-table field containing the Phase 08 terminal status and reason.

A white tile with `0` should mean:

```text
the contrast was fitted, MitoCarta genes were tested, and no genes met the DEG rule
```

Grey `NE` should mean:

```text
the planned comparison could not be estimated or did not complete successfully
```

These meanings must never be merged.

## 9. Required source tables

The figure-generation code should read:

1. Phase 08 MAST results:

   ```text
   results/minerva_production/08_mast/*.mast_de.tsv.gz
   ```

2. Phase 08 contrast and model status tables:

   ```text
   results/minerva_production/08_mast/*.mast_contrast_status.tsv
   results/minerva_production/08_mast/*.mast_model_diagnostics.tsv
   results/minerva_production/08_mast/*.mast_de_status.tsv
   ```

3. Phase 03 mitochondrial annotations:

   ```text
   results/minerva_production/03_annotations/tested_gene_universe.tsv
   ```

4. Phase 07 contrast manifest for donor counts and eligibility metadata:

   ```text
   results/minerva_production/07_contrasts/minerva_production_contrast_manifest.tsv
   ```

5. Optionally, restored Phase 11 MAST rows for the secondary MitoCarta-global overlay:

   ```text
   results/minerva_production/11_multiple_testing/gene_multiple_testing.tsv.gz
   ```

Phase 08 status files must be `validated_complete` before the figure is labeled final.

## 10. Recommended outputs

### Main PDF

```text
results/minerva_production/15_figures/11_mitocarta_mast_deg_landscape.pdf
```

The name should include `mast` so the statistical source cannot be mistaken for pseudobulk.

### Companion summary table

```text
results/minerva_production/15_figures/11_mitocarta_mast_deg_landscape_tiles.tsv
```

One row per panel, comparison, fine cell type, and category should include:

- panel;
- method branch, fixed as `mast`;
- cell type;
- sex and APOE definitions;
- contrast IDs;
- Phase 08 terminal statuses;
- category;
- DEG count;
- tested MitoCarta denominator;
- percentage;
- donor counts;
- MAST call definition;
- annotation version and checksum; and
- optional Phase 11 global-support count.

### Gene-level classification table

```text
results/minerva_production/15_figures/11_mitocarta_mast_deg_landscape_genes.tsv.gz
```

This should contain every jointly eligible MitoCarta gene and its classification, not only the aggregated tile counts.

### Checks table

```text
results/minerva_production/15_figures/11_mitocarta_mast_deg_landscape_checks.tsv
```

Suggested checks include:

- all input Phase 08 statuses validated;
- method branch is always MAST;
- every plotted DEG has `paper_deg = TRUE`;
- every plotted gene is MitoCarta;
- upregulated rows have positive logFC;
- downregulated rows have negative logFC;
- paired categories are mutually exclusive;
- paired category totals equal the tested intersection;
- no ineligible contrast is displayed as zero;
- donor counts match the contrast manifest;
- all 54 fine cell types are represented or explicitly not estimable; and
- input checksums are unchanged during rendering.

## 11. Interpretation cautions

### DEG counts are influenced by power

A cell type can have more MitoCarta DEGs because it has:

- more donors;
- more nuclei contributing to the MAST fit;
- better-balanced AD and NCI groups;
- stronger gene detection;
- larger biological effects; or
- some combination of these factors.

Therefore, a larger DEG count is not automatically evidence of greater mitochondrial dysfunction.

### MAST uses nuclei, but donors determine biological replication

Phase 08 MAST uses nucleus-level observations and covariates. Many nuclei can come from the same donor. The figure must display donor counts from the contrast manifest and should be interpreted together with the donor-coverage figure.

### A unique DEG is not automatically a unique biological effect

A gene may be called significant in one group and not another because the groups have different power. A `significant versus nonsignificant` pattern is not itself a formal proof that the two effects differ.

An opposite-direction call in which both groups are significant is stronger evidence of divergence than a one-sided significance call, but a formal interaction model is still the appropriate test of effect difference.

### The figure describes transcription, not mitochondrial function directly

The figure shows MitoCarta-related RNA differences. It does not directly measure:

- mitochondrial number;
- oxygen consumption;
- ATP production;
- membrane potential;
- protein abundance; or
- causal mitochondrial dysfunction.

## 12. Suggested caption

> **MitoCarta differential-expression signatures between AD and NCI across sex-APOE subgroups.** Panels A and B show the numbers of upregulated and downregulated MitoCarta genes, respectively, between AD and NCI within each of six sex-APOE groups across 54 fine cell types. Differentially expressed genes were identified exclusively from the Phase 08 MAST analysis using the paper-comparable rule of within-contrast Benjamini-Hochberg FDR below 0.05 and absolute fold change above 1.3. Each tile reports the number of MitoCarta DEGs relative to the number of MitoCarta genes tested by MAST in that contrast. Panels C and D compare AD-associated MitoCarta signatures among APOE groups within females and males, respectively. Panel E compares female and male signatures within each APOE group. Pairwise classifications use only MitoCarta genes tested in both source contrasts. Same-direction, group-specific, and opposite-direction categories describe Phase 08 MAST DEG-call patterns and should not be interpreted as formal interaction tests. Grey tiles denote contrasts that were not estimable. Donor counts are reported from the frozen contrast manifest.

## 13. Final decision summary

The planned figure should:

1. resemble Yu et al. Figure 1;
2. focus on measured MitoCarta genes;
3. use **only Phase 08 MAST DEGs** as its primary differential-expression source;
4. use the existing Phase 08 `paper_deg` definition;
5. show both counts and tested-gene denominators;
6. use tested-gene intersections for pairwise panels;
7. display donor counts and not-estimable contrasts clearly;
8. keep any Phase 11 MitoCarta-global indicator secondary; and
9. preserve a gene-level companion table so every aggregated tile can be audited.
