# Phase 19 Endophenotype GWAS/QTL Extension Plan

**Status:** executed; validated complete  
**Plan date:** 2026-08-21  
**Execution completed:** 2026-08-21  
**Execution report:** [endophenotype_gwas_qtl_extension_execution_report.md](endophenotype_gwas_qtl_extension_execution_report.md)  
**Execution model:** local production-equivalent; Minerva is not required  
**Planned publication directory:**
`results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/`

## Executive decision

The next Phase 19 workstream will test whether the frozen ROSMAP Phase 18 key
drivers have human genetic support for three quantitative cerebrospinal-fluid
(CSF) Alzheimer endophenotypes:

1. amyloid-beta 42 (`csf_abeta42`);
2. total tau (`csf_total_tau`); and
3. phosphorylated tau 181 (`csf_ptau181`).

The primary GWAS source is the 2026 meta-analysis of up to 18,948 people of
European ancestry. The study reports 12 genome-wide-significant loci across
the three traits and provides complete meta-analysis summary-statistic links.
Its data are registered under NIAGADS `NG00191`, GWAS Catalog accessions
`GCST90726396`–`GCST90726398`, and trait-labeled Washington University links:

- [study and data-availability section](https://www.nature.com/articles/s41467-026-71682-8);
- [A-beta 42 meta-analysis](https://wustl.box.com/s/nfexw54o37smdq84lz1inpqduqcf7ofa);
- [total-tau meta-analysis](https://wustl.box.com/s/pydeqc87yke2ejvve5mrh9quyaikgq2p);
- [p-tau181 meta-analysis](https://wustl.box.com/s/nmyjzql5awxu7qu57m33rkcvq1w3njj8); and
- [Washington University open-science portal](https://neurogenomics.wustl.edu/open-science/raw-data/).

The analysis will screen every frozen candidate before acquiring large QTL or
LD inputs. It will use two different GWAS gates for two different questions:

| Gate | Frozen rule | What it permits |
|---|---|---|
| Regional single-variant gate | At least one variant in the frozen candidate region has `P < 5e-8` and regional coverage passes QC. | Regional fine-mapping and classical QTL colocalization. |
| Candidate-frozen gene-based gate | MAGMA candidate test passes `0.05 / (19 genes x 3 traits) = 8.7719298e-4`. | Gene-level follow-up, regional ambiguity analysis, and registered TWAS/PWAS routes. |

A gene-based-only result is not evidence that the GWAS and QTL share a causal
variant. It must not enter classical H0-H4 colocalization unless an independent
regional signal model is established. Conversely, a pair with a valid
single-variant regional signal may enter colocalization even if its MAGMA test
does not pass.

The QTL order for regional-signal pairs is:

1. unambiguous cis-CSF or cis-brain pQTL;
2. exact-cell-type brain eQTL;
3. exact or prespecified lineage brain sQTL;
4. bulk-brain eQTL or sQTL as an explicitly labeled fallback.

Every eligible registered dataset is retained as its own route. The workflow
must not choose the source, context, ancestry, region, prior, or method that
produces the most favorable posterior.

This is an endophenotype-specific extension. A positive A-beta or tau result
supports a genetic relationship with that biomarker pathway. It does not by
itself prove general Alzheimer-diagnosis causality, prove that the candidate is
the only causal gene in the locus, or validate a Phase 18 cell context.

## Relationship to completed Phase 19 work

This plan implements the next analysis recommended in
[Remaining GWAS/QTL analyses and recommended next step](remaining_gwas_qtl_analyses_and_next_step.md).
Where it is silent, these documents remain authoritative:

- [Phase 19 overall roadmap](../overall_plan.md);
- [Phase 19 Tier 1 plan](../tier1/human_genetic_support_plan.md);
- [Tier 2 regional GWAS/QTL plan](../tier2/tier2_regional_gwas_qtl_plan.md); and
- [Tier 2 classical colocalization recovery plan](../tier2/tier2_classical_coloc_recovery_plan.md).

The extension is additive and immutable with respect to the three completed
result bundles:

```text
results/minerva_production/19_genetic_support_tier1/
results/minerva_production/19_genetic_support_tier2_regional/
results/minerva_production/19_genetic_support_tier2_recovery/
```

It must read and hash-validate their relevant manifests and summaries. It must
not alter, replace, or publish into those directories.

The diagnosis-GWAS recovery found regional `P < 5e-8` signals for only four of
the 19 nuclear candidates: `ANKRD11`, `APOE`, `COX7C`, and `RPS15`. This new
work does not relax that earlier result. It asks whether quantitative A-beta
or tau phenotypes expose additional candidate-region signals that were hidden
in a broad diagnosis phenotype.

The unresolved APOE and RPS15 diagnosis-GWAS author/LD recovery remains a
separate parallel activity. It is not a prerequisite for this local extension.

## Questions this workstream will answer

### Primary question

For each frozen nuclear Phase 18 gene and each of the three CSF biomarkers:

> Is there a genome-wide-significant variant in the frozen candidate region,
> and, if so, do the biomarker GWAS signal and a candidate pQTL, eQTL, or sQTL
> support the same fine-mapped causal signal under compatible models and LD?

### Secondary question

> Does a candidate-frozen gene-based test support the gene even when no single
> variant in its region reaches `P < 5e-8`?

This second question is useful because a gene-based test aggregates information
across variants. It is not a substitute for regional colocalization.

### Independence question

> Does the genetic evidence come from participants independent of the ROSMAP
> discovery data and of the selected QTL source?

The answer must be explicit. Reuse of ROS/MAP or another shared cohort does not
make the analysis invalid, but it makes it triangulation or mechanism evidence,
not fully independent validation. A leave-ROS/MAP-out or otherwise independent
result is preferred wherever it can be obtained.

## Frozen candidate scope and accounting

### Unique genes

The 25 Phase 18 genes remain frozen. No gene may be added after the new GWAS
results are viewed.

Nineteen autosomal nuclear genes are eligible for ordinary regional GWAS/QTL
analysis:

```text
ANKRD11
APOE
ATP6V1F
COX4I1
COX6B1
COX7C
DYNLT1
FTL
LAMTOR5
LAPTM4A
NCOA1
RPL11
RPL15
RPL38
RPLP1
RPS13
RPS15
SELENOW
UQCR10
```

Six mitochondrial-DNA genes remain outside ordinary nuclear cis-QTL analysis:

```text
MT-ATP6
MT-CO2
MT-CO3
MT-CYB
MT-ND4
MT-ND5
```

They must remain visible in outputs with
`analysis_status = not_applicable_mtdna`, not disappear and not be counted as
negative results. A separate mtDNA association plan is required to evaluate
them.

### Fixed analysis counts

The extension must reproduce these counts from the frozen Phase 19 candidate
manifest before opening the new GWAS results:

```text
unique_phase18_genes = 25
nuclear_genes = 19
mtdna_genes = 6
candidate_context_units = 47
nuclear_candidate_context_units = 27
mtdna_candidate_context_units = 20
biomarkers = 3
unique_gene_biomarker_rows = 75
nuclear_gene_biomarker_screens = 57
mtdna_gene_biomarker_not_applicable_rows = 18
candidate_context_biomarker_rows = 141
nuclear_candidate_context_biomarker_rows = 81
mtdna_context_biomarker_not_applicable_rows = 60
```

GWAS evidence is computed once per unique gene and biomarker. It can be
referenced by each Phase 18 context containing that gene, but those repeated
context rows are not independent genetic replications. QTL evidence remains
route- and context-specific.

### Frozen regions

The primary screening regions are the existing GRCh38 candidate windows in:

```text
results/minerva_production/19_genetic_support_tier2_recovery/
  recovery_regional_gwas_summary.tsv
```

They use the Phase 19 gene interval plus 1 Mb on each side. The extension must
copy the coordinates and their source hash; it must not recalculate gene
coordinates from a newer annotation after viewing results.

Overlapping candidate windows are screened for every gene but collapsed into a
unique biomarker-locus ID before fine-mapping. One fine-mapped locus can
therefore be referenced by several nearby genes without being counted several
times. The primary model locus is the union of the passing candidate window
and the lead variant's +/-1 Mb window. A prespecified sensitivity uses the
candidate window alone.

## Frozen biomarker definitions

| Internal ID | Display label | Trait model | Primary population | Interpretation boundary |
|---|---|---|---|---|
| `csf_abeta42` | CSF amyloid-beta 42 | Quantitative, additive linear model | European ancestry meta-analysis | Biomarker-specific amyloid support. |
| `csf_total_tau` | CSF total tau | Quantitative, additive linear model | European ancestry meta-analysis | Biomarker-specific total-tau support. |
| `csf_ptau181` | CSF phosphorylated tau 181 | Quantitative, additive linear model | European ancestry meta-analysis | Biomarker-specific phosphorylated-tau support. |

The source transformed and standardized biomarker measurements within cohorts.
The pipeline must preserve the released beta convention and trait-transform
metadata. It must not infer that a positive beta is more or less pathological
until the downloaded metadata establishes the coded allele and biomarker
direction.

The main analysis uses only the full European-ancestry meta-analysis for each
trait. The paper's non-European, diagnosis-stratified, interaction, and MTAG
files are deferred sensitivity datasets. They are not allowed to replace an
unfavorable primary result.

## Source acquisition and identity contract

### Primary GWAS registry

The source registry is frozen by scientific identity, not by an assumed
accession-to-trait ordering:

| Source | Registered identity | Planned use |
|---|---|---|
| Washington University | Three trait-labeled Box links above | Preferred initial download because the article labels each link by trait. |
| GWAS Catalog | `GCST90726396`, `GCST90726397`, `GCST90726398` | Independent registry metadata and preferred immutable mirror if the harmonized full file is complete. |
| NIAGADS | `NG00191` | Declared archive/fallback when the released files become directly accessible. |

Before analysis, the downloader must verify the trait identity of every file
using its landing-page metadata, filename, header, row count, effect fields,
and at least three published sentinel variants. The accession-to-trait mapping
must be written to `endophenotype_biomarker_manifest.tsv` only after this
verification. A discrepancy is a blocking error; the code may not guess from
accession order.

For each source file, freeze:

```text
source_id
source_version_or_retrieval_timestamp
study_title
trait_id
trait_label
population
maximum_sample_size
per_variant_sample_size_available
genome_build
coordinate_convention
effect_allele_convention
effect_scale
trait_transform
source_url
resolved_download_url
compressed_bytes
uncompressed_bytes
sha256
access_date
license_or_code_of_conduct
```

If two mirrors are byte-identical or normalize to the same variant/effect
table, they are provenance mirrors, not independent evidence.

### Molecular-QTL source hierarchy

QTL sources are inventoried only after the 57 GWAS gate decisions are frozen.
Coverage can be checked for all candidates, but dense files, models, and LD are
acquired only for eligible routes.

#### 1. CSF or brain pQTL

The first coverage source is the
[NG00130.v2 CSF proteogenomic atlas](https://dss.niagads.org/datasets/ng00130/).
It includes 3,506 European-ancestry CSF samples and 7,008 SomaScan aptamers on
GRCh38. NIAGADS exposes P-value-only files and FUSION weights openly and full
files by application. The associated publication also reports public full
statistics through the Washington University portal and GWAS Catalog
`GCST90421033`–`GCST90428040`:

- [CSF proteogenomic study](https://www.nature.com/articles/s41588-024-01972-8).

Before download, construct a 19-gene protein coverage table. A pQTL route is
primary only when all of these hold:

- the aptamer maps unambiguously to the candidate protein;
- the protein identity and UniProt/gene mapping are frozen before association
  results are read;
- the association is cis under the source definition and within 1 Mb of the
  candidate gene;
- full beta, standard error, alleles, frequency, sample size, and regional
  statistics or a complete released model are available;
- the source-declared protein-level/cis-QTL significance rule passes;
- protein-altering variants that could change aptamer binding are flagged; and
- likely cohort overlap with the biomarker GWAS is recorded.

Trans-pQTLs are secondary pleiotropy evidence only. An aptamer-binding artifact
or ambiguous protein mapping cannot validate a gene.

#### 2. Exact-cell brain eQTL

Prioritize larger major-cell-type resources when full regional statistics or
complete models are available. Candidate registries include:

- [scMetaBrain](https://pubmed.ncbi.nlm.nih.gov/41394650/), which analyzes 3.9
  million transcriptomes from 1,260 samples/785 genotyped individuals; and
- the [PsychAD multi-ancestry single-nucleus atlas](https://pmc.ncbi.nlm.nih.gov/articles/PMC11661307/),
  which analyzes 5.6 million nuclei from 1,384 donors across eight cell classes
  and 27 subclasses.

PsychAD includes 152 Rush Alzheimer Disease Center donors from ROS/MAP. The
registry must therefore seek cohort-specific or leave-RADC/ROSMAP-out models.
If they are unavailable, PsychAD can support a mechanism but cannot be labeled
fully independent Phase 18 validation.

The existing NIAGADS `NG00184` inventory and the
[eQTL Catalogue](https://www.ebi.ac.uk/eqtl/Data_access/) remain candidate
sources. Significant-only rows and credible-set membership can establish
coverage but cannot be used as dense custom-colocalization input.

#### 3. Brain sQTL

Use the same exact, lineage, and bulk-brain hierarchy as the recovery plan.
Every splicing event must map unambiguously to the frozen Ensembl candidate
gene and GRCh38 interval. An absent event is
`qtl_context_not_measured`; absence from a significant-only table is not
`no_regional_qtl_signal`.

#### 4. Bulk-brain fallback

Bulk cortex or neocortex is permitted only as
`context_match_level = bulk_brain_fallback`. It measures an average across the
many cell types present in tissue and cannot be presented as proof of the
candidate's Phase 18 cell type.

### Source selection rules

Before inspecting QTL association results, rank datasets by:

1. molecular modality and cis status;
2. exact, lineage, or bulk context match;
3. ancestry compatibility;
4. independence from ROSMAP and from the biomarker GWAS;
5. complete model/statistic availability;
6. sample size; and
7. release version.

All datasets tied at the highest available registered level are retained as
separate routes. A later source may be added only through a dated plan/config
amendment written before its results are opened.

## Sample-overlap and independence audit

Sample overlap is assessed on three axes:

| Axis | Question | Consequence |
|---|---|---|
| Phase 18 vs biomarker GWAS | Did ROS/MAP participants contribute to the endophenotype meta-analysis? | If yes and no leave-ROS/MAP-out GWAS exists, label the evidence partially overlapping rather than fully independent. |
| Phase 18 vs QTL | Did the QTL use ROSMAP/Rush donors? | Prefer leave-ROSMAP-out or non-Rush QTL; otherwise call it mechanism support. |
| Biomarker GWAS vs QTL | Did both association studies include the same cohort or participants? | Prefer an independent QTL; otherwise quantify overlap or run correlation sensitivity and restrict the independence claim. |

Each dataset pair receives one of:

```text
no_known_overlap
possible_overlap
known_overlap_quantified
known_overlap_unquantified
leave_overlap_out
unknown
```

`unknown` is not silently treated as independent. Known or possible overlap
does not prevent descriptive analysis, but a shared-signal result cannot be
called fully independent unless a leave-overlap-out or independent-cohort
analysis agrees. If participant counts or error correlation can be estimated,
the colocalization result must be repeated over a prespecified plausible
correlation range; otherwise the limitation remains explicit.

## GWAS normalization and quality control

### Required normalized fields

Every trait is normalized to one GRCh38 row per biallelic autosomal variant:

```text
trait_id
chromosome
position
reference_allele
alternate_allele
effect_allele
other_allele
beta
standard_error
p_value
negative_log10_p
effect_allele_frequency
sample_size
imputation_quality_if_available
source_variant_id
canonical_variant_id
```

The canonical ID is
`chromosome:position:reference_allele:alternate_allele`. Multiallelic variants
are split only when the source representation and effect allele can be
resolved. No p-value, beta, or frequency may be silently imputed.

P-values stored as zero through numerical underflow retain the original value
and are represented by a documented lower bound for plotting only. Fine-mapping
uses beta and standard error, not a reconstructed p-value.

### File-level gates

Each GWAS must pass:

- verified biomarker identity;
- GRCh38 coordinates or a documented one-to-one lift-over;
- additive quantitative-trait beta and valid standard error;
- effect/non-effect allele definition;
- no duplicate canonical variant-effect rows after deterministic resolution;
- expected genome-wide scale and chromosome coverage;
- published sentinel-variant agreement in allele and p-value order of
  magnitude;
- hash-identical output on repeated normalization; and
- no unexpected restriction to significant or suggestive variants.

### Region-level coverage gates

A nuclear gene-biomarker pair is assessable for a negative regional screen only
if:

```text
regional_variant_density >= 500 variants per Mb
regional_variant_density >= 0.50 x the same-trait chromosome median
finite_p_value_fraction >= 0.99
beta_and_se_complete_fraction >= 0.95 for model eligibility
```

The density rule is deliberately permissive and protects against calling a
sparse or truncated region negative. A region failing it is
`not_assessable_low_gwas_coverage`, not `no_qualifying_gwas_signal`. Thresholds
may be changed only by an amendment written before candidate results are
unblinded.

## Prespecified GWAS analyses

### Analysis A: regional single-variant screen

For every one of the 57 nuclear gene-biomarker pairs:

1. extract the complete frozen region without a p-value filter;
2. calculate variant count, density, minimum p-value, lead variant, and the
   number below `5e-8`, `1e-6`, and `1e-5`;
3. apply the file- and region-coverage gates;
4. set `regional_signal = TRUE` only when at least one variant has
   `P < 5e-8`; and
5. freeze all 57 decisions before any QTL result is inspected.

`P < 1e-5` and `P < 1e-6` are descriptive only. They must not trigger classical
colocalization.

### Analysis B: candidate-frozen MAGMA

Run MAGMA locally for each biomarker using one pinned software version, one
GRCh38 gene annotation, and an ancestry-compatible European LD reference.

Primary model:

```text
model = SNP-wise mean
gene boundary = transcribed gene body
candidate family = 19 nuclear genes x 3 biomarkers
candidate Bonferroni threshold = 8.7719298e-4
```

Sensitivity model:

```text
gene boundary = gene body plus/minus 10 kb
status = sensitivity_only
```

The workflow should calculate genome-wide gene results, then extract the 19
prespecified candidates. This makes neighboring-gene competition visible. It
must also report the genome-wide Bonferroni threshold for the exact number of
successfully tested genes in each biomarker, but the independently selected
candidate threshold above is the primary validation test.

For every candidate passing the targeted threshold:

- list all overlapping and nearby tested genes in its regional window;
- show whether the candidate is the strongest gene-based result in the locus;
- condition on independently associated regional variants and repeat the gene
  test when compatible LD permits; and
- label the result `regionally_ambiguous` when neighboring genes or residual LD
  prevent gene-specific assignment.

A candidate MAGMA association is gene-level statistical support, not proof
that expression or protein abundance mediates the biomarker association.

### Gate-decision states

Every nuclear gene-biomarker pair ends GWAS screening in exactly one state:

```text
regional_and_gene_based_signal
regional_signal_only
gene_based_signal_only
no_qualifying_gwas_signal
not_assessable_gwas
```

The next step follows mechanically:

| State | Required next action |
|---|---|
| `regional_and_gene_based_signal` | QTL coverage, compatible fine-mapping, and regional colocalization; also report MAGMA. |
| `regional_signal_only` | QTL coverage, compatible fine-mapping, and regional colocalization. |
| `gene_based_signal_only` | Regional ambiguity audit and registered TWAS/PWAS follow-up; no H0-H4 route. |
| `no_qualifying_gwas_signal` | Stop without QTL/LD acquisition; report assessable no signal. |
| `not_assessable_gwas` | Stop and preserve the exact coverage/metadata reason. |

## QTL signal and model gates

For every regional-signal pair, create QTL routes using the frozen source
registry. A route proceeds only when the candidate molecular trait was
measured and has a source-significant cis signal.

The signal rule must be frozen per dataset before results are viewed:

1. use the release's declared cis-eGene, cis-sGene, or cis-pProtein FDR rule;
2. if full q-values are supplied, use `q <= 0.05`;
3. if neither exists, calculate the source-appropriate correction across all
   molecular traits tested in the registered dataset, not only the 19
   candidates; and
4. never infer no QTL signal from a significant-only table that omits the
   candidate.

Proceeding to classical colocalization additionally requires either:

- compatible complete released GWAS and QTL signal models; or
- full, unfiltered regional beta/standard-error/allele/frequency statistics
  plus ancestry-compatible LD for each trait.

P-values alone, lead-variant overlap, PIP overlap, credible-set overlap, TWAS,
or PWAS do not satisfy this requirement.

## Fine-mapping and LD plan

### LD-source order

Use this order separately for the biomarker GWAS and every QTL source:

1. complete source-released model or source-study LD;
2. author-provided locus model or LD for the analyzed ancestry;
3. the already registered ADSP R5 non-Hispanic White GRCh38 LD resource when
   ancestry and variant representation match;
4. unrelated 1000 Genomes 30x GRCh38 EUR LD as a labeled sensitivity; or
5. `model_or_ld_incompatible` when no defensible source exists.

The biomarker paper used joint European-ancestry genotype data from 6,785
participants for its conditional analysis, but this plan does not assume that
those participant-derived LD matrices are public. The paper's own
single-causal-variant `coloc.abf` results are external cross-checks, not
substitutes for this extension's multi-signal model.

The GWAS and QTL do not have to use the same people. Each fine-mapping model
must use LD appropriate for its own ancestry. Do not automatically reuse ADSP
LD for a differently composed QTL cohort.

### Harmonization gates

Before modeling, require:

- compatible genome build and one-to-one coordinates;
- canonical variant identity and allele alignment;
- deterministic effect-direction changes for allele swaps;
- removal of unresolved A/T and C/G variants with ambiguous frequency;
- explicit treatment of duplicates and multiallelic sites;
- documented allele-frequency tolerance and mismatch counts;
- at least 500 common variants in the model locus;
- at least 80% of variants in the smaller complete input represented after
  harmonization;
- retention of every available high-PIP or credible-set variant from a reused
  source model;
- identical variant order between statistics and LD;
- finite, symmetric LD with unit diagonal;
- positive-semidefinite LD after no more than a documented small numerical
  correction; and
- a passing summary-statistic/LD consistency diagnostic.

If a threshold fails, retain the audit counts and stop. Do not tune filters
until H4 improves.

### Multi-signal fine-mapping

The inherited primary settings are:

```text
primary_method = coloc.susie
credible_set_coverage = 0.95
custom_susie_L = 10
custom_susie_maxit = 1000
p1 = 1e-4
p2 = 1e-4
p12_primary = 5e-6
p12_sensitivity = 1e-6,5e-6,1e-5
shared_signal_threshold = PP.H4 >= 0.80
conditional_shared_threshold = PP.H4 / (PP.H3 + PP.H4) >= 0.80
```

Fine-map each unique biomarker locus once and reference its model from all
applicable gene/context/QTL routes. Fine-map each QTL cohort, molecular trait,
context, and assay separately. Record convergence, prior variance, credible
sets, purity, PIP, excluded variants, and warnings.

Compare every supported GWAS signal with every supported QTL signal. Retain all
signal-pair results, including discordant pairs. `coloc.abf` is permitted only
as a clearly labeled single-signal sensitivity when its assumptions are
defensible; it cannot replace a failed multi-signal primary route.

### Colocalization outcomes

Availability and scientific outcome are separate fields.

`route_terminal_status` must be one of:

```text
precomputed_resolved
custom_resolved
no_regional_gwas_signal
no_regional_qtl_signal
protein_not_measured
qtl_context_not_measured
aptamer_mapping_ambiguous
model_or_ld_incompatible
not_assessable
```

For resolved routes, `coloc_outcome` must be one of:

```text
robust_shared_signal
suggestive_shared_signal
distinct_signals
inconclusive
```

`robust_shared_signal` requires both frozen H4 thresholds, convergence and LD
QC, and robustness across `p12` sensitivity. `0.50 <= PP.H4 < 0.80` is
suggestive. Strong H3 with low H4 is `distinct_signals`, not failed support.

## TWAS and PWAS supporting route

The mandatory gene-level analysis is MAGMA. TWAS/PWAS is a conditional
supporting stage for `gene_based_signal_only` pairs and is never a classical
colocalization substitute.

Before running prediction models:

1. inventory model coverage for all 19 candidates without looking at the
   endophenotype association;
2. register tissue, cell context, cohort, ancestry, assay, weight version,
   sample overlap, and source hash;
3. prefer at least two independent brain-expression models for TWAS and two
   independent CSF/brain protein models for PWAS when available;
4. correct over every candidate-biomarker-model family actually registered;
5. run conditional/joint or FOCUS-style model comparison where correlated
   neighboring prediction models exist; and
6. keep exact, lineage, bulk-brain, CSF, and non-brain models separate.

A significant prediction model is `weak` or `suggestive` support unless it is
replicated across independent models and accompanied by valid colocalization
or high-confidence causal-gene fine-mapping. Direction is reported on the
model's coded scale and is not interpreted as therapeutic direction without
additional evidence.

## Evidence integration and the meaning of “validated”

The extension produces both biomarker-specific grades and a cumulative Phase
19 view. It never overwrites the baseline grade.

### Biomarker-specific contribution

| Contribution | Minimum evidence |
|---|---|
| `strong` | Robust multi-signal colocalization with strong model/LD QC, an exact or directly relevant CSF/brain molecular trait, prior robustness, and no unresolved independence limitation. |
| `moderate` | Robust colocalization in a biologically relevant fallback context, or robust shared signal with a clearly labeled partial-overlap limitation and independent corroboration. |
| `weak` | Corrected MAGMA, replicated TWAS/PWAS without valid colocalization, or suggestive H4. |
| `none_found` | Required data were assessable and neither GWAS gate nor any eligible downstream route qualified. |
| `not_assessable` | Missing measurement, low coverage, inaccessible full statistics, incompatible alleles/build/model/LD, or unresolved source metadata prevented the question from being answered. |

A gene is counted as **newly biomarker-supported** only if:

- its extension contribution is `strong` or `moderate` for at least one
  biomarker;
- the qualifying route names the candidate molecular trait rather than only a
  nearby gene;
- the result is not based solely on MAGMA, TWAS, PWAS, lead-variant overlap, or
  a significant-only QTL table; and
- it was not already `strong` or `moderate` in the frozen cumulative Phase 19
  baseline.

The report must separately count:

```text
newly_biomarker_supported_unique_genes
previously_supported_genes_with_new_biomarker_evidence
weak_gene_based_only_genes
assessable_no_signal_genes
not_assessable_genes
```

The word “validated” must be qualified as `biomarker-specific genetic support`
in prose. No endophenotype result is allowed to become an unqualified claim
that the gene causes Alzheimer disease.

### Carrying gene evidence to contexts

A gene-level GWAS, pQTL, MAGMA, TWAS, or PWAS result is copied to every Phase
18 context for display with `evidence_resolution = gene_level`. It does not
validate those cell types. Only an exact-cell QTL route can receive
`evidence_resolution = exact_context`; lineage and bulk sources retain their
fallback labels.

### Cumulative grading

For every candidate context:

1. retain the frozen Tier 1/Tier 2 recovery grade and provenance;
2. add separate A-beta 42, total-tau, and p-tau181 contributions;
3. select the strongest qualifying extension result using the frozen evidence
   hierarchy, not the largest posterior alone;
4. never downgrade an earlier grade because an endophenotype has no signal;
5. expose conflicting shared/distinct mappings rather than hiding them; and
6. count a repeated gene across contexts only once in unique-gene totals.

## Local execution and storage contract

This workflow is designed to run locally. The `minerva_production` component
of the final path is the repository's namespace for validated results; it is
not a claim that Minerva performed the calculation.

```text
execution_stage = local_production_equivalent
execution_backend = direct
publication_namespace = minerva_production
gpu_required = false
max_download_workers = 2
max_finemapping_workers = 1
process_one_locus_at_a_time = true
planned_memory_per_locus = 8 GiB
hard_memory_limit_per_locus = 16 GiB
minimum_free_space_after_task = 50 GiB
deterministic_gzip_mtime = 0
```

Before a source download, require free space of at least 2.2 times the largest
compressed file plus the 50 GiB reserve. If that gate fails, use an external
local disk or end the affected route with a documented resource limitation.
Do not silently migrate to Minerva.

Ignored source/work directories:

```text
data/reference/phase19_genetic_support/endophenotype_gwas_qtl_extension/
  inventory/
  gwas_raw/
  gwas_normalized/
  qtl_coverage/
  qtl_regional/
  released_models/
  ld_source/
  ld_candidate_blocks/
  prediction_weights/
  source_manifest/
  work/
```

Pilot and final outputs:

```text
results/local_pilot/19_genetic_support_endophenotype_gwas_qtl_extension/
results/minerva_production/19_genetic_support_endophenotype_gwas_qtl_extension/
```

Credentials, cookies, access tokens, signed URLs, and authorization headers
must be read from environment or user configuration and must never appear in
the repository, commands captured in reports, manifests, logs, or result
files. The public primary GWAS path should not require Synapse credentials.

## Planned implementation files

Create extension-specific files so all completed Phase 19 pipelines remain
reproducible:

```text
config/phase19_endophenotype_gwas_qtl_extension.yml
config/phase19_endophenotype_local_execution.yml
scripts/19_download_endophenotype_gwas.py
scripts/19_normalize_endophenotype_gwas.py
scripts/19_screen_endophenotype_regions.py
scripts/19_run_endophenotype_magma.R
scripts/19_inventory_endophenotype_qtl.py
scripts/19_extract_endophenotype_qtl.py
scripts/19_prepare_endophenotype_ld.py
scripts/19_run_endophenotype_coloc.R
scripts/19_run_endophenotype_twas_pwas.R
scripts/19_integrate_endophenotype_evidence.py
scripts/19_validate_endophenotype_extension.py
tests/test_phase19_endophenotype_extension.py
tests/test_phase19_endophenotype_extension.R
tests/fixtures/phase19_endophenotype_extension/
docs/phase_19_genetic_support/endophenotype_gwas_qtl_extension/
  endophenotype_gwas_qtl_extension_execution_report.md
```

Reuse the existing candidate-manifest, variant-normalization, artifact-hashing,
status-precedence, and plotting helpers where their contracts match. Modify
shared dispatch code only to register the new phase. Do not change old
configuration defaults to make the extension run.

## Detailed execution tasks

### Task 0: freeze hypotheses and baseline

1. Hash the three completed Phase 19 result bundles.
2. Read the frozen 47-row candidate-context manifest and require 25 genes.
3. Reconstruct the 19 nuclear and six mtDNA gene sets.
4. Copy the 19 GRCh38 candidate windows and their upstream hash.
5. Generate the 75 gene-biomarker and 141 context-biomarker rows.
6. Freeze the phenotype, region, threshold, QTL, ancestry, overlap, prior, and
   grading policies in configuration.
7. Abort on any count, identifier, context, coordinate, or hash drift.

Deliverables: candidate manifest, biomarker manifest, screening units, baseline
hash checks, and a decision log created before GWAS download.

### Task 1: implement and test the source registry

1. Create schemas for GWAS, QTL, LD, and prediction-model sources.
2. Register the three WUSTL links, three GWAS Catalog accessions, and NG00191.
3. Register pQTL and brain eQTL/sQTL candidate resources without reading
   candidate association outcomes.
4. Add ancestry, context, assay, sample-overlap, access, and completeness
   fields.
5. Add URL redaction and credential-leak tests.

Deliverable: a result-blind dataset registry with deterministic source IDs.

### Task 2: acquire and verify the three GWAS files

1. Resolve the trait-labeled WUSTL file identities.
2. Query GWAS Catalog metadata and compare the accession, trait, population,
   build, sample size, and publication.
3. Use NIAGADS only as a verified fallback.
4. Download each immutable source once with resume support.
5. Freeze bytes and SHA-256 before decompression.
6. Validate the downloaded headers and published sentinel variants.
7. Stop if a file is truncated, filtered, mislabeled, or lacks the fields
   required for the planned use.

Deliverable: three validated raw files and a mirror/provenance audit.

### Task 3: normalize the GWAS files

1. Parse each source with a trait-specific, tested adapter.
2. normalize chromosomes, positions, alleles, variant IDs, beta, standard
   error, p-value, frequency, and sample size;
3. preserve all original identity/effect columns needed for audit;
4. split or reject multiallelic and duplicate records deterministically;
5. create bgzip/tabix files for local regional extraction;
6. repeat the normalization and require identical hashes; and
7. emit global and chromosome-level QC.

Deliverable: three complete indexed GRCh38 summary-statistic files.

### Task 4: run the regional screen

1. Extract all 19 regions for all three traits with no p-value filter.
2. Apply the coverage gates before interpreting minimum p-values.
3. emit exactly 57 nuclear summaries and 18 mtDNA not-applicable rows;
4. create overlapping-locus IDs without merging gene-level screen rows;
5. apply the `P < 5e-8` gate; and
6. freeze and hash the regional decisions before QTL lookup.

Deliverable: complete regional statistics and the first half of the 57-row gate
table.

### Task 5: run candidate-frozen MAGMA

1. Pin MAGMA, annotation, and European LD-source versions.
2. Run genome-wide gene analysis for each trait using the primary gene body.
3. Run the +/-10 kb sensitivity separately.
4. Extract all 19 candidates, including nonsignificant results.
5. Apply the fixed `8.7719298e-4` candidate threshold.
6. inventory neighboring gene results and regional ambiguity.
7. condition and repeat where compatible LD permits.
8. combine MAGMA with the regional decision into exactly 57 gate states.

Deliverable: full MAGMA results, candidate extract, regional competition audit,
and frozen gate decisions.

### Task 6: inventory QTL coverage and independence

For regional-signal pairs only:

1. map candidates to UniProt proteins, Ensembl genes, and splicing events;
2. check cis-pQTL measurement and aptamer quality;
3. check exact/lineage brain eQTL and sQTL measurement;
4. retain bulk brain only under its fallback label;
5. identify full regional statistics and released model availability;
6. record source-declared signal thresholds;
7. audit ROSMAP/Rush and biomarker-GWAS cohort overlap; and
8. freeze all selected routes before calculating H4.

For gene-based-only pairs, inventory TWAS/PWAS weights separately and do not
create H0-H4 routes.

Deliverable: QTL coverage, overlap audit, prediction-weight inventory, and
deterministic route manifest. A zero-route manifest is scientifically valid.

### Task 7: acquire only eligible regional QTL/model inputs

1. Prefer complete released models and candidate-region indexed extracts.
2. Download full source archives only after the storage gate.
3. never reconstruct a region from significant-only rows;
4. validate gene/protein/event identity and complete effect fields;
5. record source bytes, hash, extraction command, and output hash; and
6. assign an exact terminal reason when the necessary source is unavailable.

Deliverable: immutable eligible QTL inputs plus explicit missing-source states.

### Task 8: obtain and validate ancestry-compatible LD

1. Use released/source-matched models or LD first.
2. Request author models/LD where necessary without blocking other routes.
3. use the registered ADSP European panel only when compatible;
4. use 1000 Genomes EUR only as a labeled sensitivity;
5. acquire candidate blocks only after GWAS and QTL signal gates pass; and
6. validate ancestry, build, alleles, variant order, matrix properties, and
   summary/LD consistency.

Deliverable: per-trait model/LD provenance and QC, or
`model_or_ld_incompatible`.

### Task 9: harmonize and fine-map eligible routes

1. Create the exact common variant set with a full exclusion audit.
2. require all harmonization and coverage gates;
3. fine-map each unique biomarker locus once;
4. reuse complete compatible QTL models or fine-map the full QTL region;
5. require convergence and credible-set QC; and
6. preserve failures and their terminal status instead of changing parameters
   after seeing results.

Deliverable: complete GWAS/QTL fine-mapping tables, harmonization audit, and LD
QC.

### Task 10: run colocalization and sensitivity analyses

1. Run every supported GWAS-signal/QTL-signal pair with `coloc.susie`.
2. retain H0, H1, H2, H3, H4, conditional H4, signal IDs, and warnings;
3. run all three frozen `p12` values;
4. run candidate-window locus sensitivity;
5. run overlap-correlation sensitivity where quantifiable;
6. run `coloc.abf` only as a justified single-signal sensitivity; and
7. assign route outcomes with frozen thresholds.

Deliverable: complete posterior and sensitivity tables, including negative and
discordant signal pairs.

### Task 11: run conditional TWAS/PWAS support

1. Select only registered `gene_based_signal_only` pairs for the primary
   supporting route.
2. run every preregistered model with valid coverage;
3. correct the complete registered testing family;
4. perform regional conditional/model competition where possible;
5. retain all null and conflicting models; and
6. grade these results no higher than allowed by the evidence table.

Deliverable: a complete TWAS/PWAS follow-up table, which may contain only
terminal coverage states if no models qualify.

### Task 12: integrate grades and wording

1. Start with frozen cumulative Phase 19 grades.
2. calculate biomarker-specific route contributions;
3. apply exact/fallback and independence qualifiers;
4. separate gene-level from cell-context-level evidence;
5. compute unique newly supported genes without context duplication;
6. create all 141 context-biomarker rows; and
7. generate conclusion text from structured fields, not handwritten result
   selection.

Deliverable: evidence summary, complete matrix, and auditable unique-gene
counts.

### Task 13: run the pilot

The local pilot must include:

- one real strong regional plumbing check, with APOE permitted but no required
  biological outcome;
- one real assessable no-signal route;
- one gene-based-only fixture;
- one mtDNA not-applicable route;
- one exact-cell and one bulk-brain fallback QTL fixture; and
- synthetic shared, distinct, multiple-signal, allele-flip, palindromic,
  sparse-region, wrong-build, wrong-LD-order, and sample-overlap cases.

The pilot passes on correct behavior, not on a positive real-data result.

### Task 14: run local production and publish atomically

1. Process one fine-mapping locus at a time.
2. write all files to a staging directory;
3. validate schemas, counts, statuses, grades, plots, hashes, and credential
   absence;
4. rerun the output-only validator in a clean process;
5. require zero baseline mutations and zero undeclared files; and
6. rename staging to the final directory only after every blocking check
   passes.

### Task 15: write the execution report

Record:

- exact commands and environment versions;
- local host/backend truthfully;
- source accessions, links, bytes, and hashes;
- candidate, gate, QTL-route, and terminal-state counts;
- newly supported and previously supported unique-gene counts;
- sample-overlap and independence limitations;
- all unassessable reasons;
- resource use; and
- wording boundaries for each biomarker.

## Output contract

The validated final directory contains exactly these 36 declared files. A
conditional analysis with no eligible rows must still emit a valid header-only
table.

```text
endophenotype_analysis_manifest.tsv
endophenotype_dataset_registry.tsv
endophenotype_request_manifest.tsv
endophenotype_input_inventory.tsv
endophenotype_source_checks.tsv
endophenotype_candidate_manifest.tsv
endophenotype_biomarker_manifest.tsv
endophenotype_screening_units.tsv
endophenotype_gwas_qc.tsv
endophenotype_regional_gwas_summary.tsv
endophenotype_regional_gwas.tsv.gz
endophenotype_magma_results.tsv
endophenotype_magma_conditional.tsv
endophenotype_gate_decisions.tsv
endophenotype_qtl_coverage.tsv
endophenotype_route_manifest.tsv
endophenotype_sample_overlap_audit.tsv
endophenotype_variant_harmonization.tsv.gz
endophenotype_variant_harmonization_summary.tsv
endophenotype_ld_qc.tsv
endophenotype_gwas_finemapping.tsv.gz
endophenotype_qtl_finemapping.tsv.gz
endophenotype_colocalization.tsv.gz
endophenotype_colocalization_qc.tsv
endophenotype_prior_sensitivity.tsv.gz
endophenotype_twas_pwas_followup.tsv
endophenotype_assessability.tsv
endophenotype_evidence_summary.tsv
endophenotype_context_biomarker_matrix.tsv
endophenotype_figure_data.tsv.gz
endophenotype_evidence_matrix.pdf
endophenotype_evidence_matrix.png
endophenotype_locus_plots.pdf
endophenotype_checks.tsv
endophenotype_artifacts.tsv
endophenotype_status.tsv
```

### Required table-level counts

| File | Required minimum/count rule |
|---|---|
| `endophenotype_candidate_manifest.tsv` | Exactly 47 candidate-context rows and 25 genes. |
| `endophenotype_biomarker_manifest.tsv` | Exactly three verified traits. |
| `endophenotype_screening_units.tsv` | Exactly 75 gene-biomarker rows: 57 nuclear and 18 mtDNA not applicable. |
| `endophenotype_regional_gwas_summary.tsv` | Exactly 75 rows, including explicit mtDNA states. |
| `endophenotype_gate_decisions.tsv` | Exactly 57 nuclear rows. |
| `endophenotype_magma_results.tsv` | One row per successfully tested autosomal gene and biomarker, with `phase18_candidate` flag; all 57 candidates must be present or have a named failure. |
| `endophenotype_route_manifest.tsv` | Determined mechanically from regional-signal pairs and preregistered eligible QTL sources; zero is permitted. |
| `endophenotype_context_biomarker_matrix.tsv` | Exactly 141 rows: 81 nuclear and 60 mtDNA not applicable. |
| `endophenotype_status.tsv` | Exactly one row. |

No caches, temporary files, credentials, raw downloads, indexes, or undeclared
sidecars may be present in the final result directory.

## Required automated tests

### Baseline and scope tests

- all upstream hashes are unchanged;
- exact reconstruction of 25 genes, 47 contexts, and three biomarkers;
- exact 75, 57, 141, 81, and 60 row-count contracts;
- no post-GWAS candidate addition or coordinate change;
- mtDNA rows remain present and never enter nuclear QTL code; and
- overlapping windows share a locus model without being counted as
  replication.

### Source and security tests

- accession/trait metadata identity and sentinel checks;
- checksum and byte-count verification;
- rejection of truncated or significant-only GWAS/QTL inputs;
- deterministic download/extraction manifests;
- signed URL and authorization-header redaction; and
- no token-like string in any result or report.

### GWAS and MAGMA tests

- quantitative beta/SE handling and trait direction metadata;
- p-value underflow handling without altering fine-mapping inputs;
- duplicate, multiallelic, chromosome, and build normalization;
- sparse-region coverage becomes `not_assessable`, not negative;
- exactly 57 frozen regional and gene-based gate decisions;
- candidate Bonferroni threshold equals `0.05 / 57`;
- gene-body primary and +/-10 kb sensitivity stay distinct; and
- a gene-based-only signal never creates a colocalization route.

### Molecular-QTL tests

- unambiguous gene/protein/aptamer/event mapping;
- cis and trans pQTL routes remain separate;
- protein-altering aptamer-binding flags are retained;
- absence from a significant-only table is not called no QTL signal;
- exact, lineage, and bulk context labels cannot be promoted; and
- leave-ROSMAP-out status and all overlap categories propagate to summaries.

### Harmonization, LD, and fine-mapping tests

- allele swap and beta sign change;
- ambiguous palindromic removal;
- build mismatch and failed lift-over rejection;
- common-variant count and overlap gates;
- LD order, diagonal, symmetry, finiteness, eigenvalues, and ancestry;
- summary/LD consistency rejection;
- deterministic SuSiE convergence and credible sets; and
- one unique biomarker-locus model reused across applicable contexts.

### Colocalization and grading tests

- synthetic H4 shared signal;
- synthetic H3 distinct signals;
- multiple causal signals and all signal-pair retention;
- H0-H4 sums and conditional H4 calculation;
- all three `p12` values;
- `coloc.abf` never replaces the multi-signal primary;
- sample-overlap limitation prevents an unqualified independence claim;
- MAGMA/TWAS/PWAS alone cannot produce strong validation;
- no-signal and not-assessable remain distinct;
- unique-gene counts do not duplicate Phase 18 contexts; and
- no endophenotype grade downgrades a frozen baseline grade.

### Publication tests

- exact 36-file contract;
- header-only conditional tables validate;
- exactly one terminal state for every gate and generated QTL route;
- all figure rows trace to evidence rows;
- output-only grade recalculation matches the published summary;
- artifact hashes reproduce;
- execution metadata says `direct`, not Minerva; and
- zero mutation of all completed Phase 19 result bundles.

## Blocking gates and stopping rules

Publication is forbidden if:

- any upstream Phase 19 artifact changes;
- the frozen candidate, context, biomarker, or matrix counts drift;
- a GWAS accession/file cannot be assigned to exactly one verified trait;
- a file is filtered rather than complete genome-wide summary statistics;
- build, allele, effect scale, or biomarker direction is unresolved;
- a low-coverage region is called negative;
- a threshold, source, region, context, prior, or method is chosen after seeing
  a favorable result;
- a gene-based-only result enters H0-H4 colocalization;
- a QTL no-signal conclusion comes only from significant-only data;
- an aptamer is ambiguously mapped or likely binding-affected without a flag;
- an exact/lineage/bulk context is mislabeled;
- required sample overlap is hidden or treated as independence;
- ancestry, model, alleles, variant space, or LD is incompatible;
- a model fails required convergence/diagnostic gates;
- H4 is inferred from PIP, credible-set, or lead-variant overlap;
- a route or gene-biomarker screen lacks one terminal state;
- a grade cannot be regenerated from detailed evidence;
- a credential appears in an artifact;
- an output is missing, undeclared, or schema-invalid; or
- any blocking test fails.

An external source being unavailable does not block the entire workstream. The
affected route receives a precise `not_assessable` reason, while independent
routes continue.

## Completion criteria

Technical completion requires:

```text
validation_status = validated_complete_endophenotype_gwas_qtl_extension
baseline_phase19_hashes_unchanged = true
unique_phase18_genes = 25
nuclear_gene_biomarker_screens = 57
mtdna_gene_biomarker_not_applicable_rows = 18
terminal_nuclear_gate_decisions = 57
candidate_context_biomarker_rows = 141
mtdna_context_biomarker_not_applicable_rows = 60
all_generated_qtl_routes_terminal = true
declared_output_files = 36
undeclared_output_files = 0
blocking_check_failures = 0
execution_backend = direct
full_phase19_complete = false
```

The workstream is complete even if no new gene is supported. Completion means
that every prespecified candidate and biomarker was evaluated under valid,
frozen rules; eligible QTL comparisons used compatible models; and every
negative or unavailable result is represented honestly.

## Recommended execution order

1. Freeze the baseline hashes, candidates, regions, and all 75/141 matrix rows.
2. Implement source identity/security tests.
3. Download and normalize the three endophenotype GWAS files.
4. Freeze all 57 regional decisions.
5. Run and freeze all 57 candidate MAGMA decisions.
6. Inventory QTL and prediction-model coverage only after gate freeze.
7. Run the synthetic and small real-data pilot.
8. Acquire full QTL/model/LD data only for eligible routes.
9. Fine-map and run multi-signal colocalization one locus at a time.
10. Run gene-based-only TWAS/PWAS supporting routes.
11. Integrate biomarker-specific evidence without overwriting prior results.
12. Validate and atomically publish the 36-file local bundle.
13. Write the execution report and clearly separate biomarker support,
    cell-context support, and fully independent validation.

## Acceptance checklist (verified at execution freeze)

- [x] All 25 genes, 47 contexts, 19 nuclear genes, and six mtDNA genes match
  the frozen manifests.
- [x] All 19 candidate windows and upstream hashes are frozen.
- [x] The three biomarker identities are verified rather than inferred from
  accession order.
- [x] The exact WUSTL, GWAS Catalog, and NIAGADS source roles are configured.
- [x] The primary European meta-analysis is separated from every sensitivity
  dataset.
- [x] The regional, MAGMA, QTL, overlap, LD, coloc, and grading rules are in
  configuration before candidate results are read.
- [x] Candidate MAGMA significance is exactly `0.05 / 57`.
- [x] Gene-based-only evidence cannot enter H0-H4 code.
- [x] QTL sources are ranked without looking at H4.
- [x] ROSMAP and biomarker-GWAS overlap fields are mandatory.
- [x] Exact, lineage, bulk, CSF protein, and gene-level evidence labels are
  distinct.
- [x] Local disk/memory gates pass; no Minerva job is assumed.
- [x] The pilot covers shared, distinct, multiple-signal, corrupted-input, and
  not-applicable cases.
- [x] The final validator enforces the exact 36-file and 141-row contracts.
- [x] The reporting template uses “biomarker-specific genetic support,” not an
  unqualified claim that a gene causes Alzheimer disease.

