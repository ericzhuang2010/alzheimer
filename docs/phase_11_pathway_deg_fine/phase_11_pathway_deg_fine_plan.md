# Phase 11: Fine-cell DEG pathway and mitochondrial-program analysis

## Status

**Completed and validated on September 14, 2026.**

The production output directory will be:

```text
results/minerva_production/11_pathway_deg_fine/
```

This will be a sibling analysis to:

```text
results/minerva_production/11_pathway_similarity/
```

The two analyses answer different questions:

- `11_pathway_similarity` asks which pathways occur among genes with relatively
  similar or different AD responses across sex/APOE groups.
- `11_pathway_deg_fine` will ask which pathways occur directly among the
  AD-versus-NCI DEGs in each fine cell type and sex/APOE group.

No Phase 11 similarity result, KDA result, or upstream DEG result will be
overwritten.

### Production execution summary

The registered global `pathway_deg_fine` task completed locally with the
Minerva production configuration and published a hash-valid bundle in 44.4
seconds. The bundle contains:

- 324 planned contrasts, including 321 estimable and three explicit
  non-estimable contrasts;
- 972 combined, AD-up, and AD-down query definitions;
- 199 prespecified program definitions across the legacy-4, broad-46, and
  complete-149 collections;
- 193,428 primary ORA records, of which 67,730 were testable and 1,540 met
  local BH FDR < 0.05;
- 38,606 companion ORA records for the 194 KDA-effective queries; and
- all 58 prespecified global, stratum, and slide-level legacy checkpoints
  reproduced exactly.

All 36 blocking structural, provenance, numerical, FDR, and reconciliation
checks passed. The automated production-bundle test passed, and a repeated
pipeline invocation resumed without recomputation after validating every
declared artifact hash.

## 1. Main objective

Run a reproducible pathway/program analysis for the ROSMAP fine-cell DEG
contrasts:

```text
54 fine cell types × 6 sex/APOE groups = 324 planned AD-versus-NCI contrasts
```

The six groups are:

- female APOE ε2;
- female APOE ε3/ε3;
- female APOE ε4;
- male APOE ε2;
- male APOE ε3/ε3; and
- male APOE ε4.

Of the 324 planned contrasts, 321 were estimable in Phase 08. The three
non-estimable male-ε2 contrasts must remain explicit unavailable records rather
than being treated as zero-DEG results.

The analysis will answer:

1. Which mitochondrial programs are over-represented among the DEGs in each
   fine-cell × sex/APOE contrast?
2. Is enrichment carried by AD-up genes, AD-down genes, or both?
3. Which programs recur across related fine cell types or broad cell classes?
4. Which program patterns are concentrated in one sex/APOE group?
5. Do conclusions remain visible after expanding from the current four modules
   to broad and detailed MitoCarta pathways?
6. How do the direct fine-cell DEG results compare with the earlier
   KDA-effective-query analysis?

## 2. Key scientific decision

### 2.1 Primary analysis: pre-network fine-cell DEGs

The primary analysis will use the original Phase 08/09 mitochondrial DEG
results before network intersection.

This is important because a pathway analysis of KDA-effective genes can be
affected by whether genes occur in a particular Bayesian network. The
pre-network analysis more directly answers:

> What mitochondrial biology is represented among the significant AD-versus-NCI
> genes in this fine cell type and sex/APOE group?

All 324 planned contrasts will receive a status. All 321 estimable contrasts
will be evaluated, including contrasts with zero, one, or two mitochondrial
DEGs. Small or empty queries will receive explicit statuses rather than being
silently removed.

### 2.2 KDA-aligned companion analysis

A separate compatibility profile will reproduce and expand the existing
analysis of the 194 KDA-eligible effective query lists.

This profile answers:

> Which mitochondrial programs were represented in the exact DEG lists that
> were passed to `call_key_drivers`?

It will use:

- `included_at_thresholds == TRUE`;
- `effective_member == TRUE`; and
- each call's exact network-intersected mitochondrial background.

The KDA-aligned profile must remain clearly labeled because it is downstream
of network coverage and the three-gene KDA execution threshold.

## 3. DEG and direction definitions

Use the frozen Phase 08 `paper_deg` definition:

```text
within-contrast BH FDR < 0.05
and |log2FC| > log2(1.3)
```

Phase 08 MAST also required expression in at least 10% of AD or NCI nuclei
before returning a gene for testing.

For every estimable contrast, create three query modes:

1. `AD_any_mito`: significant AD-up and AD-down mitochondrial genes combined;
2. `AD_up_mito`: significant genes with `logFC > 0`; and
3. `AD_down_mito`: significant genes with `logFC < 0`.

The combined query detects mitochondrial remodeling without assigning a common
direction. The separate up and down queries are required before describing a
program as increased or decreased in AD.

The analysis must not infer a formal disease-by-sex or disease-by-APOE
interaction from differences in enrichment. These remain stratified
AD-versus-NCI results.

## 4. Gene universe and statistical background

### 4.1 Primary mitochondrial universe

The primary universe is:

```text
mito_tier == core_mito_protein
```

For each fine-cell × sex/APOE contrast, the background is the unique current
HGNC symbols for core-MitoCarta assay features that were actually tested in
that contrast.

Admitted tested states are:

- `significant_up`;
- `significant_down`; and
- `tested_not_significant`.

The following are missing or unavailable, not tested non-DEGs:

- `present_but_filtered_min_pct`;
- `not_in_expression_matrix`;
- `contrast_not_estimable`; and
- reference-only genes.

A tested mitochondrial gene remains in the background even when it belongs to
no tested pathway. This prevents enrichment from being inflated by defining
the background from pathway members.

### 4.2 Gene identity

The ORA unit is the unique current HGNC symbol:

```text
symbol_hgnc_current
```

The implementation will:

- retain the source assay feature;
- map to a current approved symbol using the Phase 09 mapping;
- collapse duplicate features to one symbol within a query/background;
- report every mapping loss and duplicate collapse; and
- require every query gene to occur in its matching background.

## 5. Pathway and program collections

Three prespecified mitochondrial collections will be run.

### 5.1 Legacy four-module benchmark

Retain the four frozen modules from:

```text
config/phase13_respiratory_modules.tsv
```

They are:

1. 13 mtDNA-encoded OXPHOS genes;
2. 86 nuclear-encoded structural OXPHOS genes;
3. 155 mitochondrial-translation genes; and
4. 19 MIB/MICOS inner-membrane genes.

This collection preserves continuity with the current analysis document and
presentation. It is a benchmark collection, not the comprehensive discovery
collection.

### 5.2 Broad MitoCarta program collection

Use the 46 MitoCarta3.0 pathways at hierarchy depths 1 and 2 as the primary
expanded collection:

- seven top-level mitochondrial systems; and
- 39 broad level-2 programs.

The seven top-level systems are:

1. Metabolism;
2. Mitochondrial central dogma;
3. Mitochondrial dynamics and surveillance;
4. OXPHOS;
5. Protein import, sorting and homeostasis;
6. Signaling; and
7. Small-molecule transport.

The 39 level-2 programs are:

- **Metabolism:** amino-acid metabolism, carbohydrate metabolism,
  detoxification, electron carriers, lipid metabolism, metals and cofactors,
  nucleotide metabolism, sulfur metabolism, and vitamin metabolism.
- **Mitochondrial central dogma:** translation, mtDNA maintenance, and mtRNA
  metabolism.
- **Dynamics and surveillance:** apoptosis, autophagy, cristae formation,
  fission, fusion, intramitochondrial membrane interactions, mitophagy,
  organelle contact sites, and trafficking.
- **OXPHOS:** Complex I, Complex II, Complex III, Complex IV, Complex V,
  cytochrome C, OXPHOS assembly factors, OXPHOS subunits, and respirasome
  assembly.
- **Protein handling:** protein homeostasis and protein import/sorting.
- **Signaling:** calcium homeostasis, immune response, and cAMP–PKA signaling.
- **Small-molecule transport:** ABC transporters, calcium uniporter, SLC25A
  family, and sideroflexins.

This 46-pathway collection is the primary balance between biological coverage,
interpretability, and multiple-testing burden.

### 5.3 Complete MitoCarta collection

Run all 149 MitoCarta3.0 MitoPathways as a prespecified supplemental analysis.
This adds 103 detailed hierarchy-depth-3 pathways, including specific:

- respiratory-chain subunits and assembly systems;
- mitochondrial ribosome and translation machinery;
- mtDNA and mtRNA maintenance processes;
- import complexes and protein-quality-control systems;
- amino-acid, carbohydrate, lipid, vitamin, metal, and cofactor pathways; and
- mitochondrial transport and membrane-remodeling processes.

The full collection must be interpreted with hierarchy-aware redundancy
reduction. Multiple parent and child terms supported by the same genes are one
biological theme, not independent discoveries.

### 5.4 Reference authority

The authoritative pathway source is:

```text
data/reference/Human.MitoCarta3.0.xls
```

Use sheet:

```text
C MitoPathways
```

The implementation will use the same normalization rules as Phase 11
similarity and independently reconcile the result against:

```text
results/minerva_production/11_pathway_similarity/pathway_reference_manifest.tsv
results/minerva_production/11_pathway_similarity/pathway_membership_long.tsv.gz
```

The expected reference contains:

- 149 pathways;
- 3,904 pathway-gene memberships; and
- 1,035 unique symbols.

Phase 11 similarity P values and 200-gene tail selections are not inputs to the
new analysis.

## 6. Broader non-mitochondrial pathways

Whole-transcriptome pathways such as lysosome–mTOR signaling, cytosolic
ribosomes, ubiquitin/proteasome, inflammatory signaling, complement, cholesterol
metabolism, and synaptic biology must not be tested using a core-mitochondrial
background.

If desired, those pathways should be a separate future profile using:

- all genes tested in the corresponding Phase 08 contrast as background; and
- all significant Phase 08 genes, or the non-MT KDA drivers, as the query.

That profile is deferred from the required implementation so that the first
release answers the mitochondrial fine-DEG question cleanly.

## 7. Required inputs

### 7.1 Primary DEG inputs

```text
results/minerva_production/09_annotate_genes/annotation_status.tsv
results/minerva_production/09_annotate_genes/annotation_checks.tsv
results/minerva_production/09_annotate_genes/annotation_artifacts.tsv
results/minerva_production/09_annotate_genes/deg_mito_core.tsv.gz
```

Phase 09 supplies the complete mitochondrial tested-state grid and current gene
identity. Phase 08 files under the following directory provide independent
contrast and DEG reconciliation:

```text
results/minerva_production/08_deg_fine/*.yu_mast_contrast_manifest.tsv
results/minerva_production/08_deg_fine/*.yu_mast_contrast_status.tsv
results/minerva_production/08_deg_fine/*.yu_mast_de.tsv.gz
```

### 7.2 KDA-aligned companion inputs

```text
results/minerva_production/20_sex_apoe_kda_combo/combo_run_manifest.tsv
results/minerva_production/20_sex_apoe_kda_combo/combo_query_members.tsv.gz
results/minerva_production/12_rosmap_sex_apoe_mito_kda_runs/kda_background_members.tsv.gz
```

### 7.3 Reference inputs

```text
config/phase13_respiratory_modules.tsv
data/reference/Human.MitoCarta3.0.xls
results/minerva_production/11_pathway_similarity/pathway_reference_manifest.tsv
results/minerva_production/11_pathway_similarity/pathway_membership_long.tsv.gz
```

All required inputs must be checksum-validated before analysis begins.

### 7.4 Explicit non-inputs

The primary analysis must not use:

- Phase 10 similarity scores or high/low rank tails;
- Phase 11 similarity ORA P values;
- KDA-returned driver genes to define the primary DEG query;
- pathway results selected from a figure or discussion;
- SEA-AD results; or
- a whole-genome background for mitochondrial-only ORA.

## 8. ORA calculation

For each eligible
`contrast × query_mode × pathway_collection × pathway`, define:

- `N`: unique tested mitochondrial background genes;
- `n`: unique DEG query genes;
- `M`: background genes belonging to the pathway; and
- `k`: query genes belonging to the pathway.

Calculate the one-sided hypergeometric probability of observing at least `k`
pathway genes:

```r
p_value <- phyper(
  q = k - 1L,
  m = M,
  n = N - M,
  k = n,
  lower.tail = FALSE
)
```

Also retain:

- overlap genes;
- `gene_ratio = k / n`;
- `background_ratio = M / N`;
- fold enrichment;
- pathway hit rate;
- the complete 2 × 2 contingency table; and
- pathway hierarchy and source order.

### Testability

For the broad and complete MitoCarta collections:

- require query size `n >= 3`;
- require background pathway size `M >= 5`;
- require `M < N`; and
- require at least 30% of the source pathway to be represented in the
  contrast-specific background.

Tested pathways with `5 <= M <= 9` will be labeled
`small_pathway_lower_confidence`.

Zero-overlap pathways that otherwise meet testability rules remain tested with
`p = 1`. No minimum-overlap filter will be applied before P-value calculation.

The legacy four-module benchmark will reproduce the current four-test
calculation exactly. Any additional stricter testability label will be stored
as a sensitivity annotation rather than changing the compatibility result.

## 9. Multiple-testing correction

The three pathway collections have different roles and therefore separate,
prespecified FDR families.

### Legacy benchmark

Apply BH across the four legacy modules within each KDA-aligned call, matching
the existing calculation.

### Primary broad collection

Apply BH across all testable depth-1/2 MitoCarta pathways within each:

```text
fine-cell contrast × query mode
```

This is the primary per-query FDR.

### Complete supplemental collection

Apply BH across all testable members of the complete 149-pathway collection
within each:

```text
fine-cell contrast × query mode
```

### Study-wide sensitivity

Also calculate a stricter global BH value across all eligible fine-cell tests
within:

```text
pathway collection × query mode
```

Primary significance is `local_fdr_bh < 0.05`. Study-wide FDR is a sensitivity
result and must not replace the local family after looking at results.

The legacy four-module q-values, broad-collection q-values, and complete-
collection q-values must never be compared as if they came from the same
testing family.

## 10. Cross-cell and sex/APOE summaries

Create summaries by:

- fine cell type;
- sex/APOE group;
- broad cell class;
- pathway;
- query direction; and
- pathway hierarchy.

For every pathway and group, report:

- number of structurally available contrasts;
- number with a testable query;
- number significantly enriched;
- number enriched among AD-up genes;
- number enriched among AD-down genes;
- median and range of fold enrichment;
- union and recurrence count of overlap genes; and
- whether the signal depends on one fine cell type.

These are descriptive recurrence summaries. Fine cell types share donors and
must not be described as independent biological replications.

Build a pathway-overlap map using gene-set Jaccard similarity and hierarchy.
This will allow repeated parent/child terms supported by the same genes to be
collapsed into representative biological themes.

## 11. Required output bundle

Write all outputs under:

```text
results/minerva_production/11_pathway_deg_fine/
```

Required files:

```text
fine_deg_pathway_status.tsv
fine_deg_pathway_checks.tsv
fine_deg_pathway_artifacts.tsv
fine_deg_pathway_reference_manifest.tsv
fine_deg_pathway_program_manifest.tsv
fine_deg_pathway_contrast_manifest.tsv
fine_deg_pathway_background_manifest.tsv
fine_deg_pathway_background_genes.tsv.gz
fine_deg_pathway_query_manifest.tsv
fine_deg_pathway_query_genes.tsv.gz
fine_deg_pathway_ora.tsv.gz
fine_deg_pathway_significant_results.tsv.gz
fine_deg_pathway_fine_cell_summary.tsv
fine_deg_pathway_broad_cell_summary.tsv
fine_deg_pathway_sex_apoe_summary.tsv
fine_deg_pathway_redundancy_map.tsv.gz
kda_effective_query_program_ora.tsv.gz
legacy_four_module_reconciliation.tsv
README.md
```

The complete ORA table must include significant, nonsignificant, not-testable,
empty-query, and non-estimable records. The significant-results table is only
a convenience subset and is not the authoritative result.

No PDF, PNG, PowerPoint, or manually selected pathway list belongs in the
production data bundle.

## 12. Implementation files

Add:

```text
config/phase11_pathway_deg_fine.yml
scripts/11_run_fine_deg_pathway_analysis.R
tests/test_phase11_pathway_deg_fine.R
```

Update:

```text
scripts/run_pipeline.R
config/minerva_shared.yml
.gitignore
```

Register one global task mode:

```text
pathway_deg_fine
```

One global task is sufficient because the primary mitochondrial Phase 09 table
is much smaller than the complete transcriptome-wide annotated table. The task
must reject `--rds-id`.

## 13. Construction workflow

1. Validate Phase 08 and Phase 09 statuses, checks, schemas, row counts, and
   artifact hashes.
2. Normalize the four legacy modules and MitoCarta pathway hierarchy.
3. Reconcile normalized MitoCarta memberships with the validated Phase 11
   similarity reference tables.
4. Build all 324 contrast records and preserve the three non-estimable rows.
5. Build contrast-specific tested mitochondrial backgrounds.
6. Build combined, AD-up, and AD-down DEG queries.
7. Run legacy-four, broad-46, and complete-149 ORA families.
8. Calculate local and study-wide BH corrections.
9. Build fine-cell, broad-cell, sex/APOE, and redundancy summaries.
10. Run the KDA-effective-query compatibility profile.
11. Reconcile legacy four-module checkpoints with the current analysis and
    presentation calculations.
12. Write to a process-specific staging directory.
13. Validate every output, hash all artifacts, and publish the status file last.

## 14. Validation requirements

### Structural checks

- exactly 54 fine cell types;
- exactly six sex/APOE strata;
- exactly 324 planned contrast records;
- 321 estimable and three explicitly non-estimable contrasts;
- exactly three query modes per contrast;
- exactly four legacy modules;
- exactly 46 broad MitoCarta pathways;
- exactly 149 complete MitoCarta pathways;
- unique query, background, and ORA keys; and
- no partial result directory accepted as complete.

### Query/background checks

- `paper_deg` is reproduced exactly from stored fields;
- all AD-up query genes have positive `logFC`;
- all AD-down query genes have negative `logFC`;
- every query is a subset of its exact background;
- no pathway-membership filter changes `N` or `n`;
- mapping losses and duplicate collapses are explicit;
- empty and small queries remain in the manifests; and
- primary backgrounds do not depend on Bayesian-network coverage.

### Numerical checks

- contingency cells are nonnegative and sum to `N`;
- `k <= n`, `k <= M`, `n <= N`, and tested `M < N`;
- stored P values reproduce the frozen `phyper` expression;
- zero-overlap tests have `p = 1`;
- an audited subset matches one-sided Fisher exact tests;
- BH values reproduce independently within every declared family; and
- toy examples with known answers pass.

### Reconciliation checks

- MitoCarta normalization matches the frozen 149-pathway reference;
- Phase 09 DEG counts reconcile to Phase 08 source tables;
- the KDA companion contains the same 194 eligible calls as the combo manifest;
- KDA-effective members and backgrounds reconcile exactly to their source
  files; and
- the legacy four-module calculation reproduces the existing analysis and
  slide checkpoints before expanded results are interpreted.

## 15. Execution plan

After implementation, run a local or read-only smoke test first. Then run
Minerva production:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway_deg_fine \
  --dry-run
```

Expected graph:

```text
one global:pathway_deg_fine task
```

Execute:

```bash
Rscript scripts/run_pipeline.R \
  --config config/minerva_shared.yml \
  --execution-config config/minerva_production_execution.yml \
  --phase pathway_deg_fine
```

Do not run one job per RDS and do not pass `--rds-id`.

## 16. Interpretation rules

Permitted statements include:

- “The pathway was enriched among AD-up mitochondrial DEGs in this fine-cell
  and sex/APOE contrast.”
- “The program recurred across several related fine cell types.”
- “The detailed terms reduce to one shared OXPHOS theme.”

Do not claim:

- that enrichment proves pathway activity or respiratory function;
- that an enriched program is controlled by a returned key driver;
- that significant enrichment in one stratum and no enrichment in another is
  a significant interaction;
- that fine-cell recurrence represents independent donor replication; or
- that multiple overlapping parent/child pathways are separate mechanisms.

MAST is nucleus-level, not donor-level primary inference. Leading findings
should be followed by donor-level pseudobulk pathway scores or formal
disease-by-sex/APOE interaction models.

## 17. Acceptance criteria

The phase is complete when:

- the entire validated bundle exists under
  `results/minerva_production/11_pathway_deg_fine/`;
- every one of the 324 planned contrasts has an explicit status;
- combined, AD-up, and AD-down queries reconcile to Phase 09;
- broad-46 and complete-149 MitoCarta analyses pass all numerical and FDR
  checks;
- the KDA-aligned companion reproduces the previous four-module calculation;
- pathway redundancy is explicit;
- all inputs and outputs are checksummed;
- the status is `validated_complete`; and
- no upstream result is modified.

## 18. Implementation checklist

### Freeze

- [x] Freeze the scientific configuration and output schemas.
- [x] Freeze the 46-pathway broad collection from MitoCarta hierarchy depths
      1 and 2.
- [x] Freeze the complete 149-pathway collection and source checksum.
- [x] Freeze local and study-wide FDR families.
- [x] Freeze testability and small-query labels.

### Implement

- [x] Add the scientific config.
- [x] Add the global analysis script.
- [x] Add automated tests and toy ORA cases.
- [x] Register `pathway_deg_fine` in the pipeline.
- [x] Build complete query and background manifests.
- [x] Implement all three pathway collections and query directions.
- [x] Implement hierarchy-aware redundancy summaries.
- [x] Implement KDA-effective-query compatibility analysis.
- [x] Write atomic status, checks, and artifact manifests.

### Validate and run

- [x] Run the local smoke test.
- [x] Review mapping and small-query attrition.
- [x] Reproduce the current four-module checkpoints.
- [x] Run the Minerva dry run.
- [x] Execute the global production task.
- [x] Validate and interpret the production bundle.
