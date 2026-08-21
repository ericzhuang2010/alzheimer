# Phase 19 Tier 2: Candidate-region GWAS/QTL Fine-mapping and Colocalization

## Decision and relationship to the master plan

The existing
[Phase 19 master plan](human_genetic_support_plan.md) **partly includes Tier
2**, but only as a conditional extension. It already defines:

- Tier 2 as full candidate-region GWAS/QTL statistics, matching fine-mapping
  models, and ancestry-matched LD for unresolved comparisons;
- the phenotype and molecular-QTL context hierarchy;
- frozen colocalization priors and evidence thresholds;
- the preference for multi-signal `coloc.susie` over a single-signal model;
- harmonization, LD, prior-sensitivity, and stopping rules; and
- the general custom-colocalization task and output columns.

At the time this plan was written, Tier 2 was explicitly deferred in the
master plan, the statistical dependencies were not pinned, and the only
implemented pipeline schema was `human_genetic_support_tier1_v1`. The
validated Tier 1 bundle contains no classical H0-H4 posterior results.

This document is the separate implementation, acquisition, execution, output,
and completion contract for the quoted Tier 2 data increment. Where this
document is silent, the master plan remains authoritative.

## Execution status

As of 2026-08-21, the original controlled-source pilot and the approved
open-data alternative below are complete. The local run published the
validated 23-file bundle to
`results/minerva_production/19_genetic_support_tier2/`. It retained 9,363
candidate QTL fine-mapping rows and 311,180 dense candidate-region GWAS rows;
all source and artifact checks passed. The
FunGen-xQTL Synapse entities remain unreadable by the current account even
though authentication and the ADKP clickwrap succeed. That ACL no longer
blocks the alternative analysis: the workflow freezes and downloads public
NIAGADS NG00184 molecular-QTL fine-mapping files, the GWAS Catalog Bellenguez
2022 AD statistics, and only the ancestry-matched LD needed by an authorized
custom comparison. Exact Synapse reproduction remains a later sensitivity.

The alternative does not rename fine-mapping overlap or QTL significance as
classical H0-H4 evidence. A route for which dense regional statistics,
compatible models, or matched LD cannot be obtained ends honestly as
`not_assessable`; that is a terminal scientific result, not negative genetic
evidence and not a technical failure of the production bundle.

All 54 routes are terminal: 52 have released candidate QTL fine-mapping
coverage but lack compatible classical H0-H4 or full custom-coloc inputs, and
the two LAMTOR5 sQTL routes lack released candidate sQTL fine mapping. Thus all
54 are `not_assessable`, no Phase 19 grade changed, and this result must not be
read as evidence for distinct or absent signals.

See the [Tier 2 execution report](tier2_execution_report.md) for commands,
validated counts, source hashes, terminal route states, and limitations.

## Current state and Tier 2 boundary

### Frozen Tier 1 handoff

The validated Tier 1 bundle is:

```text
results/minerva_production/19_genetic_support/
```

Its status records:

```text
technical_status = validated_complete_tier1
candidate_contexts = 47
unique_genes = 25
colocalization positive_limited = 3 candidate-context units
colocalization not_assessable = 44 candidate-context units
classical H0-H4 = absent
```

The three `positive_limited` rows are APOE in astrocytes and COX7C in
astrocytes and inhibitory neurons. They remain unresolved for Tier 2 because
the Tier 1 inclusion/confidence fields are not classical H0-H4 posteriors.

Tier 2 reads and hash-validates Tier 1. It does not alter, replace, or publish
into the Tier 1 directory.

### Execution and publication decision

Tier 2 will run as a **local production-equivalent analysis**. No Minerva or
LSF job is required for the planned workflow.

```text
execution_stage = local_production_equivalent
execution_backend = direct
publication_namespace = minerva_production
max_custom_coloc_workers = 1
```

The canonical publication path contains `minerva_production` because that is
the repository's namespace for validated final results. It does not claim that
the computation ran on Minerva. The analysis manifest and status file must
record the actual local hardware, backend, execution stage, and timestamps.

The local design stays within the workstation profile by acquiring explicit
public release files and candidate-gene extracts, reusing released models
first, acquiring LD only for a custom comparison that passes all upstream
gates, and processing one custom locus at a time. A hard access or resource
failure becomes an explicit route-level terminal state; the pipeline does not
silently switch to Minerva.

### Approved open-data alternative

The primary production route is frozen as `open_alternative_2026_08_v1`:

| Required role | Frozen primary source | Use and limitation |
|---|---|---|
| Brain eQTL/sQTL statistics and fine mapping | NIAGADS `NG00184.v1`, released 2026-06-18 | GRCh38 bulk and single-nucleus brain QTLs from ROSMAP, MSBB, Knight ADRC, and MiGA; SuSiE/fSuSiE fine mapping. Candidate-gene portal downloads are significant-only and are used for coverage screening, not custom coloc. |
| Primary AD GWAS | GWAS Catalog `GCST90027158`, GRCh38 harmonized Bellenguez 2022 file | Full unfiltered summary statistics with alleles, beta, standard error, frequency, cases, and controls. |
| Primary European LD when a custom model is authorized | NIAGADS `NG00067`, ADSP WGS R5 NHW, n=26,042 | Candidate chromosome/block only; pairwise LD format and variant-order gates must pass before use. |
| Public LD fallback/sensitivity | 1000 Genomes 30x GRCh38, unrelated EUR subset | Used only when compatible with the analyzed ancestry and after recording the substitution as a sensitivity. |
| Dense regional QTL fallback | EMBL-EBI eQTL Catalogue | Tabix/API candidate regions and matching SuSiE/LBF objects; dataset/context/build/release must match. |
| Bulk-brain fallback | GTEx v11 brain SuSiE eQTL/sQTL | Prespecified bulk-brain fallback, never relabeled as an exact cell context. |

The three NG00184 `single_context_finemapping_all` archives and their
manifests are the locally practical first acquisition (about 1.24 GB total).
The complete NG00184 association archives total about 821 GB and exceed the
current local storage gate, so they are not recursively downloaded. Dense QTL
statistics are instead obtained by prespecified candidate region from the
eQTL Catalogue where possible. If no full, compatible regional QTL is publicly
available, the route ends `not_assessable_full_regional_qtl_unavailable`.

The initial alternative execution may therefore complete the production
contract with a mixture of resolved and terminal unassessable routes. It may
not claim that the inaccessible Synapse release was reproduced, and it may
not upgrade a Phase 19 evidence grade using significant-only QTL rows or
credible-set overlap alone.

### What this Tier 2 increment will answer

For every Phase 18 nuclear candidate in each displayed network context:

> Does a prespecified AD GWAS signal share a fine-mapped causal signal with an
> eQTL or sQTL for the candidate gene in the exact or prespecified fallback
> context, after matching genome build, ancestry, variants, alleles,
> fine-mapping model, and LD?

Tier 2 will first extract compatible released signal-level results and model
objects. It will run a custom analysis only for a comparison that remains
unresolved and passes every input gate.

### In scope

- all 19 nuclear Phase 18 genes;
- all 27 nuclear candidate-context units;
- separate eQTL and sQTL decision routes, producing exactly 54 base route
  units before expansion by phenotype, cohort, or fallback context;
- primary clinically anchored late-onset AD GWAS, with the master plan's
  secondary and sensitivity phenotypes kept separate;
- exact cell-context QTLs followed by the frozen fallback hierarchy;
- full, unfiltered candidate-region GWAS and QTL summary statistics when a
  route is eligible for custom colocalization;
- released AD GWAS and QTL fine-mapping/colocalization model objects;
- candidate-region or source LD-block ancestry-matched LD matrices;
- released multi-signal results and, where justified, custom SuSiE-RSS plus
  signal-pair colocalization;
- prior and locus-definition sensitivity analyses; and
- cumulative Phase 19 grading that retains the original Tier 1 grade.

One gene/locus/phenotype fine-mapping result is computed once and referenced
by all applicable Phase 18 contexts. Repeated candidate-context rows are not
independent replication.

### Out of scope

- nuclear rare-variant burden tests;
- mtDNA association, heteroplasmy, haplogroup, copy-number, or NUMT analysis;
- standard nuclear cis-QTL/LD analysis for the six mtDNA genes and their 20
  candidate-context units;
- individual-level genotype or phenotype data;
- recursive download of whole Synapse, NIAGADS, or GWAS containers;
- new GWAS, QTL mapping, or imputation from participant-level data;
- TWAS as a substitute for colocalization;
- result-dependent selection of a phenotype, context, region, prior, method,
  ancestry panel, or alternative gene; and
- modification of Phase 18 candidates or Tier 1 results.

caQTL or another molecular modality may be retained as supplementary
regulatory-chain evidence when it is present in the same frozen release. It
does not satisfy either of the 54 primary eQTL/sQTL route units.

Completing this plan does not by itself complete the rare-variant or mtDNA
routes. Therefore Tier 2 regional-colocalization completion must not set
`full_phase19_complete = TRUE` unless those separately scoped routes have also
been completed under another approved plan.

## Tier 2 end state

Tier 2 is technically complete when:

```text
validation_status = validated_complete_tier2_regional_coloc
tier1_candidate_contexts = 47
tier1_unique_genes = 25
nuclear_genes = 19
nuclear_candidate_contexts = 27
base_eqtl_sqtl_route_units = 54
tier2_summary_rows = 47
undeclared_output_files = 0
blocking_check_failures = 0
full_phase19_complete = false
```

Every one of the 54 base route units must end as one of:

```text
precomputed_resolved
custom_resolved
no_regional_gwas_signal
no_regional_qtl_signal
distinct_signals
qtl_context_not_measured
model_or_ld_incompatible
not_assessable
```

The first two statuses describe how a valid comparison was obtained, not
whether it was positive. The result table separately records `PP.H0` through
`PP.H4`, the conditional H4 value, and evidence classification.

The 20 mtDNA candidate-context rows remain in the 47-row Tier 2 summary with
`tier2_regional_coloc_status = not_applicable_mtdna`; they do not enter the 54
nuclear eQTL/sQTL route count.

## Frozen scientific design inherited from Phase 19

### Phenotype order

1. Primary: clinically anchored late-onset AD case-control GWAS.
2. Secondary: a prespecified AD endophenotype such as age at onset,
   neuropathology, amyloid, tau, or cognitive decline.
3. Sensitivity: proxy-AD or broad-dementia GWAS.

Each phenotype is analyzed and reported separately. A sensitivity result
cannot replace a missing or unfavorable primary analysis.

### QTL context order

The exact and fallback contexts are inherited without change from the master
plan:

| Phase 18 network | Exact QTL context | Ordered fallback |
|---|---|---|
| `Astrocytes` | astrocyte | major-cell-type astrocyte, then bulk brain |
| `Excitatory_neurons` | excitatory neuron | neuron, then bulk brain |
| `Inhibitory_neurons` | inhibitory neuron | neuron, then bulk brain |
| `Microglia` | microglia | myeloid/microglia bulk, then bulk brain |
| `OPCs` | OPC | oligodendrocyte lineage, then bulk brain |
| `Oligodendrocytes` | oligodendrocyte | oligodendrocyte lineage, then bulk brain |
| `Vasculature_cells` | matched endothelial or pericyte subtype | vascular aggregate, then bulk brain |

Every dataset receives an explicit `exact`, `lineage_fallback`,
`bulk_brain_fallback`, or `context_mismatch` label before its result is
examined. Exact and fallback results remain separate rows.

### Statistical rules

- Primary priors are `p1 = 1e-4`, `p2 = 1e-4`, and `p12 = 5e-6`.
- Required prior sensitivity uses `p12 = 1e-6`, `5e-6`, and `1e-5`.
- Primary colocalization support requires `PP.H4 >= 0.80` and
  `PP.H4 / (PP.H3 + PP.H4) >= 0.80`.
- `0.50 <= PP.H4 < 0.80` is suggestive.
- The conditional H4 statistic is missing when `PP.H3 + PP.H4` is effectively
  zero.
- All signal pairs and H0-H4 values are retained, including unfavorable
  comparisons.
- A high `PP.H4` is not sufficient when either trait lacks a regional signal,
  the fine-mapping model fails, or the shared variant set is inadequate.
- Multi-signal analysis is primary whenever more than one causal signal is
  plausible. `coloc.abf` is allowed only for a defensible single-signal locus
  or as a declared sensitivity analysis.
- Direction is computed only after effect alleles are harmonized. It describes
  allelic direction and does not establish mediation or therapeutic effect.

## Data acquisition contract

### Preferred evidence order

Use immutable, released signal-level results before downloading raw regional
statistics or rerunning a model:

1. released AD-xQTL signal-pair colocalization results with H0-H4 and QC;
2. matching released AD-xQTL colocalization model objects;
3. matching AD GWAS and molecular-QTL fine-mapping model objects;
4. full candidate-region GWAS and QTL summary statistics plus matching LD;
5. custom SuSiE-RSS and `coloc.susie` only when levels 1-3 do not resolve the
   comparison.

The original official FunGen-AD resource catalog identifies these containers.
They are retained for exact-source sensitivity but are not prerequisites for
the open-data production route:

| Resource role | Starting container |
|---|---|
| AD GWAS fine-mapping models/results | `syn69670625` |
| AD GWAS colocalization results | `syn69696846` |
| AD GWAS colocalization models | `syn69865824` |
| AD-xQTL colocalization results | `syn69865816` |
| AD-xQTL colocalization models | `syn69670630` |
| molecular-QTL fine-mapping models | `syn69670592` |
| raw molecular-QTL summary statistics | `syn69670632` |
| ADSP European-ancestry LD matrices | `syn69670652` |

Useful entry points are the official
[FunGen-xQTL resource description](https://statfungen.github.io/xqtl-resources/xqtl_resource_description/),
[format catalog](https://statfungen.github.io/xqtl-resources/xqtl_resource_format/),
and [ADSP LD reference description](https://statfungen.github.io/xqtl-resources/xqtl-data/reference_data/ld_reference/).
Container names are discovery handles, not immutable inputs. No result from a
different release may be described as an exact reproduction of these
containers.

### Frozen alternative-source inventory

The alternative inventory is immutable at file level before analysis:

| Source/file | Immutable identity | Expected integrity |
|---|---|---|
| NG00184 eQTL fine mapping, all | file 57059, `ADSP_FunGen_xQTL.v1.eQTL.single_context_finemapping_all.tar` | 365,291,520 bytes; MD5 `cb06f0fded0879612fa534066b255e63` |
| NG00184 sQTL fine mapping, all | file 57099, `ADSP_FunGen_xQTL.v1.sQTL.single_context_finemapping_all.tar` | 563,374,080 bytes; MD5 `c1e0c85799b027849fbe64496d7ef326` |
| NG00184 snuc-eQTL fine mapping, all | file 57109, `ADSP_FunGen_xQTL.v1.snuc-eQTL.single_context_finemapping_all.tar` | 313,733,120 bytes; MD5 `f0d3457b1ed556f85cfbc2651a20190f` |
| NG00184 metadata | files 57112 and 57113 | MD5 `f378f95597ab1422c941154fac92dd8b` and `618ae1a9167160d5eb647f989c2e6531` |
| Bellenguez AD GWAS | `GCST90027158_buildGRCh38.tsv.gz` plus source `md5sum.txt` | Source MD5 must match before extraction |
| ADSP LD | `NG00067` R5 NHW, n=26,042 | Exact per-file MD5 from the official manifest; acquire only eligible candidate chromosomes/blocks |

The NG00184 file API is
`https://st1.niagads.org/portal/v1/download-public/NG00184/fileset/{file_id}`.
The Bellenguez source directory is
`https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90027001-GCST90028000/GCST90027158/`.
Every URL, accession, file ID, byte count, source MD5, local SHA-256, retrieval
time, and analytical role is written to the source manifest.

### Local data layout

Tier 2 source data remain outside Git tracking under:

```text
data/reference/phase19_genetic_support/tier2/
├── inventory/              # official NIAGADS/GWAS/LD manifests
├── source_downloads/       # exact downloaded source files, unchanged
├── niagads_ng00184/        # QTL fine-mapping archives and candidate-gene queries
├── gwas_catalog/           # GCST90027158 source and regional extracts
├── regional_inputs/        # checksum-tracked candidate-region extracts
├── model_objects/          # matching released model objects
├── ld_blocks/              # only required ancestry-matched blocks
└── source_manifest.tsv
```

The current checkout does not contain the ignored Tier 1/Tier 2 external-data
directory. Tier 2 execution must therefore stage and checksum every required
external source rather than assume the Tier 1 downloads are present.

### Inventory before download

For every candidate child file:

1. save the parent/container inventory with retrieval time;
2. record child ID, version, filename, access class, and data-use terms;
3. obtain compressed and, when available, uncompressed byte counts;
4. map the file to candidate gene, locus/block, phenotype, QTL context, QTL
   type, cohort, ancestry, build, method, and model role;
5. calculate aggregate bytes before download;
6. verify available storage is at least `2.2 x` aggregate compressed bytes in
   addition to the 50-GiB free-space reserve;
7. download only explicit file IDs, candidate regions, and required LD blocks;
   the approximately 821-GB complete NG00184 QTL archives are disallowed by
   the local storage gate; and
8. calculate SHA-256 without renaming or modifying source files.

No recursive container download is allowed. No Synapse token, profile,
participant-level file, or controlled phenotype is written to the repository
or command log.

### Required source metadata

The Tier 2 source manifest inherits all master-plan fields and adds:

```text
tier2_source_role
candidate_gene
candidate_locus_id
source_region_or_ld_block
trait_id
model_object_id
model_method
model_parameters_id
variant_id_scheme
variant_order_hash
ld_source_id
ld_ancestry
ld_sample_size
ld_variant_order_hash
released_result_or_custom_input
decision_unit_ids
```

An undocumented filename inference is not valid metadata.

## Model, variant, and LD compatibility contract

### Matching model requirements

A released or custom fine-mapping model may be paired only when all of the
following are explicit and compatible:

- the intended trait, phenotype definition, cohort/release, and sample size;
- ancestry or documented ancestry composition;
- GRCh38 region or source LD block;
- variant normalization and identifier convention;
- reference/effect alleles and effect-size definition;
- source LD reference and variant order;
- fine-mapping method, parameters, maximum effects, and convergence state;
- credible-set coverage and purity; and
- the exact source file/model versions.

Two model objects that merely overlap the same gene or physical interval are
not considered matching.

### Ancestry rule

Each custom fine-mapping model must use LD matched to that trait's analyzed
ancestry. GWAS and QTL models may therefore require separate LD matrices on
the same ordered shared variants. The two trait ancestries must be compatible
with the intended colocalization interpretation and are always reported. The
ADSP European-ancestry panel is not a universal default:

- use it only for an explicitly European-ancestry compatible comparison;
- do not apply it to African-ancestry, admixed, or ancestry-unspecified
  summary statistics;
- do not use European LD for a multi-ancestry meta-analysis unless the source
  method explicitly documents that choice and the analysis is retained as
  source-reproduced rather than newly ancestry-matched;
- keep ancestry-stratified results separate; and
- record `model_or_ld_incompatible` or `not_assessable` when no suitable
  panel exists.

### Variant harmonization

1. require or convert to GRCh38 with the exact chain/reference recorded;
2. left-normalize indels and split multiallelic variants;
3. construct `chromosome:position:ref:alt` identifiers;
4. reject unresolved reference-allele conflicts and duplicates;
5. align GWAS, QTL, and LD alleles and flip beta on swaps;
6. use allele frequency to resolve palindromic variants only when the match is
   unambiguous; otherwise drop them;
7. preserve raw, post-QC, shared, and dropped variant counts and reasons;
8. record whether each trait lead or a trait-LD proxy with `r2 >= 0.8` remains;
9. use dense regional data without P-value filtering; and
10. make each trait's summary-statistic variant order identical to its
    corresponding LD matrix order.

Custom models are fit on the identical dense shared-variant set for both
traits. When released model objects are paired, shared variants must retain
at least 95% of the posterior mass for each compared signal, and each trait
peak must retain its lead or a trait-LD proxy with `r2 >= 0.8`. A result
that fails either gate may be preserved as source evidence but is
`not_assessable` for a primary Tier 2 claim.

### LD QC

For every LD matrix:

- dimensions must equal the registered variant list length;
- row and column variant identities and order must match;
- the matrix must be numeric, symmetric within `1e-8`, and have diagonal
  values within `1e-8` of one;
- all entries must be finite and within `[-1, 1]` within numeric tolerance;
- positive-semidefinite/eigenvalue diagnostics and any regularization must be
  recorded; and
- no silent variant reorder, allele reversal, matrix repair, or ancestry
  substitution is allowed.

## Prespecified decision matrix

Before viewing Tier 2 H0-H4 results, create one row for each of the 54 base
`candidate_id + eQTL/sQTL` route units. Expand those rows by ordered phenotype,
QTL dataset/context, cohort, and signal only after the source inventory is
frozen.

Each expanded comparison receives exactly one action:

| Action | Rule |
|---|---|
| `extract_precomputed` | A compatible released signal-level result and its QC/model provenance are available. |
| `run_from_released_models` | The result is absent or incomplete, but compatible GWAS/QTL fine-mapping models are available. |
| `run_custom_finemap_and_coloc` | Full regional statistics and ancestry-matched LD pass all gates, and the reason for rerun was recorded before results. |
| `terminal_no_signal` | Dense assessable data show no regional GWAS or QTL signal under the frozen rule. |
| `terminal_not_measured` | The required candidate molecular phenotype/context was not measured. |
| `terminal_not_assessable` | Build, allele, coverage, model, metadata, access, or LD requirements fail. |

The rerun reason must be one of:

```text
precomputed_result_absent
precomputed_result_missing_h0_h4
candidate_gene_or_context_omitted
released_model_requires_signal_pair_evaluation
released_result_failed_prespecified_qc
```

An unfavorable released result is not a valid rerun reason.

## Implementation files and isolation from Tier 1

### Add

```text
config/phase19_genetic_support_tier2.yml
config/phase19_tier2_local_execution.yml
scripts/19_download_genetic_support_tier2_alternative.py
scripts/19_extract_genetic_support_tier2_alternative.py
scripts/19_run_genetic_support_tier2.R
tests/test_phase19_genetic_support_tier2.R
tests/fixtures/phase19_tier2/
docs/phase_19_genetic_support/tier2_execution_report.md  # created after execution
```

The scientific config must freeze source child versions, hashes, the 54-unit
decision matrix, phenotype/context ordering, locus definitions, model
parameters, priors, thresholds, output schemas, and software versions before
`definitions_frozen = TRUE`.

### Modify

- `renv.lock`: pin the approved `coloc`, `susieR`, and direct dependencies;
- `scripts/run_pipeline.R`: register a separate global
  `genetic_support_tier2` task and schema;
- `config/minerva_shared.yml`: add
  `project.phase19_genetic_support_tier2_config` and the new allowed task;
- workstation-only `config/local_pilot.yml`: add the Tier 2 config/task for a
  nonfinal pilot; and
- `.gitignore` only if the existing Phase 19 reference-data rule does not
  cover the Tier 2 subtree.

### Preserve

Do not change:

```text
config/phase19_genetic_support.yml
config/phase19_local_production_execution.yml
scripts/19_run_genetic_support.py
results/minerva_production/19_genetic_support/
```

If a shared helper must be extracted from the Tier 1 script, Tier 1 tests and
artifact validation must reproduce the published Tier 1 bundle before the
refactor is accepted.

## Execution workflow

### Task 1: freeze Tier 1 handoff and Tier 2 route manifest

1. hash-validate the Tier 1 status, candidate manifest, loci, assessability,
   summary, artifact manifest, and scientific config;
2. require the validated 47/25 Tier 1 counts;
3. reconstruct the 19 nuclear genes and 27 nuclear candidate contexts from
   `is_mtdna_gene = False` without reranking;
4. cross eQTL and sQTL to create exactly 54 base route rows;
5. add the 20 mtDNA contexts to the final summary as not applicable; and
6. stop if any candidate identity or count differs.

### Task 2: inventory access, sources, and storage

1. inventory the official NIAGADS QTL/model files, GWAS Catalog release,
   eQTL Catalogue studies, and eligible LD panels;
2. record access class and public data-use terms;
3. map explicit files and candidate-region endpoints to decision units before
   download;
4. determine whether released results/models resolve each comparison;
5. calculate source, extraction, scratch, and matrix memory estimates;
6. confirm that the local production-equivalent profile passes; and
7. stop any comparison that does not fit the local gates for review.

This task may end with assessable and unassessable decision units. Public
access to a resource is not itself evidence that a matching context, dense
regional file, or compatible model exists.

### Task 3: acquire immutable candidate-region inputs

1. download the frozen NG00184 fine-mapping files and metadata and the
   Bellenguez GWAS release first;
2. query all 19 candidate genes from the NG00184 portal for coverage mapping,
   while labeling those significant-only rows ineligible for custom coloc;
3. extract candidate-gene fine-mapping rows without modifying source archives;
4. download full regional QTL statistics from a compatible public fallback
   only for still-authorized comparisons;
5. download only the required ancestry-matched LD blocks after a route passes
   the GWAS, QTL, context, and model gates;
6. preserve raw source bytes;
7. generate reproducible region extracts from registered source files;
8. checksum both source files and derived regional extracts; and
9. freeze `source_manifest.tsv` before statistical execution.

### Task 4: validate released models and results

1. validate schemas, builds, variants, alleles, traits, signals, and context;
2. retain source method names such as SuSiE-coloc or ColocBoost;
3. never rename VCP, inclusion score, confidence level, or normalized
   colocalization probability as `PP.H4`;
4. extract H0-H4 only when those hypotheses are actually reported;
5. link every signal pair to matching model and LD provenance; and
6. mark a released result resolved only after the Tier 2 QC contract passes.

### Task 5: harmonize unresolved custom inputs

Apply the build, normalization, allele, coverage, lead-retention, sample-size,
trait-type, and LD-order rules above. Write the complete per-variant operation
log before fine mapping.

No locus is filtered by association P value. No alternate nearby gene is
substituted when the candidate QTL is absent.

### Task 6: fine-map and colocalize

For each authorized signal comparison:

1. reuse a compatible released fine-mapping model when possible;
2. otherwise run a source-compatible SuSiE-RSS model with all parameters
   frozen in the Tier 2 config;
3. require convergence and retain every credible set, PIP, purity measure,
   and signal index;
4. use `coloc.susie` for pairwise GWAS/QTL signals;
5. retain every signal-pair H0-H4 result rather than only the maximum H4;
6. run `coloc.abf` only for the allowed single-signal/sensitivity role;
7. compute the frozen prior sensitivity and alternate-locus sensitivity;
8. calculate allelic direction only on aligned effects; and
9. retain model objects in scratch with hashes, not in the final bundle.

The custom workflow follows the official `coloc`
[data requirements](https://chr1swallace.github.io/coloc/articles/a02_data.html)
and [multi-signal SuSiE workflow](https://chr1swallace.github.io/coloc/articles/a06_SuSiE.html).

### Task 7: integrate evidence without rewriting Tier 1

Create a cumulative 47-row Phase 19 summary with separate fields for:

```text
tier1_genetic_evidence_grade
tier1_colocalization_status
tier2_regional_coloc_status
tier2_best_eqtl_pp_h4
tier2_best_sqtl_pp_h4
tier2_best_conditional_h4
tier2_method
tier2_context_match_level
tier2_ancestry
tier2_assessability_reason
tier2_coloc_grade_contribution
cumulative_phase19_grade
grade_changed_from_tier1
conflicting_evidence
```

An exact-context robust colocalization can contribute `strong`; a robust
prespecified fallback can contribute `moderate`. Suggestive, single-signal,
or incomplete evidence cannot be upgraded beyond the master plan's rules.
Negative Tier 2 evidence does not erase a valid Tier 1 coding/fine-mapping
result; discordance remains explicit.

### Task 8: plot, validate, and publish atomically

1. build the Tier 2 evidence matrix for all 47 candidate contexts;
2. make locus pages for every positive, suggestive, distinct-signal, and QC-
   failed custom analysis;
3. verify all counts, source hashes, decision statuses, posterior bounds,
   grades, and artifact hashes;
4. publish from a fresh staging directory only after all blocking checks pass;
5. write the status file last; and
6. create `tier2_execution_report.md` from validated tables.

## Output roots and contract

```text
results/local_pilot/19_genetic_support_tier2/
results/minerva_production/19_genetic_support_tier2/
```

Pilot output is nonfinal and is never copied into the production directory.
Although the production path contains `minerva_production`, it is the
canonical validated-results namespace rather than an execution-location claim.
Both the analysis manifest and final status must record
`execution_stage = local_production_equivalent` and
`execution_backend = direct`.

The final Tier 2 directory contains exactly these 23 declared files:

| File | Required content |
|---|---|
| `tier2_analysis_manifest.tsv` | Frozen Tier 1 identities, Tier 2 config/software, priors, rules, and execution provenance. |
| `tier2_candidate_route_manifest.tsv` | Exactly 54 nuclear candidate-context × eQTL/sQTL base routes. |
| `tier2_dataset_registry.tsv` | Registered GWAS/QTL/model/LD datasets with phenotype, context, ancestry, build, access, and eligibility. |
| `tier2_input_inventory.tsv` | Every scientific input and derived region extract with bytes, SHA-256, source ID/version, and role. |
| `tier2_source_checks.tsv` | Source identity, access, schema, build, ancestry, model, and LD checks. |
| `tier2_rerun_decisions.tsv` | Prespecified action and reason for every expanded comparison. |
| `tier2_gwas_finemapping.tsv.gz` | GWAS loci, signals, PIPs, credible sets, models, and QC. |
| `tier2_qtl_finemapping.tsv.gz` | Candidate QTL traits, contexts, signals, PIPs, credible sets, models, and QC. |
| `tier2_variant_harmonization.tsv.gz` | Per-variant source identity, allele operation, inclusion, exclusion reason, and LD order. |
| `tier2_variant_harmonization_summary.tsv` | Raw/post-QC/shared counts, coverage, leads, allele operations, and terminal state. |
| `tier2_colocalization.tsv.gz` | Every precomputed/custom signal pair, H0-H4, conditional H4, method, context, ancestry, and direction. |
| `tier2_colocalization_qc.tsv` | Signal, coverage, LD, fine-mapping, convergence, model-match, and assessability QC. |
| `tier2_prior_sensitivity.tsv.gz` | All signal pairs under frozen priors and locus definitions. |
| `tier2_assessability.tsv` | Terminal status and exact reason for every one of the 54 base route units. |
| `tier2_evidence_summary.tsv` | Exactly 47 contexts with Tier 1, Tier 2, cumulative grade, conflict, and wording fields. |
| `tier2_figure_data.tsv.gz` | Every plotted value, label, status, and order. |
| `tier2_evidence_matrix.pdf` | Vector 47-context Tier 2/cumulative evidence matrix. |
| `tier2_evidence_matrix.png` | Raster review copy of the matrix. |
| `tier2_locus_plots.pdf` | Multipage signal and LD review plots or a documented no-qualifying-locus page. |
| `tier2_stage_status.tsv` | Planned, completed, skipped, failed, and reused stages with dependencies. |
| `tier2_checks.tsv` | Blocking and nonblocking expected/observed validation checks. |
| `tier2_artifacts.tsv` | Declared paths, schemas, rows, bytes, SHA-256, and validation states. |
| `tier2_status.tsv` | Final technical/scientific status, counts, limitations, and `full_phase19_complete`, written last. |

All tables begin with `schema_version = human_genetic_support_tier2_coloc_v1`.
The artifact table does not hash itself or the final status file; the status
file stores the completed artifact-manifest hash.

## Tests and pilot

The Tier 2 test suite must cover:

- immutable Tier 1 hash validation and exact 47/25 handoff;
- exact construction of 19 nuclear genes, 27 nuclear contexts, and 54 base
  route units;
- exclusion of 20 mtDNA contexts from nuclear colocalization while retaining
  them in the 47-row summary;
- result-blind route/action assignment;
- released H0-H4 extraction without renaming other source statistics;
- allele match, swap, complement, swap-complement, palindromic, mismatch,
  duplicate, indel, and beta-flip cases;
- build mismatch and failed liftover;
- model trait, region, release, ancestry, variant-order, and LD mismatch;
- LD dimension, order, symmetry, diagonal, bounds, and eigen diagnostics;
- no P-value filtering, identical custom variant sets, released-model
  posterior-mass retention, and lead/proxy coverage gates;
- deterministic single-signal and multiple-signal synthetic loci;
- SuSiE convergence and nonconvergence;
- all signal pairs, H0-H4 bounds, and zero-denominator conditional H4;
- all three frozen `p12` values and alternate-locus sensitivity;
- exact versus fallback context and primary versus sensitivity phenotype;
- `no_regional_signal`, `distinct_signals`, and every not-assessable reason;
- cumulative grade precedence without overwriting Tier 1;
- identical scientific fingerprints across repeated local production runs;
- exact 23-file contract, undeclared-file failure, and artifact hashes; and
- output-only validation with no raw statistics or model objects present.

The pilot uses full-scope manifests plus small deterministic regional fixtures.
It cannot authorize a biological claim.

## Execution profile and escalation

Local production-equivalent execution is the planned and default backend.
Re-audit hardware and free space immediately before acquisition. All of these
gates must pass:

- at least 50 GiB remains free after source, extraction, and scratch estimates;
- each source and derived file passes checksum validation;
- one custom locus runs at a time;
- only explicit candidate-region files and required LD blocks are acquired;
- completed model objects are written to scratch and unloaded before the next
  locus;
- estimated peak memory, including multiple dense LD-matrix copies, remains
  below the master plan's 16-GiB analysis cap; and
- access terms permit local processing.

Minerva is not required and is not an automatic fallback. If a necessary comparison still cannot
fit after using released models, an explicit regional extract, the required
LD block, and one-locus-at-a-time execution, the workflow stops and records a
resource-blocked or `not_assessable` result. A Minerva run requires a
separate user decision. If access terms require an approved server
environment, stop and request direction because that would broaden the
approved local execution scope.

## Blocking gates

Tier 2 open-data production must not start until:

- [ ] this Tier 2 plan and scientific config are approved;
- [ ] the Tier 1 bundle and config hashes reproduce;
- [ ] the 19/27/54 scope counts validate;
- [ ] exact alternative file IDs/accessions, versions, sizes, terms, and
  checksums are frozen;
- [ ] every expanded comparison has a result-blind action and reason;
- [ ] `coloc`, `susieR`, and dependencies are pinned and pass the synthetic
  multi-signal smoke test;
- [ ] each custom route either has full regional trait metadata/statistics or
  a frozen terminal unassessable reason;
- [ ] every executed custom route has matching fine-mapping models and
  ancestry-compatible LD registered;
- [ ] disk, memory, scratch, and worker gates pass for the local backend and
  the actual hardware audit is recorded;
- [ ] the full-manifest pilot passes all blocking tests; and
- [ ] the production output directory is absent or contains no validated
  bundle.

Use `not_assessable` rather than weakening a gate or switching to a favorable
source when build, alleles, model identity, coverage, ancestry, LD, access, or
metadata cannot be resolved.

## Completion checklist

Tier 2 regional GWAS/QTL work is complete only when:

- [ ] Tier 1 remains byte-for-byte valid;
- [ ] all 54 nuclear eQTL/sQTL base routes have terminal statuses;
- [ ] all applicable public released H0-H4/model results were examined first,
  and inaccessible exact-source results are labeled unevaluated;
- [ ] every custom rerun has a prespecified reason;
- [ ] every custom input uses dense, complete regional data without P-value
  filtering;
- [ ] genome build, variants, alleles, ancestry, model, and LD order validate;
- [ ] all signals, credible sets, H0-H4 results, and competing genes remain
  visible;
- [ ] prior and locus sensitivity are complete for every custom comparison;
- [ ] the cumulative summary contains exactly 47 rows, including 20 mtDNA
  `not_applicable_mtdna` rows;
- [ ] the final directory contains exactly 23 declared outputs;
- [ ] every blocking check and artifact hash passes;
- [ ] `tier2_status.tsv` reports
  `validated_complete_tier2_regional_coloc`; and
- [ ] the execution report distinguishes shared-signal evidence from
  mediation, causality, therapeutic direction, rare-variant evidence, and
  mtDNA evidence.
