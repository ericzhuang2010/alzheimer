# Processing pipeline phase summaries

This document summarizes the phases displayed in the processing-pipeline
figure at
[`results/figures/processing_pipeline/processing_pipeline.pdf`](../results/figures/processing_pipeline/processing_pipeline.pdf).
It covers Phases 01, 02, 03, 05, 08, 09, 10, and 11 only. The figure is a
selected scientific overview rather than the complete execution graph.

Two dependency details are important:

- Phase 08 reads the validated Phase 05 normalized objects directly. It does
  not use the Phase 06 or Phase 07 donor/nucleus eligibility thresholds.
- Phase 09 combines Phase 08 differential-expression results with the frozen
  Phase 03 annotation layer. Phase 03 therefore has a downstream role even
  though Phase 05 and Phase 08 occur between them in the displayed sequence.

In the paths below, `<environment>` is typically `local_pilot` or
`minerva_production`.

## Phase 01 — Audit Seurat inputs

**Purpose.** Phase 01 establishes that each input Seurat object is readable,
structurally valid, and scientifically usable before any expression data are
transformed. It is a read-only audit: the source RDS files are never modified.

**Inputs.** Each task reads one enabled Seurat RDS, the RDS manifest, the
shared analysis configuration, and the independent master cell-metadata table.

**Main processing.** The audit locates the RNA raw-count matrix and checks that
it is sparse, nonnegative, and integer-valued. It verifies feature and barcode
identifiers, inventories assays and layers, reconciles donor and fine-cell-type
metadata by barcode, and confirms that the 13 prespecified mtDNA
protein-coding genes are present. It also records whether a pre-existing
normalized layer is available, but does not treat that layer as a substitute
for the uniform Phase 05 normalization.

**Outputs and handoff.** For each RDS, Phase 01 writes an audit summary,
feature inventory, cell-type inventory, donor inventory, validation checks,
and task status under `results/<environment>/01_audit/`. Phase 02 uses the
donor inventories to build RDS-specific cohort intersections, while Phase 03
uses the feature inventories to create the frozen annotation layer.

**Implementation and documentation.** The scientific script is
[`scripts/01_audit_seurat_inputs.R`](../scripts/01_audit_seurat_inputs.R).
See [Phase 01 audit explained](phase_01_explained.md) for the complete checks
and output schemas.

## Phase 02 — Build the clinical cohort

**Purpose.** Phase 02 creates the authoritative donor-level analytic cohort
and attaches consistently derived clinical covariates. The global production
cohort contains 276 eligible donors; each RDS also receives its own
intersection with those donors.

**Inputs.** The phase uses the clinical table, master cell metadata, validated
Phase 01 audit summaries, and the Phase 01 donor inventories.

**Main processing.** Donor identifiers are normalized to fixed-width
`projid` values and joined by key rather than row order. The phase derives
diagnosis, sex, APOE group, age-at-death variables, PMI variables, and scaled
model covariates. It applies the prespecified diagnosis, sex-concordance, APOE,
age, and PMI rules; verifies one clinical row per retained donor; and performs
a donor-aggregated XIST/UTY expression check for reported sex.

**Outputs and handoff.** Phase 02 writes the global 276-donor cohort,
RDS-specific cohort tables, the exclusion flow, sex-by-APOE-by-diagnosis donor
counts, sex-linked expression QC, checks, and provenance under
`results/<environment>/02_cohort/`. Phase 05 joins these donor-level fields to
the nuclei in each normalized working object.

**Implementation and documentation.** The scientific script is
[`scripts/02_build_cohort.R`](../scripts/02_build_cohort.R). See
[Phase 02 cohort results explained](phase_02_explained.md) for the observed
production cohort and supporting files.

## Phase 03 — Freeze mitochondrial gene sets and identifiers

**Purpose.** Phase 03 freezes a versioned biological annotation contract so
that all later analyses use the same gene identities and mitochondrial
definitions. It answers what each assay feature represents, whether it is
mitochondrial, whether it is measured in each RDS, and whether it has usable
raw counts; it does not test AD-versus-NCI effects.

**Inputs.** The phase combines the Phase 01 feature inventories with the
checksummed GENCODE v44 GRCh38 annotation, Human MitoCarta 3.0, the enabled RDS
manifest, and the shared scientific configuration.

**Main processing.** Phase 03 validates the reference checksums, parses
GENCODE gene records, builds an alias dictionary, maps every original assay
feature to GENCODE and MitoCarta, identifies the 13 mtDNA protein-coding genes,
and records measured and preliminary test-eligibility states per RDS. It also
normalizes MitoCarta pathway membership into tabular and GMT artifacts. The
large Seurat objects are not reopened or modified.

**Outputs and handoff.** Outputs under
`results/<environment>/03_annotations/` include the GENCODE mapping,
alias mapping, MitoCarta inventory and measured-gene tables, mtDNA gene list,
tested-gene universe, MitoCarta pathways, checks, manifest, and status. Phase
09 uses these artifacts when attaching stable identifiers and mitochondrial
tiers to the Phase 08 DEG results.

**Implementation and documentation.** The scientific script is
[`scripts/03_build_mito_annotations.R`](../scripts/03_build_mito_annotations.R).
See [Phase 03 annotation results explained](phase_03_explained.md) for the full
mapping rules and file descriptions.

## Phase 05 — Normalize expression and attach metadata

**Purpose.** Phase 05 creates the analysis-ready Seurat working objects used
by the cell-level MAST branch. It attaches validated donor and QC metadata and
recomputes the RNA normalized `data` layer while preserving the raw `counts`
layer and the source RDS.

**Inputs.** Each task reads one raw Seurat RDS, its Phase 02 cohort table,
the applicable Phase 04 QC tables and non-exclusionary flags, and the shared
normalization configuration. Phase 04 is not displayed in the selected figure
but remains an input to the metadata attachment step.

**Main processing.** Legacy objects are upgraded in memory with
`UpdateSeuratObject()` when required. Donor-level fields such as diagnosis,
sex, APOE, age, and PMI are joined by key, and mitochondrial QC fields are
attached separately. Seurat `NormalizeData` then applies RNA `LogNormalize`
with scale factor 10,000. All source nuclei are retained; `cohort_included`
marks the analytic subset rather than physically removing other nuclei.

**Validation and handoff.** The phase verifies unchanged feature/cell
dimensions, exact preservation of the serialized raw-count matrix, agreement
of sampled values with `log1p(count / cell_total * 10000)`, complete metadata
joins, successful reload, and unchanged source checksums. It writes normalized
RDS files plus formula samples, validation tables, artifact manifests, and
statuses under `results/<environment>/05_normalized/`. The validated
normalized RDS is the direct scientific input to Phase 08.

**Implementation and documentation.** The scientific script is
[`scripts/05_normalize_and_attach_metadata.R`](../scripts/05_normalize_and_attach_metadata.R).
The design is described in the archived
[mitochondria, sex, APOE research plan](previous_plans/mitochondria_sex_apoe_research_plan.md#12-phase-05-attach-metadata-and-normalize-with-seurat-normalizedata).

## Phase 08 — Yu-compatible cell-level MAST differential expression

**Purpose.** Phase 08 reproduces the Yu et al. cell-level differential-
expression design as closely as possible. Within each of 54 fine cell types,
it compares AD with NCI separately for Female/Male and APOE e2/e33/e4,
creating six planned contrasts per cell type and 324 planned production status
rows.

**Inputs and analysis population.** Phase 08 reads the validated Phase 05 RNA
normalized `data` layer and its attached metadata. For each fine-cell-type and
sex-by-APOE stratum, it uses every nucleus with `cohort_included == TRUE` and
diagnosis AD or NCI. It does **not** apply the Phase 07 thresholds of 20 nuclei
per donor-cell-type or five donors per diagnosis arm. Low counts are warnings;
the operational minimum is three cells in each diagnosis group, as required
before Seurat dispatches the MAST fit.

**Main processing.** Seurat `FindMarkers(test.use = "MAST")` is run with
`min.pct = 0.10`, no pre-fit log-fold-change threshold, and latent covariates
for RNA depth, scaled age at death, and scaled PMI. Effects are always AD minus
NCI. Within each completed contrast, BH FDR is calculated over the genes
returned by `FindMarkers`; a Yu-compatible DEG requires `FDR < 0.05` and
`abs(logFC) > log2(1.3)`.

**Outputs and handoff.** Per-RDS outputs under
`results/<environment>/08_mast/` include the contrast manifest, complete DEG
table, model diagnostics, contrast statuses, checks, artifact inventory, and
task status. A separate bundle compares the results with Yu Supplemental Table
S1. Phase 09 consumes the validated Phase 08 result and status bundles.

**Interpretive boundary.** MAST is the paper-comparability branch. Nuclei from
the same donor are not independent biological replicates, so this branch must
not be presented as replacing donor-level pseudobulk inference.

**Implementation and documentation.** The scientific script is
[`scripts/08_run_mast.R`](../scripts/08_run_mast.R). See the
[Phase 08 Yu DEG alignment plan](phase_08_deg/phase_08_yu_deg_alignment_plan.md)
for the model, DEG rule, and validation targets.

## Phase 09 — Annotate DEG genes

**Purpose.** Phase 09 integrates the Phase 08 statistical results with frozen
gene identifiers and mitochondrial definitions. It preserves every Phase 08
statistic while making gene identity, mitochondrial tier, measurement status,
testability, and DEG state explicit.

**Inputs.** The phase requires validated Phase 08 result bundles, the Phase 03
GENCODE/MitoCarta annotation artifacts, a frozen HGNC snapshot, and the
prespecified Reactome mitochondrial extended-tier reference.

**Main processing.** Exact assay features remain the row identity. Phase 09
adds stable Ensembl IDs, approved HGNC symbols, aliases, biotypes, chromosome,
genome origin, MitoCarta localization, and deterministic mapping evidence. It
classifies features into core MitoCarta proteins, mtDNA noncoding genes,
prespecified extended mitochondrial genes, or the appropriate non-core state.
It then builds a complete feature-by-contrast grid that distinguishes tested
genes, `min.pct`-filtered genes, genes absent from an expression matrix, and
non-estimable contrasts. Missing or filtered tests are not converted to
nonsignificant zeros.

**Outputs and handoff.** Outputs under
`results/<environment>/09_annotate_genes/` include
`gene_annotation_master.tsv.gz`, `deg_all_annotated.tsv.gz`, mitochondrial
subsets and inventories, unresolved mappings, QC tables, checks, artifacts,
and status. Phase 10 consumes the complete annotated table and explicit DEG
states. Phase 09 does not refit MAST, recalculate p-values, or run pathway
enrichment.

**Implementation and documentation.** The scientific script is
[`scripts/09_annotate_mitochondrial_genes.R`](../scripts/09_annotate_mitochondrial_genes.R).
See the [Phase 09 annotation plan](phase_09_annotate_genes/phase_09_annotate_mitochondrial_genes_plan.md)
for the identifier hierarchy, mitochondrial tiers, and output schemas.

## Phase 10 — Calculate mitochondrial similarity scores

**Purpose.** Phase 10 measures how similarly or differently AD-associated
mitochondrial expression states behave across paired sex or APOE strata. It
produces Yu-style cross-cell-type similarity scores, inference, ranks, and
prespecified high/low tails; it does not draw figures or run enrichment.

**Inputs.** The only scientific input bundle is the validated combined Phase
09 annotation output, principally `gene_annotation_master.tsv.gz` and
`deg_all_annotated.tsv.gz` with explicit ternary DEG states and missing-state
reasons.

**Main processing.** Each tested state is encoded as significant up (`+1`),
nonsignificant (`0`), or significant down (`-1`). Matched states are
concatenated across fine cell types before calculating one score per feature
and comparison; cell-type-specific scores are not averaged. Concordant
significant pairs contribute `+1`, one-significant/one-nonsignificant pairs
contribute `-0.5`, opposite significant pairs contribute `-1`, and two
nonsignificant states contribute zero while remaining in the denominator.
Unavailable pairs are excluded and their coverage is reported.

**Inference and ranking.** Phase 10 evaluates six comparison families,
including Female-versus-Male and APOE contrasts. Production inference uses
10,000 deterministic permutations and plus-one empirical p-values. BH FDR is
applied within each comparison-by-analysis-universe family. Eligible features
are ranked from most concordant to most divergent, and deterministic top/bottom
10-, 25-, and 200-gene sets are stored for downstream panels and enrichment.
This state-pair coverage criterion is separate from the Phase 07 donor/nucleus
thresholds that Phase 08 no longer uses.

**Outputs and handoff.** Outputs under
`results/<environment>/10_similarity/` include feature, comparison, and
dimension manifests; the complete state-pair table; similarity results;
rank-set tables; permutation diagnostics; QC checks; artifact inventory; and
status. Phase 11 consumes these validated scores, ranks, tails, and coverage
fields.

**Implementation and documentation.** The scientific script is
[`scripts/10_calculate_mitochondrial_similarity.R`](../scripts/10_calculate_mitochondrial_similarity.R).
See the [Phase 10 similarity plan](phase_10_similarity/phase_10_mitochondrial_similarity_plan.md)
for the exact score, comparison families, inference, and selection rules.

## Phase 11 — Prepare mitochondrial pathway and panel data

**Purpose.** Phase 11 converts the frozen Phase 10 rankings into pathway-
enrichment results and figure-ready similarity/pathway tables for analogues of
Yu Figures 3–6. It prepares data only; figure rendering remains a separate
workflow.

**Inputs.** The phase reads the validated Phase 10 results, rank sets, state
pairs, feature manifest, and comparison manifest. It independently freezes
and validates two pathway collections: Human MSigDB C2:CP canonical pathways
for the primary Yu-style comparison and MitoCarta3.0 MitoPathways for focused
mitochondrial interpretation.

**Main processing.** Phase 11 constructs comparison- and universe-specific
ranking-eligible backgrounds, maps exact Phase 10 features to unique current
HGNC symbols, and creates 24 high/low 200-tail queries (six comparisons × two
analysis universes × two tails). It tests each query against every eligible
pathway using a one-sided hypergeometric overrepresentation test, retains
explicit non-testable rows, and applies BH correction within each query and
pathway collection. It also reshapes the stored Phase 10 state-pair counts and
ranked features into panel-ready long tables without changing the Phase 10
ordering or inference.

**Outputs and handoff.** Outputs under
`results/<environment>/11_pathway/` include pathway reference and membership
tables, exact backgrounds and queries, the complete ORA grid, overlap genes,
similarity panel data, pathway panel data, downstream panel definitions, QC
checks, artifacts, and status. Later figure scripts consume these compact,
validated tables rather than rereading MAST results or recomputing similarity.
No PDF, PNG, SVG, or assembled figure belongs in the Phase 11 output bundle.

**Implementation and documentation.** The scientific script is
[`scripts/11_prepare_mitochondrial_pathway_data.R`](../scripts/11_prepare_mitochondrial_pathway_data.R).
See the [Phase 11 pathway-data plan](phase_11_pathway/phase_11_mitochondrial_pathway_data_plan.md)
for the reference freezes, ORA families, and downstream panel schemas.

## Selected-phase handoff summary

The displayed scientific handoff can be summarized as follows:

1. Phase 01 inventories and validates each raw Seurat object.
2. Phase 02 defines the eligible donors and clinical covariates.
3. Phase 03 freezes feature identity and mitochondrial membership.
4. Phase 05 attaches metadata and produces uniformly normalized working
   objects.
5. Phase 08 runs the all-cohort-included-nuclei Yu-compatible MAST contrasts
   directly from Phase 05.
6. Phase 09 joins the Phase 08 statistics to the Phase 03 annotation contract.
7. Phase 10 converts the annotated DEG states into cross-cell-type similarity
   scores and ranks.
8. Phase 11 converts the frozen ranks into pathway-enrichment and panel-ready
   data.
