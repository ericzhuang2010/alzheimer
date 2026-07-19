# Plan for a mitochondrial-related version of Yu et al. Figure 1

## 1. Recommendation

Create a figure similar to Figure 1 in `docs/Yu_sex_apoe.pdf`, using the
mitochondrial tiers frozen and validated by Phase 09. The default inclusive
figure uses the `all_mito_related` scope:

```text
core_mito_protein + mtdna_noncoding + mito_extended
```

The script must also support a separately labeled `core_mito` rendering that
contains only `core_mito_protein`. It must never silently mix the two scopes.

This should be one of the most informative figures in the project because it connects our mitochondrial focus directly to the sex-APOE-cell-type differential-expression design used by Yu et al.

The proposed title is:

```text
Mitochondrial-related AD differential-expression landscape across sex, APOE, and cell type
```

## 2. Required data boundary: validated Phase 09 annotations

The figure must read the validated Phase 09 annotation bundle:

```text
results/minerva_production/09_annotate_genes/
├── annotation_status.tsv
├── annotation_checks.tsv
├── annotation_artifacts.tsv
└── deg_all_annotated.tsv.gz
```

Phase 09 is the authoritative handoff because it:

1. preserves the Phase 08 MAST statistics and `paper_deg` calls exactly;
2. adds the frozen Phase 09 mitochondrial tiers and stable identifiers;
3. distinguishes tested, filtered, unmeasured, and non-estimable rows; and
4. retains the exact assay feature rather than silently collapsing
   many-to-one gene mappings.

The script must require `validation_status = validated_complete`, require all
Phase 09 checks and artifact statuses to pass, and verify the annotated
table's declared byte count and SHA-256 before reading it.

Phase 08 remains the statistical origin of the DEG calls, but the figure must
not independently join raw Phase 08 rows to Phase 03 annotations. It must not
read pseudobulk results.

## 3. Mitochondrial gene definition

Phase 09 defines four mutually exclusive tiers using deterministic precedence:

| Tier | Definition | Figure role |
|---|---|---|
| `core_mito_protein` | Canonical Human MitoCarta3.0 member | Included in `core_mito` and `all_mito_related` |
| `mtdna_noncoding` | GENCODE `chrM` mitochondrial rRNA or tRNA | Included only in `all_mito_related`; often unmeasured in snRNA-seq |
| `mito_extended` | Extended-only member of the frozen Reactome V97 four-pathway panel | Included only in `all_mito_related` |
| `non_mito` | None of the above | Excluded |

The extended reference contains 157 HGNC-normalized genes: 77 already in
MitoCarta and 80 extended-only genes. Tier precedence keeps the 77 overlapping
genes in `core_mito_protein`; only the 80 non-core genes receive
`mito_extended`.

The default `all_mito_related` figure therefore selects:

```text
mito_tier %in% c(
  "core_mito_protein",
  "mtdna_noncoding",
  "mito_extended"
)
```

The analysis identity is `feature_id_original`, the exact assay feature
carried through Phases 03, 08, and 09. `symbol_hgnc_current`, `hgnc_id`, and
`ensembl_id_stable` are annotations, not replacement keys. If several assay
features map to one canonical gene, they remain distinct and auditable. This
matches the frozen Phase 09 identifier policy and avoids inventing a
post-Phase 09 collapse rule.

Reference-only genes remain visible in Phase 09 coverage records but cannot
enter a tested denominator or DEG count.

The inclusive rendering is descriptive and must not relabel every included
feature as a MitoCarta gene. `core_mito_protein` remains the primary
mitochondrial-localization tier, `mtdna_noncoding` remains exploratory, and
`mito_extended` remains a secondary/sensitivity tier. The tier-specific
columns and optional `core_mito` rendering preserve those distinctions.

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

In practice, the figure-generation code should use the Phase 09 fields:

```text
tested_status = significant_up    and deg_state = +1
tested_status = significant_down  and deg_state = -1
tested_status = tested_not_significant and deg_state = 0
```

rather than independently generating new calls. The code should nevertheless
validate that every Phase 08 row preserved by Phase 09 reproduces the expected
`paper_deg` rule and that the `tested_status`-to-`deg_state` mapping is exact.

The direction is determined from the Phase 08 MAST log2 fold change:

```text
paper_deg = TRUE and logFC > 0  -> upregulated in AD
paper_deg = TRUE and logFC < 0  -> downregulated in AD
paper_deg = FALSE               -> not called differentially expressed
```

This last state applies only to a returned Phase 08 row represented by
`tested_status = tested_not_significant`. Phase 09 rows labeled
`present_but_filtered_min_pct`, `not_in_expression_matrix`, or
`contrast_not_estimable` are unavailable, not nonsignificant zeros, and must
not enter tested denominators.

The figure must not recalculate BH FDR within either mitochondrial scope.
Doing that would create a different testing family from Yu et al. and from the
existing Phase 08 `paper_deg` definition preserved by Phase 09.

## 5. Phase boundary

The current Phase 11 is pathway testing, not the archived global
multiple-testing phase assumed by the older version of this plan. This figure
must not read `results/minerva_production/11_multiple_testing/` and has no
Phase 11 significance overlay. Its only scientific data input is the validated
Phase 09 annotation bundle; the RDS manifest supplies display ordering.

## 6. Proposed figure panels

### Panel A: upregulated mitochondrial-related genes

Use the same general layout as Yu et al. Figure 1A.

- Rows: the six sex-APOE groups.
- Columns: the 54 fine cell types.
- Tile value: number of tested assay features in the selected mitochondrial
  scope with Phase 09 `tested_status = significant_up`.
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

### Panel B: downregulated mitochondrial-related genes

Use the same layout as Panel A.

- Rows: the six sex-APOE groups.
- Columns: the 54 fine cell types.
- Tile value: number of tested assay features in the selected mitochondrial
  scope with Phase 09 `tested_status = significant_down`.
- Suggested color: white to blue.

Panels A and B should use related, clearly labeled scales. If the maximum upregulated and downregulated counts differ greatly, either use separate scales and state that fact or use a shared maximum to support direct visual comparison.

### Panel C: APOE comparisons within females

Compare the Phase 08 MAST AD-versus-NCI calls preserved by Phase 09 between
female APOE groups:

```text
Female e2 versus Female e33
Female e4 versus Female e33
Female e2 versus Female e4
```

For each fine cell type, classify exact assay features in the selected
mitochondrial scope as:

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

Compare Phase 08 MAST AD-versus-NCI calls preserved by Phase 09 between
females and males within each APOE group:

```text
Female e2 versus Male e2
Female e33 versus Male e33
Female e4 versus Male e4
```

For each fine cell type, classify exact assay features in the selected
mitochondrial scope as:

- significant in both sexes with the same direction;
- significant only in females;
- significant only in males;
- significant in both with opposite directions; or
- not called in either sex.

This panel provides the most direct view of sex-dependent mitochondrial transcriptional responses.

## 7. Counts and denominators

Each tile should report both the DEG count and the number of exact assay
features in the selected mitochondrial scope that were tested in that
contrast.

The recommended annotation is:

```text
DEG count / tested mitochondrial assay features
```

For example:

```text
42 / 917
```

An optional second line or companion table should report:

```text
100 x DEG count / tested mitochondrial assay features
```

Using only raw counts can be misleading because the number of mitochondrial
features passing the Phase 08 detection filter can differ across cell types
and contrasts. Forty DEGs out of 500 tested features represent a different
proportion from forty DEGs out of 1,100 tested features.

For Panels C-E, pairwise classifications must use only the intersection of
exact assay features tested in both contrasts. Otherwise a feature could
appear unique merely because it was filtered or unmeasured in the comparison
group.

The companion table must record:

- features tested in the first contrast;
- features tested in the second contrast;
- features in the tested intersection; and
- features excluded from comparison because they were not jointly testable.

Every tile and gene-level output must also retain `analysis_universe`,
`included_mito_tiers`, and tier-specific tested counts. For
`all_mito_related`, the following identity must hold:

\[
\text{tested total}
=
\text{tested core}
+
\text{tested mtDNA noncoding}
+
\text{tested extended}
\]

The mtDNA-noncoding contribution may be zero because Phase 09 records these
genes as reference-only when they are absent from the expression matrices.

## 8. Ineligible and missing contrasts

If Phase 09 reports that a source contrast was not estimable, its tile must be
visually distinct from a true zero.

Recommended display:

- light grey tile;
- label `NE` for not estimable; and
- a companion-table field containing the terminal status and reason preserved
  by Phase 09.

A white tile with `0` should mean:

```text
the contrast was fitted, mitochondrial features were tested, and no features met the DEG rule
```

Grey `NE` should mean:

```text
the planned comparison could not be estimated or did not complete successfully
```

These meanings must never be merged.

## 9. Required source tables

The figure-generation code should read:

1. Phase 09 global status:

   ```text
   results/minerva_production/09_annotate_genes/annotation_status.tsv
   ```

2. Phase 09 checks and artifact manifest:

   ```text
   results/minerva_production/09_annotate_genes/annotation_checks.tsv
   results/minerva_production/09_annotate_genes/annotation_artifacts.tsv
   ```

3. Complete Phase 09 annotated DEG grid:

   ```text
   results/minerva_production/09_annotate_genes/deg_all_annotated.tsv.gz
   ```

4. RDS manifest for deterministic cell-population ordering:

   ```text
   config/minerva_rds_manifest.tsv
   ```

The script must not separately read Phase 03, raw Phase 08, Phase 10
similarity, Phase 11 pathway, archived downstream, or pseudobulk outputs.

## 10. Recommended outputs

### Main PDF

```text
results/minerva_production/15_figures/11_all_mito_related_mast_deg_landscape.pdf
```

The default name includes both `all_mito_related` and `mast` so neither the
gene scope nor statistical source can be mistaken. A `core_mito` sensitivity
rendering must use a distinct output path, for example:

```text
results/minerva_production/15_figures/11_core_mito_mast_deg_landscape.pdf
```

### Companion summary table

```text
results/minerva_production/15_figures/11_all_mito_related_mast_deg_landscape_tiles.tsv
```

One row per panel, comparison, fine cell type, and category should include:

- panel;
- method branch, fixed as `mast`;
- analysis universe and included Phase 09 tiers;
- cell type;
- sex and APOE definitions;
- contrast IDs;
- terminal statuses preserved by Phase 09;
- category;
- DEG count;
- total tested mitochondrial-feature denominator;
- tested core, mtDNA-noncoding, and extended-tier denominators;
- percentage;
- donor counts;
- MAST call definition;
- Phase 09 annotation source; and
- Phase 09 input checksum.

### Gene-level classification table

```text
results/minerva_production/15_figures/11_all_mito_related_mast_deg_landscape_genes.tsv.gz
```

This should contain every directly tested or jointly tested exact assay feature
and its classification, not only the aggregated tile counts. Retain
`feature_id_original`, HGNC and Ensembl annotations, `mapping_status`,
`mito_tier`, `genome_origin`, tested status, ternary state, log2 fold change,
within-contrast FDR, and `paper_deg` evidence for each source contrast.

### Checks table

```text
results/minerva_production/15_figures/11_all_mito_related_mast_deg_landscape_checks.tsv
```

Suggested checks include:

- Phase 09 status is `validated_complete`;
- every Phase 09 check passes;
- the annotated table matches its artifact byte count and SHA-256;
- method branch is always MAST;
- every plotted DEG has `paper_deg = TRUE`;
- every plotted feature belongs to the declared Phase 09 scope;
- exact feature keys are unique within contrast;
- upregulated rows have positive logFC;
- downregulated rows have negative logFC;
- paired categories are mutually exclusive;
- paired category totals equal the tested intersection;
- tier-specific denominators sum to the total denominator;
- no ineligible contrast is displayed as zero;
- donor counts match the Phase 09 preserved contrast metadata;
- all 54 fine cell types are represented or explicitly not estimable; and
- input checksums are unchanged during rendering.

## 11. Interpretation cautions

### DEG counts are influenced by power

A cell type can have more mitochondrial-related DEGs because it has:

- more donors;
- more nuclei contributing to the MAST fit;
- better-balanced AD and NCI groups;
- stronger gene detection;
- larger biological effects; or
- some combination of these factors.

Therefore, a larger DEG count is not automatically evidence of greater mitochondrial dysfunction.

### MAST uses nuclei, but donors determine biological replication

Phase 08 MAST uses nucleus-level observations and covariates. Many nuclei can
come from the same donor. The figure must display the donor counts preserved
in Phase 09 and should be interpreted together with the donor-coverage figure.

### A unique DEG is not automatically a unique biological effect

A gene may be called significant in one group and not another because the groups have different power. A `significant versus nonsignificant` pattern is not itself a formal proof that the two effects differ.

An opposite-direction call in which both groups are significant is stronger evidence of divergence than a one-sided significance call, but a formal interaction model is still the appropriate test of effect difference.

### The figure describes transcription, not mitochondrial function directly

The figure shows RNA differences among Phase 09 mitochondrial-related assay
features. It does not directly measure:

- mitochondrial number;
- oxygen consumption;
- ATP production;
- membrane potential;
- protein abundance; or
- causal mitochondrial dysfunction.

## 12. Suggested caption

> **Mitochondrial-related differential-expression signatures between AD and
> NCI across sex-APOE subgroups.** The displayed `all_mito_related` scope
> contains the Phase 09 `core_mito_protein`, `mtdna_noncoding`, and
> `mito_extended` tiers; non-mitochondrial features are excluded. Panels A and
> B show the numbers of upregulated and downregulated exact assay features,
> respectively, between AD and NCI within each of six sex-APOE groups across
> 54 fine cell types. Differentially expressed features were identified by
> Phase 08 MAST using the paper-comparable rule of within-contrast
> Benjamini-Hochberg FDR below 0.05 and absolute fold change above 1.3, with
> calls, testability, and mitochondrial tiers taken from the validated Phase
> 09 annotation bundle. Each tile reports the DEG count relative to the number
> of in-scope assay features tested in that contrast. Panels C and D compare
> AD-associated signatures among APOE groups within females and males,
> respectively. Panel E compares female and male signatures within each APOE
> group. Pairwise classifications use only exact assay features tested in both
> source contrasts. Same-direction, group-specific, and opposite-direction
> categories are descriptive DEG-call patterns, not formal interaction tests.
> Grey tiles denote contrasts that were not estimable. Donor counts are
> preserved Phase 09 contrast metadata.

## 13. Final decision summary

The planned figure should:

1. resemble Yu et al. Figure 1;
2. use `all_mito_related` by default and support a separately labeled
   `core_mito` rendering;
3. consume only the validated Phase 09 annotation bundle as its scientific
   data boundary;
4. preserve the Phase 08 MAST `paper_deg` definition carried by Phase 09;
5. count exact assay features without canonical-gene collapsing;
6. show total and tier-specific tested-feature denominators;
7. use tested-feature intersections for pairwise panels;
8. display donor counts and not-estimable contrasts clearly;
9. exclude archived Phase 11 multiple-testing outputs; and
10. preserve a feature-level companion table so every aggregated tile can be
    audited.
